# -*- coding: latin-1 -*-
from decimal import Decimal

from django.db import models
from django.db.models import Sum
from med.models import PersonaEstadoCivil
from sga.models import Inscripcion, SectorVivienda, Canton, TenenciaVivienda, TipoIngresoVivienda, TipoEgresoVivienda, RubroOtro
from datetime import datetime
from settings import SEXO_FEMENINO,SEXO_MASCULINO, CARRERAS_ID_EXCLUIDAS_INEC, TIPO_CONGRESO_RUBRO

#Query y Consultas - Estrato Nivel SocioEconomico

def cantidad_total_gruposocioeconomico(gruposocioe):
    return InscripcionFichaSocioeconomica.objects.filter(grupoeconomico=gruposocioe).count()

#Grupos SocioEconomicos por carreras
def cantidad_gruposocioeconomico_carrera(gruposocioe, carrera,inicio,fin):
    return InscripcionFichaSocioeconomica.objects.filter(grupoeconomico=gruposocioe, inscripcion__carrera=carrera, inscripcion__persona__usuario__is_active=True,inscripcion__fecha__gte=inicio, inscripcion__fecha__lte=fin).count()
def cantidad_gruposocioeconomico_carrera_general(gruposocioe, carrera):
    return InscripcionFichaSocioeconomica.objects.filter(grupoeconomico=gruposocioe, inscripcion__carrera=carrera, inscripcion__persona__usuario__is_active=True).count()
#Grupos SocioEconomicos por coordinaciones
def cantidad_gruposocioeconomico_coordinacion(gruposocioe, coordinacion,inicio,fin):
    return InscripcionFichaSocioeconomica.objects.filter(grupoeconomico=gruposocioe, inscripcion__carrera__in=coordinacion.carrera.all(), inscripcion__persona__usuario__is_active=True,inscripcion__fecha__gte=inicio, inscripcion__fecha__lte=fin).count()

#Niveles de Escolaridad del Jefe de Hogar por carreras
def cantidad_nivel_educacion_jefehogar_carrera(nivelesc, carrera,inicio,fin):
    return InscripcionFichaSocioeconomica.objects.filter(niveljefehogar=nivelesc, inscripcion__carrera=carrera, inscripcion__persona__usuario__is_active=True,inscripcion__fecha__gte=inicio, inscripcion__fecha__lte=fin).count()
#Niveles de Escolaridad del Jefe de Hogar por coordinaciones
def cantidad_nivel_educacion_jefehogar_coordinacion(nivelesc, coordinacion,inicio,fin):
    return InscripcionFichaSocioeconomica.objects.filter(niveljefehogar=nivelesc, inscripcion__persona__usuario__is_active=True, inscripcion__carrera__in=coordinacion.carrera.all(),inscripcion__fecha__gte=inicio, inscripcion__fecha__lte=fin).count()

#Tipos de Hogar de estudiantes por carreras
def cantidad_tipo_hogar_carrera(th, carrera,inicio,fin):
    return InscripcionFichaSocioeconomica.objects.filter(tipohogar=th, inscripcion__carrera=carrera, inscripcion__persona__usuario__is_active=True,inscripcion__fecha__gte=inicio, inscripcion__fecha__lte=fin).count()
#Tipos de Hogar de estudiantes por coordinaciones
def cantidad_tipo_hogar_coordinacion(th, coordinacion,inicio,fin):
    return InscripcionFichaSocioeconomica.objects.filter(tipohogar=th, inscripcion__persona__usuario__is_active=True, inscripcion__carrera__in=coordinacion.carrera.all(),inscripcion__fecha__gte=inicio, inscripcion__fecha__lte=fin).count()

#Dependencia Economica de estudiantes por carreras
def cantidad_SIdependientes_carrera(carrera,inicio,fin):
    return InscripcionFichaSocioeconomica.objects.filter(esdependiente=True, inscripcion__carrera=carrera, inscripcion__persona__usuario__is_active=True,inscripcion__fecha__gte=inicio, inscripcion__fecha__lte=fin).count()
def cantidad_NOdependientes_carrera(carrera,inicio,fin):
    return InscripcionFichaSocioeconomica.objects.filter(esdependiente=False, inscripcion__carrera=carrera, inscripcion__persona__usuario__is_active=True,inscripcion__fecha__gte=inicio, inscripcion__fecha__lte=fin).count()
#Dependencia Economica de estudiantes por coordinaciones
def cantidad_SIdependientes_coordinacion(coordinacion,inicio,fin):
    return InscripcionFichaSocioeconomica.objects.filter(esdependiente=True, inscripcion__persona__usuario__is_active=True, inscripcion__carrera__in=coordinacion.carrera.all(),inscripcion__fecha__gte=inicio, inscripcion__fecha__lte=fin).count()
def cantidad_NOdependientes_coordinacion(coordinacion,inicio,fin):
    return InscripcionFichaSocioeconomica.objects.filter(esdependiente=False, inscripcion__persona__usuario__is_active=True, inscripcion__carrera__in=coordinacion.carrera.all(),inscripcion__fecha__gte=inicio, inscripcion__fecha__lte=fin).count()

#Cabezas de Familias estudiantes por carreras
def cantidad_SIcabezasf_carrera(carrera,inicio,fin):
    return InscripcionFichaSocioeconomica.objects.filter(escabezafamilia=True, inscripcion__carrera=carrera, inscripcion__persona__usuario__is_active=True,inscripcion__fecha__gte=inicio, inscripcion__fecha__lte=fin).count()

def cantidad_SIcabezasf_carrera_mujer(carrera,inicio,fin):
    return InscripcionFichaSocioeconomica.objects.filter(escabezafamilia=True, inscripcion__carrera=carrera, inscripcion__persona__usuario__is_active=True,inscripcion__persona__sexo__id=SEXO_FEMENINO,inscripcion__fecha__gte=inicio, inscripcion__fecha__lte=fin).count()

def cantidad_beca_SIcabezasf_carrera(carrera,inicio,fin,sexo):
    return InscripcionFichaSocioeconomica.objects.filter(inscripcion__matricula__becado=True,inscripcion__matricula__fecha__gte=inicio,inscripcion__matricula__fecha__lte=fin,escabezafamilia=True, inscripcion__carrera=carrera, inscripcion__persona__usuario__is_active=True,inscripcion__persona__sexo__id=sexo,inscripcion__fecha__gte=inicio, inscripcion__fecha__lte=fin).count()

def cantidad_total_madres_solteras(inicio,fin):
    return Inscripcion.objects.filter(persona__personaextension__estadocivil__id=1,persona__usuario__is_active=True,fecha__gte=inicio, fecha__lte=fin,persona__personaextension__hijos__gt=0).exclude(carrera__id__in=CARRERAS_ID_EXCLUIDAS_INEC).exclude(persona__personaextension__conyuge=True).count()

def cantidad_total_beca_madres_solteras(inicio,fin):
    return Inscripcion.objects.filter(matricula__becado=True,persona__personaextension__estadocivil__id=1,persona__usuario__is_active=True,fecha__gte=inicio, fecha__lte=fin,persona__personaextension__hijos__gt=0).exclude(carrera__id__in=CARRERAS_ID_EXCLUIDAS_INEC).exclude(persona__personaextension__conyuge=True).count()

def cantidad_SIcabezasf_carrera_hombre(carrera,inicio,fin):
    return InscripcionFichaSocioeconomica.objects.filter(escabezafamilia=True, inscripcion__carrera=carrera, inscripcion__persona__usuario__is_active=True,inscripcion__persona__sexo__id=SEXO_MASCULINO,inscripcion__fecha__gte=inicio, inscripcion__fecha__lte=fin).count()
def cantidad_NOcabezasf_carrera(carrera,inicio,fin):
    return InscripcionFichaSocioeconomica.objects.filter(escabezafamilia=False, inscripcion__carrera=carrera, inscripcion__persona__usuario__is_active=True,inscripcion__fecha__gte=inicio, inscripcion__fecha__lte=fin).count()
#Cabezas de Familias estudiantes por coordinaciones
def cantidad_SIcabezasf_coordinacion(coordinacion,inicio,fin):
    return InscripcionFichaSocioeconomica.objects.filter(escabezafamilia=True, inscripcion__persona__usuario__is_active=True, inscripcion__carrera__in=coordinacion.carrera.all(),inscripcion__fecha__gte=inicio, inscripcion__fecha__lte=fin).count()
def cantidad_NOcabezasf_coordinacion(coordinacion,inicio,fin):
    return InscripcionFichaSocioeconomica.objects.filter(escabezafamilia=False, inscripcion__persona__usuario__is_active=True, inscripcion__carrera__in=coordinacion.carrera.all(),inscripcion__fecha__gte=inicio, inscripcion__fecha__lte=fin).count()
# OCU 31-01-2019 solicitud de bienestar
def cantidad_mayorcinco_miembros_carrera(thogar,carrera,inicio,fin):
    return InscripcionFichaSocioeconomica.objects.filter(cantidadmiembros__gte=5, tipohogar=thogar,inscripcion__carrera=carrera, inscripcion__persona__usuario__is_active=True,inscripcion__fecha__gte=inicio, inscripcion__fecha__lte=fin).count()

def cantidad_total_casados_xsexo(carrera,sexo,edad,inicio,fin):
    hoy = inicio.year
    edad=edad
    lista_estd=[]
    estudiantes = Inscripcion.objects.filter(persona__sexo=sexo,persona__personaextension__estadocivil__id=2,carrera=carrera,persona__usuario__is_active=True,fecha__gte=inicio, fecha__lte=fin).values('persona__nacimiento')
    for est in estudiantes:
        if hoy - est['persona__nacimiento'].year < int(edad):
            lista_estd.append(est)
    return len(lista_estd)

def cantidad_total_estudiantes_congreso(inicio,fin):
    estudiantes = RubroOtro.objects.filter(tipo__id=TIPO_CONGRESO_RUBRO,rubro__fecha__gte=inicio,rubro__fecha__lte=fin,rubro__cancelado=True).exclude(rubro__inscripcion__carrera__id__in=CARRERAS_ID_EXCLUIDAS_INEC).distinct('rubro__inscripcion').count()
    return estudiantes

def cantidad_total_mujeresxedad(carrera,edad,inicio,fin):
    hoy = inicio.year
    edad=edad
    lista_mujeres=[]
    mujeres = Inscripcion.objects.filter(persona__sexo__id=SEXO_FEMENINO,carrera=carrera,persona__usuario__is_active=True,fecha__gte=inicio, fecha__lte=fin).values('persona__nacimiento')
    for mujer in mujeres:
        if hoy - mujer['persona__nacimiento'].year < int(edad):
            lista_mujeres.append(mujer)
    return len(lista_mujeres)

def cantidad_total_menoresedad(sexo,inicio,fin):
    hoy = inicio.year
    lista_menoresedad=[]
    menores = Inscripcion.objects.filter(persona__sexo=sexo,persona__usuario__is_active=True,fecha__gte=inicio, fecha__lte=fin).exclude(id__in=CARRERAS_ID_EXCLUIDAS_INEC).values('persona__nacimiento')
    for menor in menores:
        if hoy - menor['persona__nacimiento'].year < (18):
            lista_menoresedad.append(menor)
    return len(lista_menoresedad)


class FormaTrabajo(models.Model):
    nombre = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'Forma de Trabajo'
        verbose_name_plural = 'Formas de Trabajo'

    def __str__(self):
        return self.nombre

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.nombre = self.nombre.upper()
        super(FormaTrabajo, self).save(force_insert, force_update, using, update_fields)

class ParentezcoPersona(models.Model):
    nombre = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'Parentezco'
        verbose_name_plural = 'Parentezcos'

    def __str__(self):
        return self.nombre

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.nombre = self.nombre.upper()
        super(ParentezcoPersona, self).save(force_insert, force_update, using, update_fields)

class PersonaSustentaHogar(models.Model):
    persona = models.CharField(max_length=200)
    parentezco = models.ForeignKey(ParentezcoPersona, on_delete=models.CASCADE)
    formatrabajo = models.ForeignKey(FormaTrabajo, on_delete=models.CASCADE)
    ingresomensual = models.FloatField(default=0.00)

    class Meta:
        verbose_name = 'Persona sustenta Hogar'
        verbose_name_plural = 'Personas sustentan Hogar'

    def __str__(self):
        return self.persona + ' ' + str(self.formatrabajo) + ' ($' + str(self.ingresomensual) + ')'

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.persona = self.persona.upper()
        super(PersonaSustentaHogar, self).save(force_insert, force_update, using, update_fields)

class PersonaCubreGasto(models.Model):
    nombre = models.CharField(max_length=100)
    nombrematriz = models.CharField(max_length=100,blank=True,null=True)

    class Meta:
        verbose_name = 'Persona cubre gasto estudiante'
        verbose_name_plural = 'Personas cubren gastos estudiantes'

    def __str__(self):
        return self.nombre

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.nombre = self.nombre.upper()
        self.nombrematriz = self.nombrematriz.upper()
        super(PersonaCubreGasto, self).save(force_insert, force_update, using, update_fields)

class TipoHogar(models.Model):
    nombre = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'Tipo de Hogar'
        verbose_name_plural = 'Tipos de Hogares'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

    #Para Estadisticas Graficos Niveles Socioeconomicos
    def cantidad_total_estudiantes(self,anno):
        inicio=datetime.strptime('01-01-'+str(anno[2:4]), '%d-%m-%y').date()
        fin=datetime.strptime('31-12-'+str(anno[2:4]), '%d-%m-%y').date()
        return InscripcionFichaSocioeconomica.objects.filter(tipohogar=self,inscripcion__fecha__gte=inicio, inscripcion__fecha__lte=fin).count()

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.nombre = self.nombre.upper()
        super(TipoHogar, self).save(force_insert, force_update, using, update_fields)

class TipoVivienda(models.Model):
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=4, blank=True, null=True)
    puntaje = models.FloatField(default=0)

    class Meta:
        verbose_name = 'Tipo de Vivienda'
        verbose_name_plural = 'Tipos de Viviendas'

    def __str__(self):
        return '[' + self.codigo + ']' + ' ' + self.nombre if self.codigo else self.nombre

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.nombre = self.nombre.upper()
        self.codigo = self.codigo.upper()
        super(TipoVivienda, self).save(force_insert, force_update, using, update_fields)

class MaterialPared(models.Model):
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=4, blank=True, null=True)
    puntaje = models.FloatField(default=0)

    class Meta:
        verbose_name = 'Material Predomina en Pared'
        verbose_name_plural = 'Materiales Predominan en Paredes'

    def __str__(self):
        return '[' + self.codigo + ']' + ' ' + self.nombre if self.codigo else self.nombre

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.nombre = self.nombre.upper()
        self.codigo = self.codigo.upper()
        super(MaterialPared, self).save(force_insert, force_update, using, update_fields)

class MaterialPiso(models.Model):
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=4, blank=True, null=True)
    puntaje = models.FloatField(default=0)

    class Meta:
        verbose_name = 'Material Predomina en Piso'
        verbose_name_plural = 'Materiales Predominan en Pisos'

    def __str__(self):
        return '[' + self.codigo + ']' + ' ' + self.nombre if self.codigo else self.nombre

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.nombre = self.nombre.upper()
        self.codigo = self.codigo.upper()
        super(MaterialPiso, self).save(force_insert, force_update, using, update_fields)

class CantidadBannoDucha(models.Model):
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=4, blank=True, null=True)
    puntaje = models.FloatField(default=0)

    class Meta:
        verbose_name = u'Cantidad Baños con Ducha'
        verbose_name_plural = u'Cantidad de Baños con Ducha'

    def __str__(self):
        return '[' + self.codigo + ']' + ' ' + self.nombre if self.codigo else self.nombre

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.nombre = self.nombre.upper()
        self.codigo = self.codigo.upper()
        super(CantidadBannoDucha, self).save(force_insert, force_update, using, update_fields)

class TipoServicioHigienico(models.Model):
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=4, blank=True, null=True)
    puntaje = models.FloatField(default=0)

    class Meta:
        verbose_name = 'Tipo de Servicio Higienico'
        verbose_name_plural = 'Tipos de Servicio Higienico'

    def __str__(self):
        return '[' + self.codigo + ']' + ' ' + self.nombre if self.codigo else self.nombre

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.nombre = self.nombre.upper()
        self.codigo = self.codigo.upper()
        super(TipoServicioHigienico, self).save(force_insert, force_update, using, update_fields)

class CantidadCelularHogar(models.Model):
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=4, blank=True, null=True)
    puntaje = models.FloatField(default=0)

    class Meta:
        verbose_name = 'Cantidad de Celulares en Hogar'
        verbose_name_plural = 'Cantidad de Celulares en Hogar'

    def __str__(self):
        return '[' + self.codigo + ']' + ' ' + self.nombre if self.codigo else self.nombre

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.nombre = self.nombre.upper()
        self.codigo = self.codigo.upper()
        super(CantidadCelularHogar, self).save(force_insert, force_update, using, update_fields)

class CantidadTVColorHogar(models.Model):
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=4, blank=True, null=True)
    puntaje = models.FloatField(default=0)

    class Meta:
        verbose_name = 'Cantidad de Televisores a color en Hogar'
        verbose_name_plural = 'Cantidad de Televisores a Color en Hogar'

    def __str__(self):
        return '[' + self.codigo + ']' + ' ' + self.nombre if self.codigo else self.nombre

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.nombre = self.nombre.upper()
        self.codigo = self.codigo.upper()
        super(CantidadTVColorHogar, self).save(force_insert, force_update, using, update_fields)

class CantidadVehiculoHogar(models.Model):
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=4, blank=True, null=True)
    puntaje = models.FloatField(default=0)

    class Meta:
        verbose_name = 'Cantidad de Vehiculo en Hogar'
        verbose_name_plural = 'Cantidad de Vehiculos en Hogar'

    def __str__(self):
        return '[' + self.codigo + ']' + ' ' + self.nombre if self.codigo else self.nombre

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.nombre = self.nombre.upper()
        self.codigo = self.codigo.upper()
        super(CantidadVehiculoHogar, self).save(force_insert, force_update, using, update_fields)

class NivelEstudio(models.Model):
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=4, blank=True, null=True)
    puntaje = models.FloatField(default=0)

    class Meta:
        verbose_name = 'Nivel de Estudio'
        verbose_name_plural = 'Niveles de Estudios'
        ordering = ['puntaje']

    #Para Estadisticas Graficos Niveles Socioeconomicos
    def cantidad_total_estudiantes(self,anno):
        inicio=datetime.strptime('01-01-'+str(anno[2:4]), '%d-%m-%y').date()
        fin=datetime.strptime('31-12-'+str(anno[2:4]), '%d-%m-%y').date()
        return InscripcionFichaSocioeconomica.objects.filter(niveljefehogar=self,inscripcion__fecha__gte=inicio, inscripcion__fecha__lte=fin).count()

    def __str__(self):
        return '[' + self.codigo + ']' + ' ' + self.nombre if self.codigo else self.nombre

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.nombre = self.nombre.upper()
        self.codigo = self.codigo.upper()
        super(NivelEstudio, self).save(force_insert, force_update, using, update_fields)

class OcupacionJefeHogar(models.Model):
    nombre = models.CharField(max_length=200)
    codigo = models.CharField(max_length=4, blank=True, null=True)
    puntaje = models.FloatField(default=0)

    class Meta:
        verbose_name = 'Ocupacion - Jefe Hogar'
        verbose_name_plural = 'Ocupaciones - Jefes Hogares'

    def __str__(self):
        return '[' + self.codigo + ']' + ' ' + self.nombre if self.codigo else self.nombre

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.nombre = self.nombre.upper()
        self.codigo = self.codigo.upper()
        super(OcupacionJefeHogar, self).save(force_insert, force_update, using, update_fields)

class GrupoSocioEconomico(models.Model):
    codigo = models.CharField(max_length=2)
    nombre = models.CharField(max_length=100)
    umbralinicio = models.FloatField(default=0)
    umbralfin = models.FloatField(default=0)

    class Meta:
        verbose_name = 'Grupo SocioEconomico'
        verbose_name_plural = 'Grupos SocioEconomicos'
        ordering = ['-umbralinicio']

    def __str__(self):
        return self.codigo + ' (' + self.nombre + ') Umbrales: De ' + str(self.umbralinicio) + ' a ' + str(self.umbralfin)

    def nombre_corto(self):
        return self.codigo + ' (' + self.nombre + ')'

    #Para Estadisticas Graficos Niveles Socioeconomicos
    def cantidad_total_estudiantes(self,anno):
        inicio=datetime.strptime('01-01-'+str(anno[2:4]), '%d-%m-%y').date()
        fin=datetime.strptime('31-12-'+str(anno[2:4]), '%d-%m-%y').date()
        return InscripcionFichaSocioeconomica.objects.filter(grupoeconomico=self,inscripcion__fecha__gte=inicio, inscripcion__fecha__lte=fin).count()
    def cantidad_total_estudiantes_general(self):
        return InscripcionFichaSocioeconomica.objects.filter(grupoeconomico=self).count()
    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.nombre = self.nombre.upper()
        self.codigo = self.codigo.upper()
        super(GrupoSocioEconomico, self).save(force_insert, force_update, using, update_fields)

class OcupacionEstudiante(models.Model):
    nombre = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'Ocupacion de Estudiante'
        verbose_name_plural = 'Ocupaciones de Estudiantes'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.nombre = self.nombre.upper()
        super(OcupacionEstudiante, self).save(force_insert, force_update, using, update_fields)

class IngresosEstudiante(models.Model):
    nombre = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'Ingreso de Estudiante'
        verbose_name_plural = 'Ingresos de Estudiantes'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.nombre = self.nombre.upper()
        super(IngresosEstudiante, self).save(force_insert, force_update, using, update_fields)

class BonoFmlaEstudiante(models.Model):
    nombre = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'Bono Fmla de Estudiante'
        verbose_name_plural = 'Bonos Fmla de Estudiantes'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.nombre = self.nombre.upper()
        super(BonoFmlaEstudiante, self).save(force_insert, force_update, using, update_fields)

class InscripcionFichaSocioeconomica(models.Model):
    inscripcion = models.ForeignKey(Inscripcion, on_delete=models.CASCADE)
    puntajetotal = models.FloatField(default=0)
    grupoeconomico = models.ForeignKey(GrupoSocioEconomico, blank=True, null=True, on_delete=models.CASCADE)

    #Estructura Familiar
    tipohogar = models.ForeignKey(TipoHogar, blank=True, null=True, on_delete=models.CASCADE)

    #Gastos generales
    escabezafamilia = models.BooleanField(default=False)
    esdependiente = models.BooleanField(default=False)
    personacubregasto = models.ForeignKey(PersonaCubreGasto, blank=True, null=True, on_delete=models.CASCADE)
    otroscubregasto = models.CharField(max_length=200, blank=True, null=True)   #En caso de escoger otros cubre gastos, especificar en este campo
    sustentahogar = models.ManyToManyField(PersonaSustentaHogar, blank=True)

    #Caracteristicas de la Vivienda
    tipovivienda = models.ForeignKey(TipoVivienda, blank=True, null=True, on_delete=models.CASCADE)
    val_tipovivienda = models.FloatField(default=0)
    materialpared = models.ForeignKey(MaterialPared, blank=True, null=True, on_delete=models.CASCADE)
    val_materialpared = models.FloatField(default=0)
    materialpiso = models.ForeignKey(MaterialPiso, blank=True, null=True, on_delete=models.CASCADE)
    val_materialpiso = models.FloatField(default=0)
    cantbannoducha = models.ForeignKey(CantidadBannoDucha, blank=True, null=True, on_delete=models.CASCADE)
    val_cantbannoducha = models.FloatField(default=0)
    tiposervhig = models.ForeignKey(TipoServicioHigienico, blank=True, null=True, on_delete=models.CASCADE)
    val_tiposervhig = models.FloatField(default=0)

    #Acceso a la Tecnologia
    tieneinternet = models.BooleanField(default=False)
    val_tieneinternet = models.FloatField(default=0)
    tienedesktop = models.BooleanField(default=False)
    val_tienedesktop = models.FloatField(default=0)
    tienelaptop = models.BooleanField(default=False)
    val_tienelaptop = models.FloatField(default=0)
    cantcelulares = models.ForeignKey(CantidadCelularHogar, blank=True, null=True, on_delete=models.CASCADE)
    val_cantcelulares = models.FloatField(default=0)

    #Posesion de bienes
    tienetelefconv = models.BooleanField(default=False)
    val_tienetelefconv = models.FloatField(default=0)
    tienecocinahorno = models.BooleanField(default=False)
    val_tienecocinahorno = models.FloatField(default=0)
    tienerefrig = models.BooleanField(default=False)
    val_tienerefrig = models.FloatField(default=0)
    tienelavadora = models.BooleanField(default=False)
    val_tienelavadora = models.FloatField(default=0)
    tienemusica = models.BooleanField(default=False)
    val_tienemusica = models.FloatField(default=0)
    canttvcolor= models.ForeignKey(CantidadTVColorHogar, blank=True, null=True, on_delete=models.CASCADE)
    val_canttvcolor= models.FloatField(default=0)
    cantvehiculos = models.ForeignKey(CantidadVehiculoHogar, blank=True, null=True, on_delete=models.CASCADE)
    val_cantvehiculos = models.FloatField(default=0)

    #Habitos de consumo
    compravestcc = models.BooleanField(default=False)
    val_compravestcc = models.FloatField(default=0)
    usainternetseism = models.BooleanField(default=False)
    val_usainternetseism = models.FloatField(default=0)
    usacorreonotrab = models.BooleanField(default=False)
    val_usacorreonotrab = models.FloatField(default=0)
    registroredsocial = models.BooleanField(default=False)
    val_registroredsocial = models.FloatField(default=0)
    leidolibrotresm = models.BooleanField(default=False)
    val_leidolibrotresm = models.FloatField(default=0)

    #Nivel de estudios jefe de hogar
    niveljefehogar = models.ForeignKey(NivelEstudio, blank=True, null=True, on_delete=models.CASCADE)
    val_niveljefehogar = models.FloatField(default=0)

    #Actividad Economica del hogar
    alguienafiliado = models.BooleanField(default=False)
    val_alguienafiliado = models.FloatField(default=0)
    alguienseguro = models.BooleanField(default=False)
    val_alguienseguro = models.FloatField(default=0)
    ocupacionjefehogar = models.ForeignKey(OcupacionJefeHogar, blank=True, null=True, on_delete=models.CASCADE)
    val_ocupacionjefehogar = models.FloatField(default=0)
    p_msoltera = models.BooleanField(default=False)
    num_hijos=models.IntegerField(blank=True,null=True,default=0)

    #Nuevos datos segun matriz 2017 OCU 08-dic-2017
    ocupacionestudiante = models.ForeignKey(OcupacionEstudiante, blank=True, null=True, on_delete=models.CASCADE)
    ingresoestudiante = models.ForeignKey(IngresosEstudiante, blank=True, null=True, on_delete=models.CASCADE)
    bonofmlaestudiante = models.ForeignKey(BonoFmlaEstudiante, blank=True, null=True, on_delete=models.CASCADE)
    cantidadmiembros=models.IntegerField(blank=True,null=True)
    verificado = models.BooleanField(default=False)
    fechaverificado = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = 'Estudiante - Ficha SocioEconomica'
        verbose_name_plural = 'Estudiantes - Fichas SocioEconomicas'

    def __str__(self):
        return str(self.inscripcion) + ' - ' + str(self.tipohogar)

    def total_ingresos_sustentahogar(self):
        if self.sustentahogar.all().count():
            return self.sustentahogar.all().aggregate(Sum('ingresomensual'))['ingresomensual__sum']
        return 0

    def calcular_puntaje_total(self):
        return self.val_tipovivienda + self.val_materialpared + self.val_materialpiso + self.val_cantbannoducha + self.val_tiposervhig + \
            self.val_tieneinternet + self.val_tienedesktop + self.val_tienelaptop + self.val_cantcelulares + \
            self.val_tienetelefconv + self.val_tienecocinahorno + self.val_tienerefrig + self.val_tienelavadora + self.val_tienemusica + self.val_canttvcolor + self.val_cantvehiculos + \
            self.val_compravestcc + self.val_usainternetseism + self.val_usacorreonotrab + self.val_registroredsocial + self.val_leidolibrotresm + \
            self.val_niveljefehogar + self.val_alguienafiliado + self.val_alguienseguro + self.val_ocupacionjefehogar

    def determinar_grupo_economico(self):
        return GrupoSocioEconomico.objects.filter(umbralinicio__lte=self.puntajetotal, umbralfin__gte=self.puntajetotal)[:1].get() if GrupoSocioEconomico.objects.filter(umbralinicio__lte=self.puntajetotal, umbralfin__gte=self.puntajetotal).exists() else None

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.otroscubregasto: self.otroscubregasto = self.otroscubregasto.upper()
        self.puntajetotal = self.calcular_puntaje_total()
        self.grupoeconomico = self.determinar_grupo_economico()
        super(InscripcionFichaSocioeconomica, self).save(force_insert, force_update, using, update_fields)


class InscripcionFichaSocioEconomicaBeca(models.Model):
    inscripcion = models.ForeignKey(Inscripcion, blank=True,null=True, on_delete=models.CASCADE)
    edad = models.IntegerField(blank=True, null= True)
    estadocivil = models.ForeignKey(PersonaEstadoCivil,blank=True,null=True, on_delete=models.CASCADE)
    ciudad = models.ForeignKey(Canton,blank=True,null=True, on_delete=models.CASCADE)
    direccion = models.CharField(max_length=300,blank=True,null=True)
    numero = models.CharField(max_length=200,blank=True,null=True)
    sector = models.ForeignKey(SectorVivienda,null=True,blank=True, on_delete=models.CASCADE)
    telefono = models.CharField(max_length=200,blank=True,null=True)
    celular = models.CharField(max_length=200,blank=True,null=True)
    email = models.CharField(max_length=200,blank=True,null=True)
    tipovivienda = models.ForeignKey(TipoVivienda, null=True, blank=True, on_delete=models.CASCADE)
    descriptipo = models.CharField(max_length=300,blank=True,null=True)
    personacubregasto = models.ForeignKey(PersonaCubreGasto,blank=True,null=True, on_delete=models.CASCADE)
    descripcubregasto = models.CharField(max_length=300,blank=True,null=True)
    teneciaviviend = models.ForeignKey(TenenciaVivienda, null=True, blank=True, on_delete=models.CASCADE)
    completo = models.BooleanField(default=False)
    datecomple = models.DateTimeField(blank=True, null=True)
    croquis = models.FileField(upload_to='beca/%Y/%m/%d', max_length=100,null = True,blank=True)
    emailpersona = models.CharField(max_length=200,blank=True,null=True)
    verificado = models.BooleanField(default=False)
    fechaverificado = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = 'Estudiante - Ficha SocioEconomica para Beca'
        verbose_name_plural = 'Estudiantes - Fichas SocioEconomicas para Becas'

    def __str__(self):
        return str(self.inscripcion)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.direccion: self.direccion = self.direccion.upper()
        if self.numero: self.numero = self.numero.upper()
        if self.descriptipo: self.descriptipo = self.descriptipo.upper()
        if self.descripcubregasto: self.descripcubregasto = self.descripcubregasto.upper()
        super(InscripcionFichaSocioEconomicaBeca, self).save(force_insert, force_update, using, update_fields)



class DatoResidente(models.Model):
    fichabeca = models.ForeignKey(InscripcionFichaSocioEconomicaBeca,blank=True,null=True, on_delete=models.CASCADE)
    nombres = models.CharField(max_length=400,blank=True,null=True)
    edad = models.CharField(max_length=40,blank=True,null=True)
    estadocivil = models.ForeignKey(PersonaEstadoCivil,blank=True,null=True, on_delete=models.CASCADE)
    parentesco = models.ForeignKey(ParentezcoPersona,blank=True,null=True, on_delete=models.CASCADE)
    instruccion = models.ForeignKey(NivelEstudio,blank=True,null=True, on_delete=models.CASCADE)
    ocupacion = models.ForeignKey(OcupacionJefeHogar,blank=True,null=True, on_delete=models.CASCADE)
    lugar = models.CharField(max_length=300,blank=True,null=True)

    class Meta:
        verbose_name = 'Dato de Residente del Hogar'
        verbose_name_plural = 'Datos de los Residentes en el hogar'

    def __str__(self):
        return "%s %s"%(self.nombres, self.parentesco)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.nombres: self.nombres = self.nombres.upper()
        if self.lugar: self.lugar = self.lugar.upper()
        super(DatoResidente, self).save(force_insert, force_update, using, update_fields)

class DatoTrabajo(models.Model):
    fichabeca = models.ForeignKey(InscripcionFichaSocioEconomicaBeca,blank=True,null=True, on_delete=models.CASCADE)
    trabaja = models.BooleanField(default=False)
    tipotrabajo = models.ForeignKey(FormaTrabajo, blank=True,null=True, on_delete=models.CASCADE)
    empresa = models.CharField(max_length=400,blank=True,null=True)
    direccion = models.CharField(max_length=400,blank=True,null=True)
    telefono = models.CharField(max_length=400,blank=True,null=True)
    cargo = models.CharField(max_length=400,blank=True,null=True)
    fecha = models.DateField(blank=True,null=True)
    tiempolab = models.CharField(max_length=100,blank=True,null=True)
    actual = models.BooleanField(default=False)


    class Meta:
        verbose_name = 'Dato de Trabajo'
        verbose_name_plural = 'Datos del Trabajo'

    def __str__(self):
       return "%s %s"%(self.fichabeca.inscripcion.persona.nombre_completo_simple(), self.tipotrabajo.nombre)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.empresa: self.empresa = self.empresa.upper()
        if self.direccion: self.direccion = self.direccion.upper()
        if self.cargo: self.cargo = self.cargo.upper()
        super(DatoTrabajo, self).save(force_insert, force_update, using, update_fields)

class Detallevivienda(models.Model):
    fichabeca = models.ForeignKey(InscripcionFichaSocioEconomicaBeca,blank=True,null=True, on_delete=models.CASCADE)
    inquilino = models.BooleanField(default=False)
    numeroinqui = models.IntegerField(blank=True,null=True)
    valorarriendo = models.DecimalField(max_digits=11, decimal_places=2, default=Decimal('0.0'), blank=True, null=True)
    cedidadescrip = models.CharField(max_length=400,blank=True,null=True)
    numerodormit = models.IntegerField(blank=True,null=True)

    class Meta:
        verbose_name = 'Detalle de Vivienda'
        verbose_name_plural = 'Detalles de la Vivienda'

    def __str__(self):
       return "%s"%(self.fichabeca.inscripcion.persona.nombre_completo_simple())

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.cedidadescrip: self.cedidadescrip = self.cedidadescrip.upper()
        super(Detallevivienda, self).save(force_insert, force_update, using, update_fields)

class DetalleIngrexEgres(models.Model):
    fichabeca = models.ForeignKey(InscripcionFichaSocioEconomicaBeca,blank=True,null=True, on_delete=models.CASCADE)
    tipoingreso = models.ForeignKey(TipoIngresoVivienda,blank=True,null=True, on_delete=models.CASCADE)
    valoringreso = models.DecimalField(max_digits=11, decimal_places=2, default=Decimal('0.0'), blank=True, null=True)
    tipoegreso = models.ForeignKey(TipoEgresoVivienda,blank=True,null=True, on_delete=models.CASCADE)
    valoregreso = models.DecimalField(max_digits=11, decimal_places=2, default=Decimal('0.0'), blank=True, null=True)

    class Meta:
        verbose_name = 'Detalle de Ingreso y Egreso del Hogar'
        verbose_name_plural = 'Detalles de Ingresos y Egresos del Hogar'

    def __str__(self):
       return "%s"%(self.fichabeca.inscripcion.persona.nombre_completo_simple())

class EnfermedadFamilia(models.Model):
    fichabeca = models.ForeignKey(InscripcionFichaSocioEconomicaBeca,blank=True,null=True, on_delete=models.CASCADE)
    problemsalud = models.BooleanField(default=False)
    descripcion = models.CharField(max_length=300,blank=True,null=True)
    parentesco = models.ForeignKey(ParentezcoPersona,blank=True,null=True, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Enfermedad en el Grupo Familiar'
        verbose_name_plural = 'Enfermedades en el grupo Familiar'

    def __str__(self):
       return "%s"%(self.fichabeca.inscripcion.persona.nombre_completo_simple())


class ReferenciaBeca(models.Model):
    fichabeca = models.ForeignKey(InscripcionFichaSocioEconomicaBeca,blank=True,null=True, on_delete=models.CASCADE)
    telefono=models.CharField(max_length=50)
    parentesco = models.ForeignKey(ParentezcoPersona,blank=True,null=True, on_delete=models.CASCADE)

class DatosAcademicos(models.Model):
    fichabeca = models.ForeignKey(InscripcionFichaSocioEconomicaBeca,blank=True,null=True, on_delete=models.CASCADE)
    otracarrera = models.BooleanField(default=False)
    carrera = models.CharField(max_length=300,blank=True,null=True)
    universidad = models.CharField(max_length=300,blank=True,null=True)
    colegio = models.CharField(max_length=300,blank=True,null=True)
    fiscal = models.BooleanField(default=True)
    lugar = models.CharField(max_length=300,blank=True,null=True)
    anio = models.IntegerField(blank=True,null=True)
    nota = models.CharField(max_length=20,blank=True,null=True)

    def __str__(self):
       return "%s"%(self.fichabeca.inscripcion.persona.nombre_completo_simple())


    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.carrera: self.carrera = self.carrera.upper()
        if self.universidad: self.universidad = self.universidad.upper()
        if self.colegio: self.colegio = self.colegio.upper()
        if self.lugar: self.lugar = self.lugar.upper()
        super(DatosAcademicos, self).save(force_insert, force_update, using, update_fields)


class ReferenciaPersonal(models.Model):
    fichabeca = models.ForeignKey(InscripcionFichaSocioEconomicaBeca,blank=True,null=True, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=300)
    telefono=models.CharField(max_length=50)
    celular=models.CharField(max_length=50)
    parentesco = models.ForeignKey(ParentezcoPersona,blank=True,null=True, on_delete=models.CASCADE)

    def __str__(self):
       return "%s"%(self.fichabeca.inscripcion.persona.nombre_completo_simple())


    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.nombre: self.nombre = self.nombre.upper()
        super(ReferenciaPersonal, self).save(force_insert, force_update, using, update_fields)


