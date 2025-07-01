import base64
from datetime import datetime
import json
import os
import string
from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.auth import authenticate, login
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.models.aggregates import Sum
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.encoding import force_str
from settings import NOTA_PARA_APROBAR, ASIST_PARA_APROBAR,ASIST_PARA_SEGUIR, MEDIA_ROOT, EMAIL_ACTIVE, SITE_ROOT
from sga.commonviews import ip_client_address
from sga.models import Persona,Inscripcion,Rubro,Materia,Sesion,Clase, RecordAcademico, Noticia, PagoWester, RegistroWester
from sga.reportes import elimina_tildes


def view(request):
    if 'o' in request.POST:
        action = request.POST['o']
        if action == 'login':
            try:
                user = authenticate(username=string.lower(request.POST['user']), password=request.POST['password'])
                if user is not None:
                    if not user.is_active:
                        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
                    else:
                        if Persona.objects.filter(usuario=user).count()>0:
                            persona = Persona.objects.get(usuario=user)
                            if Inscripcion.objects.filter(persona=persona).exists():
                                inscripcion = Inscripcion.objects.filter(persona=persona)[:1].get()
                                rubros = Rubro.objects.filter(inscripcion=inscripcion).order_by('cancelado','fechavence')
                                notif = 0
                                for rubro in rubros:
                                    if rubro.vencido():
                                        notif = notif + 1
                                        break
                                if inscripcion.matricula_set.filter(nivel__periodo__activo=True, nivel__cerrado=False).exists():
                                    matricula = inscripcion.matricula_set.filter(nivel__periodo__activo=True, nivel__cerrado=False)[:1].get()
                                    semana = ['Lunes','Martes','Miercoles','Jueves','Viernes', 'Sabado', 'Domingo']
                                    sesiones = Sesion.objects.all()
                                    hoy = datetime.now().date()


                                    diasemana = ""
                                    sesione = []
                                    seccionestudi = ""


                                    clases = Clase.objects.filter(materia__nivel__periodo__activo=True, materia__nivel__cerrado=False, materia__materiaasignada__matricula__inscripcion=inscripcion, materia__inicio__lte=hoy, materia__fin__gte=hoy).order_by('materia__inicio')
                                    clasespm = [(x, x.materia.profesormateria_set.filter(desde__lte=hoy, hasta__gte=hoy)[:1].get() if x.materia.profesormateria_set.filter(desde__lte=hoy, hasta__gte=hoy).exists() else None) for x in clases]
                                    horario = []
                                    band = 0

                                    for sesion in sesiones:

                                        seccion =  str(sesion)


                                        # for dia in sesion.semana():
                                        turnos = []
                                        for turno in sesion.turnos():
                                            for i in clasespm:
                                                if i[1]:
                                                    if (i[0].dia == int(datetime.now().strftime("%w")) or (i[0].dia == 7 and int(datetime.now().strftime("%w")) == 0)) and i[0].turno.id == turno.id:
                                                        notif = notif + 1
                                                        band = 1
                                                        break
                                            if band != 0:
                                                break
                                        if band != 0:
                                            break
                                else:
                                    matricula = inscripcion.matricula_set.filter(nivel__periodo__activo=True, nivel__cerrado=True)[:1].get()


                                inscripcion = Inscripcion.objects.filter(persona=persona)[:1].get()
                                if inscripcion.tiene_deuda():
                                    return HttpResponse(json.dumps({"result":"deuda"}),content_type="application/json")
                                resultado = {"result":"ok"}
                                lista = [{"idinscrip": inscripcion.id,"cedula": persona.cedula,"nombre": persona.nombre_completo().encode("ascii","ignore"),
                                         "imagen": persona.foto().foto.url if persona.foto() else "","carrera":str(matricula.nivel.carrera),"notif":notif}]
                                resultado['lista'] = lista
                                return HttpResponse(json.dumps(resultado),content_type="application/json")


                        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
                else:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
            except Exception as ex:
                return HttpResponse(json.dumps({"result":"excepcion"+str(ex)}),content_type="application/json")

        elif action == 'cronograma':
            try:
                if Inscripcion.objects.filter(id=request.POST['id']).exists():
                    inscripcion = Inscripcion.objects.get(id=request.POST['id'])
                    #Comprobar que el alumno este matriculado
                    if inscripcion.matriculado():

                        matricula = inscripcion.matricula_set.filter(nivel__periodo__activo=True, nivel__cerrado=False)[:1].get()
                        materiasAsignadas = matricula.materiaasignada_set.all().order_by('materia__inicio')
                        resultado = {"result":"ok"}
                        matri = [{"nombre": str(matricula.inscripcion),"carrera": str(matricula.nivel.carrera),
                                 "nivel": str(matricula.nivel.nivelmalla) +" - "+ matricula.nivel.paralelo +" ("+  str(matricula.nivel.sesion) +" )",
                                 "periodo":str(matricula.nivel.periodo)}]
                        resultado['matricula'] = matri
                        mateasigna = []

                        cont = 0
                        bandprof = 0
                        bandeposcio = 0
                        contarmateria = 0
                        if materiasAsignadas:
                            for maasig in materiasAsignadas:
                                asignatura = maasig.materia.identificacion +" - " if maasig.materia.identificacion else ""
                                aprobada = "MATERIA YA CURSADA" if maasig.materia.pasada_fecha() else ""
                                clasesasig = []
                                canthorario = ""
                                for clase in maasig.materia.clase_set.all().order_by("dia"):
                                    canthorario = canthorario + clase.dia_semana() +" - (" + str(clase.turno.comienza) + " a " + str(clase.turno.termina) +" )" + clase.aula.nombre
                                    clasesasig.append({"clase": clase.dia_semana() +" - (" + str(clase.turno.comienza) + " a " + str(clase.turno.termina) +" ) Aula:"+clase.aula.nombre })
                                profesor = []

                                posicio=""
                                profeaux=""
                                profeprin=""
                                profeaux2=""
                                profeprin2=""

                                if maasig.materia.profesormateria_set.count():
                                    for profesormateria in maasig.materia.profesores_materia():
                                        if profesormateria.profesor_aux:
                                            profeaux = profesormateria.profesor_auxiliar().persona.nombre_completo()
                                        else:
                                            profeprin = profesormateria.profesor.persona.nombre_completo()

                                asignatura1 = maasig.materia.identificacion +" - " if maasig.materia.identificacion else ""
                                asignatura1 = asignatura1 + elimina_tildes(maasig.materia.asignatura)
                                for maasig2 in materiasAsignadas:

                                    asignatura2 = maasig2.materia.identificacion +" - " if maasig2.materia.identificacion else ""
                                    asignatura2 = asignatura2 + elimina_tildes(maasig2.materia.asignatura)

                                    if maasig2.materia.profesormateria_set.count():
                                        for profesormateria in maasig2.materia.profesores_materia():
                                            if profesormateria.profesor_aux:
                                                profeaux2 = profesormateria.profesor_auxiliar().persona.nombre_completo()
                                            else:
                                                profeprin2 = profesormateria.profesor.persona.nombre_completo()
                                    canthorario2 = ""
                                    for clase2 in maasig2.materia.clase_set.all().order_by("dia"):
                                        canthorario2 = canthorario2 + clase2.dia_semana() +" - (" + str(clase2.turno.comienza) + " a " + str(clase2.turno.termina) +" )" + clase2.aula.nombre

                                    if maasig.materia.clase_set.all().count() <= maasig2.materia.clase_set.all().count() :

                                        if maasig.materia.clase_set.all().count() == maasig2.materia.clase_set.all().count():
                                            if  cont == 0 and maasig.materia != maasig2.materia:
                                                if len(profeaux)+len(profeprin)+len(asignatura1)+len(canthorario) >= len(profeaux2)+len(profeprin2)+len(asignatura2)+len(canthorario2):
                                                    posicio = ""
                                                    bandprof = 1
                                                else:
                                                    posicio = "style='position: absolute; top: 0;'"
                                                    if  cont == 0:
                                                        bandprof = 0
                                                    break
                                            else:
                                                if bandprof == 1 and maasig.materia == maasig2.materia:
                                                    if len(profeaux)+len(profeprin)+len(asignatura1)+len(canthorario) >= len(profeaux2)+len(profeprin2)+len(asignatura2)+len(canthorario2):
                                                        posicio = ""
                                                        bandprof = 0
                                                else:
                                                    posicio = "style='position: absolute; top: 0;'"

                                        else:
                                            posicio = "style='position: absolute; top: 0;'"
                                            break
                                    else:
                                        # if maasig.materia.clase_set.all().count() > maasig2.materia.clase_set.all().count() :
                                        #     if len(profeaux)+len(profeprin)+len(asignatura1) >= len(profeaux2)+len(profeprin2)+len(asignatura2):
                                        posicio = ""
                                        bandprof = 2
                                if bandprof != 0:
                                    cont= cont + 1

                                if maasig.materia.profesormateria_set.count():
                                    for profesormateria in maasig.materia.profesores_materia():
                                        if profesormateria.profesor_aux:
                                            profesor.append({"profesor": profesormateria.profesor_auxiliar().persona.nombre_completo(),"tipoprofe": str(profesormateria.segmento) +" ["+ str(profesormateria.desde) +" al "+str(profesormateria.hasta)+"]" })
                                        else:
                                            profesor.append({"profesor": profesormateria.profesor.persona.nombre_completo(),"tipoprofe": str(profesormateria.segmento) +" ["+ str(profesormateria.desde) +" al "+str(profesormateria.hasta)+"]" })
                                if posicio == "":
                                    bandeposcio = 1
                                contarmateria = contarmateria + 1
                                if contarmateria == materiasAsignadas.count() and bandeposcio == 0:
                                    posicio = ""
                                mateasigna.append({'asignatura': asignatura + elimina_tildes(maasig.materia.asignatura), 'aprobada': aprobada,
                                                   'horas': maasig.materia.horas,'creditos': maasig.materia.creditos,
                                                   'inicio': str(maasig.materia.inicio),'fin': str(maasig.materia.fin),"profesor":profesor,"posicio":posicio,"clasesasig":clasesasig })

                            resultado['materiasasignadas'] = mateasigna
                            return HttpResponse(json.dumps(resultado),content_type="application/json")

                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

            except Exception as ex:
                return HttpResponse(json.dumps({"result":"excepcion"+str(ex)}),content_type="application/json")

        elif action == 'materia':
            try:
                if Inscripcion.objects.filter(id=request.POST['id']).exists():
                    inscripcion = Inscripcion.objects.get(id=request.POST['id'])


                    #Comprobar que el alumno este matriculado
                    if inscripcion.matriculado():

                        matricula = inscripcion.matricula_set.filter(nivel__periodo__activo=True, nivel__cerrado=False)[:1].get()
                        materiasAsignadas = matricula.materiaasignada_set.all().order_by('materia__inicio')
                        resultado = {"result":"ok"}
                        matri = [{"nombre": str(matricula.inscripcion),"carrera": str(matricula.nivel.carrera),
                                 "nivel": str(matricula.nivel.nivelmalla) +" - "+ matricula.nivel.paralelo +" ("+  str(matricula.nivel.sesion) +" )",
                                 "periodo":str(matricula.nivel.periodo)}]
                        resultado['matricula'] = matri
                        mateasigna = []

                        cont = 0
                        bandprof = 0
                        if materiasAsignadas:
                            for maasig in materiasAsignadas:
                                asignatura = maasig.materia.identificacion  +" - " if maasig.materia.identificacion else ""

                                codigevalua1 =" - <span class='tips' title='"+str(maasig.evaluacion().cod1.nombre)+"'>["+ str(maasig.evaluacion().cod1.id) +"]</span>"  if maasig.evaluacion().n1 and maasig.evaluacion().cod1 else ""
                                codigevalua2 =" - <span class='tips' title='"+str(maasig.evaluacion().cod2.nombre)+"'>["+ str(maasig.evaluacion().cod2.id) +"]</span>" if maasig.evaluacion().n2 and maasig.evaluacion().cod2 else ""
                                codigevalua3 =" - <span class='tips' title='"+str(maasig.evaluacion().cod3.nombre)+"'>["+ str(maasig.evaluacion().cod3.id) +"]</span>" if maasig.evaluacion().n3 and maasig.evaluacion().cod3 else ""
                                codigevalua4 =" - <span class='tips' title='"+str(maasig.evaluacion().cod4.nombre)+"'>["+ str(maasig.evaluacion().cod4.id) +"]</span>" if maasig.evaluacion().n4 and maasig.evaluacion().cod4 else ""

                                profesor=[]
                                cantprofesor=""
                                if maasig.materia.profesormateria_set.count():
                                    for profesormateria in maasig.materia.profesores_materia():
                                            if profesormateria.profesor_aux:
                                                cantprofesor = cantprofesor + profesormateria.profesor_auxiliar().persona.nombre_completo()+str(profesormateria.segmento)
                                                profesor.append({"profesor": profesormateria.profesor_auxiliar().persona.nombre_completo(),"tipoprofe": str(profesormateria.segmento) })
                                            else:
                                                cantprofesor = cantprofesor + profesormateria.profesor.persona.nombre_completo()+str(profesormateria.segmento)
                                                profesor.append({"profesor": profesormateria.profesor.persona.nombre_completo(),"tipoprofe": str(profesormateria.segmento)})

                                nfinal = ""
                                if maasig.evaluacion().nota_final() < NOTA_PARA_APROBAR or maasig.porciento_asistencia() < ASIST_PARA_APROBAR:
                                    nfinal = "<span class='badge badge-error bigger'>"+ str(maasig.evaluacion().nota_final()) +"</span>"
                                else:
                                    nfinal = "<span class='badge badge-success bigger'>"+ str(maasig.evaluacion().nota_final()) +"</span>"

                                asistencia = ""
                                if maasig.porciento_asistencia < ASIST_PARA_SEGUIR:
                                    asistencia = "<span style='color: #dc143c;'><b>"+ str(maasig.porciento_asistencia())  +"%</b></span>"
                                elif maasig.porciento_asistencia >= ASIST_PARA_SEGUIR and maasig.porciento_asistencia < ASIST_PARA_APROBAR:
                                    asistencia = "<span style='color: #daa520;'><b>"+ str(maasig.porciento_asistencia())  +"%</b></span>"
                                elif maasig.porciento_asistencia >= ASIST_PARA_APROBAR:
                                    asistencia = "<span style='color:#006400;'><b>"+ str(maasig.porciento_asistencia())  +"%</b></span>"


                                estado = ""
                                if maasig.evaluacion().estado_id != 1:
                                    estado = "<span class='label  label-info'>"+ maasig.evaluacion().estado.nombre +"</span>"
                                elif maasig.evaluacion().estado_id == 2:
                                    estado = "<span style='color: #dc143c;'><b>"+ maasig.evaluacion().estado.nombre +"</b></span>"
                                    if maasig.notafinal < NOTA_PARA_APROBAR:
                                        estado = estado + "<span style='color: #dc143c;'><b> (AS)</b></span>"
                                    if maasig.porciento_asistencia() < ASIST_PARA_APROBAR:
                                        estado = estado + "<span style='color: #dc143c;'><b> (AS)</b></span>"


                                posicio=""
                                for maasig2 in materiasAsignadas:
                                    asignatura2 = maasig2.materia.identificacion  +" - " if maasig2.materia.identificacion else ""
                                    cantprofesor2 = ""
                                    if maasig2.materia.profesormateria_set.count():
                                        for profesormateria2 in maasig2.materia.profesores_materia():
                                            if profesormateria2.profesor_aux:
                                                cantprofesor2 = cantprofesor2 + profesormateria2.profesor_auxiliar().persona.nombre_completo()+str(profesormateria2.segmento)
                                            else:
                                                cantprofesor2 = cantprofesor2 + profesormateria2.profesor.persona.nombre_completo()+str(profesormateria2.segmento)

                                    if len(asignatura + elimina_tildes(maasig.materia.asignatura))+len(cantprofesor) <= len(asignatura2 + elimina_tildes(maasig2.materia.asignatura))+len(cantprofesor2) :

                                        if len(asignatura + elimina_tildes(maasig.materia.asignatura))+len(cantprofesor) == len(asignatura2 + elimina_tildes(maasig2.materia.asignatura))+len(cantprofesor2):
                                            if  cont == 0 and maasig.materia != maasig2.materia:
                                                posicio = ""
                                                bandprof = 1
                                            else:
                                                if bandprof == 1 and maasig.materia == maasig2.materia:
                                                    posicio = ""
                                                else:
                                                    posicio = "style='position: absolute; top: 0;'"

                                        else:
                                            posicio = "style='position: absolute; top: 0;'"
                                            break
                                    else:
                                        if len(asignatura + elimina_tildes(maasig.materia.asignatura)) > len(asignatura2 + elimina_tildes(maasig2.materia.asignatura)) or maasig.materia.profesormateria_set.count() > maasig2.materia.profesormateria_set.count() :
                                            posicio = ""
                                            bandprof = 1
                                cont= cont +1

                                mateasigna.append({'asignatura': asignatura + elimina_tildes(maasig.materia.asignatura),
                                                   'inicio': str(maasig.materia.inicio),'fin': str(maasig.materia.fin),"profesor":profesor,
                                                   'nota1':str(maasig.evaluacion().n1),'codigevalua1':codigevalua1,
                                                   'nota2':str(maasig.evaluacion().n2),'codigevalua2':codigevalua2,
                                                   'nota3':str(maasig.evaluacion().n3),'codigevalua3':codigevalua3,
                                                   'nota4':str(maasig.evaluacion().n4),'codigevalua4':codigevalua4,
                                                   'examen':str(maasig.evaluacion().examen),'recuperacion':str(maasig.evaluacion().recuperacion),
                                                   'nfinal':nfinal,'asistencia':asistencia,'estado':estado,"posicio":posicio})

                            resultado['materiasasignadas'] = mateasigna
                            return HttpResponse(json.dumps(resultado),content_type="application/json")
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

            except Exception as ex:
                return HttpResponse(json.dumps({"result":"excepcion"+str(ex)}),content_type="application/json")
        elif action == 'rubro':
            try:
                if Inscripcion.objects.filter(id=request.POST['id']).exists():
                    inscripcion = Inscripcion.objects.get(id=request.POST['id'])
                    matricula = inscripcion.matricula_set.filter(nivel__periodo__activo=True, nivel__cerrado=False)[:1].get()
                    resultado = {"result":"ok"}

                    matri = [{"nombre": str(matricula.inscripcion),"carrera": str(matricula.nivel.carrera),
                                 "nivel": str(matricula.nivel.nivelmalla) +" - "+ matricula.nivel.paralelo +" ("+  str(matricula.nivel.sesion) +" )",
                                 "periodo":str(matricula.nivel.periodo)}]
                    resultado['matricula'] = matri

                    rubros = Rubro.objects.filter(inscripcion=inscripcion).order_by('cancelado','fechavence')
                    total_rubros = rubros.aggregate(Sum('valor'))['valor__sum']
                    total_pagado = sum([x.total_pagado() for x in rubros])
                    total_adeudado = sum([x.adeudado() for x in rubros])

                    rubroslis=[]
                    for rubro in rubros:

                        if rubro.vencido():
                            fecha =  "<span class='label label-danger'> Vencida el "+ str(rubro.fechavence) + "</span>"
                        else:
                            if rubro.fechavence < datetime.now().date():
                                fecha = "<span class='label label-warning'>  Cancelado </span>"
                            else:
                                fecha = "<span class='label label-info'> Vence el "+ str(rubro.fechavence) + "</span>"
                        adeuda = ""
                        cancelado =  "<span class='label label-success'>Si</span>" if rubro.cancelado else "<span class='label label-important'>No</span>"
                        if rubro.adeudado():
                            adeuda = "<span class='label label-important bigger'>$"+ str(rubro.adeudado()) +"</span>" if rubro.vencido else "<span class='label label-success bigger'>"+ rubro.adeudado() + "</span>"
                        rubroslis.append({'nombre':rubro.nombre(),'fecha':fecha,'valor':str(rubro.valor),'pagado':str(rubro.total_pagado()),
                                          'adeuda':adeuda,'cancelado':cancelado})

                    totales = [{"total_rubros":str(total_rubros),"total_pagado":str(total_pagado),"total_adeudado":str(total_adeudado)}]

                    resultado['rubros'] = rubroslis
                    resultado['totales'] = totales

                    return HttpResponse(json.dumps(resultado),content_type="application/json")
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

            except Exception as ex:
                return HttpResponse(json.dumps({"result":"excepcion"+str(ex)}),content_type="application/json")

        elif action == 'horario':
            try:
                if Inscripcion.objects.filter(id=request.POST['id']).exists():
                    inscripcion = Inscripcion.objects.get(id=request.POST['id'])

                    if inscripcion.matriculado():
                        materias = Materia.objects.filter(materiaasignada__matricula__inscripcion=inscripcion)

                        # periodo = request.session['periodo']
                        matricula = inscripcion.matricula_set.filter(nivel__periodo__activo=True, nivel__cerrado=False)
                        # matricula = inscripcion.matricula_set.filter(nivel__periodo=periodo)

                        resultado = {"result":"ok","inscripcion":str(inscripcion),"periodo":str(matricula[0].nivel.periodo),"paralelo":str(matricula[0].nivel)}

                        semana = ['Lunes','Martes','Miercoles','Jueves','Viernes', 'Sabado', 'Domingo']
                        sesiones = Sesion.objects.all()

                        #hoy = datetime.now().date()
                        hoy = datetime.now().date()

                        clases = Clase.objects.filter(materia__nivel__periodo__activo=True, materia__nivel__cerrado=False, materia__materiaasignada__matricula__inscripcion=inscripcion, materia__inicio__lte=hoy, materia__fin__gte=hoy).order_by('materia__inicio')
                        clasespm = [(x, x.materia.profesormateria_set.filter(desde__lte=hoy, hasta__gte=hoy)[:1].get() if x.materia.profesormateria_set.filter(desde__lte=hoy, hasta__gte=hoy).exists() else None) for x in clases]


                        sesione = []
                        for sesion in sesiones:
                            seccion =  str(sesion)
                            horario = []
                            for dia in sesion.semana():
                                turnos = []
                                for turno in sesion.turnos():
                                    for i in clasespm:
                                        if i[1]:
                                            if i[0].dia == dia[1] and i[0].turno.id == turno.id:
                                                if i[1].profesor_aux:
                                                    profesor = i[1].profesor_auxiliar()
                                                else:
                                                    profesor = i[1].profesor.persona.nombre_completo()
                                                asignat = "<div><span class='label label-danger'>"+ str(i[1].segmento) +"</span> " \
                                                             "<strong> "+ i[0].materia.nombre_completo() +"</strong><br/>" \
                                                             "<span class='larger label label-info'>" + str(i[1].desde) +" al "+ str(i[1].hasta) +"</span>" \
                                                             "<br>"+ profesor +"<br/>"+ str(i[0].materia.nivel.carrera) \
                                                             +"<br/>"+ str(i[0].materia.nivel.nivelmalla) +" - "+ str(i[0].materia.nivel.paralelo) +" " \
                                                             "en "+ str(i[0].materia.nivel.sede) +"<br/>Aula: "+ str(i[0].aula) +"<br/></div>"
                                                turnos.append({"turno": str(turno.turno),"comienza":str(turno.comienza),"termina":str(turno.termina),"asignatura":asignat})
                                if turnos:
                                    horario.append({"dia": dia[0],"turnos":turnos})
                            if horario:
                                sesione.append({"sesiones":str(sesion),"horario":horario})
                        resultado['sesiones'] = sesione
                        return HttpResponse(json.dumps(resultado),content_type="application/json")

                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

            except Exception as ex:
                return HttpResponse(json.dumps({"result":"excepcion"+str(ex)}),content_type="application/json")
        elif action == 'notificacion':
            try:
                if Inscripcion.objects.filter(id=request.POST['id']).exists():
                    inscripcion = Inscripcion.objects.get(id=request.POST['id'])
                    matricula = inscripcion.matricula_set.filter(nivel__periodo__activo=True, nivel__cerrado=False)[:1].get()
                    resultado = {"result":"ok"}
                    matri = [{"nombre": str(matricula.inscripcion),"carrera": str(matricula.nivel.carrera),
                                 "nivel": str(matricula.nivel.nivelmalla) +" - "+ matricula.nivel.paralelo +" ("+  str(matricula.nivel.sesion) +" )",
                                 "periodo":str(matricula.nivel.periodo)}]
                    resultado['matricula'] = matri
                    hoy = datetime.now().date()
                    rubros = Rubro.objects.filter(inscripcion=inscripcion,fechavence__lt=hoy,cancelado=False).order_by('cancelado','fechavence')
                    total_rubros = rubros.aggregate(Sum('valor'))['valor__sum']
                    total_pagado = sum([x.total_pagado() for x in rubros])
                    total_adeudado = sum([x.adeudado() for x in rubros])

                    rubroslis=[]
                    for rubro in rubros:
                        if rubro.vencido():
                            fecha =  "<span class='label label-danger'> Vencida el "+ str(rubro.fechavence) + "</span>"
                        else:
                            if rubro.fechavence < datetime.now().date():
                                fecha = "<span class='label label-warning'> Cancelado </span>"
                            else:
                                fecha = "<span class='label label-info'> Vence el "+ str(rubro.fechavence) + "</span>"
                        adeuda = ""
                        cancelado =  "<span class='label label-success'>Si</span>" if rubro.cancelado else "<span class='label label-important'>No</span>"
                        if rubro.adeudado():
                            adeuda = "<span class='label label-important bigger'>$"+ str(rubro.adeudado()) +"</span>" if rubro.vencido else "<span class='label label-success bigger'>"+ rubro.adeudado() + "</span>"
                        rubroslis.append({'nombre':rubro.nombre(),'fecha':fecha,'valor':str(rubro.valor),'pagado':str(rubro.total_pagado()),
                                          'adeuda':adeuda,'cancelado':cancelado})

                    totales = [{"total_rubros":str(total_rubros),"total_pagado":str(total_pagado),"total_adeudado":str(total_adeudado)}]

                    resultado['matricula'] = matri
                    resultado['rubros'] = rubroslis
                    resultado['totales'] = totales
                    matricula = inscripcion.matricula_set.filter(nivel__periodo__activo=True, nivel__cerrado=False)[:1].get()

                    semana = ['Lunes','Martes','Miercoles','Jueves','Viernes', 'Sabado', 'Domingo']
                    sesiones = Sesion.objects.all()



                    diasemana = ""
                    sesione = []
                    seccionestudi = ""


                    clases = Clase.objects.filter(materia__nivel__periodo__activo=True, materia__nivel__cerrado=False, materia__materiaasignada__matricula__inscripcion=inscripcion, materia__inicio__lte=hoy, materia__fin__gte=hoy).order_by('materia__inicio')
                    clasespm = [(x, x.materia.profesormateria_set.filter(desde__lte=hoy, hasta__gte=hoy)[:1].get() if x.materia.profesormateria_set.filter(desde__lte=hoy, hasta__gte=hoy).exists() else None) for x in clases]
                    horario = []
                    for sesion in sesiones:

                        seccion =  str(sesion)


                        # for dia in sesion.semana():
                        turnos = []
                        for turno in sesion.turnos():
                            for i in clasespm:
                                if i[1]:
                                    if (i[0].dia == int(datetime.now().strftime("%w")) or (i[0].dia == 7 and int(datetime.now().strftime("%w")) == 0)) and i[0].turno.id == turno.id:
                                        for dia in sesion.semana():
                                           if i[0].dia == dia[1]:
                                              diasemana = dia[0]
                                              break
                                        seccionestudi = sesion
                                        if i[1].profesor_aux:
                                            profesor = i[1].profesor_auxiliar()
                                        else:
                                            profesor = i[1].profesor.persona.nombre_completo()
                                        asignat = "<div><span class='label label-danger'>"+ str(i[1].segmento) +"</span> " \
                                                     "<strong> "+ i[0].materia.nombre_completo() +"</strong><br/>" \
                                                     "<span class='larger label label-info'>" + str(i[1].desde) +" al "+ str(i[1].hasta) +"</span>" \
                                                     "<br>"+ profesor +"<br/>"+ str(i[0].materia.nivel.carrera) \
                                                     +"<br/>"+ str(i[0].materia.nivel.nivelmalla) +" - "+ str(i[0].materia.nivel.paralelo) +" " \
                                                     "en "+ str(i[0].materia.nivel.sede) +"<br/>Aula: "+ str(i[0].aula) +"<br/></span></div>"
                                        turnos.append({"turno": str(turno.turno),"comienza":str(turno.comienza),"termina":str(turno.termina),"asignatura":asignat})
                        if turnos:
                            horario.append({"dia": diasemana,"turnos":turnos})
                    if horario:
                        sesione.append({"sesiones":str(seccionestudi),"horario":horario})
                    resultado['sesiones'] = sesione
                    return HttpResponse(json.dumps(resultado),content_type="application/json")
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

            except Exception as ex:
                return HttpResponse(json.dumps({"result":"excepcion"+str(ex)}),content_type="application/json")
        elif action == "record":
            try:
                if Inscripcion.objects.filter(id=request.POST['id']).exists():
                    inscripcion = Inscripcion.objects.get(id=request.POST['id'])
                    matricula = inscripcion.matricula_set.filter(nivel__periodo__activo=True, nivel__cerrado=False)[:1].get()
                    resultado = {"result":"ok"}
                    matri = [{"nombre": str(matricula.inscripcion),"carrera": str(matricula.nivel.carrera),
                                 "nivel": str(matricula.nivel.nivelmalla) +" - "+ matricula.nivel.paralelo +" ("+  str(matricula.nivel.sesion) +" )",
                                 "periodo":str(matricula.nivel.periodo)}]
                    resultado['matricula'] = matri
                    records = RecordAcademico.objects.filter(inscripcion=inscripcion).order_by('fecha')
                    recordacadem = []
                    for record in records:
                        recor = "<tr><td style='width:90%;font-size:11;background:white'>"+ str(record.asignatura) +"<span class='label label-info'>"+ str(record.fecha) +"</span> </td><td class='"
                        nota = "red" if record.esta_suspensa() else "green"
                        recor = recor +"' style='width:5%;color:"+ nota +";font-size: 18;background:white'><b>"+ str(record.nota) +"</b></td><td class='"
                        asist = "green" if record.asistencia >= ASIST_PARA_APROBAR else "red"
                        recor = recor + "' style='width:5%;color: "+ asist +";font-size: 18;background:white'><b>"+ str(record.asistencia) +"</b></td></tr>"

                        recordacadem.append({"recor":recor})
                    resultado['recordacadem'] = recordacadem
                    return HttpResponse(json.dumps(resultado),content_type="application/json")
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
            except Exception as ex:
                return HttpResponse(json.dumps({"result":"excepcion"+str(ex)}),content_type="application/json")

        elif action == "noticia":
            try:
                if Inscripcion.objects.filter(id=request.POST['id']).exists():
                    inscripcion = Inscripcion.objects.get(id=request.POST['id'])
                    hoy = datetime.now().date()
                    noticias = Noticia.objects.filter(tipo__in=(1,2,4),desde__lte=hoy,hasta__gte=hoy)
                    noticia = []
                    resultado = {"result":"ok"}
                    for noti in noticias:
                        noticia.append({"titulo":noti.titular,"cuerpo":noti.cuerpo,"idnoti":noti.id,"fechhasta":str(noti.hasta)})
                    resultado["noticias"] = noticia
                    return HttpResponse(json.dumps(resultado),content_type="application/json")
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
            except Exception as ex:
                return HttpResponse(json.dumps({"result":"excepcion"+str(ex)}),content_type="application/json")
        elif action == "wester":
            try:
                if PagoWester.objects.filter(codigo=request.POST['codigo']).exists():
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
                base = base64.b64decode(request.POST['img64'])
                output_folder = os.path.join(MEDIA_ROOT,'wester',str(datetime.now().year),str(datetime.now().month).zfill(2),str(datetime.now().day).zfill(2))
                try:
                    os.makedirs(output_folder)
                except :
                    # return HttpResponse(json.dumps({'result':'bad'}),content_type="application/json")
                    pass
                with open(os.path.join(output_folder,request.POST['imgName']), 'wb') as f:
                    f.write(base)
                archivoname = 'wester/'+str(datetime.now().year)+"/"+str(datetime.now().month).zfill(2)+"/"+str(datetime.now().day).zfill(2)+"/"+request.POST['imgName']
                if request.POST["dato"] == "true":
                    pagowester = PagoWester(inscripcion_id=request.POST["idinscrip"],
                                        archivo = archivoname,
                                        codigo = request.POST["codigo"],
                                        datos = True,
                                        identificacion = request.POST["cedula"],
                                        nombre = request.POST["nombre"],
                                        direccion = request.POST["direccion"],
                                        telefono = request.POST["telefono"],
                                        email = request.POST["email"],
                                        fecha=datetime.now())
                else:
                    pagowester = PagoWester(inscripcion_id=request.POST["idinscrip"],
                                        codigo = request.POST["codigo"],
                                        archivo = archivoname,fecha=datetime.now())
                pagowester.save()
                inscripcion = Inscripcion.objects.filter(id=request.POST["idinscrip"])[:1].get()
                if EMAIL_ACTIVE:
                    pagowester.mail_pago(inscripcion.persona.usuario)
                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                    user_id         = inscripcion.persona.usuario.pk,
                    content_type_id = ContentType.objects.get_for_model(pagowester).pk,
                    object_id       = pagowester.id,
                    object_repr     = force_str(pagowester),
                    action_flag     = ADDITION,
                    change_message  = 'Adicionado Registro de Pago desde ITBMOVIL (' + client_address + ')' )
                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")

            except Exception as ex:
                # return HttpResponse(json.dumps({"result":"excepcion"+str(ex)}),content_type="application/json")
                return HttpResponse(json.dumps({"result":"excepcion"+str(ex)}),content_type="application/json")
        elif action == "existecod":
            try:
                # if RegistroWester.objects.filter(codigo=request.POST['busqueda']).exists():
                #     return HttpResponse(json.dumps({"result":"rbad"}),content_type="application/json")
                if PagoWester.objects.filter(codigo=request.POST['busqueda']).exists():
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            except Exception as ex:
                return HttpResponse(json.dumps({"result":"excepcion"+str(ex)}),content_type="application/json")

        elif action == "busquewester":
            try:
                if PagoWester.objects.filter(inscripcion__id=request.POST["id"]).exists():
                    resultado = {"result":"ok"}
                    wester=[]
                    nombre2=""
                    for west in PagoWester.objects.filter(inscripcion__id=request.POST["id"]):

                        cedula = west.inscripcion.persona.cedula if west.inscripcion.persona.cedula else west.inscripcion.persona.pasaporte
                        identificacion = west.identificacion if west.datos else cedula
                        nombre = west.nombre if west.datos else west.inscripcion.persona.nombre_completo()
                        if len(nombre) >= len(nombre2):
                            posicio = ""
                        else:
                            posicio = "style='position: absolute; top: 0;'"
                        nombre2 =  nombre
                        direccion = west.direccion if west.datos else west.inscripcion.persona.direccion
                        telefono = west.telefono if west.datos else west.inscripcion.persona.telefono
                        email = west.email if west.datos else west.inscripcion.persona.email
                        wester.append({"idwest":west.id,"posicio":posicio,"inscripcion":west.inscripcion.persona.nombre_completo(),"archivo":os.path.join(MEDIA_ROOT,west.archivo.url),"codigo":west.codigo,
                                       "datos":str(west.datos),"identificacion":str(identificacion),"nombre":nombre,"direccion":direccion,
                                       "telefono":str(telefono),"email":str(email),"fecha":str(west.fecha.date())})
                    resultado["wester"] = wester
                    return HttpResponse(json.dumps(resultado),content_type="application/json")
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
            except Exception as ex:
                return HttpResponse(json.dumps({"result":"excepcion"+str(ex)}),content_type="application/json")
        elif action == "imagenwester":
            try:
                if PagoWester.objects.filter(id=request.POST['id']).exists():
                    resultado = {"result":"ok"}
                    west = PagoWester.objects.filter(id=request.POST['id'])[:1].get()
                    with open(SITE_ROOT+"/"+west.archivo.url,"rb") as image_file:
                        encoded_string = base64.b64encode(image_file.read())
                    resultado["imge64"] = encoded_string
                    return HttpResponse(json.dumps(resultado),content_type="application/json")
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
            except Exception as ex:
                return HttpResponse(json.dumps({"result":"excepcion"+str(ex)}),content_type="application/json")

        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
    elif 'o' in request.GET:
        action = request.GET['o']
        # if action == "wester":
        #     try:
        #         failed = open('base64.txt', 'r')
        #         contenido = failed.read()
        #         base = base64.b64decode(contenido)
        #         filename = 'some_image.jpg'  # I assume you have a way of picking unique filenames
        #         output_folder = os.path.join(MEDIA_ROOT,'wester',str(datetime.now().year),str(datetime.now().month).zfill(2),str(datetime.now().day).zfill(2))
        #         try:
        #             os.makedirs(output_folder)
        #         except :
        #             # return HttpResponse(json.dumps({'result':'bad'}),content_type="application/json")
        #             pass
        #         with open(os.path.join(output_folder,filename), 'wb') as f:
        #             f.write(base)
        #         archivoname = 'wester/'+str(datetime.now().year)+"/"+str(datetime.now().month).zfill(2)+"/"+str(datetime.now().day).zfill(2)+"/"+filename
        #         wester = PagoWester(inscripcion_id=84,archivo = archivoname,fecha=datetime.now())
        #         wester.save()
        #         print(contenido)
        #     except Exception as e:
        #         return HttpResponse(json.dumps({"result":"excepcion"+str(e)}),content_type="application/json")
        # elif action == "existecod":
        #     try:
        #         if PagoWester.objects.filter(codigo=request.GET['busqueda']).exists():
        #             return HttpResponse(json.dumps({"result":"badg"}),content_type="application/json")
        #         return HttpResponse(json.dumps({"result":"okg"}),content_type="application/json")
        #     except Exception as ex:
        #         return HttpResponse(json.dumps({"result":"excepcion"+str(ex)}),content_type="application/json")
        #
        # elif action == "busquewester":
        #     try:
        #         if PagoWester.objects.filter(inscripcion__id=request.GET["idinscrip"]).exists():
        #             resultado = {"result":"ok"}
        #             wester=[]
        #             for west in PagoWester.objects.filter(inscripcion__id=request.GET["idinscrip"]):
        #                 wester.append({"inscripcion":west.inscripcion.persona.nombre_completo(),"archivo":os.path.join(MEDIA_ROOT,west.archivo.url),"codigo":west.codigo,
        #                                "datos":str(west.datos),"identificacion":str(west.identificacion),"nombre":str(west.nombre),"direccion":str(west.direccion),
        #                                "telefono":str(west.telefono),"email":str(west.email),"fecha":str(west.fecha.date())})
        #             resultado["wester"] = wester
        #             return HttpResponse(json.dumps(resultado),content_type="application/json")
        #         return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
        #     except Exception as ex:
        #         return HttpResponse(json.dumps({"result":"excepcion"+str(ex)}),content_type="application/json")
        #
        # elif action == "imagenwester":
        #     try:
        #         if PagoWester.objects.filter(id=7).exists():
        #             resultado = {"result":"ok"}
        #             wester=[]
        #             west = PagoWester.objects.filter(id=7)[:1].get()
        #             with open(SITE_ROOT+"/"+west.archivo.url,"rb") as image_file:
        #                 encoded_string = base64.b64encode(image_file.read())
        #             resultado["imge64"] = encoded_string
        #             return HttpResponse(json.dumps(resultado),content_type="application/json")
        #         return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
        #     except Exception as ex:
        #         return HttpResponse(json.dumps({"result":"excepcion"+str(ex)}),content_type="application/json")
        # if action == 'login':
        #     try:
        #         user = authenticate(username=string.lower(request.GET['user']), password=request.GET['password'])
        #         if user is not None:
        #             if not user.is_active:
        #                 return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
        #             else:
        #                 if Persona.objects.filter(usuario=user).count()>0:
        #                     persona = Persona.objects.get(usuario=user)
        #                     if Inscripcion.objects.filter(persona=persona).exists():
        #                         inscripcion = Inscripcion.objects.filter(persona=persona)[:1].get()
        #                         rubros = Rubro.objects.filter(inscripcion=inscripcion).order_by('cancelado','fechavence')
        #                         notif = 0
        #                         for rubro in rubros:
        #                             if rubro.vencido():
        #                                 notif = notif + 1
        #                                 break
        #                         if inscripcion.matricula_set.filter(nivel__periodo__activo=True, nivel__cerrado=False).exists():
        #                             matricula = inscripcion.matricula_set.filter(nivel__periodo__activo=True, nivel__cerrado=False)[:1].get()
        #                             semana = ['Lunes','Martes','Miercoles','Jueves','Viernes', 'Sabado', 'Domingo']
        #                         sesiones = Sesion.objects.all()
        #                         hoy = datetime.now().date()
        #
        #
        #                         diasemana = ""
        #                         sesione = []
        #                         seccionestudi = ""
        #
        #
        #                         clases = Clase.objects.filter(materia__nivel__periodo__activo=True, materia__nivel__cerrado=False, materia__materiaasignada__matricula__inscripcion=inscripcion, materia__inicio__lte=hoy, materia__fin__gte=hoy).order_by('materia__inicio')
        #                         clasespm = [(x, x.materia.profesormateria_set.filter(desde__lte=hoy, hasta__gte=hoy)[:1].get() if x.materia.profesormateria_set.filter(desde__lte=hoy, hasta__gte=hoy).exists() else None) for x in clases]
        #                         horario = []
        #                         band = 0
        #
        #                         for sesion in sesiones:
        #
        #                             seccion =  str(sesion)
        #
        #
        #                             # for dia in sesion.semana():
        #                             turnos = []
        #                             for turno in sesion.turnos():
        #                                 for i in clasespm:
        #                                     if i[1]:
        #                                         if (i[0].dia == int(datetime.now().strftime("%w")) or (i[0].dia == 7 and int(datetime.now().strftime("%w")) == 0)) and i[0].turno.id == turno.id:
        #                                             notif = notif + 1
        #                                             band = 1
        #                                             break
        #                                 if band != 0:
        #                                     break
        #                             if band != 0:
        #                                 break
        #                         else:
        #                             matricula = inscripcion.matricula_set.filter(nivel__periodo__activo=True, nivel__cerrado=True)[:1].get()
        #
        #
        #                         inscripcion = Inscripcion.objects.filter(persona=persona)[:1].get()
        #                         resultado = {"result":"ok"}
        #                         lista = [{"idinscrip": inscripcion.id,"cedula": persona.cedula,"nombre": persona.nombre_completo().encode("ascii","ignore"),
        #                                  "imagen": persona.foto().foto.url if persona.foto() else "","carrera":str(matricula.nivel.carrera),"notif":notif}]
        #                         resultado['lista'] = lista
        #                         return HttpResponse(json.dumps(resultado),content_type="application/json")
        #
        #
        #                 return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
        #         else:
        #             return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
        #     except Exception as ex:
        #         return HttpResponse(json.dumps({"result":"excepcion"+str(ex)}),content_type="application/json")
        # elif action == 'cronograma':
        #     try:
        #         if Inscripcion.objects.filter(id=request.GET['id']).exists():
        #             inscripcion = Inscripcion.objects.get(id=request.GET['id'])
        #             #Comprobar que el alumno este matriculado
        #             if inscripcion.matriculado():
        #
        #                 matricula = inscripcion.matricula_set.filter(nivel__periodo__activo=True, nivel__cerrado=False)[:1].get()
        #                 materiasAsignadas = matricula.materiaasignada_set.all().order_by('materia__inicio')
        #                 resultado = {"result":"ok"}
        #                 matri = [{"nombre": str(matricula.inscripcion),"carrera": str(matricula.nivel.carrera),
        #                          "nivel": str(matricula.nivel.nivelmalla) +" - "+ matricula.nivel.paralelo +" ("+  str(matricula.nivel.sesion) +" )",
        #                          "periodo":str(matricula.nivel.periodo)}]
        #                 resultado['matricula'] = matri
        #                 mateasigna = []
        #
        #                 cont = 0
        #                 bandprof = 0
        #                 contarmateria = 0
        #                 bandeposcio = 0
        #                 if materiasAsignadas:
        #                     for maasig in materiasAsignadas:
        #                         asignatura = maasig.materia.identificacion +" - " if maasig.materia.identificacion else ""
        #                         aprobada = "MATERIA YA CURSADA" if maasig.materia.pasada_fecha() else ""
        #                         clasesasig = []
        #                         canthorario = ""
        #                         for clase in maasig.materia.clase_set.all().order_by("dia"):
        #                             canthorario = canthorario + clase.dia_semana() +" - (" + str(clase.turno.comienza) + " a " + str(clase.turno.termina) +" )" + clase.aula.nombre
        #                             clasesasig.append({"clase": clase.dia_semana() +" - (" + str(clase.turno.comienza) + " a " + str(clase.turno.termina) +" ) Aula:"+clase.aula.nombre })
        #                         profesor = []
        #
        #                         posicio=""
        #                         profeaux=""
        #                         profeprin=""
        #                         profeaux2=""
        #                         profeprin2=""
        #
        #                         if maasig.materia.profesormateria_set.count():
        #                             for profesormateria in maasig.materia.profesores_materia():
        #                                 if profesormateria.profesor_aux:
        #                                     profeaux = profesormateria.profesor_auxiliar().persona.nombre_completo()
        #                                 else:
        #                                     profeprin = profesormateria.profesor.persona.nombre_completo()
        #
        #                         asignatura1 = maasig.materia.identificacion +" - " if maasig.materia.identificacion else ""
        #                         asignatura1 = asignatura1 + elimina_tildes(maasig.materia.asignatura)
        #                         for maasig2 in materiasAsignadas:
        #
        #                             asignatura2 = maasig2.materia.identificacion +" - " if maasig2.materia.identificacion else ""
        #                             asignatura2 = asignatura2 + elimina_tildes(maasig2.materia.asignatura)
        #
        #                             if maasig2.materia.profesormateria_set.count():
        #                                 for profesormateria in maasig2.materia.profesores_materia():
        #                                     if profesormateria.profesor_aux:
        #                                         profeaux2 = profesormateria.profesor_auxiliar().persona.nombre_completo()
        #                                     else:
        #                                         profeprin2 = profesormateria.profesor.persona.nombre_completo()
        #                             canthorario2 = ""
        #                             for clase2 in maasig2.materia.clase_set.all().order_by("dia"):
        #                                 canthorario2 = canthorario2 + clase2.dia_semana() +" - (" + str(clase2.turno.comienza) + " a " + str(clase2.turno.termina) +" )" + clase2.aula.nombre
        #
        #                             if maasig.materia.clase_set.all().count() <= maasig2.materia.clase_set.all().count() :
        #
        #                                 if maasig.materia.clase_set.all().count() == maasig2.materia.clase_set.all().count():
        #                                     if  cont == 0 and maasig.materia != maasig2.materia:
        #                                         if len(profeaux)+len(profeprin)+len(asignatura1)+len(canthorario) >= len(profeaux2)+len(profeprin2)+len(asignatura2)+len(canthorario2):
        #                                             posicio = ""
        #                                             bandprof = 1
        #                                         else:
        #                                             posicio = "style='position: absolute; top: 0;'"
        #                                             if  cont == 0:
        #                                                 bandprof = 0
        #                                             break
        #                                     else:
        #                                         if bandprof == 1 and maasig.materia == maasig2.materia:
        #                                             if len(profeaux)+len(profeprin)+len(asignatura1)+len(canthorario) >= len(profeaux2)+len(profeprin2)+len(asignatura2)+len(canthorario2):
        #                                                 posicio = ""
        #                                                 bandprof = 0
        #                                         else:
        #                                             posicio = "style='position: absolute; top: 0;'"
        #
        #                                 else:
        #                                     posicio = "style='position: absolute; top: 0;'"
        #                                     break
        #                             else:
        #                                 # if maasig.materia.clase_set.all().count() > maasig2.materia.clase_set.all().count() :
        #                                 #     if len(profeaux)+len(profeprin)+len(asignatura1) >= len(profeaux2)+len(profeprin2)+len(asignatura2):
        #                                 posicio = ""
        #                                 bandprof = 2
        #                         if bandprof != 0:
        #                             cont= cont + 1
        #
        #                         if maasig.materia.profesormateria_set.count():
        #                             for profesormateria in maasig.materia.profesores_materia():
        #                                 if profesormateria.profesor_aux:
        #                                     profesor.append({"profesor": profesormateria.profesor_auxiliar().persona.nombre_completo(),"tipoprofe": str(profesormateria.segmento) +" ["+ str(profesormateria.desde) +" al "+str(profesormateria.hasta)+"]" })
        #                                 else:
        #                                     profesor.append({"profesor": profesormateria.profesor.persona.nombre_completo(),"tipoprofe": str(profesormateria.segmento) +" ["+ str(profesormateria.desde) +" al "+str(profesormateria.hasta)+"]" })
        #                         if posicio == "":
        #                             bandeposcio = 1
        #                         contarmateria = contarmateria + 1
        #                         if contarmateria == materiasAsignadas.count() and bandeposcio == 0:
        #                             posicio = ""
        #                         mateasigna.append({'asignatura': asignatura + elimina_tildes(maasig.materia.asignatura), 'aprobada': aprobada,
        #                                            'horas': maasig.materia.horas,'creditos': maasig.materia.creditos,
        #                                            'inicio': str(maasig.materia.inicio),'fin': str(maasig.materia.fin),"profesor":profesor,"posicio":posicio,"clasesasig":clasesasig })
        #
        #                     resultado['materiasasignadas'] = mateasigna
        #                     return HttpResponse(json.dumps(resultado),content_type="application/json")
        #
        #         return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
        #
        #     except Exception as ex:
        #         return HttpResponse(json.dumps({"result":"excepcion"+str(ex)}),content_type="application/json")
        # elif action == 'materia':
        #     try:
        #         if Inscripcion.objects.filter(id=request.GET['id']).exists():
        #             inscripcion = Inscripcion.objects.get(id=request.GET['id'])
        #
        #
        #             #Comprobar que el alumno este matriculado
        #             if inscripcion.matriculado():
        #
        #                 matricula = inscripcion.matricula_set.filter(nivel__periodo__activo=True, nivel__cerrado=False)[:1].get()
        #                 materiasAsignadas = matricula.materiaasignada_set.all().order_by('materia__inicio')
        #                 resultado = {"result":"ok"}
        #                 matri = [{"nombre": str(matricula.inscripcion),"carrera": str(matricula.nivel.carrera),
        #                          "nivel": str(matricula.nivel.nivelmalla) +" - "+ matricula.nivel.paralelo +" ("+  str(matricula.nivel.sesion) +" )",
        #                          "periodo":str(matricula.nivel.periodo)}]
        #                 resultado['matricula'] = matri
        #                 mateasigna = []
        #
        #                 cont = 0
        #                 bandprof = 0
        #                 if materiasAsignadas:
        #                     for maasig in materiasAsignadas:
        #                         asignatura = maasig.materia.identificacion  +" - " if maasig.materia.identificacion else ""
        #
        #                         codigevalua1 =" - <span class='tips' title='"+str(maasig.evaluacion().cod1.nombre)+"'>["+ str(maasig.evaluacion().cod1.id) +"]</span>"  if maasig.evaluacion().n1 and maasig.evaluacion().cod1 else ""
        #                         codigevalua2 =" - <span class='tips' title='"+str(maasig.evaluacion().cod2.nombre)+"'>["+ str(maasig.evaluacion().cod2.id) +"]</span>" if maasig.evaluacion().n2 and maasig.evaluacion().cod2 else ""
        #                         codigevalua3 =" - <span class='tips' title='"+str(maasig.evaluacion().cod3.nombre)+"'>["+ str(maasig.evaluacion().cod3.id) +"]</span>" if maasig.evaluacion().n3 and maasig.evaluacion().cod3 else ""
        #                         codigevalua4 =" - <span class='tips' title='"+str(maasig.evaluacion().cod4.nombre)+"'>["+ str(maasig.evaluacion().cod4.id) +"]</span>" if maasig.evaluacion().n4 and maasig.evaluacion().cod4 else ""
        #
        #                         profesor=[]
        #                         cantprofesor=""
        #                         if maasig.materia.profesormateria_set.count():
        #                             for profesormateria in maasig.materia.profesores_materia():
        #                                     if profesormateria.profesor_aux:
        #                                         cantprofesor = cantprofesor + profesormateria.profesor_auxiliar().persona.nombre_completo()+str(profesormateria.segmento)
        #                                         profesor.append({"profesor": profesormateria.profesor_auxiliar().persona.nombre_completo(),"tipoprofe": str(profesormateria.segmento) })
        #                                     else:
        #                                         cantprofesor = cantprofesor + profesormateria.profesor.persona.nombre_completo()+str(profesormateria.segmento)
        #                                         profesor.append({"profesor": profesormateria.profesor.persona.nombre_completo(),"tipoprofe": str(profesormateria.segmento)})
        #
        #                         nfinal = ""
        #                         if maasig.evaluacion().nota_final() < NOTA_PARA_APROBAR or maasig.porciento_asistencia() < ASIST_PARA_APROBAR:
        #                             nfinal = "<span class='badge badge-error bigger'>"+ str(maasig.evaluacion().nota_final()) +"</span>"
        #                         else:
        #                             nfinal = "<span class='badge badge-success bigger'>"+ str(maasig.evaluacion().nota_final()) +"</span>"
        #
        #                         asistencia = ""
        #                         if maasig.porciento_asistencia < ASIST_PARA_SEGUIR:
        #                             asistencia = "<span style='color: #dc143c;'><b>"+ str(maasig.porciento_asistencia())  +"%</b></span>"
        #                         elif maasig.porciento_asistencia >= ASIST_PARA_SEGUIR and maasig.porciento_asistencia < ASIST_PARA_APROBAR:
        #                             asistencia = "<span style='color: #daa520;'><b>"+ str(maasig.porciento_asistencia())  +"%</b></span>"
        #                         elif maasig.porciento_asistencia >= ASIST_PARA_APROBAR:
        #                             asistencia = "<span style='color:#006400;'><b>"+ str(maasig.porciento_asistencia())  +"%</b></span>"
        #
        #
        #                         estado = ""
        #                         if maasig.evaluacion().estado_id != 1:
        #                             estado = "<span class='label  label-info'>"+ maasig.evaluacion().estado.nombre +"</span>"
        #                         elif maasig.evaluacion().estado_id == 2:
        #                             estado = "<span style='color: #dc143c;'><b>"+ maasig.evaluacion().estado.nombre +"</b></span>"
        #                             if maasig.notafinal < NOTA_PARA_APROBAR:
        #                                 estado = estado + "<span style='color: #dc143c;'><b> (AS)</b></span>"
        #                             if maasig.porciento_asistencia() < ASIST_PARA_APROBAR:
        #                                 estado = estado + "<span style='color: #dc143c;'><b> (AS)</b></span>"
        #
        #
        #                         posicio=""
        #                         for maasig2 in materiasAsignadas:
        #                             asignatura2 = maasig2.materia.identificacion  +" - " if maasig2.materia.identificacion else ""
        #                             cantprofesor2 = ""
        #                             if maasig2.materia.profesormateria_set.count():
        #                                 for profesormateria2 in maasig2.materia.profesores_materia():
        #                                     if profesormateria2.profesor_aux:
        #                                         cantprofesor2 = cantprofesor2 + profesormateria2.profesor_auxiliar().persona.nombre_completo()+str(profesormateria2.segmento)
        #                                     else:
        #                                         cantprofesor2 = cantprofesor2 + profesormateria2.profesor.persona.nombre_completo()+str(profesormateria2.segmento)
        #
        #                             if len(asignatura + elimina_tildes(maasig.materia.asignatura))+len(cantprofesor) <= len(asignatura2 + elimina_tildes(maasig2.materia.asignatura))+len(cantprofesor2) :
        #
        #                                 if len(asignatura + elimina_tildes(maasig.materia.asignatura))+len(cantprofesor) == len(asignatura2 + elimina_tildes(maasig2.materia.asignatura))+len(cantprofesor2):
        #                                     if  cont == 0 and maasig.materia != maasig2.materia:
        #                                         posicio = ""
        #                                         bandprof = 1
        #                                     else:
        #                                         if bandprof == 1 and maasig.materia == maasig2.materia:
        #                                             posicio = ""
        #                                         else:
        #                                             posicio = "style='position: absolute; top: 0;'"
        #
        #                                 else:
        #                                     posicio = "style='position: absolute; top: 0;'"
        #                                     break
        #                             else:
        #                                 if len(asignatura + elimina_tildes(maasig.materia.asignatura)) > len(asignatura2 + elimina_tildes(maasig2.materia.asignatura)) or maasig.materia.profesormateria_set.count() > maasig2.materia.profesormateria_set.count() :
        #                                     posicio = ""
        #                                     bandprof = 1
        #                         cont= cont +1
        #
        #                         mateasigna.append({'asignatura': asignatura + elimina_tildes(maasig.materia.asignatura),
        #                                            'inicio': str(maasig.materia.inicio),'fin': str(maasig.materia.fin),"profesor":profesor,
        #                                            'nota1':str(maasig.evaluacion().n1),'codigevalua1':codigevalua1,
        #                                            'nota2':str(maasig.evaluacion().n2),'codigevalua2':codigevalua2,
        #                                            'nota3':str(maasig.evaluacion().n3),'codigevalua3':codigevalua3,
        #                                            'nota4':str(maasig.evaluacion().n4),'codigevalua4':codigevalua4,
        #                                            'examen':str(maasig.evaluacion().examen),'recuperacion':str(maasig.evaluacion().recuperacion),
        #                                            'nfinal':nfinal,'asistencia':asistencia,'estado':estado,"posicio":posicio})
        #
        #                     resultado['materiasasignadas'] = mateasigna
        #                     return HttpResponse(json.dumps(resultado),content_type="application/json")
        #         return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
        #
        #     except Exception as ex:
        #         return HttpResponse(json.dumps({"result":"excepcion"+str(ex)}),content_type="application/json")
        # elif action == 'rubro':
        #     try:
        #         if Inscripcion.objects.filter(id=request.GET['id']).exists():
        #             inscripcion = Inscripcion.objects.get(id=request.GET['id'])
        #             matricula = inscripcion.matricula_set.filter(nivel__periodo__activo=True, nivel__cerrado=False)[:1].get()
        #             resultado = {"result":"ok"}
        #             matri = [{"nombre": str(matricula.inscripcion),"carrera": str(matricula.nivel.carrera),
        #                          "nivel": str(matricula.nivel.nivelmalla) +" - "+ matricula.nivel.paralelo +" ("+  str(matricula.nivel.sesion) +" )",
        #                          "periodo":str(matricula.nivel.periodo)}]
        #             resultado['matricula'] = matri
        #             rubros = Rubro.objects.filter(inscripcion=inscripcion).order_by('cancelado','fechavence')
        #             total_rubros = rubros.aggregate(Sum('valor'))['valor__sum']
        #             total_pagado = sum([x.total_pagado() for x in rubros])
        #             total_adeudado = sum([x.adeudado() for x in rubros])
        #
        #             rubroslis=[]
        #             for rubro in rubros:
        #                 if rubro.vencido():
        #                     fecha =  "<span class='label label-danger'> Vencida el "+ str(rubro.fechavence) + "</span>"
        #                 else:
        #                     if rubro.fechavence < datetime.now().date():
        #                         fecha = "<span class='label label-warning'> Cancelado </span>"
        #                     else:
        #                         fecha = "<span class='label label-info'> Vence el "+ str(rubro.fechavence) + "</span>"
        #                 adeuda = ""
        #                 cancelado =  "<span class='label label-success'>Si</span>" if rubro.cancelado else "<span class='label label-important'>No</span>"
        #                 if rubro.adeudado():
        #                     adeuda = "<span class='label label-important bigger'>$"+ str(rubro.adeudado()) +"</span>" if rubro.vencido else "<span class='label label-success bigger'>"+ rubro.adeudado() + "</span>"
        #                 rubroslis.append({'nombre':rubro.nombre(),'fecha':fecha,'valor':str(rubro.valor),'pagado':str(rubro.total_pagado()),
        #                                   'adeuda':adeuda,'cancelado':cancelado})
        #
        #             totales = [{"total_rubros":str(total_rubros),"total_pagado":str(total_pagado),"total_adeudado":str(total_adeudado)}]
        #
        #             resultado['matricula'] = matri
        #             resultado['rubros'] = rubroslis
        #             resultado['totales'] = totales
        #
        #             return HttpResponse(json.dumps(resultado),content_type="application/json")
        #         return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
        #
        #     except Exception as ex:
        #         return HttpResponse(json.dumps({"result":"excepcion"+str(ex)}),content_type="application/json")
        # elif action == 'horario':
        #     try:
        #         if Inscripcion.objects.filter(id=request.GET['id']).exists():
        #             inscripcion = Inscripcion.objects.get(id=request.GET['id'])
        #
        #             if inscripcion.matriculado():
        #                 materias = Materia.objects.filter(materiaasignada__matricula__inscripcion=inscripcion)
        #
        #                 # periodo = request.session['periodo']
        #                 matricula = inscripcion.matricula_set.filter(nivel__periodo__activo=True, nivel__cerrado=False)
        #                 # matricula = inscripcion.matricula_set.filter(nivel__periodo=periodo)
        #
        #                 resultado = {"result":"ok","inscripcion":str(inscripcion),"periodo":str(matricula[0].nivel.periodo),"paralelo":str(matricula[0].nivel)}
        #
        #                 semana = ['Lunes','Martes','Miercoles','Jueves','Viernes', 'Sabado', 'Domingo']
        #                 sesiones = Sesion.objects.all()
        #
        #                 #hoy = datetime.now().date()
        #                 hoy = datetime.now().date()
        #
        #                 clases = Clase.objects.filter(materia__nivel__periodo__activo=True, materia__nivel__cerrado=False, materia__materiaasignada__matricula__inscripcion=inscripcion, materia__inicio__lte=hoy, materia__fin__gte=hoy).order_by('materia__inicio')
        #                 clasespm = [(x, x.materia.profesormateria_set.filter(desde__lte=hoy, hasta__gte=hoy)[:1].get() if x.materia.profesormateria_set.filter(desde__lte=hoy, hasta__gte=hoy).exists() else None) for x in clases]
        #
        #
        #                 sesione = []
        #                 for sesion in sesiones:
        #
        #                     seccion =  str(sesion)
        #
        #                     horario = []
        #                     for dia in sesion.semana():
        #                         turnos = []
        #                         for turno in sesion.turnos():
        #                             for i in clasespm:
        #                                 if i[1]:
        #                                     if i[0].dia == dia[1] and i[0].turno.id == turno.id:
        #                                         if i[1].profesor_aux:
        #                                             profesor = i[1].profesor_auxiliar()
        #                                         else:
        #                                             profesor = i[1].profesor.persona.nombre_completo()
        #                                         asignat = "<div><span class='label label-danger'>"+ str(i[1].segmento) +"</span> " \
        #                                                      "<strong> "+ i[0].materia.nombre_completo() +"</strong><br/>" \
        #                                                      "<span class='larger label label-info'>" + str(i[1].desde) +" al "+ str(i[1].hasta) +"</span>" \
        #                                                      "<br>"+ profesor +"<br/>"+ str(i[0].materia.nivel.carrera) \
        #                                                      +"<br/>"+ str(i[0].materia.nivel.nivelmalla) +" - "+ str(i[0].materia.nivel.paralelo) +" " \
        #                                                      "en "+ str(i[0].materia.nivel.sede) +"<br/>Aula: "+ str(i[0].aula) +"<br/></div>"
        #                                         turnos.append({"turno": str(turno.turno),"comienza":str(turno.comienza),"termina":str(turno.termina),"asignatura":asignat})
        #                         if turnos:
        #                             horario.append({"dia": dia[0],"turnos":turnos})
        #                     if horario:
        #                         sesione.append({"sesiones":str(sesion),"horario":horario})
        #                 resultado['sesiones'] = sesione
        #                 return HttpResponse(json.dumps(resultado),content_type="application/json")
        #
        #         return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
        #
        #     except Exception as ex:
        #         return HttpResponse(json.dumps({"result":"excepcion"+str(ex)}),content_type="application/json")
        # elif action == 'notificacion':
        #     try:
        #         if Inscripcion.objects.filter(id=request.GET['id']).exists():
        #             inscripcion = Inscripcion.objects.get(id=request.GET['id'])
        #             matricula = inscripcion.matricula_set.filter(nivel__periodo__activo=True, nivel__cerrado=False)[:1].get()
        #             resultado = {"result":"ok"}
        #             matri = [{"nombre": str(matricula.inscripcion),"carrera": str(matricula.nivel.carrera),
        #                          "nivel": str(matricula.nivel.nivelmalla) +" - "+ matricula.nivel.paralelo +" ("+  str(matricula.nivel.sesion) +" )",
        #                          "periodo":str(matricula.nivel.periodo)}]
        #             resultado['matricula'] = matri
        #             hoy = datetime.now().date()
        #             rubros = Rubro.objects.filter(inscripcion=inscripcion,fechavence__lt=hoy,cancelado=False).order_by('cancelado','fechavence')
        #             total_rubros = rubros.aggregate(Sum('valor'))['valor__sum']
        #             total_pagado = sum([x.total_pagado() for x in rubros])
        #             total_adeudado = sum([x.adeudado() for x in rubros])
        #
        #             rubroslis=[]
        #             for rubro in rubros:
        #                 if rubro.vencido():
        #                     fecha =  "<span class='label label-danger'> Vencida el "+ str(rubro.fechavence) + "</span>"
        #                 else:
        #                     if rubro.fechavence < datetime.now().date():
        #                         fecha = "<span class='label label-warning'> Cancelado </span>"
        #                     else:
        #                         fecha = "<span class='label label-info'> Vence el "+ str(rubro.fechavence) + "</span>"
        #                 adeuda = ""
        #                 cancelado =  "<span class='label label-success'>Si</span>" if rubro.cancelado else "<span class='label label-important'>No</span>"
        #                 if rubro.adeudado():
        #                     adeuda = "<span class='label label-important bigger'>$"+ str(rubro.adeudado()) +"</span>" if rubro.vencido else "<span class='label label-success bigger'>"+ rubro.adeudado() + "</span>"
        #                 rubroslis.append({'nombre':rubro.nombre(),'fecha':fecha,'valor':str(rubro.valor),'pagado':str(rubro.total_pagado()),
        #                                   'adeuda':adeuda,'cancelado':cancelado})
        #
        #             totales = [{"total_rubros":str(total_rubros),"total_pagado":str(total_pagado),"total_adeudado":str(total_adeudado)}]
        #
        #             resultado['matricula'] = matri
        #             resultado['rubros'] = rubroslis
        #             resultado['totales'] = totales
        #             matricula = inscripcion.matricula_set.filter(nivel__periodo__activo=True, nivel__cerrado=False)[:1].get()
        #             materiasAsignadas = matricula.materiaasignada_set.all().order_by('materia__inicio')
        #             semana = ['Lunes','Martes','Miercoles','Jueves','Viernes', 'Sabado', 'Domingo']
        #             sesiones = Sesion.objects.all()
        #
        #
        #             diasemana = ""
        #             sesione = []
        #             seccionestudi = ""
        #
        #
        #             clases = Clase.objects.filter(materia__nivel__periodo__activo=True, materia__nivel__cerrado=False, materia__materiaasignada__matricula__inscripcion=inscripcion, materia__inicio__lte=hoy, materia__fin__gte=hoy).order_by('materia__inicio')
        #             clasespm = [(x, x.materia.profesormateria_set.filter(desde__lte=hoy, hasta__gte=hoy)[:1].get() if x.materia.profesormateria_set.filter(desde__lte=hoy, hasta__gte=hoy).exists() else None) for x in clases]
        #             horario = []
        #             for sesion in sesiones:
        #
        #                 seccion =  str(sesion)
        #
        #
        #                 # for dia in sesion.semana():
        #                 turnos = []
        #                 for turno in sesion.turnos():
        #                     for i in clasespm:
        #                         if i[1]:
        #                             if (i[0].dia == int(datetime.now().strftime("%w")) or (i[0].dia == 7 and int(datetime.now().strftime("%w")) == 0)) and i[0].turno.id == turno.id:
        #                                 for dia in sesion.semana():
        #                                    if i[0].dia == dia[1]:
        #                                       diasemana = dia[0]
        #                                       break
        #                                 seccionestudi = sesion
        #                                 if i[1].profesor_aux:
        #                                     profesor = i[1].profesor_auxiliar()
        #                                 else:
        #                                     profesor = i[1].profesor.persona.nombre_completo()
        #                                 asignat = "<div><span class='label label-danger'>"+ str(i[1].segmento) +"</span> " \
        #                                              "<strong> "+ i[0].materia.nombre_completo() +"</strong><br/>" \
        #                                              "<span class='larger label label-info'>" + str(i[1].desde) +" al "+ str(i[1].hasta) +"</span>" \
        #                                              "<br>"+ profesor +"<br/>"+ str(i[0].materia.nivel.carrera) \
        #                                              +"<br/>"+ str(i[0].materia.nivel.nivelmalla) +" - "+ str(i[0].materia.nivel.paralelo) +" " \
        #                                              "en "+ str(i[0].materia.nivel.sede) +"<br/>Aula: "+ str(i[0].aula) +"<br/></span></div>"
        #                                 turnos.append({"turno": str(turno.turno),"comienza":str(turno.comienza),"termina":str(turno.termina),"asignatura":asignat})
        #                 if turnos:
        #                     horario.append({"dia": diasemana,"turnos":turnos})
        #             if horario:
        #                 sesione.append({"sesiones":str(seccionestudi),"horario":horario})
        #             resultado['sesiones'] = sesione
        #
        #             return HttpResponse(json.dumps(resultado),content_type="application/json")
        #         return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
        #
        #     except Exception as ex:
        #         return HttpResponse(json.dumps({"result":"excepcion"+str(ex)}),content_type="application/json")
        # elif action == "record":
        #     try:
        #         if Inscripcion.objects.filter(id=request.GET['id']).exists():
        #             inscripcion = Inscripcion.objects.get(id=request.GET['id'])
        #             matricula = inscripcion.matricula_set.filter(nivel__periodo__activo=True, nivel__cerrado=False)[:1].get()
        #             resultado = {"result":"ok"}
        #             matri = [{"nombre": str(matricula.inscripcion),"carrera": str(matricula.nivel.carrera),
        #                          "nivel": str(matricula.nivel.nivelmalla) +" - "+ matricula.nivel.paralelo +" ("+  str(matricula.nivel.sesion) +" )",
        #                          "periodo":str(matricula.nivel.periodo)}]
        #             resultado['matricula'] = matri
        #             records = RecordAcademico.objects.filter(inscripcion=inscripcion).order_by('fecha')
        #             recordacadem = []
        #             recor = ""
        #             for record in records:
        #                 recor = "<tr><td style='width:90%;font-size:11;background:white'>"+ str(record.asignatura) +"<span class='label label-info'>"+ str(record.fecha) +"</span> </td><td class='"
        #                 nota = "red" if record.esta_suspensa() else "green"
        #                 recor = recor +"' style='width:5%;color:"+ nota +";font-size: 18;background:white'><b>"+ str(record.nota) +"</b></td><td class='"
        #                 asist = "green" if record.asistencia >= ASIST_PARA_APROBAR else "red"
        #                 recor = recor + "' style='width:5%;color: "+ asist +";font-size: 18;background:white'><b>"+ str(record.asistencia) +"</b></td></tr>"
        #                 recordacadem.append({"recor":recor})
        #             resultado['recordacadem'] = recordacadem
        #             return HttpResponse(json.dumps(resultado),content_type="application/json")
        #         return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
        #     except Exception as ex:
        #         return HttpResponse(json.dumps({"result":"excepcion"+str(ex)}),content_type="application/json")
        # elif action == "noticia":
        #     try:
        #         if Inscripcion.objects.filter(id=request.GET['id']).exists():
        #             inscripcion = Inscripcion.objects.get(id=request.GET['id'])
        #             hoy = datetime.now().date()
        #             noticias = Noticia.objects.filter(tipo__in=(1,2,4),desde__lte=hoy,hasta__gte=hoy)
        #             noticia = []
        #             resultado = {"result":"ok"}
        #             for noti in noticias:
        #                 noticia.append({"titulo":noti.titular,"cuerpo":noti.cuerpo})
        #             resultado["resultado"] = noticia
        #             return HttpResponse(json.dumps(resultado),content_type="application/json")
        #         return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
        #     except Exception as ex:
        #         return HttpResponse(json.dumps({"result":"excepcion"+str(ex)}),content_type="application/json")
        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
    return HttpResponse(json.dumps({"result":str(request)}),content_type="application/json")



def privacidad(request):
    return render(request ,"appmovil/privacidad.html" ,  data)