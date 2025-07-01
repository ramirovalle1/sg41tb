import json
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from decorators import secure_module
from settings import UTILIZA_GRUPOS_ALUMNOS
from sga.commonviews import addUserData
from sga.models import Inscripcion, Absentismo

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
        if request.method == 'POST':
            action = request.POST['action']
            if action == 'activar':
                absentismo = Absentismo.objects.get(id=request.POST['idabs'])
                if absentismo.reintegro:
                    absentismo.reintegro = False
                else:
                    absentismo.reintegro = True
                absentismo.save()
                return HttpResponse(json.dumps({"result": "ok"}),content_type="application/json")

        else:
            data = {'title':'Absentismo Finalizado'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']
                if action=='detalleabsent':
                    data = {}
                    if request.GET['n'] == '0':
                        nointegrados = True
                    else:
                        nointegrados = False
                    data['inscripcion'] = Inscripcion.objects.filter(id=request.GET['id'])[:1].get()
                    data['absentismos'] = Absentismo.objects.filter(materiaasignada__matricula__inscripcion=request.GET['id'],reintegro=nointegrados).exclude(finalizado=False).order_by('id')
                    return render(request ,"absentismo/detalle.html" ,  data)
            else:
                search = None

                nointegrados = None

                if 's' in request.GET:
                    search = request.GET['s']
                    data['search'] = search
                if 'n' in request.GET:
                    nointegrados = request.GET['n']

                if search:
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')
                    if len(ss)==1:
                        inscripciones = Inscripcion.objects.filter(Q(persona__nombres__icontains=search) | Q(persona__apellido1__icontains=search) | Q(persona__apellido2__icontains=search) | Q(persona__cedula__icontains=search) | Q(persona__pasaporte__icontains=search) | Q(identificador__icontains=search) | Q(inscripciongrupo__grupo__nombre__icontains=search) | Q(carrera__nombre__icontains=search) | Q(persona__usuario__username__icontains=search),pk__in=Absentismo.objects.filter(finalizado=True).distinct('materiaasignada__matricula__inscripcion').values('materiaasignada__matricula__inscripcion')).order_by('persona__apellido1')
                    else:
                        inscripciones = Inscripcion.objects.filter(Q(persona__apellido1__icontains=ss[0]) & Q(persona__apellido2__icontains=ss[1]),pk__in=Absentismo.objects.filter(finalizado=True).distinct('materiaasignada__matricula__inscripcion').values('materiaasignada__matricula__inscripcion')).order_by('persona__apellido1','persona__apellido2','persona__nombres')
                else:
                    inscripciones = Inscripcion.objects.filter(persona__usuario__is_active=True,pk__in=Absentismo.objects.filter(finalizado=True,reintegro=True).distinct('materiaasignada__matricula__inscripcion').values('materiaasignada__matricula__inscripcion')).order_by('persona__apellido1')
                if nointegrados:
                    if not search:
                        inscripciones = Inscripcion.objects.filter(persona__usuario__is_active=True,pk__in=Absentismo.objects.filter(finalizado=True,reintegro=False).distinct('materiaasignada__matricula__inscripcion').values('materiaasignada__matricula__inscripcion')).order_by('persona__apellido1')
                    data['nointegrados'] = nointegrados



                paging = MiPaginador(inscripciones, 30)
                p = 1
                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                        # if band==0:
                        #     inscripciones = Inscripcion.objects.all().order_by('persona__apellido1')
                        paging = MiPaginador(inscripciones, 30)
                    page = paging.page(p)
                except Exception as ex:
                    page = paging.page(1)

                data['paging'] = paging
                data['rangospaging'] = paging.rangos_paginado(p)
                data['page'] = page

                data['inscripciones'] = page.object_list
                data['utiliza_grupos_alumnos'] = UTILIZA_GRUPOS_ALUMNOS

                return render(request ,"absentismo/absentismo_finaliza.html" ,  data)

    except Exception as e:
        return HttpResponseRedirect('/info='+str(e))
