#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
from datetime import datetime, date
import json
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models.query_utils import Q
from django.http import  HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template.context import RequestContext
import requests
from decorators import secure_module
from settings import DEFAULT_PASSWORD, NEW_PASSWORD, EMAIL_ACTIVE, ACTIVA_ADD_EDIT_AD, IP_SERVIDOR_API_DIRECTORY
from sga.commonviews import addUserData, cambio_clave_AD, add_usuario_AD
from sga.models import Persona,PuntoAtencion,AtencionCliente,TurnoCab,TurnoDet, VturnoVideo,TIPOS_VISOR,REPOSITORIO, TipoIncidencia
from sga.tasks import send_html_mail


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
                punto = PuntoAtencion(
                        punto = request.POST['tit'],
                        horapunto=datetime.now(),
                        estadopunto=0
                        )
                punto.save()
                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            except:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
        if action=='edit':
            try:
                puntos=PuntoAtencion.objects.get(pk=request.POST['id'])
                puntos.punto = request.POST['tit']
                puntos.horapunto = datetime.now()
                puntos.save()
                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            except:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
        elif action=='act':
            try:
                if PuntoAtencion.objects.filter(pk=request.POST['id']).exists():
                    puntos = PuntoAtencion.objects.get(pk=request.POST['id'])
                    if(puntos.estadopunto):
                        puntos.estadopunto=0
                    else:
                        puntos.estadopunto=1
                    puntos.save()
                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            except:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
        elif action=='actu':
            try:
                if AtencionCliente.objects.filter(persona=request.POST['id']).exists():
                    usua=AtencionCliente.objects.get(persona=request.POST['id'])
                    if AtencionCliente.objects.filter(estado=True,puntoatencion=usua.puntoatencion).exclude(id=usua.id).exists():
                        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
                    if(usua.estado):
                        usua.estado=0
                    else:
                        usua.estado=1
                    usua.save()
                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            except:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
        elif action=='aad':
            try:
                pers=Persona.objects.get(pk=request.POST['uid'])
                if not AtencionCliente.objects.filter(persona__id=request.POST['uid']).exists():
                    atencion = AtencionCliente(
                            persona_id=pers.id,
                            puntoatencion_id=request.POST['pid'],
                            fechreg=datetime.now(),
                            estado=1
                            )
                    atencion.save()
                else:
                    atencion=AtencionCliente.objects.get(persona__id=request.POST['uid'])
                    atencion.puntoatencion_id=request.POST['pid']
                    atencion.fechreg=datetime.now()
                    atencion.estado=1
                    atencion.save()
                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            except:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
        elif action=='dell':
            try:
                if AtencionCliente.objects.filter(persona=request.POST['id'],turnocab=None).exists():
                    usua=AtencionCliente.objects.get(persona=request.POST['id'])
                    usua.delete()
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                else:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
            except:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
        elif action=='dellp':
            try:
                if PuntoAtencion.objects.filter(pk=request.POST['id'],atencioncliente=None).exists():
                    if AtencionCliente.objects.filter(puntoatencion=request.POST['id']).exists():
                        atencion=AtencionCliente.objects.get(puntoatencion=request.POST['id'])
                        atencion.delete()
                    usua=PuntoAtencion.objects.get(pk=request.POST['id'])
                    usua.delete()
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                else:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
            except:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

        #       GESTION DE VIDEO VIDEOS

        elif action=='addvid':
            try:
                ruta=request.POST['vid']
                for r in REPOSITORIO:
                    if int(request.POST['servi'])==r[0]:
                        ruta= r[2]+ruta+r[3]+ruta+r[4]
                        ancho = r[5]
                        alto = r[6]
                        code = r[7]

                video = VturnoVideo(
                            descripcion = request.POST['videsc'],
                            rutav = request.POST['vid'],
                            confv = ruta,
                            estado =False,
                            fechavideo =datetime.now(),
                            tipovista = request.POST['visor'],
                            repositorio = request.POST['servi'],
                            anchpor = ancho,
                            altopx = alto,
                            codec = code
                            )
                video.save()
                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            except:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

        elif action=='edivid':
            try:
                ruta=request.POST['vid']
                for r in REPOSITORIO:
                    if int(request.POST['servi'])==r[0]:
                        ruta= r[2]+ruta+r[3]+ruta+r[4]
                        ancho = r[5]
                        alto = r[6]
                        code = r[7]

                video = VturnoVideo.objects.get(pk=request.POST['id'])
                video.descripcion = str(request.POST['videsc'])
                video.rutav = str(request.POST['vid'])
                video.confv = str(ruta)
                video.tipovista = int(request.POST['visor'])
                video.repositorio = int(request.POST['servi'])
                video.anchpor = ancho
                video.altopx = alto
                video.codec = code

                video.save()

                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            except:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

        elif action=='dellv':
            try:
                if VturnoVideo.objects.filter(pk=request.POST['id']).exists():
                    video=VturnoVideo.objects.get(pk=request.POST['id'])
                    video.delete()
                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            except:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

        elif action=='acvid':
            try:
                if VturnoVideo.objects.filter(pk=request.POST['id']).exists():
                    video=VturnoVideo.objects.get(pk=request.POST['id'])
                    if(video.estado):
                        video.estado=0
                    else:
                        for x in VturnoVideo.objects.filter(tipovista=request.POST['depa']):
                            x.estado=0
                            x.save()
                        video=VturnoVideo.objects.get(pk=request.POST['id'])
                        video.estado=1

                    video.save()
                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            except:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")


        if action=='atender':
                try:
                    msj='Error Inesperado...'
                    idusr=Persona.objects.get(usuario=request.user).id
                    if AtencionCliente.objects.filter(persona=idusr).exists():
                        idturno=AtencionCliente.objects.get(persona=idusr)
                        if TurnoCab.objects.filter(fechatiket=datetime.now(),AtencionCliente=idturno.id).exists():
                            if TurnoDet.objects.filter(horatiket=datetime.now(),atendido=False).exists():
                               turnocab=TurnoCab.objects.get(fechatiket=datetime.now(),AtencionCliente=idturno.id)
                               total=turnocab.totaltiket+1
                               turnocab.totaltiket=total
                               turnocab.save()
                               turno = TurnoDet.objects.filter(horatiket=datetime.now(),atendido=False).order_by('id')[:1].get()
                               turno.TurnoCab=turnocab
                               turno.atendido=True
                               turno.horatiende=datetime.now()
                               turno.save()
                               msj='Turno      : '+str(turno.tiket)
                            else:
                               msj='No Quedan Turnos por Atender'
                        else:
                            if TurnoDet.objects.filter(horatiket=datetime.now(),atendido=False).exists():
                               turno = TurnoDet.objects.filter(horatiket=datetime.now(),atendido=False).order_by('id')[:1].get()
                               turnocab = TurnoCab(
                                   AtencionCliente_id = idturno.id,
                                   fechatiket = datetime.now(),
                                   totaltiket = 1
                               )
                               turnocab.save()
                               turno.TurnoCab=turnocab
                               turno.atendido=True
                               turno.horatiende=datetime.now()
                               turno.save()
                               msj='Turno      : '+str(turno.tiket)
                            else:
                               msj='No Quedan Turnos por Atender'

                    return HttpResponse(json.dumps({"result":"ok","msjs":msj}),content_type="application/json")
                except Exception as e:

                    return HttpResponse(json.dumps({"result":"bad","msjs":msj+" " + str(e) }),content_type="application/json")
    else:
        data = {'title': 'Listado de puntos de atencion'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='atender':
                try:
                    bandera=0
                    msj='Error Inesperado...'
                    idusr=Persona.objects.get(usuario=request.user).id
                    if AtencionCliente.objects.filter(persona=idusr).exists():

                        idturno=AtencionCliente.objects.get(persona=idusr)
                        if TurnoCab.objects.filter(fechatiket=datetime.now(),AtencionCliente=idturno.id).exists():
                            if TurnoDet.objects.filter(horatiket=datetime.now(),atendido=False).exists():
                                turnocab=TurnoCab.objects.get(fechatiket=datetime.now(),AtencionCliente=idturno.id)
                                total=turnocab.totaltiket+1
                                turnocab.totaltiket=total
                                turnocab.save()

                                turno = TurnoDet.objects.filter(horatiket=datetime.now(),atendido=False).order_by('id')[:1].get()
                                turno.TurnoCab=turnocab
                                turno.atendido=True
                                turno.horatiende=datetime.now()
                                turno.save()
                                bandera=1
                                msj='Turno      : '+str(turno.tiket)
                            else:
                                msj='No Quedan Turnos por Atender'
                        else:

                            if TurnoDet.objects.filter(horatiket=datetime.now(),atendido=False).exists():
                                turno = TurnoDet.objects.filter(horatiket=datetime.now(),atendido=False).order_by('id')[:1].get()
                                turnocab = TurnoCab(
                                    AtencionCliente_id = idturno.id,
                                    fechatiket = datetime.now(),
                                    totaltiket = 1
                                )
                                turnocab.save()
                                turno.TurnoCab=turnocab
                                turno.atendido=True
                                turno.horatiende=datetime.now()
                                turno.save()
                                bandera=1
                                msj='Turno      : '+str(turno.tiket)
                            else:
                                msj='No Quedan Turnos por Atender'

                    return HttpResponseRedirect('/?info='+msj+'&ban='+str(bandera))
                except Exception as ex:
                    return HttpResponseRedirect('/?info='+msj+" "+ str(ex)+'&ban=1'+str(bandera))

            if action=='video':
                search = None
                todos = None
                activos = None
                inactivos = None
                if 's' in request.GET:
                    search = request.GET['s']
                if 'a' in request.GET:
                    activos = request.GET['a']
                if 'i' in request.GET:
                    inactivos = request.GET['i']
                if 't' in request.GET:
                    todos = request.GET['t']
                if search:
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')
                    if len(ss)==1:
                        video = VturnoVideo.objects.filter(Q(rutav__icontains=search) | Q(descripcion__icontains=search)).order_by('descripcion')
                    else:
                        video = VturnoVideo.objects.filter(Q(rutav__icontains=ss[0]) & Q(descripcion__icontains=ss[1])).order_by('descripcion')
                else:
                   video = VturnoVideo.objects.all().order_by('descripcion')
                if todos:
                    video = VturnoVideo.objects.all().order_by('descripcion')
                paging = Paginator(video, 60)
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
                data['repos'] = REPOSITORIO
                data['visor'] = TIPOS_VISOR
                data['video'] = page.object_list
                return render(request ,"atencioncliente/videoturno.html" ,  data)

            if action=='punto':
                search = None
                todos = None
                activos = None
                inactivos = None
                if 's' in request.GET:
                    search = request.GET['s']
                if 'a' in request.GET:
                    activos = request.GET['a']
                if 'i' in request.GET:
                    inactivos = request.GET['i']
                if 't' in request.GET:
                    todos = request.GET['t']
                if search:
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')
                    if len(ss)==1:
                        puntos = PuntoAtencion.objects.filter(Q(punto__icontains=search) | Q(horapunto__icontains=search)).order_by('horapunto')
                    else:
                        puntos = PuntoAtencion.objects.filter(Q(punto__icontains=ss[0]) & Q(horapunto__icontains=ss[1])).order_by('punto','horapunto')
                else:
                   puntos = PuntoAtencion.objects.all().order_by('punto')
                if todos:
                    puntos = PuntoAtencion.objects.all().order_by('punto')
                paging = Paginator(puntos, 60)
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
                data['puntos'] = page.object_list
                return render(request ,"atencioncliente/atencionpuntos.html" ,  data)

            # elif action=='dell':
            #     data['title'] = 'Resetear Clave del Usuario'
            #     p = Persona.objects.get(pk=int(request.GET['id']))
            #     user = p.usuario
            #     user.set_password(DEFAULT_PASSWORD)
            #     user.save()
            #     return render(request ,"atencioncliente/atencionpuntos.html" ,  data)

            elif action=='point':
                data['title'] = 'Consulta de Puntos de Atencion'
                p = Persona.objects.get(pk=int(request.GET['id']))
                user = p.usuario
                if DEFAULT_PASSWORD == 'itb' and ACTIVA_ADD_EDIT_AD:
                    user.set_password(NEW_PASSWORD)
                    scriptresponse = ''
                    mensajesc = ''
                    listnombre = []
                    try:
                        datos = {"identity": user.username,
                         "NewPassword": NEW_PASSWORD}
                        consulta = requests.put(IP_SERVIDOR_API_DIRECTORY+'/changep',json.dumps(datos), verify=False,timeout=4)
                        if consulta.status_code == 200:
                            validacambio = True
                            datos = consulta.json()
                    except requests.Timeout:
                        print("Error Timeout")
                    except requests.ConnectionError:
                        print("Error Conexion")
                else:
                    user.set_password(DEFAULT_PASSWORD)
                    user.save()
                return render(request ,"atencioncliente/atencionpuntos.html" ,  data)

            elif action=='estadistica':
                data['title'] = 'Consulta Estadistica Puntos de Atencion'
                ini=datetime.now().date()
                fin=datetime.now().date()

                if 'inicio' in request.GET:
                    ini=request.GET['inicio']
                    ini=date(int(ini.split('-')[2]),int(ini.split('-')[1]),int(ini.split('-')[0]))


                if 'fin' in request.GET:
                    fin=request.GET['fin']
                    fin=date(int(fin.split('-')[2]),int(fin.split('-')[1]),int(fin.split('-')[0]))

                data['fechai'] = ini
                data['fechaf'] = fin
                data['graficos'] = AtencionCliente.objects.filter(id__in=TurnoCab.objects.filter(fechatiket__gte=ini,fechatiket__lte=fin).values('AtencionCliente').distinct('AtencionCliente'))
                return render(request ,"atencioncliente/reportgrafico.html" ,  data)

        else:
            search = None
            todos = None
            activos = None
            inactivos = None
            if 's' in request.GET:
                search = request.GET['s']
            if 'a' in request.GET:
                activos = request.GET['a']
            if 'i' in request.GET:
                inactivos = request.GET['i']
            if 't' in request.GET:
                todos = request.GET['t']

            if search:
                ss = search.split(' ')
                while '' in ss:
                    ss.remove('')
                if len(ss)==1:
                    administrativos = Persona.objects.filter(Q(Q(nombres__icontains=search) | Q(apellido1__icontains=search) | Q(apellido2__icontains=search) | Q(cedula__icontains=search) | Q(pasaporte__icontains=search)),usuario__groups__id__in=(17,0)).order_by('apellido1')
                else:
                    administrativos = Persona.objects.filter(Q(apellido1__icontains=ss[0]) & Q(apellido2__icontains=ss[1])).filter(usuario__groups__id__in=(17,0)).order_by('apellido1','apellido2','nombres')
            else:
                administrativos = Persona.objects.filter(usuario__groups__id__in=(17,0)).order_by('apellido1')

            if todos:
                administrativos = Persona.objects.filter(usuario__groups__id__in=(17,0)).order_by('apellido1')

            administrativos = administrativos.exclude(usuario=None)
            punto=PuntoAtencion.objects.filter(estadopunto=True).exclude(id__in=AtencionCliente.objects.filter(estado=True).values('puntoatencion')).order_by('punto')

            paging = Paginator(administrativos, 50)
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
            data['administrativos'] = page.object_list
            data['puntos'] = punto
            return render(request ,"atencioncliente/atencioncliente.html" ,  data)
