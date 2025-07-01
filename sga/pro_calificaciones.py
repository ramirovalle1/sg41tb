import io
import os
import sys
import json
import random
import subprocess
import xlrd
from datetime import datetime, time, timedelta
from django.contrib.auth.decorators import login_required
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from django.forms.models import model_to_dict
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, Http404, JsonResponse
from django.shortcuts import render, redirect
from django.template.context import RequestContext
from django.db.models.query_utils import Q
from django.template.loader import get_template
from django.utils.encoding import force_str
from decorators import secure_module
from sga.funciones import actualizar_nota_cuadro_calificacion, null_to_decimal, null_to_numeric
from settings import NOTA_PARA_APROBAR, ASIST_PARA_APROBAR, ASIST_PARA_SEGUIR, NOTA_ESTADO_APROBADO, \
    NOTA_ESTADO_REPROBADO, NOTA_ESTADO_EN_CURSO, PORCIENTO_NOTA1, PORCIENTO_NOTA4, PORCIENTO_NOTA3, PORCIENTO_NOTA2, \
    PORCIENTO_NOTA5, NOTA_ESTADO_SUPLETORIO, NOTA_PARA_SUPLET, EVALUACION_IAVQ, MODELO_EVALUACION, EVALUACION_ITB, \
    REPORTE_ACTA_NOTAS, EVALUACION_ITS, VALIDAR_ASISTENCIAS, MODULO_FINANZAS_ACTIVO, PAGO_ESTRICTO, DATOS_ESTRICTO, \
    EVALUACION_TES, VALIDA_DEUDA_EVALUACIONES, EVALUACION_IGAD, CENTRO_EXTERNO, EVALUACION_CASADE, \
    PROFE_PRACT_CONDUCCION, EMAIL_ACTIVE, VALIDA_CLAVE_CALIFICACION, TIPOSEGMENTO_PRACT, INSCRIPCION_CONDUCCION, \
    VALIDA_DEUDA_EXAM_ASIST, ID_TIPO_ESPECIE_REG_NOTA, DIAS_ESPECIE, ASIGNATURA_PRACTICA_CONDUCCION, ASIG_VINCULACION, \
    ASIG_PRATICA, \
    MIN_APROBACION, MAX_APROBACION, MIN_RECUPERACION, MAX_RECUPERACION, MIN_EXAMEN, MAX_EXAMEN, MIN_EXAMENRECUPERACION, \
    DEFAULT_PASSWORD, NIVEL_SEMINARIO, MULTA24H, MULTA48H, \
    MATERIA_PRAC_ENFERMERIA, NOTA_ESTADO_DERECHOEXAMEN, MEDIA_ROOT

from sga.commonviews import addUserData, ip_client_address

from sga.tasks import plaintext2html
from sga.finanzas import generador_especies

from sga.tasks import send_html_mail
from sga.finanzas import convertir_fecha


@login_required(redirect_field_name='ret', login_url='/login')
# @secure_module
def view(request):
    hoy = datetime.now().date()

    if request.method == 'POST':
        if 'action' in request.POST:
            action = request.POST['action']
            if action == 'loadSegmento':
                return ViewNotas.render_load_segmento(request)
            elif action == 'changeNota':
                return ViewNotas.render_change_nota(request)
            elif action == 'changeEstadoMateriaAsignada':
                return ViewNotas.render_change_estado(request)
            if action == 'changeEstadoMateriaTodos':
                return ViewNotas.render_change_estado_todos(request)
            elif action == 'closeMateria':
                return ViewNotas.render_close_materia(request)
            elif action == 'firmarActa':
                return ViewNotas.render_firmar_acta_calificacion(request)

        return JsonResponse({"isSuccess": False, "message": f"Acción no encontrada"})
    else:

        if 'action' in request.GET:
            action = request.GET['action']

            if action == 'generateActa':
                return ViewNotas.render_generate_acta_calificacion(request)
            elif action == 'loadFormFirma':
                return ViewNotas.render_load_form_firma(request)
            elif action == 'loadSeguimientoFirma':
                return ViewNotas.render_load_seguimiento_firma(request)
        else:
            return ViewNotas.render_load_init(request)


class ViewNotas:

    @staticmethod
    def render_load_segmento(request: HttpRequest) -> JsonResponse:
        from sga.models import Materia, Reporte
        try:
            data = {}
            addUserData(request, data)
            ePersona = data['persona']
            id = int(request.POST.get('id', '0'))
            try:
                eMateria = Materia.objects.get(pk=id)
            except ObjectDoesNotExist:
                raise NameError(u'No se encontro materia')
            if eMateria.modelo_evaluativo is None:
                raise NameError(u"No tiene configurado modelo evaluativo")
            data['eMateria'] = eMateria
            # data['cronograma'] = materia.cronogramacalificaciones()
            # data['usacronograma'] = materia.usaperiodocalificaciones
            # data['usa_evaluacion_integral'] = USA_EVALUACION_INTEGRAL
            data['MODULO_FINANZAS_ACTIVO'] = MODULO_FINANZAS_ACTIVO
            data['VALIDA_DEUDA_EVALUACIONES'] = VALIDA_DEUDA_EVALUACIONES
            data['VALIDA_DEUDA_EXAM_ASIST'] = not VALIDA_DEUDA_EXAM_ASIST
            data['PAGO_ESTRICTO'] = PAGO_ESTRICTO
            data['DATOS_ESTRICTO'] = DATOS_ESTRICTO
            if eMateria.fin is None:
                raise NameError(u"Materia no registra fecha fin de culminación")
            data['dentro_fechas'] = eMateria.fin >= datetime.now().date()
            data['NOTA_ESTADO_APROBADO'] = NOTA_ESTADO_APROBADO
            data['NOTA_ESTADO_REPROBADO'] = NOTA_ESTADO_REPROBADO
            data['NOTA_ESTADO_EN_CURSO'] = NOTA_ESTADO_EN_CURSO
            data['NOTA_ESTADO_SUPLETORIO'] = NOTA_ESTADO_SUPLETORIO
            data['eRepositorioActaCalificacion'] = eRepositorioActaCalificacion = eMateria.mi_repositorio_acta_calificacion()
            data['tiene_firmada_acta'] = eRepositorioActaCalificacion.tiene_firmada_acta(ePersona.id)
            data['eFirmaActaCalificacion'] = eRepositorioActaCalificacion.mi_acta_firmada(ePersona.id)
            data['puede_firmar'] = eRepositorioActaCalificacion.puede_firmar(ePersona.id)
            data['eReporte'] = Reporte.objects.filter(nombre='acta_calificaciones_modelo_evaluativo').first()
            template = get_template("pro_calificaciones/segmento.html")
            json_content = template.render(data)
            return JsonResponse({"isSuccess": True, "message": f"Se obtuvo cuadro de calificación correctamente", "html": json_content})
        except Exception as ex:
            print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
            return JsonResponse({"isSuccess": False, "message": f"Error al obtener los datos. {ex.__str__()}"})

    @staticmethod
    def render_change_nota(request: HttpRequest) -> JsonResponse:
        from sga.models import MateriaAsignada
        with transaction.atomic():
            try:
                maid = request.POST.get('maid', 0)
                try:
                    eMateriaAsignada = MateriaAsignada.objects.get(pk=maid)
                except ObjectDoesNotExist:
                    raise NameError(u"No se encontro materia asignada valida")
                campo = request.POST.get('sel', None)
                if campo is None:
                    raise NameError(u"Campo no identificado")
                valor = request.POST.get('val', None)
                if valor is None:
                    raise NameError(u"Valor no identificado")
                result = actualizar_nota_cuadro_calificacion(eMateriaAsignada.id, campo.upper().strip(), valor)
                isSuccess = result.get('isSuccess', False)
                message = result.get('message', 'Ocurrio un error en el proceso')
                data = result.get('data', {})
                if not isSuccess:
                    raise NameError(message)
                return JsonResponse(
                    {"isSuccess": True, "message": f"Se obtuvo cuadro de calificación correctamente", "data": data})
            except Exception as ex:
                transaction.set_rollback(True)
                print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
                return JsonResponse({"isSuccess": False, "message": f"Error al obtener los datos. {ex.__str__()}"})

    @staticmethod
    def render_change_estado(request: HttpRequest) -> JsonResponse:
        from sga.models import MateriaAsignada, Profesor, ProfesorMateria
        with transaction.atomic():
            try:
                id = request.POST.get('id', 0)
                try:
                    eMateriaAsignada = MateriaAsignada.objects.get(pk=id)
                except ObjectDoesNotExist:
                    raise NameError(u"No se encontro materia asignada valida")

                estado = request.POST.get('estado', None)
                if estado is None:
                    raise NameError(u"Estado no identificado")
                if estado == 'true':
                    # Abrir
                    eMateriaAsignada.cerrado = False
                else:
                    eMateriaAsignada.cerrado = True

                eMateriaAsignada.fechacierre = datetime.now()
                eMateriaAsignada.save()
                eMateria = eMateriaAsignada.materia
                eModelo = eMateria.modelo_evaluativo
                d = locals()
                exec(eModelo.logica, globals(), d)
                d['calculo_modelo_evaluativo'](eMateriaAsignada)
                eMateriaAsignada.actualiza_estado()
                ePeriodo = request.session['periodo']
                if not eMateriaAsignada.absentismo and eMateriaAsignada.cerrado:
                    try:
                        eProfesor = Profesor.objects.get(persona__usuario=request.user)
                    except ObjectDoesNotExist:
                        pass
                    if eProfesor:
                        reprobado = ''
                        observacion = ''

                        if eMateriaAsignada.asistenciafinal < eModelo.asistencia_aprobar and not eMateria.nivel.carrera.online:
                            reprobado = 'REPROBADO POR ASISTENCIA'
                            observacion = "Acercarse a justificar la asistencia"
                        if eMateriaAsignada.notafinal < NOTA_PARA_APROBAR:
                            reprobado = 'REPROBADO'
                            observacion = ""
                        eProfesorMateria = ProfesorMateria.objects.filter(
                            Q(profesor_aux=eProfesor.id) | Q(profesor=eProfesor), materia=eMateria).first()
                        if EMAIL_ACTIVE and not CENTRO_EXTERNO:
                            eMateriaAsignada.correo_alumnocierremate(eProfesorMateria, reprobado, observacion)
                # Obtain client ip address
                client_address = ip_client_address(request)
                # Log de CERRAR MATERIA ASIGNADA
                LogEntry.objects.log_action(user_id=request.user.pk,
                                            content_type_id=ContentType.objects.get_for_model(eMateriaAsignada).pk,
                                            object_id=eMateriaAsignada.id,
                                            object_repr=force_str(eMateriaAsignada),
                                            action_flag=CHANGE,
                                            change_message='Cerrada la Materia Asignada (' + client_address + ')')
                data = {
                    'cerrado': eMateriaAsignada.cerrado,
                    'tienedeuda': eMateriaAsignada.matricula.inscripcion.tiene_deuda_evaluacion(),
                    'tienemateriaasignadaabierta': eMateriaAsignada.materia.cerrar_disponible(ePeriodo),
                    'acta_entregada': eMateriaAsignada.materia.acta_entregada(),
                    'nota_final': eMateriaAsignada.notafinal,
                    'estado_display': eMateriaAsignada.estado.nombre.lower().capitalize(),
                    'estado_id': eMateriaAsignada.estado_id
                }
                return JsonResponse(
                    {"isSuccess": True, "message": f"Se cambio correctamente el estado", "data": data})
            except Exception as ex:
                transaction.set_rollback(True)
                print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
                return JsonResponse({"isSuccess": False, "message": f"Error al obtener los datos. {ex.__str__()}"})

    @staticmethod
    def render_change_estado_todos(request: HttpRequest) -> JsonResponse:
        from sga.models import MateriaAsignada, Profesor, ProfesorMateria, Materia
        with transaction.atomic():
            try:
                id = request.POST.get('id', 0)
                try:
                    eMateria = Materia.objects.get(pk=id)
                except ObjectDoesNotExist:
                    raise NameError(u"No se encontro materia valida")
                eModelo = eMateria.modelo_evaluativo
                for eMateriaAsignada in MateriaAsignada.objects.filter(materia=eMateria):
                    eMateriaAsignada.cerrado = not eMateriaAsignada.cerrado
                    eMateriaAsignada.fechacierre = datetime.now().date()
                    eMateriaAsignada.save()
                    d = locals()
                    exec(eModelo.logica, globals(), d)
                    d['calculo_modelo_evaluativo'](eMateriaAsignada)
                    eMateriaAsignada.actualiza_estado()
                return JsonResponse({"isSuccess": True, "message": f"Se abrio o cerro correctamente"})
            except Exception as ex:
                transaction.set_rollback(True)
                print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
                return JsonResponse({"isSuccess": False, "message": f"Error al obtener los datos. {ex.__str__()}"})

    @staticmethod
    def render_close_materia(request: HttpRequest) -> JsonResponse:
        from sga.models import (MateriaAsignada, Materia, Profesor, ProfesorMateria, Inscripcion)
        from firmaec.models import RepositorioActaCalificacion
        with transaction.atomic():
            try:
                id = request.POST.get('id', 0)
                try:
                    eMateria = Materia.objects.get(pk=id)
                except ObjectDoesNotExist:
                    raise NameError(u"No se encontro materia valida")
                ahora = datetime.now()
                inscripcion_ids = []
                eMateriaAsignadas = MateriaAsignada.objects.filter(materia=eMateria)
                for eMateriaAsignada in eMateriaAsignadas:
                    eMateriaAsignada.cerrado = True
                    eMateriaAsignada.fechacierre = ahora.date()
                    eMateriaAsignada.save()
                    eMateriaAsignada.actualiza_estado()
                    inscripcion_ids.append(eMateriaAsignada.id)
                eMateria.cerrado = True
                eMateria.fechacierre = ahora
                eMateria.fechaalcance = ahora + timedelta(days=14)
                # eMateria.horacierre = datetime.now().time()
                eMateria.save()
                eProfesor = Profesor.objects.filter(persona__usuario=request.user).first()
                if eProfesor:
                    eNivel = eMateriaAsignadas.first().matricula.nivel
                    eInscripciones = Inscripcion.objects.filter(id__in=inscripcion_ids).exclude(retiradomatricula__activo=False, retiradomatricula__nivel=eNivel)
                    eProfesorMateria = ProfesorMateria.objects.filter(materia=eMateria).filter(Q(profesor_aux=eProfesor.id) | Q(profesor=eProfesor)).first()
                    common_filters = Q(matricula__inscripcion__in=eInscripciones)
                    attendance_filters = Q(absentismo=None) | Q(absentismo=False)
                    total_students = eMateriaAsignadas.filter(common_filters, attendance_filters)
                    count_total = total_students.count()
                    total_reprobado = total_students.filter(estado_id=NOTA_ESTADO_REPROBADO).count()
                    total_aprobado = total_students.filter(estado_id=NOTA_ESTADO_APROBADO).count()
                    total_encurso = total_students.filter(estado_id=NOTA_ESTADO_EN_CURSO).count()
                    total_recuperacion = total_students.filter(estado_id=NOTA_ESTADO_SUPLETORIO).count()
                    total_examen = total_students.filter(estado_id=5).count()
                    if count_total > 0:


                        promedio_reprobado = int(round(total_reprobado * 100 / count_total))
                        promedio_aprobado = int(round(total_aprobado * 100 / count_total))

                        if eProfesorMateria.materia.nivel.carrera.online:
                            resum_reprobado_asist = 0
                            resum_reprobado_nota = total_reprobado
                        else:
                            resum_reprobado_asist = 0
                            resum_reprobado_nota = total_students.filter(estado_id=NOTA_ESTADO_APROBADO).count()
                    else:
                        promedio_reprobado = promedio_aprobado = resum_reprobado_nota = resum_reprobado_asist = 0

                    total_alumnos = eMateriaAsignadas.filter(matricula__inscripcion__in=eInscripciones).count()
                    total_alumno_abs = eMateriaAsignadas.filter(matricula__inscripcion__in=eInscripciones, absentismo=True).count()
                    total_becados = eMateriaAsignadas.filter(Q(matricula__inscripcion__in=eInscripciones, matricula__becado=True) & attendance_filters).count()
                    tot_estudiantes = total_alumnos - total_encurso - total_alumno_abs
                    if tot_estudiantes > 0:
                        promedio_aprobado = int(round(total_aprobado * 100 / tot_estudiantes))
                        promedio_reprobado = int(round(total_reprobado * 100 / tot_estudiantes))
                        promedio_recuperacion = int(round(total_recuperacion * 100 / tot_estudiantes))
                        promedio_examen = int(round(total_examen * 100 / tot_estudiantes))
                    else:
                        promedio_aprobado = promedio_reprobado = promedio_recuperacion = promedio_examen = 0

                    if EMAIL_ACTIVE and not CENTRO_EXTERNO:
                        eMateria.correo_promedio(
                            total_alumnos, total_alumno_abs, total_aprobado, promedio_aprobado,
                            promedio_reprobado, eProfesorMateria, total_becados, total_reprobado,
                            total_encurso, total_recuperacion, tot_estudiantes, promedio_recuperacion,
                            total_examen, promedio_examen
                        )
                # Log cerrarmateriade CERRAR MATERIA
                LogEntry.objects.log_action(
                    user_id=request.user.pk,
                    content_type_id=ContentType.objects.get_for_model(eMateria).pk,
                    object_id=eMateria.id,
                    object_repr=force_str(eMateria),
                    action_flag=CHANGE,
                    change_message='Cerrada la Materia')

                eRepositorioActaCalificacion = eMateria.mi_repositorio_acta_calificacion()
                eRepositorioActaCalificacion.estado = RepositorioActaCalificacion.Estados.Pendiente
                eRepositorioActaCalificacion.archivo_inicial = None
                eRepositorioActaCalificacion.save()
                eRepositorioActaCalificacion.secuencia_firma().update(fecha=None, subido=False, archivo=None)

                return JsonResponse({"isSuccess": True, "message": f"Se cerro la materia correctamente"})
            except Exception as ex:
                transaction.set_rollback(True)
                print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
                return JsonResponse({"isSuccess": False, "message": f"Error al obtener los datos. {ex.__str__()}"})

    @staticmethod
    def render_load_init(request: HttpRequest) -> HttpResponse:
        from sga.models import Profesor, Materia
        try:
            data = {}
            addUserData(request, data)
            persona = data['persona']
            data['title'] = 'Evaluaciones de estudiante'
            data['eProfesor'] = eProfesor = Profesor.objects.get(persona=persona)
            data['ePeriodo'] = ePeriodo = request.session['periodo']
            data['DEFAULT_PASSWORD'] = DEFAULT_PASSWORD
            data['utiliza_validacion_calificaciones'] = VALIDA_CLAVE_CALIFICACION
            data['habilitado_ingreso_calificaciones'] = True
            filtro = Q(nivel__periodo=ePeriodo)
            if eProfesor.categoria_id == PROFE_PRACT_CONDUCCION:
                filtro &= Q(profesormateria__profesor_aux=eProfesor.id)
            else:
                if eProfesor.id == 428:
                    filtro &= Q(Q(profesormateria__profesor=eProfesor, profesormateria__profesor_aux=None) | Q(
                        profesormateria__profesor_aux=eProfesor.id))
                else:
                    filtro &= Q(Q(profesormateria__profesor=eProfesor, profesormateria__profesor_aux=None,
                                  profesormateria__aceptacion=True) | Q(profesormateria__profesor_aux=eProfesor.id,
                                                                        profesormateria__aceptacion=True))
            data['eMaterias'] = eMaterias = Materia.objects.filter(filtro)

            idm = int(request.GET.get('idm', '0'))
            eMateria = None
            if int(idm) > 0:
                eMateria = eMaterias.filter(pk=idm).first()
                if not eMateria:
                    data['aMensajeError'] = {'title': "Error de consulta",
                                             'body': "Materia no asignada"}
                else:
                    idm = eMateria.id
            data['idm'] = idm
            data['eMateria'] = eMateria

            return render(request, "pro_calificaciones/view.html", data)
        except Exception as ex:
            return redirect(f"/?info={ex.__str__()}")

    @staticmethod
    def render_generate_acta_calificacion(request: HttpRequest) -> JsonResponse:
        from sga.models import Profesor, Materia, Reporte
        from firmaec.models import RepositorioActaCalificacion, Solicitud, SolicitudCancelada
        from documental.models import Repositorio
        from sga.reportes import transform_jasperstarter, elimina_tildes
        from settings import (JR_JAVA_COMMAND, DATABASES, JR_DB_TYPE, SITE_ROOT, JR_USEROUTPUT_FOLDER,
                              JR_RUN, MEDIA_URL, DEBUG)
        from django.core.files import File as DjangoFile
        from sga.funciones import remover_caracteres_especiales_unicode
        with transaction.atomic():
            try:
                SUBREPOTRS_FOLDER = os.path.join(SITE_ROOT, 'media', 'reportes', 'encabezados_pies', '')
                rid = request.GET.get('rid', 0)
                try:
                    eReporte = Reporte.objects.get(id=rid)
                except ObjectDoesNotExist:
                    raise NameError(u"Reporte no encontrado")
                if not eReporte.archivo:
                    raise NameError(u"Archivo del reporte no encontrado")
                tipo = request.GET.get('rt', 'pdf')
                output_folder = os.path.join(JR_USEROUTPUT_FOLDER, elimina_tildes(request.user.username))
                try:
                    os.makedirs(output_folder)
                except:
                    pass
                d = datetime.now()
                pdfname = f"{eReporte.nombre}_{d.strftime('%Y%m%d_%H%M%S')}"
                folder = os.path.join(os.path.join(JR_USEROUTPUT_FOLDER, elimina_tildes(request.user.username), ''))
                path_pdf = folder + pdfname + '.pdf'
                if os.path.isfile(path_pdf):
                    os.remove(path_pdf)
                runjrcommand = [JR_JAVA_COMMAND, '-jar',
                                os.path.join(JR_RUN, 'jasperstarter.jar'),
                                'pr', eReporte.archivo.file.name,
                                '--jdbc-dir', JR_RUN,
                                '-f', tipo,
                                '-t', 'postgres',
                                '-H', DATABASES['default']['HOST'],
                                '-n', DATABASES['default']['NAME'],
                                '-u', DATABASES['default']['USER'],
                                '-p', DATABASES['default']['PASSWORD'],
                                '--db-port', DATABASES['default']['PORT'],
                                '-o', output_folder + os.sep + pdfname]
                print(runjrcommand)
                parametros = eReporte.parametros()
                paramlist = [transform_jasperstarter(p, request) for p in parametros]
                if paramlist:
                    runjrcommand.append('-P')
                    for parm in paramlist:
                        runjrcommand.append(parm)
                runjrcommand.append(u'SUBREPORT_DIR=' + str(SUBREPOTRS_FOLDER))
                mens = ''
                mensaje = ''
                for m in runjrcommand:
                    mens += ' ' + m
                # reportfile = "/".join([JR_USEROUTPUT_FOLDER, elimina_tildes(request.user.username), pdfname + "." + tipo])
                # if DEBUG:
                #     runjr = subprocess.run(mens, shell=True, check=True)
                # else:
                #     runjr = subprocess.call(mens.encode("latin1"), shell=True)
                    # runjr = subprocess.call(mensaje, shell=True)
                print("Ejecutando comando:", ' '.join(runjrcommand))
                runjr = subprocess.run(runjrcommand, capture_output=True, text=True)

                # Verifica si el comando fue exitoso
                if runjr.returncode == 0:
                    print("PDF generado exitosamente.")
                else:
                    print("Error al generar el PDF:")
                    print(str(runjr.stderr))
                    print(str(runjr.stdout))
                    return JsonResponse({"isSuccess": True, "message": f"Error al crear el reporte error en el comando al generar el pdf"})
                sp = os.path.split(eReporte.archivo.file.name)
                # Obtain client ip address
                client_address = ip_client_address(request)
                url_pdf = "/".join([MEDIA_URL,'documentos','userreports',elimina_tildes(request.user.username), pdfname+"."+tipo])
                # url_pdf = (MEDIA_URL + '/documentos/userreports/' + str(elimina_tildes(request.user.username)) + '/' + pdfname+"."+tipo).replace('\\', '/')
                materia_id = request.GET.get('materia', 0)
                try:
                    eMateria = Materia.objects.get(id=materia_id)
                except ObjectDoesNotExist:
                    raise NameError(u"Materia no encontrada")
                with open(path_pdf, 'rb') as file:
                    file_name = f"acta_calificaciones_{eMateria.id}_original_{datetime.now().strftime('%Y%m%d%H%M%S%f')}.pdf"
                    file_obj = DjangoFile(file, name=f"{remover_caracteres_especiales_unicode(file_name)}")
                    eRepositorio = Repositorio(nombre=f'Acta de calificaciones original de la materia (id: {eMateria.id}) {eMateria.nombre_completo()}',
                                               tipo=Repositorio.Tipos.PDF,
                                               archivo=file_obj)
                    eRepositorio.save(request)
                    eRepositorioActaCalificacion = eMateria.mi_repositorio_acta_calificacion()
                    eRepositorioActaCalificacion.estado = RepositorioActaCalificacion.Estados.Generada
                    eRepositorioActaCalificacion.archivo_inicial = eRepositorio
                    eRepositorioActaCalificacion.save(request)
                    eRepositorioActaCalificacion.secuencia_firma().update(fecha=None, subido=False, archivo=None)
                    eSolicitudes = Solicitud.objects.filter(content_type=ContentType.objects.get_for_model(eMateria), object_id=eMateria.id)
                    for eSolicitud in eSolicitudes:
                        eSolicitud.estado = Solicitud.Estados.CANCELADO
                        eSolicitud.save(request)
                        try:
                            eSolicitudCancelada = SolicitudCancelada.objects.get(solicitud=eSolicitud)
                        except ObjectDoesNotExist:
                            eSolicitudCancelada = SolicitudCancelada(solicitud=eSolicitud)
                        eSolicitudCancelada.fechahora = datetime.now()
                        observacion = eSolicitudCancelada.observacion
                        observacion += f'Se cancelo el {str(eSolicitudCancelada.fechahora)} por generación de nueva acta de calificaciones'
                        eSolicitudCancelada.observacion = observacion
                        eSolicitudCancelada.save(request)
                return JsonResponse({"isSuccess": True, "message": f"Se genero el acta correctamente", "url_pdf": url_pdf})
            except Exception as ex:
                transaction.set_rollback(True)
                print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
                return JsonResponse({"isSuccess": False, "message": f"Error al obtener los datos. {ex.__str__()}"})

    @staticmethod
    def render_load_form_firma(request: HttpRequest) -> JsonResponse:
        from firmaec.forms import FirmaECForm
        from sga.models import Materia
        try:
            id = request.GET.get('id', 0)
            try:
                eMateria = Materia.objects.get(id=id)
            except ObjectDoesNotExist:
                raise NameError(u"Materia no encontrada")
            data = {}
            addUserData(request, data)
            ePersona = data['persona']
            f = FirmaECForm()
            data['form'] = f
            data['canViewVisor'] = False
            data['id'] = id
            data['action'] = 'firmarActa'
            eRepositorioActaCalificacion = eMateria.mi_repositorio_acta_calificacion()
            puede_firmar = eRepositorioActaCalificacion.puede_firmar(ePersona.id)
            if not puede_firmar:
                raise NameError(u"Profesor no puede firmar acta de calificaciones")
            template = get_template("firma_ec/forms/default.html")
            # eFirmaActaCalificacion = eRepositorioActaCalificacion.secuencia_firma().filter(responsable=ePersona).first()
            # palabras = f'{eFirmaActaCalificacion.responsable.nombre_completo()}'
            # x, y, numPage = obtener_coordenadas_firma_en_pdf(eRepositorioActaCalificacion.archivo_inicial.path, palabras)
            # if not x or not y:
            #     raise NameError('No se encontró el responsable en el documento.')
            # y = y - 5

            return JsonResponse({"isSuccess": True, "message": f"Se construyo formulario correctamente", 'html': template.render(data)})
        except Exception as ex:
            transaction.set_rollback(True)
            print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
            return JsonResponse({"isSuccess": False, "message": f"Error al obtener los datos. {ex.__str__()}"})

    @staticmethod
    def render_firmar_acta_calificacion(request: HttpRequest) -> JsonResponse:
        from sga.models import Profesor, Materia, Reporte
        from firmaec.models import RepositorioActaCalificacion, Solicitud
        from documental.models import Repositorio
        from firmaec.forms import FirmaECForm
        from sga.reportes import transform_jasperstarter, elimina_tildes
        from settings import (JR_JAVA_COMMAND, DATABASES, JR_DB_TYPE, SITE_ROOT, JR_USEROUTPUT_FOLDER,
                              JR_RUN, MEDIA_URL, DEBUG)
        from django.core.files import File as DjangoFile
        from sga.funciones import remover_caracteres_especiales_unicode
        from core.my_firma import MY_JavaFirmaEc
        from firmaec.functions import obtener_coordenadas_firma_en_pdf
        with transaction.atomic():
            try:
                data = {}
                f = None
                id = request.POST.get('id', 0)
                try:
                    eMateria = Materia.objects.get(id=id)
                except ObjectDoesNotExist:
                    raise NameError(u"Materia no encontrada")
                f = FirmaECForm(request.POST, request.FILES)
                if not f.is_valid():
                    f.addErrors(f.errors.get_json_data(escape_html=True))
                    raise NameError(u"Formulario incorrecto")
                addUserData(request, data)
                ePersona = data['persona']
                eRepositorioActaCalificacion = eMateria.mi_repositorio_acta_calificacion()
                puede_firmar = eRepositorioActaCalificacion.puede_firmar(ePersona.id)
                if not puede_firmar:
                    raise NameError(u"Profesor no puede firmar acta de calificaciones")
                eFirmaActaCalificacion = eRepositorioActaCalificacion.secuencia_firma().filter(responsable=ePersona).first()
                palabras = f'{eFirmaActaCalificacion.responsable.documento()}'
                url_archivo_a_firmar = eRepositorioActaCalificacion.archivo_inicial.archivo.path
                x, y, numPage = obtener_coordenadas_firma_en_pdf(url_archivo_a_firmar, palabras)
                if not x or not y:
                    raise NameError('No se encontró el responsable en el documento.')
                y = y + 50
                password = f.cleaned_data['password']
                firma = request.FILES["firma"]
                bytes_certificado = firma.read()
                extension_certificado = os.path.splitext(firma.name)[1][1:]
                with open(url_archivo_a_firmar, 'rb') as file:
                    archivo_a_firmar = file.read()
                datau = MY_JavaFirmaEc(archivo_a_firmar=archivo_a_firmar,
                                       archivo_certificado=bytes_certificado,
                                       extension_certificado=extension_certificado,
                                       password_certificado=password,
                                       page=numPage,
                                       reason=f'Acta de calificaciones-{elimina_tildes(eMateria.nombre_completo())}',
                                       lx=str(x),
                                       ly=str(y),
                                       ).sign_and_get_content_bytes()
                archivo_a_firmar = io.BytesIO()
                archivo_a_firmar.write(datau)
                archivo_a_firmar.seek(0)
                file_name = f"acta_calificaciones_{eMateria.id}_lezalizada_{datetime.now().strftime('%Y%m%d%H%M%S%f')}.pdf"
                file_obj = DjangoFile(archivo_a_firmar, name=f"{remover_caracteres_especiales_unicode(file_name)}.pdf")
                eRepositorio = Repositorio(nombre=f'Acta de calificaciones firmada por {ePersona.nombre_completo()} de la materia (id: {eMateria.id}) {eMateria.nombre_completo()}',
                                           tipo=Repositorio.Tipos.PDF,
                                           archivo=file_obj)
                eRepositorio.save(request)
                eFirmaActaCalificacion.fecha = datetime.now()
                eFirmaActaCalificacion.subido = True
                eFirmaActaCalificacion.archivo = eRepositorio
                eFirmaActaCalificacion.save(request)
                eFirmaActaCalificacion_next = eRepositorioActaCalificacion.siguiente_a_firmar(responsable_actual_id=ePersona.id)
                if eFirmaActaCalificacion_next:
                    eSolicitud = Solicitud(estado=Solicitud.Estados.PENDIENTE,
                                           tipo=Solicitud.Tipos.ACTA_CALIFICACION,
                                           descripcion=f"Solicitud de firma de acta de calificaciones por el docente {ePersona.nombre_completo()} de la materia (id: {eMateria.id}) {eMateria.nombre_completo()}",
                                           responsable=eFirmaActaCalificacion_next.responsable,
                                           content_type=ContentType.objects.get_for_model(eMateria),
                                           object_id=eMateria.id,
                                           archivo=eRepositorio)
                    eSolicitud.save(request)

                return JsonResponse({"isSuccess": True, "message": f"Se firmo el acta correctamente"})
            except Exception as ex:
                transaction.set_rollback(True)
                print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
                forms = f.toArray() if f else {}
                return JsonResponse({"isSuccess": False,
                                     "message": f"Error al procesar los datos. {ex.__str__()}",
                                     "forms": forms})

    @staticmethod
    def render_load_seguimiento_firma(request: HttpRequest) -> JsonResponse:
        from sga.models import Materia
        try:
            id = request.GET.get('id', 0)
            try:
                eMateria = Materia.objects.get(id=id)
            except ObjectDoesNotExist:
                raise NameError(u"Materia no encontrada")
            data = {}
            addUserData(request, data)
            data['eMateria'] = eMateria
            template = get_template("pro_calificaciones/seguimiento_firma/view.html")
            return JsonResponse({"isSuccess": True, "message": f"Se construyo vista correctamente", 'html': template.render(data)})
        except Exception as ex:
            transaction.set_rollback(True)
            print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
            return JsonResponse({"isSuccess": False, "message": f"Error al obtener los datos. {ex.__str__()}"})

