from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType


from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
from sga.alu_matricula import MiPaginador
from sga.commonviews import addUserData, ip_client_address
from sga.forms import ParametroDescuentoForm
from sga.models import ParametroDescuento
import json


def view(request):
    if request.method=='POST':

        if 'action' in request.POST:
            action = request.POST['action']
            if action=='add':
                d= ParametroDescuentoForm(request.POST)
                if d.is_valid():
                    try:
                        if request.POST['iddescuento']=='':
                            iddescuento=0
                        else:
                             iddescuento=request.POST['iddescuento']
                        if ParametroDescuento.objects.filter(pk=iddescuento).exists():
                            edit = ParametroDescuento.objects.get(pk=iddescuento)
                            edit.porcentaje=d.cleaned_data['porcentaje']
                            edit.cuotas = d.cleaned_data['cuotas']
                            edit.diaretras = d.cleaned_data['diaretras']
                            edit.nivel = d.cleaned_data['nivel']
                            edit.diactual = d.cleaned_data['diactual']
                            edit.activo = d.cleaned_data['activo']
                            edit.seminario = d.cleaned_data['seminario']
                            edit.matricula = d.cleaned_data['matricula']
                            mensaje = 'Edicion de Parametro'
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
                            return HttpResponseRedirect('/parametrodescuento')
                        else:
                            descuento=ParametroDescuento(porcentaje=d.cleaned_data['porcentaje'],
                                     cuotas=d.cleaned_data['cuotas'],
                                    diaretras=d.cleaned_data['diaretras'],
                                      nivel=d.cleaned_data['nivel'],
                                      diactual=d.cleaned_data['diactual'],
                                      activo=d.cleaned_data['activo'],
                                      seminario=d.cleaned_data['seminario'],
                                      matricula=d.cleaned_data['matricula'])
                            descuento.save()
                            msj='Guardado registro'
                            client_address = ip_client_address(request)
                            LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(descuento).pk,
                            object_id       = descuento.id,
                            object_repr     = force_str(descuento),
                            action_flag     = ADDITION,
                            change_message  = msj + ' (' + client_address + ')')
                            return HttpResponseRedirect("/parametrodescuento")
                    except Exception as e:
                        return HttpResponseRedirect("/parametrodescuento?error="+str(e))
                else:
                    return HttpResponseRedirect("/parametrodescuento?error=Error en el formulario")

            elif action == 'eliminar_datos':
                result={}
                try:
                    eliminar =ParametroDescuento.objects.filter(pk=request.POST['iddescuento'])[:1].get()
                    mensaje = 'Eliminar datos'
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
    else:
        data = {'title': 'Listado de Parametros'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
        else:
            search  = None
            descuento=None
            filtro  = None
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
                        descuento= ParametroDescuento.objects.filter(modulo__porcentaje__icontains=search).order_by('porcentaje')
                    else:
                        descuento = ParametroDescuento.objects.filter(modulo_porcentaje__icontains=ss[0]) .order_by('porcentaje')
                except Exception as e:
                    pass
            else:
                descuento = ParametroDescuento.objects.all().order_by('porcentaje')
            paging = MiPaginador(descuento, 30)
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
            data['form'] = ParametroDescuentoForm()
            data['descuento'] = page.object_list
            if 'error' in request.GET:
                data['error']= request.GET['error']
            return render(request ,"parametrodescuento/parametrodescuento.html" ,  data)