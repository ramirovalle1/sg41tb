import json
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from sga.commonviews import addUserData
from sga.models import Test, ColumnaTestArrastrar, elimina_tildes


@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    if request.method == 'POST':
        action = request.POST['action']

        if action == 'agregarcolumna':
            try:
                data = {'title': ''}

                if ColumnaTestArrastrar.objects.filter(
                        descripcion=elimina_tildes(request.POST['descripcion']).upper()).exists():
                    return HttpResponse(
                        json.dumps({'result': 'bad', 'message': 'El Nombre de la columna ya existe'}),
                        content_type="application/json")


                if (str(request.POST['ladob']) == 'true'):
                    ladob = 2
                else:
                    ladob = 1

                columnatest=ColumnaTestArrastrar(descripcion=elimina_tildes(request.POST['descripcion']).upper(),
                                            orden=int(request.POST['orden']),test_id=int(request.POST['idtest']),
                                            pregunta_id=int(request.POST['idpregunta']),lado=ladob,
                     estado=True)

                columnatest.save()

                data['result'] = 'ok'
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}), content_type="application/json")



        elif action == 'eliminar':
            try:
                data = {'title': ''}
                columnatest = ColumnaTestArrastrar.objects.get(pk=int(request.POST['idcolumnapre']))
                columnatest.delete()
                data['result'] = 'ok'
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}), content_type="application/json")








    else:
        data = {'title': 'Listado de Parametros '}
        addUserData(request, data)
        search=None

        test = Test.objects.get(pk=int(request.GET['idtest']))

        data['test'] = test
        data['idpregunta'] = int(request.GET['idpregunta'])

        if 'action' in request.GET:
            action = request.GET['action']






        else:
            try:

                if 's' in request.GET:
                    search = str(request.GET['s']).upper()
                    listacolumna = ColumnaTestArrastrar.objects.filter(test=test,descripcion__contains=search,pregunta__id=int(request.GET['idpregunta'])).order_by("descripcion")
                else:
                    listacolumna = ColumnaTestArrastrar.objects.filter(test=test,pregunta__id=int(request.GET['idpregunta'])).order_by("descripcion")

                data['search'] = search if search else ""
                data['listacolumna'] = listacolumna


                return render(request ,"testingreso/mantenimiento/agregarcolumna.html" ,  data)
            except Exception as ex:
                print(ex)
                return render(request ,"/panel" ,  data)
