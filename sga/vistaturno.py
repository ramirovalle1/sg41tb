from datetime import datetime, timedelta
import json
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template import RequestContext
from decorators import secure_module
from sga.models import PuntoAtencion,TurnoCab,TurnoDet,VturnoVideo

@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
@transaction.atomic()
def view(request):
    if request.method=='POST':
        data = {'title': 'Visor de Turnos Admision'}
        action = request.POST['action']
        if action=='turno':
           data['lista_turno'] = turno()
           return HttpResponse(json.dumps({"result":"ok","turno":turno()}),content_type="application/json");
    else:
        data = {'title': 'Visor de Turnos Admision'}
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='print':#********      Genera el nuevo Tiket        ***************
                a=''
        else:
            data['url'] = ''
            data['anch'] = ''
            data['alt'] = ''
            data['codc'] = ''
            if VturnoVideo.objects.filter(tipovista=1,estado=True).exists():
                video=VturnoVideo.objects.get(tipovista=1,estado=True)
                data['url'] = video.confv
                data['anch'] = video.anchpor
                data['alt'] = video.altopx
                data['codc'] = video.codec
            data['lista_turno'] = turno()
            return render(request ,"turno/turno.html" ,  data)
def turno():
    lista_turno = []
    if PuntoAtencion.objects.filter(atencioncliente__estado=True).exclude(estadopunto=False).order_by('punto'):
        for n in PuntoAtencion.objects.filter(atencioncliente__estado=True).exclude(estadopunto=False).order_by('punto'):
            tikets=0
            if PuntoAtencion.objects.all().exclude(estadopunto=False):
                if TurnoDet.objects.filter(TurnoCab__AtencionCliente__puntoatencion=n,TurnoCab__AtencionCliente__estado=True,TurnoCab__fechatiket=datetime.now().date()).exists():
                   turon= TurnoDet.objects.filter(TurnoCab__AtencionCliente__puntoatencion=n).order_by('-id')[:1].get()
                   tikets=turon.tiket
                lista_turno.append([n.id,n.punto,tikets])
    return lista_turno