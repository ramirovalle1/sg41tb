from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django.db import models

# Create your models here.
from django.db.models import Q
from settings import TIPO_DOCUMENTO, ANIO_TESIS
from sga.models import Persona, Sede,Inscripcion,Profesor,Carrera, Graduado


class TipoDocumento(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Tipo Documento"
        verbose_name_plural = "Tipos Documentos"
        ordering = ['nombre']

    @staticmethod
    def flexbox_query(q):
        return TipoDocumento.objects.filter(Q(nombre__contains=q)).order_by('nombre')

    def flexbox_repr(self):
        return self.nombre

    def flexbox_alias(self):
        return self.nombre

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.nombre = self.nombre.upper()
        super(TipoDocumento, self).save(force_insert, force_update, using, update_fields)

class Idioma(models.Model):
    nombre = models.CharField(max_length=200)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Idioma"
        verbose_name_plural = "Idiomas"

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.nombre = self.nombre.upper()
        super(Idioma, self).save(force_insert, force_update, using, update_fields)


class Documento(models.Model):
    codigo = models.CharField(max_length=20)
    nombre = models.CharField(max_length=200)
    autor = models.CharField(max_length=200)
    tipo = models.ForeignKey(TipoDocumento, on_delete=models.CASCADE)
    anno = models.IntegerField()
    emision = models.CharField(max_length=40)
    palabrasclaves = models.TextField()
    digital = models.FileField(upload_to='biblioteca/%Y/%m/%d', null=True, blank=True)
    fisico = models.BooleanField()
    copias = models.IntegerField()
    paginas = models.IntegerField(default=0)
    portada = models.FileField(upload_to='biblioteca/portadas/%Y/%m/%d', null=True, blank=True)
    editora = models.CharField(max_length=200, null=True, blank=True)
    sede = models.ForeignKey(Sede, on_delete=models.CASCADE)
    codigodewey = models.CharField(max_length=200, null=True, blank=True)
    idioma = models.ForeignKey(Idioma, on_delete=models.CASCADE)
    tutor = models.CharField(max_length=200, blank=True, null=True)
    resumen = models.TextField(blank=True, null=True)
    inscripcion = models.ForeignKey(Inscripcion, on_delete=models.CASCADE)
    docente = models.ForeignKey(Profesor, on_delete=models.CASCADE)
    carrera = models.ForeignKey(Carrera, blank=True, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return "[%s] %s - %s"%(self.codigo, self.nombre, self.autor)

    class Meta:
        verbose_name = "Documento"
        verbose_name_plural = "Documentos"

    def copias_restantes(self):
        return self.copias - self.prestamodocumento_set.filter(recibido=False).count()

    def copias_prestadas(self):
        return self.prestamodocumento_set.filter(recibido=False).count()

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.codigo: self.codigo = self.codigo.upper()
        if self.codigodewey: self.codigodewey = self.codigodewey.upper()
        if self.nombre: self.nombre = self.nombre.upper()
        if self.autor: self.autor = self.autor.upper()
        if self.emision: self.emision = self.emision.upper()
        if self.palabrasclaves: self.palabrasclaves = self.palabrasclaves.upper()
        if self.editora: self.editora = self.editora.upper()
        if self.tutor: self.tutor = self.tutor.upper()
        if self.resumen: self.resumen = self.resumen.upper()
        super(Documento, self).save(force_insert, force_update, using, update_fields)

    def es_tesis(self):
        if self.tipo.id==TIPO_DOCUMENTO and self.anno>=ANIO_TESIS:
            return True
        else:
            return False

    def tiene_autor(self):
        if  AutoresTesis.objects.filter(documento=self.id).exists():
            return True
        else:
            return False

    @staticmethod
    def flexbox_query(q):
        return Documento.objects.filter(Q(nombre__contains=q)).order_by('nombre')[:25]

    def flexbox_repr(self):
        return self.nombre+" ("+str(self.prestamodocumento_set.count())+")"

    @staticmethod
    def flexbox_query_2(q):
        return Documento.objects.filter(Q(nombre__contains=q)|Q(tutor__icontains=q)|Q(autor__icontains=q))


    def flexbox_repr2(self):
        return self.nombre+" ("+str(self.prestamodocumento_set.count())+") "+ str(self.id)


    def flexbox_alias(self):
       return str(self)

class ReferenciaWeb(models.Model):
    prioridad = models.IntegerField(null=True, blank=True)
    url = models.CharField(max_length=200)
    nombre = models.CharField(max_length=200)
    logo = models.FileField(upload_to='referencias')
    estado = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Referencia Web"
        verbose_name_plural = "Referencias Web"


class OtraBibliotecaVirtual(models.Model):
    url = models.CharField(max_length=200)
    nombre = models.CharField(max_length=200)
    logo = models.FileField(upload_to='referencias')
    descripcion = models.TextField()
    prioridad = models.IntegerField(null=True, blank=True)
    estado = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Otra Biblioteca Virtual"
        verbose_name_plural = "Otras Bibliotecas Virtuales"


class PrestamoDocumento(models.Model):
    documento = models.ForeignKey(Documento, on_delete=models.CASCADE)
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE)
    tiempo = models.IntegerField(default=24)
    responsableentrega = models.ForeignKey(Persona, related_name='entrega', on_delete=models.CASCADE)
    fechaentrega = models.DateField()
    horaentrega = models.TimeField()
    entregado = models.BooleanField(default=False)
    responsablerecibido = models.ForeignKey(Persona, related_name='recibe', null=True, blank=True, on_delete=models.CASCADE)
    recibido = models.BooleanField(default=False)
    fecharecibido = models.DateField(null=True, blank=True)
    horarecibido = models.TimeField(null=True, blank=True)

    def __str__(self):
        return str(self.documento)+" - "+self.persona.nombre_completo()+" Tiempo: "+ str(self.tiempo)

    class Meta:
        verbose_name = "Prestamo Documento"
        verbose_name_plural = "Prestamos Documentos"

    def tiempo_restante(self):
        """ Combinar la fecha y hora para convertirla a Datetime """
        entrega = datetime.combine(self.fechaentrega, self.horaentrega)
        deberecibir = entrega + timedelta(hours=self.tiempo)
        queda = deberecibir - datetime.now()
        if queda.days < 0:
            return 0
        return queda.seconds/60


class ConsultaBiblioteca(models.Model):
    fecha = models.DateField()
    hora = models.TimeField()
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE)
    busqueda = models.CharField(max_length=500)
    documentosconsultados = models.ManyToManyField(Documento)
    referenciasconsultadas = models.ManyToManyField(ReferenciaWeb)
    otrabibliotecaconsultadas = models.ManyToManyField(OtraBibliotecaVirtual)

    def __str__(self):
        return str(self.persona)+" FECHA: "+self.fecha.strftime('%d-%m-%Y')

    class Meta:
        verbose_name = "Consulta Biblioteca"
        verbose_name_plural = "Consultas Biblioteca"

    def fun_referencias(self):
        if self.referenciasconsultadas.all().exists():
            return self.referenciasconsultadas.all()
        return None

    def fun_otrasbiblio(self):
        if self.otrabibliotecaconsultadas.all().exists():
            return self.otrabibliotecaconsultadas.all()
        return None

class TipoProyecto(models.Model):
    codigo = models.CharField(max_length=10)
    descripcion = models.CharField(max_length=100)

    def __str__(self):
        return self.codigo + ' - ' + self.descripcion

    @staticmethod
    def flexbox_query(q):
        return TipoProyecto.objects.filter(Q(codigo__contains=q)|Q(descripcion__contains=q))

    def flexbox_repr(self):
        return str(self)

    class Meta:
        verbose_name = "Tipo de Proyecto"
        verbose_name_plural = "Tipos de Proyectos"

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.codigo = self.codigo.upper()
        self.descripcion = self.descripcion.upper()
        super(TipoProyecto, self).save(force_insert, force_update, using, update_fields)



class AutoresTesis(models.Model):
    documento = models.ForeignKey(Documento, on_delete=models.CASCADE)
    estudiante = models.ForeignKey(Inscripcion, on_delete=models.CASCADE)
    nota = models.FloatField(null=True, blank=True)
    plagio = models.FloatField(null=True, blank=True)
    fechasustentacion = models.DateField(null=True, blank=True)
    observaciones = models.CharField(max_length=500,null=True, blank=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha = models.DateTimeField()

    class Meta:
        verbose_name = "Autor Tesis"
        verbose_name_plural = "Autores Tesis"


class DocuemntoGraduado(models.Model):
    documento = models.ForeignKey(Documento, on_delete=models.CASCADE)
    graduado = models.ForeignKey(Graduado, on_delete=models.CASCADE)


