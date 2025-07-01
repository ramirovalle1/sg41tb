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
from settings import NOMBRE_INSTITUCION_EXAMEN, DEFAULT_PASSWORD, MEDIA_ROOT
from sga.commonviews import addUserData, ip_client_address
from sga.models import ExamenExterno, PreguntaExterno, RespuestaExterno, PersonaExamenExt, ComponenteExamen

__author__ = 'jurgiles'
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
            if action == "guardar":
                if "activo" in request.POST:
                    activo = True
                else:
                    activo = False

                tiempo = datetime(datetime.now().year,datetime.now().month,datetime.now().day,int(request.POST['tiempo'].split(':')[0]),int(request.POST['tiempo'].split(':')[1]))
                if request.POST['editar'] == '0':
                    examenexterno = ExamenExterno(
                                        nombreinstitucion = NOMBRE_INSTITUCION_EXAMEN,
                                        titulo = request.POST['titulo'],
                                        subtitulo = request.POST['subtitulo'],
                                        descripcion = request.POST['descripcion'],
                                        fecha = datetime.now(),
                                        tiempo = tiempo,
                                        activo = activo)
                    mensaje = 'Adicionando'
                else:
                    examenexterno = ExamenExterno.objects.filter(id=request.POST['editar'])[:1].get()
                    # tituloexamencondu.nombreinstitucion = NOMBRE_INSTITUCION_EXAMEN
                    examenexterno.titulo = request.POST['titulo']
                    examenexterno.subtitulo = request.POST['subtitulo']
                    examenexterno.descripcion = request.POST['descripcion']
                    examenexterno.fecha = datetime.now()
                    examenexterno.tiempo = tiempo
                    examenexterno.activo = activo
                    mensaje = 'Editando'
                examenexterno.save()
                client_address = ip_client_address(request)
                #Log de ADICIONAR INSCRIPCION
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(examenexterno).pk,
                    object_id       = examenexterno.id,
                    object_repr     = force_str(examenexterno),
                    action_flag     = ADDITION,
                    change_message  = mensaje+' Examen Externo (' + client_address + ')')
                if "continuar" in request.POST:
                    return HttpResponseRedirect('/adminexamenexterno?continuar='+str(examenexterno.id))
            elif action == 'guardarpreg':
                if request.POST['editar'] == "verpre":
                    idtitu = request.POST['idpregunexamen']
                else:
                    idtitu = request.POST['idcreaexamen']
                examenexterno = ExamenExterno.objects.filter(id=idtitu)[:1].get()
                numero = request.POST['numero']
                pregunta = request.POST['pregunta']
                puntos = request.POST['puntos']
                if "activo" in request.POST:
                    activo = True
                else:
                    activo = False

                preguntaexterno = PreguntaExterno(
                                    examenexterno = examenexterno,
                                    pregunta = pregunta,
                                    numero = numero,
                                    puntos = puntos,
                                    fecha = datetime.now(),
                                    activo = activo,
                                    usuario = request.user)
                preguntaexterno.save()
                if DEFAULT_PASSWORD == 'casade':
                    preguntaexterno.componenteexamen_id = request.POST['componenteexamen']
                    preguntaexterno.save()
                if 'imagenpr' in request.FILES:
                    imagenpr=request.FILES['imagenpr']
                    preguntaexterno.imagen = imagenpr
                    preguntaexterno.save()


                if int(request.POST['cantresp']) != 0:
                    for i in range(int(request.POST['cantresp'])):
                        respuesta = request.POST['respuesta'+str(i+1)]

                        valida = False
                        if 'valida'+str(i+1) in request.POST:
                            valida = True

                        respuestaexterno = RespuestaExterno(
                                                preguntaexterno = preguntaexterno,
                                                respuesta = respuesta,
                                                valida = valida,
                                                fecha = datetime.now(),
                                                usuario = request.user)
                        respuestaexterno.save()

                        if 'imagen'+str(i+1) in request.FILES:
                            imagen=request.FILES['imagen'+str(i+1)]
                            respuestaexterno.imagen = imagen
                            respuestaexterno.save()

                    client_address = ip_client_address(request)
                    #Log de ADICIONAR INSCRIPCION
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(preguntaexterno).pk,
                        object_id       = preguntaexterno.id,
                        object_repr     = force_str(preguntaexterno),
                        action_flag     = ADDITION,
                        change_message  = 'Adicionado Pregunta y Respuesta de Examen Externo (' + client_address + ')')
                else:
                    client_address = ip_client_address(request)
                    #Log de ADICIONAR INSCRIPCION
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(preguntaexterno).pk,
                        object_id       = preguntaexterno.id,
                        object_repr     = force_str(preguntaexterno),
                        action_flag     = ADDITION,
                        change_message  = 'Adicionado Pregunta de Examen Externo (' + client_address + ')')
                if request.POST['editar'] == "verpre":
                    return HttpResponseRedirect('/adminexamenexterno?action=examen&id='+str(preguntaexterno.examenexterno.id))
                if "continuar" in request.POST:
                    return HttpResponseRedirect('/adminexamenexterno?continuar='+str(preguntaexterno.examenexterno.id))
            elif action == 'busrespuest':
                try:
                    result={}
                    preguntaexterno = PreguntaExterno.objects.filter(id=request.POST['idpregunta'])[:1].get()
                    result["result"]= "ok"
                    result["respuesta"]=[{"idrespuesta": str(x.id),"respuesta":(x.respuesta),"valida":str(x.valida)} for x in RespuestaExterno.objects.filter(preguntaexterno=preguntaexterno)]
                    return HttpResponse(json.dumps(result),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
            elif action == 'editarpreg':
                preguntaexterno = PreguntaExterno.objects.filter(id=request.POST['idpregunexamen'])[:1].get()

                if request.POST['addrespt'] != '0':
                    if int(request.POST['cantresp']) != 0:
                        for i in range(int(request.POST['cantresp'])):
                            respuesta = request.POST['respuesta'+str(i+1)]

                            valida = False
                            if 'valida'+str(i+1) in request.POST:
                                valida = True

                            respuestaexterno = RespuestaExterno(
                                                    preguntaexterno = preguntaexterno,
                                                    respuesta = respuesta,
                                                    valida = valida,
                                                    fecha = datetime.now(),
                                                    usuario = request.user)
                            respuestaexterno.save()

                            if 'imagen'+str(i+1) in request.FILES:
                                imagen=request.FILES['imagen'+str(i+1)]
                                respuestaexterno.imagen = imagen
                                respuestaexterno.save()
                    else:
                        return HttpResponseRedirect('/adminexamenexterno?action=examen&id='+str(preguntaexterno.examenexterno.id))
                else:
                    if 'activo' in request.POST:
                        activo = True
                    else:
                        activo = False
                    preguntaexterno.pregunta = request.POST['pregunta']
                    preguntaexterno.numero = request.POST['numero']
                    preguntaexterno.puntos = request.POST['puntos']
                    preguntaexterno.fecha = datetime.now()
                    preguntaexterno.activo = activo
                    preguntaexterno.usuario = request.user
                    if DEFAULT_PASSWORD == 'casade':
                        preguntaexterno.componenteexamen_id = request.POST['componenteexamen']
                        preguntaexterno.save()

                    if 'imagenpr' in request.FILES:
                        if preguntaexterno.imagen:
                            if (MEDIA_ROOT + '/' + str(preguntaexterno.imagen)):
                                os.remove(MEDIA_ROOT + '/' + str(preguntaexterno.imagen))
                        imagenpr=request.FILES['imagenpr']
                        preguntaexterno.imagen = imagenpr
                    preguntaexterno.save()
                    for i in range(RespuestaExterno.objects.filter(preguntaexterno=preguntaexterno).count()):
                        respuestaexterno = RespuestaExterno.objects.filter(id=request.POST['respuestaid'+str(i+1)])[:1].get()

                        valida = False
                        if 'valida'+str(i+1) in request.POST:
                            valida = True
                        respuestaexterno.respuesta = request.POST['respuesta'+str(i+1)]
                        respuestaexterno.valida = valida
                        respuestaexterno.fecha = datetime.now()
                        respuestaexterno.usuario = request.user
                        respuestaexterno.save()

                        if 'imagen'+str(i+1) in request.FILES:
                            if respuestaexterno.imagen:
                                if (MEDIA_ROOT + '/' + str(respuestaexterno.imagen)):
                                    os.remove(MEDIA_ROOT + '/' + str(respuestaexterno.imagen))
                            imagen=request.FILES['imagen'+str(i+1)]
                            respuestaexterno.imagen = imagen
                            respuestaexterno.save()
                client_address = ip_client_address(request)
                #Log de ADICIONAR INSCRIPCION
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(preguntaexterno).pk,
                    object_id       = preguntaexterno.id,
                    object_repr     = force_str(preguntaexterno),
                    action_flag     = ADDITION,
                    change_message  = 'Editando Pregunta o Respuesta de Examen Externo (' + client_address + ')')
                if DEFAULT_PASSWORD == "itb":
                    return HttpResponseRedirect('/adminexamenexterno?action=examen&id='+str(preguntaexterno.examenexterno.id)+"&page="+request.POST['num_pages'])
                else:
                    return HttpResponseRedirect('/adminexamenexterno?action=examen&id='+str(preguntaexterno.examenexterno.id))
            return HttpResponseRedirect('/adminexamenexterno')
        else:
            data = {'title':'Administra Examen Externo'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']
                if action == "examen":
                    data['title'] = 'Ver Examen'
                    examenexterno = ExamenExterno.objects.filter(id=request.GET['id'])[:1].get()

                    data['DEFAULT_PASSWORD'] = DEFAULT_PASSWORD
                    if not examenexterno.activo:
                        data['examenexterno'] = examenexterno
                        if DEFAULT_PASSWORD == 'casade':
                            data['componenteexamenes'] = ComponenteExamen.objects.filter(activo = True)
                            if 'g' in request.GET:
                                data['grupoid'] = int(request.GET['g'])
                                preguntaexterno = PreguntaExterno.objects.filter(examenexterno=examenexterno,componenteexamen__id=request.GET['g']).order_by('numero')
                            else:
                                preguntaexterno = PreguntaExterno.objects.filter(examenexterno=examenexterno).order_by('numero')
                        else:
                            preguntaexterno = PreguntaExterno.objects.filter(examenexterno=examenexterno).order_by('numero')

                        paging = MiPaginador(preguntaexterno, 10)
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

                        data['preguntaexterno'] = page.object_list
                        return render(request ,"examenexterno/formularioexamenext.html" ,  data)
                    return HttpResponseRedirect('/adminexamenexterno?info=Desactivar examen para editar preguntas')


                elif action == 'activa':
                   examenexterno =  ExamenExterno.objects.filter(id=request.GET['id'])[:1].get()

                   if examenexterno.activo:
                      if PersonaExamenExt.objects.filter(examenexterno=examenexterno,valida=True,finalizado=True).count() != PersonaExamenExt.objects.filter(examenexterno = examenexterno,valida=True).count():
                          return HttpResponseRedirect('/adminexamenexterno?info=Faltan examenes por finalizar')
                      activo = False
                      mensaje = 'Desactivacion de Examen'
                   else:
                       activo = True
                       mensaje = 'Activacion de Examen'
                   examenexterno.activo = activo
                   examenexterno.save()

                   client_address = ip_client_address(request)
                   #Log de ADICIONAR INSCRIPCION
                   LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(examenexterno).pk,
                        object_id       = examenexterno.id,
                        object_repr     = force_str(examenexterno),
                        action_flag     = ADDITION,
                        change_message  = mensaje +' Externo  (' + client_address + ')')
                   return HttpResponseRedirect('/adminexamenexterno')

                elif action == 'eliminpreg':
                   preguntaexterno =  PreguntaExterno.objects.filter(id=request.GET['id'])[:1].get()
                   examenexterno = preguntaexterno.examenexterno
                   if RespuestaExterno.objects.filter(preguntaexterno=preguntaexterno).exists():
                      respuestaexterno = RespuestaExterno.objects.filter(preguntaexterno=preguntaexterno)
                      respuestaexterno.delete()
                   preguntaexterno.delete()
                   s = ""
                   if "page" in request.GET:
                       s = "&page="+request.GET['page']
                   client_address = ip_client_address(request)
                   #Log de ADICIONAR INSCRIPCION
                   LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(examenexterno).pk,
                        object_id       = examenexterno.id,
                        object_repr     = force_str(examenexterno),
                        action_flag     = ADDITION,
                        change_message  = 'Eliminacion de pregunta de Examen Externo  (' + client_address + ')')
                   return HttpResponseRedirect('/adminexamenexterno?action=examen&id='+str(examenexterno.id)+s)

                elif action == "eliminaresp":
                    respuestaexterno = RespuestaExterno.objects.filter(id=request.GET['id'])[:1].get()
                    idexamen = respuestaexterno.preguntaexterno.examenexterno.id
                    if respuestaexterno.imagen:
                        if (MEDIA_ROOT + '/' + str(respuestaexterno.imagen)):
                            os.remove(MEDIA_ROOT + '/' + str(respuestaexterno.imagen))
                    respuestaexterno.delete()
                    return HttpResponseRedirect('/adminexamenexterno?action=examen&id='+str(idexamen))
                elif action == "eliminarpreg":
                    examenexterno = ExamenExterno.objects.filter(id=request.GET['id'])[:1].get()
                    examenexterno.delete()
                    return HttpResponseRedirect('/adminexamenexterno')
            else:
                examenexterno = ExamenExterno.objects.all()
                data['examenexterno'] = examenexterno
                data['NOMBRE_INSTITUCION_EXAMEN'] = NOMBRE_INSTITUCION_EXAMEN
                if 'continuar' in request.GET:
                    data['continuar'] = request.GET['continuar']
                    data['preguntaex'] = 1
                    if PreguntaExterno.objects.filter(examenexterno__id=request.GET['continuar']).exists():
                        data['preguntaex'] = PreguntaExterno.objects.filter(examenexterno__id=request.GET['continuar']).order_by('-numero')[:1].get().numero+1
                if 'continuarpregu' in request.GET:
                    data['continuarpregu'] = PreguntaExterno.objects.filter(id=request.GET['continuarpregu'])[:1].get()
                if 'info' in request.GET:
                    data['info'] = request.GET['info']
                data['DEFAULT_PASSWORD'] = DEFAULT_PASSWORD
                if DEFAULT_PASSWORD == 'casade':
                    data['componenteexamenes'] = ComponenteExamen.objects.filter(activo = True)
                return render(request ,"examenexterno/adminexamenexterno.html" ,  data)
    except Exception as ex:
        return HttpResponseRedirect('/?info='+str(ex))
