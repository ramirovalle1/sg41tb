from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render
from decorators import secure_module
from sga.commonviews import addUserData
from django.core.paginator import Paginator
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from settings import INSCRIPCION_CONDUCCION
from sga.models import Carrera, MateriaAsignada, Persona, Matricula, Inscripcion, Rubro, InscripcionSeminario, GrupoSeminario,GraduadoConduccion,Periodo

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

    if INSCRIPCION_CONDUCCION:
        data = {'title': 'Busqueda de Cursos'}
        addUserData(request, data)
        search = None
        filtro = None
        if 'filter' in request.GET:
            filtro = request.GET['filter']

        if 's' in request.GET:
            search = request.GET['s']
        if search:
            ss = search.split(' ')
            while '' in ss:
                ss.remove('')
            if len(ss)==1:
                graduados = GraduadoConduccion.objects.filter(Q(inscripcion__persona__nombres__icontains=search) | Q(inscripcion__persona__apellido1__icontains=search) | Q(inscripcion__persona__apellido2__icontains=search) | Q(inscripcion__persona__cedula__icontains=search) | Q(inscripcion__persona__pasaporte__icontains=search)).order_by('inscripcion__persona__apellido1', 'inscripcion__persona__apellido2')
            else:
                graduados = GraduadoConduccion.objects.filter(Q(inscripcion__persona__apellido1__icontains=ss[0]) & Q(inscripcion__persona__apellido2__icontains=ss[1])).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')
        else:

            graduados = GraduadoConduccion.objects.all().order_by('inscripcion__persona__apellido1', 'inscripcion__persona__apellido2')

        if filtro:
            if  Periodo.objects.filter(pk=filtro).exists():
                periodo = Periodo.objects.get(pk=filtro)
            else:
                periodo = Periodo.objects.all()[:1].get()
            graduados = GraduadoConduccion.objects.filter(periodo=periodo).order_by('inscripcion__persona__apellido1', 'inscripcion__persona__apellido2')


        paging = Paginator(graduados, 50)
        p=1
        try:
            if 'page' in request.GET:
                p = int(request.GET['page'])
            page = paging.page(p)
        except:
            page = paging.page(1)
        data['paging'] = paging
        # data['rangospaging'] = paging.rangos_paginado(p)
        data['page'] = page
        data['search'] = search if search else ""
        data['filter'] = periodo if filtro else ""
        data['periodos'] = Periodo.objects.all().order_by('nombre')
        data['graduados'] = page.object_list
        return render(request ,"consultagraduados_condu/graduadosbs_condu.html" ,  data)

    if 'action' in request.GET:
            action = request.GET['action']
            if action=='activation':
                pass
                # d.activo = not d.activo
                # d.save()
                # return HttpResponseRedirect("/docentes")

            elif action=='graduarcondu':
                if INSCRIPCION_CONDUCCION:
                    data = {'title': 'Busqueda de Cursos'}
                    addUserData(request, data)
                    search = None
                    filtro = None
                    if 'filter' in request.GET:
                        filtro = request.GET['filter']

                    if 's' in request.GET:
                        search = request.GET['s']
                    if search:
                        ss = search.split(' ')
                        while '' in ss:
                            ss.remove('')
                        if len(ss)==1:
                            graduados = GraduadoConduccion.objects.filter(Q(inscripcion__persona__nombres__icontains=search) | Q(inscripcion__persona__apellido1__icontains=search) | Q(inscripcion__persona__apellido2__icontains=search) | Q(inscripcion__persona__cedula__icontains=search) | Q(inscripcion__persona__pasaporte__icontains=search)).order_by('inscripcion__persona__apellido1', 'inscripcion__persona__apellido2')
                        else:
                            graduados = GraduadoConduccion.objects.filter(Q(inscripcion__persona__apellido1__icontains=ss[0]) & Q(inscripcion__persona__apellido2__icontains=ss[1])).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')
                    else:
                        graduados = GraduadoConduccion.objects.all().order_by('inscripcion__persona__apellido1', 'inscripcion__persona__apellido2')

                    if filtro:
                        if  Periodo.objects.filter(pk=filtro).exists():
                            periodo = Periodo.objects.get(pk=filtro)
                        else:
                            periodo = Periodo.objects.all()[:1].get()
                        graduados = GraduadoConduccion.objects.filter(periodo=periodo).order_by('inscripcion__persona__apellido1', 'inscripcion__persona__apellido2')


                    paging = Paginator(graduados, 50)
                    p=1
                    try:
                        if 'page' in request.GET:
                            p = int(request.GET['page'])
                        page = paging.page(p)
                    except:
                        page = paging.page(1)
                    data['paging'] = paging
                    # data['rangospaging'] = paging.rangos_paginado(p)
                    data['page'] = page
                    data['search'] = search if search else ""
                    data['filter'] = periodo if filtro else ""
                    data['periodos'] = Periodo.objects.all().order_by('nombre')
                    data['graduados'] = page.object_list
                    return render(request ,"consultagraduados_condu/graduadosbs_condu.html" ,  data)


    return HttpResponseRedirect("/consultagraduados_condu")