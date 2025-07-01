from django.contrib import admin
from ext.models import *

class EntidadImportacionAdmin(admin.ModelAdmin):
    list_display = ('nombre','url','codigo')
    ordering = ('nombre',)
    search_fields = ('nombre',)
    list_filter = ('nombre','url')

admin.site.register(EntidadImportacion, EntidadImportacionAdmin)

class AsignaturaExternaAdmin(admin.ModelAdmin):
    list_display = ('entidad','asignatura','asignaturaext')
    ordering = ('entidad','asignatura',)
    search_fields = ('entidad','asignatura','asignaturaext')
    list_filter = ('entidad','asignatura','asignaturaext')

admin.site.register(AsignaturaExterna, AsignaturaExternaAdmin)