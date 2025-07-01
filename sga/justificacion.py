from datetime import datetime
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Avg
from django.db.models.query_utils import Q
from django.forms.models import model_to_dict
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from decorators import secure_module
from sga.commonviews import addUserData
from sga.models import Inscripcion,    AusenciaJustificada

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
    if request.method=='POST':
        action = request.POST['action']
    else:
        data = {'title': 'Justificacion de Ausencia'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
        else:
            persona=data['persona']
            # if persona.puede_justificar_sinfechas():
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
                    justificaciones = AusenciaJustificada.objects.filter(Q(inscripcion__persona__nombres__icontains=search) | Q(inscripcion__persona__apellido1__icontains=search) | Q(inscripcion__persona__apellido2__icontains=search) | Q(inscripcion__persona__cedula__icontains=search) | Q(profesor__persona__cedula__icontains=search) | Q(profesor__persona__apellido1__icontains=search) | Q(profesor__persona__apellido2__icontains=search) | Q(usuario__username__icontains=search)).order_by('-fecha', 'inscripcion__persona__apellido1')
                else:
                    justificaciones = AusenciaJustificada.objects.filter(Q(inscripcion__persona__apellido1__icontains=ss[0]) & Q(inscripcion__persona__apellido2__icontains=ss[1])).order_by('-fecha','inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')
            else:
                justificaciones = AusenciaJustificada.objects.all().order_by('-fecha')
            paging = MiPaginador(justificaciones, 50)
            p=1
            try:
                if 'page' in request.GET:
                    p = int(request.GET['page'])
                page = paging.page(p)
            except:
                page = paging.page(1)
            data['paging'] = paging
            data['page'] = page
            data['rangospaging'] = paging.rangos_paginado(p)
            data['search'] = search if search else ""
            data['justificaciones'] = page.object_list
            return render(request ,"justificacion/justificaciones.html" ,  data)
            # else:
            #     return HttpResponseRedirect("/?info=USTED NO TIENE PERMISOS PARA VER ESTE MODULO")



