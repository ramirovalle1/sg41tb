import json
from django.contrib.admin.models import LogEntry, CHANGE, ADDITION, DELETION
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
from sga.alu_matricula import MiPaginador
from sga.commonviews import addUserData
from sga.forms import AulaManForm
from sga.models import Aula
from socioecon.cons_socioecon import ip_client_address


def view(request):
    if request.method=='POST':

        if 'action' in request.POST:
            action = request.POST['action']
            if action=='add':
                a=AulaManForm(request.POST)
                if a.is_valid():
                    try:
                        if request.POST['idaula']=='':
                            idaula=0
                        else:
                             idaula=request.POST['idaula']
                        if Aula.objects.filter(pk=idaula).exists():
                            edit=Aula.objects.get(pk=idaula)
                            edit.nombre=a.cleaned_data['nombre']
                            edit.capacidad=a.cleaned_data['capacidad']
                            edit.tipo=a.cleaned_data['tipo']
                            edit.sede=a.cleaned_data['sede']
                            edit.ip=a.cleaned_data['ip']
                            edit.activa=a.cleaned_data['activa']
                            mensaje = 'Edicion de Aulas'
                            edit.save()
                            # Log de APLICAR DONACION
                            client_address = ip_client_address(request)
                            LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(edit).pk,
                            object_id       = edit.id,
                            object_repr     = force_str(edit),
                            action_flag     = CHANGE,
                            change_message  = mensaje+' (' + client_address + ')' )
                            return HttpResponseRedirect('/aulamantenimiento')
                        else:
                            aula=Aula(nombre=a.cleaned_data['nombre'],
                                    capacidad=a.cleaned_data['capacidad'],
                                    tipo=a.cleaned_data['tipo'],
                                    sede=a.cleaned_data['sede'],
                                    ip=a.cleaned_data['ip'],
                                    activa=a.cleaned_data['activa'])
                            aula.save()
                            msj='Guardado registro'
                            client_address = ip_client_address(request)
                            LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(aula).pk,
                            object_id       = aula.id,
                            object_repr     = force_str(aula),
                            action_flag     = ADDITION,
                            change_message  = msj + ' (' + client_address + ')')
                            return HttpResponseRedirect("/aulamantenimiento")
                    except Exception as e:
                        return HttpResponseRedirect("/aulamantenimiento?error="+str(e))
                else:
                    return HttpResponseRedirect("/aulamantenimiento?error=EL FORMULARIO ESTA INCORRECTO")

            elif action == 'eliminar_aula':
                result={}
                try:
                    aula =Aula.objects.filter(pk=request.POST['idaula'])[:1].get()
                    mensaje = 'Eliminar datos'
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(aula).pk,
                        object_id       = aula.id,
                        object_repr     = force_str(aula),
                        action_flag     = DELETION,
                        change_message  = mensaje+' (' + client_address + ')' )
                    aula.delete()
                    result['result']  = "ok"
                    return HttpResponse(json.dumps(result), content_type="application/json")
                except Exception as e:
                    result['result']  = str(e)
                    return HttpResponse(json.dumps(result), content_type="application/json")
    else:
        data = {'title': 'Listado de Aulas'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
        else:
            search  = None
            aula  = None

            ejerce = None
            cargo = None
            if 'filter' in request.GET:
                filtro = request.GET['filter']
                data['filtro']  = filtro


            if 's' in request.GET:
                search = request.GET['s']

            if search:
                try:
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')
                    if len(ss)==1:
                        aula = Aula.objects.filter(nombre__icontains=search).order_by('nombre')
                    else:
                        aula = Aula.objects.all().order_by('nombre')
                except Exception as e:
                    pass
            else:
                aula = Aula.objects.all().order_by('nombre')


            paging = MiPaginador(aula, 30)
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
            data['form'] = AulaManForm()
            data['aula'] = page.object_list
            if 'error' in request.GET:
                data['error']= request.GET['error']
            return render(request ,"aula/aulaman.html" ,  data)