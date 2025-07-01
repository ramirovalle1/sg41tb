from datetime import datetime,timedelta
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.contrib.contenttypes.models import ContentType
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
from decorators import secure_module
from sga.commonviews import addUserData, ip_client_address
from sga.forms import SolicitudSecretariaDocenteForm, PersonalSolicitudForm, SeguimientoEspecieForm, AprobacionSolicitudForm
from sga.models import SolicitudSecretariaDocente, AsistAsuntoEstudiant, IncidenciaAsignada, DepartamentoIncidenciaAsig,SolicitudesGrupo, TipoSolicitudSecretariaDocente, GrupoCorreo, Persona, Inscripcion, ModuloGrupo, AsistenteDepartamento, Departamento, elimina_tildes, SesionCaja, HorarioAsistenteSolicitudes
from django.db.models.query_utils import Q
from settings import EMAIL_ACTIVE, PROFESORES_GROUP_ID, ALUMNOS_GROUP_ID, ID_DEPARTAMENTO_ASUNTO_ESTUDIANT, SISTEMAS_GROUP_ID, ID_TIPO_SOLICITUD,TIPO_RUBRO_SOLICITUD
from sga.tasks import gen_passwd, send_html_mail
import json
from django.http import HttpResponse, HttpResponseRedirect

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
    data = {'title': 'Solicitudes de Estudiantes'}
    addUserData(request, data)
    if request.method=='POST':
        if 'action' in request.POST:
            action = request.POST['action']
            if action=='comentar':
                f = SolicitudSecretariaDocenteForm(request.POST,
                            instance=SolicitudSecretariaDocente.objects.get(pk=request.POST['id']))
                f.instance.fecha = datetime.now()
                # f.instance.hora = datetime.now().time()
                f.instance.cerrada = False
                if f.is_valid():
                    f.save()
                    f.instance.mail_subject_comentar()
                return HttpResponseRedirect("/solicitudes")
            elif action == 'asignasitente':
                try:
                    if not IncidenciaAsignada.objects.filter(solicitusecret__id=request.POST['idsolici'],asistenteasignado__id=request.POST['idasist']).exists():
                        incidenciaasignada = IncidenciaAsignada(solicitusecret_id = request.POST['idsolici'],
                                                                observacion = request.POST['observacion'],
                                                                asistenteasignado_id = request.POST['idasist'],
                                                                atendiendo = True,
                                                                fecha=datetime.now())
                        incidenciaasignada.save()
                        incidenciaasignada.solicitusecret.asignado = True
                        incidenciaasignada.solicitusecret.save()
                        if IncidenciaAsignada.objects.filter(solicitusecret=incidenciaasignada.solicitusecret,atendiendo=True).exclude(id=incidenciaasignada.id).order_by('id').exists():
                            incidenciaasignadaanterior = IncidenciaAsignada.objects.filter(solicitusecret=incidenciaasignada.solicitusecret,atendiendo=True).exclude(asistenteasignado=incidenciaasignada.asistenteasignado).order_by('id')[:1].get()
                            incidenciaasignadaanterior.atendiendo = False
                            incidenciaasignadaanterior.fecha=datetime.now()
                            incidenciaasignadaanterior.save()
                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(incidenciaasignada).pk,
                            object_id       = incidenciaasignada.id,
                            object_repr     = force_str(incidenciaasignada),
                            action_flag     = ADDITION,
                            change_message  = 'Asignado Asistente a Solicitud de Alumnos (' + client_address + ')' )

                    else:
                        if IncidenciaAsignada.objects.filter(solicitusecret__id=request.POST['idsolici'],asistenteasignado__id=request.POST['idasist'],atendiendo=False).exists():
                            incidenciaasignada = IncidenciaAsignada.objects.filter(solicitusecret__id=request.POST['idsolici'],asistenteasignado__id=request.POST['idasist'],atendiendo=False)[:1].get()
                            incidenciaasignada.atendiendo=True
                            incidenciaasignada.observacion=request.POST['observacion']
                            incidenciaasignada.fecha=datetime.now()
                            incidenciaasignada.save()
                            if IncidenciaAsignada.objects.filter(solicitusecret=incidenciaasignada.solicitusecret,atendiendo=True).exclude(id=incidenciaasignada.id).order_by('id').exists():
                                incidenciaasignadaanterior = IncidenciaAsignada.objects.filter(solicitusecret=incidenciaasignada.solicitusecret,atendiendo=True).exclude(asistenteasignado=incidenciaasignada.asistenteasignado).order_by('id')[:1].get()
                                incidenciaasignadaanterior.atendiendo = False
                                incidenciaasignadaanterior.fecha=datetime.now()
                                incidenciaasignadaanterior.save()
                            client_address = ip_client_address(request)
                            LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(incidenciaasignada).pk,
                                object_id       = incidenciaasignada.id,
                                object_repr     = force_str(incidenciaasignada),
                                action_flag     = ADDITION,
                                change_message  = 'Asistente Reasignado  a Solicitud de Alumnos  (' + client_address + ')' )

                    return HttpResponseRedirect("/solicitudes")
                except Exception as ex:
                    return HttpResponseRedirect("/solicitudes?error=Error Vuelva  intentarlo")

            elif action =='addgestion':
                try:
                    solicitud = SolicitudSecretariaDocente.objects.filter(pk=request.POST['idsol'])[:1].get()
                    asis=None
                    if AsistenteDepartamento.objects.filter(departamento=solicitud.departamento,persona=solicitud.personaasignada,activo=True).exists():
                        asis=AsistenteDepartamento.objects.filter(departamento=solicitud.departamento,persona=solicitud.personaasignada,activo=True)[:1].get()

                    seguimiento = IncidenciaAsignada(solicitusecret=solicitud,
                                                     observacion=request.POST['observacion'],
                                                     usuario = request.user,
                                                     asistentedepartamento=asis,
                                                     fecha = datetime.now())
                    seguimiento.save()
                    return HttpResponse(json.dumps({"result":"ok"}), content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({"result":str(e)}), content_type="application/json")
            elif action == 'cambiotipo':
                try:
                    if SolicitudSecretariaDocente.objects.filter(pk=request.POST['idsolici']).exists():
                        departamento = Departamento.objects.filter(pk=request.POST['idtipo'])[:1].get()
                        solicitud = SolicitudSecretariaDocente.objects.get(pk=request.POST['idsolici'])
                        asis=None
                        if AsistenteDepartamento.objects.filter(departamento=solicitud.departamento,persona=solicitud.personaasignada,activo=True).exists():
                             asis=AsistenteDepartamento.objects.filter(departamento=solicitud.departamento,persona=solicitud.personaasignada,activo=True)[:1].get()

                        # solicitud.tipo_id=request.POST['idtipo']
                        fechaant = solicitud.fechaasignacion
                        solicitud.fecha = datetime.now()
                        # solicitud.hora = datetime.now().time()
                        solicitud.observacion=request.POST['observacion']
                        # solicitud.group_id=grupoorigen.grupo.id
                        solicitud.usuario=request.user
                        solicitud.save()
                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(solicitud).pk,
                            object_id       = solicitud.id,
                            object_repr     = force_str(solicitud),
                            action_flag     = CHANGE,
                            change_message  = 'Cambio de tipo a Solicitud de Alumnos (' + client_address + ')' )
                        incidenciaasignada = IncidenciaAsignada(solicitusecret = solicitud,
                                                                observacion = request.POST['observacion'],
                                                                usuario=request.user,
                                                                asistentedepartamento=asis,
                                                                fecha=datetime.now())
                        incidenciaasignada.save()
                        incidenciaasignada = IncidenciaAsignada(solicitusecret = solicitud,
                                                                observacion ='CAMBIO DE DEPARTAMENTO',
                                                                usuario=request.user,
                                                                fechaasig=fechaant,
                                                                asistenteasig = solicitud.personaasignada.usuario,
                                                                asistentedepartamento=asis,
                                                                fecha=datetime.now())
                        incidenciaasignada.save()

                        if solicitud.personaasignada:
                            asis =  AsistenteDepartamento.objects.filter(persona__usuario=solicitud.personaasignada.usuario,activo=True)[:1].get()
                            if not asis.cantidadsol:
                                asis.cantidadsol=0

                            asis.cantidadsol = asis.cantidadsol - 1
                            asis.save()
                        asistentes=None
                        if departamento.id == 27:
                            cajeros = SesionCaja.objects.filter(abierta=True).values('caja__persona')
                            if HorarioAsistenteSolicitudes.objects.filter(fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time()).exists():
                                 horarioasis = HorarioAsistenteSolicitudes.objects.filter(fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time()).values('usuario')
                                 asistentes = AsistenteDepartamento.objects.filter(departamento=departamento,persona__usuario__id__in=horarioasis,persona__id__in=cajeros,activo=True).exclude(puedereasignar=True).order_by('cantidadsol')
                            # asistentes  = AsistenteDepartamento.objects.filter(departamento=departamento,persona__id__in=cajeros).exclude(puedereasignar=True).order_by('cantidadsol')
                        else:
                            # asistentes = AsistenteDepartamento.objects.filter(departamento=e.departamento).exclude(puedereasignar=True).order_by('cantidadsol')

                            if HorarioAsistenteSolicitudes.objects.filter(fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time()).exists():
                                 horarioasis = HorarioAsistenteSolicitudes.objects.filter(fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time()).values('usuario')
                                 asistentes = AsistenteDepartamento.objects.filter(departamento=departamento,persona__usuario__id__in=horarioasis,activo=True).exclude(puedereasignar=True).order_by('cantidadsol')
                        if asistentes:
                            asistente = asistentes.filter()[:1].get()
                            solicitud.personaasignada = asistente.persona
                            solicitud.departamento=departamento
                            solicitud.fechaasignacion = datetime.now()
                            solicitud.save()
                            if not asistente.cantidadsol :
                                asistente.cantidadsol= 0
                                asistente.save()
                            asistente.cantidadsol = asistente.cantidadsol + 1
                            asistente.save()

                            # notificacion de cambio de tipo de solicitud
                            correo=''
                            asistente.correo_reasignacion_solicitud(request.user,solicitud)
                        else:
                            solicitud.departamento=departamento
                            solicitud.personaasignada = None
                            solicitud.save()

                        return HttpResponseRedirect("/solicitudes")
                except Exception as ex:
                    print(ex)
                    return HttpResponseRedirect("/solicitudes?error=Error Vuelva  intentarlo")

            elif action == 'asignarpersona':
                try:
                    if SolicitudSecretariaDocente.objects.filter(pk=request.POST['solicitud']).exists():
                        solicitud = SolicitudSecretariaDocente.objects.get(pk=request.POST['solicitud'])
                        solicitud.asignado=True
                        solicitud.personaasignada_id=request.POST['persona']
                        solicitud.observacionasignada=request.POST['observacion']
                        solicitud.fechaasignacion = datetime.now()
                        solicitud.usuarioasigna=request.user
                        solicitud.save()

                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(solicitud).pk,
                            object_id       = solicitud.id,
                            object_repr     = force_str(solicitud),
                            action_flag     = CHANGE,
                            change_message  = 'Asigna Persona a Solicitud de Alumnos (' + client_address + ')' )

                        # notificacion de cambio de tipo de solicitud
                        if EMAIL_ACTIVE:
                            if Persona.objects.filter(pk=request.POST['persona']).exists():
                                correo=Persona.objects.filter(pk=request.POST['persona'])[:1].get()
                                correo=correo.emailinst
                                hoy = datetime.now().today()
                                contenido = "Asignacion de Solicitud"
                                descripcion = "Favor revisar y finalizar lo antes posible. Puede consultarla en el Modulo Solicitudes de Alumnos."

                                send_html_mail(contenido,
                                "emails/nuevasolicitud.html", {'d': solicitud, 'fecha': hoy,'contenido': contenido,'descripcion':descripcion,'opcion':'3'},correo.split(','))
                        return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as ex:
                    print(ex)
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
            elif action =='reasignarusuario':
                try:
                    # usuario=User.objects.filter(id=request.POST['usuario'])

                    # persona = Persona.objects.filter(usuario=usuario)[:1].get()
                    solicitud = SolicitudSecretariaDocente.objects.filter(pk=request.POST['id'])[:1].get()
                    asistente = AsistenteDepartamento.objects.filter(id=request.POST['usuario'])[:1].get()
                    asis=None
                    if solicitud.personaasignada:
                        # asis =  AsistenteDepartamento.objects.filter(persona=solicitud.personaasignada,departamento=asistente.departamento,activo=True)[:1].get()
                        asis =  AsistenteDepartamento.objects.filter(persona=solicitud.personaasignada,departamento=asistente.departamento)[:1].get()
                        asis.cantidadsol= asis.cantidadsol - 1
                        asis.save()
                    fechaant = solicitud.fechaasignacion
                    personant = solicitud.personaasignada
                    solicitud.personaasignada = Persona.objects.get(usuario=asistente.persona.usuario)
                    solicitud.fechaasignacion = datetime.now()
                    solicitud.departamento = asistente.departamento
                    solicitud.save()
                    asistente.cantidadsol = asistente.cantidadsol + 1

                    asistente.save()
                    incidenciaasignada = IncidenciaAsignada(solicitusecret = solicitud,
                                                                observacion = 'REASIGNACION DE USUARIO',
                                                                fechaasig=fechaant,
                                                                asistenteasig = personant.usuario,
                                                                usuario=request.user,
                                                                asistentedepartamento=asis,
                                                                fecha=datetime.now())
                    incidenciaasignada.save()
                    asistente.correo_reasignacion_solicitud(request.user,solicitud)
                    # client_address = ip_client_address(request)
                    # LogEntry.objects.log_action(
                    #     user_id         = request.user.pk,
                    #     content_type_id = ContentType.objects.get_for_model(solicitud).pk,
                    #     object_id       = solicitud.id,
                    #     object_repr     = force_str(solicitud),
                    #     action_flag     = CHANGE,
                    #     change_message  = 'Reasignado Solicitud de Alumnos (' + client_address + ')' )
                    return HttpResponse(json.dumps({"result":"ok" }), content_type="application/json")
                except Exception as e:
                    # print(e)
                    return HttpResponse(json.dumps({"result":"bad",'e':str(e)}),content_type="application/json")

            elif action =='reasignarusuarioengrupo':
                try:
                    asistenteactual = AsistenteDepartamento.objects.filter(pk=request.POST['id'])[:1].get()
                    solicitudes = SolicitudSecretariaDocente.objects.filter(personaasignada=asistenteactual.persona, cerrada=False)
                    asistentenuevo = AsistenteDepartamento.objects.filter(id=request.POST['usuario'],activo=True)[:1].get()
                    for sol in solicitudes:
                        fechaant = sol.fechaasignacion
                        personant = sol.personaasignada
                        asistenteactual.cantidadsol = asistenteactual.cantidadsol - 1
                        asistenteactual.save()
                        sol.personaasignada = asistentenuevo.persona
                        sol.fechaasignacion = datetime.now()
                        sol.departamento = asistentenuevo.departamento
                        sol.save()
                        asistentenuevo.cantidadsol = asistentenuevo.cantidadsol + 1
                        asistentenuevo.save()
                        incidenciaasignada = IncidenciaAsignada(solicitusecret = sol,
                                                                observacion = 'REASIGNACION DE USUARIO',
                                                                fechaasig=fechaant,
                                                                asistenteasig = personant.usuario,
                                                                usuario=request.user,
                                                                asistentedepartamento=asistenteactual,
                                                                fecha=datetime.now())
                        incidenciaasignada.save()
                        asistentenuevo.correo_reasignacion_solicitud(request.user,sol)

                    return HttpResponse(json.dumps({"result":"ok" }), content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({"result":"bad",'e':str(e)}),content_type="application/json")

            elif action =='reasignaenlote':
                asistentes=None
                try:
                    asistenteactual = AsistenteDepartamento.objects.filter(pk=request.POST['id'])[:1].get()
                    solicitudes = SolicitudSecretariaDocente.objects.filter(personaasignada=asistenteactual.persona, cerrada=False)
                    cajeros = SesionCaja.objects.filter(abierta=True).values('caja__persona')
                    if HorarioAsistenteSolicitudes.objects.filter(fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time()).exists():
                         horarioasis = HorarioAsistenteSolicitudes.objects.filter(fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time()).values('usuario')
                         asistentes = AsistenteDepartamento.objects.filter(departamento=asistenteactual.departamento,persona__usuario__id__in=horarioasis,persona__id__in=cajeros,activo=True).exclude(puedereasignar=True).exclude(cantidadsol__gte=10).order_by('cantidadsol')

                    for sol in solicitudes:
                        fechaant = sol.fechaasignacion
                        personant = sol.personaasignada

                        for asis in asistentes:
                            if asis.cantidadsol < 10:
                                asis.cantidadsol =asis.cantidadsol +1
                                sol.usuario = asis.persona.usuario
                                sol.personaasignada =asis.persona
                                sol.fechaasignacion = datetime.now()
                                sol.departamento = asis.departamento
                                sol.usuarioasigna.id=request.user.id,
                                sol.save()
                                asis.save()
                                asistenteactual.cantidadsol = asistenteactual.cantidadsol - 1
                                asistenteactual.save()
                                asis.correo_reasignacion_solicitud(request.user,sol)

                                incidenciaasignada = IncidenciaAsignada(solicitusecret = sol,
                                                                        observacion = 'REASIGNACION DE USUARIO',
                                                                        fechaasig=fechaant,
                                                                        asistenteasig = personant.usuario,
                                                                        usuario=request.user,
                                                                        asistentedepartamento=asistenteactual,
                                                                        fecha=datetime.now())
                                incidenciaasignada.save()
                    if not asistentes:
                        return HttpResponse(json.dumps({"result":"bad2"}),content_type="application/json")

                    return HttpResponse(json.dumps({"result":"ok" }), content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({"result":"bad",'e':str(e)}),content_type="application/json")

            # OCastillo reasignacion por marcacion
            elif action =='reasignarusuariopormarcacion':
                try:
                    asistenteactual = AsistenteDepartamento.objects.filter(pk=request.POST['id'])[:1].get()
                    datos = request.POST['datos']
                    asistentenuevo = AsistenteDepartamento.objects.filter(id=request.POST['usuario'],activo=True)[:1].get()
                    if datos:
                        datos = json.loads(request.POST['datos'])

                        for reg in datos:
                            sol = SolicitudSecretariaDocente.objects.get(pk=datos[reg]['trans'])
                            fechaant = sol.fechaasignacion
                            personant = sol.personaasignada
                            asistenteactual.cantidadsol = asistenteactual.cantidadsol - 1
                            asistenteactual.save()
                            sol.personaasignada = asistentenuevo.persona
                            sol.fechaasignacion = datetime.now()
                            sol.departamento = asistentenuevo.departamento
                            sol.save()
                            asistentenuevo.cantidadsol = asistentenuevo.cantidadsol + 1
                            asistentenuevo.save()
                            incidenciaasignada = IncidenciaAsignada(solicitusecret = sol,
                                                                observacion = 'REASIGNACION DE USUARIO',
                                                                fechaasig=fechaant,
                                                                asistenteasig = personant.usuario,
                                                                usuario=request.user,
                                                                asistentedepartamento=asistenteactual,
                                                                fecha=datetime.now())
                            incidenciaasignada.save()
                            asistentenuevo.correo_reasignacion_solicitud(request.user,sol)

                    return HttpResponse(json.dumps({"result":"ok" }), content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({"result":"bad",'e':str(e)}),content_type="application/json")

            elif action =='consultaasis':
                data = {}
                try:
                    usuarios=[]
                    solicitud = SolicitudSecretariaDocente.objects.filter(pk=request.POST['id'])[:1].get()

                    dpto = Departamento.objects.filter(controlespecies=True,asistentedepartamento__persona__usuario = solicitud.personaasignada.usuario).values('id')
                    for a in AsistenteDepartamento.objects.filter(departamento__id__in =dpto,activo=True).order_by('persona__apellido1','persona__apellido2','persona__nombres').exclude(persona__usuario= solicitud.personaasignada.usuario).exclude(puedereasignar=True):

                        usuarios.append({'id':a.id,'usuario': elimina_tildes(a.persona.usuario.username) })
                    data['result'] = 'ok'
                    data['usuarios'] = usuarios
                    return HttpResponse(json.dumps(data), content_type="application/json")
                except Exception as e:
                    print(e)
                    return HttpResponse(json.dumps({"result":"bad",'e':str(e)}),content_type="application/json")

            elif action =='consultaasiscaja':
                data = {}
                try:
                    usuarios=[]
                    asistente = AsistenteDepartamento.objects.filter(pk=request.POST['id'])[:1].get()

                    dpto = Departamento.objects.filter(controlespecies=True,asistentedepartamento = asistente).values('id')

                    for a in AsistenteDepartamento.objects.filter(departamento__id__in =dpto,activo=True).order_by('persona__apellido1','persona__apellido2','persona__nombres').exclude(pk=asistente.id).exclude(puedereasignar=True):

                        usuarios.append({'id':a.id,'usuario': elimina_tildes(a.persona.usuario.username) })
                    data['result'] = 'ok'
                    data['usuarios'] = usuarios
                    return HttpResponse(json.dumps(data), content_type="application/json")
                except Exception as e:
                    print(e)
                    return HttpResponse(json.dumps({"result":"bad",'e':str(e)}),content_type="application/json")

            elif action == "finalizasol":
                try:
                        solicitud = SolicitudSecretariaDocente.objects.filter(id = request.POST['idsolici'])[:1].get()
                        solicitud.observacion = request.POST['observacionresp']
                        solicitud.resolucion = request.POST['resolucion']
                        solicitud.fechacierre = datetime.now()
                        solicitud.hora = datetime.now().time()
                        solicitud.usuario = request.user
                        solicitud.cerrada = True
                        solicitud.group_id=request.POST['idgrupo']
                        solicitud.save()

                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(solicitud).pk,
                            object_id       = solicitud.id,
                            object_repr     = force_str(solicitud),
                            action_flag     = ADDITION,
                            change_message  = 'Solicitud Alumno finalizado (' + client_address + ')' )

                        asis =  AsistenteDepartamento.objects.filter(persona__usuario=solicitud.personaasignada.usuario)[:1].get()
                        asis.cantidadsol = asis.cantidadsol - 1
                        asis.save()
                        if EMAIL_ACTIVE:
                            #notificacion de finalizacion de solicitud
                            #traigo el correo del estudiante que genero la solicitud
                            correo =(str(solicitud.persona.email))
                            inscripcion=Inscripcion.objects.filter(persona=solicitud.persona_id)[:1].get()
                            personarespon = Persona.objects.filter(usuario=solicitud.usuario)[:1].get()
                            #traigo el correo del grupo a quien le corresponde el tipo de solicitud
                            if SolicitudesGrupo.objects.filter(tiposolic=solicitud.tipo,carrera=inscripcion.carrera.id).exists():
                                grupo_solicitud=SolicitudesGrupo.objects.filter(tiposolic=solicitud.tipo,carrera=inscripcion.carrera.id).values('grupo')
                                if ModuloGrupo.objects.filter(grupos__in=grupo_solicitud).exists():
                                    correo_solicitud=[]
                                    for correo_grupo in ModuloGrupo.objects.filter(grupos__in=grupo_solicitud):
                                        correo_solicitud.append(correo_grupo.correo)
                                        if correo:
                                            correo = correo+','+correo_grupo.correo
                                        else:
                                            correo = correo_grupo.correo
                            else:
                                #Para el caso de una solicitud tipo general para todas las carreras
                                if SolicitudesGrupo.objects.filter(tiposolic=solicitud.tipo,todas_carreras=True).exists():
                                    grupo_solicitud=SolicitudesGrupo.objects.filter(tiposolic=solicitud.tipo,todas_carreras=True).values('grupo')
                                    if ModuloGrupo.objects.filter(grupos__in=grupo_solicitud).exists():
                                       correo_solicitud=[]
                                       for correo_grupo in ModuloGrupo.objects.filter(grupos__in=grupo_solicitud):
                                           correo_solicitud.append(correo_grupo.correo)
                                           if correo:
                                                correo = correo+','+correo_grupo.correo
                                           else:
                                                correo = correo_grupo.correo

                            hoy = datetime.now().today()
                            personarespon = Persona.objects.filter(usuario=request.user)[:1].get()

                            send_html_mail("FINALIZACION DE SOLICITUD",
                                "emails/correo_finsolicituddpto.html", {'contenido': "FINALIZACION DE SOLICITUD", 'self': solicitud, 'personarespon': personarespon.nombre_completo(), 'fecha': hoy},correo.split())

                        return HttpResponseRedirect("/solicitudes")
                except Exception as ex:
                    print(ex)
                    return HttpResponseRedirect("/solicitudes?error=Error Vuelva  intentarlo")

            return HttpResponseRedirect("/solicitudes")
    else:
        data = {'title': 'Solicitudes de Estudiantes'}
        addUserData(request, data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='cerrar':
                solicitud = SolicitudSecretariaDocente.objects.get(pk=request.GET['id'])
                solicitud.fechacierre = datetime.now()
                solicitud.cerrada = True
                solicitud.save()
                solicitud.mail_subject_respuesta()
                return HttpResponseRedirect("/solicitudes")
            # elif action == 'actualizahora':
            #     c=0
            #     for s in SolicitudSecretariaDocente.objects.filter(cerrada=True).exclude(fechaasignacion=None).exclude(solicitudestudiante=None):
            #         try:
            #             log = LogEntry.objects.filter(object_id=s.id,change_message__icontains='Solicitud Alumno finalizado')[:1].get()
            #             s.hora=log.action_time.time()
            #             s.save()
            #             c=c+1
            #             print(s)
            #         except Exception as e:
            #             print(e)
            #             pass
            #     print(c)
            elif action=='verasistentes':
                data = {}
                data['asistentes'] = IncidenciaAsignada.objects.filter(solicitusecret__id=request.GET['idinfo'])
                return render(request ,"asuntoestudiantil/verasistentes.html" ,  data)

            elif action == 'vergestion':
                solicitud = SolicitudSecretariaDocente.objects.filter(pk=request.GET['ide'])[:1].get()
                seguimiento= IncidenciaAsignada.objects.filter(solicitusecret=solicitud).order_by('-fecha')

                data['solicitud']=solicitud
                data['seguimiento']=seguimiento
                return render(request ,"solicitudes/detalle_gestion.html" ,  data)

            elif action=='comentar':
                data['title'] = 'Comentar Solicitud a Secretaria Docente'
                solicitud = SolicitudSecretariaDocente.objects.get(pk=request.GET['id'])
                solicitud.save()
                data['form'] = SolicitudSecretariaDocenteForm(instance=solicitud)
                data['solicitud'] = solicitud
                return render(request ,"solicitudes/comentarbs.html" ,  data)

        else:
            # solicitudes=None
            tipoid = None
            todos = None
            for s in SolicitudSecretariaDocente.objects.filter(fecha__gte='2020-08-17',tipo__id=16,departamento=None).exclude(personaasignada=None):
                s.departamento_id=27
                s.save()
            if 'cerra' in request.GET:
                solicitudes = SolicitudSecretariaDocente.objects.filter(Q(cerrada=True)).exclude(solicitudestudiante=None).order_by('-fecha','-hora')
                data['cerrado'] = 'cerra'
            else:

                solicitudes = SolicitudSecretariaDocente.objects.filter(Q(cerrada=False)).exclude(solicitudestudiante=None).order_by('-fecha','-hora')

            if 't' in request.GET:
                tipoid = request.GET['t']

            if todos:
                if tipoid:
                    solicitudes =  SolicitudSecretariaDocente.objects.filter(tipo__in=tipoid).order_by('tipo__nombre','-fecha')[:100]
                else:
                    solicitudes =  SolicitudSecretariaDocente.objects.all().order_by('tipo__nombre','-fecha')[:100]

            if tipoid:
                data['tsolicitud'] = TipoSolicitudSecretariaDocente.objects.get(pk=tipoid)
                solicitudes =  SolicitudSecretariaDocente.objects.filter(tipo__id=tipoid).order_by('cerrada','-fecha','-hora')

            solicitudes = solicitudes.filter().order_by('-fecha','-hora')

            if AsistenteDepartamento.objects.filter(persona__usuario=request.user).exists() and not request.user.has_perm('sga.change_asistentedepartamento') :

                persona = Persona.objects.get(usuario=request.user)
                solicitudes = solicitudes.filter(personaasignada=persona).order_by('fecha')
            else:
                 if AsistenteDepartamento.objects.filter(persona__usuario=request.user,puedereasignar=True).exists():
                    dpto=AsistenteDepartamento.objects.filter(persona__usuario=request.user,puedereasignar=True).distinct('departamento').values('departamento')
                    usr2=AsistenteDepartamento.objects.filter(persona__usuario=request.user,puedereasignar=False).distinct('persona__usuario').values('persona__usuario')
                    usuario = AsistenteDepartamento.objects.filter(departamento__id__in=dpto).values('persona__usuario')
                    solicitudes = solicitudes.filter(Q(personaasignada__usuario__id__in=usuario)|Q(personaasignada__usuario__id__in=usr2)).order_by('cerrada','-fecha','-hora')
                # else:
                    data['asistentes'] = AsistenteDepartamento.objects.filter(departamento__id__in=dpto,activo=True).order_by('persona__apellido1','persona__apellido2','persona__nombres',)
                 else:
                        data['asistentes'] = AsistenteDepartamento.objects.filter(activo=True).order_by('persona__apellido1','persona__apellido2','persona__nombres',)

            if Persona.objects.filter(usuario=request.user, usuario__groups__id__in=[PROFESORES_GROUP_ID]).exists():
               solicitudes = solicitudes.filter(usuario=request.user).order_by('cerrada','-fecha','-hora')

            if 'op' in request.GET:
                if request.GET['op'] == 'buscar':
                    asistentefilter =AsistenteDepartamento.objects.get(pk=request.GET['asist'],activo=True)
                    data['asistentefilter'] = asistentefilter
                    data['asignados'] = asistentefilter.cantidad
                    data['cantsolicitud'] = asistentefilter.cantidadsol
                    data['gestionados'] = asistentefilter.gestionados()
                    data['solicitudgestionadas'] = asistentefilter.solicitudes_gestionados()
                    solicitudes = solicitudes.filter(personaasignada=asistentefilter.persona).order_by('fecha')

            if 's' in request.GET:
                search = request.GET['s']
                if len(search) >0:
                    ss = search.split(' ')
                    data['search']=search
                    solicitudes = SolicitudSecretariaDocente.objects.filter().exclude(solicitudestudiante=None).order_by('-fecha','-hora')
                    try:
                        if int(search):
                            numero = int(search)
                            solicitudes = solicitudes.filter(Q (id=numero)|Q (persona__cedula__icontains=ss[0])|Q (persona__pasaporte__icontains=ss[0])).order_by('cerrada','-fecha','-hora')
                    except Exception as e:
                        while '' in ss:
                            ss.remove('')
                        if len(ss)==1:
                            solicitudes = solicitudes.filter(Q (persona__apellido1__icontains=search)).order_by('cerrada','-fecha','-hora')
                        else:
                            solicitudes = solicitudes.filter(Q(persona__apellido1__icontains=ss[0]) & Q (persona__apellido2__icontains=ss[1])).order_by('cerrada','-fecha','-hora')
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
            # data['tiposolicitud'] = TipoSolicitudSecretariaDocente.objects.filter(activa=True)
            data['tiposolicitud'] = Departamento.objects.filter(controlespecies=True)
            gruposexcluidos = [PROFESORES_GROUP_ID,ALUMNOS_GROUP_ID]
            grupos = GrupoCorreo.objects.filter().values('grupos')
            data['grupos'] = Group.objects.filter(id__in=grupos).exclude(user=None).exclude(id__in=gruposexcluidos).order_by('name')
            personas=Persona.objects.filter(usuario__is_active=True,usuario__groups__id__in=request.user.groups.all()).exclude(usuario__groups__id__in=[PROFESORES_GROUP_ID,ALUMNOS_GROUP_ID]).exclude(usuario=None).exclude(usuario__groups__id__in=gruposexcluidos).values('id')
            form = PersonalSolicitudForm()
            form.personas_list(personas)
            data['personas']= Persona.objects.filter(usuario__is_active=True,usuario__groups__id__in=request.user.groups.all()).exclude(usuario__groups__id__in=[PROFESORES_GROUP_ID,ALUMNOS_GROUP_ID]).exclude(usuario=None).exclude(usuario__groups__id__in=gruposexcluidos)
            data['form']= form

            if 'error' in request.GET:
                data['error'] = request.GET['error']

            data['tipoid'] = int(tipoid) if tipoid else ""
            data['todos'] = todos if todos else ""
            data['tipo'] =  TipoSolicitudSecretariaDocente.objects.get(pk=request.GET['t']) if tipoid else ""
            data['tipos'] = TipoSolicitudSecretariaDocente.objects.all().order_by('nombre')
            data['usuario'] = request.user
            data['ID_TIPO_SOLICITUD']=ID_TIPO_SOLICITUD
            data['ID_PAGO_RUBROS']=TIPO_RUBRO_SOLICITUD
            data['segform'] = SeguimientoEspecieForm()
            data['formresol'] = AprobacionSolicitudForm()
            data['persona'] = Persona.objects.get(usuario=request.user)

            return render(request ,"solicitudes/solicitudesbs.html" ,  data)