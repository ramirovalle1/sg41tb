import json

from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from sga.commonviews import addUserData
from sga.models import Test, PreguntaTestIngreso, RespuestaTestIngreso, InscripcionTestIngreso, \
    RespuestaInscripcionTest, EncuestaItb
from datetime import datetime


def view(request):
    if request.method == 'POST':
        action = request.POST['action']

        if action == 'validarrespuestacontestada':
            try:
                data = {'title': ''}

                inscriptest=InscripcionTestIngreso.objects.filter(pk=int(request.POST['idinscriptest']))[:1].get()

                listapreguna=PreguntaTestIngreso.objects.filter(testingreso=inscriptest.test)

                # preguntar si todas las respuesta pertenecientes a esa area fueron contestadas caso contrario no permitir avanzar

                for xlistapreguna in listapreguna:

                    if not RespuestaInscripcionTest.objects.filter(inscripciontest=inscriptest,pregunta=xlistapreguna).exists():
                        return HttpResponse(json.dumps({'result': 'bad', 'message': str('Para enviar el test debe responder todas las preguntas')}),
                                            content_type="application/json")


                data['result'] = 'ok'
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}), content_type="application/json")


        elif action == 'enviarespuestas':

            try:

                data = {'title': ''}
                fechahoy = datetime.now()
                puntaje = 0
                inscriptest=InscripcionTestIngreso.objects.get(pk=request.POST['idinscripciontest'])
                listarespuestas = json.loads(request.POST['jrespuestas'])

                # buscar si tiene mas de una respuesta por pregunta
                for xlistarespuestas in listarespuestas:
                    # obtengo la preguntas
                    preguntadatantes = PreguntaTestIngreso.objects.get(pk=int(xlistarespuestas['idpregunta']))
                    if  RespuestaInscripcionTest.objects.filter(inscripciontest=inscriptest,pregunta=preguntadatantes,orden=int(xlistarespuestas['idordenrespuesta'])).count()>1:
                        ultimares=RespuestaInscripcionTest.objects.filter(inscripciontest=inscriptest,pregunta=preguntadatantes,orden=int(xlistarespuestas['idordenrespuesta']))[:1].get()
                        ultimares.delete()


                # guardar las respuesta y obtener el puntaje
                for xlistarespuestas in listarespuestas:
                   # obtengo la preguntas
                   preguntadata = PreguntaTestIngreso.objects.get(pk=int(xlistarespuestas['idpregunta']))
                   #guardar respuestas del alumno
                   if not RespuestaInscripcionTest.objects.filter(inscripciontest=inscriptest,pregunta=preguntadata,orden=int(xlistarespuestas['idordenrespuesta'])).exists():
                       guardarrespuesta=RespuestaInscripcionTest(inscripciontest=inscriptest,
                                                                 respuesta=xlistarespuestas['valorrespuesta'],pregunta=preguntadata,orden=int(xlistarespuestas['idordenrespuesta']))
                   else:

                       guardarrespuesta=RespuestaInscripcionTest.objects.filter(inscripciontest=inscriptest,pregunta=preguntadata,orden=int(xlistarespuestas['idordenrespuesta']))[:1].get()
                       guardarrespuesta.respuesta=xlistarespuestas['valorrespuesta']
                       guardarrespuesta.orden=int(xlistarespuestas['idordenrespuesta'])

                   #buscar la respuesta correcta
                   respuestapregunta=RespuestaTestIngreso.objects.get(test=inscriptest.test,pregunta=preguntadata,orden=int(xlistarespuestas['idordenrespuesta']))
                   if str(xlistarespuestas['valorrespuesta']).lower().lstrip().rstrip()==str(respuestapregunta.respuesta).lower():
                       if respuestapregunta.respuestacorrecta:
                            guardarrespuesta.puntaje=respuestapregunta.puntaje
                            puntaje=puntaje+respuestapregunta.puntaje
                       else:
                            guardarrespuesta.puntaje=0

                   else:
                       # Si la respuesta no coincide, establece el puntaje como 0
                       guardarrespuesta.puntaje = 0

                   guardarrespuesta.validada=True
                   guardarrespuesta.save()




                inscriptest.horafin=fechahoy.now()
                if int(request.POST['segundos'])<9:
                    segundo ="0"+str(request.POST['segundos'])
                else:
                    segundo = str(request.POST['segundos'])


                inscriptest.horafincronometro=str(request.POST['minutos']).strip()+":"+str(segundo).strip()
                inscriptest.puntaje=puntaje
                inscriptest.finalizado = True
                inscriptest.save()

                data['result'] = 'ok'
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as ex:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(ex)}), content_type="application/json")


        elif action == 'guardarpreguntaseleccion':

            try:

                data = {'title': ''}
                inscriptest=InscripcionTestIngreso.objects.get(pk=request.POST['idinscripciontest'])
                # obtengo la preguntas
                preguntadata = PreguntaTestIngreso.objects.get(pk=int(request.POST['idpregunta']))
                #guardar respuestas del alumno



                if not RespuestaInscripcionTest.objects.filter(inscripciontest=inscriptest,
                                                               pregunta=preguntadata,orden=int(request.POST['idordenrespuesta'])).exists():
                    guardarrespuesta=RespuestaInscripcionTest(inscripciontest=inscriptest,
                                                             respuesta=request.POST['respuesta'],puntaje=float(request.POST['puntaje']),pregunta=preguntadata,orden=int(request.POST['idordenrespuesta']))
                else:

                    guardarrespuesta = RespuestaInscripcionTest.objects.filter(inscripciontest=inscriptest,
                                                                            pregunta=preguntadata,orden=int(request.POST['idordenrespuesta']))[:1].get()
                    guardarrespuesta.respuesta = request.POST['respuesta']
                    guardarrespuesta.orden = int(request.POST['idordenrespuesta'])

                #buscar la respuesta correcta
                respuestapregunta=RespuestaTestIngreso.objects.get(test=inscriptest.test,pregunta=preguntadata,orden=int(request.POST['idordenrespuesta']))
                if str(request.POST['respuesta']).lower() == str(respuestapregunta.respuesta).lower():
                   if respuestapregunta.respuestacorrecta:
                        guardarrespuesta.puntaje = respuestapregunta.puntaje
                   else:
                        guardarrespuesta.puntaje=0

                guardarrespuesta.save()



                data['result'] = 'ok'
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as ex:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(ex)}), content_type="application/json")


        elif action == 'guardarpreguntaseleccionotra':

            try:

                data = {'title': ''}
                inscriptest=InscripcionTestIngreso.objects.get(pk=request.POST['idinscripciontest'])
                # obtengo la preguntas
                preguntadata = PreguntaTestIngreso.objects.get(pk=int(request.POST['idpregunta']))
                #guardar respuestas del alumno

                if  RespuestaInscripcionTest.objects.filter(inscripciontest=inscriptest,
                                                               pregunta=preguntadata,orden=int(request.POST['idordenrespuesta'])).exists():
                    guardarrespuesta = RespuestaInscripcionTest.objects.filter(inscripciontest=inscriptest,
                                                                            pregunta=preguntadata,orden=int(request.POST['idordenrespuesta']))[:1].get()
                    guardarrespuesta.delete()

                guardarrespuesta=RespuestaInscripcionTest(inscripciontest=inscriptest,
                                                             respuesta=request.POST['respuesta'],puntaje=float(0),pregunta=preguntadata,orden=int(request.POST['idordenrespuesta']))
                guardarrespuesta.save()



                data['result'] = 'ok'
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as ex:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(ex)}), content_type="application/json")

        # se actualiza el tiempo
        elif action == "actualizatime":
            try:
                tiempo = datetime(datetime.now().year,datetime.now().month,datetime.now().day,0,int(request.POST['minut']),int(request.POST['segun']))
                if InscripcionTestIngreso.objects.filter(persona__id=request.POST['idpersona'],test__id = request.POST['id_test']).exists():
                    inscripciontest = InscripcionTestIngreso.objects.filter(persona__id=request.POST['idpersona'],test__id = request.POST['id_test'])[:1].get()
                    inscripciontest.tiempo = tiempo
                    inscripciontest.save()
                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

        elif action =='finaliza':
            try:
                data = {'title': ''}
                listarespuestas = json.loads(request.POST['jrespuestas'])
                fechahoy = datetime.now()
                tiempo = datetime(datetime.now().year, datetime.now().month, datetime.now().day, int(request.POST['minutos']), int(request.POST['segundos']))
                if InscripcionTestIngreso.objects.filter(pk=request.POST['idinscripciontest']).exists():
                    inscriptest = InscripcionTestIngreso.objects.get(pk=request.POST['idinscripciontest'])
                    inscriptest.tiempo = tiempo
                    # inscriptest.finalizado = True
                    puntaje=0
                    if inscriptest.test.id==1: # matematica
                        if RespuestaInscripcionTest.objects.filter(inscripciontest=inscriptest).exists():
                            for r in RespuestaInscripcionTest.objects.filter(inscripciontest=inscriptest):
                                respuestapregunta = RespuestaTestIngreso.objects.get(test=inscriptest.test, pregunta=r.pregunta,orden=r.orden)
                                if str(r.respuesta).lower().lstrip().rstrip() == str(respuestapregunta.respuesta).lower():
                                    if respuestapregunta.respuestacorrecta:
                                        r.puntaje = respuestapregunta.puntaje
                                    else:
                                        r.puntaje = 0
                                else:
                                    r.puntaje = 0

                                r.validada = True
                                r.save()

                        puntaje = RespuestaInscripcionTest.objects.filter(inscripciontest=inscriptest, validada=True).aggregate(Sum('puntaje'))['puntaje__sum']

                    elif inscriptest.test.id ==2: # lenguaje
                        if RespuestaInscripcionTest.objects.filter(inscripciontest=inscriptest).exists():
                            for r in RespuestaInscripcionTest.objects.filter(inscripciontest=inscriptest):
                                if r.pregunta.id == 8 or r.pregunta.id == 9:  # son radiobox y solo necesita una respuesta
                                    resp = RespuestaInscripcionTest.objects.filter(inscripciontest=inscriptest, pregunta=r.pregunta)
                                    if resp.count() > 1:
                                        resp2 = resp.last()
                                        resp2.validada = True
                                        rotra = resp.filter().exclude(id=resp2.id).update(validada=False, puntaje=0)
                                    else:
                                        resp2 = resp.first()

                                    respuestapregunta = RespuestaTestIngreso.objects.get(test=inscriptest.test, pregunta=resp2.pregunta,orden=resp2.orden)

                                    if str(resp2.respuesta).lower().lstrip().rstrip() == str(respuestapregunta.respuesta).lower():
                                        if respuestapregunta.respuestacorrecta:
                                            resp2.puntaje = respuestapregunta.puntaje
                                        else:
                                            resp2.puntaje = 0
                                    else:
                                        resp2.puntaje = 0
                                    resp2.validada = True
                                    resp2.save()
                                else:
                                    respuestapregunta = RespuestaTestIngreso.objects.get(test=inscriptest.test, pregunta=r.pregunta,orden=r.orden)

                                    if str(r.respuesta).lower().lstrip().rstrip() == str(respuestapregunta.respuesta).lower():
                                        if respuestapregunta.respuestacorrecta:
                                            r.puntaje = respuestapregunta.puntaje
                                        else:
                                            r.puntaje = 0
                                    else:
                                        r.puntaje = 0
                                    r.validada = True
                                    r.save()
                        puntaje = RespuestaInscripcionTest.objects.filter(inscripciontest=inscriptest, validada=True).aggregate(Sum('puntaje'))['puntaje__sum']

                    elif inscriptest.test.id==3: #informatica
                        if RespuestaInscripcionTest.objects.filter(inscripciontest=inscriptest).exists():
                            for r in RespuestaInscripcionTest.objects.filter(inscripciontest=inscriptest):
                                resp = RespuestaInscripcionTest.objects.filter(inscripciontest=inscriptest, pregunta=r.pregunta)
                                if resp.count() > 1:
                                    resp2 = resp.last()
                                    resp2.validada = True
                                    rotra = resp.filter().exclude(id=resp2.id).update(validada=False, puntaje=0)
                                else:
                                    resp2 = resp.first()

                                respuestapregunta = RespuestaTestIngreso.objects.get(test=inscriptest.test, pregunta=r.pregunta,
                                                                                     orden=resp2.orden)

                                if str(resp2.respuesta).lower().lstrip().rstrip() == str(respuestapregunta.respuesta).lower():
                                    if respuestapregunta.respuestacorrecta:
                                        resp2.puntaje = respuestapregunta.puntaje
                                    else:
                                        resp2.puntaje = 0
                                else:
                                    resp2.puntaje = 0
                                resp2.validada = True
                                resp2.save()

                        puntaje = RespuestaInscripcionTest.objects.filter(inscripciontest=inscriptest, validada=True).aggregate(Sum('puntaje'))['puntaje__sum']

                        # RespuestaInscripcionTest.objects.filter(inscripciontest=inscriptest).update(validada=True)

                        # guardarrespuesta.validada = True
                    # for xlistarespuestas in listarespuestas:
                    #     # obtengo la preguntas
                    #     preguntadatantes = PreguntaTestIngreso.objects.get(pk=int(xlistarespuestas['idpregunta']))
                    #     # guardar respuestas del alumno
                    #     if RespuestaInscripcionTest.objects.filter(inscripciontest=inscriptest,pregunta=preguntadatantes, orden=int(xlistarespuestas['idordenrespuesta'])).exists():
                    #         guardarrespuesta = RespuestaInscripcionTest.objects.filter(inscripciontest=inscriptest,pregunta=preguntadatantes,orden=int(xlistarespuestas['idordenrespuesta']))[:1].get()
                    #         if xlistarespuestas['valorrespuesta']:
                    #             guardarrespuesta.respuesta = xlistarespuestas['valorrespuesta']
                    #             guardarrespuesta.orden = int(xlistarespuestas['idordenrespuesta'])
                    #
                    #             # buscar la respuesta correcta
                    #             respuestapregunta = RespuestaTestIngreso.objects.get(test=inscriptest.test,pregunta=preguntadatantes, orden=int(xlistarespuestas['idordenrespuesta']))
                    #             if str(xlistarespuestas['valorrespuesta']).lower() == str(respuestapregunta.respuesta).lower():
                    #                 if respuestapregunta.respuestacorrecta:
                    #                     guardarrespuesta.puntaje = respuestapregunta.puntaje
                    #                     puntaje = puntaje + respuestapregunta.puntaje
                    #                 else:
                    #                     guardarrespuesta.puntaje = 0

                    inscriptest.puntaje = puntaje
                    if inscriptest.puntaje == None:
                        inscriptest.puntaje = 0
                    inscriptest.save()


                    inscriptest.horafin=fechahoy.now()
                    if int(request.POST['segundos'])<9:
                        segundo ="0"+str(request.POST['segundos'])
                    else:
                        segundo = str(request.POST['segundos'])


                    inscriptest.horafincronometro=str(request.POST['minutos']).strip()+":"+str(segundo).strip()
                    inscriptest.finalizado = True
                    inscriptest.save()
                data['result'] = 'ok'
                return HttpResponse(json.dumps({"result": "ok"}), content_type="application/json")

            except Exception as ex:
                return HttpResponse(json.dumps({"result": "bad"}), content_type="application/json")

        elif action == 'actualizar_puntaje':
            try:
                data = {'title': ''}
                test = Test.objects.filter(id__in=[1,2,3])
                for t in test:
                    inscripciones = InscripcionTestIngreso.objects.filter(finalizado=True, test=t)
                    if t.id==1: #test matematica
                        for i in inscripciones:
                            if RespuestaInscripcionTest.objects.filter(inscripciontest=i).exists():
                                for r in RespuestaInscripcionTest.objects.filter(inscripciontest=i):
                                    respuestapregunta = RespuestaTestIngreso.objects.get(test=i.test,pregunta=r.pregunta,orden=r.orden)

                                    if str(r.respuesta).lower().lstrip().rstrip() == str(respuestapregunta.respuesta).lower():
                                        if respuestapregunta.respuestacorrecta:
                                            r.puntaje = respuestapregunta.puntaje
                                        else:
                                            r.puntaje = 0
                                    else:
                                        r.puntaje = 0

                                    r.validada=True
                                    r.save()

                            puntaje = RespuestaInscripcionTest.objects.filter(inscripciontest=i, validada=True).aggregate(Sum('puntaje'))['puntaje__sum']
                            if puntaje==None:
                                puntaje=0
                            i.puntaje = puntaje
                            i.save()
                    if t.id==2:
                        for i in inscripciones:
                            if RespuestaInscripcionTest.objects.filter(inscripciontest=i).exists():
                                for r in RespuestaInscripcionTest.objects.filter(inscripciontest=i).order_by('pregunta__id'):
                                    if r.pregunta.id ==8 or r.pregunta.id==9: # son radiobox y solo necesita una respuesta
                                        resp = RespuestaInscripcionTest.objects.filter(inscripciontest=i,pregunta=r.pregunta)
                                        if resp.count() > 1:
                                            resp2 = resp.last()
                                            resp2.validada = True
                                            rotra = resp.filter().exclude(id=resp2.id).update(validada=False, puntaje=0)
                                        else:
                                            resp2 = resp.first()

                                        respuestapregunta = RespuestaTestIngreso.objects.get(test=i.test,pregunta=resp2.pregunta,orden=resp2.orden)

                                        if str(resp2.respuesta).lower().lstrip().rstrip() == str(respuestapregunta.respuesta).lower():
                                            if respuestapregunta.respuestacorrecta:
                                                resp2.puntaje = respuestapregunta.puntaje
                                            else:
                                                resp2.puntaje = 0
                                        else:
                                            resp2.puntaje = 0
                                        resp2.validada = True
                                        resp2.save()
                                    else:
                                        respuestapregunta = RespuestaTestIngreso.objects.get(test=i.test,pregunta=r.pregunta,orden=r.orden)

                                        if str(r.respuesta).lower().lstrip().rstrip() == str(respuestapregunta.respuesta).lower():
                                            if respuestapregunta.respuestacorrecta:
                                                r.puntaje = respuestapregunta.puntaje
                                            else:
                                                r.puntaje = 0
                                        else:
                                            r.puntaje = 0
                                        r.validada = True
                                        r.save()
                            puntaje = RespuestaInscripcionTest.objects.filter(inscripciontest=i, validada=True).aggregate(Sum('puntaje'))['puntaje__sum']
                            i.puntaje = puntaje
                            i.save()
                    if t.id==3: #informatica
                        for i in inscripciones:
                            if RespuestaInscripcionTest.objects.filter(inscripciontest=i).exists():
                                for r in RespuestaInscripcionTest.objects.filter(inscripciontest=i):
                                    resp = RespuestaInscripcionTest.objects.filter(inscripciontest=i,pregunta=r.pregunta)
                                    if resp.count() > 1:
                                        resp2 = resp.last()
                                        resp2.validada = True
                                        rotra = resp.filter().exclude(id=resp2.id).update(validada=False, puntaje=0)
                                    else:
                                        resp2 = resp.first()

                                    respuestapregunta = RespuestaTestIngreso.objects.get(test=i.test,pregunta=r.pregunta,orden=resp2.orden)

                                    if str(resp2.respuesta).lower().lstrip().rstrip() == str(respuestapregunta.respuesta).lower():
                                        if respuestapregunta.respuestacorrecta:
                                            resp2.puntaje = respuestapregunta.puntaje
                                        else:
                                            resp2.puntaje = 0
                                    else:
                                        resp2.puntaje = 0
                                    resp2.validada = True
                                    resp2.save()

                            puntaje = RespuestaInscripcionTest.objects.filter(inscripciontest=i,validada=True).aggregate(Sum('puntaje'))['puntaje__sum']
                            i.puntaje = puntaje
                            i.save()
                # RespuestaInscripcionTest.objects.filter(inscripciontest=i).update(validada=True)

                data['result'] = 'ok'
                return HttpResponse(json.dumps({"result": "ok"}), content_type="application/json")

            except Exception as ex:
                print("error examen")
                print(ex)
                return HttpResponse(json.dumps({"result": "bad"}), content_type="application/json")


    else:
        data = {'title': 'Inscripcion Test '}
        addUserData(request, data)
        search=None
        data['personadado']=data['persona']
        if 'action' in request.GET:
            action = request.GET['action']

            if action == 'realizartest':

                fechahoy = datetime.now()

                realizartest = Test.objects.get(pk=int(request.GET['idtest']),estado=True)
                persona=data['persona']


                # buscar las preguntas que pertene al test
                listapreguntas=PreguntaTestIngreso.objects.filter(testingreso=realizartest).order_by('orden')

                data['listapreguntas'] = listapreguntas

                data['realizartest'] = realizartest
                data['persona'] = persona


                val_tiempo = realizartest.minutofin
                data['val_tiempo']= val_tiempo
                tiempo_asignado = datetime(datetime.now().year, datetime.now().month, datetime.now().day,0,int(val_tiempo))
                if not InscripcionTestIngreso.objects.filter(test=realizartest,persona=persona).exists():
                    inscriptest=InscripcionTestIngreso(persona=persona,fecha=fechahoy.date(),fechainicio=fechahoy.now(),estado=True,test=realizartest)
                    inscriptest.tiempo = tiempo_asignado
                    inscriptest.save()
                    data['segundos'] = '59'
                    minutos_str = str(inscriptest.tiempo.time()).split(":")[1]
                    minutos = int(minutos_str)
                    if minutos <= 0:
                        minutos = 59
                    else:
                        minutos -= 1
                    if minutos < 0:
                        minutos = 59
                    data['minutos'] = str(minutos).zfill(2)

                else:
                    inscriptest=InscripcionTestIngreso.objects.filter(test=realizartest,persona=persona)[:1].get()
                    inscriptest.fechainicio=fechahoy.now()
                    if not inscriptest.tiempo:
                        inscriptest.tiempo = tiempo_asignado
                    if not inscriptest.grupo:
                        inscriptest.grupo= EncuestaItb.objects.get(persona =inscriptest.persona).grupo_id

                    inscriptest.save()
                    data['persona'] = inscriptest.persona
                    # examen
                    data['minutos'] = str(inscriptest.tiempo.time()).split(":")[1]
                    data['segundos'] = str(inscriptest.tiempo.time()).split(":")[2]




                data['inscriptest'] = inscriptest


                return render(request ,"testingreso/proceso/realizartestbs.html" ,  data)








        else:
            try:
                persona_user =request.user
                inscripciontest= InscripcionTestIngreso.objects.filter(persona__usuario=persona_user).values('test')
                listadotestactivoxestudiante= Test.objects.filter(id__in=inscripciontest, estado=True)

                if 's' in request.GET:
                    search = str(request.GET['s']).upper()
                    listadotestactivo = listadotestactivoxestudiante.filter(titulo__contains=search).order_by("id")
                else:
                    listadotestactivo = listadotestactivoxestudiante.filter().order_by("id")

                data['search'] = search if search else ""
                data['listadotestactivo'] = listadotestactivo

                return render(request ,"testingreso/proceso/inscripciontestbs.html" ,  data)
            except Exception as ex:
                print(ex)
                return render(request ,"/panel" ,  data)
