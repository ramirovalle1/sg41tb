from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_str
from sga.models import TipoMedicamento,TipoOficio
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.core.paginator import Paginator
from sga.commonviews import addUserData, ip_client_address
from django.template import RequestContext
from sga.forms import TipoMedicamentoForm, TipoOficioForm
from datetime import datetime

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
# @secure_module
# @transaction.atomic()
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action == 'add':
                f= TipoOficioForm(request.POST)
                if f.is_valid():
                    tipooficio = TipoOficio(
                                            nombre = f.cleaned_data['nombre'])
                    tipooficio.save()
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(tipooficio).pk,
                        object_id       = tipooficio.id,
                        object_repr     = force_str(tipooficio),
                        action_flag     = ADDITION,
                        change_message  = 'Adicionado Tipo de Oficio (' + client_address + ')' )
                    return HttpResponseRedirect("/tipooficio")
                return HttpResponseRedirect("/tipooficio?action=add")
            elif action == 'edit':
                f= TipoOficioForm(request.POST)
                if f.is_valid():
                    tipooficio = TipoOficio.objects.get(pk=request.POST['id'])
                    tipooficio.nombre = f.cleaned_data['nombre']
                    tipooficio.save()
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(tipooficio).pk,
                        object_id       = tipooficio.id,
                        object_repr     = force_str(tipooficio),
                        action_flag     = ADDITION,
                        change_message  = 'Editado Tipo de Oficio (' + client_address + ')' )
                    return HttpResponseRedirect("/tipooficio")
                return HttpResponseRedirect("/tipooficio?action=edit")

        else:
            data = {'title': 'Tipos de Oficio'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']
                if action == 'add':
                    data['title']= 'Ingresar Tipo'

                    form = TipoOficioForm()
                    data['form']= form
                    return render(request ,"oficios/addtipooficio.html" ,  data)
                elif action == 'edit':
                    data['title']= 'Editar Tipo Oficio'
                    data['tipooficio']= TipoOficio.objects.get(id=request.GET['id'])

                    form = TipoOficioForm(instance=data['tipooficio'])
                    data['form']= form
                    return render(request ,"oficios/edittipooficio.html" ,  data)

            else:
                search = None
                todos = None

                if 's' in request.GET:
                    search = request.GET['s']
                if 't' in request.GET:
                    todos = request.GET['t']
                if search:
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')

                    tipooficio = TipoOficio.objects.filter(nombre__icontains=search).order_by('nombre')
                else:
                    tipooficio = TipoOficio.objects.all().order_by('nombre')

                paging = MiPaginador(tipooficio, 30)
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
                data['tipooficio'] = page.object_list
                return render(request ,"oficios/tiposoficio.html" ,  data)
    except:
        return HttpResponseRedirect("/")
