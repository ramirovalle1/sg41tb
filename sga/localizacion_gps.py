import json
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from geopy import Nominatim
from sga.commonviews import addUserData
from sga.models import LeccionGrupo
from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action == 'consult':
                try:
                    geolocator = Nominatim()
                    location = geolocator.reverse(str(request.POST['latitu'])+','+str(request.POST['longi']))
                    localizacion = 'Direccion: '+elimina_tildes(location.raw['address']['road']) +' '+elimina_tildes(location.raw['address']['residential'])+' '+elimina_tildes(location.raw['address']['county'])+' '+elimina_tildes(location.raw['address']['state'])
                    # print(location.address)
                    return HttpResponse(json.dumps({"result":"ok", "direccion": str(elimina_tildes(localizacion))}),content_type="application/json")
                except:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
            if action == 'direccion':
                leccionGrupo = LeccionGrupo.objects.get(pk=request.POST['id'])
                try:
                    geolocator = Nominatim()
                    location = geolocator.reverse(str(request.POST['latitu'])+','+str(request.POST['longi']))
                    localizacion = 'Direccion: '+elimina_tildes(location.raw['address']['road']) +' '+elimina_tildes(location.raw['address']['residential'])+' '+elimina_tildes(location.raw['address']['county'])+' '+elimina_tildes(location.raw['address']['state'])
                    if leccionGrupo.ubicacion == None:
                        leccionGrupo.ubicacion=localizacion
                        leccionGrupo.save()

                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except:
                    if leccionGrupo.ubicacion == None:
                        leccionGrupo.ubicacion='NO se encuentra ubicacion'
                        leccionGrupo.save()
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
            if action == 'error':
                leccionGrupo = LeccionGrupo.objects.get(pk=request.POST['id'])
                try:
                   if leccionGrupo.ubicacion == None:
                        leccionGrupo.ubicacion=request.POST['mensajee']
                        leccionGrupo.save()
                   return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except:
                    if leccionGrupo.ubicacion == None:
                        leccionGrupo.ubicacion='NO se encuentra ubicacion'
                        leccionGrupo.save()
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
        else:
            data = {'title': 'Niveles Academicos'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']
            else:
                return render(request ,"localizacion_gps/localizacion_gps.html" ,  data)
    except:
        return HttpResponseRedirect('/')