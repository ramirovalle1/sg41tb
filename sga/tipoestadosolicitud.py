import json
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from sga.commonviews import addUserData
from sga.models import TipoEstadoSolicitudBeca

__author__ = 'vgonzalez'

@login_required(redirect_field_name='ret', login_url='/login')
# @secure_module
# @transaction.atomic()
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action == 'agregartipoestadosolicitud':
                if TipoEstadoSolicitudBeca.objects.filter(nombre = str(request.POST['nombre']).upper()).exists():
                     return HttpResponse(json.dumps({'result':'bad', 'message':'Nombre del tipo del estado ya existe'}), content_type="application/json")

                tipoestado = TipoEstadoSolicitudBeca(nombre = str(request.POST['nombre']).upper())
                tipoestado.save()
                return HttpResponse(json.dumps({'result':'ok'}), content_type="application/json")

            if action == 'eliminar':
                tipoestado = TipoEstadoSolicitudBeca.objects.get(pk=int(request.POST['id']))
                tipoestado.delete()
                return HttpResponse(json.dumps({'result':'ok'}), content_type="application/json")

            if action == 'actualizar':
                tipoestado = TipoEstadoSolicitudBeca.objects.get(pk=int(request.POST['idRe']))
                tipoestado.nombre = str(request.POST['nombreEdit']).upper()
                tipoestado.save()
                return HttpResponse(json.dumps({'result':'ok'}), content_type="application/json")

        else:
            data = {'title': 'Estado'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']

            else:
                search = None
                if 's' in request.GET:
                    search = request.GET['s']

                if search:
                    tipoestadosolicitud = TipoEstadoSolicitudBeca.objects.filter(nombre__icontains = search)
                else:
                    tipoestadosolicitud = TipoEstadoSolicitudBeca.objects.filter()

                data['search'] = search if search else ''
                data['listatiposolicitud']= tipoestadosolicitud

                return render(request ,"tiposolicitudbeca/tiposolicitudbeca.html" ,  data)
    except Exception as e:
        return HttpResponseRedirect("/")