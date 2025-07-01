from sga.commonviews import addUserData
from django.shortcuts import render
from django.http import HttpResponseRedirect
from sga.models import EscenarioPractica

__author__ = 'jjurgiles'


def view(request):
    try:
        if request.method == 'POST':
            action = request.POST['action']
        else:
            data = {'title':'Escenario Pract. Adm'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']
            else:
                escenario = EscenarioPractica.objects.filter().exclude(fechaenvio=None)
                return render(request ,"solicitudpractica/escenariopractadm.html" ,  data)
    except Exception as e:
        print("Error en escenariopractadm"+str(e))
        return HttpResponseRedirect("/?info=Error comuniquese con el administrador")