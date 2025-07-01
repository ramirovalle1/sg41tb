from datetime import datetime, time,timedelta
import json

from django.contrib.admin.models import LogEntry, ADDITION, DELETION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models.query_utils import Q
from django.forms.models import model_to_dict
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template.context import RequestContext
from django.template.loader import get_template
from django.utils.encoding import force_str

from decorators import secure_module,inclassroom_check
from settings import PAGO_ESTRICTO, DATOS_ESTRICTO, ASIST_PARA_APROBAR, NOTA_PARA_APROBAR, ASIST_PARA_SEGUIR, PORCIENTO_NOTA1, PORCIENTO_NOTA2, PORCIENTO_NOTA3, PORCIENTO_NOTA4, \
     PORCIENTO_NOTA5, NOTA_ESTADO_APROBADO, NOTA_ESTADO_EN_CURSO, NOTA_ESTADO_REPROBADO, NOTA_ESTADO_SUPLETORIO, NOTA_PARA_SUPLET, REPORTE_ACTA_NOTAS, EVALUACION_IAVQ, \
     MODELO_EVALUACION, EVALUACION_ITB, EVALUACION_ITS, MODULO_FINANZAS_ACTIVO, REPORTE_CRONOGRAMA_PROFESOR, PUEDE_CAMBIAR_CALIFICACIONES, EVALUACION_TES, EVALUACION_IGAD, \
     CENTRO_EXTERNO, USA_MODULO_JUSTIFICACION_AUSENCIAS, VICERECTORADO_GROUP_ID, RECTORADO_GROUP_ID, SISTEMAS_GROUP_ID, EVALUACION_CASADE, PROFE_PRACT_CONDUCCION,EMAIL_ACTIVE, \
     COORDINACION_ACADEMICA_UASS,COORD_ACADEMICO_UACECD, DEFAULT_PASSWORD, SEGUIMIENTO_SYLLABUS, CANTIDAD_JUSTIFICACION_ESPECIE, VALIDA_ABRIR_CLASES, VALIDA_MATERIA_APROBADA,\
     ESPECIE_JUSTIFICA_FALTA, INSCRIPCION_CONDUCCION,DIAS_ESPECIE, MIN_EXAMEN
from sga.commonviews import addUserData, ip_client_address
from sga.finanzas import convertir_fecha
from sga.forms import NotaIAVQForm, AusenciaJustificadaForm, MotivoApertura,MotivoCambioNotaForm,MotivoCierreClasesForm
from sga.models import Profesor, LeccionGrupo, AsistenciaLeccion, Turno, Aula, Clase, Leccion, Sesion, Materia, MateriaAsignada, CodigoEvaluacion, PeriodoEvaluacionesIAVQ, AusenciaJustificada, \
     EvaluacionITB, TipoEstado, RubroEspecieValorada,ProfesorMateria,RolPago, Absentismo, TemaSyllabus,SubTemaSyll,DetalleSubTemaSyll, SeguimientoSyllabus, SeguimientoTema, SeguimientoDetalleTema,\
     SeguimientoSubTema, SeguimientoDetalleSubTema, Inscripcion, MotivoAlcance,TipoMotivoCierreClases


@login_required(redirect_field_name='ret', login_url='/login')
@secure_module

def view(request):

    try:
        if request.method == 'POST':
            action = request.POST['action']
            op =0
            if action == 'deleteclase':
                lecciongrupo = LeccionGrupo.objects.get(pk=request.POST['id'])
                if  RolPago.objects.filter(inicio__lte = lecciongrupo.fecha ,fin__gte =lecciongrupo.fecha,activo=True ).order_by('-id').exists():
                    r = RolPago.objects.filter(inicio__lte = lecciongrupo.fecha , fin__gte =lecciongrupo.fecha,activo=True ).order_by('-id')[:1].get()
                    if r.fechamax >= datetime.now().date():
                        op = 1
                else:
                    op=1
                if  op == 1:
                    try:
                    # case server externo
                         client_address = request.META['HTTP_X_FORWARDED_FOR']
                    except:
                    # case localhost o 127.0.0.1
                            client_address = request.META['REMOTE_ADDR']
                        # Log de CERRAR MATERIA
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(lecciongrupo).pk,
                        object_id       = lecciongrupo.id,
                        object_repr     = force_str(lecciongrupo),
                        action_flag     = DELETION,
                        change_message  = 'Eliminada  Clase  (' + client_address + ')' )
                    profesor = lecciongrupo.profesor_id
                    todaslecciones = lecciongrupo.lecciones.all()
                    for lecciones in todaslecciones:
                        lecciones.delete()
                    lecciongrupo.delete()

                    return HttpResponseRedirect("/adm_docentes?action=clases&id=" + str(profesor))
                else:
                    return HttpResponseRedirect("/adm_docentes?action=clases&id=" + str(lecciongrupo.profesor.id)+"&error=1")


            elif action == 'addclase':

                f = MotivoApertura(request.POST)
                ban = 0

                if f.is_valid():
                    hoy = datetime.now().date()

                    profesor = Profesor.objects.get(pk=request.POST['prof'])
                    if LeccionGrupo.objects.filter(profesor=profesor,abierta=True).exists():
                        return HttpResponseRedirect("/adm_docentes?action=nuevaclase&id="+str(profesor.id))

                    if Turno.objects.filter(pk=request.POST['turno']).exists():
                        turno = Turno.objects.get(pk=request.POST['turno'])
                    if Aula.objects.filter(pk=request.POST['aula']).exists():
                        aula = Aula.objects.get(pk=request.POST['aula'])


                    try:
                        # if not Clase.objects.filter(materia__nivel__periodo__activo=True, materia__inicio__lte=hoy, materia__fin__gte=hoy, turno=turno, dia=int(request.POST['dia']), aula=aula, materia__profesormateria__profesor=profesor, materia__profesormateria__desde__lte=hoy, materia__profesormateria__hasta__gte=hoy, materia__cerrado=False).exists():
                        if not Clase.objects.filter(Q(materia__nivel__periodo__activo=True, profesormateria__desde__lte=hoy, profesormateria__hasta__gte=hoy, turno=turno, dia=int(request.POST['dia']), aula=aula,materia__cerrado=False)& (Q(profesormateria__profesor=profesor)|Q(profesormateria__profesor_aux=profesor.id))).exists():

                            return HttpResponseRedirect("/adm_docentes?action=nuevaclase&error=1&id="+str(profesor.id))

                        else:
                            # clases = Clase.objects.filter(materia__nivel__periodo__activo=True, materia__inicio__lte=hoy, materia__fin__gte=hoy, turno=turno, dia=int(request.POST['dia']), aula=aula, materia__profesormateria__profesor=profesor, materia__profesormateria__desde__lte=hoy, materia__profesormateria__hasta__gte=hoy, materia__cerrado=False)
                            clases = Clase.objects.filter(Q(materia__nivel__periodo__activo=True, profesormateria__desde__lte=hoy, profesormateria__hasta__gte=hoy, turno=turno, dia=int(request.POST['dia']), aula=aula,materia__cerrado=False)& (Q(profesormateria__profesor=profesor)|Q(profesormateria__profesor_aux=profesor.id)))
                            ids = []

                            # if Materia.objects.filter(pk=clases[0].materia.id).exists():
                            #     m= Materia.objects.filter(pk=clases[0].materia.id)[:1].get()
                            #     if LeccionGrupo.objects.filter(materia=clases[0].materia).exists():
                            #         l=LeccionGrupo.objects.filter(materia=clases[0].materia).aggregate(Sum('turno__horas'))['turno__horas__sum']
                            #         if l >= m.horas :
                            #             return HttpResponseRedirect("/?info=Ha completado el numero de horas establecidas para esa materia ")

                            leccionGrupo = LeccionGrupo(materia=clases[0].materia, profesor=profesor, turno=turno,
                                                    aula=aula, dia=request.POST['dia'], fecha=datetime.now(),
                                                    horaentrada=turno.comienza, horasalida=turno.termina, abierta=True,
                                                    contenido='', observaciones='')
                            leccionGrupo.save()
                            if ProfesorMateria.objects.filter(materia=clases[0].materia,profesor_aux__gt=0,profesor=profesor).exists():
                                pm = ProfesorMateria.objects.get(materia=clases[0].materia, profesor_aux__gt=0,profesor=profesor)
                                if pm.profesor_aux:
                                    prof=Profesor.objects.get(pk=pm.profesor_aux)
                                    leccionGrupo.profesor=  prof
                                    leccionGrupo.save()
                            for clase in clases:
                                leccion = Leccion(clase=clase, fecha=datetime.now(),
                                                horaentrada=datetime.now().time(),
                                                abierta=True, contenido='',
                                                observaciones='')
                                leccion.save()
                                leccionGrupo.lecciones.add(leccion)
                                materia = clase.materia
                                asignadas = materia.materiaasignada_set.all()
                                for asignada in asignadas:
                                    matricula = asignada.matricula
                                    asistenciaLeccion = AsistenciaLeccion(leccion=leccion, matricula=matricula, asistio=False)
                                    asistenciaLeccion.save()

                                ids.append(leccion.id)
                            leccionGrupo.save()

                            client_address = ip_client_address(request)

                             # LOG DE ABRIR CLASE
                            LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(leccionGrupo).pk,
                            object_id       = leccionGrupo.id,
                            object_repr     = force_str(leccionGrupo),
                            action_flag     = ADDITION,
                            change_message  = 'Abierta Clase desde CE - Motivo:'+ f.cleaned_data['motivo'] +' (' + client_address + ')'  )
                            if EMAIL_ACTIVE:
                                usuario = request.user
                                leccionGrupo.mail_apertura(usuario,f.cleaned_data['motivo'],client_address)

                        return HttpResponseRedirect("/adm_docentes?action=editclase&id=" + str(leccionGrupo.id)+'&b='+str(ban) + "&pm="+str(leccionGrupo.pm()))
                    except Exception as ex:
                        HttpResponseRedirect("/adm_docentes?action=nuevaclase&id="+str(profesor.id))

            elif action=='cerrarmateria':
                    materia = Materia.objects.get(pk=request.POST['mid'])
                    materia.cerrado = True
                    materia.fechacierre = datetime.now()
                    materia.horacierre = datetime.now().time()
                    materia.save()
                    try:
                # case server externo
                       client_address = request.META['HTTP_X_FORWARDED_FOR']
                    except:
                # case localhost o 127.0.0.1
                          client_address = request.META['REMOTE_ADDR']

                    # Log de CERRAR MATERIA
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(materia).pk,
                        object_id       = materia.id,
                        object_repr     = force_str(materia),
                        action_flag     = DELETION,
                        change_message  = 'Cerrada la Materia  (' + client_address + ')'  )

                    return HttpResponse(json.dumps({"result": "ok"}),content_type="application/json")

            elif action=='editnota':
                materiaasignada = MateriaAsignada.objects.get(pk=request.POST['id'])
                profesor = Profesor.objects.get(pk=request.POST['p'])
                evaluacion = materiaasignada.evaluacion()
                tipo = int(request.POST['tipo'])
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
                    materiaasignada.notafinal= evaluacion.nota_final()

                    if evaluacion.n1.nota and evaluacion.n2.nota and evaluacion.pi:
                        if materiaasignada.materia.nivel.carrera.online:
                            if evaluacion.nota_final() >= NOTA_PARA_APROBAR:
                                evaluacion.estado_id = NOTA_ESTADO_APROBADO
                            if (NOTA_PARA_SUPLET <= evaluacion.nota_final() < NOTA_PARA_APROBAR) or (
                                    evaluacion.pi < NOTA_PARA_APROBAR):
                                evaluacion.estado_id = NOTA_ESTADO_SUPLETORIO
                            if evaluacion.nota_final() < NOTA_PARA_SUPLET:
                                evaluacion.estado_id = NOTA_ESTADO_REPROBADO
                        else:
                            if evaluacion.nota_final() >= NOTA_PARA_APROBAR and materiaasignada.porciento_asistencia() >= ASIST_PARA_APROBAR:
                                evaluacion.estado_id = NOTA_ESTADO_APROBADO
                            if (ASIST_PARA_SEGUIR <= materiaasignada.porciento_asistencia() < ASIST_PARA_APROBAR) or (
                                    NOTA_PARA_SUPLET <= evaluacion.nota_final() < NOTA_PARA_APROBAR) or (
                                    evaluacion.pi < NOTA_PARA_APROBAR):
                                evaluacion.estado_id = NOTA_ESTADO_SUPLETORIO
                            if evaluacion.nota_final() < NOTA_PARA_SUPLET or materiaasignada.porciento_asistencia() < ASIST_PARA_SEGUIR:
                                evaluacion.estado_id = NOTA_ESTADO_REPROBADO
                    else:
                        evaluacion.estado_id = NOTA_ESTADO_EN_CURSO

                    evaluacion.save()
                    materiaasignada.save()
                    return HttpResponseRedirect("/adm_docentes?action=calificaciones&id=" + str(profesor.id)+"&materia="+str(materiaasignada.materia_id))

            elif action=='actualiza':
                result={}
                c=0
                for m in MateriaAsignada.objects.filter(Q(notafinal__gte=NOTA_PARA_APROBAR, evaluacionitb__estado__id=NOTA_ESTADO_REPROBADO), Q(asistenciafinal__gte=ASIST_PARA_APROBAR, materia__nivel__carrera__online=False) | Q(materia__nivel__carrera__online=True)):

                    if  EvaluacionITB.objects.filter(materiaasignada=m).exists():
                        e = EvaluacionITB.objects.filter(materiaasignada=m)[:1].get()
                        estado= TipoEstado.objects.filter(pk=NOTA_ESTADO_APROBADO)[:1].get()
                        c = c +1
                        e.estado = estado
                        e.save()
                result['result'] = "ok"
                result['c'] = c
                return HttpResponse(json.dumps(result),content_type="application/json")

            elif action=='actualiza2':
                result={}
                c=0
                materia = Materia.objects.filter(pk=request.POST['materia'])[:1].get()
                for m in  MateriaAsignada.objects.filter(materia=materia):
                    if  EvaluacionITB.objects.filter(materiaasignada=m).exists():
                        e = EvaluacionITB.objects.filter(materiaasignada=m)[:1].get()
                        if m.notafinal != e.nota_final():
                           if DEFAULT_PASSWORD == 'itb':
                                if m.materia.fin>convertir_fecha('30-09-2019'):
                                    m.notafinal = e.nota_final_nueva()
                                else:
                                    m.notafinal = e.nota_final()
                           else:
                                m.notafinal = e.nota_final()
                           m.save()
                           c = c +1
                        if DEFAULT_PASSWORD == 'itb':
                            if m.materia.fin>convertir_fecha('30-09-2019'):
                                e.actualiza_estado_nueva()

                result['result'] = "ok"
                result['c'] = c
                return HttpResponse(json.dumps(result),content_type="application/json")

            elif action=='otrasnotas':
                materiaasignada = MateriaAsignada.objects.get(pk=request.POST['id'])
                profesor = Profesor.objects.get(pk=request.POST['p'])
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
                            if evaluacion.nota_final() >= NOTA_PARA_APROBAR:
                                evaluacion.estado_id = NOTA_ESTADO_APROBADO
                            if (NOTA_PARA_SUPLET <= evaluacion.nota_final() < NOTA_PARA_APROBAR) or (
                                    evaluacion.pi < NOTA_PARA_APROBAR):
                                evaluacion.estado_id = NOTA_ESTADO_SUPLETORIO
                            if evaluacion.nota_final() < NOTA_PARA_SUPLET:
                                evaluacion.estado_id = NOTA_ESTADO_REPROBADO
                        else:
                            if evaluacion.nota_final() >= NOTA_PARA_APROBAR and materiaasignada.porciento_asistencia() >= ASIST_PARA_APROBAR:
                                evaluacion.estado_id = NOTA_ESTADO_APROBADO
                            if (ASIST_PARA_SEGUIR <= materiaasignada.porciento_asistencia() < ASIST_PARA_APROBAR) or (
                                    NOTA_PARA_SUPLET <= evaluacion.nota_final() < NOTA_PARA_APROBAR) or (
                                    evaluacion.pi < NOTA_PARA_APROBAR):
                                evaluacion.estado_id = NOTA_ESTADO_SUPLETORIO
                            if evaluacion.nota_final() < NOTA_PARA_SUPLET or materiaasignada.porciento_asistencia() < ASIST_PARA_SEGUIR:
                                evaluacion.estado_id = NOTA_ESTADO_REPROBADO
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
                            if materiaasignada2.materia.nivel.carrera.online:
                                if evaluac.nota_final() >= NOTA_PARA_APROBAR:
                                    evaluac.estado_id = NOTA_ESTADO_APROBADO
                                if (NOTA_PARA_SUPLET <= evaluac.nota_final() < NOTA_PARA_APROBAR):
                                    evaluac.estado_id = NOTA_ESTADO_SUPLETORIO
                                if evaluac.nota_final() < NOTA_PARA_SUPLET:
                                    evaluac.estado_id = NOTA_ESTADO_REPROBADO
                            else:
                                if evaluac.nota_final() >= NOTA_PARA_APROBAR and materiaasignada2.porciento_asistencia() >= ASIST_PARA_APROBAR:
                                    evaluac.estado_id = NOTA_ESTADO_APROBADO
                                if (
                                        ASIST_PARA_SEGUIR <= materiaasignada2.porciento_asistencia() < ASIST_PARA_APROBAR) or (
                                        NOTA_PARA_SUPLET <= evaluac.nota_final() < NOTA_PARA_APROBAR):
                                    evaluac.estado_id = NOTA_ESTADO_SUPLETORIO
                                if evaluac.nota_final() < NOTA_PARA_SUPLET or materiaasignada.porciento_asistencia() < ASIST_PARA_SEGUIR:
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
                                if evaluacion.nota_final() < NOTA_PARA_SUPLET:
                                    evaluacion.estado_id = NOTA_ESTADO_REPROBADO
                            else:
                                if evaluacion.nota_final() >= NOTA_PARA_APROBAR and materiaasignada.porciento_asistencia() >= ASIST_PARA_APROBAR:
                                    evaluacion.estado_id = NOTA_ESTADO_APROBADO
                                if (
                                        ASIST_PARA_SEGUIR <= materiaasignada.porciento_asistencia() < ASIST_PARA_APROBAR) or (
                                        NOTA_PARA_SUPLET <= evaluacion.nota_final() < NOTA_PARA_APROBAR) or (
                                        evaluacion.pi < NOTA_PARA_APROBAR):
                                    evaluacion.estado_id = NOTA_ESTADO_SUPLETORIO
                                if evaluacion.nota_final() < NOTA_PARA_SUPLET or materiaasignada.porciento_asistencia() < ASIST_PARA_SEGUIR:
                                    evaluacion.estado_id = NOTA_ESTADO_REPROBADO
                        else:
                            evaluacion.estado_id = NOTA_ESTADO_EN_CURSO

                    evaluacion.save()
                    materiaasignada.save()

                return HttpResponseRedirect("/adm_docentes?action=calificaciones&id=" + str(profesor.id)+"&materia="+str(materiaasignada.materia_id))

            elif action=='justificar2':
                try:
                    profesor = Profesor.objects.get(pk=request.POST['profid'])
                    asistencialeccion = AsistenciaLeccion.objects.get(pk=request.POST['asistid'])
                    numeroespecie = '0000'
                    codigoespecie = '0000'
                    observaciones = request.POST['observaciones'].upper()
                    usuario = request.user
                    hoy = datetime.now().date()

                    aus = AusenciaJustificada(asist=asistencialeccion,numeroe=numeroespecie,
                                                                          codigoe=codigoespecie, fechae=hoy,
                                                          profesor=profesor, observaciones=observaciones,
                                                          fecha=datetime.now(), usuario=usuario,
                                                          inscripcion=asistencialeccion.matricula.inscripcion)
                    aus.save()
                    asistencialeccion.asistio = True
                    asistencialeccion.save()
                    for materiaasignada in asistencialeccion.matricula.materiaasignada_set.all():
                        materiaasignada.save()

                    client_address = ip_client_address(request)

                    # Log de ADICIONAR GRUPO
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(aus).pk,
                        object_id       = aus.id,
                        object_repr     = force_str(aus),
                        action_flag     = ADDITION,
                        change_message  = 'Justificacion de falta a alumno sin especie '+ aus.inscripcion.persona.nombre_completo() +' (' + client_address + ')'  )
                    return HttpResponse(json.dumps({"result": "ok"}),content_type="application/json")

                except Exception as e:
                    return HttpResponse(json.dumps({"result": "bad"}),content_type="application/json")


            elif action=='justificar':
                try:
                    profesor = Profesor.objects.get(pk=request.POST['profid'])
                    asistencialeccion = AsistenciaLeccion.objects.get(pk=request.POST['asistid'])
                    numeroespecie = request.POST['numeroe'].upper()
                    codigoespecie = request.POST['codigoe'].upper()
                    fechaespecie = convertir_fecha(request.POST['fechae'])
                    observaciones = request.POST['observaciones'].upper()
                    usuario = request.user
                    hoy = datetime.now().date()

                    dias = (fechaespecie - asistencialeccion.leccion.fecha).days
                    # OCU 11-enero-2019 se volvio a poner programacion anterior
                    # if not RubroEspecieValorada.objects.filter(serie=request.POST['numeroe'].upper(), rubro__fecha__year = hoy.year,rubro__inscripcion=asistencialeccion.matricula.inscripcion,rubro__cancelado=True).exists():
                    #     return HttpResponse(json.dumps({"result": "badespecie"}),content_type="application/json")

                    #Si el usuario tiene estos permisos podra justificar sin importar los dias de diferencia entre especie y clase
                    if usuario.groups.filter(id__in=[VICERECTORADO_GROUP_ID, RECTORADO_GROUP_ID, SISTEMAS_GROUP_ID,COORDINACION_ACADEMICA_UASS,COORD_ACADEMICO_UACECD]).exists():
                        dias = 0
                    else:
                        # OCU 02-mayo-2017 validacion por validez de 45 dias de especie
                        diasvalidez = (datetime.now().date()- fechaespecie).days
                        dias=diasvalidez

                    # if dias >= 0:
                    #     if dias <= 7:

                    # # OCU 02-mayo-2017 validacion por validez de 45 dias de especie
                    # diasvalidez = (datetime.now().date()- fechaespecie).days
                    if dias <= DIAS_ESPECIE:
                        try:
                            b=1
                            # OCU 11-enero-2019 se volvio a poner programacion anterior
                            if AusenciaJustificada.objects.filter(numeroe=numeroespecie,inscripcion=asistencialeccion.matricula.inscripcion).exists():
                            # if AusenciaJustificada.objects.filter(numeroe=numeroespecie,fecha__year = hoy.year).exists():
                                # OCU 11-enero-2019 se volvio a poner programacion anterior
                                aus = AusenciaJustificada.objects.filter(numeroe=numeroespecie,inscripcion=asistencialeccion.matricula.inscripcion)[:1].get()
                                # aus = AusenciaJustificada.objects.filter(numeroe=numeroespecie,fecha__year = hoy.year)[:1].get()
                                if fechaespecie == aus.fechae:
                                    if asistencialeccion.matricula.inscripcion == aus.inscripcion:
                                        if aus.profesor==profesor:
                                            # OCU 11-enero-2019 se volvio a poner programacion anterior
                                            rubroespecie = RubroEspecieValorada.objects.filter(serie=request.POST['numeroe'].upper(),rubro__inscripcion=asistencialeccion.matricula.inscripcion)[:1].get()
                                            # rubroespecie = RubroEspecieValorada.objects.filter(serie=request.POST['numeroe'].upper(), rubro__fecha__year = hoy.year,rubro__inscripcion=asistencialeccion.matricula.inscripcion)[:1].get()
                                            cantidad =  AusenciaJustificada.objects.filter(numeroe=numeroespecie,profesor=profesor,fechae=fechaespecie,inscripcion=asistencialeccion.matricula.inscripcion).count()
                                            if rubroespecie.es_online():
                                                if not asistencialeccion.aprobado or asistencialeccion.aprobado is None:
                                                    return HttpResponse(json.dumps({"result": "badaprobado"}),content_type="application/json")

                                            if rubroespecie.tipoespecie.id == ESPECIE_JUSTIFICA_FALTA:
                                                if rubroespecie.rubro.fecha <= asistencialeccion.leccion.fecha:
                                                    return HttpResponse(json.dumps({"result": "badfechaesp"}),content_type="application/json")
                                                else:
                                                    cantidad = 0

                                            if cantidad < CANTIDAD_JUSTIFICACION_ESPECIE:

                                                aus = AusenciaJustificada(asist=asistencialeccion, numeroe=numeroespecie,
                                                                          codigoe=codigoespecie, fechae=fechaespecie,
                                                                          profesor=profesor, observaciones=observaciones,
                                                                          fecha=datetime.now(), usuario=usuario,
                                                                          inscripcion=asistencialeccion.matricula.inscripcion)
                                                aus.save()
                                                asistencialeccion.asistio = True
                                                asistencialeccion.save()
                                                for materiaasignada in asistencialeccion.matricula.materiaasignada_set.all():
                                                    materiaasignada.save()

                                                    #OCastillo 24-01-2020 actualiza estado
                                                    if DEFAULT_PASSWORD == 'itb':
                                                        e = EvaluacionITB.objects.filter(materiaasignada=materiaasignada)[:1].get()
                                                        if e.materiaasignada.materia.fin>convertir_fecha('30-09-2019'):
                                                            e.actualiza_estado_nueva()
                                                    else:
                                                        e = EvaluacionITB.objects.filter(materiaasignada=materiaasignada)[:1].get()
                                                        e.actualiza_estado()

                                                #Obtain client ip address
                                                client_address = ip_client_address(request)

                                                # Log de ADICIONAR GRUPO
                                                LogEntry.objects.log_action(
                                                    user_id         = request.user.pk,
                                                    content_type_id = ContentType.objects.get_for_model(aus).pk,
                                                    object_id       = aus.id,
                                                    object_repr     = force_str(aus),
                                                    action_flag     = ADDITION,
                                                    change_message  = 'Justificacion de falta a alumno '+ aus.inscripcion.persona.nombre_completo() +' (' + client_address + ')'  )
                                                return HttpResponse(json.dumps({"result": "ok"}),content_type="application/json")
                                            else:
                                                return HttpResponse(json.dumps({"result": "badcanti"}),content_type="application/json")
                                        else:
                                            return HttpResponse(json.dumps({"result": "badprof"}),content_type="application/json")
                                    else:
                                        return HttpResponse(json.dumps({"result": "badins"}),content_type="application/json")
                                else:
                                    return HttpResponse(json.dumps({"result": "badfechae"}),content_type="application/json")
                            else:
                                aus = AusenciaJustificada(asist=asistencialeccion, numeroe=numeroespecie,
                                                          codigoe=codigoespecie, fechae=fechaespecie,
                                                          profesor=profesor, observaciones=observaciones,
                                                          fecha=datetime.now(), usuario=usuario,
                                                          inscripcion=asistencialeccion.matricula.inscripcion)
                                aus.save()
                                asistencialeccion.asistio = True
                                asistencialeccion.save()
                                for materiaasignada in asistencialeccion.matricula.materiaasignada_set.all():
                                    materiaasignada.save()

                                    #OCastillo 24-01-2020 actualiza estado
                                    if DEFAULT_PASSWORD == 'itb':
                                        e = EvaluacionITB.objects.filter(materiaasignada=materiaasignada)[:1].get()
                                        if e.materiaasignada.materia.fin>convertir_fecha('30-09-2019'):
                                            e.actualiza_estado_nueva()
                                    else:
                                         e = EvaluacionITB.objects.filter(materiaasignada=materiaasignada)[:1].get()
                                         e.actualiza_estado()

                                #Obtain client ip address
                                client_address = ip_client_address(request)

                                # Log de ADICIONAR GRUPO
                                LogEntry.objects.log_action(
                                    user_id         = request.user.pk,
                                    content_type_id = ContentType.objects.get_for_model(aus).pk,
                                    object_id       = aus.id,
                                    object_repr     = force_str(aus),
                                    action_flag     = ADDITION,
                                    change_message  = 'Justificacion de falta a alumno '+ aus.inscripcion.persona.nombre_completo() +' (' + client_address + ')'  )
                                rubroespecie = RubroEspecieValorada.objects.filter(serie=request.POST['numeroe'].upper(),rubro__inscripcion=asistencialeccion.matricula.inscripcion)[:1].get()
                                # rubroespecie = RubroEspecieValorada.objects.filter(serie=request.POST['numeroe'].upper(), rubro__fecha__year = hoy.year,rubro__inscripcion=asistencialeccion.matricula.inscripcion)[:1].get()
                                rubroespecie.codigoe= aus.codigoe
                                rubroespecie.observaciones= aus.observaciones
                                rubroespecie.aplicada= True
                                if AusenciaJustificada.objects.filter(numeroe=numeroespecie,profesor=profesor,fechae=fechaespecie,inscripcion=asistencialeccion.matricula.inscripcion).count()  >= CANTIDAD_JUSTIFICACION_ESPECIE:
                                    rubroespecie.disponible= False
                                rubroespecie.fecha=datetime.now().date()
                                rubroespecie.usuario=request.user
                                rubroespecie.save()
                                return HttpResponse(json.dumps({"result": "ok"}),content_type="application/json")
                        except Exception as ex:
                            return HttpResponse(json.dumps({"result": "bad"}),content_type="application/json")
                    else:
                       # return HttpResponse(json.dumps({"result": "badfechas", "dias": str(dias)}),content_type="application/json")
                       return HttpResponse(json.dumps({"result": "badfechas", "dias": str(diasvalidez)}),content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({"result": "bad"}),content_type="application/json")
                # else:
                #     return HttpResponse(json.dumps({"result": "badfechanegativa", "dias": str(dias)}),content_type="application/json")

            elif action=='fechaespecie':
                # OCastillo 02-mayo-2017 para nueva validez de especie 45 dias
                fechaespecie=request.POST['fechaespecie']
                fe=convertir_fecha(fechaespecie)
                diasvalidez = (datetime.now().date()- fe).days

                if diasvalidez >=DIAS_ESPECIE:
                   return HttpResponse(json.dumps({"result":"bad","dias":diasvalidez}),content_type="application/json")
                else:
                   return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")



            elif action == 'detsubtema':
                try:
                    b = 0
                    detalle2 = SeguimientoDetalleSubTema.objects.get(pk=request.POST['id'])
                    if detalle2.leccion:
                        if not detalle2.leccion.id == int(request.POST['lec']):
                            detalle = SeguimientoDetalleSubTema(seguimientosubtema=detalle2.seguimientosubtema,
                                                                detsubtema=detalle2.detsubtema )
                            detalle.save()
                            b=1
                        else:
                            detalle = detalle2
                    else:
                        detalle = detalle2
                    if request.POST['op'] == '0':
                        detalle.finalizado = False
                    else:
                        detalle.finalizado = True

                    detalle.leccion_id = request.POST['lec']
                    detalle.save()
                    if not detalle.seguimientosubtema.seguimientotema.seguimiento.inicio and b == 0:
                        detalle.seguimientosubtema.seguimientotema.seguimiento.inicio = datetime.now()
                        detalle.seguimientosubtema.seguimientotema.seguimiento.save()
                    if  not detalle.seguimientosubtema.inicio and b == 0:
                        detalle.seguimientosubtema.inicio = datetime.now()
                        detalle.seguimientosubtema.save()
                    if not detalle.seguimientosubtema.seguimientotema.inicio and b == 0:
                        detalle.seguimientosubtema.seguimientotema.inicio = datetime.now()
                        detalle.seguimientosubtema.seguimientotema.save()
                    c = DetalleSubTemaSyll.objects.filter(subtema=detalle.detsubtema.subtema).count()
                    if SeguimientoDetalleSubTema.objects.filter(detsubtema__subtema=detalle.detsubtema.subtema,finalizado=True,seguimientosubtema__seguimientotema__seguimiento__profesor=detalle.seguimientosubtema.seguimientotema.seguimiento.profesor).count() == c:
                       detalle.seguimientosubtema.fin = datetime.now()
                       detalle.seguimientosubtema.finalizado =True
                       detalle.seguimientosubtema.save()
                    detalle.save()

                    cs = SubTemaSyll.objects.filter(tema=detalle.seguimientosubtema.seguimientotema.tema).count()
                    if SeguimientoSubTema.objects.filter(subtema__tema=detalle.seguimientosubtema.seguimientotema.tema,finalizado=True,
                                                         seguimientotema__seguimiento__profesor=detalle.seguimientosubtema.seguimientotema.seguimiento.profesor).count() == cs:
                        detalle.seguimientosubtema.seguimientotema.finalizado = True
                        detalle.seguimientosubtema.seguimientotema.fin =datetime.now()
                        detalle.seguimientosubtema.seguimientotema.save()
                        detalle.seguimientosubtema.finalizado  =True
                        detalle.seguimientosubtema.fin  = datetime.now()
                        detalle.seguimientosubtema.save()

                    t = TemaSyllabus.objects.filter(capitulo__syllabus=detalle.seguimientosubtema.seguimientotema.seguimiento.syllabus,capitulo=detalle.seguimientosubtema.seguimientotema.seguimiento.capitulo).count()
                    if SeguimientoTema.objects.filter(tema__capitulo__syllabus=detalle.seguimientosubtema.seguimientotema.seguimiento.syllabus, tema__capitulo=detalle.seguimientosubtema.seguimientotema.seguimiento.capitulo,finalizado=True,
                                                     seguimiento__profesor=detalle.seguimientosubtema.seguimientotema.seguimiento.profesor).count() == t :
                        detalle.seguimientosubtema.seguimientotema.seguimiento.fin = datetime.now()
                        detalle.seguimientosubtema.seguimientotema.seguimiento.finalizado = True
                        detalle.seguimientosubtema.seguimientotema.seguimiento.save()
                    return HttpResponse(json.dumps({"result":"ok"}), content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({"result":"bad" }), content_type="application/json")

            elif action == 'subtema':
                try:
                    b=0
                    subtema2 = SeguimientoSubTema.objects.get(pk=request.POST['id'])
                    if subtema2.leccion:
                        if not subtema2.leccion.id == int(request.POST['lec']):
                            subtema = SeguimientoSubTema(seguimientotema=subtema2.seguimientotema,
                                                         subtema=subtema2.subtema)
                            subtema.save()
                            b=1
                        else:
                            subtema=subtema2
                    else:
                        subtema=subtema2

                    if request.POST['op'] == '0':
                        subtema.finalizado = False
                    else:
                        subtema.finalizado = True

                    if not SeguimientoDetalleSubTema.objects.filter(seguimientosubtema=subtema).exists() and subtema.finalizado:
                        subtema.fin = datetime.now()
                        subtema.save()


                    subtema.leccion_id = request.POST['lec']
                    subtema.save()
                    if  not subtema.inicio and b == 0:
                        subtema.inicio = datetime.now()
                        subtema.save()
                    if not subtema. seguimientotema.inicio and b == 0:
                        subtema.seguimientotema.inicio=datetime.now()
                        subtema.seguimientotema.save()
                    c = SubTemaSyll.objects.filter(tema=subtema.subtema.tema).count()
                    if SeguimientoSubTema.objects.filter(subtema__tema=subtema.subtema.tema,finalizado=True,
                                                         seguimientotema__seguimiento__profesor=subtema.seguimientotema.seguimiento.profesor).count() == c:
                        subtema.fin = datetime.now()
                        subtema.finalizado =True
                        subtema.save()
                        subtema.seguimientotema.finalizado = True
                        subtema.seguimientotema.fin = datetime.now()
                        subtema.seguimientotema.save()

                    t =  TemaSyllabus.objects.filter(capitulo__syllabus=subtema.seguimientotema.seguimiento.syllabus,capitulo=subtema.seguimientotema.seguimiento.capitulo).count()
                    if SeguimientoTema.objects.filter(tema__capitulo__syllabus=subtema.seguimientotema.seguimiento.syllabus,tema__capitulo=subtema.seguimientotema.seguimiento.capitulo,finalizado=True,
                                                      seguimiento__profesor=subtema.seguimientotema.seguimiento.profesor).count() == t :
                        subtema.seguimientotema.seguimiento.fin = datetime.now()
                        subtema.seguimientotema.seguimiento.finalizado = True
                        subtema.seguimientotema.seguimiento.save()
                    return HttpResponse(json.dumps({"result":"ok"}), content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({"result":"bad" }), content_type="application/json")

            elif action=='addabsen':
                try:
                    if request.POST['absencheck'] == 'true':
                        activo = True
                    else:
                        activo = False
                    absentismo = Absentismo(
                                    materiaasignada_id = request.POST['idmateriasig'],
                                    observacion = request.POST['observacion'],
                                    fecha = datetime.now()
                                    )
                    absentismo.save()
                    materiaasignada = MateriaAsignada.objects.get(id=request.POST['idmateriasig'])
                    materiaasignada.absentismo = activo
                    materiaasignada.save()
                    try:
                        if EMAIL_ACTIVE:
                            absentismo.email_observacion(request.user)
                    except Exception as e:
                        pass
                    return HttpResponse(json.dumps({"result":"ok"}), content_type="application/json")
                except Exception as e:
                   return HttpResponse(json.dumps({"result":"bad"}), content_type="application/json")


            elif action=='addmotivo':
                try:
                    if request.POST['motivo']:
                        motivo = MotivoAlcance(
                                        motivo = request.POST['motivo'].upper(),
                                        fecha = datetime.now(),
                                        usuario=request.user
                                        )
                        motivo.save()
                        return HttpResponse(json.dumps({"result":"ok"}), content_type="application/json")
                except Exception as e:
                   return HttpResponse(json.dumps({"result":"bad"}), content_type="application/json")

            return HttpResponseRedirect("/adm_docentes")


        else:
            data = {'title': 'Administracion de Clases y Evaluaciones'}
            addUserData(request, data)
            if 'action' in request.GET:
                action = request.GET['action']

                if action == 'clases':
                    data['title'] = 'Clases del Docente'
                    profesor = Profesor.objects.get(pk=request.GET['id'])
                    search = None
                    if 's' in request.GET:
                        search = request.GET['s']

                    if search:
                        materia = Materia.objects.get(pk=search)
                        leccionesGrupo = LeccionGrupo.objects.filter(materia__nivel__periodo__activo=True,materia=materia,profesor=profesor).order_by('-fecha', '-horaentrada')
                    else:
                        leccionesGrupo = LeccionGrupo.objects.filter(profesor=profesor, materia__nivel__periodo__activo=True).order_by('-fecha', '-horaentrada')

                    paging = Paginator(leccionesGrupo, 50)
                    p = 1
                    try:
                        if 'page' in request.GET:
                            p = int(request.GET['page'])
                        page = paging.page(p)
                    except:
                        page = paging.page(1)
                    data['paging'] = paging
                    data['page'] = page
                    data['leccionesgrupo'] = page.object_list
                    data['search'] = materia if search else ""

                    data['profesor'] = profesor
                    data['materias'] = profesor.materias_imparte()
                    if 'error' in request.GET:
                        data['error'] = 1
                    return render(request ,"adm_academica/clasesbs.html" ,  data)

                elif action =='actualizartodo':
                    for m in MateriaAsignada.objects.filter(materia__nivel__cerrado=False):
                         m.save()
                elif action == 'nuevaclase':
                    profesor = Profesor.objects.get(pk=request.GET['id'])
                    if 'error' in request.GET:
                        data['error'] = request.GET['error']
                    hoy = datetime.now().date()
                    data['disponible'] = LeccionGrupo.objects.filter(profesor=profesor, abierta=True ).count()==0
                    if not data['disponible']:
                        data['lecciongrupo'] = LeccionGrupo.objects.get(profesor=profesor, abierta=True)
                    data['title'] = 'Horario de Profesor'
                    data['profesor'] = profesor
                    data['semana'] = ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes','Sabado','Domingo']
    #                data['clases'] = Clase.objects.filter(profesor=profesor)
    #                hoy = datetime.now().date()
                    if Profesor.objects.filter(categoria__id = PROFE_PRACT_CONDUCCION, pk = profesor.id):
                        clases = Clase.objects.filter(materia__nivel__periodo__activo=True, materia__profesormateria__profesor_aux=profesor.id, materia__cerrado=False,materia__fin__gte=hoy).order_by('materia__inicio')
                        clasespm = [(x, x.materia.profesormateria_set.filter(profesor_aux=profesor.id)[:1].get()) for x in clases]
                        sesiones = Clase.objects.filter(materia__nivel__periodo__activo=True, materia__profesormateria__profesor_aux=profesor.id, materia__cerrado=False,materia__fin__gte=hoy).distinct('materia__nivel__sesion').values('materia__nivel__sesion')
                    else:
                        if VALIDA_MATERIA_APROBADA :
                            clases = Clase.objects.filter((Q(materia__nivel__periodo__activo=True, materia__cerrado=False,materia__fin__gte=hoy)& (Q(materia__profesormateria__profesor=profesor,materia__profesormateria__profesor_aux=None) | Q(materia__profesormateria__profesor_aux=profesor.id))),materia__aprobada=True).order_by('materia__inicio')
                            clasespm = [(x, x.materia.profesormateria_set.filter(Q(profesor=profesor,profesor_aux=None)|Q(profesor_aux=profesor.id))[:1].get()) for x in clases]
                            sesiones = Clase.objects.filter((Q(materia__nivel__periodo__activo=True, materia__cerrado=False,materia__fin__gte=hoy)& (Q(materia__profesormateria__profesor=profesor,materia__profesormateria__profesor_aux=None) | Q(materia__profesormateria__profesor_aux=profesor.id))),materia__aprobada=True).distinct('materia__nivel__sesion').values('materia__nivel__sesion')
                        else:
                            clases = Clase.objects.filter(Q(materia__nivel__periodo__activo=True, materia__cerrado=False,profesormateria__desde__lte=hoy,profesormateria__hasta__gte=hoy)& (Q(profesormateria__profesor=profesor,profesormateria__profesor_aux=None) | Q(profesormateria__profesor_aux=profesor.id,  profesormateria__desde__lte=hoy, profesormateria__hasta__gte=hoy))).order_by('materia__inicio')
                            cla = clases.filter(materia__id__in=ProfesorMateria.objects.filter(Q(profesor=profesor,profesor_aux=None)|Q(profesor_aux=profesor.id)).values('materia'))
                            clasespm = [(x, x.materia.profesormateria_set.filter(Q(profesor=profesor,profesor_aux=None)|Q(profesor_aux=profesor.id))[:1].get()) for x in cla]
                            # clasespm = [(x, x.materia.profesormateria_set.filter(Q(profesor=profesor,profesor_aux=None)|Q(profesor_aux=profesor.id))[:1].get()) for x in clases]
                            sesiones = Clase.objects.filter(Q(profesormateria__desde__lte=hoy,profesormateria__hasta__gte=hoy)& (Q(profesormateria__profesor=profesor,materia__profesormateria__profesor_aux=None) | Q(profesormateria__profesor_aux=profesor.id))).distinct('materia__nivel__sesion').values('materia__nivel__sesion')
                    data['clases'] = clasespm
                    try:
                        data['pm'] = clasespm[0][1]
                    except:
                        pass
                    data['sesiones'] = Sesion.objects.filter(id__in=sesiones)
                    return render(request ,"adm_academica/horariosbs.html" ,  data)

                elif action == 'addclase':

                    if VALIDA_ABRIR_CLASES and not request.user.has_perm('sga.change_aula'):
                        if not inclassroom_check(request):
                            return HttpResponseRedirect("/?info=Esta funcion solo es accesible desde maquinas autorizadas")

                    if 'm' in request.GET:
                        data['title'] = 'Motivo Apertura de Clase'
                        data['form'] = MotivoApertura(initial={'fecha': datetime.now().strftime("%d-%m-%Y")})
                        data['turno2'] = request.GET['turno']
                        data['profesor2'] = request.GET['profesor']
                        data['prof'] = request.GET['prof']
                        data['aula2'] = request.GET['aula']
                        data['sede2'] = request.GET['sede']
                        data['dia2'] = request.GET['dia']
                        return render(request ,"adm_academica/motivo_apertura.html" ,  data)
                    else:
                        return HttpResponseRedirect("/adm_docentes")

                elif action == 'editclase':
                    b=0
                    if 'justifica' in request.GET:
                        data['justifica'] = 1
                    data['title'] = 'Editar Clase'
                    leccionGrupo = LeccionGrupo.objects.get(pk=request.GET['id'])
                    profesor = leccionGrupo.profesor
                    lecciones = leccionGrupo.lecciones.all()
                    leccionGrupo.abierta = True
                    for leccion in leccionGrupo.lecciones.all():
                        leccion.abierta = True

                    data['profesor'] = profesor
                    data['modulofinanzas'] = MODULO_FINANZAS_ACTIVO
                    data['incluyepago'] = PAGO_ESTRICTO
                    data['incluyedatos'] = DATOS_ESTRICTO
                    data['SEGUIMIENTO_SYLLABUS'] =SEGUIMIENTO_SYLLABUS
                    data['lecciongrupo'] = leccionGrupo
                    data['lecciones'] = lecciones
                    data['ASISTENCIA_APROBAR'] = ASIST_PARA_APROBAR
                    data['usa_modulo_justificacion_ausencias'] = USA_MODULO_JUSTIFICACION_AUSENCIAS
                    data['MODELO_EVALUATIVO'] = [MODELO_EVALUACION, EVALUACION_CASADE]
                    hoy = datetime.now().date()
                    data['inicio'] = hoy
                    data['fin'] = hoy
                    # if RolPago.objects.all().exists():
                    #     rolp = RolPago.objects.all().order_by('-id')[:1].get()
                    #     data['inicio'] = rolp.inicio
                    if  RolPago.objects.filter(inicio__lte = hoy , fechamax__gte =hoy,cerrado=False).order_by('-id').exists():
                        r = RolPago.objects.filter(inicio__lte = hoy , fechamax__gte =hoy,cerrado=False).order_by('-id')[:1].get()
                        if  hoy > r.fechamax :

                            b=1
                        data['inicio'] = r.fin
                        data['fin'] = r.inicio+ timedelta(days=-1)
                    else:
                        if RolPago.objects.filter(cerrado=False ).order_by('-id').exists():
                            r = RolPago.objects.filter(cerrado=False ).order_by('-id')[:1].get()
                            data['inicio'] = r.inicio
                            data['fin'] = r.fin

                    data['b'] = b
                    data['DEFAULT_PASSWORD'] = DEFAULT_PASSWORD
                    if MODELO_EVALUACION == EVALUACION_CASADE:
                        data['modulo_casade']=EVALUACION_CASADE
                    data['form'] = AusenciaJustificadaForm(initial={'fechae': datetime.now().strftime("%d-%m-%Y")})
                    if SeguimientoSyllabus.objects.filter(profesor__id=request.GET['pm']).exists():
                        data['seguimiento'] = SeguimientoSyllabus.objects.filter(profesor__id=request.GET['pm'])[:1].get()
                        data['seguimientotema'] = SeguimientoTema.objects.filter(seguimiento=data['seguimiento'] )
                        data['seguimientodettema'] = SeguimientoDetalleTema.objects.filter(seguimientotema__in= data['seguimientotema'] )
                        data['seguimientosubtema'] = SeguimientoSubTema.objects.filter(seguimientotema__in= data['seguimientotema'])
                        data['seguimientodetsubtema'] = SeguimientoDetalleSubTema.objects.filter(seguimientosubtema__in=data['seguimientosubtema'] )
                        if SeguimientoTema.objects.filter(seguimiento=data['seguimiento'],finalizado=False ).exists():
                            data['tema'] =  SeguimientoTema.objects.filter(seguimiento=data['seguimiento'],finalizado=False ).order_by('tema__orden')[:1].get()
                            if  SeguimientoSubTema.objects.filter(seguimientotema__in= data['seguimientotema'],subtema__tema=data['tema'].tema ,finalizado=False ).exists():
                                st  =  SeguimientoSubTema.objects.filter(seguimientotema__in= data['seguimientotema'],subtema__tema=data['tema'].tema ,finalizado=True ).distinct('subtema').values('subtema')
                                data['subtema'] = SeguimientoSubTema.objects.filter(seguimientotema__in= data['seguimientotema'],subtema__tema=data['tema'].tema ,finalizado=False ).exclude(subtema__in=st).order_by('subtema__numero','-id')[:1].get()
                                v = SeguimientoDetalleSubTema.objects.filter(seguimientosubtema__in=data['seguimientosubtema'], detsubtema__subtema=data['subtema'].subtema,finalizado=True).distinct('detsubtema').values('detsubtema')
                                if SeguimientoDetalleSubTema.objects.filter(seguimientosubtema__in=data['seguimientosubtema'], detsubtema__subtema=data['subtema'].subtema,finalizado=False).exclude(detsubtema__in=v).exists():
                                    data['detsubtema'] = SeguimientoDetalleSubTema.objects.filter(seguimientosubtema__in=data['seguimientosubtema'], detsubtema__subtema=data['subtema'].subtema,finalizado=False).exclude(detsubtema__in=v).order_by('detsubtema__numero','-id')[:1].get()
                    data['motivoccform'] = MotivoCierreClasesForm()
                    return render(request ,"adm_academica/editar_leccionbs.html" ,  data)

                elif action == 'deleteclase':
                    data['title'] = 'Borrar Leccion del Docente'
                    data['lecciongrupo'] = LeccionGrupo.objects.get(pk=request.GET['id'])
                    return render(request ,"adm_academica/borrar_leccionbs.html" ,  data)

                elif action == 'cerrarclase':
                    leccionGrupo = LeccionGrupo.objects.get(pk=request.GET['id'])
                    motivocierre = TipoMotivoCierreClases.objects.get(pk=request.GET['motivo'])
                    f = request.GET['fecha']
                    horaentrada = request.GET['horaentrada']
                    horasalida = request.GET['horasalida']
                    horaentrada2 = time(int(horaentrada[:horaentrada.index(':')]),int(horaentrada[horaentrada.index(':')+1:]))
                    if horasalida:
                        horasalida2 = time(int(horasalida[:horasalida.index(':')]),int(horasalida[horasalida.index(':')+1:]))
                    else:
                        horasalida2 = datetime.now().time()
                    leccionGrupo.abierta = False
                    leccionGrupo.fecha = datetime(int(f[6:]),int(f[3:5]),int(f[:2]))
                    leccionGrupo.horaentrada = horaentrada2
                    leccionGrupo.horasalida = horasalida2
                    #OCastillo 03-07-2023 control de fecha y hora de cierre de clases
                    leccionGrupo.fechasalida=datetime(int(f[6:]),int(f[3:5]),int(f[:2]))
                    leccionGrupo.save()

                    horasturno= ((datetime.combine(leccionGrupo.fecha,leccionGrupo.turno.termina) - datetime.combine (leccionGrupo.fecha, leccionGrupo.turno.comienza)).seconds)/60
                    if leccionGrupo.horaentrada<leccionGrupo.turno.comienza:
                        fechaentrada=datetime.combine(leccionGrupo.fecha,leccionGrupo.turno.comienza)
                    else:
                        fechaentrada=datetime.combine(leccionGrupo.fecha,leccionGrupo.horaentrada)

                    fechasalida=datetime.combine(leccionGrupo.fechasalida,leccionGrupo.horasalida)

                    minutosleccion = ((fechasalida-fechaentrada).seconds)/60
                    minutoscierre=horasturno-minutosleccion
                    leccionGrupo.minutosleccion=minutosleccion
                    leccionGrupo.minutoscierre=minutoscierre
                    leccionGrupo.motivocierre=motivocierre
                    leccionGrupo.fechacierre=datetime.now()
                    leccionGrupo.usuariocierre=request.user
                    leccionGrupo.save()

                    profesor = leccionGrupo.profesor_id
                    for leccion in leccionGrupo.lecciones.all():
                        leccion.abierta = False
                        leccion.fecha = datetime(int(f[6:]),int(f[3:5]),int(f[:2]))
                        leccion.horaentrada = horaentrada2
                        leccion.horasalida = horasalida2
                        leccion.save()

                    #OCastillo 23-08-2022 log en esta accion
                    #Obtain client ip address
                    client_address = ip_client_address(request)
                    # Log de CIERRE DE CLASES
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(leccionGrupo).pk,
                        object_id       = leccionGrupo.id,
                        object_repr     = force_str(leccionGrupo),
                        action_flag     = ADDITION,
                        change_message  = 'Clase cerrada desde Clases y Evaluaciones '+' (' + client_address + ')'  )

                    return HttpResponseRedirect("/adm_docentes?action=clases&id=" + str(profesor))
                elif action=='cronograma':
                    profesor = Profesor.objects.get(pk=request.GET['id'])
                    materias = profesor.materias_imparte().order_by('inicio','nivel__sede')
                    data['periodo'] = request.session['periodo']
                    data['profesor'] = profesor
                    data['materias'] = materias
                    data['centroexterno'] = CENTRO_EXTERNO
                    data['reporte_cronograma_profesor'] = REPORTE_CRONOGRAMA_PROFESOR
                    return render(request ,"adm_academica/cronogramabs.html" ,  data)
                elif action=='horario':
                    profesor = Profesor.objects.get(pk=request.GET['id'])
                    data['disponible'] = LeccionGrupo.objects.filter(profesor=profesor,abierta=True).count()==0
                    if not data['disponible']:
                        data['lecciongrupo'] = LeccionGrupo.objects.get(profesor=profesor,abierta=True)
                    data['title'] = 'Horario de Profesor'
                    data['profesor'] = profesor
                    data['semana'] = ['Lunes','Martes','Miercoles','Jueves','Viernes', 'Sabado', 'Domingo']
                    data['sesiones'] = Sesion.objects.all()
                    hoy = datetime.now().date()
                    clases = Clase.objects.filter(materia__nivel__periodo__activo=True,materia__inicio__lte=hoy, materia__fin__gte=hoy, materia__profesormateria__profesor=profesor, materia__profesormateria__desde__lte=hoy, materia__profesormateria__hasta__gte=hoy).order_by('materia__inicio')
                    clasespm = [(x, x.materia.profesormateria_set.filter(profesor=profesor)[:1].get()) for x in clases]
                    data['clases'] = clasespm
                    data['periodo'] = request.session['periodo']
                    return render(request ,"adm_academica/horariobs.html" ,  data)

                elif action=='segmento':
                    data['nota_aprobar'] = NOTA_PARA_APROBAR
                    materia = Materia.objects.get(pk=request.GET['id'])
                    for m in  MateriaAsignada.objects.filter(materia=materia):
                        if  EvaluacionITB.objects.filter(materiaasignada=m).exists():
                            e = EvaluacionITB.objects.filter(materiaasignada=m)[:1].get()
                            if m.notafinal != e.nota_final():
                               if DEFAULT_PASSWORD=='itb':
                                   if m.materia.fin>convertir_fecha('30-09-2019'):
                                       m.notafinal = e.nota_final_nueva()
                               else:
                                   m.notafinal = e.nota_final()
                               m.save()
                            if DEFAULT_PASSWORD == 'itb':
                                if e.materiaasignada.materia.fin>convertir_fecha('30-09-2019'):
                                    e.actualiza_estado_nueva()
                            else:
                                e.actualiza_estado()

                    data['materia'] = materia
                    data['periodo'] = request.session['periodo']
                    data['profesor'] = Profesor.objects.get(pk=request.GET['profesor'])
                    data['reporte_acta_id'] = REPORTE_ACTA_NOTAS
                    if MODELO_EVALUACION==EVALUACION_IAVQ:
                        periodoevaluaciones = PeriodoEvaluacionesIAVQ.objects.get(periodo=request.session['periodo'])
                        data['periodoeval'] = periodoevaluaciones
                    if MODELO_EVALUACION==EVALUACION_ITB:
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
                        #OCastillo 25-05-2019
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
                    data['puede_cambiar_nota'] = PUEDE_CAMBIAR_CALIFICACIONES
                    data['DEFAULT_PASSWORD']=DEFAULT_PASSWORD
                    data['min_exa']=MIN_EXAMEN
                    data['nota_para_aprobar'] = NOTA_PARA_APROBAR
                    data['asistencia_para_aprobar'] = ASIST_PARA_APROBAR

                    return render(request ,"adm_academica/segmentobs.html" ,  data)

                elif action == 'calificaciones':
                    abiertas=None
                    cerradas = None
                    data = {'title': 'Evaluaciones de Alumnos'}
                    addUserData(request, data)
                    profesor = Profesor.objects.get(pk=request.GET['id'])
                    data['profesor'] = profesor
                    # data['materias'] = profesor.materias_imparte()
                    data['materias'] = profesor.materias_imparte_abiertas()
                    data['nota_aprobar'] = NOTA_PARA_APROBAR
                    data['MODELO_EVALUATIVO'] = [MODELO_EVALUACION, EVALUACION_IAVQ, EVALUACION_ITB, EVALUACION_ITS, EVALUACION_TES, EVALUACION_IGAD, EVALUACION_CASADE,NOTA_PARA_APROBAR]
                    if 'materia' in request.GET:
                        data['materia'] = Materia.objects.get(pk=request.GET['materia'])
                        data['reporte_acta_id'] = REPORTE_ACTA_NOTAS
                        if MODELO_EVALUACION==EVALUACION_IAVQ:
                            periodoevaluaciones = PeriodoEvaluacionesIAVQ.objects.get(periodo=request.session['periodo'])
                            data['periodoeval'] = periodoevaluaciones
                        if MODELO_EVALUACION==EVALUACION_ITB:
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


                        data['listadoprecargado'] = get_template("adm_academica/segmentobs.html").render(RequestContext(request, data))

                    if 'a' in request.GET:
                        abiertas = request.GET['a']
                    if 'c' in request.GET:
                        cerradas = request.GET['c']

                    if abiertas:
                            data['materias'] = profesor.materias_imparte_abiertas()
                    if cerradas:
                            data['materias'] = profesor.materias_imparte_cerradas()

                    data['abiertas'] = abiertas if abiertas else ""
                    data['cerradas'] = cerradas if cerradas else ""
                    return render(request ,"adm_academica/calificacionesbs.html" ,  data)

                elif action=='segmentoasist':
                    materia = Materia.objects.get(pk=request.GET['id'])

                    data['profesor'] = Profesor.objects.get(pk=request.GET['profid'])
                    data['materia'] = materia
                    if "ins_id" in request.GET:
                        data['ins_id'] = request.GET['ins_id']
                        data['inscrip'] = Inscripcion.objects.filter(pk=request.GET['ins_id'])[:1].get()
                        data['especienum']=request.GET['especienum']
                        if 'op' in  request.GET:
                            data['op'] = request.GET['op']
                        data['materiaasignada'] = MateriaAsignada.objects.filter(materia=materia,matricula__inscripcion__id=request.GET['ins_id'])
                        data['totalestmateria'] = MateriaAsignada.objects.filter(materia=materia,matricula__inscripcion__id=request.GET['ins_id']).count()
                        data['absentos']=MateriaAsignada.objects.filter(materia=materia,absentismo=True).count()
                        data['absentosver']=MateriaAsignada.objects.filter(materia=materia,absentismo=True)

                    else:
                        data['materiaasignada']  = materia.asignados_a_esta_materia()
                        data['totalestmateria'] = materia.asignados_a_esta_materia().count()
                        data['absentos']=MateriaAsignada.objects.filter(materia=materia,absentismo=True).count()
                        data['absentosver']=MateriaAsignada.objects.filter(materia=materia,absentismo=True)


                    # data['form'] = AusenciaJustificadaForm(initial={'fechae': datetime.now().strftime("%d-%m-%Y")})
                    data['form'] = AusenciaJustificadaForm()
                    data['usa_modulo_justificacion_ausencias'] = USA_MODULO_JUSTIFICACION_AUSENCIAS
                    data['conduccion']=INSCRIPCION_CONDUCCION
                    return render(request ,"adm_academica/segmentoasist.html" ,  data)

                elif action=='asistencias':
                    try:
                        periodo = request.session['periodo']

                        if 'idmateria' in request.GET:
                            materia = Materia.objects.get(pk=request.GET['idmateria'])
                            data['ins_id'] = request.GET['ins_id']
                            data['materiajus']=materia.id
                            data['op'] = request.GET['op']
                            data['especienum']=request.GET['especienum']
                            data['inscrip'] = Inscripcion.objects.filter(pk=request.GET['ins_id'])[:1].get()
                            profesor = Profesor.objects.get(pk=request.GET['prof_id'])
                        else:
                            profesor = Profesor.objects.get(pk=request.GET['id'])
                            if 'opabs' in  request.GET:
                                data['opabs'] = request.GET['opabs']

                                materiaabstento=Materia.objects.get(pk=request.GET['idmaterias'])
                                data['materiaabs']=materiaabstento.id


                        data['profesor'] = profesor
                        if 'a' in request.GET:
                            data['materias'] = profesor.materias_imparte_abiertas()
                        if 'c' in request.GET:
                            data['materias'] = profesor.materias_imparte_cerradas()

                        return render(request ,"adm_academica/asistenciasbs.html" ,  data)
                    except:
                        return HttpResponseRedirect("/adm_docentes")

                elif action=='editnota':
                    data['title'] = 'Evaluacion del Alumno'
                    materiaasignada = MateriaAsignada.objects.get(pk=request.GET['id'])
                    profesor = Profesor.objects.get(pk=request.GET['p'])
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

                    return render(request ,"adm_academica/editnotabs.html" ,  data)

                elif action=='otrasnotas':
                    data['title'] = 'Evaluacion del Alumno'
                    materiaasignada = MateriaAsignada.objects.get(pk=request.GET['id'])
                    profesor = Profesor.objects.get(pk=request.GET['p'])
                    data['title'] = 'Evaluacion del Alumno'
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
                    return render(request ,"adm_academica/otranotabs.html" ,  data)

                return HttpResponseRedirect("/adm_docentes")
            else:
                try:
                    search = None
                    id = None
                    # abiertas = None
                    # cerradas = None
                    if 's' in request.GET:
                        search = request.GET['s']
                    if 'id' in request.GET:
                        id = request.GET['id']
                    if search:
                        ss = search.split(' ')
                        while '' in ss:
                            ss.remove('')
                        if len(ss)==1:
                            profesores = Profesor.objects.filter(Q(persona__nombres__icontains=search) | Q(persona__apellido1__icontains=search) | Q(persona__apellido2__icontains=search) | Q(persona__cedula__icontains=search) | Q(persona__pasaporte__icontains=search)).order_by('persona__apellido1')
                        else:
                            profesores = Profesor.objects.filter(Q(persona__apellido1__icontains=ss[0]) & Q(persona__apellido2__icontains=ss[1])).order_by('persona__apellido1')
                        # profesores = Profesor.objects.filter(Q(persona__nombres__icontains=search) | Q(persona__apellido1__icontains=search) | Q(persona__apellido2__icontains=search) | Q(persona__cedula__icontains=search) | Q(persona__pasaporte__icontains=search)).order_by('persona__apellido1').exclude(categoria=PROFE_PRACT_CONDUCCION)
                    else:
                        if id:
                            # profesores = Profesor.objects.filter(id=id).exclude(categoria=PROFE_PRACT_CONDUCCION)
                            profesores = Profesor.objects.filter(id=id)
                        else:
                            profesores = Profesor.objects.filter(activo=True).order_by('persona__apellido1')
                            # profesores = Profesor.objects.filter(activo=True).exclude(categoria=PROFE_PRACT_CONDUCCION).order_by('persona__apellido1')
                    paging = Paginator(profesores, 50)
                    p = 1
                    try:
                        if 'page' in request.GET:
                            p = int(request.GET['page'])
                        page = paging.page(p)
                    except:
                        page = paging.page(1)
                    data['paging'] = paging
                    data['page'] = page
                    data['search'] = search if search else ""
                    data['search'] = id if id else ""
                    data['profesores'] = page.object_list
                    data['centroexterno'] = CENTRO_EXTERNO
                    data['form']=MotivoCambioNotaForm()
                    return render(request ,"adm_academica/adm_docentesbs.html" ,  data)
                except Exception as ex:
                    pass


    except Exception as e:
       return HttpResponseRedirect('/adm_docentes')