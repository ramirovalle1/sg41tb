import json
from decimal import Decimal

import xlwt
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType

from django.db.models import Q, Sum
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import RequestContext

from datetime import datetime
from sga.commonviews import addUserData
from sga.models import CoordinadorCarrera, Periodo, EvaluacionDocentePeriodo, Profesor, EvaluacionAlumno, DetalleEvaluacionAlumno, Carrera, EvaluacionDirectivoPeriodo


def view(request):
    if request.method == 'POST':

        if 'action' in request.POST:
            action = request.POST['action']

    else:
        data = {'title': 'Listado de parametros de Descuento'}
        addUserData(request, data)
        if 'action' in request.GET:
            action = request.GET['action']
            # if action == 'verevalalumno':
            #     try:
            #         if Profesor.objects.filter(pk=request.GET['profesor']).exists():
            #             profesor = Profesor.objects.filter(pk=request.GET['profesor'])[:1].get()
            #             if Periodo.objects.filter(pk=request.GET['periodo']).exists():
            #                 periodo = Periodo.objects.filter(pk=request.GET['periodo'])[:1].get()
            #                 if EvaluacionAlumno.objects.filter(profesormateria__profesor=profesor,
            #                                                    materia__nivel__periodo=periodo).exists():
            #                     eval = EvaluacionAlumno.objects.filter(profesormateria__profesor=profesor,
            #                                                            materia__nivel__periodo=periodo)[
            #                            :1].get().evaluaciondocente
            #                     ejes = DetalleEvaluacionPregunta.objects.filter(evaluacion=eval).values('eje')
            #                     data['ejes'] = EjesEvaluacion.objects.filter(id__in=ejes)
            #                     data['evaluacion'] = eval
            #                     data['profesor'] = profesor
            #                     if EvaluacionDirectivoPeriodo.objects.filter(evaluaciondocenteperiodo__periodo=periodo, evaluaciondocenteperiodo__profesor=profesor).exists():
            #                         evaluaciondirectivo=EvaluacionDirectivoPeriodo.objects.filter(evaluaciondocenteperiodo__periodo=periodo, evaluaciondocenteperiodo__profesor=profesor)[:1].get()
            #                         data['evaluaciondirectivo']=evaluaciondirectivo
            #                     data['periodo'] = periodo
            #                     if 'acc' in request.GET:
            #                         data['acc'] = request.GET['acc']
            #                     return render(request, 'evaluacionesdirectivo/evaluaciondocenteprofe.html', data)
            #     except Exception as ex:
            #         print(ex)
            # if action == 'verevaldocente':
            #     if Profesor.objects.filter(pk=request.GET['profesor']).exists():
            #         profesor = Profesor.objects.filter(pk=request.GET['profesor'])[:1].get()
            #         if Periodo.objects.filter(pk=request.GET['periodo']).exists():
            #             periodo = Periodo.objects.filter(pk=request.GET['periodo'])[:1].get()
            #             if EvaluacionDocentePeriodo.objects.filter(profesor=profesor, periodo=periodo,evaluaciondocente__docente=True,).exists():
            #                 evaluacionprofesor = EvaluacionDocentePeriodo.objects.filter(profesor=profesor,
            #                                                                              periodo=periodo,evaluaciondocente__docente=True,)[:1].get()
            #                 ejes = DetalleEvaluacionPregunta.objects.filter(
            #                     evaluacion=evaluacionprofesor.evaluaciondocente).values('eje')
            #                 data['ejes'] = EjesEvaluacion.objects.filter(id__in=ejes)
            #                 data['profesor'] = profesor
            #                 data['evaluacionprofesor'] = evaluacionprofesor
            #                 if EvaluacionDirectivoPeriodo.objects.filter(evaluaciondocenteperiodo=evaluacionprofesor).exists():
            #                     evaluaciondirectivo = EvaluacionDirectivoPeriodo.objects.filter(evaluaciondocenteperiodo=evaluacionprofesor)[:1].get()
            #                     data['evaluaciondirectivo'] = evaluaciondirectivo
            #                 data['periodo'] = periodo
            #                 if 'acc' in request.GET:
            #                     data['acc'] = request.GET['acc']
            #                 return render(request,'evaluacionesdirectivo/evaluaciondocente.html', data)
            # if action == 'verevaldirectivo':
            #     if Profesor.objects.filter(pk=request.GET['profesor']).exists():
            #         profesor = Profesor.objects.filter(pk=request.GET['profesor'])[:1].get()
            #         if Periodo.objects.filter(pk=request.GET['periodo']).exists():
            #             periodo = Periodo.objects.filter(pk=request.GET['periodo'])[:1].get()
            #             if EvaluacionDocentePeriodo.objects.filter(profesor=profesor, evaluaciondocente__docente=True,periodo=periodo).exists():
            #                 evaluacionprofesor = EvaluacionDocentePeriodo.objects.filter(evaluaciondocente__docente=True,profesor=profesor,
            #                                                                              periodo=periodo)[:1].get()
            #                 if EvaluacionDirectivoPeriodo.objects.filter(evaluaciondocenteperiodo=evaluacionprofesor).exists():
            #                     evaluaciondirectivo = EvaluacionDirectivoPeriodo.objects.filter(evaluaciondocenteperiodo=evaluacionprofesor)[:1].get()
            #                     ejes = DetalleEvaluacionPregunta.objects.filter(evaluacion=evaluaciondirectivo.evaluaciondocente).values('eje')
            #                     data['ejes'] = EjesEvaluacion.objects.filter(id__in=ejes)
            #                     data['profesor'] = profesor
            #                     data['evaluaciondirectivo'] = evaluaciondirectivo
            #                     data['periodo'] = periodo
            #                     if 'acc' in request.GET:
            #                         data['acc'] = request.GET['acc']
            #                     return render(request'evaluacionesdirectivo/evaluaciondirectivo.html', data)
            #             else:
            #                 data['error'] = request.GET['acc']
            #     if action == 'verdetalle':
            #         profesor = Profesor.objects.filter(pk=request.GET['profesor'])[:1].get()
            #         evaluacion = EvaluacionDocente.objects.filter(pk=request.GET['evaluacion'])[:1].get()
            #         pregunta = PreguntasEvaluacion.objects.filter(pk=request.GET['pid'])[:1].get()
            #         data['materias'] = Materia.objects.filter(
            #             id__in=EvaluacionAlumno.objects.filter(evaluaciondocente=evaluacion,
            #                                                    profesormateria__profesor=profesor).values(
            #                 'materia')).order_by('asignatura__nombre')
            #         data['profesor'] = profesor
            #         data['evaluacion'] = evaluacion
            #         data['pregunta'] = pregunta
            #         data['respuestas'] = pregunta.eje.respuestas()
            #         data['periodo'] = request.GET['periodo']
            #         return render(request,'evaluacionesdirectivo/verdetalledocenteeval.html', data)
            # if action == 'evaluardirectivo':
            #     search = None
            #     if 'periodo' in request.GET:
            #         periodoeval = PeriodoEvaluacion.objects.filter(id=request.GET['periodo'])[:1].get()
            #         data['periodo'] = periodoeval
            #         persona = CoordinadorCarrera.objects.filter(carrera__maestria=periodoeval.periodo.maestria).values(
            #             'persona')
            #     else:
            #         persona = CoordinadorCarrera.objects.filter().values('persona')
            #     periodos = PeriodoEvaluacion.objects.filter(
            #         evaluaciondoc__id__in=EvaluacionDocente.objects.filter(directivocargo=True).values('id'))
            #
            #     data['periodos'] = periodos
            #
            #     coordinador = Persona.objects.filter(id__in=persona).order_by('apellido1')
            #     # data['docentesevaluacion'] = docentesevaluacion
            #     data['acc'] = request.GET['acc']
            #     data['coordinador'] = coordinador
            #     if 's' in request.GET:
            #         search = request.GET['s']
            #         if search:
            #             ss = search.split(' ')
            #             while '' in ss:
            #                 ss.remove('')
            #             if len(ss) == 1:
            #                 coordinador = coordinador.filter(
            #                     Q(nombres__icontains=search) | Q(apellido1__icontains=search) | Q(
            #                         apellido2__icontains=search) | Q(cedula__icontains=search) | Q(
            #                         pasaporte__icontains=search) | Q(
            #                         usuario__username__icontains=search),
            #                     usuario__is_active=True).order_by('apellido1')
            #             else:
            #                 coordinador = coordinador.filter(Q(apellido1__icontains=ss[0]) & Q(
            #                     apellido2__icontains=ss[1]), usuario__is_active=True).order_by(
            #                     'apellido1',
            #                     'apellido2', 'nombres')
            #     paging = MiPaginador(coordinador, 30)
            #     p = 1
            #     try:
            #         if 'page' in request.GET:
            #             p = int(request.GET['page'])
            #         page = paging.page(p)
            #     except:
            #         page = paging.page(1)
            #     data['paging'] = paging
            #     data['rangospaging'] = paging.rangos_paginado(p)
            #     data['page'] = page
            #     data['search'] = search if search else ""
            #     # if EvaluacionCargoPeriodo.objects.filter()
            #     data['coordinador'] = page.object_list
            #     return render(request,"evaluacionesdirectivo/cordinadorescarrera.html", data)
            # if action == 'evaluar':
            #     try:
            #         if 'acc' in request.GET:
            #             data['acc'] = request.GET['acc']
            #         # periodoeval = EvaluacionDocentePeriodo.objects.filter(pk=request.GET['id'])[:1].get()
            #         personaevalua = Persona.objects.filter(usuario=request.user)[:1].get()
            #         personaevaluada = Persona.objects.filter(pk=request.GET['idper'])[:1].get()
            #         if PeriodoEvaluacion.objects.filter(id=request.GET['idperiodo'], evaluaciondoc__directivocargo=True,
            #                                             evaluaciondoc__estado=True).exists():
            #             periodoeval = PeriodoEvaluacion.objects.filter(id=request.GET['idperiodo'],
            #                                                            evaluaciondoc__directivocargo=True,
            #                                                            evaluaciondoc__estado=True)[:1].get()
            #             if EvaluacionDocente.objects.filter(directivocargo=True, estado=True).exists():
            #                 evaluaciondoc = EvaluacionDocente.objects.filter(directivocargo=True, estado=True)[:1].get()
            #             if EvaluacionCargoPeriodo.objects.filter(evaluaciondocente=periodoeval,
            #                                                      personaevaluada=personaevaluada).exists():
            #                 evaluaciondirectivocargo = EvaluacionCargoPeriodo.objects.filter(
            #                     evaluaciondocente=periodoeval, personaevaluada=personaevaluada)[:1].get()
            #             else:
            #                 evaluaciondirectivocargo = EvaluacionCargoPeriodo(evaluaciondocente=periodoeval,
            #                                                                   personaevaluada=personaevaluada,
            #                                                                   personaevalua=personaevalua,
            #                                                                   fecha=datetime.now())
            #                 evaluaciondirectivocargo.save()
            #
            #             for e in DetalleEvaluacionPregunta.objects.filter(evaluacion=periodoeval.evaluaciondoc):
            #
            #                 for ejecargo in RespuestaEjeEvaluacionDirectivo.objects.filter(
            #                         id__in=RespuestasEjesEvaluacion.objects.filter(eje=e.eje).values(
            #                             'respuesta__respuestadirectivo').distinct('respuesta__respuestadirectivo')):
            #                     if not DetalleEvaluacionCargo.objects.filter(evaluacion=evaluaciondirectivocargo,
            #                                                                  pregunta=e.pregunta,
            #                                                                  ejecargo=ejecargo).exists() and not evaluaciondirectivocargo.finalizado:
            #                         d = DetalleEvaluacionCargo(evaluacion=evaluaciondirectivocargo, pregunta=e.pregunta,
            #                                                    ejecargo=ejecargo)
            #                         d.save()
            #             ejes = DetalleEvaluacionPregunta.objects.filter(evaluacion=periodoeval.evaluaciondoc).values(
            #                 'eje')
            #             data['ejes'] = EjesEvaluacion.objects.filter(id__in=ejes)
            #             data['evaluaciondirectivo'] = evaluaciondirectivocargo
            #             data['evaluacion'] = True
            #             data['personaeva'] = personaevaluada
            #             data['rescargo'] = RespuestaEjeEvaluacionDirectivo.objects.filter(activo=True)
            #             data['bandera'] = '1'
            #             # data['eva'] = EvaluacionDocente.objects.filter(pk=request.GET['eva'])[:1].get()
            #             data['acc'] = request.GET['acc']
            #             return render(request,'evaluacionesdirectivo/evaluarcargo.html', data)
            #         else:
            #             return HttpResponseRedirect('/?info=No hay evaluacion para el perioodo')
            #
            #
            #     except Exception as e:
            #         return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}),
            #                             content_type="application/json")
        else:
            periodo = None
            profesor = None
            search = None
            try:
                coordinadores = CoordinadorCarrera.objects.filter().values('persona')

                if 'periodo' in request.GET:
                    if (request.GET['periodo']) != '':
                        periodo=Periodo.objects.filter(pk=request.GET['periodo'])[:1].get()

                        if EvaluacionDocentePeriodo.objects.filter(periodo=periodo).exists():
                            profesor = EvaluacionDocentePeriodo.objects.filter(periodo=periodo).exclude(profesor__persona__id__in=coordinadores).distinct(
                                'profesor').values('profesor')
                            # if EvaluacionAlumno.objects.filter( profesormateria__materia__nivel__periodo=request.GET['periodo']).exists():
                            #     evaluacion = EvaluacionAlumno.objects.filter(profesormateria__materia__nivel__periodo=request.GET['periodo']).distinct('profesormateria__profesor').values('profesormateria__profesor')
                            profesor = Profesor.objects.filter(id__in=profesor).order_by('persona__apellido1')
                            # evaluaciondocente=EvaluacionDocentePeriodo.objects.filter(id__in)
                            data['profesor'] = profesor
                            data['periodo'] = periodo

                            # data['periodonombre'] = per
                            # evaluaciondocente=EvaluacionDocente.objects.filter(directivo=True, estado=True)[:1].get()
                            # data['eva']=evaluaciondocente
                            evaluaciondirectivo = EvaluacionDirectivoPeriodo.objects.filter(finalizado=True,
                                                                      evaluaciondocenteperiodo__periodo_id=int(request.GET['periodo']),
                                                                      evaluaciondocenteperiodo__profesor__in=profesor).distinct('evaluaciondocenteperiodo__profesor').count()
                            evaluacionauto  = EvaluacionDocentePeriodo.objects.filter(periodo_id=int(request.GET['periodo']), profesor__in=profesor).distinct('profesor').count()
                            evaluacionalumno = EvaluacionAlumno.objects.filter(materia__nivel__periodo_id=int(request.GET['periodo']),profesormateria__profesor__in=profesor).distinct('profesormateria__profesor').count()



                            data['evaluacionalumno'] =  evaluacionalumno
                            data['totalevaluacionalumno'] =  (evaluacionalumno/profesor.count()) * 100

                            data['evaluacionauto'] =  evaluacionauto
                            data['totalautoevaluacion'] =  (evaluacionauto/profesor.count()) * 100

                            data['evaluaciondirectivo'] =evaluaciondirectivo
                            data['totalevaluaciondirectivo'] =( evaluaciondirectivo/profesor.count()) * 100

                            data['profesortotalporperiodo'] = profesor
                if 's' in request.GET:
                    search = request.GET['s']
                if search:
                    data['search'] = search
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')
                    if len(ss) == 1:


                        inprof = Profesor.objects.filter(Q(evaluaciondocenteperiodo__profesor__persona__nombres__icontains=search) | Q(
                            evaluaciondocenteperiodo__profesor__persona__apellido1__icontains=search) | Q(
                            evaluaciondocenteperiodo__profesor__persona__apellido2__icontains=search) | Q(
                            evaluaciondocenteperiodo__profesor__persona__cedula__icontains=search) | Q(
                            evaluaciondocenteperiodo__profesor__persona__pasaporte__icontains=search), evaluaciondocenteperiodo__periodo = request.GET['periodo']).values('id').distinct('id')
                        profesor = Profesor.objects.filter(id__in=inprof).exclude(persona__id__in=coordinadores).order_by('persona__apellido1')
                    else:
                        profesor = Profesor.objects.filter(Q(evaluaciondocenteperiodo__profesor__persona__apellido1__icontains=ss[0]) & Q(
                            evaluaciondocenteperiodo__profesor__persona__apellido2__icontains=ss[1]), evaluaciondocenteperiodo__periodo = request.GET['periodo']).exclude(persona__id__in=coordinadores).order_by('persona__apellido1',
                                                                           'persona__apellido2',
                                                                           'persona__nombres')

                if 'tipo' in request.GET:
                    data['tipo'] = int(request.GET['tipo'])
                    if request.GET['tipo'] == '1':
                        evaluacionprofesor = EvaluacionAlumno.objects.filter(
                            materia__nivel__periodo_id=int(request.GET['periodo']),
                            profesormateria__profesor__in=profesor).values_list(
                            'profesormateria__profesor').distinct('profesormateria__profesor')
                        profesor = profesor.filter().exclude(id__in=evaluacionprofesor)

                    elif request.GET['tipo'] == '2':
                        evaluacionprofesor = EvaluacionDocentePeriodo.objects.filter(
                            periodo_id=int(request.GET['periodo']), profesor__in=profesor).values_list(
                            'profesor').distinct('profesor')
                        profesor = profesor.filter().exclude(id__in=evaluacionprofesor)

                    elif request.GET['tipo'] == '3':
                        evaluacionprofesor = EvaluacionDirectivoPeriodo.objects.filter(
                            evaluaciondocenteperiodo__periodo_id=int(request.GET['periodo']),
                            evaluaciondocenteperiodo__profesor__in=profesor).values_list(
                            'evaluaciondocenteperiodo__profesor').distinct('evaluaciondocenteperiodo__profesor')
                        profesor = profesor.filter().exclude(id__in=evaluacionprofesor)

                    elif request.GET['tipo'] == '4':
                        evaluacionDirectivoPeriodoProfesor = EvaluacionDirectivoPeriodo.objects.filter(
                            evaluaciondocenteperiodo__periodo_id=int(request.GET['periodo']),
                            evaluaciondocenteperiodo__profesor__in=profesor).values_list(
                            'evaluaciondocenteperiodo__profesor').distinct('evaluaciondocenteperiodo__profesor')
                        evaluacionDocentePeriodoprofesor = EvaluacionDocentePeriodo.objects.filter(
                            periodo_id=int(request.GET['periodo']), profesor__in=profesor).values_list(
                            'profesor').distinct('profesor')
                        evaluacionAlumnoProfesor = EvaluacionAlumno.objects.filter(
                            materia__nivel__periodo_id=int(request.GET['periodo']),
                            profesormateria__profesor__in=profesor).values_list(
                            'profesormateria__profesor').distinct('profesormateria__profesor')

                        profesor = profesor.filter().exclude(
                            Q(id__in=evaluacionAlumnoProfesor) & Q(id__in=evaluacionDocentePeriodoprofesor) & Q(
                                id__in=evaluacionDirectivoPeriodoProfesor))


                evaperiodo=EvaluacionDocentePeriodo.objects.filter().values('periodo')
                # periodo=PeriodoEvaluacion.objects.filter(evaluaciondoc__id__in=EvaluacionDocente.objects.filter(directivocargo=True))
                periodo = Periodo.objects.filter(id__in=evaperiodo)
                data['periodos'] = periodo

                if 'periodo' in request.GET:
                    data['carreras'] = Carrera.objects.filter(id__in=DetalleEvaluacionAlumno.objects.filter(
                        evaluacion__materia__nivel__periodo_id=int(request.GET['periodo'])).values(
                        'evaluacion__materia__nivel__carrera_id'), activo=True).order_by('nombre')


                data['profesor'] = profesor
                return render(request ,"evaluacionesdirectivo/evaluacionesdirectivo.html" ,  data)

            except Exception as e:
                return HttpResponseRedirect("/?info="+str(e))
