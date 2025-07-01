from django.contrib import admin
from bib.models import TipoDocumento, ReferenciaWeb, PrestamoDocumento, Documento, ConsultaBiblioteca, OtraBibliotecaVirtual, Idioma, TipoProyecto


class ReferenciaWebAdmin(admin.ModelAdmin):
    list_display = ('url', 'nombre', 'logo')
    ordering = ('url', 'nombre')
    search_fields = ('nombre',)

class OtraBibliotecaVirtualAdmin(admin.ModelAdmin):
    list_display = ('url', 'nombre', 'logo', 'descripcion')
    ordering = ('url', 'nombre')
    search_fields = ('nombre','descripcion')



class ConsultaBibliotecaAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'hora', 'persona', 'busqueda')
    ordering = ('fecha', 'hora')
    search_fields = ('persona__apellido1','persona__apellido2','persona__nombres')

class PrestamoDocumentoAdmin(admin.ModelAdmin):
    list_display = ('documento', 'persona', 'entregado', 'tiempo', 'responsableentrega', 'fechaentrega', 'horaentrega', 'recibido' , 'responsablerecibido', 'fecharecibido' , 'horarecibido')
    ordering = ('fechaentrega', 'horaentrega')
    search_fields = ('persona__apellido1','persona__apellido2','persona__nombres', 'documento__codigo', 'documento__nombre', 'documento__autor')

class DocumentoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'autor', 'tipo', 'anno', 'emision' , 'palabrasclaves', 'digital' , 'fisico', 'copias')
    ordering = ('codigo', 'autor' , 'tipo')
    search_fields = ('persona__apellido1','persona__apellido2','persona__nombres', 'codigo', 'nombre', 'autor', 'tipo')
    list_filter = ('tipo','fisico')

class TipoProyectoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'descripcion')
    ordering = ('codigo', )
    search_fields = ('codigo','descripcion')
    list_filter = ('codigo',)


admin.site.register(TipoDocumento)
admin.site.register(Idioma)
admin.site.register(ReferenciaWeb, ReferenciaWebAdmin)
admin.site.register(OtraBibliotecaVirtual,OtraBibliotecaVirtualAdmin)

admin.site.register(ConsultaBiblioteca, ConsultaBibliotecaAdmin)
admin.site.register(PrestamoDocumento, PrestamoDocumentoAdmin)
admin.site.register(Documento, DocumentoAdmin)
admin.site.register(TipoProyecto, TipoProyectoAdmin)



