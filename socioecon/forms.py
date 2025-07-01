# -*- coding: latin-1 -*-

from django import forms
from socioecon.models import FormaTrabajo, TipoHogar, PersonaCubreGasto, NivelEstudio, OcupacionJefeHogar, TipoVivienda, MaterialPared, MaterialPiso, CantidadBannoDucha, \
     TipoServicioHigienico, CantidadTVColorHogar, CantidadVehiculoHogar, CantidadCelularHogar, ParentezcoPersona,OcupacionEstudiante,IngresosEstudiante,BonoFmlaEstudiante


#SUSTENTO DEL HOGAR FORM
class SustentoHogarForm(forms.Form):
    persona = forms.CharField(max_length=50, label='Persona que sustenta')
    parentezco = forms.ModelChoiceField(ParentezcoPersona.objects, label='Parentezco')
    formatrabajo = forms.ModelChoiceField(FormaTrabajo.objects, label='Formas de Trabajo')
    ingresomensual = forms.FloatField(label='Ingreso Mensual')

class TipoHogarForm(forms.Form):
    tipohogar = forms.ModelChoiceField(TipoHogar.objects, label='Tipos de Hogar')

class PersonaCubreGastoForm(forms.Form):
    personacubregasto = forms.ModelChoiceField(PersonaCubreGasto.objects, label='Quien cubre los gastos')
    otroscubregasto = forms.CharField(label='Especifique OTROS', required=False)

class NivelEstudioForm(forms.Form):
    niveljefehogar = forms.ModelChoiceField(NivelEstudio.objects, label='Nivel de Esudios')

class OcupacionJefeHogarForm(forms.Form):
    ocupacionjefehogar = forms.ModelChoiceField(OcupacionJefeHogar.objects, label='Ocupacion')

class TipoViviendaForm(forms.Form):
    tipovivienda = forms.ModelChoiceField(TipoVivienda.objects, label='Tipo de Vivienda')

class MaterialParedForm(forms.Form):
    materialpared = forms.ModelChoiceField(MaterialPared.objects, label='Material de Paredes')

class MaterialPisoForm(forms.Form):
    materialpiso = forms.ModelChoiceField(MaterialPiso.objects, label='Material de Piso')

class CantidadBannoDuchaForm(forms.Form):
    cantbannoducha = forms.ModelChoiceField(CantidadBannoDucha.objects, label=u'Baños con ducha')

class TipoServicioHigienicoForm(forms.Form):
    tiposervhig = forms.ModelChoiceField(TipoServicioHigienico.objects, label='Servicio Higienico')

class CantidadTVColorHogarForm(forms.Form):
    canttvcolor = forms.ModelChoiceField(CantidadTVColorHogar.objects, label='Cantidad TV a color')

class CantidadVehiculoHogarForm(forms.Form):
    cantvehiculos = forms.ModelChoiceField(CantidadVehiculoHogar.objects, label='Cantidad Vehiculos')

class CantidadCelularHogarForm(forms.Form):
    cantcelulares = forms.ModelChoiceField(CantidadCelularHogar.objects, label='Cantidad Celulares')

class OcupacionEstudianteForm(forms.Form):
    ocupacion = forms.ModelChoiceField(OcupacionEstudiante.objects, label='Ocupacion de Estudiante')

class IngresosEstudianteForm(forms.Form):
    ingresos = forms.ModelChoiceField(IngresosEstudiante.objects, label='Ingresos Estudiante')

class BonoFmlaEstudianteForm(forms.Form):
    bono = forms.ModelChoiceField(BonoFmlaEstudiante.objects, label='Recibe Bono')
