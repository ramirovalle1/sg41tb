from datetime import datetime
import json
from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
from decorators import secure_module
from settings import EMAIL_ACTIVE, NIVEL_MALLA_CERO, NOTA_PARA_APROBAR
from sga.alu_malla import aprobadaAsignatura
from sga.commonviews import addUserData, ip_client_address
from sga.forms import EstudianteTutoriaForm, ObservacionTutoriaForm, ArchivoTesisForm, RevisionTutoriaForm, ActaSustentacionForm, ComiteSustentacionForm
from sga.models import EstudianteTutoria, Egresado, Tutoria, Inscripcion, AsignaturaMalla, RevisionTutoria, convertir_fecha, ActaSustentacion, HistoricoRecordAcademico, RecordAcademico, Profesor


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
# @secure_module
@transaction.atomic()
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action == 'add':
                f= EstudianteTutoriaForm(request.POST)
                if f.is_valid():
                    tutt = Tutoria.objects.get(id=f.cleaned_data['tutoria'].id)
                    if EstudianteTutoria.objects.filter(tutoria=tutt).count() >= tutt.numtutoria:
                        return HttpResponseRedirect('/profe_tutoria?error=EL ALUMNO YA TIENE EL NUMERO DE TUTORIAS COMPLETAS&id='+str(tutt.id))
                    if EstudianteTutoria.objects.filter(tutoria=tutt,asistencia=True,aprobar=False).exists():
                        return HttpResponseRedirect('/profe_tutoria?error=NO PUEDE INGRESAR LA TUTORIA, TIENE UNA TUTORIA SIN APROBAR&id='+str(tutt.id))
                    if 'profe_tutor' in request.POST:
                        estudiantetutor = EstudianteTutoria.objects.get(id = request.POST['profe_tutor'])
                        estudiantetutor.tutoria = f.cleaned_data['tutoria']
                        estudiantetutor.progreso = f.cleaned_data['progreso']
                        estudiantetutor.observacion = f.cleaned_data['observacion']
                        estudiantetutor.tarea = f.cleaned_data['tarea']
                        estudiantetutor.asistencia = int(f.cleaned_data['asistencia'])
                        estudiantetutor.fecha = datetime.now().date()
                    else:
                        estudiantetutor = EstudianteTutoria(
                                            tutoria = f.cleaned_data['tutoria'],
                                            progreso = f.cleaned_data['progreso'],
                                            observacion = f.cleaned_data['observacion'],
                                            tarea = f.cleaned_data['tarea'],
                                            asistencia = f.cleaned_data['asistencia'] ,
                                            fecha = datetime.now().date(),
                                            fechaaprobar = datetime.now())
                    estudiantetutor.save()
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(estudiantetutor).pk,
                    object_id       = estudiantetutor.id,
                    object_repr     = force_str(estudiantetutor),
                    action_flag     = ADDITION,
                    change_message  = 'Ingreso o edicion de Registro de Tutoria (' + client_address + ')' )
                    return HttpResponseRedirect('/profe_tutoria?id='+str(f.cleaned_data['tutoria'].id))

                return HttpResponseRedirect('/profe_tutoria?action=add')
            elif action == 'addcomite':
                try:
                    tutoria = Tutoria.objects.get(pk=request.POST['archtesis_id'])
                    f = ComiteSustentacionForm(request.POST)
                    correod = ''
                    correog = ''
                    correom = ''
                    correof = ''
                    comite =[]
                    correoeli = ''
                    b=0
                    if f.is_valid():
                        fechaant = tutoria.fecha_sustentacion
                        horaant = tutoria.hora_sustentacion
                        doc1ant = tutoria.docente1
                        doc2ant = tutoria.docente2
                        doc3ant = tutoria.docente3
                        if (f.cleaned_data['docente1_id']):
                            tutoria.docente1_id = f.cleaned_data['docente1_id']
                            pr= Profesor.objects.get(pk= f.cleaned_data['docente1_id'])
                            comite.append((pr.persona.nombre_completo()))
                            correog = correog + ',' + pr.persona.emailinst
                        if f.cleaned_data['docente2_id']:
                            tutoria.docente2_id = f.cleaned_data['docente2_id']
                            pr= Profesor.objects.get(pk= f.cleaned_data['docente2_id'])
                            correog = correog + ',' + pr.persona.emailinst
                            comite.append((pr.persona.nombre_completo()))
                        if (f.cleaned_data['docente3_id']):
                            tutoria.docente3_id = f.cleaned_data['docente3_id']
                            pr= Profesor.objects.get(pk= f.cleaned_data['docente3_id'])
                            correog= correog + ',' + pr.persona.emailinst
                            comite.append((pr.persona.nombre_completo()))

                        tutoria.fecha_sustentacion = f.cleaned_data['fechasust']
                        tutoria.hora_sustentacion = f.cleaned_data['horasust']
                        tutoria.save()
                        if doc1ant:
                            if str(doc1ant.id) != str(f.cleaned_data['docente1_id']):
                                b = 1
                                if f.cleaned_data['docente1_id']:
                                    pr= Profesor.objects.get(pk= f.cleaned_data['docente1_id'])
                                    correom = correom + ',' + pr.persona.emailinst
                                tutoria.notificacion_sustentacion_elimina(request.user,'Estimado: '+ doc1ant.persona.nombre_completo() + ' Agradecemos su colaboracion con el tribunal pero lamentablemente por razones de fuerza mayor usted no formara parte de este tribunal', doc1ant.persona.emailinst)
                            else:
                                if f.cleaned_data['docente1_id']:
                                    pr= Profesor.objects.get(pk= f.cleaned_data['docente1_id'])
                                    correof = correof + ',' + pr.persona.emailinst

                        else:
                            if str(f.cleaned_data['docente1_id']):
                                pr= Profesor.objects.get(pk= f.cleaned_data['docente1_id'])
                                correod = correod + ',' + pr.persona.emailinst

                        if doc2ant:
                            if str(doc2ant.id) != str(f.cleaned_data['docente2_id']) :
                                if f.cleaned_data['docente2_id']:
                                    pr= Profesor.objects.get(pk= f.cleaned_data['docente2_id'])
                                    correom = correom + ',' + pr.persona.emailinst
                                tutoria.notificacion_sustentacion_elimina(request.user,'Estimado: '+ doc2ant.persona.nombre_completo() + ' Agradecemos su colaboracion con el tribunal pero lamentablemente por razones de fuerza mayor usted no formara parte de este tribunal', doc2ant.persona.emailinst)
                                b = 1
                            else:
                                if f.cleaned_data['docente2_id']:
                                    pr= Profesor.objects.get(pk= f.cleaned_data['docente2_id'])
                                    correof = correof + ',' + pr.persona.emailinst
                        else:
                            if str(f.cleaned_data['docente2_id']):
                                pr= Profesor.objects.get(pk= f.cleaned_data['docente2_id'])
                                correod = correod + ',' + pr.persona.emailinst
                        if doc3ant:
                            if str(doc3ant.id) != str(f.cleaned_data['docente3_id']):
                                if f.cleaned_data['docente3_id']:
                                    pr= Profesor.objects.get(pk= f.cleaned_data['docente3_id'])
                                    correom = correom + ',' + pr.persona.emailinst
                                b = 1
                                tutoria.notificacion_sustentacion_elimina(request.user,'Estimado: '+ doc3ant.persona.nombre_completo() + ' Agradecemos su colaboracion con el tribunal pero lamentablemente por razones de fuerza mayor usted no formara parte de este tribunal ', doc3ant.persona.emailinst)
                            else:
                                if f.cleaned_data['docente3_id']:
                                    pr= Profesor.objects.get(pk= f.cleaned_data['docente3_id'])
                                    correof = correof + ',' + pr.persona.emailinst
                        else:
                            if str(f.cleaned_data['docente3_id']):
                                pr= Profesor.objects.get(pk= f.cleaned_data['docente3_id'])
                                correod = correod + ',' + pr.persona.emailinst

                        if correom:
                            tutoria.notificacion_sustentacion(request.user,'Se ha  modificado comite de sustentacion',  correom,comite)
                        if correod:
                            tutoria.notificacion_sustentacion(request.user,'Comite Sustentacion',  correod,comite)
                        # else:
                        #     tutoria.notificacion_sustentacion(request.user,'Comite Sustentacion',correod,comite)

                        if request.POST['op'] == '1':
                            # tutoria.notificacion_sustentacion(request.user,'Se ha adicionado fecha de sustentacion', correog,'')
                            tutoria.notificacion_sustentacion_alumno(request.user,'Se ha Programado la sustentacion',tutoria.estudiante.persona.emailinst+","+ tutoria.estudiante.persona.email)
                        else:
                            if fechaant != f.cleaned_data['fechasust'] or  horaant != str(f.cleaned_data['horasust']) :
                                tutoria.notificacion_sustentacion(request.user,'Se ha reprogramado la  sustentacion',correof,'')
                                tutoria.notificacion_sustentacion_alumno(request.user,'Se ha ha reprogramado la  sustentacion',tutoria.estudiante.persona.emailinst+","+ tutoria.estudiante.persona.email)

                        return HttpResponseRedirect('/tutoria?id='+str(tutoria.profesor.id)+'&msj=Registro Guarado Correctamente')
                except Exception as e:
                    return HttpResponseRedirect('/tutoria?id='+str(tutoria.profesor.id)+'&error='+str(e))

            elif action == 'addobservacion':
                try:
                    if EstudianteTutoria.objects.filter(id = request.POST['idestu']).exists():
                        estudiantetutoria = EstudianteTutoria.objects.get(id = request.POST['idestu'])
                        estudiantetutoria.observacionestudia = request.POST['obser']
                        estudiantetutoria.save()
                        if EMAIL_ACTIVE:
                            estudiantetutoria.email_observacion(request.POST['obser'])
                        return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
            elif action == 'activacion':
                try:
                    e = EstudianteTutoria.objects.get(pk=request.POST['id'])
                    if e.asistencia == False:
                        e.asistencia = not e.asistencia
                        e.save()

                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(e).pk,
                            object_id       = e.id,
                            object_repr     = force_str(e),
                            action_flag     = ADDITION,
                            change_message  = 'Activacion o desactivacion Tutoria (' + client_address + ')' )
                        return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
                except:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
            elif action == 'activarapro':
                try:
                    e = EstudianteTutoria.objects.get(pk=request.POST['id'])
                    if  e.tutoria.estudiante.graduado():
                        return HttpResponse(json.dumps({"result":"gradua"}),content_type="application/json")
                    if e.aprobar == False:
                        e.aprobar = not e.aprobar
                        e.fechaaprobar = datetime.now()
                        e.save()

                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(e).pk,
                            object_id       = e.id,
                            object_repr     = force_str(e),
                            action_flag     = ADDITION,
                            change_message  = 'Aprobar o reprobar Tutoria (' + client_address + ')' )
                        return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
            elif action == 'antiplagio':
                try:
                    # transegr = TransaccionEgreso.objects.get(pk=request.POST['transac'])
                    tutoria = Tutoria.objects.get(pk=request.POST['archtesis_id'])

                    # pagoch = PagoCheque.objects.get(egreso=transegr)
                    f = ArchivoTesisForm(request.POST,request.FILES)
                    if f.is_valid():
                        if 'soportetesis' in request.FILES:
                            tutoria.archivotesis=request.FILES['soportetesis']
                            tutoria.fechaarchivo=datetime.now()
                            tutoria.user=request.user
                            tutoria.save()

                            client_address = ip_client_address(request)
                            LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(tutoria).pk,
                                object_id       = tutoria.id,
                                object_repr     = force_str(tutoria),
                                action_flag     = ADDITION,
                                change_message  = 'Se ha guardado Archivo Tesis (' + client_address + ')' )

                            if EMAIL_ACTIVE:
                                tutoria.email_enviatesis(request.FILES['soportetesis'])
                            return HttpResponseRedirect('/tutoria?s='+str(tutoria.estudiante.persona.apellido1)+' '+str(tutoria.estudiante.persona.apellido2)+'&msj=Archivo Guardado')
                        else:
                            return HttpResponseRedirect('/tutoria?s='+str(tutoria.estudiante.persona.apellido1)+' '+str(tutoria.estudiante.persona.apellido2)+'&error=Error en Formulario')
                    else:
                        return HttpResponseRedirect('/tutoria?s='+str(tutoria.estudiante.persona.apellido1)+' '+str(tutoria.estudiante.persona.apellido2)+'&error=Error en Formulario')

                except Exception as ex:
                    # return HttpResponseRedirect("/profe_tutoria")
                    return HttpResponseRedirect('/tutoria?error='+str(ex))
            elif action == 'addinforme':
                try:
                    # transegr = TransaccionEgreso.objects.get(pk=request.POST['transac'])
                    tutoria = Tutoria.objects.get(pk=request.POST['archtesis_id'])

                    # pagoch = PagoCheque.objects.get(egreso=transegr)
                    f = RevisionTutoriaForm(request.POST,request.FILES)
                    if 'informe' in request.FILES:
                        if f.is_valid():
                            revison = RevisionTutoria(tutoria = tutoria,
                                                      fecha = datetime.now(),
                                                      observacion = f.cleaned_data['observacion'],
                                                      informe = request.FILES['informe'],
                                                      finalizado=f.cleaned_data['finalizado'])
                            revison.save()

                            client_address = ip_client_address(request)
                            LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(tutoria).pk,
                                object_id       = tutoria.id,
                                object_repr     = force_str(tutoria),
                                action_flag     = ADDITION,
                                change_message  = 'Se ha Adicionado Revision de Tesis (' + client_address + ')' )

                            revison.notificacion()

                            return HttpResponseRedirect('/tutoria?action=revision&tut='+str(tutoria.id))
                        else:
                            return HttpResponseRedirect('/tutoria?action=revision&tut='+str(tutoria.id)+'&error=Error en Formulario')
                    else:
                        return HttpResponseRedirect('/tutoria?action=revision&tut='+str(tutoria.id)+'&error=No se ha agregado el informe')
                except Exception as ex:
                    # return HttpResponseRedirect("/profe_tutoria")
                    return HttpResponseRedirect('/tutoria?error='+str(ex))

            elif action == 'addacta':
                sid = transaction.savepoint()
                try:
                    # transegr = TransaccionEgreso.objects.get(pk=request.POST['transac'])
                    tutoria = Tutoria.objects.get(pk=request.POST['archtesis_id'])

                    # pagoch = PagoCheque.objects.get(egreso=transegr)
                    f = ActaSustentacionForm(request.POST,request.FILES)
                    if 'acta' in request.FILES:
                        if f.is_valid():
                            inscripcionmalla = tutoria.estudiante.malla_inscripcion().malla
                            if AsignaturaMalla.objects.filter(malla=inscripcionmalla,asignatura__titulacion=True).exists():
                                if AsignaturaMalla.objects.filter(malla=inscripcionmalla,asignatura__titulacion=True).count() > 1:
                                    return HttpResponseRedirect('/tutoria?error=Existe mas de una asignatura de Titulacion')
                                else:
                                    acta = ActaSustentacion(tutoria = tutoria,
                                                              fecha = datetime.now(),
                                                              usuario = request.user,
                                                              fecha_sustentacion = (f.cleaned_data['fecha_sustentacion']),
                                                              acta = request.FILES['acta'],
                                                              nota=f.cleaned_data['nota'],
                                                              observacion=f.cleaned_data['observacion'])
                                    acta.save()

                                    client_address = ip_client_address(request)
                                    LogEntry.objects.log_action(
                                        user_id         = request.user.pk,
                                        content_type_id = ContentType.objects.get_for_model(tutoria).pk,
                                        object_id       = tutoria.id,
                                        object_repr     = force_str(tutoria),
                                        action_flag     = ADDITION,
                                        change_message  = 'Se ha Adicionado Acta (' + client_address + ')' )


                                    asig = AsignaturaMalla.objects.filter(malla=inscripcionmalla,asignatura__titulacion=True)[:1].get().asignatura
                                    if acta.nota >= NOTA_PARA_APROBAR:
                                        aprobado = True
                                    else:
                                        aprobado = False
                                    historico = HistoricoRecordAcademico(inscripcion=tutoria.estudiante,
                                                                asignatura=asig,
                                                                nota=acta.nota,
                                                                asistencia=100,
                                                                fecha=acta.fecha_sustentacion,
                                                                aprobada=aprobado,
                                                                convalidacion=False,
                                                                pendiente=False)
                                    historico.save()
                                    if RecordAcademico.objects.filter(inscripcion=tutoria.estudiante,asignatura=asig).exists():
                                        record = RecordAcademico.objects.filter(inscripcion=tutoria.estudiante,asignatura=asig)[:1].get()
                                        record.nota=acta.nota
                                        record.asistencia=100
                                        record.fecha=acta.fecha_sustentacion
                                        record.aprobada=aprobado
                                        record.convalidacion=False
                                        record.pendiente=False
                                    else:
                                        record = RecordAcademico(inscripcion=tutoria.estudiante, asignatura=asig,
                                                                nota=acta.nota, asistencia=100,
                                                                fecha=acta.fecha_sustentacion, aprobada=aprobado,
                                                                convalidacion=False, pendiente=False)
                                    record.save()

                                    client_address = ip_client_address(request)
                                    LogEntry.objects.log_action(
                                        user_id         = request.user.pk,
                                        content_type_id = ContentType.objects.get_for_model(tutoria).pk,
                                        object_id       = tutoria.id,
                                        object_repr     = force_str(tutoria),
                                        action_flag     = ADDITION,
                                        change_message  = 'Se ha Adicionado Historico y Record (' + client_address + ')' )


                                    tutoria.estudiante.notiificacion_acta(record,request.user, acta)
                                    transaction.savepoint_commit(sid)
                                    return HttpResponseRedirect('/tutoria?id='+str(tutoria.profesor.id)+'&msj= Registro Guardado Correctamente')
                            else:
                                return HttpResponseRedirect('/tutoria?id='+str(tutoria.profesor.id)+'&error=No Existe  asignatura de titulacion ')
                        else:
                            return HttpResponseRedirect('/tutoria?id='+str(tutoria.profesor.id)+'&error=Error en Formulario')
                    else:
                        return HttpResponseRedirect('/tutoria?id='+str(tutoria.profesor.id)+'&error=No se ha agregado el acta de sustentacion')
                except Exception as ex:
                    transaction.savepoint_rollback(sid)
                    return HttpResponseRedirect('/tutoria?id='+str(tutoria.profesor.id)+'&error= Ocurrio un error'+str(ex))
            return HttpResponseRedirect('/profe_tutoria')


        else:
            data = {'title': 'Registro de Tutorias'}
            addUserData(request,data)

            if 'action' in request.GET:
                action = request.GET['action']
                if action == 'add':
                    data['title'] = 'Ingreso de Tutoria a Estudiante'
                    hoy = datetime.now().date()
                    tutoria = Tutoria.objects.get(id=request.GET['id'])
                    if EstudianteTutoria.objects.filter(tutoria=tutoria,asistencia=True,aprobar=False).exists():
                        return HttpResponseRedirect('/profe_tutoria?error=NO PUEDE INGRESAR LA TUTORIA, TIENE UNA TUTORIA SIN APROBAR&id='+str(tutoria.id))
                    inscripcion = Inscripcion.objects.get(id=tutoria.estudiante.id)
                    if inscripcion.adeuda_a_la_fecha():
                        return HttpResponseRedirect('/profe_tutoria?error=EL ALUMNO TIENE VALORES POR CANCELAR&id='+str(tutoria.id))
                    inscripcionmalla = inscripcion.malla_inscripcion()
                    num = 0
                    for x in AsignaturaMalla.objects.filter(malla=inscripcionmalla.malla).exclude(nivelmalla__id=NIVEL_MALLA_CERO):
                        try:
                            if aprobadaAsignatura(x, inscripcion).aprobada:
                                num = num + 1
                        except:
                            pass
                    if inscripcion.matricula():
                        if not Inscripcion.objects.get(id=tutoria.estudiante_id).matriculatutori().esta_retirado():
                            form = EstudianteTutoriaForm(initial={"tutoria":tutoria})
                            # form.tutoriaprofe(request.GET['id'])

                            data['form'] = form
                            return render(request ,"tutoria/addprofetutoria.html" ,  data)
                        else:
                            return HttpResponseRedirect('/profe_tutoria?error=EL ALUMNO ESTA RETIRADO NO PUEDE REALIZAR TUTORIA&id='+str(tutoria.id))
                    else:
                        #OCastillo 08-09-2021 se excluyen asignaturas practica y titulacion para carrera Tricologia
                        if inscripcion.carrera.id!=33:
                            if ( num >= AsignaturaMalla.objects.filter(malla=inscripcionmalla.malla).exclude(nivelmalla__id=NIVEL_MALLA_CERO).exclude(asignatura__nivelacion=True).exclude(asignatura__nombre__icontains='TRABAJO DE TITULACI').exclude(asignatura__nombre__icontains='CTICAS PREPROFE').count() - 1 ):
                                form = EstudianteTutoriaForm(initial={"tutoria":tutoria})
                                data['form'] = form
                                return render(request ,"tutoria/addprofetutoria.html" ,  data)
                            else:
                                return HttpResponseRedirect('/profe_tutoria?error=EL ALUMNO NO CUMPLE LA MALLA&id='+str(tutoria.id))
                        else:
                            if ( num >= AsignaturaMalla.objects.filter(malla=inscripcionmalla.malla).exclude(nivelmalla__id=NIVEL_MALLA_CERO).exclude(asignatura__id__in=[650,651]).count() - 1 ):
                                form = EstudianteTutoriaForm(initial={"tutoria":tutoria})
                                data['form'] = form
                                return render(request ,"tutoria/addprofetutoria.html" ,  data)
                            else:
                                return HttpResponseRedirect('/profe_tutoria?error=EL ALUMNO NO CUMPLE LA MALLA&id='+str(tutoria.id))

                elif action == 'edit':
                    data['title'] = 'Editar  Tutoria a Estudiante'
                    estuditutoria = EstudianteTutoria.objects.get(id = request.GET['id'])
                    if Inscripcion.objects.get(id=estuditutoria.tutoria.estudiante_id).matriculatutori():
                        if not Inscripcion.objects.get(id=estuditutoria.tutoria.estudiante_id).matriculatutori().esta_retirado():
                            data['edit'] = 1
                            data['profe_tutor'] = estuditutoria
                            data['form'] = EstudianteTutoriaForm(initial={"tutoria":estuditutoria.tutoria,"progreso":estuditutoria.progreso,"tarea":estuditutoria.tarea, "observacion":estuditutoria.observacion,"asistencia":estuditutoria.asistencia})
                            return render(request ,"tutoria/addprofetutoria.html" ,  data)

                        return HttpResponseRedirect('/profe_tutoria?error=EL ALUMNO ESTA RETIRADO NO PUEDE EDITAR TUTORIA&id='+str(estuditutoria.tutoria.id))
                    return HttpResponseRedirect('/profe_tutoria?error=EL ALUMNO NO ESTA MATRICULADO NO PUEDE EDITAR TUTORIA&id='+str(estuditutoria.tutoria.id))
                elif action == 'delete':
                    estuditutoria = EstudianteTutoria.objects.get(id = request.GET['id'])
                    estuditutoria.delete()
                    return HttpResponseRedirect('/profe_tutoria?id='+str(request.GET['idtut']))




            else:
                if 'id' in request.GET:
                    idtuto = request.GET['id']
                else:
                    try:
                        idtuto = Tutoria.objects.get(estudiante__persona__usuario=request.user,estado = True).id
                        try:
                            inscripcion = Inscripcion.objects.get(id=Tutoria.objects.get(id=idtuto).estudiante.id)
                            inscripcionmalla = inscripcion.malla_inscripcion()
                            num = 0
                            for x in AsignaturaMalla.objects.filter(malla=inscripcionmalla.malla).exclude(nivelmalla__id=NIVEL_MALLA_CERO):
                                try:
                                    if aprobadaAsignatura(x, inscripcion).aprobada:
                                        num = num + 1
                                except:
                                    pass
                            tutoria = Tutoria.objects.get(id=idtuto)
                            if Tutoria.objects.get(id=idtuto).estudiante.matricula():
                                if Tutoria.objects.get(id=idtuto).estudiante.matriculatutori().esta_retirado():
                                    return HttpResponseRedirect("/?info=NO PUEDE ACCEDER AL MODULO ESTA RETIRADO")
                            else:
                                # OCastillo 13-09-2021 se excluyen asignaturas practica y titulacion para carrera Tricologia
                                if inscripcion.carrera.id!=33:
                                    if not ( num >= AsignaturaMalla.objects.filter(malla=inscripcionmalla.malla).exclude(nivelmalla__id=NIVEL_MALLA_CERO).exclude(asignatura__nombre__icontains='TRABAJO DE TITULACI').exclude(asignatura__nombre__icontains='CTICAS PREPROFE').count() - 1 ):
                                        return HttpResponseRedirect('/?info=EL ALUMNO NO CUMPLE LA MALLA')
                                else:
                                    if( num >= AsignaturaMalla.objects.filter(malla=inscripcionmalla.malla).exclude(nivelmalla__id=NIVEL_MALLA_CERO).exclude(asignatura__nivelacion=True).exclude(asignatura__id__in=[650,651]).count() -1) :
                                        pass

                        except:
                            return HttpResponseRedirect("/?info=NO ESTA MATRICULADO ")
                    except:
                        return HttpResponseRedirect("/?info=No tiene Tutorias ")
                    data['egresado'] = 1
                if Tutoria.objects.filter(estudiante__persona__usuario=request.user,estado = True).exists() and 'id' in request.GET:
                    return HttpResponseRedirect("/?info=Error al ingresar al modulo, intentelo nuevamente")
                search = None
                todos = None

                if 's' in request.GET:
                    search = request.GET['s']
                if 't' in request.GET:
                    todos = request.GET['t']
                if search:
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')

                    estudiantetutor = EstudianteTutoria.objects.filter(Q(tutoria__estudiante__persona__nombres__icontains=search)
                                                     |Q(tutoria__estudiante__persona__apellido1__icontains=search)|Q(tutoria__estudiante__persona__apellido2__icontains=search)|Q(tutoria__estudiante__persona__cedula__icontains=search)
                                                     |Q(tutoria__estudiante__persona__pasaporte__icontains=search),tutoria__id=idtuto).order_by('-fecha')

                else:
                    estudiantetutor = EstudianteTutoria.objects.filter(tutoria__id=idtuto).order_by('-fecha')

                paging = MiPaginador(estudiantetutor, 30)
                p = 1
                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                    page = paging.page(p)
                except:
                    page = paging.page(p)

                data['paging'] = paging
                data['rangospaging'] = paging.rangos_paginado(p)
                data['page'] = page
                if 'error' in request.GET:
                    data['error'] = request.GET['error']
                data['search'] = search if search else ""
                data['todos'] = todos if todos else ""
                data['estudiantetutor'] = page.object_list
                data['idtuto'] =Tutoria.objects.get(id=idtuto)
                data['numtutorias'] =len(estudiantetutor)
                data['form'] = ObservacionTutoriaForm()
                data['formtesis']= ArchivoTesisForm()
                return render(request ,"tutoria/profetutoria.html" ,  data)
    except Exception as ex:
        return HttpResponseRedirect("/?info=Error comunicarse con el administrador "+str(ex))

