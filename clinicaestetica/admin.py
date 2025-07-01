from django.contrib import admin
from clinicaestetica.models import TipoHabito, TipoEstetico, ParametroEstetico, Tratamiento, TipoPersona, TratamientoPrecio, FichaMedica

__author__ = 'jurgiles'
admin.site.register(TipoHabito)
admin.site.register(TipoEstetico)
admin.site.register(ParametroEstetico)
admin.site.register(Tratamiento)
admin.site.register(TipoPersona)
admin.site.register(TratamientoPrecio)
admin.site.register(FichaMedica)
