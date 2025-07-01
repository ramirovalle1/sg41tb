# -*- coding: latin-1 -*-
import os
from django.contrib.auth.models import User

from django.db import models
from sga.models import Persona

CALIDAD_SUENNO = (
    ('TRANQUILO','TRANQUILO'),
    ('INSOMNIO','INSOMNIO'),
    ('REPARADOR','REPARADOR')
    )

MOTIVO_LENTES = (
    ('',''),
    ('ASTIGMATISMO','ASTIGMATISMO'),
    ('MIOPIA','MIOPIA'),
    ('HIPERMETROPIA','HIPERMETROPIA')
    )

class PersonaEstadoCivil(models.Model):
    nombre = models.CharField(max_length=50)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Persona Estado Civil"
        verbose_name_plural = "Persona Estados Civil"

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.nombre = self.nombre.upper()
        super(PersonaEstadoCivil, self).save(force_insert, force_update, using, update_fields)

class PersonaEducacion(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Persona Educacion"
        verbose_name_plural = "Personas Educacion"

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.nombre = self.nombre.upper()
        super(PersonaEducacion, self).save(force_insert, force_update, using, update_fields)


class PersonaProfesion(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Persona Profesion"
        verbose_name_plural = "Personas Profesiones"

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.nombre = self.nombre.upper()
        super(PersonaProfesion, self).save(force_insert, force_update, using, update_fields)


class PersonaExtension(models.Model):
    # Modelo Extension del model PERSONA
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE)
    estadocivil = models.ForeignKey(PersonaEstadoCivil, related_name='estadocivil', blank=True, null=True, on_delete=models.CASCADE)
    tienelicencia = models.BooleanField(verbose_name='Licencia de Conduccion', default=False)
    tipolicencia = models.CharField(max_length=50, verbose_name='Tipo de Licencia', blank=True, null=True)
    telefonos = models.CharField(max_length=100, verbose_name=u"Telefonos de Familiar", blank=True, null=True)
    tieneconyuge = models.BooleanField(verbose_name="Conyuge", default=False)
    hijos = models.IntegerField(verbose_name="No. de Hijos", blank=True, null=True)

    # Datos Familiares
    padre = models.CharField(max_length=100, verbose_name='Nombre Completo Padre', blank=True, null=True)
    edadpadre = models.IntegerField(verbose_name='Edad del Padre', blank=True, null=True)
    estadopadre = models.ForeignKey(PersonaEstadoCivil, related_name='estadopadre', blank=True, null=True, on_delete=models.CASCADE)
    telefpadre = models.CharField(max_length=50, verbose_name='Telefono del Padre', blank=True, null=True)
    educacionpadre = models.ForeignKey(PersonaEducacion, related_name='educacionpadre', blank=True, null=True, on_delete=models.CASCADE)
    profesionpadre = models.ForeignKey(PersonaProfesion, related_name='profesionpadre', blank=True, null=True, on_delete=models.CASCADE)
    trabajopadre = models.CharField(max_length=200, verbose_name='Lugar de Trabajo del Padre', blank=True, null=True)

    madre = models.CharField(max_length=100, verbose_name='Nombre Completo Madre', blank=True, null=True)
    edadmadre = models.IntegerField(verbose_name='Edad de la Madre', blank=True, null=True)
    estadomadre = models.ForeignKey(PersonaEstadoCivil, related_name='estadomadre', blank=True, null=True, on_delete=models.CASCADE)
    telefmadre = models.CharField(max_length=50, verbose_name='Telefono de la Madre', blank=True, null=True)
    educacionmadre = models.ForeignKey(PersonaEducacion, related_name='educacionmadre', blank=True, null=True, on_delete=models.CASCADE)
    profesionmadre = models.ForeignKey(PersonaProfesion, related_name='profesionmadre', blank=True, null=True, on_delete=models.CASCADE)
    trabajomadre = models.CharField(max_length=200, verbose_name='Lugar de Trabajo de la Madre', blank=True, null=True)

    conyuge = models.CharField(max_length=100, verbose_name='Nombre Completo Conyuge', blank=True, null=True)
    edadconyuge = models.IntegerField(verbose_name='Edad del Conyuge', blank=True, null=True)
    estadoconyuge = models.ForeignKey(PersonaEstadoCivil, related_name='estadoconyuge', blank=True, null=True, on_delete=models.CASCADE)
    telefconyuge = models.CharField(max_length=50, verbose_name='Telefono del Conyuge', blank=True, null=True)
    educacionconyuge = models.ForeignKey(PersonaEducacion, related_name='educacionconyuge', blank=True, null=True, on_delete=models.CASCADE)
    profesionconyuge = models.ForeignKey(PersonaProfesion, related_name='profesionconyuge', blank=True, null=True, on_delete=models.CASCADE)
    trabajoconyuge = models.CharField(max_length=200, verbose_name='Lugar de Trabajo del Conyuge', blank=True, null=True)

    # Antecedentes Patologicos Familiares
    enfermedadpadre = models.CharField(max_length=200, verbose_name='Enfermedades del Padre', blank=True, null=True)
    enfermedadmadre = models.CharField(max_length=200, verbose_name='Enfermedades de la Madre', blank=True, null=True)
    enfermedadabuelos = models.CharField(max_length=200, verbose_name='Enfermedades de Abuelos', blank=True, null=True)
    enfermedadhermanos = models.CharField(max_length=200, verbose_name='Enfermedades de Hermanos', blank=True, null=True)
    enfermedadotros = models.CharField(max_length=200, verbose_name='Enfermedad Otros Familia', blank=True, null=True)


    def __str__(self):
        return str(self.persona)

    class Meta:
        verbose_name = "Persona Extension"
        verbose_name_plural = "Personas Extension"

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.tipolicencia:
            self.tipolicencia = self.tipolicencia.upper().strip()
        if self.padre:
            self.padre = self.padre.upper().strip()
        if self.trabajopadre:
            self.trabajopadre = self.trabajopadre.upper().strip()
        if self.madre:
            self.madre = self.madre.upper().strip()
        if self.trabajomadre:
            self.trabajomadre = self.trabajomadre.upper().strip()
        if self.conyuge:
            self.conyuge = self.conyuge.upper().strip()
        if self.trabajoconyuge:
            self.trabajoconyuge = self.trabajoconyuge.upper().strip()
        if self.enfermedadpadre:
            self.enfermedadpadre = self.enfermedadpadre.upper().strip()
        if self.enfermedadmadre:
            self.enfermedadmadre = self.enfermedadmadre.upper().strip()
        if self.enfermedadabuelos:
            self.enfermedadabuelos = self.enfermedadabuelos.upper().strip()
        if self.enfermedadhermanos:
            self.enfermedadhermanos = self.enfermedadhermanos.upper().strip()
        if self.enfermedadotros:
            self.enfermedadotros = self.enfermedadotros.upper().strip()

        super(PersonaExtension, self).save(force_insert, force_update, using, update_fields)


class PersonaFichaMedica(models.Model):
    #Antecedentes Patologicos Personales
    personaextension = models.ForeignKey(PersonaExtension, on_delete=models.CASCADE)
    vacunas = models.BooleanField(verbose_name='Vacunas Basicas Completas?', default=False)
    nombrevacunas = models.CharField(max_length=100,verbose_name='Nombre las Vacunas', blank=True, null=True)
    enfermedades = models.BooleanField(verbose_name='Enfermedades Cronicas?',default=False)
    nombreenfermedades = models.CharField(max_length=100,verbose_name='Nombre las Enfermedades', blank=True, null=True)
    alergiamedicina = models.BooleanField(verbose_name='Alergias a Medicinas?',default=False)
    nombremedicinas = models.CharField(max_length=100,verbose_name='Nombre las Medicinas', blank=True, null=True)
    alergiaalimento = models.BooleanField(verbose_name='Alergias o Intoxicacion con alimentos?',default=False)
    nombrealimentos = models.CharField(max_length=100,verbose_name='Nombre los Alimentos', blank=True, null=True)
    cirugias = models.BooleanField(verbose_name='Cirugias?',default=False)
    nombrecirugia = models.CharField(max_length=100,verbose_name='Organo Comprometido', blank=True, null=True)
    fechacirugia = models.DateField(verbose_name='Fecha de Operacion', blank=True, null=True)
    aparato = models.BooleanField(verbose_name='Aparatos Ortopedicos?',default=False)
    tipoaparato = models.CharField(max_length=100, verbose_name='Tipo Aparato Ortopedico', blank=True, null=True)

    #Antecedentes Ginecologicos
    gestacion = models.BooleanField(verbose_name='Gestacion?',default=False)
    partos = models.IntegerField(verbose_name='No. Partos', blank=True, null=True)
    abortos = models.IntegerField(verbose_name='No. Abortos', blank=True, null=True)
    cesareas = models.IntegerField(verbose_name='No. Cesareas', blank=True, null=True)
    hijos2 = models.IntegerField(verbose_name='No. Hijos', blank=True, null=True)

    #Habitos
    cigarro = models.BooleanField(verbose_name='Cigarrillo?',default=False)
    numerocigarros = models.IntegerField(verbose_name='No. Cigarrillos por dia', blank=True, null=True)
    tomaalcohol = models.BooleanField(verbose_name='Alcohol?',default=False)
    tipoalcohol = models.CharField(max_length=100,verbose_name='Tipo de Alcohol', blank=True, null=True)
    copasalcohol = models.IntegerField(verbose_name='No. Copas a la Semana', blank=True, null=True)
    tomaantidepresivos = models.BooleanField(verbose_name='Antidepresivos?',default=False)
    antidepresivos = models.CharField(max_length=100, verbose_name='Especifique Antidepresivos', blank=True, null=True)
    tomaotros = models.BooleanField(verbose_name='Otros?',default=False)
    otros = models.CharField(max_length=100, verbose_name='Especifique Otros', blank=True, null=True)
    horassueno = models.IntegerField(verbose_name='No. Horas de Suenno', blank=True, null=True)
    calidadsuenno = models.CharField(max_length=30, choices=CALIDAD_SUENNO, blank=True, null=True)

    def __str__(self):
        return str(self.personaextension)


    class Meta:
        verbose_name = "Persona Ficha Medica"
        verbose_name_plural = "Personas Fichas Medicas"

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.nombrevacunas:
            self.nombrevacunas = self.nombrevacunas.upper().strip()
        if self.nombreenfermedades:
            self.nombreenfermedades = self.nombreenfermedades.upper().strip()
        if self.nombremedicinas:
            self.nombremedicinas = self.nombremedicinas.upper().strip()
        if self.nombrealimentos:
            self.nombrealimentos = self.nombrealimentos.upper().strip()
        if self.nombrecirugia:
            self.nombrecirugia = self.nombrecirugia.upper().strip()
        if self.tipoaparato:
            self.tipoaparato = self.tipoaparato.upper().strip()
        if self.tipoalcohol:
            self.tipoalcohol = self.tipoalcohol.upper().strip()
        if self.antidepresivos:
            self.antidepresivos = self.antidepresivos.upper().strip()
        if self.otros:
            self.otros = self.otros.upper().strip()

        super(PersonaFichaMedica, self).save(force_insert, force_update, using, update_fields)


class PersonaExamenFisico(models.Model):
    # Inspeccion (Observacion General de la Persona - estudiante)
    personafichamedica = models.ForeignKey(PersonaFichaMedica, on_delete=models.CASCADE)
    inspeccion = models.TextField(verbose_name='Observacion General del Alumno', blank=True, null=True)
    usalentes = models.BooleanField(verbose_name='Usa Lentes?',default=False)
    motivo = models.CharField(max_length=100, choices=MOTIVO_LENTES, blank=True, null=True)

    # Signos Vitales
    peso = models.FloatField(verbose_name='PESO', blank=True, null=True)
    talla = models.FloatField(verbose_name='TALLA', blank=True, null=True)
    pa = models.CharField(max_length=50, verbose_name='P/A', blank=True, null=True)
    pulso = models.CharField(max_length=50, verbose_name='PULSO', blank=True, null=True)
    rcar = models.CharField(max_length=50, verbose_name='R. CAR', blank=True, null=True)
    rresp = models.FloatField(verbose_name='R. RESP', blank=True, null=True)
    temp = models.FloatField(verbose_name='TEMP', blank=True, null=True)

    # Observaciones (Especifica las limitantes que impidan cumplir el perfil)
    observaciones = models.TextField(verbose_name='Observacion(especificar limitantes si existen)', blank=True, null=True)

    def __str__(self):
        return str(self.personafichamedica)

    class Meta:
        verbose_name = "Persona Examen Fisico"
        verbose_name_plural = "Personas Examenenes Fisicos"
        ordering = ['personafichamedica__personaextension__persona__apellido1']

class PersonaValoracionImagen(models.Model):
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE)
    observaciones = models.TextField(verbose_name='Observaciones', blank=True, null=True)
    diagnostico = models.FileField(upload_to='diagnostico/%Y/%m/%d', max_length=200)
    imagen = models.FileField(upload_to='imagenrayosx/%Y/%m/%d', max_length=200)
    fecha = models.DateField()
    user = models.ForeignKey(User,blank=True,null=True, on_delete=models.CASCADE)

    def __str__(self):
        return "Imagen "+str(self.persona)

    class Meta:
        verbose_name = "Imagen"
        verbose_name_plural = "Imagenes"

    class Meta:
        verbose_name = "Persona Rayos X"
        verbose_name_plural = "Personas Rayos X"
        ordering = ['persona__apellido1']

    def download_imagen(self):
        if PersonaValoracionImagen.objects.filter(persona=self.persona):
            return PersonaValoracionImagen.objects.filter(persona=self.persona)[:1].get().imagen.url

    def download_diagnostico(self):
        if PersonaValoracionImagen.objects.filter(persona=self.persona):
            return PersonaValoracionImagen.objects.filter(persona=self.persona)[:1].get().diagnostico.url

class PersonaExamenesLab(models.Model):
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE)
    observaciones = models.TextField(verbose_name='Observaciones', blank=True, null=True)
    resultadoslab = models.FileField(upload_to='resultadoslab/%Y/%m/%d', max_length=200)
    fecha = models.DateField()
    user = models.ForeignKey(User,blank=True,null=True, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Persona Examen Laboratorio"
        verbose_name_plural = "Personas Examenes de Laboratorio"
        ordering = ['persona__apellido1']

    def download_resultadolab(self):
        if PersonaExamenesLab.objects.filter(persona=self.persona):
            return PersonaExamenesLab.objects.filter(persona=self.persona)[:1].get().resultadoslab.url

