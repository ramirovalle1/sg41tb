from datetime import datetime
import json
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Q
from django.db import transaction
from django.forms.models import model_to_dict
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
from sga.commonviews import addUserData, ip_client_address
from sga.forms import NotificacionForm, NotificacionPersonaForm
from sga.models import Notificacion, NotificacionPersona, Persona


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
#@secure_module
@transaction.atomic()

def view(request):
    if request.method=='POST':
        action = request.POST['action']
        if action == 'eliminar': #Eliminar Notificaciones
            result = {}
            try:
                if NotificacionPersona.objects.filter(notificacion__id=request.POST['idnotificacion']).exists():
                    result['result']= "No se puede eliminar esta notificacion"
                else:
                    eliminar = Notificacion.objects.filter(pk=request.POST['idnotificacion'])[:1].get()
                    msj = 'Eliminado Notificacion'
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(eliminar).pk,
                        object_id       = eliminar.id,
                        object_repr     = force_str(eliminar),
                        action_flag     = DELETION,
                        change_message  = msj+' (' + client_address + ')')
                    eliminar.delete()
                    result['result']  = "ok"
                return HttpResponse(json.dumps(result), content_type="application/json")
            except Exception as e:
                result['result']  = str(e)
                return HttpResponse(json.dumps(result), content_type="application/json")

        elif action == 'add':
            try:
                if 'estado' in request.POST:
                    estado=True
                else:
                    estado=False

                nombre=request.POST['nombre']
                funcion= request.POST['funcion']
                descripcion= request.POST['descripcion']
                query= request.POST['query']
                add = Notificacion(nombre=nombre, funcion=funcion, estado=estado, descripcion=descripcion, query=query)
                add.save()

                mensaje = 'Ingreso de nueva notificacion'
                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                user_id         = request.user.pk,
                content_type_id = ContentType.objects.get_for_model(add).pk,
                object_id       = add.id,
                object_repr     = force_str(add),
                action_flag     = ADDITION,
                change_message  = mensaje+' (' + client_address + ')')

                return HttpResponseRedirect("/notificaciones_mant")

            except Exception as ex:
                return HttpResponseRedirect("/notificaciones_mant?error=Error al ingresar notificacion, vuelva a intentarlo")

        elif action == 'editar':
            try:
                id_notificacion = request.POST['idnotificacion']

                if 'estado' in request.POST:
                    estado = True
                else:
                    estado = False

                edit = Notificacion.objects.get(pk=id_notificacion)
                edit.nombre = request.POST['nombre']
                edit.descripcion = request.POST['descripcion']
                edit.query = request.POST['query']
                edit.funcion = request.POST['funcion']
                edit.estado = estado
                mensaje = 'Edicion de notificacion'
                edit.save()
                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                user_id         = request.user.pk,
                content_type_id = ContentType.objects.get_for_model(edit).pk,
                object_id       = edit.id,
                object_repr     = force_str(edit),
                action_flag     = CHANGE,
                change_message  = mensaje+' (' + client_address + ')' )

                return HttpResponseRedirect("/notificaciones_mant")

            except Exception as ex:
                return HttpResponseRedirect("/notificaciones_mant?error=Error al editar notificacion, vuelva a intentarlo")

        elif action == 'add_persona':
            data = {}
            try:
                notificacion = Notificacion.objects.get(pk=request.POST["idnotificacion"])
                persona = Persona.objects.get(pk = request.POST['idpersona'])
                if NotificacionPersona.objects.filter(persona=persona, notificacion=notificacion).exists():
                     data['result']= "Esta persona ya tiene asignada esta notificacion"
                else:
                    registro = NotificacionPersona(notificacion=notificacion,persona=persona)
                    registro.save()
                    data["result"] = "ok"

                    mensaje = 'Ingreso de nueva persona'
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(registro).pk,
                    object_id       = registro.id,
                    object_repr     = force_str(registro),
                    action_flag     = ADDITION,
                    change_message  = mensaje+' (' + client_address + ')' )
                return HttpResponse(json.dumps(data),content_type="application/json")

            except Exception as ex:
                data["result"]="Error al ingresar la persona"
                return HttpResponse(json.dumps(data),content_type="application/json")

        elif action=='add_personas':
            try:
                data = {}
                notificacion = Notificacion.objects.get(pk=request.POST["idnotificacion"])
                grupo= Group.objects.get(pk=request.POST['idGrupo'])
                personas = Persona.objects.filter(usuario__groups=grupo, usuario__is_active= True)
                for p in personas:
                    if not NotificacionPersona.objects.filter(notificacion=notificacion, persona=p).exists():
                        registro = NotificacionPersona(notificacion=notificacion,persona=p)
                        registro.save()

                mensaje = 'Grupo agregado'
                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                user_id         = request.user.pk,
                content_type_id = ContentType.objects.get_for_model(notificacion).pk,
                object_id       = notificacion.id,
                object_repr     = force_str(notificacion),
                action_flag     = CHANGE,
                change_message  = mensaje+' (' + client_address + ')' )

                data["result"] = "ok"
                return HttpResponse(json.dumps(data),content_type="application/json")

            except Exception as ex:
                print(ex)
                return HttpResponse(json.dumps({"result": "bad", "mensaje":"Error al agregar grupo: "+str(ex)}),content_type="application/json")

        elif action =='eliminar_persgrupo':
            try:
                data = {}
                eliminar = NotificacionPersona.objects.filter(pk=request.POST['idnotificacion'])[:1].get()

                msj = 'Eliminado persona del grupo de notificaciones'
                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(eliminar).pk,
                    object_id       = eliminar.id,
                    object_repr     = force_str(eliminar),
                    action_flag     = DELETION,
                    change_message  = msj+' (' + client_address + ')' )
                eliminar.delete()
                data["result"] = "ok"
                return HttpResponse(json.dumps(data),content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({"result": "bad", "mensaje":"Error al eliminar persona: "+str(e)}),content_type="application/json")

        elif action == 'cargar_grupos':
            try:
                notificacion = Notificacion.objects.get(pk=request.POST['id'])
                data = []
                if notificacion.obtener_grupos():
                    data = [{'id':x.id, 'name':x.name} for x in notificacion.obtener_grupos()]
                return HttpResponse(json.dumps({'result':'ok', 'grupos':data}),content_type="application/json")
            except Exception as e:
                print(e)

        elif action == 'cargar_combo_grupos':
            notificacion = Notificacion.objects.get(pk=request.POST['id'])
            grupos = Group.objects.filter()
            if notificacion.obtener_grupos():
                grupos = grupos.exclude(id__in=notificacion.obtener_grupos()).order_by('name')
            data = [{'id':x.id, 'name':x.name} for x in grupos]
            return HttpResponse(json.dumps({'result':'ok', 'grupos':data}),content_type="application/json")

        elif action == 'add_grupo':
            try:
                grupo = Group.objects.get(pk=request.POST['grupo'])
                notificacion = Notificacion.objects.get(pk=request.POST['id'])
                notificacion.grupos = notificacion.grupos+","+str(grupo.id) if notificacion.grupos else str(grupo.id)
                notificacion.save()
                return HttpResponse(json.dumps({'result':'ok'}),content_type="application/json")
            except Exception as e:
                print(e)

        elif action == 'delete_grupo':
            try:
                grupo = Group.objects.get(pk=request.POST['grupo'])
                notificacion = Notificacion.objects.get(pk=request.POST['id'])
                lista_grupos =  notificacion.grupos.split(',')
                if str(grupo.id) in lista_grupos:
                    lista_grupos.remove(str(grupo.id))
                notificacion.grupos = ','.join(lista_grupos)
                notificacion.save()
                return HttpResponse(json.dumps({'result':'ok'}),content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({'result':'ok', 'mensaje':str(e)}),content_type="application/json")

        elif action == 'cambiar_estado_persona':
            notificacion_persona = NotificacionPersona.objects.get(pk=request.POST['id'])
            notificacion_persona.estado = not notificacion_persona.estado
            notificacion_persona.save()
            mensaje = "Notificacion se encuentra activa" if notificacion_persona.estado else "Notificacion se encuentra inactiva"
            return HttpResponse(json.dumps({'result':'ok', 'mensaje':mensaje}),content_type="application/json")

    else:
        data = {'title': 'Listado de Notificaciones'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action == 'ver_grupo':
                try:
                    data['title'] = 'Listado de Notificaciones'
                    notificacion = Notificacion.objects.get(pk=request.GET['id'])
                    search = None
                    if 's' in request.GET:
                        search = request.GET['s']
                    if search:
                        ss = search.split(' ')
                        while '' in ss:
                            ss.remove('')
                        if len(ss)==1:
                            notificaciones = NotificacionPersona.objects.filter(Q(persona__nombres__icontains=search)|Q(persona__apellido1__icontains=search) |Q(persona__apellido2__icontains=search),notificacion=notificacion).order_by('persona__apellido1')
                        else:
                            notificaciones = NotificacionPersona.objects.filter(Q(persona__apellido1__icontains=ss[0]) & Q(persona__apellido2__icontains=ss[1]), notificacion= notificacion).order_by('persona__apellido1')
                    else:
                        notificaciones = NotificacionPersona.objects.filter(notificacion=notificacion).order_by('persona__apellido1')

                    paging = MiPaginador(notificaciones, 20)
                    p = 1
                    try:
                        if 'page' in request.GET:
                            p = int(request.GET['page'])
                        page = paging.page(p)
                    except:
                        page = paging.page(1)
                    data['paging'] = paging
                    data['page'] = page
                    data['rangospaging'] = paging.rangos_paginado(p)
                    data['search'] = search if search else ""
                    data['notificaciones'] = page.object_list
                    data['form'] = NotificacionPersonaForm
                    data['notificacion'] = notificacion
                    if 'error' in request.GET:
                        data['error'] = request.GET['error']
                    data['grupos']= Group.objects.filter(id__in=notificacion.obtener_grupos()).order_by('name')
                    return render(request ,"notificaciones/notificacionpersona.html" ,  data)
                except Exception as ex:
                    print(ex)
        else:
            try:
                search = None
                if 's' in request.GET:
                    search = request.GET['s']

                if search:
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')
                    if len(ss)==1:
                        notificaciones = Notificacion.objects.filter(Q(nombre__icontains=search)|Q(funcion__icontains = search)).order_by('nombre')
                    else:
                        notificaciones = Notificacion.objects.filter(nombre__icontains=ss).order_by('nombre')
                else:
                    notificaciones = Notificacion.objects.all().order_by('-estado', 'nombre')

                paging = MiPaginador(notificaciones, 30)
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
                data['form'] = NotificacionPersonaForm
                data['form_notificacion'] = NotificacionForm
                data['notificaciones'] = page.object_list
                if 'error' in request.GET:
                    data['error']= request.GET['error']
                return render(request ,"notificaciones/notificaciones.html" ,  data)

            except Exception as e:
                return HttpResponseRedirect("/")