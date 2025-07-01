from datetime import datetime
import json
from django.contrib.admin.models import LogEntry, ADDITION, DELETION, CHANGE
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
from sga.commonviews import addUserData, ip_client_address
from sga.forms import NivelTutorForm, DatosTutorForm, TutorForm, TutorForm2
from sga.models import NivelTutor, AsistenteDepartamento, Nivel, Matricula, MatriculaTutor


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
@transaction.atomic()

def view(request):
    if request.method=='POST':
        action = request.POST['action']

        if action == 'add_tutor':
            try:
                print(request.POST)
                tutor = AsistenteDepartamento.objects.filter(pk=request.POST['tutor'])[:1].get()

                if NivelTutor.objects.filter(tutor=tutor).exists():
                    return HttpResponseRedirect('/tutor_grupo?error=Este usuario ya se encuentra registrado como Tutor')
                else:
                    tutor.estutor = True
                    tutor.save()
                    mensaje = 'Ingreso de tutor'
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(tutor).pk,
                    object_id       = tutor.id,
                    object_repr     = force_str(tutor),
                    action_flag     = CHANGE,
                    change_message  = mensaje+' (' + client_address + ')' )
                return HttpResponseRedirect('/tutor_grupo')
            except Exception as ex:
                print(ex)
                return HttpResponseRedirect('/tutor_grupo?error=Error al ingresar tutor, vuelva a intentarlo')

        elif action == 'add_grupo':
            try:
                print(request.POST)
                asistente = AsistenteDepartamento.objects.filter(pk=request.POST['idasistente'])[:1].get()
                nivel = Nivel.objects.filter(pk=request.POST['nivel_id'])[:1].get()
                if 'activo' in request.POST:
                    activo = True
                else:
                    activo = False

                if NivelTutor.objects.filter(nivel=nivel).exists():
                    niveltutor = NivelTutor.objects.filter(nivel=nivel)[:1].get()
                    return HttpResponseRedirect('/tutor_grupo?error=El grupo "'+niveltutor.nivel.paralelo+'" ya tiene como tutor a "'+niveltutor.tutor.persona.nombre_completo_inverso()+'"')
                else:
                    niveltutor = NivelTutor(nivel=nivel, tutor=asistente, activo=activo)
                    niveltutor.save()

                    matriculas = Matricula.objects.filter(nivel=niveltutor.nivel)
                    for i in matriculas:
                        if not MatriculaTutor.objects.filter(niveltutor=niveltutor, matricula=i).exists():
                            matricula_tutor = MatriculaTutor(niveltutor=niveltutor, matricula=i, activo=True)
                            matricula_tutor.save()

                    mensaje = 'Ingreso de grupo a tutor'
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(niveltutor).pk,
                    object_id       = niveltutor.id,
                    object_repr     = force_str(niveltutor),
                    action_flag     = ADDITION,
                    change_message  = mensaje+' (' + client_address + ')' )
                return HttpResponseRedirect('/tutor_grupo')
            except Exception as ex:
                print(ex)
                return HttpResponseRedirect('/tutor_grupo?error=Error al ingresar grupo, vuelva a intentarlo')

        elif action == 'edit_tutor':
            try:
                print(request.POST)
                asistente = AsistenteDepartamento.objects.filter(pk=request.POST['idasistente'])[:].get()
                print(asistente)
                asistente.persona.telefono = request.POST['telefono']
                asistente.persona.email = request.POST['correo']
                asistente.persona.save()
                mensaje = 'Ingreso de tutor'
                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                user_id         = request.user.pk,
                content_type_id = ContentType.objects.get_for_model(asistente.persona).pk,
                object_id       = asistente.persona.id,
                object_repr     = force_str(asistente.persona),
                action_flag     = CHANGE,
                change_message  = mensaje+' (' + client_address + ')' )
                return HttpResponseRedirect('/tutor_grupo')
            except Exception as ex:
                print(ex)
                return HttpResponseRedirect('/tutor_grupo?error=Error al editar tutor, vuelva a intentarlo')

        elif action == 'activar_estado':
            try:
                niveltutor =  NivelTutor.objects.get(pk=request.POST['idtutornivel'])
                print(niveltutor.tutor)
                if niveltutor.activo:
                    mensaje = 'Desactivacion de Tutor'
                else:
                    mensaje = 'Activacion de Tutor'
                niveltutor.activo = not niveltutor.activo
                niveltutor.save()
                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(niveltutor).pk,
                    object_id       = niveltutor.id,
                    object_repr     = force_str(niveltutor),
                    action_flag     = CHANGE,
                    change_message  = mensaje+' (' + client_address + ')' )

                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            except:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

        elif action == 'eliminar':
            try:
                eliminar =NivelTutor.objects.filter(pk=request.POST['idtutornivel'])[:1].get()
                eliminar.delete()
                mensaje = 'Eliminar niveltutor'
                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(eliminar).pk,
                    object_id       = eliminar.id,
                    object_repr     = force_str(eliminar),
                    action_flag     = DELETION,
                    change_message  = mensaje+' (' + client_address + ')' )
                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            except:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

        elif action == 'cambiar_tutor':
            try:
                print(request.POST)
                niveltutor =NivelTutor.objects.filter(pk=request.POST['idtutornivel'])[:1].get()
                tutor = AsistenteDepartamento.objects.filter(pk=request.POST['tutor'])
                niveltutor.tutor = tutor
                niveltutor.save()
                mensaje = 'Cambio de tutor en NivelTutor'
                # client_address = ip_client_address(request)
                # LogEntry.objects.log_action(
                #     user_id         = request.user.pk,
                #     content_type_id = ContentType.objects.get_for_model(niveltutor).pk,
                #     object_id       = niveltutor.id,
                #     object_repr     = force_str(niveltutor),
                #     action_flag     = CHANGE,
                #     change_message  = mensaje+' (' + client_address + ')' )
                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            except:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

        elif action == 'actualizar':
            result = {}
            try:
                print(request.POST)
                contador = 0
                niveltutor = NivelTutor.objects.filter(activo=True, nivel__cerrado=True)
                for n in niveltutor:
                    n.activo=False
                    n.save()
                    contador = contador + 1
                result['result']  = "Se desactivaron "+str(contador)+" niveles cerrados de los tutores"
                return HttpResponse(json.dumps(result), content_type="application/json")
            except Exception as e:
                result['result']  = str(e)
                return HttpResponse(json.dumps(result), content_type="application/json")

    else:
        data = {'title': 'Listado de Tutores'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action == 'ver_grupos':
                print(request.GET)
                niveltutor = NivelTutor.objects.filter(tutor=request.GET['id']).order_by('-activo','nivel__paralelo','nivel__nivelmalla')
                data['niveltutores'] = niveltutor
                data['form'] = TutorForm2
                if 'error' in request.GET:
                    data['error'] = 1
                return render(request ,"tutor_grupo/ver_grupos.html" ,  data)

        else:
            try:
                hoy = str(datetime.date(datetime.now()))
                search = None

                tutores = AsistenteDepartamento.objects.filter(estutor=True).order_by('persona__apellido1','persona__apellido2')
                if 's' in request.GET:
                    search = request.GET['s']
                if search:
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')
                    if len(ss)==1:
                        tutores = tutores.filter(Q(persona__apellido1__icontains=search)|Q(persona__apellido2__icontains=search)|Q(persona__nombres__icontains=search)|Q(persona__cedula__icontains=search)).order_by('persona__apellido1','persona__apellido2')
                    else:
                        tutores = tutores.filter(Q(persona__apellido1__icontains=search)|Q(persona__apellido2__icontains=search)|Q(persona__nombres__icontains=search)|Q(persona__cedula__icontains=search)).order_by('persona__apellido1','persona__apellido2')

                paging = Paginator(tutores, 20)
                p = 1
                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                    page = paging.page(p)
                except:
                    page = paging.page(1)

                data['paging'] = paging
                data['page'] = page
                data['tutores'] = page.object_list
                data['search'] = search if search else ""
                data['form'] = TutorForm
                data['form1'] = NivelTutorForm
                data['form2'] = DatosTutorForm
                if 'error' in request.GET:
                    data['error'] = request.GET['error']



                return render(request ,"tutor_grupo/tutor_grupobs.html" ,  data)
            except Exception as e:
                print(e)
                return HttpResponseRedirect("/tutor_grupo")
