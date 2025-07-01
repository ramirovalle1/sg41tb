import json
from datetime import datetime

from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator

from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
from sga.commonviews import addUserData
from sga.models import EvaluacionAlumno, Inscripcion, Matricula,  MateriaAsignada, ProfesorMateria, \
    EvaluacionMateria, DetalleEvaluacionPregunta, DetalleEvaluacionAlumno, EjesEvaluacion, RespuestasEvaluacion, \
    RespuestasEjesEvaluacion, PreguntasEvaluacion, Profesor, CoordinadorCarrera


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
                    evaluacionalumno = EvaluacionAlumno.objects.filter(id=request.POST['evaluacionalumno'])[:1].get()
                    if DetalleEvaluacionAlumno.objects.filter(pregunta=pregunta,evaluacion=evaluacionalumno).exists():
                        detalleeval=DetalleEvaluacionAlumno.objects.filter(pregunta=pregunta,evaluacion=evaluacionalumno)[:1].get()
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
                    evaluacionalumno = EvaluacionAlumno.objects.filter(id=request.POST['evaluacionalumno'])[:1].get()
                    if DetalleEvaluacionAlumno.objects.filter(evaluacion=evaluacionalumno,respuesta=None).exists():
                        eje=DetalleEvaluacionAlumno.objects.filter(evaluacion=evaluacionalumno, respuesta=None).order_by('pregunta__eje')[:1].get().pregunta.eje
                        return HttpResponse(json.dumps({'result': 'bad', 'message': 'No ha respondido todas las preguntas del eje ' + str(eje.descripcion),'eje':str(eje.id)}),                            content_type="application/json")
                    evaluacionalumno.finalizado=True
                    evaluacionalumno.save()
                    return HttpResponse(json.dumps({'result': 'ok'}),
                                    content_type="application/json")

                except Exception as e:
                    msn = str(e)
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(msn)}), content_type="application/json")




    else:
        data = {'title': 'Evaluacion de Mis Docentes'}
        addUserData(request,data)
        data['puede_entrar_al_sistema'] = True
        # data['docadicional'] = None
        if 'action' in request.GET:
            action = request.GET['action']
            if action == 'evaluar':
                try:

                    # data = {'title': ''}
                    # data['acc'] = request.GET['acc']
                    if 'ins' in request.GET:
                        inscripcion = Inscripcion.objects.get(id=request.GET['ins'])
                    else:
                        inscripcion = Inscripcion.objects.get(persona=data['persona'])
                    if 'op' in request.GET:
                        data['op'] = request.GET['op']
                    if 'acc' in request.GET:
                        data['acc'] = request.GET['acc']
                    profemate = ProfesorMateria.objects.filter(pk=request.GET['id'])[:1].get()
                    evaluacion = EvaluacionMateria.objects.filter(materia=profemate.materia)[:1].get()
                    if   EvaluacionAlumno.objects.filter(evaluaciondocente=evaluacion.evaluaciondocente,
                                                          inscripcion=inscripcion,
                                                          profesormateria=profemate,
                                                          materia=profemate.materia).exists():
                        evaluacionalumno = EvaluacionAlumno.objects.filter(evaluaciondocente=evaluacion.evaluaciondocente,
                                                          inscripcion=inscripcion,
                                                          profesormateria=profemate,
                                                          materia=profemate.materia)[:1].get()
                    else:
                        evaluacionalumno=EvaluacionAlumno(evaluaciondocente=evaluacion.evaluaciondocente,
                                                          inscripcion=inscripcion,
                                                          profesormateria=profemate,
                                                          materia=profemate.materia,
                                                          fecha=datetime.now())
                        evaluacionalumno.save()
                    for e in DetalleEvaluacionPregunta.objects.filter(evaluacion=evaluacion.evaluaciondocente):
                        if not DetalleEvaluacionAlumno.objects.filter(evaluacion=evaluacionalumno,pregunta=e.pregunta).exists() and not evaluacionalumno.finalizado:
                            d=DetalleEvaluacionAlumno(evaluacion=evaluacionalumno,
                                                      pregunta=e.pregunta)
                            d.save()
                        else:
                            if  DetalleEvaluacionAlumno.objects.filter(evaluacion=evaluacionalumno,pregunta=e.pregunta).count()>1:
                                if DetalleEvaluacionAlumno.objects.filter(evaluacion=evaluacionalumno, pregunta=e.pregunta,
                                                                       respuesta=None).exists():
                                    elimina=DetalleEvaluacionAlumno.objects.filter(evaluacion=evaluacionalumno, pregunta=e.pregunta,respuesta=None)[:1].get()
                                else:
                                    elimina = DetalleEvaluacionAlumno.objects.filter(evaluacion=evaluacionalumno,
                                                                                     pregunta=e.pregunta)[:1].get()
                                elimina.delete()
                    ejes=DetalleEvaluacionPregunta.objects.filter(evaluacion=evaluacion.evaluaciondocente).values('eje')
                    data['ejes'] = EjesEvaluacion.objects.filter(id__in=ejes)
                    data['evaluacionalumno']=evaluacionalumno
                    data['evaluacion'] = True
                    data['inscripcion'] = inscripcion

                    return render(request ,"alu_evaluaciondocente/evaluaciondocente.html" ,  data)
                except Exception as e:
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}),
                                        content_type="application/json")

        else:

            try:
                search = None
                matricula = None
                inscripcion = None
                if 'op' in request.GET:
                    data['op']=request.GET['op']
                if 'id' in request.GET:
                    if  Profesor.objects.filter(persona__usuario=request.user).exists():
                        data['estutor']=True
                    if CoordinadorCarrera.objects.filter(persona__usuario=request.user).exists():
                        data['escoordinador'] = True
                    inscripcion = Inscripcion.objects.get(id=request.GET['id'])
                else:
                    if Inscripcion.objects.get(persona=data['persona']):
                        inscripcion = Inscripcion.objects.get(persona=data['persona'])

                if 'mid' in request.GET:
                    matricula = Matricula.objects.filter(pk=request.GET['mid'])[:1].get()
                    data['matricula']=matricula

                data['matriculas'] = Matricula.objects.filter(inscripcion=inscripcion)
                data['inscripcion']=inscripcion
                if matricula:
                    materiasasgi = MateriaAsignada.objects.filter(matricula=matricula).values('materia')
                    evaluaciones = EvaluacionAlumno.objects.filter(materia__id__in=materiasasgi,
                                                                   inscripcion=inscripcion).order_by('profesormateria')
                else:
                    evaluaciones = EvaluacionAlumno.objects.filter(inscripcion=inscripcion).order_by('profesormateria')
                    data['matricula'] = inscripcion.matricula()


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

                data['inscripcion']=inscripcion
                data['evaluacion']=True
                return render(request ,"alu_evaluaciondocente/evaluacion.html" ,  data)

            except Exception as e:
                print(e)
                return HttpResponseRedirect("/encuestaevaluacion")