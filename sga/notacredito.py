from datetime import datetime
from decimal import Decimal
import json
import locale
import os
from django.contrib.admin.models import LogEntry, ADDITION, DELETION
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models.query_utils import Q
from django.forms import model_to_dict
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template.context import RequestContext
from django.utils.encoding import force_str
from fpdf import FPDF
from decorators import secure_module
from settings import UTILIZA_FACTURACION_CON_FPDF, JR_USEROUTPUT_FOLDER, MEDIA_URL, POSICIONES_IMPRESION, FACTURACION_CON_IVA
from sga.commonviews import addUserData, ip_client_address
from sga.finanzas import representacion_factura_str
from sga.forms import FacturaCanceladaForm, NotaCreditoInstitucionForm, NotaCreditoInstitucionAnuladaForm, BajaNotaCreditoForm
from sga.inscripciones import MiPaginador
from sga.models import Factura, FacturaCancelada, NotaCreditoInstitucion, Inscripcion, NotaCreditoInstitucionAnulada, BajaNC, TipoMotivoNotaCredito
from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):

    if request.method=='POST':
        action = request.POST['action']
        if action=='anular':
            notacredito = NotaCreditoInstitucion.objects.get(pk=request.POST['id'])
            f = NotaCreditoInstitucionAnuladaForm(request.POST)
            persona = request.session['persona']
            # if request.session['persona'].lugarrecaudacion_set.exists():

            if f.is_valid():
                notacredito.anulada = True
                notacredito.save()

                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de ANULAR FACTURA
                LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(notacredito).pk,
                        object_id       = notacredito.id,
                        object_repr     = force_str(notacredito),
                        action_flag     = DELETION,
                        change_message  = 'Anulada Nota de Credito (' + client_address + ')')

                notacreditoa = NotaCreditoInstitucionAnulada(notacredito=notacredito, motivo=f.cleaned_data['motivo'],
                                                             fecha=datetime.now(), usuario=persona.usuario)
                notacreditoa.save()
                return HttpResponseRedirect("/notacredito")
        elif action == 'baja':
            notacredito = NotaCreditoInstitucion.objects.get(pk=request.POST['id'])
            f = NotaCreditoInstitucionAnuladaForm(request.POST)
            if f.is_valid():
                baja = BajaNC(notacredito=notacredito,
                              motivo= f.cleaned_data['motivo'],
                              fecha=datetime.now(),
                              usuario = request.session['persona'].usuario)
                baja.save()
                notacredito.cancelada = True
                notacredito.save()
                client_address = ip_client_address(request)

                # Log de ANULAR FACTURA
                LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(notacredito).pk,
                        object_id       = notacredito.id,
                        object_repr     = force_str(notacredito),
                        action_flag     = DELETION,
                        change_message  = 'Nota de Credito Dada de Baja (' + client_address + ')')

                return HttpResponseRedirect("/notacredito")

        elif action=='eliminaduplicado':
            notacredito = NotaCreditoInstitucion.objects.get(pk=request.POST['id'])
            #Obtain client ip address
            client_address = ip_client_address(request)

            # Log de ELIMINAR DUPLICADO
            LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(notacredito).pk,
                    object_id       = notacredito.id,
                    object_repr     = force_str(notacredito),
                    action_flag     = DELETION,
                    change_message  = 'Eliminada Nota de Credito Duplicada(' + client_address + ')')

            notacredito.delete()
            datos = {"result": "ok"}
            return HttpResponse(json.dumps(datos),content_type="application/json")

    else:
        data = {'title': 'Listado de Nota de Credito'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='anular':
                data['title'] = 'Anular Nota de Credito'
                notacredito = NotaCreditoInstitucion.objects.get(pk=request.GET['id'])
                data['notacredito'] = notacredito
                data['form'] = NotaCreditoInstitucionAnuladaForm()
                return render(request ,"notacredito/anular.html" ,  data)

            action = request.GET['action']
            if action=='baja':
                notacredito = NotaCreditoInstitucion.objects.get(pk=request.GET['id'])
                data['notacredito'] = notacredito
                data['form'] = BajaNotaCreditoForm()
                return render(request ,"notacredito/baja.html" ,  data)

            elif action=='addnc':
                error = None
                data['title'] = 'Asociar Nota de Credito'
                if 'error' in request.GET:
                    data['error'] = request.GET['error']
                factura = Factura.objects.get(pk=request.GET['id'])
                data['factura'] = factura
                data['form'] = NotaCreditoInstitucionForm()
                return render(request ,"facturas/addnc.html" ,  data)
        else:

            search = None
            ret = None
            id = None
            motivoid = None
            if 'id' in request.GET:
                id = int(request.GET['id'])
            if 'ret' in request.GET:
                ret = request.GET['ret']
            if 's' in request.GET:
                search = request.GET['s']
            if 'm' in request.GET:
                motivoid = request.GET['m']
                data['motivoid'] = int(motivoid) if motivoid else ""
                data['motivos'] = TipoMotivoNotaCredito.objects.get(pk=request.GET['m'])
                notacredito =  NotaCreditoInstitucion.objects.filter(motivonc=data['motivos']).distinct().order_by('-fecha','-numero')

            if search:
                notacredito = NotaCreditoInstitucion.objects.filter(Q(numero__icontains=search)).order_by('-fecha','-numero')
            else:
                if id:
                    notacredito = NotaCreditoInstitucion.objects.filter(id=id)
                elif motivoid:
                    notacredito = NotaCreditoInstitucion.objects.filter(motivonc__in=motivoid).order_by('-fecha','-numero')
                else:
                    notacredito = NotaCreditoInstitucion.objects.all().order_by('-fecha','-numero')
            notacreditoanulada = NotaCreditoInstitucionAnulada.objects.all().order_by('-fecha')

            paging = MiPaginador(notacredito, 20)
            p=1
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
            data['motivo'] = motivoid if motivoid else ""
            if motivoid:
                data['motivos'] = TipoMotivoNotaCredito.objects.filter(id__in=motivoid).order_by('descripcion')
            else:
                data['motivos'] = TipoMotivoNotaCredito.objects.all().order_by('descripcion')
            data['ret'] = ret if ret else ""
            data['notacreditoanulada'] = notacreditoanulada
            data['notacredito'] = page.object_list
            data['puede_pagar'] = data['persona'].puede_recibir_pagos()
            data['hora'] = datetime.now().date()
            try:
                caja = request.session['persona'].lugarrecaudacion_set.get()
                sesion_caja = caja.sesion_caja()
                data['sesion_caja'] = sesion_caja
            except :
                pass

            return render(request ,"notacredito/notacredito.html" ,  data)
