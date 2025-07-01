import json
from itertools import chain
from datetime import datetime
import os
from django.contrib.auth.models import Group
from sga.tasks import send_html_mail
from settings import NIVELMALLA_INICIO_PRACTICA, HORAS_MAX_LABORA, TIPO_ESPECIEVALO_PRACPRE, ID_REPORTE_CARTA_COMPROM, ID_REPORTE_CARTA_ASIGNAC, MEDIA_ROOT, ID_SOLIC__ONLINE, TIPO_SOLIC__SECRET_PRACPRE, HORAS_MIN_PRACTICAS, PUNTAJE_APRUEBA_PRACTICA, ALUMNOS_GROUP_ID, SISTEMAS_GROUP_ID, ASIGNATURA_PRACTICAS_SM,PROFESORES_GROUP_ID
from sga.commonviews import addUserData, ip_client_address
from django.shortcuts import render
from django.template import RequestContext
from django.core.paginator import Paginator
from django.db.models.query_utils import Q
from sga.finanzas import generador_especies
from sga.models import Inscripcion, SolicitudPracticas, EmpresaSinConvenio, FichaReceptora, RubroEspecieValorada, EmpresaConvenio, SegmentoIndicadorEmp, PuntajeIndicador, IndicadorAcademico, EvaluacionAcademico, EscenarioPractica, SolicitudHorarioAsistente, TipoEspecieValorada, Rubro, SolicitudOnline, SolicitudEstudiante, Matricula, Grupo, Carrera, Nivel, TutorEntidadRecep, ProcesoSeleccion, ProcesoSelecDetalle, ReportePracticas, ReportePractSolicitud, HorarioAsistenteSolicitudes, AsistenteDepartamento, CoordinacionDepartamento, EspecieGrupo, EstadoEmpresa, SegmentoDetalle, EvaluacionSupervisorEmp, SolictudDetallFinal, SupervisorPracticas, SupervisionPracticasDet,SupervisionPracticas, ProfesorMateria,TipoSupervisionPracticas,Persona, CoordinadorPracticas
from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_str
from django.http import HttpResponse, HttpResponseRedirect
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

__author__ = 'jjurgiles'

def view(request):
    try:
        if request.method == 'POST':
            action = request.POST['action']
            if "buscarempresa" == action:
                result = {}
                try:
                    if EmpresaConvenio.objects.filter(ruc=request.POST['ruc']).exists() or 'idempcon' in request.POST:
                        if 'idempcon' in request.POST:
                            empresa =  EmpresaConvenio.objects.filter(id=request.POST['idempcon'])[:1].get()
                        else:
                            empresa =  EmpresaConvenio.objects.filter(ruc=request.POST['ruc'])[:1].get()
                        result['result'] ="ok"
                        result['mensaje'] = empresa.nombre
                        result['ruc'] = empresa.ruc
                        result['idempresacon'] = empresa.id
                        result['actividad'] = empresa.activideconomica
                        result['direccion'] = empresa.direccion
                        result['provincia'] = empresa.ciudad.provincia.nombre if empresa.ciudad else ''
                        result['idprov'] = empresa.ciudad.provincia.id if empresa.ciudad else 0
                        result['ciudad'] = empresa.ciudad.nombre if empresa.ciudad else ''
                        result['idciu'] = empresa.ciudad.id if empresa.ciudad else 0
                    else:
                        if EmpresaSinConvenio.objects.filter(ruc=request.POST['ruc']).exists():
                            result['result'] ="existe"
                            empresa =  EmpresaSinConvenio.objects.filter(ruc=request.POST['ruc'])[:1].get()
                            result['ruc'] = empresa.ruc
                            result['mensaje'] = empresa.nombre
                            result['idempresacon'] = empresa.id
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
                    print("error excep buscarempresa soliadm "+str(e))
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

            elif "buscartutempr" == action:
               try:
                   result = {}
                   if TutorEntidadRecep.objects.filter(correo=request.POST['emailtut'],sinconvenio=None).exclude(convenio=None).exists():
                       tutorentidadrecep = TutorEntidadRecep.objects.filter(correo=request.POST['emailtut'],sinconvenio=None).exclude(convenio=None)[:1].get()
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
            elif "guardarfichrecp" == action:
                result = {}
                try:
                    datos = json.loads(request.POST['datos'])
                    if int(datos['solicitudid']) > 0:
                        solicitudpractica = SolicitudPracticas.objects.get(id=datos['solicitudid'])
                    else:
                        inscripcion = Inscripcion.objects.get(id=datos['idinscripcion'])
                        escenariopractica = EscenarioPractica.objects.get(id=request.POST['idesc'])
                        matricula = inscripcion.matricula()
                        # if RubroEspecieValorada.objects.filter(id=escenariopractica.rubroespecievalorada.id,rubro__cancelado=True,aplicada=True).exists():
                        #     rubrespecie =  RubroEspecieValorada.objects.filter(id=escenariopractica.rubroespecievalorada.id,rubro__cancelado=True,aplicada=True)[:1].get()
                        if SolicitudPracticas.objects.filter(matricula = matricula,aprobada=False,fecaprobada=None).exists():
                            solicitudpractica = SolicitudPracticas.objects.filter(matricula = matricula,aprobada=False,fecaprobada=None)[:1].get()
                        else:
                            solicitudpractica = SolicitudPracticas(matricula = matricula,
                                                        escenariopractica = escenariopractica,
                                                        fecha = datetime.now(),
                                                        promedionota = inscripcion.calculopromedio())
                            solicitudpractica.save()

                        solicitudpractica.escenariopractica.fechafinaliza = datetime.now()
                        solicitudpractica.escenariopractica.save()
                        solicitudpractica.fecaprobada = datetime.now()
                        solicitudpractica.aprobada = True
                        solicitudpractica.save()
                        # else:
                        #     result['result'] ="bad"
                        #     result['mensaje'] ="No hay especie registrada para la solicitud de practias"
                        #     return HttpResponse(json.dumps(result),content_type="application/json")
                    empresa = None
                    if int(datos['idempresa']) > 0:
                        empresa = EmpresaConvenio.objects.get(id=datos['idempresa'])
                    else:
                        for em in datos['empresa']:
                            if EmpresaConvenio.objects.filter(ruc = em['ruc']).exists():
                                empresa = EmpresaConvenio.objects.filter(ruc = em['ruc'])[:1].get()
                            else:
                                empresa =  EmpresaConvenio(ruc = em['ruc'])
                            empresa.nombre = em['entidadrec']
                            empresa.ruc = em['ruc']
                            empresa.activideconomica = em['actividaent']
                            empresa.direccion = em['direccionent']
                            empresa.ciudad_id = em['ciudadrec']
                            empresa.save()
                    mensaje = ''
                    for info in datos['informacion']:
                        if int(datos['fichrecepid']) == 0:
                            fichareceptora = FichaReceptora(convenio = empresa,
                                                            inicio = info['feinicio'],
                                                            fin = info['fefin'],
                                                            horaspracticas = info['horas'],
                                                            horainicio = info['hini'],
                                                            horafin = info['hfin'],
                                                            supervisor = info['nomtutot'],
                                                            correo = info['emailtut'],
                                                            cargo = info['cargotut'],
                                                            cantidad = info['numprac'])
                            fichareceptora.save()
                            mensaje = 'Ingreso de Ficha de Entidad Receptora'
                        else:
                            fichareceptora = FichaReceptora.objects.get(id=datos['fichrecepid'])
                            fichareceptora.convenio = empresa
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
                        if not TutorEntidadRecep.objects.filter(correo=info['emailtut'],convenio=empresa).exists():
                            tutorentidadrecep = TutorEntidadRecep(convenio = empresa,
                                                                  correo = info['emailtut'])
                        else:
                            tutorentidadrecep = TutorEntidadRecep.objects.filter(correo=info['emailtut'],convenio=empresa)[:1].get()
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
                        if not solicitudpractica.id:
                            print('AQUI')
                            result['result'] ="bad"
                            result['mensaje'] ="no se guarda solicitud pracita"
                            return HttpResponse(json.dumps(result),content_type="application/json")
                        fichareceptora.solicitudpracticas_id = solicitudpractica.id
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

            elif "enviarsolicict" == action:
                result = {}
                try:
                    solicitudpractica = SolicitudPracticas.objects.get(id=request.POST['idsoli'])
                    solicitudpractica.mail_enviosolpract(request.user)
                    solicitudpractica.fechaenvio = datetime.now()
                    solicitudpractica.enviada = True
                    solicitudpractica.save()
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
                    return HttpResponse(json.dumps(result),content_type="application/json")
                except Exception as e:
                    print("error excep enviarsolicict soli "+str(e))
                    result['result'] ="bad"
                    result['mensaje'] ="error al guardar la informacion"
                    return HttpResponse(json.dumps(result),content_type="application/json")

            elif "aprobarsolici" == action:
                result = {}
                try:
                    solicitudpractica = SolicitudPracticas.objects.get(id=request.POST['idsoli'])
                    if not solicitudpractica.escenariopractica.convenio:
                        solicitudpractica.aprobada = json.loads(request.POST['aprobado'])
                        solicitudpractica.observacion = request.POST['observacion']
                        solicitudpractica.fecaprobada = datetime.now()
                        solicitudpractica.save()
                        solicitudpractica.mail_aprobsolpract(request.user,1)
                        if solicitudpractica.aprobada:
                            # ////////////////////////////////////////////////////////////////////
                            # ////////////////////////////////////////////////////////////////////
                            # tipoEspecie = TipoEspecieValorada.objects.get(pk=TIPO_ESPECIEVALO_PRACPRE)
                            # inscripcion = solicitudpractica.escenariopractica.matricula.inscripcion
                            #
                            #
                            # rubro = Rubro(fecha=datetime.now(),
                            #             valor=tipoEspecie.precio,
                            #             inscripcion = inscripcion,
                            #             cancelado=tipoEspecie.precio==0,
                            #             fechavence=datetime.now())
                            # rubro.save()
                            # solicitud = SolicitudOnline.objects.filter(pk=ID_SOLIC__ONLINE)[:1].get()
                            # solicitudest = SolicitudEstudiante(solicitud=solicitud,
                            #                                    inscripcion=inscripcion,
                            #                                    observacion=str('SOLICITUD GENERADA DE PRACTICAS PRE-PROFESIONALES'),
                            #                                    tipoe_id=tipoEspecie.id,
                            #                                    correo=inscripcion.persona.emailinst,
                            #                                    celular=inscripcion.persona.telefono,
                            #                                    fecha=datetime.now())
                            # solicitudest.save()
                            # solicitudest.rubro = rubro
                            # solicitudest.solicitado=True
                            #
                            # solicitudest.save()
                            #
                            # # Rubro especie valorada
                            # rubroenot = generador_especies.generar_especie(rubro=rubro, tipo=tipoEspecie)
                            # rubroenot.autorizado=False
                            # rubroenot.save()
                            # # ///////////////////////////////////////////////////////////////
                            # # ///////////////////////////////////////////////////////////////
                            # iddepartamentoesp = EspecieGrupo.objects.filter(tipoe__id=TIPO_SOLIC__SECRET_PRACPRE).values('departamento').distinct('departamento')
                            # iddepartamento =  CoordinacionDepartamento.objects.filter(departamento__id__in = iddepartamentoesp,coordinacion__carrera=solicitudpractica.matricula.inscripcion.carrera).values('departamento').distinct('departamento')
                            # idusuario = AsistenteDepartamento.objects.filter(departamento__id__in=iddepartamento).values('persona__usuario').distinct('persona__usuario')
                            # if HorarioAsistenteSolicitudes.objects.filter(fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time(),usuario__id__in=idusuario).exists():
                            #     horarioasis = HorarioAsistenteSolicitudes.objects.filter(fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time(),usuario__id__in=idusuario).exclude(nolabora=True).order_by('sinatender')[:1].get()
                            #     asistentes = AsistenteDepartamento.objects.filter(persona__usuario=horarioasis.usuario).exclude(puedereasignar=True).order_by('cantidadsol')[:1].get()
                            #     if asistentes:
                            #         rubroenot.usrasig = asistentes.persona.usuario
                            #         rubroenot.departamento = asistentes.departamento
                            #         asistentes.cantidad =asistentes.cantidad +1
                            #         rubroenot.fechaasigna = datetime.now()
                            #         rubroenot.save()
                            #         asistentes.save()
                            #         lista = str(asistentes.persona.email)
                            #         hoy = datetime.now().today()
                            #         contenido = "  Tramites Asignados"
                            #         descripcion = "Ud. tiene tramites por atender"
                            #         send_html_mail(contenido,
                            #             "emails/notificacion_tramites_adm.html", {'fecha': hoy,'contenido': contenido,'descripcion':descripcion,'opcion':'1'},lista.split(','))
                            # # ///////////////////////////////////////////////////////////////
                            # # ///////////////////////////////////////////////////////////////
                            #
                            # solicitudpractica.rubroespecie = rubroenot
                            # solicitudpractica.solicitudestudiante = solicitudest
                            solicitudpractica.escenariopractica.fechafinaliza = datetime.now()
                            solicitudpractica.escenariopractica.aprobado = True
                            solicitudpractica.escenariopractica.fechaacepta = datetime.now()
                            solicitudpractica.escenariopractica.save()
                            solicitudpractica.save()
                            result['mens'] ="Aprobada"
                        else:
                            result['mens'] ="No aprobada"
                    else:
                        if not ProcesoSeleccion.objects.filter(id=request.POST['idproceselec'],activo = True).exists():
                            result['result'] ="bad"
                            result['mensaje'] ="Proceso de seleccion no esta activo"
                            return HttpResponse(json.dumps(result),content_type="application/json")
                        proceso = ProcesoSeleccion.objects.get(id=request.POST['idproceselec'],activo = True)
                        fichaentidadrecep = solicitudpractica.fichaentidadrec()
                        procesodetalle = ProcesoSelecDetalle(procesoseleccion=proceso,
                                                            fichareceptora=fichaentidadrecep)
                        procesodetalle.save()
                        solicitudpractica.escenariopractica.fechafinaliza = datetime.now()
                        solicitudpractica.escenariopractica.save()
                        solicitudpractica.fecaprobada = datetime.now()
                        solicitudpractica.fechaenvio = datetime.now()
                        solicitudpractica.enviada = True
                        solicitudpractica.save()
                        solicitudpractica.mail_aprobsolpract(request.user,2)
                        result['mens'] ="Enviada"
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(solicitudpractica).pk,
                        object_id       = solicitudpractica.id,
                        object_repr     = force_str(solicitudpractica),
                        action_flag     = ADDITION,
                        change_message  = 'Solicitud '+str(result['mens'])+' (' + client_address + ')' )

                    result['result'] ="ok"

                    result['idsol'] =solicitudpractica.id
                    return HttpResponse(json.dumps(result),content_type="application/json")
                except Exception as e:
                    print("error excep guardarempresa soli "+str(e))
                    result['result'] ="bad"
                    result['mensaje'] ="error al guardar la informacion"
                    return HttpResponse(json.dumps(result),content_type="application/json")

            elif "enviarcorreo" == action:
                result = {}
                try:
                    solicitudpractica = SolicitudPracticas.objects.get(id=request.POST['idsoli'])
                    solicitudpractica.mail_correosolpract(request.user,request.POST['contenidocorr'])
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
                    return HttpResponse(json.dumps(result),content_type="application/json")
                except Exception as e:
                    print("error excep guardarempresa soli "+str(e))
                    result['result'] ="bad"
                    result['mensaje'] ="error al guardar la informacion"
                    return HttpResponse(json.dumps(result),content_type="application/json")
            elif "guardarevalinst" == action:
                result = {}
                try:
                    solicitudpractica = SolicitudPracticas.objects.get(id=request.POST['idsoli'])
                    datos = json.loads(request.POST['datos'])
                    for indi in datos['indicadores']:
                        evaluacionacademico = EvaluacionAcademico(solicitudpracticas = solicitudpractica,
                                                                indicadoracademico_id = indi['idindic'],
                                                                cumple = indi['cumple'])
                        evaluacionacademico.save()
                    solicitudpractica.supervisado = datos['supervisado']
                    solicitudpractica.observacionevalaca = datos['observacion']
                    solicitudpractica.fechasupervis = datetime.now()
                    solicitudpractica.save()
                    solicitudpractica.mail_evaluainstrealizada(request.user)
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(solicitudpractica).pk,
                        object_id       = solicitudpractica.id,
                        object_repr     = force_str(solicitudpractica),
                        action_flag     = ADDITION,
                        change_message  = 'Evalaucion de la institucion Enviada (' + client_address + ')' )

                    result['result'] ="ok"
                    result['idsol'] =solicitudpractica.id
                    return HttpResponse(json.dumps(result),content_type="application/json")
                except Exception as e:
                    print("error excep guardarevalinst "+str(e))
                    result['result'] ="bad"
                    result['mensaje'] ="error al guardar la informacion"
                    return HttpResponse(json.dumps(result),content_type="application/json")


            elif "aceptarescena" == action:
                result = {}
                try:
                    escenariopracticahorario = SolicitudHorarioAsistente.objects.get(id=request.POST['ideschor'])
                    escenariopractica = escenariopracticahorario.escenario
                    if json.loads(request.POST['aprobado']):
                        # ////////////////////////////////////////////////////////////////////
                        # ////////////////////////////////////////////////////////////////////
                        tipoEspecie = TipoEspecieValorada.objects.get(pk=TIPO_ESPECIEVALO_PRACPRE)
                        inscripcion = escenariopractica.matricula.inscripcion


                        rubro = Rubro(fecha=datetime.now(),
                                    valor=tipoEspecie.precio,
                                    inscripcion = inscripcion,
                                    cancelado=tipoEspecie.precio==0,
                                    fechavence=datetime.now())
                        rubro.save()
                        solicitud = SolicitudOnline.objects.filter(pk=3)[:1].get()
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
                        rubroenot = generador_especies.generar_especie(rubro=rubro, tipo=tipoEspecie)
                        rubroenot.autorizado=False
                        rubroenot.save()
                        # ///////////////////////////////////////////////////////////////
                        # ///////////////////////////////////////////////////////////////

                        escenariopracticahorario.finaliza = json.loads(request.POST['aprobado'])
                        escenariopractica.aprobado = json.loads(request.POST['aprobado'])
                        escenariopractica.rubroespecievalorada = rubroenot
                        escenariopractica.solicitudestudiante = solicitudest
                        escenariopractica.fechafinaliza = datetime.now()
                    else:
                        escenariopracticahorario.finaliza = json.loads(request.POST['finalizado'])
                        if json.loads(request.POST['finalizado']):
                            escenariopractica.aprobado = json.loads(request.POST['aprobado'])
                            escenariopractica.fechafinaliza = datetime.now()
                    escenariopractica.save()
                    escenariopracticahorario.obshorario = request.POST['observacion']
                    escenariopracticahorario.fechahorar = datetime.now()
                    escenariopracticahorario.aprobado = json.loads(request.POST['aprobado'])
                    escenariopracticahorario.save()
                    escenariopractica.mail_correosolpract(request.user,request.POST['observacion'])
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(escenariopractica).pk,
                        object_id       = escenariopractica.id,
                        object_repr     = force_str(escenariopractica),
                        action_flag     = ADDITION,
                        change_message  = 'Escenario Aprobado (' + client_address + ')' )

                    result['result'] ="ok"
                    result['idsol'] =escenariopractica.id
                    return HttpResponse(json.dumps(result),content_type="application/json")
                except Exception as e:
                    print("error excep aceptarescena soliadm "+str(e))
                    result['result'] ="bad"
                    result['mensaje'] ="Error al guardar la informacion"
                    return HttpResponse(json.dumps(result),content_type="application/json")

            elif action == 'guardaresce':
                try:
                    escenariopractica = EscenarioPractica.objects.get(id=request.POST['idesc'])
                    escenariopractica.convenio = json.loads(request.POST['escenario'])
                    escenariopractica.fecha = datetime.now()
                    mensaje = 'Editando desde asistente'

                    escenariopractica.save()

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

            elif action == 'busquenivel':
                try:
                    result = {'result':'ok'}
                    idniveles = Matricula.objects.filter(nivel__cerrado=False,nivel__nivelmalla__orden__gte=NIVELMALLA_INICIO_PRACTICA).values('nivel').distinct('nivel')
                    niveles = Nivel.objects.filter(cerrado=False,id__in=idniveles,carrera__id=request.POST['idcarrfich'])
                    datos =  [{"id": str(n.id),"descripcion":str(elimina_tildes(n.nivelmalla )+' - '+ elimina_tildes(n.paralelo) +' - ' + elimina_tildes(n.carrera))  } for n in niveles]
                    result['datos'] =  datos
                    return HttpResponse(json.dumps(result),content_type="application/json")
                except Exception as e:
                    print("error excep escenariopractica busquenivel "+str(e))
                    result = {}
                    result['result'] ="bad"
                    result['mensaje'] ="error al guardar"
                    return HttpResponse(json.dumps(result),content_type="application/json")

            elif action == 'busqueescenario':
                try:
                    result = {'result':'ok'}
                    filtro = ''
                    solicitudpractica = SolicitudPracticas.objects.get(id=request.POST['idsoli'])
                    if int(request.POST['idcarrfich'])  > 0:
                        filtro = 'matricula__inscripcion__carrera__id='+request.POST['idcarrfich']
                    if int(request.POST['idnivelfich'])  > 0:
                        if filtro:
                            filtro = filtro+',matricula__nivel__id='+request.POST['idnivelfich']
                        else:
                            filtro = 'matricula__nivel__id='+request.POST['idnivelfich']
                    # if json.loads(request.POST['convenio']):
                    #     if filtro:
                    #         filtro = filtro+',convenio=True'
                    #     else:
                    #         filtro = 'convenio=True'

                    if filtro:
                        filtro = filtro +',convenio=True,fechafinaliza=None'
                        escenariopractica = eval('EscenarioPractica.objects.filter(%s)'%(filtro))
                        escenariopractica = escenariopractica.filter().exclude(id=solicitudpractica.escenariopractica.id).order_by('fecha','matricula__inscripcion__persona__apellido1')
                    else:
                        escenariopractica = EscenarioPractica.objects.filter(convenio=True,fechafinaliza=None).exclude(id=solicitudpractica.escenariopractica.id).order_by('fecha','matricula__inscripcion__persona__apellido1')
                    datos = []
                    for e in escenariopractica:
                        if not e.exis_solipracticas():
                            datos.append({"idesc": str(e.id),"nombre":str(elimina_tildes(e.matricula.inscripcion.persona.nombre_completo())),'fecha':str(e.fecha)})
                    result['datos'] =  datos
                    return HttpResponse(json.dumps(result),content_type="application/json")
                except Exception as e:
                    print("error excep solicitudpract busqueescenario "+str(e))
                    result = {}
                    result['result'] ="bad"
                    result['mensaje'] ="error al busqueescenario"
                    return HttpResponse(json.dumps(result),content_type="application/json")

            elif action == 'guardarprocselec':
                try:
                    result = {}
                    fichareceptora = FichaReceptora.objects.get(id=request.POST['idficharecep'])
                    if ProcesoSeleccion.objects.filter(empresa = fichareceptora.convenio,activo=True):
                        proceso = ProcesoSeleccion.objects.filter(empresa = fichareceptora.convenio,activo=True)[:1].get()
                        if int(request.POST['idcant']) <= ProcesoSelecDetalle.objects.filter(procesoseleccion=proceso).count():
                            result['result'] ="bad"
                            result['mensaje'] ="La cantidad del los estudiantes del proceso de seleccion, no debe ser menor a los aceptado"
                            return HttpResponse(json.dumps(result),content_type="application/json")
                        mensaje = 'Se modifico'
                    else:
                        proceso = ProcesoSeleccion(empresa = fichareceptora.convenio,
                                                   fecha=datetime.now(),
                                                    activo = True)
                        mensaje = 'Se creo'

                    proceso.cantidad = request.POST['idcant']
                    proceso.save()
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(proceso).pk,
                    object_id       = proceso.id,
                    object_repr     = force_str(proceso),
                    action_flag     = ADDITION,
                    change_message  = mensaje+' proceso de seleccion (' + client_address + ')' )
                    result['result'] ="ok"
                    return HttpResponse(json.dumps(result),content_type="application/json")
                except Exception as e:
                    print("error excep solicitudpract guardarprocselec "+str(e))
                    result = {}
                    result['result'] ="bad"
                    result['mensaje'] ="error al busqueescenario"
                    return HttpResponse(json.dumps(result),content_type="application/json")

            elif action == 'copiarficharecept':
                try:
                    result = {'result':'ok'}
                    datos = json.loads(request.POST['datos'])
                    fichareceptora = FichaReceptora.objects.get(id=datos['fichrecepid'])
                    html = ""
                    idesce = datos['idescen']
                    for i in idesce:
                        escenariopractica = EscenarioPractica.objects.get(id=i['idesc'])
                        if not SolicitudPracticas.objects.filter(escenariopractica=escenariopractica).exists() and escenariopractica.convenio:
                            matricula = escenariopractica.matricula
                            if 'idproceselec' in datos:
                                proceso = ProcesoSeleccion.objects.get(id=datos['idproceselec'],activo=True)
                            else:
                                if ProcesoSeleccion.objects.filter(empresa=fichareceptora.convenio,activo=True).exists():
                                    proceso = ProcesoSeleccion.objects.filter(empresa=fichareceptora.convenio,activo=True)[:1].get()
                                else:
                                    proceso = ProcesoSeleccion(empresa = fichareceptora.convenio,
                                                                fecha=datetime.now(),
                                                                activo=True)
                            proceso.cantidad = datos['cantprocesficha']
                            proceso.save()
                            if proceso.cantidad <= ProcesoSelecDetalle.objects.filter(procesoseleccion=proceso,acepto=True).count():
                                html = html + '<tr><td>'+str(elimina_tildes(escenariopractica.matricula.inscripcion.persona.nombre_completo())) + ' no se creo, la cantidad del proceso de seleccion es menor a la cantidad de alumnos que aceptaron la solicitud practica.<td/><tr/>'
                            else:
                                solicitudpractica = SolicitudPracticas(matricula = matricula,
                                                            escenariopractica = escenariopractica,
                                                            fecha = datetime.now(),
                                                            promedionota = escenariopractica.matricula.inscripcion.calculopromedio())
                                solicitudpractica.save()

                                fichareceptoracop = FichaReceptora(solicitudpracticas = solicitudpractica,
                                                        convenio = fichareceptora.convenio,
                                                        inicio = fichareceptora.inicio,
                                                        fin = fichareceptora.fin,
                                                        horainicio = fichareceptora.horainicio,
                                                        horafin = fichareceptora.horafin,
                                                        horaspracticas = fichareceptora.horaspracticas,
                                                        supervisor = fichareceptora.supervisor,
                                                        correo = fichareceptora.correo,
                                                        cargo = fichareceptora.cargo,
                                                        cantidad = fichareceptora.cantidad)
                                if fichareceptora.celular:
                                    fichareceptoracop.celular = fichareceptora.celular
                                if fichareceptora.telefono:
                                    fichareceptoracop.telefono = fichareceptora.telefono
                                if fichareceptora.extension:
                                    fichareceptoracop.extension = fichareceptora.extension
                                fichareceptoracop.lunes = fichareceptora.lunes
                                fichareceptoracop.martes = fichareceptora.martes
                                fichareceptoracop.miercoles = fichareceptora.miercoles
                                fichareceptoracop.jueves = fichareceptora.jueves
                                fichareceptoracop.viernes = fichareceptora.viernes
                                fichareceptoracop.sabado = fichareceptora.sabado
                                fichareceptoracop.domingo = fichareceptora.domingo
                                fichareceptoracop.save()
                                if datos['opcionenvio'] == 'enviar':
                                    procesodetalle = ProcesoSelecDetalle(procesoseleccion = proceso,
                                                                        fichareceptora = fichareceptoracop)
                                    procesodetalle.save()
                                    solicitudpractica.escenariopractica.fechafinaliza = datetime.now()
                                    solicitudpractica.escenariopractica.save()
                                    solicitudpractica.fecaprobada = datetime.now()
                                    solicitudpractica.aprobada = True
                                    solicitudpractica.fechaenvio = datetime.now()
                                    solicitudpractica.enviada = True
                                    solicitudpractica.save()
                                    solicitudpractica.mail_aprobsolpract(request.user,2)

                                client_address = ip_client_address(request)
                                LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(solicitudpractica).pk,
                                object_id       = solicitudpractica.id,
                                object_repr     = force_str(solicitudpractica),
                                action_flag     = ADDITION,
                                change_message  = 'Ficha receptora copiada (' + client_address + ')' )
                                html = html + '<tr><td>Se creo Ficha Receptora para '+ str(elimina_tildes(escenariopractica.matricula.inscripcion.persona.nombre_completo())) + ' <a target="_blank" href="/solicitud_practicasadm?action=solicitud&ides='+str(escenariopractica.id)+'&fire=1&idsol='+str(solicitudpractica.id)+'"> Ir a Ficha </a><td/><tr/>'
                        else:
                            if not escenariopractica.convenio:
                                html = html + '<tr><td>El escenerario de '+ str(elimina_tildes(escenariopractica.matricula.inscripcion.persona.nombre_completo())) + ' no es de convenio<td/><tr/>'
                            else:
                                html = html + '<tr><td>'+str(elimina_tildes(escenariopractica.matricula.inscripcion.persona.nombre_completo())) + ' ya tiene una solicitud.<td/><tr/>'
                    result['html'] = html
                    return HttpResponse(json.dumps(result),content_type="application/json")
                except Exception as e:
                    print("error excep escenariopractica busqueescenario "+str(e))
                    result = {}
                    result['result'] ="bad"
                    result['mensaje'] ="error al copiarficharecept"
                    return HttpResponse(json.dumps(result),content_type="application/json")
            elif action == 'checkrevisado':
                try:
                    result = {}
                    reportsolic = ReportePractSolicitud.objects.get(id=request.POST['reptsolid'])
                    reportsolic.fecharev = datetime.now()
                    reportsolic.revisado = True
                    reportsolic.save()
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(reportsolic).pk,
                    object_id       = reportsolic.id,
                    object_repr     = force_str(reportsolic),
                    action_flag     = ADDITION,
                    change_message  = 'Reporte Solicitud Revisado (' + client_address + ')' )
                    result['result'] = 'ok'
                    return HttpResponse(json.dumps(result),content_type="application/json")
                except Exception as e:
                    print("error excep escenariopractica busqueescenario "+str(e))
                    result = {}
                    result['result'] ="bad"
                    result['mensaje'] ="error al copiarficharecept"
                    return HttpResponse(json.dumps(result),content_type="application/json")


            elif "guardarreport" == action:
                result = {}
                try:

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


            elif "finalizpract" == action:
                result = {}
                try:
                    solicitudpractica = SolicitudPracticas.objects.get(id=request.POST['idsolic'])
                    solicitudpractica.finalizada = True
                    solicitudpractica.rechazado = json.loads(request.POST['rechazado'])
                    solicitudpractica.observrechazado = request.POST['observ']
                    solicitudpractica.fecfinaliza = datetime.now()
                    if not  solicitudpractica.rechazado:
                        for d in json.loads(request.POST['datos']):
                            solicdetfinal = SolictudDetallFinal(solicitud = solicitudpractica ,
                                                            practica = d['pract'],
                                                            horas = d['horas'],
                                                            fecha = datetime.now() )
                            solicdetfinal.save()
                    solicitudpractica.save()
                    solicitudpractica.mail_finalizapract(request.user,6)
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(solicitudpractica).pk,
                        object_id       = solicitudpractica.id,
                        object_repr     = force_str(solicitudpractica),
                        action_flag     = ADDITION,
                        change_message  = 'Practica finalizada (' + client_address + ')' )
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as e:
                    print("error excep guardarreport solic "+str(e))
                    result['result'] ="bad"
                    result['mensaje'] ="error al guardar la informacion"
                    return HttpResponse(json.dumps(result),content_type="application/json")

            elif action == 'guardar_supervisiondocente':
                try:
                    print(request.POST['datos'])
                    result = {}
                    solicitudpractica = SolicitudPracticas.objects.get(id=request.POST['idsoli'])
                    datos = json.loads(request.POST['datos'])
                    supervisor = SupervisorPracticas.objects.get(pk=request.POST['supervisor'])
                    tipo_supervision = TipoSupervisionPracticas.objects.get(pk=request.POST['tipo_supervision'])
                    num_supervision=0
                    if SupervisionPracticas.objects.filter(supervisor=supervisor).exists():
                        num_supervisiones_actual = SupervisionPracticas.objects.filter(supervisor=supervisor).order_by('-numsupervision')[:1].get()
                        num_supervision = num_supervisiones_actual.numsupervision

                    if request.POST['editar']=='1':
                        print('editar')
                        if SupervisionPracticas.objects.filter(pk=request.POST['idsupervision']).exists():
                            supervision = SupervisionPracticas.objects.get(pk=request.POST['idsupervision'])
                            supervision.ejecucion = request.POST['ejecucion']
                            supervision.observaciones=request.POST['observaciones']
                            supervision.tipo=tipo_supervision
                            supervision.save()
                            if IndicadorAcademico.objects.filter(estado=True).exists():
                                for i in datos['indicadores']:
                                    if SupervisionPracticasDet.objects.filter(supervision=supervision,indicadoracademico__id=i['idindic']).exists():
                                        supervisiondet = SupervisionPracticasDet.objects.get(supervision=supervision,indicadoracademico__id=i['idindic'])
                                        supervisiondet.cumple = i['cumple']
                                        supervisiondet.save()
                    else:
                        supervision = SupervisionPracticas(supervisor=supervisor,
                                                           numsupervision=num_supervision+1,
                                                           ejecucion=request.POST['ejecucion'],
                                                           observaciones=request.POST['observaciones'],
                                                           tipo=tipo_supervision)
                        supervision.save()
                        if IndicadorAcademico.objects.filter(estado=True).exists():
                            for i in datos['indicadores']:
                                supervisiondet = SupervisionPracticasDet(supervision=supervision,
                                                                         indicadoracademico_id=i['idindic'],
                                                                         cumple=i['cumple'])
                                supervisiondet.save()


                    # solicitudpractica.supervisado = datos['supervisado']
                    # solicitudpractica.observacionevalaca = datos['observacion']
                    # solicitudpractica.fechasupervis = datetime.now()
                    # solicitudpractica.save()
                    # solicitudpractica.mail_evaluainstrealizada(request.user)
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(solicitudpractica).pk,
                        object_id       = solicitudpractica.id,
                        object_repr     = force_str(solicitudpractica),
                        action_flag     = ADDITION,
                        change_message  = 'Evalaucion de la institucion Enviada (' + client_address + ')' )

                    result['result'] ="ok"
                    result['idsol'] =solicitudpractica.id
                    return HttpResponse(json.dumps(result),content_type="application/json")
                except Exception as e:
                    print(e)
                    result['result'] ="bad"
                    result['mensaje'] ="error al guardar la informacion"
                    return HttpResponse(json.dumps(result),content_type="application/json")

            elif action == 'add_coordinadorpracticas':
                try:
                    result = {}
                    print(request.POST)
                    solicitud = SolicitudPracticas.objects.get(pk=request.POST['solicitud'])
                    persona = Persona.objects.get(pk=request.POST['persona'])
                    if CoordinadorPracticas.objects.filter(coordinador=persona, solicitudpracticas=solicitud, activo=True).exists():
                        coordinador = CoordinadorPracticas.objects.filter(coordinador=persona, solicitudpracticas=solicitud, activo=True)[:1].get()
                    else:
                        coordinador = CoordinadorPracticas(coordinador=persona,
                                                           solicitudpracticas=solicitud,
                                                           activo=True)
                        coordinador.save()
                        for c in CoordinadorPracticas.objects.filter(solicitudpracticas=solicitud, activo=True).exclude(pk=coordinador.id):
                            c.activo=False
                            c.save()
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as e:
                    print(e)
                    result['result'] ="bad"
                    result['mensaje'] ="error al guardar la informacion"
                    return HttpResponse(json.dumps(result),content_type="application/json")

        else:
            data = {"title":"Solicitud Practicas"}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']
                if action == 'solicitud':
                    solicitudpractica = ''
                    if 'reac' in request.GET:
                        data['reac'] = True
                    if 'fire' in request.GET:
                        data['fire'] = True
                    if 'eval' in request.GET:
                        data['eval'] = True
                    if 'archpra' in request.GET:
                        data['archpra'] = True
                    if 'idsol' in request.GET:
                        solicitudpractica = SolicitudPracticas.objects.get(id=request.GET['idsol'])
                        data['solicitudpractica'] = solicitudpractica
                        if solicitudpractica.evalsuperinstit():
                            data['exiteevalacadem'] = True
                            indicadoracademico = IndicadorAcademico.objects.filter(id__in=solicitudpractica.evalsuperinstit().values('indicadoracademico'))
                        else:
                            indicadoracademico = IndicadorAcademico.objects.filter(estado=True)
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
                    else:
                        indicadoracademico = IndicadorAcademico.objects.filter(estado=True)
                        data['segmentoindicadoremp'] = SegmentoIndicadorEmp.objects.filter(estado=True)
                        data['puntajeindicador'] = PuntajeIndicador.objects.filter(estado=True).order_by('-puntos')
                    escenariopractica = EscenarioPractica.objects.get(id=request.GET['ides'])
                    data['escenariopractica'] = escenariopractica
                    data['fechahoy'] = datetime.now()
                    data['inscripcion'] = escenariopractica.matricula.inscripcion

                    data['indicadoracademico'] = indicadoracademico
                    data['HORAS_MAX_LABORA'] = HORAS_MAX_LABORA
                    idcarreras = Matricula.objects.filter(nivel__cerrado=False,nivel__nivelmalla__orden__gte=NIVELMALLA_INICIO_PRACTICA).values('inscripcion__carrera').distinct('inscripcion__carrera')
                    idgrupos = Matricula.objects.filter(nivel__cerrado=False,nivel__nivelmalla__orden__gte=NIVELMALLA_INICIO_PRACTICA).values('nivel__grupo').distinct('nivel__grupo')
                    idniveles = Matricula.objects.filter(nivel__cerrado=False,nivel__nivelmalla__orden__gte=NIVELMALLA_INICIO_PRACTICA).values('nivel').distinct('nivel')
                    data['carreras'] = Carrera.objects.filter(carrera=True,id__in=idcarreras)
                    data['grupos'] = Grupo.objects.filter(cerrado=False,id__in=idgrupos,carrera__carrera=True).order_by('nombre')
                    data['niveles'] = Nivel.objects.filter(cerrado=False,id__in=idniveles,carrera__carrera=True)

                    data['estadoempresa'] = EstadoEmpresa.objects.filter(estado=True).order_by('descripcion')
                    if ReportePracticas.objects.filter(carrera=escenariopractica.matricula.inscripcion.carrera,nivel=escenariopractica.matricula.nivel.nivelmalla).exists():
                        if solicitudpractica:
                            if ReportePractSolicitud.objects.filter(reportepractica__nombre__id=ID_REPORTE_CARTA_COMPROM,solicitudpractica=solicitudpractica,revisado=True).exists():
                                data['reportcartcompro'] = ReportePractSolicitud.objects.filter(reportepractica__nombre__id=ID_REPORTE_CARTA_COMPROM,solicitudpractica=solicitudpractica,revisado=True)[:1].get()
                            if ReportePractSolicitud.objects.filter(reportepractica__nombre__id=ID_REPORTE_CARTA_ASIGNAC,solicitudpractica=solicitudpractica,revisado=True).exists():
                                data['reportcartasigna'] = ReportePractSolicitud.objects.filter(reportepractica__nombre__id=ID_REPORTE_CARTA_ASIGNAC,solicitudpractica=solicitudpractica,revisado=True)[:1].get()
                            if not solicitudpractica.fecaprobada or solicitudpractica.aprobada:
                                numrep = ReportePractSolicitud.objects.filter(solicitudpractica=solicitudpractica).count() + 1
                                if solicitudpractica.escenariopractica.convenio:
                                    if numrep <= 1:
                                        reportepracticas = ReportePracticas.objects.filter(Q(carrera=escenariopractica.matricula.inscripcion.carrera,nivel=escenariopractica.matricula.nivel.nivelmalla,convenio=True,estudiante=False) | Q(convenio=True,estudiante=False,carrera=None) | Q(general=True,estudiante=False)).order_by('orden')[:numrep]
                                    else:
                                        reportepracticas = ReportePracticas.objects.filter(Q(carrera=escenariopractica.matricula.inscripcion.carrera,nivel=escenariopractica.matricula.nivel.nivelmalla,convenio=True)| Q(convenio=True,carrera=None) | Q(general=True)).order_by('orden')[:numrep]
                                else:
                                    reportepracticas = ReportePracticas.objects.filter(Q(carrera=escenariopractica.matricula.inscripcion.carrera,nivel=escenariopractica.matricula.nivel.nivelmalla,sinconvenio=True) | Q(sinconvenio=True,carrera=None) | Q(general=True)).order_by('orden')[:numrep]
                            else:
                                idreport = ReportePractSolicitud.objects.filter(solicitudpractica=solicitudpractica).values('reportepractica')
                                reportepracticas = ReportePracticas.objects.filter(id__in=idreport).order_by('orden')
                        else:
                            if escenariopractica.convenio:
                                reportepracticas = ReportePracticas.objects.filter(Q(carrera=escenariopractica.matricula.inscripcion.carrera,nivel=escenariopractica.matricula.nivel.nivelmalla,convenio=True,estudiante=False)| Q(convenio=True,estudiante=False,carrera=None)   | Q(general=True,estudiante=False)).order_by('orden')[:1]
                            else:
                                reportepracticas = ReportePracticas.objects.filter(Q(carrera=escenariopractica.matricula.inscripcion.carrera,nivel=escenariopractica.matricula.nivel.nivelmalla,sinconvenio=True,estudiante=False)| Q(sinconvenio=True,estudiante=False,carrera=None) |Q(general=True,estudiante=False)).order_by('orden')[:1]

                        data['reportepracticas'] = reportepracticas

                    data['HORAS_MIN_PRACTICAS'] = HORAS_MIN_PRACTICAS
                    data['PUNTAJE_APRUEBA_PRACTICA'] = PUNTAJE_APRUEBA_PRACTICA
                    data['ID_REPORTE_CARTA_ASIGNAC'] = ID_REPORTE_CARTA_ASIGNAC
                    gruposid = []
                    for g in Group.objects.filter().exclude(id__in=[ALUMNOS_GROUP_ID,SISTEMAS_GROUP_ID]):
                        gruposid.append(g.id)
                    data['gruposid'] = gruposid
                    if solicitudpractica:
                        if ProfesorMateria.objects.filter(materia__asignatura=ASIGNATURA_PRACTICAS_SM, materia__nivel=solicitudpractica.matricula.nivel).exists():
                            prof = ProfesorMateria.objects.filter(materia__asignatura=ASIGNATURA_PRACTICAS_SM, materia__nivel=solicitudpractica.matricula.nivel).order_by('-id')[:1].get()
                            if SupervisorPracticas.objects.filter(profesormateria=prof, solicitudpracticas=solicitudpractica, activo=True).exists():
                                supervisor = SupervisorPracticas.objects.get(profesormateria=prof, solicitudpracticas=solicitudpractica, activo=True)
                                data['supervisor_practicas'] = supervisor
                                if Persona.objects.filter(usuario=request.user, usuario__groups__id__in=[PROFESORES_GROUP_ID]).exists():
                                    data['es_supervisor'] = supervisor

                        if SupervisionPracticas.objects.filter(supervisor__solicitudpracticas=solicitudpractica).exists():
                            supervisiones = SupervisionPracticas.objects.filter(supervisor__solicitudpracticas=solicitudpractica).order_by('numsupervision')
                            supervisiones_det = SupervisionPracticasDet.objects.filter(supervision__supervisor__solicitudpracticas=solicitudpractica).order_by('indicadoracademico__id')
                            data['supervisiones'] = supervisiones
                            data['supervisiones_det'] = supervisiones_det

                        if TipoSupervisionPracticas.objects.filter(activo=True).exists():
                            tipo_supervision = TipoSupervisionPracticas.objects.filter(activo=True)
                            data['tipo_supervision'] = tipo_supervision

                    return render(request ,"solicitudpractica/solicitupracadm.html" ,  data)
                elif action == 'solicitudes':
                    solicitudpractica = SolicitudPracticas.objects.filter(enviada=True,matricula__inscripcion__id=request.GET['id'])
                    data['NIVELMALLA_INICIO_PRACTICA'] = NIVELMALLA_INICIO_PRACTICA
                    data['solicitudpractica'] = solicitudpractica
                    return render(request ,"solicitudpractica/listsolicipractadm.html" ,  data)
                elif action == 'escenarios':
                    escenariopracticas = EscenarioPractica.objects.filter(matricula__inscripcion__id=request.GET['id']).exclude(fechaenvio=None)
                    data['NIVELMALLA_INICIO_PRACTICA'] = NIVELMALLA_INICIO_PRACTICA
                    data['inscripcion'] = Inscripcion.objects.get(id=request.GET['id'])
                    data['escenariopracticas'] = escenariopracticas
                    return render(request ,"solicitudpractica/escenariopractadm.html" ,  data)
                elif action=='versolnoapor':
                    persona = data['persona']
                    data = {}
                    escenariopractica = EscenarioPractica.objects.filter(id=request.GET['id'])[:1].get()
                    data['solicitudpracticas'] = SolicitudPracticas.objects.filter(escenariopractica=escenariopractica,aprobada=False).exclude(fecaprobada=None)
                    data['escenariopractica'] = escenariopractica
                    data['persona'] = persona
                    data['adm'] = True
                    return render(request ,"solicitudpractica/vergestion.html" ,  data)
                elif action=='versolictudnoacep':
                    persona = data['persona']
                    data = {}
                    escenariopractica = EscenarioPractica.objects.filter(id=request.GET['id'])[:1].get()
                    data['solictudnoaceptada'] = escenariopractica.tiene_solinoaceptada()
                    data['escenariopractica'] = escenariopractica
                    data['persona'] = persona
                    return render(request ,"solicitudpractica/vergestion.html" ,  data)
                elif action=='agreestado':
                    solicitudpractica = SolicitudPracticas.objects.filter(id=request.GET['idsol'])[:1].get()
                    empresasinconv = EmpresaSinConvenio.objects.filter(id=request.GET['idemp'])[:1].get()
                    estadoempresa = EstadoEmpresa.objects.filter(id=request.GET['idesem'])[:1].get()
                    empresasinconv.estadoempresa = estadoempresa
                    empresasinconv.save()
                    return  HttpResponseRedirect('/solicitud_practicasadm?action=solicitud&ides='+str(solicitudpractica.escenariopractica.id)+'&idsol='+str(solicitudpractica.id)+'&fire=1')

                elif action=='veraplazado':
                    data = {}
                    inscripcion = Inscripcion.objects.get(id=request.GET['id'])
                    data['aplazados'] = inscripcion.exist_aplazados()
                    data['inscripcion'] = inscripcion
                    return render(request ,"solicitudpractica/vergestion.html" ,  data)

            else:
                idescenhorasis = SolicitudHorarioAsistente.objects.filter(horario__usuario=request.user).values('solicitud__escenariopractica').distinct('solicitud__escenariopractica')
                if 'aplazam' in request.GET:
                    idinscripcion = Matricula.objects.filter(aplazamiento=True).distinct('inscripcion').values('inscripcion')
                    idgrupos = Matricula.objects.filter(aplazamiento=True).distinct('inscripcion__carrera').values('inscripcion__carrera')
                    idcarreras = Matricula.objects.filter(aplazamiento=True).values('nivel__grupo').distinct('nivel__grupo')
                    # data['matricula'] = matriculas

                    search = None
                    if 's' in request.GET:
                        search = request.GET['s']
                        band=1
                    if search:
                        ss = search.split(' ')
                        while '' in ss:
                            ss.remove('')
                        if len(ss)==1:
                            inscripciones = Inscripcion.objects.filter(Q(persona__nombres__icontains=search) | Q(persona__apellido1__icontains=search) | Q(persona__apellido2__icontains=search) | Q(persona__cedula__icontains=search) | Q(persona__pasaporte__icontains=search) | Q(identificador__icontains=search) | Q(inscripciongrupo__grupo__nombre__icontains=search) | Q(carrera__nombre__icontains=search) | Q(persona__usuario__username__icontains=search),id__in=idinscripcion).order_by('persona__apellido1')[:100]
                        else:
                            inscripciones = Inscripcion.objects.filter(Q(persona__apellido1__icontains=ss[0]) & Q(persona__apellido2__icontains=ss[1]),id__in=idinscripcion).order_by('persona__apellido1','persona__apellido2','persona__nombres')[:100]
                    elif 'g' in request.GET:
                        grupoid = request.GET['g']
                        data['grupo'] = Grupo.objects.get(pk=request.GET['g'])
                        data['grupoid'] = int(grupoid) if grupoid else ""
                        inscripciones = Inscripcion.objects.filter(id__in=idinscripcion,inscripciongrupo__grupo__id=grupoid).order_by('persona__apellido1','persona__apellido2','persona__nombres')
                    elif 'c' in request.GET:
                        carreraid = request.GET['c']
                        data['grupo'] = Carrera.objects.get(pk=request.GET['c'])
                        data['carreraid'] = int(carreraid) if carreraid else ""
                        inscripciones = Inscripcion.objects.filter(id__in=idinscripcion,carrera__id=carreraid).order_by('persona__apellido1','persona__apellido2','persona__nombres')
                    else:
                        inscripciones = Inscripcion.objects.filter(id__in=idinscripcion).order_by('persona__apellido1','persona__apellido2','persona__nombres')
                    paging = MiPaginador(inscripciones, 30)
                    p = 1
                    try:
                        if 'page' in request.GET:
                            p = int(request.GET['page'])
                            # if band==0:
                            #     inscripciones = Inscripcion.objects.all().order_by('persona__apellido1')
                            paging = MiPaginador(inscripciones, 30)
                        page = paging.page(p)
                    except Exception as ex:
                        page = paging.page(1)

                    data['paging'] = paging
                    data['rangospaging'] = paging.rangos_paginado(p)
                    data['page'] = page
                    data['search'] = search if search else ""
                    data['inscripciones'] = page.object_list
                    data['grupos'] = Grupo.objects.filter(id__in=idgrupos).order_by('nombre')
                    data['carreras'] = Carrera.objects.filter(id__in=idcarreras).order_by('nombre')
                    return render(request ,"solicitudpractica/aplazado.html" ,  data)
                if request.user.has_perm('sga.add_escenariopractica'):
                    data['idescenhorasis'] = 1
                    if 'conven' in request.GET:
                        idinscripcion = EscenarioPractica.objects.filter(convenio=True).values('matricula__inscripcion').distinct('matricula__inscripcion')
                        idgrupos =  EscenarioPractica.objects.filter(convenio=True).values('matricula__nivel__grupo').distinct('matricula__nivel__grupo')
                        idcarreras =  EscenarioPractica.objects.filter(convenio=True).values('matricula__inscripcion__carrera').distinct('matricula__inscripcion__carrera')
                    elif 'filt' in request.GET:
                        filt = request.GET['filt']
                        if 'enviad' == filt:
                            idinscripcion = EscenarioPractica.objects.filter(convenio=True,aprobado=False,fechafinaliza=None).values('matricula__inscripcion').distinct('matricula__inscripcion')
                            idgrupos =  EscenarioPractica.objects.filter(convenio=True,aprobado=False,fechafinaliza=None).values('matricula__nivel__grupo').distinct('matricula__nivel__grupo')
                            idcarreras =  EscenarioPractica.objects.filter(convenio=True,aprobado=False,fechafinaliza=None).values('matricula__inscripcion__carrera').distinct('matricula__inscripcion__carrera')
                        elif 'poracep' == filt:
                            idinscripcion = EscenarioPractica.objects.filter(convenio=True,aprobado=True,fechaacepta=None).values('matricula__inscripcion').distinct('matricula__inscripcion')
                            idgrupos =  EscenarioPractica.objects.filter(convenio=True,aprobado=True,fechaacepta=None).values('matricula__nivel__grupo').distinct('matricula__nivel__grupo')
                            idcarreras =  EscenarioPractica.objects.filter(convenio=True,aprobado=True,fechaacepta=None).values('matricula__inscripcion__carrera').distinct('matricula__inscripcion__carrera')
                        elif 'aceptad' == filt:
                            idinscripcion = EscenarioPractica.objects.filter(convenio=True,aprobado=True).exclude(fechaacepta=None).values('matricula__inscripcion').distinct('matricula__inscripcion')
                            idgrupos =  EscenarioPractica.objects.filter(convenio=True,aprobado=True).exclude(fechaacepta=None).values('matricula__nivel__grupo').distinct('matricula__nivel__grupo')
                            idcarreras =  EscenarioPractica.objects.filter(convenio=True,aprobado=True).exclude(fechaacepta=None).values('matricula__inscripcion__carrera').distinct('matricula__inscripcion__carrera')
                    elif 'sinconven' in request.GET:
                        idinscripcion = EscenarioPractica.objects.filter(convenio=False).exclude(fechaenvio=None).values('matricula__inscripcion').distinct('matricula__inscripcion')
                        idgrupos =  EscenarioPractica.objects.filter(convenio=False).exclude(fechaenvio=None).values('matricula__nivel__grupo').distinct('matricula__nivel__grupo')
                        idcarreras =  EscenarioPractica.objects.filter(convenio=False).exclude(fechaenvio=None).values('matricula__inscripcion__carrera').distinct('matricula__inscripcion__carrera')
                    elif 'sinapr' in request.GET:
                        data['poraprobar'] = 1
                        idinscripcion = EscenarioPractica.objects.filter(fechafinaliza=None).exclude(fechaenvio=None).values('matricula__inscripcion').distinct('matricula__inscripcion')
                        idgrupos =  EscenarioPractica.objects.filter(fechafinaliza=None).exclude(fechaenvio=None).values('matricula__nivel__grupo').distinct('matricula__nivel__grupo')
                        idcarreras =  EscenarioPractica.objects.filter(fechafinaliza=None).exclude(fechaenvio=None).values('matricula__inscripcion__carrera').distinct('matricula__inscripcion__carrera')
                    else:
                        # idinscripcion = EscenarioPractica.objects.filter().values_list('matricula__inscripcion',flat=True).distinct('matricula__inscripcion')
                        idinscripcion = EscenarioPractica.objects.filter(convenio=False).exclude(fechaenvio=None).values_list('matricula__inscripcion',flat=True).distinct('matricula__inscripcion')
                        idinscripcion = list(chain(idinscripcion, EscenarioPractica.objects.filter(convenio=True).exclude(fechaenvio=None).values_list('matricula__inscripcion',flat=True).distinct('matricula__inscripcion')))
                        idgrupos =  EscenarioPractica.objects.filter(convenio=False).exclude(fechaenvio=None).values_list('matricula__nivel__grupo',flat=True).distinct('matricula__nivel__grupo')
                        idgrupos = list(chain(idgrupos, EscenarioPractica.objects.filter(convenio=True).exclude(fechaenvio=None).values_list('matricula__nivel__grupo',flat=True).distinct('matricula__nivel__grupo')))
                        idcarreras =  EscenarioPractica.objects.filter(convenio=False).exclude(fechaenvio=None).values_list('matricula__inscripcion__carrera',flat=True).distinct('matricula__inscripcion__carrera')
                        idcarreras = list(chain(idcarreras,EscenarioPractica.objects.filter(convenio=True).exclude(fechaenvio=None).values_list('matricula__inscripcion__carrera',flat=True).distinct('matricula__inscripcion__carrera')))

                elif Persona.objects.filter(usuario=request.user, usuario__groups__id__in=[PROFESORES_GROUP_ID]).exists():
                    supervisor = SupervisorPracticas.objects.filter(profesormateria__profesor__persona__usuario=request.user).values('solicitudpracticas')
                    solicitudes = SolicitudPracticas.objects.filter(id__in=supervisor).values('escenariopractica')
                    idinscripcion = EscenarioPractica.objects.filter(id__in=solicitudes).values_list('matricula__inscripcion',flat=True).distinct('matricula__inscripcion')
                    idgrupos =  EscenarioPractica.objects.filter(id__in=idescenhorasis,convenio=False).exclude(fechaenvio=None).values_list('matricula__nivel__grupo',flat=True).distinct('matricula__nivel__grupo')
                    idgrupos = list(chain(idgrupos, EscenarioPractica.objects.filter(convenio=True).exclude(fechaenvio=None).values_list('matricula__nivel__grupo',flat=True).distinct('matricula__nivel__grupo')))
                    idcarreras =  EscenarioPractica.objects.filter(id__in=idescenhorasis,convenio=False).exclude(fechaenvio=None).values_list('matricula__inscripcion__carrera',flat=True).distinct('matricula__inscripcion__carrera')
                    idcarreras = list(chain(idcarreras,EscenarioPractica.objects.filter(convenio=True).exclude(fechaenvio=None).values_list('matricula__inscripcion__carrera',flat=True).distinct('matricula__inscripcion__carrera')))
                    data['es_supervisor'] = supervisor
                else:
                    if 'sinapr' in request.GET:
                        data['poraprobar'] = 1
                        idinscripcion = EscenarioPractica.objects.filter(fechafinaliza=None,id__in=idescenhorasis,convenio=False).exclude(fechaenvio=None).values('matricula__inscripcion').distinct('matricula__inscripcion')
                        idgrupos =  EscenarioPractica.objects.filter(fechafinaliza=None,id__in=idescenhorasis,convenio=False).exclude(fechaenvio=None).values('matricula__nivel__grupo').distinct('matricula__nivel__grupo')
                        idcarreras =  EscenarioPractica.objects.filter(fechafinaliza=None,id__in=idescenhorasis,convenio=False).exclude(fechaenvio=None).values('matricula__inscripcion__carrera').distinct('matricula__inscripcion__carrera')
                    else:
                        idinscripcion = EscenarioPractica.objects.filter(id__in=idescenhorasis,convenio=False).exclude(fechaenvio=None).values('matricula__inscripcion').distinct('matricula__inscripcion')
                        idgrupos =  EscenarioPractica.objects.filter(id__in=idescenhorasis,convenio=False).exclude(fechaenvio=None).values('matricula__nivel__grupo').distinct('matricula__nivel__grupo')
                        idcarreras =  EscenarioPractica.objects.filter(id__in=idescenhorasis,convenio=False).exclude(fechaenvio=None).values('matricula__inscripcion__carrera').distinct('matricula__inscripcion__carrera')
                search = None
                if 's' in request.GET:
                    search = request.GET['s']
                    band=1
                if search:
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')
                    if len(ss)==1:
                        inscripciones = Inscripcion.objects.filter(Q(persona__nombres__icontains=search) | Q(persona__apellido1__icontains=search) | Q(persona__apellido2__icontains=search) | Q(persona__cedula__icontains=search) | Q(persona__pasaporte__icontains=search) | Q(identificador__icontains=search) | Q(inscripciongrupo__grupo__nombre__icontains=search) | Q(carrera__nombre__icontains=search) | Q(persona__usuario__username__icontains=search),id__in=idinscripcion).order_by('persona__apellido1')[:100]
                    else:
                        inscripciones = Inscripcion.objects.filter(Q(persona__apellido1__icontains=ss[0]) & Q(persona__apellido2__icontains=ss[1]),id__in=idinscripcion).order_by('persona__apellido1','persona__apellido2','persona__nombres')[:100]
                elif 'g' in request.GET:
                    grupoid = request.GET['g']
                    data['grupo'] = Grupo.objects.get(pk=request.GET['g'])
                    data['grupoid'] = int(grupoid) if grupoid else ""
                    inscripciones = Inscripcion.objects.filter(id__in=idinscripcion,inscripciongrupo__grupo__id=grupoid).order_by('persona__apellido1','persona__apellido2','persona__nombres')
                elif 'c' in request.GET:
                    carreraid = request.GET['c']
                    data['grupo'] = Carrera.objects.get(pk=request.GET['c'])
                    data['carreraid'] = int(carreraid) if carreraid else ""
                    inscripciones = Inscripcion.objects.filter(id__in=idinscripcion,carrera__id=carreraid).order_by('persona__apellido1','persona__apellido2','persona__nombres')
                else:
                    inscripciones = Inscripcion.objects.filter(id__in=idinscripcion).order_by('persona__apellido1','persona__apellido2','persona__nombres')
                paging = MiPaginador(inscripciones, 30)
                p = 1
                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                        # if band==0:
                        #     inscripciones = Inscripcion.objects.all().order_by('persona__apellido1')
                        paging = MiPaginador(inscripciones, 30)
                    page = paging.page(p)
                except Exception as ex:
                    page = paging.page(1)

                data['paging'] = paging
                data['rangospaging'] = paging.rangos_paginado(p)
                data['page'] = page
                data['search'] = search if search else ""
                data['inscripciones'] = page.object_list
                data['grupos'] = Grupo.objects.filter(id__in=idgrupos).order_by('nombre')
                data['carreras'] = Carrera.objects.filter(id__in=idcarreras).order_by('nombre')
                return render(request ,"solicitudpractica/inscripcionescenario.html" ,  data)
    except Exception as e:
        print("Error solicitudpractica "+str(e))
        return HttpResponseRedirect('/?info=Error comuniquese con el administrador')
