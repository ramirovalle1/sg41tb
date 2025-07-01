from datetime import datetime, timedelta
import json
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template import RequestContext
from decorators import secure_module
from sga.models import TipoVisitasBox,VisitaTiket,VisTiketDet

@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
@transaction.atomic()
def view(request):
    if request.method=='POST':
        action = request.POST['action']
        if action=='turno':
           return HttpResponse(json.dumps({"result":"ok","turno":turno()}),content_type="application/json");
    else:
        data = {'title': 'Visor de Turnos'}
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='print':#********      Genera el nuevo Tiket        ***************
                a=''
        else:
            data['lista_turno'] = turno()
            return render(request ,"turno/turno.html" ,  data)
def turno():
    lista_turno = []
    if TipoVisitasBox.objects.filter().exclude(alias=None).exclude(alias='').exists():
        for n in TipoVisitasBox.objects.filter().exclude(alias=None).exclude(alias=''):
            dettik=0
            idvis=0
            if VisitaTiket.objects.filter(fechatiket=datetime.now().date(),tipovisitabox=n.id).exists():
                visi = VisitaTiket.objects.get(fechatiket=datetime.now().date(),tipovisitabox=n.id)
                idvis=visi.id
                if VisTiketDet.objects.filter(atendido=True,visitatiket__id=visi.id).exists():
                    det = VisTiketDet.objects.filter(atendido=True,visitatiket__id=visi.id).order_by('-id')[:1].get()
                    dettik=det.tiket
            lista_turno.append([n.id,str(n.alias).split('-')[1],idvis,dettik])
    return lista_turno
