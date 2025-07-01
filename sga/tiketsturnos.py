from datetime import datetime, timedelta
import json
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template import RequestContext
from decorators import secure_module
from sga.commonviews import ip_client_address
from sga.models import TipoVisitasBox,VisitaTiket,VisTiketDet,VturnoVideo, Aula

@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
@transaction.atomic()
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action=='turno':
               return HttpResponse(json.dumps({"result":"ok","turno":turno(request)}),content_type="application/json");
        else:
            data = {'title': 'Visor de Turnos'}
            if 'action' in request.GET:
                action = request.GET['action']
                if action=='print':#********      Genera el nuevo Tiket        ***************
                    a=''
            else:
                data['url'] = ''
                data['anch'] = ''
                data['alt'] = ''
                data['codc'] = ''
                if VturnoVideo.objects.filter(tipovista=2,estado=True).exists():
                    video=VturnoVideo.objects.get(tipovista=2,estado=True)
                    data['url'] = video.confv
                    data['anch'] = video.anchpor
                    data['alt'] = video.altopx
                    data['codc'] = video.codec
                data['lista_turno'] = turno(request)
                return render(request ,"visitabtiket/tiketsturno.html" ,  data)
    except:
        return HttpResponseRedirect('/')
def turno(request):
    lista_turno = []
    valida=[]
    client_address = ip_client_address(request)
    sede = 0
    if Aula.objects.filter(ip=str(client_address),activa=False).exists():
        sede = Aula.objects.filter(ip=str(client_address),activa=False)[:1].get().sede.id
    if VisTiketDet.objects.filter(atendido=True,visitatiket__fechatiket=datetime.now().date(),visitatiket__tipovisitabox__sede__id=sede).exists():
        for n in VisTiketDet.objects.filter(atendido=True,visitatiket__fechatiket=datetime.now().date(),visitatiket__tipovisitabox__sede__id=sede).order_by('-horaatendido'):
            if not n.visitatiket.tipovisitabox.visor+n.tipoatencionbox.descripcion[0] in valida and len(lista_turno) <4:
                valida.append(n.visitatiket.tipovisitabox.visor+n.tipoatencionbox.descripcion[0])
                lista_turno.append([n.id,n.visitatiket.tipovisitabox.visor+n.tipoatencionbox.descripcion[0],n.visitatiket.id,n.tiket])
    return lista_turno