from datetime import datetime
import json
import os
from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
from decorators import secure_module
from settings import MEDIA_ROOT
from sga.commonviews import addUserData, ip_client_address
from sga.models import Asignatura, PreguntaAsignatura, PreguntaAsigRespuesta, Carrera


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
            if action == 'copiar':
                try:
                    asignprin = Asignatura.objects.filter(id=request.POST['asignprin'])[:1].get()
                    carrprin = Carrera.objects.filter(id=request.POST['carrprin'])[:1].get()
                    asigncop = Asignatura.objects.filter(id=request.POST['asigncop'])[:1].get()
                    carrcop = Carrera.objects.filter(id=request.POST['carrcop'])[:1].get()
                    for p in PreguntaAsignatura.objects.filter(asignatura=asignprin,carrera=carrprin).order_by('numero'):
                        preguntaasignatura = PreguntaAsignatura(
                                        carrera = carrcop,
                                        asignatura = asigncop,
                                        pregunta = p.pregunta,
                                        numero = p.numero,
                                        puntos = p.puntos,
                                        fecha = datetime.now(),
                                        activo = p.activo,
                                        usuario = request.user)
                        if p.imagen:
                            preguntaasignatura.imagen = p.imagen
                        preguntaasignatura.save()
                        for re in PreguntaAsigRespuesta.objects.filter(preguntaasignatura=p).order_by('id'):
                            preguntaasirespuesta = PreguntaAsigRespuesta(
                                                    preguntaasignatura = preguntaasignatura,
                                                    respuesta = re.respuesta,
                                                    valida = re.valida,
                                                    fecha = datetime.now(),
                                                    usuario = request.user)
                            if re.imagen:
                                preguntaasirespuesta.imagen = re.imagen
                            preguntaasirespuesta.save()
                    client_address = ip_client_address(request)
                    #Log de ADICIONAR INSCRIPCION
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(asignprin).pk,
                        object_id       = asignprin.id,
                        object_repr     = force_str(asignprin),
                        action_flag     = ADDITION,
                        change_message  = 'Preguntas copiadas de la asignatura (' + client_address + ')')
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as e:
                    print(e)
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
            elif action == 'guardarpreg':
                idasign = request.POST['idpregunexamen']
                idcar = request.POST['idcar']
                asignatura = Asignatura.objects.filter(id=idasign)[:1].get()
                carrera = Carrera.objects.filter(id=idcar)[:1].get()
                numero = request.POST['numero']
                pregunta = request.POST['pregunta']
                puntos = request.POST['puntos']
                if "activo" in request.POST:
                    activo = True
                else:
                    activo = False

                preguntaasignatura = PreguntaAsignatura(
                                    carrera = carrera,
                                    asignatura = asignatura,
                                    pregunta = pregunta,
                                    numero = numero,
                                    puntos = puntos,
                                    fecha = datetime.now(),
                                    activo = activo,
                                    usuario = request.user)
                preguntaasignatura.save()
                if 'imagenpr' in request.FILES:
                    imagenpr=request.FILES['imagenpr']
                    preguntaasignatura.imagen = imagenpr
                    preguntaasignatura.save()


                if int(request.POST['cantresp']) != 0:
                    for i in range(int(request.POST['cantresp'])):
                        respuesta = request.POST['respuesta'+str(i+1)]

                        valida = False
                        if 'valida'+str(i+1) in request.POST:
                            valida = True

                        preguntaasirespuesta = PreguntaAsigRespuesta(
                                                preguntaasignatura = preguntaasignatura,
                                                respuesta = respuesta,
                                                valida = valida,
                                                fecha = datetime.now(),
                                                usuario = request.user)
                        preguntaasirespuesta.save()

                        if 'imagen'+str(i+1) in request.FILES:
                            imagen=request.FILES['imagen'+str(i+1)]
                            preguntaasirespuesta.imagen = imagen
                            preguntaasirespuesta.save()

                    client_address = ip_client_address(request)
                    #Log de ADICIONAR INSCRIPCION
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(preguntaasirespuesta).pk,
                        object_id       = preguntaasirespuesta.id,
                        object_repr     = force_str(preguntaasirespuesta),
                        action_flag     = ADDITION,
                        change_message  = 'Adicionado Respuesta de Examen Parcial (' + client_address + ')')
                else:
                    client_address = ip_client_address(request)
                    #Log de ADICIONAR INSCRIPCION
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(preguntaasignatura).pk,
                        object_id       = preguntaasignatura.id,
                        object_repr     = force_str(preguntaasignatura),
                        action_flag     = ADDITION,
                        change_message  = 'Adicionado Pregunta de Examen Parcial(' + client_address + ')')
                return HttpResponseRedirect('/preguntaasignatura?idcar='+str(carrera.id)+'&asign='+str(asignatura.id))
            elif action == 'busrespuest':
                try:
                    result={}
                    preguntaasignatura = PreguntaAsignatura.objects.get(id=request.POST['idpregunta'])
                    result["result"]= "ok"
                    result["respuesta"]=[{"idrespuesta": str(x.id),"respuesta":(x.respuesta),"valida":str(x.valida)} for x in PreguntaAsigRespuesta.objects.filter(preguntaasignatura=preguntaasignatura)]
                    return HttpResponse(json.dumps(result),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
            elif action == 'editarpreg':
                preguntaasignatura = PreguntaAsignatura.objects.filter(id=request.POST['idpregunexamen'])[:1].get()

                if request.POST['addrespt'] != '0':
                    if int(request.POST['cantresp']) != 0:
                        for i in range(int(request.POST['cantresp'])):
                            respuesta = request.POST['respuesta'+str(i+1)]

                            valida = False
                            if 'valida'+str(i+1) in request.POST:
                                valida = True

                            preguntaasigrespuesta = PreguntaAsigRespuesta(
                                                    preguntaasignatura = preguntaasignatura,
                                                    respuesta = respuesta,
                                                    valida = valida,
                                                    fecha = datetime.now(),
                                                    usuario = request.user)
                            preguntaasigrespuesta.save()

                            if 'imagen'+str(i+1) in request.FILES:
                                imagen=request.FILES['imagen'+str(i+1)]
                                preguntaasigrespuesta.imagen = imagen
                                preguntaasigrespuesta.save()
                    else:
                        return HttpResponseRedirect('/preguntaasignatura?idcar='+str(preguntaasignatura.carrera.id)+'&asign='+str(preguntaasignatura.asignatura.id)+"&page="+request.POST['num_pages'])
                else:
                    if 'activo' in request.POST:
                        activo = True
                    else:
                        activo = False
                    preguntaasignatura.pregunta = request.POST['pregunta']
                    preguntaasignatura.numero = request.POST['numero']
                    preguntaasignatura.puntos = request.POST['puntos']
                    preguntaasignatura.fecha = datetime.now()
                    preguntaasignatura.activo = activo
                    preguntaasignatura.usuario = request.user
                    # preguntaexamen.save()
                    if 'imagenpr' in request.FILES:
                        if preguntaasignatura.imagen:
                            if os.path.exists(MEDIA_ROOT + '/' + str(preguntaasignatura.imagen)):
                                os.remove(MEDIA_ROOT + '/' + str(preguntaasignatura.imagen))
                        imagenpr=request.FILES['imagenpr']
                        preguntaasignatura.imagen = imagenpr
                    preguntaasignatura.save()
                    for i in range(PreguntaAsigRespuesta.objects.filter(preguntaasignatura=preguntaasignatura).count()):
                        preguntaasigrespuesta = PreguntaAsigRespuesta.objects.get(id=request.POST['respuestaid'+str(i+1)])

                        valida = False
                        if 'valida'+str(i+1) in request.POST:
                            valida = True
                        preguntaasigrespuesta.respuesta = request.POST['respuesta'+str(i+1)]
                        preguntaasigrespuesta.valida = valida
                        preguntaasigrespuesta.fecha = datetime.now()
                        preguntaasigrespuesta.usuario = request.user
                        preguntaasigrespuesta.save()

                        if 'imagen'+str(i+1) in request.FILES:
                            if preguntaasigrespuesta.imagen:
                                if os.path.exists(MEDIA_ROOT + '/' + str(preguntaasigrespuesta.imagen)):
                                    os.remove(MEDIA_ROOT + '/' + str(preguntaasigrespuesta.imagen))
                            imagen=request.FILES['imagen'+str(i+1)]
                            preguntaasigrespuesta.imagen = imagen
                            preguntaasigrespuesta.save()
                client_address = ip_client_address(request)
                #Log de ADICIONAR INSCRIPCION
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(preguntaasignatura).pk,
                    object_id       = preguntaasignatura.id,
                    object_repr     = force_str(preguntaasignatura),
                    action_flag     = ADDITION,
                    change_message  = 'Editando Pregunta o Respuesta de Examen Parcial (' + client_address + ')')
                return HttpResponseRedirect('/preguntaasignatura?idcar='+str(preguntaasignatura.carrera.id)+'&asign='+str(preguntaasignatura.asignatura.id)+"&page="+request.POST['num_pages'])
            return HttpResponseRedirect('/preguntaasignatura')
        else:
            data = {'title':'Pregunta Asignatura'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']
                if action == 'activpregunta':
                   preguntaasignatura =  PreguntaAsignatura.objects.get(id=request.GET['id'])
                   s = ""
                   if "page" in request.GET:
                      s = "&page="+request.GET['page']

                   if preguntaasignatura.activo:
                      activo = False
                      mensaje = 'Desactivacion de Examen'
                   else:
                       activo = True
                       mensaje = 'Activacion de Examen'
                   preguntaasignatura.activo = activo
                   preguntaasignatura.save()

                   client_address = ip_client_address(request)
                   #Log de ADICIONAR INSCRIPCION
                   LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(preguntaasignatura).pk,
                        object_id       = preguntaasignatura.id,
                        object_repr     = force_str(preguntaasignatura),
                        action_flag     = ADDITION,
                        change_message  = mensaje +' de conduccion  (' + client_address + ')')
                   return HttpResponseRedirect('/preguntaasignatura?idcar='+str(preguntaasignatura.carrera.id)+'&asign='+str(preguntaasignatura.asignatura.id)+s)

                elif action == 'eliminpreg':
                   preguntaasignatura =  PreguntaAsignatura.objects.filter(id=request.GET['id'])[:1].get()
                   asignatura = preguntaasignatura.asignatura
                   carrera = preguntaasignatura.carrera
                   if PreguntaAsigRespuesta.objects.filter(preguntaasignatura=preguntaasignatura).exists():
                      for presp in  PreguntaAsigRespuesta.objects.filter(preguntaasignatura=preguntaasignatura):
                          if presp.imagen:
                            if os.path.exists(MEDIA_ROOT+'/'+str(presp.imagen)):
                                os.remove(MEDIA_ROOT+'/'+str(presp.imagen))
                          presp.delete()
                   s = ""
                   if "page" in request.GET:
                       s = "&page="+request.GET['page']
                   client_address = ip_client_address(request)
                   #Log de ADICIONAR INSCRIPCION
                   LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(preguntaasignatura).pk,
                        object_id       = preguntaasignatura.id,
                        object_repr     = force_str(preguntaasignatura),
                        action_flag     = ADDITION,
                        change_message  = 'Eliminacion de pregunta de examen parcial (' + client_address + ')')
                   if preguntaasignatura.imagen:
                        if os.path.exists(MEDIA_ROOT+'/'+str(preguntaasignatura.imagen)):
                            os.remove(MEDIA_ROOT+'/'+str(preguntaasignatura.imagen))
                   preguntaasignatura.delete()
                   return HttpResponseRedirect('/preguntaasignatura?idcar='+str(carrera.id)+'&asign='+str(asignatura.id)+s)

                elif action == "eliminaresp":
                    preguntaasigrespuesta = PreguntaAsigRespuesta.objects.filter(id=request.GET['id'])[:1].get()
                    idpregunt = preguntaasigrespuesta.preguntaasignatura
                    if preguntaasigrespuesta.imagen:
                        if os.path.exists(MEDIA_ROOT + '/' + str(preguntaasigrespuesta.imagen)):
                            os.remove(MEDIA_ROOT + '/' + str(preguntaasigrespuesta.imagen))
                    client_address = ip_client_address(request)
                    #Log de ADICIONAR INSCRIPCION
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(preguntaasigrespuesta).pk,
                        object_id       = preguntaasigrespuesta.id,
                        object_repr     = force_str(preguntaasigrespuesta),
                        action_flag     = ADDITION,
                        change_message  = 'Eliminacion de respuesta de examen parcial (' + client_address + ')')
                    preguntaasigrespuesta.delete()
                    return HttpResponseRedirect('/preguntaasignatura?idcar='+str(idpregunt.carrera.id)+'&asign='+str(idpregunt.asignatura.id))
            else:
                s = ''
                asignaturas = Asignatura.objects.filter()
                car = ''
                if 'idcar' in request.GET:
                    car = Carrera.objects.get(id=request.GET['idcar'])
                    data['carrera'] = car
                if 'asign' in request.GET:
                    asign = Asignatura.objects.get(id=request.GET['asign'])

                    if 's' in request.GET:
                        s = request.GET['s']
                        preguntasasignatara = PreguntaAsignatura.objects.filter(carrera=car,asignatura=asign,pregunta__icontains=s).order_by('numero')
                    else:
                        preguntasasignatara = PreguntaAsignatura.objects.filter(carrera=car,asignatura=asign).order_by('numero')
                    data['asign'] = asign

                    data['s'] = s
                    paging = MiPaginador(preguntasasignatara, 10)
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
                    data['numpag'] = p

                    data['preguntasasignatura'] = page.object_list
                data['asignaturas'] = asignaturas
                return render(request ,"examenparcial/preguntaasignatura.html" ,  data)

    except Exception as e:
        print('ERROR EXCEP '+str(e))
        return HttpResponseRedirect('/?info=Error en excepcion intentelo nuevamente o comuniquese con el Administrador')