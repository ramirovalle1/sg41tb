
from datetime import datetime, timedelta
import json
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from decorators import secure_module
from sga.models import TurnoCab,TurnoDet,NewsTiket

@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
@transaction.atomic()
def view(request):
    if request.method=='POST':
        action = request.POST['action']
        if action=='print':
           tiket=0
           fecha=datetime.now().date()
           sfecha=str(fecha)
           if TurnoDet.objects.filter(horatiket=fecha).exists():
              tiket=int(TurnoDet.objects.filter(horatiket=fecha).order_by('-tiket')[:1].get().tiket)+1
              dtiket = TurnoDet(tiket=tiket,horatiket=datetime.now(),atendido=False,hora=datetime.now())
              dtiket.save()
           else:
              tiket=1
              dtiket = TurnoDet(tiket=tiket,horatiket=datetime.now(),atendido=False,hora=datetime.now())
              dtiket.save()

           return HttpResponse(json.dumps({"result":"ok","tiket":tiket,"fechas":sfecha}),content_type="application/json");
    else:
        data = {'title': 'Impresion de Tikets'}
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='print': #********   Genera el nuevo Tiket    ***************
                a=''
        else:
            data['newstiket'] = NewsTiket.objects.filter().exclude(estadonoticia=False)
            return render(request ,"turno/turnotikets.html" ,  data)