from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.forms import model_to_dict
from django.utils.encoding import force_str
from decorators import secure_module
from sga.models import TipoMedicamento,TipoOficio,Oficio
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.core.paginator import Paginator
from sga.commonviews import addUserData, ip_client_address
from django.template import RequestContext
from sga.forms import TipoMedicamentoForm, TipoOficioForm, OficioForm
from datetime import datetime
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
            if action == 'add':
                f= OficioForm(request.POST,request.FILES)
                if f.is_valid():
                    oficio = Oficio(tipo = f.cleaned_data['tipo'],
                                        numero = f.cleaned_data['numero'],
                                        asunto = f.cleaned_data['asunto'],
                                        remitente = f.cleaned_data['remitente'],
                                        archivo = request.FILES['archivo'],
                                        fecharecepcion = f.cleaned_data['fecharecepcion'],
                                        fecha=datetime.now().date(),
                                        emitido = f.cleaned_data['emitido'])
                    oficio.save()
                    if EMAIL_ACTIVE:
                        oficio.mail_oficio(request.user)
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(oficio).pk,
                        object_id       = oficio.id,
                        object_repr     = force_str(oficio),
                        action_flag     = ADDITION,
                        change_message  = 'Adicionado Oficio (' + client_address + ')' )

                    return HttpResponseRedirect("/oficio")
                return HttpResponseRedirect("/tipooficio?action=add")
            elif action == 'edit':
                f= OficioForm(request.POST,request.FILES)
                if f.is_valid():
                    oficio = Oficio.objects.get(pk=request.POST['id'])
                    oficio.tipo = f.cleaned_data['tipo']
                    oficio.numero = f.cleaned_data['numero']
                    oficio.asunto = f.cleaned_data['asunto']
                    oficio.remitente = f.cleaned_data['remitente']
                    oficio.fecharecepcion = f.cleaned_data['fecharecepcion']
                    oficio.fecha = datetime.now().date()
                    if 'archivo' in request.FILES:
                        oficio.archivo =  request.FILES['archivo']
                    oficio.emitido = f.cleaned_data['emitido']
                    oficio.save()
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(oficio).pk,
                        object_id       = oficio.id,
                        object_repr     = force_str(oficio),
                        action_flag     = ADDITION,
                        change_message  = 'Editado  Oficio (' + client_address + ')' )
                    return HttpResponseRedirect("/oficio")
                return HttpResponseRedirect("/oficio?action=edit")

        else:
            data = {'title': 'Oficio'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']
                if action == 'add':
                    data['title']= 'Ingresar Oficio'

                    form = OficioForm()
                    data['form']= form
                    return render(request ,"oficios/addoficio.html" ,  data)
                elif action == 'edit':
                    data['title']= 'Editar Oficio'
                    oficio= Oficio.objects.get(id=request.GET['id'])

                    initial = model_to_dict(oficio)
                    data['oficio'] = oficio
                    data['form'] = OficioForm(initial=initial)
                    return render(request ,"oficios/editoficio.html" ,  data)

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

                    oficio = Oficio.objects.filter(Q(numero__icontains=search) | Q(asunto__icontains=search) | Q(tipo__nombre__icontains=search) | Q(remitente__icontains=search) | Q(fecharecepcion__icontains=search)).order_by('-fecha')
                else:
                    oficio = Oficio.objects.all().order_by('-fecha','-fecharecepcion')

                paging = MiPaginador(oficio, 30)
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
                data['oficio'] = page.object_list
                return render(request ,"oficios/oficios.html" ,  data)
    except:
        return HttpResponseRedirect("/")
