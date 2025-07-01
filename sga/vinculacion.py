from datetime import datetime, timedelta,date

import os
import json

from django.contrib.admin.models import LogEntry, CHANGE, ADDITION,DELETION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.forms import model_to_dict
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str

from settings import HORAS_VINCULACION, ASIG_VINCULACION, DEFAULT_PASSWORD, VALOR_VINCULACION, MEDIA_ROOT, EMAIL_ACTIVE, INCIDENCIA_PRAC_VINC, NOTA_ESTADO_APROBADO
from sga.forms import VinculacionForm, ParticipanteForm, ParticipanteIndForm, DocenteVincForm, EvidenciaForm, ObservacionForm,\
                      BeneficiariosForm, AprobacionVinculacionForm, ModificaParticipanteForm,GrupoCambioForm,GrupoIndividualCambioForm,\
                      DocumentacionEstudForm
from sga.models import LugarRecaudacion, ActividadVinculacion, EstudianteVinculacion, Nivel, Matricula, Inscripcion, \
                       DocenteVinculacion, EvidenciaVinculacion, ObservacionVinculacion,BeneficiariosVinculacion,Profesor,\
                       Asignatura,RecordAcademico,HistoricoRecordAcademico, convertir_fecha,RolPago, Convenio, Programa, \
                       AprobacionVinculacion, Persona, TipoIncidencia, NivelMalla, InscripcionPracticas, Malla, AsignaturaMalla, \
                       MateriaAsignada, EvaluacionITB,DocumentosVinculacionEstudiantes, TipoConvenio, Egresado, Graduado
from sga.commonviews import addUserData, ip_client_address
from sga.reportes import elimina_tildes
from sga.tasks import send_html_mail

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
    hoy = datetime.today().date()
    if request.method=='POST':
        if 'action' in request.POST:
            action = request.POST['action']
            if action == 'buscar':
                punto = request.POST['punto']
                puntos = ''
                if LugarRecaudacion.objects.filter(puntoventa = punto,activa=True ).exists():
                    for p in LugarRecaudacion.objects.filter(puntoventa = punto ,activa=True):
                        puntos = puntos + ' - ' +p.nombre
                    fac =str( p.numerofact)
                    cre = str(p.numeronotacre)
                    dir = str(p.direccion)

                    return HttpResponse(json.dumps({'result':'ok', "puntos": str(puntos),'ncre':cre,'fac':fac,'dir':dir}),content_type="application/json")
                else:
                    return HttpResponse(json.dumps({'result':'bad'}),content_type="application/json")

            if action == 'buscarpersona':
                persona = request.POST['persona']
                puntos = ''
                if LugarRecaudacion.objects.filter(persona__id = persona,activa=True ).exists():
                    for p in LugarRecaudacion.objects.filter(persona__id = persona ,activa=True):
                        puntos = puntos + ' - ' +p.nombre

                    return HttpResponse(json.dumps({'result':'ok', "puntos": str(puntos)}),content_type="application/json")
                else:
                    return HttpResponse(json.dumps({'result':'bad'}),content_type="application/json")
            elif action =='editarb':
                b = BeneficiariosVinculacion.objects.get(id=request.POST['id'])
                return HttpResponse(json.dumps({'result':'ok', "nombre": str(b.nombre), "identificacion":b.identificacion , "edad":b.edad , "sexo":b.sexo.id , "raza":b.etnia.id , "procedencia":b.procedencia }),content_type="application/json")

            elif action == 'add':
                    f = VinculacionForm(request.POST)
                    # convenio = Convenio.objects.filter(pk=request.POST['convenio'])[:1].get()
                    if f.is_valid():
                        try:
                            if request.POST['ban'] == '1':
                                actividad = ActividadVinculacion(programa=f.cleaned_data['programa'],
                                                         # convenio=f.cleaned_data['convenio'],
                                                         # convenio=convenio,
                                                         nombre = f.cleaned_data['nombre'],
                                                         lugar = f.cleaned_data['lugar'],
                                                         inicio = f.cleaned_data['inicio'],
                                                         fin = f.cleaned_data['fin'],
                                                         objetivo = f.cleaned_data['objetivo'],
                                                         carrera = f.cleaned_data['carrera'],
                                                         lider = f.cleaned_data['lider'])
                                actividad.save()

                                if f.cleaned_data['convenio']:
                                    actividad.convenio_id = f.cleaned_data['convenio_id']
                                    actividad.save()

                                mensaje = 'Adicionado'

                            else:
                                actividad = ActividadVinculacion.objects.get(pk=int(request.POST['actividad']))
                                actividad.programa=f.cleaned_data['programa']
                                # actividad.convenio=f.cleaned_data['convenio']
                                actividad.nombre = f.cleaned_data['nombre']
                                actividad.lugar = f.cleaned_data['lugar']
                                actividad.inicio = f.cleaned_data['inicio']
                                actividad.fin = f.cleaned_data['fin']
                                actividad.objetivo = f.cleaned_data['objetivo']
                                actividad.carrera = f.cleaned_data['carrera']
                                actividad.lider = f.cleaned_data['lider']
                                actividad.save()
                                mensaje = 'Editado'

                            if 'archivo' in request.FILES:
                                    actividad.archivo =  request.FILES['archivo']
                                    actividad.save()

                            if f.cleaned_data['convenio']:
                                actividad.convenio_id = f.cleaned_data['convenio_id']
                                actividad.save()

                        # Log Editar Inscripcion
                            client_address = ip_client_address(request)
                            LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(actividad).pk,
                                object_id       = actividad.id,
                                object_repr     = force_str(actividad),
                                action_flag     = CHANGE,
                                change_message  = mensaje + " Actividad de Vinculacion " +  '(' + client_address + ')' )

                            if mensaje == 'Adicionado':
                                actividad.mail_vinculacion(request.user)

                            return HttpResponseRedirect("/vinculacion")
                        except Exception as ex:
                            if request.POST['ban'] == '1':
                                return HttpResponseRedirect("vinculacion?action=add&error=1",)
                            else:
                                return HttpResponseRedirect("vinculacion?action=editar&error=1&id="+str(request.POST['vinculacion']),)
                    else:
                        if request.POST['ban'] == '1':
                            return HttpResponseRedirect("vinculacion?action=add&error=1",)
                        else:
                            return HttpResponseRedirect("vinculacion?action=editar&error=1&id="+str(request.POST['vinculacion']),)

            elif action == 'add_docuest':
                f = DocumentacionEstudForm(request.POST)
                if f.is_valid():
                    try:
                        if 'archivo' in request.FILES:
                            documentoest = DocumentosVinculacionEstudiantes(fecha = datetime.now().today(),user=request.user)
                            documentoest.save()
                            documentoest.archivo =  request.FILES['archivo']
                            documentoest.save()
                            mensaje = 'Adicionado'
                            # Log Agregar documento vinculacion estudiantes
                            client_address = ip_client_address(request)
                            LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(documentoest).pk,
                                object_id       = documentoest.id,
                                object_repr     = force_str(documentoest),
                                action_flag     = CHANGE,
                                change_message  = mensaje + " documento vinculacion para estudiantes" +  '(' + client_address + ')' )
                            return HttpResponseRedirect("/vinculacion?action=documentosestudiantes")
                        else:
                            return HttpResponseRedirect("/vinculacion?action=documentosestudiantes&error=1")

                    except Exception as ex:
                        pass
                else:
                    mensaje="Debe seleccionar un documento"
                    return HttpResponseRedirect("/vinculacion?action=documentosestudiantes")

            elif action == 'agregard':
                    profesor = Profesor.objects.get(pk=request.POST['id'])
                    op=0
                    vinculacion = ActividadVinculacion.objects.get(pk=request.POST['actividad'])
                    if  RolPago.objects.filter(inicio__lte = convertir_fecha(request.POST['fecha']),fin__gte=convertir_fecha(request.POST['fecha']),activo=True).order_by('-id').exists():
                        r = RolPago.objects.filter(inicio__lte =convertir_fecha(request.POST['fecha']), fin__gte=convertir_fecha(request.POST['fecha']),activo=True).order_by('-id')[:1].get()
                        if r.fechamaxvin >= datetime.now().date():
                           op = 1
                    else:
                        op=1
                    if  op == 1:
                # SE ELIMINA LA PREGUNTA PORQUE AHORA EL INGRESO ES  POR HORA PARA REALIZAR EL PAGO
                # if not DocenteVinculacion.objects.filter(actividad=vinculacion,persona=profesor.persona).exists():
                        docentep = DocenteVinculacion(actividad=vinculacion,
                                                  persona=profesor.persona,
                                                  horas=request.POST['horas'],
                                                  fecha=convertir_fecha(request.POST['fecha']),
                                                  fechaingreso =datetime.now())
                        docentep.save()
                        if "informe" in request.FILES:
                            docentep.informe = request.FILES["informe"]
                            docentep.save()
                        docentep.correo(request.user)

                    # data['matriculas'] = EstudianteVinculacion.objects.filter(vinculacion=vinculacion).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2')
                        return HttpResponse(json.dumps({"result": "ok"}),content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({"result": "bad"}),content_type="application/json")
            elif action == 'addevidencia':
                try:
                    f = EvidenciaForm(request.POST,request.FILES)
                    if f.is_valid():
                        vinculacion = ActividadVinculacion.objects.get(pk=request.POST['id'])
                        evidencia= EvidenciaVinculacion(actividad=vinculacion,
                                                    nombre = request.POST['nombre'],
                                                    foto = request.FILES['archivo'])
                        evidencia.save()
                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(vinculacion).pk,
                            object_id       = vinculacion.id,
                            object_repr     = force_str(vinculacion),
                            action_flag     = CHANGE,
                            change_message  =  " Adicionada Evidencia" +  '(' + client_address + ')' )

                        return HttpResponseRedirect("/vinculacion?action=evidencia&id="+str(vinculacion.id))
                except Exception as ex:
                    pass

            elif action == 'addobservacion':
                try:
                    f = ObservacionForm(request.POST,request.FILES)
                    if f.is_valid():
                        vinculacion = ActividadVinculacion.objects.get(pk=request.POST['id'])
                        observacion= ObservacionVinculacion(actividad=vinculacion,
                                                    observacion = request.POST['observacion'],
                                                    fecha = datetime.now())
                        observacion.save()
                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(vinculacion).pk,
                            object_id       = vinculacion.id,
                            object_repr     = force_str(vinculacion),
                            action_flag     = CHANGE,
                            change_message  =  " Adicionada Observacion" +  '(' + client_address + ')' )
                        return HttpResponseRedirect("/vinculacion?action=observacion&id="+str(vinculacion.id))
                except Exception as ex:
                    pass

            elif action == 'activa':

                   actividad =  ActividadVinculacion.objects.filter(id=request.POST['estid'])[:1].get()
                   fecha_dia=hoy

                   if not actividad.fin >= fecha_dia:
                       if actividad.activo:
                          activo = False
                          mensaje = 'Actividad Inactiva'
                       else:
                           activo = True
                           mensaje = 'Actividad Activa'

                   else:
                       msg='Actividad no ha finalizado, no se puede cambiar estado'
                       return HttpResponse(json.dumps({"result":str(msg)}),content_type="application/json")

                   actividad.activo = activo
                   actividad.save()

                   client_address = ip_client_address(request)
                   #Log de MODIFICAR ACTIVIDAD
                   LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(actividad).pk,
                        object_id       = actividad.id,
                        object_repr     = force_str(actividad),
                        action_flag     =CHANGE,
                        change_message  = mensaje +' cambio estado (' + client_address + ')')
                   return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")

            elif action=='aprobarvinculacion':
                # OCastillo 14-05-2019 aprobacion de vinculacion grupal
                try:
                    estud_vinculacion = EstudianteVinculacion.objects.filter(actividad=request.POST['id']).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2')
                    cant=0
                    sin_aprobar=0
                    estudiantes_sinaprobacion=[]
                    estudiantes_aprobados=[]
                    if request.POST['revisionestud']=='true' and request.POST['revisionproyecto']=='true' and request.POST['revisiondocente']=='true':
                        estudiante=True
                        proyecto=True
                        docente=True
                        for estudiantes in estud_vinculacion:
                            print(estudiantes.inscripcion)
                            #horas = EstudianteVinculacion.objects.filter(inscripcion=estudiantes.inscripcion).exclude(actividad__convenio=None).aggregate(Sum('horas'))['horas__sum']
                            #if AsignaturaMalla.objects.filter(asignatura__nombre__icontains='PREPRO',malla=estudiantes.inscripcion.malla_inscripcion().malla,nivelmalla=estudiantes.nivelmalla).exists():
                                #asig = AsignaturaMalla.objects.get(asignatura__nombre__icontains='PREPRO',malla=estudiantes.inscripcion.malla_inscripcion().malla,nivelmalla=estudiantes.nivelmalla)
                                #if horas >= asig.horas :

                            if AprobacionVinculacion.objects.filter(inscripcion=estudiantes.inscripcion,estudiantevinculacion=estudiantes).exists():
                                aprobacion = AprobacionVinculacion.objects.filter(inscripcion=estudiantes.inscripcion,estudiantevinculacion=estudiantes)[:1].get()
                                if not aprobacion.tiene_aprobacion(estudiantes.actividad):
                                    cant=cant + 1
                                    aprobacion.revisionestudiante= estudiante
                                    aprobacion.revisionproyecto= proyecto
                                    aprobacion.revisiondocente= docente
                                    aprobacion.comentarios=request.POST['comentarios']
                                    aprobacion.usuario = request.user
                                    aprobacion.fecha = datetime.now()
                                    aprobacion.estudiantevinculacion=estudiantes
                                    aprobacion.save()
                                    estudiantes_aprobados.append((estudiantes.inscripcion.persona.nombre_completo(),elimina_tildes(estudiantes.inscripcion.carrera.nombre)))
                                    #Obtain client ip address
                                    client_address = ip_client_address(request)
                                    # Log de Aprobacion Vinculacion
                                    LogEntry.objects.log_action(
                                     user_id         = request.user.pk,
                                     content_type_id = ContentType.objects.get_for_model(estudiantes.inscripcion).pk,
                                     object_id       = estudiantes.inscripcion.id,
                                     object_repr     = force_str(estudiantes.inscripcion),
                                     action_flag     = ADDITION,
                                     change_message  = 'Aprobacion Vinculacion en grupo (' + client_address + ')' + elimina_tildes(estudiantes.inscripcion) )

                            else:
                                cant=cant + 1
                                aprobacion = AprobacionVinculacion(inscripcion_id = estudiantes.inscripcion.id,
                                                                   revisionestudiante = estudiante,
                                                                   revisionproyecto = proyecto,
                                                                   revisiondocente = docente,
                                                                   comentarios = request.POST['comentarios'],
                                                                   usuario = request.user,
                                                                   fecha = datetime.now(),
                                                                   estudiantevinculacion=estudiantes)
                                aprobacion.save()
                                estudiantes_aprobados.append((estudiantes.inscripcion.persona.nombre_completo(),elimina_tildes(estudiantes.inscripcion.carrera.nombre)))

                                #Obtain client ip address
                                client_address = ip_client_address(request)
                                # Log de Aprobacion Vinculacion
                                LogEntry.objects.log_action(
                                 user_id         = request.user.pk,
                                 content_type_id = ContentType.objects.get_for_model(estudiantes.inscripcion).pk,
                                 object_id       = estudiantes.inscripcion.id,
                                 object_repr     = force_str(estudiantes.inscripcion),
                                 action_flag     = ADDITION,
                                 change_message  = 'Aprobacion Vinculacion en grupo (' + client_address + ')' + elimina_tildes(estudiantes.inscripcion) )


                            if not aprobacion.inscripcion.malla_inscripcion().malla.nueva_malla:
                                asig = Asignatura.objects.get(pk=ASIG_VINCULACION)
                                horas_va1= AprobacionVinculacion.objects.filter(estudiantevinculacion__inscripcion=estudiantes.inscripcion,revisionestudiante=True,revisionproyecto=True,revisiondocente=True).aggregate(Sum('estudiantevinculacion__horas'))['estudiantevinculacion__horas__sum'] if AprobacionVinculacion.objects.filter(estudiantevinculacion__inscripcion=estudiantes.inscripcion,revisionestudiante=True,revisionproyecto=True,revisiondocente=True).exists() else 0
                                if (horas_va1 if horas_va1!=None else 0 )>= HORAS_VINCULACION :
                                    if aprobacion.tiene_aprobacion(estudiantes.actividad):
                                        fechaaprobacion=aprobacion.fecha.date()
                                    else:
                                        fechaaprobacion=datetime.now().date()
                                    if HistoricoRecordAcademico.objects.filter(inscripcion=estudiantes.inscripcion,asignatura=asig).exists():
                                        historico = HistoricoRecordAcademico.objects.filter(inscripcion=estudiantes.inscripcion,asignatura=asig)[:1].get()
                                        historico.nota=100
                                        historico.asistencia=100
                                        historico.fecha=datetime.now().date()
                                        historico.aprobada=True
                                        historico.convalidacion=False
                                        historico.pendiente=False
                                    else:
                                        historico = HistoricoRecordAcademico(inscripcion=estudiantes.inscripcion,
                                                                    asignatura=asig,
                                                                    nota=100,
                                                                    asistencia=100,
                                                                    fecha=fechaaprobacion,
                                                                    aprobada=True,
                                                                    convalidacion=False,
                                                                    pendiente=False)
                                    historico.save()

                                    if RecordAcademico.objects.filter(inscripcion=estudiantes.inscripcion,asignatura=asig).exists():
                                        record = RecordAcademico.objects.filter(inscripcion=estudiantes.inscripcion,asignatura=asig)[:1].get()
                                        record.nota=100
                                        record.asistencia=100
                                        record.fecha=datetime.now().date()
                                        record.aprobada=True
                                        record.convalidacion=False
                                        record.pendiente=False
                                    else:
                                        record = RecordAcademico(inscripcion=estudiantes.inscripcion, asignatura=asig,
                                                            nota=100, asistencia=100,
                                                            fecha=fechaaprobacion, aprobada=True,
                                                            convalidacion=False, pendiente=False)
                                    record.save()
                                    client_address = ip_client_address(request)
                                    # aprobacion.correo_aprobacionvinculacion(request.user,'SE HA APROBADO Y AGREGADO LA NOTA DE VINCULACION CON LA COMUNIDAD',estudiantes_aprobados)
                                    # Log de Aprobacion Vinculacion
                                    LogEntry.objects.log_action(
                                     user_id         = request.user.pk,
                                     content_type_id = ContentType.objects.get_for_model(estudiantes.inscripcion).pk,
                                     object_id       = estudiantes.inscripcion.id,
                                     object_repr     = force_str(estudiantes.inscripcion),
                                     action_flag     = ADDITION,
                                     change_message  = 'Adicionada Nota de Vinculacion Grupal (' + client_address + ')' + elimina_tildes(estudiantes.inscripcion))

                            #else:
                             #   sin_aprobar=sin_aprobar+1
                             #   estudiantes_sinaprobacion.append((estudiantes.inscripcion.persona.nombre_completo(),str(horas)))



                        if EMAIL_ACTIVE:
                            # correo_aprobacionvinculacion(request.user,'SE HA APROBADO Y AGREGADO LA NOTA DE VINCULACION CON LA COMUNIDAD',estudiantes_aprobados)
                            if len(estudiantes_aprobados)>0:
                                correo_aprobacionvinculacion(request.user,'SE HA APROBADO VINCULACION CON LA COMUNIDAD',estudiantes_aprobados)
                            if len(estudiantes_sinaprobacion)>0:
                                # no_aprobacion_vinculacion('ESTUDIANTES QUE NO SE HA APROBADO NI AGREGADO LA NOTA DE VINCULACION CON LA COMUNIDAD',estudiantes_sinaprobacion,request.user)
                                no_aprobacion_vinculacion('ESTUDIANTES QUE NO SE HA APROBADO VINCULACION CON LA COMUNIDAD',estudiantes_sinaprobacion,request.user)
                        return HttpResponse(json.dumps({"result":"ok","estud":str(cant),"sin_aprob":str(sin_aprobar)}),content_type="application/json")
                    else:
                        if request.POST['revisionestud']=='true':
                            estudiante=True
                        else:
                            estudiante=False

                        if request.POST['revisionproyecto']=='true':
                            proyecto=True
                        else:
                            proyecto=False

                        if request.POST['revisiondocente']=='true':
                            docente=True
                        else:
                            docente=False

                        for estudiantes in estud_vinculacion:
                            if AprobacionVinculacion.objects.filter(inscripcion=estudiantes.inscripcion).exists():
                                aprobacion = AprobacionVinculacion.objects.filter(inscripcion=estudiantes.inscripcion)[:1].get()
                                if not aprobacion.tiene_aprobacion(estudiantes.actividad):
                                    aprobacion.revisionestudiante= estudiante
                                    aprobacion.revisionproyecto= proyecto
                                    aprobacion.revisiondocente= docente
                                    aprobacion.comentarios=request.POST['comentarios']
                                    aprobacion.usuario = request.user
                                    aprobacion.fecha = datetime.now()
                                    aprobacion.estudiantevinculacion=estudiante
                                    aprobacion.save()
                                    #Obtain client ip address
                                    client_address = ip_client_address(request)

                                    # Log de Revision Vinculacion
                                    LogEntry.objects.log_action(
                                     user_id         = request.user.pk,
                                     content_type_id = ContentType.objects.get_for_model(estudiantes.inscripcion).pk,
                                     object_id       = estudiantes.inscripcion.id,
                                     object_repr     = force_str(estudiantes.inscripcion),
                                     action_flag     = CHANGE,
                                     change_message  = 'Revision Vinculacion en grupo (' + client_address + ')' +elimina_tildes(estudiantes.inscripcion))
                            else:
                                aprobacion = AprobacionVinculacion(inscripcion_id = estudiantes.inscripcion.id,
                                                                   revisionestudiante = estudiante,
                                                                   revisionproyecto = proyecto,
                                                                   revisiondocente = docente,
                                                                   comentarios = request.POST['comentarios'],
                                                                   usuario = request.user,
                                                                   fecha = datetime.now(),
                                                                   estudiantevinculacion=estudiantes)
                                aprobacion.save()
                                #Obtain client ip address
                                client_address = ip_client_address(request)

                                # Log de Revision Vinculacion
                                LogEntry.objects.log_action(
                                 user_id         = request.user.pk,
                                 content_type_id = ContentType.objects.get_for_model(estudiantes.inscripcion).pk,
                                 object_id       = estudiantes.inscripcion.id,
                                 object_repr     = force_str(estudiantes.inscripcion),
                                 action_flag     = CHANGE,
                                 change_message  = 'Revision Vinculacion en grupo (' + client_address + ')' +elimina_tildes(estudiantes.inscripcion))

                        return HttpResponse(json.dumps({"result":"ok2","estud":str(cant)}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

            return HttpResponseRedirect("/vinculacion")
    else:
        data = {'title': 'Actividad de Vinculacion'}
        addUserData(request,data)
        try:
            if 'action' in request.GET:
                action = request.GET['action']

                if action == 'add':
                    data['form'] = VinculacionForm(initial={"inicio":datetime.now().date(),"fin":datetime.now().date()})
                    if 'error' in request.GET:
                        data['error'] = 1
                    data['ban'] =1
                    return render(request ,"vinculacion/add.html" ,  data)

                elif action == 'documentosestudiantes':
                    data['documento'] = DocumentosVinculacionEstudiantes.objects.all().order_by('fecha')
                    data['form'] = DocumentacionEstudForm(initial={"fecha":datetime.now().date()})
                    if 'error' in request.GET:
                        data['error'] = "Debe seleccionar documento"
                    return render(request ,"vinculacion/documentosestudiantes.html" ,  data)

                elif action == 'participantes':
                    try:
                        data = {'title': 'Estudiantes'}
                        addUserData(request,data)
                        data['vinculacion'] = ActividadVinculacion.objects.get(pk=request.GET['id'])
                        actividad = ActividadVinculacion.objects.get(pk=request.GET['id'])
                        data['mat_vinculacion']=ASIG_VINCULACION
                        data['participantes'] = EstudianteVinculacion.objects.filter(actividad=data['vinculacion']).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2')
                        inscritos = EstudianteVinculacion.objects.filter(actividad=data['vinculacion']).values('inscripcion').distinct('inscripcion__persona__apellido1','inscripcion__persona__apellido2').order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2')
                        data['record'] = RecordAcademico.objects.filter(inscripcion__id__in=inscritos,asignatura=ASIG_VINCULACION).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2')
                        if 's' in request.GET:
                            search = request.GET['s']
                            if search:
                                ss = search.split(' ')
                                while '' in ss:
                                    ss.remove('')
                                if len(ss) == 1:
                                    data['participantes'] = EstudianteVinculacion.objects.filter(Q(actividad=data['vinculacion'],inscripcion__persona__apellido1__icontains=search)|Q(actividad=data['vinculacion'],inscripcion__persona__apellido2__icontains=search)|Q(actividad=data['vinculacion'],inscripcion__persona__nombres__icontains=search)).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2')
                                    inscritos = EstudianteVinculacion.objects.filter(Q(actividad=data['vinculacion'],inscripcion__persona__apellido1__icontains=search)|Q(actividad=data['vinculacion'],inscripcion__persona__apellido2__icontains=search)|Q(actividad=data['vinculacion'],inscripcion__persona__nombres__icontains=search)).values('inscripcion').distinct('inscripcion')
                                else:
                                    data['participantes'] = EstudianteVinculacion.objects.filter(Q(inscripcion__persona__apellido1__icontains=ss[0]) &Q(inscripcion__persona__apellido2__icontains=ss[1]) ,actividad=data['vinculacion']).order_by('inscripcion__persona__apellido1', 'inscripcion__persona__apellido2')
                                    inscritos = EstudianteVinculacion.objects.filter(Q(inscripcion__persona__apellido1__icontains=ss[0]) &Q(inscripcion__persona__apellido2__icontains=ss[1]) ,actividad=data['vinculacion']).values('inscripcion').distinct('inscripcion')
                            data['record'] = RecordAcademico.objects.filter(inscripcion__id__in=inscritos,asignatura=ASIG_VINCULACION)
                            data['search'] = search

                        form = ParticipanteForm()
                        # malla = Malla.objects.get(carrera=actividad.carrera, vigente=True)
                        # form.nivel_malla(malla)
                        data['form'] = form

                        form2 = ParticipanteIndForm()
                        # malla2 = Malla.objects.get(carrera=actividad.carrera, vigente=True)
                        # form2.nivel_malla(malla2)

                        data['form2'] = form2
                        data['h_vinculacion']= HORAS_VINCULACION
                        data['aprobargrupo'] = AprobacionVinculacionForm()
                        data['formod'] = ModificaParticipanteForm()
                        data['formCambioNivel'] = GrupoCambioForm()
                        data['formCambioNivelIndividual'] = GrupoIndividualCambioForm()

                        return render(request ,"vinculacion/participantes.html" ,  data)
                    except Exception as ex:
                        print(ex)

                elif action == 'evidencia':
                    data = {'title': 'Evidencias'}
                    addUserData(request,data)
                    data['vinculacion'] = ActividadVinculacion.objects.get(pk=request.GET['id'])
                    data['evidencia'] = EvidenciaVinculacion.objects.filter(actividad=data['vinculacion'])
                    if 's' in request.GET:
                        search = request.GET['s']
                        data['evidencia'] = EvidenciaVinculacion.objects.filter(Q(actividad=data['vinculacion'],nombre__icontains=search)|Q(actividad=data['vinculacion'],nombre__icontains=search)|Q(actividad=data['vinculacion'],nombre__icontains=search)).order_by('nombre')
                        data['search'] = search
                    data['form'] = EvidenciaForm()
                    return render(request ,"vinculacion/evidencia.html" ,  data)

                elif action == 'observacion':
                    data['vinculacion'] = ActividadVinculacion.objects.get(pk=request.GET['id'])
                    data['observacion'] = ObservacionVinculacion.objects.filter(actividad=data['vinculacion'])
                    data['form'] = ObservacionForm()
                    return render(request ,"vinculacion/observacion.html" ,  data)

                elif action == 'docentes':
                    data = {'title': 'Docentes Vinculacion'}
                    addUserData(request,data)
                    data['h_vinculacion']= HORAS_VINCULACION
                    data['actividad'] = ActividadVinculacion.objects.get(pk=request.GET['id'])
                    data['docente'] = DocenteVinculacion.objects.filter(actividad=data['actividad']).order_by('persona__apellido1','persona__apellido2')
                    if 's' in request.GET:
                        search = request.GET['s']
                        data['docente'] = DocenteVinculacion.objects.filter(Q(actividad=data['actividad'],persona__apellido1__icontains=search)|Q(actividad=data['actividad'],persona__apellido2__icontains=search)|Q(actividad=data['actividad'],docente__persona__nombres__icontains=search)).order_by('persona__apellido1','persona__apellido2')
                        data['search'] = search
                    data['form2'] = DocenteVincForm(initial={'fecha':datetime.now().date()})
                    if 'error' in request.GET:
                        data['error']= request.GET['error']
                    data['DEFAULT_PASSWORD']=DEFAULT_PASSWORD
                    data['VALOR_VINCULACION']=VALOR_VINCULACION
                    return render(request ,"vinculacion/docentes.html" ,  data)

                elif action == 'beneficiarios':
                    data['vinculacion'] = ActividadVinculacion.objects.get(pk=request.GET['id'])
                    data['beneficiarios'] = BeneficiariosVinculacion.objects.filter(actividad=data['vinculacion']).order_by('nombre')
                    if 's' in request.GET:
                        search = request.GET['s']
                        data['beneficiarios'] = BeneficiariosVinculacion.objects.filter(Q(actividad=data['vinculacion'],identificacion=search)|Q(actividad=data['vinculacion'],nombre__icontains=search))
                        data['search'] = search
                    data['form2'] = BeneficiariosForm()
                    return render(request ,"vinculacion/beneficiarios.html" ,  data)

                elif action == 'buscar':
                    try:
                        horas_v = 0
                        horas_va = 0

                        data['nivel'] = Nivel.objects.get(pk=request.GET['id'])
                        idnivel =NivelMalla.objects.get(pk=int(request.GET['idnivel']))
                        puedeingresar=True
                        # asigmalla= AsignaturaMalla.objects.get(nivelmalla=idnivel,articulada=True)
                        #
                        # materiasig = MateriaAsignada.objects.filter()

                        vinculacion = ActividadVinculacion.objects.get(pk=request.GET['vinculacion'])
                        data['matriculas'] = Matricula.objects.filter(nivel=data['nivel']).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2')
                        horas_v = int(request.GET['horas'])
                        for m in Matricula.objects.filter(nivel=data['nivel']).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2'):
                            # print((m))
                            # Validacion para las horas de Vinculacion OC

                            if  AsignaturaMalla.objects.filter(malla=m.inscripcion.malla_inscripcion().malla,nivelmalla=idnivel,articulada=True).exists():
                                idmateriarticulaasignatura = AsignaturaMalla.objects.filter(malla=m.inscripcion.malla_inscripcion().malla,nivelmalla=idnivel,articulada=True).values('asignatura__id')
                                idmateriasignada=MateriaAsignada.objects.filter(matricula__inscripcion=m.inscripcion,materia__asignatura__id__in=idmateriarticulaasignatura).values('id')
                                eva =  EvaluacionITB.objects.filter(materiaasignada__id__in=idmateriasignada,estado__id=NOTA_ESTADO_APROBADO).values('materiaasignada__materia__asignatura__id')
                                record= RecordAcademico.objects.filter(inscripcion=m.inscripcion,asignatura__id__in=idmateriarticulaasignatura,aprobada=True).exclude(asignatura__id__in=eva)
                                totalmateriaaprobada= len(eva)+len(record)

                                if len(idmateriarticulaasignatura)==totalmateriaaprobada:
                                    puedeingresar=True
                                else:
                                    puedeingresar=False

                            if puedeingresar==True:

                                if not m.inscripcion.tiene_malla_nueva():
                                    horas_va= m.inscripcion.estudiantevinculacion_set.all().aggregate(Sum('horas'))['horas__sum'] if m.inscripcion.estudiantevinculacion_set.all().exists() else 0
                                    if (horas_v + horas_va)<= HORAS_VINCULACION :
                                        participante = EstudianteVinculacion(actividad=vinculacion,
                                                                  inscripcion=m.inscripcion,
                                                                  horas=request.GET['horas'])
                                        participante.save()
                                    else:

                                        vinculacion.mail_vinculacionotro(request.user,"ESTUDIANTE NO SE HA AGREGADO ACTIVIDAD DE VINCULACION PORQUE LAS HORAS SON MAYORES A LAS HORAS ASIGNADAS "+elimina_tildes(m.inscripcion.persona.nombre_completo_inverso()))
                                        pass

                                else:
                                    if m.inscripcion.tiene_vinculacion():
                                        # OCU 16-08-2018 sin validacion de horas ahora los estudiantes pueden tener varias actividades
                                        #horas_va=horas_v+ m.inscripcion.estudiantevinculacion_set.all().aggregate(Sum('horas'))['horas__sum']
                                        horas_va=horas_v+ m.inscripcion.estudiantevinculacion_set.filter(nivelmalla__id=idnivel.id).aggregate(Sum('horas'))['horas__sum'] if EstudianteVinculacion.objects.filter(inscripcion=m.inscripcion,nivelmalla__id=idnivel.id).exists() else 0
                                        nivelingreso=NivelMalla.objects.filter(id__in=AsignaturaMalla.objects.filter(Q(asignatura__nombre__icontains='PREPRO',malla=m.inscripcion.malla_inscripcion().malla)|Q(asignatura__nombre__icontains='COMUNI',malla=m.inscripcion.malla_inscripcion().malla)).values('nivelmalla'),promediar=True)
                                        if AsignaturaMalla.objects.filter(Q(asignatura__nombre__icontains='PREPRO',malla=m.inscripcion.malla_inscripcion().malla,nivelmalla=idnivel)|Q(asignatura__nombre__icontains='COMUNI',malla=m.inscripcion.malla_inscripcion().malla,nivelmalla=idnivel)).exists():
                                            asig = AsignaturaMalla.objects.get(Q(asignatura__nombre__icontains='PREPRO',malla=m.inscripcion.malla_inscripcion().malla,nivelmalla=idnivel)|Q(asignatura__nombre__icontains='COMUNI',malla=m.inscripcion.malla_inscripcion().malla,nivelmalla=idnivel))
                                            if horas_va > asig.horas :
                                                act_vin = EstudianteVinculacion.objects.filter(inscripcion=m.inscripcion)[:1].get()
                                                carrera= act_vin.inscripcion.carrera
                                                act_vin.tiene_actvinculacion(request.user,'ESTUDIANTE NO SE HA AGREGADO ACTIVIDAD DE VINCULACION PORQUE LAS HORAS SON MAYORES A LAS HORAS ASIGNADAS EN ESE NIVEL',horas_va,carrera)
                                            else:

                                                if not nivelingreso.filter(id=int(request.GET['idnivel'])).exists():
                                                    act_vin.tiene_actvinculacion(request.user,'NO PUEDE INGRESAR VINCULACION EN EL NIVEL PORQUE EN LA MALLA NO TIENE ASIGNADO ESE NIVEL',0,carrera)

                                                else:

                                                    if  InscripcionPracticas.objects.filter(inscripcion=m.inscripcion,nivelmalla__id=idnivel.id).exists():
                                                        act_vin.tiene_actvinculacion(request.user,'YA TIENE INGRESADA LAS PRACTICAS EN ESE NIVEL',0,carrera)
                                                    else:

                                                        participante = EstudianteVinculacion(actividad=vinculacion,
                                                                                  inscripcion=m.inscripcion,
                                                                                  horas=request.GET['horas'],nivelmalla=idnivel)
                                                        participante.save()
                                                        #
                                                        # if request.GET['nivelmalla_id']:
                                                        #     participante.nivelmalla_id=request.GET['nivelmalla_id']

                                                        horas = EstudianteVinculacion.objects.filter(inscripcion=participante.inscripcion).exclude(actividad__convenio=None).aggregate(Sum('horas'))['horas__sum']

                                                    # if ASIG_VINCULACION > 0 :
                                                    #     asig = Asignatura.objects.get(pk=ASIG_VINCULACION)
                                                    #
                                                    #     if HistoricoRecordAcademico.objects.filter(inscripcion=participante.inscripcion,asignatura=asig).exists():
                                                    #         historico = HistoricoRecordAcademico.objects.filter(inscripcion=participante.inscripcion,asignatura=asig)[:1].get()
                                                    #         historico.nota=100
                                                    #         historico.asistencia=100
                                                    #         historico.fecha=datetime.now().date()
                                                    #         historico.aprobada=True
                                                    #         historico.convalidacion=False
                                                    #         historico.pendiente=False
                                                    #     else:
                                                    #
                                                    #         historico = HistoricoRecordAcademico(inscripcion=participante.inscripcion,
                                                    #                                     asignatura=asig,
                                                    #                                     nota=100,
                                                    #                                     asistencia=100,
                                                    #                                     fecha=datetime.now().date(),
                                                    #                                     aprobada=True,
                                                    #                                     convalidacion=False,
                                                    #                                     pendiente=False)
                                                    #     historico.save()
                                                    #
                                                    #     if RecordAcademico.objects.filter(inscripcion=participante.inscripcion,asignatura=asig).exists():
                                                    #         record = RecordAcademico.objects.filter(inscripcion=participante.inscripcion,asignatura=asig)[:1].get()
                                                    #         record.nota=100
                                                    #         record.asistencia=100
                                                    #         record.fecha=datetime.now().date()
                                                    #         record.aprobada=True
                                                    #         record.convalidacion=False
                                                    #         record.pendiente=False
                                                    #     else:
                                                    #         record = RecordAcademico(inscripcion=participante.inscripcion, asignatura=asig,
                                                    #                             nota=100, asistencia=100,
                                                    #                             fecha=datetime.now().date(), aprobada=True,
                                                    #                             convalidacion=False, pendiente=False)
                                                    #     record.save()
                                                    #
                                                    #     if horas < HORAS_VINCULACION :
                                                    #         record.delete()
                                                    #         historico.delete()
                                                    #     else:
                                                        carrera = participante.inscripcion.carrera.nombre
                                                        actividad=participante.actividad.nombre
                                                        participante.correo_vinculacion(request.user,'SE HA AGREGADO ACTIVIDAD DE VINCULACION CON LA COMUNIDAD',horas,carrera,actividad)

                                                        #Obtain client ip address
                                                        client_address = ip_client_address(request)
                                                        # Log de ADICIONAR VINCULACION
                                                        LogEntry.objects.log_action(
                                                            user_id         = request.user.pk,
                                                            content_type_id = ContentType.objects.get_for_model(m.inscripcion).pk,
                                                            object_id       = m.inscripcion.id,
                                                            object_repr     = force_str(vinculacion),
                                                            action_flag     = ADDITION,
                                                            change_message  = 'Adicionado Estudiante  Actividad (' + client_address + ')' )
                                        else:
                                            vinculacion.mail_vinculacionotro(request.user,"NO SE PUEDE INGRESAR VINCULACION PORQUE NO TIENE ASIGANDO EL NIVEL "+elimina_tildes(m.inscripcion.persona.nombre_completo_inverso()))


                                    else:
                                        if not EstudianteVinculacion.objects.filter(actividad=vinculacion,inscripcion=m.inscripcion,nivelmalla__id=idnivel.id).exists():
                                            if not InscripcionPracticas.objects.filter(inscripcion=m.inscripcion,nivelmalla__id=idnivel.id).exists():

                                                if not m.inscripcion.tiene_malla_nueva():
                                                    horas_va= m.inscripcion.estudiantevinculacion_set.all().aggregate(Sum('horas'))['horas__sum']
                                                    if (horas_v + horas_va)<= HORAS_VINCULACION :
                                                        participante = EstudianteVinculacion(actividad=vinculacion,
                                                                                  inscripcion=m.inscripcion,
                                                                                  horas=request.GET['horas'])
                                                        participante.save()
                                                    else:

                                                        vinculacion.mail_vinculacionotro(request.user,"ESTUDIANTE NO SE HA AGREGADO ACTIVIDAD DE VINCULACION PORQUE LAS HORAS SON MAYORES A LAS HORAS ASIGNADAS "+elimina_tildes(m.inscripcion.persona.nombre_completo_inverso()))
                                                        pass
                                                else:

                                                    horas_va=horas_v+ m.inscripcion.estudiantevinculacion_set.filter(nivelmalla__id=idnivel.id).aggregate(Sum('horas'))['horas__sum'] if EstudianteVinculacion.objects.filter(inscripcion=m.inscripcion,nivelmalla__id=idnivel.id).exists() else 0
                                                    nivelingreso=NivelMalla.objects.filter(id__in=AsignaturaMalla.objects.filter(Q(asignatura__nombre__icontains='PREPRO',malla=m.inscripcion.malla_inscripcion().malla)|Q(asignatura__nombre__icontains='COMUNI',malla=m.inscripcion.malla_inscripcion().malla)).values('nivelmalla'),promediar=True)
                                                    if AsignaturaMalla.objects.filter(Q(asignatura__nombre__icontains='PREPRO',malla=m.inscripcion.malla_inscripcion().malla,nivelmalla=idnivel)|Q(asignatura__nombre__icontains='COMUNI',malla=m.inscripcion.malla_inscripcion().malla,nivelmalla=idnivel)).exists():
                                                        asig = AsignaturaMalla.objects.get(Q(asignatura__nombre__icontains='PREPRO',malla=m.inscripcion.malla_inscripcion().malla,nivelmalla=idnivel)|Q(asignatura__nombre__icontains='COMUNI',malla=m.inscripcion.malla_inscripcion().malla,nivelmalla=idnivel))
                                                        if horas_va > asig.horas :
                                                            act_vin = EstudianteVinculacion.objects.filter(inscripcion=m.inscripcion)[:1].get()
                                                            carrera= act_vin.inscripcion.carrera
                                                            act_vin.tiene_actvinculacion(request.user,'ESTUDIANTE NO SE HA AGREGADO ACTIVIDAD DE VINCULACION PORQUE LAS HORAS SON MAYORES A LAS HORAS ASIGNADAS EN ESE NIVEL',horas_va,carrera)
                                                        else:

                                                            if not nivelingreso.filter(id=int(request.GET['idnivel'])).exists():
                                                                act_vin.tiene_actvinculacion(request.user,'NO PUEDE INGRESAR VINCULACION EN EL NIVEL PORQUE EN LA MALLA NO TIENE ASIGNADO ESE NIVEL',0,carrera)

                                                            else:

                                                                if  InscripcionPracticas.objects.filter(inscripcion=m.inscripcion,nivelmalla__id=idnivel.id).exists():
                                                                    act_vin.tiene_actvinculacion(request.user,'YA TIENE INGRESADA LAS PRACTICAS EN ESE NIVEL',0,carrera)
                                                                else:

                                                                    participante = EstudianteVinculacion(actividad=vinculacion,
                                                                                              inscripcion=m.inscripcion,
                                                                                              horas=request.GET['horas'],nivelmalla=idnivel)
                                                                    participante.save()
                                                                    #
                                                                    # if request.GET['nivelmalla_id']:
                                                                    #     participante.nivelmalla_id=request.GET['nivelmalla_id']

                                                                    horas = EstudianteVinculacion.objects.filter(inscripcion=participante.inscripcion).exclude(actividad__convenio=None).aggregate(Sum('horas'))['horas__sum']

                                                                # if ASIG_VINCULACION > 0 :
                                                                #     asig = Asignatura.objects.get(pk=ASIG_VINCULACION)
                                                                #
                                                                #     if HistoricoRecordAcademico.objects.filter(inscripcion=participante.inscripcion,asignatura=asig).exists():
                                                                #         historico = HistoricoRecordAcademico.objects.filter(inscripcion=participante.inscripcion,asignatura=asig)[:1].get()
                                                                #         historico.nota=100
                                                                #         historico.asistencia=100
                                                                #         historico.fecha=datetime.now().date()
                                                                #         historico.aprobada=True
                                                                #         historico.convalidacion=False
                                                                #         historico.pendiente=False
                                                                #     else:
                                                                #
                                                                #         historico = HistoricoRecordAcademico(inscripcion=participante.inscripcion,
                                                                #                                     asignatura=asig,
                                                                #                                     nota=100,
                                                                #                                     asistencia=100,
                                                                #                                     fecha=datetime.now().date(),
                                                                #                                     aprobada=True,
                                                                #                                     convalidacion=False,
                                                                #                                     pendiente=False)
                                                                #     historico.save()
                                                                #
                                                                #     if RecordAcademico.objects.filter(inscripcion=participante.inscripcion,asignatura=asig).exists():
                                                                #         record = RecordAcademico.objects.filter(inscripcion=participante.inscripcion,asignatura=asig)[:1].get()
                                                                #         record.nota=100
                                                                #         record.asistencia=100
                                                                #         record.fecha=datetime.now().date()
                                                                #         record.aprobada=True
                                                                #         record.convalidacion=False
                                                                #         record.pendiente=False
                                                                #     else:
                                                                #         record = RecordAcademico(inscripcion=participante.inscripcion, asignatura=asig,
                                                                #                             nota=100, asistencia=100,
                                                                #                             fecha=datetime.now().date(), aprobada=True,
                                                                #                             convalidacion=False, pendiente=False)
                                                                #     record.save()
                                                                #
                                                                #     if horas < HORAS_VINCULACION :
                                                                #         record.delete()
                                                                #         historico.delete()
                                                                #     else:
                                                                    carrera = participante.inscripcion.carrera.nombre
                                                                    actividad=participante.actividad.nombre
                                                                    participante.correo_vinculacion(request.user,'SE HA AGREGADO ACTIVIDAD DE VINCULACION CON LA COMUNIDAD',horas,carrera,actividad)

                                                                    #Obtain client ip address
                                                                    client_address = ip_client_address(request)
                                                                    # Log de ADICIONAR VINCULACION
                                                                    LogEntry.objects.log_action(
                                                                        user_id         = request.user.pk,
                                                                        content_type_id = ContentType.objects.get_for_model(m.inscripcion).pk,
                                                                        object_id       = m.inscripcion.id,
                                                                        object_repr     = force_str(vinculacion),
                                                                        action_flag     = ADDITION,
                                                                        change_message  = 'Adicionado Estudiante  Actividad (' + client_address + ')' )
                                                    else:
                                                        vinculacion.mail_vinculacionotro(request.user,"NO SE PUEDE INGRESAR VINCULACION PORQUE NO TIENE ASIGANDO EL NIVEL "+elimina_tildes(m.inscripcion.persona.nombre_completo_inverso()))
                            else:
                                vinculacion.mail_vinculacionotro(request.user,"NO SE HA AGREGADO LA ACTIVIDAD - PORQUE NO TIENE MATERIA ARTICULADA APROBADA EN ESTE NIVEL "+elimina_tildes(m.inscripcion.persona.nombre_completo_inverso()))

                        # data['matriculas'] = EstudianteVinculacion.objects.filter(vinculacion=vinculacion).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2')
                        return HttpResponseRedirect("/vinculacion?action=participantes&id="+str(vinculacion.id))

                    except Exception as e:
                        return HttpResponseRedirect('/?info='+str(e))


                elif action == 'buscarsinarticulada':
                    try:
                        horas_v = 0
                        horas_va = 0

                        data['nivel'] = Nivel.objects.get(pk=request.GET['id'])
                        idnivel =NivelMalla.objects.get(pk=int(request.GET['idnivel']))
                        puedeingresar=True
                        # asigmalla= AsignaturaMalla.objects.get(nivelmalla=idnivel,articulada=True)
                        #
                        # materiasig = MateriaAsignada.objects.filter()

                        vinculacion = ActividadVinculacion.objects.get(pk=request.GET['vinculacion'])
                        data['matriculas'] = Matricula.objects.filter(nivel=data['nivel']).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2')
                        horas_v = int(request.GET['horas'])
                        for m in Matricula.objects.filter(nivel=data['nivel']).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2'):
                            # print((m))
                            # Validacion para las horas de Vinculacion OC


                            if not m.inscripcion.tiene_malla_nueva():
                                horas_va= m.inscripcion.estudiantevinculacion_set.all().aggregate(Sum('horas'))['horas__sum'] if m.inscripcion.estudiantevinculacion_set.all().exists() else 0
                                if (horas_v + horas_va)<= HORAS_VINCULACION :
                                    participante = EstudianteVinculacion(actividad=vinculacion,
                                                              inscripcion=m.inscripcion,
                                                              horas=request.GET['horas'])
                                    participante.save()
                                else:

                                    vinculacion.mail_vinculacionotro(request.user,"ESTUDIANTE NO SE HA AGREGADO ACTIVIDAD DE VINCULACION PORQUE LAS HORAS SON MAYORES A LAS HORAS ASIGNADAS "+elimina_tildes(m.inscripcion.persona.nombre_completo_inverso()))
                                    pass

                            else:
                                if m.inscripcion.tiene_vinculacion():
                                    # OCU 16-08-2018 sin validacion de horas ahora los estudiantes pueden tener varias actividades
                                    #horas_va=horas_v+ m.inscripcion.estudiantevinculacion_set.all().aggregate(Sum('horas'))['horas__sum']
                                    horas_va=horas_v+ m.inscripcion.estudiantevinculacion_set.filter(nivelmalla__id=idnivel.id).aggregate(Sum('horas'))['horas__sum'] if EstudianteVinculacion.objects.filter(inscripcion=m.inscripcion,nivelmalla__id=idnivel.id).exists() else 0
                                    nivelingreso=NivelMalla.objects.filter(id__in=AsignaturaMalla.objects.filter(Q(asignatura__nombre__icontains='PREPRO',malla=m.inscripcion.malla_inscripcion().malla)|Q(asignatura__nombre__icontains='COMUNI',malla=m.inscripcion.malla_inscripcion().malla)).values('nivelmalla'),promediar=True)
                                    if AsignaturaMalla.objects.filter(Q(asignatura__nombre__icontains='PREPRO',malla=m.inscripcion.malla_inscripcion().malla,nivelmalla=idnivel)|Q(asignatura__nombre__icontains='COMUNI',malla=m.inscripcion.malla_inscripcion().malla,nivelmalla=idnivel)).exists():
                                        asig = AsignaturaMalla.objects.get(Q(asignatura__nombre__icontains='PREPRO',malla=m.inscripcion.malla_inscripcion().malla,nivelmalla=idnivel)|Q(asignatura__nombre__icontains='COMUNI',malla=m.inscripcion.malla_inscripcion().malla,nivelmalla=idnivel))
                                        if horas_va > asig.horas :
                                            act_vin = EstudianteVinculacion.objects.filter(inscripcion=m.inscripcion)[:1].get()
                                            carrera= act_vin.inscripcion.carrera
                                            act_vin.tiene_actvinculacion(request.user,'ESTUDIANTE NO SE HA AGREGADO ACTIVIDAD DE VINCULACION PORQUE LAS HORAS SON MAYORES A LAS HORAS ASIGNADAS EN ESE NIVEL',horas_va,carrera)
                                        else:

                                            if not nivelingreso.filter(id=int(request.GET['idnivel'])).exists():
                                                act_vin.tiene_actvinculacion(request.user,'NO PUEDE INGRESAR VINCULACION EN EL NIVEL PORQUE EN LA MALLA NO TIENE ASIGNADO ESE NIVEL',0,carrera)

                                            else:

                                                if  InscripcionPracticas.objects.filter(inscripcion=m.inscripcion,nivelmalla__id=idnivel.id).exists():
                                                    act_vin.tiene_actvinculacion(request.user,'YA TIENE INGRESADA LAS PRACTICAS EN ESE NIVEL',0,carrera)
                                                else:

                                                    participante = EstudianteVinculacion(actividad=vinculacion,
                                                                              inscripcion=m.inscripcion,
                                                                              horas=request.GET['horas'],nivelmalla=idnivel)
                                                    participante.save()
                                                    #
                                                    # if request.GET['nivelmalla_id']:
                                                    #     participante.nivelmalla_id=request.GET['nivelmalla_id']

                                                    horas = EstudianteVinculacion.objects.filter(inscripcion=participante.inscripcion).exclude(actividad__convenio=None).aggregate(Sum('horas'))['horas__sum']

                                                # if ASIG_VINCULACION > 0 :
                                                #     asig = Asignatura.objects.get(pk=ASIG_VINCULACION)
                                                #
                                                #     if HistoricoRecordAcademico.objects.filter(inscripcion=participante.inscripcion,asignatura=asig).exists():
                                                #         historico = HistoricoRecordAcademico.objects.filter(inscripcion=participante.inscripcion,asignatura=asig)[:1].get()
                                                #         historico.nota=100
                                                #         historico.asistencia=100
                                                #         historico.fecha=datetime.now().date()
                                                #         historico.aprobada=True
                                                #         historico.convalidacion=False
                                                #         historico.pendiente=False
                                                #     else:
                                                #
                                                #         historico = HistoricoRecordAcademico(inscripcion=participante.inscripcion,
                                                #                                     asignatura=asig,
                                                #                                     nota=100,
                                                #                                     asistencia=100,
                                                #                                     fecha=datetime.now().date(),
                                                #                                     aprobada=True,
                                                #                                     convalidacion=False,
                                                #                                     pendiente=False)
                                                #     historico.save()
                                                #
                                                #     if RecordAcademico.objects.filter(inscripcion=participante.inscripcion,asignatura=asig).exists():
                                                #         record = RecordAcademico.objects.filter(inscripcion=participante.inscripcion,asignatura=asig)[:1].get()
                                                #         record.nota=100
                                                #         record.asistencia=100
                                                #         record.fecha=datetime.now().date()
                                                #         record.aprobada=True
                                                #         record.convalidacion=False
                                                #         record.pendiente=False
                                                #     else:
                                                #         record = RecordAcademico(inscripcion=participante.inscripcion, asignatura=asig,
                                                #                             nota=100, asistencia=100,
                                                #                             fecha=datetime.now().date(), aprobada=True,
                                                #                             convalidacion=False, pendiente=False)
                                                #     record.save()
                                                #
                                                #     if horas < HORAS_VINCULACION :
                                                #         record.delete()
                                                #         historico.delete()
                                                #     else:
                                                    carrera = participante.inscripcion.carrera.nombre
                                                    actividad=participante.actividad.nombre
                                                    participante.correo_vinculacion(request.user,'SE HA AGREGADO ACTIVIDAD DE VINCULACION CON LA COMUNIDAD',horas,carrera,actividad)

                                                    #Obtain client ip address
                                                    client_address = ip_client_address(request)
                                                    # Log de ADICIONAR VINCULACION
                                                    LogEntry.objects.log_action(
                                                        user_id         = request.user.pk,
                                                        content_type_id = ContentType.objects.get_for_model(m.inscripcion).pk,
                                                        object_id       = m.inscripcion.id,
                                                        object_repr     = force_str(vinculacion),
                                                        action_flag     = ADDITION,
                                                        change_message  = 'Adicionado Estudiante  Actividad (' + client_address + ')' )
                                    else:
                                        vinculacion.mail_vinculacionotro(request.user,"NO SE PUEDE INGRESAR VINCULACION PORQUE NO TIENE ASIGANDO EL NIVEL "+elimina_tildes(m.inscripcion.persona.nombre_completo_inverso()))


                                else:
                                    if not EstudianteVinculacion.objects.filter(actividad=vinculacion,inscripcion=m.inscripcion,nivelmalla__id=idnivel.id).exists():
                                        if not InscripcionPracticas.objects.filter(inscripcion=m.inscripcion,nivelmalla__id=idnivel.id).exists():

                                            if not m.inscripcion.tiene_malla_nueva():
                                                horas_va= m.inscripcion.estudiantevinculacion_set.all().aggregate(Sum('horas'))['horas__sum']
                                                if (horas_v + horas_va)<= HORAS_VINCULACION :
                                                    participante = EstudianteVinculacion(actividad=vinculacion,
                                                                              inscripcion=m.inscripcion,
                                                                              horas=request.GET['horas'])
                                                    participante.save()
                                                else:

                                                    vinculacion.mail_vinculacionotro(request.user,"ESTUDIANTE NO SE HA AGREGADO ACTIVIDAD DE VINCULACION PORQUE LAS HORAS SON MAYORES A LAS HORAS ASIGNADAS "+elimina_tildes(m.inscripcion.persona.nombre_completo_inverso()))
                                                    pass
                                            else:

                                                horas_va=horas_v+ m.inscripcion.estudiantevinculacion_set.filter(nivelmalla__id=idnivel.id).aggregate(Sum('horas'))['horas__sum'] if EstudianteVinculacion.objects.filter(inscripcion=m.inscripcion,nivelmalla__id=idnivel.id).exists() else 0
                                                nivelingreso=NivelMalla.objects.filter(id__in=AsignaturaMalla.objects.filter(Q(asignatura__nombre__icontains='PREPRO',malla=m.inscripcion.malla_inscripcion().malla)|Q(asignatura__nombre__icontains='COMUNI',malla=m.inscripcion.malla_inscripcion().malla)).values('nivelmalla'),promediar=True)
                                                if AsignaturaMalla.objects.filter(Q(asignatura__nombre__icontains='PREPRO',malla=m.inscripcion.malla_inscripcion().malla,nivelmalla=idnivel)|Q(asignatura__nombre__icontains='COMUNI',malla=m.inscripcion.malla_inscripcion().malla,nivelmalla=idnivel)).exists():
                                                    asig = AsignaturaMalla.objects.get(Q(asignatura__nombre__icontains='PREPRO',malla=m.inscripcion.malla_inscripcion().malla,nivelmalla=idnivel)|Q(asignatura__nombre__icontains='COMUNI',malla=m.inscripcion.malla_inscripcion().malla,nivelmalla=idnivel))
                                                    if horas_va > asig.horas :
                                                        act_vin = EstudianteVinculacion.objects.filter(inscripcion=m.inscripcion)[:1].get()
                                                        carrera= act_vin.inscripcion.carrera
                                                        act_vin.tiene_actvinculacion(request.user,'ESTUDIANTE NO SE HA AGREGADO ACTIVIDAD DE VINCULACION PORQUE LAS HORAS SON MAYORES A LAS HORAS ASIGNADAS EN ESE NIVEL',horas_va,carrera)
                                                    else:

                                                        if not nivelingreso.filter(id=int(request.GET['idnivel'])).exists():
                                                            act_vin.tiene_actvinculacion(request.user,'NO PUEDE INGRESAR VINCULACION EN EL NIVEL PORQUE EN LA MALLA NO TIENE ASIGNADO ESE NIVEL',0,carrera)

                                                        else:

                                                            if  InscripcionPracticas.objects.filter(inscripcion=m.inscripcion,nivelmalla__id=idnivel.id).exists():
                                                                act_vin.tiene_actvinculacion(request.user,'YA TIENE INGRESADA LAS PRACTICAS EN ESE NIVEL',0,carrera)
                                                            else:

                                                                participante = EstudianteVinculacion(actividad=vinculacion,
                                                                                          inscripcion=m.inscripcion,
                                                                                          horas=request.GET['horas'],nivelmalla=idnivel)
                                                                participante.save()
                                                                #
                                                                # if request.GET['nivelmalla_id']:
                                                                #     participante.nivelmalla_id=request.GET['nivelmalla_id']

                                                                horas = EstudianteVinculacion.objects.filter(inscripcion=participante.inscripcion).exclude(actividad__convenio=None).aggregate(Sum('horas'))['horas__sum']

                                                            # if ASIG_VINCULACION > 0 :
                                                            #     asig = Asignatura.objects.get(pk=ASIG_VINCULACION)
                                                            #
                                                            #     if HistoricoRecordAcademico.objects.filter(inscripcion=participante.inscripcion,asignatura=asig).exists():
                                                            #         historico = HistoricoRecordAcademico.objects.filter(inscripcion=participante.inscripcion,asignatura=asig)[:1].get()
                                                            #         historico.nota=100
                                                            #         historico.asistencia=100
                                                            #         historico.fecha=datetime.now().date()
                                                            #         historico.aprobada=True
                                                            #         historico.convalidacion=False
                                                            #         historico.pendiente=False
                                                            #     else:
                                                            #
                                                            #         historico = HistoricoRecordAcademico(inscripcion=participante.inscripcion,
                                                            #                                     asignatura=asig,
                                                            #                                     nota=100,
                                                            #                                     asistencia=100,
                                                            #                                     fecha=datetime.now().date(),
                                                            #                                     aprobada=True,
                                                            #                                     convalidacion=False,
                                                            #                                     pendiente=False)
                                                            #     historico.save()
                                                            #
                                                            #     if RecordAcademico.objects.filter(inscripcion=participante.inscripcion,asignatura=asig).exists():
                                                            #         record = RecordAcademico.objects.filter(inscripcion=participante.inscripcion,asignatura=asig)[:1].get()
                                                            #         record.nota=100
                                                            #         record.asistencia=100
                                                            #         record.fecha=datetime.now().date()
                                                            #         record.aprobada=True
                                                            #         record.convalidacion=False
                                                            #         record.pendiente=False
                                                            #     else:
                                                            #         record = RecordAcademico(inscripcion=participante.inscripcion, asignatura=asig,
                                                            #                             nota=100, asistencia=100,
                                                            #                             fecha=datetime.now().date(), aprobada=True,
                                                            #                             convalidacion=False, pendiente=False)
                                                            #     record.save()
                                                            #
                                                            #     if horas < HORAS_VINCULACION :
                                                            #         record.delete()
                                                            #         historico.delete()
                                                            #     else:
                                                                carrera = participante.inscripcion.carrera.nombre
                                                                actividad=participante.actividad.nombre
                                                                participante.correo_vinculacion(request.user,'SE HA AGREGADO ACTIVIDAD DE VINCULACION CON LA COMUNIDAD',horas,carrera,actividad)

                                                                #Obtain client ip address
                                                                client_address = ip_client_address(request)
                                                                # Log de ADICIONAR VINCULACION
                                                                LogEntry.objects.log_action(
                                                                    user_id         = request.user.pk,
                                                                    content_type_id = ContentType.objects.get_for_model(m.inscripcion).pk,
                                                                    object_id       = m.inscripcion.id,
                                                                    object_repr     = force_str(vinculacion),
                                                                    action_flag     = ADDITION,
                                                                    change_message  = 'Adicionado Estudiante  Actividad (' + client_address + ')' )
                                                else:
                                                    vinculacion.mail_vinculacionotro(request.user,"NO SE PUEDE INGRESAR VINCULACION PORQUE NO TIENE ASIGANDO EL NIVEL "+elimina_tildes(m.inscripcion.persona.nombre_completo_inverso()))


                        # data['matriculas'] = EstudianteVinculacion.objects.filter(vinculacion=vinculacion).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2')
                        return HttpResponseRedirect("/vinculacion?action=participantes&id="+str(vinculacion.id))

                    except Exception as e:
                        return HttpResponseRedirect('/?info='+str(e))

                elif action == 'agregar':
                    try:
                        inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                        #OCastillo 24-05-2023 validacion estudiante que no este egresado ni graduado
                        if Egresado.objects.filter(inscripcion=inscripcion).exists() or Graduado.objects.filter(inscripcion=inscripcion).exists():
                            return HttpResponseRedirect('/?info=NO PUEDE INGRESAR VINCULACION A ESTUDIANTE EGRESADO O GRADUADO')
                        vinculacion = ActividadVinculacion.objects.get(pk=request.GET['vinculacion'])
                        puedeingresar=True
                        # nivelmalla=None
                        # if request.GET['nivelmalla']:
                        #     nivelmalla = NivelMalla.objects.get(pk=request.GET['nivelmalla'])
                        horas_v = int(request.GET['horas'])
                        idnivel =NivelMalla.objects.get(pk=int(request.GET['idnivel']))

                        if  AsignaturaMalla.objects.filter(malla=inscripcion.malla_inscripcion().malla,nivelmalla=idnivel,articulada=True).exists():
                            idmateriarticulaasignatura = AsignaturaMalla.objects.filter(malla=inscripcion.malla_inscripcion().malla,nivelmalla=idnivel,articulada=True).values('asignatura__id')
                            idmateriasignada=MateriaAsignada.objects.filter(matricula__inscripcion=inscripcion,materia__asignatura__id__in=idmateriarticulaasignatura).values('id')
                            eva =  EvaluacionITB.objects.filter(materiaasignada__id__in=idmateriasignada,estado__id=NOTA_ESTADO_APROBADO).values('materiaasignada__materia__asignatura__id')
                            record= RecordAcademico.objects.filter(inscripcion=inscripcion,asignatura__id__in=idmateriarticulaasignatura,aprobada=True).exclude(asignatura__id__in=eva)
                            totalmateriaaprobada= len(eva)+len(record)

                            if len(idmateriarticulaasignatura)==totalmateriaaprobada:
                                puedeingresar=True
                            else:
                                puedeingresar=False


                        if puedeingresar==True:
                            if not inscripcion.malla_inscripcion().malla.nueva_malla:

                                horas_va= inscripcion.estudiantevinculacion_set.all().aggregate(Sum('horas'))['horas__sum']
                                if (horas_v + horas_va if horas_va!=None else 0 )<= HORAS_VINCULACION :
                                #if not EstudianteVinculacion.objects.filter(actividad=vinculacion,inscripcion=inscripcion,nivelmalla=idnivel).exists():
                                    participante = EstudianteVinculacion(actividad=vinculacion,
                                                              inscripcion=inscripcion,
                                                              horas=request.GET['horas'])

                                    participante.save()

                                    carrera = participante.inscripcion.carrera.nombre
                                    actividad=participante.actividad.nombre
                                    participante.correo_vinculacion(request.user,'SE HA AGREGADO ACTIVIDAD DE VINCULACION CON LA COMUNIDAD',horas_v,carrera,actividad)
                                    #Obtain client ip address
                                    client_address = ip_client_address(request)

                                    # Log de ADICIONAR NIVEL
                                    LogEntry.objects.log_action(
                                        user_id         = request.user.pk,
                                        content_type_id = ContentType.objects.get_for_model(inscripcion).pk,
                                        object_id       = inscripcion.id,
                                        object_repr     = force_str(vinculacion),
                                        action_flag     = ADDITION,
                                        change_message  = 'Adicionado Estudiante  Actividad (' + client_address + ')' )

                                    return HttpResponseRedirect("/vinculacion?action=participantes&id="+str(vinculacion.id))


                                else:
                                    return HttpResponseRedirect('/?info=NO SE HA AGREGADO LA ACTIVIDAD - EL NUMERO DE HORAS SUPERA LAS PERMITIDAS')

                            else:
                                idnivel =NivelMalla.objects.get(pk=int(request.GET['idnivel']))

                                nivelingreso=NivelMalla.objects.filter(id__in=AsignaturaMalla.objects.filter(Q(asignatura__nombre__icontains='PREPRO',malla=inscripcion.malla_inscripcion().malla)|Q(asignatura__nombre__icontains='COMUNI',malla=inscripcion.malla_inscripcion().malla)).values('nivelmalla'),promediar=True)

                                if not nivelingreso.filter(id=int(request.GET['idnivel'])).exists():
                                    return HttpResponseRedirect('/?info=NO PUEDE INGRESAR VINCULACION EN EL NIVEL PORQUE EN LA MALLA NO TIENE ASIGNADO ESE NIVEL')
                                else:

                                    if inscripcion.tiene_vinculacion():
                                        horas_v1=horas_v+ inscripcion.estudiantevinculacion_set.filter(nivelmalla__id=idnivel.id).aggregate(Sum('horas'))['horas__sum'] if EstudianteVinculacion.objects.filter(inscripcion=inscripcion,nivelmalla__id=idnivel.id).exists() else 0
                                        #horas_v1= inscripcion.estudiantevinculacion_set.all().aggregate(Sum('horas'))['horas__sum']
                                        horastotal = horas_v+horas_v1
                                        asig = AsignaturaMalla.objects.get(Q(asignatura__nombre__icontains='PREPRO',malla=inscripcion.malla_inscripcion().malla,nivelmalla=idnivel)|Q(asignatura__nombre__icontains='COMUNI',malla=inscripcion.malla_inscripcion().malla,nivelmalla=idnivel))
                                        if horastotal > asig.horas :
                                            return HttpResponseRedirect('/?info=NO PUEDE INGRESAR VINCULACION PORQUE SUPERA LAS HORAS ASIGNADA EN EL NIVEL')
                                            #return HttpResponse(json.dumps({"result":"bad","horas": "mayores a las asignada en el nivel"}),content_type="application/json")




                                horas_va=0
                                # Validacion para las horas de Vinculacion OC
                                # OCU 16-08-2018 sin validacion de horas ahora los estudiantes pueden tener varias actividades

                                if  EstudianteVinculacion.objects.filter(inscripcion=inscripcion,nivelmalla=idnivel).exists():
                                    return HttpResponseRedirect('/?info=Ya tiene ingresar las practicas en ese nivel')
                                    #return HttpResponse(json.dumps({'result':'bad', 'mensaje':"Ya tiene ingresar las practicas en ese nivel"}), content_type="application/json")

                                #horas_va= inscripcion.estudiantevinculacion_set.all().aggregate(Sum('horas'))['horas__sum']
                                horas_va = inscripcion.estudiantevinculacion_set.filter(nivelmalla__id=idnivel.id).aggregate(Sum('horas'))['horas__sum'] if EstudianteVinculacion.objects.filter(inscripcion=inscripcion,nivelmalla__id=idnivel.id).exists() else 0
                                if horas_va < HORAS_VINCULACION or (horas_v + horas_va)<= HORAS_VINCULACION :
                                    #if not EstudianteVinculacion.objects.filter(actividad=vinculacion,inscripcion=inscripcion,nivelmalla=idnivel).exists():
                                    participante = EstudianteVinculacion(actividad=vinculacion,
                                                              inscripcion=inscripcion,
                                                              horas=request.GET['horas'],nivelmalla=idnivel)

                                    participante.save()
                                    # if nivelmalla:
                                    #     participante.nivelmalla_id=nivelmalla.id
                                    #     participante.save()
                                    horas = EstudianteVinculacion.objects.filter(inscripcion=participante.inscripcion).exclude(actividad__convenio=None).aggregate(Sum('horas'))['horas__sum']
                                    asig = Asignatura.objects.get(pk=ASIG_VINCULACION)

                                    # if HistoricoRecordAcademico.objects.filter(inscripcion=participante.inscripcion, asignatura=asig).exists():
                                    #     historico = HistoricoRecordAcademico.objects.filter(inscripcion=participante.inscripcion, asignatura=asig)[:1].get()
                                    #     historico.nota = 100
                                    #     historico.asistencia=100
                                    #     historico.fecha=datetime.now().date()
                                    #     historico.aprobada=True
                                    #     historico.convalidacion=False
                                    #     historico.pendiente=False
                                    #
                                    # else:
                                    #     historico = HistoricoRecordAcademico(inscripcion=participante.inscripcion,
                                    #                                 asignatura=asig,
                                    #                                 nota=100,
                                    #                                 asistencia=100,
                                    #                                 fecha=datetime.now().date(),
                                    #                                 aprobada=True,
                                    #                                 convalidacion=False,
                                    #                                 pendiente=False)
                                    #     historico.save()
                                    #
                                    # if RecordAcademico.objects.filter(inscripcion=participante.inscripcion,asignatura=asig).exists():
                                    #     record = RecordAcademico.objects.filter(inscripcion=participante.inscripcion,asignatura=asig)[:1].get()
                                    #     record.nota=100
                                    #     record.asistencia=100
                                    #     record.fecha=datetime.now().date()
                                    #     record.aprobada=True
                                    #     record.convalidacion=False
                                    #     record.pendiente=False
                                    #
                                    # else:
                                    #     record = RecordAcademico(inscripcion=participante.inscripcion, asignatura=asig,
                                    #                         nota=100, asistencia=100,
                                    #                         fecha=datetime.now().date(), aprobada=True,
                                    #                         convalidacion=False, pendiente=False)
                                    #     record.save()
                                    # if horas < HORAS_VINCULACION :
                                    #     record.delete()
                                    #     historico.delete()
                                    # else:
                                    carrera = participante.inscripcion.carrera.nombre
                                    actividad=participante.actividad.nombre
                                    participante.correo_vinculacion(request.user,'SE HA AGREGADO ACTIVIDAD DE VINCULACION CON LA COMUNIDAD',horas,carrera,actividad)
                                    #Obtain client ip address
                                    client_address = ip_client_address(request)

                                    # Log de ADICIONAR NIVEL
                                    LogEntry.objects.log_action(
                                        user_id         = request.user.pk,
                                        content_type_id = ContentType.objects.get_for_model(inscripcion).pk,
                                        object_id       = inscripcion.id,
                                        object_repr     = force_str(vinculacion),
                                        action_flag     = ADDITION,
                                        change_message  = 'Adicionado Estudiante  Actividad (' + client_address + ')' )
                                else:
                                    return HttpResponseRedirect('/?info=NO SE HA AGREGADO LA ACTIVIDAD - EL NUMERO DE HORAS SUPERA LAS PERMITIDAS')
                                #else:
                                   # return HttpResponseRedirect('/?info=NO SE HA AGREGADO LA ACTIVIDAD - PORQUE YA TIENE REGISTRADA EN ESE NIVEL')
                                return HttpResponseRedirect("/vinculacion?action=participantes&id="+str(vinculacion.id))
                        else:
                            return HttpResponseRedirect('/?info=NO SE HA AGREGADO LA ACTIVIDAD - PORQUE NO TIENE MATERIA ARTICULADA APROBADA EN ESTE NIVEL')
                    except Exception as e:
                        return HttpResponseRedirect('/?info='+str(e))
                    # data['matriculas'] = EstudianteVinculacion.objects.filter(vinculacion=vinculacion).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2')


                elif action == 'agregarsinarticulada':
                    try:
                        inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                        # OCastillo 24-05-2023 validacion estudiante que no este egresado ni graduado
                        if Egresado.objects.filter(inscripcion=inscripcion).exists() or Graduado.objects.filter(inscripcion=inscripcion).exists():
                            return HttpResponseRedirect('/?info=NO PUEDE INGRESAR VINCULACION A ESTUDIANTE EGRESADO O GRADUADO')
                        vinculacion = ActividadVinculacion.objects.get(pk=request.GET['vinculacion'])
                        puedeingresar=True
                        # nivelmalla=None
                        # if request.GET['nivelmalla']:
                        #     nivelmalla = NivelMalla.objects.get(pk=request.GET['nivelmalla'])
                        horas_v = int(request.GET['horas'])
                        idnivel =NivelMalla.objects.get(pk=int(request.GET['idnivel']))



                        if not inscripcion.malla_inscripcion().malla.nueva_malla:

                            horas_va= inscripcion.estudiantevinculacion_set.all().aggregate(Sum('horas'))['horas__sum']
                            if (horas_v + horas_va if horas_va!=None else 0 )<= HORAS_VINCULACION :
                            #if not EstudianteVinculacion.objects.filter(actividad=vinculacion,inscripcion=inscripcion,nivelmalla=idnivel).exists():
                                participante = EstudianteVinculacion(actividad=vinculacion,
                                                          inscripcion=inscripcion,
                                                          horas=request.GET['horas'])

                                participante.save()

                                carrera = participante.inscripcion.carrera.nombre
                                actividad=participante.actividad.nombre
                                participante.correo_vinculacion(request.user,'SE HA AGREGADO ACTIVIDAD DE VINCULACION CON LA COMUNIDAD',horas_v,carrera,actividad)
                                #Obtain client ip address
                                client_address = ip_client_address(request)

                                # Log de ADICIONAR NIVEL
                                LogEntry.objects.log_action(
                                    user_id         = request.user.pk,
                                    content_type_id = ContentType.objects.get_for_model(inscripcion).pk,
                                    object_id       = inscripcion.id,
                                    object_repr     = force_str(vinculacion),
                                    action_flag     = ADDITION,
                                    change_message  = 'Adicionado Estudiante  Actividad (' + client_address + ')' )

                                return HttpResponseRedirect("/vinculacion?action=participantes&id="+str(vinculacion.id))


                            else:
                                return HttpResponseRedirect('/?info=NO SE HA AGREGADO LA ACTIVIDAD - EL NUMERO DE HORAS SUPERA LAS PERMITIDAS')

                        else:
                            idnivel =NivelMalla.objects.get(pk=int(request.GET['idnivel']))

                            nivelingreso=NivelMalla.objects.filter(id__in=AsignaturaMalla.objects.filter(Q(asignatura__nombre__icontains='PREPRO',malla=inscripcion.malla_inscripcion().malla)|Q(asignatura__nombre__icontains='COMUNI',malla=inscripcion.malla_inscripcion().malla)).values('nivelmalla'),promediar=True)

                            if not nivelingreso.filter(id=int(request.GET['idnivel'])).exists():
                                return HttpResponseRedirect('/?info=NO PUEDE INGRESAR VINCULACION EN EL NIVEL PORQUE EN LA MALLA NO TIENE ASIGNADO ESE NIVEL')
                            else:

                                if inscripcion.tiene_vinculacion():
                                    horas_v1=horas_v+ inscripcion.estudiantevinculacion_set.filter(nivelmalla__id=idnivel.id).aggregate(Sum('horas'))['horas__sum'] if EstudianteVinculacion.objects.filter(inscripcion=inscripcion,nivelmalla__id=idnivel.id).exists() else 0
                                    #horas_v1= inscripcion.estudiantevinculacion_set.all().aggregate(Sum('horas'))['horas__sum']
                                    horastotal = horas_v+horas_v1
                                    asig = AsignaturaMalla.objects.get(Q(asignatura__nombre__icontains='PREPRO',malla=inscripcion.malla_inscripcion().malla,nivelmalla=idnivel)|Q(asignatura__nombre__icontains='COMUNI',malla=inscripcion.malla_inscripcion().malla,nivelmalla=idnivel))
                                    if horastotal > asig.horas :
                                        return HttpResponseRedirect('/?info=NO PUEDE INGRESAR VINCULACION PORQUE SUPERA LAS HORAS ASIGNADA EN EL NIVEL')
                                        #return HttpResponse(json.dumps({"result":"bad","horas": "mayores a las asignada en el nivel"}),content_type="application/json")




                            horas_va=0
                            # Validacion para las horas de Vinculacion OC
                            # OCU 16-08-2018 sin validacion de horas ahora los estudiantes pueden tener varias actividades

                            if  InscripcionPracticas.objects.filter(inscripcion=inscripcion,nivelmalla__id=idnivel.id).exists():
                                return HttpResponseRedirect('/?info=Ya tiene ingresar las practicas en ese nivel')
                                #return HttpResponse(json.dumps({'result':'bad', 'mensaje':"Ya tiene ingresar las practicas en ese nivel"}), content_type="application/json")

                            #horas_va= inscripcion.estudiantevinculacion_set.all().aggregate(Sum('horas'))['horas__sum']
                            horas_va = inscripcion.estudiantevinculacion_set.filter(nivelmalla__id=idnivel.id).aggregate(Sum('horas'))['horas__sum'] if EstudianteVinculacion.objects.filter(inscripcion=inscripcion,nivelmalla__id=idnivel.id).exists() else 0
                            if horas_va < HORAS_VINCULACION or (horas_v + horas_va)<= HORAS_VINCULACION :
                                #if not EstudianteVinculacion.objects.filter(actividad=vinculacion,inscripcion=inscripcion,nivelmalla=idnivel).exists():
                                participante = EstudianteVinculacion(actividad=vinculacion,
                                                          inscripcion=inscripcion,
                                                          horas=request.GET['horas'],nivelmalla=idnivel)

                                participante.save()
                                # if nivelmalla:
                                #     participante.nivelmalla_id=nivelmalla.id
                                #     participante.save()
                                horas = EstudianteVinculacion.objects.filter(inscripcion=participante.inscripcion).exclude(actividad__convenio=None).aggregate(Sum('horas'))['horas__sum']
                                asig = Asignatura.objects.get(pk=ASIG_VINCULACION)

                                # if HistoricoRecordAcademico.objects.filter(inscripcion=participante.inscripcion, asignatura=asig).exists():
                                #     historico = HistoricoRecordAcademico.objects.filter(inscripcion=participante.inscripcion, asignatura=asig)[:1].get()
                                #     historico.nota = 100
                                #     historico.asistencia=100
                                #     historico.fecha=datetime.now().date()
                                #     historico.aprobada=True
                                #     historico.convalidacion=False
                                #     historico.pendiente=False
                                #
                                # else:
                                #     historico = HistoricoRecordAcademico(inscripcion=participante.inscripcion,
                                #                                 asignatura=asig,
                                #                                 nota=100,
                                #                                 asistencia=100,
                                #                                 fecha=datetime.now().date(),
                                #                                 aprobada=True,
                                #                                 convalidacion=False,
                                #                                 pendiente=False)
                                #     historico.save()
                                #
                                # if RecordAcademico.objects.filter(inscripcion=participante.inscripcion,asignatura=asig).exists():
                                #     record = RecordAcademico.objects.filter(inscripcion=participante.inscripcion,asignatura=asig)[:1].get()
                                #     record.nota=100
                                #     record.asistencia=100
                                #     record.fecha=datetime.now().date()
                                #     record.aprobada=True
                                #     record.convalidacion=False
                                #     record.pendiente=False
                                #
                                # else:
                                #     record = RecordAcademico(inscripcion=participante.inscripcion, asignatura=asig,
                                #                         nota=100, asistencia=100,
                                #                         fecha=datetime.now().date(), aprobada=True,
                                #                         convalidacion=False, pendiente=False)
                                #     record.save()
                                # if horas < HORAS_VINCULACION :
                                #     record.delete()
                                #     historico.delete()
                                # else:
                                carrera = participante.inscripcion.carrera.nombre
                                actividad=participante.actividad.nombre
                                participante.correo_vinculacion(request.user,'SE HA AGREGADO ACTIVIDAD DE VINCULACION CON LA COMUNIDAD',horas,carrera,actividad)
                                #Obtain client ip address
                                client_address = ip_client_address(request)

                                # Log de ADICIONAR NIVEL
                                LogEntry.objects.log_action(
                                    user_id         = request.user.pk,
                                    content_type_id = ContentType.objects.get_for_model(inscripcion).pk,
                                    object_id       = inscripcion.id,
                                    object_repr     = force_str(vinculacion),
                                    action_flag     = ADDITION,
                                    change_message  = 'Adicionado Estudiante  Actividad (' + client_address + ')' )
                            else:
                                return HttpResponseRedirect('/?info=NO SE HA AGREGADO LA ACTIVIDAD - EL NUMERO DE HORAS SUPERA LAS PERMITIDAS')
                        #else:
                           # return HttpResponseRedirect('/?info=NO SE HA AGREGADO LA ACTIVIDAD - PORQUE YA TIENE REGISTRADA EN ESE NIVEL')
                        return HttpResponseRedirect("/vinculacion?action=participantes&id="+str(vinculacion.id))

                    except Exception as e:
                        return HttpResponseRedirect('/?info='+str(e))
                    # data['matriculas'] = EstudianteVinculacion.objects.filter(vinculacion=vinculacion).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2')




                elif action=='h_vinculacion':
                    horas_v = 0
                    horas_va =int(request.GET['horas'])
                    nivelmallaid =int(request.GET['nivelmalla'])
                    inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                    if not inscripcion.tiene_malla_nueva():
                       horas_va1= inscripcion.estudiantevinculacion_set.all().aggregate(Sum('horas'))['horas__sum']
                       if (horas_va+horas_va1 if horas_va1!=None else 0 )<= HORAS_VINCULACION :
                           return HttpResponse(json.dumps({"result":"ok","horas":horas_v}),content_type="application/json")
                       else:
                           return HttpResponse(json.dumps({"result":"bad3","horas": "mayor a las"}),content_type="application/json")

                    else:
                        if inscripcion.tiene_vinculacion():
                            horas_v= inscripcion.estudiantevinculacion_set.all().aggregate(Sum('horas'))['horas__sum']
                            actividad = EstudianteVinculacion.objects.filter(inscripcion=inscripcion).values('actividad')
                            malla = Malla.objects.get(carrera=inscripcion.carrera)
                            asig = AsignaturaMalla.objects.get(Q(asignatura__nombre__icontains='PREPRO',malla=malla,nivelmalla__id=nivelmallaid)|Q(asignatura__nombre__icontains='COMUNI',malla=malla,nivelmalla__id=nivelmallaid))

                            if horas_v > asig.horas :
                                return HttpResponse(json.dumps({"result":"bad1","horas":horas_v}),content_type="application/json")

                            #if horas_v == HORAS_VINCULACION :
                             #   return HttpResponse(json.dumps({"result":"bad2","horas":horas_v}),content_type="application/json")

                            if (horas_v + horas_va) > asig.horas:
                                return HttpResponse(json.dumps({"result":"bad3","horas":horas_v}),content_type="application/json")

                            if (horas_v + horas_va) <= asig.horas:
                                return HttpResponse(json.dumps({"result":"ok","horas":horas_v}),content_type="application/json")
                        else:

                            # nivelingreso=NivelMalla.objects.filter(id__in=AsignaturaMalla.objects.filter(asignatura__nombre__icontains='PREPRO',malla=inscripcion.malla_inscripcion().malla).values('nivelmalla'),promediar=True)
                            nivelingreso= NivelMalla.objects.filter(id__in=AsignaturaMalla.objects.filter(Q(asignatura__nombre__icontains='PREPRO')|Q(asignatura__nombre__icontains='COMUNI'),malla=inscripcion.malla_inscripcion().malla).values('nivelmalla'),promediar=True)

                            if not nivelingreso.filter(id=int(request.GET['nivelmalla'])).exists():
                                return HttpResponse(json.dumps({"result":"bad3","horas":"No se puede ingresar vinculacion en el nivel porque en la malla no tiene asignado ese nivel"}),content_type="application/json")
                                #return HttpResponseRedirect('/?info=NO PUEDE INGRESAR VINCULACION EN EL NIVEL PORQUE EN LA MALLA NO TIENE ASIGNADO ESE NIVEL')
                            else:
                                malla = Malla.objects.get(carrera=inscripcion.carrera)
                                asig = AsignaturaMalla.objects.get(Q(asignatura__nombre__icontains='PREPRO',malla=malla,nivelmalla__id=nivelmallaid)|Q(asignatura__nombre__icontains='COMUNI',malla=malla,nivelmalla__id=nivelmallaid))
                                if horas_va > asig.horas :
                                    return HttpResponse(json.dumps({"result":"bad3","horas": "mayor horas a las asignada en el nivel"}),content_type="application/json")
                                else:
                                    return HttpResponse(json.dumps({"result":"ok","horas":horas_v}),content_type="application/json")




                elif action == 'agregarb':
                    vinculacion = ActividadVinculacion.objects.get(pk=request.GET['id'])
                    if request.GET['b'] == '0' :
                        if not BeneficiariosVinculacion.objects.filter(identificacion=request.GET['iden']).exists():
                            beneficiario = BeneficiariosVinculacion(actividad=vinculacion,
                                                      nombre=request.GET['nom'],
                                                      identificacion=request.GET['iden'],
                                                      edad=request.GET['edad'],
                                                      sexo_id=request.GET['sexo'],
                                                      etnia_id=request.GET['etnia'],
                                                      procedencia=request.GET['proce'])
                            beneficiario.save()
                    else:
                        b =BeneficiariosVinculacion.objects.get(id=request.GET['b'])
                        b.nombre=request.GET['nom']
                        b.identificacion=request.GET['iden']
                        b.edad=request.GET['edad']
                        b.sexo_id=request.GET['sexo']
                        b.etnia_id=request.GET['etnia']
                        b.procedencia=request.GET['proce']
                        b.save()


                    # data['matriculas'] = EstudianteVinculacion.objects.filter(vinculacion=vinculacion).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2')
                    return HttpResponseRedirect("/vinculacion?action=beneficiarios&id="+str(vinculacion.id))


                elif action == 'eliminarins':
                    i =  EstudianteVinculacion.objects.get(pk=request.GET['id'])
                    v = i.actividad.id
                    inscripcion = i.inscripcion
                    carrera = i.inscripcion.carrera.nombre
                    actividad=i.actividad.nombre

                    i.correo_vinculacion(request.user,'SE HA ELIMINADO LA NOTA DE VINCULACION CON LA COMUNIDAD',i.horas,carrera,actividad)
                    horas = EstudianteVinculacion.objects.filter(inscripcion=inscripcion).exclude(actividad__convenio=None).aggregate(Sum('horas'))['horas__sum']
                    asig =  Asignatura.objects.get(pk=ASIG_VINCULACION)
                    i.delete()

                    if horas <= HORAS_VINCULACION:
                        if HistoricoRecordAcademico.objects.filter(inscripcion=inscripcion, asignatura=asig).exists():
                            HistoricoRecordAcademico.objects.filter(inscripcion=inscripcion, asignatura=asig)[:1].get().delete()
                        if RecordAcademico.objects.filter(inscripcion=inscripcion,asignatura=asig).exists():
                            RecordAcademico.objects.filter(inscripcion=inscripcion,asignatura=asig)[:1].get().delete()

                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de EDITAR HORARIO CLASE
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(i).pk,
                        object_id       = i.id,
                        object_repr     = force_str(i),
                        action_flag     = CHANGE,
                        change_message  = 'Eliminado Estudiante Vinculacion  (' + client_address + ')'  )


                    return HttpResponseRedirect("/vinculacion?action=participantes&id="+str(v))

                elif action == 'eliminaractividad':
                    i =  EstudianteVinculacion.objects.get(pk=request.GET['id'])
                    v = i.actividad.id
                    inscripcion = i.inscripcion
                    carrera=i.inscripcion.carrera.nombre
                    nota_historico=''
                    nota_record=''

                    asig = Asignatura.objects.get(pk=ASIG_VINCULACION)

                    if HistoricoRecordAcademico.objects.filter(inscripcion=inscripcion, asignatura=asig).exists():
                        nota_historico=HistoricoRecordAcademico.objects.filter(inscripcion=inscripcion, asignatura=asig)[:1].get()
                        nota_historico = nota_historico.nota
                    if RecordAcademico.objects.filter(inscripcion=inscripcion,asignatura=asig).exists():
                        nota_record=RecordAcademico.objects.filter(inscripcion=inscripcion,asignatura=asig)[:1].get()
                        nota_record=nota_record.nota

                    i.elimina_actividad_vinculacion(request.user,'SE HA ELIMINADO ACTIVIDAD DE VINCULACION A ESTUDIANTE EGRESADO',i.horas,nota_historico,nota_record,carrera)
                    i.delete()

                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de ELIMINAR ACTIVIDAD VINCULACION A EGRESADO
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(i).pk,
                        object_id       = i.id,
                        object_repr     = force_str(i),
                        action_flag     = DELETION,
                        change_message  = 'Eliminada Actividad Vinculacion a Egresado  (' + client_address + ')'  )

                    return HttpResponseRedirect("/vinculacion?action=participantes&id="+str(v))

                elif action == 'eliminard':
                    d =  DocenteVinculacion.objects.get(pk=request.GET['id'])
                    v = d.actividad.id
                    op=0
                    if d.fecha:
                        if  RolPago.objects.filter(inicio__lte =d.fecha,fechamaxvin__gte=d.fecha,activo=True).order_by('-id').exists():
                            r = RolPago.objects.filter(inicio__lte =d.fecha, fechamaxvin__gte=d.fecha,activo=True).order_by('-id')[:1].get()
                            if r.fechamaxvin >= datetime.now().date():
                               op = 1
                        else:
                            op=1
                    else:
                        op=1
                    if  op == 1:
                        if d.informe:
                            if (MEDIA_ROOT + '/' + str(d.informe)):
                                os.remove(MEDIA_ROOT + '/' + str(d.informe))
                    #Obtain client ip address
                        client_address = ip_client_address(request)

                        # Log de EDITAR HORARIO CLASE
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(d).pk,
                            object_id       = d.id,
                            object_repr     = force_str(d),
                            action_flag     = CHANGE,
                            change_message  = 'Eliminado Docente Vinculcion  (' + client_address + ')'  )
                        d.delete()

                        return HttpResponseRedirect("/vinculacion?action=docentes&id="+str(v))
                    else:
                        return HttpResponseRedirect("/vinculacion?action=docentes&id="+str(v)+"&error=No se puede eliminar registro con esta fecha")

                elif action == 'eliminarb':
                    d =  BeneficiariosVinculacion.objects.get(pk=request.GET['id'])
                    v = d.actividad.id

                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de ELIMINAR BENEFICIARIO
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(d).pk,
                        object_id       = d.id,
                        object_repr     = force_str(d),
                        action_flag     = CHANGE,
                        change_message  = 'Eliminado Beneficiario Vinculacion  (' + client_address + ')'  )
                    d.delete()

                    return HttpResponseRedirect("/vinculacion?action=beneficiarios&id="+str(v))

                elif action == 'eliminarev':
                    d =  EvidenciaVinculacion.objects.get(pk=request.GET['id'])
                    v = d.actividad.id

                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de EDITAR HORARIO CLASE
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(d).pk,
                        object_id       = d.id,
                        object_repr     = force_str(d),
                        action_flag     = CHANGE,
                        change_message  = 'Eliminada Evidencia Vinculacion  (' + client_address + ')'  )
                    d.delete()

                    return HttpResponseRedirect("/vinculacion?action=evidencia&id="+str(v))

                elif action == 'eliminarobs':
                    d =  ObservacionVinculacion.objects.get(pk=request.GET['id'])
                    v = d.actividad.id

                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de EDITAR HORARIO CLASE
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(d).pk,
                        object_id       = d.id,
                        object_repr     = force_str(d),
                        action_flag     = CHANGE,
                        change_message  = 'Eliminada Observacion Vinculacion  (' + client_address + ')'  )
                    d.delete()

                    return HttpResponseRedirect("/vinculacion?action=observacion&id="+str(v))

                elif action == 'eliminar':
                    i =  ActividadVinculacion.objects.get(pk=request.GET['id'])
                    g = i
                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de EDITAR HORARIO CLASE
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(i).pk,
                        object_id       = i.id,
                        object_repr     = force_str(i),
                        action_flag     = CHANGE,
                        change_message  = 'Eliminado Proyecto Vinculacion (' + client_address + ')'  )
                    i.delete()

                    return HttpResponseRedirect("/vinculacion")

                elif action == 'editar':
                    actividad = ActividadVinculacion.objects.get(pk=request.GET['id'])
                    initial = model_to_dict(actividad)
                    initial.update(model_to_dict(actividad))
                    data['form'] = VinculacionForm(initial=initial)
                    if 'error' in request.GET:
                        data['error'] = 1
                    data['ban'] = 2
                    data['actividad'] =actividad
                    return render(request ,"vinculacion/add.html" ,  data)

                elif action=='estadoconvenio':
                    convenio = Convenio.objects.get(pk=request.GET['cid'])
                    if convenio.activo==True:
                        estado='Activo'
                    else:
                        estado='Inactivo'

                    return HttpResponse(json.dumps({'estado': estado}),content_type="application/json")

                elif action=='tipoprograma':
                    programa = Programa.objects.get(pk=request.GET['pid'])
                    tipoprograma=programa.tipo.nombre

                    return HttpResponse(json.dumps({'tipoprograma': tipoprograma}),content_type="application/json")

                #OC 14-05-2019 para ver aprobacion de horas vinculacion por grupo
                elif action=='veraprobacionvinculacion':
                    data['vinculacion'] = ActividadVinculacion.objects.get(pk=request.GET['id'])
                    data['participantes'] = EstudianteVinculacion.objects.filter(actividad=data['vinculacion']).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2')
                    estudiantes_actividad = EstudianteVinculacion.objects.filter(actividad=data['vinculacion']).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2').values('inscripcion_id')
                    cantidad_estud=len(data['participantes'])
                    aprobados=AprobacionVinculacion.objects.filter(inscripcion__in=estudiantes_actividad,revisionestudiante=True,revisionproyecto=True,revisiondocente=True,estudiantevinculacion__in=data['participantes']).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2')
                    estdaprobados=AprobacionVinculacion.objects.filter(inscripcion__in=estudiantes_actividad,revisionestudiante=True,revisionproyecto=True,revisiondocente=True,estudiantevinculacion__in=data['participantes']).values('inscripcion__id')
                    estnoaprobados = EstudianteVinculacion.objects.filter(actividad=data['vinculacion']).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2').exclude(inscripcion__in=estdaprobados)
                    data['aprobados']=aprobados
                    if len(estnoaprobados)>0:
                        data['cantnoaprobados']=len(estnoaprobados)
                        data['noaprobados']=estnoaprobados
                    else:
                        data['cantnoaprobados']=0

                    data['cantidad_aprobados']=len(data['aprobados'])
                    data['cantidad_estud']=cantidad_estud

                    return render(request ,"vinculacion/veraprobacionvinculacionxgrupo.html" ,  data)

                #OCastillo 20-06-2019
                elif action == 'modificarhoras':
                    horas_v = 0
                    carrera=''
                    actividad=''
                    estudiantes_modificahoras=[]
                    estudiantes_nomodificahoras=[]
                   # data['nivel'] = Nivel.objects.get(pk=request.GET['id'])
                    idnivelmalla =NivelMalla.objects.get(pk=int(request.GET['idnivel']))
                    vinculacion = ActividadVinculacion.objects.get(pk=request.GET['vinculacion'])
                    #data['matriculas'] = Matricula.objects.filter().order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2')
                    horas_v = int(request.GET['horasmod'])
                    inscritos = EstudianteVinculacion.objects.filter(actividad=vinculacion).values('inscripcion')
                    for m in Inscripcion.objects.filter(id__in=inscritos):
                        # print((m))
                        if m.tiene_vinculacion():
                            if EstudianteVinculacion.objects.filter(actividad=vinculacion,inscripcion=m).exists():
                                participante = EstudianteVinculacion.objects.filter(actividad=vinculacion,inscripcion=m)[:1].get()
                            # else:
                            #     participante = EstudianteVinculacion.objects.filter(inscripcion=m.inscripcion,actividad=vinculacion)[:1].get()
                            if  m.malla_inscripcion().malla.nueva_malla:
                                malla = Malla.objects.get(carrera=m.malla_inscripcion().inscripcion.carrera)
                                asig = AsignaturaMalla.objects.get(Q(asignatura__nombre__icontains='PREPRO',malla=malla,nivelmalla=idnivelmalla)|Q(asignatura__nombre__icontains='COMUNI',malla=malla,nivelmalla=idnivelmalla))

                                horas_v1= m.estudiantevinculacion_set.all().aggregate(Sum('horas'))['horas__sum']
                                horastotal = horas_v+horas_v1

                                if horastotal<=asig.horas:

                                    participante.horas=horas_v
                                    participante.nivelmalla=idnivelmalla
                                    participante.save()
                                    carrera = participante.inscripcion.carrera.nombre
                                    actividad=participante.actividad.nombre
                                    estudiantes_modificahoras.append((m.persona.nombre_completo(),elimina_tildes(m.carrera.nombre)))
                                    #Obtain client ip address
                                    client_address = ip_client_address(request)
                                    # Log de adicionar Actividad VINCULACION
                                    LogEntry.objects.log_action(
                                        user_id         = request.user.pk,
                                        content_type_id = ContentType.objects.get_for_model(m).pk,
                                        object_id       = m.id,
                                        object_repr     = force_str(vinculacion),
                                        action_flag     = CHANGE,
                                        change_message  = 'Adicionado Estudiante  Actividad (' + client_address + ')' )
                                else:
                                    estudiantes_nomodificahoras.append((m.persona.nombre_completo(),elimina_tildes(m.carrera.nombre)))
                            else:

                                horas_va= m.estudiantevinculacion_set.all().aggregate(Sum('horas'))['horas__sum']
                                if (horas_v + horas_va if horas_va!=None else 0 )<= HORAS_VINCULACION :

                                    participante.horas=horas_v
                                    participante.save()
                                    carrera = participante.inscripcion.carrera.nombre
                                    actividad=participante.actividad.nombre
                                    estudiantes_modificahoras.append((m.persona.nombre_completo(),elimina_tildes(m.carrera.nombre)))
                                    #Obtain client ip address
                                    client_address = ip_client_address(request)
                                    # Log de adicionar Actividad VINCULACION
                                    LogEntry.objects.log_action(
                                        user_id         = request.user.pk,
                                        content_type_id = ContentType.objects.get_for_model(m).pk,
                                        object_id       = m.id,
                                        object_repr     = force_str(vinculacion),
                                        action_flag     = CHANGE,
                                        change_message  = 'Adicionado Estudiante  Actividad (' + client_address + ')' )
                                else:
                                    estudiantes_nomodificahoras.append((m.persona.nombre_completo(),elimina_tildes(m.carrera.nombre)))

                            # else:
                            #     if not EstudianteVinculacion.objects.filter(actividad=vinculacion,inscripcion=m.inscripcion,nivelmalla=idnivelmalla).exists():
                            #         participante = EstudianteVinculacion(actividad=vinculacion,
                            #                                   inscripcion=m.inscripcion,
                            #                                   horas=horas_v,nivelmalla=idnivelmalla)
                            #         participante.save()
                            #
                            #     carrera = participante.inscripcion.carrera.nombre
                            #     actividad=participante.actividad.nombre
                            #     participante.correo_vinculacion(request.user,'SE HA AGREGADO ACTIVIDAD DE VINCULACION CON LA COMUNIDAD',horas_v,carrera,actividad)
                            #
                            #     #Obtain client ip address
                            #     client_address = ip_client_address(request)
                            #     # Log de Modificar VINCULACION
                            #     LogEntry.objects.log_action(
                            #         user_id         = request.user.pk,
                            #         content_type_id = ContentType.objects.get_for_model(m.inscripcion).pk,
                            #         object_id       = m.inscripcion.id,
                            #         object_repr     = force_str(vinculacion),
                            #         action_flag     = CHANGE,
                            #         change_message  = 'Modificado Estudiante  Actividad (' + client_address + ')' )

                    if len(estudiantes_modificahoras)>0:
                        modificahoras_vinculacion('SE HA MODIFICADO HORAS ACTIVIDAD DE VINCULACION CON LA COMUNIDAD',estudiantes_modificahoras,request.user)


                    if len(estudiantes_nomodificahoras)>0:
                        modificahoras_vinculacion('NO SE HA MODIFICADO HORAS ACTIVIDAD DE VINCULACION CON LA COMUNIDAD PORQUE SUPERA A LA CANTIDAD DE HORA ASIGNADA A ESE NIVEL',estudiantes_modificahoras,request.user)

                    return HttpResponseRedirect("/vinculacion?action=participantes&id="+str(vinculacion.id))

                elif action == 'cambiarnivel':
                    data = {'title': 'Estudiantes'}
                    addUserData(request,data)
                    vinculacion = ActividadVinculacion.objects.get(pk=int(request.GET['idvinculacion']))
                    nivelmallaid=NivelMalla.objects.get(pk=int(request.GET['id']))
                    listaestudiante= EstudianteVinculacion.objects.filter(actividad=vinculacion).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2')
                    for a in listaestudiante:
                        estudivinc=EstudianteVinculacion.objects.get(pk=a.id)
                        # if estudivinc.nivelmalla==None:
                        estudivinc.nivelmalla=nivelmallaid
                        estudivinc.save()
                        client_address = ip_client_address(request)
                        # Log de adicionar Actividad VINCULACION
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(estudivinc).pk,
                            object_id       = estudivinc.id,
                            object_repr     = force_str(estudivinc),
                            action_flag     = CHANGE,
                            change_message  = 'Agregar Nivel (' + client_address + ')' )

                    return HttpResponseRedirect("/vinculacion?action=participantes&id="+str(vinculacion.id))

                elif action == 'eliminardocu':
                    d =  DocumentosVinculacionEstudiantes.objects.get(pk=request.GET['id'])

                    #Obtain client ip address
                    client_address = ip_client_address(request)
                    # Log de Eliminar documento Vinculacion Estudiantes
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(d).pk,
                        object_id       = d.id,
                        object_repr     = force_str(d),
                        action_flag     = DELETION,
                        change_message  = 'Eliminado Documento Vinculacion Estudiante  (' + client_address + ')'  )
                    d.delete()

                    return HttpResponseRedirect("/vinculacion?action=documentosestudiantes")

                elif action == 'cambiarnivelindividual':
                    data = {'title': 'Estudiantes'}
                    addUserData(request,data)
                    vinculacion = ActividadVinculacion.objects.get(pk=int(request.GET['idvinculacion']))
                    nivelmallaid=NivelMalla.objects.get(pk=int(request.GET['id']))

                    estudivinc= EstudianteVinculacion.objects.get(pk=int(request.GET['idregistro']))

                    if estudivinc.nivelmalla==None:
                        estudivinc.nivelmalla=nivelmallaid
                        estudivinc.save()
                        client_address = ip_client_address(request)
                        # Log de adicionar Actividad VINCULACION
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(estudivinc).pk,
                            object_id       = estudivinc.id,
                            object_repr     = force_str(estudivinc),
                            action_flag     = CHANGE,
                            change_message  = 'Agregar Nivel (' + client_address + ')' )

                return HttpResponseRedirect("/vinculacion?action=participantes&id="+str(vinculacion.id))

            else:
                search = ""
                activos = None
                inactivos = None
                todos = None

                if 's' in request.GET:
                    search = request.GET['s']
                if 't' in request.GET:
                    todos = request.GET['t']
                if 'a' in request.GET:
                    activos = request.GET['a']
                if 'i' in request.GET:
                    inactivos = request.GET['i']

                if search:
                    actividad = ActividadVinculacion.objects.filter(Q(programa__nombre__icontains=search)|Q(nombre__icontains=search)).order_by('-inicio')
                else:
                    actividad = ActividadVinculacion.objects.all().order_by('-inicio')
                if todos:
                    actividad = ActividadVinculacion.objects.all().order_by('-inicio')
                if activos:
                    actividad = ActividadVinculacion.objects.filter(activo=True).order_by('-inicio')
                if inactivos:
                    actividad = ActividadVinculacion.objects.filter(activo=False).order_by('-inicio')
                if DocumentosVinculacionEstudiantes.objects.filter().exists():
                    data['documentoest']=DocumentosVinculacionEstudiantes.objects.all().order_by('fecha')
                if 'tipo' in request.GET:
                    if request.GET['tipo'] == 't':
                        actividad = ActividadVinculacion.objects.all().order_by('-inicio')
                    else:
                        tipo = TipoConvenio.objects.filter(pk=request.GET['tipo'])[:1].get()
                        data['tipo_id'] = tipo
                        actividad = ActividadVinculacion.objects.filter(convenio__tipo=tipo).order_by('-inicio')

                paging = MiPaginador(actividad, 30)
                p = 1
                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                        paging = MiPaginador(actividad, 30)
                    page = paging.page(p)
                except Exception as ex:
                    page = paging.page(1)

                data['paging'] = paging
                data['rangospaging'] = paging.rangos_paginado(p)
                data['page'] = page
                data['actividad'] = page.object_list
                data['search'] = search if search else ""
                data['todos'] = todos if todos else ""
                data['activos'] = activos if activos else ""
                data['inactivos'] = inactivos if inactivos else ""
                data['tipo_convenio'] = TipoConvenio.objects.filter().order_by('nombre')
                return render(request ,"vinculacion/vinculacion.html" ,  data)
        except Exception as ex:
            print(ex)
            pass


def correo_aprobacionvinculacion(user,contenido,estudiantes):
    if TipoIncidencia.objects.filter(pk=INCIDENCIA_PRAC_VINC).exists():
        tipo = TipoIncidencia.objects.get(pk=INCIDENCIA_PRAC_VINC)
        hoy = datetime.now().today()
        contenido = contenido
        send_html_mail(contenido,
            "emails/practicas_vinculacion.html", {'fecha': hoy,'contenido': contenido, 'usuario': user,'op':'3','estudiantes':estudiantes},tipo.correo.split(","))

def no_aprobacion_vinculacion(contenido,estudiantes,user):
    if TipoIncidencia.objects.filter(pk=INCIDENCIA_PRAC_VINC).exists():
        tipo = TipoIncidencia.objects.get(pk=INCIDENCIA_PRAC_VINC)
        hoy = datetime.now().today()
        persona = Persona.objects.get(usuario=user)
        asunto="NO APROBACION VINCULACION"
        contenido = contenido
        send_html_mail(str(asunto),"emails/practicas_vinculacion.html", {'fecha': hoy,'contenido': contenido, 'usuario': user,'estudiantes':estudiantes,'op':'4'},tipo.correo.split(","))


def modificahoras_vinculacion(contenido,estudiantes,user):
    if TipoIncidencia.objects.filter(pk=INCIDENCIA_PRAC_VINC).exists():
        tipo = TipoIncidencia.objects.get(pk=INCIDENCIA_PRAC_VINC)
        hoy = datetime.now().today()
        persona = Persona.objects.get(usuario=user)
        asunto="MODIFICACION HORAS VINCULACION"
        contenido = contenido
        send_html_mail(str(asunto),"emails/practicas_vinculacion.html", {'fecha': hoy,'contenido': contenido, 'usuario': user,'estudiantes':estudiantes,'op':'5'},tipo.correo.split(","))
