from datetime import datetime
import json
from django.contrib.admin.models import LogEntry, CHANGE, ADDITION, DELETION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
from sga.commonviews import addUserData, ip_client_address
from sga.forms import VendedorForm
from sga.models import Vendedor, InscripcionVendedor


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
@transaction.atomic()

def view(request):
    if request.method=='POST':
        action = request.POST['action']
        if action == 'add_vendedor':
            try:
                if 'activo' in request.POST:
                    activo=request.POST['activo']
                else:
                    activo=False

                if request.POST['idvendedor']=='':
                    idvendedor=0
                else:
                    idvendedor=request.POST['idvendedor']
                if Vendedor.objects.filter(pk=idvendedor).exists():
                    edit = Vendedor.objects.get(pk=idvendedor)
                    edit.nombres=request.POST['nombres']
                    edit.identificacion=request.POST['identificacion']
                    edit.extra=request.POST['extra']
                    edit.activo= activo
                    mensaje = 'Edicion de vendedor'
                    edit.save()
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(edit).pk,
                    object_id       = edit.id,
                    object_repr     = force_str(edit),
                    action_flag     = CHANGE,
                    change_message  = mensaje+' (' + client_address + ')' )
                else:
                    if Vendedor.objects.filter(identificacion=request.POST['identificacion']).exists():
                        return HttpResponseRedirect('/vendedor?error=Vendedor ya existe')
                    else:
                        add = Vendedor(nombres=request.POST['nombres'],
                                       identificacion=request.POST['identificacion'],
                                       extra=request.POST['extra'],
                                       activo=activo)
                        mensaje = 'Nuevo vendedor'
                        add.save()
                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(add).pk,
                        object_id       = add.id,
                        object_repr     = force_str(add),
                        action_flag     = ADDITION,
                        change_message  = mensaje+' (' + client_address + ')' )
                return HttpResponseRedirect('/vendedor')
            except Exception as ex:
                return HttpResponseRedirect('/vendedor?error=Ocurrio un error, vuelva a intentarlo')

        elif action == 'eliminar_vendedor':
            result = {}
            try:
                if InscripcionVendedor.objects.filter(vendedor__id=request.POST['idvendedor']).exists():
                    result['result']  = "No se puede eliminar vendedor"
                else:
                    eliminar =Vendedor.objects.filter(pk=request.POST['idvendedor'])[:1].get()
                    mensaje = 'Eliminar vendedor'
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(eliminar).pk,
                        object_id       = eliminar.id,
                        object_repr     = force_str(eliminar),
                        action_flag     = DELETION,
                        change_message  = mensaje+' (' + client_address + ')' )
                    eliminar.delete()
                    result['result']  = "ok"
                return HttpResponse(json.dumps(result), content_type="application/json")
            except Exception as e:
                result['result']  = str(e)
                return HttpResponse(json.dumps(result), content_type="application/json")
    else:
        data = {'title': 'Listado de vendedores'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']

        else:
            try:
                search = None
                if 's' in request.GET:
                    search = request.GET['s']
                if search:
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')
                    if len(ss)==1:
                        vendedor = Vendedor.objects.filter(Q(nombres__icontains=search)|Q(identificacion__icontains=search)).order_by('-activo','nombres')
                    else:
                        vendedor = Vendedor.objects.filter(Q(nombres__icontains=ss)|Q(identificacion__icontains=ss)).order_by('-activo','nombres')
                else:
                    vendedor = Vendedor.objects.filter().order_by('-activo','nombres')

                paging = Paginator(vendedor, 30)
                p = 1
                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                    page = paging.page(p)
                except:
                    page = paging.page(1)
                data['paging'] = paging
                data['page'] = page
                data['search'] = search if search else ""
                data['vendedores'] = page.object_list
                data['fechaactual']= datetime.now().date()
                data['form'] = VendedorForm
                if 'error' in request.GET:
                    data['error'] = request.GET['error']
                return render(request ,"vendedor/vendedor.html" ,  data)
            except Exception as e:
                return HttpResponseRedirect("/vendedor")
