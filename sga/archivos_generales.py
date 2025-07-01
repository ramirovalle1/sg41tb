from django.contrib.admin.models import LogEntry, ADDITION, DELETION, CHANGE
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.forms import model_to_dict
from django.utils.encoding import force_str
from sga.models import Archivo
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.core.paginator import Paginator
from sga.commonviews import addUserData, ip_client_address
from django.template import RequestContext
from sga.forms import EvidenciaForm
from datetime import datetime
from settings import  ARCHIVO_TIPO_GENERAL
from decorators import secure_module


class MiPaginador(Paginator):
    def __init__(self, object_list, per_page, orphans=0, allow_empty_first_page=True, rango=5):
        super(MiPaginador,self).__init__(object_list, per_page, orphans=orphans, allow_empty_first_page=allow_empty_first_page)
        self.rango = rango
        self.paginas = []
        self.primera_pagina = False
        self.ultima_pagina = False

    def rangos_paginado(self, pagina):
        left = pagina - self.rango
        right = pagina + self.rango
        if left<1:
            left=1
        if right>self.num_pages:
            right = self.num_pages
        self.paginas = range(left, right+1)
        self.primera_pagina = True if left>1 else False
        self.ultima_pagina = True if right<self.num_pages else False
        self.ellipsis_izquierda = left-1
        self.ellipsis_derecha = right+1

@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action == 'add':
                try:
                    f= EvidenciaForm(request.POST,request.FILES)
                    if f.is_valid():
                        archivo = Archivo(tipo_id = ARCHIVO_TIPO_GENERAL,
                                          nombre = f.cleaned_data['nombre'],
                                          archivo = request.FILES['archivo'],
                                          fecha=datetime.now().date())
                        archivo.save()
                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(archivo).pk,
                            object_id       = archivo.id,
                            object_repr     = force_str(archivo),
                            action_flag     = ADDITION,
                            change_message  = 'Adicionado Archivo General (' + client_address + ')' )

                        return HttpResponseRedirect("/archivos_generales")
                except Exception as e:
                    return HttpResponseRedirect("/archivos_generales?action=add")
                return HttpResponseRedirect("/archivos_generales?action=add")
            elif action == 'edit':
                f= EvidenciaForm(request.POST,request.FILES)
                if f.is_valid():
                    archivo = Archivo.objects.get(pk=request.POST['id'])
                    archivo.nombre = f.cleaned_data['nombre']
                    if 'archivo' in request.FILES:
                        archivo.archivo =  request.FILES['archivo']
                    archivo.save()
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(archivo).pk,
                        object_id       = archivo.id,
                        object_repr     = force_str(archivo),
                        action_flag     = CHANGE,
                        change_message  = 'Editado   Archivo General (' + client_address + ')' )
                    return HttpResponseRedirect("/archivos_generales")
                return HttpResponseRedirect("/archivos_generales?action=edit")

        else:
            data = {'title': 'Archivos Generales'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']
                if action == 'add':
                    data['title']= 'Agregar Archivo'

                    form = EvidenciaForm()
                    data['form']= form
                    return render(request ,"archivos_generales/add.html" ,  data)
                elif action == 'edit':
                    data['title']= 'Cambiar Archivo'
                    archivo= Archivo.objects.get(id=request.GET['id'])
                    data['archivo'] = archivo
                    initial = model_to_dict(archivo)
                    data['form'] = EvidenciaForm(initial=initial)
                    return render(request ,"archivos_generales/edit.html" ,  data)
                elif action == 'eliminar':
                    archivo = Archivo.objects.filter(pk=request.GET['id'])[:1].get()
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(archivo).pk,
                        object_id       = archivo.id,
                        object_repr     = force_str(archivo),
                        action_flag     = DELETION,
                        change_message  = 'Eliminado Archivo General (' + client_address + ')' )
                    archivo.delete()
                    return HttpResponseRedirect("/archivos_generales")

            else:
                search = None
                todos = None
                archivo = Archivo.objects.filter(tipo__id=ARCHIVO_TIPO_GENERAL).order_by('nombre')

                paging = MiPaginador(archivo, 30)
                p = 1
                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                    page = paging.page(p)
                except:
                    page = paging.page(p)

                data['paging'] = paging
                data['rangospaging'] = paging.rangos_paginado(p)
                data['page'] = page
                data['search'] = search if search else ""
                data['todos'] = todos if todos else ""
                data['archivo'] = page.object_list
                return render(request ,"archivos_generales/archivos.html" ,  data)
    except:
        return HttpResponseRedirect("/")
