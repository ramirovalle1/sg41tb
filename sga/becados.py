from datetime import datetime
import json
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models.query_utils import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from decorators import secure_module
from settings import SEXO_FEMENINO, SEXO_MASCULINO
from sga.commonviews import addUserData
from sga.finanzas import convertir_fecha
from sga.forms import FechaBecaForm, TipoBecaForm, MotivoBecaForm
from sga.models import Matricula, Periodo, TipoBeca, MotivoBeca
from sga.commonviews import addUserData, ip_client_address
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_str
from django.template import RequestContext


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
    """

    :param request:
    :return:
    """
    if request.method=='POST':
        action = request.POST['action']
        if action=='fechabeca':
            try:
                fecha = convertir_fecha(request.POST['fecha'])
                idest = Matricula.objects.get(pk=request.POST['idest'])
                idest.fechabeca = fecha
                idest.save()
                return HttpResponse(json.dumps({'result':'ok'}),content_type="application/json")
            except Exception as ex:
                return HttpResponse(json.dumps({'result':'bad'}),content_type="application/json")

        elif action == 'addtipobeca':
            f= TipoBecaForm(request.POST)
            if f.is_valid():
                if 'tipobeca' in request.POST:
                    tipobeca = TipoBeca.objects.get(pk=request.POST['tipobeca'])
                    tipobeca.nombre = f.cleaned_data['nombre']
                    mensaje = 'Modificado'

                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(tipobeca).pk,
                    object_id       = tipobeca.id,
                    object_repr     = force_str(tipobeca),
                    action_flag     = CHANGE,
                    change_message  = mensaje + ' Tipo de Beca(' + client_address + ')' )

                else:
                    tipobeca = TipoBeca(nombre=f.cleaned_data['nombre'])
                    mensaje = 'Adicionado'


                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(tipobeca).pk,
                        object_id       = tipobeca.id,
                        object_repr     = force_str(tipobeca),
                        action_flag     = ADDITION,
                        change_message  = mensaje + 'Tipo de Beca(' + client_address + ')' )

                tipobeca.save()
                return  HttpResponseRedirect("/becados?action=tipobecas")

        elif action == 'addmotivobeca':
            f= MotivoBecaForm(request.POST)
            if f.is_valid():
                if 'motivobeca' in request.POST:
                    motivobeca = MotivoBeca.objects.get(pk=request.POST['motivobeca'])
                    motivobeca.nombre = f.cleaned_data['nombre']
                    mensaje = 'Modificado'

                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(motivobeca).pk,
                    object_id       = motivobeca.id,
                    object_repr     = force_str(motivobeca),
                    action_flag     = CHANGE,
                    change_message  = mensaje + ' Motivo de Beca(' + client_address + ')' )

                else:
                    motivobeca = MotivoBeca(nombre=f.cleaned_data['nombre'])
                    mensaje = 'Adicionado'


                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(motivobeca).pk,
                        object_id       = motivobeca.id,
                        object_repr     = force_str(motivobeca),
                        action_flag     = ADDITION,
                        change_message  = mensaje + 'Motivo de Beca(' + client_address + ')' )

                motivobeca.save()
                return  HttpResponseRedirect("/becados?action=motivobecas")


        return HttpResponseRedirect("/becados")
    else:
        data = {'title': 'Listado de Estudiantes con Becas'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']

            if action == 'tipobecas':
                data['title'] = 'Tipos de Becas '
                data['tipobecas'] = TipoBeca.objects.all().order_by('nombre')
                return render(request ,"becados/tipobecas.html" ,  data)

            elif action == 'addtipobeca':
                data['title'] = 'Adicionar Tipo de Beca'
                data['form']= TipoBecaForm()
                return render(request ,"becados/addtipobecas.html" ,  data)

            elif action == 'edittipobeca':
                data['title'] = 'Editar Tipo de Beca '
                data['tipobecas'] = TipoBeca.objects.filter(pk=request.GET['id'])[:1].get()
                data['form']= TipoBecaForm(initial={'nombre':data['tipobecas'].nombre})
                return render(request ,"becados/addtipobecas.html" ,  data)

            elif action == 'motivobecas':
                data['title'] = 'Motivos de Becas '
                data['motivobecas'] = MotivoBeca.objects.all().order_by('nombre')
                return render(request ,"becados/motivobecas.html" ,  data)

            elif action == 'addmotivobeca':
                data['title'] = 'Adicionar Motivo de Beca'
                data['form']= MotivoBecaForm()
                return render(request ,"becados/addmotivobecas.html" ,  data)

            elif action == 'editmotivobeca':
                data['title'] = 'Editar Motivo de Beca '
                data['motivobecas'] = MotivoBeca.objects.filter(pk=request.GET['id'])[:1].get()
                data['form']= MotivoBecaForm(initial={'nombre':data['motivobecas'].nombre})
                return render(request ,"becados/addmotivobecas.html" ,  data)



        else:
            periodo = Periodo.objects.get(pk=request.session['periodo'].id)
            search = None

            if 's' in request.GET:
                search = request.GET['s']
            if search:
                ss = search.split(' ')
                while '' in ss:
                    ss.remove('')
                if len(ss)==1:
                    becados = Matricula.objects.filter(Q(inscripcion__persona__nombres__icontains=search) | Q(inscripcion__persona__apellido1__icontains=search) | Q(inscripcion__persona__apellido2__icontains=search) | Q(inscripcion__persona__cedula__icontains=search) | Q(inscripcion__persona__pasaporte__icontains=search), becado=True, nivel__periodo=periodo).order_by('inscripcion__persona__apellido1', 'inscripcion__persona__apellido2', 'inscripcion__persona__nombres')
                else:
                    becados = Matricula.objects.filter(Q(inscripcion__persona__apellido1__icontains=ss[0]) & Q(inscripcion__persona__apellido2__icontains=ss[1]), becado=True, nivel__periodo=periodo).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')

            else:
                becados = Matricula.objects.filter(becado=True, nivel__periodo=periodo).order_by('nivel__periodo', 'inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')

            paging = MiPaginador(becados, 50)
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
            data['becados'] = page.object_list
            data['periodo'] = periodo
            data['becados_periodo'] = becados.count()
            data['matriculados_periodo'] = Matricula.objects.filter(nivel__periodo=periodo).count()
            data['porciento_becados_matriculados'] = round(becados.count() * 100.0 / Matricula.objects.filter(nivel__periodo=periodo).count(), 2) if Matricula.objects.filter(nivel__periodo=periodo).exists() else 0
            data['becados_mujeres_periodo'] = becados.filter(inscripcion__persona__sexo__id=SEXO_FEMENINO).count()
            data['becados_hombres_periodo'] = becados.filter(inscripcion__persona__sexo__id=SEXO_MASCULINO).count()
            data['fechabecaform'] = FechaBecaForm({'fecha': datetime.now()})
            return render(request ,"becados/becados.html" ,  data)
