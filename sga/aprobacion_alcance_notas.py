from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from django.template.context import RequestContext
import requests
from sga.inscripciones import MiPaginador
from decorators import secure_module
from settings import EMAIL_ACTIVE, NOTA_ESTADO_REPROBADO, ASIST_PARA_APROBAR, NOTA_ESTADO_APROBADO, \
    NOTA_PARA_APROBAR, SECRETARIAGENERAL_GROUP_ID

from sga.commonviews import addUserData,ip_client_address
from sga.forms import EvaluacionObservacionForm
from sga.models import RecordAcademico, HistoricoNotasITB, HistoricoRecordAcademico, Profesor, Materia, \
    MateriaAsignada, RubroEspecieValorada, Persona, \
    EvaluacionITB, EvaluacionAlcance, CodigoEvaluacion, Coordinacion, MotivoAlcance, ProfesorMateria, \
    EvaluacionAlcanceHistorial, TipoEstado
from django.db.models.query_utils import Q
from sga.tasks import plaintext2html,send_html_mail
from datetime import datetime, time, timedelta
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_str
import json
from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    if request.method=='POST':
        if 'action' in request.POST:
            action = request.POST['action']

            if action == 'saveAlcanceNivelCerrado':
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
                            change_message  = 'Rechazo de alcance de notas nivel cerrado por parte de secretaria general (' + client_address + ')')

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
                            change_message  = 'Tramite asentamiento en nivel cerrado devuelto al docente por parte de secretaria general (' + client_address + ')')

                    elif tipo == 'aprobado':
                        evaluacion_historial = finalizar_tramite(request, evaluacion_alcance)
                        mensaje = "Se aplicaron los cambios en el record academico del alumno."

                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(evaluacion_historial).pk,
                            object_id       = evaluacion_historial.id,
                            object_repr     = force_str(evaluacion_historial),
                            action_flag     = CHANGE,
                            change_message  = 'Aprobacion de alcance de notas nivel cerrado por parte de secretaria general (' + client_address + ')')

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


    else:
        try:
            data = {'title': 'Aprobacion Alcance Calificaciones'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']
                if action=='observaciones':
                    ma = MateriaAsignada.objects.get(pk=request.GET['id'])
                    evaluacion = ma.tiene_evaluacionalcance()
                    data['evaluacion'] = evaluacion
                    data['mat']=ma
                    data['form'] = EvaluacionObservacionForm()
                    return render(request ,"aprobacion_alcance_notas/observacion.html" ,  data)
            else:

                evaluaciones = EvaluacionAlcance.objects.filter(fecha__gte=datetime.strptime('2024-03-01', "%Y-%m-%d"), enviado=True).order_by('-fecha', 'rubroespecie__serie')
                search = None
                if 's' in request.GET:
                    search = request.GET['s']
                if search:
                    data['search'] = search
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')
                    if len(ss) == 1:
                        evaluaciones = evaluaciones.filter(Q(materiaasignada__materia__asignatura__nombre__icontains=search)|
                                                           Q(materiaasignada__matricula__inscripcion__persona__apellido1__icontains=search)|
                                                           Q(materiaasignada__matricula__inscripcion__persona__nombres__icontains=search)|
                                                           Q(materiaasignada__matricula__inscripcion__persona__cedula__icontains=search)|
                                                           Q(materiaasignada__matricula__inscripcion__persona__pasaporte__icontains=search))
                    else:
                        evaluaciones = evaluaciones.filter(Q(materiaasignada__matricula__inscripcion__persona__apellido1__icontains=ss[0]) & Q(materiaasignada__matricula__inscripcion__persona__apellido1__icontains=ss[1])|
                                                           Q(rubroespecie__profesor__persona__apellido1__icontains=ss[0]) & Q(rubroespecie__profesor__persona__apellido2__icontains=ss[1])|
                                                           Q(materiaasignada__materia__asignatura__nombre__icontains=search))


                if 'tipo' in request.GET:
                    tipo = request.GET['tipo']
                    if tipo == 'finalizadas':
                        especies = RubroEspecieValorada.objects.filter(disponible=False, autorizado=True, rubro__cancelado=True, aplicada=True).exclude(materia=None)
                        evaluaciones = evaluaciones.filter(
                            enviado=True,
                            rubroespecie__id__in=especies.values('id'),
                            materiaasignada__id__in=especies.values('materia')).exclude(fechaaprobacion=None)
                        users_resolucion = User.objects.filter(id__in=evaluaciones.values('usuarioaprueba'), groups__in=[SECRETARIAGENERAL_GROUP_ID]).order_by('username')
                        if 'user' in request.GET:
                            evaluaciones = evaluaciones.filter(usuarioaprueba__id=request.GET['user'])
                        data['finalizadas'] = True
                        data['users_resolucion'] = users_resolucion

                else:
                    especies = RubroEspecieValorada.objects.filter(disponible=True, autorizado=True, rubro__cancelado=True).exclude(aplicada=True).exclude(materia=None)
                    evaluaciones = evaluaciones.filter(
                        enviado=True,
                        aprobado=False,
                        rubroespecie__id__in=especies.values('id'),
                        materiaasignada__id__in=especies.values('materia'))



                paging = MiPaginador(evaluaciones, 20)
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
                data['evaluaciones'] = page.object_list
                # data['evaluaciones'] = evaluaciones


                return render(request ,"aprobacion_alcance_notas/aprobacion_alcancebs.html" ,  data)
        except Exception as e:
            print(e)

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