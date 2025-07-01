from datetime import datetime
import json
from decimal import Decimal

from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template import RequestContext
# from requests.packages.urllib3 import request
from sga.commonviews import addUserData
from sga.models import PreguntasEvaluacion, RespuestasEjesEvaluacion, EvaluacionCargoPeriodo, DetalleEvaluacionCargo, elimina_tildes, DetalleEvaluacionPregunta, EjesEvaluacion, PeriodoEvaluacion, EvaluacionDocente, Persona, Coordinacion, EvaluacionCoordinadorDocente


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
def view(request):
    if request.method=='POST':

        if 'action' in request.POST:
            action = request.POST['action']
            if action == 'evaluarpregunta':

                try:
                    pregunta = PreguntasEvaluacion.objects.filter(pk=request.POST['pregid'])[:1].get()
                    respuesta = RespuestasEjesEvaluacion.objects.filter(pk=request.POST['respid'])[:1].get()
                    evaluacionprofesor = EvaluacionCargoPeriodo.objects.filter(id=request.POST['evaluacioncoordinador'])[:1].get()
                    if DetalleEvaluacionCargo.objects.filter(pregunta=pregunta,evaluacion=evaluacionprofesor).exists():


                        detalleeval=DetalleEvaluacionCargo.objects.filter(pregunta=pregunta,evaluacion=evaluacionprofesor)[:1].get()
                        print(23)
                        if request.POST['val'] == 'true':
                            print(90)
                            detalleeval.respuesta=respuesta
                            detalleeval.fecha=datetime.now()

                        else:
                            detalleeval.respuesta = None
                            detalleeval.fecha = datetime.now()
                        detalleeval.save()
                        print('guarda')
                    return HttpResponse(json.dumps({'result': 'ok'}),
                                    content_type="application/json")

                except Exception as e:
                    msn = str(e)
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(msn)}), content_type="application/json")

            if action == 'finalizar':
                try:
                    evaluacioncargo = EvaluacionCargoPeriodo.objects.filter(id=request.POST['evaluacioncargo'])[:1].get()
                    if DetalleEvaluacionCargo.objects.filter(evaluacion=evaluacioncargo,respuesta=None).exists():
                        eje=DetalleEvaluacionCargo.objects.filter(evaluacion=evaluacioncargo, respuesta=None).order_by('pregunta__eje')[:1].get().pregunta.eje
                        return HttpResponse(json.dumps({'result': 'bad', 'message': 'No ha respondido todas las preguntas del eje ' + elimina_tildes(eje.descripcion),'eje':str(eje.id)}),                            content_type="application/json")
                    evaluacioncargo.finalizado=True
                    evaluacioncargo.fechafinaliza=datetime.now()
                    calificacion = DetalleEvaluacionCargo.objects.filter(evaluacion=evaluacioncargo).aggregate(total_puntaje=Sum('respuesta__respuesta__puntaje'))['total_puntaje']

                    calificacion = Decimal(calificacion).quantize(Decimal(10) ** -0)
                    evaluacioncargo.calificacion=calificacion

                    evaluacioncargo.save()
                    return HttpResponse(json.dumps({'result': 'ok'}),
                                    content_type="application/json")

                except Exception as e:
                    msn = str(e)
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(msn)}), content_type="application/json")
    else:
        data = {'title': 'Evaluacion Docentes'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action == 'verevaluaciondecano':
                try:
                    search = None
                    data['title'] = 'Ver Evaluacion'
                    personas=None
                    if EvaluacionDocente.objects.filter(id=request.GET['id']).exists():
                        evaluaciondocente=EvaluacionDocente.objects.get(id=request.GET['id'])
                        periodos=PeriodoEvaluacion.objects.filter(evaluaciondoc=evaluaciondocente)
                        data['periodos']=periodos
                        data['evaluaciondocente']=evaluaciondocente
                        if 'per' in request.GET:
                            periodoeval=PeriodoEvaluacion.objects.filter(pk=request.GET['per'])[:1].get()
                            data['pereval']=periodoeval
                            if Coordinacion.objects.filter(persona__usuario=request.user).exists():
                                coordinacion = Coordinacion.objects.filter(persona__usuario=request.user, estado=True)[:1].get()
                                carrerascoord = coordinacion.fun_carrera().values('id')

                                if EvaluacionCoordinadorDocente.objects.filter(coordinador__carrera__id__in =carrerascoord,evaluacion__periodo=periodoeval.periodo).exists():
                                    if EvaluacionCoordinadorDocente.objects.filter(coordinador__carrera__id__in =carrerascoord,evaluacion__periodo=periodoeval.periodo).exists():
                                        evacor=EvaluacionCoordinadorDocente.objects.filter(coordinador__carrera__id__in =carrerascoord,evaluacion__periodo=periodoeval.periodo).values('coordinador__persona__id')

                                        personas=Persona.objects.filter(id__in=evacor).distinct('apellido1', 'apellido2', 'cedula', 'nombres')
                                        data['decanosevaluacion']=personas

                                else:
                                    print('error')

                        # data['acc'] = request.GET['acc']

                            if 's' in request.GET:
                                search = request.GET['s']
                                if search:
                                    ss = search.split(' ')
                                    while '' in ss:
                                        ss.remove('')
                                    if len(ss) == 1:
                                        personas = personas.filter(
                                            Q(nombres__icontains=search) | Q(apellido1__icontains=search) | Q(
                                                apellido2__icontains=search) | Q(cedula__icontains=search) | Q(
                                                pasaporte__icontains=search) | Q(
                                                usuario__username__icontains=search),
                                            usuario__is_active=True).order_by('apellido1')
                                    else:
                                        personas = personas.filter(Q(apellido1__icontains=ss[0]) & Q(
                                            apellido2__icontains=ss[1]),
                                                                                 usuario__is_active=True).order_by(
                                            'apellido1',
                                            'apellido2', 'nombres')
                            if personas:
                                paging = MiPaginador(personas, 30)
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
                                data['personas'] = page.object_list

                    return render(request,"evaluacionesdirectivo/coordinadores.html", data)
                except Exception as e:
                    print(e)
                    return HttpResponseRedirect("/evaluacionesdirectivo")
            if action == 'verevaluacionesdecanos':

                try:
                    if Coordinacion.objects.filter(persona__usuario=request.user).exists():
                        coordinacion = Coordinacion.objects.filter(persona__usuario=request.user)[:1].get()
                        carrerascoord = coordinacion.fun_carrera().values('id')
                        if EvaluacionCoordinadorDocente.objects.filter(coordinador__carrera__id__in =carrerascoord).exists():
                            evacor=EvaluacionCoordinadorDocente.objects.filter(coordinador__carrera__id__in =carrerascoord).values('coordinador__persona__id')
                            percor=Persona.objects.filter(id__in=evacor)
                            # periodocor=EvaluacionCoordinadorDocente.objects.filter(coordinador__carrera__id__in =carrerascoord).values('evaluacion__evaluaciondoc__id')
                            data['periodocor']=EvaluacionDocente.objects.filter(estado=True, directivo=True).order_by('descripcion')

                            paging = MiPaginador(percor, 30)
                            p = 1

                            try:
                                if 'page' in request.GET:
                                    p = int(request.GET['page'])
                                page = paging.page(p)
                                print(5)
                            except:
                                page = paging.page(p)
                                print(4)
                            data['paging'] = paging
                            data['rangospaging'] = paging.rangos_paginado(p)
                            data['page'] = page
                            # data['search'] = search if search else ""
                            # data['form'] = AreasElementosEvaluacionForm()
                            data['percor'] = page.object_list

                            if 'error' in request.GET:
                                data['error']= request.GET['error']

                    return render(request,"evaluacionesdirectivo/evaluaciondecano.html", data)

                except Exception as e:
                    print(e)
                    return HttpResponseRedirect("/evaluaciondecano")

            if action=='evaluardecano':
                try:
                    persona=Persona.objects.filter(usuario=request.user)[:1].get()
                    personaevaluada=Persona.objects.get(pk=request.GET['per'])

                    if PeriodoEvaluacion.objects.filter(pk=request.GET['periodo']).exists():
                        periodoeval=PeriodoEvaluacion.objects.filter(pk=request.GET['periodo'])[:1].get()

                        if EvaluacionDocente.objects.filter(pk=request.GET['id']).exists():
                            evadi=EvaluacionDocente.objects.filter(pk=request.GET['id'])[:1].get()
                            evaluacion=EvaluacionDocente.objects.filter(directivocargo=True,estado=True)[:1].get()
                            print(evaluacion.id)

                            if EvaluacionCargoPeriodo.objects.filter(personaevalua=persona,personaevaluada=personaevaluada,evaluaciondocente=periodoeval).exists():

                                evaluacioncargo=EvaluacionCargoPeriodo.objects.filter(personaevalua=persona,personaevaluada=personaevaluada,evaluaciondocente=periodoeval)[:1].get()
                                print(34322)
                            else:
                                evaluacioncargo=EvaluacionCargoPeriodo(personaevalua=persona,personaevaluada=personaevaluada,evaluaciondocente=periodoeval,fecha=datetime.now())
                                evaluacioncargo.save()

                                for e in DetalleEvaluacionPregunta.objects.filter(evaluacion=evaluacion):
                                    if not DetalleEvaluacionCargo.objects.filter(evaluacion=evaluacioncargo,pregunta=e.pregunta).exists() and not evaluacioncargo.finalizado:
                                        d = DetalleEvaluacionCargo(evaluacion=evaluacioncargo,pregunta=e.pregunta)
                                        d.save()
                            ejes=DetalleEvaluacionPregunta.objects.filter(evaluacion=evaluacion).values('eje')
                            data['ejes'] = EjesEvaluacion.objects.filter(id__in=ejes).order_by('id')
                            data['evaluacioncargo'] = evaluacioncargo

                            data['evaluaciondoc'] = evaluacion
                            data['evadi'] = evadi
                            print(evaluacion.id)
                            print(evadi.id)
                            data['periodoeval'] = periodoeval

                            data['evaluacion'] = True
                            data['persona'] = persona
                            data['personaevaluada'] = personaevaluada
                            return render(request,'evaluacionesdirectivo/evaluarcoordinadordecano.html', data)
                except Exception as e:
                    print(e)
        else:
            try:

                if Coordinacion.objects.filter(persona__usuario=request.user).exists():
                    coordinacion = Coordinacion.objects.filter(persona__usuario=request.user,id=3)[:1].get()
                    carrerascoord = coordinacion.fun_carrera().values('id')
                    if EvaluacionCoordinadorDocente.objects.filter(coordinador__carrera__id__in =carrerascoord).exists():
                        evacor=EvaluacionCoordinadorDocente.objects.filter(coordinador__carrera__id__in =carrerascoord).values('coordinador__persona__id')
                        percor=Persona.objects.filter(id__in=evacor)
                        # periodocor=EvaluacionCoordinadorDocente.objects.filter(coordinador__carrera__id__in =carrerascoord).values('evaluacion__evaluaciondoc__id')
                        data['periodocor']=EvaluacionDocente.objects.filter(estado=True, directivocargo=True).order_by('descripcion')

                        paging = MiPaginador(percor, 30)
                        p = 1

                        try:
                            if 'page' in request.GET:
                                p = int(request.GET['page'])
                            page = paging.page(p)
                            print(5)
                        except:
                            page = paging.page(p)
                            print(4)
                        data['paging'] = paging
                        data['rangospaging'] = paging.rangos_paginado(p)
                        data['page'] = page
                        # data['search'] = search if search else ""
                        # data['form'] = AreasElementosEvaluacionForm()
                        data['percor'] = page.object_list

                        if 'error' in request.GET:
                            data['error']= request.GET['error']

                    return render(request,"evaluacionesdirectivo/evaluaciondecano.html", data)
                else:
                    return HttpResponseRedirect("/evaluaciondecano?error=error")

            except Exception as e:
                print (e)
                return HttpResponseRedirect("/encuestaevaluacion")