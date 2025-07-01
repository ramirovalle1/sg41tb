from django.contrib import admin
from socioecon.models import FormaTrabajo, PersonaCubreGasto, TipoHogar, TipoVivienda, MaterialPared, MaterialPiso, CantidadBannoDucha, TipoServicioHigienico, CantidadCelularHogar, CantidadTVColorHogar, CantidadVehiculoHogar, NivelEstudio, OcupacionJefeHogar, GrupoSocioEconomico, InscripcionFichaSocioeconomica, ParentezcoPersona, DatoResidente

admin.site.register(FormaTrabajo)
admin.site.register(ParentezcoPersona)
admin.site.register(PersonaCubreGasto)
admin.site.register(TipoHogar)
admin.site.register(DatoResidente)


class PersonaExtensionAdmin(admin.ModelAdmin):
    list_display = ('persona', 'estadocivil', 'tienelicencia', 'tieneconyuge', 'hijos', 'padre', 'madre', 'conyuge' )
    ordering = ('persona__apellido1','estadocivil')
    search_fields = ('persona__apellido1',)

class PersonaSustentaHogarAdmin(admin.ModelAdmin):
    list_display = ('persona', 'parentezco', 'formatrabajo', 'ingresomensual')
    ordering = ('persona','ingresomensual')
    search_fields = ('formatrabajo',)

class TipoViviendaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo', 'puntaje')
    ordering = ('puntaje',)
    search_fields = ('codigo',)

class MaterialParedAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo', 'puntaje')
    ordering = ('puntaje',)
    search_fields = ('codigo',)

class MaterialPisoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo', 'puntaje')
    ordering = ('puntaje',)
    search_fields = ('codigo',)

class CantidadBannoDuchaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo', 'puntaje')
    ordering = ('puntaje',)
    search_fields = ('codigo',)

class TipoServicioHigienicoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo', 'puntaje')
    ordering = ('puntaje',)
    search_fields = ('codigo',)

class CantidadCelularHogarAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo', 'puntaje')
    ordering = ('puntaje',)
    search_fields = ('codigo',)

class CantidadTVColorHogarAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo', 'puntaje')
    ordering = ('puntaje',)
    search_fields = ('codigo',)

class CantidadVehiculoHogarAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo', 'puntaje')
    ordering = ('puntaje',)
    search_fields = ('codigo',)

class NivelEstudioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo', 'puntaje')
    ordering = ('puntaje',)
    search_fields = ('codigo',)

class OcupacionJefeHogarAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo', 'puntaje')
    ordering = ('puntaje',)
    search_fields = ('codigo',)

class GrupoSocioEconomicoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'umbralinicio', 'umbralfin')
    ordering = ('-umbralinicio',)
    search_fields = ('codigo',)

admin.site.register(TipoVivienda, TipoViviendaAdmin)
admin.site.register(MaterialPiso, MaterialPisoAdmin)
admin.site.register(MaterialPared, MaterialParedAdmin)
admin.site.register(CantidadBannoDucha, CantidadBannoDuchaAdmin)
admin.site.register(TipoServicioHigienico, TipoServicioHigienicoAdmin)
admin.site.register(CantidadCelularHogar, CantidadCelularHogarAdmin)
admin.site.register(CantidadTVColorHogar, CantidadTVColorHogarAdmin)
admin.site.register(CantidadVehiculoHogar, CantidadVehiculoHogarAdmin)
admin.site.register(NivelEstudio, NivelEstudioAdmin)
admin.site.register(OcupacionJefeHogar, OcupacionJefeHogarAdmin)
admin.site.register(GrupoSocioEconomico, GrupoSocioEconomicoAdmin)

class InscripcionFichaSocioeconomicaAdmin(admin.ModelAdmin):
    list_display = ('inscripcion', 'grupoeconomico', 'puntajetotal', 'tipohogar')
    ordering = ('inscripcion__persona__apellido1', )
    search_fields = ('inscripcion__persona__apellido1', 'inscripcion__persona__apellido2', 'inscripcion__persona__nombres', 'inscripcion__persona__cedula')

admin.site.register(InscripcionFichaSocioeconomica, InscripcionFichaSocioeconomicaAdmin)