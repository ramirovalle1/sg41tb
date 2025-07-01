# -*- coding: latin-1 -*-
import os
from django import forms
from django.contrib.auth.models import Group
from django.db.models import Q
from django.forms.models import ModelForm, ModelChoiceField
from django.forms.widgets import DateTimeInput, HiddenInput
import psycopg2
from settings import PARAMETROS_NOTA1, PARAMETROS_NOTA2, PARAMETROS_NOTA3, PARAMETROS_NOTA4, PARAMETROS_NOTA5, \
    UTILIZA_GRUPOS_ALUMNOS, TIPO_PERIODO_PROPEDEUTICO, NIVEL_MALLA_CERO, TIPO_PERIODO_REGULAR, PROFESORES_GROUP_ID, \
    FORMA_PAGO_RECIBOCAJAINSTITUCION, FORMA_PAGO_NOTA_CREDITO, ALUMNOS_GROUP_ID, SISTEMAS_GROUP_ID, INSCRIPCION_CONDUCCION, \
    PROFE_PRACT_CONDUCCION,ASIGNATURA_PRACTICA_CONDUCCION,CARRERAS_ID_EXCLUIDAS_INEC,FORMA_PAGO_WESTER, ID_TIPO_ESPECIE_REG_NOTA, ESPECIE_JUSTIFICA_FALTA, \
    ESPECIE_JUSTIFICA_FALTA_AU,FORMA_PAGO_DEPOSITO,FORMA_PAGO_TRANSFERENCIA,GRUPO_BOX_ID, COORDINACION_UACED,TIPOSEGMENTO_TEORIA,COORDINACION_UASSS, TIPOSEGMENTO_PRACT
from sga.models import Persona, Canton, Malla, AsignaturaMalla, Nivel, Periodo, Materia, Profesor, Turno, Sexo, \
    Provincia, Carrera, Modalidad, Sesion, Especialidad, Matricula, Inscripcion, SolicitudSecretariaDocente, TipoSangre, \
    NIVELES_TITULACION, Asignatura, TipoArchivo, HistoriaNivelesDeInscripcion, Noticia, PeriodoEvaluacionesIAVQ, \
    TiempoDedicacionDocente, CategorizacionDocente, MotivoBeca, PerfilInscripcion, Discapacidad, Banco, Grupo, \
    TipoPeriodo, Sede, FormaDePago, TipoTarjetaBanco, ProcesadorPagoTarjeta, Aula, CuentaBanco, TipoEspecieValorada, \
    NivelMalla, Raza, EstratoSociocultural, TipoBeca, DIAS_CHOICES, TipoBeneficio, TipoEstado, CodigoEvaluacion, \
    PeriodoEvaluacionesITS, TIPOS_PAGO_NIVEL, NotaCredito, LugarRecaudacion, MONTH_CHOICES, TipoOtroRubro, \
    TipoIncidencia, Parroquia, Donacion, ReciboCajaInstitucion, NotaCreditoInstitucion, TipoMulta, Coordinacion, \
    TablaTarifaIRPersonaNatural, TipoLiquidacion, TipoObservacionInscripcion, Pais, TipoNivelTitulacion, CargoProfesor, \
    EntidadFinancia, TipoEstudioCursa, SubAreaConocimiento, RelacionTrabajo, AusenciaJustificada, Nacionalidad, \
    TipoActividad, DepartamentoActividad, TipoRetencion, TipoVisitasBiblioteca, TipoPersona, GrupoPractica, Practica, \
    TurnoPractica, Vehiculo, ClaseConduccion, SesionPractica, TipoVisitasBox, \
    TipoConsulta, SesionTratamiento, ClaveBox, ParametroEvaluacion, TipoTest, ParametroTest, AreaTest, TipoIngreso, \
    GrupoCurso, DetallePagos, RegistroMedicamento, SuministroBox, TipoMedicamento, Tutoria, Egresado, RolPagoProfesor, \
    RolPago, ProgresoTutoria, Rubro, TipoOficio, TipoSegmento, TipoTestDobe, TipoSuspension, MotivoSuspension, \
    MotivoResolucion, TipoDocumenBeca, TipoPrograma, Programa, Convenio, TipoAnuncio, AsistAsuntoEstudiant, Panel, \
    IncidenciaAdministrativo, GrupoSeminario, OpcionRespuesta, TipoRegistroAspirante, AulaAdministra, \
    TipoNoRegistroAspirante, Colegio, TipoColegio, IpRecaudacion, ConvenioBox, \
    MotivoVisitasBiblioteca, PagoWester, RegistroWester, ConvenioAcademico, User, ConvenioUsuario, MateriaAsignada, \
    CategoriaVehiculo, TipoCombustible, PersonaConduccion, Promocion, TipoCulminacionEstudio, AlternativasBoxExt, \
    EmpresaConvenio, ComisionCongreso, ModalidadPonencia, Vendedor, PagoNivel, TipoDocumentosOficiales, Sector, \
    Departamento, TipoSolicitudSecretariaDocente, RecordAcademico, TipoPonencia, AbreviaturaTitulo, TipoConvenio, \
    ActividadVinculacion, AsistenteDepartamento, MotivoAlcance, TipoEntrega, TipoMaterialDocente, \
    DatosTransfereciaDeposito, ListaFormaDePago, ColorUniforme, ColorZapato, Modulo, TipoAula, EstadoEmpresa, \
    ReferidosInscripcion, AmbitosTutor, elimina_tildes, ProfesorMateria, NivelPagoPracticasDocente, \
    TipoPersonaEmpresaConvenio, ParentescoTipoPersonaEmpresaConvenio, DescuentosporConvenio, EspecieGrupo, \
    VacunasCovid, CoordinacionDepartamento, TipoWebinar, TipoMotivoNotaCredito, TituloExamenCondu, \
    TipoMotivoCierreClases, SupervisorGrupos, EjesEvaluacion, \
    TipoArticulo


from sga.models import Persona, Canton, Malla, AsignaturaMalla, Nivel, Periodo, Materia, Profesor, Turno, Sexo, Provincia, Carrera, Modalidad, Sesion, Especialidad, Matricula, Inscripcion, SolicitudSecretariaDocente, TipoSangre, NIVELES_TITULACION, Asignatura, TipoArchivo, HistoriaNivelesDeInscripcion, Noticia, PeriodoEvaluacionesIAVQ, TiempoDedicacionDocente, CategorizacionDocente, MotivoBeca, PerfilInscripcion, Discapacidad, Banco, Grupo, TipoPeriodo, Sede, FormaDePago, TipoTarjetaBanco, ProcesadorPagoTarjeta, Aula, CuentaBanco, TipoEspecieValorada, NivelMalla, Raza, EstratoSociocultural, TipoBeca, DIAS_CHOICES, TipoBeneficio, TipoEstado, CodigoEvaluacion, PeriodoEvaluacionesITS, TIPOS_PAGO_NIVEL, NotaCredito, LugarRecaudacion, MONTH_CHOICES, TipoOtroRubro, TipoIncidencia, Parroquia, Donacion, ReciboCajaInstitucion, NotaCreditoInstitucion, TipoMulta, Coordinacion, TablaTarifaIRPersonaNatural, TipoLiquidacion, TipoObservacionInscripcion, Pais, TipoNivelTitulacion, CargoProfesor, EntidadFinancia, TipoEstudioCursa, SubAreaConocimiento, RelacionTrabajo, AusenciaJustificada, Nacionalidad, TipoActividad, DepartamentoActividad, TipoRetencion, TipoVisitasBiblioteca, TipoPersona, GrupoPractica, Practica, TurnoPractica, Vehiculo, ClaseConduccion, SesionPractica, TipoVisitasBox, \
    TipoConsulta, SesionTratamiento, ClaveBox , ParametroEvaluacion,TipoTest,ParametroTest,AreaTest,TipoIngreso, GrupoCurso, DetallePagos,RegistroMedicamento, SuministroBox, TipoMedicamento, Tutoria, Egresado, RolPagoProfesor, RolPago, ProgresoTutoria, Rubro,TipoOficio, TipoSegmento, TipoTestDobe, TipoSuspension, MotivoSuspension, MotivoResolucion, TipoDocumenBeca,TipoPrograma,Programa,Convenio,TipoAnuncio,AsistAsuntoEstudiant,Panel,IncidenciaAdministrativo,GrupoSeminario,OpcionRespuesta,TipoRegistroAspirante, AulaAdministra,TipoNoRegistroAspirante, Colegio, TipoColegio, IpRecaudacion,ConvenioBox, \
    MotivoVisitasBiblioteca,PagoWester,RegistroWester, ConvenioAcademico,User, ConvenioUsuario, MateriaAsignada, CategoriaVehiculo, TipoCombustible, PersonaConduccion, Promocion,TipoCulminacionEstudio, AlternativasBoxExt,EmpresaConvenio, \
    ComisionCongreso, ModalidadPonencia, Vendedor,PagoNivel,TipoDocumentosOficiales, Sector,Departamento, TipoSolicitudSecretariaDocente, RecordAcademico, TipoPonencia, AbreviaturaTitulo, TipoConvenio, ActividadVinculacion, AsistenteDepartamento, \
    MotivoAlcance, TipoEntrega, TipoMaterialDocente, DatosTransfereciaDeposito,ListaFormaDePago,ColorUniforme,ColorZapato,Modulo, TipoAula, \
    EstadoEmpresa, ReferidosInscripcion, AmbitosTutor,elimina_tildes,ProfesorMateria, NivelPagoPracticasDocente, TipoPersonaEmpresaConvenio, \
    ParentescoTipoPersonaEmpresaConvenio,DescuentosporConvenio, EspecieGrupo, VacunasCovid, \
    CoordinacionDepartamento, TipoWebinar,TipoMotivoNotaCredito, TituloExamenCondu,TipoMotivoCierreClases, \
    SupervisorGrupos, EjesEvaluacion, ModeloEvaluativo
from core.my_form import ExtFileField, FixedForm, MY_Form
# Pregunta


class PersonaForm(FixedForm):
    date_fields = ['nacimiento']
    tipoanuncio = forms.ModelChoiceField(TipoAnuncio.objects.all(), label='Por cual medio te enteraste del Instituto?',
                                         required=False)
    raza = forms.ModelChoiceField(Raza.objects.all(), label='Etnia', required=False)

    # sectorresid = forms.ModelChoiceField(Sector.objects.all(),label='Sector', required=False)
    class Meta:
        model = Persona
        exclude = ('usuario', 'emailinst', 'reestablecer', 'codigo', 'fecha_res', 'activedirectory', 'cambioclavad',
                   'fechaultimactualizaciondatabook', 'aceptaprotecciondatos', 'fechaceptaprotecciondatos')

    def __init__(self, *args, **kwargs):
        super(PersonaForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.id:
            self.fields['nombres'].widget.attrs['readonly'] = True
            self.fields['apellido1'].widget.attrs['readonly'] = True
            self.fields['apellido2'].widget.attrs['readonly'] = True
            # if instance.cedula:
            #     self.fields['cedula'].widget.attrs['readonly'] = True

    def clean_nombres(self):
        return self.instance.nombres

    def clean_apellido1(self):
        return self.instance.apellido1

    def clean_apellido2(self):
        return self.instance.apellido2


class MallaForm(FixedForm):
    date_fields = ['inicio']

    class Meta:
        model = Malla
        exclude = ('',)


class AsignaturaMallaForm(FixedForm):
    class Meta:
        model = AsignaturaMalla
        exclude = ('',)


class NivelForm(FixedForm):
    date_fields = ['inicio', 'fin', 'fechatopematricula', 'fechatopematriculaex']

    class Meta:
        model = Nivel
        exclude = ('cerrado', 'fechacierre', '')

    def __init__(self, *args, **kargs):
        super(NivelForm, self).__init__(*args, **kargs)

        if 'instance' in kargs:
            self.fields['malla'].queryset = Malla.objects.filter(carrera=kargs['instance'].carrera)
            self.fields['nivelmalla'].queryset = NivelMalla.objects.all().exclude(nombre=NIVEL_MALLA_CERO)
            self.fields['grupo'].queryset = Grupo.objects.filter(carrera=kargs['instance'].carrera).order_by('-nombre')


class NivelPropedeuticoForm(forms.Form):
    carrera = forms.ModelChoiceField(Carrera.objects.all().order_by('nombre'), label='Carrera')
    sede = forms.ModelChoiceField(Sede.objects.filter(solobodega=False).order_by('nombre'), label='Sede')
    sesion = forms.ModelChoiceField(Sesion.objects.all().order_by('nombre'), label='Sesion')
    grupo = forms.ModelChoiceField(Grupo.objects.all().order_by('nombre'), label='Grupo')
    inicio = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha Inicio")
    fin = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha Fin")

    def for_grupo(self, carrera):
        self.fields['grupo'].queryset = Grupo.objects.filter(carrera=carrera).order_by('nombre')


class NoticiaForm(FixedForm):
    date_fields = ['desde', 'hasta']

    class Meta:
        model = Noticia
        exclude = ('publica',)


class NivelFormEdit(FixedForm):
    date_fields = ['inicio', 'fin', 'fechatopematricula', 'fechatopematriculaex']

    class Meta:
        model = Nivel
        exclude = ('malla', 'nivelmalla', 'carrera', 'cerrado', 'fechacierre')

    def for_grupo(self, carrera):
        self.fields['grupo'].queryset = Grupo.objects.filter(carrera=carrera)
        self.fields['periodo'].queryset = Periodo.objects.filter(activo=True).exclude(tipo=TIPO_PERIODO_PROPEDEUTICO)

    def for_nivelacion(self, carrera):
        self.fields['grupo'].queryset = Grupo.objects.filter(carrera=carrera)
        self.fields['periodo'].queryset = Periodo.objects.filter(activo=True).exclude(tipo=2)


class MateriaForm(FixedForm):
    date_fields = ['inicio', 'fin']

    class Meta:
        model = Materia
        exclude = ('nivel', 'cerrado', 'fechacierre', 'aprobada', 'exordinario', 'revision', 'exatrasado', 'grupo',
                   'culminacion_tit', 'sgaonline', 'numper', 'convalida', 'id_moodle_course')

    def for_modelo_evaluativo(self, sede):
        self.fields['modelo_evaluativo'].queryset = ModeloEvaluativo.objects.filter(sedes=sede)


class MateriaFormCext(FixedForm):
    date_fields = ['inicio', 'fin']

    class Meta:
        model = Materia
        exclude = ('nivel', 'cerrado', 'fechacierre', 'rectora', 'aprobada', 'exordinario', 'revision', 'exatrasado')


class AsignaturaForm(FixedForm):
    class Meta:
        model = Asignatura
        exclude = ('',)


class MatriculaMultipleForm(forms.Form):
    nivel = ModelChoiceField(Nivel.objects.filter(periodo__activo=True))
    pago = forms.BooleanField(required=False)
    iece = forms.BooleanField(required=False)


class MatriculaLibreForm(forms.Form):
    inscripcion = forms.CharField(required=True, label="Estudiante")


class MatriculaExtraForm(forms.Form):
    inscripcion = ModelChoiceField(Inscripcion.objects.all().order_by('persona__apellido1'))
    recargo = forms.FloatField(label='Recargo')

    def for_grupo(self, grupo):
        self.fields['inscripcion'].queryset = Inscripcion.objects.filter(
            Q(inscripciongrupo__in=grupo.inscripciongrupo_set.all()),
            Q(Q(suspension=False) | Q(suspension=None))).exclude(matricula__nivel__cerrado=False)


class MatriculaForm(FixedForm):
    inscripcion = ModelChoiceField(Inscripcion.objects.all().order_by('persona__apellido1'))
    tipobeneficio = ModelChoiceField(TipoBeneficio.objects.all(), label="Tipo de Beneficio", required=False)
    motivobeca = ModelChoiceField(MotivoBeca.objects.all(), label="Motivo de Beca", required=False)

    class Meta:
        model = Matricula
        exclude = ('fecha', 'aplazamiento', 'fechaaplaza', 'observacionaplaza',)
        # exclude = ('fecha','becado','tipobeneficio','porcientobeca','motivobeca','tipobeca','observaciones','fechabeca','becaparcial')

    def __init__(self, *args, **kargs):
        super(MatriculaForm, self).__init__(*args, **kargs)

        if 'instance' in kargs:
            if self.instance.inscripcion_id != None:
                self.fields['nivel'].queryset = Nivel.objects.filter(periodo=kargs['periodo'],
                                                                     carrera=self.instance.inscripcion.carrera).order_by(
                    'nivelmalla')
            else:
                self.fields['nivel'].queryset = Nivel.objects.filter(periodo=kargs['periodo']).order_by('nivelmalla')

    def for_grupo(self, grupo):
        # self.fields['inscripcion'].queryset = Inscripcion.objects.filter(Q(inscripciongrupo__in=grupo.inscripciongrupo_set.all(), procesodobe__aprobado=True)|Q(inscripciongrupo__in=grupo.inscripciongrupo_set.all() ,procesodobe=None,persona__usuario__is_active=True)).exclude(matricula__nivel__cerrado=False)
        # self.fields['inscripcion'].queryset = Inscripcion.objects.filter(Q(Q(inscripciongrupo__in=grupo.inscripciongrupo_set.all(), procesodobe__aprobado=True)|Q(inscripciongrupo__in=grupo.inscripciongrupo_set.all() ,procesodobe=None,persona__usuario__is_active=True)),Q(Q(suspension=False)|Q(suspension=None))).exclude(matricula__nivel__cerrado=False)
        # 01-oct-2015 OCastillo proceso doble matricula
        self.fields['inscripcion'].queryset = Inscripcion.objects.filter(
            Q(Q(inscripciongrupo__in=grupo.inscripciongrupo_set.all(), procesodobe__aprobado=True,
                procesodoblematricula__aprobado=True) | Q(inscripciongrupo__in=grupo.inscripciongrupo_set.all(),
                                                          procesodobe=None, persona__usuario__is_active=True) | Q(
                inscripciongrupo__in=grupo.inscripciongrupo_set.all(), procesodoblematricula=None,
                persona__usuario__is_active=True)), Q(Q(suspension=False) | Q(suspension=None))).exclude(
            matricula__nivel__cerrado=False)


class MatriculaEditForm(forms.Form):
    nivel = forms.ModelChoiceField(Nivel.objects.all().order_by('grupo__nombre'))
    pago = forms.BooleanField(label="Pago", required=False)
    iece = forms.BooleanField(label="IECE", required=False)
    becado = forms.BooleanField(label="Becado", required=False)
    tipobeneficio = forms.ModelChoiceField(TipoBeneficio.objects.all(), label="Tipo de Beneficio", required=False)
    porcientobeca = forms.FloatField(label="% de Beca", required=False)
    tipobeca = forms.ModelChoiceField(TipoBeca.objects.all(), label="Tipo de Beca", required=False)
    motivobeca = forms.ModelChoiceField(MotivoBeca.objects.all(), label="Motivo de Beca", required=False)
    observaciones = forms.CharField(label='Observaciones', required=False)

    def for_nivel(self, tipo):
        if tipo == TIPO_PERIODO_PROPEDEUTICO:
            self.fields['nivel'].queryset = Nivel.objects.filter(periodo__tipo=tipo).order_by('grupo__nombre')
        else:
            self.fields['nivel'].queryset = Nivel.objects.all().order_by('nivelmalla__nombre', 'grupo__nombre').exclude(
                periodo__tipo=TIPO_PERIODO_PROPEDEUTICO)


class MatriculaBecaForm(forms.Form):
    becado = forms.BooleanField(label="Becado", required=False)
    tipobeneficio = forms.ModelChoiceField(TipoBeneficio.objects.all(), label="Tipo de Beneficio", required=False)
    porcientobeca = forms.FloatField(label="Porciento de Beca", required=False)
    tipobeca = forms.ModelChoiceField(TipoBeca.objects.all(), label="Tipo de Beca", required=False)
    motivobeca = forms.ModelChoiceField(MotivoBeca.objects.all(), label="Motivo de Beca", required=False)
    fechabeca = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'),
                                label="Fecha Resolucion", required=False)
    observaciones = forms.CharField(widget=forms.Textarea, label='Observaciones', required=False)
    becaparcial = forms.BooleanField(label="Aplica Beca Parcial", required=False)


class MatBecaForm(forms.Form):
    becado = forms.BooleanField(label="Becado", required=False)
    tipobeneficio = forms.ModelChoiceField(TipoBeneficio.objects.all(), label="Tipo de Beneficio", required=False)
    porcientobeca = forms.FloatField(label="Porciento de Beca", required=False)
    tipobeca = forms.ModelChoiceField(TipoBeca.objects.all(), label="Tipo de Beca", required=False)
    motivobeca = forms.ModelChoiceField(MotivoBeca.objects.all(), label="Motivo de Beca", required=False)
    fechabeca = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'),
                                label="Fecha Resolucion", required=False)
    observaciones = forms.CharField(widget=forms.Textarea, label='Observaciones', required=False)


class MateriaModelChoiceField(ModelChoiceField):

    def label_from_instance(self, obj):
        return obj.nombre_completo()


class LeccionGrupoModelChoiceField(ModelChoiceField):

    def label_from_instance(self, obj):
        return "A"


class ClaseForm(forms.Form):
    materia = MateriaModelChoiceField(Materia.objects.all())
    turno = forms.ModelChoiceField(Turno.objects.all())
    aula = forms.ModelChoiceField(Aula.objects.filter(activa=True).exclude(tipo__id=9))
    dia = forms.ChoiceField(choices=DIAS_CHOICES)
    virtual = forms.BooleanField(label='Clase Virtual?', required=False)
    profesormateria = forms.ModelChoiceField(ProfesorMateria.objects.all())

    def for_nivel(self, nivel):
        self.fields['materia'].queryset = Materia.objects.filter(nivel=nivel)
        self.fields['turno'].queryset = Turno.objects.filter(sesion=nivel.sesion)
        self.fields['aula'].queryset = Aula.objects.filter(activa=True).exclude(tipo__id=9).order_by('nombre')

    def for_profesormateria(self, nivel, materia):
        self.fields['profesormateria'].queryset = ProfesorMateria.objects.filter(materia__nivel=nivel,
                                                                                 materia=materia).order_by('desde')


class ClaseNivelCerradoForm(forms.Form):
    materia = MateriaModelChoiceField(Materia.objects.all())
    turno = forms.ModelChoiceField(Turno.objects.all())
    aula = forms.ModelChoiceField(Aula.objects.filter(activa=True, tipo__id=6).order_by('nombre'))
    dia = forms.ChoiceField(choices=DIAS_CHOICES)
    virtual = forms.BooleanField(label='Clase Virtual?', required=False)
    profesormateria = forms.ModelChoiceField(ProfesorMateria.objects.all())

    def for_nivel(self, nivel):
        self.fields['materia'].queryset = Materia.objects.filter(nivel=nivel)
        self.fields['turno'].queryset = Turno.objects.filter(sesion=nivel.sesion)
        self.fields['aula'].queryset = Aula.objects.filter(activa=True, tipo__id=6).order_by('nombre')

    def for_profesormateria(self, nivel, materia):
        self.fields['profesormateria'].queryset = ProfesorMateria.objects.filter(materia__nivel=nivel,
                                                                                 materia=materia).order_by('desde')


class RecordAcademicoForm(forms.Form):
    asignatura = forms.ModelChoiceField(Asignatura.objects.all(), label="Asignatura")
    nota = forms.FloatField(label="Nota", required=True)
    asistencia = forms.FloatField(label="Asistencia", required=True)
    fecha = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha",
                            required=False)
    aprobada = forms.BooleanField(label="Aprobada?", required=False)
    convalidacion = forms.BooleanField(label="Convalidada?", required=False)
    pendiente = forms.BooleanField(label="Pendiente?", required=False)


class HistoricoRecordAcademicoForm(forms.Form):
    asignatura = forms.ModelChoiceField(Asignatura.objects.all(), label="Asignatura")
    nota = forms.FloatField(label="Nota", required=True)
    asistencia = forms.FloatField(label="Asistencia", required=True)
    fecha = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha",
                            required=True)
    aprobada = forms.BooleanField(label="Aprobada?", required=False)
    convalidacion = forms.BooleanField(label="Convalidada?", required=False)
    pendiente = forms.BooleanField(label="Pendiente?", required=False)

    def for_carrera(self, carrera):
        # self.fields['asignatura'].queryset = Asignatura.objects.filter(materia__nivel__carrera = carrera).distinct('asignatura')
        self.fields['asignatura'].queryset = Asignatura.objects.all().exclude(pk=ASIGNATURA_PRACTICA_CONDUCCION)


class HistoriaNivelesDeInscripcionForm(FixedForm):
    date_fields = ['fechaperiodo']

    class Meta:
        model = HistoriaNivelesDeInscripcion
        exclude = ('',)


class ConvalidacionInscripcionForm(forms.Form):
    centro = forms.CharField(label='Institucion', required=False)
    carrera = forms.CharField(label='Carrera', required=False)
    asignatura = forms.CharField(label='Asignatura', required=False)
    anno = forms.CharField(label='Anno de Aprobacion', required=False)
    nota_ant = forms.CharField(label='Calificacion', required=False)
    nota_act = forms.CharField(label='Calificacion Equivalente', required=False)
    observaciones = forms.CharField(widget=forms.Textarea, label='Observaciones', required=False)

    if INSCRIPCION_CONDUCCION:
        ra = forms.BooleanField(label="RA (Record Academico)", required=False)
        exa = forms.BooleanField(label="EXA (Rinde Examen)", required=False)
        nojus = forms.BooleanField(label="NO (No Justifica)", required=False)


class EvaluacionObservacionForm(forms.Form):
    observaciones = forms.CharField(widget=forms.Textarea, label='Adicionar Observacion', required=False)


class InscripcionForm(forms.Form):
    nombres = forms.CharField(max_length=200, label="Nombres (*)")
    apellido1 = forms.CharField(max_length=50, label="1er Apellido (*)")
    apellido2 = forms.CharField(max_length=50, label="2do Apellido", required=False)

    extranjero = forms.BooleanField(label='Extranjero?', required=False)

    cedula = forms.CharField(max_length=13, label=u"Cédula (*)", required=False)
    pasaporte = forms.CharField(max_length=15, label=u"Pasaporte", initial='', required=False)

    # if not INSCRIPCION_CONDUCCION:
    titulobachiller = forms.BooleanField(label='Titulo Bachiller verificado en web autorizada? (*)', required=False)
    titulodoc = ExtFileField(label='Titulo (*)', help_text='Tamano Maximo permitido 4Mb, en formato doc, docx, pdf',
                             ext_whitelist=(".doc", ".docx", ".pdf"), max_upload_size=4194304, required=False)

    doblematricula = forms.BooleanField(label='Se remite a DOBE?', required=False)

    nacionalidad = forms.ModelChoiceField(Nacionalidad.objects.all().order_by('id'), label="Nacionalidad",
                                          required=False)
    # nacionalidad = forms.CharField(max_length=100, required=False, initial='ECUATORIANA')

    provincia = forms.ModelChoiceField(Provincia.objects.order_by('nombre'), label="Provincia de Nacimiento",
                                       required=False)
    canton = forms.ModelChoiceField(Canton.objects.order_by('nombre'), label="Canton de Nacimiento", required=False)
    nacimiento = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'),
                                 label="Fecha Nacimiento (*)", required=False)

    sexo = forms.ModelChoiceField(Sexo.objects, label="Sexo (*)")
    madre = forms.CharField(max_length=100, required=False)
    padre = forms.CharField(max_length=100, required=False)

    direccion = forms.CharField(max_length=100, label=u"Calle Principal  (*)", required=False)
    num_direccion = forms.CharField(max_length=15, label=u"Numero Domicilio", required=False)
    direccion2 = forms.CharField(max_length=100, label=u"Calle Secundaria", required=False)
    sector = forms.CharField(max_length=100, label=u"Sector de Residencia", required=False)
    provinciaresid = forms.ModelChoiceField(Provincia.objects.order_by('nombre'), label="Provincia Residencia (*)",
                                            required=False)
    cantonresid = forms.ModelChoiceField(Canton.objects.order_by('nombre'), label="Canton Residencia (*)",
                                         required=False)
    ciudad = forms.CharField(max_length=50, label=u"Ciudad Residencia (*)", required=False)
    parroquia = forms.ModelChoiceField(Parroquia.objects.order_by('nombre'), label="Parroquia (*)", required=False)
    sectorresid = forms.ModelChoiceField(Sector.objects.order_by('nombre'), label="Sector (*)", required=False)

    telefono = forms.CharField(max_length=100, label=u"Telefonos Moviles (*)", required=False)
    telefono_conv = forms.CharField(max_length=100, label=u"Telefonos Fijos (*)", required=False)
    email = forms.CharField(max_length=240, label="Correo Electronico 1", required=False)
    email1 = forms.CharField(max_length=240, label="Correo Electronico 2", required=False)
    email2 = forms.CharField(max_length=240, label="Correo Electronico 3", required=False)
    # emailinst = forms.CharField(max_length=200, label="Correo Institucional", required=False)

    sangre = forms.ModelChoiceField(TipoSangre.objects.order_by('sangre'), label="Tipo de Sangre", required=False)

    # OCastillo 17-oct-2014 se quitó la fecha y ahora se graba automáticamente
    # fecha = forms.DateField(label=u'Fecha de Inscripción',input_formats=['%d-%m-%Y'],widget=DateTimeInput(format='%d-%m-%Y'))

    if UTILIZA_GRUPOS_ALUMNOS:
        grupo = forms.ModelChoiceField(Grupo.objects.order_by('nombre'), label="Grupo (*)")

    carrera = forms.ModelChoiceField(Carrera.objects, label="Carrera (*)")
    modalidad = forms.ModelChoiceField(Modalidad.objects, label="Modalidad (*)")
    sesion = forms.ModelChoiceField(Sesion.objects, label="Sesion (*)")
    colegio = forms.CharField(max_length=200, required=False)
    estcolegio_id = forms.CharField(label='Colegio Estudiante', required=False)
    especialidad = forms.ModelChoiceField(Especialidad.objects, required=False, label='Especialidad (*)')
    anuncio = forms.ModelChoiceField(TipoAnuncio.objects.filter(activo=True).order_by('descripcion'),
                                     label="Por cual medio te enteraste del Instituto (*)")
    estcolegio = forms.CharField(label='Colegio Estudiante(*)', required=False)
    observacion = forms.CharField(widget=forms.Textarea, label=u'Observación', required=False)

    if INSCRIPCION_CONDUCCION:
        titulo = forms.BooleanField(label="Titulo", required=False)
        acta = forms.BooleanField(label="Acta de Grado", required=False)
        fotos2 = forms.BooleanField(label="Fotos", required=False)
        licencia = forms.BooleanField(label="Licencia Tipo B", required=False)
        copia_cedula = forms.BooleanField(label="Copia Cedula", required=False)
        votacion = forms.BooleanField(label="Copia Papeleta Votacion", required=False)
        carnetsangre = forms.BooleanField(label="Carnet Tipo/Sangre", required=False)
        ex_psicologico = forms.BooleanField(label="Examen Psicologico", required=False)
        val_psicosometrica = forms.BooleanField(label='Valoracion Psicosometrica', required=False)
        val_medica = forms.BooleanField(label='Valoracion Medica', required=False)
        licienciatipoc = forms.BooleanField(label='Licencia Tipo C', required=False)
        originalrecord = forms.BooleanField(label='Original Record Academico', required=False)
        originalcontenido = forms.BooleanField(label='Original Contenido Pragmatico', required=False)
        certificado = forms.BooleanField(label='Certificado Licencia Tipo C', required=False)
        identificador = forms.CharField(label='Archivador', required=False)
        tienediscapacidad = forms.BooleanField(label='Tiene Discapacidad?', required=False)
        sabe_conducir = forms.BooleanField(label='Sabe Conducir?', required=False)
        tiene_licencia = forms.BooleanField(label='Tiene Licencia?', required=False)
        tipo_licencia = forms.CharField(label='Licencia', required=False)
        f_emision = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'),
                                    label=u"Fecha Emisión", required=False)
        puntos_licencia = forms.CharField(label='Puntos Licencia', required=False)
        soporte_ant = ExtFileField(label='Soporte ANT', help_text='Tamano Maximo permitido 500Kb, en formato jpg, png',
                                   ext_whitelist=(".png", ".jpg", ".JPG"), max_upload_size=524288, required=False)


    else:
        titulo = forms.BooleanField(label="Titulo", required=False)
        acta = forms.BooleanField(label="Acta de Grado", required=False)
        cedula2 = forms.BooleanField(label="Copia de Cedula", required=False)
        votacion = forms.BooleanField(label="Copia Papeleta Votacion", required=False)
        partida_nac = forms.BooleanField(label="Partida Nacimiento", required=False)
        partida_nac = forms.BooleanField(label="Partida Nacimiento", required=False)
        actaconv = forms.BooleanField(label="Documento Convalidacion", required=False)
        fotos = forms.BooleanField(label="Fotos", required=False)
        actafirmada = forms.BooleanField(label="Acta Inscripcion Firmada", required=False)
        identificador = forms.CharField(label='Archivador', required=False)
        becamunicipio = forms.BooleanField(label='Beca Municipio', required=False)
        autorizacionbecadobe = forms.BooleanField(label=u'Aprobacion Beca Dobe?', required=False)
        autorizacionbecasencyt = forms.BooleanField(label=u'Aprobacion Beca Senescyt?', required=False)
        aprobacionayudadobe = forms.BooleanField(label=u'Aprobacion Ayuda Dobe?', required=False)
        benemeritocuerpobombero = forms.BooleanField(label=u'Benemerito Cuerpo de Bomberos?', required=False)
        tienediscapacidad = forms.BooleanField(label='Tiene Discapacidad?', required=False)
        sindiscapacidad = forms.BooleanField(label='No tiene Discapacidad?', required=False)
    enviarcorreo = forms.BooleanField(label='Enviar Correo?', required=False)

    foto = ExtFileField(label='Ingresar Foto', help_text='Tamano Maximo permitido 500Kb, en formato jpg, png',
                        ext_whitelist=(".png", ".jpg", ".JPG"), max_upload_size=524288, required=False)
    if not INSCRIPCION_CONDUCCION:
        promocion = forms.ModelChoiceField(Promocion.objects.filter(activo=True).order_by('descripcion'),
                                           label=u"Promoción", required=False)
        descuentoporcent = forms.IntegerField(label='% Descuento', required=False)
        # empresaconvenio = forms.ModelChoiceField(EmpresaConvenio.objects.filter().order_by('nombre'),label="Convenio", required=False)
        empresaconvenio = forms.CharField(label='Convenio', required=False)
        descuentoempresa = forms.ModelChoiceField(DescuentosporConvenio.objects.filter(activo=True).order_by('id'),
                                                  label=u"% Descuento", required=False)
        documentoconvenio = ExtFileField(label='Seleccione Documento',
                                         help_text='Tamano Maximo permitido 4Mb, en formato pdf',
                                         ext_whitelist=(".pdf"), max_upload_size=4194304, required=False)
        espariente = forms.BooleanField(label='Pariente?', required=False)
        pariente = forms.ModelChoiceField(ParentescoTipoPersonaEmpresaConvenio.objects.filter().order_by('descripcion'),
                                          label="Parentesco", required=False)
        tipopersona = forms.ModelChoiceField(TipoPersonaEmpresaConvenio.objects.filter().order_by('descripcion'),
                                             label="Tipo de trabajador", required=False)

    def set_add_mode(self, user):
        if UTILIZA_GRUPOS_ALUMNOS:
            if ConvenioUsuario.objects.filter(usuario=user).exists():
                convenio = ConvenioUsuario.objects.filter(usuario=user).values('convenio')
                self.fields['grupo'].queryset = Grupo.objects.filter(convenio__in=convenio)
            else:
                self.fields['grupo'].queryset = Grupo.objects.filter(abierto=True).order_by('nombre')


class InscripcionGraduadosForm(forms.Form):
    nombres = forms.CharField(max_length=200, label="Nombres (*)")
    apellido1 = forms.CharField(max_length=50, label="1er Apellido (*)")
    apellido2 = forms.CharField(max_length=50, label="2do Apellido", required=False)

    extranjero = forms.BooleanField(label='Extranjero?', required=False)

    cedula = forms.CharField(max_length=13, label=u"Cédula (*)", required=False)
    pasaporte = forms.CharField(max_length=15, label=u"Pasaporte", initial='', required=False)

    # if not INSCRIPCION_CONDUCCION:
    titulobachiller = forms.BooleanField(label='Titulo Bachiller verificado en web autorizada? (*)', required=False)
    titulodoc = ExtFileField(label='Titulo (*)', help_text='Tamano Maximo permitido 4Mb, en formato doc, docx, pdf',
                             ext_whitelist=(".doc", ".docx", ".pdf"), max_upload_size=4194304, required=False)

    doblematricula = forms.BooleanField(label='Se remite a DOBE?', required=False)

    nacionalidad = forms.ModelChoiceField(Nacionalidad.objects.all().order_by('id'), label="Nacionalidad",
                                          required=False)
    # nacionalidad = forms.CharField(max_length=100, required=False, initial='ECUATORIANA')

    provincia = forms.ModelChoiceField(Provincia.objects.order_by('nombre'), label="Provincia de Nacimiento",
                                       required=False)
    canton = forms.ModelChoiceField(Canton.objects.order_by('nombre'), label="Canton de Nacimiento", required=False)
    nacimiento = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'),
                                 label="Fecha Nacimiento (*)", required=False)

    sexo = forms.ModelChoiceField(Sexo.objects, label="Sexo (*)")
    madre = forms.CharField(max_length=100, required=False)
    padre = forms.CharField(max_length=100, required=False)

    direccion = forms.CharField(max_length=100, label=u"Calle Principal", required=False)
    num_direccion = forms.CharField(max_length=15, label=u"Numero Domicilio", required=False)
    direccion2 = forms.CharField(max_length=100, label=u"Calle Secundaria", required=False)
    sector = forms.CharField(max_length=100, label=u"Sector de Residencia", required=False)
    provinciaresid = forms.ModelChoiceField(Provincia.objects.order_by('nombre'), label="Provincia Residencia (*)",
                                            required=False)
    cantonresid = forms.ModelChoiceField(Canton.objects.order_by('nombre'), label="Canton Residencia (*)",
                                         required=False)
    ciudad = forms.CharField(max_length=50, label=u"Ciudad Residencia (*)", required=False)
    parroquia = forms.ModelChoiceField(Parroquia.objects.order_by('nombre'), label="Parroquia (*)", required=False)

    telefono = forms.CharField(max_length=100, label=u"Telefonos Moviles", required=False)
    telefono_conv = forms.CharField(max_length=100, label=u"Telefonos Fijos", required=False)
    email = forms.CharField(max_length=240, label="Correo Electronico 1", required=False)
    email1 = forms.CharField(max_length=240, label="Correo Electronico 2", required=False)
    email2 = forms.CharField(max_length=240, label="Correo Electronico 3", required=False)
    # emailinst = forms.CharField(max_length=200, label="Correo Institucional", required=False)

    sangre = forms.ModelChoiceField(TipoSangre.objects.order_by('sangre'), label="Tipo de Sangre", required=False)


class InscripcionCextForm(forms.Form):
    cedula = forms.CharField(max_length=13, label=u"Cédula")
    nombres = forms.CharField(max_length=200)
    apellido1 = forms.CharField(max_length=50, label="1er Apellido")
    apellido2 = forms.CharField(max_length=50, label="2do Apellido", required=False)
    sexo = forms.ModelChoiceField(Sexo.objects)
    provincia = forms.ModelChoiceField(Provincia.objects.order_by('nombre'), label="Provincia de Nacimiento",
                                       required=False)
    canton = forms.ModelChoiceField(Canton.objects.order_by('nombre'), label="Canton de Nacimiento", required=False)
    direccion = forms.CharField(max_length=100, label=u"Calle Principal", required=False)
    direccion2 = forms.CharField(max_length=100, label=u"Calle Secundaria", required=False)
    sector = forms.CharField(max_length=100, label=u"Sector de Residencia", required=False)
    ciudad = forms.CharField(max_length=50, label=u"Ciudad de Residencia", required=False)
    parroquia = forms.ModelChoiceField(Parroquia.objects.order_by('nombre'), label="Parroquia", required=False)
    nacimiento = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'),
                                 label="Fecha Nacimiento", required=False)
    telefono = forms.CharField(max_length=100, label=u"Telefonos Moviles", required=False)
    telefono_conv = forms.CharField(max_length=100, label=u"Telefonos Fijos", required=False)
    email = forms.CharField(max_length=240, label="Correos Electronicos", required=False)
    sangre = forms.ModelChoiceField(TipoSangre.objects.order_by('sangre'), label="Tipo de Sangre", required=False)


class GraduadoDatosForm(forms.Form):
    nombres = forms.CharField(max_length=200)
    apellido1 = forms.CharField(max_length=50, label="1er Apellido")
    apellido2 = forms.CharField(max_length=50, label="2do Apellido", required=False)

    extranjero = forms.BooleanField(label='Extranjero?', required=False)

    cedula = forms.CharField(max_length=13, label=u"Cédula", required=False)
    pasaporte = forms.CharField(max_length=15, label=u"Pasaporte", initial='', required=False)

    provincia = forms.ModelChoiceField(Provincia.objects.order_by('nombre'), label="Provincia de Nacimiento",
                                       required=False)
    canton = forms.ModelChoiceField(Canton.objects.order_by('nombre'), label="Canton de Nacimiento", required=False)

    nacimiento = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'),
                                 label="Fecha Nacimiento", required=False)

    nacionalidad = forms.ModelChoiceField(Nacionalidad.objects.all().order_by('id'), label="Nacionalidad",
                                          required=False)
    # nacionalidad = forms.CharField(max_length=100, required=False, initial='ECUATORIANA')
    sexo = forms.ModelChoiceField(Sexo.objects)
    madre = forms.CharField(max_length=100, required=False)
    padre = forms.CharField(max_length=100, required=False)

    direccion = forms.CharField(max_length=100, label=u"Calle Principal", required=False)
    num_direccion = forms.CharField(max_length=15, label=u"Numero Domicilio", required=False)
    direccion2 = forms.CharField(max_length=100, label=u"Calle Secundaria", required=False)
    sector = forms.CharField(max_length=100, label=u"Sector de Residencia", required=False)
    ciudad = forms.CharField(max_length=50, label=u"Ciudad de Residencia", required=False)
    parroquia = forms.ModelChoiceField(Parroquia.objects.order_by('nombre'), label="Parroquia", required=False)

    telefono = forms.CharField(max_length=100, label=u"Telefonos Moviles", required=False)
    telefono_conv = forms.CharField(max_length=100, label=u"Telefonos Fijos", required=False)
    email = forms.CharField(max_length=240, label="Correos Electronicos", required=False)
    emailinst = forms.CharField(max_length=200, label="Correo Institucional", required=False)

    sangre = forms.ModelChoiceField(TipoSangre.objects.order_by('sangre'), label="Tipo de Sangre", required=False)


class SolicitudSecretariaDocenteForm(FixedForm):
    class Meta:
        model = SolicitudSecretariaDocente
        exclude = ('fecha', 'hora', 'persona', 'cerrada', 'fechacierre')


# si nuevo form OCU 20-02-2019
class SolicitudSecretariaAlumnosForm(forms.Form):
    tipo = forms.ModelChoiceField(TipoSolicitudSecretariaDocente.objects.filter(activa=True), label="Tipo de Solicitud",
                                  required=False)
    descripcion = forms.CharField(widget=forms.Textarea, label='Descripcion', required=False)
    comprobante = ExtFileField(label='Seleccione Imagen',
                               help_text='Tamano Maximo permitido 2048Kb, en formato jpg, png, jpeg',
                               ext_whitelist=(".png", ".jpg", ".jpeg", ".PNG", ".JPG", ".JPEG"),
                               max_upload_size=2097152, required=False)


# class SolicitudSecretariaAlumnosForm(FixedForm):
#     class Meta:
#         model = SolicitudSecretariaDocente
#         exclude = ('fecha','hora','persona','cerrada','fechacierre','observacion','resolucion','usuario','asignado','group')

class ProfesorForm(forms.Form):
    tutor = forms.BooleanField(label='Es Tutor?', required=False)
    conhorario = forms.BooleanField(label='Tiene Horario?', required=False)
    horainicio = forms.TimeField(label='Desde: ', required=False)
    horafin = forms.TimeField(label='Hasta: ', required=False)
    practicahospital = forms.BooleanField(label='Practica Hospitalaria?', required=False)
    nombres = forms.CharField(max_length=200)
    apellido1 = forms.CharField(max_length=50, label="1er Apellido")
    apellido2 = forms.CharField(max_length=50, label="2do Apellido", required=False)

    extranjero = forms.BooleanField(label='Extranjero?', required=False)

    cedula = forms.CharField(max_length=13, label=u"Cédula", required=False)
    pasaporte = forms.CharField(max_length=15, label=u"Pasaporte", initial='', required=False)

    provincia = forms.ModelChoiceField(Provincia.objects.order_by('nombre'), label="Provincia de Nacimiento",
                                       required=False)
    canton = forms.ModelChoiceField(Canton.objects.order_by('nombre'), label="Canton de Nacimiento", required=False)
    nacimiento = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'),
                                 label="Fecha Nacimiento", required=False)

    nacionalidad = forms.ModelChoiceField(Nacionalidad.objects.all().order_by('id'), label="Nacionalidad",
                                          required=False)
    # nacionalidad = forms.CharField(max_length=100, required=False, initial='ECUATORIANA')

    sexo = forms.ModelChoiceField(Sexo.objects)
    madre = forms.CharField(max_length=100, required=False)
    padre = forms.CharField(max_length=100, required=False)

    direccion = forms.CharField(max_length=100, label=u"Calle Principal", required=False)
    num_direccion = forms.CharField(max_length=15, label=u"Numero Domicilio", required=False)
    direccion2 = forms.CharField(max_length=100, label=u"Calle Secundaria", required=False)
    sector = forms.CharField(max_length=100, label=u"Sector", required=False)
    provinciaresid = forms.ModelChoiceField(Provincia.objects.order_by('nombre'), label="Provincia de Residencia",
                                            required=False)
    cantonresid = forms.ModelChoiceField(Canton.objects.order_by('nombre'), label="Canton de Residencia",
                                         required=False)
    ciudad = forms.CharField(max_length=50, label=u"Ciudad", required=False)
    parroquia = forms.ModelChoiceField(Parroquia.objects.order_by('nombre'), label="Parroquia", required=False)

    telefono = forms.CharField(max_length=100, label=u"Telefonos Moviles", required=False)
    telefono_conv = forms.CharField(max_length=100, label=u"Telefonos Fijos", required=False)
    email = forms.CharField(max_length=240, required=False)

    sangre = forms.ModelChoiceField(TipoSangre.objects.order_by('sangre'), label="Tipo de Sangre", required=False)

    dedicacion = forms.ModelChoiceField(TiempoDedicacionDocente.objects, label=u'Tiempo de Dedicacion', required=False)
    categoria = forms.ModelChoiceField(CategorizacionDocente.objects, label=u'Categorización', required=False)

    fechaingreso = forms.DateField(label=u'Fecha de Ingreso', input_formats=['%d-%m-%Y'],
                                   widget=DateTimeInput(format='%d-%m-%Y'))
    numerocontrato = forms.CharField(max_length=100, label=u"No. Contrato", required=False)
    relaciontrab = forms.ModelChoiceField(RelacionTrabajo.objects, label="Relacion Trabajo", required=False)
    reemplazo = forms.BooleanField(label='Puede Reemplazar?', required=False)

    if INSCRIPCION_CONDUCCION:
        identificador = forms.CharField(label='Archivador', required=False)
    # Discapacidades
    tienediscapacidad = forms.BooleanField(label='Tiene Discapacidad?', required=False)
    tipodiscapacidad = forms.ModelChoiceField(Discapacidad.objects, label="Tipo de Discapacidad", required=False)
    porcientodiscapacidad = forms.FloatField(initial=0, label='% de Discapacidad', required=False)
    carnetdiscapacidad = forms.CharField(label='Carnet Discapacitado', required=False)

    def filtra_instructor(self, ins):
        self.fields['dedicacion'].queryset = TiempoDedicacionDocente.objects.filter(pk=ins)


class HorasProfesorForm(forms.Form):
    # Horas de Dedicacion a Actividades
    anno = forms.IntegerField(label=u'Año')
    horasded = forms.FloatField(initial=0, label='Horas Dedicacion')
    horasinv = forms.FloatField(initial=0, label='Horas Investigacion')
    horasadm = forms.FloatField(initial=0, label='Horas Administrativas')
    horasvin = forms.FloatField(initial=0, label='Horas Vinculacion')
    horasotr = forms.FloatField(initial=0, label='Horas Otras Actividades')
    otrasactividades = forms.CharField(widget=forms.Textarea, label='Otras Actividades', required=False)


class AdministrativosForm(forms.Form):
    nombres = forms.CharField(max_length=200)
    apellido1 = forms.CharField(max_length=50, label="1er Apellido")
    apellido2 = forms.CharField(max_length=50, label="2do Apellido", required=False)

    extranjero = forms.BooleanField(label='Extranjero?', required=False)

    cedula = forms.CharField(max_length=13, label=u"Cédula", required=False)
    pasaporte = forms.CharField(max_length=15, label=u"Pasaporte", initial='', required=False)

    provincia = forms.ModelChoiceField(Provincia.objects.order_by('nombre'), label="Provincia de Nacimiento",
                                       required=False)
    canton = forms.ModelChoiceField(Canton.objects.order_by('nombre'), label="Canton de Nacimiento", required=False)
    nacimiento = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'),
                                 label="Fecha Nacimiento", required=False)

    nacionalidad = forms.ModelChoiceField(Nacionalidad.objects.all().order_by('id'), label="Nacionalidad",
                                          required=False)
    # nacionalidad = forms.CharField(max_length=100, required=False, initial='ECUATORIANA')

    sexo = forms.ModelChoiceField(Sexo.objects)
    madre = forms.CharField(max_length=100, required=False)
    padre = forms.CharField(max_length=100, required=False)

    direccion = forms.CharField(max_length=100, label=u"Calle Principal", required=False)
    num_direccion = forms.CharField(max_length=15, label=u"Numero Domicilio", required=False)
    direccion2 = forms.CharField(max_length=100, label=u"Calle Secundaria", required=False)
    sector = forms.CharField(max_length=100, label=u"Sector", required=False)
    provinciaresid = forms.ModelChoiceField(Provincia.objects.order_by('nombre'), label="Provincia de Residencia",
                                            required=False)
    cantonresid = forms.ModelChoiceField(Canton.objects.order_by('nombre'), label="Canton de Residencia",
                                         required=False)
    ciudad = forms.CharField(max_length=50, label=u"Ciudad", required=False)
    parroquia = forms.ModelChoiceField(Parroquia.objects.order_by('nombre'), label="Parroquia", required=False)

    telefono = forms.CharField(max_length=100, label=u"Telefonos Moviles", required=False)
    telefono_conv = forms.CharField(max_length=100, label=u"Telefonos Fijos", required=False)
    email = forms.CharField(max_length=240, required=False)
    sangre = forms.ModelChoiceField(TipoSangre.objects.order_by('sangre'), label="Tipo de Sangre", required=False)
    # Nuevos datos para matriz sniese
    numerocontrato = forms.CharField(max_length=100, label=u"No. Contrato", required=False)
    tienediscapacidad = forms.BooleanField(label='Tiene Discapacidad?', required=False)
    tipodiscapacidad = forms.ModelChoiceField(Discapacidad.objects, label="Tipo de Discapacidad", required=False)
    porcientodiscapacidad = forms.FloatField(initial=0, label='% de Discapacidad', required=False)
    carnetdiscapacidad = forms.CharField(label='Carnet Discapacitado', required=False)

    grupos = forms.ModelMultipleChoiceField(
        Group.objects.exclude(id__in=[PROFESORES_GROUP_ID, ALUMNOS_GROUP_ID, SISTEMAS_GROUP_ID]).order_by('name'),
        label='Grupos Usuario')


class TitulacionProfesorForm(forms.Form):
    titulo = forms.CharField(label='Titulo')
    pais = forms.ModelChoiceField(Pais.objects, label='Pais')
    nivel = forms.ChoiceField(choices=NIVELES_TITULACION)
    tiponivel = forms.ModelChoiceField(TipoNivelTitulacion.objects, label='Tipo Nivel')
    institucion = forms.CharField(label='Institucion')
    fecha = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha",
                            required=True)
    registro = forms.CharField(label='Registro SENESCYT', required=False)
    codigoprofesional = forms.CharField(label="Codigo Profesional", required=False)
    subarea = forms.ModelChoiceField(SubAreaConocimiento.objects, label='SubArea Conocimiento')
    area = forms.CharField(label='Area Conocimiento', required=False)


class CambioClaveForm(forms.Form):
    anterior = forms.CharField(label='Clave Anterior', widget=forms.PasswordInput)
    nueva = forms.CharField(label='Nueva clave', widget=forms.PasswordInput)
    repetir = forms.CharField(label='Repetir clave', widget=forms.PasswordInput)
    # pregunta = forms.ModelChoiceField(Pregunta.objects.all().order_by('descripcion'), label='Pregunta')
    # respuesta = forms.CharField(label='Respuesta')


class ArchivoSyllabusForm(forms.Form):
    nombre = forms.CharField(label="Nombre", required=True)
    materia = forms.ModelChoiceField(Materia.objects.filter(), label="Materia")
    # archivo = forms.FileField(label='Seleccione Archivo', help_text='max. 42 mb')
    archivo = ExtFileField(label='Seleccione Archivo',
                           help_text='Tamano Maximo permitido 40Mb, en formato doc, docx, xls, xlsx, pdf',
                           ext_whitelist=(".doc", ".docx", ".xls", ".xlsx", ".pdf"), max_upload_size=41943040)

    def for_materia(self, id):
        self.fields['materia'].queryset = Materia.objects.filter(pk=id)


class ArchivoDeberForm(forms.Form):
    nombre = forms.CharField(label="Nombre", required=True)
    puntaje = forms.FloatField(label='Puntos', initial=0.00, required=False)
    fechaentrega = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'),
                                   label=u"Fecha Máxima")
    archivo = ExtFileField(label='Seleccione Archivo',
                           help_text='Tamano Maximo permitido 40Mb, en formato doc, docx, xls, xlsx, pdf, ppt, pptx, rar, zip , odp,DOCX',
                           ext_whitelist=(
                               ".doc", ".docx", ".DOCX", ".xls", ".xlsx", ".pdf", ".ppt", ".pptx", ".zip", ".rar", ".odp"),
                           max_upload_size=41943040)


class NotaIAVQForm(forms.Form):
    p1 = forms.FloatField(label=PARAMETROS_NOTA1, initial=0.00, required=False)
    p2 = forms.FloatField(label=PARAMETROS_NOTA2, initial=0.00, required=False)
    p3 = forms.FloatField(label=PARAMETROS_NOTA3, initial=0.00, required=False)
    p4 = forms.FloatField(label=PARAMETROS_NOTA4, initial=0.00, required=False)
    p5 = forms.FloatField(label=PARAMETROS_NOTA5, initial=0.00, required=False)
    nota = forms.FloatField(label='EVALUACION', initial=0.00, required=False)


class GraduadoForm(forms.Form):
    tesis = forms.CharField(label="Tesis", required=True)
    tematesis = forms.CharField(widget=forms.Textarea, label='Observacion', required=False)
    notatesis = forms.FloatField(label="Nota de Tesis")
    notafinal = forms.FloatField(label="Nota de Grado")
    fechagraduado = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'),
                                    label="Fecha Graduacion")
    registro = forms.CharField(label='Registro Senescyt', max_length=50, required=False)
    archivo = ExtFileField(label='Seleccione Archivo',
                           help_text='Tamano Maximo permitido 40Mb, en formato doc, docx, xls, xlsx, pdf, ppt, pptx, rar, zip , odp',
                           ext_whitelist=(
                               ".doc", ".docx", ".xls", ".xlsx", ".pdf", ".ppt", ".pptx", ".zip", ".rar", ".odp"),
                           max_upload_size=41943040, required=False)


#   inscripcion = ModelChoiceField(Inscripcion.objects.all().order_by('persona__apellido1'))
#
#    date_fields = ['fechagraduado']
#
#    class Meta:
#        model = Graduado


class SeguimientoGraduadoForm(forms.Form):
    ejerce = forms.BooleanField(label='Ejerce la Profesion', required=False)
    empresa = forms.CharField(label="Empresa", max_length=200, required=False)
    cargo = forms.CharField(label="Cargo", max_length=100, required=False)
    ocupacion = forms.CharField(label="Ocupacion", max_length=100, required=False)
    telefono = forms.CharField(max_length=50, label="Telefonos", required=False)
    email = forms.CharField(max_length=100, label="Email Empresa", required=False)
    sueldo = forms.FloatField(label="Salario", required=False)
    observaciones = forms.CharField(widget=forms.Textarea, label='Observaciones', required=False)


#    graduado = ModelChoiceField(Graduado.objects.all().order_by('inscripcion__persona__apellido1'))
#
#    class Meta:
#        model = SeguimientoGraduado

class ObservacionGraduadoForm(forms.Form):
    observaciones = forms.CharField(widget=forms.Textarea, label='Observaciones')
    fechaobs = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'),
                               label="Fecha Observaciones", required=True)


class ObservacionInscripcionForm(forms.Form):
    tipo = forms.ModelChoiceField(TipoObservacionInscripcion.objects, label='Tipo', required=True)
    observaciones = forms.CharField(widget=forms.Textarea, label='Observaciones', required=True)
    activa = forms.BooleanField(required=False)


class ObservacionMatriculaForm(forms.Form):
    observaciones = forms.CharField(widget=forms.Textarea, label='Observaciones', required=True)


class EgresadoForm(forms.Form):
    notaegreso = forms.FloatField(label="Nota de Egreso")
    fechaegreso = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'),
                                  label="Fecha Egreso", required=True)

    # inscripcion = ModelChoiceField(Inscripcion.objects.all().order_by('persona__apellido1'))
    # date_fields = ['fechaegreso']

    # class Meta:
    #    model = Egresado


class BecarioForm(forms.Form):
    porciento = forms.FloatField(label="Porciento")
    tipobeca = forms.ModelChoiceField(TipoBeca.objects.all(), label="Tipo de Beca")
    motivo = forms.CharField(widget=forms.Textarea, label='Motivo', required=False)


class PerfilInscripcionForm(FixedForm):
    # inscripcion = ModelChoiceField(Inscripcion.objects.all().order_by('persona__apellido1'))
    tipodiscapacidad = ModelChoiceField(Discapacidad.objects.all().exclude(id__in=[7, 8]), required=False)
    valoracion = forms.CharField(widget=forms.Textarea, label=u'Valoración', required=False)
    fechavaloracion = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'),
                                      label=u"Fecha Valoración", required=False)
    tutor = forms.CharField(label="Tutor", required=False)
    contacto = forms.CharField(label="Contacto", required=False)
    fechamatricula = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'),
                                     label=u"Fecha Matricula", required=False)
    mediostecnicos = forms.CharField(widget=forms.Textarea, label=u'Medios Técnicos', required=False)
    fecharesumen = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'),
                                   label=u"Emisión Resumen", required=False)
    resumen = ExtFileField(label='Resumen', help_text='Tamano Maximo permitido 4Mb, en formato doc, docx, pdf',
                           ext_whitelist=(".doc", ".docx", ".pdf"), max_upload_size=4194304, required=False)
    fechaemision = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'),
                                   label=u"Emisión Informe", required=False)
    informe = ExtFileField(label='Informe', help_text='Tamano Maximo permitido 4Mb, en formato doc, docx, pdf',
                           ext_whitelist=(".doc", ".docx", ".pdf"), max_upload_size=4194304, required=False)

    class Meta:
        model = PerfilInscripcion
        exclude = ('inscripcion',)


class DobeInscripcionForm(forms.Form):
    raza = forms.ModelChoiceField(Raza.objects.all(), label='Raza', required=False)
    estrato = forms.ModelChoiceField(EstratoSociocultural.objects.all(), label='Estrato Sociocultural', required=False)
    tienediscapacidad = forms.BooleanField(label="Tiene Discapacidad?", required=False)
    tipodiscapacidad = forms.ModelChoiceField(Discapacidad.objects.all().exclude(id__in=[7, 8]),
                                              label="Tipo de Discapacidad", required=False)
    porcientodiscapacidad = forms.FloatField(label='% de Discapacidad', required=False)
    carnetdiscapacidad = forms.CharField(label='Carnet Discapacitado', required=False)


class CargarFotoForm(forms.Form):
    # foto = forms.FileField(label='Seleccione Imagen', help_text='max. 1 mb')
    foto = ExtFileField(label='Seleccione Imagen', help_text='Tamano Maximo permitido 500Kb, en formato jpg, png',
                        ext_whitelist=(".png", ".jpg"), max_upload_size=524288)


class CargarFotoProfForm(forms.Form):
    # OCastillo 06/oct/2014 foto profesional
    fotoprof = ExtFileField(label='Seleccione Imagen', help_text='Tamano Maximo permitido 500Kb, en formato jpg, png',
                            ext_whitelist=(".png", ".jpg"), max_upload_size=524288)


class CargarCVForm(forms.Form):
    # cv = forms.FileField(label='Seleccione Archivo', help_text='max. 2 mb')
    cv = ExtFileField(label='Seleccione Archivo', help_text='Tamano Maximo permitido 2 mb, en formato doc, docx, pdf',
                      ext_whitelist=(".docx", ".doc", ".pdf"), max_upload_size=2097152)


class PeriodoEvaluacionesIAVQForm(FixedForm):
    periodo = ModelChoiceField(Periodo.objects.all().order_by('inicio'))

    date_fields = ['n1desde', 'n1hasta', 'n2desde', 'n2hasta', 'pidesde', 'pihasta', 'sudesde', 'suhasta']

    class Meta:
        model = PeriodoEvaluacionesIAVQ
        exclude = ('',)


class PeriodoEvaluacionesITSForm(FixedForm):
    periodo = ModelChoiceField(Periodo.objects.all().order_by('inicio'))

    date_fields = ['mom1desde', 'mom1hasta', 'mom2desde', 'mom2hasta', 'pfinaldesde', 'pfinalhasta', 'proydesde',
                   'proyhasta', 'sudesde', 'suhasta']

    class Meta:
        model = PeriodoEvaluacionesITS
        exclude = ('',)


class EmpresaInscripcionForm(forms.Form):
    razon = forms.CharField(max_length=200, label="Razon Social", required=False)
    cargo = forms.CharField(max_length=200, label="Cargo", required=False)
    direccion = forms.CharField(max_length=200, label="Direccion", required=False)
    telefono = forms.CharField(max_length=100, label="Telefonos", required=False)
    email = forms.CharField(max_length=200, label="Email", required=False)


class EstudioInscripcionForm(forms.Form):
    colegio = forms.CharField(max_length=200, label="Colegio", required=False)
    titulo = forms.CharField(max_length=200, label="Titulo", required=False)
    incorporacion = forms.CharField(max_length=10, label="Anno de Incorporacion", required=False)
    especialidad = forms.CharField(max_length=100, label="Especialidad", required=False)
    universidad = forms.CharField(max_length=200, label="Universidad", required=False)
    carrera = forms.CharField(max_length=200, label="Carrera", required=False)
    anoestudio = forms.IntegerField(label="Tiempo de Estudio", required=False)
    graduado = forms.BooleanField(label="Graduado?", required=False)


class InscripcionPracticaForm(forms.Form):
    nivelmalla = forms.ModelChoiceField(NivelMalla.objects.filter(
        id__in=AsignaturaMalla.objects.filter(asignatura__nombre__icontains='PREPRO').values('nivelmalla'),
        promediar=True), label="Nivel", required=False)
    horas = forms.IntegerField(label=u"Horas de Prácticas", required=True)
    lugar = forms.CharField(max_length=200, label="Lugar", required=False)
    profesor = forms.ModelChoiceField(Profesor.objects.all(), label="Docente supervisa")
    inicio = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Inicio",
                             required=True)
    fin = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fin",
                          required=True)
    equipamiento = forms.CharField(max_length=200, label="Equipamiento", required=False)
    archivo = ExtFileField(label='Seleccione Archivo',
                           help_text='Tamano Maximo permitido 6Mb, en formato doc, docx, pdf',
                           ext_whitelist=(".doc", ".docx", ".pdf"), max_upload_size=6291456, required=False)
    observaciones = forms.CharField(widget=forms.Textarea, label='Observaciones', required=False)

    def nivel_malla(self, malla):
        self.fields['nivelmalla'].queryset = (NivelMalla.objects.filter(id__in=AsignaturaMalla.objects.filter(
            Q(asignatura__nombre__icontains='LABORALES') | Q(asignatura__nombre__icontains='PREPRO'),
            malla=malla).values('nivelmalla')))


class InscripcionPracticaDistribucionForm(forms.Form):
    # nivelmalla=forms.ModelChoiceField(NivelMalla.objects.filter(id__in=AsignaturaMalla.objects.filter(Q(asignatura__nombre__icontains='LABORALES')|Q(asignatura__nombre__icontains='PREPRO')).values('nivelmalla')), label="Nivel",required=False)
    horas = forms.IntegerField(label=u"Horas Total de Prácticas", required=True)
    lugar = forms.CharField(max_length=200, label="Lugar", required=False)
    profesor = forms.ModelChoiceField(Profesor.objects.all(), label="Docente supervisa")
    inicio = forms.DateField(input_formats=['%Y-%m-%d'], widget=DateTimeInput(format='%d-%m-%Y'), label="Inicio",
                             required=True)
    fin = forms.DateField(input_formats=['%Y-%m-%d'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fin",
                          required=True)
    equipamiento = forms.CharField(max_length=200, label="Equipamiento", required=False)
    archivo = ExtFileField(label='Seleccione Archivo',
                           help_text='Tamano Maximo permitido 6Mb, en formato doc, docx, pdf',
                           ext_whitelist=(".doc", ".docx", ".pdf"), max_upload_size=6291456, required=False)
    observaciones = forms.CharField(widget=forms.Textarea, label='Observaciones', required=False)

    def nivel_malla(self, malla):
        self.fields['nivelmalla'].queryset = (NivelMalla.objects.filter(id__in=AsignaturaMalla.objects.filter(
            Q(asignatura__nombre__icontains='LABORALES') | Q(asignatura__nombre__icontains='PREPRO'),
            malla=malla).values('nivelmalla')))


class PracticaDistribucionHorasForm(forms.Form):
    nivelmalla = forms.ModelChoiceField(NivelMalla.objects.filter(id__in=AsignaturaMalla.objects.filter(
        Q(asignatura__nombre__icontains='LABORALES') | Q(asignatura__nombre__icontains='PREPRO')).values('nivelmalla')),
                                        label="Nivel", required=False)
    horasnivel = forms.IntegerField(label=u"Horas Nivel", required=True)

    def nivel_malla(self, malla):
        # OCastillo 13-03-2023 cambio para tecnologias universitarias de Podologia y Gerontologia
        if not (malla.id == 72 or malla.id == 74):
            self.fields['nivelmalla'].queryset = (NivelMalla.objects.filter(id__in=AsignaturaMalla.objects.filter(
                Q(asignatura__nombre__icontains='LABORALES') | Q(asignatura__nombre__icontains='PREPRO'),
                malla=malla).values('nivelmalla')))
        else:
            self.fields['nivelmalla'].queryset = (NivelMalla.objects.filter(
                id__in=AsignaturaMalla.objects.filter(asignatura__nombre__icontains='TELECLINICA', malla=malla).values(
                    'nivelmalla')))


class HistoricoNotasITBForm(forms.Form):
    n1 = forms.IntegerField(label="Nota 1", required=False)
    cod1 = forms.ModelChoiceField(CodigoEvaluacion.objects, label="Codigo 1")
    n2 = forms.IntegerField(label="Nota 2", required=False)
    cod2 = forms.ModelChoiceField(CodigoEvaluacion.objects, label="Codigo 2")
    n3 = forms.IntegerField(label="Nota 3", required=False)
    cod3 = forms.ModelChoiceField(CodigoEvaluacion.objects, label="Codigo 3")
    n4 = forms.IntegerField(label="Nota 4", required=False)
    cod4 = forms.ModelChoiceField(CodigoEvaluacion.objects, label="Codigo 4")
    n5 = forms.IntegerField(label="Nota 5", required=False)
    total = forms.IntegerField(label="Total", required=False)
    recup = forms.IntegerField(label="Recup.", required=False)
    notafinal = forms.IntegerField(label="Nota Final", required=False)
    estado = forms.ModelChoiceField(TipoEstado.objects, label='Estado')


class DocumentoInscripcionForm(forms.Form):
    tipo = forms.ModelChoiceField(TipoArchivo.objects.all().exclude(pk=6).order_by('nombre'), label="Tipo de Documento")
    # archivo = forms.FileField(label='Seleccione Archivo', help_text='max. 4 mb')
    archivo = ExtFileField(label='Seleccione Archivo',
                           help_text='Tamano Maximo permitido 4Mb, en formato doc, docx, pdf',
                           ext_whitelist=(".doc", ".docx", ".pdf"), max_upload_size=4194304)

    def for_tipoarchivo(self):
        self.fields['tipo'].queryset = TipoArchivo.objects.filter().exclude(id__in=[1, 2, 6, 11, 12, 13]).order_by(
            'nombre')


class PeriodoForm(forms.Form):
    nombre = forms.CharField(max_length=200, label="Nombre", required=True)
    inicio = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Inicio",
                             required=True)
    fin = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fin",
                          required=True)
    tipo = forms.ModelChoiceField(TipoPeriodo.objects.all())


# Se hace un Form (Estudio y Trabajo) para asociarlo a la Inscripcion

class ActividadesInscripcionForm(forms.Form):
    # ESTUDIOS
    colegio = forms.CharField(max_length=200, label="Colegio", required=False)
    titulo = forms.CharField(max_length=200, label="Titulo", required=False)
    incorporacion = forms.CharField(max_length=10, label="Ano Incorporacion", required=False)
    especialidad = forms.CharField(max_length=100, label="Especialidad", required=False)
    universidad = forms.CharField(max_length=200, label="Universidad", required=False)
    carrera = forms.CharField(max_length=200, label="Carrera", required=False)
    anoestudio = forms.IntegerField(label="Anos de Estudio", required=False)
    graduado = forms.BooleanField(label="Graduado?", required=False)

    # TRABAJO
    razon = forms.CharField(max_length=200, label="Razon Social", required=False)
    cargo = forms.CharField(max_length=200, label="Cargo", required=False)
    direccion = forms.CharField(max_length=200, label="Direccion del Trabajo", required=False)
    telefono = forms.CharField(max_length=200, label='Telefono', required=False)
    email = forms.EmailField(label="Email Trabajo", required=False)


class GrupoForm(forms.Form):
    carrera = forms.ModelChoiceField(Carrera.objects, label="Carrera")
    modalidad = forms.ModelChoiceField(Modalidad.objects, label="Modalidad")
    sesion = forms.ModelChoiceField(Sesion.objects, label="Sesion")
    nombre = forms.CharField(max_length=40, label="Nombre")
    sede = forms.ModelChoiceField(Sede.objects.filter(solobodega=False), label="Sede")
    inicio = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha Inicio")
    fin = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha Fin")
    capacidad = forms.IntegerField(label="Capacidad", required=False)
    observaciones = forms.CharField(max_length=200, label="Observaciones", required=False)

    periodo = forms.ModelChoiceField(Periodo.objects.filter(tipo=TIPO_PERIODO_REGULAR, activo=True),
                                     label="Periodo Regular", required=False)
    convenio = forms.ModelChoiceField(ConvenioAcademico.objects.filter(activo=True), label="Convenio", required=False)
    convenioempresa = forms.ModelChoiceField(EmpresaConvenio.objects.filter(estado=True), label="Empresa Convenio",
                                             required=False)
    descuento = forms.BooleanField(label='Aplica Descuento? ', required=False)
    online = forms.BooleanField(label='Online? ', required=False)


class GrupoPropedeuticoForm(forms.Form):
    carrera = forms.ModelChoiceField(Carrera.objects, label="Carrera")
    modalidad = forms.ModelChoiceField(Modalidad.objects, label="Modalidad")
    sesion = forms.ModelChoiceField(Sesion.objects, label="Sesion")
    nombre = forms.CharField(max_length=40, label="Nombre")
    sede = forms.ModelChoiceField(Sede.objects.filter(solobodega=False), label="Sede")
    inicio = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha Inicio")
    fin = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha Fin")
    capacidad = forms.IntegerField(label="Capacidad", required=False)
    observaciones = forms.CharField(max_length=200, label="Observaciones", required=False)

    periodo = forms.ModelChoiceField(Periodo.objects.filter(tipo=TIPO_PERIODO_PROPEDEUTICO, activo=True),
                                     label="Periodo Nivelacion", required=False)
    convenioempresa = forms.ModelChoiceField(EmpresaConvenio.objects.filter(estado=True), label="Empresa Convenio",
                                             required=False)


class GrupoEditForm(forms.Form):
    carrera = forms.ModelChoiceField(Carrera.objects, label="Carrera",required=False)
    nombre = forms.CharField(max_length=40, label="Nombre")
    inicio = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha Inicio")
    fin = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha Fin")
    capacidad = forms.IntegerField(label="Capacidad", required=False)
    observaciones = forms.CharField(max_length=200, label="Observaciones", required=False)
    sede = forms.ModelChoiceField(Sede.objects.filter(solobodega=False), label="Sede", required=True)
    convenioempresa = forms.ModelChoiceField(EmpresaConvenio.objects.filter(estado=True), label="Empresa Convenio",
                                             required=False)
    descuento = forms.BooleanField(label='Aplica Descuento? ', required=False)
    online = forms.BooleanField(label='Online? ', required=False)


class PrecioCarreraGrupoForm(forms.Form):
    precioinscripcion = forms.FloatField(label="Precio de Inscripcion", required=True)
    preciomatricula = forms.FloatField(label="Precio de Matricula", required=True)
    precioperiodo = forms.FloatField(label="Precio del Periodo", required=True)
    cuotas = forms.IntegerField(label="Cantidad de Cuotas", required=True)


class SesionCajaForm(forms.Form):
    fondo = forms.FloatField(label="Fondo Inicial", required=True)
    facturaempieza = forms.IntegerField(label="Factura Inicial", required=True)
    autorizacion = forms.CharField(label="Autorizacion SRI", required=False)


class CierreSesionCajaForm(forms.Form):
    bill100 = forms.IntegerField(label="Billetes de 100", required=False)
    bill50 = forms.IntegerField(label="Billetes de 50", required=False)
    bill20 = forms.IntegerField(label="Billetes de 20", required=False)
    bill10 = forms.IntegerField(label="Billetes de 10", required=False)
    bill5 = forms.IntegerField(label="Billetes de 5", required=False)
    bill2 = forms.IntegerField(label="Billetes de 2", required=False)
    bill1 = forms.IntegerField(label="Billetes de 1", required=False)
    enmonedas1 = forms.FloatField(label="Monedas de 1 Ctv$", required=False)
    enmonedas5 = forms.FloatField(label="Monedas de 5 Ctv$", required=False)
    enmonedas10 = forms.FloatField(label="Monedas de 10 Ctv$", required=False)
    enmonedas25 = forms.FloatField(label="Monedas de 25 Ctv$", required=False)
    enmonedas50 = forms.FloatField(label="Monedas de 50 Ctv$", required=False)
    enmonedas100 = forms.FloatField(label="Monedas de 1 US$", required=False)
    chequesfecha = forms.FloatField(label="Cheques a la fecha", required=False)
    vales = forms.FloatField(label="Vales", required=False)
    referido = forms.FloatField(label="Referido", required=False)
    tarjetas = forms.FloatField(label="Tarjetas", required=False)
    deposito = forms.FloatField(label="Depositos", required=False)
    total = forms.FloatField(label="Total Sistema", required=False)
    totalrecaudado = forms.FloatField(label="Total Recaudado", required=False)
    faltante = forms.FloatField(label="Faltante", required=False)
    sobrante = forms.FloatField(label="Sobrante", required=False)
    observacion = forms.CharField(widget=forms.Textarea, label="Observacion", required=False)


class PagoForm(forms.Form):
    valor = forms.FloatField(label="Valor", required=True)
    factura = forms.IntegerField(label="No. Factura", required=True)
    facturaruc = forms.CharField(max_length=20, label='RUC/Cedula', required=True)
    facturanombre = forms.CharField(max_length=100, label='Nombre', required=True)
    facturadireccion = forms.CharField(max_length=100, label="Direccion", required=True)
    facturatelefono = forms.CharField(max_length=50, label="Telefono", required=True)
    formadepago = forms.ModelChoiceField(FormaDePago.objects.all(), label='Forma de Pago')

    # Efectivo

    # Cheque
    numero = forms.CharField(max_length=50, label='Numero Cheque', required=False)
    bancocheque = forms.ModelChoiceField(Banco.objects.filter(activo=True), label="Banco", required=False)
    fechacobro = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'),
                                 label="Fecha Cobro", required=False)
    emite = forms.CharField(max_length=100, label="Emisor", required=False)

    # Tarjeta
    referencia = forms.CharField(max_length=50, label="Referencia", required=False)
    lote = forms.IntegerField(label="Lote", required=True)
    bancotarjeta = forms.ModelChoiceField(Banco.objects.filter(activo=True), label="Banco", required=False)
    tipo = forms.ModelChoiceField(TipoTarjetaBanco.objects.all(), label="Tipo", required=False)
    poseedor = forms.CharField(max_length=100, label='Tarjetahabiente', required=False)
    procesadorpago = forms.ModelChoiceField(ProcesadorPagoTarjeta.objects.all(), label="Procesador de Pago",
                                            required=False)
    adquiriente = forms.CharField(max_length=150, label='Adquiriente', required=True)

    # Transferencia/Deposito
    referenciatransferencia = forms.CharField(max_length=50, label='Referencia', required=False)
    cuentabanco = forms.ModelChoiceField(CuentaBanco.objects.filter(activo=True), label="Cuenta", required=False)

    # Retencion
    tiporetencion = forms.ModelChoiceField(TipoRetencion.objects.all(), label="Retencion", required=True)
    autorizacion = forms.CharField(max_length=50, label="Autorizacion", required=True)
    numerot = forms.CharField(max_length=50, label="No Retencion", required=True)


class FormaPagoForm(forms.Form):
    valor = forms.FloatField(label="Valor", required=True)
    formadepago = forms.ModelChoiceField(FormaDePago.objects.all(), label='Forma de Pago')

    # Efectivo

    # Cheque
    numero = forms.CharField(max_length=50, label='Numero Cheque', required=False)
    bancocheque = forms.ModelChoiceField(Banco.objects.filter(activo=True), label="Banco", required=False)
    fechacobro = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'),
                                 label="Fecha Cobro", required=False)
    emite = forms.CharField(max_length=100, label="Emisor", required=False)

    # Tarjeta
    # OCastillo 21-11-2022 agregar autorizacion a forma de pago tarjeta
    referencia = forms.CharField(max_length=50, label="Referencia", required=False)
    lote = forms.IntegerField(label="Lote", required=True)
    bancotarjeta = forms.ModelChoiceField(Banco.objects.filter(activo=True), label="Banco", required=False)
    procesadorpago = forms.ModelChoiceField(ProcesadorPagoTarjeta.objects.all(), label="Procesador de Pago",
                                            required=False)
    tipo = forms.ModelChoiceField(TipoTarjetaBanco.objects.filter().exclude(activa=False), label="Tipo", required=False)
    poseedor = forms.CharField(max_length=100, label='Tarjetahabiente', required=False)
    adquiriente = forms.CharField(max_length=150, label='Adquiriente', required=True)
    autorizacion = forms.CharField(max_length=50, label='Autorizacion', required=True)

    # Transferencia/Deposito
    solicitudtr = forms.ModelChoiceField(
        DatosTransfereciaDeposito.objects.filter(solicitud__cerrada=False, solicitud__autorizado=True, disponible=True,
                                                 deposito=False), label='Solicitud')
    solicitudep = forms.ModelChoiceField(
        DatosTransfereciaDeposito.objects.filter(solicitud__cerrada=False, solicitud__autorizado=True, disponible=True,
                                                 deposito=True), label='Solicitud')
    referenciatransferencia = forms.CharField(max_length=50, label='Referencia', required=False)
    cuentabanco = forms.ModelChoiceField(CuentaBanco.objects.filter(activo=True), label="Cuenta", required=False)

    # Nota de Credito
    notacredito = forms.ModelChoiceField(NotaCreditoInstitucion.objects.filter(cancelada=False, anulada=False),
                                         label="Nota de Credito", required=False)

    # Recibos de Caja Institucion
    recibocaja = forms.ModelChoiceField(ReciboCajaInstitucion.objects.all(), label="Recibo de Caja", required=False)

    # Retencion
    tiporetencion = forms.ModelChoiceField(TipoRetencion.objects.all(), label="% Retencion", required=True)
    autorizacion = forms.CharField(max_length=50, label="Autorizacion", required=True)
    numerot = forms.CharField(max_length=50, label="No Retencion", required=True)

    # Wester
    wester = forms.ModelChoiceField(PagoWester.objects.filter().exclude(factura=None), label="Pago Wester",
                                    required=False)

    def para_inscripcion(self, ins, persona):
        formap = FormaDePago.objects.all()
        if ReciboCajaInstitucion.objects.filter(inscripcion=ins, saldo__gt=0, activo=True).exists():
            self.fields['recibocaja'].queryset = ReciboCajaInstitucion.objects.filter(inscripcion=ins, saldo__gt=0,
                                                                                      activo=True)
        else:
            formap = formap.exclude(id=FORMA_PAGO_RECIBOCAJAINSTITUCION)

        if PagoWester.objects.filter(inscripcion=ins, factura=None).exists():
            self.fields['wester'].queryset = PagoWester.objects.filter(inscripcion=ins, factura=None)
        else:
            formap = formap.exclude(id=FORMA_PAGO_WESTER)

        if NotaCreditoInstitucion.objects.filter(beneficiario=ins, cancelada=False, anulada=False).exists():
            self.fields['notacredito'].queryset = NotaCreditoInstitucion.objects.filter(beneficiario=ins,
                                                                                        cancelada=False, anulada=False)
        else:
            formap = formap.exclude(id=FORMA_PAGO_NOTA_CREDITO)

        self.fields['solicitudtr'].queryset = DatosTransfereciaDeposito.objects.filter(
            solicitud__personaasignada=persona, solicitud__persona=ins.persona, solicitud__autorizado=True,
            disponible=True, deposito=False)
        self.fields['solicitudep'].queryset = DatosTransfereciaDeposito.objects.filter(
            solicitud__personaasignada=persona, solicitud__persona=ins.persona, solicitud__autorizado=True,
            disponible=True, deposito=True)

        self.fields['formadepago'].queryset = formap

    def solicitud(self, solicitud):
        if DatosTransfereciaDeposito.objects.filter(id=solicitud).exists():
            datos = DatosTransfereciaDeposito.objects.filter(id=solicitud)[:1].get()
            if datos.deposito:
                formap = FormaDePago.objects.filter(id=FORMA_PAGO_DEPOSITO)
                self.fields['solicitudep'].queryset = DatosTransfereciaDeposito.objects.filter(id=datos.id)
            else:
                formap = FormaDePago.objects.filter(id=FORMA_PAGO_TRANSFERENCIA)
                self.fields['solicitudtr'].queryset = DatosTransfereciaDeposito.objects.filter(id=datos.id)
            self.fields['formadepago'].queryset = formap

    def westercaja(self, pwester):
        if PagoWester.objects.filter(id=pwester).exists():
            # self.fields['wester'].queryset = PagoWester.objects.filter(id=wester)
            self.fields['wester'].queryset = PagoWester.objects.filter(id=pwester)
            formap = FormaDePago.objects.filter(id=FORMA_PAGO_WESTER)
            self.fields['formadepago'].queryset = formap

    def para_fichamedica(self, fich):
        if NotaCreditoInstitucion.objects.filter(fichamedica=fich, cancelada=False, anulada=False).exists():
            self.fields['formadepago'].queryset = FormaDePago.objects.exclude(id=FORMA_PAGO_RECIBOCAJAINSTITUCION)
        else:
            self.fields['formadepago'].queryset = FormaDePago.objects.exclude(
                id=FORMA_PAGO_RECIBOCAJAINSTITUCION).exclude(id=FORMA_PAGO_NOTA_CREDITO).exclude(id=FORMA_PAGO_WESTER)


class EspecieForm(forms.Form):
    tipoespeciee = forms.ModelChoiceField(TipoEspecieValorada.objects.all().order_by('precio'), label='Tipo de Especie')
    facturae = forms.IntegerField(label="No. Factura", required=True)
    facturaruce = forms.CharField(max_length=20, label='RUC/Cedula', required=True)
    facturanombree = forms.CharField(max_length=100, label='Nombre', required=True)
    facturadireccione = forms.CharField(max_length=100, label="Direccion", required=True)
    facturatelefonoe = forms.CharField(max_length=50, label="Telefono", required=True)
    formadepagoe = forms.ModelChoiceField(FormaDePago.objects.all(), label='Forma de Pago')

    # Efectivo

    # Cheque
    numeroe = forms.CharField(max_length=50, label='Numero Cheque', required=False)
    bancochequee = forms.ModelChoiceField(Banco.objects.all(), label="Banco", required=False)
    fechacobroe = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'),
                                  label="Fecha Cobro", required=False)
    emitee = forms.CharField(max_length=100, label="Emisor", required=False)

    # Tarjeta
    referenciae = forms.CharField(max_length=50, label="Referencia", required=False)
    bancotarjetae = forms.ModelChoiceField(Banco.objects.all(), label="Banco", required=False)
    tipoe = forms.ModelChoiceField(TipoTarjetaBanco.objects.all(), label="Tipo", required=False)
    poseedore = forms.CharField(max_length=100, label='Poseedor', required=False)
    procesadorpagoe = forms.ModelChoiceField(ProcesadorPagoTarjeta.objects.all(), label="Procesador de Pago",
                                             required=False)

    # Transferencia/Deposito
    referenciatransferenciae = forms.CharField(max_length=50, label='Referencia', required=False)
    cuentabancoe = forms.ModelChoiceField(CuentaBanco.objects.filter(activo=True), label="Cuenta", required=False)


class PagoNivelForm(forms.Form):
    tipo = forms.ChoiceField(choices=TIPOS_PAGO_NIVEL, label='Tipo')
    fecha = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha",
                            required=False)
    valor = forms.FloatField(label='Valor', required=True)

    def excluir_tipos(self, nivel):
        self.fields['tipo'].choices = tuple(
            [(x, y) for x, y in TIPOS_PAGO_NIVEL if not nivel.pagonivel_set.filter(tipo=x).exists()])


class PagoCalendarioForm(forms.Form):
    tipo = forms.ChoiceField(choices=TIPOS_PAGO_NIVEL, label='Tipo')
    fecha = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha",
                            required=False)
    valor = forms.FloatField(label='Valor', required=True)

    def excluir_tipos(self, periodo):
        self.fields['tipo'].choices = tuple(
            [(x, y) for x, y in TIPOS_PAGO_NIVEL if not periodo.pagocalendario_set.filter(tipo=x).exists()])


class PagoNivelEditForm(forms.Form):
    fecha = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha",
                            required=False)
    modificarvalorcuota = forms.BooleanField(label='Modificar el valor de la Cuota', required=False)
    valor = forms.FloatField(label='Valor', required=True)
    observacion = forms.CharField(max_length=500, label='Observacion', widget=forms.Textarea, required=True)


class PagoCalendarioEditForm(forms.Form):
    fecha = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha",
                            required=False)
    valor = forms.FloatField(label='Valor', required=True)


class FacturaCanceladaForm(forms.Form):
    motivo = forms.CharField(max_length=200, label='Motivo', required=True)


class ChequeProtestadoForm(forms.Form):
    motivo = forms.CharField(max_length=200, label='Motivo', required=True)


class ChequeFechaCobroForm(forms.Form):
    fechacobro = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'),
                                 label="Fecha Cobro", required=True)


class RetiradoMatriculaForm(forms.Form):
    motivo = forms.CharField(max_length=200, label='Motivo', required=True)
    especie = forms.CharField(max_length=200, label='No. Especie', required=True)
    codigoe = forms.CharField(max_length=200, label='Cod Especie', required=True)
    fecha = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha")


class EliminacionMatriculaForm(forms.Form):
    motivo = forms.CharField(max_length=200, label='Motivo', required=True)
    fecha = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha")


class ReintegrarRetiroForm(forms.Form):
    motivo = forms.CharField(max_length=200, label='Motivo', required=True)
    departamento = forms.ModelChoiceField(Departamento.objects.filter().order_by('descripcion'),
                                          label=u'Departamento realizó gestión', required=False)
    persona = forms.CharField(max_length=200, label=u'Persona Realizó Gestión', required=False)
    persona_id = forms.IntegerField(required=False)
    fecha = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha")


class PadreClaveForm(forms.Form):
    nombre = forms.CharField(max_length=200, label='Nombre Completo')
    cedula = forms.CharField(max_length=15, label='Cedula')
    email = forms.CharField(max_length=200, label='Correo')
    fecha = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'),
                            label="Fecha de Solicitud")


class ProfesorMateriaFormAdd(forms.Form):
    enviar = forms.BooleanField(label='Enviar Correo? ', required=False)
    segmento = forms.ModelChoiceField(TipoSegmento.objects.filter(), required=False)
    profesor = forms.ModelChoiceField(Profesor.objects.filter(activo=True).exclude(categoria=PROFE_PRACT_CONDUCCION))
    profesor_aux = forms.ModelChoiceField(
        Profesor.objects.filter(Q(categoria=PROFE_PRACT_CONDUCCION) | Q(reemplazo=True)), required=False,
        label='Auxiliar')
    desde = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Desde",
                            required=False)
    hasta = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Hasta",
                            required=False)
    valor = forms.DecimalField(max_digits=11, decimal_places=2, required=False)

    def for_tipodocente(self, tiposegmento):
        if tiposegmento == TIPOSEGMENTO_TEORIA:
            self.fields['profesor'].queryset = Profesor.objects.filter(activo=True).exclude(practicahospital=True).exclude(categoria=PROFE_PRACT_CONDUCCION).order_by('persona__apellido1', 'persona__apellido2')


class UnirGruposForm(forms.Form):
    fuente = forms.ModelChoiceField(Grupo.objects.filter(cerrado=False).exclude(
        inscripciongrupo__inscripcion__matricula__nivel__cerrado=False).order_by('nombre'), label='Desde')
    destino = forms.ModelChoiceField(Grupo.objects.filter(cerrado=False).order_by('nombre'), label='Destino')


class RubroForm(forms.Form):
    valor = forms.FloatField(label='Valor del Rubro')
    motivo = forms.CharField(label='Motivo', required=True)
    autoriza = forms.CharField(label='Autoriza', required=True)
    # fechavence = forms.DateField(input_formats=['%d-%m-%Y'],widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha Vencimiento", required=False)


class NotaCreditoForm(forms.Form):
    valorinicial = forms.FloatField(label='Valor')
    fecha = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha",
                            required=False)
    motivo = forms.CharField(max_length=200, label='Motivo')


class ReciboCajaInstitucionForm(forms.Form):
    valorinicial = forms.FloatField(label='Valor')
    motivo = forms.CharField(max_length=200, label='Motivo')


class NotaCreditoInstitucionForm(forms.Form):
    numero = forms.CharField(label='Numero')
    valor = forms.FloatField(label='Valor')
    motivo = forms.CharField(max_length=250, label='Motivo')
    motivonc = forms.ModelChoiceField(TipoMotivoNotaCredito.objects.filter(), required=False)
    beneficiario = forms.CharField(label='Beneficiario')


class ValeCajaForm(forms.Form):
    valor = forms.FloatField(label='Valor')
    recibe = forms.CharField(label='Recibe')
    responsable = forms.CharField(label='Autoriza')
    referencia = forms.CharField(label='Referencia', required=False)
    concepto = forms.CharField(widget=forms.Textarea, label='Concepto')


class ReciboCajaForm(forms.Form):
    valor = forms.FloatField(label='Valor')
    persona = forms.CharField(label='Persona')
    concepto = forms.CharField(widget=forms.Textarea, label='Concepto')


class AsignarMateriaGrupoForm(forms.Form):
    nivel = forms.ModelChoiceField(Nivel.objects.filter(cerrado=False).order_by("nivelmalla__nombre", "grupo__nombre"),
                                   label='Escoger Paralelo')


TIPO_EXPORT = (
    (1, 'DBF'),
    (2, 'CSV'),
)

TIPO_EXPORT2 = (
    (1, 'DBF'),
    # (2, 'CSV'),
)

TIPO_EXPORT_MES = (
    (1, 'FACTURAS ANULADAS'),
    (2, 'VENTAS'),
    (3, 'FACTURAS')
)


class DBFForm(forms.Form):
    caja = forms.ModelChoiceField(LugarRecaudacion.objects.order_by('nombre'), label='Caja')
    fecha = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha",
                            required=False)
    formato = forms.ChoiceField(choices=TIPO_EXPORT)


class DBFForm2(forms.Form):
    caja = forms.ModelChoiceField(LugarRecaudacion.objects.order_by('nombre'), label='Caja')
    inicio = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha Inicio",
                             required=False)
    fin = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha Fin",
                          required=False)
    formato = forms.ChoiceField(choices=TIPO_EXPORT2)


class TipoIncidenciaForm(forms.Form):
    tipo = forms.ModelChoiceField(TipoIncidencia.objects.order_by('nombre'))


class ResponderIncidenciaForm(forms.Form):
    solucion = forms.CharField(widget=forms.Textarea, label='Respuesta', required=True)


class DBFMesForm(forms.Form):
    tipoexp = forms.ChoiceField(choices=TIPO_EXPORT_MES)
    anno = forms.IntegerField(label=u"Año")
    mes = forms.ChoiceField(choices=MONTH_CHOICES)


class RolPerfilProfesorForm(forms.Form):
    chlunes = forms.FloatField(label='CxH Lunes')
    chmartes = forms.FloatField(label='CxH Martes')
    chmiercoles = forms.FloatField(label='CxH Miercoles')
    chjueves = forms.FloatField(label='CxH Jueves')
    chviernes = forms.FloatField(label='CxH Viernes')
    chsabado = forms.FloatField(label='CxH Sabado')
    chdomingo = forms.FloatField(label='CxH Domingo')
    esfijo = forms.BooleanField(label='Es fijo?', required=False)
    horassalario = forms.FloatField(label='Horas Salario', required=False)
    salario = forms.FloatField(label='Salario', required=False)
    fechaafiliacion = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'),
                                      label="Fecha Afiliacion", required=False)
    coordinacion = forms.ModelChoiceField(Coordinacion.objects.order_by('nombre'), label='Coordinacion', required=False)
    esadministrativo = forms.BooleanField(label='Es Administrativo?', required=False)

    # Nuevos campos para si es administrativo adicionar cargo
    cargo = forms.ModelChoiceField(CargoProfesor.objects, label='Cargo', required=False)
    iniciocargo = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'),
                                  label="Inicio Cargo", required=False)
    fincargo = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fin Cargo",
                               required=False)
    documentocargo = forms.CharField(label='#Documento', required=False)


class RolPagoForm(forms.Form):
    nombre = forms.CharField(max_length=200)
    inicio = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha Inicio",
                             required=False)
    fin = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha Fin",
                          required=False)
    fechamax = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'),
                               label="Fecha Maxima Clase", required=False)
    fechamaxvin = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'),
                                  label="Fecha Maxima Vinculacion", required=False)
    tablatarifa = forms.ModelChoiceField(TablaTarifaIRPersonaNatural.objects, label='Tabla Tarifa IR')


class MatriculaProxNivelForm(forms.Form):
    niveldestino = forms.ModelChoiceField(Nivel.objects, label='Proximo Nivel')

    def for_carrera(self, nivel):
        self.fields['niveldestino'].queryset = Nivel.objects.filter(carrera=nivel.carrera, cerrado=False,
                                                                    periodo__activo=True).order_by('nivelmalla__nombre',
                                                                                                   'paralelo')


class NivelLibreForm(forms.Form):
    paralelo = forms.CharField(max_length=30, label='Bimestre')
    sesion = forms.ModelChoiceField(Sesion.objects, label='Sesion')
    inicio = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha Inicio",
                             required=True)
    fin = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha Fin",
                          required=True)
    fechatopematricula = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'),
                                         label="Limite Matricula", required=True)


class AdicionarOtroRubroForm(forms.Form):
    tipo = forms.ModelChoiceField(TipoOtroRubro.objects, label='Tipo', required=True)
    valor = forms.FloatField(label='Valor', required=True)
    fecha = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha Vence",
                            required=True)
    descripcion = forms.CharField(max_length=200, label='Descripcion')
    numerorecargo = forms.IntegerField(label='No. de Recargo', required=False)


class SNIESEForm(forms.Form):
    periodo = forms.ModelChoiceField(Periodo.objects, label='Periodo', required=True)


class SNIESEAnnoForm(forms.Form):
    annomatricula = forms.IntegerField(label=u"Año")


class InscripcionSenescytForm(forms.Form):
    fecha = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha",
                            required=True)
    tienebeca = forms.BooleanField(label='Tiene Beca Senescyt', required=False)
    observaciones = forms.CharField(widget=forms.Textarea, label='Observaciones', required=False)


class PrestamoInstitucionalForm(forms.Form):
    persona = forms.ModelChoiceField(Persona.objects.all().order_by('apellido1', 'apellido2', 'nombres'),
                                     label='Persona')
    valor = forms.FloatField(label='Valor')
    cuota = forms.FloatField(label='Cuotas de:')
    motivo = forms.CharField(widget=forms.Textarea, label='Motivo')

    def for_profesor(self):
        self.fields['persona'].queryset = Persona.objects.filter(usuario__groups__in=[PROFESORES_GROUP_ID]).order_by(
            'apellido1', 'apellido2', 'nombres').exclude(profesor__dedicacion__id=PROFE_PRACT_CONDUCCION)


class MultaForm(forms.Form):
    profesor = forms.ModelChoiceField(
        Profesor.objects.filter(activo=True).order_by('persona__apellido1', 'persona__apellido2',
                                                      'persona__nombres').exclude(
            dedicacion__id=PROFE_PRACT_CONDUCCION), label='Profesor')
    valor = forms.FloatField(label='Valor')
    tipo = forms.ModelChoiceField(TipoMulta.objects.all(), label='Tipo')
    motivo = forms.CharField(widget=forms.Textarea, label='Motivo')


class EncuestaForm(forms.Form):
    nombre = forms.CharField()
    fechainicio = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'),
                                  label="Fecha Inicio", required=True)
    fechafin = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha Fin",
                               required=True)
    obligatoria = forms.BooleanField(required=False)
    activa = forms.BooleanField(required=False)
    grupos = forms.ModelMultipleChoiceField(Group.objects.all().order_by('name'))


class DonacionForm(forms.Form):
    valor = forms.FloatField(label='Valor')
    motivo = forms.CharField(widget=forms.Textarea, label='Motivo', required=False)


class DonacionporAplicarForm(forms.Form):
    donaciones = forms.ModelChoiceField(Donacion.objects.all(), label='Donaciones')

    def for_inscripcion(self, inscripcion):
        self.fields['donaciones'].queryset = Donacion.objects.filter(inscripcion=inscripcion, aplicada=False)


class BeneficiarioPlan12Form(forms.Form):
    inscripcion = forms.ModelChoiceField(Inscripcion.objects.all(), label='Beneficiario')
    contrato = forms.CharField()
    inicio = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha Inicio",
                             required=True)
    vencimiento = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'),
                                  label="Fecha Vencimiento", required=True)
    materiastotales = forms.IntegerField(label='Materias')
    materiascursadas = forms.IntegerField(label='Ya Cursadas')
    valorpormateria = forms.FloatField(label='Valor Por Materia')
    valortotal = forms.FloatField(label='Valor Total')

    def __init__(self, *args, **kwargs):
        super(BeneficiarioPlan12Form, self).__init__(*args, **kwargs)
        self.fields['valortotal'].widget.attrs['readonly'] = True


class PersonalInstitucionGPForm(forms.Form):
    vivienda = forms.DecimalField(max_digits=11, decimal_places=2)
    educacion = forms.DecimalField(max_digits=11, decimal_places=2)
    salud = forms.DecimalField(max_digits=11, decimal_places=2)
    vestimenta = forms.DecimalField(max_digits=11, decimal_places=2)
    alimentacion = forms.DecimalField(max_digits=11, decimal_places=2)
    total = forms.DecimalField(max_digits=11, decimal_places=2, required=False)


class ProfesorLiquidacionForm(forms.Form):
    tipo = forms.ModelChoiceField(TipoLiquidacion.objects, label='Tipo')
    salida = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha Salida",
                             required=False)
    observaciones = forms.CharField(widget=forms.Textarea, label='Observaciones')


class DocumentosProfesorForm(forms.Form):
    tipo = forms.ModelChoiceField(TipoArchivo.objects.all().order_by('nombre'), label="Tipo de Documento")
    archivo = ExtFileField(label='Seleccione Archivo',
                           help_text='Tamano Maximo permitido 4Mb, en formato doc, docx, pdf',
                           ext_whitelist=(".doc", ".docx", ".pdf"), max_upload_size=4194304)


class ObservacionAbrirMateriaForm(forms.Form):
    observaciones = forms.CharField(widget=forms.Textarea, label='Observaciones', required=False)


class ProfesorEstudiosCursaForm(forms.Form):
    inicio = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha Inicio")
    tipoestudio = forms.ModelChoiceField(TipoEstudioCursa.objects, label='Tipo Estudio')
    financiado = forms.ModelChoiceField(EntidadFinancia.objects, label='Entidad que financia')


class MateriaRecepcionActaNotasForm(forms.Form):
    entregada = forms.BooleanField(label='Entregada?', required=False)
    codigo = forms.CharField(label='Codigo Reporte', required=False)
    entrega = forms.CharField(label='Persona que entrega', required=False)
    observaciones = forms.CharField(widget=forms.Textarea, label='Observaciones', required=False)
    alcanceentregada = forms.BooleanField(label='Entregada?', required=False)
    observacionesalcance = forms.CharField(widget=forms.Textarea, label='Observaciones', required=False)
    actanivelentregada = forms.BooleanField(label='Entregada ?', required=False)
    actanivelobservaciones = forms.CharField(widget=forms.Textarea, label='Observaciones', required=False)


class FechaBecaForm(forms.Form):
    fecha = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Nueva Fecha")


class AusenciaJustificadaForm(forms.Form):
    # numeroe = forms.CharField(label='Numero Especie')
    # codigoe = forms.CharField(label='Codigo Especie')
    # fechae = forms.DateField(label='Fecha Especie')
    observaciones = forms.CharField(widget=forms.Textarea, label='Observaciones')


class ActividadForm(forms.Form):
    periodo = forms.ModelChoiceField(Periodo.objects.filter(activo=True).order_by('tipo', 'inicio'), label='Periodo')
    nombre = forms.CharField(label=u'Nombre', required=True)
    responsable = forms.CharField(label='Responsable')
    es_auditorio = forms.BooleanField(label='Es Auditorio?', required=False)
    es_aula = forms.BooleanField(label='Es Aula?', required=False)
    lugar = forms.CharField(label='Lugar', required=False)
    auditorio = forms.ModelChoiceField(Aula.objects.filter(tipo__id=9), label='Auditorio', required=False)
    aula = forms.ModelChoiceField(Aula.objects.filter(activa=True).exclude(tipo__id=9), label='Aula', required=False)
    fechainicio = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'),
                                  label=u'Fecha Inicio', required=True)
    horainicio = forms.TimeField(label='Hora Inicio', required=False)
    fechafin = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label=u'Fecha Fin',
                               required=True)
    horafin = forms.TimeField(label='Hora Fin', required=False)
    tipo = forms.ModelChoiceField(TipoActividad.objects.all(), label=u'Tipo Actividad',
                                  widget=forms.Select(attrs={'class': 'imp-50'}))
    lunes = forms.BooleanField(label=u'Lunes', required=False)
    martes = forms.BooleanField(label=u'Martes', required=False)
    miercoles = forms.BooleanField(label=u'Miercoles', required=False)
    jueves = forms.BooleanField(label=u'Jueves', required=False)
    viernes = forms.BooleanField(label=u'Viernes', required=False)
    sabado = forms.BooleanField(label=u'Sabado', required=False)
    domingo = forms.BooleanField(label=u'Domingo', required=False)
    departamento = forms.ModelChoiceField(DepartamentoActividad.objects, label='Departamento')
    archivo = ExtFileField(label='Seleccione Archivo',
                           help_text='Tamano Maximo permitido 40Mb, en formato doc, docx, xls, xlsx, pdf, png , jpg',
                           ext_whitelist=(".doc", ".docx", ".png", "jpg", ".jpeg", ".xls", ".xlsx", ".pdf"),
                           max_upload_size=41943040, required=False)
    adicional = forms.CharField(widget=forms.Textarea(attrs={'maxlength': 500}), label='Informacion Adicional')


class ProcesoDobeForm(forms.Form):
    observacion = forms.CharField(widget=forms.Textarea, label='Observacion')
    aprobado = forms.BooleanField(required=False)


class ProcesoDobleMatriculaForm(forms.Form):
    observacion = forms.CharField(widget=forms.Textarea, label='Observacion')
    aprobado = forms.BooleanField(required=False)


class ActivaInactivaUsuarioForm(forms.Form):
    motivo = forms.CharField(max_length=200, label='Motivo', required=True)


class NotaCreditoInstitucionAnuladaForm(forms.Form):
    motivo = forms.CharField(max_length=200, label='Motivo', required=True)


class VisitaBibliotecaForm(forms.Form):
    sede = forms.ModelChoiceField(Sede.objects.filter(solobodega=False).order_by('nombre'), label="Sede",required=False)
    tipovisitabiblioteca = forms.ModelChoiceField(TipoVisitasBiblioteca.objects.all().order_by('descripcion'),label="Tipo de Servicio")
    tipoarticulo = forms.ModelChoiceField(TipoArticulo.objects.filter(estado=True).order_by('descripcion'),label="Tipo de Articulo")
    tipopersona = forms.ModelChoiceField(TipoPersona.objects.all().order_by('descripcion'), label="Tipo de Persona")
    di = forms.BooleanField(label='Cedula?', required=False)
    cedula = forms.CharField(max_length=10, label=u"Documento de Identificacion", required=False)
    nombres = forms.CharField(max_length=200, label=u"Nombre")
    direccion = forms.CharField(max_length=300, label=u"Direccion", required=False)
    telefono = forms.CharField(max_length=100, label=u"Telefonos", required=False)
    observacion = forms.CharField(max_length=100, label=u'Sugerencia')
    motivovisita = forms.ModelChoiceField(MotivoVisitasBiblioteca.objects.all().order_by('descripcion'),label="Motivo de Visita")


class EstudiantesXDesertarObservacionForm(forms.Form):
    observaciones = forms.CharField(widget=forms.Textarea, label='Observaciones', required=True)


class EstudiantesXDesertarObservacionForm(forms.Form):
    observaciones = forms.CharField(widget=forms.Textarea, label='Observaciones', required=True)


class GrupoPracticaForm(FixedForm):
    date_fields = ['inicio', 'fin']

    class Meta:
        model = GrupoPractica
        exclude = ('cerrado', 'fechacierre')

    def __init__(self, *args, **kargs):
        super(GrupoPracticaForm, self).__init__(*args, **kargs)


class GrupoPracticaFormEdit(FixedForm):
    date_fields = ['inicio', 'fin']

    class Meta:
        model = GrupoPractica
        exclude = ('cerrado', 'fechacierre')

    # def for_grupo(self, carrera):
    #     self.fields['grupo'].queryset = Grupo.objects.filter(carrera=carrera)
    #     self.fields['periodo'].queryset = Periodo.objects.filter(activo=True).exclude(tipo=TIPO_PERIODO_PROPEDEUTICO)

    def for_nivelacion(self, carrera):
        self.fields['grupo'].queryset = Grupo.objects.filter(carrera=carrera)
        self.fields['periodo'].queryset = Periodo.objects.filter(activo=True).exclude(tipo=2)


class PracticaForm(FixedForm):
    date_fields = ['fechainicio', 'fechafin']

    class Meta:
        model = Practica
        exclude = ('grupopracticas',)


# class ClaseConduccionForm(forms.Form):
#     practica = MateriaModelChoiceField(Materia.objects.all())
#     turnopractica = forms.ModelChoiceField(TurnoPractica.objects.all())
#     vehiculo = forms.ModelChoiceField(Vehiculo.objects.all())
#     dia = forms.ChoiceField(choices=DIAS_CHOICES)
#
#     def for_grupopractica(self, grupopractica):
#         self.fields['practica'].queryset = Practica.objects.filter(grupopracticas=grupopractica)
#         self.fields['turnopractica'].queryset = TurnoPractica.objects.filter(sesionpracticas=grupopractica.sesionpracticas)
#         self.fields['dia'].queryset = Vehiculo.objects.all().order_by('codigo')

class ClaseConduccionForm(FixedForm):
    # date_fields = []

    class Meta:
        model = ClaseConduccion
        exclude = ('practica', 'turnopractica', 'dia')

    def for_grupopractica(self, turnopractica, practica):
        self.fields['profesor'].queryset = Profesor.objects.filter(dedicacion__id=PROFE_PRACT_CONDUCCION).exclude(
            claseconduccion__turnopractica=turnopractica, claseconduccion__practica=practica)
        self.fields['vehiculo'].queryset = Vehiculo.objects.all().exclude(claseconduccion__turnopractica=turnopractica,
                                                                          claseconduccion__practica=practica)

    def for_grupopracticaedit(self, turnopractica, practica):
        # p=Profesor.objects.filter(pk=profesor)[:1].get()
        self.fields['profesor'].queryset = Profesor.objects.filter(dedicacion__id=PROFE_PRACT_CONDUCCION).exclude(
            claseconduccion__turnopractica=turnopractica, claseconduccion__practica=practica)

    def for_vehiculo(self, turnopractica, practica):
        self.fields['vehiculo'].queryset = Vehiculo.objects.all().exclude(claseconduccion__turnopractica=turnopractica,
                                                                          claseconduccion__practica=practica)


class AlumnoPracticaForm(forms.Form):
    grupopractica = forms.ModelChoiceField(GrupoPractica.objects.all().order_by('sesionpracticas'), label="Seccion")
    practica = forms.ModelChoiceField(Practica.objects.all().order_by('descripcion'), label="Practica")
    claseconduccion = forms.ModelChoiceField(ClaseConduccion.objects.all().order_by('id'), label="Turno")

    def for_claseconduc(self, periodo):
        self.fields['grupopractica'].queryset = GrupoPractica.objects.filter(periodo=periodo)
        self.fields['practica'].queryset = Practica.objects.filter(grupopracticas__periodo__id=0)
        self.fields['claseconduccion'].queryset = ClaseConduccion.objects.filter(
            practica__grupopracticas__periodo__id=0)

    def for_practica(self, grupo, fecha, periodo):
        self.fields['grupopractica'].queryset = GrupoPractica.objects.filter(periodo=periodo)
        self.fields['practica'].queryset = Practica.objects.filter(grupopracticas=grupo, fechafin__gte=fecha)
        self.fields['claseconduccion'].queryset = ClaseConduccion.objects.filter(
            practica__grupopracticas__periodo__id=0)

    def for_turno(self, practica, grupo, fecha, periodo, sesiondia):
        self.fields['grupopractica'].queryset = GrupoPractica.objects.filter(periodo=periodo)
        self.fields['practica'].queryset = Practica.objects.filter(grupopracticas=grupo, fechafin__gte=fecha)
        self.fields['claseconduccion'].queryset = ClaseConduccion.objects.filter(Q(practica=practica, dia=sesiondia),
                                                                                 alumnopractica__claseconduccion=None)
        # self.fields['vehiculo'].queryset = Vehiculo.objects.all().exclude(claseconduccion__turnopractica  = turnopractica)


class SesionPracticaForm(FixedForm):
    # date_fields = ['comienza','termina']

    class Meta:
        model = SesionPractica
        exclude = ('',)


class TurnoPracticaForm(FixedForm):
    # date_fields = ['comienza','termina']

    class Meta:
        model = TurnoPractica
        exclude = ('',)


class VehiculoForm(forms.Form):
    # OCastillo 15/oct/2014 foto vehiculo
    categoria = forms.ModelChoiceField(CategoriaVehiculo.objects.all().order_by('nombre'), label=u"Categoría",
                                       required=False)
    combustible = forms.ModelChoiceField(TipoCombustible.objects.all().order_by('nombre'), label="Combustible",
                                         required=False)
    valor = forms.CharField(max_length=100, label='Valor', required=False)
    placa = forms.CharField(max_length=100, label='Placa', required=False)
    codigo = forms.CharField(max_length=100, label=u'Código', required=False)
    marca = forms.CharField(max_length=100, label='Marca', required=False)
    modelo = forms.CharField(max_length=100, label='Modelo', required=False)
    color = forms.CharField(max_length=100, label='Color', required=False)
    motor = forms.CharField(max_length=100, label='Motor', required=False)
    chasis = forms.CharField(max_length=100, label='Chasis', required=False)
    anio = forms.IntegerField(label=u'Año', required=False)
    # OCastillo 15/oct/2014 foto vehiculo
    imagen = ExtFileField(label='Seleccione Imagen', help_text='Tamano Maximo permitido 500Kb, en formato jpg, png',
                          ext_whitelist=(".png", ".jpg"), max_upload_size=524288, required=False)


class VisitaBoxForm(forms.Form):
    sede = forms.ModelChoiceField(Sede.objects.all().order_by('nombre'), label="Sede (*)")
    tipovisitabox = forms.ModelChoiceField(TipoVisitasBox.objects.all().order_by('descripcion'),
                                           label="Tipo de Servicio (*)")
    tipoconsulta = forms.ModelChoiceField(TipoConsulta.objects.all().order_by('descripcion'), label="Tipo de Consulta",
                                          required=False)
    consulta = forms.CharField(max_length=200, label="Tipo de Consulta", required=False)
    di = forms.BooleanField(label=u'Cédula?', required=False)
    cedula = forms.CharField(label=u"Identificacion (*)", required=False)
    tipopersona = forms.ModelChoiceField(TipoPersona.objects.all().order_by('descripcion'), label="Tipo Persona",
                                         required=False)
    convenio = forms.ModelChoiceField(ConvenioBox.objects.all(), label='Convenio', required=False)
    nombres = forms.CharField(max_length=200, label="Nombres (*)")
    direccion = forms.CharField(max_length=300, label=u"Direccion", required=False)
    telefono = forms.CharField(max_length=100, label=u"Telefonos", required=False)
    sexo = forms.ModelChoiceField(Sexo.objects.all(), label=u"Sexo", required=False)
    clavebox = forms.ModelChoiceField(ClaveBox.objects.all(), label=u"Clave", required=False)
    alternativa = forms.ModelChoiceField(AlternativasBoxExt.objects.all(), label=u"Alternativa", required=False)
    contratamiento = forms.BooleanField(label='Tratamiento', required=False)
    sesiontratamiento = forms.ModelChoiceField(SesionTratamiento.objects.all().order_by('descripcion'),
                                               label="Tipo de Tratamiento", required=False)
    consesion = forms.BooleanField(label='Sesiones?', required=False)
    descripciontrata = forms.CharField(max_length=100, label=u"Descripcion", required=False)
    numerosesion = forms.IntegerField(label="Numero de Sesiones", required=False)
    sesion = forms.IntegerField(label="Sesion No", required=False)
    costo = forms.BooleanField(label='con costo?', required=False)
    valor = forms.DecimalField(max_digits=11, decimal_places=2, label='Valor', required=False)
    motivo = forms.CharField(widget=forms.Textarea(attrs={'maxlength': 500}), max_length=500,
                             label="Motivo de Consulta (*)")
    observacion = forms.CharField(widget=forms.Textarea(attrs={'maxlength': 500}), label="Observacion (*)")

    def consulta_tipvisita(self, id):
        self.fields['tipovisitabox'].queryset = TipoVisitasBox.objects.filter(sede__id=id)

    def consulta_tip(self, con):
        self.fields['tipoconsulta'].queryset = TipoConsulta.objects.filter(tipovisitabox=con)
        self.fields['sesiontratamiento'].queryset = SesionTratamiento.objects.filter(tipovisitabox=con)

    def consulta_tratamiento(self, con, lista, tipo):
        self.fields['sesiontratamiento'].queryset = SesionTratamiento.objects.filter(visitabox=con,
                                                                                     tipovisitabox=tipo).exclude(
            pk__in=lista)


class AnulaValeForm(forms.Form):
    motivo = forms.CharField(max_length=200, label='Motivo', required=True)
    fecha = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha")


class EditarFacturaForm(forms.Form):
    numero = forms.CharField()
    cliente = forms.CharField()
    ruc = forms.CharField()


# OCastillo modificacion de referencia en Transferencias 11-06-2015
class EditarTransferenciaForm(forms.Form):
    referencia = forms.CharField()
    fecha = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha")
    cuentabanco = forms.CharField(label="Cuenta", required=False)
    cuentabanco_id = forms.CharField(label="Cuenta", required=False)


# OCastillo modificacion de referencia en pago con Tarjetas 15-06-2015
# OCastillo modificacion agregar autorizacion en pago con Tarjetas 21-11-2022
class EditarTarjetaForm(forms.Form):
    banco = forms.CharField(label="Banco", required=False)
    banco_id = forms.CharField(label="Banco", required=False)
    tipotarjeta = forms.CharField(label="Tarjeta", required=False)
    tipotarjeta_id = forms.CharField(label="Tarjeta", required=False)
    referencia = forms.CharField()
    procesador = forms.CharField(label="Procesador", required=False)
    procesador_id = forms.CharField(label="Procesador", required=False)
    lote = forms.IntegerField(label="Lote", required=False)
    autorizacion = forms.CharField(label="Autorizacion", required=False)
    fecha = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha")


# OCastillo modificacion de referencia en pago con Cheques a fecha 23-09-2015
class EditarChequesForm(forms.Form):
    numero = forms.CharField(label="Cheque Numero", required=False)
    banco_id = forms.CharField(label="Banco", required=False)
    banco = forms.CharField(label="Banco", required=False)
    emite = forms.CharField(label="Emite", required=False)
    fechacobro = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'),
                                 label="Fecha Cobro")
    observacion = forms.CharField(max_length=300, label='Observacion', required=False)
    recibido = forms.BooleanField(label="Recibido", required=False)


# PRACTICAS CONDUC
class HistoricoNotasPracticaForm(forms.Form):
    responsable = forms.ModelChoiceField(
        Profesor.objects.filter(activo=True, dedicacion__id=PROFE_PRACT_CONDUCCION).order_by('persona__apellido1'),
        label="Instructor Responsable", required=False)
    evaluador = forms.ModelChoiceField(
        Profesor.objects.filter(activo=True, dedicacion__id=PROFE_PRACT_CONDUCCION).order_by('persona__apellido1'),
        label="Instructor Evaluador", required=False)
    n1 = forms.IntegerField(label="Parcial 1", required=False)
    cod1 = forms.ModelChoiceField(ParametroEvaluacion.objects, label="Codigo 1", required=False)
    n2 = forms.IntegerField(label="Parcial 2", required=False)
    cod2 = forms.ModelChoiceField(ParametroEvaluacion.objects, label="Codigo 2", required=False)
    n3 = forms.IntegerField(label="Parcial 3", required=False)
    cod3 = forms.ModelChoiceField(ParametroEvaluacion.objects, label="Codigo 3", required=False)
    n4 = forms.IntegerField(label="Parcial 4", required=False)
    cod4 = forms.ModelChoiceField(ParametroEvaluacion.objects, label="Codigo 4", required=False)
    n5 = forms.IntegerField(label="Examen", required=False)
    total = forms.IntegerField(label="Total", required=False)
    recup = forms.IntegerField(label="Recup.", required=False)
    notafinal = forms.IntegerField(label="Nota Final", required=False)
    estado = forms.ModelChoiceField(TipoEstado.objects, label='Estado', required=False)


class EditarReciboForm(forms.Form):
    valorinicial = forms.CharField()
    saldo = forms.CharField()
    motivo = forms.CharField(label='Motivo')


class TipoTestForm(forms.Form):
    descripcion = forms.CharField(max_length=300, label="Titulo", required=False)
    descripcioncorta = forms.CharField(max_length=300, label="Descripcion Corta", required=False)
    minutofin = forms.IntegerField(required=False, label="Tiempo de Finalizacion")
    observacion = forms.CharField(required=False, max_length=300, label="Mensaje", widget=forms.Textarea)
    estado = forms.BooleanField(required=False)
    personalidad = forms.BooleanField(required=False)

    class Meta:
        model = TipoTest


class InstruccionTestForm(forms.Form):
    tipotest = forms.ModelChoiceField(TipoTest.objects.all(), label='Test')
    imagen = ExtFileField(required=False, label='Seleccione Imagen',
                          help_text='Tamano Maximo permitido 500Kb, en formato jpg, png,gif,gif',
                          ext_whitelist=(".png", ".jpg", ".gif"), max_upload_size=524288)
    ejemplo = forms.CharField(max_length=1000, label='Ejemplo', required=False, widget=forms.Textarea)
    explicacion = forms.CharField(max_length=1000, label='Explicacion', required=False, widget=forms.Textarea)

    def consulta_tip(self, test):
        self.fields['tipotest'].queryset = TipoTest.objects.filter(pk=test.id)


class EjercicioTestForm(forms.Form):
    # tipotest = forms.ModelChoiceField(TipoTest.objects.all(),label='Test')
    imagen = ExtFileField(required=False, label='Seleccione Imagen',
                          help_text='Tamano Maximo permitido 500Kb, en formato jpg, png',
                          ext_whitelist=(".png", ".jpg", ".gif"), max_upload_size=524288)
    parametrotest = forms.ModelChoiceField(ParametroTest.objects.all(), label='Respuesta', required=False)


class ParametroTestForm(FixedForm):
    class Meta:
        model = ParametroTest
        exclude = ('',)


class AreaTestForm(FixedForm):
    class Meta:
        model = AreaTest
        exclude = ('',)


class PreguntaTestForm(forms.Form):
    orden = forms.IntegerField(label='Numero', required=False)
    pregunta = forms.CharField(max_length=1000, label='Texto', required=False, widget=forms.Textarea)
    tipo = forms.ModelChoiceField(TipoIngreso.objects.all(), label='Tipo', required=False)
    areatest = forms.ModelChoiceField(AreaTest.objects.all().order_by('id'), label='Area', required=False)


class ObservacionTestForm(forms.Form):
    motivo = forms.CharField(max_length=3000, label='Observacion', required=True, widget=forms.Textarea)


class CarreraForm(FixedForm):
    class Meta:
        model = Carrera
        exclude = ('practica')
        exclude = ('',)


class InscripcionCursoForm(forms.Form):
    cedula = forms.CharField(max_length=13, label=u"Cédula", required=False)
    extranjero = forms.BooleanField(label='Extranjero?', required=False)

    pasaporte = forms.CharField(max_length=15, label=u"Pasaporte", initial='', required=False)
    nombres = forms.CharField(max_length=200)
    apellido1 = forms.CharField(max_length=50, label="1er Apellido")
    apellido2 = forms.CharField(max_length=50, label="2do Apellido", required=False)
    curso = forms.ModelChoiceField(
        GrupoCurso.objects.filter(activo=True).exclude(pagoscurso=None).exclude(materiacurso=None).order_by('nombre'))

    nacionalidad = forms.ModelChoiceField(Nacionalidad.objects.all().order_by('id'), label="Nacionalidad",
                                          required=False)
    # nacionalidad = forms.CharField(max_length=100, required=False, initial='ECUATORIANA')
    nacimiento = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'),
                                 label="Fecha Nacimiento", required=False)
    sexo = forms.ModelChoiceField(Sexo.objects)
    telefono = forms.CharField(max_length=100, label=u"Telefonos Moviles", required=False)
    telefono_conv = forms.CharField(max_length=100, label=u"Telefonos Fijos", required=False)
    email = forms.CharField(max_length=240, label="Correos Electronicos", required=False)
    fecha = forms.DateField(label=u'Fecha de Inscripción', input_formats=['%d-%m-%Y'],
                            widget=DateTimeInput(format='%d-%m-%Y'))


class MateriaCursoForm(forms.Form):
    asignatura = forms.ModelChoiceField(Asignatura.objects.all(), label='Asignatura')
    instructor = forms.ModelChoiceField(Profesor.objects.all(), label='Instructor')
    grupo = forms.CharField(max_length=20, label=u"Grupo")
    horas = forms.IntegerField(label='Horas')
    inicio = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha Inicio")
    fin = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha Fin")


class PagoCursoForm(forms.Form):
    nombre = forms.CharField(label='Descripcion')
    valor = forms.FloatField(label='Valor', required=True)
    fechavence = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha")


class GrupoCursoForm(forms.Form):
    nombre = forms.CharField(label='Descripcion')
    numeropagos = forms.IntegerField(label='# Pagos', required=True)
    activo = forms.BooleanField(label="Activo?", required=False)


class AsignarGrupoForm(forms.Form):
    grupo = forms.ModelChoiceField(GrupoCurso.objects.filter(activo=True), label='Curso')

    def verifica_grupo(self, i):
        g = DetallePagos.objects.filter(inscripcion=i).values('grupocurso').distinct('grupocurso')
        self.fields['grupo'].queryset = GrupoCurso.objects.filter(activo=True).exclude(id__in=g).exclude(
            pagoscurso=None).exclude(materiacurso=None)


class AsignarGrupoMasivoForm(forms.Form):
    grupo = forms.ModelChoiceField(GrupoCurso.objects.filter(activo=True), label='Curso')


class MotivoApertura(forms.Form):
    motivo = forms.CharField(max_length=200, label='Motivo', required=True)
    fecha = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha")


class ClaveFacturacionForm(forms.Form):
    anterior = forms.CharField(label='Clave Anterior', widget=forms.PasswordInput)
    nueva = forms.CharField(label='Nueva clave', widget=forms.PasswordInput)
    repetir = forms.CharField(label='Repetir clave', widget=forms.PasswordInput)


class MotivoBaja(forms.Form):
    motivo = forms.CharField(max_length=200, label='Motivo', required=True)
    fecha = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha")


class RegistroMedicamentoForm(FixedForm):
    nombre = forms.ModelChoiceField(SuministroBox.objects.filter(estado=True), required=False)
    presentacion = forms.ModelChoiceField(TipoMedicamento.objects.all().order_by('descripcion'), required=False)
    cantidad = forms.IntegerField(required=True)
    fechavencimiento = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'),
                                       label="Fecha", required=False)
    lote = forms.CharField(max_length=200, required=False)
    motivo = forms.CharField(max_length=300, label='Motivo', required=False, widget=forms.Textarea)
    observacion = forms.CharField(widget=forms.Textarea, label=u'Observación', required=False)

    class Meta:
        model = RegistroMedicamento
        exclude = ('precio_venta',)
        fields = (
            'nombre', 'presentacion', 'bodega', 'lote', 'cantidad', 'costo', 'factura', 'iva', 'motivo', 'observacion',)

    def for_suministro(self):
        self.fields['nombre'].queryset = SuministroBox.objects.filter(estado=True).order_by('descripcion')

    def for_bodega(self, idsede):
        self.fields['bodega'].queryset = Sede.objects.filter(pk=idsede)


class SuministroBoxForm(FixedForm):
    class Meta:
        model = SuministroBox
        exclude = ('',)


class TipoMedicamentoForm(FixedForm):
    class Meta:
        model = TipoMedicamento
        exclude = ('',)


class MedicamentoForm(forms.Form):
    # registro = forms.ModelChoiceField(RegistroMedicamento.objects.filter(cantidad__gte=1).order_by('nombre__descripcion'),required=True)
    registro = forms.CharField(max_length=200, required=True)
    cantidad = forms.IntegerField(required=True)

    def registrobodega(self, bodeg):
        self.fields['registro'].queryset = RegistroMedicamento.objects.filter(bodega__id=bodeg,
                                                                              cantidad__gte=1).order_by(
            'nombre__descripcion')


class TutoriaForm(forms.Form):
    profesor = forms.ModelChoiceField(Profesor.objects.all(), required=False)
    estudiante = forms.CharField(label='Estudiante')
    numtutoria = forms.IntegerField(required=False, label='No Tutoria')
    valor = forms.DecimalField(max_digits=11, decimal_places=2)
    estado = forms.BooleanField(required=False, label='Estado')
    fecha = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha")

    def tutoria(self, id):
        self.fields['profesor'].queryset = Profesor.objects.filter(activo=True, id=id)


class EstudianteTutoriaForm(forms.Form):
    tutoria = forms.ModelChoiceField(Tutoria.objects.filter(estado=True), label='Estudiante')
    progreso = forms.ModelChoiceField(ProgresoTutoria.objects.filter())
    observacion = forms.CharField(widget=forms.Textarea(attrs={'maxlength': 300}), label='Observacion')
    tarea = forms.CharField(widget=forms.Textarea(attrs={'maxlength': 300}), label='Tarea', required=False)
    asistencia = forms.BooleanField(required=False)

    def tutoriaprofe(self, tutor):
        self.fields['tutoria'].queryset = Tutoria.objects.filter(id=tutor)


class PagartutoriaForm(forms.Form):
    rol = forms.ModelChoiceField(RolPago.objects.filter().order_by('-id')[:1], required=True)
    valor = forms.DecimalField(max_digits=11, decimal_places=2)
    contarol = forms.CharField(max_length=20, label='Codigo Rol Contable', required=True)


class ObservacionTutoriaForm(forms.Form):
    observacion = forms.CharField(max_length=300, widget=forms.Textarea, label='Observacion', required=True)


class PagoNotaCreditodevoluForm(forms.Form):
    rubro = forms.ModelChoiceField(Rubro.objects.filter().order_by('fechavence')[:5], label='Rubro', required=True)
    valor = forms.FloatField(label='Valor', required=True)

    def rubros_list(self, lista):
        self.fields['rubro'].queryset = Rubro.objects.filter(id__in=lista).order_by('fechavence')


class CabezNotaCreditoInstitucionForm(forms.Form):
    numero = forms.CharField(label='Numero')
    motivo = forms.CharField(max_length=250, label='Motivo')
    beneficiario = forms.CharField(label='Beneficiario')
    total = forms.FloatField(label='Total')


class TipoOficioForm(FixedForm):
    class Meta:
        model = TipoOficio
        exclude = ('',)


class OficioForm(forms.Form):
    tipo = forms.ModelChoiceField(TipoOficio.objects.all(), label='Tipo')
    numero = forms.CharField(label=u'Número', required=False)
    asunto = forms.CharField(widget=forms.Textarea, label='Observaciones', required=False)
    remitente = forms.CharField(label='Remitente', required=False)
    fecharecepcion = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'),
                                     label=u"Fecha Recepción")
    archivo = ExtFileField(label='Seleccione Archivo',
                           help_text='Tamano Maximo permitido 40Mb, en formato doc, docx, xls, xlsx, pdf',
                           ext_whitelist=(".doc", ".docx", ".xls", ".xlsx", ".pdf"), max_upload_size=41943040,
                           required=False)
    emitido = forms.BooleanField(required=False, label='Emitido?')


class DeberAlumnoForm(forms.Form):
    archivo = ExtFileField(label='Seleccione Archivo',
                           help_text='Tamano Maximo permitido 40Mb, en formato doc, docx, xls, xlsx, pdf, ppt, pptx, rar, zip , odp',
                           ext_whitelist=(
                               ".doc", ".docx", ".xls", ".xlsx", ".pdf", ".ppt", ".pptx", ".zip", ".rar", ".odp"),
                           max_upload_size=41943040)


class TipoVistForm(forms.Form):
    especialidad = forms.ModelChoiceField(TipoVisitasBox.objects.filter(estado=True).exclude(alias=None),
                                          required=False)

    def list_visitabox(self, sede):
        self.fields['especialidad'].queryset = TipoVisitasBox.objects.filter(sede__id=sede, estado=True).order_by(
            'descripcion')


class DescuentoForm(forms.Form):
    motivo = forms.CharField(widget=forms.Textarea, label='Motivo', required=False)
    total = forms.FloatField(label='Total', required=True)


class BecaParcialForm(forms.Form):
    total = forms.FloatField(label='Total', required=True)


class DetalleDescuentoForm(forms.Form):
    rubro = forms.ModelChoiceField(Rubro.objects.filter(cancelado=False).order_by('fechavence')[:5], label='Rubro',
                                   required=True)
    porcentaje = forms.BooleanField(label='Porcentaje?', required=False)
    val = forms.BooleanField(label='Valor?', required=False)
    valor = forms.FloatField(label='Valor', required=True)
    valorporcentaje = forms.FloatField(label='Porcentaje %', required=True)

    def rubros_list(self, lista):
        self.fields['rubro'].queryset = Rubro.objects.filter(id__in=lista).order_by('fechavence')


class DetalleRubrosPagadosForm(forms.Form):
    rubro = forms.ModelChoiceField(Rubro.objects.filter().order_by('fechavence')[:5], label='Rubro', required=True)
    valorrubro = forms.FloatField(label='Valor Rubro', required=True)
    descuento = forms.FloatField(label='Descuento', required=True)
    porcentaje = forms.FloatField(label='Porcentaje %', required=True)

    def rubros_list(self, lista):
        self.fields['rubro'].queryset = Rubro.objects.filter(id__in=lista).order_by('fechavence')


class InscripcionGuarderiaForm(forms.Form):
    tipopersona = forms.ModelChoiceField(TipoPersona.objects.all().exclude(pk=3).exclude(pk=4), label='Tipo Persona')
    inscripcion = forms.CharField(label='Inscripcion', required=False)
    inscripcion_id = forms.CharField(label='Inscripcion', required=False)
    persona = forms.CharField(label='Persona', required=False)
    persona_id = forms.CharField(label='Persona', required=False)
    personaext = forms.CharField(label='Persona', required=False)
    responsable = forms.CharField(label='Responsable', required=False)
    identificacion = forms.CharField(label=u'Identificación Responsable', required=False)
    edadresponsable = forms.CharField(label='Edad Responsable', required=False)
    dirresponsable = forms.CharField(label='Direccion Responsable', required=False)
    telresponsable = forms.CharField(label='Telefono Responsable', required=False)
    email = forms.CharField(label='Email Responsable', required=False)
    numhijos = forms.CharField(label=u'Número Hijos', required=False)


class DetalleInscripcionGuarderiaForm(forms.Form):
    nombre = forms.CharField(label='Nombre', required=False)
    cedula = forms.CharField(label=u'Cédula', required=False)
    peso = forms.CharField(label='Peso', required=False)
    fechanacimiento = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'),
                                      label="Fecha Nacimiento", required=True)
    edad = forms.CharField(label='Edad', required=False)

    lugar = forms.CharField(widget=forms.Textarea, label=u'Lugar Nacimiento', required=False)
    direccion = forms.CharField(widget=forms.Textarea, label=u'Dirección', required=False)
    enfermedades = forms.CharField(widget=forms.Textarea, label='Enfermedades', required=False)
    alergias = forms.CharField(widget=forms.Textarea, label='Alergias', required=False)
    observacion = forms.CharField(widget=forms.Textarea, label=u'Observación', required=False)
    foto = ExtFileField(label='Ingresar Foto', help_text='Tamano Maximo permitido 500Kb, en formato jpg, png',
                        ext_whitelist=(".png", ".jpg", ".JPG"), max_upload_size=524288, required=False)


class RegistroGuarderiaForm(forms.Form):
    horaentrada = forms.TimeField(label='Hora Entrada', required=False)
    horasalida = forms.TimeField(label='Hora Salida', required=False)
    observacion = forms.CharField(widget=forms.Textarea, label=u'Observación', required=False)


class BajaNotaCreditoForm(forms.Form):
    motivo = forms.CharField(max_length=200, label='Motivo', required=True)


class LugarRecaudacionForm(forms.Form):
    nombre = forms.CharField(label='Caja', required=True)
    persona = forms.CharField(label='Responsable', required=True)
    puntoventa = forms.CharField(label='Punto de Venta', required=True)
    direccion = forms.CharField(label=u'Dirección', required=True)
    numerofact = forms.IntegerField(label=u'N°. Factura', required=True)
    numeronotacre = forms.IntegerField(label=u'N°. Nota de Crédito', required=True)
    nuevomodeloreporte = forms.BooleanField(label='Utiliza nuevo modelo Reporte?', required=False)


class TipoTestDobeForm(FixedForm):
    class Meta:
        model = TipoTestDobe
        exclude = ('',)


class AddTipoTestDobeForm(forms.Form):
    nombre = forms.ModelChoiceField(TipoTestDobe.objects.all())


class RecomendacionForm(forms.Form):
    recomendacion = forms.CharField(widget=forms.Textarea, label=u'Recomendación', required=True)


class AddPersonaForm(forms.Form):
    nombre = forms.CharField(label='Persona', required=True)
    nombre_id = forms.CharField()


class ParticipanteActividadForm(forms.Form):
    participante = forms.CharField(label='Participante')


class SuspensionForm(forms.Form):
    tiposuspension = forms.ModelChoiceField(TipoSuspension.objects.all(), required=True, label=u'Tipo Suspesión')
    motivosuspension = forms.ModelChoiceField(MotivoSuspension.objects.all(), required=True, label=u'Motivo')
    observacion = forms.CharField(widget=forms.Textarea, label=u'Observación', required=True)
    fechasus = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha",
                               required=False)


class ResolucionForm(forms.Form):
    motivo = forms.ModelChoiceField(MotivoResolucion.objects.all(), required=False, label=u'Motivo de Resolución')
    inscripcion = forms.CharField(label=u'Inscripción', required=False)
    asunto = forms.CharField(label='Asunto')
    resumen = forms.CharField(widget=forms.Textarea, label='Resumen')
    fecharesolucion = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'),
                                      label="Fecha", required=False)
    numero = forms.CharField(label=u'Número de Oficio', required=False)
    archivo = ExtFileField(label='Seleccione Archivo',
                           help_text='Tamano Maximo permitido 40Mb, en formato doc, docx, xls, xlsx, pdf, ppt, pptx, rar, zip , odp',
                           ext_whitelist=(
                               ".doc", ".docx", ".xls", ".xlsx", ".pdf", ".ppt", ".pptx", ".zip", ".rar", ".odp"),
                           max_upload_size=41943040, required=False)


class ArchivoResolucionForm(forms.Form):
    numero = forms.CharField(label=u'Número de Oficio', required=False)
    archivo = ExtFileField(label='Seleccione Archivo',
                           help_text='Tamano Maximo permitido 40Mb, en formato doc, docx, xls, xlsx, pdf, ppt, pptx, rar, zip , odp',
                           ext_whitelist=(
                               ".doc", ".docx", ".xls", ".xlsx", ".pdf", ".ppt", ".pptx", ".zip", ".rar", ".odp"),
                           max_upload_size=41943040, required=False)


class GrupoSeminarioForm(forms.Form):
    taller = forms.CharField(widget=forms.Textarea, label='Nombre')
    objetivo = forms.CharField(widget=forms.Textarea, label='Objetivo')
    inicio = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Desde",
                             required=False)
    fin = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Hasta",
                          required=False)
    empezardesde = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'),
                                   label=u"Fecha Inscripción", required=False)
    horainicio = forms.CharField(max_length=10, required=False, label='Hora Inicio')
    horafin = forms.CharField(max_length=10, required=False, label='Hora Fin')
    ubicacion = forms.CharField(max_length=300, required=False, label=u'Ubicación')
    libre = forms.BooleanField(label='Libre?', required=False)
    precio = forms.FloatField(label="Precio", required=False)
    capacidad = forms.IntegerField(label='Capacidad')
    carrera = forms.ModelChoiceField(Carrera.objects.filter(), label='Carrera')
    expositor = forms.CharField(label='Expositor')
    procedencia = forms.CharField(label='Procedencia', required=False)


class SolicitudBecaForm(forms.Form):
    motivo = forms.CharField(widget=forms.Textarea(attrs={'maxlength': 400}), max_length=400, label=u'Motivo de Beca',
                             required=False)
    # tipo = forms.ModelChoiceField(TipoDocumenBeca.objects.all(),required=False,label=u'Tipo Documento')
    # archivo = ExtFileField(label='Seleccione Archivo',help_text='Tamano Maximo permitido 40Mb, en formato doc, docx, pdf, png, jpg',ext_whitelist=( ".doc", ".docx", ".pdf",".png",".jpg"),max_upload_size=41943040,required=False)


class SolicitudBecaNuevaForm(forms.Form):
    motivo = forms.CharField(widget=forms.Textarea(attrs={'maxlength': 400}), max_length=400, label=u'Motivo de Beca',
                             required=False)
    tipo = forms.ModelChoiceField(TipoDocumenBeca.objects.all(), required=False, label=u'Tipo Documento')
    archivo = ExtFileField(label='Seleccione Archivo', help_text='Tamano Maximo permitido 40Mb, en formato  pdf ',
                           ext_whitelist=(".doc", ".docx", ".pdf", ".png", ".jpg"), max_upload_size=41943040,
                           required=False)


class ResponSolicBecaForm(forms.Form):
    aprobado = forms.BooleanField(required=False, label='Aprobado?')
    observacion = forms.CharField(label=u'Observacion', widget=forms.Textarea, required=False)


class VinculacionForm(forms.Form):
    # convenio = forms.ModelChoiceField(Convenio.objects.all(),label='Convenio',required=False)
    convenio = forms.CharField(label='Convenio', required=False)
    estadoconv = forms.CharField(label='Estado Convenio', required=False)
    convenio_id = forms.IntegerField(required=False)
    programa = forms.ModelChoiceField(Programa.objects.filter(activo=True), label='Proyecto', required=False)
    tipoprograma = forms.CharField(label='Tipo Programa', required=False)
    inicio = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label='Inicio',
                             required=False)
    fin = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label='Fin',
                          required=False)
    nombre = forms.CharField(label='Actividad', widget=forms.Textarea)
    lugar = forms.CharField(label='Lugar', widget=forms.Textarea)
    lider = forms.CharField(label='Lider', widget=forms.Textarea)
    objetivo = forms.CharField(label='Objetivo', required=False, widget=forms.Textarea)
    carrera = forms.ModelChoiceField(Carrera.objects.filter().exclude(id__in=CARRERAS_ID_EXCLUIDAS_INEC),
                                     label='Carrera')
    archivo = ExtFileField(label='Seleccione Archivo', required=False,
                           help_text='Tamano Maximo permitido 40Mb, en formato doc, docx, xls, xlsx, pdf',
                           ext_whitelist=(".doc", ".docx", ".xls", ".xlsx", ".pdf"), max_upload_size=41943040)


class ParticipanteForm(forms.Form):
    sinarticuladagrupo = forms.BooleanField(label='Articulada?', required=False)
    nivelmalla = forms.ModelChoiceField(NivelMalla.objects.filter(
        id__in=AsignaturaMalla.objects.filter(asignatura__nombre__icontains='PREPRO', malla__nueva_malla=True).values(
            'nivelmalla'), promediar=True), label="Nivel", required=False)
    # nivelmalla=forms.ModelChoiceField(NivelMalla.objects.all(id__in=AsignaturaMalla.objects.filter(asignatura__nombre__icontains='PREPRO').values('nivelmalla'),promediar=True), label="Nivel",required=False)
    grupo = forms.CharField(label='Grupo')
    horas2 = forms.IntegerField(label='Horas')
    #
    # def nivel_malla(self,malla):
    #     self.fields['nivelmalla'].queryset=(NivelMalla.objects.filter(id__in=AsignaturaMalla.objects.filter(asignatura__nombre__icontains='PREPRO',malla=malla).values('nivelmalla'),promediar=True))


class ParticipanteIndForm(forms.Form):
    sinarticulada = forms.BooleanField(label='Articulada?', required=False)
    nivelmallaind = forms.ModelChoiceField(NivelMalla.objects.filter(
        id__in=AsignaturaMalla.objects.filter(asignatura__nombre__icontains='PREPRO', malla__nueva_malla=True).values(
            'nivelmalla'), promediar=True), label="Nivel", required=False)
    inscripcion = forms.CharField(label='Inscripcion')
    horas = forms.IntegerField(label='Horas')

    # def nivel_malla(self,malla):
    #     self.fields['nivelmallaind'].queryset=(NivelMalla.objects.filter(id__in=AsignaturaMalla.objects.filter(asignatura__nombre__icontains='PREPRO',malla=malla).values('nivelmalla'),promediar=True))


class DocenteVincForm(forms.Form):
    persona = forms.CharField(label='Persona')
    horas = forms.IntegerField(label='Horas')
    valor = forms.IntegerField(label='Valor', required=False)
    total = forms.IntegerField(label='Total', required=False)
    fecha = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label='Fecha',
                            required=False)
    informe = ExtFileField(label='Seleccione Archivo',
                           help_text='Tamano Maximo permitido 40Mb, en formato doc, docx, xls, xlsx, pdf, zip, tar, ppt, pptx',
                           ext_whitelist=(".doc", ".docx", ".xls", ".xlsx", ".pdf", ".zip", ".ppt", ".pptx", ".rar"),
                           max_upload_size=41943040, required=False)


class EvidenciaForm(forms.Form):
    nombre = forms.CharField(label='Nombre')
    archivo = ExtFileField(label='Seleccione Archivo',
                           help_text='Tamano Maximo permitido 40Mb, en formato doc, docx, xls, xlsx, pdf, zip, tar, ppt, pptx',
                           ext_whitelist=(".doc", ".docx", ".xls", ".xlsx", ".pdf", ".zip", ".ppt", ".pptx", ".rar"),
                           max_upload_size=41943040)


class ObservacionForm(forms.Form):
    observacion = forms.CharField(widget=forms.Textarea, label='Observacion', required=False)


class KitCongresoForm(forms.Form):
    observacion = forms.CharField(label='Observacion', required=False)


class BeneficiariosForm(forms.Form):
    nombre = forms.CharField(label='Nombres')
    identificacion = forms.CharField(label='Identificacion')
    sexo = forms.ModelChoiceField(Sexo.objects.all(), label='Sexo')
    etnia = forms.ModelChoiceField(Raza.objects.all(), label='Raza')
    procedencia = forms.CharField(label='Procedencia')
    edad = forms.CharField(label='Edad')


class ConvenioForm(forms.Form):
    nombre = forms.CharField(label='Nombre', widget=forms.Textarea)
    institucion = forms.CharField(label=u'Institución', widget=forms.Textarea, required=False)
    tipo = forms.ModelChoiceField(TipoConvenio.objects.filter(), label='Tipo de Convenio')
    objetivo = forms.CharField(label='Objetivo', widget=forms.Textarea, required=False)
    nacional = forms.BooleanField(label='Nacional?', required=False)
    indefinido = forms.BooleanField(label='Indefinido?', required=False)
    inicio = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label='Inicio',
                             required=False)
    fin = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label='Fin',
                          required=False)
    tiempo = forms.CharField(label='Tiempo', required=False)
    contacto = forms.CharField(label='Administrador', required=False)
    contactofono = forms.CharField(label='Telefono Administrador', required=False)
    contactoemail = forms.CharField(label='Email Administrador', required=False)
    # OCastillo 22-06-2023 campos adicionales solicitados por A.Rivera
    representante = forms.CharField(label='Representante Legal', required=False)
    representantetelefono = forms.CharField(label='Telefono Representante', required=False)
    representanteemail = forms.CharField(label='Email Representante', required=False)

    prolonga = forms.CharField(label='Prolonga', required=False)
    canton = forms.CharField(label=u'Cantón', required=False)
    idcanton = forms.CharField(label=u'Cantón', required=False)
    idpais = forms.CharField(label=u'País', required=False)
    pais = forms.CharField(label=u'País', required=False)
    archivo = ExtFileField(label='Seleccione Archivo', required=False,
                           help_text='Tamano Maximo permitido 40Mb, en formato doc, docx, xls, xlsx, pdf',
                           ext_whitelist=(".doc", ".docx", ".xls", ".xlsx", ".pdf"), max_upload_size=41943040)


class ProgramaForm(forms.Form):
    tipo = forms.ModelChoiceField(TipoPrograma.objects.filter(activo=True), label='Nombre de Programa')
    nombre = forms.CharField(label='Nombre Proyecto', widget=forms.Textarea)
    objetivo = forms.CharField(label='Objetivo Proyecto', widget=forms.Textarea, required=False)
    inicio = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label='Inicio',
                             required=False)
    fin = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label='Fin',
                          required=False)
    archivo = ExtFileField(label='Seleccione Archivo', required=False,
                           help_text='Tamano Maximo permitido 40Mb, en formato doc, docx, xls, xlsx, pdf',
                           ext_whitelist=(".doc", ".docx", ".xls", ".xlsx", ".pdf"), max_upload_size=41943040)


class FormaPagoPermForm(forms.Form):
    valorperm = forms.FloatField(label="Valor", required=True)
    formadepagoperm = forms.ModelChoiceField(
        FormaDePago.objects.all().exclude(id=FORMA_PAGO_RECIBOCAJAINSTITUCION).exclude(id=FORMA_PAGO_NOTA_CREDITO),
        label='Forma de Pago')

    # Efectivo

    # Cheque
    numerocheq = forms.CharField(max_length=50, label='Numero Cheque', required=False)
    bancochequeperm = forms.ModelChoiceField(Banco.objects.all(), label="Banco", required=False)
    fechacobroperm = forms.DateField(input_formats=['%Y-%m-%d'], widget=DateTimeInput(format='%Y-%m-%d'),
                                     label="Fecha Cobro", required=False)
    emiteperm = forms.CharField(max_length=100, label="Emisor", required=False)

    # Tarjeta
    referenciaperm = forms.CharField(max_length=50, label="Referencia", required=False)
    bancotarjetaperm = forms.ModelChoiceField(Banco.objects.all(), label="Banco", required=False)
    tipoperm = forms.ModelChoiceField(TipoTarjetaBanco.objects.all(), label="Tipo", required=False)
    poseedorperm = forms.CharField(max_length=100, label='Poseedor', required=False)
    procesadorpagoperm = forms.ModelChoiceField(ProcesadorPagoTarjeta.objects.all(), label="Procesador de Pago",
                                                required=False)

    # Transferencia/Deposito
    referenciatransferenciaperm = forms.CharField(max_length=50, label='Referencia', required=False)
    cuentabancoperm = forms.ModelChoiceField(CuentaBanco.objects.filter(activo=True), label="Cuenta", required=False)


class TituloForm(forms.Form):
    titulo = forms.CharField(label='Titulo')


class AsignaAsuntoEstudiantForm(forms.Form):
    asistente = forms.ModelChoiceField(AsistAsuntoEstudiant.objects.filter(estado=True))


class AsistAsuntoEstudiantForm(FixedForm):
    asistente = forms.CharField(label=u'Asistente', required=False)
    telefono = forms.CharField(label=u'Telefono', required=False)
    fecha = forms.DateField(input_formats=['%Y-%m-%d'], widget=DateTimeInput(format='%Y-%m-%d'), label='Fecha',
                            required=False)
    puedereasignar = forms.BooleanField(required=False, label='Puede Reasignar?')

    class Meta:
        model = AsistAsuntoEstudiant
        exclude = ('',)


class IncidenciaAsuntoEstudiantilForm(FixedForm):
    incidencia = forms.CharField(label='Incidencia', widget=forms.Textarea, required=False)
    observacion = forms.CharField(label='Responder Incidencia', widget=forms.Textarea, required=False)
    resolucion = forms.CharField(label='Resolucion', widget=forms.Textarea, required=False)

    class Meta:
        model = IncidenciaAdministrativo
        exclude = ('usuario', 'finalizado', 'usuariofinali', 'fecha', 'fechafinaliza', 'asignado')


class PanelForm(forms.Form):
    nombre = forms.CharField(widget=forms.Textarea, label='Nombre')
    fecha = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha",
                            required=False)
    horainicio = forms.CharField(max_length=10, required=False, label='Hora Inicio')
    horafin = forms.CharField(max_length=10, required=False, label='Hora Fin')
    capacidad = forms.IntegerField(label='Capacidad')


class AdicionarPanelForm(forms.Form):
    panel = forms.ModelChoiceField(Panel.objects.all(), label='Panel')


class CarrerasEstadForm(forms.Form):
    carrera = forms.CharField(label='Carrera')
    detalle = forms.BooleanField(required=False, label='Detallado?')


class ReestablecerClaveForm(forms.Form):
    nueva = forms.CharField(label='Nueva clave', widget=forms.PasswordInput)
    repetir = forms.CharField(label='Repetir clave', widget=forms.PasswordInput)


class PrecongresoForm(forms.Form):
    precongreso = forms.ModelChoiceField(GrupoSeminario.objects.filter(activo=True))


class CroquisForm(forms.Form):
    croquis = ExtFileField(label='Seleccione Archivo',
                           help_text='Tamano Maximo permitido 40Mb, en formato doc, docx, pdf, png, jpg',
                           ext_whitelist=(".doc", ".docx", ".pdf", ".png", ".jpg"), max_upload_size=41943040,
                           required=False)


class SyllabusForm(forms.Form):
    archivo = ExtFileField(label='Seleccione Archivo',
                           help_text='Tamano Maximo permitido 40Mb, en formato doc, docx, pdf, png, jpg',
                           ext_whitelist=(".doc", ".docx", ".pdf", ".png", ".jpg"), max_upload_size=41943040,
                           required=False)


class CapituloForm(forms.Form):
    numero = forms.CharField(label=u'Número')
    orden = forms.IntegerField(label='Orden')
    nombre = forms.CharField(label='Nombre')
    contenido = forms.CharField(widget=forms.Textarea, label='Contenido', required=False)
    tiene_detalle = forms.BooleanField(label='Tiene Contenido?')


class TemaForm(forms.Form):
    numerotema = forms.CharField(label=u'Número')
    ordentema = forms.IntegerField(label='Orden')
    nombretema = forms.CharField(label='Nombre')
    contenidotema = forms.CharField(widget=forms.Textarea, label='Contenido', required=False)


class DetTemaForm(forms.Form):
    descripcion = forms.CharField(widget=forms.Textarea, label='Contenido', required=False)


class SubTemaForm(forms.Form):
    numerosubtema = forms.CharField(label=u'Número')
    nombresubtema = forms.CharField(widget=forms.Textarea, label='Nombre', required=False)


class HabilidadesForm(forms.Form):
    habilidad = forms.CharField(widget=forms.Textarea, label=u'Descripción', required=False)


class HorasForm(forms.Form):
    valor = forms.IntegerField(label='Valor', required=False)


class RespuestaForm(forms.Form):
    descripcion = forms.CharField(label=u'Descripción', required=False)


class InscripcionReferidoForm(forms.Form):
    extranjero = forms.BooleanField(label='Extranjero?', required=False)
    cedula = forms.CharField(max_length=13, label=u"Cédula (*)", required=False)
    pasaporte = forms.CharField(max_length=15, label=u"Pasaporte", initial='', required=False)
    nombres = forms.CharField(max_length=200, label="Nombres (*)")
    apellido1 = forms.CharField(max_length=50, label="1er Apellido (*)")
    apellido2 = forms.CharField(max_length=50, label="2do Apellido", required=False)
    sexo = forms.ModelChoiceField(Sexo.objects, label="Sexo (*)")
    itb = forms.BooleanField(label='Modalidad Presencial?', required=False)
    online = forms.BooleanField(label='Modalidad Online?', required=False)
    conduccion = forms.BooleanField(label='Conduccion?', required=False)
    carrera = forms.ModelChoiceField(Carrera.objects.filter(carrera=True, activo=True, vigente=True),
                                     label="Carrera (*)", required=False)

    carreraonline = forms.CharField(max_length=500, label="Carrera Online (*)", required=False)
    tipolicencia = forms.CharField(max_length=500, label="Tipo Licencia (*)", required=False)
    modalidad = forms.ModelChoiceField(Modalidad.objects.filter(id__in=(1, 2)), label="Modalidad (*)", required=False)
    telefono_conv = forms.CharField(max_length=100, label=u"Telefonos Convencional", required=False)
    telefono = forms.CharField(max_length=100, label=u"Célular (*)", required=False)
    email = forms.CharField(max_length=240, label="Correos Electronicos (*)", required=False)

    def cargarcarrera(self):
        lista = []
        cn = psycopg2.connect("host=10.10.9.45 dbname=sgaonline user=aok password=R0b3rt0.1tb$")
        cur = cn.cursor()
        cur.execute("select id,nombre from sga_carrera")
        dato = cur.fetchall()
        cur.close()
        for row in dato:
            lista.append({'id': str(row[0]), 'nombre': elimina_tildes(row[1])})
        self.fields['carreraonline'] = forms.ChoiceField(choices=[(tag['id'], tag['nombre']) for tag in lista],
                                                         label="Carrera Online (*)", required=False)

    def cargarcarreraconduccion(self):
        listacon = []
        cn = psycopg2.connect("host=10.10.9.45 dbname=conduccion user=aok password=R0b3rt0.1tb$")
        cur = cn.cursor()
        cur.execute("select id,nombre from sga_carrera")
        dato = cur.fetchall()
        cur.close()
        for row in dato:
            listacon.append({'id': str(row[0]), 'nombre': elimina_tildes(row[1])})
        self.fields['tipolicencia'] = forms.ChoiceField(choices=[(tag['id'], tag['nombre']) for tag in listacon],
                                                        label="Tipo de Licencia (*)", required=False)


class CitaForm(forms.Form):
    asistio = forms.BooleanField(label=u'Asistió', required=False)
    observacion = forms.CharField(widget=forms.Textarea, label=u'Observación')


class InscripcionAspirantesForm(forms.Form):
    date_fields = ['f_inscripcion']
    cedula = forms.CharField(max_length=13, label=u"Cédula", required=False)
    pasaporte = forms.CharField(max_length=15, label=u"Pasaporte", initial='', required=False)
    nombres = forms.CharField(max_length=200, label="Nombres (*)")
    apellido1 = forms.CharField(max_length=50, label="1er Apellido (*)")
    apellido2 = forms.CharField(max_length=50, label="2do Apellido (*)", required=False)
    sexo = forms.ModelChoiceField(Sexo.objects, label="Sexo (*)")
    carrera = forms.ModelChoiceField(Carrera.objects.filter().exclude(id__in=CARRERAS_ID_EXCLUIDAS_INEC),
                                     label="Carrera (*)")
    sesionpractica = forms.ModelChoiceField(SesionPractica.objects, label="Horario (*)")
    telefono_conv = forms.CharField(max_length=100, label=u"Teléfono Convencional", required=False)
    telefono = forms.CharField(max_length=100, label=u"Célular (*)", required=False)
    email = forms.CharField(max_length=240, label=u"Correo Electrónico (*)", required=False)
    tiporegistro = forms.ModelChoiceField(TipoRegistroAspirante.objects.all(), label=u"Tipo Atención (*)")
    respuesta = forms.ModelChoiceField(OpcionRespuesta.objects.all(), label=u"Se inscribirá?")
    f_inscripcion = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'),
                                    label="Posible Fecha", required=False)
    tiponoregistro = forms.ModelChoiceField(TipoNoRegistroAspirante.objects.all(), label=u"Tipo No Registro",
                                            required=False)
    # vendedor = forms.ModelChoiceField(Vendedor.objects.filter(activo=True), label="Vendedor (*)")


class AulaAdministraForm(FixedForm):
    motivo = forms.CharField(widget=forms.Textarea, label=u'Motivo', required=False)
    fecha = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'),
                            label="Fecha de Inicio", required=False)

    class Meta:
        model = AulaAdministra
        exclude = ('user',)

    def for_aulafilter(self):
        self.fields['aula'].queryset = Aula.objects.filter(tipo__id=9)


class ArchivoForm(forms.Form):
    archivo = ExtFileField(label='Seleccione Archivo',
                           help_text='Tamano Maximo permitido 40Mb, en formato doc, docx, xls, xlsx, pdf, zip, tar, ppt, pptx',
                           ext_whitelist=(".doc", ".docx", ".xls", ".xlsx", ".pdf", ".zip", ".ppt", ".pptx", ".rar"),
                           max_upload_size=41943040)


class EnvioCorreoForm(forms.Form):
    prueba = forms.BooleanField(label='Prueba?', required=False)
    emails = forms.CharField(label=u"Destinatario", required=True)
    carrera = forms.ModelChoiceField(Carrera.objects.filter().exclude(id__in=CARRERAS_ID_EXCLUIDAS_INEC),
                                     required=False)
    periodo = forms.ModelChoiceField(Periodo.objects.filter(activo=True), required=False)
    nivel = forms.ModelChoiceField(NivelMalla.objects, required=False)
    asunto = forms.CharField(label=u"Asunto", required=True)
    correo = forms.CharField(label=u"Descripción", widget=forms.Textarea, required=True)
    archivo = ExtFileField(label='Seleccione Archivo', required=False,
                           help_text='Tamano Maximo permitido 40Mb, en formato doc, docx, xls, xlsx, pdf, jpg, png',
                           ext_whitelist=(".jpg", ".png", ".doc", ".docx", ".xls", ".xlsx", ".pdf"),
                           max_upload_size=41943040)

    def for_absentos(self):
        self.fields['carrera'].widget = HiddenInput()
        self.fields['carrera'].label = ''
        self.fields['periodo'].widget = HiddenInput()
        self.fields['periodo'].label = ''
        self.fields['nivel'].widget = HiddenInput()
        self.fields['nivel'].label = ''

    def for_egresados(self):
        self.fields['periodo'].widget = HiddenInput()
        self.fields['periodo'].label = ''
        self.fields['nivel'].widget = HiddenInput()
        self.fields['nivel'].label = ''


class ColegioForm(forms.Form):
    nombre = forms.CharField(max_length=300, label='Nombre Colegio', required=True)
    provincia = forms.ModelChoiceField(Provincia.objects.order_by('nombre'), label="Provincia Colegio", required=True)
    canton = forms.ModelChoiceField(Canton.objects.order_by('nombre'), label="Canton Colegio", required=True)
    tipo = forms.ModelChoiceField(TipoColegio.objects.order_by('nombre'), label="Tipo Colegio", required=True)


class RangoFacturasForm(forms.Form):
    inicio = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label='Fecha Inicio')
    fin = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label='Fecha Fin')


class RangoNCForm(forms.Form):
    inicio = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label='Fecha Inicio')
    fin = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label='Fecha Fin')


class IpRecaudacionForm(forms.Form):
    ip = forms.ModelChoiceField(IpRecaudacion.objects.order_by('nombre'), required=True)


class ConvenioBoxForm(FixedForm):
    class Meta:
        model = ConvenioBox
        exclude = ('',)


class PersonalConvenioForm(forms.Form):
    conveniobox = forms.ModelChoiceField(ConvenioBox.objects.filter(), label='Convenio')
    identificacion = forms.CharField(label='Identificacion')
    nombres = forms.CharField(label='Nombres')

    def for_convenio(self, usuario):
        self.fields['conveniobox'].queryset = ConvenioBox.objects.filter(usuarioconvenio__usuario=usuario)


class PrecioBoxForm(forms.Form):
    tipovisita = forms.ModelChoiceField(TipoVisitasBox.objects.all(), label='Tipo de Consulta')
    tipopersona = forms.ModelChoiceField(TipoPersona.objects.all(), label='Tipo de Persona')
    convenio = forms.ModelChoiceField(ConvenioBox.objects.all(), label='Convenio', required=False)
    precio = forms.DecimalField(max_digits=11, decimal_places=2)


class DetalleBecaCompletaForm(forms.Form):
    detalle = forms.CharField(max_length=150, label='Descripcion', required=False)
    valorrubro = forms.FloatField(label='Valor Rubro', required=True)


class RubroFechaForm(forms.Form):
    motivo = forms.CharField(label='Motivo', required=True)
    autoriza = forms.CharField(label='Autoriza', required=True)
    fechavence = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'),
                                 label="Fecha Vencimiento", required=True)


class DistributivoForm(forms.Form):
    inicio = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label='Fecha Inicio')
    fin = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label='Fecha Fin')


class EliminaRubroForm(forms.Form):
    motivo = forms.CharField(label='Motivo', required=True)
    autoriza = forms.CharField(label='Autoriza', required=True)


class PagoWesterForm(forms.Form):
    codigo = forms.CharField(max_length=30, label=u'Código Transacción', required=True)
    datos = forms.BooleanField(required=False, label='Datos?')
    identificacion = forms.CharField(max_length=20, label='RUC/Cedula', required=False)
    nombre = forms.CharField(max_length=100, label='Nombre', required=False)
    direccion = forms.CharField(max_length=100, label=u"Dirección", required=False)
    email = forms.CharField(max_length=50, label="Email", required=False)
    telefono = forms.CharField(max_length=20, label=u"Teléfono", required=False)
    archivo = ExtFileField(label='Seleccione Archivo',
                           help_text='Tamano Maximo permitido 40Mb, en formato doc, docx, xls, xlsx, pdf, png, jpg',
                           ext_whitelist=(
                               ".doc", ".docx", ".xls", ".xlsx", ".pdf", ".jpg", ".jpeg", ".JPEG", ".png", ".JPG"),
                           max_upload_size=41943040, required=True)


class ArchivoWesterForm(forms.Form):
    archivo = ExtFileField(label='Seleccione Archivo', help_text='Tamano Maximo permitido 40Mb, en formato  xlsx',
                           ext_whitelist=(".xlsx", ".xls"), max_upload_size=41943040)


class ArchivoPichinchaForm(forms.Form):
    archivo = ExtFileField(label='Seleccione Archivo', help_text='Tamano Maximo permitido 40Mb, en formato  txt',
                           ext_whitelist=(".txt", ".TXT"), max_upload_size=41943040)


class ConvenioAcadForm(forms.Form):
    descripcion = forms.CharField(max_length=150, label='Nombre', required=False)


class ConvenioUsuarioForm(forms.Form):
    usuario = forms.CharField(max_length=150, label='Usuario', required=False)
    usuario_id = forms.CharField(max_length=150, label='Usuario', required=False)
    convenio = forms.ModelChoiceField(ConvenioAcademico.objects.filter(activo=True).order_by('descripcion'),
                                      label='Convenio', required=False)


class ControlEspeciesForm(forms.Form):
    numeroe = forms.CharField(label='Numero Especie', required=False)
    codigoe = forms.CharField(label='Codigo Especie', required=False)
    fechae = forms.DateField(label='Fecha Especie', required=False)
    # destinatario = forms.CharField(label='Destinatario', required=False)
    observaciones = forms.CharField(widget=forms.Textarea(attrs={'maxlength': 300}), label='Observaciones')
    # reporte = forms.CharField(label='Seleccione Reporte',required=False)
    # reporte_id = forms.CharField(required=False)
    archivo = ExtFileField(label='Seleccione Archivo',
                           help_text='Tamano Maximo permitido 500Kb, en formato pdf,png, doc,docx',
                           ext_whitelist=(".doc", ".docx", ".pdf"), max_upload_size=524288, required=False)


class ControlEspeciesSecretariaForm(forms.Form):
    profesor = forms.CharField(label='Docente')
    profesor_id = forms.CharField(label='Docente')
    observaciones = forms.CharField(widget=forms.Textarea, label='Observaciones')


class RegistroVehiculoForm(forms.Form):
    vehiculo = forms.ModelChoiceField(Vehiculo.objects.filter(activo=True), label='Vehiculo')
    chofervehiculo = forms.ModelChoiceField(PersonaConduccion.objects.filter(chofer=True), label='Chofer')
    solicitante = forms.ModelChoiceField(Group.objects.all(), label="Solicitante")
    beneficiario = forms.ModelChoiceField(PersonaConduccion.objects.filter(), label='Beneficiario')
    fsalida = forms.DateField(input_formats=['%d-%m-%Y'], label="Fecha Salida")
    hsalida = forms.CharField(label="Hora Salida")
    kmsalida = forms.CharField(label="Km. Salida")
    origen = forms.CharField(label="Origen")
    fllegada = forms.DateField(input_formats=['%d-%m-%Y'], label="Fecha Regreso", required=False)
    hllegada = forms.CharField(label="Hora Regreso", required=False)
    kmllegada = forms.CharField(label="Km. Llegada", required=False)
    destino = forms.CharField(label="Destino", required=False)
    consumocomb = forms.CharField(label="Consumo Combustible (GL)", required=False)
    costocomb = forms.CharField(label="Costo Combustible ($)", required=False)
    observacion = forms.CharField(widget=forms.Textarea, label=u"Observación", required=False)
    salida = ExtFileField(label='Foto de Salida', help_text='Tamano Maximo permitido 40Mb, en formato ,jpg, png',
                          ext_whitelist=(".png", ".jpg", ".JPG"), max_upload_size=41943040, required=False)
    llegada = ExtFileField(label='Foto de Llegada', help_text='Tamano Maximo permitido 40Mb, en formato ,jpg, png',
                           ext_whitelist=(".png", ".jpg", ".JPG"), max_upload_size=41943040, required=False)


class AbsentismoForm(forms.Form):
    fecha = forms.DateField(label='Fecha')
    observacion = forms.CharField(widget=forms.Textarea, label=u'Observación')


class ObservacionDepositoForm(forms.Form):
    observacion = forms.CharField(label='Numero', required=False)


class PolizaForm(forms.Form):
    descripcion = forms.CharField(label=u'Descripción')
    proveedor = forms.CharField(label='Proveedor')
    inicio = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Inicio")
    fin = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fin")
    valor = forms.CharField(label='Valor')
    vigente = forms.BooleanField(label='Vigente', required=False)


class AdicionarVehiForm(forms.Form):
    vehiculo = forms.ModelChoiceField(Vehiculo.objects.filter(), label='Vehiculo')


class PersonaConduccionForm(forms.Form):
    identificacion = forms.CharField(label=u'Identificación')
    nombres = forms.CharField(label='Nombres')
    telefono = forms.CharField(label=u'Teléfono')
    email = forms.CharField(label='Email')
    categorialicencia = forms.ModelChoiceField(CategoriaVehiculo.objects.filter(), label=u'Categoría', required=False)
    chofer = forms.BooleanField(required=False)
    licencia = ExtFileField(label='Seleccione Archivo',
                            help_text='Tamano Maximo permitido 40Mb, en formato doc, docx, xls, xlsx, pdf ,jpg, png',
                            ext_whitelist=(".doc", ".docx", ".xls", ".xlsx", ".pdf", ".png", ".jpg", ".JPG"),
                            max_upload_size=41943040, required=False)


class FechasForm(forms.Form):
    exordinario = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'),
                                  label=u"Exámen Ordinario")
    revision = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'),
                               label=u"Revisión de Exámen")
    exatrasado = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'),
                                 label=u"Exámen Atrasado")


class MotivoForm(forms.Form):
    motivo = forms.CharField(max_length=200, label='Motivo', required=True)


class CertificadoForm(forms.Form):
    anio = forms.IntegerField(required=True, label=u'Año')
    certificado = forms.CharField(required=True, label='Nombre del Certificado')
    entregado = forms.CharField(required=True, label='Recibe')


class CulminacionEstudiosForm(forms.Form):
    correo = forms.CharField(required=True, label='Correo')
    celular = forms.CharField(required=True, label='Tlf. Celular')
    oficina = forms.CharField(required=True, label='Tlf. Oficina')
    domicilio = forms.CharField(required=True, label='Tlf. Domicilio')
    tipo = forms.ModelChoiceField(TipoCulminacionEstudio.objects.filter())

    def for_tipo(self, carrera):
        self.fields['tipo'].queryset = TipoCulminacionEstudio.objects.filter(carreratipoculminacion__carrera=carrera)


class TipoCulminacionForm(forms.Form):
    nombre = forms.CharField(label='Nombre')


class CarreraCulminacionForm(forms.Form):
    tipo = forms.ModelChoiceField(TipoCulminacionEstudio.objects.filter())


class AsignacionTutorForm(forms.Form):
    correo = forms.CharField(required=True, label='Tlf. Correo')
    celular = forms.CharField(required=True, label='Tlf. Celular')
    oficina = forms.CharField(required=True, label='Tlf. Oficina')
    domicilio = forms.CharField(required=True, label='Tlf. Domicilio')
    tema = forms.CharField(widget=forms.Textarea, required=True, label='Tema')

    def for_tipo(self, carrera):
        pass


class RespuestaEspecieForm(forms.Form):
    aprobado = forms.BooleanField(label='Aprobado?', required=False)
    reprobado = forms.BooleanField(label='Reprobado?', required=False)
    departamento = forms.ModelChoiceField(Departamento.objects.filter().order_by('descripcion'),
                                          label=u'Departamento realizó gestión')
    respuesta = forms.CharField(widget=forms.Textarea(attrs={'maxlength': 300}), required=True, label=u'Resolución')


class IngresoDocenteForm(forms.Form):
    profesor = forms.CharField(label='Profesor', required=False)


class ControlCambioProgramacionForm(forms.Form):
    nivel = forms.ModelChoiceField(Nivel.objects.filter(cerrado=False), label='Nivel')
    numeroe = forms.CharField(label='Numero Especie')
    codigoe = forms.CharField(label='Codigo Especie')
    fechae = forms.DateField(label='Fecha Especie')
    total = forms.DateField(label='Total')
    observacion = forms.CharField(widget=forms.Textarea(attrs={'maxlength': 300}), label='Observaciones')


class RubrosCambioProgramacionForm(forms.Form):
    rubro = forms.ModelChoiceField(Rubro.objects.filter().order_by('fechavence')[:5], label='Rubro', required=True)
    valor = forms.FloatField(label='Valor', required=True)

    def rubros_list(self, lista):
        self.fields['rubro'].queryset = Rubro.objects.filter(id__in=lista).order_by('fechavence')


class SeguimientoRetiroForm(forms.Form):
    seguimiento = forms.CharField(max_length=300, label='Seguimiento', required=True)
    fecha = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha")


class ProyeccionForm(forms.Form):
    desde = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Desde",
                            required=False)
    hasta = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Hasta",
                            required=False)


class VinculacionExcelForm(forms.Form):
    carrera = forms.ModelChoiceField(Carrera.objects.filter(carrera=True).order_by('nombre'), label='Carrera')


class MatriculadosExcelForm(forms.Form):
    carrera = forms.ModelChoiceField(Carrera.objects.filter(carrera=True).order_by('nombre'), label='Carrera')
    nivelmalla = forms.ModelChoiceField(NivelMalla.objects.filter().order_by('orden'), label='Nivel')


class EficienciaExcelForm(forms.Form):
    carrera = forms.ModelChoiceField(Carrera.objects.filter(carrera=True).order_by('nombre'), label='Carrera')
    inicio = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha Inicio")
    fin = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha Fin")


class GestionExcelForm(forms.Form):
    carrera = forms.ModelChoiceField(Carrera.objects.filter(carrera=True).order_by('nombre'), label='Carrera')
    periodo = forms.ModelChoiceField(Periodo.objects.filter(activo=True).order_by('inicio'), label='Periodo')


class PublicacionForm(forms.Form):
    es_revista = forms.BooleanField(label='Es Revista', required=False)
    titulo = forms.CharField(widget=forms.Textarea, label=u'Título', max_length=1500, required=True)
    autor = forms.CharField(label='Autor(s)', required=False)
    autor_codigos = forms.CharField(required=False)
    coautor = forms.CharField(label='CoAutor(s)', required=False)
    coautor_codigos = forms.CharField(required=False)
    codigo = forms.CharField(label=u'Código', max_length=50, required=True)
    num_paginas = forms.IntegerField(label=u'#Páginas', required=True)
    volumen = forms.IntegerField(label='Volumen', required=True)
    num_capitulos = forms.IntegerField(label=u'#Capítulos', required=False)
    referencias_bib = forms.IntegerField(label=u'#Referencias Bib.', required=False)
    proposito = forms.CharField(widget=forms.Textarea, label='Proposito', max_length=500, required=False)
    anno_publ = forms.CharField(label=u'Año Publicación', max_length=4, required=True)
    pais = forms.ModelChoiceField(Pais.objects.all(), label=u'País', required=True)
    descripcion = forms.CharField(widget=forms.Textarea, label=u'Descripción', max_length=1500, required=False)
    patrocinador = forms.CharField(widget=forms.Textarea, label='Patrocinador', max_length=300)
    imprenta = forms.CharField(widget=forms.Textarea, label='Imprenta', max_length=300, required=False)
    frecuencia = forms.IntegerField(label='Frecuencia en Meses', required=False)
    electronica = forms.BooleanField(label=u'Electrónica', required=False)
    impresa = forms.BooleanField(label='Impresa', required=False)
    indexado = forms.BooleanField(label='Indexado', required=False)
    bases_index = forms.CharField(widget=forms.Textarea, label='Bases Indexadas', max_length=1500, required=False)
    archivo = ExtFileField(label='Seleccione Archivo', required=False,
                           help_text='Tamano Maximo permitido 40Mb, en formato doc, docx, xls, xlsx, pdf',
                           ext_whitelist=(".doc", ".docx", ".xls", ".xlsx", ".pdf"), max_upload_size=41943040)


class AutorForm(forms.Form):
    existe = forms.BooleanField(label='Otro?', required=False)
    persona = forms.CharField(label='Autor(s)', required=False)
    persona_id = forms.CharField(label='Autor(s)', required=False)
    otro = forms.CharField(label='Otro(s)', required=False)


class EntregaMedicamentoForm(forms.Form):
    nombre = forms.ModelChoiceField(SuministroBox.objects.filter(estado=True), required=False)
    presentacion = forms.ModelChoiceField(TipoMedicamento.objects.all().order_by('descripcion'), required=False)
    lote = forms.CharField(max_length=200, required=False)
    cantidad = forms.IntegerField(required=True)
    fechavencimiento = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'),
                                       label="Fecha", required=False)
    motivo = forms.CharField(max_length=300, label='Motivo', required=False, widget=forms.Textarea)
    observacion = forms.CharField(widget=forms.Textarea, label=u'Observación', required=False)
    profesor = forms.CharField(label='Profesor', required=True)
    profesor_id = forms.CharField()

    def for_suministro(self):
        self.fields['nombre'].queryset = SuministroBox.objects.filter(estado=True).order_by('descripcion')


class GrupoPonenciaForm(forms.Form):
    codigo = forms.CharField(label=u'Código')
    nombre = forms.CharField(widget=forms.Textarea, label=u'Título Ponencia')
    horainicio = forms.CharField(max_length=10, required=False, label='Hora Inicio')
    horafin = forms.CharField(max_length=10, required=False, label='Hora Fin')
    integrantes = forms.IntegerField(label='Capacidad de Integrantes')
    precio = forms.FloatField(label="Costo")
    revisadopor = forms.CharField(label='Revisado por:')
    comision = forms.ModelChoiceField(ComisionCongreso.objects.filter().order_by('nombre'), label=u'Comisión')
    modalidad = forms.ModelChoiceField(ModalidadPonencia.objects.filter(), label='Modalidad')
    tipo = forms.ModelChoiceField(TipoPonencia.objects.filter(activo=True), required=False)
    numero = forms.CharField(label='Numero de Ensayo Cientifico/Ponencia')
    ubicacion = forms.CharField(max_length=300, required=False, label=u'Ubicación')


class InscripcionGrupoPonenciaForm(forms.Form):
    nombre = forms.CharField(widget=forms.Textarea, label=u'Título Ponencia')
    institucion = forms.CharField(widget=forms.Textarea, label=u'Institucion')
    horainicio = forms.CharField(max_length=10, required=False, label='Hora Inicio')
    horafin = forms.CharField(max_length=10, required=False, label='Hora Fin')
    integrantes = forms.IntegerField(label='Capacidad de Integrantes')
    tipo = forms.ModelChoiceField(TipoPonencia.objects.filter(activo=True), required=False,
                                  label='Tipo de Aporte Cientifico')


class InscripcionPonenciaForm(forms.Form):
    autor = forms.BooleanField(label='Es Autor?', required=False)
    inscripcion = forms.CharField(label='Autor:', required=False)
    inscripcion_id = forms.CharField(required=False)
    coautor = forms.CharField(label='Coautor:', required=False)
    institucion = forms.CharField(widget=forms.Textarea, label=u'Institucion')


class VendedorInscForm(forms.Form):
    vendedor = forms.ModelChoiceField(Vendedor.objects.filter(activo=True).order_by('nombres'))


class RecibirTituloForm(forms.Form):
    fechatitulo = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha",
                                  required=False)
    archivo = ExtFileField(label='Seleccione Archivo',
                           help_text='Tamano Maximo permitido 40Mb, en formato doc, docx, xls, xlsx, pdf',
                           ext_whitelist=(".doc", ".docx", ".xls", ".xlsx", ".pdf"), max_upload_size=41943040)
    insc_id = forms.CharField(required=False)


#
class VerEntregarTitForm(forms.Form):
    # fechaentregatitulo = forms.DateField(input_formats=['%d-%m-%Y'],widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha", required=False)
    recibetit = forms.CharField(label='Persona que recibe', required=False)


class InscripcionValoresForm(forms.Form):
    usuario = forms.CharField(label='Inscrito por:', required=False)
    usuario_id = forms.CharField(required=False)
    nivelmalla = forms.ModelChoiceField(NivelMalla.objects.filter().order_by('nombre'), label='Nivel Malla')
    desde = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Desde",
                            required=False)
    hasta = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Hasta",
                            required=False)


class MatriculadosporCarreraExcelForm(forms.Form):
    carrera = forms.ModelChoiceField(Carrera.objects.filter(carrera=True).order_by('nombre'), label='Carrera')
    detallado = forms.BooleanField(label='Reporte Detallado', required=False)
    resumido = forms.BooleanField(label='Reporte Resumido', required=False)


class InscritosGeneralForm(forms.Form):
    nivelmalla = forms.ModelChoiceField(NivelMalla.objects.filter().order_by('nombre'), label='Nivel Malla')
    desde = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Desde",
                            required=False)
    hasta = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Hasta",
                            required=False)


class ActualizaDatosForm(forms.Form):
    telefono = forms.CharField(label=u'Celular', required=True)
    telefono_conv = forms.CharField(label=u'Convencional', required=True)
    email = forms.CharField(label='Email', required=True)


class MateriaCursoBuckForm(forms.Form):
    sgaonline = forms.BooleanField(label='sgaonline', required=False)
    asignatura = forms.ModelChoiceField(Asignatura.objects.all(), label='Asignatura')
    instructor = forms.ModelChoiceField(Profesor.objects.all(), label='Instructor')
    grupo = forms.CharField(max_length=20, label=u"Grupo")
    horas = forms.IntegerField(label='Horas')
    numper = forms.IntegerField(label='Cantidad de Alumnos ')
    inicio = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha Inicio")
    fin = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha Fin")
    convalida = forms.BooleanField(label='Convalida', required=False)


class EspecieUniversalForm(forms.Form):
    departamento = forms.ModelChoiceField(Departamento.objects.filter(controlespecies=True,
                                                                      id__in=EspecieGrupo.objects.filter().values(
                                                                          'departamento')).order_by('descripcion'),
                                          label='Departamento', required=False)
    tipoe = forms.ModelChoiceField(TipoEspecieValorada.objects.filter(activa=True).order_by('nombre'),
                                   label='Tipo de Solicitud', required=True)
    materia = forms.CharField(label='Materia', required=False)
    # materia = forms.ModelChoiceField(MateriaAsignada.objects.filter(materia__cerrado=False),label='Materia',required=False)
    asignatura = forms.ModelChoiceField(Asignatura.objects.filter(), label='Asignatura', required=False)
    profesor = forms.ModelChoiceField(Profesor.objects.filter(activo=True, persona__usuario__is_active=True),
                                      label='Profesor', required=False)
    observacion = forms.CharField(widget=forms.Textarea, max_length=500, label=u'Observación', required=True)
    correo = forms.CharField(required=True, label='Correo Personal')
    celular = forms.CharField(required=True, label='Tlf. Celular')
    comprobante = ExtFileField(label='Subir Soporte',
                               help_text='Tamano Maximo permitido  4Mb,, en formato jpg, png, jpeg, pdf ',
                               ext_whitelist=(".png", ".jpg", ".jpeg", ".PNG", ".JPG", ".JPEG", ".pdf", ".PDF"),
                               max_upload_size=41943040, required=False)

    # cuentabanco = forms.ModelChoiceField(CuentaBanco.objects.all(),label="Cuenta", required=False)
    # referenciatransferencia = forms.CharField(max_length=50, label='# Transaccion del Banco', required=False)

    def for_tipo(self, inscripcion):
        # Inscripcion.objects.filter(persona__usuario=requstes)
        for i in Matricula.objects.filter(inscripcion=inscripcion):
            matricula = i
            materias = matricula.materia_asignada().filter().values('materia')
            self.fields['materia'] = forms.ChoiceField(
                choices=[(x.id, x.materia.asignatura.nombre) for x in matricula.materia_asignada().filter()])
            break

        coord = Coordinacion.objects.filter(carrera=inscripcion.carrera)[:1].get()
        coorddpto = CoordinacionDepartamento.objects.filter(coordinacion=coord).distinct('departamento').values(
            'departamento')
        self.fields['departamento'].queryset = Departamento.objects.filter(controlespecies=True,
                                                                           id__in=coorddpto).order_by('descripcion')
        # if coord.id==COORDINACION_UASSS and inscripcion.alumno_estado:
        #     self.fields['tipoe'].queryset=  TipoEspecieValorada.objects.filter(activa=True).exclude(id=85).order_by('nombre')
        malla = inscripcion.malla_inscripcion().malla
        asigrecord = RecordAcademico.objects.filter(inscripcion=inscripcion, aprobada=True).values('asignatura')
        asignaturas = AsignaturaMalla.objects.filter(malla=malla).exclude(asignatura__id__in=asigrecord).values(
            'asignatura')
        self.fields['asignatura'].queryset = Asignatura.objects.filter(id__in=asignaturas)

    def for_tipoasuntos(self, inscripcion):
        for i in Matricula.objects.filter(inscripcion=inscripcion):
            matricula = i
            materias = matricula.materia_asignada().filter().values('materia')
            self.fields['materia'] = forms.ChoiceField(
                choices=[(x.id, x.materia.asignatura.nombre) for x in matricula.materia_asignada().filter()])
            break

        coord = Coordinacion.objects.filter(carrera=inscripcion.carrera)[:1].get()
        coorddpto = CoordinacionDepartamento.objects.filter(coordinacion=coord, departamento__in=[14, 16, 17]).distinct(
            'departamento').values('departamento')
        self.fields['departamento'].queryset = Departamento.objects.filter(controlespecies=True,
                                                                           id__in=coorddpto).order_by('descripcion')
        malla = inscripcion.malla_inscripcion().malla
        asigrecord = RecordAcademico.objects.filter(inscripcion=inscripcion, aprobada=True).values('asignatura')
        asignaturas = AsignaturaMalla.objects.filter(malla=malla).exclude(asignatura__id__in=asigrecord).values(
            'asignatura')
        self.fields['asignatura'].queryset = Asignatura.objects.filter(id__in=asignaturas)


class RubroNivelCambioProgramacionForm(forms.Form):
    pagonivel = forms.ModelChoiceField(PagoNivel.objects.filter().order_by('fecha')[:5], label='Rubro', required=True)
    valorotro = forms.FloatField(label='Valor', required=True)

    def rubros_list(self, nivel):
        self.fields['pagonivel'].queryset = PagoNivel.objects.filter(nivel=nivel).order_by('fecha')


class ResolucionSolForm(forms.Form):
    resolucion = forms.CharField(widget=forms.Textarea(attrs={'maxlength': 500}), required=True, label=u'Resolución')


class RangoPagoTarjetasForm(forms.Form):
    inicio = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label='Fecha Inicio')
    fin = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label='Fecha Fin')


class DocumentoVinculacionForm(forms.Form):
    tipo = forms.ModelChoiceField(TipoDocumentosOficiales.objects.filter().order_by('tipo'), label='Tipo Documento')
    director1 = forms.CharField(label='Director Principal', required=True)
    director2 = forms.CharField(label='Segundo Director', required=False)
    director1id = forms.CharField(label='Director Principal', required=False)
    director2id = forms.CharField(label='Segundo Director', required=False)
    nombredocumento = forms.CharField(max_length=500, required=False, label='Nombre Documento')
    inicio = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha Inicio",
                             required=False)
    fin = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha Fin",
                          required=False)
    documento = ExtFileField(label='Seleccione Archivo',
                             help_text='Tamano Maximo permitido 40Mb, en formato doc, docx, xls, xlsx, pdf, zip, tar, ppt, pptx',
                             ext_whitelist=(".doc", ".docx", ".xls", ".xlsx", ".pdf", ".zip", ".ppt", ".pptx", ".rar"),
                             max_upload_size=41943040, required=False)


class EditarProvinciaForm(forms.Form):
    nombre = forms.CharField(label='Nombre')


class EditarCantonForm(forms.Form):
    nombre = forms.CharField(label='Nombre')
    provincia = forms.ModelChoiceField(Provincia.objects.all())


class EditarParroquiaForm(forms.Form):
    nombre = forms.CharField(label='Nombre')
    canton = forms.ModelChoiceField(Canton.objects.all())


class EditarSectorForm(forms.Form):
    nombre = forms.CharField(label='Nombre')
    parroquia = forms.ModelChoiceField(Parroquia.objects.all())


class ExternoForm(forms.Form):
    nombres = forms.CharField(label="Nombres", required=False)
    apellidos = forms.CharField(label="Apellidos", required=False)
    extranjero = forms.BooleanField(label='Extranjero?', required=False)
    cedula = forms.CharField(max_length=13, label=u"Cédula", required=False)
    pasaporte = forms.CharField(max_length=15, label=u"Pasaporte", initial='', required=False)
    email = forms.CharField(label="Email", required=False)
    fono = forms.CharField(label=u"Teléfono", required=False)
    direccion = forms.CharField(label=u"Dirección", required=False)
    valor = forms.CharField(label=u"Valor", required=False)


class GrupoCongresoForm(forms.Form):
    grupo = forms.ModelChoiceField(Grupo.objects.filter(carrera__id=16), label='Grupo')


class ArchivoTesisForm(forms.Form):
    soportetesis = ExtFileField(label='Documento de Tesis para Revision',
                                help_text='Tamano Maximo permitido 4Mb, en formato doc, docx',
                                ext_whitelist=(".doc", ".docx"), max_upload_size=41943040, required=True)


class RevisionTutoriaForm(forms.Form):
    observacion = forms.CharField(widget=forms.Textarea, max_length=1500, label=u'Observación')
    informe = ExtFileField(label='Informe Urkund',
                           help_text='Tamano Maximo permitido 4Mb, en formato doc, docx, jpg, png, pdf',
                           ext_whitelist=(".doc", ".docx", ".jpeg", ".JPEG", ".png", ".pdf", ".JPG"),
                           max_upload_size=41943040, required=True)
    finalizado = forms.BooleanField(label='Finalizado?', required=False)


class ActaSustentacionForm(forms.Form):
    nota = forms.DecimalField(max_digits=11, decimal_places=2)
    fecha_sustentacion = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'),
                                         label="Fecha Sustentacion", required=True)
    observacion = forms.CharField(widget=forms.Textarea, max_length=1500, label=u'Observación', required=False)
    acta = ExtFileField(label=u'Acta de Sustentación',
                        help_text='Tamano Maximo permitido 4Mb, en formato doc, docx, jpg, png, pdf',
                        ext_whitelist=(".doc", ".docx", ".jpeg", ".JPEG", ".png", ".pdf", ".JPG"),
                        max_upload_size=41943040, required=True)


class ComiteSustentacionForm(forms.Form):
    fechasust = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'),
                                label="Fecha Sustentacion", required=True)
    horasust = forms.TimeField(label='Hora', required=False)
    docente1 = forms.CharField(label="Docente", required=False)
    docente1_id = forms.CharField(label="Docente", required=False)
    docente2 = forms.CharField(label="Docente", required=False)
    docente2_id = forms.CharField(label="Docente", required=False)
    docente3 = forms.CharField(label="Docente", required=False)
    docente3_id = forms.CharField(label="Docente", required=False)


class TipoProgramaForm(forms.Form):
    nombre = forms.CharField(label='Nombre', widget=forms.Textarea)
    objetivo = forms.CharField(label='Objetivo', widget=forms.Textarea, required=False)


class TipoBecaForm(FixedForm):
    class Meta:
        model = TipoBeca
        exclude = ('',)


class MotivoBecaForm(FixedForm):
    class Meta:
        model = MotivoBeca
        exclude = ('',)


class PersonalSolicitudForm(forms.Form):
    persona = forms.ModelChoiceField(Persona.objects.filter(), label='Persona', required=True)
    observacion = forms.CharField(widget=forms.Textarea, max_length=1500, label=u'Observación', required=False)

    def personas_list(self, lista):
        self.fields['persona'].queryset = Persona.objects.filter(id__in=lista).order_by('apellido1', 'apellido2',
                                                                                        'nombres')


class DatoForm(forms.Form):
    dato = forms.CharField(required=True, label='Carrera')


class DatoForm2(forms.Form):
    dato2 = forms.CharField(required=True, label='Modalidad')


class DatoForm3(forms.Form):
    dato3 = forms.CharField(required=True, label=u'Clasificación')


class AprobacionVinculacionForm(forms.Form):
    # nivelmalla = forms.ModelChoiceField(NivelMalla.objects.filter(promediar=True).order_by('nombre'), label='Nivel Malla')
    revisionestudiante = forms.BooleanField(label='Revision de Estudiantes?', required=False)
    revisionproyecto = forms.BooleanField(label='Revision de Proyecto?', required=False)
    revisiondocente = forms.BooleanField(label='Revision Horas Docente?', required=False)
    comentarios = forms.CharField(widget=forms.Textarea, max_length=500, label='Comentarios', required=False)


class ModificaParticipanteForm(forms.Form):
    nivelmallamod = forms.ModelChoiceField(NivelMalla.objects.filter(
        id__in=AsignaturaMalla.objects.filter(asignatura__nombre__icontains='PREPRO').values('nivelmalla'),
        promediar=True), label="Nivel", required=False)
    # grupomod = forms.CharField(label='Grupo')
    horasmod = forms.IntegerField(label='Horas')


class Distributivo_AulasForm(forms.Form):
    sede = forms.ModelChoiceField(Sede.objects.filter(solobodega=False).order_by('nombre'), label='Sede')
    inicio = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label='Fecha Inicio')
    fin = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label='Fecha Fin')


class EstudianteInglesForm(forms.Form):
    sgaonline = forms.BooleanField(label='sgaonline', required=False)
    inscripcion = forms.CharField(label='Inscripcion', required=False)
    numdocument = forms.CharField(label=u'Cédula/Pasaporte', required=False)
    curso = forms.ModelChoiceField(Asignatura.objects.filter(),
                                   label=u'Nivel de convalidación ( Eligir el nivel hasta el cual el estudiante convalido.  )',
                                   required=False)


class VerificaPagoForm(forms.Form):
    codigo = forms.CharField(label=u'Código')


class RangoReferidoForm(forms.Form):
    inicio = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label='Fecha Inicio')
    fin = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label='Fecha Fin')


class MotivoCambioNotaForm(forms.Form):
    motivo = forms.CharField(label='Motivo')


class AprobacionCambioNotaForm(forms.Form):
    aprobado = forms.BooleanField(label='Aprobado?', required=False)
    reprobado = forms.BooleanField(label='Reprobado?', required=False)
    respuesta = forms.CharField(widget=forms.Textarea(attrs={'maxlength': 1000}), required=True, label=u'Observación')


class DescuentoGestionForm(forms.Form):
    porcentaje = forms.IntegerField(label='Porcentaje')
    fechadesc = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'),
                                label="Fecha Compromiso")


class LogQuitarAsignacionProfesorForm(forms.Form):
    observacion = forms.CharField(widget=forms.Textarea(attrs={'maxlength': 1000}), required=True, label=u'Observación')
    fechahasta = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'),
                                 label='Fecha Hasta')
    documento = ExtFileField(label='Seleccione Archivo',
                             help_text='Tamano Maximo permitido 40Mb, en formato doc, docx,  pdf',
                             ext_whitelist=(".doc", ".docx", ".xls", ".xlsx", ".pdf"), max_upload_size=41943040,
                             required=False)


class AbsentosExcelForm(forms.Form):
    todos = forms.BooleanField(label='Todas las carreras?', required=False)
    carrera = forms.ModelChoiceField(Carrera.objects.filter(carrera=True).order_by('nombre'), label='Carrera')
    inicio = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha Inicio")
    fin = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha Fin")


class TipoEspecieForm(FixedForm):
    class Meta:
        model = TipoEspecieValorada
        exclude = ('reporte', 'destinatario', 'cargo', 'certificado')

    def for_tipo(self):
        self.fields['tiposolicitud'].queryset = TipoSolicitudSecretariaDocente.objects.filter(activa=True).order_by(
            'nombre')

    informacion = forms.CharField(widget=forms.Textarea(attrs={'maxlength': 800}), required=False, label=u'Información')


class DepartamentoGrupoForm(forms.Form):
    departamento = forms.ModelChoiceField(Departamento.objects.filter(controlespecies=True).order_by('descripcion'),
                                          label='Departamento')


class DepartamentoForm(forms.Form):
    nombre = forms.CharField(label=u'Nombre', max_length=300)


class GrupoUsuarioForm(forms.Form):
    grupo = forms.CharField(label=u'Grupo', max_length=300)


class SeguimientoEspecieForm(forms.Form):
    observacion = forms.CharField(widget=forms.Textarea, label='Observacion', required=True)


class KitUniformeMunicipioForm(forms.Form):
    observacion = forms.CharField(label='Observacion', required=False)


class EntregaUniformeExcelForm(forms.Form):
    inicio = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha Inicio")
    fin = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha Fin")


class ClaseOnlineForm(forms.Form):
    fecha = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha")
    url = forms.CharField(widget=forms.Textarea, label='Enlace ', required=False)


class FechaForm(forms.Form):
    fecha = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha")


class RangoCobrosForm(forms.Form):
    inicio = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label='Fecha Inicio')
    fin = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label='Fecha Fin')
    carrera = forms.BooleanField(label='Carrera')
    coorinacion = forms.BooleanField(label=u'Coordinación')


class CuentaBancoForm(forms.Form):
    banco = forms.ModelChoiceField(Banco.objects.order_by('nombre'), label="Nombre de Banco", required=True)
    numero = forms.IntegerField(label=u"Numero de Cuenta", required=True)
    tipocuenta = forms.CharField(max_length=300, label='Tipo de Cuenta', required=True)
    representante = forms.CharField(max_length=300, label='Representante', required=True)
    activo = forms.BooleanField(label='Activo', required=False)


class XLSPeriodoForm(forms.Form):
    periodo = forms.ModelChoiceField(Periodo.objects.filter(activo=True).order_by('-inicio'), label='Periodo')


class PerfilProfesorAsignaturaForm(forms.Form):
    # profesor = forms.ModelChoiceField(Profesor.objects.filter(activo=True).order_by('persona__apellido1', 'persona__apellido2', 'persona__nombres').exclude(dedicacion__id=PROFE_PRACT_CONDUCCION), label='Docente', required=True)
    profesor = forms.CharField(label='Docente', required=True)
    fecha = forms.DateField(input_formats=['%Y-%m-%d'], widget=DateTimeInput(format='%Y-%m-%d'), label='Fecha',
                            required=False)
    estado = forms.BooleanField(label='Activo', required=False)


class SesionForm(forms.Form):
    sesion = forms.CharField(label='Nombre de Sesion', required=True)
    comienza = forms.TimeField(label='Hora de Inicio', required=False)
    termina = forms.TimeField(label='Hora de Fin', required=False)
    lunes = forms.BooleanField(label='Lunes', required=False)
    martes = forms.BooleanField(label='Martes', required=False)
    miercoles = forms.BooleanField(label='Miercoles', required=False)
    jueves = forms.BooleanField(label='Jueves', required=False)
    viernes = forms.BooleanField(label='Viernes', required=False)
    sabado = forms.BooleanField(label='Sabado', required=False)
    domingo = forms.BooleanField(label='Domingo', required=False)
    estado = forms.BooleanField(label='Estado Activo', required=False)


class SesionJornadaForm(forms.Form):
    sesion = forms.ModelChoiceField(Sesion.objects, label="Sesion", required=False)


class JornadaForm(forms.Form):
    nombre = forms.CharField(label='Nombre de Jornada', required=False)


class TurnoForm(forms.Form):
    turno = forms.IntegerField(label='# Turno', required=False)
    comienza = forms.TimeField(label='Hora de Inicio', required=False)
    termina = forms.TimeField(label='Hora de Fin', required=False)
    horas = forms.FloatField(label='Cantidad de horas', required=False)
    practica = forms.BooleanField(label='Tipo Practica', required=False)


class VendedorForm(forms.Form):
    nombres = forms.CharField(label='Nombres', required=False)
    identificacion = forms.IntegerField(label='Cedula', required=False)
    extra = forms.CharField(label='Informacion adicional', required=False)
    activo = forms.BooleanField(label='Estado', required=False)


class PromocionForm(forms.Form):
    descripcion = forms.CharField(label='Descripcion', required=False)
    directo = forms.BooleanField(label='Directo', required=False)
    activo = forms.BooleanField(label='Activo', required=False)
    todos_niveles = forms.BooleanField(label='Todos los niveles', required=False)
    val_inscripcion = forms.IntegerField(label='Descuento en Inscripcion (%)', required=False)
    descuentomaterial = forms.BooleanField(label='Descuento en material de apoyo', required=False)
    valormaterialapoyo = forms.FloatField(label='Valor del material de apoyo', required=False)
    valdescuentomaterial = forms.IntegerField(label='Descuento en material de apoyo(%)', required=False)


class GrupoCambioForm(forms.Form):
    nivelactualiza = forms.ModelChoiceField(NivelMalla.objects.filter(
        id__in=AsignaturaMalla.objects.filter(asignatura__nombre__icontains='PREPRO').values('nivelmalla'),
        promediar=True), label="Nivel", required=False)


# grupomod = forms.CharField(label='Grupo')

class GrupoIndividualCambioForm(forms.Form):
    nivelactualizaindividual = forms.ModelChoiceField(NivelMalla.objects.filter(
        id__in=AsignaturaMalla.objects.filter(asignatura__nombre__icontains='PREPRO').values('nivelmalla'),
        promediar=True), label="Nivel", required=False)


# grupomod = forms.CharField(label='Grupo')

class RecepcionActaDocenteForm(forms.Form):
    acta = ExtFileField(label='Acta de Notas', help_text='Tamano Maximo permitido 40Mb, pdf',
                        ext_whitelist=(".pdf", ".PDF"), max_upload_size=41943040, required=True)
    resumen = ExtFileField(label='Resumen de Acta', help_text='Tamano Maximo permitido 40Mb, pdf',
                           ext_whitelist=(".pdf", ".PDF"), max_upload_size=41943040, required=True)
    observaciones = forms.CharField(widget=forms.Textarea(attrs={'maxlength': 300}), label='Observaciones',
                                    required=True)


class RecepcionActaAlcanceDocenteForm(forms.Form):
    alcance = ExtFileField(label='Acta de Alcance', help_text='Tamano Maximo permitido 40Mb, pdf',
                           ext_whitelist=(".pdf", ".PDF"), max_upload_size=41943040, required=True)
    observaciones = forms.CharField(widget=forms.Textarea(attrs={'maxlength': 300}), label='Observaciones',
                                    required=True)


class RecepcionNivelCerradoDocenteForm(forms.Form):
    actanivel = ExtFileField(label='Acta', help_text='Tamano Maximo permitido 40Mb, pdf',
                             ext_whitelist=(".pdf", ".PDF"), max_upload_size=41943040, required=True)
    resumen = ExtFileField(label='Resumen de Acta Nivel Cerrado', help_text='Tamano Maximo permitido 40Mb, pdf',
                           ext_whitelist=(".pdf", ".PDF"), max_upload_size=41943040, required=True)
    observaciones = forms.CharField(widget=forms.Textarea(attrs={'maxlength': 300}), label='Observaciones',
                                    required=True)


class SolicutudMatriculaForm(forms.Form):
    observaciones = forms.CharField(widget=forms.Textarea(attrs={'maxlength': 1055}), label='Solicitud', required=True)


class SolicitudAyudaFinancieraForm(forms.Form):
    motivo = forms.CharField(widget=forms.Textarea(attrs={'maxlength': 400}), max_length=400,
                             label=u'Motivo de la Ayuda', required=False)
    # tipo = forms.ModelChoiceField(TipoDocumenBeca.objects.all(),required=False,label=u'Tipo Documento')
    # archivo = ExtFileField(label='Seleccione Archivo',help_text='Tamano Maximo permitido 40Mb, en formato doc, docx, pdf, png, jpg',ext_whitelist=( ".doc", ".docx", ".pdf",".png",".jpg"),max_upload_size=41943040,required=False)


class ResponSolicAyudaEconomicaForm(forms.Form):
    aprobado = forms.BooleanField(required=False, label='Aprobado?')
    observacion = forms.CharField(label=u'Observacion', widget=forms.Textarea, required=False)


class SolicitudArchivoAyudaForm(forms.Form):
    comentario = forms.CharField(widget=forms.Textarea(attrs={'maxlength': 400}), max_length=400, label=u'Comentario',
                                 required=False)
    tipobeca = forms.ModelChoiceField(TipoBeca.objects.all(), label="Tipo de Beca", required=False)
    motivobeca = forms.ModelChoiceField(MotivoBeca.objects.all(), label="Motivo de Beca", required=False)
    porcentajebeca = forms.FloatField(label="Porcentaje de Beca", required=False)
    puntarenovacion = forms.FloatField(label="Puntaje de Renovacion Beca", required=False)
    archivoanalisis = ExtFileField(label='Seleccione Archivo',
                                   help_text='Tamano Maximo permitido 40Mb, en formato doc, docx, pdf, png, jpg',
                                   ext_whitelist=(".doc", ".docx", ".pdf", ".png", ".jpg"), max_upload_size=41943040,
                                   required=False)


class SolicitudBecaRenovarForm(forms.Form):
    motivo = forms.CharField(widget=forms.Textarea(attrs={'maxlength': 400}), max_length=400,
                             label=u'Motivo de la Renovacion', required=False)
    # tipo = forms.ModelChoiceField(TipoDocumenBeca.objects.all(),required=False,label=u'Tipo Documento')
    # archivo = ExtFileField(label='Seleccione Archivo',help_text='Tamano Maximo permitido 40Mb, en formato doc, docx, pdf, png, jpg',ext_whitelist=( ".doc", ".docx", ".pdf",".png",".jpg"),max_upload_size=41943040,required=False)


class EmpresaConvenioForm(forms.Form):
    nombre = forms.CharField(label=u'Nombre de Empresa', required=False)
    ruc = forms.CharField(label=u'RUC', required=False)
    activideconomica = forms.CharField(label=u'Actividad Económica', required=False)
    direccion = forms.CharField(label=u'Dirección', required=False)
    ciudad = forms.ModelChoiceField(Canton.objects.all(), label="Ciudad", required=False)
    esempresa = forms.BooleanField(required=False, label='Es empresa?')
    estado = forms.BooleanField(required=False, label='Estado')


class BancoForm(forms.Form):
    nombre = forms.CharField(label=u'Nombre de Banco', required=False)
    tasaprotesto = forms.FloatField(label='Tasa Protesto', required=False)


class ComisionCongresoForm(forms.Form):
    nombre = forms.CharField(widget=forms.Textarea(attrs={'maxlength': 300}), max_length=300, label=u'Nombre Comision',
                             required=False)
    moderador = forms.CharField(label=u'Moderador', required=False)
    lugar = forms.CharField(label=u'Lugar', required=False)
    fecha = forms.DateField(input_formats=['%Y-%m-%d'], widget=DateTimeInput(format='%Y-%m-%d'), label='Fecha',
                            required=False)
    horainicio = forms.TimeField(label='Hora Inicio', required=False)
    horafin = forms.TimeField(label='Hora Fin', required=False)
    activo = forms.BooleanField(required=False, label='Estado')
    ubicacion = forms.CharField(label=u'Ubicacion', required=False)
    imgubicacion = ExtFileField(label='Imagen Ubicacion (*)',
                                help_text='Tamano Maximo permitido 4Mb, en formato doc, docx, pdf',
                                ext_whitelist=(".doc", ".docx", ".pdf"), max_upload_size=4194304, required=False)


class DetalleDescuentoBecaForm(forms.Form):
    rubro = forms.ModelChoiceField(Rubro.objects.filter(cancelado=False).order_by('fechavence')[:5], label='Rubro',
                                   required=True)
    porcentaje = forms.BooleanField(label='Porcentaje?', required=False)
    valorporcentaje = forms.FloatField(label='Porcentaje %', required=True)

    def rubros_list(self, lista):
        self.fields['rubro'].queryset = Rubro.objects.filter(id__in=lista).order_by('fechavence')


class AbreviaturaTituloForm(forms.Form):
    abreviatura = forms.ModelChoiceField(AbreviaturaTitulo.objects.filter().order_by('abreviatura'),
                                         label='Abreviatura de titulo', required=True)
    sin_titulo = forms.BooleanField(label='Sin titulo', required=False)
    otro_check = forms.BooleanField(label='Otro', required=False)
    otro = forms.CharField(label='Abreviatura de titulo', required=False)


class DocumentacionEstudForm(forms.Form):
    archivo = ExtFileField(label='Seleccione Archivo', required=False,
                           help_text='Tamano Maximo permitido 40Mb, en formato doc, docx, xls, xlsx, pdf',
                           ext_whitelist=(".doc", ".docx", ".xls", ".xlsx", ".pdf"), max_upload_size=41943040)


class TipoDocumentosOficialesForm(forms.Form):
    tipo = forms.CharField(label='Tipo Documento', required=False)


class TipoConvenioForm(forms.Form):
    nombre = forms.CharField(label='Tipo Convenio', required=False)


class GrupoReporteForm(forms.Form):
    grupo = forms.CharField(label='Grupo')


class RangoGestionForm(forms.Form):
    inicio = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label='Fecha Inicio')
    fin = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label='Fecha Fin')


class TutorForm(forms.Form):
    tutor = forms.ModelChoiceField(
        AsistenteDepartamento.objects.filter(estutor=False).order_by('persona__apellido1', 'persona__apellido2'),
        label='Tutor:', required=False)


class TutorForm2(forms.Form):
    tutor = forms.ModelChoiceField(
        AsistenteDepartamento.objects.filter(estutor=True).order_by('persona__apellido1', 'persona__apellido2'),
        label='Tutor:', required=False)


class NivelTutorForm(forms.Form):
    # nivel = forms.ModelChoiceField(Nivel.objects.filter(cerrado=False, carrera__carrera=True).order_by('paralelo'),label='Grupo:', required=False)
    nivel = forms.CharField(label='Grupo:', required=True)
    nivel_id = forms.CharField(label='Grupo:', required=True)
    activo = forms.BooleanField(label='Activo:', required=False)


class DatosTutorForm(forms.Form):
    telefono = forms.CharField(label='Telefono:', required=False)
    correo = forms.CharField(label='Correo Electronico:', required=False)


class MotivoAlcanceForm(forms.Form):
    motivoalcance = forms.ModelChoiceField(MotivoAlcance.objects, label='Motivo Alcance')


class MotivoAnulacionForm(forms.Form):
    motivoanulacion = forms.CharField(widget=forms.Textarea, label='Adicionar Motivo Anulacion', required=True)


class EntregaJugueteForm(forms.Form):
    tipoentrega = forms.ModelChoiceField(TipoEntrega.objects.filter(), label='Tipo de Entrega', required=True)
    observacion = forms.CharField(widget=forms.Textarea, label='Observacion', required=False)


class ExamenConvalidacionIngresoForm(forms.Form):
    aprobada = forms.BooleanField(label='Aprobado?', required=False)
    nota = forms.IntegerField(label="Nota", required=True)
    observacion = forms.CharField(widget=forms.Textarea, label=u'Observación', required=True)


class HorarioPersonaForm(forms.Form):
    # persona=forms.ModelChoiceField(Persona.objects.filter() ,required=False)
    horageneral = forms.BooleanField(required=False, label='Hora General')
    horaentrada = forms.CharField(max_length=10, required=False, label='Hora Entrada')
    horasalida = forms.CharField(max_length=10, required=False, label='Hora Salida')
    lunes = forms.BooleanField(required=False, label='Lunes')
    horalunesent = forms.CharField(max_length=10, required=False, label='Hora de Entrada')
    horalunessal = forms.CharField(max_length=10, required=False, label='Hora de Salida')
    martes = forms.BooleanField(required=False, label='Martes')
    horamartesent = forms.CharField(max_length=10, required=False, label='Hora de Entrada')
    horamartessal = forms.CharField(max_length=10, required=False, label='Hora de Salida')
    miercoles = forms.BooleanField(required=False, label='Miercoles')
    horamiercolesent = forms.CharField(max_length=10, required=False, label='Hora de Entrada')
    horamiercolessal = forms.CharField(max_length=10, required=False, label='Hora de Salida')
    jueves = forms.BooleanField(required=False, label='Jueves')
    horajuevesent = forms.CharField(max_length=10, required=False, label='Hora de Entrada')
    horajuevessal = forms.CharField(max_length=10, required=False, label='Hora de Salida')
    viernes = forms.BooleanField(required=False, label='Viernes')
    horaviernesent = forms.CharField(max_length=10, required=False, label='Hora de Entrada')
    horaviernessal = forms.CharField(max_length=10, required=False, label='Hora de Salida')
    finsemana = forms.BooleanField(required=False, label='Trabaja Fin de Semana')
    sabado = forms.BooleanField(required=False, label='Sabado')
    horasabadoent = forms.CharField(max_length=10, required=False, label='Hora de Entrada')
    horasabadosal = forms.CharField(max_length=10, required=False, label='Hora de Salida')
    domingo = forms.BooleanField(required=False, label='Domingo')
    horadomingoent = forms.CharField(max_length=10, required=False, label='Hora de Entrada')
    horadomingosal = forms.CharField(max_length=10, required=False, label='Hora de Salida')


class WebinarForm(forms.Form):
    nombre = forms.CharField(widget=forms.Textarea, label=u'Nombre:', required=False)
    # tipo = forms.ModelChoiceField(TipoWebinar.objects.filter(activo=True),label='Tipo Webinar')
    fecha = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha Desde:",
                            required=False)
    hasta = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha Hasta:",
                            required=False)
    hora = forms.TimeField(label='Hora:', required=False)
    archivo = ExtFileField(label='Base de Participantes', help_text='Tamano Maximo permitido 40Mb, en formato  xlsx',
                           ext_whitelist=(".xlsx", ".xls"), max_upload_size=41943040)
    archivofondo = ExtFileField(label='Imagen base para generar Certificados 3508x2482px',
                                help_text='Tamano Maximo permitido 40Mb', ext_whitelist=(".jpg", ".png"),
                                max_upload_size=41943040)


class TipoWebinarForm(forms.Form):
    nombre = forms.CharField(widget=forms.Textarea, label=u'Nombre:', required=False)
    archivo = ExtFileField(label='Imagen base para generar Certificados', help_text='Tamano Maximo permitido 40Mb',
                           ext_whitelist=(".jpg", ".png"), max_upload_size=41943040)


class MaterialDocenteForm(forms.Form):
    material = ExtFileField(label='Seleccione el Materia', help_text='Tamano Maximo permitido 40Mb, en formato  pdf ',
                            ext_whitelist=(".doc", ".docx", ".pdf", ".png", ".jpg"), max_upload_size=41943040,
                            required=True)
    bancopregunta = ExtFileField(label='Seleccione Banco de Pregunta',
                                 help_text='Tamano Maximo permitido 40Mb, en formato  pdf ',
                                 ext_whitelist=(".doc", ".docx", ".pdf", ".png", ".jpg"), max_upload_size=41943040,
                                 required=True)
    idzoom = forms.CharField(max_length=1000, required=False, label='Zoom ID')
    comentario = forms.CharField(widget=forms.Textarea(attrs={'maxlength': 400}), max_length=400, label=u'Comentario',
                                 required=False)


class MaterialDocenteEditarForm(forms.Form):
    materialeditar = ExtFileField(label='Seleccione el Materia',
                                  help_text='Tamano Maximo permitido 40Mb, en formato  pdf ',
                                  ext_whitelist=(".doc", ".docx", ".pdf", ".png", ".jpg"), max_upload_size=41943040,
                                  required=False)
    bancopreguntaeditar = ExtFileField(label='Seleccione Banco de Pregunta',
                                       help_text='Tamano Maximo permitido 40Mb, en formato  pdf ',
                                       ext_whitelist=(".doc", ".docx", ".pdf", ".png", ".jpg"),
                                       max_upload_size=41943040, required=False)


class AgregarPagoNivelMatriculaForm(forms.Form):
    observacion = forms.CharField(max_length=500, label='Observacion', widget=forms.Textarea, required=True)


class AprobacionSolicitudForm(forms.Form):
    autorizado = forms.BooleanField(label='Autorizado?')
    motivoautoriza = forms.CharField(widget=forms.Textarea(attrs={'maxlength': 1055}), max_length=1055,
                                     label=u'Observación', required=True)
    fechadeposito = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'),
                                    label='Fecha Transaccion')
    referencia = forms.CharField(max_length=50, required=True, label='Referencia')
    cuentabanco = forms.ModelChoiceField(CuentaBanco.objects.filter(activo=True), label='Cuenta')
    valor = forms.FloatField(label="Valor", required=True)
    deposito = forms.BooleanField(label=u'Depósito')
    transferencia = forms.BooleanField(label='Transferencia')


class PymentezForm(forms.Form):
    archivo = ExtFileField(label='Seleccione Archivo', help_text='Tamano Maximo permitido 40Mb, en formato xls, xlsx ',
                           ext_whitelist=(".xls", ".xlsx"), max_upload_size=41943040)


class MotivoLiberadaForm(forms.Form):
    motivoliberada = forms.CharField(widget=forms.Textarea, required=True, label="Motivo", max_length=2500)


class SolicitudBecaFormAddArchivo(forms.Form):
    cedula = ExtFileField(label='Seleccione Cedula',
                          help_text='Tamano Maximo permitido 40Mb, en formato doc, docx, pdf, png, jpg',
                          ext_whitelist=(".doc", ".docx", ".pdf", ".png", ".jpg"), max_upload_size=41943040,
                          required=False)
    cedulahijo = ExtFileField(label='Seleccione Cedula Hijo',
                              help_text='Tamano Maximo permitido 40Mb, en formato doc, docx, pdf, png, jpg',
                              ext_whitelist=(".doc", ".docx", ".pdf", ".png", ".jpg"), max_upload_size=41943040,
                              required=False)
    rolpago = ExtFileField(label='Seleccione Rol Pago',
                           help_text='Tamano Maximo permitido 40Mb, en formato doc, docx, pdf, png, jpg',
                           ext_whitelist=(".doc", ".docx", ".pdf", ".png", ".jpg"), max_upload_size=41943040,
                           required=False)
    partidanacimiento = ExtFileField(label='Seleccione Partida de Nacimiento',
                                     help_text='Tamano Maximo permitido 40Mb, en formato doc, docx, pdf, png, jpg',
                                     ext_whitelist=(".doc", ".docx", ".pdf", ".png", ".jpg"), max_upload_size=41943040,
                                     required=False)
    carnetdiscapacidad = ExtFileField(label='Seleccione Carnet de Discapacidad',
                                      help_text='Tamano Maximo permitido 40Mb, en formato doc, docx, pdf, png, jpg',
                                      ext_whitelist=(".doc", ".docx", ".pdf", ".png", ".jpg"), max_upload_size=41943040,
                                      required=False)
    certificado = ExtFileField(label='Seleccione Certificado de Enfermedad Catastrofica',
                               help_text='Tamano Maximo permitido 40Mb, en formato doc, docx, pdf, png, jpg',
                               ext_whitelist=(".doc", ".docx", ".pdf", ".png", ".jpg"), max_upload_size=41943040,
                               required=False)


class LiquidaRubroForm(forms.Form):
    motivo = forms.CharField(label='Motivo', required=True)
    autoriza = forms.CharField(label='Autoriza', required=True)


class InscritosAnioForm(forms.Form):
    anio = forms.IntegerField(label=u'Año', required=True)


class RegistroLlamadasForm(forms.Form):
    inscripcion = forms.CharField(label='Inscripcion')
    registro = forms.CharField()


class AsistenciaPeriodoCarreraExcelForm(forms.Form):
    periodo = forms.ModelChoiceField(Periodo.objects.filter(activo=True).order_by('-inicio'), label='Periodo')
    carrera = forms.ModelChoiceField(Carrera.objects.filter(carrera=True).order_by('nombre'), label='Carrera')


class ConveniosExcelForm(forms.Form):
    usaconvenio = forms.BooleanField(label='Elegir convenio', required=False)
    convenio = forms.ModelChoiceField(EmpresaConvenio.objects.filter().order_by('nombre'), label="Convenio")
    inicio = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label='Fecha Inicio')
    fin = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label='Fecha Fin')


class CambioPromocionForm(forms.Form):
    promocion = forms.ModelChoiceField(Promocion.objects.filter().order_by('descripcion'), label=u"Promoción")
    motivo = forms.CharField(label='Motivo')


class FormasdePagoForm(forms.Form):
    formadepago = forms.ModelChoiceField(ListaFormaDePago.objects.filter(pk=2), label='Forma de Pago')
    inicio = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label='Fecha Inicio')
    fin = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label='Fecha Fin')


class ColorTallaUniformeForm(forms.Form):
    color = forms.ModelChoiceField(ColorUniforme.objects.filter().order_by('nombre'), label="Color Uniforme")
    talla = forms.CharField(label='Talla')


class ColorTallaZapatosyUniformeForm(forms.Form):
    coloruniforme = forms.ModelChoiceField(ColorUniforme.objects.filter().order_by('nombre'), label="Color Uniforme")
    tallauniforme = forms.CharField(label='Talla Uniforme')
    colorzapatos = forms.ModelChoiceField(ColorZapato.objects.filter().order_by('nombre'), label="Color Zapatos")
    tallazapatos = forms.CharField(label='Talla Zapatos')


class AutorizarWesterForm(forms.Form):
    codigo = forms.CharField(max_length=30, label=u'Código Transacción', required=True)
    fecha = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label='Fecha')


class AprobarDocumentoForm(forms.Form):
    motivo = forms.CharField(widget=forms.Textarea, required=True, label="Motivo", max_length=2500)
    aprobado = forms.BooleanField(label='Aprobado', required=False)


class ParametroDescuentoForm(forms.Form):
    porcentaje = forms.IntegerField(label='Porcentaje', required=True)
    cuotas = forms.IntegerField(label='Cuotas', required=False)
    diaretras = forms.IntegerField(label='Dia Retraso', required=False)
    nivel = forms.BooleanField(label='Nivel', required=False)
    diactual = forms.BooleanField(label='Dia Actual', required=False)
    activo = forms.BooleanField(label='Activo', required=False)
    seminario = forms.BooleanField(label='Seminario', required=False)
    matricula = forms.BooleanField(label='Matricula', required=False)


class PermisoSgaForm(forms.Form):
    modulo = forms.ModelChoiceField(Modulo.objects.filter(activo=True), label='Modulo', required=False)
    permiso = forms.CharField(label='Permiso', required=False)
    observacion = forms.CharField(widget=forms.Textarea, label='Observaciones', required=False)
    accion = forms.CharField(label='Accion', required=False)


class UniformeForm(forms.Form):
    nombre = forms.CharField(label='Nombre', required=True)


class AulaManForm(forms.Form):
    nombre = forms.CharField(label='Nombre', required=True)
    capacidad = forms.IntegerField(label='Capacidad', required=False)
    tipo = forms.ModelChoiceField(TipoAula.objects.filter(), label='Tipo', required=False)
    sede = forms.ModelChoiceField(Sede.objects.filter(), label='Sede', required=False)
    ip = forms.CharField(label='IP', required=False)
    activa = forms.BooleanField(label='Activa', required=False)


class HorarioAsistenteSoliForm(forms.Form):
    horainicio = forms.TimeField(label='Hora Inicio', required=False)
    horafin = forms.TimeField(label='Hora fin', required=False)
    fecha = forms.DateField(label='Fecha', required=False)
    usuario = forms.ModelChoiceField(User.objects.filter(), label='Usuario', required=False)
    nolabora = forms.BooleanField(label='No Labora', required=False)
    sinatender = forms.IntegerField(label='Sin atender', required=False)
    fechaingreso = forms.DateTimeField(label='fecha de ingreso', required=False)


class PagoPyForms(forms.Form):
    # inscripcion=forms.CharField(label='Estudiante', required=False)
    estado = forms.CharField(label='Estado', required=False)
    idref = forms.CharField(label='Referencia', required=False)
    codigo_aut = forms.CharField(label=u'Código Autorización', required=False)
    mensaje = forms.CharField(label='Mensaje', required=False)
    factura = forms.CharField(label='Factura ID', required=False)

    monto = forms.CharField(label='Valor', required=False)
    referencia_dev = forms.CharField(label='Referencia Dev', required=False)

    detalle_estado = forms.CharField(label='Detalle Estado', required=False)
    referencia_tran = forms.CharField(label='Referencia Tran', required=False)
    tipo = forms.CharField(label='Tipo', required=False)
    rubros = forms.CharField(label='Rubro', required=False)
    correo = forms.CharField(label='Correo', required=False)
    nombre = forms.CharField(label='Nombre', required=False)
    direccion = forms.CharField(label='Direccion', required=False)
    ruc = forms.CharField(label='Ruc', required=False)
    telefono = forms.CharField(label='Telefono', required=False)
    anulado = forms.BooleanField(label='Anulado', required=False)
    motivo = forms.CharField(label='Motivo', required=False)
    detalle = forms.CharField(label='Detalle', required=False)

    lote = forms.CharField(label='Lote', required=False)


class ClienteFacturaForm(forms.Form):
    ruc = forms.CharField(label='RUC', required=False)
    nombre = forms.CharField(label='Nombre', required=False)
    direccion = forms.CharField(label='Direccion', required=False)
    telefono = forms.CharField(label='Telefono', required=False)
    correo = forms.CharField(label='Correo', required=False)
    contrasena = forms.CharField(label=u'Contraseña', required=False)
    numcambio = forms.CharField(label='Numero Cambio', required=False)


class RubroEspecieValoradaForm(forms.Form):
    observacionescon = forms.CharField(widget=forms.Textarea, label='Observaciones', required=False)
    # tipoespecie=forms.ModelChoiceField(TipoEspecieValorada.objects.filter(activa=True,pk__in=(13,16,39,47)).order_by('nombre'),label="Tipo Especie",required=False)
    # OCastillo 18-08-2022 al editar se puedan cambiar a todos los tipos de especies
    tipoespecie = forms.ModelChoiceField(TipoEspecieValorada.objects.filter(activa=True).order_by('nombre'),
                                         label="Tipo Especie", required=False)
    asignada = forms.ModelChoiceField(MateriaAsignada.objects.filter()[:1], label="Materia", required=False)
    docente = forms.ModelChoiceField(Profesor.objects.filter(activo=True)[:1], label="Profesor", required=False)
    aplicada = forms.BooleanField(label='Aplicada', required=False)
    usrautoriza = forms.CharField(label='Persona autoriza', required=False)
    usuario_id = forms.CharField(label='Usuario_id', required=False)
    disponible = forms.BooleanField(label='Disponible', required=False)
    obssecretaria = forms.CharField(label='Obs Secretaria', required=False)
    usrregistro = forms.CharField(label='Persona registra', required=False)
    usrregistro_id = forms.CharField(label='Usrregi_id', required=False)
    usrasig = forms.CharField(label='Persona asigna', required=False)
    usrasign_id = forms.CharField(label='Usrasig_id', required=False)


class InscripcionFlaForm(forms.Form):
    motivo = forms.CharField(label='Motivo', required=False)


class PagoSustentacionesDocenteForm(forms.Form):
    # profesor = forms.CharField(label= u'Docente', required=False)
    profesor = forms.ModelChoiceField(Profesor.objects.filter().order_by('persona__apellido1', 'persona__apellido2'),
                                      label="Docente")
    valorxestudiante = forms.FloatField(label='Valor por Alumno', required=False)
    numestudiantes = forms.IntegerField(label='Numero de Alumnos', required=False)
    fecha = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label='Fecha')


class EmpresaSinConvenioForm(forms.Form):
    nombre = forms.CharField(label='Nombre', required=False)
    ruc = forms.CharField(label='Ruc', required=False)
    activideconomica = forms.CharField(label='Actividad Economica', required=False)
    direccion = forms.CharField(label='Direccion', required=False)
    estadoempresa = forms.ModelChoiceField(EstadoEmpresa.objects.filter(), label='Estado de la Empresa', required=False)
    ciudad = forms.ModelChoiceField(Canton.objects.filter(), label='Ciudad', required=False)
    estado = forms.BooleanField(label='Estado', required=False)


class RangoReferidoComisionaForm(forms.Form):
    esadmin = forms.BooleanField(label='¿Es administrativo?', required=False)
    inscripcion = forms.ModelChoiceField(queryset=Inscripcion.objects.none(), label='Inscripción', required=False)
    administrativo = forms.ModelChoiceField(queryset=Persona.objects.none(), label='Administrativo', required=False)
    rangofechas = forms.BooleanField(label='¿Por rango de fechas?', required=False)
    finicio = forms.DateField(input_formats=['%d-%m-%Y'], widget=forms.DateTimeInput(format='%d-%m-%Y'), label='Fecha de inicio', required=False)
    ffin = forms.DateField(input_formats=['%d-%m-%Y'], widget=forms.DateTimeInput(format='%d-%m-%Y'), label='Fecha de fin', required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.utils.translation import gettext_lazy as _
        inscripciones = Inscripcion.objects.filter(inscripcion__inscripcion__isnull=False).distinct()  # cuando existen dos foreinkey en la misma tabla se define con el relatedname inscripcion__inscripcion__isnull=False en este caso de la tabla referidoinscripcion
        administrativos = Persona.objects.filter(referidosinscripcion__administrativo__isnull=False).distinct()

        if inscripciones.exists():
            self.fields['inscripcion'].queryset = inscripciones
        else:
            self.fields['inscripcion'].label = _('Inscripción (no hay opciones disponibles)')

        if administrativos.exists():
            self.fields['administrativo'].queryset = administrativos
        else:
            self.fields['administrativo'].label = _('Administrativo (no hay opciones disponibles)')
class GraduadosMatrizForm(forms.Form):
    anio = forms.IntegerField(label=u'Año', required=True)


class CacesRangoPeriodoForm(forms.Form):
    porperiodo = forms.BooleanField(required=False, label='Por Periodo?')
    inicio = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label='Fecha Inicio')
    fin = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label='Fecha Fin')
    periodo = forms.ModelChoiceField(Periodo.objects.filter(activo=True).order_by('-inicio'), label='Periodo')


class BodegaMantForm(forms.Form):
    # sede=forms.ModelChoiceField(Sede.objects.filter().exclude(solobodega=True),label='Bodega', required=True)
    sede = forms.ModelChoiceField(Sede.objects.filter(), label='Bodega', required=True)
    persona = forms.ModelChoiceField(Persona.objects.all().order_by('apellido1', 'apellido2', 'nombres'),
                                     label='Persona', required=True)

    def for_personal(self):
        self.fields['persona'].queryset = Persona.objects.filter(usuario__groups__id__in=GRUPO_BOX_ID).order_by(
            'apellido1', 'apellido2', 'nombres')


class RespuestaEspeciePracticasForm(forms.Form):
    aprobado = forms.BooleanField(label='Aprobado?', required=False)
    reprobado = forms.BooleanField(label='Reprobado?', required=False)
    respuesta = forms.CharField(widget=forms.Textarea(attrs={'maxlength': 300}), required=True, label=u'Resolución')


class EncuestaTutorForm(forms.Form):
    pregunta = forms.CharField(widget=forms.Textarea, label='Pregunta', required=False)
    orden = forms.IntegerField(label='Orden', required=False)


class IndicadorEncuestaForm(forms.Form):
    nombre = forms.CharField(label='Nombre Indicador', required=False)


class EncuestaAmbitosForm(forms.Form):
    ambitotutor = forms.ModelChoiceField(AmbitosTutor.objects.filter(), label='Pregunta')


class CrearEncuestaForm(forms.Form):
    cabecera = forms.CharField(label='Cabecera', required=False)
    recomendaciones = forms.CharField(widget=forms.Textarea, label='Recomendaciones', required=False)
    objetivos = forms.CharField(widget=forms.Textarea, label='Objetivos', required=False)
    estado = forms.BooleanField(label='Estado', required=False)


class CarreraEncuestaForm(forms.Form):
    carrera = forms.ModelChoiceField(Carrera.objects.filter(activo=True))


class ValorporMateriaForm(forms.Form):
    valorporhora = forms.BooleanField(label='Asignar Valor?', required=False)
    valor = forms.DecimalField(max_digits=11, decimal_places=2)


class HorasDictadasForm(forms.Form):
    pordocente = forms.BooleanField(required=False, label='Por Docente?')
    rolpago = forms.ModelChoiceField(RolPago.objects.filter(activo=True).order_by('-fecha'), label='Rol')
    profesor = forms.ModelChoiceField(Profesor.objects.all(), label="Docente")


class ExamenForm(forms.Form):
    archivo = ExtFileField(label='Seleccione Archivo', help_text='Tamano Maximo permitido 40Mb, en formato  pdf',
                           ext_whitelist=(".pdf", ".PDF"), max_upload_size=41943040, required=False)


class HorasDictadasxFechasForm(forms.Form):
    pordocente = forms.BooleanField(required=False, label='Por Docente?')
    profesor = forms.ModelChoiceField(Profesor.objects.all(), label="Docente")
    inicio = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label='Fecha Inicio')
    fin = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label='Fecha fin')


class PagoPracticasForm(forms.Form):
    descripcion = forms.CharField(widget=forms.Textarea, label='Descripcion:', required=False)
    # profesor = forms.CharField(label='Docente:',required=False)
    profesor = forms.ModelChoiceField(
        Profesor.objects.filter(activo=True).order_by('persona__apellido1', 'persona__apellido2', 'persona__nombres'),
        label="Docente")
    inicio = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha Inicio:")
    fin = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha Fin:")
    valor = forms.DecimalField(max_digits=4, decimal_places=2, label="Valor a pagar:")
    archivo = ExtFileField(label='Informe:',
                           help_text='Tamano Maximo permitido 40Mb, en formato doc, docx, xls, xlsx, pdf',
                           ext_whitelist=(".doc", ".docx", ".xls", ".xlsx", ".pdf"), max_upload_size=41943040)


class InscripcionPracticasForm(forms.Form):
    inscripcion = forms.CharField(label='Alumno', required=False)
    inscripcion_id = forms.CharField(required=False)
    nivelmalla = forms.ModelChoiceField(NivelMalla.objects.filter(
        id__in=AsignaturaMalla.objects.filter(asignatura__nombre__icontains='PREPRO').values('nivelmalla'),
        promediar=True), label="Nivel", required=False)
    horas = forms.IntegerField(label=u"Horas de Prácticas", required=True)
    lugar = forms.CharField(max_length=200, label="Lugar", required=False)
    inicio = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Inicio",
                             required=True)
    fin = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fin",
                          required=True)
    equipamiento = forms.CharField(max_length=200, label="Equipamiento", required=False)
    archivo = ExtFileField(label='Seleccione Archivo',
                           help_text='Tamano Maximo permitido 6Mb, en formato doc, docx, pdf',
                           ext_whitelist=(".doc", ".docx", ".pdf"), max_upload_size=6291456, required=False)
    observaciones = forms.CharField(widget=forms.Textarea, label='Observaciones', required=False)

    def nivel_malla(self, inscripcion):
        self.fields['nivelmalla'].queryset = (NivelMalla.objects.filter(id__in=AsignaturaMalla.objects.filter(
            Q(asignatura__nombre__icontains='LABORALES') | Q(asignatura__nombre__icontains='PREPRO'),
            malla=inscripcion.ultima_matricula_pararetiro().nivel.malla).values('nivelmalla')))


class InscripcionPracticasDistribucionForm(forms.Form):
    inscripcion_id = forms.CharField(label='Alumno', required=False)
    inscripcion = forms.CharField(required=False)
    horastotal = forms.IntegerField(label=u"Horas Total de Prácticas", required=True)
    lugar = forms.CharField(max_length=200, label="Lugar", required=False)
    inicio = forms.DateField(input_formats=['%Y-%m-%d'], widget=DateTimeInput(format='%d-%m-%Y'), label="Inicio",
                             required=True)
    fin = forms.DateField(input_formats=['%Y-%m-%d'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fin",
                          required=True)
    equipamiento = forms.CharField(max_length=200, label="Equipamiento", required=False)
    archivo = ExtFileField(label='Seleccione Archivo',
                           help_text='Tamano Maximo permitido 6Mb, en formato doc, docx, pdf',
                           ext_whitelist=(".doc", ".docx", ".pdf"), max_upload_size=6291456, required=False)
    observaciones = forms.CharField(widget=forms.Textarea, label='Observaciones', required=False)

    def nivel_malla(self, malla):
        self.fields['nivelmalla'].queryset = (NivelMalla.objects.filter(id__in=AsignaturaMalla.objects.filter(
            Q(asignatura__nombre__icontains='LABORALES') | Q(asignatura__nombre__icontains='PREPRO'),
            malla=malla).values('nivelmalla')))


class PracticasDistribucionHorasForm(forms.Form):
    nivelmalla = forms.ModelChoiceField(NivelMalla.objects.filter(id__in=AsignaturaMalla.objects.filter(
        Q(asignatura__nombre__icontains='LABORALES') | Q(asignatura__nombre__icontains='PREPRO')).values('nivelmalla')),
                                        label="Nivel", required=False)
    horas = forms.IntegerField(label=u"Horas", required=True)

    def nivel_malla(self, malla):
        self.fields['nivelmalla'].queryset = (NivelMalla.objects.filter(id__in=AsignaturaMalla.objects.filter(
            Q(asignatura__nombre__icontains='LABORALES') | Q(asignatura__nombre__icontains='PREPRO'),
            malla=malla).values('nivelmalla')))


class GraduadosAnioCarreraForm(forms.Form):
    anio = forms.IntegerField(label=u'Año', required=True)
    carrera = forms.ModelChoiceField(Carrera.objects.filter(carrera=True).order_by('nombre'), label='Carrera')


class NivelPagoPPPForm(forms.Form):
    coordinacion = Coordinacion.objects.filter(pk=COORDINACION_UACED).values('carrera')
    niveles = Nivel.objects.filter(cerrado=False, carrera__id=36, nivelmalla__id=5) | Nivel.objects.filter(
        cerrado=False, nivelmalla__id=4).exclude(carrera__id=36).order_by("nivelmalla__nombre", "grupo__nombre")
    # nivel = forms.ModelChoiceField(niveles.filter(carrera__id__in=coordinacion) ,label='Paralelo')
    nivel = forms.CharField(label='Paralelo', required=False)
    nivel_id = forms.CharField(label='Paralelo_id', required=False)


class DescuentosporConvenioForm(forms.Form):
    empresaconvenio = forms.ModelChoiceField(EmpresaConvenio.objects.filter(esempresa=True), label="Empresa Convenio",
                                             required=False)
    descripcion = forms.CharField(label='Descripcion', required=False)
    descuento = forms.IntegerField(label='Descuento', required=False)
    activo = forms.BooleanField(required=False)


class CoordinacionForm(forms.Form):
    coordinacion = forms.ModelChoiceField(Coordinacion.objects.filter(id__in=[1, 3, 5]), label="Facultad",
                                          required=False)


class EncuestaVacunasForm(forms.Form):
    estavacunado = forms.BooleanField(label='Esta Vacunado?', required=False)
    tipovacuna = forms.ModelChoiceField(VacunasCovid.objects.all().order_by('nombre'), label='Tipo de Vacuna',
                                        required=False)
    primeradosis = forms.BooleanField(label='1ra Dosis')
    segundadosis = forms.BooleanField(label='2da Dosis')
    terceradosis = forms.BooleanField(label='3ra Dosis')
    tipovacunaterceradosis = forms.ModelChoiceField(VacunasCovid.objects.all().order_by('nombre'),
                                                    label='Vacuna 3ra Dosis', required=False)
    hatenidocovid = forms.BooleanField(label='Ha tenido Covid?', required=False)


class CambioValoresRecibosForm(forms.Form):
    valorinicial = forms.FloatField(required=False, label='Valor Inicial')
    saldo = forms.FloatField(required=False, label='Saldo')
    motivocambio = forms.CharField(widget=forms.Textarea, label='Adicionar Motivo Cambio', required=True)


class CambioValorRubroForm(forms.Form):
    valor = forms.FloatField(required=True, label='Valor')


class AbsentosyRetiradosExcelForm(forms.Form):
    coordinacion = forms.ModelChoiceField(Coordinacion.objects.filter(id__in=[1, 3, 5]).order_by('nombre'),
                                          label='Facultad', required=True)
    anio = forms.IntegerField(label=u'Año', required=True)


class EjercicioTestPersonalidadForm(forms.Form):
    pregunta = forms.CharField(widget=forms.Textarea, label='Adicionar Pregunta', required=True)
    parametrotest = forms.ModelChoiceField(ParametroTest.objects.filter(tipotest__personalidad=True), label='Respuesta',
                                           required=True)


class SolicitudRevisionAplicada(forms.Form):
    comentario = forms.CharField(widget=forms.Textarea(attrs={'maxlength': 1000}), max_length=1000, label=u'Comentario',
                                 required=False)


class VacunadosporCoordinacionExcelForm(forms.Form):
    coordinacion = forms.ModelChoiceField(Coordinacion.objects.filter(id__in=[1, 3, 5]).order_by('nombre'),
                                          label='Facultad', required=True)
    resumido = forms.BooleanField(label='Reporte Resumido', required=False)


class XLSInscritosCantonForm(forms.Form):
    provincia = forms.ModelChoiceField(Provincia.objects.order_by('nombre'), label="Provincia de Residencia",
                                       required=False)
    canton = forms.ModelChoiceField(Canton.objects.order_by('nombre'), label="Canton de Residencia", required=False)
    inicio = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label='Fecha Inicio')
    fin = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label='Fecha Fin')


class GestorForm(forms.Form):
    persona = forms.ModelChoiceField(Persona.objects.filter().exclude(usuario__groups__id=ALUMNOS_GROUP_ID),
                                     label="Persona", required=False)
    activo = forms.BooleanField(label="Estado", required=False)


class PagoOtrosIngresosForm(forms.Form):
    profesor = forms.ModelChoiceField(Profesor.objects.filter().order_by('persona__apellido1', 'persona__apellido2'),
                                      label="Docente")
    valor = forms.FloatField(label='Valor', required=False)


class InscritosProvinciaForm(forms.Form):
    provincia = forms.ModelChoiceField(Provincia.objects.order_by('nombre'), label="Provincia de Residencia",
                                       required=True)


class PromocionInscForm(forms.Form):
    promocion = forms.ModelChoiceField(Promocion.objects.filter(activo=True).order_by('descripcion'))


class AprobacionSustentacionesDocenteForm(forms.Form):
    fechaaprueba = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'),
                                   label='Fecha de Aprobacion')


class IndicadoresExamComplexivoForm(forms.Form):
    carcord = Coordinacion.objects.filter(pk=COORDINACION_UASSS).values('carrera')
    carrera = forms.ModelChoiceField(
        Carrera.objects.filter(activo=True, carrera=True, pk__in=carcord).order_by('nombre'), label="Carrera")
    descripcion = forms.CharField(label='Descripcion', required=True)
    escala = forms.IntegerField(label='Escala', required=True)
    estado = forms.BooleanField(required=False)


class TramitesporDepartamentoForm(forms.Form):
    departamento = forms.ModelChoiceField(Departamento.objects.filter(controlespecies=True).order_by('descripcion'),
                                          label='Departamento', required=True)
    inicio = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label='Fecha Inicio',
                             required=True)
    fin = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label='Fecha Fin',
                          required=True)

    def for_departamento(self, departamento):
        self.fields['departamento'].queryset = Departamento.objects.filter(id__in=departamento).order_by('descripcion')


class FormasdePagoGeneralForm(forms.Form):
    formadepago = forms.ModelChoiceField(
        ListaFormaDePago.objects.filter(pk__in=[1, 2, 3, 4, 5, 13, 14, 15]).order_by('nombre'), label='Forma de Pago')
    inicio = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label='Fecha Inicio')
    fin = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label='Fecha Fin')


class CargaMasivaGraduacionForm(forms.Form):
    tipootrorubro = forms.ModelChoiceField(TipoOtroRubro.objects.filter().order_by('nombre'), label='Tipo Otro Rubro')
    valor = forms.DecimalField(max_digits=4, decimal_places=2)
    descripcion = forms.CharField(label='Descripcion')
    fecha = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'),
                            label='Fecha del Rubro')
    fechavencimiento = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'),
                                       label='Fecha de Vencimiento del Rubro')
    documento = ExtFileField(label='Seleccione Archivo', help_text='Tamano Maximo permitido 40Mb,en formato xls, xlsx',
                             ext_whitelist=(".xls", ".xlsx"), max_upload_size=41943040)


class CambioFechaActividadVinculacionForm(forms.Form):
    fecha = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha Cambio:",
                            required=True)


class EntrevistaProfesionalizacionForm(forms.Form):
    comentario = forms.CharField(widget=forms.Textarea(attrs={'maxlength': 1000}), max_length=1000, label=u'Comentario',
                                 required=False)
    link_video = forms.CharField(label='Enlace')


class AprobacionProfesionalizacionForm(forms.Form):
    observacion = forms.CharField(widget=forms.Textarea(attrs={'maxlength': 3000}), max_length=1000,
                                  label=u'Observacion', required=False)
    resolucion = forms.CharField(widget=forms.Textarea(attrs={'maxlength': 1500}), max_length=1000, label=u'Resolucion',
                                 required=False)
    aprobado = forms.BooleanField(label='Aprobado?', required=False)
    reprobado = forms.BooleanField(label='Reprobado?', required=False)


class DescuentoDobeForm(forms.Form):
    porcentaje = forms.FloatField(label='Porcentaje %', required=True)
    descuento = forms.FloatField(label='Descuento', required=True)
    valorrubro = forms.FloatField(label='Valor Rubro', required=False)


class ConveniosForm(forms.Form):
    anio = forms.IntegerField(label=u'Año', required=False)
    general = forms.BooleanField(required=False, label='General?')


class PlagioForm(forms.Form):
    observacion = forms.CharField(widget=forms.Textarea(attrs={'maxlength': 2000}), max_length=2000, label=u'Observacion', required=False)
    valorplagio = forms.FloatField(label='Valor Rubro', required=True)
    soporte = ExtFileField(label='Seleccione Archivo',
                           help_text='Tamano Maximo permitido 40Mb, en formato doc, docx, xls, xlsx, pdf, ppt, pptx, rar, zip , odp,DOCX',
                           ext_whitelist=(
                               ".doc", ".docx", ".DOCX", ".xls", ".xlsx", ".pdf", ".ppt", ".pptx", ".zip", ".rar", ".odp"),
                           max_upload_size=41943040)

class BuscarDemoForm(forms.Form):
    examencomplex = forms.ModelChoiceField(TituloExamenCondu.objects.filter(fecha='2015-01-01'), label='Complexivo')
    examendemo = forms.CharField(max_length=500, label=u'Examen')


class FacultadRangoFechasExcelForm(forms.Form):
    coordinacion = forms.ModelChoiceField(Coordinacion.objects.filter(id__in=[1, 3, 5]).order_by('nombre'),
                                          label='Facultad', required=True)
    inicio = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label='Desde')
    fin = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label='Hasta')


class MotivoCierreClasesForm(forms.Form):
    motivo = forms.ModelChoiceField(TipoMotivoCierreClases.objects.all().order_by('descripcion'), label='Motivo Cierre',
                                    required=True)


class MotivoInactivarAtrasoDocenteForm(forms.Form):
    descripcion = forms.CharField(widget=forms.Textarea(attrs={'maxlength': 100}), max_length=100, label=u'Descripcion')
    motivo = forms.CharField(widget=forms.Textarea(attrs={'maxlength': 100}), max_length=100, label=u'Motivo',
                             required=True)


class DepositoArchivoForm(forms.Form):
    cuentabancaria = forms.ModelChoiceField(CuentaBanco.objects.all(), label='Cuenta')
    fecha = forms.CharField(label='Fecha')
    archivo = ExtFileField(label='Seleccione Archivo', help_text='Tamano Maximo permitido 40Mb, en formato xls, xlsx ',
                           ext_whitelist=(".xls", ".xlsx"), max_upload_size=41943040)


class DetalleRegistroDepositoForm(forms.Form):
    fecha = forms.DateField(label="Fecha Inicio")
    hora = forms.TimeField(label="Hora")
    valor = forms.FloatField(label='Valor')
    tipo = forms.CharField(label='Tipo', required=False)
    horasimple = forms.CharField(label='Hora Simple', max_length=6)
    concepto = forms.CharField(label='Concepto')
    nut = forms.CharField(label='Nut')
    referencia = forms.CharField(label='Numero')
    fechareal = forms.DateField(label='Fecha Real')


class SupervisorGruposForm(forms.ModelForm):
    supervisor = forms.ModelChoiceField(
        queryset=Persona.objects.all().order_by('apellido1').exclude(
            usuario__groups__id__in=[PROFESORES_GROUP_ID, ALUMNOS_GROUP_ID]),
        label='Supervisor',
        required=True,
    )
    director = forms.ModelChoiceField(
        queryset=Persona.objects.all().order_by('apellido1').exclude(
            usuario__groups__id__in=[PROFESORES_GROUP_ID, ALUMNOS_GROUP_ID]),
        label='Director',
        required=True,
    )

    grupo = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all().order_by('name').exclude(id__in=[PROFESORES_GROUP_ID, ALUMNOS_GROUP_ID]),
        label='Departamentos',
        required=True,
    )
    activo = forms.BooleanField(required=False, label='Activo')

    def __init__(self, *args, **kwargs):
        super(SupervisorGruposForm, self).__init__(*args, **kwargs)
        self.fields['supervisor'].empty_label = 'Seleccionar un Supervisor'
        self.fields['director'].empty_label = 'Seleccionar un Director'
        self.fields['grupo'].widget.attrs['class'] = 'grupos-select'

    class Meta:
        model = SupervisorGrupos
        fields = ['supervisor', 'director', 'grupo', 'activo']


class EvaluacionDocenteForms(forms.Form):
    eje = forms.ModelChoiceField(EjesEvaluacion.objects.filter(estado=True), label=u'Ejes', required=False)
    descripcion = forms.CharField(widget=forms.Textarea, label=u'Descripcion', required=False)
    estado = forms.BooleanField(required=False, label='Estado')

    # periodo = forms.ModelChoiceField(Periodo.objects.filter(activo=True), label=u'Periodo', required=False)
    # desde = forms.DateField(label="Desde", required=False)
    # hasta = forms.DateField(label="Hasta", required=False)
    def evaluacion(self, op):
        if op == 1:
            self.fields['eje'].queryset = EjesEvaluacion.objects.filter(estado=True, docente=False, directivo=False,
                                                                        directivocargo=False)
        if op == 2:
            self.fields['eje'].queryset = EjesEvaluacion.objects.filter(estado=True, docente=True)
        if op == 3:
            self.fields['eje'].queryset = EjesEvaluacion.objects.filter(estado=True, directivo=True)
        if op == 4:
            self.fields['eje'].queryset = EjesEvaluacion.objects.filter(estado=True, directivocargo=True)


class AsignaEvaluacionForm(forms.Form):
    periodo = forms.ModelChoiceField(Periodo.objects.filter(activo=True), required=False, label=u'Nivel')
    materia = forms.ModelChoiceField(Materia.objects.filter(cerrado=True), required=False, label=u'Materia')


class CarrerasporCoordinacionForm(forms.Form):
    coordinacion = forms.ModelChoiceField(Coordinacion.objects.filter(id__in=[1, 3, 5]).order_by('nombre'),
                                          label='Facultad: ', required=True)


class MotObsEvidenciaCambioNotaForm(forms.Form):
    motivo = forms.ModelChoiceField(MotivoAlcance.objects.all().order_by('motivo'))
    observacion = forms.CharField(widget=forms.Textarea(attrs={'maxlength': 300}), label='Adicionar Observacion')
    evidencia = ExtFileField(label='Seleccione Archivo',
                             help_text='Tamano Maximo permitido 40Mb, en formato doc, docx, pdf, jpg, png',
                             ext_whitelist=(".doc", ".docx", ".DOCX", ".pdf", ".jpg", ".png"), max_upload_size=41943040)


class VerMotivoCambioNotaForm(forms.Form):
    motivo2 = forms.CharField(required=True, label='Motivo')
    observacion = forms.CharField(widget=forms.Textarea(attrs={'maxlength': 200}), label=u'Observacion')


class NotificacionForm(forms.Form):
    nombre = forms.CharField(label='Nombre:', max_length=300)
    descripcion = forms.CharField(label='Descripcion:', max_length=1000, widget=forms.Textarea, required=False)
    query = forms.CharField(label='Query:', max_length=1000, widget=forms.Textarea, required=False)
    funcion = forms.CharField(label='Funcion:', max_length=300)
    estado = forms.BooleanField(label='Estado?', required=False)


class NotificacionPersonaForm(forms.Form):
    persona = forms.CharField(label='Persona:', required=True)


# class VisitasBibliotecaPorCarreraForm(forms.Form):
#     sede = forms.ModelChoiceField(Sede.objects.filter(solobodega=False).order_by('nombre'), label="Sede:", required=False)
#     carrera = forms.ModelChoiceField(Carrera.objects.filter(carrera=True).order_by('nombre'), label='Carrera:')
#     inicio = forms.DateField(input_formats=['%d-%m-%Y'],widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha Inicio:")
#     fin = forms.DateField(input_formats=['%d-%m-%Y'],widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha Fin:")

class RepVisitasBibliotecaPorCarreraForm(forms.Form):
    sede = forms.CharField(label='Sede')
    carrera = forms.CharField(label='Carrera')
    desde = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label='Fecha Inicio')
    hasta = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label='Fecha Fin')

class ResumenVisitasBibliotecaForm(forms.Form):
    desde = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label='Fecha Inicio')
    hasta = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label='Fecha Fin')


class ProgramaVinculacionForm(forms.Form):
    tipo = forms.CharField(label='Nombre de Proyecto:')
    todo = forms.BooleanField(label='Todos', required=False)


class ReferenciaWebForm(forms.Form):
    prioridad = forms.IntegerField(label='Prioridad:', required=False)
    url = forms.CharField(widget=forms.Textarea, label='Enlace:', required=False)
    nombre = forms.CharField(label='Nombre:', required=False)
    logo = ExtFileField(label='Seleccione Imagen',
                        help_text='Tamano Maximo permitido 500Kb, en formato jpg, png. Dimensiones recomendadas 150x150 px',
                        ext_whitelist=(".png", ".jpg", ".JPG", ".PNG"), max_upload_size=524288)
    estado = forms.BooleanField(label='Estado?', required=False)


class OtraBibliotecaVirtualForm(forms.Form):
    prioridad = forms.IntegerField(label='Prioridad:', required=False)
    url = forms.CharField(widget=forms.Textarea, label='Enlace:', required=False)
    nombre = forms.CharField(label='Nombre:', required=False)
    logo = ExtFileField(label='Seleccione Imagen',
                        help_text='Tamano Maximo permitido 500Kb, en formato jpg, png. Dimensiones recomendadas 150x150 px',
                        ext_whitelist=(".png", ".jpg", ".JPG", ".PNG"), max_upload_size=524288)
    descripcion = forms.CharField(widget=forms.Textarea, label='Descripcion:', required=False)
    estado = forms.BooleanField(label='Estado?', required=False)


class ConsultasBibliotecasVirtualesForm(forms.Form):
    estudiante = forms.BooleanField(label='Estudiante?', required=False)
    docente = forms.BooleanField(label='Docente?', required=False)
    carrera = forms.CharField(label='Carrera')
    desde = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label='Fecha Inicio')
    hasta = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label='Fecha Fin')


class ListadoDocentexCoordinacion(forms.Form):
    coordinacion = forms.ModelChoiceField(Coordinacion.objects.filter(id__in=[1, 3, 5]).order_by('nombre'),
                                          label='Facultad: ', required=True)  # 1,3,5


class RangoPostulacionBecaForm(forms.Form):
    inicio = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label='Fecha Inicio')
    fin = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label='Fecha Fin')


class TotalEstudiantesXAnioForm(forms.Form):
    anio = forms.IntegerField(label=u'Año', required=False)
    carrera = forms.BooleanField(label='Carrera?', required=False)
    modalidad = forms.BooleanField(label='Modalidad?', required=False)
    grupo = forms.BooleanField(label='Grupo?', required=False)


class GraduadosGeneralForm(forms.Form):
    inicio = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label='Fecha Inicio')
    fin = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label='Fecha Fin')
    todos = forms.BooleanField(label='Todos',required= False)


class PlanAnaliticoForm(MY_Form):
    formacionprofesional = forms.CharField(
        label='FUNCIONES ESPECÍFICAS DE LA ASIGNATURA EN LA FORMACIÓN DEL PROFESIONAL',
        required=True,
        error_messages={'required': 'Campo no debe estar vacío'},
        widget=forms.Textarea(attrs={'class': 'form-control ckeditor', 'rows': '3', 'autocomplete': 'off'}))
    evidencialogro = forms.CharField(
        label='EVIDENCIAS DEL LOGRO DE LOS OBJETIVOS (SISTEMA DE EVALUACIÓN)',
        required=True,
        error_messages={'required': 'Campo no debe estar vacío'},
        widget=forms.Textarea(attrs={'class': 'form-control ckeditor', 'rows': '3', 'autocomplete': 'off'}))
    metodologia = forms.CharField(
        label='METODOLOGÍA DE ENSEÑANZA',
        required=True,
        error_messages={'required': 'Campo no debe estar vacío'},
        widget=forms.Textarea(attrs={'class': 'form-control ckeditor', 'rows': '3', 'autocomplete': 'off'}))
    # bibliografia = forms.CharField(
    #     label='BIBLIOGRAFÍA',
    #     required=True,
    #     error_messages={'required': 'Campo no debe estar vacío'},
    #     widget=forms.Textarea(attrs={'class': 'form-control ckeditor', 'rows': '3', 'autocomplete': 'off'}))
    # perfildocente = forms.CharField(
    #     label='PERFIL DEL DOCENTE',
    #     required=True,
    #     error_messages={'required': 'Campo no debe estar vacío'},
    #     widget=forms.Textarea(attrs={'class': 'form-control ckeditor', 'rows': '3', 'autocomplete': 'off'}))
    # compromiso = forms.CharField(label='Compromiso', required=True, error_messages={'required': 'Campo no debe estar vacío'}, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': '3', 'autocomplete': 'off'}))
    # caracterinvestigacion = forms.CharField(label='Caracter de investigación', required=True, error_messages={'required': 'Campo no debe estar vacío'}, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': '3', 'autocomplete': 'off'}))
    # lista_items1 = forms.JSONField(required=True, initial=list, error_messages={'required': 'Registre al menos un resultado de aprendizaje institucional RAI'}, widget=forms.HiddenInput())
    # lista_items2 = forms.JSONField(required=True, initial=list, error_messages={'required': 'Registre al menos un resultado de aprendizaje de carrera RAC'}, widget=forms.HiddenInput())
    # lista_items3 = forms.JSONField(required=True, initial=list, error_messages={'required': 'Registre al menos un objetivo'}, widget=forms.HiddenInput())
    # lista_items4 = forms.JSONField(required=True, initial=list, error_messages={'required': 'Registre al menos una metodologia'}, widget=forms.HiddenInput())
    lista_items5 = forms.JSONField(required=True, initial=list, error_messages={'required': 'Registre al menos un contenido programático'}, widget=forms.HiddenInput())

    def build(self):
        # del self.fields['lista_items1']
        # del self.fields['lista_items2']
        # del self.fields['lista_items3']
        # del self.fields['lista_items4']
        del self.fields['lista_items5']

    def clean_lista_items1(self):
        items = self.cleaned_data['lista_items1']

        for item in items:
            if not isinstance(item, dict):
                raise forms.ValidationError('Cada registro debe ser un diccionario.')
            required_keys = {"id", "descripcion"}
            if not required_keys.issubset(item.keys()):
                raise forms.ValidationError('Cada regisro debe contener las claves: id y descripcion.')

            if not isinstance(item.get('id'), int):
                raise forms.ValidationError('La clave id debe ser entero.')

            if not isinstance(item.get('descripcion'), str):
                raise forms.ValidationError('La clave descripcion debe ser cadena de caracteres.')

            if not item.get('descripcion'):
                raise forms.ValidationError('No se permite campos vacios')
        return items

    def clean_lista_items2(self):
        items = self.cleaned_data['lista_items2']

        for item in items:
            if not isinstance(item, dict):
                raise forms.ValidationError('Cada registro debe ser un diccionario.')
            required_keys = {"id", "descripcion"}
            if not required_keys.issubset(item.keys()):
                raise forms.ValidationError('Cada regisro debe contener las claves: id y descripcion.')

            if not isinstance(item.get('id'), int):
                raise forms.ValidationError('La clave id debe ser entero.')

            if not isinstance(item.get('descripcion'), str):
                raise forms.ValidationError('La clave descripcion debe ser cadena de caracteres.')

            if not item.get('descripcion'):
                raise forms.ValidationError('No se permite campos vacios')
        return items

    def clean_lista_items3(self):
        items = self.cleaned_data['lista_items3']

        for item in items:
            if not isinstance(item, dict):
                raise forms.ValidationError('Cada registro debe ser un diccionario.')
            required_keys = {"id", "descripcion"}
            if not required_keys.issubset(item.keys()):
                raise forms.ValidationError('Cada regisro debe contener las claves: id y descripcion.')

            if not isinstance(item.get('id'), int):
                raise forms.ValidationError('La clave id debe ser entero.')

            if not isinstance(item.get('descripcion'), str):
                raise forms.ValidationError('La clave descripcion debe ser cadena de caracteres.')

            if not item.get('descripcion'):
                raise forms.ValidationError('No se permite campos vacios')
        return items

    def clean_lista_items4(self):
        items = self.cleaned_data['lista_items4']

        for item in items:
            if not isinstance(item, dict):
                raise forms.ValidationError('Cada registro debe ser un diccionario.')
            required_keys = {"id", "descripcion"}
            if not required_keys.issubset(item.keys()):
                raise forms.ValidationError('Cada regisro debe contener las claves: id y descripcion.')

            if not isinstance(item.get('id'), int):
                raise forms.ValidationError('La clave id debe ser entero.')

            if not isinstance(item.get('descripcion'), str):
                raise forms.ValidationError('La clave descripcion debe ser cadena de caracteres.')

            if not item.get('descripcion'):
                raise forms.ValidationError('No se permite campos vacios')
        return items

    def clean(self, *args, **kwargs):
        cleaned_data = super(PlanAnaliticoForm, self).clean(*args, **kwargs)
        return cleaned_data


class BibliografiaApaForm(MY_Form):
    descripcion = forms.CharField(label='Bibliografía', required=True, error_messages={'required': 'Campo no debe estar vacío'}, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': '3', 'autocomplete': 'off'}))

    def clean(self, *args, **kwargs):
        cleaned_data = super(BibliografiaApaForm, self).clean(*args, **kwargs)
        return cleaned_data


class CronogramaAcademicoForm(MY_Form):
    nombre = forms.CharField(label='Nombre', required=True, error_messages={'required': 'Campo no debe estar vacío'}, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': '2', 'autocomplete': 'off'}))

    def clean(self, *args, **kwargs):
        cleaned_data = super(CronogramaAcademicoForm, self).clean(*args, **kwargs)
        return cleaned_data


class CronograAcademicoDetalleForm(MY_Form):
    from datetime import datetime
    from .models import PARCIAL
    descripcion = forms.CharField(label='Descripcion', required=True, error_messages={'required': 'Campo no debe estar vacío'}, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': '2', 'autocomplete': 'off'}))
    inicio = forms.DateField(input_formats=['%d-%m-%Y'], required=True, error_messages={'required': 'Campo no debe estar vacío'}, initial=datetime.now(), widget=forms.DateTimeInput(attrs={'class': 'form-control', 'autocomplete': 'off'}, format='%d-%m-%Y'), label='Fecha Inicio')
    fin = forms.DateField(input_formats=['%d-%m-%Y'],  required=True, error_messages={'required': 'Campo no debe estar vacío'}, initial=datetime.now(), widget=forms.DateTimeInput(attrs={'class': 'form-control', 'autocomplete': 'off'}, format='%d-%m-%Y'), label='Fecha Fin')
    parcial = forms.ChoiceField(label=u'Parcial', required=False, choices=PARCIAL, widget=forms.Select(attrs={'class': 'form-select'}))
    numsemana = forms.IntegerField(label=u'Número de semana', initial=0, required=True, error_messages={'required': 'Campo no debe estar vacío', 'invalid': 'Debe ser un número válido'}, widget=forms.NumberInput(attrs={'class': 'form-control', 'decimal': '0', 'autocomplete': 'off'}))
    examen = forms.BooleanField(label='Examen', initial=False, required=False, widget=forms.CheckboxInput(attrs={'class': ''}))

    def clean_numsemana(self):
        numsemana = self.cleaned_data.get('numsemana')
        if numsemana is not None and numsemana <= 0:
            raise forms.ValidationError('El número de semana debe ser mayor a cero.')
        return numsemana

    def clean(self, *args, **kwargs):
        cleaned_data = super(CronograAcademicoDetalleForm, self).clean(*args, **kwargs)
        return cleaned_data


class SilaboSemanalForm(MY_Form):
    objetivoaprendizaje = forms.CharField(label='Objetivo Aprendizaje', required=True,  error_messages={'required': 'Campo no debe estar vacío'}, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': '2', 'autocomplete': 'off'}))
    enfoque = forms.CharField(label='Enfoque', required=True,  error_messages={'required': 'Campo no debe estar vacío'}, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': '2', 'autocomplete': 'off'}))
    enfoquedos = forms.CharField(label='Enfoque de Desarrollo', required=True,  error_messages={'required': 'Campo no debe estar vacío'}, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': '2', 'autocomplete': 'off'}))
    enfoquetres = forms.CharField(label='Enfoque de Cierre', required=True,  error_messages={'required': 'Campo no debe estar vacío'}, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': '2', 'autocomplete': 'off'}))
    recursos = forms.CharField(label='Recursos Didácticos', required=True,  error_messages={'required': 'Campo no debe estar vacío'}, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': '2', 'autocomplete': 'off'}))
    evaluacion = forms.CharField(label='Evaluación', required=True,  error_messages={'required': 'Campo no debe estar vacío'}, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': '2', 'autocomplete': 'off'}))

    def build(self):
        del self.fields['lista_items1']
        del self.fields['lista_items2']

    def clean_lista_items1(self):
        items = self.cleaned_data['lista_items1']

        for item in items:
            if not isinstance(item, dict):
                raise forms.ValidationError('Cada registro debe ser un diccionario.')
            required_keys = {"id", "nombreCorto", "enlace"}
            if not required_keys.issubset(item.keys()):
                raise forms.ValidationError('Cada regisro debe contener las claves: id, nombreCorto y enlace.')

            if not isinstance(item.get('id'), int):
                raise forms.ValidationError('La clave id debe ser entero.')

            if not isinstance(item.get('nombreCorto'), str):
                raise forms.ValidationError('La clave nombreCorto debe ser cadena de caracteres.')

            if not isinstance(item.get('enlace'), str):
                raise forms.ValidationError('La clave enlace debe ser cadena de caracteres.')

            if not item.get('nombreCorto'):
                raise forms.ValidationError('No se permite campos vacios')

            if not item.get('enlace'):
                raise forms.ValidationError('No se permite campos vacios')
        return items

    def clean_lista_items2(self):
        items = self.cleaned_data['lista_items2']

        for item in items:
            if not isinstance(item, dict):
                raise forms.ValidationError('Cada registro debe ser un diccionario.')
            required_keys = {"id_t", "subtemas"}
            if not required_keys.issubset(item.keys()):
                raise forms.ValidationError('Cada regisro debe contener las claves: id_t y subtemas.')

            if not isinstance(item.get('id_t'), int):
                raise forms.ValidationError('La clave id debe ser entero.')

            if not isinstance(item.get('subtemas'), dict):
                raise forms.ValidationError('La clave subtemas debe ser un diccionario.')

            if not item.get('id_t'):
                raise forms.ValidationError('No se permite campos vacios')

        return items
    def clean(self, *args, **kwargs):
        cleaned_data = super(SilaboSemanalForm, self).clean(*args, **kwargs)
        return cleaned_data


class DiapositivaSilaboSemanalForm(MY_Form):
    from .models import TIPO_MATERIALADICIONAL
    nombre = forms.CharField(label='Nombre', required=True, max_length=100, error_messages={'required': 'Campo no debe estar vacío'}, widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off', 'maxlength': 100}))
    descripcion = forms.CharField(label='Enfoque', required=True,  error_messages={'required': 'Campo no debe estar vacío'}, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': '2', 'autocomplete': 'off'}))
    tipomaterial = forms.ChoiceField(label=u'Tipo material', required=True, choices=TIPO_MATERIALADICIONAL, widget=forms.Select(attrs={'class': 'form-select'}))
    archivodiapositiva = ExtFileField(label='Seleccione Archivo', required=False,
                                      error_messages={'required': 'Campo no debe estar vacío'},
                                      help_text='Tamaño máximo permitido 30MB, en formato DOC, DOCX, XLS, XLSX, PDF, PPT, PPTX',
                                      ext_whitelist=(".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"),
                                      max_upload_size=30000000,
                                      widget=forms.FileInput(attrs={
                                          'accept': 'application/pdf, application/msword, application/vnd.openxmlformats-officedocument.wordprocessingml.document, application/vnd.ms-excel, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-powerpoint, application/vnd.openxmlformats-officedocument.presentationml.presentation'
                                      }))
    url = forms.CharField(label='Url', max_length=100, required=False, error_messages={'required': 'Campo no debe estar vacío'}, widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}))

    def set_tipomaterial(self, tipo, esNuevo=False):
        self.fields['archivodiapositiva'].required = False
        if tipo == 2:
            self.fields['url'].required = True
        else:
            if esNuevo:
                self.fields['archivodiapositiva'].required = True

    def clean(self, *args, **kwargs):
        cleaned_data = super(DiapositivaSilaboSemanalForm, self).clean(*args, **kwargs)
        return cleaned_data


class VideoMagistralSilaboSemanalForm(MY_Form):
    from .models import TIPO_MATERIALADICIONAL, TIPO_GRABACION, TIPO_RECURSO_VIDEO
    descripcion = forms.CharField(label='Enfoque', required=True,  error_messages={'required': 'Campo no debe estar vacío'}, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': '2', 'autocomplete': 'off'}))
    tipomaterial = forms.ChoiceField(label=u'Tipo material', required=True, choices=TIPO_MATERIALADICIONAL, widget=forms.Select(attrs={'class': 'form-select'}))
    tipovideo = forms.ChoiceField(label=u'Tipo de recurso', required=True, choices=TIPO_RECURSO_VIDEO, widget=forms.Select(attrs={'class': 'form-select'}))
    tipograbacion = forms.ChoiceField(label=u'Tipo de grabación', required=True, choices=TIPO_GRABACION, widget=forms.Select(attrs={'class': 'form-select'}))
    archivovideo = ExtFileField(label='Seleccione Archivo', required=False,
                                error_messages={'required': 'Campo no debe estar vacío'},
                                help_text='Tamano Maximo permitido 40Mb, en formato mp4',
                                ext_whitelist=(".mp4",),
                                max_upload_size=41943040,
                                widget=forms.FileInput(attrs={'accept': 'video/mp4'}))
    url = forms.CharField(label='Url', max_length=300, required=False, error_messages={'required': 'Campo no debe estar vacío'}, widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}))

    def set_tipomaterial(self, tipo, esNuevo=False):
        self.fields['archivovideo'].required = False
        if tipo == 2:
            self.fields['url'].required = True
        else:
            if esNuevo:
                self.fields['archivovideo'].required = True

    def clean_tipovideo(self):
        tipovideo = int(self.cleaned_data.get('tipovideo', '0'))
        if tipovideo <=0:
            raise forms.ValidationError('Seleccione un tipo de video')
        return tipovideo

    def clean_tipograbacion(self):
        tipograbacion = int(self.cleaned_data.get('tipograbacion', '0'))
        if tipograbacion <= 0:
            raise forms.ValidationError('Seleccione un tipo de grabacion')
        return tipograbacion

    def clean(self, *args, **kwargs):
        cleaned_data = super(VideoMagistralSilaboSemanalForm, self).clean(*args, **kwargs)
        return cleaned_data


class CompendioSilaboSemanalForm(MY_Form):
    nombre = forms.CharField(label='Nombre', required=True, max_length=100, error_messages={'required': 'Campo no debe estar vacío'}, widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off', 'maxlength': 100}))
    descripcion = forms.CharField(label='Descripción', required=True, error_messages={'required': 'Campo no debe estar vacío'}, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': '2', 'autocomplete': 'off'}))
    archivocompendio = ExtFileField(label='Archivo compendio', required=False,
                                    error_messages={'required': 'Campo no debe estar vacío'},
                                    help_text='Tamano Maximo permitido 30Mb, en formato pdf, doc, docx',
                                    ext_whitelist=(".pdf", ".doc", ".docx"),
                                    max_upload_size=30000000,
                                    widget=forms.FileInput(attrs={'accept': 'application/pdf, application/msword, application/vnd.openxmlformats-officedocument.wordprocessingml.document'}))
    archivoplagio = ExtFileField(label='Archivo plagio', required=False,
                                 error_messages={'required': 'Campo no debe estar vacío'},
                                 help_text='Tamano Maximo permitido 30Mb, en formato pdf, doc, docx',
                                 ext_whitelist=(".pdf", ".doc", ".docx"),
                                 max_upload_size=30000000,
                                 widget=forms.FileInput(attrs={'accept': 'application/pdf, application/msword, application/vnd.openxmlformats-officedocument.wordprocessingml.document'}))
    porcentaje = forms.IntegerField(label=u'Porcentaje', initial=0, required=True, error_messages={'required': 'Campo no debe estar vacío', 'invalid': 'Debe ser un número válido'}, widget=forms.NumberInput(attrs={'class': 'form-control', 'decimal': '2', 'autocomplete': 'off'}))

    def set_required(self):
        self.fields['archivocompendio'].required = True
        self.fields['archivoplagio'].required = True

    def clean(self, *args, **kwargs):
        cleaned_data = super(CompendioSilaboSemanalForm, self).clean(*args, **kwargs)
        return cleaned_data


class GuiaEstudianteSilaboSemanalForm(MY_Form):
    nombre = forms.CharField(label='Nombre', required=True, max_length=100, error_messages={'required': 'Campo no debe estar vacío'}, widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off', 'maxlength': 100}))
    objetivo = forms.CharField(label='Objetivo', required=True, error_messages={'required': 'Campo no debe estar vacío'}, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': '2', 'autocomplete': 'off'}))
    archivoguiaestudiante = ExtFileField(label='Archivo guía del estudiante', required=False,
                                         error_messages={'required': 'Campo no debe estar vacío'},
                                         help_text='Tamano Maximo permitido 30Mb, en formato pdf, doc, docx',
                                         ext_whitelist=(".pdf", ".doc", ".docx"),
                                         max_upload_size=30000000,
                                         widget=forms.FileInput(attrs={'accept': 'application/pdf, application/msword, application/vnd.openxmlformats-officedocument.wordprocessingml.document'}))

    def set_required(self):
        self.fields['archivoguiaestudiante'].required = True

    def clean(self, *args, **kwargs):
        cleaned_data = super(GuiaEstudianteSilaboSemanalForm, self).clean(*args, **kwargs)
        return cleaned_data


class CriterioForm(MY_Form):
    from .models import TiempoDedicacionDocente, TIPO_CRITERIO
    nombre = forms.CharField(label='Nombre', required=True, error_messages={'required': 'Campo no debe estar vacío'}, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': '3', 'autocomplete': 'off'}))
    dedicacion = ModelChoiceField(label='Tipo de dedicación', queryset=TiempoDedicacionDocente.objects.all().order_by('nombre'), required=True, error_messages={'required': 'Campo no debe estar vacío'}, widget=forms.Select(attrs={'class': 'form-control form-select', 'autocomplete': 'off'}))
    tipocriterio = forms.ChoiceField(label=u'Tipo Criterio', choices=TIPO_CRITERIO, required=True, error_messages={'required': 'Campo no debe estar vacío'}, widget=forms.Select(attrs={'class': 'form-control form-select', 'autocomplete': 'off'}))

    def clean(self, *args, **kwargs):
        cleaned_data = super(CriterioForm, self).clean(*args, **kwargs)
        return cleaned_data


class PeriodoActForm(MY_Form):
    from datetime import datetime
    nombre = forms.CharField(label='Nombre', required=True, error_messages={'required': 'Campo no debe estar vacío'}, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': '3', 'autocomplete': 'off'}))
    inicio = forms.DateField(input_formats=['%d-%m-%Y'], required=True,
                             error_messages={'required': 'Campo no debe estar vacío'}, initial=datetime.now(),
                             widget=forms.DateTimeInput(attrs={'class': 'form-control', 'autocomplete': 'off'},
                                                        format='%d-%m-%Y'), label='Fecha Inicio')
    fin = forms.DateField(input_formats=['%d-%m-%Y'], required=True,
                          error_messages={'required': 'Campo no debe estar vacío'}, initial=datetime.now(),
                          widget=forms.DateTimeInput(attrs={'class': 'form-control', 'autocomplete': 'off'},
                                                     format='%d-%m-%Y'), label='Fecha Fin')
    tipo = ModelChoiceField(label='Tipo de periodo', queryset=TipoPeriodo.objects.all().order_by('nombre'), required=True, error_messages={'required': 'Campo no debe estar vacío'}, widget=forms.Select(attrs={'class': 'form-control form-select', 'autocomplete': 'off'}))
    activo = forms.BooleanField(label='Activo?', initial=False, required=False, widget=forms.CheckboxInput(attrs={'class': ''}))

    def clean(self, *args, **kwargs):
        cleaned_data = super(PeriodoActForm, self).clean(*args, **kwargs)
        return cleaned_data


class EvaluacionComponentePeriodoFrom(MY_Form):
    from .models import EvaluacionComponente, PARCIAL
    componente = ModelChoiceField(label='Componente', queryset=EvaluacionComponente.objects.all(),
                                  required=True, error_messages={'required': 'Campo no debe estar vacío'},
                                  widget=forms.Select(attrs={'class': 'form-control form-select', 'autocomplete': 'off'}))
    parcial = forms.ChoiceField(label=u'Parcial', required=False, choices=PARCIAL,
                                widget=forms.Select(attrs={'class': 'form-select'}))
    nivelacion = forms.BooleanField(label='Compnenete aplica solo para nivelación?', initial=False, required=False,
                                    widget=forms.CheckboxInput(attrs={'class': ''}))


class TestSilaboSemanalForm(MY_Form):
    from datetime import datetime
    from .models import DetalleModeloEvaluativo, METODO_NAVEGACION
    #nombre = forms.CharField(label='Nombre', max_length=100, required=True, error_messages={'required': 'Campo no debe estar vacío'}, widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}))
    instruccion = forms.CharField(label='Insctrucción', required=True, error_messages={'required': 'Campo no debe estar vacío'}, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': '2', 'autocomplete': 'off'}))
    recomendacion = forms.CharField(label='Recomendación', required=True, error_messages={'required': 'Campo no debe estar vacío'}, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': '2', 'autocomplete': 'off'}))
    desde = forms.DateTimeField(input_formats=['%Y-%m-%dT%H:%M'], required=True, error_messages={'required': 'Campo no debe estar vacío'},
                                initial=datetime.now(),
                                widget=forms.DateTimeInput(attrs={'class': 'form-control', 'autocomplete': 'off', 'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
                                label='Desde')
    hasta = forms.DateTimeField(input_formats=['%Y-%m-%dT%H:%M'], required=True, error_messages={'required': 'Campo no debe estar vacío'},
                                initial=datetime.now(),
                                widget=forms.DateTimeInput(attrs={'class': 'form-control', 'autocomplete': 'off', 'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
                                label='Hasta')
    detallemodelo = ModelChoiceField(label='Item Evaluativo', queryset=DetalleModeloEvaluativo.objects.none(),
                                     required=True, error_messages={'required': 'Campo no debe estar vacío'},
                                     widget=forms.Select(attrs={'class': 'form-control form-select', 'autocomplete': 'off'}))
    vecesintento = forms.IntegerField(label=u'Número de intento', initial=1, required=True, error_messages={'required': 'Campo no debe estar vacío', 'invalid': 'Debe ser un número válido'}, widget=forms.NumberInput(attrs={'class': 'form-control', 'decimal': '0', 'autocomplete': 'off'}))
    tiempoduracion = forms.IntegerField(label=u'Tiempo de duración', help_text='El tiempo es en minutos (60 minutos equivale una hora)', initial=60, required=True, error_messages={'required': 'Campo no debe estar vacío', 'invalid': 'Debe ser un número válido'}, widget=forms.NumberInput(attrs={'class': 'form-control', 'decimal': '0', 'autocomplete': 'off'}))
    navegacion = forms.ChoiceField(label=u'Navegacion', required=True, choices=METODO_NAVEGACION, widget=forms.Select(attrs={'class': 'form-select'}))

    def item_evaluativo(self, detalles_modelo):
        self.fields['detallemodelo'].queryset = detalles_modelo

    def clean(self, *args, **kwargs):
        cleaned_data = super(TestSilaboSemanalForm, self).clean(*args, **kwargs)
        return cleaned_data


class ForoSilaboSemanalForm(MY_Form):
    from datetime import datetime
    from .models import DetalleModeloEvaluativo, TIPO_CONSOLIDACIONFORO, TIPO_FORO
    # nombre = forms.CharField(label='Nombre', required=True, max_length=500, error_messages={'required': 'Campo no debe estar vacío'}, widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}))
    instruccion = forms.CharField(label='Insctrucción', required=True, error_messages={'required': 'Campo no debe estar vacío'}, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': '2', 'autocomplete': 'off'}))
    objetivo = forms.CharField(label='Objetivo', required=True, error_messages={'required': 'Campo no debe estar vacío'}, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': '2', 'autocomplete': 'off'}))
    rubrica = forms.CharField(label='Rubrica', required=True, error_messages={'required': 'Campo no debe estar vacío'}, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': '2', 'autocomplete': 'off'}))
    recomendacion = forms.CharField(label='Recomendación', required=True, error_messages={'required': 'Campo no debe estar vacío'}, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': '2', 'autocomplete': 'off'}))
    desde = forms.DateTimeField(input_formats=['%Y-%m-%dT%H:%M'], required=True, error_messages={'required': 'Campo no debe estar vacío'},
                                initial=datetime.now(),
                                widget=forms.DateTimeInput(attrs={'class': 'form-control', 'autocomplete': 'off', 'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
                                label='Desde')
    hasta = forms.DateTimeField(input_formats=['%Y-%m-%dT%H:%M'], required=True, error_messages={'required': 'Campo no debe estar vacío'},
                                initial=datetime.now(),
                                widget=forms.DateTimeInput(attrs={'class': 'form-control', 'autocomplete': 'off', 'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
                                label='Hasta')

    detallemodelo = ModelChoiceField(label='Item Evaluativo', queryset=DetalleModeloEvaluativo.objects.none(),
                                     required=True, error_messages={'required': 'Campo no debe estar vacío'},
                                     widget=forms.Select(attrs={'class': 'form-control form-select', 'autocomplete': 'off'}))
    tipoforo = forms.ChoiceField(label=u'Tipo de foro', required=True, choices=TIPO_FORO, widget=forms.Select(attrs={'class': 'form-select'}))
    tipoconsolidacion = forms.ChoiceField(label=u'Tipo de consolidación', required=True, choices=TIPO_CONSOLIDACIONFORO, widget=forms.Select(attrs={'class': 'form-select'}))
    # calificar = forms.BooleanField(label='Foro calificado?', initial=False, required=False, widget=forms.CheckboxInput(attrs={'class': ''}))
    archivorubrica = ExtFileField(label='Archivo Rubrica', required=False,
                                  error_messages={'required': 'Campo no debe estar vacío'},
                                  help_text='Tamano Maximo permitido 30Mb, en formato pdf, doc, docx',
                                  ext_whitelist=(".pdf", ".doc", ".docx"),
                                  max_upload_size=30000000,
                                  widget=forms.FileInput(attrs={'accept': 'application/pdf, application/msword, application/vnd.openxmlformats-officedocument.wordprocessingml.document'}))
    archivoforo = ExtFileField(label='Archivo Foro', required=False,
                               error_messages={'required': 'Campo no debe estar vacío'},
                               help_text='Tamano Maximo permitido 30Mb, en formato pdf, doc, docx',
                               ext_whitelist=(".pdf", ".doc", ".docx"),
                               max_upload_size=30000000,
                               widget=forms.FileInput(attrs={'accept': 'application/pdf, application/msword, application/vnd.openxmlformats-officedocument.wordprocessingml.document'}))

    def item_evaluativo(self, detalles_modelo):
        self.fields['detallemodelo'].queryset = detalles_modelo

    def clean(self, *args, **kwargs):
        cleaned_data = super(ForoSilaboSemanalForm, self).clean(*args, **kwargs)
        return cleaned_data


class TareaSilaboSemanalForm(MY_Form):
    from datetime import datetime
    from .models import DetalleModeloEvaluativo, TIPO_CONSOLIDACIONFORO, TIPO_FORO
    objetivo = forms.CharField(label='Objetivo', required=True, error_messages={'required': 'Campo no debe estar vacío'}, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': '2', 'autocomplete': 'off'}))
    instruccion = forms.CharField(label='Insctrucción', required=True, error_messages={'required': 'Campo no debe estar vacío'}, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': '2', 'autocomplete': 'off'}))
    rubrica = forms.CharField(label='Rubrica', required=True, error_messages={'required': 'Campo no debe estar vacío'}, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': '2', 'autocomplete': 'off'}))
    recomendacion = forms.CharField(label='Recomendación', required=True, error_messages={'required': 'Campo no debe estar vacío'}, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': '2', 'autocomplete': 'off'}))
    desde = forms.DateTimeField(input_formats=['%Y-%m-%dT%H:%M'], required=True, error_messages={'required': 'Campo no debe estar vacío'},
                                initial=datetime.now(),
                                widget=forms.DateTimeInput(attrs={'class': 'form-control', 'autocomplete': 'off', 'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
                                label='Desde')
    hasta = forms.DateTimeField(input_formats=['%Y-%m-%dT%H:%M'], required=True, error_messages={'required': 'Campo no debe estar vacío'},
                                initial=datetime.now(),
                                widget=forms.DateTimeInput(attrs={'class': 'form-control', 'autocomplete': 'off', 'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
                                label='Hasta')

    detallemodelo = ModelChoiceField(label='Item Evaluativo', queryset=DetalleModeloEvaluativo.objects.none(),
                                     required=True, error_messages={'required': 'Campo no debe estar vacío'},
                                     widget=forms.Select(attrs={'class': 'form-control form-select', 'autocomplete': 'off'}))
    word = forms.BooleanField(label='Word?', initial=False, required=False,
                              widget=forms.CheckboxInput(attrs={'class': ''}))
    pdf = forms.BooleanField(label='Pdf?', initial=False, required=False,
                             widget=forms.CheckboxInput(attrs={'class': ''}))
    excel = forms.BooleanField(label='Excel?', initial=False, required=False,
                               widget=forms.CheckboxInput(attrs={'class': ''}))
    powerpoint = forms.BooleanField(label='PowerPoint?', initial=False, required=False,
                                    widget=forms.CheckboxInput(attrs={'class': ''}))
    # calificar = forms.BooleanField(label='Tarea calificado?', initial=False, required=False, widget=forms.CheckboxInput(attrs={'class': ''}))
    archivotareasilabo = ExtFileField(label='Archivo tarea', required=False,
                                      error_messages={'required': 'Campo no debe estar vacío'},
                                      help_text='Tamano Maximo permitido 30Mb, en formato pdf, doc, docx',
                                      ext_whitelist=(".pdf", ".doc", ".docx"),
                                      max_upload_size=30000000,
                                      widget=forms.FileInput(attrs={'accept': 'application/pdf, application/msword, application/vnd.openxmlformats-officedocument.wordprocessingml.document'}))
    archivorubrica = ExtFileField(label='Archivo Rubrica', required=False,
                                  error_messages={'required': 'Campo no debe estar vacío'},
                                  help_text='Tamano Maximo permitido 30Mb, en formato pdf, doc, docx',
                                  ext_whitelist=(".pdf", ".doc", ".docx"),
                                  max_upload_size=30000000,
                                  widget=forms.FileInput(attrs={'accept': 'application/pdf, application/msword, application/vnd.openxmlformats-officedocument.wordprocessingml.document'}))

    def item_evaluativo(self, detalles_modelo):
        self.fields['detallemodelo'].queryset = detalles_modelo

    def clean(self, *args, **kwargs):
        cleaned_data = super(TareaSilaboSemanalForm, self).clean(*args, **kwargs)
        return cleaned_data


class BannerMateriaForm(MY_Form):
    banner = ExtFileField(label='Seleccione archivo', required=True,
                          error_messages={'required': 'Campo no debe estar vacío'},
                          help_text='Tamano Maximo permitido 4Mb, en formato jpg, png',
                          ext_whitelist=(".jpg",".png"),
                          max_upload_size=4194304,
                          widget=forms.FileInput({'accept': 'image/jpeg, image/jpg, image/png', 'class': 'dropify'}))


class EnfoqueMetodologicoForm(MY_Form):
    inicio = forms.CharField(label='Inicio', required=True,
                             error_messages={'required': 'Campo no debe estar vacío'},
                             widget=forms.Textarea(attrs={'class': 'form-control', 'rows': '5', 'autocomplete': 'off'})
                             )
    desarrollo = forms.CharField(label='Desarrollo', required=True,
                                 error_messages={'required': 'Campo no debe estar vacío'},
                                 widget=forms.Textarea(attrs={'class': 'form-control', 'rows': '5', 'autocomplete': 'off'})
                                 )
    cierre = forms.CharField(label='Cierre', required=True,
                             error_messages={'required': 'Campo no debe estar vacío'},
                             widget=forms.Textarea(attrs={'class': 'form-control', 'rows': '5', 'autocomplete': 'off'})
                             )


class CriterioDocenteForm(MY_Form):
    from datetime import datetime
    profesor = ModelChoiceField(label='Profesor', queryset=Profesor.objects.filter(activo=True).order_by('persona'), required=True, error_messages={'required': 'Campo no debe estar vacío'}, widget=forms.Select(attrs={'class': 'form-control form-select', 'autocomplete': 'off'}))
    desde = forms.DateField(input_formats=['%d-%m-%Y'], required=True,
                            error_messages={'required': 'Campo no debe estar vacío'}, initial=datetime.now(),
                            widget=forms.DateTimeInput(attrs={'class': 'form-control', 'autocomplete': 'off', 'type': 'date'},
                                                       format='%d-%m-%Y'), label='Desde')
    hasta = forms.DateField(input_formats=['%d-%m-%Y'], required=True,
                            error_messages={'required': 'Campo no debe estar vacío'}, initial=datetime.now(),
                            widget=forms.DateTimeInput(attrs={'class': 'form-control', 'autocomplete': 'off', 'type': 'date'},
                                                       format='%d-%m-%Y'), label='Hasta')

    def clean(self, *args, **kwargs):
        cleaned_data = super(CriterioDocenteForm, self).clean(*args, **kwargs)
        return cleaned_data

class EstudianteFamiliarForm(forms.Form):
    inicio = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha Inicio")
    fin = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha Fin")
    carrera = forms.ModelChoiceField(Carrera.objects.filter(carrera=True).order_by('nombre'), label='Carrera')
    todos = forms.BooleanField(label='Todos:', required=False)
class RVisitaBiblioForm(forms.Form):
    inicio = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label='Fecha Inicio')
    fin = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label='Fecha Fin')
    sede = forms.ModelChoiceField(Sede.objects.filter(solobodega=False).order_by('nombre'), label='Sede')

class EstudiantesProgramaVinculacionForm(forms.Form):
    tipo = forms.CharField(label='Nombre de Proyecto:')
    inicio = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha Inicio")
    fin = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha Fin")

class RangoFacturasxFormaPagoForm(forms.Form):
    inicio = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label='Fecha Inicio')
    fin = forms.DateField(input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y'), label='Fecha Fin')
    formapago=forms.BooleanField(label='Incluir forma de pago?', required=False)