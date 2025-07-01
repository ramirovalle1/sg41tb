import json
from datetime import datetime

from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator

from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from sga.commonviews import addUserData

from sga.models import PreguntasEvaluacion, RespuestasEjesEvaluacion, EvaluacionDocentePeriodo, \
    Profesor, PeriodoEvaluacion, DetalleEvaluacionPregunta, EjesEvaluacion, \
    DetalleEvaluacionDocente, elimina_tildes


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
                    evaluacionprofesor = EvaluacionDocentePeriodo.objects.filter(id=request.POST['evaluacionprofesor'])[:1].get()
                    if DetalleEvaluacionDocente.objects.filter(pregunta=pregunta,evaluacion=evaluacionprofesor).exists():
                        detalleeval=DetalleEvaluacionDocente.objects.filter(pregunta=pregunta,evaluacion=evaluacionprofesor)[:1].get()
                        if request.POST['val'] == 'true':
                            detalleeval.respuesta=respuesta
                            detalleeval.fecha=datetime.now()

                        else:
                            detalleeval.respuesta = None
                            detalleeval.fecha = datetime.now()
                        detalleeval.save()
                    return HttpResponse(json.dumps({'result': 'ok'}),
                                    content_type="application/json")

                except Exception as e:
                    msn = str(e)
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(msn)}), content_type="application/json")
            if action == 'finalizar':
                try:
                    evaluacionalumno = EvaluacionDocentePeriodo.objects.filter(id=request.POST['evaluacionprofesor'])[:1].get()
                    if DetalleEvaluacionDocente.objects.filter(evaluacion=evaluacionalumno,respuesta=None).exists():
                        eje=DetalleEvaluacionDocente.objects.filter(evaluacion=evaluacionalumno, respuesta=None).order_by('pregunta__eje')[:1].get().pregunta.eje
                        return HttpResponse(json.dumps({'result': 'bad', 'message': 'No ha respondido todas las preguntas del eje ' + elimina_tildes(eje.descripcion),'eje':str(eje.id)}),                            content_type="application/json")
                    evaluacionalumno.finalizado=True
                    evaluacionalumno.fechafinaliza=datetime.now()
                    evaluacionalumno.profesor.resultadoauto(evaluacionalumno.periodo)
                    # evaluacionalumno.calificacionporcentual=calificacion
                    evaluacionalumno.save()
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
                    # print('joj'+ str(evaluacionprofesor))
                    detallesevaluacion = DetalleEvaluacionPregunta.objects.filter(evaluacion=evaluacion)
                    if  not profesor.es_coordinadorperiodo(evaluacionprofesor.periodo):
                        detallesevaluacion = DetalleEvaluacionPregunta.objects.filter(evaluacion=evaluacion).exclude(eje__percepcion=True)
                    print(detallesevaluacion)
                    for e in detallesevaluacion:
                        if not DetalleEvaluacionDocente.objects.filter(evaluacion=evaluacionprofesor,pregunta=e.pregunta).exists() and not evaluacionprofesor.finalizado:
                            d=DetalleEvaluacionDocente(evaluacion=evaluacionprofesor,
                                                      pregunta=e.pregunta)
                            d.save()
                    if  not profesor.es_coordinadorperiodo(evaluacionprofesor.periodo):
                        ejes=DetalleEvaluacionPregunta.objects.filter(evaluacion=evaluacion).exclude(eje__percepcion=True).values('eje')
                    else:
                        ejes=DetalleEvaluacionPregunta.objects.filter(evaluacion=evaluacion).values('eje')
                    data['ejes'] = EjesEvaluacion.objects.filter(id__in=ejes).order_by('orden')
                    data['evaluacionprofesor']=evaluacionprofesor
                    # data['evaluacionprofesor']=evaluacionprofesor
                    data['evaluacion'] = True
                    data['profesor'] = profesor
                    return render(request ,"doc_evaluaciondocente/evaluaciondocente.html" ,  data)
                except Exception as e:
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}),
                                        content_type="application/json")

        else:

            try:
                search = None
                matricula = None
                inscripcion = None
                if 'id' in request.GET:
                    profesor = Profesor.objects.get(id=request.GET['id'])
                else:
                    profesor = Profesor.objects.get(persona=data['persona'])

                evaluaciones = EvaluacionDocentePeriodo.objects.filter(profesor=profesor,evaluaciondocente__estado=True).order_by('fecha')



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

                # data['permisopcion'] = AccesoModulo.objects.get(id=int(request.GET['acc']))
                if 'error' in request.GET:
                    data['error']= request.GET['error']
                data['profesor']=profesor
                data['evaluacion']=True
                return render(request ,"doc_evaluaciondocente/evaluacion.html" ,  data)

            except Exception as e:
                print((e))
                return HttpResponseRedirect("/encuestaevaluacion")