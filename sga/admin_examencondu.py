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
from settings import NOMBRE_INSTITUCION_EXAMEN, MEDIA_ROOT, ASIGNATURA_EXAMEN_GRADO_CONDU,DEFAULT_PASSWORD
from sga.commonviews import addUserData, ip_client_address
from sga.models import TituloExamenCondu, PreguntaExamen, RespuestaExamen, Asignatura, InscripcionExamen, Carrera, \
    elimina_tildes, AsignaturaMalla
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
                    activo = False
                if "convalida" in request.POST:
                    convalida = True
                else:
                    convalida = False
                tiempo = datetime(datetime.now().year,datetime.now().month,datetime.now().day,int(request.POST['tiempo'].split(':')[0]),int(request.POST['tiempo'].split(':')[1]))
                if request.POST['editar'] == '0':
                    tituloexamencondu = TituloExamenCondu(
                                        nombreinstitucion = NOMBRE_INSTITUCION_EXAMEN,
                                        tituloexamen = request.POST['titulo'],
                                        asignatura_id = request.POST['asignatura'],
                                        carrera_id = request.POST['carrera'],
                                        subtituloexamen = request.POST['subtitulo'],
                                        descripcion = request.POST['descripcion'],
                                        fecha = datetime.now(),
                                        tiempo = tiempo,
                                        activo = activo,
                                        convalida = convalida)
                    mensaje = 'Adicionando'
                else:
                    tituloexamencondu = TituloExamenCondu.objects.filter(id=request.POST['editar'])[:1].get()
                    # tituloexamencondu.nombreinstitucion = NOMBRE_INSTITUCION_EXAMEN
                    tituloexamencondu.asignatura_id = request.POST['asignatura']
                    tituloexamencondu.carrera_id = request.POST['carrera']
                    tituloexamencondu.tituloexamen = request.POST['titulo']
                    tituloexamencondu.subtituloexamen = request.POST['subtitulo']
                    tituloexamencondu.descripcion = request.POST['descripcion']
                    tituloexamencondu.fecha = datetime.now()
                    tituloexamencondu.tiempo = tiempo
                    tituloexamencondu.activo = activo
                    tituloexamencondu.convalida = convalida
                    mensaje = 'Editando'
                tituloexamencondu.save()
                client_address = ip_client_address(request)
                #Log de ADICIONAR INSCRIPCION
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(tituloexamencondu).pk,
                    object_id       = tituloexamencondu.id,
                    object_repr     = force_str(tituloexamencondu),
                    action_flag     = ADDITION,
                    change_message  = mensaje+' examen (' + client_address + ')')
                if "continuar" in request.POST:
                    return HttpResponseRedirect('/admin_examencondu?continuar='+str(tituloexamencondu.id))
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
                    #Log de ADICIONAR INSCRIPCION
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(respuestaexamen).pk,
                        object_id       = respuestaexamen.id,
                        object_repr     = force_str(respuestaexamen),
                        action_flag     = ADDITION,
                        change_message  = 'Adicionado Respuesta de examen (' + client_address + ')')
                else:
                    client_address = ip_client_address(request)
                    #Log de ADICIONAR INSCRIPCION
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(preguntaexamen).pk,
                        object_id       = preguntaexamen.id,
                        object_repr     = force_str(preguntaexamen),
                        action_flag     = ADDITION,
                        change_message  = 'Adicionado Pregunta de examen (' + client_address + ')')
                if request.POST['editar'] == "verpre":
                    return HttpResponseRedirect('/admin_examencondu?action=examen&id='+str(preguntaexamen.tituloexamencondu.id))
                if "continuar" in request.POST:
                    return HttpResponseRedirect('/admin_examencondu?continuar='+str(preguntaexamen.tituloexamencondu.id))
            elif action == 'busrespuest':
                try:
                    result={}
                    preguntaexamen = PreguntaExamen.objects.filter(id=request.POST['idpregunta'])[:1].get()
                    result["result"]= "ok"
                    result["respuesta"]=[{"idrespuesta": str(x.id),"respuesta":(x.respuesta),"valida":str(x.valida)} for x in RespuestaExamen.objects.filter(preguntaexamen=preguntaexamen)]
                    return HttpResponse(json.dumps(result),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

            elif action == 'buscarexamen':
                try:
                    complex=str(request.POST['complexivo']).upper()
                    #prueba en desarrollo
                    # cn = psycopg2.connect("host=localhost dbname=demo_18mayo user=postgres password=aok port=5433 ")
                    # produccion
                    cn = psycopg2.connect("host=10.10.9.45 dbname=demoitb2 user=postgres password=Itb$2019 port=5432 ")
                    cur = cn.cursor()
                    cur.execute("select id,tituloexamen,subtituloexamen from sga_tituloexamencondu where tituloexamen like '%"+complex+"%'")
                    dato = cur.fetchall()
                    cur.close()
                    if len(dato)>0:
                        result  = {"examen": [{"id": str(x[0]),"titulo": elimina_tildes(x[1]),"subtitulo": elimina_tildes(x[2])} for x in dato]}
                        result['result']  = 'ok'
                        return HttpResponse(json.dumps(result), content_type="application/json")
                except Exception as e:
                    print(e)
                    return HttpResponse(json.dumps({'result': 'bad','error':'Error vuelva a ingresar el usuario'}), content_type="application/json")

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
                            # Log de ADICIONAR INSCRIPCION
                            LogEntry.objects.log_action(
                                user_id=request.user.pk,
                                content_type_id=ContentType.objects.get_for_model(preguntaexamen).pk,
                                object_id=preguntaexamen.id,
                                object_repr=force_str(preguntaexamen),
                                action_flag=ADDITION,
                                change_message='Editando Pregunta o Respuesta de examen (' + client_address + ')')
                    else:
                        return HttpResponseRedirect('/admin_examencondu?action=examen&id='+str(preguntaexamen.tituloexamencondu.id))
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
                #Log de ADICIONAR INSCRIPCION
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(preguntaexamen).pk,
                    object_id       = preguntaexamen.id,
                    object_repr     = force_str(preguntaexamen),
                    action_flag     = ADDITION,
                    change_message  = 'Editando Pregunta o Respuesta de examen (' + client_address + ')')
                if DEFAULT_PASSWORD == "itb":
                    return HttpResponseRedirect('/admin_examencondu?action=examen&id='+str(preguntaexamen.tituloexamencondu.id)+"&page="+request.POST['num_pages'])
                else:
                    return HttpResponseRedirect('/admin_examencondu?action=examen&id='+str(preguntaexamen.tituloexamencondu.id))

            #OCastillo mayo-2023 nueva funcion
            elif action == "importardemo":
                    #Para traer info del demo al academico
                    #en esta linea el id del nuevo examen en el SGA
                    tituloexamenconducion = TituloExamenCondu.objects.filter(id=request.POST['titexamen'])[:1].get()
                    db = psycopg2.connect("host=10.10.9.45 dbname=demoitb2 user=postgres password=Itb$2019 port=5432 ")
                    # db = psycopg2.connect("host=localhost dbname=demo_18mayo user=postgres password=aok port=5433 ")
                    cursor = db.cursor()
                    cursor.execute("select p.id as id, p.tituloexamencondu_id,p.pregunta, p.numero, p.puntos, p.fecha,p.activo,p.usuario_id "
                                   "from sga_preguntaexamen as p where p.tituloexamencondu_id ="+ str(request.POST['examencomplex'])+"  order by id ")

                    dato = cursor.fetchall()
                    if len(dato) > 0:
                        for x in range(len(dato)):
                            print(dato[x][0])
                            print(dato[x][1])
                            print(dato[x][2])
                            print(dato[x][3])
                            print(dato[x][4])
                            print(dato[x][5])
                            print(dato[x][6])
                            print(dato[x][7])
                            preguntaexamen = PreguntaExamen(
                                    tituloexamencondu = tituloexamenconducion,
                                    pregunta = str(dato[x][2]),
                                    numero = dato[x][3],
                                    puntos = dato[x][4],
                                    fecha = datetime.now(),
                                    activo = dato[x][6],
                                    usuario_id = dato[x][7])
                            preguntaexamen.save()
                            db.close()
                            db = psycopg2.connect("host=10.10.9.45 dbname=demoitb2 user=postgres password=Itb$2019 port=5432 ")
                            # db = psycopg2.connect("host=localhost dbname=demo_18mayo user=postgres password=aok port=5433 ")
                            cursor = db.cursor()
                            cursor.execute("select r.id as id, r.preguntaexamen_id,r.respuesta, r.valida, r.fecha,r.usuario_id "
                                           "from sga_respuestaexamen as r where r.preguntaexamen_id ="+str(dato[x][0])+" order by id")
                            dato1 = cursor.fetchall()
                            if len(dato1) > 0:
                                for i in range(len(dato1)):
                                    print(dato1[i][0])
                                    print(dato1[i][1])
                                    print(dato1[i][2])
                                    print(dato1[i][3])
                                    print(dato1[i][4])
                                    print(dato1[i][5])
                                    respuestaexamen = RespuestaExamen(
                                                    preguntaexamen = preguntaexamen,
                                                    respuesta = str(dato1[i][2]),
                                                    valida = dato1[i][3],
                                                    fecha = datetime.now(),
                                                    usuario_id = dato1[i][5])

                                    respuestaexamen.save()
                        client_address = ip_client_address(request)
                        #Log de ADICIONAR EXAMEN DESDE DEMO
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(tituloexamenconducion).pk,
                            object_id       = tituloexamenconducion.id,
                            object_repr     = force_str(tituloexamenconducion),
                            action_flag     = ADDITION,
                            change_message  = 'Importar examen desde DEMO (' + client_address + ')')
                        return HttpResponseRedirect("/admin_examencondu?info=IMPORTACION TERMINADA")

            elif action =='consultaasignatura':
                data = {}
                try:
                    carrera = Carrera.objects.filter(pk=request.POST['idcarrera'])[:1].get()
                    data ={"asignaturas":[{'id': a.asignatura.id,'asignatura': elimina_tildes(a.asignatura)} for a in  AsignaturaMalla.objects.filter(malla__carrera=carrera).distinct('asignatura__nombre').order_by('asignatura__nombre')]}
                    data['result'] = 'ok'
                    return HttpResponse(json.dumps(data), content_type="application/json")
                except Exception as e:
                    data['result'] = 'bad'
                    return HttpResponse(json.dumps(data), content_type="application/json")

            return HttpResponseRedirect('/admin_examencondu')
        else:
            data={"title":"Administrador Examen"}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']
                if action == "examen":
                    data['title'] = 'Ver Examen'
                    tituloexamencondu = TituloExamenCondu.objects.filter(id=request.GET['id'])[:1].get()

                    data['DEFAULT_PASSWORD'] = DEFAULT_PASSWORD
                    if not tituloexamencondu.activo:
                        data['tituloexamencondu'] = tituloexamencondu
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
                        return render(request ,"examenconducion/formularioexamen.html" ,  data)
                    return HttpResponseRedirect('/admin_examencondu?info=Desactivar examen para editar preguntas')


                elif action == 'activa':
                   tituloexamencondu =  TituloExamenCondu.objects.filter(id=request.GET['id'])[:1].get()

                   if tituloexamencondu.activo:
                      if InscripcionExamen.objects.filter(tituloexamencondu=tituloexamencondu,valida=True,finalizado=True).count() != InscripcionExamen.objects.filter(tituloexamencondu = tituloexamencondu,valida=True).count():
                          return HttpResponseRedirect('/admin_examencondu?info=Faltan examenes por finalizar')
                      activo = False
                      mensaje = 'Desactivacion de Examen'
                   else:
                       activo = True
                       mensaje = 'Activacion de Examen'
                   tituloexamencondu.activo = activo
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
                   return HttpResponseRedirect('/admin_examencondu')

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
                   #Log de ADICIONAR INSCRIPCION
                   LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(tituloexamencondu).pk,
                        object_id       = tituloexamencondu.id,
                        object_repr     = force_str(tituloexamencondu),
                        action_flag     = ADDITION,
                        change_message  = 'Eliminacion de pregunta de examen  (' + client_address + ')')
                   return HttpResponseRedirect('/admin_examencondu?action=examen&id='+str(tituloexamencondu.id)+s)

                elif action == "eliminaresp":
                    respuestaexamen = RespuestaExamen.objects.filter(id=request.GET['id'])[:1].get()
                    idpregunt = respuestaexamen.preguntaexamen.tituloexamencondu.id
                    if respuestaexamen.imagen:
                        if (MEDIA_ROOT + '/' + str(respuestaexamen.imagen)):
                            os.remove(MEDIA_ROOT + '/' + str(respuestaexamen.imagen))
                    respuestaexamen.delete()
                    return HttpResponseRedirect('/admin_examencondu?action=examen&id='+str(idpregunt))
                elif action == "eliminarpreg":
                    tituloexamencondu = TituloExamenCondu.objects.filter(id=request.GET['id'])[:1].get()
                    tituloexamencondu.delete()
                    return HttpResponseRedirect('/admin_examencondu')
                # elif action == "clonaexamen":
                #     tituloexamencondu = TituloExamenCondu.objects.filter(id=19)[:1].get()
                #     tituloexamenconduclon = TituloExamenCondu.objects.filter(id=20)[:1].get()
                #     for p in PreguntaExamen.objects.filter(tituloexamencondu=tituloexamencondu):
                #         preguntaexamen = PreguntaExamen(
                #                     tituloexamencondu = tituloexamenconduclon,
                #                     pregunta = p.pregunta,
                #                     numero = p.numero,
                #                     puntos = p.puntos,
                #                     fecha = datetime.now(),
                #                     activo = p.activo,
                #                     usuario = p.usuario)
                #         preguntaexamen.save()
                #         if p.imagen:
                #             preguntaexamen.imagen = p.imagen
                #             preguntaexamen.save()
                #
                #
                #         for r in RespuestaExamen.objects.filter(preguntaexamen=p):
                #             respuestaexamen = RespuestaExamen(
                #                                     preguntaexamen = preguntaexamen,
                #                                     respuesta = r.respuesta,
                #                                     valida = r.valida,
                #                                     fecha = datetime.now(),
                #                                     usuario = r.usuario)
                #             respuestaexamen.save()
                #
                #             if r.imagen:
                #                 respuestaexamen.imagen = r.imagen
                #                 respuestaexamen.save()
                #     return HttpResponseRedirect('/admin_examencondu')
            else:
                search = None
                if 's' in request.GET:
                    search = request.GET['s']
                if search:
                    tituloexamencondu = TituloExamenCondu.objects.filter(tituloexamen__icontains=search,teleclinica=False).order_by('-fecha')
                else:
                    tituloexamencondu = TituloExamenCondu.objects.filter(teleclinica=False).order_by('-id')

                data['tituloexamencondu'] = tituloexamencondu
                data['NOMBRE_INSTITUCION_EXAMEN'] = NOMBRE_INSTITUCION_EXAMEN
                data['asignatura'] = Asignatura.objects.filter(id__in=ASIGNATURA_EXAMEN_GRADO_CONDU)
                data['asignatura2'] = Asignatura.objects.filter().exclude(id__in=ASIGNATURA_EXAMEN_GRADO_CONDU)
                data['carreras'] = Carrera.objects.filter(activo=True,carrera=True,vigente=True).exclude(id__in=[63,66])
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

                return render(request ,"examenconducion/admin_examencondu.html" ,  data)
    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))


