import json
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import Sum, Q
from django.forms import model_to_dict
from django.utils.encoding import force_str
from decorators import secure_module
from settings import EMAIL_ACTIVE, MARGEN_GANANCIA
from sga.models import RegistroMedicamento, TipoMedicamento, DetalleRegistroMedicamento, BajaMedicamento, RecetaVisitaBox, Sede, Persona, TrasladoMedicamento,DetalleVisitasBox, Profesor, Aula, Parroquia,Provincia, Canton, Sector
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.core.paginator import Paginator
from sga.commonviews import addUserData, ip_client_address
from django.template import RequestContext
from sga.forms import RegistroMedicamentoForm, EntregaMedicamentoForm, EditarProvinciaForm, EditarCantonForm, EditarParroquiaForm, EditarSectorForm
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
            if action == 'editarprov':
                try:
                    provincia = Provincia.objects.filter(pk=request.POST['id'])[:1].get()
                    provincia.nombre = request.POST['nombre']
                    provincia.save()
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
            elif action == 'editarcan':
                try:
                    if request.POST['id'] == '0':
                        canton = Canton(nombre = request.POST['nombre'],
                                        provincia_id = request.POST['provincia'])
                        canton.save()
                        msj = 'Adicionado'
                        action = ADDITION
                    else:
                        canton = Canton.objects.filter(pk=request.POST['id'])[:1].get()
                        canton.nombre = request.POST['nombre']
                        canton.provincia_id = request.POST['provincia']
                        canton.save()
                        msj = 'Editado'
                        action = CHANGE
                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de ADICIONAR RECORD
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(canton).pk,
                        object_id       = canton.id,
                        object_repr     = force_str(canton),
                        action_flag     = action,
                        change_message  = msj +  ' Canton (' + client_address + ')' )
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
            elif action == 'editaparr':
                try:
                    if request.POST['id'] == '0':
                        parroquia = Parroquia(nombre = request.POST['nombre'],
                                               canton_id = request.POST['canton'])
                        parroquia.save()
                        msj = 'Adicionada'
                        action = ADDITION
                    else:
                        parroquia = Parroquia.objects.filter(pk=request.POST['id'])[:1].get()
                        parroquia.nombre = request.POST['nombre']
                        parroquia.canton_id = request.POST['canton']
                        parroquia.save()
                        msj = 'Editada'
                        action = CHANGE

                        #Obtain client ip address
                        client_address = ip_client_address(request)

                        # Log de ADICIONAR RECORD
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(parroquia).pk,
                            object_id       = parroquia.id,
                            object_repr     = force_str(parroquia),
                            action_flag     = action,
                            change_message  = msj +  ' Parroquia (' + client_address + ')' )
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
            elif action == 'editasect':
                try:
                    if request.POST['id'] == '0':
                        sector = Sector(nombre = request.POST['nombre'],
                                               parroquia_id = request.POST['parroquia'])
                        sector.save()
                        msj = 'Adicionado'
                        action = ADDITION
                    else:
                        sector = Sector.objects.filter(pk=request.POST['id'])[:1].get()
                        sector.nombre = request.POST['nombre']
                        sector.parroquia_id = request.POST['parroquia']
                        sector.save()
                        msj = 'Editada'
                        action = CHANGE

                        #Obtain client ip address
                        client_address = ip_client_address(request)

                        # Log de ADICIONAR RECORD
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(sector).pk,
                            object_id       = sector.id,
                            object_repr     = force_str(sector),
                            action_flag     = action,
                            change_message  = msj +  ' Sector (' + client_address + ')' )
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")


        else:
            data = {'title': 'Mantenimiento '}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']
                if action == 'cantones':
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

                        cantones = Canton.objects.filter(Q(nombre__icontains=search)|Q(provincia__nombre__icontains=search)).order_by('provincia__nombre')
                    else:
                        cantones = Canton.objects.all()

                    paging = MiPaginador(cantones, 30)
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
                    data['cantones'] = page.object_list
                    data['frmcanton'] =  EditarCantonForm()
                    return render(request ,"mtto_sectores/cantones.html" ,  data)
                elif action == 'parroquias':
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

                        parroquias = Parroquia.objects.filter(Q(nombre__icontains=search)|Q(canton__nombre__icontains=search)).order_by('canton__nombre')
                    else:
                        parroquias = Parroquia.objects.all()

                    paging = MiPaginador(parroquias, 30)
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
                    data['parroquias'] = page.object_list
                    data['frmparroquia'] =  EditarParroquiaForm()
                    return render(request ,"mtto_sectores/parroquias.html" ,  data)

                elif action == 'sectores':
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

                        sectores = Sector.objects.filter(Q(nombre__icontains=search)|Q(parroquia__nombre__icontains=search)).order_by('parroquia__nombre')
                    else:
                        sectores = Sector.objects.all()

                    paging = MiPaginador(sectores, 30)
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
                    data['sectores'] = page.object_list
                    data['frmparroquia'] =  EditarSectorForm()
                    return render(request ,"mtto_sectores/sectores.html" ,  data)

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

                    provincia = Provincia.objects.filter(nombre__icontains=search).order_by('nombre')
                else:
                    provincia = Provincia.objects.all()

                paging = MiPaginador(provincia, 30)
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
                data['provincia'] = page.object_list
                data['frmprov'] =  EditarProvinciaForm()
                return render(request ,"mtto_sectores/mtto_sectores.html" ,  data)
    except Exception as ex:
        return HttpResponseRedirect("/")