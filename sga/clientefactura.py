from genericpath import exists
import json
from django.contrib.admin.models import LogEntry, CHANGE, ADDITION, DELETION
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
from sga.commonviews import addUserData, ip_client_address
from sga.examen_conduc import MiPaginador
from sga.forms import ClienteFacturaForm
from sga.models import ClienteFactura, Factura


def view(request):

    if request.method=='POST':
        action = request.POST['action']
        if action=='editar':
            cli=ClienteFacturaForm(request.POST)
            if cli.is_valid():
                try:
                    idclientefac=request.POST['idclientefac']
                    if ClienteFactura.objects.filter(pk=idclientefac).exists():
                        editar = ClienteFactura.objects.get(pk=idclientefac)
                        editar.ruc = cli.cleaned_data['ruc']
                        editar.nombre = cli.cleaned_data['nombre']
                        editar.direccion = cli.cleaned_data['direccion']
                        editar.telefono = cli.cleaned_data['telefono']
                        editar.correo = cli.cleaned_data['correo']
                        editar.contrasena = cli.cleaned_data['contrasena']
                        editar.numcambio = cli.cleaned_data['numcambio']

                        mensaje = 'EDICION DE CLIENTE'
                        editar.save()
                        # Log de APLICAR DONACION
                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(editar).pk,
                        object_id       = editar.id,
                        object_repr     = force_str(editar),
                        action_flag     = CHANGE,
                        change_message  = mensaje+' (' + client_address + ')' )
                        return HttpResponseRedirect("/clientefactura")
                except Exception as e:
                    return HttpResponseRedirect("/clientefactura?error="+str(e))
            else:
                return HttpResponseRedirect("/clientefactura?error=Error en el formulario")
        if action=='cambiar_cliente':
            result={}
            try:
                if ClienteFactura.objects.filter(pk=request.POST['cliente']).exists():
                    clifac=ClienteFactura.objects.filter(pk=request.POST['cliente'])[:1].get()
                    if ClienteFactura.objects.filter(id=request.POST['factura']).exists():
                        cli=ClienteFactura.objects.filter(id=request.POST['factura'])[:1].get()
                        if Factura.objects.filter(cliente__ruc=cli.ruc).exists():
                            if clifac.ruc==cli.ruc:
                                for fact in Factura.objects.filter(cliente__ruc=cli.ruc).order_by('id'):
                                    fact.cliente=clifac

                                    fact.save()

                                client_address = ip_client_address(request)

                                LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(clifac).pk,
                                object_id       = clifac.id,
                                object_repr     = force_str(clifac),
                                action_flag     = ADDITION,
                                change_message  = 'Edicion de Cliente Factura (' + client_address + ')' )
                                result['result']  = "ok"
                                return HttpResponse(json.dumps(result), content_type="application/json")
                            result['result']="EL RUC DEL CLIENTE NO ES IGUAL AL ASIGNADO"
                            return HttpResponse(json.dumps(result), content_type="application/json")
                        result['result']="EL ID DEL CLIENTE NO ES CORRECTO"
                        return HttpResponse(json.dumps(result), content_type="application/json")
                result['result']="EL ID DEL CLIENTE NO ES VALIDO"
                return HttpResponse(json.dumps(result), content_type="application/json")
            except Exception as ex:
                print(ex)
                result['result']  = str(ex)
            return HttpResponse(json.dumps(result), content_type="application/json")
        if action == 'eliminar_cliente':
            result={}
            try:
                cliente =ClienteFactura.objects.filter(pk=request.POST['idclientefac'])[:1].get()
                if cliente.contar_facturas()==0:
                    mensaje = 'Eliminar datos'
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(cliente).pk,
                        object_id       = cliente.id,
                        object_repr     = force_str(cliente),
                        action_flag     = DELETION,
                        change_message  = mensaje+' (' + client_address + ')' )
                    cliente.delete()
                    result['result']  = "ok"
                    return HttpResponse(json.dumps(result), content_type="application/json")
                else:
                    result['result']  = "No se puede elimiar por que posee facturas asociadas"
                    return HttpResponse(json.dumps(result), content_type="application/json")
            except Exception as e:
                result['result']  = str(e)
        return HttpResponse(json.dumps(result), content_type="application/json")

    else:
        data = {'title': 'Listado de Clientes Factura'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
        else:
            search  = None
            cliente_fact=None
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
                    clientes_id= ClienteFactura.objects.filter(Q(factura__numero=search)| Q(ruc=search)).distinct('id').values('id')
                    cliente_fact=ClienteFactura.objects.filter(id__in=clientes_id)


                except Exception as e:
                    pass
            else:
                cliente_fact = ClienteFactura.objects.all().order_by('factura__fecha')
            paging = MiPaginador(cliente_fact, 30)
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
            data['form'] = ClienteFacturaForm()
            data['clientefact'] = page.object_list
            if 'error' in request.GET:
                data['error']= request.GET['error']
            return render(request ,"clientefactura/clientefactura.html" ,  data)
