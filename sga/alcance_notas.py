from django.contrib.auth.decorators import login_required
from django.db.models import Max
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from django.template.context import RequestContext
from decorators import secure_module
from settings import NOTA_ESTADO_EN_CURSO, ID_TIPO_ESPECIE_REG_NOTA, DIAS_ESPECIE, NOTA_ESTADO_DERECHOEXAMEN, EMAIL_ACTIVE, \
     MIN_APROBACION, MAX_APROBACION, MIN_RECUPERACION, MAX_RECUPERACION, MIN_EXAMEN, MAX_EXAMEN, MIN_EXAMENRECUPERACION,PORCIENTO_NOTA1,PORCIENTO_NOTA2,PORCIENTO_NOTA3,\
     PORCIENTO_NOTA4,PORCIENTO_NOTA5,PORCIENTO_RECUPERACION, NOTA_ESTADO_REPROBADO, ASIST_PARA_APROBAR, \
     NOTA_ESTADO_SUPLETORIO,NOTA_ESTADO_APROBADO, NOTA_PARA_SUPLET, NOTA_PARA_APROBAR
from sga.alcance_nivelcerrado import mail_notificacionevidencia

from sga.commonviews import addUserData, ip_client_address
from sga.forms import EvaluacionObservacionForm,AprobacionCambioNotaForm,MotObsEvidenciaCambioNotaForm
from sga.models import RecordAcademico, HistoricoNotasITB, HistoricoRecordAcademico, Profesor, Materia, MateriaAsignada, RubroEspecieValorada, Persona,\
     EvaluacionITB, EvaluacionAlcance, CodigoEvaluacion, Coordinacion,MotivoAlcance, ProfesorMateria, Carrera, NivelMalla, TipoEstado, GestionTramite, EvaluacionAlcanceHistorial, TipoEspecieValorada, SolicitudEstudiante, SolicitudOnline, Rubro, CoordinadorCarreraPeriodo
from django.db.models.query_utils import Q
from sga.tasks import send_html_mail
from datetime import datetime, timedelta
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_str
import json
from sga.reportes import elimina_tildes


@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    data = {'title': 'Registro Academico'}
    addUserData(request, data)
    arreglo_notas=[]
    if request.method=='POST':
        if 'action' in request.POST:
            action = request.POST['action']

            if action=='actualiza_notas':
                try:
                    materia_asignada = MateriaAsignada.objects.get(pk=request.POST['matasignada'])
                    rubro_especie = RubroEspecieValorada.objects.get(pk=request.POST['rubro_especie'])
                    evaluacion_alcance = EvaluacionAlcance.objects.filter(materiaasignada=materia_asignada, rubroespecie=rubro_especie).order_by('-id')[:1].get()
                    setattr(evaluacion_alcance, request.POST['posicion'], int(request.POST['nota']))
                    evaluacion_alcance.notafinal = evaluacion_alcance.recuperacion if evaluacion_alcance.recuperacion>0 else int(evaluacion_alcance.n1)+int(evaluacion_alcance.n2)+int(evaluacion_alcance.n3)+int(evaluacion_alcance.n4)+int(evaluacion_alcance.examen)
                    evaluacion_alcance.save()
                    return HttpResponse(json.dumps({'result':'ok', 'nota_final':evaluacion_alcance.notafinal}),content_type="application/json")
                except Exception as ex:
                    print(ex)
                    return HttpResponse(json.dumps({"result": "bad", "error": str(ex)}),content_type="application/json")

            elif action == 'genera_especie_asentamiento_sinvalor':
                try:
                    materia_asignada = MateriaAsignada.objects.get(pk=request.POST['materia_asignada'])
                    tipo_especie = TipoEspecieValorada.objects.get(pk=ID_TIPO_ESPECIE_REG_NOTA)
                    solicitud_online = SolicitudOnline.objects.get(pk=3)

                    rubro = Rubro(fecha=datetime.now().date(),
                                valor=0,
                                inscripcion=materia_asignada.matricula.inscripcion,
                                cancelado=True,
                                fechavence=datetime.now().date())
                    rubro.save()

                    solicitud_est = SolicitudEstudiante(solicitud=solicitud_online,
                                                        tipoe=tipo_especie,
                                                        inscripcion=materia_asignada.matricula.inscripcion,
                                                        correo=materia_asignada.matricula.inscripcion.persona.emailinst,
                                                        fecha=datetime.now(),
                                                        materia=materia_asignada,
                                                        profesor=Profesor.objects.get(persona=data['persona']),
                                                        observacion="Especie generada por el docente desde modulo Alcance de Notas",
                                                        solicitado=True,
                                                        rubro=rubro)
                    solicitud_est.save()

                    serie = 0
                    valor = RubroEspecieValorada.objects.filter(rubro__fecha__year=rubro.fecha.year).aggregate(Max('serie'))
                    if valor['serie__max']!=None:
                        serie = valor['serie__max']+1

                    rubro_especie = RubroEspecieValorada(rubro=rubro,
                                                         tipoespecie=tipo_especie,
                                                         serie=serie,
                                                         autorizado=False,
                                                         materia=solicitud_est.materia)
                    rubro_especie.save()

                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(rubro_especie).pk,
                        object_id       = rubro_especie.id,
                        object_repr     = force_str(rubro_especie),
                        action_flag     = CHANGE,
                        change_message  = 'Especie generada desde modulo Alcance de Notas (' + client_address + ')')

                    return HttpResponse(json.dumps({"result": "ok"}), content_type="application/json")

                except Exception as e:
                    print(e)
                    return HttpResponse(json.dumps({"result": "bad", "mensaje":str(e)}), content_type="application/json")

            elif action == 'puede_generar_especie':
                materia_asignada = MateriaAsignada.objects.get(pk=request.POST['materia_asignada'])
                asistencia = materia_asignada.asistenciafinal
                if materia_asignada.materia.nivel.cerrado:
                    if RecordAcademico.objects.filter(asignatura=materia_asignada.materia.asignatura, inscripcion=materia_asignada.matricula.inscripcion).exists():
                        asistencia = RecordAcademico.objects.filter(asignatura=materia_asignada.materia.asignatura, inscripcion=materia_asignada.matricula.inscripcion).order_by('-id')[:1].get().asistencia
                if materia_asignada.matricula.inscripcion.tiene_deuda():
                    return HttpResponse(json.dumps({"result": "bad", "mensaje":"Alumno tiene deuda pendiente."}),content_type="application/json")
                elif asistencia < ASIST_PARA_APROBAR and not materia_asignada.materia.nivel.carrera.online:
                    return HttpResponse(json.dumps({"result": "bad", "mensaje":"Alumno no cumple con el minimo de asistencia requerido."}),content_type="application/json")
                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")

            #NIVEL ABIERTO
            if action=='add_motivo_nivel_abierto':
                try:
                    motivo = MotivoAlcance.objects.get(pk=request.POST['tipomotivo'])
                    rubro_especie = RubroEspecieValorada.objects.get(pk=request.POST['rubro_especie'])
                    materia_asignada = MateriaAsignada.objects.get(pk=request.POST['matasignada'])
                    evaluaciones = EvaluacionITB.objects.filter(materiaasignada=materia_asignada)[:1].get()

                    if EvaluacionAlcance.objects.filter(materiaasignada=materia_asignada, rubroespecie=rubro_especie).exists():
                        evaluacion_alcance = EvaluacionAlcance.objects.filter(materiaasignada=materia_asignada, rubroespecie=rubro_especie)[:1].get()
                        evaluacion_alcance.motivo = motivo
                        evaluacion_alcance.observaciones = elimina_tildes(request.POST['observacion'])
                        evaluacion_alcance.usuario = request.user
                        evaluacion_alcance.save()
                    else:
                        nota_final = evaluaciones.recuperacion if evaluaciones.recuperacion>0 else evaluaciones.n1+evaluaciones.n2+evaluaciones.n3+evaluaciones.n4+evaluaciones.examen
                        evaluacion_alcance = EvaluacionAlcance(
                                                                materiaasignada=materia_asignada,
                                                                rubroespecie=rubro_especie,
                                                                n1=evaluaciones.n1,
                                                                n2=evaluaciones.n2,
                                                                n3=evaluaciones.n3,
                                                                n4=evaluaciones.n4,
                                                                examen=evaluaciones.examen,
                                                                recuperacion=evaluaciones.recuperacion,
                                                                notafinal=nota_final,
                                                                motivo=motivo,
                                                                observaciones=elimina_tildes(request.POST['observacion']),
                                                                usuario=request.user,
                                                                fecha=datetime.now().date())
                        evaluacion_alcance.save()
                    return HttpResponse(json.dumps({'result':'ok'}),content_type="application/json")
                except Exception as ex:
                    print(ex)
                    return HttpResponse(json.dumps({"result": "bad", "mensaje": str(ex)}),content_type="application/json")

            elif action == 'verificaCambiosAlcanceNivelAbierto':
                try:
                    materia_asignada = MateriaAsignada.objects.get(pk=request.POST['materia_asignada'])
                    rubro_especie = RubroEspecieValorada.objects.get(pk=request.POST['rubro_especie'])
                    evaluaciones = EvaluacionITB.objects.filter(materiaasignada=materia_asignada).order_by('-id')[:1].get()
                    if EvaluacionAlcance.objects.filter(materiaasignada=materia_asignada,
                                                        rubroespecie=rubro_especie,
                                                        n1=evaluaciones.n1,
                                                        n2=evaluaciones.n2,
                                                        n3=evaluaciones.n3,
                                                        n4=evaluaciones.n4,
                                                        examen=evaluaciones.examen,
                                                        recuperacion=evaluaciones.recuperacion).exists():
                        return HttpResponse(json.dumps({"result":"bad", "mensaje":"Aun no se han realizado cambios en notas parciales, examen o recuperacion. Haga un cambio en e intente nuevamente."}),content_type="application/json")
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as ex:
                    print(ex)
                    return HttpResponse(json.dumps({"result": "bad", "mensaje": str(ex)}),content_type="application/json")

            elif action == 'addAlcanceNivelAbierto':
                try:
                    materia_asignada = MateriaAsignada.objects.get(pk=request.POST['materia_asignada'])
                    rubro_especie = RubroEspecieValorada.objects.get(pk=request.POST['rubro_especie'])
                    evaluacion_alcance = EvaluacionAlcance.objects.filter(materiaasignada=materia_asignada, rubroespecie=rubro_especie)[:1].get()
                    evaluacion = EvaluacionITB.objects.filter(materiaasignada=materia_asignada)[:1].get()

                    materia_asignada.notafinal = evaluacion_alcance.notafinal
                    materia_asignada.save()

                    evaluacion.n1 = evaluacion_alcance.n1
                    evaluacion.n2 = evaluacion_alcance.n2
                    evaluacion.n3 = evaluacion_alcance.n3
                    evaluacion.n4 = evaluacion_alcance.n4
                    evaluacion.examen = evaluacion_alcance.examen
                    evaluacion.recuperacion = evaluacion_alcance.recuperacion
                    evaluacion.actualiza_estado_nueva()
                    evaluacion.save()

                    # CAMBIOS EN GESTION TRAMITE DOCENTE
                    gestion_docente = GestionTramite.objects.filter(tramite=evaluacion_alcance.rubroespecie)[:1].get()
                    gestion_docente.fecharespuesta = datetime.now()
                    gestion_docente.respuesta = "CALIFICACIONES EDITADAS DESDE MODULO ALCANCE DE NOTAS"
                    gestion_docente.finalizado = True
                    gestion_docente.save()

                    # FINALIZAR ESPECIE
                    especie = evaluacion_alcance.rubroespecie
                    especie.disponible = False
                    especie.aplicada = True
                    especie.fechafinaliza = datetime.now()
                    especie.usuario = request.user
                    especie.habilita = False
                    especie.save()

                    # HISTORIAL DE CAMBIOS REALIZADOS POR ESPECIE
                    if EvaluacionAlcanceHistorial.objects.filter(evaluacionalcance=evaluacion_alcance, estado=True).exists():
                        evaluacion_historial = EvaluacionAlcanceHistorial.objects.filter(evaluacionalcance=evaluacion_alcance, estado=True).order_by('-id')[:1].get()
                        evaluacion_historial.n1 = evaluacion_alcance.n1
                        evaluacion_historial.n2 = evaluacion_alcance.n2
                        evaluacion_historial.n3 = evaluacion_alcance.n3
                        evaluacion_historial.n4 = evaluacion_alcance.n4
                        evaluacion_historial.examen = evaluacion_alcance.examen
                        evaluacion_historial.recuperacion = evaluacion_alcance.recuperacion
                        evaluacion_historial.notafinal = evaluacion_alcance.notafinal
                        evaluacion_historial.estado = False
                        evaluacion_historial.usuario_actualiza = request.user #Profesor.objects.get(persona=data['persona'])
                    else:
                        evaluacion_historial = EvaluacionAlcanceHistorial(evaluacionalcance=evaluacion_alcance,
                                                                      n1=evaluacion_alcance.n1,
                                                                      n2=evaluacion_alcance.n2,
                                                                      n3=evaluacion_alcance.n3,
                                                                      n4=evaluacion_alcance.n4,
                                                                      examen=evaluacion_alcance.examen,
                                                                      recuperacion=evaluacion_alcance.recuperacion,
                                                                      notafinal=evaluacion_alcance.notafinal,
                                                                      estado=False,
                                                                      fecha=datetime.now(),
                                                                      usuario_actualiza=request.user)
                    evaluacion_historial.save()

                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(evaluacion_historial).pk,
                        object_id       = evaluacion_historial.id,
                        object_repr     = force_str(evaluacion_historial),
                        action_flag     = CHANGE,
                        change_message  = 'Cambio de Calificaciones desde modulo Alcance de Notas Nivel Abierto por parte del docente (' + client_address + ')')

                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as ex:
                    print(ex)
                    return HttpResponse(json.dumps({"result": "bad", "mensaje": str(ex)}),content_type="application/json")

            # NIVEL CERRADO
            elif action == 'verificaCambiosAlcanceNivelCerrado':
                try:
                    materia_asignada = MateriaAsignada.objects.get(pk=request.POST['materia_asignada'])
                    rubro_especie = RubroEspecieValorada.objects.get(pk=request.POST['rubro_especie'])
                    historico_notas = HistoricoNotasITB.objects.filter(historico__asignatura=materia_asignada.materia.asignatura, historico__inscripcion=materia_asignada.matricula.inscripcion).order_by('-id')[:1].get()
                    if EvaluacionAlcance.objects.filter(materiaasignada=materia_asignada,
                                                        rubroespecie=rubro_especie,
                                                        n1=historico_notas.n1,
                                                        n2=historico_notas.n2,
                                                        n3=historico_notas.n3,
                                                        n4=historico_notas.n4,
                                                        examen=historico_notas.n5,
                                                        recuperacion=historico_notas.recup,
                                                        notafinal=historico_notas.notafinal).exists():
                        return HttpResponse(json.dumps({"result":"bad", "mensaje":"Aun no se han realizado cambios en notas parciales, examen o recuperacion. Haga un cambio en las notas e intente nuevamente."}),content_type="application/json")
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as ex:
                    print(ex)
                    return HttpResponse(json.dumps({"result": "bad", "mensaje": str(ex)}),content_type="application/json")

            elif action == 'addAlcanceNivelCerrado': #Docente guarda los cambios para que el coordinador autorice
                try:
                    materia_asignada = MateriaAsignada.objects.get(pk=request.POST['materia_asignada'])
                    rubro_especie = RubroEspecieValorada.objects.get(pk=request.POST['rubro_especie'])
                    evaluacion_alcance = EvaluacionAlcance.objects.filter(materiaasignada=materia_asignada, rubroespecie=rubro_especie)[:1].get()
                    evaluacion_alcance.enviado = True
                    evaluacion_alcance.save()

                    gestion_docente = GestionTramite.objects.filter(tramite=rubro_especie)[:1].get()
                    gestion_docente.fecharespuesta = datetime.now()
                    gestion_docente.respuesta = "CALIFICACIONES EDITADAS DESDE MODULO ALCANCE DE NOTAS NIVEL CERRADO"
                    gestion_docente.finalizado = True
                    gestion_docente.save()

                    mensaje = 'Notas enviadas al coordinador para su aprobacion. El tramite en bandeja se finalizo de forma atumatica.'
                    if rubro_especie.rubro.valor>0: #Si la especie es generada por el docente (rubro=0), los cambios deben ser aprobados por los coordinadores, caso contrarrio se finaliza el tramite y actualizan las notas.
                        evaluacion_historial = finalizar_tramite(request, evaluacion_alcance) #Funcion para dar de baja especie y actualizar record academico
                        mensaje = "Se aplicaron los cambios en el record academico del alumno."

                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(evaluacion_historial).pk,
                            object_id       = evaluacion_historial.id,
                            object_repr     = force_str(evaluacion_historial),
                            action_flag     = CHANGE,
                            change_message  = 'Actualiza Record Academico desde Alcance de notas nivel cerrado por parte del docente (' + client_address + ')')

                    return HttpResponse(json.dumps({"result":"ok", 'mensaje':mensaje}), content_type="application/json")
                except Exception as e:
                    print(e)
                    return HttpResponse(json.dumps({"result": "bad", "mensaje": str(e)}),content_type="application/json")

            elif action == 'saveAlcanceNivelCerrado': #los cambios los guarda el coordinador
                try:
                    evaluacion_alcance = EvaluacionAlcance.objects.get(pk=request.POST['id'])
                    evaluacion_alcance.motivoaprobacion = request.POST['observacion']
                    evaluacion_alcance.save()
                    tipo = request.POST['tipo']
                    client_address = ip_client_address(request)
                    coordinador = Persona.objects.get(usuario=request.user)
                    docente = Persona.objects.get(usuario=evaluacion_alcance.usuario)
                    mensaje = ''

                    if tipo == 'rechazado':
                        evaluacion_alcance.aprobado = False
                        evaluacion_alcance.usuarioaprueba = request.user
                        evaluacion_alcance.fechaaprobacion = datetime.now().date()
                        evaluacion_alcance.save()

                        especie = evaluacion_alcance.rubroespecie
                        especie.disponible = False
                        especie.aplicada = True
                        especie.fechafinaliza = datetime.now()
                        especie.usuario = request.user
                        especie.habilita = False
                        especie.save()
                        mensaje = "Cambio en alcance de notas se ha rechazado."

                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(evaluacion_alcance).pk,
                            object_id       = evaluacion_alcance.id,
                            object_repr     = force_str(evaluacion_alcance),
                            action_flag     = CHANGE,
                            change_message  = 'Rechazo de alcance de notas nivel cerrado por parte del coordinador (' + client_address + ')')

                    elif tipo == 'devuelto':
                        evaluacion_alcance.enviado = False
                        evaluacion_alcance.save()
                        mensaje = "Se han activado los casilleros para que el docente haga cambio en alcance de notas."

                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(evaluacion_alcance).pk,
                            object_id       = evaluacion_alcance.id,
                            object_repr     = force_str(evaluacion_alcance),
                            action_flag     = CHANGE,
                            change_message  = 'Tramite asentamiento en nivel cerrado devuelto al docente por parte del coordinador (' + client_address + ')')

                    elif tipo == 'aprobado':
                        evaluacion_historial = finalizar_tramite(request, evaluacion_alcance)
                        mensaje = "Se aplicaron los cambios en el record academico del alumno."

                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(evaluacion_historial).pk,
                            object_id       = evaluacion_historial.id,
                            object_repr     = force_str(evaluacion_historial),
                            action_flag     = CHANGE,
                            change_message  = 'Aprobacion de alcance de notas nivel cerrado por parte del coordinador (' + client_address + ')')

                    if EMAIL_ACTIVE:
                        send_html_mail('Notificacion - Alcance de notas nivel cerrado',
                                       'emails/email_alcance_notal.html',
                                       {
                                           'estado':str(tipo).upper(),
                                           'evaluacion':evaluacion_alcance,
                                           'coordinador':coordinador,
                                           'docente':docente
                                       },
                                       [coordinador.emailinst, docente.emailinst]
                        )

                    return HttpResponse(json.dumps({"result":"ok", "mensaje":mensaje}),content_type="application/json")
                except Exception as ex:
                    print(ex)
                    return HttpResponse(json.dumps({"result": "bad", "mensaje": str(ex)}),content_type="application/json")

            elif action=='add_motivo_nivel_cerrado':
                try:
                    motivo = MotivoAlcance.objects.filter(id=request.POST['motivo'])[:1].get()
                    if request.POST['editar'] == 'true':
                        # if EvaluacionAlcance.objects.filter(pk=request.POST['idEvaluacion'], motivo=motivo, observaciones=elimina_tildes(request.POST['obs']), usuario=request.user, evidencia=str(request.FILES['evidencia'])).exists():
                        #     return HttpResponse(json.dumps({"result": "bad", "mensaje":"Aun no se han realizado cambios"}),content_type="application/json")

                        evaluacion_alcance = EvaluacionAlcance.objects.get(pk=request.POST['idEvaluacion'])
                        evaluacion_alcance.motivo = motivo
                        evaluacion_alcance.observaciones = elimina_tildes(request.POST['obs']).upper()
                        evaluacion_alcance.usuario = request.user
                        if 'evidencia' in request.FILES:
                            evaluacion_alcance.evidencia = request.FILES['evidencia']
                        evaluacion_alcance.save()
                        mensaje = "Motivo editado correctamente."
                    else:
                        materia_asignada = MateriaAsignada.objects.get(pk=request.POST['matasignada'])
                        rubro_especie = RubroEspecieValorada.objects.get(pk=request.POST['rubroEspecie'])
                        aprobada = False
                        if materia_asignada.materia.nivel.carrera.online:
                            if materia_asignada.notafinal >= NOTA_PARA_APROBAR:
                                aprobada = True
                        else:
                            if materia_asignada.notafinal >= NOTA_PARA_APROBAR and materia_asignada.asistenciafinal >= ASIST_PARA_APROBAR:
                                aprobada = True
                        if not RecordAcademico.objects.filter(inscripcion=materia_asignada.matricula.inscripcion, asignatura=materia_asignada.materia.asignatura).exists():
                            record_academico = RecordAcademico(inscripcion=materia_asignada.matricula.inscripcion,
                                                               asignatura=materia_asignada.materia.asignatura,
                                                               nota=materia_asignada.notafinal,
                                                               asistencia=materia_asignada.asistenciafinal,
                                                               fecha=datetime.now().date(),
                                                               convalidacion=False,
                                                               aprobada=aprobada,
                                                               pendiente=False)
                            record_academico.save()

                        if not HistoricoNotasITB.objects.filter(historico__asignatura=materia_asignada.materia.asignatura, historico__inscripcion=materia_asignada.matricula.inscripcion).exists():
                            if HistoricoRecordAcademico.objects.filter(inscripcion=materia_asignada.matricula.inscripcion, asignatura=materia_asignada.materia.asignatura).exists():
                                historico_record = HistoricoRecordAcademico.objects.filter(inscripcion=materia_asignada.matricula.inscripcion, asignatura=materia_asignada.materia.asignatura)[:1].get()
                            else:
                                historico_record = HistoricoRecordAcademico(inscripcion=materia_asignada.matricula.inscripcion,
                                                                            asignatura=materia_asignada.materia.asignatura,
                                                                            nota=materia_asignada.notafinal,
                                                                            asistencia=materia_asignada.asistenciafinal,
                                                                            fecha=datetime.now().date(),
                                                                            convalidacion=False,
                                                                            aprobada=True if materia_asignada.notafinal >= NOTA_PARA_APROBAR and materia_asignada.asistenciafinal>=ASIST_PARA_APROBAR else False,
                                                                            pendiente=False)
                                historico_record.save()
                            aprobada = False
                            if materia_asignada.materia.nivel.carrera.online:
                                if materia_asignada.notafinal >= NOTA_PARA_APROBAR:
                                    aprobada = True
                            else:
                                if materia_asignada.notafinal >= NOTA_PARA_APROBAR and materia_asignada.asistenciafinal >= ASIST_PARA_APROBAR:
                                    aprobada = True
                            historico_record.aprobada=aprobada
                            historico_record.save()
                            evaluacion = EvaluacionITB.objects.filter(materiaasignada=materia_asignada)[:1].get()
                            nota_final = evaluacion.recuperacion if evaluacion.recuperacion > 0 else evaluacion.n1 + evaluacion.n2 + evaluacion.n3 + evaluacion.n4 + evaluacion.examen
                            if materia_asignada.materia.nivel.carrera.online:
                                if nota_final >= NOTA_PARA_SUPLET:
                                    estado = TipoEstado.objects.get(pk=NOTA_ESTADO_SUPLETORIO)
                                else:
                                    estado = TipoEstado.objects.get(pk=NOTA_ESTADO_REPROBADO)
                            else:
                                if nota_final >= NOTA_PARA_SUPLET and materia_asignada.asistenciafinal >= ASIST_PARA_APROBAR:
                                    estado = TipoEstado.objects.get(pk=NOTA_ESTADO_SUPLETORIO)
                                else:
                                    estado = TipoEstado.objects.get(pk=NOTA_ESTADO_REPROBADO)

                            historico_notas = HistoricoNotasITB(historico=historico_record,
                                                                cod1=evaluacion.cod1.id,
                                                                cod2=evaluacion.cod2.id,
                                                                cod3=evaluacion.cod3.id,
                                                                cod4=evaluacion.cod4.id,
                                                                n1=evaluacion.n1,
                                                                n2=evaluacion.n2,
                                                                n3=evaluacion.n3,
                                                                n4=evaluacion.n4,
                                                                n5=evaluacion.examen,
                                                                recup=evaluacion.recuperacion,
                                                                notafinal=nota_final,
                                                                estado=estado)
                            historico_notas.save()

                        else:
                            historico_notas = HistoricoNotasITB.objects.filter(historico__asignatura=materia_asignada.materia.asignatura,
                                                                               historico__inscripcion=materia_asignada.matricula.inscripcion).order_by('-id')[:1].get()

                        if EvaluacionAlcance.objects.filter(materiaasignada=materia_asignada, rubroespecie=rubro_especie).exists():
                            evaluacion_alcance = EvaluacionAlcance.objects.filter(materiaasignada=materia_asignada, rubroespecie=rubro_especie)[:1].get()
                            evaluacion_alcance.motivo = motivo
                            evaluacion_alcance.observaciones = elimina_tildes(request.POST['obs']).upper()
                            evaluacion_alcance.usuario = request.user
                            evaluacion_alcance.save()
                        else:
                            evaluacion_alcance = EvaluacionAlcance(
                                                                    materiaasignada=materia_asignada,
                                                                    rubroespecie=rubro_especie,
                                                                    n1=historico_notas.n1,
                                                                    n2=historico_notas.n2,
                                                                    n3=historico_notas.n3,
                                                                    n4=historico_notas.n4,
                                                                    examen=historico_notas.n5,
                                                                    recuperacion=historico_notas.recup,
                                                                    notafinal=historico_notas.notafinal,
                                                                    motivo=motivo,
                                                                    observaciones=elimina_tildes(request.POST['obs']).upper(),
                                                                    usuario=request.user,
                                                                    fecha=datetime.now().date())
                            evaluacion_alcance.save()

                        if 'evidencia' in request.FILES:
                            evaluacion_alcance.evidencia = request.FILES['evidencia']
                            evaluacion_alcance.save()

                        try:
                            coordinacion= Coordinacion.objects.filter(carrera=materia_asignada.materia.nivel.carrera)[:1].get()
                            profesor = Persona.objects.filter(usuario=evaluacion_alcance.usuario, usuario__is_active=True)[:1].get()
                            correo = coordinacion.correo+','+str(profesor.emailinst)
                            datos = {"result": "ok"}
                            opt='2'
                            contenido='CAMBIO DE NOTAS NIVEL CERRADO: Por medio del presente correo se notifica el ingreso de Evidencia previo a realizar el cambio de notas en Nivel Cerrado'
                            if EMAIL_ACTIVE:
                                mail_notificacionevidencia(contenido,
                                                           'EVIDENCIA CAMBIO DE NOTAS',
                                                           correo,
                                                           materia_asignada.materia.nivel.carrera,
                                                           materia_asignada.materia,
                                                           profesor,
                                                           materia_asignada.matricula.inscripcion.persona.nombre_completo_inverso(),
                                                           request.user,
                                                           opt,
                                                           motivo,
                                                           evaluacion_alcance.observaciones,
                                                           evaluacion_alcance.evidencia)
                        except:
                            print('ERROR')
                        mensaje = "La pagina se actualizara. La opcion para asentar notas estara activa."

                    return HttpResponse(json.dumps({"result": "ok", "mensaje":mensaje}),content_type="application/json")
                except Exception as e:
                    print('ERROR add_motivo_nivel_cerrado: '+str(e))
                    return HttpResponse(json.dumps({"result": "bad", "mensaje": str(e)}),content_type="application/json")


    else:
        data = {'title': 'Evaluaciones por Alumnos'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='observaciones':
                ma = MateriaAsignada.objects.get(pk=request.GET['id'])
                evaluacion = ma.tiene_evaluacionalcance()
                data['evaluacion'] = evaluacion
                data['mat']=ma
                data['form'] = EvaluacionObservacionForm()
                return render(request ,"alcance_notas/observacion.html" ,  data)
        else:
            try:
                data = {'title': 'Notas de Alcance'}
                addUserData(request, data)
                data['periodo'] = request.session['periodo']
                materia = ''
                profesor = None
                p=''
                hoy = datetime.now().today()
                coordinador = None

                if Profesor.objects.filter(persona=data['persona']).exists():
                    profesor = Profesor.objects.get(persona=data['persona'])
                    data['profesor'] = profesor
                elif CoordinadorCarreraPeriodo.objects.filter(persona__usuario=request.user).exists():
                    coordinador = Persona.objects.filter(usuario=request.user)[:1].get()
                    data['coordinador'] = coordinador

                if 'id' in request.GET :
                    mat = request.GET['id']

                    if profesor or coordinador:
                            materia = Materia.objects.get(pk=mat)
                            etib = EvaluacionITB.objects.filter(materiaasignada__materia=materia).order_by('cod1','cod2','cod3','cod4')[:1].get()
                            evalumnos = EvaluacionITB.objects.filter(materiaasignada__materia=materia).values('materiaasignada')
                            asignados = MateriaAsignada.objects.filter(pk__in=evalumnos).order_by('matricula__inscripcion__persona__apellido1', 'matricula__inscripcion__persona__apellido2')
                            if etib.cod1:
                                if CodigoEvaluacion.objects.filter(pk=etib.cod1.id).exists():
                                    data['cod1'] = CodigoEvaluacion.objects.get(pk=etib.cod1.id)
                            else:
                                return HttpResponseRedirect("/?info= NO EXISTE CODIGO NOTA PARCIAL 1")

                            if etib.cod2:
                                if CodigoEvaluacion.objects.filter(pk=etib.cod2.id).exists():
                                    data['cod2'] = CodigoEvaluacion.objects.get(pk=etib.cod2.id)
                            else:
                                return HttpResponseRedirect("/?info= NO EXISTE CODIGO NOTA PARCIAL 2")

                            if etib.cod3:
                                if CodigoEvaluacion.objects.filter(pk=etib.cod3.id).exists():
                                    data['cod3'] = CodigoEvaluacion.objects.get(pk=etib.cod3.id)
                            else:
                                return HttpResponseRedirect("/?info= NO EXISTE CODIGO NOTA PARCIAL 3")

                            if etib.cod4:
                                if CodigoEvaluacion.objects.filter(pk=etib.cod4.id).exists():
                                    data['cod4'] = CodigoEvaluacion.objects.get(pk=etib.cod4.id)
                            else:
                                return HttpResponseRedirect("/?info= NO EXISTE CODIGO NOTA PARCIAL 4")
                            data['materia'] = materia
                            data['asignados'] = asignados
                            data['aprobacionform'] = AprobacionCambioNotaForm()
                            data['prof'] = p

                            if 'nivel-cerrado' in request.GET:
                                data['evidenciaform'] = MotObsEvidenciaCambioNotaForm()
                            else:
                                data['obsform'] = EvaluacionObservacionForm()
                                data['motivos_alcance'] = MotivoAlcance.objects.all().order_by('motivo')

                data['encurso']=NOTA_ESTADO_EN_CURSO
                data['examen']=NOTA_ESTADO_DERECHOEXAMEN
                data['reprobado'] = NOTA_ESTADO_REPROBADO
                data['min_aproba']=MIN_APROBACION
                data['max_aproba']=MAX_APROBACION
                data['min_recupera']=MIN_RECUPERACION
                data['max_recupera']=MAX_RECUPERACION
                data['min_exa']=MIN_EXAMEN
                data['max_exa']=MAX_EXAMEN
                data['min_exarecupera']=MIN_EXAMENRECUPERACION
                data['porcnota1']= PORCIENTO_NOTA1
                data['porcnota2']= PORCIENTO_NOTA2
                data['porcnota3']= PORCIENTO_NOTA3
                data['porcnota4']= PORCIENTO_NOTA4
                data['porcnota5']= PORCIENTO_NOTA5
                data['porcrecupera']= PORCIENTO_RECUPERACION
                data['asistencia_aprobar']= ASIST_PARA_APROBAR
                data['recuperacion']= NOTA_ESTADO_SUPLETORIO
                data['aprobado'] = NOTA_ESTADO_APROBADO
                data['carreras'] = Carrera.objects.filter(activo=True,carrera=True).order_by('nombre')
                data['nivelmalla'] = NivelMalla.objects.filter().order_by('nombre')

                data['nivel_cerrado'] = False
                data['nivel_abierto'] = False

                if profesor: #Profesores
                    mat_all = ProfesorMateria.objects.filter(Q(profesor=profesor, materia__cerrado=True,materia__nivel__periodo=data['periodo'])|Q(profesor_aux=profesor.id, materia__cerrado=True,materia__nivel__periodo=data['periodo'])).distinct('materia')
                    if 'nivel-cerrado' in request.GET:
                        data['nivel_cerrado'] = True
                        mat = mat_all.filter(materia__nivel__cerrado=True).values('materia')
                    else:
                        data['nivel_abierto'] = True
                        mat = mat_all.filter(materia__nivel__cerrado=False).values('materia')
                    data['materias'] = Materia.objects.filter(id__in=mat)


                elif CoordinadorCarreraPeriodo.objects.filter(persona__usuario=request.user).exists():  # Coordinadores
                    coordinador_carreras = CoordinadorCarreraPeriodo.objects.filter(persona__usuario=request.user,estado=True)
                    carreras = Carrera.objects.filter(id__in=coordinador_carreras.values('carrera'))
                    mat_all = ProfesorMateria.objects.filter(materia__nivel__carrera__id__in=carreras,
                                                             materia__cerrado=True,
                                                             materia__nivel__periodo=data['periodo'],
                                                             profesor__persona__usuario__is_active=False)

                    if 'aprobacion' in request.GET:
                        data['aprobacion'] = True
                    elif 'nivel-cerrado' in request.GET:
                        data['nivel_cerrado'] = True
                        mat = mat_all.filter(materia__nivel__cerrado=True, materia__asignatura__promedia=True).values('materia')
                        data['materias'] = Materia.objects.filter(id__in=mat)
                    else:
                        data['nivel_abierto'] = True
                        mat = mat_all.filter(materia__nivel__cerrado=False).values('materia')
                        data['materias'] = Materia.objects.filter(id__in=mat)

                    especies = RubroEspecieValorada.objects.filter(disponible=True, autorizado=True, rubro__cancelado=True).exclude(aplicada=True).exclude(materia=None)
                    evaluaciones = EvaluacionAlcance.objects.filter(fecha__gte=datetime.strptime('2024-03-01', "%Y-%m-%d"),
                                                                    enviado=True,
                                                                    aprobado=False,
                                                                    materiaasignada__matricula__inscripcion__carrera__id__in=carreras,
                                                                    materiaasignada__id__in=especies.values('materia')).order_by('-fecha')
                    data['evaluaciones'] = evaluaciones

                elif Coordinacion.objects.filter(persona__usuario=request.user).exists(): #Decanos
                    coordinacion = Coordinacion.objects.filter(persona__usuario=request.user).order_by('-id')[:1].get()
                    carreras = coordinacion.carrera.filter(carrera=True)
                    especies = RubroEspecieValorada.objects.filter(disponible=True, autorizado=True, rubro__cancelado=True).exclude(aplicada=True).exclude(materia=None)
                    evaluaciones = EvaluacionAlcance.objects.filter(fecha__gte=datetime.strptime('2024-03-01', "%Y-%m-%d"),
                                                                    enviado=True,
                                                                    aprobado=False,
                                                                    materiaasignada__matricula__inscripcion__carrera__id__in=carreras,
                                                                    materiaasignada__id__in=especies.values('materia')).order_by('-fecha')
                    data['evaluaciones'] = evaluaciones
                    data['aprobacion'] = True


                data['DIAS_ESPECIE'] = DIAS_ESPECIE

                # evaluaciones = EvaluacionAlcanceHistorial.objects.all().order_by('id')
                # print(evaluaciones.count())
                # lista = []
                # for x in evaluaciones:
                #     if LogEntry.objects.filter(object_id=x.id, change_message__icontains='Cambio de Calificaciones desde modulo Alcance de Notas').exists():
                #         # log = LogEntry.objects.filter(object_id=x.id, change_message__icontains='Cambio de Calificaciones desde modulo Alcance de Notas')[:1].get()
                #         record = RecordAcademico.objects.filter(
                #                 asignatura=x.evaluacionalcance.materiaasignada.materia.asignatura,
                #                 inscripcion=x.evaluacionalcance.materiaasignada.matricula.inscripcion)[:1].get()
                #         if record.nota >= NOTA_PARA_APROBAR and record.asistencia >= ASIST_PARA_APROBAR:
                #             # estado = TipoEstado.objects.get(pk=NOTA_ESTADO_APROBADO)
                #             lista.append(record.id)
                #             record.aprobada = True
                #             record.save()
                # print(lista)

                # for x in evaluaciones:
                #     if LogEntry.objects.filter(object_id=x.id, change_message__icontains='Cambio de Calificaciones desde modulo Alcance de Notas').exists():
                #         log = LogEntry.objects.filter(object_id=x.id, change_message__icontains='Cambio de Calificaciones desde modulo Alcance de Notas')[:1].get()
                #         historico = HistoricoNotasITB.objects.filter\
                #                 (
                #                  historico__asignatura=x.evaluacionalcance.materiaasignada.materia.asignatura,
                #                  historico__inscripcion=x.evaluacionalcance.materiaasignada.matricula.inscripcion)[:1].get()
                #         if historico.total >= NOTA_PARA_APROBAR and historico.historico.asistencia >= ASIST_PARA_APROBAR:
                #             estado = TipoEstado.objects.get(pk=NOTA_ESTADO_APROBADO)
                #             historico.estado = estado
                #             historico.save()

                return render(request ,"alcance_notas/alcancebs.html" ,  data)
            except Exception as e:
                print(e)
                return HttpResponseRedirect('/')

def finalizar_tramite(request, evaluacion_alcance):
    evaluacion_alcance.aprobado = True
    evaluacion_alcance.usuarioaprueba = request.user
    evaluacion_alcance.fechaaprobacion = datetime.now().date()
    evaluacion_alcance.save()

    historico_notas = HistoricoNotasITB.objects.filter(historico__asignatura=evaluacion_alcance.materiaasignada.materia.asignatura,
                                                       historico__inscripcion=evaluacion_alcance.materiaasignada.matricula.inscripcion).order_by('-id')[:1].get()
    # CAMBIOS EN HISTORICO NOTAS ITB
    historico_notas.n1 = evaluacion_alcance.n1 if evaluacion_alcance.n1 > 0 else historico_notas.n1
    historico_notas.n2 = evaluacion_alcance.n2 if evaluacion_alcance.n2 > 0 else historico_notas.n2
    historico_notas.n3 = evaluacion_alcance.n3 if evaluacion_alcance.n3 > 0 else historico_notas.n3
    historico_notas.n4 = evaluacion_alcance.n4 if evaluacion_alcance.n4 > 0 else historico_notas.n4
    historico_notas.n5 = evaluacion_alcance.examen if evaluacion_alcance.examen > 0 else  historico_notas.n5
    historico_notas.recup = evaluacion_alcance.recuperacion if evaluacion_alcance.recuperacion > 0 else historico_notas.recup

    total_parciales = historico_notas.n1 + historico_notas.n2 + historico_notas.n3 + historico_notas.n4 + historico_notas.n5
    historico_notas.total = evaluacion_alcance.recuperacion if evaluacion_alcance.recuperacion > 0 else total_parciales
    historico_notas.notafinal = historico_notas.total

    evaluacion_alcance.notafinal = historico_notas.total
    evaluacion_alcance.save()

    if evaluacion_alcance.materiaasignada.materia.nivel.carrera.online:
        if historico_notas.total >= NOTA_PARA_APROBAR:
            estado = TipoEstado.objects.get(pk=NOTA_ESTADO_APROBADO)
        else:
            estado = TipoEstado.objects.get(pk=NOTA_ESTADO_REPROBADO)
    else:
        if historico_notas.total >= NOTA_PARA_APROBAR and historico_notas.historico.asistencia >= ASIST_PARA_APROBAR:
            estado = TipoEstado.objects.get(pk=NOTA_ESTADO_APROBADO)
        else:
            estado = TipoEstado.objects.get(pk=NOTA_ESTADO_REPROBADO)

    historico_notas.estado = estado
    historico_notas.save()

    # CAMBIOS EN HISTORICO RECORD ACADEMICO
    historico_notas.historico.nota = historico_notas.total
    historico_notas.historico.fecha = evaluacion_alcance.materiaasignada.matricula.nivel.fin
    historico_notas.historico.convalidacion = False
    historico_notas.historico.pendiente = False

    if historico_notas.historico.asistencia >= ASIST_PARA_APROBAR and historico_notas.historico.nota >= NOTA_PARA_APROBAR:
        historico_notas.historico.aprobada = True
    else:
        historico_notas.historico.aprobada = False
    historico_notas.historico.save()

    # CAMBIOS EN RECORD ACADEMICO
    record_academico = RecordAcademico.objects.filter(inscripcion=evaluacion_alcance.materiaasignada.matricula.inscripcion,
                                                      asignatura=evaluacion_alcance.materiaasignada.materia.asignatura)[:1].get()
    record_academico.nota = historico_notas.total
    record_academico.fecha = evaluacion_alcance.materiaasignada.matricula.nivel.fin
    record_academico.convalidacion = False
    record_academico.pendiente = False
    record_academico.aprobada = historico_notas.historico.aprobada
    record_academico.save()

    # CAMBIOS EN GESTION TRAMITE DOCENTE
    # gestion_docente = GestionTramite.objects.filter(tramite=evaluacion_alcance.rubroespecie)[:1].get()
    # gestion_docente.fecharespuesta = datetime.now()
    # gestion_docente.respuesta = "CALIFICACIONES EDITADAS DESDE MODULO ALCANCE DE NOTAS"
    # gestion_docente.finalizado = True
    # gestion_docente.save()

    # FINALIZAR ESPECIE
    especie = evaluacion_alcance.rubroespecie
    especie.disponible = False
    especie.aplicada = True
    especie.fechafinaliza = datetime.now()
    especie.usuario = request.user
    especie.habilita = False
    especie.save()

    # HISTORIAL DE CAMBIOS REALIZADOS POR ESPECIE
    if EvaluacionAlcanceHistorial.objects.filter(evaluacionalcance=evaluacion_alcance, estado=True).exists():
        evaluacion_historial = EvaluacionAlcanceHistorial.objects.filter(evaluacionalcance=evaluacion_alcance, estado=True).order_by('-id')[:1].get()
        evaluacion_historial.n1 = evaluacion_alcance.n1
        evaluacion_historial.n2 = evaluacion_alcance.n2
        evaluacion_historial.n3 = evaluacion_alcance.n3
        evaluacion_historial.n4 = evaluacion_alcance.n4
        evaluacion_historial.examen = evaluacion_alcance.examen
        evaluacion_historial.recuperacion = evaluacion_alcance.recuperacion
        evaluacion_historial.notafinal = evaluacion_alcance.notafinal
        evaluacion_historial.estado = False
        evaluacion_historial.usuario_actualiza = request.user #Profesor.objects.get(persona=data['persona'])
    else:
        evaluacion_historial = EvaluacionAlcanceHistorial(evaluacionalcance=evaluacion_alcance,
                                                      n1=evaluacion_alcance.n1,
                                                      n2=evaluacion_alcance.n2,
                                                      n3=evaluacion_alcance.n3,
                                                      n4=evaluacion_alcance.n4,
                                                      examen=evaluacion_alcance.examen,
                                                      recuperacion=evaluacion_alcance.recuperacion,
                                                      notafinal=evaluacion_alcance.notafinal,
                                                      estado=False,
                                                      usuario_actualiza=request.user,
                                                      fecha=datetime.now().date())
    evaluacion_historial.save()
    return evaluacion_historial