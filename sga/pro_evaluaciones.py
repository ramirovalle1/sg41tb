from datetime import datetime, time, timedelta
import json
import random
from django.contrib.auth.decorators import login_required
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.forms.models import model_to_dict
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render, render
from django.template.context import RequestContext
from django.db.models.query_utils import Q
from django.template.loader import get_template
from django.utils.encoding import force_str
import xlrd
from decorators import secure_module
from settings import NOTA_PARA_APROBAR, ASIST_PARA_APROBAR, ASIST_PARA_SEGUIR, NOTA_ESTADO_APROBADO, NOTA_ESTADO_REPROBADO, NOTA_ESTADO_EN_CURSO, PORCIENTO_NOTA1, PORCIENTO_NOTA4, PORCIENTO_NOTA3, PORCIENTO_NOTA2, PORCIENTO_NOTA5, NOTA_ESTADO_SUPLETORIO, NOTA_PARA_SUPLET, EVALUACION_IAVQ, MODELO_EVALUACION, EVALUACION_ITB, REPORTE_ACTA_NOTAS, EVALUACION_ITS, VALIDAR_ASISTENCIAS, MODULO_FINANZAS_ACTIVO, PAGO_ESTRICTO, DATOS_ESTRICTO, EVALUACION_TES, VALIDA_DEUDA_EVALUACIONES, EVALUACION_IGAD, CENTRO_EXTERNO, EVALUACION_CASADE,PROFE_PRACT_CONDUCCION, EMAIL_ACTIVE, VALIDA_CLAVE_CALIFICACION, TIPOSEGMENTO_PRACT, INSCRIPCION_CONDUCCION, VALIDA_DEUDA_EXAM_ASIST, ID_TIPO_ESPECIE_REG_NOTA, DIAS_ESPECIE, ASIGNATURA_PRACTICA_CONDUCCION, ASIG_VINCULACION, ASIG_PRATICA,\
    MIN_APROBACION,MAX_APROBACION,MIN_RECUPERACION,MAX_RECUPERACION,MIN_EXAMEN,MAX_EXAMEN,MIN_EXAMENRECUPERACION,DEFAULT_PASSWORD, NIVEL_SEMINARIO,MULTA24H,MULTA48H,\
    MATERIA_PRAC_ENFERMERIA, NOTA_ESTADO_DERECHOEXAMEN, MEDIA_ROOT

from sga.commonviews import addUserData, ip_client_address
from sga.forms import NotaIAVQForm, EvaluacionObservacionForm
from sga.models import Profesor, Materia, MateriaAsignada, EvaluacionIAVQ2, NotaIAVQ, Periodo, PeriodoEvaluacionesIAVQ, CodigoEvaluacion, TipoEstado, PeriodoEvaluacionesITS, ProfesorMateria, ClaveEvaluacionNota, Persona, Inscripcion,EvaluacionITB, RubroEspecieValorada, RecordAcademico, HistoricoRecordAcademico,TipoEspecieValorada, Rubro\
    ,MultaDocenteMateria, Coordinacion, Clase, Turno, Aula, Leccion, AsistenciaLeccion, GestionTramite, SubirArchivoNota
from sga.tasks import plaintext2html
from sga.finanzas import generador_especies

from sga.tasks import send_html_mail
from sga.finanzas import convertir_fecha

def mail_correoalumnoespecie(contenido,asunto,user,materiaasignada,emailestudiante,profesor):
        hoy = datetime.now().today()
        persona = Persona.objects.get(usuario=user)
        email=emailestudiante
        materia=materiaasignada
        docente=profesor
        send_html_mail(str(asunto),"emails/correoalumno_especie.html", {'fecha': hoy,"user":user,'contenido': contenido, 'asunto': asunto,'persona':persona,'materia':materia,'docente':docente},email.split(","))

def if_integer(string):
    try:
        int(string)
        return True
    except ValueError:
        return False


@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    hoy =  datetime.now().date()
    if request.method=='POST':
        if 'action' in request.POST:
            action = request.POST['action']
            if action=='editnota':
                materiaasignada = MateriaAsignada.objects.get(pk=request.POST['id'])
                tipo = int(request.POST['tipo'])
                evaluacion = materiaasignada.evaluacion()
                if tipo==1:
                    notaiavq = evaluacion.n1
                else:
                    notaiavq = evaluacion.n2

                f = NotaIAVQForm(request.POST, initial=notaiavq)
                if f.is_valid():
                    notaiavq.p1=f.cleaned_data['p1']
                    notaiavq.p2=f.cleaned_data['p2']
                    notaiavq.p3=f.cleaned_data['p3']
                    notaiavq.p4=f.cleaned_data['p4']
                    notaiavq.p5=f.cleaned_data['p5']
                    notaiavq.save()

                    evaluacion.nota_n3()
                    if DEFAULT_PASSWORD=='itb':
                        materiaasignada.notafinal = evaluacion.nota_final_nueva()
                    else:
                        materiaasignada.notafinal = evaluacion.nota_final()

                    if evaluacion.n1.nota and evaluacion.n2.nota and evaluacion.pi:
                        if materiaasignada.materia.nivel.carrera.online:
                            if evaluacion.nota_final() >= NOTA_PARA_APROBAR :
                                evaluacion.estado_id = NOTA_ESTADO_APROBADO
                            if(NOTA_PARA_SUPLET <= evaluacion.nota_final() < NOTA_PARA_APROBAR) or (evaluacion.pi < NOTA_PARA_APROBAR):
                                evaluacion.estado_id = NOTA_ESTADO_SUPLETORIO
                            if evaluacion.nota_final() < NOTA_PARA_SUPLET :
                                evaluacion.estado_id = NOTA_ESTADO_REPROBADO
                        else:
                            if evaluacion.nota_final()>=NOTA_PARA_APROBAR and materiaasignada.porciento_asistencia()>=ASIST_PARA_APROBAR:
                                evaluacion.estado_id = NOTA_ESTADO_APROBADO
                            if (ASIST_PARA_SEGUIR <= materiaasignada.porciento_asistencia() < ASIST_PARA_APROBAR) or (NOTA_PARA_SUPLET<=evaluacion.nota_final()<NOTA_PARA_APROBAR) or (evaluacion.pi<NOTA_PARA_APROBAR):
                                evaluacion.estado_id = NOTA_ESTADO_SUPLETORIO
                            if evaluacion.nota_final()<NOTA_PARA_SUPLET or materiaasignada.porciento_asistencia()<ASIST_PARA_SEGUIR:
                                evaluacion.estado_id = NOTA_ESTADO_REPROBADO
                    else:
                        evaluacion.estado_id = NOTA_ESTADO_EN_CURSO

                    evaluacion.save()
                    materiaasignada.save()
                    return HttpResponseRedirect("/pro_evaluaciones?materia="+str(materiaasignada.materia_id))
            elif action=='otrasnotas':
                materiaasignada = MateriaAsignada.objects.get(pk=request.POST['id'])
                materiasasignadas = MateriaAsignada.objects.filter(matricula=materiaasignada.matricula).exclude(id=materiaasignada.id)
                tipo_num = int(request.POST['tipo_num'])
                val = float(request.POST['valor'])

                evaluacion = materiaasignada.evaluacion()

                if tipo_num == 3:
                    evaluacion.pi = val
                    evaluacion.nota_n3()
                    materiaasignada.notafinal= evaluacion.nota_final()

                    #Este codigo actualiza el ESTADO de la asignatura rectora
                    if evaluacion.n1.nota and evaluacion.n2.nota and evaluacion.pi:
                        if materiaasignada.materia.nivel.carrera.online:
                            if evaluacion.nota_final() >= NOTA_PARA_APROBAR :
                                evaluacion.estado_id = NOTA_ESTADO_APROBADO
                            if (evaluacion.nota_final() >= NOTA_PARA_APROBAR ) or (
                                        evaluacion.nota_final() < NOTA_PARA_SUPLET ):
                                evaluacion.estado_id = NOTA_ESTADO_REPROBADO
                            if (NOTA_PARA_SUPLET <= evaluacion.nota_final() < NOTA_PARA_APROBAR) or (
                                    evaluacion.pi < NOTA_PARA_APROBAR):
                                evaluacion.estado_id = NOTA_ESTADO_SUPLETORIO
                        else:
                            if evaluacion.nota_final()>=NOTA_PARA_APROBAR and materiaasignada.porciento_asistencia()>=ASIST_PARA_APROBAR:
                                evaluacion.estado_id = NOTA_ESTADO_APROBADO
                            if (evaluacion.nota_final()>=NOTA_PARA_APROBAR and materiaasignada.porciento_asistencia()<ASIST_PARA_SEGUIR) or (evaluacion.nota_final()<NOTA_PARA_SUPLET and materiaasignada.porciento_asistencia()>=ASIST_PARA_APROBAR):
                                evaluacion.estado_id = NOTA_ESTADO_REPROBADO
                            if (ASIST_PARA_SEGUIR <= materiaasignada.porciento_asistencia() < ASIST_PARA_APROBAR) or (NOTA_PARA_SUPLET<=evaluacion.nota_final()<NOTA_PARA_APROBAR) or (evaluacion.pi<NOTA_PARA_APROBAR):
                                evaluacion.estado_id = NOTA_ESTADO_SUPLETORIO
                    else:
                        evaluacion.estado_id = NOTA_ESTADO_EN_CURSO

                    evaluacion.save()
                    materiaasignada.save()

                    #Este codigo sirve para escribir la misma nota del P.I a todas las materias del nivel de ese alumno y actualizarle ESTADO a c/u, no tener en cuenta la validacion del PI, pq solo es en la rectora
                    for materiaasignada2 in materiasasignadas:
                        evaluac = materiaasignada2.evaluacion()
                        evaluac.pi = val

                        evaluac.nota_n3()
                        materiaasignada2.notafinal = evaluac.nota_final()

                        if evaluac.n1.nota and evaluac.n2.nota and evaluac.pi:
                            if evaluac.nota_final()>=NOTA_PARA_APROBAR and materiaasignada2.porciento_asistencia()>=ASIST_PARA_APROBAR:
                                evaluac.estado_id = NOTA_ESTADO_APROBADO
                            if (ASIST_PARA_SEGUIR <= materiaasignada2.porciento_asistencia() < ASIST_PARA_APROBAR) or (NOTA_PARA_SUPLET<=evaluac.nota_final()<NOTA_PARA_APROBAR) :
                                evaluac.estado_id = NOTA_ESTADO_SUPLETORIO
                            if evaluac.nota_final()<NOTA_PARA_SUPLET or materiaasignada.porciento_asistencia()<ASIST_PARA_SEGUIR:
                                evaluac.estado_id = NOTA_ESTADO_REPROBADO
                        else:
                            evaluac.estado_id = NOTA_ESTADO_EN_CURSO

                        evaluac.save()
                        materiaasignada2.save()

                elif tipo_num == 4:
                    materiaasignada.supletorio = evaluacion.su = val
                    materiaasignada.notafinal= evaluacion.nota_final()

                    if evaluacion.n1.nota and evaluacion.n2.nota and evaluacion.su:
                        if evaluacion.nota_final()>=NOTA_PARA_APROBAR:
                            evaluacion.estado_id = NOTA_ESTADO_APROBADO
                        else:
                            evaluacion.estado_id = NOTA_ESTADO_REPROBADO

                    if not evaluacion.su:
                        if evaluacion.n1.nota and evaluacion.n2.nota and evaluacion.pi:
                            if materiaasignada.materia.nivel.carrera.online:
                                if evaluacion.nota_final() >= NOTA_PARA_APROBAR:
                                    evaluacion.estado_id = NOTA_ESTADO_APROBADO
                                if (NOTA_PARA_SUPLET <= evaluacion.nota_final() < NOTA_PARA_APROBAR) or (
                                        evaluacion.pi < NOTA_PARA_APROBAR):
                                    evaluacion.estado_id = NOTA_ESTADO_SUPLETORIO
                                if evaluacion.nota_final() < NOTA_PARA_SUPLET :
                                    evaluacion.estado_id = NOTA_ESTADO_REPROBADO
                            else:

                                if evaluacion.nota_final()>=NOTA_PARA_APROBAR and materiaasignada.porciento_asistencia()>=ASIST_PARA_APROBAR:
                                    evaluacion.estado_id = NOTA_ESTADO_APROBADO
                                if (ASIST_PARA_SEGUIR <= materiaasignada.porciento_asistencia() < ASIST_PARA_APROBAR) or (NOTA_PARA_SUPLET<=evaluacion.nota_final()<NOTA_PARA_APROBAR) or (evaluacion.pi<NOTA_PARA_APROBAR):
                                    evaluacion.estado_id = NOTA_ESTADO_SUPLETORIO
                                if evaluacion.nota_final()<NOTA_PARA_SUPLET or materiaasignada.porciento_asistencia()<ASIST_PARA_SEGUIR:
                                    evaluacion.estado_id = NOTA_ESTADO_REPROBADO
                        else:
                            evaluacion.estado_id = NOTA_ESTADO_EN_CURSO

                    evaluacion.save()
                    materiaasignada.save()

                return HttpResponseRedirect("/pro_evaluaciones?materia="+str(materiaasignada.materia_id))
            elif action=='alcance':
                ma = MateriaAsignada.objects.get(pk=request.POST['maid'])
                periodo = request.session['periodo']
                ma.alcance = True
                ma.save()
                if EMAIL_ACTIVE:
                    profesor =  Profesor.objects.filter(persona__usuario=request.user)[:1].get()
                    ma.correo_alcance(profesor)

                return HttpResponse(json.dumps({"result":"ok", 'cerrado': not ma.cerrado,'tienedeuda': ma.matricula.inscripcion.tiene_deuda_evaluacion(), 'tienemateriaasignadaabierta': ma.materia.cerrar_disponible(periodo), 'acta_entregada':ma.materia.acta_entregada()}),content_type="application/json")

            elif action=='cerrarmateriaasignada':
                ma = MateriaAsignada.objects.get(pk=request.POST['maid'])
                e = ma.evaluacion()
                cerrado = request.POST['cerrado']=='true'
                if cerrado:
                    # Abrir
                    ma.cerrado = False
                else:
                    ma.cerrado = True

                ma.fechacierre = datetime.now()
                ma.save()
                periodo = request.session['periodo']
                if not ma.absentismo and ma.cerrado:
                    if Profesor.objects.filter(persona__usuario=request.user).exists():
                        reprobado=''
                        observacion=''

                        if ma.asistenciafinal < ASIST_PARA_APROBAR and not ma.materia.nivel.carrera.online:
                            reprobado='REPROBADO POR ASISTENCIA'
                            observacion = "Acercarse a justificar la asistencia"
                        if ma.notafinal < NOTA_PARA_APROBAR:
                            reprobado='REPROBADO'
                            observacion = ""
                        profesor = Profesor.objects.filter(persona__usuario=request.user)[:1].get()
                        if ProfesorMateria.objects.filter(materia=ma.materia,profesor_aux=profesor.id).exists():
                            profesormateria = ProfesorMateria.objects.filter(materia=ma.materia,profesor_aux=profesor.id)[:1].get()
                        else:
                            profesormateria = ProfesorMateria.objects.filter(materia=ma.materia,profesor=profesor)[:1].get()
                        if EMAIL_ACTIVE and not CENTRO_EXTERNO:
                            ma.correo_alumnocierremate(profesormateria,reprobado,observacion)
                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de CERRAR MATERIA ASIGNADA
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(ma).pk,
                    object_id       = ma.id,
                    object_repr     = force_str(ma),
                    action_flag     = CHANGE,
                    change_message  = 'Cerrada la Materia Asignada (' + client_address + ')' )

                # return HttpResponse(json.dumps({"result":"ok", 'cerrado': not cerrado,'tienedeuda': ma.matricula.inscripcion.tiene_deuda(), 'tienemateriaasignadaabierta': MateriaAsignada.objects.filter(materia=ma.materia, cerrado=False).exists()}),content_type="application/json")
                return HttpResponse(json.dumps({"result":"ok", 'cerrado': not cerrado,'tienedeuda': ma.matricula.inscripcion.tiene_deuda_evaluacion(), 'tienemateriaasignadaabierta': ma.materia.cerrar_disponible(periodo), 'acta_entregada':ma.materia.acta_entregada()}),content_type="application/json")

            elif action=='actualiza':
                result={}
                c=0
                try:
                    for m in  MateriaAsignada.objects.filter(materia__id=request.POST['mid']):
                        if m.materia.cerrado:
                            result['result'] = "cerrada"
                            return HttpResponse(json.dumps(result),content_type="application/json")
                        if  EvaluacionITB.objects.filter(materiaasignada=m).exists():
                            e = EvaluacionITB.objects.filter(materiaasignada=m)[:1].get()
                            if not DEFAULT_PASSWORD == 'itb':
                                e.actualiza_estado()
                            else:
                            #aqui nuevo estado OCastillo 22-07-2019
                                e.actualiza_estado_nueva()

                    result['result'] = "ok"

                    return HttpResponse(json.dumps(result),content_type="application/json")
                except:
                    result['result'] = "bad"
                    return HttpResponse(json.dumps(result),content_type="application/json")

            elif action=='cerrarmateria':
                materia = Materia.objects.get(pk=request.POST['mid'])
                materia.cerrado = True
                materia.fechacierre = datetime.now()
                materia.save()
                #OCastillo 20-08-2020 agregar 7 dias como tope de fecha de alcance
                materia.fechaalcance =materia.fechacierre + timedelta(days=14)
                materia.save()
                if Profesor.objects.filter(persona__usuario=request.user).exists():
                    profesor = Profesor.objects.filter(persona__usuario=request.user)[:1].get()
                    nivel=MateriaAsignada.objects.filter(materia=materia)[:1].get().matricula.nivel
                    inscrip=Inscripcion.objects.filter(id__in=MateriaAsignada.objects.filter(materia=materia).values("matricula__inscripcion")).exclude(retiradomatricula__activo=False,retiradomatricula__nivel=nivel).values('id')
                    if ProfesorMateria.objects.filter(materia=materia,profesor_aux=profesor.id).exists():
                        profesormateria = ProfesorMateria.objects.filter(materia=materia,profesor_aux=profesor.id)[:1].get()
                    else:
                        profesormateria = ProfesorMateria.objects.filter(materia=materia,profesor=profesor)[:1].get()
                    if profesormateria.segmento_id == TIPOSEGMENTO_PRACT:
                        promedioreprobado = int(round(round(MateriaAsignada.objects.filter(Q(matricula__inscripcion__id__in=inscrip,materia=materia,notafinal__lt=NOTA_PARA_APROBAR),Q(absentismo=None)|Q(absentismo=False)).count()*100)/round(MateriaAsignada.objects.filter(Q(matricula__inscripcion__id__in=inscrip,materia=materia),Q(absentismo=None)|Q(absentismo=False)).count())))
                        promedioaprobado = int(round(round(MateriaAsignada.objects.filter(Q(matricula__inscripcion__id__in=inscrip,materia=materia,notafinal__gte=NOTA_PARA_APROBAR),Q(absentismo=None)|Q(absentismo=False)).count()*100)/round(MateriaAsignada.objects.filter(Q(matricula__inscripcion__id__in=inscrip,materia=materia),Q(absentismo=None)|Q(absentismo=False)).count())))
                        # totalreprobado = MateriaAsignada.objects.filter(Q(matricula__inscripcion__id__in=inscrip,materia=materia,notafinal__lt=NOTA_PARA_APROBAR),Q(absentismo=None)|Q(absentismo=False)).count()
                        # OCU 27-oct-2017 no estaba considerando asistencia en reprobados
                        if profesormateria.materia.nivel.carrera.online:
                            totalreprobado = MateriaAsignada.objects.filter(Q(matricula__inscripcion__id__in=inscrip, materia=materia,notafinal__lt=NOTA_PARA_APROBAR),
                                Q(absentismo=None) | Q(absentismo=False)).count()
                            totalaprobado = MateriaAsignada.objects.filter(
                                Q(matricula__inscripcion__id__in=inscrip, materia=materia,
                                  notafinal__gte=NOTA_PARA_APROBAR), Q(absentismo=None) | Q(absentismo=False)).count()
                            resumreprobadoasist = 0
                            resumreprobadonota = MateriaAsignada.objects.filter(
                                Q(matricula__inscripcion__id__in=inscrip, materia=materia),
                                Q(notafinal__lt=NOTA_PARA_APROBAR), Q(absentismo=None) | Q(absentismo=False)).count()
                        else:
                            totalreprobado = MateriaAsignada.objects.filter(Q(matricula__inscripcion__id__in=inscrip,materia=materia,notafinal__lt=NOTA_PARA_APROBAR,asistenciafinal__lt=ASIST_PARA_APROBAR),Q(absentismo=None)|Q(absentismo=False)).count()
                            totalaprobado = MateriaAsignada.objects.filter(Q(matricula__inscripcion__id__in=inscrip,materia=materia,notafinal__gte=NOTA_PARA_APROBAR),Q(absentismo=None)|Q(absentismo=False)).count()
                            resumreprobadoasist = 0
                            resumreprobadonota = MateriaAsignada.objects.filter(Q(matricula__inscripcion__id__in=inscrip,materia=materia),Q(notafinal__lt=NOTA_PARA_APROBAR),Q(absentismo=None)|Q(absentismo=False)).count()
                    else:
                        # OCU 28-abril-2017 formulas anteriores
                        # promedioreprobado = int(round(round(MateriaAsignada.objects.filter(Q(matricula__inscripcion__id__in=inscrip,materia=materia),Q(notafinal__lt=NOTA_PARA_APROBAR)|Q(asistenciafinal__lt=ASIST_PARA_APROBAR),Q(absentismo=None)|Q(absentismo=False)).count()*100)/round(MateriaAsignada.objects.filter(Q(matricula__inscripcion__id__in=inscrip,materia=materia),Q(absentismo=None)|Q(absentismo=False)).count())))
                        # promedioaprobado = int(round(round(MateriaAsignada.objects.filter(Q(matricula__inscripcion__id__in=inscrip,materia=materia,notafinal__gte=NOTA_PARA_APROBAR,asistenciafinal__gte=ASIST_PARA_APROBAR),Q(absentismo=None)|Q(absentismo=False)).count()*100)/round(MateriaAsignada.objects.filter(Q(matricula__inscripcion__id__in=inscrip,materia=materia),Q(absentismo=None)|Q(absentismo=False)).count())))
                        # totalreprobado = MateriaAsignada.objects.filter(Q(matricula__inscripcion__id__in=inscrip,materia=materia),Q(notafinal__lt=NOTA_PARA_APROBAR)|Q(asistenciafinal__lt=ASIST_PARA_APROBAR),Q(absentismo=None)|Q(absentismo=False)).count()
                        # resumreprobadoasist = MateriaAsignada.objects.filter(Q(matricula__inscripcion__id__in=inscrip,materia=materia),Q(asistenciafinal__lt=ASIST_PARA_APROBAR),Q(absentismo=None)|Q(absentismo=False)).exclude(notafinal__lt=NOTA_PARA_APROBAR).count()
                        # resumreprobadonota = MateriaAsignada.objects.filter(Q(matricula__inscripcion__id__in=inscrip,materia=materia),Q(notafinal__lt=NOTA_PARA_APROBAR),Q(absentismo=None)|Q(absentismo=False)).exclude(asistenciafinal__lt=ASIST_PARA_APROBAR).count()
                        # resumreprobadoasistnota = MateriaAsignada.objects.filter(Q(matricula__inscripcion__id__in=inscrip,materia=materia),Q(asistenciafinal__lt=ASIST_PARA_APROBAR),Q(notafinal__lt=NOTA_PARA_APROBAR),Q(absentismo=None)|Q(absentismo=False)).count()
                        # totalaprobado = (MateriaAsignada.objects.filter(Q(matricula__inscripcion__id__in=inscrip,materia=materia,notafinal__gte=NOTA_PARA_APROBAR,asistenciafinal__gte=ASIST_PARA_APROBAR),Q(absentismo=None)|Q(absentismo=False)).count())

                        materiaasignada=MateriaAsignada.objects.filter(Q(materia=materia),Q(absentismo=None)|Q(absentismo=False)).values('id')
                        totalaprobado= (EvaluacionITB.objects.filter(Q(materiaasignada__id__in=materiaasignada,materiaasignada__matricula__inscripcion__id__in=inscrip,estado=NOTA_ESTADO_APROBADO),Q(materiaasignada__absentismo=None)|Q(materiaasignada__absentismo=False)).count())
                        # OCU 27-abril-2017 para obtener alumnos en Curso y Recuperacion
                        totencurso= EvaluacionITB.objects.filter(materiaasignada__id__in=materiaasignada,materiaasignada__matricula__inscripcion__id__in=inscrip,estado=NOTA_ESTADO_EN_CURSO).count()
                        totrecuperacion= EvaluacionITB.objects.filter(materiaasignada__id__in=materiaasignada,materiaasignada__matricula__inscripcion__id__in=inscrip,estado=NOTA_ESTADO_SUPLETORIO).count()
                        totalreprobado= EvaluacionITB.objects.filter(materiaasignada__id__in=materiaasignada,materiaasignada__matricula__inscripcion__id__in=inscrip,estado=NOTA_ESTADO_REPROBADO).count()
                        totalexamen= EvaluacionITB.objects.filter(materiaasignada__id__in=materiaasignada,materiaasignada__matricula__inscripcion__id__in=inscrip,estado=NOTA_ESTADO_DERECHOEXAMEN).count()

                    #OCastillo 24-octubre-2019 esta parte se quita por el nuevo proceso de Notas de Alcance
                    #OCastillo 04-06-2019 para pasar nota de materia asignada al record al cierre de la materia
                    # for asignado in MateriaAsignada.objects.filter(materia=materia).order_by('matricula__inscripcion__persona__apellido1','matricula__inscripcion__persona__apellido2'):
                    #     if materia.nivel!= asignado.matricula.nivel:
                    #         if asignado.materia.asignatura.asistencia and asignado.notafinal >= NOTA_PARA_APROBAR:
                    #             asistencia = 100
                    #         else:
                    #             asistencia = asignado.asistenciafinal
                    #
                    #             # Record
                    #             b = 1
                    #             if not asignado.materia.asignatura.sin_malla:
                    #                 if (asignado.materia.asignatura.id == ASIGNATURA_PRACTICA_CONDUCCION and INSCRIPCION_CONDUCCION):
                    #                      b=0
                    #                 if ((asignado.materia.asignatura.id == ASIG_VINCULACION  or asignado.materia.asignatura.id == ASIG_PRATICA)and not INSCRIPCION_CONDUCCION) :
                    #                     b = 0
                    #             if b == 1:
                    #                 if RecordAcademico.objects.filter(inscripcion=asignado.matricula.inscripcion,asignatura=asignado.materia.asignatura,fecha=asignado.matricula.nivel.fin).exists():
                    #                     r = RecordAcademico.objects.filter(inscripcion=asignado.matricula.inscripcion,asignatura=asignado.materia.asignatura,fecha=asignado.matricula.nivel.fin)[:1].get()
                    #                     r.nota = asignado.notafinal
                    #                     r.asistencia = asistencia
                    #                     r.fecha = asignado.matricula.nivel.fin
                    #                     r.convalidacion = False
                    #                     r.aprobada = asignado.esta_aprobado_final()
                    #                     r.pendiente = False
                    #                     r.save()
                    #                 else:
                    #                     r = RecordAcademico(inscripcion=asignado.matricula.inscripcion, asignatura=asignado.materia.asignatura,
                    #                                         nota=asignado.notafinal, asistencia=asistencia,
                    #                                         fecha=asignado.matricula.nivel.fin, convalidacion=False,
                    #                                         aprobada=asignado.esta_aprobado_final(), pendiente=False)
                    #                     r.save()
                    #                 # Historico
                    #                 if HistoricoRecordAcademico.objects.filter(inscripcion=asignado.matricula.inscripcion,asignatura=asignado.materia.asignatura,fecha=asignado.matricula.nivel.fin).exists():
                    #                     h = HistoricoRecordAcademico.objects.filter(inscripcion=asignado.matricula.inscripcion,asignatura=asignado.materia.asignatura,fecha=asignado.matricula.nivel.fin)[:1].get()
                    #                     h.nota = asignado.notafinal
                    #                     h.asistencia = asistencia
                    #                     h.fecha = asignado.matricula.nivel.fin
                    #                     h.convalidacion = False
                    #                     h.aprobada = asignado.esta_aprobado_final()
                    #                     h.pendiente = False
                    #                     h.save()
                    #                 else:
                    #                     h = HistoricoRecordAcademico(inscripcion=asignado.matricula.inscripcion, asignatura=asignado.materia.asignatura,
                    #                                                 nota=asignado.notafinal, asistencia=asistencia,
                    #                                                 fecha=asignado.matricula.nivel.fin, convalidacion=False,
                    #                                                 aprobada=asignado.esta_aprobado_final(), pendiente=False)
                    #                     h.save()
                    #
                    #                 #Obtain client ip address
                    #                 client_address = ip_client_address(request)
                    #
                    #                 # Log de ADICIONAR RECORD
                    #                 LogEntry.objects.log_action(
                    #                     user_id         = request.user.pk,
                    #                     content_type_id = ContentType.objects.get_for_model(r).pk,
                    #                     object_id       = r.id,
                    #                     object_repr     = force_str(r),
                    #                     action_flag     = ADDITION,
                    #                     change_message  = 'Adicionado Historico Record desde Cierre Materia (' + client_address + ')' )

                    totalalumnos = MateriaAsignada.objects.filter(matricula__inscripcion__id__in=inscrip,materia=materia).count()
                    # totalalumnosinabs = MateriaAsignada.objects.filter(Q(matricula__inscripcion__id__in=inscrip,materia=materia),Q(absentismo=None)|Q(absentismo=False)).count()
                    totalalumnoabs = MateriaAsignada.objects.filter(matricula__inscripcion__id__in=inscrip,materia=materia,absentismo=True).count()
                    totalbecados = MateriaAsignada.objects.filter(Q(matricula__inscripcion__id__in=inscrip,materia=materia,matricula__becado=True),Q(absentismo=None)|Q(absentismo=False)).count()

                    # OCU 13-NOV-2017 al total de estudiantes no se debe restar los reprobados porque altera los porcentajes finales
                    # totestudiantes=totalalumnos-totencurso-totalalumnoabs-totalreprobado
                    totestudiantes=totalalumnos-totencurso-totalalumnoabs

                    promedioaprobado = int(round((round(totalaprobado*100)/totestudiantes)))
                    promedioreprobado = int(round((round(totalreprobado*100)/totestudiantes)))
                    promediorecuperacion = int(round((round(totrecuperacion*100)/totestudiantes)))
                    promedioexamen = int(round((round(totalexamen*100)/totestudiantes)))

                    # if promediototal >= 40:
                    if EMAIL_ACTIVE and not CENTRO_EXTERNO:
                        # materia. correo_promedio(totalalumnos,totalalumnoabs,totalalumnosinabs,totalaprobado,promedioaprobado,totalreprobado,promedioreprobado,resumreprobadonota,resumreprobadoasist,profesormateria,totalbecados,resumreprobadoasistnota)
                        # OCU 27-abril-2017 nuevo email
                        materia.correo_promedio(totalalumnos,totalalumnoabs,totalaprobado,promedioaprobado,promedioreprobado,profesormateria,totalbecados,totalreprobado,totencurso,totrecuperacion,totestudiantes,promediorecuperacion,totalexamen,promedioexamen)
                # Log cerrarmateriade CERRAR MATERIA
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(materia).pk,
                    object_id       = materia.id,
                    object_repr     = force_str(materia),
                    action_flag     = DELETION,
                    change_message  = 'Cerrada la Materia' )

                return HttpResponse(json.dumps({"result": "ok"}),content_type="application/json")

            elif action=='abrirmateria':
                materia = Materia.objects.get(pk=request.POST['mid'])
                materia.cerrado = False
                materia.fechacierre = datetime.now()
                materia.save()

                # Log de ABRIR MATERIA
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(materia).pk,
                    object_id       = materia.id,
                    object_repr     = force_str(materia),
                    action_flag     = ADDITION,
                    change_message  = 'Abierta la Materia' )

                return HttpResponse(json.dumps({"result": "ok"}),content_type="application/json")

            elif action=='codigo':
                try:
                    materia = Materia.objects.get(pk=request.POST['materia'])
                    codigo = CodigoEvaluacion.objects.get(pk=request.POST['cod'])
                    sel = request.POST['sel']
                    materiasasignadas = MateriaAsignada.objects.filter(materia=materia)
                    for x in materiasasignadas:
                        evaluacion = x.evaluacion()
                        if sel=='1': evaluacion.cod1 = codigo
                        if sel=='2': evaluacion.cod2 = codigo
                        if sel=='3': evaluacion.cod3 = codigo
                        if sel=='4': evaluacion.cod4 = codigo
                        evaluacion.save()
                    return HttpResponse(json.dumps({"result": "ok", "codigo": str(codigo.id)+" - "+codigo.alias}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad", "error": str(ex)}),content_type="application/json")

            elif action=='nota':
                try:
                    materiaasignada = MateriaAsignada.objects.get(pk=request.POST['maid'])
                    sel = request.POST['sel']
                    puedeingresar =False
                    # if not VALIDA_DEUDA_EXAM_ASIST and RubroEspecieValorada.objects.filter(materia=materiaasignada, autorizado=True,disponible=True, tipoespecie__id=ID_TIPO_ESPECIE_REG_NOTA,aplicada = False,rubro__cancelado=True).exists() and materiaasignada.matricula.inscripcion.tiene_deuda():
                    #     if RubroEspecieValorada.objects.filter(materia=materiaasignada, disponible=True, tipoespecie__id=ID_TIPO_ESPECIE_REG_NOTA,aplicada = False,rubro__cancelado=True,rubro__fecha__lte='2020-09-18').values('id'):
                    #         puedeingresar=True
                    #     else:
                    #         especies=  RubroEspecieValorada.objects.filter(materia=materiaasignada, disponible=True, tipoespecie__id=ID_TIPO_ESPECIE_REG_NOTA,aplicada = False,rubro__cancelado=True).exclude(rubro__fecha__lte='2020-09-18').values('id')
                    #         if GestionTramite.objects.filter(tramite__id__i=especies,finalizado=False):
                    #             puedeingresar =True
                    # if puedeingresar:
                    #     fechamax = datetime.now() - timedelta(days=DIAS_ESPECIE)
                    #     if RubroEspecieValorada.objects.filter(materia=materiaasignada, disponible=True, autorizado=True,tipoespecie__id=ID_TIPO_ESPECIE_REG_NOTA,aplicada = False,rubro__fecha__gte=fechamax,rubro__cancelado=True).exists():
                    #         t = RubroEspecieValorada.objects.filter(materia=materiaasignada, disponible=True, autorizado=True,tipoespecie__id=ID_TIPO_ESPECIE_REG_NOTA,aplicada = False,rubro__fecha__gte=fechamax,rubro__cancelado=True)[:1].get()
                    #         persona = Persona.objects.filter(usuario=request.user)[:1].get()
                    #         if Profesor.objects.filter(persona=persona).exists():
                    #             profesor = Profesor.objects.filter(persona=persona)[:1].get()
                    #             t.profesor = profesor
                    #         t.f_registro = datetime.now()
                    #         t.save()
                    #         # Log de ABRIR MATERIA
                    #         LogEntry.objects.log_action(
                    #             user_id         = request.user.pk,
                    #             content_type_id = ContentType.objects.get_for_model(t).pk,
                    #             object_id       = t.id,
                    #             object_repr     = force_str(t),
                    #             action_flag     = ADDITION,
                    #             change_message  = 'Aplica especie reg nota' )

                        # for re in  RubroEspecieValorada.objects.filter(materia=materiaasignada, disponible=True, tipoespecie__id=ID_TIPO_ESPECIE_REG_NOTA,aplicada = False,rubro__fecha__gt=fechamax,rubro__cancelado=True):
                        #     # re.aplicada = True
                        #     re.disponible = False
                        #     re.save()

                    codigo = None
                    if not MODELO_EVALUACION==EVALUACION_TES and not MODELO_EVALUACION==EVALUACION_CASADE:
                        codigo = CodigoEvaluacion.objects.get(pk=request.POST['cod'])

                    if MODELO_EVALUACION==EVALUACION_ITS:
                        valor = float(request.POST['val'])
                    else:
                        valor = int(request.POST['val'])

                    evaluacion = materiaasignada.evaluacion()
                    datos = {"result": "ok"}

                    if sel=='n1':
                        evaluacion.n1 = valor
                        if not MODELO_EVALUACION==EVALUACION_TES and not MODELO_EVALUACION==EVALUACION_CASADE:
                            evaluacion.cod1 = codigo
                        evaluacion.save()
                        datos['valor'] = evaluacion.n1
                    if sel=='n2':
                        evaluacion.n2 = valor
                        if not MODELO_EVALUACION==EVALUACION_TES and not MODELO_EVALUACION==EVALUACION_CASADE:
                            evaluacion.cod2 = codigo
                        evaluacion.save()
                        datos['valor'] = evaluacion.n2
                    if sel=='n3':
                        evaluacion.n3 = valor
                        if not MODELO_EVALUACION==EVALUACION_TES and not MODELO_EVALUACION==EVALUACION_CASADE:
                            evaluacion.cod3 = codigo
                        evaluacion.save()
                        datos['valor'] = evaluacion.n3
                    if sel=='n4':
                        evaluacion.n4 = valor
                        if not MODELO_EVALUACION==EVALUACION_TES and not MODELO_EVALUACION==EVALUACION_CASADE:
                            evaluacion.cod4 = codigo
                        evaluacion.save()
                        datos['valor'] = evaluacion.n4
                    if sel=='examen':
                        evaluacion.examen = valor
                        evaluacion.save()
                        datos['valor'] = evaluacion.examen
                    if sel=='recuperacion':
                        evaluacion.recuperacion = valor
                        evaluacion.save()
                        datos['valor'] = evaluacion.recuperacion

                    if sel=='tc1':
                        evaluacion.tc1 = valor
                        evaluacion.save()
                        datos['valor'] = evaluacion.tc1
                    if sel=='te1':
                        evaluacion.te1 = valor
                        evaluacion.save()
                        datos['valor'] = evaluacion.te1
                    if sel=='p1':
                        evaluacion.p1 = valor
                        evaluacion.save()
                        datos['valor'] = evaluacion.p1
                    if sel=='tc2':
                        evaluacion.tc2 = valor
                        evaluacion.save()
                        datos['valor'] = evaluacion.tc2
                    if sel=='te2':
                        evaluacion.te2 = valor
                        evaluacion.save()
                        datos['valor'] = evaluacion.te2
                    if sel=='p2':
                        evaluacion.p2 = valor
                        evaluacion.save()
                        datos['valor'] = evaluacion.p2
                    if sel=='pfinal':
                        evaluacion.pfinal = valor
                        evaluacion.save()
                        datos['valor'] = evaluacion.pfinal
                    if sel=='proy':
                        evaluacion.proy = valor
                        evaluacion.save()
                        datos['valor'] = evaluacion.proy
                    if sel=='su':
                        evaluacion.su = valor
                        evaluacion.save()
                        datos['valor'] = evaluacion.su

                    #Validacion y Actualizacion de notas y Estado del Alumno
                    #OCastillo 22-07-2019
                    if DEFAULT_PASSWORD == 'itb':
                        evaluacion.actualiza_estado_nueva()
                    else:
                        evaluacion.actualiza_estado()

                    materiaasignada = MateriaAsignada.objects.get(pk=request.POST['maid'])
                    evaluacion = materiaasignada.evaluacion()

                    datos['nota_final'] = materiaasignada.notafinal
                    datos['deuda'] = materiaasignada.matricula.inscripcion.tiene_deuda_temp()
                    # if MODELO_EVALUACION==EVALUACION_TES or MODELO_EVALUACION==EVALUACION_CASADE:
                    #     datos['nota_parcial'] = evaluacion.nota_parcial()
                    if EVALUACION_ITB and EVALUACION_ITS and not INSCRIPCION_CONDUCCION :
                        datos['nota_parcial'] = evaluacion.nota_parcial()
                        datos['examen']=evaluacion.examen
                        datos['recuperacion']=evaluacion.recuperacion
                        datos['asistencia']=materiaasignada.asistenciafinal

                    if materiaasignada.materia.nivel.carrera.online:
                        datos['valida_asistencia'] = False
                    else:
                        datos['valida_asistencia'] = VALIDAR_ASISTENCIAS
                    datos['estado'] = evaluacion.estado.nombre
                    datos['estadoid'] = evaluacion.estado.id
                    datos['recuperacion'] = evaluacion.recuperacion
                    datos['asistenciafinal'] = materiaasignada.asistenciafinal
                    datos['nota_para_aprobar'] = NOTA_PARA_APROBAR
                    if materiaasignada.materia.nivel.carrera.online:
                        datos['asistencia_para_aprobar'] = 0
                    else:
                        datos['asistencia_para_aprobar'] = ASIST_PARA_APROBAR
                    datos['asistencia_practica'] = not materiaasignada.materia.asignatura.asistencia
                    datos['min_exa']=MIN_EXAMEN

                    if MODELO_EVALUACION==EVALUACION_ITS:
                        datos['momento1'] = evaluacion.momento1
                        datos['momento2'] = evaluacion.momento2
                    # if materiaasignada.materia.nueva_acta_buck():
                    #     datos['nueva_acta_buck'] = 1
                        # datos['estado_nuevo'] = materiaasignada.nuevo_estado()


                    return HttpResponse(json.dumps(datos),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result": "bad", "error": str(ex)}),content_type="application/json")

            elif action=='actualizarestado':
                try:
                    materia = Materia.objects.get(pk=request.POST['mid'])
                    for asignado in materia.asignados_a_esta_materia():
                        evaluacion = asignado.evaluacion()
                        evaluacion.actualiza_estado()
                        evaluacion.save()
                    return HttpResponse(json.dumps({'result': 'ok'}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({'result': 'bad'}),content_type="application/json")

            elif action=='habilita24':
                try:
                    finasignacion=False
                    tmulta=MULTA24H
                    docente=''
                    materia = Materia.objects.get(pk=request.POST['h24'])
                    if not materia.cerrado:
                        if materia.verificacioncierremateria():
                            desde=datetime.now()
                            hasta=desde + timedelta(days=1)
                            persona = Persona.objects.filter(usuario=request.user)[:1].get()
                            if Profesor.objects.filter(persona=persona).exists():
                                docente = Profesor.objects.filter(persona=persona)[:1].get()

                            if materia.multaactiva():
                                if MultaDocenteMateria.objects.filter(materia=materia,profesor=docente,tipomulta=tmulta,activo=True).exists():
                                    return HttpResponse(json.dumps({'result': 'bad'}),content_type="application/json")
                            else:
                                multa24= MultaDocenteMateria(materia=materia,
                                         profesor=docente,
                                         tipomulta_id=tmulta,
                                         fechadesde=desde,
                                         fechahasta=hasta,
                                         usuario=request.user,
                                         activo=True)
                                multa24.save()

                                carrera=  materia.nivel.carrera
                                if Coordinacion.objects.filter(carrera=carrera).exists():
                                    coord = Coordinacion.objects.filter(carrera=carrera)[:1].get()
                                    email=str(coord.correo)+','+str(docente.persona.emailinst)
                                    materia.correo_multasnotas(docente,email,MULTA24H)

                                #Obtain client ip address
                                client_address = ip_client_address(request)
                                # Log de Adicionar Multa de 24H
                                LogEntry.objects.log_action(
                                    user_id         = request.user.pk,
                                    content_type_id = ContentType.objects.get_for_model(multa24).pk,
                                    object_id       = multa24.id,
                                    object_repr     = force_str(multa24),
                                    action_flag     = ADDITION,
                                    change_message  = 'Se genero multa de 24H ' + client_address + ')' )
                                return HttpResponse(json.dumps({'result': 'ok'}),content_type="application/json")
                            # else:
                            #     return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")
                        else:
                            #OCastillo 13-07-2021 para materias segmento teoria
                            if materia.profesorfinasignacionteoria():
                                desde=datetime.now()
                                hasta=desde + timedelta(days=1)
                                persona = Persona.objects.filter(usuario=request.user)[:1].get()
                                if Profesor.objects.filter(persona=persona).exists():
                                    docente = Profesor.objects.filter(persona=persona)[:1].get()
                                    if materia.multaactiva():
                                        if MultaDocenteMateria.objects.filter(materia=materia,profesor=docente,tipomulta=tmulta,activo=True).exists():
                                            return HttpResponse(json.dumps({'result': 'bad'}),content_type="application/json")
                                        else:
                                            multa24= MultaDocenteMateria(materia=materia,
                                                     profesor=docente,
                                                     tipomulta_id=tmulta,
                                                     fechadesde=desde,
                                                     fechahasta=hasta,
                                                     usuario=request.user,
                                                     activo=True)
                                            multa24.save()

                                            carrera=  materia.nivel.carrera
                                            if Coordinacion.objects.filter(carrera=carrera).exists():
                                                coord = Coordinacion.objects.filter(carrera=carrera)[:1].get()
                                                email=str(coord.correo)+','+str(docente.persona.emailinst)
                                                materia.correo_multasnotas(docente,email,MULTA24H)

                                            #Obtain client ip address
                                            client_address = ip_client_address(request)
                                            # Log de Adicionar Multa de 24H
                                            LogEntry.objects.log_action(
                                                user_id         = request.user.pk,
                                                content_type_id = ContentType.objects.get_for_model(multa24).pk,
                                                object_id       = multa24.id,
                                                object_repr     = force_str(multa24),
                                                action_flag     = ADDITION,
                                                change_message  = 'Se genero multa de 24H ' + client_address + ')' )
                                            return HttpResponse(json.dumps({'result': 'ok'}),content_type="application/json")
                            else:
                                # return HttpResponseRedirect("/?info= LOS CASILLEROS DE LA MATERIA SE ENCUENTRAN ACTIVOS ")
                                return HttpResponse(json.dumps({'result': 'bad2'}), content_type="application/json")
                    else:
                        if not materia.nivel.cerrado:
                            tmulta=4
                            desde=datetime.now()
                            hasta=desde + timedelta(days=1)
                            persona = Persona.objects.filter(usuario=request.user)[:1].get()
                            if Profesor.objects.filter(persona=persona).exists():
                                docente = Profesor.objects.filter(persona=persona)[:1].get()

                            if materia.multaactiva():
                                if MultaDocenteMateria.objects.filter(materia=materia,profesor=docente,tipomulta=tmulta,activo=True).exists():
                                    return HttpResponse(json.dumps({'result': 'bad'}),content_type="application/json")
                            else:
                                multa24cierre= MultaDocenteMateria(materia=materia,
                                         profesor=docente,
                                         tipomulta_id=tmulta,
                                         fechadesde=desde,
                                         fechahasta=hasta,
                                         usuario=request.user,
                                         activo=True)
                                multa24cierre.save()

                                carrera=  materia.nivel.carrera
                                if Coordinacion.objects.filter(carrera=carrera).exists():
                                    coord = Coordinacion.objects.filter(carrera=carrera)[:1].get()
                                    email=str(coord.correo)+','+str(docente.persona.emailinst)
                                    materia.correo_multasnotas(docente,email,MULTA24H)

                                materia.cerrado=False
                                materia.save()

                                #Obtain client ip address
                                client_address = ip_client_address(request)
                                # Log de Multa Materia cerrada
                                LogEntry.objects.log_action(
                                    user_id         = request.user.pk,
                                    content_type_id = ContentType.objects.get_for_model(multa24cierre).pk,
                                    object_id       = multa24cierre.id,
                                    object_repr     = force_str(multa24cierre),
                                    action_flag     = ADDITION,
                                    change_message  = 'Se genero multa 24H materia cerrada ' + client_address + ')' )

                                return HttpResponse(json.dumps({'result': 'ok'}),content_type="application/json")
                            # else:
                            #     return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")
                        else:
                            return HttpResponseRedirect("/?info= NIVEL SE ENCUENTRA CERRADO ")

                except Exception as ex:
                    return HttpResponse(json.dumps({'result': 'bad'}),content_type="application/json")

            elif action=='habilita48':
                try:
                    finasignacion=False
                    tmulta=MULTA48H
                    docente=''
                    materia = Materia.objects.get(pk=request.POST['h48'])
                    if not materia.cerrado:
                        if materia.verificacioncierremateria():
                            desde=datetime.now()
                            hasta=desde + timedelta(days=2)
                            persona = Persona.objects.filter(usuario=request.user)[:1].get()
                            if Profesor.objects.filter(persona=persona).exists():
                                docente = Profesor.objects.filter(persona=persona)[:1].get()

                            if materia.multaactiva():
                                if MultaDocenteMateria.objects.filter(materia=materia,profesor=docente,tipomulta=tmulta,activo=True).exists():
                                   return HttpResponse(json.dumps({'result': 'bad'}),content_type="application/json")
                            else:
                                multa48= MultaDocenteMateria(materia=materia,
                                         profesor=docente,
                                         tipomulta_id=tmulta,
                                         fechadesde=desde,
                                         fechahasta=hasta,
                                         usuario=request.user,
                                         activo=True)
                                multa48.save()

                                carrera=  materia.nivel.carrera
                                if Coordinacion.objects.filter(carrera=carrera).exists():
                                    coord = Coordinacion.objects.filter(carrera=carrera)[:1].get()
                                    email=str(coord.correo)+','+str(docente.persona.emailinst)
                                    materia.correo_multasnotas(docente,email,MULTA48H)

                                #Obtain client ip address
                                client_address = ip_client_address(request)
                                # Log de Multa por 48 Horas
                                LogEntry.objects.log_action(
                                    user_id         = request.user.pk,
                                    content_type_id = ContentType.objects.get_for_model(multa48).pk,
                                    object_id       = multa48.id,
                                    object_repr     = force_str(multa48),
                                    action_flag     = ADDITION,
                                    change_message  = 'Se genero multa de 48H ' + client_address + ')' )

                                return HttpResponse(json.dumps({'result': 'ok'}),content_type="application/json")
                            # else:
                            #     return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")
                        else:
                            # return HttpResponseRedirect("/?info= LOS CASILLEROS DE LA MATERIA SE ENCUENTRAN ACTIVOS ")
                            return HttpResponse(json.dumps({'result': 'bad2'}), content_type="application/json")
                    else:
                        if not materia.nivel.cerrado:
                            desde=datetime.now()
                            hasta=desde + timedelta(days=1)
                            persona = Persona.objects.filter(usuario=request.user)[:1].get()
                            if Profesor.objects.filter(persona=persona).exists():
                                docente = Profesor.objects.filter(persona=persona)[:1].get()

                                if MultaDocenteMateria.objects.filter(materia=materia,profesor=docente,tipomulta=tmulta,activo=True).exists():
                                    return HttpResponse(json.dumps({'result': 'bad'}),content_type="application/json")
                                else:
                                    multa48= MultaDocenteMateria(materia=materia,
                                             profesor=docente,
                                             tipomulta_id=tmulta,
                                             fechadesde=desde,
                                             fechahasta=hasta,
                                             usuario=request.user,
                                             activo=True)
                                    multa48.save()

                                    carrera=  materia.nivel.carrera
                                    if Coordinacion.objects.filter(carrera=carrera).exists():
                                        coord = Coordinacion.objects.filter(carrera=carrera)[:1].get()
                                        email=str(coord.correo)+','+str(docente.persona.emailinst)
                                        materia.correo_multasnotas(docente,email,MULTA48H)

                                    materia.cerrado=False
                                    materia.save()
                                    return HttpResponse(json.dumps({'result': 'ok'}),content_type="application/json")
                        else:
                            return HttpResponseRedirect("/?info= NIVEL SE ENCUENTRA CERRADO ")
                except Exception as ex:
                    return HttpResponse(json.dumps({'result': 'bad'}),content_type="application/json")

            elif action == 'observaciones':
                ma = MateriaAsignada.objects.get(pk=request.POST['id'])
                evaluacion = ma.evaluacion()
                f = EvaluacionObservacionForm(request.POST)
                if f.is_valid():
                    if not evaluacion.observaciones:
                        evaluacion.observaciones = '-> ' + f.cleaned_data['observaciones']
                    else:
                        evaluacion.observaciones += plaintext2html('\r -> '+ f.cleaned_data['observaciones'])
                    evaluacion.save()
                return HttpResponseRedirect("/pro_evaluaciones?materia="+str(evaluacion.materiaasignada.materia.id))

            elif action=='claveevaluanota':
                try:
                    materia = Materia.objects.get(pk=request.POST['idmate'])
                    persona = Persona.objects.filter(usuario=request.user)[:1].get()
                    if Profesor.objects.filter(persona=persona).exists():
                        profesor = Profesor.objects.filter(persona=persona)[:1].get()
                        if ProfesorMateria.objects.filter(Q(materia=materia,profesor=profesor)| Q(materia=materia,profesor_aux=profesor.id)).exists():
                            clave=str(random.randint(1, 9))+str(random.randint(1, 9))+str(random.randint(1, 9))+str(random.randint(1, 9))

                            #Obtain client ip address
                            client_address = ip_client_address(request)
                            if ClaveEvaluacionNota.objects.filter(usuario=request.user).exists():
                                claveevaluacionnota = ClaveEvaluacionNota.objects.filter(usuario=request.user)[:1].get()
                                claveevaluacionnota.clave=clave
                                claveevaluacionnota.claveconfirm=''
                                claveevaluacionnota.fecha=datetime.now()
                                claveevaluacionnota.maquina=client_address
                            else:
                                claveevaluacionnota = ClaveEvaluacionNota(usuario=request.user,clave=clave,fecha=datetime.now().date(),claveconfirm='',maquina=client_address)
                            claveevaluacionnota.save()

                            if EMAIL_ACTIVE:
                                claveevaluacionnota.email_claveevaluanota(str(persona.emailinst))



                            # Log de ABRIR ACTA DE NOTAS
                            LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(claveevaluacionnota).pk,
                                object_id       = claveevaluacionnota.id,
                                object_repr     = force_str(claveevaluacionnota),
                                action_flag     = ADDITION,
                                change_message  = 'Solicitando Codigo (' + client_address + ')' )

                            return HttpResponse(json.dumps({"result": "ok","email":str(persona.emailinst)}),content_type="application/json")
                        return HttpResponse(json.dumps({"result": "bad"}),content_type="application/json")
                    return HttpResponse(json.dumps({"result": "bad"}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad", "error": str(ex)}),content_type="application/json")

            elif action=='validaclave':
                try:

                    if ClaveEvaluacionNota.objects.filter(usuario=request.user,clave=request.POST['clave']).exists():
                        claveevaluacionnota = ClaveEvaluacionNota.objects.filter(usuario=request.user,clave=request.POST['clave'])[:1].get()
                        claveevaluacionnota.claveconfirm=request.POST['clave']
                        claveevaluacionnota.save()
                        return HttpResponse(json.dumps({"result": "ok"}),content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({"result": "bad"}),content_type="application/json")


                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad", "error": str(ex)}),content_type="application/json")

            elif action=='generarespecie':
                try:
                    fechamax = (datetime.now() - timedelta(days=DIAS_ESPECIE)).date()
                    materiaasignada = MateriaAsignada.objects.get(pk=request.POST['matasignada'])
                    inscrip=materiaasignada.matricula.inscripcion
                    persona = Persona.objects.filter(usuario=request.user)[:1].get()
                    profesor = Profesor.objects.filter(persona=persona)[:1].get()
                    tipoEspecie = TipoEspecieValorada.objects.get(pk=ID_TIPO_ESPECIE_REG_NOTA)
                    if not RubroEspecieValorada.objects.filter(materia=materiaasignada,rubro__inscripcion=inscrip,tipoespecie__id=ID_TIPO_ESPECIE_REG_NOTA,aplicada = False,rubro__fecha__gt=fechamax,rubro__cancelado=True).exists():
                        rubro = Rubro(fecha=datetime.now().date(),
                                      valor=tipoEspecie.precio,
                                      inscripcion = inscrip,
                                      cancelado=tipoEspecie.precio==0,
                                      fechavence=datetime.now().date())
                        rubro.save()

                        # Rubro especie valorada
                        rubroenot = generador_especies.generar_especie(rubro=rubro, tipo=tipoEspecie)
                        if tipoEspecie.id == ID_TIPO_ESPECIE_REG_NOTA:
                            if rubroenot:
                                rubroenot.fecha = datetime.now().date()
                                rubroenot.usuario = request.user
                                rubroenot.materia_id = materiaasignada.id
                                rubroenot.profesor=profesor
                                rubroenot.save()

                        datos = {"result": "ok"}

                        if EMAIL_ACTIVE:
                            contenido='Estimado/a estudiante se ha generado una especie de Asentamiento de Notas. Favor acercarse a caja a cancelarla'
                            asunto='Especie Asentamiento Notas'
                            emailestudiante=str(materiaasignada.matricula.inscripcion.persona.emailinst)+','+str(materiaasignada.matricula.inscripcion.persona.email)
                            mail_correoalumnoespecie(contenido,asunto,request.user,materiaasignada,emailestudiante,profesor.persona.nombre_completo_inverso())

                        return HttpResponse(json.dumps(datos),content_type="application/json")
                    else:
                        datos = {"result": "error"}
                        return HttpResponse(json.dumps(datos),content_type="application/json")

                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad", "error": str(ex)}),content_type="application/json")


            elif action=='subirnota':
                try:
                    data = {}
                    addUserData(request, data)
                    materia = Materia.objects.get(pk=request.POST['id'])
                    nota=int(request.POST['idnota'])
                    codigo = None
                    codigo = CodigoEvaluacion.objects.get(pk=request.POST['idcodigoeve'])
                    profesor = Profesor.objects.get(persona=data['persona'])
                    subirarch = SubirArchivoNota(archivo=request.FILES["file"], profesor=profesor.persona,
                                             fecharegistro=datetime.now())
                    subirarch.save()

                    wb = xlrd.open_workbook(MEDIA_ROOT + '/' + str(subirarch.archivo))

                    hoja = wb.sheet_by_index(0)
                    for i in range(0, hoja.nrows):
                        if i>0:
                            if User.objects.filter(username=str(hoja.cell_value(i, 0)).strip()).exists():
                                usuario=User.objects.get(username=str(hoja.cell_value(i, 0)).strip())

                                for m in materia.asignados_a_esta_materia():

                                        if m.matricula.inscripcion.persona.usuario_id==usuario.id:
                                            if if_integer(hoja.cell_value(i, 3)):
                                                evaluacion = m.evaluacion()

                                                if nota == 1:
                                                    if float(hoja.cell_value(i, 3))<=PORCIENTO_NOTA1:
                                                        evaluacion.n1 = float(hoja.cell_value(i, 3))
                                                        evaluacion.cod1 = codigo
                                                        evaluacion.save()
                                                    else:
                                                        return HttpResponse(json.dumps({'result': 'bad', 'mensaje': str('No se puede terminar de cargar las notas porque la nota del estudiante:' + str(
                                                                hoja.cell_value(i, 1)) + ' ' + str(hoja.cell_value(i,2))) + ' ' + 'se paso del rango establecido'}), content_type="application/json")

                                                if nota == 2:
                                                    if float(hoja.cell_value(i, 3)) <= PORCIENTO_NOTA2:
                                                        evaluacion.n2 = float(hoja.cell_value(i, 3))
                                                        evaluacion.cod2 = codigo
                                                        evaluacion.save()
                                                    else:
                                                        return HttpResponse(json.dumps({'result': 'bad', 'mensaje': str('No se puede terminar de cargar las notas porque la nota del estudiante:' + str(
                                                                hoja.cell_value(i, 1)) + ' ' + str(hoja.cell_value(i,2))) + ' ' + 'se paso del rango establecido'}),
                                                                            content_type="application/json")

                                                if nota == 3:
                                                    if float(hoja.cell_value(i, 3)) <= PORCIENTO_NOTA3:
                                                        evaluacion.n3 = float(hoja.cell_value(i, 3))
                                                        evaluacion.cod3 = codigo
                                                        evaluacion.save()
                                                    else:
                                                        return HttpResponse(json.dumps({'result': 'bad', 'mensaje': str('No se puede terminar de cargar las notas porque la nota del estudiante:' + str(
                                                                hoja.cell_value(i, 1)) + ' ' + str(hoja.cell_value(i,2))) + ' ' + 'se paso del rango establecido'}),
                                                                            content_type="application/json")

                                                if nota == 4:
                                                    if float(hoja.cell_value(i, 3)) <= PORCIENTO_NOTA4:
                                                        evaluacion.n4 = float(hoja.cell_value(i, 3))
                                                        evaluacion.cod4 = codigo
                                                        evaluacion.save()
                                                    else:
                                                        return HttpResponse(json.dumps({'result': 'bad', 'mensaje': str(
                                                            'No se puede terminar de cargar las notas porque la nota del estudiante:' + str(
                                                                hoja.cell_value(i, 1)) + ' ' + str(
                                                                hoja.cell_value(i,
                                                                                2))) + ' ' + 'se paso del rango estabalecido'}),
                                                                            content_type="application/json")

                                                if nota == 5:
                                                    evaluacion.examen = float(hoja.cell_value(i, 3))
                                                    evaluacion.save()

                                                if nota == 6:
                                                    evaluacion.recuperacion = float(hoja.cell_value(i, 3))
                                                    evaluacion.save()


                                                evaluacion.actualiza_estado_nueva()

                                            else:
                                                return HttpResponse(json.dumps({'result': 'bad', 'mensaje': str(
                                                    'No se puede terminar de cargar las notas porque la nota no es un numero del estudiante:' + str(
                                                        hoja.cell_value(i, 1)) + ' ' + str(hoja.cell_value(i, 2)))}),
                                                                    content_type="application/json")

                            else:
                                return HttpResponse(json.dumps({'result': 'bad','mensaje':str('No se puede terminar de cargar las notas porque no se encontro al siguiente estudiante:'+str(hoja.cell_value(i, 1))+' '+str(hoja.cell_value(i, 2)))}), content_type="application/json")

                    return HttpResponse(json.dumps({'result': 'ok'}), content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({'result': 'bad','mensaje':str(ex)}), content_type="application/json")


            return HttpResponseRedirect("/pro_evaluaciones")


    else:
        data = {'title': 'Evaluaciones por Alumnos'}
        addUserData(request,data)

        if 'action' in request.GET:
            action = request.GET['action']
            if action=='segmento':
                try:
                    periodo_actual = request.session['periodo'] #Periodo.objects.get(activo=True)
                    if not Materia.objects.filter(pk=request.GET['id']).exists():
                        return HttpResponseRedirect("/")
                    else:
                        materia = Materia.objects.get(pk=request.GET['id'])
                        # promediototal = MateriaAsignada.objects.filter(materia=materia,notafinal__gte=NOTA_PARA_APROBAR,asistenciafinal__gte=ASIST_PARA_APROBAR).count()*100/MateriaAsignada.objects.filter(materia=materia).count()
                        # if promediototal <= 40:
                        #     if EMAIL_ACTIVE:
                        #         materia.correo_promedio(promediototal)
                        for m in  MateriaAsignada.objects.filter(materia=materia).order_by('matricula__inscripcion__persona__apellido1','matricula__inscripcion__persona__apellido2','matricula__inscripcion__persona__nombres'):
                            # print(m)
                            if  EvaluacionITB.objects.filter(materiaasignada=m).exists():
                                if  EvaluacionITB.objects.filter(materiaasignada=m).count()>1:
                                    for eva in EvaluacionITB.objects.filter(materiaasignada=m):
                                        if (eva.n1+eva.n2+eva.n3+eva.n4)==0:
                                            eva.delete()
                                            break

                                e = EvaluacionITB.objects.filter(materiaasignada=m)[:1].get()

                                if DEFAULT_PASSWORD == 'itb':
                                    if m.notafinal != e.nota_final_nueva():
                                       m.notafinal = e.nota_final_nueva()
                                else:
                                    if m.notafinal != e.nota_final():
                                       m.notafinal = e.nota_final()
                                m.save()

                                if DEFAULT_PASSWORD == 'itb':
                                    if e.materiaasignada.materia.fin>convertir_fecha('30-09-2019'):
                                        e.actualiza_estado_nueva()
                                else:
                                    e.actualiza_estado()
                        if DEFAULT_PASSWORD == 'itb':
                            if not MultaDocenteMateria.objects.filter(materia=materia,tipomulta=4,activo=True).exists():
                                if materia.verificacioncuatrodias():
                                    materia.cierre_sistema()

                        data['materia'] = materia
                        data['reporte_acta_id'] = REPORTE_ACTA_NOTAS
                        if data['materia'].nivel.carrera.online:
                            data['validarasistencia'] = False
                            data['asistenciaparaaprobar'] = 0
                        else:
                            data['validarasistencia'] = VALIDAR_ASISTENCIAS
                            data['asistenciaparaaprobar'] = ASIST_PARA_APROBAR
                        print(data['asistenciaparaaprobar'] )

                        if MODELO_EVALUACION==EVALUACION_IAVQ:
                            if PeriodoEvaluacionesIAVQ.objects.filter(periodo=periodo_actual).exists():
                                periodoevaluaciones = PeriodoEvaluacionesIAVQ.objects.filter(periodo=periodo_actual)[:1].get()
                            else:
                                periodoevaluaciones = PeriodoEvaluacionesIAVQ(periodo=periodo_actual)
                                periodoevaluaciones.save()
                            data['periodoeval'] = periodoevaluaciones

                        if MODELO_EVALUACION==EVALUACION_ITS:
                            if PeriodoEvaluacionesITS.objects.filter(periodo=periodo_actual).exists():
                                periodoevaluaciones = PeriodoEvaluacionesITS.objects.filter(periodo=periodo_actual)[:1].get()
                            else:
                                periodoevaluaciones = PeriodoEvaluacionesITS(periodo=periodo_actual)
                                periodoevaluaciones.save()
                            data['periodoeval'] = periodoevaluaciones

                        if MODELO_EVALUACION==EVALUACION_ITB or MODELO_EVALUACION==EVALUACION_IGAD:
                            data['codigos'] = CodigoEvaluacion.objects.all().order_by('id')
                            if CodigoEvaluacion.objects.filter(codn1__materiaasignada__materia=data['materia']).exists():
                                data['cod1'] = CodigoEvaluacion.objects.filter(codn1__materiaasignada__materia=data['materia'])[:1].get()
                            if CodigoEvaluacion.objects.filter(codn2__materiaasignada__materia=data['materia']).exists():
                                data['cod2'] = CodigoEvaluacion.objects.filter(codn2__materiaasignada__materia=data['materia'])[:1].get()
                            if CodigoEvaluacion.objects.filter(codn3__materiaasignada__materia=data['materia']).exists():
                                data['cod3'] = CodigoEvaluacion.objects.filter(codn3__materiaasignada__materia=data['materia'])[:1].get()
                            if CodigoEvaluacion.objects.filter(codn4__materiaasignada__materia=data['materia']).exists():
                                data['cod4'] = CodigoEvaluacion.objects.filter(codn4__materiaasignada__materia=data['materia'])[:1].get()
                            data['conduccion']=INSCRIPCION_CONDUCCION
                            data['codigos_recuperacion'] = CodigoEvaluacion.objects.filter(recuperacion=True).order_by('id')
                            if CodigoEvaluacion.objects.filter(codn1__materiaasignada__materia=data['materia'],recuperacion=True).exists():
                                data['cod1rec'] = CodigoEvaluacion.objects.filter(codn1__materiaasignada__materia=data['materia'],recuperacion=True)[:1].get()
                            if CodigoEvaluacion.objects.filter(codn2__materiaasignada__materia=data['materia'],recuperacion=True).exists():
                                data['cod2rec'] = CodigoEvaluacion.objects.filter(codn2__materiaasignada__materia=data['materia'],recuperacion=True)[:1].get()
                            if CodigoEvaluacion.objects.filter(codn3__materiaasignada__materia=data['materia'],recuperacion=True).exists():
                                data['cod3rec'] = CodigoEvaluacion.objects.filter(codn3__materiaasignada__materia=data['materia'],recuperacion=True)[:1].get()
                            if CodigoEvaluacion.objects.filter(codn4__materiaasignada__materia=data['materia'],recuperacion=True).exists():
                                data['cod4rec'] = CodigoEvaluacion.objects.filter(codn4__materiaasignada__materia=data['materia'],recuperacion=True)[:1].get()

                        data['MODELO_EVALUATIVO'] = [MODELO_EVALUACION, EVALUACION_IAVQ, EVALUACION_ITB, EVALUACION_ITS, EVALUACION_TES, EVALUACION_IGAD, EVALUACION_CASADE]
                        data['modulofinanzas'] = MODULO_FINANZAS_ACTIVO
                        data['validardeuda'] = VALIDA_DEUDA_EVALUACIONES
                        data['valida_deuda_exam_asist'] = not VALIDA_DEUDA_EXAM_ASIST

                        data['incluyepago'] = PAGO_ESTRICTO
                        data['incluyedatos'] = DATOS_ESTRICTO
                        data['periodo'] =  request.session['periodo']

                        #Obtain client ip address
                        client_address = ip_client_address(request)

                        # Log de ABRIR ACTA DE NOTAS
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(materia).pk,
                            object_id       = materia.id,
                            object_repr     = force_str(materia),
                            action_flag     = ADDITION,
                            change_message  = 'Abierta Acta de Notas (' + client_address + ')' )
                        if VALIDA_CLAVE_CALIFICACION:
                            if not ClaveEvaluacionNota.objects.filter(usuario=request.user,fecha__gte=datetime.now().date()).exclude(claveconfirm='').exists():
                                data['claveevaluacionnota'] = True

                        data['min_aproba']=MIN_APROBACION
                        data['max_aproba']=MAX_APROBACION
                        data['min_recupera']=MIN_RECUPERACION
                        data['max_recupera']=MAX_RECUPERACION
                        data['min_exa']=MIN_EXAMEN
                        data['max_exa']=MAX_EXAMEN
                        data['min_exarecupera']=MIN_EXAMENRECUPERACION
                        data['DEFAULT_PASSWORD']=DEFAULT_PASSWORD
                        data ['centro_externo']=CENTRO_EXTERNO
                        data ['fechadia']=hoy
                        data ['nivel_seminario']=NIVEL_SEMINARIO
                        data['nota_para_aprobar']=NOTA_PARA_APROBAR

                        return render(request ,"pro_evaluaciones/segmento1bs.html" ,  data)


                except Exception as ex:
                    print((ex))
                    return render(request ,"pro_evaluaciones/segmento1bs.html" ,  data)

            elif action=='editnota':
                data['title'] = 'Evaluacion del Alumno'
                materiaasignada = MateriaAsignada.objects.get(pk=request.GET['id'])
                profesor = Profesor.objects.get(persona=data['persona'])
                tipo_nota = int(request.GET['n'])
                evaluacion = materiaasignada.evaluacion()
                if tipo_nota==1:
                    NotasIavq = evaluacion.n1
                else:
                    NotasIavq = evaluacion.n2

                initial = model_to_dict(NotasIavq)
                data['evaluacion'] = evaluacion
                data['notaiavq'] = NotasIavq
                data['form'] = NotaIAVQForm(initial)

                data['materiaasignada'] = materiaasignada
                data['profesor'] = profesor
                data['tipo'] = tipo_nota
                data['porciento_p1'] = PORCIENTO_NOTA1
                data['porciento_p2'] = PORCIENTO_NOTA2
                data['porciento_p3'] = PORCIENTO_NOTA3
                data['porciento_p4'] = PORCIENTO_NOTA4
                data['porciento_p5'] = PORCIENTO_NOTA5

                return render(request ,"pro_evaluaciones/editnotabs.html" ,  data)

            elif action=='otrasnotas':
                data['title'] = 'Evaluacion del Alumno'
                materiaasignada = MateriaAsignada.objects.get(pk=request.GET['id'])
                profesor = Profesor.objects.get(persona=data['persona'])
                tipo_nota = int(request.GET['n'])

                evaluacion = materiaasignada.evaluacion()

                if tipo_nota == 3:
                    data['tipo_num'] = 3
                    data['tipo'] = 'Proyecto Integrador'
                    data['valor'] = evaluacion.pi
                if tipo_nota == 4:
                    data['tipo_num'] = 4
                    data['tipo'] = 'Supletorio'
                    data['valor'] = evaluacion.su

                matricula = materiaasignada.matricula
                data['matricula'] = matricula
                data['materiaasignada'] = materiaasignada
                data['profesor'] = profesor
                return render(request ,"pro_evaluaciones/otranotabs.html" ,  data)

            elif action=='observaciones':
                ma = MateriaAsignada.objects.get(pk=request.GET['id'])
                evaluacion = ma.evaluacion()
                data['evaluacion'] = evaluacion
                data['form'] = EvaluacionObservacionForm()
                return render(request ,"pro_evaluaciones/observacion.html" ,  data)
        else:
            data = {'title': 'Evaluaciones de Alumnos'}
            addUserData(request,data)
            try:
                profesor = Profesor.objects.get(persona=data['persona'])
                data['profesor'] = profesor
                periodo = request.session['periodo']
                data['DEFAULT_PASSWORD']=DEFAULT_PASSWORD
                data ['ASISTENCIA']=ASIST_PARA_APROBAR
                if Materia.objects.filter(Q(nivel__periodo=periodo) & (Q(profesormateria__profesor=profesor,profesormateria__profesor_aux=None) | Q(profesormateria__profesor_aux=profesor.id))).exists():
                    if CENTRO_EXTERNO:
                        materias = Materia.objects.filter(cerrado=False, nivel__periodo__activo=True, profesormateria__profesor=profesor)
                    else:
                        if profesor.categoria.id == PROFE_PRACT_CONDUCCION:
                            materias = Materia.objects.filter(nivel__periodo=periodo, profesormateria__profesor_aux=profesor.id)
                        else:
                            #OCastillo 13-07-2021 para Buck Center que no realiza el proceso de aceptacion materia
                            if profesor.id==428:
                                materias = Materia.objects.filter(Q(nivel__periodo=periodo)& (Q(profesormateria__profesor=profesor,profesormateria__profesor_aux=None) | Q(profesormateria__profesor_aux=profesor.id)))
                            else:
                             materias = Materia.objects.filter(Q(nivel__periodo=periodo)& (Q(profesormateria__profesor=profesor,profesormateria__profesor_aux=None,profesormateria__aceptacion=True) | Q(profesormateria__profesor_aux=profesor.id,profesormateria__aceptacion=True)))

                    data['materias'] = materias
                    data['codigos'] = CodigoEvaluacion.objects.all().order_by('id')
                    if 'materia' in request.GET:
                        materiaid = request.GET['materia']
                        data['materiaid'] = int(materiaid)
                        data['materia'] = Materia.objects.get(pk=data['materiaid'])
                        periodo_actual = request.session['periodo'] #Periodo.objects.get(activo=True)

                        if MODELO_EVALUACION==EVALUACION_IAVQ:
                            if PeriodoEvaluacionesIAVQ.objects.filter(periodo=periodo_actual).exists():
                                periodoevaluaciones = PeriodoEvaluacionesIAVQ.objects.filter(periodo=periodo_actual)[:1].get()
                            else:
                                periodoevaluaciones = PeriodoEvaluacionesIAVQ(periodo=periodo_actual)
                                periodoevaluaciones.save()
                            data['periodoeval'] = periodoevaluaciones

                        if MODELO_EVALUACION==EVALUACION_ITS:
                            if PeriodoEvaluacionesITS.objects.filter(periodo=periodo_actual).exists():
                                periodoevaluaciones = PeriodoEvaluacionesITS.objects.filter(periodo=periodo_actual)[:1].get()
                            else:
                                periodoevaluaciones = PeriodoEvaluacionesITS(periodo=periodo_actual)
                                periodoevaluaciones.save()
                            data['periodoeval'] = periodoevaluaciones

                        if MODELO_EVALUACION==EVALUACION_ITB or MODELO_EVALUACION==EVALUACION_IGAD:
                            data['codigos'] = CodigoEvaluacion.objects.all().order_by('id')
                            if CodigoEvaluacion.objects.filter(codn1__materiaasignada__materia=data['materia']).exists():
                                data['cod1'] = CodigoEvaluacion.objects.filter(codn1__materiaasignada__materia=data['materia'])[:1].get()
                            if CodigoEvaluacion.objects.filter(codn2__materiaasignada__materia=data['materia']).exists():
                                data['cod2'] = CodigoEvaluacion.objects.filter(codn2__materiaasignada__materia=data['materia'])[:1].get()
                            if CodigoEvaluacion.objects.filter(codn3__materiaasignada__materia=data['materia']).exists():
                                data['cod3'] = CodigoEvaluacion.objects.filter(codn3__materiaasignada__materia=data['materia'])[:1].get()
                            if CodigoEvaluacion.objects.filter(codn4__materiaasignada__materia=data['materia']).exists():
                                data['cod4'] = CodigoEvaluacion.objects.filter(codn4__materiaasignada__materia=data['materia'])[:1].get()

                        data['conduccion']=INSCRIPCION_CONDUCCION
                        data['codigos_recuperacion'] = CodigoEvaluacion.objects.filter(recuperacion=True).order_by('id')
                        if CodigoEvaluacion.objects.filter(codn1__materiaasignada__materia=data['materia'],recuperacion=True).exists():
                            data['cod1rec'] = CodigoEvaluacion.objects.filter(codn1__materiaasignada__materia=data['materia'],recuperacion=True)[:1].get()
                        if CodigoEvaluacion.objects.filter(codn2__materiaasignada__materia=data['materia'],recuperacion=True).exists():
                            data['cod2rec'] = CodigoEvaluacion.objects.filter(codn2__materiaasignada__materia=data['materia'],recuperacion=True)[:1].get()
                        if CodigoEvaluacion.objects.filter(codn3__materiaasignada__materia=data['materia'],recuperacion=True).exists():
                            data['cod3rec'] = CodigoEvaluacion.objects.filter(codn3__materiaasignada__materia=data['materia'],recuperacion=True)[:1].get()
                        if CodigoEvaluacion.objects.filter(codn4__materiaasignada__materia=data['materia'],recuperacion=True).exists():
                            data['cod4rec'] = CodigoEvaluacion.objects.filter(codn4__materiaasignada__materia=data['materia'],recuperacion=True)[:1].get()

                        data['modulofinanzas'] = MODULO_FINANZAS_ACTIVO
                        data['incluyepago'] = PAGO_ESTRICTO
                        data['incluyedatos'] = DATOS_ESTRICTO
                        data['validardeuda'] = VALIDA_DEUDA_EVALUACIONES
                        data['valida_deuda_exam_asist'] = not VALIDA_DEUDA_EXAM_ASIST
                        if data['materia'].nivel.carrera.online:
                            data['validarasistencia'] = False
                            data['asistenciaparaaprobar'] = 0
                        else:
                            data['validarasistencia'] = VALIDAR_ASISTENCIAS
                            data['asistenciaparaaprobar'] = ASIST_PARA_APROBAR


                        data['MODELO_EVALUATIVO'] = [MODELO_EVALUACION, EVALUACION_IAVQ, EVALUACION_ITB, EVALUACION_ITS, EVALUACION_TES, EVALUACION_IGAD, EVALUACION_CASADE]
                        data ['centro_externo']=CENTRO_EXTERNO
                        data['DEFAULT_PASSWORD']=DEFAULT_PASSWORD
                        data ['nivel_seminario']=NIVEL_SEMINARIO

                        data['listadoprecargado'] = get_template("pro_evaluaciones/segmento1bs.html").render(RequestContext(request, data))
                    return render(request ,"pro_evaluaciones/evaluacionesbs.html" ,  data)
                else:
                    return HttpResponseRedirect("/?info=No tiene Materias en el periodo, SELECCIONE OTRO PERIODO")
            except Exception as t:
                print(t)
                return HttpResponseRedirect("/")
