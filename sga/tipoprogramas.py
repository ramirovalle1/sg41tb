import datetime
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
from sga.forms import LugarRecaudacionForm, GrupoSeminarioForm, VinculacionForm, ParticipanteForm, ParticipanteIndForm, DocenteVincForm, EvidenciaForm, ObservacionForm,BeneficiariosForm, ConvenioForm, TipoProgramaForm
from sga.models import LugarRecaudacion, GrupoSeminario, InscripcionSeminario, ActividadVinculacion, EstudianteVinculacion, Nivel, Matricula, Inscripcion, DocenteVinculacion, Persona, EvidenciaVinculacion, ObservacionVinculacion,BeneficiariosVinculacion,Convenio, TipoPrograma
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
# @secure_module
def view(request):
    if request.method=='POST':
        if 'action' in request.POST:
            action = request.POST['action']
            if action == 'add':
                    f = TipoProgramaForm(request.POST)
                    if f.is_valid():
                        try:
                            if request.POST['ban'] == '1':
                                tprograma = TipoPrograma(nombre=f.cleaned_data['nombre'],
                                                         objetivo = f.cleaned_data['objetivo'])
                                tprograma.save()

                                mensaje = 'Adicionado'

                            else:
                                tprograma = TipoPrograma.objects.get(pk=int(request.POST['tprograma']))
                                tprograma.nombre=f.cleaned_data['nombre']
                                tprograma.objetivo=f.cleaned_data['objetivo']
                                tprograma.save()

                                mensaje = 'Editado'

                        # Log Editar Tipo Programa
                            client_address = ip_client_address(request)
                            LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(tprograma).pk,
                                object_id       = tprograma.id,
                                object_repr     = force_str(tprograma),
                                action_flag     = CHANGE,
                                change_message  = mensaje + " Tipo de Programa " +  '(' + client_address + ')' )

                            return HttpResponseRedirect("/tipoprogramas")
                        except Exception as ex:
                            if request.POST['ban'] == '1':
                                return HttpResponseRedirect("tipoprogramas?action=add&error=1",)
                            else:
                                return HttpResponseRedirect("tipoprogramas?action=editar&error=1&id="+str(request.POST['tprograma']),)
                    else:
                        if request.POST['ban'] == '1':
                            return HttpResponseRedirect("tipoprogramas?action=add&error=1",)
                        else:
                            return HttpResponseRedirect("tipoprogramas?action=editar&error=1&id="+str(request.POST['tprograma']),)

    else:
        data = {'title': 'Tipos de Programas'}
        addUserData(request,data)
        try:
            if 'action' in request.GET:
                action = request.GET['action']

                if action == 'add':
                    data['form'] = TipoProgramaForm()
                    if 'error' in request.GET:
                        data['error'] = 1
                    data['ban'] =1
                    return render(request ,"vinculacion/addtipoprograma.html" ,  data)

                elif action == 'editar':
                    tprograma = TipoPrograma.objects.get(pk=request.GET['id'])
                    initial = model_to_dict(tprograma)
                    data['form'] = TipoProgramaForm(initial=initial)
                    if 'error' in request.GET:
                        data['error'] = 1
                    data['ban'] = 2
                    data['tprograma'] =tprograma

                    return render(request ,"vinculacion/addtipoprograma.html" ,  data)

                elif action == 'activa':
                   tprograma =  TipoPrograma.objects.filter(id=request.GET['id'])[:1].get()

                   if tprograma.activo:
                      activo = False
                      mensaje = 'Tipo Programa Inactivo'
                   else:
                       activo = True
                       mensaje = 'Tipo Programa Activo'

                   tprograma.activo = activo
                   tprograma.save()

                   client_address = ip_client_address(request)
                   #Log de Modificar Tipo de Programa
                   LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(tprograma).pk,
                        object_id       = tprograma.id,
                        object_repr     = force_str(tprograma),
                        action_flag     = CHANGE,
                        change_message  = mensaje +' cambio estado  (' + client_address + ')')
                   return HttpResponseRedirect('/tipoprogramas')

                return HttpResponseRedirect("/tipoprogramas")

            else:
                search = ""
                activos = None
                inactivos = None
                todos = None

                if 's' in request.GET:
                    search = request.GET['s']
                if 't' in request.GET:
                    todos = request.GET['t']
                if 'a' in request.GET:
                    activos = request.GET['a']
                if 'i' in request.GET:
                    inactivos = request.GET['i']

                if search:
                    tprograma = TipoPrograma.objects.filter(Q(nombre__icontains=search)).order_by('nombre')
                else:
                    tprograma = TipoPrograma.objects.all().order_by('-activo','nombre')

                if todos:
                    tprograma = TipoPrograma.objects.all().order_by('-activo','nombre')

                if activos:
                    tprograma = TipoPrograma.objects.filter(activo=True).order_by('nombre')

                if inactivos:
                    tprograma = TipoPrograma.objects.filter(activo=False).order_by('nombre')

                paging = MiPaginador(tprograma, 30)
                p = 1
                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                        paging = MiPaginador(tprograma, 30)
                    page = paging.page(p)
                except Exception as ex:
                    page = paging.page(1)

                data['paging'] = paging
                data['rangospaging'] = paging.rangos_paginado(p)
                data['page'] = page
                data['tprograma'] = page.object_list
                data['todos'] = todos if todos else ""
                data['activos'] = activos if activos else ""
                data['inactivos'] = inactivos if inactivos else ""
                data['search'] = search if search else ""
                return render(request ,"vinculacion/tipoprograma.html" ,  data)
        except Exception as ex:
            pass

