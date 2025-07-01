from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from django.template.context import RequestContext
import requests
from decorators import secure_module
from settings import REGISTRO_HISTORIA_NOTAS, VALIDAR_ENTRADA_SISTEMA_CON_DEUDA,VALIDA_DEUDA_EXAM_ASIST, DEFAULT_PASSWORD, INSCRIPCION_CONDUCCION, NOTA_ESTADO_EN_CURSO, ID_TIPO_ESPECIE_REG_NOTA, DIAS_ESPECIE, NOTA_ESTADO_DERECHOEXAMEN, EMAIL_ACTIVE, \
     MIN_APROBACION, MAX_APROBACION, MIN_RECUPERACION, MAX_RECUPERACION, MIN_EXAMEN, MAX_EXAMEN, MIN_EXAMENRECUPERACION,PORCIENTO_NOTA1,PORCIENTO_NOTA2,PORCIENTO_NOTA3,\
     PORCIENTO_NOTA4,PORCIENTO_NOTA5,PORCIENTO_RECUPERACION, NOTA_ESTADO_REPROBADO, ESPECIE_ASENTAMIENTO_NOTA, ESPECIE_EXAMEN, ESPECIE_RECUPERACION, ASIST_PARA_APROBAR, \
     NOTA_ESTADO_SUPLETORIO,NOTA_ESTADO_APROBADO,ESPECIE_MEJORAMIENTO, NOTA_PARA_SUPLET, NOTA_PARA_APROBAR,ESPECIE_ASENTAMIENTOCONVENIO_SINVALOR,ESPECIE_ASENTAMIENTOCONVENIO_CONVALOR

from sga.commonviews import addUserData
from sga.forms import EvaluacionObservacionForm,AprobacionCambioNotaForm,MotObsEvidenciaCambioNotaForm, VerMotivoCambioNotaForm
from sga.models import Inscripcion, RecordAcademico, HistoricoNotasITB, HistoricoRecordAcademico, Profesor, Materia, MateriaAsignada, RubroEspecieValorada, Persona,\
     EvaluacionITB, EvaluacionAlcance, CodigoEvaluacion, Coordinacion,MotivoAlcance, ProfesorMateria, Carrera, NivelMalla, TipoEstado
from django.db.models.query_utils import Q
from sga.tasks import plaintext2html,send_html_mail
from datetime import datetime, time, timedelta
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_str
import json
from sga.reportes import elimina_tildes


@login_required(redirect_field_name='ret', login_url='/login')
#@secure_module
def view(request):
    data = {'title': 'Alcance Notas Nivel Cerrado'}
    addUserData(request, data)
    arreglo_notas=[]
    if request.method=='POST':
        if 'action' in request.POST:
            action = request.POST['action']
            obsalcance=''

            if action=='observaciones':
                try:
                    ma = MateriaAsignada.objects.get(pk=request.POST['id'])
                    f = EvaluacionObservacionForm(request.POST)
                    if f.is_valid():
                        if EvaluacionAlcance.objects.filter(materiaasignada=ma).exists():
                            obsalcance = EvaluacionAlcance.objects.filter(materiaasignada=ma)[:1].get()
                            if not obsalcance.observaciones:
                                obsalcance.observaciones = '- ' + elimina_tildes(f.cleaned_data['observaciones']).upper()
                            else:
                                obsalcance.observaciones += plaintext2html(' - '+ elimina_tildes(f.cleaned_data['observaciones']).upper())
                            obsalcance.save()

                            if not obsalcance.nivelmalla:
                                obsalcance.nivelmalla=ma.materia.nivel.nivelmalla
                                obsalcance.save()

                            return HttpResponseRedirect("/alcance_nivelcerrado?id="+str(obsalcance.materiaasignada.materia.id))
                        else:
                            evaalcance=EvaluacionAlcance(materiaasignada=ma,
                                       n1=0,n2=0,n3=0,n4=0,examen=0,recuperacion=0,notafinal=0,
                                       observaciones=f.cleaned_data['observaciones'].upper(),
                                       fecha=datetime.now().date(),
                                       usuario_id=request.user.id)
                            evaalcance.save()
                            return HttpResponseRedirect("/alcance_nivelcerrado?id="+str(evaalcance.materiaasignada.materia.id))

                except Exception as ex:
                    return HttpResponseRedirect("/alcance_nivelcerrado?id="+str(obsalcance.materiaasignada.materia.id))

            elif action=='motivonota':
                try:
                    motivo=MotivoAlcance.objects.get(pk=request.POST['tipomotivo'])
                    ma = MateriaAsignada.objects.get(pk=request.POST['matasignada'])
                    if EvaluacionAlcance.objects.filter(materiaasignada=ma).exists():
                        evaalcance = EvaluacionAlcance.objects.filter(materiaasignada=ma)[:1].get()
                        if not evaalcance.motivo:
                            evaalcance.motivo=motivo
                        else:
                            evaalcance.motivo=motivo
                        evaalcance.save()

                        if not evaalcance.nivelmalla:
                            evaalcance.nivelmalla=ma.materia.nivel.nivelmalla
                            evaalcance.save()

                        datos = {"result": "ok"}
                    else:
                        evaalcance=EvaluacionAlcance(materiaasignada=ma,
                                                     n1=0,n2=0,n3=0,n4=0,examen=0,recuperacion=0,notafinal=0,
                                                     motivo=motivo,
                                                     fecha=datetime.now().date(),
                                                     usuario_id=request.user.id)

                        evaalcance.save()
                        datos = {"result": "ok"}

                    return HttpResponse(json.dumps(datos),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result": "bad", "error": str(ex)}),content_type="application/json")

            elif action=='actualizanotas':
                try:
                    profesor=None
                    fechamax = datetime.now() - timedelta(days=DIAS_ESPECIE)
                    parciales=''
                    promedioanterior=0
                    promedioactual=0
                    persona = Persona.objects.filter(usuario=request.user)[:1].get()
                    if Profesor.objects.filter(persona=persona).exists():
                        profesor=Profesor.objects.filter(persona=persona)[:1].get()

                    materiaasignada = MateriaAsignada.objects.get(pk=request.POST['matasignada'])
                    estudiante = materiaasignada.matricula.inscripcion.persona.nombre_completo_inverso()
                    carrera=materiaasignada.materia.nivel.carrera
                    coordinacion= Coordinacion.objects.filter(carrera=carrera)[:1].get()
                    correo=coordinacion.correo+','+str(persona.emailinst)

                    nota = int(request.POST['nota'])
                    posicion = request.POST['posicion']
                    codigo=0
                    cod=''
                    evalua=EvaluacionITB.objects.filter(materiaasignada=materiaasignada)[:1].get()
                    nota1 = evalua.n1
                    nota2 = evalua.n2
                    nota3 = evalua.n3
                    nota4 = evalua.n4
                    examen = evalua.examen
                    recupera = evalua.recuperacion

                    if EvaluacionAlcance.objects.filter(materiaasignada=materiaasignada).exists():
                        alcance=EvaluacionAlcance.objects.filter(materiaasignada=materiaasignada)[:1].get()
                    else:
                        alcance = EvaluacionAlcance(materiaasignada=materiaasignada,
                        n1=nota1,
                        n2=nota2,
                        n3=nota3,
                        n4=nota4,
                        examen=examen,
                        recuperacion=recupera,
                        fecha=datetime.now().date(),
                        usuario=request.user,
                        nivel=materiaasignada.materia.nivel.nivelmalla)
                        alcance.save()

                    if posicion=='n1':
                        parciales='1'
                        alcance.n1=nota
                        alcance.save()
                        codigo=evalua.cod1
                    elif posicion=='n2':
                        parciales='1'
                        alcance.n2=nota
                        alcance.save()
                        codigo=evalua.cod2
                    elif posicion=='n3':
                        parciales='1'
                        alcance.n3=nota
                        alcance.save()
                        codigo=evalua.cod3
                    elif posicion=='n4':
                        parciales='1'
                        alcance.n4=nota
                        alcance.save()
                        codigo=evalua.cod4

                    #OCastillo 09-02-2024 para actualizar historico y record
                    totalparciales=0
                    if parciales=='1':
                        if HistoricoRecordAcademico.objects.filter(inscripcion=alcance.materiaasignada.matricula.inscripcion, asignatura=alcance.materiaasignada.materia.asignatura, fecha=alcance.materiaasignada.matricula.nivel.fin).exists():
                            h = HistoricoRecordAcademico.objects.filter(inscripcion=alcance.materiaasignada.matricula.inscripcion, asignatura=alcance.materiaasignada.materia.asignatura, fecha=alcance.materiaasignada.matricula.nivel.fin)[:1].get()
                            if HistoricoNotasITB.objects.filter(historico=h).exists() :
                                hn = HistoricoNotasITB.objects.filter(historico=h)[:1].get()
                            else:
                                hn = HistoricoNotasITB(historico=h)
                                hn.save()
                            promedioanterior=h.nota
                            evaluacion = alcance.materiaasignada.evaluacion_itb()
                            hn.cod1 = evaluacion.cod1.id if evaluacion.cod1 else 3
                            hn.cod2 = evaluacion.cod2.id if evaluacion.cod2 else 5
                            hn.cod3 = evaluacion.cod3.id if evaluacion.cod3 else 10
                            hn.cod4 = evaluacion.cod4.id if evaluacion.cod4 else 11
                            hn.save()
                            if alcance.n1>0:
                                hn.n1 = alcance.n1
                            if alcance.n2>0:
                                hn.n2 = alcance.n2
                            if alcance.n3>0:
                                hn.n3 = alcance.n3
                            if alcance.n4>0:
                                hn.n4 = alcance.n4
                            hn.save()
                            totalparciales=(hn.n1+hn.n2+hn.n3+hn.n4+hn.n5)
                            hn.total = totalparciales
                            hn.save()
                            hn.notafinal = hn.total
                            hn.save()
                            promedioactual=hn.notafinal
                            if hn.historico.inscripcion.carrera.online:
                                if hn.total >= NOTA_PARA_SUPLET:
                                    estado = TipoEstado.objects.get(pk=NOTA_ESTADO_SUPLETORIO)
                                else:
                                    estado = TipoEstado.objects.get(pk=NOTA_ESTADO_REPROBADO)
                            else:
                                if hn.total >= NOTA_PARA_SUPLET and h.asistencia >= ASIST_PARA_APROBAR:
                                    estado = TipoEstado.objects.get(pk=NOTA_ESTADO_SUPLETORIO)
                                else:
                                    estado = TipoEstado.objects.get(pk=NOTA_ESTADO_REPROBADO)

                            hn.estado = estado
                            hn.save()

                            h.nota = hn.total
                            h.fecha = alcance.materiaasignada.matricula.nivel.fin
                            h.convalidacion = False
                            h.pendiente = False
                            h.save()
                            if h.inscripcion.carrera.online:
                                if h.nota >= NOTA_PARA_APROBAR:
                                    h.aprobada = True
                                else:
                                    h.aprobada = False
                            else:
                                if h.asistencia>=ASIST_PARA_APROBAR and h.nota >= NOTA_PARA_APROBAR:
                                    h.aprobada = True
                                else:
                                    h.aprobada = False
                            h.save()
                        else:
                            promedioanterior=0
                            h = HistoricoRecordAcademico(inscripcion=alcance.materiaasignada.matricula.inscripcion,
                                                         asignatura=alcance.materiaasignada.materia.asignatura,
                                                         nota=totalparciales, asistencia=ASIST_PARA_APROBAR,
                                                         fecha=alcance.materiaasignada.matricula.nivel.fin, convalidacion=False,pendiente=False)
                            h.save()
                            if h.inscripcion.carrera.online:
                                if h.nota >= NOTA_PARA_APROBAR:
                                    h.aprobada = True
                                else:
                                    h.aprobada = False
                            else:
                                if h.asistencia>=ASIST_PARA_APROBAR and h.nota >= NOTA_PARA_APROBAR:
                                    h.aprobada = True
                                else:
                                    h.aprobada = False
                            h.save()
                            promedioactual=h.nota

                        if RecordAcademico.objects.filter(inscripcion=alcance.materiaasignada.matricula.inscripcion, asignatura=alcance.materiaasignada.materia.asignatura).exists():
                            r = RecordAcademico.objects.filter(inscripcion=alcance.materiaasignada.matricula.inscripcion, asignatura=alcance.materiaasignada.materia.asignatura)[:1].get()
                            r.nota = totalparciales
                            r.fecha =alcance.materiaasignada.matricula.nivel.fin
                            r.convalidacion = False
                            r.pendiente = False
                            r.save()
                            if r.inscripcion.carrera.online:
                                if r.nota >= NOTA_PARA_APROBAR:
                                    r.aprobada = True
                                else:
                                    r.aprobada = False
                            else:
                                if r.asistencia>=ASIST_PARA_APROBAR and r.nota >= NOTA_PARA_APROBAR:
                                    r.aprobada = True
                                else:
                                    r.aprobada = False
                            r.save()
                        else:
                            r = RecordAcademico(inscripcion=alcance.materiaasignada.matricula.inscripcion,
                                                asignatura=alcance.materiaasignada.materia.asignatura,
                                                nota=totalparciales,
                                                asistencia=ASIST_PARA_APROBAR,fecha=alcance.materiaasignada.matricula.nivel.fin,
                                                convalidacion=False,pendiente=False)
                            r.save()

                    if posicion=='n1' or posicion=='n2' or posicion=='n3' or posicion=='n4':
                        # Log de Grabar Notas Parciales
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(alcance).pk,
                            object_id       = alcance.id,
                            object_repr     = force_str(alcance),
                            action_flag     = ADDITION,
                            change_message  = 'Notas Parciales en Nivel Cerrado' + str(alcance.materiaasignada.matricula.inscripcion) )

                    elif posicion=='examen':
                        alcance.examen=nota
                        alcance.aprobado=True
                        alcance.save()
                        total=0
                        estado=''
                        if HistoricoRecordAcademico.objects.filter(inscripcion=alcance.materiaasignada.matricula.inscripcion, asignatura=alcance.materiaasignada.materia.asignatura, fecha=alcance.materiaasignada.matricula.nivel.fin).exists():
                            h = HistoricoRecordAcademico.objects.filter(inscripcion=alcance.materiaasignada.matricula.inscripcion, asignatura=alcance.materiaasignada.materia.asignatura, fecha=alcance.materiaasignada.matricula.nivel.fin)[:1].get()
                            promedioanterior=h.nota
                            if HistoricoNotasITB.objects.filter(historico=h).exists() :
                                hn = HistoricoNotasITB.objects.filter(historico=h)[:1].get()
                                hn.n5 = alcance.examen
                                hn.recup = alcance.recuperacion
                                hn.save()
                                total=(hn.n1+hn.n2+hn.n3+hn.n4+hn.n5)
                                hn.total=total
                                hn.notafinal = total
                                hn.save()

                                h.nota =hn.total
                                h.save()
                                if h.inscripcion.carrera.online:
                                    if h.nota >= NOTA_PARA_APROBAR:
                                        h.aprobada = True
                                        estado = TipoEstado.objects.get(pk=NOTA_ESTADO_APROBADO)
                                    else:
                                        estado = TipoEstado.objects.get(pk=NOTA_ESTADO_REPROBADO)
                                        h.aprobada = False
                                else:
                                    if h.asistencia>=ASIST_PARA_APROBAR and h.nota >= NOTA_PARA_APROBAR:
                                        estado = TipoEstado.objects.get(pk=NOTA_ESTADO_APROBADO)
                                        h.aprobada = True
                                    else:
                                        estado = TipoEstado.objects.get(pk=NOTA_ESTADO_REPROBADO)
                                        h.aprobada = False
                                h.save()
                                hn.estado = estado
                                hn.save()
                                promedioactual=hn.notafinal

                        if RecordAcademico.objects.filter(inscripcion=alcance.materiaasignada.matricula.inscripcion, asignatura=alcance.materiaasignada.materia.asignatura).exists():
                            r = RecordAcademico.objects.filter(inscripcion=alcance.materiaasignada.matricula.inscripcion, asignatura=alcance.materiaasignada.materia.asignatura)[:1].get()
                            r.nota=total
                            r.save()
                            if r.inscripcion.carrera.online:
                                if  r.nota >= NOTA_PARA_APROBAR:
                                    r.aprobada = True
                                else:
                                    r.aprobada = False
                            else:
                                if r.asistencia>=ASIST_PARA_APROBAR and r.nota >= NOTA_PARA_APROBAR:
                                    r.aprobada = True
                                else:
                                    r.aprobada = False
                            r.save()

                        # Log de Grabar Nota Examen Atrasado en nivel cerrado
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(alcance).pk,
                            object_id       = alcance.id,
                            object_repr     = force_str(alcance),
                            action_flag     = ADDITION,
                            change_message  = 'Nota examen atrasado en Nivel Cerrado' + str(alcance.materiaasignada.matricula.inscripcion) )

                        if materiaasignada.ver_asentamiento():
                            especie=RubroEspecieValorada.objects.filter(materia=materiaasignada,autorizado = True,tipoespecie__id__in=[ID_TIPO_ESPECIE_REG_NOTA,ESPECIE_ASENTAMIENTOCONVENIO_SINVALOR,ESPECIE_ASENTAMIENTOCONVENIO_CONVALOR],rubro__fecha__gte=fechamax,disponible=True,rubro__cancelado=True)[:1].get()
                            especie.profesor = profesor
                            especie.f_registro = datetime.now()
                            especie.save()

                    elif posicion=='recuperacion':
                        alcance.recuperacion=nota
                        alcance.aprobado=True
                        alcance.save()
                        estado=''
                        if HistoricoRecordAcademico.objects.filter(inscripcion=alcance.materiaasignada.matricula.inscripcion, asignatura=alcance.materiaasignada.materia.asignatura, fecha=alcance.materiaasignada.matricula.nivel.fin).exists():
                            h = HistoricoRecordAcademico.objects.filter(inscripcion=alcance.materiaasignada.matricula.inscripcion, asignatura=alcance.materiaasignada.materia.asignatura, fecha=alcance.materiaasignada.matricula.nivel.fin)[:1].get()
                            promedioanterior=h.nota
                            if HistoricoNotasITB.objects.filter(historico=h).exists() :
                                hn = HistoricoNotasITB.objects.filter(historico=h)[:1].get()
                                hn.recup = alcance.recuperacion
                                hn.save()

                                if alcance.recuperacion>= hn.total and alcance.recuperacion >= NOTA_PARA_APROBAR:
                                    hn.notafinal=alcance.recuperacion
                                    hn.total=alcance.recuperacion
                                    hn.save()

                                    h.nota=hn.total
                                    h.save()
                                    if h.inscripcion.carrera.online:
                                        if  h.nota >= NOTA_PARA_APROBAR:
                                            estado = TipoEstado.objects.get(pk=NOTA_ESTADO_APROBADO)
                                            h.aprobada = True
                                        else:
                                            estado = TipoEstado.objects.get(pk=NOTA_ESTADO_REPROBADO)
                                            h.aprobada = False
                                    else:
                                        if h.asistencia>=ASIST_PARA_APROBAR and h.nota >= NOTA_PARA_APROBAR:
                                            estado = TipoEstado.objects.get(pk=NOTA_ESTADO_APROBADO)
                                            h.aprobada = True
                                        else:
                                            estado = TipoEstado.objects.get(pk=NOTA_ESTADO_REPROBADO)
                                            h.aprobada = False
                                    h.save()
                                    hn.estado = estado
                                    hn.save()
                                    promedioactual=hn.notafinal
                                else:
                                    total=(hn.n1+hn.n2+hn.n3+hn.n4+hn.n5)
                                    hn.total=total
                                    hn.notafinal = total
                                    hn.save()

                                if RecordAcademico.objects.filter(inscripcion=alcance.materiaasignada.matricula.inscripcion, asignatura=alcance.materiaasignada.materia.asignatura).exists():
                                    r = RecordAcademico.objects.filter(inscripcion=alcance.materiaasignada.matricula.inscripcion, asignatura=alcance.materiaasignada.materia.asignatura)[:1].get()
                                    r.noa=hn.total
                                    r.save()
                                    if r.inscripcion.carrera.online:
                                        if r.nota >= NOTA_PARA_APROBAR:
                                            r.aprobada = True
                                        else:
                                            r.aprobada = False
                                    else:
                                        if r.asistencia>=ASIST_PARA_APROBAR and r.nota >= NOTA_PARA_APROBAR:
                                            r.aprobada = True
                                        else:
                                            r.aprobada = False
                                    r.save()

                        # Log de Grabar Nota Recuperacion o Mejoramiento
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(alcance).pk,
                            object_id       = alcance.id,
                            object_repr     = force_str(alcance),
                            action_flag     = ADDITION,
                            change_message  = 'Recuperacion o mejoramiento en Nivel Cerrado' + str(alcance.materiaasignada.matricula.inscripcion) )

                        # especie=RubroEspecieValorada.objects.filter(materia=materiaasignada,autorizado = True,tipoespecie__id__in=[ID_TIPO_ESPECIE_REG_NOTA,ESPECIE_ASENTAMIENTOCONVENIO_SINVALOR,ESPECIE_ASENTAMIENTOCONVENIO_CONVALOR],rubro__fecha__gte=fechamax,disponible=True,rubro__cancelado=True)[:1].get()
                        # especie.profesor = profesor
                        # especie.f_registro = datetime.now()
                        # especie.save()

                    if not alcance.nivelmalla:
                        alcance.nivelmalla=materiaasignada.materia.nivel.nivelmalla
                        alcance.save()

                    if codigo:
                        cod=CodigoEvaluacion.objects.filter(pk=codigo.id)[:1].get()
                        cod=cod.alias
                    datos = {"result": "ok"}
                    opt='1'
                    contenido='CAMBIO DE NOTAS NIVEL CERRADO: Por medio del presente correo se notifica el cambio de notas en Nivel Cerrado'
                    if EMAIL_ACTIVE:
                        mail_notificacioncambionotas(contenido,'CAMBIO DE NOTAS',correo,carrera,materiaasignada.materia,persona,estudiante,request.user,opt,promedioanterior,promedioactual)

                    return HttpResponse(json.dumps(datos),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result": "bad", "error": str(ex)}),content_type="application/json")

            elif action=='notificacioncorreo':
                try:
                    profesor=''
                    materiaasignada = MateriaAsignada.objects.get(pk=request.POST['matasignada'])
                    carrera=materiaasignada.materia.nivel.carrera
                    coordinacion= Coordinacion.objects.filter(carrera=carrera)[:1].get()
                    if EvaluacionAlcance.objects.filter(materiaasignada=materiaasignada).exists():
                        alcance=EvaluacionAlcance.objects.filter(materiaasignada=materiaasignada)[:1].get()
                        notaparcial=alcance.n1+alcance.n2+alcance.n3+alcance.n4+alcance.examen
                        if notaparcial>0 or alcance.recuperacion>0:
                            alcance.enviado=True
                            alcance.save()
                            profesor=Persona.objects.filter(usuario=alcance.usuario,usuario__is_active=True)[:1].get()
                            correo=coordinacion.correo+','+str(profesor.emailinst)
                            datos = {"result": "ok"}
                            if EMAIL_ACTIVE:
                                alcance.email_notaalcance(profesor,correo)
                                return HttpResponse(json.dumps(datos),content_type="application/json")
                        else:
                            datos = {"result": "error"}
                            return HttpResponse(json.dumps(datos),content_type="application/json")

                except Exception as ex:
                    return HttpResponse(json.dumps({"result": "bad", "error": str(ex)}),content_type="application/json")

            elif action=='soportecambionotas':
                try:
                    profesor=''
                    evidencia=''
                    motivo=MotivoAlcance.objects.filter(id=request.POST['motivo'])[:1].get()
                    observacion=elimina_tildes(request.POST['obs'])
                    materiaasignada = MateriaAsignada.objects.get(pk=request.POST['matasignada'])
                    estudiante=materiaasignada.matricula.inscripcion.persona.nombre_completo_inverso()
                    carrera=materiaasignada.materia.nivel.carrera
                    coordinacion= Coordinacion.objects.filter(carrera=carrera)[:1].get()
                    if EvaluacionAlcance.objects.filter(materiaasignada=materiaasignada).exists():
                        alcance=EvaluacionAlcance.objects.filter(materiaasignada=materiaasignada)[:1].get()
                        alcance.motivo=motivo
                        alcance.observaciones=observacion
                        alcance.usuario=request.user
                        alcance.save()
                    else:
                        evalua=EvaluacionITB.objects.filter(materiaasignada=materiaasignada)[:1].get()
                        nota1 = evalua.n1
                        nota2 = evalua.n2
                        nota3 = evalua.n3
                        nota4 = evalua.n4
                        examen = evalua.examen
                        recupera = evalua.recuperacion
                        alcance=EvaluacionAlcance(materiaasignada=materiaasignada,n1=nota1,n2=nota2,n3=nota3,n4=nota4,
                                                  examen=examen,recuperacion=recupera,notafinal=materiaasignada.notafinal,
                                                  motivo=motivo,observaciones=observacion,usuario=request.user)
                        alcance.save()

                    if 'evidencia' in request.FILES:
                        alcance.evidencia=request.FILES['evidencia']
                        alcance.save()
                        evidencia=alcance.evidencia

                    profesor=Persona.objects.filter(usuario=alcance.usuario,usuario__is_active=True)[:1].get()
                    correo=coordinacion.correo+','+str(profesor.emailinst)
                    datos = {"result": "ok"}
                    opt='2'
                    contenido='CAMBIO DE NOTAS NIVEL CERRADO: Por medio del presente correo se notifica el ingreso de Evidencia previo a realizar el cambio de notas en Nivel Cerrado'
                    if EMAIL_ACTIVE:
                        mail_notificacionevidencia(contenido,'EVIDENCIA CAMBIO DE NOTAS',correo,carrera,materiaasignada.materia,profesor,estudiante,request.user,opt,motivo,observacion,evidencia)

                        return HttpResponse(json.dumps(datos),content_type="application/json")
                    else:
                        datos = {"result": "error"}
                        return HttpResponse(json.dumps(datos),content_type="application/json")

                except Exception as ex:
                    return HttpResponse(json.dumps({"result": "bad", "error": str(ex)}),content_type="application/json")


            elif action=='solicitudasecretaria':
                try:
                    correocoordinacion=None
                    materiaasignada = MateriaAsignada.objects.get(pk=request.POST['matasignada'])
                    estudiante = materiaasignada.matricula.inscripcion.persona.nombre_completo_inverso()
                    carrera=materiaasignada.materia.nivel.carrera
                    #OCastillo 22-04-2022 notificar a la coordinacion de la carrera el cambio solicitado
                    if Coordinacion.objects.filter(carrera=carrera).exists():
                        correocoordinacion = Coordinacion.objects.filter(carrera=carrera)[:1].get()

                    persona = Persona.objects.get(usuario=request.user)
                    profesor=Persona.objects.filter(pk=persona.id,usuario__is_active=True)[:1].get()
                    correo=str(persona.email) + ','+ str(persona.emailinst)+','+str('secretariageneral@bolivariano.edu.ec')+ ','+ str(correocoordinacion.correo)
                    # correo=str(persona.email) + ','+ str(persona.emailinst)+ ','+ str(correocoordinacion.correo)

                    if EvaluacionAlcance.objects.filter(materiaasignada=materiaasignada).exists():
                        evaalcance = EvaluacionAlcance.objects.filter(materiaasignada=materiaasignada)[:1].get()
                        if not evaalcance.usuario:
                            evaalcance.usuario=request.user
                        else:
                            evaalcance.usuario=request.user
                        evaalcance.save()

                        if not evaalcance.nivelmalla:
                            evaalcance.nivelmalla=materiaasignada.materia.nivel.nivelmalla
                            evaalcance.fecha=datetime.now().date()
                            evaalcance.save()
                    else:
                        evaalcance=EvaluacionAlcance(materiaasignada=materiaasignada,
                                                     n1=0,n2=0,n3=0,n4=0,examen=0,recuperacion=0,notafinal=0,
                                                     fecha=datetime.now().date(),usuario_id=request.user.id)

                        evaalcance.save()

                    datos = {"result": "ok"}
                    if EMAIL_ACTIVE:
                        mail_solicitudasecretaria('SOLICITUD A SECRETARIA - > POR MEDIO DEL PRESENTE SOLICITO AUTORIZACION PARA CORRECCION DE NOTAS A ESTUDIANTE ','PERMISO CAMBIO DE NOTAS',correo,carrera,materiaasignada.materia,profesor,estudiante,request.user)
                        return HttpResponse(json.dumps(datos),content_type="application/json")

                except Exception as ex:
                    return HttpResponse(json.dumps({"result": "bad", "error": str(ex)}),content_type="application/json")


    else:
        data = {'title': 'Alcance de Notas Nivel Cerrado'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='observaciones':
                ma = MateriaAsignada.objects.get(pk=request.GET['id'])
                evaluacion = ma.tiene_evaluacionalcance()
                data['evaluacion'] = evaluacion
                data['mat']=ma
                data['form'] = EvaluacionObservacionForm()
                return render(request ,"alcance_nivelcerrado/observacion.html" ,  data)
        else:
            data = {'title': 'Alcance Notas Nivel Cerrado'}
            addUserData(request,data)
            data['periodo'] = request.session['periodo']
            diaactual = datetime.today().date()
            mat=''
            materia=''
            profesor=None
            p=''
            alumnosevaluacion=''
            if Profesor.objects.filter(persona=data['persona']).exists():
                profesor = Profesor.objects.get(persona=data['persona'])
                data['profesor'] = profesor
            fechamax = datetime.now() - timedelta(days=DIAS_ESPECIE)
            if 'id' in request.GET :
                mat= request.GET['id']
                if Profesor.objects.filter(persona=data['persona']).exists():
                    profesor = Profesor.objects.get(persona=data['persona'])
                    data['profesor'] = profesor

                    if Materia.objects.filter(pk=mat,profesormateria__profesor=profesor,cerrado = True,nivel__periodo=data['periodo'],nivel__cerrado=True).exists() or  Materia.objects.filter(pk=mat,profesormateria__profesor_aux=profesor.id,cerrado = True,nivel__periodo=data['periodo'],nivel__cerrado=True).exists() :
                        if Materia.objects.filter(pk=mat,profesormateria__profesor=profesor,cerrado = True,nivel__periodo=data['periodo'],nivel__cerrado=True).exists():
                            materia=Materia.objects.filter(pk=mat,profesormateria__profesor=profesor,cerrado = True,nivel__periodo=data['periodo'],nivel__cerrado=True)[:1].get()
                        else:
                            if Materia.objects.filter(pk=mat,profesormateria__profesor_aux=profesor.id,cerrado = True,nivel__periodo=data['periodo'],nivel__cerrado=True).exists():
                                materia=Materia.objects.filter(pk=mat,profesormateria__profesor_aux=profesor.id,cerrado=True,nivel__periodo=data['periodo'],nivel__cerrado=True)[:1].get()

                        etib = EvaluacionITB.objects.filter(materiaasignada__materia=materia).order_by('cod1','cod2','cod3','cod4')[:1].get()
                        evalumnos = EvaluacionITB.objects.filter(materiaasignada__materia=materia).values('materiaasignada')
                        # evalumnos = EvaluacionITB.objects.filter(materiaasignada__materia=materia).exclude(materiaasignada__retiradomatricula__activo=False,materiaasignada__retiradomatricula__nivel=materia.nivel).values('materiaasignada')
                        asignados=MateriaAsignada.objects.filter(pk__in=evalumnos).order_by('matricula__inscripcion__persona__apellido1')
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
                        data['materia']=materia
                        data['asignados']=asignados
                        data['motivonota']=MotivoAlcance.objects.all().order_by('motivo')
                        data['aprobacionform'] = AprobacionCambioNotaForm()
                        data['evidenciaform'] = MotObsEvidenciaCambioNotaForm()
                        data['vermotivoform'] = VerMotivoCambioNotaForm()

                        data['prof']= p

                    elif Materia.objects.filter(pk=mat,profesormateria__profesor=profesor,cerrado=False,nivel__cerrado=False,nivel__periodo=data['periodo']).exists() or  Materia.objects.filter(pk=mat,profesormateria__profesor_aux=profesor.id,cerrado=False,nivel__cerrado=False,nivel__periodo=data['periodo']).exists() :
                            return HttpResponseRedirect("/?info= MATERIA SE ENCUENTRA ABIERTA")
                    else:
                        return HttpResponseRedirect("/?info= UD NO ES DOCENTE DE LA MATERIA EN CONSULTA")

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

            mat = ProfesorMateria.objects.filter(Q(profesor=profesor,materia__cerrado=True,materia__nivel__cerrado=True,materia__nivel__periodo=data['periodo'])|Q(profesor_aux=profesor.id,materia__cerrado=True,materia__nivel__cerrado=True,materia__nivel__periodo=data['periodo'])).exclude(hasta__lte=diaactual,aceptacion=False).distinct('materia').values('materia')
            #mat = ProfesorMateria.objects.filter(Q(profesor=profesor,materia__cerrado=True,materia__nivel__cerrado=True,materia__nivel__periodo=data['periodo'])|Q(profesor_aux=profesor.id,materia__cerrado=True,materia__nivel__cerrado=True,materia__nivel__periodo=data['periodo'])).distinct('materia').values('materia')
            data['materias']=Materia.objects.filter(id__in=mat)

            return render(request ,"alcance_nivelcerrado/alcance_nivelcerrado.html" ,  data)


def mail_solicitudasecretaria(contenido,asunto,email,carrera,materia,profesor,estudiante,user,opt):
    hoy = datetime.now().today()
    send_html_mail(str(asunto),"emails/email_notificacionalcance_secretaria.html", {'fecha': hoy,"user":user,'contenido': contenido, 'asunto': asunto,'docente':profesor,'materia':materia,'carrera':carrera,'estudiante':estudiante,'opt':opt},email.split(","))

def mail_notificacionevidencia(contenido,asunto,email,carrera,materia,profesor,estudiante,user,opt,motivo,observacion,evidencia):
    hoy = datetime.now().today()
    send_html_mail(str(asunto),"emails/email_notificacionalcance_secretaria.html", {'fecha': hoy,"user":user,'contenido': contenido, 'asunto': asunto,'docente':profesor,'materia':materia,'carrera':carrera,'estudiante':estudiante,'opt3':opt,'motivo':motivo,'obs':observacion,'evidencia':evidencia},email.split(","))

def mail_notificacioncambionotas(contenido,asunto,email,carrera,materia,profesor,estudiante,user,opt,promanterior,promactual):
    hoy = datetime.now().today()
    send_html_mail(str(asunto),"emails/email_notificacionalcance_secretaria.html", {'fecha': hoy,"user":user,'contenido': contenido, 'asunto': asunto,'docente':profesor,'materia':materia,'carrera':carrera,'estudiante':estudiante,'opt':opt,'anterior':promanterior,'actual':promactual},email.split(","))