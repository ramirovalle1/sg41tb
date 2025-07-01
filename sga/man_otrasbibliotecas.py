from django.contrib.admin.models import LogEntry, CHANGE, ADDITION, DELETION
from django.contrib.contenttypes.models import ContentType
import json
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
from bib.models import  ConsultaBiblioteca, OtraBibliotecaVirtual
from sga.commonviews import addUserData, ip_client_address
from django.core.paginator import Paginator
from sga.forms import OtraBibliotecaVirtualForm


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
        if action == 'addotrabiblio':
            try:
                print(request.FILES)
                if 'estado' in request.POST:
                    estado=True
                else:
                    estado=False

                if request.POST['idotrabiblioteca']=='':
                    idotrabiblioteca=0
                else:
                    idotrabiblioteca=request.POST['idotrabiblioteca']
                 #EDITAR OTRA BIBLIOTECA
                if OtraBibliotecaVirtual.objects.filter(pk=idotrabiblioteca).exists():
                    edit = OtraBibliotecaVirtual.objects.get(pk=idotrabiblioteca)
                    edit.prioridad = request.POST['prioridad']
                    edit.url=request.POST['url']
                    edit.nombre=request.POST['nombre']
                    edit.descripcion = request.POST['descripcion']

                    if 'logo' in request.FILES:
                        edit.logo=request.FILES['logo']
                    edit.estado= estado
                    edit.save()

                    mensaje = 'Edicion de Otra Biblioteca'
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(edit).pk,
                    object_id       = edit.id,
                    object_repr     = force_str(edit),
                    action_flag     = CHANGE,
                    change_message  = mensaje+' (' + client_address + ')' )
                else:
                    if OtraBibliotecaVirtual.objects.filter(id=idotrabiblioteca).exists():
                        return HttpResponseRedirect('/man_otrasbibliotecas?error=Biblioteca Virtual ya existe')
                    else:
                        add = OtraBibliotecaVirtual(prioridad= request.POST['prioridad'],
                                            url=request.POST['url'],
                                            nombre=request.POST['nombre'],
                                            descripcion = request.POST['descripcion'],
                                            estado=estado)
                        add.save()

                        if 'logo' in request.FILES:
                            add.logo=request.FILES['logo']
                        add.save()

                        mensaje = 'Nueva Biblioteca Virtual'
                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(add).pk,
                        object_id       = add.id,
                        object_repr     = force_str(add),
                        action_flag     = ADDITION,
                        change_message  = mensaje+' (' + client_address + ')' )
                return HttpResponseRedirect('/man_otrasbibliotecas')
            except Exception as ex:
                return HttpResponseRedirect('/man_otrasbibliotecas?error=Ocurrio un error, vuelva a intentarlo')

        elif action == 'elim_otrabiblioteca':
            result = {}
            try:
                if ConsultaBiblioteca.objects.filter(otrabibliotecaconsultadas=request.POST['idotrabiblioteca']).exists():
                    result['result']  = "No se puede eliminar biblioteca"
                else:
                    eliminar =OtraBibliotecaVirtual.objects.filter(pk=request.POST['idotrabiblioteca'])[:1].get()
                    mensaje = 'Eliminado Biblioteca Virtual'
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

        data = {'title': 'Listado de Otras Bibliotecas Virtuales'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action == "desactivar":
                    otrasbiblio = OtraBibliotecaVirtual.objects.get(id=request.GET["id"])
                    if otrasbiblio.estado:
                        mensaje= 'Desactiva Otra Biblioteca Virtual'
                    else:
                        mensaje= 'Activa Otra Biblioteca Virtual'
                    otrasbiblio.estado = not otrasbiblio.estado
                    otrasbiblio.save()

                    #Obtain client ip address
                    client_address = ip_client_address(request)
                    # Log de ESTADO DE OTRA BIBLIOTECA VIRTUAL
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(otrasbiblio).pk,
                        object_id       = otrasbiblio.id,
                        object_repr     = force_str(otrasbiblio),
                        action_flag     = CHANGE,
                        change_message  = mensaje+ ' (' + client_address + ')')
                    return HttpResponseRedirect("/man_otrasbibliotecas")
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
                        otrabiblioteca = OtraBibliotecaVirtual.objects.filter(Q(nombre=search)| Q(url=search)).order_by('prioridad')
                    else:
                        otrabiblioteca = OtraBibliotecaVirtual.objects.filter(Q(nombre__icontains=ss[0]) & Q(url__icontains=ss[1])).order_by('prioridad')

                else:
                    otrabiblioteca = OtraBibliotecaVirtual.objects.filter().order_by('prioridad')

                paging = MiPaginador(otrabiblioteca, 30)
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
                data['otrabiblioteca'] = page.object_list
                data['otrabibliotecas'] = OtraBibliotecaVirtualForm
                if 'error' in request.GET:
                    data['error']= request.GET['error']
                return render(request,"biblioteca/man_otrasbibliotecas.html", data)
            except Exception as e:
                return HttpResponseRedirect("/man_otrasbibliotecas")
