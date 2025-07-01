import json
from django.http import HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from sga.commonviews import addUserData
from sga.models import Test, PreguntaTest, PreguntaTestIngreso, elimina_tildes, AreaDominioAcademico, DominiosAcademicos


def view(request):
    if request.method == 'POST':
        action = request.POST['action']
        if action == 'agregarpregunta':
            try:
                data = {'title': ''}

                if PreguntaTestIngreso.objects.filter(
                        pregunta=elimina_tildes(request.POST['pregunta']).upper()).exists():
                    return HttpResponse(
                        json.dumps({'result': 'bad', 'message': 'La pregunta  ya existe'}),
                        content_type="application/json")

                if (str(request.POST['cajatext']) == 'true'):
                    cajatext = True
                else:
                    cajatext = False

                if (str(request.POST['cajatextleyenda']) == 'true'):
                    cajatextleyenda = True
                else:
                    cajatextleyenda = False

                if (str(request.POST['cmbobox']) == 'true'):
                    cmbobox = True
                else:
                    cmbobox = False

                if (str(request.POST['txtfecha']) == 'true'):
                    txtfecha = True
                else:
                    txtfecha = False


                if (str(request.POST['marquesina']) == 'true'):
                    marquesina = True
                else:
                    marquesina = False

                if (str(request.POST['checkbox']) == 'true'):
                    checkbox = True
                else:
                    checkbox = False

                if (str(request.POST['radiocheck']) == 'true'):
                    radiocheck = True
                else:
                    radiocheck = False


                if (str(request.POST['arrastrar']) == 'true'):
                    arrastrar = True
                else:
                    arrastrar = False


                pregunta=PreguntaTestIngreso(pregunta=elimina_tildes(request.POST['pregunta']).upper(),
                     testingreso_id=int(request.POST['idtest']),orden=int(request.POST['orden']),
                     estado=True,descripcion=elimina_tildes(request.POST['descripcioncorta']).upper(),cantidadrespuesta=int(request.POST['numerorespuesta']),
                                      cajatexto=cajatext,combobox=cmbobox,fecha=txtfecha,marquesina=marquesina,checkbox=checkbox,arrastarsoltar=arrastrar,
                                      cajatextoleyenda=cajatextleyenda,radiobox=radiocheck,dominio_id=request.POST['dominio']
                                       )

                if "filerchivoarchivoimagen" in request.FILES:
                    pregunta.imagen==request.FILES["filerchivoarchivoimagen"]

                pregunta.save()

                data['result'] = 'ok'
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}), content_type="application/json")


        if action == 'editarpregunta':
            try:
                data = {'title': ''}

                pregunta=PreguntaTestIngreso.objects.get(pk=int(request.POST['idpregunta']))
                pregunta.pregunta=elimina_tildes(request.POST['pregunta']).upper()
                pregunta.orden=int(request.POST['orden'])
                pregunta.descripcion=elimina_tildes(request.POST['descripcioncorta']).upper()
                pregunta.dominioacademico_id=request.POST['dominio']

                if (str(request.POST['cajatext']) == 'true'):
                    cajatext = True
                else:
                    cajatext = False

                if (str(request.POST['cajatextleyenda']) == 'true'):
                    cajatextleyenda = True
                else:
                    cajatextleyenda = False

                if (str(request.POST['cmbobox']) == 'true'):
                    cmbobox = True
                else:
                    cmbobox = False

                if (str(request.POST['txtfecha']) == 'true'):
                    txtfecha = True
                else:
                    txtfecha = False


                if (str(request.POST['marquesina']) == 'true'):
                    marquesina = True
                else:
                    marquesina = False

                if (str(request.POST['checkbox']) == 'true'):
                    checkbox = True
                else:
                    checkbox = False

                if (str(request.POST['radiocheck']) == 'true'):
                    radiocheck = True
                else:
                    radiocheck = False

                if (str(request.POST['arrastrar']) == 'true'):
                    arrastrar = True
                else:
                    arrastrar = False



                pregunta.cajatexto=cajatext
                pregunta.cajatextoleyenda=cajatextleyenda
                pregunta.combobox=cmbobox
                pregunta.fecha=txtfecha
                pregunta.marquesina=marquesina
                pregunta.checkbox=checkbox
                pregunta.radiobox=radiocheck
                pregunta.arrastarsoltar=arrastrar
                pregunta.cantidadrespuesta=int(request.POST['numerorespuesta'])



                if "filerchivoarchivoimagen" in request.FILES:
                    pregunta.imagen=request.FILES["filerchivoarchivoimagen"]

                pregunta.save()

                data['result'] = 'ok'
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}), content_type="application/json")


        elif action == 'eliminar':
            try:
                data = {'title': ''}
                pregunta = PreguntaTestIngreso.objects.get(pk=int(request.POST['idpregunta']))
                # if RespuestaInscripcionTest.objects.filter(pregunta=pregunta
                #                                ).exists():
                #     return HttpResponse(
                #         json.dumps(
                #             {'result': 'bad', 'message': 'No se puede eliminar porque tiene respuesta de los estudiantes'}),
                #         content_type="application/json")

                pregunta.delete()
                data['result'] = 'ok'
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}), content_type="application/json")


        elif  action=='add_dominioacademico':
            try:
                result = {}
                if DominiosAcademicos.objects.filter(pk=request.POST['id']).exists():
                    dominio = DominiosAcademicos.objects.get(pk=request.POST['id'])
                    dominio.nombre = request.POST['nombre']
                    dominio.area_id = request.POST['area']
                    dominio.save()
                else:
                    dominio = DominiosAcademicos(nombre=request.POST['nombre'],
                                        area_id=request.POST['area'])
                    dominio.save()
                # result['listproducto'] = [{"id": producto.id, "producto": str(producto)} for producto in Producto.objects.filter()]
                result['result'] = 'ok'
                return HttpResponse(json.dumps(result), content_type="application/json")

            except Exception as ex:
                return HttpResponse(json.dumps({'result': 'bad', "error": str(ex)}),content_type="application/json")





    else:
        data = {'title': 'Listado de Preguntas '}
        addUserData(request, data)
        search=None

        test=Test.objects.get(pk=int(int(request.GET['idtest'])))
        data['test']=test

        if 'action' in request.GET:
            action = request.GET['action']

            if action == 'agregapregunta':
                area =AreaDominioAcademico.objects.filter(id=test.id) # depende del area
                data['dominios'] = DominiosAcademicos.objects.filter(area=area).order_by('nombre')

                return render(request ,"testingreso/mantenimiento/agregarpregunta.html" ,  data)

            elif action == 'editpregunta':

                preguntatest = PreguntaTestIngreso.objects.get(pk=int(request.GET['idpregunta']))
                data['preguntatest'] = preguntatest
                area = AreaDominioAcademico.objects.get(id=test.id)  # depende del area
                data['dominios'] = DominiosAcademicos.objects.filter(area=area).order_by('nombre')

                return render(request ,"testingreso/mantenimiento/editarpregunta.html" ,  data)

            elif action =='agregardominio':
                data['dominios']=DominiosAcademicos.objects.filter(area=test.id).order_by('nombre')
                data['tipo']= AreaDominioAcademico.objects.filter()
                return render(request, "testingreso/mantenimiento/dominioacademico.html", data)



        else:
            try:
                if 's' in request.GET:
                    search = str(request.GET['s']).upper()
                    listadopreguntas = PreguntaTestIngreso.objects.filter(testingreso__id=int(request.GET['idtest']),pregunta__contains=search).order_by("orden")
                else:
                    listadopreguntas = PreguntaTestIngreso.objects.filter(testingreso__id=int(request.GET['idtest'])).order_by("orden")



                data['search'] = search if search else ""
                data['listadopreguntas'] = listadopreguntas



                return render(request ,"testingreso/mantenimiento/preguntastestbs.html" ,  data)
            except Exception as ex:
                print(ex)
                return render(request ,"/panel" ,  data)
