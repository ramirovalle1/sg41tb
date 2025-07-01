from datetime import datetime, date, timedelta
import json
import requests
from django.contrib.admin.models import ADDITION, LogEntry, CHANGE
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q, Sum
from django.forms.models import model_to_dict
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.utils.encoding import force_str
from decorators import secure_module
from settings import MODELO_EVALUACION, EVALUACION_TES,INSCRIPCION_CONDUCCION, MAXIMO_HORAS_CLASE, VALIDA_MAXIMO_HORAS,DOCENTE_POR_DEFINIR,TIPOSEGMENTO_TEORIA,TIPOSEGMENTO_PRACT
from sga.commonviews import addUserData, ip_client_address
from sga.forms import ClaseForm, ClaseNivelCerradoForm
from django.template.context import RequestContext
from sga.models import Periodo, Sede, Carrera, Nivel, Turno, Clase, Materia, Aula,ProfesorMateria, elimina_tildes, ViewHorarioDocente

@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    if request.method=='POST':
        action = request.POST['action']
        if action=='addclase':
            try:
                materia = Materia.objects.get(pk=request.POST['id_materia'])
                # Chequear que el profesor no colisione en esas mismas horas
                dia = int(request.POST['id_dia'])
                aula = Aula.objects.get(pk=request.POST['id_aula'])
                turno = Turno.objects.get(pk=request.POST['id_turno'])
                profesormateria = ProfesorMateria.objects.get(pk=request.POST['id_profesormateria'])

                if  request.POST['virtual']=='SI':
                    virtual=True
                else:
                    virtual=False
                profesoresmateria = materia.profesores_materia()
                otro_horario = []
                data={}
                horasclase = 0
                for pm in profesoresmateria:
                    if pm.profesor == profesormateria.profesor:
                    # materias_activas = Materia.objects.filter(
                    #     (Q(inicio__lte=pm.desde) & Q(fin__gte=pm.desde)) |
                    #     (Q(inicio__lte=pm.hasta) & Q(fin__gte=pm.hasta)) |
                    #     (Q(inicio__gte=pm.desde) & Q(fin__lte=pm.hasta)),
                    #     cerrado=False,
                    #     profesormateria__profesor=pm.profesor).exclude(id__in=[materia.id])

                        materias_activas = ProfesorMateria.objects.filter(
                            (Q(desde__lte=pm.desde) & Q(hasta__gte=pm.desde)) |
                            (Q(desde__lte=pm.hasta) & Q(hasta__gte=pm.hasta)) |
                            (Q(desde__gte=pm.desde) & Q(hasta__lte=pm.hasta)),
                            # materia__cerrado=False, profesor=pm.profesor).exclude(materia__id__in=[materia.id]).values('materia')
                            #OCastillo 06-10-2023 se excluye docente por definir
                            materia__cerrado=False, profesor=pm.profesor,aceptacion=True).exclude(profesor__id=DOCENTE_POR_DEFINIR).exclude(materia__id__in=[materia.id]).values('materia')

                        clases = Clase.objects.filter(
                                    (Q(turno__comienza__lte=turno.comienza) & Q(turno__termina__gte=turno.comienza)) |
                                    (Q(turno__comienza__lte=turno.termina) & Q(turno__termina__gte=turno.termina)) |
                                    (Q(turno__comienza__gte=turno.comienza) & Q(turno__termina__lte=turno.termina)),
                                    materia__in=materias_activas, dia=dia)

                        if materia.inicio < date(materia.inicio.year,materia.inicio.month,22):
                            dia2 = datetime(materia.inicio.year,materia.inicio.month,22)- timedelta(days=30)
                            inicio = datetime(dia2.year,dia2.month,22)
                            fin = datetime(materia.inicio.year,materia.inicio.month,21)
                        else:
                            dia2 = date(materia.inicio.year,materia.inicio.month,22) + timedelta(days=30)
                            inicio =datetime(materia.inicio.year,materia.inicio.month,22)
                            fin = datetime(dia2.year,dia2.month,21)
                        dia2 = 7

                        if clases.count()>0:
                            otro_horario.append((str(pm.profesor)+" ["+str(pm.segmento)+": "+pm.desde.strftime("%d-%m-%Y")+" a "+pm.hasta.strftime("%d-%m-%Y")+"]", [str(x) for x in clases]))
                    else:
                        pass
                    # horarios_online = []
                    # if pm.profesor.id != DOCENTE_POR_DEFINIR:
                    #     if pm.profesor.persona.cedula:
                    #         identificacion = pm.profesor.persona.cedula
                    #     else:
                    #         identificacion = pm.profesor.persona.pasaporte
                    #     materias_activas_online = requests.get('https://sgaonline.itb.edu.ec/api',params={'a':'materias_activas_sga', 'desde':pm.desde, 'hasta':pm.hasta, 'profesor':identificacion , 'dia':dia, 'turno_comienza':turno.comienza, 'turno_termina':turno.termina},verify=False)
                    #     # materias_activas_online = requests.get('http://127.0.0.1:8005/api',params={'a':'materias_activas_sga', 'desde':pm.desde, 'hasta':pm.hasta, 'profesor':identificacion, 'dia':dia, 'turno_comienza':turno.comienza, 'turno_termina':turno.termina},verify=False)
                    #     if materias_activas_online.status_code == 200:
                    #         materias_activas_online = materias_activas_online.json()
                    #         if materias_activas_online['result']=='ok':
                    #             horarios_online.append([ pm.profesor.persona.nombre_completo_inverso(), materias_activas_online['clases']])

                    # if pm.profesor.persona.cedula:
                    #     clases_externas = ViewHorarioDocente.objects.filter(
                    #                                                         Q((Q(desde__lte=pm.desde) & Q(hasta__gte=pm.desde)) |
                    #                                                           (Q(desde__lte=pm.hasta) & Q(hasta__gte=pm.hasta)) |
                    #                                                           (Q(desde__gte=pm.desde) & Q(hasta__lte=pm.hasta))),
                    #                                                         (Q(turno_comienza__lte=turno.comienza) & Q(turno_termina__gte=turno.comienza)) |
                    #                                                         (Q(turno_comienza__lte=turno.termina) & Q(turno_termina__gte=turno.termina)) |
                    #                                                         (Q(turno_comienza__gte=turno.comienza) & Q(turno_termina__lte=turno.termina)),
                    #                                                         cedula=pm.profesor.persona.cedula, dia=dia)
                    # else:
                    #     clases_externas = ViewHorarioDocente.objects.filter(
                    #                                                         Q((Q(desde__lte=pm.desde) & Q(hasta__gte=pm.desde)) |
                    #                                                           (Q(desde__lte=pm.hasta) & Q(hasta__gte=pm.hasta)) |
                    #                                                           (Q(desde__gte=pm.desde) & Q(hasta__lte=pm.hasta))),
                    #                                                         (Q(turno_comienza__lte=turno.comienza) & Q(turno_termina__gte=turno.comienza)) |
                    #                                                         (Q(turno_comienza__lte=turno.termina) & Q(turno_termina__gte=turno.termina)) |
                    #                                                         (Q(turno_comienza__gte=turno.comienza) & Q(turno_termina__lte=turno.termina)),
                    #                                                         pasaporte=pm.profesor.persona.pasaporte, dia=dia)

                    otro_horario_externos = []
                    # if clases_externas:
                    #     for ce in clases_externas:
                    #         otro_horario_externos.append(["COLISION DE HORARIO EXTERNO: "+ce.lugar.upper(), ce.asignatura+" ("+ce.grupo+") - del "+str(ce.desde)+" al "+str(ce.hasta)+" de "+str(ce.turno_comienza)+" a "+str(ce.turno_termina)])

                force = request.POST['force']=='SI'
                if force or (not otro_horario) and (len(otro_horario_externos)==0):
                    clase = Clase(materia=materia,
                            turno=turno,
                            aula=aula,
                            dia=dia,
                            virtual=virtual,
                            profesormateria=profesormateria)
                    clase.save()
                    b=0
                    for profesor in ProfesorMateria.objects.filter(materia=materia).distinct('profesor').values('profesor'):
                        if b == 0:
                            horasclase = 0
                            for pm in ProfesorMateria.objects.filter(profesor__id= profesor['profesor']):
                                horasclase = horasclase + pm.materia.horas_materia_rangofecha(pm,inicio,fin)[0]
                            if horasclase > MAXIMO_HORAS_CLASE and VALIDA_MAXIMO_HORAS :
                                data = {'result': 'clase', 'horasclase':(str(elimina_tildes(pm.profesor.persona.nombre_completo())) + " " + str(horasclase) ),'inicio':str(inicio.date()),'fin':str(fin.date())}
                                b = 1
                                clase.delete()
                    if b == 0 or not VALIDA_MAXIMO_HORAS:
                        if horasclase > MAXIMO_HORAS_CLASE and not VALIDA_MAXIMO_HORAS and MAXIMO_HORAS_CLASE>0:
                            data = {'result': 'claseok', 'horasclase':(str(elimina_tildes(pm.profesor.persona.nombre_completo())) + " " + str(horasclase) ),'inicio':str(inicio.date()),'fin':str(fin.date())}
                        else:
                            data = {'result': 'ok',}

                        #Obtain client ip address
                        client_address = ip_client_address(request)

                        # Log de ADICIONAR HORARIO CLASE
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(clase).pk,
                            object_id       = clase.id,
                            object_repr     = force_str(clase),
                            action_flag     = ADDITION,
                            change_message  = 'Adicionado Horario Clase (' + client_address + ')' )
                else:
                    data = {'result': 'bad', 'otros_horarios': otro_horario, 'otros_horarios_externo':otro_horario_externos}

                return HttpResponse(json.dumps(data),content_type="application/json")
            except Exception as e:
                print(e)
                return HttpResponse(json.dumps({"result": "bad", 'otros_horarios_externo':otro_horario_externos}),content_type="application/json")


        elif action =='consulta_profesor':
                data = {}
                docentes = []
                profesormateria=None
                try:
                    turno=Turno.objects.filter(pk=request.POST['id'])[:1].get()
                    if turno.practica:
                        profesormateria=ProfesorMateria.objects.filter(materia=request.POST['materia'],segmento__id=TIPOSEGMENTO_PRACT)
                    else:
                        profesormateria=ProfesorMateria.objects.filter(materia=request.POST['materia'],segmento__id=TIPOSEGMENTO_TEORIA)
                    for prof in profesormateria:
                        docentes.append({'id':prof.id,'nombre':elimina_tildes(prof.profesor.persona.nombre_completo_inverso()),'materia':elimina_tildes(prof.materia.asignatura.nombre),'segmento':elimina_tildes(prof.segmento.descripcion),'desde':str(prof.desde),'hasta':str(prof.hasta)})
                    data['result'] = 'ok'
                    data['docente']=docentes
                    return HttpResponse(json.dumps({"result":"ok","docente":docentes}),content_type="application/json")
                except Exception as e:
                    data['result']  = 'bad'
                    return HttpResponse(json.dumps(data), content_type="application/json")


        elif action =='consulta_materia':
                data = {}
                docentes = []
                profesormateria=None
                try:
                    materia=Materia.objects.filter(pk=request.POST['id'])[:1].get()
                    if 'turno' in request.POST:
                        turno=Turno.objects.filter(pk=request.POST['turno'])[:1].get()
                        if turno.practica:
                            profesormateria=ProfesorMateria.objects.filter(materia=materia,segmento__id=TIPOSEGMENTO_PRACT)
                        else:
                            profesormateria=ProfesorMateria.objects.filter(materia=materia,segmento__id=TIPOSEGMENTO_TEORIA)
                    else:
                        profesormateria=ProfesorMateria.objects.filter(materia=materia)
                    for prof in profesormateria:
                        docentes.append({'id':prof.id,'nombre':elimina_tildes(prof.profesor.persona.nombre_completo_inverso()),'materia':elimina_tildes(prof.materia.asignatura.nombre),'segmento':elimina_tildes(prof.segmento.descripcion),'desde':str(prof.desde),'hasta':str(prof.hasta)})
                    data['result'] = 'ok'
                    data['docente']=docentes
                    return HttpResponse(json.dumps({"result":"ok","docente":docentes}),content_type="application/json")
                except Exception as e:
                    data['result']  = 'bad'
                    return HttpResponse(json.dumps(data), content_type="application/json")


        elif action=='editclase':
            f = ClaseForm(request.POST)
            if f.is_valid():
                clase = Clase.objects.get(pk=request.POST['id'])
                clase.materia = f.cleaned_data['materia']
                clase.turno = f.cleaned_data['turno']
                clase.aula = f.cleaned_data['aula']
                clase.virtual =  f.cleaned_data['virtual']
                clase.dia = f.cleaned_data['dia']
                clase.profesormateria = f.cleaned_data['profesormateria']
                clase.save()

                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de EDITAR HORARIO CLASE
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(clase).pk,
                    object_id       = clase.id,
                    object_repr     = force_str(clase),
                    action_flag     = CHANGE,
                    change_message  = 'Modificado Horario Clase (' + client_address + ')'  )

                return HttpResponseRedirect("/horarios?action=horario&id="+str(clase.materia.nivel_id))
            else:
                return HttpResponseRedirect("/horarios?action=editclase&id="+str(request.POST['id']))

        elif action=='editaula':
            try:
                clase = Clase.objects.get(pk=request.POST['id'])
                clase.aula_id = int(request.POST['aula'])
                clase.save()
                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de EDITAR AULA EN CLASE NIVEL CERRADO
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(clase).pk,
                    object_id       = clase.id,
                    object_repr     = force_str(clase),
                    action_flag     = CHANGE,
                    change_message  = 'Cambio de Aula en Clase Nivel Cerrado (' + client_address + ')'  )

                return HttpResponseRedirect("/horarios?action=horario&id="+str(clase.materia.nivel_id))
            except Exception as e:
                print(e)
                return HttpResponseRedirect("/horarios?action=editaula&id="+str(request.POST['id']))

        return HttpResponseRedirect("/horarios")
    else:
        data = {'title': 'Horarios de Clases del Periodo'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='horario':
                ret = None
                # Editar un Horario
                data['title'] = 'Horario de Nivel Academico'
                nivel = Nivel.objects.get(pk=request.GET['id'])
                data['nivel'] = nivel
                if 'ret' in request.GET:
                    ret = request.GET['ret']
                # Chequear que todos tengan su profesor
                sinprofesor = [x for x in nivel.materia_set.all() if x.profesores_materia().count()==0]
                if len(sinprofesor):
                    if INSCRIPCION_CONDUCCION and len(sinprofesor) == 1:
                        data['activo'] = True
                    else:
                        data['activo'] = False
                    # data['activo'] = False
                else:
                    data['activo'] = True

                data['semana'] = ['Lunes','Martes','Miercoles','Jueves','Viernes','Sabado','Domingo']
                data['turnos'] = Turno.objects.filter(sesion=data['nivel'].sesion).order_by('turno')
                data['clases'] = Clase.objects.filter(materia__nivel=nivel).order_by('-materia__inicio')

                data['materiasfaltantes'] = [x for x in nivel.materia_set.all() if x.clase_set.count()==0]
                data['ret'] = ret if ret else ""  #Para retornar a nivel y no a horarios
                data['cronogramapagos'] = MODELO_EVALUACION!=EVALUACION_TES
                if 'horasclase' in request.GET:
                     data['horasclase'] = request.GET['horasclase']
                return render(request ,"horarios/horariobs.html" ,  data)

            elif action=='addclase':
                data['title'] = 'Adicionar Clase a Horario'
                nivel = Nivel.objects.get(pk=request.GET['nivel'])
                turno=None
                materia=None
                form=None
                data['nivel'] = nivel

                if 'turno' in request.GET:
                    turno=Turno.objects.get(pk=request.GET['turno'])
                    form = ClaseForm(initial={'turno':Turno.objects.get(pk=request.GET['turno']),'dia':request.GET['dia']})

                if 'materia' in request.GET:
                    form = ClaseForm(initial={'materia': Materia.objects.get(pk=request.GET['materia'])})
                    materia = Materia.objects.get(pk=request.GET['materia'])
                else:
                    form = ClaseForm(initial={'turno':Turno.objects.get(pk=request.GET['turno']),'dia':request.GET['dia']})

                form.for_nivel(nivel)
                form.for_profesormateria(nivel,materia)
                data['form'] = form
                return render(request ,"horarios/adicionarbs.html" ,  data)
            elif action=='editclase':
                data['title'] = 'Editar Clase de Horario'
                clase = Clase.objects.get(pk=request.GET['id'])
                data['clase'] = clase
                form = ClaseForm(initial=model_to_dict(clase))
                form.for_nivel(clase.materia.nivel)
                form.for_profesormateria(clase.materia.nivel,clase.materia)
                data['form'] = form
                data['nivel'] = clase.materia.nivel
                return render(request ,"horarios/editarbs.html" ,  data)

            elif action=='editaula':
                data['title'] = 'Editar Aula en Nivel Cerrado'
                clase = Clase.objects.get(pk=request.GET['id'])
                data['clase'] = clase
                form = ClaseNivelCerradoForm(initial=model_to_dict(clase))
                form.for_nivel(clase.materia.nivel)
                form.for_profesormateria(clase.materia.nivel,clase.materia)
                data['form'] = form
                data['nivel'] = clase.materia.nivel
                return render(request,"horarios/editaraulabs.html", data)

            elif action=='right':
                clase = Clase.objects.get(pk=request.GET['id'])
                sesion = clase.materia.nivel.sesion
                if clase.materia.inicio < date(clase.materia.inicio.year,clase.materia.inicio.month,22):
                        dia2 = datetime(clase.materia.inicio.year,clase.materia.inicio.month,22)- timedelta(days=30)
                        inicio = datetime(dia2.year,dia2.month,22)
                        fin = datetime(clase.materia.inicio.year,clase.materia.inicio.month,21)
                else:
                    dia2 = date(clase.materia.inicio.year,clase.materia.inicio.month,22) + timedelta(days=30)
                    inicio =datetime(clase.materia.inicio.year,clase.materia.inicio.month,22)
                    fin = datetime(dia2.year,dia2.month,21)
                for i in range(clase.dia+1,8):
                    if sesion.clases_los_(i):
                        clase_clon = Clase(materia=clase.materia,
                                                profesor=clase.profesor,
                                                turno = clase.turno,
                                                aula=clase.aula,
                                                dia=i,
                                                profesormateria=clase.profesormateria)
                        clase_clon.save()
                        b=0
                        if VALIDA_MAXIMO_HORAS:
                            for profesor in ProfesorMateria.objects.filter(materia=clase.materia).distinct('profesor').values('profesor'):
                                horasclase = 0
                                for pm in ProfesorMateria.objects.filter(profesor__id= profesor['profesor']):
                                    horasclase = horasclase + pm.materia.horas_materia_rangofecha(pm,inicio,fin)[0]
                                if horasclase > MAXIMO_HORAS_CLASE and VALIDA_MAXIMO_HORAS :
                                    clase_clon.delete()
                                    return HttpResponseRedirect('/horarios?action=horario&id='+str(clase.materia.nivel_id)+'&horasclase='+'El Profesor '+(str(pm.profesor.persona.nombre_completo()) + ' ha superado las horas permitidas ' + str(horasclase) +' en el periodo ' + str(inicio.date()) + ' / ' + str(fin.date())))
                                    # data = {'result': 'clase', 'horasclase':(str(pm.profesor.persona.nombre_completo()) + " " + str(horasclase) ),'inicio':str(inicio.date()),'fin':str(fin.date())}
                        # if b == 0 or not VALIDA_MAXIMO_HORAS:

                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de Replica del horario a la derecha
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(clase).pk,
                    object_id       = clase.id,
                    object_repr     = force_str(clase),
                    action_flag     = CHANGE,
                    change_message  = 'Horario a la derecha replicado (' + client_address + ')'  )

                return HttpResponseRedirect('/horarios?action=horario&id='+str(clase.materia.nivel_id))
            elif action=='down':
                clase = Clase.objects.get(pk=request.GET['id'])
                sesion = clase.materia.nivel.sesion
                if clase.materia.inicio < date(clase.materia.inicio.year,clase.materia.inicio.month,22):
                        dia2 = datetime(clase.materia.inicio.year,clase.materia.inicio.month,22)- timedelta(days=30)
                        inicio = datetime(dia2.year,dia2.month,22)
                        fin = datetime(clase.materia.inicio.year,clase.materia.inicio.month,21)
                else:
                    dia2 = date(clase.materia.inicio.year,clase.materia.inicio.month,22) + timedelta(days=30)
                    inicio =datetime(clase.materia.inicio.year,clase.materia.inicio.month,22)
                    fin = datetime(dia2.year,dia2.month,21)
                for t in Turno.objects.filter(sesion=sesion).exclude(id=clase.turno_id):
                    clase_clon = Clase(materia=clase.materia,
                        profesor=clase.profesor,
                        turno = t,
                        aula=clase.aula,
                        dia=clase.dia,
                        profesormateria=clase.profesormateria)
                    clase_clon.save()
                    if VALIDA_MAXIMO_HORAS:
                        for profesor in ProfesorMateria.objects.filter(materia=clase.materia).distinct('profesor').values('profesor'):
                            horasclase = 0
                            for pm in ProfesorMateria.objects.filter(profesor__id= profesor['profesor']):
                                horasclase = horasclase + pm.materia.horas_materia_rangofecha(pm,inicio,fin)[0]
                            if horasclase > MAXIMO_HORAS_CLASE and VALIDA_MAXIMO_HORAS :
                                clase_clon.delete()
                                return HttpResponseRedirect('/horarios?action=horario&id='+str(clase.materia.nivel_id)+'&horasclase='+'El Profesor '+(str(pm.profesor.persona.nombre_completo()) + ' ha superado las horas permitidas ' + str(horasclase) +' en el periodo ' + str(inicio.date()) + ' / ' + str(fin.date())))
                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de Replica del horario hacia abajo
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(clase).pk,
                    object_id       = clase.id,
                    object_repr     = force_str(clase),
                    action_flag     = CHANGE,
                    change_message  = 'Horario hacia abajo replicado (' + client_address + ')'  )

                return HttpResponseRedirect('/horarios?action=horario&id='+str(clase.materia.nivel_id))
            elif action=='delclase':
                clase = Clase.objects.get(pk=request.GET['id'])
                nid = clase.materia.nivel_id

                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de Eliminar horario
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(clase).pk,
                    object_id       = clase.id,
                    object_repr     = force_str(clase),
                    action_flag     = CHANGE,
                    change_message  = 'Horario eliminado (' + client_address + ')'  )

                clase.delete()
                return HttpResponseRedirect('/horarios?action=horario&id='+str(nid))
            return HttpResponseRedirect("/horarios")
        else:
            if MODELO_EVALUACION==EVALUACION_TES:
                return HttpResponseRedirect("/niveles")
            #data['periodo'] = Periodo.periodo_vigente()
            data['sedes'] = Sede.objects.filter(solobodega=False)
            data['carreras'] = Carrera.objects.filter(grupocoordinadorcarrera__group__in=request.user.groups.all()).distinct().order_by('nombre')
            data['niveles'] = Nivel.objects.filter(periodo=data['periodo'], carrera__in=data['carreras']).order_by('paralelo')
            return render(request ,"horarios/horariosbs.html" ,  data)