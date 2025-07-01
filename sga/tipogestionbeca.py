import json
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template import RequestContext
from sga.commonviews import addUserData
from sga.models import TipoGestionBeca

__author__ = 'vgonzalez'
@login_required(redirect_field_name='ret', login_url='/login')
# @secure_module
# @transaction.atomic()
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action == 'agregartipogestionbeca':
                if TipoGestionBeca.objects.filter(nombre = str(request.POST['nombre']).upper()).exists():
                     return HttpResponse(json.dumps({'result':'bad', 'message':'Nombre del tipo del gestion ya existe'}), content_type="application/json")

                tipoestado = TipoGestionBeca(nombre = str(request.POST['nombre']).upper())
                tipoestado.save()
                return HttpResponse(json.dumps({'result':'ok'}), content_type="application/json")

            if action == 'eliminar':
                tipoestado = TipoGestionBeca.objects.get(pk=int(request.POST['id']))
                tipoestado.delete()
                return HttpResponse(json.dumps({'result':'ok'}), content_type="application/json")

            if action == 'actualizar':
                tipoestado = TipoGestionBeca.objects.get(pk=int(request.POST['idRe']))
                tipoestado.nombre = str(request.POST['nombreEdit']).upper()
                if int(request.POST['idestado']) == 1:
                    tipoestado.estado = True
                else:
                    tipoestado.estado = False
                tipoestado.save()

                return HttpResponse(json.dumps({'result':'ok'}), content_type="application/json")

        else:
            data = {'title': 'Gestion'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']

            else:
                search = None
                if 's' in request.GET:
                    search = request.GET['s']

                if search:
                    tipogestionbeca = TipoGestionBeca.objects.filter(nombre__icontains = search)
                else:
                    tipogestionbeca = TipoGestionBeca.objects.filter()

                data['search'] = search if search else ''
                data['listagestionbeca']= tipogestionbeca

                return render(request ,"tipogestionbeca/tipogestionbeca.html" ,  data)
    except Exception as e:
        return HttpResponseRedirect("/")