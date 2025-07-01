import csv
from datetime import datetime, timedelta
import json
import os
import urllib
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Avg
from django.db.models.aggregates import Sum
from django.db import transaction
from django.db.models.query_utils import Q
from django.forms.models import model_to_dict
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.utils.encoding import force_str
from django.template import RequestContext
from decorators import secure_module
from settings import CENTRO_EXTERNO, RUBRO_TIPO_OTRO_MODULO_INTERNO, RUBRO_TIPO_OTRO_INSCRIPCION, DEFAULT_PASSWORD, PROFESORES_GROUP_ID, \
    ALUMNOS_GROUP_ID, UTILIZA_GRUPOS_ALUMNOS, REPORTE_CERTIFICADO_INSCRIPCION, EMAIL_ACTIVE, EVALUACION_ITB, REGISTRO_HISTORIA_NOTAS, \
    NOTA_ESTADO_EN_CURSO, GENERAR_RUBROS_PAGO, GENERAR_RUBRO_INSCRIPCION, GENERAR_RUBRO_INSCRIPCION_MARGEN_DIAS, MODELO_EVALUACION, \
    EVALUACION_IAVQ, EVALUACION_ITS, UTILIZA_NIVEL0_PROPEDEUTICO, TIPO_PERIODO_PROPEDEUTICO, NOTA_ESTADO_APROBADO, UTILIZA_FICHA_MEDICA,\
    EVALUACION_TES, CORREO_INSTITUCIONAL, USA_CORREO_INSTITUCIONAL, INSCRIPCION_CONDUCCION,PORCIENTO_NOTA1,PORCIENTO_NOTA2,PORCIENTO_NOTA3,\
    PORCIENTO_NOTA4,PORCIENTO_NOTA5,PORCIENTO_RECUPERACION,ASIGNATURA_PRACTICA_CONDUCCION,NOTA_PARA_APROBAR, ASIST_PARA_APROBAR,\
    ASIGNATURA_EDU_VIAL, ASIGNATURA_LEY_TRANSPORTE,ASIGNATURA_PRACTICAS_CONDU, CARRERAS_ID_EXCLUIDAS_INEC, CORREO_JEFE_ASUNTO_ESTUDIANTIL

from sga.alu_malla import aprobadaAsignatura
from sga.commonviews import addUserData, ip_client_address
from sga.docentes import calculate_username
from sga.forms import PersonaForm, InscripcionForm, RecordAcademicoForm, HistoricoRecordAcademicoForm, HistoriaNivelesDeInscripcionForm, CargarFotoForm, EmpresaInscripcionForm, EstudioInscripcionForm, DocumentoInscripcionForm, ActividadesInscripcionForm, PadreClaveForm, ConvalidacionInscripcionForm, HistoricoNotasITBForm, GraduadoDatosForm, EgresadoForm, InscripcionSenescytForm, RetiradoMatriculaForm, InscripcionCextForm, BecarioForm, InscripcionPracticaForm, ObservacionInscripcionForm, ProcesoDobeForm,  ActivaInactivaUsuarioForm, HistoricoNotasPracticaForm

from sga.models import Profesor, ProcesoDobe, Persona, Inscripcion, RecordAcademico, DocumentosDeInscripcion, HistoricoRecordAcademico, HistoriaNivelesDeInscripcion, \
    FotoPersona, EmpresaInscripcion, EstudioInscripcion, DocumentoInscripcion, Archivo, TipoArchivo, Grupo, InscripcionGrupo, PerfilInscripcion, HistoricoNotasITB,\
    PadreClave, Malla, ConvalidacionInscripcion, TipoEstado, Rubro, RubroInscripcion, NivelMalla, EjeFormativo, AsignaturaMalla, Egresado, Asignatura, InscripcionSenescyt, \
    RetiradoMatricula, Carrera, Modalidad, Sesion, Especialidad, Materia, Nivel, TipoOtroRubro, Matricula, MateriaAsignada, RubroOtro, Graduado, InscripcionBecario, \
    InscripcionPracticas, ObservacionInscripcion, InscripcionConduccion, InactivaActivaUsr,PreInscripcion,EstudianteXEgresar, Sexo,HistoricoNotasPractica,GraduadoConduccion, \
    Periodo, EquivalenciaCondu,AtencionCliente,TurnoDet,TurnoCab, OpcionRespuesta, OpcionEstadoLlamada, EstadoLlamada, Referidos, RegistroSeguimiento, LlamadaUsuario, \
    SolicituInfo,IncidenciaAdministrativo,AsistAsuntoEstudiant,IncidenciaAsignada,SolicitudSecretariaDocente
from sga.tasks import gen_passwd, send_html_mail
from decimal import Decimal

def guardar():
    try:
        url = ("http://www.itb.edu.ec/public/docs/dataformcontacto.txt")

        # Crea el archivo dato.txt
        # urllib.urlretrieve(url,"contacto3.txt")
        urllib.urlretrieve(url,"/var/lib/django/repobucki/media/reportes/contacto.txt")
        #
        # Archivo web
        # SITE_ROOT = os.path.dirname(os.path.realpath(__file__))

        # csv_filepathname= "dato.txt"

        # csv_filepathname="contacto3.txt"
        csv_filepathname="/var/lib/django/repobucki/media/reportes/contacto.txt"

        # your_djangoproject_home=os.path.split(SITE_ROOT)[0]

        # sys.path.append(your_djangoproject_home)
        os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

        dataReader = csv.reader(open(csv_filepathname), delimiter=';')


        LINE = -1
        for row in dataReader:
            if row:
                # LINE += 1
                # if LINE==1:
                #     continue
                try:
                    if not SolicituInfo.objects.filter(codigo=row[0]).exists():
                        solicitud  = SolicituInfo(codigo=row[0],
                                        identificacion  = row[0],
                                        nombres=row[1],
                                        correo=row[2],
                                        ciudad=row[3],
                                        direccion=row[4],
                                        fonodom=row[5],
                                        fonoofi=row[6],
                                        celular=row[7],
                                        interes=row[9],
                                        mensaje=row[10],
                                        fecha = row[11])
                        solicitud.save()
                    else:
                        solicitud=SolicituInfo.objects.filter(codigo=row[0])[:1].get()
                        solicitud.codigo=row[0]
                        solicitud.nombres=row[1]
                        solicitud.correo=row[2]
                        solicitud.ciudad=row[3]
                        solicitud.direccion=row[4]
                        solicitud.fonodom=row[5]
                        solicitud.fonoofi=row[6]
                        solicitud.celular=row[7]
                        solicitud.interes=row[9]
                        solicitud.mensaje=row[10]
                        solicitud.fecha = row[11]

                    solicitud.save()
                        # print(preinscripcion.nombres + " " +preinscripcion.apellido1)
                except Exception as ex:
                        pass
    except Exception as ex:
        pass
    # os.remove("contacto.txt")
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
@secure_module
@transaction.atomic()
def view(request):
    if request.method=='POST':
        action = request.POST['action']
        try:
            if action=='addseguimientoinscrito':
                try:


                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
            # //////////////////////////////////////////////////////////////////////////////////////////////////
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
                    if EMAIL_ACTIVE:
                        incidenciaasignada.email_asistenteasigna('Solicitud de Alumnos')
                    return HttpResponseRedirect("/seguimiento?action=solicitudes")
                except Exception as ex:
                    return HttpResponseRedirect("/seguimiento?action=solicitudes&error=Error Vuelva  intentarlo")

            elif action == "finalizasol":
                try:
                    if SolicitudSecretariaDocente.objects.filter(id = request.POST['idsolici'],cerrada=False).exists():
                        solicitud = SolicitudSecretariaDocente.objects.filter(id = request.POST['idsolici'])[:1].get()
                        if AsistAsuntoEstudiant.objects.filter(asistente__usuario=request.user).exists():
                            asistente = AsistAsuntoEstudiant.objects.filter(asistente__usuario=request.user)[:1].get()
                            if not IncidenciaAsignada.objects.filter(solicitusecret=solicitud,asistenteasignado=asistente).exists():
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
                                "emails/email_resolucionincidencia.html", {'self': solicitud, 'fecha': hoy,"tip":'Incidencia Administrativas','contenido': contenido,'personarespon':personarespon},lista.split(','))

                        return HttpResponseRedirect("/seguimiento?action=solicitudes")
                    else:
                        return HttpResponseRedirect("/seguimiento?action=solicitudes&error=La incidencia ya esta finalizada")
                except Exception as ex:
                    return HttpResponseRedirect("/seguimiento?action=solicitudes&error=Error Vuelva  intentarlo")
            # //////////////////////////////////////////////////////////////////////////////////////////////////
            elif action=='addseguimientopreinscrito':
                try:
                    preinscripcion =  PreInscripcion.objects.get(pk=request.POST['id'])


                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

            elif action == 'guardar':
                try:
                    registro = RegistroSeguimiento.objects.get(pk=request.POST['id'])
                    registro.identificacion = request.POST['iden']
                    registro.nombres = request.POST['nomb']
                    registro.apellidos = request.POST['ape']
                    registro.celular = request.POST['cel']
                    registro.email = request.POST['email']
                    registro.ciudad = request.POST['ciu']
                    registro.fonodomicilio = request.POST['fonod']
                    registro.fonotrabajo = request.POST['fonot']
                    registro.lugartrabajo = request.POST['lugart']
                    registro.ext = request.POST['ext']

                    registro.observacion = request.POST['obs']
                    registro.save()

                    if request.POST['sexo'] !='0' :
                        registro.sexo.id = request.POST['sexo']
                        registro.save()

                    if 'opc' in request.POST:
                        try:
                            if OpcionRespuesta.objects.filter(pk=request.POST['opc']).exists():
                                op = OpcionRespuesta.objects.get(pk=request.POST['opc'])
                                registro.opcionrespuesta = op
                                registro.save()
                        except:
                            pass

                    if 'motivor' in request.POST:
                        registro.motivorespuesta = request.POST['motivor']
                        registro.save()

                    if 'info' in request.POST:
                        if request.POST['info'] == 'on':
                            registro.enviarinformacion = True

                        else:
                            registro.enviarinformacion = False
                        registro.save()
                    if 'enviado' in request.POST:
                        if request.POST['enviado'] == 'on':
                            registro.enviado = True

                        else:
                            registro.enviado = False
                        registro.save()
                    if request.POST['rid1']:
                        if Referidos.objects.filter(pk=request.POST['rid1']).exists():
                            referido = Referidos.objects.get(pk=request.POST['rid1'])
                            referido.nombres = request.POST['rnombre1']
                            referido.celular = request.POST['rcel1']
                            referido.email = request.POST['remail1']
                            referido.save()

                    else:
                        referido = Referidos(registro=registro,
                                             nombres = request.POST['rnombre1'],
                                             celular = request.POST['rcel1'],
                                             email = request.POST['remail1'])

                        referido.save()
                    if request.POST['rid2']:
                        if Referidos.objects.filter(pk=request.POST['rid2']).exists():
                            referido = Referidos.objects.get(pk=request.POST['rid2'])
                            referido.nombres = request.POST['rnombre2']
                            referido.celular = request.POST['rcel2']
                            referido.email = request.POST['remail2']
                            referido.save()
                    else:
                         referido = Referidos(registro=registro,
                                              nombres = request.POST['rnombre2'],
                                             celular = request.POST['rcel2'],
                                             email = request.POST['remail2'])

                         referido.save()
                    if request.POST['rid3']:
                        if Referidos.objects.filter(pk=request.POST['rid3']).exists():
                            referido = Referidos.objects.get(pk=request.POST['rid3'])
                            referido.nombres = request.POST['rnombre3']
                            referido.celular = request.POST['rcel3']
                            referido.email = request.POST['remail3']
                            referido.save()
                    else:
                         referido = Referidos(registro=registro,
                                             nombres = request.POST['rnombre3'],
                                             celular = request.POST['rcel3'],
                                             email = request.POST['remail3'])

                         referido.save()



                    usuario = LlamadaUsuario(usuario=request.user,
                                             registro=registro,
                                             fecha=datetime.now())
                    usuario.save()
                    if 'estado' in request.POST:
                        if  EstadoLlamada.objects.filter(pk=request.POST['estado']).exists():
                            est = EstadoLlamada.objects.get(pk=request.POST['estado'])
                            usuario.estadollamada = est
                            usuario.save()
                    if 'opcestado' in request.POST:
                        if  OpcionEstadoLlamada.objects.filter(pk=request.POST['opcestado']).exists():
                            opc = OpcionEstadoLlamada.objects.get(pk=request.POST['opcestado'])
                            usuario.opcionllamada= opc
                            usuario.save()

                    if 'nota' in request.POST:
                        usuario.nota= request.POST['nota']
                        usuario.save()

                    if  request.POST['ids'] != '':
                        solicitud = SolicituInfo.objects.get(pk=request.POST['ids'])
                        solicitud.identificacion = registro.identificacion
                        solicitud.save()


                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
            elif action == 'consulta':
                try:
                    lista=[]
                    if OpcionEstadoLlamada.objects.filter(estadollamada__id=request.POST['id']).exists():
                        for op in OpcionEstadoLlamada.objects.filter(estadollamada__id=request.POST['id']):
                            lista.append((op.id , op.descripcion))
                        return HttpResponse(json.dumps({"result":"ok","lista":lista }),content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({"result":"nodata" }),content_type="application/json")


                except:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

            elif action == 'asigasitente':
                try:
                    if not IncidenciaAsignada.objects.filter(incidenciaadministrativo__id=request.POST['idincide'],asistenteasignado__id=request.POST['idasist']).exists():
                        incidenciaasignada = IncidenciaAsignada(incidenciaadministrativo_id = request.POST['idincide'],
                                                                observacion = request.POST['observacion'],
                                                                asistenteasignado_id = request.POST['idasist'],
                                                                fecha=datetime.now(),
                                                                atendiendo = True )
                        incidenciaasignada.save()
                        incidenciaasignada.incidenciaadministrativo.asignado = True
                        incidenciaasignada.incidenciaadministrativo.save()
                        if IncidenciaAsignada.objects.filter(incidenciaadministrativo=incidenciaasignada.incidenciaadministrativo,atendiendo=True).exclude(id=incidenciaasignada.id).order_by('id').exists():
                            incidenciaasignadaanterior = IncidenciaAsignada.objects.filter(incidenciaadministrativo=incidenciaasignada.incidenciaadministrativo,atendiendo=True).exclude(id=incidenciaasignada.id).order_by('id')[:1].get()
                            incidenciaasignadaanterior.atendiendo = False
                            incidenciaasignadaanterior.save()
                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(incidenciaasignada).pk,
                            object_id       = incidenciaasignada.id,
                            object_repr     = force_str(incidenciaasignada),
                            action_flag     = ADDITION,
                            change_message  = 'Asignado asistente a incidencia administrativa (' + client_address + ')' )
                    else:
                        if IncidenciaAsignada.objects.filter(incidenciaadministrativo__id=request.POST['idincide'],asistenteasignado__id=request.POST['idasist'],atendiendo=False).exists():
                            incidenciaasignada = IncidenciaAsignada.objects.filter(incidenciaadministrativo__id=request.POST['idincide'],asistenteasignado__id=request.POST['idasist'],atendiendo=False)[:1].get()
                            incidenciaasignada.atendiendo=True
                            incidenciaasignada.observacion=request.POST['observacion']
                            incidenciaasignada.fecha=datetime.now()
                            incidenciaasignada.save()
                            if IncidenciaAsignada.objects.filter(incidenciaadministrativo=incidenciaasignada.incidenciaadministrativo,atendiendo=True).exclude(id=incidenciaasignada.id).order_by('id').exists():
                                incidenciaasignadaanterior = IncidenciaAsignada.objects.filter(incidenciaadministrativo=incidenciaasignada.incidenciaadministrativo,atendiendo=True).exclude(id=incidenciaasignada.id).order_by('id')[:1].get()
                                incidenciaasignadaanterior.atendiendo = False
                                incidenciaasignadaanterior.save()
                            client_address = ip_client_address(request)
                            LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(incidenciaasignada).pk,
                                object_id       = incidenciaasignada.id,
                                object_repr     = force_str(incidenciaasignada),
                                action_flag     = ADDITION,
                                change_message  = 'asistente Reasignado a incidencia administrativa (' + client_address + ')' )
                    if EMAIL_ACTIVE:
                        incidenciaasignada.email_asistenteasigna("Incidencia Administrativa")
                    return HttpResponseRedirect("/seguimiento?action=incidenciaadminis")
                except:
                    return HttpResponseRedirect("/seguimiento?action=incidenciaadminis&error=Error Vuelva  intentarlo")

            elif action == 'asigasitentecorreo':
                try:
                    if not IncidenciaAsignada.objects.filter(solicituinfo__id=request.POST['idincide'],asistenteasignado__id=request.POST['idasist']).exists():
                        incidenciaasignada = IncidenciaAsignada(solicituinfo_id = request.POST['idincide'],
                                                                observacion = request.POST['observacion'],
                                                                asistenteasignado_id = request.POST['idasist'],
                                                                atendiendo = True,
                                                                fecha=datetime.now())
                        incidenciaasignada.save()
                        incidenciaasignada.solicituinfo.asignado = True
                        incidenciaasignada.solicituinfo.save()
                        if IncidenciaAsignada.objects.filter(solicituinfo=incidenciaasignada.solicituinfo,atendiendo=True).exclude(id=incidenciaasignada.id).order_by('id').exists():
                            incidenciaasignadaanterior = IncidenciaAsignada.objects.filter(solicituinfo=incidenciaasignada.solicituinfo,atendiendo=True).exclude(asistenteasignado=incidenciaasignada.asistenteasignado).order_by('id')[:1].get()
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
                            change_message  = 'Asignado asistente a correo info (' + client_address + ')' )

                    else:
                        if IncidenciaAsignada.objects.filter(solicituinfo__id=request.POST['idincide'],asistenteasignado__id=request.POST['idasist'],atendiendo=False).exists():
                            incidenciaasignada = IncidenciaAsignada.objects.filter(solicituinfo__id=request.POST['idincide'],asistenteasignado__id=request.POST['idasist'],atendiendo=False)[:1].get()
                            incidenciaasignada.atendiendo=True
                            incidenciaasignada.observacion=request.POST['observacion']
                            incidenciaasignada.fecha=datetime.now()
                            incidenciaasignada.save()
                            if IncidenciaAsignada.objects.filter(solicituinfo=incidenciaasignada.solicituinfo,atendiendo=True).exclude(id=incidenciaasignada.id).order_by('id').exists():
                                incidenciaasignadaanterior = IncidenciaAsignada.objects.filter(solicituinfo=incidenciaasignada.solicituinfo,atendiendo=True).exclude(asistenteasignado=incidenciaasignada.asistenteasignado).order_by('id')[:1].get()
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
                                change_message  = 'Asistente reasignado a correo info (' + client_address + ')' )
                    if EMAIL_ACTIVE:
                        incidenciaasignada.email_asistenteasigna("Correo Info")
                    return HttpResponseRedirect("/seguimiento?action=correos")
                except:
                    return HttpResponseRedirect("/seguimiento?action=correos&error=Error Vuelva  intentarlo")


            return HttpResponseRedirect("/seguimiento")

        except:
            return HttpResponseRedirect("/seguimiento")
    else:
        data = {'title': 'Seguimiento'}
        addUserData(request,data)
        try:
            if 'action' in request.GET:
                action = request.GET['action']
                if action=='verasistentes':
                    data = {}
                    data['asistentes'] = IncidenciaAsignada.objects.filter(solicituinfo__id=request.GET['idinfo'])
                    return render(request ,"asuntoestudiantil/verasistentes.html" ,  data)

                elif action=='verasistentessoli':
                    data = {}
                    data['asistentes'] = IncidenciaAsignada.objects.filter(solicitusecret__id=request.GET['idinfo'])
                    return render(request ,"asuntoestudiantil/verasistentes.html" ,  data)

                elif action=='correos':
                    if 'ficha' in request.GET:
                        solicitud = SolicituInfo.objects.get(id=request.GET['id'])
                        data['solicitud'] = solicitud
                        if RegistroSeguimiento.objects.filter(identificacion=solicitud.identificacion).exists():
                            registro = RegistroSeguimiento.objects.filter(identificacion=solicitud.identificacion)[:1].get()

                        else:
                            registro = RegistroSeguimiento(identificacion = solicitud.identificacion,
                                                           nombres=solicitud.nombres,
                                                            celular = solicitud.celular,
                                                            email =  solicitud.correo,
                                                            fonodomicilio = solicitud.fonodom,
                                                            fonotrabajo = solicitud.fonoofi,
                                                            ciudad=solicitud.ciudad)

                            registro.save()
                        # registro.seinscribio = registro.se_incribio()
                        # registro.pago = registro.pago_ins()
                        data['registro'] = registro
                        ref =[]
                        if registro.opcionrespuesta:
                            data['opcrespuesta'] = OpcionRespuesta.objects.filter().exclude(pk=registro.opcionrespuesta.id)
                        else:
                            data['opcrespuesta'] = OpcionRespuesta.objects.all()
                        data['estadollamada'] = EstadoLlamada.objects.all()
                        data['opcllamada'] = OpcionEstadoLlamada.objects.all()
                        if registro.sexo:
                            data['sexo'] = Sexo.objects.filter().exclude(pk=registro.sexo.id)
                        else:
                            data['sexo'] = Sexo.objects.all()
                        # data['referidos'] = Referidos.objects.filter(registro=registro)
                        for r in Referidos.objects.filter(registro=registro):
                            ref.append((r.id,r.nombres,r.celular,r.email))
                        data['ref'] = ref

                        data['llamada'] = LlamadaUsuario.objects.filter(registro=registro)
                        if LlamadaUsuario.objects.filter(registro=registro,estadollamada__id=1).exists():
                            data['efectiva'] = 1
                        data['op'] = 'correo'
                        return render(request ,"seguimiento/ficha.html" ,  data)
                    else:

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
                        if 'i' in request.GET:
                            inactivos = request.GET['i']
                        if 't' in request.GET:
                            todos = request.GET['t']
                        if 'f' in request.GET:
                            finalizados = request.GET['f']
                        if search:
                            ss = search.split(' ')
                            while '' in ss:
                                ss.remove('')
                            if len(ss)==1:
                                solicitudes = SolicituInfo.objects.filter(Q(Q(nombres__icontains=search) | Q(codigo__icontains=search) | Q(identificacion=search))).order_by('-codigo')
                            else:
                                solicitudes = SolicituInfo.objects.filter(Q(Q(nombres__icontains=search) | Q(codigo__icontains=search))).order_by('-codigo')

                        else:
                            guardar()
                            solicitudes = SolicituInfo.objects.filter(finalizado=False).order_by('-codigo')
                            # inscripciones = Inscripcion.objects.filter(persona__usuario__is_active=True,fecha__gte=fecha).order_by('persona__apellido1')[:100]


                        #     inscripciones = inscripciones.filter(carrera__grupocoordinadorcarrera__group__in=request.user.groups.all()).distinct()

                        if todos:
                            solicitudes = SolicituInfo.objects.filter(finalizado=False).order_by('-codigo')

                        if finalizados:
                            data['finalizados'] = finalizados
                            solicitudes = SolicituInfo.objects.filter(finalizado=True).order_by('-codigo')


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
                        data['fechaactual'] = datetime.now().date()
                        data['asistasuntoestudiant'] = AsistAsuntoEstudiant.objects.filter(estado=True)


                        return render(request ,"seguimiento/seguimiento.html" ,  data)


                elif action == 'online':

                    if 'ficha' in request.GET:
                        preinscripcion = PreInscripcion.objects.get(id=request.GET['id'])
                        if RegistroSeguimiento.objects.filter(identificacion=preinscripcion.cedula).exists():
                            registro = RegistroSeguimiento.objects.filter(identificacion=preinscripcion.cedula)[:1].get()

                        else:
                            registro = RegistroSeguimiento(identificacion = preinscripcion.cedula,
                                                           nombres=preinscripcion.nombres,
                                                           apellidos = str(preinscripcion.apellido1 + " "+  preinscripcion.apellido2),
                                                            celular = preinscripcion.celular,
                                                            email =  preinscripcion.email,
                                                            fonodomicilio = preinscripcion.telefono,
                                                            sexo_id = preinscripcion.sexo.id)
                            registro.save()
                        # registro.seinscribio = registro.se_incribio()
                        # registro.pago = registro.pago_ins()
                        registro.save()
                        data['registro'] = registro
                        ref =[]
                        if registro.opcionrespuesta:
                            data['opcrespuesta'] = OpcionRespuesta.objects.filter().exclude(pk=registro.opcionrespuesta.id)
                        else:
                            data['opcrespuesta'] = OpcionRespuesta.objects.all()
                        data['estadollamada'] = EstadoLlamada.objects.all()
                        data['opcllamada'] = OpcionEstadoLlamada.objects.all()
                        if registro.sexo:
                            data['sexo'] = Sexo.objects.filter().exclude(pk=registro.sexo.id)
                        else:
                            data['sexo'] = Sexo.objects.all()
                        # data['referidos'] = Referidos.objects.filter(registro=registro)
                        for r in Referidos.objects.filter(registro=registro):
                            ref.append((r.id,r.nombres,r.celular,r.email))
                        data['ref'] = ref

                        data['llamada'] = LlamadaUsuario.objects.filter(registro=registro)
                        if LlamadaUsuario.objects.filter(registro=registro,estadollamada__id=1).exists():
                            data['efectiva'] = 1

                        data['op'] = 'online'
                        return render(request ,"seguimiento/ficha.html" ,  data)


                    elif 'addregistro' in request.GET:

                        return render(request ,"seguimiento/addobservacion.html" ,  data)





                    else:
                        try:
                            hoy = str(datetime.date(datetime.now()))
                            search = None
                            todos = None
                            activos = None
                            inactivos = None

                            if 's' in request.GET:
                                search = request.GET['s']
                            if 'a' in request.GET:
                                activos = request.GET['a']
                            if 'i' in request.GET:
                                inactivos = request.GET['i']
                            if 't' in request.GET:
                                todos = request.GET['t']
                            if search:
                                ss = search.split(' ')
                                while '' in ss:
                                    ss.remove('')
                                if len(ss)==1:
                                    preinscritos = PreInscripcion.objects.filter(Q(nombres__icontains=search,inscrito=False, fecha_caducidad__lt=hoy) | Q(apellido1__icontains=search,inscrito=False, fecha_caducidad__lt=hoy) | Q(apellido2__icontains=search,inscrito=False, fecha_caducidad__lt=hoy) | Q(cedula__icontains=search,inscrito=False, fecha_caducidad__lt=hoy) | Q(cedula=search,inscrito=False)| Q(grupo__nombre__icontains=search,inscrito=False, fecha_caducidad__lt=hoy) | Q(carrera__nombre__icontains=search,inscrito=False, fecha_caducidad__lt=hoy)).exclude(id__in=PreInscripcion.objects.filter(cedula__in=Inscripcion.objects.all().values('persona__cedula')).order_by('-fecha_registro').values('id')).order_by('-fecha_registro')
                                else:
                                    preinscritos = PreInscripcion.objects.filter(Q(apellido1__icontains=ss[0],inscrito=False, fecha_caducidad__lt=hoy) & Q(apellido2__icontains=ss[1],inscrito=False, fecha_caducidad__lt=hoy)).exclude(id__in=PreInscripcion.objects.filter(cedula__in=Inscripcion.objects.all().values('persona__cedula')).order_by('-fecha_registro').values('id')).order_by('-fecha_registro','apellido1','apellido2','nombres')

                            else:
                                # i = Inscripcion.objects.all().values('persona__cedula')

                                # preinscritos = PreInscripcion.objects.filter().exclude(cedula__in=Inscripcion.objects.all().values('persona__cedula')).order_by('-fecha_registro')
                                preinscritos=PreInscripcion.objects.filter().exclude(id__in=PreInscripcion.objects.filter(cedula__in=Inscripcion.objects.all().values('persona__cedula')).order_by('fecha_registro').values('id')).order_by('-fecha_registro')
                                # preinscritos = PreInscripcion.objects.filter(inscrito=False, fecha_caducidad__lt=hoy).exclude(cedula__in=i).order_by('-fecha_registro')

                            if 'g' in request.GET:
                                grupoid = request.GET['g']
                                data['grupo'] = Grupo.objects.get(pk=request.GET['g'])
                                data['grupoid'] = int(grupoid) if grupoid else ""
                                preinscritos = PreInscripcion.objects.filter(carrera__grupocoordinadorcarrera__group__in=request.user.groups.all(), grupo=data['grupo'],inscrito=False, fecha_caducidad__gte=hoy).distinct().order_by('-fecha_registro')
                            # else:
                            #     preinscritos = PreInscripcion.objects.filter(carrera__grupocoordinadorcarrera__group__in=request.user.groups.all()).distinct()

                            paging = MiPaginador(preinscritos, 30)
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
                            data['search'] = search if search else ""
                            data['preinscritos'] = page.object_list
                            data['utiliza_grupos_alumnos'] = UTILIZA_GRUPOS_ALUMNOS
                            data['reporte_ficha_id'] = REPORTE_CERTIFICADO_INSCRIPCION
                            data['clave'] = DEFAULT_PASSWORD
                            data['usafichamedica'] = UTILIZA_FICHA_MEDICA
                            data['centroexterno'] = CENTRO_EXTERNO
                            data['matriculalibre'] = MODELO_EVALUACION==EVALUACION_TES
                            data['grupos'] = Grupo.objects.all().order_by('nombre')
                            return render(request ,"seguimiento/preinscripcionesbs.html" ,  data)

                        except:
                            return HttpResponseRedirect("/seguimiento")
                elif action=='incidenciaadminis':

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
                    if search:
                        incidenciaadministrativo = IncidenciaAdministrativo.objects.filter(nombre__icontains=search).order_by('id')
                    else:
                        incidenciaadministrativo = IncidenciaAdministrativo.objects.filter(finalizado=False).order_by('id')

                    if finalizados:
                        incidenciaadministrativo = IncidenciaAdministrativo.objects.filter(finalizado = True).order_by('-fechafinaliza','id')
                    if todos:
                        incidenciaadministrativo = IncidenciaAdministrativo.objects.filter(finalizado=False).order_by('id')


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
                    data['paging'] = paging
                    data['rangospaging'] = paging.rangos_paginado(p)
                    data['page'] = page
                    data['search'] = search if search else ""
                    data['todos'] = todos if todos else ""
                    data['finalizados'] = finalizados if finalizados else ""
                    data['incidenciaadministrativo'] = page.object_list
                    if 'error' in request.GET:
                        data['error'] = request.GET['error']
                    data['asistasuntoestudiant'] = AsistAsuntoEstudiant.objects.filter(estado=True)
                    return render(request ,"asuntoestudiantil/incidenciadministrativa.html" ,  data)
                elif action == "solicitudes":
                    if 'cerra' in request.GET:
                        solicitudes = SolicitudSecretariaDocente.objects.filter(cerrada=True).order_by('-fecha','-hora')
                        data['cerrado'] = 'cerra'
                    else:
                        solicitudes = SolicitudSecretariaDocente.objects.filter(cerrada=False).order_by('-fecha','-hora')
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

                    if 'error' in request.GET:
                        data['error'] = request.GET['error']
                    return render(request ,"solicitudes/solicitudesbs.html" ,  data)
            else:
                return render(request ,"seguimiento/menu.html" ,  data)

        except Exception as ex:
            return HttpResponseRedirect("/?info="+str(ex))