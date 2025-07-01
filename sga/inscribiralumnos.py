import json
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from sga.cita import MiPaginador
from sga.commonviews import addUserData
from sga.models import  Test, InscripcionTestIngreso, Persona, Inscripcion, PreguntaTestIngreso, RespuestaInscripcionTest, ConclusionesTest
from datetime import datetime


@login_required(redirect_field_name='ret', login_url='/login')

def view(request):
    if request.method == 'POST':
        action = request.POST['action']

        if action == 'alumnos':
            try:
                ss = request.POST['q'].split(' ')
                while '' in ss:
                    ss.remove('')
                if len(ss) == 1:

                    persona = Persona.objects.filter(Q(cedula__icontains=request.POST['q']) | Q(
                        pasaporte__icontains=request.POST['q']) | Q(
                        nombres__icontains=request.POST['q']) | Q(
                        apellido1__icontains=request.POST['q']) | Q(
                        apellido2__icontains=request.POST['q']),usuario__is_active=True).order_by(
                        'apellido1',
                        'apellido2')
                else:

                    persona = Persona.objects.filter(
                        Q(pellido1__icontains=ss[0]) & Q(
                            apellido2__icontains=ss[1]), usuario__is_active=True).order_by(
                        'apellido1',
                        'apellido2')


                persona=persona.filter(id__in=Inscripcion.objects.filter(persona__id__in=persona.filter().values_list('id',flat=True)).values('persona_id'))

                paging = MiPaginador(persona, 30)
                p = 1
                try:
                    if 'page' in request.POST:
                        p = int(request.POST['page'])
                    page = paging.page(p)
                except:
                    page = paging.page(p)

                lista = [{"id": d.id, "nombre": str(d)} for d in
                         page.object_list]

                return HttpResponse(json.dumps({'result': 'ok', 'items': lista, 'page': p}),
                                    content_type="application/json")

            except Exception as ex:
                return HttpResponse(json.dumps({"result": "bad", "message": ex}), content_type="application/json")


        if action == 'agregarasignacionalumno':
            try:
                data = {'title': ''}
                test= Test.objects.get(pk=int(request.POST['idtest']))
                fechahoy = datetime.now()

                if not InscripcionTestIngreso.objects.filter(test=test,persona__id=int(request.POST['idalumno'])).exists():

                    inscriptest=InscripcionTestIngreso(persona_id=int(request.POST['idalumno']),fecha=fechahoy.date(),estado=True,test=test)
                    inscriptest.save()

                else:
                    inscriptest=InscripcionTestIngreso.objects.filter(persona__id=int(request.POST['idalumno']),estado=True,test=test)[:1].get()
                    inscriptest.fechainicio=fechahoy.now()
                    inscriptest.save()


                data['result'] = 'ok'
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}), content_type="application/json")

        elif action == 'eliminar':
            try:
                data = {'title': ''}
                inscrptest = InscripcionTestIngreso.objects.get(pk=int(request.POST['idinscr']))
                inscrptest.delete()
                data['result'] = 'ok'
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}), content_type="application/json")





    else:
        data = {'title': 'Alumnos Inscrito Test '}
        addUserData(request, data)
        test= Test.objects.get(pk=int(request.GET['idtest']))
        data['test'] = test
        search=None


        if 'action' in request.GET:
            action = request.GET['action']

            if action == 'vertest':

                inscripciondata = InscripcionTestIngreso.objects.get(pk=int(request.GET['id']))

                data['inscripciondata'] = inscripciondata

                # buscar las preguntas que pertene al test
                listapreguntas = PreguntaTestIngreso.objects.filter(testingreso=inscripciondata.test).order_by('orden')
                data['listapreguntas'] = listapreguntas


                # buscar las respuesta de la inscripcion
                data['cantidadrespuestaenviada']=RespuestaInscripcionTest.objects.filter(inscripciontest=inscripciondata).count()
                data['listarespuesta'] = RespuestaInscripcionTest.objects.filter(inscripciontest=inscripciondata).order_by('orden')
                data['listatablaconclu'] = ConclusionesTest.objects.filter(test=inscripciondata.test).order_by('id')
                # data['listadopuntajetest']=PuntajesTest.objects.filter(estado=True)



                return render(request ,"testingreso/consulta/vertest.html" ,  data)




        else:
            try:

                if 's' in request.GET:
                    search = str(request.GET['s']).upper()
                    listadoalumnosinscrito = InscripcionTestIngreso.objects.filter(Q(persona__nombres__icontains=search) | Q(persona__apellido1__icontains=search) | Q(
                                    persona__apellido2__icontains=search) |Q(persona__cedula__icontains=search) | Q(
                        persona__pasaporte__icontains=search),estado=True).order_by("id")
                else:
                    listadoalumnosinscrito = InscripcionTestIngreso.objects.filter().order_by("id")


                listadoalumnosinscrito=listadoalumnosinscrito.filter(test=test)


                paging = MiPaginador(listadoalumnosinscrito, 25)
                p = 1
                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                    page = paging.page(p)
                except:
                    page = paging.page(1)

                data['paging'] = paging
                data['rangospaging'] = paging.rangos_paginado(p)
                data['page'] = page

                data['search'] = search if search else ""
                data['listadoalumnosinscrito'] = page.object_list
                data['totalinscrito'] = listadoalumnosinscrito.count()
                now = datetime.now()
                data['fechaDesdeD'] = now.strftime("%Y-%m-%d")
                data['fechaHastaH'] = now.strftime("%Y-%m-%d")

                return render(request ,"testingreso/consulta/alumnosinscritotestbs.html" ,  data)
            except Exception as ex:
                print(ex)
                return render(request ,"/panel" ,  data)