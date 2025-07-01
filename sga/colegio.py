import csv
from datetime import datetime, timedelta
import json
import os
import urllib
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Avg
from django.db.models.aggregates import Sum
from django.db import transaction
from django.db.models.query_utils import Q
from django.forms.models import model_to_dict
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.utils.encoding import force_str
from django.template import RequestContext
import sys
from decorators import secure_module
from sga.commonviews import addUserData, ip_client_address
from sga.forms import ColegioForm
from sga.models import Colegio
from sga.tasks import gen_passwd

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
        if action=='inscribir':
            pass

        elif action=='addcolegio':
                form = ColegioForm(request.POST, request.FILES)
                if form.is_valid():
                    colegio = Colegio(nombre=form.cleaned_data['nombre'],
                        provincia=form.cleaned_data['provincia'],
                        canton =form.cleaned_data['canton'],
                        tipo = form.cleaned_data['tipo'])
                    colegio.save()

                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de ADICIONAR COLEGIO
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(colegio).pk,
                        object_id       = colegio.id,
                        object_repr     = force_str(colegio),
                        action_flag     = ADDITION,
                        change_message  = 'Adicionado Colegio (' + client_address + ')' )

                    return HttpResponseRedirect("/inscripciones")

        elif action == 'modificacolegio':
            try:
                colegio =Colegio.objects.get(pk=request.POST['id'])
                nombre = request.POST['nombre']
                nombre = nombre.upper()

                if Colegio.objects.filter(nombre=nombre,provincia=int( request.POST['provincia']),canton=int(request.POST['canton']),tipo=int(request.POST['tipo'])).exists():
                    return HttpResponseRedirect("/colegio?action=modificacolegio&id="+str(colegio.id)+"&error= Colegio ya existe")
                else:
                    colegio.nombre=nombre
                    colegio.provincia_id=request.POST['provincia']
                    colegio.canton_id = request.POST['canton']
                    colegio.tipo_id=request.POST['tipo']
                    colegio.save()

                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de MODIFICAR COLEGIO
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(colegio).pk,
                        object_id       = colegio.id,
                        object_repr     = force_str(colegio),
                        action_flag     = CHANGE,
                        change_message  = 'Modificado Colegio (' + client_address + ')' )

                    return HttpResponseRedirect("/colegio?s="+colegio.nombre)

            except Exception as ex:
                return HttpResponseRedirect("/colegio?action=modificacolegio&id="+str(colegio.id)+"&error= Ocurrieron errores al Grabar.")

        elif action=='buscarcolegio':
            # OCastillo 28-oct-2016 verificar colegio antes de grabar
            col=request.POST['colegio']
            col =col.upper( )
            if Colegio.objects.filter(nombre=col,provincia=int(request.POST['provincia']),canton=int(request.POST['canton']),tipo=int(request.POST['tipo'])).exists():
               nombre=col
               return HttpResponse(json.dumps({"result":"bad","colegio":nombre}),content_type="application/json")
            else:
               return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")

        elif action=='eliminarcolegio':
            try:
                colegio = Colegio.objects.get(pk=request.POST['id'])
                colegio.delete()

                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de ELIMINAR COLEGIO
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(colegio).pk,
                    object_id       = colegio.id,
                    object_repr     = force_str(colegio),
                    action_flag     = DELETION,
                    change_message  = 'Eliminado Colegio (' + client_address + ')' )

                return HttpResponseRedirect("/colegio")

            except Exception as ex:
                return HttpResponseRedirect("/colegio")

    else:
        data = {'title': 'Listado de Colegios'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if  action == 'inscribir':
                return HttpResponseRedirect("/colegio")

            elif action=='addcolegio':
                    data['title'] = 'Adicionar Colegio'
                    form = ColegioForm()
                    data['form'] = form
                    return render(request ,"inscripciones/adicionar_colegio.html" ,  data)

            elif action=='buscarcolegio':
                # OCastillo 28-oct-2016 verificar colegio antes de grabar
                col=request.POST['nombre']
                col =col.upper( )
                if Colegio.objects.filter(nombre=col,provincia=int(request.POST['provincia']),canton=int(request.POST['canton']),tipo=int(request.POST['tipo'])).exists():
                   nombre=col
                   return HttpResponse(json.dumps({"result":"bad","colegio":nombre}),content_type="application/json")
                else:
                   return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")

            elif action=='modificacolegio':
                    data['title'] = 'Modificar Colegio'
                    colegio = Colegio.objects.get(pk=request.GET['id'])
                    data['colegio'] = colegio
                    initial = model_to_dict(colegio)
                    data['form'] = ColegioForm(initial=initial)
                    if 'error' in  request.GET:
                        data['error']=request.GET['error']
                    return render(request ,"inscripciones/modifica_colegio.html" ,  data)

            elif action=='eliminarcolegio':
                    data['title'] = 'Elimminar Colegio'
                    colegio = Colegio.objects.get(pk=request.GET['id'])
                    data['colegio'] = colegio
                    return render(request ,"inscripciones/borrar_colegio.html" ,  data)
        else:
            try:
                hoy = str(datetime.date(datetime.now()))
                search = None
                todos = None
                activos = None
                inactivos = None

                if 's' in request.GET:
                    search = request.GET['s']

                if 't' in request.GET:
                    todos = request.GET['t']
                if search:
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')
                    if len(ss)==1:
                        colegio = Colegio.objects.filter(nombre__icontains=search).order_by('nombre')
                    else:
                        colegio = Colegio.objects.filter(nombre__icontains=ss[0]).order_by('nombre')
                else:
                    colegio =Colegio.objects.filter().order_by('nombre')

                paging = MiPaginador(colegio, 30)
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
                data['colegio'] = page.object_list
                data['form'] = ColegioForm()
                return render(request ,"inscripciones/colegiosbs.html" ,  data)

            except Exception as e:
                return HttpResponseRedirect("/colegio")