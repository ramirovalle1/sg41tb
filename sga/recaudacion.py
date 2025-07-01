import datetime
from django.contrib.admin.models import LogEntry, CHANGE, DELETION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
import json
from django.db.models import Q
from django.forms import model_to_dict
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.utils.encoding import force_str
from decorators import secure_module
from sga.forms import LugarRecaudacionForm, IpRecaudacionForm
from sga.models import LugarRecaudacion, SesionCaja, IpRecaudLugar
from sga.commonviews import addUserData, ip_client_address


@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    if request.method=='POST':
        if 'action' in request.POST:
            action = request.POST['action']
            if action == 'buscar':
                punto = request.POST['punto']
                puntos = ''
                if LugarRecaudacion.objects.filter(puntoventa = punto,activa=True ).exists():
                    for p in LugarRecaudacion.objects.filter(puntoventa = punto ,activa=True):
                        puntos = puntos + ' - ' +p.nombre
                    fac =str( p.numerofact)
                    cre = str(p.numeronotacre)
                    dir = str(p.direccion)

                    return HttpResponse(json.dumps({'result':'ok', "puntos": str(puntos),'ncre':cre,'fac':fac,'dir':dir}),content_type="application/json")
                else:
                    return HttpResponse(json.dumps({'result':'bad'}),content_type="application/json")

            if action == 'buscarpersona':
                persona = request.POST['persona']
                puntos = ''
                if LugarRecaudacion.objects.filter(persona__id = persona,activa=True ).exists():
                    for p in LugarRecaudacion.objects.filter(persona__id = persona ,activa=True):
                        puntos = puntos + ' - ' +p.nombre

                    return HttpResponse(json.dumps({'result':'ok', "puntos": str(puntos)}),content_type="application/json")
                else:
                    return HttpResponse(json.dumps({'result':'bad'}),content_type="application/json")

            elif action == 'add':
                    f = LugarRecaudacionForm(request.POST)
                    if f.is_valid():
                        try:
                            if request.POST['ban'] == '1':
                                lugar = LugarRecaudacion(nombre=f.cleaned_data['nombre'],
                                                         persona_id=f.cleaned_data['persona'],
                                                         puntoventa = f.cleaned_data['puntoventa'],
                                                         numerofact = f.cleaned_data['numerofact'],
                                                         direccion = f.cleaned_data['direccion'],
                                                         nuevomodeloreporte = f.cleaned_data['nuevomodeloreporte'],
                                                         numeronotacre = f.cleaned_data['numeronotacre'])
                                lugar.save()
                                mensaje = 'Adicionado'

                            else:
                                lugar = LugarRecaudacion.objects.get(pk=int(request.POST['lugar']))
                                lugar.nombre=f.cleaned_data['nombre']
                                lugar.persona_id=f.cleaned_data['persona']
                                lugar.puntoventa = f.cleaned_data['puntoventa']
                                lugar.numerofact = f.cleaned_data['numerofact']
                                lugar.direccion = f.cleaned_data['direccion']
                                lugar.numeronotacre = f.cleaned_data['numeronotacre']
                                lugar.nuevomodeloreporte = f.cleaned_data['nuevomodeloreporte']
                                lugar.save()
                                mensaje = 'Editado'
                        # Log Editar Inscripcion
                            client_address = ip_client_address(request)
                            LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(lugar).pk,
                                object_id       = lugar.id,
                                object_repr     = force_str(lugar),
                                action_flag     = CHANGE,
                                change_message  = mensaje + " Lugar de Recaudacion " +  '(' + client_address + ')' )

                            return HttpResponseRedirect("/recaudacion")
                        except Exception as ex:
                            return HttpResponseRedirect("recaudacion?add&error=1",)
                    else:
                       return HttpResponseRedirect("recaudacion?add&error=1",)

            elif action == 'existip':
                if request.POST['idlugarrec'] and request.POST['ip'] and int(request.POST['edit']) == 0:
                    if IpRecaudLugar.objects.filter(lugarrecaudacion__id = request.POST['idlugarrec'],ip__id = request.POST['ip']).exists():
                        return HttpResponse(json.dumps({'result':'bad'}),content_type="application/json")
                return HttpResponse(json.dumps({'result':'ok'}),content_type="application/json")
            elif action == 'addip':
                try:
                    if request.POST['idlugarrec'] and request.POST['ip'] or int(request.POST['edit']) != 0:
                        if int(request.POST['edit']) != 0:
                            iprecaudlugar = IpRecaudLugar.objects.filter(id=request.POST['edit'])[:1].get()
                            iprecaudlugar.ip_id = request.POST['ip']
                            iprecaudlugar.fecha = datetime.datetime.now()
                            iprecaudlugar.usuario = request.user
                            mensaje = "Edicion"
                        else:
                            iprecaudlugar = IpRecaudLugar(
                                                    lugarrecaudacion_id = request.POST['idlugarrec'],
                                                    ip_id = request.POST['ip'],
                                                    fecha = datetime.datetime.now(),
                                                    usuario = request.user)
                            mensaje = "Ingreso"
                        iprecaudlugar.save()
                        # Log Editar Inscripcion
                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(iprecaudlugar).pk,
                            object_id       = iprecaudlugar.id,
                            object_repr     = force_str(iprecaudlugar),
                            action_flag     = CHANGE,
                            change_message  = mensaje+" de Ip para Recaudacion " +  '(' + client_address + ')' )
                        return HttpResponse(json.dumps({'result':'ok'}),content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({'result':'bad'}),content_type="application/json")
                except:
                    return HttpResponse(json.dumps({'result':'bad'}),content_type="application/json")





    else:
        data = {'title': 'Lugares de Recaudacion'}
        addUserData(request,data)
        try:
            if 'action' in request.GET:
                action = request.GET['action']
                if action == 'cambiaestado':
                    lugar = LugarRecaudacion.objects.get(pk=request.GET['id'])
                    if lugar.activa :
                        lugar.activa = False
                    else:
                        lugar.activa = True
                    lugar.save()
                    client_address = ip_client_address(request)

                    # Log Editar Inscripcion
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(lugar).pk,
                        object_id       = lugar.id,
                        object_repr     = force_str(lugar),
                        action_flag     = CHANGE,
                        change_message  = "Cambio de estado a: "+ str(lugar.activa) +  '(' + client_address + ')' )

                    return HttpResponseRedirect("/recaudacion")
                elif action == 'add':
                    data['form'] = LugarRecaudacionForm()
                    if 'error' in request.GET:
                        data['error'] = 1
                    data['ban'] =1
                    return render(request ,"recaudacion/add.html" ,  data)

                elif action == 'editar':
                    lugar = LugarRecaudacion.objects.get(pk=request.GET['id'])
                    initial = model_to_dict(lugar)
                    data['form'] = LugarRecaudacionForm(initial=initial)
                    data['per'] = lugar.persona
                    if 'error' in request.GET:
                        data['error'] = 1
                    data['ban'] = 2
                    data['lugar'] =lugar
                    return render(request ,"recaudacion/add.html" ,  data)
                # OCastillo 01-dic-2015
                elif action == 'eliminar':
                    sesion = SesionCaja.objects.filter(caja__id=request.GET['id'])
                    lugar = LugarRecaudacion.objects.get(pk=request.GET['id'])
                    if sesion:
                        data['error'] = 'No se puede eliminar. Tiene sesiones de caja relacionadas'
                        return render(request ,"recaudacion/recaudacion.html" ,  data)
                    else:
                        lugar.delete()

                     # data['lugares'] =lugar
                    # return render(request ,"recaudacion/recaudacion.html",+ "&error=No se puede eliminar. Tiene sesiones de caja" ,  data)
                    # return render(request ,"niveles/adicionarbs.html" ,  data)
                    # return render(request ,"recaudacion/recaudacion.html" ,  data)
                    return HttpResponseRedirect("/recaudacion")

                   # return HttpResponseRedirect("/niveles?action=add&carrera="+ str(carrera.id) +"&sede="+ str(sede.id) +"&periodo="+str(periodo.id)+"&error=Ya ingreso este PARALELO")

                elif action=='verip':
                    data = {}
                    data['iprecaudacion'] = IpRecaudLugar.objects.filter(lugarrecaudacion=request.GET['id'])
                    return render(request ,"recaudacion/detalleip.html" ,  data)
                elif action=='deliprecau':
                    iprecaudlugar = IpRecaudLugar.objects.filter(id=request.GET['id'])[:1].get()
                    # Log Editar Inscripcion
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(iprecaudlugar).pk,
                        object_id       = iprecaudlugar.id,
                        object_repr     = force_str(iprecaudlugar),
                        action_flag     = DELETION,
                        change_message  = " Eliminar Equipo de Recaudacion " +  '(' + client_address + ')' )
                    iprecaudlugar.delete()
                    return HttpResponseRedirect("/recaudacion")
            else:
                search = ""
                if 's' in request.GET:
                    search = request.GET['s']

                if search:
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')
                    if len(ss)==1:
                        lugares = LugarRecaudacion.objects.filter(Q(persona__nombres__icontains=search) | Q(persona__apellido1__icontains=search) | Q(persona__apellido2__icontains=search) | Q(persona__cedula__icontains=search) | Q(persona__pasaporte__icontains=search)| Q(nombre__icontains=search)  | Q(puntoventa__icontains=search) ).order_by('direccion')
                    else:
                        lugares = LugarRecaudacion.objects.filter(Q(persona__apellido1__icontains=ss[0]) & Q(persona__apellido2__icontains=ss[1]) | Q(nombre__icontains=search)  | Q(puntoventa__icontains=search)).order_by( 'direccion')
                else:

                    lugares = LugarRecaudacion.objects.all().order_by('direccion')
                paging = Paginator(lugares, 100)
                p = 1
                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                    page = paging.page(p)
                except:
                    page = paging.page(1)

                data['paging'] = paging
                data['page'] = page
                data['lugares'] = page.object_list
                data['search'] = search if search else ""
                data['form1'] = IpRecaudacionForm()
                return render(request ,"recaudacion/recaudacion.html" ,  data)
        except Exception as ex:
            pass

