from datetime import datetime
import json
from django.contrib.admin.models import ADDITION, CHANGE, LogEntry
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
from decorators import secure_module
from settings import ID_CARRERA_CONGRESO
from sga.commonviews import addUserData, ip_client_address
from sga.models import TutorCongreso, TutorMatricula, TipoSeguimiento, TutorCongSeguimiento, Rubro, Nivel, Carrera


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
__author__ = 'jjurgiles'


@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    try:
        if request.method == 'POST':
            action = request.POST['action']
            if action == 'guardar':
                try:
                    tutormat = TutorMatricula.objects.get(id=request.POST['idtumat'])
                    # if int(request.POST['editar']) == 0:
                    tutorcongseguimiento = TutorCongSeguimiento(tutormatricula = tutormat,
                                                  tiposeguimiento_id = request.POST['idtipo'],
                                                  descripcion = request.POST['gestion'],
                                                  fecha = datetime.now())
                    actflag = ADDITION
                    mens = 'Agregado Seguimiento'

                    tutorcongseguimiento.save()

                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de ADICIONAR GRUPO
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(tutorcongseguimiento).pk,
                        object_id       = tutorcongseguimiento.id,
                        object_repr     = force_str(tutorcongseguimiento),
                        action_flag     = actflag,
                        change_message  = mens+' (' + client_address + ')'  )

                    return HttpResponse(json.dumps({'result': 'ok'}), content_type="application/json")
                except Exception as e:
                    print("Error JSON guardar tutorcongreso"+str(e))
                    return HttpResponse(json.dumps({'result': 'bad','mensaj':'Error al guardar los datos'}), content_type="application/json")
        else:
            data = {'title':'Tutor Matricula'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']
                if action == 'veralumnos':
                    tutorcongreso = TutorCongreso.objects.get(id=request.GET['id'])
                    tutormatriculas = TutorMatricula.objects.filter(tutorcongreso__id=request.GET['id'])
                    tiposeguimientos = TipoSeguimiento.objects.filter(activo=True)
                    data['tutormatriculas'] = tutormatriculas
                    data['tutorcongreso'] = tutorcongreso
                    data['tiposeguimientos'] = tiposeguimientos
                    data['urlcongr'] = '/tutormatricula'
                    data['congract'] = False
                    return render(request ,"tutorcongreso/tutorlumnos.html" ,  data)

                elif action=='vergestion':
                    data = {}
                    tutormatricula = TutorMatricula.objects.get(id=request.GET['idtumat'])
                    data['tutormatricula'] = tutormatricula
                    data['tutorseguimientos'] = TutorCongSeguimiento.objects.filter(tutormatricula=tutormatricula)
                    data['urlcongr'] = '/tutormatricula'
                    data['congract'] = False
                    return render(request ,"tutorcongreso/vergestion.html" ,  data)
                elif action=='verfinanza':
                    data = {}
                    tutormatricula = TutorMatricula.objects.get(id=request.GET['idtumat'])
                    data['tutormatricula'] = tutormatricula
                    data['rubros'] = Rubro.objects.filter(inscripcion=tutormatricula.matricula.inscripcion)
                    data['urlcongr'] = '/tutormatricula'
                    data['congract'] = False
                    return render(request ,"tutorcongreso/vergestion.html" ,  data)
            else:
                if 'idniv' in request.GET:
                    nivel = Nivel.objects.get(id=request.GET['idniv'])
                    data['nivel'] = nivel
                    tutorcongresos = TutorCongreso.objects.filter(persona=data['persona'],nivel=nivel)
                else:
                    tutorcongresos = TutorCongreso.objects.filter(persona=data['persona'])
                paging = MiPaginador(tutorcongresos, 30)
                p=1
                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                    page = paging.page(p)
                except:
                    page = paging.page(1)
                if 'info' in request.GET:
                    data['info'] = request.GET['info']
                data['paging'] = paging
                data['page'] = page
                data['rangospaging'] = paging.rangos_paginado(p)
                data['carrera'] = Carrera.objects.get(id=ID_CARRERA_CONGRESO)
                data['tutorcongresos'] = page.object_list
                return render(request ,"tutorcongreso/tutormatricula.html" ,  data)
    except Exception as e:
        print("Error tutor matricula"+str(e))
        return HttpResponseRedirect('/?info=Error comuniquese con el administrador')