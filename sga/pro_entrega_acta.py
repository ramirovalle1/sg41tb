# -*- coding: latin-1 -*-
import json
from datetime import datetime
import os
import smtplib
from django.contrib.admin.models import LogEntry, CHANGE, ADDITION, DELETION
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from django.db.models import Q
import xlwt
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.forms import model_to_dict
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.utils.encoding import force_str
from decorators import secure_module
from settings import REPORTE_CRONOGRAMA_PROFESOR, EMAIL_ACTIVE, VALIDA_MATERIA_APROBADA, DEFAULT_PASSWORD, SITE_ROOT, EMAIL_HOST, EMAIL_HOST_USER, \
     EMAIL_HOST_PASSWORD, MEDIA_ROOT,TIPOSEGMENTO_PRACT,TIPOSEGMENTO_TEORIA,COORDINACION_UASSS
from sga.commonviews import addUserData
from sga.forms import ClaseOnlineForm, RecepcionActaDocenteForm, RecepcionActaAlcanceDocenteForm, RecepcionNivelCerradoDocenteForm
from sga.models import Profesor, Materia, MateriaAsignada, TipoIncidencia, Persona, LogAceptacionProfesorMateria, ProfesorMateria, LeccionGrupo, Coordinacion, elimina_tildes, ClasesOnline, convertir_fecha, Leccion, TituloInstitucion, MateriaRecepcionActaNotas
from sga.tasks import send_html_mail
from socioecon.cons_socioecon import ip_client_address


@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    if request.method == 'POST':
        action = request.POST['action']

        if action == 'addacta':
            idmateria = request.POST['materiaid']
            materia = Materia.objects.filter(id=idmateria)[:1].get()
            f = RecepcionActaDocenteForm(request.POST, request.FILES)
            persona = Persona.objects.filter(usuario=request.user)[:1].get()
            if f.is_valid():
                try:
                    if MateriaRecepcionActaNotas.objects.filter(materia=materia).exists():
                        mrecep = MateriaRecepcionActaNotas.objects.filter(materia=materia)[:1].get()
                    else:
                        mrecep = MateriaRecepcionActaNotas(materia=materia)
                        mrecep.save()
                    if mrecep.entregada:
                        return HttpResponseRedirect('/pro_entrega_acta?error=ACTA APROBADA')
                    if 'acta' in request.FILES:
                        mrecep.acta = request.FILES['acta']

                    if 'resumen' in request.FILES:
                        mrecep.resumen = request.FILES['resumen']
                        # mrecep.entregada = True
                    mrecep.fecha = datetime.now()
                    mrecep.hora = datetime.now().time()
                    # mrecep.codigo = 'ONLINE'
                    mrecep.entrega = Persona.objects.filter(usuario=request.user)[:1].get().nombre_completo_inverso()
                    mrecep.observaciones = f.cleaned_data['observaciones']
                    # mrecep.usuario = request.user
                    mrecep.save()
                    tipo = ''
                    correo = ''
                    if Coordinacion.objects.filter(carrera=materia.nivel.carrera).exists():
                        correocoordinacion = Coordinacion.objects.filter(carrera=materia.nivel.carrera)[:1].get()
                        if TipoIncidencia.objects.filter(pk=57).exists():
                            tipo = TipoIncidencia.objects.get(pk=57)
                        correo = str(persona.emailinst) + ',' + tipo.correo + ',' + correocoordinacion.correo
                    mrecep.correoentrega_acta(correo, persona)
                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de ACTA ENTREGADA
                    LogEntry.objects.log_action(
                        user_id=request.user.pk,
                        content_type_id=ContentType.objects.get_for_model(mrecep).pk,
                        object_id=mrecep.id,
                        object_repr=force_str(mrecep),
                        action_flag=ADDITION,
                        change_message='Acta Entregada (' + client_address + ')')
                    return HttpResponseRedirect('/pro_entrega_acta?error=ACTA DE NOTAS ENTREGADA')
                except Exception as e:
                    return HttpResponseRedirect('/pro_entrega_acta?error=' + str(e))
            else:
                return HttpResponseRedirect(
                    '/pro_entrega_acta?error=OCURRIO UN ERROR.. DEBE INGRESAR LOS 2 ARCHIVOS Y LA OBSERVACION')

        elif action == 'addactaalcance':
            idmateria = request.POST['materiaid']
            materia = Materia.objects.filter(id=idmateria)[:1].get()
            f = RecepcionActaAlcanceDocenteForm(request.POST, request.FILES)
            persona = Persona.objects.filter(usuario=request.user)[:1].get()
            if f.is_valid():
                try:
                    if MateriaRecepcionActaNotas.objects.filter(materia=materia).exists():
                        mrecep = MateriaRecepcionActaNotas.objects.filter(materia=materia)[:1].get()
                        if mrecep.alcanceentregada:
                            return HttpResponseRedirect('/pro_entrega_acta?error=ACTA DE ALCANCE APROBADA')
                    else:
                        mrecep = MateriaRecepcionActaNotas(materia=materia)
                        mrecep.save()
                    if 'alcance' in request.FILES:
                        mrecep.alcance = request.FILES['alcance']

                    # mrecep.entregada = True
                    mrecep.alcancefecha = datetime.now()
                    mrecep.alcancehora = datetime.now().time()
                # mrecep.codigo = 'ONLINE'

                    mrecep.observacionesalcance = f.cleaned_data['observaciones']
                # mrecep.usuario = request.user
                    mrecep.save()
                    tipo = ''
                    correo = ''
                    if Coordinacion.objects.filter(carrera=materia.nivel.carrera).exists():
                        correocoordinacion = Coordinacion.objects.filter(carrera=materia.nivel.carrera)[:1].get()
                        if TipoIncidencia.objects.filter(pk=57).exists():
                            tipo = TipoIncidencia.objects.get(pk=57)
                        correo = str(persona.emailinst) + ',' + tipo.correo + ',' + correocoordinacion.correo
                    mrecep.correoentrega_acta_alcance(correo, persona)
                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de ADICIONAR ACTA DE ALCANCE
                    LogEntry.objects.log_action(
                        user_id=request.user.pk,
                        content_type_id=ContentType.objects.get_for_model(mrecep).pk,
                        object_id=mrecep.id,
                        object_repr=force_str(mrecep),
                        action_flag=ADDITION,
                        change_message='Acta Entregada Alcance (' + client_address + ')')
                    return HttpResponseRedirect('/pro_entrega_acta?error=ACTA DE ALCANCE ENTREGADA')
                except Exception as e:
                    return HttpResponseRedirect('/pro_entrega_acta?error=' + str(e))
            else:
                return HttpResponseRedirect(
                    '/pro_entrega_acta?error=OCURRIO UN ERROR.. DEBE INGRESAR UN ARCHIVO Y LA OBSERVACION')

        elif action == 'addactanivel':
            idmateria = request.POST['materiaid']
            materia = Materia.objects.filter(id=idmateria)[:1].get()
            f = RecepcionNivelCerradoDocenteForm(request.POST, request.FILES)
            persona = Persona.objects.filter(usuario=request.user)[:1].get()
            mrecep=None
            if f.is_valid():
                try:
                    if MateriaRecepcionActaNotas.objects.filter(materia=materia).exists():
                        mrecep = MateriaRecepcionActaNotas.objects.filter(materia=materia)[:1].get()
                        if mrecep.actanivelentregada:
                            return HttpResponseRedirect('/pro_entrega_acta?error=ACTA YA ESTA APROBADA')
                        else:
                            #OCastillo 18-06-2021 si otra acta existe y no ha sido aprobada debe poder ingresar nueva acta
                            if 'actanivel' in request.FILES:
                                mrecep.actanivel = request.FILES['actanivel']

                            #OCastillo 04-01-2023 subir resumen en nivel cerrado
                            if 'resumen' in request.FILES:
                                mrecep.resumennivel = request.FILES['resumen']

                            mrecep.actanivelfecha = datetime.now()
                            mrecep.actanivelhora = datetime.now().time()
                            mrecep.actanivelobservaciones = f.cleaned_data['observaciones']
                            mrecep.save()
                    else:
                        mrecep = MateriaRecepcionActaNotas(materia=materia)
                        mrecep.save()
                        if 'actanivel' in request.FILES:
                            mrecep.actanivel = request.FILES['actanivel']

                        #OCastillo 04-01-2023 subir resumen en nivel cerrado
                        if 'resumen' in request.FILES:
                            mrecep.resumennivel = request.FILES['resumen']

                        mrecep.actanivelfecha = datetime.now()
                        mrecep.actanivelhora = datetime.now().time()
                        mrecep.actanivelobservaciones = f.cleaned_data['observaciones']

                        mrecep.save()
                    tipo = ''
                    correo = ''
                    if Coordinacion.objects.filter(carrera=materia.nivel.carrera).exists():
                        correocoordinacion = Coordinacion.objects.filter(carrera=materia.nivel.carrera)[:1].get()
                        if TipoIncidencia.objects.filter(pk=57).exists():
                            tipo = TipoIncidencia.objects.get(pk=57)
                        correo = str(persona.emailinst) + ',' + tipo.correo + ',' + correocoordinacion.correo
                        mrecep.correoentrega_acta_nivelcerrado(correo, persona)
                        #Obtain client ip address
                        client_address = ip_client_address(request)

                        # Log de ADICIONAR ACTA NIVEL CERRADO
                        LogEntry.objects.log_action(
                            user_id=request.user.pk,
                            content_type_id=ContentType.objects.get_for_model(mrecep).pk,
                            object_id=mrecep.id,
                            object_repr=force_str(mrecep),
                            action_flag=ADDITION,
                            change_message='Acta Entregada Nivel Cerrado (' + client_address + ')')
                        return HttpResponseRedirect('/pro_entrega_acta?error=ACTA ENTREGADA')
                except Exception as e:
                    return HttpResponseRedirect('/pro_entrega_acta?error=' + str(e))
            else:
                return HttpResponseRedirect(
                    '/pro_entrega_acta?error=OCURRIO UN ERROR.. DEBE INGRESAR UN ARCHIVO Y LA OBSERVACION')


    else:
        data = {'title': 'Cronograma de Materias del Profesor'}
        addUserData(request, data)
        if 'action' in request.GET:
            action = request.GET['action']

        else:
            listamaterias=[]
            if 'error' in request.GET:
                data['error'] = request.GET['error']

            periodo = request.session['periodo']
            ret = None
            if 'ret' in request.GET:
                ret = request.GET['ret']
            profesor = Profesor.objects.get(persona=data['persona'])
            #OCastillo 29-03-2022 se excluyen las materias segmento practica
            # materias = Materia.objects.filter((Q(id__in=ProfesorMateria.objects.filter(materia__cerrado=True, profesor=profesor).exclude(segmento__id=TIPOSEGMENTO_PRACT).values('materia'))
            #                                   |Q(id__in=ProfesorMateria.objects.filter(materia__cerrado=True, profesor_aux=profesor.id).exclude(segmento__id=TIPOSEGMENTO_PRACT).values('materia'))), nivel__periodo=periodo, cerrado=True)

            #OCastillo 02-08-2022 incluir materias practicas a excepcion de FASS
            materias = Materia.objects.filter((Q(id__in=ProfesorMateria.objects.filter(materia__cerrado=True, profesor=profesor).values('materia'))
                                              |Q(id__in=ProfesorMateria.objects.filter(materia__cerrado=True, profesor_aux=profesor.id).values('materia'))), nivel__periodo=periodo, cerrado=True)

            for mat in Materia.objects.filter(id__in=materias):
                mat_carrera= Materia.objects.filter(pk=mat.id)[:1].get()
                if ProfesorMateria.objects.filter(materia=mat_carrera,segmento__id=TIPOSEGMENTO_PRACT):
                    if mat_carrera.nivel.carrera.coordinacion_pertenece()!=COORDINACION_UASSS:
                        listamaterias.append(mat_carrera)
                else:
                    if ProfesorMateria.objects.filter(materia=mat_carrera,segmento__id=TIPOSEGMENTO_TEORIA).exists():
                        listamaterias.append(mat_carrera)

            materias=listamaterias

            data['periodo'] = periodo
            data['profesor'] = profesor
            data['materias'] = materias
            data['DEFAULT_PASSWORD'] = DEFAULT_PASSWORD
            data['ret'] = ret if ret else ""
            data['reporte_cronograma_profesor'] = REPORTE_CRONOGRAMA_PROFESOR
            data['VALIDA_MATERIA_APROBADA'] = VALIDA_MATERIA_APROBADA
            data['form'] = RecepcionActaDocenteForm()
            data['formalcance'] = RecepcionActaAlcanceDocenteForm()
            data['formacatanivel'] = RecepcionNivelCerradoDocenteForm()
            return render(request ,"pro_entrega_acta/materiasbs.html" ,  data)

