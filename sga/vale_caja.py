# -*- coding: latin-1 -*-
from datetime import datetime
import json
from django.contrib.admin.models import LogEntry, DELETION, ADDITION, CHANGE
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models.query_utils import Q
from django.forms.models import model_to_dict
from django.http import  HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
from decorators import secure_module
from sga.commonviews import addUserData,  total_efectivo_sesion, total_vale_sesion
from sga.forms import ValeCajaForm, AnulaValeForm, MotivoBaja
from sga.models import ValeCaja


@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    if request.method=='POST':
        action = request.POST['action']
        if action=='add':
            caja = request.session['persona'].lugarrecaudacion_set.get()
            sesion_caja = caja.sesion_caja()
            hora_actual=datetime.now().time()
            f = ValeCajaForm(request.POST)
            if f.is_valid():
                vale = ValeCaja(valor=f.cleaned_data['valor'],
                                recibe=f.cleaned_data['recibe'],
                                responsable=f.cleaned_data['responsable'],
                                concepto=f.cleaned_data['concepto'],
                                referencia=f.cleaned_data['referencia'],
                                sesion=sesion_caja,
                                hora=hora_actual,
                                anulado=False)
                vale.save()
                try:
                        # case server externo
                    client_address = request.META['HTTP_X_FORWARDED_FOR']
                except:
                    # case localhost o 127.0.0.1
                    client_address = request.META['REMOTE_ADDR']

                # Log de ADICIONADO VALE DE CAJA
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(vale).pk,
                    object_id       = vale.id,
                    object_repr     = force_str(vale),
                    action_flag     = ADDITION,
                    change_message  = 'Adicionado Vale de Caja (' + client_address + ')' )
                return HttpResponseRedirect("/vale_caja")
        elif action == 'baja':
            f = MotivoBaja(request.POST)
            hoy = datetime.now().date()
            vale = ValeCaja.objects.get(pk=request.POST['vale'])
            if  f.is_valid():
                vale.motivo_baja=f.cleaned_data['motivo']
                vale.pendiente = False
                vale.fecha_baja = hoy
                vale.save()
                return HttpResponseRedirect("/vale_caja")
            else:
                return HttpResponseRedirect("/vale_caja?action=edit&id"+str(vale.id))


        elif action == 'verifica_saldo':
            result = {}
            caja = request.session['persona'].lugarrecaudacion_set.get()
            sesion_caja = caja.sesion_caja()
            hoy = datetime.now().date()
            total = total_efectivo_sesion(hoy,sesion_caja) - total_vale_sesion(hoy,sesion_caja)
            if float(request.POST['valor']) <= total:
                result['result']  = "ok"
            else:
                result['result']  = "bad"
            return HttpResponse(json.dumps(result),content_type="application/json")

        elif action=='edit':
            vale = ValeCaja.objects.get(pk=request.POST['id'])
            caja = request.session['persona'].lugarrecaudacion_set.get()
            sesion_caja = caja.sesion_caja()
            hora_actual=datetime.now().time()
            f = ValeCajaForm(request.POST)
            if f.is_valid():
                vale.valor=f.cleaned_data['valor']
                vale.recibe=f.cleaned_data['recibe']
                vale.responsable=f.cleaned_data['responsable']
                vale.concepto=f.cleaned_data['concepto']
                vale.referencia=f.cleaned_data['referencia']
                vale.sesion=sesion_caja
                vale.hora=hora_actual

                vale.save()
            else:
                return HttpResponseRedirect("/vale_caja?action=edit&id"+str(vale.id))
        elif action == 'anular':
            vale = ValeCaja.objects.get(pk=request.POST['id'])
            f = AnulaValeForm(request.POST)
            if f.is_valid():
                vale.anulado = True
                vale.motivo = f.cleaned_data['motivo']
                vale.fecha_anula = f.cleaned_data['fecha']
                vale.save()
                try:
                            # case server externo
                    client_address = request.META['HTTP_X_FORWARDED_FOR']
                except:
                    # case localhost o 127.0.0.1
                    client_address = request.META['REMOTE_ADDR']

                    # Log de ANULADO VALE DE CAJA
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(vale).pk,
                    object_id       = vale.id,
                    object_repr     = force_str(vale),
                    action_flag     = CHANGE,
                    change_message  = 'Anulado Vale de Caja (' + client_address + ')' )

                return HttpResponseRedirect("/vale_caja")

    else:
        data = {'title': 'Listado de Vales de Caja'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='add':
                data['title'] = 'Adicionar Vale de Caja'
                data['form'] = ValeCajaForm()
                return render(request ,"vale_caja/adicionarbs.html" ,  data)
            elif action=='edit':
                data['title'] = 'Editar Vale de Caja'
                vale = ValeCaja.objects.get(pk=request.GET['id'])
                initial = model_to_dict(vale)
                data['form'] = ValeCajaForm(initial=initial)
                data['vale'] = vale
                return render(request ,"vale_caja/editarbs.html" ,  data)
            elif action == 'baja':
                data['title'] = 'Motivo Apertura de Clase'
                data['form'] = MotivoBaja(initial={'fecha': datetime.now().strftime("%d-%m-%Y")})
                data['id_vale'] = request.GET['id']
                return render(request ,"vale_caja/motivo_baja.html" ,  data)


            elif action=='anular':
                data['venta'] = ValeCaja.objects.get(pk=request.GET['id'])
                data['form'] = AnulaValeForm()
                data['form'] =AnulaValeForm(initial={'fecha': datetime.now().strftime("%d-%m-%Y")})
                return render(request ,"vale_caja/anulavale.html" ,  data)

        else:
            search = None
            if 's' in request.GET:
                search = request.GET['s']
            if search:
                vales = ValeCaja.objects.filter(Q(referencia__icontains=search) | Q(valor__icontains=search) | Q(recibe__icontains=search) | Q(responsable__icontains=search) | Q(sesion__caja__persona__nombres__icontains=search)| Q(sesion__caja__persona__apellido1__icontains=search)| Q(sesion__caja__persona__apellido2__icontains=search)).order_by('-sesion__fecha','-hora')
            else:
                vales = ValeCaja.objects.all().order_by('-sesion__fecha','-hora')
            paging = Paginator(vales, 50)
            p=1
            try:
                if 'page' in request.GET:
                    p = int(request.GET['page'])
                page = paging.page(p)
            except:
                page = paging.page(1)
            data['paging'] = paging
            data['page'] = page
            data['search'] = search if search else ""
            data['vales'] = page.object_list
            data['hoy'] =  datetime.now().date()
            data['puede_pagar'] = data['persona'].puede_recibir_pagos()
            return render(request ,"vale_caja/valesbs.html" ,  data)
