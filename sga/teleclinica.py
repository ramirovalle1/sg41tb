from datetime import datetime, timedelta
from decimal import Decimal
from itertools import chain
import json
from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Sum
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.utils.encoding import force_str
from decorators import secure_module
from settings import NOTA_PARA_EXAMEN_CONDUCCION, NUMERO_PREGUNTA, ASIGNATURA_EXAMEN_GRADO_CONDU, ASIGNATURA_PRACTICA_CONDUCCION, NIVEL_MALLA_CERO, \
     DEFAULT_PASSWORD, EXAMEN_PRACTI_COMPLEX, EXAMEN_TEORI_COMPLEX, EXAMEN_PRACTIPORC_COMPLEX, EXAMEN_TEORIPORC_COMPLEX, NOTA_PARA_APROBAR, ASIST_PARA_APROBAR, \
     PROMEDIO_ASISTENCIAS_CONDU,INSCRIPCION_CONDUCCION, ABRIR_EXAMEN_DESDE_AULA,ASIG_PRATICA, ID_ASIGNATURA_PRACT
from sga.commonviews import addUserData, ip_client_address
from sga.models import TituloExamenCondu, PreguntaExamen, Inscripcion, InscripcionExamen, RespuestaExamen, DetalleExamen, HistoricoRecordAcademico, RecordAcademico, Aula, AsignaturaMalla, ExamenPractica, TipoAula, TipAulaExamen


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

@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    try:
        if request.method == 'POST':
            action = request.POST['action']
            if action == "addrespuesta":
                try:
                    respuestaexamen = RespuestaExamen.objects.filter(id=request.POST['idresp'])[:1].get()
                    tiempo = datetime(datetime.now().year,datetime.now().month,datetime.now().day,int(request.POST['hora']),int(request.POST['minut']),int(request.POST['segun']))

                    inscripcionexamen = InscripcionExamen.objects.filter(inscripcion__id=request.POST['idinscrip'],tituloexamencondu = respuestaexamen.preguntaexamen.tituloexamencondu,valida=True)[:1].get()
                    inscripcionexamen.tiempo = tiempo
                    inscripcionexamen.fecha = datetime.now()
                    inscripcionexamen.save()
                    detalleexamen = DetalleExamen.objects.filter(inscripcionexamen = inscripcionexamen,respuestaexamen__preguntaexamen = respuestaexamen.preguntaexamen)[:1].get()

                    if request.POST['check'] == 'false':
                        if detalleexamen.respuestaexamen.valida and inscripcionexamen.puntaje != 0:
                            inscripcionexamen.puntaje = inscripcionexamen.puntaje - detalleexamen.respuestaexamen.preguntaexamen.puntos
                        detalleexamen.fecha = None
                    elif detalleexamen.respuestaexamen.valida and inscripcionexamen.puntaje != 0 and detalleexamen.fecha != None:
                        inscripcionexamen.puntaje = inscripcionexamen.puntaje - detalleexamen.respuestaexamen.preguntaexamen.puntos

                    if respuestaexamen.valida and request.POST['check'] == 'true':
                        inscripcionexamen.puntaje = inscripcionexamen.puntaje + respuestaexamen.preguntaexamen.puntos

                    if request.POST['check'] == 'true':
                        detalleexamen.fecha = datetime.now()

                    detalleexamen.respuestaexamen = respuestaexamen
                    detalleexamen.save()
                    inscripcionexamen.save()
                    sinconte = DetalleExamen.objects.filter(inscripcionexamen = inscripcionexamen,fecha=None).count()
                    html='<h3>Evaluacion Finalizada.</h3>'
                    idpre=[]
                    if sinconte>0:
                        html= html +'<h5>Existen Preguntas sin contestar: '+ str(sinconte) +' Se marcaran en rojo </h5> '
                        for sinresp in DetalleExamen.objects.filter(inscripcionexamen = inscripcionexamen,fecha=None):
                            idpre.append({'id':sinresp.respuestaexamen.preguntaexamen.id})
                    else:
                        html='Evaluacion Finalizada.'
                    client_address = ip_client_address(request)
                    #Log de Realizar Evaluacion
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(detalleexamen).pk,
                        object_id       = detalleexamen.id,
                        object_repr     = force_str(detalleexamen),
                        action_flag     = ADDITION,
                        change_message  = 'Realizacion de evaluacion (' + client_address + ')')


                    return HttpResponse(json.dumps({"result":"ok","sinconte":str(sinconte),'html':html,'idpre':idpre}),content_type="application/json")
                except Exception as ex:
                        return HttpResponse(json.dumps({"result":"bad","mensaje":str(ex)}),content_type="application/json")
            elif action == "actualizatime":
                try:
                    tiempo = datetime(datetime.now().year,datetime.now().month,datetime.now().day,int(request.POST['hora']),int(request.POST['minut']),int(request.POST['segun']))
                    if InscripcionExamen.objects.filter(inscripcion__id=request.POST['idinscrip'],tituloexamencondu__id = request.POST['idtituex'],valida=True,tituloexamencondu__teleclinica=True).exists():
                        inscripcionexamen = InscripcionExamen.objects.filter(inscripcion__id=request.POST['idinscrip'],tituloexamencondu__id = request.POST['idtituex'],valida=True,tituloexamencondu__teleclinica=True)[:1].get()
                        inscripcionexamen.tiempo = tiempo
                        inscripcionexamen.save()
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as ex:
                        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

            elif action == "finalizar":
                try:
                    client_address = ip_client_address(request)
                    tiempo = datetime(datetime.now().year,datetime.now().month,datetime.now().day,int(request.POST['hora']),int(request.POST['minut']),int(request.POST['segun']))
                    if InscripcionExamen.objects.filter(inscripcion__id=request.POST['idinscrip'],tituloexamencondu__id = request.POST['idtituex'],valida=True).exists():
                        inscripcionexamen = InscripcionExamen.objects.filter(inscripcion__id=request.POST['idinscrip'],tituloexamencondu__id = request.POST['idtituex'],valida=True)[:1].get()
                        inscripcionexamen.tiempo = tiempo
                        inscripcionexamen.finalizado = True
                        inscripcionexamen.ipmaquina = client_address

                        puntaje = DetalleExamen.objects.filter(inscripcionexamen = inscripcionexamen,respuestaexamen__valida=True).exclude(fecha=None).aggregate(Sum('respuestaexamen__preguntaexamen__puntos'))['respuestaexamen__preguntaexamen__puntos__sum']
                        inscripcionexamen.puntaje = puntaje
                        if inscripcionexamen.puntaje == None:
                            inscripcionexamen.puntaje = 0
                        inscripcionexamen.save()

                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(inscripcionexamen).pk,
                            object_id       = inscripcionexamen.id,
                            object_repr     = force_str(inscripcionexamen),
                            action_flag     = ADDITION,
                            change_message  = 'Finalizando evaluacion teleclinica  (' + client_address + ')')
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as ex:
                        return HttpResponse(json.dumps({"result":"bad",'mensaje':str(ex)}),content_type="application/json")
            elif action == "activarexamen":
                try:
                    datos = json.loads(request.POST['datos'])
                    for d in datos:
                        tipaulaexamen = TipAulaExamen(tituloexamen_id = d['idtitexamen'],
                                                      tipo_id = d['idlaborat'],
                                                      fecha = datetime.now(),
                                                      activo = True,
                                                      usuario = request.user)
                        tipaulaexamen.save()

                    tituloexamencondu =  TituloExamenCondu.objects.filter(id=request.POST['id'],convalida=False)[:1].get()
                    mensaje = 'Activacion de Examen'
                    tituloexamencondu.activo = True
                    tituloexamencondu.save()

                    client_address = ip_client_address(request)
                    #Log de ADICIONAR INSCRIPCION
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(tituloexamencondu).pk,
                        object_id       = tituloexamencondu.id,
                        object_repr     = force_str(tituloexamencondu),
                        action_flag     = ADDITION,
                        change_message  = mensaje +' de conduccion  (' + client_address + ')')
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
            elif action == "validlaborato":
                try:
                    client_address = ip_client_address(request)
                    tipoaula = TipAulaExamen.objects.filter(activo=True,tituloexamen__id=request.POST['id']).values('tipo')
                    ips_aulas = [x.ip for x in Aula.objects.filter(activa=False,tipo__id__in=tipoaula)]
                    if not client_address in ips_aulas and ABRIR_EXAMEN_DESDE_AULA:
                        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
        else:
            data={'title':'Evaluaciones'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']
                if action == 'activa':
                   tituloexamencondu =  TituloExamenCondu.objects.filter(id=request.GET['id'],teleclinica=True)[:1].get()

                   if tituloexamencondu.activo:
                      if InscripcionExamen.objects.filter(tituloexamencondu=tituloexamencondu,valida=True,finalizado=True).count() != InscripcionExamen.objects.filter(tituloexamencondu = tituloexamencondu,valida=True).count():
                          return HttpResponseRedirect('/evaluacion_teleclinica?info=Faltan evaluaciones por finalizar')
                      activo = False
                      mensaje = 'Desactivacion de Evaluacion'
                   else:
                       activo = True
                       mensaje = 'Activacion de Evaluacion'
                   tituloexamencondu.activo = activo
                   tituloexamencondu.save()

                   client_address = ip_client_address(request)
                   #Log de Activacion Teleclinica
                   LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(tituloexamencondu).pk,
                        object_id       = tituloexamencondu.id,
                        object_repr     = force_str(tituloexamencondu),
                        action_flag     = ADDITION,
                        change_message  = mensaje +' Teleclinica  (' + client_address + ')')
                   return HttpResponseRedirect('/evaluacion_teleclinica')

                # elif action == 'finalizadirec':
                #     try:
                #         client_address = ip_client_address(request)
                #         if InscripcionExamen.objects.filter(valida=True,finalizado=False).exists():
                #             for inscripcionexamen in InscripcionExamen.objects.filter(valida=True,finalizado=False):
                #                 fechafinalizacion = inscripcionexamen.fecha + timedelta(hours=inscripcionexamen.tiempo.time().hour) + timedelta(minutes=inscripcionexamen.tiempo.time().minute) + timedelta(seconds=inscripcionexamen.tiempo.time().second)
                #                 if datetime.now() >= fechafinalizacion:
                #                     inscripcionexamen.tiempo = inscripcionexamen.tiempo - timedelta(hours=inscripcionexamen.tiempo.time().hour) - timedelta(minutes=inscripcionexamen.tiempo.time().minute) - timedelta(seconds=inscripcionexamen.tiempo.time().second)
                #                     inscripcionexamen.finalizado = True
                #                     inscripcionexamen.ipmaquina = client_address
                #
                #                     puntaje = DetalleExamen.objects.filter(inscripcionexamen = inscripcionexamen,respuestaexamen__valida=True).exclude(fecha=None).aggregate(Sum('respuestaexamen__preguntaexamen__puntos'))['respuestaexamen__preguntaexamen__puntos__sum']
                #                     inscripcionexamen.puntaje = puntaje
                #                     inscripcionexamen.save()
                #                     itbband = 0
                #
                #                     if DEFAULT_PASSWORD == "itb":
                #                         if int(inscripcionexamen.puntaje) >= int(EXAMEN_TEORI_COMPLEX):
                #                             itbband = 1
                #
                #                     if DEFAULT_PASSWORD != "itb" or itbband != 0:
                #                         if itbband == 0:
                #                             puntajenota = inscripcionexamen.puntaje
                #                             if int(inscripcionexamen.puntaje) >= int(NOTA_PARA_EXAMEN_CONDUCCION):
                #                                 aprobado = True
                #                             else:
                #                                 aprobado = False
                #                         else:
                #                             examenpractica = ExamenPractica.objects.filter(valida=True,inscripcion=inscripcionexamen.inscripcion)[:1].get()
                #                             puntajenota = Decimal((inscripcionexamen.puntaje*EXAMEN_TEORIPORC_COMPLEX)/100) + Decimal((examenpractica.puntaje*EXAMEN_PRACTIPORC_COMPLEX)/100)
                #                             aprobado = True
                #
                #                         if HistoricoRecordAcademico.objects.filter( inscripcion=inscripcionexamen.inscripcion,asignatura=inscripcionexamen.tituloexamencondu.asignatura).exists():
                #                             historico = HistoricoRecordAcademico.objects.filter(inscripcion=inscripcionexamen.inscripcion,asignatura=inscripcionexamen.tituloexamencondu.asignatura)[:1].get()
                #                             historico.nota=puntajenota
                #                             historico.aprobada=aprobado
                #                             historico.fecha=datetime.now().date()
                #                             mensaje = "Editando"
                #                         else:
                #                             historico = HistoricoRecordAcademico(inscripcion=inscripcionexamen.inscripcion,
                #                                                     asignatura=inscripcionexamen.tituloexamencondu.asignatura,
                #                                                     nota=inscripcionexamen.puntaje,
                #                                                     asistencia=100,
                #                                                     fecha=datetime.now().date(),
                #                                                     aprobada=aprobado,
                #                                                     convalidacion=False,
                #                                                     pendiente=False)
                #                             mensaje = "Ingresando"
                #                         historico.save()
                #
                #                         if RecordAcademico.objects.filter( inscripcion=inscripcionexamen.inscripcion,asignatura=inscripcionexamen.tituloexamencondu.asignatura).exists():
                #                             recordacademico = RecordAcademico.objects.filter(inscripcion=inscripcionexamen.inscripcion,asignatura=inscripcionexamen.tituloexamencondu.asignatura)[:1].get()
                #                             recordacademico.nota=inscripcionexamen.puntaje
                #                             recordacademico.aprobada=aprobado
                #                             recordacademico.fecha=datetime.now().date()
                #                             mensaje = "Editando"
                #                         else:
                #                             recordacademico = RecordAcademico(inscripcion=inscripcionexamen.inscripcion,
                #                                                     asignatura=inscripcionexamen.tituloexamencondu.asignatura,
                #                                                     nota=inscripcionexamen.puntaje,
                #                                                     asistencia=100,
                #                                                     fecha=datetime.now().date(),
                #                                                     aprobada=aprobado,
                #                                                     convalidacion=False,
                #                                                     pendiente=False)
                #                             mensaje = "Ingresando"
                #                         recordacademico.save()
                #
                #
                #                         #Log de ADICIONAR INSCRIPCION
                #                         LogEntry.objects.log_action(
                #                             user_id         = request.user.pk,
                #                             content_type_id = ContentType.objects.get_for_model(historico).pk,
                #                             object_id       = historico.id,
                #                             object_repr     = force_str(historico),
                #                             action_flag     = ADDITION,
                #                             change_message  = mensaje +' Record Academico desde finalizar automatico el examen  (' + client_address + ')')
                #
                #                     else:
                #                         #Log de ADICIONAR INSCRIPCION
                #                         LogEntry.objects.log_action(
                #                             user_id         = request.user.pk,
                #                             content_type_id = ContentType.objects.get_for_model(inscripcionexamen).pk,
                #                             object_id       = inscripcionexamen.id,
                #                             object_repr     = force_str(inscripcionexamen),
                #                             action_flag     = ADDITION,
                #                             change_message  = 'Finalizar automaticamente  examen  (' + client_address + ')')
                #         return HttpResponseRedirect('/evaluacion_teleclinica')
                #     except Exception as e:
                #         return HttpResponseRedirect('/evaluacion_teleclinica?info=Error al finalizar examenes')

                elif action == 'examen':
                    tituloexamencondu =  TituloExamenCondu.objects.filter(id=request.GET['id'],convalida=False)[:1].get()
                    preguntaexamen = PreguntaExamen.objects.filter(tituloexamencondu=tituloexamencondu,activo=True).order_by('numero')
                    if Inscripcion.objects.filter(persona__usuario=request.user).exists():
                        data['inscripcion']=Inscripcion.objects.filter(persona__usuario=request.user)[:1].get()
                        if InscripcionExamen.objects.filter(inscripcion=data['inscripcion'],tituloexamencondu=tituloexamencondu,valida=True).exists():
                            inscripcionexamen = InscripcionExamen.objects.filter(inscripcion=data['inscripcion'],tituloexamencondu=tituloexamencondu,valida=True)[:1].get()
                            data['minutos'] = str(inscripcionexamen.tiempo.time()).split(":")[1]
                            data['horas'] = str(inscripcionexamen.tiempo.time()).split(":")[0]
                            data['segundos'] = str(inscripcionexamen.tiempo.time()).split(":")[2]
                            if DetalleExamen.objects.filter(inscripcionexamen=inscripcionexamen).exists():
                                detalle = DetalleExamen.objects.filter(inscripcionexamen=inscripcionexamen)
                                if inscripcionexamen.finalizado:
                                    preguntaexamen = DetalleExamen.objects.filter(inscripcionexamen=inscripcionexamen).order_by('id')
                                else:
                                    preguntaexamen = DetalleExamen.objects.filter(inscripcionexamen=inscripcionexamen).order_by('id')
                                    data['NUMERO_PREGUNTA'] = DetalleExamen.objects.filter(inscripcionexamen=inscripcionexamen,fecha=None).count()
                        else:
                            tiempo = datetime(datetime.now().year,datetime.now().month,datetime.now().day,int(str(tituloexamencondu.tiempo.time()).split(":")[0]),int(str(tituloexamencondu.tiempo.time()).split(":")[1]),int('59'))
                            client_address = ip_client_address(request)
                            inscripcionexamen =   InscripcionExamen(
                                                inscripcion = data['inscripcion'],
                                                puntaje= 0,
                                                tituloexamencondu = tituloexamencondu,
                                                tiempo = tiempo,
                                                fecha = datetime.now(),
                                                valida = True,
                                                finalizado = False,
                                                ipmaquina=client_address)
                            inscripcionexamen.save()
                            for p in PreguntaExamen.objects.filter(tituloexamencondu=tituloexamencondu,activo=True).order_by('?')[:NUMERO_PREGUNTA]:
                                respuestaexamen = RespuestaExamen.objects.filter(preguntaexamen=p)[:1].get()
                                detalleexamen = DetalleExamen(
                                                inscripcionexamen = inscripcionexamen,
                                                respuestaexamen = respuestaexamen,
                                                fecha = None)
                                detalleexamen.save()
                            preguntaexamen = DetalleExamen.objects.filter(inscripcionexamen=inscripcionexamen).order_by('id')

                            data['segundos'] = '59'
                            if int(str(tituloexamencondu.tiempo.time()).split(":")[1]) <= 0:
                                minutos = '59'
                                if int(int(str(tituloexamencondu.tiempo.time()).split(":")[0])) <= 0:
                                    hora = 0
                                    minutos = 0
                                else:
                                    hora = int(str(tituloexamencondu.tiempo.time()).split(":")[0]) - 1
                            else:
                                minutos = int(str(tituloexamencondu.tiempo.time()).split(":")[1])-1
                                hora = str(tituloexamencondu.tiempo.time()).split(":")[0]
                            data['minutos'] = str(minutos).zfill(2)
                            data['horas'] = str(hora).zfill(2)
                            data['NUMERO_PREGUNTA'] = NUMERO_PREGUNTA



                    data['tituloexamencondu'] = tituloexamencondu

                    paging = MiPaginador(preguntaexamen, NUMERO_PREGUNTA)
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
                    data['NOTA_PARA_EXAMEN_CONDUCCION'] = NOTA_PARA_EXAMEN_CONDUCCION
                    data['EXAMEN_TEORI_COMPLEX'] = EXAMEN_TEORI_COMPLEX
                    data['DEFAULT_PASSWORD'] = DEFAULT_PASSWORD

                    return render(request ,"teleclinica/realiza_evaluacion.html" ,  data)
            else:
                data['tituloexamen'] = TituloExamenCondu.objects.filter(teleclinica=True).order_by('tituloexamen')
                data['examentitactivo'] = TituloExamenCondu.objects.filter(teleclinica=True,activo=True).order_by('tituloexamen')
                if Inscripcion.objects.filter(persona__usuario=request.user).exists():
                        # client_address = ip_client_address(request)
                        try:
                            # case server externo
                            client_address = request.META['HTTP_X_FORWARDED_FOR']
                        except:
                            # case localhost o 127.0.0.1
                            client_address = request.META['REMOTE_ADDR']

                        data['inscripcion']=Inscripcion.objects.filter(persona__usuario=request.user)[:1].get()

                        if InscripcionExamen.objects.filter(inscripcion=data['inscripcion']).exists():
                            for inscripcionexamen in InscripcionExamen.objects.filter(valida=True,inscripcion=data['inscripcion'],finalizado=True):
                                inscripcionexamen.valida = False
                                inscripcionexamen.save()

                                titulo = InscripcionExamen.objects.filter(inscripcion=data['inscripcion'],finalizado=True,valida=True,tituloexamencondu__teleclinica=True).values('tituloexamencondu')
                                data['tituloexamen'] = TituloExamenCondu.objects.filter(activo=True,teleclinica=True).exclude(id__in=titulo).order_by('tituloexamen')
                        else:
                            data['tituloexamen'] = TituloExamenCondu.objects.filter(activo=True,teleclinica=True).exclude().order_by('tituloexamen')
                else:
                    data['finalizaautomaticamente'] = ''
                    if InscripcionExamen.objects.filter(valida=True,finalizado=False).exists():
                        for inscripcionexamen in InscripcionExamen.objects.filter(valida=True,finalizado=False):
                            fechafinalizacion = inscripcionexamen.fecha + timedelta(hours=inscripcionexamen.tiempo.time().hour) + timedelta(minutes=inscripcionexamen.tiempo.time().minute) + timedelta(seconds=inscripcionexamen.tiempo.time().second)
                            if datetime.now() >= fechafinalizacion:
                                data['finalizaautomaticamente'] = 'existe'
                    if InscripcionExamen.objects.filter(valida=True).exists():
                        data['validainactivar'] = True
                    else:
                        data['validainactivar'] = False
                    if 'info' in request.GET:
                        data['info'] = request.GET['info']
                    data['DEFAULT_PASSWORD'] = DEFAULT_PASSWORD
                return render(request ,"teleclinica/menu.html" ,  data)
    except Exception as ex:
        return  HttpResponseRedirect('/?info='+str(ex))
