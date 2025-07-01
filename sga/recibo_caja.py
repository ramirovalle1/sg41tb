# -*- coding: latin-1 -*-
from datetime import datetime
from django.contrib.admin.models import LogEntry, CHANGE, ADDITION
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models.query_utils import Q
from django.forms.models import model_to_dict
from django.http import  HttpResponseRedirect
from django.shortcuts import render
from django.utils.encoding import force_str
from decorators import secure_module
from sga.commonviews import addUserData
from sga.forms import  ReciboCajaForm
from sga.models import  ReciboCaja


@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    if request.method=='POST':
        action = request.POST['action']
        if action=='add':
            persona = request.session['persona']
            if persona.lugarrecaudacion_set.exists():
                caja = request.session['persona'].lugarrecaudacion_set.get()
                if caja.sesion_caja():
                    sesion_caja = caja.sesion_caja()
                    hora_actual=datetime.now().time()
                    f = ReciboCajaForm(request.POST)
                    if f.is_valid():
                        recibo = ReciboCaja(valor=f.cleaned_data['valor'],
                                        persona=f.cleaned_data['persona'],
                                        concepto=f.cleaned_data['concepto'],
                                        sesion=sesion_caja,
                                        hora=hora_actual)
                        recibo.save()

                        # Log de CREACION DE RECIBO DE CAJA
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(recibo).pk,
                            object_id       = recibo.id,
                            object_repr     = force_str(recibo),
                            action_flag     = ADDITION,
                            change_message  = 'Adicionado Recibo de Caja')
                    else:
                        return HttpResponseRedirect("/recibo_caja?action=add")
                else:
                    return HttpResponseRedirect("/recibo_caja?action=add&sesion=1")
            else:
                return HttpResponseRedirect("/recibo_caja?action=add&error=1")

        elif action=='edit':
            recibo = ReciboCaja.objects.get(pk=request.POST['id'])
            caja = request.session['persona'].lugarrecaudacion_set.get()
            sesion_caja = caja.sesion_caja()
            hora_actual=datetime.now().time()
            f = ReciboCajaForm(request.POST)
            if f.is_valid():
                recibo.valor=f.cleaned_data['valor']
                recibo.persona=f.cleaned_data['persona']
                recibo.concepto=f.cleaned_data['concepto']
                recibo.sesion=sesion_caja
                recibo.hora=hora_actual

                recibo.save()

                # Log de EDICION DE RECIBO DE CAJA
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(recibo).pk,
                    object_id       = recibo.id,
                    object_repr     = force_str(recibo),
                    action_flag     = CHANGE,
                    change_message  = 'Editado Recibo de Caja')
            else:
                return HttpResponseRedirect("/vale_caja?action=edit&id"+str(recibo.id))

        return HttpResponseRedirect("/recibo_caja")

    else:
        data = {'title': 'Listado de Recibos de Caja'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='add':
                error = None
                sesion = None
                if 'error' in request.GET:
                    error = request.GET['error']
                if 'sesion' in request.GET:
                    sesion = request.GET['sesion']
                data['title'] = 'Adicionar Recibo de Caja'
                data['form'] = ReciboCajaForm()
                data['error'] = error
                data['sesion'] = sesion
                return render(request ,"recibo_caja/adicionarbs.html" ,  data)
            elif action=='edit':
                data['title'] = 'Editar Recibo de Caja'
                recibo = ReciboCaja.objects.get(pk=request.GET['id'])
                initial = model_to_dict(recibo)
                data['form'] = ReciboCajaForm(initial=initial)
                data['recibo'] = recibo
                return render(request ,"recibo_caja/editarbs.html" ,  data)
        else:
            search = None
            if 's' in request.GET:
                search = request.GET['s']
            if search:
                recibos = ReciboCaja.objects.filter(Q(valor__icontains=search) | Q(persona__icontains=search) | Q(sesion__caja__persona__nombres__icontains=search)| Q(sesion__caja__persona__apellido1__icontains=search)| Q(sesion__caja__persona__apellido2__icontains=search)).order_by('-sesion__fecha','-hora')
            else:
                recibos = ReciboCaja.objects.all().order_by('-sesion__fecha','-hora')
            paging = Paginator(recibos, 50)
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
            data['recibos'] = page.object_list
            data['puede_cobrar'] = data['persona'].puede_recibir_pagos()
            return render(request ,"recibo_caja/recibosbs.html" ,  data)
