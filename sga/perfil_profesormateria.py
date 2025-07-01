from datetime import datetime
import json
from django.contrib.admin.models import LogEntry, ADDITION, DELETION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db import transaction
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
from sga.commonviews import addUserData, ip_client_address
from sga.forms import PerfilProfesorAsignaturaForm
from sga.models import AsignaturaMalla, Malla, PerfilProfesorAsignatura, Asignatura, Profesor


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


        if action == 'add':
            try:
                asignatura = Asignatura.objects.filter(pk=request.POST['idmateria'])[:1].get()
                profesor = Profesor.objects.filter(pk=request.POST['profesor'])[:1].get()

                if 'estado' in request.POST:
                    estado = request.POST['estado']
                else:
                    estado=False
                fecha = request.POST['fecha']
                if PerfilProfesorAsignatura.objects.filter(profesor=profesor, asignatura=asignatura).exists():
                    return HttpResponseRedirect('/perfil_profesormateria?action=seleccionar_carrera&id='+request.POST['idmalla']+'&error=Docente ya existe para impartir esta materia')
                else:
                    guardar = PerfilProfesorAsignatura(profesor=profesor, asignatura=asignatura, estado=estado, fecha = fecha)
                    guardar.save()
                    mensaje = 'Ingreso de profesor a asignatura'
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(guardar).pk,
                    object_id       = guardar.id,
                    object_repr     = force_str(guardar),
                    action_flag     = ADDITION,
                    change_message  = mensaje+' (' + client_address + ')' )
                return HttpResponseRedirect('/perfil_profesormateria?action=seleccionar_carrera&id='+request.POST['idmalla'])
            except Exception as ex:
                print(ex)
                return HttpResponseRedirect('/perfil_profesormateria?action=seleccionar_carrera&id='+request.POST['idmalla']+'&error=Error al ingresar docente, vuelva a intentarlo')

        elif action == 'eliminar':
                result = {}
                try:
                    eliminar =PerfilProfesorAsignatura.objects.filter(pk=request.POST['id'])
                    eliminar.delete()
                    mensaje = 'Eliminar docente de asignatura'
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(eliminar).pk,
                    object_id       = eliminar.id,
                    object_repr     = force_str(eliminar),
                    action_flag     = DELETION,
                    change_message  = mensaje+' (' + client_address + ')' )
                    result['result']  = "ok"
                    return HttpResponse(json.dumps(result), content_type="application/json")
                except Exception as e:
                    result['result']  = str(e)
                    return HttpResponse(json.dumps(result), content_type="application/json")


        elif action == 'activar_estado':
            try:
                profesor =  PerfilProfesorAsignatura.objects.get(pk=request.POST['id'])
                if profesor.estado:
                    mensaje = 'Desactivacion de docente'
                else:
                    mensaje = 'Activacion de docente'
                profesor.estado = not profesor.estado
                profesor.save()
                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(profesor).pk,
                    object_id       = profesor.id,
                    object_repr     = force_str(profesor),
                    action_flag     = ADDITION,
                    change_message  = mensaje+' (' + client_address + ')' )

                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            except:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")


    else:
        data = {'title': 'Listado de Mallas'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']

            if action == 'seleccionar_carrera':
                data['title'] = 'Asignaturas'
                carrera = Malla.objects.get(pk=request.GET['id'])
                search = None
                if 's' in request.GET:
                    search = request.GET['s']
                if search:
                    materia = AsignaturaMalla.objects.filter(asignatura__nombre__icontains=search,malla=carrera )

                else:
                    materia = AsignaturaMalla.objects.filter(malla=carrera).order_by('nivelmalla')

                paging = Paginator(materia, 30)
                p = 1
                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                    page = paging.page(p)
                except:
                    page = paging.page(1)
                data['paging'] = paging
                data['page'] = page
                data['malla'] = carrera
                data['materias'] = page.object_list
                data['form'] = PerfilProfesorAsignaturaForm(initial={'fecha':datetime.now().date()})
                data['search'] = search if search else ""
                data['fechaactual']=datetime.now().date()
                if 'error' in request.GET:
                    data['error'] = request.GET['error']
                return render(request ,"perfil_profesormateria/materiasbs.html" ,  data)

            elif action == 'verdocentes':
                mat=request.GET['id']
                print(mat)
                profesor = PerfilProfesorAsignatura.objects.filter(asignatura=mat)
                data['profesores'] = profesor
                if 'error' in request.GET:
                    data['error'] = 1
                return render(request ,"perfil_profesormateria/ver_docentes.html" ,  data)

            elif action == 'ver_materias':
                prof = request.GET['id']
                print('profesor es:'+prof)
                materia = PerfilProfesorAsignatura.objects.filter(profesor=prof).order_by('asignatura')

                data['materias'] = materia

                if 'error' in request.GET:
                    data['error'] = 1
                return render(request ,"perfil_profesormateria/ver_materias.html" ,  data)
        else:
            try:
                hoy = str(datetime.date(datetime.now()))
                search = None

                if 's' in request.GET:
                    search = request.GET['s']

                if search:
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')
                    if len(ss)==1:
                        malla = Malla.objects.filter(carrera__nombre__icontains=search).order_by('-inicio')
                    else:
                        malla = Malla.objects.filter(carrera__nombre__icontains=ss).order_by('-inicio')
                else:
                    malla = Malla.objects.filter(carrera__carrera=True, carrera__activo=True).order_by('-inicio')

                paging = MiPaginador(malla, 30)
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
                data['mallas'] = page.object_list
                data['profesor_asignatura'] = PerfilProfesorAsignatura.objects.filter(estado=True)
                data['fechaactual']=datetime.now().date()
                return render(request ,"perfil_profesormateria/perfil_profesormateria.html" ,  data)
            except Exception as e:
                return HttpResponseRedirect("/perfil_profesormateria")