from datetime import datetime
from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
from decorators import secure_module
from settings import PROFESORES_GROUP_ID, ALUMNOS_GROUP_ID, SISTEMAS_GROUP_ID, EMAIL_ACTIVE, CORREO_JEFE_ASUNTO_ESTUDIANTIL, ID_DEPARTAMENTO_ASUNTO_ESTUDIANT
from sga.commonviews import addUserData, ip_client_address
from sga.forms import IncidenciaAsuntoEstudiantilForm
from sga.models import IncidenciaAdministrativo, AsistAsuntoEstudiant, SolicituInfo, DepartamentoIncidenciaAsig, IncidenciaAsignada, ObservacionIncidencia, SolicitudSecretariaDocente, Modulo,Persona
from sga.tasks import send_html_mail


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
def view(request):
    try:
        if 'POST' in request.method:
            if 'action' in request.POST:
                action = request.POST['action']
                if action == "add":
                    try:
                        f = IncidenciaAsuntoEstudiantilForm(request.POST)
                        if f.is_valid():
                            incidenciaadministrativo = IncidenciaAdministrativo(
                                                            nombre = f.cleaned_data['nombre'],
                                                            correo = f.cleaned_data['correo'],
                                                            telefono = f.cleaned_data['telefono'],
                                                            incidencia = f.cleaned_data['incidencia'],
                                                            tipoconsulta = f.cleaned_data['tipoconsulta'],
                                                            fecha = datetime.now(),
                                                            usuario = request.user,
                                                            )
                            incidenciaadministrativo.save()
                            if f.cleaned_data['inmediato']:
                                if AsistAsuntoEstudiant.objects.filter(asistente__usuario=request.user).exists():
                                    asistente = AsistAsuntoEstudiant.objects.filter(asistente__usuario=request.user)[:1].get()
                                    incidenciaasignada = IncidenciaAsignada(incidenciaadministrativo = incidenciaadministrativo,
                                                                    observacion = "Incidencia asignada por finalizacion inmediata",
                                                                    asistenteasignado = asistente,
                                                                    fecha=datetime.now(),
                                                                    atendiendo = True)
                                    incidenciaasignada.save()
                                incidenciaadministrativo.inmediato = True
                                incidenciaadministrativo.observacion = f.cleaned_data['observacion']
                                incidenciaadministrativo.resolucion = f.cleaned_data['resolucion']
                                incidenciaadministrativo.finalizado = True
                                incidenciaadministrativo.fechafinaliza = datetime.now()
                                incidenciaadministrativo.usuariofinali = request.user
                                incidenciaadministrativo.asignado = True
                                incidenciaadministrativo.save()
                                if EMAIL_ACTIVE:
                                    incidenciaadministrativo.email_finalizaincidenc()
                                    personarespon = Persona.objects.filter(usuario=incidenciaadministrativo.usuariofinali)[:1].get()
                                    lista = str(CORREO_JEFE_ASUNTO_ESTUDIANTIL)
                                    hoy = datetime.now().today()
                                    contenido = "FINALIZACION DE INCIDENCIA INMEDIATA"
                                    send_html_mail(contenido,
                                        "emails/email_resolucionincidencia.html", {'self': incidenciaadministrativo, 'fecha': hoy,"tip":'Incidencia Administrativas','contenido': contenido,'personarespon':personarespon},lista.split(','))
                            else:
                                if EMAIL_ACTIVE:
                                    personarespon = Persona.objects.filter(usuario=incidenciaadministrativo.usuario)[:1].get()
                                    lista = str('ae@bolivariano.edu.ec')
                                    hoy = datetime.now().today()
                                    contenido = "INGRESO DE INCIDENCIA"
                                    send_html_mail(contenido,
                                        "emails/email_nuevaincidencia.html", {'self': incidenciaadministrativo, 'fecha': hoy,"tip":'Incidencia Administrativas','contenido': contenido,'personarespon':personarespon},lista.split(','))


                            mensaje="Ingreso de Incidencia Administartiva"
                            client_address = ip_client_address(request)
                            LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(incidenciaadministrativo).pk,
                                object_id       = incidenciaadministrativo.id,
                                object_repr     = force_str(incidenciaadministrativo),
                                action_flag     = ADDITION,
                                change_message  = mensaje+' (' + client_address + ')' )
                            if "jefe" in request.POST:
                                return HttpResponseRedirect('/seguimiento')
                            return HttpResponseRedirect('/incidenciaadministrativa')
                    except Exception as ex:
                        return HttpResponseRedirect('/incidenciaadministrativa?action=add&error=Ocurrio un Error Vuelva Intentarlo')



                elif action == 'finaliza':
                    try:
                        if SolicituInfo.objects.filter(id = request.POST['idcorreo'],finalizado=False).exists():
                            solicitudinfo = SolicituInfo.objects.filter(id = request.POST['idcorreo'])[:1].get()
                            if AsistAsuntoEstudiant.objects.filter(asistente__usuario=request.user).exists():
                                asistente = AsistAsuntoEstudiant.objects.filter(asistente__usuario=request.user)[:1].get()
                                if not IncidenciaAsignada.objects.filter(solicituinfo=solicitudinfo,asistenteasignado=asistente).exists():
                                    if IncidenciaAsignada.objects.filter(solicituinfo=solicitudinfo,atendiendo=True).exists():
                                        return HttpResponseRedirect("/incidenciaadministrativa?action=correos&error=Ya se encuentra asignado esta incidencia")
                                    incidenciaasignada = IncidenciaAsignada(solicituinfo = solicitudinfo,
                                                                        observacion = "Incidencia asignada automaticamnete",
                                                                        asistenteasignado = asistente,
                                                                        fecha=datetime.now(),
                                                                        atendiendo = True)
                                    incidenciaasignada.save()
                                    solicitudinfo.asignado = True
                            solicitudinfo.observacion = request.POST['observacionresp']
                            solicitudinfo.resolucion = request.POST['resolucion']
                            solicitudinfo.fechafinaliza = datetime.now()
                            solicitudinfo.usuariofinali = request.user
                            solicitudinfo.finalizado = True

                            solicitudinfo.save()
                            client_address = ip_client_address(request)
                            LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(solicitudinfo).pk,
                                object_id       = solicitudinfo.id,
                                object_repr     = force_str(solicitudinfo),
                                action_flag     = ADDITION,
                                change_message  = 'Correo finalizado info (' + client_address + ')' )
                            if EMAIL_ACTIVE:
                                solicitudinfo.email_finalizaincidenc()
                                personarespon = Persona.objects.filter(usuario=solicitudinfo.usuariofinali)[:1].get()
                                lista = str(CORREO_JEFE_ASUNTO_ESTUDIANTIL)
                                hoy = datetime.now().today()
                                contenido = "FINALIZACION DE INCIDENCIA"
                                send_html_mail(contenido,
                                    "emails/email_resolucionincidencia.html", {'self': solicitudinfo, 'fecha': hoy,"tip":'Correo Info','contenido': contenido,'personarespon':personarespon},lista.split(','))
                            if IncidenciaAsignada.objects.filter(solicituinfo__id=request.POST['idcorreo'],asistenteasignado__asistente__usuario=request.user).exists():
                                return HttpResponseRedirect("/incidenciaadministrativa?action=correos")
                            return HttpResponseRedirect("/seguimiento?action=correos")
                        else:
                            if AsistAsuntoEstudiant.objects.filter(asistente__usuario=request.user).exists():
                                return HttpResponseRedirect("/incidenciaadministrativa?action=correos&error=La incidencia ya esta finalizada")
                            return HttpResponseRedirect("/seguimiento?action=correos&error=La incidencia ya esta finalizada")
                    except Exception as ex:
                        return HttpResponseRedirect("/incidenciaadministrativa?action=correos&error=Error Vuelva  intentarlo")
                elif action == "finalizasol":
                    try:
                        if SolicitudSecretariaDocente.objects.filter(id = request.POST['idsolici'],cerrada = False).exists():
                            solicitud = SolicitudSecretariaDocente.objects.filter(id = request.POST['idsolici'])[:1].get()
                            if AsistAsuntoEstudiant.objects.filter(asistente__usuario=request.user).exists():
                                asistente = AsistAsuntoEstudiant.objects.filter(asistente__usuario=request.user)[:1].get()
                                if not IncidenciaAsignada.objects.filter(solicitusecret=solicitud,asistenteasignado=asistente).exists():
                                    if IncidenciaAsignada.objects.filter(solicitusecret=solicitud,atendiendo=True).exists():
                                        return HttpResponseRedirect("/incidenciaadministrativa?action=solicitudes&error=Ya se encuentra asignado esta incidencia")
                                    incidenciaasignada = IncidenciaAsignada(solicitusecret = solicitud,
                                                                        observacion = "Incidencia asignada automaticamnete",
                                                                        asistenteasignado = asistente,
                                                                        fecha=datetime.now(),
                                                                        atendiendo = True)
                                    incidenciaasignada.save()
                                    solicitud.asignado = True

                            solicitud.observacion = request.POST['observacionresp']
                            solicitud.resolucion = request.POST['resolucion']
                            solicitud.fechacierre = datetime.now()
                            solicitud.usuario = request.user
                            solicitud.cerrada = True
                            solicitud.save()
                            client_address = ip_client_address(request)
                            LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(solicitud).pk,
                                object_id       = solicitud.id,
                                object_repr     = force_str(solicitud),
                                action_flag     = ADDITION,
                                change_message  = 'Solicitud Alumno finalizado (' + client_address + ')' )
                            if EMAIL_ACTIVE:
                                solicitud.email_finalizaincidenc()
                                personarespon = Persona.objects.filter(usuario=solicitud.usuario)[:1].get()
                                lista = str(CORREO_JEFE_ASUNTO_ESTUDIANTIL)
                                hoy = datetime.now().today()
                                contenido = "FINALIZACION DE INCIDENCIA"
                                send_html_mail(contenido,
                                    "emails/email_resolucionincidencia.html", {'self': solicitud, 'fecha': hoy,"tip":'Solicitud Alumno','contenido': contenido,'personarespon':personarespon},lista.split(','))

                            if IncidenciaAsignada.objects.filter(solicitusecret__id=request.POST['idsolici'],asistenteasignado__asistente__usuario=request.user).exists():
                                return HttpResponseRedirect("/incidenciaadministrativa?action=solicitudes")
                            return HttpResponseRedirect("/seguimiento?action=solicitudes")
                        else:
                            if AsistAsuntoEstudiant.objects.filter(asistente__usuario=request.user).exists():
                                return HttpResponseRedirect("/incidenciaadministrativa?action=solicitudes&error=La incidencia ya esta finalizada")
                            return HttpResponseRedirect("/seguimiento?action=solicitudes&error=La incidencia ya esta finalizada")
                    except Exception as ex:
                        return HttpResponseRedirect("/solicitudes?error=Error Vuelva  intentarlo")

                elif action == "finalizainci":
                    try:
                        if IncidenciaAdministrativo.objects.filter(id = request.POST['idsolici'],finalizado = False).exists():
                            incidencia = IncidenciaAdministrativo.objects.filter(id = request.POST['idsolici'])[:1].get()
                            if AsistAsuntoEstudiant.objects.filter(asistente__usuario=request.user).exists():
                                asistente = AsistAsuntoEstudiant.objects.filter(asistente__usuario=request.user)[:1].get()
                                if not IncidenciaAsignada.objects.filter(incidenciaadministrativo=incidencia,asistenteasignado=asistente).exists():
                                    if IncidenciaAsignada.objects.filter(incidenciaadministrativo=incidencia,atendiendo=True).exists():
                                        return HttpResponseRedirect("/incidenciaadministrativa?action=incidenciaadminis&error=Ya se encuentra asignado esta incidencia")
                                    incidenciaasignada = IncidenciaAsignada(incidenciaadministrativo = incidencia,
                                                                        observacion = "Incidencia asignada automaticamente",
                                                                        asistenteasignado = asistente,
                                                                        fecha=datetime.now(),
                                                                        atendiendo = True)
                                    incidenciaasignada.save()
                                    incidencia.asignado = True

                            incidencia.observacion = request.POST['observacionresp']
                            incidencia.resolucion = request.POST['resolucion']
                            incidencia.finalizado = True
                            incidencia.fechafinaliza = datetime.now()
                            incidencia.usuariofinali = request.user

                            incidencia.save()
                            client_address = ip_client_address(request)
                            LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(incidencia).pk,
                                object_id       = incidencia.id,
                                object_repr     = force_str(incidencia),
                                action_flag     = ADDITION,
                                change_message  = 'Incidencia Administrativo Alumno finalizado (' + client_address + ')' )
                            if EMAIL_ACTIVE:
                                incidencia.email_finalizaincidenc()
                                personarespon = Persona.objects.filter(usuario=incidencia.usuariofinali)[:1].get()
                                lista = str(CORREO_JEFE_ASUNTO_ESTUDIANTIL)
                                hoy = datetime.now().today()
                                contenido = "FINALIZACION DE INCIDENCIA"
                                send_html_mail(contenido,
                                    "emails/email_resolucionincidencia.html", {'self': incidencia, 'fecha': hoy,"tip":'Incidencia Administrativas','contenido': contenido,'personarespon':personarespon},lista.split(','))
                            if IncidenciaAsignada.objects.filter(incidenciaadministrativo__id=request.POST['idsolici'],asistenteasignado__asistente__usuario=request.user).exists():
                                return HttpResponseRedirect("/incidenciaadministrativa?action=incidenciaadminis")
                            return HttpResponseRedirect("/seguimiento?action=incidenciaadminis")
                        else:
                            if AsistAsuntoEstudiant.objects.filter(asistente__usuario=request.user).exists():
                                return HttpResponseRedirect("/incidenciaadministrativa?action=incidenciaadminis&error=La incidencia ya esta finalizada")
                            return HttpResponseRedirect("/seguimiento?action=incidenciaadminis&error=La incidencia ya esta finalizado")
                    except Exception as ex:
                        return HttpResponseRedirect("/seguimiento?action=incidenciaadminis&error=Error Vuelva  intentarlo")
                elif action == 'asigdepartcorreo':
                    try:
                        if not IncidenciaAsignada.objects.filter(solicituinfo__id=request.POST['idcorreo'],asistenteasignado__asistente__usuario=request.user,atendiendo=True).exists():
                            if IncidenciaAsignada.objects.filter(solicituinfo__id=request.POST['idcorreo'],atendiendo=True).exists():
                                return HttpResponseRedirect("/incidenciaadministrativa?action=correos&error=Ya se encuentra asignado esta incidencia")
                            incidencia = SolicituInfo.objects.filter(id = request.POST['idcorreo'])[:1].get()
                            if AsistAsuntoEstudiant.objects.filter(asistente__usuario=request.user).exists():
                                asistente = AsistAsuntoEstudiant.objects.filter(asistente__usuario=request.user)[:1].get()
                                if not IncidenciaAsignada.objects.filter(solicituinfo=incidencia,asistenteasignado=asistente).exists():
                                    incidenciaasignada = IncidenciaAsignada(solicituinfo = incidencia,
                                                                        observacion = "Incidencia asignada automaticamente",
                                                                        asistenteasignado = asistente,
                                                                        fecha=datetime.now(),
                                                                        atendiendo = True)
                                    incidenciaasignada.save()
                                    incidenciaasignada.solicituinfo.asignado = True
                                    incidenciaasignada.solicituinfo.save()
                        else:
                            incidenciaasignada = IncidenciaAsignada.objects.filter(solicituinfo__id=request.POST['idcorreo'],asistenteasignado__asistente__usuario=request.user,atendiendo=True)[:1].get()


                        if not DepartamentoIncidenciaAsig.objects.filter(incidenciaasignada__solicituinfo__id=request.POST['idcorreo'],departamento__id=request.POST['iddepart']).exists():
                            deparatincidenciaasignada = DepartamentoIncidenciaAsig(observacion = request.POST['observaciondepar'],
                                                                        departamento_id = request.POST['iddepart'],
                                                                        incidenciaasignada = incidenciaasignada,
                                                                        atendiendo = True ,
                                                                        fecha = datetime.now())
                            deparatincidenciaasignada.save()
                            if DepartamentoIncidenciaAsig.objects.filter(incidenciaasignada=deparatincidenciaasignada.incidenciaasignada,atendiendo=True).exclude(id=deparatincidenciaasignada.id).order_by('id').exists():
                                departincidenciaasignadaanterior = DepartamentoIncidenciaAsig.objects.filter(incidenciaasignada=deparatincidenciaasignada.incidenciaasignada,atendiendo=True).exclude(id=deparatincidenciaasignada.id).order_by('id')[:1].get()
                                departincidenciaasignadaanterior.atendiendo = False
                                departincidenciaasignadaanterior.save()
                            client_address = ip_client_address(request)
                            LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(deparatincidenciaasignada).pk,
                                object_id       = deparatincidenciaasignada.id,
                                object_repr     = force_str(deparatincidenciaasignada),
                                action_flag     = ADDITION,
                                change_message  = 'Asignado Departamento a correo info (' + client_address + ')' )

                        else:
                            if DepartamentoIncidenciaAsig.objects.filter(incidenciaasignada__solicituinfo__id=request.POST['idcorreo'],departamento__id=request.POST['iddepart'],atendiendo=False).exists():
                                deparatincidenciaasignada = DepartamentoIncidenciaAsig.objects.filter(incidenciaasignada__solicituinfo__id=request.POST['idcorreo'],departamento__id=request.POST['iddepart'],atendiendo=False)[:1].get()
                                deparatincidenciaasignada.atendiendo=True
                                deparatincidenciaasignada.observacion=request.POST['observaciondepar']
                                deparatincidenciaasignada.fecha=datetime.now()
                                deparatincidenciaasignada.save()
                                if DepartamentoIncidenciaAsig.objects.filter(incidenciaasignada=deparatincidenciaasignada.incidenciaasignada,atendiendo=True).exclude(id=deparatincidenciaasignada.id).order_by('id').exists():
                                    departincidenciaasignadaanterior = DepartamentoIncidenciaAsig.objects.filter(incidenciaasignada=deparatincidenciaasignada.incidenciaasignada,atendiendo=True).exclude(id=deparatincidenciaasignada.id).order_by('id')[:1].get()
                                    departincidenciaasignadaanterior.atendiendo = False
                                    departincidenciaasignadaanterior.save()
                                client_address = ip_client_address(request)
                                LogEntry.objects.log_action(
                                    user_id         = request.user.pk,
                                    content_type_id = ContentType.objects.get_for_model(deparatincidenciaasignada).pk,
                                    object_id       = deparatincidenciaasignada.id,
                                    object_repr     = force_str(deparatincidenciaasignada),
                                    action_flag     = ADDITION,
                                    change_message  = 'Departamento reasignado a correo info (' + client_address + ')' )
                        if EMAIL_ACTIVE:
                            deparatincidenciaasignada.email_departasigna('Correo Info')
                        return HttpResponseRedirect("/incidenciaadministrativa?action=correos")
                    except:
                        return HttpResponseRedirect("/incidenciaadministrativa?action=correos&error=Error Vuelva  intentarlo")
                elif action == 'asigdepartsolicitud':
                    try:
                        if not IncidenciaAsignada.objects.filter(solicitusecret__id=request.POST['idsolici'],asistenteasignado__asistente__usuario=request.user,atendiendo=True).exists():
                            if IncidenciaAsignada.objects.filter(solicitusecret__id=request.POST['idsolici'],atendiendo=True).exists():
                                return HttpResponseRedirect("/incidenciaadministrativa?action=solicitudes&error=Ya se encuentra asignado esta incidencia")
                            incidencia = SolicitudSecretariaDocente.objects.filter(id = request.POST['idsolici'])[:1].get()
                            if AsistAsuntoEstudiant.objects.filter(asistente__usuario=request.user).exists():
                                asistente = AsistAsuntoEstudiant.objects.filter(asistente__usuario=request.user)[:1].get()
                                if not IncidenciaAsignada.objects.filter(solicitusecret=incidencia,asistenteasignado=asistente).exists():
                                    incidenciaasignada = IncidenciaAsignada(solicitusecret = incidencia,
                                                                        observacion = "Incidencia asignada automaticamente",
                                                                        asistenteasignado = asistente,
                                                                        fecha=datetime.now(),
                                                                        atendiendo = True)
                                    incidenciaasignada.save()
                                    incidenciaasignada.solicitusecret.asignado=True
                                    incidenciaasignada.solicitusecret.save()
                        else:
                            incidenciaasignada = IncidenciaAsignada.objects.filter(solicitusecret__id=request.POST['idsolici'],asistenteasignado__asistente__usuario=request.user,atendiendo=True)[:1].get()


                        if not DepartamentoIncidenciaAsig.objects.filter(incidenciaasignada__solicitusecret__id=request.POST['idsolici'],departamento__id=request.POST['iddepart']).exists():
                            deparatincidenciaasignada = DepartamentoIncidenciaAsig(observacion = request.POST['observaciondepar'],
                                                                        departamento_id = request.POST['iddepart'],
                                                                        incidenciaasignada = incidenciaasignada,
                                                                        atendiendo = True ,
                                                                        fecha = datetime.now())
                            deparatincidenciaasignada.save()
                            if DepartamentoIncidenciaAsig.objects.filter(incidenciaasignada=deparatincidenciaasignada.incidenciaasignada,atendiendo=True).exclude(id=deparatincidenciaasignada.id).order_by('id').exists():
                                departincidenciaasignadaanterior = DepartamentoIncidenciaAsig.objects.filter(incidenciaasignada=deparatincidenciaasignada.incidenciaasignada,atendiendo=True).exclude(id=deparatincidenciaasignada.id).order_by('id')[:1].get()
                                departincidenciaasignadaanterior.atendiendo = False
                                departincidenciaasignadaanterior.save()
                            client_address = ip_client_address(request)
                            LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(deparatincidenciaasignada).pk,
                                object_id       = deparatincidenciaasignada.id,
                                object_repr     = force_str(deparatincidenciaasignada),
                                action_flag     = ADDITION,
                                change_message  = 'Asignado Departamento a Solicitud de secretaria (' + client_address + ')' )

                        else:
                            if DepartamentoIncidenciaAsig.objects.filter(incidenciaasignada__solicitusecret__id=request.POST['idsolici'],departamento__id=request.POST['iddepart'],atendiendo=False).exists():
                                deparatincidenciaasignada = DepartamentoIncidenciaAsig.objects.filter(incidenciaasignada__solicitusecret__id=request.POST['idsolici'],departamento__id=request.POST['iddepart'],atendiendo=False)[:1].get()
                                deparatincidenciaasignada.atendiendo=True
                                deparatincidenciaasignada.observacion=request.POST['observaciondepar']
                                deparatincidenciaasignada.fecha=datetime.now()
                                deparatincidenciaasignada.save()
                                if DepartamentoIncidenciaAsig.objects.filter(incidenciaasignada=deparatincidenciaasignada.incidenciaasignada,atendiendo=True).exclude(id=deparatincidenciaasignada.id).order_by('id').exists():
                                    departincidenciaasignadaanterior = DepartamentoIncidenciaAsig.objects.filter(incidenciaasignada=deparatincidenciaasignada.incidenciaasignada,atendiendo=True).exclude(id=deparatincidenciaasignada.id).order_by('id')[:1].get()
                                    departincidenciaasignadaanterior.atendiendo = False
                                    departincidenciaasignadaanterior.save()
                                client_address = ip_client_address(request)
                                LogEntry.objects.log_action(
                                    user_id         = request.user.pk,
                                    content_type_id = ContentType.objects.get_for_model(deparatincidenciaasignada).pk,
                                    object_id       = deparatincidenciaasignada.id,
                                    object_repr     = force_str(deparatincidenciaasignada),
                                    action_flag     = ADDITION,
                                    change_message  = 'Departamento reasignado a Solicitud de secretaria (' + client_address + ')' )
                        if EMAIL_ACTIVE:
                            deparatincidenciaasignada.email_departasigna('Incidencia Administrativa')
                        return HttpResponseRedirect("/incidenciaadministrativa?action=solicitudes")
                    except:
                        return HttpResponseRedirect("/incidenciaadministrativa?action=solicitudes&error=Error Vuelva  intentarlo")

                elif action == 'asigdepartincidencia':
                    try:
                        if not IncidenciaAsignada.objects.filter(incidenciaadministrativo__id=request.POST['idsolici'],asistenteasignado__asistente__usuario=request.user,atendiendo=True).exists():
                            if IncidenciaAsignada.objects.filter(incidenciaadministrativo__id=request.POST['idsolici'],atendiendo=True).exists():
                                return HttpResponseRedirect("/incidenciaadministrativa?action=incidenciaadminis&error=Ya se encuentra asignado esta incidencia")
                            incidencia = IncidenciaAdministrativo.objects.filter(id = request.POST['idsolici'])[:1].get()
                            if AsistAsuntoEstudiant.objects.filter(asistente__usuario=request.user).exists():
                                asistente = AsistAsuntoEstudiant.objects.filter(asistente__usuario=request.user)[:1].get()
                                if not IncidenciaAsignada.objects.filter(incidenciaadministrativo=incidencia,asistenteasignado=asistente).exists():
                                    incidenciaasignada = IncidenciaAsignada(incidenciaadministrativo = incidencia,
                                                                        observacion = "Incidencia asignada automaticamente",
                                                                        asistenteasignado = asistente,
                                                                        fecha=datetime.now(),
                                                                        atendiendo = True)
                                    incidenciaasignada.save()
                                    incidenciaasignada.incidenciaadministrativo.asignado=True
                                    incidenciaasignada.incidenciaadministrativo.save()
                        else:
                            incidenciaasignada = IncidenciaAsignada.objects.filter(incidenciaadministrativo__id=request.POST['idsolici'],asistenteasignado__asistente__usuario=request.user,atendiendo=True)[:1].get()
                        if not DepartamentoIncidenciaAsig.objects.filter(incidenciaasignada__incidenciaadministrativo__id=request.POST['idsolici'],departamento__id=request.POST['iddepart']).exists():
                            deparatincidenciaasignada = DepartamentoIncidenciaAsig(observacion = request.POST['observaciondepar'],
                                                                        departamento_id = request.POST['iddepart'],
                                                                        incidenciaasignada = incidenciaasignada,
                                                                        atendiendo = True ,
                                                                        fecha = datetime.now())
                            deparatincidenciaasignada.save()
                            if DepartamentoIncidenciaAsig.objects.filter(incidenciaasignada=deparatincidenciaasignada.incidenciaasignada,atendiendo=True).exclude(id=deparatincidenciaasignada.id).order_by('id').exists():
                                departincidenciaasignadaanterior = DepartamentoIncidenciaAsig.objects.filter(incidenciaasignada=deparatincidenciaasignada.incidenciaasignada,atendiendo=True).exclude(id=deparatincidenciaasignada.id).order_by('id')[:1].get()
                                departincidenciaasignadaanterior.atendiendo = False
                                departincidenciaasignadaanterior.save()
                            client_address = ip_client_address(request)
                            LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(deparatincidenciaasignada).pk,
                                object_id       = deparatincidenciaasignada.id,
                                object_repr     = force_str(deparatincidenciaasignada),
                                action_flag     = ADDITION,
                                change_message  = 'Asignado Departamento a Incidencia Administrativa(' + client_address + ')' )

                        else:
                            if DepartamentoIncidenciaAsig.objects.filter(incidenciaasignada__incidenciaadministrativo__id=request.POST['idsolici'],departamento__id=request.POST['iddepart'],atendiendo=False).exists():
                                deparatincidenciaasignada = DepartamentoIncidenciaAsig.objects.filter(incidenciaasignada__incidenciaadministrativo__id=request.POST['idsolici'],departamento__id=request.POST['iddepart'],atendiendo=False)[:1].get()
                                deparatincidenciaasignada.atendiendo=True
                                deparatincidenciaasignada.observacion=request.POST['observaciondepar']
                                deparatincidenciaasignada.fecha=datetime.now()
                                deparatincidenciaasignada.save()
                                if DepartamentoIncidenciaAsig.objects.filter(incidenciaasignada=deparatincidenciaasignada.incidenciaasignada,atendiendo=True).exclude(id=deparatincidenciaasignada.id).order_by('id').exists():
                                    departincidenciaasignadaanterior = DepartamentoIncidenciaAsig.objects.filter(incidenciaasignada=deparatincidenciaasignada.incidenciaasignada,atendiendo=True).exclude(id=deparatincidenciaasignada.id).order_by('id')[:1].get()
                                    departincidenciaasignadaanterior.atendiendo = False
                                    departincidenciaasignadaanterior.save()
                                client_address = ip_client_address(request)
                                LogEntry.objects.log_action(
                                    user_id         = request.user.pk,
                                    content_type_id = ContentType.objects.get_for_model(deparatincidenciaasignada).pk,
                                    object_id       = deparatincidenciaasignada.id,
                                    object_repr     = force_str(deparatincidenciaasignada),
                                    action_flag     = ADDITION,
                                    change_message  = 'Departamento reasignado a Incidencia Administrativa (' + client_address + ')' )
                        if EMAIL_ACTIVE:
                            deparatincidenciaasignada.email_departasigna('Incidencia Administrativa')
                        return HttpResponseRedirect("/incidenciaadministrativa?action=incidenciaadminis")
                    except:
                        return HttpResponseRedirect("/incidenciaadministrativa?action=incidenciaadminis&error=Error Vuelva  intentarlo")

                elif action == 'respuestacorreo':
                    try:
                        if request.POST['idobserv']  == '0' or request.POST['idobserv']  == '':
                            if request.POST['obsasistente']  == '0' or  request.POST['obsasistente']  == '' :
                                departaasignado = DepartamentoIncidenciaAsig.objects.filter(incidenciaasignada__solicituinfo__id=request.POST['idcorreo'],atendiendo=True).order_by('-id')[:1].get()
                                observacionincidencia = ObservacionIncidencia(
                                                                    respuestadepart = request.POST['observacionresp'],
                                                                    departamentoincidenciaasig   = departaasignado,
                                                                    usuario = request.user,
                                                                    fecha = datetime.now())
                                observacionincidencia.save()
                                client_address = ip_client_address(request)
                                LogEntry.objects.log_action(
                                    user_id         = request.user.pk,
                                    content_type_id = ContentType.objects.get_for_model(observacionincidencia).pk,
                                    object_id       = observacionincidencia.id,
                                    object_repr     = force_str(observacionincidencia),
                                    action_flag     = ADDITION,
                                    change_message  = 'Respuesta a correo info (' + client_address + ')' )
                            else:
                                departaasignado = DepartamentoIncidenciaAsig.objects.filter(incidenciaasignada__solicituinfo__id=request.POST['idcorreo'],atendiendo=True).order_by('-id')[:1].get()
                                observacionincidencia = ObservacionIncidencia(
                                                                    observacionasisten = request.POST['observacionresp'],
                                                                    departamentoincidenciaasig   = departaasignado,
                                                                    fechaobservacion = datetime.now())
                                observacionincidencia.save()
                                client_address = ip_client_address(request)
                                LogEntry.objects.log_action(
                                    user_id         = request.user.pk,
                                    content_type_id = ContentType.objects.get_for_model(observacionincidencia).pk,
                                    object_id       = observacionincidencia.id,
                                    object_repr     = force_str(observacionincidencia),
                                    action_flag     = ADDITION,
                                    change_message  = 'Observacion a departamento a correo info (' + client_address + ')' )
                            if EMAIL_ACTIVE:
                                observacionincidencia.email_observacionincidencia('Correo Info')
                        else:
                            observacionincidencia = ObservacionIncidencia.objects.filter(id=request.POST['idobserv'])[:1].get()
                            if observacionincidencia.observacionasisten == '' :
                                observacionincidencia.observacionasisten = request.POST['observacionresp']
                                observacionincidencia.fechaobservacion = datetime.now()
                                observacionincidencia.save()
                            else:
                                observacionincidencia.respuestadepart = request.POST['observacionresp']
                                observacionincidencia.usuario = request.user
                                observacionincidencia.fecha = datetime.now()
                                observacionincidencia.save()
                                if EMAIL_ACTIVE:
                                    observacionincidencia.email_observacionincidencia('Correo Info')
                                return HttpResponseRedirect("/incidenciaadministrativa?action=correos")
                            if EMAIL_ACTIVE:
                                observacionincidencia.email_observacionincidencia('Correo Info')
                            return HttpResponseRedirect("/incidenciaadministrativa?action=correos&iddepart="+str(observacionincidencia.departamentoincidenciaasig.id))
                        return HttpResponseRedirect("/incidenciaadministrativa?action=correos")
                    except Exception as ex:
                        return HttpResponseRedirect("/incidenciaadministrativa?action=correos&error=Error Vuelva  intentarlo")
                elif action == 'respuestasolicitud':
                    try:
                        if request.POST['idobserv']  == '0' or request.POST['idobserv']  == '':
                            if request.POST['obsasistente']  == '0' or  request.POST['obsasistente']  == '' :
                                departaasignado = DepartamentoIncidenciaAsig.objects.filter(incidenciaasignada__solicitusecret__id=request.POST['idsolici'],atendiendo=True).order_by('-id')[:1].get()
                                observacionincidencia = ObservacionIncidencia(
                                                                    respuestadepart = request.POST['observacionresp'],
                                                                    departamentoincidenciaasig   = departaasignado,
                                                                    usuario = request.user,
                                                                    fecha = datetime.now())
                                observacionincidencia.save()
                                client_address = ip_client_address(request)
                                LogEntry.objects.log_action(
                                    user_id         = request.user.pk,
                                    content_type_id = ContentType.objects.get_for_model(observacionincidencia).pk,
                                    object_id       = observacionincidencia.id,
                                    object_repr     = force_str(observacionincidencia),
                                    action_flag     = ADDITION,
                                    change_message  = 'Respuesta a Solicitudes de Alumnos (' + client_address + ')' )
                            else:
                                departaasignado = DepartamentoIncidenciaAsig.objects.filter(incidenciaasignada__solicitusecret__id=request.POST['idsolici'],atendiendo=True).order_by('-id')[:1].get()
                                observacionincidencia = ObservacionIncidencia(
                                                                    observacionasisten = request.POST['observacionresp'],
                                                                    departamentoincidenciaasig   = departaasignado,
                                                                    fechaobservacion = datetime.now())
                                observacionincidencia.save()
                                client_address = ip_client_address(request)
                                LogEntry.objects.log_action(
                                    user_id         = request.user.pk,
                                    content_type_id = ContentType.objects.get_for_model(observacionincidencia).pk,
                                    object_id       = observacionincidencia.id,
                                    object_repr     = force_str(observacionincidencia),
                                    action_flag     = ADDITION,
                                    change_message  = 'Observacion a departamento Sobre solicitudes de alumnos (' + client_address + ')' )
                            if EMAIL_ACTIVE:
                                observacionincidencia.email_observacionincidencia('Solicitud Alumnos')
                        else:
                            observacionincidencia = ObservacionIncidencia.objects.filter(id=request.POST['idobserv'])[:1].get()
                            if observacionincidencia.observacionasisten == '' :
                                observacionincidencia.observacionasisten = request.POST['observacionresp']
                                observacionincidencia.fechaobservacion = datetime.now()
                                observacionincidencia.save()
                            else:
                                observacionincidencia.respuestadepart = request.POST['observacionresp']
                                observacionincidencia.usuario = request.user
                                observacionincidencia.fecha = datetime.now()
                                observacionincidencia.save()
                                if EMAIL_ACTIVE:
                                    observacionincidencia.email_observacionincidencia('Solicitud Alumnos')
                                return HttpResponseRedirect("/incidenciaadministrativa?action=solicitudes")
                            if EMAIL_ACTIVE:
                                observacionincidencia.email_observacionincidencia('Solicitud Alumnos')
                            return HttpResponseRedirect("/incidenciaadministrativa?action=solicitudes&iddepart="+str(observacionincidencia.departamentoincidenciaasig.id))
                        return HttpResponseRedirect("/incidenciaadministrativa?action=solicitudes")
                    except Exception as ex:
                        return HttpResponseRedirect("/incidenciaadministrativa?action=solicitudes&error=Error Vuelva  intentarlo")

                elif action == 'respuestaincidenc':
                    try:
                        if request.POST['idobserv']  == '0' or request.POST['idobserv']  == '':
                            if request.POST['obsasistente']  == '0' or  request.POST['obsasistente']  == '' :
                                departaasignado = DepartamentoIncidenciaAsig.objects.filter(incidenciaasignada__incidenciaadministrativo__id=request.POST['idsolici'],atendiendo=True).order_by('-id')[:1].get()
                                observacionincidencia = ObservacionIncidencia(
                                                                    respuestadepart = request.POST['observacionresp'],
                                                                    departamentoincidenciaasig   = departaasignado,
                                                                    usuario = request.user,
                                                                    fecha = datetime.now())
                                observacionincidencia.save()
                                client_address = ip_client_address(request)
                                LogEntry.objects.log_action(
                                    user_id         = request.user.pk,
                                    content_type_id = ContentType.objects.get_for_model(observacionincidencia).pk,
                                    object_id       = observacionincidencia.id,
                                    object_repr     = force_str(observacionincidencia),
                                    action_flag     = ADDITION,
                                    change_message  = 'Respuesta a Incidencia Administrativa (' + client_address + ')' )
                            else:
                                departaasignado = DepartamentoIncidenciaAsig.objects.filter(incidenciaasignada__incidenciaadministrativo__id=request.POST['idsolici'],atendiendo=True).order_by('-id')[:1].get()
                                observacionincidencia = ObservacionIncidencia(
                                                                    observacionasisten = request.POST['observacionresp'],
                                                                    departamentoincidenciaasig   = departaasignado,
                                                                    fechaobservacion = datetime.now())
                                observacionincidencia.save()
                                client_address = ip_client_address(request)
                                LogEntry.objects.log_action(
                                    user_id         = request.user.pk,
                                    content_type_id = ContentType.objects.get_for_model(observacionincidencia).pk,
                                    object_id       = observacionincidencia.id,
                                    object_repr     = force_str(observacionincidencia),
                                    action_flag     = ADDITION,
                                    change_message  = 'Observacion a departamento Sobre Incidencia Administrativa (' + client_address + ')' )
                            if EMAIL_ACTIVE:
                                observacionincidencia.email_observacionincidencia('Incidencia Administrativas')
                        else:
                            observacionincidencia = ObservacionIncidencia.objects.filter(id=request.POST['idobserv'])[:1].get()
                            if observacionincidencia.observacionasisten == '' :
                                observacionincidencia.observacionasisten = request.POST['observacionresp']
                                observacionincidencia.fechaobservacion = datetime.now()
                                observacionincidencia.save()
                                if EMAIL_ACTIVE:
                                    observacionincidencia.email_observacionincidencia('Incidencia Administrativas')
                            else:
                                observacionincidencia.respuestadepart = request.POST['observacionresp']
                                observacionincidencia.usuario = request.user
                                observacionincidencia.fecha = datetime.now()
                                observacionincidencia.save()
                                if EMAIL_ACTIVE:
                                    observacionincidencia.email_observacionincidencia('Incidencia Administrativas')
                                return HttpResponseRedirect("/incidenciaadministrativa?action=incidenciaadminis")

                            return HttpResponseRedirect("/incidenciaadministrativa?action=incidenciaadminis&iddepart="+str(observacionincidencia.departamentoincidenciaasig.id))
                        return HttpResponseRedirect("/incidenciaadministrativa?action=incidenciaadminis")
                    except Exception as ex:
                        return HttpResponseRedirect("/incidenciaadministrativa?action=incidenciaadminis&error=Error Vuelva  intentarlo")
        else:
            data = {"title": "Incidencias Administrativas"}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']
                if action == "add":
                    data['title'] = "Nueva Incidencia"
                    form = IncidenciaAsuntoEstudiantilForm()
                    if AsistAsuntoEstudiant.objects.filter(asistente__usuario=request.user).exists() or 'jefe' in request.GET:
                        if 'jefe' in request.GET:
                            data['asistente']= '1'
                        else:
                            data['asistente']= AsistAsuntoEstudiant.objects.filter(asistente__usuario=request.user)[:1].get()
                    else:
                        data['departa'] = 1
                    data['form'] = form
                    return render(request ,"asuntoestudiantil/addincidenciaestudiant.html" ,  data)
                elif action=='verasistentes':
                    data = {}
                    data['asistentes'] = IncidenciaAsignada.objects.filter(incidenciaadministrativo__id=request.GET['idinfo'])
                    return render(request ,"asuntoestudiantil/verasistentes.html" ,  data)

                elif action=='verdepartamentos':
                    data = {}
                    data['departamentos'] = DepartamentoIncidenciaAsig.objects.filter(incidenciaasignada__solicituinfo__id=request.GET['idinfo'])
                    if 'asigna' in request.GET:
                        data['asigna'] = request.GET['asigna']
                    return render(request ,"asuntoestudiantil/verdepartamentos.html" ,  data)

                elif action=='verdepartamentossolicitud':
                    data = {}
                    data['departamentos'] = DepartamentoIncidenciaAsig.objects.filter(incidenciaasignada__solicitusecret__id=request.GET['idinfo'])
                    if 'asigna' in request.GET:
                        data['asigna'] = request.GET['asigna']
                    return render(request ,"asuntoestudiantil/verdepartamentos.html" ,  data)

                elif action=='verdepartamentosinciden':
                    data = {}
                    data['departamentos'] = DepartamentoIncidenciaAsig.objects.filter(incidenciaasignada__incidenciaadministrativo__id=request.GET['idinfo'])
                    if 'asigna' in request.GET:
                        data['asigna'] = request.GET['asigna']
                    return render(request ,"asuntoestudiantil/verdepartamentos.html" ,  data)


                elif action=='detallpartamentos':
                    data = {}
                    if 'asigna' in request.GET and request.GET['asigna'] == '1':
                        data['asigna'] = request.GET['asigna']
                        data['observaciones'] = ObservacionIncidencia.objects.filter(departamentoincidenciaasig__id=request.GET['iddepart'],respuestadepart='')
                    else:
                        if 'asigna' in request.GET and request.GET['asigna'] == '2':
                            data['asigna'] = request.GET['asigna']
                            data['observaciones'] = ObservacionIncidencia.objects.filter(departamentoincidenciaasig__id=request.GET['iddepart']).exclude(respuestadepart='')
                        else:
                            if 'asigna' in request.GET and request.GET['asigna'] == '3':
                                data['asigna'] = '2'
                            data['observaciones'] = ObservacionIncidencia.objects.filter(departamentoincidenciaasig__id=request.GET['iddepart'])
                    return render(request ,"asuntoestudiantil/detalledepartamentcorreo.html" ,  data)

                elif action=='correos':
                    p =request.session['persona']
                    if not Modulo.objects.filter(modulogrupo__grupos__in=p.usuario.groups.all(), url=request.path[1:]).exists():
                        return HttpResponseRedirect("/")
                    if AsistAsuntoEstudiant.objects.filter(asistente__usuario=request.user).exists():
                        data['asistente']= AsistAsuntoEstudiant.objects.filter(asistente__usuario=request.user)[:1].get()

                    else:
                        departamentos = request.user.groups.filter().values('id')
                        data['departamento'] = DepartamentoIncidenciaAsig.objects.filter(departamento__id__in=departamentos,atendiendo=True).values('incidenciaasignada')
                        data['departa']=1
                    search = None
                    todos = None
                    activos = None
                    finalizados = None
                    band=0
                    if 's' in request.GET:
                        search = request.GET['s']
                        band=1
                    if 'a' in request.GET:
                        activos = request.GET['a']
                    if 'f' in request.GET:
                        finalizados = request.GET['f']
                    if 't' in request.GET:
                        todos = request.GET['t']

                    if 'asistente' in data:
                        if search:
                            ss = search.split(' ')
                            while '' in ss:
                                ss.remove('')
                            if len(ss)==1:
                                solicitudes = SolicituInfo.objects.filter((Q(Q(nombres__icontains=search) | Q(codigo__icontains=search) | Q(identificacion=search))),incidenciaasignada__asistenteasignado__asistente__usuario=request.user,incidenciaasignada__atendiendo=True).order_by('-codigo')
                            else:
                                solicitudes = SolicituInfo.objects.filter((Q(Q(nombres__icontains=search) | Q(codigo__icontains=search))),incidenciaasignada__asistenteasignado__asistente__usuario=request.user,incidenciaasignada__atendiendo=True).order_by('-codigo')

                        else:
                            solicitudes = SolicituInfo.objects.filter(Q(incidenciaasignada__asistenteasignado__asistente__usuario=request.user,finalizado=False,incidenciaasignada__atendiendo=True) | Q(finalizado=False,incidenciaasignada=None)).order_by('-codigo')

                        if todos:
                            solicitudes = SolicituInfo.objects.filter(Q(incidenciaasignada__asistenteasignado__asistente__usuario=request.user,finalizado=False,incidenciaasignada__atendiendo=True) | Q(finalizado=False,incidenciaasignada=None)).order_by('-codigo')



                        if finalizados:
                            data['finalizados'] = finalizados
                            solicitudes = SolicituInfo.objects.filter(incidenciaasignada__asistenteasignado__asistente__usuario=request.user,finalizado=True,incidenciaasignada__atendiendo=True).order_by('-codigo')
                    else:

                        if search:
                            ss = search.split(' ')
                            while '' in ss:
                                ss.remove('')
                            if len(ss)==1:
                                solicitudes = SolicituInfo.objects.filter((Q(Q(nombres__icontains=search) | Q(codigo__icontains=search) | Q(identificacion=search))),incidenciaasignada__id__in=data['departamento']).order_by('-codigo')
                            else:
                                solicitudes = SolicituInfo.objects.filter((Q(Q(nombres__icontains=search) | Q(codigo__icontains=search))),incidenciaasignada__id__in=data['departamento']).order_by('-codigo')
                        else:
                            solicitudes = SolicituInfo.objects.filter(incidenciaasignada__id__in=data['departamento'],finalizado=False).order_by('-codigo')

                        if todos:
                            solicitudes = SolicituInfo.objects.filter(incidenciaasignada__id__in=data['departamento'],finalizado=False).order_by('-codigo')

                        if finalizados:
                            data['finalizados'] = finalizados
                            solicitudes = SolicituInfo.objects.filter(incidenciaasignada__id__in=data['departamento'],finalizado=True).order_by('-codigo')


                    paging = MiPaginador(solicitudes, 30)
                    p = 1
                    try:
                        if 'page' in request.GET:
                            p = int(request.GET['page'])
                            # if band==0:
                            #     inscripciones = Inscripcion.objects.all().order_by('persona__apellido1')
                            paging = MiPaginador(solicitudes, 30)
                        page = paging.page(p)
                    except Exception as ex:
                        page = paging.page(1)

                    # Para atencion al cliente

                    data['paging'] = paging
                    data['rangospaging'] = paging.rangos_paginado(p)
                    data['page'] = page
                    data['search'] = search if search else ""
                    data['todos'] = todos if todos else ""
                    data['solicitudes'] = page.object_list

                    if 'error' in request.GET:
                        data['errordep'] = request.GET['error']
                    if 'iddepart' in request.GET:
                        observacionincidencia = ObservacionIncidencia.objects.filter(departamentoincidenciaasig__id=request.GET['iddepart'])[:1].get()
                        data['observacionincidencia'] = observacionincidencia
                    data['fechaactual'] = datetime.now().date()
                    gruposexcluidos = [PROFESORES_GROUP_ID,ALUMNOS_GROUP_ID]
                    data['departamentos'] = Group.objects.filter(id__in=ID_DEPARTAMENTO_ASUNTO_ESTUDIANT).exclude(user=None).exclude(id__in=gruposexcluidos).order_by('name')
                    return render(request ,"seguimiento/seguimiento.html" ,  data)

                elif action=='incidenciaadminis':
                    p =request.session['persona']
                    if not Modulo.objects.filter(modulogrupo__grupos__in=p.usuario.groups.all(), url=request.path[1:]).exists():
                        return HttpResponseRedirect("/")

                    if AsistAsuntoEstudiant.objects.filter(asistente__usuario=request.user).exists():
                        data['asistente']= AsistAsuntoEstudiant.objects.filter(asistente__usuario=request.user)[:1].get()

                    else:
                        departamentos = request.user.groups.filter().values('id')
                        data['departamento'] = DepartamentoIncidenciaAsig.objects.filter(departamento__id__in=departamentos,atendiendo=True).values('incidenciaasignada')
                        data['departa']=1
                    search = None
                    todos = None
                    finalizados = None
                    band=0

                    if 's' in request.GET:
                        search = request.GET['s']
                        band=1

                    if 't' in request.GET:
                        todos = request.GET['i']
                    if 'f' in request.GET:
                        finalizados = request.GET['f']

                    if 'asistente' in data:
                        if search:
                            incidenciaadministrativo = IncidenciaAdministrativo.objects.filter(nombre__icontains=search,incidenciaasignada__asistenteasignado__asistente__usuario=request.user,incidenciaasignada__atendiendo=True).order_by('id')
                        else:
                            incidenciaadministrativo = IncidenciaAdministrativo.objects.filter(Q(finalizado=False,incidenciaasignada__asistenteasignado__asistente__usuario=request.user,incidenciaasignada__atendiendo=True) | Q(finalizado=False,incidenciaasignada=None)).order_by('id')

                        if finalizados:
                            incidenciaadministrativo = IncidenciaAdministrativo.objects.filter(finalizado = True,incidenciaasignada__asistenteasignado__asistente__usuario=request.user,incidenciaasignada__atendiendo=True).order_by('-fechafinaliza','id')
                        if todos:
                            incidenciaadministrativo = IncidenciaAdministrativo.objects.filter(Q(finalizado=False,incidenciaasignada__asistenteasignado__asistente__usuario=request.user,incidenciaasignada__atendiendo=True) | Q(finalizado=False,incidenciaasignada=None)).order_by('id')

                    else:
                        if search:
                            incidenciaadministrativo = IncidenciaAdministrativo.objects.filter(nombre__icontains=search,incidenciaasignada__id__in=data['departamento']).order_by('id')
                        else:
                            incidenciaadministrativo = IncidenciaAdministrativo.objects.filter(finalizado=False,incidenciaasignada__id__in=data['departamento']).order_by('id')
                        if todos:
                            incidenciaadministrativo = IncidenciaAdministrativo.objects.filter(finalizado=False,incidenciaasignada__id__in=data['departamento']).order_by('id')



                    paging = MiPaginador(incidenciaadministrativo, 30)
                    p = 1
                    try:
                        if 'page' in request.GET:
                            p = int(request.GET['page'])
                            paging = MiPaginador(incidenciaadministrativo, 30)
                        page = paging.page(p)
                    except Exception as ex:
                        page = paging.page(1)

                    # Para atencion al cliente
                    if "error" in request.GET:
                        data['error'] = request.GET['error']

                    if 'iddepart' in request.GET:
                        observacionincidencia = ObservacionIncidencia.objects.filter(departamentoincidenciaasig__id=request.GET['iddepart'])[:1].get()
                        data['observacionincidencia'] = observacionincidencia

                    data['paging'] = paging
                    data['rangospaging'] = paging.rangos_paginado(p)
                    data['page'] = page
                    data['search'] = search if search else ""
                    data['todos'] = todos if todos else ""
                    data['finalizados'] = finalizados if finalizados else ""
                    data['incidenciaadministrativo'] = page.object_list
                    data['asistasuntoestudiant'] = AsistAsuntoEstudiant.objects.filter(estado=True)
                    gruposexcluidos = [PROFESORES_GROUP_ID,ALUMNOS_GROUP_ID]
                    data['departamentos'] = Group.objects.filter(id__in=ID_DEPARTAMENTO_ASUNTO_ESTUDIANT).exclude(user=None).exclude(id__in=gruposexcluidos).order_by('name')

                    return render(request ,"asuntoestudiantil/incidenciadministrativa.html" ,  data)

                elif action=='solicitudes':

                    p =request.session['persona']
                    if not Modulo.objects.filter(modulogrupo__grupos__in=p.usuario.groups.all(), url=request.path[1:]).exists():
                        return HttpResponseRedirect("/")

                    if AsistAsuntoEstudiant.objects.filter(asistente__usuario=request.user).exists():
                        data['asistente']= AsistAsuntoEstudiant.objects.filter(asistente__usuario=request.user)[:1].get()
                    else:
                        departamentos = request.user.groups.filter().values('id')
                        data['departamento'] = DepartamentoIncidenciaAsig.objects.filter(departamento__id__in=departamentos,atendiendo=True).values('incidenciaasignada')
                        data['departa'] = 1

                    if 'asistente' in data:
                        # if search:
                        #     incidenciaadministrativo = IncidenciaAdministrativo.objects.filter(nombre__icontains=search,incidenciaasignada__asistenteasignado__asistente__usuario=request.user,incidenciaasignada__atendiendo=True).order_by('id')
                        # else:
                        #     incidenciaadministrativo = IncidenciaAdministrativo.objects.filter(finalizado=False,incidenciaasignada__asistenteasignado__asistente__usuario=request.user,incidenciaasignada__atendiendo=True).order_by('id')

                        if 'cerra' in request.GET:
                            solicitudes = SolicitudSecretariaDocente.objects.filter(incidenciaasignada__asistenteasignado__asistente__usuario=request.user,cerrada=True,incidenciaasignada__atendiendo=True).order_by('-fecha','-hora')
                            data['cerrado'] = 'cerra'
                        else:
                            solicitudes = SolicitudSecretariaDocente.objects.filter(Q(incidenciaasignada__asistenteasignado__asistente__usuario=request.user,cerrada=False,incidenciaasignada__atendiendo=True)| Q(cerrada=False,incidenciaasignada=None)).order_by('-fecha','-hora')

                    else:
                        # if search:
                        #     incidenciaadministrativo = IncidenciaAdministrativo.objects.filter(nombre__icontains=search,incidenciaasignada__asistenteasignado__asistente__usuario__groups__id__in=departamentos).order_by('id')
                        # else:
                        #     incidenciaadministrativo = IncidenciaAdministrativo.objects.filter(finalizado=False,incidenciaasignada__asistenteasignado__asistente__usuario__groups__id__in=departamentos).order_by('id')

                        if 'cerra' in request.GET:
                            solicitudes = SolicitudSecretariaDocente.objects.filter(incidenciaasignada__id__in=data['departamento'],cerrada=True).order_by('-fecha','-hora')
                            data['cerrado'] = 'cerra'
                        else:
                            solicitudes = SolicitudSecretariaDocente.objects.filter(incidenciaasignada__id__in=data['departamento'],cerrada=False).order_by('-fecha','-hora')




                    paging = MiPaginador(solicitudes, 30)
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
                    data['solicitudes'] = page.object_list
                    data['fechaactual'] = datetime.now().date()
                    data['asistasuntoestudiant'] = AsistAsuntoEstudiant.objects.filter(estado=True)
                    gruposexcluidos = [PROFESORES_GROUP_ID,ALUMNOS_GROUP_ID]
                    data['departamentos'] = Group.objects.filter(id__in=ID_DEPARTAMENTO_ASUNTO_ESTUDIANT).exclude(user=None).exclude(id__in=gruposexcluidos).order_by('name')

                    if 'error' in request.GET:
                        data['error'] = request.GET['error']

                    if 'iddepart' in request.GET:
                        observacionincidencia = ObservacionIncidencia.objects.filter(departamentoincidenciaasig__id=request.GET['iddepart'])[:1].get()
                        data['observacionincidencia'] = observacionincidencia

                    return render(request ,"solicitudes/solicitudesbs.html" ,  data)
            else:
                p =request.session['persona']
                if not Modulo.objects.filter(modulogrupo__grupos__in=p.usuario.groups.all(), url=request.path[1:]).exists():
                    return HttpResponseRedirect("/")
                if AsistAsuntoEstudiant.objects.filter(asistente__usuario=request.user).exists():
                    data['asistente']= AsistAsuntoEstudiant.objects.filter(asistente__usuario=request.user)[:1].get()

                return render(request ,"asuntoestudiantil/menu.html" ,  data)
    except Exception as ex:
        return HttpResponseRedirect('/?info=Error'+str(ex))