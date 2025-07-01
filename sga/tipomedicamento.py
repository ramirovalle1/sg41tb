from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_str
from sga.models import TipoMedicamento
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.core.paginator import Paginator
from sga.commonviews import addUserData, ip_client_address
from django.template import RequestContext
from sga.forms import TipoMedicamentoForm
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
                f= TipoMedicamentoForm(request.POST)
                if f.is_valid():
                    if 'tipomedi' in request.POST:
                        tipomedicamento = TipoMedicamento.objects.get(id = request.POST['tipomedi'])
                        tipomedicamento.descripcion = f.cleaned_data['descripcion']
                    else:
                        tipomedicamento = TipoMedicamento(
                                            descripcion = f.cleaned_data['descripcion'])
                    tipomedicamento.save()
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(tipomedicamento).pk,
                        object_id       = tipomedicamento.id,
                        object_repr     = force_str(tipomedicamento),
                        action_flag     = ADDITION,
                        change_message  = 'Ingreso o edicion de Tipo de Medicamento (' + client_address + ')' )
                    return HttpResponseRedirect("/tipomedicamento")
                return HttpResponseRedirect("/tipomedicamento?action=add")
            return HttpResponseRedirect("/tipomedicamento")
        else:
            data = {'title': 'Listado de Visitas Box'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']
                if action == 'add':
                    data['title']= 'Ingresar Tipo'

                    form = TipoMedicamentoForm({"fechavencimiento":datetime.today().date()})
                    data['form']= form
                    return render(request ,"registromedicamento/addtipomedicamento.html" ,  data)
                elif action == 'edit':
                    data['title']= 'Editar Registro'
                    data['tipomedi']= TipoMedicamento.objects.get(id=request.GET['id'])

                    form = TipoMedicamentoForm(instance=data['tipomedi'])
                    data['form']= form
                    return render(request ,"registromedicamento/addtipomedicamento.html" ,  data)

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

                    tipomedi = TipoMedicamento.objects.filter(descripcion__icontains=search).order_by('descripcion')
                else:
                    tipomedi = TipoMedicamento.objects.all().order_by('descripcion')

                paging = MiPaginador(tipomedi, 30)
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
                data['tipomedi'] = page.object_list
                data['grupos'] = TipoMedicamento.objects.all().order_by('descripcion')
                return render(request ,"registromedicamento/tipomedicamento.html" ,  data)
    except:
        return HttpResponseRedirect("/")
