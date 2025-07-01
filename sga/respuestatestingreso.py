import json
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from sga.commonviews import addUserData
from sga.models import PreguntaTest, RespuestaTestIngreso, PreguntaTestIngreso


@login_required(redirect_field_name='ret', login_url='/login')

def view(request):
    if request.method == 'POST':
        action = request.POST['action']


        if action == 'agregarrespuesta':
            try:
                data = {'title': ''}

                preguntatest=PreguntaTestIngreso.objects.get(pk=int(request.POST['idpregunta']))


                if (str(request.POST['actualizacionsistema']) == 'true'):
                    actualizacionsistema=True
                else:
                    actualizacionsistema = False


                if (str(request.POST['respuestacorrecta']) == 'true'):
                    respuestacorrecta=True
                else:
                    respuestacorrecta = False

                respuesta=RespuestaTestIngreso(respuesta=str(request.POST['respuestas']),
                     test=preguntatest.testingreso,pregunta=preguntatest,orden=int(request.POST['orden']),
                                        atualizacion=actualizacionsistema,estado=True,puntaje=float(request.POST['puntaje']),
                                        respuestacorrecta=respuestacorrecta)


                if "filerchivoarchivoimagen" in request.FILES:
                    respuesta.imagen=request.FILES["filerchivoarchivoimagen"]
                respuesta.save()


                data['result'] = 'ok'
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}), content_type="application/json")


        if action == 'editarrespuestas':
            try:
                data = {'title': ''}

                respuestatest=RespuestaTestIngreso.objects.get(pk=int(request.POST['idrespuesta']))




                if (str(request.POST['actualizacionsistema']) == 'true'):
                    actualizacionsistema=True
                else:
                    actualizacionsistema = False

                respuestatest.respuesta=str(request.POST['respuestas'])
                respuestatest.orden=int(request.POST['orden'])
                respuestatest.puntaje=float(request.POST['puntaje'])
                respuestatest.atualizacion=actualizacionsistema

                if "filerchivoarchivoimagen" in request.FILES:
                    respuestatest.imagen=request.FILES["filerchivoarchivoimagen"]

                respuestatest.save()


                data['result'] = 'ok'
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}), content_type="application/json")


        elif action == 'eliminar':
            try:
                data = {'title': ''}
                respuesta = RespuestaTestIngreso.objects.get(pk=int(request.POST['idrespuesta']))
                respuesta.delete()
                data['result'] = 'ok'
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}), content_type="application/json")




    else:
        data = {'title': 'Listado de Respuesta '}
        addUserData(request, data)
        search=None
        preguntatest=PreguntaTestIngreso.objects.get(pk=int(int(request.GET['idpregunta'])))
        data['preguntatest']=preguntatest


        if 'action' in request.GET:
            action = request.GET['action']


            if action == 'agregarespuesta':


                return render(request ,"testingreso/mantenimiento/agregarrespuesta.html" ,  data)


            elif action == 'editrespuesta':

                respuestatest = RespuestaTestIngreso.objects.get(pk=int(request.GET['idrespuesta']))
                data['respuestatest'] = respuestatest

                return render(request ,"testingreso/mantenimiento/editarrespuestas.html" ,  data)


        else:
            try:

                if 's' in request.GET:
                    search = str(request.GET['s']).upper()
                    listadorespuesta = RespuestaTestIngreso.objects.filter(respuesta__contains=search,pregunta=preguntatest).order_by("orden")
                else:
                    listadorespuesta = RespuestaTestIngreso.objects.filter(pregunta=preguntatest).order_by("orden")

                data['search'] = search if search else ""
                data['listadorespuesta'] = listadorespuesta

                return render(request ,"testingreso/mantenimiento/respuestatestbs.html" ,  data)
            except Exception as ex:
                print(ex)
                return render(request ,"/panel" ,  data)
