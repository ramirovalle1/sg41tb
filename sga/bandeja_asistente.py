from datetime import datetime
import json
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Q
from django.forms import model_to_dict
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.utils.encoding import force_str
from decorators import secure_module
from settings import PROFESORES_GROUP_ID, ALUMNOS_GROUP_ID, SISTEMAS_GROUP_ID
from sga.commonviews import addUserData, ip_client_address
from sga.forms import AsistAsuntoEstudiantForm,  HorarioPersonaForm
from sga.models import  Persona, Inscripcion, elimina_tildes, AsistenteDepartamento,  Departamento, HorarioAsistenteSolicitudes,HorarioPersona


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
    try:
        if request.method == 'POST':
            if 'action' in request.POST:
                action = request.POST['action']

                if action == 'addhorario':
                    asistente = AsistenteDepartamento.objects.get(pk=request.POST['id'])
                    f = HorarioPersonaForm(request.POST)
                    if f.is_valid():
                        if 'idhor' in request.POST:
                            horario = HorarioPersona.objects.get(id = request.POST['idhor'])
                            horario.persona= asistente.persona
                            horario.horaentrada = f.cleaned_data['horaentrada']
                            horario.horasalida = f.cleaned_data['horasalida']
                            horario.horalunesent = f.cleaned_data['horalunesent']
                            horario.horalunessal = f.cleaned_data['horalunessal']
                            horario.horamartesent = f.cleaned_data['horamartesent']
                            horario.horamartessal = f.cleaned_data['horamartessal']
                            horario.horamiercolesent = f.cleaned_data['horamiercolesent']
                            horario.horamiercolessal = f.cleaned_data['horamiercolessal']
                            horario.horajuevesent = f.cleaned_data['horajuevesent']
                            horario.horajuevessal = f.cleaned_data['horajuevessal']
                            horario.horaviernesent = f.cleaned_data['horaviernesent']
                            horario.horaviernessal = f.cleaned_data['horaviernessal']
                            horario.horasabadoent = f.cleaned_data['horasabadoent']
                            horario.horasabadosal = f.cleaned_data['horasabadosal']
                            horario.horadomingoent = f.cleaned_data['horadomingoent']
                            horario.horadomingosal = f.cleaned_data['horadomingosal']

                            mensaj=' editado'

                        else:

                            horario = HorarioPersona(
                                                persona=asistente.persona,
                                                horaentrada = f.cleaned_data['horaentrada'],
                                                horasalida = f.cleaned_data['horasalida'],
                                                horalunesent = f.cleaned_data['horalunesent'],
                                                horalunessal = f.cleaned_data['horalunessal'],
                                                horamartesent = f.cleaned_data['horamartesent'],
                                                horamartessal = f.cleaned_data['horamartessal'],
                                                horamiercolesent = f.cleaned_data['horamiercolesent'],
                                                horamiercolessal = f.cleaned_data['horamiercolessal'],
                                                horajuevesent = f.cleaned_data['horajuevesent'],
                                                horajuevessal = f.cleaned_data['horajuevessal'],
                                                horaviernesent = f.cleaned_data['horaviernesent'],
                                                horaviernessal = f.cleaned_data['horaviernessal'],
                                                horasabadoent = f.cleaned_data['horasabadoent'],
                                                horasabadosal = f.cleaned_data['horasabadosal'],
                                                horadomingoent = f.cleaned_data['horadomingoent'],
                                                horadomingosal = f.cleaned_data['horadomingosal'] )
                            mensaj=' ingresado'
                        horario.save()
                        try:
                        # case server externo
                            client_address = request.META['HTTP_X_FORWARDED_FOR']
                        except:
                            # case localhost o 127.0.0.1
                            client_address = request.META['REMOTE_ADDR']

                        # Log de ADICIONAR CENTRO DE COSTO
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(horario).pk,
                            object_id       = horario.id,
                            object_repr     = force_str(horario),
                            action_flag     = CHANGE,
                            change_message  = 'Horario de '+ str(elimina_tildes(horario.persona.nombre_completo()))+ mensaj +' (' + client_address + ')' )

                    return HttpResponseRedirect("/horario_asistente?action=horarioasis&id="+str(asistente.id))
        else:
            data = {"title":"Horarios de Asistentes"}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']

                if action == 'horarioasis':
                    hoy = datetime.now().date()
                    asistente =AsistenteDepartamento.objects.filter(pk=request.GET['id'])[:1].get()
                    horarios = HorarioPersona.objects.filter(persona=asistente.persona)
                    data['horarios']=horarios
                    data['cont']=horarios.count()
                    data['asistente']=asistente
                    return render(request ,"bandeja_asistente/horario.html" ,  data)
                elif action == 'eliminar':
                    horario=HorarioPersona.objects.filter(pk=request.GET['id'])[:1].get()
                    try:
                    # case server externo
                        client_address = request.META['HTTP_X_FORWARDED_FOR']
                    except:
                        # case localhost o 127.0.0.1
                        client_address = request.META['REMOTE_ADDR']
                    mensaj=' eliminado'
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(horario).pk,
                        object_id       = horario.id,
                        object_repr     = force_str(horario),
                        action_flag     = DELETION,
                        change_message  = 'Horario de '+ str(elimina_tildes(horario.persona.nombre_completo()))+ mensaj +' (' + client_address + ')' )
                    horario.delete()
                    return  HttpResponseRedirect("/horario_asistente?action=horarioasis&id="+request.GET['idasis'])
                elif action == 'editar':
                    data['title'] = 'Editar Horario'
                    error = None
                    asistente = AsistenteDepartamento.objects.get(pk=request.GET['id'])
                    if AsistenteDepartamento.objects.filter(id=request.GET['id']).exists():
                        horario = HorarioPersona.objects.get(id=request.GET['horid'])
                        data['edit']  = 1
                        initial = model_to_dict(horario)
                        data['form'] = HorarioPersonaForm(initial=initial)
                        data['asistente'] = asistente
                        data['horario'] = horario
                        # data['fechahoy'] = datetime.now().date()
                        data['error'] = error if error else ""
                        return render(request ,"bandeja_asistente/addhorario.html" ,  data)
                elif action == 'addhorarioasis':
                    data['title'] = 'Ingresar Horario'
                    error = None
                    asistente = AsistenteDepartamento.objects.get(pk=request.GET['id'])
                    if 'hor' in request.GET:
                        data['horar']  = 1

                    data['form'] = HorarioPersonaForm()
                    data['asistente'] = asistente
                    # data['fechahoy'] = datetime.now().date()
                    data['error'] = error if error else ""
                    return render(request ,"bandeja_asistente/addhorario.html" ,  data)

                return HttpResponseRedirect('/horario_asistente')

            else:
                persona = Persona.objects.filter(usuario=request.user)[:1].get()
                asistentes=None
                if AsistenteDepartamento.objects.filter(persona=persona,puedereasignar=True).exists():
                    dpto = AsistenteDepartamento.objects.filter(persona=persona,puedereasignar=True).values('departamento')
                    ids = AsistenteDepartamento.objects.filter(persona=persona,puedereasignar=True).values('id')
                    asistentes = AsistenteDepartamento.objects.filter(departamento__id__in=dpto,activo=True).exclude(id__in=ids)

                else:
                    if  data['persona'].usuario.is_superuser:
                        asistentes = AsistenteDepartamento.objects.filter()
                search = None
                if asistentes:
                    if 's' in request.GET:
                        search = request.GET['s']
                    if search:
                        ss = search.split(' ')
                        while '' in ss:
                            ss.remove('')
                        if len(ss)==1:
                            asistentes = asistentes.filter(Q(persona__nombres__icontains=search) | Q(persona__apellido1__icontains=search) | Q(persona__apellido2__icontains=search) | Q(persona__cedula__icontains=search) | Q(persona__pasaporte__icontains=search) ).order_by('persona__apellido1')
                        else:
                            asistentes = asistentes.filter(Q(persona__apellido1__icontains=ss[0]) & Q(persona__apellido2__icontains=ss[1])).order_by('persona__apellido1','persona__apellido2','persona__nombres')

                    paging = MiPaginador(asistentes, 30)
                    p = 1
                    try:
                        if 'page' in request.GET:
                            p = int(request.GET['page'])
                            # if band==0:
                            #     inscripciones = Inscripcion.objects.all().order_by('persona__apellido1')
                            paging = MiPaginador(asistentes, 30)
                        page = paging.page(p)
                    except Exception as ex:
                        page = paging.page(1)

                    data['paging'] = paging
                    data['rangospaging'] = paging.rangos_paginado(p)
                    data['page'] = page
                    data['search'] = search if search else ""
                    data['asistentes']=page.object_list
                    if 'error' in request.GET:
                        data['error'] = request.GET['error']
                    data['fechaactual']=datetime.now().date()

                return render(request ,"bandeja_asistente/asistentes.html" ,  data)
    except Exception as ex:
        return HttpResponseRedirect('/?info='+str(ex))
