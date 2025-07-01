import json
import os
from datetime import datetime
from django.contrib.auth.decorators import login_required
from sga.tasks import send_html_mail
from django.db.models.query_utils import Q
from decimal import Decimal
from django.db.models.aggregates import Sum, Max
from settings import MEDIA_ROOT, NIVELMALLA_INICIO_PRACTICA, HORAS_MAX_LABORA, TIPO_ESPECIEVALO_PRACPRE, ID_REPORTE_CARTA_COMPROM, EMAIL_ACTIVE, TIPO_SOLIC__SECRET_PRACPRE, ID_SOLIC__ONLINE, HORAS_MIN_PRACTICAS, PUNTAJE_APRUEBA_PRACTICA, ID_REPORTE_CERTI_PRACTIC, ASIGNATURA_PRACTICAS_SM
from sga.commonviews import addUserData, ip_client_address
from django.shortcuts import render
from django.template import RequestContext
from sga.finanzas import generador_especies
from sga.models import Inscripcion, SolicitudPracticas, EmpresaSinConvenio, ExperienciaLaboral, FichaReceptora, RegistroActividad, RubroEspecieValorada, ReportePracticas, EscenarioPractica, TutorEntidadRecep, EvaluacionSupervisorEmp, SegmentoIndicadorEmp, PuntajeIndicador, ProcesoSelecDetalle, SolictudNoAceptada, TipoEspecieValorada, Rubro, SolicitudOnline, SolicitudEstudiante, ReportePractSolicitud, EspecieGrupo, CoordinacionDepartamento, AsistenteDepartamento, HorarioAsistenteSolicitudes, SolicitudHorarioAsistente, TipoSolicitudSecretariaDocente, SolicitudSecretariaDocente, SolicitudesGrupo, ModuloGrupo, SegmentoDetalle, SupervisorPracticas, ProfesorMateria
from django.contrib.admin.models import LogEntry, ADDITION,DELETION,CHANGE
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_str
from django.http import HttpResponse, HttpResponseRedirect

__author__ = 'jjurgiles'


@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method == 'POST':
            action = request.POST['action']
            if action == 'editinscripcion':
                result = {}
                try:
                    inscripcion = Inscripcion.objects.get(id=request.POST['idinscr'])
                    mensaje = ''
                    if request.POST['opc'] == 'direccion1':
                        inscripcion.persona.direccion = request.POST['dato']
                        mensaje = 'Direccion Principal Ingresada con exito'
                    elif request.POST['opc'] == 'direccion2':
                        inscripcion.persona.direccion2 = request.POST['dato']
                        mensaje = 'Direccion Secundaria Ingresada con exito'
                    elif request.POST['opc'] == 'numdom':
                        inscripcion.persona.num_direccion = request.POST['dato']
                        mensaje = 'Numero de domicilio Ingresado con exito'
                    elif request.POST['opc'] == 'telefonogen':
                        inscripcion.persona.telefono_conv = request.POST['dato']
                        mensaje = 'Telefono convencional Ingresado con exito'
                    elif request.POST['opc'] == 'celulargen':
                        inscripcion.persona.telefono = request.POST['dato']
                        mensaje = 'Celular Ingresado con exito'
                    elif request.POST['opc'] == 'emailgen':
                        inscripcion.persona.email = request.POST['dato']
                        mensaje = 'Email Ingresado con exito'
                    inscripcion.persona.save()
                    client_address = ip_client_address(request)

                    LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(inscripcion.persona).pk,
                    object_id       = inscripcion.persona.id,
                    object_repr     = force_str(inscripcion.persona),
                    action_flag     = CHANGE,
                    change_message  = 'Editando informacion de persona (' + client_address + ')' )

                    result['result'] = 'ok'
                    result['mensaje'] = mensaje
                    return HttpResponse(json.dumps(result),content_type="application/json")

                except Exception as e:
                    print("error excep editinscripcion soli "+str(e))
                    result['result'] ="bad"
                    return HttpResponse(json.dumps(result),content_type="application/json")
            elif action == 'guardararchiv':
                result = {}
                try:
                    inscripcion = Inscripcion.objects.get(id=request.POST['idins'])
                    escenariopractica = EscenarioPractica.objects.get(id=request.POST['idesc'])
                    if inscripcion.matricula():
                        if inscripcion.matricula().nivel.nivelmalla.orden >= NIVELMALLA_INICIO_PRACTICA:
                            if int(request.POST['idsoliprac']) > 0:
                                solicitudpractica = SolicitudPracticas.objects.get(id=request.POST['idsoliprac'])
                                mensaje = 'Registro editado exitosamente'
                            else:
                                matricula = inscripcion.matricula()

                                solicitudpractica = SolicitudPracticas(matricula = matricula,
                                                            escenariopractica = escenariopractica,
                                                            fecha = datetime.now(),
                                                            promedionota = inscripcion.calculopromedio()
                                                            )
                                solicitudpractica.save()

                                mensaje = 'Registro ingresado exitosamente'
                            if 'archivo' in request.FILES:
                                if solicitudpractica.foto:
                                    if os.path.exists(MEDIA_ROOT+'/'+str(solicitudpractica.foto)):
                                        os.remove(MEDIA_ROOT+'/'+str(solicitudpractica.foto))
                                solicitudpractica.foto = request.FILES['archivo']
                                solicitudpractica.save()
                            client_address = ip_client_address(request)

                            LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(solicitudpractica).pk,
                            object_id       = solicitudpractica.id,
                            object_repr     = force_str(solicitudpractica),
                            action_flag     = CHANGE,
                            change_message  = 'Creando o editando Solicitud de practica (' + client_address + ')' )

                            result['result'] = 'ok'
                            result['idsoli'] = solicitudpractica.id
                            result['mensaje'] = mensaje
                            return HttpResponse(json.dumps(result),content_type="application/json")
                        result['result'] = 'bad'
                        result['mensaje'] = "No se encuentra en el nivel para iniciar las practicas"
                        return HttpResponse(json.dumps(result),content_type="application/json")
                    result['result'] ="bad"
                    result['mensaje'] ="No esta matriculado"
                    return HttpResponse(json.dumps(result),content_type="application/json")
                except Exception as e:
                    print("error excep editinscripcion soli "+str(e))
                    result['result'] ="bad"
                    result['mensaje'] ="error al guardar la imagen"
                    return HttpResponse(json.dumps(result),content_type="application/json")
            elif "buscarempresa" == action:
                result = {}
                try:
                    if EmpresaSinConvenio.objects.filter(ruc=request.POST['ruc']).exists():
                        empresa =  EmpresaSinConvenio.objects.filter(ruc=request.POST['ruc'])[:1].get()
                        result['result'] ="ok"
                        result['mensaje'] = empresa.nombre
                        result['idempresasin'] = empresa.id
                        result['actividad'] = empresa.activideconomica
                        result['direccion'] = empresa.direccion
                        result['provincia'] = empresa.ciudad.provincia.nombre
                        result['idprov'] = empresa.ciudad.provincia.id
                        result['ciudad'] = empresa.ciudad.nombre
                        result['idciu'] = empresa.ciudad.id
                    else:
                        result['result'] ="noexiste"
                    return HttpResponse(json.dumps(result),content_type="application/json")
                except Exception as e:
                    print("error excep buscarempresa soli "+str(e))
                    result['result'] ="bad"
                    result['mensaje'] ="error al buscar la empresa"
                    return HttpResponse(json.dumps(result),content_type="application/json")
            elif "guardarempresa" == action:
                result = {}
                try:
                    if not EmpresaSinConvenio.objects.filter(ruc=request.POST['ruc']).exists():
                        empresa =  EmpresaSinConvenio(nombre = request.POST['nomempres'],
                                                    ruc = request.POST['ruc'],
                                                    activideconomica = request.POST['actempre'],
                                                    direccion = request.POST['direcemp'],
                                                    ciudad_id = request.POST['idciudaemp'])
                        empresa.save()

                        result['result'] ="ok"
                        client_address = ip_client_address(request)

                        LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(empresa).pk,
                        object_id       = empresa.id,
                        object_repr     = force_str(empresa),
                        action_flag     = ADDITION,
                        change_message  = 'Creando empresa sin convenio (' + client_address + ')' )
                    else:
                        result['result'] ="bad"
                        result['mensaje'] ="La empresa ya se encuentra registrada"
                    return HttpResponse(json.dumps(result),content_type="application/json")
                except Exception as e:
                    print("error excep guardarempresa soli "+str(e))
                    result['result'] ="bad"
                    result['mensaje'] ="error al guardar la informacion"
                    return HttpResponse(json.dumps(result),content_type="application/json")
            elif "guardarexplab" == action:
                result = {}
                try:
                    datos = json.loads(request.POST['datos'])
                    if int(datos['idsolicitudprac']) > 0:
                        solicitudpractica = SolicitudPracticas.objects.get(id=datos['idsolicitudprac'])
                    else:
                        escenariopractica = EscenarioPractica.objects.get(id=request.POST['idesc'])
                        inscripcion = Inscripcion.objects.get(id=datos['idinscripcion'])
                        matricula = inscripcion.matricula()

                        solicitudpractica = SolicitudPracticas(matricula = matricula,
                                                    escenariopractica = escenariopractica,
                                                    fecha = datetime.now(),
                                                    promedionota = inscripcion.calculopromedio())
                        solicitudpractica.save()
                    idexlab = []
                    for experlabo in datos['experlabo']:

                        if int(experlabo['idexplab']) > 0:
                            idexlab.append(experlabo['idexplab'])
                            experiencialaboral = ExperienciaLaboral.objects.get(id=experlabo['idexplab'])
                        else:
                            experiencialaboral = ExperienciaLaboral(solicitudpracticas = solicitudpractica)

                        if experlabo['convenio']:
                            experiencialaboral.convenio_id = experlabo['empresid']
                            experiencialaboral.sinconvenio_id = None
                        else:
                            experiencialaboral.convenio  = None
                            experiencialaboral.sinconvenio_id = experlabo['empresid']
                        experiencialaboral.tiempo = experlabo['tiempo']
                        experiencialaboral.funcion = experlabo['funcion']
                        experiencialaboral.save()
                        idexlab.append(experiencialaboral.id)
                    if idexlab:
                        experlaborales = ExperienciaLaboral.objects.filter(solicitudpracticas=solicitudpractica).exclude(id__in=idexlab)
                        if experlaborales:
                            experlaborales.delete()
                    client_address = ip_client_address(request)

                    LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(solicitudpractica).pk,
                    object_id       = solicitudpractica.id,
                    object_repr     = force_str(solicitudpractica),
                    action_flag     = ADDITION,
                    change_message  = 'Ingreso de experiencia laboral (' + client_address + ')' )
                    result['result'] ="ok"
                    result['idsol'] =solicitudpractica.id
                    return HttpResponse(json.dumps(result),content_type="application/json")
                except Exception as e:
                    print("error excep guardarempresa soli "+str(e))
                    result['result'] ="bad"
                    result['mensaje'] ="error al guardar la informacion"
                    return HttpResponse(json.dumps(result),content_type="application/json")
            elif "guardarfichrecp" == action:
                result = {}
                try:
                    datos = json.loads(request.POST['datos'])
                    if int(datos['solicitudid']) > 0:
                        solicitudpractica = SolicitudPracticas.objects.get(id=datos['solicitudid'])
                    else:
                        escenariopractica = EscenarioPractica.objects.get(id=request.POST['idesc'])
                        inscripcion = Inscripcion.objects.get(id=datos['idinscripcion'])
                        matricula = inscripcion.matricula()
                        # if RubroEspecieValorada.objects.filter(id=escenariopractica.rubroespecievalorada.id,rubro__cancelado=True,aplicada=True).exists():
                        #     rubrespecie =  RubroEspecieValorada.objects.filter(id=escenariopractica.rubroespecievalorada.id,rubro__cancelado=True,aplicada=True)[:1].get()
                        solicitudpractica = SolicitudPracticas(matricula = matricula,
                                                    escenariopractica = escenariopractica,
                                                    fecha = datetime.now(),
                                                    promedionota = inscripcion.calculopromedio())
                        solicitudpractica.save()
                        # else:
                        #     result['result'] ="bad"
                        #     result['mensaje'] ="No hay especie registrada para la solicitud de practias"
                        #     return HttpResponse(json.dumps(result),content_type="application/json")
                    empresa = None
                    if int(datos['idempresa']) > 0:
                        empresa = EmpresaSinConvenio.objects.get(id=datos['idempresa'])
                    else:
                        for em in datos['empresa']:
                            if EmpresaSinConvenio.objects.filter(ruc = em['ruc']).exists():
                                empresa = EmpresaSinConvenio.objects.filter(ruc = em['ruc'])[:1].get()
                            else:
                                empresa =  EmpresaSinConvenio(ruc = em['ruc'])
                            empresa.nombre = em['entidadrec']
                            empresa.ruc = em['ruc']
                            empresa.activideconomica = em['actividaent']
                            empresa.direccion = em['direccionent']
                            empresa.ciudad_id = em['ciudadrec']
                            empresa.save()
                    mensaje = ''
                    for info in datos['informacion']:
                        if int(datos['fichrecepid']) == 0:
                            fichareceptora = FichaReceptora(solicitudpracticas = solicitudpractica,
                                                            sinconvenio = empresa,
                                                            inicio = info['feinicio'],
                                                            fin = info['fefin'],
                                                            horaspracticas = info['horas'],
                                                            horainicio = info['hini'],
                                                            horafin = info['hfin'],
                                                            supervisor = info['nomtutot'],
                                                            correo = info['emailtut'],
                                                            cargo = info['cargotut'],
                                                            cantidad = info['numprac'])
                            mensaje = 'Ingreso de Ficha de Entidad Receptora'
                        else:
                            fichareceptora = FichaReceptora.objects.get(id=datos['fichrecepid'])
                            fichareceptora.sinconvenio = empresa
                            fichareceptora.inicio = info['feinicio']
                            fichareceptora.fin = info['fefin']
                            fichareceptora.horaspracticas = info['horas']
                            fichareceptora.horainicio = info['hini']
                            fichareceptora.horafin = info['hfin']
                            fichareceptora.supervisor = info['nomtutot']
                            fichareceptora.correo = info['emailtut']
                            fichareceptora.cargo = info['cargotut']
                            fichareceptora.cantidad = info['numprac']
                            mensaje = 'Editando de Ficha de Entidad Receptora'
                        if not TutorEntidadRecep.objects.filter(correo=info['emailtut'],sinconvenio=empresa).exists():
                            tutorentidadrecep = TutorEntidadRecep(sinconvenio = empresa,
                                                                  correo = info['emailtut'])
                        else:
                            tutorentidadrecep = TutorEntidadRecep.objects.filter(correo=info['emailtut'],sinconvenio=empresa)[:1].get()

                        tutorentidadrecep.supervisor = info['nomtutot']
                        if info['celularrec'] != '':
                            tutorentidadrecep.celular = info['celularrec']
                        if info['convencional']:
                            tutorentidadrecep.telefono = info['convencional']
                        if info['extensionrec']:
                            tutorentidadrecep.extension = info['extensionrec']
                        #delsupervisor
                        tutorentidadrecep.cargo = info['cargotut']
                        tutorentidadrecep.save()
                        if info['celularrec'] != '':
                            fichareceptora.celular = info['celularrec']
                        if info['convencional']:
                            fichareceptora.telefono = info['convencional']
                        if info['extensionrec']:
                            fichareceptora.extension = info['extensionrec']
                        for jor in datos['jornadalab']:
                            fichareceptora.lunes = jor['lunes']
                            fichareceptora.martes = jor['martes']
                            fichareceptora.miercoles = jor['miercoles']
                            fichareceptora.jueves = jor['jueves']
                            fichareceptora.viernes = jor['viernes']
                            fichareceptora.sabado = jor['sabado']
                            fichareceptora.domingo = jor['domingo']
                        fichareceptora.save()
                    client_address = ip_client_address(request)

                    LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(solicitudpractica).pk,
                    object_id       = solicitudpractica.id,
                    object_repr     = force_str(solicitudpractica),
                    action_flag     = ADDITION,
                    change_message  = mensaje+' (' + client_address + ')' )
                    result['result'] ="ok"
                    result['idsol'] =solicitudpractica.id
                    return HttpResponse(json.dumps(result),content_type="application/json")
                except Exception as e:
                    print("error excep guardar ficha receptora "+str(e))
                    result['result'] ="bad"
                    result['mensaje'] ="error al guardar la informacion"
                    return HttpResponse(json.dumps(result),content_type="application/json")

            elif "guardarregact" == action:
                result = {}
                try:
                    datos = json.loads(request.POST['datos'])
                    solicitudpractica = SolicitudPracticas.objects.get(id=datos['idsolicitudprac'])

                    idreg = []
                    for regprac in datos['registroprac']:

                        if int(regprac['idregact']) > 0:
                            idreg.append(regprac['idregact'])
                            registroactividad = RegistroActividad.objects.get(id=regprac['idregact'])
                            mensaje = 'Ingreso de registrod e actividades '
                        else:
                            registroactividad = RegistroActividad(solicitudpracticas = solicitudpractica)
                            mensaje = 'Edicion de Ficha de Entidad Receptora'

                        registroactividad.fecha = regprac['fechregact']
                        registroactividad.actividad = regprac['actividadreg']
                        registroactividad.observacion = regprac['observacionreg']
                        registroactividad.inicio = regprac['hinicioreg']
                        registroactividad.fin = regprac['hfinreg']
                        registroactividad.save()
                        idreg.append(registroactividad.id)

                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(registroactividad).pk,
                            object_id       = registroactividad.id,
                            object_repr     = force_str(registroactividad),
                            action_flag     = ADDITION,
                            change_message  = mensaje+' (' + client_address + ')' )
                    if idreg:
                        registroactividades = RegistroActividad.objects.filter(solicitudpracticas=solicitudpractica).exclude(id__in=idreg)
                        if registroactividades:
                            registroactividades.delete()


                    result['result'] ="ok"
                    result['idsol'] =solicitudpractica.id
                    return HttpResponse(json.dumps(result),content_type="application/json")
                except Exception as e:
                    print("error excep guardarempresa soli "+str(e))
                    result['result'] ="bad"
                    result['mensaje'] ="error al guardar la informacion"
                    return HttpResponse(json.dumps(result),content_type="application/json")

            # elif "enviarsolicict" == action:
            #     result = {}
            #     try:
            #         solicitudpractica = SolicitudPracticas.objects.get(id=request.POST['idsoli'])
            #         # ///////////////////////////////////HORARIO ASISTENTE /////////////////////////////////////////////////////////////////////////
            #         if not EspecieGrupo.objects.filter(tipoe__id=TIPO_SOLIC__SECRET_PRACPRE).exists():
            #             return HttpResponse(json.dumps({'result':'bad','mensaje':'No se puede ingresar el escenario contactese con el administrador'}),content_type="application/json")
            #         iddepartamentoesp = EspecieGrupo.objects.filter(tipoe__id=TIPO_SOLIC__SECRET_PRACPRE).values('departamento').distinct('departamento')
            #         iddepartamento =  CoordinacionDepartamento.objects.filter(departamento__id__in = iddepartamentoesp,coordinacion__carrera=solicitudpractica.matricula.inscripcion.carrera).values('departamento').distinct('departamento')
            #         idusuario = AsistenteDepartamento.objects.filter(departamento__id__in=iddepartamento).values('persona__usuario').distinct('persona__usuario')
            #         horarioasis = ''
            #         mensaje = 'La Solicitud de practica fue enviado, pronto un asistente le antendera'
            #
            #         tipoespecie = TipoEspecieValorada.objects.get(pk=TIPO_SOLIC__SECRET_PRACPRE)
            #         solicitudonline = SolicitudOnline.objects.get(pk=ID_SOLIC__ONLINE)
            #         solicitudest = SolicitudEstudiante(solicitud=solicitudonline,
            #                                                       inscripcion=solicitudpractica.matricula.inscripcion,
            #                                                       observacion="SOLICITUD DE APROBACION DE PRACTICA PREPROFESIONAL",
            #                                                       tipoe = tipoespecie,
            #                                                       correo=solicitudpractica.matricula.inscripcion.persona.email,
            #                                                       celular=solicitudpractica.matricula.inscripcion.persona.telefono,
            #                                                       fecha=datetime.now())
            #         solicitudest.save()
            #         solicitud = SolicitudSecretariaDocente(solicitudestudiante=solicitudest,
            #                                                persona=solicitudpractica.matricula.inscripcion.persona,
            #                                                tipo=tipoespecie.tiposolicitud,
            #                                                descripcion="SOLICITUD DE APROBACION DE PRACTICA PREPROFESIONAL",
            #                                                fecha = datetime.now(),
            #                                                hora = datetime.now().time(),
            #                                                cerrada = False)
            #
            #         solicitud.save()
            #         asistenten = ""
            #         if HorarioAsistenteSolicitudes.objects.filter(fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time(),usuario__id__in=idusuario).exists():
            #             horarioasis = HorarioAsistenteSolicitudes.objects.filter(fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time(),usuario__id__in=idusuario).exclude(nolabora=True).order_by('sinatender')[:1].get()
            #             asistenten = AsistenteDepartamento.objects.filter(persona__usuario=horarioasis.usuario).exclude(puedereasignar=True).order_by('cantidadsol')[:1].get()
            #             mensaje = 'La Solicitud de practica fue enviado, el asistente '+ str(asistenten.persona.nombre_completo())+' lo atendera'
            #         solicitudhorario = SolicitudHorarioAsistente(solicitud = solicitudpractica,
            #                                                     fecha = datetime.now(),
            #                                                     obsestud = "SOLICITUD DE PRACTICA PREPROFESIONAL")
            #         if horarioasis:
            #             solicitudhorario.horario = horarioasis
            #             horarioasis.sinatender = horarioasis.sinatender + 1
            #             horarioasis.save()
            #             solicitudhorario.fechaasig = datetime.now()
            #             if EMAIL_ACTIVE:
            #                 solicitudhorario.mail_escenariohorarioasis(request.user)
            #         solicitudhorario.save()
            #         solicitudpractica.escenariopractica.fechaenvio = datetime.now()
            #         solicitudpractica.escenariopractica.save()
            #         solicitudpractica.fechaenvio = datetime.now()
            #         solicitudpractica.fechaacepta = datetime.now()
            #         solicitudpractica.acepto = True
            #         solicitudpractica.enviada = True
            #         solicitudpractica.save()
            #         if asistenten:
            #             asistenten.cantidadsol =asistenten.cantidadsol +1
            #             solicitud.usuario = asistenten.persona.usuario
            #             solicitud.personaasignada =asistenten.persona
            #             solicitud.asignado=True
            #             solicitud.fechaasignacion = datetime.now()
            #             solicitud.departamento = asistenten.departamento
            #             solicitud.usuarioasigna=asistenten.persona.usuario
            #             solicitud.save()
            #             asistenten.save()
            #
            #         solicitudpractica.solicitudsecretaria = solicitud
            #         solicitudpractica.save()
            #         if EMAIL_ACTIVE:
            #             lista = str(solicitud.persona.email)
            #             hoy = datetime.now().today()
            #             contenido = "Nueva Solicitud"
            #             descripcion = "Estimado/a estudiante. Su solicitud ha sido recibida. Sera asignada al Departamento correspondiente. Puede ver el estado de la misma en el Sistema."
            #             send_html_mail(contenido,
            #                 "emails/nuevasolicitud.html", {'d': solicitud, 'fecha': hoy,'contenido': contenido,'descripcion':descripcion,'opcion':'1'},lista.split(','))
            #
            #         # //////////////////////////////////////////////////////////////////
            #         # //////////////////////////////////////////////////////////////////
            #         solicitudpractica.mail_enviosolpract(request.user)
            #         client_address = ip_client_address(request)
            #         LogEntry.objects.log_action(
            #             user_id         = request.user.pk,
            #             content_type_id = ContentType.objects.get_for_model(solicitudpractica).pk,
            #             object_id       = solicitudpractica.id,
            #             object_repr     = force_str(solicitudpractica),
            #             action_flag     = ADDITION,
            #             change_message  = 'Solicitud Enviada (' + client_address + ')' )
            #
            #         result['result'] ="ok"
            #         result['idsol'] =solicitudpractica.id
            #         result['mensaje'] = mensaje
            #         return HttpResponse(json.dumps(result),content_type="application/json")
            #     except Exception as e:
            #         print("error excep enviarsolicict soli "+str(e))
            #         result['result'] ="bad"
            #         result['mensaje'] ="error al guardar la informacion"
            #         return HttpResponse(json.dumps(result),content_type="application/json")


            elif "enviarsolicict" == action:
                print(request.POST)
                result = {}
                try:
                    solicitudpractica = SolicitudPracticas.objects.get(id=request.POST['idsoli'])
                    # ///////////////////////////////////HORARIO ASISTENTE /////////////////////////////////////////////////////////////////////////
                    if not EspecieGrupo.objects.filter(tipoe__id=TIPO_SOLIC__SECRET_PRACPRE).exists():
                        return HttpResponse(json.dumps({'result':'bad','mensaje':'No se puede ingresar el escenario contactese con el administrador'}),content_type="application/json")
                    if not ProfesorMateria.objects.filter(materia__asignatura=ASIGNATURA_PRACTICAS_SM, materia__nivel=solicitudpractica.matricula.nivel).exists():
                        return HttpResponse(json.dumps({'result':'bad','mensaje':'No existe supervisor de practicas, Comuniquese con el coordinador'}),content_type="application/json")
                    else:
                        prof = ProfesorMateria.objects.filter(materia__asignatura=ASIGNATURA_PRACTICAS_SM, materia__nivel=solicitudpractica.matricula.nivel).order_by('-id')[:1].get()
                        if SupervisorPracticas.objects.filter(profesormateria=prof, solicitudpracticas=solicitudpractica, activo=True).exists():
                            supervisor = SupervisorPracticas.objects.get(profesormateria=prof, solicitudpracticas=solicitudpractica, activo=True)
                        else:
                            supervisor = SupervisorPracticas(profesormateria=prof,
                                                             solicitudpracticas=solicitudpractica,
                                                             desde=datetime.now().date(),
                                                             activo=True)
                            supervisor.save()
                            supervisores = SupervisorPracticas.objects.filter(solicitudpracticas=solicitudpractica, activo=True).exclude(pk=supervisor.id)
                            for s in supervisores:
                                s.activo=False
                                s.save()

                    mensaje = 'La Solicitud de practica fue enviado, pronto un asistente le antendera'

                    tipoespecie = TipoEspecieValorada.objects.get(pk=TIPO_SOLIC__SECRET_PRACPRE)
                    solicitudonline = SolicitudOnline.objects.get(pk=ID_SOLIC__ONLINE)
                    solicitudest = SolicitudEstudiante(solicitud=solicitudonline,
                                                                  inscripcion=solicitudpractica.matricula.inscripcion,
                                                                  observacion="SOLICITUD DE APROBACION DE PRACTICA PREPROFESIONAL",
                                                                  tipoe = tipoespecie,
                                                                  correo=solicitudpractica.matricula.inscripcion.persona.email,
                                                                  celular=solicitudpractica.matricula.inscripcion.persona.telefono,
                                                                  fecha=datetime.now())
                    solicitudest.save()
                    solicitud = SolicitudSecretariaDocente(solicitudestudiante=solicitudest,
                                                           persona=solicitudpractica.matricula.inscripcion.persona,
                                                           tipo=tipoespecie.tiposolicitud,
                                                           descripcion="SOLICITUD DE APROBACION DE PRACTICA PREPROFESIONAL",
                                                           fecha = datetime.now(),
                                                           hora = datetime.now().time(),
                                                           cerrada = False,
                                                           usuario = supervisor.profesormateria.profesor.persona.usuario,
                                                           personaasignada = supervisor.profesormateria.profesor.persona,
                                                           asignado=True,
                                                           fechaasignacion = datetime.now(),
                                                           usuarioasigna = supervisor.profesormateria.profesor.persona.usuario)

                    solicitud.save()
                    asistenten = ""
                    mensaje = 'La Solicitud de practica fue enviado, al supervisor docente '+ str(supervisor.profesormateria.profesor.persona.nombre_completo())

                    solicitudpractica.escenariopractica.fechaenvio = datetime.now()
                    solicitudpractica.escenariopractica.save()
                    solicitudpractica.fechaenvio = datetime.now()
                    solicitudpractica.fechaacepta = datetime.now()
                    solicitudpractica.acepto = True
                    solicitudpractica.enviada = True
                    solicitudpractica.save()

                    solicitudpractica.solicitudsecretaria = solicitud
                    solicitudpractica.save()
                    if EMAIL_ACTIVE:
                        lista = str(solicitud.persona.email)
                        hoy = datetime.now().today()
                        contenido = "Nueva Solicitud"
                        descripcion = "Estimado/a estudiante. Su solicitud ha sido recibida. Sera asignada al Departamento correspondiente. Puede ver el estado de la misma en el Sistema."
                        send_html_mail(contenido,
                            "emails/nuevasolicitud.html", {'d': solicitud, 'fecha': hoy,'contenido': contenido,'descripcion':descripcion,'opcion':'1'},lista.split(','))

                    # //////////////////////////////////////////////////////////////////
                    # //////////////////////////////////////////////////////////////////
                    solicitudpractica.mail_enviosolpract(request.user)
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(solicitudpractica).pk,
                        object_id       = solicitudpractica.id,
                        object_repr     = force_str(solicitudpractica),
                        action_flag     = ADDITION,
                        change_message  = 'Solicitud Enviada (' + client_address + ')' )

                    result['result'] ="ok"
                    result['idsol'] =solicitudpractica.id
                    result['mensaje'] = mensaje
                    return HttpResponse(json.dumps(result),content_type="application/json")
                except Exception as e:
                    print("error excep enviarsolicict soli "+str(e))
                    result['result'] ="bad"
                    result['mensaje'] ="error al guardar la informacion"
                    return HttpResponse(json.dumps(result),content_type="application/json")

            elif "enviarevalua" == action:
                result = {}
                try:
                    solicitudpractica = SolicitudPracticas.objects.get(id=request.POST['idsoli'])
                    solicitudpractica.mail_envioevalpract(request.user)
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(solicitudpractica).pk,
                        object_id       = solicitudpractica.id,
                        object_repr     = force_str(solicitudpractica),
                        action_flag     = ADDITION,
                        change_message  = 'Evaluacion pre profesionales enviada (' + client_address + ')' )

                    result['result'] ="ok"
                    result['idsol'] =solicitudpractica.id
                    return HttpResponse(json.dumps(result),content_type="application/json")
                except Exception as e:
                    print("error excep enviarevalua soli "+str(e))
                    result['result'] ="bad"
                    result['mensaje'] ="error al guardar la informacion"
                    return HttpResponse(json.dumps(result),content_type="application/json")
            elif "aceppracticaclas" == action:
                result = {}
                try:
                    solicitudpractica = SolicitudPracticas.objects.get(id=request.POST['idsoli'])
                    if not SupervisorPracticas.objects.filter(solicitudpracticas=solicitudpractica, activo=True).exists():
                        return HttpResponse(json.dumps({'result':'bad'}),content_type="application/json")
                    supervisor = SupervisorPracticas.objects.get(solicitudpracticas=solicitudpractica, activo=True)

                    solicitudpractica.fechaacepta = datetime.now()
                    solicitudpractica.acepto = json.loads(request.POST['acepta'])
                    solicitudpractica.save()

                    if solicitudpractica.acepto:
                        fichaentidadrecep = solicitudpractica.fichaentidadrec()
                        proceso = fichaentidadrecep.existe_procesoselec()[0]
                        if proceso.cantidad <=  ProcesoSelecDetalle.objects.filter(procesoseleccion=proceso,fichareceptora__convenio=fichaentidadrecep.convenio,acepto=True).count():
                            idsolicitud = ProcesoSelecDetalle.objects.filter(procesoseleccion=proceso,fichareceptora__convenio=fichaentidadrecep.convenio,acepto=False).values('fichareceptora__solicitudpracticas')
                            for s in SolicitudPracticas.objects.filter(id__in=idsolicitud):
                                s.escenariopractica.fechafinaliza = None
                                s.escenariopractica.save()
                                s.mail_aprobsolpract(request.user,3)
                                s.delete()
                            result['result'] ="ok"
                            result['mensaje'] ="Ya no hay cupo para la practica, debe esperar otra solicitud"
                            return HttpResponse(json.dumps(result),content_type="application/json")
                        procesodetalle = ProcesoSelecDetalle.objects.filter(procesoseleccion=proceso,fichareceptora=fichaentidadrecep,acepto=False)[:1].get()
                        procesodetalle.acepto = True
                        procesodetalle.save()
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
                        # rubroenot.autorizado=False
                        # rubroenot.save()
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

                        solicitudpractica.rubroespecie = rubroenot
                        solicitudpractica.solicitudestudiante = solicitudest
                        solicitudpractica.escenariopractica.fechafinaliza = datetime.now()
                        solicitudpractica.escenariopractica.aprobado = True
                        solicitudpractica.escenariopractica.fechaacepta = datetime.now()
                        solicitudpractica.escenariopractica.save()
                        solicitudpractica.save()

                        if proceso.cantidad ==  ProcesoSelecDetalle.objects.filter(procesoseleccion=proceso,fichareceptora__convenio=fichaentidadrecep.convenio,acepto=True).count():
                            idsolicitud = ProcesoSelecDetalle.objects.filter(procesoseleccion=proceso,fichareceptora__convenio=fichaentidadrecep.convenio,acepto=False).values('fichareceptora__solicitudpracticas')
                            for s in SolicitudPracticas.objects.filter(id__in=idsolicitud):
                                s.escenariopractica.fechafinaliza = None
                                s.escenariopractica.save()
                                s.mail_aprobsolpract(request.user,3)
                                s.delete()
                        solicitudpractica.mail_aceptacionpractica(request.user)
                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(solicitudpractica).pk,
                            object_id       = solicitudpractica.id,
                            object_repr     = force_str(solicitudpractica),
                            action_flag     = ADDITION,
                            change_message  = 'Aceptacion de practica por convenio (' + client_address + ')' )
                        result['result'] ="ok"
                        result['url'] = '/solicitudpracticas?ides='+str(solicitudpractica.escenariopractica.id)+'&idsol='+str(solicitudpractica.id)
                        return HttpResponse(json.dumps(result),content_type="application/json")
                    else:
                        solicitudpractica.escenariopractica.fechafinaliza = None
                        solicitudpractica.escenariopractica.fecha = datetime.now()
                        solicitudpractica.escenariopractica.save()
                        solicitudpractica.mail_aceptacionpractica(request.user)
                        fichaentidadrecep = solicitudpractica.fichaentidadrec()
                        proceso = fichaentidadrecep.existe_procesoselec()[0]
                        solicitunoaceptada =    SolictudNoAceptada(escenario =  solicitudpractica.escenariopractica,
                                                                   proceso = proceso,
                                                                   empresa =  fichaentidadrecep.convenio,
                                                                   fechasolict =  solicitudpractica.fechaenvio,
                                                                   observacion =  request.POST['obser'],
                                                                   fecha =  datetime.now())
                        solicitunoaceptada.save()
                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(solicitudpractica).pk,
                            object_id       = solicitudpractica.id,
                            object_repr     = force_str(solicitudpractica),
                            action_flag     = ADDITION,
                            change_message  = 'Practica por convenio no aceptada y eliminada (' + client_address + ')' )
                        solicitudpractica.delete()
                        result['result'] ="ok"
                        result['url'] ='/escenariopractica'
                        return HttpResponse(json.dumps(result),content_type="application/json")
                except Exception as e:
                    print("error excep enviarevalua soli "+str(e))
                    result['result'] ="bad"
                    result['mensaje'] ="error al guardar la informacion"
                    return HttpResponse(json.dumps(result),content_type="application/json")
            elif action == 'guardareval':
                result = {}
                try:
                    datos = json.loads(request.POST['datos'])
                    solicitud = SolicitudPracticas.objects.get(id=datos['idsolicitud'])
                    if EvaluacionSupervisorEmp.objects.filter(solicitudpracticas = solicitud).exists():
                        evalsuperempr = EvaluacionSupervisorEmp.objects.filter(solicitudpracticas = solicitud)
                        evalsuperempr.delete()
                    for d in datos['indicadores']:
                        evaluacion = EvaluacionSupervisorEmp(solicitudpracticas = solicitud,
                                                        segmentodetalle_id = d['iddetseg'] ,
                                                        fecha = datetime.now(),
                                                        puntajeindicador_id = d['idindic'])
                        evaluacion.save()
                    solicitud.save()
                    if 'archivo' in request.FILES:
                        if solicitud.archsupervempresa:
                            if os.path.exists(MEDIA_ROOT+'/'+str(solicitud.archsupervempresa)):
                                os.remove(MEDIA_ROOT+'/'+str(solicitud.archsupervempresa))
                        solicitud.archsupervempresa = request.FILES['archivo']
                    solicitud.mail_evaluacrealizada(request.user)
                    numsegdet = SegmentoDetalle.objects.filter(segmentoindicador__id__in=SegmentoIndicadorEmp.objects.filter(estado=True).values('id'),estado=True).count()
                    solicitud.promedioevasuper = Decimal(Decimal(EvaluacionSupervisorEmp.objects.filter(solicitudpracticas = solicitud).aggregate(Sum('puntajeindicador__puntos'))['puntajeindicador__puntos__sum'])/numsegdet).quantize(Decimal(10) ** -1)
                    solicitud.save()
                    result['result'] = 'ok'
                    return HttpResponse(json.dumps(result),content_type="application/json")

                except Exception as e:
                    print("error excep guardareval superv "+str(e))
                    result['result'] ="bad"
                    return HttpResponse(json.dumps(result),content_type="application/json")

            elif "buscartutempr" == action:
               try:
                   result = {}
                   if TutorEntidadRecep.objects.filter(correo=request.POST['emailtut'],convenio=None).exclude(sinconvenio=None).exists():
                       tutorentidadrecep = TutorEntidadRecep.objects.filter(correo=request.POST['emailtut'],convenio=None).exclude(sinconvenio=None)[:1].get()
                       result['supervisor'] = tutorentidadrecep.supervisor
                       result['celular'] = tutorentidadrecep.celular
                       result['telefono'] = tutorentidadrecep.telefono
                       result['extension'] = tutorentidadrecep.extension
                       result['cargo'] = tutorentidadrecep.cargo
                       result['result'] = "ok"
                   else:
                       result['result'] ="bad"
                   return HttpResponse(json.dumps(result),content_type="application/json")
               except Exception as e:
                    print("error excep guardarempresa soli "+str(e))
                    result['result'] ="bad"
                    result['mensaje'] ="error al guardar la informacion"
                    return HttpResponse(json.dumps(result),content_type="application/json")

            elif "guardarreport" == action:
               try:
                    result = {}
                    reportepractica = ReportePracticas.objects.get(id=request.POST['idrep'])
                    solicitudpractica = SolicitudPracticas.objects.get(id=request.POST['idsolic'])
                    if ReportePractSolicitud.objects.filter(reportepractica=reportepractica,solicitudpractica=solicitudpractica).exists():
                       reportprac = ReportePractSolicitud.objects.filter(reportepractica=reportepractica,solicitudpractica=solicitudpractica)[:1].get()
                    else:
                       reportprac = ReportePractSolicitud(reportepractica=reportepractica,
                                                          solicitudpractica=solicitudpractica)

                    if 'archivo' in request.FILES:
                        if reportprac.archivo:
                            if os.path.exists(MEDIA_ROOT+'/'+str(reportprac.archivo)):
                                os.remove(MEDIA_ROOT+'/'+str(reportprac.archivo))
                        reportprac.archivo = request.FILES['archivo']
                    reportprac.fecha=datetime.now()
                    reportprac.save()


                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(reportprac).pk,
                        object_id       = reportprac.id,
                        object_repr     = force_str(reportprac),
                        action_flag     = ADDITION,
                        change_message  = 'Guardando archivo (' + client_address + ')' )
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
               except Exception as e:
                    print("error excep guardarreport solic "+str(e))
                    result['result'] ="bad"
                    result['mensaje'] ="error al guardar la informacion"
                    return HttpResponse(json.dumps(result),content_type="application/json")

            elif "enviarpract" == action:
               try:
                    result = {}
                    solicitudpractica = SolicitudPracticas.objects.get(id=request.POST['idsolic'])
                    # ///////////////////////////////////HORARIO ASISTENTE /////////////////////////////////////////////////////////////////////////
                    if not EspecieGrupo.objects.filter(tipoe__id=TIPO_SOLIC__SECRET_PRACPRE).exists():
                        return HttpResponse(json.dumps({'result':'bad','mensaje':'No se puede ingresar el escenario contactese con el administrador'}),content_type="application/json")
                    iddepartamentoesp = EspecieGrupo.objects.filter(tipoe__id=TIPO_SOLIC__SECRET_PRACPRE).values('departamento').distinct('departamento')
                    iddepartamento =  CoordinacionDepartamento.objects.filter(departamento__id__in = iddepartamentoesp,coordinacion__carrera=solicitudpractica.matricula.inscripcion.carrera).values('departamento').distinct('departamento')
                    idusuario = AsistenteDepartamento.objects.filter(departamento__id__in=iddepartamento).values('persona__usuario').distinct('persona__usuario')
                    horarioasis = ''
                    mensaje = 'La Finalizacion de practica fue enviado, pronto un asistente le antendera'

                    tipoespecie = TipoEspecieValorada.objects.get(pk=TIPO_SOLIC__SECRET_PRACPRE)
                    solicitudonline = SolicitudOnline.objects.get(pk=ID_SOLIC__ONLINE)
                    solicitudest = SolicitudEstudiante(solicitud=solicitudonline,
                                                                  inscripcion=solicitudpractica.matricula.inscripcion,
                                                                  observacion="SOLICITUD DE FINALIZACION  DE PRACTICA PREPROFESIONAL",
                                                                  tipoe = tipoespecie,
                                                                  correo=solicitudpractica.matricula.inscripcion.persona.email,
                                                                  celular=solicitudpractica.matricula.inscripcion.persona.telefono,
                                                                  fecha=datetime.now())
                    solicitudest.save()
                    solicitud = SolicitudSecretariaDocente(solicitudestudiante=solicitudest,
                                                           persona=solicitudpractica.matricula.inscripcion.persona,
                                                           tipo=tipoespecie.tiposolicitud,
                                                           descripcion="SOLICITUD DE FINALIZACION  DE PRACTICA PREPROFESIONAL",
                                                           fecha = datetime.now(),
                                                           hora = datetime.now().time(),
                                                           cerrada = False)

                    solicitud.save()
                    asistenten = ""
                    if HorarioAsistenteSolicitudes.objects.filter(fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time(),usuario__id__in=idusuario).exists():
                        horarioasis = HorarioAsistenteSolicitudes.objects.filter(fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time(),usuario__id__in=idusuario).exclude(nolabora=True).order_by('sinatender')[:1].get()
                        asistenten = AsistenteDepartamento.objects.filter(persona__usuario=horarioasis.usuario).exclude(puedereasignar=True).order_by('cantidadsol')[:1].get()
                        mensaje = 'La finalizacion de practica fue enviado, el asistente '+ str(asistenten.persona.nombre_completo())+' lo atendera'
                    solicitudhorario = SolicitudHorarioAsistente(solicitud = solicitudpractica,
                                                                fecha = datetime.now(),
                                                                obsestud = "SOLICITUD DE FINALIZACION  DE PRACTICA PREPROFESIONAL")
                    if horarioasis:
                        solicitudhorario.horario = horarioasis
                        horarioasis.sinatender = horarioasis.sinatender + 1
                        horarioasis.save()
                        solicitudhorario.fechaasig = datetime.now()
                        if EMAIL_ACTIVE:
                            solicitudhorario.mail_escenariohorarioasis(request.user)
                    solicitudhorario.save()
                    if asistenten:
                        asistenten.cantidadsol =asistenten.cantidadsol +1
                        solicitud.usuario = asistenten.persona.usuario
                        solicitud.personaasignada =asistenten.persona
                        solicitud.asignado=True
                        solicitud.fechaasignacion = datetime.now()
                        solicitud.departamento = asistenten.departamento
                        solicitud.usuarioasigna=asistenten.persona.usuario
                        solicitud.save()
                        asistenten.save()

                    solicitudpractica.fechestudfinal = datetime.now()
                    solicitudpractica.solicitudsecretariaenvi = solicitud
                    solicitudpractica.save()
                    if EMAIL_ACTIVE:
                        lista = str(solicitud.persona.email)
                        hoy = datetime.now().today()
                        contenido = "Nueva Solicitud"
                        descripcion = "Estimado/a estudiante. Su solicitud ha sido recibida. Sera asignada al Departamento correspondiente. Puede ver el estado de la misma en el Sistema."
                        send_html_mail(contenido,
                            "emails/nuevasolicitud.html", {'d': solicitud, 'fecha': hoy,'contenido': contenido,'descripcion':descripcion,'opcion':'1'},lista.split(','))


                    # //////////////////////////////////////////////////////////////////
                    # //////////////////////////////////////////////////////////////////
                    solicitudpractica.mail_enviofinalpract(request.user)
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(solicitudpractica).pk,
                        object_id       = solicitudpractica.id,
                        object_repr     = force_str(solicitudpractica),
                        action_flag     = ADDITION,
                        change_message  = 'Practica Enviada para finalizacion(' + client_address + ')' )

                    result['result'] ="ok"
                    result['idsol'] =solicitudpractica.id
                    result['mensaje'] = mensaje
                    return HttpResponse(json.dumps(result),content_type="application/json")
               except Exception as e:
                    print("error excep enviarsolicict soli "+str(e))
                    result['result'] ="bad"
                    result['mensaje'] ="error al guardar la informacion"
                    return HttpResponse(json.dumps(result),content_type="application/json")
        else:
            data = {"title":"Solicitud Practicas"}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']
                if action == 'solicitud' :
                    pass
            else:
                # inscripcion = Inscripcion.objects.filter(persona=data['persona'])[:1].get()
                # data['inscripcion'] = inscripcion
                # if 'info' in request.GET:
                #     if request.GET['info'] == '1':
                #         data['info'] = "No esta Matriculado"
                #     if request.GET['info'] == '2':
                #         data['info'] = "No se encuentra en el nivel para iniciar las practicas"
                #     if request.GET['info'] == '3':
                #         data['info'] = "No tiene una especie de solicitud de practicas registrada"
                # solicitudpractica = SolicitudPracticas.objects.filter(matricula__inscripcion=inscripcion)
                # if RubroEspecieValorada.objects.filter(rubro__inscripcion=inscripcion,rubro__cancelado=True,tipoespecie=TIPO_ESPECIEVALO_PRACPRE,rubro__fecha__year=datetime.now().year,aplicada=True).exists():
                #     rubrespecie =  RubroEspecieValorada.objects.filter(rubro__inscripcion=inscripcion,rubro__cancelado=True,tipoespecie=TIPO_ESPECIEVALO_PRACPRE,rubro__fecha__year=datetime.now().year,aplicada=True)[:1].get()
                #     if not SolicitudPracticas.objects.filter(rubroespecie=rubrespecie).exists():
                #         data['rubrespecie'] = rubrespecie
                # data['NIVELMALLA_INICIO_PRACTICA'] = NIVELMALLA_INICIO_PRACTICA
                # data['solicitudpractica'] = solicitudpractica
                # return render(request ,"solicitudpractica/listsolicitudpractica.html" ,  data)
                inscripcion = Inscripcion.objects.filter(persona=data['persona'])[:1].get()
                solicitudpractica = ''
                if inscripcion.matricula():
                    if inscripcion.matricula().nivel.nivelmalla.orden >= NIVELMALLA_INICIO_PRACTICA:
                        if EscenarioPractica.objects.filter(matricula=inscripcion.matricula(),id=request.GET['ides']).exists():
                            escenariopractica = EscenarioPractica.objects.get(id=request.GET['ides'])
                            data['escenariopractica'] = escenariopractica
                            # if RubroEspecieValorada.objects.filter(id=escenariopractica.rubroespecievalorada.id,rubro__cancelado=True,aplicada=True).exists():
                            #     rubrespecie =  RubroEspecieValorada.objects.filter(id=escenariopractica.rubroespecievalorada.id,rubro__cancelado=True,aplicada=True)[:1].get()
                            #     if SolicitudPracticas.objects.filter(rubroespecie=rubrespecie).exists() and not 'idsol' in request.GET:
                            #         return HttpResponseRedirect("/escenariopractica?info=3")
                            if 'reac' in request.GET:
                                data['reac'] = True
                            if 'fire' in request.GET:
                                data['fire'] = True
                            if 'supem' in request.GET:
                                data['supem'] = True
                            if 'archpra' in request.GET:
                                data['archpra'] = True
                            if 'idsol' in request.GET:
                                solicitudpractica = SolicitudPracticas.objects.get(id=request.GET['idsol'])
                                data['solicitudpractica'] = solicitudpractica
                                if not solicitudpractica.finalizada:
                                    numsegdet = SegmentoDetalle.objects.filter(segmentoindicador__id__in=SegmentoIndicadorEmp.objects.filter(estado=True).values('id'),estado=True).count()
                                    data['segmentoindicadoremp'] = SegmentoIndicadorEmp.objects.filter(estado=True)
                                    data['puntajeindicador'] = PuntajeIndicador.objects.filter(estado=True).order_by('-puntos')
                                else:
                                    numsegdet = EvaluacionSupervisorEmp.objects.filter(solicitudpracticas=solicitudpractica).count()
                                    idsegmenind = EvaluacionSupervisorEmp.objects.filter(solicitudpracticas=solicitudpractica).values('segmentodetalle__segmentoindicador').distinct('segmentodetalle__segmentoindicador')
                                    data['segmentoindicadoremp'] = SegmentoIndicadorEmp.objects.filter(id__in=idsegmenind)
                                    data['puntajeindicador'] = PuntajeIndicador.objects.filter(estado=True).order_by('-puntos')
                                data['numsegdet'] = numsegdet
                            if ReportePracticas.objects.filter(carrera=inscripcion.carrera,nivel=escenariopractica.matricula.nivel.nivelmalla).exists():
                                print('POSI')
                                if solicitudpractica:
                                    if ReportePractSolicitud.objects.filter(reportepractica__nombre__id=ID_REPORTE_CARTA_COMPROM,solicitudpractica=solicitudpractica).exists():
                                        data['reportcartcompro'] = ReportePractSolicitud.objects.filter(reportepractica__nombre__id=ID_REPORTE_CARTA_COMPROM,solicitudpractica=solicitudpractica,)[:1].get()
                                    if ReportePractSolicitud.objects.filter(reportepractica__nombre__id=ID_REPORTE_CERTI_PRACTIC,solicitudpractica=solicitudpractica).exists():
                                        data['reportcertpracti'] = ReportePractSolicitud.objects.filter(reportepractica__nombre__id=ID_REPORTE_CERTI_PRACTIC,solicitudpractica=solicitudpractica,)[:1].get()
                                    if not solicitudpractica.fecaprobada or solicitudpractica.aprobada:
                                        numrep = ReportePractSolicitud.objects.filter(solicitudpractica=solicitudpractica,revisado=True).exclude(solicitudpractica__aprobada=False).count() + 1
                                        if solicitudpractica.escenariopractica.convenio:
                                            reportepracticas = ReportePracticas.objects.filter(Q(carrera=inscripcion.carrera,nivel=escenariopractica.matricula.nivel.nivelmalla,convenio=True)| Q(convenio=True,estudiante=True,carrera=None) | Q(general=True)).order_by('orden')[:numrep]
                                        else:
                                            reportepracticas = ReportePracticas.objects.filter(Q(carrera=inscripcion.carrera,nivel=escenariopractica.matricula.nivel.nivelmalla,sinconvenio=True)| Q(sinconvenio=True,estudiante=True,carrera=None)| Q(general=True)).order_by('orden')[:numrep]
                                    else:
                                        idreport = ReportePractSolicitud.objects.filter(solicitudpractica=solicitudpractica).values('reportepractica')
                                        reportepracticas = ReportePracticas.objects.filter(id__in=idreport).order_by('orden')

                                    # DE AQUI
                                    if ProfesorMateria.objects.filter(materia__asignatura=ASIGNATURA_PRACTICAS_SM, materia__nivel=solicitudpractica.matricula.nivel).exists():
                                        prof = ProfesorMateria.objects.filter(materia__asignatura=ASIGNATURA_PRACTICAS_SM, materia__nivel=solicitudpractica.matricula.nivel).order_by('-id')[:1].get()
                                        if SupervisorPracticas.objects.filter(profesormateria=prof, solicitudpracticas=solicitudpractica, activo=True).exists():
                                            supervisor = SupervisorPracticas.objects.get(profesormateria=prof, solicitudpracticas=solicitudpractica, activo=True)
                                        else:
                                            supervisor = SupervisorPracticas(profesormateria=prof,
                                                                             solicitudpracticas=solicitudpractica,
                                                                             desde=datetime.now().date(),
                                                                             activo=True)
                                            supervisor.save()
                                            supervisores = SupervisorPracticas.objects.filter(solicitudpracticas=solicitudpractica, activo=True).exclude(pk=supervisor.id)
                                            for s in supervisores:
                                                s.activo=False
                                                s.save()
                                        data['supervisor'] = supervisor

                                    # HASTA AQUI
                                else:
                                    if escenariopractica.convenio:
                                        reportepracticas = ReportePracticas.objects.filter(Q(carrera=escenariopractica.matricula.inscripcion.carrera,nivel=escenariopractica.matricula.nivel.nivelmalla,convenio=True) | Q(convenio=True,estudiante=True,carrera=None)).order_by('orden')[:1]
                                    else:
                                        reportepracticas = ReportePracticas.objects.filter(Q(carrera=escenariopractica.matricula.inscripcion.carrera,nivel=escenariopractica.matricula.nivel.nivelmalla,sinconvenio=True)| Q(sinconvenio=True,estudiante=True,carrera=None)).order_by('orden')[:1]

                                data['reportepracticas'] = reportepracticas

                            data['fechahoy'] = datetime.now()
                            data['inscripcion'] = inscripcion
                            data['HORAS_MAX_LABORA'] = HORAS_MAX_LABORA
                            data['HORAS_MIN_PRACTICAS'] = HORAS_MIN_PRACTICAS
                            data['PUNTAJE_APRUEBA_PRACTICA'] = PUNTAJE_APRUEBA_PRACTICA
                            return render(request ,"solicitudpractica/solicitudpractica.html" ,  data)
                        return HttpResponseRedirect("/escenariopractica?info=3")
                    return HttpResponseRedirect("/escenariopractica?info=2")
                return HttpResponseRedirect("/escenariopractica?info=1")
    except Exception as e:
        print("Error solicitudpractica "+str(e))
        return HttpResponseRedirect('/?info=Error comuniquese con el administrador')
