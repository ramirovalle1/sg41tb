#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
from datetime import datetime,timedelta
import json
import requests
from sga.reportes import elimina_tildes
from django.contrib.admin.models import LogEntry, CHANGE, ADDITION, DELETION

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models.query_utils import Q
from django.forms.models import model_to_dict
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template.context import RequestContext
from django.utils.encoding import force_str
from sga.tasks import send_html_mail
from decorators import secure_module
from settings import DEFAULT_PASSWORD, PROFESORES_GROUP_ID, COEFICIENTE_PORCIENTO_IESS, UTILIZA_FICHA_MEDICA, USA_CORREO_INSTITUCIONAL, CORREO_INSTITUCIONAL, PROFE_PRACT_CONDUCCION,\
     INSCRIPCION_CONDUCCION, EMAIL_ACTIVE, TIPOSEGMENTO_TEORIA,COORDINACION_UASSS, NEW_PASSWORD, ACTIVA_ADD_EDIT_AD, TUTORES_GROUP_ID, IP_SERVIDOR_API_DIRECTORY
from sga.commonviews import addUserData, ip_client_address, cambio_clave_AD, add_usuario_AD
from sga.forms import ProfesorForm, TitulacionProfesorForm, CargarCVForm, RolPerfilProfesorForm, PersonalInstitucionGPForm, ProfesorLiquidacionForm, DocumentosProfesorForm,\
     ProfesorEstudiosCursaForm, HorasProfesorForm, CargarFotoForm, CargarFotoProfForm
from sga.models import Profesor, Persona, TitulacionProfesor, Clase, Sesion, CVPersona, RolPerfilProfesor, Carrera, ProfesorInstitucionGP, ProfesorLiquidacion, DocumentosProfesor, \
     Archivo, ProfesorEstudiosCursa, SubAreaConocimiento, ProfesorHorasActividades, FotoPersona, FotoPersonaProf, AnalisisEvaluacion, Materia, ProfesorMateria,LeccionGrupo, Coordinacion, MateriaRecepcionActaNotas, TipoIncidencia

def calculate_username(persona, variant=1):
    s = persona.nombres.lower().split(' ')
    while '' in s:
        s.remove('')
    if len(s) > 1:
        usernamevariant = s[0][0] + s[1][0] + elimina_tildes(persona.apellido1.lower())
    else:
        usernamevariant = s[0][0] + elimina_tildes(persona.apellido1.lower())
    usernamevariant = usernamevariant.replace(' ', '').replace(u'Ñ', 'n').replace(u'ñ', 'n')
    if variant > 1:
        usernamevariant += str(variant)
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
    if User.objects.filter(username=usernamevariant).count() == 0:
        return usernamevariant
    else:
        return calculate_username(persona, variant + 1)

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
def view(request):
    """

    :param request:
    :return:
    """
    if request.method == 'POST':
        action = request.POST['action']
        if action == 'add':
            f = ProfesorForm(request.POST)
            if f.is_valid():
                persona = Persona(nombres=f.cleaned_data['nombres'],
                                  apellido1=f.cleaned_data['apellido1'],
                                  apellido2=f.cleaned_data['apellido2'],
                                  extranjero=f.cleaned_data['extranjero'],
                                  cedula=f.cleaned_data['cedula'],
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
                                  sector=f.cleaned_data['sector'],
                                  provinciaresid=f.cleaned_data['provinciaresid'],
                                  cantonresid=f.cleaned_data['cantonresid'],
                                  ciudad=f.cleaned_data['ciudad'],
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
                if USA_CORREO_INSTITUCIONAL:
                    persona.emailinst = user.username + '' + CORREO_INSTITUCIONAL
                else:
                    persona.emailinst = ''
                persona.save()
                profesor = Profesor(persona=persona,
                                    activo=True,
                                    fechaingreso=f.cleaned_data['fechaingreso'],
                                    dedicacion=f.cleaned_data['dedicacion'],
                                    categoria=f.cleaned_data['categoria'],
                                    numerocontrato=f.cleaned_data['numerocontrato'],
                                    relaciontrab=f.cleaned_data['relaciontrab'],
                                    reemplazo=f.cleaned_data['reemplazo'],
                                    tutor=f.cleaned_data['tutor'],
                                    practicahospital=f.cleaned_data['practicahospital'])
                profesor.save()

                if INSCRIPCION_CONDUCCION:
                    profesor.identificador=f.cleaned_data['identificador']
                profesor.save()

                if profesor.tutor:
                    g = Group.objects.get(pk=TUTORES_GROUP_ID)
                else:
                    g = Group.objects.get(pk=PROFESORES_GROUP_ID)
                g.user_set.add(user)
                g.save()

                #Comprobar si es discapacitado
                if f.cleaned_data['tienediscapacidad']==True:
                    profesor.tienediscapacidad = f.cleaned_data['tienediscapacidad']
                    profesor.tipodiscapacidad = f.cleaned_data['tipodiscapacidad']
                    profesor.porcientodiscapacidad = f.cleaned_data['porcientodiscapacidad']
                    profesor.carnetdiscapacidad = f.cleaned_data['carnetdiscapacidad']
                else:
                    profesor.tienediscapacidad = False
                    profesor.tipodiscapacidad = None
                    profesor.porcientodiscapacidad = 0
                    profesor.carnetdiscapacidad = ''

                if f.cleaned_data['conhorario'] == True:
                    profesor.conhorario = True
                    profesor.horainicio = inicio
                    profesor.horafin = fin

                    # Obtain client ip address
                    client_address = ip_client_address(request)
                    # Log de Adicionar Horario a Profesor
                    LogEntry.objects.log_action(
                        user_id=request.user.pk,
                        content_type_id=ContentType.objects.get_for_model(profesor).pk,
                        object_id=profesor.id,
                        object_repr=force_str(profesor),
                        action_flag=CHANGE,
                        change_message='Adicionado horario a Profesor (' + client_address + ')')

                profesor.save()

                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de ADICIONAR PROFESOR
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(profesor).pk,
                    object_id       = profesor.id,
                    object_repr     = force_str(profesor),
                    action_flag     = CHANGE,
                    change_message  = 'Adicionado Profesor (' + client_address + ')')

                if profesor.persona.cedula:
                    return HttpResponseRedirect("/docentes?s="+str(profesor.persona.cedula))
                else:
                    return HttpResponseRedirect("/docentes?s="+str(profesor.persona.pasaporte))

            else:
                return HttpResponseRedirect("/docentes?action=add")

        elif action == 'edit':
            profesor = Profesor.objects.get(pk=request.POST['id'])
            f = ProfesorForm(request.POST)
            if f.is_valid():
                profesor.persona.nombres = f.cleaned_data['nombres']
                profesor.persona.apellido1 = f.cleaned_data['apellido1']
                profesor.persona.apellido2 = f.cleaned_data['apellido2']
                profesor.persona.extranjero = f.cleaned_data['extranjero']
                profesor.persona.cedula = f.cleaned_data['cedula']
                profesor.persona.pasaporte = f.cleaned_data['pasaporte']
                profesor.persona.nacimiento = f.cleaned_data['nacimiento']
                profesor.persona.provincia = f.cleaned_data['provincia']
                profesor.persona.canton = f.cleaned_data['canton']
                profesor.persona.sexo = f.cleaned_data['sexo']
                profesor.persona.nacionalidad = f.cleaned_data['nacionalidad']
                profesor.persona.madre = f.cleaned_data['madre']
                profesor.persona.padre = f.cleaned_data['padre']
                profesor.persona.direccion = f.cleaned_data['direccion']
                profesor.persona.direccion2 = f.cleaned_data['direccion2']
                profesor.persona.num_direccion = f.cleaned_data['num_direccion']
                profesor.persona.sector = f.cleaned_data['sector']
                profesor.persona.provinciaresid = f.cleaned_data['provinciaresid']
                profesor.persona.cantonresid = f.cleaned_data['cantonresid']
                profesor.persona.ciudad = f.cleaned_data['ciudad']
                profesor.persona.telefono = f.cleaned_data['telefono']
                profesor.persona.telefono_conv = f.cleaned_data['telefono_conv']
                profesor.persona.email = f.cleaned_data['email']
                # profesor.persona.emailinst = f.cleaned_data['emailinst']
                profesor.persona.sangre = f.cleaned_data['sangre']
                profesor.persona.parroquia = f.cleaned_data['parroquia']
                profesor.persona.save()
                profesor.fechaingreso = f.cleaned_data['fechaingreso']
                profesor.dedicacion = f.cleaned_data['dedicacion']
                profesor.categoria = f.cleaned_data['categoria']
                profesor.numerocontrato = f.cleaned_data['numerocontrato']
                profesor.relaciontrab = f.cleaned_data['relaciontrab']
                profesor.reemplazo = f.cleaned_data['reemplazo']
                profesor.tutor = f.cleaned_data['tutor']
                profesor.practicahospital = f.cleaned_data['practicahospital']
                # OCastillo 06/10/2014
                if INSCRIPCION_CONDUCCION:
                    profesor.identificador=f.cleaned_data['identificador']

                profesor.save()

                #Comprobar si es discapacitado
                if f.cleaned_data['tienediscapacidad']==True:
                    profesor.tienediscapacidad = True
                    profesor.tipodiscapacidad = f.cleaned_data['tipodiscapacidad']
                    profesor.porcientodiscapacidad = f.cleaned_data['porcientodiscapacidad']
                    profesor.carnetdiscapacidad = f.cleaned_data['carnetdiscapacidad']
                else:
                    profesor.tienediscapacidad = False
                    profesor.tipodiscapacidad = None
                    profesor.porcientodiscapacidad = 0
                    profesor.carnetdiscapacidad = ''

                if f.cleaned_data['horainicio'] and f.cleaned_data['conhorario']==True:
                    profesor.conhorario = True
                    profesor.horainicio = f.cleaned_data['horainicio']
                    profesor.horafin = f.cleaned_data['horafin']

                    # Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de EDITAR HORARIO PROFESOR
                    LogEntry.objects.log_action(
                        user_id=request.user.pk,
                        content_type_id=ContentType.objects.get_for_model(profesor).pk,
                        object_id=profesor.id,
                        object_repr=force_str(profesor),
                        action_flag=CHANGE,
                        change_message='Se ha realizado cambio de horario a docente  (' + client_address + ')')

                else:
                    profesor.conhorario = False

                    # Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de EDITAR HORARIO PROFESOR
                    LogEntry.objects.log_action(
                        user_id=request.user.pk,
                        content_type_id=ContentType.objects.get_for_model(profesor).pk,
                        object_id=profesor.id,
                        object_repr=force_str(profesor),
                        action_flag=CHANGE,
                        change_message='Se ha quitado horario a docente  (' + client_address + ')')

                profesor.save()

                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de EDITAR PROFESOR
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(profesor).pk,
                    object_id       = profesor.id,
                    object_repr     = force_str(profesor),
                    action_flag     = CHANGE,
                    change_message  = 'Editado Profesor (' + client_address + ')')

                if profesor.persona.cedula:
                    return HttpResponseRedirect("/docentes?s="+str(profesor.persona.cedula))
                else:
                    return HttpResponseRedirect("/docentes?s="+str(profesor.persona.pasaporte))
            else:
                return HttpResponseRedirect("/docentes?action=edit&id="+str(profesor.id))
        elif action == 'analisis':
            try:
                analisis  = AnalisisEvaluacion(profesor_id =request.POST['profesor'],
                                               periodo_id = request.POST['periodo'],
                                               observacion = request.POST['obs'])
                analisis.save()
                profesor = Profesor.objects.get(pk=request.POST['profesor'])
                if profesor.persona.cedula:
                    prof = profesor.persona.cedula
                else:
                    prof = profesor.persona.pasaporte

                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de EDITAR PROFESOR
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(profesor).pk,
                    object_id       = profesor.id,
                    object_repr     = force_str(profesor),
                    action_flag     = CHANGE,
                    change_message  = 'Adicionado Analisis de Evaluacion '+str(analisis.periodo) + ' (' + client_address + ')')

                return HttpResponse(json.dumps({"result": "ok", "profesor":prof  }),content_type="application/json")
            except :
                return HttpResponse(json.dumps({"result": "bad" }),content_type="application/json")

        elif action == 'addhorasprof':
            profesor = Profesor.objects.get(pk=request.POST['id'])
            f = HorasProfesorForm(request.POST)
            if f.is_valid():
                anno= f.cleaned_data['anno']
                if not ProfesorHorasActividades.objects.filter(profesor=profesor, anno=anno).exists():
                    # Adicionar Horas de actividades del docente
                    hp = ProfesorHorasActividades(profesor=profesor,
                                                  anno= f.cleaned_data['anno'],
                                                  horasded = f.cleaned_data['horasded'],
                                                  horasinv = f.cleaned_data['horasinv'],
                                                  horasvin = f.cleaned_data['horasvin'],
                                                  horasadm = f.cleaned_data['horasadm'],
                                                  horasotr = f.cleaned_data['horasotr'],
                                                  otrasactividades = f.cleaned_data['otrasactividades'])
                    hp.save()

                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de ADICIONAR HORAS DE ACTIVIDADES
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(hp).pk,
                        object_id       = hp.id,
                        object_repr     = force_str(hp),
                        action_flag     = ADDITION,
                        change_message  = 'Adicionadas Horas Profesor (' + client_address + ')')

                    return HttpResponseRedirect("/docentes?action=horasprof&id=" + str(profesor.id))
                else:
                    return HttpResponseRedirect("/docentes?action=addhorasprof&error=1&id=" + str(profesor.id))

        elif action == 'edithorasprof':
            horasprof = ProfesorHorasActividades.objects.get(pk=request.POST['id'])
            profesor = horasprof.profesor
            f = HorasProfesorForm(request.POST)
            if f.is_valid():
                # Editar Horas de actividades del docente
                anno= f.cleaned_data['anno']
                if not ProfesorHorasActividades.objects.filter(profesor=profesor, anno=anno).exclude(id=horasprof.id).exists():
                    horasprof.anno = f.cleaned_data['anno']
                    horasprof.horasded = f.cleaned_data['horasded']
                    horasprof.horasinv = f.cleaned_data['horasinv']
                    horasprof.horasvin = f.cleaned_data['horasvin']
                    horasprof.horasadm = f.cleaned_data['horasadm']
                    horasprof.horasotr = f.cleaned_data['horasotr']
                    horasprof.otrasactividades = f.cleaned_data['otrasactividades']
                    horasprof.save()

                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de EDITAR HORAS DE ACTIVIDADES
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(horasprof).pk,
                        object_id       = horasprof.id,
                        object_repr     = force_str(horasprof),
                        action_flag     = CHANGE,
                        change_message  = 'Editado Horas Profesor (' + client_address + ')')

                    return HttpResponseRedirect("/docentes?action=horasprof&id=" + str(profesor.id))
                else:
                    return HttpResponseRedirect("/docentes?action=edithorasprof&error=1&id=" + str(profesor.id))

        elif action == 'addtitulacion':
            profesor = Profesor.objects.get(pk=request.POST['id'])
            f = TitulacionProfesorForm(request.POST)
            if f.is_valid():
                profesortitulacion = TitulacionProfesor(profesor=profesor,
                                                        titulo=f.cleaned_data['titulo'],
                                                        nivel=f.cleaned_data['nivel'],
                                                        tiponivel=f.cleaned_data['tiponivel'],
                                                        pais=f.cleaned_data['pais'],
                                                        institucion=f.cleaned_data['institucion'],
                                                        fecha=f.cleaned_data['fecha'],
                                                        registro=f.cleaned_data['registro'],
                                                        codigoprofesional=f.cleaned_data['codigoprofesional'],
                                                        subarea=f.cleaned_data['subarea'])
                profesortitulacion.save()
                return HttpResponseRedirect("/docentes?action=titulacion&id=" + str(profesor.id))
            else:
                return HttpResponseRedirect("/docentes?action=addtitulacion&id=" + str(profesor.id))

        elif action == 'edittitulacion':
            titulacion = TitulacionProfesor.objects.get(pk=request.POST['id'])
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
                return HttpResponseRedirect("/docentes?action=titulacion&id=" + str(titulacion.profesor_id))
            else:
                return HttpResponseRedirect("/docentes?action=edittitulacion&id=" + str(request.POST['id']))

        elif action == 'deltitulacion':
            titulacion = TitulacionProfesor.objects.get(pk=request.POST['id'])
            profesor = titulacion.profesor
            titulacion.delete()
            return HttpResponseRedirect("/docentes?action=titulacion&id=" + str(profesor.id))

        elif action == 'cargarcv':
            profesor = Profesor.objects.get(pk=request.POST['id'])
            form = CargarCVForm(profesor, request.FILES)
            if form.is_valid():
                persona = profesor.persona
                cv = persona.cv()
                if cv is not None:
                    cv.cv = request.FILES['cv']
                else:
                    cv = CVPersona(persona=persona, cv=request.FILES['cv'])
                cv.save()
        #OCastillo 03-oct-2014 cargar foto docentes en conduccion
        elif action == 'cargarfoto':
                if INSCRIPCION_CONDUCCION:
                    profesor = Profesor.objects.get(pk=request.POST['id'])
                    form = CargarFotoForm(profesor, request.FILES)
                    if form.is_valid():
                        persona = profesor.persona
                        foto = persona.foto()
                        if foto!=None:
                            foto.foto = request.FILES['foto']
                        else:
                            foto = FotoPersona(persona=persona, foto=request.FILES['foto'])

                        foto.save()
        #OCastillo 06-oct-2014 foto profesional
        elif action == 'cargarfotoprof':
                if INSCRIPCION_CONDUCCION:
                    profesor = Profesor.objects.get(pk=request.POST['id'])
                    # form = CargarFotoForm(profesor, request.FILES)
                    form = CargarFotoProfForm(profesor, request.FILES)
                    if form.is_valid():
                        persona = profesor.persona
                        foto = persona.fotoprof()

                        if foto!=None:
                            foto.fotoprof = request.FILES['fotoprof']
                        else:
                            foto = FotoPersonaProf(persona=persona, fotoprof=request.FILES['fotoprof'])

                        foto.save()

        elif action == 'editrolpagoperfil':
            rolperfilprofesor = RolPerfilProfesor.objects.get(pk=request.POST['id'])
            f = RolPerfilProfesorForm(request.POST)
            if f.is_valid():
                rolperfilprofesor.chlunes = f.cleaned_data['chlunes']
                rolperfilprofesor.chmartes = f.cleaned_data['chmartes']
                rolperfilprofesor.chmiercoles = f.cleaned_data['chmiercoles']
                rolperfilprofesor.chjueves = f.cleaned_data['chjueves']
                rolperfilprofesor.chviernes = f.cleaned_data['chviernes']
                rolperfilprofesor.chsabado = f.cleaned_data['chsabado']
                rolperfilprofesor.chdomingo = f.cleaned_data['chdomingo']
                rolperfilprofesor.esfijo = f.cleaned_data['esfijo']
                rolperfilprofesor.esadministrativo = f.cleaned_data['esadministrativo']
                rolperfilprofesor.fechaafiliacion = f.cleaned_data['fechaafiliacion']
                rolperfilprofesor.coordinacion = f.cleaned_data['coordinacion']
                if rolperfilprofesor.esfijo:
                    rolperfilprofesor.horassalario = f.cleaned_data['horassalario']
                    rolperfilprofesor.salario = f.cleaned_data['salario']
                else:
                    rolperfilprofesor.horassalario = 0
                    rolperfilprofesor.salario = 0
                    rolperfilprofesor.descuentos = 0
                    rolperfilprofesor.salariopercibir = 0

                #Si es administrativo poner cargo
                if f.cleaned_data['esadministrativo']==True:
                    rolperfilprofesor.esadministrativo = True
                    rolperfilprofesor.cargo = f.cleaned_data['cargo']
                    rolperfilprofesor.iniciocargo = f.cleaned_data['iniciocargo']
                    rolperfilprofesor.fincargo = f.cleaned_data['fincargo']
                    rolperfilprofesor.documentocargo = f.cleaned_data['documentocargo']
                else:
                    rolperfilprofesor.esadministrativo = False
                    rolperfilprofesor.cargo = None
                    rolperfilprofesor.iniciocargo = None
                    rolperfilprofesor.fincargo = None
                    rolperfilprofesor.documentocargo = ''

                rolperfilprofesor.save()

                try:
                # case server externo
                     client_address = request.META['HTTP_X_FORWARDED_FOR']
                except:
                # case localhost o 127.0.0.1
                        client_address = request.META['REMOTE_ADDR']

            # Log de CAMBIO DE CLAVE
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(rolperfilprofesor).pk,
                    object_id       = rolperfilprofesor.id,
                    object_repr     = force_str(rolperfilprofesor),
                    action_flag     = CHANGE,
                    change_message  = 'Editado Perifil Rol Profesor (' + client_address + ')' )
                return HttpResponseRedirect("/docentes?action=rolpagoperfil&id=" + str(rolperfilprofesor.profesor.id))

        elif action == 'gastospersonales':
            profesorgp = ProfesorInstitucionGP.objects.get(pk=request.POST['id'])
            rol = request.POST['rol']
            f = PersonalInstitucionGPForm(request.POST)
            if f.is_valid():
                profesorgp.vivienda = f.cleaned_data['vivienda']
                profesorgp.educacion = f.cleaned_data['educacion']
                profesorgp.salud = f.cleaned_data['salud']
                profesorgp.vestimenta = f.cleaned_data['vestimenta']
                profesorgp.alimentacion = f.cleaned_data['alimentacion']
                profesorgp.save()
                if rol:
                    return HttpResponseRedirect("/rol_pago?action=ver&id=" + str(rol))
                else:
                    return HttpResponseRedirect("/docentes?s=" + str(profesorgp.perfilprof.profesor.persona.cedula))

        elif action=='liquidacion':
            profesor = Profesor.objects.get(pk=request.POST['id'])
            f = ProfesorLiquidacionForm(request.POST)
            if f.is_valid():
                profesorliquidacion = ProfesorLiquidacion(profesor=profesor,
                                                        salida=f.cleaned_data['salida'],
                                                        tipo=f.cleaned_data['tipo'],
                                                        observaciones=f.cleaned_data['observaciones'])
                profesorliquidacion.save()
                profesor.activo = False
                profesor.save()

                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de GENERACION DE LIQUIDACION
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(profesor).pk,
                    object_id       = profesor.id,
                    object_repr     = force_str(profesor),
                    action_flag     = CHANGE,
                    change_message  = 'Generada Liquidacion a Profesor (' + client_address + ')')

        elif action=='adddocumento':
            form = DocumentosProfesorForm(request.POST, request.FILES)
            profesor = Profesor.objects.get(pk=request.POST['id'])
            if form.is_valid():
                archivo = Archivo(fecha=datetime.now(),
                                  archivo=request.FILES['archivo'],
                                  tipo=form.cleaned_data['tipo'])
                archivo.save()

                documento = DocumentosProfesor(profesor=profesor, archivo=archivo)
                documento.save()

                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de ADICIONAR DOCUMENTO DEL DOCENTE
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(profesor).pk,
                    object_id       = profesor.id,
                    object_repr     = force_str(profesor),
                    action_flag     = ADDITION,
                    change_message  = 'Adicionado Documento del Profesor (' + client_address + ')' )

                return HttpResponseRedirect("/docentes?action=documentos&id="+str(profesor.id))
            else:
                return HttpResponseRedirect("/docentes?action=adddocumento&id="+str(profesor.id))


        elif action=='deldocumento':
            documento = DocumentosProfesor.objects.get(pk=request.POST['id'])
            profesor = documento.profesor
            archivo = documento.archivo

            archivo.archivo.delete()
            documento.delete()
            archivo.delete()

            #Obtain client ip address
            client_address = ip_client_address(request)

            # Log de ELIMINACION DE DOCUMENTOS DEL DOCENTE
            LogEntry.objects.log_action(
                user_id         = request.user.pk,
                content_type_id = ContentType.objects.get_for_model(profesor).pk,
                object_id       = profesor.id,
                object_repr     = force_str(profesor),
                action_flag     = DELETION,
                change_message  = 'Eliminado Documento del Profesor (' + client_address + ')')

            return HttpResponseRedirect("/personal?action=documentos&id="+str(profesor.id))

        elif action=='addestudiocursa':
            f = ProfesorEstudiosCursaForm(request.POST)
            profesor = Profesor.objects.get(pk=request.POST['id'])
            if f.is_valid():
                profesorestudio = ProfesorEstudiosCursa(profesor=profesor,
                                                        inicio=f.cleaned_data['inicio'],
                                  tipoestudio=f.cleaned_data['tipoestudio'],
                                  financiado=f.cleaned_data['financiado'])
                profesorestudio.save()

                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de ADICIONAR ESTUDIOS CURSANDO EL DOCENTE
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(profesorestudio).pk,
                    object_id       = profesorestudio.id,
                    object_repr     = force_str(profesorestudio),
                    action_flag     = ADDITION,
                    change_message  = 'Adicionado Estudio Cursando del Profesor ' + client_address +')'  )

                return HttpResponseRedirect("/docentes?action=estudioscursa&id="+str(profesor.id))
            else:
                return HttpResponseRedirect("/docentes?action=addestudiocursa&id="+str(profesor.id))

        elif action=='delestudiocursa':
            estudio = ProfesorEstudiosCursa.objects.get(pk=request.POST['id'])
            profesor = estudio.profesor

            #Obtain client ip address
            client_address = ip_client_address(request)

            # Log de ELIMINACION DE ESTUDIOS QUE CURSA EL DOCENTE
            LogEntry.objects.log_action(
                user_id         = request.user.pk,
                content_type_id = ContentType.objects.get_for_model(estudio).pk,
                object_id       = estudio.id,
                object_repr     = force_str(estudio),
                action_flag     = DELETION,
                change_message  = 'Eliminado Estudio que cursa el Profesor (' + client_address + ')')

            estudio.delete()

            return HttpResponseRedirect("/docentes?action=estudioscursa&id="+str(profesor.id))

        elif action=='areaconocimiento':
            subarea = SubAreaConocimiento.objects.get(pk=request.POST['subarea'])
            return HttpResponse(json.dumps({"result": "ok", "areaconocimiento": subarea.area.nombre }),content_type="application/json")

        return HttpResponseRedirect("/docentes")
    else:
        try:
            data = {'title': 'Listado de Docentes'}
            addUserData(request, data)
            if 'action' in request.GET:
                action = request.GET['action']

                if action == 'activation':
                    d = Profesor.objects.get(pk=request.GET['id'])
                    d.persona.usuario.is_active = not d.activo
                    d.persona.usuario.save()
                    d.activo = not d.activo
                    d.save()

                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de ELIMINACION DE ESTUDIOS QUE CURSA EL DOCENTE
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(d).pk,
                        object_id       = d.id,
                        object_repr     = force_str(d),
                        action_flag     = DELETION,
                        change_message  = 'Cambio de Estado de Profesor a '+ str(d.activo) +' (' + client_address + ')')
                    return HttpResponseRedirect("/docentes?s="+d.persona.cedula)

                elif action == 'titulacion':
                    data['title'] = 'Titulos del Docente'
                    profesor = Profesor.objects.get(pk=request.GET['id'])
                    data['profesor'] = profesor
                    return render(request ,"docentes/titulacionbs.html" ,  data)
                elif action =='cambiaestado':
                    for p in Profesor.objects.filter(activo=False):
                        p.persona.usuario.is_active = False
                        p.persona.usuario.save()
                        # print(str(p))

                if action == 'addtitulacion':
                    data['title'] = 'Adicionar Titulacion del Docente'
                    profesor = Profesor.objects.get(pk=request.GET['id'])
                    data['profesor'] = profesor
                    form = TitulacionProfesorForm()
                    data['form'] = form
                    return render(request ,"docentes/adicionartitulacionbs.html" ,  data)

                elif action == 'edittitulacion':
                    data['title'] = 'Editar Titulacion del Docente'
                    titulacion = TitulacionProfesor.objects.get(pk=request.GET['id'])
                    data['profesor'] = titulacion.profesor
                    initial = model_to_dict(titulacion)
                    form = TitulacionProfesorForm(initial=initial)
                    data['form'] = form
                    data['titulacion'] = titulacion
                    return render(request ,"docentes/editartitulacionbs.html" ,  data)

                elif action == 'deltitulacion':
                    data['title'] = 'Borrar Titulacion del Profesor'
                    titulacion = TitulacionProfesor.objects.get(pk=request.GET['id'])
                    data['titulacion'] = titulacion
                    data['profesor'] = titulacion.profesor
                    return render(request ,"docentes/borrartitulacionbs.html" ,  data)

                elif action == 'add':
                    data['title'] = 'Adicionar Profesor'
                    data['form'] = ProfesorForm()
                    data['conduccion'] = INSCRIPCION_CONDUCCION
                    return render(request ,"docentes/adicionarbs.html" ,  data)

                elif action == 'edit':
                    p = Profesor.objects.get(pk=request.GET['id'])
                    initial = model_to_dict(p)
                    initial.update(model_to_dict(p.persona))
                    data['form'] = ProfesorForm(initial=initial)
                    data['profesor'] = p
                    return render(request ,"docentes/editarbs.html" ,  data)

                #Horas de diferentes actividades que realiza el docente
                elif action == 'horasprof':
                    profesor = Profesor.objects.get(pk=request.GET['id'])
                    data['horasprof'] = profesor.horas_actividades()
                    data['profesor'] = profesor
                    return render(request ,"docentes/horasprof.html" ,  data)

                elif action == 'addhorasprof':
                    error1 = None
                    profesor = Profesor.objects.get(pk=request.GET['id'])
                    if 'error' in request.GET:
                        error1 = request.GET['error']
                    data['error1'] = error1 if error1 else ''
                    data['profesor'] = profesor
                    data['form'] = HorasProfesorForm()
                    return render(request ,"docentes/addhorasprof.html" ,  data)

                elif action == 'edithorasprof':
                    ph = ProfesorHorasActividades.objects.get(pk=request.GET['id'])
                    initial = model_to_dict(ph)
                    data['form'] = HorasProfesorForm(initial=initial)
                    data['ph'] = ph
                    return render(request ,"docentes/edithorasprof.html" ,  data)

                elif action == 'delhorasprof':
                    horasprof = ProfesorHorasActividades.objects.get(pk=request.GET['id'])
                    profesor = horasprof.profesor

                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de ELIMINAR HORAS DE ACTIVIDADES
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(horasprof).pk,
                        object_id       = horasprof.id,
                        object_repr     = force_str(horasprof),
                        action_flag     = CHANGE,
                        change_message  = 'Eliminada Horas Profesor (' + client_address + ')')

                    horasprof.delete()
                    return HttpResponseRedirect("/docentes?action=horasprof&id=" + str(profesor.id))

                elif action == 'cargarcv':
                    data['profesor'] = Profesor.objects.get(pk=request.GET['id'])
                    data['form'] = CargarCVForm()
                    return render(request ,"docentes/cargarcvbs.html" ,  data)

                #Fotos del docente
                elif action=='borrarfoto':
                    if INSCRIPCION_CONDUCCION:
                         profesor = Profesor.objects.get(pk=request.GET['id'])
                         persona = profesor.persona
                         persona.borrar_foto()
                         return HttpResponseRedirect("/docentes")
                elif action=='cargarfoto':
                    if INSCRIPCION_CONDUCCION:
                         profesor = Profesor.objects.get(pk=request.GET['id'])
                         form = CargarFotoForm()
                         data['profesor'] = profesor
                         data['form'] = form
                         data['conduccion'] = INSCRIPCION_CONDUCCION
                         return render(request ,"docentes/cargarfotobs.html" ,  data)
                elif action=='verfoto':
                    if INSCRIPCION_CONDUCCION:
                         profesor = Profesor.objects.get(pk=request.GET['id'])
                         data['profesor'] = profesor
                         data['conduccion'] = INSCRIPCION_CONDUCCION
                         return render(request ,"docentes/fotobs.html" ,  data)

                #Fotos profesional del docente
                elif action=='borrarfotoprof':
                    if INSCRIPCION_CONDUCCION:
                         profesor = Profesor.objects.get(pk=request.GET['id'])
                         persona = profesor.persona
                         persona.borrar_fotoprof()
                         return HttpResponseRedirect("/docentes")
                elif action=='cargarfotoprof':
                    if INSCRIPCION_CONDUCCION:
                         profesor = Profesor.objects.get(pk=request.GET['id'])
                         form =  CargarFotoProfForm()
                         data['profesor'] = profesor
                         data['form'] = form
                         data['conduccion'] = INSCRIPCION_CONDUCCION
                         return render(request ,"docentes/cargarfotobs.html" ,  data)
                elif action=='verfotoprof':
                    if INSCRIPCION_CONDUCCION:
                         profesor = Profesor.objects.get(pk=request.GET['id'])
                         data['profesor'] = profesor
                         data['conduccion'] = 'SI'
                         return render(request ,"docentes/fotobs.html" ,  data)


                elif action == 'borrarcv':
                    profesor = Profesor.objects.get(pk=request.GET['id'])
                    persona = profesor.persona
                    persona.borrar_cv()
                    data['profesor'] = profesor
                    return HttpResponseRedirect("/docentes")

                #Resetear la Clave del usuario a la contrasenna por default en el settings
                elif action == 'resetear':
                    data['title'] = 'Resetear Clave del Usuario'
                    profesor = Profesor.objects.get(pk=int(request.GET['id']))
                    user = profesor.persona.usuario
                    numdocment = profesor.persona.cedula if profesor.persona.cedula else profesor.persona.pasaporte
                    if DEFAULT_PASSWORD == 'itb' and ACTIVA_ADD_EDIT_AD:
                        user.set_password(NEW_PASSWORD)
                        scriptresponse = ''
                        mensajesc = ''
                        listnombre = []
                        validacambio = False
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
                        if  not validacambio:
                            return HttpResponseRedirect("/docentes?error=Vuelva a intentarlo")
                    else:
                        user.set_password(DEFAULT_PASSWORD)
                        user.save()
                    return HttpResponseRedirect("/docentes?s="+numdocment)

                elif action == 'eliminar':
                    try:
                        profesor = Profesor.objects.get(pk=request.GET['id'])

                        #Obtain client ip address
                        client_address = ip_client_address(request)

                        # Log de BORRAR HISTORICO
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(profesor).pk,
                            object_id       = profesor.id,
                            object_repr     = force_str(profesor),
                            action_flag     = DELETION,
                            change_message  = 'Borrado Historico Academico (' + client_address + ')')

                        profesor.persona.usuario.delete()

                        request.method = ''
                        return HttpResponseRedirect("/docentes?t=" + request.method)
                        # return render(request ,"docentes/docentesbs.html" ,  data)
                    except Exception as ex:
                        return HttpResponseRedirect("/")

                #Perfil del Rol de Pago del Profesor
                elif action == 'rolpagoperfil':
                    ret = None
                    data['title'] = 'Perfil del Rol de Pago del Docente'
                    if 'ret' in request.GET:
                        ret = request.GET['ret']
                    profesor = Profesor.objects.get(pk=int(request.GET['id']))
                    rolperfilprofesor = profesor.rol_perfil()                   #Funcion para crear el rol perfil del docente si no existe, sino toma el valor actual
                    data['profesor'] = profesor
                    data['rolperfilprofesor'] = rolperfilprofesor
                    data['ret'] = ret if ret else ""
                    return render(request ,"docentes/rolpagoperfil.html" ,  data)

                elif action == 'editrolpagoperfil':
                    data['title'] = 'Editar Perfil Rol de Pago a Docente'
                    rolperfilprofesor = RolPerfilProfesor.objects.get(pk=request.GET['id'])
                    initial = model_to_dict(rolperfilprofesor)
                    data['form'] = RolPerfilProfesorForm(initial=initial)
                    data['rolperfilprofesor'] = rolperfilprofesor
                    data['iess'] = COEFICIENTE_PORCIENTO_IESS
                    return render(request ,"docentes/editperfilrol.html" ,  data)

                elif action == 'horario':
                    try:
                        profesor = Profesor.objects.get(pk=request.GET['id'])
                        #data['disponible'] = LeccionGrupo.objects.filter(profesor=profesor, abierta=True).count() == 0
                        #data['lecciongrupo'] = LeccionGrupo.objects.get(profesor=profesor,abierta=True)
                        data['title'] = 'Horario de Profesor'
                        data['profesor'] = profesor
                        data['semana'] = ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes']
                        data['sesiones'] = Sesion.objects.all()
                        clases = Clase.objects.filter(materia__profesormateria__profesor=profesor, materia__nivel__periodo=request.session['periodo'])
                        clasespm = [(x, x.materia.profesormateria_set.filter(profesor=profesor)[:1].get()) for x in clases]
                        data['clases'] = clasespm
                        return render(request ,"docentes/horariosbs.html" ,  data)
                    except Exception as ex:
                        return HttpResponseRedirect("/?error="+str(ex))

                elif action == 'materias':
                    try:
                        profesor = Profesor.objects.get(pk=request.GET['id'])
                        periodo = request.session['periodo']
                        data['title'] = 'Materias de Profesor'
                        data['profesor'] = profesor
                        data['materias'] = profesor.mis_materias(periodo).order_by('materia__asignatura__nombre')
                        return render(request ,"docentes/materiasbs.html" ,  data)
                    except:
                        return HttpResponseRedirect("/")

                elif action=='gastospersonales':
                    rol = None
                    if 'rol' in request.GET:
                        rol = request.GET['rol']
                    data['title'] = 'Gastos Personales SRI del Docente'
                    profesor = Profesor.objects.get(pk=request.GET['id'])
                    perfilprofesor = profesor.rol_perfil()
                    if not perfilprofesor.profesorinstituciongp_set.exists():
                        #Si no existe crea Proyeccion de Gastos Personales - Impuesto Renta SRI
                        profesorgpsri = ProfesorInstitucionGP(perfilprof=perfilprofesor)
                        profesorgpsri.save()
                    else:
                        profesorgpsri = perfilprofesor.profesorinstituciongp_set.all()[:1].get()

                    initial = model_to_dict(profesorgpsri)
                    data['form'] = PersonalInstitucionGPForm(initial=initial)
                    data['profesorgpsri'] = profesorgpsri
                    data['profesor'] = profesorgpsri.perfilprof.profesor
                    data['rol'] = rol if rol else ""
                    return render(request ,"docentes/gp/gastos.html" ,  data)

                elif action=='liquidacion':
                    profesor = Profesor.objects.get(pk=request.GET['id'])
                    data['form'] = ProfesorLiquidacionForm(initial={'salida': datetime.today()})
                    data['profesor'] = profesor
                    return render(request ,"docentes/liquidacion.html" ,  data)

                elif action=='documentos':
                    data['title'] = 'Documentos y Archivos del Docente'
                    profesor = Profesor.objects.get(pk=request.GET['id'])
                    data['profesor'] = profesor
                    data['documentos'] = profesor.documentosprofesor_set.all()
                    return render(request ,"docentes/documentos.html" ,  data)

                elif action=='adddocumento':
                    data['title'] = 'Adicionar Documentos y Archivos del Docente'
                    profesor = Profesor.objects.get(pk=request.GET['id'])
                    data['profesor'] = profesor
                    form = DocumentosProfesorForm()
                    data['form'] = form
                    return render(request ,"docentes/add_documentos.html" ,  data)

                elif action=='deldocumento':
                    data['title'] = 'Eliminar Archivo o Documento del Profesor'
                    data['documento'] = DocumentosProfesor.objects.get(pk=request.GET['id'])
                    return render(request ,"docentes/borrar_documentos.html" ,  data)

                elif action=='estudioscursa':
                    data['title'] = 'Estudios que cursa el docente'
                    profesor = Profesor.objects.get(pk=request.GET['id'])
                    data['profesor'] = profesor
                    data['cursandoestudios'] = profesor.profesorestudioscursa_set.all()
                    return render(request ,"docentes/estudioscursa.html" ,  data)

                elif action=='addestudiocursa':
                    data['title'] = 'Adicionar Estudios que cursa el Docente'
                    profesor = Profesor.objects.get(pk=request.GET['id'])
                    data['profesor'] = profesor
                    form = ProfesorEstudiosCursaForm(initial={'inicio': datetime.today()})
                    data['form'] = form
                    return render(request ,"docentes/estudiocursaadd.html" ,  data)

                elif action=='delestudiocursa':
                    data['title'] = 'Eliminar Estudio que cursa el Docente'
                    data['estudio'] = ProfesorEstudiosCursa.objects.get(pk=request.GET['id'])
                    return render(request ,"docentes/estudiocursadel.html" ,  data)

                elif action == 'analisis':
                    profesor = Profesor.objects.get(pk=request.GET['id'])
                    periodo = request.session['periodo']
                    data['profesor'] = profesor
                    data['autoevaluacion']= profesor.calcula_autoevaluacion(periodo)
                    data['evaluacioncoordinador'] = profesor.calcula_evaluacion_coordinador(periodo)
                    data['evaluacionalumno'] = profesor.calcula_evaluacion_alumno(periodo)
                    return render(request ,"docentes/analisis.html" ,  data)
                elif action == 'veranalisis':
                    profesor = Profesor.objects.get(pk=request.GET['id'])
                    periodo = request.session['periodo']
                    data['profesor'] = profesor
                    data['autoevaluacion']= profesor.calcula_autoevaluacion(periodo)
                    data['evaluacioncoordinador'] = profesor.calcula_evaluacion_coordinador(periodo)
                    data['evaluacionalumno'] = profesor.calcula_evaluacion_alumno(periodo)
                    data['obs'] = AnalisisEvaluacion.objects.get(profesor=profesor,periodo=periodo)
                    data['ver'] = 1
                    return render(request ,"docentes/analisis.html" ,  data)

                elif action == 'mat_nocerrada':
                    data['title'] = 'Materias No Cerradas'
                    search = None
                    if 'buscar' in request.GET:

                        todos = None
                        activos = None
                        inactivos = None
                        band=0
                        if 's' in request.GET:
                            search = request.GET['s']
                            band=1
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
                                profesores = ProfesorMateria.objects.filter(Q(profesor__persona__nombres__icontains=search) |
                                                                            Q(profesor__persona__apellido1__icontains=search) |
                                                                            Q(profesor__persona__apellido2__icontains=search) |
                                                                            Q(profesor__persona__cedula__icontains=search) |
                                                                            Q(profesor__persona__pasaporte__icontains=search),materia__cerrado = False,materia__fin__lt=datetime.now().date()).order_by('profesor__persona__apellido1','profesor__persona__apellido2','profesor__persona__nombres','desde')
                           else:
                                profesores = ProfesorMateria.objects.filter(Q(profesor__persona__nombres__icontains=search) |
                                                                            Q(profesor__persona__cedula__icontains=search) ,materia__cerrado = False,materia__fin__lt=datetime.now().date()).order_by('profesor__persona__apellido1','profesor__persona__apellido2','profesor__persona__nombres','desde')
                    else:
                        profesores=ProfesorMateria.objects.filter(materia__cerrado = False,materia__fin__lt=datetime.now().date()).order_by('profesor__persona__apellido1','profesor__persona__apellido2','profesor__persona__nombres','desde')

                    paging = MiPaginador(profesores, 30)
                    p = 1
                    try:
                       if 'page' in request.GET:
                           p = int(request.GET['page'])
                           paging = MiPaginador(profesores, 30)
                       page = paging.page(p)
                    except Exception as ex:
                           page = paging.page(1)

                    data['paging'] = paging
                    data['rangospaging'] = paging.rangos_paginado(p)
                    data['page'] = page
                    data['search'] = search if search else ""
                    data['profesores'] = page.object_list
                    return render(request ,"docentes/mat_sincerrar.html" ,  data)

                # return HttpResponseRedirect("/docentes")

                elif action == 'clase_nocerrada':
                    #OCU 24-agosto-2017 clases no cerradas
                    data['title'] = 'Clases No Cerradas'
                    search = None
                    if 'buscar' in request.GET:

                        todos = None
                        activos = None
                        inactivos = None
                        band=0
                        if 's' in request.GET:
                            search = request.GET['s']
                            band=1
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
                                leccion=LeccionGrupo.objects.filter(Q(profesor__persona__nombres__icontains=search) |
                                                                    Q(profesor__persona__apellido1__icontains=search) |
                                                                    Q(profesor__persona__apellido2__icontains=search),abierta=True).order_by('-fecha')
                           else:
                                leccion=LeccionGrupo.objects.filter(Q(profesor__persona__nombres__icontains=search) |
                                                                    Q(profesor__persona__cedula__icontains=search),abierta=True).order_by('-fecha')
                    else:
                        leccion=LeccionGrupo.objects.filter(abierta=True).order_by('-fecha')

                    paging = MiPaginador(leccion, 30)
                    p = 1
                    try:
                       if 'page' in request.GET:
                           p = int(request.GET['page'])
                           paging = MiPaginador(leccion, 30)
                       page = paging.page(p)
                    except Exception as ex:
                           page = paging.page(1)

                    data['paging'] = paging
                    data['rangospaging'] = paging.rangos_paginado(p)
                    data['page'] = page
                    data['search'] = search if search else ""
                    data['leccion'] = page.object_list
                    return render(request ,"docentes/clases_sincerrar.html" ,  data)

                return HttpResponseRedirect("/docentes")
            else:
                search = None
                todos = None
                activos = None
                inactivos = None
                docentes = None
                instructores = None
                periodo = request.session['periodo']
                # sin_coordinadores = Carrera.objects.all().exclude(coordinadorcarrera__periodo=periodo)
                if 's' in request.GET:
                    search = request.GET['s']
                if 'a' in request.GET:
                    activos = request.GET['a']
                if 'error' in request.GET:
                    data['error'] = request.GET['error']
                if 'i' in request.GET:
                    inactivos = request.GET['i']
                if 't' in request.GET:
                    todos = request.GET['t']
                if 'd' in request.GET:
                    docentes = request.GET['d']
                if 'it' in request.GET:
                    instructores = request.GET['it']
                if search:
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')
                    if len(ss) == 1:
                        profesores = Profesor.objects.filter(Q(persona__nombres__icontains=search) |
                                                             Q(persona__apellido1__icontains=search) |
                                                             Q(persona__apellido2__icontains=search) |
                                                             Q(persona__cedula__icontains=search) |
                                                             Q(persona__pasaporte__icontains=search)).order_by('persona__apellido1')
                                                             # OCastillo 02-oct-2014 se quita la exclusión de instructores
                                                             # Q(persona__pasaporte__icontains=search)).order_by('persona__apellido1').exclude(dedicacion__id=PROFE_PRACT_CONDUCCION)

                    else:
                        profesores = Profesor.objects.filter(Q(persona__apellido1__icontains=ss[0]) &
                                                             Q(persona__apellido2__icontains=ss[1])).order_by('persona__apellido1', 'persona__apellido2', 'persona__nombres')
                                                             # OCastillo 02-oct-2014 se quita la exclusión de instructores
                                                             # Q(persona__apellido2__icontains=ss[1])).order_by('persona__apellido1', 'persona__apellido2', 'persona__nombres').exclude(dedicacion__id=PROFE_PRACT_CONDUCCION)
                else:
                    # OCastillo 02-oct-2014 se quita la exclusión de instructores
                    # profesores = Profesor.objects.filter(activo=True).order_by('persona__apellido1').exclude(dedicacion__id=PROFE_PRACT_CONDUCCION)
                    profesores = Profesor.objects.filter(activo=True).order_by('persona__apellido1')
                if todos:
                    # OCastillo 02-oct-2014 se quita la exclusión de instructores
                    # profesores = Profesor.objects.all().order_by('persona__apellido1').exclude(dedicacion__id=PROFE_PRACT_CONDUCCION)
                    profesores = Profesor.objects.all().order_by('persona__apellido1')
                if activos:
                    # OCastillo 02-oct-2014 se quita la exclusión de instructores
                    # profesores = Profesor.objects.filter(activo=True).order_by('persona__apellido1').exclude(dedicacion__id=PROFE_PRACT_CONDUCCION)
                    profesores = Profesor.objects.filter(activo=True).order_by('persona__apellido1')
                if inactivos:
                    # OCastillo 02-oct-2014 se quita la exclusión de instructores
                    # profesores = Profesor.objects.filter(activo=False).order_by('persona__apellido1').exclude(dedicacion__id=PROFE_PRACT_CONDUCCION)
                    profesores = Profesor.objects.filter(activo=False).order_by('persona__apellido1')
                if docentes:
                    # OCastillo 02-oct-2014 presenta solo docentes
                    if INSCRIPCION_CONDUCCION:
                        profesores = Profesor.objects.all().order_by('persona__apellido1').exclude(dedicacion__id=PROFE_PRACT_CONDUCCION)
                    else:
                    # profesores = Profesor.objects.filter(activo=False).order_by('persona__apellido1').exclude(dedicacion__id=PROFE_PRACT_CONDUCCION)
                        profesores = Profesor.objects.all().order_by('persona__apellido1')
                    # profesores = Profesor.objects.all().order_by('persona__apellido1').exclude(dedicacion__id=PROFE_PRACT_CONDUCCION)
                if instructores:
                    # OCastillo 02-oct-2014 presenta solo instructores
                    profesores = Profesor.objects.filter(dedicacion=PROFE_PRACT_CONDUCCION).order_by('persona__apellido1')

                paging = Paginator(profesores, 20)
                p=1
                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                    page = paging.page(p)
                except:
                    page = paging.page(p)
                data['paging'] = paging
                data['search'] = search if search else ""
                data['todos'] = todos if todos else ""
                data['activos'] = activos if activos else ""
                data['inactivos'] = inactivos if inactivos else ""
                data['docentes'] = docentes if docentes else ""
                data['instructores'] = instructores if instructores else ""
                data['profesores'] = page.object_list
                data['clave'] = DEFAULT_PASSWORD if not ACTIVA_ADD_EDIT_AD else NEW_PASSWORD
                data['alum'] = 0
                # data['carreras']= sin_coordinadores
                data['usafichamedica'] = UTILIZA_FICHA_MEDICA
                # data['cantidadcarreras'] = sin_coordinadores.count()
                data['conduccion'] = INSCRIPCION_CONDUCCION
                data['fechahoy'] = datetime.now().date()

                #OCastillo 05-06-2019 correo de materias si cerrar
                arreglo_coordinacion = []
                dias = 0
                if not DEFAULT_PASSWORD=='itf':
                    fecha =datetime.now().date() + timedelta(days=-3)
                    for coordinacion in Coordinacion.objects.values('id').all().exclude(pk=4).order_by('id'):

                        coord=Coordinacion.objects.filter(id=coordinacion['id'])[:1].get()
                        carreras= Coordinacion.objects.filter(id=coordinacion['id']).order_by('id').values('carrera')

                        arreglo_coordinacion = []
                        if coord.id!=COORDINACION_UASSS:
                            if carreras:
                                for matsinrecep in MateriaRecepcionActaNotas.objects.filter(entregada=False,materia__cerrado=True,materia__fechacierre__gte='2019-05-01',materia__fechacierre__lte=fecha,materia__nivel__carrera__in=carreras).order_by('materia__asignatura__nombre'):
                                    if ProfesorMateria.objects.filter(materia=matsinrecep.materia,segmento__id=TIPOSEGMENTO_TEORIA,materia__cerrado=True,hasta=matsinrecep.materia.fin).exists():
                                        docente = ProfesorMateria.objects.filter(materia=matsinrecep.materia,segmento__id=TIPOSEGMENTO_TEORIA,hasta=matsinrecep.materia.fin)[:1].get()
                                        if docente.profesor_aux:
                                            profesor=Profesor.objects.get(pk=docente.profesor_aux)
                                            if profesor.activo:
                                                if docente.fechacorreo != datetime.now().date():
                                                    docente.fechacorreo = datetime.now().date()
                                                    docente.save()
                                                    arreglo_coordinacion.append((elimina_tildes(matsinrecep.materia.asignatura.nombre),elimina_tildes(profesor.persona.nombre_completo_inverso()),matsinrecep.materia.nivel.nivelmalla.nombre,matsinrecep.materia.nivel.grupo.nombre,matsinrecep.materia.fechacierre,elimina_tildes(matsinrecep.materia.nivel.carrera.nombre)))
                                        else:
                                            profesor = docente.profesor
                                            if profesor.activo:
                                                if docente.fechacorreo != datetime.now().date():
                                                    docente.fechacorreo = datetime.now().date()
                                                    docente.save()
                                                    arreglo_coordinacion.append((elimina_tildes(matsinrecep.materia.asignatura.nombre),elimina_tildes(profesor.persona.nombre_completo_inverso()),matsinrecep.materia.nivel.nivelmalla.nombre,matsinrecep.materia.nivel.grupo.nombre,matsinrecep.materia.fechacierre,elimina_tildes(matsinrecep.materia.nivel.carrera.nombre)))
                        else:
                            if carreras:
                                for matsinrecep in MateriaRecepcionActaNotas.objects.filter(entregada=False,materia__cerrado=True,materia__fechacierre__gte='2019-05-01',materia__fechacierre__lte=fecha,materia__nivel__carrera__in=carreras).order_by('materia__asignatura__nombre'):
                                    if ProfesorMateria.objects.filter(materia=matsinrecep.materia,segmento__id=TIPOSEGMENTO_TEORIA,profesor__activo=True,materia__cerrado=True).exists():
                                        docente = ProfesorMateria.objects.filter(materia=matsinrecep.materia,segmento__id=TIPOSEGMENTO_TEORIA,profesor__activo=True,materia__cerrado=True)[:1].get()
                                        if docente.profesor_aux:
                                            profesor=Profesor.objects.get(pk=docente.profesor_aux)
                                            if profesor.activo:
                                                if docente.fechacorreo != datetime.now().date():
                                                    docente.fechacorreo = datetime.now().date()
                                                    docente.save()
                                                    arreglo_coordinacion.append((elimina_tildes(matsinrecep.materia.asignatura.nombre),elimina_tildes(profesor.persona.nombre_completo_inverso()),matsinrecep.materia.nivel.nivelmalla.nombre,matsinrecep.materia.nivel.grupo.nombre,matsinrecep.materia.fechacierre,elimina_tildes(matsinrecep.materia.nivel.carrera.nombre)))
                                        else:
                                            profesor = docente.profesor
                                            if profesor.activo:
                                                if docente.fechacorreo != datetime.now().date():
                                                    docente.fechacorreo = datetime.now().date()
                                                    docente.save()
                                                    arreglo_coordinacion.append((elimina_tildes(matsinrecep.materia.asignatura.nombre),elimina_tildes(profesor.persona.nombre_completo_inverso()),matsinrecep.materia.nivel.nivelmalla.nombre,matsinrecep.materia.nivel.grupo.nombre,matsinrecep.materia.fechacierre,elimina_tildes(matsinrecep.materia.nivel.carrera.nombre)))
                        if arreglo_coordinacion and EMAIL_ACTIVE and coord.correo:
                            correo_persona(arreglo_coordinacion,coord)
                return render(request ,"docentes/docentesbs.html" ,  data)
        except Exception as ex:
            print(ex)

def correo_persona(arreglo_coordinacion,coord):
    hoy = datetime.now()
    contenido = "NOTIFICACION - ACTAS SIN ENTREGAR"
    send_html_mail("ACTAS SIN ENTREGAR",
        "emails/actas_sinentregar.html", { 'contenido': contenido,  'arreglo_coordinacion':arreglo_coordinacion,'coordinacion':coord.nombre,'fecha':hoy},coord.correo.split(","))