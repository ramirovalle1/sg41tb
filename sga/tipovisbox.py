#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
from datetime import datetime, date
import json
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models.query_utils import Q
from django.http import  HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template.context import RequestContext
from django.utils.encoding import force_str
from decorators import secure_module
from settings import DEFAULT_PASSWORD
from sga.commonviews import addUserData, ip_client_address
from sga.models import Persona,PuntoAtencion,AtencionCliente,TurnoCab,TurnoDet,TipoVisitasBox,Aula, TipoAtencionBox
# from sga.forms import  PrecioForm
from decimal import Decimal
from django.contrib.contenttypes.models import ContentType


def calculate_username(persona, variant = 1):
    s = persona.nombres.lower().split(' ')
    while '' in s:
        s.remove('')

    if len(s)>1:
        usernamevariant = s[0][0] + s[1][0] + persona.apellido1.lower()
    else:
        usernamevariant = s[0][0] + persona.apellido1.lower()
    usernamevariant = usernamevariant.replace(' ','').replace(u'Ñ','n').replace(u'ñ','n')

    if variant>1:
        usernamevariant = usernamevariant+str(variant)
    import psycopg2
    db = psycopg2.connect("host=10.10.9.45 dbname=sgaonline user=postgres password=Itb$2019")
    cursor = db.cursor()
    cursor.execute("select * from auth_user where username='" + str(usernamevariant) + "'")
    dato = cursor.fetchall()
    # names = [row[0] for row in cursor.fetchall()]
    db.close()
    if len(dato) > 0:
        return calculate_username(persona, variant + 1)
    db = psycopg2.connect("host=10.10.9.45 dbname=conduccion user=postgres password=Itb$2019")
    cursor = db.cursor()
    cursor.execute("select * from auth_user where username='" + str(usernamevariant) + "'")
    dato = cursor.fetchall()
    # names = [row[0] for row in cursor.fetchall()]
    db.close()
    if len(dato) > 0:
        return calculate_username(persona, variant + 1)
    db = psycopg2.connect("host=10.10.9.45 dbname=contable2 user=postgres password=Itb$2019")
    cursor = db.cursor()
    cursor.execute("select * from auth_user where username='" + str(usernamevariant) + "'")
    dato = cursor.fetchall()
    # names = [row[0] for row in cursor.fetchall()]
    db.close()
    if len(dato) > 0:
        return calculate_username(persona, variant + 1)
    db = psycopg2.connect("host=10.10.9.45 dbname=educacontinua user=postgres password=Itb$2019")
    cursor = db.cursor()
    cursor.execute("select * from auth_user where username='" + str(usernamevariant) + "'")
    dato = cursor.fetchall()
    # names = [row[0] for row in cursor.fetchall()]
    db.close()
    if len(dato) > 0:
        return calculate_username(persona, variant + 1)
    if User.objects.filter(username=usernamevariant).count()==0:
        return usernamevariant
    else:
        return calculate_username(persona, variant+1)

@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    if request.method=='POST':
        action = request.POST['action']
        if action=='add':
            try:
                tvisita = TipoVisitasBox(
                        descripcion = request.POST['desc'],
                        valida_deuda = False,
                        valida_retiro = False,
                        alias = request.POST['alias'],
                        visor = request.POST['visor'],
                        estado = False
                        )
                tvisita.save()
                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            except:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
        if action=='edit':
            try:
                tvbox=TipoVisitasBox.objects.get(pk=request.POST['id'])
                tvbox.alias = request.POST['alias']
                tvbox.visor = request.POST['visor']
                tvbox.estado= False
                tvbox.save()
                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            except:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
        elif action=='act':
            try:
                if TipoVisitasBox.objects.filter(pk=request.POST['id']).exists():
                    tvisita = TipoVisitasBox.objects.get(pk=request.POST['id'])
                    if(tvisita.estado):
                        tvisita.estado=0
                    else:
                        tvisita.estado=1
                    tvisita.save()
                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            except:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
        elif action=='actd':
            try:
                if TipoVisitasBox.objects.filter(pk=request.POST['id']).exists():
                    tvisita = TipoVisitasBox.objects.get(pk=request.POST['id'])
                    if(tvisita.valida_deuda):
                        tvisita.valida_deuda=0
                    else:
                        tvisita.valida_deuda=1
                    tvisita.save()
                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            except:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
        elif action=='actr':
            try:
                if TipoVisitasBox.objects.filter(pk=request.POST['id']).exists():
                    tvisita = TipoVisitasBox.objects.get(pk=request.POST['id'])
                    if(tvisita.valida_retiro):
                        tvisita.valida_retiro=0
                    else:
                        tvisita.valida_retiro=1
                    tvisita.save()
                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            except:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

    else:
        data = {'title': 'Listado de puntos de atencion'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='atender':
                bandera=0
            
        else:
            search = None
            todos = None
            activos = None
            inactivos = None
            tipovisbox = TipoVisitasBox.objects.all()
            sede = 0
            client_address = ip_client_address(request)
            if Aula.objects.filter(ip=str(client_address),activa=False).exists():
                sede = Aula.objects.filter(ip=str(client_address),activa=False)[:1].get().sede.id
            if 's' in request.GET:
                search = request.GET['s']

            if search:
                ss = search.split(' ')
                while '' in ss:
                    ss.remove('')
                if len(ss)==1:
                    tipovisbox = TipoVisitasBox.objects.filter(Q(descripcion__icontains=search) | Q(alias__icontains=search)).order_by('descripcion')
                else:
                    tipovisbox = TipoVisitasBox.objects.filter(Q(descripcion__icontains=ss[0]) & Q(alias__icontains=ss[1])).order_by('descripcion','alias')

            if todos:
                tipovisbox = TipoVisitasBox.objects.all()

            paging = Paginator(tipovisbox, 50)
            p = 1
            try:
                if 'page' in request.GET:
                    p = int(request.GET['page'])
                page = paging.page(p)
            except:
                page = paging.page(1)

            data['paging'] = paging
            data['page'] = page
            data['search'] = search if search else ""
            data['todos'] = todos if todos else ""
            data['activos'] = activos if activos else ""
            data['inactivos'] = inactivos if inactivos else ""
            data['tipovisitabox'] = page.object_list
            # data['puntos'] = punto
            return render(request ,"visitabox/tipovisbox.html" ,  data)
