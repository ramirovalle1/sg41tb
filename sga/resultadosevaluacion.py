import json
from decimal import Decimal
from django.core.paginator import Paginator

import xlwt
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType

from django.db.models import Q, Sum
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import RequestContext

from datetime import datetime
from settings import MEDIA_ROOT

from sga.commonviews import addUserData
from sga.forms import XLSPeriodoForm
from sga.models import Carrera, CoordinadorCarrera, EvaluacionDocentePeriodo, EvaluacionAlumno, \
    DetalleEvaluacionPregunta, EjesEvaluacion, TituloInstitucion, Periodo, Profesor, EvaluacionDirectivoPeriodo, \
    DetalleEvaluacionAlumno, DetalleEvaluacionDocente, PeriodoEvaluacion, EvaluacionCoordinadorDocente, \
    DetalleEvaluacionDirectivo, EvaluacionDocente, CoordinadorCarreraPeriodo, ProfesorMateria, Coordinacion, Persona, \
    ReporteExcel, elimina_tildes, PreguntasEvaluacion, EvaluacionCargoPeriodo


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
    if request.method == 'POST':

        if 'action' in request.POST:
            action = request.POST['action']

            if action == 'generarexcelevaluacionprofesor':
                try:

                    carrera = None
                    periodo = None

                    carrera = Carrera.objects.get(pk=int(request.POST['carrera']))
                    if int(request.POST['periodo']) > 0:
                        periodo = int(request.POST['periodo'])
                    coordinadores = CoordinadorCarrera.objects.filter().values('persona')
                    evaluacionprofesor = EvaluacionDocentePeriodo.objects.filter(periodo=periodo)[:1].get()
                    if EvaluacionAlumno.objects.filter(materia__nivel__periodo=periodo).exists():
                        eval = EvaluacionAlumno.objects.filter(materia__nivel__periodo=periodo)[:1].get().evaluaciondocente
                        idejes = DetalleEvaluacionPregunta.objects.filter(evaluacion=eval).values('eje')
                        ejes = EjesEvaluacion.objects.filter(id__in=idejes)
                    else:
                        return HttpResponse(json.dumps({'result': 'bad', 'message': 'No existen evaluaciones disponibles'}),
                                            content_type="application/json")


                    m = 12

                    borders = xlwt.Borders()
                    borders.left = xlwt.Borders.THIN
                    borders.right = xlwt.Borders.THIN
                    borders.top = xlwt.Borders.THIN
                    borders.bottom = xlwt.Borders.THIN

                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo2_v1 = xlwt.easyxf('font: bold on; align: wrap off, vert centre, horiz center')
                    subtitulo2 = xlwt.easyxf('align:vert centre, horiz center')
                    subtitulo3 = xlwt.easyxf('font: name Times New Roman, colour black, bold on;')
                    titulo.font.height = 20 * 11

                    titulo2.font.height = 20 * 11
                    titulo2_v1.font.height = 20 * 11

                    subtitulo = xlwt.easyxf(
                        'font: name Times New Roman, colour black, bold on; align: wrap on, vert centre, horiz center; pattern: pattern solid, fore_colour silver_ega;')
                    subtitulo.font.height = 20 * 10
                    subtitulo.borders = borders
                    subtitulo2.font.height = 20 * 10
                    subtitulo2.borders = borders
                    subtitulo3.borders = borders

                    wb = xlwt.Workbook()

                    ws = wb.add_sheet("Evaluacion Alumnos", cell_overwrite_ok=True)

                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0, 0, m + 4, tit.nombre, titulo2)
                    ws.write_merge(1, 1, 0, m + 4, str('REPORTE EVALUACION ALUMNOS'), titulo2_v1)
                    ws.write_merge(2, 2, 0, m + 4, "PERIODO: " + str(Periodo.objects.get(pk=periodo).nombre),
                                   titulo2_v1)
                    ws.write_merge(3, 3, 0, m + 4, "CARRERA: " + str(carrera.nombre), titulo2_v1)

                    fila = 6

                    for e in ejes:
                        ws.write_merge(fila, fila, 0, 4, str(e.descripcion), subtitulo)
                        colum = 5

                        for r in e.respuestas():
                            ws.write_merge(fila, fila, colum, colum + 1, str(r.respuesta.nombre),
                                           subtitulo)
                            colum = colum + 2

                        ws.write_merge(fila, fila, colum, colum + 1, 'Porcentaje',
                                       subtitulo)
                        fila = fila + 1
                        porcentajetotal = 0
                        for p in e.preguntas_alumno():
                            ws.write_merge(fila, fila, 0, 4, str(p.nombre), subtitulo3)
                            colum = 5
                            valor = 0

                            for r in e.respuestas():
                                ws.write_merge(fila, fila, colum, colum + 1,
                                               str(r.cantidad_respuestaperiododatos_total(eval,coordinadores, p, carrera, periodo)),
                                               subtitulo2)
                                valor += r.cantidad_respuestaperiododatos_total(eval, coordinadores,p, carrera, periodo)

                                colum = colum + 2
                            resp = e.respuestas()

                            ultima = resp[resp.count() - 1].cantidad_respuestaperiododatos_total(eval, coordinadores,p, carrera,
                                                                                                 periodo)
                            penultima = resp[resp.count() - 2].cantidad_respuestaperiododatos_total(eval,coordinadores, p, carrera,
                                                                                                    periodo)
                            porcentaje = (((ultima + penultima) / valor) * 100) if valor else 0
                            porcentajetotal += porcentaje
                            ws.write_merge(fila, fila, colum, colum + 1, str("{:.2f}".format(porcentaje)),
                                           subtitulo2)

                            fila = fila + 1

                        porcentajetotal = porcentajetotal / e.preguntas_alumno().count() if porcentajetotal else 0
                        ws.write_merge(fila, fila, 0, (e.respuestas().count() * 2) + 4, str(e.descripcion),
                                       subtitulo)
                        ws.write_merge(fila, fila, (e.respuestas().count() * 2) + 5, (e.respuestas().count() * 2) + 6,
                                       str("{:.2f}".format(porcentajetotal)), subtitulo)
                        fila = fila + 1

                    fila = fila + 2
                    ws.write(fila, 0, "Fecha Impresion", titulo)
                    ws.write(fila, 1, str(datetime.now()), titulo)
                    ws.write(fila + 1, 0, "Usuario", titulo)
                    ws.write(fila + 1, 1, str(request.user), titulo)

                    nombre = 'evaluacionalumnos' + str(datetime.now()).replace(" ", "").replace(".", "").replace(":",
                                                                                                                 "") + '.xls'
                    wb.save(MEDIA_ROOT + '/reportes_excel/' + nombre)
                    return HttpResponse(json.dumps({"result": "ok", "url": "/ube/media/reportes_excel/" + nombre}),
                                        content_type="application/json")

                except Exception as e:
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}),
                                        content_type="application/json")

            if action == 'generarexcel':
                try:
                    titulo = xlwt.easyxf(
                        'font: name Times New Roman, colour black, bold on;align: wrap on, vert centre, horiz center')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20 * 11
                    titulo2.font.height = 20 * 11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20 * 10
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('Listado', cell_overwrite_ok=True)

                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0, 0, 14, tit.nombre, titulo2)

                    periodo = Periodo.objects.filter(pk=request.POST['cmbperiodoexcel'])[:1].get()
                    carrera = Carrera.objects.filter(pk=request.POST['cmbcarrerasexcel'])[:1].get()
                    profesorma = EvaluacionCoordinadorDocente.objects.filter(coordinador__carrera=carrera).values('profesor__id')
                    profeeva = EvaluacionDocentePeriodo.objects.filter(periodo=periodo, finalizado=True,profesor__id__in=profesorma).values('profesor')
                    profesores = Profesor.objects.filter(id__in=profeeva).order_by('persona__apellido1')

                    ws.write(2, 0, "Periodo",titulo)
                    ws.write(2, 1, elimina_tildes(periodo.nombre))
                    ws.write(3, 0, "Carrera",titulo)
                    ws.write(3, 1, elimina_tildes(carrera.nombre))

                    fila = 5
                    ws.write(fila, 0, "Profesor", titulo)
                    ws.col(0).width = 10 * 1000
                    ws.write(fila, 1, "Evaluación Alumno", titulo)
                    ws.col(1).width = 10 * 300
                    ws.write(fila, 2, "Autoevaluación", titulo)
                    ws.col(2).width = 10 * 300
                    ws.write(fila, 3, "Evaluación Directivo", titulo)
                    ws.col(3).width = 10 * 300

                    fila =fila+1

                    for profesor in profesores:
                        ws.write(fila, 0, elimina_tildes(profesor.persona.nombre_completo_inverso()))

                        if profesor.tiene_evaluacionalumno(periodo):
                            resutadoevaluacion_alumno = profesor.resultadosevaluacion(periodo)[0]
                            if resutadoevaluacion_alumno:
                                ws.write(fila, 1, str(resutadoevaluacion_alumno)+'/25')

                        if profesor.tiene_evaluacion(periodo):
                            resultadosautoevaluacion = profesor.resultadosevaluacion(periodo)[1]
                            if resultadosautoevaluacion:
                                ws.write(fila, 2, str(resultadosautoevaluacion)+'/25')

                        if profesor.tiene_evaluaciondirectivo(periodo):
                            resultadosevaluaciondirectivo = profesor.resultadosevaluacion(periodo)[2]
                            if resultadosevaluaciondirectivo:
                                ws.write(fila, 3, str(resultadosevaluaciondirectivo)+'/45')
                        fila += 1

                    fila += 2
                    ws.write(fila, 0, "Fecha Impresion", subtitulo)
                    ws.write(fila, 1, str(datetime.now()), subtitulo)
                    ws.write(fila + 1, 0, "Usuario", subtitulo)
                    ws.write(fila + 1, 1, str(request.user), subtitulo)

                    nombre = 'resultadoevaluacion' + str(datetime.now()).replace(" ", "").replace(".", "").replace(":", "") + '.xls'
                    wb.save(MEDIA_ROOT + '/reporteexcel/' + nombre)
                    return HttpResponse(json.dumps({"result": "ok", "url": "/media/reporteexcel/" + nombre}),
                                        content_type="application/json")

                except Exception as ex:
                    print(ex)
                    return HttpResponse(json.dumps({"result": "bad", "message": ex}), content_type="application/json")


            if action == 'generarexcelreporte':
                try:
                    print(request.POST)

                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on;align: wrap on, vert centre, horiz center')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20 * 11
                    titulo2.font.height = 20 * 11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20 * 10
                    wb = xlwt.Workbook()

                    # RESULTADO EVALUACION DE ALUMNOS
                    ws_ea = wb.add_sheet('Evaluación Alumno', cell_overwrite_ok=True)

                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws_ea.write_merge(0, 0, 0, 14, tit.nombre, titulo2)

                    profesor = Profesor.objects.filter(id=request.POST['id'])[:1].get()
                    periodo = Periodo.objects.filter(pk=request.POST['periodo_id']).first()

                    ws_ea.write(2, 0, "EVALUACIÓN DOCENTE:", titulo)
                    ws_ea.col(0).width = 10 * 800
                    ws_ea.write(2, 1, elimina_tildes(profesor))

                    fila = 4
                    evaluacion_alumno = EvaluacionAlumno.objects.filter(profesormateria__profesor=profesor,materia__nivel__periodo=periodo).first()

                    if evaluacion_alumno:

                        ejes_alumnos = DetalleEvaluacionPregunta.objects.filter(
                            evaluacion=evaluacion_alumno.evaluaciondocente).values('eje')
                        ejesevaluacion_alumno = EjesEvaluacion.objects.filter(id__in=ejes_alumnos)

                        for e in ejesevaluacion_alumno:
                            col = 6
                            ws_ea.write_merge(fila, fila, 0, col, elimina_tildes(e.descripcion), titulo2)
                            for r in e.respuestas():
                                col += 1
                                ws_ea.write(fila, col, elimina_tildes(r.respuesta.nombre), titulo2)
                            fila += 1
                            for p in e.preguntas_alumno():
                                col = 6
                                ws_ea.write_merge(fila, fila, 0, col, elimina_tildes(p.nombre))
                                for r in e.respuestas():
                                    col += 1
                                    ws_ea.write(fila, col,
                                                r.cantidad_respuestaperiododatos(evaluacion_alumno.evaluaciondocente, p,
                                                                                 profesor, periodo))
                                fila += 1
                        fila += 2
                    else:
                        ws_ea.write(fila, 0, "NO EXISTEN EVALUACIONES DE ALUMNOS")
                        fila = fila + 1

                    ws_ea.write(fila, 0, "Fecha Impresión", subtitulo)
                    ws_ea.write(fila, 1, str(datetime.now()), subtitulo)
                    ws_ea.write(fila + 1, 0, "Usuario", subtitulo)
                    ws_ea.write(fila + 1, 1, str(request.user), subtitulo)

                    # AUTOEVALUACION
                    ws_autoevaluacion = wb.add_sheet('Autoevaluación', cell_overwrite_ok=True)

                    ws_autoevaluacion.write_merge(0, 0, 0, 14, tit.nombre, titulo2)

                    periodoeval = PeriodoEvaluacion.objects.filter(periodo__id=request.POST['periodo_id'])[:1].get()

                    ws_autoevaluacion.write(2, 0, "AUTOEVALUACIÓN DEL DOCENTE:", titulo)
                    ws_autoevaluacion.col(0).width = 10 * 800
                    ws_autoevaluacion.write(2, 1, elimina_tildes(profesor))

                    evaluacion = periodoeval.evaluaciondoc
                    evaluacionprofesor = EvaluacionDocentePeriodo.objects.filter(evaluaciondocente=evaluacion,profesor=profesor,periodo=periodoeval.periodo).first()

                    fila = 4
                    if evaluacionprofesor:

                        if not profesor.es_coordinadorperiodo(evaluacionprofesor.periodo):
                            ejes_autoevaluacion = DetalleEvaluacionPregunta.objects.filter(evaluacion=evaluacion).exclude(eje__percepcion=True).values('eje')
                        else:
                            ejes_autoevaluacion = DetalleEvaluacionPregunta.objects.filter(evaluacion=evaluacion).values('eje')

                        ejes_evaluacionprofesor = EjesEvaluacion.objects.filter(id__in=ejes_autoevaluacion).order_by('orden')

                        for e in ejes_evaluacionprofesor:
                            col = 6
                            ws_autoevaluacion.write_merge(fila, fila, 0, col, elimina_tildes(e.descripcion), titulo2)
                            for r in e.respuestas():
                                col += 1
                                ws_autoevaluacion.write(fila, col, elimina_tildes(r.respuesta.nombre), titulo2)
                            fila += 1
                            if e.areas():
                                for a in e.areas():
                                    col = 3
                                    totpreguntas_docentearea = e.preguntas_docentearea(a)
                                    ws_autoevaluacion.write_merge(fila, fila + totpreguntas_docentearea.count() - 1, 0,col, elimina_tildes(a.descripcion))
                                    col += 1
                                    for p in totpreguntas_docentearea:
                                        ws_autoevaluacion.write_merge(fila, fila, 4, 6, elimina_tildes(p.nombre))
                                        col = 6
                                        for r in e.respuestas():
                                            descripcion = 'no'
                                            respuesta = p.tiene_respuesta_docente(evaluacionprofesor)
                                            if respuesta:
                                                if respuesta.respuesta == r:
                                                    descripcion = 'si'
                                            col += 1
                                            ws_autoevaluacion.write(fila, col, descripcion)

                                        fila += 1
                            else:
                                for p in e.preguntas_docente():
                                    col = 6
                                    ws_autoevaluacion.write_merge(fila, fila, 4, col, elimina_tildes(p.nombre))
                                    for r in e.respuestas():
                                        descripcion = 'no'
                                        respuesta = p.tiene_respuesta_docente(evaluacionprofesor)
                                        if respuesta:
                                            if respuesta.respuesta == r:
                                                descripcion = 'si'
                                        col += 1
                                        ws_autoevaluacion.write(fila, col, descripcion)
                                    fila += 1
                            fila += 1

                        fila += 2
                    else:
                        ws_autoevaluacion.write(fila, 0, "NO EXISTE AUTOEVALUACIÓN")
                        fila = fila + 1

                    ws_autoevaluacion.write(fila, 0, "Fecha Impresión", subtitulo)
                    ws_autoevaluacion.write(fila, 1, str(datetime.now()), subtitulo)
                    ws_autoevaluacion.write(fila + 1, 0, "Usuario", subtitulo)
                    ws_autoevaluacion.write(fila + 1, 1, str(request.user), subtitulo)

                    # DIRECTIVOS
                    ws_evaluacion_directivo = wb.add_sheet('Evaluación Directivo', cell_overwrite_ok=True)

                    ws_evaluacion_directivo.write_merge(0, 0, 0, 14, tit.nombre, titulo2)

                    ws_evaluacion_directivo.write(2, 0, "EVALUACIÓN DIRECTIVO:", titulo)
                    ws_evaluacion_directivo.col(0).width = 10 * 800
                    ws_evaluacion_directivo.write(2, 1, elimina_tildes(profesor))

                    fila = 4

                    if EvaluacionDocentePeriodo.objects.filter(profesor=profesor, evaluaciondocente__docente=True,
                                                               periodo=periodo).exists():
                        evaluacionprofesor = EvaluacionDocentePeriodo.objects.filter(evaluaciondocente__docente=True,
                                                                                     profesor=profesor,
                                                                                     periodo=periodo)[:1].get()

                        if EvaluacionDirectivoPeriodo.objects.filter(
                                evaluaciondocenteperiodo=evaluacionprofesor).exists():
                            evaluaciondirectivo = EvaluacionDirectivoPeriodo.objects.filter(
                                evaluaciondocenteperiodo=evaluacionprofesor)[:1].get()
                            ejes_evaluaciondirectivo = DetalleEvaluacionPregunta.objects.filter(
                                evaluacion=evaluaciondirectivo.evaluaciondocente).exclude(eje__percepcion=True).values(
                                'eje')
                            ejesevaluaciondirectivo = EjesEvaluacion.objects.filter(
                                id__in=ejes_evaluaciondirectivo).order_by('orden')

                            for e in ejesevaluaciondirectivo:
                                col = 6
                                ws_evaluacion_directivo.write_merge(fila, fila, 0, col, elimina_tildes(e.descripcion),
                                                                    titulo2)

                                for r in e.respuestas():
                                    col += 1
                                    ws_evaluacion_directivo.write(fila, col, elimina_tildes(r.respuesta.nombre),
                                                                  titulo2)

                                fila += 1

                                if e.areas():
                                    for area in e.areas():
                                        col = 3

                                        totpreguntas_docentearea = e.preguntas_directivoarea(area)
                                        ws_evaluacion_directivo.write_merge(fila,
                                                                            fila + totpreguntas_docentearea.count() - 1,
                                                                            0, col, elimina_tildes(area.descripcion))
                                        col += 1
                                        for pregunta in e.preguntas_directivoarea(area):
                                            ws_evaluacion_directivo.write_merge(fila, fila, 4, 6,
                                                                                elimina_tildes(pregunta.nombre))
                                            col = 6
                                            for r in e.respuestas():
                                                descripcion = 'no'
                                                respuesta = pregunta.tiene_respuesta_directivo(evaluaciondirectivo)
                                                if respuesta:
                                                    if respuesta.respuesta == r:
                                                        descripcion = 'si'
                                                col += 1
                                                ws_evaluacion_directivo.write(fila, col, elimina_tildes(descripcion))

                                            fila += 1
                                else:
                                    for p in e.preguntas_directivo():
                                        col = 6
                                        ws_evaluacion_directivo.write_merge(fila, fila, 4, col,
                                                                            elimina_tildes(p.nombre))
                                        for r in e.respuestas():
                                            descripcion = 'no'
                                            respuesta = p.tiene_respuesta_directivo(evaluaciondirectivo)
                                            if respuesta:
                                                if respuesta.respuesta == r:
                                                    descripcion = 'si'
                                            col += 1
                                            ws_evaluacion_directivo.write(fila, col, elimina_tildes(descripcion))
                                        fila += 1
                                fila += 1

                        else:
                            ws_evaluacion_directivo.write(fila, 0, "NO EXISTE EVALUACIÓN DE DIRECTIVO")
                            fila = fila + 1

                    fila += 1
                    ws_evaluacion_directivo.write(fila, 0, "Fecha Impresión", subtitulo)
                    ws_evaluacion_directivo.write(fila, 1, str(datetime.now()), subtitulo)
                    ws_evaluacion_directivo.write(fila + 1, 0, "Usuario", subtitulo)
                    ws_evaluacion_directivo.write(fila + 1, 1, str(request.user), subtitulo)

                    nombre = 'resultadoevaluacionindividual' + str(datetime.now()).replace(" ", "").replace(".",
                                                                                                            "").replace(
                        ":", "") + '.xls'
                    wb.save(MEDIA_ROOT + '/reporteexcel/' + nombre)
                    return HttpResponse(json.dumps({"result": "ok", "url": "/media/reporteexcel/" + nombre}),
                                        content_type="application/json")

                except Exception as ex:
                    print(ex)
                    return HttpResponse(json.dumps({"result": "bad", "message": ex}), content_type="application/json")

    else:
        data = {'title': ''}
        addUserData(request, data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action == 'verevalalumno':
                try:
                    if Profesor.objects.filter(pk=request.GET['profesor']).exists():
                        profesor = Profesor.objects.filter(pk=request.GET['profesor'])[:1].get()
                        if Periodo.objects.filter(pk=request.GET['periodo']).exists():
                            periodo = Periodo.objects.filter(pk=request.GET['periodo'])[:1].get()
                            if EvaluacionAlumno.objects.filter(profesormateria__profesor=profesor,
                                                               materia__nivel__periodo=periodo).exists():
                                eval = EvaluacionAlumno.objects.filter(profesormateria__profesor=profesor,
                                                                       materia__nivel__periodo=periodo)[
                                       :1].get().evaluaciondocente
                                ejes = DetalleEvaluacionPregunta.objects.filter(evaluacion=eval).values('eje')
                                data['ejes'] = EjesEvaluacion.objects.filter(id__in=ejes)
                                data['evaluacion'] = eval
                                data['profesor'] = profesor
                                if EvaluacionDirectivoPeriodo.objects.filter(evaluaciondocenteperiodo__periodo=periodo, evaluaciondocenteperiodo__profesor=profesor).exists():
                                    evaluaciondirectivo=EvaluacionDirectivoPeriodo.objects.filter(evaluaciondocenteperiodo__periodo=periodo, evaluaciondocenteperiodo__profesor=profesor)[:1].get()
                                    data['evaluaciondirectivo']=evaluaciondirectivo
                                data['periodo'] = periodo
                                if 'acc' in request.GET:
                                    data['acc'] = request.GET['acc']
                                return render(request ,"evaluacionesdirectivo/evaluaciondocenteprofe.html" ,  data)
                except Exception as ex:
                    print(ex)


            if action == 'verevaldocente':
                try:
                    print(request.GET)
                    # data = {'title': ''}
                    # data['acc'] = request.GET['acc']
                    if 'profesor' in request.GET:
                        profesor = Profesor.objects.get(id=request.GET['profesor'])
                    else:
                        profesor = Profesor.objects.get(persona=data['persona'])
                    if 'op' in request.GET:
                        data['op'] = request.GET['op']

                    if 'eval' in request.GET:
                        periodoeval = PeriodoEvaluacion.objects.filter(periodo__id=request.GET['periodo'],evaluaciondoc__id=request.GET['eval'])[:1].get()
                    else:
                        periodoeval = PeriodoEvaluacion.objects.filter(periodo__id=request.GET['periodo'],evaluaciondoc__docente=True,evaluaciondoc__estado=True)[:1].get()
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
                    data['evaluacion'] = True
                    data['profesor'] = profesor
                    data['evaluaciondoc'] = evaluacion
                    if 'opver' in request.GET:
                        data['opver'] = 'opver'
                    if 'resul' in request.GET:
                        data['resul'] = 'resul'
                        data['periodoevalu'] = periodoeval.periodo.id

                    return render(request ,"doc_evaluaciondocente/evaluaciondocente.html" ,  data)
                except Exception as e:
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}),
                                        content_type="application/json")
            if action == 'verevaldirectivo':

                try:
                    periodoeval=None
                    if Profesor.objects.filter(pk=request.GET['profesor']).exists():
                        profesor = Profesor.objects.filter(pk=request.GET['profesor'])[:1].get()
                        if Periodo.objects.filter(pk=request.GET['periodo']).exists():
                            periodo = Periodo.objects.filter(pk=request.GET['periodo'])[:1].get()

                            periodoeval = EvaluacionDocentePeriodo.objects.filter(profesor=profesor, periodo=periodo)[:1].get()
                            if EvaluacionCargoPeriodo.objects.filter(personaevaluada=profesor.persona).exists():
                                evaluacion = EvaluacionDocente.objects.filter(directivocargo=True, estado=True)[:1].get()
                                evaluaciondecano=EvaluacionCargoPeriodo.objects.filter(personaevaluada=profesor.persona)[:1].get()
                                ejes = DetalleEvaluacionPregunta.objects.filter(evaluacion=evaluacion).values('eje')
                                data['ejes'] = EjesEvaluacion.objects.filter(id__in=ejes).order_by('id')
                                data['evaluacioncargo'] = evaluaciondecano
                                data['evaluaciondoc'] = evaluacion
                                data['resultado']=1
                                data['evaluacion'] = True
                                data['persona'] = profesor.persona
                                data['periodo'] = periodo

                                return render(request,'evaluacionesdirectivo/evaluarcoordinadordecano.html', data)
                            else:
                                if EvaluacionDocente.objects.filter(directivo=True, estado=True).exists():
                                    evaluaciondoc=EvaluacionDocente.objects.filter(directivo=True, estado=True)[:1].get()

                                    if EvaluacionDirectivoPeriodo.objects.filter(evaluaciondocenteperiodo=periodoeval,evaluaciondocente=evaluaciondoc, activo=True).exists():
                                        evaluaciondirectivo = EvaluacionDirectivoPeriodo.objects.filter(evaluaciondocenteperiodo=periodoeval,evaluaciondocente=evaluaciondoc,activo=True)[:1].get()
                                    else:
                                        evaluaciondirectivo = EvaluacionDirectivoPeriodo(evaluaciondocenteperiodo=periodoeval,evaluaciondocente=evaluaciondoc,fecha=datetime.now())
                                        evaluaciondirectivo.save()
                                        for e in DetalleEvaluacionPregunta.objects.filter(evaluacion=evaluaciondoc):
                                            if not DetalleEvaluacionDirectivo.objects.filter(evaluacion=evaluaciondirectivo,pregunta=e.pregunta).exists() and not evaluaciondirectivo.finalizado:
                                                d = DetalleEvaluacionDirectivo(evaluacion=evaluaciondirectivo,pregunta=e.pregunta)
                                                d.save()
                            # else:
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
                            data['periodo'] = periodo

                            data['evaluacion'] = True

                            if 'resul' in request.GET:
                                data['resul']='resul'
                                data['periodoevalu'] = periodoeval.periodo.id
                            return render(request ,"evaluacionesdirectivo/evaluardirectivo.html" ,  data)
                except Exception as e:
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}),
                                        content_type="application/json")

        else:
            periodo = None
            profesor = None
            search = None
            try:
                coordinadores = CoordinadorCarreraPeriodo.objects.filter().values('persona')
                decano = None
                persona = Persona.objects.filter(usuario= request.user)[:1].get()

                if Coordinacion.objects.filter(persona= persona).exists():

                    coordinacion = Coordinacion.objects.filter(persona=persona, estado=True).order_by('nombre')
                    data['coordinacion']=coordinacion
                    for cord in coordinacion:
                        carrera = cord.fun_carrera().values('id')
                        if EvaluacionCoordinadorDocente.objects.filter(coordinador__carrera__id__in = carrera).exists():
                            decano = EvaluacionCoordinadorDocente.objects.filter(coordinador__carrera__id__in = carrera).values('profesor')
                if 'periodo' in request.GET:

                    if (request.GET['periodo']) != '':
                        periodo=Periodo.objects.filter(pk=request.GET['periodo'])[:1].get()

                        if EvaluacionDocentePeriodo.objects.filter(periodo=periodo).exists():
                            profesor = EvaluacionDocentePeriodo.objects.filter(periodo=periodo, finalizado=True).distinct(
                                'profesor').values('profesor')
                            profesor = Profesor.objects.filter(id__in=profesor).order_by('persona__apellido1')
                            data['profesor'] = profesor
                            data['periodo'] = periodo

                            profesorma=ProfesorMateria.objects.filter(materia__nivel__periodo=periodo).values('materia__nivel__carrera')

                            data['carreras'] = Carrera.objects.filter(id__in=profesorma,activo=True)
                        if 'carrera' in request.GET:
                            if (request.GET['carrera']) != '':
                                periodo=Periodo.objects.filter(pk=request.GET['periodo'])[:1].get()
                                carrera=Carrera.objects.filter(pk=request.GET['carrera'])[:1].get()
                                profesorma=EvaluacionCoordinadorDocente.objects.filter(coordinador__carrera=carrera).values('profesor__id')
                                profeeva=EvaluacionDocentePeriodo.objects.filter(periodo=periodo, finalizado=True,profesor__id__in=profesorma).values('profesor')
                                profesor = Profesor.objects.filter(id__in=profeeva).order_by('persona__apellido1')
                                data['profesor'] = profesor
                                data['carrera'] = carrera
                                data['periodo'] = periodo
                        data['contador'] = profesor.count()


                    if decano:
                        profesor = profesor.filter(id__in = decano)
                        data['contador'] = profesor.count()
                        profesorid = profesor.filter().values('persona')
                        coord = coordinadores.filter(persona__id__in = profesorid).values('carrera')
                        data['car'] = Carrera.objects.filter(id__in = coord)
                        data['decano']=1

                    # elif coordinadores:
                    #     profesor= profesor.filter().exclude(persona__id__in=coordinadores)
                    #     data['contador'] = profesor.count()

                    else:
                         data['contador'] = profesor.count()
                    if 's' in request.GET:
                        search = request.GET['s']
                    if search:
                        data['search'] = search
                        ss = search.split(' ')
                        while '' in ss:
                            ss.remove('')
                        if len(ss) == 1:
                            inprof = Profesor.objects.filter(Q(persona__nombres__icontains=search) | Q(
                                persona__apellido1__icontains=search) | Q(
                                persona__apellido2__icontains=search) | Q(
                                persona__cedula__icontains=search) | Q(
                                persona__pasaporte__icontains=search)).values('id').distinct('id')
                            profesor = Profesor.objects.filter(id__in=inprof, evaluaciondocenteperiodo__periodo__id=request.GET['periodo']).order_by('persona__apellido1')
                        else:
                            profesor = Profesor.objects.filter(Q(persona__apellido1__icontains=ss[0]) & Q(
                                persona__apellido2__icontains=ss[1])).order_by('persona__apellido1',
                                                                               'persona__apellido2',
                                                                           'persona__nombres')
                    paging = MiPaginador(profesor, 30)
                # print(paging)
                    p = 1
                    try:
                        if 'page' in request.GET:
                            p = int(request.GET['page'])
                        page = paging.page(p)
                    except:
                        page = paging.page(1)
                    data['page'] = page
                    data['paging'] = paging
                    data['rangospaging'] = paging.rangos_paginado(p)
                    data['profesor'] = page.object_list
                evaperiodo=EvaluacionDocentePeriodo.objects.filter().values('periodo')
                periodo = Periodo.objects.filter(id__in=evaperiodo)
                data['periodos'] = periodo
                data['puedetodo'] = True
                data['profesor'] = profesor
                data ["carreras_priodos"] = Carrera.objects.filter(activo =True).order_by("nombre")

                return render(request ,"evaluacionesdirectivo/evaluacionesdirectivo.html" ,  data)

            except Exception as e:
                print(e)
                return HttpResponseRedirect("/resultadosevaluacion?info="+str(e))
