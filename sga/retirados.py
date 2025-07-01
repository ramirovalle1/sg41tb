# -*- coding: latin-1 -*-
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models.query_utils import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template import RequestContext
from decorators import secure_module
from settings import PROFESORES_GROUP_ID, ALUMNOS_GROUP_ID, SISTEMAS_GROUP_ID
from sga.commonviews import addUserData
from sga.forms import ReintegrarRetiroForm,SeguimientoRetiroForm
from sga.models import RetiradoMatricula, DetalleRetiradoMatricula, Persona, convertir_fecha
import json

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
        if 'action' in request.POST:
            action = request.POST['action']
            if action== 'reintegrar':
                try:
                    f = ReintegrarRetiroForm(request.POST)
                    r = RetiradoMatricula.objects.filter(pk=request.POST['id'])[:1].get()

                    if f.is_valid():
                        fecha=request.POST['fecha']
                        fecha=(convertir_fecha(fecha))

                        r.activo=True
                        r.save()
                        if request.POST['departamento']:
                            departamento = int(request.POST['departamento'])
                        else:
                            departamento = None

                        if request.POST['persona_id']:
                            persona = int(request.POST['persona_id'])
                        else:
                            persona = None
                        dr = DetalleRetiradoMatricula(retirado=r,
                                                      motivo=request.POST['motivo'],
                                                      fecha=fecha,
                                                      estado='REINTEGRO',
                                                      usuario=request.user,
                                                      departamento_id=departamento,
                                                      persona_id=persona)
                        dr.save()
                        return HttpResponseRedirect('/retirados?s='+r.inscripcion.persona.cedula)
                    else:
                        return HttpResponseRedirect('/retirados?s='+r.inscripcion.persona.cedula)
                except Exception as ex:
                    print(ex)

            elif action=='buscapersona':
                if request.POST['persona']:
                    persona = int(request.POST['persona'])
                else:
                    persona = None
                gruposexcluidos = [PROFESORES_GROUP_ID,ALUMNOS_GROUP_ID,SISTEMAS_GROUP_ID]
                if not Persona.objects.filter(pk=persona).exclude(usuario__groups__id__in=gruposexcluidos,usuario__is_active=True).exists():
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
                else:
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")


            elif action== 'seguimiento':
                f = SeguimientoRetiroForm(request.POST)
                dr = DetalleRetiradoMatricula.objects.filter(retirado__id=request.POST['id']).get()
                if f.is_valid():
                    dr.seguimiento=f.cleaned_data['seguimiento']
                    dr.f_seguimiento=f.cleaned_data['fecha']
                    dr.usrseguimiento=request.user
                    dr.save()

                    return HttpResponseRedirect('/retirados?s='+dr.retirado.inscripcion .persona.cedula)
                else:
                    return HttpResponseRedirect('/retirados?s='+dr.retirado.inscripcion.persona.cedula)
    else:
        data = {'title': 'Retirados de Matriculas'}
        addUserData(request,data)
        try:
            if 'action' in request.GET:
                action = request.GET['action']
                if action == 'ver':
                    data={}
                    data['detalle'] = DetalleRetiradoMatricula.objects.filter(retirado__id=request.GET['id'])
                    return render(request ,"retirados/detalleretiro.html" ,  data)
                if action == 'retirar':
                    data={}
                    r = RetiradoMatricula.objects.filter(pk=request.GET['id'])[:1].get()
                    data['form'] =ReintegrarRetiroForm(initial={'fecha': datetime.now().strftime("%d-%m-%Y")})
                    data['r'] =r
                    gruposexcluidos = [PROFESORES_GROUP_ID,ALUMNOS_GROUP_ID,SISTEMAS_GROUP_ID]
                    data['gruposexcluidos'] = list(Persona.objects.filter().exclude(usuario__groups__id__in=gruposexcluidos,usuario__is_active=True).order_by('apellido1').values_list('id', flat=True))
                    return render(request ,"retirados/reintegrar.html" ,  data)

                if action == 'seguimiento':
                    data={}
                    r = RetiradoMatricula.objects.filter(pk=request.GET['id'])[:1].get()
                    data['form'] =SeguimientoRetiroForm(initial={'fecha': datetime.now().strftime("%d-%m-%Y")})
                    data['r'] =r
                    return render(request ,"retirados/seguimiento.html" ,  data)

            detalleanio = RetiradoMatricula.objects.filter().values_list('detalleretiradomatricula__fecha__year',flat=True).distinct().order_by('detalleretiradomatricula__fecha__year').exclude(detalleretiradomatricula__estado='REINTEGRO')
            data['anioselect'] = [{"anio": i} for i in detalleanio]

            search = None
            if 's' in request.GET:
                search = request.GET['s']

            if search:
                ss = search.split(' ')
                while '' in ss:
                    ss.remove('')
                if len(ss)==1:
                    retirados = RetiradoMatricula.objects.filter(Q(inscripcion__persona__nombres__icontains=search) | Q(inscripcion__persona__apellido1__icontains=search) | Q(inscripcion__persona__apellido2__icontains=search) | Q(inscripcion__persona__cedula__icontains=search) | Q(inscripcion__persona__pasaporte__icontains=search)).order_by( 'inscripcion__persona__apellido1')
                else:
                    retirados = RetiradoMatricula.objects.filter(Q(inscripcion__persona__apellido1__icontains=ss[0]) & Q(inscripcion__persona__apellido2__icontains=ss[1])).order_by( 'inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')
            else:
                retirados = RetiradoMatricula.objects.all().order_by('inscripcion__persona__apellido1')

            if 'aselect' in request.GET:
                anio = request.GET['aselect']
                data['anio'] = int(anio) if anio else ""
                retirados = RetiradoMatricula.objects.filter(detalleretiradomatricula__fecha__year=anio).exclude(detalleretiradomatricula__estado='REINTEGRO')
                contadorretirados = retirados.count()
                data['totalretirados'] =contadorretirados

            paging = MiPaginador(retirados, 30)
            p = 1
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
            data['retirados'] = page.object_list
            return render(request ,"retirados/retiradosbs.html" ,  data)
        except Exception as ex:
            return HttpResponse("/retirados")
