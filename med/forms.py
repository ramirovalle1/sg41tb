# -*- coding: latin-1 -*-
import os
from django import forms
from datetime import datetime
from django.forms.models import ModelForm, ModelChoiceField
from django.forms.widgets import DateTimeInput
from med.models import PersonaEstadoCivil, PersonaEducacion, PersonaProfesion, CALIDAD_SUENNO, MOTIVO_LENTES
from sga.models import Persona

class ExtFileField(forms.FileField):
    """
    * max_upload_size - a number indicating the maximum file size allowed for upload.
            500Kb - 524288
            1MB - 1048576
            2.5MB - 2621440
            5MB - 5242880
            10MB - 10485760
            20MB - 20971520
            50MB - 5242880
            100MB 104857600
            250MB - 214958080
            500MB - 429916160
    t = ExtFileField(ext_whitelist=(".pdf", ".txt"), max_upload_size=)
    """
    def __init__(self, *args, **kwargs):
        ext_whitelist = kwargs.pop("ext_whitelist")
        self.ext_whitelist = [i.lower() for i in ext_whitelist]
        self.max_upload_size = kwargs.pop("max_upload_size")
        super(ExtFileField, self).__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):
        upload = super(ExtFileField, self).clean(*args, **kwargs)
        if upload:
            size = upload.size
            filename = upload.name
            ext = os.path.splitext(filename)[1]
            ext = ext.lower()

            if size == 0  or ext not in self.ext_whitelist or size>self.max_upload_size:
                raise forms.ValidationError("Tipo de fichero o tamanno no permitido!")
class FixedForm(ModelForm):

    date_fields = []

    def __init__(self, *args, **kwargs):
        super(ModelForm, self).__init__(*args, **kwargs)
        for f in self.date_fields:
            self.fields[f].widget.format = '%d-%m-%Y'
            self.fields[f].input_formats = ['%d-%m-%Y']


class PersonaExtensionForm(forms.Form):
    #PERSONA EXTENSION
    estadocivil = forms.ModelChoiceField(PersonaEstadoCivil.objects, label='Estado Civil (*)')
    tienelicencia = forms.BooleanField(label='Licencia de Conduccion', required=False)
    tipolicencia = forms.CharField(max_length=50, label='Tipo de Licencia', required=False)
    telefonos = forms.CharField(max_length=100, label="Telefonos de Familiar", required=False)
    tieneconyuge = forms.BooleanField(label="Conyuge", required=False)
    hijos = forms.IntegerField(label="No. de Hijos", required=False)

class PersonaFamiliaForm(forms.Form):
    # Datos Familiares
    padre = forms.CharField(max_length=100, label='Nombre Completo', required=False)
    edadpadre = forms.IntegerField(label='Edad', required=False)
    estadopadre = forms.ModelChoiceField(PersonaEstadoCivil.objects, label='Estado Civil', required=False)
    telefpadre = forms.CharField(max_length=50, label='Telefono', required=False)
    educacionpadre = forms.ModelChoiceField(PersonaEducacion.objects, label='Educacion', required=False)
    profesionpadre = forms.ModelChoiceField(PersonaProfesion.objects, label='Profesion', required=False)
    trabajopadre = forms.CharField(max_length=200, label='Trabajo', required=False)

    madre = forms.CharField(max_length=100, label='Nombre Completo', required=False)
    edadmadre = forms.IntegerField(label='Edad', required=False)
    estadomadre = forms.ModelChoiceField(PersonaEstadoCivil.objects, label='Estado Civil', required=False)
    telefmadre = forms.CharField(max_length=50, label='Telefono', required=False)
    educacionmadre = forms.ModelChoiceField(PersonaEducacion.objects, label='Educacion', required=False)
    profesionmadre = forms.ModelChoiceField(PersonaProfesion.objects, label='Profesion', required=False)
    trabajomadre = forms.CharField(max_length=200, label='Trabajo', required=False)

    conyuge = forms.CharField(max_length=100, label='Nombre Completo', required=False)
    edadconyuge = forms.IntegerField(label='Edad', required=False)
    estadoconyuge = forms.ModelChoiceField(PersonaEstadoCivil.objects, label='Estado Civil', required=False)
    telefconyuge = forms.CharField(max_length=50, label='Telefono', required=False)
    educacionconyuge = forms.ModelChoiceField(PersonaEducacion.objects, label='Educacion', required=False)
    profesionconyuge = forms.ModelChoiceField(PersonaProfesion.objects, label='Profesion', required=False)
    trabajoconyuge = forms.CharField(max_length=200, label='Trabajo', required=False)


class PersonaPatologicoForm(forms.Form):
    #Antecedentes Patologicos Personales
    vacunas = forms.BooleanField(label='Vacunas Basicas Completas?', required=False)
    nombrevacunas = forms.CharField(max_length=100,label='Nombre las Vacunas', required=False)
    enfermedades = forms.BooleanField(label='Enfermedades Cronicas?', required=False)
    nombreenfermedades = forms.CharField(max_length=100,label='Nombre las Enfermedades', required=False)
    alergiamedicina = forms.BooleanField(label='Alergias a Medicinas?', required=False)
    nombremedicinas = forms.CharField(max_length=100,label='Nombre las Medicinas', required=False)
    alergiaalimento = forms.BooleanField(label='Alergias o Intoxicacion con alimentos?', required=False)
    nombrealimentos = forms.CharField(max_length=100,label='Nombre los Alimentos', required=False)
    cirugias = forms.BooleanField(label='Cirugias?', required=False)
    nombrecirugia = forms.CharField(max_length=100,label='Organos Comprometidos', required=False)
    fechacirugia = forms.DateField(input_formats=['%d-%m-%Y'],widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha Cirugia", required=False)
    aparato = forms.BooleanField(label='Aparatos Ortopedicos?', required=False)
    tipoaparato = forms.CharField(max_length=100, label='Tipo Aparato Ortopedico', required=False)

class PersonaGinecologicoForm(forms.Form):
    #Antecedentes Ginecologicos
    gestacion = forms.BooleanField(label='Gestacion?', required=False)
    partos = forms.IntegerField(label='No. Partos', required=False)
    abortos = forms.IntegerField(label='No. Abortos', required=False)
    cesareas = forms.IntegerField(label='No. Cesareas', required=False)
    hijos2 = forms.IntegerField(label='No. Hijos', required=False)

class PersonaHabitoForm(forms.Form):
    #Habitos
    cigarro = forms.BooleanField(label='Cigarrillo?', required=False)
    numerocigarros = forms.IntegerField(label='No. Cigarrillos por dia', required=False)
    tomaalcohol = forms.BooleanField(label='Alcohol?', required=False)
    tipoalcohol = forms.CharField(max_length=100,label='Tipo de Alcohol', required=False)
    copasalcohol = forms.IntegerField(label='No. Copas a la Semana', required=False)
    tomaantidepresivos = forms.BooleanField(label='Antidepresivos?', required=False)
    antidepresivos = forms.CharField(max_length=100, label='Especifique Antidepresivos', required=False)
    tomaotros = forms.BooleanField(label='Otros?', required=False)
    otros = forms.CharField(max_length=100, label='Especifique Otros', required=False)
    horassueno = forms.IntegerField(label='No. Horas de Suenno (*)', required=False)
    calidadsuenno = forms.ChoiceField(required=False, choices=CALIDAD_SUENNO, label='Calidad de Suenno')

class PersonaPatologicoFamiliarForm(forms.Form):
    # Antecedentes Patologicos Familiares
    enfermedadpadre = forms.CharField(max_length=200, label='Padre', required=False)
    enfermedadmadre = forms.CharField(max_length=200, label='Madre', required=False)
    enfermedadabuelos = forms.CharField(max_length=200, label='Abuelos', required=False)
    enfermedadhermanos = forms.CharField(max_length=200, label='Hermanos', required=False)
    enfermedadotros = forms.CharField(max_length=200, label='Familia', required=False)



class PersonaExamenFisicoForm(forms.Form):

    # PERSONA EXAMEN FISICO
    inspeccion = forms.CharField(widget=forms.Textarea, label='Inspeccion', required=False)
    usalentes = forms.BooleanField(label='Usa Lentes?', required=False)
    motivo = forms.ChoiceField(choices=MOTIVO_LENTES, required=False)

    # Signos Vitales
    peso = forms.FloatField(label='PESO', required=False)
    talla = forms.FloatField(label='TALLA', required=False)
    pa = forms.CharField(label='P/A', required=False)
    # pulso = forms.CharField(label='PULSO', required=False)
    pulso = forms.FloatField(label='PULSO', required=False)
    # rcar = forms.CharField(label='R.CAR', required=False)
    rcar = forms.FloatField(label='R.CAR', required=False)
    rresp = forms.FloatField(label='R.RESP', required=False)
    temp = forms.FloatField(label='TEMP', required=False)

    observaciones = forms.CharField(widget=forms.Textarea, label='Observaciones', required=False)


class PersonaRayosxForm(forms.Form):
    # Diagnostico Rayos X
    observaciones = forms.CharField(widget=forms.Textarea, label='Observaciones', required=False)
    diagnostico = ExtFileField(label='Seleccione Archivo',help_text='Tamano Maximo permitido 500Kb, en formato doc, docx, xls, xlsx, pdf, ppt, pptx, rar, zip , odp',ext_whitelist=(".doc", ".docx", ".xls", ".xlsx", ".pdf", ".ppt", ".pptx", ".zip", ".rar",".odp"),max_upload_size=524288,required=False)
    imagen = ExtFileField(label='Seleccione Imagen',help_text='Tamano Maximo permitido 500Kb, en formato jpg, png',ext_whitelist=(".png", ".jpg"),max_upload_size=524288,required=False)

    class Meta:
        model = Persona
        exclude = ('persona')


class PersonaExamenesLabForm(forms.Form):
    # Examenes de Laboratorio
    observaciones = forms.CharField(widget=forms.Textarea, label='Observaciones', required=False)
    resultadoslab = ExtFileField(label='Seleccione Archivo',help_text='Tamano Maximo permitido 500Kb, en formato doc, docx, xls, xlsx, pdf, ppt, pptx, rar, zip , odp',ext_whitelist=(".doc", ".docx", ".xls", ".xlsx", ".pdf", ".ppt", ".pptx", ".zip", ".rar",".odp"),max_upload_size=524288,required=False)

    class Meta:
        model = Persona
        exclude = ('persona')





