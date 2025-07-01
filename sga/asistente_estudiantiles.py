from datetime import datetime, timedelta
import json
from math import ceil
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.utils.encoding import force_str
from decorators import secure_module
from settings import PROFESORES_GROUP_ID, ALUMNOS_GROUP_ID, SISTEMAS_GROUP_ID
from sga.commonviews import addUserData, ip_client_address
from sga.forms import AsistAsuntoEstudiantForm
from sga.models import AsistAsuntoEstudiant, Persona, Inscripcion, elimina_tildes, Carrera, RegistroSeguimiento


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
                if action == 'add':
                    try:
                        if 'estado' in request.POST:
                            estado = True
                        else:
                            estado = False
                        if request.POST['editar'] == '0':
                            asistestudiant = AsistAsuntoEstudiant(asistente_id=request.POST['idsolici'], fecha=request.POST['fecha'], estado=estado, telefono=request.POST['telefono'])
                            mensaje = 'Ingreso asistente de asunto estudiantil'
                        else:
                            asistestudiant = AsistAsuntoEstudiant.objects.get(pk=request.POST['editar'])
                            asistestudiant.asistente_id = request.POST['idsolici']
                            asistestudiant.fecha=request.POST['fecha']
                            asistestudiant.estado=estado
                            asistestudiant.telefono = request.POST['telefono']
                            mensaje = 'Edicion asistente de asunto estudiantil'
                        asistestudiant.save()

                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(asistestudiant).pk,
                            object_id       = asistestudiant.id,
                            object_repr     = force_str(asistestudiant),
                            action_flag     = ADDITION,
                            change_message  = mensaje+' (' + client_address + ')' )

                        return HttpResponseRedirect('/asistente_estudiantiles')
                    except Exception as ex:
                        return HttpResponseRedirect('asistente_estudiantiles?error=Error al ingresar el asistente vuelva a intentarlo')
                elif action == 'activar':
                    try:
                        asistestudiant =  AsistAsuntoEstudiant.objects.get(pk=request.POST['idasistasunt'])
                        if asistestudiant.estado:
                            mensaje = 'Desactivacion de asistente de asunto estudiantil'
                        else:
                            mensaje = 'Activacion de asistente de asunto estudiantil'
                        asistestudiant.estado = not asistestudiant.estado
                        asistestudiant.save()

                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(asistestudiant).pk,
                            object_id       = asistestudiant.id,
                            object_repr     = force_str(asistestudiant),
                            action_flag     = ADDITION,
                            change_message  = mensaje+' (' + client_address + ')' )
                        return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                    except:
                        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
                elif action == 'reasignar':
                    try:
                        asistente = AsistAsuntoEstudiant.objects.filter(asistente__usuario__id=request.POST['usuario'])[:1].get()
                        asistrecibe = AsistAsuntoEstudiant.objects.filter(asistente__usuario__id=request.POST['asistrecibe'])[:1].get()
                        cantidad = int(request.POST['cantidad'])
                        if (cantidad > (asistente.asignados() - asistente.gestionados())) and asistente.estado:
                            return HttpResponse(json.dumps({"result":"bad",'mensaje': 'Cantidad excede las inscripciones asignadas'}),content_type="application/json")
                        if asistente.estado:
                            inscripcion = Inscripcion.objects.filter(asistente = asistente,registroseguimiento__inscripcion=None)[:cantidad]
                        else:
                            inscripcion = Inscripcion.objects.filter(asistente=asistente)[:cantidad]
                        if request.POST['carrera'] != '':
                            carrera = Carrera.objects.get(pk=request.POST['carrera'])
                            inscripcion = Inscripcion.objects.filter(asistente = asistente,registroseguimiento__inscripcion=None, carrera=carrera)[:cantidad]
                        for i in inscripcion:
                            i.asistente = asistrecibe
                            i.save()
                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(asistente).pk,
                            object_id       = asistente.id,
                            object_repr     = force_str(asistente),
                            action_flag     = ADDITION,
                            change_message  = 'Se ha reasignado ' + str(cantidad) + ' registros de '+ elimina_tildes(asistente.asistente.nombre_completo()) + 'a ' + elimina_tildes  (asistrecibe.asistente.nombre_completo()) + ' ('+ client_address + ')' )
                        return HttpResponse(json.dumps({"result":"ok", 'cantidad':inscripcion.count(), 'nuevoGestor':asistrecibe.asistente.nombre_completo_inverso()}),content_type="application/json")

                    except Exception as e:
                        return HttpResponse(json.dumps({"result":"bad",'mensaje': str(e)}),content_type="application/json")

                elif action == 'cruzar':
                    try:
                        asistente = AsistAsuntoEstudiant.objects.filter(asistente__usuario__id=request.POST['usuario'])[:1].get()
                        asistcruce = AsistAsuntoEstudiant.objects.filter(asistente__usuario__id=request.POST['asistcruce'])[:1].get()
                        inscripcion1 = Inscripcion.objects.filter(asistente = asistente,registroseguimiento__inscripcion=None).values('id')
                        inscripcion2 = Inscripcion.objects.filter(asistente = asistcruce,registroseguimiento__inscripcion=None).values_list('id',flat=True)
                        lista=[]
                        for i in Inscripcion.objects.filter(id__in=inscripcion1):
                            i.asistente = asistcruce
                            i.save()
                            lista.append(i.id)

                        for ins in Inscripcion.objects.filter(id__in=inscripcion2).exclude(id__in =lista):
                            ins.asistente = asistente
                            ins.save()
                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(asistente).pk,
                            object_id       = asistente.id,
                            object_repr     = force_str(asistente),
                            action_flag     = ADDITION,
                            change_message  = 'Cruce de cartera entre  '+ elimina_tildes(asistente.asistente.nombre_completo()) + ' y ' + elimina_tildes  (asistcruce.asistente.nombre_completo()) + ' ('+ client_address + ')' )
                        return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")

                    except Exception as e:
                        return HttpResponse(json.dumps({"result":"bad",'mensaje': str(e)}),content_type="application/json")
                elif action == 'existe':
                    try:
                        if request.POST['editar'] == '0':
                            if AsistAsuntoEstudiant.objects.filter(asistente__id=request.POST['idasis']).exists():
                                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                        else:
                            if AsistAsuntoEstudiant.objects.filter(asistente__id=request.POST['idasis']).exclude(pk=request.POST['editar']).exists():
                                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
                    except:
                        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

                elif action == 'redistribuirCartera':
                    try:
                        fechaFiltro = datetime.now() - timedelta(days=int(request.POST['cantidad']))
                        gestionesAntiguas = RegistroSeguimiento.objects.filter().exclude(fecha__gte=fechaFiltro)
                        inscripciones = Inscripcion.objects.filter(id__in=gestionesAntiguas.values('inscripcion')).exclude(asistente=None)
                        asistentes = AsistAsuntoEstudiant.objects.filter(estado=True).order_by('asistente__apellido1', 'asistente__apellido2')

                        indice_asistente = 0
                        for inscripcion in inscripciones:
                            asistente_actual = AsistAsuntoEstudiant.objects.filter(estado=True).order_by('asistente__apellido1', 'asistente__apellido2')[indice_asistente]
                            inscripcion.asistente = asistente_actual
                            inscripcion.save()

                            indice_asistente = (indice_asistente + 1) % asistentes.count()

                        persona = Persona.objects.get(usuario__username=request.user)
                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(persona).pk,
                        object_id       = persona.id,
                        object_repr     = force_str(persona),
                        action_flag     = CHANGE,
                        change_message  = 'REDISTRIBUCION DE CARTERA: (dias ingresados: '+request.POST['cantidad']+') - '+'(' + client_address + ')' )

                        return HttpResponse(json.dumps({"result":"ok", "cantidadAsistentes":asistentes.count(), "cantidadInscripcion":inscripciones.count(), 'promedio':ceil(inscripciones.count() / asistentes.count())}),content_type="application/json")
                    except Exception as e:
                        print(e)
                        return HttpResponse(json.dumps({"result":"bad", 'error': str(e)}),content_type="application/json")

        else:
            data = {"title":"Asistentes de Asuntos Estudiantiles"}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']
                if action == 'eliminar':
                    asisten = AsistAsuntoEstudiant.objects.filter(pk=request.GET['id'])[:1].get()
                    asisten.estado = not asisten.estado
                    asisten.save()
                return HttpResponseRedirect('/asistente_estudiantiles')
            else:
                search = None
                if 's' in request.GET:
                    search = request.GET['s']
                if search:
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')
                    if len(ss)==1:
                        asistentes = AsistAsuntoEstudiant.objects.filter(Q(asistente__nombres__icontains=search) | Q(asistente__apellido1__icontains=search) | Q(asistente__apellido2__icontains=search) | Q(asistente__cedula__icontains=search) | Q(asistente__pasaporte__icontains=search) ).order_by('asistente__apellido1')
                    else:
                        asistentes = AsistAsuntoEstudiant.objects.filter(Q(asistente__apellido1__icontains=ss[0]) & Q(asistente__apellido2__icontains=ss[1])).order_by('asistente__apellido1','asistente__apellido2','asistente__nombres')
                else:
                    asistentes = AsistAsuntoEstudiant.objects.filter(estado=True).order_by('asistente__apellido1')
                if 'i' in request.GET:
                    asistentes = AsistAsuntoEstudiant.objects.filter(estado=False).order_by('asistente__apellido1')
                    data['inactivos'] = True
                if 'r' in request.GET:
                    data['registros'] = True
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
                data['asis'] = AsistAsuntoEstudiant.objects.filter(estado=True).order_by('asistente__apellido1')
                gruposexcluidos = [PROFESORES_GROUP_ID,ALUMNOS_GROUP_ID,SISTEMAS_GROUP_ID]
                data['gruposexcluidos'] = list(Persona.objects.filter().exclude(usuario__groups__id__in=gruposexcluidos).order_by('apellido1').values_list('id', flat=True))
                data['form']=AsistAsuntoEstudiantForm(initial={'fecha':datetime.now().date()})
                if 'error' in request.GET:
                    data['error'] = request.GET['error']
                data['fechaactual']=datetime.now().date()
                data['carreras'] = Carrera.objects.filter(carrera=True, activo=True).order_by('nombre')
            return render(request ,"asuntoestudiantil/asuntoestudiantil.html" ,  data)
    except Exception as ex:
        return HttpResponseRedirect('/?info='+str(ex))
