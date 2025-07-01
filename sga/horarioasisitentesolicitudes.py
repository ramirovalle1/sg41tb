from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
from sga.alu_matricula import MiPaginador
from sga.commonviews import addUserData, ip_client_address
from sga.forms import  HorarioAsistenteSoliForm
from sga.models import  HorarioAsistenteSolicitudes, Persona
import json


def view(request):

    if request.method=='POST':

        if 'action' in request.POST:
            action = request.POST['action']

    else:
        data = {'title': 'Listado de Horarios de Solicitudes'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
        else:
            search  = None
            horasis=None
            filtro  = None
            ejerce = None
            cargo = None
            if 'filter' in request.GET:
                filtro = request.GET['filter']
                data['filtro']  = filtro

            if 's' in request.GET:
                search = request.GET['s']

            if search:
                try:
                    if Persona.objects.filter(Q(cedula__icontains=search)|Q(pasaporte__icontains=search)):
                        usuarios = Persona.objects.filter(Q(cedula__icontains=search)|Q(pasaporte__icontains=search)).values('usuario')
                        horasis = HorarioAsistenteSolicitudes.objects.filter(usuario__id__in=usuarios).order_by('-fecha')
                    else:
                        horasis = HorarioAsistenteSolicitudes.objects.filter(usuario__username__icontains=search).order_by('-fecha')

                except Exception as e:
                    pass
            else:
                horasis = HorarioAsistenteSolicitudes.objects.all().order_by('-fecha')
            paging = MiPaginador(horasis, 30)
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
            data['form'] = HorarioAsistenteSoliForm()
            data['horasis'] = page.object_list
            if 'error' in request.GET:
                data['error']= request.GET['error']
            return render(request ,"horarioasistentesolicitudes/horarioasistentesolicitudes.html" ,  data)
