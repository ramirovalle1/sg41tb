import os
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.template import RequestContext
from settings import SITE_ROOT
from sga.commonviews import addUserData
from sga.models import ArchivoReporteCarrera


@login_required(redirect_field_name='ret', login_url='/login')

def view(request):
    if request.method=='POST':
        action = request.POST['action']


    else:
        data = {'title': 'Listado de Reportes por Carrera'}
        addUserData(request,data)
        data['reportecarrera'] = ArchivoReporteCarrera.objects.filter(carrera__grupocoordinadorcarrera__group__in=request.user.groups.all())
        if os.path.exists(SITE_ROOT + '/media/gestion/'+'ReporteResumen.xls'):
            data['reporte'] = 'media/gestion/'+'ReporteResumen.xls'
        return render(request ,"reportesexcel/nuevo_reporte_carrera.html" ,  data)

