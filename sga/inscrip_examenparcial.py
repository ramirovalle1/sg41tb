from datetime import datetime
import json
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Sum
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.utils.encoding import force_str
from decorators import secure_module
from settings import ABRIR_EXAMEN_DESDE_AULA, NOTA_PARA_SUPLET, PUNTAJE_MIN_EXAMEN, NUM_PREGUN_EXAMENPARC, NOTA_PARA_APROBAR, NUM_PREGUN_EXAMENPARCSUPLE, NOTA_ESTADO_APROBADO, DEFAULT_PASSWORD, MODELO_EVALUACION, EVALUACION_ITB, ASIG_VINCULACION, ASIGNATURA_PRACTICA_CONDUCCION, INSCRIPCION_CONDUCCION, ASIG_PRATICA
from sga.commonviews import addUserData, ip_client_address
from sga.models import MateriaAsignada, ExamenParcial, TituloExamenParcial, Aula, Matricula, PreguntaAsignatura, ExamenParRespuesta, PreguntaAsigRespuesta, HistoricoNotasITB, HistoricoRecordAcademico, RecordAcademico


class MiPaginador(Paginator):
    def __init__(self, object_list, per_page, orphans=0, allow_empty_first_page=True, rango=5):
        super(MiPaginador,self).__init__(object_list, per_page, orphans=orphans, allow_empty_first_page=allow_empty_first_page)
        self.rango = rango
        self.paginas = []
        self.primera_pagina = False
        self.ultima_pagina = False

    def rangos_paginado(self, pagina):
        left = pagina - self.rango
        right = pagina + self.rango
        if left<1:
            left=1
        if right>self.num_pages:
            right = self.num_pages
        self.paginas = range(left, right+1)
        self.primera_pagina = True if left>1 else False
        self.ultima_pagina = True if right<self.num_pages else False
        self.ellipsis_izquierda = left-1
        self.ellipsis_derecha = right+1
__author__ = 'JuanJose'
@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    try:
        if request.method == 'POST':
            action = request.POST['action']
            if action == "actualizatime":
                try:
                    tiempo = datetime(datetime.now().year,datetime.now().month,datetime.now().day,int(request.POST['hora']),int(request.POST['minut']),int(request.POST['segun']))
                    if ExamenParcial.objects.filter(id=request.POST['idexamenparc'],valida=True).exists():
                        examenparcial = ExamenParcial.objects.get(id=request.POST['idexamenparc'],valida=True)
                        examenparcial.tiempo = tiempo
                        examenparcial.save()
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as ex:
                        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
            elif action == "addrespuesta":
                try:
                    preguntaasigrespuesta = PreguntaAsigRespuesta.objects.filter(id=request.POST['idresp'])[:1].get()
                    tiempo = datetime(datetime.now().year,datetime.now().month,datetime.now().day,int(request.POST['hora']),int(request.POST['minut']),int(request.POST['segun']))

                    examenparcial = ExamenParcial.objects.get(id=request.POST['idexamenparc'])
                    examenparcial.tiempo = tiempo
                    examenparcial.fecha = datetime.now()
                    examenparcial.save()
                    examenparrespuesta = ExamenParRespuesta.objects.filter(examenparcial = examenparcial,preguntaasigrespuesta__preguntaasignatura = preguntaasigrespuesta.preguntaasignatura)[:1].get()

                    if request.POST['check'] == 'false':
                        if examenparrespuesta.preguntaasigrespuesta.valida and examenparcial.puntaje != 0:
                            examenparcial.puntaje = examenparcial.puntaje - examenparrespuesta.preguntaasigrespuesta.preguntaasignatura.puntos
                        examenparrespuesta.fecha = None
                    elif examenparrespuesta.preguntaasigrespuesta.valida and examenparcial.puntaje != 0 and examenparcial.fecha != None:
                        examenparcial.puntaje = examenparcial.puntaje - examenparrespuesta.preguntaasigrespuesta.preguntaasignatura.puntos

                    if preguntaasigrespuesta.valida and request.POST['check'] == 'true':
                        examenparcial.puntaje = examenparcial.puntaje + preguntaasigrespuesta.preguntaasignatura.puntos

                    if request.POST['check'] == 'true':
                        examenparrespuesta.fecha = datetime.now()

                    examenparrespuesta.preguntaasigrespuesta = preguntaasigrespuesta
                    examenparrespuesta.save()
                    examenparcial.save()
                    sinconte = ExamenParRespuesta.objects.filter(examenparcial = examenparcial,fecha=None).count()
                    client_address = ip_client_address(request)
                    #Log de ADICIONAR INSCRIPCION
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(examenparrespuesta).pk,
                        object_id       = examenparrespuesta.id,
                        object_repr     = force_str(examenparrespuesta),
                        action_flag     = ADDITION,
                        change_message  = 'Realizacion de examen parcial (' + client_address + ')')


                    return HttpResponse(json.dumps({"result":"ok","sinconte":str(sinconte)}),content_type="application/json")
                except Exception as ex:
                        return HttpResponse(json.dumps({"result":"bad","mensaje":str(ex)}),content_type="application/json")
            elif action == "finalizar":
                try:
                    client_address = ip_client_address(request)
                    tiempo = datetime(datetime.now().year,datetime.now().month,datetime.now().day,int(request.POST['hora']),int(request.POST['minut']),int(request.POST['segun']))
                    if ExamenParcial.objects.filter(id=request.POST['idexamenparc'],valida=True).exists():
                        examenparcial = ExamenParcial.objects.filter(id=request.POST['idexamenparc'],valida=True)[:1].get()
                        examenparcial.tiempo = tiempo
                        examenparcial.finalizado = True
                        examenparcial.ipmaquina = client_address

                        puntaje = ExamenParRespuesta.objects.filter(examenparcial = examenparcial,preguntaasigrespuesta__valida=True).exclude(fecha=None).aggregate(Sum('preguntaasigrespuesta__preguntaasignatura__puntos'))['preguntaasigrespuesta__preguntaasignatura__puntos__sum']
                        examenparcial.puntaje = puntaje
                        if examenparcial.puntaje == None:
                            puntaje = 0
                            examenparcial.puntaje = 0
                        examenparcial.save()
                        materiaasignada = MateriaAsignada.objects.filter(materia=examenparcial.tituloexamenparcial.profesormateria.materia,matricula=examenparcial.matricula).order_by()[:1].get()
                        evaluacion = materiaasignada.evaluacion()
                        if not examenparcial.tituloexamenparcial.supletorio:
                            evaluacion.examen = int(puntaje)
                            evaluacion.save()
                        if examenparcial.tituloexamenparcial.supletorio:
                            evaluacion.recuperacion = int(puntaje)
                            evaluacion.save()
                        evaluacion.actualiza_estado()
                        # ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
                        # ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
                        # ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
                        # ///////////////////////////////////SI ESTA CERRADO EL NIVEL////////////////////////////////////////////////////////////////////////
                        if materiaasignada.materia.nivel.cerrado:
                            ma = materiaasignada

                            if ma.materia.asignatura.asistencia and ma.notafinal >= NOTA_PARA_APROBAR:
                                asistencia = 100
                            else:
                                asistencia = ma.asistenciafinal
                            # Record
                            b = 1
                            if not ma.materia.asignatura.sin_malla:
                                if (ma.materia.asignatura.id == ASIGNATURA_PRACTICA_CONDUCCION and INSCRIPCION_CONDUCCION):
                                     b=0
                                if ((ma.materia.asignatura.id == ASIG_VINCULACION  or ma.materia.asignatura.id == ASIG_PRATICA)and not INSCRIPCION_CONDUCCION) :
                                    b = 0
                                if b == 1:
                                # if ((ma.materia.asignatura.id != ASIG_VINCULACION  or ma.materia.asignatura.id != ASIG_PRATICA)and not INSCRIPCION_CONDUCCION)  or (ma.materia.asignatura.id != ASIGNATURA_PRACTICA_CONDUCCION and INSCRIPCION_CONDUCCION):
                                    if RecordAcademico.objects.filter(inscripcion=ma.matricula.inscripcion, asignatura=ma.materia.asignatura).exists():
                                        r = RecordAcademico.objects.filter(inscripcion=ma.matricula.inscripcion, asignatura=ma.materia.asignatura)[:1].get()
                                        r.nota = ma.notafinal
                                        r.asistencia = asistencia
                                        r.fecha = ma.matricula.nivel.fin
                                        r.convalidacion = False
                                        # r.aprobada = ma.esta_aprobado()
                                        r.pendiente = False
                                        r.save()
                                        if DEFAULT_PASSWORD == 'itb':
                                            r.aprobada = ma.esta_aprobado_final()
                                            if ma.materia.asignatura.asistencia and ma.notafinal >= NOTA_PARA_APROBAR:
                                                r.aprobada = True
                                            else:
                                                if str(ma.evaluacion().estado.nombre)=='APROBADO':
                                                    r.aprobada = True
                                                else:
                                                    r.aprobada = False
                                        else:
                                            r.aprobada = ma.esta_aprobado()
                                        r.save()
                                    else:
                                        r = RecordAcademico(inscripcion=ma.matricula.inscripcion, asignatura=ma.materia.asignatura,
                                                            nota=ma.notafinal, asistencia=asistencia,
                                                            fecha=ma.matricula.nivel.fin, convalidacion=False,
                                                            pendiente=False)
                                        r.save()
                                        if DEFAULT_PASSWORD == 'itb':
                                            r.aprobada = ma.esta_aprobado_final()
                                            if ma.materia.asignatura.asistencia and ma.notafinal >= NOTA_PARA_APROBAR:
                                                r.aprobada = True
                                            else:
                                                if str(ma.evaluacion().estado.nombre)=='APROBADO':
                                                    r.aprobada = True
                                                else:
                                                    r.aprobada = False
                                        else:
                                            r.aprobada = ma.esta_aprobado()
                                        r.save()
                                    # Historico
                                    if HistoricoRecordAcademico.objects.filter(inscripcion=ma.matricula.inscripcion, asignatura=ma.materia.asignatura, fecha=ma.matricula.nivel.fin).exists():
                                        r = HistoricoRecordAcademico.objects.filter(inscripcion=ma.matricula.inscripcion, asignatura=ma.materia.asignatura, fecha=ma.matricula.nivel.fin)[:1].get()
                                        r.nota = ma.notafinal
                                        r.asistencia = asistencia
                                        r.fecha = ma.matricula.nivel.fin
                                        r.convalidacion = False
                                        # r.aprobada = ma.esta_aprobado()
                                        r.pendiente = False
                                        r.save()
                                        if DEFAULT_PASSWORD == 'itb':
                                            r.aprobada = ma.esta_aprobado_final()
                                            if ma.materia.asignatura.asistencia and ma.notafinal >= NOTA_PARA_APROBAR:
                                                r.aprobada = True
                                            else:
                                                if str(ma.evaluacion().estado.nombre)=='APROBADO':
                                                    r.aprobada = True
                                                else:
                                                    r.aprobada = False
                                        else:
                                            r.aprobada = ma.esta_aprobado()
                                        r.save()
                                    else:
                                        r = HistoricoRecordAcademico(inscripcion=ma.matricula.inscripcion, asignatura=ma.materia.asignatura,
                                                                    nota=ma.notafinal, asistencia=asistencia,
                                                                    fecha=ma.matricula.nivel.fin, convalidacion=False,
                                                                    pendiente=False)
                                        r.save()
                                        if DEFAULT_PASSWORD == 'itb':
                                            r.aprobada = ma.esta_aprobado_final()
                                            if ma.materia.asignatura.asistencia and ma.notafinal >= NOTA_PARA_APROBAR:
                                                r.aprobada = True
                                            else:
                                                if str(ma.evaluacion().estado.nombre)=='APROBADO':
                                                    r.aprobada = True
                                                else:
                                                    r.aprobada = False
                                        else:
                                            r.aprobada = ma.esta_aprobado()
                                        r.save()
                                    #Obtain client ip address
                                    client_address = ip_client_address(request)

                                    # Log de CERRAR MATERIA
                                    LogEntry.objects.log_action(
                                        user_id         = request.user.pk,
                                        content_type_id = ContentType.objects.get_for_model(ma.matricula).pk,
                                        object_id       = ma.matricula.id,
                                        object_repr     = force_str(ma.matricula),
                                        action_flag     = CHANGE,
                                        change_message  = 'Cerrada Materia Asignada (' + client_address + ')' )

                                    # Guardar Historico Notas ITB
                                    if MODELO_EVALUACION==EVALUACION_ITB:
                                        if HistoricoNotasITB.objects.filter(historico=r).exists() :
                                            hn = HistoricoNotasITB.objects.filter(historico=r)[:1].get()
                                        else:
                                            hn = HistoricoNotasITB(historico=r)
                                            hn.save()

                                        evaluacion = ma.evaluacion_itb()

                                        hn.cod1 = evaluacion.cod1.id if evaluacion.cod1 else 3
                                        hn.cod2 = evaluacion.cod2.id if evaluacion.cod2 else 5
                                        hn.cod3 = evaluacion.cod3.id if evaluacion.cod3 else 10
                                        hn.cod4 = evaluacion.cod4.id if evaluacion.cod4 else 11
                                        hn.n1 = evaluacion.n1
                                        hn.n2 = evaluacion.n2
                                        hn.n3 = evaluacion.n3
                                        hn.n4 = evaluacion.n4
                                        hn.n5 = evaluacion.examen
                                        if DEFAULT_PASSWORD == 'itb':
                                            hn.total = evaluacion.nota_total_nueva()
                                            hn.notafinal = evaluacion.nota_final_nueva()
                                            if not ma.materia.asignatura.asistencia:
                                                hn.estado = evaluacion.estado
                                            else:
                                               if ma.notafinal >= NOTA_PARA_APROBAR:
                                                    hn.estado.id = NOTA_ESTADO_APROBADO
                                               else:
                                                   hn.estado = evaluacion.estado
                                        else:
                                            hn.total = evaluacion.nota_total()
                                            hn.notafinal = evaluacion.nota_final()
                                        hn.recup = evaluacion.recuperacion
                                        hn.save()
                        # ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
                        # ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(examenparcial).pk,
                            object_id       = examenparcial.id,
                            object_repr     = force_str(examenparcial),
                            action_flag     = ADDITION,
                            change_message  = 'Finalizando examen complexivo  (' + client_address + ')')
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as ex:
                        return HttpResponse(json.dumps({"result":"bad",'mensaje':str(ex)}),content_type="application/json")
        else:
            data = {'title': 'Examen Parcial'}
            addUserData(request, data)
            if 'action' in request.GET:
                action = request.GET['action']
                if action == 'examen':
                    tituloexamenparcial =  TituloExamenParcial.objects.filter(id=request.GET['id'])[:1].get()
                    # client_address = ip_client_address(request)
                    try:
                        # case server externo
                        client_address = request.META['HTTP_X_FORWARDED_FOR']
                    except:
                        # case localhost o 127.0.0.1
                        client_address = request.META['REMOTE_ADDR']
                    if ABRIR_EXAMEN_DESDE_AULA:
                        if not Aula.objects.filter(activa=False,ip=client_address):
                            return  HttpResponseRedirect('/?info=No tiene permiso para acceder al modulo')
                    matricula = Matricula.objects.filter(inscripcion__persona=data['persona']).order_by('-id')[:1].get()
                    if tituloexamenparcial.supletorio:
                        numeropregunta = NUM_PREGUN_EXAMENPARCSUPLE
                    else:
                        numeropregunta =  NUM_PREGUN_EXAMENPARC
                    if ExamenParcial.objects.filter(matricula=matricula,tituloexamenparcial=tituloexamenparcial,valida=True).exists():
                        examenparcial = ExamenParcial.objects.filter(matricula=matricula,tituloexamenparcial=tituloexamenparcial,valida=True)[:1].get()
                        data['minutos'] = str(examenparcial.tiempo.time()).split(":")[1]
                        data['horas'] = str(examenparcial.tiempo.time()).split(":")[0]
                        data['segundos'] = str(examenparcial.tiempo.time()).split(":")[2]
                        if examenparcial.finalizado:
                            examenparrespuesta = ExamenParRespuesta.objects.filter(examenparcial=examenparcial).order_by('id')
                        else:
                            examenparrespuesta = ExamenParRespuesta.objects.filter(examenparcial=examenparcial).order_by('?')
                            data['NUMERO_PREGUNTA'] = ExamenParRespuesta.objects.filter(examenparcial=examenparcial,fecha=None).count()

                    else:
                        tiempo = datetime(datetime.now().year,datetime.now().month,datetime.now().day,int(str(tituloexamenparcial.tiempo.time()).split(":")[0]),int(str(tituloexamenparcial.tiempo.time()).split(":")[1]),int('59'))
                        examenparcial =   ExamenParcial(
                                            matricula = matricula,
                                            puntaje= 0,
                                            tituloexamenparcial = tituloexamenparcial,
                                            tiempo = tiempo,
                                            fecha = datetime.now(),
                                            valida = True,
                                            finalizado = False,
                                            ipmaquina=client_address)
                        examenparcial.save()
                        idpreguntaasig = PreguntaAsigRespuesta.objects.filter(preguntaasignatura__carrera=matricula.nivel.carrera,preguntaasignatura__asignatura=tituloexamenparcial.profesormateria.materia.asignatura,preguntaasignatura__activo=True,valida=True).distinct('preguntaasignatura').values('preguntaasignatura')
                        for p in PreguntaAsignatura.objects.filter(carrera=matricula.nivel.carrera,asignatura=tituloexamenparcial.profesormateria.materia.asignatura,activo=True,id__in=idpreguntaasig).order_by('?')[:numeropregunta]:
                            if PreguntaAsigRespuesta.objects.filter(preguntaasignatura=p).exists():
                                preguntaasigrespuesta = PreguntaAsigRespuesta.objects.filter(preguntaasignatura=p)[:1].get()
                                examenparrespuesta = ExamenParRespuesta(
                                                examenparcial=examenparcial,
                                                preguntaasigrespuesta = preguntaasigrespuesta,
                                                fecha = None)
                                examenparrespuesta.save()
                        examenparrespuesta = ExamenParRespuesta.objects.filter(examenparcial=examenparcial).order_by('?')

                        data['segundos'] = '59'
                        if int(str(tituloexamenparcial.tiempo.time()).split(":")[1]) <= 0:
                            minutos = '59'
                            if int(int(str(tituloexamenparcial.tiempo.time()).split(":")[0])) <= 0:
                                hora = 0
                                minutos = 0
                            else:
                                hora = int(str(tituloexamenparcial.tiempo.time()).split(":")[0]) - 1
                        else:
                            minutos = int(str(tituloexamenparcial.tiempo.time()).split(":")[1])-1
                            hora = str(tituloexamenparcial.tiempo.time()).split(":")[0]
                        data['minutos'] = str(minutos).zfill(2)
                        data['horas'] = str(hora).zfill(2)
                        data['NUMERO_PREGUNTA'] = numeropregunta



                    data['tituloexamenparcial'] = tituloexamenparcial

                    paging = MiPaginador(examenparrespuesta, numeropregunta)
                    p = 1
                    try:
                        if 'page' in request.GET:
                            p = int(request.GET['page'])
                        page = paging.page(p)
                    except:
                        page = paging.page(1)
                    data['paging'] = paging
                    data['rangospaging'] = paging.rangos_paginado(p)
                    data['page'] = page
                    data['preguntaexamen'] = page.object_list
                    data['examenparcial'] = examenparcial
                    data['NOTA_PARA_APROBAR'] = NOTA_PARA_APROBAR
                    data['NOTA_PARA_SUPLET'] = NOTA_PARA_SUPLET

                    return render(request ,"examenparcial/examenparcial.html" ,  data)

            else:
                idtitexamen = ExamenParcial.objects.filter(matricula__inscripcion__persona=data['persona'],valida=True,finalizado=True).distinct('tituloexamenparcial').values('tituloexamenparcial')
                idmateria = MateriaAsignada.objects.filter(matricula__inscripcion__persona=data['persona']).distinct('materia').values('materia')
                tituloexamen = TituloExamenParcial.objects.filter(activo=True,profesormateria__materia__id__in=idmateria).exclude(id__in=idtitexamen)

                # client_address = ip_client_address(request)
                try:
                    # case server externo
                    client_address = request.META['HTTP_X_FORWARDED_FOR']
                except:
                    # case localhost o 127.0.0.1
                    client_address = request.META['REMOTE_ADDR']
                if ABRIR_EXAMEN_DESDE_AULA:
                    if not Aula.objects.filter(activa=False,ip=client_address):
                        return  HttpResponseRedirect('/?info=No tiene permiso para acceder al modulo')
                matricula = Matricula.objects.filter(inscripcion__persona=data['persona']).order_by('-id')[:1].get()
                data['matricula'] = matricula
                if not tituloexamen:
                    return HttpResponseRedirect('/?info=NO hay examenes activos')
                data['tituloexamenes'] = tituloexamen
                data['NOTA_PARA_SUPLET'] = NOTA_PARA_SUPLET
                data['PUNTAJE_MIN_EXAMEN'] = PUNTAJE_MIN_EXAMEN
                data['NOTA_PARA_APROBAR'] = NOTA_PARA_APROBAR
                return render(request ,"examenparcial/menuexam.html" ,  data)
    except Exception as e:
        print(e)
        return HttpResponseRedirect('/?info=Error de Excepcion comunicarse con el administrador')