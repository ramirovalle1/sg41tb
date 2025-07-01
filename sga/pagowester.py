import json
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.forms import model_to_dict
from django.utils.encoding import force_str
from sga.models import Oficio, PagoWester,Inscripcion, RegistroWester
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.core.paginator import Paginator
from sga.commonviews import addUserData, ip_client_address
from django.template import RequestContext
from sga.forms import TipoMedicamentoForm, TipoOficioForm, OficioForm, PagoWesterForm
from datetime import datetime
from decorators import secure_module
from django.db.models import Q
from settings import EMAIL_ACTIVE

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
# @transaction.atomic()
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action == 'guardar':
                try:
                    f = PagoWesterForm(request.POST,request.FILES)
                    if f.is_valid():
                        if not PagoWester.objects.filter(codigo=(f.cleaned_data['codigo']).strip()).exists():
                            if not RegistroWester.objects.filter(codigo=(f.cleaned_data['codigo']).strip()).exists():
                                inscripcion = Inscripcion.objects.get(pk=int(request.POST['inscripcion']))
                                pagowester = PagoWester(inscripcion=inscripcion,
                                                        datos=f.cleaned_data['datos'],
                                                        codigo=(f.cleaned_data['codigo']).strip(),
                                                        fecha=datetime.now())
                                pagowester.save()
                                if pagowester.datos:
                                    pagowester.nombre = f.cleaned_data['nombre']
                                    pagowester.identificacion = f.cleaned_data['identificacion']
                                    pagowester.direccion = f.cleaned_data['direccion']
                                    pagowester.telefono = f.cleaned_data['telefono']
                                    pagowester.email = f.cleaned_data['email']
                                    pagowester.save()
                                if 'archivo' in request.FILES:
                                     pagowester.archivo = request.FILES['archivo']
                                     pagowester.save()

                                if EMAIL_ACTIVE:
                                    pagowester.mail_pago(request.user)
                                client_address = ip_client_address(request)
                                LogEntry.objects.log_action(
                                    user_id         = request.user.pk,
                                    content_type_id = ContentType.objects.get_for_model(pagowester).pk,
                                    object_id       = pagowester.id,
                                    object_repr     = force_str(pagowester),
                                    action_flag     = ADDITION,
                                    change_message  = 'Adicionado Registro de Pago (' + client_address + ')' )
                                return HttpResponseRedirect("/pagowester")
                            else:
                                return HttpResponseRedirect('/pagowester?error=el codigo ya fue registrado por W.U.')
                        else:
                            return HttpResponseRedirect('/pagowester?error=el codigo ya se encuentra registrado')


                except Exception as e:
                    pass
                    return HttpResponseRedirect("/pagowester?action=add")
            elif action == 'edit':
                f= PagoWesterForm(request.POST,request.FILES)
                pagowester = PagoWester.objects.get(pk=request.POST['id'])
                pagowester.codigo = f.data['codigo']
                pagowester.fecha = datetime.now()
                pagowester.save()
                if 'archivo' in request.FILES:
                    pagowester.archivo =  request.FILES['archivo']
                if 'datos' in f.data:
                    pagowester.nombre = f.data['nombre']
                    pagowester.identificacion = f.data['identificacion']
                    pagowester.direccion = f.data['direccion']
                    pagowester.telefono = f.data['telefono']
                    pagowester.email = f.data['email']
                    pagowester.datos = True

                else:
                    pagowester.datos=False
                    pagowester.nombre =""
                    pagowester.identificacion =""
                    pagowester.direccion = ""
                    pagowester.telefono = ""
                    pagowester.email =""
                pagowester.save()
                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(pagowester).pk,
                    object_id       = pagowester.id,
                    object_repr     = force_str(pagowester),
                    action_flag     = CHANGE,
                    change_message  = 'Editado  Registro de Pago (' + client_address + ')' )
                return HttpResponseRedirect("/pagowester")
            return HttpResponseRedirect("/pagowester?action=edit")

        else:
            data = {'title': 'Registro de Pagos'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']
                if action == 'add':
                    data['title']= 'Ingresar Registro de Pago'
                    form = PagoWesterForm()
                    data['form']= form
                    data['inscripcion'] = Inscripcion.objects.get(persona=data['persona'])
                    return render(request ,"pagowester/addregistro.html" ,  data)
                elif action == 'edit':
                    data['title']= 'Editar Registro de Pago'
                    rpago= PagoWester.objects.get(id=request.GET['id'])
                    initial = model_to_dict(rpago)
                    data['rpago'] = rpago
                    data['form'] = PagoWesterForm(initial=initial)
                    return render(request ,"pagowester/editregistro.html" ,  data)

            else:
                search = None
                todos = None
                inscripcion= Inscripcion.objects.get(persona=data['persona'])

                if 's' in request.GET:
                    search = request.GET['s']
                if 't' in request.GET:
                    todos = request.GET['t']
                if search:
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')

                    rpago = PagoWester.objects.filter(codigo__icontains=search,inscripcion=inscripcion).order_by('-fecha')
                else:
                    rpago = PagoWester.objects.filter(inscripcion=inscripcion).order_by('-fecha')

                paging = MiPaginador(rpago, 30)
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
                data['rpago'] = page.object_list
                if 'error' in request.GET:
                    data['error'] = request.GET['error']

                return render(request ,"pagowester/registropago.html" ,  data)
    except Exception as e:
        return HttpResponseRedirect("/pagowester")
