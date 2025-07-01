import json
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.core.paginator import Paginator
from sga.commonviews import addUserData
from django.template import RequestContext
from sga.models import Test, elimina_tildes


class MiPaginador(Paginator):
    def __init__(self, object_list, per_page, orphans=0, allow_empty_first_page=True, rango=5):
        super(MiPaginador,self).__init__(object_list, per_page, orphans=orphans, allow_empty_first_page=allow_empty_first_page)
        self.rango = rango
        self.paginas = []
        self.primera_pagina = False
        self.ultima_pagina = False

    def rangos_paginado(self, pagina):
        left = pagina - self.rango
        right = pagina + self.rango
        if left<1:
            left=1
        if right>self.num_pages:
            right = self.num_pages
        self.paginas = range(left, right+1)
        self.primera_pagina = True if left>1 else False
        self.ultima_pagina = True if right<self.num_pages else False
        self.ellipsis_izquierda = left-1
        self.ellipsis_derecha = right+1

@login_required(redirect_field_name='ret', login_url='/login')
# @secure_module
# @transaction.atomic()
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action == 'agregartest':
                try:
                    data = {'title': ''}

                    if (str(request.POST['esencuesta']) == 'true'):
                        esencuesta = True
                    else:
                        esencuesta = False

                    if Test.objects.filter(
                            titulo=elimina_tildes(request.POST['titulo']).upper()).exists():
                        return HttpResponse(
                            json.dumps({'result': 'bad', 'message': 'El Nombre del Test ya existe'}),
                           content_type="application/json")

                    test=Test(titulo=elimina_tildes(request.POST['titulo']).upper(),descripcioncorta=elimina_tildes(request.POST['descripcioncorta']).upper(),
                         minutofin=int(request.POST['tiempofinalizacion']),observacion=elimina_tildes(request.POST['observacion']).upper(),
                         fecha=datetime.now(),estado=True,encuesta=esencuesta)

                    test.save()

                    data['result'] = 'ok'
                    return HttpResponse(json.dumps(data),content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}),content_type="application/json")

            elif action == 'edittest':
                try:
                    data = {'title': ''}

                    if (str(request.POST['esencuesta']) == 'true'):
                        esencuesta = True
                    else:
                        esencuesta = False

                    tipotest=Test.objects.get(pk=int(int(request.POST['idtest'])))
                    tipotest.titulo=elimina_tildes(request.POST['titulo']).upper()
                    tipotest.descripcioncorta=elimina_tildes(request.POST['descripcioncorta']).upper()
                    tipotest.minutofin=int(request.POST['tiempofinalizacion'])
                    tipotest.observacion = elimina_tildes(request.POST['observacion']).upper()
                    tipotest.encuesta=esencuesta

                    tipotest.save()

                    data['result'] = 'ok'
                    return HttpResponse(json.dumps(data),content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}),content_type="application/json")


            elif action == 'eliminar':
                try:
                    data = {'title': ''}
                    test = Test.objects.get(pk=int(request.POST['idtest']))

                    # if InscripcionTest.objects.filter(test=test
                    #                                ).exists():
                    #     return HttpResponse(
                    #         json.dumps(
                    #             {'result': 'bad', 'message': 'No se puede eliminar el test porque tiene alumnos inscrito'}),
                    #         content_type="application/json")

                    test.delete()
                    data['result'] = 'ok'
                    return HttpResponse(json.dumps(data),content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}),content_type="application/json")

        else:
            data = {'title': 'Test de Ingreso'}
            addUserData(request,data)
            search=None
            if 'action' in request.GET:
                action = request.GET['action']
                if action == 'agregatest':
                    return render(request ,"testingreso/mantenimiento/agregartest.html" ,  data)

                elif action == 'editartest':
                    tipotest = Test.objects.get(pk=int(request.GET['idtest']))
                    data['tipotest']=tipotest
                    return render(request ,"testingreso/mantenimiento/editartest.html" ,  data)

            else:

                if 's' in request.GET:
                    search = request.GET['s']
                    listadoTest = Test.objects.filter(titulo__contains=search).order_by("titulo")
                else:
                    listadoTest = Test.objects.filter().order_by("titulo")

                data['search'] = search if search else ""
                data['listadoTest'] = listadoTest

                return render(request ,"testingreso/testingresobs.html" ,  data)
    except Exception as e:
        return HttpResponseRedirect("/testingreso")
