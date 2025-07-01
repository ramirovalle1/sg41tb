import json
from django.contrib.admin.models import ADDITION,CHANGE, LogEntry, DELETION
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_str
from settings import ESPECIE_CAMBIO_PROGRAMACION, NOTA_PARA_APROBAR, EMAIL_ACTIVE, DIAS_ESPECIE, MODELO_EVALUACION, EVALUACION_CASADE, \
     NIVEL_MALLA_CERO,DEFAULT_PASSWORD,TIPO_OTRO_RUBRO, VALIDA_PRECEDENCIA, ASIST_PARA_APROBAR, GENERAR_RUBROS_PAGO, NIVEL_MALLA_UNO, \
     ESPECIE_RETIRO_MATRICULA,ESPECIE_JUSTIFICA_FALTA, ESPECIE_JUSTIFICA_FALTA_AU,ESPECIE_REINGRESO, ID_TIPO_ESPECIE_REG_NOTA,\
     ESPECIE_ASENTAMIENTO_NOTA,ESPECIE_EXAMEN,ESPECIE_RECUPERACION,ESPECIE_MEJORAMIENTO,MEDIA_ROOT, EXAMEN_CONVALIDACION, ESPECIES_ASENTAMIENTO_NOTAS
from sga.models import convertir_fecha, RubroEspecieValorada,MateriaAsignada, Rubro, Grupo, RubroOtro, InscripcionGrupo, RecordAcademico, \
     HistoricoRecordAcademico, EliminacionMatricula, Nivel, Reporte, Matricula, TipoOtroRubro, PagoNivel, TIPOS_PAGO_NIVEL, Leccion, \
     AsistenciaLeccion, RubroMatricula, RubroCuota, EspecieGrupo, GrupoCoordinadorCarrera, DepartamentoGroup, Carrera, AsistenteDepartamento, \
     CoordinacionDepartamento, SeguimientoEspecie, CoordinadorCarrera, Departamento, elimina_tildes, TipoEspecieValorada, Persona, \
     HorarioAsistenteSolicitudes, ProfesorMateria, GestionTramite, SolicitudSecretariaDocente, Inscripcion, SolicitudEstudiante, \
     IncidenciaAsignada,Coordinacion,TituloInstitucion,CoordinadorCarrera, ExamenConvalidacionIngreso, Profesor, EvaluacionAlcance, InscripcionTestIngreso
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.core.paginator import Paginator
from sga.commonviews import addUserData, ip_client_address
from django.template import RequestContext
from sga.forms import ControlEspeciesForm,ControlEspeciesSecretariaForm, DescuentoForm, DetalleDescuentoForm, ControlCambioProgramacionForm, RubrosCambioProgramacionForm, \
     RubroNivelCambioProgramacionForm, RetiradoMatriculaForm, RespuestaEspecieForm, SeguimientoEspecieForm,RangoGestionForm, ExamenConvalidacionIngresoForm,RubroEspecieValoradaForm
# from settings import  EMAIL_ACTIVE,UTILIZA_GRUPOS_ALUMNOS,CENTRO_EXTERNO,INSCRIPCION_CONDUCCION
from datetime import datetime, timedelta
import sys
import xlwt
from decorators import secure_module
from django.db.models.query_utils import Q
from sga.tasks import send_html_mail
from decimal import Decimal


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


def correo_profesor(especie,emailestudiante,auxiliar):
        hoy = datetime.now().today()
        email=emailestudiante
        asunto = "Estimado/a Docente se ha asignado un tramite #" +str(especie.serie)
        contenido = "ESPECIE " + str(especie.tipoespecie.nombre)
        send_html_mail(str(asunto),"emails/especie_coordinador.html", {'fecha': hoy,'contenido': contenido, 'asunto': asunto,'especie':especie,'auxiliar':auxiliar},email.split(","))

def correo_coordinador(especie,emailestudiante):
        hoy = datetime.now().today()
        email=emailestudiante
        asunto = "Estimado/a Coordinador se ha asignado un tramite #" +str(especie.serie)
        contenido = "ESPECIE " + str(especie.tipoespecie.nombre)
        send_html_mail(str(asunto),"emails/especie_coordinador.html", {'fecha': hoy,'contenido': contenido, 'asunto': asunto,'especie':especie},email.split(","))

def mail_correoalumnoespecie_finaliza(especie,emailestudiante):
        hoy = datetime.now().today()
        email=emailestudiante
        asunto = "Su tramite #" +str(especie.serie) + " ha sido finalizado"
        contenido = "ESPECIE " + elimina_tildes(especie.tipoespecie.nombre)
        send_html_mail(str(asunto),"emails/correoalumno_especie_finaliza.html", {'fecha': hoy,'contenido': contenido, 'asunto': asunto,'especie':especie},email.split(","))

def mail_iniciohorario(email,horarioasistente,persona,asunto):
        hoy = datetime.now().today()
        email=email
        asunto = asunto
        contenido = ""
        hoy = datetime.now()
        send_html_mail(str(asunto),"emails/ingreso_horario.html", {'fecha': hoy,'contenido': contenido, 'asunto': asunto,'horarioasistente' :horarioasistente,'persona':persona,'hoy':hoy},email)
@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
@transaction.atomic()

def view(request):

    if request.method=='POST':
        action = request.POST['action']

        if action == 'registro':
            f = ControlEspeciesForm(request.POST,request.FILES)
            rubroespecie = RubroEspecieValorada.objects.get(pk=request.POST['id'])
            if f.is_valid():
                if 'codigoe' in f.cleaned_data:
                    rubroespecie.codigoe=f.cleaned_data['codigoe'].upper()
                rubroespecie.observaciones=f.cleaned_data['observaciones']
                rubroespecie.aplicada= True
                rubroespecie.fecha=datetime.now().date()
                rubroespecie.usuario=request.user
                rubroespecie.fechafinaliza = datetime.now()
                rubroespecie.habilita = False
                # rubroespecie.destinatario=f.cleaned_data['destinatario'].upper()


                # if request.POST['reporte_id']:
                #     certificado = Reporte.objects.filter(pk=request.POST['reporte_id'])[:1].get()
                #     rubroespecie.certificado=certificado

                # if request.POST['materia']:
                #     rubroespecie.materia_id=request.POST['materia']
                rubroespecie.save()

                if 'archivo' in request.FILES:
                    rubroespecie.archivo=request.FILES['archivo']
                    rubroespecie.save()
                asis =  AsistenteDepartamento.objects.filter(persona__usuario=rubroespecie.usrasig)[:1].get()
                asis.cantidad = asis.cantidad - 1
                asis.save()

                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(rubroespecie).pk,
                    object_id       = rubroespecie.id,
                    object_repr     = force_str(rubroespecie),
                    action_flag     = ADDITION,
                    change_message  = 'Ingreso de Especie ' )
                if EMAIL_ACTIVE:
                        emailestudiante=elimina_tildes(rubroespecie.rubro.inscripcion.persona.emailinst)+','+elimina_tildes(rubroespecie.rubro.inscripcion.persona.email)
                        mail_correoalumnoespecie_finaliza(rubroespecie,emailestudiante)
                return HttpResponseRedirect("/controlespecies")
            else:
                return HttpResponseRedirect("/controlespecies?action=registro&especie="+str(rubroespecie.id)+'&error=ERROR EN FORMULARIO')
        elif action == 'addregistronota':
            f = ExamenConvalidacionIngresoForm(request.POST)
            rubroespecie = RubroEspecieValorada.objects.get(pk=request.POST['id'])
            if f.is_valid():
                rubroespecie.observaciones=f.cleaned_data['observacion']
                rubroespecie.aplicada= True
                rubroespecie.fecha=datetime.now().date()
                rubroespecie.usuario=request.user
                rubroespecie.fechafinaliza = datetime.now()
                rubroespecie.habilita = False
                rubroespecie.save()
                examen = ExamenConvalidacionIngreso(inscripcion=rubroespecie.rubro.inscripcion,
                                                   aprobada = f.cleaned_data['aprobada'],
                                                   observacion = f.cleaned_data['observacion'],
                                                   nota = f.cleaned_data['nota'])
                examen.save()

                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(rubroespecie).pk,
                    object_id       = rubroespecie.id,
                    object_repr     = force_str(rubroespecie),
                    action_flag     = ADDITION,
                    change_message  = 'Ingreso de Especie ' )
                if EMAIL_ACTIVE:
                        emailestudiante=elimina_tildes(rubroespecie.rubro.inscripcion.persona.emailinst)+','+elimina_tildes(rubroespecie.rubro.inscripcion.persona.email)
                        mail_correoalumnoespecie_finaliza(rubroespecie,emailestudiante)
                return HttpResponseRedirect("/controlespecies")
            else:
                return HttpResponseRedirect("/controlespecies?action=registro&especie="+str(rubroespecie.id)+'&error=ERROR EN FORMULARIO')
        elif action == 'quitarautorizar':
            result = {}
            try:
                rubroespecie = RubroEspecieValorada.objects.get(pk=request.POST['id'])
                rubroespecie.autorizado=False
                rubroespecie.obsautorizar = None
                rubroespecie.usrautoriza = None
                rubroespecie.save()

                if InscripcionTestIngreso.objects.filter(rubroespecie=rubroespecie.id).exists():
                   inscriptesde=InscripcionTestIngreso.objects.filter(rubroespecie=rubroespecie.id)[:1].get()
                   inscriptesde.aplicada=False
                   inscriptesde.save()

                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                    user_id=request.user.pk,
                    content_type_id=ContentType.objects.get_for_model(rubroespecie).pk,
                    object_id=rubroespecie.id,
                    object_repr=force_str(rubroespecie),
                    action_flag=CHANGE,
                    change_message='Resolucion Eliminada' + ' (' + client_address + ')')
                result['result'] = "ok"
                return HttpResponse(json.dumps(result), content_type="application/json")
            except Exception as e:
                result['result'] = str(e)
                return HttpResponse(json.dumps(result), content_type="application/json")
        elif action == 'verregistros':
            registros = []
            errores = []
            data = {}
            try:
                inscripcion = Inscripcion.objects.filter(id=request.POST['inscripcionid'])[:1].get()
                especie = SolicitudEstudiante.objects.filter(inscripcion=inscripcion).order_by('-fecha',)
                for e in especie:
                    try:
                        usuario=''
                        fechaa=''
                        if RubroEspecieValorada.objects.filter(rubro=e.rubro).exists():
                            tramite = RubroEspecieValorada.objects.filter(rubro=e.rubro)[:1].get()
                            if tramite.usrasig:
                                usuario=tramite.usrasig.username
                            if tramite.aplicada :
                                finalizada='FINALIZADA'
                            else:
                                if tramite.autorizado:
                                    finalizada='EN PROCESO'
                                else:
                                    if  tramite.usrautoriza:
                                        finalizada='NO APROBADA'
                                    else:
                                        finalizada='EN PROCESO'
                            usrautoriza=''
                            if tramite.usrautoriza:
                                usrautoriza=tramite.usrautoriza.username
                            nombre = tramite.tipoespecie.nombre
                            if tramite.es_online().materia:
                                nombre = nombre +  "<br> Asig: "+  tramite.es_online().materia.materia.asignatura.nombre + "<br> Nivel: " +tramite.es_online().materia.materia.nivel.nivelmalla.nombre+ " " + tramite.es_online().materia.materia.nivel.paralelo
                                if tramite.es_online().profesor:
                                    nombre = nombre + " <br>Docente: " + tramite.es_online().profesor.persona.apellido1 + " "  +tramite.es_online().profesor.persona.apellido2 + " " + tramite.es_online().profesor.persona.nombres
                            if tramite.fechaasigna:
                                fechaa = tramite.fechaasigna.strftime("%d-%m-%Y") + " "+tramite.fechaasigna.strftime("%H:%M")
                            registros.append({'solid':e.id,'id':tramite.id,'tipotramite':nombre,'fechat':e.fecha.strftime("%d-%m-%Y") + " " + e.fecha.strftime("%H:%M"),
                                              'fechaa':fechaa,'usrautoriza':usrautoriza,'resolucion':tramite.obsautorizar,'serie':tramite.serie,'obsfinal':tramite.observaciones,
                                              'depart':tramite.dptoactual(),'obsest':e.observacion,'estado':finalizada,'tipo':'TRAMITE','asigando':usuario})
                        else:
                            if SolicitudSecretariaDocente.objects.filter(solicitudestudiante=e).exists():
                                solicitud = SolicitudSecretariaDocente.objects.filter(solicitudestudiante=e)[:1].get()
                                if solicitud.personaasignada:
                                    usuario=solicitud.personaasignada.usuario.username
                                if solicitud.cerrada:
                                    finalizada ='FINALIZADA'
                                else:
                                    finalizada ='EN PROCESO'
                                if solicitud.fechaasignacion:
                                    fechaa = solicitud.fechaasignacion.strftime("%d-%m-%Y") + " " + solicitud.fechaasignacion.strftime("%H:%M")
                                registros.append({'solid':e.id,'id':solicitud.id,'fechat':e.fecha.strftime("%d-%m-%Y") + " " + e.fecha.strftime("%H:%M") ,'fechaa':fechaa,
                                                  'usrautoriza':'','serie':solicitud.id,'tipotramite':e.tipoe.nombre,'resolucion':solicitud.observacion,'obsfinal':solicitud.resolucion,
                                              'depart':solicitud.dptoactual(),'obsest':e.observacion,'estado':finalizada,'tipo':'SOLICITUD','asigando':usuario})
                    except Exception as ex:
                        errores.append(e.id)
                        print("ERROR: ("+str(ex)+"), ID's: ("+str(errores)+")")

                data['registros'] = registros
                data['inscripcion'] = inscripcion.persona.nombre_completo()
                data['result'] =  'ok'
                if errores:
                    data['errores'] = errores
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as e:
                print(e)
                data['result'] =  'bad'
                return HttpResponse(json.dumps(data), content_type="application/json")

        if action=='edit_especie':
            try:
                print(request.POST['observaciones'])
                especie = RubroEspecieValorada.objects.get(pk=request.POST['id'])
                tipo_especie = TipoEspecieValorada.objects.get(pk=request.POST['tipo_especie'])
                mensaje = 'Especie editada de '+ elimina_tildes(especie.tipoespecie.nombre) + ' a '
                especie.tipoespecie = tipo_especie
                especie.observaciones = elimina_tildes(request.POST['observaciones']).upper()
                especie.aplicada = True if str(request.POST['aplicada']) == 'true' else False
                especie.disponible = True if str(request.POST['disponible']) == 'true' else False
                especie.save()
                mensaje += elimina_tildes(especie.tipoespecie.nombre)

                if SolicitudEstudiante.objects.filter(rubro=especie.rubro).exists():
                    solicitud=SolicitudEstudiante.objects.filter(rubro=especie.rubro).order_by('-id')[:1].get()
                    solicitud.tipoe = tipo_especie
                    solicitud.save()
                    if especie.tipoespecie.relaciodocente:
                        materia_asignada = MateriaAsignada.objects.get(pk=request.POST['materia_asignada'])
                        profesor = Profesor.objects.get(pk=request.POST['profesor'])
                        solicitud.profesor = profesor
                        solicitud.materia = materia_asignada
                        especie.materia = materia_asignada
                    else:
                        solicitud.profesor = None
                        solicitud.materia = None
                        especie.materia = None
                    solicitud.save()
                especie.save()

                # Log de APLICAR DONACION
                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                user_id         = request.user.pk,
                content_type_id = ContentType.objects.get_for_model(especie).pk,
                object_id       = especie.id,
                object_repr     = force_str(especie),
                action_flag     = CHANGE,
                change_message  = mensaje + ' (' + client_address + ')' )

                return HttpResponse(json.dumps({'result':'ok', 'mensaje':'Especie editada correctamente.'}), content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({'result':'bad', 'mensaje':str(e)}), content_type="application/json")

        elif action == 'filtrarregistro':
            registros=[]
            data = {}
            try:
                inscripcion = Inscripcion.objects.filter(id=request.POST['inscripcionid'])[:1].get()

                usuario=''
                fechaa=''
                if RubroEspecieValorada.objects.filter(rubro__inscripcion=inscripcion,serie=request.POST['serie']).exists():
                    tramite = RubroEspecieValorada.objects.filter(rubro__inscripcion=inscripcion,serie=request.POST['serie'])[:1].get()
                    if tramite.es_online():
                        e = tramite.es_online()
                        if tramite.usrasig:
                            usuario=tramite.usrasig.username
                        if tramite.aplicada :
                            finalizada='FINALIZADA'
                        else:
                            if tramite.autorizado:
                                finalizada='EN PROCESO'
                            else:
                                if  tramite.usrautoriza:
                                    finalizada='NO APROBADA'
                                else:
                                    finalizada='EN PROCESO'
                        usrautoriza=''
                        if tramite.usrautoriza:
                            usrautoriza=tramite.usrautoriza.username
                        if tramite.fechaasigna:
                            fechaa = tramite.fechaasigna.strftime("%d-%m-%Y") + " "+tramite.fechaasigna.strftime("%H:%M")
                        registros.append({'solid':e.id,'id':tramite.id,'tipotramite':tramite.tipoespecie.nombre,'fechat':e.fecha.strftime("%d-%m-%Y") + " " + e.fecha.strftime("%H:%M"),
                                          'fechaa':fechaa,'usrautoriza':usrautoriza,'resolucion':tramite.obsautorizar,'serie':tramite.serie,'obsfinal':tramite.observaciones,
                                          'depart':tramite.dptoactual(),'obsest':e.observacion,'estado':finalizada,'tipo':'TRAMITE','asigando':usuario})
                if SolicitudSecretariaDocente.objects.filter(id=int(request.POST['serie'])).exclude(solicitudestudiante=None).exists():
                    solicitud = SolicitudSecretariaDocente.objects.filter(id=int(request.POST['serie'])).exclude(solicitudestudiante=None)[:1].get()
                    if solicitud.personaasignada:
                        usuario=solicitud.personaasignada.usuario.username
                    if solicitud.cerrada:
                        finalizada ='FINALIZADA'
                    else:
                        finalizada ='EN PROCESO'
                    if solicitud.fechaasignacion:
                        fechaa = solicitud.fechaasignacion.strftime("%d-%m-%Y") + " " + solicitud.fechaasignacion.strftime("%H:%M")
                    registros.append({'solid':solicitud.solicitudestudiante.id,'id':solicitud.id,'fechat':solicitud.solicitudestudiante.fecha.strftime("%d-%m-%Y") + " " + solicitud.solicitudestudiante.fecha.strftime("%H:%M") ,'fechaa':fechaa,
                                      'usrautoriza':'','serie':solicitud.id,'tipotramite':solicitud.solicitudestudiante.tipoe.nombre,'resolucion':solicitud.observacion,'obsfinal':solicitud.resolucion,
                                  'depart':solicitud.dptoactual(),'obsest':solicitud.solicitudestudiante.observacion,'estado':finalizada,'tipo':'SOLICITUD','asigando':usuario})
                data['registros'] = registros
                data['inscripcion'] = inscripcion.persona.nombre_completo()
                data['result'] =  'ok'
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as e:
                print(e)
                data['result'] =  'bad'
                return HttpResponse(json.dumps(data), content_type="application/json")
        elif action == 'consupago':
            pn = PagoNivel.objects.filter(pk=request.POST['id'])[:1].get()
            return HttpResponse(json.dumps({"valor":str(pn.valor)}),content_type="application/json")
        elif  action == 'ingresahorario':
                try:
                    sede = None
                    asistente = AsistenteDepartamento.objects.filter(persona__usuario=request.user)[:1].get()
                    hinicio = None
                    hfin = None
                    nolabora = True
                    if request.POST['nolabora'] == "false":
                        hinicio = request.POST['hinicio']
                        hfin = request.POST['hfin']
                        if datetime.strptime(str(hfin), '%H:%M').time() < datetime.strptime(str(hinicio), '%H:%M').time():
                            return HttpResponse(json.dumps({'result': 'badhora'}), content_type="application/json")
                        nolabora = False

                    if not HorarioAsistenteSolicitudes.objects.filter(usuario=request.user,fecha = datetime.now()).exists():
                        horarioasistente = HorarioAsistenteSolicitudes(usuario=request.user,
                                                            horainicio = hinicio,
                                                            horafin = hfin,
                                                            fecha = datetime.now(),
                                                            fechaingreso=datetime.now(),
                                                            nolabora = nolabora)
                        horarioasistente.save()
                        correo=[]
                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(horarioasistente).pk,
                            object_id       = horarioasistente.id,
                            object_repr     = force_str(horarioasistente),
                            action_flag     = ADDITION,
                            change_message  = 'Adicionado Horario de Asistente'+ ' (' + client_address + ') ')
                        dpto = AsistenteDepartamento.objects.filter(persona__usuario=request.user).values('departamento')
                        for c in AsistenteDepartamento.objects.filter(departamento__id__in=dpto,puedereasignar=True):
                            correo.append(c.persona.emailinst)
                        persona =Persona.objects.filter(usuario=request.user)[:1].get()
                        asunto='NOTIFICACION DE INGRESO DE HORARIO'
                        mail_iniciohorario(correo,horarioasistente,persona,asunto)

                        return HttpResponse(json.dumps({'result': 'ok'}), content_type="application/json")
                    return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")
                except Exception as e:
                    print(e)
                    return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")
        elif action == 'editarhorario':
                try:
                    horarioasistente = HorarioAsistenteSolicitudes.objects.get(id=request.POST['idhorat'])
                    hinicio = None
                    hfin = None
                    nolabora = True
                    antinicio =  horarioasistente.horainicio
                    antfin = horarioasistente.horafin

                    if request.POST['nolabora'] == "false":
                        hinicio = request.POST['hinicio']
                        hfin = request.POST['hfin']
                        nolabora = False
                        hinicio = request.POST['hinicio']
                        hfin = request.POST['hfin']
                        if datetime.strptime(str(hfin), '%H:%M').time() < datetime.strptime(str(hinicio), '%H:%M').time():
                            return HttpResponse(json.dumps({'result': 'badhora'}), content_type="application/json")
                    horarioasistente.horainicio = hinicio
                    horarioasistente.horafin = hfin
                    horarioasistente.fecha = datetime.now()
                    horarioasistente.usuario = request.user
                    horarioasistente.nolabora = nolabora
                    horarioasistente.save()
                    correo=[]
                    dpto = AsistenteDepartamento.objects.filter(persona__usuario=request.user).values('departamento')
                    for c in AsistenteDepartamento.objects.filter(departamento__id__in=dpto,puedereasignar=True):
                            correo.append(c.persona.emailinst)
                    persona =Persona.objects.filter(usuario=request.user)[:1].get()
                    asunto='NOTIFICACION DE EDICION DE HORARIO'
                    mail_iniciohorario(correo,horarioasistente,persona,asunto)
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(horarioasistente).pk,
                        object_id       = horarioasistente.id,
                        object_repr     = force_str(horarioasistente),
                        action_flag     = ADDITION,
                        change_message  = 'Modificado Horario de Asistente'+ str(horarioasistente.horainicio) +" / "+ str(horarioasistente.horafin) +" Horario Anterior " + str(antinicio)+" / " + str(antfin)+ ' (' + client_address + ') ')
                    return HttpResponse(json.dumps({'result': 'ok'}), content_type="application/json")
                except Exception as e:
                    print(e)
                    return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")

        if action == 'autorizar':
            try:
                especie = RubroEspecieValorada.objects.filter(pk=request.POST['idespecie'])[:1].get()
                if request.POST['aprobado'] =='1':
                    especie.autorizado=True
                else:
                    especie.autorizado=False
                # if request.POST['dpto']:
                #     especie.departamento_id=int(request.POST['dpto'])
                # else:
                #     especie.departamento_id=None
                especie.obsautorizar = request.POST['respuesta']
                especie.usrautoriza = request.user
                especie.save()
                if not especie.autorizado:
                     asis =  AsistenteDepartamento.objects.filter(persona__usuario=especie.usrasig)[:1].get()
                     asis.cantidad = asis.cantidad - 1
                     asis.save()
                     especie.aplicada= True
                     especie.fecha=datetime.now().date()
                     especie.usuario=request.user
                     especie.fechafinaliza =datetime.now()
                     especie.habilita = False
                     especie.save()
                else:
                    if especie.tipoespecie.relaciodocente:
                        if especie.materia:
                            profesor=especie.es_online().profesor
                            # especie.aplicada= True
                            # especie.fecha=datetime.now().date()
                            # especie.usuario=request.user
                            # especie.fechafinaliza =datetime.now()

                            # if ProfesorMateria.objects.filter(materia=especie.materia.materia).exists():
                            # #     asis =  AsistenteDepa 8 m rtamento.objects.filter(persona__usuario=especie.usrasig)[:1].get()
                            # #     asis.cantidad = asis.cantidad - 1
                            # #     asis.save()
                            #     p=ProfesorMateria.objects.filter(materia=especie.materia.materia).order_by('hasta')[:1].get()
                            #     especie.profesor=p.profesor
                            #     especie.save()
                            #     especie.usrasig=p.profesor.persona.usuario
                            #     especie.fechaasigna = datetime.now()
                            #     especie.save()
                            #OCastillo 26-08-2024 correo de notificacion a docente auxiliar
                            if especie.materia.materia.tiene_prof_aux(especie.es_online().profesor):
                                profesor=especie.materia.materia.tiene_prof_aux(especie.es_online().profesor)
                                correo_profesor(especie, profesor.persona.emailinst,profesor)
                            else:
                                auxiliar=None
                                correo_profesor(especie,profesor.persona.emailinst,auxiliar)
                            gestion = GestionTramite(tramite=especie,
                                                     profesor=profesor.persona,
                                                     fechaasignacion=datetime.now())
                            gestion.save()
                            return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                            # else:
                            #     return HttpResponse(json.dumps({"result":'MATERIA NO TIENE DOCENTE ASOCIADO'}),content_type="application/json")

                    # if especie.autorizado and especie.tipoespecie.coordinadores and especie.usuario == None and especie.aplicada == False :
                    # # for c in RubroEspecieValorada.objects.filter(tipoespecie__coordinadores=True,autorizado=True,usrasig=None,usuario=None,aplicada=False,rubro__fecha__gte='2020-01-01'):
                    # # periodo = Periodo.objects.filter(activo=True).order_by('-fin')[:1].get()
                    #     if CoordinadorCarrera.objects.filter(carrera=especie.rubro.inscripcion.carrera).exists():
                    #         persona = CoordinadorCarrera.objects.filter(carrera=especie.rubro.inscripcion.carrera).order_by('-id')[:1].get().persona
                    #         especie.usrasig = persona.usuario
                    #         especie.save()
                    #         emails=str(persona.emailinst)+','+str(persona.email)
                    #         correo_coordinador(especie,emails)

                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({"result":str(e)}),content_type="application/json")

        elif action == 'cambioprogramacion':
            try:
                datos = json.loads(request.POST['datos'])
                rnoeliminado=""
                reliminado=""
                rubroespecie = RubroEspecieValorada.objects.get(pk=request.POST['especieid'])
                inscripcion = rubroespecie.rubro.inscripcion
                pnid= []
                pagonivel = json.loads(request.POST['nivelpago'])

                for pn in pagonivel:
                    pnid.append(pn['pagoid'])
                if not rubroespecie.aplicada:
                    rubroespecie.codigoe=request.POST['codigoe'].upper()
                    rubroespecie.observaciones=request.POST['obs']
                    rubroespecie.aplicada= True
                    rubroespecie.fecha= datetime.now().date()
                    rubroespecie.usuario=request.user
                    rubroespecie.habilita = False
                    rubroespecie.save()
                    nivel = Nivel.objects.filter(pk=request.POST['nivel'])[:1].get()
                    if not rubroespecie.rubro.inscripcion.matricula():


                        if rubroespecie.rubro.inscripcion.inscripciongrupo_set.exists():
                            rubroespecie.rubro.inscripcion.inscripciongrupo_set.all().delete()

                        ig = InscripcionGrupo(inscripcion=rubroespecie.rubro.inscripcion, grupo=nivel.grupo, activo=True)
                        ig.save()
                        rubroespecie.rubro.inscripcion.carrera = ig.grupo.carrera
                        rubroespecie.rubro.inscripcion.modalidad = ig.grupo.modalidad
                        rubroespecie.rubro.inscripcion.sesion = ig.grupo.sesion
                        rubroespecie.rubro.inscripcion.save()
                        for d in datos['detalle']:
                            try:
                                rubro = Rubro.objects.filter(pk=d['rubro'])[:1].get()
                                if rubro.puede_eliminarse():
                                    reliminado = reliminado + str(rubro.nombre()) + " - "

                                    if RubroOtro.objects.filter(rubro=rubro).exists():
                                        RubroOtro.objects.filter(rubro=rubro)[:1].get().delete()
                                    rubro.delete()

                                else:
                                    rnoeliminado = rnoeliminado + str(rubro.nombre()) + " - "
                            except:
                                    pass

                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(rubroespecie).pk,
                            object_id       = rubroespecie.id,
                            object_repr     = force_str(rubroespecie),
                            action_flag     = ADDITION,
                            change_message  = 'Se Realizo cambio de Programacion a grupo '+ str(nivel.grupo.nombre) + ' (' + client_address + ') '+ reliminado)
                        asis =  AsistenteDepartamento.objects.filter(persona__usuario=rubroespecie.usrasig)[:1].get()
                        asis.cantidad = asis.cantidad - 1
                        rubroespecie.usuario=request.user
                        rubroespecie.fechafinaliza = datetime.now()
                        rubroespecie.save()
                        asis.save()
                        rubroespecie.save()
                    if  EMAIL_ACTIVE:
                        rubroespecie.correo(request.user.username,reliminado)

                    matricula = Matricula(inscripcion=inscripcion,
                                nivel=nivel,
                                pago=False,
                                iece=False,
                                becado=False,
                                porcientobeca=0)
                    matricula.save()

                    materias = nivel.materia_set.filter(Q(cerrado=False)|Q(cerrado=None))

                    #Actualizar el registro de InscripcionMalla con la malla correspondiente
                    im = inscripcion.malla_inscripcion()
                    im.malla = matricula.nivel.malla
                    im.save()
                    for materia in materias:
                        asignatura = materia.asignatura
                        if not inscripcion.ya_aprobada(asignatura):
                            # Si no la tiene aprobada aun
                            # pendientes = self.recordacademico_set.filter(asignatura__in=asignatura.precedencia.all(),aprobada=False)
                            if VALIDA_PRECEDENCIA:
                                if inscripcion.carrera.online:
                                    asistenciaparaaprobar = 0
                                else:
                                    asistenciaparaaprobar=ASIST_PARA_APROBAR
                                if inscripcion.recordacademico_set.filter(asignatura__in=asignatura.precedencia.all().values('id'),nota__gte=NOTA_PARA_APROBAR,asistencia__gte=asistenciaparaaprobar).exists() or not asignatura.precedencia.all():
                                # if pendientes.count()==0:
                                    if not MateriaAsignada.objects.filter(matricula=matricula,materia=materia).exists():
                                        asign = MateriaAsignada(matricula=matricula,materia=materia,notafinal=0,asistenciafinal=0,supletorio=0)
                                        asign.save()

                                    # Correccion de Lecciones ya impartidas
                                        leccionesYaDadas = Leccion.objects.filter(clase__materia=asign.materia)
                                        for leccion in leccionesYaDadas:
                                            asistenciaLeccion = AsistenciaLeccion(leccion=leccion,matricula=matricula,asistio=False)
                                            asistenciaLeccion.save()
                            else:
                                pendientes = inscripcion.recordacademico_set.filter(asignatura__in=asignatura.precedencia.all(),aprobada=False)
                                if pendientes.count()==0:
                                    if  not MateriaAsignada.objects.filter(matricula=matricula,materia=materia).exists():
                                        asign = MateriaAsignada(matricula=matricula,materia=materia,notafinal=0,asistenciafinal=0,supletorio=0)
                                        asign.save()

                                    # Correccion de Lecciones ya impartidas
                                        leccionesYaDadas = Leccion.objects.filter(clase__materia=asign.materia)
                                        for leccion in leccionesYaDadas:
                                            asistenciaLeccion = AsistenciaLeccion(leccion=leccion,matricula=matricula,asistio=False)
                                            asistenciaLeccion.save()
                                else:
                                    recordPendiente = RecordAcademico(inscripcion=inscripcion,asignatura=asignatura,nota=0,asistencia=0,fecha=datetime.now(),convalidacion=False,aprobada=False,pendiente=True)
                                    recordPendiente.save()
                    if GENERAR_RUBROS_PAGO and not inscripcion.beca_senescyt().tienebeca:

                        pp = 1.0 if not matricula.becado else ((100-matricula.porcientobeca)/100.0)

                        for pago in nivel.pagonivel_set.all().exclude(id__in=pnid):
                            if pago.tipo==0 or (pago.tipo>0 and pp>0):
                                rubro = Rubro(fecha=datetime.today().date(),
                                    valor = pago.valor, inscripcion=inscripcion,
                                    cancelado = False, fechavence = pago.fecha)

                                rubro.save()

                                # Beca
                                if matricula.becado and pago.tipo!=0:
                                    rubro.valor *= pp
                                    rubro.save()

                                if matricula.inscripcion.promocion :
                                    if pago.tipo!=0 and matricula.inscripcion.promocion.todos_niveles and DEFAULT_PASSWORD == 'itb' and matricula.nivel.nivelmalla.id != NIVEL_MALLA_UNO:

                                        des = ((100-matricula.inscripcion.descuentoporcent)/100.0)
                                        rubro.valor *= des
                                        rubro.save()

                                    elif matricula.inscripcion.promocion and pago.tipo!=0 and matricula.nivel.nivelmalla.id == NIVEL_MALLA_CERO and DEFAULT_PASSWORD == 'itb':
                                        des = ((100-matricula.inscripcion.descuentoporcent)/100.0)
                                        rubro.valor *= des
                                        rubro.save()
                                # if matricula.inscripcion.promocion.val_inscripcion> 0

                                if pago.tipo==0:
                                    rm = RubroMatricula(rubro=rubro, matricula=matricula)
                                    rm.save()
                                else:
                                    # CUOTA MENSUAL
                                    rc = RubroCuota(rubro=rubro, matricula=matricula, cuota=pago.tipo)
                                    rc.save()

                    if matricula.nivel.nivelmalla.id == NIVEL_MALLA_UNO and DEFAULT_PASSWORD == 'itb':
                        if  Matricula.objects.filter(inscripcion=matricula.inscripcion,nivel__nivelmalla__id=NIVEL_MALLA_CERO).exists():
                            mat =  Matricula.objects.filter(inscripcion=matricula.inscripcion,nivel__nivelmalla__id=NIVEL_MALLA_CERO)[:1].get()
                            if  mat.becado:
                                matricula.becado = True
                                matricula.porcientobeca = mat.porcientobeca
                                matricula.tipobeca = mat.tipobeca
                                matricula.motivobeca  = mat.motivobeca
                                matricula.tipobeneficio  = mat.tipobeneficio
                                matricula.fechabeca = datetime.now()
                                matricula.save()

                                if GENERAR_RUBROS_PAGO:
                                    pp = (100-matricula.porcientobeca)/100.0

                                    # Aplicar el % de Beca por cada Rubro Real q tenga el estudiante matriculado
                                    for rubro in matricula.inscripcion.rubro_set.all():
                                        #El tipo Otro es solo para pasar los historicos, luego quitarlo y dejar solo si es cuota
                                        if rubro.es_cuota() and rubro.total_pagado()==0:
                                            if pp==0:
                                                rubro.delete()
                                            else:
                                                rubro.valor *= pp
                                                rubro.save()
                        # for rubro in matricula.inscripcion.rubro_set.all():
                            #El tipo Otro es solo para pasar los historicos, luego quitarlo y dejar solo si es cuota
                        for rubro in  matricula.rubrocuota_set.all():
                            if rubro.rubro.es_cuota() and rubro.rubro.total_pagado()==0:
                                if matricula.inscripcion.promocion:
                                    des = ((100-matricula.inscripcion.descuentoporcent)/100.0)
                                    rubro.rubro.valor *= des
                                    rubro.rubro.save()

                    # rubroespecie.rubro.inscripcion.matricular(nivel)
                    return HttpResponse(json.dumps({"result":"ok",'rnoeliminado':rnoeliminado,'reliminado':reliminado}),content_type="application/json")
                else:
                    return HttpResponse(json.dumps({"result":"bad2"}),content_type="application/json")

            except Exception as e:
                return HttpResponse(json.dumps({"result":"bad",'e':str(e)}),content_type="application/json")

        elif action =='consultaasis':
                data = {}
                try:
                    usuarios=[]
                    especie = RubroEspecieValorada.objects.filter(pk=request.POST['id'])[:1].get()
                    user = request.user
                    usuarios.append({'id': user.id, 'usuario': user.username})
                    dpto = Departamento.objects.filter(controlespecies=True,asistentedepartamento__persona__usuario = especie.usrasig).exclude(id=27).values('id')
                    for a in AsistenteDepartamento.objects.filter(departamento__id__in =dpto,activo=True).order_by('persona__apellido1','persona__apellido2','persona__nombres').exclude(persona__usuario=especie.usrasig).exclude(puedereasignar=True):

                        usuarios.append({'id':a.id,'usuario': elimina_tildes(a.persona.usuario.username)})
                    data['result'] = 'ok'
                    data['usuarios'] = usuarios
                    return HttpResponse(json.dumps(data), content_type="application/json")
                except Exception as e:
                    # print(e)
                    return HttpResponse(json.dumps({"result":"bad",'e':str(e)}),content_type="application/json")

        elif action =='consulta':
                data = {}
                try:
                    departamento=[]
                    # especie = RubroEspecieValorada.objects.filter(pk=request.POST['id'])[:1].get()
                    # carrera = especie.rubro.inscripcion.grupo().carrera
                    # dpt = CoordinacionDepartamento.objects.filter(coordinacion__carrera=carrera).distinct('departamento').values('departamento')
                    for d in Departamento.objects.filter(controlespecies=True ).exclude(id=27).order_by('descripcion'):
                    # for d in Departamento.objects.filter(controlespecies=True,id__in =dpt ).order_by('descripcion'):
                        departamento.append({'id':d.id,'descripcion': elimina_tildes(d.descripcion) })
                    data['result'] = 'ok'
                    data['op'] = 'materia'
                    data['departamento'] = departamento
                    return HttpResponse(json.dumps(data), content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({"result":"bad",'e':str(e)}),content_type="application/json")

        elif action =='reasignar':
                try:
                    departamento=Departamento.objects.filter(id=request.POST['dpto'])[:1].get()
                    especie = RubroEspecieValorada.objects.filter(pk=request.POST['id'])[:1].get()
                    if especie.usrasig:
                        asis =  AsistenteDepartamento.objects.filter(persona__usuario=especie.usrasig)[:1].get()
                        asis.cantidad = asis.cantidad - 1
                        asis.save()
                        seguimiento = SeguimientoEspecie(rubroespecie=especie,
                                                 observacion='REASIGNACION DE DEPARTAMENTO',
                                                 usuario = request.user,
                                                 fecha = datetime.now(),
                                                 asistente=especie.usrasig,
                                                 fechaasig = especie.fechaasigna,
                                                 asistentedepartamento=asis,
                                                 hora=datetime.now().time())
                        seguimiento.save()
                    asistentes=None
                    if HorarioAsistenteSolicitudes.objects.filter(fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time()).exists():
                         horarioasis = HorarioAsistenteSolicitudes.objects.filter(fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time()).values('usuario')
                         asistentes = AsistenteDepartamento.objects.filter(departamento=departamento,persona__usuario__id__in=horarioasis,activo=True).exclude(puedereasignar=True).values('id')
                         if asistentes:

                             asistente = AsistenteDepartamento.objects.filter(departamento=departamento,id__in=asistentes,activo=True).exclude(puedereasignar=True).order_by('cantidad')[:1].get()
                             especie.usrasig = asistente.persona.usuario
                             especie.fechaasigna=datetime.now()
                             especie.departamento = asistente.departamento
                             especie.save()
                             asistente.cantidad = asistente.cantidad + 1
                             asistente.save()


                             asistente.correo_reasignacion(request.user,especie)
                             return HttpResponse(json.dumps({"result":"ok" }), content_type="application/json")

                    especie.departamento=departamento
                    especie.usrasig = None
                    # especie.asignado=False
                    especie.save()

                    return HttpResponse(json.dumps({"result":"ok" }), content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({"result":"bad",'e':str(e)}),content_type="application/json")
        elif action =='reasignarusuario':
                try:
                    # usuario=User.objects.filter(id=request.POST['usuario'])
                    asistente = AsistenteDepartamento.objects.filter(id=request.POST['usuario'])[:1].get()
                    # persona = Persona.objects.filter(usuario=usuario)[:1].get()
                    especie = RubroEspecieValorada.objects.filter(pk=request.POST['id'])[:1].get()
                    asis=None
                    if especie.usrasig:
                        asis =  AsistenteDepartamento.objects.filter(persona__usuario=especie.usrasig,departamento=asistente.departamento)[:1].get()
                        asis.cantidad = asis.cantidad - 1
                        asis.save()
                    usuarioasintente = especie.usrasig
                    fechaasigna = especie.fechaasigna

                    # asistente = AsistenteDepartamento.objects.filter(persona=asistente.persona,departamento=asistente.departamento).order_by('cantidad')[:1].get()
                    especie.usrasig = asistente.persona.usuario
                    especie.fechaasigna=datetime.now()
                    especie.save()
                    asistente.cantidad = asistente.cantidad + 1

                    asistente.save()
                    seguimiento = SeguimientoEspecie(rubroespecie=especie,
                                         observacion='REASIGNACION DE USUARIO',
                                         usuario = request.user,
                                         fecha = datetime.now(),
                                         asistente =usuarioasintente,
                                         fechaasig=fechaasigna,
                                         asistentedepartamento=asis,
                                         hora=datetime.now().time())
                    seguimiento.save()
                    asistente.correo_reasignacion(request.user,especie)
                    return HttpResponse(json.dumps({"result":"ok" }), content_type="application/json")
                except Exception as e:
                    # print(e)
                    return HttpResponse(json.dumps({"result":"bad",'e':str(e)}),content_type="application/json")

        elif action =='desmatricular':
            if Matricula.objects.filter(pk=request.POST['mat']).exists():
                try:
                    matricula = Matricula.objects.get(pk=request.POST['mat'])
                    asignadas = matricula.materiaasignada_set.all()
                    inscripcion = matricula.inscripcion

                    for materiaAsignada in asignadas:
                        if materiaAsignada.notafinal>0:
                            record = RecordAcademico(inscripcion=inscripcion,asignatura=materiaAsignada.materia.asignatura,
                                                nota=materiaAsignada.notafinal,asistencia=materiaAsignada.asistenciafinal,fecha=datetime.now(),
                                                convalidacion=False, aprobada=(materiaAsignada.notafinal >= NOTA_PARA_APROBAR), pendiente=(materiaAsignada.notafinal==0))
                            record.save()
                            historico = HistoricoRecordAcademico(inscripcion=inscripcion, asignatura=materiaAsignada.materia.asignatura,
                                                nota=materiaAsignada.notafinal, asistencia=materiaAsignada.asistenciafinal,fecha=datetime.now(),
                                                convalidacion=False, aprobada=(materiaAsignada.notafinal >= NOTA_PARA_APROBAR), pendiente=(materiaAsignada.notafinal==0))
                            historico.save()

                    nivelid = matricula.nivel_id
                    inscripcion = matricula.inscripcion
                    for record in inscripcion.recordacademico_set.all():
                        if record.esta_pendiente():
                            record.delete()

                        # Corregir Rubros de existir

                    rmat = matricula.rubromatricula_set.all()
                    rcuot = matricula.rubrocuota_set.all()



                    OTRO_RUBRO = TipoOtroRubro.objects.get(pk=TIPO_OTRO_RUBRO)

                    for r in rmat:
                        if not r.rubro.puede_eliminarse():
                            if matricula.inscripcion.promocion and matricula.nivel.nivelmalla.id == NIVEL_MALLA_CERO and DEFAULT_PASSWORD == 'itb':
                                if matricula.inscripcion.promocion.directo:
                                    ro = RubroOtro(rubro=r.rubro, tipo=OTRO_RUBRO, descripcion=r.rubro.nombre())
                                    ro.save()
                                else:
                                    ro = RubroOtro(rubro=r.rubro, tipo=OTRO_RUBRO, descripcion=r.rubro.nombre()+" (MATRICULA BORRADA)")
                                    ro.save()
                            else:
                                ro = RubroOtro(rubro=r.rubro, tipo=OTRO_RUBRO, descripcion=r.rubro.nombre()+" (MATRICULA BORRADA)")
                                ro.save()
                        else:
                            if matricula.inscripcion.promocion and matricula.nivel.nivelmalla.id == NIVEL_MALLA_CERO and DEFAULT_PASSWORD == 'itb':
                                if matricula.inscripcion.promocion.directo:
                                    ro = RubroOtro(rubro=r.rubro, tipo=OTRO_RUBRO, descripcion=r.rubro.nombre())
                                    ro.save()
                                else:
                                    rubro = r.rubro
                                    rubro.delete()
                            else:
                                rubro = r.rubro
                                rubro.delete()

                    for r in rcuot:
                        if not r.rubro.puede_eliminarse():
                            ro = RubroOtro(rubro=r.rubro, tipo=OTRO_RUBRO, descripcion=r.rubro.nombre()+" (MATRICULA BORRADA)")
                            ro.save()
                        else:
                            try:
                                rubro = r.rubro
                                rubro.delete()
                            except Exception as ex:
                                pass

                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de ELIMINAR MATRICULA
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(matricula).pk,
                        object_id       = matricula.id,
                        object_repr     = force_str(matricula),
                        action_flag     = DELETION,
                        change_message  = 'Eliminada Matricula (' + client_address + ')' )

                    eliminacion = EliminacionMatricula(inscripcion=inscripcion, nivel=matricula.nivel, fecha=datetime.now().date(), motivo="CAMBIO DE PROGRAMACION")
                    eliminacion.save()
                    matricula.delete()
                    return HttpResponse(json.dumps({"result":"ok"}), content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({"result":str(e)}), content_type="application/json")
            else:
                return HttpResponse(json.dumps({"result":"No esta Matriculado"}), content_type="application/json")
                # return HttpResponseRedirect("/matriculas?action=matricula&id="+str(nivelid)

            # rubroespecie.save()

        elif action =='addgestion':
            try:
                especie = RubroEspecieValorada.objects.filter(pk=request.POST['idespecie'])[:1].get()
                asis=None
                if AsistenteDepartamento.objects.filter(departamento=especie.departamento,persona__usuario=especie.usrasig).exists():
                    asis = AsistenteDepartamento.objects.filter(departamento=especie.departamento,persona__usuario=especie.usrasig)[:1].get()
                seguimiento = SeguimientoEspecie(rubroespecie=especie,
                                                 observacion=request.POST['observacion'],
                                                 usuario = especie.usrasig,
                                                 asistentedepartamento=asis,
                                                 fecha = datetime.now(),
                                                    hora=datetime.now().time())
                seguimiento.save()
                return HttpResponse(json.dumps({"result":"ok"}), content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({"result":str(e)}), content_type="application/json")

        elif 'dataregistros' == action:
                try:
                    list = []
                    totales = []
                    departamento = []
                    departamentos = []
                    departamentosid = []
                    totasignadotramite=0
                    totpendientetramite=0
                    totatrasadotramites=0
                    totatrasadosolicitud=0
                    totgestiontramite=0
                    totpendientesolicitud=0
                    totgestionsolicitud=0
                    totatendidosolicitud=0
                    totasignadosolicitud=0
                    totatendidotramite=0
                    data = {}
                    cant=0
                    if request.user.has_perm('sga.change_asistentedepartamento') :
                        general = False
                        if request.POST['general'] =='true':
                            general=True
                        c= 0
                        if AsistenteDepartamento.objects.filter(persona__usuario=request.user,puedereasignar=True).exists():
                            dpto=AsistenteDepartamento.objects.filter(persona__usuario=request.user,puedereasignar=True).values('departamento')
                            asistentes=AsistenteDepartamento.objects.filter(departamento__id__in=dpto).order_by('puedereasignar','persona__apellido1','persona__apellido2')
                            cant = len(asistentes)/2
                            nuevafecha =  str(request.POST['fechafin'][8:10]) + "-" +str(request.POST['fechafin'][5:7])+ "-"+ str(request.POST['fechafin'][0:4])
                            nuevafechaini =  str(request.POST['fecha'][8:10]) + "-" +str(request.POST['fecha'][5:7])+ "-"+ str(request.POST['fecha'][0:4])
                            nuevafechaini = convertir_fecha(nuevafechaini)
                            for a in asistentes:
                                departamento=[]

                                asidptp= AsistenteDepartamento.objects.filter(persona=a.persona).values('departamento')
                                for d in Departamento.objects.filter(id__in=asidptp):
                                    departamento.append(d.descripcion)
                                    if not d.id in departamentosid:
                                        departamentosid.append(d.id)
                                        departamentos.append(({'id':d.id, 'desc':d.descripcion}))

                                # mes =  request.POST['fecha'][5:7]

                                list.append({"horaingre": str(a.horario_ingreso()),"horarioactual": str(a.horario_actual()),"nombre": str(a.persona.usuario),
                                             "asignadotramite": str(a.asignadasfecha(nuevafechaini,nuevafecha,general)),
                                             "pendientetramite": str(a.pendientestfecha(nuevafechaini,nuevafecha,general)),
                                             "atrasadotramites": str(a.gestionadosfecha72(nuevafechaini,nuevafecha,general)),
                                             "atrasadosolicitud": str(a.gestionadossolfecha72(nuevafechaini,nuevafecha,general)),
                                             "gestiontramite": str(a.gestionesfecha(nuevafechaini,nuevafecha,general)) ,
                                             "departamento":sorted(departamento) ,
                                             "pendientesolicitud": str(a.pendientesssolifecha(nuevafechaini,nuevafecha,general)) ,
                                             "gestionsolicitud": str(a.gestionessolfecha(nuevafechaini,nuevafecha,general)) ,
                                             "atendidosolicitud": str(a.finalizadossolfecha(nuevafechaini,nuevafecha,general)) ,
                                             "asignadosolicitud": str(a.asignadassolifecha(nuevafechaini,nuevafecha,general)) ,
                                             "atendidotramite": str(a.finalizadosfecha(nuevafechaini,nuevafecha,general))})

                                totasignadotramite = totasignadotramite + int(list[c]['asignadotramite'])
                                totpendientetramite = totpendientetramite + int(list[c]['pendientetramite'])
                                totatrasadotramites = totatrasadotramites + int(list[c]['atrasadotramites'])
                                totatrasadosolicitud = totatrasadosolicitud + int(list[c]['atrasadosolicitud'])
                                totgestiontramite = totgestiontramite + int(list[c]['gestiontramite'])
                                totpendientesolicitud = totpendientesolicitud+ int(list[c]['pendientesolicitud'])
                                totgestionsolicitud = totgestionsolicitud+ int(list[c]['gestionsolicitud'])
                                totatendidosolicitud = totatendidosolicitud+ int(list[c]['atendidosolicitud'])
                                totasignadosolicitud = totasignadosolicitud + int(list[c]['asignadosolicitud'])
                                totatendidotramite = totatendidotramite + int(list[c]['atendidotramite'])
                                c=c+1
                    totales.append({"totasignadotramite":totasignadotramite , "totpendientetramite" : totpendientetramite , "totatrasadotramites":totatrasadotramites ,
                                    "totatrasadosolicitud":totatrasadosolicitud , "totgestiontramite" : totgestiontramite , "totpendientesolicitud" : totpendientesolicitud ,
                                    "totgestionsolicitud" : totgestionsolicitud ,"totatendidosolicitud" : totatendidosolicitud , "totasignadosolicitud":totasignadosolicitud,
                                    "totatendidotramite":totatendidotramite})
                    data['list'] = list
                    data['totales'] = totales
                    data['cant'] = cant
                    data['departamentos'] = departamentos
                    data['result'] =  'ok'
                    return HttpResponse(json.dumps(data), content_type="application/json")
                    # return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")
                except Exception as e:
                    print("ERROR DATAREG"+str(e))
                    return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")
        elif action=='obsdocente':
            try:
                especie=request.POST['id']
                rubroespecie = RubroEspecieValorada.objects.get(pk=request.POST['id'])
                if not 'op' in request.POST:
                    docente =request.POST['doc']
                    obsdocente=request.POST['obs'].upper()

                    if rubroespecie:
                        rubroespecie.profesor_id = docente
                        rubroespecie.obssecretaria=obsdocente
                        rubroespecie.disponible=False
                        rubroespecie.f_registro=datetime.now().date()
                        rubroespecie.usrregistro=request.user
                        rubroespecie.save()

                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(rubroespecie).pk,
                        object_id       = rubroespecie.id,
                        object_repr     = force_str(rubroespecie),
                        action_flag     = CHANGE,
                        change_message  = 'Obs Secretaria Especie (' + client_address + ')'+ rubroespecie.tipoespecie.nombre +rubroespecie.rubro.inscripcion.persona.nombre_completo_inverso())

                return HttpResponse(json.dumps({"result":"ok","docente":rubroespecie.profesor.persona.nombre_completo_inverso(),"obsdocente":rubroespecie.obssecretaria}), content_type="application/json")
            except Exception as ex:
                return HttpResponse(json.dumps({"result": "bad"}),content_type="application/json")

        elif action=='modificarregistro':
             try:
                matasignada=0
                materia=request.POST['id_materia']
                if MateriaAsignada.objects.filter(pk=materia).exists():
                    matasignada=MateriaAsignada.objects.filter(pk=materia)[:1].get()
                rubroespecie = RubroEspecieValorada.objects.get(pk=request.POST['especie'])

                if rubroespecie:
                    rubroespecie.materia = matasignada
                    rubroespecie.f_registro=datetime.now().date()
                    rubroespecie.usrregistro=request.user
                    rubroespecie.save()

                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(rubroespecie).pk,
                    object_id       = rubroespecie.id,
                    object_repr     = force_str(rubroespecie),
                    action_flag     = CHANGE,
                    change_message  = 'Cambio Registro Materia (' + client_address + ')'+ rubroespecie.tipoespecie.nombre +rubroespecie.rubro.inscripcion.persona.nombre_completo_inverso())

                return HttpResponse(json.dumps({"result":"ok","especie":rubroespecie.materia.materia.asignatura.nombre}), content_type="application/json")
             except Exception as ex:
                return HttpResponse(json.dumps({"result": "bad"}),content_type="application/json")

        elif action == 'generarcondensado':
            inicio = request.POST['fechainicio']
            fin = request.POST['fechafin']
            try:
                fechai = convertir_fecha(inicio)
                fechaf = convertir_fecha(fin)
                fechai2 = convertir_fecha(inicio).date()
                fechaf2 = convertir_fecha(fin).date()

                m = 5
                titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                titulo.font.height = 20*11
                titulo2.font.height = 20*11
                subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                subtitulored = xlwt.easyxf('font: name Times New Roman, colour red, bold on')
                subtituloceleste = xlwt.easyxf('font: name Times New Roman, colour blue, bold on')
                subtitulo.font.height = 20*10
                style1 = xlwt.easyxf('',num_format_str='DD-MMM-YY')
                wb = xlwt.Workbook()
                ws = wb.add_sheet('condensado',cell_overwrite_ok=True)
                tit = TituloInstitucion.objects.all()[:1].get()
                ws.write_merge(0, 0,0,m+10, tit.nombre , titulo2)
                ws.write_merge(1, 1,0,m+10, 'Condensado Gestion de Tramites y Solicitudes ', titulo2)
                ws.write(3, 0, 'DESDE', titulo)
                ws.write(3, 1, inicio, titulo)
                ws.write(4, 0, 'HASTA:', titulo)
                ws.write(4, 1, fin, titulo)
                ws.write(6, 0,  'CENTRO DE ATENCION', subtitulored)
                ws.write(6, 1,  'TOTAL PENDIENTES', subtitulored)
                ws.write(6, 2,  'TRAMITES', titulo)
                ws.write(6, 3,  'SOLICITUDES', titulo)
                ws.write(6, 4,  'TOTAL TRAMITADOS MAS DE 72H', subtitulored)
                ws.write(6, 5,  'TRAMITES', titulo)
                ws.write(6, 6,  'SOLICITUDES', titulo)
                ws.write(6, 7,  'TOTAL ATENDIDOS', subtitulored)
                ws.write(6, 8,  'TRAMITES', titulo)
                ws.write(6, 9, 'SOLICITUDES', titulo)
                ws.write(6, 10, 'TOTAL PROMEDIO ATENCION(HORAS)', subtitulored)
                ws.write(6, 11, 'TRAMITES', titulo)
                ws.write(6, 12, 'SOLICITUDES', titulo)
                ws.write(6, 13, 'TOTAL REASIGNADOS OTRO DPTO', subtitulored)
                ws.write(6, 14, 'TRAMITES', titulo)
                ws.write(6, 15, 'SOLICITUDES', titulo)

                cabecera = 1
                columna = 0
                tot =0
                detalle = 6
                anterior = 0
                actual = 0
                fila = 6
                dpto=0
                totsolicasistente=0
                tottramitesistente=0

                totpendientesgen=0
                totpendientesasistramitegen=0
                totpendientesasisolicgen=0

                totatendidos72hgen=0
                totatendidosasistramite72hgen=0
                totatendidasasissolic72hgen=0

                totatendidosgen=0
                totatendidotramitegen=0
                totatendidosolicgen=0

                totpromediogen=0
                totpromediotramitegen=0
                totpromediosolicgen=0

                totreasignadosgen=0
                totreasigtramitegen=0
                totreasigsolicgen=0
                totpasistrareasignados=0
                totpasissolicreasignados=0
                depart=''

                if request.user.has_perm('sga.add_asistentedepartamento'):
                    depart=Departamento.objects.filter(controlespecies=True).order_by('descripcion')
                else:
                    lider= Persona.objects.filter(usuario=request.user)[:1].get()
                    asistentesdpto=AsistenteDepartamento.objects.filter(puedereasignar=True,persona=lider).values('departamento')
                    depart=Departamento.objects.filter(pk__in=asistentesdpto,controlespecies=True).order_by('descripcion')
                cant_dpto=depart.count()
                for dpto in depart:
                #for dpto in Departamento.objects.filter(pk=25,controlespecies=True).order_by('descripcion').exclude(id=27):
                    #print(dpto)
                    totgestionados=0
                    totsolicgestion=0
                    totalhtramasistente=0
                    totalhsolicasistente=0
                    departamento=elimina_tildes(dpto.descripcion)
                    fila = fila +1
                    filcab=fila

                    totpendientesdpto=0
                    totpendientes72hdpto=0
                    totatendidosdpto=0
                    totreasignadosdpto=0

                    totpendientesasistramite=0
                    totpendientesasisolic=0

                    totatendidosasistramite72h=0
                    totatendidassasissolic72h=0

                    totasistramiteatendidos=0
                    totpasissolicatendidos=0
                    totalhtramasistenteindividual=0
                    totalhsolicasistenteindividual=0

                    tpsolicitudesasist=0
                    tptramitesasist=0
                    tiempopromedioasistente=0

                    tottramitestpxdpto=0
                    totsolictpxdpto=0
                    totsolicgestionados=0
                    totaltiempopromedioxdpto=0

                    totpasistrareasignados=0
                    totpasissolicreasignados=0
                    tiempopromedioxdpto=0
                    tot_tramitesatendidosxdpto=dpto.tramitesgestionadospordpto(fechai,fechaf,fin)
                    tot_solicitudesatendidasxdpto=dpto.solfinalizadospordptofecha(fechai,fechaf,fin)
                    for asistente in AsistenteDepartamento.objects.filter(departamento=dpto).exclude(puedereasignar=True).order_by('persona__apellido1','persona__apellido2','persona__nombres'):
                    #for asistente in AsistenteDepartamento.objects.filter(departamento=dpto,pk=135).exclude(puedereasignar=True).order_by('persona__apellido1','persona__apellido2','persona__nombres'):
                        #print(asistente)
                        totalhtramasistenteindividual=0
                        totalhsolicasistenteindividual=0

                        tpsolicitudesasist=0
                        tptramitesasist=0

                        tiempopromedioasistente=0
                        asist=asistente.persona.nombre_completo_inverso()
                        totpendientesasistramite=totpendientesasistramite+ asistente.pendientestfecha(fechai2,fin,False)
                        totpendientesasisolic= totpendientesasisolic+asistente.pendientesssolifecha(fechai,fin,False)

                        totatendidosasistramite72h=totatendidosasistramite72h+asistente.gestionadosfecha72(fechai,fin,False)
                        totatendidassasissolic72h=totatendidassasissolic72h+asistente.gestionadossolfecha72(fechai,fin,False)

                        totasistramiteatendidos=totasistramiteatendidos+asistente.tramitesfinalizadosfecha(fechai,fechaf,fin)
                        totpasissolicatendidos=totpasissolicatendidos+asistente.solicitudesfinalizadasfecha(fechai,fechaf,fin)

                        totpasistrareasignados=totpasistrareasignados+ asistente.reasignadostramitesfecha(fechai,fechaf)
                        totpasissolicreasignados=totpasissolicreasignados+asistente.reasignadossolicitudesfecha(fechai,fin)

                        tottramitesistente=asistente.tramitesfinalizadosfecha(fechai,fechaf,fin)
                        totsolicasistente=asistente.solicitudesfinalizadasfecha(fechai,fechaf,fin)
                        tiempopromediotramiteasist=0
                        tiempopromediosolicasist=0

                        totalhtramasistente+=asistente.horastramitesatendidosfecha(fechai,fechaf,fin)
                        totalhsolicasistente+=asistente.horassolicitudesatendidasfecha(fechai,fechaf,fin)

                        totalhtramasistenteindividual=asistente.horastramitesatendidosfecha(fechai,fechaf,fin)
                        totalhsolicasistenteindividual=asistente.horassolicitudesatendidasfecha(fechai,fechaf,fin)

                        #if tot_tramitesatendidosxdpto>0:
                            #tiempopromediotramiteasist=Decimal((Decimal((Decimal(tottramitesistente).quantize(Decimal(10)**-2)/Decimal(tot_tramitesatendidosxdpto).quantize(Decimal(10)**-2))*100).quantize(Decimal(10)**-2)*totalhtramasistente)/100).quantize(Decimal(10)**-2)
                        #if tot_solicitudesatendidasxdpto>0:
                        #    tiempopromediosolicasist=Decimal((Decimal((Decimal(totsolicasistente).quantize(Decimal(10)**-2)/Decimal(tot_solicitudesatendidasxdpto).quantize(Decimal(10)**-2))*100).quantize(Decimal(10)**-2)*totalhsolicasistente)/100).quantize(Decimal(10)**-2)
                        if tottramitesistente>0:
                            tiempopromediotramiteasist=Decimal((Decimal(totalhtramasistenteindividual).quantize(Decimal(10)**-2)/Decimal(tottramitesistente).quantize(Decimal(10)**-2))).quantize(Decimal(10)**-2)

                        if totsolicasistente>0:
                            tiempopromediosolicasist=Decimal((Decimal(totalhsolicasistenteindividual).quantize(Decimal(10)**-2)/Decimal(totsolicasistente).quantize(Decimal(10)**-2))).quantize(Decimal(10)**-2)
                        #tottramitestpxdpto+=tiempopromediotramiteasist
                        tottramitestpxdpto+=tiempopromediotramiteasist
                        totsolictpxdpto+=tiempopromediosolicasist
                        #totaltiempopromedioxdpto+=tiempopromediotramiteasist+tiempopromediosolicasist
                        totaltiempopromedioxdpto+=totalhtramasistente+totalhsolicasistente

                        fila = fila +1
                        ws.write(fila,0 ,elimina_tildes(asist),subtitulo)
                        ws.write(fila,1 ,(asistente.pendientestfecha(fechai,fin,False)+asistente.pendientesssolifecha(fechai,fin,False)))
                        ws.write(fila,2 ,asistente.pendientestfecha(fechai,fin,False))
                        ws.write(fila,3 ,asistente.pendientesssolifecha(fechai,fin,False))

                        ws.write(fila,4 ,(asistente.gestionadosfecha72(fechai,fin,False)+asistente.gestionadossolfecha72(fechai,fin,False)))
                        ws.write(fila,5 ,asistente.gestionadosfecha72(fechai,fin,False))
                        ws.write(fila,6 ,asistente.gestionadossolfecha72(fechai,fin,False))

                        ws.write(fila,7 ,(asistente.tramitesfinalizadosfecha(fechai,fechaf,fin)+asistente.solicitudesfinalizadasfecha(fechai,fechaf,fin)))
                        ws.write(fila,8 ,asistente.tramitesfinalizadosfecha(fechai,fechaf,fin))
                        ws.write(fila,9 ,asistente.solicitudesfinalizadasfecha(fechai,fechaf,fin))

                        #tiempopromedioasistente=Decimal((Decimal(tiempopromediotramiteasist+tiempopromediosolicasist).quantize(Decimal(10)**-2)/Decimal(tot_tramitesatendidosxdpto+tot_solicitudesatendidasxdpto).quantize(Decimal(10)**-2))).quantize(Decimal(10)**-2)
                        horasasistente=(totalhtramasistenteindividual+totalhsolicasistenteindividual)
                        atencionesasistente=(tottramitesistente+totsolicasistente)
                        if atencionesasistente>0:
                            tiempopromedioasistente=Decimal((Decimal(horasasistente).quantize(Decimal(10)**-2)/Decimal(atencionesasistente).quantize(Decimal(10)**-2))).quantize(Decimal(10)**-2)
                        ws.write(fila,10 ,(tiempopromedioasistente))
                        ws.write(fila,11 ,tiempopromediotramiteasist)
                        ws.write(fila,12 ,tiempopromediosolicasist)

                        ws.write(fila,13 ,(asistente.reasignadostramitesfecha(fechai,fechaf)+asistente.reasignadossolicitudesfecha(fechai,fin)))
                        ws.write(fila,14 ,asistente.reasignadostramitesfecha(fechai,fechaf))
                        ws.write(fila,15 ,asistente.reasignadossolicitudesfecha(fechai,fin))

                        totpendientesdpto=(totpendientesdpto+totpendientesasistramite+totpendientesasisolic)
                        totpendientes72hdpto=(totpendientes72hdpto+totatendidosasistramite72h+totatendidassasissolic72h)
                        totatendidosdpto=(totatendidosdpto+totasistramiteatendidos+totpasissolicatendidos)
                        totreasignadosdpto=(totreasignadosdpto+totpasistrareasignados+totpasissolicreasignados)

                    ws.write(filcab,0 ,elimina_tildes(departamento),subtituloceleste)
                    ws.write(filcab,1 ,(totpendientesasistramite+totpendientesasisolic),subtitulored)
                    ws.write(filcab,2 ,totpendientesasistramite)
                    ws.write(filcab,3 ,totpendientesasisolic)

                    totpendientesgen+=totpendientesasistramite+totpendientesasisolic
                    totpendientesasistramitegen+=totpendientesasistramite
                    totpendientesasisolicgen+=totpendientesasisolic

                    ws.write(filcab,4 ,(totatendidosasistramite72h+totatendidassasissolic72h),subtitulored)
                    ws.write(filcab,5 ,totatendidosasistramite72h)
                    ws.write(filcab,6 ,totatendidassasissolic72h)

                    totatendidos72hgen+=totatendidosasistramite72h+totatendidassasissolic72h
                    totatendidosasistramite72hgen+=totatendidosasistramite72h
                    totatendidasasissolic72hgen+=totatendidassasissolic72h

                    ws.write(filcab,7 ,(totasistramiteatendidos+totpasissolicatendidos),subtitulored)
                    ws.write(filcab,8 ,totasistramiteatendidos)
                    ws.write(filcab,9 ,totpasissolicatendidos)

                    totatendidosgen+=totasistramiteatendidos+totpasissolicatendidos
                    totatendidotramitegen+=totasistramiteatendidos
                    totatendidosolicgen+=totpasissolicatendidos
                    #tiempopromedioxdpto=Decimal((totalhtramasistente+totalhsolicasistente)/(tottramitestpxdpto+totsolictpxdpto)).quantize(Decimal(10)**-2)
                    totalatencionxdpto=tot_tramitesatendidosxdpto+tot_solicitudesatendidasxdpto
                    if totalatencionxdpto>0:
                        tiempopromedioxdpto=Decimal(totalhtramasistente+totalhsolicasistente).quantize(Decimal(10)**-2)/totalatencionxdpto

                    #ws.write(filcab,10 ,(tottramitestpxdpto+totsolictpxdpto),subtitulored)
                    #ws.write(filcab,11 ,tottramitestpxdpto)
                    #ws.write(filcab,12 ,totsolictpxdpto)
                    if tot_tramitesatendidosxdpto>0:
                        tptramitesasist=Decimal(totalhtramasistente/tot_tramitesatendidosxdpto).quantize(Decimal(10)**-2)
                    if tot_solicitudesatendidasxdpto>0:
                        tpsolicitudesasist=Decimal(totalhsolicasistente/tot_solicitudesatendidasxdpto).quantize(Decimal(10)**-2)

                    ws.write(filcab,10 ,Decimal(tiempopromedioxdpto).quantize(Decimal(10)**-2),subtitulored)
                    ws.write(filcab,11 ,tptramitesasist)
                    ws.write(filcab,12 ,tpsolicitudesasist)

                    #totpromediogen+=tottramitestpxdpto+totsolictpxdpto
                    totpromediogen+=Decimal(tiempopromedioxdpto).quantize(Decimal(10)**-2)
                    totpromediotramitegen+=tptramitesasist
                    totpromediosolicgen+=tpsolicitudesasist

                    ws.write(filcab,13 ,(totpasistrareasignados+totpasissolicreasignados),subtitulored)
                    ws.write(filcab,14 ,totpasistrareasignados)
                    ws.write(filcab,15 ,totpasissolicreasignados)

                    totreasignadosgen+=totpasistrareasignados+totpasissolicreasignados
                    totreasigtramitegen+=totpasistrareasignados
                    totreasigsolicgen+=totpasissolicreasignados

                ws.write(fila+1,0 ,'TOTAL',subtitulo)
                ws.write(fila+1,1 ,totpendientesgen,subtitulo)
                ws.write(fila+1,2 ,totpendientesasistramitegen,subtitulo)
                ws.write(fila+1,3 ,totpendientesasisolicgen,subtitulo)
                ws.write(fila+1,4 ,totatendidos72hgen,subtitulo)
                ws.write(fila+1,5 ,totatendidosasistramite72hgen,subtitulo)
                ws.write(fila+1,6 ,totatendidasasissolic72hgen,subtitulo)
                ws.write(fila+1,7 ,totatendidosgen,subtitulo)
                ws.write(fila+1,8 ,totatendidotramitegen,subtitulo)
                ws.write(fila+1,9 ,totatendidosolicgen,subtitulo)

                ws.write(fila+1,13 ,totreasignadosgen,subtitulo)
                ws.write(fila+1,14 ,totreasigtramitegen,subtitulo)
                ws.write(fila+1,15 ,totreasigsolicgen,subtitulo)

                #fila = fila+3
                #con esta variable para calcular el tiempo promedio por dpto
                total_atencionesITB=totatendidosgen
                #con esta variable para calcular el tiempo promedio por instituto
                total_dpto=cant_dpto
                tiempopromediototal=0

                if request.user.has_perm('sga.add_asistentedepartamento'):
                    depart=Departamento.objects.filter(controlespecies=True).order_by('descripcion')
                    #depart=Departamento.objects.filter(controlespecies=True,pk=25).order_by('descripcion')
                else:
                    lider= Persona.objects.filter(usuario=request.user)[:1].get()
                    asistentesdpto=AsistenteDepartamento.objects.filter(puedereasignar=True,persona=lider).values('departamento')
                    depart=Departamento.objects.filter(pk__in=asistentesdpto,controlespecies=True).order_by('descripcion')

                tot_tramitesatendidosxdpto=0
                tot_solicitudesatendidasxdpto=0
                tot_horastramitesxdpto=0
                tot_horassolicitudesxdpto=0
                totalhorasxdpto=0
                tot_atencionesxdpto=0
                for dpto in depart:
                    tiempopromedioxdpto=0
                    tiempopromediotramitedpto=0
                    #print((dpto.id))
                    departamento=elimina_tildes(dpto.descripcion)
                    #fila = fila +1
                    #filcab=fila

                    tot_tramitesatendidosxdpto+=dpto.tramitesgestionadospordpto(fechai,fechaf,fin)
                    tot_solicitudesatendidasxdpto+=dpto.solfinalizadospordptofecha(fechai,fechaf,fin)

                    tot_horastramitesxdpto+=dpto.tothorastramitesxdpto(fechai,fechaf,fin)
                    tot_horassolicitudesxdpto+=dpto.tothorassolicitudesxdpto(fechai,fechaf,fin)

                    totalhorasxdpto=tot_horastramitesxdpto+tot_horassolicitudesxdpto
                    tot_atencionesxdpto=tot_tramitesatendidosxdpto+tot_solicitudesatendidasxdpto
                    if tot_atencionesxdpto>0:
                        tiempopromedioxdpto=Decimal(totalhorasxdpto).quantize(Decimal(10)**-2)/(tot_atencionesxdpto)

                    if total_atencionesITB>0:
                        tiempopromediotramitedpto=Decimal((Decimal((Decimal(tot_atencionesxdpto).quantize(Decimal(10)**-2)/total_atencionesITB)*100).quantize(Decimal(10)**-2)*tiempopromedioxdpto)/100).quantize(Decimal(10)**-2)

                    #ws.write(fila,0 ,departamento,subtitulo)
                    #ws.write(fila,1 ,tiempopromediotramitedpto)

                    tiempopromediototal+=tiempopromediotramitedpto
                tppromediotramitesitb=0
                tppromediosolicitudesitb=0
                if tot_tramitesatendidosxdpto>0:
                    tppromediotramitesitb=Decimal(tot_horastramitesxdpto/tot_tramitesatendidosxdpto).quantize(Decimal(10)**-2)
                if tot_solicitudesatendidasxdpto>0:
                    tppromediosolicitudesitb=Decimal(tot_horassolicitudesxdpto/tot_solicitudesatendidasxdpto).quantize(Decimal(10)**-2)

                if total_dpto>0:
                    if tot_tramitesatendidosxdpto+tot_solicitudesatendidasxdpto>0:
                        tiempopromediototal=Decimal((tot_horastramitesxdpto+tot_horassolicitudesxdpto)/(tot_tramitesatendidosxdpto+tot_solicitudesatendidasxdpto)).quantize(Decimal(10)**-2)

                #ws.write(fila+1,0 ,'Tiempo Promedio',subtitulo)
                #ws.write(fila+1,1 ,tiempopromediototal,subtitulo)
                #ws.write(fila+1,2 ,tppromediotramitesitb)
                #ws.write(fila+1,3 ,tppromediosolicitudesitb)
                ws.write(fila+1,10 ,tiempopromediototal,subtitulo)
                ws.write(fila+1,11 ,tppromediotramitesitb,subtitulo)
                ws.write(fila+1,12 ,tppromediosolicitudesitb,subtitulo)
                fila=fila +2
                #Para la parte de los docentes
                promedioatenciondocente=0
                docente=''
                coordinacion=''
                cant_coordinacion=0
                totpendientesxcoordgen=0
                totpendientes72hxcoordgen=0
                totatendidosxcoordgen=0
                totapromhxcoordgen=0
                carreracoord=''
                especies=''
                if request.user.has_perm('sga.add_asistentedepartamento'):
                    depart=Departamento.objects.filter(controlespecies=True).order_by('descripcion').exclude(id=27)
                    #especies=RubroEspecieValorada.objects.filter(rubro__fecha__gte=fechai,rubro__fecha__lte=fechaf,tipoespecie__relaciodocente=True).order_by('rubro__inscripcion__carrera__coordinacion').distinct('rubro__inscripcion__carrera__coordinacion').values('rubro__inscripcion__carrera__coordinacion')
                    #especies=RubroEspecieValorada.objects.filter(pk=430348,rubro__fecha__gte=fechai,rubro__fecha__lte=fechaf,tipoespecie__relaciodocente=True).order_by('rubro__inscripcion__carrera__coordinacion').distinct('rubro__inscripcion__carrera__coordinacion').values('rubro__inscripcion__carrera__coordinacion')
                    especies=SolicitudEstudiante.objects.filter(rubro__fecha__gte=fechai,rubro__fecha__lte=fechaf,rubro__rubroespecievalorada__tipoespecie__relaciodocente=True).order_by('rubro__inscripcion__carrera__coordinacion').distinct('rubro__inscripcion__carrera__coordinacion').values('rubro__inscripcion__carrera__coordinacion')

                else:
                    lider= Persona.objects.filter(usuario=request.user)[:1].get()
                    asistentesdpto=AsistenteDepartamento.objects.filter(puedereasignar=True,persona=lider)[:1].get()
                    depart=Departamento.objects.filter(pk=asistentesdpto.departamento.id,controlespecies=True).order_by('descripcion').exclude(id=27)
                    if CoordinadorCarrera.objects.filter(persona=lider,carrera__activo=True).exclude(id=4).order_by('-id').exists():
                        coordcarreras=CoordinadorCarrera.objects.filter(persona=lider,carrera__activo=True).exclude(id=4).order_by('-id')[:1].get()
                        carreracoord=Coordinacion.objects.filter(carrera=coordcarreras.carrera,carrera__activo=True)[:1].get()
                        #especies=RubroEspecieValorada.objects.filter(rubro__fecha__gte=fechai,rubro__fecha__lte=fechaf,tipoespecie__relaciodocente=True,rubro__inscripcion__carrera__coordinacion=carreracoord).order_by('rubro__inscripcion__carrera__coordinacion').distinct('rubro__inscripcion__carrera__coordinacion').values('rubro__inscripcion__carrera__coordinacion')
                        especies=SolicitudEstudiante.objects.filter(rubro__fecha__gte=fechai,rubro__fecha__lte=fechaf,rubro__rubroespecievalorada__tipoespecie__relaciodocente=True,rubro__inscripcion__carrera__coordinacion=carreracoord).distinct('rubro__inscripcion__carrera__coordinacion').values('rubro__inscripcion__carrera__coordinacion')

                for coord in especies:
                    #print(coord)
                    cant_coordinacion=cant_coordinacion+1
                    filacoord=fila+1
                    coordinacion=Coordinacion.objects.filter(pk=coord['rubro__inscripcion__carrera__coordinacion'])[:1].get()
                    totgestionxcoord=coordinacion.tot_gestionesporcoordinacion(fechai,fin)
                    coordinacion=elimina_tildes(coordinacion)
                    pendientescoord=0
                    atendidosprof72Hcoord=0
                    atendidoscoord=0
                    horasatencioncoord=0
                    fila=fila+1
                    fechaaux = convertir_fecha(fin)+timedelta(hours=23,minutes=59)
                    for prof in  GestionTramite.objects.filter(fechaasignacion__gte=fechai,fechaasignacion__lte=fechaaux,tramite__rubro__inscripcion__carrera__coordinacion=coord['rubro__inscripcion__carrera__coordinacion']).distinct('profesor').order_by('profesor').values('profesor'):

                        fila=fila+1
                        promedioatenciondocente=0
                        docente=GestionTramite.objects.filter(profesor=prof['profesor'])[:1].get()
                        doc=elimina_tildes(docente.profesor.nombre_completo_inverso())
                        print(doc)
                        pendientesprof=docente.profesor.pendientesfecha(fechai,fin)
                        pendientescoord+=pendientesprof
                        atendidosprof72H=docente.profesor.gestion72Hfecha(fechai,fin)
                        atendidosprof72Hcoord+=atendidosprof72H
                        atendidosprof=docente.profesor.atendidosfecha(fechai,fin)
                        atendidoscoord+=atendidosprof
                        horasatencion=docente.profesor.hatencionfecha(fechai,fin)

                        if atendidosprof:
                            promedioatenciondocente=Decimal(((Decimal(horasatencion).quantize(Decimal(10)**-2)/Decimal(atendidosprof).quantize(Decimal(10)**-2))).quantize(Decimal(10) ** -2))

                        horasatencioncoord+=horasatencion
                        ws.write(fila,0 ,doc,subtitulo)
                        ws.write(fila,1 ,pendientesprof)
                        ws.write(fila,2 ,pendientesprof)
                        ws.write(fila,3 ,0)
                        ws.write(fila,4 , atendidosprof72H)
                        ws.write(fila,5 , atendidosprof72H)
                        ws.write(fila,6 ,0)
                        ws.write(fila,7 ,atendidosprof)
                        ws.write(fila,8 ,atendidosprof)
                        ws.write(fila,9 ,0)
                        ws.write(fila,10,promedioatenciondocente)
                        ws.write(fila,11,promedioatenciondocente)
                        ws.write(fila,12,0)
                        ws.write(fila,13,0)
                        ws.write(fila,14,0)
                        ws.write(fila,15,0)
                    totpendientesxcoordgen+=pendientescoord
                    totpendientes72hxcoordgen+=atendidosprof72Hcoord
                    totatendidosxcoordgen+=atendidoscoord
                    totapromhxcoordgen+=horasatencioncoord
                    if totgestionxcoord>0:
                        tpcoordinacion=Decimal(horasatencioncoord/totgestionxcoord).quantize(Decimal(10)**-2)
                    else:
                        tpcoordinacion=0
                    ws.write(filacoord,0 ,coordinacion,subtitulored)
                    ws.write(filacoord,1 ,pendientescoord,subtitulored)
                    ws.write(filacoord,2 ,pendientescoord)
                    ws.write(filacoord,3 ,0)
                    ws.write(filacoord,4 ,atendidosprof72Hcoord,subtitulored)
                    ws.write(filacoord,5 ,atendidosprof72Hcoord)
                    ws.write(filacoord,6 ,0)
                    ws.write(filacoord,7 ,atendidoscoord,subtitulored)
                    ws.write(filacoord,8 ,atendidoscoord)
                    ws.write(filacoord,9 ,0)
                    ws.write(filacoord,10,tpcoordinacion,subtitulored)
                    ws.write(filacoord,11,tpcoordinacion)
                    ws.write(filacoord,12,0)
                    ws.write(filacoord,13,0,subtitulored)
                    ws.write(filacoord,14,0)
                    ws.write(filacoord,15,0)

                detalle = detalle + fila
                ws.write(detalle, 0, "Fecha Impresion", subtitulo)
                ws.write(detalle, 2, str(datetime.now()), subtitulo)
                detalle=detalle +1
                ws.write(detalle, 0, "Usuario", subtitulo)
                ws.write(detalle, 2, str(request.user), subtitulo)

                nombre ='condensado'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")
            except Exception as ex:
                print(str(ex) + " ")
                return HttpResponse(json.dumps({"result":str(dpto.id) }),content_type="application/json")

        elif action == 'obtenerMateriasAsignadas':
            try:
                inscripcion = Inscripcion.objects.get(pk=request.POST['inscripcion'])
                tipoEspecie = TipoEspecieValorada.objects.get(pk=request.POST['tipoEspecie'])
                asignadas = MateriaAsignada.objects.filter(matricula__inscripcion=inscripcion).order_by('matricula__nivel__id', 'materia__asignatura__nombre')
                data = [{'id':x.id, 'nivelMalla':x.matricula.nivel.nivelmalla.nombre, 'materia':x.materia.asignatura.nombre} for x in asignadas]
                return HttpResponse(json.dumps({"result":'ok', 'materiasAsignadas':data, 'relacionDocente':tipoEspecie.relaciodocente}),content_type="application/json")
            except Exception as ex:
                print(ex)
                return HttpResponse(json.dumps({"result":'bad', 'msj':'ERROR: '+str(ex)}),content_type="application/json")

        elif action == 'obtenerProfesor':
            try:
                asignada = MateriaAsignada.objects.get(pk=request.POST['materiaAsignada'])
                docentes = ProfesorMateria.objects.filter(materia=asignada.materia).order_by('profesor__persona__apellido1')
                data = [{'id':x.profesor.id, 'docente':x.profesor.persona.nombre_completo_inverso()} for x in docentes]
                return HttpResponse(json.dumps({"result":'ok', 'docentes':data}),content_type="application/json")
            except Exception as ex:
                print(ex)
                return HttpResponse(json.dumps({"result":'bad', 'msj':'ERROR: '+str(ex)}),content_type="application/json")

        elif action == 'habilitaEspecie':
            try:
                rubro_especie = RubroEspecieValorada.objects.get(pk=request.POST['rubro_especie'])
                rubro_especie.disponible = True
                rubro_especie.aplicada = False
                rubro_especie.fechafinaliza = None
                rubro_especie.habilita = True
                rubro_especie.fechahabilita = datetime.now().date()
                rubro_especie.save()

                if EvaluacionAlcance.objects.filter(rubroespecie=rubro_especie).exists():
                    alcance = EvaluacionAlcance.objects.filter(rubroespecie=rubro_especie).order_by('-id')[:1].get()
                    if not alcance.enviado:
                        gestion = GestionTramite(tramite=rubro_especie,
                                                 profesor=rubro_especie.es_online().profesor.persona,
                                                 fechaasignacion=datetime.now())
                        gestion.save()

                return HttpResponse(json.dumps({"result":'ok'}),content_type="application/json")
            except Exception as ex:
                print(ex)
                return HttpResponse(json.dumps({"result":'bad', 'mensaje':str(ex)}),content_type="application/json")

        elif action == 'obtenerNombreUsuario':
            usuario = User.objects.get(pk=request.POST['id'])
            persona = Persona.objects.get(usuario=usuario)
            nombre = persona.nombre_completo_inverso() + ' (' + (persona.cedula if persona.cedula else persona.pasaporte) + ')'
            return HttpResponse(json.dumps({"result": 'ok', 'nombre': nombre}), content_type="application/json")

        elif action == 'verRutaTramite':
            try:
                ruta = []
                cont = 1
                rubro_especie = RubroEspecieValorada.objects.get(pk=request.POST['id'])
                if SeguimientoEspecie.objects.filter(rubroespecie=rubro_especie).exists():
                    seguimientos = SeguimientoEspecie.objects.filter(rubroespecie=rubro_especie).order_by('id')
                    for seguimiento in seguimientos:
                        ruta.append({
                            'num': cont,
                            'usuario': Persona.objects.get(usuario=seguimiento.usuario).nombre_completo_inverso() if seguimiento.usuario else '',
                            'fechaAsigna': seguimiento.fechaasig.strftime("%d-%m-%Y") if seguimiento.fechaasig else '',
                            'observacion': seguimiento.observacion.upper()
                        })
                        cont += 1
                if GestionTramite.objects.filter(tramite=rubro_especie).exists():
                    gestionesDocente = GestionTramite.objects.filter(tramite=rubro_especie).order_by('id')
                    for gestion in gestionesDocente:
                        ruta.append({
                            'num': cont,
                            'usuario': gestion.profesor.nombre_completo_inverso() if gestion.profesor else '',
                            'fechaAsigna': gestion.fechaasignacion.strftime("%d-%m-%Y") if gestion.fechaasignacion else '',
                            'observacion': gestion.respuesta.upper() if gestion.respuesta else ''
                        })
                        cont += 1

                usuario = 'NO ASIGNADO'
                try:
                    usuario = Persona.objects.get(usuario=rubro_especie.usrasig).nombre_completo_inverso()
                except:
                    pass
                ruta.append({
                    'num': cont,
                    'usuario': usuario,
                    'fechaAsigna': rubro_especie.fechafinaliza.strftime("%d-%m-%Y") if rubro_especie.fechafinaliza else '',
                    'observacion': rubro_especie.observaciones.upper() if rubro_especie.observaciones else ''
                })

                return HttpResponse(json.dumps({"result":'ok', 'ruta':ruta}), content_type="application/json")
            except Exception as ex:
                print(ex)
                return HttpResponse(json.dumps({"result":'bad', 'mensaje':str(ex)}), content_type="application/json")

        return HttpResponseRedirect("/controlespecies")

    else:
        data = {'title': 'Bandejas de Atencion'}
        addUserData(request,data)
        hoy = datetime.today().date()
        data['fechahoy'] = hoy
        if 'action' in request.GET:
            action = request.GET['action']
            if action == 'registro':
                data['title']= 'Control de Especies'
                rubroespecie = RubroEspecieValorada.objects.get(pk=request.GET['especie'])
                inscripcion = rubroespecie.rubro.inscripcion
                data['especie']=rubroespecie
                data['especieid']=rubroespecie.id
                data['inscripcion'] = inscripcion
                if 'op' in request.GET:
                    data['op']=request.GET['op']
                else:
                    data['op']='esp'
                if rubroespecie.tipoespecie.id == EXAMEN_CONVALIDACION:
                    data['form'] = ExamenConvalidacionIngresoForm()
                    return render(request ,"controlespecies/examenconvalida.html" ,  data)
                if rubroespecie.tipoespecie.id == ESPECIE_CAMBIO_PROGRAMACION and 'cambio' in request.GET:
                    if request.user.has_perm('sga.change_matricula') :
                        if 'nivel' in request.GET:
                            nivel = Nivel.objects.filter(pk=request.GET['nivel'])[:1].get()
                            form2 = RubroNivelCambioProgramacionForm()
                            form2.rubros_list(nivel)
                            data['form2'] = form2
                            data['pagonivel']= PagoNivel.objects.filter(nivel=nivel)
                            data['TIPOS_PAGO_NIVEL']=TIPOS_PAGO_NIVEL
                            data['form1'] = ControlCambioProgramacionForm(initial={'numeroe':rubroespecie.serie,'codigoe':rubroespecie.serie,'fechae':rubroespecie.rubro.fecha,'nivel':nivel})
                        else:
                            data['form1'] = ControlCambioProgramacionForm(initial={'numeroe':rubroespecie.serie,'codigoe':rubroespecie.serie,'fechae':rubroespecie.rubro.fecha})

                        rubros = Rubro.objects.filter(inscripcion= rubroespecie.rubro.inscripcion,cancelado=False).values('id')
                        form = RubrosCambioProgramacionForm()
                        form.rubros_list(rubros)
                        data['rubros']= Rubro.objects.filter(inscripcion= rubroespecie.rubro.inscripcion,cancelado=False)
                        data['form']= form
                        data['matricula']=inscripcion.matricula()
                        data['grupo']=Grupo.objects.all()

                        return render(request ,"controlespecies/cambio_programacion.html" ,  data)
                    else:
                        return HttpResponseRedirect("/controlespecies?s="+str(rubroespecie.serie)+"&error=ESTE TRAMITE LO REALIZA SECRETARIA... UD. NO TIENE EL PERMISO PARA REALIZARLO")
                if rubroespecie.tipoespecie.id == ESPECIE_RETIRO_MATRICULA and 'retiro' in request.GET:
                    if rubroespecie.rubro.inscripcion.ultima_matricula_pararetiro():
                        if  not rubroespecie.rubro.inscripcion.retirado():
                            data['title'] = 'Retiro Matricula'
                            matricula = rubroespecie.rubro.inscripcion.ultima_matricula_pararetiro()
                            if 'error' in request.GET:
                                data['error'] = request.GET['error']
                            data['matricula'] = matricula
                            data['form'] = RetiradoMatriculaForm(initial={'fecha': datetime.now().strftime("%d-%m-%Y"),'especie':rubroespecie.serie })
                            rubros = Rubro.objects.filter(inscripcion= matricula.inscripcion,cancelado=False).values('id')
                            form2 = RubrosCambioProgramacionForm()
                            form2.rubros_list(rubros)
                            data['form2']=form2
                            data['rubros']= Rubro.objects.filter(inscripcion= matricula.inscripcion,cancelado=False)
                        # else:
                        #     return HttpResponseRedirect("/controlespecies?s="+str(rubroespecie.serie)+"&error=YA SE ENCUENTRA RETIRADO")
                            return render(request ,"matriculas/retiro_matricula.html" ,  data)
                    # else:
                    #     return HttpResponseRedirect("/controlespecies?s="+str(rubroespecie.serie)+"&error=NO ESTA MATRICULADO")

                materiaasignada = MateriaAsignada.objects.filter(matricula=inscripcion.matricula()).values('id')

                form = ControlEspeciesForm(initial={'numeroe':rubroespecie.serie,'fechae':rubroespecie.rubro.fecha,'codigoe':rubroespecie.serie})
                data['form']= form

                data['mat']=MateriaAsignada.objects.filter(id__in=materiaasignada).order_by('materia__asignatura__nombre')

                data['asentamiento']=ESPECIE_ASENTAMIENTO_NOTA
                data['examen']=ESPECIE_EXAMEN
                data['recuperacion'] = ESPECIE_RECUPERACION
                data['mejoramiento'] = ESPECIE_MEJORAMIENTO
                if 'error' in request.GET:
                    data['error']=request.GET['error']

                return render(request ,"controlespecies/registrar.html" ,  data)

            elif action == 'impespecies':
                rubroespecie = RubroEspecieValorada.objects.filter(pk=request.GET['id'])
                data['especie']=rubroespecie
                return render(request ,"controlespecies/especies.html" ,  data)

            elif action == 'vergestion':
                especie = RubroEspecieValorada.objects.filter(pk=request.GET['ide'])[:1].get()
                seguimiento= SeguimientoEspecie.objects.filter(rubroespecie=especie).order_by('-fecha','-hora')

                data['especie']=especie
                data['seguimiento']=seguimiento
                return render(request ,"controlespecies/detalle_gestion.html" ,  data)

            elif action == 'vergestiontramite':
                try:
                    solicitud = SolicitudEstudiante.objects.filter(id=request.GET['ide'])[:].get()
                    segprofe=None
                    if RubroEspecieValorada.objects.filter(rubro=solicitud.rubro).exists():
                        tramite = RubroEspecieValorada.objects.filter(rubro=solicitud.rubro)[:1].get()
                        seguimiento= SeguimientoEspecie.objects.filter(rubroespecie=tramite).order_by('-fecha','-hora')
                        segprofe= GestionTramite.objects.filter(tramite=tramite).exclude(fecharespuesta=None)
                        data['especie']=tramite
                        data['seguimiento']=seguimiento
                        data['segprofe']=segprofe
                        return render(request ,"controlespecies/detalle_gestion.html" ,  data)
                    else:
                        if SolicitudSecretariaDocente.objects.filter(solicitudestudiante=solicitud).exists():
                            solicitud = SolicitudSecretariaDocente.objects.filter(solicitudestudiante=solicitud)[:1].get()
                            seguimiento= IncidenciaAsignada.objects.filter(solicitusecret=solicitud).order_by('-fecha')
                            data['solicitud']=solicitud
                            data['seguimiento']=seguimiento
                            return render(request ,"solicitudes/detalle_gestion.html" ,  data)
                except Exception as e:
                    print(e)
            #
            # elif action =='actualiza2':
            #     c=0
            #     for r in IncidenciaAsignada.objects.filter(fecha__gte='2020-09-01').exclude(asistenteasig=None):
            #         try:
            #             if AsistenteDepartamento.objects.filter(persona__usuario=r.asistenteasig).exists():
            #                 if AsistenteDepartamento.objects.filter(persona__usuario=r.asistenteasig).count() >1 :
            #                     print(r.solicitusecret)
            #                 else:
            #                     asistentes = AsistenteDepartamento.objects.filter(persona__usuario=r.asistenteasig).order_by('id')[:1].get()
            #                     r.asistentedepartamento=asistentes
            #                     r.save()
            #                     c= c+1
            #         except Exception as e:
            #             print(e)
            #             pass
            #
            #         # r.departamento = r.dptoactual()
            #     print(c)
            # elif action =='actualiza':
            #     c=0
            #     for r in SolicitudSecretariaDocente.objects.filter().exclude(solicitudestudiante=None):
            #         print(SolicitudSecretariaDocente.objects.filter().exclude(solicitudestudiante=None)).count()
            #         try:
            #             dpto_id=EspecieGrupo.objects.filter(tipoe=r.solicitudestudiante.tipoe).values('departamento')
            #             if AsistenteDepartamento.objects.filter(persona__usuario=r.personaasignada.usuario,departamento__id__in=dpto_id).exclude(puedereasignar=True).exists():
            #                 asistentes = AsistenteDepartamento.objects.filter(persona__usuario=r.personaasignada.usuario,departamento__id__in=dpto_id).exclude(puedereasignar=True)[:1].get()
            #                 print(asistentes)
            #             else:
            #
            #                 asistentes = r.dptoactual()
            #             print(r.dptoactual())
            #             if asistentes:
            #                 r.departamento = asistentes.departamento
            #                 r.save()
            #                 c=c +1
            #         except Exception as e:
            #             print(e)
            #             pass
            #
            #         # r.departamento = r.dptoactual()
            #     print(c)



            elif action == 'modificarregistro':
                rubroespecie = RubroEspecieValorada.objects.get(pk=request.GET['especie'])
                inscripcion = rubroespecie.rubro.inscripcion
                data['materias'] = MateriaAsignada.objects.filter(matricula=inscripcion.matricula()).order_by('materia__asignatura__nombre')
                data['inscripcion']=inscripcion
                data['especie']=rubroespecie
                return render(request ,"controlespecies/modificaregistro.html" ,  data)

        else:
            try:
                search = None
                todos = None
                numero = None
                especie = None
                op=None

                totreasigsolicgen=0
                inicio = '17-08-2020'
                fin = datetime.now().date().strftime("%d-%m-%Y")
                mensualini = '01' + '-' + str(datetime.now().month).zfill(2)+ '-'+ str(datetime.now().year)
                promedio=[]
                fechai = convertir_fecha(inicio)
                fechaf = convertir_fecha(fin)
                fechaimes = convertir_fecha(mensualini)
                if AsistenteDepartamento.objects.filter(persona__usuario=request.user,activo=True).exists():
                    for dpto in Departamento.objects.filter(id__in=AsistenteDepartamento.objects.filter(persona__usuario=request.user).values('departamento')):
                        totgestionados=0
                        totsolicgestion=0
                        totalhtramasistente=0
                        totalhsolicasistente=0

                        totalhtramasistentemes=0
                        totalhsolicasistentemes=0
                        departamento=elimina_tildes(dpto.descripcion)
                        for asistente in AsistenteDepartamento.objects.filter(departamento=dpto,persona__usuario=request.user,activo=True).exclude(puedereasignar=True).order_by('persona__apellido1','persona__apellido2','persona__nombres'):
                            ttpsolicitudesasist=0
                            tptramitesasist=0

                            tiempopromedioasistente=0
                            asist=asistente.persona.nombre_completo_inverso()

                            tottramitesistente=asistente.tramitesfinalizadosfecha(fechai,fechaf,fin)
                            totsolicasistente=asistente.solicitudesfinalizadasfecha(fechai,fechaf,fin)
                            tiempopromediotramiteasist=0
                            tiempopromediosolicasist=0

                            tottramitesistentemes=asistente.tramitesfinalizadosfecha(fechaimes,fechaf,fin)
                            totsolicasistentemes=asistente.solicitudesfinalizadasfecha(fechaimes,fechaf,fin)
                            tiempopromediotramiteasistmes=0
                            tiempopromediosolicasistmes=0

                            totalhtramasistente+=asistente.horastramitesatendidosfecha(fechai,fechaf,fin)
                            totalhsolicasistente+=asistente.horassolicitudesatendidasfecha(fechai,fechaf,fin)

                            totalhtramasistentemes+=asistente.horastramitesatendidosfecha(fechaimes,fechaf,fin)
                            totalhsolicasistentemes+=asistente.horassolicitudesatendidasfecha(fechaimes,fechaf,fin)

                            totalhtramasistenteindividualmes=asistente.horastramitesatendidosfecha(fechaimes,fechaf,fin)
                            totalhsolicasistenteindividualmes=asistente.horassolicitudesatendidasfecha(fechaimes,fechaf,fin)

                            totalhtramasistenteindividual=asistente.horastramitesatendidosfecha(fechai,fechaf,fin)
                            totalhsolicasistenteindividual=asistente.horassolicitudesatendidasfecha(fechai,fechaf,fin)

                            if tottramitesistente>0:
                                tiempopromediotramiteasist=Decimal((Decimal(totalhtramasistenteindividual).quantize(Decimal(10)**-2)/Decimal(tottramitesistente).quantize(Decimal(10)**-2))).quantize(Decimal(10)**-2)

                            if totsolicasistente>0:
                                tiempopromediosolicasist=Decimal((Decimal(totalhsolicasistenteindividual).quantize(Decimal(10)**-2)/Decimal(totsolicasistente).quantize(Decimal(10)**-2))).quantize(Decimal(10)**-2)

                            if tottramitesistentemes>0:
                                tiempopromediotramiteasistmes=Decimal((Decimal(totalhtramasistenteindividualmes).quantize(Decimal(10)**-2)/Decimal(tottramitesistentemes).quantize(Decimal(10)**-2))).quantize(Decimal(10)**-2)

                            if totsolicasistentemes>0:
                                tiempopromediosolicasistmes=Decimal((Decimal(totalhsolicasistenteindividualmes).quantize(Decimal(10)**-2)/Decimal(totsolicasistentemes).quantize(Decimal(10)**-2))).quantize(Decimal(10)**-2)
                            promedio.append({'dpto':dpto.descripcion,'promediot':tiempopromediotramiteasist,'promedios':tiempopromediosolicasist,'promediotmes':tiempopromediotramiteasistmes,'promediosmes':tiempopromediosolicasistmes})


                    data['promedio']=promedio
                if 's' in request.GET:
                    search = request.GET['s']
                if 't' in request.GET:
                    todos = request.GET['t']
                c =0
                fecha =datetime.now().date() - timedelta(30)

                if search:
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')
                    if len(ss)==1:
                        try:
                            if int(search):
                                numero = int(search)
                                especie = RubroEspecieValorada.objects.filter(Q(serie=numero)|Q(rubro__inscripcion__persona__cedula=search)|Q(rubro__inscripcion__persona__pasaporte=search)).order_by('-rubro__fecha','serie')
                        except:
                            especie = RubroEspecieValorada.objects.filter(Q(rubro__inscripcion__persona__apellido1__icontains=search)).order_by('-rubro__fecha','serie')
                    else:
                        especie = RubroEspecieValorada.objects.filter(Q(rubro__inscripcion__persona__apellido1__icontains=ss[0]) & Q(rubro__inscripcion__persona__apellido2__icontains=ss[1])).order_by('rubro__fecha','rubro__inscripcion__persona__apellido1','rubro__inscripcion__persona__apellido2','rubro__inscripcion__persona__nombres')

                else:
                    especie = RubroEspecieValorada.objects.filter(aplicada=False,rubro__cancelado=True,disponible=True).order_by('-rubro__fecha','rubro__inscripcion__persona__apellido1')

                if 'op' in request.GET:
                    if request.GET['op'] == 'buscar':
                        asistentefilter =AsistenteDepartamento.objects.get(pk=request.GET['asist'],activo=True)
                        data['asistentefilter'] = asistentefilter
                        data['asignados'] = asistentefilter.cantidad
                        data['gestionados'] = asistentefilter.gestionados()
                        data['solicitudgestionadas'] = asistentefilter.solicitudes_gestionados()
                        for asistentedpto   in AsistenteDepartamento.objects.filter(id=request.GET['asist'],activo=True):
                            cantidad = RubroEspecieValorada.objects.filter(aplicada=False,usrasig=asistentedpto.persona.usuario,rubro__cancelado=True,disponible=True).count()
                            cantidadsol =SolicitudSecretariaDocente.objects.filter(personaasignada=asistentedpto.persona,cerrada=False).exclude(solicitudestudiante=None).count()
                            asistentedpto.cantidad=cantidad
                            asistentedpto.cantidadsol=cantidadsol
                            asistentedpto.save()
                        if HorarioAsistenteSolicitudes.objects.filter(fecha=datetime.now().date(),usuario=asistentefilter.persona.usuario).exists():
                            horarioasistente = HorarioAsistenteSolicitudes.objects.filter(fecha=datetime.now().date(),usuario=asistentefilter.persona.usuario)[:1].get()
                            data['horarioasistente'] = horarioasistente
                        especie = especie.filter(usrasig=asistentefilter.persona.usuario).order_by('rubro__fecha','serie')

                # if RubroEspecieValorada.objects.filter(usrasig=request.user).exists():
                #     especie = especie.filter(usrasig=request.user).order_by('rubro__fecha','serie')
                data['puedecambiarturno'] = False
                if AsistenteDepartamento.objects.filter(persona__usuario=request.user,activo=True).exists() and not request.user.has_perm('sga.change_asistentedepartamento') :
                    especie = especie.filter(usrasig=request.user).order_by('-rubro__fecha','serie')
                else:
                    if AsistenteDepartamento.objects.filter(persona__usuario=request.user,puedereasignar=True,activo=True).exists() and not request.user.has_perm('sga.add_departamento'):
                        dpto=AsistenteDepartamento.objects.filter(persona__usuario=request.user,puedereasignar=True,activo=True).distinct('departamento').values('departamento')
                        usr2=AsistenteDepartamento.objects.filter(persona__usuario=request.user,puedereasignar=False,activo=True).distinct('persona__usuario').values('persona__usuario')
                        usuario = AsistenteDepartamento.objects.filter(departamento__id__in=dpto,activo=True).values('persona__usuario')
                        especie = especie.filter(Q(usrasig__id__in=usuario)|Q(usrasig__id__in=usr2)).order_by('-rubro__fecha','serie')
                    # else:
                        data['puedecambiarturno'] = True
                        data['asistentes'] = AsistenteDepartamento.objects.filter(departamento__id__in=dpto,activo=True).order_by('persona__apellido1','persona__apellido2','persona__nombres',)
                    else:
                        data['asistentes'] = AsistenteDepartamento.objects.filter(activo=True).order_by('persona__apellido1','persona__apellido2','persona__nombres',)

                if AsistenteDepartamento.objects.filter(persona__usuario=request.user,departamento__id=27,activo=True).exclude(puedereasignar=True).exists():
                    data['puedecambiarturno']=False

                if AsistenteDepartamento.objects.filter(persona__usuario=request.user,activo=True).exclude(puedereasignar=True).exists():
                    for asistentedpto   in AsistenteDepartamento.objects.filter(persona__usuario=request.user,activo=True).exclude(puedereasignar=True):
                        cantidad = RubroEspecieValorada.objects.filter(aplicada=False,usrasig=request.user,rubro__cancelado=True,disponible=True).count()
                        cantidadsol =SolicitudSecretariaDocente.objects.filter(personaasignada__usuario=request.user,cerrada=False).exclude(solicitudestudiante=None).count()
                        asistentedpto.cantidad=cantidad
                        asistentedpto.cantidadsol=cantidadsol
                        asistentedpto.save()

                paging = MiPaginador(especie, 30)
                p = 1
                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                    page = paging.page(p)
                except:
                    page = paging.page(p)

                if 'error' in request.GET:
                    data['error'] = request.GET['error']

                data['paging'] = paging
                data['rangospaging'] = paging.rangos_paginado(p)
                data['page'] = page
                data['search'] = search if search else ""
                data['todos'] = todos if todos else ""
                data['especie'] = page.object_list
                data['form']= ControlEspeciesSecretariaForm()
                data['DIAS_ESPECIE']=DIAS_ESPECIE
                data['ESPECIE_CAMBIO_PROGRAMACION']=ESPECIE_CAMBIO_PROGRAMACION
                data['ESPECIE_REINGRESO']=ESPECIE_REINGRESO
                data['ESPECIES_ASENTAMIENTO_NOTAS'] = ESPECIES_ASENTAMIENTO_NOTAS
                data['ESPECIE_RETIRO_MATRICULA']=ESPECIE_RETIRO_MATRICULA
                data['respform'] = RespuestaEspecieForm()
                data['segform'] = SeguimientoEspecieForm()
                data['controlesp']=RubroEspecieValoradaForm()
                data['usuario'] = request.user
                data['persona'] = Persona.objects.filter(usuario=request.user)[:1].get()
                data['departamentos'] = Departamento.objects.filter(controlespecies=True).order_by('descripcion')

                if 'op' in request.GET:
                    op =request.GET['op']
                data['op'] = op if op else ""

                data['fechahoy'] = datetime.now()
                data['formfechas'] = RangoGestionForm(initial={'inicio': datetime.now().date(),'fin': datetime.now().date()})
                if HorarioAsistenteSolicitudes.objects.filter(fecha=datetime.now().date(),usuario=request.user).exists():
                    horarioasistente = HorarioAsistenteSolicitudes.objects.filter(fecha=datetime.now().date(),usuario=request.user)[:1].get()
                    data['horarioasistente'] = horarioasistente

                data['tipos_especies'] = TipoEspecieValorada.objects.filter(activa=True).order_by('nombre')

                return render(request ,"controlespecies/especies.html" ,  data)
            except Exception as ex:
                print(ex)