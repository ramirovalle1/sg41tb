import json

from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from datetime import datetime
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
from sga.commonviews import ip_client_address, addUserData
from sga.estudiantesxdesertar import MiPaginador
from sga.models import EjesEvaluacion, PreguntasEvaluacion, RespuestasEvaluacion, RespuestasEjesEvaluacion, DetalleEvaluacionAlumno, AreasElementosEvaluacion, DetalleEvaluacionPregunta


def view(request):
    if request.method=='POST':

        if 'action' in request.POST:
            action = request.POST['action']
            if action=='add':
                data = {'title': ''}
                lisFormacion = []
                try:
                    # if not RespuestasEvaluacion.objects.filter(nombre=request.POST['nombre']).exists():
                        respuesta=RespuestasEvaluacion(nombre=request.POST['nombre'],puntaje=request.POST['puntaje'], estado=request.POST['estado'])
                        respuesta.save()
                        msj = 'Guardado registro'
                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id=request.user.pk,
                            content_type_id=ContentType.objects.get_for_model(respuesta).pk,
                            object_id=respuesta.id,
                            object_repr=force_str(respuesta),
                            action_flag=ADDITION,
                            change_message=msj + ' (' + client_address + ')')
                        # if RespuestaEjeEvaluacionDirectivo.objects.filter(pk=request.POST['eje']).exists():
                        #     eje=RespuestaEjeEvaluacionDirectivo.objects.filter(pk=request.POST['eje'])[:1].get()
                        #     respuesta.respuestadirectivo=eje
                        #     respuesta.save()
                        data['result'] = 'ok'
                        for a in RespuestasEvaluacion.objects.filter().order_by('nombre'):
                            lisFormacion.append(
                                {"id": a.id, "nombre": a.nombre, 'puntaje': a.puntaje, "estado":a.estado})
                        data['lisFormacion']=lisFormacion
                        return HttpResponse(json.dumps(data), content_type="application/json")
                    # else:
                    #     data['result'] = 'bad'
                    #     data['error'] = 'Ya existe una respuesta con esa descripcion'
                    #     return HttpResponse(json.dumps(data), content_type="application/json")
                except Exception as e:
                    return HttpResponseRedirect("/encuestasevaluacion?error="+str(e))

            if action=='addarea':
                data = {'title': ''}
                lisFormacion = []
                try:

                    if not AreasElementosEvaluacion.objects.filter(descripcion=request.POST['descripcion']).exists():
                        area=AreasElementosEvaluacion(descripcion=request.POST['descripcion'],
                                            )
                        area.save()
                        if request.POST['docente']=='true':
                            area.docente=True
                            area.save()
                        else:
                            area.docente=False
                            area.save()
                        if request.POST['estado']=='true':
                            area.activo=True
                            area.save()
                        else:
                            area.activo=False
                            area.save()
                        if request.POST['directivo']=='true':
                            area.directivo=True
                            area.save()
                        else:
                            area.directivo=False
                            area.save()
                        # if request.POST['directivocargo']=='true':
                        #     ejes.directivocargo=True
                        #     ejes.save()
                        # else:
                        #     ejes.directivocargo=False
                        #     ejes.save()
                        msj = 'Guardado registro'
                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id=request.user.pk,
                            content_type_id=ContentType.objects.get_for_model(area).pk,
                            object_id=area.id,
                            object_repr=force_str(area),
                            action_flag=ADDITION,
                            change_message=msj + ' (' + client_address + ')')
                        data['result'] = 'ok'
                        for a in AreasElementosEvaluacion.objects.filter():
                            lisFormacion.append(
                                {"id": a.id,
                                 "descripcion": a.descripcion,
                                 'estado': a.activo,
                                 # 'orden':a.orden,
                                 'docente':a.docente,'directivo':a.directivo})
                        data['lisFormacion']=lisFormacion
                        return HttpResponse(json.dumps(data), content_type="application/json")

                except Exception as e:
                    return HttpResponseRedirect("/encuestasevaluacion?error="+str(e))

            if action=='addeje':
                data = {'title': ''}
                lisFormacion = []
                try:

                    if not EjesEvaluacion.objects.filter(descripcion=request.POST['descripcion']).exists():
                        ejes=EjesEvaluacion(descripcion=request.POST['descripcion'],
                                            orden=request.POST['orden'])
                        ejes.save()
                        if request.POST['docente']=='true':
                            ejes.docente=True
                            ejes.save()
                        else:
                            ejes.docente=False
                            ejes.save()
                        if request.POST['estado']=='true':
                            ejes.estado=True
                            ejes.save()
                        else:
                            ejes.estado=False
                            ejes.save()
                        if request.POST['directivo']=='true':
                            ejes.directivo=True
                            ejes.save()
                        else:
                            ejes.directivo=False
                            ejes.save()
                        if request.POST['decano']=='true':
                            ejes.directivocargo=True
                            ejes.save()
                        else:
                            ejes.decano=False
                            ejes.save()
                        # if request.POST['directivocargo']=='true':
                        #     ejes.directivocargo=True
                        #     ejes.save()
                        # else:
                        #     ejes.directivocargo=False
                        #     ejes.save()
                        msj = 'Guardado registro'
                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id=request.user.pk,
                            content_type_id=ContentType.objects.get_for_model(ejes).pk,
                            object_id=ejes.id,
                            object_repr=force_str(ejes),
                            action_flag=ADDITION,
                            change_message=msj + ' (' + client_address + ')')
                        data['result'] = 'ok'
                        for a in EjesEvaluacion.objects.filter().order_by('orden'):
                            lisFormacion.append(
                                {"id": a.id,
                                 "descripcion": a.descripcion,
                                 'estado': a.estado,
                                 'orden':a.orden,
                                 'docente':a.docente,
                                 'directivo':a.directivo,'directivocargo':a.directivocargo})
                        data['lisFormacion']=lisFormacion
                        return HttpResponse(json.dumps(data), content_type="application/json")

                except Exception as e:
                    return HttpResponseRedirect("/encuestasevaluacion?error="+str(e))
            elif action=='addpregunta':
                data = {'title': ''}
                try:
                    lisFormacion=[]
                    if EjesEvaluacion.objects.filter(pk=request.POST['eje']).exists():
                        eje=EjesEvaluacion.objects.filter(pk=request.POST['eje'])[:1].get()

                        if not PreguntasEvaluacion.objects.filter(eje=eje,nombre=request.POST['pregunta']).exists():
                            pregunta=PreguntasEvaluacion(eje=eje,
                                                         nombre=request.POST['pregunta'],
                                                         estado=request.POST['estado'],

                                                         orden=request.POST['orden'])
                            pregunta.save()

                            if request.POST['area'] != '':
                                if AreasElementosEvaluacion.objects.filter(pk=request.POST['area']).exists():
                                    area = AreasElementosEvaluacion.objects.filter(pk=request.POST['area'])[:1].get()
                                    pregunta.area=area
                                    pregunta.save()
                            # if request.POST['areadirec'] != '':
                            #     if AreasElementosEvaluacion.objects.filter(pk=request.POST['areadirec']).exists():
                            #         area = AreasElementosEvaluacion.objects.filter(pk=request.POST['areadirec'])[:1].get()
                            #         pregunta.area=area
                            #         pregunta.save()
                            msj = 'Guardado registro'
                            client_address = ip_client_address(request)
                            LogEntry.objects.log_action(
                                user_id=request.user.pk,
                                content_type_id=ContentType.objects.get_for_model(pregunta).pk,
                                object_id=pregunta.id,
                                object_repr=force_str(pregunta),
                                action_flag=ADDITION,
                                change_message=msj + ' (' + client_address + ')')
                            data['result'] = 'ok'
                            for a in PreguntasEvaluacion.objects.filter().order_by("orden"):
                                lisFormacion.append(
                                    {"id": a.id,
                                     "eje": a.eje.descripcion,
                                     'nombre': a.nombre,
                                     'estado':a.estado,
                                     'orden':a.orden,
                                     "area": a.area.descripcion if a.area else ''})
                            data['lisFormacion']=lisFormacion
                            return HttpResponse(json.dumps(data), content_type="application/json")
                        else:
                            data['result'] = 'bad'
                            data['error'] = 'Ya existe la pregunta registrada en el Eje'
                            return HttpResponse(json.dumps(data), content_type="application/json")
                    else:
                        data['result'] = 'bad'
                        data['error'] = 'No existe Eje'
                        return HttpResponse(json.dumps(data), content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps(data), content_type="application/json")
            elif action == 'addrespuestaeje':
                data = {'title': ''}
                try:
                    lisFormacion = []
                    if EjesEvaluacion.objects.filter(pk=request.POST['eje']).exists():
                        eje = EjesEvaluacion.objects.filter(pk=request.POST['eje'])[:1].get()
                        if RespuestasEvaluacion.objects.filter(pk=request.POST['respuesta']).exists():
                            respuesta=RespuestasEvaluacion.objects.filter(pk=request.POST['respuesta'])[:1].get()
                            if not RespuestasEjesEvaluacion.objects.filter(respuesta=respuesta,eje=eje).exists():
                                ejeresp = RespuestasEjesEvaluacion(eje=eje, respuesta=respuesta)
                                ejeresp.save()
                                msj = 'Guardado registro'
                                client_address = ip_client_address(request)
                                LogEntry.objects.log_action(
                                    user_id=request.user.pk,
                                    content_type_id=ContentType.objects.get_for_model(ejeresp).pk,
                                    object_id=ejeresp.id,
                                    object_repr=force_str(ejeresp),
                                    action_flag=ADDITION,
                                    change_message=msj + ' (' + client_address + ')')
                                data['result'] = 'ok'
                                for a in RespuestasEjesEvaluacion.objects.filter().order_by('eje__orden'):
                                    lisFormacion.append(
                                        {"id": a.id,
                                         "eje": a.eje.descripcion,
                                         'nombre': a.respuesta.nombre,
                                         'estado':a.estado})
                                data['lisFormacion'] = lisFormacion
                                return HttpResponse(json.dumps(data), content_type="application/json")
                            else:
                                data['result'] = 'bad'
                                data['error'] = 'Ya existe un eje con esa descripcion'
                                return HttpResponse(json.dumps(data), content_type="application/json")
                        else:
                            data['result'] = 'bad'
                            data['error'] = 'Ya existe una respuesta con esa descripcion'
                            return HttpResponse(json.dumps(data), content_type="application/json")
                    else:
                        data['result'] = 'bad'
                        data['error'] = 'Ya existe una eje con esa descripcion'
                        return HttpResponse(json.dumps(data), content_type="application/json")
                except Exception as e:
                    data['result'] = 'bad'
                    data['error'] = str(e)
                    return HttpResponse(json.dumps(data), content_type="application/json")
            if action =='quitarrespuesta':
                try:
                    lisFormacion = []
                    data = {'title': ''}
                    if not RespuestasEjesEvaluacion.objects.filter(respuesta__id=request.POST['idrespuesta']).exists() \
                            and not DetalleEvaluacionAlumno.objects.filter(respuesta__respuesta__id=request.POST['idrespuesta']).exists():
                        respuesta = RespuestasEvaluacion.objects.filter(pk=request.POST['idrespuesta'])[:1].get()


                        client_address = ip_client_address(request)

                        LogEntry.objects.log_action(
                            user_id=request.user.pk,
                            content_type_id=ContentType.objects.get_for_model(respuesta).pk,
                            object_id=respuesta.id,
                            object_repr=force_str(respuesta),
                            action_flag=DELETION,
                            change_message='Eliminado respuesta (' + client_address + ')')
                        respuesta.delete()
                        for a in RespuestasEvaluacion.objects.filter().order_by("nombre"):
                            lisFormacion.append(
                                {"id": a.id, "nombre": a.nombre, 'puntaje': a.puntaje,'estado':a.estado})
                        data['lisFormacion']=lisFormacion
                        return HttpResponse(json.dumps({'result': 'ok', 'lisFormacion': lisFormacion}),
                                            content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({'result': 'error2','message':'Ya existe una respuesta registrada en otra tabla'}), content_type="application/json")

                except Exception as e:
                    msn = str(e)
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(msn)}), content_type="application/json")
            if action =='eliminareje':
                data = {'title': ''}
                try:
                    lisFormacion = []
                    if not RespuestasEjesEvaluacion.objects.filter(eje__id=request.POST['ideje']).exists() and not DetalleEvaluacionPregunta.objects.filter(eje__id=request.POST['ideje']).exists():
                        eje = EjesEvaluacion.objects.filter(pk=request.POST['ideje'])[:1].get()

                        client_address = ip_client_address(request)

                        LogEntry.objects.log_action(
                            user_id=request.user.pk,
                            content_type_id=ContentType.objects.get_for_model(eje).pk,
                            object_id=eje.id,
                            object_repr=force_str(eje),
                            action_flag=DELETION,
                            change_message='Eliminado eje (' + client_address + ')')
                        eje.delete()
                        for a in EjesEvaluacion.objects.filter().order_by("orden"):
                            lisFormacion.append(
                                {"id": a.id, "descripcion": a.descripcion, 'estado': a.estado,'orden':a.orden, 'docente': a.docente, 'directivo': a.directivo})
                        data['lisFormacion']=lisFormacion

                        return HttpResponse(json.dumps({'result': 'ok','lisFormacion':lisFormacion}), content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({'result': 'error2','message':'Ya existe una eje registrada en otra tabla'}), content_type="application/json")

                except Exception as e:
                    msn = str(e)
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(msn)}), content_type="application/json")

            if action =='eliminaarea':
                data = {'title': ''}
                try:
                    lisFormacion = []
                    # if not AreasElementosEvaluacion.objects.filter(eje__id=request.POST['ideje']).exists() and not DetalleEvaluacionPregunta.objects.filter(eje__id=request.POST['ideje']).exists():
                    area = AreasElementosEvaluacion.objects.filter(pk=request.POST['ideje'])[:1].get()

                    client_address = ip_client_address(request)

                    LogEntry.objects.log_action(
                        user_id=request.user.pk,
                        content_type_id=ContentType.objects.get_for_model(area).pk,
                        object_id=area.id,
                        object_repr=force_str(area),
                        action_flag=DELETION,
                        change_message='Eliminado eje (' + client_address + ')')
                    area.delete()
                    for a in AreasElementosEvaluacion.objects.filter().order_by("descripcion"):
                        lisFormacion.append(
                            {"id": a.id, "descripcion": a.descripcion, 'estado': a.activo, 'docente': a.docente, 'directivo': a.directivo})
                    data['lisFormacion']=lisFormacion

                    return HttpResponse(json.dumps({'result': 'ok','lisFormacion':lisFormacion}), content_type="application/json")
                    # else:
                    #     return HttpResponse(json.dumps({'result': 'error2','message':'Ya existe una eje registrada en otra tabla'}), content_type="application/json")

                except Exception as e:
                    msn = str(e)
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(msn)}), content_type="application/json")
            if action =='quitarpregunta':
                data = {'title': ''}
                try:
                    lisFormacion = []

                    if not DetalleEvaluacionPregunta.objects.filter(pregunta__id=request.POST['idpregunta']).exists():
                        if  PreguntasEvaluacion.objects.filter(pk=request.POST['idpregunta']).exists():
                            respuesta = PreguntasEvaluacion.objects.filter(pk=request.POST['idpregunta'])[:1].get()


                            client_address = ip_client_address(request)

                            LogEntry.objects.log_action(
                                user_id=request.user.pk,
                                content_type_id=ContentType.objects.get_for_model(respuesta).pk,
                                object_id=respuesta.id,
                                object_repr=force_str(respuesta),
                                action_flag=DELETION,
                                change_message='Eliminada pregunta (' + client_address + ')')
                            respuesta.delete()
                            for a in PreguntasEvaluacion.objects.filter().order_by("orden"):
                                lisFormacion.append(
                                    {"id": a.id,
                                     "eje": a.eje.descripcion,
                                     'nombre': a.nombre,
                                     'estado': a.estado,
                                     'orden': a.orden,
                                     "area": a.area.descripcion if a.area else ''})
                            data['lisFormacion']=lisFormacion

                            return HttpResponse(json.dumps({'result': 'ok','lisFormacion':lisFormacion}), content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({'result': 'error2','message':'Ya existe una pregunta registrada en otra tabla'}), content_type="application/json")
                except Exception as e:
                    msn = str(e)
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(msn)}), content_type="application/json")
            if action =='quitarejerespuesta':
                data = {'title': ''}
                try:
                    lisFormacion = []
                    if  RespuestasEjesEvaluacion.objects.filter(pk=request.POST['idejerespuesta']).exists():
                        respuesta = RespuestasEjesEvaluacion.objects.filter(pk=request.POST['idejerespuesta'])[:1].get()
                        if not DetalleEvaluacionAlumno.objects.filter(respuesta=respuesta).exists():
                            client_address = ip_client_address(request)

                            LogEntry.objects.log_action(
                                user_id=request.user.pk,
                                content_type_id=ContentType.objects.get_for_model(respuesta).pk,
                                object_id=respuesta.id,
                                object_repr=force_str(respuesta),
                                action_flag=DELETION,
                                change_message='Eliminado eje y respuesta (' + client_address + ')')
                            respuesta.delete()
                            for a in RespuestasEjesEvaluacion.objects.filter().order_by("eje__orden"):
                                lisFormacion.append(
                                    {"id": a.id, "eje": a.eje.descripcion, 'nombre': a.respuesta.nombre, 'estado':a.estado})
                            data['lisFormacion']=lisFormacion

                            return HttpResponse(json.dumps({'result': 'ok','lisFormacion':lisFormacion}), content_type="application/json")
                        else:
                            return HttpResponse(json.dumps({'result': 'error2','message':'Ya existe una respuesta registrada en otra tabla'}), content_type="application/json")

                except Exception as e:
                    msn = str(e)
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(msn)}), content_type="application/json")
            if action=='filtrarejepre':
                data = {'title': ''}

                try:
                    lisFormacion = []
                    p=None

                    if (request.POST['eje']!=''):

                        if EjesEvaluacion.objects.filter(pk=request.POST['eje']).exists():
                            eje=EjesEvaluacion.objects.filter(pk=request.POST['eje'])[:1].get()
                            p=PreguntasEvaluacion.objects.filter(eje=eje).order_by("orden")
                    else:

                        p=PreguntasEvaluacion.objects.all().order_by("orden")
                    for a in p:
                        lisFormacion.append(
                            {"id": a.id,
                             "eje": a.eje.descripcion,
                             'nombre': a.nombre,
                             'estado':a.estado,
                             'orden':a.orden,
                             "area": a.area.descripcion if a.area else ''})
                    data['lisFormacion']=lisFormacion

                    return HttpResponse(json.dumps({'result': 'ok','lisFormacion':lisFormacion}), content_type="application/json")

                except Exception as e:
                    pass
            if action=='filtrarejeres':
                data = {'title': ''}

                try:
                    lisFormacion = []
                    p=None

                    if (request.POST['eje']!=''):

                        if EjesEvaluacion.objects.filter(pk=request.POST['eje']).exists():
                            eje=EjesEvaluacion.objects.filter(pk=request.POST['eje'])[:1].get()

                            p=RespuestasEjesEvaluacion.objects.filter(eje=eje).order_by("eje__orden")
                    else:

                        p=RespuestasEjesEvaluacion.objects.all().order_by("eje__orden")
                    for a in p:
                        lisFormacion.append(
                            {"id": a.id, "eje": a.eje.descripcion, 'nombre': a.respuesta.nombre, 'estado':a.estado, 'orden':a.eje.orden})
                    data['lisFormacion']=lisFormacion

                    return HttpResponse(json.dumps({'result': 'ok','lisFormacion':lisFormacion}), content_type="application/json")

                except Exception as e:
                    pass
            if action == 'cambiaestado':
                try:
                    lisFormacion = []
                    data = {'title': ''}
                    eje = EjesEvaluacion.objects.get(pk=request.POST['ideje'])
                    if eje.estado :
                        eje.estado = False
                    else:
                        eje.estado = True
                    eje.save()
                    client_address = ip_client_address(request)

                    # Log Editar Inscripcion
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(eje).pk,
                        object_id       = eje.id,
                        object_repr     = force_str(eje),
                        action_flag     = CHANGE,
                        change_message  = "Cambio de estado a: "+ str(eje.estado) +  '(' + client_address + ')' )

                    for a in EjesEvaluacion.objects.filter().order_by("orden"):
                        lisFormacion.append(
                            {"id": a.id, "descripcion": a.descripcion, 'estado': a.estado, 'orden':a.orden , 'docente':a.docente})
                    data['lisFormacion'] = lisFormacion
                    return HttpResponse(json.dumps({'result': 'ok', 'lisFormacion': lisFormacion}),
                                        content_type="application/json")
                except Exception as e:
                    msn = str(e)
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(msn)}), content_type="application/json")


            if action == 'cambiaestadorespuesta':

                try:
                    lisFormacion = []
                    data = {'title': ''}
                    respuesta = RespuestasEvaluacion.objects.get(pk=request.POST['idres'])

                    if respuesta.estado :
                        respuesta.estado = False

                    else:
                        respuesta.estado = True

                    respuesta.save()
                    client_address = ip_client_address(request)

                    # Log Editar Inscripcion
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(respuesta).pk,
                        object_id       = respuesta.id,
                        object_repr     = force_str(respuesta),
                        action_flag     = CHANGE,
                        change_message  = "Cambio de estado a: "+ str(respuesta.estado) +  '(' + client_address + ')' )

                    for a in RespuestasEvaluacion.objects.filter().order_by("nombre"):
                        lisFormacion.append(
                            {"id": a.id, "nombre": a.nombre, 'puntaje':a.puntaje,'estado': a.estado})
                    data['lisFormacion'] = lisFormacion
                    return HttpResponse(json.dumps({'result': 'ok', 'lisFormacion': lisFormacion}),
                                        content_type="application/json")
                except Exception as e:
                    msn = str(e)
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(msn)}), content_type="application/json")
            if action == 'cambiaestadoejerespuesta':
                try:
                    lisFormacion = []
                    data = {'title': ''}
                    respuestaeje = RespuestasEjesEvaluacion.objects.get(pk=request.POST['idejeres'])
                    if respuestaeje.estado :
                        respuestaeje.estado = False
                    else:
                        respuestaeje.estado = True
                    respuestaeje.save()
                    client_address = ip_client_address(request)

                    # Log Editar Inscripcion
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(respuestaeje).pk,
                        object_id       = respuestaeje.id,
                        object_repr     = force_str(respuestaeje),
                        action_flag     = CHANGE,
                        change_message  = "Cambio de estado a: "+ str(respuestaeje.estado) +  '(' + client_address + ')' )

                    for a in RespuestasEjesEvaluacion.objects.filter().order_by('eje__orden'):
                        lisFormacion.append(
                            {"id": a.id, "eje": a.eje.descripcion, 'nombre':a.respuesta.nombre,'estado': a.estado})
                    data['lisFormacion'] = lisFormacion
                    return HttpResponse(json.dumps({'result': 'ok', 'lisFormacion': lisFormacion}),
                                        content_type="application/json")
                except Exception as e:
                    msn = str(e)
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(msn)}), content_type="application/json")
            if action == 'cambiaestadopregunta':
                try:
                    lisFormacion = []
                    data = {'title': ''}
                    pregunta = PreguntasEvaluacion.objects.get(pk=request.POST['idpre'])
                    if pregunta.estado :
                        pregunta.estado = False
                    else:
                        pregunta.estado = True
                    pregunta.save()
                    client_address = ip_client_address(request)

                    # Log Editar Inscripcion
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(pregunta).pk,
                        object_id       = pregunta.id,
                        object_repr     = force_str(pregunta),
                        action_flag     = CHANGE,
                        change_message  = "Cambio de estado a: "+ str(pregunta.estado) +  '(' + client_address + ')' )

                    for a in PreguntasEvaluacion.objects.filter().order_by('eje__descripcion'):
                        lisFormacion.append(
                            {"id": a.id, "eje": a.eje.descripcion, 'nombre':a.nombre,'estado': a.estado, 'orden':a.orden,"area": a.area.descripcion if a.area else ''})
                    data['lisFormacion'] = lisFormacion
                    return HttpResponse(json.dumps({'result': 'ok', 'lisFormacion': lisFormacion}),
                                        content_type="application/json")
                except Exception as e:
                    msn = str(e)
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(msn)}), content_type="application/json")
    else:
        data = {'title': 'Listado Ejes de Evaluacion'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action == 'verrespuestas':
                try:

                    data = {'title': ''}
                    # data['acc'] = request.GET['acc']
                    data['respuesta'] = RespuestasEvaluacion.objects.filter().order_by('nombre')
                    data['eje'] =EjesEvaluacion.objects.filter().order_by('orden')
                    # data['eje'] = RespuestaEjeEvaluacionDirectivo.objects.filter().order_by('descripcion')
                    return render(request ,"encuestaevaluacion/verrespuesta.html" ,  data)
                except Exception as e:
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}),
                                        content_type="application/json")
            if action == 'verrejes':
                try:

                    data = {'title': ''}
                    # data['acc'] = request.GET['acc']
                    data['eje'] = EjesEvaluacion.objects.filter().order_by('orden')

                    return render(request ,"encuestaevaluacion/verejes.html" ,  data)
                except Exception as e:
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}),
                                        content_type="application/json")
            if action == 'verpreguntas':
                try:

                    data = {'title': ''}
                    # data['acc'] = request.GET['acc']
                    data['eje'] = EjesEvaluacion.objects.filter()
                    data['pregunta'] = PreguntasEvaluacion.objects.filter().order_by('orden')
                    data['areas'] = AreasElementosEvaluacion.objects.filter(activo=True).order_by('descripcion')
                    # data['areasdirectivo'] = AreasElementosEvaluacion.objects.filter(directivo=True,activo=True).order_by('descripcion')

                    return render(request ,"encuestaevaluacion/verpreguntas.html" ,  data)
                except Exception as e:
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}),
                                        content_type="application/json")
            if action == 'verejerespuesta':
                try:

                    data = {'title': ''}
                    # data['acc'] = request.GET['acc']
                    data['eje'] = EjesEvaluacion.objects.filter()
                    data['respuesta'] = RespuestasEvaluacion.objects.filter()
                    data['ejeres'] = RespuestasEjesEvaluacion.objects.filter().order_by('eje__orden')
                    return render(request ,"encuestaevaluacion/verejerespuesta.html" ,  data)
                except Exception as e:
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}),
                                        content_type="application/json")

            if action == 'verareas':
                try:

                    data = {'title': ''}
                    # data['acc'] = request.GET['acc']
                    data['area'] = AreasElementosEvaluacion.objects.filter()

                    return render(request ,"encuestaevaluacion/verareaseva.html" ,  data)
                except Exception as e:
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}),
                                        content_type="application/json")
        else:

            try:
                search = None

                if 's' in request.GET:
                    search = request.GET['s']

                if search:
                    respuestas = RespuestasEjesEvaluacion.objects.filter(nombre=search).order_by('eje__descripcion')

                else:

                    respuestas = RespuestasEjesEvaluacion.objects.all()


                paging = MiPaginador(respuestas, 30)
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
                data['search'] = search if search else ""
                # data['form'] = ParametroDescuentoForm()
                data['respuestas'] = page.object_list
                data['eje'] =EjesEvaluacion.objects.filter().order_by('orden')
                data['respuesta'] = RespuestasEvaluacion.objects.filter().order_by('puntaje')

                if 'error' in request.GET:
                    data['error']= request.GET['error']
                # data['acc'] = request.GET['acc']
                return render(request ,"encuestaevaluacion/evaluacion.html" ,  data)

            except Exception as e:
                print((e))
                return HttpResponseRedirect("/encuestaevaluacion")