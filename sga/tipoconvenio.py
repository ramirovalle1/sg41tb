import json
from django.contrib.admin.models import ADDITION, LogEntry, CHANGE, DELETION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_str
from sga.models import ConvenioBox
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.core.paginator import Paginator
from sga.commonviews import addUserData, ip_client_address
from django.template import RequestContext
from sga.forms import SuministroBoxForm, ConvenioBoxForm
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
                f= ConvenioBoxForm(request.POST)
                if f.is_valid():
                    if 'tipo' in request.POST:
                        tipoconvenio = ConvenioBox.objects.get(id = request.POST['tipo'])
                        tipoconvenio.descripcion = f.cleaned_data['descripcion']
                        tipoconvenio.activo = f.cleaned_data['activo']
                        mensaje = 'Edicion'
                        actionflag =CHANGE

                    else:
                        tipoconvenio = ConvenioBox(
                                            descripcion = f.cleaned_data['descripcion'],
                                            activo = f.cleaned_data['activo'])
                        mensaje = 'Ingreso'
                        actionflag =ADDITION

                    tipoconvenio.save()
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(tipoconvenio).pk,
                        object_id       = tipoconvenio.id,
                        object_repr     = force_str(tipoconvenio),
                        action_flag     = actionflag,
                        change_message  = mensaje + ' de Convenio (' + client_address + ')' )
                    return HttpResponseRedirect("/tipoconvenio")
                return HttpResponseRedirect("/tipoconvenio?action=add")

            return HttpResponseRedirect("/tipoconvenio")
        else:
            data = {'title': 'Convenios'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']
                if action == 'add':
                    data['title']= 'Ingresar Registro'

                    form = ConvenioBoxForm()
                    data['form']= form
                    return render(request ,"visitabox/addtipoconvenio.html" ,  data)
                elif action == 'edit':
                    data['title']= 'Editar Registro'
                    data['tipo']= ConvenioBox.objects.get(id=request.GET['id'])

                    form = ConvenioBoxForm(instance=data['tipo'])
                    data['form']= form
                    return render(request ,"visitabox/addtipoconvenio.html" ,  data)

                elif action == 'eliminar':
                    tipoconvenio= ConvenioBox.objects.get(id=request.GET['id'])
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(tipoconvenio).pk,
                        object_id       = tipoconvenio.id,
                        object_repr     = force_str(tipoconvenio),
                        action_flag     = DELETION,
                        change_message  = 'Convenio Eliminado (' + client_address + ')' )
                    tipoconvenio.delete()

                    return HttpResponseRedirect("/tipoconvenio")

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

                    tipoconvenio = ConvenioBox.objects.filter(descripcion__icontains=search).order_by('descripcion')
                else:
                    tipoconvenio = ConvenioBox.objects.all().order_by('descripcion')

                paging = MiPaginador(tipoconvenio, 30)
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
                data['tipoconvenio'] = page.object_list
                return render(request ,"visitabox/tipoconvenio.html" ,  data)
    except Exception as e:
        return HttpResponseRedirect("/tipoconvenio")