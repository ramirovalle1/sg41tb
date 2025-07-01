import json
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from sga.commonviews import addUserData
from sga.models import ArchivoSolicitudBeca

__author__ = 'vgonzalez'
@login_required(redirect_field_name='ret', login_url='/login')
# @secure_module
# @transaction.atomic()
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action == 'agregararchivosolicitud':
                if ArchivoSolicitudBeca.objects.filter(nombre = str(request.POST['nombre']).upper()).exists():
                     return HttpResponse(json.dumps({'result':'bad', 'message':'Nombre del archivo ya existe'}), content_type="application/json")

                tipoarchivo = ArchivoSolicitudBeca(nombre = str(request.POST['nombre']).upper())
                tipoarchivo.save()
                return HttpResponse(json.dumps({'result':'ok'}), content_type="application/json")

            if action == 'eliminar':
                tipoarchivo = ArchivoSolicitudBeca.objects.get(pk=int(request.POST['id']))
                tipoarchivo.delete()
                return HttpResponse(json.dumps({'result':'ok'}), content_type="application/json")

            if action == 'actualizar':
                tipoarchivo = ArchivoSolicitudBeca.objects.get(pk=int(request.POST['idRe']))
                tipoarchivo.nombre = str(request.POST['nombreEdit']).upper()
                tipoarchivo.save()
                return HttpResponse(json.dumps({'result':'ok'}), content_type="application/json")

        else:
            data = {'title': 'Archivos'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']
            else:
                search = None
                if 's' in request.GET:
                    search = request.GET['s']

                if search:
                    archivosolicitud = ArchivoSolicitudBeca.objects.filter(nombre__icontains = search)
                else:
                    archivosolicitud = ArchivoSolicitudBeca.objects.filter()

                data['search'] = search if search else ''
                data['listarchivosolicitud']= archivosolicitud

                return render(request ,"archivosolicitudbeca/archivosolicitudbeca.html" ,  data)
    except Exception as e:
        return HttpResponseRedirect("/")