from datetime import datetime
import json
from django.core.paginator import Paginator
from django.utils.encoding import force_str


from django.contrib.admin.models import LogEntry, DELETION, CHANGE, ADDITION
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import RequestContext



# @secure_module
import xlwt
from settings import MEDIA_ROOT

from sga.commonviews import ip_client_address, addUserData
from sga.estudiantesxdesertar import MiPaginador
from sga.forms import EvaluacionDocenteForms, AsignaEvaluacionForm
from sga.models import EvaluacionDocente, EvaluacionMateria, Materia, EjesEvaluacion, PreguntasEvaluacion, DetalleEvaluacionPregunta, EvaluacionAlumno, Profesor, TituloInstitucion, elimina_tildes, Periodo, Carrera, CoordinadorCarrera, Inscripcion, PeriodoEvaluacion, AreasElementosEvaluacion, ProfesorMateria, viewHorasClase, EvaluacionCoordinadorDocente, Persona, CoordinadorCarreraPeriodo, EvaluacionDocentePeriodo, DetalleEvaluacionDocente, Matricula, MateriaAsignada, DetalleEvaluacionAlumno, EvaluacionDirectivoPeriodo

def busqueda(search, evaluacion):
    if search:
        ss = search.split(' ')
        while '' in ss:
            ss.remove('')
        if len(ss) == 1:
            query = EvaluacionCoordinadorDocente.objects.filter(
                Q(profesor__persona__apellido1__icontains=search)|
                Q(profesor__persona__apellido2__icontains=search)|
                Q(profesor__persona__nombres__icontains=search),
                evaluacion__id =  evaluacion).order_by(
                    'profesor__persona__apellido1','profesor__persona__apellido2','profesor__persona__nombres')
        else:
            query = EvaluacionCoordinadorDocente.objects.filter(
                Q(profesor__persona__apellido1__icontains=ss[0]) &
                Q(profesor__persona__apellido2__icontains=ss[1]) |
                Q(profesor__persona__nombres__icontains=ss[0]),
                evaluacion__id=evaluacion).order_by(
                'profesor__persona__apellido1', 'profesor__persona__apellido2', 'profesor__persona__nombres')
    else:
        query = EvaluacionCoordinadorDocente.objects.filter(
            evaluacion__id=evaluacion).order_by(
            'profesor__persona__apellido1', 'profesor__persona__apellido2', 'profesor__persona__nombres')

    # if query:
    #     query = eval('query.filter(%s)'%(sql))
    return query


def view(request):

    if request.method=='POST':

        if 'action' in request.POST:
            action = request.POST['action']
            if action == 'addcoordinador':
                data = {'title': ''}
                try:

                    evaluacioncoordinadordocente =EvaluacionCoordinadorDocente.objects.get(id = int(request.POST['evacorpro']))
                    evaluacioncoordinadordocente.coordinador_id = int(request.POST['coordinador_id'])
                    evaluacioncoordinadordocente.save()
                    client_address = ip_client_address(request)
                    # Log de AGREGACION EvaluacionCoordinadorDocente
                    LogEntry.objects.log_action(
                        user_id=request.user.pk,
                        content_type_id=ContentType.objects.get_for_model(evaluacioncoordinadordocente).pk,
                        object_id=evaluacioncoordinadordocente.id,
                        object_repr=force_str(evaluacioncoordinadordocente),
                        action_flag=ADDITION,
                        change_message='Agregacion Evaluacion Coordinador Docente ' + ' (' + client_address + ')')

                    data['result'] = 'ok'
                    return HttpResponse(json.dumps(data), content_type="application/json")
                except Exception as e:
                    print(e)
                    return HttpResponse(json.dumps({'result': 'Error al registrar el coordinador', 'error': str(e)}),
                                        content_type="application/json")
            if action == 'reporteevalprofesor':

                try:
                    carrera = None
                    periodo = None
                    # if int(request.POST['carrera']) > 0:
                    #     carrera = int(request.POST['carrera'])
                    # if int(request.POST['periodo']) > 0:
                    #     periodo = int(request.POST['periodo'])

                    profesor = Profesor.objects.get(id=request.POST['id'])
                    evaluacion = EvaluacionDocente.objects.filter(pk=request.POST['evalid'])[:1].get()
                    evaluaciones= EvaluacionAlumno.objects.filter(evaluaciondocente=evaluacion,profesormateria__profesor=profesor)
                    idejes = DetalleEvaluacionPregunta.objects.filter(evaluacion=evaluacion).values('eje')

                    ejes = EjesEvaluacion.objects.filter(id__in=idejes)



                    m = 12
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2_v1 = xlwt.easyxf('font: bold on; align: wrap off, vert centre, horiz center')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    subtitulo2 = xlwt.easyxf('align:vert centre, horiz center')
                    titulo.font.height = 20 * 11
                    titulo2.font.height = 20 * 11
                    titulo2_v1.font.height = 20 * 11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20 * 10
                    subtitulo2.font.height = 20 * 10
                    style1 = xlwt.easyxf('', num_format_str='DD-MMM-YY')
                    wb = xlwt.Workbook()

                    ws = wb.add_sheet('Informacion', cell_overwrite_ok=True)
                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0, 0, m + 2, tit.nombre, titulo2)
                    ws.write_merge(1, 1, 0, m + 2, str(evaluacion) , titulo2_v1)
                    # ws.write_merge(1, 1, 0, m + 2, 'DATOS DE ESTUDIANTES: ' + elimina_tildes(materia.asignatura.id), titulo)
                    ws.write(3, 0, 'Profesor: ', titulo)
                    ws.write(3, 1, elimina_tildes(profesor.persona.nombre_completo()), titulo)

                    if periodo:
                        ws.write(4, 0, 'Periodo: ', titulo)
                        ws.write(4, 1, str(Periodo.objects.get(pk=periodo).nombre), titulo)

                    if carrera:
                        if periodo:
                            ws.write(5, 0, 'Carrera: ', titulo)
                            ws.write(5, 1, str(Carrera.objects.get(pk = carrera).nombre), titulo)
                        else:
                            ws.write(4, 0, 'Carrera: ', titulo)
                            ws.write(4, 1, str(Carrera.objects.get(pk=carrera).nombre), titulo)
                    fila = 7
                    for e in ejes:
                        ws.write_merge(fila, fila, 0, 4, elimina_tildes(e.descripcion), subtitulo)
                        colum = 5

                        for r in e.respuestas():
                            ws.write_merge(fila, fila,colum, colum+1, elimina_tildes(r.respuesta.nombre), titulo2)
                            colum = colum + 2
                        fila = fila + 1

                        for p in e.preguntas_alumno():
                            ws.write_merge(fila, fila, 1, 4, elimina_tildes(p.nombre))
                            colum = 5
                            for r in e.respuestas():
                                ws.write_merge(fila, fila,colum, colum+1, str(r.cantidad_respuesta(evaluacion,p,profesor,carrera,periodo)), subtitulo2)
                                colum = colum + 2
                            fila = fila + 1
                    fila = fila + 2
                    ws.write(fila, 0, "Fecha Impresion", subtitulo)
                    ws.write(fila, 1, str(datetime.now()), subtitulo)
                    ws.write(fila + 1, 0, "Usuario", subtitulo)
                    ws.write(fila + 1, 1, str(request.user), subtitulo)

                    nombre ='evaluacionprofesordatos'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    print(44)
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    print(55)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}), content_type="application/json")
                    # nombre = 'evaluacionprofesor' + str(datetime.now()).replace(" ", "").replace(".", "").replace(":", "") + '.xls'
                    # wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    # return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as e:
                    print(e)
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}), content_type="application/json")

            if action == 'addevamat':
                evaluacion = EvaluacionDocente.objects.filter(id=request.POST['id'])[:1].get()
                f = AsignaEvaluacionForm(request.POST)
                if f.is_valid():
                    if request.POST['materiasid'] != '':
                        for a in request.POST['materiasid'].split(","):
                            if Materia.objects.filter(id=a).exists():
                                materia = Materia.objects.filter(id=a)[:1].get()
                                if not EvaluacionMateria.objects.filter(evaluaciondocente=evaluacion,
                                                                          materia=materia).exists():
                                    evaluacionmateria = EvaluacionMateria(evaluaciondocente=evaluacion,
                                                                          materia=materia)
                                    evaluacionmateria.save()

                    if request.POST['nivelesid'] != '':
                        for a in request.POST['nivelesid'].split(","):
                            if Materia.objects.filter(nivel__id=a).exists():
                                materia = Materia.objects.filter(nivel__id=a,cerrado=True)
                                for m in materia:

                                    if not EvaluacionMateria.objects.filter(materia=m,
                                                                            evaluaciondocente=evaluacion).exists():
                                        evaluacionmateria = EvaluacionMateria(materia=m,
                                                                              evaluaciondocente=evaluacion)
                                        evaluacionmateria.save()
                if 'op' in request.POST:

                    return HttpResponseRedirect(
                        "/evaluacionesdocentes$?action=ver&acc="+ request.POST['acc']+"&id="+str(evaluacion.id))
                else:
                    return HttpResponseRedirect(
                        "/evaluacionesdocentes$?acc=" + request.POST['acc'] + "&info=SE AGREGO CORRECTAMENTE")
            if action == 'addperiodoeval':
                data = {'title': ''}
                lisFormacion = []
                try:
                    if EvaluacionDocente.objects.filter(pk=request.POST['evaluacion']).exists():
                        evaluacion= EvaluacionDocente.objects.filter(pk=request.POST['evaluacion'])[:1].get()

                        if Periodo.objects.filter(pk=request.POST['periodo']).exists():
                            periodo=Periodo.objects.filter(pk=request.POST['periodo'])[:1].get()

                            if not PeriodoEvaluacion.objects.filter( evaluaciondoc=evaluacion, periodo=periodo).exists():
                                pereva = PeriodoEvaluacion(evaluaciondoc=evaluacion,periodo=periodo,activo=True)
                                pereva.save()

                                msj = 'Guardado registro'
                                client_address = ip_client_address(request)
                                LogEntry.objects.log_action(
                                    user_id=request.user.pk,
                                    content_type_id=ContentType.objects.get_for_model(pereva).pk,
                                    object_id=pereva.id,
                                    object_repr=force_str(pereva),
                                    action_flag=ADDITION,
                                    change_message=msj + ' (' + client_address + ')')

                                data['result'] = 'ok'
                                for a in PeriodoEvaluacion.objects.filter(evaluaciondoc=evaluacion):
                                    lisFormacion.append(
                                        {"id": a.id, "nombre": a.periodo.nombre, 'inicio': str(a.periodo.inicio), "fin":str(a.periodo.fin), "tipo": a.periodo.tipo.nombre })
                                data['lisFormacion']=lisFormacion
                                return HttpResponse(json.dumps(data), content_type="application/json")
                            else:
                                data['bad']='bad'
                                return HttpResponse(json.dumps(data), content_type="application/json")
                except Exception as e:
                    return HttpResponseRedirect("/evaluacionesdocentes?error="+str(e))
            if action == 'eliminarperiodo':
                data = {'title': ''}
                try:
                    lisFormacion = []

                    if PeriodoEvaluacion.objects.filter(pk=request.POST['idperiodo']).exists():

                        periodo=PeriodoEvaluacion.objects.filter(pk=request.POST['idperiodo'])[:1].get()
                        if not EvaluacionDocentePeriodo.objects.filter(periodo=periodo.periodo).exists():
                            evaluacion=EvaluacionDocente.objects.filter(pk=request.POST['evaluacion'])[:1].get()
                            client_address = ip_client_address(request)

                            LogEntry.objects.log_action(
                                user_id=request.user.pk,
                                content_type_id=ContentType.objects.get_for_model(periodo).pk,
                                object_id=periodo.id,
                                object_repr=force_str(periodo),
                                action_flag=DELETION,
                                change_message='Eliminada pregunta (' + client_address + ')')
                            periodo.delete()
                            for a in PeriodoEvaluacion.objects.filter(evaluaciondoc=evaluacion):
                                lisFormacion.append(
                                    {"id": a.id, "nombre": a.periodo.nombre, 'inicio': str(a.periodo.inicio), "fin":str(a.periodo.fin), "tipo": a.periodo.nombre })
                            data['lisFormacion']=lisFormacion

                            return HttpResponse(json.dumps({'result': 'ok','lisFormacion':lisFormacion}), content_type="application/json")
                        else:
                            return HttpResponse(json.dumps({'result': 'badperiodo','message':'Ya existe evaluaciones registradas en este periodo'}), content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({'result': 'error2','message':'Ya existe una pregunta registrada en otra tabla'}), content_type="application/json")
                except Exception as e:
                    msn = str(e)
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(msn)}), content_type="application/json")
            if action == 'cargarmaterias':
                try:
                    evaluacion = EvaluacionDocente.objects.filter(id=request.POST['id'],docente=False, directivo=False)[:1].get()
                    if PeriodoEvaluacion.objects.filter().exists():
                        periodo=PeriodoEvaluacion.objects.filter().values('periodo_id')
                        if Materia.objects.filter(cerrado=True, nivel__periodo__id__in=periodo).exists():
                            for materia in Materia.objects.filter(cerrado=True, nivel__periodo__id__in=periodo):
                                if not EvaluacionMateria.objects.filter(evaluaciondocente=evaluacion,
                                                                          materia=materia).exists():
                                    evaluacionmateria = EvaluacionMateria(evaluaciondocente=evaluacion,
                                                                          materia=materia)
                                    evaluacionmateria.save()
                            return HttpResponse(json.dumps({'result': 'ok'}), content_type="application/json")
                        else:
                            return HttpResponse(json.dumps({'result': 'badmateria'}), content_type="application/json")
                except Exception as e:
                    return HttpResponse(
                        json.dumps({'result': 'bad', 'message': "Ocurrio un error (" + str(e) + ")"}),
                        content_type="application/json")

            if action == 'cambiaestadoeval':
                try:
                    lisFormacion = []
                    data = {'title': ''}
                    eval = EvaluacionDocente.objects.get(pk=request.POST['id'])

                    eval.estado = not eval.estado
                    eval.save()
                    client_address = ip_client_address(request)

                    # Log Editar Inscripcion
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(eval).pk,
                        object_id       = eval.id,
                        object_repr     = force_str(eval),
                        action_flag     = CHANGE,
                        change_message  = "Cambio de estado a: "+ str(eval.estado) +  '(' + client_address + ')' )

                    return HttpResponse(json.dumps({'result': 'ok' }),
                                        content_type="application/json")
                except Exception as e:
                    msn = str(e)
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(msn)}), content_type="application/json")


            if action == 'actualizar':

                # evaluaciond = EvaluacionDocente.objects.filter(id=request.POST['id'])[:1].get()
                try:
                    if PeriodoEvaluacion.objects.filter(id=request.POST['id']).exists():
                        p=PeriodoEvaluacion.objects.filter(id=request.POST['id'])[:1].get()

                        # print(p)
                        profesorsid= EvaluacionCoordinadorDocente.objects.filter(evaluacion=p).values('profesor')

                        for d in Profesor.objects.filter(id__in=ProfesorMateria.objects.filter(materia__nivel__periodo__id=p.periodo.id).exclude(profesor__id__in=profesorsid).values('profesor')):
                            coordinador=None
                            if viewHorasClase.objects.filter(periodo=p.periodo.id,profeid=d.id).exists():
                                horas = viewHorasClase.objects.filter(periodo=p.periodo.id, profeid=d.id).order_by('-total')[:1].get()
                                if not viewHorasClase.objects.filter(periodo=p.periodo.id, profeid=d.id,total=horas.total).exclude(id=horas.id).exists():
                                    if CoordinadorCarreraPeriodo.objects.filter(carrera__id=horas.carrera).exists():
                                        coordinador = CoordinadorCarreraPeriodo.objects.filter(carrera__id=horas.carrera)[:1].get()
                            if not EvaluacionCoordinadorDocente.objects.filter(profesor=d,evaluacion=p).exists():
                                cordinadoreval = EvaluacionCoordinadorDocente(coordinador=coordinador,
                                                                              profesor=d,
                                                                              evaluacion=p)

                                cordinadoreval.save()
                        return HttpResponse(
                            json.dumps({'result': 'ok'}),
                            content_type="application/json")
                except Exception as e:
                    print(e)
                    return HttpResponse(
                        json.dumps({'result': 'bad', 'message': "Ocurrio un error (" + str(e) + ")"}),
                        content_type="application/json")

            if action == 'addevaluacion':
                e = EvaluacionDocenteForms(request.POST)
                if e.is_valid():
                    docente=False
                    directivo=False
                    decano=False
                    op =request.POST['op']
                    if op == '1':
                        docente=False
                        directivo=False
                        decano=False
                    if op == '2':
                        docente=True
                        directivo=False
                        decano=False
                    if op == '3':
                        docente=False
                        directivo=True
                        decano=False
                    if op == '4':
                        docente=False
                        directivo=False
                        decano=True

                    if not EvaluacionDocente.objects.filter(descripcion=request.POST['descripcion']).exists():
                        evaluacion=EvaluacionDocente(estado=e.cleaned_data['estado'],docente=docente,directivo=directivo,directivocargo=decano,
                                                     fechacreacion=datetime.now(),
                                                     usauriocrea=request.user,
                                                     descripcion=e.cleaned_data['descripcion']
                                                     )
                        evaluacion.save()

                        if request.POST['ejeid'] != '':
                            for a in request.POST['ejeid'].split(","):
                                if EjesEvaluacion.objects.filter(id=a).exists():
                                    eje = EjesEvaluacion.objects.filter(id=a)[:1].get()
                                    if PreguntasEvaluacion.objects.filter(eje=eje).exists():
                                        # pregunta=PreguntasEvaluacion.objects.filter(eje=eje)[:1].get()
                                        for p in PreguntasEvaluacion.objects.filter(eje=eje):

                                            if not DetalleEvaluacionPregunta.objects.filter(evaluacion=evaluacion,eje=eje, pregunta=p).exists():
                                                eval = DetalleEvaluacionPregunta(evaluacion=evaluacion,
                                                                                 eje=eje,
                                                                                 pregunta=p,
                                                                                 estado=True)
                                                eval.save()

                    return HttpResponseRedirect("/evaluacionesdocentes" )



            if action == 'eliminar':
                try:
                    evaluacion=EvaluacionDocente.objects.filter(pk=request.POST['id'])[:1].get()
                    if not EvaluacionMateria.objects.filter(evaluaciondocente=evaluacion).exists() and not EvaluacionAlumno.objects.filter(evaluaciondocente=evaluacion).exists()  :
                        if not EvaluacionDocentePeriodo.objects.filter(evaluaciondocente=evaluacion).exists():
                            if not EvaluacionDirectivoPeriodo.objects.filter(evaluaciondocente=evaluacion).exists():
                                client_address = ip_client_address(request)
                                LogEntry.objects.log_action(
                                    user_id=request.user.pk,
                                    content_type_id=ContentType.objects.get_for_model(evaluacion).pk,
                                    object_id=evaluacion.id,
                                    object_repr=force_str(evaluacion),
                                    action_flag=DELETION,
                                    change_message='Eliminada Evaluacion Docente(' + client_address + ')')
                                evaluacion.delete()

                                return HttpResponse(json.dumps({'result': 'ok'}), content_type="application/json")
                            else:
                                return HttpResponse(
                                    json.dumps({'result': 'bad',
                                                'message': "No se puede eliminar la evaluacion. ya existen datos asociados a la evaluacion"}),
                                    content_type="application/json")
                        else:
                            return HttpResponse(
                                json.dumps({'result': 'bad',
                                            'message': "No se puede eliminar la evaluacion. ya existen datos asociados a la evaluacion"}),
                                content_type="application/json")
                    else:
                        return HttpResponse(
                            json.dumps({'result': 'bad',
                                        'message': "No se puede eliminar la evaluacion. ya existen datos asociados a la evaluacion"}),
                            content_type="application/json")
                except Exception as e:
                    return HttpResponse(
                        json.dumps({'result': 'bad', 'message': "Ocurrio un error (" + str(e) + ")"}),
                        content_type="application/json")
            elif action == 'eliminarmateria':
                try:

                    evamateria = EvaluacionMateria.objects.get(id=request.POST['id'])
                    if not EvaluacionAlumno.objects.filter(materia=evamateria.materia).exists():

                        # Obtain client ip address
                        client_address = ip_client_address(request)

                        # Log de EDITAR GRUPO
                        LogEntry.objects.log_action(
                            user_id=request.user.pk,
                            content_type_id=ContentType.objects.get_for_model(evamateria).pk,
                            object_id=evamateria.id,
                            object_repr=force_str(evamateria),
                            action_flag=DELETION,
                            change_message='Eliminada Materia de Evaluacion (' + client_address + ')')
                        evamateria.delete()

                        return HttpResponse(json.dumps({'result': 'ok'}), content_type="application/json")
                    else:
                        return HttpResponse(
                            json.dumps({'result': 'bad', 'message': "No se puede eliminar la materia. ya existen evaluaciones realizadas"}),
                            content_type="application/json")
                except Exception as e:
                    return HttpResponse(
                        json.dumps({'result': 'bad', 'message': "Ocurrio un error (" + str(e) + ")"}),
                        content_type="application/json")
            if action=='generarexceldocente':
                try:
                    carrera = None
                    periodo = None
                    # if int(request.POST['carrera']) > 0:
                    #     carrera = int(request.POST['carrera'])
                    # if int(request.POST['periodo']) > 0:
                    #     periodo = int(request.POST['periodo'])

                    periodo = PeriodoEvaluacion.objects.get(id=request.POST['periodo'])
                    evaluacion=EvaluacionDocente.objects.get(docente=True, estado=True)
                    evaluaciondocente = EvaluacionDocentePeriodo.objects.filter(periodo=periodo.periodo, evaluaciondocente=evaluacion)



                    m = 12
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2_v1 = xlwt.easyxf('font: bold on; align: wrap off, vert centre, horiz center')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    subtitulo2 = xlwt.easyxf('align:vert centre, horiz center')
                    titulo.font.height = 20 * 11
                    titulo2.font.height = 20 * 11
                    titulo2_v1.font.height = 20 * 11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20 * 10
                    subtitulo2.font.height = 20 * 10
                    style1 = xlwt.easyxf('', num_format_str='DD-MMM-YY')
                    wb = xlwt.Workbook()

                    ws = wb.add_sheet('Informacion', cell_overwrite_ok=True)
                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0, 0, m + 2, tit.nombre, titulo2)
                    ws.write_merge(1, 1, 0, m + 2, 'EVALUACIONDES DOCENTES' , titulo2_v1)
                    # ws.write_merge(1, 1, 0, m + 2, 'DATOS DE ESTUDIANTES: ' + elimina_tildes(materia.asignatura.id), titulo)

                    ws.write(3, 0, 'Periodo: ', titulo)
                    ws.write(3, 1, periodo.periodo.nombre, titulo)

                    ws.write(6, 0, 'NOMBRES', subtitulo)
                    ws.write(6, 1, 'APELLIDOS', subtitulo)
                    ws.write(6, 2, 'CEDULA', subtitulo)
                    ws.write(6, 3, 'FECHA', subtitulo)
                    ws.write(6, 4, 'FINALIZADO', subtitulo)

                    fila=7
                    for eva in evaluaciondocente:
                        if eva.profesor.persona.nombres:
                            ws.write(fila, 0, eva.profesor.persona.nombres)
                        if eva.profesor.persona.apellido1:
                            ws.write(fila, 1, eva.profesor.persona.apellido1 + ' ' +  eva.profesor.persona.apellido2)
                        if eva.profesor.persona.cedula:
                            ws.write(fila, 2, eva.profesor.persona.cedula)
                        else:
                            if eva.profesor.persona.pasaporte:
                                ws.write(fila, 2, eva.profesor.persona.pasaporte)
                            else:
                                ws.write(fila, 2, '')
                        if eva.fecha:
                            ws.write(fila, 3, str(eva.fecha))
                        if eva.finalizado:
                            ws.write(fila, 4, 'SI')
                        else:
                            ws.write(fila, 4, 'NO')

                        fila=fila+1
                    ws.write(fila, 0, "Fecha Impresion", subtitulo)
                    ws.write(fila, 1, str(datetime.now()), subtitulo)
                    ws.write(fila + 1, 0, "Usuario", subtitulo)
                    ws.write(fila + 1, 1, str(request.user), subtitulo)

                    nombre = 'evaluaciondocente' + str(datetime.now()).replace(" ", "").replace(".", "").replace(":", "") + '.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as e:
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}), content_type="application/json")
            elif action == 'reporteevalprofesor':
                try:
                    carrera = None
                    periodo = None
                    # if int(request.POST['carrera']) > 0:
                    #     carrera = int(request.POST['carrera'])
                    # if int(request.POST['periodo']) > 0:
                    #     periodo = int(request.POST['periodo'])

                    profesor = Profesor.objects.get(id=request.POST['id'])
                    evaluacion = EvaluacionDocente.objects.filter(pk=request.POST['evalid'])[:1].get()
                    evaluaciones= EvaluacionAlumno.objects.filter(evaluaciondocente=evaluacion,profesormateria__profesor=profesor)
                    idejes = DetalleEvaluacionPregunta.objects.filter(evaluacion=evaluacion).values('eje')

                    ejes = EjesEvaluacion.objects.filter(id__in=idejes)



                    m = 12
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2_v1 = xlwt.easyxf('font: bold on; align: wrap off, vert centre, horiz center')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    subtitulo2 = xlwt.easyxf('align:vert centre, horiz center')
                    titulo.font.height = 20 * 11
                    titulo2.font.height = 20 * 11
                    titulo2_v1.font.height = 20 * 11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20 * 10
                    subtitulo2.font.height = 20 * 10
                    style1 = xlwt.easyxf('', num_format_str='DD-MMM-YY')
                    wb = xlwt.Workbook()

                    ws = wb.add_sheet('Informacion', cell_overwrite_ok=True)
                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0, 0, m + 2, tit.nombre, titulo2)
                    ws.write_merge(1, 1, 0, m + 2, str(evaluacion) , titulo2_v1)
                    # ws.write_merge(1, 1, 0, m + 2, 'DATOS DE ESTUDIANTES: ' + elimina_tildes(materia.asignatura.id), titulo)
                    ws.write(3, 0, 'Profesor: ', titulo)
                    ws.write(3, 1, elimina_tildes(profesor.persona.nombre_completo()), titulo)
                    if periodo:
                        ws.write(4, 0, 'Periodo: ', titulo)
                        ws.write(4, 1, str(Periodo.objects.get(pk=periodo).nombre), titulo)

                    if carrera:
                        if periodo:
                            ws.write(5, 0, 'Carrera: ', titulo)
                            ws.write(5, 1, str(Carrera.objects.get(pk = carrera).nombre), titulo)
                        else:
                            ws.write(4, 0, 'Carrera: ', titulo)
                            ws.write(4, 1, str(Carrera.objects.get(pk=carrera).nombre), titulo)
                    fila = 7
                    for e in ejes:
                        ws.write_merge(fila, fila, 0, 4, elimina_tildes(e.descripcion), subtitulo)
                        colum = 5

                        for r in e.respuestas():
                            ws.write_merge(fila, fila,colum, colum+1, elimina_tildes(r.respuesta.nombre), titulo2)
                            colum = colum + 2
                        fila = fila + 1

                        for p in e.preguntas_alumno():
                            ws.write_merge(fila, fila, 1, 4, elimina_tildes(p.nombre))
                            colum = 5
                            for r in e.respuestas():
                                ws.write_merge(fila, fila,colum, colum+1, str(r.cantidad_respuesta(evaluacion,p,profesor,carrera,periodo)), subtitulo2)
                                colum = colum + 2
                            fila = fila + 1
                    fila = fila + 2
                    ws.write(fila, 0, "Fecha Impresion", subtitulo)
                    ws.write(fila, 1, str(datetime.now()), subtitulo)
                    ws.write(fila + 1, 0, "Usuario", subtitulo)
                    ws.write(fila + 1, 1, str(request.user), subtitulo)

                    nombre = 'evaluacionprofesor' + str(datetime.now()).replace(" ", "").replace(".", "").replace(":", "") + '.xls'
                    wb.save(MEDIA_ROOT + '/reportes_excel/' + nombre)
                    return HttpResponse(json.dumps({"result": "ok", "url": "/ube/media/reportes_excel/" + nombre }), content_type="application/json")

                except Exception as e:
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}), content_type="application/json")
            if action == 'guardacoordina':
                lisFormacion = []
                try:
                    periodo=Periodo.objects.filter(id=request.POST['periodo'])[:1].get()
                    persona= Persona.objects.filter(id=request.POST['idpersona'])[:1].get()
                    carrera=Carrera.objects.filter(id=request.POST['idcarrera'])[:1].get()
                    if not CoordinadorCarreraPeriodo.objects.filter(persona=persona, periodo=periodo, carrera=carrera).exists():
                        coordinadorcarrera=CoordinadorCarreraPeriodo(persona=persona, periodo=periodo, carrera=carrera)
                        coordinadorcarrera.save()
                        # return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                    else:
                        coordinadorcarrera=CoordinadorCarreraPeriodo.objects.filter(persona=persona, periodo=periodo, carrera=carrera)[:1].get()
                        coordinadorcarrera.periodo=periodo
                        coordinadorcarrera.persona=persona
                        coordinadorcarrera.carrera=carrera
                        coordinadorcarrera.save()
                    # for a in Carrera.objects.filter(id__in=Materia.objects.filter(nivel__periodo=periodo.periodo).values('nivel__carrera__id'),activo=True).order_by('nombre'):
                    #     lisFormacion.append(
                    #         {"id": a.id, "carrera": a.nombre,
                    #          "coordinador":  a.coordinadorcarr(periodo) if a .coordinadorcarr(periodo) else '',
                    #          })
                    # print(lisFormacion)

                    return HttpResponse(json.dumps({'result': 'ok', 'lisFormacion': lisFormacion}),
                                        content_type="application/json")

                except Exception as e:
                    return HttpResponse(
                        json.dumps({'result': 'bad', 'message': "Ocurrio un error (" + str(e) + ")"}),
                        content_type="application/json")
            if action == 'eliminarcoord':

                try:

                    periodo=PeriodoEvaluacion.objects.filter(id=request.POST['idperiodo'])[:1].get()

                    carrera=Carrera.objects.filter(id=request.POST['idcarrera'])[:1].get()

                    persona= Persona.objects.filter(id=request.POST['idpersona'])[:1].get()
                    print(persona)

                    if CoordinadorCarreraPeriodo.objects.filter(persona=persona, periodo=periodo.periodo, carrera=carrera).exists():
                        coordinadorcarrera=CoordinadorCarreraPeriodo.objects.filter(persona=persona, periodo=periodo.periodo, carrera=carrera)[:1].get()

                        client_address = ip_client_address(request)

                        # Log de EDITAR GRUPO
                        LogEntry.objects.log_action(
                            user_id=request.user.pk,
                            content_type_id=ContentType.objects.get_for_model(coordinadorcarrera).pk,
                            object_id=coordinadorcarrera.id,
                            object_repr=force_str(coordinadorcarrera),
                            action_flag=DELETION,
                            change_message='Eliminado Coordinador carrera periodo (' + client_address + ')')
                        coordinadorcarrera.delete()
                        return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as e:
                    return HttpResponse(
                        json.dumps({'result': 'bad', 'message': "Ocurrio un error (" + str(e) + ")"}),
                        content_type="application/json")
            if action =='clonarcoordinador':
                try:
                    periodo_nuevo=Periodo.objects.filter(id=request.POST['periodo_nuevo'])[:1].get()
                    periodo_clon=Periodo.objects.filter(id=request.POST['periodo_clon'])[:1].get()
                    materia=Materia.objects.filter(nivel__periodo=periodo_nuevo).values('nivel__carrera__id')
                    carrera=Carrera.objects.filter(id__in=materia,activo=True).order_by('nombre')

                    # persona=None
                    for ca in carrera:
                        if CoordinadorCarreraPeriodo.objects.filter(carrera=ca, periodo=periodo_clon).exists():
                            cordinadoreval=CoordinadorCarreraPeriodo.objects.filter(carrera=ca, periodo=periodo_clon)[:1].get()
                            if not CoordinadorCarreraPeriodo.objects.filter(carrera=ca, periodo=periodo_nuevo).exists():
                                cordina=CoordinadorCarreraPeriodo(carrera=ca, periodo=periodo_nuevo, persona=cordinadoreval.persona)
                                cordina.save()
                        else:
                            cordina=CoordinadorCarreraPeriodo(carrera=ca, periodo=periodo_nuevo)
                            cordina.save()
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as e:
                    print((e))
                    return HttpResponse(
                        json.dumps({'result': 'bad', 'message': "Ocurrio un error (" + str(e) + ")"}),
                        content_type="application/json")

    else:
        data = {'title': 'Listado de Evaluaciones '}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action == 'cordinadores':
                if Periodo.objects.filter(pk=request.GET['periodo']).exists():
                    periodo=Periodo.objects.filter(pk=request.GET['periodo'])[:1].get()
                    data['periodo']=periodo
                    materia=Materia.objects.filter(nivel__periodo=periodo).values('nivel__carrera__id')
                    carrera=Carrera.objects.filter(id__in=materia,activo=True).order_by('nombre')
                    data['carrera']=carrera
                    cordina=CoordinadorCarreraPeriodo.objects.filter().count()

                    if cordina>0:
                        periodo_id=CoordinadorCarreraPeriodo.objects.filter().values('periodo__id')
                        data['periodos']=Periodo.objects.filter(id__in=periodo_id)
                    # data['coordinadorcar']=CoordinadorCarreraPeriodo.objects.filter(carrera=carrera, periodo=periodo)
                    return render(request ,"encuestaevaluacion/carreras.html" ,  data)
            if action=='adicionareva':

                data['title'] = 'Adicionar Evaluacion'
                op= int(request.GET['op'])
                # if op ==2:
                #     data['form'] = EvaluacionDocenteDocForms()
                #     data['op']=op
                # else:
                data['form'] = EvaluacionDocenteForms()
                data['form'].evaluacion(op)
                data['op']=op

                return render(request ,"encuestaevaluacion/addevaluacion.html" ,  data)
            elif action == 'agregar':
                data['title'] = ''
                evaluacion = EvaluacionDocente.objects.get(pk=request.GET['id'])
                data['evaluacion'] = evaluacion
                fecha = datetime.now()
                if 'op' in request.GET:
                    data['op']='op'
                data['form'] = AsignaEvaluacionForm()
                # data['acc'] = request.GET['acc']
                return render(request ,"encuestaevaluacion/asignar.html" ,  data)
            if action == 'ver':
                search = None
                data['title'] = 'Adicionar Materias a la Evaluacion'
                evaluaciondocente = EvaluacionDocente.objects.get(pk=request.GET['id'])

                data['evaluaciondocente'] = evaluaciondocente
                # data['evadesc'] = evaluacion
                data['acc'] = request.GET['acc']
                data['idpag'] = request.GET['id']
                evaluacion =EvaluacionMateria.objects.filter(evaluaciondocente=evaluaciondocente).order_by('materia__asignatura__nombre',)
                if 's' in request.GET:
                    search = request.GET['s']
                    if search:
                        evaluacion = evaluacion.filter(
                            Q(materia__nivel__periodo__nombre__icontains=search) | Q(materia__asignatura__nombre__icontains=search)| Q(materia__nivel__nivelmalla__nombre__icontains=search)| Q(materia__nivel__paralelo__icontains=search)).order_by('materia__asignatura__nombre',)


                paging = MiPaginador(evaluacion, 30)
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
                data['evaluacion'] = page.object_list

                return render(request ,"encuestaevaluacion/vermaterias.html" ,  data)
            # if action == 'verformato':
            #     data['title'] = 'Ver Formato Evaluacion'
            #     ejes=None
            #     evaluacion=None
            #     if 'id' in request.GET:
            #
            #         evaluacion = EvaluacionDocente.objects.filter(pk=request.GET['id'])[:1].get()
            #         ejes = EjesEvaluacion.objects.filter(id__in=DetalleEvaluacionPregunta.objects.filter(evaluacion=evaluacion).distinct('eje').values('eje'))
            #
            #     # if 'eje' in request.GET :
            #     #     ejeinfo=EjesEvaluacion.objects.filter(pk=request.GET['eje'])[:1].get()
            #     #     evaluacion = EvaluacionDocente.objects.filter(pk=request.GET['eva'])[:1].get()
            #     #     ejest = EjesEvaluacion.objects.filter(pk=request.GET['eje'],id__in=DetalleEvaluacionPregunta.objects.filter(evaluacion=evaluacion).distinct('eje').values('eje'))
            #     #     data['ejest'] = ejest
            #     #     ejes = EjesEvaluacion.objects.filter(id__in=DetalleEvaluacionPregunta.objects.filter(evaluacion=evaluacion).distinct('eje').values('eje'))
            #     #     if DetalleEvaluacionPregunta.objects.filter(evaluacion=evaluacion,eje=ejeinfo).exists():
            #     #         area=DetalleEvaluacionPregunta.objects.filter(evaluacion=evaluacion,eje=ejeinfo).values('pregunta__area__id')
            #     #         areaseva=AreasElementosEvaluacion.objects.filter(id__in=area)
            #     #         data['areaseva']=areaseva
            #             # ejest = EjesEvaluacion.objects.filter(pk=request.GET['eje'],id__in=DetalleEvaluacionPregunta.objects.filter(evaluacion=evaluacion,eje=ejeinfo,pregunta__area__id__in=areaseva).distinct('eje').values('eje'))
            #             # data['ejest'] = ejest
            #     data['ejes'] = ejes
            #     data['evaluacion']=evaluacion
            #
            #     # return render_to_response("encuestaevaluacion/detalleevaluacion.html", data,
            #     #                           context_instance=RequestContext(request))
            #     return render_to_response("encuestaevaluacion/detalleevaluacion.html", data,
            #                               context_instance=RequestContext(request))
            # if action == 'verformato':
            #     data['title'] = 'Ver Formato Evaluacion'
            #     evaluacion = EvaluacionDocente.objects.filter(pk=request.GET['id'])[:1].get()
            #     ejes = EjesEvaluacion.objects.filter(id__in=DetalleEvaluacionPregunta.objects.filter(evaluacion=evaluacion).distinct('eje').values('eje'))
            #     data['ejes'] = ejes
            #     data['evaluacion']=evaluacion
            #     area=AreasElementosEvaluacion.objects.filter(id__in=DetalleEvaluacionPregunta.objects.filter(evaluacion=evaluacion).values('pregunta__area__id'))
            #     data['area']=area
            #     # data['ejetot']=EjesEvaluacion.objects.filter(pk=request.GET['eje'],  id__in=DetalleEvaluacionPregunta.objects.filter(evaluacion=evaluacion).distinct('eje').values('eje'))
            #
            #     return render_to_response("encuestaevaluacion/detalleevaluacion2.html", data,
            #                               context_instance=RequestContext(request))
            if action == 'verformato':
                data['title'] = 'Ver Formato Evaluacion'
                evaluacion = EvaluacionDocente.objects.filter(pk=request.GET['id'])[:1].get()
                ejes = EjesEvaluacion.objects.filter(id__in=DetalleEvaluacionPregunta.objects.filter(evaluacion=evaluacion).distinct('eje').values('eje'))
                data['ejes'] = ejes
                data['evaluacion']=evaluacion
                # data['acc'] = request.GET['acc']
                return render(request ,"encuestaevaluacion/detalleevaluacion.html" ,  data)
            if action == 'vercoordinadores':
                search = None
                data['title'] = str(Periodo.objects.get(id = int(request.GET['periodo'])))
                if 's' in request.GET:
                    search = request.GET['s']
                if search:
                    listEvaluacionCoordinador = busqueda(search, int(request.GET['periodoev']))
                else:
                    listEvaluacionCoordinador = busqueda(search, int(request.GET['periodoev']))

                data['listcoordinadoresdisponibles'] = CoordinadorCarreraPeriodo.objects.filter(periodo__id=request.GET['periodo'],
                    id__in=listEvaluacionCoordinador.filter().values_list('coordinador__id')).exclude(persona=None).distinct().order_by('persona__apellido1','persona__apellido2','persona__nombres')
                if 'coord' in request.GET:
                    if int(request.GET['coord'])>0 :
                        listEvaluacionCoordinador = listEvaluacionCoordinador.filter(coordinador__id =  int(request.GET['coord']))
                    elif int(request.GET['coord'])<0:
                        listEvaluacionCoordinador = listEvaluacionCoordinador.filter(
                            coordinador__isnull=True)
                paging = Paginator(listEvaluacionCoordinador, 30)
                try:
                    if 'page' in request.GET:
                        listEvaluacionCoordinador = int(request.GET['page'])
                    page = paging.page(listEvaluacionCoordinador)
                except:
                    page = paging.page(1)
                data['paging'] = paging
                data['page'] = page
                data['pagenumer'] = int(request.GET['page']) if 'page' in request.GET else '0'
                data['search'] = search if search else ""
                data['listEvaluacion'] = page.object_list
                # data['acc'] = request.GET['acc']
                data['periodo'] = request.GET['periodo']
                # print((request.GET))
                data['periodoev'] = request.GET['periodoev']
                data['listcoordinadores'] = CoordinadorCarreraPeriodo.objects.filter(periodo__id=request.GET['periodo']).distinct('persona').select_related('persona').order_by('persona','persona__apellido1','persona__apellido2','persona__nombres')
                data['coord'] = int(request.GET['coord']) if 'coord' in request.GET else '0'
                # data['permisopcion'] = AccesoModulo.objects.get(id=int(request.GET['acc']))
                return render(request ,"encuestaevaluacion/evaluacioncoordinadordocente.html" ,  data)
            if action == 'verperiodos':

                try:
                    evaluacion = None
                    data = {'title': ''}
                    if EvaluacionDocente.objects.filter(pk=request.GET['id'], docente=True).exists():
                        evaluacion = EvaluacionDocente.objects.filter(pk=request.GET['id'], docente=True)[:1].get()
                        data['periodoeva'] = PeriodoEvaluacion.objects.filter(evaluaciondoc=evaluacion)
                        data['periodo'] = Periodo.objects.filter(activo=True)
                    if EvaluacionDocente.objects.filter(pk=request.GET['id'], directivo=True).exists():
                        evaluacion = EvaluacionDocente.objects.filter(pk=request.GET['id'], directivo=True)[:1].get()
                        data['directivo'] = 1
                        # evaluaciondoc=EvaluacionDocente.objects.filter(pk=request.GET['id'],docente=True )[:1].get()
                        per = PeriodoEvaluacion.objects.filter(evaluaciondoc__docente=True).values('periodo__id')

                        if per:
                            data['periodoeva'] = PeriodoEvaluacion.objects.filter(evaluaciondoc=evaluacion)

                            data['periodo'] = Periodo.objects.filter(id__in=per)
                    if EvaluacionDocente.objects.filter(pk=request.GET['id'], directivocargo=True).exists():
                        evaluacion = EvaluacionDocente.objects.filter(pk=request.GET['id'], directivocargo=True)[
                                     :1].get()
                        data['directivocargo'] = 1
                        # evaluaciondoc=EvaluacionDocente.objects.filter(pk=request.GET['id'],docente=True )[:1].get()
                        per = PeriodoEvaluacion.objects.filter(evaluaciondoc__directivo=True).values('periodo__id')

                        if per:
                            data['periodoeva'] = PeriodoEvaluacion.objects.filter(evaluaciondoc=evaluacion)

                            data['periodo'] = Periodo.objects.filter(id__in=per)

                    data['evaluacion'] = evaluacion

                    return render(request ,"encuestaevaluacion/veperiodos.html" ,  data)
                except Exception as e:
                    print(e)
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}),
                                        content_type="application/json")


            if action == 'evaluardocente':
                try:

                    # data = {'title': ''}
                    # data['acc'] = request.GET['acc']
                    if 'idprofe' in request.GET:
                        profesor = Profesor.objects.get(id=request.GET['idprofe'])
                    else:
                        profesor = Profesor.objects.get(persona=data['persona'])
                    if 'op' in request.GET:
                        data['op'] = request.GET['op']

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
                    data['evaluacion'] = True
                    data['profesor'] = profesor
                    data['evaluaciondoc'] = evaluacion
                    if 'opver' in request.GET:
                        data['opver'] = 'opver'
                    return render(request ,"doc_evaluaciondocente/evaluaciondocente.html" ,  data)
                except Exception as e:
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}),
                                        content_type="application/json")
            if action == 'evaluacionprofesor':
                try:

                    # data = {'title': ''}
                    # data['acc'] = request.GET['acc']
                    evaluacioneslist = []
                    preguntas = None
                    periodo = None
                    carrera = None
                    profesor = Profesor.objects.get(id=request.GET['id'])
                    if 'acc' in request.GET:
                        data['acc'] = request.GET['acc']
                    evaluacion = EvaluacionDocente.objects.filter(docente=False, directivo=False, estado=True)[:1].get()
                    evaluaciondoc = EvaluacionDocente.objects.filter(pk=request.GET['evalid'])[:1].get()
                    evaluaciones = EvaluacionAlumno.objects.filter(evaluaciondocente=evaluacion,
                                                                   profesormateria__profesor=profesor)
                    carrera_id=EvaluacionAlumno.objects.filter(evaluaciondocente=evaluacion,
                                                                   profesormateria__profesor=profesor).values('profesormateria__materia__nivel__carrera__id')


                    if 'carrera' in request.GET:
                        if int(request.GET['carrera']) > 0:
                            carrera = int(request.GET['carrera'])
                    if 'periodo' in request.GET:
                        if int(request.GET['periodo']) > 0:
                            periodo = int(request.GET['periodo'])

                    ejes = DetalleEvaluacionPregunta.objects.filter(evaluacion=evaluacion).values('eje')

                    data['ejes'] = EjesEvaluacion.objects.filter(id__in=ejes)

                    data['carrera'] = carrera
                    data['periodo'] = periodo
                    data['evaluaciones']=evaluaciones
                    data['evaluacion']=evaluacion
                    data['evaluaciondoc']=evaluaciondoc
                    data['profesor']=profesor
                    # carreraid=ProfesorMateria.objects.filter(profesor=Profesor).values('materia__nivel__carrera__id')
                    # print(carreraid)
                    # data['carreras']=Carrera.objects.filter(id__in=carreraid)
                    data['carreras']=Carrera.objects.filter(id__in=carrera_id)

                    data['periodos'] = EvaluacionAlumno.objects.filter(evaluaciondocente=evaluacion,
                                                                       profesormateria__profesor=profesor).distinct('materia__nivel__periodo')



                    return render(request ,"encuestaevaluacion/evaluaciondocenteprofe.html" ,  data)
                except Exception as e:
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}),
                                        content_type="application/json")



            if action == 'verevaluaciondocente':
                try:
                    search = None
                    matricula = None
                    inscripcion = None
                    profesor = Profesor.objects.get(id=request.GET['id'])
                    evaluaciondocente = EvaluacionDocente.objects.filter(pk=request.GET['eva'])[:1].get()
                    if CoordinadorCarrera.objects.filter(persona__usuario=request.user).exists():
                        data['escoordinador'] = True

                        coord = CoordinadorCarrera.objects.filter(persona__usuario=request.user)[:1].get()
                        if EvaluacionCoordinadorDocente.objects.filter(coordinador=coord).exists():
                            profesorescoor = EvaluacionCoordinadorDocente.objects.filter(coordinador=coord,
                                                                                         evaluacion__evaluaciondoc=evaluaciondocente).values(
                                'profesor')
                            periodoscoor = EvaluacionCoordinadorDocente.objects.filter(coordinador=coord,
                                                                                       evaluacion__evaluaciondoc=evaluaciondocente).values(
                                'evaluacion__periodo')
                            profesores = Profesor.objects.filter(
                                id__in=EvaluacionDocentePeriodo.objects.filter(periodo__id__in=periodoscoor,
                                                                               profesor__id__in=profesorescoor).values(
                                    'profesor')).order_by('persona__apellido1')
                            evaluaciones = EvaluacionDocentePeriodo.objects.filter(profesor=profesor,periodo__id__in=periodoscoor).order_by(
                                'fecha')
                            data['escoordinador'] = True
                    else:

                        evaluaciones = EvaluacionDocentePeriodo.objects.filter(profesor=profesor,evaluaciondocente__docente=True).order_by('fecha')

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

                    data['profesor']=profesor
                    data['evaluacion']=True

                    return render(request ,"encuestaevaluacion/verevaluaciondocente.html" ,  data)
                except Exception as e:
                    print(e)
                    return HttpResponseRedirect("/encuestaevaluacion")

            if action == 'verevaluacion':
                search = None
                data['title'] = 'Ver Evaluacion'
                if EvaluacionDocentePeriodo.objects.filter(evaluaciondocente__id=request.GET['id']).exists():
                    evaluacion = EvaluacionDocente.objects.filter(pk=request.GET['id'])[:1].get()
                    docentesevaluacion = EvaluacionDocentePeriodo.objects.filter(evaluaciondocente=evaluacion)
                    periodoid = EvaluacionDocentePeriodo.objects.filter(evaluaciondocente=evaluacion).values('periodo__id')
                    finalizados = docentesevaluacion.filter(finalizado=True).count()
                    pendientes = docentesevaluacion.filter(finalizado=False).count()
                    periodo = EvaluacionDocentePeriodo.objects.filter(evaluaciondocente=evaluacion).distinct(
                        'periodo').values('periodo_id')
                    nomperiodos = EvaluacionDocentePeriodo.objects.filter(evaluaciondocente=evaluacion).distinct(
                        'periodo')

                    if CoordinadorCarrera.objects.filter(persona__usuario=request.user).exists():
                        data['escoordinador'] = True
                        coord = CoordinadorCarrera.objects.filter(persona__usuario=request.user).values('id')
                        coordinador = CoordinadorCarrera.objects.filter(persona__usuario=request.user)[:1].get()
                        if EvaluacionCoordinadorDocente.objects.filter(coordinador__id__in=coord).exists():
                            profesorescoor= EvaluacionCoordinadorDocente.objects.filter(coordinador__id__in=coord,evaluacion__evaluaciondoc=evaluacion).values('profesor')
                            periodoscoor= EvaluacionCoordinadorDocente.objects.filter(coordinador__id__in=coord,evaluacion__evaluaciondoc=evaluacion).values('evaluacion__periodo')
                            profesores = Profesor.objects.filter(
                                id__in=EvaluacionDocentePeriodo.objects.filter(periodo__id__in=periodoscoor,profesor__id__in=profesorescoor).values('profesor')).exclude(persona=coordinador.persona).order_by('persona__apellido1')

                    else:

                        profesores = Profesor.objects.filter(id__in=EvaluacionDocentePeriodo.objects.filter(evaluaciondocente=evaluacion).values('profesor')).order_by('persona__apellido1')
                else:
                    evaluacion = EvaluacionDocente.objects.filter(pk=request.GET['id'])[:1].get()
                    finalizados = 0
                    pendientes = 0
                    periodo = PeriodoEvaluacion.objects.filter(evaluaciondoc__id=request.GET['id']).distinct('periodo').values('periodo__id')
                    profesores = ""
                    nomperiodos = PeriodoEvaluacion.objects.filter(evaluaciondoc__id=request.GET['id']).distinct('periodo')
                    docentesevaluacion = profesores
                data['periodo'] = periodo

                data['periodos'] = PeriodoEvaluacion.objects.filter(id__in=periodoid).distinct('periodo')
                data['nomperiodo'] = nomperiodos
                data['finalizados'] = finalizados
                data['pendientes'] = pendientes
                data['docentesevaluacion'] = docentesevaluacion

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
                                    persona__pasaporte__icontains=search)).order_by('persona__apellido1')
                        else:
                            profesores = profesores.filter(Q(persona__apellido1__icontains=ss[0]) & Q(
                                persona__apellido2__icontains=ss[1]),
                                                                     persona__usuario__is_active=True).order_by(
                                'persona__apellido1',
                                'persona__apellido2', 'persona__nombres')
                            print(profesores)
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
                return render(request ,"encuestaevaluacion/profesores.html" ,  data)
            if action == 'evaluacionprofesor':
                try:

                    # data = {'title': ''}
                    # data['acc'] = request.GET['acc']
                    evaluacioneslist = []
                    preguntas = None
                    periodo = None
                    carrera = None
                    profesor = Profesor.objects.get(id=request.GET['id'])
                    if 'acc' in request.GET:
                        data['acc'] = request.GET['acc']
                    evaluacion = EvaluacionDocente.objects.filter(pk=request.GET['evalid'])[:1].get()
                    evaluaciones = EvaluacionAlumno.objects.filter(evaluaciondocente=evaluacion,
                                                                   profesormateria__profesor=profesor)



                    if 'carrera' in request.GET:
                        if int(request.GET['carrera']) > 0:
                            carrera = int(request.GET['carrera'])
                    if 'periodo' in request.GET:
                        if int(request.GET['periodo']) > 0:
                            periodo = int(request.GET['periodo'])

                    ejes = DetalleEvaluacionPregunta.objects.filter(evaluacion=evaluacion).values('eje')

                    data['ejes'] = EjesEvaluacion.objects.filter(id__in=ejes)

                    data['carrera'] = carrera
                    data['periodo'] = periodo
                    data['evaluaciones']=evaluaciones
                    data['evaluacion']=evaluacion
                    data['profesor']=profesor
                    data['carreras']=Carrera.objects.filter()

                    data['periodos'] = EvaluacionAlumno.objects.filter(evaluaciondocente=evaluacion,
                                                                       profesormateria__profesor=profesor).distinct('materia__nivel__periodo')



                    return render(request ,"encuestaevaluacion/evaluaciondocenteprofe.html" ,  data)
                except Exception as e:
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}),
                                        content_type="application/json")
            if action == 'verdetalle':
                profesor = Profesor.objects.filter(pk=request.GET['profesor'])[:1].get()
                evaluacion = EvaluacionDocente.objects.filter(pk=request.GET['evaluacion'])[:1].get()
                pregunta = PreguntasEvaluacion.objects.filter(pk=request.GET['pid'])[:1].get()
                data['materias'] = Materia.objects.filter(id__in=EvaluacionAlumno.objects.filter(evaluaciondocente=evaluacion,
                                                           profesormateria__profesor=profesor).values('materia')).order_by('asignatura__nombre')
                data['profesor']=profesor
                data['evaluacion']=evaluacion
                data['pregunta']=pregunta
                data['respuestas']=pregunta.eje.respuestas()
                return render(request ,"encuestaevaluacion/verdetalledocenteeval.html" ,  data)
            if action == 'verdocentes':
                search = None
                data['title'] = 'Docentes Evaluados'
                evaluacion = EvaluacionDocente.objects.filter(pk=request.GET['id'])[:1].get()
                profesores = Profesor.objects.filter(id__in=EvaluacionAlumno.objects.filter(evaluaciondocente=evaluacion).distinct('profesormateria__profesor').values('profesormateria__profesor')).order_by('persona__apellido1','persona__apellido2')
                data['profesores']=profesores
                # data['acc'] = request.GET['acc']
                data['idpag'] = request.GET['id']
                data['evaluacion']=evaluacion
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
                                    persona__pasaporte__icontains=search)| Q(
                                    carrera__nombre__icontains=search) | Q(
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
                # data['form'] = ParametroDescuentoForm()
                data['profesores'] = page.object_list

                return render(request ,"encuestaevaluacion/profesores.html" ,  data)
            if action == 'verevaluacionalumno':
                search = None
                data['title'] = 'Ver Evaluacion'
                if CoordinadorCarreraPeriodo.objects.filter(persona__usuario=request.user).exists():
                   escoordinador = True
                   cid = CoordinadorCarreraPeriodo.objects.filter(persona__usuario=request.user).values('carrera')
                   carreras=Carrera.objects.filter(id__in=cid).order_by('nombre')

                else:
                    carreras=Carrera.objects.all().order_by('nombre')
                    if 'carrera' in request.GET:
                        c=Carrera.objects.filter(id=request.GET['carrera'])[:1].get()
                        carreras = Carrera.objects.filter(id=c.id).order_by('nombre')
                evaluacion = EvaluacionDocente.objects.filter(pk=request.GET['id'])[:1].get()
                if Profesor.objects.filter(persona__usuario=request.user,tutor=True).exists():
                    profesor = Profesor.objects.filter(persona__usuario=request.user,tutor=True)[:1].get()
                    data['profesor'] = profesor
                    data['estutor']=True
                    # if InscripcionTutor.objects.filter(tutor=profesor,activo=True).exists():
                    #     inscrip = InscripcionTutor.objects.filter(tutor=profesor,activo=True).values('inscripcion')
                    #     grupos = InscripcionGrupo.objects.filter(activo=True,inscripcion__id__in=inscrip).values('grupo').distinct('grupo')
                    #     # data['grupos'] = Grupo.objects.filter(id__in=grupos).order_by('nombre')
                    #     inscripciones = Inscripcion.objects.filter(
                    #         id__in=EvaluacionAlumno.objects.filter(evaluaciondocente=evaluacion,
                    #                                                id__in=inscrip).distinct('inscripcion').values(
                    #             'inscripcion')).order_by('persona__apellido1', 'persona__apellido2')
                if carreras:
                    inscripciones = Inscripcion.objects.filter(id__in=EvaluacionAlumno.objects.filter(evaluaciondocente=evaluacion).distinct('inscripcion').values('inscripcion'),carrera__in=carreras).order_by('persona__apellido1','persona__apellido2')
                data['inscripciones']=inscripciones

                data['idpag'] = request.GET['id']
                data['evaluacion']=evaluacion
                if 's' in request.GET:
                    search = request.GET['s']
                    if search:
                        ss = search.split(' ')
                        while '' in ss:
                            ss.remove('')
                        if len(ss) == 1:
                            inscripciones = inscripciones.filter(
                                Q(persona__nombres__icontains=search) | Q(persona__apellido1__icontains=search) | Q(
                                    persona__apellido2__icontains=search) | Q(persona__cedula__icontains=search) | Q(
                                    persona__pasaporte__icontains=search) | Q(identificador__icontains=search) | Q(
                                    inscripciongrupo__grupo__nombre__icontains=search) | Q(
                                    carrera__nombre__icontains=search) | Q(
                                    persona__usuario__username__icontains=search),
                                persona__usuario__is_active=True).order_by('persona__apellido1')
                        else:
                            inscripciones = inscripciones.filter(Q(persona__apellido1__icontains=ss[0]) & Q(
                                persona__apellido2__icontains=ss[1]),
                                                                     persona__usuario__is_active=True).order_by(
                                'persona__apellido1',
                                'persona__apellido2', 'persona__nombres')
                paging = MiPaginador(inscripciones, 30)
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
                data['inscripciones'] = page.object_list


                return render(request ,"encuestaevaluacion/inscripciones.html" ,  data)

            if action == 'verevalalumno':
                try:
                    search = None
                    matricula = None
                    inscripcion = None

                    if 'eva' in request.GET:
                        evalu=EvaluacionDocente.objects.filter(id=request.GET['eva'])[:1].get()
                        data['eva']=evalu

                    if 'id' in request.GET:
                        if  Profesor.objects.filter(persona__usuario=request.user).exists():
                            data['estutor']=True
                        if CoordinadorCarreraPeriodo.objects.filter(persona__usuario=request.user).exists():
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
                    return render(request ,"encuestaevaluacion/evaluacionesalumno.html" ,  data)
                except Exception as e:
                    print((e))
                    # return HttpResponse(
                    #     json.dumps({'result': 'bad', 'message': "Ocurrio un error (" + str(e) + ")"}),
                    #     content_type="application/json")
            if action == 'evaluaralumno':
                try:
                    if 'eva' in request.GET:
                        print(2222)
                        evalu=EvaluacionDocente.objects.filter(id=request.GET['eva'])[:1].get()
                        data['eva']=evalu

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
                    if 'opalumn' in request.GET:
                        data['opalumn']='opalumn'
                        print(333)
                    return render(request ,"alu_evaluaciondocente/evaluaciondocente.html" ,  data)
                except Exception as e:
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}),
                                        content_type="application/json")

        else:

            try:
                search = None

                if 's' in request.GET:
                    search = request.GET['s']

                if search:
                    evaluacion = EvaluacionDocente.objects.filter(descripcion=search,docente=False, directivo=False).order_by('descripcion')

                else:

                    evaluacion = EvaluacionDocente.objects.filter(estado=True, docente=False, directivo=False,directivocargo=False)
                    print(evaluacion)
                if 'tipo' in request.GET:
                    tipo = request.GET['tipo']
                    if tipo == 'ins': #ESTUDIANTE
                        data['estudiante'] =  True
                        evaluacion = EvaluacionDocente.objects.filter(estado=True,docente=False, directivo=False).order_by('descripcion')
                    elif tipo == 'doc': #DOCENTES
                        data['docentes'] =  True
                        evaluacion = EvaluacionDocente.objects.filter(estado=True,docente=True).order_by('descripcion')
                    elif tipo == 'adm': #ADMINISTRATIVOS
                        data['administrativos'] =  True
                        evaluacion = EvaluacionDocente.objects.filter(estado=True,directivo=True).order_by('descripcion')
                    elif tipo == 'dec': #DECANOS
                        data['decano'] =  True
                        evaluacion = EvaluacionDocente.objects.filter(estado=True,directivocargo=True).order_by('descripcion')
                paging = MiPaginador(evaluacion, 30)
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
                data['evaluacion'] = page.object_list
                periodos=PeriodoEvaluacion.objects.filter().values('periodo__id')
                data['periodos'] = Periodo.objects.filter(id__in=periodos)


                # data['respuesta'] = RespuestasEvaluacion.objects.filter()
                # data['permisopcion'] = AccesoModulo.objects.get(id=int(request.GET['acc']), modulo__url=request.path[1:])
                if 'error' in request.GET:
                    data['error']= request.GET['error']
                # data['acc'] = request.GET['acc']
                if Profesor.objects.filter(persona__usuario=request.user,tutor=True).exists():
                    profesor = Profesor.objects.filter(persona__usuario=request.user,tutor=True)[:1].get()
                    data['profesor'] = profesor

                    # if InscripcionTutor.objects.filter(tutor=profesor,activo=True).exists():
                    #     data['estutor'] = True

                return render(request ,"encuestaevaluacion/evaluaciondocente.html" ,  data)

            except Exception as e:
                print((e))
                return HttpResponseRedirect("/encuestaevaluacion")