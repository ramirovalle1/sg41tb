import json
from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import Sum
from django.forms import model_to_dict
from django.utils.encoding import force_str
from decorators import secure_module
from settings import EMAIL_ACTIVE, MARGEN_GANANCIA
from sga.models import RegistroMedicamento, TipoMedicamento, DetalleRegistroMedicamento, BajaMedicamento, RecetaVisitaBox, Sede, Persona, TrasladoMedicamento,\
     DetalleVisitasBox, Profesor, Aula,ResponsableBodegaConsultorio
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.core.paginator import Paginator
from sga.commonviews import addUserData, ip_client_address
from django.template import RequestContext
from sga.forms import RegistroMedicamentoForm, EntregaMedicamentoForm
from datetime import datetime

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
@transaction.atomic()
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action == 'add':
                f = RegistroMedicamentoForm(request.POST)
                if f.is_valid():
                    if 'regismed' in request.POST:
                        registromedicamento = RegistroMedicamento.objects.get(id=request.POST['regismed'])
                        if int(registromedicamento.cantidad) >= int(f.cleaned_data['cantidad']):
                            registromedicamento.cantidad = int(registromedicamento.cantidad) - int(f.cleaned_data['cantidad'])
                            bajamedicina = BajaMedicamento(
                                            registromedicamento_id = registromedicamento.id,
                                            cantidad = f.cleaned_data['cantidad'],
                                            motivo = f.cleaned_data['motivo'],
                                            fecha=datetime.now().date(),
                                            lote=request.POST['lote'],
                                            observacion = f.cleaned_data['observacion'],
                                            usuario = request.user)
                            if request.POST['tipbaja'] == 'detalle':
                                tipobaja = DetalleRegistroMedicamento.objects.filter(id=request.POST['idtipobaja'])[:1].get()
                            else:
                                tipobaja = TrasladoMedicamento.objects.filter(id=request.POST['idtipobaja'])[:1].get()
                            tipobaja.stock = tipobaja.stock - int(f.cleaned_data['cantidad'])
                            tipobaja.save()
                            bajamedicina.save()
                            registromedicamento.save()

                            if EMAIL_ACTIVE:
                                if Persona.objects.filter(usuario=request.user).exists():
                                    bajamedicina.mail_bajamedicamento(str(Persona.objects.filter(usuario=request.user)[:1].get().nombre_completo()))
                                else:
                                    bajamedicina.mail_bajamedicamento('se')
                        else:
                            return HttpResponseRedirect("/registromedicamento?action=edit&id="+str(registromedicamento.id)+"&error="+str(f.cleaned_data['cantidad']))
                    else:
                        if RegistroMedicamento.objects.filter( nombre = f.cleaned_data['nombre'],presentacion = f.cleaned_data['presentacion'],bodega = f.cleaned_data['bodega']).exists():
                            registromedicamento = RegistroMedicamento.objects.get(nombre = f.cleaned_data['nombre'],presentacion = f.cleaned_data['presentacion'],bodega = f.cleaned_data['bodega'])
                            registromedicamento.cantidad = registromedicamento.cantidad + int(f.cleaned_data['cantidad'])
                        else:
                            registromedicamento = RegistroMedicamento(nombre = f.cleaned_data['nombre'],
                                                                      presentacion = f.cleaned_data['presentacion'],
                                                                      cantidad = f.cleaned_data['cantidad'],
                                                                      bodega = f.cleaned_data['bodega'],
                                                                      observacion=f.cleaned_data['observacion'])
                        registromedicamento.save()

                        detalle = DetalleRegistroMedicamento(registromedicamento_id = registromedicamento.id,
                                                             cantidad = f.cleaned_data['cantidad'],
                                                             costo_unitario = f.cleaned_data['costo'],
                                                             fechavencimiento = f.cleaned_data['fechavencimiento'],
                                                             lote = f.cleaned_data['lote'],
                                                             observacion=f.cleaned_data['observacion'],
                                                             stock = f.cleaned_data['cantidad'],
                                                             fechaingreso = datetime.now().date())

                        detalle.save()
                        if registromedicamento.costo:
                            registromedicamento.costo =  (registromedicamento.costo + f.cleaned_data['costo'])/2
                        else:
                            registromedicamento.costo =  f.cleaned_data['costo']
                        registromedicamento.precio_venta =  registromedicamento.costo
                        registromedicamento.factura =  f.cleaned_data['factura']
                        registromedicamento.iva = f.cleaned_data['iva']
                        registromedicamento.save()
                    client_address = ip_client_address(request)
                    if 'regismed' in request.POST:
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(registromedicamento).pk,
                            object_id       = registromedicamento.id,
                            object_repr     = force_str(registromedicamento),
                            action_flag     = ADDITION,
                            change_message  = 'Baja de Medicamento (' + client_address + ')' )
                    else:
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(registromedicamento).pk,
                            object_id       = registromedicamento.id,
                            object_repr     = force_str(registromedicamento),
                            action_flag     = ADDITION,
                            change_message  = 'Ingreso de Registro de Medicamento (' + client_address + ')' )
                    return HttpResponseRedirect("/registromedicamento?id="+str(registromedicamento.id))
                return HttpResponseRedirect("/registromedicamento?action=add")
            elif action == 'entregar':

                client_address = ip_client_address(request)
                registromedicamento = RegistroMedicamento.objects.get(id=request.POST['regismed'])
                bodega = None
                if Aula.objects.filter(ip=str(client_address),activa=False,sede__id=9).exists():
                    bodega = Aula.objects.filter(ip=str(client_address),activa=False,sede__id=9)[:1].get().sede
                    if bodega != registromedicamento.bodega:
                        return HttpResponseRedirect("/registromedicamento?action=entregar&id="+str(registromedicamento.id)+"&error2=No Tiene Permiso para entregar Suministros de esta Bodega")
                else:
                    return HttpResponseRedirect("/registromedicamento?action=entregar&id="+str(registromedicamento.id)+"&error2=No Puede Entregar desde este equipo")
                f = EntregaMedicamentoForm(request.POST)
                if f.is_valid():
                    if int(registromedicamento.cantidad) >= int(f.cleaned_data['cantidad']):
                        registromedicamento.cantidad = int(registromedicamento.cantidad) - int(f.cleaned_data['cantidad'])
                        profesor = Profesor.objects.filter(pk=f.cleaned_data['profesor_id'])[:1].get()
                        bajamedicina = BajaMedicamento(
                                        registromedicamento_id = registromedicamento.id,
                                        cantidad = f.cleaned_data['cantidad'],
                                        motivo = f.cleaned_data['motivo'],
                                        fecha=datetime.now().date(),
                                        lote=request.POST['lote'],
                                        observacion = f.cleaned_data['observacion'],
                                        profesor = profesor,
                                        usuario = request.user)
                        if request.POST['tipbaja'] == 'detalle':
                            tipobaja = DetalleRegistroMedicamento.objects.filter(id=request.POST['idtipobaja'])[:1].get()
                        else:
                            tipobaja = TrasladoMedicamento.objects.filter(id=request.POST['idtipobaja'])[:1].get()
                        tipobaja.stock = tipobaja.stock - int(f.cleaned_data['cantidad'])
                        tipobaja.save()
                        bajamedicina.save()
                        registromedicamento.save()
                        client_address = ip_client_address(request)

                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(registromedicamento).pk,
                            object_id       = registromedicamento.id,
                            object_repr     = force_str(registromedicamento),
                            action_flag     = ADDITION,
                            change_message  = 'Entrega de Medicamento (' + client_address + ')' )

                        return HttpResponseRedirect("/registromedicamento?id="+str(registromedicamento.id))

                    else:
                        return HttpResponseRedirect("/registromedicamento?action=entregar&id="+str(registromedicamento.id)+"&error="+str(f.cleaned_data['cantidad']))


                return HttpResponseRedirect("/registromedicamento?action=entregar&id="+str(registromedicamento.id)+"&error="+str(f.cleaned_data['cantidad']))

            elif action =='editar':
                f = RegistroMedicamentoForm(request.POST)
                if f.is_valid():
                    registro = RegistroMedicamento.objects.get(pk=request.POST['regismed'])
                    # if DetalleRegistroMedicamento.objects.filter(registromedicamento=registro).exists():
                    #     detalle = DetalleRegistroMedicamento.objects.filter(registromedicamento=registro)[:1].get()
                    #     detalle.costo_unitario = f.cleaned_data['costo']
                    #     detalle.save()
                    #
                    #     registro.costo = (detalle.costo_unitario *  f.cleaned_data['costo'])/2
                    # else:
                    registro.costo = f.cleaned_data['costo']
                    if MARGEN_GANANCIA:
                        registro.precio_venta = (registro.costo + (registro.costo*MARGEN_GANANCIA))
                    else:
                        registro.precio_venta = registro.costo
                    registro.factura =  f.cleaned_data['factura']
                    registro.iva = f.cleaned_data['iva']
                    registro.save()
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(registro).pk,
                        object_id       = registro.id,
                        object_repr     = force_str(registro),
                        action_flag     = ADDITION,
                        change_message  = 'Precio Editado '+ str(registro.nombre.descripcion) +' (' + client_address + ')' )
                    return HttpResponseRedirect("/registromedicamento")
            elif action == 'consult':
                registro = RegistroMedicamento.objects.get(id = request.POST['id'])
                if int(registro.cantidad) < int(request.POST['cant']):
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                else:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
            elif action == 'addstockdet':
                try:
                    detalle = DetalleRegistroMedicamento.objects.get(id = request.POST['iddet'])
                    detalle.stock = request.POST['stock']
                    detalle.save()
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({"result":str(e)}),content_type="application/json")
            elif action == 'addstocktrasl':
                try:
                    detalle = TrasladoMedicamento.objects.get(id = request.POST['iddet'])
                    detalle.stock = request.POST['stock']
                    detalle.save()
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
            elif action == 'addlotetrasl':
                try:
                    detalle = TrasladoMedicamento.objects.get(id = request.POST['iddet'])
                    detalle.lote = request.POST['stock']
                    detalle.save()
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
            elif action == 'eliminar':
                registro = RegistroMedicamento.objects.get(id = request.POST['id'])
                if RecetaVisitaBox.objects.filter(registro=registro).exists() or BajaMedicamento.objects.filter(registromedicamento=registro).exists():
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                else:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

            elif action == 'traslado':
                try:
                    registro = RegistroMedicamento.objects.get(id = request.POST['id'])
                    if RegistroMedicamento.objects.filter( nombre = registro.nombre,presentacion = registro.presentacion,bodega__id = request.POST['bodegarecibo']).exists():
                        registromedicamento = RegistroMedicamento.objects.get(nombre = registro.nombre,presentacion = registro.presentacion,bodega__id = request.POST['bodegarecibo'])
                        registromedicamento.cantidad = registromedicamento.cantidad + int(request.POST['cantidad'])
                    else:
                        registromedicamento = RegistroMedicamento(
                                                                nombre = registro.nombre,
                                                                presentacion =registro.presentacion,
                                                                cantidad = request.POST['cantidad'],
                                                                bodega_id =  request.POST['bodegarecibo'])
                    registromedicamento.save()
                    trasladomedicamento = TrasladoMedicamento(
                                    registromedicamento_id = request.POST['id'],
                                    bodegaenvio_id = request.POST['bodegaenvio'],
                                    bodegarecibo_id = request.POST['bodegarecibo'],
                                    cantidad = request.POST['cantidad'],
                                    observacion = request.POST['observacion'],
                                    fechatraslado = datetime.now(),
                                    fechavencimiento = request.POST['fechavencimiento'].split(' .')[0],
                                    lote = request.POST['lote'],
                                    stock = request.POST['cantidad'],
                                    registmedicadest = registromedicamento,
                                    user_id = request.user.pk)
                    trasladomedicamento.save()

                    registro.cantidad = registro.cantidad - int(request.POST['cantidad'])
                    if request.POST['tipbaja'] == 'detalle':
                        tipobaja = DetalleRegistroMedicamento.objects.filter(id=request.POST['idtipobaja'])[:1].get()
                    else:
                        tipobaja = TrasladoMedicamento.objects.filter(id=request.POST['idtipobaja'])[:1].get()
                    tipobaja.stock = tipobaja.stock - int(request.POST['cantidad'])
                    tipobaja.save()
                    registro.save()
                    if EMAIL_ACTIVE:
                        trasladomedicamento.mail_traslmedicamento()

                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(trasladomedicamento).pk,
                                object_id       = trasladomedicamento.id,
                                object_repr     = force_str(trasladomedicamento),
                                action_flag     = ADDITION,
                                change_message  = 'Traslado de Medicamento (' + client_address + ')' )
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
            return HttpResponseRedirect("/registromedicamento")

        else:
            data = {'title': 'Registro de Medicamento'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']
                if action == 'add':
                    data['title']= 'Ingresar Medicina'
                    form = RegistroMedicamentoForm({"fechavencimiento":datetime.now().date()})
                    form.for_suministro()
                    if request.GET['op']=='1':
                        client_address = ip_client_address(request)
                        print('ip')
                        print(client_address)
                        sede = Aula.objects.filter(ip=str(client_address),activa=False)[:1].get()
                        form.for_bodega(sede.sede_id)
                    data['form']= form
                    return render(request ,"registromedicamento/nuevomedicamento.html" ,  data)
                elif action == 'edit':
                    data['title']= 'Dar de baja Medicina'
                    if 'error' in request.GET:
                        data['error']=request.GET['error']
                    data['regismed']= RegistroMedicamento.objects.get(id=request.GET['id'])
                    initial = model_to_dict(data['regismed'])
                    form = RegistroMedicamentoForm(initial=initial)
                    # form = RegistroMedicamentoForm(instance=data['regismed'])
                    data['form']= form
                    return render(request ,"registromedicamento/nuevomedicamento.html" ,  data)
                elif action == 'entregar':
                    data['title']= 'Entregar Medicina o Suministro'
                    if 'error' in request.GET:
                        data['error']=request.GET['error']
                    if 'error2' in request.GET:
                        data['error2']=request.GET['error2']
                    data['regismed']= RegistroMedicamento.objects.get(id=request.GET['id'])
                    initial = model_to_dict(data['regismed'])
                    form = EntregaMedicamentoForm(initial=initial)
                    data['entregar']=1
                    # form = RegistroMedicamentoForm(instance=data['regismed'])
                    data['form']= form
                    return render(request ,"registromedicamento/entregamedicamento.html" ,  data)
                elif action == 'editar':
                    data['title']= 'Editar Medicamento'
                    if 'error' in request.GET:
                        data['error']=request.GET['error']
                    data['regismed']= RegistroMedicamento.objects.get(id=request.GET['id'])
                    initial = model_to_dict(data['regismed'])
                    form = RegistroMedicamentoForm(initial=initial)
                    data['form']= form
                    return render(request ,"registromedicamento/editmedicamento.html" ,  data)
                elif action == 'eliminar':
                    registro = RegistroMedicamento.objects.get(id=request.GET['id'])
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(registro).pk,
                        object_id       = registro.id,
                        object_repr     = force_str(registro),
                        action_flag     = ADDITION,
                        change_message  = 'eliminacion de medicamento '+ str(registro.nombre.descripcion) +' (' + client_address + ')' )
                    registro.delete()
                    return  HttpResponseRedirect("/registromedicamento")
                elif action == 'detalle':
                    registromedi = DetalleRegistroMedicamento.objects.filter(registromedicamento=request.GET['reg']).order_by('-fechavencimiento','fechaingreso')
                    paging = MiPaginador(registromedi, 30)
                    p = 1
                    try:
                        if 'page' in request.GET:
                            p = int(request.GET['page'])
                        page = paging.page(p)
                    except:
                        page = paging.page(p)

                    data['paging'] = paging
                    data['rangospaging'] = paging.rangos_paginado(p)
                    data['page'] = page
                    data['title']= 'Detalle de Baja de Medicina'
                    data['detalle']= page.object_list
                    data['registro']= RegistroMedicamento.objects.get(id=request.GET['reg'])
                    return render(request ,"registromedicamento/detalleregistro.html" ,  data)
                elif action == 'baja':
                    bajamedi = BajaMedicamento.objects.filter(registromedicamento=request.GET['reg'],profesor=None).order_by('-fecha')
                    paging = MiPaginador(bajamedi, 30)
                    p = 1
                    try:
                        if 'page' in request.GET:
                            p = int(request.GET['page'])
                        page = paging.page(p)
                    except:
                        page = paging.page(p)

                    # data['registrovisita'] = RecetaVisitaBox.objects.filter(registro__id=request.GET['reg']).aggregate(Sum('cantidad'))['cantidad__sum']
                    data['paging'] = paging
                    data['rangospaging'] = paging.rangos_paginado(p)
                    data['page'] = page
                    data['title']= 'Detalle de baja de Medicamento'
                    data['detalle']= page.object_list
                    data['registro']= RegistroMedicamento.objects.get(id=request.GET['reg'])
                    return render(request ,"registromedicamento/bajamedicamento.html" ,  data)
                elif action == 'entrega':
                    bajamedi = BajaMedicamento.objects.filter(registromedicamento=request.GET['reg']).exclude(profesor=None).order_by('-fecha')
                    paging = MiPaginador(bajamedi, 30)
                    p = 1
                    try:
                        if 'page' in request.GET:
                            p = int(request.GET['page'])
                        page = paging.page(p)
                    except:
                        page = paging.page(p)

                    # data['registrovisita'] = RecetaVisitaBox.objects.filter(registro__id=request.GET['reg']).aggregate(Sum('cantidad'))['cantidad__sum']
                    data['paging'] = paging
                    data['rangospaging'] = paging.rangos_paginado(p)
                    data['page'] = page
                    data['title']= 'Detalle de Entrega de Medicamento'
                    data['detalle']= page.object_list
                    data['registro']= RegistroMedicamento.objects.get(id=request.GET['reg'])
                    data['entrega'] = 1
                    return render(request ,"registromedicamento/bajamedicamento.html" ,  data)
                elif action == 'bajareceta':
                    registrovisita = RecetaVisitaBox.objects.filter(registro__id=request.GET['reg']).order_by('-fecha')

                    paging = MiPaginador(registrovisita, 30)
                    p = 1
                    try:
                        if 'page' in request.GET:
                            p = int(request.GET['page'])
                        page = paging.page(p)
                    except:
                        page = paging.page(p)
                    data['total'] = RecetaVisitaBox.objects.filter(registro__id=request.GET['reg']).aggregate(Sum('cantidad'))['cantidad__sum']
                    data['paging'] = paging
                    data['rangospaging'] = paging.rangos_paginado(p)
                    data['page'] = page
                    data['title']= 'Detalle de baja de Medicamento x Receta'
                    data['detalle']= page.object_list
                    data['registro']= RegistroMedicamento.objects.get(id=request.GET['reg'])
                    return render(request ,"registromedicamento/bajareceta.html" ,  data)
                elif action == 'trasladosdet':
                    if '_' in request.GET['reg']:
                        traslado = TrasladoMedicamento.objects.filter(registromedicamento__id=int(str(request.GET['reg']).split('_')[0]))
                        data['registro'] = request.GET['reg']
                    else:
                        data['registro'] = request.GET['reg']
                        registro= RegistroMedicamento.objects.get(id=request.GET['reg'])
                        traslado = TrasladoMedicamento.objects.filter(registromedicamento__nombre=registro.nombre,registromedicamento__presentacion=registro.presentacion,bodegarecibo=registro.bodega)
                    paging = MiPaginador(traslado, 30)
                    p = 1
                    try:
                        if 'page' in request.GET:
                            p = int(request.GET['page'])
                        page = paging.page(p)
                    except:
                        page = paging.page(p)
                    data['paging'] = paging
                    data['rangospaging'] = paging.rangos_paginado(p)
                    data['page'] = page
                    data['title']= 'Detalle de Traslado'
                    data['detalle']= page.object_list
                    return render(request ,"registromedicamento/traslado.html" ,  data)
            else:
                search = None
                todos = None
                bandera = 0
                lab=[]
                client_address = ip_client_address(request)
                #OCastillo 21-07-2021 cambio por nueva tabla responsable bodega
                medico=Persona.objects.filter(usuario=request.user)[:1].get()
                data['medico']=medico

                if Aula.objects.filter(ip=str(client_address),activa=False,sede__id=10).exists():
                    for a in Aula.objects.filter(ip=str(client_address),activa=False):
                    # bodega = Aula.objects.filter(ip=str(client_address),activa=False)[:1].get().sede
                    # if bodega.id == 9:
                        lab.append(a.sede_id)
                    lab.append(9)
                elif Aula.objects.filter(ip=str(client_address),activa=False,sede__id=9).exists():
                    # bodega = Aula.objects.filter(ip=str(client_address),activa=False)[:1].get().sede
                    # if bodega.id == 9:
                    lab.append(9)
                elif ResponsableBodegaConsultorio.objects.filter(medico=medico,activa=True).exists():
                     sede=ResponsableBodegaConsultorio.objects.filter(medico=medico,activa=True)[:1].get().bodega.id
                     lab.append(sede)
                if len(lab) == 0:
                    lab =Sede.objects.filter().exclude(id=9).exclude(id=10).values('id')
                if data['persona'].usuario.is_superuser:
                    lab =Sede.objects.filter().values('id')
                if 's' in request.GET:
                    search = request.GET['s']
                if 't' in request.GET:
                    todos = request.GET['t']
                if search:
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')

                    registromedi = RegistroMedicamento.objects.filter(nombre__descripcion__icontains=search,bodega__id__in=lab).exclude(presentacion=None,cantidad=0).order_by('nombre__descripcion')
                    bandera = 1
                if 'g' in request.GET:
                    tipoid = request.GET['g']
                    if tipoid == "0":
                        data['grupo'] = tipoid
                        data['grupoid'] = int(tipoid)
                        registromedi = RegistroMedicamento.objects.filter(presentacion=None,bodega__id__in=lab).exclude(cantidad=0).order_by('nombre__descripcion')
                    else:
                        data['grupo'] = TipoMedicamento.objects.get(pk=request.GET['g'])
                        data['grupoid'] = int(tipoid) if tipoid else ""
                        registromedi = RegistroMedicamento.objects.filter(presentacion=data['grupo'],bodega__id__in=lab).exclude(presentacion=None,cantidad=0).order_by('nombre__descripcion')
                    bandera = 1
                if 'se' in request.GET:
                    grupoids = request.GET['se']
                    data['grupose'] = Sede.objects.get(pk=request.GET['se'])
                    data['grupoids'] = int(grupoids) if grupoids else ""
                    if bandera == 1:
                        registromedi = registromedi.filter(bodega=data['grupose'],bodega__id__in=lab).exclude(presentacion=None,cantidad=0).order_by('nombre__descripcion')
                    else:
                        registromedi = RegistroMedicamento.objects.filter(bodega=data['grupose'],bodega__id__in=lab).exclude(presentacion=None,cantidad=0).order_by('nombre__descripcion')
                    bandera = 1

                if bandera == 0:
                    registromedi = RegistroMedicamento.objects.filter(bodega__id__in=lab).exclude(presentacion=None,cantidad=0).order_by('nombre__descripcion')
                if 'id' in request.GET:
                    data['id_reg'] = request.GET['id']
                    registromedi = RegistroMedicamento.objects.filter(id=request.GET['id'],bodega__id__in=lab)

                paging = MiPaginador(registromedi, 30)
                p = 1
                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                    page = paging.page(p)
                except:
                    page = paging.page(p)


                per = RequestContext(request)
                data['paging'] = paging
                data['rangospaging'] = paging.rangos_paginado(p)
                data['page'] = page
                data['search'] = search if search else ""
                data['todos'] = todos if todos else ""
                data['medicamento'] = page.object_list
                data['gruposede'] = Sede.objects.filter(id__in=lab).order_by('nombre')
                data['grupos'] = TipoMedicamento.objects.all().order_by('descripcion')
                data['bodega'] = Sede.objects.all().order_by('nombre')
                return render(request ,"registromedicamento/registromedicamento.html" ,  data)
    except Exception as ex:
        return HttpResponseRedirect("/")