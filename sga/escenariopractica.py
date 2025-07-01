import json
from datetime import datetime
from django.contrib.auth.decorators import login_required
from decorators import secure_module
from sga.tasks import send_html_mail
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from settings import NIVELMALLA_INICIO_PRACTICA,  EMAIL_ACTIVE, TIPO_ESPECIEVALO_PRACPRE, ID_SOLIC__ONLINE, TIPO_SOLIC__SECRET_PRACPRE, ASIGNATURA_PRACTICAS_SM
from sga.commonviews import addUserData, ip_client_address
from sga.finanzas import generador_especies
from sga.models import EscenarioPractica, Inscripcion, Matricula, InscripcionPracticas, SolicitudPracticas, TipoEspecieValorada, Rubro, SolicitudOnline, SolicitudEstudiante, EspecieGrupo, CoordinacionDepartamento, AsistenteDepartamento, HorarioAsistenteSolicitudes, ProfesorMateria, SupervisorPracticas, RubroEspecieValorada
from django.db.models.aggregates import Sum, Max
from django.contrib.admin.models import LogEntry, ADDITION, DELETION
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_str
__author__ = 'jjurgiles'

@login_required(redirect_field_name='ret', login_url='/login')
# @secure_module
def view(request):
    try:
        if request.method == 'POST':
            action = request.POST['action']
            if action == 'guardaresce':
                try:
                    matricula = Matricula.objects.get(id=request.POST['idmatr'])
                    horas = 0
                    if InscripcionPracticas.objects.filter(inscripcion=matricula.inscripcion).exists():
                        horas = int(InscripcionPracticas.objects.filter(inscripcion=matricula.inscripcion).aggregate(Sum('horas'))['horas__sum'])
                    if int(request.POST['idesc']) == 0:
                        escenariopractica = EscenarioPractica(matricula=matricula,convenio=json.loads(request.POST['escenario']),fecha=datetime.now(),horaspractica=horas)
                        mensaje = 'Guardando '
                    else:
                        escenariopractica = EscenarioPractica.objects.get(id=request.POST['idesc'])
                        escenariopractica.convenio = json.loads(request.POST['escenario'])
                        escenariopractica.fecha = datetime.now()
                        escenariopractica.horaspractica = horas
                        mensaje = 'Editando '

                    # escenariopractica.save()
                    if escenariopractica.convenio:
                        escenariopractica.fechaenvio = datetime.now()
                    escenariopractica.save()
                    if escenariopractica.convenio:
                        if EMAIL_ACTIVE:
                            escenariopractica.mail_envioescenarioconvenio(request.user)
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(escenariopractica).pk,
                        object_id       = escenariopractica.id,
                        object_repr     = force_str(escenariopractica),
                        action_flag     = ADDITION,
                        change_message  = mensaje+' escenario (' + client_address + ')' )
                    return HttpResponse(json.dumps({'result':'ok'}),content_type="application/json")
                except Exception as e:
                    print("error excep escenariopractica guardaresce "+str(e))
                    result = {}
                    result['result'] ="bad"
                    result['mensaje'] ="error al guardar"
                    return HttpResponse(json.dumps(result),content_type="application/json")
            if action == 'delete':
                try:
                    escenariopractica = EscenarioPractica.objects.get(id=request.POST['idesc'])

                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(escenariopractica).pk,
                        object_id       = escenariopractica.id,
                        object_repr     = force_str(escenariopractica),
                        action_flag     = DELETION,
                        change_message  = 'Eliminando escenario (' + client_address + ')' )
                    escenariopractica.delete()
                    return HttpResponse(json.dumps({'result':'ok'}),content_type="application/json")
                except Exception as e:
                    print("error excep escenariopractica delete "+str(e))
                    result = {}
                    result['result'] ="bad"
                    result['mensaje'] ="error al eliminar"
                    return HttpResponse(json.dumps(result),content_type="application/json")
            elif action == 'aprobarsolici':
                result = {}
                try:
                    solicitudpractica = SolicitudPracticas.objects.get(id=request.POST['idsoli'])
                    if not SupervisorPracticas.objects.filter(solicitudpracticas=solicitudpractica, activo=True).exists():
                        return HttpResponse(json.dumps({'result':'bad'}),content_type="application/json")
                    supervisor = SupervisorPracticas.objects.get(solicitudpracticas=solicitudpractica, activo=True)
                    # ////////////////////////////////////////////////////////////////////
                    # ////////////////////////////////////////////////////////////////////
                    tipoEspecie = TipoEspecieValorada.objects.get(pk=TIPO_ESPECIEVALO_PRACPRE)
                    inscripcion = solicitudpractica.escenariopractica.matricula.inscripcion

                    rubro = Rubro(fecha=datetime.now(),
                                valor=tipoEspecie.precio,
                                inscripcion = inscripcion,
                                cancelado=tipoEspecie.precio==0,
                                fechavence=datetime.now())
                    rubro.save()

                    solicitud = SolicitudOnline.objects.filter(pk=ID_SOLIC__ONLINE)[:1].get()
                    solicitudest = SolicitudEstudiante(solicitud=solicitud,
                                                       inscripcion=inscripcion,
                                                       observacion=str('SOLICITUD GENERADA DE PRACTICAS PRE-PROFESIONALES'),
                                                       tipoe_id=tipoEspecie.id,
                                                       correo=inscripcion.persona.emailinst,
                                                       celular=inscripcion.persona.telefono,
                                                       fecha=datetime.now())
                    solicitudest.save()
                    solicitudest.rubro = rubro
                    solicitudest.solicitado=True
                    solicitudest.save()

                    # Rubro especie valorada
                    # rubroenot = generador_especies.generar_especie(rubro=rubro, tipo=tipoEspecie)
                    serie = 0
                    valor = RubroEspecieValorada.objects.filter(rubro__fecha__year=rubro.fecha.year).aggregate(Max('serie'))
                    if valor['serie__max']!=None:
                        serie = valor['serie__max']+1

                    if not RubroEspecieValorada.objects.filter(rubro__fecha__year=rubro.fecha.year,serie=serie).exists():
                        rubroenot = RubroEspecieValorada(rubro=rubro, tipoespecie=tipoEspecie, serie=serie, usrasig=supervisor.profesormateria.profesor.persona.usuario, fechaasigna = datetime.now())
                        rubroenot.save()

                    rubroenot.autorizado=False
                    rubroenot.save()
                    # ///////////////////////////////////////////////////////////////
                    # ///////////////////////////////////////////////////////////////
                    iddepartamentoesp = EspecieGrupo.objects.filter(tipoe__id=TIPO_ESPECIEVALO_PRACPRE).values('departamento').distinct('departamento')
                    iddepartamento =  CoordinacionDepartamento.objects.filter(departamento__id__in = iddepartamentoesp,coordinacion__carrera=solicitudpractica.matricula.inscripcion.carrera).values('departamento').distinct('departamento')
                    idusuario = AsistenteDepartamento.objects.filter(departamento__id__in=iddepartamento).values('persona__usuario').distinct('persona__usuario')
                    if HorarioAsistenteSolicitudes.objects.filter(fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time(),usuario__id__in=idusuario).exists():
                        horarioasis = HorarioAsistenteSolicitudes.objects.filter(fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time(),usuario__id__in=idusuario).exclude(nolabora=True).order_by('sinatender')[:1].get()
                        asistentes = AsistenteDepartamento.objects.filter(persona__usuario=horarioasis.usuario).exclude(puedereasignar=True).order_by('cantidadsol')[:1].get()
                        if asistentes:
                            rubroenot.usrasig = asistentes.persona.usuario
                            rubroenot.departamento = asistentes.departamento
                            asistentes.cantidad =asistentes.cantidad +1
                            rubroenot.fechaasigna = datetime.now()
                            # rubroenot.save()
                            # asistentes.save()
                            lista = str(asistentes.persona.email)
                            hoy = datetime.now().today()
                            contenido = "  Tramites Asignados"
                            descripcion = "Ud. tiene tramites por atender"
                            send_html_mail(contenido,
                                "emails/notificacion_tramites_adm.html", {'fecha': hoy,'contenido': contenido,'descripcion':descripcion,'opcion':'1'},lista.split(','))
                    # ///////////////////////////////////////////////////////////////
                    # ///////////////////////////////////////////////////////////////

                    solicitudpractica.rubroespecie = rubroenot
                    solicitudpractica.solicitudestudiante = solicitudest
                    solicitudpractica.save()
                    result['mens'] ="Aprobada"

                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(solicitudpractica).pk,
                        object_id       = solicitudpractica.id,
                        object_repr     = force_str(solicitudpractica),
                        action_flag     = ADDITION,
                        change_message  = 'Generado especie practica sin convenio (' + client_address + ')' )

                    result['result'] ="ok"

                    result['idsol'] =solicitudpractica.id
                    return HttpResponse(json.dumps(result),content_type="application/json")
                except Exception as e:
                    print("error excep aprobarsolici soli "+str(e))
                    result['result'] ="bad"
                    result['mensaje'] ="error al guardar la informacion"
                    return HttpResponse(json.dumps(result),content_type="application/json")
            # if action == 'enviarescenar':
            #     try:
            #         escenariopractica = EscenarioPractica.objects.get(id=request.POST['idescen'])
            #         if not EspecieGrupo.objects.filter(tipoe__id=TIPO_ESPECIEVALO_PRACPRE).exists():
            #             return HttpResponse(json.dumps({'result':'bad','mensaje':'No se puede ingresar el escenario contactese con el administrador'}),content_type="application/json")
            #         iddepartamentoesp = EspecieGrupo.objects.filter(tipoe__id=TIPO_ESPECIEVALO_PRACPRE).values('departamento').distinct('departamento')
            #         iddepartamento =  CoordinacionDepartamento.objects.filter(departamento__id__in = iddepartamentoesp,coordinacion__carrera=escenariopractica.matricula.inscripcion.carrera).values('departamento').distinct('departamento')
            #         idusuario = AsistenteDepartamento.objects.filter(departamento__id__in=iddepartamento).values('persona__usuario').distinct('persona__usuario')
            #         horarioasis = ''
            #         mensaje = 'El escenario de practica fue enviado, pronto un asistente le antendera'
            #         if HorarioAsistenteSolicitudes.objects.filter(fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time(),usuario__id__in=idusuario).exists():
            #             horarioasis = HorarioAsistenteSolicitudes.objects.filter(fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time(),usuario__id__in=idusuario).exclude(nolabora=True).order_by('sinatender')[:1].get()
            #             asistenten = AsistenteDepartamento.objects.filter(persona__usuario=horarioasis.usuario)[:1].get()
            #             mensaje = 'El escenario de practica fue enviado, el asistente '+ str(asistenten.persona.nombre_completo())+' lo atendera'
            #         escenariohorario = SolicitudHorarioAsistente(escenario = escenariopractica,
            #                                                     fecha = datetime.now(),
            #                                                     obsestud = request.POST['observacion'])
            #         if horarioasis:
            #             escenariohorario.horario = horarioasis
            #             horarioasis.sinatender = horarioasis.sinatender + 1
            #             horarioasis.save()
            #             escenariohorario.fechaasig = datetime.now()
            #             if EMAIL_ACTIVE:
            #                 escenariohorario.mail_escenariohorarioasis(request.user)
            #         escenariohorario.save()
            #         escenariopractica.fechaenvio = datetime.now()
            #         escenariopractica.save()
            #         client_address = ip_client_address(request)
            #         LogEntry.objects.log_action(
            #             user_id         = request.user.pk,
            #             content_type_id = ContentType.objects.get_for_model(escenariohorario).pk,
            #             object_id       = escenariohorario.id,
            #             object_repr     = force_str(escenariohorario),
            #             action_flag     = ADDITION,
            #             change_message  = 'Agregado escenario horario  (' + client_address + ')' )
            #         return HttpResponse(json.dumps({'result':'ok','mensaje':mensaje}),content_type="application/json")
            #
            #     except Exception as e:
            #         print("error excep escenariopractica enviarescenar "+str(e))
            #         result = {}
            #         result['result'] ="bad"
            #         result['mensaje'] ="error al enviar vuelva a intentarlo"
            #         return HttpResponse(json.dumps(result),content_type="application/json")
        else:
            data = {'title': 'Escenario Practica'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']
                if action=='versolnoapor':
                    persona = data['persona']
                    data = {}
                    escenariopractica = EscenarioPractica.objects.filter(id=request.GET['id'])[:1].get()
                    data['solicitudpracticas'] = SolicitudPracticas.objects.filter(escenariopractica=escenariopractica,aprobada=False).exclude(fecaprobada=None)
                    data['escenariopractica'] = escenariopractica
                    data['persona'] = persona
                    return render(request ,"solicitudpractica/vergestion.html" ,  data)
                if action=='versolictudnoacep':
                    persona = data['persona']
                    data = {}
                    escenariopractica = EscenarioPractica.objects.filter(id=request.GET['id'])[:1].get()
                    data['solictudnoaceptada'] = escenariopractica.tiene_solinoaceptada()
                    data['escenariopractica'] = escenariopractica
                    data['persona'] = persona
                    return render(request ,"solicitudpractica/vergestion.html" ,  data)
            else:
                inscripcion = Inscripcion.objects.filter(persona=data['persona'])[:1].get()
                if not inscripcion.carrera.practica:
                    return HttpResponseRedirect("/?info= No tiene acceso a este modulo")
                escenariopractica = EscenarioPractica.objects.filter(matricula__inscripcion=inscripcion)
                data['escenariopractica'] = escenariopractica
                data['inscripcion'] = inscripcion
                if 'info' in request.GET:
                    if request.GET['info'] == '1':
                        data['info'] = "No esta Matriculado"
                    if request.GET['info'] == '2':
                        data['info'] = "No se encuentra en el nivel para iniciar las practicas"
                    if request.GET['info'] == '3':
                        data['info'] = "No tiene una especie de solicitud de practicas registrada"
                if inscripcion.matricula():
                    matricula = inscripcion.matricula()
                    data['matricula'] = matricula
                    if not EscenarioPractica.objects.filter(matricula=inscripcion.matricula()).exists() and matricula.nivel.nivelmalla.orden >= NIVELMALLA_INICIO_PRACTICA:
                        data['nuevoescenario'] = True
                return render(request ,"solicitudpractica/escenariopractica.html" ,  data)
    except Exception as e:
        print("Error en escenariopractica"+str(e))
        return HttpResponseRedirect("/?info=Error comuniquese con el administrador")