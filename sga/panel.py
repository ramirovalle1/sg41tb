from datetime import datetime, timedelta
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
import json
from django.db.models import Q
from django.forms import model_to_dict
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
from decorators import secure_module
from sga.forms import  PanelForm
from sga.models import LugarRecaudacion, Panel, InscripcionPanel, RubroOtro
from sga.commonviews import addUserData, ip_client_address

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
def view(request):
    if request.method=='POST':
        if 'action' in request.POST:
            action = request.POST['action']

            if action == 'add':

                    f = PanelForm(request.POST)
                    if f.is_valid():
                        try:
                            if request.POST['ban'] == '1':
                                panel = Panel(nombre=f.cleaned_data['nombre'],
                                                         fecha=f.cleaned_data['fecha'],
                                                         horainicio = f.cleaned_data['horainicio'],
                                                         horafin = f.cleaned_data['horafin'],
                                                         capacidad = f.cleaned_data['capacidad'])
                                panel.save()
                                mensaje = 'Adicionado'

                            else:
                                panel = Panel.objects.get(pk=int(request.POST['id']))
                                panel.nombre=f.cleaned_data['nombre']
                                panel.fecha=f.cleaned_data['fecha']
                                panel.horainicio = f.cleaned_data['horainicio']
                                panel.horafin = f.cleaned_data['horafin']
                                panel.capacidad = f.cleaned_data['capacidad']
                                panel.save()

                                mensaje = 'Editado'
                        # Log Editar Inscripcion
                            client_address = ip_client_address(request)
                            LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(panel).pk,
                                object_id       = panel.id,
                                object_repr     = force_str(panel),
                                action_flag     = CHANGE,
                                change_message  = mensaje + " Panel " +  '(' + client_address + ')' )

                            return HttpResponseRedirect("/panel")
                        except Exception as ex:
                            if request.POST['ban'] == '1':
                                return HttpResponseRedirect("panel?action=add&error=1",)
                            else:
                                return HttpResponseRedirect("panel?action=editar&error=1&id="+str(request.POST['seminario']),)
                    else:
                        if request.POST['ban'] == '1':
                            return HttpResponseRedirect("panel?action=add&error=1",)
                        else:
                            return HttpResponseRedirect("panel?action=editar&error=1&id="+str(request.POST['seminario']),)

    else:
        data = {'title': 'Paneles'}
        addUserData(request,data)
        try:
            if 'action' in request.GET:
                action = request.GET['action']

                if action == 'add':
                    data['form'] = PanelForm(initial={"fecha":datetime.now().date(),"horainicio":'00:00:00',"horafin":'00:00:00'})
                    if 'error' in request.GET:
                        data['error'] = 1
                    data['ban'] =1
                    return render(request ,"panel/add.html" ,  data)

                if action == 'ver':
                    data['seminario'] = Panel.objects.get(pk=request.GET['id'])
                    data['inscritos'] = InscripcionPanel.objects.filter(panel__id=request.GET['id'])

                    return render(request ,"panel/ver.html" ,  data)

                if action == 'eliminarins':
                    i =  InscripcionPanel.objects.get(pk=request.GET['id'])
                    g = i.panel.id
                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de EDITAR HORARIO CLASE
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(i).pk,
                        object_id       = i.id,
                        object_repr     = force_str(i),
                        action_flag     = CHANGE,
                        change_message  = 'Eliminada Inscripcion Panel (' + client_address + ')'  )
                    i.delete()

                    return HttpResponseRedirect("/panel?action=ver&id="+str(g))

                if action == 'eliminar':
                    i =  Panel.objects.get(pk=request.GET['id'])
                    g = i
                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de EDITAR HORARIO CLASE
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(i).pk,
                        object_id       = i.id,
                        object_repr     = force_str(i),
                        action_flag     = CHANGE,
                        change_message  = 'Eliminado Panel (' + client_address + ')'  )
                    i.delete()

                    return HttpResponseRedirect("/panel")

                elif action == 'editar':
                    panel = Panel.objects.get(pk=request.GET['id'])
                    initial = model_to_dict(panel)
                    data['form'] = PanelForm(initial=initial)
                    if 'error' in request.GET:
                        data['error'] = 1
                    data['ban'] = 2
                    data['panel'] = panel
                    return render(request ,"panel/add.html" ,  data)

            else:
                search = ""
                if 's' in request.GET:
                    search = request.GET['s']

                if search:
                    panel = Panel.objects.filter(nombre__icontains=search).order_by('id')
                else:

                    panel = Panel.objects.all().order_by('id')
                paging = MiPaginador(panel, 30)
                p = 1
                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                        # if band==0:
                        #     inscripciones = Inscripcion.objects.all().order_by('persona__apellido1')
                        paging = MiPaginador(panel, 30)
                    page = paging.page(p)
                except Exception as ex:
                    page = paging.page(1)


                data['paging'] = paging
                data['rangospaging'] = paging.rangos_paginado(p)
                data['page'] = page
                data['panel'] = page.object_list
                data['search'] = search if search else ""
                return render(request ,"panel/panel.html" ,  data)
        except Exception as e:
            pass

