from django.contrib import admin
from sga.models import Provincia, Canton, TipoAula, EjeFormativo, \
    Sesion, Sede, Carrera, Colegio, Sexo, Persona, Alumno, Especialidad, Asignatura, Periodo, AsignaturaMalla, Nivel, \
    Materia, Malla, Aula, Turno, Modulo, ModuloGrupo, Clase, Profesor, Modalidad, Inscripcion, RecordAcademico, \
    Matricula, MateriaAsignada, Leccion, EvaluacionIAVQ, TipoSolicitudSecretariaDocente, SolicitudSecretariaDocente, \
    DocumentosDeInscripcion, RetiradoMatricula, TipoSangre, TitulacionProfesor, LeccionGrupo, Licencia, TipoArchivo, \
    Archivo, NotaIAVQ, EvaluacionIAVQ2, TipoEstado, Graduado, CategoriaReporte, Reporte, ParametroReporte, Banco, \
    CuentaBanco, ClienteFactura, Factura, ProcesadorPagoTarjeta, PrecioMatricula, TipoActividadExtraCurricular, Rubro, \
    RubroMatricula, PrecioActividadExtraCurricular, ActividadExtraCurricular, ParticipanteActividadExtraCurricular, \
    RubroActividadExtraCurricular, TipoOtroRubro, PrecioTipoOtroRubro, RubroOtro, LugarRecaudacion, PagoCheque, \
    PagoTarjeta, FacturaCancelada, Pago, FotoPersona, Egresado, HistoriaNivelesDeInscripcion, PrecioMateria, \
    RubroMateria, TipoIncidencia, Incidencia, PeriodoEvaluacionesIAVQ, HistoricoRecordAcademico, SeguimientoGraduado, \
    CVPersona, EstratoSociocultural, PerfilInscripcion, InscripcionMalla, CoordinadorCarrera, AmbitoEvaluacion, \
    IndicadorEvaluacion, InstrumentoEvaluacion, AmbitoInstrumentoEvaluacion, IndicadorAmbitoInstrumentoEvaluacion, \
    ProcesoEvaluativo, EvaluacionProfesor, TipoBeca, DatoInstrumentoEvaluacion, EstudioInscripcion, EmpresaInscripcion, \
    DocumentoInscripcion, Grupo, InscripcionGrupo, TipoPeriodo, AsignaturaNivelacionCarrera, GrupoCoordinadorCarrera, \
    SesionCaja, CierreSesionCaja, PrecioCarreraGrupo, FormaDePago, TipoTarjetaBanco, TipoEspecieValorada, \
    RubroEspecieValorada, TituloPersona, ChequeProtestado, Feriado, \
    CategorizacionDocente, TipoBeneficio, CargoInstitucion, TituloInstitucion, ConvalidacionInscripcion, \
    PeriodoEvaluacionesITS, InscripcionFlags, NotaCredito, RubroNotaDebito, Coordinacion, InscripcionEstadistica, \
    RolPerfilProfesor, RolPago, RolPagoProfesor, RolPagoDetalleProfesor, CodigoEvaluacion, Parroquia, \
    PrestamoInstitucional, DonacionRubros, ReciboCajaInstitucion, Encuesta, NotaCreditoInstitucion, TipoMulta, \
    TipoLiquidacion, TipoObservacionInscripcion, ObservacionInscripcion, ObservacionGraduado, ListaFormaDePago, \
    Pais, TipoNivelTitulacion, CargoProfesor, EntidadFinancia, TipoEstudioCursa, ProfesorEstudiosCursa, \
    PersonaDatosMatriz, AreaConocimiento, SubAreaConocimiento, \
    ProfesorHorasActividades, AdministrativoEstudiosCursa, TitulacionAdministrativo, MateriaRecepcionActaNotas, \
    AusenciaJustificada, Nacionalidad, DepartamentoActividad, \
    VisitaBiblioteca, EstudianteXEgresar, ClaveBox, DetalleVisitasBox, ParametroEvaluacion, \
    NotaCreditoInstitucionAnulada, ServiciosBox, TipoNotaCredito, TipoMedicamento, PreInscripcion, DetalleNotacredDevol, \
    DetalleRegistroMedicamento, SuministroBox, RegistroMedicamento, Oficio, \
    TipoOficio, AnalisisEvaluacion, RubroAdicional, RecetaVisitaBox, DeberAlumno, DetalleInscGuarderia, \
    InscripcionGuarderia, Descuento, EstudianteTutoria, Tutoria, PagoTutoria, DetallePagoTutoria, AtencionCliente, \
    PuntoAtencion, Nee, SeguimientoNee, PersonaNee, InscripcionTipoTestDobe, \
    TipoTestDobe, PagoTransferenciaDeposito, Noticia, IngresoGuarderia, OpcionRespuesta, EstadoLlamada, \
    OpcionEstadoLlamada, RegistroSeguimiento, Referidos, LlamadaUsuario, \
    SolicituInfo, RubroMasivo, DetalleRubroMasivo, ProcesoDobleMatricula, ReciboCaja, ObservacionMatricula, \
    InscripcionSenescyt, ReciboPermisoCondu, TurnoCab, DetalleRubrosBeca, \
    ReporteExcel, GrupoReporteExcel, InscripcionExamen, DetalleExamen, ExamenPractica, ProfeExamenPractica, \
    ModalidadPonencia, ComisionCongreso, TipoDocumentosOficiales, \
    RegistroExterno, AprobacionVinculacion, PagoPymentez, EvaluacionITB, MotivoAlcance, CategoriaRubro, \
    LogAceptacionProfesorMateria, EvaluacionAlcance, \
    TipoMultaDocente, MultaDocenteMateria, DetalleEliminaMatricula, DocumentosVinculacionEstudiantes, NivelTutor, \
    DatosTransfereciaDeposito, InscripcionMotivoCambioPromocion, \
    RegistroLlamadas, ColorZapato, ColorUniforme, TallaZapato, TallaUniforme, EntregaUniforme, NotasComplexivo, \
    NotasComplexivoDet, LogQuitarAsignacionProfesor, PagoSustentacionesDocente, \
    ResponsableBodegaConsultorio, RegistroValorporDocente, ParametroSeguimiento, SeguimientoTutor, MatriculaTutor, \
    CabSeguimiento, DetSeguimiento, PeriodoExamen, ProvinciaPeriodoEx, CronogramaExamen, \
    CronogramaAlumno, NivelPeriodoEx, PagoPracticasDocente, CostoAsignatura, RegistroPlagioTarjetas, \
    CalificacionSolicitudes, TipoPersonaEmpresaConvenio, \
    ParentescoTipoPersonaEmpresaConvenio, DescuentosporConvenio, VacunasCovid, RegistroVacunas, CalificacionAutoestima, \
    OrganizacionAprendizaje, PersonAutorizaBecaAyuda, \
    DescuentoDOBE, InscripcionProfesionalizacion, TipoMotivoNotaCredito, RegistroAceptacionPagoenLinea, \
    RegistroAceptacionPagoenLineaConduccion, TipoConvenio, \
    RegistroAceptacionProtecciondeDatos, Webinar, ActividadesHorasExtra, SupervisorGrupos, EjesEvaluacion, \
    AreasElementosEvaluacion, PreguntasEvaluacion, RespuestasEvaluacion, \
    EvaluacionDocente, DetalleEvaluacionPregunta, EvaluacionMateria, EvaluacionAlumno, PeriodoEvaluacion, \
    CoordinadorCarreraPeriodo, EvaluacionDirectivoPeriodo, DetalleEvaluacionDocente, \
    EvaluacionAlcanceHistorial, Notificacion, EstudiantesXDesertarObservacion, \
    EstudiantesXDesertar, DescuentoReferido, InscripcionDescuentoRef, InscripcionBecario, CamposFormacion, \
    UnidadOrganizacion, CapituloSyllabus, SubTemaSyll, DetalleSubTemaSyll, HabilidadesTema, ValoresTema, HorasTema, \
    DetalleCapitulo, DetalleTema, TemaSyllabus, Syllabus, TipoVisitasBiblioteca, TipoPersona, NivelMalla, \
    ModeloImpresion, RelacionTrabajo, TiempoDedicacionDocente, GrupoCurso, MateriaCurso, InscripcionMateria, \
    DetallePagos, PagosCurso, InscripcionAspirantes, PagoWester, Raza, Discapacidad, MotivoBeca, ArchivoReporteCarrera, \
    Impresion, ProcesoDobe, MensajesEnviado, PersonaExamenExt, ExamenExterno, PersonaExterna, Sector, VideoLogin, \
    ComponenteExamen, PreguntaExterno, AulaAdministra, TipAulaExamen, TipoPersonaCongreso, RequerimientoCongreso, \
    DatosPersonaCongresoIns, PagoExternoPedagogia, CarreraConvenio, ModalidadCarreraConvenio, Clasificacion, \
    ConvenioClasificacion, CalculoTest, CalculoRasgoEstado, RespuestaTest, RolPagoProfesorDescuento, Donacion, \
    EvaluacionCoordinadorDocente, EvaluacionDocentePeriodo, PagoCalendario, ProfesorInstitucionGP, \
    TablaTarifaIRPersonaNatural, DetalleTablaTarifaIRPersonaNatural, Multa, TipoRetencion, TipoActividad, Actividad, \
    Vehiculo, SesionPractica, TurnoPractica, DetalleVisitasBiblioteca, VisitaBox, TipoVisitasBox, ValeCaja, \
    TipoConsulta, GrupoPractica, TipoTest, InstruccionTest, ParametroTest, EjercicioTest, TipoIngreso, PuntoBaremo, \
    PreguntaTest, ProgresoTutoria, TipoSegmento, TipoSuspension, MotivoSuspension, TrasladoMedicamento, Resolucion, \
    InscripcionSuspension, GrupoSeminario, InscripcionSeminario, ActividadVinculacion, DocenteVinculacion, \
    EvidenciaVinculacion, ObservacionVinculacion, KitCongreso, CalificacionEvaluacion, Convenio, \
    BeneficiariosVinculacion, TipoDocumenBeca, Absentismo, TipoPrograma, Programa, ClaveEvaluacionNota, TipoAtencionBox, \
    TipoAnuncio, AsistAsuntoEstudiant, IncidenciaAsignada, IncidenciaAdministrativo, ObservacionIncidencia, \
    DepartamentoIncidenciaAsig, GrupoCorreo, TipoConsultaAsunto, InscripcionPanel, PermisoPanel, Panel, TipoRespuesta, \
    TituloExamenCondu, PreguntaExamen, EliminaSuspension, InscripcionPracticas, ReferidosInscripcion, \
    TipoNoRegistroAspirante, TipoRegistroAspirante, CodigoFormaPago, RubrosConduccion, PromedioNotasGrado, \
    SolicitudOnline, SolicitudCarrera, MateriaNivel, IpRecaudacion, IpRecaudLugar, PrecioConsulta, AsistenciaCofia, \
    RespuestaExamen, UsuarioConvenio, ConvenioAcademico, ConvenioUsuario, ConvenioBox, RegistroVehiculo, \
    PersonaConduccion, CategoriaVehiculo, TipoCombustible, Promocion, Departamento, DepartamentoGroup, \
    RequerimientoDepart, DetalleRequerimiento, CertificadoEntregado, TipoCulminacionEstudio, ProfesorMateria, \
    AlternativasBoxExt, PagoNivel, LibroRevista, ArchivoTestConduccion, ArchivoWester, SolicitudEstudiante, \
    RegistroWester, IndicEvaluacionExamen, GrupoPonencia, InscripcionGrupoPonencia, Vendedor, EspecieGrupo, \
    InscripcionVendedor, EstudianteVinculacion, CalculoLocus, InscripcionTipoTest, ResultadoRespuesta, SolicitudesGrupo, \
    AsistenteDepartamento, PagosCursoITB, CoordinacionDepartamento, Jornada, SesionJornada, SolicitudBeca, \
    DetActivaExamenParc, ExamenParRespuesta, ExamenParcial, TituloExamenParcial, PreguntaAsigRespuesta, \
    PreguntaAsignatura, PagoConduccion, ArchivoSoliciBeca, EmpresaConvenio, TipoPonencia, AsistenteSoporte, \
    CalificacionSoporte, HorarioAsistente, TipoProblema, ArchivoPichincha, RecaudacionPichincha, RequerimientoSoporte, \
    RequerimSolucion, RespProgramdor, TipoSeguimiento, TutorCongreso, TutorMatricula, TutorCongSeguimiento, \
    Resolucionbeca, TablaDescuentoBeca, HistoricoNotasITB, CuponInscripcion, RequerimientoAsistentes, \
    HorarioAsistenteSolicitudes, ExamenConvalidacionIngreso, DocumentosOficialesVinculacion, PagoReciboCajaInstitucion, \
    EntregaJugueteCanasta, RubroLog, HorarioPersona, HistoriaArchivoPymentez, ParametroDescuento, ParametrosPromocion, \
    EmpresaSinConvenio, SolicitudPracticas, EvaluacionSupervisorEmp, EvaluacionAcademico, SegmentoIndicadorEmp, \
    SegmentoDetalle, IndicadorAcademico, PuntajeIndicador, EscenarioPractica, SupervisorPracticas, \
    TipoSupervisionPracticas, SupervisionPracticas, SupervisionPracticasDet, CoordinadorPracticas, ReportePracticas, \
    NombreReportePract, EstadoEmpresa, PermisosSga, RespuestasEjesEvaluacion, EvidenciaSolicitudAntencion, \
    SolicitudAntencion, NotificacionPersona, ClasesOnline, EvaluacionCargoPeriodo, EntregaUniformeAdmisiones, \
    TipoArticulo, EstrategiasPedagogicas, InstrumentosTutoriaPedagogicas, Genero, NucleoFamiliar, ZonaResidencia, \
    Afiliacion, MaterialCasa, TipoServicio, CondicionesHogar, TipoIngresoHogar, TipoIngresoPropio, TipoEmpleo, \
    UsoTransporte, TipoTransporte, Deporte, ManifestacionArtistica, DeseosFuturos, TutoriaPedagogica, EncuestaItb, \
    InscripcionTestIngreso, AreaDominioAcademico, DominiosAcademicos, \
    AlternativaEvaluacion, DetalleModeloEvaluativo, ModeloEvaluativo, TipoRecurso, Estado, \
    EstadoModel, EvaluacionComponente

from ext.models import MateriaExterna
from django.contrib.admin.models import LogEntry, DELETION
from django.utils.html import escape
from django.urls import reverse
from socioecon.models import InscripcionFichaSocioEconomicaBeca, ReferenciaPersonal, ReferenciaBeca, BonoFmlaEstudiante, OcupacionEstudiante, IngresosEstudiante


admin.site.register(EstudiantesXDesertarObservacion)
admin.site.register(EstudiantesXDesertar)
admin.site.register(DescuentoReferido)
admin.site.register(InscripcionDescuentoRef)
admin.site.register(InscripcionBecario)
admin.site.register(CamposFormacion)
admin.site.register(UnidadOrganizacion)
admin.site.register(CapituloSyllabus)
admin.site.register(SubTemaSyll)
admin.site.register(DetalleSubTemaSyll)
admin.site.register(HabilidadesTema)
admin.site.register(ValoresTema)
admin.site.register(HorasTema)
admin.site.register(DetalleCapitulo)
admin.site.register(DetalleTema)
admin.site.register(TemaSyllabus)
admin.site.register(Syllabus)
admin.site.register(Provincia)
admin.site.register(SolicituInfo)
admin.site.register(IngresoGuarderia)
admin.site.register(EstudianteTutoria)
admin.site.register(Noticia)
admin.site.register(Tutoria)
admin.site.register(Nee)
admin.site.register(InscripcionTipoTestDobe)
admin.site.register(TipoTestDobe)
admin.site.register(SeguimientoNee)
admin.site.register(EstadoLlamada)
admin.site.register(LlamadaUsuario)
admin.site.register(OpcionEstadoLlamada)
admin.site.register(RegistroSeguimiento)
admin.site.register(Referidos)
admin.site.register(PersonaNee)
admin.site.register(AtencionCliente)
admin.site.register(PagoTransferenciaDeposito)
admin.site.register(PuntoAtencion)
admin.site.register(DetalleRegistroMedicamento)
admin.site.register(PagoTutoria)
admin.site.register(DetallePagoTutoria)
admin.site.register(Canton)
admin.site.register(Descuento)

admin.site.register(InscripcionGuarderia)
admin.site.register(DetalleInscGuarderia)
admin.site.register(OpcionRespuesta)
admin.site.register(DeberAlumno)
admin.site.register(Parroquia)
admin.site.register(AnalisisEvaluacion)
admin.site.register(Oficio)
admin.site.register(TipoOficio)
admin.site.register(RubroAdicional)
admin.site.register(Pais)
admin.site.register(Sexo)
admin.site.register(CoordinadorCarreraPeriodo)
# admin.site.register(Colegio)

admin.site.register(Sede)
admin.site.register(Nacionalidad)
admin.site.register(TipoVisitasBiblioteca)
admin.site.register(SuministroBox)
admin.site.register(TipoPersona)
# admin.site.register(DetalleEvaluacionDocente)

class NivelMallaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'nombrematriz')
    ordering = ('nombre',)
    search_fields = ('nombre',)

admin.site.register(NivelMalla,NivelMallaAdmin)

admin.site.register(EjeFormativo)
admin.site.register(TipoAula)
admin.site.register(ModeloImpresion)
admin.site.register(TipoLiquidacion)
admin.site.register(TipoObservacionInscripcion)
admin.site.register(RelacionTrabajo)
admin.site.register(TipoNotaCredito)
admin.site.register(TiempoDedicacionDocente)
admin.site.register(GrupoCurso)
admin.site.register(MateriaCurso)
admin.site.register(InscripcionMateria)
admin.site.register(PagosCurso)
admin.site.register(DetallePagos )
admin.site.register(DetalleNotacredDevol)
admin.site.register(ObservacionMatricula)
admin.site.register(InscripcionAspirantes)
admin.site.register(PagoWester)
# admin.site.register(MateriaRecepcionActaNotas)



class EspecialidadAdmin(admin.ModelAdmin):
    list_display = ('nombre', )
    ordering = ('nombre',)
    search_fields = ('nombre',)

class CategorizacionDocenteAdmin(admin.ModelAdmin):
    list_display = ('nombre', )
    ordering = ('nombre',)
    search_fields = ('nombre',)

class CoordinacionAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    ordering = ('nombre',)
    search_fields = ('nombre',)

admin.site.register(Especialidad, EspecialidadAdmin)
admin.site.register(Coordinacion, CoordinacionAdmin)
admin.site.register(CategorizacionDocente, CategorizacionDocenteAdmin)

admin.site.register(TipoPeriodo)

admin.site.register(Modalidad)
admin.site.register(TipoSangre)
admin.site.register(CategoriaReporte)

admin.site.register(FotoPersona)
admin.site.register(CVPersona)


class RazaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'nombrematriz')
    ordering = ('nombre',)
    search_fields = ('nombre',)

admin.site.register(Raza,RazaAdmin)

admin.site.register(EstratoSociocultural)

class DiscapacidadAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'nombrematriz')
    ordering = ('nombre',)
    search_fields = ('nombre',)

admin.site.register(Discapacidad,DiscapacidadAdmin)

admin.site.register(PrecioMateria)
admin.site.register(RubroMateria)

class MotivoBecaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'nombrematriz')
    ordering = ('nombre',)
    search_fields = ('nombre',)

admin.site.register(MotivoBeca,MotivoBecaAdmin)

admin.site.register(TipoBeca)
admin.site.register(TipoBeneficio)

admin.site.register(DocumentoInscripcion)


class ArchivoReporteCarreraAdmin(admin.ModelAdmin):
    list_display = ('fecharegistro', 'archivo_matriz','archivo_pendientes','carrera','nombhoja','fila')
    ordering = ('fecharegistro',)
    search_fields = ('carrera',)
    list_filter = ('fecharegistro','carrera')
admin.site.register(ArchivoReporteCarrera,ArchivoReporteCarreraAdmin)


class InscripcionGrupoAdmin(admin.ModelAdmin):
    list_display = ('inscripcion', 'grupo','activo')
    ordering = ('inscripcion',)
    search_fields = ('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres','inscripcion__persona__cedula')
    list_filter = ('inscripcion',)

admin.site.register(InscripcionGrupo, InscripcionGrupoAdmin)
# DetalleEvaluacionDocente
class DetalleEvaluacionDocenteAdmin(admin.ModelAdmin):
    list_display = ('evaluacion','pregunta',)
    ordering = ('evaluacion',)
    search_fields = ('evaluacion__profesor__persona__apellido1','evaluacion__profesor__persona__apellido2','evaluacion__profesor__persona__nombres','evaluacion__profesor__persona__cedula')
    list_filter = ('evaluacion',)

admin.site.register(DetalleEvaluacionDocente, DetalleEvaluacionDocenteAdmin)
class AusenciaJustificadaAdmin(admin.ModelAdmin):
    list_display = ('asist', 'numeroe','codigoe','fechae','profesor','inscripcion','observaciones','usuario','fecha')
    ordering = ('fecha','numeroe')
    search_fields = ('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres','inscripcion__persona__cedula')
    list_filter = ('usuario',)

admin.site.register(AusenciaJustificada, AusenciaJustificadaAdmin)

class InscripcionFlagsAdmin(admin.ModelAdmin):
    list_display = ('inscripcion', 'tienechequeprotestado','tienedeudaexterna')
    ordering = ('inscripcion',)
    search_fields = ('inscripcion__persona__cedula','inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')
    list_filter = ('tienechequeprotestado','tienedeudaexterna')

class InscripcionEstadisticaAdmin(admin.ModelAdmin):
    list_display = ('inscripcion', 'deuda','credito')
    ordering = ('inscripcion',)
    search_fields = ('inscripcion__persona__cedula','inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')

class NotaCreditoAdmin(admin.ModelAdmin):
    list_display = ('inscripcion', 'motivo','fecha','valorinicial','saldo')
    ordering = ('inscripcion',)
    search_fields = ('inscripcion',)

class NotaCreditoInstitucionAnuladaAdmin(admin.ModelAdmin):
    list_display = ('notacredito','motivo', 'fecha','usuario')
    ordering = ('notacredito__numero',)
    search_fields = ('notacredito__numero', )

admin.site.register(NotaCreditoInstitucionAnulada, NotaCreditoInstitucionAnuladaAdmin)

class NotaCreditoInstitucionAdmin(admin.ModelAdmin):
    list_display = ('numero','inscripcion', 'motivo','fecha','valor','factura','estado','mensaje','claveacceso')
    ordering = ('fecha','numero')
    search_fields = ('inscripcion__persona__apellido1', 'inscripcion__persona__apellido2','inscripcion__persona__nombres', 'numero')

class ReciboCajaInstitucionAdmin(admin.ModelAdmin):
    list_display = ('inscripcion', 'motivo','fecha','hora', 'valorinicial','saldo')
    ordering = ('fecha', 'inscripcion' )
    search_fields = ('inscripcion', )


class PrecioCarreraGrupoAdmin(admin.TabularInline):
    model = PrecioCarreraGrupo

class CargoInstitucionAdmin(admin.ModelAdmin):
    list_display = ('persona', 'cargo')
    ordering = ('persona','cargo')
    search_fields = ('persona','cargo')

class CarreraAdmin(admin.ModelAdmin):
    list_display = ('nombre','alias')
    ordering = ('alias','nombre')
    search_fields = ('alias','nombre')

class ImpresionAdmin(admin.ModelAdmin):
    list_display = ('usuario','impresa')
    ordering = ('usuario',)
    search_fields = ('usuario',)


class TituloInstitucionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'alias', 'direccion','telefono','correo','web', 'municipio')
    ordering = ('nombre',)
    search_fields = ('nombre','correo')

class ConvalidacionInscripcionAdmin(admin.ModelAdmin):
    list_display = ('record', 'centro','carrera','asignatura','anno','nota_ant', 'nota_act','observaciones')
    ordering = ('asignatura',)
    search_fields = ('asignatura',)

class ProfesorEstudiosCursaAdmin(admin.ModelAdmin):
    list_display = ('profesor', 'inicio','tipoestudio','financiado')
    ordering = ('inicio',)
    search_fields = ('tipoestudio',)

class AdministrativoEstudiosCursaAdmin(admin.ModelAdmin):
    list_display = ('administrativo', 'inicio','tipoestudio','financiado')
    ordering = ('inicio',)
    search_fields = ('tipoestudio',)

admin.site.register(ProfesorEstudiosCursa, ProfesorEstudiosCursaAdmin)
admin.site.register(AdministrativoEstudiosCursa, AdministrativoEstudiosCursaAdmin)

admin.site.register(Carrera, CarreraAdmin)
admin.site.register(Impresion, ImpresionAdmin)
admin.site.register(CargoInstitucion, CargoInstitucionAdmin)
admin.site.register(InscripcionFlags, InscripcionFlagsAdmin)
admin.site.register(InscripcionEstadistica, InscripcionEstadisticaAdmin)
admin.site.register(NotaCredito, NotaCreditoAdmin)
admin.site.register(NotaCreditoInstitucion, NotaCreditoInstitucionAdmin)
admin.site.register(ReciboCajaInstitucion, ReciboCajaInstitucionAdmin)
admin.site.register(TituloInstitucion, TituloInstitucionAdmin)
admin.site.register(ConvalidacionInscripcion, ConvalidacionInscripcionAdmin)
admin.site.register(EvaluacionDirectivoPeriodo)




class GrupoAdmin(admin.ModelAdmin):
    inlines = [ PrecioCarreraGrupoAdmin ]
    list_display = ('nombre', 'tiene_cupo', 'carrera', 'sesion', 'modalidad', 'sede', 'capacidad', 'inicio', 'fin', 'observaciones','abierto','cerrado')
    ordering = ('inicio',)
    search_fields = ('nombre','observaciones','capacidad','abierto')
    list_filter = ('carrera','sesion','modalidad','sede','cerrado')

class SesionCajaAdmin(admin.ModelAdmin):
    list_display = ('caja', 'fecha', 'hora', 'fondo', 'facturaempieza', 'facturatermina', 'fondo', 'abierta')
    ordering = ('fecha','hora')
    search_fields = ('caja','facturaempieza','facturatermina')
    list_filter = ('abierta',)

class PadreClaveAdmin(admin.ModelAdmin):
    list_display = ('inscripcion', 'nombre', 'cedula', 'email', 'fecha','clave')
    ordering = ('inscripcion','fecha')
    search_fields = ('nombre','observaciones','capacidad','abierto')
    list_filter = ('carrera','sesion','modalidad','sede')

admin.site.register(SesionCaja, SesionCajaAdmin)
admin.site.register(Grupo, GrupoAdmin)
admin.site.register(FormaDePago)
admin.site.register(ListaFormaDePago)
admin.site.register(TipoTarjetaBanco)

class GrupoCoordinadorCarreraAdmin(admin.ModelAdmin):
    list_display = ('group', 'carrera')
    ordering = ('carrera__nombre',)
    search_fields = ('group__name','carrera__nombre')
    list_filter = ('group','carrera')


class FeriadoAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'motivo')
    ordering = ('fecha',)
    search_fields = ('fecha','motivo')

admin.site.register(Feriado, FeriadoAdmin)
admin.site.register(GrupoCoordinadorCarrera, GrupoCoordinadorCarreraAdmin)


class ParametroReporteAdmin(admin.TabularInline):
    model = ParametroReporte

class PagoAdmin(admin.TabularInline):
    model = Pago

class ReporteAdmin(admin.ModelAdmin):
    inlines = [ ParametroReporteAdmin ]
    list_display = ('nombre','descripcion','archivo', 'categoria')
    ordering = ('nombre',)
    search_fields = ('nombre','descripcion')
    list_filter = ('categoria','grupos')

admin.site.register(Reporte, ReporteAdmin)


class TipoIncidenciaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'correo', 'responsable')
    ordering = ('nombre',)
    search_fields = ('nombre','correo', 'responsable')

class IncidenciaAdmin(admin.ModelAdmin):
    list_display = ('lecciongrupo', 'tipo','contenido', 'cerrada')
    ordering = ('lecciongrupo','cerrada')
    list_filter = ('tipo','cerrada')


admin.site.register(TipoIncidencia, TipoIncidenciaAdmin)
admin.site.register(Incidencia, IncidenciaAdmin)

class PeriodoEvaluacionesIAVQAdmin(admin.ModelAdmin):
    list_display = ('periodo', 'n1desde', 'n1hasta', 'n2desde', 'n2hasta', 'pidesde', 'pihasta','sudesde', 'suhasta')
    ordering = ('periodo',)
    search_fields = ('periodo',)

class PeriodoEvaluacionesITSAdmin(admin.ModelAdmin):
    list_display = ('periodo', 'mom1desde', 'mom1hasta', 'mom2desde', 'mom2hasta', 'pfinaldesde', 'pfinalhasta','proydesde', 'proyhasta','sudesde', 'suhasta')
    ordering = ('periodo',)
    search_fields = ('periodo',)



admin.site.register(TituloPersona)
admin.site.register(PeriodoEvaluacionesIAVQ, PeriodoEvaluacionesIAVQAdmin)
admin.site.register(PeriodoEvaluacionesITS, PeriodoEvaluacionesITSAdmin)

class TipoEspecieValoradaAdmin(admin.ModelAdmin):
    list_display = ('nombre','precio','reporte','destinatario','cargo', 'activa','certificado')
    ordering = ('nombre',)
    search_fields = ('nombre',)

class RubroEspecieValoradaAdmin(admin.ModelAdmin):
    list_display = ('rubro', 'tipoespecie',)
    search_fields = ('rubro__inscripcion__persona__nombres','materia__materia__asignatura__nombre',)
    ordering = ('rubro__fecha',)

admin.site.register(RubroEspecieValorada, RubroEspecieValoradaAdmin)
admin.site.register(TipoEspecieValorada, TipoEspecieValoradaAdmin)


class PerfilInscripcionAdmin(admin.ModelAdmin):
    list_display = ('inscripcion','raza','estrato','tienediscapacidad','tipodiscapacidad')
    ordering = ('inscripcion__persona__apellido1',)
    search_fields = ('inscripcion__persona__apellido1','inscripcion__persona__apellido2')

admin.site.register(PerfilInscripcion, PerfilInscripcionAdmin)

class PersonaAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'cedula', 'sexo', 'email', 'telefono', 'provincia', 'usuario')
    ordering = ('nombres',)
    search_fields = ('nombres','apellido1','apellido2','cedula')
    list_filter = ('provincia', 'sexo')

class AlumnoAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'colegio', 'especialidad')
    ordering = ('persona',)
    search_fields = ('nombre_completo',)
    list_filter = ('colegio', 'especialidad')

class AsignaturaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'cantidad_dependencias', 'codigo', 'creditos', 'horas')
    ordering = ('nombre',)
    search_fields = ('nombre','codigo')

class CodigoEvaluacionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'alias')
    ordering = ('nombre','alias')
    search_fields = ('nombre','alias')

class PeriodoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'inicio', 'fin', 'activo', 'tipo')
    ordering = ('activo','fin')
    search_fields = ('nombre',)
    list_filter = ('activo',)
    date_hierarchy = 'inicio'


class AsignaturaMallaAdmin(admin.ModelAdmin):
    list_display = ('malla', 'asignatura', 'nivelmalla', 'ejeformativo','horas','creditos')
    ordering = ('malla',)
    search_fields = ('malla','asignatura',)
    list_filter = ('nivelmalla','ejeformativo','malla','asignatura')

class AsignaturaNivelacionCarreraAdmin(admin.ModelAdmin):
    list_display = ('carrera', 'asignatura')
    ordering = ('carrera',)
    search_fields = ('carrera','asignatura',)
    list_filter = ('carrera', 'asignatura')

admin.site.register(AsignaturaNivelacionCarrera, AsignaturaNivelacionCarreraAdmin)
admin.site.register(CodigoEvaluacion, CodigoEvaluacionAdmin)

class NivelAdmin(admin.ModelAdmin):
    list_display = ('carrera', 'periodo', 'sede', 'sesion','nivelmalla','malla','paralelo')
    ordering = ('carrera',)
    search_fields = ('carrera__nombre','periodo__nombre','sede__nombre','sesion__nombre','nivelmalla__nombre','malla__carrera__nombre','paralelo')
    list_filter = ('periodo','sede','sesion','nivelmalla','malla')

class SesionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'comienza', 'termina', 'cantidad_turnos', 'repr_dias')
    ordering = ('nombre',)
    search_fields = ('nombre',)

admin.site.register(Sesion, SesionAdmin)

class MateriaAdmin(admin.ModelAdmin):
    list_display = ('asignatura', 'nivel', 'horas', 'creditos','identificacion')
    ordering = ('nivel','asignatura')
    search_fields = ('identificacion',)
    list_filter = ('identificacion',)

class MallaAdmin(admin.ModelAdmin):
    list_display = ('carrera', 'inicio', 'vigente')
    ordering = ('inicio',)
    search_fields = ('carrera',)
    list_filter = ('vigente',)
    date_hierarchy = 'inicio'

class InscripcionMallaAdmin(admin.ModelAdmin):
    list_display = ('inscripcion', 'malla', )
    ordering = ('inscripcion',)

admin.site.register(InscripcionMalla, InscripcionMallaAdmin)


class AulaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'capacidad', 'tipo', 'sede', 'activa', 'ip')
    ordering = ('nombre','tipo')
    search_fields = ('nombre','ip')
    list_filter = ('tipo','sede',)

class TurnoAdmin(admin.ModelAdmin):
    list_display = ('sesion', 'turno', 'comienza', 'termina','horas')
    ordering = ('sesion','turno')
    search_fields = ('sesion','turno')
    list_filter = ('sesion','turno')

class ModuloAdmin(admin.ModelAdmin):
    list_display = ('url', 'nombre', 'icono', 'descripcion','activo', 'orden')
    ordering = ('orden','url')
    search_fields = ('url','nombre','descripcion')
    list_filter = ('activo',)

class ModuloGrupoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'prioridad', 'descripcion')
    ordering = ('prioridad','nombre')
    search_fields = ('nombre','descripcion')

class ClaseAdmin(admin.ModelAdmin):
    list_display = ('materia', 'profesor', 'turno', 'aula', 'dia')
    ordering = ('materia','dia','aula')
    search_fields = ('materia','profesor','aula')
    list_filter = ('aula','dia','turno')



class ProfesorAdmin(admin.ModelAdmin):
    list_display = ('persona', 'activo', 'fechaingreso')
    ordering = ('persona',)
    search_fields = ('persona__nombres','persona__apellido1', 'persona__apellido2')
    list_filter = ('activo',)
    date_hierarchy = 'fechaingreso'

class InscripcionAdmin(admin.ModelAdmin):
    list_display = ('persona', 'fecha', 'carrera', 'modalidad', 'sesion', 'colegio', 'especialidad')
    ordering = ('persona',)
    search_fields = ('persona__nombres','persona__apellido1', 'persona__apellido2', 'carrera__nombre')
    list_filter = ('modalidad','carrera','especialidad')
    date_hierarchy = 'fecha'

class RecordAcademicoAdmin(admin.ModelAdmin):
    list_display = ('inscripcion', 'asignatura','nota','asistencia','fecha', 'convalidacion', 'estado')
    ordering = ('inscripcion__persona__nombres',)
    search_fields = ('inscripcion__persona__nombres','asignatura__nombre',)
    list_filter = ('asignatura','convalidacion')
    date_hierarchy = 'fecha'


class HistoricoRecordAcademicoAdmin(admin.ModelAdmin):
    list_display = ('inscripcion', 'asignatura','nota','asistencia','fecha', 'convalidacion', 'estado','pendiente')
    ordering = ('inscripcion__persona__nombres',)
    search_fields = ('inscripcion__persona__nombres','asignatura__nombre',)
    list_filter = ('asignatura','convalidacion')
    date_hierarchy = 'fecha'

class ProcesoDobeAdmin(admin.ModelAdmin):
    list_display = ('inscripcion','observacion','aprobado','usuario','fecha')
    ordering = ('inscripcion','fecha')
    search_fields = ('inscripcion__persona__nombres','inscripcion__persona__apellido1', 'inscripcion__persona__apellido2')
    list_filter = ('aprobado','fecha')

class MatriculaAdmin(admin.ModelAdmin):
    list_display = ('inscripcion','nivel','pago','becado','porcientobeca','motivobeca','tipobeca','tipobeneficio')
    ordering = ('inscripcion',)
    search_fields = ('inscripcion__persona__nombres','inscripcion__persona__apellido1', 'inscripcion__persona__apellido2')
    list_filter = ('nivel','pago')

class MateriaAsignadaAdmin(admin.ModelAdmin):
    list_display = ('matricula','materia','notafinal','asistenciafinal', 'supletorio')
    ordering = ('matricula','materia','notafinal')
    search_fields = ('matricula','materia')

class LeccionAdmin(admin.ModelAdmin):
    list_display = ('clase','fecha','horaentrada','horasalida','abierta')
    ordering = ('-fecha',)
    search_fields = ('clase','contenido','observaciones')
    list_filter = ('abierta',)
    date_hierarchy = 'fecha'

class LeccionGrupoAdmin(admin.ModelAdmin):
    list_display = ('materia','profesor','fecha','horaentrada','horasalida','abierta')
    ordering = ('-fecha',)
    search_fields = ('materia','profesor','contenido','observaciones')
    list_filter = ('abierta','profesor')
    date_hierarchy = 'fecha'

class EvaluacionIAVQAdmin(admin.ModelAdmin):
    list_display = ('materiaasignada','n1','n2','pi','n3','supletorio')
    ordering = ('-materiaasignada',)
    search_fields = ('materiaasignada',)

class SolicitudSecretariaDocenteAdmin(admin.ModelAdmin):
    list_display = ('persona','fecha','hora','tipo','cerrada','fechacierre')
    ordering = ('-fecha',)
    search_fields = ('persona','descripcion')
    list_filter = ('cerrada','tipo')
    date_hierarchy = 'fecha'

class DocumentosDeInscripcionAdmin(admin.ModelAdmin):
    list_display = ('inscripcion','titulo','acta','cedula','fotos','partida_nac','actaconv','votacion')
    ordering = ('inscripcion__persona__apellido1',)
    search_fields = ('inscripcion',)
    list_filter = ('titulo','acta','cedula','fotos')

class GraduadoAdmin(admin.ModelAdmin):
    list_display = ('inscripcion','notatesis','notafinal','fechagraduado','tematesis','registro')
    ordering = ('inscripcion__persona__apellido1', 'notatesis')
    search_fields = ('inscripcion',)

class SeguimientoGraduadoAdmin(admin.ModelAdmin):
    list_display = ('graduado','empresa','cargo','ocupacion','telefono','email','sueldo','ejerce')
    ordering = ('graduado__inscripcion__persona__apellido1', 'empresa')
    search_fields = ('graduado__inscripcion',)

class EgresadoAdmin(admin.ModelAdmin):
    list_display = ('inscripcion','fechaegreso','notaegreso')
    ordering = ('inscripcion__persona__apellido1','fechaegreso','notaegreso')
    search_fields = ('inscripcion',)

class RetiradoMatriculaAdmin(admin.ModelAdmin):
    list_display = ('inscripcion','nivel')
    ordering = ('inscripcion',)
    search_fields = ('inscripcion__persona__nombres','inscripcion__persona__apellido1', 'inscripcion__persona__apellido2')
    # date_hierarchy = 'fecha'

class TitulacionProfesorAdmin(admin.ModelAdmin):
    list_display = ('profesor','titulo','pais','nivel','tiponivel','institucion','fecha','registro', 'subarea')
    ordering = ('profesor__persona__apellido1', )
    search_fields = ('profesor__persona__apellido1','profesor__persona__apellido2','profesor__persona__nombres','titulo','institucion')
    list_filter = ('nivel','subarea')
    date_hierarchy = 'fecha'

class TitulacionAdministrativoAdmin(admin.ModelAdmin):
    list_display = ('administrativo','titulo','pais','nivel','tiponivel','institucion','fecha','registro', 'subarea')
    ordering = ('administrativo__apellido1', )
    search_fields = ('administrativo__apellido1','administrativo__apellido2','administrativo__nombres','titulo','institucion')
    list_filter = ('nivel','subarea')
    date_hierarchy = 'fecha'

class ProfesorHorasActividadesAdmin(admin.ModelAdmin):
    list_display = ('profesor','horasded','horasadm','horasinv','horasvin','horasotr','otrasactividades')
    ordering = ('profesor__persona__apellido1', )
    search_fields = ('profesor__persona__apellido1','profesor__persona__apellido2','profesor__persona__nombres','titulo','institucion')

admin.site.register(ProfesorHorasActividades, ProfesorHorasActividadesAdmin)
admin.site.register(TitulacionAdministrativo, TitulacionAdministrativoAdmin)

class LicenciaAdmin(admin.ModelAdmin):
    list_display = ('nombre','ruc','email','telefono','direccion','expira','idautorizacion')
    ordering = ('expira',)
    search_fields = ('nombre','ruc','email')
    date_hierarchy = 'expira'

class ArchivoAdmin(admin.ModelAdmin):
    list_display = ('nombre','materia','lecciongrupo','fecha','archivo','tipo')
    ordering = ('nombre',)
    search_fields = ('nombre','materia','archivo')
    list_filter = ('tipo',)
    date_hierarchy = 'fecha'

class NotaIAVQAdmin(admin.ModelAdmin):
    list_display = ('p1','p2','p3','p4','p5','nota')
    ordering = ('nota',)
    search_fields = ('nota',)
    list_filter = ('nota',)


class EvaluacionIAVQ2Admin(admin.ModelAdmin):
    list_display = ('materiaasignada','n1', 'n2', 'n3', 'pi', 'su', 'estado')
    ordering = ('-materiaasignada',)
    search_fields = ('materiaasignada__matricula__inscripcion__persona__apellido1','materiaasignada__matricula__inscripcion__persona__apellido2','materiaasignada__matricula__inscripcion__persona__nombres')


class SubAreaConocimientoAdmin(admin.ModelAdmin):
    list_display = ('codigo','nombre','descripcion','area')
    ordering = ('codigo',)
    search_fields = ('nombre','descripcion')
    list_filter = ('area',)

admin.site.register(HistoriaNivelesDeInscripcion)
admin.site.register(AreaConocimiento)
admin.site.register(SubAreaConocimiento, SubAreaConocimientoAdmin)
admin.site.register(TipoArchivo)
admin.site.register(Archivo,ArchivoAdmin)

admin.site.register(Graduado, GraduadoAdmin)
admin.site.register(Egresado, EgresadoAdmin)
admin.site.register(SeguimientoGraduado, SeguimientoGraduadoAdmin)

admin.site.register(NotaIAVQ,NotaIAVQAdmin)
admin.site.register(EvaluacionIAVQ2, EvaluacionIAVQ2Admin)

admin.site.register(TipoEstado)
admin.site.register(TipoNivelTitulacion)
admin.site.register(CargoProfesor)
admin.site.register(TipoEstudioCursa)
admin.site.register(EntidadFinancia)

admin.site.register(Licencia, LicenciaAdmin)
admin.site.register(TitulacionProfesor, TitulacionProfesorAdmin)
admin.site.register(RetiradoMatricula, RetiradoMatriculaAdmin)
admin.site.register(DocumentosDeInscripcion, DocumentosDeInscripcionAdmin)
admin.site.register(SolicitudSecretariaDocente, SolicitudSecretariaDocenteAdmin)
admin.site.register(TipoSolicitudSecretariaDocente)
admin.site.register(EvaluacionIAVQ, EvaluacionIAVQAdmin)
admin.site.register(Leccion, LeccionAdmin)
admin.site.register(LeccionGrupo, LeccionGrupoAdmin)
admin.site.register(MateriaAsignada, MateriaAsignadaAdmin)
admin.site.register(Matricula, MatriculaAdmin)
admin.site.register(Inscripcion, InscripcionAdmin)
admin.site.register(RecordAcademico, RecordAcademicoAdmin)
admin.site.register(HistoricoRecordAcademico, HistoricoRecordAcademicoAdmin)
admin.site.register(Persona, PersonaAdmin)
admin.site.register(Alumno, AlumnoAdmin)
admin.site.register(Asignatura, AsignaturaAdmin)
admin.site.register(Periodo, PeriodoAdmin)
admin.site.register(AsignaturaMalla, AsignaturaMallaAdmin)
admin.site.register(Nivel, NivelAdmin)
admin.site.register(Materia, MateriaAdmin)
admin.site.register(Malla, MallaAdmin)
admin.site.register(Aula, AulaAdmin)
admin.site.register(Turno, TurnoAdmin)
admin.site.register(Modulo, ModuloAdmin)
admin.site.register(ModuloGrupo, ModuloGrupoAdmin)
admin.site.register(ProcesoDobe, ProcesoDobeAdmin)
admin.site.register(Clase, ClaseAdmin)
admin.site.register(Profesor, ProfesorAdmin)


#----------------------------------------------------------------
#
#   FINANZAS Y FACTURACION
#
#----------------------------------------------------------------
class BancoAdmin(admin.ModelAdmin):
    list_display = ('nombre','tasaprotesto')
    ordering = ('nombre',)
    search_fields = ('nombre','tasaprotesto')

class CuentaBancoAdmin(admin.ModelAdmin):
    list_display = ('banco','numero', 'tipocuenta', 'representante')
    ordering = ('banco',)
    search_fields = ('banco','numero','tipocuenta')
    list_filter = ('numero',)

class ClienteFacturaAdmin(admin.ModelAdmin):
    list_display = ('ruc','nombre', 'direccion', 'telefono')
    ordering = ('ruc',)
    search_fields = ('ruc','nombre')


class FacturaAdmin(admin.ModelAdmin):
    list_display = ('numero','fecha', 'valida', 'cliente','subtotal','iva','total','caja','impresa','estado','mensaje','numautorizacion','fechaautorizacion','claveacceso')
    ordering = ('numero','fecha')
    search_fields = ('numero','fecha')
    list_filter = ('impresa','valida','caja')

class PrecioMatriculaAdmin(admin.ModelAdmin):
    list_display = ('periodo','sede', 'carrera', 'precio')
    ordering = ('periodo','sede', 'carrera', 'precio')
    search_fields = ('periodo','sede')

class RubroAdmin(admin.ModelAdmin):
    list_display = ('fecha','valor', 'inscripcion','cancelado', 'fechavence')
    ordering = ('fecha','valor')
    search_fields = ('fecha','inscripcion__persona__cedula','inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')

class RubroMatriculaAdmin(admin.ModelAdmin):
    list_display = ('rubro','matricula')
    ordering = ('rubro','matricula')
    search_fields = ('rubro__inscripcion__persona__cedula','rubro__inscripcion__persona__apellido1','rubro__inscripcion__persona__apellido2','rubro__inscripcion__persona__nombres')

class RubroNotaDebitoAdmin(admin.ModelAdmin):
    list_display = ('rubro','motivo')
    ordering = ('rubro','motivo')
    search_fields = ('rubro__inscripcion__persona__cedula','rubro__inscripcion__persona__apellido1','rubro__inscripcion__persona__apellido2','rubro__inscripcion__persona__nombres','motivo')

class PrecioActividadExtraCurricularAdmin(admin.ModelAdmin):
    list_display = ('tipo','precio','fecha')
    ordering = ('tipo','fecha')
    search_fields = ('tipo','precio')

class ActividadExtraCurricularAdmin(admin.ModelAdmin):
    list_display = ('periodo','nombre', 'tipo', 'fechainicio','fechafin','costo','responsable','cupo')
    ordering = ('periodo','tipo', 'fechainicio')
    search_fields = ('nombre','tipo')
    list_filter = ('fechainicio',)

class ParticipanteActividadExtraCurricularAdmin(admin.ModelAdmin):
    list_display = ('actividad','inscripcion','nota','asistencia')
    ordering = ('actividad','nota')
    search_fields = ('actividad','inscripcion')

class RubroActividadExtraCurricularAdmin(admin.ModelAdmin):
    list_display = ('rubro','actividad')
    ordering = ('rubro','actividad')
    search_fields = ('rubro','actividad')

class TipoOtroRubroAdmin(admin.ModelAdmin):
    list_display = ('nombre','preciolibre')
    ordering = ('nombre','preciolibre')
    search_fields = ('nombre','preciolibre')

class PrecioTipoOtroRubroAdmin(admin.ModelAdmin):
    list_display = ('tipo','precio','fecha')
    ordering = ('tipo','precio')
    search_fields = ('tipo','fecha')

class RubroOtroAdmin(admin.ModelAdmin):
    list_display = ('rubro','tipo','descripcion')
    ordering = ('rubro','tipo')
    search_fields = ('rubro','tipo')

class LugarRecaudacionAdmin(admin.ModelAdmin):
    list_display = ('nombre','persona','puntoventa','numerofact','numeronotacre','direccion')
    ordering = ('nombre','persona')
    search_fields = ('nombre','persona')

class PagoAdmin(admin.ModelAdmin):
    list_display = ('fecha','sesion','recibe','valor','rubro','efectivo')
    ordering = ('fecha','valor')
    search_fields = ('rubro',)

class PagoChequeAdmin(admin.ModelAdmin):
    list_display = ('numero','banco','fecha','fechacobro','emite','valor','protestado','recibido')
    ordering = ('numero','fecha')
    search_fields = ('banco',)

class PagoTarjetaAdmin(admin.ModelAdmin):
    list_display = ('banco','poseedor','valor','procesadorpago','referencia','fecha')
    ordering = ('banco','valor','fecha')
    search_fields = ('banco','poseedor')



class FacturaCanceladaAdmin(admin.ModelAdmin):
    list_display = ('factura','motivo','fecha','sesion')
    ordering = ('factura',)
    search_fields = ('factura','fecha')

class ChequeProtestadoAdmin(admin.ModelAdmin):
    list_display = ('cheque','motivo','fecha')
    ordering = ('cheque',)
    search_fields = ('cheque','fecha')

# EVALUACIONES A DOCENTES

class CoordinadorCarreraAdmin(admin.ModelAdmin):
    list_display = ('persona','carrera','periodo')
    ordering = ('persona','carrera')
    search_fields = ('persona','carrera')
    list_filter = ('periodo','carrera')

class AmbitoInstrumentoEvaluacionAdmin(admin.ModelAdmin):
    list_display = ('instrumento','ambito')
    ordering = ('instrumento',)
    search_fields = ('instrumento','ambito')

class IndicadorAmbitoInstrumentoEvaluacionAdmin(admin.ModelAdmin):
    list_display = ('ambitoinstrumento','indicador')
    ordering = ('ambitoinstrumento',)
    search_fields = ('ambitoinstrumento','indicador')

class ProcesoEvaluativoAdmin(admin.ModelAdmin):
    list_display = ('periodo','instrumentoalumno','instrumentoprofesor','instrumentocoordinador','desde','hasta')
    ordering = ('periodo','desde')
    search_fields = ('periodo',)

class EvaluacionProfesorAdmin(admin.ModelAdmin):
    list_display = ('proceso','profesor','fecha')
    ordering = ('proceso','fecha')
    search_fields = ('profesor__persona__nombres', 'profesor__persona__apellido1', 'profesor__persona__apellido2')

class EncuestaAdmin(admin.ModelAdmin):
    list_display = ('nombre','fechainicio','fechafin', 'activa', 'instrumento', 'obligatoria')
    ordering = ('fechainicio','fechafin','nombre')
    search_fields = ('nombre', )

class DatoInstrumentoEvaluacionAdmin(admin.ModelAdmin):
    list_display = ('evaluacion','indicador','valor','observaciones')
    ordering = ('evaluacion',)
    search_fields = ('valor','evaluacion')

#Modelos Admin para los Roles de Pagos de Profesores
class RolPagoAdmin(admin.ModelAdmin):
    list_display = ('nombre','inicio','fin')
    ordering = ('inicio',)
    search_fields = ('nombre','inicio')

class RolPagoProfesorAdmin(admin.ModelAdmin):
    list_display = ('rol','profesor','horastrabajo')
    ordering = ('rol',)
    search_fields = ('rol','profesor')

class RolPagoProfesorDescuentoAdmin(admin.ModelAdmin):
    list_display = ('rolprof','totaldesc')
    ordering = ('rolprof',)
    search_fields = ('rolprof__profesor__persona__apellido1', 'rolprof__profesor__persona__apellido2', 'rolprof__profesor__persona__nombres', 'rolprof__profesor__persona__cedula')

class RolPagoDetalleProfesorAdmin(admin.ModelAdmin):
    list_display = ('rolprof','materia','horasmateria','valormateria')
    ordering = ('rolprof',)
    search_fields = ('rolprof','materia')

class RolPerfilProfesorAdmin(admin.ModelAdmin):
    list_display = ('profesor','chlunes','chmartes','chmiercoles','chjueves','chviernes','chsabado','chdomingo','esfijo','horassalario','salario', 'salariopercibir', 'esadministrativo')
    ordering = ('profesor','esfijo')
    search_fields = ('profesor__persona__nombres','profesor__persona__apellido1','profesor__persona__apellido2')
    list_filter = ('esfijo', 'esadministrativo')

class PrestamoInstitucionalAdmin(admin.ModelAdmin):
    list_display = ('persona','fecha','motivo', 'valor', 'cuota', 'cancelado')
    ordering = ('persona__apellido1','persona__apellido2', 'persona__nombre')
    search_fields = ('persona__nombres','persona__apellido1','persona__apellido2')

class DonacionAdmin(admin.ModelAdmin):
    list_display = ('inscripcion','valor','motivo','fecha','aplicada', 'usuario', 'usuarioaplica')
    ordering = ('fecha','valor')
    search_fields = ('inscripcion__persona__nombres','inscripcion__persona__apellido1','inscripcion__persona__apellido2')
    list_filter = ('aplicada', )

class PersonaDatosMatrizAdmin(admin.ModelAdmin):
    list_display = ('persona','numerocontrato','tienediscapacidad','tipodiscapacidad','porcientodiscapacidad', 'carnetdiscapacidad')
    ordering = ('persona',)
    search_fields = ('persona__nombres','persona__apellido1','persona__apellido2', 'persona__cedula')
    list_filter = ('tienediscapacidad', )


admin.site.register(PersonaDatosMatriz, PersonaDatosMatrizAdmin)
admin.site.register(PrestamoInstitucional, PrestamoInstitucionalAdmin)
admin.site.register(RolPago,RolPagoAdmin)
admin.site.register(RolPagoProfesor,RolPagoProfesorAdmin)
admin.site.register(RolPagoProfesorDescuento,RolPagoProfesorDescuentoAdmin)
admin.site.register(RolPagoDetalleProfesor,RolPagoDetalleProfesorAdmin)
admin.site.register(RolPerfilProfesor,RolPerfilProfesorAdmin)

admin.site.register(CoordinadorCarrera,CoordinadorCarreraAdmin)
admin.site.register(AmbitoInstrumentoEvaluacion,AmbitoInstrumentoEvaluacionAdmin)
admin.site.register(IndicadorAmbitoInstrumentoEvaluacion,IndicadorAmbitoInstrumentoEvaluacionAdmin)
admin.site.register(ProcesoEvaluativo,ProcesoEvaluativoAdmin)
admin.site.register(EvaluacionProfesor,EvaluacionProfesorAdmin)
admin.site.register(Encuesta,EncuestaAdmin)
admin.site.register(DatoInstrumentoEvaluacion,DatoInstrumentoEvaluacionAdmin)
admin.site.register(AmbitoEvaluacion)
admin.site.register(IndicadorEvaluacion)
admin.site.register(InstrumentoEvaluacion)

admin.site.register(ProcesadorPagoTarjeta)
admin.site.register(TipoActividadExtraCurricular)

admin.site.register(CuentaBanco,CuentaBancoAdmin)
admin.site.register(Banco,BancoAdmin)
admin.site.register(ClienteFactura,ClienteFacturaAdmin)
admin.site.register(Factura, FacturaAdmin)
admin.site.register(PrecioMatricula, PrecioMatriculaAdmin)
admin.site.register(Rubro, RubroAdmin)
admin.site.register(RubroMatricula, RubroMatriculaAdmin)
admin.site.register(RubroNotaDebito, RubroNotaDebitoAdmin)
admin.site.register(PrecioActividadExtraCurricular, PrecioActividadExtraCurricularAdmin)
admin.site.register(ActividadExtraCurricular, ActividadExtraCurricularAdmin)
admin.site.register(ParticipanteActividadExtraCurricular, ParticipanteActividadExtraCurricularAdmin)
admin.site.register(RubroActividadExtraCurricular, RubroActividadExtraCurricularAdmin)
admin.site.register(TipoOtroRubro, TipoOtroRubroAdmin)
admin.site.register(PrecioTipoOtroRubro, PrecioTipoOtroRubroAdmin)
admin.site.register(RubroOtro, RubroOtroAdmin)
admin.site.register(LugarRecaudacion, LugarRecaudacionAdmin)
admin.site.register(Pago, PagoAdmin)
admin.site.register(PagoCheque, PagoChequeAdmin)
admin.site.register(PagoTarjeta, PagoTarjetaAdmin)
admin.site.register(FacturaCancelada, FacturaCanceladaAdmin)
admin.site.register(ChequeProtestado, ChequeProtestadoAdmin)
admin.site.register(Donacion, DonacionAdmin)
admin.site.register(DonacionRubros)
admin.site.register(EvaluacionCoordinadorDocente)
# admin.site.register(EvaluacionDocentePeriodo)
admin.site.register(PeriodoEvaluacion)
class EvaluacionDocentePeriodoAdmin(admin.ModelAdmin):
    readonly_fields = ('evaluaciondocente','periodo','profesor')
    list_display = ('evaluaciondocente','periodo','profesor')
    ordering = ('profesor__persona__apellido1',)
    search_fields = ('profesor__persona__apellido1', )
    list_filter = ('evaluaciondocente',)
admin.site.register(EvaluacionDocentePeriodo,EvaluacionDocentePeriodoAdmin)

class EvaluacionAlumnoAdmin(admin.ModelAdmin):
    readonly_fields = ('evaluaciondocente','inscripcion')
    list_display = ('evaluaciondocente', 'inscripcion')
    ordering = ('inscripcion__persona__apellido1',)
    search_fields = ('inscripcion__persona__apellido1', )
    list_filter = ('evaluaciondocente',)
admin.site.register(EvaluacionAlumno,EvaluacionAlumnoAdmin)

class EstudioInscripcionAdmin(admin.ModelAdmin):
    list_display = ('inscripcion','colegio','titulo','incorporacion','especialidad','universidad','carrera','anoestudio','graduado')
    ordering = ('inscripcion__persona__apellido1',)
    search_fields = ('inscripcion','graduado')
    list_filter = ('titulo','carrera','colegio')

class EmpresaInscripcionAdmin(admin.ModelAdmin):
    list_display = ('inscripcion','razon','cargo','direccion','telefono','email')
    ordering = ('inscripcion__persona__apellido1',)
    search_fields = ('inscripcion','cargo')
    list_filter = ('cargo','telefono')

class ObservacionGraduadoAdmin(admin.ModelAdmin):
    list_display = ('graduado','observaciones','fecha')
    ordering = ('graduado__inscripcion__persona__apellido1', 'inscripcion__persona__apellido2')
    search_fields = ('graduado__inscripcion__persona__apellido1','graduado__inscripcion__persona__apellido2','graduado__inscripcion__persona__nombres')
    list_filter = ('fecha',)

class ObservacionInscripcionAdmin(admin.ModelAdmin):
    list_display = ('inscripcion','tipo','observaciones','fecha')
    ordering = ('inscripcion__persona__apellido1', 'inscripcion__persona__apellido2')
    search_fields = ('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')
    list_filter = ('fecha',)


admin.site.register(EstudioInscripcion, EstudioInscripcionAdmin)
admin.site.register(EmpresaInscripcion, EmpresaInscripcionAdmin)
admin.site.register(ObservacionInscripcion, ObservacionInscripcionAdmin)
admin.site.register(ObservacionGraduado, ObservacionGraduadoAdmin)


class CierreSesionCajaAdmin(admin.ModelAdmin):
    list_display = ('sesion', 'bill100', 'bill50', 'bill20', 'bill10', 'bill5', 'bill2', 'bill1', 'enmonedas','deposito','total','fecha','hora')
    ordering = ('sesion__fecha',)

admin.site.register(CierreSesionCaja, CierreSesionCajaAdmin)

class PagoCalendarioAdmin(admin.ModelAdmin):
    list_display = ('periodo','tipo','fecha','valor')
    ordering = ('periodo','tipo')
    list_filter = ('periodo',)

admin.site.register(PagoCalendario, PagoCalendarioAdmin)

# Nuevos modelos para Nomina

class MultaAdmin(admin.ModelAdmin):
    list_display = ('profesor','tipo','valor','fecha', 'motivo', 'cancelada')
    ordering = ('fecha','tipo')
    search_fields = ('profesor__persona__apellido1', 'profesor__persona__apellido2', 'profesor__persona__nombres', 'profesor__persona__cedula')
    list_filter = ('tipo', 'cancelada')

#Modelos para el SRI - Impuesto a la Renta y Gastos Personales
class ProfesorInstitucionGPAdmin(admin.ModelAdmin):
    list_display = ('perfilprof', 'vivienda', 'educacion', 'salud', 'vestimenta', 'alimentacion', 'total')
    ordering = ('perfilprof',)
    search_fields = ('perfilprof__profesor__persona__nombres', 'perfilprof__profesor__persona__apellido1', 'perfilprof__profesor__persona__apellido2', 'perfilprof__profesor__persona__cedula')

class TablaTarifaIRPersonaNaturalAdmin(admin.ModelAdmin):
    list_display = ('anno', 'nombre', 'registro')
    ordering = ('anno',)
    search_fields = ('anno',)
    list_filter = ('anno',)

class DetalleTablaTarifaIRPersonaNaturalAdmin(admin.ModelAdmin):
    list_display = ('tarifa', 'fb', 'eh', 'ifb', 'ife')
    ordering = ('fb', 'tarifa')
    search_fields = ('tarifa__anno','tarifa__registro')

class MateriaRecepcionActaNotasAdmin(admin.ModelAdmin):
    list_display = ('materia', 'entregada', 'fecha', 'codigo', 'entrega', 'observaciones')
    ordering = ('fecha', 'materia__profesormateria__profesor')
    search_fields = ('materia__profesormateria__profesor__persona__apellido1','materia__profesormateria__profesor__persona__apellido2', 'materia__profesormateria__profesor__persona__nombres', 'materia__profesormateria__profesor__persona__cedula', 'materia__asignatura')
    list_filter = ('materia__profesormateria__profesor__persona__apellido1','materia__nivel__paralelo')

admin.site.register(MateriaRecepcionActaNotas, MateriaRecepcionActaNotasAdmin)
admin.site.register(ProfesorInstitucionGP, ProfesorInstitucionGPAdmin)
admin.site.register(TablaTarifaIRPersonaNatural, TablaTarifaIRPersonaNaturalAdmin)
admin.site.register(DetalleTablaTarifaIRPersonaNatural, DetalleTablaTarifaIRPersonaNaturalAdmin)
admin.site.register(Multa, MultaAdmin)
admin.site.register(TipoMulta)

# Modelos para Actividades de la Institucion por Periodos
class TipoActividadAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'representacion')
    ordering = ('nombre', )
    search_fields = ('nombre', )

class ActividadAdmin(admin.ModelAdmin):
    list_display = ('periodo', 'nombre', 'inicio', 'fin', 'tipo', 'lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo')
    ordering = ('periodo', 'inicio')
    search_fields = ('periodo__nombre','nombre')
    list_filter = ('tipo', )

class TipoRetencionAdmin(admin.ModelAdmin):
    list_display = ('descripcion', 'porcentaje')
    ordering = ('descripcion', 'porcentaje')

class VehiculoAdmin(admin.ModelAdmin):
    list_display =("placa","codigo")
    ordering = ("placa","codigo")

class SesionPracticaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'comienza', 'termina')
    ordering = ('nombre',)
    search_fields = ('nombre',)

class TurnoPracticaAdmin(admin.ModelAdmin):
    list_display = ('sesionpracticas', 'turno', 'comienza', 'termina')
    ordering = ('sesionpracticas','turno')
    search_fields = ('sesionpracticas','turno')
    list_filter = ('sesionpracticas','turno')

class VisitaBibliotecaAdmin(admin.ModelAdmin):
    list_display = ('tipopersona','nombre','cedula')
    ordering = ('tipopersona__descripcion','nombre')
    search_fields = ('nombre','cedula')
    list_filter = ('tipopersona__descripcion',)

class DetalleVisitasBibliotecaAdmin(admin.ModelAdmin):
    list_display = ('visitabiblioteca','tipovisitabiblioteca','fecha','sede')
    ordering = ('tipovisitabiblioteca__descripcion','fecha')
    search_fields = ('visitabiblioteca','tipovisitabiblioteca','sede')


# class DetalleVisitasBibliotecaAdmin(admin.ModelAdmin):
#     list_display = ('visitabiblioteca','tipovisitabiblioteca','sede')


admin.site.register(TipoRetencion, TipoRetencionAdmin)
admin.site.register(TipoActividad, TipoActividadAdmin)
admin.site.register(Actividad, ActividadAdmin)
admin.site.register(DepartamentoActividad)
admin.site.register(Vehiculo, VehiculoAdmin)
admin.site.register(SesionPractica, SesionPracticaAdmin)
admin.site.register(TurnoPractica,TurnoPracticaAdmin)
admin.site.register(VisitaBiblioteca,VisitaBibliotecaAdmin)
admin.site.register(DetalleVisitasBiblioteca,DetalleVisitasBibliotecaAdmin)




# Administracion de Logs del Sistema

class LogEntryAdmin(admin.ModelAdmin):

    date_hierarchy = 'action_time'

    # readonly_fields = LogEntry._meta.get_fields()

    list_filter = [
        'user',
        'content_type',
        'action_flag'
    ]

    search_fields = [
        'object_repr',
        'change_message'
    ]


    list_display = [
        'action_time',
        'user',
        'content_type',
        'object_link',
        'action_flag',
        'change_message',
        ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser and request.method != 'POST'

    def has_delete_permission(self, request, obj=None):
        return False

    def object_link(self, obj):
        if obj.action_flag == DELETION:
            link = escape(obj.object_repr)
        else:
            ct = obj.content_type
            link = u'<a href="%s">%s</a>' % (
                reverse('admin:%s_%s_change' % (ct.app_label, ct.model), args=[obj.object_id]),
                escape(obj.object_repr),
                )
        return link
    object_link.allow_tags = True
    object_link.admin_order_field = 'object_repr'
    object_link.short_description = u'object'


admin.site.register(LogEntry, LogEntryAdmin)


class VisitaBoxAdmin(admin.ModelAdmin):
    list_display = ('nombre','cedula')
    ordering = ('nombre',)
    search_fields = ('nombre','cedula')


class DetalleVisitasBoxAdmin(admin.ModelAdmin):
    list_display = ('visitabox','motivo','fecha','tipovisitabox','sede')
    ordering = ('motivo',)
    search_fields = ('visitabox__nombre','motivo','fecha','sede')
    list_filter = ('tipovisitabox','sede')

admin.site.register(DetalleVisitasBox, DetalleVisitasBoxAdmin)

class MateriaExternaAdmin(admin.ModelAdmin):
    list_display = ('entidad','materia','materiaexterna','codigo','cantexport')
    ordering = ('codigo',)
    search_fields = ('codigo',)

admin.site.register(MateriaExterna, MateriaExternaAdmin)
admin.site.register(VisitaBox,VisitaBoxAdmin)
# admin.site.register(TipoVisitasBox)
admin.site.register(ClaveBox)

class TipoVisitaBoxAdmin(admin.ModelAdmin):
    list_display = ('descripcion','alias','sede','valida_deuda','valida_retiro','estado')
    ordering = ('descripcion',)
    search_fields = ('descripcion',)

admin.site.register(TipoVisitasBox, TipoVisitaBoxAdmin)
class ValeCajaAdmin(admin.ModelAdmin):
    list_display = ('recibe','valor','responsable','concepto','sesion')
    ordering = ('sesion__fecha',)
    search_fields = ('responsable','sesion__fecha')

admin.site.register(ValeCaja, ValeCajaAdmin)

# class UsuarioPreguntaAdmin(admin.ModelAdmin):
#     list_display = ('usuario','pregunta','respuesta')
#     ordering = ('usuario__username','pregunta__descripcion','respuesta')
#     search_fields = ('usuario__username','pregunta__descripcion','respuesta')
#
# admin.site.register(UsuarioPregunta, UsuarioPreguntaAdmin)
# admin.site.register(Pregunta)

class EstudianteXEgresarAdmin(admin.ModelAdmin):
    list_display = ('inscripcion','promedio','estado')
    ordering = ('inscripcion__persona__nombres','promedio','estado')
    # search_fields = ('inscripcion','promedio','estado')

admin.site.register(EstudianteXEgresar, EstudianteXEgresarAdmin)

class TipoConsultaAdmin(admin.ModelAdmin):
    list_display = ('descripcion',)
    ordering = ('descripcion',)
    search_fields = ('descripcion',)

admin.site.register(TipoConsulta, TipoConsultaAdmin)

class ParametroEvaluacionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'alias')
    ordering = ('nombre','alias')
    search_fields = ('nombre','alias')

admin.site.register(ParametroEvaluacion, ParametroEvaluacionAdmin)
admin.site.register(GrupoPractica)

#########################################################################

class TipoTestAdmin(admin.ModelAdmin):
    list_display = ('descripcion',)
    ordering = ('descripcion',)
    search_fields = ('descripcion',)

admin.site.register(TipoTest, TipoTestAdmin)

class InstruccionTestAdmin(admin.ModelAdmin):
    list_display = ('id','tipotest')
    ordering = ('tipotest__descripcion',)
    search_fields = ('tipotest__descripcion',)

admin.site.register(InstruccionTest, InstruccionTestAdmin)


class ParametroTestAdmin(admin.ModelAdmin):
    list_display = ('descripcion',)
    ordering = ('descripcion',)
    search_fields = ('descripcion',)

admin.site.register(ParametroTest, ParametroTestAdmin)
admin.site.register(EjercicioTest)
admin.site.register(TipoIngreso)

class PuntoBaremoAdmin(admin.ModelAdmin):
    list_display = ('descripcion','directo','percentil')
    ordering = ('descripcion',)
    search_fields = ('descripcion',)


class ServiciosBoxAdmin(admin.ModelAdmin):
    list_display = ('tipovisita','tipopersona','libre')
    ordering = ('tipovisita__descripcion','tipopersona__descripcion')
    search_fields = ('tipovisita',)
    list_filter = ('tipovisita','tipopersona')

admin.site.register(ServiciosBox, ServiciosBoxAdmin)

admin.site.register(PuntoBaremo, PuntoBaremoAdmin)
admin.site.register(PreguntaTest)
#admin.site.register(InscripcionTipoTest)
admin.site.register(TipoMedicamento)
admin.site.register(ProgresoTutoria)
admin.site.register(TipoSegmento)

class RecetaVisitaBoxAdmin(admin.ModelAdmin):
    list_display = ('registro','cantidad','visita')
    ordering = ('visita__id','cantidad')
    search_fields = ('visita__id','cantidad','registro__nombre__descripcion')
    list_filter = ('visita__id','cantidad')
admin.site.register(RecetaVisitaBox,RecetaVisitaBoxAdmin)

class RegistroMedicamentoAdmin(admin.ModelAdmin):
    list_display = ('id','nombre','presentacion','cantidad')
    search_fields = ('nombre',)
# nombre = models.ForeignKey(SuministroBox,blank=True,null=True, on_delete=models.CASCADE)
#     presentacion = models.ForeignKey(TipoMedicamento,blank=True,null=True, on_delete=models.CASCADE)
#     cantidad = models.IntegerField(blank=True,null=True)
admin.site.register(RegistroMedicamento,RegistroMedicamentoAdmin)

admin.site.register(TipoSuspension)
admin.site.register(MotivoSuspension)
admin.site.register(TrasladoMedicamento)

class ResolucionAdmin(admin.ModelAdmin):
    list_display = ('asunto','resumen','fecharesolucion')
    ordering = ('asunto',)
    search_fields = ('asunto','resumen','fecharesolucion')

admin.site.register(Resolucion, ResolucionAdmin)

admin.site.register(InscripcionSuspension)
admin.site.register(RubroMasivo)
class DetalleRubroMasivoAdmin(admin.ModelAdmin):
    list_display = ('rubromasivo','rubrootro')
    ordering = ('rubrootro__rubro__inscripcion__persona__apellido1',)
    search_fields = ('rubrootro__rubro__inscripcion__persona__nombres','rubrootro__rubro__inscripcion__persona__apellido1','rubrootro__rubro__inscripcion__persona__apellido2')
    list_filter = ('rubromasivo__carrera','rubromasivo__descripcion')

admin.site.register(DetalleRubroMasivo,DetalleRubroMasivoAdmin)
admin.site.register(GrupoSeminario)
class InscripcionSeminarioAdmin(admin.ModelAdmin):
    list_display = ('gruposeminario','matricula','fecha','rubrootro')
    ordering = ('matricula__inscripcion__persona__apellido1',)
    search_fields = ('matricula__inscripcion__persona__nombres','matricula__inscripcion__persona__apellido1','matricula__inscripcion__persona__apellido2')
    list_filter = ('gruposeminario__id','matricula__inscripcion__persona__apellido1')

admin.site.register(InscripcionSeminario,InscripcionSeminarioAdmin)

class PreInscripcionAdmin(admin.ModelAdmin):
    list_display = ('nombres','apellido1','apellido2',)
    ordering = ('apellido1',)
    search_fields = ('apellido1','apellido2','nombres')

admin.site.register(PreInscripcion,PreInscripcionAdmin)

admin.site.register(ProcesoDobleMatricula)
admin.site.register(ActividadVinculacion)
# admin.site.register(EstudianteVinculacion)
admin.site.register(DocenteVinculacion)
admin.site.register(EvidenciaVinculacion)
admin.site.register(ObservacionVinculacion)
admin.site.register(KitCongreso)
admin.site.register(CalificacionEvaluacion)
admin.site.register(Convenio)
admin.site.register(BeneficiariosVinculacion)
admin.site.register(TipoDocumenBeca)
admin.site.register(Absentismo)
admin.site.register(TipoPrograma)
admin.site.register(Programa)

class InscripcionFichaSocioEconomicaBecaAmin(admin.ModelAdmin):
    list_display = ('inscripcion',)
    ordering = ('inscripcion',)
    search_fields = ('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres','inscripcion__persona__cedula')
    list_filter = ('inscripcion',)

admin.site.register(InscripcionFichaSocioEconomicaBeca, InscripcionFichaSocioEconomicaBecaAmin)

admin.site.register(ClaveEvaluacionNota)
admin.site.register(TipoAtencionBox)

# admin.site.register(SolicitudBeca)
admin.site.register(ReciboCaja)
admin.site.register(TipoAnuncio)
admin.site.register(AsistAsuntoEstudiant)
admin.site.register(IncidenciaAsignada)
admin.site.register(IncidenciaAdministrativo)
admin.site.register(ObservacionIncidencia)
admin.site.register(DepartamentoIncidenciaAsig)
admin.site.register(GrupoCorreo)
admin.site.register(TipoConsultaAsunto)
admin.site.register(InscripcionPanel)
admin.site.register(PermisoPanel)
admin.site.register(Panel)
admin.site.register(TipoRespuesta)
admin.site.register(ReferenciaPersonal)
admin.site.register(ReferenciaBeca)
# admin.site.register(InscripcionSenescyt)

class InscripcionSenescytAdmin(admin.ModelAdmin):
    list_display = ('inscripcion',)
    ordering = ('inscripcion__persona__apellido1',)
    search_fields = ('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')


admin.site.register(InscripcionSenescyt,InscripcionSenescytAdmin)

class ReciboPermisoConduAdmin(admin.ModelAdmin):
    list_display = ('inscripcion','numero','fecha','usuario')
    ordering = ('inscripcion__persona__apellido1',)
    search_fields = ('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres','numero','fecha','usuario__username')

admin.site.register(ReciboPermisoCondu,ReciboPermisoConduAdmin)

admin.site.register(TituloExamenCondu)
admin.site.register(PreguntaExamen)

class InscripcionExamenAdmin(admin.ModelAdmin):
    list_display = ('inscripcion', 'tiempo','puntaje','fecha','valida')
    ordering = ('inscripcion','fecha')
    search_fields = ('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres','inscripcion__persona__cedula')
    # list_filter = ('inscripcion',)

admin.site.register(InscripcionExamen, InscripcionExamenAdmin)
admin.site.register(EliminaSuspension)

class DetalleExamenAdmin(admin.ModelAdmin):
    list_display = ('inscripcionexamen', 'fecha')
    ordering = ('inscripcionexamen__inscripcion','fecha')
    search_fields = ('inscripcionexamen__inscripcion__persona__apellido1','inscripcionexamen__inscripcion__persona__apellido2','inscripcionexamen__inscripcion__persona__nombres','inscripcionexamen__inscripcion__persona__cedula')
    # list_filter = ('inscripcion',)

admin.site.register(DetalleExamen, DetalleExamenAdmin)
admin.site.register(InscripcionPracticas)

class TurnoCabAdmin(admin.ModelAdmin):
    list_display = ('AtencionCliente','fechatiket')
    ordering = ('AtencionCliente',)
    search_fields = ('AtencionCliente__id','fechatiket')
    list_filter = ('AtencionCliente',)

admin.site.register(TurnoCab,TurnoCabAdmin)

class ReferidosInscripcionAdmin(admin.ModelAdmin):
    list_display = ('apellido1','apellido2','nombres','inscrito','pago','activo','inscripcion')
    ordering = ('apellido1','apellido2')
    search_fields = ('apellido1','cedula','inscripcion__persona__apellido1')
    list_filter = ('inscrito',)

admin.site.register(ReferidosInscripcion,ReferidosInscripcionAdmin)

class TipoNoRegistroAspiranteAdmin(admin.ModelAdmin):
    list_display = ('id','descripcion')
    ordering = ('descripcion',)

admin.site.register(TipoNoRegistroAspirante,TipoNoRegistroAspiranteAdmin)

class TipoRegistroAspiranteAdmin(admin.ModelAdmin):
    list_display = ('id','descripcion')
    ordering = ('descripcion',)

admin.site.register(TipoRegistroAspirante,TipoRegistroAspiranteAdmin)

class ColegioAdmin(admin.ModelAdmin):
    list_display = ('id','nombre','provincia','canton','tipo')
    ordering = ('nombre',)

admin.site.register(Colegio,ColegioAdmin)
admin.site.register(CodigoFormaPago)

class RubrosConduccionAdmin(admin.ModelAdmin):
    list_display = ('carrera','precio','descripcion')
    ordering = ('carrera',)
admin.site.register(RubrosConduccion,RubrosConduccionAdmin)

class DetalleRubrosBecaAdmin(admin.ModelAdmin):
    list_display = ('matricula','rubro','descripcion','descuento','porcientobeca','valorrubro')
    ordering = ('matricula',)
admin.site.register(DetalleRubrosBeca,DetalleRubrosBecaAdmin)

class MateriaNivelAdmin(admin.ModelAdmin):
    list_display = ('materia','nivel','fecha')
    ordering = ('materia__asignatura__nombre','nivel__paralelo')
    search_fields = ('materia__asignatura__nombre','nivel__paralelo')
    list_filter = ('nivel__paralelo',)

class PromedioNotasGradoAdmin(admin.ModelAdmin):
    list_display = ('carrera','asignatura','vial','practica','activo')
    ordering = ('carrera',)
admin.site.register(PromedioNotasGrado,PromedioNotasGradoAdmin)

class SolicitudOnlineAdmin(admin.ModelAdmin):
    list_display = ('nombre','valor','html','form','valida_malla')
    ordering = ('nombre',)
admin.site.register(SolicitudOnline,SolicitudOnlineAdmin)

class SolicitudCarreraAdmin(admin.ModelAdmin):
    list_display = ('solicitud','carrera','activo')
    ordering = ('carrera',)
admin.site.register(SolicitudCarrera,SolicitudCarreraAdmin)


admin.site.register(MateriaNivel,MateriaNivelAdmin)
admin.site.register(IpRecaudacion)
admin.site.register(IpRecaudLugar)
admin.site.register(ReporteExcel)
admin.site.register(GrupoReporteExcel)
admin.site.register(PrecioConsulta)
admin.site.register(AsistenciaCofia)
admin.site.register(RespuestaExamen)
class ExamenPracticaAdmin(admin.ModelAdmin):
    list_display = ('inscripcion', 'puntaje', 'valida','fecha')
    ordering = ('inscripcion__persona__apellido1','inscripcion__persona__apellido2', 'puntaje', 'valida','fecha')
    search_fields = ('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres','inscripcion__persona__cedula')
    list_filter = ('inscripcion__persona__apellido1',)

admin.site.register(ExamenPractica, ExamenPracticaAdmin)
admin.site.register(UsuarioConvenio)
admin.site.register(ConvenioAcademico)
admin.site.register(ConvenioUsuario)
admin.site.register(ConvenioBox)
admin.site.register(RegistroVehiculo)
admin.site.register(PersonaConduccion)
admin.site.register(CategoriaVehiculo)
admin.site.register(TipoCombustible)
admin.site.register(Promocion)
admin.site.register(Departamento)
admin.site.register(DepartamentoGroup)
admin.site.register(RequerimientoDepart)
admin.site.register(DetalleRequerimiento)
admin.site.register(CertificadoEntregado)
admin.site.register(TipoCulminacionEstudio)
admin.site.register(ProfesorMateria)
admin.site.register(AlternativasBoxExt)
admin.site.register(PagoNivel)
admin.site.register(LibroRevista)
admin.site.register(ArchivoTestConduccion)

# admin.site.register(SolicitudEstudiante)

class ArchivoWesterAdmin(admin.ModelAdmin):
    list_display = ('fecha','archivo','archivowester')
    ordering = ('fecha',)
admin.site.register(ArchivoWester,ArchivoWesterAdmin)

class SolicitudEstudianteAdmin(admin.ModelAdmin):
    list_display = ('inscripcion','solicitud','fecha')
    ordering = ('fecha',)
admin.site.register(SolicitudEstudiante,SolicitudEstudianteAdmin)

class RegistroWesterAdmin(admin.ModelAdmin):
    list_display = ('codigo','valor','facturado','archivo')
    ordering = ('fecha',)
    list_filter = ('archivo__fecha',)
admin.site.register(RegistroWester,RegistroWesterAdmin)


class IndicEvaluacionExamenAdmin(admin.ModelAdmin):
    list_display = ('descripcion', 'escala','teorico','coordinacion','carrera')
    ordering = ('coordinacion','teorico','descripcion','escala')
    search_fields = ('descripcion','escala')
    list_filter = ('descripcion',)

admin.site.register(IndicEvaluacionExamen,IndicEvaluacionExamenAdmin)

class ProfeExamenPracticaAdmin(admin.ModelAdmin):
    list_display = ('profesor','examenpractica')
    ordering = ('profesor__persona__apellido1','profesor__persona__apellido2')
    search_fields = ('profesor__persona__apellido1','profesor__persona__apellido2')


admin.site.register(ProfeExamenPractica,ProfeExamenPracticaAdmin)

class ComisionCongresoAdmin(admin.ModelAdmin):
    list_display = ('id','nombre','moderador','lugar','fecha','horainicio','horafin','activo')
    ordering = ('nombre',)

admin.site.register(ComisionCongreso,ComisionCongresoAdmin)

class GrupoPonenciaAdmin(admin.ModelAdmin):
    list_display = ('id','codigo','nombre','horainicio','horafin','integrantes','comision','modalidad','revisadopor','precio','activo')
    ordering = ('nombre',)

admin.site.register(GrupoPonencia,GrupoPonenciaAdmin)
admin.site.register(InscripcionGrupoPonencia)

class ModalidadPonenciaAdmin(admin.ModelAdmin):
    list_display = ('id','nombre','activo')
    ordering = ('nombre',)

admin.site.register(ModalidadPonencia,ModalidadPonenciaAdmin)

class VendedorAdmin(admin.ModelAdmin):
    list_display = ('nombres','identificacion','extra')
    ordering = ('nombres',)
    search_fields = ('nombres','identificacion')

admin.site.register(Vendedor,VendedorAdmin)

class EspecieGrupoAdmin(admin.ModelAdmin):
    list_display = ('tipoe','departamento','todas_carreras')
    ordering = ('tipoe__nombre',)
    search_fields = ('tipoe__nombre',)
    list_filter = ('tipoe','departamento','todas_carreras')

admin.site.register(EspecieGrupo,EspecieGrupoAdmin)

class InscripcionVendedorAdmin(admin.ModelAdmin):
    list_display = ('inscripcion','vendedor','fecha')
    ordering = ('inscripcion__persona__apellido1','inscripcion__persona__apellido2','vendedor')
    search_fields = ('inscripcion__persona__apellido1','inscripcion__persona__apellido2','vendedor')

admin.site.register(InscripcionVendedor,InscripcionVendedorAdmin)

class ExternosAdmin(admin.ModelAdmin):
    list_display = ('identificacion','apellidos','nombres')
    ordering = ('apellidos','nombres','fecha')
    search_fields = ('identificacion','apellidos','nombres')
    list_filter = ('cuenta__numero',)

admin.site.register(RegistroExterno,ExternosAdmin)

class MensajesEnviadoAdmin(admin.ModelAdmin):
    list_display = ('nombre','celular','filtro','nivel','periodo','grupo','carrera')
    ordering = ('nombre','fecha','filtro')
    search_fields = ('nombre','filtro')

admin.site.register(MensajesEnviado,MensajesEnviadoAdmin)

class TipoDocumentosOficialesAdmin(admin.ModelAdmin):
    list_display = ('id','tipo')
    ordering = ('tipo',)
admin.site.register(TipoDocumentosOficiales,TipoDocumentosOficialesAdmin)
admin.site.register(PersonaExamenExt)
admin.site.register(ExamenExterno)
admin.site.register(PersonaExterna)
admin.site.register(Sector)
admin.site.register(VideoLogin)
admin.site.register(ComponenteExamen)
admin.site.register(PreguntaExterno)
admin.site.register(AulaAdministra)
admin.site.register(OcupacionEstudiante)
admin.site.register(IngresosEstudiante)
admin.site.register(BonoFmlaEstudiante)
admin.site.register(TipAulaExamen)
admin.site.register(TipoPersonaCongreso)
admin.site.register(RequerimientoCongreso)
admin.site.register(DatosPersonaCongresoIns)
admin.site.register(PagoExternoPedagogia)
admin.site.register(CarreraConvenio)
admin.site.register(ModalidadCarreraConvenio)
admin.site.register(Clasificacion)
admin.site.register(ConvenioClasificacion)
admin.site.register(CalculoTest)
# admin.site.register(CalculoLocus)
admin.site.register(CalculoRasgoEstado)

class RespuestaTestAdmin(admin.ModelAdmin):
    list_display = ('inscripciontipotest','tipotest','preguntatest',)
    ordering = ('inscripciontipotest','tipotest','preguntatest',)
    search_fields = ('inscripciontipotest','tipotest','preguntatest',)

admin.site.register(RespuestaTest, RespuestaTestAdmin)
class PagoPymentezAdmin(admin.ModelAdmin):
    list_display = ('inscripcion','factura','estado','monto','rubros','correo','codigo_aut','referencia_dev','fechatransaccion')
    ordering = ('inscripcion','factura','estado',)
    search_fields = ('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres',)

admin.site.register(PagoPymentez, PagoPymentezAdmin)

class AprobacionVinculacionAdmin(admin.ModelAdmin):
    list_display = ('inscripcion','estudiantevinculacion','fecha')
    ordering = ('inscripcion','estudiantevinculacion')
    search_fields = ('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres','inscripcion__persona__cedula')

admin.site.register(AprobacionVinculacion, AprobacionVinculacionAdmin)

class EstudianteVinculacionAdmin(admin.ModelAdmin):
    list_display = ('actividad','inscripcion','inscripcion')
    ordering = ('inscripcion',)
    search_fields = ('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres','inscripcion__persona__cedula')
    list_filter = ('inscripcion__carrera',)

admin.site.register(EstudianteVinculacion, EstudianteVinculacionAdmin)

class CalculoLocusAdmin(admin.ModelAdmin):
    list_display = ('tipotest','externo','pregunta','interno')
    ordering = ('tipotest','pregunta')
    search_fields = ('pregunta',)
    list_filter = ('externo','pregunta','interno')

admin.site.register(CalculoLocus, CalculoLocusAdmin)

class InscripcionTipoTestAdmin(admin.ModelAdmin):
    list_display = ('inscripcion','observacion','tipotest',)
    ordering = ('inscripcion','observacion','tipotest',)
    search_fields = ('inscripcion','observacion','tipotest',)

admin.site.register(InscripcionTipoTest, InscripcionTipoTestAdmin)

class ResultadoRespuestaAdmin(admin.ModelAdmin):
    list_display = ('inscripciontipotest','tipotest','puntaje',)
    ordering = ('inscripciontipotest','tipotest','puntaje',)
    search_fields = ('inscripciontipotest','tipotest','puntaje',)

admin.site.register(ResultadoRespuesta, ResultadoRespuestaAdmin)

class SolicitudesGrupoAdmin(admin.ModelAdmin):
    list_display = ('tiposolic','carrera','grupo','todas_carreras')
    ordering = ('tiposolic__nombre',)
    search_fields = ('tiposolic__nombre',)
    list_filter = ('tiposolic','carrera','grupo','todas_carreras')

admin.site.register(SolicitudesGrupo,SolicitudesGrupoAdmin)

admin.site.register(EvaluacionITB)
# admin.site.register(AsistenteDepartamento)

class AsistenteDepartamentoAdmin(admin.ModelAdmin):
    list_display = ('departamento','persona','cantidad','cantidadsol','puedereasignar')
    ordering = ('cantidad',)
    search_fields = ('persona',)

admin.site.register(AsistenteDepartamento,AsistenteDepartamentoAdmin)

class LogAceptacionProfesorMateriaAdmin(admin.ModelAdmin):
    list_display = ('profesor','profesormateria','fechaceptacion','tipolog','oberservacion')
    ordering = ('profesor',)
    search_fields = ('profesor__persona__apellido1','profesor__persona__apellido2','profesor__persona__nombres')
    list_filter = ('profesor',)
admin.site.register(LogAceptacionProfesorMateria,LogAceptacionProfesorMateriaAdmin)

class CategoriaRubroAdmin(admin.ModelAdmin):
    list_display = ('categoria','porcentaje','porcentajecom','porcentajedesc')
    ordering = ('categoria',)
    search_fields = ('categoria',)

admin.site.register(CategoriaRubro,CategoriaRubroAdmin)

class MotivoAlcanceAdmin(admin.ModelAdmin):
    list_display = ('motivo','estado')
    ordering = ('motivo',)
    search_fields = ('motivo',)

admin.site.register(MotivoAlcance,MotivoAlcanceAdmin)


class TipoMultaDocenteAdmin(admin.ModelAdmin):
    list_display = ('nombre','valor','estado')
    ordering = ('valor',)
    search_fields = ('nombre',)

admin.site.register(TipoMultaDocente,TipoMultaDocenteAdmin)


class MultaDocenteMateriaAdmin(admin.ModelAdmin):
    list_display = ('materia','profesor','tipomulta','fechadesde','fechahasta','aprobado','activo')
    ordering = ('materia',)
    search_fields = ('materia__asignatura__nombre','profesor__persona__apellido1','profesor__persona__apellido2')

admin.site.register(MultaDocenteMateria,MultaDocenteMateriaAdmin)

admin.site.register(PagosCursoITB)

class CoordinacionDepartamentoAdmin(admin.ModelAdmin):
    list_display = ('departamento','coordinacion')
    ordering = ('departamento',)
    search_fields = ('departamento__descripcion',)

admin.site.register(CoordinacionDepartamento,CoordinacionDepartamentoAdmin)

admin.site.register(Jornada)

class EvaluacionAlcanceAdmin(admin.ModelAdmin):
    list_display = ('materiaasignada','n1','n2','n3','n4','examen','recuperacion')
    ordering = ('materiaasignada',)
    search_fields = ('materiaasignada__materia__asignatura__nombre','materiaasignada__matricula__inscripcion__persona__apellido1','materiaasignada__matricula__inscripcion__persona__apellido2','materiaasignada__matricula__inscripcion__persona__nombres')

admin.site.register(EvaluacionAlcance,EvaluacionAlcanceAdmin)

class SesionJornadaAdmin(admin.ModelAdmin):
    list_display = ('sesion','jornada')
    ordering = ('jornada','sesion')
    search_fields = ('jornada',)
    list_filter = ('jornada',)
admin.site.register(SesionJornada,SesionJornadaAdmin)

class SolicitudBecaAdmin(admin.ModelAdmin):
    list_display = ('inscripcion',)
    ordering = ('inscripcion',)
    search_fields = (
    'inscripcion__persona__apellido1', 'inscripcion__persona__apellido2', 'inscripcion__persona__nombres',
    'inscripcion__persona__cedula')
    list_filter = ('inscripcion',)

admin.site.register(SolicitudBeca,SolicitudBecaAdmin)
admin.site.register(DetActivaExamenParc)
admin.site.register(ExamenParRespuesta)
admin.site.register(ExamenParcial)
admin.site.register(TituloExamenParcial)
admin.site.register(PreguntaAsigRespuesta)
admin.site.register(PreguntaAsignatura)
admin.site.register(PagoConduccion)
admin.site.register(ArchivoSoliciBeca)
admin.site.register(EmpresaConvenio)

class DetalleEliminaMatriculaAdmin(admin.ModelAdmin):
    list_display = ('eliminadamatriculada','asignatura',)
    ordering = ('asignatura',)
    search_fields = (
    'eliminadamatriculada', 'asignatura')
    list_filter = ('asignatura',)
admin.site.register(DetalleEliminaMatricula,DetalleEliminaMatriculaAdmin)

class TipoPonenciaAdmin(admin.ModelAdmin):
    list_display = ('id','nombre','activo')
    ordering = ('nombre',)

admin.site.register(TipoPonencia,TipoPonenciaAdmin)



admin.site.register(AsistenteSoporte)
admin.site.register(CalificacionSoporte)
admin.site.register(HorarioAsistente)
admin.site.register(TipoProblema)
admin.site.register(ArchivoPichincha)
admin.site.register(RecaudacionPichincha)
admin.site.register(RequerimientoSoporte)
admin.site.register(RequerimSolucion)
admin.site.register(RespProgramdor)
admin.site.register(TipoSeguimiento)
admin.site.register(TutorCongreso)
admin.site.register(TutorMatricula)
admin.site.register(TutorCongSeguimiento)

admin.site.register(Resolucionbeca)
admin.site.register(TablaDescuentoBeca)
admin.site.register(HistoricoNotasITB)

class CuponInscripcionAdmin(admin.ModelAdmin):
    list_display = ('inscripcion','grupo','cupon','descripcion','cuponalias','valor')
    ordering = ('inscripcion','grupo')
    search_fields = ( 'inscripcion__persona__apellido1', 'inscripcion__persona__apellido2', 'inscripcion__persona__nombres',
    'inscripcion__persona__cedula')
    list_filter = ('cupon','grupo')

admin.site.register(CuponInscripcion,CuponInscripcionAdmin)
admin.site.register(RequerimientoAsistentes)


class HorarioAsistenteSolicitudesAdmin(admin.ModelAdmin):
    list_display = ('usuario','horainicio','horafin','fecha')
    ordering = ('fecha','horainicio','horafin')
    search_fields = ( 'usuario__username', )
    list_filter = ('fecha','usuario')
admin.site.register(HorarioAsistenteSolicitudes,HorarioAsistenteSolicitudesAdmin)

admin.site.register(ExamenConvalidacionIngreso)
admin.site.register(DocumentosVinculacionEstudiantes)
admin.site.register(DocumentosOficialesVinculacion)

class PagoReciboCajaInstitucionAdmin(admin.ModelAdmin):
    list_display = ('recibocaja','valor','fecha')
    ordering = ('fecha','recibocaja','valor')
admin.site.register(PagoReciboCajaInstitucion,PagoReciboCajaInstitucionAdmin)


admin.site.register(EntregaJugueteCanasta)
admin.site.register(RubroLog)
admin.site.register(HorarioPersona)
admin.site.register(NivelTutor)
admin.site.register(HistoriaArchivoPymentez)
class ParametroDescuentoAdmin(admin.ModelAdmin):
    list_display = ('porcentaje','cuotas','diaretras','nivel','diactual','matricula','seminario','activo','incluyematricula')
    ordering = ('diaretras','cuotas',)
admin.site.register(ParametroDescuento,ParametroDescuentoAdmin)

class DatosTransfereciaDepositoAdmin(admin.ModelAdmin):
    list_display = ('solicitud','referencia','fecha','disponible','valor','pago')
    ordering = ('fecha',)
    search_fields = ( 'solicitud__persona__inscripcion__apellido1','solicitud__persona__inscripcion__apellido2','solicitud__persona__inscripcion__nombres', )
    list_filter = ('fecha','solicitud__persona__inscripcion')
admin.site.register(DatosTransfereciaDeposito,DatosTransfereciaDepositoAdmin)

class ParametrosPromocionAdmin(admin.ModelAdmin):
    list_display = ('iniciodiferir','findiferir','fechadiferir')
    ordering = ('iniciodiferir',)
     # This will help you to disbale add functionality
    def has_add_permission(self, request):
        return False
    #
    #     # This will help you to disable delete functionaliyt
    def has_delete_permission(self, request, obj=None):
        return False
admin.site.register(ParametrosPromocion,ParametrosPromocionAdmin)
admin.site.register(RegistroLlamadas)
admin.site.register(InscripcionMotivoCambioPromocion)
admin.site.register(EmpresaSinConvenio)
admin.site.register(SolicitudPracticas)
admin.site.register(EvaluacionSupervisorEmp)
admin.site.register(EvaluacionAcademico)
admin.site.register(SegmentoIndicadorEmp)
admin.site.register(SegmentoDetalle)
admin.site.register(IndicadorAcademico)
admin.site.register(PuntajeIndicador)
admin.site.register(EscenarioPractica)

admin.site.register(SupervisorPracticas)
admin.site.register(TipoSupervisionPracticas)
admin.site.register(SupervisionPracticas)
admin.site.register(SupervisionPracticasDet)
admin.site.register(CoordinadorPracticas)


class ReportePracticasAdmin(admin.ModelAdmin):
    list_display = ('reporte','nombre','carrera','nivel','orden','convenio','sinconvenio','general','estudiante')
    ordering = ('orden',)
admin.site.register(ReportePracticas,ReportePracticasAdmin)
admin.site.register(NombreReportePract)
admin.site.register(EstadoEmpresa)

admin.site.register(ColorZapato)
admin.site.register(TallaZapato)
admin.site.register(ColorUniforme)
admin.site.register(TallaUniforme)
admin.site.register(EntregaUniforme)
admin.site.register(NotasComplexivo)
admin.site.register(NotasComplexivoDet)
admin.site.register(PermisosSga)
admin.site.register(LogQuitarAsignacionProfesor)
admin.site.register(PagoSustentacionesDocente)
admin.site.register(ResponsableBodegaConsultorio)
admin.site.register(RegistroValorporDocente)

admin.site.register(ParametroSeguimiento)
admin.site.register(SeguimientoTutor)
admin.site.register(MatriculaTutor)
admin.site.register(CabSeguimiento)
admin.site.register(DetSeguimiento)
admin.site.register(PeriodoExamen)
admin.site.register(ProvinciaPeriodoEx)
admin.site.register(CronogramaExamen)
admin.site.register(CronogramaAlumno)
admin.site.register(NivelPeriodoEx)
admin.site.register(PagoPracticasDocente)
admin.site.register(CostoAsignatura)
admin.site.register(RegistroPlagioTarjetas)

admin.site.register(CalificacionSolicitudes)
admin.site.register(DescuentosporConvenio)
admin.site.register(ParentescoTipoPersonaEmpresaConvenio)
admin.site.register(TipoPersonaEmpresaConvenio)
admin.site.register(PersonAutorizaBecaAyuda)

admin.site.register(VacunasCovid)

class RegistroVacunasAdmin(admin.ModelAdmin):
    list_display = ('persona','estavacunado','hatenidocovid','fecharegistro','usuario')
    ordering = ('persona',)
    search_fields = ('persona__apellido1','persona__apellido2','persona__cedula',)

admin.site.register(RegistroVacunas,RegistroVacunasAdmin)
admin.site.register(CalificacionAutoestima)
admin.site.register(OrganizacionAprendizaje)
admin.site.register(DescuentoDOBE)
admin.site.register(InscripcionProfesionalizacion)
admin.site.register(TipoMotivoNotaCredito)
admin.site.register(RegistroAceptacionPagoenLinea)
admin.site.register(RegistroAceptacionPagoenLineaConduccion)
admin.site.register(TipoConvenio)
admin.site.register(RegistroAceptacionProtecciondeDatos)
admin.site.register(Webinar)

class ActividadesHorasExtraAdmin(admin.ModelAdmin):
    list_display = ('usuario','descripcion', 'fecha_inicio', 'fecha_fin','horas_extras')
    ordering = ('usuario','fecha_fin',)
    search_fields = ('usuario','descripcion',)
    list_filter = ('fecha_inicio','fecha_fin')


admin.site.register(ActividadesHorasExtra,ActividadesHorasExtraAdmin)


admin.site.register(SupervisorGrupos)
admin.site.register(EjesEvaluacion)
admin.site.register(AreasElementosEvaluacion)
admin.site.register(PreguntasEvaluacion)
admin.site.register(RespuestasEvaluacion)
admin.site.register(RespuestasEjesEvaluacion)
admin.site.register(EvaluacionDocente)
admin.site.register(DetalleEvaluacionPregunta)
admin.site.register(EvaluacionMateria)
admin.site.register(EvidenciaSolicitudAntencion)
admin.site.register(SolicitudAntencion)
admin.site.register(EvaluacionAlcanceHistorial)
admin.site.register(Notificacion)
admin.site.register(NotificacionPersona)
admin.site.register(ClasesOnline)
admin.site.register(EvaluacionCargoPeriodo)
admin.site.register(EntregaUniformeAdmisiones)
admin.site.register(TipoArticulo)
admin.site.register(Genero)
admin.site.register(NucleoFamiliar)
admin.site.register(ZonaResidencia)
admin.site.register(Afiliacion)
admin.site.register(MaterialCasa)
admin.site.register(TipoServicio)
admin.site.register(CondicionesHogar)
admin.site.register(TipoIngresoHogar)
admin.site.register(TipoIngresoPropio)
admin.site.register(TipoEmpleo)
admin.site.register(UsoTransporte)
admin.site.register(TipoTransporte)
admin.site.register(Deporte)
admin.site.register(ManifestacionArtistica)
admin.site.register(DeseosFuturos)
admin.site.register(InstrumentosTutoriaPedagogicas)
admin.site.register(EstrategiasPedagogicas)
admin.site.register(TutoriaPedagogica)
admin.site.register(EncuestaItb)
admin.site.register(InscripcionTestIngreso)
admin.site.register(AlternativaEvaluacion)


class DetalleModeloEvaluativoAdmin(admin.TabularInline):
    model = DetalleModeloEvaluativo


class ModeloEvaluativoAdmin(admin.ModelAdmin):
    inlines = [DetalleModeloEvaluativoAdmin]
    list_display = ('nombre', 'nota_maxima', 'nota_aprobar', 'esta_activo', 'get_sedes')
    ordering = ('nombre',)
    search_fields = ('nombre', )
    list_filter = ('sedes', 'esta_activo')

    def get_sedes(self, obj):
        # return ", ".join([sede.nombre for sede in obj.sedes.all()])
        return obj.sedes.all().values("id").count()

    get_sedes.short_description = 'Sedes'


admin.site.register(ModeloEvaluativo, ModeloEvaluativoAdmin)

class TipoRecursoAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    ordering = ('nombre',)
    search_fields = ('nombre', )
    list_filter = ('nombre', 'activo')


admin.site.register(TipoRecurso, TipoRecursoAdmin)


class EstadoAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    ordering = ('nombre',)
    search_fields = ('nombre',)
    list_filter = ('nombre',)

admin.site.register(Estado, EstadoAdmin)

class EstadoModelAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    ordering = ('nombre',)
    search_fields = ('nombre', )
    list_filter = ('nombre', )

admin.site.register(EstadoModel, EstadoModelAdmin)

class EvaluacionComponenteModelAdmin(admin.ModelAdmin):
    list_display = ('alias',)
    ordering = ('alias',)
    search_fields = ('alias', )
    list_filter = ('alias', )

admin.site.register(EvaluacionComponente, EvaluacionComponenteModelAdmin)


admin.site.register(AreaDominioAcademico)
admin.site.register(DominiosAcademicos)

