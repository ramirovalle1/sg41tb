from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from django.template.context import RequestContext
import requests
from decorators import secure_module
from settings import REGISTRO_HISTORIA_NOTAS, VALIDAR_ENTRADA_SISTEMA_CON_DEUDA,VALIDA_DEUDA_EXAM_ASIST, DEFAULT_PASSWORD, INSCRIPCION_CONDUCCION, NOTA_ESTADO_EN_CURSO, \
     ID_TIPO_ESPECIE_REG_NOTA, DIAS_ESPECIE, NOTA_ESTADO_DERECHOEXAMEN, EMAIL_ACTIVE,MIN_APROBACION, MAX_APROBACION, MIN_RECUPERACION, MAX_RECUPERACION, MIN_EXAMEN, MAX_EXAMEN,\
     MIN_EXAMENRECUPERACION,PORCIENTO_NOTA1,PORCIENTO_NOTA2,PORCIENTO_NOTA3,PORCIENTO_NOTA4,PORCIENTO_NOTA5,PORCIENTO_RECUPERACION, NOTA_ESTADO_REPROBADO, ESPECIE_ASENTAMIENTO_NOTA, \
     ESPECIE_EXAMEN, ESPECIE_RECUPERACION, ASIST_PARA_APROBAR,ESPECIE_MEJORAMIENTO,NOTA_PARA_APROBAR,NOTA_ESTADO_APROBADO,\
     NOTA_ESTADO_REPROBADO,NOTA_ESTADO_SUPLETORIO,NOTA_PARA_SUPLET

from sga.commonviews import addUserData,ip_client_address
from sga.forms import EvaluacionObservacionForm,AprobacionCambioNotaForm
from sga.models import Inscripcion, RecordAcademico, HistoricoNotasITB, HistoricoRecordAcademico, Profesor, Materia, MateriaAsignada, RubroEspecieValorada, Persona,\
     EvaluacionITB, EvaluacionAlcance, CodigoEvaluacion, Coordinacion,MotivoAlcance, ProfesorMateria,TipoEstado
from django.db.models.query_utils import Q
from sga.tasks import plaintext2html,send_html_mail
from datetime import datetime, time, timedelta
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_str
import json
from sga.reportes import elimina_tildes


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




@login_required(redirect_field_name='ret', login_url='/login')
#@secure_module
def view(request):
    data = {'title': 'Registro Academico'}
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
                        if EvaluacionAlcance.objects.filter(materiaasignada=ma).exclude(nivelmalla=None).exists():
                            obsalcance = EvaluacionAlcance.objects.filter(materiaasignada=ma).exclude(nivelmalla=None)[:1].get()
                            if not obsalcance.observaciones:
                                obsalcance.observaciones = '- ' + elimina_tildes(f.cleaned_data['observaciones']).upper()
                            else:
                                obsalcance.observaciones += plaintext2html(' - '+ elimina_tildes(f.cleaned_data['observaciones']).upper())
                            obsalcance.save()
                            return HttpResponseRedirect("/aprobacion_nivelcerrado?id="+str(obsalcance.materiaasignada.materia.id))
                        else:
                            evaalcance=EvaluacionAlcance(materiaasignada=ma,
                                       n1=0,n2=0,n3=0,n4=0,examen=0,recuperacion=0,notafinal=0,
                                       observaciones=f.cleaned_data['observaciones'].upper(),
                                       fecha=datetime.now().date(),
                                       usuario_id=request.user.id)
                            evaalcance.save()
                            return HttpResponseRedirect("/aprobacion_nivelcerrado?id="+str(evaalcance.materiaasignada.materia.id))

                except Exception as ex:
                    return HttpResponseRedirect("/aprobacion_alcance_notas?id="+str(obsalcance.materiaasignada.materia.id))

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
                    profesor=''
                    materiaasignada = MateriaAsignada.objects.get(pk=request.POST['matasignada'])
                    carrera=materiaasignada.materia.nivel.carrera
                    coordinacion= Coordinacion.objects.filter(carrera=carrera)[:1].get()
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

                    if materiaasignada.ver_especie():
                        fechamax = datetime.now() - timedelta(days=DIAS_ESPECIE)
                        persona = Persona.objects.filter(usuario=request.user)[:1].get()
                        if Profesor.objects.filter(persona=persona).exists():
                            profesor = Profesor.objects.filter(persona=persona)[:1].get()
                        if posicion=='n1' or posicion=='n2' or posicion=='n3' or posicion=='n4':
                            if RubroEspecieValorada.objects.filter(materia=materiaasignada,autorizado = True,fecha__gte=fechamax).exists():
                                if materiaasignada.ver_especie():
                                    rb_asentamiento=RubroEspecieValorada.objects.filter(materia=materiaasignada,autorizado = True,tipoespecie__id__in= [ESPECIE_ASENTAMIENTO_NOTA,ID_TIPO_ESPECIE_REG_NOTA],fecha__gte=fechamax)[:1].get()
                                    rb_asentamiento.profesor = profesor
                                    rb_asentamiento.f_registro = datetime.now()
                                    rb_asentamiento.save()
                                    # Log de Grabar Notas
                                    LogEntry.objects.log_action(
                                        user_id         = request.user.pk,
                                        content_type_id = ContentType.objects.get_for_model(rb_asentamiento).pk,
                                        object_id       = rb_asentamiento.id,
                                        object_repr     = force_str(rb_asentamiento),
                                        action_flag     = ADDITION,
                                        change_message  = 'Aplica especie asentamiento de notas' + str(materiaasignada.matricula.inscripcion) )

                        if posicion=='examen':
                            if materiaasignada.ver_examen():
                                rb_examen=RubroEspecieValorada.objects.filter(materia=materiaasignada,autorizado = True,tipoespecie__id=ESPECIE_EXAMEN,fecha__gte=fechamax)[:1].get()
                                rb_examen.profesor = profesor
                                rb_examen.f_registro = datetime.now()
                                rb_examen.save()
                                # Log de Grabar Nota Examen Atrasado
                                LogEntry.objects.log_action(
                                    user_id         = request.user.pk,
                                    content_type_id = ContentType.objects.get_for_model(rb_examen).pk,
                                    object_id       = rb_examen.id,
                                    object_repr     = force_str(rb_examen),
                                    action_flag     = ADDITION,
                                    change_message  = 'Aplica especie examen atrasado' + str(materiaasignada.matricula.inscripcion) )

                        if posicion=='recuperacion':
                            if materiaasignada.ver_recuperacion()or materiaasignada.ver_mejoramiento():
                                rb_recuperacion=RubroEspecieValorada.objects.filter(materia=materiaasignada,autorizado = True,tipoespecie__in=[ESPECIE_RECUPERACION,ESPECIE_MEJORAMIENTO],fecha__gte=fechamax)[:1].get()
                                rb_recuperacion.profesor = profesor
                                rb_recuperacion.f_registro = datetime.now()
                                rb_recuperacion.save()
                                # Log de Grabar Nota Recuperacion
                                LogEntry.objects.log_action(
                                    user_id         = request.user.pk,
                                    content_type_id = ContentType.objects.get_for_model(rb_recuperacion).pk,
                                    object_id       = rb_recuperacion.id,
                                    object_repr     = force_str(rb_recuperacion),
                                    action_flag     = ADDITION,
                                    change_message  = 'Aplica especie recuperacion o mejoramiento' + str(materiaasignada.matricula.inscripcion) )

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
                            usuario=request.user)
                            alcance.save()

                        if posicion=='n1':
                            alcance.n1=nota
                            alcance.save()
                            codigo=evalua.cod1
                        elif posicion=='n2':
                            alcance.n2=nota
                            alcance.save()
                            codigo=evalua.cod2
                        elif posicion=='n3':
                            alcance.n3=nota
                            alcance.save()
                            codigo=evalua.cod3
                        elif posicion=='n4':
                            alcance.n4=nota
                            alcance.save()
                            codigo=evalua.cod4
                        elif posicion=='examen':
                            alcance.examen=nota
                            alcance.save()
                        elif posicion=='recuperacion':
                            alcance.recuperacion=nota
                            alcance.save()

                        if alcance:
                             alcance.actualiza_estado_alcance()
                             alcance.nota_total_alcance()
                        if codigo:
                            cod=CodigoEvaluacion.objects.filter(pk=codigo.id)[:1].get()
                            cod=cod.alias
                        datos = {"result": "ok"}
                        if EMAIL_ACTIVE:
                            evalua.email_notaalcance(profesor,posicion,nota,coordinacion.correo,'01',cod)

                        return HttpResponse(json.dumps(datos),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result": "bad", "error": str(ex)}),content_type="application/json")

            elif action=='aprobacionnota':
                try:
                    hoy = datetime.now().today()
                    profesor=''
                    estado_aprobacion=str(request.POST['estado'])
                    parciales = str(request.POST['parciales'])
                    nexamen = str(request.POST['examen'])
                    nrecuperacion = str(request.POST['recuperacion'])
                    if EvaluacionAlcance.objects.filter(materiaasignada=request.POST['matasignada']).exclude(nivelmalla=None).exists():
                        alcance=EvaluacionAlcance.objects.filter(materiaasignada=request.POST['matasignada']).exclude(nivelmalla=None)[:1].get()
                        materiaasignada = MateriaAsignada.objects.get(pk=alcance.materiaasignada.id)
                        materia=elimina_tildes(materiaasignada.materia.asignatura)
                        carrera=materiaasignada.materia.nivel.carrera
                        coordinacion= Coordinacion.objects.filter(carrera=carrera)[:1].get()
                        personarespon = Persona.objects.filter(usuario=request.user)[:1].get()
                        personarespon=elimina_tildes(personarespon.nombre_completo_inverso())
                        correoinstitucional=alcance.materiaasignada.matricula.inscripcion.persona.emailinst
                        correopersonal=alcance.materiaasignada.matricula.inscripcion.persona.email
                        datos={}
                        if estado_aprobacion=='0':
                            estudiante=str(materiaasignada.matricula.inscripcion)
                            alcance.aprobado=False
                            alcance.fechaaprobacion=datetime.now().date()
                            alcance.usuarioaprueba=request.user
                            alcance.motivoaprobacion=request.POST['obssecretaria'].upper()
                            alcance.save()
                            profesor=Persona.objects.filter(usuario=alcance.usuario,usuario__is_active=True)[:1].get()
                            docente=elimina_tildes(profesor.nombre_completo_inverso())
                            correo=coordinacion.correo+','+str(profesor.emailinst)
                            if EMAIL_ACTIVE:
                                send_html_mail("DESAPROBACION CAMBIO NOTAS",
                                "emails/correo_desaprobacionnota.html", {'contenido': "CAMBIO DE NOTAS NO HA SIDO APROBADO", 'obs':request.POST['obssecretaria'], 'estudiante': estudiante,'materia':materia,'docente':docente,'personarespon':personarespon, 'fecha': hoy},correo.split())
                            datos = {"result": "ok"}
                            return HttpResponse(json.dumps(datos),content_type="application/json")
                        else:
                            #aquiiiii grabar notas en record e historico
                            fechamax = datetime.now() - timedelta(days=DIAS_ESPECIE)
                            estado=None
                            if parciales=='1':
                                totalparciales=0
                                if HistoricoRecordAcademico.objects.filter(inscripcion=alcance.materiaasignada.matricula.inscripcion, asignatura=alcance.materiaasignada.materia.asignatura, fecha=alcance.materiaasignada.matricula.nivel.fin).exists():
                                    h = HistoricoRecordAcademico.objects.filter(inscripcion=alcance.materiaasignada.matricula.inscripcion, asignatura=alcance.materiaasignada.materia.asignatura, fecha=alcance.materiaasignada.matricula.nivel.fin)[:1].get()
                                    if HistoricoNotasITB.objects.filter(historico=h).exists() :
                                        hn = HistoricoNotasITB.objects.filter(historico=h)[:1].get()
                                    else:
                                        hn = HistoricoNotasITB(historico=h)
                                        hn.save()

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
                                    if hn.historico.inscripcion.carrera.online:
                                        if hn.total >= NOTA_PARA_SUPLET:
                                            estado=TipoEstado.objects.get(pk=NOTA_ESTADO_SUPLETORIO)
                                        else:
                                            estado=TipoEstado.objects.get(pk=NOTA_ESTADO_REPROBADO)
                                    else:
                                        if hn.total >= NOTA_PARA_SUPLET and h.asistencia>=ASIST_PARA_APROBAR:
                                            estado=TipoEstado.objects.get(pk=NOTA_ESTADO_SUPLETORIO)
                                        else:
                                            estado=TipoEstado.objects.get(pk=NOTA_ESTADO_REPROBADO)

                                    hn.estado = estado
                                    hn.save()

                                    h.nota = hn.total
                                    h.fecha = alcance.materiaasignada.matricula.nivel.fin
                                    h.convalidacion = False
                                    h.pendiente = False
                                    h.save()
                                    if h.asistencia >= ASIST_PARA_APROBAR and h.nota >= NOTA_PARA_APROBAR and not h.inscripcion.carrera.online or h.nota >= NOTA_PARA_APROBAR and h.inscripcion.carrera.online:
                                        h.aprobada = True
                                    else:
                                        h.aprobada = False
                                    h.save()
                                else:
                                    h = HistoricoRecordAcademico(inscripcion=alcance.materiaasignada.matricula.inscripcion,
                                                                 asignatura=alcance.materiaasignada.materia.asignatura,
                                                                 nota=totalparciales, asistencia=ASIST_PARA_APROBAR,
                                                                 fecha=alcance.materiaasignada.matricula.nivel.fin, convalidacion=False,pendiente=False)
                                    h.save()
                                    if h.asistencia >= ASIST_PARA_APROBAR and h.nota >= NOTA_PARA_APROBAR and not h.inscripcion.carrera.online or h.nota >= NOTA_PARA_APROBAR and h.inscripcion.carrera.online:
                                        h.aprobada = True
                                    else:
                                        h.aprobada = False
                                    h.save()

                                if RecordAcademico.objects.filter(inscripcion=alcance.materiaasignada.matricula.inscripcion, asignatura=alcance.materiaasignada.materia.asignatura).exists():
                                    r = RecordAcademico.objects.filter(inscripcion=alcance.materiaasignada.matricula.inscripcion, asignatura=alcance.materiaasignada.materia.asignatura)[:1].get()
                                    r.nota = totalparciales
                                    r.fecha =alcance.materiaasignada.matricula.nivel.fin
                                    r.convalidacion = False
                                    r.pendiente = False
                                    r.save()
                                    if r.asistencia >= ASIST_PARA_APROBAR and r.nota >= NOTA_PARA_APROBAR and not r.inscripcion.carrera.online or r.nota >= NOTA_PARA_APROBAR and r.inscripcion.carrera.online:
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

                                alcance.aprobado=True
                                alcance.fechaaprobacion=datetime.now().date()
                                alcance.motivoaprobacion=request.POST['obssecretaria'].upper()
                                alcance.usuarioaprueba=request.user
                                alcance.estado=estado
                                alcance.save()
                                #OCastillo 13-09-2022 se incluyen especies en nivel cerrado
                                if RubroEspecieValorada.objects.filter(materia=materiaasignada,rubro__fecha__gte=fechamax,autorizado=True,disponible=True,tipoespecie=ID_TIPO_ESPECIE_REG_NOTA).exists():
                                    especie = RubroEspecieValorada.objects.filter(materia=materiaasignada,rubro__fecha__gte=fechamax,autorizado=True,disponible=True,tipoespecie=ID_TIPO_ESPECIE_REG_NOTA)[:1].get()
                                    especie.disponible=False
                                    especie.aplicada = True
                                    especie.fechafinaliza=datetime.now()
                                    especie.usuario=request.user
                                    especie.save()

                                # Log de Grabar Aprobacion Notas Parciales
                                LogEntry.objects.log_action(
                                    user_id         = request.user.pk,
                                    content_type_id = ContentType.objects.get_for_model(alcance).pk,
                                    object_id       = alcance.id,
                                    object_repr     = force_str(alcance),
                                    action_flag     = CHANGE,
                                    change_message  = 'Aprobadas Parciales en nivel cerrado' )

                                profesor=Persona.objects.filter(usuario=alcance.usuario,usuario__is_active=True)[:1].get()
                                correo=coordinacion.correo+','+str(profesor.emailinst)+','+str(correopersonal)+','+str(correoinstitucional)
                                datos = {"result": "ok"}
                                if EMAIL_ACTIVE:
                                    alcance.materiaasignada.evaluacion().email_notaalcance(personarespon,alcance,0,correo,'02',0)
                                return HttpResponse(json.dumps(datos),content_type="application/json")

                            if nexamen=='1':
                                total=0
                                if HistoricoRecordAcademico.objects.filter(inscripcion=alcance.materiaasignada.matricula.inscripcion, asignatura=alcance.materiaasignada.materia.asignatura, fecha=alcance.materiaasignada.matricula.nivel.fin).exists():
                                    h = HistoricoRecordAcademico.objects.filter(inscripcion=alcance.materiaasignada.matricula.inscripcion, asignatura=alcance.materiaasignada.materia.asignatura, fecha=alcance.materiaasignada.matricula.nivel.fin)[:1].get()
                                    if HistoricoNotasITB.objects.filter(historico=h).exists() :
                                        hn = HistoricoNotasITB.objects.filter(historico=h)[:1].get()
                                        hn.n5 = alcance.examen
                                        hn.recup = alcance.recuperacion
                                        hn.save()
                                        total=(hn.n1+hn.n2+hn.n3+hn.n4+hn.n5)
                                        hn.total=total
                                        hn.notafinal = total
                                        hn.save()
                                        estado=''

                                        h.nota =hn.total
                                        h.save()
                                        if h.asistencia >= ASIST_PARA_APROBAR and h.nota >= NOTA_PARA_APROBAR and not h.inscripcion.carrera.online or h.nota >= NOTA_PARA_APROBAR and h.inscripcion.carrera.online:

                                            h.aprobada = True
                                        else:
                                            h.aprobada = False
                                        h.save()
                                        if h.asistencia >= ASIST_PARA_APROBAR and hn.total >= NOTA_PARA_APROBAR and not h.inscripcion.carrera.online or hn.total >= NOTA_PARA_APROBAR and h.inscripcion.carrera.online:
                                            estado=TipoEstado.objects.get(pk=NOTA_ESTADO_APROBADO)
                                        else:
                                            estado=TipoEstado.objects.get(pk=NOTA_ESTADO_REPROBADO)

                                        hn.estado = estado
                                        hn.save()
                                if RecordAcademico.objects.filter(inscripcion=alcance.materiaasignada.matricula.inscripcion, asignatura=alcance.materiaasignada.materia.asignatura).exists():
                                    r = RecordAcademico.objects.filter(inscripcion=alcance.materiaasignada.matricula.inscripcion, asignatura=alcance.materiaasignada.materia.asignatura)[:1].get()
                                    r.nota=total
                                    r.save()
                                    if r.asistencia >= ASIST_PARA_APROBAR and r.nota >= NOTA_PARA_APROBAR and not r.inscripcion.carrera.online or r.nota >= NOTA_PARA_APROBAR and r.inscripcion.carrera.online:
                                        r.aprobada = True
                                    else:
                                        r.aprobada = False
                                    r.save()

                                alcance.aprobadoex=True
                                alcance.fechaaprobacionex=datetime.now().date()
                                alcance.motivoaprobacionex=request.POST['obssecretaria'].upper()
                                alcance.usuarioapruebaex=request.user
                                alcance.estado=estado
                                alcance.save()

                                if RubroEspecieValorada.objects.filter(materia=materiaasignada,disponible=True,autorizado=True,rubro__fecha__gte=fechamax,tipoespecie__id__in=[ESPECIE_EXAMEN,ESPECIE_RECUPERACION,ESPECIE_MEJORAMIENTO]).exists():
                                    especie = RubroEspecieValorada.objects.filter(materia=materiaasignada,rubro__fecha__gte=fechamax,tipoespecie__id__in=[ESPECIE_EXAMEN,ESPECIE_RECUPERACION,ESPECIE_MEJORAMIENTO],disponible=True,autorizado=True)[:1].get()
                                    especie.disponible=False
                                    especie.aplicada = True
                                    especie.usuario=request.user
                                    especie.fechafinaliza=datetime.now()
                                    especie.save()

                                # Log de Grabar Aprobacion Nota Examen
                                LogEntry.objects.log_action(
                                    user_id         = request.user.pk,
                                    content_type_id = ContentType.objects.get_for_model(alcance).pk,
                                    object_id       = alcance.id,
                                    object_repr     = force_str(alcance),
                                    action_flag     = CHANGE,
                                    change_message  = 'Aprobada nota Examen Nivel Cerrado' )

                                profesor=Persona.objects.filter(usuario=alcance.usuario,usuario__is_active=True)[:1].get()
                                correo=coordinacion.correo+','+str(profesor.emailinst)+','+str(correopersonal)+','+str(correoinstitucional)
                                datos = {"result": "ok"}
                                if EMAIL_ACTIVE:
                                    alcance.materiaasignada.evaluacion().email_notaalcance(personarespon,alcance,0,correo,'02',0)
                                return HttpResponse(json.dumps(datos),content_type="application/json")

                            if nrecuperacion=='1':
                                if HistoricoRecordAcademico.objects.filter(inscripcion=alcance.materiaasignada.matricula.inscripcion, asignatura=alcance.materiaasignada.materia.asignatura, fecha=alcance.materiaasignada.matricula.nivel.fin).exists():
                                    h = HistoricoRecordAcademico.objects.filter(inscripcion=alcance.materiaasignada.matricula.inscripcion, asignatura=alcance.materiaasignada.materia.asignatura, fecha=alcance.materiaasignada.matricula.nivel.fin)[:1].get()

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
                                            if h.asistencia >= ASIST_PARA_APROBAR and h.nota >= NOTA_PARA_APROBAR and not h.inscripcion.carrera.online or h.nota >= NOTA_PARA_APROBAR and h.inscripcion.carrera.online:

                                                h.aprobada = True
                                            else:
                                                h.aprobada = False
                                            h.save()

                                            estado=''
                                            if h.asistencia >= ASIST_PARA_APROBAR and hn.total >= NOTA_PARA_APROBAR and not h.inscripcion.carrera.online or hn.total >= NOTA_PARA_APROBAR and h.inscripcion.carrera.online:

                                                estado=TipoEstado.objects.get(pk=NOTA_ESTADO_APROBADO)
                                            else:
                                                estado=TipoEstado.objects.get(pk=NOTA_ESTADO_REPROBADO)

                                            hn.estado = estado
                                            hn.save()

                                        if RecordAcademico.objects.filter(inscripcion=alcance.materiaasignada.matricula.inscripcion, asignatura=alcance.materiaasignada.materia.asignatura).exists():
                                            r = RecordAcademico.objects.filter(inscripcion=alcance.materiaasignada.matricula.inscripcion, asignatura=alcance.materiaasignada.materia.asignatura)[:1].get()
                                            r.nota=hn.total
                                            r.save()
                                            if r.asistencia >= ASIST_PARA_APROBAR and r.nota >= NOTA_PARA_APROBAR and not r.inscripcion.carrera.online or r.nota >= NOTA_PARA_APROBAR and r.inscripcion.carrera.online:
                                                r.aprobada = True
                                            else:
                                                r.aprobada = False
                                            r.save()
                                alcance.aprobadorec=True
                                alcance.fechaaprobacionrec=datetime.now().date()
                                alcance.motivoaprobacionrec=request.POST['obssecretaria'].upper()
                                alcance.usuarioapruebarec=request.user
                                alcance.estado=estado
                                alcance.save()

                                if RubroEspecieValorada.objects.filter(materia=materiaasignada,disponible=True,autorizado=True,rubro__fecha__gte=fechamax,tipoespecie__id__in=[ESPECIE_EXAMEN,ESPECIE_RECUPERACION,ESPECIE_MEJORAMIENTO]).exists():
                                    especie = RubroEspecieValorada.objects.filter(materia=materiaasignada,rubro__fecha__gte=fechamax,tipoespecie__id__in=[ESPECIE_EXAMEN,ESPECIE_RECUPERACION,ESPECIE_MEJORAMIENTO],disponible=True,autorizado=True)[:1].get()
                                    especie.disponible=False
                                    especie.aplicada = True
                                    especie.fechafinaliza=datetime.now()
                                    especie.usuario=request.user
                                    especie.save()

                                # Log de Grabar Aprobacion Nota Recuperacion
                                LogEntry.objects.log_action(
                                    user_id         = request.user.pk,
                                    content_type_id = ContentType.objects.get_for_model(alcance).pk,
                                    object_id       = alcance.id,
                                    object_repr     = force_str(alcance),
                                    action_flag     = CHANGE,
                                    change_message  = 'Aprobadas notas alcance Recuperacion' )

                                profesor=Persona.objects.filter(usuario=alcance.usuario,usuario__is_active=True)[:1].get()
                                correo=coordinacion.correo+','+str(profesor.emailinst)+','+str(correopersonal)+','+str(correoinstitucional)
                                datos = {"result": "ok"}
                                if EMAIL_ACTIVE:
                                    alcance.materiaasignada.evaluacion().email_notaalcance(personarespon,alcance,0,correo,'02',0)
                                return HttpResponse(json.dumps(datos),content_type="application/json")

                except Exception as ex:
                    return HttpResponse(json.dumps({"result": "bad", "error": str(ex)}),content_type="application/json")

            elif action=='quitaaprobacionparcial':
                estado=None
                fechamax = datetime.now() - timedelta(days=DIAS_ESPECIE)
                try:
                    if EvaluacionAlcance.objects.filter(materiaasignada=request.POST['matasignada']).exclude(nivelmalla=None).exists():
                        alcance=EvaluacionAlcance.objects.filter(materiaasignada=request.POST['matasignada']).exclude(nivelmalla=None)[:1].get()

                        if HistoricoRecordAcademico.objects.filter(inscripcion=alcance.materiaasignada.matricula.inscripcion, asignatura=alcance.materiaasignada.materia.asignatura, fecha=alcance.materiaasignada.matricula.nivel.fin).exists():
                            h = HistoricoRecordAcademico.objects.filter(inscripcion=alcance.materiaasignada.matricula.inscripcion, asignatura=alcance.materiaasignada.materia.asignatura, fecha=alcance.materiaasignada.matricula.nivel.fin)[:1].get()
                            h.nota=(h.nota-(alcance.n1+alcance.n2+alcance.n3+alcance.n4))
                            h.aprobada=False
                            h.save()

                            if HistoricoNotasITB.objects.filter(historico=h).exists() :
                                hn = HistoricoNotasITB.objects.filter(historico=h)[:1].get()
                                if alcance.n1>0:
                                    hn.n1 = hn.n1-alcance.n1
                                if alcance.n2>0:
                                    hn.n2 = hn.n2-alcance.n2
                                if alcance.n3>0:
                                    hn.n3 = hn.n3-alcance.n3
                                if alcance.n4>0:
                                    hn.n4 = hn.n4-alcance.n4
                                hn.total=h.nota
                                hn.notafinal=h.nota
                                estado=TipoEstado.objects.get(pk=NOTA_ESTADO_EN_CURSO)
                                hn.estado = estado
                                hn.save()

                                if RecordAcademico.objects.filter(inscripcion=alcance.materiaasignada.matricula.inscripcion, asignatura=alcance.materiaasignada.materia.asignatura).exists():
                                    r = RecordAcademico.objects.filter(inscripcion=alcance.materiaasignada.matricula.inscripcion, asignatura=alcance.materiaasignada.materia.asignatura)[:1].get()
                                    r.nota = (r.nota - (alcance.n1 + alcance.n2 + alcance.n3 + alcance.n4))
                                    r.aprobada=False
                                    r.save()

                        alcance.aprobado=False
                        alcance.fechaaprobacion=datetime.now().date()
                        alcance.usuarioaprueba=request.user
                        alcance.estado=estado
                        alcance.save()

                        if RubroEspecieValorada.objects.filter(materia=request.POST['matasignada'],disponible=False,autorizado=True,rubro__fecha__gte=fechamax,tipoespecie=ID_TIPO_ESPECIE_REG_NOTA).exists():
                            especie = RubroEspecieValorada.objects.filter(materia=request.POST['matasignada'],rubro__fecha__gte=fechamax,autorizado=True,disponible=False,tipoespecie=ID_TIPO_ESPECIE_REG_NOTA)[:1].get()
                            especie.disponible=True
                            especie.save()

                        # Log de Grabar Quitar Aprobacion Notas
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(alcance).pk,
                            object_id       = alcance.id,
                            object_repr     = force_str(alcance),
                            action_flag     = CHANGE,
                            change_message  = 'Quito aprobacion parciales nivel cerrado ' )
                        datos = {"result": "ok"}
                        return HttpResponse(json.dumps(datos),content_type="application/json")

                except Exception as ex:
                    return HttpResponse(json.dumps({"result": "bad", "error": str(ex)}),content_type="application/json")

            elif action=='quitaaprobacionexamen':
                fechamax = datetime.now() - timedelta(days=DIAS_ESPECIE)
                estado=None
                try:
                    if EvaluacionAlcance.objects.filter(materiaasignada=request.POST['matasignada']).exclude(nivelmalla=None).exists():
                        alcance=EvaluacionAlcance.objects.filter(materiaasignada=request.POST['matasignada']).exclude(nivelmalla=None)[:1].get()

                        if HistoricoRecordAcademico.objects.filter(inscripcion=alcance.materiaasignada.matricula.inscripcion, asignatura=alcance.materiaasignada.materia.asignatura, fecha=alcance.materiaasignada.matricula.nivel.fin).exists():
                            h = HistoricoRecordAcademico.objects.filter(inscripcion=alcance.materiaasignada.matricula.inscripcion, asignatura=alcance.materiaasignada.materia.asignatura, fecha=alcance.materiaasignada.matricula.nivel.fin)[:1].get()
                            h.nota=(h.nota-(alcance.examen))
                            h.aprobada=False
                            h.save()

                            if HistoricoNotasITB.objects.filter(historico=h).exists():
                                hn = HistoricoNotasITB.objects.filter(historico=h)[:1].get()
                                if alcance.examen>0:
                                    hn.n5 = hn.n5-alcance.examen
                                hn.total=h.nota
                                hn.notafinal=h.nota
                                estado=TipoEstado.objects.get(pk=NOTA_ESTADO_EN_CURSO)
                                hn.estado = estado
                                hn.save()

                            if RecordAcademico.objects.filter(inscripcion=alcance.materiaasignada.matricula.inscripcion, asignatura=alcance.materiaasignada.materia.asignatura).exists():
                                r = RecordAcademico.objects.filter(inscripcion=alcance.materiaasignada.matricula.inscripcion, asignatura=alcance.materiaasignada.materia.asignatura)[:1].get()
                                r.nota=(r.nota-(alcance.examen))
                                r.aprobada=False
                                r.save()

                        alcance.aprobadoex=False
                        alcance.fechaaprobacionex=datetime.now().date()
                        alcance.usuarioapruebaex=request.user
                        alcance.estado=estado
                        alcance.save()

                        if RubroEspecieValorada.objects.filter(materia=request.POST['matasignada'],disponible=False,autorizado=True,rubro__fecha__gte=fechamax,tipoespecie__in=[ID_TIPO_ESPECIE_REG_NOTA,ESPECIE_EXAMEN,ESPECIE_RECUPERACION,ESPECIE_MEJORAMIENTO]).exists():
                            especie = RubroEspecieValorada.objects.filter(materia=request.POST['matasignada'],rubro__fecha__gte=fechamax,disponible=False,autorizado=True,tipoespecie__in=[ID_TIPO_ESPECIE_REG_NOTA,ESPECIE_EXAMEN,ESPECIE_RECUPERACION,ESPECIE_MEJORAMIENTO])[:1].get()
                            especie.disponible=True
                            especie.save()

                        #Obtain client ip address
                        client_address = ip_client_address(request)
                        # Log de Grabar Quitar Aprobacion Examen
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(alcance).pk,
                            object_id       = alcance.id,
                            object_repr     = force_str(alcance),
                            action_flag     = CHANGE,
                            change_message  = 'Quito aprobacion examen nivel cerrado ' + client_address + ')' )
                        datos = {"result": "ok"}
                        return HttpResponse(json.dumps(datos),content_type="application/json")

                except Exception as ex:
                    return HttpResponse(json.dumps({"result": "bad", "error": str(ex)}),content_type="application/json")

            elif action=='quitaaprobacionrecuperacion':
                fechamax = datetime.now() - timedelta(days=DIAS_ESPECIE)
                estado=None
                try:
                    if EvaluacionAlcance.objects.filter(materiaasignada=request.POST['matasignada']).exclude(nivelmalla=None).exists():
                        alcance=EvaluacionAlcance.objects.filter(materiaasignada=request.POST['matasignada']).exclude(nivelmalla=None)[:1].get()
                        notastotales=0
                        if HistoricoRecordAcademico.objects.filter(inscripcion=alcance.materiaasignada.matricula.inscripcion, asignatura=alcance.materiaasignada.materia.asignatura, fecha=alcance.materiaasignada.matricula.nivel.fin).exists():
                            h = HistoricoRecordAcademico.objects.filter(inscripcion=alcance.materiaasignada.matricula.inscripcion, asignatura=alcance.materiaasignada.materia.asignatura, fecha=alcance.materiaasignada.matricula.nivel.fin)[:1].get()

                            if HistoricoNotasITB.objects.filter(historico=h).exists():
                                hn = HistoricoNotasITB.objects.filter(historico=h)[:1].get()
                                hn.recup = 0
                                notastotales=(hn.n1+hn.n2+hn.n3+hn.n4+hn.n5)
                                hn.total=notastotales
                                hn.notafinal=notastotales
                                hn.save()
                                if hn.notafinal < NOTA_PARA_APROBAR:
                                    estado=TipoEstado.objects.get(pk=NOTA_ESTADO_EN_CURSO)
                                    hn.estado = estado
                                else:
                                    estado=TipoEstado.objects.get(pk=NOTA_ESTADO_SUPLETORIO)
                                    hn.estado = estado
                                hn.save()

                                h.nota=hn.notafinal
                                h.save()
                                if h.asistencia>=ASIST_PARA_APROBAR and h.nota>=NOTA_PARA_APROBAR and not h.inscripcion.carrera.online or h.nota>=NOTA_PARA_APROBAR and h.inscripcion.carrera.online:
                                    h.aprobada=True
                                else:
                                    h.aprobada=False
                                h.save()
                                if RecordAcademico.objects.filter(inscripcion=alcance.materiaasignada.matricula.inscripcion, asignatura=alcance.materiaasignada.materia.asignatura).exists():
                                    r = RecordAcademico.objects.filter(inscripcion=alcance.materiaasignada.matricula.inscripcion, asignatura=alcance.materiaasignada.materia.asignatura)[:1].get()
                                    r.nota=hn.notafinal
                                    if r.asistencia >= ASIST_PARA_APROBAR and r.nota >= NOTA_PARA_APROBAR and not r.inscripcion.carrera.online or r.nota >= NOTA_PARA_APROBAR and r.inscripcion.carrera.online:
                                        r.aprobada=True
                                    else:
                                        r.aprobada=False
                                    r.save()

                        alcance.aprobadorec=False
                        alcance.fechaaprobacionrec=datetime.now().date()
                        alcance.usuarioapruebarec=request.user
                        alcance.estado=estado
                        alcance.save()

                        if RubroEspecieValorada.objects.filter(materia=request.POST['matasignada'],disponible=False,autorizado=True,rubro__fecha__gte=fechamax,tipoespecie__in=[ID_TIPO_ESPECIE_REG_NOTA,ESPECIE_EXAMEN,ESPECIE_RECUPERACION,ESPECIE_MEJORAMIENTO]).exists():
                            especie = RubroEspecieValorada.objects.filter(materia=request.POST['matasignada'],rubro__fecha__gte=fechamax,disponible=False,autorizado=True,tipoespecie__in=[ID_TIPO_ESPECIE_REG_NOTA,ESPECIE_EXAMEN,ESPECIE_RECUPERACION,ESPECIE_MEJORAMIENTO])[:1].get()
                            especie.disponible=True
                            especie.save()

                        #Obtain client ip address
                        client_address = ip_client_address(request)
                        # Log de Grabar Quitar Aprobacion Recuperacion
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(alcance).pk,
                            object_id       = alcance.id,
                            object_repr     = force_str(alcance),
                            action_flag     = CHANGE,
                            change_message  = 'Quito aprobacion recuperacion nivel cerrado ' + client_address + ')' )
                        datos = {"result": "ok"}
                        return HttpResponse(json.dumps(datos),content_type="application/json")

                except Exception as ex:
                    return HttpResponse(json.dumps({"result": "bad", "error": str(ex)}),content_type="application/json")

            elif action=='cambiodeestado':
                try:
                    if EvaluacionAlcance.objects.filter(materiaasignada=request.POST['matasignada']).exists():
                        if EvaluacionITB.objects.filter(materiaasignada=request.POST['matasignada']).exists():
                            evalua=EvaluacionITB.objects.filter(materiaasignada=request.POST['matasignada'])[:1].get()
                            if evalua.recuperacion>0 and evalua.estado.id==NOTA_ESTADO_REPROBADO:
                                evalua.recuperacion=0
                                evalua.save()
                                evalua.actualiza_estado_nueva()

                            # Log de Cambio de estado
                            LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(evalua).pk,
                                object_id       = evalua.id,
                                object_repr     = force_str(evalua),
                                action_flag     = CHANGE,
                                change_message  = 'Cambio de estado de nota' )
                            datos = {"result": "ok"}
                            return HttpResponse(json.dumps(datos),content_type="application/json")

                except Exception as ex:
                    return HttpResponse(json.dumps({"result": "bad", "error": str(ex)}),content_type="application/json")


            elif action=='eliminaalcance':
                try:
                    alcance = EvaluacionAlcance.objects.get(pk=request.POST['alcance'])
                    #Obtain client ip address
                    client_address = ip_client_address(request)
                    # Log de Eliminar Evaluacion Alcance
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(alcance).pk,
                        object_id       = alcance.id,
                        object_repr     = force_str(alcance),
                        action_flag     = DELETION,
                        change_message  = 'Se elimino alcance evaluacion ' + client_address + ')' )
                    alcance.delete()
                    return HttpResponse(json.dumps({'result': 'ok'}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({'result': 'bad'}),content_type="application/json")



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
                return render(request ,"aprobacion_alcance_notas/observacion.html" ,  data)
        else:
            data = {'title': 'Aprobacion en Nivel Cerrado'}
            evaalcance=None
            mat=''
            todos = None
            data['aprobacionform'] = AprobacionCambioNotaForm()

            if 'profesorid' in request.GET:
                profesor = Profesor.objects.filter(pk=request.GET['profesorid'])[:1].get()
                data['profesor']=profesor
                # materiasid = RubroEspecieValorada.objects.filter(Q(materia__materia__id__in=ProfesorMateria.objects.filter(profesor=profesor,materia__cerrado=True).distinct('materia').values('materia'))|Q(materia__materia__id__in=ProfesorMateria.objects.filter(profesor_aux=profesor.id,materia__cerrado=True).distinct('materia').values('materia')),rubro__fecha__gte=fechamax,rubro__cancelado=True,materia__materia__nivel__cerrado=False,autorizado=True).distinct('materia__materia').values('materia__materia')
                materiasid = ProfesorMateria.objects.filter(Q(profesor=profesor,materia__cerrado=True,materia__nivel__cerrado=True)|Q(profesor_aux=profesor.id,materia__cerrado=True,materia__nivel__cerrado=True)).distinct('materia').values('materia')
                data['materias']=Materia.objects.filter(id__in=materiasid)
                evaalcance = EvaluacionAlcance.objects.filter(materiaasignada__materia__id__in=materiasid,materiaasignada__materia__nivel__cerrado=True).exclude(nivelmalla=None).order_by('materiaasignada__matricula__inscripcion__persona__apellido1','materiaasignada__matricula__inscripcion__persona__apellido2','materiaasignada__matricula__inscripcion__persona__nombres')
            if 'id' in request.GET:
                mat= request.GET['id']
                materia = Materia.objects.get(pk=mat)
                evaalcance = EvaluacionAlcance.objects.filter(materiaasignada__materia=materia,materiaasignada__materia__cerrado=True,materiaasignada__materia__nivel__cerrado=True).exclude(nivelmalla=None).order_by('materiaasignada__matricula__inscripcion__persona__apellido1','materiaasignada__matricula__inscripcion__persona__apellido2','materiaasignada__matricula__inscripcion__persona__nombres')
                data['mat'] = int(mat)
                data['materiaselec'] = materia

            elif 't' in request.GET:
                todos = request.GET['t']
                evaalcance=EvaluacionAlcance.objects.filter(materiaasignada__materia__cerrado=True,materiaasignada__materia__nivel__cerrado=True).exclude(nivelmalla=None).order_by('-fecha')

            elif 'aprob' in request.GET:
                evaalcance = EvaluacionAlcance.objects.filter(aprobado=True,materiaasignada__materia__nivel__cerrado=True).exclude(nivelmalla=None).order_by('-fecha')
                data['aprobadas'] = 'aprob'

            elif 'noaprob' in request.GET:
                evaalcance = EvaluacionAlcance.objects.filter(aprobado=False,materiaasignada__materia__nivel__cerrado=True).exclude(nivelmalla=None).order_by('-fecha')
                data['noaprobadas'] = 'noaprob'

            elif 'noexa' in request.GET:
                evaalcance = EvaluacionAlcance.objects.filter(aprobadoex=False,materiaasignada__materia__nivel__cerrado=True).exclude(nivelmalla=None).order_by('-fecha')
                data['noaprobexa'] = 'noexa'

            elif 'norec' in request.GET:
                evaalcance = EvaluacionAlcance.objects.filter(aprobadorec=False,materiaasignada__materia__nivel__cerrado=True).exclude(nivelmalla=None).order_by('-fecha')
                data['noaprobrec'] = 'norec'

            else:
                if not evaalcance:
                    evaalcance=EvaluacionAlcance.objects.filter(materiaasignada__materia__cerrado=True,materiaasignada__materia__nivel__cerrado=True).exclude(nivelmalla=None).order_by('-fecha')
                    data['todos']=evaalcance

            paging = MiPaginador(evaalcance, 60)
            p = 1
            try:
                if 'page' in request.GET:
                    p = int(request.GET['page'])
                    paging = MiPaginador(evaalcance, 60)
                page = paging.page(p)
            except Exception as ex:
                page = paging.page(1)
            data['paging'] = paging
            data['rangospaging'] = paging.rangos_paginado(p)
            data['page'] = page
            data['evaalcance'] = page.object_list
            data['todos'] = todos if todos else ""
            data['encurso']=NOTA_ESTADO_EN_CURSO
            data['examen']=NOTA_ESTADO_DERECHOEXAMEN
            data['recuperacion']=NOTA_ESTADO_SUPLETORIO
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
            return render(request ,"alcance_nivelcerrado/aprobacion_nivelcerrado.html" ,  data)
