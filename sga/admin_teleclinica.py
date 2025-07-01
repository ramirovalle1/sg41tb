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
from settings import NOMBRE_INSTITUCION_EXAMEN, MEDIA_ROOT, ASIGNATURA_EXAMEN_GRADO_CONDU, DEFAULT_PASSWORD, \
    COORDINACION_UASSS
from sga.commonviews import addUserData, ip_client_address
from sga.models import TituloExamenCondu, PreguntaExamen, RespuestaExamen, Asignatura, InscripcionExamen, Carrera, \
    elimina_tildes, AsignaturaMalla, EjeFormativo
from sga.forms import BuscarDemoForm
import psycopg2

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
                    activo = True
                tiempo = datetime(datetime.now().year,datetime.now().month,datetime.now().day,int(request.POST['tiempo'].split(':')[0]),int(request.POST['tiempo'].split(':')[1]))
                if request.POST['editar'] == '0':
                    tituloexamencondu = TituloExamenCondu(
                                        nombreinstitucion = NOMBRE_INSTITUCION_EXAMEN,
                                        tituloexamen = request.POST['titulo'],
                                        asignatura_id = request.POST['asignatura'],
                                        carrera_id = request.POST['carrera'],
                                        numeropreguntas = request.POST['numeropreguntas'],
                                        descripcion = request.POST['descripcion'],
                                        link_televideo = request.POST['link_televideo'],
                                        fecha = datetime.now(),
                                        tiempo = tiempo,
                                        activo = activo,
                                        teleclinica = True)
                    mensaje = 'Adicionando'
                else:
                    tituloexamencondu = TituloExamenCondu.objects.filter(id=request.POST['editar'])[:1].get()
                    tituloexamencondu.asignatura_id = request.POST['asignatura']
                    tituloexamencondu.carrera_id = request.POST['carrera']
                    tituloexamencondu.tituloexamen = request.POST['titulo']
                    tituloexamencondu.link_televideo = request.POST['link_televideo']
                    tituloexamencondu.descripcion = request.POST['descripcion']
                    tituloexamencondu.numeropreguntas = int(request.POST['numeropreguntas'])
                    tituloexamencondu.fecha = datetime.now()
                    tituloexamencondu.tiempo = tiempo
                    tituloexamencondu.activo = activo
                    mensaje = 'Editando'
                tituloexamencondu.save()
                client_address = ip_client_address(request)
                #Log de ADICIONAR EVALUACION TELECLINICA
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(tituloexamencondu).pk,
                    object_id       = tituloexamencondu.id,
                    object_repr     = force_str(tituloexamencondu),
                    action_flag     = ADDITION,
                    change_message  = mensaje+' evaluacion (' + client_address + ')')
                if "continuar" in request.POST:
                    return HttpResponseRedirect('/admin_teleclinica?continuar='+str(tituloexamencondu.id))
            elif action == 'guardarpreg':
                respuestaexamen=None
                if request.POST['editar'] == "verpre":
                    idtitu = request.POST['idpregunexamen']
                else:
                    idtitu = request.POST['idcreaexamen']
                tituloexamencondu = TituloExamenCondu.objects.filter(id=idtitu)[:1].get()
                numero = request.POST['numero']
                pregunta = request.POST['pregunta']
                puntos = request.POST['puntos']
                if "activo" in request.POST:
                    activo = True
                else:
                    activo = False

                preguntaexamen = PreguntaExamen(
                                    tituloexamencondu = tituloexamencondu,
                                    pregunta = pregunta,
                                    numero = numero,
                                    puntos = puntos,
                                    fecha = datetime.now(),
                                    activo = activo,
                                    usuario = request.user)
                preguntaexamen.save()
                if 'imagenpr' in request.FILES:
                    imagenpr=request.FILES['imagenpr']
                    preguntaexamen.imagen = imagenpr
                    preguntaexamen.save()


                if int(request.POST['cantresp']) != 0:
                    for i in range(int(request.POST['cantresp'])):
                        respuesta = request.POST['respuesta'+str(i+1)]

                        valida = False
                        if 'valida'+str(i+1) in request.POST:
                            valida = True

                        respuestaexamen = RespuestaExamen(
                                                preguntaexamen = preguntaexamen,
                                                respuesta = respuesta,
                                                valida = valida,
                                                fecha = datetime.now(),
                                                usuario = request.user)
                        respuestaexamen.save()

                        if 'imagen'+str(i+1) in request.FILES:
                            imagen=request.FILES['imagen'+str(i+1)]
                            respuestaexamen.imagen = imagen
                            respuestaexamen.save()

                    client_address = ip_client_address(request)
                    #Log de ADICIONAR Respuestas
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(respuestaexamen).pk,
                        object_id       = respuestaexamen.id,
                        object_repr     = force_str(respuestaexamen),
                        action_flag     = ADDITION,
                        change_message  = 'Agregada respuesta de evaluacion (' + client_address + ')')
                else:
                    client_address = ip_client_address(request)
                    #Log de ADICIONAR PREGUNTAS EVALUACION
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(preguntaexamen).pk,
                        object_id       = preguntaexamen.id,
                        object_repr     = force_str(preguntaexamen),
                        action_flag     = ADDITION,
                        change_message  = 'Agregada pregunta de evaluacion (' + client_address + ')')
                if request.POST['editar'] == "verpre":
                    return HttpResponseRedirect('/admin_teleclinica?action=examen&id='+str(preguntaexamen.tituloexamencondu.id))
                if "continuar" in request.POST:
                    return HttpResponseRedirect('/admin_teleclinica?continuar='+str(preguntaexamen.tituloexamencondu.id))
            elif action == 'busrespuest':
                try:
                    result={}
                    preguntaexamen = PreguntaExamen.objects.filter(id=request.POST['idpregunta'])[:1].get()
                    result["result"]= "ok"
                    result["respuesta"]=[{"idrespuesta": str(x.id),"respuesta":(x.respuesta),"valida":str(x.valida)} for x in RespuestaExamen.objects.filter(preguntaexamen=preguntaexamen)]
                    return HttpResponse(json.dumps(result),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

            elif action == 'editarpreg':
                preguntaexamen = PreguntaExamen.objects.filter(id=request.POST['idpregunexamen'])[:1].get()

                if request.POST['addrespt'] != '0':
                    if int(request.POST['cantresp']) != 0:
                        for i in range(int(request.POST['cantresp'])):
                            respuesta = request.POST['respuesta'+str(i+1)]

                            valida = False
                            if 'valida'+str(i+1) in request.POST:
                                valida = True

                            respuestaexamen = RespuestaExamen(
                                                    preguntaexamen = preguntaexamen,
                                                    respuesta = respuesta,
                                                    valida = valida,
                                                    fecha = datetime.now(),
                                                    usuario = request.user)
                            respuestaexamen.save()

                            if 'imagen'+str(i+1) in request.FILES:
                                imagen=request.FILES['imagen'+str(i+1)]
                                respuestaexamen.imagen = imagen
                                respuestaexamen.save()

                            client_address = ip_client_address(request)
                            # Log de Editar Preguntas
                            LogEntry.objects.log_action(
                                user_id=request.user.pk,
                                content_type_id=ContentType.objects.get_for_model(preguntaexamen).pk,
                                object_id=preguntaexamen.id,
                                object_repr=force_str(preguntaexamen),
                                action_flag=ADDITION,
                                change_message='Editando Pregunta o Respuesta de evaluacion (' + client_address + ')')
                    else:
                        return HttpResponseRedirect('/admin_teleclinica?action=examen&id='+str(preguntaexamen.tituloexamencondu.id))
                else:
                    if 'activo' in request.POST:
                        activo = True
                    else:
                        activo = False
                    preguntaexamen.pregunta = request.POST['pregunta']
                    preguntaexamen.numero = request.POST['numero']
                    preguntaexamen.puntos = request.POST['puntos']
                    preguntaexamen.fecha = datetime.now()
                    preguntaexamen.activo = activo
                    preguntaexamen.usuario = request.user
                    # preguntaexamen.save()
                    if 'imagenpr' in request.FILES:
                        if preguntaexamen.imagen:
                            if (MEDIA_ROOT + '/' + str(preguntaexamen.imagen)):
                                os.remove(MEDIA_ROOT + '/' + str(preguntaexamen.imagen))
                        imagenpr=request.FILES['imagenpr']
                        preguntaexamen.imagen = imagenpr
                    preguntaexamen.save()
                    for i in range(RespuestaExamen.objects.filter(preguntaexamen=preguntaexamen).count()):
                        respuestaexamen = RespuestaExamen.objects.filter(id=request.POST['respuestaid'+str(i+1)])[:1].get()

                        valida = False
                        if 'valida'+str(i+1) in request.POST:
                            valida = True
                        respuestaexamen.respuesta = request.POST['respuesta'+str(i+1)]
                        respuestaexamen.valida = valida
                        respuestaexamen.fecha = datetime.now()
                        respuestaexamen.usuario = request.user
                        respuestaexamen.save()

                        if 'imagen'+str(i+1) in request.FILES:
                            if respuestaexamen.imagen:
                                if (MEDIA_ROOT + '/' + str(respuestaexamen.imagen)):
                                    os.remove(MEDIA_ROOT + '/' + str(respuestaexamen.imagen))
                            imagen=request.FILES['imagen'+str(i+1)]
                            respuestaexamen.imagen = imagen
                            respuestaexamen.save()
                client_address = ip_client_address(request)
                #Log de Editar Preguntas o Respuestas
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(preguntaexamen).pk,
                    object_id       = preguntaexamen.id,
                    object_repr     = force_str(preguntaexamen),
                    action_flag     = ADDITION,
                    change_message  = 'Editando Pregunta o Respuesta de evaluacion (' + client_address + ')')
                if DEFAULT_PASSWORD == "itb":
                    return HttpResponseRedirect('/admin_teleclinica?action=examen&id='+str(preguntaexamen.tituloexamencondu.id)+"&page="+request.POST['num_pages'])
                else:
                    return HttpResponseRedirect('/admin_teleclinica?action=examen&id='+str(preguntaexamen.tituloexamencondu.id))

            elif action =='consultaasignatura':
                data = {}
                try:
                    carrera = Carrera.objects.filter(pk=request.POST['idcarrera'])[:1].get()
                    ejeformativo = EjeFormativo.objects.filter(pk=9)[:1].get()
                    data ={"asignaturas":[{'id': a.asignatura.id,'asignatura': elimina_tildes(a.asignatura)} for a in  AsignaturaMalla.objects.filter(ejeformativo=ejeformativo,malla__carrera=carrera).distinct('asignatura__nombre').order_by('asignatura__nombre')]}
                    data['result'] = 'ok'
                    return HttpResponse(json.dumps(data), content_type="application/json")
                except Exception as e:
                    data['result'] = 'bad'
                    return HttpResponse(json.dumps(data), content_type="application/json")

            return HttpResponseRedirect('/admin_teleclinica')
        else:
            data={"title":"Administrador Teleclinica"}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']
                if action == "examen":
                    data['title'] = 'Ver Evaluacion'
                    tituloexamencondu = TituloExamenCondu.objects.filter(id=request.GET['id'])[:1].get()

                    data['DEFAULT_PASSWORD'] = DEFAULT_PASSWORD
                    if not tituloexamencondu.activo:
                        data['evaluacionteleclinica'] = tituloexamencondu
                        preguntaexamen = PreguntaExamen.objects.filter(tituloexamencondu=tituloexamencondu).order_by('numero')

                        paging = MiPaginador(preguntaexamen, 10)
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

                        data['preguntaexamen'] = page.object_list if DEFAULT_PASSWORD == "itb" else preguntaexamen
                        return render(request, "teleclinica/formularioevaluacion.html", data)
                    return HttpResponseRedirect('/admin_teleclinica?info=Desactivar evaluacion para editar preguntas')


                elif action == 'activa':
                   tituloexamencondu =  TituloExamenCondu.objects.filter(id=request.GET['id'])[:1].get()

                   if tituloexamencondu.activo:
                      if InscripcionExamen.objects.filter(tituloexamencondu=tituloexamencondu,valida=True,finalizado=True).count() != InscripcionExamen.objects.filter(tituloexamencondu = tituloexamencondu,valida=True).count():
                          return HttpResponseRedirect('/admin_teleclinica?info=Faltan evaluaciones por finalizar')
                      activo = False
                      mensaje = 'Desactivacion de Evaluacion'
                   else:
                       activo = True
                       mensaje = 'Activacion de Evaluacion'
                   tituloexamencondu.activo = activo
                   tituloexamencondu.save()

                   client_address = ip_client_address(request)
                   #Log de cambio de estado de evaluacion
                   LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(tituloexamencondu).pk,
                        object_id       = tituloexamencondu.id,
                        object_repr     = force_str(tituloexamencondu),
                        action_flag     = ADDITION,
                        change_message  = mensaje +' de teleclinica  (' + client_address + ')')
                   return HttpResponseRedirect('/admin_teleclinica')

                elif action == 'eliminpreg':
                   preguntaexamen =  PreguntaExamen.objects.filter(id=request.GET['id'])[:1].get()
                   tituloexamencondu = preguntaexamen.tituloexamencondu
                   if RespuestaExamen.objects.filter(preguntaexamen=preguntaexamen).exists():
                      respuestaexamen = RespuestaExamen.objects.filter(preguntaexamen=preguntaexamen)
                      respuestaexamen.delete()
                   preguntaexamen.delete()
                   s = ""
                   if "page" in request.GET:
                       s = "&page="+request.GET['page']
                   client_address = ip_client_address(request)
                   #Log de eliminar pregunta
                   LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(tituloexamencondu).pk,
                        object_id       = tituloexamencondu.id,
                        object_repr     = force_str(tituloexamencondu),
                        action_flag     = ADDITION,
                        change_message  = 'Eliminacion de pregunta de evaluacion  (' + client_address + ')')
                   return HttpResponseRedirect('/admin_teleclinica?action=examen&id='+str(tituloexamencondu.id)+s)

                elif action == "eliminaresp":
                    respuestaexamen = RespuestaExamen.objects.filter(id=request.GET['id'])[:1].get()
                    idpregunt = respuestaexamen.preguntaexamen.tituloexamencondu.id
                    if respuestaexamen.imagen:
                        if (MEDIA_ROOT + '/' + str(respuestaexamen.imagen)):
                            os.remove(MEDIA_ROOT + '/' + str(respuestaexamen.imagen))
                    respuestaexamen.delete()
                    return HttpResponseRedirect('/admin_teleclinica?action=examen&id='+str(idpregunt))
                elif action == "eliminarpreg":
                    tituloexamencondu = TituloExamenCondu.objects.filter(id=request.GET['id'])[:1].get()
                    tituloexamencondu.delete()
                    return HttpResponseRedirect('/admin_teleclinica')
            else:
                search = None
                if 's' in request.GET:
                    search = request.GET['s']
                if search:
                    tituloexamencondu = TituloExamenCondu.objects.filter(tituloexamen__icontains=search,teleclinica=True).order_by('-fecha')
                else:
                    tituloexamencondu = TituloExamenCondu.objects.filter(teleclinica=True).order_by('-id')

                data['evaluacionteleclinica'] = tituloexamencondu
                data['NOMBRE_INSTITUCION_EXAMEN'] = NOMBRE_INSTITUCION_EXAMEN
                carreras = Carrera.objects.filter(activo=True, carrera=True, vigente=True, teleclinica=True)
                data['carreras'] = carreras
                ejeformativo = EjeFormativo.objects.filter(pk=9)[:1].get()
                asignatura= AsignaturaMalla.objects.filter(ejeformativo=ejeformativo,malla__carrera__in=carreras).values('asignatura')
                data['asignatura2'] = Asignatura.objects.filter(pk__in=asignatura)

                if 'continuar' in request.GET:
                    data['continuar'] = request.GET['continuar']
                    data['preguntaex'] = 1
                    if PreguntaExamen.objects.filter(tituloexamencondu__id=request.GET['continuar']).exists():
                        data['preguntaex'] = PreguntaExamen.objects.filter(tituloexamencondu__id=request.GET['continuar']).order_by('-numero')[:1].get().numero+1
                if 'continuarpregu' in request.GET:
                    data['continuarpregu'] = PreguntaExamen.objects.filter(id=request.GET['continuarpregu'])[:1].get()
                if 'info' in request.GET:
                    data['info'] = request.GET['info']
                data['DEFAULT_PASSWORD'] = DEFAULT_PASSWORD

                paging = MiPaginador(tituloexamencondu, 15)
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
                data['demoform'] = BuscarDemoForm()

                return render(request ,"teleclinica/admin_teleclinica.html" ,  data)
    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))


