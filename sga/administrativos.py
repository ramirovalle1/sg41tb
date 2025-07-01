#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
from datetime import datetime
import json
from django.contrib.admin.models import LogEntry, ADDITION, DELETION, CHANGE

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models.query_utils import Q
from django.forms.models import model_to_dict
from django.http import  HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template.context import RequestContext
from django.utils.encoding import force_str
import requests
from decorators import secure_module
from settings import DEFAULT_PASSWORD, PROFESORES_GROUP_ID, ADMINISTRATIVOS_GROUP_ID, ALUMNOS_GROUP_ID, SISTEMAS_GROUP_ID, CENTRO_EXTERNO, USA_CORREO_INSTITUCIONAL, CORREO_INSTITUCIONAL, NEW_PASSWORD, EMAIL_ACTIVE, ACTIVA_ADD_EDIT_AD, IP_SERVIDOR_API_DIRECTORY
from sga.commonviews import addUserData, ip_client_address, cambio_clave_AD, add_usuario_AD
from sga.forms import AdministrativosForm, ProfesorEstudiosCursaForm, TitulacionProfesorForm
from sga.models import Persona, AdministrativoEstudiosCursa, TitulacionAdministrativo, SubAreaConocimiento, TipoIncidencia
from suds.client import Client
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
            f = AdministrativosForm(request.POST)
            if f.is_valid():
                cedula=f.cleaned_data['cedula']
                persona = Persona(nombres=f.cleaned_data['nombres'],
                                apellido1=f.cleaned_data['apellido1'],
                                apellido2=f.cleaned_data['apellido2'],
                                extranjero=f.cleaned_data['extranjero'],
                                cedula=cedula,
                                pasaporte=f.cleaned_data['pasaporte'],
                                nacimiento=f.cleaned_data['nacimiento'],
                                provincia=f.cleaned_data['provincia'],
                                canton=f.cleaned_data['canton'],
                                sexo=f.cleaned_data['sexo'],
                                nacionalidad=f.cleaned_data['nacionalidad'],
                                madre=f.cleaned_data['madre'],
                                padre=f.cleaned_data['padre'],
                                direccion=f.cleaned_data['direccion'],
                                direccion2=f.cleaned_data['direccion2'],
                                num_direccion=f.cleaned_data['num_direccion'],
                                sector = f.cleaned_data['sector'],
                                provinciaresid = f.cleaned_data['provinciaresid'],
                                cantonresid = f.cleaned_data['cantonresid'],
                                ciudad = f.cleaned_data['ciudad'],
                                telefono=f.cleaned_data['telefono'],
                                telefono_conv=f.cleaned_data['telefono_conv'],
                                email=f.cleaned_data['email'],
                                sangre=f.cleaned_data['sangre'],
                                parroquia=f.cleaned_data['parroquia'])
                persona.save()

                username = calculate_username(persona)
                password = DEFAULT_PASSWORD
                user = User.objects.create_user(username, persona.email, password)
                user.save()
                persona.usuario = user
                persona.save()

                grupos = f.cleaned_data['grupos']       #Grupos de Usuarios escogidos
                for g in grupos:
                    g.user_set.add(persona.usuario)         #Asignar al usuario a los nuevos grupos
                    g.save()

                if USA_CORREO_INSTITUCIONAL:
                    persona.emailinst = user.username + '' + CORREO_INSTITUCIONAL
                else:
                    persona.emailinst = ''

                persona.save()

                #Comprobar si es discapacitado, en caso de serlo llenar modelo PersonaDatosMatriz
                pdm = persona.datos_matriz()
                if f.cleaned_data['tienediscapacidad']==True:
                    pdm.tienediscapacidad = True
                    pdm.tipodiscapacidad = f.cleaned_data['tipodiscapacidad']
                    pdm.porcientodiscapacidad = f.cleaned_data['porcientodiscapacidad']
                    pdm.carnetdiscapacidad = f.cleaned_data['carnetdiscapacidad']
                else:
                    pdm.tienediscapacidad = False
                    pdm.tipodiscapacidad = None
                    pdm.porcientodiscapacidad = 0
                    pdm.carnetdiscapacidad = ''

                pdm.numerocontrato = f.cleaned_data['numerocontrato']
                pdm.save()

                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de ADICIONAR ADMINISTRATIVO
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(persona).pk,
                    object_id       = persona.id,
                    object_repr     = force_str(persona),
                    action_flag     = ADDITION,
                    change_message  = 'Adicionado Personal Administrativo ' + client_address +')'  )

                if persona.cedula:
                    return HttpResponseRedirect("/administrativos?s="+str(persona.cedula))
                else:
                    return HttpResponseRedirect("/administrativos?s="+str(persona.pasaporte))

            else:
                return HttpResponseRedirect("/administrativos?action=add")

        elif action=='edit':
            per = Persona.objects.get(pk=request.POST['id'])
            f = AdministrativosForm(request.POST)
            if f.is_valid():
                per.nombres=f.cleaned_data['nombres']
                per.apellido1=f.cleaned_data['apellido1']
                per.apellido2=f.cleaned_data['apellido2']
                per.extranjero=f.cleaned_data['extranjero']
                per.cedula=f.cleaned_data['cedula']
                per.pasaporte=f.cleaned_data['pasaporte']
                per.nacimiento=f.cleaned_data['nacimiento']
                per.provincia=f.cleaned_data['provincia']
                per.canton=f.cleaned_data['canton']
                per.sexo=f.cleaned_data['sexo']
                per.nacionalidad=f.cleaned_data['nacionalidad']
                per.madre=f.cleaned_data['madre']
                per.padre=f.cleaned_data['padre']
                per.direccion=f.cleaned_data['direccion']
                per.direccion2=f.cleaned_data['direccion2']
                per.num_direccion=f.cleaned_data['num_direccion']
                per.sector=f.cleaned_data['sector']
                per.provinciaresid=f.cleaned_data['provinciaresid']
                per.cantonresid=f.cleaned_data['cantonresid']
                per.ciudad=f.cleaned_data['ciudad']
                per.telefono=f.cleaned_data['telefono']
                per.telefono_conv=f.cleaned_data['telefono_conv']
                per.email=f.cleaned_data['email']
                per.sangre=f.cleaned_data['sangre']
                per.parroquia=f.cleaned_data['parroquia']
                per.save()

                grupos = f.cleaned_data['grupos']       #Grupos de Usuarios escogidos
                usuario = per.usuario
                usuario.groups.clear()
                for g in grupos:
                    g.user_set.add(usuario)         #Asignar al usuario a los nuevos grupos
                    g.save()

                #Comprobar si es discapacitado, en caso de serlo llenar modelo PersonaDatosMatriz
                pdm = per.datos_matriz()
                if f.cleaned_data['tienediscapacidad']==True:
                    pdm.tienediscapacidad = True
                    pdm.tipodiscapacidad = f.cleaned_data['tipodiscapacidad']
                    pdm.porcientodiscapacidad = f.cleaned_data['porcientodiscapacidad']
                    pdm.carnetdiscapacidad = f.cleaned_data['carnetdiscapacidad']
                else:
                    pdm.tienediscapacidad = False
                    pdm.tipodiscapacidad = None
                    pdm.porcientodiscapacidad = 0
                    pdm.carnetdiscapacidad = ''

                pdm.numerocontrato = f.cleaned_data['numerocontrato']
                pdm.save()

                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de MODIFICAR ADMINISTRATIVO
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(per).pk,
                    object_id       = per.id,
                    object_repr     = force_str(per),
                    action_flag     = CHANGE,
                    change_message  = 'Modificado Personal Administrativo ' + client_address +')'  )

                if per.cedula:
                    return HttpResponseRedirect("/administrativos?s="+str(per.cedula))
                else:
                    return HttpResponseRedirect("/administrativos?s="+str(per.pasaporte))

            else:
                return HttpResponseRedirect("/administrativos?action=edit&id="+str(per.id))

        elif action=='addestudiocursa':
            f = ProfesorEstudiosCursaForm(request.POST)
            persona = Persona.objects.get(pk=request.POST['id'])
            if f.is_valid():
                administrativoestudio = AdministrativoEstudiosCursa(administrativo=persona,
                                                        inicio=f.cleaned_data['inicio'],
                                                        tipoestudio=f.cleaned_data['tipoestudio'],
                                                        financiado=f.cleaned_data['financiado'])
                administrativoestudio.save()

                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de ADICIONAR ESTUDIOS ADMINISTRATIVOS
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(administrativoestudio).pk,
                    object_id       = administrativoestudio.id,
                    object_repr     = force_str(administrativoestudio),
                    action_flag     = ADDITION,
                    change_message  = 'Adicionado Estudio Cursando el Administrativo ' + client_address +')'  )

                return HttpResponseRedirect("/administrativos?action=estudioscursa&id="+str(persona.id))
            else:
                return HttpResponseRedirect("/administrativos?action=addestudiocursa&id="+str(persona.id))

        elif action=='delestudiocursa':
            estudio = AdministrativoEstudiosCursa.objects.get(pk=request.POST['id'])
            persona = estudio.administrativo

            #Obtain client ip address
            client_address = ip_client_address(request)

            # Log de ELIMINACION DE ESTUDIOS QUE CURSA EL DOCENTE
            LogEntry.objects.log_action(
                user_id         = request.user.pk,
                content_type_id = ContentType.objects.get_for_model(estudio).pk,
                object_id       = estudio.id,
                object_repr     = force_str(estudio),
                action_flag     = DELETION,
                change_message  = 'Eliminado Estudio que cursa el Administrativo (' + client_address + ')')

            estudio.delete()

            return HttpResponseRedirect("/administrativos?action=estudioscursa&id="+str(persona.id))

        elif action=='areaconocimiento':
            subarea = SubAreaConocimiento.objects.get(pk=request.POST['subarea'])
            return HttpResponse(json.dumps({"result": "ok", "areaconocimiento": subarea.area.nombre }),content_type="application/json")

        elif action == 'addtitulacion':
            administrativo = Persona.objects.get(pk=request.POST['id'])
            f = TitulacionProfesorForm(request.POST)
            if f.is_valid():
                administrativotitulacion = TitulacionAdministrativo(administrativo=administrativo,
                                                        titulo=f.cleaned_data['titulo'],
                                                        nivel=f.cleaned_data['nivel'],
                                                        tiponivel=f.cleaned_data['tiponivel'],
                                                        pais=f.cleaned_data['pais'],
                                                        institucion=f.cleaned_data['institucion'],
                                                        fecha=f.cleaned_data['fecha'],
                                                        registro=f.cleaned_data['registro'],
                                                        codigoprofesional=f.cleaned_data['codigoprofesional'],
                                                        subarea=f.cleaned_data['subarea'])
                administrativotitulacion.save()
                return HttpResponseRedirect("/administrativos?action=titulacion&id=" + str(administrativo.id))
            else:
                return HttpResponseRedirect("/administrativos?action=addtitulacion&id=" + str(administrativo.id))

        elif action == 'edittitulacion':
            titulacion = TitulacionAdministrativo.objects.get(pk=request.POST['id'])
            f = TitulacionProfesorForm(request.POST)
            if f.is_valid():
                titulacion.titulo = f.cleaned_data['titulo']
                titulacion.nivel = f.cleaned_data['nivel']
                titulacion.tiponivel = f.cleaned_data['tiponivel']
                titulacion.pais = f.cleaned_data['pais']
                titulacion.fecha = f.cleaned_data['fecha']
                titulacion.institucion = f.cleaned_data['institucion']
                titulacion.registro = f.cleaned_data['registro']
                titulacion.codigoprofesional = f.cleaned_data['codigoprofesional']
                titulacion.subarea=f.cleaned_data['subarea']
                titulacion.save()
                return HttpResponseRedirect("/administrativos?action=titulacion&id=" + str(titulacion.administrativo_id))
            else:
                return HttpResponseRedirect("/administrativos?action=edittitulacion&id=" + str(request.POST['id']))

        elif action == 'deltitulacion':
            titulacion = TitulacionAdministrativo.objects.get(pk=request.POST['id'])
            administrativo = titulacion.administrativo
            titulacion.delete()
            return HttpResponseRedirect("/administrativos?action=titulacion&id=" + str(administrativo.id))


        return HttpResponseRedirect("/administrativos")
    else:
        data = {'title': 'Listado de personal administrativo'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='add':
                data['title'] = 'Adicionar personal administrativo'
                data['form'] = AdministrativosForm(initial={'nacimiento': datetime.now()})
                return render(request ,"administrativos/adicionarbs.html" ,  data)
            elif action=='activation':
                if Persona.objects.filter(pk=request.GET['id']).exists():
                    pe = Persona.objects.get(pk=request.GET['id'])
                    ui = pe.usuario
                    if ui.is_active:
                        ui.is_active = False
                    else:
                        ui.is_active = True
                    ui.save()

                    #Obtain client ip address
                    client_address = ip_client_address(request)
                    # Log de ACTIVACION DE PERSONAL ADMINISTRATIVO
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(pe).pk,
                        object_id       = pe.id,
                        object_repr     = force_str(pe),
                        action_flag     = CHANGE,
                        change_message  = 'Cambio de Estado de Personal a '+ str(pe.usuario.is_active) +' (' + client_address + ')')

                return HttpResponseRedirect("/administrativos")
            elif action=='edit':
                p = Persona.objects.get(pk=request.GET['id'])
                groups = p.usuario.groups.all()
                initial = model_to_dict(p)
                pdm = p.datos_matriz()
                initial.update(model_to_dict(pdm))
                initial.update({'grupos': groups})
                data['form'] = AdministrativosForm(initial=initial)
                data['administrativos'] = p
                return render(request ,"administrativos/editarbs.html" ,  data)
            elif action=='resetear':
                data['title'] = 'Resetear Clave del Usuario'
                p = Persona.objects.get(pk=int(request.GET['id']))
                user = p.usuario
                numdocment = p.cedula if p.cedula else p.pasaporte
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
                            user.save()
                            datos = consulta.json()
                    except requests.Timeout:
                        print("Error Timeout")

                    except requests.ConnectionError:
                        print("Error Conexion")

                else:
                    user.set_password(DEFAULT_PASSWORD)
                    user.save()
                return HttpResponseRedirect("/administrativos?s="+numdocment)

            elif action=='estudioscursa':
                data['title'] = 'Estudios que cursa el Administrativo'
                persona = Persona.objects.get(pk=request.GET['id'])
                persona2 = Persona.objects.get(usuario=request.user)
                data['persona'] = persona
                data['persona2'] = persona2
                data['cursandoestudios'] = persona.administrativoestudioscursa_set.all()
                return render(request ,"administrativos/estudioscursa.html" ,  data)

            elif action=='addestudiocursa':
                data['title'] = 'Adicionar Estudios que cursa el Administrativo'
                persona = Persona.objects.get(pk=request.GET['id'])
                data['persona'] = persona
                form = ProfesorEstudiosCursaForm(initial={'inicio': datetime.today()})
                data['form'] = form
                return render(request ,"administrativos/estudiocursaadd.html" ,  data)

            elif action=='delestudiocursa':
                data['title'] = 'Eliminar Estudio que cursa el Administrativo'
                data['estudio'] = AdministrativoEstudiosCursa.objects.get(pk=request.GET['id'])
                return render(request ,"administrativos/estudiocursadel.html" ,  data)

            elif action == 'titulacion':
                data['title'] = 'Titulos del Administrativo'
                administrativo = Persona.objects.get(pk=request.GET['id'])
                data['administrativo'] = administrativo
                return render(request ,"administrativos/titulacionbs.html" ,  data)

            if action == 'addtitulacion':
                data['title'] = 'Adicionar Titulacion del Administrativo'
                administrativo = Persona.objects.get(pk=request.GET['id'])
                data['administrativo'] = administrativo
                form = TitulacionProfesorForm(initial={'fecha': datetime.now()})
                data['form'] = form
                return render(request ,"administrativos/adicionartitulacionbs.html" ,  data)

            elif action == 'edittitulacion':
                data['title'] = 'Editar Titulacion del Administrativo'
                titulacion = TitulacionAdministrativo.objects.get(pk=request.GET['id'])
                data['administrativo'] = titulacion.administrativo
                initial = model_to_dict(titulacion)
                form = TitulacionProfesorForm(initial=initial)
                data['form'] = form
                data['titulacion'] = titulacion
                return render(request ,"administrativos/editartitulacionbs.html" ,  data)
            elif action =='probar':
                import subprocess
                try:
                    subprocess.call(["php", "creacionAD.php"])
                    proc = subprocess.Popen("creacionAD.php", shell=True, stdout=subprocess.PIPE)
                    script_response = proc.stdout.read()
                    print(script_response)
                except Exception as e:
                    print(e)

            elif action == 'deltitulacion':
                data['title'] = 'Borrar Titulacion del Administrativo'
                titulacion = TitulacionAdministrativo.objects.get(pk=request.GET['id'])
                data['titulacion'] = titulacion
                data['administrativo'] = titulacion.administrativo
                return render(request ,"administrativos/borrartitulacionbs.html" ,  data)

        else:

            search = None
            todos = None
            activos = None
            inactivos = None
            gruposexcluidos = [PROFESORES_GROUP_ID,ALUMNOS_GROUP_ID,SISTEMAS_GROUP_ID]

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
                    administrativos = Persona.objects.filter(Q(nombres__icontains=search) | Q(apellido1__icontains=search) | Q(apellido2__icontains=search) | Q(cedula__icontains=search) | Q(pasaporte__icontains=search)).exclude(usuario__groups__id__in=gruposexcluidos).order_by('apellido1')
                else:
                    administrativos = Persona.objects.filter(Q(apellido1__icontains=ss[0]) & Q(apellido2__icontains=ss[1])).exclude(usuario__groups__id__in=gruposexcluidos).order_by('apellido1','apellido2','nombres')
            else:
                administrativos = Persona.objects.filter().exclude(usuario__groups__id__in=gruposexcluidos).order_by('apellido1')

            if todos:
                administrativos = Persona.objects.filter().exclude(usuario__groups__id__in=gruposexcluidos).order_by('apellido1')

            administrativos = administrativos.exclude(usuario=None)

            paging = Paginator(administrativos, 60)
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
            data['clave'] = DEFAULT_PASSWORD if not ACTIVA_ADD_EDIT_AD else NEW_PASSWORD
            data['centroexterno'] = CENTRO_EXTERNO
            if 'error' in request.GET:
                data['error'] = request.GET['error']
            return render(request ,"administrativos/administrativosbs.html" ,  data)
