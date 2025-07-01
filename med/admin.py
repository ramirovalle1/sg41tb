from django.contrib import admin
from med.models import PersonaEstadoCivil, PersonaEducacion, PersonaProfesion, PersonaExtension, PersonaFichaMedica, PersonaExamenFisico


class PersonaEstadoCivilAdmin(admin.ModelAdmin):
    list_display = ('nombre', )
    ordering = ('nombre',)
    search_fields = ('nombre',)

class PersonaEducacionAdmin(admin.ModelAdmin):
    list_display = ('nombre', )
    ordering = ('nombre',)
    search_fields = ('nombre',)

class PersonaProfesionAdmin(admin.ModelAdmin):
    list_display = ('nombre', )
    ordering = ('nombre',)
    search_fields = ('nombre',)


admin.site.register(PersonaEstadoCivil, PersonaEstadoCivilAdmin)
admin.site.register(PersonaEducacion, PersonaEducacionAdmin)
admin.site.register(PersonaProfesion, PersonaProfesionAdmin)


class PersonaExtensionAdmin(admin.ModelAdmin):
    list_display = ('persona', 'estadocivil', 'tienelicencia', 'tieneconyuge', 'hijos', 'padre', 'madre', 'conyuge' )
    ordering = ('persona__apellido1','estadocivil')
    search_fields = ('persona__apellido1',)
    list_filter = ('persona',)

class PersonaFichaMedicaAdmin(admin.ModelAdmin):
    list_display = ('personaextension', 'vacunas', 'enfermedades', 'alergiamedicina', 'alergiaalimento', 'cirugias', 'aparato', 'cigarro','tomaalcohol' )
    ordering = ('personaextension__persona__apellido1','vacunas','enfermedades')
    search_fields = ('personaextension__persona__apellido1',)
    list_filter = ('personaextension',)

class PersonaExamenFisicoAdmin(admin.ModelAdmin):
    list_display = ('personafichamedica', 'usalentes', 'peso', 'talla', 'pa', 'pulso', 'rcar', 'rresp','temp' )
    ordering = ('personafichamedica__personaextension__persona__apellido1','usalentes','peso','talla')
    search_fields = ('personafichamedica__personaextension__persona__apellido1',)
    list_filter = ('personafichamedica',)

admin.site.register(PersonaExtension, PersonaExtensionAdmin)
admin.site.register(PersonaFichaMedica, PersonaFichaMedicaAdmin)
admin.site.register(PersonaExamenFisico, PersonaExamenFisicoAdmin)
