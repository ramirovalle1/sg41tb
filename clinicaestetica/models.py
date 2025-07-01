from decimal import Decimal
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q, Sum

from settings import ID_TIPO_FACIAL





class TipoEstetico(models.Model):
    descripcion = models.CharField(max_length=1200,blank=True,null=True)
    activo = models.BooleanField(default=False)
    fecha = models.DateTimeField(null=True,blank=True)

    def __str__(self):
        return self.descripcion
    class Meta:
        verbose_name = "Tipo estetico"
        verbose_name_plural = "Tipos esteticos"

class Tratamiento(models.Model):
    tipoestetico = models.ForeignKey(TipoEstetico, null=True, blank=True, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=300,blank=True,null=True)
    descripcion = models.CharField(max_length=300,blank=True,null=True)
    fecha = models.DateTimeField(null=True,blank=True)

    def __str__(self):
        return str(self.tipoestetico) +' '+self.nombre

    def preciotratamiento(self,ficha):
        if TratamientoPrecio.objects.filter(tratamiento = self,tipopersona=ficha.tipopersona).exists():
            return TratamientoPrecio.objects.get(tratamiento = self,tipopersona=ficha.tipopersona)
        return False

    @staticmethod
    def flexbox_query(q):
        return Tratamiento.objects.filter(Q(nombre__contains=q)|Q(descripcion__contains=q)).order_by('nombre')

    def flexbox_repr(self):
        return str(self)

    def flexbox_alias(self):
        return str(self)

    class Meta:
        verbose_name = "Tratamiento Estetico"
        verbose_name_plural = "Tratamientos Esteticos"

class TipoPersona(models.Model):
    nombre = models.CharField(max_length=300,blank=True,null=True)
    codigo = models.CharField(max_length=10,blank=True,null=True)
    url = models.CharField(max_length=300,blank=True,null=True)
    verifica = models.BooleanField(default=True)
    fecha = models.DateTimeField(null=True,blank=True)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Tipo de persona"
        verbose_name_plural = "Tipos de Persona"


class TratamientoPrecio(models.Model):
    tratamiento = models.ForeignKey(Tratamiento, null=True, blank=True, on_delete=models.CASCADE)
    tipopersona = models.ForeignKey(TipoPersona, null=True, blank=True, on_delete=models.CASCADE)
    valor = models.DecimalField(max_digits=11, decimal_places=2, default=Decimal('0.0'), blank=True, null=True)
    fecha = models.DateTimeField(null=True,blank=True)

    class Meta:
        verbose_name = "Tratamiento tipo de persona"
        verbose_name_plural = "Tratamientos tipos de Persona"

class FichaMedica(models.Model):
    from med.models import PersonaEstadoCivil
    from sga.models import Sexo
    nombres = models.CharField(max_length=300,blank=True,null=True)
    apellidos = models.CharField(max_length=300,blank=True,null=True)
    numdocumento = models.CharField(max_length=20,blank=True,null=True)
    pasaporte = models.BooleanField(default=False)
    telefono = models.CharField(max_length=300,blank=True,null=True)
    ocupacion = models.CharField(max_length=300,blank=True,null=True)
    sexo = models.ForeignKey(Sexo,blank=True,null=True, on_delete=models.CASCADE)
    fechanacimiento = models.DateField(blank=True,null=True)
    estadocivil = models.ForeignKey(PersonaEstadoCivil,blank=True,null=True, on_delete=models.CASCADE)
    direccion = models.CharField(max_length=300,blank=True,null=True)
    email = models.CharField(max_length=300,blank=True,null=True)
    hijos = models.IntegerField(blank=True, null=True)
    partos = models.IntegerField(blank=True, null=True)
    cesareas = models.IntegerField(blank=True, null=True)
    controlnatal = models.CharField(max_length=600,null=True,blank=True)
    fum = models.DateTimeField(null=True,blank=True)
    tipopersona = models.ForeignKey(TipoPersona,blank=True,null=True, on_delete=models.CASCADE)
    creacion = models.DateTimeField(null=True,blank=True)
    edicion = models.DateTimeField(null=True,blank=True)

    def __str__(self):
        return self.nombres +" "+ self.apellidos +" ( "+ self.numdocumento+" ) "
    def habitoficha(self,idtipohabito):
        if HabitoFicha.objects.filter(fichamedica=self,habito__id=idtipohabito).exists():
            return HabitoFicha.objects.filter(fichamedica=self,habito__id=idtipohabito)[:1].get()
        return False

    def total_rubros(self):
        from sga.models import Rubro
        sum = Rubro.objects.filter(fichamedica=self).aggregate(Sum('valor'))
        return sum['valor__sum'] if sum['valor__sum'] else 0
    def rubros_pendientes(self):
        return self.rubro_set.filter(cancelado=False).order_by('fechavence')

    def rubros_vencidos(self):
        return [x for x in self.rubro_set.filter(cancelado=False, valor__gt=0) if x.vencido()]

    def total_pagado(self):
        from sga.models import Pago
        sum = Pago.objects.filter(rubro__fichamedica=self).aggregate(Sum('valor'))
        return sum['valor__sum'] if sum['valor__sum'] else 0

    def total_adeudado(self):
        return self.total_rubros() - self.total_pagado()

    @staticmethod
    def flexbox_query(q):
        return FichaMedica.objects.filter(Q(nombres__icontains=q)| Q(apellidos__icontains=q)| Q(numdocumento__icontains=q)).order_by('nombres','apellidos')

    def flexbox_repr(self):
        return self.numdocumento+" - "+self.apellidos +" "+ self.nombres

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.nombres = self.nombres.upper().strip()
        self.apellidos = self.apellidos.upper().strip()
        if self.ocupacion:
            self.ocupacion = self.ocupacion.upper().strip()
        if self.email:
            self.email = self.email.lower().strip()
        if self.direccion:
            self.direccion = self.direccion.lower().strip()
        super(FichaMedica, self).save(force_insert, force_update, using, update_fields)
class AntecedenteMedFicha(models.Model):
    fichamedica = models.ForeignKey(FichaMedica,blank=True,null=True, on_delete=models.CASCADE)
    descripcion = models.CharField(max_length=300,blank=True,null=True)
    patolog_personales = models.BooleanField(default=False)
    patolog_familiares = models.BooleanField(default=False)
    quirurgico = models.BooleanField(default=False)
    alergia = models.BooleanField(default=False)
    fecha = models.DateTimeField(null=True,blank=True)

class TipoHabito(models.Model):
    tipoestetico = models.ForeignKey(TipoEstetico,blank=True,null=True, on_delete=models.CASCADE)
    nombres = models.CharField(max_length=300,blank=True,null=True)
    descrip = models.BooleanField(default=False)
    cant = models.BooleanField(default=False)
    porcen = models.IntegerField(blank=True,null=True)
    clas = models.CharField(max_length=100,blank=True,null=True)
    activo = models.BooleanField(default=True)
    fecha = models.DateTimeField(null=True,blank=True)

    class Meta:
        verbose_name = "Tipo Habito"
        verbose_name_plural = "Tipos de habito"

    # def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
    #     self.nombres = self.nombres.upper().strip()
    #     super(TipoHabito, self).save(force_insert, force_update, using, update_fields)

class HabitoFicha(models.Model):
    fichamedica = models.ForeignKey(FichaMedica,blank=True,null=True, on_delete=models.CASCADE)
    habito = models.ForeignKey(TipoHabito,blank=True,null=True, on_delete=models.CASCADE)
    descripcion = models.CharField(max_length=300,blank=True,null=True)
    cant = models.IntegerField(null=True,blank=True)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.descripcion = self.descripcion.upper().strip()
        super(HabitoFicha, self).save(force_insert, force_update, using, update_fields)

class AntecedenteEsteticoFicha(models.Model):
    fichamedica = models.ForeignKey(FichaMedica,blank=True,null=True, on_delete=models.CASCADE)
    tipoestetico = models.ForeignKey(TipoEstetico,blank=True,null=True, on_delete=models.CASCADE)
    descripcion = models.CharField(max_length=300,blank=True,null=True)
    cirugia = models.BooleanField(default=False)
    tratamiento = models.BooleanField(default=False)
    autotratamiento = models.BooleanField(default=False)
    fecha = models.DateTimeField(null=True,blank=True)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.descripcion = self.descripcion.upper().strip()
        super(AntecedenteEsteticoFicha, self).save(force_insert, force_update, using, update_fields)

class Consulta(models.Model):
    fichamedica = models.ForeignKey(FichaMedica,blank=True,null=True, on_delete=models.CASCADE)
    motivo = models.CharField(max_length=1200,blank=True,null=True)
    medicamento = models.CharField(max_length=800,blank=True,null=True)
    cosmetico = models.CharField(max_length=800,blank=True,null=True)
    horasol = models.TimeField(blank=True,null=True)
    fps = models.CharField(max_length=200,blank=True,null=True)
    fecha = models.DateTimeField(null=True,blank=True)
    usuario = models.ForeignKey(User, null=True,blank=True, on_delete=models.CASCADE)
    guardado = models.BooleanField(default=False)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.motivo = self.motivo.upper().strip()
        if self.medicamento:
            self.medicamento = self.medicamento.upper().strip()
        if self.fps:
            self.fps = self.fps.upper().strip()
        if self.cosmetico:
            self.cosmetico = self.cosmetico.upper().strip()
        super(Consulta, self).save(force_insert, force_update, using, update_fields)

class ParametroEstetico(models.Model):
    nombre = models.CharField(max_length=300,null=True,blank=True)
    fotpiel = models.BooleanField(default=False)
    biotipo = models.BooleanField(default=False)
    tippiel = models.BooleanField(default=False)
    eglogau = models.BooleanField(default=False)
    linexpr = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)
    fecha = models.DateTimeField(null=True,blank=True)

    def __str__(self):
        return self.nombre
    class Meta:
        verbose_name = "Parametro Estetico"
        verbose_name_plural = "Parametros Esteticos"

class EvaluacionEstetica(models.Model):
    consulta = models.ForeignKey(Consulta,blank=True,null=True, on_delete=models.CASCADE)
    tipoestetico = models.ForeignKey(TipoEstetico,blank=True,null=True, on_delete=models.CASCADE)
    tratamiento = models.ForeignKey(Tratamiento,blank=True,null=True, on_delete=models.CASCADE)
    # CAMPOS FACIAL
    fotpiel = models.ForeignKey(ParametroEstetico,related_name='Foto Piel+',blank=True,null=True, on_delete=models.CASCADE)
    biotipo = models.ForeignKey(ParametroEstetico,related_name='Bio Tipo+',blank=True,null=True, on_delete=models.CASCADE)
    tipopiel = models.ForeignKey(ParametroEstetico,related_name='Tipo Piel+',blank=True,null=True, on_delete=models.CASCADE)
    glogau = models.ForeignKey(ParametroEstetico,related_name='Escala Glogau+',blank=True,null=True, on_delete=models.CASCADE)
    linexpre = models.ForeignKey(ParametroEstetico,related_name='Linea Expre+',blank=True,null=True, on_delete=models.CASCADE)
    # CAMPOS FACIAL Y CORPORAL
    ftextpiel_cpeso = models.CharField(max_length=300,null=True,blank=True)
    fporos_ctalla = models.CharField(max_length=300,null=True,blank=True)
    fcomedones_cimc = models.CharField(max_length=300,null=True,blank=True)
    falteraciones_cgrasa = models.CharField(max_length=300,null=True,blank=True)
    # CAMPOS CORPORAL
    cuello = models.DecimalField(max_digits=11, decimal_places=2, blank=True, null=True)
    abalto = models.DecimalField(max_digits=11, decimal_places=2, blank=True, null=True)
    cintura = models.DecimalField(max_digits=11, decimal_places=2,blank=True, null=True)
    abbajo = models.DecimalField(max_digits=11, decimal_places=2, blank=True, null=True)
    muslo = models.DecimalField(max_digits=11, decimal_places=2,  blank=True, null=True)
    brazo = models.DecimalField(max_digits=11, decimal_places=2,  blank=True, null=True)
    pesoideal = models.DecimalField(max_digits=11, decimal_places=2, blank=True, null=True)
    pesodesado = models.DecimalField(max_digits=11, decimal_places=2, blank=True, null=True)

    diagnostico = models.CharField(max_length=300,null=True,blank=True)
    desctratamiento = models.CharField(max_length=300,null=True,blank=True)
    sesion = models.IntegerField(null=True,blank=True)
    dias = models.IntegerField(null=True,blank=True)
    valor = models.DecimalField(max_digits=11, decimal_places=2, default=Decimal('0.0'), blank=True, null=True)
    fecha = models.DateTimeField(null=True,blank=True)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.tipoestetico.id == ID_TIPO_FACIAL:
            if self.ftextpiel_cpeso:
                self.ftextpiel_cpeso = self.ftextpiel_cpeso.upper().strip()
            if self.fporos_ctalla:
                self.fporos_ctalla = self.fporos_ctalla.upper().strip()
            if self.fcomedones_cimc:
                self.fcomedones_cimc = self.fcomedones_cimc.upper().strip()
        if self.diagnostico:
            self.diagnostico = self.diagnostico.upper().strip()
        if self.desctratamiento:
            self.desctratamiento = self.desctratamiento.upper().strip()
        super(EvaluacionEstetica, self).save(force_insert, force_update, using, update_fields)

class ControlSesion(models.Model):
    evaluacionestetica = models.ForeignKey(EvaluacionEstetica,null=True,blank=True, on_delete=models.CASCADE)
    procedimiento = models.CharField(max_length=300,null=True,blank=True)
    recomendacion = models.CharField(max_length=300,null=True,blank=True)
    valor = models.DecimalField(max_digits=11, decimal_places=2, default=Decimal('0.0'), blank=True, null=True)
    firma = models.FileField(upload_to='firmadatos/%Y/%m/%d', max_length=200)
    fecha = models.DateTimeField(null=True,blank=True)

class MedicamentoSesion(models.Model):
    medicamento = models.IntegerField(null=True,blank=True) #/// ID FOREINKEY DE REGISTRO DE MEDICAMENTO DEL SGA
    controlsesion = models.ForeignKey(ControlSesion, null=True, blank=True, on_delete=models.CASCADE)
    cantidad = models.IntegerField(null=True,blank=True)
    valor = models.DecimalField(max_digits=11, decimal_places=2, default=Decimal('0.0'), blank=True, null=True)
    cobrar =models.BooleanField(default=True)
    fecha = models.DateTimeField(null=True,blank=True)

class RubroEstetico(models.Model):
    rubro = models.IntegerField( null=True, blank=True) #/// ID FOREINKEY DE RUBRO DEL SGA
    evaluacionestetica = models.ForeignKey(EvaluacionEstetica, null=True, blank=True, on_delete=models.CASCADE)
    controlsesion = models.ForeignKey(ControlSesion, null=True, blank=True, on_delete=models.CASCADE)
    pago = models.DateTimeField(null=True,blank=True)
    fecha = models.DateTimeField(null=True,blank=True)

