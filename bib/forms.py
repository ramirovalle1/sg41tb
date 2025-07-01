# -*- coding: latin-1 -*-

from django import forms
from django.forms.models import ModelForm
from bib.models import TipoDocumento, Idioma
from sga.forms import ExtFileField
from sga.models import Persona, Sede, Inscripcion
from django.forms.widgets import DateTimeInput, HiddenInput


class FixedForm(ModelForm):

    date_fields = []

    def __init__(self, *args, **kwargs):
        super(ModelForm, self).__init__(*args, **kwargs)
        for f in self.date_fields:
            self.fields[f].widget.format = '%d-%m-%Y'
            self.fields[f].input_formats = ['%d-%m-%Y']


class DocumentoForm(forms.Form):
    codigo = forms.CharField(max_length=20, label=u'Código')
    codigodewey = forms.CharField(max_length=200, label=u'Código Dewey', required=False)

    tipo = forms.ModelChoiceField(TipoDocumento.objects, label='Tipo de Documento')
    tutor = forms.CharField(max_length=200, label=u'Tutor Tésis', required=False)

    tutor1 = forms.CharField(label='Tutor',required=False)
    tutor1_id = forms.IntegerField(required=False)

    nombre = forms.CharField(max_length=200, label=u'Título')
    autor = forms.CharField(max_length=200, label='Autor(es)',required=False)

    autor1 = forms.CharField(label='Autor',required=False)
    autor1_id = forms.IntegerField(required=False)

    carrera = forms.CharField(label='Carrera',required=False)
    carrera_id = forms.IntegerField(required=False)

    anno = forms.IntegerField(label=u'Año de Publicacion')
    emision = forms.CharField(max_length=40, label=u'Emisión', required=False)
    editora = forms.CharField(max_length=200, label='Editora', required=False)
    sede = forms.ModelChoiceField(Sede.objects, label='Sede')
    idioma = forms.ModelChoiceField(Idioma.objects, label='Idioma')

    paginas = forms.IntegerField(label=u'No. Páginas')
    copias = forms.IntegerField(label='No. Copias')

    fisico = forms.BooleanField(label=u'Es Físico?', required=False)

    digital = ExtFileField(label='Archivo Digital',help_text='Tamano Maximo permitido 60Mb, en formato doc, docx, xls, xlsx, pdf, zip, rar, NO deben contener espacios ni caracteres especiales',ext_whitelist=(".doc", ".docx", ".xls", ".xlsx", ".pdf", ".zip", ".rar"),max_upload_size=68157440, required=False)
    # OC 25-enero-2019 para que puedan subir archivos digitales de mas capacidad
    # digital = ExtFileField(label='Archivo Digital',help_text='Tamano Maximo permitido 250Mb, en formato doc, docx, xls, xlsx, pdf, zip, rar, NO deben contener espacios ni caracteres especiales',ext_whitelist=(".doc", ".docx", ".xls", ".xlsx", ".pdf", ".zip", ".rar"),max_upload_size=262144000, required=False)
    portada = ExtFileField(label='Imagen de Portada',help_text='Tamano Maximo permitido 4MB, en formato jpg, png,NO deben contener espacios ni caracteres especiales',ext_whitelist=(".png", ".jpg"),max_upload_size=4194304, required=False)

    palabrasclaves = forms.CharField(widget=forms.Textarea, label='Palabras Claves')

    resumen = forms.CharField(widget=forms.Textarea, label='Resumen', required=False)



class PrestamoDocumentoForm(forms.Form):
    persona = forms.CharField(label='Persona que solicita')
    persona_id = forms.IntegerField(required=False)
    tiempo = forms.IntegerField(label='Tiempo Prestamo (Horas)')
    entregado = forms.BooleanField(label='Entregado?', required=False)


class AutoresTesisForm(forms.Form):
    autor1 = forms.CharField(label='Autor')
    autor1_id = forms.IntegerField(required=False)
    nota = forms.FloatField(label="Nota", required=True)
    plagio = forms.FloatField(label="%Plagio",required=False)
    fechasustentacion = forms.DateField(input_formats=['%d-%m-%Y'],widget=DateTimeInput(format='%d-%m-%Y'), label="Fecha Sustentacion")
    observaciones = forms.CharField(widget=forms.Textarea, label='Observaciones', required=False)



class PlagioForm(forms.Form):
    autor1 = forms.CharField(label='Autor')
    autor1_id = forms.IntegerField(required=False)
    plagio = forms.FloatField(label="%Plagio",required=False)


