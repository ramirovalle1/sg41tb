from core.my_form import ExtFileField, FixedForm, MY_Form
from django import forms
from django.db.models import Q
from settings import ALUMNOS_GROUP_ID


class FirmaECForm(MY_Form):
    password = forms.CharField(label=u'Contraseña', required=True,
                               widget=forms.PasswordInput(
                                   attrs={'class': 'form-control', "col": "5", 'autocomplete': False}),
                               error_messages={'required': 'Favor ingrese la contraseña'})
    firma = ExtFileField(label=u'Firma Electrónica', required=True,
                         help_text=u'Formato permitido .p12 y .pfx',
                         ext_whitelist=(".p12", ".pfx"), max_upload_size=52428800,
                         error_messages={'required': 'Formato requerido .p12 y .pfx',
                                         'max_upload_size': 'Tamaño Máximo permitido 50Mb, en formato .p12 y .pfx'},
                         widget=forms.FileInput(
                             attrs={"class": "form-control w-100", "col": "7", 'autocomplete': False}))

    def clean_firma(self):
        firma = self.files.get('firma', None)
        if firma:
            # Example of additional validation: check file size
            if firma.size > self.fields['firma'].max_upload_size:
                raise forms.ValidationError('La supera el tamaño máximo permitido de 50MB.')

            # Example of additional validation: check file extension
            ext = firma.name.split('.')[-1].lower()
            if f".{ext}" not in self.fields['firma'].ext_whitelist:
                raise forms.ValidationError('El archivo debe estar en formato requerido .p12 y .pfx')

        return firma

    def clean(self, *args, **kwargs):
        cleaned_data = super(FirmaECForm, self).clean(*args, **kwargs)
        return cleaned_data


class FirmaActaCalificacionForm(MY_Form):
    from sga.models import Persona
    from firmaec.models import FirmaActaCalificacion
    orden = forms.IntegerField(label=u'Orden',
                               initial=0,
                               required=True,
                               error_messages={'required': 'Campo no debe estar vacío'},
                               widget=forms.NumberInput(attrs={'class': 'form-control', 'col': '6'}))
    tipo = forms.ChoiceField(label='Tipo de Responsable',
                             required=True,
                             choices=FirmaActaCalificacion.TiposResponsable.choices,
                             error_messages={'required': 'Campo no debe estar vacío'},
                             widget=forms.Select(attrs={'class': 'form-control form-select', 'col': '6'})
                             )
    responsable = forms.ModelChoiceField(label='Responsable',
                                         queryset=Persona.objects.none(),
                                         required=True,
                                         error_messages={'required': 'Campo no debe estar vacío'},
                                         widget=forms.Select(attrs={'class': 'form-control form-select', 'col': '12'}))
    cargo = forms.ChoiceField(label='Cargo',
                              required=True,
                              choices=FirmaActaCalificacion.CargosResponsable.choices,
                              error_messages={'required': 'Campo no debe estar vacío'},
                              widget=forms.Select(attrs={'class': 'form-control form-select', 'col': '12'})
                              )

    def set_responsable(self, id):
        from sga.models import Persona
        ePersonas = Persona.objects.filter(id=id)
        self.fields['responsable'].queryset = ePersonas

    def edit(self, eMateria, tipo):
        from sga.models import Persona, ProfesorMateria, Profesor
        ePersonas = Persona.objects.none()
        # Filtrar según el tipo
        if tipo == 1:
            # Filtrar docentes de la materia
            custom_filter = Q(
                id__in=ProfesorMateria.objects.values_list('profesor__persona__id', flat=True).filter(materia=eMateria,
                                                                                                      profesor__activo=True))
            ePersonas = Persona.objects.filter(custom_filter).order_by('apellido1', 'apellido2')
        elif tipo == 2:
            # Filtrar profesores que no son docentes de la materia
            ids_exclude = ProfesorMateria.objects.values_list('profesor__persona__id', flat=True).filter(
                materia=eMateria, profesor__activo=True)
            custom_filter = Q(id__in=Profesor.objects.values_list('persona__id', flat=True).filter(activo=True).exclude(
                id__in=ids_exclude))
            ePersonas = Persona.objects.filter(custom_filter).order_by('apellido1', 'apellido2')
        elif tipo == 3:
            # Filtrar administrativos excluyendo docentes y grupos específicos
            eProfesorMaterias = ProfesorMateria.objects.values_list('profesor__persona__id', flat=True).filter(
                materia=eMateria, profesor__activo=True)
            eProfesores = Profesor.objects.values_list('persona__id', flat=True).filter(activo=True)
            gruposexcluidos = [ALUMNOS_GROUP_ID]
            ePersonas = Persona.objects.exclude(
                Q(usuario__groups__id__in=gruposexcluidos) | Q(id__in=eProfesorMaterias) | Q(
                    id__in=eProfesores)).order_by('apellido1', 'apellido2')
        self.fields['responsable'].queryset = ePersonas

    def clean_orden(self):
        orden = self.cleaned_data['orden']
        if orden <= 0:
            raise forms.ValidationError("Orden debe ser mayor a cero")
        return orden

    def clean(self, *args, **kwargs):
        cleaned_data = super(FirmaActaCalificacionForm, self).clean(*args, **kwargs)
        return cleaned_data
