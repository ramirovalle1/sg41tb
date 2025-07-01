from django.contrib.admin.models import LogEntry, CHANGE, ADDITION, DELETION
from django.contrib.contenttypes.models import ContentType
import json
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
from bib.models import  ConsultaBiblioteca, ReferenciaWeb
from sga.commonviews import addUserData, ip_client_address
from django.core.paginator import Paginator
from sga.forms import ReferenciaWebForm


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


def view(request):
    if request.method=='POST':
        action = request.POST['action']
        if action == 'addreferencia':
            try:
                print(request.FILES)
                if 'estado' in request.POST:
                    estado=True
                else:
                    estado=False

                if request.POST['idreferencia']=='':
                    idreferencia=0
                else:
                    idreferencia=request.POST['idreferencia']
                 #EDITAR REFERENCIA WEB
                if ReferenciaWeb.objects.filter(pk=idreferencia).exists():
                    edit = ReferenciaWeb.objects.get(pk=idreferencia)
                    edit.prioridad = request.POST['prioridad']
                    edit.url=request.POST['url']
                    edit.nombre=request.POST['nombre']

                    if 'logo' in request.FILES:
                        edit.logo=request.FILES['logo']
                    edit.estado= estado
                    edit.save()

                    mensaje = 'Edicion de Referencia Web'
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(edit).pk,
                    object_id       = edit.id,
                    object_repr     = force_str(edit),
                    action_flag     = CHANGE,
                    change_message  = mensaje+' (' + client_address + ')' )
                else:
                    if ReferenciaWeb.objects.filter(id=idreferencia).exists():
                        return HttpResponseRedirect('/man_referenciasweb?error=Referencia Web ya existe')
                    else:
                        add = ReferenciaWeb(prioridad= request.POST['prioridad'],
                                            url=request.POST['url'],
                                            nombre=request.POST['nombre'],
                                            estado=estado)
                        add.save()

                        if 'logo' in request.FILES:
                            add.logo=request.FILES['logo']
                        add.save()

                        mensaje = 'Nueva Referencia Web'
                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(add).pk,
                        object_id       = add.id,
                        object_repr     = force_str(add),
                        action_flag     = ADDITION,
                        change_message  = mensaje+' (' + client_address + ')' )
                return HttpResponseRedirect('/man_referenciasweb')
            except Exception as ex:
                return HttpResponseRedirect('/man_referenciasweb?error=Ocurrio un error, vuelva a intentarlo')

        elif action == 'elim_referencia':
            result = {}
            try:
                if ConsultaBiblioteca.objects.filter(referenciasconsultadas__id=request.POST['idreferencia']).exists():
                    result['result']  = "No se puede eliminar referencia web"
                else:
                    eliminar =ReferenciaWeb.objects.filter(pk=request.POST['idreferencia'])[:1].get()
                    mensaje = 'Eliminar Referencia Web'
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
                return HttpResponse(json.dumps(result),content_type="application/json")
            except Exception as e:
                result['result']  = str(e)
                return HttpResponse(json.dumps(result),content_type="application/json")

    else:

        data = {'title': 'Listado de Referencias Web'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action == "desactivar":
                referenciasweb = ReferenciaWeb.objects.get(id=request.GET["id"])
                if referenciasweb.estado:
                    mensaje= 'Desactiva Referencia Web'
                else:
                    mensaje= 'Activa Referencia Web'
                referenciasweb.estado = not referenciasweb.estado
                referenciasweb.save()

                #Obtain client ip address
                client_address = ip_client_address(request)
                # Log de ESTADO REFERENCIA WEB
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(referenciasweb).pk,
                    object_id       = referenciasweb.id,
                    object_repr     = force_str(referenciasweb),
                    action_flag     = CHANGE,
                    change_message  = mensaje+ ' (' + client_address + ')')

                return HttpResponseRedirect("/man_referenciasweb")
        else:
            try:
                search  = None
                if 's' in request.GET:
                    search = request.GET['s']

                if search:
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')
                    if len(ss)==1:
                        referencia = ReferenciaWeb.objects.filter(Q(nombre=search)| Q(url=search)).order_by('prioridad')
                    else:
                        referencia = ReferenciaWeb.objects.filter(Q(nombre__icontains=ss[0]) & Q(url__icontains=ss[1])).order_by('prioridad')

                else:
                    referencia = ReferenciaWeb.objects.filter().order_by('prioridad')

                paging = MiPaginador(referencia, 30)
                p = 1
                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                    page = paging.page(p)
                except:
                    page = paging.page(1)

                data['paging'] = paging
                data['rangospaging'] = paging.rangos_paginado(p)
                data['page'] = page
                data['search'] = search if search else ""
                data['referencia'] = page.object_list
                data['referencias'] = ReferenciaWebForm
                if 'error' in request.GET:
                    data['error']= request.GET['error']
                return render(request,"biblioteca/man_referenciasweb.html", data)
            except Exception as e:
                return HttpResponseRedirect("/man_referenciasweb")
