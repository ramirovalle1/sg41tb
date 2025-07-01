from datetime import datetime
import json
from django.contrib.admin.models import LogEntry, ADDITION, DELETION, CHANGE
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
from sga.commonviews import addUserData, ip_client_address
from sga.forms import SesionForm, SesionJornadaForm, JornadaForm, TurnoForm
from sga.models import Jornada, SesionJornada, Sesion, Turno, Materia, Clase, ReferidosInscripcion, Inscripcion, Nivel


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
# @secure_module
@transaction.atomic()

def view(request):
    if request.method=='POST':
        action = request.POST['action']
        if action == 'add_jornada':
            print(request.POST)
            try:
                if request.POST['idjornada']=='':
                    id_jornada=0
                else:
                    id_jornada=request.POST['idjornada']
                if Jornada.objects.filter(pk=id_jornada).exists():
                    edit = Jornada.objects.get(pk=id_jornada)
                    edit.nombre=request.POST['nombre']
                    mensaje = 'Edicion de jornada'
                    edit.save()
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(edit).pk,
                    object_id       = edit.id,
                    object_repr     = force_str(edit),
                    action_flag     = CHANGE,
                    change_message  = mensaje+' (' + client_address + ')' )
                else:
                    if Jornada.objects.filter(nombre=request.POST['nombre']).exists():
                        return HttpResponseRedirect('/jornada?error=Ya existe una jor6nada con ese nombre')
                    else:
                        add = Jornada(nombre=request.POST['nombre'])
                        mensaje = 'Ingreso de nueva jornada'
                        add.save()
                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(add).pk,
                        object_id       = add.id,
                        object_repr     = force_str(add),
                        action_flag     = ADDITION,
                        change_message  = mensaje+' (' + client_address + ')' )
                return HttpResponseRedirect('/jornada')
            except Exception as ex:
                return HttpResponseRedirect('/jornada?error=Error al ingresar jornada, vuelva a intentarlo')

        elif action == 'eliminar_jornada':
            result = {}
            try:
                if SesionJornada.objects.filter(jornada__id=request.POST['id_jornada']).exists():
                    result['result']  = "No se puede eliminar esta jornada, contiene sesiones"
                    return HttpResponse(json.dumps(result), content_type="application/json")
                else:
                    eliminar =Jornada.objects.filter(pk=request.POST['id_jornada'])[:1].get()
                    mensaje = 'Eliminar jornada'
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(eliminar).pk,
                        object_id       = eliminar.id,
                        object_repr     = force_str(eliminar),
                        action_flag     = DELETION,
                        change_message  = mensaje+' (' + client_address + ')' )
                    eliminar.delete()
                    result['result']  = "ok"
                    return HttpResponse(json.dumps(result), content_type="application/json")
            except Exception as e:
                result['result']  = str(e)
                return HttpResponse(json.dumps(result), content_type="application/json")

        elif action == 'add_sesionjornada':
            try:
                sesion = Sesion.objects.get(pk=request.POST['sesion'])
                jornada = Jornada.objects.get(pk=request.POST['idjornada'])
                if SesionJornada.objects.filter(sesion=sesion).exists():
                    return HttpResponseRedirect('/jornada?error=Registro ya existe')
                else:
                    guardar = SesionJornada(sesion=sesion, jornada=jornada)
                    guardar.save()
                    mensaje = 'Ingresar sesion a jornada'
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(guardar).pk,
                    object_id       = guardar.id,
                    object_repr     = force_str(guardar),
                    action_flag     = ADDITION,
                    change_message  = mensaje+' (' + client_address + ')' )
                    return HttpResponseRedirect('/jornada')
            except Exception as ex:
                return HttpResponseRedirect('/jornada?error=Error al ingresar sesion, vuelva a intentarlo')

        elif action == 'add_sesion':
            try:
                print(request.POST)
                nombre=request.POST['sesion']
                comienza = datetime.strptime (request.POST['comienza'] , '%H:%M:%S').time()
                termina = datetime.strptime (request.POST['termina'] , '%H:%M:%S').time()

                if 'idjornada' in request.POST:
                    j=request.POST['idjornada']
                else:
                    pass
                if 'lunes' in request.POST:
                    lunes = True
                else:
                    lunes=False
                if 'martes' in request.POST:
                    martes = True
                else:
                    martes=False
                if 'miercoles' in request.POST:
                    miercoles = True
                else:
                    miercoles=False
                if 'jueves' in request.POST:
                    jueves = True
                else:
                    jueves=False
                if 'viernes' in request.POST:
                    viernes = True
                else:
                    viernes=False
                if 'sabado' in request.POST:
                    sabado = True
                else:
                    sabado=False
                if 'domingo' in request.POST:
                    domingo = True
                else:
                    domingo=False
                if 'estado' in request.POST:
                    estado = True
                else:
                    estado = False
                if request.POST['idsesion']=='':
                    sesion_id=0
                else:
                    sesion_id=request.POST['idsesion']
                if Sesion.objects.filter(pk=sesion_id).exists():
                    sesion = Sesion.objects.get(pk=sesion_id)
                    sesion.nombre = nombre
                    sesion.comienza = comienza
                    sesion.termina = termina
                    sesion.lunes = lunes
                    sesion.martes = martes
                    sesion.miercoles = miercoles
                    sesion.jueves = jueves
                    sesion.viernes = viernes
                    sesion.sabado = sabado
                    sesion.domingo = domingo
                    sesion.estado = estado
                    sesion.save()
                    mensaje = 'Modificar sesion'
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(sesion).pk,
                    object_id       = sesion.id,
                    object_repr     = force_str(sesion),
                    action_flag     = CHANGE,
                    change_message  = mensaje+' (' + client_address + ')' )
                    return HttpResponseRedirect('/jornada?action=ver_sesiones&id='+request.GET['id'])
                else:
                    sesion = Sesion(nombre=nombre, comienza=comienza, termina=termina, lunes=lunes, martes=martes, miercoles=miercoles, jueves=jueves, viernes=viernes, sabado=sabado, domingo=domingo, estado=estado)
                    sesion.save()
                    mensaje = 'Ingresar sesion'
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(sesion).pk,
                    object_id       = sesion.id,
                    object_repr     = force_str(sesion),
                    action_flag     = ADDITION,
                    change_message  = mensaje+' (' + client_address + ')' )
                    if 'idjornada' in request.POST:
                        jornada = Jornada.objects.get(pk=request.POST['idjornada'])
                        guardar_sesionjornada = SesionJornada(jornada=jornada, sesion=sesion)
                        guardar_sesionjornada.save()
                        return HttpResponseRedirect('/jornada?action=ver_sesiones&id='+request.GET['id'])
                    else:
                        return HttpResponseRedirect('/jornada?action=ver_pendientes')
            except Exception as ex:
                print(ex)
                return HttpResponseRedirect('/jornada?action=ver_sesiones&id='+request.GET['id']+'&error=Error al ingresar sesion, vuelva a intentarlo')

        elif action == 'eliminar_sesionjornada':
            print(request.POST)
            result = {}
            try:
                if SesionJornada.objects.filter(sesion__id=request.POST['id_sesion']).exists():
                    eliminar =SesionJornada.objects.filter(sesion__id=request.POST['id_sesion'])[:1].get()
                    result['result']  = "Registro eliminadio de esta jornada"
                    mensaje = 'Quitar sesion de jornada'
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(eliminar).pk,
                        object_id       = eliminar.id,
                        object_repr     = force_str(eliminar),
                        action_flag     = DELETION,
                        change_message  = mensaje+' (' + client_address + ')' )
                    eliminar.delete()
                else:
                    sesion = Sesion.objects.filter(pk=request.POST['id_sesion'])
                    if Nivel.objects.filter(sesion=sesion).exists() or Turno.objects.filter(sesion__id=request.POST['id_sesion']).exists():
                        result['result']  = "No se puede eliminar esta sesion"
                    else:
                        eliminar = Sesion.objects.filter(pk=request.POST['id_sesion'])[:1].get()
                        result['result']  = "ok"
                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(eliminar).pk,
                            object_id       = eliminar.id,
                            object_repr     = force_str(eliminar),
                            action_flag     = ADDITION,
                            change_message  = 'Eliminada sesion (' + client_address + ')')
                        eliminar.delete()
                return HttpResponse(json.dumps(result), content_type="application/json")
            except Exception as e:
                result['result']  = str(e)
                return HttpResponse(json.dumps(result), content_type="application/json")

        if action == 'add_turno':
            print(request.POST)
            practica=False
            try:
                idjornada = request.POST['idjornada']
                idsesion = request.POST['idsesion']
                sesion = Sesion.objects.get(pk=request.POST['idsesion'])
                comienza = datetime.strptime (request.POST['comienza'] , '%H:%M:%S').time()
                termina = datetime.strptime (request.POST['termina'] , '%H:%M:%S').time()

                if request.POST['idturno']=='':
                    turno_id=0
                else:
                    turno_id=request.POST['idturno']
                if Turno.objects.filter(pk=turno_id).exists():
                    modifica = Turno.objects.get(pk=request.POST['idturno'])
                    modifica.turno = request.POST['turno']
                    modifica.comienza = comienza
                    modifica.termina = termina
                    modifica.horas = request.POST['horas']
                    if request.POST['practica']:
                        modifica.practica = request.POST['practica']

                    modifica.save()
                    mensaje = 'Modifica turno'
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(modifica).pk,
                        object_id       = modifica.id,
                        object_repr     = force_str(modifica),
                        action_flag     = CHANGE,
                        change_message  = mensaje+' (' + client_address + ')' )
                    return HttpResponseRedirect('/jornada?action=ver_turnos&id='+idsesion+'&jornada='+idjornada)
                else:
                    if 'practica' in request.POST:
                        if request.POST['practica'] =='on':
                            practica = True

                    if practica:
                        guardar = Turno(sesion=sesion, turno=request.POST['turno'], comienza=comienza, termina=termina, horas=request.POST['horas'],practica=practica)
                    else:
                        guardar = Turno(sesion=sesion, turno=request.POST['turno'], comienza=comienza, termina=termina, horas=request.POST['horas'])
                    guardar.save()
                    mensaje = 'Ingresa turno'
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(guardar).pk,
                        object_id       = guardar.id,
                        object_repr     = force_str(guardar),
                        action_flag     = CHANGE,
                        change_message  = mensaje+' (' + client_address + ')' )
                    return HttpResponseRedirect('/jornada?action=ver_turnos&id='+idsesion+'&jornada='+idjornada)
            except Exception as ex:
                print(ex)
                return HttpResponseRedirect('/jornada?action=ver_turnos&id='+idsesion+'&jornada='+idjornada+'&error=Ocurrio un error, vuelva a intentarlo')

        elif action == 'eliminar_turno':
            print(request.POST)
            result = {}
            try:
                turno = Turno.objects.filter(pk=request.POST['idturno'])
                if Clase.objects.filter(turno=turno).exists():
                    # clase = Clase.objects.filter(turno=turno).values('materia')
                    # materia = Materia.objects.filter(Q(cerrado=False)|Q(id__in=clase))
                    # if materia.exists():
                    result['result']  = "No se puede eliminar este turno"
                else:
                    eliminar =Turno.objects.filter(pk=request.POST['idturno'])[:1].get()
                    mensaje = 'Elimina turno'
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(eliminar).pk,
                        object_id       = eliminar.id,
                        object_repr     = force_str(eliminar),
                        action_flag     = CHANGE,
                        change_message  = mensaje+' (' + client_address + ')' )
                    eliminar.delete()
                    result['result']  = "ok"

                return HttpResponse(json.dumps(result), content_type="application/json")
            except Exception as e:
                result['result']  = str(e)
                return HttpResponse(json.dumps(result), content_type="application/json")
    else:
        data = {'title': 'Listado de Jornadas'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action == 'ver_sesiones':
                try:
                    data['title'] = 'Listado de Sesiones'
                    jornada = Jornada.objects.get(pk=request.GET['id'])
                    hoy = str(datetime.date(datetime.now()))
                    search = None
                    if 's' in request.GET:
                        search = request.GET['s']
                    if search:
                        ss = search.split(' ')
                        while '' in ss:
                            ss.remove('')
                        if len(ss)==1:
                            sesion = SesionJornada.objects.filter(sesion__nombre__icontains=search).order_by('sesion__comienza','sesion__termina','sesion__nombre')
                        else:
                            sesion = SesionJornada.objects.filter(sesion__nombre__icontains=ss).order_by('sesion__comienza','sesion__termina','sesion__nombre')
                    else:
                        sesion = SesionJornada.objects.filter(jornada=jornada).order_by('sesion__comienza','sesion__termina','sesion__nombre')
                    paging = Paginator(sesion, 20)
                    p = 1
                    try:
                        if 'page' in request.GET:
                            p = int(request.GET['page'])
                        page = paging.page(p)
                    except:
                        page = paging.page(1)
                    data['paging'] = paging
                    data['page'] = page
                    data['search'] = search if search else ""
                    data['sesionjornada'] = page.object_list
                    data['form'] = SesionForm
                    data['jornada'] = jornada
                    if 'error' in request.GET:
                        data['error'] = request.GET['error']
                    return render(request ,"jornada/select_jornada.html" ,  data)
                except Exception as ex:
                    print(ex)
            if action == 'ver_turnos':
                try:
                    data['title'] = 'Listado de Turnos'
                    sesion = Sesion.objects.get(pk=request.GET['id'])
                    turno = Turno.objects.filter(sesion=sesion).order_by('turno','comienza','termina','horas')
                    paging = Paginator(turno, 20)
                    p = 1
                    try:
                        if 'page' in request.GET:
                            p = int(request.GET['page'])
                        page = paging.page(p)
                    except:
                        page = paging.page(1)

                    data['paging'] = paging
                    data['page'] = page
                    data['turnos'] = page.object_list
                    data['form'] = TurnoForm
                    data['sesion'] = sesion
                    if 'jornada' in request.GET:
                        data['jornada'] = Jornada.objects.get(pk=request.GET['jornada'])
                    if 'error' in request.GET:
                        data['error'] = request.GET['error']
                    return render(request ,"jornada/turnosbs.html" ,  data)
                except Exception as ex:
                    print(ex)
                    return HttpResponseRedirect("/jornada?action=ver_sesiones&id="+request.GET['jornada'])
            if action == 'ver_pendientes':
                try:
                    data['title'] = 'Sesiones pendientes'
                    sesionjornada=SesionJornada.objects.filter().values('sesion')
                    search = None
                    if 's' in request.GET:
                        search = request.GET['s']
                    if search:
                        ss = search.split(' ')
                        while '' in ss:
                            ss.remove('')
                        if len(ss)==1:
                            sesion = Sesion.objects.filter(nombre__icontains=search).exclude(id__in=sesionjornada).order_by('comienza','termina','nombre')
                        else:
                            sesion = Sesion.objects.filter(nombre__icontains=ss).exclude(id__in=sesionjornada).order_by('comienza','termina','nombre')
                    else:
                        sesion=Sesion.objects.filter().exclude(id__in=sesionjornada).order_by('comienza','termina','nombre')
                    jornada = Jornada.objects.filter().order_by('id')
                    data['jornadas'] = jornada
                    data['pendientes'] = sesion
                    data['search'] = search if search else ""
                    data['form'] = SesionForm
                    if 'error' in request.GET:
                        data['error'] = request.GET['error']
                    return render(request ,"jornada/sesiones_pendientes.html" ,  data)
                except Exception as ex:
                    print(ex)
                    return HttpResponseRedirect("/jornada")
        else:
            try:
                hoy = str(datetime.date(datetime.now()))
                search = None
                if 's' in request.GET:
                    search = request.GET['s']
                if search:
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')
                    if len(ss)==1:
                        jornada = Jornada.objects.filter(nombre__icontains=search)
                    else:
                        jornada = Jornada.objects.filter(nombre__icontains=ss)
                else:
                    jornada = Jornada.objects.filter().order_by('id')

                sesionsi=SesionJornada.objects.filter().values('sesion')
                sesionoi=Sesion.objects.filter().exclude(id__in=sesionsi)
                totsesionoi=Sesion.objects.filter().exclude(id__in=sesionsi).count()

                data['pendiente_count'] = totsesionoi
                data['search'] = search if search else ""
                data['jornadas'] = jornada
                data['fechaactual']=datetime.now().date()
                data['form'] = SesionJornadaForm
                data['form_jornada'] = JornadaForm
                if 'error' in request.GET:
                    data['error'] = request.GET['error']
                return render(request ,"jornada/jornada.html" ,  data)
            except Exception as e:
                return HttpResponseRedirect("/jornada")
