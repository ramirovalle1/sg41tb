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
from sga.forms import PromocionForm
from sga.models import Vendedor, InscripcionVendedor, Promocion, Inscripcion


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
        if action == 'add_promocion':
            print(request.POST)
            try:
                if 'directo' in request.POST:
                    directo=request.POST['directo']
                else:
                    directo=False
                activo=False
                if 'activo' in request.POST:
                    if request.POST['activo'] =='on':
                        activo=True
                else:
                    activo=False
                todos_niveles=False
                if 'todos_niveles' in request.POST:
                    if request.POST['todos_niveles'] == 'on':
                        todos_niveles=True
                else:
                    todos_niveles=False
                descuentomaterial=False
                if 'descuentomaterial' in request.POST:
                    if request.POST['descuentomaterial'] =='on':
                        descuentomaterial=True
                else:
                    descuentomaterial=False

                if request.POST['val_inscripcion']=='':
                    val_inscripcion=0
                else:
                    val_inscripcion=request.POST['val_inscripcion']
                if request.POST['valdescuentomaterial']=='':
                    valdescuentomaterial=0
                else:
                    valdescuentomaterial=request.POST['valdescuentomaterial']

                if request.POST['idpromocion']=='':
                    idpromocion=0
                else:
                    idpromocion=request.POST['idpromocion']

                if request.POST['valormaterialapoyo'] == '':
                    valormaterialapoyo = 0
                else:
                    valormaterialapoyo = request.POST['valormaterialapoyo']

                if Promocion.objects.filter(pk=idpromocion).exists():
                    edit = Promocion.objects.get(pk=idpromocion)
                    edit.descripcion=request.POST['descripcion']
                    edit.directo= directo
                    edit.activo= activo
                    edit.todos_niveles= todos_niveles
                    edit.val_inscripcion= val_inscripcion
                    edit.descuentomaterial= descuentomaterial
                    edit.valormaterialapoyo= valormaterialapoyo
                    edit.valdescuentomaterial= valdescuentomaterial
                    mensaje = 'Edicion de promocion'
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
                    add = Promocion(descripcion=request.POST['descripcion'],
                                   directo=directo,
                                   activo=activo,
                                   todos_niveles=todos_niveles,
                                   descuentomaterial=descuentomaterial,
                                   valdescuentomaterial=valdescuentomaterial,
                                   val_inscripcion=val_inscripcion,
                                    valormaterialapoyo=valormaterialapoyo)
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
                return HttpResponseRedirect('/promociones')
            except Exception as ex:
                return HttpResponseRedirect('/promociones?error=Ocurrio un error, vuelva a intentarlo')

        elif action == 'eliminar_promocion':
            result = {}
            try:
                if Inscripcion.objects.filter(promocion__id=request.POST['idpromocion']).exists():
                    result['result']  = "Promocion esta siendo usada por una inscripcion"
                else:
                    eliminar =Promocion.objects.filter(pk=request.POST['idpromocion'])[:1].get()
                    mensaje = 'Eliminar promocion'
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
        data = {'title': 'Listado de promociones'}
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
                        promocion = Promocion.objects.filter(descripcion__icontains=search).order_by('-activo')
                    else:
                        promocion = Promocion.objects.filter(descripcion__icontains=ss).order_by('-activo')
                else:
                    promocion = Promocion.objects.filter().order_by('-activo')

                paging = Paginator(promocion, 30)
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
                data['promociones'] = page.object_list
                data['form'] = PromocionForm()
                if 'error' in request.GET:
                    data['error'] = request.GET['error']
                return render(request ,"promociones/promocionesbs.html" ,  data)
            except Exception as e:
                return HttpResponseRedirect("/promociones")
