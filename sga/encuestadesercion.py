import json
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from sga.commonviews import addUserData
from sga.models import Test, Inscripcion, InscripcionTestIngreso, PreguntaTestIngreso, RespuestaInscripcionTest, RespuestaTestIngreso, elimina_tildes, SolicitudEstudiante, RubroEspecieValorada, Matricula, Periodo
from datetime import datetime


def view(request):
    if request.method == 'POST':
        action = request.POST['action']

        if action == 'guardarpreguntaseleccion':

            try:

                data = {'title': ''}
                inscriptest=InscripcionTestIngreso.objects.get(pk=request.POST['idinscripciontest'])
                # obtengo la preguntas
                preguntadata = PreguntaTestIngreso.objects.get(pk=int(request.POST['idpregunta']))
                #guardar respuestas del alumno
                if  RespuestaInscripcionTest.objects.filter(inscripciontest=inscriptest,
                                                                            pregunta=preguntadata).exists():
                    guardarrespuesta = RespuestaInscripcionTest.objects.filter(inscripciontest=inscriptest,
                                                                                pregunta=preguntadata)
                    guardarrespuesta.delete()

                if not RespuestaInscripcionTest.objects.filter(inscripciontest=inscriptest,
                                                               pregunta=preguntadata,orden=int(request.POST['idordenrespuesta'])).exists():
                    guardarrespuesta=RespuestaInscripcionTest(inscripciontest=inscriptest,
                                                             respuesta=elimina_tildes(request.POST['respuesta']).lower(),puntaje=float(0),pregunta=preguntadata,orden=int(request.POST['idordenrespuesta']))

                    guardarrespuesta.save()

                data['result'] = 'ok'
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as ex:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(ex)}), content_type="application/json")


        elif action == 'validarrespuestacontestada':
            try:
                data = {'title': ''}

                inscriptest=InscripcionTestIngreso.objects.filter(pk=int(request.POST['idinscriptest']))[:1].get()

                listapreguna=PreguntaTestIngreso.objects.filter(testingreso=inscriptest.test).order_by('orden')

                # preguntar si todas las respuesta pertenecientes a esa area fueron contestadas caso contrario no permitir avanzar

                for xlistapreguna in listapreguna:

                    if not RespuestaInscripcionTest.objects.filter(inscripciontest=inscriptest,pregunta=xlistapreguna).exists():
                        return HttpResponse(json.dumps({'result': 'bad', 'message': str('Debe contestar la pregunta ')+str(xlistapreguna.orden) +'.-'+str(xlistapreguna.pregunta)}),
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
                       guardarrespuesta.respuesta=elimina_tildes(xlistarespuestas['valorrespuesta'])
                       guardarrespuesta.orden=int(xlistarespuestas['idordenrespuesta'])


                   guardarrespuesta.save()




                inscriptest.horafin=fechahoy.now()
                if int(request.POST['segundos'])<9:
                    segundo ="0"+str(request.POST['segundos'])
                else:
                    segundo = str(request.POST['segundos'])


                inscriptest.horafincronometro=str(request.POST['minutos']).strip()+":"+str(segundo).strip()
                inscriptest.puntaje=0
                inscriptest.save()

                data['result'] = 'ok'
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as ex:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(ex)}), content_type="application/json")





    else:

        data = {'title': 'Encuesta Itb'}
        addUserData(request, data)

        if 'action' in request.GET:
            action = request.GET['action']
            if action=='verencuesta':
                try:
                    especie = RubroEspecieValorada.objects.get(rubro_id=int(request.GET['especie']))
                    encuesta=InscripcionTestIngreso.objects.filter(rubroespecie=especie.rubro_id,persona=especie.rubro.inscripcion.persona)[:1].get()
                    data['inscripciondata'] = encuesta

                    # buscar las preguntas que pertene al test
                    listapreguntas = PreguntaTestIngreso.objects.filter(testingreso=encuesta.test).order_by('orden')
                    data['listapreguntas'] = listapreguntas


                    # buscar las respuesta de la inscripcion
                    data['cantidadrespuestaenviada']=RespuestaInscripcionTest.objects.filter(inscripciontest=encuesta).count()
                    data['listarespuesta'] = RespuestaInscripcionTest.objects.filter(inscripciontest=encuesta).order_by('orden')



                    return render(request,'encuestaitb/verencuestadesercion.html', data)

                except Exception as ex:
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(ex)}), content_type="application/json")



        else:


            persona=data['persona']
            fechahoy = datetime.now()
            realizartest = Test.objects.get(pk=int(request.GET['idtest']),estado=True)
            data['realizartest'] = realizartest
            inscrip=Inscripcion.objects.get(persona=persona)
            data['datainscripcion']=Inscripcion.objects.get(persona=persona)

            # buscar las preguntas que pertence al test
            listapreguntas=PreguntaTestIngreso.objects.filter(testingreso=realizartest).order_by('orden')

            data['listapreguntas'] = listapreguntas

            grupo=0
            if inscrip.matricula():
                grupo=inscrip.matricula().nivel.grupo_id
            else:
                matriculaant = Matricula.objects.filter(Q(nivel__cerrado=True) | Q(liberada=True),inscripcion = inscrip).order_by('-fecha')[:1].get()
                grupo=matriculaant.nivel.grupo_id

            if not InscripcionTestIngreso.objects.filter(test=realizartest,persona__id=int(request.GET['idalumno']),grupo=grupo).exists():

                inscriptest=InscripcionTestIngreso(persona_id=int(request.GET['idalumno']),fecha=fechahoy.date(),estado=True,test=realizartest,grupo=grupo)
                inscriptest.save()

            else:
                inscriptest=InscripcionTestIngreso.objects.filter(persona__id=int(request.GET['idalumno']),estado=True,test=realizartest,grupo=grupo)[:1].get()
                inscriptest.fechainicio=fechahoy.now()
                inscriptest.save()

            data['inscriptest'] = inscriptest
            data['persona'] = persona



            return render(request,"encuestaitb/encuestadesercionitbbs.html", data)
