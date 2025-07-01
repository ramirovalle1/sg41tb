import json
from django.contrib.auth.decorators import login_required
from decorators import secure_module
from sga.commonviews import addUserData, ip_client_address
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from sga.models import PuntajeIndicador, SegmentoIndicadorEmp, SegmentoDetalle, IndicadorAcademico
from django.contrib.admin.models import LogEntry, ADDITION,DELETION,CHANGE
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_str

__author__ = 'jjurgiles'

@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    try:
        if request.method == 'POST':
            action = request.POST['action']
            if action == 'guardarindic':
                result = {}
                try:
                    if int(request.POST['idindic']) == 0:
                        puntajesindicadores = PuntajeIndicador(descripcion = request.POST['descripcion'],
                                                        puntos = request.POST['puntos'],
                                                        estado = json.loads(request.POST['estado']))
                        mensaje = 'Puntaje Indicador Guardado'
                    else:
                        puntajesindicadores = PuntajeIndicador.objects.get(id = request.POST['idindic'])
                        puntajesindicadores.descripcion = request.POST['descripcion']
                        puntajesindicadores.puntos = request.POST['puntos']
                        puntajesindicadores.estado = json.loads(request.POST['estado'])
                        mensaje = 'Puntaje Indicador Editado'
                    puntajesindicadores.save()
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(puntajesindicadores).pk,
                            object_id       = puntajesindicadores.id,
                            object_repr     = force_str(puntajesindicadores),
                            action_flag     = ADDITION,
                            change_message  = mensaje+' (' + client_address + ')' )

                    result['result'] ="ok"
                    return HttpResponse(json.dumps(result),content_type="application/json")
                except Exception as e:
                    print("error excep guardarindic "+str(e))
                    result['result'] ="bad"
                    result['mensaje'] ="error al guardar la informacion"
                    return HttpResponse(json.dumps(result),content_type="application/json")
            if action == 'guardarsegempr':
                result = {}
                try:
                    if int(request.POST['idindic']) == 0:
                        segmentoindicadoremp = SegmentoIndicadorEmp(descripcion = request.POST['descripcion'],
                                                                    orden = request.POST['orden'],
                                                                    estado = json.loads(request.POST['estado']))
                        mensaje = 'Segmento  Indicador Empresa Guardado'
                    else:
                        segmentoindicadoremp = SegmentoIndicadorEmp.objects.get(id = request.POST['idindic'])
                        segmentoindicadoremp.descripcion = request.POST['descripcion']
                        segmentoindicadoremp.orden = request.POST['orden']
                        segmentoindicadoremp.estado = json.loads(request.POST['estado'])
                        mensaje = 'Segmento Indicador Empresa Editado'
                    segmentoindicadoremp.save()
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(segmentoindicadoremp).pk,
                            object_id       = segmentoindicadoremp.id,
                            object_repr     = force_str(segmentoindicadoremp),
                            action_flag     = ADDITION,
                            change_message  = mensaje+' (' + client_address + ')' )

                    result['result'] ="ok"
                    return HttpResponse(json.dumps(result),content_type="application/json")
                except Exception as e:
                    print("error excep guardarsegempr  "+str(e))
                    result['result'] ="bad"
                    result['mensaje'] ="error al guardar la informacion"
                    return HttpResponse(json.dumps(result),content_type="application/json")
            if action == 'guardardetsegempr':
                result = {}
                try:
                    if int(request.POST['idindic']) == 0:
                        segmentodetalle = SegmentoDetalle(descripcion = request.POST['descripcion'],
                                                        segmentoindicador_id = request.POST['segmento'],
                                                        estado = json.loads(request.POST['estado']))
                        mensaje = 'Segmento Detalle Empresa Guardado'
                    else:
                        segmentodetalle = SegmentoDetalle.objects.get(id = request.POST['idindic'])
                        segmentodetalle.descripcion = request.POST['descripcion']
                        segmentodetalle.segmentoindicador_id = request.POST['segmento']
                        segmentodetalle.estado = json.loads(request.POST['estado'])
                        mensaje = 'Segmento Detalle Empresa Editado'
                    segmentodetalle.save()
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(segmentodetalle).pk,
                            object_id       = segmentodetalle.id,
                            object_repr     = force_str(segmentodetalle),
                            action_flag     = ADDITION,
                            change_message  = mensaje+' (' + client_address + ')' )

                    result['result'] ="ok"
                    return HttpResponse(json.dumps(result),content_type="application/json")
                except Exception as e:
                    print("error excep guardardetsegempr  "+str(e))
                    result['result'] ="bad"
                    result['mensaje'] ="error al guardar la informacion"
                    return HttpResponse(json.dumps(result),content_type="application/json")
            if action == 'guardarindiacade':
                result = {}
                try:
                    if int(request.POST['idindic']) == 0:
                        indicadoracademico = IndicadorAcademico(descripcion = request.POST['descripcion'],
                                                        estado = json.loads(request.POST['estado']))
                        mensaje = 'Indicador Academico Guardado'
                    else:
                        indicadoracademico = IndicadorAcademico.objects.get(id = request.POST['idindic'])
                        indicadoracademico.descripcion = request.POST['descripcion']
                        indicadoracademico.estado = json.loads(request.POST['estado'])
                        mensaje = 'Indicador AcademicoEmpresa Editado'
                    indicadoracademico.save()
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(indicadoracademico).pk,
                            object_id       = indicadoracademico.id,
                            object_repr     = force_str(indicadoracademico),
                            action_flag     = ADDITION,
                            change_message  = mensaje+' (' + client_address + ')' )

                    result['result'] ="ok"
                    return HttpResponse(json.dumps(result),content_type="application/json")
                except Exception as e:
                    print("error excep guardarindiacade  "+str(e))
                    result['result'] ="bad"
                    result['mensaje'] ="error al guardar la informacion"
                    return HttpResponse(json.dumps(result),content_type="application/json")
        else:
            data = {'title':'supervisor'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']
                if action == 'indicador':
                    puntajesindicadores = PuntajeIndicador.objects.all()
                    if 'noti' in request.GET:
                        if  int(request.GET['noti'])==1:
                            data['noti'] = 'Registro Eliminado'
                    data['puntajesindicadores'] =puntajesindicadores
                    return render(request ,"paramevalpract/puntajeindicador.html" ,  data)
                elif action == 'estadopun':
                    puntajesindicador = PuntajeIndicador.objects.get(id=request.GET['id'])
                    puntajesindicador.estado = not puntajesindicador.estado
                    puntajesindicador.save()
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(puntajesindicador).pk,
                            object_id       = puntajesindicador.id,
                            object_repr     = force_str(puntajesindicador),
                            action_flag     = CHANGE,
                            change_message  = 'Cambio de estado puntajesindicador (' + client_address + ')' )
                    return HttpResponseRedirect('/paramevalpract?action=indicador')
                elif action == 'delreg':
                    puntajesindicador = PuntajeIndicador.objects.get(id=request.GET['id'])

                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(puntajesindicador).pk,
                            object_id       = puntajesindicador.id,
                            object_repr     = force_str(puntajesindicador),
                            action_flag     = CHANGE,
                            change_message  = 'Eliminado registro puntajesindicador (' + client_address + ')' )
                    puntajesindicador.delete()
                    return HttpResponseRedirect('/paramevalpract?action=indicador&noti=1')
                elif action == 'segmentoin':
                    segmentoindicadoremp = SegmentoIndicadorEmp.objects.all().order_by('orden')
                    if 'noti' in request.GET:
                        if  int(request.GET['noti'])==1:
                            data['noti'] = 'Registro Eliminado'
                    data['segmentoindicadoremp'] =segmentoindicadoremp
                    return render(request ,"paramevalpract/segmentoindiempre.html" ,  data)
                elif action == 'estadoseemp':
                    segmentoindicadoremp = SegmentoIndicadorEmp.objects.get(id=request.GET['id'])
                    segmentoindicadoremp.estado = not segmentoindicadoremp.estado
                    segmentoindicadoremp.save()
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(segmentoindicadoremp).pk,
                            object_id       = segmentoindicadoremp.id,
                            object_repr     = force_str(segmentoindicadoremp),
                            action_flag     = CHANGE,
                            change_message  = 'Cambio de estado segmentoindicadoremp(' + client_address + ')' )
                    return HttpResponseRedirect('/paramevalpract?action=segmentoin')
                elif action == 'delregseg':
                    segmentoindicadoremp = SegmentoIndicadorEmp.objects.get(id=request.GET['id'])

                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(segmentoindicadoremp).pk,
                            object_id       = segmentoindicadoremp.id,
                            object_repr     = force_str(segmentoindicadoremp),
                            action_flag     = CHANGE,
                            change_message  = 'Eliminado registro segmentoindicadoremp (' + client_address + ')' )
                    segmentoindicadoremp.delete()
                    return HttpResponseRedirect('/paramevalpract?action=segmentoin&noti=1')
                elif action == 'detsegmentoin':
                    segmentodetalle = SegmentoDetalle.objects.all()
                    if 'noti' in request.GET:
                        if  int(request.GET['noti'])==1:
                            data['noti'] = 'Registro Eliminado'
                    data['segmentodetalle'] = segmentodetalle
                    data['segmentoindicadoremp'] = SegmentoIndicadorEmp.objects.filter(estado=True)
                    return render(request ,"paramevalpract/segmentodetinemp.html" ,  data)
                elif action == 'estadodetseemp':
                    segmentodetalle = SegmentoDetalle.objects.get(id=request.GET['id'])
                    segmentodetalle.estado = not segmentodetalle.estado
                    segmentodetalle.save()
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(segmentodetalle).pk,
                            object_id       = segmentodetalle.id,
                            object_repr     = force_str(segmentodetalle),
                            action_flag     = CHANGE,
                            change_message  = 'Cambio de estado segmentodetalle (' + client_address + ')' )
                    return HttpResponseRedirect('/paramevalpract?action=detsegmentoin')
                elif action == 'deldetseg':
                    segmentodetalle = SegmentoDetalle.objects.get(id=request.GET['id'])

                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(segmentodetalle).pk,
                            object_id       = segmentodetalle.id,
                            object_repr     = force_str(segmentodetalle),
                            action_flag     = CHANGE,
                            change_message  = 'Eliminado registro segmentodetalle (' + client_address + ')' )
                    segmentodetalle.delete()
                    return HttpResponseRedirect('/paramevalpract?action=detsegmentoin&noti=1')
                elif action == 'indicadinst':
                    indicadoracademico = IndicadorAcademico.objects.all()
                    if 'noti' in request.GET:
                        if  int(request.GET['noti'])==1:
                            data['noti'] = 'Registro Eliminado'
                    data['indicadoracademico'] =indicadoracademico
                    return render(request ,"paramevalpract/indicadoracademico.html" ,  data)
                if action == 'estadoindacad':
                    indicadoracademico = IndicadorAcademico.objects.get(id=request.GET['id'])
                    indicadoracademico.estado = not indicadoracademico.estado
                    indicadoracademico.save()
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(indicadoracademico).pk,
                            object_id       = indicadoracademico.id,
                            object_repr     = force_str(indicadoracademico),
                            action_flag     = CHANGE,
                            change_message  = 'Cambio de estado indicadoracademico(' + client_address + ')' )
                    return HttpResponseRedirect('/paramevalpract?action=indicadinst')
                elif action == 'delindacad':
                    indicadoracademico = IndicadorAcademico.objects.get(id=request.GET['id'])

                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(indicadoracademico).pk,
                            object_id       = indicadoracademico.id,
                            object_repr     = force_str(indicadoracademico),
                            action_flag     = CHANGE,
                            change_message  = 'Eliminado registro indicadoracademico (' + client_address + ')' )
                    indicadoracademico.delete()
                    return HttpResponseRedirect('/paramevalpract?action=indicadinst&noti=1')
            else:
                return render(request ,"paramevalpract/menu.html" ,  data)
    except Exception as e:
        print("Error en paramevalpract"+str(e))
        return HttpResponseRedirect("/?info=Error comuniquese con el administrador")
