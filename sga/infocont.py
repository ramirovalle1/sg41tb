import json
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from decorators import secure_module
from sga.commonviews import addUserData
from sga.models import  RolPago, FormaDePago, Carrera, TipoOtroRubro, LugarRecaudacion


@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    if request.method=='POST':
        action = request.POST['action']
        if action == 'loadSearch':
            modelos = {'carreras':Carrera, 'formasPago':FormaDePago, 'tiposRubro':TipoOtroRubro, 'cajas':LugarRecaudacion}
            modelo = modelos[request.POST['type']].objects.filter(Q(nombre__icontains=request.POST['value'])).order_by('nombre')
            data = [{'id':x.id, 'nombre':x.nombre} for x in modelo]
            return HttpResponse(json.dumps({"result":"ok", 'registros':data}),content_type="application/json")

    else:
        try:
            data = {'title': 'Informacion Utiliza Contable'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']

                if action == 'formasPago':
                    formasPago = FormaDePago.objects.all().order_by('id')
                    data['formasPago'] = formasPago
                    return render(request ,"infocont/formasPago.html" ,  data)

                if action == 'carreras':
                    carreras = Carrera.objects.filter().order_by('id')
                    data['carreras'] = carreras
                    return render(request ,"infocont/carreras.html" ,  data)

                if action == 'tiposRubro':
                    tiposRubro = TipoOtroRubro.objects.all().order_by('id')
                    data['tiposRubro'] = tiposRubro
                    return render(request ,"infocont/tiposRubro.html" ,  data)

                if action == 'cajas':
                    cajas = LugarRecaudacion.objects.filter(activa=True).order_by('persona__apellido1','persona__apellido2','persona__nombres')
                    data['cajas'] = cajas
                    return render(request ,"infocont/cajas.html" ,  data)

            else:
                data['rolespago'] = RolPago.objects.filter(activo=True).order_by('inicio')
                return render(request ,"infocont/infocontbs.html" ,  data)
        except Exception as ex:
            print(ex)

