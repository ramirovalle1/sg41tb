import json
from django.contrib.admin.models import LogEntry, CHANGE, ADDITION, DELETION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db import transaction
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
from sga.commonviews import addUserData, ip_client_address
from sga.forms import EmpresaConvenioForm
from sga.models import EmpresaConvenio, Inscripcion


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
        if action == 'add_convenio':
            try:
                if 'estado' in request.POST:
                    estado=request.POST['estado']
                else:
                    estado=False
                if 'esempresa' in request.POST:
                    esempresa = True
                else:
                    esempresa = False
                if request.POST['idconvenio']=='':
                    idconvenio=0
                else:
                    idconvenio=request.POST['idconvenio']
                if EmpresaConvenio.objects.filter(pk=idconvenio).exists():
                    edit = EmpresaConvenio.objects.get(pk=idconvenio)
                    edit.nombre=request.POST['nombre']
                    edit.ruc = request.POST['ruc']
                    edit.activideconomica = request.POST['activideconomica']
                    edit.direccion = request.POST['direccion']
                    edit.ciudad_id = request.POST['ciudad']
                    edit.esempresa = esempresa
                    edit.estado= estado
                    mensaje = 'Edicion de convenio'
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
                    add = EmpresaConvenio(
                        nombre=request.POST['nombre'],
                        ruc = request.POST['ruc'],
                        activideconomica = request.POST['activideconomica'],
                        direccion = request.POST['direccion'],
                        ciudad_id = request.POST['ciudad'],
                        estado=estado,
                        esempresa=esempresa)
                    mensaje = 'Nuevo convenio'
                    add.save()
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(add).pk,
                    object_id       = add.id,
                    object_repr     = force_str(add),
                    action_flag     = ADDITION,
                    change_message  = mensaje+' (' + client_address + ')' )
                return HttpResponseRedirect('/empresaconvenio')
            except Exception as ex:
                print(ex)
                return HttpResponseRedirect('/empresaconvenio?error=Ocurrio un error, vuelva a intentarlo')

        elif action == 'eliminar_convenio':
            result = {}
            try:
                if Inscripcion.objects.filter(empresaconvenio__id=request.POST['idconvenio']).exists():
                    result['result']  = "Convenio esta siendo usado por una inscripcion"
                else:
                    eliminar =EmpresaConvenio.objects.filter(pk=request.POST['idconvenio'])[:1].get()
                    mensaje = 'Eliminar convenio'
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
        data = {'title': 'Listado de Convenios por Empresas'}
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
                        convenio = EmpresaConvenio.objects.filter(nombre__icontains=search).order_by('-estado','nombre')
                    else:
                        convenio = EmpresaConvenio.objects.filter(nombre__icontains=ss).order_by('-estado','nombre')
                else:
                    convenio = EmpresaConvenio.objects.filter().order_by('-estado','nombre')

                paging = Paginator(convenio, 30)
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
                data['convenio'] = page.object_list
                data['form'] = EmpresaConvenioForm()
                if 'error' in request.GET:
                    data['error'] = request.GET['error']
                return render(request ,"empresaconvenio/empresaconveniobs.html" ,  data)
            except Exception as e:
                return HttpResponseRedirect("/empresaconvenio")
