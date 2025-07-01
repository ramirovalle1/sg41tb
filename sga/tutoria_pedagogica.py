
import json
from datetime import datetime

import requests
import xlwt
from django.contrib.admin.models import LogEntry, CHANGE, ADDITION, DELETION
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str

from clinicaestetica.historclinico import MiPaginador
from settings import MEDIA_ROOT
from sga.commonviews import addUserData, ip_client_address
from sga.forms import XLSPeriodoForm
from sga.funciones import custom_render_to_response
from sga.models import Materia, CoordinadorCarrera, Coordinacion, ProfesorMateria, Profesor, Inscripcion, \
    TutoriaPedagogica, DetalleTutoriaPedagogica, EstudianteTutoriaPedagogica, Matricula, EstrategiasPedagogicas, \
    InstrumentosTutoriaPedagogicas, DetalleEstrategiasPedagogicas, DetalleInstrumentosTutoriaPedagogicas, Periodo, \
    EvaluacionDocente, TituloInstitucion, elimina_tildes, ReporteExcel


def view(request):
    if request.method=='POST':

        if 'action' in request.POST:
            action = request.POST['action']

            if action == 'addtutoria':
                if Profesor.objects.filter(pk=request.POST['profesor_id']).exists():
                    profesor=Profesor.objects.filter(pk=request.POST['profesor_id'])[:1].get()

                    if Materia.objects.filter(pk=request.POST['materia_id']).exists():
                        materia=Materia.objects.filter(pk=request.POST['materia_id'])[:1].get()
                        tutoria=TutoriaPedagogica(profesor=profesor, materia=materia, numero_tutoria=request.POST['numtutoria'],aceptada=None)
                        tutoria.save()
                        if request.POST['grupal']=='true':
                            tutoria.grupal=True
                        else:
                            tutoria.grupal=False

                        tutoria.save()
                        detalle_tutoria=DetalleTutoriaPedagogica(tutoria=tutoria, fecha_tutoria=request.POST['fecha_tutoria'],
                                                                 hora_inicio_tutoria=request.POST['horainicio'],
                                                                 hora_fin_tutoria=request.POST['horafin'],
                                                                 necesidad=request.POST['necesidad'])
                        detalle_tutoria.save()
                        if request.POST['via']=='true':
                            detalle_tutoria.via_tutoria=True
                        else:
                            detalle_tutoria.via_tutoria=False
                        detalle_tutoria.save()

                        if request.POST['inscripcion_id_indi']!='0':
                            matricula = Matricula.objects.filter(nivel=materia.nivel, id=request.POST['inscripcion_id_indi'])[:1].get()
                            # inscripcion=Inscripcion.objects.filter(id=a)[:1].get()
                            estudiante_tutoria = EstudianteTutoriaPedagogica(estudiante=matricula.inscripcion,
                                                                             tutoria=tutoria)
                            estudiante_tutoria.save()
                            print('indivudual')
                        else:
                            if request.POST['inscripcion_id'] != '':
                                for a in request.POST['inscripcion_id'].split(","):
                                    if Matricula.objects.filter(nivel=materia.nivel,id=a).exists():
                                        matricula=Matricula.objects.filter(nivel=materia.nivel,id=a)[:1].get()
                                        # inscripcion=Inscripcion.objects.filter(id=a)[:1].get()
                                        estudiante_tutoria=EstudianteTutoriaPedagogica(estudiante=matricula.inscripcion, tutoria=tutoria)
                                        estudiante_tutoria.save()
                                        print('grupal')
                        client_address = ip_client_address(request)

                        LogEntry.objects.log_action(
                            user_id=request.user.pk,
                            content_type_id=ContentType.objects.get_for_model(tutoria).pk,
                            object_id=tutoria.id,
                            object_repr=force_str(tutoria),
                            action_flag=ADDITION,
                            change_message='ADICIONADA TUTORIA PEDAGOGICA' + ' (' + client_address + ')')

                        return HttpResponse(json.dumps({"result": "ok",
                                                        "message": 'SE AGREGO CORRRECTAMENTE LA TUTORIA PEDAGOGICA'}),
                                            content_type="application/json")

            if action == 'buscar_materia':
                try:
                    query = request.POST.get('q', '')
                    ss = query.split()
                    ss = [s for s in ss if s]  # Elimina cadenas vacías
                    if len(ss) == 1:
                        materias = Materia.objects.filter(asignatura__nombre__icontains=ss[0]).order_by(
                            'asignatura__nombre')
                    else:
                        materias = Materia.objects.filter(asignatura__nombre__icontains=ss[0]).order_by(
                            'asignatura__nombre')

                    # Paginar resultados
                    paging = MiPaginador(materias, 30)
                    p = int(request.POST.get('page', 1))
                    page = paging.page(p)

                    lista = [{"id": d.id, "nombre": str(d)} for d in page.object_list]
                    return JsonResponse({'result': 'ok', 'items': lista, 'page': p})

                except Exception as ex:
                    return JsonResponse({"result": "bad", "message": str(ex)}, status=500)

            if action == 'cambio_docente':
                try:
                    data = {}
                    if TutoriaPedagogica.objects.filter(pk=request.POST['id_tutoria']).exists():
                        tutoria = TutoriaPedagogica.objects.get(pk=request.POST['id_tutoria'])
                        profesor_anterior=tutoria.profesor

                        if Profesor.objects.filter(pk=request.POST['profesor_id']).exists():
                            profesor=Profesor.objects.filter(pk=request.POST['profesor_id'])[:1].get()
                            tutoria.profesor=profesor
                            tutoria.aceptada=None
                            tutoria.save()
                            client_address = ip_client_address(request)

                            LogEntry.objects.log_action(
                                user_id=request.user.pk,
                                content_type_id=ContentType.objects.get_for_model(tutoria).pk,
                                object_id=tutoria.id,
                                object_repr=force_str(tutoria),
                                action_flag=CHANGE,
                                change_message='CAMBIO DE DOCENTE A LA TUTORIA DE:'+str(profesor_anterior)+ ' - a - ' + str(profesor)  + ' (' + client_address + ')')
                            data['result'] = 'ok'
                            return HttpResponse(json.dumps(data), content_type="application/json")


                except Exception as e:
                    print(e)
                    return JsonResponse({'result': 'error', 'message': str(e)})

            if action == 'verdocentes':
                try:
                    tutoria=None
                    materia=None
                    data = {}
                    profesor_list = []
                    inscripciones_list = []
                    if 'id_tutoria' in request.POST:
                        if TutoriaPedagogica.objects.filter(pk=request.POST['id_tutoria']).exists():
                            tutoria=TutoriaPedagogica.objects.get(pk=request.POST['id_tutoria'])
                            if tutoria:
                                if Materia.objects.filter(id=tutoria.materia.id).exists():
                                    materia=Materia.objects.filter(id=tutoria.materia.id)[:1].get()
                    else:
                        if Materia.objects.filter(pk=request.POST['id']).exists():
                            materia = Materia.objects.get(pk=request.POST['id'])
                    if Coordinacion.objects.filter(carrera=materia.nivel.carrera).exists():
                        coordinacion = Coordinacion.objects.filter(carrera=materia.nivel.carrera).values(
                            'carrera__id')
                        profesormateria = ProfesorMateria.objects.filter(
                            materia__nivel__carrera__id__in=coordinacion)
                        profesores = Profesor.objects.filter(id__in=profesormateria.values('profesor_id'), activo=True)

                        # Crear una lista de profesores con id y nombre_completo
                        profesor_list = [{'id': p.id, 'nombre_completo': p.persona.nombre_completo_inverso()} for p in profesores]
                        inscripciones = Matricula.objects.filter(nivel=materia.nivel)
                        for i in inscripciones:
                            inscripciones_list.append({
                                'inscripcion_id': i.id,
                                'alumno_nombre_completo': i.inscripcion.persona.nombre_completo_inverso()
                            })

                        data['result'] = 'ok'
                        data['profesor_list'] = profesor_list
                        data['inscripciones_list'] = inscripciones_list
                        print(profesor_list)
                        if tutoria:
                            data['idtutoria'] = tutoria.id
                            data['idmateria'] = materia.asignatura.nombre
                        return HttpResponse(json.dumps(data), content_type="application/json")

                    return JsonResponse({'result': 'error', 'message': 'Materia o Coordinación no encontrados'})
                except Exception as e:
                    return JsonResponse({'result': 'error', 'message': str(e)})

            if action == 'aprobartutoria':

                try:
                    if TutoriaPedagogica.objects.filter(pk=request.POST['id_tutoria']).exists():

                        tutoria=TutoriaPedagogica.objects.filter(pk=request.POST['id_tutoria'])[:1].get()
                        if request.POST['aceptar']=='true':
                            tutoria.aceptada=True
                        else:
                            tutoria.aceptada=False

                        tutoria.save()

                        client_address = ip_client_address(request)

                        LogEntry.objects.log_action(
                            user_id=request.user.pk,
                            content_type_id=ContentType.objects.get_for_model(tutoria).pk,
                            object_id=tutoria.id,
                            object_repr=force_str(tutoria),
                            action_flag=CHANGE,
                            change_message='APROBAR/RECHAZAR LA TUTORIA PEDAGOGICA - PROFESOR:'+str(tutoria.profesor)+' (' + client_address + ')')

                        return HttpResponse(json.dumps({"result": "ok",
                                                        "message": 'SE AGREGO CORRRECTAMENTE LA TUTORIA PEDAGOGICA'}),
                                            content_type="application/json")

                except Exception as ex:
                    print(ex)
                    return HttpResponse(json.dumps({"result": "bad", "message": ex}), content_type="application/json")

            if action == 'ver_detalle_tutoria':
                print(request.POST)

                data = {}
                tutoria_id = request.POST.get('id')
                if TutoriaPedagogica.objects.filter(pk=tutoria_id).exists():
                    tutoria = TutoriaPedagogica.objects.get(pk=tutoria_id)
                    print(45)
                    if DetalleTutoriaPedagogica.objects.filter(tutoria=tutoria).count()==tutoria.numero_tutoria:
                        data['result'] = 'okfin'
                        print(2)
                        return HttpResponse(json.dumps(data), content_type="application/json")
                    else:
                        print(4)
                        data['result'] = 'oknueva'
                        return HttpResponse(json.dumps(data), content_type="application/json")

            if action == 'ingresartutoria':
                print(request.POST)
                if 'final' in request.POST or ('fecha_tutoria' in request.POST and request.POST['fecha_tutoria'] != '' and'horainicio' in request.POST and request.POST['horainicio'] != '' and
                        'horafin' in request.POST and request.POST['horafin'] != '' and
                        'necesidad' in request.POST and request.POST['necesidad'] != ''):
                    tema = request.POST.get('tema_tratado')
                    estrategias = request.POST.get('estrategias')
                    instrumentos = request.POST.get('instrumentos')

                    estrategia_ids = json.loads(estrategias) if estrategias else []
                    instrumento_ids = json.loads(instrumentos) if instrumentos else []

                    tutoria_id = request.POST.get('id')
                    if TutoriaPedagogica.objects.filter(pk=tutoria_id).exists():
                        tutoria = TutoriaPedagogica.objects.get(pk=tutoria_id)

                        if DetalleTutoriaPedagogica.objects.filter(tutoria=tutoria).exists():
                            detalletutoria = DetalleTutoriaPedagogica.objects.filter(tutoria=tutoria).last()
                            detalletutoria.tema_tratado=tema
                            detalletutoria.finalizado=True
                            detalletutoria.save()
                            for estrategia_id in estrategia_ids:
                                if EstrategiasPedagogicas.objects.filter(id=estrategia_id).exists():
                                    estrategia = EstrategiasPedagogicas.objects.get(id=estrategia_id)
                                    detalleestrategia = DetalleEstrategiasPedagogicas(estrategia=estrategia,
                                                                                            detallepedagogica=detalletutoria,
                                                                                            usercrea=request.user,
                                                                                            fecha=datetime.now().date())
                                    detalleestrategia.save()
                            for instrumento_id in instrumento_ids:
                                if InstrumentosTutoriaPedagogicas.objects.filter(id=instrumento_id).exists():
                                    instrumento = InstrumentosTutoriaPedagogicas.objects.get(id=instrumento_id)
                                    detalleinstrumento = DetalleInstrumentosTutoriaPedagogicas(instrumento=instrumento,
                                                                                                detallepedagogica=detalletutoria,
                                                                                                usercrea=request.user,
                                                                                                fecha=datetime.now().date())
                                    detalleinstrumento.save()
                            if not 'final' in request.POST:
                                detalle_tutoria_nueva = DetalleTutoriaPedagogica(tutoria=tutoria,
                                                                           fecha_tutoria=request.POST['fecha_tutoria'],
                                                                           hora_inicio_tutoria=request.POST['horainicio'],
                                                                           hora_fin_tutoria=request.POST['horafin'],
                                                                           necesidad=request.POST['necesidad'])
                                detalle_tutoria_nueva.save()
                                if request.POST['via'] == 'true':
                                    detalle_tutoria_nueva.via_tutoria = True
                                else:
                                    detalle_tutoria_nueva.via_tutoria = False
                            # if tutoria.numero_tutoria>1:
                            if DetalleTutoriaPedagogica.objects.filter(tutoria=tutoria, finalizado=True).count()< tutoria.numero_tutoria:
                                    return HttpResponse(json.dumps({"result": "ok","tutoriaid":tutoria.id,
                                                                    "message": 'SE AGREGO CORRRECTAMENTE LA TUTORIA PEDAGOGICA'}),content_type="application/json")
                            else:
                                tutoria.finalizado=True
                                tutoria.save()

                                return HttpResponse(json.dumps({"result": "ok",
                                                                "message": 'SE AGREGO CORRRECTAMENTE LA TUTORIA PEDAGOGICA'}),
                                                    content_type="application/json")
                else:
                    return HttpResponse(json.dumps({"result": "bad",
                                                    "message": 'DEBE INGRESAR LA FECHA Y HORA DE LA PROXIMA TUTORIA'}),
                                        content_type="application/json")

            if action == 'guardarHorarioTutoria':
                tutoria_id = request.POST.get('id_tutoria')
                if TutoriaPedagogica.objects.filter(pk=tutoria_id).exists():
                    tutoria = TutoriaPedagogica.objects.get(pk=tutoria_id)
                    detalle_tutoria = DetalleTutoriaPedagogica(tutoria=tutoria,
                                                               fecha_tutoria=request.POST['fecha_tutoria'],
                                                               hora_inicio_tutoria=request.POST['horainicio'],
                                                               hora_fin_tutoria=request.POST['horafin'],
                                                               necesidad=request.POST['necesidad'])
                    detalle_tutoria.save()
                    if request.POST['via'] == 'true':
                        detalle_tutoria.via_tutoria = True
                    else:
                        detalle_tutoria.via_tutoria = False
                    detalle_tutoria.save()
                    return HttpResponse(json.dumps({"result": "ok",
                                                    "message": 'SE AGREGO CORRRECTAMENTE LA TUTORIA PEDAGOGICA'}),
                                        content_type="application/json")

            if action == ' eliminar_tutoria':
                try:
                    if TutoriaPedagogica.objects.filter(pk=request.POST['id']).exists():
                        tutoria=TutoriaPedagogica.objects.filter(pk=request.POST['id'])[:1].get()

                        client_address = ip_client_address(request)

                        LogEntry.objects.log_action(
                            user_id=request.user.pk,
                            content_type_id=ContentType.objects.get_for_model(tutoria).pk,
                            object_id=tutoria.id,
                            object_repr=force_str(tutoria),
                            action_flag=CHANGE,
                            change_message='Eliminar Tutoria Pedagogica'+' (' + client_address + ')')

                        return HttpResponse(json.dumps({"result": "ok",
                                                        "message": 'SE ELIMINO CORRRECTAMENTE LA TUTORIA PEDAGOGICA'}),
                                            content_type="application/json")

                except Exception as ex:
                    print(ex)
                    return HttpResponse(json.dumps({"result": "bad", "message": ex}), content_type="application/json")

# <---------------------------------------------------------Acciones De ESTRATEGIA PEDAGOGICA-----------------------------------------------------------------------------#}

            if action == 'agregarestrategiaspedagogicas':
                try:
                    nombre = request.POST['nombre']
                    nombre = nombre.upper()

                    estado = True if request.POST['estado'] == 'true' else False
                    estrategiaspedagogicas = EstrategiasPedagogicas(nombre=nombre, estado=estado)
                    estrategiaspedagogicas.save()
                    client_address = ip_client_address(request)

                    LogEntry.objects.log_action(
                        user_id=request.user.pk,
                        content_type_id=ContentType.objects.get_for_model(estrategiaspedagogicas).pk,
                        object_id=estrategiaspedagogicas.id,
                        object_repr=force_str(estrategiaspedagogicas),
                        action_flag=CHANGE,
                        change_message='APROBAR/RECHAZAR LA TUTORIA PEDAGOGICA - PROFESOR:' + str(' (' + client_address + ')'))

                    return HttpResponse(json.dumps({"result": "ok",
                                                    "message": 'SE AGREGO CORRRECTAMENTE LA informacion'}),
                                        content_type="application/json")

                except Exception as ex:
                    print(ex)
                    return HttpResponse(json.dumps({"result": "bad", "message": ex}), content_type="application/json")

            if action == 'editarestrategiaspedagogicas':
                try:
                    id = int(request.POST['id'])
                    nombre = request.POST['nombre']
                    nombre = nombre.upper()
                    estado = True if request.POST['estado'] == 'true' else False
                    estrategiaspedagogicas = EstrategiasPedagogicas.objects.get(id=id)
                    estrategiaspedagogicas.nombre = nombre
                    estrategiaspedagogicas.estado = estado
                    estrategiaspedagogicas.save()
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id=request.user.pk,
                        content_type_id=ContentType.objects.get_for_model(estrategiaspedagogicas).pk,
                        object_id=estrategiaspedagogicas.id,
                        object_repr=force_str(estrategiaspedagogicas),
                        action_flag=CHANGE,
                        change_message='Actualizar:' + str(
                            ' (' + client_address + ')'))
                    return HttpResponse(json.dumps({'result': 'ok'}), content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}),
                                        content_type="application/json")


            if action == 'eliminarestrategiaspedagogicas':
                try:
                    estrategiaspedagogicas = EstrategiasPedagogicas.objects.get(id=request.POST['id'])
                    estrategiaspedagogicas.delete()

                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id=request.user.pk,
                        content_type_id=ContentType.objects.get_for_model(estrategiaspedagogicas).pk,
                        object_id=estrategiaspedagogicas.id,
                        object_repr=force_str(estrategiaspedagogicas),
                        action_flag=DELETION,
                        change_message='Eliminación  (' + client_address + ')')
                    return HttpResponse(json.dumps({'result': 'ok'}), content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}),
                                        content_type="application/json")

 # <---------------------------------------------------------Acciones De IMSTRUMENTO PEDAGOGICA-----------------------------------------------------------------------------#}

            if action == 'agregarinstrumentostutoriapedagogicas':
                try:
                    nombre = request.POST['nombre']
                    nombre = nombre.upper()

                    estado = True if request.POST['estado'] == 'true' else False
                    instrumentostutoriapedagogicas = InstrumentosTutoriaPedagogicas(nombre=nombre, estado=estado)
                    instrumentostutoriapedagogicas.save()
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id=request.user.pk,
                        content_type_id=ContentType.objects.get_for_model(instrumentostutoriapedagogicas).pk,
                        object_id=instrumentostutoriapedagogicas.id,
                        object_repr=force_str(instrumentostutoriapedagogicas),
                        action_flag=ADDITION,
                        change_message='APROBAR/RECHAZAR LA TUTORIA PEDAGOGICA - PROFESOR:' + str(
                            ' (' + client_address + ')'))

                    return HttpResponse(json.dumps({"result": "ok",
                                                    "message": 'SE AGREGO CORRRECTAMENTE LA informacion'}),
                                        content_type="application/json")

                except Exception as ex:
                    print(ex)
                    return HttpResponse(json.dumps({"result": "bad", "message": ex}), content_type="application/json")

            if action == 'editarinstrumentostutoriapedagogicas':
                try:
                    id = int(request.POST['id'])
                    nombre = request.POST['nombre']
                    nombre = nombre.upper()
                    estado = True if request.POST['estado'] == 'true' else False
                    instrumentostutoriapedagogicas = InstrumentosTutoriaPedagogicas.objects.get(id=id)
                    instrumentostutoriapedagogicas.nombre = nombre
                    instrumentostutoriapedagogicas.estado = estado
                    instrumentostutoriapedagogicas.save()
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id=request.user.pk,
                        content_type_id=ContentType.objects.get_for_model(instrumentostutoriapedagogicas).pk,
                        object_id=instrumentostutoriapedagogicas.id,
                        object_repr=force_str(instrumentostutoriapedagogicas),
                        action_flag=CHANGE,
                        change_message='Actualizar:' + str(
                            ' (' + client_address + ')'))
                    return HttpResponse(json.dumps({'result': 'ok'}), content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}),
                                        content_type="application/json")

            if action == 'eliminarinstrumentostutoriapedagogicas':
                try:
                    instrumentostutoriapedagogicas = InstrumentosTutoriaPedagogicas.objects.get(id=request.POST['id'])
                    instrumentostutoriapedagogicas.delete()

                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id=request.user.pk,
                        content_type_id=ContentType.objects.get_for_model(instrumentostutoriapedagogicas).pk,
                        object_id=instrumentostutoriapedagogicas.id,
                        object_repr=force_str(instrumentostutoriapedagogicas),
                        action_flag=DELETION,
                        change_message='Eliminación  (' + client_address + ')')
                    return HttpResponse(json.dumps({'result': 'ok'}), content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}),
                                        content_type="application/json")

            if action == 'generarreporte':
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







                    col = 3


                    fechainicio = request.POST['fechainicio']
                    fechafin = request.POST['fechafin']

                    ws.write(2, 0, "fecha inicio")
                    ws.write(2, 1, str(fechainicio))
                    ws.write(3, 0, "fecha final")
                    ws.write(3, 1, str(fechafin))



                    fila = 4
                    detalle = DetalleTutoriaPedagogica.objects.filter(fecha_tutoria__range=(fechainicio, fechafin))

                    if request.POST['cmbprofesor'] != "0":
                        profesor = Profesor.objects.filter(id=request.POST['cmbprofesor'])[:1].get()
                        detalle = detalle.filter(tutoria__profesor=profesor).order_by('id')
                        ws.write(fila, 0, "Profesor")
                        ws.write(fila, 1, elimina_tildes(profesor.persona.nombre_completo_inverso()))
                        fila += 1

                    if request.POST['cmbperiodo'] != "0":
                        periodo = Periodo.objects.filter(id=request.POST['cmbperiodo'])[:1].get()
                        detalle = detalle.filter(tutoria__materia__nivel__periodo=periodo).order_by('id')
                        ws.write(fila, 0, "Periodo")
                        ws.write(fila, 1, elimina_tildes(periodo.nombre))
                        fila += 1

                    fila += 1

                    ws.write_merge(fila, fila, 0,3 , "Tutoria", titulo2)
                    ws.write(fila+1, 0, "fecha", titulo)
                    ws.write(fila+1, 1, "Profesor", titulo)
                    ws.write(fila+1, 2, "periodo", titulo)

                    ws.write_merge(fila,fila, 5,11, "Detalle", titulo2)
                    ws.write(fila+1, 3, "Materia", titulo)
                    ws.write(fila+1, 4, "Hora Inicio Tutoria", titulo)
                    ws.write(fila+1, 5, "Hora Fin Tutoria", titulo)
                    ws.write(fila+1, 6, "Via Tutoria", titulo)
                    ws.write(fila+1, 7, "Necesidad", titulo)
                    ws.write(fila+1, 8, "Tema", titulo)
                    ws.write(fila+1, 9, "Finalizado", titulo)
                    ws.write(fila+1, 10, "Aprobado", titulo)

                    fila +=2
                    for c in detalle:



                        ws.write(fila, 0, elimina_tildes(c.fecha_tutoria))
                        ws.col(0).width = 10 * 300
                        ws.write(fila, 1, elimina_tildes(c.tutoria.profesor.persona.nombre_completo_inverso()))
                        ws.col(1).width = 10 * 1000
                        ws.write(fila, 2, elimina_tildes(c.tutoria.materia.nivel.periodo))
                        ws.col(2).width = 10 * 1000


                        ws.write(fila, 3, elimina_tildes(c.tutoria.materia.asignatura.nombre))
                        ws.col(3).width = 10 * 1000
                        ws.write(fila, 4, elimina_tildes(c.hora_inicio_tutoria))
                        ws.col(4).width = 10 * 300
                        ws.write(fila, 5, elimina_tildes(c.hora_fin_tutoria))
                        ws.col(5).width = 10 * 300
                        ws.write(fila, 6, elimina_tildes(c. via_tutoria) if c.via_tutoria else '')
                        ws.col(6).width = 10 * 300
                        ws.write(fila, 7, elimina_tildes(c.necesidad))
                        ws.col(7).width = 10 * 300
                        ws.write(fila, 8, elimina_tildes(c.tema_tratado) if c.tema_tratado else '')
                        ws.col(8).width = 10 * 300
                        ws.write(fila, 9, "SI" if c.finalizado else "NO")
                        ws.col(9).width = 10 * 300
                        ws.write(fila, 10, "SI" if c.aprobado_inscrip else "NO")
                        ws.col(10).width = 10 * 300
                        fila +=1
                        col = col + 1


                    fila += 2
                    ws.write(fila, 0, "Fecha Impresion", subtitulo)
                    ws.write(fila, 1, str(datetime.now()), subtitulo)
                    ws.write(fila + 1, 0, "Usuario", subtitulo)
                    ws.write(fila + 1, 1, str(request.user), subtitulo)

                    nombre = 'reporte' + str(datetime.now()).replace(" ", "").replace(".", "").replace(":", "") + '.xls'
                    wb.save(MEDIA_ROOT + '/reporteexcel/' + nombre)
                    return HttpResponse(json.dumps({"result": "ok", "url": "/media/reporteexcel/" + nombre}),
                                        content_type="application/json")

                    return HttpResponse(json.dumps({"result": "ok"}), content_type="application/json")
                except Exception as ex:
                    print(ex)
                    return HttpResponse(json.dumps({"result": "bad", "message": ex}), content_type="application/json")

        else:
                data = {'title': 'REPORTE'}
                addUserData(request,data)
                if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                    reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                    data['reportes'] = reportes
                    data['generarform']=XLSPeriodoForm()



    else:
        search = None
        tutoria = None
        filtro = None
        rechazadas = None
        cargo = None
        data = {'title': 'Tutorias Pedagogicas'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action =='verdetalletutoria':
                if TutoriaPedagogica.objects.filter(pk=request.GET['id']).exists():
                    tutoria=TutoriaPedagogica.objects.filter(pk=request.GET['id'])[:1].get()
                    if DetalleTutoriaPedagogica.objects.filter(tutoria=tutoria).exists():
                        detalletutoria=DetalleTutoriaPedagogica.objects.filter(tutoria=tutoria)
                        data['tutoria']=detalletutoria
                        data['tutoriainfo']=tutoria
                        return render(request, "tutoria_pedagogica/detalle_tutoria.html", data)

        if 'action' in request.GET:
            action = request.GET['action']
            if action == 'estrategia_pedagogica':
                data['title'] = 'Estrategia Pedagogica'

                if 's' in request.GET:
                    search = request.GET['s']
                    estrategia_pedagogica = EstrategiasPedagogicas.objects.filter(nombre__icontains=search)
                else:
                    estrategia_pedagogica = EstrategiasPedagogicas.objects.filter().order_by("nombre")

                paging = MiPaginador(estrategia_pedagogica, 20)
                p = 1

                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                    paging = MiPaginador(estrategia_pedagogica, 20)
                    page = paging.page(p)
                except Exception as ex:
                    page = paging.page(1)

                data['paging'] = paging
                data['rangospaging'] = paging.rangos_paginado(p)
                data['page'] = page
                data['paging'] = paging
                data['estrategia_pedagogica'] = page.object_list
                data['search'] = search if search else ""
                return render(request, "tutoria_pedagogica/estrategia_pedagogica.html", data)

        if 'action' in request.GET:
            action = request.GET['action']
            if action == 'instrumentostutoriapedagogicas':
                data['title'] = 'Instrumento Pedagogico '

                if 's' in request.GET:
                    search = request.GET['s']
                    ipedagogica = InstrumentosTutoriaPedagogicas.objects.filter(nombre__icontains=search)
                else:
                    ipedagogica = InstrumentosTutoriaPedagogicas.objects.filter().order_by("nombre")

                paging = MiPaginador(ipedagogica, 20)
                p = 1

                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                    paging = MiPaginador(ipedagogica, 20)
                    page = paging.page(p)
                except Exception as ex:
                    page = paging.page(1)

                data['paging'] = paging
                data['rangospaging'] = paging.rangos_paginado(p)
                data['page'] = page
                data['paging'] = paging
                data['instrumentostutoriapedagogicas'] = page.object_list
                data['search'] = search if search else ""
                return render(request, "tutoria_pedagogica/instrumentostutoriapedagogicas.html", data)

        else:
            try:

                if 'filter' in request.GET:
                    filtro = request.GET['filter']
                    data['filtro']  = filtro

                if 's' in request.GET:
                    search = request.GET['s']
                if 'rechazadas' in request.GET:
                    rechazadas = request.GET['rechazadas']
                if search:
                    try:
                        ss = search.split(' ')
                        while '' in ss:
                            ss.remove('')
                        if len(ss)==1:
                            tutoria= TutoriaPedagogica.objects.filter(Q(materia__asignatura__nombre__icontains=search)
                                                                      | Q(profesor__persona__nombres__icontains=search)|
                                                                      Q(profesor__persona__apellido1__icontains=search) | Q(
                            profesor__persona__apellido2__icontains=search) | Q(profesor__persona__cedula__icontains=search)).order_by('materia__asignatura__nombre')
                        else:
                            tutoria = TutoriaPedagogica.objects.filter(materia__asignatura__nombre__icontains=ss[0]) .order_by('materia__asignatura__nombre')
                    except Exception as e:
                        pass
                else:
                    if Profesor.objects.filter(persona__usuario=request.user).exists():
                         data['nover']=1
                         data['profesor']=1

                         tutoria = TutoriaPedagogica.objects.filter(profesor__persona__usuario=request.user).order_by('materia__asignatura__nombre')
                    elif Inscripcion.objects.filter(persona__usuario=request.user).exists():
                         data['nover']=1

                         inscr=EstudianteTutoriaPedagogica.objects.filter(estudiante__persona__usuario=request.user).values('tutoria__id')
                         tutoria = TutoriaPedagogica.objects.filter(id__in=inscr).order_by(
                             'materia__asignatura__nombre')
                    else:
                        tutoria = TutoriaPedagogica.objects.all().order_by('materia__asignatura__nombre')
                if rechazadas:
                    tutoria = TutoriaPedagogica.objects.filter(aceptada=False).order_by('materia__asignatura__nombre')
                    data['rechazada']=1
                paging = MiPaginador(tutoria, 30)
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

                data['tutoria'] = page.object_list
                data['estrategias'] = EstrategiasPedagogicas.objects.filter()
                data['instrumentos'] = InstrumentosTutoriaPedagogicas.objects.filter()
                data['periodo'] = Periodo.objects.filter()
                data['profesor'] = Profesor.objects.filter()
                if 'error' in request.GET:
                    data['error']= request.GET['error']
                return render(request ,"tutoria_pedagogica/tutoria_pedagogica.html" ,  data)
            except Exception as e:
                print('error '+str(e))
                return HttpResponseRedirect("/?info=1")