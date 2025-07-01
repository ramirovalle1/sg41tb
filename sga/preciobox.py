import json
from django.contrib.admin.models import ADDITION, LogEntry, CHANGE, DELETION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.forms import model_to_dict
from django.utils.encoding import force_str
from sga.models import PrecioConsulta
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.core.paginator import Paginator
from sga.commonviews import addUserData, ip_client_address
from django.template import RequestContext
from sga.forms import SuministroBoxForm, ConvenioBoxForm, PrecioBoxForm
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
                pass
                f= PrecioBoxForm(request.POST)
                if f.is_valid():
                    if 'pre' in request.POST:
                        precio = PrecioConsulta.objects.get(id = request.POST['pre'])
                        precio.tipovisita = f.cleaned_data['tipovisita']
                        precio.tipopersona = f.cleaned_data['tipopersona']
                        precio.precio = f.cleaned_data['precio']
                        mensaje = 'Edicion'
                        actionflag =CHANGE

                    else:
                        precio = PrecioConsulta(tipovisita = f.cleaned_data['tipovisita'],
                                                tipopersona = f.cleaned_data['tipopersona'],
                                                precio =f.cleaned_data['precio'] )
                        mensaje = 'Ingreso'
                        actionflag =ADDITION

                    if f.cleaned_data['convenio']:
                        precio.convenio = f.cleaned_data['convenio']

                    precio.save()
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(precio).pk,
                        object_id       = precio.id,
                        object_repr     = force_str(precio),
                        action_flag     = actionflag,
                        change_message  = mensaje + ' Precio de Consulta (' + client_address + ')' )
                    return HttpResponseRedirect("/preciobox")
                return HttpResponseRedirect("/precio?action=add")

            return HttpResponseRedirect("/tipoconvenio")
        else:
            data = {'title': 'Precios'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']
                if action == 'add':
                    data['title']= 'Ingresar Registro'

                    form = PrecioBoxForm()
                    data['form']= form
                    return render(request ,"visitabox/addprecio.html" ,  data)
                elif action == 'edit':
                    data['title']= 'Editar Registro'
                    data['pre']= PrecioConsulta.objects.get(id=request.GET['id'])
                    initial = model_to_dict(data['pre'])
                    form = PrecioBoxForm(initial=initial)
                    data['form']= form
                    return render(request ,"visitabox/addprecio.html" ,  data)

                elif action == 'eliminar':
                    precio= PrecioConsulta.objects.get(id=request.GET['id'])
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(precio).pk,
                        object_id       = precio.id,
                        object_repr     = force_str(precio),
                        action_flag     = DELETION,
                        change_message  = 'Precio Eliminado (' + client_address + ')' )
                    precio.delete()

                    return HttpResponseRedirect("/preciobox")

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

                    precio = PrecioConsulta.objects.filter(tipovisita__descripcion__icontains=search)
                else:
                    precio = PrecioConsulta.objects.all()

                paging = MiPaginador(precio, 30)
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
                data['precio'] = page.object_list
                return render(request ,"visitabox/preciobox.html" ,  data)
    except:
        return HttpResponseRedirect("/")