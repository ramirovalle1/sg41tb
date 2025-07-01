from datetime import datetime
import json
import locale
import os
from django.contrib.admin.models import LogEntry, ADDITION, DELETION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models.query_utils import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template.context import RequestContext
from django.utils.encoding import force_str
from fpdf import FPDF
from decorators import secure_module
from settings import UTILIZA_FACTURACION_CON_FPDF, JR_USEROUTPUT_FOLDER, MEDIA_URL, POSICIONES_IMPRESION, FACTURACION_CON_IVA
from sga.commonviews import addUserData, ip_client_address
from sga.finanzas import representacion_factura_str
from sga.forms import FacturaCanceladaForm, NotaCreditoInstitucionForm, NotaCreditoInstitucionAnuladaForm, EditarReciboForm
from sga.inscripciones import MiPaginador
from sga.models import Factura, FacturaCancelada, NotaCreditoInstitucion, Inscripcion, NotaCreditoInstitucionAnulada, ReciboCajaInstitucion
from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
# @secure_module
def view(request):

    if request.method=='POST':
        action = request.POST['action']
        if action=='editar':
            recibocajainstitucion = ReciboCajaInstitucion.objects.get(pk=request.POST['id'])
            r2 = str(recibocajainstitucion)
            f = EditarReciboForm(request.POST)
            persona = request.session['persona']
            # if request.session['persona'].lugarrecaudacion_set.exists():
            if f.is_valid():
                # caja = request.session['persona'].lugarrecaudacion_set.get()
                # sesion = caja.sesion_caja()

                recibocajainstitucion.valorinicial = float(f.cleaned_data['valorinicial'])
                recibocajainstitucion.saldo=float(f.cleaned_data['saldo'])
                recibocajainstitucion.save()

                #sesion = notacredito.sesion_caja()   #Obtener la sesion antes de borrar los pagos asociados

                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de ANULAR FACTURA
                LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(recibocajainstitucion).pk,
                        object_id       = recibocajainstitucion.id,
                        object_repr     = force_str(recibocajainstitucion),
                        action_flag     = ADDITION,
                        change_message  = 'Editado Recibo de Caja (' + client_address + ')')

                recibocajainstitucion.mail_recibo(request.user,str(r2),str(f.cleaned_data['motivo']))
            else:
                return HttpResponseRedirect("/recibocaja?action=editar&error=1&id="+str(recibocajainstitucion.id))

                return HttpResponseRedirect("/recibocaja")

    else:
        data = {'title': 'Listado de Recibo de Caja'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='anular':
                data['title'] = 'Anular Nota de Credito'
                notacredito = NotaCreditoInstitucion.objects.get(pk=request.GET['id'])
                data['notacredito'] = notacredito
                data['form'] = NotaCreditoInstitucionAnuladaForm()
                return render(request ,"notacredito/anular.html" ,  data)
            elif action=='editar':
                data['title'] = 'Editar Recibo de Caja'
                recibo = ReciboCajaInstitucion.objects.get(pk=request.GET['id'])
                data['recibo'] = recibo
                if 'error' in request.GET:
                    data['error']  = 'INGRESE UN MOTIVO'
                data['form'] = EditarReciboForm()
                data['form'] = EditarReciboForm(initial={'valorinicial':recibo.valorinicial, 'saldo':recibo.saldo})
                return render(request ,"recibocaja/editar.html" ,  data)
        else:

            search = None
            ret = None
            id = None
            if 'id' in request.GET:
                id = int(request.GET['id'])
            if 'ret' in request.GET:
                ret = request.GET['ret']
            if 's' in request.GET:
                search = request.GET['s']
            if search:
                recibocaja = ReciboCajaInstitucion.objects.filter(Q(id__icontains=search, saldo__gt=0)  | Q(inscripcion__persona__nombres__icontains=search) | Q(inscripcion__persona__apellido1__icontains=search) | Q(inscripcion__persona__apellido2__icontains=search)).order_by('-fecha','-id')
            else:
                if id:
                    recibocaja = ReciboCajaInstitucion.objects.filter(id=id,saldo__gt=0)
                else:
                    recibocaja = ReciboCajaInstitucion.objects.filter(saldo__gt=0).order_by('-fecha')

            paging = MiPaginador(recibocaja, 70)
            p=1
            try:
                if 'page' in request.GET:
                    p = int(request.GET['page'])
                page = paging.page(p)
            except:
                page = paging.page(1)

            paging.rangos_paginado(p)

            data['paging'] = paging
            data['page'] = page
            data['search'] = search if search else ""
            data['ret'] = ret if ret else ""
            # data['notacreditoanulada'] = notacreditoanulada
            data['recibocaja'] = page.object_list
            data['puede_pagar'] = data['persona'].puede_recibir_pagos()
            data['hora'] = datetime.now().date()
            try:
                caja = request.session['persona'].lugarrecaudacion_set.get()
                sesion_caja = caja.sesion_caja()
                data['sesion_caja'] = sesion_caja
            except :
                pass

            return render(request ,"recibocaja/recibocaja.html" ,  data)
