from datetime import datetime, timedelta,date
import json
import os
import locale
from urllib.error import URLError, HTTPError

from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Avg
from django.db.models.aggregates import Sum, Max
from django.db import transaction
from django.db.models.query_utils import Q
from django.forms.models import model_to_dict
# from django.forms import model_to_dict
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.utils.encoding import force_str
from django.template import RequestContext
from decorators import secure_module
from settings import CENTRO_EXTERNO, RUBRO_TIPO_OTRO_MODULO_INTERNO, RUBRO_TIPO_OTRO_INSCRIPCION, DEFAULT_PASSWORD, \
    PROFESORES_GROUP_ID, ALUMNOS_GROUP_ID, UTILIZA_GRUPOS_ALUMNOS, REPORTE_CERTIFICADO_INSCRIPCION, EMAIL_ACTIVE, \
    EVALUACION_ITB, \
    REGISTRO_HISTORIA_NOTAS, NOTA_ESTADO_EN_CURSO, GENERAR_RUBROS_PAGO, GENERAR_RUBRO_INSCRIPCION, \
    GENERAR_RUBRO_INSCRIPCION_MARGEN_DIAS, \
    MODELO_EVALUACION, EVALUACION_IAVQ, EVALUACION_ITS, UTILIZA_NIVEL0_PROPEDEUTICO, TIPO_PERIODO_PROPEDEUTICO, \
    NOTA_ESTADO_APROBADO, \
    UTILIZA_FICHA_MEDICA, EVALUACION_TES, CORREO_INSTITUCIONAL, USA_CORREO_INSTITUCIONAL, INSCRIPCION_CONDUCCION, \
    PORCIENTO_NOTA1, \
    PORCIENTO_NOTA2, PORCIENTO_NOTA3, PORCIENTO_NOTA4, PORCIENTO_NOTA5, PORCIENTO_RECUPERACION, \
    ASIGNATURA_PRACTICA_CONDUCCION, NOTA_PARA_APROBAR, \
    ASIST_PARA_APROBAR, VALIDA_PRECEDENCIA, ASIGNATURA_EDU_VIAL, ASIGNATURA_LEY_TRANSPORTE, ASIGNATURA_PRACTICAS_CONDU, \
    CARRERAS_ID_EXCLUIDAS_INEC, \
    DESCUENTO_REFERIDO, NOTA_PARA_EXAMEN_CONDUCCION, ASIG_PRATICA, HORAS_PRACTICA, TIPO_OTRO_RUBRO, \
    ANIO_PARA_INSCRIPCION, NOTA_MAXIMA, ADMISION_GROUP_ID, \
    HORAS_VINCULACION, ASIG_VINCULACION, ID_CARRERA_RECUPERACION, ID_TIPO_SOLICITUD, SISTEMAS_GROUP_ID, EJE_PRACTICA, \
    NEW_PASSWORD, \
    ACTIVA_ADD_EDIT_AD, NOTA_ESTADO_REPROBADO, HABILITA_DESC_INSCRIPCION, DESCUENTO_INSCRIPCION, \
    ESPECIE_JUSTIFICA_FALTA, ESPECIE_JUSTIFICA_FALTA_AU, \
    EXAMEN_CONVALIDACION, DIAS_ESPECIE, ID_SOLIC__ONLINE, TIPO_RUBRO_SOLICITUD, ESPECIE_CAMBIO_PROGRAMACION, \
    ID_TIPO_ESPECIE_REG_NOTA, ESPECIE_EXAMEN, \
    ESPECIE_RECUPERACION, ESPECIE_MEJORAMIENTO, NOTA_ESTADO_DERECHOEXAMEN, NOTA_ESTADO_SUPLETORIO, RUBRO_PLAGIO, \
    IP_SERVIDOR_API_DIRECTORY, ESPECIE_ASENTAMIENTOCONVENIO_SINVALOR, ESPECIE_ASENTAMIENTOCONVENIO_CONVALOR, \
    NIVEL_MALLA_CERO, ASIGNATURA_EXAMEN_GRADO_CONDU, ESPECIES_ASUNTOS_ESTUDIANTILES, TIPO_RUBRO_MATERIALAPOYO, \
    NIVEL_MALLA_UNO, TIPO_OTRO_FRAUDE, HORAS_TELECLINICA

from sga.tasks import gen_passwd, send_html_mail
from sga.alu_malla import aprobadaAsignatura, horaspracticas,horasteleclinica
from sga.commonviews import addUserData, ip_client_address, cambio_clave_AD, add_usuario_AD
from sga.docentes import calculate_username
import requests
import threading
from sga import forms
from sga.forms import PersonaForm, InscripcionForm, RecordAcademicoForm, HistoricoRecordAcademicoForm, \
    HistoriaNivelesDeInscripcionForm, CargarFotoForm, \
    EmpresaInscripcionForm, EstudioInscripcionForm, DocumentoInscripcionForm, ActividadesInscripcionForm, \
    PadreClaveForm, ConvalidacionInscripcionForm, \
    HistoricoNotasITBForm, GraduadoDatosForm, EgresadoForm, InscripcionSenescytForm, RetiradoMatriculaForm, \
    InscripcionCextForm, BecarioForm, InscripcionPracticaForm, \
    ObservacionInscripcionForm, ProcesoDobeForm, ActivaInactivaUsuarioForm, HistoricoNotasPracticaForm, SuspensionForm, \
    ProcesoDobleMatriculaForm, KitCongresoForm, VendedorInscForm, \
    AdicionarPanelForm, PrecongresoForm, ColegioForm, CertificadoForm, InscripcionGraduadosForm, RangoNCForm, \
    RecibirTituloForm, VerEntregarTitForm, AprobacionVinculacionForm, SolicitudSecretariaAlumnosForm, KitUniformeMunicipioForm, EspecieUniversalForm,\
    EntregaJugueteForm, AprobarDocumentoForm,InscripcionPracticaDistribucionForm,PracticaDistribucionHorasForm,PromocionInscForm,PlagioForm

from sga.models import Profesor, ProcesoDobe, Persona, Inscripcion, RecordAcademico, DocumentosDeInscripcion, \
    HistoricoRecordAcademico, HistoriaNivelesDeInscripcion, \
    FotoPersona, EmpresaInscripcion, EstudioInscripcion, DocumentoInscripcion, Archivo, TipoArchivo, Grupo, \
    InscripcionGrupo, PerfilInscripcion, HistoricoNotasITB, \
    PadreClave, Malla, ConvalidacionInscripcion, TipoEstado, Rubro, RubroInscripcion, NivelMalla, EjeFormativo, \
    AsignaturaMalla, Egresado, Asignatura, InscripcionSenescyt, \
    RetiradoMatricula, Carrera, Modalidad, Sesion, Especialidad, Materia, Nivel, TipoOtroRubro, Matricula, \
    MateriaAsignada, RubroOtro, Graduado, InscripcionBecario, \
    InscripcionPracticas, ObservacionInscripcion, InscripcionConduccion, InactivaActivaUsr, PreInscripcion, \
    EstudianteXEgresar, Sexo, HistoricoNotasPractica, GraduadoConduccion, \
    Periodo, EquivalenciaCondu, AtencionCliente, TurnoDet, TurnoCab, InscripcionSuspension, EliminaSuspension, \
    ProcesoDobleMatricula, KitCongreso, PermisoPanel, Panel, TipoAnuncio, inscritos_anuncio, \
    GrupoSeminario, InscripcionSeminario, ReferidosInscripcion, InscripcionExamen, Detvalidaexamen, \
    InscripcionAspirantes, FotoInstEstudiante, RubrosConduccion, TituloExamenCondu, PreguntaExamen, \
    DetalleExamen, Colegio, InscripcionExtranjerosTitulo, AsistenciaCofia, PromedioNotasGrado, RecordAcademico, \
    ConvenioUsuario, CertificadoEntregado, EstudianteVinculacion, \
    Tutoria, EstudianteTutoria, InscripcionVendedor, Vendedor, RubroMatricula, Canton, Parroquia, Sector, \
    DatosPersonaCongresoIns, AprobacionVinculacion, InscripcionTipoTest, PreguntaTest, TipoTest, ResultadoRespuesta, \
    TipoSolicitudSecretariaDocente, SolicitudSecretariaDocente, SolicitudesGrupo, ModuloGrupo, TipoIncidencia, \
    EntregaUniformeMunicipo, EvaluacionAlcance, TipoEspecieValorada, HorarioAsistenteSolicitudes, \
    AsistenteDepartamento, CoordinacionDepartamento, SesionCaja, Coordinacion, EspecieGrupo, SolicitudOnline, \
    SolicitudEstudiante, TipoEntrega, EntregaJugueteCanasta, ExamenConvalidacionIngreso, Descuento, DetalleDescuento, \
    RegistroPlagioTarjetas, RubroEspecieValorada, LeccionGrupo, AsistenciaLeccion, DescuentosporConvenio, \
    EmpresaConvenio, ViewCertificacionesIngles, Promocion, Departamento, PuntoAtencion, EntregaUniforme, TallaUniforme, \
    EntregaUniformeAdmisiones, InscripcionMalla, Factura, NotaCreditoInstitucion

from med.models import PersonaExtension,PersonaExamenFisico,PersonaFichaMedica,PersonaEstadoCivil,PersonaEducacion,PersonaProfesion
from sga.tasks import gen_passwd
from decimal import Decimal
from sga.reportes import elimina_tildes
import traceback
from django.db import connection
def convertir_fecha(s):
    return datetime(int(s[6:10]), int(s[3:5]), int(s[0:2])).date()

def mail_correoalumnoespecie(solicitud,emailestudiante):
        hoy = datetime.now().today()
        email=emailestudiante
        asunto = "Estimado/a estudiante el numero de tramite es " +elimina_tildes(solicitud.rubro.especie_valorada().serie)
        contenido = "ESPECIE " + elimina_tildes(solicitud.tipoe.nombre)
        send_html_mail(str(asunto),"emails/correoalumno_especie_libre.html", {'fecha': hoy,'contenido': contenido, 'asunto': asunto,'solicitud':solicitud},email.split(","))


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

class EspecieSerieGenerador:
    def __init__(self):
        self.__lock = threading.RLock()

    def generar_especie(self, rubro, tipo):
        self.__lock.acquire()
        try:
            serie = 0
            valor = RubroEspecieValorada.objects.filter(rubro__fecha__year=rubro.fecha.year).aggregate(Max('serie'))
            if valor['serie__max']!=None:
                serie = valor['serie__max']+1

            # OCU 09-junio-2017 para evitar que la serie de la especie se duplique
            if not RubroEspecieValorada.objects.filter(rubro__fecha__year=rubro.fecha.year,serie=serie).exists():
                rubroe = RubroEspecieValorada(rubro=rubro, tipoespecie=tipo, serie=serie)
                if tipo.id == ESPECIE_CAMBIO_PROGRAMACION:
                    rubroe.autorizado = False
                rubroe.save()

                return rubroe
            else:
                rubro.delete()
        finally:
            self.__lock.release()


generador_especies = EspecieSerieGenerador()


@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
@transaction.atomic()
def view(request):
    try:
        hoy = datetime.today().date()
        start_time = datetime.now().time()
        # documentosestudiante = list()
        if request.method=='POST':
            action = request.POST['action']
            try:
                if action == 'buscarnivel':
                    try:
                        if Inscripcion.objects.filter(pk=request.POST['idinscripcion']).exists():
                            inscripcion=Inscripcion.objects.filter(pk=request.POST['idinscripcion'])[:1].get()

                            matricula=Matricula.objects.filter(inscripcion=inscripcion).values('nivel__id')

                            data = {'title': ''}

                            listaniveles = []
                            # for a in AsignaturaMalla.objects.filter().order_by("asignatura"):
                            #     lisasignatura.append({"id": a.id, "asignatura": a.asignatura.nombre, "carrera":a.malla.carrera.nombre})
                            for a in Matricula.objects.filter(inscripcion=inscripcion):
                                listaniveles.append({"id": a.id, "nivel": elimina_tildes(a.nivel)})

                            data['listaniveles'] = listaniveles
                            print(listaniveles)
                            # data['listaasignatura'] = lisAsig
                            data['result'] = 'ok'
                            return HttpResponse(json.dumps(data), content_type="application/json")
                    except Exception as e:
                        return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}),
                                        content_type="application/json")

                if action == 'buscarteleclinica':
                    try:
                        if Inscripcion.objects.filter(pk=request.POST['idinscripcion']).exists():
                            inscripcion=Inscripcion.objects.filter(pk=request.POST['idinscripcion'])[:1].get()
                            teleclinica=TituloExamenCondu.objects.filter(activo=True,teleclinica=True,carrera=inscripcion.carrera).order_by('id')
                            data = {'title': ''}
                            listaasignaturas = []
                            for t in teleclinica:
                                listaasignaturas.append({"id": t.asignatura.id, "asignatura": elimina_tildes(t.asignatura.nombre)})
                            data['listaasignaturas'] = listaasignaturas
                            print(listaasignaturas)
                            data['result'] = 'ok'
                            return HttpResponse(json.dumps(data), content_type="application/json")
                    except Exception as e:
                        return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}),content_type="application/json")

                if action=='addrecord':
                    inscripcion = Inscripcion.objects.get(pk=request.POST['id'])
                    b = True
                    f = RecordAcademicoForm(request.POST)

                    if f.is_valid():
                        asignatura = f.cleaned_data['asignatura']
                        if VALIDA_PRECEDENCIA  and not f.cleaned_data['convalidacion']:
                            b = inscripcion.recordacademico_set.filter(asignatura__in=asignatura.precedencia.all().values('id'),nota__gte=NOTA_PARA_APROBAR,asistencia__gte=ASIST_PARA_APROBAR).exists() or not asignatura.precedencia.all()
                        if b:
                            record = RecordAcademico(inscripcion=inscripcion,
                                                asignatura=f.cleaned_data['asignatura'],
                                                nota=f.cleaned_data['nota'],
                                                asistencia=f.cleaned_data['asistencia'],
                                                fecha=f.cleaned_data['fecha'],
                                                aprobada=f.cleaned_data['aprobada'],
                                                convalidacion=f.cleaned_data['convalidacion'],
                                                pendiente=f.cleaned_data['pendiente'])
                            record.save()

                            #Obtain client ip address
                            client_address = ip_client_address(request)

                            # Log de ADICIONAR RECORD
                            LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(record).pk,
                                object_id       = record.id,
                                object_repr     = force_str(record),
                                action_flag     = ADDITION,
                                change_message  = 'Adicionado Registro Academico (' + client_address + ')' )

                            return HttpResponseRedirect("/inscripciones?action=record&id="+str(inscripcion.id))
                        else:
                            return HttpResponseRedirect("/inscripciones?action=addrecord&id="+str(inscripcion.id)+"&error=FALTA APROBAR MATERIAS CON PRECEDENCIA")
                    else:
                            return HttpResponseRedirect("/inscripciones?action=addrecord&id="+str(inscripcion.id))
                if action =="aprobar":
                    documento =DocumentoInscripcion.objects.filter(pk=request.POST['id'])[:1].get()
                    f = AprobarDocumentoForm(request.POST)
                    if f.is_valid():
                        documento.aprobado = f.cleaned_data['aprobado']
                        documento.motivo=f.cleaned_data['motivo']
                        documento.save()
                        if documento.aprobado:
                            msj = 'SU DOCUMENTO ' + str(documento.archivo.tipo) + " HA SIDO VALIDADO"
                        else:
                            msj = 'SU DOCUMENTO ' + str(documento.archivo.tipo) + " NO HA SIDO VALIDADO"
                        documento.correo_alumno(msj)
                        return HttpResponseRedirect("/inscripciones?action=documentos&id="+str(documento.inscripcion.id))
                    else:
                        return HttpResponseRedirect("/inscripciones?action=documentos&error=ERROR EN EL FORMULARIO&id="+str(documento.inscripcion.id))
                if action=='addhistorico':
                    inscripcion = Inscripcion.objects.get(pk=request.POST['id'])
                    f = HistoricoRecordAcademicoForm(request.POST)
                    if f.is_valid():
                        asignatura = f.cleaned_data['asignatura']
                        b = True
                        if inscripcion.carrera.online:
                            asistenciaparaaprobar = 0
                        else:
                            asistenciaparaaprobar = ASIST_PARA_APROBAR
                        if VALIDA_PRECEDENCIA and not f.cleaned_data['convalidacion']:
                            b = inscripcion.recordacademico_set.filter(asignatura__in=asignatura.precedencia.all().values('id'),nota__gte=NOTA_PARA_APROBAR,asistencia__gte=asistenciaparaaprobar).exists() or not asignatura.precedencia.all()
                        if b:
                            historico = HistoricoRecordAcademico(inscripcion=inscripcion,
                                                        asignatura=f.cleaned_data['asignatura'],
                                                        nota=f.cleaned_data['nota'],
                                                        asistencia=f.cleaned_data['asistencia'],
                                                        fecha=f.cleaned_data['fecha'],
                                                        aprobada=f.cleaned_data['aprobada'],
                                                        convalidacion=f.cleaned_data['convalidacion'],
                                                        pendiente=f.cleaned_data['pendiente'])
                            historico.save()

                            if RecordAcademico.objects.filter(inscripcion=historico.inscripcion,asignatura=historico.asignatura).exists():
                                record = RecordAcademico.objects.filter(inscripcion=historico.inscripcion,asignatura=historico.asignatura)[:1].get()
                            else:
                                record = RecordAcademico(inscripcion=historico.inscripcion, asignatura=historico.asignatura,
                                                    nota=historico.nota, asistencia=historico.asistencia,
                                                    fecha=historico.fecha, aprobada=historico.aprobada,
                                                    convalidacion=False, pendiente=False)
                                record.save()

                            #Obtain client ip address
                            client_address = ip_client_address(request)

                            # Log de ADICIONAR HISTORICO
                            LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(historico).pk,
                                object_id       = historico.id,
                                object_repr     = force_str(historico),
                                action_flag     = ADDITION,
                                change_message  = 'Adicionado Historico y Registro (' + client_address + ')' )

                            return HttpResponseRedirect("/inscripciones?action=historico&id="+str(inscripcion.id))
                        else:
                            return HttpResponseRedirect("/inscripciones?action=addhistorico&id="+str(inscripcion.id)+"&error=FALTA APROBAR MATERIAS CON PRECEDENCIA")
                    else:
                        return HttpResponseRedirect("/inscripciones?action=addhistorico&id="+str(inscripcion.id))
                if action == 'addproceso':
                        persona = request.session['persona']
                        inscripcion = Inscripcion.objects.get(pk=request.POST['id'])
                        ap = 'No Aprobado'
                        f = ProcesoDobeForm(request.POST)
                        if f.is_valid():
                            try:
                                if  ProcesoDobe.objects.filter(inscripcion=inscripcion).exists():
                                    proceso=ProcesoDobe.objects.filter(inscripcion=inscripcion)[:1].get()
                                    # if proceso.aprobado:
                                    #     proceso.observacion = f.cleaned_data['observacion']
                                    #    # proceso.aprobado = f.cleaned_data['aprobado']
                                    #     proceso.inscripcion = inscripcion
                                    #     proceso.usuario = request.user
                                    #     proceso.fecha = datetime.now()
                                    #
                                    #     proceso.save()
                                    # else:
                                    proceso.observacion = f.cleaned_data['observacion']
                                    # proceso.aprobado = f.cleaned_data['aprobado']
                                    proceso.usuario = request.user
                                    proceso.fecha = datetime.now()

                                    proceso.save()

                                    # if f.cleaned_data['aprobado']== True:
                                    #     usu = Inscripcion.objects.filter(pk=inscripcion.id)[:1].get().persona.usuario.id
                                    #     usuario = User.objects.filter(pk=usu)[:1].get()
                                    #     usuario.is_active=True
                                    #     usuario.save()

                                    #Obtain client ip address
                                    client_address = ip_client_address(request)

                                    # Log de EDICION PROCESO
                                    LogEntry.objects.log_action(
                                        user_id         = request.user.pk,
                                        content_type_id = ContentType.objects.get_for_model(proceso).pk,
                                        object_id       = proceso.id,
                                        object_repr     = force_str(proceso),
                                        action_flag     = CHANGE,
                                        change_message  = 'Editada Observacion PD (' + client_address + ')' )
                                else:
                                    proceso = ProcesoDobe(inscripcion = inscripcion,
                                                          observacion = f.cleaned_data['observacion'],
                                                          aprobado = f.cleaned_data['aprobado'],
                                                          usuario = request.user,
                                                          fecha = datetime.now())
                                    proceso.save()

                                    if f.cleaned_data['aprobado']== True:
                                        usu = Inscripcion.objects.filter(pk=inscripcion.id)[:1].get().persona.usuario.id
                                        usuario = User.objects.filter(pk=usu)[:1].get()
                                        usuario.is_active=True
                                        usuario.save()
                                        ap = 'Aprobado'
                                    #Obtain client ip address
                                    client_address = ip_client_address(request)

                                    # Log de ADICIONAR PROCESO
                                    LogEntry.objects.log_action(
                                        user_id         = request.user.pk,
                                        content_type_id = ContentType.objects.get_for_model(proceso).pk,
                                        object_id       = proceso.id,
                                        object_repr     = force_str(proceso),
                                        action_flag     = ADDITION,
                                        change_message  = 'Adicionado Proceso DOBE - ' + ap +' (' + client_address + ')' )

                                    if  EMAIL_ACTIVE and proceso.aprobado:
                                        proceso.mail_procesodobe(persona)

                                return HttpResponseRedirect("/inscripciones?s="+str(inscripcion.persona.cedula))
                            except Exception as ex :
                                return HttpResponseRedirect("/inscripciones?s="+str(inscripcion.persona.cedula))
                        else:
                            return HttpResponseRedirect("/inscripciones?action=proceso&id="+str(inscripcion.id)+"&error=1")

                if action == 'addprocesodm':
                        persona = request.session['persona']
                        inscripcion = Inscripcion.objects.get(pk=request.POST['id'])
                        f = ProcesoDobleMatriculaForm(request.POST)
                        if f.is_valid():
                            try:
                                if  ProcesoDobleMatricula.objects.filter(inscripcion=inscripcion).exists():
                                    procesodm=ProcesoDobleMatricula.objects.filter(inscripcion=inscripcion)[:1].get()
                                    procesodm.observacion = f.cleaned_data['observacion']
                                    procesodm.aprobado = f.cleaned_data['aprobado']
                                    procesodm.inscripcion = inscripcion
                                    procesodm.usuario = request.user
                                    procesodm.fecha = datetime.now()

                                    procesodm.save()

                                    if f.cleaned_data['aprobado']== True:
                                        usu = Inscripcion.objects.filter(pk=inscripcion.id)[:1].get().persona.usuario.id
                                        usuario = User.objects.filter(pk=usu)[:1].get()
                                        usuario.is_active=True
                                        usuario.save()

                                    #Obtain client ip address
                                    client_address = ip_client_address(request)

                                    # Log de EDICION PROCESO
                                    LogEntry.objects.log_action(
                                        user_id         = request.user.pk,
                                        content_type_id = ContentType.objects.get_for_model(procesodm).pk,
                                        object_id       = procesodm.id,
                                        object_repr     = force_str(procesodm),
                                        action_flag     = CHANGE,
                                        change_message  = 'Editado Proceso Doble Matricula (' + client_address + ')' )
                                else:
                                    procesodm = ProcesoDobleMatricula(inscripcion = inscripcion,
                                                          observacion = f.cleaned_data['observacion'],
                                                          aprobado = f.cleaned_data['aprobado'],
                                                          usuario = request.user,
                                                          fecha = datetime.now())
                                    procesodm.save()
                                    #Obtain client ip address
                                    client_address = ip_client_address(request)

                                    # Log de ADICIONAR PROCESO
                                    LogEntry.objects.log_action(
                                        user_id         = request.user.pk,
                                        content_type_id = ContentType.objects.get_for_model(procesodm).pk,
                                        object_id       = procesodm.id,
                                        object_repr     = force_str(procesodm),
                                        action_flag     = ADDITION,
                                        change_message  = 'Adicionado Proceso Doble Matricula (' + client_address + ')' )

                                if  EMAIL_ACTIVE and procesodm.aprobado:
                                    procesodm.mail_procesodoblematriculaap(persona,inscripcion.carrera.nombre,request.user)

                                return HttpResponseRedirect("/inscripciones?s="+str(inscripcion.persona.cedula))
                            except Exception as ex :
                                return HttpResponseRedirect("/inscripciones?s="+str(inscripcion.persona.cedula))
                        else:
                            return HttpResponseRedirect("/inscripciones?action=procesodm&id="+str(inscripcion.id)+"&error=1")
                if action == 'consultanivel':
                    print('entro')
                    try:
                        factura=None
                        mat = Matricula.objects.filter(id=request.POST['id'])[:1].get()
                        print(mat)
                        if RubroOtro.objects.filter(matricula=mat.id, tipo__id=TIPO_RUBRO_MATERIALAPOYO, rubro__inscripcion=mat.inscripcion, rubro__cancelado=True).exists():
                            rubroo = RubroOtro.objects.filter(matricula=mat.id, tipo__id=TIPO_RUBRO_MATERIALAPOYO, rubro__inscripcion=mat.inscripcion, rubro__cancelado=True)[:1].get()
                            rubro = rubroo.rubro
                            #OCastillo 26-06-2024 validacion por promocion uniformer 1er nivel
                            if mat.nivel.nivelmalla.id == NIVEL_MALLA_UNO:
                                if mat.inscripcion.promocion:
                                    if mat.inscripcion.promocion.descuentomaterial and mat.inscripcion.promocion.valdescuentomaterial > 0 :
                                        if RubroInscripcion.objects.filter(rubro__inscripcion=mat.inscripcion).exists():
                                            ri=RubroInscripcion.objects.filter(rubro__inscripcion=mat.inscripcion)[:1].get()
                                            if ri.rubro.pago_set.exists():
                                                pago = ri.rubro.pago_set.filter()[:1].get()
                                                if pago.factura_set.exists():
                                                    factura = pago.factura_set.filter()[:1].get()
                                                    return HttpResponse(json.dumps({"result": 'ok', 'fac': factura.numero, 'fech': str(pago.fecha)}),content_type="application/json")
                            else:
                                if rubro.pago_set.exists():
                                    pago = rubro.pago_set.filter()[:1].get()
                                    if pago.factura_set.exists():
                                        factura = pago.factura_set.filter()[:1].get()
                                        return HttpResponse(json.dumps({"result": 'ok', 'fac': factura.numero, 'fech': str(pago.fecha)}), content_type="application/json")
                            return HttpResponse(json.dumps({"result": 'ok', 'fac': factura.numero, 'fech': str(pago.fecha)}), content_type="application/json")
                        else:
                            return HttpResponse(json.dumps({"result": 'bad'}), content_type="application/json")
                    except Exception as e:
                        print(e)
                if action == 'cambiarvendedor':
                    try:
                        inscripcion = Inscripcion.objects.filter(pk=request.POST['id'])[:1].get()
                        usuario = User.objects.filter(pk=request.POST['usu_id'])[:1].get()
                        inscripcion.user = usuario
                        inscripcion.save()
                        client_address = ip_client_address(request)

                        # Log de ADICIONAR PROCESO
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(inscripcion).pk,
                            object_id       = inscripcion.id,
                            object_repr     = force_str(inscripcion),
                            action_flag     = ADDITION,
                            change_message  = 'Usuario de Venta Cambiado (' + client_address + ')' )
                        return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                    except Exception as ex:
                        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

                # OCU 02/06/2014 para desactivar usuarios POST
                if action=='desactivar':
                    inscripcion = Inscripcion.objects.get(pk=request.POST['id'])
                    f = ActivaInactivaUsuarioForm(request.POST)
                    if f.is_valid():
                        inactiva = InactivaActivaUsr(inscripcion=inscripcion, accion='inactivo',
                                                              motivo=f.cleaned_data['motivo'], fecha=datetime.now(),
                                                              usuario= request.user)
                        inactiva.save()

                        inscripcion.persona.usuario.is_active = False
                        inscripcion.persona.usuario.save()
                        inactiva.activa_usuario()


                        # Log de DESACTIVAR USUARIO ESTUDIANTE
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(inscripcion).pk,
                            object_id       = inscripcion.id,
                            object_repr     = force_str(inscripcion),
                            action_flag     = DELETION,
                            change_message  = 'Desactivado Estudiante' )
                        return HttpResponseRedirect("/inscripciones?s="+str(inscripcion.persona.cedula))

                if action == 'validahorasnivel':
                    horas = int(request.POST['numerohoras'])
                    nivel = int(request.POST['idnivel'])
                    inscrip = Inscripcion.objects.get(pk=request.POST['inscriid'])
                    malla = Malla.objects.get(carrera=inscrip.carrera)
                    asig = AsignaturaMalla.objects.get(asignatura__nombre__icontains='PREPRO',malla=malla,nivelmalla__id=nivel)
                    horastotalingresada = horas + InscripcionPracticas.objects.filter(inscripcion=inscrip,nivelmalla__id=nivel).aggregate(Sum('horas'))['horas__sum']
                    if horastotalingresada>asig.horas:
                        return HttpResponse(json.dumps({'result':'bad', 'mensaje':"La cantidad de hora ingresada es mayor a la horas de la practica en este Nivel"+" "+str(asig.horas)}), content_type="application/json")

                    #if  InscripcionPracticas.objects.filter(inscripcion=inscrip,nivelmalla__id=nivel).exists():
                    #   return HttpResponse(json.dumps({'result':'bad', 'mensaje':"Ya tiene ingresar las practicas en ese nivel"}), content_type="application/json")

                    if EstudianteVinculacion.objects.filter(inscripcion=inscrip,nivelmalla__id=nivel).exists():
                        return HttpResponse(json.dumps({'result':'bad', 'mensaje':"Ya tiene ingresar las practicas comunitaria en ese nivel"}), content_type="application/json")

                    return HttpResponse(json.dumps({'result':'ok'}),content_type="application/json")


                if action == 'validahorasniveldistribucion':
                    horas = int(request.POST['numerohoras'])
                    nivel = int(request.POST['idnivel'])
                    inscrip = Inscripcion.objects.get(pk=request.POST['inscriid'])
                    malla = Malla.objects.get(carrera=inscrip.carrera,vigente=True)

                    #OCastillo 13-03-2023 cambio para tecnologias universitarias de Podologia y Gerontologia
                    if not (malla.id ==72 or malla.id ==74):
                        asig = AsignaturaMalla.objects.get(Q(asignatura__nombre__icontains='LABORALES')|Q(asignatura__nombre__icontains='PREPRO'), malla=malla,nivelmalla__id=nivel)
                    else:
                        asig = AsignaturaMalla.objects.get(asignatura__nombre__icontains='TELECLINICA', malla=malla,nivelmalla__id=nivel)

                    if InscripcionPracticas.objects.filter(inscripcion=inscrip,nivelmalla__id=nivel).exists():

                        horastotalingresada = horas + InscripcionPracticas.objects.filter(inscripcion=inscrip,nivelmalla__id=nivel).aggregate(
                            Sum('horas'))['horas__sum']
                    else:
                        horastotalingresada = horas

                    if horastotalingresada > asig.horas:
                        return HttpResponse(json.dumps({'result': 'bad',
                                                        'mensaje': "La cantidad de hora ingresada es mayor a la horas de la practica en este Nivel" + " " + str(
                                                            asig.horas)}), content_type='application/json')

                    # if  InscripcionPracticas.objects.filter(inscripcion=inscrip,nivelmalla__id=nivel).exists():
                    #   return HttpResponse(json.dumps({'result':'bad', 'mensaje':"Ya tiene ingresar las practicas en ese nivel"}), content_type="application/json")

                    # if EstudianteVinculacion.objects.filter(inscripcion=inscrip, nivelmalla__id=nivel).exists():
                    #     return HttpResponse(json.dumps(
                    #         {'result': 'bad', 'mensaje': "Ya tiene ingresar las practicas comunitaria en ese nivel"}),
                    #                 content_type='application/json')

                    return HttpResponse(json.dumps({"result": "ok"}), content_type="application/json")

                if action == 'validahorasniveleditar':
                    horas = int(request.POST['numerohoras'])
                    nivel = int(request.POST['idnivel'])
                    inscrip = Inscripcion.objects.get(pk=request.POST['inscriid'])
                    malla = Malla.objects.get(carrera=inscrip.carrera)
                    asig = AsignaturaMalla.objects.get(asignatura__nombre__icontains='PREPRO',malla=malla,nivelmalla__id=nivel)
                    horastotalingresada = horas + InscripcionPracticas.objects.filter(inscripcion=inscrip,nivelmalla__id=nivel).aggregate(Sum('horas'))['horas__sum'] if InscripcionPracticas.objects.filter(inscripcion=inscrip,nivelmalla__id=nivel).aggregate(Sum('horas'))['horas__sum']!=None else 0

                    if horastotalingresada>asig.horas:
                        return HttpResponse(json.dumps({'result':'bad', 'mensaje':"La cantidad de hora ingresada es mayor a la horas de la practica en este Nivel"}), content_type="application/json")


                    return HttpResponse(json.dumps({'result':'ok'}),content_type="application/json")

                if action=='activar':
                    inscripcion = Inscripcion.objects.get(pk=request.POST['id'])
                    f = ActivaInactivaUsuarioForm(request.POST)
                    if f.is_valid():
                        activa = InactivaActivaUsr(inscripcion=inscripcion, accion='activo',
                                                              motivo=f.cleaned_data['motivo'], fecha=datetime.now(),
                                                              usuario= request.user)
                        activa.save()

                        inscripcion.persona.usuario.is_active = True
                        inscripcion.persona.usuario.save()
                        activa.activa_usuario()

                        # Log de ACTIVAR USUARIO ESTUDIANTE
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(inscripcion).pk,
                            object_id       = inscripcion.id,
                            object_repr     = force_str(inscripcion),
                            action_flag     = ADDITION,
                            change_message  = 'Activado Estudiante' )
                        return HttpResponseRedirect("/inscripciones?s="+str(inscripcion.persona.cedula))
                elif action =='addtramite':
                    try:
                        inscripcion = Inscripcion.objects.filter(pk=request.POST['idinscrip'])[:1].get()
                        solicitud = SolicitudOnline.objects.filter(pk=3)[:1].get()

                        # if solicitud.libre:
                        #     form.for_tipo(inscripcion)

                        f = EspecieUniversalForm(request.POST)


                        if not 'comprobante' in request.FILES or  len(request.POST['observacion']) == 0:
                            return HttpResponseRedirect("/inscripciones?action=ingresacomprobante&idins="+str(inscripcion.id)+"&error=TODOS LOS CAMPOS SON OBLIGATORIOS")
                        solicitudest = SolicitudEstudiante(solicitud=solicitud,
                                                          inscripcion=inscripcion,
                                                          fecha=datetime.now(),
                                                          observacion= (request.POST['observacion']),
                                                          tipoe_id=ID_TIPO_SOLICITUD)
                        solicitudest.save()

                        solicitudsec = SolicitudSecretariaDocente(persona=inscripcion.persona,
                                                           solicitudestudiante=solicitudest,
                                                           tipo=solicitudest.tipoe.tiposolicitud,
                                                           descripcion=solicitudest.observacion,
                                                           fecha = datetime.now(),
                                                           hora = datetime.now().time(),
                                                           cerrada = False)
                        solicitudsec.save()
                        adjunto=False
                        solicitudest.solicitado=True
                        solicitudest.save()
                        if 'comprobante' in request.FILES:
                            solicitudsec.comprobante= request.FILES['comprobante']
                            solicitudsec.save()
                            adjunto=True
                        listasolicitudes=[]
                        coordinacion = Coordinacion.objects.filter(carrera=solicitudsec.solicitudestudiante.inscripcion.carrera)[:1].get()
                        for cdp in  CoordinacionDepartamento.objects.filter(coordinacion=coordinacion):
                            if EspecieGrupo.objects.filter(departamento=cdp.departamento,tipoe=solicitudsec.solicitudestudiante.tipoe).exists():
                                asistentes=None
                                if cdp.departamento.id == 27:
                                    cajeros = SesionCaja.objects.filter(abierta=True).values('caja__persona')
                                    # asistentes  = AsistenteDepartamento.objects.filter(departamento=cdp.departamento,persona__id__in=cajeros).exclude(puedereasignar=True).order_by('cantidadsol')
                                    if HorarioAsistenteSolicitudes.objects.filter(fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time()).exists():
                                         horarioasis = HorarioAsistenteSolicitudes.objects.filter(fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time()).values('usuario')
                                         asistentes = AsistenteDepartamento.objects.filter(departamento=cdp.departamento,persona__usuario__id__in=horarioasis,persona__id__in=cajeros).exclude(puedereasignar=True).order_by('cantidadsol')
                                else:
                                    if HorarioAsistenteSolicitudes.objects.filter(fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time()).exists():
                                         horarioasis = HorarioAsistenteSolicitudes.objects.filter(fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time()).values('usuario')
                                         asistentes = AsistenteDepartamento.objects.filter(departamento=cdp.departamento,persona__usuario__id__in=horarioasis).exclude(puedereasignar=True).order_by('cantidadsol')

                                if asistentes:
                                    for asis in asistentes:
                                        asis.cantidadsol =asis.cantidadsol +1
                                        solicitudsec.usuario = asis.persona.usuario
                                        solicitudsec.personaasignada =asis.persona
                                        solicitudsec.asignado=True
                                        solicitudsec.fechaasignacion = datetime.now()
                                        solicitudsec.usuarioasigna=asis.persona.usuario
                                        solicitudsec.save()
                                        asis.save()
                                        listasolicitudes.append(asis.persona.emailinst)
                                        break
                        if listasolicitudes:
                            try:
                                 hoy = datetime.now().today()
                                 contenido = "  Solicitudes Asignadas"
                                 descripcion = "Ud. tiene solicitudes por atender"
                                 send_html_mail(contenido,
                                    "emails/notificacion_solicitud_adm.html", {'fecha': hoy,'contenido': contenido,'descripcion':descripcion,'opcion':'1'},listasolicitudes)
                            except Exception as e:
                                print((e))
                                pass
                        if EMAIL_ACTIVE:
                            # f.instance.mail_subject_nuevo()
                            #OCastillo 17-05-2019
                            gruposexcluidos = [SISTEMAS_GROUP_ID]
                            lista=''
                            persona=Persona.objects.filter(usuario=request.user)[:1].get()
                            lista = str(persona.email)
                            hoy = datetime.now().today()
                            contenido = "Nueva Solicitud"
                            descripcion = "Estimado/a estudiante. Su solicitud ha sido recibida. Sera asignada al Departamento correspondiente. Puede ver el estado de la misma en el Sistema."
                            send_html_mail(contenido,
                                "emails/nuevasolicitud.html", {'d': solicitudsec, 'fecha': hoy,'contenido': contenido,'descripcion':descripcion,'opcion':'1'},lista.split(','))

                            #traigo el correo del grupo a quien le corresponde el tipo de solicitud
                            if SolicitudesGrupo.objects.filter(tiposolic=solicitudsec.tipo,carrera=inscripcion.carrera.id).exists():
                                grupo_solicitud=SolicitudesGrupo.objects.filter(tiposolic=solicitudsec.tipo,carrera=inscripcion.carrera.id).values('grupo')
                                if ModuloGrupo.objects.filter(grupos__in=grupo_solicitud).exists():
                                    correo_solicitud=[]
                                    for correo_grupo in ModuloGrupo.objects.filter(grupos__in=grupo_solicitud):
                                        correo_solicitud.append(correo_grupo.correo)
                                        if lista:
                                            lista = lista+','+correo_grupo.correo
                                        else:
                                            lista = correo_grupo.correo
                            else:
                                #Para el caso de una solicitud tipo general para todas las carreras
                                if SolicitudesGrupo.objects.filter(tiposolic=solicitudsec.tipo,todas_carreras=True).exists():
                                    if solicitudsec.tipo.sistema==True:
                                        grupo_solicitud=SolicitudesGrupo.objects.filter(tiposolic=solicitudsec.tipo,todas_carreras=True).values('grupo')
                                    else:
                                        grupo_solicitud=SolicitudesGrupo.objects.filter(tiposolic=solicitudsec.tipo,todas_carreras=True).exclude(grupo__id__in=gruposexcluidos).values('grupo')
                                    if ModuloGrupo.objects.filter(grupos__in=grupo_solicitud).exists():
                                       correo_solicitud=[]
                                       for correo_grupo in ModuloGrupo.objects.filter(grupos__in=grupo_solicitud):
                                           correo_solicitud.append(correo_grupo.correo)
                                           if lista:
                                                lista = lista+','+correo_grupo.correo
                                           else:
                                                lista = correo_grupo.correo

                            hoy = datetime.now().today()
                            contenido = "Nueva Solicitud"
                            # descripcion = solicitud.descripcion
                            # if adjunto:
                            #      descripcion = descripcion +   " Archivo adjunto"
                            #     # descripcion = solicitud.descripcion +  "Estudiante ha realizado solicitud. Revisar el detalle de la misma en el Modulo Solicitudes de Alumnos. Archivo adjunto"
                            send_html_mail(contenido,
                                "emails/nuevasolicitud.html", {'d': solicitudsec, 'fecha': hoy,'contenido': contenido,'adjunto':adjunto,'opcion':'2'},lista.split(','))
                            if 'comprobante' in request.FILES:
                                pass

                            return HttpResponseRedirect("/inscripciones?info=SE AGREGO CORRECTAMENTE")
                        else:
                            return HttpResponseRedirect("/inscripciones?action=ingresacomprobante&idins="+str(inscripcion.id))
                        # else:
                        #     # print(f)
                        #     return HttpResponseRedirect("/inscripciones?action=ingresacomprobante&idins="+str(inscripcion.id)+"&error=TODOS LOS CAMPOS SON OBLIGATORIOS")
                    except Exception as e:
                        print(e)
                        return HttpResponseRedirect("/inscripciones?action=ingresacomprobante&idins="+str(inscripcion.id)+"&error="+str(e))
                elif action=='edithistorico':
                    historico = HistoricoRecordAcademico.objects.get(pk=request.POST['id'])
                    asignatura = historico.asignatura

                    if historico.inscripcion.carrera.online:
                        asistenciaparaaprobar = 0
                    else:
                        asistenciaparaaprobar = ASIST_PARA_APROBAR
                    if historico.inscripcion.recordacademico_set.filter(asignatura__in=asignatura.precedencia.all().values('id'),nota__gte=NOTA_PARA_APROBAR,asistencia__gte=asistenciaparaaprobar).exists() or not asignatura.precedencia.all():
                        if RecordAcademico.objects.filter(inscripcion=historico.inscripcion,asignatura=historico.asignatura).exists():
                            record = RecordAcademico.objects.filter(inscripcion=historico.inscripcion,asignatura=historico.asignatura)[:1].get()
                        else:
                            record = RecordAcademico(inscripcion=historico.inscripcion, asignatura=historico.asignatura,
                                                    nota=0, asistencia=0,fecha=datetime.now(), aprobada=False,
                                                    convalidacion=False, pendiente=False)
                            record.save()

                        inscripcion = historico.inscripcion
                        f = HistoricoRecordAcademicoForm(request.POST)
                        if f.is_valid():
                            nota =  historico.nota
                            asistencia = historico.asistencia
                            historico.asignatura=f.cleaned_data['asignatura']
                            historico.nota=f.cleaned_data['nota']
                            historico.asistencia=f.cleaned_data['asistencia']
                            historico.fecha=f.cleaned_data['fecha']
                            historico.aprobada=f.cleaned_data['aprobada']
                            historico.convalidacion=f.cleaned_data['convalidacion']
                            historico.pendiente=f.cleaned_data['pendiente']

                            historico.save()

                            record.asignatura = historico.asignatura
                            record.nota = historico.nota
                            record.asistencia = historico.asistencia
                            record.fecha = historico.fecha
                            record.aprobada = historico.aprobada
                            record.convalidacion=historico.convalidacion
                            record.pendiente = historico.pendiente

                            record.save()

                            #Obtain client ip address
                            client_address = ip_client_address(request)

                            # Log de EDICION HISTORICO
                            LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(historico).pk,
                                object_id       = historico.id,
                                object_repr     = force_str(historico),
                                action_flag     = CHANGE,
                                change_message  = 'Editado Historico y Registro (' + client_address + ')' )
                            if 'INGLES' in historico.asignatura.nombre and EMAIL_ACTIVE:
                                historico.notificacion_ingles(request.user,nota,asistencia)

                            return HttpResponseRedirect("/inscripciones?action=historico&id="+str(inscripcion.id))
                        return HttpResponseRedirect("/inscripciones?action=edithistorico&id="+str(historico.id))
                    else:
                        return HttpResponseRedirect("/inscripciones?action=edithistorico&id="+str(historico.id)+"&error=FALTA APROBAR MATERIAS CON PRECEDENCIA")

                elif action=='addhistoriconotas':
                    historico = HistoricoRecordAcademico.objects.get(pk=request.POST['id'])
                    f = HistoricoNotasITBForm(request.POST)
                    if f.is_valid():
                        historia = HistoricoNotasITB(historico=historico,
                                                    n1=f.cleaned_data['n1'], cod1=f.cleaned_data['cod1'],
                                                    n2=f.cleaned_data['n2'], cod2=f.cleaned_data['cod2'],
                                                    n3=f.cleaned_data['n3'], cod3=f.cleaned_data['cod3'],
                                                    n4=f.cleaned_data['n4'], cod4=f.cleaned_data['cod4'],
                                                    n5=f.cleaned_data['n5'],
                                                    total = f.cleaned_data['total'],
                                                    recup = f.cleaned_data['recup'],
                                                    notafinal = f.cleaned_data['notafinal'],
                                                    estado = f.cleaned_data['estado'])
                        historia.save()

                        # Actualizar el Historico de Records
                        historico = historia.historico
                        historico.nota = historia.notafinal
                        historico.save()

                        #Actualizar el Record Academico
                        if RecordAcademico.objects.filter(inscripcion=historico.inscripcion, asignatura=historico.asignatura).exists():
                            record = RecordAcademico.objects.filter(inscripcion=historico.inscripcion, asignatura=historico.asignatura)[:1].get()
                            record.nota = historico.nota
                            record.save()

                        #Obtain client ip address
                        client_address = ip_client_address(request)

                        # Log de ADICIONAR HISTORICO NOTAS
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(historia).pk,
                            object_id       = historia.id,
                            object_repr     = force_str(historia),
                            action_flag     = ADDITION,
                            change_message  = 'Adicionado Historico Notas (' + client_address + ')' )

                        return HttpResponseRedirect("/inscripciones?action=historiconotas&id="+str(historia.id))
                    else:
                        return HttpResponseRedirect("/inscripciones?action=addhistoriconotas&id="+str(historico.id))

                elif action=='edithistoriconotas':
                    bande=0
                    historico = HistoricoRecordAcademico.objects.get(pk=request.POST['his'])
                    if historico.asignatura.id != ASIGNATURA_PRACTICA_CONDUCCION:
                        historia = HistoricoNotasITB.objects.get(pk=request.POST['id'])
                        f = HistoricoNotasITBForm(request.POST)
                    else:
                        historia = HistoricoNotasPractica.objects.get(pk=request.POST['id'])
                        f = HistoricoNotasPracticaForm(request.POST)
                        bande=1
                    if f.is_valid():
                        if bande == 1:
                            historia.responsable = f.cleaned_data['responsable'].id
                            historia.evaluador= f.cleaned_data['evaluador']
                        historia.n1 = f.cleaned_data['n1']
                        historia.n2 = f.cleaned_data['n2']
                        historia.n3 = f.cleaned_data['n3']
                        historia.n4 = f.cleaned_data['n4']
                        historia.n5 = f.cleaned_data['n5']

                        historia.cod1 = f.cleaned_data['cod1'].id
                        historia.cod2 = f.cleaned_data['cod2'].id
                        historia.cod3 = f.cleaned_data['cod3'].id
                        historia.cod4 = f.cleaned_data['cod4'].id

                        historia.total = f.cleaned_data['total']
                        historia.recup = f.cleaned_data['recup']
                        historia.notafinal = f.cleaned_data['notafinal']
                        historia.estado = f.cleaned_data['estado']

                        historia.save()

                        #Actualizar el Historico de Records
                        historico = historia.historico
                        historico.nota = historia.notafinal
                        if historia.estado_id == NOTA_ESTADO_APROBADO:
                            historico.aprobada = True
                        else:
                            historico.aprobada = False

                        historico.save()

                        #Actualizar el Record Academico
                        if RecordAcademico.objects.filter(inscripcion=historico.inscripcion, asignatura=historico.asignatura).exists():
                            record = RecordAcademico.objects.filter(inscripcion=historico.inscripcion, asignatura=historico.asignatura)[:1].get()
                            record.nota = historico.nota
                            record.aprobada = historico.aprobada
                            record.save()

                        #Obtain client ip address
                        client_address = ip_client_address(request)

                        # Log de EDITAR HISTORICO NOTAS
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(historico).pk,
                            object_id       = historico.id,
                            object_repr     = force_str(historico),
                            action_flag     = CHANGE,
                            change_message  = 'Editado Historia Notas del historico: '+str(historico.id) + ' (' + client_address + ')')

                        return HttpResponseRedirect("/inscripciones?action=historiconotas&id="+str(historia.historico.id))
                    else:
                        return HttpResponseRedirect("/inscripciones?action=edithistoriconotas&id="+str(historia.id))

                #OCastillo 21-07-2020 Permiso para que docente pueda ingresar notas asi estudiante tenga estado reprobado
                elif action=='permitir':
                    total=0
                    correocoordinacion = None
                    hist = HistoricoNotasITB.objects.get(pk=request.POST['idh'])
                    inscripcion = hist.historico.inscripcion
                    #OCastillo 22-04-2022 notificar a la coordinacion de la carrera el cambio solicitado
                    carrera=hist.historico.inscripcion.carrera
                    if Coordinacion.objects.filter(carrera=carrera).exists():
                        correocoordinacion = Coordinacion.objects.filter(carrera=carrera)[:1].get()
                    hist.recup=0
                    hist.permitir=True
                    hist.save()
                    total=(hist.n1+hist.n2+hist.n3+hist.n4+hist.n5)
                    hist.total=total
                    hist.notafinal=total
                    hist.save()

                    if HistoricoRecordAcademico.objects.filter(pk=hist.historico.id,inscripcion=inscripcion).exists():
                        h = HistoricoRecordAcademico.objects.filter(pk=hist.historico.id,inscripcion=inscripcion)[:1].get()
                        h.nota=total
                        h.save()

                    if RecordAcademico.objects.filter(inscripcion=inscripcion,asignatura=h.asignatura).exists():
                        r = RecordAcademico.objects.filter(inscripcion=inscripcion, asignatura=h.asignatura)[:1].get()
                        r.nota=total
                        r.save()

                    if EvaluacionAlcance.objects.filter(materiaasignada__materia__asignatura=h.asignatura,materiaasignada__matricula__inscripcion=inscripcion).exists():
                        evaalcance = EvaluacionAlcance.objects.filter(materiaasignada__materia__asignatura=h.asignatura,materiaasignada__matricula__inscripcion=inscripcion)[:1].get()
                        docente = Persona.objects.filter(usuario=evaalcance.usuario,usuario__is_active=True)[:1].get()
                    #Obtain client ip address
                    client_address = ip_client_address(request)
                    # Log de Cambiar Historico Notas
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(hist).pk,
                        object_id       = hist.id,
                        object_repr     = force_str(hist),
                        action_flag     = CHANGE,
                        change_message  = 'Agregado Permiso modificar notas (' + client_address + ')')

                    datos = {"result": "ok"}

                    materiaasignada = hist.historico.asignatura
                    estudiante = hist.historico.inscripcion.persona.nombre_completo_inverso()
                    carrera=hist.historico.inscripcion.carrera
                    persona = Persona.objects.get(usuario=request.user)
                    profesor=docente
                    opt=1
                    correo=str(persona.email) + ','+ str(persona.emailinst)+','+str('secretariageneral@bolivariano.edu.ec')+ ','+ str(correocoordinacion.correo)
                    # correo=str(persona.email) + ','+ str(persona.emailinst)+ ','+ str(correocoordinacion.correo)

                    if EMAIL_ACTIVE:
                        mail_respuestasecretaria('RESPUESTA A SOLICITUD - > SU PETICION HA SIDO ACEPTADA, PUEDE MODIFICAR LAS NOTAS A ESTUDIANTE ','PERMISO CAMBIO DE NOTAS',correo,carrera,materiaasignada,profesor,estudiante,request.user,opt)
                        return HttpResponse(json.dumps(datos),content_type="application/json")

                    return HttpResponse(json.dumps(datos),content_type="application/json")

                    #return HttpResponseRedirect("/inscripciones?action=historiconotas&id="+str(inscripcion.id))


                elif action == 'addhistorianivel':
                    f = HistoriaNivelesDeInscripcionForm(request.POST)
                    if f.is_valid():
                        f.save()
                        return HttpResponseRedirect("/inscripciones?action=historianivel&id="+str(f.instance.inscripcion.id))
                    else:
                        return HttpResponseRedirect("/inscripciones?action=addhistorianivel&id="+str(f.instance.inscripcion.id))

                elif action=='editrecord':
                    record = RecordAcademico.objects.get(pk=request.POST['id'])
                    inscripcion = record.inscripcion
                    f = RecordAcademicoForm(request.POST)
                    if f.is_valid():
                        record.asignatura=f.cleaned_data['asignatura']
                        record.nota=f.cleaned_data['nota']
                        record.asistencia=f.cleaned_data['asistencia']
                        record.fecha=f.cleaned_data['fecha']
                        record.aprobada=f.cleaned_data['aprobada']
                        record.convalidacion=f.cleaned_data['convalidacion']
                        record.pendiente=f.cleaned_data['pendiente']

                        record.save()

                        #Obtain client ip address
                        client_address = ip_client_address(request)

                        # Log de EDITAR RECORD
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(record).pk,
                            object_id       = record.id,
                            object_repr     = force_str(record),
                            action_flag     = CHANGE,
                            change_message  = 'Editado Registro Academico (' + client_address + ')')

                        return HttpResponseRedirect("/inscripciones?action=record&id="+str(inscripcion.id))
                    else:
                        return HttpResponseRedirect("/inscripciones?action=editrecord&id="+str(inscripcion.id))

                elif action == 'aprobarproceso':
                    try:
                        persona = request.session['persona']
                        procesodobe = ProcesoDobe.objects.get(pk=request.POST['id'])
                        procesodobe.aprobado = True
                        procesodobe.save()

                        usu = Inscripcion.objects.filter(pk=procesodobe.inscripcion.id)[:1].get().persona.usuario.id
                        usuario = User.objects.filter(pk=usu)[:1].get()
                        usuario.is_active=True
                        usuario.save()

                        client_address = ip_client_address(request)

                        # Log de EDITAR RECORD
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(procesodobe).pk,
                            object_id       = procesodobe.id,
                            object_repr     = force_str(procesodobe),
                            action_flag     = CHANGE,
                            change_message  = 'Aprobado Proceso Dobe (' + client_address + ')')
                        if  EMAIL_ACTIVE:
                            procesodobe.mail_procesodobe(persona)

                        return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                    except Exception as ex:
                        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")



                elif action == 'addpracticasdistribucion':
                    try:
                        practica=None
                        inscripcion = Inscripcion.objects.get(pk=request.POST['inscripcion'])
                        datos = json.loads(request.POST['datos'])
                        ingreso=False
                        seguardo=False
                        ruta=''

                        for d in datos['detalle']:
                            if validaingresohorasdistribucion(inscripcion.id,int(d['hor']),int(d['nivel'])):
                                practica = InscripcionPracticas(inscripcion=inscripcion,
                                                                horas=int(d['hor']),
                                                                lugar=elimina_tildes(request.POST['id_lugar']).upper(),
                                                                profesor_id=int(request.POST['id_profesor']),
                                                                inicio=datetime.strptime(request.POST['id_inicio'], '%d-%m-%Y'),
                                                                fin=datetime.strptime(request.POST['id_fin'], '%d-%m-%Y'),
                                                                observaciones=elimina_tildes(request.POST['id_observaciones']).upper(),
                                                                equipamiento=elimina_tildes(request.POST['id_equipamiento']).upper(),
                                                                nivelmalla_id=int(d['nivel']))
                                practica.save()
                                if 'id_archivo' in request.FILES:
                                    if not seguardo:
                                        uploaded_file = request.FILES['id_archivo']
                                        print(f"Archivo subido: {uploaded_file.name}")

                                        practica.archivo = uploaded_file
                                        practica.save()
                                        seguardo=True
                                        ruta=practica.archivo.name
                                    else:
                                        practica.archivo=ruta
                                        practica.save()
                                ingreso=True

                        if ingreso:
                            practica.correo_practica(request.user, 'SE HA AGREGO PRACTICAS PREPROFESIONALES')
                            # Obtain client ip address
                            client_address = ip_client_address(request)

                            # Log de ADICIONAR DOCUMENTO
                            LogEntry.objects.log_action(
                                user_id=request.user.pk,
                                content_type_id=ContentType.objects.get_for_model(practica).pk,
                                object_id=practica.id,
                                object_repr=force_str(practica),
                                action_flag=ADDITION,
                                change_message='Adicionada Practica (' + client_address + ')')


                        return HttpResponse(json.dumps({"result": "ok"}), content_type="application/json")


                    except Exception as ex:
                        print(ex)
                        return HttpResponse(json.dumps({"result": "bad","mensaje":ex}),content_type="application/json")

                elif action=='delrecord':
                    record = RecordAcademico.objects.get(pk=request.POST['id'])
                    inscripcion = record.inscripcion

                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de BORRAR RECORD
                    LogEntry.objects.log_action(
                     user_id         = request.user.pk,
                     content_type_id = ContentType.objects.get_for_model(record).pk,
                     object_id       = record.id,
                     object_repr     = force_str(record),
                     action_flag     = DELETION,
                     change_message  = 'Borrado Registro Academico (' + client_address + ')')

                    record.delete()
                    return HttpResponseRedirect("/inscripciones?action=record&id="+str(inscripcion.id))

                elif action=='delhistorianivel':
                    historianivel = HistoriaNivelesDeInscripcion.objects.get(pk=request.POST['id'])
                    inscripcion = historianivel.inscripcion

                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de BORRAR HISTORIA NIVEL
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(historianivel).pk,
                        object_id       = historianivel.id,
                        object_repr     = force_str(historianivel),
                        action_flag     = DELETION,
                        change_message  = 'Borrada Historia Nivel' )

                    historianivel.delete()
                    return HttpResponseRedirect("/inscripciones?action=historianivel&id="+str(inscripcion.id) + ' (' + client_address + ')')

                elif action=='delhistorico':
                    record = HistoricoRecordAcademico.objects.get(pk=request.POST['id'])
                    inscripcion = record.inscripcion

                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de BORRAR HISTORICO
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(record).pk,
                        object_id       = record.id,
                        object_repr     = force_str(record),
                        action_flag     = DELETION,
                        change_message  = 'Borrado Historico Academico (' + client_address + ')')

                    record.delete()
                    return HttpResponseRedirect("/inscripciones?action=historico&id="+str(inscripcion.id))
                elif action=='edithistorianivel':
                    f = HistoriaNivelesDeInscripcionForm(request.POST,instance=HistoriaNivelesDeInscripcion.objects.get(pk=request.POST['id']))
                    if f.is_valid():
                        f.save()
                        return HttpResponseRedirect("/inscripciones?action=historianivel&id="+str(f.instance.inscripcion.id))
                    else:
                        return HttpResponseRedirect("/inscripciones?action=edithistorianivel&id="+str(f.instance.inscripcion.id))

                elif action == 'addpanel':
                    try:
                        i = Inscripcion.objects.get(pk=request.POST['id'])
                        p = Panel.objects.get(pk=request.POST['panel'])
                        if not PermisoPanel.objects.filter(inscripcion=i,panel=p).exists():
                            ip = PermisoPanel(inscripcion=i,panel=p)
                            ip.save()

                            #Obtain client ip address
                            client_address = ip_client_address(request)

                            # Log de BORRAR HISTORICO
                            LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(ip).pk,
                                object_id       = ip.id,
                                object_repr     = force_str(ip),
                                action_flag     = ADDITION,
                                change_message  = 'Agregado Permiso a Panel (' + client_address + ')')
                        return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                    except Exception as ex:
                        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

                elif action=='convalidar':
                    convalidacion = ConvalidacionInscripcion.objects.get(pk=request.POST['id'])
                    f = ConvalidacionInscripcionForm(request.POST)
                    if f.is_valid():
                        convalidacion.centro = f.cleaned_data['centro']
                        convalidacion.carrera = f.cleaned_data['carrera']
                        convalidacion.asignatura = f.cleaned_data['asignatura']
                        convalidacion.anno = f.cleaned_data['anno']
                        convalidacion.nota_ant = f.cleaned_data['nota_ant']
                        convalidacion.nota_act = f.cleaned_data['nota_act']
                        convalidacion.observaciones = f.cleaned_data['observaciones']
                        convalidacion.usuario = request.user
                        convalidacion.fecha = datetime.now()
                        if INSCRIPCION_CONDUCCION:
                            convalidacion.ra = f.cleaned_data['ra']
                            convalidacion.exa = f.cleaned_data['exa']
                            convalidacion.nojus = f.cleaned_data['nojus']

                        convalidacion.save()

                        #Obtain client ip address
                        client_address = ip_client_address(request)

                        # Log de ADICIONAR CONVALIDACION
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(convalidacion).pk,
                            object_id       = convalidacion.id,
                            object_repr     = force_str(convalidacion),
                            action_flag     = ADDITION,
                            change_message  = 'Adicionada Convalidacion' + ' (' + client_address + ')')

                        return HttpResponseRedirect("/inscripciones?action=record&id="+str(convalidacion.record.inscripcion.id))
                    else:
                        return HttpResponseRedirect("/inscripciones?action=convalidar&id="+str(convalidacion.record.id))

                elif action == 'cargarfoto':
                    inscripcion = Inscripcion.objects.get(pk=request.POST['id'])
                    form = CargarFotoForm(inscripcion, request.FILES)
                    if form.is_valid():
                        persona = inscripcion.persona
                        foto = persona.foto()
                        if foto!=None:
                            foto.foto = request.FILES['foto']
                        else:
                            foto = FotoPersona(persona=persona, foto=request.FILES['foto'])

                        foto.save()

                elif action == 'verificar_empresaconvenio':
                    if EmpresaConvenio.objects.filter(pk=request.POST['id']).exists():
                        empresaconvenio = EmpresaConvenio.objects.get(pk=request.POST['id'])
                        if DescuentosporConvenio.objects.filter(empresaconvenio=empresaconvenio,activo=True).exists() and empresaconvenio.esempresa:
                            return HttpResponse(json.dumps({"result":1}),content_type="application/json")
                    return HttpResponse(json.dumps({"result":0}),content_type="application/json")


                elif action=='add':
                        documento=False
                        asp=None
                        try:
                            if not CENTRO_EXTERNO:
                                f = InscripcionForm(request.POST)
                                inscripaspirantes=''
                                if f.is_valid():
                                    # if not Persona.objects.filter(Q(cedula=f.cleaned_data['cedula'])).exists():
                                    # if not Persona.objects.filter(Q(cedula=f.cleaned_data['cedula'])|Q(pasaporte=f.cleaned_data['pasaporte'])).exists():
                                    if request.user.has_perm('sga.add_referidos') :
                                      valida=False
                                    else:
                                      valida=True

                                    if valida :

                                        datosCrm = requests.post('https://crm.itb.edu.ec/api',{'a': 'verificarprospecto1','identificacion': str(f.cleaned_data['cedula'])},verify=False)

                                        if datosCrm.status_code == 200:
                                            datosCrm=datosCrm.json()
                                            if datosCrm['result']=='ok':
                                                pass
                                            else:
                                                #return HttpResponse(json.dumps({"result":"bad3","mensaje":"SE ENCUENTRA REGISTRADO EN EL CRM PRESENCIAL"}),content_type="application/json")
                                                mensajeinscrip='SE ENCUENTRA REGISTRADO EN EL CRM PRESENCIAL'
                                                return HttpResponseRedirect("/inscripciones?action=add&error1="+(str(mensajeinscrip)))

                                        datoscrmonline = requests.get('https://sgaonline.itb.edu.ec/funciones',params={'a': 'verificarprospecto1','identificacion': str(f.cleaned_data['cedula'])},verify=False)

                                        if datoscrmonline.status_code == 200:
                                            datoscrmonline=datoscrmonline.json()
                                            if datoscrmonline['result']=='ok':
                                                pass
                                            else:
                                                # return HttpResponse(json.dumps({"result":"bad3","mensaje":"SE ENCUENTRA REGISTRADO EN EL CRM ONLINE"}),content_type="application/json")
                                                mensajeinscrip='SE ENCUENTRA REGISTRADO EN EL CRM ONLINE'
                                                return HttpResponseRedirect("/inscripciones?action=add&error1="+(str(mensajeinscrip)))


                                        datoscrmonlinereferido = requests.get('https://sgaonline.itb.edu.ec/funciones',params={'a': 'verificareferido1','identificacion': str(f.cleaned_data['cedula'])},verify=False)

                                        if datoscrmonlinereferido.status_code == 200:
                                            datoscrmonlinereferido=datoscrmonlinereferido.json()
                                            if datoscrmonlinereferido['result']=='ok':
                                                pass
                                            else:
                                                # return HttpResponse(json.dumps({"result":"bad3","mensaje":"SE ENCUENTRA REGISTRADO EN REFERIDO ONLINE"}),content_type="application/json")
                                                mensajeinscrip='SE ENCUENTRA REGISTRADO EN REFERIDO ONLINE'
                                                return HttpResponseRedirect("/inscripciones?action=add&error1="+(str(mensajeinscrip)))



                                        if ReferidosInscripcion.objects.filter(cedula=request.POST['cedula']).exists():
                                            # return HttpResponse(json.dumps({"result":"bad3","mensaje":"Se encuentra registrado en referidos"}),content_type="application/json")

                                            rf = ReferidosInscripcion.objects.get(cedula=request.POST['cedula'])
                                            valida = False

                                            if Inscripcion.objects.filter(persona__cedula=rf.cedula,persona__usuario__is_active=False).exclude(
                                                persona__cedula=None).exclude(persona__cedula='').exists():
                                                valida=True

                                            elif Inscripcion.objects.filter(persona__pasaporte=rf.cedula,persona__usuario__is_active=False).exclude(
                                                    persona__pasaporte=None).exclude(persona__pasaporte='').exists():

                                                valida = True

                                            if valida==True:
                                                mensajeinscrip='SE ENCUENTRA REGISTRADO EN REFERIDO '
                                                return HttpResponseRedirect("/inscripciones?action=add&error1="+(str(mensajeinscrip)))





                                    # OCastillo 27-septiembre-2018 solo el usuario que lo graba en aspirantes lo inscribe
                                    if InscripcionAspirantes.objects.filter(cedula=f.cleaned_data['cedula'],activo=True,extranjero=False).order_by('-id').exists() or  InscripcionAspirantes.objects.filter(pasaporte=f.cleaned_data['pasaporte'],extranjero=True,activo=True).order_by('-id').exists():
                                        if InscripcionAspirantes.objects.filter(cedula=f.cleaned_data['cedula'],activo=True,extranjero=False).order_by('-id').exists():
                                             asp = InscripcionAspirantes.objects.filter(cedula=f.cleaned_data['cedula'],activo=True,extranjero=False).order_by('-id')[:1].get()
                                        else:
                                            asp = InscripcionAspirantes.objects.filter(pasaporte=f.cleaned_data['pasaporte'],activo=True,extranjero=True).order_by('-id')[:1].get()
                                        if asp:
                                            if asp.fueratiempo() <= 7:
                                                 if asp.usuario != request.user:
                                                    #06-03-2019 OCastillo solo Narcisa inscribira de usuario Ventas Externas
                                                    if asp.usuario.username == 'vexterno' and request.user.username=='gngonzalez2':
                                                        pass
                                                    else:
                                                        mensajeinscrip='Proviene del Modulo Aspirantes, no puede ser ingresado por UD'
                                                        return HttpResponseRedirect("/inscripciones?action=add&error1="+(str(mensajeinscrip)))

                                    persona = Persona(nombres=elimina_tildes(f.cleaned_data['nombres']),
                                                    apellido1= elimina_tildes(f.cleaned_data['apellido1']),
                                                    apellido2=elimina_tildes(f.cleaned_data['apellido2']),
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
                                                    sector = f.cleaned_data['sector'],
                                                    provinciaresid=f.cleaned_data['provinciaresid'],
                                                    cantonresid=f.cleaned_data['cantonresid'],
                                                    ciudad = f.cleaned_data['ciudad'],
                                                    telefono=f.cleaned_data['telefono'],
                                                    telefono_conv=f.cleaned_data['telefono_conv'],
                                                    email=f.cleaned_data['email'],
                                                    email1=f.cleaned_data['email1'],
                                                    email2=f.cleaned_data['email2'],
                                                    sangre=f.cleaned_data['sangre'],
                                                    # emailinst=f.cleaned_data['emailinst'],
                                                    parroquia=f.cleaned_data['parroquia'])
                                    persona.save()
                                    if 'sectorresid' in f.cleaned_data :
                                        persona.sectorresid=f.cleaned_data['sectorresid']
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

                                    inscripcion = Inscripcion(persona=persona,
                                                                # fecha=f.cleaned_data['fecha'],
                                                                fecha = datetime.now(),
                                                                carrera=f.cleaned_data['carrera'],
                                                                modalidad=f.cleaned_data['modalidad'],
                                                                sesion=f.cleaned_data['sesion'],
                                                                # colegio=f.cleaned_data['colegio'],
                                                                especialidad=f.cleaned_data['especialidad'],
                                                                identificador=f.cleaned_data['identificador'],
                                                                tienediscapacidad=f.cleaned_data['tienediscapacidad'],
                                                                doblematricula=f.cleaned_data['doblematricula'],
                                                                observacion=f.cleaned_data['observacion'],
                                                                anuncio=f.cleaned_data['anuncio'],
                                                                user=request.user)

                                    #Verifica que no se cree una Inscripcion doble (misma Cedula y Carrera)
                                    if not Inscripcion.objects.filter(persona__cedula=persona.cedula, carrera=f.cleaned_data['carrera'] ,persona__pasaporte=persona.pasaporte).exists():

                                        # inscripcion.save()
                                                #Incrementar el numerom a partir del ultimo inscrito del sistema para
                                        i = Inscripcion.objects.latest('id') if Inscripcion.objects.exists() else None
                                        if i:
                                            inscripcion.numerom = i.numerom + 1
                                        else:
                                            inscripcion.numerom = 1

                                        if not INSCRIPCION_CONDUCCION:
                                            if f.cleaned_data['promocion']:
                                                inscripcion.promocion = f.cleaned_data['promocion']
                                                inscripcion.descuentoporcent = f.cleaned_data['descuentoporcent']
                                            if f.cleaned_data['becamunicipio']:
                                                inscripcion.becamunicipio=f.cleaned_data['becamunicipio']
                                            if f.cleaned_data['empresaconvenio']:
                                                empresa_convenio = EmpresaConvenio.objects.get(pk=request.POST['empresaconvenio'])
                                                inscripcion.empresaconvenio = empresa_convenio
                                                # inscripcion.empresaconvenio = f.cleaned_data['empresaconvenio']
                                                if empresa_convenio.esempresa:
                                                    if DescuentosporConvenio.objects.filter(empresaconvenio=inscripcion.empresaconvenio,activo=True).exists():
                                                        inscripcion.tipopersonaempresaconvenio = f.cleaned_data['tipopersona']
                                                        inscripcion.descuentoconvenio = f.cleaned_data['descuentoempresa']
                                                        if 'documentoconvenio' in request.FILES:
                                                            inscripcion.documentoempresaconvenio=request.FILES['documentoconvenio']
                                                        if f.cleaned_data['espariente']==True:
                                                            inscripcion.parentescotipopersonaec = f.cleaned_data['pariente']
                                            if 'autorizacionbecadobe' in  f.cleaned_data:
                                                # if f.cleaned_data['autorizacionbecadobe']:
                                                inscripcion.autorizacionbecadobe=f.cleaned_data['autorizacionbecadobe']

                                            if 'autorizacionbecasencyt' in  f.cleaned_data:
                                                inscripcion.autorizacionbecasenecyt=f.cleaned_data['autorizacionbecasencyt']

                                            if 'aprobacionayudadobe' in  f.cleaned_data:
                                                inscripcion.aprobacionayudadobe=f.cleaned_data['aprobacionayudadobe']

                                            if 'benemeritocuerpobombero' in  f.cleaned_data:
                                                # if f.cleaned_data['autorizacionbecadobe']:
                                                inscripcion.benemeritocuerpobombero=f.cleaned_data['benemeritocuerpobombero']

                                        inscripcion.save()
                                        if f.cleaned_data['estcolegio']:
                                            inscripcion.estcolegio_id = f.cleaned_data['estcolegio_id']
                                            inscripcion.save()

                                        # Crear el registro en el Perfil de Inscripciones si es discapacitado para el DOBE
                                        if inscripcion.tienediscapacidad:
                                            perfil = PerfilInscripcion(inscripcion=inscripcion, tienediscapacidad=True)
                                            perfil.save()

                                        # Foto Institucional 05-agosto-2016
                                        if 'foto' in request.FILES:
                                            foto = FotoInstEstudiante(inscripcion=inscripcion,
                                                                      foto=request.FILES['foto'])
                                            foto.save()

                                        # OCU para titulo bachiller extranjeros 10-enero-2017
                                        if 'titulodoc' in request.FILES:
                                            titulodoc = InscripcionExtranjerosTitulo(inscripcion=inscripcion,
                                                                                     titulodoc=request.FILES['titulodoc'])
                                            titulodoc.save()

                                        #Obtain client ip address
                                        client_address = ip_client_address(request)

                                        # Log de ADICIONAR INSCRIPCION
                                        LogEntry.objects.log_action(
                                            user_id         = request.user.pk,
                                            content_type_id = ContentType.objects.get_for_model(inscripcion).pk,
                                            object_id       = inscripcion.id,
                                            object_repr     = force_str(inscripcion),
                                            action_flag     = ADDITION,
                                            change_message  = 'Adicionada Inscripcion (' + client_address + ')' )


                                        # Grabo en tb proceso doble matricula OCU 30-sep-2015
                                        if inscripcion.doblematricula:
                                            px=''
                                            doblemat = ProcesoDobleMatricula(inscripcion=inscripcion, aprobado=False,fecha=datetime.now())
                                            doblemat.save()

                                            # obtengo informacion de ficha medica completa para grabar en nueva inscripcion OCU 28-03-2016
                                            if PersonaExtension.objects.filter(persona__cedula=persona.cedula).exclude(persona__cedula='').exists() or PersonaExtension.objects.filter(persona__pasaporte=persona.pasaporte).exclude(persona__pasaporte='').exists():
                                                if PersonaExtension.objects.filter(persona__cedula=persona.cedula).exclude(persona__cedula='').exists():
                                                    for p in PersonaExtension.objects.filter(persona__cedula=persona.cedula).exclude(persona__cedula=''):
                                                        if not p.persona.datos_medicos_incompletos():
                                                            px=p
                                                else:
                                                    # obtengo informacion de ficha medica completa para grabar en nueva inscripcion OCU 31-03-2016
                                                    for p in PersonaExtension.objects.filter(persona__pasaporte=persona.pasaporte).exclude(persona__pasaporte=''):
                                                        if not p.persona.datos_medicos_incompletos():
                                                            px=p

                                                if not px.persona.datos_medicos_incompletos():

                                                    personaext = PersonaExtension(persona=persona,
                                                                                  estadocivil=px.estadocivil,
                                                                                  tienelicencia=px.tienelicencia,
                                                                                  tipolicencia=px.tipolicencia,
                                                                                  telefonos=px.telefonos,
                                                                                  tieneconyuge=px.tieneconyuge,
                                                                                  hijos=px.hijos,
                                                                                  padre=px.padre,
                                                                                  edadpadre=px.edadpadre,
                                                                                  estadopadre=px.estadopadre,
                                                                                  telefpadre=px.telefpadre,
                                                                                  educacionpadre=px.educacionpadre,
                                                                                  profesionpadre=px.profesionpadre,
                                                                                  trabajopadre=px.trabajopadre,
                                                                                  madre=px.madre,
                                                                                  edadmadre=px.edadmadre,
                                                                                  estadomadre=px.estadomadre,
                                                                                  telefmadre=px.telefmadre,
                                                                                  educacionmadre=px.educacionmadre,
                                                                                  profesionmadre=px.profesionmadre,
                                                                                  trabajomadre=px.trabajomadre,
                                                                                  conyuge=px.conyuge,
                                                                                  edadconyuge=px.edadconyuge,
                                                                                  estadoconyuge=px.estadoconyuge,
                                                                                  telefconyuge=px.telefconyuge,
                                                                                  educacionconyuge=px.educacionconyuge,
                                                                                  profesionconyuge=px.profesionconyuge,
                                                                                  trabajoconyuge=px.trabajoconyuge,
                                                                                  enfermedadpadre=px.enfermedadpadre,
                                                                                  enfermedadmadre=px.enfermedadmadre,
                                                                                  enfermedadabuelos=px.enfermedadabuelos,
                                                                                  enfermedadhermanos=px.enfermedadhermanos,
                                                                                  enfermedadotros=px.enfermedadotros)
                                                    personaext.save()

                                                    #Ficha Medica
                                                    if PersonaFichaMedica.objects.filter(personaextension=px).exists():
                                                        pfm = PersonaFichaMedica.objects.get(personaextension=px)
                                                        personafmedica=PersonaFichaMedica(personaextension=personaext,
                                                                                          vacunas=pfm.vacunas,
                                                                                          nombrevacunas=pfm.nombrevacunas,
                                                                                          enfermedades=pfm.enfermedades,
                                                                                          nombreenfermedades=pfm.nombreenfermedades,
                                                                                          alergiamedicina=pfm.alergiamedicina,
                                                                                          nombremedicinas=pfm.nombremedicinas,
                                                                                          alergiaalimento=pfm.alergiaalimento,
                                                                                          nombrealimentos=pfm.nombrealimentos,
                                                                                          cirugias=pfm.cirugias,
                                                                                          nombrecirugia=pfm.nombrecirugia,
                                                                                          fechacirugia=pfm.fechacirugia,
                                                                                          aparato=pfm.aparato,
                                                                                          tipoaparato=pfm.tipoaparato,
                                                                                          gestacion=pfm.gestacion,
                                                                                          partos=pfm.partos,
                                                                                          abortos=pfm.abortos,
                                                                                          cesareas=pfm.cesareas,
                                                                                          hijos2=pfm.hijos2,
                                                                                          cigarro=pfm.cigarro,
                                                                                          numerocigarros=pfm.numerocigarros,
                                                                                          tomaalcohol=pfm.tomaalcohol,
                                                                                          tipoalcohol=pfm.tipoalcohol,
                                                                                          copasalcohol=pfm.copasalcohol,
                                                                                          tomaantidepresivos=pfm.tomaantidepresivos,
                                                                                          antidepresivos=pfm.antidepresivos,
                                                                                          tomaotros=pfm.tomaotros,
                                                                                          otros=pfm.otros,
                                                                                          horassueno=pfm.horassueno,
                                                                                          calidadsuenno=pfm.calidadsuenno)
                                                    personafmedica.save()

                                                    # Examen Fisico
                                                    if PersonaExamenFisico.objects.filter(personafichamedica__personaextension=px).exists():
                                                        pef=PersonaExamenFisico.objects.get(personafichamedica__personaextension=px)
                                                        personaef=PersonaExamenFisico(personafichamedica=personafmedica,
                                                                                      inspeccion=pef.inspeccion,
                                                                                      usalentes=pef.usalentes,
                                                                                      motivo=pef.motivo,
                                                                                      peso=pef.peso,
                                                                                      talla=pef.talla,
                                                                                      pa=pef.pa,
                                                                                      pulso=pef.pulso,
                                                                                      rcar=pef.rcar,
                                                                                      rresp=pef.rresp,
                                                                                      temp=pef.temp,
                                                                                      observaciones=pef.observaciones)
                                                        personaef.save()

                                                # Verificar documentos en secretaria con cedula 31-03-2016 OCU ok

                                                if Inscripcion.objects.filter(persona__cedula=persona.cedula).exclude(persona__cedula='').exists() or Inscripcion.objects.filter(persona__pasaporte=persona.pasaporte).exclude(persona__pasaporte='').exists():
                                                    if Inscripcion.objects.filter(persona__cedula=persona.cedula).exclude(persona__cedula='').exists():
                                                        perins = Inscripcion.objects.filter(persona__cedula=persona.cedula).order_by('id')[:1].get()
                                                        doc_insc = DocumentosDeInscripcion.objects.filter(inscripcion=perins)[:1].get()
                                                    else:
                                                        perins = Inscripcion.objects.filter(persona__pasaporte=persona.pasaporte).order_by('id')[:1].get()
                                                        doc_insc = DocumentosDeInscripcion.objects.filter(inscripcion=perins)[:1].get()
                                                    if perins:
                                                        documentos = perins.documentos_entregados()
                                                        insdoc=DocumentosDeInscripcion(inscripcion=inscripcion,
                                                                                       titulo=doc_insc.titulo,
                                                                                       acta= doc_insc.acta,
                                                                                       cedula=doc_insc.cedula,
                                                                                       votacion=doc_insc.votacion,
                                                                                       fotos=doc_insc.fotos,
                                                                                       actaconv=doc_insc.actaconv,
                                                                                       partida_nac=doc_insc.partida_nac,
                                                                                       actafirmada=doc_insc.actafirmada)
                                                        insdoc.save()

                                        if  EMAIL_ACTIVE and inscripcion.doblematricula:
                                            doblemat.mail_procesodoblematricula(persona,inscripcion.carrera.nombre,request.user)

                                        if UTILIZA_GRUPOS_ALUMNOS:
                                            grupo = f.cleaned_data['grupo']

                                            ig = InscripcionGrupo(inscripcion=inscripcion, grupo=grupo, activo=True)
                                            ig.save()

                                            #Actualizar el estado del Grupo
                                            if grupo.abierto:
                                                grupo.abierto = grupo.esta_abierto()
                                                grupo.save()

                                            # Precios de Carrera segun grupo
                                            pcg = grupo.precios()
                                            valor =0
                                            if INSCRIPCION_CONDUCCION:
                                                if RubrosConduccion.objects.filter(carrera=inscripcion.carrera).exists():
                                                    r = RubrosConduccion.objects.filter(carrera=inscripcion.carrera)[:1].get()
                                                    rubro = Rubro(fecha=datetime.now(),valor=r.precio,inscripcion=inscripcion,cancelado=False,fechavence=ig.grupo.fin)
                                                    rubro.save()
                                                    #Se crea el tipo de Rubro Otro q es de tipo Derecho Examen
                                                    rubroo = RubroOtro(rubro=rubro, tipo=r.tipo, descripcion=r.descripcion)
                                                    rubroo.save()

                                            if GENERAR_RUBROS_PAGO and GENERAR_RUBRO_INSCRIPCION:
                                                if 'referido' in request.POST:
                                                    referido = ReferidosInscripcion.objects.get(pk=request.POST['referido'])
                                                    referido.inscrito=True
                                                    referido.inscripcionref = inscripcion
                                                    referido.save()
                                                    if pcg.precioinscripcion>0:
                                                        valor = Decimal(pcg.precioinscripcion) - Decimal((pcg.precioinscripcion*DESCUENTO_REFERIDO)/100).quantize(Decimal(10)**-2)
                                                else:
                                                    if pcg.precioinscripcion>0:
                                                        valor = pcg.precioinscripcion

                                                if 'insasp' in request.POST:
                                                    aspirante = InscripcionAspirantes.objects.get(pk=request.POST['insasp'])
                                                    aspirante.inscrito=True
                                                    aspirante.inscripcion=inscripcion
                                                    aspirante.activo = False
                                                    aspirante.save()

                                                    if aspirante.vendedor:
                                                        insc_vend = InscripcionVendedor(inscripcion=inscripcion,
                                                                    fecha=datetime.now().date(),
                                                                    vendedor=aspirante.vendedor)
                                                        insc_vend.save()

                                                hoy = datetime.today().date()
                                                if valor>0:
                                                    tienedescuento =False
                                                    valdescuento=0
                                                    if  inscripcion.promocion:
                                                        if inscripcion.promocion.val_inscripcion > 0:
                                                            tienedescuento =True
                                                            valdescuento = (( valor * inscripcion.promocion.val_inscripcion)/100)
                                                            valor =valor - valdescuento
                                                            porcentajedescuento = inscripcion.promocion.val_inscripcion
                                                            descripdeta ='PROMOCION '+ elimina_tildes(inscripcion.promocion.descripcion) + ' ' + str(inscripcion.promocion.val_inscripcion)

                                                    if HABILITA_DESC_INSCRIPCION and not  tienedescuento:
                                                        if not inscripcion.carrera.validacionprofesional:
                                                            #OCastillo 04-10-2021 no aplica descuento por grupo que no este marcado
                                                            if inscripcion.grupo().descuento:
                                                                #OCastillo 02-12-2021 se debe excluir de descuento por convenio empresas rubro inscripcion
                                                                if not inscripcion.descuentoconvenio:
                                                                    valdescuento = (( valor * DESCUENTO_INSCRIPCION)/100)
                                                                    valor =valor - valdescuento
                                                                    descripdeta = 'PROMOCION ' + str(DESCUENTO_INSCRIPCION) + ' DESCUENTO POR INSCRIPCION'
                                                                    porcentajedescuento = DESCUENTO_INSCRIPCION
                                                    rubro = Rubro(fecha=hoy, valor=valor,
                                                                    inscripcion=inscripcion, cancelado=False,
                                                                    fechavence=hoy+timedelta(GENERAR_RUBRO_INSCRIPCION_MARGEN_DIAS))
                                                    rubro.save()
                                                    if valdescuento > 0:
                                                        desc = Descuento(inscripcion = inscripcion,
                                                                      motivo =descripdeta,
                                                                      total = valdescuento,
                                                                      fecha = datetime.now().date())
                                                        desc.save()
                                                        detalle = DetalleDescuento(descuento =desc,
                                                                                    rubro =rubro,
                                                                                    valor = valdescuento,
                                                                                    porcentaje = porcentajedescuento)
                                                        detalle.save()
                                                    if rubro.valor == 0:
                                                        rubro.cancelado=True
                                                        rubro.save()
                                                    ri = RubroInscripcion(rubro=rubro)
                                                    ri.save()

                                            # Matriculacion automatica en NIVEL PROPEDEUTICO
                                            if UTILIZA_NIVEL0_PROPEDEUTICO and not f.cleaned_data['extranjero'] and not f.cleaned_data['tienediscapacidad']and not f.cleaned_data['doblematricula']:
                                                if grupo.nivel_set.filter(periodo__tipo__id=TIPO_PERIODO_PROPEDEUTICO, cerrado=False).exists():
                                                    nivel = grupo.nivel_set.filter(periodo__tipo__id=TIPO_PERIODO_PROPEDEUTICO, cerrado=False)[:1].get()
                                                    inscripcion.matricular(nivel)
                                            elif (f.cleaned_data['extranjero'] or f.cleaned_data['tienediscapacidad']or f.cleaned_data['doblematricula']) and UTILIZA_NIVEL0_PROPEDEUTICO:
                                                if not 'CONGRESO' in grupo.carrera.nombre:
                                                    user.is_active = False
                                                    user.save()
                                                    if f.cleaned_data['extranjero'] or f.cleaned_data['tienediscapacidad'] and EMAIL_ACTIVE:
                                                        # inscripcion.notificacion_dobe(request.user)
                                                        # OCU 03-enero-2017 para indicar en correo tipo de notificacion
                                                        if f.cleaned_data['extranjero']:
                                                            tipo_notificacion='EXTRANJERO'

                                                        if f.cleaned_data['tienediscapacidad']:
                                                            tipo_notificacion='DISCAPACIDAD'

                                                        # inscripcion.notificacion_dobe(request.user)
                                                        # inscripcion.notificacion_dobe(request.user,tipo_notificacion)
                                                        # OCU 04-sep-2017
                                                        asunto='Se ha inscrito una persona'
                                                        inscripcion.notificacion_dobe(request.user,tipo_notificacion, asunto)


                                        # OCU 31-marzo-2016 realiza esto en el caso de inscripcion nueva
                                        if not inscripcion.doblematricula:
                                            if INSCRIPCION_CONDUCCION:
                                                requisitos = InscripcionConduccion(inscripcion = inscripcion,
                                                                                   fotos2 = f.cleaned_data['fotos2'],
                                                                                   acta = f.cleaned_data['acta'],
                                                                                   titulo = f.cleaned_data['titulo'],
                                                                                   licencia=f.cleaned_data['licencia'],
                                                                                   copia_cedula=f.cleaned_data['copia_cedula'],
                                                                                   votacion=f.cleaned_data['votacion'],
                                                                                   carnetsangre=f.cleaned_data['carnetsangre'],
                                                                                   ex_psicologico=f.cleaned_data['ex_psicologico'],
                                                                                   val_psicosometrica=f.cleaned_data['val_psicosometrica'],
                                                                                   val_medica=f.cleaned_data['val_medica'],
                                                                                   licienciatipoc=f.cleaned_data['licienciatipoc'],
                                                                                   originalrecord=f.cleaned_data['originalrecord'],
                                                                                   originalcontenido=f.cleaned_data['originalcontenido'],
                                                                                   certificado=f.cleaned_data['certificado'],
                                                                                   sabe_conducir=f.cleaned_data['sabe_conducir'],
                                                                                   tiene_licencia=f.cleaned_data['tiene_licencia'],
                                                                                   tipo_licencia=f.cleaned_data['tipo_licencia'],
                                                                                   tienediscapacidad=f.cleaned_data['tienediscapacidad'],
                                                                                   f_emision=f.cleaned_data['f_emision'],
                                                                                   puntos_licencia=f.cleaned_data['puntos_licencia'])
                                                requisitos.save()

                                                if 'soporte_ant' in request.FILES:
                                                    requisitos.soporte_ant=request.FILES['soporte_ant']
                                                    requisitos.save()

                                            else:
                                                documentos = DocumentosDeInscripcion(inscripcion=inscripcion,
                                                                                    titulo=f.cleaned_data['titulo'],
                                                                                    acta=f.cleaned_data['acta'],
                                                                                    cedula=f.cleaned_data['cedula2'],
                                                                                    votacion=f.cleaned_data['votacion'],
                                                                                    actaconv=f.cleaned_data['actaconv'],
                                                                                    partida_nac=f.cleaned_data['partida_nac'],
                                                                                    fotos=f.cleaned_data['fotos'],
                                                                                    actafirmada=f.cleaned_data['actafirmada'])
                                                documentos.save()

                                        g = Group.objects.get(pk=ALUMNOS_GROUP_ID)
                                        g.user_set.add(user)
                                        g.save()
                                        p=None
                                        if PreInscripcion.objects.filter(cedula = inscripcion.persona.cedula,tipodoc='c').exists():
                                            p = PreInscripcion.objects.filter(cedula = inscripcion.persona.cedula,tipodoc='c')[:1].get()
                                        if PreInscripcion.objects.filter(cedula = inscripcion.persona.pasaporte, tipodoc='p').exists():
                                            p = PreInscripcion.objects.filter(cedula = inscripcion.persona.pasaporte,tipodoc='p')[:1].get()
                                        if p:
                                            p.inscrito=True
                                            p.save()
                                            if inscripcion.carrera.nombre == 'CONGRESO DE PEDAGOGIA':
                                                if inscripcion.matricula():
                                                    matins =inscripcion.matricula()
                                                    if p.valor:
                                                        if RubroMatricula.objects.filter(matricula=matins).exists():
                                                            rubromatins = RubroMatricula.objects.filter(matricula=matins)[:1].get()
                                                            rubromatins.rubro.valor = p.valor
                                                            rubromatins.rubro.save()

                                            if DatosPersonaCongresoIns.objects.filter(preinscripcion=p,grupo=grupo).exists():
                                                for dpi in  DatosPersonaCongresoIns.objects.filter(preinscripcion=p,grupo=grupo):
                                                    dpi.inscripcion = inscripcion
                                                    dpi.save()
                                        if f.cleaned_data['enviarcorreo'] and EMAIL_ACTIVE:
                                            inscripcion.correo_congreo(ig.grupo)

                                        if not INSCRIPCION_CONDUCCION:
                                            if EMAIL_ACTIVE and (inscripcion.documentos_entregados().cedula or inscripcion.documentos_entregados().titulo or inscripcion.documentos_entregados().votacion or inscripcion.documentos_entregados().fotos or inscripcion.documentos_entregados().acta or inscripcion.documentos_entregados().actaconv or inscripcion.documentos_entregados().partida_nac):
                                                inscripcion.correo_entregadocumentos(inscripcion.documentos_entregados(),request.user)
                                                documento=True

                                    else:
                                        user.delete()
                                        return HttpResponseRedirect("/inscripciones?action=add&error=1")

                                    if request.POST['redireccion']=='actividades':
                                        return HttpResponseRedirect("/inscripciones?action=actividades&id="+str(inscripcion.id))

                                    if inscripcion.persona.cedula:
                                        if  documento and not INSCRIPCION_CONDUCCION :
                                            return HttpResponseRedirect("/inscripciones?s="+str(inscripcion.persona.cedula)+"&doc="+str(documento)+"&ins="+str(inscripcion.id))
                                        else:
                                            return HttpResponseRedirect("/inscripciones?s="+str(inscripcion.persona.cedula))
                                    else:
                                         if documento and not INSCRIPCION_CONDUCCION:
                                            return HttpResponseRedirect("/inscripciones?s="+str(inscripcion.persona.pasaporte))
                                         else:
                                            return HttpResponseRedirect("/inscripciones?s="+str(inscripcion.persona.pasaporte)+"&doc="+str(documento)+"&ins="+str(inscripcion.id))
                                else:
                                    return HttpResponseRedirect("/inscripciones?action=add&error1="+(str(f._errors)))
                            else:
                                f = InscripcionCextForm(request.POST)
                                if f.is_valid():
                                    sid = transaction.savepoint()
                                    try:
                                        if not Persona.objects.filter(cedula=f.cleaned_data['cedula']).exists():
                                            persona = Persona(nombres=f.cleaned_data['nombres'],
                                                              apellido1=f.cleaned_data['apellido1'],
                                                              apellido2=f.cleaned_data['apellido2'],
                                                              cedula=f.cleaned_data['cedula'],
                                                              nacimiento=f.cleaned_data['nacimiento'],
                                                              provincia=f.cleaned_data['provincia'],
                                                              canton=f.cleaned_data['canton'],
                                                              sexo=f.cleaned_data['sexo'],
                                                              direccion=f.cleaned_data['direccion'],
                                                              direccion2=f.cleaned_data['direccion2'],
                                                              sector = f.cleaned_data['sector'],
                                                              ciudad = f.cleaned_data['ciudad'],
                                                              telefono=f.cleaned_data['telefono'],
                                                              telefono_conv=f.cleaned_data['telefono_conv'],
                                                              email=f.cleaned_data['email'],
                                                              sangre=f.cleaned_data['sangre'],
                                                              parroquia=f.cleaned_data['parroquia'])
                                            persona.save()
                                        else:
                                            persona = Persona.objects.filter(cedula=f.cleaned_data['cedula'])[:1].get()

                                        if not Inscripcion.objects.filter(persona=persona).exists():
                                            carrera = Carrera.objects.all()[:1].get()
                                            modalidad = Modalidad.objects.all()[:1].get()
                                            sesion = Sesion.objects.all()[:1].get()
                                            especialidad = Especialidad.objects.all()[:1].get()
                                            inscripcion = Inscripcion(persona=persona,
                                                                      fecha=datetime.now(),
                                                                      carrera=carrera,
                                                                      modalidad=modalidad,
                                                                      sesion=sesion,
                                                                      especialidad=especialidad,
                                                                      tienediscapacidad=False)
                                            inscripcion.save()
                                    except Exception as e:
                                        transaction.savepoint_rollback(sid)
                                        return HttpResponseRedirect("/inscripciones?action=add&error1="+str(e))

                                    if DEFAULT_PASSWORD=='itb':
                                        try:
                                            datos = requests.get('https://crm.itb.edu.ec/api',
                                                params={'a': 'actualizains', 'identificacion': inscripcion.persona.cedula if inscripcion.persona.cedula else inscripcion.persona.pasaporte},verify=False)
                                            if datos.status_code == 200:
                                                pass
                                        except:
                                            pass


                                        try:
                                            datos = requests.get('https://crm.itb.edu.ec/api',
                                                params={'a': 'usuariogestor', 'identificacion': inscripcion.persona.cedula if inscripcion.persona.cedula else inscripcion.persona.pasaporte},verify=False)
                                            if datos.status_code == 200:
                                                datos=datos.json()
                                                if int(datos['idgestor'])>0:
                                                    persona = Persona.objects.get(id=int(datos['idgestor']))
                                                    inscripcion.user=persona.usuario
                                                    inscripcion.save()
                                        except:
                                            pass



                                    transaction.savepoint_commit(sid)
                                    return HttpResponseRedirect("/inscripciones?s="+f.cleaned_data['cedula'])

                                return HttpResponseRedirect("/inscripciones?action=add")
                        except Exception as e:
                            return HttpResponseRedirect("/inscripciones?action=add&error1="+str(e))
                elif action=='addkit':
                    try:
                        i = Inscripcion.objects.get(pk=request.POST['id'])
                        kit = KitCongreso(inscripcion=i,
                                          observacion=request.POST['obs'],
                                          fecha=datetime.now().date(),
                                          usuario=request.user,
                                          valor = Decimal(i.kit_congreso_valor()))
                        kit.save()
                        #Obtain client ip address
                        client_address = ip_client_address(request)

                        # Log de ADICIONAR INSCRIPCION
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(kit).pk,
                            object_id       = kit.id,
                            object_repr     = force_str(kit),
                            action_flag     = ADDITION,
                            change_message  = 'Entrega de Kit (' + client_address + ')' )

                        return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                    except Exception as ex:
                        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

                elif action=='adduniformemunicipio':

                    try:
                        print(356)
                        # print(34)
                        # print(request.POST)
                        # if Nivel.objects.filter(pk=request.POST['nivel']).exists():
                        #     print(2)
                        #     nivel=Nivel.objects.get(pk=request.POST['nivel'])
                        #     i = Inscripcion.objects.get(pk=request.POST['id'])
                        if Matricula.objects.filter(pk=request.POST['nivel']).exists():
                            matricula = Matricula.objects.filter(pk=request.POST['nivel'])[:1].get()

                        if not EntregaUniforme.objects.filter(matricula=matricula).exists():
                            uniforme=EntregaUniforme(matricula=matricula,uniforme=True, usuario=request.user,fecha=datetime.now().date(),fecharep=datetime.now(), observacion=request.POST['obs'])
                            uniforme.save()

                            #Obtain client ip address
                            client_address = ip_client_address(request)

                            # Log de ADICIONAR INSCRIPCION
                            LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(uniforme).pk,
                                object_id       = uniforme.id,
                                object_repr     = force_str(uniforme),
                                action_flag     = ADDITION,
                                change_message  = 'Entrega de Uniforme (' + client_address + ')' )

                            return HttpResponse(json.dumps({"result":"ok"}), content_type="application/json")
                        else:
                            return HttpResponse(json.dumps({"result":"bad"}), content_type="application/json")
                    except Exception as ex:
                        print(ex)
                        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

                elif action=='addentregajuguetecanasta':
                    try:
                        i = Inscripcion.objects.get(pk=request.POST['id'])
                        tipoentrega= TipoEntrega.objects.get(pk=request.POST['tipoentrega'])
                        juguetecanasta = EntregaJugueteCanasta(inscripcion=i,
                                          tipoentrega=tipoentrega,
                                          observacion=request.POST['obs'],
                                          fecha=datetime.now().date(),
                                          usuario=request.user
                                          )
                        juguetecanasta.save()
                        i.entregajuguetecanastas=True
                        i.save()
                        #Obtain client ip address
                        client_address = ip_client_address(request)

                        # Log de ADICIONAR INSCRIPCION
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(juguetecanasta).pk,
                            object_id       = juguetecanasta.id,
                            object_repr     = force_str(juguetecanasta),
                            action_flag     = ADDITION,
                            change_message  = 'Entrega de Jueguete o Canasta (' + client_address + ')' )

                        return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                    except Exception as ex:
                        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

                elif action == 'entregacarnet':
                    result={}
                    try:
                        if Inscripcion.objects.filter(pk=request.POST['idinsc']).exists():
                            inscripcion=Inscripcion.objects.filter(pk=request.POST['idinsc'])[:1].get()
                            inscripcion.carnet= not inscripcion.carnet
                            inscripcion.save()
                            client_address = ip_client_address(request)
                            mensaje = 'Editados datos carnet'
                            LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(inscripcion).pk,
                                object_id       = inscripcion.id,
                                object_repr     = force_str(inscripcion),
                                action_flag     = CHANGE,
                                change_message  = mensaje+' (' + client_address + ')' )

                            result['result']  = "ok"
                            return HttpResponse(json.dumps(result), content_type="application/json")
                    except Exception as e:
                        result['result']  = str(e)
                        return HttpResponse(json.dumps(result), content_type="application/json")

                elif action =='addrecibetit':
                    try:
                        inscripcion = Inscripcion.objects.get(pk=request.POST['id'])
                        inscripcion.recibetit = request.POST['recibe']
                        inscripcion.fechaentregatitulo = datetime.now().date()
                        inscripcion.usuarioentrega = request.user
                        inscripcion.save()
                        client_address = ip_client_address(request)

                        # Log de ADICIONAR INSCRIPCION
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(inscripcion).pk,
                            object_id       = inscripcion.id,
                            object_repr     = force_str(inscripcion),
                            action_flag     = ADDITION,
                            change_message  = 'Entregado Titulo (' + client_address + ')' )
                        return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                    except Exception as e:
                        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

                elif action == 'addhorasteleclinica':
                    try:
                        i = Inscripcion.objects.get(pk=request.POST['id'])
                        if TituloExamenCondu.objects.filter(asignatura__id=request.POST['asignatura']).exists():
                            evaluacion = TituloExamenCondu.objects.filter(asignatura__id=request.POST['asignatura'])[:1].get()
                            if not InscripcionExamen.objects.filter(inscripcion=i,tituloexamencondu=evaluacion).exists():
                                inscripcionexamen = InscripcionExamen(inscripcion=i,puntaje=Decimal(request.POST['horas']),
                                                                      tituloexamencondu=evaluacion,fecha=datetime.now(),
                                                                      valida=True,finalizado=True)
                                inscripcionexamen.save()

                                # Obtain client ip address
                                client_address = ip_client_address(request)
                                # Log de ADICIONAR HORAS DE TELECLINICA
                                LogEntry.objects.log_action(
                                    user_id=request.user.pk,
                                    content_type_id=ContentType.objects.get_for_model(inscripcionexamen).pk,
                                    object_id=inscripcionexamen.id,
                                    object_repr=force_str(inscripcionexamen),
                                    action_flag=ADDITION,
                                    change_message='Horas Teleclinica desde Inscripciones (' + client_address + ')')

                                return HttpResponse(json.dumps({"result": "ok"}), content_type="application/json")
                            else:
                                return HttpResponse(json.dumps({"result": "bad"}), content_type="application/json")
                    except Exception as ex:
                        print(ex)
                        return HttpResponse(json.dumps({"result": "bad"}), content_type="application/json")


                elif action =='consulta_canton':
                    result =  {}
                    try:
                        result  = {"canton": [{"id": x.id, "nombre": x.nombre } for x in Canton.objects.filter(provincia__id=request.POST['id']).order_by('nombre')]}
                        result['result']  = 'ok'
                        return HttpResponse(json.dumps(result), content_type="application/json")
                    except Exception as e:
                        result['result']  = 'bad'
                        return HttpResponse(json.dumps(result), content_type="application/json")

                elif action =='consulta_parroquia':
                    result =  {}
                    try:
                        result  = {"parroquia": [{"id": x.id, "nombre": x.nombre } for x in Parroquia.objects.filter(canton__id=request.POST['id']).order_by('nombre')]}
                        result['result']  = 'ok'
                        return HttpResponse(json.dumps(result), content_type="application/json")
                    except Exception as e:
                            result['result']  = 'bad'
                            return HttpResponse(json.dumps(result), content_type="application/json")

                elif action =='consulta_sector':
                    result =  {}
                    try:
                        result  = {"sector": [{"id": x.id, "nombre": x.nombre } for x in Sector.objects.filter(parroquia__id=request.POST['id']).order_by('nombre')]}
                        result['result']  = 'ok'
                        return HttpResponse(json.dumps(result), content_type="application/json")
                    except Exception as e:
                        result['result']  = 'bad'
                        return HttpResponse(json.dumps(result), content_type="application/json")

                elif action == 'addtitulo':
                    try:
                        inscripcion = Inscripcion.objects.get(pk=request.POST['insc_id'])
                        f = RecibirTituloForm(request.POST, request.FILES)
                        if f.is_valid():
                            inscripcion.fechatitulo=f.cleaned_data['fechatitulo']
                            if 'archivo' in request.FILES:
                                inscripcion.titulo = request.FILES['archivo']
                            inscripcion.save()
                            client_address = ip_client_address(request)

                        # Log de ADICIONAR INSCRIPCION
                            LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(inscripcion).pk,
                                object_id       = inscripcion.id,
                                object_repr     = force_str(inscripcion),
                                action_flag     = ADDITION,
                                change_message  = 'Recibido Titulo (' + client_address + ')' )
                            return HttpResponseRedirect("/inscripciones?s="+str(inscripcion.persona.cedula))
                        else:
                            return HttpResponseRedirect("/inscripciones?s="+str(inscripcion.persona.cedula)+"&info=Formato no Aceptado")
                    except Exception as ex:
                        return HttpResponseRedirect("/inscripciones?s="+str(inscripcion.persona.cedula)+"&info="+str(ex))

                elif action=='addvendedor':
                    try:
                        if request.POST['opcion'] == '1':
                            i = Inscripcion.objects.get(pk=request.POST['id'])
                            vendedor = Vendedor.objects.get(pk=request.POST['vendedor'])
                            insc_vend = InscripcionVendedor(inscripcion=i,fecha=datetime.now().date(),vendedor=vendedor)
                            insc_vend.save()
                            #Obtain client ip address
                            client_address = ip_client_address(request)

                            # Log de ADICIONAR INSCRIPCION
                            LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(insc_vend).pk,
                                object_id       = insc_vend.id,
                                object_repr     = force_str(insc_vend),
                                action_flag     = ADDITION,
                                change_message  = 'Agregado Vendedor (' + client_address + ')' )
                            datos = {"result": "ok","op":1}

                            #return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                            return HttpResponse(json.dumps(datos),content_type="application/json")
                        else:
                            inscripcion = Inscripcion.objects.filter(pk=request.POST['id'])[:1].get()
                            vendedor = Vendedor.objects.filter(pk=request.POST['vendedor'])[:1].get()
                            inscripvendedor = InscripcionVendedor.objects.filter(inscripcion=inscripcion)[:1].get()
                            inscripvendedor.vendedor=vendedor
                            inscripvendedor.save()

                            client_address = ip_client_address(request)
                            # Log de Modificar Vendedor
                            LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(inscripvendedor).pk,
                                object_id       = inscripvendedor.id,
                                object_repr     = force_str(inscripvendedor),
                                action_flag     = CHANGE,
                                change_message  = 'Vendedor de Inscripcion Cambiado (' + client_address + ')' )
                            datos = {"result": "ok","op":2}
                            #return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                            return HttpResponse(json.dumps(datos),content_type="application/json")
                    except Exception as ex:
                        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

                elif action=='addpromocion':
                    try:
                        i = Inscripcion.objects.get(pk=request.POST['id'])
                        promocion = Promocion.objects.get(pk=request.POST['promocion'])
                        i.promocion=promocion
                        i.save()
                        #Obtain client ip address
                        client_address = ip_client_address(request)

                        # Log de ADICIONAR PROMOCION
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(i).pk,
                            object_id       = i.id,
                            object_repr     = force_str(i),
                            action_flag     = ADDITION,
                            change_message  = 'Se agrego Promocion (' + client_address + ')' )
                        return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                    except Exception as ex:
                        return HttpResponse(json.dumps({"result":"bad"+' '+str(ex)}),content_type="application/json")

                elif action=='addcofia':
                    try:
                        i = Inscripcion.objects.get(pk=request.POST['id'])
                        cofia =  AsistenciaCofia(inscripcion=i,
                                          observacion=request.POST['obs'],
                                          fecha=datetime.now().date(),
                                          usuario=request.user)
                        cofia.save()
                        #Obtain client ip address
                        client_address = ip_client_address(request)

                        # Log de ADICIONAR COFIA
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(cofia).pk,
                            object_id       = cofia.id,
                            object_repr     = force_str(cofia),
                            action_flag     = ADDITION,
                            change_message  = 'Registrada Asistencia Cofia(' + client_address + ')' )

                        return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                    except Exception as ex:
                        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

                elif action=='addplagio':
                    try:
                        inscripcion = Inscripcion.objects.get(pk=request.POST['idInscripcion'])
                        observacion = request.POST['observacion']
                        factura = Factura.objects.get(pk=request.POST['factura'])

                        if RegistroPlagioTarjetas.objects.filter(pk=request.POST['id']).exists():
                            mensaje='Change Fraude con tarjeta'
                            plagio = RegistroPlagioTarjetas.objects.filter(pk=request.POST['id'])[:1].get()
                            plagio.observacionplagio = observacion.strip()
                            plagio.factura = factura
                            plagio.fecha = datetime.now()
                            plagio.save()
                        else:
                            mensaje = 'Add Fraude con tarjeta'
                            rubro = Rubro(fecha=datetime.now().date(),
                                          valor=float(request.POST['valorplagio']),
                                          inscripcion=inscripcion, cancelado=False,
                                          fechavence=datetime.now().date(),
                                          editable=False)
                            rubro.save()

                            rubrootro = RubroOtro(rubro=rubro,
                                                  tipo_id=TIPO_OTRO_FRAUDE,
                                                  descripcion='Cargo por reversos de pagos no confirmados con tarjeta')
                            rubrootro.save()

                            plagio = RegistroPlagioTarjetas(inscripcion=inscripcion,
                                                            observacionplagio=observacion,
                                                            plagioactivo=True,
                                                            usuario=request.user,
                                                            fecha=datetime.now(),
                                                            factura=factura,
                                                            rubro=rubro)
                            plagio.save()
                            inscripcion.plagiotarjeta = True
                            inscripcion.save()

                            if EMAIL_ACTIVE:
                                tipo = TipoIncidencia.objects.get(pk=25)
                                hoy = datetime.now().today()
                                contenido = 'REGISTRO DE FRAUDE DE TARJETAS'
                                send_html_mail(contenido, "emails/plagio_notificacion.html", {'fecha':hoy, 'contenido':contenido, 'usuario':request.user, 'estudiante': inscripcion.persona.nombre_completo_inverso()}, tipo.correo.split(","))

                        if "soportesfraude" in request.FILES:
                            plagio.soporte = request.FILES["soportesfraude"]
                            plagio.save()

                        #Obtain client ip address
                        client_address = ip_client_address(request)
                        # Log de ADICIONAR Fraude con tarjeta
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(plagio).pk,
                            object_id       = plagio.id,
                            object_repr     = force_str(plagio),
                            action_flag     = ADDITION,
                            change_message  = mensaje + ' (' + elimina_tildes(inscripcion.persona.nombre_completo_inverso()) + client_address + ')' )

                        return HttpResponseRedirect("/inscripciones?action=versoportefraude&id="+str(inscripcion.id))
                    except Exception as ex:
                        return HttpResponseRedirect("/inscripciones?action=versoportefraude&id="+str(inscripcion.id)+"&error="+str(ex))

                elif action == 'verifica_edicion_fraude':
                    try:
                        fraude = RegistroPlagioTarjetas.objects.get(pk=request.POST['id'])
                        habilitaFacturas = True
                        habilitaValorRubro = True
                        if NotaCreditoInstitucion.objects.filter(factura=fraude.factura).exists():
                            habilitaFacturas = False
                        if fraude.rubro:
                            if fraude.rubro.cancelado:
                                habilitaValorRubro = False
                        facturasNC = NotaCreditoInstitucion.objects.filter(inscripcion=fraude.inscripcion).values('factura')
                        facturasFiltradas = Factura.objects.filter(pagos__rubro__inscripcion=fraude.inscripcion).exclude(id__in=facturasNC).order_by('-fecha').distinct()
                        if fraude.factura != None:
                            facturaFraude = Factura.objects.filter(id=fraude.factura.id).distinct()
                            filtroFacturas = facturasFiltradas | facturaFraude
                        else:
                            facturasNC2 = NotaCreditoInstitucion.objects.filter(inscripcion=fraude.inscripcion).values('factura')
                            facturasFiltradas2 = Factura.objects.filter(pagos__rubro__inscripcion=fraude.inscripcion, id__in=facturasNC2).order_by('-fecha').distinct()
                            filtroFacturas = facturasFiltradas2

                        facturas = [{'id':x.id, 'value':str(x.fecha)+' | '+ str(x.numero)+' ('+str(x.total)+')'} for x in filtroFacturas]
                        return HttpResponse(json.dumps({'result': 'ok', 'facturas': facturas, 'habilitaFacturas': habilitaFacturas, 'habilitaValorRubro': habilitaValorRubro}), content_type="application/json")
                    except Exception as ex:
                        return HttpResponse(json.dumps({'result': 'bad', 'mensaje': str(ex)}), content_type="application/json")

                elif action == 'obtener_facturas_fraude':
                        try:
                            inscripcion = Inscripcion.objects.get(pk=request.POST['id'])
                            registroplagio = RegistroPlagioTarjetas.objects.filter(inscripcion=request.POST['id']).exclude(factura=None)
                            facturasFiltradas = Factura.objects.filter(pagos__rubro__inscripcion=inscripcion).order_by('-fecha').exclude(id__in=registroplagio.values('factura').distinct()).distinct()
                            facturas = [{'id':x.id, 'value':str(x.fecha)+' | '+ str(x.numero)+' ('+str(x.total)+')'} for x in facturasFiltradas]
                            return HttpResponse(json.dumps({'result': 'ok', 'facturas': facturas}), content_type="application/json")
                        except Exception as ex:
                            return HttpResponse(json.dumps({'result': 'bad', 'mensaje': str(ex)}), content_type="application/json")

                elif action =='editar_observacion_si_tiene_errores':
                    try:
                        pass
                    except Exception as ex:
                        print(ex)
                elif action=='addsoporte':
                    mensaje=''
                    try:
                        i = Inscripcion.objects.get(pk=request.POST['id'])
                        if RegistroPlagioTarjetas.objects.filter(pk=request.POST['regid']).exists():
                            plagio=RegistroPlagioTarjetas.objects.filter(pk=request.POST['regid'])[:1].get()
                            plagio.observacionplagio=elimina_tildes(request.POST['obs'])
                            plagio.usuario= request.user
                            plagio.fecha=datetime.now()

                        if "soporte" in request.FILES:
                            plagio.soporte = request.FILES["soporte"]
                            plagio.save()

                            mensaje='Edicion Soporte Fraude con tarjeta'

                        #Obtain client ip address
                        client_address = ip_client_address(request)
                        # Log de ADICIONAR Fraude con tarjeta
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(plagio).pk,
                            object_id       = plagio.id,
                            object_repr     = force_str(plagio),
                            action_flag     = ADDITION,
                            change_message  = mensaje + ' (' + elimina_tildes(i.persona.nombre_completo_inverso()) + client_address + ')' )

                        return HttpResponseRedirect("/inscripciones?action=versoportefraude&id="+str(inscripcion.id))
                    except Exception as ex:
                        return HttpResponseRedirect("/inscripciones?action=versoportefraude&id="+str(inscripcion.id)+"&error="+str(ex))


                elif action=='quitarplagio':
                    try:
                        i = Inscripcion.objects.get(pk=request.POST['id'])
                        i.plagiotarjeta=False

                        if RegistroPlagioTarjetas.objects.filter(inscripcion=i,plagioactivo=True).exists():
                            obsquitarplagio=RegistroPlagioTarjetas.objects.filter(inscripcion=i,plagioactivo=True)[:1].get()
                            obsquitarplagio.plagioactivo=False
                            obsquitarplagio.observacionquitaplagio=request.POST['obs']
                            obsquitarplagio.usrquitaplagio=request.user
                            obsquitarplagio.fechaquitaplagio=datetime.now()
                            obsquitarplagio.save()
                        else:
                            obsquitarplagio=RegistroPlagioTarjetas(inscripcion=i,plagioactivo=False,observacionquitaplagio=request.POST['obs'],
                                                                   usrquitaplagio = request.user,fechaquitaplagio=datetime.now())
                            obsquitarplagio.save()
                        i.save()

                        #Obtain client ip address
                        client_address = ip_client_address(request)
                        # Log de ADICIONAR Quitar Plagio con Tarjeta
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(obsquitarplagio).pk,
                            object_id       = obsquitarplagio.id,
                            object_repr     = force_str(obsquitarplagio),
                            action_flag     = ADDITION,
                            change_message  = 'Registro Quitar Fraude con Tarjeta (' + elimina_tildes(i.persona.nombre_completo_inverso()) + client_address + ')' )
                        return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")

                    except Exception as ex:
                        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

                elif action=='buscar':
                    estudiante = ''
                    cedula=request.POST['cedula']
                    documentos=[]

                    asp=False
                    if cedula:

                        if request.user.has_perm('sga.add_referidos') :
                            valida=False
                        else:
                            valida=True

                        if valida :
                            datosCrm = requests.post('https://crm.itb.edu.ec/api',{'a': 'verificarprospecto1','identificacion': str(cedula)},verify=False)

                            if datosCrm.status_code == 200:
                                datosCrm=datosCrm.json()
                                if datosCrm['result']=='ok':
                                    pass
                                else:
                                    return HttpResponse(json.dumps({"result":"bad3","mensaje":"Se encuentra registrado en crm presencial"}),content_type="application/json")

                            datoscrmonline = requests.get('https://sgaonline.itb.edu.ec/funciones',params={'a': 'verificarprospecto1','identificacion': str(cedula)},verify=False)

                            if datoscrmonline.status_code == 200:
                                datoscrmonline=datoscrmonline.json()
                                if datoscrmonline['result']=='ok':
                                    pass
                                else:
                                    return HttpResponse(json.dumps({"result":"bad3","mensaje":"Se encuentra registrado en crm online"}),content_type="application/json")


                            datoscrmonlinereferido = requests.get('https://sgaonline.itb.edu.ec/funciones',params={'a': 'verificareferido1','identificacion': str(cedula)},verify=False)

                            if datoscrmonlinereferido.status_code == 200:
                                datoscrmonlinereferido=datoscrmonlinereferido.json()
                                if datoscrmonlinereferido['result']=='ok':
                                    pass
                                else:
                                    return HttpResponse(json.dumps({"result":"bad3","mensaje":"Se encuentra registrado en referidos online"}),content_type="application/json")

                            if ReferidosInscripcion.objects.filter(cedula=request.POST['cedula']).exists():

                                rf = ReferidosInscripcion.objects.get(cedula=request.POST['cedula'])
                                valida = False

                                if Inscripcion.objects.filter(persona__cedula=rf.cedula,persona__usuario__is_active=False).exclude(
                                    persona__cedula=None).exclude(persona__cedula='').exists():



                                    valida=True

                                elif Inscripcion.objects.filter(persona__pasaporte=rf.cedula,persona__usuario__is_active=False).exclude(
                                        persona__pasaporte=None).exclude(persona__pasaporte='').exists():



                                    valida = True

                                if valida==True:
                                    return HttpResponse(json.dumps({"result":"bad3","mensaje":"Se encuentra registrado en referidos"}),content_type="application/json")

                            # OCastillo 20-09-2018 validacion adicional si persona existe en el modulo aspirantes
                            if InscripcionAspirantes.objects.filter(cedula=request.POST['cedula'],activo=True).exists():
                                inscripaspirantes = InscripcionAspirantes.objects.filter(cedula=request.POST['cedula'],activo=True).order_by('-id')[:1].get()
                                if inscripaspirantes.fueratiempo()<3:
                                    asp=True
                                if inscripaspirantes.usuario != request.user and asp:
                                    return HttpResponse(json.dumps({"result":"bad2","estudiante": str(estudiante)}),content_type="application/json")
                            # OCastillo 02-10-2015 se incluye validacion que excluya Congresos y Seminarios
                            elif Inscripcion.objects.filter(persona__cedula=request.POST['cedula']).exclude(carrera__in=CARRERAS_ID_EXCLUIDAS_INEC).exists():
                                    for i in Inscripcion.objects.filter(persona__cedula=request.POST['cedula']).exclude(carrera__in=CARRERAS_ID_EXCLUIDAS_INEC):
                                        estudiante = estudiante + ' - ' +i.carrera.nombre

                                    # Para presentar los documentos que hay en secretaria OCU 31-mar-2016
                                    d = DocumentosDeInscripcion.objects.filter(inscripcion__persona__cedula=request.POST['cedula'])[:1].get()
                                    if d.titulo:
                                        documentos.append('titulo')
                                    if d.acta:
                                        documentos.append('acta')
                                    if d.cedula:
                                        documentos.append('cedula')
                                    if d.votacion:
                                        documentos.append('votacion')
                                    if d.fotos:
                                        documentos.append('fotos')
                                    if d.actaconv:
                                        documentos.append('actaconv')
                                    if d.partida_nac:
                                        documentos.append('partida_nac')

                                    return HttpResponse(json.dumps({"result":"bad","estudiante": str(estudiante),"documentos":documentos}),content_type="application/json")

                            else:
                                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                        else:
                             return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")

                elif action=='buscarpas':
                    estudiante = ''
                    pasaporte=  request.POST['pasaporte']
                    pasaporte = pasaporte.upper( )
                    documentos=[]

                    asp=False
                    if pasaporte:
                         # OCastillo 20-09-2018 validacion adicional si persona existe en el modulo aspirantes
                        if InscripcionAspirantes.objects.filter(pasaporte=request.POST['pasaporte'],activo=True).exists():
                            inscripaspirantes= InscripcionAspirantes.objects.filter(pasaporte=request.POST['pasaporte'],activo=True).order_by('-id')[:1].get()
                            if inscripaspirantes.fueratiempo()<3:
                                asp=True
                            if inscripaspirantes.usuario != request.user  and asp:
                                return HttpResponse(json.dumps({"result":"bad2","estudiante": str(estudiante)}),content_type="application/json")
                        # OCastillo 05-10-2015 para pasaporte se incluye validacion que excluya Congresos y Seminarios
                        elif Inscripcion.objects.filter(persona__pasaporte=pasaporte).exists():
                            for i in Inscripcion.objects.filter(persona__pasaporte=pasaporte).exclude(carrera__in=CARRERAS_ID_EXCLUIDAS_INEC):
                                estudiante = estudiante + ' - ' +i.carrera.nombre

                            # Para presentar los documentos que hay en secretaria OCU 31-mar-2016
                            d = DocumentosDeInscripcion.objects.filter(inscripcion__persona__pasaporte=request.POST['pasaporte'])[:1].get()
                            if d.titulo:
                                documentos.append('titulo')
                            if d.acta:
                                documentos.append('acta')
                            if d.cedula:
                                documentos.append('cedula')
                            if d.votacion:
                                documentos.append('votacion')
                            if d.fotos:
                                documentos.append('fotos')
                            if d.actaconv:
                                documentos.append('actaconv')
                            if d.partida_nac:
                                documentos.append('partida_nac')

                            return HttpResponse(json.dumps({"result":"bad","estudiante": str(estudiante),"documentos":documentos}),content_type="application/json")

                        else:
                            return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")

                elif action=='buscarfechanac':
                    # OCastillo 01-abril-2016 para sacar edad de inscrito
                    anio=''
                    mes=''
                    anio_act=''
                    mes_act=''

                    f_nacido=request.POST['nacimiento']
                    fn=(convertir_fecha(f_nacido))
                    anio = fn.year
                    mes = fn.month
                    anio_act=hoy.year
                    mes_act=hoy.month

                    if f_nacido:
                       anios=(anio_act-anio)
                       if mes_act<mes:
                           anios=anios-1

                    # OCU 15-05-2017 validacion de edad mayor e igual a 17 y menor e igual a 75
                    if  anios >= ANIO_PARA_INSCRIPCION and anios <=75:
                        return HttpResponse(json.dumps({"result":"ok","anios":anios}),content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({"result":"bad","anios":anios,"meses":mes}),content_type="application/json")


                elif action=='buscafgrupo':
                    # OCastillo 04-abril-2016 para sacar verificar que inscrito sea mayor de edad para escuela de conduccion
                    anio=0
                    mes=0
                    anio_gr=0
                    mes_gr=0
                    f_grupo=0

                    f_nacido=request.POST['nacimiento']
                    fe =  (convertir_fecha(f_nacido))
                    anio =fe.year
                    mes = fe.month

                    grupo=Grupo.objects.filter(pk=request.POST['grupo']).get()

                    anio_gr=grupo.inicio.year
                    mes_gr=grupo.inicio.month

                    if f_nacido:
                       anios=(anio_gr-anio)
                       if mes_gr<mes:
                           anios=anios-1
                       #     return HttpResponse(json.dumps({"result":"bad","anios":anios,"meses":mes}),content_type="application/json")
                       # else:
                       #     return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")


                    if  anios >=18 :
                        return HttpResponse(json.dumps({"result":"ok","anios":anios}),content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({"result":"bad","anios":anios,"meses":mes}),content_type="application/json")

                elif action=='buscaemision':
                    # OCastillo 16-marzo-2018 para obtener fecha emision licencia
                    anio=0
                    mes=0
                    anio_gr=0
                    mes_gr=0
                    f_grupo=0
                    anios=0

                    f_emision=request.POST['emision']
                    fe =  (convertir_fecha(f_emision))
                    anio =fe.year
                    mes = fe.month

                    anio_act=hoy.year
                    mes_act=hoy.month


                    if f_emision:
                       anios=(anio_act-anio)
                       if mes_act<mes:
                           anios=anios-1

                    if  anios >=2 :
                        return HttpResponse(json.dumps({"result":"ok","anios":anios}),content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({"result":"bad","anios":anios}),content_type="application/json")

                elif action=='datosasuntos':
                    try:

                        inscripcion = Inscripcion.objects.get(id=int(request.POST['id']))
                        inscripcion.persona.telefono=request.POST['telefono']
                        inscripcion.persona.telefono_conv=request.POST['telefono_conv']
                        inscripcion.persona.email=str(request.POST['email']).lower()
                        inscripcion.persona.email1=str(request.POST['email1']).lower()
                        inscripcion.persona.email2=str(request.POST['email2']).lower()
                        inscripcion.observacion=request.POST['observacion']
                        inscripcion.save()

                        inscripcion.persona.save()
                        return HttpResponseRedirect("/inscripciones?s="+str(inscripcion.persona.nombre_completo_inverso()))
                    except Exception as ex:
                        return HttpResponseRedirect("/inscripciones?action=datos&id="+str(inscripcion.id)+"&error=1")

                elif action=='edit':
                    try:
                        acta=False
                        cedula=False
                        fotos = False
                        titulo = False
                        votacion = False
                        actaconv = False
                        partidanacimiento = False
                        documento2=False
                        actafirmada=False

                        inscripcion = Inscripcion.objects.get(pk=request.POST['id'])
                        initial = model_to_dict(inscripcion)
                        initial.update(model_to_dict(inscripcion.persona))
                        bandera=True
                        if 'graduado' in request.POST:
                            bandera=False
                            f = InscripcionGraduadosForm(request.POST, initial=initial)
                        else:
                            f = InscripcionForm(request.POST, initial=initial)

                        try:
                            if f.is_valid() and bandera:
                                # inscripcion.fecha=f.cleaned_data['fecha']
                                inscripcion.carrera_id=f.cleaned_data['carrera']
                                inscripcion.modalidad_id=f.cleaned_data['modalidad']
                                inscripcion.sesion_id=f.cleaned_data['sesion']
                                # inscripcion.colegio=f.cleaned_data['colegio']
                                inscripcion.especialidad_id=f.cleaned_data['especialidad']
                                inscripcion.anuncio_id=f.cleaned_data['anuncio']
                                inscripcion.identificador=f.cleaned_data['identificador']
                                inscripcion.tienediscapacidad=f.cleaned_data['tienediscapacidad']
                                inscripcion.observacion=f.cleaned_data['observacion']
                                # inscripcion.estcolegio = f.cleaned_data['estcolegio']
                                inscripcion.autorizacionbecadobe=f.cleaned_data['autorizacionbecadobe']
                                inscripcion.autorizacionbecasenecyt=f.cleaned_data['autorizacionbecasencyt']
                                inscripcion.benemeritocuerpobombero=f.cleaned_data['benemeritocuerpobombero']
                                inscripcion.aprobacionayudadobe=f.cleaned_data['aprobacionayudadobe']

                                inscripcion.save()


                                if f.cleaned_data['estcolegio']:
                                    inscripcion.estcolegio_id = f.cleaned_data['estcolegio_id']
                                    inscripcion.save()

                                    # personal.centrocosto_id = int(f.cleaned_data['centrocosto'])
                                    # personal.save()
                                if not INSCRIPCION_CONDUCCION:
                                    if f.cleaned_data['promocion']:
                                        inscripcion.promocion = f.cleaned_data['promocion']
                                        inscripcion.descuentoporcent = f.cleaned_data['descuentoporcent']

                                    if f.cleaned_data['empresaconvenio']:
                                        inscripcion.empresaconvenio_id = f.cleaned_data['empresaconvenio']
                                        if inscripcion.convenio_esempresa():
                                            inscripcion.tipopersonaempresaconvenio = f.cleaned_data['tipopersona']
                                            inscripcion.descuentoconvenio = f.cleaned_data['descuentoempresa']
                                            if 'documentoconvenio' in request.FILES:
                                                inscripcion.parentescotipopersonaec=request.FILES['documentoconvenio']
                                            if f.cleaned_data['espariente']:
                                                inscripcion.parentescotipopersonaec = f.cleaned_data['pariente']
                                            else:
                                                inscripcion.parentescotipopersonaec = None
                                        else:
                                            inscripcion.tipopersonaempresaconvenio = None
                                            inscripcion.parentescotipopersonaec = None
                                            inscripcion.parentescotipopersonaec = None

                                    # OCastillo 26-06-2020 log al poner estado discapacidad
                                    if f.cleaned_data['tienediscapacidad']:
                                        inscripcion.tienediscapacidad = f.cleaned_data['tienediscapacidad']
                                        #Obtain client ip address
                                        client_address = ip_client_address(request)
                                        # Log Editar Discapacidad
                                        LogEntry.objects.log_action(
                                            user_id         = request.user.pk,
                                            content_type_id = ContentType.objects.get_for_model(inscripcion).pk,
                                            object_id       = inscripcion.id,
                                            object_repr     = force_str(inscripcion),
                                            action_flag     = CHANGE,
                                            change_message  = 'Agreagada Discapacidad (' + client_address + ')' )

                                    # OCastillo 26-06-2020 log al quitar estado discapacidad
                                    if f.cleaned_data['sindiscapacidad']:
                                        inscripcion.tienediscapacidad = f.cleaned_data['sindiscapacidad']
                                        #Obtain client ip address
                                        client_address = ip_client_address(request)
                                        # Log Quitar Discapacidad
                                        LogEntry.objects.log_action(
                                            user_id         = request.user.pk,
                                            content_type_id = ContentType.objects.get_for_model(inscripcion).pk,
                                            object_id       = inscripcion.id,
                                            object_repr     = force_str(inscripcion),
                                            action_flag     = CHANGE,
                                            change_message  = 'Sin Discapacidad  (' + client_address + ')' )

                                    inscripcion.save()

                                # Editar el registro en el Perfil de Inscripciones para el seguimiento DOBE
                                if inscripcion.tienediscapacidad:
                                    try:
                                        perfil = PerfilInscripcion.objects.get(inscripcion=inscripcion)
                                        perfil.tienediscapacidad=inscripcion.tienediscapacidad
                                        perfil.save()
                                    except :
                                        perfil = PerfilInscripcion(inscripcion=inscripcion, tienediscapacidad=inscripcion.tienediscapacidad)
                                        perfil.save()

                                #OCastillo 04-julio-2024 cambio en asignatura malla al cambiar la carrera
                                if InscripcionMalla.objects.filter(inscripcion=inscripcion).exists():
                                    inscripcionmalla = InscripcionMalla.objects.get(inscripcion=inscripcion)
                                    malla=Malla.objects.filter(carrera=inscripcion.carrera_id)[:1].get()
                                    if inscripcionmalla.malla.carrera!= inscripcion.carrera_id:
                                        inscripcionmalla.malla=malla
                                        inscripcionmalla.save()
                                        # Obtain client ip address
                                        client_address = ip_client_address(request)

                                        # Log Editar Inscripcion Malla
                                        LogEntry.objects.log_action(
                                            user_id=request.user.pk,
                                            content_type_id=ContentType.objects.get_for_model(inscripcionmalla).pk,
                                            object_id=inscripcionmalla.id,
                                            object_repr=force_str(inscripcionmalla),
                                            action_flag=CHANGE,
                                            change_message='Modificada Inscripcion Malla por cambio de carrera (' + client_address + ')')


                                if UTILIZA_GRUPOS_ALUMNOS:
                                    if inscripcion.inscripciongrupo_set.exists():
                                        inscripcion.inscripciongrupo_set.all().delete()

                                    ig = InscripcionGrupo(inscripcion=inscripcion, grupo=f.cleaned_data['grupo'], activo=True)
                                    ig.save()

                                    #Actualizar el estado del Grupo
                                    if ig.grupo.abierto:
                                        ig.grupo.abierto = ig.grupo.esta_abierto()
                                        ig.grupo.save()


                                inscripcion.persona.nombres=f.cleaned_data['nombres']
                                inscripcion.persona.apellido1=f.cleaned_data['apellido1']
                                inscripcion.persona.apellido2=f.cleaned_data['apellido2']
                                inscripcion.persona.extranjero=f.cleaned_data['extranjero']
                                inscripcion.persona.cedula=f.cleaned_data['cedula']
                                inscripcion.persona.pasaporte=f.cleaned_data['pasaporte']
                                inscripcion.persona.nacimiento=f.cleaned_data['nacimiento']
                                inscripcion.persona.provincia=f.cleaned_data['provincia']
                                inscripcion.persona.canton=f.cleaned_data['canton']
                                if 'sectorresid' in f.cleaned_data :
                                        inscripcion.persona.sectorresid=f.cleaned_data['sectorresid']
                                inscripcion.persona.sexo=f.cleaned_data['sexo']
                                inscripcion.persona.nacionalidad=f.cleaned_data['nacionalidad']
                                inscripcion.persona.madre=f.cleaned_data['madre']
                                inscripcion.persona.padre=f.cleaned_data['padre']

                                inscripcion.persona.direccion=f.cleaned_data['direccion']
                                inscripcion.persona.direccion2=f.cleaned_data['direccion2']
                                inscripcion.persona.num_direccion=f.cleaned_data['num_direccion']
                                inscripcion.persona.sector=f.cleaned_data['sector']
                                inscripcion.persona.provinciaresid=f.cleaned_data['provinciaresid']
                                inscripcion.persona.cantonresid=f.cleaned_data['cantonresid']
                                inscripcion.persona.ciudad=f.cleaned_data['ciudad']

                                inscripcion.persona.telefono=f.cleaned_data['telefono']
                                inscripcion.persona.telefono_conv=f.cleaned_data['telefono_conv']
                                inscripcion.persona.email=f.cleaned_data['email']
                                inscripcion.persona.email1=f.cleaned_data['email1']
                                inscripcion.persona.email2=f.cleaned_data['email2']
                                inscripcion.persona.sangre=f.cleaned_data['sangre']
                                if 'sectorresid' in f.cleaned_data :
                                    inscripcion.persona.sectorresid=f.cleaned_data['sectorresid']
                                    inscripcion.persona.parroquia=f.cleaned_data['parroquia']
                                    inscripcion.persona.save()

                                grupo = f.cleaned_data['grupo']

                                if  f.cleaned_data['extranjero'] or f.cleaned_data['tienediscapacidad'] and  bandera:
                                    # if grupo.nivel_set.filter(periodo__tipo__id=TIPO_PERIODO_PROPEDEUTICO).exists():

                                    # OCU 29-dic-2016 para indicar en correo tipo de notificacion
                                    if f.cleaned_data['extranjero']:
                                        tipo_notificacion='EXTRANJERO'

                                    if f.cleaned_data['tienediscapacidad']:
                                        tipo_notificacion='DISCAPACIDAD'

                                    asunto='Ha cambiado la inscripcion a: ' + tipo_notificacion

                                    if grupo.nivel_set.all().count() == 1 and UTILIZA_NIVEL0_PROPEDEUTICO:
                                        if not 'CONGRESO' in grupo.carrera.nombre:
                                            if not inscripcion.tiene_procesodobe_aprobado():
                                                inscripcion.persona.usuario.is_active= False
                                                inscripcion.persona.usuario.save()

                                                if EMAIL_ACTIVE:
                                                    # inscripcion.notificacion_dobe(request.user)
                                                    inscripcion.notificacion_dobe(request.user,tipo_notificacion,asunto)
                                    else:
                                    #OCastillo 05-sep-2017 Para el caso de modificar inscripcion por tipo discapacidad en cualquier nivel
                                        if EMAIL_ACTIVE:
                                            inscripcion.notificacion_dobe(request.user,tipo_notificacion,asunto)

                                if bandera:
                                    if INSCRIPCION_CONDUCCION:
                                        requisitos = inscripcion.documentos_entregados_conduccion()
                                        requisitos.fotos2 = f.cleaned_data['fotos2']
                                        requisitos.acta = f.cleaned_data['acta']
                                        requisitos.titulo = f.cleaned_data['titulo']
                                        requisitos.licencia=f.cleaned_data['licencia']
                                        requisitos.copia_cedula=f.cleaned_data['copia_cedula']
                                        requisitos.votacion=f.cleaned_data['votacion']
                                        requisitos.carnetsangre=f.cleaned_data['carnetsangre']
                                        requisitos.ex_psicologico=f.cleaned_data['ex_psicologico']
                                        requisitos.val_psicosometrica=f.cleaned_data['val_psicosometrica']
                                        requisitos.val_medica=f.cleaned_data['val_medica']
                                        requisitos.tienediscapacidad=f.cleaned_data['tienediscapacidad']
                                        requisitos.licienciatipoc=f.cleaned_data['licienciatipoc']
                                        requisitos.originalrecord=f.cleaned_data['originalrecord']
                                        requisitos.originalcontenido=f.cleaned_data['originalcontenido']
                                        requisitos.certificado=f.cleaned_data['certificado']
                                        requisitos.tienediscapacidad=f.cleaned_data['tienediscapacidad']
                                        requisitos.tiene_licencia=f.cleaned_data['tiene_licencia']
                                        requisitos.tipo_licencia=f.cleaned_data['tipo_licencia']
                                        requisitos.sabe_conducir=f.cleaned_data['sabe_conducir']
                                        requisitos.puntos_licencia=f.cleaned_data['puntos_licencia']

                                        requisitos.save()

                                        if 'soporte_ant' in request.FILES:
                                            requisitos.soporte_ant=request.FILES['soporte_ant']
                                            requisitos.save()

                                    else:
                                        documentos = inscripcion.documentos_entregados()

                                        if not INSCRIPCION_CONDUCCION:
                                            if f.cleaned_data['becamunicipio']== True:
                                                inscripcion.becamunicipio = True
                                                inscripcion.save()
                                            else:
                                                inscripcion.becamunicipio = False
                                                inscripcion.save()

                                        if f.cleaned_data['acta']== True and not documentos.acta:
                                            documentos.acta = f.cleaned_data['acta']
                                            acta=True
                                            documento2=True
                                        if f.cleaned_data['cedula2'] == True and not documentos.cedula:
                                            documentos.cedula = f.cleaned_data['cedula2']
                                            cedula=True
                                            documento2=True
                                        if f.cleaned_data['fotos'] == True and not documentos.fotos:
                                            documentos.fotos = f.cleaned_data['fotos']
                                            fotos = True
                                            documento2=True
                                        if f.cleaned_data['titulo'] == True and not documentos.titulo:
                                            documentos.titulo = f.cleaned_data['titulo']
                                            titulo = True
                                            documento2=True
                                        if f.cleaned_data['votacion'] == True and not documentos.votacion:
                                            documentos.votacion=f.cleaned_data['votacion']
                                            votacion = True
                                            documento2=True
                                        if f.cleaned_data['actaconv'] == True and not documentos.actaconv:
                                            documentos.actaconv=f.cleaned_data['actaconv']
                                            actaconv = True
                                            documento2=True
                                        if f.cleaned_data['partida_nac'] == True and not documentos.partida_nac:
                                            documentos.partida_nac=f.cleaned_data['partida_nac']
                                            partidanacimiento = True
                                            documento2=True

                                        if f.cleaned_data['actafirmada'] == True and not documentos.actafirmada:
                                            documentos.actafirmada=f.cleaned_data['actafirmada']
                                            actafirmada = True
                                            documento2=True

                                        documentos.save()

                                    if not INSCRIPCION_CONDUCCION:
                                        if EMAIL_ACTIVE:
                                            if documento2:
                                                inscripcion.correo_entregadocumentos_edit(request.user,acta,cedula,fotos,titulo,votacion,actaconv,partidanacimiento,actafirmada)

                                inscripcion.persona.save()

                                if FotoInstEstudiante.objects.filter(inscripcion=inscripcion).exists():
                                    fotoinst = FotoInstEstudiante.objects.get(inscripcion=inscripcion)
                                    if 'foto' in request.FILES:
                                        fotoinst.foto=request.FILES['foto']
                                        fotoinst.save()
                                else:
                                    if 'foto' in request.FILES:
                                        fotoinst = FotoInstEstudiante(inscripcion=inscripcion,
                                                                      foto=request.FILES['foto'])
                                        fotoinst.save()

                                # OCU 11-ene-2017 para extranjeros
                                if InscripcionExtranjerosTitulo.objects.filter(inscripcion=inscripcion).exists():
                                    tituloextranjero=InscripcionExtranjerosTitulo.objects.get(inscripcion=inscripcion)
                                    if 'titulodoc' in request.FILES:
                                        tituloextranjero.titulodoc=request.FILES['titulodoc']
                                        tituloextranjero.save()
                                else:
                                    if f.cleaned_data['extranjero'] and 'titulodoc' in request.FILES:
                                        tituloextranjero = InscripcionExtranjerosTitulo(inscripcion=inscripcion,
                                                                                        titulodoc=request.FILES['titulodoc'])
                                        tituloextranjero.save()

                                if f.cleaned_data['enviarcorreo'] and EMAIL_ACTIVE:
                                    inscripcion.correo_congreo(ig.grupo)

                            else:
                                inscripcion.persona.nombres=f.cleaned_data['nombres']
                                inscripcion.persona.apellido1=f.cleaned_data['apellido1']
                                inscripcion.persona.apellido2=f.cleaned_data['apellido2']
                                inscripcion.persona.extranjero=f.cleaned_data['extranjero']
                                inscripcion.persona.cedula=f.cleaned_data['cedula']
                                inscripcion.persona.pasaporte=f.cleaned_data['pasaporte']
                                inscripcion.persona.nacimiento=f.cleaned_data['nacimiento']
                                inscripcion.persona.provincia=f.cleaned_data['provincia']
                                inscripcion.persona.canton=f.cleaned_data['canton']
                                inscripcion.persona.sexo=f.cleaned_data['sexo']
                                inscripcion.persona.nacionalidad=f.cleaned_data['nacionalidad']
                                inscripcion.persona.madre=f.cleaned_data['madre']
                                inscripcion.persona.padre=f.cleaned_data['padre']

                                inscripcion.persona.direccion=f.cleaned_data['direccion']
                                inscripcion.persona.direccion2=f.cleaned_data['direccion2']
                                inscripcion.persona.num_direccion=f.cleaned_data['num_direccion']
                                inscripcion.persona.sector=f.cleaned_data['sector']
                                inscripcion.persona.provinciaresid=f.cleaned_data['provinciaresid']
                                inscripcion.persona.cantonresid=f.cleaned_data['cantonresid']
                                inscripcion.persona.ciudad=f.cleaned_data['ciudad']

                                inscripcion.persona.telefono=f.cleaned_data['telefono']
                                inscripcion.persona.telefono_conv=f.cleaned_data['telefono_conv']
                                inscripcion.persona.email=f.cleaned_data['email']
                                inscripcion.persona.email1=f.cleaned_data['email1']
                                inscripcion.persona.email2=f.cleaned_data['email2']
                                inscripcion.persona.sangre=f.cleaned_data['sangre']

                                inscripcion.persona.save()

                            #Obtain client ip address
                            client_address = ip_client_address(request)

                            # Log Editar Inscripcion
                            LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(inscripcion).pk,
                                object_id       = inscripcion.id,
                                object_repr     = force_str(inscripcion),
                                action_flag     = CHANGE,
                                change_message  = 'Modificada Inscripcion (' + client_address + ')' )



                            if 'graduado' in request.POST:
                                graduado = Graduado.objects.get(pk=request.POST['graduado'])
                                return HttpResponseRedirect("/graduados?s="+str(graduado.inscripcion.persona.cedula))
                            else:
                                if inscripcion.persona.cedula:
                                     if documento2 and not INSCRIPCION_CONDUCCION :
                                        return HttpResponseRedirect("/inscripciones?s="+str(inscripcion.persona.cedula)+"&doc2="+str(documento2)+"&ins="+str(inscripcion.id)+"&cedula="+str(cedula)+"&acta="+str(acta)+"&fotos="+str(fotos)+"&titulo="+str(titulo)+"&votacion="+str(votacion)+"&actaconv="+str(actaconv)+"&partidanacimiento="+str(partidanacimiento))
                                     else:
                                        return HttpResponseRedirect("/inscripciones?s="+str(inscripcion.persona.cedula))
                                else:
                                     if documento2 and not INSCRIPCION_CONDUCCION :
                                        return HttpResponseRedirect("/inscripciones?s="+str(inscripcion.persona.pasaporte)+"&doc2="+str(documento2)+"&ins="+str(inscripcion.id)+"&cedula="+str(cedula)+"&acta="+str(acta)+"&fotos="+str(fotos)+"&titulo="+str(titulo)+"&votacion="+str(votacion)+"&actaconv="+str(actaconv)+"&partidanacimiento="+str(partidanacimiento))
                                     else:
                                        return HttpResponseRedirect("/inscripciones?s="+str(inscripcion.persona.pasaporte))

                        except Exception as ex:
                            return HttpResponseRedirect("/inscripciones?action=edit&id="+str(inscripcion.id)+"&error=1")
                    except Exception as e:
                        return HttpResponseRedirect("/?info="+str(e))
                elif action == 'addtrabajo':
                    inscripcion = Inscripcion.objects.get(pk=request.POST['id'])
                    f = EmpresaInscripcionForm(request.POST)
                    if f.is_valid():
                        empresa = EmpresaInscripcion(inscripcion=inscripcion,
                                                     razon=f.cleaned_data['razon'],
                                                     cargo=f.cleaned_data['cargo'],
                                                     direccion=f.cleaned_data['direccion'],
                                                     telefono=f.cleaned_data['telefono'],
                                                     email=f.cleaned_data['email'])
                        empresa.save()
                        return HttpResponseRedirect("/inscripciones?action=trabajo&id="+str(inscripcion.id))
                    else:
                        return HttpResponseRedirect("/inscripciones?action=addtrabajo&id="+str(inscripcion.id))
                elif action=='edittrabajo':
                    empresa = EmpresaInscripcion.objects.get(pk=request.POST['id'])
                    inscripcion = empresa.inscripcion
                    f = EmpresaInscripcionForm(request.POST)
                    if f.is_valid():
                        empresa.razon=f.cleaned_data['razon']
                        empresa.cargo=f.cleaned_data['cargo']
                        empresa.direccion=f.cleaned_data['direccion']
                        empresa.telefono=f.cleaned_data['telefono']
                        empresa.email=f.cleaned_data['email']

                        empresa.save()
                        return HttpResponseRedirect("/inscripciones?action=trabajo&id="+str(inscripcion.id))
                    else:
                        return HttpResponseRedirect("/inscripciones?action=edittrabajo&id="+str(inscripcion.id))
                elif action=='deltrabajo':
                    trabajo = EmpresaInscripcion.objects.get(pk=request.POST['id'])
                    inscripcion = trabajo.inscripcion
                    trabajo.delete()
                    return HttpResponseRedirect("/inscripciones?action=trabajo&id="+str(inscripcion.id))

                elif action == 'addestudio':
                    inscripcion = Inscripcion.objects.get(pk=request.POST['id'])
                    f = EstudioInscripcionForm(request.POST)
                    if f.is_valid():
                        estudio = EstudioInscripcion(inscripcion=inscripcion,
                                                    colegio=f.cleaned_data['colegio'],
                                                    titulo=f.cleaned_data['titulo'],
                                                    incorporacion=f.cleaned_data['incorporacion'],
                                                    especialidad=f.cleaned_data['especialidad'],
                                                    universidad=f.cleaned_data['universidad'],
                                                    carrera=f.cleaned_data['carrera'],
                                                    anoestudio=f.cleaned_data['anoestudio'],
                                                    graduado=f.cleaned_data['graduado'])
                        estudio.save()

                elif action=='editestudio':
                    estudio = EstudioInscripcion.objects.get(pk=request.POST['id'])
                    inscripcion = estudio.inscripcion
                    f = EstudioInscripcionForm(request.POST)
                    if f.is_valid():
                        estudio.colegio=f.cleaned_data['colegio']
                        estudio.titulo=f.cleaned_data['titulo']
                        estudio.incorporacion=f.cleaned_data['incorporacion']
                        estudio.especialidad=f.cleaned_data['especialidad']
                        estudio.universidad=f.cleaned_data['universidad']
                        estudio.carrera=f.cleaned_data['carrera']
                        estudio.anoestudio=f.cleaned_data['anoestudio']
                        estudio.graduado=f.cleaned_data['graduado']

                        estudio.save()
                        return HttpResponseRedirect("/inscripciones?action=estudio&id="+str(inscripcion.id))
                    else:
                        return HttpResponseRedirect("/inscripciones?action=editestudio&id="+str(inscripcion.id))

                elif action=='delestudio':
                    estudio = EstudioInscripcion.objects.get(pk=request.POST['id'])
                    inscripcion = estudio.inscripcion
                    estudio.delete()
                    return HttpResponseRedirect("/inscripciones?action=estudio&id="+str(inscripcion.id))

                #Practicas Preprofesionales
                elif action == 'addpracticas':
                    inscripcion = Inscripcion.objects.get(pk=request.POST['id'])
                    f = InscripcionPracticaForm(request.POST, request.FILES)
                    if f.is_valid():
                        practica = InscripcionPracticas(inscripcion=inscripcion,
                                                     horas=f.cleaned_data['horas'],
                                                     lugar=f.cleaned_data['lugar'],
                                                     profesor=f.cleaned_data['profesor'],
                                                     inicio=f.cleaned_data['inicio'],
                                                     fin=f.cleaned_data['fin'],
                                                     observaciones=f.cleaned_data['observaciones'],
                                                     equipamiento=f.cleaned_data['equipamiento'],
                                                     nivelmalla=f.cleaned_data['nivelmalla'])
                        practica.save()
                        if 'archivo' in request.FILES:
                            practica.archivo = request.FILES['archivo']
                            practica.save()

                        practica.correo_practica(request.user,'SE HA AGREGO PRACTICAS PREPROFESIONALES')
                        #Obtain client ip address
                        client_address = ip_client_address(request)

                        # Log de ADICIONAR DOCUMENTO
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(practica).pk,
                            object_id       = practica.id,
                            object_repr     = force_str(practica),
                            action_flag     = ADDITION,
                            change_message  = 'Adicionada Practica (' + client_address + ')' )

                        if not inscripcion.malla_inscripcion().malla.nueva_malla:

                            if ASIG_PRATICA > 0:

                                asig = Asignatura.objects.get(pk=ASIG_PRATICA)
                                if HistoricoRecordAcademico.objects.filter(inscripcion=inscripcion, asignatura=asig).exists():
                                    historico = HistoricoRecordAcademico.objects.filter(inscripcion=inscripcion, asignatura=asig)[:1].get()
                                    historico.asignatura=asig
                                    historico.nota=100
                                    historico.asistencia=100
                                    historico.fecha=practica.fin
                                    historico.aprobada=True
                                    historico.convalidacion=False
                                    historico.pendiente=False
                                else:

                                    historico = HistoricoRecordAcademico(inscripcion=inscripcion,
                                                                asignatura=asig,
                                                                nota=100,
                                                                asistencia=100,
                                                                fecha=practica.fin,
                                                                aprobada=True,
                                                                convalidacion=False,
                                                                pendiente=False)
                                historico.save()

                                if RecordAcademico.objects.filter(inscripcion=inscripcion,asignatura=asig).exists():
                                    record = RecordAcademico.objects.filter(inscripcion=inscripcion,asignatura=asig)[:1].get()
                                    record.nota=100
                                    record.asistencia=100
                                    record.fecha=practica.fin
                                    record.aprobada=True
                                    record.convalidacion=False
                                    record.pendiente=False
                                else:
                                    record = RecordAcademico(inscripcion=inscripcion, asignatura=asig,
                                                        nota=100, asistencia=100,
                                                        fecha=practica.fin, aprobada=True,
                                                        convalidacion=False, pendiente=False)
                                record.save()
                                if practica.horas < HORAS_PRACTICA:
                                    record.delete()
                                    historico.delete()
                                else:
                                    client_address = ip_client_address(request)
                                    # aprobacion.correo_aprobacionvinculacion(request.user,'SE HA APROBADO Y AGREGADO LA NOTA DE VINCULACION CON LA COMUNIDAD',estudiantes_aprobados)
                                    # Log de Aprobacion Vinculacion
                                    LogEntry.objects.log_action(
                                         user_id         = request.user.pk,
                                         content_type_id = ContentType.objects.get_for_model(inscripcion).pk,
                                         object_id       = inscripcion.id,
                                         object_repr     = force_str(inscripcion),
                                         action_flag     = ADDITION,
                                         change_message  = 'Adicionada Nota de Practica (' + client_address + ')'  )
                            #     else:
                            #         practica.correo_practica(request.user,'SE HA AGREGADO LA NOTA DE  PRACTICAS PREPROFESIONALES')

                        return HttpResponseRedirect("/inscripciones?action=practicas&id="+str(inscripcion.id))
                    else:
                        return HttpResponseRedirect("/inscripciones?action=addpracticas&id="+str(inscripcion.id))


                elif action=='editpracticas':
                    practica = InscripcionPracticas.objects.get(pk=request.POST['id'])
                    inscripcion = practica.inscripcion
                    f = InscripcionPracticaForm(request.POST, request.FILES)
                    malla = inscripcion.malla_inscripcion().malla


                    if f.is_valid():
                        nivelmall = f.cleaned_data['nivelmalla']
                        if inscripcion.malla_inscripcion().malla.nueva_malla:
                            asig = AsignaturaMalla.objects.get(asignatura__nombre__icontains='PREPRO',malla=malla,nivelmalla=nivelmall)
                            # horastotalingresada = int(f.cleaned_data['horas']) + InscripcionPracticas.objects.filter(inscripcion=inscripcion,nivelmalla=nivelmall).aggregate(Sum('horas'))['horas__sum'] if InscripcionPracticas.objects.filter(inscripcion=inscripcion,nivelmalla=nivelmall).aggregate(Sum('horas'))['horas__sum']!=None else 0
                            horastotalingresada = int(f.cleaned_data['horas'])
                            if horastotalingresada>asig.horas:
                                return HttpResponseRedirect("/?info="+str("La cantidad de hora ingresada es mayor a la horas de la practica en este Nivel"))
                        practica.horas=f.cleaned_data['horas']
                        practica.lugar=f.cleaned_data['lugar']
                        practica.profesor=f.cleaned_data['profesor']
                        practica.inicio=f.cleaned_data['inicio']
                        practica.fin=f.cleaned_data['fin']
                        practica.observaciones=f.cleaned_data['observaciones']
                        practica.equipamiento=f.cleaned_data['equipamiento']
                        practica.nivelmalla=f.cleaned_data['nivelmalla']
                        if 'archivo' in request.FILES:
                            practica.archivo=request.FILES['archivo']
                        practica.save()
                        asig = Asignatura.objects.get(pk=ASIG_PRATICA)
                        if not inscripcion.malla_inscripcion().malla.nueva_malla:
                            if HistoricoRecordAcademico.objects.filter(inscripcion=inscripcion, asignatura=asig).exists():
                                historico = HistoricoRecordAcademico.objects.filter(inscripcion=inscripcion, asignatura=asig)[:1].get()
                            else:
                                historico = HistoricoRecordAcademico(inscripcion=inscripcion,
                                                            asignatura=asig,
                                                            nota=100,
                                                            asistencia=100,
                                                            fecha=practica.fin,
                                                            aprobada=True,
                                                            convalidacion=False,
                                                            pendiente=False)
                                historico.save()
                            if RecordAcademico.objects.filter(inscripcion=inscripcion,asignatura=asig).exists():
                                record = RecordAcademico.objects.filter(inscripcion=inscripcion,asignatura=asig)[:1].get()
                            else:
                                record = RecordAcademico(inscripcion=inscripcion, asignatura=asig,
                                                    nota=100, asistencia=100,
                                                    fecha=practica.fin, aprobada=True,
                                                    convalidacion=False, pendiente=False)
                                record.save()
                            if practica.horas < HORAS_PRACTICA:
                                record.delete()
                                historico.delete()
                            else:
                                client_address = ip_client_address(request)

                                # Log de ADICIONAR DOCUMENTO
                                LogEntry.objects.log_action(
                                    user_id         = request.user.pk,
                                    content_type_id = ContentType.objects.get_for_model(practica).pk,
                                    object_id       = practica.id,
                                    object_repr     = force_str(practica),
                                    action_flag     = ADDITION,
                                    change_message  = 'Adicionada Nota de Practica (' + client_address + ')' )
                        practica.correo_practica(request.user,'SE HA EDITADO PRACTICAS PREPROFESIONALES')

                        if 'p' in request.POST:
                            return HttpResponseRedirect("pagopracticas_docente?action=ver_practicas&id="+str(request.POST['p']))
                        else:
                            return HttpResponseRedirect("/inscripciones?action=practicas&id="+str(inscripcion.id))
                    else:
                        return HttpResponseRedirect("/inscripciones?action=editpracticas&id="+str(inscripcion.id))

                elif action=='delpracticas':
                    practica = InscripcionPracticas.objects.get(pk=request.POST['id'])
                    inscripcion = practica.inscripcion
                    practica.correo_practica(request.user,'SE HA ELIMINADO LA NOTA DE PRACTICAS PREPROFESIONALES')
                    asig = Asignatura.objects.get(pk=ASIG_PRATICA)
                    if HistoricoRecordAcademico.objects.filter(inscripcion=inscripcion, asignatura=asig).exists():
                        HistoricoRecordAcademico.objects.filter(inscripcion=inscripcion, asignatura=asig)[:1].get().delete()
                    if RecordAcademico.objects.filter(inscripcion=inscripcion,asignatura=asig).exists():
                        RecordAcademico.objects.filter(inscripcion=inscripcion,asignatura=asig)[:1].get().delete()

                    client_address = ip_client_address(request)
                    # Log de ELIMINAR PRACTICAS OCastillo 17-08-2020
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(practica).pk,
                        object_id       = practica.id,
                        object_repr     = force_str(practica),
                        action_flag     = DELETION,
                        change_message  = 'Eliminada Nota de Practica (' + client_address + ')' )
                    practica.delete()
                    if 'p' in request.POST:
                        return HttpResponseRedirect("pagopracticas_docente?action=ver_practicas&id="+str(request.POST['p']))
                    else:
                        return HttpResponseRedirect("/inscripciones?action=practicas&id="+str(inscripcion.id))

                elif action == 'generarclave':
                    inscripcion = Inscripcion.objects.get(pk=request.POST['id'])
                    f = PadreClaveForm(request.POST)
                    if f.is_valid():
                        clave = gen_passwd()
                        email = f.cleaned_data['email']
                        padreclave = PadreClave(inscripcion=inscripcion,
                                                nombre=f.cleaned_data['nombre'],
                                                cedula=f.cleaned_data['cedula'],
                                                email=email,
                                                fecha=datetime.now(),
                                                clave=clave)
                        padreclave.save()
                        if EMAIL_ACTIVE:
                            padreclave.mail_subject_respuesta_clave(email)

                        return HttpResponseRedirect("/inscripciones?s="+str(inscripcion.persona.cedula))
                    else:
                        return HttpResponseRedirect("/inscripciones?action=generarclave&id="+str(inscripcion.id))

                elif action == 'activacionegresado':
                    d = EstudianteXEgresar.objects.get(pk=request.POST['id'])
                    d.estado = not d.estado
                    d.save()
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                elif action=='egresados':
                    try:
                        estudiantexegresar = EstudianteXEgresar.objects.all()
                        estudiantexegresar.delete()
                        insc = [x for x in Inscripcion.objects.filter(persona__usuario__is_active=True,egresado=None) if x.puede_egresar() == ""  and not x.egresado() and not x.graduado()]

                        for inscripcion in insc:
                            estudiantexegresar = EstudianteXEgresar(inscripcion=inscripcion,
                                                                    promedio = inscripcion.promedio_egresado(),
                                                                    asistencia = inscripcion.promedioasistencia_egresado(),
                                                                    estado = True)
                            estudiantexegresar.save()
                        result = {}
                        result['result'] = 'ok'
                        return HttpResponse(json.dumps(result),content_type="application/json")
                    except Exception as e:
                        return HttpResponse(json.dumps({'result':'bad'+str(e)}),content_type="application/json")

                elif action=='adddocumento':
                    form = DocumentoInscripcionForm(request.POST, request.FILES)
                    inscripcion = Inscripcion.objects.get(pk=int(request.POST['inscripcion']))
                    if form.is_valid():
                        archivo = Archivo(nombre=form.cleaned_data['tipo'].nombre,
                            fecha=datetime.now(),
                            archivo = request.FILES['archivo'],
                            tipo = form.cleaned_data['tipo'])
                        archivo.save()

                        documento = DocumentoInscripcion(inscripcion=inscripcion, archivo=archivo)
                        documento.save()

                        #Obtain client ip address
                        client_address = ip_client_address(request)

                        # Log de ADICIONAR DOCUMENTO
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(documento).pk,
                            object_id       = documento.id,
                            object_repr     = force_str(documento),
                            action_flag     = ADDITION,
                            change_message  = 'Adicionado Documento Inscripcion (' + client_address + ')' )

                        return HttpResponseRedirect("/inscripciones?action=documentos&id="+str(inscripcion.id))

                elif action=='deldocumento':
                    documento = DocumentoInscripcion.objects.get(pk=request.POST['id'])
                    inscripcion = documento.inscripcion
                    archivo = Archivo.objects.get(pk=documento.archivo.id)

                    archivo.archivo.delete()

                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de ELIMINAR DOCUMENTO
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(documento).pk,
                        object_id       = documento.id,
                        object_repr     = force_str(documento),
                        action_flag     = DELETION,
                        change_message  = 'Eliminado Documento Inscripcion (' + client_address + ')' )

                    documento.delete()
                    archivo.delete()

                    return HttpResponseRedirect("/inscripciones?action=documentos&id="+str(inscripcion.id))

                elif action=='egresar':
                    inscripcion = Inscripcion.objects.get(pk=request.POST['id'])
                    f = EgresadoForm(request.POST)
                    if f.is_valid():
                        egresado = Egresado(inscripcion=inscripcion, notaegreso=f.cleaned_data['notaegreso'], fechaegreso=f.cleaned_data['fechaegreso'])
                        egresado.save()

                        #Obtain client ip address
                        client_address = ip_client_address(request)

                        # Log de ADICIONAR EGRESADO
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(inscripcion).pk,
                            object_id       = inscripcion.id,
                            object_repr     = force_str(inscripcion),
                            action_flag     = ADDITION,
                            change_message  = 'Adicionado Egresado (' + client_address + ')' )

                        return HttpResponseRedirect("/egresados")
                    else:
                        return HttpResponseRedirect("/inscripciones?action=egresar&id="+str(inscripcion.id))

                elif action=='becasenescyt':
                    isenescyt = InscripcionSenescyt.objects.get(pk=request.POST['id'])
                    inscripcion = isenescyt.inscripcion
                    f = InscripcionSenescytForm(request.POST)
                    if f.is_valid():
                        isenescyt.fecha = f.cleaned_data['fecha']
                        isenescyt.tienebeca = f.cleaned_data['tienebeca']
                        isenescyt.observaciones = f.cleaned_data['observaciones']
                        isenescyt.save()

                        #Eliminarle los rubros que haya tenido creados y no cancelados como el de inscripcion
                        if inscripcion.rubros_pendientes():
                            for r in inscripcion.rubros_pendientes():
                                r.delete()

                        #Obtain client ip address
                        client_address = ip_client_address(request)

                        # Log de ADICIONAR BECA SENESCYT
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(inscripcion).pk,
                            object_id       = inscripcion.id,
                            object_repr     = force_str(inscripcion),
                            action_flag     = CHANGE,
                            change_message  = 'Asignada Beca Senescyt (' + client_address + ')' )

                        return HttpResponseRedirect("/inscripciones?s="+str(inscripcion.persona.cedula))
                    else:
                        return HttpResponseRedirect("/inscripciones?action=becasenescyt&id="+str(inscripcion.id))

                elif action=='asignarbeca':
                    inscripcion = Inscripcion.objects.get(pk=request.POST['id'])
                    f = BecarioForm(request.POST)
                    if f.is_valid():
                        becario = InscripcionBecario(inscripcion=inscripcion,
                                                     porciento=f.cleaned_data['porciento'],
                                                     tipobeca=f.cleaned_data['tipobeca'],
                                                     motivo=f.cleaned_data['motivo'],
                                                     fecha=datetime.now())
                        becario.save()

                        #Obtain client ip address
                        client_address = ip_client_address(request)

                        # Log de ADICIONAR BECARIO
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(becario).pk,
                            object_id       = becario.id,
                            object_repr     = force_str(becario),
                            action_flag     = ADDITION,
                            change_message  = 'Adicionado Becario (' + client_address + ')' )

                        return HttpResponseRedirect("/inscripciones?s="+str(inscripcion.persona.cedula))
                    else:
                        return HttpResponseRedirect("/inscripciones?action=asignarbeca&id="+str(inscripcion.id))

                elif action=='actividades':
                    inscripcion = Inscripcion.objects.get(pk=request.POST['inscripcion'])
                    f = ActividadesInscripcionForm(request.POST)
                    if f.is_valid():
                        ei = EstudioInscripcion(inscripcion=inscripcion,
                                                colegio=f.cleaned_data['colegio'],
                                                titulo=f.cleaned_data['titulo'],
                                                incorporacion=f.cleaned_data['incorporacion'],
                                                especialidad=f.cleaned_data['especialidad'],
                                                universidad=f.cleaned_data['universidad'],
                                                carrera=f.cleaned_data['carrera'],
                                                anoestudio=f.cleaned_data['anoestudio'],
                                                graduado=f.cleaned_data['graduado'])
                        if ei.colegio or ei.titulo or ei.incorporacion or \
                            ei.especialidad or ei.universidad or ei.carrera or \
                            ei.anoestudio:
                            ei.save()

                        ti = EmpresaInscripcion(inscripcion=inscripcion,
                                                razon=f.cleaned_data['razon'],
                                                cargo=f.cleaned_data['cargo'],
                                                direccion=f.cleaned_data['direccion'],
                                                telefono=f.cleaned_data['telefono'],
                                                email=f.cleaned_data['email'])
                        if ti.razon or ti.cargo or ti.direccion or \
                            ti.telefono or ti.email:
                            ti.save()
                        return HttpResponseRedirect("/inscripciones?s="+(inscripcion.persona.cedula if inscripcion.persona.cedula else inscripcion.persona.pasaporte))

                elif action=='retirar':
                    inscripcion = Inscripcion.objects.get(pk=request.POST['id'])
                    f = RetiradoMatriculaForm(request.POST)
                    if f.is_valid():
                        if not RetiradoMatricula.objects.filter(inscripcion=inscripcion, nivel=None).exists():
                            retiro = RetiradoMatricula(inscripcion=inscripcion,
                                                       fecha=f.cleaned_data['fecha'],
                                                       motivo=f.cleaned_data['motivo'])
                            retiro.save()

                            #Obtain client ip address
                            client_address = ip_client_address(request)

                            # Log de RETIRAR INSCRIPCION
                            LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(inscripcion).pk,
                                object_id       = inscripcion.id,
                                object_repr     = force_str(inscripcion),
                                action_flag     = DELETION,
                                change_message  = 'Retirado de Inscripcion (' + client_address + ')' )

                    else:
                        return HttpResponseRedirect("/inscripciones?action=retirar&id="+str(inscripcion.id))

                #Observaciones a Estudiantes
                elif action=='addobservacion':
                    inscripcion = Inscripcion.objects.get(pk=request.POST['id'])
                    f = ObservacionInscripcionForm(request.POST)
                    if f.is_valid():
                        observacion = ObservacionInscripcion(inscripcion=inscripcion,
                                                             tipo=f.cleaned_data['tipo'],
                                                             observaciones=f.cleaned_data['observaciones'],
                                                             fecha = datetime.now(),
                                                             activa=True,
                                                             usuario=request.user)
                        observacion.save()

                        if observacion.tipo.id == 3:
                            observacion.correo_docente()
                            if observacion.inscripcion.matricula():
                                 if 'CONGRESO' in observacion.inscripcion.matricula().nivel.carrera.nombre:
                                     if RubroMatricula.objects.filter(matricula=observacion.inscripcion.matricula()).exists():

                                         if RubroMatricula.objects.filter(matricula=observacion.inscripcion.matricula())[:1].get().rubro.puede_eliminarse():
                                             rubro = RubroMatricula.objects.filter(matricula=observacion.inscripcion.matricula())[:1].get().rubro
                                             RubroMatricula.objects.filter(matricula=observacion.inscripcion.matricula())[:1].get().delete()
                                             rubro.delete()


                        #Obtain client ip address
                        client_address = ip_client_address(request)

                        # Log de ADICIONAR OBSERVACION
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(observacion).pk,
                            object_id       = observacion.id,
                            object_repr     = force_str(observacion),
                            action_flag     = ADDITION,
                            change_message  = 'Adicionada Observacion de Inscripcion (' + client_address + ')' )

                        return HttpResponseRedirect("/inscripciones?action=observaciones&id="+str(inscripcion.id))
                    else:
                        return HttpResponseRedirect("/inscripciones?action=addobservacion")
                #Observaciones a Estudiantes
                elif action=='addcertificado':
                    inscripcion = Inscripcion.objects.get(pk=request.POST['id'])
                    f = CertificadoForm(request.POST)
                    if f.is_valid():
                        certificado = CertificadoEntregado(inscripcion=inscripcion,
                                                             anio=f.cleaned_data['anio'],
                                                             certificado=f.cleaned_data['certificado'],
                                                             entregado=f.cleaned_data['entregado'],
                                                             fecha = datetime.now(),
                                                             usuario=request.user)
                        certificado.save()

                        #Obtain client ip address
                        client_address = ip_client_address(request)

                        # Log de ADICIONAR OBSERVACION
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(certificado).pk,
                            object_id       = certificado.id,
                            object_repr     = force_str(certificado),
                            action_flag     = ADDITION,
                            change_message  = 'Adicionada Entrega de Certificado (' + client_address + ')' )

                        return HttpResponseRedirect("/inscripciones?action=certificados&id="+str(inscripcion.id))
                    else:
                        return HttpResponseRedirect("/inscripciones?action=addcertificado")

                elif action=='editobservacion':
                    observacion = ObservacionInscripcion.objects.get(pk=request.POST['id'])
                    f = ObservacionInscripcionForm(request.POST)
                    if f.is_valid():
                        observacion.observaciones = f.cleaned_data['observaciones']
                        observacion.tipo = f.cleaned_data['tipo']
                        observacion.fecha = datetime.now()
                        observacion.usuario=request.user
                        observacion.activa = f.cleaned_data['activa']
                        observacion.save()

                        #Obtain client ip address
                        client_address = ip_client_address(request)

                        # Log de EDITAR OBSERVACION
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(observacion).pk,
                            object_id       = observacion.id,
                            object_repr     = force_str(observacion),
                            action_flag     = CHANGE,
                            change_message  = 'Editada Observacion de Inscripcion (' + client_address + ')' )

                        return HttpResponseRedirect("/inscripciones?action=observaciones&id="+str(observacion.inscripcion.id))
                    else:
                        return HttpResponseRedirect("/inscripciones?action=editobservacion&id="+str(observacion.id))

                elif action=='delobservacion':
                    observacion = ObservacionInscripcion.objects.get(pk=request.POST['id'])
                    inscripcion = observacion.inscripcion

                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de ELIMINAR OBSERVACION
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(observacion).pk,
                        object_id       = observacion.id,
                        object_repr     = force_str(observacion),
                        action_flag     = CHANGE,
                        change_message  = 'Eliminada Observacion de Inscripcion (' + client_address + ')' )

                    observacion.delete()
                    return HttpResponseRedirect("/inscripciones?action=observaciones&id="+str(inscripcion.id))
                #   Opcion para Atender turnos
                elif action=='attu':
                    try:
                        persona=Persona.objects.get(usuario=request.user).id
                        fecha=datetime.now().date()
                        if TurnoDet.objects.filter(atendido=False, horatiket=fecha).exists():
                            tiket=int(TurnoDet.objects.filter(atendido=False, horatiket=fecha).order_by('tiket')[:1].get().tiket)
                            if TurnoCab.objects.filter().exists():
                                a=''

                            puntos=PuntoAtencion.objects.get(pk=request.POST['id'])
                            if(puntos.estadopunto):
                                puntos.estadopunto=0
                            else:
                                puntos.estadopunto=1
                            puntos.save()
                        return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                    except:
                        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

                elif action=='addsuspension':
                    try:
                        if Inscripcion.objects.filter(id=request.POST['id']).exists():
                            inscripcion =  Inscripcion.objects.get(id=request.POST['id'])
                            fechasus = date(int(request.POST['fechasus'].split('-')[2]),int(request.POST['fechasus'].split('-')[1]),int(request.POST['fechasus'].split('-')[0]))
                            #Obtain client ip address
                            client_address = ip_client_address(request)
                            if request.POST['opc'] == '3':
                               eliminasuspension = EliminaSuspension(
                                                        inscripcionsuspension_id = request.POST['inscsusp'],
                                                        motivosuspension_id = request.POST['motivosuspension'],
                                                        observacion = request.POST['observacion'],
                                                        fecha = fechasus,
                                                        user_id = request.user.pk)
                               eliminasuspension.save()
                               contenido = 'SUSPENSION REVOCADA'
                               objetsuspen = eliminasuspension
                               opcsus = 3
                               inscripcion.suspension = False
                               # Log de ELIMINAR OBSERVACION
                               LogEntry.objects.log_action(
                                    user_id         = request.user.pk,
                                    content_type_id = ContentType.objects.get_for_model(eliminasuspension).pk,
                                    object_id       = eliminasuspension.id,
                                    object_repr     = force_str(eliminasuspension),
                                    action_flag     = CHANGE,
                                    change_message  = u'Quitar suspension de alumno (' + client_address + ')' )
                            else:
                                if request.POST['opc'] == '1':
                                    inscripcionsuspencion = InscripcionSuspension(
                                                            tiposuspension_id = int(request.POST['tiposuspension']),
                                                            motivosuspension_id = int(request.POST['motivosuspension']),
                                                            inscripcion_id =int(request.POST['id']) ,
                                                            observacion = request.POST['observacion'],
                                                            fecha = fechasus,
                                                            user_id = request.user.pk)
                                    mensaje = 'Suspension de Alumno ('
                                    inscripcion.suspension = True
                                    contenido = 'SUSPENSION'
                                    opcsus = 1
                                else:

                                    inscripcionsuspencion = InscripcionSuspension.objects.get(id = int(request.POST['inscsusp']))
                                    inscripcionsuspencion.tiposuspension_id = int(request.POST['tiposuspension'])
                                    inscripcionsuspencion.motivosuspension_id = int(request.POST['motivosuspension'])
                                    inscripcionsuspencion.inscripcion_id =int(request.POST['id'])
                                    inscripcionsuspencion.observacion = request.POST['observacion']
                                    inscripcionsuspencion.fecha = fechasus
                                    inscripcionsuspencion.user_id = request.user.pk
                                    mensaje = 'Eliminacion de Suspension de Alumno ('
                                    inscripcion.suspension = True
                                    contenido = 'SUSPENSION EDITADA'
                                    opcsus = 2
                                inscripcionsuspencion.save()
                                objetsuspen = inscripcionsuspencion
                                # Log de ELIMINAR OBSERVACION
                                LogEntry.objects.log_action(
                                    user_id         = request.user.pk,
                                    content_type_id = ContentType.objects.get_for_model(inscripcionsuspencion).pk,
                                    object_id       = inscripcionsuspencion.id,
                                    object_repr     = force_str(inscripcionsuspencion),
                                    action_flag     = CHANGE,
                                    change_message  = mensaje + client_address + ')' )
                            inscripcion.save()

                            if EMAIL_ACTIVE:
                                inscripcion.correo_suspension(contenido,objetsuspen,opcsus)

                            return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
                    except:
                        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

                elif action=='graduarcondu':
                    if INSCRIPCION_CONDUCCION:
                         periodo = request.session['periodo']
                         estudiantexgraduar = GraduadoConduccion.objects.filter(periodo=periodo)
                         estudiantexgraduar.delete()
                         # insc = [x for x in Inscripcion.objects.filter(matricula__nivel__periodo=periodo,graduadoconduccion__inscripcion=None).order_by('persona__apellido1','persona__apellido2','persona__nombres') if not x.graduadocondu()]
                         insc = [x for x in Inscripcion.objects.filter(matricula__nivel__periodo=periodo).order_by('persona__apellido1','persona__apellido2','persona__nombres')]
                         examen_teo = 0
                         examen_prac = 0
                         promedio = 0
                         notal_final = 0
                         grado_fecha = ""
                         result={}
                         result['mensaje']  = 'bad'
                         if insc:
                             for inscripcion in insc:
                                try:
                                    # promedio = (inscripcion.graduadocondu_prom_val()).quantize(Decimal(10)**-2)
                                    # print((inscripcion))
                                    promedio = inscripcion.graduadocondu_prom_val()
                                    # if inscripcion.recordacademico_set.filter(asignatura__id=ASIGNATURA_EDU_VIAL).exists():
                                    # OCU 25-abril-2017 cambio para promedio teorico por carrera
                                    if PromedioNotasGrado.objects.filter(carrera=inscripcion.carrera,vial=True,activo=True).exists():
                                        teoria=PromedioNotasGrado.objects.filter(carrera=inscripcion.carrera,vial=True)[:1].get()
                                    # if RecordAcademico.objects.filter(inscripcion=insc).exists():
                                        examen_teo =  inscripcion.promedio_teorico()
                                        if examen_teo != 0:
                                            examen_teo = Decimal(examen_teo).quantize(Decimal(10)**-2)
                                        # grado_fecha = inscripcion.recordacademico_set.get(asignatura__id=ASIGNATURA_EDU_VIAL).fecha
                                        if RecordAcademico.objects.filter(inscripcion=inscripcion,asignatura = teoria.asignatura_id).exists():
                                            grado_fecha = inscripcion.recordacademico_set.get(asignatura=teoria.asignatura_id).fecha
                                    else:
                                        examen_teo = 0
                                        grado_fecha = ""
                                    # if inscripcion.recordacademico_set.filter(asignatura__id=ASIGNATURA_PRACTICAS_CONDU).exists():
                                    if PromedioNotasGrado.objects.filter(carrera=inscripcion.carrera,practica=True,activo=True).exists():
                                        # examen_prac = inscripcion.recordacademico_set.get(asignatura__id=ASIGNATURA_PRACTICAS_CONDU).nota
                                        practica=PromedioNotasGrado.objects.filter(carrera=inscripcion.carrera,practica=True,activo=True)[:1].get()
                                        try:
                                            if inscripcion.recordacademico_set.filter(asignatura=practica.asignatura_id).exists():
                                                examen_prac = inscripcion.recordacademico_set.get(asignatura=practica.asignatura_id).nota
                                            else:
                                                examen_prac = 0
                                        except Exception as t:
                                            examen_prac = RecordAcademico.objects.filter(asignatura=practica.asignatura_id)[:1].get()
                                            return HttpResponse(json.dumps({"result":str(inscripcion)+' Revisar Record de: '+str(examen_prac.asignatura.nombre)}),content_type="application/json")
                                    else:
                                        examen_prac = 0

                                    # notal_final = ((promedio + examen_teo + examen_prac)/3).quantize(Decimal(10)**-2)
                                    notal_final = ((promedio + Decimal(examen_teo) + Decimal(examen_prac))/3).quantize(Decimal(10)**-2)

                                    if notal_final >= 16:
                                        equivale = EquivalenciaCondu.objects.get(equivale=notal_final)
                                        equivalencia = equivale.nombre
                                    else:
                                        equivalencia = 'REPROBADO'

                                    estudiantexgraduar = GraduadoConduccion(inscripcion=inscripcion,
                                                                            nombres =inscripcion.persona.nombre_completo_inverso(),
                                                                            promedio = promedio,
                                                                            examen_teorico = examen_teo,
                                                                            examen_practico = examen_prac,
                                                                            nota_final = notal_final,
                                                                            equivalente = equivalencia,
                                                                            periodo = periodo)
                                    estudiantexgraduar.save()
                                    if grado_fecha:
                                        estudiantexgraduar.fecha_grado=grado_fecha
                                        estudiantexgraduar.save()
                                except Exception as ex:
                                    return HttpResponse(json.dumps({"result":str(inscripcion)}),content_type="application/json")
                             n_acta =GraduadoConduccion.objects.all().exclude(numero_acta=None)

                             if not n_acta:
                                 num_acta = 0
                             else:
                                acta = GraduadoConduccion.objects.all().order_by('-numero_acta').exclude(numero_acta=None)[:1].get()
                                num_acta = acta.numero_acta
                             # result=[]
                             if GraduadoConduccion.objects.filter(numero_acta=None).order_by('nombres').exists():
                                 grad = GraduadoConduccion.objects.filter(numero_acta=None).order_by('nombres')
                                 for graduados in grad:
                                     num_acta = num_acta + 1
                                     graduados.numero_acta=num_acta
                                     graduados.save()

                                     #Obtain client ip address
                                     client_address = ip_client_address(request)

                                     # Log de Graduar en Conduccion
                                     LogEntry.objects.log_action(
                                           user_id         = request.user.pk,
                                           content_type_id = ContentType.objects.get_for_model(graduados).pk,
                                           object_id       = graduados.id,
                                           object_repr     = force_str(graduados),
                                           action_flag     = DELETION,
                                           change_message  = 'Adicionado Graduado Conduccion (' + client_address + ')' )

                                 result['mensaje']  = 'ok'
                             # return HttpResponse(json.dumps(result),content_type="application/json")
                             return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                         else:
                              # return HttpResponse(json.dumps(result),content_type="application/json")
                              return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

                elif action == 'validoexamen':
                    try:
                        inscripcionexamen = InscripcionExamen.objects.get(id=request.POST['idinscripexam'])
                        if not inscripcionexamen.valida:
                            for i in InscripcionExamen.objects.filter(valida=True,tituloexamencondu=inscripcionexamen.tituloexamencondu,inscripcion=inscripcionexamen.inscripcion):
                                i.valida = False
                                i.save()
                            inscripcionexamen.valida = True
                            puntaje = inscripcionexamen.puntaje
                            mensaje = 'Activando Examen'
                        else:
                            inscripcionexamen.valida = False
                            puntaje = 0
                            mensaje = 'Desactivando Examen'
                        inscripcionexamen.save()
                        if inscripcionexamen.puntaje >= NOTA_PARA_EXAMEN_CONDUCCION:
                            aprobado=True
                        else:
                            aprobado=False
                        if RecordAcademico.objects.filter( inscripcion=inscripcionexamen.inscripcion,asignatura=inscripcionexamen.tituloexamencondu.asignatura).exists():
                            recordacademico = RecordAcademico.objects.filter(inscripcion=inscripcionexamen.inscripcion,asignatura=inscripcionexamen.tituloexamencondu.asignatura)[:1].get()
                            recordacademico.nota=float(puntaje)
                            recordacademico.aprobada=aprobado
                            recordacademico.fecha=datetime.now().date()
                            # mensaje = "Editando"
                            recordacademico.save()
                        if HistoricoRecordAcademico.objects.filter( inscripcion=inscripcionexamen.inscripcion,asignatura=inscripcionexamen.tituloexamencondu.asignatura).exists():
                            historico = HistoricoRecordAcademico.objects.filter(inscripcion=inscripcionexamen.inscripcion,asignatura=inscripcionexamen.tituloexamencondu.asignatura)[:1].get()
                            historico.nota=float(puntaje)
                            historico.aprobada=aprobado
                            historico.fecha=datetime.now().date()
                            # mensaje = "Editando"
                            historico.save()
                        detvalidaexamen = Detvalidaexamen(
                                            inscripcionexamen = inscripcionexamen,
                                            observacion = request.POST['observacionvali'],
                                            usuario = request.user,
                                            fecha = datetime.now(),
                                            activo = inscripcionexamen.valida)
                        detvalidaexamen.save()
                        #Obtain client ip address
                        client_address = ip_client_address(request)

                        # Log de Graduar en Conduccion
                        LogEntry.objects.log_action(
                           user_id         = request.user.pk,
                           content_type_id = ContentType.objects.get_for_model(inscripcionexamen).pk,
                           object_id       = inscripcionexamen.id,
                           object_repr     = force_str(inscripcionexamen),
                           action_flag     = DELETION,
                           change_message  = mensaje+ ' de Grado de  Conduccion (' + client_address + ')' )

                        return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                    except Exception as ex:
                        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

                elif action=='eliminarinscripcion':
                    inscripcion = Inscripcion.objects.filter(pk=request.POST['id'])[:1].get()
                    try:
                      datos = requests.get('https://crm.itb.edu.ec/api',
                                                    params={'a': 'actualizarestadoinscrito', 'idinscrito': str(inscripcion.id)},verify=False)
                    except requests.Timeout:
                        print('Error Timeout')
                        return  HttpResponseRedirect('/inscripciones?info=Estudiante ' +str(inscripcion)+ ' Error de Timeout con el servidor Crm')
                    except requests.ConnectionError:
                        print('Error Conexion')
                        return  HttpResponseRedirect('/inscripciones?info=Estudiante ' +str(inscripcion)+ ' Error de Conexion con el servidor Crm')

                    if datos.status_code == 200:
                       datos=datos.json()
                       if datos['result']=='ok':
                            if inscripcion.total_pagado()==0:
                                estudiante=elimina_tildes(inscripcion.persona.nombre_completo_inverso())
                                user_inscrip = inscripcion.persona.usuario.id
                                usuario= User.objects.get(pk=user_inscrip)

                                #Obtain client ip address
                                client_address = ip_client_address(request)

                                # Log de BORRAR RECORD
                                LogEntry.objects.log_action(
                                 user_id         = request.user.pk,
                                 content_type_id = ContentType.objects.get_for_model(inscripcion).pk,
                                 object_id       = inscripcion.id,
                                 object_repr     = force_str(inscripcion),
                                 action_flag     = DELETION,
                                 change_message  = 'Elimimada Inscripcion (' + client_address + ')' +str(estudiante))

                                usuario.delete()
                                return HttpResponseRedirect('/?info=Inscripcion Eliminada')
                            else:
                                return  HttpResponseRedirect('/inscripciones?info=Estudiante ' +str(inscripcion)+ ' tiene facturas canceladas. No se puede eliminar')
                       else:
                           return  HttpResponseRedirect('/inscripciones?info=Estudiante ' +str(inscripcion)+ datos['message'])

                    else:
                        return  HttpResponseRedirect('/inscripciones?info=Estudiante ' +str(inscripcion)+ 'Problema con el Servidor Crm')


                elif action=='aprobarvinculacion':
                    try:
                        inscripcion = Inscripcion.objects.filter(pk=request.POST['id'])[:1].get()
                        listavinculacionaprueba = json.loads(request.POST['data'])
                        estudiantes_aprobados=[]
                        if request.POST['revisionestud']=='true' and request.POST['revisionproyecto']=='true' and request.POST['revisiondocente']=='true':
                            estudiante=True
                            proyecto=True
                            docente=True

                            for d in listavinculacionaprueba:
                                vincu = EstudianteVinculacion.objects.get(id=int(d['idvinculacion']))
                                if AprobacionVinculacion.objects.filter(inscripcion=inscripcion,estudiantevinculacion=vincu).exists():
                                    aprobacion = AprobacionVinculacion.objects.filter(inscripcion=inscripcion,estudiantevinculacion=vincu)[:1].get()
                                    if not aprobacion.tiene_aprobacion(vincu.actividad):
                                        aprobacion.revisionestudiante= estudiante
                                        aprobacion.revisionproyecto= proyecto
                                        aprobacion.revisiondocente= docente
                                        aprobacion.comentarios=request.POST['comentarios']
                                        aprobacion.usuario = request.user
                                        aprobacion.fecha = datetime.now()
                                        aprobacion.estudiantevinculacion=vincu

                                else:
                                    aprobacion = AprobacionVinculacion(inscripcion_id = request.POST['id'],
                                                                       revisionestudiante = estudiante,
                                                                       revisionproyecto = proyecto,
                                                                       revisiondocente = docente,
                                                                       comentarios = request.POST['comentarios'],
                                                                       usuario = request.user,
                                                                       fecha = datetime.now(),estudiantevinculacion=vincu)
                                aprobacion.save()

                                if not inscripcion.malla_inscripcion().malla.nueva_malla:
                                    asig = Asignatura.objects.get(pk=ASIG_VINCULACION)
                                    horas_va1= AprobacionVinculacion.objects.filter(estudiantevinculacion__inscripcion=inscripcion,revisionestudiante=True,revisionproyecto=True,revisiondocente=True).aggregate(Sum('estudiantevinculacion__horas'))['estudiantevinculacion__horas__sum'] if AprobacionVinculacion.objects.filter(estudiantevinculacion__inscripcion=inscripcion,revisionestudiante=True,revisionproyecto=True,revisiondocente=True).exists() else 0
                                    if (horas_va1 if horas_va1!=None else 0 )== HORAS_VINCULACION :
                                        if aprobacion.tiene_aprobacion(vincu.actividad):
                                            fechaaprobacion=aprobacion.fecha.date()
                                        else:
                                            fechaaprobacion=datetime.now().date()

                                        if HistoricoRecordAcademico.objects.filter(inscripcion=inscripcion,asignatura=asig).exists():
                                            historico = HistoricoRecordAcademico.objects.filter(inscripcion=inscripcion,asignatura=asig)[:1].get()
                                            historico.nota=100
                                            historico.asistencia=100
                                            historico.fecha=datetime.now().date()
                                            historico.aprobada=True
                                            historico.convalidacion=False
                                            historico.pendiente=False
                                        else:
                                            historico = HistoricoRecordAcademico(inscripcion=inscripcion,
                                                                        asignatura=asig,
                                                                        nota=100,
                                                                        asistencia=100,
                                                                        fecha=fechaaprobacion,
                                                                        aprobada=True,
                                                                        convalidacion=False,
                                                                        pendiente=False)
                                        historico.save()

                                        if RecordAcademico.objects.filter(inscripcion=inscripcion,asignatura=asig).exists():
                                            record = RecordAcademico.objects.filter(inscripcion=inscripcion,asignatura=asig)[:1].get()
                                            record.nota=100
                                            record.asistencia=100
                                            record.fecha=datetime.now().date()
                                            record.aprobada=True
                                            record.convalidacion=False
                                            record.pendiente=False
                                        else:
                                            record = RecordAcademico(inscripcion=inscripcion, asignatura=asig,
                                                                nota=100, asistencia=100,
                                                                fecha=datetime.now().date(), aprobada=True,
                                                                convalidacion=False, pendiente=False)
                                        record.save()

                                client_address = ip_client_address(request)
                                # aprobacion.correo_aprobacionvinculacion(request.user,'SE HA APROBADO Y AGREGADO LA NOTA DE VINCULACION CON LA COMUNIDAD',estudiantes_aprobados)
                                # Log de Aprobacion Vinculacion
                                LogEntry.objects.log_action(
                                 user_id         = request.user.pk,
                                 content_type_id = ContentType.objects.get_for_model(inscripcion).pk,
                                 object_id       = inscripcion.id,
                                 object_repr     = force_str(inscripcion),
                                 action_flag     = ADDITION,
                                 change_message  = 'Adicionada Nota de Vinculacion (' + client_address + ')' + str(inscripcion))
                                estudiantes_aprobados.append((inscripcion.persona.nombre_completo(),elimina_tildes(inscripcion.carrera.nombre)))
                                #Obtain client ip address
                                client_address = ip_client_address(request)
                                # aprobacion.correo_aprobacionvinculacion(request.user,'SE HA APROBADO Y AGREGADO LA NOTA DE VINCULACION CON LA COMUNIDAD',estudiantes_aprobados)
                                aprobacion.correo_aprobacionvinculacion(request.user,'SE HA APROBADO VINCULACION CON LA COMUNIDAD',estudiantes_aprobados)
                                # Log de Aprobacion Vinculacion
                                LogEntry.objects.log_action(
                                 user_id         = request.user.pk,
                                 content_type_id = ContentType.objects.get_for_model(inscripcion).pk,
                                 object_id       = inscripcion.id,
                                 object_repr     = force_str(inscripcion),
                                 action_flag     = ADDITION,
                                 change_message  = 'Aprobacion Vinculacion (' + client_address + ')' + str(inscripcion))

                            return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")

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

                            for d in listavinculacionaprueba:
                                vincu = EstudianteVinculacion.objects.get(id=int(d['idvinculacion']))
                                #horas_va1= AprobacionVinculacion.objects.filter(estudiantevinculacion__inscripcion=vincu.inscripcion,revisionestudiante=True,revisionproyecto=True,revisiondocente=True).aggregate(Sum('estudiantevinculacion__horas'))['estudiantevinculacion__horas__sum']
                                #if (horas_va1 if horas_va1!=None else 0 )== HORAS_VINCULACION :
                                if AprobacionVinculacion.objects.filter(inscripcion=inscripcion,estudiantevinculacion=vincu).exists():
                                    aprobacion = AprobacionVinculacion.objects.filter(inscripcion=inscripcion,estudiantevinculacion=vincu)[:1].get()
                                    aprobacion.revisionestudiante= estudiante
                                    aprobacion.revisionproyecto= proyecto
                                    aprobacion.revisiondocente= docente
                                    aprobacion.comentarios=request.POST['comentarios']
                                    aprobacion.usuario = request.user
                                    aprobacion.fecha = datetime.now()
                                    aprobacion.estudiantevinculacion=vincu
                                else:
                                    aprobacion = AprobacionVinculacion(inscripcion_id = request.POST['id'],
                                                                       revisionestudiante = estudiante,
                                                                       revisionproyecto = proyecto,
                                                                       revisiondocente = docente,
                                                                       comentarios = request.POST['comentarios'],
                                                                       usuario = request.user,
                                                                       fecha = datetime.now(),estudiantevinculacion=vincu)
                                aprobacion.save()

                            #Obtain client ip address
                            client_address = ip_client_address(request)

                            # Log de Revision Vinculacion
                            LogEntry.objects.log_action(
                             user_id         = request.user.pk,
                             content_type_id = ContentType.objects.get_for_model(inscripcion).pk,
                             object_id       = inscripcion.id,
                             object_repr     = force_str(inscripcion),
                             action_flag     = CHANGE,
                             change_message  = 'Revision Vinculacion (' + client_address + ')' +str(inscripcion))

                        return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                    except Exception as ex:
                        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")


                elif action=='solicitar':
                    adjunto=False
                    try:
                        f = SolicitudSecretariaAlumnosForm(request.POST,request.FILES)
                        if f.is_valid():
                            inscripcion = Inscripcion.objects.get(id=request.POST['idinscrip'])
                            print('ingreso al is valid')
                            if not 'pr' in request.POST:
                                solicitud = SolicitudSecretariaDocente(persona=inscripcion.persona,
                                                                       tipo=f.cleaned_data['tipo'],
                                                                       descripcion=f.cleaned_data['descripcion'],
                                                                       fecha = datetime.now(),
                                                                       hora = datetime.now().time(),
                                                                       cerrada = False)
                                solicitud.save()
                            else:
                                print('ingreso A GUARDAR ')
                                tipoespecie = TipoSolicitudSecretariaDocente.objects.get(pk=ID_TIPO_SOLICITUD)
                                solicitud = SolicitudSecretariaDocente(persona=inscripcion.persona,
                                                                       tipo=tipoespecie,
                                                                       descripcion=f.cleaned_data['descripcion'],
                                                                       fecha = datetime.now(),
                                                                       hora = datetime.now().time(),
                                                                       cerrada = False)
                                solicitud.save()

                            opcion='Alumno'

                            if 'comprobante' in request.FILES:
                                solicitud.comprobante= request.FILES['comprobante']
                                solicitud.save()
                                adjunto=True

                            if EMAIL_ACTIVE:
                                # f.instance.mail_subject_nuevo()
                                lista=''
                                # OCastillo 17-05-2019
                                gruposexcluidos = [SISTEMAS_GROUP_ID]
                                lista = ''

                                lista = str(solicitud.persona.email)
                                hoy = datetime.now().today()
                                contenido = "Nueva Solicitud"
                                descripcion = "Estimado/a estudiante. Su solicitud ha sido recibida. Sera asignada al Departamento correspondiente. Puede ver el estado de la misma en el Sistema."
                                send_html_mail(contenido,
                                    "emails/nuevasolicitud.html", {'d': solicitud, 'fecha': hoy,'contenido': contenido,'descripcion':descripcion,'opcion':'1'},lista.split(','))

                                #traigo el correo del grupo a quien le corresponde el tipo de solicitud
                                if SolicitudesGrupo.objects.filter(tiposolic=solicitud.tipo,carrera=inscripcion.carrera.id).exists():
                                    grupo_solicitud=SolicitudesGrupo.objects.filter(tiposolic=solicitud.tipo,carrera=inscripcion.carrera.id).values('grupo')
                                    if ModuloGrupo.objects.filter(grupos__in=grupo_solicitud).exists():
                                        correo_solicitud=[]
                                        for correo_grupo in ModuloGrupo.objects.filter(grupos__in=grupo_solicitud):
                                            correo_solicitud.append(correo_grupo.correo)
                                            if lista:
                                                lista = lista+','+correo_grupo.correo
                                            else:
                                                lista = correo_grupo.correo

                                else:
                                    #Para el caso de una solicitud tipo general para todas las carreras
                                    if SolicitudesGrupo.objects.filter(tiposolic=solicitud.tipo,todas_carreras=True).exists():
                                        grupo_solicitud=SolicitudesGrupo.objects.filter(tiposolic=solicitud.tipo,todas_carreras=True).exclude(grupo__id__in=gruposexcluidos).values('grupo')
                                        if ModuloGrupo.objects.filter(grupos__in=grupo_solicitud).exists():
                                           correo_solicitud=[]
                                           for correo_grupo in ModuloGrupo.objects.filter(grupos__in=grupo_solicitud):
                                               correo_solicitud.append(correo_grupo.correo)
                                               if lista:
                                                    lista = lista+','+correo_grupo.correo
                                               else:
                                                    lista = correo_grupo.correo

                                hoy = datetime.now().today()
                                contenido = "Nueva Solicitud"

                                send_html_mail(contenido,
                                    "emails/nuevasolicitud.html", {'d': solicitud, 'fecha': hoy,'contenido': contenido,'adjunto':adjunto,'opcion':'2'},lista.split(','))
                                return HttpResponseRedirect("/inscripciones")
                        else:
                            if not 'pr' in request.POST:
                                return HttpResponseRedirect("/inscripciones")
                            else:
                                return HttpResponseRedirect("/inscripciones?error= Error en el formulario fichero o tamano no permitido")
                    except Exception as e:
                        print(str(e))
                        return HttpResponseRedirect("/inscripciones?error= Error ingrese nuevamente")

                elif action == 'verificacion':
                    result = {}
                    try:
                        inscripcion = Inscripcion.objects.get(id=request.POST['id'])
                        if request.POST['opc'] == 'titulo':
                            inscripcion.veriftit = True
                        elif request.POST['opc'] == 'cedula':
                            inscripcion.verifarchced = True
                        elif request.POST['opc'] == 'votacion':
                            inscripcion.verifvota = True
                        elif request.POST['opc'] == 'pasaporte':
                            inscripcion.verifarchpasp = True
                        elif request.POST['opc'] == 'foto':
                            inscripcion.verifoto = True
                        elif request.POST['opc'] == 'carnetdisca':
                            inscripcion.vericarnetd = True
                        elif request.POST['opc'] == 'certimsp':
                            inscripcion.vericertimsp = True
                        inscripcion.save()
                        result['result'] = 'ok'
                        return HttpResponse(json.dumps(result), content_type="application/json")
                    except Exception as e:
                        result['result'] = str(e)
                        return HttpResponse(json.dumps(result), content_type="application/json")

                #OCastillo 19-11-2021 funciones para generar tramites
                elif action =='addsolicitud':
                    try:
                        inscripcion = Inscripcion.objects.filter(pk=request.POST['inscripcion'])[:1].get()
                        persona = Persona.objects.filter(pk=inscripcion.persona.id)[:1].get()
                        solicitud = SolicitudOnline.objects.filter(pk=request.POST['solicitud'])[:1].get()
                        solicitudest=None
                        form =getattr(forms,solicitud.form,None)
                        f = form(request.POST)
                        if f.is_valid():
                            if solicitud.id == ID_SOLIC__ONLINE:
                                if Matricula.objects.filter(inscripcion=inscripcion).order_by('-fecha').exists():
                                    pass
                            if f.cleaned_data['tipoe'].id == ID_TIPO_SOLICITUD or f.cleaned_data['tipoe'].id == ESPECIE_JUSTIFICA_FALTA_AU:
                                if not 'comprobante' in request.FILES:
                                    return HttpResponseRedirect("/inscripciones?generartramite&id="+str(inscripcion.id)+ "&error=TODOS LOS CAMPOS SON OBLIGATORIOS")
                                if f.cleaned_data['tipoe'].relaciodocente:
                                    if not f.cleaned_data['materia']  or  not f.cleaned_data['profesor']:
                                        return HttpResponseRedirect("/inscripciones?generartramite&id="+str(inscripcion.id)+ "&error=TODOS LOS CAMPOS SON OBLIGATORIOS")
                                if len(f.cleaned_data['observacion']) > 500:
                                        return HttpResponseRedirect("/inscripciones?generartramite&id="+str(inscripcion)+ "&error=LA OBSERVACION EXCEDE CARACTERES PERMITIDOS(500)")

                            if f.cleaned_data['tipoe'].id == ESPECIE_JUSTIFICA_FALTA_AU:
                                if inscripcion.matricula():
                                    materiasig=MateriaAsignada.objects.filter(id=f.cleaned_data['materia'])[:1].get()
                                    matricula = inscripcion.matricula()
                                    leccionesGrupo = LeccionGrupo.objects.filter(fecha__lte=datetime.now(),profesor=f.cleaned_data['profesor'],materia__nivel__periodo__activo=True,lecciones__clase__materia= materiasig.materia,lecciones__asistencialeccion__matricula=matricula,lecciones__asistencialeccion__asistio=False,lecciones__asistencialeccion__fechaaprobacion=None).order_by('-fecha', '-horaentrada')
                                    cantidad = leccionesGrupo.count()
                                    if cantidad == 0:
                                         return  HttpResponseRedirect("/inscripciones?action=generartramite&id="+str(inscripcion.id)+ "&error=NO TIENE INASISTENCIAS CON EL DOCENTE SELECCIONADO")
                            # print((f))
                            # if not SolicitudEstudiant e.objects.filter(solicitud=solicitud).exists():
                            if int(request.POST['id']) != 0:
                                if solicitud.libre:
                                    solicitudest = SolicitudEstudiante.objects.filter(id=request.POST['id'])[:1].get()
                                    solicitudest.observacion=f.cleaned_data['observacion']
                                    solicitudest.tipoe = f.cleaned_data['tipoe']
                                    solicitudest.celular=f.cleaned_data['celular']
                                    solicitudest.oficina= f.cleaned_data['oficina']
                                    solicitudest.presencial=True
                                else:
                                    solicitudest = SolicitudEstudiante.objects.filter(id=request.POST['id'])[:1].get()
                                    solicitudest.correo=f.cleaned_data['correo']
                                    solicitudest.celular=f.cleaned_data['celular']
                                    solicitudest.oficina= f.cleaned_data['oficina']
                                    solicitudest.domicilio=f.cleaned_data['domicilio']
                                    solicitudest.fecha=datetime.now()
                                    solicitudest.presencial=True
                            else:
                                if solicitud.libre:
                                    solicitudest = SolicitudEstudiante(solicitud=solicitud,
                                                                      inscripcion=inscripcion,
                                                                      observacion=f.cleaned_data['observacion'],
                                                                      tipoe = f.cleaned_data['tipoe'],
                                                                      correo=f.cleaned_data['correo'],
                                                                      celular=f.cleaned_data['celular'],
                                                                      fecha=datetime.now(),presencial=True)
                                else:
                                    solicitudest = SolicitudEstudiante(solicitud=solicitud,
                                                                      inscripcion=inscripcion,
                                                                      correo=f.cleaned_data['correo'],
                                                                      celular=f.cleaned_data['celular'],
                                                                      oficina = f.cleaned_data['oficina'],
                                                                      domicilio=f.cleaned_data['domicilio'],
                                                                      fecha=datetime.now(),presencial=True)
                            solicitudest.save()
                            if 'comprobante' in request.FILES:
                                solicitudest.comprobante= request.FILES['comprobante']
                                solicitudest.save()
                                adjunto=True
                            inscripcion.persona.email =solicitudest.correo
                            inscripcion.persona.telefono=solicitudest.celular
                            inscripcion.persona.save()
                            if solicitudest.tipoe:
                                if solicitudest.tipoe.relaciodocente:
                                    solicitudest.materia_id = f.cleaned_data['materia']
                                    solicitudest.profesor= f.cleaned_data['profesor']

                                if solicitudest.tipoe.relacionaasig:
                                    solicitudest.asignatura = f.cleaned_data['asignatura']
                                solicitudest.save()

                            if 'tipo' in f.cleaned_data:
                                solicitudest.tipo = f.cleaned_data['tipo']
                            if 'tema' in f.cleaned_data:
                                solicitudest.tema = f.cleaned_data['tema']
                            solicitudest.save()

                            if solicitudest.tipoe.id == ESPECIE_JUSTIFICA_FALTA_AU:
                                if solicitudest.inscripcion.matricula():
                                    matricula = solicitudest.inscripcion.matricula()
                                    leccionesGrupo = LeccionGrupo.objects.filter(fecha__lte=solicitudest.fecha,profesor=solicitudest.profesor,materia__nivel__periodo__activo=True,lecciones__clase__materia=solicitudest.materia.materia,lecciones__asistencialeccion__matricula=matricula,lecciones__asistencialeccion__asistio=False,lecciones__asistencialeccion__fechaaprobacion=None).order_by('-fecha', '-horaentrada')
                                    cantidad = leccionesGrupo.count()
                                    if cantidad > 5:
                                        cantidad = 5
                                    return HttpResponseRedirect("/inscripciones?action=generartramite2&id="+str(solicitudest.id)+"&cantidad="+str(cantidad))
                            if not solicitudest.tipoe.es_especie:
                                solicitudsec = SolicitudSecretariaDocente(persona=persona,
                                                                   solicitudestudiante=solicitudest,
                                                                   tipo=solicitudest.tipoe.tiposolicitud,
                                                                   descripcion=solicitudest.observacion,
                                                                   fecha = datetime.now(),
                                                                   hora = datetime.now().time(),
                                                                   cerrada = False)
                                solicitudsec.save()
                                adjunto=False
                                solicitudest.solicitado=True
                                solicitudest.save()
                                if 'comprobante' in request.FILES:
                                    solicitudsec.comprobante= request.FILES['comprobante']
                                    solicitudsec.save()
                                    adjunto=True
                                listasolicitudes=[]
                                coordinacion = Coordinacion.objects.filter(carrera=solicitudsec.solicitudestudiante.inscripcion.carrera)[:1].get()
                                for cdp in  CoordinacionDepartamento.objects.filter(coordinacion=coordinacion):
                                    if EspecieGrupo.objects.filter(departamento=cdp.departamento,tipoe=solicitudsec.solicitudestudiante.tipoe).exists():
                                        asistentes=None
                                        if cdp.departamento.id == 27:
                                            cajeros = SesionCaja.objects.filter(abierta=True).values('caja__persona')
                                            if HorarioAsistenteSolicitudes.objects.filter(fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time()).exists():
                                                 horarioasis = HorarioAsistenteSolicitudes.objects.filter(fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time()).values('usuario')
                                                 asistentes = AsistenteDepartamento.objects.filter(departamento=cdp.departamento,persona__usuario__id__in=horarioasis,persona__id__in=cajeros).exclude(puedereasignar=True).order_by('cantidadsol')
                                        else:
                                            if HorarioAsistenteSolicitudes.objects.filter(fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time()).exists():
                                                 horarioasis = HorarioAsistenteSolicitudes.objects.filter(fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time()).values('usuario')
                                                 asistentes = AsistenteDepartamento.objects.filter(departamento=cdp.departamento,persona__usuario__id__in=horarioasis).exclude(puedereasignar=True).order_by('cantidadsol')
                                        if asistentes:
                                            for asis in asistentes:
                                                asis.cantidadsol =asis.cantidadsol +1
                                                asis.save()
                                                solicitudsec.usuario = asis.persona.usuario
                                                solicitudsec.personaasignada =asis.persona
                                                solicitudsec.asignado=True
                                                solicitudsec.fechaasignacion = datetime.now()
                                                solicitudsec.usuarioasigna=asis.persona.usuario
                                                solicitudsec.departamento=asis.departamento
                                                solicitudsec.save()

                                                listasolicitudes.append(asis.persona.emailinst)
                                                break
                                if listasolicitudes:
                                    try:
                                         hoy = datetime.now().today()
                                         contenido = "  Solicitudes Asignadas"
                                         descripcion = "Ud. tiene solicitudes por atender"
                                         send_html_mail(contenido,
                                            "emails/notificacion_solicitud_adm.html", {'fecha': hoy,'contenido': contenido,'descripcion':descripcion,'opcion':'1'},listasolicitudes)
                                    except Exception as e:
                                        print((e))
                                        pass
                                if EMAIL_ACTIVE:
                                    gruposexcluidos = [SISTEMAS_GROUP_ID]
                                    lista=''
                                    lista = str(solicitudsec.persona.email)
                                    hoy = datetime.now().today()
                                    contenido = "Nueva Solicitud"
                                    descripcion = "Estimado/a estudiante. Su solicitud ha sido recibida. Sera asignada al Departamento correspondiente. Puede ver el estado de la misma en el Sistema."
                                    send_html_mail(contenido,
                                        "emails/nuevasolicitud.html", {'d': solicitudsec, 'fecha': hoy,'contenido': contenido,'descripcion':descripcion,'opcion':'1'},lista.split(','))

                                    #traigo el correo del grupo a quien le corresponde el tipo de solicitud
                                    if SolicitudesGrupo.objects.filter(tiposolic=solicitudsec.tipo,carrera=inscripcion.carrera.id).exists():
                                        grupo_solicitud=SolicitudesGrupo.objects.filter(tiposolic=solicitudsec.tipo,carrera=inscripcion.carrera.id).values('grupo')
                                        if ModuloGrupo.objects.filter(grupos__in=grupo_solicitud).exists():
                                            correo_solicitud=[]
                                            for correo_grupo in ModuloGrupo.objects.filter(grupos__in=grupo_solicitud):
                                                correo_solicitud.append(correo_grupo.correo)
                                                if lista:
                                                    lista = lista+','+correo_grupo.correo
                                                else:
                                                    lista = correo_grupo.correo
                                    else:
                                        #Para el caso de una solicitud tipo general para todas las carreras
                                        if SolicitudesGrupo.objects.filter(tiposolic=solicitudsec.tipo,todas_carreras=True).exists():
                                            if solicitudsec.tipo.sistema==True:
                                                grupo_solicitud=SolicitudesGrupo.objects.filter(tiposolic=solicitudsec.tipo,todas_carreras=True).values('grupo')
                                            else:
                                                grupo_solicitud=SolicitudesGrupo.objects.filter(tiposolic=solicitudsec.tipo,todas_carreras=True).exclude(grupo__id__in=gruposexcluidos).values('grupo')
                                            if ModuloGrupo.objects.filter(grupos__in=grupo_solicitud).exists():
                                               correo_solicitud=[]
                                               for correo_grupo in ModuloGrupo.objects.filter(grupos__in=grupo_solicitud):
                                                   correo_solicitud.append(correo_grupo.correo)
                                                   if lista:
                                                        lista = lista+','+correo_grupo.correo
                                                   else:
                                                        lista = correo_grupo.correo

                                    hoy = datetime.now().today()
                                    contenido = "Nueva Solicitud"
                                    send_html_mail(contenido,
                                        "emails/nuevasolicitud.html", {'d': solicitudsec, 'fecha': hoy,'contenido': contenido,'adjunto':adjunto,'opcion':'2'},lista.split(','))
                                    if 'comprobante' in request.FILES:
                                        pass

                                    return HttpResponseRedirect("/inscripciones?info=SE AGREGO CORRECTAMENTE")
                            else:
                                return HttpResponseRedirect("/inscripciones?action=generartramite2&id="+str(solicitudest.id))

                        else:
                            return HttpResponseRedirect("/inscripciones?generartramite&id=3&error=ERROR EN EL FORMULARIO DE SOLICITUD...LA OBSERVACION NO DEBE SUPERAR LOS 500 CARACTERES, VERIFIQUE EL PESO DEL DOCUMENTO Y SU EXTENSION")
                    except Exception as e:
                        print(e)
                        return HttpResponseRedirect("/inscripciones?error="+str(e))

                elif action =='consulta':
                    try:
                        data ={}
                        inscripcion = Inscripcion.objects.get(pk=request.POST['inscrip'])
                        tipoespecie = TipoEspecieValorada.objects.filter(pk=request.POST['tipo'])[:1].get()
                        if tipoespecie.informacion:
                            data['informacion'] = elimina_tildes(tipoespecie.informacion)
                        else:
                            data['informacion'] = 'bad'

                        #OCastillo 26-04-2022 validar si estudiante tiene deuda no permitir comprar especies de asentamiento de notas, examen ni recuperacion
                        if inscripcion.tiene_deuda():
                            if tipoespecie.id == ID_TIPO_ESPECIE_REG_NOTA or tipoespecie.id == ESPECIE_EXAMEN or tipoespecie.id == ESPECIE_RECUPERACION or tipoespecie.id == ESPECIE_MEJORAMIENTO:
                                data['informacion'] = 'bad'
                                data['result2'] = 'ESTIMADO ESTUDIANTE DEBE ESTAR AL DIA EN SUS PAGOS PARA REALIZAR ESTA SOLICITUD'
                                return HttpResponse(json.dumps(data), content_type="application/json")

                        if tipoespecie.id == EXAMEN_CONVALIDACION :
                            if inscripcion.carrera.validacionprofesional:
                                if ExamenConvalidacionIngreso.objects.filter(inscripcion=inscripcion,aprobada=True).exists():
                                        data['result'] = 'ESTUDIANTE YA TIENE APROBADO ESTE TRAMITE'
                                        return HttpResponse(json.dumps(data), content_type="application/json")
                                if not RubroInscripcion.objects.filter(rubro__inscripcion=inscripcion,rubro__cancelado=True).exists():
                                    data['result'] = 'PARA SOLICITAR EL TRAMITE ESTUDIANTE DEBE CANCELAR LA INSCRIPCION'
                                    return HttpResponse(json.dumps(data), content_type="application/json")
                            else:
                                data['result'] = 'LA CARRERA DEL ESTUDIANTE NO ADMITE ESTE TRAMITE'
                                return HttpResponse(json.dumps(data), content_type="application/json")

                        if tipoespecie.relaciodocente:
                            if not inscripcion.matricula() and tipoespecie.id == ESPECIE_JUSTIFICA_FALTA_AU:
                                data['result'] = 'ESTUDIANTE DEBE ESTAR MATRICULADO PARA SOLICITAR LA ESPECIE'
                                return HttpResponse(json.dumps(data), content_type="application/json")
                            materia=[]
                            # inscripcion = Inscripcion.objects.get(persona=persona)
                            if tipoespecie.id == ESPECIE_JUSTIFICA_FALTA_AU:
                                m = inscripcion.matricula()
                                fechamax = datetime.now() - timedelta(days=DIAS_ESPECIE)
                                if RubroEspecieValorada.objects.filter(tipoespecie=tipoespecie,rubro__inscripcion=inscripcion, aplicada=False,fecha__gte=fechamax).exclude(materia=None).exists():
                                   materiaid = RubroEspecieValorada.objects.filter(tipoespecie=tipoespecie,rubro__inscripcion=inscripcion,
                                                                               aplicada=False,fecha__gte=fechamax).distinct('materia').values('materia')

                                   materias= m.materia_asignada().filter().exclude(id__in=materiaid)
                                else:
                                   materias = m.materia_asignada().filter()
                                for m in materias:
                                    materia.append({'id':m.id,'asignatura': elimina_tildes(m.materia.asignatura.nombre) })
                            else:
                                for m in Matricula.objects.filter(inscripcion=inscripcion):
                                    fechamax = datetime.now() - timedelta(days=DIAS_ESPECIE)
                                    if RubroEspecieValorada.objects.filter(tipoespecie=tipoespecie,rubro__inscripcion=inscripcion, aplicada=False,fecha__gte=fechamax).exclude(materia=None).exists():
                                       materiaid = RubroEspecieValorada.objects.filter(tipoespecie=tipoespecie,rubro__inscripcion=inscripcion,
                                                                                   aplicada=False,fecha__gte=fechamax).distinct('materia').values('materia')
                                       materias= m.materia_asignada().filter().exclude(id__in=materiaid)
                                    else:
                                       materias = m.materia_asignada().filter()
                                    for m in materias:
                                        materia.append({'id':m.id,'asignatura': elimina_tildes(m.materia.asignatura.nombre) })
                            data['result'] = 'ok'
                            data['op'] = 'materia'
                            data['materias'] = materia
                            return HttpResponse(json.dumps(data), content_type="application/json")

                        elif tipoespecie.relacionaasig :
                            malla= inscripcion.malla_inscripcion().malla
                            asigrecord = RecordAcademico.objects.filter(inscripcion=inscripcion,aprobada=True).values('asignatura')
                            asignaturas = AsignaturaMalla.objects.filter(malla=malla).exclude(asignatura__id__in=asigrecord)
                            asignatura=[]
                            for a in asignaturas:
                                asignatura.append({'id':a.asignatura.id,'asignatura': elimina_tildes(a.asignatura.nombre) })
                            data['result'] = 'ok'
                            data['op'] = 'asignatura'
                            data['asignatura'] = asignatura
                            return HttpResponse(json.dumps(data), content_type="application/json")
                        else:
                            data['result'] = 'ok'
                            return HttpResponse(json.dumps(data), content_type="application/json")
                    except Exception as e:
                        data['result'] = 'e'
                        return HttpResponse(json.dumps(data), content_type="application/json")

                elif action =='actuali_pract':  #metodo actualizar
                    try:
                        data={}
                        data['title'] = 'Actualizar Practica de Vinculacion a Nueva Malla'
                        if Inscripcion.objects.filter(pk=request.POST['iid']).exists():
                            if Inscripcion.objects.filter(pk=request.POST['id']).exists():
                                anterior = Inscripcion.objects.filter(pk=request.POST['iid'])[:1].get() #obtiene el objeto anterior
                                inscripcion = Inscripcion.objects.filter(pk=request.POST['id'])[:1].get()  #donde se va a guardar
                                vinculacion = EstudianteVinculacion.objects.filter(inscripcion = anterior)

                                for v in vinculacion:
                                    # if EstudianteVinculacion.objects.filter(inscripcion=anterior).exists():
                                    for a in AprobacionVinculacion.objects.filter(estudiantevinculacion=v):
                                        a.inscripcion=inscripcion
                                        a.save()
                                    v.inscripcion = inscripcion
                                    v.save()
                                # Obtain client ip address
                                client_address = ip_client_address(request)

                                # Log de Revision Vinculacion
                                LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(inscripcion).pk,
                                object_id       = inscripcion.id,
                                object_repr     = force_str(inscripcion),
                                action_flag     = CHANGE,
                                change_message  = 'Actualizacion Vinculacion (' + client_address + ')' +str(inscripcion))
                                return HttpResponse(json.dumps({"result":"ok", "nueva":str(inscripcion.id)}),content_type="application/json")
                            else:
                                return HttpResponse(json.dumps({"result":"bad","error":"No existe la nueva inscripcion"}),content_type="application/json")
                        else:
                            return HttpResponse(json.dumps({"result":"bad","error":"No existe la inscripcion anterior"}),content_type="application/json")

                    except Exception as e:
                        return HttpResponse(json.dumps(e), content_type="application/json")

                elif action =='consultadocente':
                    data = {}
                    tipoespecie = TipoEspecieValorada.objects.filter(pk=request.POST['tipo'])[:1].get()
                    try:
                        materiaasignada = MateriaAsignada.objects.filter(pk=request.POST['materia'])[:1].get()
                        # OCastillo 12-09-2022 para las materias en nivel cerrado solo se puede generar especie hasta 45 dias
                        if tipoespecie.id == ID_TIPO_ESPECIE_REG_NOTA or tipoespecie.id == ESPECIE_EXAMEN or tipoespecie.id == ESPECIE_RECUPERACION or tipoespecie.id == ESPECIE_MEJORAMIENTO:
                            if materiaasignada.matricula.nivel.cerrado==True:
                                fechacierre=materiaasignada.matricula.nivel.fechacierre
                                if (datetime.now().date() - materiaasignada.matricula.nivel.fechacierre).days > 45:
                                    data['docente'] = 'bad'
                                    data['mensaje'] = 'ESTIMADO ESTUDIANTE SE HA VENCIDO EL PLAZO DE ASENTAMIENTO DE NOTAS. EL NIVEL FUE CERRADO EL: ' +str(fechacierre)+ ' FAVOR COMUNICARSE CON SU COORDINACION'
                                    return HttpResponse(json.dumps(data), content_type="application/json")
                        profesores=[]
                        arreglo_pr=[]
                        for p in materiaasignada.materia.profesores_materia():
                            if not p.profesor.id in arreglo_pr:
                                if p.profesor.activo==True:
                                    arreglo_pr.append(p.profesor.id)
                                    profesores.append({'id':p.profesor.id,'profesor': elimina_tildes(p.profesor.persona.nombre_completo_inverso()) })
                        if len(profesores)!=0:
                            data['result'] = 'ok'
                            data['op'] = 'materia'
                            data['profesores'] = profesores
                            return HttpResponse(json.dumps(data), content_type="application/json")
                        else:
                           data['docente'] = 'bad'
                           data['mensaje']='Docente de la materia escogida no esta activo'
                           return HttpResponse(json.dumps(data), content_type="application/json")
                    except Exception as e:
                        data['result'] = 'e'
                        return HttpResponse(json.dumps(data), content_type="application/json")

                elif action == 'consulta_departamento2':
                    data = {}
                    try:
                        especies = []
                        especie_grupo=[]
                        especies.append({'id':'---','nombre': '---','valor': '----' })
                        departamento = Departamento.objects.get(pk=request.POST['depa'])
                        especie_grupo = EspecieGrupo.objects.filter(departamento=departamento, tipoe__id__in=ESPECIES_ASUNTOS_ESTUDIANTILES)
                        tipos_especies = TipoEspecieValorada.objects.filter(id__in=especie_grupo.values('tipoe'),activa=True).order_by('nombre')

                        for te in tipos_especies:
                            precio = 0
                            if te.precio:
                                if te.precio>0:
                                    precio=te.precio
                            especies.append({'id':te.id,'nombre': elimina_tildes(te.nombre),'valor': precio })
                        print(especies)
                        data['result'] = 'ok'
                        data['especies'] = especies
                        return HttpResponse(json.dumps(data), content_type="application/json")

                    except Exception as e:
                        print(e)
                        data['result'] = str(e)
                        return HttpResponse(json.dumps(data), content_type="application/json")

                elif action == 'consulta_departamento':
                    data = {}
                    try:
                        especies = []
                        especie_grupo=[]
                        especies.append({'id':'---','nombre': '---','valor': '----' })
                        departamento = Departamento.objects.get(pk=request.POST['depa'])
                        especie_grupo = EspecieGrupo.objects.filter(departamento=departamento)
                        tipos_especies = TipoEspecieValorada.objects.filter(id__in=especie_grupo.values('tipoe'),activa=True).exclude(id__in=[ESPECIE_ASENTAMIENTOCONVENIO_SINVALOR,ESPECIE_ASENTAMIENTOCONVENIO_CONVALOR]).order_by('nombre')

                        for te in tipos_especies:
                            precio = 0
                            if te.precio:
                                if te.precio>0:
                                    precio=te.precio
                            especies.append({'id':te.id,'nombre': elimina_tildes(te.nombre),'valor': precio })
                        print(especies)
                        data['result'] = 'ok'
                        data['especies'] = especies
                        return HttpResponse(json.dumps(data), content_type="application/json")

                    except Exception as e:
                        print(e)
                        data['result'] = 'e'
                        return HttpResponse(json.dumps(data), content_type="application/json")

                elif action == 'addUniformeAdmisiones':
                    try:
                        inscripcion = Inscripcion.objects.get(pk=request.POST['id'])
                        talla = TallaUniforme.objects.get(pk=request.POST['talla'])
                        hoy = datetime.now().date()
                        entregado = False
                        fechaEntrega = None
                        usuarioEntrega = None
                        if request.POST['entregado'] == '1':
                            entregado = True
                            fechaEntrega = hoy
                            usuarioEntrega = request.user
                        if EntregaUniformeAdmisiones.objects.filter(inscripcion=inscripcion).exists():
                            entregaUniforme = EntregaUniformeAdmisiones.objects.filter(inscripcion=inscripcion).order_by('-id')[:1].get()
                            entregaUniforme.talla = talla
                            entregaUniforme.entregado = entregado
                            entregaUniforme.fechaentrega = fechaEntrega
                            entregaUniforme.save()
                        else:
                            entregaUniforme = EntregaUniformeAdmisiones(
                                fecha=hoy,
                                inscripcion=inscripcion,
                                usuario = request.user,
                                talla=talla,
                                entregado=entregado,
                                fechaentrega=fechaEntrega,
                                usuarioentrega=usuarioEntrega
                            )
                            entregaUniforme.save()
                        if 'foto' in request.FILES:
                            entregaUniforme.foto = request.FILES['foto']
                            entregaUniforme.save()
                        return HttpResponse(json.dumps({'result':'ok'}), content_type="application/json")
                    except Exception as e:
                        print(e)
                        return HttpResponse(json.dumps({'result': 'bad', 'mensaje': str(e)}), content_type="application/json")

                elif action == 'obtenerUniformeAdmision':
                    try:
                        print(request.POST)
                        inscripcion = Inscripcion.objects.get(pk=request.POST['id'])
                        if EntregaUniformeAdmisiones.objects.filter(inscripcion=inscripcion).exists():
                            entregaUniforme = EntregaUniformeAdmisiones.objects.filter(inscripcion=inscripcion).order_by('-id')[:1].get()
                            data = {
                                'usuario': entregaUniforme.usuario.username,
                                'fecha': str(entregaUniforme.fecha.date()),
                                'talla': entregaUniforme.talla.id,
                                'entregado': '1' if entregaUniforme.entregado else '0',
                                'usuarioEntrega': entregaUniforme.usuarioentrega.username if entregaUniforme.usuarioentrega else '',
                                'fechaEntrega': str(entregaUniforme.fechaentrega.date()) if entregaUniforme.fechaentrega else '',
                                'foto': str(entregaUniforme.foto) if entregaUniforme.foto else ''
                            }

                            return HttpResponse(json.dumps({'result':'ok', 'data':data}), content_type="application/json")
                        return HttpResponse(json.dumps({'result':'bad'}), content_type="application/json")
                    except Exception as e:
                        print(e)
                        return HttpResponse(json.dumps({'result': 'bad', 'mensaje': str(e)}), content_type="application/json")

                return HttpResponseRedirect("/inscripciones")

            except Exception as ex:
                return HttpResponseRedirect("/?info="+str(ex))
        else:
            data = {'title': 'Listado de Inscripciones'}
            addUserData(request,data)
            try:
                if 'action' in request.GET:
                    action = request.GET['action']
                    if action=='activation':
                        pass
                        # d.activo = not d.activo
                        # d.save()
                        # return HttpResponseRedirect("/docentes")

                    elif action=='add':
                        # if True:
                        if request.user.has_perm('sga.change_inscripcion') or request.user.has_perm('sga.add_inscripcionvendedor') :
                            if DEFAULT_PASSWORD == 'itb' and not request.user.has_perm('auth.add_group'):
                                return HttpResponseRedirect("/?info= NO TIENE ACCESO A ESTA OPCION")
                        # if request.user.has_perm('sga.change_inscripcion') or  request.user.has_perm('sga.add_inscripcionvendedor') :
                            data['title'] = 'Nueva Inscripcion de Alumno'
                            if 'error' in request.GET:
                                data['error'] = request.GET['error']
                            if 'error1' in request.GET:
                                data['error1'] = request.GET['error1']
                            if not CENTRO_EXTERNO:
                                if 'preinscripcion' in request.GET:
                                    colegio=''
                                    data['preinscripcion'] = request.GET['preinscripcion']
                                    preins = PreInscripcion.objects.filter(pk=request.GET['preinscripcion'])[:1].get()
                                    data['preins']=preins
                                    if preins.carrera.nombre == 'CONGRESO DE PEDAGOGIA':
                                        if Colegio.objects.filter(pk=1).exists():
                                            colegio= Colegio.objects.filter(pk=1)[:1].get()
                                            data['colegiopre']=colegio
                                    insf = InscripcionForm(initial={'nombres' : preins.nombres,'apellido1':preins.apellido1,
                                                                    'apellido2':preins.apellido2,'cedula':preins.cedula,'nacimiento':preins.nacimiento,
                                                                    'email':preins.email,'sexo':preins.sexo,'telefono':preins.celular,'telefono_conv':preins.telefono,
                                                                    'carrera':preins.carrera,'modalidad':preins.modalidad,'sesion':preins.seccion,
                                                                    'grupo':preins.grupo, 'colegio':preins.colegio,'especialidad':preins.especialidad,'provinciaresid':preins.provincia,
                                                                    'cantonresid':preins.canton,'direccion':preins.calleprincipal,'direccion2':preins.callesecundaria,
                                                                    'num_direccion':preins.numerocasa,'anuncio':preins.tipoanuncio})
                                    insf.set_add_mode(request.user)
                                elif 'referido' in request.GET:
                                        data['referido'] = request.GET['referido']
                                        ref = ReferidosInscripcion.objects.filter(pk=request.GET['referido'])[:1].get()
                                        insf = InscripcionForm(initial={'nombres' : ref.nombres,'apellido1':ref.apellido1,
                                                                        'apellido2':ref.apellido2,'cedula':ref.cedula,
                                                                        'extranjero': ref.extranjero,'pasaporte':ref.pasaporte,
                                                                        'email':ref.email,'sexo':ref.sexo,'telefono':ref.telefono,'telefono_conv':ref.telefono_conv})
                                        insf.set_add_mode(request.user)

                                # OCU 13-julio-2016 traigo informacion de inscripcionaspitantes
                                elif 'insasp' in request.GET:
                                        data['insasp'] = request.GET['insasp']
                                        aspirante = InscripcionAspirantes.objects.filter(pk=request.GET['insasp'])[:1].get()
                                        insf = InscripcionForm(initial={'nombres' : aspirante.nombres,'apellido1': aspirante.apellido1,
                                                                     'apellido2' : aspirante.apellido2,'email': aspirante.email,
                                                                     'cedula' : aspirante.cedula,'pasaporte': aspirante.pasaporte,'extranjero': aspirante.extranjero,'sexo':aspirante.sexo,
                                                                     'telefono': aspirante.telefono,'telefono_conv': aspirante.telefono_conv})
                                        insf.set_add_mode(request.user)
                                else:

                                    insf = InscripcionForm(initial={'fecha': datetime.now()})
                                    insf.set_add_mode(request.user)
                            else:
                                insf = InscripcionCextForm(initial={'fecha': datetime.now()})
                            data['form'] = insf
                            data['utiliza_grupos_alumnos'] = UTILIZA_GRUPOS_ALUMNOS
                            data['grupos_abiertos'] = Grupo.objects.filter(abierto=True).order_by('-nombre')
                            data['centroexterno'] = CENTRO_EXTERNO
                            data['DEFAULT_PASSWORD'] = DEFAULT_PASSWORD
                            data['inscripcion_conduccion'] = INSCRIPCION_CONDUCCION
                            data['carrera_recuperacion'] = ID_CARRERA_RECUPERACION
                            return render(request ,"inscripciones/adicionarbs.html" ,  data)
                        else:
                            return HttpResponseRedirect("/?info= NO TIENE ACCESO A ESTA OPCION")

                    elif action == 'buscar':
                        cedula = request.GET['cedula']
                        estudiante = ''
                        if cedula:
                            if Inscripcion.objects.filter(persona__cedula=cedula).exclude(carrera__in=CARRERAS_ID_EXCLUIDAS_INEC).exists():
                                for b in Inscripcion.objects.filter(persona__cedula=cedula):
                                    estudiante = estudiante + str(b.persona.nombre_completo())
                                    carrera =str( b.carrera)
                                    nacimiento = b.persona.nacimiento
                                    sexo = b.persona.sexo.nombre
                                    modalidad=b.modalidad.nombre
                                    sesion=b.sesion.nombre
                                return HttpResponse(json.dumps({'result':'ok', 'estudiante': str(estudiante),'carrera':carrera,'nacimiento': nacimiento,'sexo': sexo,'modalidad':modalidad,'sesion':sesion}), content_type="application/json")
                            else:
                                return HttpResponse(json.dumps({'result':'bad'}),content_type="application/json")

                    elif action == 'buscarpas':
                        pasaporte = request.GET['pasaporte']
                        estudiante = ''

                        if pasaporte:
                            if Inscripcion.objects.filter(persona__pasaporte=pasaporte).exclude(carrera__in=CARRERAS_ID_EXCLUIDAS_INEC).exists():
                                for b in Inscripcion.objects.filter(persona__pasaporte=pasaporte):
                                    estudiante = estudiante + str(b.persona.nombre_completo())
                                    carrera =str( b.carrera)
                                    nacimiento = b.persona.nacimiento
                                    sexo = b.persona.sexo.nombre
                                    modalidad=b.modalidad.nombre
                                    sesion=b.sesion.nombre
                                return HttpResponse(json.dumps({'result':'ok', 'estudiante': str(estudiante),'carrera':carrera,'nacimiento': nacimiento,'sexo': sexo,'modalidad':modalidad,'sesion':sesion}), content_type="application/json")
                            else:
                                return HttpResponse(json.dumps({'result':'bad'}),content_type="application/json")

                    elif action=='edit':
                        if 'graduado' in request.GET:
                            data['graduado'] = request.GET['graduado']

                        inscripcion = Inscripcion.objects.get(pk=request.GET['id'])

                        if INSCRIPCION_CONDUCCION:
                            if FotoInstEstudiante.objects.filter(inscripcion=inscripcion).exists():
                                fotoinst = FotoInstEstudiante.objects.get(inscripcion=inscripcion)
                                documentos = inscripcion.documentos_entregados_conduccion()
                                initial = model_to_dict(inscripcion)
                                initial.update(model_to_dict(inscripcion.persona))
                                initial.update({'copia_cedula': documentos.copia_cedula, 'titulo': documentos.titulo,
                                                'fotos2': documentos.fotos2, 'licencia': documentos.licencia,
                                                'votacion': documentos.votacion, 'carnetsangre': documentos.carnetsangre,
                                                'ex_psicologico': documentos.ex_psicologico,
                                                'val_psicosometrica': documentos.val_psicosometrica,
                                                'licienciatipoc': documentos.licienciatipoc,
                                                'originalrecord': documentos.originalrecord,
                                                'originalcontenido': documentos.originalcontenido,
                                                'acta': documentos.acta,
                                                'certificado': documentos.certificado,
                                                'sabe_conducir': documentos.sabe_conducir,
                                                'tiene_licencia': documentos.tiene_licencia,
                                                'tipo_licencia': documentos.tipo_licencia,
                                                'val_medica': documentos.val_medica,'foto':fotoinst.foto,
                                                'puntos_licencia': documentos.puntos_licencia,'soporte_ant': documentos.soporte_ant})
                                data['fotoinst']=fotoinst
                            else:
                                documentos = inscripcion.documentos_entregados_conduccion()
                                initial = model_to_dict(inscripcion)
                                initial.update(model_to_dict(inscripcion.persona))
                                initial.update({'copia_cedula': documentos.copia_cedula, 'titulo': documentos.titulo,
                                                'fotos2': documentos.fotos2, 'licencia': documentos.licencia,
                                                'votacion': documentos.votacion, 'carnetsangre': documentos.carnetsangre,
                                                'ex_psicologico': documentos.ex_psicologico,
                                                'val_psicosometrica': documentos.val_psicosometrica,
                                                'licienciatipoc': documentos.licienciatipoc,
                                                'originalrecord': documentos.originalrecord,
                                                'originalcontenido': documentos.originalcontenido,
                                                'acta': documentos.acta,
                                                'certificado': documentos.certificado,
                                                'sabe_conducir': documentos.sabe_conducir,
                                                'tiene_licencia': documentos.tiene_licencia,
                                                'tipo_licencia': documentos.tipo_licencia,
                                                'val_medica': documentos.val_medica,
                                                'puntos_licencia': documentos.puntos_licencia,
                                                'soporte_ant': documentos.soporte_ant})

                        else:
                            documentos = inscripcion.documentos_entregados()
                            initial = model_to_dict(inscripcion)
                            initial.update(model_to_dict(inscripcion.persona))

                            if FotoInstEstudiante.objects.filter(inscripcion=inscripcion).exists():
                                fotoinst = FotoInstEstudiante.objects.get(inscripcion=inscripcion)
                                initial.update({'cedula2': documentos.cedula, 'titulo': documentos.titulo,
                                            'acta': documentos.acta, 'votacion': documentos.votacion,
                                            'actaconv': documentos.actaconv, 'partida_nac': documentos.partida_nac,
                                            'fotos': documentos.fotos,'foto':fotoinst.foto,'actafirmada': documentos.actafirmada})
                                data['fotoinst']=fotoinst

                            else:
                                initial.update({'cedula2': documentos.cedula, 'titulo': documentos.titulo,
                                                'acta': documentos.acta, 'votacion': documentos.votacion,
                                                'actaconv': documentos.actaconv, 'partida_nac': documentos.partida_nac,
                                                'fotos': documentos.fotos,'actafirmada': documentos.actafirmada})

                        # OCU 11-enero-2017 titulo bachiller para extranjeros
                        if InscripcionExtranjerosTitulo.objects.filter(inscripcion=inscripcion).exists():
                            tituloextranjero=InscripcionExtranjerosTitulo.objects.get(inscripcion=inscripcion)
                            initial.update({'titulodoc':tituloextranjero.titulodoc})
                            data['titulodoc']=tituloextranjero

                        if UTILIZA_GRUPOS_ALUMNOS and inscripcion.inscripciongrupo_set.exists():
                            initial.update({'grupo': inscripcion.grupo})
                        if ConvenioUsuario.objects.filter(usuario=request.user).exists():
                            convenio = ConvenioUsuario.objects.filter(usuario=request.user).values('convenio')
                            data['grupos_abiertos'] = Grupo.objects.filter(convenio__in=convenio)
                        else:
                            data['grupos_abiertos'] = Grupo.objects.all()
                        if inscripcion.convenio_esempresa():
                            initial.update({'tipopersona': inscripcion.tipopersonaempresaconvenio,
                                            'pariente': inscripcion.parentescotipopersonaec,
                                            'documentoconvenio': inscripcion.documentoempresaconvenio,
                                            'descuentoempresa': inscripcion.descuentoconvenio})
                        data['utiliza_grupos_alumnos'] = UTILIZA_GRUPOS_ALUMNOS
                        insf = InscripcionForm(initial=initial)
                        data['form'] = insf
                        data['inscripcion'] = inscripcion
                        data['inscripcion_conduccion'] = INSCRIPCION_CONDUCCION
                        data['matriculado'] = inscripcion.matriculado()
                        data['DEFAULT_PASSWORD'] = DEFAULT_PASSWORD
                        data['convenio_es_empresa'] = True if inscripcion.convenio_esempresa() else False
                        return render(request ,"inscripciones/editarbs.html" ,  data)

                    elif action=='editgraduados':
                        if 'graduado' in request.GET:
                            data['graduado'] = request.GET['graduado']

                        inscripcion = Inscripcion.objects.get(pk=request.GET['id'])

                        documentos = inscripcion.documentos_entregados()
                        initial = model_to_dict(inscripcion)
                        initial.update(model_to_dict(inscripcion.persona))

                        # if FotoInstEstudiante.objects.filter(inscripcion=inscripcion).exists():
                        #     fotoinst = FotoInstEstudiante.objects.get(inscripcion=inscripcion)
                        #     initial.update({'cedula2': documentos.cedula, 'titulo': documentos.titulo,
                        #                 'acta': documentos.acta, 'votacion': documentos.votacion,
                        #                 'actaconv': documentos.actaconv, 'partida_nac': documentos.partida_nac,
                        #                 'fotos': documentos.fotos,'foto':fotoinst.foto})
                        #     data['fotoinst']=fotoinst
                        #
                        # else:
                        #     initial.update({'cedula2': documentos.cedula, 'titulo': documentos.titulo,
                        #                     'acta': documentos.acta, 'votacion': documentos.votacion,
                        #                     'actaconv': documentos.actaconv, 'partida_nac': documentos.partida_nac,
                        #                     'fotos': documentos.fotos})

                        # OCU 11-enero-2017 titulo bachiller para extranjeros
                        # if InscripcionExtranjerosTitulo.objects.filter(inscripcion=inscripcion).exists():
                        #     tituloextranjero=InscripcionExtranjerosTitulo.objects.get(inscripcion=inscripcion)
                        #     initial.update({'titulodoc':tituloextranjero.titulodoc})
                        #     data['titulodoc']=tituloextranjero

                        # if UTILIZA_GRUPOS_ALUMNOS and inscripcion.inscripciongrupo_set.exists():
                        #     initial.update({'grupo': inscripcion.grupo})
                        # if ConvenioUsuario.objects.filter(usuario=request.user).exists():
                        #     convenio = ConvenioUsuario.objects.filter(usuario=request.user).values('convenio')
                        #     data['grupos_abiertos'] = Grupo.objects.filter(convenio__in=convenio)
                        # else:
                        #     data['grupos_abiertos'] = Grupo.objects.all()
                        # data['utiliza_grupos_alumnos'] = UTILIZA_GRUPOS_ALUMNOS
                        insf = InscripcionGraduadosForm(initial=initial)
                        data['form'] = insf
                        data['inscripcion'] = inscripcion
                        data['inscripcion_conduccion'] = INSCRIPCION_CONDUCCION
                        data['matriculado'] = inscripcion.matriculado()
                        return render(request ,"inscripciones/editargraduados.html" ,  data)


                    elif action=='datos':
                        inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                        documentos = inscripcion.documentos_entregados()
                        initial = model_to_dict(inscripcion)
                        initial.update(model_to_dict(inscripcion.persona))
                        initial.update({'cedula2': documentos.cedula, 'titulo': documentos.titulo,
                                        'acta': documentos.acta, 'votacion': documentos.votacion,
                                        'actaconv': documentos.actaconv, 'partida_nac': documentos.partida_nac, 'fotos': documentos.fotos})

                        if UTILIZA_GRUPOS_ALUMNOS and inscripcion.inscripciongrupo_set.exists():
                            initial.update({'grupo': inscripcion.grupo})
                        data['grupos_abiertos'] = Grupo.objects.all()
                        data['utiliza_grupos_alumnos'] = UTILIZA_GRUPOS_ALUMNOS

                        insf = InscripcionForm(initial=initial)

                        data['form'] = insf
                        data['inscripcion'] = inscripcion
                        data['matriculado'] = inscripcion.matriculado()
                        return render(request ,"inscripciones/datosbs.html" ,  data)

                    #Record e Historico estudiantes
                    elif action=='record':
                        data = {'title': 'Registro Academico del Alumno'}
                        inscripcion = Inscripcion.objects.get(pk=request.GET['id'])

                        search = None
                        if 's' in request.GET:
                            search = request.GET['s']
                        if search:
                            records = RecordAcademico.objects.filter(Q(asignatura__nombre__icontains=search), inscripcion=inscripcion).order_by('fecha','asignatura','id')
                        else:
                            addUserData(request,data)
                            persona=data['persona']
                            if persona.puede_editar_ingles():
                                records = RecordAcademico.objects.filter(Q(asignatura__nombre__icontains='INGL'), inscripcion=inscripcion).order_by('fecha','asignatura','id')
                            else:
                                records = RecordAcademico.objects.filter(inscripcion=inscripcion).order_by('fecha', 'asignatura', 'id')

                        paging = Paginator(records, 30)
                        p = 1
                        if 'ret' in request.GET:
                            data['ret'] = request.GET['ret']

                        try:
                            if 'page' in request.GET:
                                p = int(request.GET['page'])
                            page = paging.page(p)
                        except:
                            page = paging.page(1)
                        data['paging'] = paging
                        data['page'] = page
                        data['records'] = page.object_list
                        data['inscripcion'] = inscripcion
                        data['search'] = search if search else ""
                        data['inscripcion_conduccion'] = INSCRIPCION_CONDUCCION
                        data['MODELO_EVALUATIVO'] = [MODELO_EVALUACION, EVALUACION_IAVQ, EVALUACION_ITB, EVALUACION_ITS]
                        if DEFAULT_PASSWORD == 'itb':
                            try:
                                if inscripcion.persona.extranjero:
                                    ced = inscripcion.persona.pasaporte
                                    op=0
                                else:
                                    op=1
                                    ced = inscripcion.persona.cedula
                                datos = requests.get('https://sga.buckcenter.com.ec/api',params={'a': 'datos_ingles', 'ced':ced , 'op':op })
                                if datos.status_code==200:
                                    data['otrasnotas']=datos.json()['notas']
                            except Exception as e:
                                pass
                        return render(request ,"inscripciones/recordbs.html" ,  data)
                    elif action=='historico':
                        data['title'] = 'Historico de Notas del Alumno'
                        inscripcion = Inscripcion.objects.get(pk=request.GET['id'])

                        search = None
                        if 's' in request.GET:
                            search = request.GET['s']
                        if search:
                            records = HistoricoRecordAcademico.objects.filter(Q(asignatura__nombre__icontains=search), inscripcion=inscripcion).order_by('fecha','asignatura','id')
                        else:
                            addUserData(request,data)
                            persona=data['persona']
                            if persona.puede_editar_ingles():
                               records = HistoricoRecordAcademico.objects.filter(Q(asignatura__nombre__icontains='INGLES'), inscripcion=inscripcion).order_by('fecha','asignatura','id')
                            else:
                                records = HistoricoRecordAcademico.objects.filter(inscripcion=inscripcion).order_by('fecha','asignatura','id')

                        paging = Paginator(records, 30)
                        try:
                            p = 1
                            if 'page' in request.GET:
                                p = int(request.GET['page'])
                            page = paging.page(p)
                        except:
                            page = paging.page(1)
                        data['paging'] = paging
                        data['page'] = page
                        data['records'] = page.object_list
                        data['inscripcion'] = inscripcion
                        data['search'] = search if search else ""
                        data['historia_notas'] = REGISTRO_HISTORIA_NOTAS
                        certificado_ingles = None
                        data['MODELO_EVALUATIVO'] = [MODELO_EVALUACION, EVALUACION_IAVQ, EVALUACION_ITB, EVALUACION_ITS]
                        if ViewCertificacionesIngles.objects.filter(cedula=inscripcion.persona.cedula).exclude(cedula=None).exclude(cedula="").exists():
                            certificado_ingles = ViewCertificacionesIngles.objects.filter(cedula=inscripcion.persona.cedula).exclude(cedula=None).exclude(cedula="").order_by('tipo','certificacion')
                        elif ViewCertificacionesIngles.objects.filter(pasaporte=inscripcion.persona.pasaporte).exclude(pasaporte=None).exclude(pasaporte="").exists():
                            certificado_ingles = ViewCertificacionesIngles.objects.filter(pasaporte=inscripcion.persona.pasaporte).exclude(pasaporte=None).exclude(pasaporte='').order_by('tipo','certificacion')
                        data['cert_ingles'] = certificado_ingles
                        if DEFAULT_PASSWORD == 'itb':
                            try:
                                if inscripcion.persona.extranjero:
                                    ced = inscripcion.persona.pasaporte
                                    op=0
                                else:
                                    op=1
                                    ced = inscripcion.persona.cedula
                                datos = requests.get('http://sga.buckcenter.com.ec/api',params={'a': 'datos_ingles', 'ced':ced , 'op':op })
                                if datos.status_code==200:
                                    data['otrasnotas']=datos.json()['notas']
                            except Exception as e:
                                pass
                        return render(request ,"inscripciones/historicobs.html" ,  data)
                    elif action=='motivoanula':
                        if(InactivaActivaUsr.objects.filter(inscripcion__id=request.GET['id']).exists()):
                            registros = InactivaActivaUsr.objects.filter(inscripcion__id=request.GET['id']).order_by('fecha')
                            data['inscripcion']=registros.filter()[:1].get().inscripcion
                            data['registros']=registros
                            return render(request ,"inscripciones/motivoanula.html" ,  data)
                    elif action=='vernivelesuniforme':
                        if Inscripcion.objects.filter(pk=request.GET['idinscripcion']).exists():
                            inscripcion=Inscripcion.objects.filter(pk=request.GET['idinscripcion'])[:1].get()
                            print(1)
                            # matricula=Matricula.objects.filter(inscripcion=inscripcion).values('id')
                            # print(2)
                            if EntregaUniforme.objects.filter(matricula__inscripcion=inscripcion).exists():
                                print(3)
                                uniforme=EntregaUniforme.objects.filter(matricula__inscripcion=inscripcion)
                                data['uniforme']=uniforme
                                data['inscripcion']=inscripcion

                                return render(request,"inscripciones/veruniforme.html", data)

                    elif action == 'proceso':
                        data['title'] = 'DOBE - Entrevista'
                        inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                        if 'error' in request.GET:
                            data['error'] = request.GET['error']
                        if ProcesoDobe.objects.filter(inscripcion=inscripcion).exists():
                            proceso=ProcesoDobe.objects.filter(inscripcion=inscripcion)[:1].get()
                            initial = model_to_dict(proceso)
                            data['form'] = ProcesoDobeForm(initial=initial)
                            data['inscripcion'] = inscripcion
                            data['proceso']=proceso
                        else:
                            data['inscripcion'] = inscripcion
                            form = ProcesoDobeForm()
                            data['form'] = form

                        return render(request ,"inscripciones/proceso_dobe.html" ,  data)

                    # OCastillo 01-oct-2015 proceso doble matricula
                    elif action == 'procesodm':
                        data['title'] = 'Doble Matricula - Entrevista'
                        inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                        if 'error' in request.GET:
                            data['error'] = request.GET['error']
                        if ProcesoDobleMatricula.objects.filter(inscripcion=inscripcion).exists():
                            procesodm=ProcesoDobleMatricula.objects.filter(inscripcion=inscripcion)[:1].get()
                            initial = model_to_dict(procesodm)
                            data['form'] = ProcesoDobleMatriculaForm(initial=initial)
                            data['inscripcion'] = inscripcion
                        else:
                            data['inscripcion'] = inscripcion
                            form = ProcesoDobleMatriculaForm()
                            data['form'] = form
                        return render(request ,"inscripciones/proceso_doblematricula.html" ,  data)

                    elif action=='addrecord':
                        data['title'] = 'Adicionar Registro Academico del Alumno'
                        inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                        data['inscripcion'] = inscripcion
                        form = RecordAcademicoForm()
                        data['form'] = form
                        if 'error' in request.GET:
                            data['error']= request.GET['error']
                        return render(request ,"inscripciones/adicionar_recordbs.html" ,  data)
                    elif action=='addhistorico':
                        data['title'] = 'Adicionar Historico de Registro Academico del Alumno'
                        inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                        carrera = inscripcion.carrera_id
                        data['inscripcion'] = inscripcion
                        form = HistoricoRecordAcademicoForm()
                        form.for_carrera(carrera)
                        data['form'] = form
                        # OCU 17-nov-2017 para validar la nota maxima
                        data['nota_maxima']=NOTA_MAXIMA
                        if 'error' in request.GET:
                            data['error']= request.GET['error']
                        return render(request ,"inscripciones/adicionar_historicobs.html" ,  data)
                    elif action=='editrecord':
                        data['title'] = 'Editar Registro Academico'
                        record = RecordAcademico.objects.get(pk=request.GET['id'])
                        initial = model_to_dict(record)
                        data['form'] = RecordAcademicoForm(initial=initial)
                        data['record'] = record
                        return render(request ,"inscripciones/editar_recordbs.html" ,  data)
                    elif action=='edithistorico':
                        data['title'] = 'Editar Historico de Registro Academico'
                        record = HistoricoRecordAcademico.objects.get(pk=request.GET['id'])
                        initial = model_to_dict(record)
                        data['form'] = HistoricoRecordAcademicoForm(initial=initial)
                        data['record'] = record
                        #OCU 17-nov-2017 para que las notas que ingresen sean validas
                        data['nota_maxima']=NOTA_MAXIMA

                        if 'error' in request.GET:
                            data['error']= request.GET['error']
                        return render(request ,"inscripciones/editar_historicobs.html" ,  data)
                    elif action=='delrecord':
                        data['title'] = 'Eliminar Registro Academico'
                        data['record'] = RecordAcademico.objects.get(pk=request.GET['id'])
                        return render(request ,"inscripciones/borrar_recordbs.html" ,  data)

                    elif action=='delhistorico':
                        data['title'] = 'Eliminar Historico de Registro Academico'
                        data['record'] = HistoricoRecordAcademico.objects.get(pk=request.GET['id'])
                        return render(request ,"inscripciones/borrar_historicobs.html" ,  data)

                    #Historico de notas estudiantes parciales ITB
                    elif action=='historiconotas':
                        data['reprobado'] = NOTA_ESTADO_REPROBADO
                        data['aprobado'] = NOTA_ESTADO_APROBADO
                        data['examen'] = NOTA_ESTADO_DERECHOEXAMEN
                        data['recuperacion'] = NOTA_ESTADO_SUPLETORIO
                        data['title'] = 'Historico de Notas Parciales'
                        try:
                            if HistoricoNotasITB.objects.filter(historico=request.GET['id']).exists():
                                record = HistoricoNotasITB.objects.filter(historico=request.GET['id']).order_by('-id')[:1].get()
                            else:
                                record = HistoricoNotasPractica.objects.filter(historico=request.GET['id'])[:1].get()
                        except :
                                record = HistoricoNotasITB(historico=HistoricoRecordAcademico.objects.filter(pk=request.GET['id'])[:1].get(),
                                                            n1=0, cod1=0, n2=0, cod2=0, n3=0, cod3=0, n4=0, cod4=0, n5=0,
                                                            total=0, recup=0, notafinal=0, estado = TipoEstado.objects.get(pk=NOTA_ESTADO_EN_CURSO))
                                record.save()
                        data['record'] = record
                        return render(request ,"inscripciones/historiconotasbs.html" ,  data)

                    elif action=='edithistoriconotas':
                        data['title'] = 'Editar Historico de Notas'
                        form = ""
                        historia = ""
                        band=0

                        historico = HistoricoRecordAcademico.objects.filter(pk=request.GET['his']).order_by('-id')[:1].get()

                        if historico.asignatura.id != ASIGNATURA_PRACTICA_CONDUCCION:
                            historia = HistoricoNotasITB.objects.get(pk=request.GET['id'])
                            initial = model_to_dict(historia)
                            form = HistoricoNotasITBForm(initial=initial)
                        else:
                            band=1
                            historia = HistoricoNotasPractica.objects.get(pk=request.GET['id'])
                            initial = model_to_dict(historia)
                            form = HistoricoNotasPracticaForm(initial=initial)
                        data['form'] = form
                        data['historia'] = historia
                        data['nota1'] = PORCIENTO_NOTA1
                        data['nota2']= PORCIENTO_NOTA2
                        data['nota3']= PORCIENTO_NOTA3
                        data['nota4']= PORCIENTO_NOTA4
                        data['nota5']= PORCIENTO_NOTA5
                        data['recup']= PORCIENTO_RECUPERACION
                        data['band']= band
                        data['historico']= historico
                        data['inscripcion'] = historia.historico.inscripcion
                        data['DEFAULT_PASSWORD']=DEFAULT_PASSWORD
                        return render(request ,"inscripciones/edithistorianotas.html" ,  data)
                    elif action=='addhistoriconotas':
                        data['title'] = 'Adicionar Historico de Notas'
                        historico = HistoricoRecordAcademico.objects.get(pk=request.GET['id'])
                        data['historico'] = historico
                        data['form'] = HistoricoNotasITBForm()
                        return render(request ,"inscripciones/addhistoriconotas.html" ,  data)
                    elif action == 'verexamening':
                        inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                        data['inscripcion'] = inscripcion
                        examen = ExamenConvalidacionIngreso.objects.filter(inscripcion=inscripcion)
                        data['examen'] = examen
                        return render(request ,"inscripciones/exameningreso.html" ,  data)
                    #Historia nivel estudiante
                    elif action=='historianivel':
                        data['title'] = 'Historia de Niveles del Alumno'
                        inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                        historianiveles = HistoriaNivelesDeInscripcion.objects.filter(inscripcion=inscripcion).order_by('fechaperiodo')
                        data['inscripcion'] = inscripcion
                        data['historianiveles'] = historianiveles
                        return render(request ,"inscripciones/historianivelesbs.html" ,  data)
                    elif action=='addhistorianivel':
                        data['title'] = 'Adicionar Historia de Niveles del Alumno'
                        inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                        data['inscripcion'] = inscripcion
                        form = HistoriaNivelesDeInscripcionForm(instance=HistoriaNivelesDeInscripcion(inscripcion=inscripcion))
                        data['form'] = form
                        return render(request ,"inscripciones/adicionar_historianivelesbs.html" ,  data)
                    elif action=='edithistorianivel':
                        data['title'] = 'Editar Historia de Niveles'
                        historianiveles = HistoriaNivelesDeInscripcion.objects.get(pk=request.GET['id'])
                        data['form'] = HistoriaNivelesDeInscripcionForm(instance=historianiveles)
                        data['historianivel'] = historianiveles
                        return render(request ,"inscripciones/editar_historianivelesbs.html" ,  data)
                    elif action=='convalidar':
                        data['title'] = 'Convalidacion del Estudiante'
                        record = RecordAcademico.objects.get(pk=request.GET['id'])
                        try:
                            convalidacion = ConvalidacionInscripcion.objects.get(record=record)
                        except :
                            convalidacion = ConvalidacionInscripcion(record=record)
                            convalidacion.save()
                        initial = model_to_dict(convalidacion)
                        data['form'] = ConvalidacionInscripcionForm(initial=initial)
                        data['convalidacion'] = convalidacion
                        return render(request ,"inscripciones/convalidar.html" ,  data)
                    elif action=='delhistorianivel':
                        data['title'] = 'Eliminar Historia de Nivel'
                        data['historianivel'] = HistoriaNivelesDeInscripcion.objects.get(pk=request.GET['id'])
                        return render(request ,"inscripciones/borrar_historianivelesbs.html" ,  data)

                    #Fotos del estudiante
                    elif action=='borrarfoto':
                        inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                        persona = inscripcion.persona
                        persona.borrar_foto()
                        return HttpResponseRedirect("/inscripciones")
                    elif action=='cargarfoto':
                        inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                        form = CargarFotoForm()
                        data['inscripcion'] = inscripcion
                        data['form'] = form
                        return render(request ,"inscripciones/cargarfotobs.html" ,  data)
                    elif action=='verfoto':
                        inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                        data['inscripcion'] = inscripcion
                        return render(request ,"inscripciones/fotobs.html" ,  data)

                    #Empresas en las que ha trabajado el estudiante
                    elif action=='trabajo':
                        inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                        data['inscripcion'] = inscripcion
                        trabajos = EmpresaInscripcion.objects.filter(inscripcion=inscripcion)
                        data['trabajos'] = trabajos
                        return render(request ,"inscripciones/trabajobs.html" ,  data)
                    elif action=='addtrabajo':
                        data['title'] = 'Adicionar Actividad Laboral del Alumno'
                        inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                        data['inscripcion'] = inscripcion
                        form = EmpresaInscripcionForm()
                        data['form'] = form
                        return render(request ,"inscripciones/adicionar_trabajobs.html" ,  data)
                    elif action=='edittrabajo':
                        data['title'] = 'Editar Actividad Laboral'
                        trabajo = EmpresaInscripcion.objects.get(pk=request.GET['id'])
                        initial = model_to_dict(trabajo)
                        data['form'] = EmpresaInscripcionForm(initial=initial)
                        data['trabajo'] = trabajo
                        data['inscripcion'] = trabajo.inscripcion
                        return render(request ,"inscripciones/editar_trabajobs.html" ,  data)
                    elif action=='deltrabajo':
                        data['title'] = 'Eliminar Actividad Laboral'
                        data['trabajo'] = EmpresaInscripcion.objects.get(pk=request.GET['id'])
                        return render(request ,"inscripciones/borrar_trabajobs.html" ,  data)

                    #Estudios Realizados del estudiante
                    elif action=='estudio':
                        inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                        data['inscripcion'] = inscripcion
                        estudios = EstudioInscripcion.objects.filter(inscripcion=inscripcion)
                        data['estudios'] = estudios
                        return render(request ,"inscripciones/estudiobs.html" ,  data)
                    elif action=='addestudio':
                        data['title'] = 'Adicionar Estudios Realizados del Alumno'
                        inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                        data['inscripcion'] = inscripcion
                        form = EstudioInscripcionForm()
                        data['form'] = form
                        return render(request ,"inscripciones/adicionar_estudiobs.html" ,  data)
                    elif action=='editestudio':
                        data['title'] = 'Editar Estudios Realizados'
                        estudio = EstudioInscripcion.objects.get(pk=request.GET['id'])
                        initial = model_to_dict(estudio)
                        data['form'] = EstudioInscripcionForm(initial=initial)
                        data['estudio'] = estudio
                        data['inscripcion'] = estudio.inscripcion
                        return render(request ,"inscripciones/editar_estudiobs.html" ,  data)
                    elif action=='delestudio':
                        data['title'] = 'Eliminar Estudios Realizados'
                        data['estudio'] = EstudioInscripcion.objects.get(pk=request.GET['id'])
                        return render(request ,"inscripciones/borrar_estudiobs.html" ,  data)

                    #Practicas Preprofesionales
                    elif action=='practicas':
                        inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                        data['inscripcion'] = inscripcion
                        aprobacion=None
                        hpracticas = 0
                        vinculacion = 0
                        if InscripcionPracticas.objects.filter(inscripcion=inscripcion).exists():
                            practicas = InscripcionPracticas.objects.filter(inscripcion=inscripcion).order_by('inicio')
                            data['totalhoras'] = practicas.aggregate(Sum('horas'))['horas__sum']
                            hpracticas = practicas.aggregate(Sum('horas'))['horas__sum']
                            data['practicas'] = practicas
                        if EstudianteVinculacion.objects.filter(inscripcion=inscripcion).exists():
                            data['vinculacion'] = EstudianteVinculacion.objects.filter(inscripcion=inscripcion)
                            vinculacion= EstudianteVinculacion.objects.filter(inscripcion=inscripcion).aggregate(Sum('horas'))['horas__sum']
                            data['tohorasvin'] =vinculacion
                        if AprobacionVinculacion.objects.filter(inscripcion=inscripcion).exists():
                            aprobacion=AprobacionVinculacion.objects.filter(inscripcion=inscripcion)[:1].get()
                        data['totalgen'] = vinculacion + hpracticas
                        data['aprobacion']=aprobacion
                        if 'p' in request.GET:
                            data['p']=request.GET['p']

                        return render(request ,"inscripciones/practicasbs.html" ,  data)

                    #OC 05-04-2019 verificar horas vinculacion
                    elif action=='verificarvinculacion':
                        inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                        data['inscripcion'] = inscripcion
                        aprobacion=None
                        vinculacion = 0
                        if EstudianteVinculacion.objects.filter(inscripcion=inscripcion).exists():
                            data['vinculacion'] = EstudianteVinculacion.objects.filter(inscripcion=inscripcion).order_by('nivelmalla')
                            vinculacion= EstudianteVinculacion.objects.filter(inscripcion=inscripcion).aggregate(Sum('horas'))['horas__sum']
                            data['tohorasvin'] =vinculacion

                        if AprobacionVinculacion.objects.filter(inscripcion=inscripcion).exists():
                            apruebavinculacion=AprobacionVinculacion.objects.filter(inscripcion=inscripcion)
                            aprobacion=AprobacionVinculacion.objects.filter(inscripcion=inscripcion).order_by('estudiantevinculacion__nivelmalla')
                            # data['form'] = VinculacionForm(initial={"inicio":datetime.now().date(),"fin":datetime.now().date()})
                           # initial = model_to_dict(apruebavinculacion)
                           # initial.update(model_to_dict(apruebavinculacion))
                            data['form'] = AprobacionVinculacionForm()
                        else:
                            data['form'] = AprobacionVinculacionForm()
                        data['aprobacion']=aprobacion

                        return render(request ,"inscripciones/verificacionvinculacion.html" ,  data)

                    #OCastillo 11-01-2022 eliminar aprobacion de vinculacion
                    elif action == 'eliminaraprobacionvinc':
                        aprobacion = AprobacionVinculacion.objects.get(pk=request.GET['id'])
                        i=aprobacion.inscripcion.id
                        #Obtain client ip address
                        client_address = ip_client_address(request)

                        # Log de ELIMINAR APROBACION DE VINCULACION
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(aprobacion).pk,
                            object_id       = aprobacion.id,
                            object_repr     = force_str(aprobacion),
                            action_flag     = DELETION,
                            change_message  = 'Eliminada Aprobacion Vinculacion  (' + client_address + ')'  )
                        aprobacion.delete()

                        return HttpResponseRedirect("/inscripciones?action=verificarvinculacion&id="+str(i))


                    #OC 16-04-2019 para ver aprobacion de horas vinculacion
                    elif action=='veraprobacionvinculacion':
                        inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                        data['inscripcion'] = inscripcion
                        data['vinculacion'] = EstudianteVinculacion.objects.filter(inscripcion=inscripcion)
                        aprobacion=None
                        vinculacion= EstudianteVinculacion.objects.filter(inscripcion=inscripcion).aggregate(Sum('horas'))['horas__sum']
                        data['tohorasvin'] = vinculacion
                        if AprobacionVinculacion.objects.filter(inscripcion=inscripcion).exists():
                            aprobacion=AprobacionVinculacion.objects.filter(inscripcion=inscripcion)
                            apruebavinculacion=AprobacionVinculacion.objects.filter(inscripcion=inscripcion)
                            #initial = model_to_dict(apruebavinculacion)
                            #initial.update(model_to_dict(apruebavinculacion))
                            data['form'] = AprobacionVinculacionForm()
                        else:
                            data['form'] = AprobacionVinculacionForm()
                        data['aprobacion']=aprobacion

                        return render(request ,"inscripciones/veraprobacionvinculacion.html" ,  data)

                    elif action=='addpracticas':
                        #OCastillo 14-07-2021 quitar obligatoriedad del archivo si este ya existe
                        archivo=False
                        data['title'] = 'Adicionar Practica Preprofesional del Alumno'
                        data['inscripcion'] = Inscripcion.objects.get   (pk=request.GET['id'])
                        inscripcion = Inscripcion.objects.get   (pk=request.GET['id'])

                        if InscripcionPracticas.objects.filter(inscripcion=inscripcion).exists():
                            practicas = InscripcionPracticas.objects.filter(inscripcion=inscripcion).order_by('inicio')[:1].get()
                            if practicas.archivo:
                                archivo=True
                        data['archivo'] = archivo
                        form =InscripcionPracticaForm(initial={'horas':0, 'inicio': datetime.now(), 'fin': datetime.now() })
                        form.nivel_malla(inscripcion.malla_inscripcion().malla)
                        data['form'] = form
                        data['horas_practicas']=HORAS_PRACTICA
                        return render(request ,"inscripciones/adicionar_practicas.html" ,  data)


                    elif action == 'addpracticasdistribucion':
                        data['title'] = 'Adicionar Practica Preprofesional del Alumno'
                        data['inscripcion'] = Inscripcion.objects.get(pk=request.GET['id'])
                        inscripcion = Inscripcion.objects.get(pk=request.GET['id'])

                        form = InscripcionPracticaDistribucionForm(initial={'horas': 0, 'inicio': datetime.now(), 'fin': datetime.now()})
                        formhorasnivel=PracticaDistribucionHorasForm(initial={'horasnivel': 0})

                        formhorasnivel.nivel_malla(inscripcion.malla_inscripcion().malla)

                        #OCastillo 13-03-2023 cambio para tecnologias universitarias de Podologia y Gerontologia
                        if not (inscripcion.malla_inscripcion().malla.id== 72 or inscripcion.malla_inscripcion().malla.id==74):
                            data['listnivel'] = NivelMalla.objects.filter(id__in=AsignaturaMalla.objects.filter(Q(asignatura__nombre__icontains='LABORALES')|Q(asignatura__nombre__icontains='PREPRO'),malla=inscripcion.malla_inscripcion().malla).values('nivelmalla'))
                        else:
                            data['listnivel'] = NivelMalla.objects.filter(id__in=AsignaturaMalla.objects.filter(asignatura__nombre__icontains='TELECLINICA',malla=inscripcion.malla_inscripcion().malla).values('nivelmalla'))

                        data['formhorasnivel'] = formhorasnivel
                        data['form'] = form

                        #OCastillo 13-03-2023 cambio para tecnologias universitarias de Podologia y Gerontologia
                        if not (inscripcion.malla_inscripcion().malla.id== 72 or inscripcion.malla_inscripcion().malla.id==74):
                            data['horas_practicas'] = HORAS_PRACTICA
                        else:
                            horas=AsignaturaMalla.objects.filter(asignatura__nombre__icontains='TELECLINICA',malla=inscripcion.malla_inscripcion().malla).aggregate(Sum('horas'))['horas__sum']
                            data['horas_practicas'] = horas

                        return render(request ,"inscripciones/adicionar_practicas_administracion.html" ,  data)


                    elif action=='editpracticas':
                        data['title'] = 'Editar Practica Preprofesional del Alumno'
                        practica = InscripcionPracticas.objects.get(pk=request.GET['id'])
                        initial = model_to_dict(practica)

                        form =InscripcionPracticaForm(initial=initial)
                        form.nivel_malla(practica.inscripcion.malla_inscripcion().malla)
                        data['form'] = form
                        data['practica'] = practica
                        data['inscripcion'] = practica.inscripcion
                        data['horas_practicas']=HORAS_PRACTICA
                        if 'p' in request.GET:
                            data['p'] = request.GET['p']

                        return render(request ,"inscripciones/editar_practicas.html" ,  data)
                    elif action=='delpracticas':
                        data['title'] = 'Eliminar Practica Preprofesional del Alumno'
                        data['practica'] = InscripcionPracticas.objects.get(pk=request.GET['id'])
                        return render(request ,"inscripciones/borrar_practicas.html" ,  data)

                    #Documentos y archivos de estudiantes
                    elif action=='documentos':
                        data['title'] = 'Documentos y Archivos del Alumno'
                        inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                        data['inscripcion'] = inscripcion
                        documentos = DocumentoInscripcion.objects.filter(inscripcion=inscripcion)
                        data['documentos'] = documentos
                        return render(request ,"inscripciones/documentosbs.html" ,  data)
                    elif action=='adddocumento':
                        data['title'] = 'Adicionar Archivos del Alumno'
                        inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                        data['inscripcion'] = inscripcion
                        form = DocumentoInscripcionForm()
                        data['form'] = form
                        return render(request ,"inscripciones/adicionar_documentosbs.html" ,  data)
                    elif action=='deldocumento':
                        data['title'] = 'Eliminar Archivo o Documento del Alumno'
                        data['documento'] = DocumentoInscripcion.objects.get(pk=request.GET['id'])
                        return render(request ,"inscripciones/borrar_documentobs.html" ,  data)

                    elif action=='actividades':
                        data['title'] = 'Trabajos y Estudios del Alumno'
                        inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                        data['inscripcion'] = inscripcion
                        form = ActividadesInscripcionForm()
                        data['form'] = form
                        return render(request ,"inscripciones/actividadesbs.html" ,  data)

                    # Desactiva el usuario en el sistema
                    elif action=='desactivar':
                        data['title'] = 'Desactivar Usuario'
                        inscripcion = Inscripcion.objects.get(pk=int(request.GET['id']))
                        data['inscripcion'] = inscripcion

                        data['form'] = ActivaInactivaUsuarioForm()
                        return render(request ,"inscripciones/inactivar_usr.html" ,  data)

                    # Activa el usuario en el sistema
                    elif action=='activar':
                        data['title'] = 'Activar Usuario'
                        inscripcion = Inscripcion.objects.get(pk=int(request.GET['id']))
                        data['inscripcion'] = inscripcion
                        data['form'] = ActivaInactivaUsuarioForm()
                        return render(request ,"inscripciones/activar_usr.html" ,  data)

                    elif action=='alumalla':
                        data['title'] = 'Malla del Alumno'
                        inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                        inscripcionmalla = inscripcion.malla_inscripcion()
                        #Comprobar que exista la malla en la carrera de la inscripcion
                        if not inscripcionmalla:
                            return HttpResponseRedirect("/?info=Este estudiante no tiene ninguna malla asociada")
                        malla = inscripcionmalla.malla

                        data['inscripcion'] = inscripcion
                        data['inscripcion_malla'] = inscripcionmalla
                        data['malla'] = malla

                        data['nivelesdemallas'] = NivelMalla.objects.all().order_by('orden')
                        data['ejesformativos'] = EjeFormativo.objects.all().order_by('nombre')
                        data['asignaturasmallas'] = [(x, aprobadaAsignatura(x, inscripcion),horaspracticas(x, inscripcion),horasteleclinica(x,inscripcion)) for x in AsignaturaMalla.objects.filter(malla=malla)]
                        resumenNiveles = [{'id':x.id, 'horas': x.total_horas2(malla,inscripcion), 'creditos': x.total_creditos(malla)} for x in NivelMalla.objects.all().order_by('orden')]
                        data['resumenes'] = resumenNiveles
                        data['title'] = "Ver Malla Curricular : "+elimina_tildes(malla.carrera.nombre)
                        if malla.carrera.online:
                            data['ASIST_PARA_APROBAR'] = 0
                        else:
                            data['ASIST_PARA_APROBAR']=ASIST_PARA_APROBAR
                        if InscripcionPracticas.objects.filter(inscripcion=inscripcion).exists():
                            practicas = InscripcionPracticas.objects.filter(inscripcion=inscripcion).aggregate(Sum('horas'))['horas__sum']
                            data['practicas'] = practicas
                        if EstudianteVinculacion.objects.filter(inscripcion=inscripcion).exists():
                            data['vinculacion'] = EstudianteVinculacion.objects.filter(inscripcion=inscripcion)
                            #OCastillo 15-oct-2019 presentar las horas de vinculacion asi no esten terminadas
                            if AprobacionVinculacion.objects.filter(inscripcion=inscripcion).exists():
                                vinculacion= EstudianteVinculacion.objects.filter(inscripcion=inscripcion).aggregate(Sum('horas'))['horas__sum']
                                data['tohorasvin'] =vinculacion

                        #OCastillo 13-03-2023 cambio para tecnologias universitarias de Podologia y Gerontologia
                        if inscripcion.malla_inscripcion().malla.id ==72 or inscripcion.malla_inscripcion().malla.id ==74:
                            data['EJE_PRACTICA']  = 9
                            data['HORAS_TELECLINICA'] = HORAS_TELECLINICA
                        else:
                            data['EJE_PRACTICA']  = EJE_PRACTICA

                        certificado_ingles = None
                        if ViewCertificacionesIngles.objects.filter(cedula=inscripcion.persona.cedula).exclude(cedula=None).exclude(cedula="").exists():
                            certificado_ingles = ViewCertificacionesIngles.objects.filter(cedula=inscripcion.persona.cedula).exclude(cedula=None).exclude(cedula="").order_by('tipo','certificacion')
                        if ViewCertificacionesIngles.objects.filter(pasaporte=inscripcion.persona.pasaporte).exclude(pasaporte=None).exclude(pasaporte='').exists():
                            certificado_ingles = ViewCertificacionesIngles.objects.filter(pasaporte=inscripcion.persona.pasaporte).exclude(pasaporte=None).exclude(pasaporte='').order_by('tipo','certificacion')
                        data['cert_ingles'] = certificado_ingles
                        return render(request ,"inscripciones/mallabs.html" ,  data)

                    #Resetear la Clave del usuario a la contrasenna por default en el settings
                    elif action=='resetear':
                        data['title'] = 'Resetear Clave del Usuario'
                        inscripcion = Inscripcion.objects.get(pk=int(request.GET['id']))
                        user = inscripcion.persona.usuario
                        if DEFAULT_PASSWORD == 'itb' and ACTIVA_ADD_EDIT_AD:
                            validacambio = True
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
                            if not validacambio:
                                return HttpResponseRedirect("/inscripciones?error=Vuelva a intentarlo")
                        else:
                            user.set_password(DEFAULT_PASSWORD)
                        user.save()
                        return HttpResponseRedirect("/inscripciones?info=Se cambio la clave con exito")
                    elif action=='generarclave':
                        data['title'] = 'Generar Clave de Acceso de Padres'
                        inscripcion = Inscripcion.objects.get(pk=int(request.GET['id']))
                        data['inscripcion'] = inscripcion
                        data['form'] = PadreClaveForm(initial={'fecha': datetime.now().strftime("%d-%m-%Y")})
                        return render(request ,"inscripciones/padreclavesbs.html" ,  data)

                    elif action=='adicionamateria':
                        from ext.models import MateriaExterna
                        data['title'] = 'Adicionar Materia Local'
                        inscripcion = Inscripcion.objects.get(pk=int(request.GET['id']))
                        materias_externas = MateriaExterna.objects.all()
                        mismaterias = [x.id for x in Materia.objects.filter(materiaasignada__matricula__inscripcion=inscripcion)]
                        ma = Materia.objects.filter(cerrado=False).exclude(materiaexterna__in=materias_externas)
                        ma = ma.exclude(id__in=mismaterias)
                        data['inscripcion'] = inscripcion
                        data['materias'] = ma
                        return render(request ,"inscripciones/adicionamateriabs.html" ,  data)

                    elif action=='addmateria':
                        sid = transaction.savepoint()
                        try:
                            inscripcion = Inscripcion.objects.get(pk=int(request.GET['id']))
                            materia = Materia.objects.get(pk=int(request.GET['mat']))
                            nivel = Nivel.objects.filter()[:1].get()
                            rubroinscripcion = TipoOtroRubro.objects.filter(id=RUBRO_TIPO_OTRO_INSCRIPCION)[:1].get()
                            rubromodulo = TipoOtroRubro.objects.filter(id=RUBRO_TIPO_OTRO_MODULO_INTERNO)[:1].get()

                            if not Matricula.objects.filter(inscripcion=inscripcion, nivel=nivel).exists():
                                alu_matricul = Matricula(   inscripcion = inscripcion,
                                                            nivel = nivel )
                                alu_matricul.save()
                            else:
                                alu_matricul = Matricula.objects.filter(inscripcion=inscripcion, nivel=nivel)[:1].get()

                            if not MateriaAsignada.objects.filter(materia=materia,matricula=alu_matricul).exists():
                                alu_materia = MateriaAsignada(  matricula = alu_matricul,
                                                                materia = materia,
                                                                notafinal = 0,
                                                                asistenciafinal = 0,
                                                                supletorio = 0,
                                                                cerrado = materia.cerrado)
                                alu_materia.save()
                                #rubros
                                #rubro modulo

                                r1 = Rubro( fecha = materia.inicio,
                                            valor = rubroinscripcion.precio_sugerido(),
                                            inscripcion = inscripcion,
                                            cancelado = False,
                                            fechavence = materia.fin)
                                r1.save()
                                r1otro = RubroOtro(rubro=r1,
                                                   tipo=TipoOtroRubro.objects.get(pk=RUBRO_TIPO_OTRO_INSCRIPCION),
                                                   descripcion=materia.nombre_completo())
                                r1otro.save()
                                r2 = Rubro( fecha = materia.inicio,
                                            valor = rubromodulo.precio_sugerido(),
                                            inscripcion = inscripcion,
                                            cancelado = False,
                                            fechavence = materia.fin)
                                r2.save()
                                r2otro = RubroOtro(rubro=r2,
                                                   tipo=TipoOtroRubro.objects.get(pk=RUBRO_TIPO_OTRO_MODULO_INTERNO),
                                                   descripcion=materia.nombre_completo())
                                r2otro.save()
                        except:
                            transaction.savepoint_rollback(sid)
                            return HttpResponseRedirect("/inscripciones?action=adicionamateria&id="+str(inscripcion.id))
                        transaction.savepoint_commit(sid)
                        return HttpResponseRedirect("/inscripciones?s="+inscripcion.persona.cedula)


                    elif action=='borrarclave':
                        data['title'] = 'Eliminar Clave de Acceso de Padres'
                        inscripcion = Inscripcion.objects.get(pk=int(request.GET['id']))
                        try:
                            padreclave = inscripcion.clave_padre()
                            if EMAIL_ACTIVE:
                                padreclave.mail_subject_borrar_clave(padreclave.email)

                            padreclave.delete()

                        except :
                            pass

                    elif action=='egresar':
                        data['title'] = 'Egresar Alumno'
                        inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                        if inscripcion.puede_egresar() == "":
                            data['inscripcion'] = inscripcion
                            if inscripcion.recordacademico_set.filter(aprobada=True, asignatura__in=Asignatura.objects.filter(asignaturamalla__nivelmalla__promediar=True)).exists():
                                promedio = round(inscripcion.recordacademico_set.filter(aprobada=True, asignatura__in=Asignatura.objects.filter(asignaturamalla__nivelmalla__promediar=True)).aggregate(Avg('nota'))['nota__avg'],2)
                            else:
                                promedio = 0
                            data['form'] = EgresadoForm(initial={'fechaegreso': datetime.now().strftime("%d-%m-%Y"), 'notaegreso': promedio})
                            return render(request ,"inscripciones/egresar.html" ,  data)
                        else:
                            return  HttpResponseRedirect("/inscripciones?s="+str(inscripcion.persona.cedula)+"&info="+ str(inscripcion.puede_egresar()))

                    elif action=='egresados':
                        data['title'] = 'Lista de Alumnos Egresados'
                        search = None
                        todos = None
                        if 's' in request.GET:
                            search = request.GET['s']
                        if 't' in request.GET:
                            todos = request.GET['t']
                        if search:
                            ss = search.split(' ')
                            while '' in ss:
                                ss.remove('')
                            if len(ss)==1:
                                estudiantexegresar = EstudianteXEgresar.objects.filter(Q(inscripcion__persona__nombres__icontains=search) | Q(inscripcion__persona__apellido1__icontains=search) | Q(inscripcion__persona__apellido2__icontains=search) | Q(inscripcion__persona__cedula__icontains=search) | Q(inscripcion__persona__pasaporte__icontains=search) | Q(inscripcion__carrera__nombre__icontains=search)).order_by('inscripcion__persona__apellido1')
                            else:
                                estudiantexegresar = EstudianteXEgresar.objects.filter(Q(inscripcion__persona__apellido1__icontains=ss[0]) & Q(inscripcion__persona__apellido2__icontains=ss[1])).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')

                        else:
                            estudiantexegresar = EstudianteXEgresar.objects.filter(inscripcion__persona__usuario__is_active=True).order_by('inscripcion__persona__apellido1')

                        if 'c' in request.GET:
                            carreraid = request.GET['c']
                            data['carrera'] = Carrera.objects.get(pk=request.GET['c'])
                            data['carreraid'] = int(carreraid) if carreraid else ""
                            estudiantexegresar = estudiantexegresar.filter(inscripcion__carrera__grupocoordinadorcarrera__group__in=request.user.groups.all(), carrera=data['carrera']).distinct()
                        else:
                            estudiantexegresar = estudiantexegresar.filter(inscripcion__carrera__grupocoordinadorcarrera__group__in=request.user.groups.all()).distinct()

                        if 'g' in request.GET:
                            grupoid = request.GET['g']
                            data['grupo'] = Grupo.objects.get(pk=request.GET['g'])
                            data['grupoid'] = int(grupoid) if grupoid else ""
                            estudiantexegresar =  estudiantexegresar.filter(inscripcion__carrera__grupocoordinadorcarrera__group__in=request.user.groups.all(), inscripciongrupo__grupo=data['grupo']).distinct()
                        else:
                            estudiantexegresar =  estudiantexegresar.filter(inscripcion__carrera__grupocoordinadorcarrera__group__in=request.user.groups.all()).distinct()

                        if todos:
                            estudiantexegresar = EstudianteXEgresar.objects.all().order_by('inscripcion__persona__apellido1')
                        if CENTRO_EXTERNO and not ('s' in request.GET):
                            estudiantexegresar = EstudianteXEgresar.objects.all().order_by('inscripcion__persona__apellido1')

                        paging = MiPaginador(estudiantexegresar, 30)
                        p = 1
                        try:
                            if 'page' in request.GET:
                                p = int(request.GET['page'])
                            page = paging.page(p)
                        except:
                            page = paging.page(p)

                        data['paging'] = paging
                        data['rangospaging'] = paging.rangos_paginado(p)
                        data['page'] = page
                        data['search'] = search if search else ""
                        data['todos'] = todos if todos else ""
                        # data['activos'] = activos if activos else ""
                        # data['inactivos'] = inactivos if inactivos else ""
                        data['estudiantexegresar'] = page.object_list


                        return render(request ,"inscripciones/egresados.html" ,  data)

                    elif action == 'activacionegresado':
                        d = EstudianteXEgresar.objects.get(pk=request.GET['id'])
                        d.estado = not d.estado
                        d.save()
                        return HttpResponseRedirect("/inscripciones?action=egresados&ban=0")

                    elif action == 'cambiarautorizacionbecadobe':
                        inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                        contenido=''
                        if request.GET['aprobado']=='true':
                            inscripcion.autorizacionbecadobe=True
                            contenido = "SE COMUNICA QUE SE AUTORIZO LA APROBACION DE BECA POR EL JEFE DOBE"
                        else:
                            inscripcion.autorizacionbecadobe=False
                            contenido = "SE COMUNICA QUE SE ELIMINO AUTORIZO LA APROBACION DE BECA POR EL JEFE DOBE"
                        inscripcion.save()

                        if EMAIL_ACTIVE:
                            if TipoIncidencia.objects.filter(pk=4).exists():
                                    tipo = TipoIncidencia.objects.get(pk=4)
                                    hoy = datetime.now().today()


                            send_html_mail('AUTORIZACION DE BECA DOBE',
                                "emails/aprobacionbecadobe.html", {'inscripcion': inscripcion, 'fecha': hoy,'contenido': contenido},tipo.correo.split(","))




                        client_address = ip_client_address(request)

                        # Log de ADICIONAR EGRESADO
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(inscripcion).pk,
                            object_id       = inscripcion.id,
                            object_repr     = force_str(inscripcion),
                            action_flag     = CHANGE,
                            change_message  = 'Cambio autorizacion  beca dobe (' + client_address + ')' )

                        return HttpResponseRedirect("/inscripciones?action=edit&id="+str(inscripcion.id))

                    elif action == 'cambiarautorizacionbecasenescyt':
                        inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                        contenido=''
                        if request.GET['aprobado']=='true':
                            inscripcion.autorizacionbecasenecyt=True
                            contenido = "SE COMUNICA QUE SE AUTORIZO LA APROBACION DE BECA SENESCYT POR EL JEFE DOBE"
                        else:
                            inscripcion.autorizacionbecasenecyt=False
                            contenido = "SE COMUNICA QUE SE ELIMINO AUTORIZO LA APROBACION DE BECA SENESCYT POR EL JEFE DOBE"
                        inscripcion.save()

                        if EMAIL_ACTIVE:
                            if TipoIncidencia.objects.filter(pk=4).exists():
                                    tipo = TipoIncidencia.objects.get(pk=4)
                                    hoy = datetime.now().today()


                            send_html_mail('AUTORIZACION DE BECA SENESCYT',
                                "emails/aprobacionbecadobe.html", {'inscripcion': inscripcion, 'fecha': hoy,'contenido': contenido},tipo.correo.split(","))




                        client_address = ip_client_address(request)

                        # Log de ADICIONAR EGRESADO
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(inscripcion).pk,
                            object_id       = inscripcion.id,
                            object_repr     = force_str(inscripcion),
                            action_flag     = CHANGE,
                            change_message  = 'Cambio autorizacion  beca senecyt (' + client_address + ')' )

                        return HttpResponseRedirect("/inscripciones?action=edit&id="+str(inscripcion.id))

                    elif action == 'cambiarautorizacionayudabeca':
                        inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                        contenido=''
                        if request.GET['aprobado']=='true':
                            inscripcion.aprobacionayudadobe=True
                            contenido = "SE COMUNICA QUE SE AUTORIZO LA APROBACION DE AYUDA BECA POR EL JEFE DOBE"
                        else:
                            inscripcion.aprobacionayudadobe=False
                            contenido = "SE COMUNICA QUE SE ELIMINO AUTORIZO LA APROBACION DE AYUDA DECA POR EL JEFE DOBE"
                        inscripcion.save()

                        if EMAIL_ACTIVE:
                            if TipoIncidencia.objects.filter(pk=4).exists():
                                    tipo = TipoIncidencia.objects.get(pk=4)
                                    hoy = datetime.now().today()


                            send_html_mail('AUTORIZACION DE AYUDA BECA',
                                "emails/aprobacionbecadobe.html", {'inscripcion': inscripcion, 'fecha': hoy,'contenido': contenido},tipo.correo.split(","))




                        client_address = ip_client_address(request)

                        # Log de ADICIONAR EGRESADO
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(inscripcion).pk,
                            object_id       = inscripcion.id,
                            object_repr     = force_str(inscripcion),
                            action_flag     = CHANGE,
                            change_message  = 'Cambio autorizacion  beca ayuda (' + client_address + ')' )

                        return HttpResponseRedirect("/inscripciones?action=edit&id="+str(inscripcion.id))

                    elif action == 'egresarestudi':
                        estudiantexegresar = EstudianteXEgresar.objects.filter(estado=True)
                        for n in estudiantexegresar:
                            record=RecordAcademico.objects.filter(inscripcion=n.inscripcion).order_by('-fecha')[:1].get()
                            fecha = record.fecha
                            egresado = Egresado(inscripcion=n.inscripcion, notaegreso=n.promedio, fechaegreso=fecha)
                            egresado.save()
                            #Obtain client ip address
                            client_address = ip_client_address(request)

                            # Log de ADICIONAR EGRESADO
                            LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(egresado).pk,
                                object_id       = egresado.inscripcion.id,
                                object_repr     = force_str(egresado),
                                action_flag     = ADDITION,
                                change_message  = 'Adicionado Egresado (' + client_address + ')' )
                        estudiantexegresar = EstudianteXEgresar.objects.all()
                        estudiantexegresar.delete()
                        return HttpResponseRedirect("/egresados")
                    elif action=='becasenescyt':
                        data['title'] = 'Asignar una Beca Senescyt'
                        inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                        isenescyt = inscripcion.beca_senescyt()
                        data['inscripcion'] = inscripcion
                        data['isenescyt'] = isenescyt
                        initial = model_to_dict(isenescyt)
                        data['form'] = InscripcionSenescytForm(initial=initial)
                        return render(request ,"inscripciones/becasenescyt.html" ,  data)

                    elif action=='asignarbeca':
                        data['title'] = 'Asignar una Beca'
                        inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                        data['inscripcion'] = inscripcion
                        data['form'] = BecarioForm()
                        return render(request ,"inscripciones/asignarbeca.html" ,  data)
                    elif action=='recalcular':
                        inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                        if inscripcion.matriculado():
                            matricula = inscripcion.matricula()
                            matricula.recalcular_rubros_segun_creditos()
                            return HttpResponseRedirect('/inscripciones?s='+inscripcion.persona.cedula)
                    elif action=='retirar':
                        data['title'] = 'Retirar Estudiante'
                        data['inscripcion'] = Inscripcion.objects.get(pk=request.GET['id'])
                        data['form'] = RetiradoMatriculaForm(initial={'fecha': datetime.now().strftime("%d-%m-%Y")})
                        return render(request ,"inscripciones/retirar.html" ,  data)

                    #Observaciones a estudiantes
                    elif action=='observaciones':
                        data['title'] = 'Observaciones de Estudiantes'
                        inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                        data['observaciones'] = inscripcion.observacioninscripcion_set.all()
                        data['inscripcion'] = inscripcion
                        return render(request ,"inscripciones/observaciones.html" ,  data)
                    # ENTREGA DE CERTIFICADOS
                    elif action=='certificados':
                        data['title'] = 'Certificados Entregados a Estudiantes'
                        inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                        data['certificados'] = CertificadoEntregado.objects.filter(inscripcion=inscripcion)
                        data['inscripcion'] = inscripcion
                        return render(request ,"inscripciones/certificados.html" ,  data)
                    elif action=='addcertificado':
                        data['title'] = 'Adicionar Certificado del Estudiante'
                        inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                        data['form'] = CertificadoForm()
                        data['inscripcion'] = inscripcion
                        return render(request ,"inscripciones/addcertificado.html" ,  data)
                    elif action=='addobservacion':
                        data['title'] = 'Adicionar Observacion del Estudiante'
                        inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                        data['form'] = ObservacionInscripcionForm()
                        data['inscripcion'] = inscripcion
                        return render(request ,"inscripciones/addobservacion.html" ,  data)
                    elif action=='editobservacion':
                        data['title'] = 'Editar Observacion del Estudiante'
                        observacion = ObservacionInscripcion.objects.get(pk=request.GET['id'])
                        initial = model_to_dict(observacion)
                        data['form'] = ObservacionInscripcionForm(initial=initial)
                        data['observacion'] = observacion
                        return render(request ,"inscripciones/editobservacion.html" ,  data)
                    elif action=='delobservacion':
                        data['title'] = 'Eliminar Observacion del Graduado'
                        data['observacion'] = ObservacionInscripcion.objects.get(pk=request.GET['id'])
                        return render(request ,"inscripciones/delobservacion.html" ,  data)

                    elif action=='detallesusp':
                        data = {}
                        data['suspension'] = InscripcionSuspension.objects.filter(inscripcion__id=request.GET['id']).order_by('fecha')
                        return render(request ,"inscripciones/detallesuspension.html" ,  data)

                    elif action=='obsplagio':
                        inscripcion = Inscripcion.objects.filter(pk=request.GET['id'],plagiotarjeta=True)[:1].get()
                        if RegistroPlagioTarjetas.objects.filter(inscripcion=inscripcion,plagioactivo=True).exists():
                            obsplagio = RegistroPlagioTarjetas.objects.filter(inscripcion=inscripcion,plagioactivo=True).order_by('-fecha')[:1].get()
                            obsplagio = str(str(elimina_tildes(obsplagio.observacionplagio))+' Usuario: '+str(obsplagio.usuario)+' Fecha: '+str(obsplagio.fecha.date()))
                        else:
                            obsplagio=str(elimina_tildes(inscripcion.observacionplagio))

                        return HttpResponse(json.dumps({"result":"ok","plagio":obsplagio}),content_type="application/json")

                    elif action=='obsquitarplagio':
                        obsplagio = Inscripcion.objects.filter(pk=request.GET['id'])[:1].get()
                        obsquitarplagio=RegistroPlagioTarjetas.objects.filter(inscripcion=obsplagio).order_by('-fechaquitaplagio')[:1].get()
                        quitarplagioobs = str(str(elimina_tildes(obsquitarplagio.observacionquitaplagio))+' Usuario: '+str(obsquitarplagio.usrquitaplagio)+' Fecha: '+str(obsquitarplagio.fechaquitaplagio.date()))
                        return HttpResponse(json.dumps({"result":"ok","plagio":quitarplagioobs}),content_type="application/json")

                    elif action == 'verpanel':
                        try:
                            inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                            if PermisoPanel.objects.filter(inscripcion=inscripcion).exists():
                                data['panel'] = PermisoPanel.objects.filter(inscripcion=inscripcion)
                                return render(request ,"inscripciones/panel.html" ,  data)
                            else:
                                return render(request ,"inscripciones/panel.html" ,  data)
                        except:
                            return render(request ,"inscripciones/panel.html" ,  data)

                    elif action == 'borrarpanel':
                        p = PermisoPanel.objects.get(pk=request.GET['id'])
                        i = p.inscripcion
                        #Obtain client ip address
                        client_address = ip_client_address(request)

                        # Log de ADICIONAR RECORD
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(p).pk,
                            object_id       = p.id,
                            object_repr     = force_str(p),
                            action_flag     = DELETION,
                            change_message  = 'Eliminado Permiso Panel (' + client_address + ')' )
                        p.delete()
                        if i.persona.cedula:
                            return  HttpResponseRedirect('/inscripciones?s='+i.persona.cedula)
                        else:
                            return  HttpResponseRedirect('/inscripciones?s='+i.persona.pasaporte)
                    elif action == 'estadistica':
                        inicio = convertir_fecha(request.GET['inicio'])
                        fin = convertir_fecha(request.GET['fin'])
                        # inicio=datetime.strptime('01-01-'+str(anno[2:4]), '%d-%m-%y').date()
                        # fin=datetime.strptime('31-12-'+str(anno[2:4]), '%d-%m-%y').date()
                        #Conformacion de Tabla de grupos socioeconomicos por carreras
                        data = {'title': 'Estadistica de Inscripciones'}
                        addUserData(request,data)
                        carreras = Carrera.objects.all().exclude(id__in=CARRERAS_ID_EXCLUIDAS_INEC)
                        lista_carreras_grupos = []
                        for c in carreras:
                            lista_grupos = []
                            for anuncio in TipoAnuncio.objects.filter(activo=True).order_by('id'):
                                lista_grupos.append(inscritos_anuncio(inicio,fin,anuncio,c))
                            lista_carreras_grupos.append((c.nombre, lista_grupos))

                        data['carreras'] = carreras
                        data['inicio'] = inicio
                        data['fin'] = fin
                        data['lista_carreras_grupos'] = lista_carreras_grupos
                        data['anuncios'] = TipoAnuncio.objects.filter(activo=True).order_by('id')
                        return render(request ,"inscripciones/estadistica.html" ,  data)

                    elif action == 'addprecon':
                        try:
                            inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                            if inscripcion.matricula():
                                matricula = inscripcion.matricula()
                                seminario = GrupoSeminario.objects.get(pk=request.GET['precon'])
                                if seminario.inscritos() < seminario.capacidad:
                                    # if not InscripcionSeminario.objects.filter(matricula = matricula).exists():
                                    if not InscripcionSeminario.objects.filter(gruposeminario=seminario,matricula = matricula).exists():
                                        iseminario = InscripcionSeminario(gruposeminario=seminario,
                                                                          matricula = matricula,
                                                                          fecha=datetime.now().date())
                                        iseminario.save()
                                        hoy =datetime.now().date() + timedelta(2)
                                        if not  seminario.libre :
                                        # if  ObservacionInscripcion.objects.filter(inscripcion=matricula.inscripcion,tipo__id=3).exists():
                                        # if InscripcionSeminario.objects.filter(matricula = matricula).count() % 4 != 0 and InscripcionSeminario.objects.filter(matricula = matricula).count() >= 1:
                                            tipootro = TipoOtroRubro.objects.get(pk=TIPO_OTRO_RUBRO)
                                            rubro = Rubro(fecha=datetime.now().date(),
                                                          valor=seminario.precio,
                                                          inscripcion=matricula.inscripcion,
                                                          cancelado=False,
                                                          fechavence=hoy)
                                            rubro.save()
                                            rubrootro = RubroOtro(rubro=rubro, tipo=tipootro, descripcion='TALLER ' + str(seminario.id) + ' - '+str(seminario.carrera.alias) )

                                            rubrootro.save()
                                            iseminario.rubrootro = rubrootro
                                            iseminario.save()
                                        client_address = ip_client_address(request)

                                        # Log de EDITAR HORARIO CLASE
                                        LogEntry.objects.log_action(
                                            user_id         = request.user.pk,
                                            content_type_id = ContentType.objects.get_for_model(iseminario).pk,
                                            object_id       = iseminario.id,
                                            object_repr     = force_str(iseminario),
                                            action_flag     = ADDITION,
                                            change_message  = 'Adicionada Inscripcion Taller (' + client_address + ')'  )
                                        return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")

                                    # return HttpResponse(json.dumps({"result":"inscrito"}),content_type="application/json")
                                return HttpResponse(json.dumps({"result":"cupo"}),content_type="application/json")
                            return HttpResponse(json.dumps({"result":"matri"}),content_type="application/json")
                        except Exception as ex:
                            return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

                    elif action=='graduarcondu':
                        if INSCRIPCION_CONDUCCION:
                            search = None
                            filtro = None
                            if 'filter' in request.GET:
                                filtro = request.GET['filter']

                            if 's' in request.GET:
                                search = request.GET['s']
                            if search:
                                ss = search.split(' ')
                                while '' in ss:
                                    ss.remove('')
                                if len(ss)==1:
                                    graduados = GraduadoConduccion.objects.filter(Q(inscripcion__persona__nombres__icontains=search) | Q(inscripcion__persona__apellido1__icontains=search) | Q(inscripcion__persona__apellido2__icontains=search) | Q(inscripcion__persona__cedula__icontains=search) | Q(inscripcion__persona__pasaporte__icontains=search)).order_by('inscripcion__persona__apellido1', 'inscripcion__persona__apellido2')
                                else:
                                    graduados = GraduadoConduccion.objects.filter(Q(inscripcion__persona__apellido1__icontains=ss[0]) & Q(inscripcion__persona__apellido2__icontains=ss[1])).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')
                            else:
                                graduados = GraduadoConduccion.objects.all().order_by('inscripcion__persona__apellido1', 'inscripcion__persona__apellido2')

                            if filtro:
                                if  Periodo.objects.filter(pk=filtro).exists():
                                    periodo = Periodo.objects.get(pk=filtro)
                                else:
                                    periodo = Periodo.objects.all()[:1].get()
                                graduados = GraduadoConduccion.objects.filter(periodo=periodo).order_by('inscripcion__persona__apellido1', 'inscripcion__persona__apellido2')


                            paging = Paginator(graduados, 50)
                            p=1
                            try:
                                if 'page' in request.GET:
                                    p = int(request.GET['page'])
                                page = paging.page(p)
                            except:
                                page = paging.page(1)
                            data['paging'] = paging
                            # data['rangospaging'] = paging.rangos_paginado(p)
                            data['page'] = page
                            data['search'] = search if search else ""
                            data['filter'] = periodo if filtro else ""
                            data['periodos'] = Periodo.objects.all().order_by('nombre')
                            data['graduados'] = page.object_list
                            return render(request ,"inscripciones/graduadosbs_condu.html" ,  data)


                    elif action == 'inscripcionexamen':
                        try:
                            inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                            if InscripcionExamen.objects.filter(inscripcion=inscripcion).exists():
                                data['inscripcionexamen'] = InscripcionExamen.objects.filter(inscripcion=inscripcion).order_by('tituloexamencondu','fecha')
                                data['nota_examen']=NOTA_PARA_EXAMEN_CONDUCCION
                                return render(request ,"inscripciones/detalleexamen.html" ,  data)

                        except Exception as ex:
                            return  HttpResponseRedirect("/inscripciones")


                    elif action=='inscriptest':
                        try:
                            #inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                            if Inscripcion.objects.filter(pk=request.GET['id']).exists():
                                inscrip =Inscripcion.objects.filter(pk=request.GET['id'])[:1].get()
                                data['listinscriptest'] = InscripcionTipoTest.objects.filter(inscripcion=inscrip)

                            return render(request ,"testconduccion/detalletest.html" ,  data)
                        except Exception as ex:
                            return  HttpResponseRedirect("/inscripciones")

                    elif action=='verespuestatest':
                        try:
                            #inscripcion = Inscripcion.objects.get(pk=request.GET['idins'])

                            inscriptest= InscripcionTipoTest.objects.get(pk=request.GET['id'])
                            tipotest= TipoTest.objects.get(id=inscriptest.tipotest_id)
                            resultado =ResultadoRespuesta.objects.get(inscripciontipotest=inscriptest,tipotest=tipotest)
                            preguntas= PreguntaTest.objects.filter(tipotest=inscriptest.tipotest,estado=True).order_by('orden')
                            data['listpreguntarespu']=preguntas
                            data['tipotest']=tipotest
                            data['resulttest']=resultado
                            data['inscripcion']=inscriptest.inscripcion
                            return render(request ,"testconduccion/verespuestapregunta.html" ,  data)
                        except Exception as ex:
                            return  HttpResponseRedirect("/inscripciones")



                    elif action == 'examen':


                        data['inscripcion']=Inscripcion.objects.filter(id=request.GET['idins'])[:1].get()
                            # if InscripcionExamen.objects.filter(inscripcion=data['inscripcion'],tituloexamencondu=tituloexamencondu,valida=True,finalizado=True).exists():
                            #     return  HttpResponseRedirect('/examen_conduc?info=Usted ya realizo este examen')

                        inscripcionexamen = InscripcionExamen.objects.filter(id=request.GET['id'])[:1].get()

                        preguntaexamen = DetalleExamen.objects.filter(inscripcionexamen=inscripcionexamen).order_by('id')


                        data['tituloexamencondu'] = inscripcionexamen.tituloexamencondu

                        paging = MiPaginador(preguntaexamen, 20)
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
                        data['preguntaexamen'] = page.object_list
                        data['NOTA_PARA_EXAMEN_CONDUCCION'] = NOTA_PARA_EXAMEN_CONDUCCION

                        return render(request ,"inscripciones/verexamencondu.html" ,  data)

                    elif action == 'detavaliexa':
                        try:
                            inscripcionexamen = InscripcionExamen.objects.get(pk=request.GET['id'])
                            if inscripcionexamen.detallevalidaexist():
                                data['detallevalida'] = inscripcionexamen.detallevalidaexist().order_by('fecha')
                                return render(request ,"inscripciones/detallevaliexamen.html" ,  data)

                        except Exception as ex:
                            return  HttpResponseRedirect("/inscripciones")

                    #Ver Tutorias
                    elif action=='vertutorias':
                        inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                        data['inscripcion'] = inscripcion
                        if Tutoria.objects.filter(estudiante=inscripcion,estado=True).exists():
                            tutorias = Tutoria.objects.get(estudiante=inscripcion,estado=True)
                            data['tutorias'] = tutorias
                            if EstudianteTutoria.objects.filter(tutoria=tutorias.id).exists():
                                data['tuto_estudiante']=EstudianteTutoria.objects.filter(tutoria=tutorias.id)
                        return render(request ,"inscripciones/tutoriasbs.html" ,  data)

                    #eliminar inscripcion cuando los rubros no esten cancelados
                    #OCU 19-febrero-2019 eliminar inscripcion cuando los rubros no esten cancelados
                    elif action=='eliminarinscripcion':
                        data['title'] = 'Eliminar Inscripcion'
                        data['inscripcion'] = Inscripcion.objects.filter(pk=request.GET['id'])[:1].get()
                        return render(request ,"inscripciones/borrar_inscripcion.html" ,  data)

                    elif action == 'ingresacomprobante':
                        if Inscripcion.objects.filter(id=request.GET['idins']).exists():
                            inscripcion = Inscripcion.objects.get(id=request.GET['idins'])

                            data['pr'] = 1
                            tipoespecie = TipoEspecieValorada.objects.get(id=ID_TIPO_SOLICITUD)

                            data['title'] = 'Nuevo Tramite'
                            data['form'] = EspecieUniversalForm(initial={'tipoe': tipoespecie})
                            data['urlaccion'] = 'inscripciones'
                            data['inscripcion'] = inscripcion
                            if "error" in request.GET:
                                data['error'] = request.GET['error']
                            return render(request ,"inscripciones/adicionartramite.html" ,  data)
                        return HttpResponseRedirect(
                                    "/inscripciones?error=No existe la Inscripcion")
                    elif action == 'vercomprobante':

                        data['inscripcion'] = Inscripcion.objects.get(id=request.GET['id'])
                        data['solicitudes'] = SolicitudSecretariaDocente.objects.filter(persona=data['inscripcion'].persona,solicitudestudiante__tipoe__id=ID_TIPO_SOLICITUD).exclude(solicitudestudiante=None)

                        return render(request ,"inscripciones/vercomprobante.html" ,  data)

                    elif action == 'versoportefraude':
                        inscripcion = Inscripcion.objects.get(id=request.GET['id'])
                        data['inscripcion'] = inscripcion
                        facturas = Factura.objects.filter(pagos__rubro__inscripcion=inscripcion).distinct().order_by('-fecha')
                        fraudes = None
                        if RegistroPlagioTarjetas.objects.filter(inscripcion=inscripcion).exists():
                            fraudes = RegistroPlagioTarjetas.objects.filter(inscripcion=inscripcion).order_by('-id')
                            facturas = facturas.exclude(id__in=fraudes.values_list('factura_id', flat=True)).distinct().order_by('-fecha')
                        data['facturas'] = facturas
                        data['soportesfraude'] = fraudes
                        data['valorplagio'] = RUBRO_PLAGIO
                        if 'error' in request.GET:
                            data['error'] = request.GET['error']

                        return render(request ,"inscripciones/versoportesfraude.html" ,  data)

                    elif action == 'aprobar':
                        data['title'] = 'Aprobar documento subido '
                        documento =  DocumentoInscripcion.objects.get(pk=request.GET['id'])
                        data['documento'] = documento
                        data['form'] = AprobarDocumentoForm()
                        return render(request ,"inscripciones/aprobardocumento.html" ,  data)

                    #OCastillo 18-11-2021 generar solicitud parte 2
                    elif action=='generartramite2':
                        locale.setlocale(locale.LC_ALL,"")
                        solicitud=SolicitudEstudiante.objects.filter(pk=request.GET['id'])[:1].get()
                        data['solicitud']=solicitud
                        data['mes']=str(solicitud.fecha.strftime("%B")).capitalize()
                        data['anio']=solicitud.fecha.year
                        data['dia2']=solicitud.fecha.day
                        if 'cantidad' in request.GET:
                            data['cantidad'] = int(request.GET['cantidad'])
                        return render(request ,"inscripciones/"+str(solicitud.solicitud.html)+".html" ,  data)

                    #OCastillo 18-11-2021 generar solicitud parte1
                    elif action=='generartramite':
                        if 'cantidad' in request.GET:
                            data['cantidad'] = int(request.GET['cantidad'])

                        matricula=None
                        inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                        data['inscripcion'] = inscripcion
                        if  inscripcion.matricula():
                            matricula = inscripcion.matricula()
                            data['matricula']=matricula
                        solicitud= SolicitudOnline.objects.get(pk=3)
                        data['solicitud'] = solicitud
                        if not SolicitudEstudiante.objects.filter(inscripcion=inscripcion,solicitud=solicitud).exists() or solicitud.libre:
                            form =getattr(forms,solicitud.form,None)()
                            form.for_tipo(inscripcion)
                            if solicitud.libre:
                                data['libre'] = True
                            if 'error' in request.GET:
                                data['error'] = request.GET['error']
                            data['form'] = form
                            data['soli']=0
                            if solicitud.valida_malla:
                                if HistoricoRecordAcademico.objects.filter( inscripcion=matricula.inscripcion).exists():
                                    c = 0
                                    mallainscripcion = matricula.inscripcion.malla_inscripcion()
                                    if not mallainscripcion:
                                        return  HttpResponseRedirect('/?info=No tiene una malla asociada')
                                    if len(AsignaturaMalla.objects.filter(malla=mallainscripcion.malla).exclude(nivelmalla=NIVEL_MALLA_CERO).exclude(asignatura__id__in=ASIGNATURA_EXAMEN_GRADO_CONDU).exclude(asignatura__nivelacion=True).distinct('asignatura').values('asignatura')) > len(HistoricoRecordAcademico.objects.filter( inscripcion=matricula.inscripcion).exclude(asignatura__id__in=ASIGNATURA_EXAMEN_GRADO_CONDU).exclude(asignatura__nivelacion=True).distinct('asignatura').values('asignatura')):
                                        return  HttpResponseRedirect('/?info=Malla Incompleta no Puede Realizar Solicitud ')
                                    a=AsignaturaMalla.objects.filter(malla__id=mallainscripcion.malla.id).exclude(nivelmalla__id=NIVEL_MALLA_CERO).exclude(asignatura__id__in=ASIGNATURA_EXAMEN_GRADO_CONDU).exclude(asignatura__nivelacion=True).values('asignatura')
                                    if matricula.inscripcion.carrera.online:
                                        asistenciaparaaprobar = 0
                                    else:
                                        asistenciaparaaprobar = ASIST_PARA_APROBAR
                                    c = HistoricoRecordAcademico.objects.filter(asignatura__in=a, nota__gte=NOTA_PARA_APROBAR, asistencia__gte=asistenciaparaaprobar,inscripcion=matricula.inscripcion).exclude(asignatura__id__in=ASIGNATURA_EXAMEN_GRADO_CONDU).exclude(asignatura__nivelacion=True).distinct('asignatura').values('asignatura')
                                    if a.count() > c.count():
                                        return  HttpResponseRedirect('/?info=Tiene Asignaturas Reprobadas, no Puede Realizar Solicitud')
                                else:
                                    return  HttpResponseRedirect('/?info=Malla Incompleta no Puede Realizar Solicitud ')
                            data['ESPECIE_JUSTIFICA_FALTA'] = ESPECIE_JUSTIFICA_FALTA
                            data['ESPECIE_JUSTIFICA_FALTA_AU'] = ESPECIE_JUSTIFICA_FALTA_AU
                            data['ID_TIPO_SOLICITUD']=ID_TIPO_SOLICITUD

                            return render(request ,"inscripciones/datos.html" ,  data)

                    elif action=='practicas_act':
                        if Inscripcion.objects.filter(pk=request.GET['id']).exists():
                            inscrip = Inscripcion.objects.get(pk=request.GET['id'])
                            ced = inscrip.persona.cedula
                            if Inscripcion.objects.filter(persona__cedula=ced).exclude(pk=request.GET['id']).exists():
                                inscripcion = Inscripcion.objects.filter(persona__cedula=ced).exclude(pk=request.GET['id'])
                                data['inscripciones'] = inscripcion

                        return render(request ,"inscripciones/actualizar_practicas.html" ,  data)

                    elif action =='generarsolicitud':
                        try:
                            solicitud = SolicitudEstudiante.objects.filter(id=request.GET['id'])[:1].get()
                            asist = None
                            inscripcion=None
                            if solicitud.tipoe.id == ESPECIE_JUSTIFICA_FALTA_AU:
                                if solicitud.inscripcion.matricula():
                                    matricula = solicitud.inscripcion.matricula()
                                    inscripcion = solicitud.inscripcion.id
                                    leccionesGrupo = LeccionGrupo.objects.filter(fecha__lte=solicitud.fecha,profesor=solicitud.profesor,materia__nivel__periodo__activo=True,lecciones__clase__materia=solicitud.materia.materia,lecciones__asistencialeccion__matricula=matricula,lecciones__asistencialeccion__asistio=False,lecciones__asistencialeccion__fechaaprobacion=None).order_by('-fecha', '-horaentrada')
                                    asist = LeccionGrupo.objects.filter(fecha__lte=solicitud.fecha,profesor=solicitud.profesor,materia__nivel__periodo__activo=True,lecciones__clase__materia=solicitud.materia.materia,lecciones__asistencialeccion__matricula=matricula,lecciones__asistencialeccion__asistio=False,lecciones__asistencialeccion__fechaaprobacion=None).order_by('-fecha', '-horaentrada').values('lecciones__asistencialeccion')

                                    if leccionesGrupo.count() == 0:
                                        return HttpResponseRedirect("/inscripciones?action=generartramite&id="+str(inscripcion)+ "&error=NO TIENE INASISTENCIAS CON EL DOCENTE SELECCIONADO")
                            if asist:
                                for a in AsistenciaLeccion.objects.filter(id__in=asist)[:5]:
                                    a.aprobado = False
                                    a.save()

                            hoy =datetime.now().date()
                            solicitud.solicitado=True

                            solicitud.fecha = datetime.now()
                            solicitud.save()
                            rubro = None
                            if solicitud.solicitud.libre:
                                tipoEspecie = TipoEspecieValorada.objects.get(pk=solicitud.tipoe.id)

                                rubro = Rubro(fecha=datetime.now().date(),
                                            valor=tipoEspecie.precio,
                                            inscripcion = solicitud.inscripcion,
                                            cancelado=tipoEspecie.precio==0,
                                            # fechavence=datetime.now().date()  + timedelta(45))
                                            # OCastillo 11-04-2022 se debe generar la especie con la fecha del dia
                                            fechavence=datetime.now().date())
                                rubro.save()

                                # Rubro especie valorada
                                rubroespecie = generador_especies.generar_especie(rubro=rubro, tipo=tipoEspecie)
                                rubroespecie.autorizado=False
                                rubroespecie.save()
                                #OCastillo 27-04-2022 nueva especie cambio de modalidad
                                if tipoEspecie.id==84:
                                    rubronuevo = Rubro(fecha=datetime.now().date(),
                                            valor=50,
                                            inscripcion = solicitud.inscripcion,
                                            cancelado=tipoEspecie.precio==0,
                                            fechavence=datetime.now().date())
                                    rubronuevo.save()

                                    rubrootro = RubroOtro(rubro=rubronuevo,
                                            tipo_id = TIPO_OTRO_RUBRO,
                                            descripcion='DERECHO')
                                    rubrootro.save()

                                #OCastillo 12-05-2022 nueva especie examen complexivo
                                #OCastillo 13-07-2022 otro rubro cambia a 10 examen complexivo
                                if tipoEspecie.id==85:
                                    rubronuevo = Rubro(fecha=datetime.now().date(),
                                            valor=10,
                                            inscripcion = solicitud.inscripcion,
                                            cancelado=tipoEspecie.precio==0,

                                            fechavence=datetime.now().date())
                                    rubronuevo.save()

                                    rubrootro = RubroOtro(rubro=rubronuevo,
                                            tipo_id = TIPO_OTRO_RUBRO,
                                            descripcion='DERECHO A COMPLEXIVO')
                                    rubrootro.save()


                                if solicitud.materia:
                                    rubroespecie.materia = solicitud.materia
                                    rubroespecie.save()

                            else:
                                if solicitud.solicitud.valor > 0:
                                    valor = float(solicitud.solicitud.valor)
                                    tipootro = TipoOtroRubro.objects.get(pk=TIPO_RUBRO_SOLICITUD)

                                    rubro = Rubro(fecha=datetime.now().date(),
                                                  valor=valor,
                                                  inscripcion=solicitud.inscripcion,
                                                  cancelado=False,
                                                  fechavence=hoy)
                                    rubro.save()
                                    rubrootro = RubroOtro(rubro=rubro, tipo=tipootro, descripcion='SOLICITUD ' + elimina_tildes(solicitud.solicitud.nombre) )
                                    rubrootro.save()

                            client_address = ip_client_address(request)
                            LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(solicitud).pk,
                                object_id       = solicitud.id,
                                object_repr     = force_str(solicitud),
                                action_flag     = ADDITION,
                                change_message  = 'Generada Solicitud OnLine desde Inscripciones'+ str(solicitud.tipoe) + '(' + client_address + ')' )

                            if rubro:
                                solicitud.rubro = rubro
                                solicitud.save()
                            if not solicitud.solicitud.libre:
                                solicitud.correo_estudiante()
                            else:
                                if EMAIL_ACTIVE:
                                    emailestudiante=elimina_tildes(solicitud.inscripcion.persona.emailinst)+','+elimina_tildes(solicitud.inscripcion.persona.email)
                                    mail_correoalumnoespecie(solicitud,emailestudiante)
                            listaespecies=[]
                            #OCastillo 08-04-2022 desde esta accion se asigna el requerimiento al asistente que lo genera
                            if rubro.cancelado==False :
                                coordinacion = Coordinacion.objects.filter(carrera=solicitud.inscripcion.carrera)[:1].get()
                                for cdp in  CoordinacionDepartamento.objects.filter(coordinacion=coordinacion):
                                    if EspecieGrupo.objects.filter(departamento=cdp.departamento,tipoe=solicitud.tipoe).exists():
                                        asistentes=None
                                        #OCastillo 24-11-2021 debe asignarse al usuario que genera el tramite
                                        if HorarioAsistenteSolicitudes.objects.filter(usuario=request.user,fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time()).exists():
                                             horarioasis = HorarioAsistenteSolicitudes.objects.filter(usuario=request.user,fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time()).values('usuario')
                                             asistentes = AsistenteDepartamento.objects.filter(departamento=cdp.departamento,persona__usuario__id__in=horarioasis).exclude(puedereasignar=True).order_by('cantidad')
                                        else:
                                            horarioasis = HorarioAsistenteSolicitudes.objects.filter(fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time()).values('usuario')
                                            asistentes = AsistenteDepartamento.objects.filter(departamento=cdp.departamento,persona__usuario__id__in=horarioasis).exclude(puedereasignar=True).order_by('cantidad')

                                        if asistentes:
                                            for asis in asistentes:
                                                rubroespecie.usrasig = asis.persona.usuario
                                                rubroespecie.fechaasigna = datetime.now()
                                                rubroespecie.departamento= asis.departamento
                                                rubroespecie.save()

                                                asis.cantidad =asis.cantidad +1

                                                asis.save()
                                                listaespecies.append(asis.persona.emailinst)
                                                break
                                if listaespecies:
                                    try:
                                         hoy = datetime.now().today()
                                         contenido = "  Tramites Asignados"
                                         descripcion = "Ud. tiene tramites por atender"
                                         send_html_mail(contenido,
                                            "emails/notificacion_tramites_adm.html", {'fecha': hoy,'contenido': contenido,'descripcion':descripcion,'opcion':'1'},listaespecies)
                                    except Exception as e:
                                        print((e))
                                        pass
                            return HttpResponseRedirect("inscripciones?info=TRAMITE GENERADO CORRECTAMENTE")

                        except Exception as e:
                            return HttpResponseRedirect("/inscripciones?error="+str(e))

                    elif action=='generarespecieasuntos':
                        if 'cantidad' in request.GET:
                            data['cantidad'] = int(request.GET['cantidad'])

                        if 'tipoespecie' in request.GET:
                            tipoespecie= request.GET['tipoespecie']
                        matricula=None
                        inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                        data['inscripcion'] = inscripcion
                        if  inscripcion.matricula():
                            matricula = inscripcion.matricula()
                            data['matricula']=matricula
                        solicitud= SolicitudOnline.objects.get(pk=ID_SOLIC__ONLINE)
                        data['solicitud'] = solicitud
                        if not SolicitudEstudiante.objects.filter(inscripcion=inscripcion,solicitud=solicitud).exists() or solicitud.libre:
                            form =getattr(forms,solicitud.form,None)()
                            form.for_tipoasuntos(inscripcion)
                            if solicitud.libre:
                                data['libre'] = True
                            if 'error' in request.GET:
                                data['error'] = request.GET['error']
                            data['form'] = form
                            data['soli']=0
                            if tipoespecie=='asentamiento':
                                data['ESPECIE_ASENTAMIENTO_SINVALOR'] = ESPECIE_ASENTAMIENTOCONVENIO_SINVALOR
                                data['ESPECIE_ASENTAMIENTO_CONNVALOR'] = ESPECIE_ASENTAMIENTOCONVENIO_CONVALOR
                            else:
                                data['ESPECIE_JUSTIFICA_FALTA'] = ESPECIE_JUSTIFICA_FALTA
                                data['ESPECIE_JUSTIFICA_FALTA_AU'] = ESPECIE_JUSTIFICA_FALTA_AU
                            data['ID_TIPO_SOLICITUD']=ID_TIPO_SOLICITUD

                            return render(request ,"inscripciones/datosasuntos.html" ,  data)

                    return HttpResponseRedirect("/inscripciones")

                else:

                    search = None
                    todos = None
                    activos = None
                    inactivos = None
                    gruposc = None
                    band=0
                    carrerasfiltro=None
                    usuarioreporte=request.user
                    administrativo=Persona.objects.filter(usuario=request.user)[:1].get()

                    if ConvenioUsuario.objects.filter(usuario=request.user).exists():
                        convenio = ConvenioUsuario.objects.filter(usuario=request.user).values('convenio')
                        gruposc = Grupo.objects.filter(convenio__in=convenio)
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
                            if carrerasfiltro:
                                inscripciones = Inscripcion.objects.filter(Q(persona__nombres__icontains=search) | Q(persona__apellido1__icontains=search) | Q(persona__apellido2__icontains=search) | Q(persona__cedula__icontains=search) | Q(persona__pasaporte__icontains=search) | Q(identificador__icontains=search) | Q(inscripciongrupo__grupo__nombre__icontains=search) | Q(carrera__nombre__icontains=search) | Q(persona__usuario__username__icontains=search), carrera__in=carrerasfiltro).order_by('persona__apellido1')
                            if gruposc:
                                inscripciones = Inscripcion.objects.filter(Q(persona__nombres__icontains=search) | Q(persona__apellido1__icontains=search) | Q(persona__apellido2__icontains=search) | Q(persona__cedula__icontains=search) | Q(persona__pasaporte__icontains=search) | Q(identificador__icontains=search) | Q(inscripciongrupo__grupo__nombre__icontains=search) | Q(carrera__nombre__icontains=search) | Q(persona__usuario__username__icontains=search), inscripciongrupo__grupo__in=gruposc).order_by('persona__apellido1')
                            else:
                                inscripciones = Inscripcion.objects.filter(Q(persona__nombres__icontains=search) | Q(persona__apellido1__icontains=search) | Q(persona__apellido2__icontains=search) | Q(persona__cedula__icontains=search) | Q(persona__pasaporte__icontains=search) | Q(identificador__icontains=search) | Q(inscripciongrupo__grupo__nombre__icontains=search) | Q(carrera__nombre__icontains=search) | Q(persona__usuario__username__icontains=search)).order_by('persona__apellido1')
                        else:
                            if gruposc:
                                inscripciones = Inscripcion.objects.filter(Q(persona__apellido1__icontains=ss[0]) & Q(persona__apellido2__icontains=ss[1]), inscripciongrupo__grupo__in=gruposc).order_by('persona__apellido1','persona__apellido2','persona__nombres')
                            else:
                                inscripciones = Inscripcion.objects.filter(Q(persona__apellido1__icontains=ss[0]) & Q(persona__apellido2__icontains=ss[1])).order_by('persona__apellido1','persona__apellido2','persona__nombres')

                    else:
                        fech=datetime.now().year
                        fecha= '2014-12-01'
                        if carrerasfiltro:
                            inscripciones = Inscripcion.objects.filter(carrera__in=carrerasfiltro,persona__usuario__is_active=True).order_by('persona__apellido1')
                        if gruposc:
                            inscripciones = Inscripcion.objects.filter(inscripciongrupo__grupo__in=gruposc,persona__usuario__is_active=True).order_by('persona__apellido1')
                        else:
                            inscripciones = Inscripcion.objects.filter(persona__usuario__is_active=True).order_by('persona__apellido1')
                        # inscripciones = Inscripcion.objects.filter(persona__usuario__is_active=True,fecha__gte=fecha).order_by('persona__apellido1')[:100]

                    if 'g' in request.GET:
                        grupoid = request.GET['g']
                        data['grupo'] = Grupo.objects.get(pk=request.GET['g'])
                        data['grupoid'] = int(grupoid) if grupoid else ""
                        if gruposc:
                            inscripciones =  Inscripcion.objects.filter(carrera__grupocoordinadorcarrera__group__in=request.user.groups.all(), inscripciongrupo__grupo=data['grupo']).distinct()
                        else:
                            inscripciones =  Inscripcion.objects.filter(carrera__grupocoordinadorcarrera__group__in=request.user.groups.all(), inscripciongrupo__grupo=data['grupo']).distinct()

                    if 'c' in request.GET:
                        carreraid = request.GET['c']
                        data['carrera'] = Carrera.objects.get(pk=request.GET['c'])
                        data['carreraid'] = int(carreraid) if carreraid else ""
                        if carrerasfiltro:
                            inscripciones = Inscripcion.objects.filter(carrera__grupocoordinadorcarrera__group__in=request.user.groups.all(),carrera=data['carrera']).distinct().order_by('persona__apellido1')
                        else:
                            inscripciones = Inscripcion.objects.filter(carrera__grupocoordinadorcarrera__group__in=request.user.groups.all(),carrera=data['carrera']).distinct().order_by('persona__apellido1')
                    # else:
                    #     inscripciones = inscripciones.filter(carrera__grupocoordinadorcarrera__group__in=request.user.groups.all()).distinct()

                    if todos:
                        if  gruposc:
                            inscripciones = Inscripcion.objects.filter(inscripciongrupo__grupo__in=gruposc).order_by('persona__apellido1')
                        else:
                            inscripciones = Inscripcion.objects.all().order_by('persona__apellido1')

                    if activos:
                        if gruposc:
                            inscripciones = Inscripcion.objects.filter(persona__usuario__is_active=True, inscripciongrupo__grupo__in=gruposc).order_by('persona__apellido1')
                        else:
                            inscripciones = Inscripcion.objects.filter(persona__usuario__is_active=True).order_by('persona__apellido1')
                    if inactivos:
                        if gruposc:
                            inscripciones = Inscripcion.objects.filter(persona__usuario__is_active=False, inscripciongrupo__grupo=gruposc).order_by('persona__apellido1')
                        else:
                            inscripciones = Inscripcion.objects.filter(persona__usuario__is_active=False).order_by('persona__apellido1')

                    if CENTRO_EXTERNO and not ('s' in request.GET):
                        inscripciones = Inscripcion.objects.all().order_by('persona__apellido1')

                    paging = MiPaginador(inscripciones, 20)
                    p = 1
                    try:
                        if 'page' in request.GET:
                            p = int(request.GET['page'])
                            # if band==0:
                            #     inscripciones = Inscripcion.objects.all().order_by('persona__apellido1')
                            paging = MiPaginador(inscripciones, 20)
                        page = paging.page(p)
                    except Exception as ex:
                        page = paging.page(1)

                    # Para atencion al cliente
                    atiende=False
                    idpresona=data['persona'].id
                    if AtencionCliente.objects.filter(persona=idpresona,estado=True).exists():
                        atiende=True
                    data['atiende'] = atiende

                    data['paging'] = paging
                    data['rangospaging'] = paging.rangos_paginado(p)
                    data['page'] = page
                    data['search'] = search if search else ""
                    data['todos'] = todos if todos else ""
                    data['gruposc'] = gruposc if gruposc else ""
                    data['carrerasfiltro'] = carrerasfiltro if carrerasfiltro else ""
                    data['activos'] = activos if activos else ""
                    data['inactivos'] = inactivos if inactivos else ""
                    # ///cambio funciones
                    inscripcionespage = page.object_list
                    if str(request.user) == 'jjurgiles':
                            end_time = datetime.now().time()
                            print("INGRESO ANTES DEL FOR  INSCRIPCIONES "+str(request.user)+" - "+str(end_time))
                    for inscripcion in inscripcionespage:
                    # for inscripcion in inscripcionespage.filter().prefetch_related('matricula_set','egresado_set','rubro_set').select_related('persona'):
                        if str(request.user) == 'jjurgiles':
                            end_time = datetime.now().time()
                            print("INGRESO FUNCION 1  INSCRIPCIONES "+str(request.user)+" - "+str(end_time))
                        inscripcion.nombrecompleto = inscripcion.persona.nombre_completo()
                        inscripcion.nombrecompletoinverso = inscripcion.persona.nombre_completo_inverso()

                        if str(request.user) == 'jjurgiles':
                            end_time = datetime.now().time()
                            print("INGRESO FUNCION 2  INSCRIPCIONES "+str(request.user)+' '+str(start_time)+" - "+str(end_time))
                        inscripcion.tipobeneficio = inscripcion.tipo_beneficio()

                        if str(request.user) == 'jjurgiles':
                            end_time = datetime.now().time()
                            print("INGRESO FUNCION 3  INSCRIPCIONES "+str(request.user)+' '+str(start_time)+" - "+str(end_time))
                        inscripcion.alumnoestado = inscripcion.alumno_estado()

                        if str(request.user) == 'jjurgiles':
                            end_time = datetime.now().time()
                            print("INGRESO FUNCION 4  INSCRIPCIONES "+str(request.user)+' '+str(start_time)+" - "+str(end_time))
                        inscripcion.datosincompletos = inscripcion.persona.datos_incompletos()

                        if str(request.user) == 'jjurgiles':
                            end_time = datetime.now().time()
                            print("INGRESO FUNCION 5  INSCRIPCIONES "+str(request.user)+' '+str(start_time)+" - "+str(end_time))
                        inscripcion.datosmedicosincompletos = inscripcion.persona.datos_medicos_incompletos()

                        if str(request.user) == 'jjurgiles':
                            end_time = datetime.now().time()
                            print("INGRESO FUNCION 6  INSCRIPCIONES "+str(request.user)+' '+str(start_time)+" - "+str(end_time))
                        inscripcion.valoracionmedicaincompleta = inscripcion.persona.valoracion_medica_incompleta()

                        if str(request.user) == 'jjurgiles':
                            end_time = datetime.now().time()
                            print("INGRESO FUNCION 7  INSCRIPCIONES "+str(request.user)+' '+str(start_time)+" - "+str(end_time))
                        inscripcion.becasenescyt = inscripcion.beca_senescyt()

                        if str(request.user) == 'jjurgiles':
                            end_time = datetime.now().time()
                            print("INGRESO FUNCION 8  INSCRIPCIONES "+str(request.user)+' '+str(start_time)+" - "+str(end_time))
                        inscripcion.becaasignadaobj = inscripcion.beca_asignada_obj() if inscripcion.beca_asignada() else False

                        if str(request.user) == 'jjurgiles':
                            end_time = datetime.now().time()
                            print("INGRESO FUNCION 9  INSCRIPCIONES "+str(request.user)+' '+str(start_time)+" - "+str(end_time))
                        inscripcion.tieneprocesosolicitudbecafun = inscripcion.tieneprocesosolicitudbeca()

                        if str(request.user) == 'jjurgiles':
                            end_time = datetime.now().time()
                            print("INGRESO FUNCION 10  INSCRIPCIONES "+str(request.user)+' '+str(start_time)+" - "+str(end_time))
                        inscripcion.tieneprocesodobe = inscripcion.tiene_procesodobe()

                        if str(request.user) == 'jjurgiles':
                            end_time = datetime.now().time()
                            print("INGRESO FUNCION 11  INSCRIPCIONES "+str(request.user)+' '+str(start_time)+" - "+str(end_time))
                        inscripcion.tieneprocesodobeaprobado = inscripcion.tiene_procesodobe_aprobado() if inscripcion.tieneprocesodobe else None

                        if str(request.user) == 'jjurgiles':
                            end_time = datetime.now().time()
                            print("INGRESO FUNCION 12  INSCRIPCIONES "+str(request.user)+' '+str(start_time)+" - "+str(end_time))
                        inscripcion.estaretiradoper = inscripcion.esta_retiradoper(data['periodo'])

                        if str(request.user) == 'jjurgiles':
                            end_time = datetime.now().time()
                            print("INGRESO FUNCION 13  INSCRIPCIONES "+str(request.user)+' '+str(start_time)+" - "+str(end_time))
                        inscripcion.tieneaprobadoexamen = inscripcion.tiene_aprobado_examen()


                        if str(request.user) == 'jjurgiles':
                            end_time = datetime.now().time()
                            print("INGRESO FUNCION 14  INSCRIPCIONES "+str(request.user)+' '+str(start_time)+" - "+str(end_time))
                        inscripcion.tienedeuda = inscripcion.tiene_deuda()

                        if str(request.user) == 'jjurgiles':
                            end_time = datetime.now().time()
                            print("INGRESO FUNCION 15  INSCRIPCIONES "+str(request.user)+' '+str(start_time)+" - "+str(end_time))
                        inscripcion.adeudaalafecha = inscripcion.adeuda_a_la_fecha() if inscripcion.tienedeuda else ''

                        if str(request.user) == 'jjurgiles':
                            end_time = datetime.now().time()
                            print("INGRESO FUNCION 16  INSCRIPCIONES "+str(request.user)+' '+str(start_time)+" - "+str(end_time))
                        inscripcion.tienetesthecho = inscripcion.tiene_test_hecho()

                        if str(request.user) == 'jjurgiles':
                            end_time = datetime.now().time()
                            print("INGRESO FUNCION 17  INSCRIPCIONES "+str(request.user)+' '+str(start_time)+" - "+str(end_time))
                        inscripcion.matriculaperiodo = inscripcion.matricula_periodo(data['periodo'])

                        if str(request.user) == 'jjurgiles':
                            end_time = datetime.now().time()
                            print("INGRESO FUNCION 18  INSCRIPCIONES "+str(request.user)+' '+str(start_time)+" - "+str(end_time))
                        inscripcion.numeromstring = inscripcion.numerom_string() if inscripcion.numerom else None

                        if str(request.user) == 'jjurgiles':
                            end_time = datetime.now().time()
                            print("INGRESO FUNCION 19  INSCRIPCIONES "+str(request.user)+' '+str(start_time)+" - "+str(end_time))
                        inscripcion.tieneobsnombramiento = inscripcion.tiene_obs_nombramiento()
                        inscripcion.alumnoestado = inscripcion.alumno_estado()
                        inscripcion.verentregakituniforme = inscripcion.ver_entrega_kit_uniforme()
                        inscripcion.kitestaentregado = inscripcion.kit_esta_entregado()
                        inscripcion.kitentregado = inscripcion.kit_entregado() if inscripcion.kitestaentregado else False
                        inscripcion.kitcongresovalor = inscripcion.kit_congreso_valor()
                        inscripcion.tieneobsnombramiento = inscripcion.tiene_obs_nombramiento()
                        inscripcion.verentregajuegutecanasta = inscripcion.ver_entrega_juegute_canasta()
                        inscripcion.asistiocofia = inscripcion.asistio_cofia()
                        inscripcion.inscripcionexamenfun = inscripcion.inscripcionexamen()
                        inscripcion.tieneprecongreso = inscripcion.tiene_precongreso()
                        inscripcion.tienedeudacertificadocongreso = inscripcion.tiene_deuda_certificado_congreso()
                        inscripcion.tienedeudacertificadocongreso = inscripcion.tiene_deuda_certificado_congreso()
                        inscripcion.downloadfoto = inscripcion.download_foto()
                        inscripcion.tienepracticas = inscripcion.tiene_practicas()
                        inscripcion.hpracticasvinculacion = inscripcion.h_practicas_vinculacion()
                        inscripcion.tienevinculacion = inscripcion.tiene_vinculacion()
                        inscripcion.solicitudsecrefun = inscripcion.solicitudsecre()
                        inscripcion.grupofun = inscripcion.grupo()
                        inscripcion.vendedorfun = inscripcion.vendedor()
                        inscripcion.egresadofun = inscripcion.egresado()
                        inscripcion.retiradofun = inscripcion.retirado()
                        inscripcion.matriculadofun = inscripcion.matriculado()
                        inscripcion.matriculafun = inscripcion.matricula()
                        inscripcion.tieneinactivacion = inscripcion.tiene_inactivacion()
                        inscripcion.clavepadrefun = inscripcion.clave_padre()
                        inscripcion.cantidadobservacionesfun = inscripcion.cantidadobservaciones()
                        inscripcion.historicopract = inscripcion.historico_pract()
                        inscripcion.inscripcionsuspenexisfun = inscripcion.inscripcionsuspenexis()
                        inscripcion.posponerdesc = inscripcion.posponer_desc()
                        inscripcion.totalpagado = inscripcion.total_pagado()
                        inscripcion.tienesolicitudbeca = inscripcion.tiene_solicitudbeca()
                        if str(request.user) == 'jjurgiles':
                            end_time = datetime.now().time()
                            print("INGRESO FUNCION 20  INSCRIPCIONES "+str(request.user)+' '+str(start_time)+" - "+str(end_time))
                    administrativo.pertenecesoporte = administrativo.pertenece_soporte()
                    administrativo.pertenecepracticas = administrativo.pertenece_practicas()
                    administrativo.pertenececonvenioapol = administrativo.pertenece_convenioapol()
                    administrativo.pertenecesecretaria = administrativo.pertenece_secretaria()
                    administrativo.pertenecejefeadmision = administrativo.pertenece_jefeadmision()
                    administrativo.perteneceasuntos = administrativo.pertenece_asuntos()
                    administrativo.perteneceadmision = administrativo.pertenece_admision()
                    data['administrativo'] = administrativo
                    # //////
                    data['inscripciones'] = inscripcionespage
                    data['utiliza_grupos_alumnos'] = UTILIZA_GRUPOS_ALUMNOS
                    data['reporte_ficha_id'] = REPORTE_CERTIFICADO_INSCRIPCION
                    data['clave'] = DEFAULT_PASSWORD
                    data['usafichamedica'] = UTILIZA_FICHA_MEDICA
                    data['centroexterno'] = CENTRO_EXTERNO
                    data['matriculalibre'] = MODELO_EVALUACION==EVALUACION_TES
                    if gruposc:
                        data['grupos'] = Grupo.objects.filter(id__in=gruposc).order_by('nombre')
                    else:
                        data['grupos'] = Grupo.objects.all().order_by('nombre')
                    data['inscripcion_conduccion'] = INSCRIPCION_CONDUCCION
                    data['extra'] = 1
                    form = SuspensionForm(initial={'fechasus': datetime.now().date()})
                    data['form'] = form
                    data['formkit'] = KitCongresoForm()
                    data['formplagio'] = PlagioForm()
                    data['valorplagio'] = RUBRO_PLAGIO
                    data['frmvend'] = VendedorInscForm()
                    data['frmpromocion'] = PromocionInscForm()
                    data['frmentregartit'] = VerEntregarTitForm()
                    data['frmtitulo'] = RecibirTituloForm(initial={'fechatitulo': datetime.now().date()})
                    data['formpanel'] = AdicionarPanelForm()
                    data['formprecongreso'] = PrecongresoForm()
                    data['formestd'] = RangoNCForm(initial={'inicio': datetime.now().date(),'fin': datetime.now().date()})
                    #data['vendedores'] = User.objects.filter(pk__in=InscripcionAspirantes.objects.filter().distinct('usuario').values('usuario'),is_active=True)
                    data['vendedores'] = User.objects.filter(groups__id=ADMISION_GROUP_ID,is_active=True)
                    data['formkitUniforme'] = KitUniformeMunicipioForm()
                    data['formentregaJuguete'] = EntregaJugueteForm()




                    if 'idinscripexam' in request.GET:
                        data['inscripexam'] = InscripcionExamen.objects.get(id=request.GET['idinscripexam'])

                    if 'info' in request.GET:
                        data['info'] = request.GET['info']

                    if 'doc' in request.GET:
                        data['docu'] = request.GET['doc']
                        data['usr_imp'] =  usuarioreporte
                        data['identidad'] = request.GET ['s']

                    if 'doc2' in request.GET:
                        data['docu2'] = request.GET['doc2']
                        data['usr_imp'] =  usuarioreporte
                        data['fotos'] = request.GET ['fotos']
                        data['titulo'] = request.GET ['titulo']
                        data['cedula'] = request.GET ['cedula']
                        data['votacion'] = request.GET ['votacion']
                        data['actaconv'] = request.GET ['actaconv']
                        data['partidanacimiento'] = request.GET ['partidanacimiento']
                        data['acta'] = request.GET ['acta']
                        data['identidad'] = request.GET ['s']

                    if 'ins' in request.GET:
                        data['ins'] = request.GET['ins']

                    if 'error' in request.GET:
                        data['error'] = request.GET['error']

                    if 'info' in request.GET:
                        data['info'] = request.GET['info']

                    if carrerasfiltro:
                        data['carreras'] = Carrera.objects.filter(id__in=carrerasfiltro, activo=True,
                                                                  carrera=True).order_by('nombre')
                    else:
                        data['carreras'] = Carrera.objects.filter(activo=True, carrera=True).order_by('nombre')

                    data['tallaUniforme'] = TallaUniforme.objects.all().select_related().order_by('nombre')
                    data['h_vinculacion']=HORAS_VINCULACION
                    data['NEW_PASSWORD']=NEW_PASSWORD
                    data['ACTIVA_ADD_EDIT_AD']=ACTIVA_ADD_EDIT_AD
                    data['discapacitados'] = Matricula.objects.filter(inscripcion__tienediscapacidad=True,nivel__periodo=request.session['periodo']).count()
                    end_time = datetime.now().time()
                    print('hello')
                    print("DURACION PROCESO INSCRIPCIONES "+str(request.user)+' '+str(start_time)+" - "+str(end_time))
                    connection.queries.clear()  # Limpia consultas previas

                    try:
                        response = render(request, "inscripciones/inscripcionesbs.html", data)
                        return response
                    except Exception as e:
                        for query in connection.queries:
                            print(
                                f"{query['time']}s: {query['sql']}")  # Aquí ves todas las consultas hechas hasta que crashea
                        import traceback
                        traceback.print_exc()  # Verás qué parte del template falló
                        raise e  # O redirige, como tú quieras

            except HTTPError as e:
                print('The server could fulfil the request')
                print('Error code:' + str(e.code))
                return HttpResponse(json.dumps({"result":"error ","mensaje":'Error code:' + str(e.code)}),content_type="application/json")
            except URLError as e:
                print('We failed to reach a server ')
                return HttpResponse(json.dumps({"result":"error ","mensaje":'Error Reason:' + str(e.reason)}),content_type="application/json")
            except Exception as e:
                print('errorinscripcion '+str(e))
                return HttpResponseRedirect("/?info="+str(e))
    except Exception as e:
        print('ERROR EN MODULO INSCRIPCION '+str(e))
        return HttpResponseRedirect('/?info=1')

def mail_respuestasecretaria(contenido,asunto,email,carrera,materia,profesor,estudiante,user,opt):
    hoy = datetime.now().today()
    send_html_mail(str(asunto),"emails/email_notificacionalcance_secretaria.html", {'fecha': hoy,"user":user,'contenido': contenido, 'asunto': asunto,'docente':profesor,'materia':materia,'carrera':carrera,'estudiante':estudiante,'opt':opt},email.split(","))


def validaingresohorasdistribucion(idinscripcion,numhoras,idnivelmall):
    horas = numhoras
    nivel = idnivelmall
    inscrip = Inscripcion.objects.get(pk=idinscripcion)
    malla = Malla.objects.get(carrera=inscrip.carrera,vigente=True)

    #OCastillo 13-03-2023 cambio para tecnologias universitarias de Podologia y Gerontologia
    if not (malla.id ==72 or malla.id ==74) :
        asig = AsignaturaMalla.objects.get(Q(asignatura__nombre__icontains='LABORALES') | Q(asignatura__nombre__icontains='PREPRO'), malla=malla,nivelmalla__id=nivel)
    else:
        asig = AsignaturaMalla.objects.get(asignatura__nombre__icontains='TELECLINICA', malla=malla,nivelmalla__id=nivel)

    if InscripcionPracticas.objects.filter(inscripcion=inscrip,nivelmalla__id=nivel).exists():

        horastotalingresada = horas + InscripcionPracticas.objects.filter(inscripcion=inscrip,nivelmalla__id=nivel).aggregate(Sum('horas'))['horas__sum']
    else:
        horastotalingresada = horas

    if horastotalingresada > asig.horas:
        return False


    return True