# -*- coding: latin-1 -*-
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models.query_utils import Q
from django.http import HttpResponse
from django.shortcuts import render
from decorators import secure_module
from settings import FACTURACION_ELECTRONICA
from sga.commonviews import addUserData
from sga.facturacionelectronica import facturacionelectronicaeject, notacreditoelectronica
from sga.models import RetiradoMatricula, EliminacionMatricula


@login_required(redirect_field_name='ret', login_url='/login')
# @secure_module
def view(request):
    data = {'title': 'Matriculas Eliminadas'}
    addUserData(request,data)
    try:
        # if FACTURACION_ELECTRONICA:
        #     facturacionelectronicaeject()
        #     notacreditoelectronica()
        search = None
        if 's' in request.GET:
            search = request.GET['s']

        if search:
            ss = search.split(' ')
            while '' in ss:
                ss.remove('')
            if len(ss)==1:
                retirados = EliminacionMatricula.objects.filter(Q(inscripcion__persona__nombres__icontains=search) | Q(inscripcion__persona__apellido1__icontains=search) | Q(inscripcion__persona__apellido2__icontains=search) | Q(inscripcion__persona__cedula__icontains=search) | Q(inscripcion__persona__pasaporte__icontains=search)).order_by('-fecha', 'inscripcion__persona__apellido1')
            else:
                retirados = EliminacionMatricula.objects.filter(Q(inscripcion__persona__apellido1__icontains=ss[0]) & Q(inscripcion__persona__apellido2__icontains=ss[1])).order_by('-fecha', 'inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')
        else:
            retirados = EliminacionMatricula.objects.all().order_by('-fecha','inscripcion__persona__apellido1')


        paging = Paginator(retirados, 100)
        p = 1
        try:
            if 'page' in request.GET:
                p = int(request.GET['page'])
            page = paging.page(p)
        except:
            page = paging.page(1)

        data['paging'] = paging
        data['page'] = page
        data['search'] = search if search else ""
        data['retirados'] = page.object_list
        return render(request ,"eliminado_matricula/eliminado_matricula.html" ,  data)
    except :
        return HttpResponse("/retirados")
