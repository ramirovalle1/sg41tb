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
from sga.forms import PromocionForm, BancoForm
from sga.models import Vendedor, InscripcionVendedor, Promocion, Inscripcion, Banco, CuentaBanco, PagoCheque


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
        if action == 'add_banco':
            print(request.POST)
            try:
                if request.POST['idbanco']=='':
                    idbanco=0
                else:
                    idbanco=request.POST['idbanco']

                if Banco.objects.filter(pk=idbanco).exists():
                    edit = Banco.objects.get(pk=idbanco)
                    edit.nombre=request.POST['nombre']
                    edit.tasaprotesto=request.POST['tasaprotesto']
                    mensaje = 'Edicion de banco'
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
                    add = Banco(nombre=request.POST['nombre'], tasaprotesto=request.POST['tasaprotesto'])
                    mensaje = 'Nueva promocion'
                    add.save()
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(add).pk,
                    object_id       = add.id,
                    object_repr     = force_str(add),
                    action_flag     = ADDITION,
                    change_message  = mensaje+' (' + client_address + ')' )
                return HttpResponseRedirect('/bancos')
            except Exception as ex:
                return HttpResponseRedirect('/bancos?error=Ocurrio un error, vuelva a intentarlo')

        elif action == 'eliminar_banco':
            result = {}
            try:
                if CuentaBanco.objects.filter(banco__id=request.POST['idbanco']).exists() or PagoCheque.objects.filter(banco__id=request.POST['idbanco']).exists():
                    result['result']  = "Banco esta siendo utilizado por otros modelos"
                else:
                    eliminar =Banco.objects.filter(pk=request.POST['idbanco'])[:1].get()
                    mensaje = 'Eliminar banco'
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

        elif action == 'inactivaractivar':
            try:
                b = Banco.objects.get(pk=request.POST['id'])
                b.activo = not b.activo
                b.save()
                if b.activo:
                    mensaje = 'Activar banco'
                else:
                    mensaje = 'Inactivar banco'

                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                    user_id=request.user.pk,
                    content_type_id=ContentType.objects.get_for_model(b).pk,
                    object_id=b.id,
                    object_repr=force_str(b),
                    action_flag=CHANGE,
                    change_message=mensaje + ' (' + client_address + ')')
                return HttpResponse(json.dumps({"result": "ok"}), content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({"result": "bad"}), content_type="application/json")
    else:
        data = {'title': 'Listado de Bancos'}
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
                        bancos = Banco.objects.filter(nombre__icontains=search).order_by('nombre')
                    else:
                        bancos = Banco.objects.filter(nombre__icontains=ss).order_by('nombre')
                else:
                    bancos = Banco.objects.filter().order_by('nombre')

                paging = Paginator(bancos, 30)
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
                data['bancos'] = page.object_list
                data['form'] = BancoForm()
                if 'error' in request.GET:
                    data['error'] = request.GET['error']
                return render(request ,"bancos/bancos.html" ,  data)
            except Exception as e:
                return HttpResponseRedirect("/bancos")
