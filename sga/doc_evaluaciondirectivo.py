import json
from datetime import datetime

from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Q

from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from sga.commonviews import addUserData

from sga.models import PreguntasEvaluacion, RespuestasEjesEvaluacion, EvaluacionDocentePeriodo, \
    Profesor, PeriodoEvaluacion, DetalleEvaluacionPregunta, EjesEvaluacion, \
    DetalleEvaluacionDocente, EvaluacionDirectivoPeriodo, CoordinadorCarrera, EvaluacionCoordinadorDocente, EvaluacionDocente, Persona, DetalleEvaluacionDirectivo, CoordinadorCarreraPeriodo


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
                print(2)
                try:
                    pregunta = PreguntasEvaluacion.objects.filter(pk=request.POST['pregid'])[:1].get()
                    respuesta = RespuestasEjesEvaluacion.objects.filter(pk=request.POST['respid'])[:1].get()
                    evaluacionprofesor = EvaluacionDirectivoPeriodo.objects.filter(id=request.POST['evaluacionprofesor'])[:1].get()
                    if DetalleEvaluacionDirectivo.objects.filter(pregunta=pregunta,evaluacion=evaluacionprofesor).exists():
                        print(45)

                        detalleeval=DetalleEvaluacionDirectivo.objects.filter(pregunta=pregunta,evaluacion=evaluacionprofesor)[:1].get()
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
                    evaluaciondire = EvaluacionDirectivoPeriodo.objects.filter(id=request.POST['evaluaciondirectivo'])[:1].get()
                    print(evaluaciondire)
                    if  not evaluaciondire.evaluaciondocenteperiodo.profesor.es_coordinadorperiodo(evaluaciondire.evaluaciondocenteperiodo.periodo):
                         det=DetalleEvaluacionDirectivo.objects.filter(evaluacion=evaluaciondire,respuesta=None).exclude(pregunta__eje__percepcion=True)

                    else:
                        det=DetalleEvaluacionDirectivo.objects.filter(evaluacion=evaluaciondire,respuesta=None)
                    if det :
                        print(4)
                        eje=det.filter().order_by('pregunta__eje')[:1].get().pregunta.eje
                        print(eje)
                        return HttpResponse(json.dumps({'result': 'bad', 'message': 'No ha respondido todas las preguntas del eje ' + str(eje.descripcion),'eje':str(eje.id)}),                            content_type="application/json")
                    evaluaciondire.finalizado=True
                    evaluaciondire.fechafinaliza=datetime.now()
                    evaluaciondire.save()
                    print(3)
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

            if action == 'evaluacioncoordinador':
                try:
                    if not CoordinadorCarreraPeriodo.objects.filter(persona__usuario=request.user).exists():
                        return HttpResponseRedirect("/?erro=No tiene Carrera asignada como coordinador")
                    if CoordinadorCarreraPeriodo.objects.filter(persona__usuario=request.user).exists():
                        data['escoordinador'] = True
                        # evaluacioncor=EvaluacionCoordinadorDocente.objects.filter().values('coordinador__id')
                        cordina=CoordinadorCarreraPeriodo.objects.filter(persona__usuario=request.user)
                        print(cordina)
                        # coord = CoordinadorCarrera.objects.filter(persona__usuario=request.user, id__in=evaluacioncor)[:1].get()
                        # print(coord.carrera)
                        # eva=EvaluacionCoordinadorDocente.objects.filter(id=14)[:1].get()
                        if EvaluacionCoordinadorDocente.objects.filter(coordinador__in=cordina).exists():
                            print(87)
                            evaluaciondoc= EvaluacionCoordinadorDocente.objects.filter(coordinador__in=cordina).distinct('evaluacion__evaluaciondoc').values('evaluacion__evaluaciondoc')
                            print(evaluaciondoc)
                            area = EvaluacionDocente.objects.filter(id__in=evaluaciondoc, estado=True).order_by('descripcion')

                            paging = MiPaginador(area, 30)
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
                            data['area'] = page.object_list

                            if 'error' in request.GET:
                                data['error']= request.GET['error']

                    return render(request ,"evaluacionesdirectivo/evaluacioncoordinador.html" ,  data)

                except Exception as e:
                    print(e)
                    return HttpResponseRedirect("/evaluacioncoordinador")
            if action == 'verevaluacion':
                search = None
                data['title'] = 'Ver Evaluacion'
                coordinadores = CoordinadorCarreraPeriodo.objects.filter().values('persona')
                if EvaluacionDocentePeriodo.objects.filter(evaluaciondocente__id=request.GET['id']).exists():

                    evaluacion = EvaluacionDocente.objects.filter(pk=request.GET['id'])[:1].get()
                    docentesevaluacion = EvaluacionDocentePeriodo.objects.filter(evaluaciondocente=evaluacion)
                    finalizados = docentesevaluacion.filter(finalizado=True).count()

                    pendientes = docentesevaluacion.filter(finalizado=False).count()

                    periodo = EvaluacionDocentePeriodo.objects.filter(evaluaciondocente=evaluacion).distinct(
                        'periodo').values('periodo_id')

                    nomperiodos = EvaluacionDocentePeriodo.objects.filter(evaluaciondocente=evaluacion).distinct(
                        'periodo')

                    # if EvaluacionCargoPeriodo.objects.filter(evaluaciondocente__periodo__id__in=periodo, personaevaluada__usuario=request.user).exists():
                    #     evacargo=EvaluacionCargoPeriodo.objects.filter(evaluaciondocente__periodo__id__in=periodo, personaevaluada__usuario=request.user)[:1].get()
                    #     data['evacargo']=evacargo

                    if CoordinadorCarreraPeriodo.objects.filter(persona__usuario=request.user).exists():
                        print('3333')
                        data['escoordinador'] = True
                        coord = CoordinadorCarreraPeriodo.objects.filter(persona__usuario=request.user).values('id')
                        coordinador = CoordinadorCarreraPeriodo.objects.filter(persona__usuario=request.user)[:1].get()
                        if EvaluacionCoordinadorDocente.objects.filter(coordinador__id__in=coord).exists():
                            profesorescoor= EvaluacionCoordinadorDocente.objects.filter(coordinador__id__in=coord,evaluacion__evaluaciondoc=evaluacion).values('profesor')
                            periodoscoor= EvaluacionCoordinadorDocente.objects.filter(coordinador__id__in=coord,evaluacion__evaluaciondoc=evaluacion).values('evaluacion__periodo')
                            profesores = Profesor.objects.filter(
                                id__in=EvaluacionDocentePeriodo.objects.filter(periodo__id__in=periodoscoor,profesor__id__in=profesorescoor).values('profesor')).order_by('persona__apellido1')
                            repli=profesores.values('id')
                            print(profesores)
                            # replica=ReplicaEvaluacionDirectivoPeriodo.objects.filter(evaluaciondirectivo__evaluaciondocenteperiodo__profesor__id__in=repli,evaluaciondirectivo__evaluaciondocente=evaluacion, activo=True).count()
                            # data['replica']=replica
                            data['periodoscoor']=periodoscoor
                            # if EvaluacionDirectivoPeriodo.objects.filter(finalizado=True, activo=True, evaluaciondocenteperiodo__profesor__id__in=profesores).exists():
                            #     data['evaluado']=EvaluacionDirectivoPeriodo.objects.filter(finalizado=True, activo=True, evaluaciondocenteperiodo__profesor__id__in=profesores)
                    else:

                        profesores = Profesor.objects.filter(id__in=EvaluacionDocentePeriodo.objects.filter(evaluaciondocente=evaluacion).exclude(persona__id__in=coordinadores).values('profesor')).order_by('persona__apellido1')
                else:
                    evaluacion = EvaluacionDocente.objects.filter(pk=request.GET['id'])[:1].get()
                    finalizados = 0
                    pendientes = 0
                    periodo = PeriodoEvaluacion.objects.filter(evaluaciondoc_id=request.GET['id']).distinct('periodo').values('periodo_id')
                    profesores = ""
                    nomperiodos = PeriodoEvaluacion.objects.filter(evaluaciondoc_id=request.GET['id']).distinct('periodo')
                    docentesevaluacion = profesores
                data['periodo'] = periodo
                data['nomperiodo'] = nomperiodos
                data['finalizados'] = finalizados
                data['pendientes'] = pendientes
                data['docentesevaluacion'] = docentesevaluacion
                # data['acc'] = request.GET['acc']
                data['evaluacion'] = evaluacion
                if 's' in request.GET:
                    search = request.GET['s']
                    if search:
                        ss = search.split(' ')
                        while '' in ss:
                            ss.remove('')
                        if len(ss) == 1:
                            profesores = profesores.filter(
                                Q(persona__nombres__icontains=search) | Q(persona__apellido1__icontains=search) | Q(
                                    persona__apellido2__icontains=search) | Q(persona__cedula__icontains=search) | Q(
                                    persona__pasaporte__icontains=search) | Q(
                                    persona__usuario__username__icontains=search),
                                persona__usuario__is_active=True).order_by('persona__apellido1')
                        else:
                            profesores = profesores.filter(Q(persona__apellido1__icontains=ss[0]) & Q(
                                persona__apellido2__icontains=ss[1]),
                                                                     persona__usuario__is_active=True).order_by(
                                'persona__apellido1',
                                'persona__apellido2', 'persona__nombres')
                paging = MiPaginador(profesores, 30)
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
                data['profesores'] = page.object_list

                return render(request ,"evaluacionesdirectivo/profesores.html" ,  data)

            if action == 'verevaluaciondocente':
                try:
                    search = None
                    matricula = None
                    inscripcion = None
                    profesor = Profesor.objects.get(id=request.GET['id'])
                    evaluaciondocente = EvaluacionDocente.objects.filter(pk=request.GET['eva'])[:1].get()
                    if CoordinadorCarreraPeriodo.objects.filter(persona__usuario=request.user).exists():
                        data['escoordinador'] = True

                        coord = CoordinadorCarreraPeriodo.objects.filter(persona__usuario=request.user)
                        print(coord)
                        if EvaluacionCoordinadorDocente.objects.filter(coordinador__in=coord).exists():
                            profesorescoor = EvaluacionCoordinadorDocente.objects.filter(coordinador__in=coord,
                                                                                         evaluacion__evaluaciondoc=evaluaciondocente).values(
                                'profesor')
                            # print(profesorescoor)
                            periodoscoor = EvaluacionCoordinadorDocente.objects.filter(coordinador__in=coord,
                                                                                       evaluacion__evaluaciondoc=evaluaciondocente).values(
                                'evaluacion__periodo')
                            # print(periodoscoor)
                            profesores = Profesor.objects.filter(
                                id__in=EvaluacionDocentePeriodo.objects.filter(periodo__id__in=periodoscoor,
                                                                               profesor__id__in=profesorescoor).values(
                                    'profesor')).order_by('persona__apellido1')
                            evaluaciones = EvaluacionDocentePeriodo.objects.filter(profesor=profesor,periodo__id__in=periodoscoor,evaluaciondocente=evaluaciondocente).order_by(
                                'fecha')
                            print(evaluaciones)
                            data['escoordinador'] = True
                    else:

                        evaluaciones = EvaluacionDocentePeriodo.objects.filter(profesor=profesor,evaluaciondocente=evaluaciondocente).order_by('fecha')
                        print((evaluaciones))

                    paging = MiPaginador(evaluaciones, 30)

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
                    # data['form'] = ParametroDescuentoForm()
                    data['evaluaciones'] = page.object_list
                    data['evaluaciondocente'] = evaluaciondocente.id

                    if 'error' in request.GET:
                        data['error']= request.GET['error']
                    # data['acc'] = request.GET['acc']
                    data['profesor']=profesor
                    data['evaluacion']=True

                    return render(request ,"evaluacionesdirectivo/evaluacionescoordina.html" ,  data)
                except Exception as e:
                    print(e)
                    return HttpResponseRedirect("/encuestaevaluacion")
            if action == 'evaluardirectivo':

                try:
                    periodoeval = EvaluacionDocentePeriodo.objects.filter(pk=request.GET['id'])[:1].get()

                    persona=Persona.objects.filter(usuario=request.user)[:1].get()

                    if EvaluacionDocente.objects.filter(directivo=True, estado=True).exists():
                        evaluaciondoc=EvaluacionDocente.objects.filter(directivo=True, estado=True)[:1].get()

                        # if not EvaluacionDirectivoPeriodo.objects.filter(evaluaciondocenteperiodo=periodoeval,
                        #                                              evaluaciondocente=evaluaciondoc).exists():
                        #     return  HttpResponseRedirect('/areasevaluacion?action=verevaluaciondocente&id='+str(periodoeval.profesor.id)+'&eva='+str(evaluaciondoc.id)+"&acc="+request.GET['acc']+"&error=NO EXISTE EVALUACION REALIZADA")

                        # if  not periodoeval.profesor.es_coordinadorperiodo(periodoeval.periodo):
                        #     detallesevaluacion = DetalleEvaluacionPregunta.objects.filter(evaluacion=periodoeval.evaluaciondocente).exclude(eje__percepcion=True)
                        if EvaluacionCoordinadorDocente.objects.filter(
                                evaluacion__evaluaciondoc=periodoeval.evaluaciondocente, coordinador__persona=persona,
                                profesor=periodoeval.profesor).exists():

                            if EvaluacionDirectivoPeriodo.objects.filter(evaluaciondocenteperiodo=periodoeval,evaluaciondocente=evaluaciondoc,persona=persona, activo=True).exists():
                                evaluaciondirectivo = EvaluacionDirectivoPeriodo.objects.filter(evaluaciondocenteperiodo=periodoeval,evaluaciondocente=evaluaciondoc,persona=persona,activo=True)[:1].get()
                            else:
                                evaluaciondirectivo = EvaluacionDirectivoPeriodo(evaluaciondocenteperiodo=periodoeval,evaluaciondocente=evaluaciondoc,persona=persona,fecha=datetime.now())
                                evaluaciondirectivo.save()
                                for e in DetalleEvaluacionPregunta.objects.filter(evaluacion=evaluaciondoc):
                                    if not DetalleEvaluacionDirectivo.objects.filter(evaluacion=evaluaciondirectivo,pregunta=e.pregunta).exists() and not evaluaciondirectivo.finalizado:
                                        d = DetalleEvaluacionDirectivo(evaluacion=evaluaciondirectivo,pregunta=e.pregunta)
                                        d.save()
                        else:
                            if EvaluacionDirectivoPeriodo.objects.filter(evaluaciondocenteperiodo=periodoeval,evaluaciondocente=evaluaciondoc).exists():
                                evaluaciondirectivo = EvaluacionDirectivoPeriodo.objects.filter(evaluaciondocenteperiodo=periodoeval,evaluaciondocente=evaluaciondoc)[:1].get()
                        if  not periodoeval.profesor.es_coordinadorperiodo(periodoeval.periodo):
                             ejes=DetalleEvaluacionPregunta.objects.filter(evaluacion=evaluaciondoc).exclude(eje__percepcion=True).values('eje')
                        else:
                            ejes=DetalleEvaluacionPregunta.objects.filter(evaluacion=evaluaciondoc).values('eje')

                        # ejes = DetalleEvaluacionPregunta.objects.filter(evaluacion=evaluaciondoc).values('eje')
                        data['ejes'] = EjesEvaluacion.objects.filter(id__in=ejes).order_by('id')
                        data['evaluaciondirectivo'] = evaluaciondirectivo
                        data['evaluaciondoc'] = evaluaciondoc
                        data['periodoeval'] = periodoeval

                        data['evaluacion'] = True
                        data['persona'] = persona
                        # data['acc'] = request.GET['acc']
                        print(67)
                        if CoordinadorCarrera.objects.filter(persona__usuario=request.user).exists():
                            data['escoordinador'] = True

                        return render(request ,"evaluacionesdirectivo/evaluardirectivo.html" ,  data)
                except Exception as e:
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}),
                                        content_type="application/json")


            if action == 'evaluar':
                try:

                    # data = {'title': ''}
                    # data['acc'] = request.GET['acc']
                    if 'iddoc' in request.GET:
                        profesor = Profesor.objects.get(id=request.GET['ins'])
                    else:
                        profesor = Profesor.objects.get(persona=data['persona'])
                    if 'op' in request.GET:
                        data['op'] = request.GET['op']
                    if 'acc' in request.GET:
                        data['acc'] = request.GET['acc']
                    if 'eval' in request.GET:
                        periodoeval = PeriodoEvaluacion.objects.filter(periodo__id=request.GET['id'],evaluaciondoc__id=request.GET['eval'])[:1].get()
                    else:
                        periodoeval = PeriodoEvaluacion.objects.filter(pk=request.GET['id'])[:1].get()
                    evaluacion = periodoeval.evaluaciondoc
                    if   EvaluacionDocentePeriodo.objects.filter(evaluaciondocente=evaluacion,
                                                          profesor=profesor,
                                                          periodo=periodoeval.periodo).exists():
                        evaluacionprofesor = EvaluacionDocentePeriodo.objects.filter(evaluaciondocente=evaluacion,
                                                          profesor=profesor,
                                                          periodo=periodoeval.periodo)[:1].get()
                    else:
                        evaluacionprofesor=EvaluacionDocentePeriodo(evaluaciondocente=evaluacion,
                                                                  profesor=profesor,
                                                                  periodo=periodoeval.periodo,
                                                                  fecha=datetime.now())
                        evaluacionprofesor.save()
                    detallesevaluacion = DetalleEvaluacionPregunta.objects.filter(evaluacion=evaluacion)
                    if  not profesor.es_coordinadorperiodo(evaluacionprofesor.periodo):
                        detallesevaluacion = DetalleEvaluacionPregunta.objects.filter(evaluacion=evaluacion).exclude(eje__percepcion=False)

                    for e in detallesevaluacion:
                        if not DetalleEvaluacionDocente.objects.filter(evaluacion=evaluacionprofesor,pregunta=e.pregunta).exists() and not evaluacionprofesor.finalizado:
                            d=DetalleEvaluacionDocente(evaluacion=evaluacionprofesor,
                                                      pregunta=e.pregunta)
                            d.save()
                    ejes=DetalleEvaluacionPregunta.objects.filter(evaluacion=evaluacion).exclude(eje__percepcion=True).values('eje')
                    data['ejes'] = EjesEvaluacion.objects.filter(id__in=ejes)
                    data['evaluacionprofesor']=evaluacionprofesor
                    data['evaluacion'] = True
                    data['profesor'] = profesor
                    return render(request ,"doc_evaluaciondocente/evaluaciondocente.html" ,  data)
                except Exception as e:
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}),
                                        content_type="application/json")

        else:
            try:
                if not CoordinadorCarreraPeriodo.objects.filter(persona__usuario=request.user).exists():
                    return HttpResponseRedirect("/?erro=No tiene Carrera asignada como coordinador")
                if CoordinadorCarreraPeriodo.objects.filter(persona__usuario=request.user).exists():
                    data['escoordinador'] = True
                    # evaluacioncor=EvaluacionCoordinadorDocente.objects.filter().values('coordinador__id')
                    cordina=CoordinadorCarreraPeriodo.objects.filter(persona__usuario=request.user)
                    print(cordina)
                    # coord = CoordinadorCarrera.objects.filter(persona__usuario=request.user, id__in=evaluacioncor)[:1].get()
                    # print(coord.carrera)
                    # eva=EvaluacionCoordinadorDocente.objects.filter(id=14)[:1].get()
                    if EvaluacionCoordinadorDocente.objects.filter(coordinador__in=cordina).exists():
                        print(87)
                        evaluaciondoc= EvaluacionCoordinadorDocente.objects.filter(coordinador__in=cordina).distinct('evaluacion__evaluaciondoc').values('evaluacion__evaluaciondoc')
                        print(evaluaciondoc)
                        area = EvaluacionDocente.objects.filter(id__in=evaluaciondoc, estado=True).order_by('descripcion')

                        paging = MiPaginador(area, 30)
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
                        data['area'] = page.object_list

                        if 'error' in request.GET:
                            data['error']= request.GET['error']

                return render(request ,"evaluacionesdirectivo/evaluacioncoordinador.html" ,  data)

            except Exception as e:
                print((e))
                return HttpResponseRedirect("/encuestaevaluacion")