import json
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import Sum, Q
from django.forms import model_to_dict
from django.utils.encoding import force_str
from decorators import secure_module
from settings import EMAIL_ACTIVE
from sga.models import UsuarioConvenio, TipoMedicamento, DetalleRegistroMedicamento, BajaMedicamento, RecetaVisitaBox, Sede, Persona, TrasladoMedicamento,DetalleVisitasBox,PersonalConvenio, ConvenioBox, ConvenioAcademico, ConvenioUsuario
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.core.paginator import Paginator
from sga.commonviews import addUserData, ip_client_address
from django.template import RequestContext
from sga.forms import RegistroMedicamentoForm, PersonalConvenioForm, ConvenioAcadForm, ConvenioUsuarioForm
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
@secure_module
@transaction.atomic()
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action == 'add':
                f=ConvenioAcadForm(request.POST)
                if f.is_valid():
                    if 'convenio' in request.POST:
                        convenio = ConvenioAcademico.objects.get(id = request.POST['convenio'])
                        convenio.descripcion = f.cleaned_data['descripcion']
                        mensaje = 'Edicion'
                        actionflag =CHANGE

                    else:
                        convenio = ConvenioAcademico(
                                    descripcion = f.cleaned_data['descripcion'])
                        mensaje = 'Ingreso'
                        actionflag =ADDITION

                    convenio.save()
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(convenio).pk,
                        object_id       = convenio.id,
                        object_repr     = force_str(convenio),
                        action_flag     = actionflag,
                        change_message  = mensaje + ' Personal (' + client_address + ')' )
                    return HttpResponseRedirect("/convenio_academico")
                return HttpResponseRedirect("/convenio_academico?action=addpersona")
            elif action == 'addcu':
                f=ConvenioUsuarioForm(request.POST)
                if f.is_valid():
                    if 'cu' in request.POST:
                        cu = ConvenioUsuario.objects.get(id = request.POST['cu'])
                        cu.usuario_id = f.cleaned_data['usuario_id']
                        cu.convenio = f.cleaned_data['convenio']
                        mensaje = 'Edicion'
                        actionflag =CHANGE

                    else:
                        cu = ConvenioUsuario(
                                    usuario_id = f.cleaned_data['usuario_id'],
                                    convenio = f.cleaned_data['convenio'])
                        mensaje = 'Ingreso'
                        actionflag =ADDITION

                    cu.save()
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(cu).pk,
                        object_id       = cu.id,
                        object_repr     = force_str(cu),
                        action_flag     = actionflag,
                        change_message  = mensaje + ' Usuario Convenio (' + client_address + ')' )
                    return HttpResponseRedirect("/convenio_academico?action=personausuario")
                return HttpResponseRedirect("/convenio_academico")


        else:
            data = {'title': 'Convenios Academicos'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']
                if action == 'add':
                    data['title']= 'Convenios Academicos'
                    form = ConvenioAcadForm()
                    data['form']= form
                    return render(request ,"convenio_academico/adicionar.html" ,  data)
                elif action == 'cambiaestado':
                    c = ConvenioAcademico.objects.get(pk=request.GET['id'])
                    if c.activo :
                        c.activo = False
                    else:
                       c.activo=True

                    c.save()
                    client_address = ip_client_address(request)

                        # Log de Cambio de Estado
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(c).pk,
                        object_id       = c.id,
                        object_repr     = force_str(c),
                        action_flag     = CHANGE,
                        change_message  = 'Cambio de Estado de Convenio a ' + str(c.activo) + ' (   ' +client_address + ')' )
                    return HttpResponseRedirect("/convenio_academico")
                elif action == 'editar':
                    data['title']= 'Editar Convenio Academico'
                    if 'error' in request.GET:
                        data['error']=request.GET['error']
                    data['convenio']= ConvenioAcademico.objects.get(id=request.GET['id'])
                    initial = model_to_dict(data['convenio'])
                    form = ConvenioAcadForm(initial=initial)
                    data['form']= form
                    return render(request ,"convenio_academico/adicionar.html" ,  data)
                elif action == 'eliminar':
                    convenio = ConvenioAcademico.objects.get(id=request.GET['id'])
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(convenio).pk,
                        object_id       = convenio.id,
                        object_repr     = force_str(convenio),
                        action_flag     = ADDITION,
                        change_message  = 'Eliminado Convenio Academico (' + client_address + ')' )
                    convenio.delete()
                    return  HttpResponseRedirect("/convenio_academico")
                elif action =='personausuario':
                    if 'add' in request.GET:
                        data['title']= 'Usuario Convenio'
                        form = ConvenioUsuarioForm()
                        data['form']= form
                        return render(request ,"convenio_academico/adicionar_usuario.html" ,  data)
                    if 'edit' in request.GET:
                        data['title']= 'Editar Usuario Convenio'
                        if 'error' in request.GET:
                            data['error']=request.GET['error']
                        data['cu']= ConvenioUsuario.objects.get(id=request.GET['cu'])
                        initial = model_to_dict(data['cu'])
                        form = ConvenioUsuarioForm(initial=initial)
                        data['form']= form
                        return render(request ,"convenio_academico/adicionar_usuario.html" ,  data)
                    if 'eliminar' in request.GET:
                        cu = ConvenioUsuario.objects.get(id=request.GET['id'])
                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(cu).pk,
                            object_id       = cu.id,
                            object_repr     = force_str(cu),
                            action_flag     = ADDITION,
                            change_message  = 'Eliminado Usuario Convenio Academico (' + client_address + ')' )
                        cu.delete()
                        return HttpResponseRedirect("/convenio_academico?action=personausuario")
                    else:
                        search = None
                        todos = None
                        if 's' in request.GET:
                            search = request.GET['s']
                        if 't' in request.GET:
                            todos = request.GET['t']
                        if search:
                            convenios = ConvenioUsuario.objects.filter(Q(usuario__username__icontains=search)|Q(convenio__descripcion__icontains=search))
                        else:
                            convenios = ConvenioUsuario.objects.all()

                        paging = MiPaginador(convenios, 30)
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
                        data['convenios'] = page.object_list
                        return render(request ,"convenio_academico/convenios_usuario.html" ,  data)
            else:
                search = None
                todos = None
                if 's' in request.GET:
                    search = request.GET['s']
                if 't' in request.GET:
                    todos = request.GET['t']
                if search:

                    convenios = ConvenioAcademico.objects.filter(descripcion__icontains=search)

                else:
                    convenios = ConvenioAcademico.objects.all()

                paging = MiPaginador(convenios, 30)
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
                data['convenios'] = page.object_list
                return render(request ,"convenio_academico/convenios.html" ,  data)
    except Exception as ex:
        return HttpResponseRedirect("/")