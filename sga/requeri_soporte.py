from datetime import datetime
import os
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
import json
from django.contrib.admin.models import LogEntry, ADDITION, DELETION, CHANGE
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
from suds.client import Client
from decorators import secure_module
from settings import MEDIA_ROOT, EMAIL_ACTIVE
from sga.commonviews import addUserData, ip_client_address
from sga.models import RequerimientoSoporte, HorarioAsistente, Sede, Persona, RequerimSolucion, MensajesEnviado, CalificacionSoporte, TipoProblema,RespProgramdor


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
__author__ = 'jjurgiles'

@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    try:
        if request.method == 'POST':
            action = request.POST['action']
            if action == 'addrequer':
                try:
                    sede = None
                    soporte = None
                    tipopro = None
                    mensaje = None
                    persona = Persona.objects.filter(usuario=request.user)[:1].get()
                    if int(request.POST['sede']) > 0:
                        sede = Sede.objects.get(id=request.POST['sede'])
                    if int(request.POST['tipopro']) > 0:
                        tipopro = TipoProblema.objects.get(id=request.POST['tipopro'])
                    fechaactual = datetime.now()
                    # if HorarioAsistente.objects.filter(fecha=fechaactual.date(),horainicio__lte=fechaactual.time(),nolabora=False,horafin__gte=fechaactual.time(),sede=sede,programador=False).exists():
                    #     soporte = HorarioAsistente.objects.filter(fecha=fechaactual.date(),horainicio__lte=fechaactual.time(),nolabora=False,horafin__gte=fechaactual.time(),sede=sede,programador=False).order_by('sinatender','fechaasigna')[:1].get()
                    #     mensaje = "Su requerimiento sera atendido por "+str(soporte.soporte.persona.nombre_completo())
                    #     soporte.sinatender = soporte.sinatender + 1
                    #     soporte.fechaasigna = datetime.now()
                    #     soporte.save()

                    #OCastillo 18-08-2022 asignacion a Joseph requerimientos tipo correo y pagina web
                    if tipopro.id==5 or tipopro.id==7:
                        if HorarioAsistente.objects.filter(fecha=fechaactual.date(),nolabora=False,horainicio__lte=fechaactual.time(),horafin__gte=fechaactual.time(),programador=False):
                            for soporte in HorarioAsistente.objects.filter(fecha=fechaactual.date(),nolabora=False,horainicio__lte=fechaactual.time(),horafin__gte=fechaactual.time(),programador=False).order_by('sinatender','fechaasigna'):
                                if soporte.soporte.persona.pertenece_soporte_bandeja():
                                    soporte.sinatender = soporte.sinatender + 1
                                    soporte.fechaasigna = datetime.now()
                                    soporte.save()
                                    mensaje = "Su requerimiento sera atendido por "+str(soporte.soporte.persona.nombre_completo())
                                    break
                                else:
                                    soporte=None
                                    mensaje = "No hay soporte en este momento, su requerimiento sera atendido cuando el soporte inicie su turno"
                        else:
                            soporte=None
                            mensaje = "No hay soporte en este momento, su requerimiento sera atendido cuando el soporte inicie su turno"
                    else:
                        if HorarioAsistente.objects.filter(fecha=fechaactual.date(),nolabora=False,horainicio__lte=fechaactual.time(),horafin__gte=fechaactual.time(),programador=False):
                            for soporte in HorarioAsistente.objects.filter(fecha=fechaactual.date(),nolabora=False,horainicio__lte=fechaactual.time(),horafin__gte=fechaactual.time(),programador=False).order_by('sinatender','fechaasigna'):
                                if not soporte.soporte.persona.pertenece_soporte_bandeja():
                                    soporte.sinatender = soporte.sinatender + 1
                                    soporte.fechaasigna = datetime.now()
                                    soporte.save()
                                    mensaje = "Su requerimiento sera atendido por "+str(soporte.soporte.persona.nombre_completo())
                                    break
                                else:
                                    soporte=None
                                    mensaje = "No hay soporte en este momento, su requerimiento sera atendido cuando el soporte inicie su turno"
                                    pass
                        else:
                            soporte=None
                            mensaje = "No hay soporte en este momento, su requerimiento sera atendido cuando el soporte inicie su turno"

                    requerimiento = RequerimientoSoporte(sede=sede,
                                                         tipoproblema=tipopro,
                                                         persona=persona,
                                                         soporte=soporte,
                                                         requerimiento=request.POST['requerimiento'],
                                                         fecha=datetime.now())
                    if "archivo" in request.FILES:
                        requerimiento.archivo = request.FILES["archivo"]
                    requerimiento.save()
                    client_address = ip_client_address(request)
                    if EMAIL_ACTIVE:
                        requerimiento.mail_requerimiento()
                    #Log de ADICIONAR INSCRIPCION
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(requerimiento).pk,
                        object_id       = requerimiento.id,
                        object_repr     = force_str(requerimiento),
                        action_flag     = ADDITION,
                        change_message  = 'AGREGADO REQUERIMIENTO  (' + client_address + ')' )
                    return HttpResponse(json.dumps({'result': 'ok','mensaje':mensaje}), content_type="application/json")
                except Exception as e:
                    print("ERROR DE INGRESO DE MESA DE AYUDA"+str(e))
                    return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")

            if action=='leerreq':
                try:
                   if RequerimientoSoporte.objects.filter(persona__usuario=request.user, leido=False, finalizado=True).exists():
                       for r in RequerimientoSoporte.objects.filter(persona__usuario=request.user, leido=False, Finalizado=True):
                           r.leido=True
                           r.save()
                           client_address = ip_client_address(request)
                           LogEntry.objects.log_action(
                               user_id=request.user.pk,
                               content_type_id=ContentType.objects.get_for_model(r).pk,
                               object_id=r.id,
                               object_repr=force_str(r),
                               action_flag=CHANGE,
                               change_message=' SE HA MARCADO COMO LEIDO El REQUERIMIENTO (' + client_address + ')')
                   # if RequerimSolucion.objects.filter(requerimiento__persona__usuario=request.user, leido=False).exists():
                   #      for rs in RequerimSolucion.objects.filter(requerimiento__persona__usuario=request.user, leido=False):
                   #         rs.leido=True
                   #         rs.save()
                   #         client_address = ip_client_address(request)
                   #         LogEntry.objects.log_action(
                   #          user_id=request.user.pk,
                   #          content_type_id=ContentType.objects.get_for_model(rs).pk,
                   #          object_id=rs.id,
                   #          object_repr=force_str(rs),
                   #          action_flag=CHANGE,
                   #          change_message=' SE HA MARCADO COMO LEIDO LA RESPUESTA (' + client_address + ')')
                   return HttpResponse(json.dumps({'result': 'ok' }), content_type="application/json")
                except Exception as e:
                    print(e)
                    return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")



            if action == 'editrequer':
                try:
                    sede = None
                    soporte = None
                    tipopro = None
                    mensaje = None
                    if int(request.POST['sede']) > 0:
                        sede = Sede.objects.get(id=request.POST['sede'])
                    if int(request.POST['tipopro']) > 0:
                        tipopro = TipoProblema.objects.get(id=request.POST['tipopro'])
                    fechaactual = datetime.now()
                    requerimiento = RequerimientoSoporte.objects.get(id=request.POST['idrequeri'])
                    # if HorarioAsistente.objects.filter(fecha=fechaactual.date(),nolabora=False,horainicio__lte=fechaactual.time(),horafin__gte=fechaactual.time(),sede=sede,programador=False).exists():
                    #     soporte = HorarioAsistente.objects.filter(fecha=fechaactual.date(),nolabora=False,horainicio__lte=fechaactual.time(),horafin__gte=fechaactual.time(),sede=sede,programador=False).order_by('sinatender','fechaasigna')[:1].get()
                    #     mensaje = "Su requerimiento sera atendido por "+str(soporte.soporte.persona.nombre_completo())
                    #     soporte.sinatender = soporte.sinatender + 1
                    #     soporte.fechaasigna = datetime.now()
                    #     soporte.save()
                    #OCastillo 14-10-2022 en editar la misma exclusion que en addrequer
                    if not (tipopro.id==5 or tipopro.id==7):
                        if not requerimiento.soporte:
                            if HorarioAsistente.objects.filter(fecha=fechaactual.date(),nolabora=False,horainicio__lte=fechaactual.time(),horafin__gte=fechaactual.time(),programador=False):
                                soporte = HorarioAsistente.objects.filter(fecha=fechaactual.date(),nolabora=False,horainicio__lte=fechaactual.time(),horafin__gte=fechaactual.time(),programador=False).order_by('sinatender','fechaasigna')[:1].get()
                                if not soporte.soporte.persona.pertenece_soporte_bandeja():
                                    mensaje = "Su requerimiento sera atendido por "+str(soporte.soporte.persona.nombre_completo())
                                    soporte.sinatender = soporte.sinatender + 1
                                    soporte.fechaasigna = datetime.now()
                                    soporte.save()
                                else:
                                    soporte=None
                                    mensaje = "No hay soporte en este momento, su requerimiento sera atendido cuando el soporte inicie su turno"
                                    pass
                            else:
                                soporte=None
                                mensaje = "No hay soporte en este momento, su requerimiento sera atendido cuando el soporte inicie su turno"
                    else:
                        if HorarioAsistente.objects.filter(fecha=fechaactual.date(),nolabora=False,horainicio__lte=fechaactual.time(),horafin__gte=fechaactual.time(),programador=False):
                            for soporte in HorarioAsistente.objects.filter(fecha=fechaactual.date(),nolabora=False,horainicio__lte=fechaactual.time(),horafin__gte=fechaactual.time(),programador=False).order_by('sinatender','fechaasigna'):
                                if soporte.soporte.persona.pertenece_soporte_bandeja():
                                    soporte.sinatender = soporte.sinatender + 1
                                    soporte.fechaasigna = datetime.now()
                                    soporte.save()
                                    mensaje = "Su requerimiento sera atendido por "+str(soporte.soporte.persona.nombre_completo())
                                    break
                                else:
                                    soporte=None
                                    mensaje = "No hay soporte en este momento, su requerimiento sera atendido cuando el soporte inicie su turno"
                                    pass
                        else:
                            soporte=None
                            mensaje = "No hay soporte en este momento, su requerimiento sera atendido cuando el soporte inicie su turno"


                    requerimiento.sede=sede
                    requerimiento.tipoproblema=tipopro
                    requerimiento.soporte=soporte
                    requerimiento.requerimiento=request.POST['requerimiento']
                    requerimiento.fecha=datetime.now()

                    if "archivo" in request.FILES:
                        if requerimiento.archivo:
                            if os.path.exists(MEDIA_ROOT+'/'+str(requerimiento.archivo)):
                                os.remove(MEDIA_ROOT+'/'+str(requerimiento.archivo))
                        requerimiento.archivo = request.FILES["archivo"]
                    requerimiento.save()
                    client_address = ip_client_address(request)

                    #Log de ADICIONAR INSCRIPCION
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(requerimiento).pk,
                        object_id       = requerimiento.id,
                        object_repr     = force_str(requerimiento),
                        action_flag     = CHANGE,
                        change_message  = 'EDITADO REQUERIMIENTO  (' + client_address + ')' )
                    return HttpResponse(json.dumps({'result': 'ok','mensaje':mensaje}), content_type="application/json")
                except Exception as e:
                    print(e)
                    return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")
            elif action == 'eliminar':
                try:
                    requerimiento = RequerimientoSoporte.objects.get(id=request.POST['idreq'])
                    if requerimiento.soporte:
                        requerimiento.soporte.sinatender = requerimiento.soporte.sinatender - 1
                        requerimiento.soporte.save()
                    if requerimiento.archivo:
                        if os.path.exists(MEDIA_ROOT+'/'+str(requerimiento.archivo)):
                            os.remove(MEDIA_ROOT+'/'+str(requerimiento.archivo))
                    client_address = ip_client_address(request)

                    #Log de ADICIONAR INSCRIPCION
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(requerimiento).pk,
                        object_id       = requerimiento.id,
                        object_repr     = force_str(requerimiento),
                        action_flag     = DELETION,
                        change_message  = 'REQUERIMIENTO ELIMINADO  (' + client_address + ')' )

                    requerimiento.delete()
                    return HttpResponse(json.dumps({'result': 'ok','mensaje':'Registro eliminado'}), content_type="application/json")
                except Exception as e:
                    print(e)
                    return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")
            elif action == 'busqreq':
                try:
                    requerimiento = RequerimientoSoporte.objects.get(id=request.POST['idreq'])
                    html = '<h2> Requerimiento: </h2><h3>'+ requerimiento.requerimiento +'</h3>'
                    for r in requerimiento.existereqsolu():
                        html = html + '<hr><div class="row-fluid">' \
                                      '<div class="span12"><h3>Respuesta: </h3><h4>'+ r.solucion +'</h4></div></div>'
                        if r.archivo:
                            html = html + '<br><div class="row-fluid">' \
                                          '<div class="span4"><h3>Archivo: <a href="'+ r.archivo.url +'" class="btn btn-success">' \
                                          '<i class="icon-download"></i> Descargar</a></h3></div></div>'

                    return HttpResponse(json.dumps({'result': 'ok','html': html}), content_type="application/json")
                except Exception as e:
                    print(e)
                    return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")
            elif action == 'guardcalif':
                try:
                    requerimiento = RequerimientoSoporte.objects.get(id=request.POST['idreq'])
                    requerimiento.calificacion_id = request.POST['calific']
                    requerimiento.desccalificacion = request.POST['observacion']
                    requerimiento.save()
                    client_address = ip_client_address(request)

                    #Log de ADICIONAR INSCRIPCION
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(requerimiento).pk,
                        object_id       = requerimiento.id,
                        object_repr     = force_str(requerimiento),
                        action_flag     = DELETION,
                        change_message  = 'Guardando calificacion  (' + client_address + ')' )
                    return HttpResponse(json.dumps({'result': 'ok'}), content_type="application/json")
                except Exception as e:
                    print(e)
                    return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")

            elif 'addressolu' == action:
                try:
                    sede = None
                    requerimientosolu = RequerimSolucion.objects.get(id=request.POST['idrequeri'])
                    requerimientosolu.respuesta = request.POST['requerimiento']
                    requerimientosolu.fecharesp = datetime.now()

                    if "archivo" in request.FILES:
                        if requerimientosolu.archivoresp:
                            if os.path.exists(MEDIA_ROOT+'/'+str(requerimientosolu.archivoresp)):
                                os.remove(MEDIA_ROOT+'/'+str(requerimientosolu.archivoresp))
                        requerimientosolu.archivoresp = request.FILES["archivo"]
                    requerimientosolu.leido=True
                    requerimientosolu.save()
                    if EMAIL_ACTIVE:
                        requerimientosolu.mail_requerimiento("Respuesta de Requerimiento",4)
                    client_address = ip_client_address(request)

                    #Log de ADICIONAR INSCRIPCION
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(requerimientosolu).pk,
                        object_id       = requerimientosolu.id,
                        object_repr     = force_str(requerimientosolu),
                        action_flag     = ADDITION,
                        change_message  = 'AGREGADO GESTION  (' + client_address + ')' )
                    return HttpResponse(json.dumps({'result': 'ok'}), content_type="application/json")
                except Exception as e:
                    print(e)
                    return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")
        else:
            data = {'title':'Requerimiento Soporte'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']

                if action=='vergestion':
                    data = {}
                    requerimiento = RequerimientoSoporte.objects.get(id=request.GET['idreq'])
                    data['requerimiento'] = requerimiento
                    data['requerimientosol'] = RequerimSolucion.objects.filter(requerimiento=requerimiento)
                    data['sopor'] = False
                    return render(request ,"soportereque/reqsolucion.html" ,  data)

                elif action=='vergestionprogramador':
                    data = {}
                    requerimiento = RequerimientoSoporte.objects.get(id=request.GET['idreq'])
                    data['requerimiento'] = requerimiento
                    data['respprogramdor'] = RespProgramdor.objects.filter(requerimiento=requerimiento)
                    data['sopor'] = False
                    return render(request ,"soportereque/reqsolucion.html" ,  data)
            else:
                fechaactual = datetime.now()

                # if HorarioAsistente.objects.filter(fecha=fechaactual.date(),horainicio__lte=fechaactual.time(),horafin__gte=fechaactual.time()).exists():
                #     horarioasistentes = HorarioAsistente.objects.filter(fecha=fechaactual.date(),horainicio__lte=fechaactual.time(),horafin__gte=fechaactual.time())
                #     data['horarioasistentes'] = horarioasistentes
                sedes = Sede.objects.filter(solobodega=False)
                data['sedes'] = sedes
                requerimientos = None
                if 'id' in request.GET:
                    requerimientos = RequerimientoSoporte.objects.filter(id=request.GET['id']).order_by('-fecha')
                    requer = RequerimientoSoporte.objects.get(id=request.GET['id'])
                    if not requer.calificacion:
                        data['requer'] = requer
                    else:
                        requerimientos = None
                if not requerimientos:
                    if 'sincal' in request.GET:
                        requerimientos = RequerimientoSoporte.objects.filter(leido = True,persona=data['persona'],calificacion=None ).order_by('-fecha')
                        data['sincal'] = 1
                    elif 'finali' in request.GET:
                        requerimientos = RequerimientoSoporte.objects.filter(leido = True,persona=data['persona'] ).order_by('-fecha')
                    else:
                        requerimientos = RequerimientoSoporte.objects.filter(leido = False,persona=data['persona']).order_by('-fecha')
                if RequerimientoSoporte.objects.filter(persona=data['persona'],leido=False, finalizado=True).exists():
                    data['finalizados']=RequerimientoSoporte.objects.filter(persona=data['persona'],leido=False, finalizado=True).count()
                paging = MiPaginador(requerimientos, 30)
                p=1
                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                    page = paging.page(p)
                except:
                    page = paging.page(1)

                data['paging'] = paging
                data['page'] = page
                data['rangospaging'] = paging.rangos_paginado(p)
                data['finali'] = "finali" if 'finali' in request.GET else ""
                data['calificaciones'] = CalificacionSoporte.objects.filter()
                data['tipoproblemas'] = TipoProblema.objects.filter().order_by('descripcion')

                data['requerimientos'] = page.object_list
                return render(request ,"soportereque/requerisoporte.html" ,  data)

    except Exception as e:
        print(e)
        return HttpResponseRedirect("/?info=Error comuniquese con el administrador")