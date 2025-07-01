import json
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import Sum
from django.forms import model_to_dict
from django.utils.encoding import force_str
from decorators import secure_module
from settings import EMAIL_ACTIVE
from sga.models import UsuarioConvenio, TipoMedicamento, DetalleRegistroMedicamento, BajaMedicamento, RecetaVisitaBox, Sede, Persona, TrasladoMedicamento,DetalleVisitasBox,PersonalConvenio, ConvenioBox
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.core.paginator import Paginator
from sga.commonviews import addUserData, ip_client_address
from django.template import RequestContext
from sga.forms import RegistroMedicamentoForm, PersonalConvenioForm
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
            if action == 'addpersona':
                f=PersonalConvenioForm(request.POST)
                if f.is_valid():
                    if 'personal' in request.POST:
                        personal = PersonalConvenio.objects.get(id = request.POST['personal'])
                        personal.nombres = f.cleaned_data['nombres']
                        personal.identificacion = f.cleaned_data['identificacion']
                        mensaje = 'Edicion'
                        actionflag =CHANGE

                    else:
                        personal = PersonalConvenio(
                                            conveniobox = f.cleaned_data['conveniobox'],
                                            nombres = f.cleaned_data['nombres'],
                                            identificacion = f.cleaned_data['identificacion'])
                        mensaje = 'Ingreso'
                        actionflag =ADDITION

                    personal.save()
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(personal).pk,
                        object_id       = personal.id,
                        object_repr     = force_str(personal),
                        action_flag     = actionflag,
                        change_message  = mensaje + ' Personal (' + client_address + ')' )
                    return HttpResponseRedirect("/conveniobox")
                return HttpResponseRedirect("/conveniobox?action=addpersona")
            if action =='editar':
                pass
            return HttpResponseRedirect("/registromedicamento")

        else:
            data = {'title': 'Convenios'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']
                if action == 'addpersona':
                    data['title']= 'Convenio'
                    if UsuarioConvenio.objects.filter(usuario=request.user).exists():
                        usuario =request.user
                    else:
                        usuario = None
                    form = PersonalConvenioForm()
                    if usuario:
                        form.for_convenio(usuario)
                    data['form']= form
                    return render(request ,"visitabox/addpersona.html" ,  data)
                elif action == 'editar':
                    data['title']= 'Editar Registro'
                    data['personal']= PersonalConvenio.objects.get(id=request.GET['id'])
                    initial = model_to_dict(data['personal'])

                    form = PersonalConvenioForm(initial=initial)
                    data['form']= form
                    return render(request ,"visitabox/addpersona.html" ,  data)
                elif action == 'edit':
                    # data['title']= 'Editar Medicamento'
                    # if 'error' in request.GET:
                    #     data['error']=request.GET['error']
                    # data['regismed']= RegistroMedicamento.objects.get(id=request.GET['id'])
                    # initial = model_to_dict(data['regismed'])
                    # form = RegistroMedicamentoForm(initial=initial)
                    # data['form']= form
                    return render(request ,"registromedicamento/editmedicamento.html" ,  data)
                elif action == 'eliminar':
                    personal = PersonalConvenio.objects.get(id=request.GET['id'])
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(personal).pk,
                        object_id       = personal.id,
                        object_repr     = force_str(personal),
                        action_flag     = ADDITION,
                        change_message  = 'Eliminado Personal (' + client_address + ')' )
                    personal.delete()
                    return  HttpResponseRedirect("/conveniobox")

            else:
                search = None
                todos = None
                bandera = 0
                if 's' in request.GET:
                    search = request.GET['s']
                if 't' in request.GET:
                    todos = request.GET['t']
                if search:
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')
                    if UsuarioConvenio.objects.filter(usuario=request.user).exists():
                        per =UsuarioConvenio.objects.filter(usuario=request.user)[:1].get()
                        personalconvenio = PersonalConvenio.objects.filter(nombres__icontains=search,conveniobox=per.convenio).order_by('nombres')
                    else:
                        personalconvenio = PersonalConvenio.objects.filter(nombres__icontains=search).order_by('nombres')


                else:
                     if UsuarioConvenio.objects.filter(usuario=request.user).exists():
                        per =UsuarioConvenio.objects.filter(usuario=request.user)[:1].get()
                        personalconvenio = PersonalConvenio.objects.filter(conveniobox=per.convenio).order_by('nombres')
                     else:
                        personalconvenio = PersonalConvenio.objects.all().order_by('nombres')
                paging = MiPaginador(personalconvenio, 30)
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
                data['personalconvenio'] = page.object_list
                return render(request ,"visitabox/convenios.html" ,  data)
    except Exception as ex:
        return HttpResponseRedirect("/")