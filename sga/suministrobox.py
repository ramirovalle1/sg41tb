import json
from django.contrib.admin.models import ADDITION, LogEntry
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_str
from sga.models import SuministroBox
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.core.paginator import Paginator
from sga.commonviews import addUserData, ip_client_address
from django.template import RequestContext
from sga.forms import SuministroBoxForm
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
                f= SuministroBoxForm(request.POST)
                if f.is_valid():
                    if 'suminis' in request.POST:
                        suministro = SuministroBox.objects.get(id = request.POST['suminis'])
                        suministro.descripcion = f.cleaned_data['descripcion']
                        suministro.estado = f.cleaned_data['estado']
                        suministro.baja = f.cleaned_data['baja']

                    else:
                        suministro = SuministroBox(
                                            descripcion = f.cleaned_data['descripcion'],
                                            estado = f.cleaned_data['estado'],
                                            baja = f.cleaned_data['baja'])
                    suministro.save()
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(suministro).pk,
                        object_id       = suministro.id,
                        object_repr     = force_str(suministro),
                        action_flag     = ADDITION,
                        change_message  = 'Ingreso o edicion de Sumnistro (' + client_address + ')' )
                    return HttpResponseRedirect("/suministrobox")
                return HttpResponseRedirect("/suministrobox?action=add")
            if action == 'activacion':
                try:
                    d = SuministroBox.objects.get(pk=request.POST['id'])
                    d.estado = not d.estado
                    d.save()

                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(d).pk,
                        object_id       = d.id,
                        object_repr     = force_str(d),
                        action_flag     = ADDITION,
                        change_message  = 'Activacion o desactivacion Sumnistro (' + client_address + ')' )
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")

                except:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

            if action == 'baja':
                try:
                    b = SuministroBox.objects.get(pk=request.POST['id'])
                    b.baja = not b.baja
                    b.save()

                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(b).pk,
                        object_id       = b.id,
                        object_repr     = force_str(b),
                        action_flag     = ADDITION,
                        change_message  = 'Baja o No baja Sumnistro (' + client_address + ')' )
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")

                except:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
            return HttpResponseRedirect("/suministrobox")
        else:
            data = {'title': 'Suministro'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']
                if action == 'add':
                    data['title']= 'Ingresar Registro'

                    form = SuministroBoxForm()
                    data['form']= form
                    return render(request ,"registromedicamento/addsumnistro.html" ,  data)
                elif action == 'edit':
                    data['title']= 'Editar Registro'
                    data['suminist']= SuministroBox.objects.get(id=request.GET['id'])

                    form = SuministroBoxForm(instance=data['suminist'])
                    data['form']= form
                    return render(request ,"registromedicamento/addsumnistro.html" ,  data)

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

                    suministro = SuministroBox.objects.filter(descripcion__icontains=search).order_by('descripcion')
                else:
                    suministro = SuministroBox.objects.all().order_by('descripcion')

                paging = MiPaginador(suministro, 30)
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
                data['suministro'] = page.object_list
                data['grupos'] = SuministroBox.objects.all().order_by('descripcion')
                return render(request ,"registromedicamento/suministrobox.html" ,  data)
    except:
        return HttpResponseRedirect("/")