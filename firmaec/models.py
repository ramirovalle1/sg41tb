from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.contrib.auth import get_user_model, authenticate
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.auth.models import User
from core.my_model import ModelBase


class RepositorioActaCalificacion(ModelBase):
    class Estados(models.IntegerChoices):
        Pendiente = 0, "Pendiente"
        Generada = 1, "Generada"
        Firmada = 2, "Firmada"
        Cancelada = 3, "Cancelada"

    BG_COLOR_MAPPING = {
        Estados.Pendiente: 'bg-primary',
        Estados.Generada: 'bg-warning',
        Estados.Firmada: 'bg-success',
        Estados.Cancelada: 'bg-danger',
    }

    BADGE_COLOR_MAPPING = {
        Estados.Pendiente: 'badge-primary',
        Estados.Generada: 'badge-warning',
        Estados.Firmada: 'badge-success',
        Estados.Cancelada: 'badge-danger',
    }

    materia = models.OneToOneField('sga.Materia', on_delete=models.CASCADE, verbose_name='Materia')
    estado = models.IntegerField(choices=Estados.choices, default=Estados.Pendiente, verbose_name='Estado')
    archivo_inicial = models.ForeignKey('documental.Repositorio', blank=True, null=True, related_name='+', on_delete=models.CASCADE, verbose_name='Archivo inicial')
    archivo_final = models.ForeignKey('documental.Repositorio', blank=True, null=True, related_name='+', on_delete=models.CASCADE, verbose_name='Archivo Final')

    def __str__(self):
        return f'{self.materia}'

    def nombre_input(self):
        return f'materia_{self.materia.pk}'

    def puede_firmar(self, responsable_id):
        secuencia_firma = self.secuencia_firma()
        firma_persona = secuencia_firma.filter(subido=False, responsable_id=responsable_id).first()
        if not firma_persona:
            return False
        # Verificar si la firma anterior ya fue subida
        if firma_persona.orden > 1:
            anterior = secuencia_firma.filter(orden=firma_persona.orden - 1).first()
            if anterior and not anterior.subido:
                return False

        return True

    def siguiente_a_firmar(self, responsable_actual_id):
        secuencia_firma = self.secuencia_firma()
        firmante_actual = secuencia_firma.filter(responsable_id=responsable_actual_id).first()

        if not firmante_actual:
            raise NameError("No se encontró firmante actual")

        if not firmante_actual.subido or firmante_actual.archivo is None:
            raise NameError("El firmante actual aún no ha firmado o no ha subido el archivo")

        # Obtener el siguiente firmante en la secuencia
        firmante_siguiente = secuencia_firma.filter(orden=firmante_actual.orden + 1).first()

        if not firmante_siguiente:
            # No hay más firmantes en la secuencia
            return None

        if firmante_siguiente.subido and firmante_siguiente.archivo is not None:
            raise NameError("El firmante siguiente ya ha firmado")

        return firmante_siguiente

    def mi_acta_firmada(self, responsable_id):
        secuencia_firma = self.secuencia_firma()
        return secuencia_firma.filter(subido=True, responsable_id=responsable_id).first()

    def tiene_firmada_acta(self, responsable_id):
        secuencia_firma = self.secuencia_firma()
        return secuencia_firma.only("id").filter(subido=True, responsable_id=responsable_id).exists()

    def secuencia_firma(self):
        return FirmaActaCalificacion.objects.filter(materia=self.materia).order_by('orden')

    def color_estado_bg(self):
        return self.BG_COLOR_MAPPING.get(self.estado, 'bg-default')

    def color_estado_badge(self):
        return self.BADGE_COLOR_MAPPING.get(self.estado, 'badge-default')


class FirmaActaCalificacion(ModelBase):
    class TiposResponsable(models.IntegerChoices):
        ProfesorMateria = 1, "Profesor de la materia"
        Profesor = 2, "Profesor"
        Administrativo = 3, "Administrativo"

    class CargosResponsable(models.IntegerChoices):
        SECRETARIA_GENERAL = 1, "Secretaria General"
        DOCENTE = 2, "Docente"
        SECRETARIA_RESPONSABLE = 3, "Secretaria Responsable"

    materia = models.ForeignKey('sga.Materia', on_delete=models.CASCADE, verbose_name=u'Materia')
    tipo = models.IntegerField(choices=TiposResponsable.choices, default=0, verbose_name='Tipo')
    responsable = models.ForeignKey('sga.Persona', verbose_name=u'Persona', on_delete=models.CASCADE, related_name='+')
    cargo = models.IntegerField(choices=CargosResponsable.choices, default=0, verbose_name='Cargo')
    orden = models.IntegerField(default=0, verbose_name=u'Orden')
    fecha = models.DateTimeField(blank=True, null=True, verbose_name=u"Fecha de subida")
    subido = models.BooleanField(default=False, verbose_name=u'¿Subio archivo?')
    archivo = models.ForeignKey('documental.Repositorio', blank=True, null=True, related_name='+', on_delete=models.CASCADE, verbose_name='Archivo')

    def __str__(self):
        return f'Materia: {self.materia} - Responsable: {self.responsable} ({self.cargo})'

    class Meta:
        verbose_name = u"Firma del acta de calificación"
        verbose_name_plural = u"Firmas del acta de calificación"
        ordering = ['materia', 'orden']
        unique_together = ('materia', 'responsable',)

    def actualizar_estado_repositorio_acta(self):
        # Obtener el repositorio relacionado
        repositorio = self.materia.mi_repositorio_acta_calificacion()

        # Verificar si todos han firmado
        total_firmas = FirmaActaCalificacion.objects.only("id").filter(materia=self.materia).count()
        firmas_subidas = FirmaActaCalificacion.objects.only("id").filter(materia=self.materia, subido=True).count()

        if firmas_subidas == total_firmas and total_firmas > 0:
            # Todos han firmado, actualizar estado y archivo_final
            repositorio.estado = RepositorioActaCalificacion.Estados.Firmada

            # Actualizar archivo_final con el archivo de la última firma
            ultima_firma = FirmaActaCalificacion.objects.filter(materia=self.materia).order_by('-orden').first()
            if ultima_firma:
                repositorio.archivo_final = ultima_firma.archivo

        elif firmas_subidas == 0:
            # Nadie ha firmado, poner estado Pendiente
            repositorio.estado = RepositorioActaCalificacion.Estados.Pendiente
            repositorio.archivo_final = None  # Opcional, si deseas limpiar el archivo final

        else:
            # Alguno han firmado pero no todos, podría mantenerse en estado Generada
            repositorio.estado = RepositorioActaCalificacion.Estados.Generada

        repositorio.save()

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old_instance = FirmaActaCalificacion.objects.filter(pk=self.pk).first()

        super(FirmaActaCalificacion, self).save(*args, **kwargs)

        if not is_new and old_instance:
            # Comparar atributos para ver si hubo cambios
            if (
                    old_instance.tipo != self.tipo or
                    old_instance.responsable != self.responsable or
                    old_instance.cargo != self.cargo or
                    old_instance.orden != self.orden or
                    old_instance.fecha != self.fecha or
                    old_instance.subido != self.subido or
                    old_instance.archivo != self.archivo
            ):
                HistorialFirmaActaCalificacion.objects.create(
                    materia=self.materia,
                    tipo=self.tipo,
                    responsable=self.responsable,
                    cargo=self.cargo,
                    orden=self.orden,
                    fecha=self.fecha,
                    subido=self.subido,
                    archivo=self.archivo
                )
        self.actualizar_estado_repositorio_acta()


class HistorialFirmaActaCalificacion(ModelBase):
    materia = models.ForeignKey('sga.Materia', on_delete=models.CASCADE, verbose_name=u'Materia')
    tipo = models.IntegerField(choices=FirmaActaCalificacion.TiposResponsable.choices, default=0, verbose_name='Tipo')
    responsable = models.ForeignKey('sga.Persona', verbose_name=u'Persona', on_delete=models.CASCADE, related_name='+')
    cargo = models.IntegerField(choices=FirmaActaCalificacion.CargosResponsable.choices, default=0, verbose_name='Cargo')
    orden = models.IntegerField(default=0, blank=True, null=True, verbose_name=u'Orden')
    fecha = models.DateTimeField(blank=True, null=True, verbose_name=u"Fecha de subida")
    subido = models.BooleanField(default=False, verbose_name=u'¿Subió archivo?')
    archivo = models.ForeignKey('documental.Repositorio', blank=True, null=True, related_name='+', on_delete=models.CASCADE, verbose_name='Archivo')

    def __str__(self):
        return u'Materia: %s - Responsable(%s): %s ' % (self.materia, self.cargo, self.responsable)


class Solicitud(ModelBase):
    class Estados(models.IntegerChoices):
        PENDIENTE = 0, "Pendiente"
        FIRMADO = 1, "Firmado"
        CANCELADO = 2, "Cancelado"

    class Tipos(models.IntegerChoices):
        NINGUNO = 0, "Ninguno"
        ACTA_CALIFICACION = 1, "Acta de calificaciones"

    BG_COLOR_MAPPING = {
        Estados.PENDIENTE: 'bg-warning',
        Estados.FIRMADO: 'bg-primary',
        Estados.CANCELADO: 'bg-danger',
    }

    estado = models.IntegerField(choices=Estados.choices, default=Estados.PENDIENTE, verbose_name='Estado')
    tipo = models.IntegerField(choices=Tipos.choices, default=Tipos.NINGUNO, verbose_name='Tipo')
    descripcion = models.CharField(default='', verbose_name=u'Descripcion', max_length=500)
    responsable = models.ForeignKey('sga.persona', on_delete=models.CASCADE, verbose_name=u'Responsable', related_name='+')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, verbose_name=u'content type', blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True, verbose_name=u'object id')
    content_object = GenericForeignKey('content_type', 'object_id')
    archivo = models.ForeignKey('documental.Repositorio', related_name='+', on_delete=models.CASCADE, verbose_name='Archivo')

    class Meta:
        verbose_name = u'Solicitud de firma'
        verbose_name_plural = u'Solicitudes de firmas'
        ordering = ('responsable',)
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]

    def color_estado_bg(self):
        return self.BG_COLOR_MAPPING.get(self.estado, 'bg-default')

    def solicitud_firmada(self):
        try:
            eSolicitudFirmada = SolicitudFirmada.objects.get(solicitud=self)
        except ObjectDoesNotExist:
            eSolicitudFirmada = None
        return eSolicitudFirmada

    def solicitud_cancelada(self):
        try:
            eSolicitudCancelada = SolicitudCancelada.objects.get(solicitud=self)
        except ObjectDoesNotExist:
            eSolicitudCancelada = None
        return eSolicitudCancelada


class SolicitudFirmada(ModelBase):
    solicitud = models.OneToOneField(Solicitud, on_delete=models.CASCADE, verbose_name=u'Solicitud')
    archivo = models.ForeignKey('documental.Repositorio', related_name='+', on_delete=models.CASCADE, verbose_name='Archivo')
    fechahora = models.DateTimeField(verbose_name=u"Fecha de firma")
    observacion = models.TextField(null=True, blank=True, verbose_name='Observacion')

    class Meta:
        verbose_name = u'Solicitud firmada'
        verbose_name_plural = u'Solicitudes firmadas'
        ordering = ('solicitud',)


class SolicitudCancelada(ModelBase):
    solicitud = models.OneToOneField(Solicitud, on_delete=models.CASCADE, verbose_name=u'Solicitud')
    fechahora = models.DateTimeField(verbose_name=u"Fecha de cancelamiento")
    observacion = models.TextField(verbose_name='Observacion')

    class Meta:
        verbose_name = u'Solicitud cancelada'
        verbose_name_plural = u'Solicitudes canceladas'
        ordering = ('solicitud',)
