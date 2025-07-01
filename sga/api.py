import csv
import json
import os
import string
import urllib

from django.db.models import F
from django.db.models.query_utils import Q
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.contrib.auth import authenticate, logout
from django.contrib.auth.models import Group, User
from django.contrib.contenttypes.models import ContentType
from django.db import connection, transaction
from django.db.models.aggregates import Sum
from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.utils.encoding import force_str
import psycopg2
import requests
from suds.client import Client
import xlwt
from bib.models import Documento
from settings import MODELO_EVALUACION, EVALUACION_ITB, VALIDAR_ASISTENCIAS, SEXO_MASCULINO, SEXO_FEMENINO, \
    GRUPO_USUARIOS_IMPRESION, \
    TIPO_RETENCION_IVA, NOTA_PARA_APROBAR, TIPO_NC_ANULACION, TIPO_NC_DEVOLUCION, DEFAULT_PASSWORD, EMAIL_ACTIVE, \
    VALOR_VINCULACION, \
    ADMINISTRATIVOS_GROUP_ID, PROFESORES_GROUP_ID, ALUMNOS_GROUP_ID, SISTEMAS_GROUP_ID, CAJA_CONGRESO, \
    FACTURACION_ELECTRONICA, \
    USER_CONGRESO, CAJA_ONLINE, URL_PRE_INSCRIPCION, RUTA_PRE_INSCRIPCION, PROMOCION_GYM, SITE_ROOT, GESTION_DESCUENTO, \
    GESTION_INDIVIDUAL, MEDIA_ROOT, NEW_PASSWORD, ACTIVA_ADD_EDIT_AD, RUBRO_TIPO_CURSOS, DATABASES, CAJA_REFERIDO, \
    ESPECIE_JUSTIFICA_FALTA_AU, PORCENTAJE_DESCUENTO, PORCENTAJE_DESCUENTO15, MULTA24H, MULTA48H, TIPOSEGMENTO_PRACT, \
    ASIST_PARA_APROBAR, \
    NOTA_ESTADO_EN_CURSO, NOTA_ESTADO_SUPLETORIO, NOTA_ESTADO_REPROBADO, NOTA_ESTADO_DERECHOEXAMEN, \
    NOTA_ESTADO_APROBADO, HABILITA_APLICA_DESCUE, CONSUMIDOR_FINAL, \
    ID_CARRERA_CONGRESO, CAJA_PICHINCHA, TIPO_ESPECIEVALO_PRACPRE, IP_SERVIDOR_API_DIRECTORY, FORMA_PAGO_EFECTIVO, \
    FORMA_PAGO_WESTER, FORMA_PAGO_PACIFICO, FORMA_PAGO_REFERIDO, FORMA_PAGO_PICHINCHA, FORMA_PAGO_PAGOONLINE, \
    FORMA_PAGO_FACILITO, FORMA_PAGO_ELECTRONICO, FORMA_PAGO_DEPOSITO, FORMA_PAGO_TRANSFERENCIA, FORMA_PAGO_CHEQUE, \
    FORMA_PAGO_CHEQUE_POSTFECHADO, FORMA_PAGO_TARJETA_DEB, FORMA_PAGO_TARJETA, FORMA_PAGO_RETENCION, \
    FORMA_PAGO_NOTA_CREDITO, FORMA_PAGO_RECIBOCAJAINSTITUCION, TIPO_OTRO_RUBRO

from sga import number_to_letter
from datetime import datetime, timedelta
from sga.commonviews import ip_client_address, cambio_clave_AD, add_usuario_AD
from sga.docentes import calculate_username
from sga.facturacionelectronica import mail_errores_autorizacion
from sga.finanzas import convertir_fecha
from sga.models import AsistenciaLeccion, Clase, Leccion, Aula, Turno, LeccionGrupo, EvaluacionITB, LugarRecaudacion, Factura, ClienteFactura, Pago, Rubro, Inscripcion, \
    Nivel, Materia, MateriaAsignada, CodigoEvaluacion, LeccionGrupo, AsistenciaLeccion, ChequeProtestado, RubroNotaDebito, Matricula, total_matriculados, Profesor, Impresion, \
    Asignatura, RecordAcademico, HistoricoRecordAcademico, AsignaturaMalla, PrecioMateria, AsignaturaNivelacionCarrera, FacturaCancelada, PagoRetencion, RolPerfilProfesor, \
    NotaCreditoInstitucion,DetallePagoTutoria, Persona, Egresado, Graduado, Grupo, Carrera, Modalidad, TipoAnuncio, Sexo, Discapacidad, DatosPersonaCongresoIns, Sesion, \
    RubroMatricula, SesionCaja, CierreSesionCaja, PagoTarjeta, TipoTarjetaBanco, ProcesadorPagoTarjeta, TipoIncidencia, TipoPersonaCongreso, InscripcionGrupo, \
    RequerimientoCongreso, PagoPymentez, Canton, Provincia, Especialidad, PreInscripcion,ReferidosInscripcion, MensajesEnviado, PromoGym, RubroSeguimiento, DescuentoSeguimiento, \
    RubroOtro, PagosCursoITB, DetallePagosITB, TipoOtroRubro, RetiradoMatricula, ViewEstudiantEmpleo, PagoConduccion,EspecieGrupo, AsistenteDepartamento, RubroEspecieValorada, \
    CoordinacionDepartamento, RecaudacionPichincha, DetalleDescuento, Descuento, ReciboCajaInstitucion, ArchivoPichincha, SolicitudSecretariaDocente, TutorCongreso, TutorMatricula, \
    CuponInscripcion,MultaDocenteMateria,ProfesorMateria, HorarioAsistenteSolicitudes, HorarioPersona, SolicitudPracticas, SolicitudHorarioAsistente, ViewPersonasAdmProAlu, Malla, \
    HistoricoNotasITB, AsistAsuntoEstudiant, ViewInscripcionParaIngles, Absentismo, PersonaAsuntos, SeguimientoAbsentismo, SeguimientoAbsentismoDetalle, DIAS_CHOICES, \
    CategoriaAbsentismo, PagoNotaCreditoInstitucion, PagoReciboCajaInstitucion, DetalleRubrosBeca, FormaDePago, PagoTransferenciaDeposito, PagoCheque, RubroInscripcion, \
    RubroCuota, RubroMateria, RubroActividadExtraCurricular, ReciboPago, EvaluacionAlumno, DetalleEvaluacionAlumno, EjesEvaluacion, PreguntasEvaluacion, RespuestasEjesEvaluacion, EvaluacionDocentePeriodo, DetalleEvaluacionDocente, EvaluacionDirectivoPeriodo, DetalleEvaluacionDirectivo
from sga.pre_inscripciones import email_error, email_error_congreso
from sga.reportes import elimina_tildes
from decimal import Decimal
from sga.tasks import send_html_mail


def reinicia_secuencia(request):
    cursor = connection.cursor()
    cursor.execute("select setval ('sec_serie_especie ',0,true) ")

def representacion_factura_str2(x):
    return fix_factura_str(model_to_dict(x,exclude='fecha'), x)
def fix_factura_str(obj, f):
    obj['fecha'] = f.fecha.strftime("%d-%m-%Y")
    obj['cliente'] = model_to_dict(ClienteFactura.objects.get(pk=obj['cliente']))
    formasdepago = [fix_formadepago_str(x) for x in obj['pagos']]
    pagos = [fix_pago_str(x) for x in obj['pagos']]
    obj['pagos'] = pagos
    obj['enletras'] = number_to_letter.enletras(obj['total'])
    obj['formasdepago'] = formasdepago
    return obj


def abrir_caja(idcaja):
    lugarRecaudacion=LugarRecaudacion.objects.filter(pk=idcaja)[:1].get()
    if not SesionCaja.objects.filter(caja=lugarRecaudacion,fecha=datetime.now().date()).exists():
        sc = SesionCaja(caja=lugarRecaudacion, fecha=datetime.now(), hora=datetime.now().time(),
                        fondo=0,
                        facturaempieza=lugarRecaudacion.numerofact,
                        facturatermina=lugarRecaudacion.numerofact,
                        abierta=True)
        sc.save()
    else:
        if SesionCaja.objects.filter(caja=lugarRecaudacion,fecha=datetime.now().date(),abierta=True).exists():
            sc = SesionCaja.objects.filter(caja=lugarRecaudacion,fecha=datetime.now().date(),abierta=True)[:1].get()
        else:
            return False
    return  sc
def calificaciondocente(request):
    try:
        calificacion=0
        calificacionauto=0
        evaperiodo=EvaluacionDocentePeriodo.objects.filter(finalizado=True).values('profesor__id')
        profesor=Profesor.objects.filter(id__in=evaperiodo)
        # profesor=Profesor.objects.filter(id=279)
        print(profesor.count())
        contadirectivo=0
        for p in profesor:
            evaprofe=EvaluacionDocentePeriodo.objects.filter(profesor=p,finalizado=True)[:1].get()
            if EvaluacionDirectivoPeriodo.objects.filter(evaluaciondocenteperiodo=evaprofe,finalizado=True).exists():
                evaluaciondirectivo=EvaluacionDirectivoPeriodo.objects.filter(evaluaciondocenteperiodo=evaprofe,finalizado=True)[:1].get()
                if DetalleEvaluacionDirectivo.objects.filter(evaluacion=evaluaciondirectivo).exists():
                    if  not p.es_coordinadorperiodo(evaprofe.periodo):
                        detadirectivo = DetalleEvaluacionDirectivo.objects.filter(evaluacion=evaluaciondirectivo).exclude(respuesta__eje__percepcion=True).values('respuesta__eje')
                    else:
                        detadirectivo = DetalleEvaluacionDirectivo.objects.filter(evaluacion=evaluaciondirectivo).values('respuesta__eje')
                    eje = EjesEvaluacion.objects.filter(id__in=detadirectivo)
                    totalmmaximoejedirectivo=0
                    puntajemacimoobtenerdirectivo=0
                    acumuladorespuestadirectivo=0
                    for e in eje:
                        totalpdire = PreguntasEvaluacion.objects.filter(eje=e).order_by('orden').count()
                        totalrdire = RespuestasEjesEvaluacion.objects.filter(eje=e).order_by('-respuesta__puntaje')[:1].get()
                        totalmmaximoejedirectivo=totalpdire*totalrdire.respuesta.puntaje
                        totalmmaximoejedirectivo=Decimal(totalmmaximoejedirectivo).quantize(Decimal(10) ** -0)
                        puntajemacimoobtenerdirectivo=puntajemacimoobtenerdirectivo+totalmmaximoejedirectivo
                        puntajemacimoobtenerdirectivo=Decimal(puntajemacimoobtenerdirectivo).quantize(Decimal(10) ** -0)
                        VRA = 0
                        for det in PreguntasEvaluacion.objects.filter(eje=e).order_by('orden'):
                            for r in DetalleEvaluacionDirectivo.objects.filter(pregunta=det, evaluacion=evaluaciondirectivo):
                                # c = r.cantidad_respuesta_autoeva(evadoc.evaluaciondocente,det,periodo)
                                puntajerespuestadirec = r.respuesta.respuesta.puntaje
                                puntajerespuestadirec=Decimal(puntajerespuestadirec).quantize(Decimal(10) ** -0)
                                acumuladorespuestadirectivo=acumuladorespuestadirectivo+puntajerespuestadirec
                    calificaciondirectivo=(acumuladorespuestadirectivo*45)/puntajemacimoobtenerdirectivo
                    calificaciondirectivo=Decimal(calificaciondirectivo).quantize(Decimal(10) ** -0)
                    # print(calificaciondirectivo)
                    evaprofe.porcentajedirectivo=calificaciondirectivo
                    evaprofe.save()
                    contadirectivo=contadirectivo+1
            if DetalleEvaluacionDocente.objects.filter(evaluacion=evaprofe).exists():
                    detaeva = DetalleEvaluacionDocente.objects.filter(evaluacion=evaprofe).values('respuesta__eje')
                    eje = EjesEvaluacion.objects.filter(id__in=detaeva)
                    totalmmaximoeje=0
                    puntajemacimoobtener=0
                    acumuladorespuesta=0

                    for e in eje:
                        totalp = PreguntasEvaluacion.objects.filter(eje=e).order_by('orden').count()
                        totalr = RespuestasEjesEvaluacion.objects.filter(eje=e).order_by('-respuesta__puntaje')[:1].get()

                        totalmmaximoeje=totalp*totalr.respuesta.puntaje

                        totalmmaximoeje=Decimal(totalmmaximoeje).quantize(Decimal(10) ** -0)

                        puntajemacimoobtener=puntajemacimoobtener+totalmmaximoeje
                        puntajemacimoobtener=Decimal(puntajemacimoobtener).quantize(Decimal(10) ** -0)

                        VRA = 0

                        for det in PreguntasEvaluacion.objects.filter(eje=e).order_by('orden'):

                            for r in DetalleEvaluacionDocente.objects.filter(pregunta=det, evaluacion=evaprofe):

                                # c = r.cantidad_respuesta_autoeva(evadoc.evaluaciondocente,det,periodo)
                                puntajerespuesta = r.respuesta.respuesta.puntaje

                                puntajerespuesta=Decimal(puntajerespuesta).quantize(Decimal(10) ** -0)
                                acumuladorespuesta=acumuladorespuesta+puntajerespuesta

                    calificacionauto=(acumuladorespuesta*25)/puntajemacimoobtener
                    calificacionauto=Decimal(calificacionauto).quantize(Decimal(10) ** -0)
                    evaprofe.porcentajetotal=calificacionauto
                    evaprofe.save()
            if EvaluacionAlumno.objects.filter(profesormateria__profesor=p, finalizado=True, materia__nivel__periodo=evaprofe.periodo).exists():
                evaalumno = EvaluacionAlumno.objects.filter(profesormateria__profesor=p, finalizado=True,materia__nivel__periodo=evaprofe.periodo)[:1].get()

                if DetalleEvaluacionAlumno.objects.filter(evaluacion=evaalumno).exists():
                    detaeva = DetalleEvaluacionAlumno.objects.filter(evaluacion=evaalumno).values('respuesta__eje')
                    eje = EjesEvaluacion.objects.filter(id__in=detaeva)
                    totalmaximo=0
                    tote = EvaluacionAlumno.objects.filter(profesormateria__profesor=p, finalizado=True).count()

                    for e in eje:
                        totalp = PreguntasEvaluacion.objects.filter(eje=e).order_by('orden').count()
                        VRA = 0
                        for det in PreguntasEvaluacion.objects.filter(eje=e).order_by('orden'):
                            totalr = RespuestasEjesEvaluacion.objects.filter(eje=det.eje).count()
                            totalmaximo = tote * totalp * totalr
                            acumulado = 0
                            for r in RespuestasEjesEvaluacion.objects.filter(eje=det.eje):

                                c = r.cantidad_respuestaperiodo_resulatado(det, p, evaprofe.periodo)

                                puntajerespuesta = r.respuesta.puntaje
                                valor = c * puntajerespuesta

                                acumulado = (acumulado + valor)
                            acumuladototal = acumulado / tote

                            VRA = (VRA + acumuladototal)

                        VRAT = VRA * tote
                        calificacion=(VRAT * 25)/totalmaximo
                        calificacion=Decimal(calificacion).quantize(Decimal(10) ** -0)
                        evaprofe.procentajeestudiante=calificacion
                        evaprofe.save()
    except Exception as e:
        print(e)


def cerrar_caja_congreso(request):
    lugarRecaudacion=LugarRecaudacion.objects.filter(pk=CAJA_CONGRESO)[:1].get()
    if SesionCaja.objects.filter(caja=lugarRecaudacion,fecha=datetime.now().date(),abierta=True).exists():
        sc= SesionCaja.objects.filter(caja=lugarRecaudacion,fecha=datetime.now().date(),abierta=True)[:1].get()
        cs = CierreSesionCaja(sesion=sc,
                              enmonedas = (sc.total_sesion_pedagogia()),
                              total = float(sc.total_sesion_pedagogia()),
                              fecha=datetime.now(),
                              hora=datetime.now().time())
        cs.save()

        sc.facturatermina -= 1
        sc.abierta = False
        sc.save()
        return  cs
    return ''

def cerrar_caja_online(request):
    lugarRecaudacion=LugarRecaudacion.objects.filter(pk=CAJA_ONLINE)[:1].get()
    if SesionCaja.objects.filter(caja=lugarRecaudacion,fecha=datetime.now().date(),abierta=True).exists():
        sc= SesionCaja.objects.filter(caja=lugarRecaudacion,fecha=datetime.now().date(),abierta=True)[:1].get()
        cs = CierreSesionCaja(sesion=sc,
                              enmonedas = (sc.total_sesion_pedagogia()),
                              total = float(sc.total_sesion_pedagogia()),
                              fecha=datetime.now(),
                              hora=datetime.now().time())
        cs.save()

        sc.facturatermina -= 1
        sc.abierta = False
        sc.save()
        return  cs
    return ''

def cerrar_caja_referido(request):
    lugarRecaudacion=LugarRecaudacion.objects.filter(pk=CAJA_REFERIDO)[:1].get()
    if SesionCaja.objects.filter(caja=lugarRecaudacion,fecha=datetime.now().date(),abierta=True).exists():
        sc= SesionCaja.objects.filter(caja=lugarRecaudacion,fecha=datetime.now().date(),abierta=True)[:1].get()
        cs = CierreSesionCaja(sesion=sc,
                              enmonedas = (sc.total_sesion_pedagogia()),
                              total = float(sc.total_sesion_pedagogia()),
                              fecha=datetime.now(),
                              hora=datetime.now().time())
        cs.save()

        sc.facturatermina -= 1
        sc.abierta = False
        sc.save()
        return  cs
    return ''

def cerrar_caja_pichincha(request):
    lugarRecaudacion=LugarRecaudacion.objects.filter(pk=CAJA_PICHINCHA)[:1].get()
    if SesionCaja.objects.filter(caja=lugarRecaudacion,fecha=datetime.now().date(),abierta=True).exists():
        sc= SesionCaja.objects.filter(caja=lugarRecaudacion,fecha=datetime.now().date(),abierta=True)[:1].get()
        cs = CierreSesionCaja(sesion=sc,
                              enmonedas = (sc.total_sesion_pedagogia()),
                              total = float(sc.total_sesion_pedagogia()),
                              fecha=datetime.now(),
                              hora=datetime.now().time())
        cs.save()

        sc.facturatermina -= 1
        sc.abierta = False
        sc.save()
        return  cs
    return ''

def cerrar_cajas_abiertas(request):
    #OCastillo 06-04-2022 cierre de sesiones cajas que hayan dejado abiertas los cajeros en el dia
    cerradas=0
    if SesionCaja.objects.filter(fecha=datetime.now().date(),abierta=True).exclude(caja__id__in=[CAJA_ONLINE,CAJA_REFERIDO,CAJA_PICHINCHA]).exists():
        for sesiones in SesionCaja.objects.filter(fecha=datetime.now().date(),abierta=True).exclude(caja__id__in=[CAJA_ONLINE,CAJA_REFERIDO,CAJA_PICHINCHA]):
            sc= SesionCaja.objects.filter(caja=sesiones.caja,fecha=datetime.now().date(),abierta=True)[:1].get()
            cs = CierreSesionCaja(sesion=sc,
                                  enmonedas = (sc.total_sesion_pedagogia()),
                                  total = float(sc.total_sesion_pedagogia()),
                                  fecha=datetime.now(),
                                  hora=datetime.now().time())
            cs.save()

            sc.facturatermina -= 1
            sc.abierta = False
            sc.save()
            cerradas += 1
        return  cerradas
    return ''


def callback(request):
    print("INICIO CALLBACK ")
    try:
        datos= (request.POST)
        transaccion= json.loads(datos.lists()[0][0])['transaction']
        print(transaccion)
        tarjeta= json.loads(datos.lists()[0][0])['card']
        referencia_dev = transaccion['dev_reference']
        fecha_pay = transaccion['paid_date']
        if int(transaccion['status']) == 1:
            estado = 'success'

        else:
            estado = transaccion['status']
        if transaccion['order_description'] == 'PAGO DE RUBROS CONDUCE':
             print("okconduce")
             if PagoConduccion.objects.filter(pk=int(referencia_dev)).exists():

                pagopy = PagoConduccion.objects.filter(pk=referencia_dev)[:1].get()
                pagopy.estado =estado
                pagopy.monto = transaccion['amount']
                pagopy.codigo_aut = transaccion['authorization_code']
                pagopy.referencia_dev = transaccion['dev_reference']
                pagopy.idref = transaccion['id']
                pagopy.mensaje = transaccion['message']
                pagopy.fecha_pay = fecha_pay
                pagopy.detalle_estado = transaccion['status_detail']
                pagopy.referencia_tran = transaccion['id']
                pagopy.tipo = tarjeta['type']
                pagopy.fecha = datetime.now()
                pagopy.save()
             else:
                pagopy = PagoConduccion(pk=int(referencia_dev),
                                      estado=estado,
                                      monto = transaccion['amount'],
                                      codigo_aut = transaccion['authorization_code'],
                                      referencia_dev = transaccion['dev_reference'],
                                      idref = transaccion['id'],
                                      mensaje = transaccion['message'],
                                      fecha_pay = fecha_pay,
                                      detalle_estado = transaccion['status_detail'],
                                      referencia_tran = transaccion['id'],
                                      tipo = tarjeta['type'],
                                      fecha = datetime.now())
                pagopy.save()

        else:
            print("okitb")
            if PagoPymentez.objects.filter(pk=int(referencia_dev)).exists():
                if PagoPymentez.objects.filter(pk=int(referencia_dev),factura=None).exists():
                    pagopy = PagoPymentez.objects.filter(pk=referencia_dev)[:1].get()
                    pagopy.estado =estado
                    pagopy.monto = transaccion['amount']
                    pagopy.codigo_aut = transaccion['authorization_code']
                    pagopy.referencia_dev = transaccion['dev_reference']
                    pagopy.idref = transaccion['id']
                    pagopy.mensaje = transaccion['message']
                    pagopy.fecha_pay = fecha_pay
                    pagopy.detalle_estado = transaccion['status_detail']
                    pagopy.referencia_tran = transaccion['id']
                    pagopy.tipo = tarjeta['type']
                    pagopy.fecha = datetime.now()
                    pagopy.save()
            else:
                pagopy = PagoPymentez(pk=int(referencia_dev),
                                      estado=transaccion['status'],
                                      monto = transaccion['amount'],
                                      codigo_aut = transaccion['authorization_code'],
                                      referencia_dev = transaccion['dev_reference'],
                                      idref = transaccion['id'],
                                      mensaje = transaccion['message'],
                                      fecha_pay = fecha_pay,
                                      detalle_estado = transaccion['status_detail'],
                                      referencia_tran = transaccion['id'],
                                      tipo = tarjeta['type'],
                                      fecha = datetime.now())
                pagopy.save()

    except Exception as e:
        print(e)
        return HttpResponse(json.dumps({"result":"error"}),content_type="application/json")
    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")

def generarpinchincha(request):
    errores  =[]
    start_time = datetime.now()
    client_address = ip_client_address(request)
    if 'cron' in request.GET:
        print('generarpinchincha '+str(datetime.now().date())+' SE ENVIO CRON EN EL GET')
    print('generarpinchincha '+str(datetime.now().date())+'INGRESO URL GENERA PICHINCHA INICIO '+str(datetime.now())+' IP:'+str(client_address))
    if not ArchivoPichincha.objects.filter(fecha=datetime.now()).exists():
        try:
            matricula =Inscripcion.objects.filter(persona__usuario__is_active=True).exclude(id=CONSUMIDOR_FINAL).exclude(id=69852).exclude(carrera__id=ID_CARRERA_CONGRESO).order_by('persona__apellido1','persona__apellido2','persona__nombres')
            archivow = ArchivoPichincha(fecha=datetime.now(),
                                        fechainicioproceso=datetime.now())
            archivow.save()
            titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
            titulo.font.height = 20*11
            subtitulo = xlwt.easyxf(num_format_str="@")
            # subtitulo.font.height = 20*10
            # style1 = xlwt.easyxf('')
            wb = xlwt.Workbook()
            ws = wb.add_sheet('Hoja1',cell_overwrite_ok=True)
            cont =1
            datos = open(os.path.join(MEDIA_ROOT+'/archivopichincha/', 'registro'+str(datetime.now().date())+'.txt'), 'w')
            for m in matricula:
                try:
                    if not RetiradoMatricula.objects.filter(inscripcion=m,activo=True).exists():
                        fec=datetime.now().date()
                        fec=datetime.now().date()  + timedelta(days=30)
                        tipo=''
                        inden=''
                        nombre=''
                        cont = 0
                        print('generarpinchincha '+str(datetime.now().date())+' '+str(m))

                        if m.persona.cedula or   m.persona.pasaporte:
                            for r in Rubro.objects.filter(inscripcion=m,cancelado=False,fechavence__lte=fec,valor__gt=0).order_by('cancelado','fechavence'):
                                adeuda=0
                                if HABILITA_APLICA_DESCUE:
                                    if r.aplicadescuento(None)[1] > 0:
                                        if r.aplicadescuento(None)[0] >0:
                                            adeuda = str(Decimal(r.aplicadescuento(None)[0]).quantize(Decimal(10) ** -2)).replace(".","")
                                    else:
                                        if r.verifica_adeudado() >0:
                                            adeuda = str(Decimal(r.verifica_adeudado()).quantize(Decimal(10)**-2)).replace(".","")
                                else:
                                    adeuda = str(Decimal(r.adeudado()).quantize(Decimal(10)**-2)).replace(".","")
                                # adeuda= '0001'
                                if m.persona.cedula:
                                    tipo='C'
                                    inden = str(m.persona.cedula)
                                elif   m.persona.pasaporte:
                                    tipo='P'
                                    inden = m.persona.pasaporte
                                try:
                                    rub = elimina_tildes(r.nombre().replace("#",'').replace(".",'').replace("-",''))[:40]
                                except:
                                    rub = 'PAGO DE RUBRO'
                                try:
                                    nombre = str(elimina_tildes(m.persona.nombre_completo()))[:41]
                                except:
                                    nombre = inden
                                datos.write('CO'+'\t'+str(inden)+'\t'+'USD' +'\t'+ str(adeuda)+'\t'+ 'REC' +'\t'+'\t'+'\t'+"S"+str(r.id)+'\t'+str(tipo)+'\t'+str(inden)+'\t'+str(nombre)+'\n')
                except Exception as ex:
                    errores.append(('error al generar el archivo '+ str(m.id) ,str(m.id)))
                    print('generarpinchincha '+str(datetime.now().date())+' '+ str(ex))
                    pass
            datos.close()
            archivow.archivo='registro'+str(datetime.now().date())+'.txt'
            archivow.fechafinproceso = datetime.now()
            archivow.save()
            if errores:
                email_error_congreso(errores,'GENERACION DE ARCHIVO PICHINCHA')
            print('EJECUCION URL GENERA PICHINCHA EJECUTADO FIN '+str(datetime.now())+' Tiempo de Duracion: {}'.format(datetime.now() - start_time))
            return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
        except Exception as ex:
            print('generarpinchincha '+str(datetime.now().date())+' '+str(ex))
            return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")
    print('generarpinchincha '+str(datetime.now().date())+' EJECUCION URL GENERA PICHINCHA FALSE '+str(datetime.now())+' Tiempo de Duracion: {}'.format(datetime.now() - start_time))
    return HttpResponse(json.dumps({"result":'ya esiste archivo'}),content_type="application/json")
@transaction.atomic()

def inscripciones_demo(request):
    sid = transaction.savepoint()
    try:
        print(request.POST)
        datos_demo = requests.post('http://127.0.0.1:8001/api',{'a': 'sga_demo'})
        inscritos = []
        ins = ""
        if datos_demo.status_code==200:
            print('global')
        if ins:
            for i in ins:
                inscritos.append({})
        resultado = {}
        resultado['result'] = "ok"
        resultado['inscritos'] = inscritos
        return HttpResponse(json.dumps(resultado),content_type="application/json")

    except Exception as ex:
        transaction.savepoint_rollback(sid)
        return HttpResponse(json.dumps({"result":"bad","error":str(ex)}), content_type="application/json")

def factura_online(request):
    errores  =[]
    factura=None
    cliente = None
    inscripcion = None
    pago2 = None
    formapago = FormaDePago.objects.get(id=16)
    for pagopy in PagoPymentez.objects.filter(Q(factura=None,estado='success',detalle_estado=3)|Q(factura=None,estado='success',detalle_estado=30)).exclude(anulado=True):
        if datetime.now() > pagopy.fechatransaccion + timedelta(minutes=10):
            sid = transaction.savepoint()
            try:
                b= 0
                if abrir_caja(CAJA_ONLINE):
                    caja = abrir_caja(CAJA_ONLINE)
                    op=0
                    valida = True
                    for r in Rubro.objects.filter(pk__in=pagopy.rubros.split(",")).order_by('fechavence'):
                        inscripcion=r.inscripcion
                        if PagoTarjeta.objects.filter(tipo=TipoTarjetaBanco.objects.filter(alias=pagopy.tipo.upper())[:1].get(), referencia=pagopy.referencia_tran, online=True, poseedor=pagopy.nombre, pagos__in=Pago.objects.filter(rubro=r)).exists():
                            valida = False
                            pt = PagoTarjeta.objects.filter(tipo=TipoTarjetaBanco.objects.filter(alias=pagopy.tipo.upper())[:1].get(), referencia=pagopy.referencia_tran, online=True, poseedor=pagopy.nombre, pagos__in=Pago.objects.filter(rubro=r))[:1].get()
                            factura = pt.pagos.all()[:1].get().dbf_factura()
                            pagopy.factura = factura
                            pagopy.save()
                            break
                        if r.total_pagado() == r.valor:
                            errores.append(('Rubro ya esta facturado pyid: '+ str(pagopy.id) ,str(r.inscripcion.id)))
                            op =1
                            break

                    if op == 0 and valida:
                        try:
                            if ClienteFactura.objects.filter(ruc= pagopy.ruc).exists():
                                cliente = ClienteFactura.objects.filter(ruc=pagopy.ruc)[:1].get()
                                cliente.nombre =elimina_tildes(pagopy.nombre)
                                cliente.direccion =elimina_tildes(pagopy.direccion)
                                cliente.telefono =elimina_tildes(pagopy.telefono)
                                cliente.correo =pagopy.correo
                                if cliente.contrasena == None:
                                    cliente.contrasena =pagopy.ruc
                                    cliente.numcambio = 0
                                cliente.save()
                            else:
                                cliente = ClienteFactura(ruc=pagopy.ruc, nombre=elimina_tildes(pagopy.nombre),
                                    direccion=elimina_tildes(pagopy.direccion), telefono=elimina_tildes(pagopy.telefono),
                                    correo=pagopy.correo,contrasena=pagopy.ruc,numcambio=0)
                                cliente.save()
                        except :
                            cliente = ClienteFactura(ruc=pagopy.ruc, nombre=elimina_tildes(pagopy.nombre),
                                direccion=elimina_tildes(pagopy.direccion), telefono=elimina_tildes(pagopy.telefono),
                                correo=pagopy.correo,contrasena=pagopy.ruc,numcambio=0)
                            cliente.save()

                        if not Factura.objects.filter(numero=caja.caja.puntoventa.strip()+"-"+str(caja.caja.numerofact).zfill(9)).exists():
                            factura = Factura(numero = caja.caja.puntoventa.strip()+"-"+str(caja.caja.numerofact).zfill(9), fecha = datetime.now().date(),
                                                    valida = True, cliente = cliente,
                                                    subtotal = pagopy.monto , iva = 0, total = pagopy.monto, hora=datetime.now().time(),
                                                    impresa=False, caja=caja.caja, estado = '', mensaje = '',dirfactura='')
                            factura.save()

                            tarjetadebito = False

                            tp = PagoTarjeta(tipo=TipoTarjetaBanco.objects.filter(alias=pagopy.tipo.upper())[:1].get(),
                                    poseedor=pagopy.nombre,
                                    valor =pagopy.monto ,
                                    procesadorpago=ProcesadorPagoTarjeta.objects.get(pk=1),
                                    referencia=pagopy.referencia_tran,
                                    tarjetadebito=tarjetadebito,
                                    online=True,
                                    fecha=datetime.now().date())
                            tp.save()
                            promogim = 0
                            monto = float(pagopy.monto)
                            sumaPagos = Decimal(0)
                            for r in Rubro.objects.filter(pk__in=pagopy.rubros.split(",")).order_by('fechavence'):
                                if r.total_pagado() == r.valor:
                                    errores.append(('Rubro ya esta facturado pyid: '+ str(pagopy.id) ,str(r.inscripcion.id)))
                                    b = 1
                                    continue

                                if Decimal(monto) >= Decimal(r.adeudado()):
                                    adeudado = r.adeudado()
                                    monto = monto - r.adeudado()
                                else:
                                    adeudado = monto
                                pago2 = Pago(fecha=datetime.now().date(),
                                                        recibe=caja.caja.persona,
                                                        valor=adeudado,
                                                        rubro=r,
                                                        efectivo=False,
                                                        wester=False,
                                                        sesion=caja,
                                                        electronico=False,
                                                        facilito=False)
                                pago2.save()
                                sumaPagos = Decimal(sumaPagos + Decimal(pago2.valor)).quantize(Decimal(10)**-2)
                                tp.pagos.add(pago2)
                                factura.pagos.add(pago2)
                                if r.adeudado()==0:
                                    if not r.vencido():
                                        if r.es_cuota() or r.es_matricula():
                                            promogim = 1
                                    r.cancelado = True
                                    r.save()
                                    if RubroSeguimiento.objects.filter(rubro=r, estado=True).exists():
                                        rubroseg = RubroSeguimiento.objects.filter(rubro=r, estado=True)[:1].get()
                                        rubroseg.fechapago = datetime.now().date()
                                        rubroseg.save()
                                        seguimiento = True
                            if b == 1:
                                transaction.savepoint_rollback(sid)
                                continue
                            caja.facturatermina= int(caja.caja.numerofact)+1
                            caja.save()
                            factura.total = sumaPagos
                            factura.save()

                            if FACTURACION_ELECTRONICA or caja.caja.numerofact  != None:
                                for luga in LugarRecaudacion.objects.all():
                                    if luga.puntoventa == caja.caja.puntoventa:
                                        luga.numerofact = int(caja.caja.numerofact)+1
                                        luga.save()
                            client_address = ip_client_address(request)

                            # Log de CREACION DE NOTA DE CREDITO INSTITUCIONAL
                            LogEntry.objects.log_action(
                                # user_id         = request.user.pk,
                                user_id         = caja.caja.persona.usuario.pk,
                                content_type_id = ContentType.objects.get_for_model(factura).pk,
                                object_id       = factura.id,
                                object_repr     = force_str(factura),
                                action_flag     = ADDITION,
                                change_message  = 'Adicionada Factura Pagos-Online '+  ' (' + client_address + ')' )
                            try:
                                if pagopy.factura:
                                    transaction.savepoint_rollback(sid)
                                    continue
                                transaction.savepoint_commit(sid)
                                if PROMOCION_GYM:
                                    if promogim:
                                        inicio = datetime.now().date()
                                        fin = datetime.now().date() + timedelta(30)
                                        promo = PromoGym(inscripcion=pagopy.inscripcion,
                                                         inicio=inicio,
                                                         fin=fin,
                                                         factura=factura)
                                        promo.save()
                                if Factura.objects.filter(numero= factura.numero).count()>1:
                                    mail_errores_autorizacion("FACTURA REPETIDA "+DEFAULT_PASSWORD,"Existe mas de una factura repetida verificar en factura PAGO ONLINE",factura.numero)
                                    transaction.savepoint_rollback(sid)
                                    errores.append(('error pago en linea - factura repetida pyid: '+ str(pagopy.id) ,str(r.inscripcion.id)))
                                    continue
                                transaction.savepoint_commit(sid)
                                pagopy.factura = factura
                                pagopy.save()
                                transaction.savepoint_commit(sid)
                                if Decimal(pagopy.monto) > sumaPagos:
                                    valor_rc = Decimal(pagopy.monto) - sumaPagos
                                    rc = ReciboCajaInstitucion(inscripcion=inscripcion,
                                                               motivo='RECIBO GENERADO PAGO EN LINEA',
                                                               sesioncaja=caja,
                                                               fecha=datetime.now().date(),
                                                               hora=datetime.now().time(),
                                                               valorinicial=float(valor_rc),
                                                               formapago=formapago,
                                                               saldo=float(valor_rc))
                                    rc.save()
                                    recibopago = ReciboPago(pago=pago2, recibocaja=rc)
                                    recibopago.save()
                                    pagopy.disponible = False
                                    pagopy.save()
                                # factura.notificacion_pago_online(rubro)
                            except Exception as ex:
                                transaction.savepoint_rollback(sid)
                                errores.append(('error pago en linea pyid: '+ str(ex) ,str(pagopy.inscripcion.id)))
                                continue
                                # errores.append(('Ocurrio un Error.. Intente Nuevamente' + str(ex) ,d['ci']))
                                # email_error_pagoonline(errores,'ONLINE')
                                # return HttpResponse(json.dumps({'codigo':0,'mensaje':'Ocurrio un Error.. Intente Nuevamente' + str(ex)}),content_type="application/json")
                            # return HttpResponse(json.dumps({'codigo':1,'mensaje':'ok'}),content_type="application/json")
                        else:
                            errores.append(('ya existe factura : ' +str(pagopy.id ), str(pagopy.inscripcion.id)))
                            break
                else:
                    transaction.savepoint_rollback(sid)
                    errores.append(('error pago en linea - caja cerrada pyid: ' +str(pagopy.id ), str(pagopy.inscripcion.id)))
                    continue

                    # errores.append(('Factura Repetida' ,d['ci']))
                    # email_error_pagoonline(errores,'ONLINE')
                    # return HttpResponse(json.dumps({'codigo':0,'mensaje':'Factura Repetida'}),content_type="application/json")

            except Exception as ex:
                transaction.savepoint_rollback(sid)
                # if not factura.pagos.exists():
                #     factura.delete()
                errores.append(('error pago en linea - caja cerrada pyid: ' +str(pagopy.id ), str(ex)))
                continue
    if errores:
          email_error_congreso(errores,'PAGO EN LINEA')

def creahorarios(request):
    dia  = datetime.now().isoweekday()
    for a in AsistenteDepartamento.objects.filter(activo=True).exclude(puedereasignar=True):
        try:
            entrada=None
            salida=None
            if dia == 1:
                if HorarioPersona.objects.filter(persona=a.persona).exclude(horalunesent='').exclude(horalunessal='').exists():
                    entrada= HorarioPersona.objects.filter(persona=a.persona).exclude(horalunesent='').exclude(horalunessal='')[:1].get().horalunesent
                    salida= HorarioPersona.objects.filter(persona=a.persona).exclude(horalunesent='').exclude(horalunessal='')[:1].get().horalunessal

            if  dia == 2:
                if HorarioPersona.objects.filter(persona=a.persona).exclude(horamartesent='').exclude(horamartessal='').exists():
                    entrada= HorarioPersona.objects.filter(persona=a.persona).exclude(horamartesent='').exclude(horamartessal='')[:1].get().horamartesent
                    salida= HorarioPersona.objects.filter(persona=a.persona).exclude(horamartesent='').exclude(horamartessal='')[:1].get().horamartessal
            if  dia == 3:
                if HorarioPersona.objects.filter(persona=a.persona).exclude(horamiercolesent='').exclude(horamiercolessal='').exists():
                    entrada= HorarioPersona.objects.filter(persona=a.persona).exclude(horamiercolesent='').exclude(horamiercolessal='')[:1].get().horamiercolesent
                    salida= HorarioPersona.objects.filter(persona=a.persona).exclude(horamiercolesent='').exclude(horamiercolessal='')[:1].get().horamiercolessal
            if  dia == 4:
                if HorarioPersona.objects.filter(persona=a.persona).exclude(horajuevesent='').exclude(horajuevessal='').exists():
                    entrada= HorarioPersona.objects.filter(persona=a.persona).exclude(horajuevesent='').exclude(horajuevessal='')[:1].get().horajuevesent
                    salida= HorarioPersona.objects.filter(persona=a.persona).exclude(horajuevesent='').exclude(horajuevessal='')[:1].get().horajuevessal
            if  dia == 5:
                if HorarioPersona.objects.filter(persona=a.persona).exclude(horaviernesent='').exclude(horaviernessal='').exists():
                    entrada= HorarioPersona.objects.filter(persona=a.persona).exclude(horaviernesent='').exclude(horaviernessal='')[:1].get().horaviernesent
                    salida= HorarioPersona.objects.filter(persona=a.persona).exclude(horaviernesent='').exclude(horaviernessal='')[:1].get().horaviernessal
            if  dia == 6:
                if HorarioPersona.objects.filter(persona=a.persona).exclude(horasabadoent='').exclude(horasabadosal='').exists():
                    entrada= HorarioPersona.objects.filter(persona=a.persona).exclude(horasabadoent='').exclude(horasabadosal='')[:1].get().horasabadoent
                    salida= HorarioPersona.objects.filter(persona=a.persona).exclude(horasabadoent='').exclude(horasabadosal='')[:1].get().horasabadosal

            if dia == 7:
                if HorarioPersona.objects.filter(persona=a.persona).exclude(horadomingoent='').exclude(horadomingosal='').exists():
                    entrada= HorarioPersona.objects.filter(persona=a.persona).exclude(horadomingoent='').exclude(horadomingosal='')[:1].get().horadomingoent
                    salida= HorarioPersona.objects.filter(persona=a.persona).exclude(horadomingoent='').exclude(horadomingosal='')[:1].get().horadomingosal

            if HorarioPersona.objects.filter(persona=a.persona).exclude(horaentrada='').exclude(horasalida='').exists() and dia != 6 and dia != 7 :
                entrada= HorarioPersona.objects.filter(persona=a.persona).exclude(horaentrada='').exclude(horasalida='')[:1].get().horaentrada
                salida= HorarioPersona.objects.filter(persona=a.persona).exclude(horaentrada='').exclude(horasalida='')[:1].get().horasalida
            if entrada and salida:
                if not HorarioAsistenteSolicitudes.objects.filter(fecha=datetime.now().date(),usuario=a.persona.usuario).exists():
                    horarioasistente =HorarioAsistenteSolicitudes( horainicio = entrada,
                                                                   horafin=salida,
                                                                   usuario=a.persona.usuario,
                                                                   fecha=datetime.now().date(),
                                                                   fechaingreso=datetime.now())
                    horarioasistente.save()
                    print('ok')
        except Exception as e:
            print(e)


def asigna_asistentehorario(request):
    try:
        for s in SolicitudHorarioAsistente.objects.filter(horario=None):
            solicitudpractica = SolicitudPracticas.objects.get(id=s.solicitud.id)
            if EspecieGrupo.objects.filter(tipoe__id=TIPO_ESPECIEVALO_PRACPRE).exists():

                iddepartamentoesp = EspecieGrupo.objects.filter(tipoe__id=TIPO_ESPECIEVALO_PRACPRE).values('departamento').distinct('departamento')
                iddepartamento =  CoordinacionDepartamento.objects.filter(departamento__id__in = iddepartamentoesp,coordinacion__carrera=solicitudpractica.matricula.inscripcion.carrera).values('departamento').distinct('departamento')
                idusuario = AsistenteDepartamento.objects.filter(departamento__id__in=iddepartamento,activo=True).values('persona__usuario').distinct('persona__usuario')
                horarioasis = ''
                mensaje = 'El escenario de practica fue enviado, pronto un asistente le antendera'
                if HorarioAsistenteSolicitudes.objects.filter(fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time(),usuario__id__in=idusuario).exists():
                    horarioasis = HorarioAsistenteSolicitudes.objects.filter(fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time(),usuario__id__in=idusuario).exclude(nolabora=True).order_by('sinatender')[:1].get()
                    asistenten = AsistenteDepartamento.objects.filter(persona__usuario=horarioasis.usuario,activo=True)[:1].get()
                    mensaje = 'El escenario de practica fue enviado, el asistente '+ str(asistenten.persona.nombre_completo())+' lo atendera'

                if horarioasis:
                    s.horario = horarioasis
                    horarioasis.sinatender = horarioasis.sinatender + 1
                    horarioasis.save()
                    s.fechaasig = datetime.now()
                    s.save()
                    if EMAIL_ACTIVE:
                        s.mail_escenariohorarioasis(request.user)
            else:
                print('No se puede ingresar el escenario contactese con el administrador')
    except Exception as e:
        print(e)
def asigna_especies(request):
        listaespecies=[]
        listasolicitudes=[]
        for e in EspecieGrupo.objects.filter(tipoe__es_especie=True):
            try:
                if RubroEspecieValorada.objects.filter(aplicada=False,tipoespecie=e.tipoe,usrasig=None,usuario=None,tipoespecie__coordinadores=False,rubro__fecha__gte='2020-08-01',rubro__cancelado=True).exists():
                    for coor in CoordinacionDepartamento.objects.filter(departamento = e.departamento):
                        for c in coor.coordinacion.carrera.all():
                            asistentes=None
                            for r in RubroEspecieValorada.objects.filter(aplicada=False,tipoespecie=e.tipoe,rubro__inscripcion__carrera=c,usrasig=None,usuario=None,tipoespecie__coordinadores=False,rubro__fecha__gte='2020-08-01',rubro__cancelado=True):
                                if r.es_online():
                                    if not r.departamento:
                                        if HorarioAsistenteSolicitudes.objects.filter(fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time()).exists():
                                             horarioasis = HorarioAsistenteSolicitudes.objects.filter(fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time()).values('usuario')
                                             asistentes = AsistenteDepartamento.objects.filter(departamento=e.departamento,persona__usuario__id__in=horarioasis,activo=True).exclude(puedereasignar=True).order_by('cantidad')
                                    else:
                                        if HorarioAsistenteSolicitudes.objects.filter(fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time()).exists():
                                             horarioasis = HorarioAsistenteSolicitudes.objects.filter(fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time()).values('usuario')
                                             asistentes = AsistenteDepartamento.objects.filter(departamento=r.departamento,persona__usuario__id__in=horarioasis,activo=True).exclude(puedereasignar=True).order_by('cantidad')
                                    if asistentes:
                                        for asis in asistentes:
                                            r.usrasig = asis.persona.usuario
                                            r.departamento = asis.departamento
                                            asis.cantidad =asis.cantidad +1
                                            r.fechaasigna = datetime.now()
                                            r.save()
                                            asis.save()
                                            if not asis.persona.emailinst in listaespecies:
                                                listaespecies.append(asis.persona.emailinst)
                                            break

            except Exception as e:
                print(e)

        if listaespecies:
            try:
                 hoy = datetime.now().today()
                 contenido = "  Tramites Asignados"
                 descripcion = "Ud. tiene tramites por atender"
                 send_html_mail(contenido,
                    "emails/notificacion_tramites_adm.html", {'fecha': hoy,'contenido': contenido,'descripcion':descripcion,'opcion':'1'},listaespecies)
            except Exception as e:
                print(e)
                pass
        for e in EspecieGrupo.objects.filter(tipoe__es_especie=False):
            try:
                if SolicitudSecretariaDocente.objects.filter(solicitudestudiante__tipoe=e.tipoe,personaasignada=None,fecha__gte='2020-08-01').exists():
                    for coor in CoordinacionDepartamento.objects.filter(departamento = e.departamento):
                        for c in coor.coordinacion.carrera.all():
                            asistentes=None
                            for r in SolicitudSecretariaDocente.objects.filter(solicitudestudiante__tipoe=e.tipoe,solicitudestudiante__inscripcion__carrera=c,personaasignada=None,solicitudestudiante__tipoe__coordinadores=False,fecha__gte='2020-08-01'):
                                if not r.departamento:
                                    depar = e.departamento
                                else:
                                    depar= r.departamento
                                if depar.id== 27:
                                    cajeros = SesionCaja.objects.filter(abierta=True).values('caja__persona')
                                    # asistentes  = AsistenteDepartamento.objects.filter(departamento=depar,persona__id__in=cajeros).exclude(puedereasignar=True).order_by('cantidadsol')
                                    if HorarioAsistenteSolicitudes.objects.filter(fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time()).exists():
                                         horarioasis = HorarioAsistenteSolicitudes.objects.filter(fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time()).values('usuario')
                                         asistentes = AsistenteDepartamento.objects.filter(departamento=depar,persona__usuario__id__in=horarioasis,persona__id__in=cajeros,activo=True).exclude(puedereasignar=True).order_by('cantidadsol')

                                else:
                                    # asistentes = AsistenteDepartamento.objects.filter(departamento=e.departamento).exclude(puedereasignar=True).order_by('cantidadsol')
                                    # if not r.departamento:
                                    if HorarioAsistenteSolicitudes.objects.filter(fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time()).exists():
                                         horarioasis = HorarioAsistenteSolicitudes.objects.filter(fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time()).values('usuario')
                                         asistentes = AsistenteDepartamento.objects.filter(departamento=depar,persona__usuario__id__in=horarioasis,activo=True).exclude(puedereasignar=True).order_by('cantidadsol')


                                for asis in asistentes:
                                    asis.cantidadsol =asis.cantidadsol +1
                                    r.usuario = asis.persona.usuario
                                    r.personaasignada =asis.persona
                                    r.asignado=True
                                    r.fechaasignacion = datetime.now()
                                    r.departamento = asis.departamento
                                    r.usuarioasigna=asis.persona.usuario
                                    r.save()
                                    asis.save()
                                    if not asis.persona.emailinst in  listasolicitudes:
                                        listasolicitudes.append(asis.persona.emailinst)
                                    break

            except Exception as e:
                print(e)
        if listasolicitudes:
            try:
                 hoy = datetime.now().today()
                 contenido = "  Tramites Asignados"
                 descripcion = "Ud. tiene tramites por atender"
                 send_html_mail(contenido,
                    "emails/notificacion_solicitud_adm.html", {'fecha': hoy,'contenido': contenido,'descripcion':descripcion,'opcion':'1'},listasolicitudes)
            except Exception as e:
                print((e))
                pass

def cierra_clasesabiertas(request):
        #OCastillo 03-07-2023 para cerrar clases que docentes hayan dejado abiertas
        hoy = datetime.now().date()
        for l in LeccionGrupo.objects.filter(abierta=True,fecha__gte=hoy).order_by('id'):
        # for l in LeccionGrupo.objects.filter(id__in=[470254,470299,470329],abierta=True):
            print(l)
            horaaproxsalida=datetime.now().time()
            salidasistema= datetime.combine(hoy, datetime.now().time())
            terminaturno=datetime.combine(l.fecha, l.turno.termina)
            horasturno= ((datetime.combine(l.fecha,l.turno.termina) - datetime.combine (l.fecha, l.turno.comienza)).seconds)/60
            if l.horaentrada<l.turno.comienza:
                fechaentrada=datetime.combine(l.fecha,l.turno.comienza)
            else:
                fechaentrada=datetime.combine(l.fecha,l.horaentrada)

            fechasalida=datetime.combine(hoy,horaaproxsalida)

            minutosleccion = ((fechasalida-fechaentrada).seconds)/60
            minutoscierre=(horasturno-minutosleccion)

            if  salidasistema > terminaturno:
                minutoscierresistema=((salidasistema-terminaturno).seconds)/60
            else:
                minutoscierresistema=0

            if minutoscierresistema >=15:
                l.fechasalida=hoy
                l.horasalida=horaaproxsalida
                l.cierresistema=True
                l.save()

                l.minutosleccion=minutosleccion
                l.minutoscierre=minutoscierre
                l.abierta=False
                l.save()

                for leccion in l.lecciones.all():
                    leccion.abierta = False
                    leccion.horasalida = horaaproxsalida
                    leccion.save()

                client_address = ip_client_address(request)
                # Log de CERRAR CLASE POR MEDIO DEL SISTEMA
                LogEntry.objects.log_action(
                    # user_id         = request.user.pk,
                    user_id         = l.profesor.persona.usuario.pk,
                    content_type_id = ContentType.objects.get_for_model(l).pk,
                    object_id       = l.id,
                    object_repr     = force_str(l),
                    action_flag     = ADDITION,
                    change_message  = 'Clase Cerrada por el Sistema Academico (' + client_address + ')' )

def inscribircongreso(request):
    errores =[]
    consulta = requests.post('http://api.pedagogia.edu.ec',{'action': 'consulta', 'pagado': '0','codigo':'6TO CONGRESO DE PEDAGOGIA'},verify=False)
    if consulta.status_code==200:
        datos = consulta.json()
        for d in datos['response']['inscripcion']:
            canton = None
            provincia = None
            tipoanuncio = None
            colegio = None
            inscripcion = None

            try:
                if Carrera.objects.filter(nombre=d['cnombre'].upper()).exists():
                    carrera = Carrera.objects.filter(nombre=d['cnombre'].upper())[:1].get()
                else:
                    carrera = Carrera.objects.all()[:1].get()

                if Modalidad.objects.filter(nombre=d['tipo'].upper()).exists():
                    modalidad= Modalidad.objects.filter(nombre=d['tipo'].upper())[:1].get()
                else:
                    modalidad = Modalidad.objects.all()[:1].get()


                if TipoAnuncio.objects.filter(pk=13).exists():
                    tipoanuncio= TipoAnuncio.objects.filter(pk=13)[:1].get()

                if Grupo.objects.filter(nombre=d['codigo'].upper()).exists():
                    grupo= Grupo.objects.filter(nombre=d['codigo'].upper())[:1].get()
                    seccion = grupo.sesion
                else:
                    grupo = Grupo.objects.all()[:1].get()
                    seccion = Sesion.objects.all()[:1].get()

                if Sexo.objects.filter(nombre=d['sexo'].upper()).exists():
                    sexo= Sexo.objects.filter(nombre=d['sexo'].upper())[:1].get()
                else:
                    sexo = Sexo.objects.all()[:1].get()


                valor = Decimal(d['valor'])



                cedula = (d['ci'].lstrip().strip())
                hoy = str(datetime.date(datetime.now()))
                # caducidad = (row[20])
                if not PreInscripcion.objects.filter(cedula=cedula,carrera=carrera).exists():
                    preinscripcion = PreInscripcion(
                                    tipodoc = d['tipodni'],
                                    carrera=carrera,
                                    modalidad=modalidad,
                                    seccion=seccion,
                                    grupo=grupo,
                                    # inicio_clases=(row[4]),
                                    nombres=elimina_tildes(d['nombre']),
                                    apellido1=elimina_tildes(d['paterno']),
                                    apellido2=elimina_tildes(d['materno']),
                                    cedula=cedula,
                                    fecha_registro = d['creado'],
                                    nacimiento=d['fecha'],
                                    email=(d['email'].lower()),
                                    sexo=sexo,
                                    telefono=d['telefono'],
                                    celular=d['cell'],
                                    fecha_caducidad=d['vence'],
                                    calleprincipal=d['direccion'],
                                    valor=valor,
                                    tipoanuncio=tipoanuncio)
                else:
                    preinscripcion=PreInscripcion.objects.filter(cedula=cedula,carrera=carrera)[:1].get()
                    preinscripcion.carrera=carrera
                    preinscripcion.modalidad=modalidad
                    preinscripcion.seccion=seccion
                    preinscripcion.grupo=grupo
                    preinscripcion.nombres=d['nombre']
                    preinscripcion.tipodoc=d['tipodni']
                    preinscripcion.apellido1=d['paterno']
                    preinscripcion.apellido2=d['materno']
                    preinscripcion.cedula=cedula
                    preinscripcion.email=(d['email'].lower())
                    preinscripcion.sexo=sexo
                    preinscripcion.telefono=d['telefono']
                    preinscripcion.celular=d['cell']
                    preinscripcion.fecha_caducidad=d['vence']
                    preinscripcion.valor=valor
                    preinscripcion.fecha_registro=d['creado']
                    preinscripcion.calleprincipal=d['direccion']
                    preinscripcion.tipoanuncio=tipoanuncio
                preinscripcion.save()

                if DatosPersonaCongresoIns.objects.filter(preinscripcion=preinscripcion,grupo=preinscripcion.grupo,inscripcion=None).exists():
                    DatosPersonaCongresoIns.objects.filter(preinscripcion=preinscripcion,grupo=preinscripcion.grupo,inscripcion=None).delete()
                for part in d['participa'].split(','):
                    try:
                        partid = int(part)
                    except:
                        partid =0

                    if TipoPersonaCongreso.objects.filter(pk=partid).exists():
                        tipopersona = TipoPersonaCongreso.objects.filter(pk=partid)[:1].get()
                        if not DatosPersonaCongresoIns.objects.filter(preinscripcion=preinscripcion,tipopersona=tipopersona,grupo=preinscripcion.grupo).exists():
                            personains = DatosPersonaCongresoIns(preinscripcion=preinscripcion,
                                                           tipopersona=tipopersona,
                                                           grupo=preinscripcion.grupo)
                            personains.save()

                for dis in d['discapacidad'].split(','):
                    try:
                        disid = int(dis)
                    except:
                        disid =0
                    if Discapacidad.objects.filter(pk=disid).exists():
                        discapacidad = Discapacidad.objects.filter(pk=disid)[:1].get()
                        if not DatosPersonaCongresoIns.objects.filter(preinscripcion=preinscripcion,tipodiscapacidad=discapacidad,grupo=preinscripcion.grupo).exists():
                            personains = DatosPersonaCongresoIns(preinscripcion=preinscripcion,
                                                           tipodiscapacidad=discapacidad,
                                                           grupo=preinscripcion.grupo)
                            personains.save()
                for r in d['requerimiento'].split(','):
                    try:
                        rid = int(r)
                    except:
                        rid=0
                    if RequerimientoCongreso.objects.filter(pk=rid).exists():
                        requerimiento = RequerimientoCongreso.objects.filter(pk=rid)[:1].get()
                        if not DatosPersonaCongresoIns.objects.filter(preinscripcion=preinscripcion,requerimiento=requerimiento,grupo=preinscripcion.grupo).exists():
                            personains = DatosPersonaCongresoIns(preinscripcion=preinscripcion,
                                                           requerimiento=requerimiento,
                                                           grupo=preinscripcion.grupo)
                            personains.save()
                inscripciones=''
                if d['tipodni'] == 'c':
                    if Inscripcion.objects.filter(persona__cedula=preinscripcion.cedula).exists():
                        inscripciones = Inscripcion.objects.filter(persona__cedula=preinscripcion.cedula)
                if d['tipodni'] == 'p':
                        if Inscripcion.objects.filter(persona__pasaporte=preinscripcion.cedula).exists():
                            inscripciones = Inscripcion.objects.filter(persona__pasaporte=preinscripcion.cedula)
                if inscripciones:
                    for i in inscripciones:
                        for ic in i.inscripciongrupo_set.all():
                            if ic.grupo.carrera == preinscripcion.grupo.carrera:
                                ic.grupo = preinscripcion.grupo
                                ic.save()
                                inscripcion = i
                                preinscripcion.inscrito=True
                                preinscripcion.save()

                    preinscripcion.save()
                    fechacaducidad = datetime(int(preinscripcion.fecha_caducidad.split('-')[0]),int(preinscripcion.fecha_caducidad.split('-')[1]), int(preinscripcion.fecha_caducidad.split('-')[2]))
                    if fechacaducidad.date() >= datetime.now().date() :
                        if inscripcion:
                            if d['cupon'] != '':
                                if not CuponInscripcion.objects.filter(inscripcion=inscripcion,grupo=grupo):
                                    cupon = CuponInscripcion(inscripcion=inscripcion,
                                                             grupo=grupo,
                                                             cupon= d['cupon'] ,
                                                             descripcion=d['cod_desc'],
                                                             cuponalias=d['cod_alias'],
                                                             valor=d['cod_valor'])
                                    cupon.save()
                            if not inscripcion.matriculado():
                                try:

                                    nivel=Nivel.objects.filter(grupo=grupo)[:1].get()
                                    inscripcion.matricular_pedagogia(nivel)
                                    inscripcion.correo_congreo(grupo)
                                except Exception as e:
                                    errores.append((e,d['ci']))
                                    pass
                    else:
                        if not preinscripcion.enviocorreo:
                            if inscripcion:
                                if d['cupon'] != '':
                                    if not CuponInscripcion.objects.filter(inscripcion=inscripcion,grupo=grupo):
                                        cupon = CuponInscripcion(inscripcion=inscripcion,
                                                                 grupo=grupo,
                                                                 cupon= d['cupon'] ,
                                                                 descripcion=d['cod_desc'],
                                                                 cuponalias=d['cod_alias'],
                                                                 valor=d['cod_valor'])
                                        cupon.save()
                                if not inscripcion.matriculado():
                                    print("enviar correo")
                                    preinscripcion.correo_aviso()
                                    preinscripcion.enviocorreo=True
                                    preinscripcion.save()

                else:
                    fechacaducidad = datetime(int(preinscripcion.fecha_caducidad.split('-')[0]),int(preinscripcion.fecha_caducidad.split('-')[1]), int(preinscripcion.fecha_caducidad.split('-')[2]))
                    if fechacaducidad.date() >= datetime.now().date() :
                        extranjero=False
                        pasaporte=''
                        cedula=''
                        if preinscripcion.tipodoc =='p':
                            extranjero=True
                            pasaporte=preinscripcion.cedula
                        else:
                            cedula=preinscripcion.cedula
                        persona = Persona(nombres=elimina_tildes(d['nombre']),
                                            apellido1= elimina_tildes(d['paterno']),
                                            apellido2=elimina_tildes(d['materno']),
                                            extranjero=extranjero,
                                            cedula=cedula,
                                            pasaporte=pasaporte,
                                            nacimiento=d['fecha'],
                                            sexo=sexo,
                                            direccion=d['direccion'],
                                            telefono=d['cell'],
                                            telefono_conv=d['telefono'],
                                            email=(d['email'].lower()))
                        persona.save()
                        username = calculate_username(persona)
                        password = DEFAULT_PASSWORD
                        user = User.objects.create_user(username, persona.email, password)
                        user.save()
                        persona.usuario = user
                        persona.save()
                        usuariocon = User.objects.get(pk=USER_CONGRESO)
                        inscripcion = Inscripcion(persona=persona,
                                                fecha = datetime.now(),
                                                carrera=grupo.carrera,
                                                descuentoporcent=0,
                                                modalidad=grupo.modalidad,
                                                sesion=grupo.sesion,
                                                identificador='',
                                                tienediscapacidad=False,
                                                doblematricula=False,
                                                observacion="INSCRIPCION AUTOMATICA",
                                                anuncio=tipoanuncio,
                                                user=usuariocon )
                        # inscripcion.save()
                        i = Inscripcion.objects.latest('id') if Inscripcion.objects.exists() else None
                        if i:
                            inscripcion.numerom = i.numerom + 1
                        else:
                            inscripcion.numerom = 1
                        inscripcion.save()
                        if not InscripcionGrupo.objects.filter(inscripcion=inscripcion, grupo=grupo, activo=True).exists():
                            ig = InscripcionGrupo(inscripcion=inscripcion, grupo=grupo, activo=True)
                            ig.save()
                        else:
                            ig= InscripcionGrupo.objects.filter(inscripcion=inscripcion,activo=True)[:1].get()
                            ig.grupo=grupo
                            ig.save()
                        if inscripcion:
                            if d['cupon'] != '':
                                if not CuponInscripcion.objects.filter(inscripcion=inscripcion,grupo=grupo):
                                    cupon = CuponInscripcion(inscripcion=inscripcion,
                                                             grupo=grupo,
                                                             cupon= d['cupon'] ,
                                                             descripcion=d['cod_desc'],
                                                             cuponalias=d['cod_alias'],
                                                             valor=d['cod_valor'])
                                    cupon.save()
                            if not inscripcion.matriculado():
                                try:

                                    nivel=Nivel.objects.filter(grupo=grupo)[:1].get()
                                    inscripcion.matricular_pedagogia(nivel)
                                    inscripcion.correo_congreo(grupo)
                                except Exception as e:
                                    errores.append((e,d['ci']))
                                    pass
                    else:
                        if not preinscripcion.enviocorreo:
                            if inscripcion:
                                if d['cupon'] != '':
                                    if not CuponInscripcion.objects.filter(inscripcion=inscripcion,grupo=grupo):
                                        cupon = CuponInscripcion(inscripcion=inscripcion,
                                                                 grupo=grupo,
                                                                 cupon= d['cupon'] ,
                                                                 descripcion=d['cod_desc'],
                                                                 cuponalias=d['cod_alias'],
                                                                 valor=d['cod_valor'])
                                        cupon.save()
                                if not inscripcion.matriculado():
                                    print("enviar correo")
                                    preinscripcion.correo_aviso()
                                    preinscripcion.enviocorreo=True
                                    preinscripcion.save()




            except Exception as e:
                errores.append((e,d['ci']))
    if errores:
          email_error_congreso(errores,'PREINSCRIPCION CONGRESO')
    return HttpResponse(json.dumps({'mensaje':'ok'}),content_type="application/json")
@transaction.atomic()
def factura_pichincha(request):
    errores  =[]
    for pagop in RecaudacionPichincha.objects.filter(archivo__gestionado=False,factura=None):
        sid = transaction.savepoint()
        try:
            b= 0
            if abrir_caja(CAJA_ONLINE):
                caja = abrir_caja(CAJA_ONLINE)
                try:
                    cliente = ClienteFactura.objects.filter(ruc=pagop.numeroidentificacion)[:1].get()
                    cliente.nombre = pagop.cuenta.inscripcion.persona.nombre_completo()
                    cliente.direccion =pagop.cuenta.inscripcion.persona.direccion
                    cliente.telefono =pagop.cuenta.inscripcion.persona.telefono
                    cliente.correo =pagop.cuenta.inscripcion.persona.emailinst
                    if cliente.contrasena == None:
                        cliente.contrasena =pagop.numeroidentificacion
                        cliente.numcambio = 0
                    cliente.save()
                except :
                    if not ClienteFactura.objects.filter(ruc=pagop.numeroidentificacion).exists():
                        cliente = ClienteFactura(ruc=pagop.numeroidentificacion, nombre=pagop.cuenta.inscripcion.persona.nombre_completo(),
                            direccion=pagop.cuenta.inscripcion.persona.direccion, telefono=pagop.cuenta.inscripcion.persona.telefono,
                            correo=pagop.cuenta.inscripcion.persona.emailinst,contrasena=pagop.numeroidentificacion,numcambio=0)
                        cliente.save()
                    else:
                        cliente = ClienteFactura.objects.filter(ruc=pagop.numeroidentificacion)[:1].get()

                if not Factura.objects.filter(numero=caja.caja.puntoventa.strip()+"-"+str(caja.caja.numerofact).zfill(9)).exists():
                    factura = Factura(numero = caja.caja.puntoventa.strip()+"-"+str(caja.caja.numerofact).zfill(9), fecha = datetime.now().date(),
                                            valida = True, cliente = cliente, hora=datetime.now().time(),
                                            subtotal = Decimal(pagop.valorprocesado)  , iva = 0, total = Decimal(pagop.valorprocesado) ,
                                            impresa=False, caja=caja.caja, estado = '', mensaje = '',dirfactura='')
                    factura.save()


                    monto = float(Decimal(pagop.valorprocesado))
                    r = pagop.cuenta
                    if r.total_pagado() == r.valor:
                        transaction.savepoint_rollback(sid)
                        errores.append(('Rubro ya esta facturado pyid: '+ str(pagop.id) ,elimina_tildes(pagop.cuenta.inscripcion.persona.nombre_completo())))
                        b = 1
                        continue

                    if Decimal(monto) >= Decimal(r.adeudado()):
                        adeudado = r.adeudado()
                        monto = monto - r.adeudado()
                    else:
                        adeudado = monto

                    t = pagop.cuenta
                    if r.aplicadescuento(convertir_fecha(pagop.fechaproceso).date())[1]:

                        valor,aplicanivcut,valdescuento,porcentajedescuento = r.calculadescuento([],convertir_fecha(pagop.fechaproceso).date())
                        if float(monto) >= float(adeudado - valdescuento):
                            monto = monto - (r.adeudado() - valdescuento)
                        else:
                            adeudado = monto
                        descripdeta = 'PROMOCION ' + str(porcentajedescuento) + ' DESCUENTO POR PAGO DE CUOTAS'
                        if r.adeudado() == adeudado:
                            if not DetalleDescuento.objects.filter(rubro =r).exists():
                                desc = Descuento(inscripcion = r.inscripcion,
                                                          motivo =descripdeta,
                                                          total = valdescuento,
                                                          fecha = datetime.now())
                                desc.save()
                                detalle = DetalleDescuento(descuento =desc,
                                                            rubro =r,
                                                            valor = valdescuento,
                                                            porcentaje = porcentajedescuento)
                                detalle.save()

                                adeudado = r.adeudado()  - valdescuento
                                r.valor = (r.valor - valdescuento)
                                r.save()
                    pago2 = Pago(fecha=datetime.now().date(),
                                            recibe=caja.caja.persona,
                                            valor=adeudado,
                                            rubro=r,
                                            efectivo=False,
                                            wester=False,
                                            sesion=caja,
                                            electronico=False,
                                            pichincha=True,
                                            facilito=False)
                    pago2.save()
                    factura.pagos.add(pago2)

                    if r.adeudado()==0:
                        r.cancelado = True
                        r.save()
                        if RubroSeguimiento.objects.filter(rubro=r, estado=True).exists():
                            rubroseg = RubroSeguimiento.objects.filter(rubro=r, estado=True)[:1].get()
                            rubroseg.fechapago = datetime.now().date()
                            rubroseg.save()
                            seguimiento = True

                    caja.facturatermina= int(caja.caja.numerofact)+1
                    caja.save()

                    if FACTURACION_ELECTRONICA or caja.caja.numerofact  != None:
                        for luga in LugarRecaudacion.objects.all():
                            if luga.puntoventa == caja.caja.puntoventa:
                                luga.numerofact = int(caja.caja.numerofact)+1
                                luga.save()
                    client_address = ip_client_address(request)

                    # Log de CREACION DE NOTA DE CREDITO INSTITUCIONAL
                    LogEntry.objects.log_action(
                        # user_id         = request.user.pk,
                        user_id         = caja.caja.persona.usuario.pk,
                        content_type_id = ContentType.objects.get_for_model(factura).pk,
                        object_id       = factura.id,
                        object_repr     = force_str(factura),
                        action_flag     = ADDITION,
                        change_message  = 'Adicionada Factura Pagos-Pichincha '+  ' (' + client_address + ')' )
                    try:
                        if pagop.factura:
                            transaction.savepoint_rollback(sid)
                            continue

                        if Factura.objects.filter(numero= factura.numero).count()>1:
                            mail_errores_autorizacion("FACTURA REPETIDA "+DEFAULT_PASSWORD,"Existe mas de una factura repetida verificar en factura RECAUDACION PICHINCHA",factura.numero)
                            transaction.savepoint_rollback(sid)
                            errores.append(('error pago en linea - factura repetida pyid: '+ str(pagop.id) ,elimina_tildes(pagop.cuenta.inscripcion.persona.nombre_completo())))
                            continue
                        transaction.savepoint_commit(sid)
                        pagop.factura = factura
                        pagop.save()
                        transaction.savepoint_commit(sid)
                        valorrecibo = float(pagop.valorprocesado)  - adeudado
                        if  valorrecibo >0:
                        # if  Decimal(pagop.valorprocesado) > monto:
                        #     valorrecibo = float(pagop.valorprocesado)  - adeudado
                            rc = ReciboCajaInstitucion(inscripcion=pagop.cuenta.inscripcion,
                                                   motivo='RECIBO GENERADO POR EXCEDENTE EN RECAUDACION B. PICHINCHA',
                                                   sesioncaja=abrir_caja(CAJA_ONLINE),
                                                   fecha=datetime.now().date(),
                                                   hora=datetime.now().time(),
                                                   valorinicial = float(valorrecibo),
                                                   saldo=float(valorrecibo),
                                                   formapago=FormaDePago.objects.get(pk=12))
                            rc.save()
                            recibopago = ReciboPago(pago=pago2, recibocaja=rc)
                            recibopago.save()
                            transaction.savepoint_commit(sid)
                            errores.append(('se genero recibo caja a favor inscid: '+ str(pagop.cuenta.inscripcion.id) ,elimina_tildes(pagop.cuenta.inscripcion.persona.nombre_completo())))
                        # factura.notificacion_pago_online(rubro)
                    except Exception as ex:
                        transaction.savepoint_rollback(sid)
                        errores.append(('error en recaudacion pichincha inscid: '+ str(ex) ,elimina_tildes(pagop.cuenta.inscripcion.persona.nombre_completo())))
                        continue
                        # errores.append(('Ocurrio un Error.. Intente Nuevamente' + str(ex) ,d['ci']))
                        # email_error_pagoonline(errores,'ONLINE')
                        # return HttpResponse(json.dumps({'codigo':0,'mensaje':'Ocurrio un Error.. Intente Nuevamente' + str(ex)}),content_type="application/json")
                    # return HttpResponse(json.dumps({'codigo':1,'mensaje':'ok'}),content_type="application/json")
            else:
                transaction.savepoint_rollback(sid)
                errores.append(('error pago en recuadacion pichincha - caja cerrada inscid: ' +str(pagop.id ), elimina_tildes(pagop.cuenta.inscripcion.persona.nombre_completo())))
                continue

                # errores.append(('Factura Repetida' ,d['ci']))
                # email_error_pagoonline(errores,'ONLINE')
                # return HttpResponse(json.dumps({'codigo':0,'mensaje':'Factura Repetida'}),content_type="application/json")

        except Exception as ex:
            transaction.savepoint_rollback(sid)
            errores.append(('error pago en linea - caja cerrada pyid: ' +str(pagop.id ), str(ex)))
            continue
    if errores:
          email_error_congreso(errores,'RECAUDACION PICHINCHA')

    for rp in ArchivoPichincha.objects.filter(gestionado=False):
        if not RecaudacionPichincha.objects.filter(archivo=rp,factura=None).exists():
            rp.gestionado=True
            rp.save()
    return HttpResponse(json.dumps({'mensaje':'ok'}),content_type="application/json")

def sga_facturacion(request):
    formapago = FormaDePago.objects.get(id=16)
    for pagopy in PagoPymentez.objects.filter(factura=None,estado='success',detalle_estado=3):
        sid = transaction.savepoint()
        try:
            if abrir_caja(CAJA_ONLINE):
                caja = abrir_caja(CAJA_ONLINE)
            else:

                # errores.append(('Caja ya esta cerrada  ' ,d['ci']))
                # email_error_pagoonline(errores,'ONLINE')
                return HttpResponse(json.dumps({'codigo':0,'mensaje':'Caja ya esta cerrada'}),content_type="application/json")

            try:
                if ClienteFactura.objects.filter(ruc=pagopy.ruc).exists():
                    cliente = ClienteFactura.objects.filter(ruc=pagopy.ruc)[:1].get()
                    cliente.nombre =elimina_tildes(pagopy.nombre)
                    cliente.direccion =elimina_tildes(pagopy.direccion)
                    cliente.telefono =elimina_tildes(pagopy.telefono)
                    cliente.correo =pagopy.correo
                    if cliente.contrasena == None:
                        cliente.contrasena =pagopy.ruc
                        cliente.numcambio = 0
                    cliente.save()
                else:
                    cliente = ClienteFactura(ruc=elimina_tildes(pagopy.ruc),nombre=elimina_tildes(pagopy.nombre),
                        direccion=elimina_tildes(pagopy.direccion), telefono= elimina_tildes(pagopy.telefono),
                        correo=pagopy.correo,contrasena=pagopy.ruc,numcambio=0)
                    cliente.save()
            except :
                cliente = ClienteFactura(ruc=elimina_tildes(pagopy.ruc),nombre=elimina_tildes(pagopy.nombre),
                    direccion=elimina_tildes(pagopy.direccion), telefono= elimina_tildes(pagopy.telefono),
                    correo=pagopy.correo,contrasena=pagopy.ruc,numcambio=0)
                cliente.save()

            if not Factura.objects.filter(numero=caja.caja.puntoventa.strip()+"-"+str(caja.caja.numerofact).zfill(9)).exists():
                factura = Factura(numero = caja.caja.puntoventa.strip()+"-"+str(caja.caja.numerofact).zfill(9), fecha = datetime.now().date(),
                                        valida = True, cliente = cliente,
                                        subtotal = pagopy.monto , iva = 0, total = pagopy.monto, hora=datetime.now().time(),
                                        impresa=False, caja=caja.caja, estado = '', mensaje = '',dirfactura='')
                factura.save()
                if Factura.objects.filter(numero= factura.numero).count()>1:
                    mail_errores_autorizacion("FACTURA REPETIDA "+DEFAULT_PASSWORD,"Existe mas de una factura repetida verificar en factura PAGO ONLINE",factura.numero)
                    transaction.savepoint_rollback(sid)
                    continue
                tarjetadebito = False


                tp = PagoTarjeta(tipo=TipoTarjetaBanco.objects.filter(alias=pagopy.tipo.upper())[:1].get(),
                        poseedor=pagopy.nombre,
                        valor =pagopy.monto ,
                        procesadorpago=ProcesadorPagoTarjeta.objects.get(pk=1),
                        referencia=pagopy.referencia_tran,
                        tarjetadebito=tarjetadebito,
                        online=True,
                        fecha=datetime.now().date())
                tp.save()
                promogim = 0
                inscripcion = None
                pago2 = None
                sumaPagos = Decimal(0)
                for r in Rubro.objects.filter(pk__in=pagopy.rubros.split(",")):
                    pago2 = Pago(fecha=datetime.now().date(),
                                            recibe=caja.caja.persona,
                                            valor=r.adeudado(),
                                            rubro=r,
                                            efectivo=False,
                                            wester=False,
                                            sesion=caja,
                                            electronico=False,
                                            facilito=False)
                    pago2.save()
                    sumaPagos = sumaPagos + Decimal(pago2.valor)
                    tp.pagos.add(pago2)
                    factura.pagos.add(pago2)
                    if r.adeudado()==0:
                        if not r.vencido() :
                            if r.es_cuota() or r.es_matricula():
                                promogim = 1
                        r.cancelado = True
                        r.save()

                caja.facturatermina= int(caja.caja.numerofact)+1
                caja.save()
                factura.total = sumaPagos
                factura.save()

                if FACTURACION_ELECTRONICA or caja.caja.numerofact  != None:
                    for luga in LugarRecaudacion.objects.all():
                        if luga.puntoventa == caja.caja.puntoventa:
                            luga.numerofact = int(caja.caja.numerofact)+1
                            luga.save()
                client_address = ip_client_address(request)

                # Log de CREACION DE NOTA DE CREDITO INSTITUCIONAL
                LogEntry.objects.log_action(
                    # user_id         = request.user.pk,
                    user_id         = caja.caja.persona.usuario.pk,
                    content_type_id = ContentType.objects.get_for_model(factura).pk,
                    object_id       = factura.id,
                    object_repr     = force_str(factura),
                    action_flag     = ADDITION,
                    change_message  = 'Adicionada Factura Pagos-Online '+  ' (' + client_address + ')' )
                try:
                    pagopy.factura = factura
                    pagopy.save()
                    if PROMOCION_GYM:
                        if promogim:
                            inicio = datetime.datetime.now().date()
                            fin = datetime.datetime.now().date() + datetime.timedelta(30)
                            promo = PromoGym(inscripcion=pagopy.inscripcion,
                                             inicio=inicio,
                                             fin=fin,
                                             factura=factura)
                            promo.save()
                    transaction.savepoint_commit(sid)

                    if Decimal(pagopy.monto) > sumaPagos:
                        valor_rc = Decimal(pagopy.monto) - sumaPagos
                        rc = ReciboCajaInstitucion(inscripcion=inscripcion,
                                                   motivo='RECIBO GENERADO PAGO EN LINEA',
                                                   sesioncaja=caja,
                                                   fecha=datetime.now().date(),
                                                   hora=datetime.now().time(),
                                                   valorinicial=float(valor_rc),
                                                   formapago=formapago,
                                                   saldo=float(valor_rc))
                        rc.save()
                        recibopago = ReciboPago(pago=pago2, recibocaja=rc)
                        recibopago.save()
                        pagopy.disponible = False
                        pagopy.save()

                    # factura.notificacion_pago_online(rubro)
                except Exception as ex:
                    transaction.savepoint_rollback(sid)
                    continue
                    # errores.append(('Ocurrio un Error.. Intente Nuevamente' + str(ex) ,d['ci']))
                    # email_error_pagoonline(errores,'ONLINE')
                    # return HttpResponse(json.dumps({'codigo':0,'mensaje':'Ocurrio un Error.. Intente Nuevamente' + str(ex)}),content_type="application/json")
                # return HttpResponse(json.dumps({'codigo':1,'mensaje':'ok'}),content_type="application/json")
            else:
                transaction.savepoint_rollback(sid)
                continue
                # errores.append(('Factura Repetida' ,d['ci']))
                # email_error_pagoonline(errores,'ONLINE')
                # return HttpResponse(json.dumps({'codigo':0,'mensaje':'Factura Repetida'}),content_type="application/json")

        except Exception as ex:
            transaction.savepoint_rollback(sid)
            continue
    return HttpResponse(json.dumps({'codigo':0,'mensaje':'ok'}),content_type="application/json")
@transaction.atomic()

def facturacion_pedagogia(request):

    datos = requests.post('http://api.pedagogia.edu.ec',{'action': 'pagos_request_sga', 'pagado': '1','codigo':'0','rquest_sga':'0'},verify=False)
    if datos.status_code==200:
        errores =[]
        datosok =[]
        # datos2 =[]
        for d in  datos.json()['datos']:
            sid = transaction.savepoint()
            try:
                inscripcion=None
                grupo=None
                nivel=None
                cedula=None
                pasaporte=None
                if Grupo.objects.filter(nombre=d['codigo'].upper()).exists():
                    grupo= Grupo.objects.filter(nombre=d['codigo'].upper())[:1].get()
                    if Nivel.objects.filter(grupo=grupo).exists():
                        nivel = Nivel.objects.filter(grupo=grupo)[:1].get()
                if d['tipodni'] == 'c':
                    cedula = d['ci']
                    if Inscripcion.objects.filter(persona__cedula=d['ci']).exists():
                         inscripcion = Inscripcion.objects.filter(persona__cedula=d['ci'])[:1].get()
                if d['tipodni'] == 'p':
                    pasaporte = d['ci']
                    if Inscripcion.objects.filter(persona__pasaporte=d['ci']).exists():
                        inscripcion = Inscripcion.objects.filter(persona__pasaporte=d['ci'])[:1].get()
                if abrir_caja(CAJA_CONGRESO):
                    caja = abrir_caja(CAJA_CONGRESO)
                else:
                    transaction.savepoint_rollback(sid)
                    errores.append(('Caja ya esta cerrada ' ,d['ci']))
                    continue
                    # return HttpResponse(json.dumps({'codigo':0,'mensaje':'Caja ya esta cerrada'}),content_type="application/json")

                if grupo and nivel:

                    if not inscripcion:
                        canton = None
                        provincia = None
                        tipoanuncio = None
                        colegio = None
                        extranjero = False

                        try:
                            if d['tipodni'] == 'p':
                                extranjero = True

                            if TipoAnuncio.objects.filter(pk=13).exists():
                                tipoanuncio= TipoAnuncio.objects.filter(pk=13)[:1].get()

                            if Grupo.objects.filter(nombre=d['codigo'].upper()).exists():
                                grupo= Grupo.objects.filter(nombre=d['codigo'].upper())[:1].get()


                            if Sexo.objects.filter(nombre=d['sexo'].upper()).exists():
                                sexo= Sexo.objects.filter(nombre=d['sexo'].upper())[:1].get()
                            else:
                                sexo = Sexo.objects.all()[:1].get()

                            persona = Persona(nombres=d['nombre'],
                                            apellido1= d['paterno'],
                                            apellido2=d['materno'],
                                            extranjero=extranjero,
                                            cedula=cedula,
                                            pasaporte=pasaporte,
                                            nacimiento=d['fecha'],
                                            sexo=sexo,
                                            direccion=d['direccion'],
                                            telefono=d['cell'],
                                            telefono_conv=d['telefono'],
                                            email=(d['email'].lower()))
                            persona.save()
                            username = calculate_username(persona)
                            password = DEFAULT_PASSWORD
                            user = User.objects.create_user(username, persona.email, password)
                            user.save()
                            persona.usuario = user
                            persona.save()
                            usuariocon = User.objects.get(pk=USER_CONGRESO)
                            inscripcion = Inscripcion(persona=persona,
                                                    fecha = datetime.now(),
                                                    carrera=grupo.carrera,
                                                    descuentoporcent=0,
                                                    modalidad=grupo.modalidad,
                                                    sesion=grupo.sesion,
                                                    identificador='',
                                                    tienediscapacidad=False,
                                                    doblematricula=False,
                                                    observacion="INSCRIPCION AUTOMATICA",
                                                    anuncio=tipoanuncio,
                                                    user=usuariocon )
                            # inscripcion.save()
                            i = Inscripcion.objects.latest('id') if Inscripcion.objects.exists() else None
                            if i:
                                inscripcion.numerom = i.numerom + 1
                            else:
                                inscripcion.numerom = 1
                            inscripcion.save()
                            if not InscripcionGrupo.objects.filter(inscripcion=inscripcion, grupo=grupo, activo=True).exists():
                                ig = InscripcionGrupo(inscripcion=inscripcion, grupo=grupo, activo=True)
                                ig.save()
                            else:
                                ig= InscripcionGrupo.objects.filter(inscripcion=inscripcion,activo=True)[:1].get()
                                ig.grupo=grupo
                                ig.save()
                            if DatosPersonaCongresoIns.objects.filter(preinscripcion=None,inscripcion=inscripcion,grupo=grupo).exists():
                                DatosPersonaCongresoIns.objects.filter(preinscripcion=None,inscripcion=inscripcion,grupo=grupo).delete()
                            for part in d['participa'].split(','):
                                try:
                                    partid = int(part)
                                except:
                                    partid =0

                                if TipoPersonaCongreso.objects.filter(pk=partid).exists():
                                    tipopersona = TipoPersonaCongreso.objects.filter(pk=partid)[:1].get()
                                    if not DatosPersonaCongresoIns.objects.filter(inscripcion=inscripcion,tipopersona=tipopersona,grupo=grupo).exists():
                                        personains = DatosPersonaCongresoIns(inscripcion=inscripcion,
                                                                       tipopersona=tipopersona,
                                                                       grupo=grupo)
                                        personains.save()
                            for dis in d['discapacidad'].split(','):
                                try:
                                    disid = int(dis)
                                except:
                                    disid =0
                                if Discapacidad.objects.filter(pk=disid).exists():
                                    discapacidad = Discapacidad.objects.filter(pk=disid)[:1].get()
                                    if not DatosPersonaCongresoIns.objects.filter(inscripcion=inscripcion,tipodiscapacidad=discapacidad,grupo=grupo).exists():
                                        personains = DatosPersonaCongresoIns(inscripcion=inscripcion,
                                                                       tipodiscapacidad=discapacidad,
                                                                       grupo=grupo)
                                        personains.save()
                                    inscripcion.tienediscapacidad=True
                                    inscripcion.save()
                            for r in d['requerimiento'].split(','):
                                try:
                                    rid = int(r)
                                except:
                                    rid=0
                                if RequerimientoCongreso.objects.filter(pk=rid).exists():
                                    requerimiento = RequerimientoCongreso.objects.filter(pk=rid)[:1].get()
                                    if not DatosPersonaCongresoIns.objects.filter(inscripcion=inscripcion,requerimiento=requerimiento,grupo=grupo).exists():
                                        personains = DatosPersonaCongresoIns(inscripcion=inscripcion,
                                                                       requerimiento=requerimiento,
                                                                       grupo=grupo)
                                        personains.save()


                        except Exception as e:
                            transaction.savepoint_rollback(sid)
                            errores.append(('Ocurrio un Error.. ' + str(e),d['ci']))
                            continue
                            # return HttpResponse(json.dumps({'codigo':0,'mensaje':'Ocurrio un Error.. Intente Nuevamente' + str(e)}),content_type="application/json")
                    if inscripcion:
                        # rubromat = inscripcion.matricular(nivel)
                        if inscripcion.matricula():
                            rubromat = RubroMatricula.objects.filter(matricula=inscripcion.matricula())[:1].get()
                        else:
                            rubromat = inscripcion.matricular_pedagogia(nivel)
                        # if rubromat:
                        if rubromat:
                            rubromat.rubro.valor=  Decimal(d['valor'])
                            rubromat.rubro.save()
                            rubro =rubromat.rubro
                            recepcion = ''
                            dirfactur=''
                            mensajerecep=''
                            # if rubro.cancelado
                            if rubro.valor > rubro.adeudado():
                                transaction.savepoint_rollback(sid)
                                datosok.append([d['trj_id'],d['id']])
                                # datos2.append(datosok)
                                errores.append(('Excede el valor permitido del pago ' ,d['ci']))
                                continue
                                # return HttpResponse(json.dumps({'codigo':3,'mensaje':'Excede el valor permitido del pago'}),content_type="application/json")
                            try:

                                cliente = ClienteFactura.objects.filter(ruc=d['fac_ci'])[:1].get()
                                cliente.nombre =d['fac_nombre']
                                cliente.direccion =d['fac_direcion']
                                cliente.telefono = d['telefono']
                                cliente.correo =d['fac_email']
                                if cliente.contrasena == None:
                                    cliente.contrasena = d['fac_ci']
                                    cliente.numcambio = 0
                                cliente.save()
                            except :
                                cliente = ClienteFactura(ruc=d['fac_ci'], nombre=d['fac_nombre'],
                                    direccion=d['fac_direcion'], telefono= d['telefono'],
                                    correo=d['fac_email'],contrasena=d['fac_ci'],numcambio=0)
                                cliente.save()

                            if not Factura.objects.filter(numero=caja.caja.puntoventa.strip()+"-"+str(caja.caja.numerofact).zfill(9)).exists():
                                factura = Factura(numero = caja.caja.puntoventa.strip()+"-"+str(caja.caja.numerofact).zfill(9), fecha = datetime.now().date(),
                                                        valida = True, cliente = cliente,
                                                        subtotal = d['valor'], iva = 0, total = d['valor'], hora=datetime.now().time(),
                                                        impresa=False, caja=caja.caja, estado = recepcion, mensaje = mensajerecep,dirfactura=dirfactur)
                                factura.save()
                                tarjetadebito = False

                                tp = PagoTarjeta(tipo=TipoTarjetaBanco.objects.get(alias=d['trj_tipo']),
                                        poseedor=d['trj_nombre'],
                                        valor = d['valor'],
                                        procesadorpago=ProcesadorPagoTarjeta.objects.get(pk=1),
                                        referencia=d['trj_referencia'],
                                        tarjetadebito=tarjetadebito,
                                        online=True,
                                        fecha=datetime.now().date())
                                tp.save()
                                pago2 = Pago(fecha=datetime.now().date(),
                                                        recibe=caja.caja.persona,
                                                        valor=d['valor'],
                                                        rubro=rubro,
                                                        efectivo=False,
                                                        wester=False,
                                                        sesion=caja,
                                                        electronico=False,
                                                        facilito=False)
                                pago2.save()
                                tp.pagos.add(pago2)
                                factura.pagos.add(pago2)

                                caja.facturatermina= int(caja.caja.numerofact)+1
                                caja.save()
                                if rubro.adeudado()==0:
                                    rubro.cancelado = True
                                    rubro.save()
                                if FACTURACION_ELECTRONICA or caja.caja.numerofact  != None:
                                    for luga in LugarRecaudacion.objects.all():
                                        if luga.puntoventa == caja.caja.puntoventa:
                                            luga.numerofact = int(caja.caja.numerofact)+1
                                            luga.save()


                                # Log de CREACION DE NOTA DE CREDITO INSTITUCIONAL
                                LogEntry.objects.log_action(
                                    # user_id         = request.user.pk,
                                    user_id         = caja.caja.persona.usuario.pk,
                                    content_type_id = ContentType.objects.get_for_model(factura).pk,
                                    object_id       = factura.id,
                                    object_repr     = force_str(factura),
                                    action_flag     = ADDITION,
                                    change_message  = 'Adicionada Factura Pagos-Online ')
                                try:
                                    transaction.savepoint_commit(sid)
                                    factura.notificacion_pago_online(rubro)
                                except Exception as ex:
                                    transaction.savepoint_rollback(sid)
                                    errores.append(('Ocurrio un Error.. ' + str(ex) ,d['ci']))
                                    continue
                                # datosok.append((d['id']))
                                datosok.append([d['trj_id'],d['id']])
                                # datos2.append(datosok)
                            else:
                                transaction.savepoint_rollback(sid)
                                errores.append(('Factura Repetida ' ,d['ci']))
                                continue
                                # return HttpResponse(json.dumps({'codigo':0,'mensaje':'Factura Repetida'}),content_type="application/json")
                        else:

                            transaction.savepoint_rollback(sid)
                            errores.append(('No se pudo matricular ' ,d['ci']))
                            continue
                            # return HttpResponse(json.dumps({'codigo':0,'mensaje':'No se pudo matricular'}),content_type="application/json")
            except Exception as ex:
                transaction.savepoint_rollback(sid)
                errores.append(('Ocurrio un Error.. ' + str(ex) ,d['ci']))
                continue
                # return HttpResponse(json.dumps({'codigo':0,'mensaje':'Ocurrio un Error.. Intente Nuevamente' + str(ex)}),content_type="application/json")
        if errores:
            from sga.pre_inscripciones import email_error_pagoonline
            email_error_pagoonline(errores,'CRONTAB')
        if datosok:
            dat = requests.post('http://api.pedagogia.edu.ec',{'action': 'pagos_request_udp', 'datos':json.dumps(datosok)},verify=False)

# def facturacion_sga(request)
def fix_formadepago_str(x):
    pago = Pago.objects.get(pk=x.id)
    return pago.nombre()

def fix_pago_str(x):
    pago = Pago.objects.get(pk=x.id)
    if pago.es_retencion():
        fp = 1
    elif pago.es_notacreditoinst():
        fp=2
    else :
        fp = 0

    obj = model_to_dict(pago, exclude=['fecha', 'lugar', 'recibe','efectivo','id'])
    rubro = Rubro.objects.get(pk=obj['rubro'])
    obj['rubro'] = model_to_dict(rubro, exclude=['fecha','fechavence', 'cancelado','inscripcion','fichamedica','valor'])
    obj['rubro'].update({'nombre': rubro.nombre(), 'tipo': rubro.tipo(), 'alumno': rubro.inscripcion.persona.nombre_completo() if rubro.inscripcion else str(rubro.fichamedica),'fp':fp,'id':rubro.id})

    return obj
def exportacion_datos_asignaturaitb(idmalla):

    asignatura=AsignaturaMalla.objects.filter(malla__id=idmalla).order_by('asignatura')
    data = []
    for a in asignatura:
        datos = []
        try:
            datos.append(a.malla.id)
            datos.append(a.asignatura.id)
            datos.append(elimina_tildes(a.nivelmalla.nombre))
            datos.append(elimina_tildes(a.asignatura.nombre))
            datos.append(a.id)

            data.append(datos)
            # print(datos)
        except Exception as ex:
            print('ERROR EXCEPCION ASIGNATURACONVALIDAR  ' + str(ex))


    return data

def exportacion_datos_mallaitb():
    malla=Malla.objects.filter().order_by("carrera")
    data = []
    for m in malla:
        datos = []
        try:
            datos.append(elimina_tildes(m.carrera.nombre))
            datos.append(m.carrera.id)
            datos.append(m.id)

            data.append(datos)
            # print(datos)
        except Exception as ex:
            pass
    # print(data)
    return data


def exportacion_datos_historicoitb(cedula):

    historicoitb= RecordAcademico.objects.filter(inscripcion__persona__cedula=cedula,aprobada=True).order_by()
    data = []
    for hi in historicoitb:
        print(cedula)
        print(hi)
        datos=[]
        try:
            # datos.append(hi.carrera.nombre.encode("ascii","ignore"))
            datos.append(hi.asignatura.id)
            datos.append(hi.estado())
            datos.append(hi.nota)
            datos.append(hi.fecha.year)
# anno->fecha.year, notafinal

            data.append(datos)

        except Exception as ex:
            print(ex)
            pass

    return data

@transaction.atomic()
def view (request):
    # if request.method=='POST':
        if 'a' in request.POST:
            action =request.POST['a']
            if action == 'facturar':
                errores=[]
                from sga.pre_inscripciones import email_error_pagoonline
                sid = transaction.savepoint()
                if request.POST['opcion'] == 'pedagogia':
                    try:
                        inscripcion=None
                        grupo=None
                        nivel=None
                        cedula=None
                        pasaporte=None

                        d = json.loads(request.POST['datos'])
                        if Grupo.objects.filter(nombre=d['codigo'].upper()).exists():
                            grupo= Grupo.objects.filter(nombre=d['codigo'].upper())[:1].get()
                            if Nivel.objects.filter(grupo=grupo).exists():
                                nivel = Nivel.objects.filter(grupo=grupo)[:1].get()
                        if d['tipodni'] == 'c':
                            cedula = d['ci']
                            if Inscripcion.objects.filter(persona__cedula=d['ci']).exists():
                                 inscripcion = Inscripcion.objects.filter(persona__cedula=d['ci'])[:1].get()
                        if d['tipodni'] == 'p':
                            pasaporte = d['ci']
                            if Inscripcion.objects.filter(persona__pasaporte=d['ci']).exists():
                                inscripcion = Inscripcion.objects.filter(persona__pasaporte=d['ci'])[:1].get()
                        if abrir_caja(CAJA_CONGRESO):
                            caja = abrir_caja(CAJA_CONGRESO)
                        else:

                            errores.append(('Caja ya esta cerrada  ' ,d['ci']))
                            email_error_pagoonline(errores,'ONLINE')
                            return HttpResponse(json.dumps({'codigo':0,'mensaje':'Caja ya esta cerrada'}),content_type="application/json")

                        if grupo and nivel:

                            if not inscripcion:
                                canton = None
                                provincia = None
                                tipoanuncio = None
                                colegio = None
                                extranjero = False

                                try:
                                    if d['tipodni'] == 'p':
                                        extranjero = True

                                    if TipoAnuncio.objects.filter(pk=13).exists():
                                        tipoanuncio= TipoAnuncio.objects.filter(pk=13)[:1].get()

                                    if Grupo.objects.filter(nombre=d['codigo'].upper()).exists():
                                        grupo= Grupo.objects.filter(nombre=d['codigo'].upper())[:1].get()


                                    if Sexo.objects.filter(nombre=d['sexo'].upper()).exists():
                                        sexo= Sexo.objects.filter(nombre=d['sexo'].upper())[:1].get()
                                    else:
                                        sexo = Sexo.objects.all()[:1].get()

                                    persona = Persona(nombres=d['nombre'],
                                                    apellido1= d['paterno'],
                                                    apellido2=d['materno'],
                                                    extranjero=extranjero,
                                                    cedula=cedula,
                                                    pasaporte=pasaporte,
                                                    nacimiento=d['fecha'],
                                                    sexo=sexo,
                                                    direccion=d['direccion'],
                                                    telefono=d['cell'],
                                                    telefono_conv=d['telefono'],
                                                    email=(d['email'].lower()))
                                    persona.save()
                                    username = calculate_username(persona)
                                    password = DEFAULT_PASSWORD
                                    user = User.objects.create_user(username, persona.email, password)
                                    user.save()
                                    persona.usuario = user
                                    persona.save()
                                    usuariocon = User.objects.get(pk=USER_CONGRESO)
                                    inscripcion = Inscripcion(persona=persona,
                                                            fecha = datetime.now(),
                                                            carrera=grupo.carrera,
                                                            descuentoporcent=0,
                                                            modalidad=grupo.modalidad,
                                                            sesion=grupo.sesion,
                                                            identificador='',
                                                            tienediscapacidad=False,
                                                            doblematricula=False,
                                                            observacion="INSCRIPCION AUTOMATICA",
                                                            anuncio=tipoanuncio,
                                                            user=usuariocon )
                                    # inscripcion.save()
                                    i = Inscripcion.objects.latest('id') if Inscripcion.objects.exists() else None
                                    if i:
                                        inscripcion.numerom = i.numerom + 1
                                    else:
                                        inscripcion.numerom = 1
                                    inscripcion.save()
                                    if not InscripcionGrupo.objects.filter(inscripcion=inscripcion, grupo=grupo, activo=True).exists():
                                        ig = InscripcionGrupo(inscripcion=inscripcion, grupo=grupo, activo=True)
                                        ig.save()
                                    else:
                                        ig= InscripcionGrupo.objects.filter(inscripcion=inscripcion,activo=True)[:1].get()
                                        ig.grupo=grupo
                                        ig.save()
                                    if DatosPersonaCongresoIns.objects.filter(preinscripcion=None,inscripcion=inscripcion).exists():
                                        DatosPersonaCongresoIns.objects.filter(preinscripcion=None,inscripcion=inscripcion).delete()
                                    for part in d['participa'].split(','):
                                        try:
                                            partid = int(part)
                                        except:
                                            partid =0

                                        if TipoPersonaCongreso.objects.filter(pk=partid).exists():
                                            tipopersona = TipoPersonaCongreso.objects.filter(pk=partid)[:1].get()
                                            if not DatosPersonaCongresoIns.objects.filter(inscripcion=inscripcion,tipopersona=tipopersona,grupo=grupo).exists():
                                                personains = DatosPersonaCongresoIns(inscripcion=inscripcion,
                                                                               tipopersona=tipopersona,
                                                                               grupo=grupo)
                                                personains.save()
                                    for dis in d['discapacidad'].split(','):
                                        try:
                                            disid = int(dis)
                                        except:
                                            disid =0
                                        if Discapacidad.objects.filter(pk=disid).exists():
                                            discapacidad = Discapacidad.objects.filter(pk=disid)[:1].get()
                                            if not DatosPersonaCongresoIns.objects.filter(inscripcion=inscripcion,tipodiscapacidad=discapacidad,grupo=grupo).exists():
                                                personains = DatosPersonaCongresoIns(inscripcion=inscripcion,
                                                                               tipodiscapacidad=discapacidad,
                                                                               grupo=grupo)
                                                personains.save()
                                            inscripcion.tienediscapacidad=True
                                            inscripcion.save()
                                    for r in d['requerimiento'].split(','):
                                        try:
                                            rid = int(r)
                                        except:
                                            rid=0
                                        if RequerimientoCongreso.objects.filter(pk=rid).exists():
                                            requerimiento = RequerimientoCongreso.objects.filter(pk=rid)[:1].get()
                                            if not DatosPersonaCongresoIns.objects.filter(inscripcion=inscripcion,requerimiento=requerimiento,grupo=grupo).exists():
                                                personains = DatosPersonaCongresoIns(inscripcion=inscripcion,
                                                                               requerimiento=requerimiento,
                                                                               grupo=grupo)
                                                personains.save()

                                except Exception as e:
                                    transaction.savepoint_rollback(sid)
                                    errores.append(('Ocurrio un Error.. Intente Nuevamente' + str(e) ,d['ci']))
                                    email_error_pagoonline(errores,'ONLINE')
                                    return HttpResponse(json.dumps({'codigo':0,'mensaje':'Ocurrio un Error.. Intente Nuevamente' + str(e)}),content_type="application/json")
                            if inscripcion:
                                # rubromat = inscripcion.matricular(nivel)
                                if inscripcion.matricula():
                                    rubromat = RubroMatricula.objects.filter(matricula=inscripcion.matricula())[:1].get()
                                else:
                                    rubromat = inscripcion.matricular_pedagogia(nivel)
                                # if rubromat:
                                if rubromat:
                                    rubromat.rubro.valor= Decimal(d['valor'])
                                    rubromat.rubro.save()
                                    rubro =rubromat.rubro
                                    recepcion = ''
                                    dirfactur=''
                                    mensajerecep=''
                                    # if rubro.cancelado
                                    if rubro.valor > rubro.adeudado():
                                        errores.append(('Excede el valor permitido del pago' ,d['ci']))
                                        email_error_pagoonline(errores,'ONLINE')
                                        return HttpResponse(json.dumps({'codigo':3,'mensaje':'Excede el valor permitido del pago'}),content_type="application/json")
                                    try:

                                        cliente = ClienteFactura.objects.filter(ruc=d['fac_ci'])[:1].get()
                                        cliente.nombre =d['fac_nombre']
                                        cliente.direccion =d['fac_direcion']
                                        cliente.telefono = d['telefono']
                                        cliente.correo =d['fac_email']
                                        if cliente.contrasena == None:
                                            cliente.contrasena = d['fac_ci']
                                            cliente.numcambio = 0
                                        cliente.save()
                                    except :
                                        cliente = ClienteFactura(ruc=d['fac_ci'], nombre=d['fac_nombre'],
                                            direccion=d['fac_direcion'], telefono= d['telefono'],
                                            correo=d['fac_email'],contrasena=d['fac_ci'],numcambio=0)
                                        cliente.save()

                                    if not Factura.objects.filter(numero=caja.caja.puntoventa.strip()+"-"+str(caja.caja.numerofact).zfill(9)).exists():
                                        factura = Factura(numero = caja.caja.puntoventa.strip()+"-"+str(caja.caja.numerofact).zfill(9), fecha = datetime.now().date(),
                                                                valida = True, cliente = cliente, hora=datetime.now().time(),
                                                                subtotal = d['valor'], iva = 0, total = d['valor'],
                                                                impresa=False, caja=caja.caja, estado = recepcion, mensaje = mensajerecep,dirfactura=dirfactur)
                                        factura.save()
                                        tarjetadebito = False

                                        tp = PagoTarjeta(tipo=TipoTarjetaBanco.objects.get(alias=d['trj_tipo']),
                                                poseedor=d['trj_nombre'],
                                                valor = d['valor'],
                                                procesadorpago=ProcesadorPagoTarjeta.objects.get(pk=1),
                                                referencia=d['trj_referencia'],
                                                tarjetadebito=tarjetadebito,
                                                online=True,
                                                fecha=datetime.now().date())
                                        tp.save()
                                        pago2 = Pago(fecha=datetime.now().date(),
                                                                recibe=caja.caja.persona,
                                                                valor=d['valor'],
                                                                rubro=rubro,
                                                                efectivo=False,
                                                                wester=False,
                                                                sesion=caja,
                                                                electronico=False,
                                                                facilito=False)
                                        pago2.save()
                                        tp.pagos.add(pago2)
                                        factura.pagos.add(pago2)

                                        caja.facturatermina= int(caja.caja.numerofact)+1
                                        caja.save()
                                        if rubro.adeudado()==0:
                                            rubro.cancelado = True
                                            rubro.save()
                                        if FACTURACION_ELECTRONICA or caja.caja.numerofact  != None:
                                            for luga in LugarRecaudacion.objects.all():
                                                if luga.puntoventa == caja.caja.puntoventa:
                                                    luga.numerofact = int(caja.caja.numerofact)+1
                                                    luga.save()
                                        client_address = ip_client_address(request)

                                        # Log de CREACION DE NOTA DE CREDITO INSTITUCIONAL
                                        LogEntry.objects.log_action(
                                            # user_id         = request.user.pk,
                                            user_id         = caja.caja.persona.usuario.pk,
                                            content_type_id = ContentType.objects.get_for_model(factura).pk,
                                            object_id       = factura.id,
                                            object_repr     = force_str(factura),
                                            action_flag     = ADDITION,
                                            change_message  = 'Adicionada Factura Pagos-Online '+  ' (' + client_address + ')' )
                                        try:
                                            transaction.savepoint_commit(sid)
                                            factura.notificacion_pago_online(rubro)
                                        except Exception as ex:
                                            transaction.savepoint_rollback(sid)
                                            errores.append(('Ocurrio un Error.. Intente Nuevamente' + str(ex) ,d['ci']))
                                            email_error_pagoonline(errores,'ONLINE')
                                            return HttpResponse(json.dumps({'codigo':0,'mensaje':'Ocurrio un Error.. Intente Nuevamente' + str(ex)}),content_type="application/json")
                                        return HttpResponse(json.dumps({'codigo':1,'mensaje':'ok'}),content_type="application/json")
                                    else:
                                        transaction.savepoint_rollback(sid)
                                        errores.append(('Factura Repetida' ,d['ci']))
                                        email_error_pagoonline(errores,'ONLINE')
                                        return HttpResponse(json.dumps({'codigo':0,'mensaje':'Factura Repetida'}),content_type="application/json")
                                else:
                                    transaction.savepoint_rollback(sid)
                                    errores.append(('No se pudo matricular' ,d['ci']))
                                    email_error_pagoonline(errores,'ONLINE')
                                    return HttpResponse(json.dumps({'codigo':0,'mensaje':'No se pudo matricular'}),content_type="application/json")
                    except Exception as ex:
                        transaction.savepoint_rollback(sid)
                        errores.append(('Ocurrio un Error.. Intente Nuevamente ' + str(ex) ,''))
                        email_error_pagoonline(errores,'ONLINE')
                        return HttpResponse(json.dumps({'codigo':0,'mensaje':'Ocurrio un Error.. Intente Nuevamente' + str(ex)}),content_type="application/json")
                else:
                    transaction.savepoint_rollback(sid)
                    return HttpResponse(json.dumps({'codigo':0,'mensaje':'opcion incorrecta'}),content_type="application/json")
            # else:
            #     transaction.savepoint_rollback(sid)
            #     return HttpResponse(json.dumps({'codigo':0,'mensaje':'No existe accion'}),content_type="application/json")

            elif action == 'mensajes':
                try:
                    d = json.loads(request.POST['datos'])
                    client = Client('http://online.publimes.com:5000/Service.svc?wsdl')
                    comprobar =  client.service.EnviarMensaje( 79,'TECBO14593', d['operadora'], d['telefono'], d['mensaje'])
                    if comprobar == '0':
                        mensajeenviado = MensajesEnviado(nombre = "WEB SERVICE PAGINA",
                                                        celular = d['telefono'],
                                                        filtro = "WEBSERVICE",
                                                        mensaje = d['mensaje'],
                                                        fecha = datetime.datetime.now())
                        mensajeenviado.save()
                    return HttpResponse(json.dumps({'result':"ok",'comprobar':str(comprobar)}),content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({'result':"bad",'comprobar':str(e)}),content_type="application/json")
            elif action == 'matribucksgaonline':
                sid = transaction.savepoint()
                try:
                    d = json.loads(request.POST['data'])
                    materiacurso= Materia.objects.get(pk=d['id'])
                    pagocurso = PagosCursoITB.objects.filter(materia=materiacurso)
                    if MateriaAsignada.objects.filter(materia=materiacurso).exists():
                        cantinsc = MateriaAsignada.objects.filter(materia=materiacurso).count()
                        if materiacurso.numper <= cantinsc:
                            return HttpResponse(json.dumps({"result":"bad","error":"No hay cupo disponible"}), content_type="application/json")
                    if not Persona.objects.filter(cedula=d['cedula']).exclude(cedula=None).exclude(cedula='').exists() and  not  Persona.objects.filter(pasaporte=d['pasaporte']).exclude(pasaporte=None).exclude(pasaporte='').exists():
                        cedula = d['cedula']
                        pasaporte = d['pasaporte']
                        p = Persona(apellido1 =d['apellido1'],
                                    apellido2 = d['apellido2'],
                                    nombres = d['nombres'],
                                    cedula = cedula,
                                    pasaporte = pasaporte,
                                    telefono_conv = d['telefono_conv'],
                                    telefono = d['telefono'],
                                    email = d['email'],
                                    direccion = d['direccion'],
                                    direccion2 = d['direccion2'])
                        p.save()
                        if pasaporte != '':
                            p.extranjero=True
                            p.save()

                    else:
                        if Persona.objects.filter(cedula=d['cedula']).exclude(cedula=None).exclude(cedula='').exists():
                            p = Persona.objects.filter(cedula=d['cedula']).exclude(cedula=None).exclude(cedula='')[:1].get()
                        else:
                            p = Persona.objects.filter(pasaporte=d['pasaporte']).exclude(pasaporte=None).exclude(pasaporte='')[:1].get()

                    if not Inscripcion.objects.filter(persona=p).exists():
                         inscrip = Inscripcion(persona = p,
                                               carrera_id = 2,
                                               modalidad_id = 1,
                                               sesion_id = 1,
                                               especialidad_id=1,
                                               fecha=datetime.now(),
                                               sgaonline = True)
                         inscrip.save()
                    else:
                         inscrip = Inscripcion.objects.filter(persona=p,sgaonline=True)[:1].get()

                    #matricular alumnos
                    nivel = Nivel.objects.filter()[:1].get()
                    if not Matricula.objects.filter(inscripcion=inscrip, nivel=nivel).exists():

                        alu_matricul = Matricula(inscripcion = inscrip,
                                                 nivel = nivel)
                        alu_matricul.save()
                    else:
                        alu_matricul = Matricula.objects.filter(inscripcion=inscrip, nivel=nivel)[:1].get()

                    if not MateriaAsignada.objects.filter(matricula=alu_matricul,materia=materiacurso).exists():
                        alu_materia = MateriaAsignada(matricula = alu_matricul,
                                                      materia = materiacurso,
                                                      notafinal = 0,
                                                      asistenciafinal = 0,
                                                      supletorio = 0,
                                                      cerrado = False)
                        alu_materia.save()

                    #asignacion de rubros
                    pcurso = PagosCursoITB.objects.filter(materia=materiacurso)[:1].get()
                    if not DetallePagosITB.objects.filter(inscripcion=inscrip,materia=materiacurso,rubrocurso=pcurso).exists():
                        for pagos in pagocurso:
                            hoy = datetime.now().date()
                            detallepagos = DetallePagosITB(inscripcion = inscrip,
                                                           materia=materiacurso,
                                                           rubrocurso=pagos)
                            detallepagos.save()

                            r = Rubro(fecha =hoy,
                                      valor = pagos.valor,
                                      inscripcion = inscrip,
                                      cancelado = False,
                                      fechavence = pagos.fechavence)
                            r.save()

                            rotro = RubroOtro(rubro=r,
                                              tipo=TipoOtroRubro.objects.get(pk=RUBRO_TIPO_CURSOS),
                                              descripcion= pagos.materia.asignatura.nombre + " - " + pagos.materia.grupo+ " - " + pagos.nombre)
                            rotro.save()
                            detallepagos.rubro = r
                            detallepagos.save()
                    else:
                        for pagos in pagocurso:
                            hoy = datetime.now().date()
                            if DetallePagosITB.objects.filter(inscripcion=inscrip,materia=materiacurso,rubrocurso=pagos).exists():
                                rubrodet=DetallePagosITB.objects.get(inscripcion=inscrip,materia=materiacurso,rubrocurso=pagos)
                                rbdet = Rubro.objects.get(pk=rubrodet.rubro.id)

                                if rbdet.cancelado==False:
                                    rbdet.fecha=hoy
                                    rbdet.valor = pagos.valor
                                    rbdet.fechavence= pagos.fechavence
                                    rbdet.save()

                                    rubrootro=RubroOtro.objects.get(rubro=rbdet)
                                    rubrootro.descripcion=rubrodet.rubrocurso.nombre
                                    rubrootro.save()
                    if 'buckop' in request.POST:
                        datosbase = DATABASES
                        if datosbase['default']['HOST'] != 'localhost':
                            db = psycopg2.connect("host=10.10.9.45 dbname=sgaonline user=postgres password=Itb$2019")
                            cursor = db.cursor()
                            cursor.execute("UPDATE sga_inscripcion	SET nivelconvalid='"+ str(d['curso']) +"'	from sga_persona "
                                           " WHERE sga_inscripcion.persona_id = sga_persona.id and "
                                           "sga_persona.cedula = '"+ str(d['cedula']) +"' or sga_persona.pasaporte = '"+d['pasaporte']+"' and sga_inscripcion.convalingle = true")
                            db.commit()
                            # count = cursor.rowcount
                            db.close()
                    transaction.savepoint_commit(sid)
                    return HttpResponse(json.dumps({"result":"ok"}), content_type="application/json")
                except Exception as ex:
                    transaction.savepoint_rollback(sid)
                    return HttpResponse(json.dumps({"result":"bad","error":str(ex)}), content_type="application/json")
            elif action == 'pagempleo':
                sid = transaction.savepoint()
                try:
                    datos = []
                    cursos = []
                    tienediscapacidad = 'NO'
                    colegio = ''
                    colegioid = ''
                    canton = ''
                    cantonid = ''
                    parroquia = ''
                    parroquiaid = ''
                    nombres = ''
                    apellido1 = ''
                    apellido2 = ''
                    pasaporte = ''
                    cedula = ''
                    email = ''
                    emailinst = ''
                    celular = ''
                    convecional = ''
                    sexo = 'FEMENINO'
                    direccion = ''
                    fechanacimiento = ''
                    estadocivil = ''
                    cedrequest = request.POST['cedula']
                    if ViewEstudiantEmpleo.objects.filter(cedula=cedrequest).exclude(cedula='').exclude(cedula=None).exists():
                        viewestudiantempleo = ViewEstudiantEmpleo.objects.filter(cedula=cedrequest).exclude(cedula='').exclude(cedula=None)
                    elif ViewEstudiantEmpleo.objects.filter(pasaporte=cedrequest).exclude(pasaporte='').exclude(pasaporte=None).exists():
                        viewestudiantempleo = ViewEstudiantEmpleo.objects.filter(pasaporte=cedrequest).exclude(pasaporte='').exclude(pasaporte=None)
                    else:
                        return HttpResponse(json.dumps({"result":"bad","error":str("NO EXISTE INFORMACION")}), content_type="application/json")
                    for i in viewestudiantempleo:

                        if i.nombres:
                            nombres = i.nombres
                        if i.apellido1:
                            apellido1 = i.apellido1
                        if i.apellido2:
                            apellido2 = i.apellido2
                        if i.email:
                            email = i.email
                        if i.emailinst:
                            emailinst = i.emailinst
                        if i.telefono:
                            celular = i.telefono
                        if i.telefono_conv:
                            convecional = i.telefono_conv


                        if i.tienediscapacidad:
                            tienediscapacidad = 'SI'
                        if i.estcolegio_id:
                          colegio = i.colegio
                          colegioid = i.estcolegio_id
                        if i.cantonresid_id:
                          canton = i.canton
                          cantonid = i.cantonresid_id
                        if i.parroquia_id:
                          parroquia = i.parroquia
                          parroquiaid = i.parroquia_id
                        if i.sexo:
                          sexo = i.sexo
                        diring = False
                        if i.direccion:
                            diring = True
                            direccion = i.direccion
                        if i.direccion2:
                            if direccion and diring:
                                direccion = direccion +" y " + i.direccion2
                            else:
                                direccion = i.direccion2
                        if i.pasaporte:
                            pasaporte = i.pasaporte
                        else:
                            cedula = i.cedula
                        if i.estadocivil:
                            estadocivil = i.estadocivil
                        if i.carrera:
                            datos.append({"tipopersona": "GRADUADO" if i.graduado else "ESTUDIANTE","carrera":i.carreranom,"idcarrera":i.idcarrera,"fechaestudio":str(i.fechaestudio),"online":i.online})
                        else:
                            cursos.append({"curso":i.carreranom})
                        if i.fechanacimiento:
                            fechanacimiento = i.fechanacimiento


                    datosidio = requests.get('http://sga.buckcenter.com.ec/api',params={'a': 'datos_idiomas', 'ced':cedrequest })
                    idiomas = []
                    idiom = ""
                    if datosidio.status_code==200:
                        try:
                            idiom = datosidio.json()['notas']
                        except:
                            pass
                    if idiom:
                        for idio in idiom:
                            idiomas.append({'nivel':idio[0]})
                    resultado = {}
                    resultado['result'] = "ok"
                    lista = [{"nombres": nombres,"apellido1": apellido1,
                              "apellido2": apellido2,"cedula": cedula,
                              "pasaporte": pasaporte,"emailinst": emailinst,"email": email,
                              "direccion": direccion ,"celular": celular ,"telefono": convecional,
                              "colegio":colegio,"colegioid":colegioid, "discapacidad": tienediscapacidad,
                              "ciudad":canton,"ciudadid":cantonid,"parroquia":parroquia,"parroquiaid":parroquiaid,
                              "sexo":sexo,"estadocivil":estadocivil,'fechanacimiento':str(fechanacimiento)}]
                    resultado['lista'] = lista
                    resultado['estudios'] = datos
                    resultado['cursos'] = cursos
                    resultado['idiomas'] = idiomas
                    return HttpResponse(json.dumps(resultado),content_type="application/json")

                except Exception as ex:
                    transaction.savepoint_rollback(sid)
                    return HttpResponse(json.dumps({"result":"bad","error":str(ex)}), content_type="application/json")
            elif action == 'consultapersona':
                sid = transaction.savepoint()
                try:
                    datos = []
                    canton = ''
                    cantonid = ''
                    parroquia = ''
                    parroquiaid = ''
                    nombres = ''
                    apellido1 = ''
                    apellido2 = ''
                    pasaporte = ''
                    cedula = ''
                    email = ''
                    emailinst = ''
                    celular = ''
                    convecional = ''
                    sexo = 'FEMENINO'
                    direccion = ''
                    fechanacimiento = ''
                    estadocivil = ''
                    online = ''
                    conduccion = ''
                    rolpersona = ''
                    cedrequest = request.POST['cedula']
                    rolbusq  = request.POST['rol']
                    if ViewPersonasAdmProAlu.objects.filter(cedula=cedrequest,rol=rolbusq).exclude(cedula='').exclude(cedula=None).exists():
                        viewpersonasadmproalu = ViewPersonasAdmProAlu.objects.filter(cedula=cedrequest,rol=rolbusq).exclude(cedula='').exclude(cedula=None).order_by('rol')
                    elif ViewPersonasAdmProAlu.objects.filter(pasaporte=cedrequest).exclude(pasaporte='',rol=rolbusq).exclude(pasaporte=None).exists():
                        viewpersonasadmproalu = ViewPersonasAdmProAlu.objects.filter(pasaporte=cedrequest,rol=rolbusq).exclude(pasaporte='').exclude(pasaporte=None).order_by('rol')
                    else:
                        return HttpResponse(json.dumps({"result":"bad","error":str("NO EXISTE INFORMACION")}), content_type="application/json")
                    for i in viewpersonasadmproalu:

                        if i.nombres:
                            nombres = i.nombres
                        if i.apellido1:
                            apellido1 = i.apellido1
                        if i.apellido2:
                            apellido2 = i.apellido2
                        if i.email:
                            email = i.email
                        if i.emailinst:
                            emailinst = i.emailinst
                        if i.telefono:
                            celular = i.telefono
                        if i.telefono_conv:
                            convecional = i.telefono_conv

                        if i.cantonresid_id:
                          canton = i.canton
                          cantonid = i.cantonresid_id
                        if i.parroquia_id:
                          parroquia = i.parroquia
                          parroquiaid = i.parroquia_id
                        if i.sexo:
                          sexo = i.sexo
                        diring = False
                        if i.direccion:
                            diring = True
                            direccion = i.direccion
                        if i.direccion2:
                            if direccion and diring:
                                direccion = direccion +" y " + i.direccion2
                            else:
                                direccion = i.direccion2
                        if i.pasaporte:
                            pasaporte = i.pasaporte
                        else:
                            cedula = i.cedula
                        if i.estadocivil:
                            estadocivil = i.estadocivil

                        if i.fechanacimiento:
                            fechanacimiento = i.fechanacimiento
                        rolpersona = i.rol
                        online = i.online
                        conduccion = i.conduccion

                    resultado = {}
                    resultado['result'] = "ok"
                    lista = [{"nombres": nombres,"apellido1": apellido1,
                              "apellido2": apellido2,"cedula": cedula,"conduccion": conduccion,"online": online,
                              "pasaporte": pasaporte,"emailinst": emailinst,"email": email,
                              "direccion": direccion ,"celular": celular ,"telefono": convecional,
                              "ciudad":canton,"ciudadid":cantonid,"parroquia":parroquia,"parroquiaid":parroquiaid,
                              "sexo":sexo,"estadocivil":estadocivil,'fechanacimiento':str(fechanacimiento),'rolpersona':rolpersona}]
                    resultado['lista'] = lista
                    return HttpResponse(json.dumps(resultado),content_type="application/json")

                except Exception as ex:
                    transaction.savepoint_rollback(sid)
                    return HttpResponse(json.dumps({"result":"bad","error":str(ex)}), content_type="application/json")
            elif action == 'obtengraduados':
                try:
                    listagraduados=[]
                    idinscripube = json.loads(request.POST["idinscrip"])
                    if Graduado.objects.filter().exclude(inscripcion__id__in=idinscripube).exists():
                        idinscrip = Graduado.objects.filter().exclude(inscripcion__id__in=idinscripube).values('inscripcion').distinct('inscripcion')

                        for i in Inscripcion.objects.filter(id__in=idinscrip).exclude(id__in=idinscripube).order_by('id')[:1000]:
                            graduado = Graduado.objects.filter(inscripcion__carrera=i.carrera,inscripcion=i)[:1].get()
                            listagraduados.append({"nombres": i.persona.nombres, "apellido1": i.persona.apellido1, "apellido2": i.persona.apellido2, "email": i.persona.email, "nacimiento": str(i.persona.nacimiento),
                                                   "email1": i.persona.email1, "email2": i.persona.email2, "sexo": str(i.persona.sexo.id) if i.persona.sexo else None ,
                                                   "celular": i.persona.telefono,  "telefono": i.persona.telefono_conv,"estcolegio": str(i.estcolegio.id) if i.estcolegio else None,
                                                   "especialidad": str(i.especialidad.id) if i.especialidad else None, "calleprincipal": i.persona.direccion,  "callesecundaria": i.persona.direccion2,
                                                   "canton": str(i.persona.cantonresid.id)  if i.persona.cantonresid else None, "provincia": str(i.persona.provinciaresid.id)  if i.persona.provinciaresid else None,
                                                   "parroquia": str(i.persona.parroquia.id) if i.persona.parroquia else None, "sector": str(i.persona.sectorresid.id)  if i.persona.sectorresid else None,
                                                   "tiposangre": str(i.persona.sangre.id)  if i.persona.sangre else None, "tienediscapacidad": i.tienediscapacidad,
                                                   "provincianacmiento": str(i.persona.provincia.id)  if i.persona.provincia else None, "cantonnacimiento": str(i.persona.canton.id)  if i.persona.canton else None,
                                                   "nombrepadre": i.persona.padre, "nombremadre": i.persona.madre, "extranjero": True if i.persona.cedula else False,
                                                   "cedula": i.persona.cedula if i.persona.cedula else i.persona.pasaporte, "nacionalidad": str(i.persona.nacionalidad.id) if i.persona.nacionalidad else None,
                                                   "numerodomicilio": i.persona.num_direccion, "carrera": i.carrera.nombre, "idinscripitb": str(i.id) , "fechagrad": str(graduado.fechagraduado) })

                    else:
                        return HttpResponse(json.dumps({"result":"bad","error":str("NO EXISTE INFORMACION")}),content_type="application/json")


                    resultado = {}
                    resultado['result'] = "ok"

                    resultado['listagraduados'] = listagraduados
                    return HttpResponse(json.dumps(resultado), content_type="application/json")

                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad","error":str(ex)}),content_type="application/json")


            elif action == 'obtencongreso':
                try:
                    listacongreso=[]
                    carreras = [16, 8,9,11,12,13,14,16,17,18,19,20,25,26,38]
                    idinscricongreso = json.loads(request.POST["idinscrip"])
                    if Inscripcion.objects.filter(carrera__id__in=carreras).exclude(id__in=idinscricongreso).exists():
                        idinscrip = Inscripcion.objects.filter(carrera__id__in=carreras).exclude(id__in=idinscricongreso).values('id').distinct('id')

                        for i in Inscripcion.objects.filter(id__in=idinscrip,carrera__id__in=carreras).exclude(id__in=idinscricongreso).order_by('id')[:1000]:
                            listacongreso.append({"nombres": i.persona.nombres, "apellido1": i.persona.apellido1, "apellido2": i.persona.apellido2, "email": i.persona.email, "nacimiento": str(i.persona.nacimiento),
                                                   "email1": i.persona.email1, "email2": i.persona.email2, "sexo": str(i.persona.sexo.id) if i.persona.sexo else None ,
                                                   "celular": i.persona.telefono,  "telefono": i.persona.telefono_conv,"estcolegio": str(i.estcolegio.id) if i.estcolegio else None,
                                                   "especialidad": str(i.especialidad.id) if i.especialidad else None, "calleprincipal": i.persona.direccion,  "callesecundaria": i.persona.direccion2,
                                                   "canton": str(i.persona.cantonresid.id)  if i.persona.cantonresid else None, "provincia": str(i.persona.provinciaresid.id)  if i.persona.provinciaresid else None,
                                                   "parroquia": str(i.persona.parroquia.id) if i.persona.parroquia else None, "sector": str(i.persona.sectorresid.id)  if i.persona.sectorresid else None,
                                                   "tiposangre": str(i.persona.sangre.id)  if i.persona.sangre else None, "tienediscapacidad": i.tienediscapacidad,
                                                   "provincianacmiento": str(i.persona.provincia.id)  if i.persona.provincia else None, "cantonnacimiento": str(i.persona.canton.id)  if i.persona.canton else None,
                                                   "nombrepadre": i.persona.padre, "nombremadre": i.persona.madre, "extranjero": True if i.persona.cedula else False,
                                                   "cedula": i.persona.cedula if i.persona.cedula else i.persona.pasaporte, "nacionalidad": str(i.persona.nacionalidad.id) if i.persona.nacionalidad else None,
                                                   "numerodomicilio": i.persona.num_direccion, "carrera": i.carrera.nombre, "idinscripitb": str(i.id)  })

                    else:
                        return HttpResponse(json.dumps({"result":"bad","error":str("NO EXISTE INFORMACION")}),content_type="application/json")


                    resultado = {}
                    resultado['result'] = "ok"

                    resultado['listacongreso'] = listacongreso
                    return HttpResponse(json.dumps(resultado), content_type="application/json")

                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad","error":str(ex)}),content_type="application/json")
            elif action =='consultains':
                try:

                    if ViewInscripcionParaIngles.objects.filter(cedula=request.POST["cedula"]):
                        for ins in ViewInscripcionParaIngles.objects.filter(cedula=request.POST["cedula"]):
                            if request.POST["carrera"] in elimina_tildes(ins.nomcarrera).upper():
                                return HttpResponse(json.dumps({"result":"ok","carreradescrip":elimina_tildes(ins.nomcarrera).upper()}),content_type="application/json")
                            else:
                                return HttpResponse(json.dumps({"result":"ok","carreradescrip":elimina_tildes(ins.nomcarrera).upper()}),content_type="application/json")

                    elif ViewInscripcionParaIngles.objects.filter(pasaporte=request.POST["pasaporte"]):
                        for ins in ViewInscripcionParaIngles.objects.filter(pasaporte=request.POST["pasaporte"]):
                            if request.POST["carrera"] in elimina_tildes(ins.nomcarrera).upper():
                                return HttpResponse(json.dumps({"result":"ok","carreradescrip":elimina_tildes(ins.nomcarrera).upper()}),content_type="application/json")
                            else:
                                return HttpResponse(json.dumps({"result":"ok","carreradescrip":elimina_tildes(ins.nomcarrera).upper()}),content_type="application/json")
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad","error":str(ex)}),content_type="application/json")
            elif action == 'perfil':
                try:
                    data = {}
                    if not 'identificacion' in request.POST:
                        return HttpResponse(json.dumps( {'result': 'bad', 'message': 'No ingreso una identificacion'}),
                                            content_type="application/json")
                    identificacion = request.POST['identificacion']
                    datospersona = []
                    tipodoc = ''
                    perfil = []
                    viewpersonasadmproalu = None
                    if ViewPersonasAdmProAlu.objects.filter(cedula=identificacion).exclude(cedula='').exclude(cedula=None).exists():
                        tipodoc = 'cedula'
                        viewpersonasadmproalu = ViewPersonasAdmProAlu.objects.filter(cedula=identificacion).exclude(cedula='').exclude(cedula=None).order_by('rol')
                    elif ViewPersonasAdmProAlu.objects.filter(pasaporte=identificacion).exclude(pasaporte='').exclude(pasaporte=None).exists():
                        tipodoc = 'pasaporte'
                        viewpersonasadmproalu = ViewPersonasAdmProAlu.objects.filter(pasaporte=identificacion).exclude(pasaporte='').exclude(pasaporte=None).order_by('rol')
                    if not viewpersonasadmproalu:
                        return HttpResponse(json.dumps({"result":"bad","error":str("NO EXISTE INFORMACION")}), content_type="application/json")
                    for persona in viewpersonasadmproalu:
                        datospersona.append({'nombres': persona.nombres,
                                             'apellido1': persona.apellido1,
                                             'apellido2': persona.apellido2,
                                             'usuario': persona.usuario if persona.usuario else '',
                                             'cedula': persona.cedula,
                                             'pasaporte': persona.pasaporte,
                                             'emailinst': persona.emailinst,
                                             'email': persona.email,
                                             'email1': '',
                                             'email2': '',
                                             'celular': persona.telefono,
                                             'telefono': persona.telefono_conv,
                                             'nacionalidad': persona.nacionalidad,
                                             'perfiles': persona.rol,
                                             'direccion': persona.direccion,
                                             'extranjero': persona.extranjero,
                                             'tipo_identific': tipodoc,
                                             'tipobase': persona.tipobase,
                                             'ciudad': persona.canton
                                             })
                    data['datospersona'] = datospersona
                    data['result'] = 'ok'
                    return HttpResponse(json.dumps(data), content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({'status':False, 'message': 'error de Excepcion '+str(e)}), content_type="application/json")
            elif action == 'registrosComedor':
                try:
                    data = {}
                    if not 'identificacion' in request.POST:
                        return HttpResponse(json.dumps( {'result': 'bad', 'message': 'No ingreso una identificacion'}),
                                            content_type="application/json")
                    identificacion = request.POST['identificacion']
                    datospersona = []
                    tipodoc = ''
                    perfil = []
                    viewpersonasadmproalu = None
                    if ViewPersonasAdmProAlu.objects.filter(cedula=identificacion).exclude(cedula='').exclude(cedula=None).exists():
                        tipodoc = 'cedula'
                        viewpersonasadmproalu = ViewPersonasAdmProAlu.objects.filter(cedula=identificacion).exclude(cedula='').exclude(cedula=None).order_by('rol')
                    elif ViewPersonasAdmProAlu.objects.filter(pasaporte=identificacion).exclude(pasaporte='').exclude(pasaporte=None).exists():
                        tipodoc = 'pasaporte'
                        viewpersonasadmproalu = ViewPersonasAdmProAlu.objects.filter(pasaporte=identificacion).exclude(pasaporte='').exclude(pasaporte=None).order_by('rol')
                    if not viewpersonasadmproalu:
                        return HttpResponse(json.dumps({"result":"bad","error":str("NO EXISTE INFORMACION")}),content_type="application/json")

                    perfil = []

                    if viewpersonasadmproalu.filter().exclude(rol = 'ESTUDIANTE'):
                        persona = viewpersonasadmproalu.filter().exclude(rol='ESTUDIANTE')[:1].get()
                        perfil.append({'perfil': 'ADMINISTRATIVO'})
                    else:
                        persona = viewpersonasadmproalu.filter(rol='ESTUDIANTE')[:1].get()
                        perfil.append({'perfil': 'ALUMNO'})

                    datospersona.append({'nombres': persona.nombres,
                                         'apellido1': persona.apellido1,
                                         'apellido2': persona.apellido2,
                                         'usuario': persona.usuario if persona.usuario else '',
                                         'cedula': persona.cedula,
                                         'pasaporte': persona.pasaporte,
                                         'emailinst': persona.emailinst,
                                         'email': persona.email,
                                         'email1': '',
                                         'email2': '',
                                         'celular': persona.telefono,
                                         'telefono': persona.telefono_conv,
                                         'nacionalidad': persona.nacionalidad,
                                         'perfiles': perfil,
                                         'direccion': persona.direccion,
                                         'extranjero': persona.extranjero,
                                         'tipo_identific': tipodoc,
                                         'tipobase': persona.tipobase,
                                         'ciudad': persona.canton
                                             })
                    data['datospersona'] = datospersona
                    data['result'] = 'ok'
                    return HttpResponse(json.dumps(data), content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({'status':False, 'message': 'error de Excepcion '+str(e)}), content_type="application/json")

            elif action == 'personalRegistrado':
                try:
                    data = {}
                    noregistrados = []
                    registradosalumno = []
                    registradosadmin = []
                    if not 'dnis' in request.POST:
                        return HttpResponse(json.dumps({'result': 'bad', 'message': 'No ingreso una identificacion'}),
                                            content_type="application/json")
                    arraydnis = request.POST['dnis'].split(',')
                    for ar in arraydnis:
                        viewpersonasadmproalu = None
                        if ViewPersonasAdmProAlu.objects.filter(cedula=ar).exclude(cedula='').exclude(cedula=None).exists() :
                            if ViewPersonasAdmProAlu.objects.filter(cedula=ar).exclude(cedula='').exclude(cedula=None).exclude(rol='ESTUDIANTE'):
                                # perfil.append({'perfil': 'ADMINISTRATIVO'})
                                registradosadmin.append(ar)
                            else:
                                # perfil.append({'perfil': 'ALUMNO'})
                                registradosalumno.append(ar)

                        elif ViewPersonasAdmProAlu.objects.filter(pasaporte=ar).exclude(pasaporte='').exclude(pasaporte=None).exists():
                            if ViewPersonasAdmProAlu.objects.filter(pasaporte=ar).exclude(pasaporte='').exclude(pasaporte=None).exclude(rol='ESTUDIANTE'):
                                # perfil.append({'perfil': 'ADMINISTRATIVO'})
                                registradosadmin.append(ar)
                            else:
                                # perfil.append({'perfil': 'ALUMNO'})
                                registradosalumno.append(ar)
                        else:
                            noregistrados.append(ar)
                    data['noregistrados'] = noregistrados
                    data['registradosalumno'] = registradosalumno
                    data['registradosadmin'] = registradosadmin
                    data['result'] = 'ok'
                    return HttpResponse(json.dumps(data), content_type="application/json")
                except Exception as e:
                    print('----------------------------')
                    print('Error api comedor: '+str(e))
                    return HttpResponse(json.dumps({'status': False, 'message': 'error de Excepcion ' + str(e)}),
                                        content_type="application/json")

            elif action == 'resetclave':
                try:
                    from django.utils.encoding import force_str
                    user = User.objects.get(username=request.POST['username'])
                    if user is not None:
                        if user.is_active:
                            user.set_password(request.POST['documento'])
                            # Obtain client ip address
                            client_address = ip_client_address(request)

                            # Log de ADICIONAR PROFESOR
                            LogEntry.objects.log_action(
                                user_id=user.pk,
                                content_type_id=ContentType.objects.get_for_model(user).pk,
                                object_id=user.id,
                                object_repr=force_str(user),
                                action_flag=CHANGE,
                                change_message='Reseteado contrasena desde nominas (' + client_address + ')')
                            return HttpResponse(json.dumps({'result': 'ok', 'error': ''}), content_type="application/json")
                        return HttpResponse(json.dumps({'result': 'bad', 'error': 'el usuario no esta activo'}), content_type="application/json")
                    return HttpResponse(json.dumps({'result': 'bad', 'error': u'No existe el usuario'}),
                                        content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({'result': 'bad', 'error': u'Error en la excepcion: '+str(e)}), content_type="application/json")
    # else:
        if 'a' in request.GET:
            action=request.GET['a']
            if action=='printusers':
                usuarios = []
                g = Group.objects.get(pk=GRUPO_USUARIOS_IMPRESION)
                for u in g.user_set.all():
                    usuarios.append({'id': u.id, 'username': u.username, 'fullname': u.get_full_name()})
                return HttpResponse(json.dumps(usuarios),content_type="application/json")
            elif action=='printstart':
                for i in Impresion.objects.filter(usuario__id=request.GET['usuario']):
                    i.impresa = True
                    i.save()
                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            elif action=='asignatutor':
                idnivel = TutorCongreso.objects.filter().distinct('nivel').values('nivel')
                for n in Nivel.objects.filter(id__in=idnivel):
                    idmatricula = TutorMatricula.objects.filter().distinct('matricula').values('matricula')
                    for m in Matricula.objects.filter(nivel=n).exclude(id__in=idmatricula):
                        tutor = None
                        for t in TutorCongreso.objects.filter(nivel=n).order_by('numasignado','fechaasign'):
                            numasignado = t.numasignado + 1
                            if t.cantidad >= numasignado:
                                tutor = t
                                break
                        if tutor:
                            tutor.numasignado = tutor.numasignado + 1
                            tutor.fechaasign = datetime.now()
                            tutor.save()
                            tutormatricula = TutorMatricula(matricula = m,
                                                            tutorcongreso = tutor,
                                                            fecha = datetime.now())
                            tutormatricula.save()
                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")

            elif action ==   'consultapromo':
                try:
                    identificacion = request.GET['identificacion']
                    inscripcion=None
                    if Inscripcion.objects.filter(persona__cedula=identificacion,persona__usuario__is_active=True):
                        inscripcion =Inscripcion.objects.filter(persona__cedula=identificacion,persona__usuario__is_active=True)[:1].get()
                    elif Inscripcion.objects.filter(persona__pasaporte=identificacion,persona__usuario__is_active=True):
                        inscripcion = Inscripcion.objects.filter(persona__pasaporte=identificacion,persona__usuario__is_active=True)[:1].get()
                    if inscripcion:
                        hoy=datetime.now().date()
                        if PromoGym.objects.filter(inscripcion=inscripcion,inicio__lte=hoy,fin__gte=hoy,registrada=None):
                            promo = PromoGym.objects.filter(inscripcion=inscripcion,inicio__lte=hoy,fin__gte=hoy,registrada=None).order_by('id')[:1].get()
                            return HttpResponse(json.dumps({'mensaje': 'ok','id':str(promo.id) }), content_type="application/json")
                        else:
                            return HttpResponse(json.dumps({'mensaje': 'bad' }), content_type="application/json")
                    return HttpResponse(json.dumps({'mensaje': 'bad' }), content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({'mensaje': str(e) }), content_type="application/json")


            elif action == 'guardapromo':
                try:
                    if PromoGym.objects.filter(pk=int(request.GET['idpromo'])).exists():
                        promo = PromoGym.objects.filter(pk=int(request.GET['idpromo']))[:1].get()
                        promo.registrada = datetime.now().date()
                        promo.save()
                        return HttpResponse(json.dumps({'mensaje': 'ok' }), content_type="application/json")
                    return HttpResponse(json.dumps({'mensaje': 'bad' }), content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({'mensaje': 'error','error':str(e) }), content_type="application/json")

            elif action=='logincrm':
                try:
                    user = authenticate(username=str(request.GET['user']).lower(), password=request.GET['pass'])
                    if user is not None:
                        return HttpResponse(json.dumps({"result":"ok","id":str(user.id)}),content_type="application/json")
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":str(ex)}), content_type="application/json")

            elif action=='eliminareferido':
                try:
                    referdio = None
                    if ReferidosInscripcion.objects.filter(cedula=request.GET['cedula'],online=False).exists():
                        referdio = ReferidosInscripcion.objects.get(cedula=request.GET['cedula'],online=False)

                    if ReferidosInscripcion.objects.filter(pasaporte=str(request.GET['cedula']).upper(),online=False).exists():
                        referdio = ReferidosInscripcion.objects.get(pasaporte=str(request.GET['cedula']).upper())

                    if referdio!=None:
                        referdio.delete()
                        return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

                except Exception as ex:
                    return HttpResponse(json.dumps({"result":str(ex)}), content_type="application/json")

            elif action=='eliminareferidonline':
                try:
                    referdio = None
                    if ReferidosInscripcion.objects.filter(cedula=request.GET['cedula'],online=True).exists():
                        referdio = ReferidosInscripcion.objects.get(cedula=request.GET['cedula'])

                    if ReferidosInscripcion.objects.filter(pasaporte=str(request.GET['cedula']).upper(),online=True).exists():
                        referdio = ReferidosInscripcion.objects.get(pasaporte=str(request.GET['cedula']).upper())

                    if referdio!=None:
                        referdio.delete()
                        return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

                except Exception as ex:
                    return HttpResponse(json.dumps({"result":str(ex)}), content_type="application/json")



            elif action=='addreferidoprospecto':
                try:

                    if ReferidosInscripcion.objects.filter(cedula=request.GET['identificacion'],online=False).exists():
                        return HttpResponse(json.dumps({"result":"bad","message":"Ya existe el referido"}),content_type="application/json")

                    if ReferidosInscripcion.objects.filter(pasaporte=str(request.GET['identificacion']).upper(),online=True).exists():
                        return HttpResponse(json.dumps({"result":"bad","message":"Ya existe el referido"}),content_type="application/json")


                    cedula=''
                    pasaporte=''

                    if request.GET['extranjero']=='true':
                        extrajero=True
                        pasaporte=request.GET['identificacion']
                    else:
                        extrajero=False
                        cedula=request.GET['identificacion']

                    if int(request.GET['personaid'])>0:
                        persona=Persona.objects.get(id=int(request.GET['personaid']))
                        inscrip=Inscripcion.objects.filter(persona=persona)[:1].get()
                    else:
                        inscrip=None

                    referido=ReferidosInscripcion(nombres=elimina_tildes(request.GET['nombres']),
                                                 apellido1=elimina_tildes(request.GET['apellido1']),
                                                 apellido2=elimina_tildes(request.GET['apellido2']),extranjero=extrajero,
                                                 cedula=cedula,pasaporte=pasaporte,sexo_id=int(request.GET['sexo']),
                                                 telefono=request.GET['celular'],telefono_conv=request.GET['telefono'],
                                                 email=request.GET['email'],fecha=datetime.now().date(),
                                                 inscripcion=inscrip,carrera_id=int(request.GET['carreraid']),
                                                 modalidad_id=int(request.GET['modalidadid']),
                                                 idprospecto=int(request.GET['prospectoid'])
                                                 )
                    referido.save()

                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")


                except Exception as ex:
                    return HttpResponse(json.dumps({"result":str(ex)}), content_type="application/json")


            elif action=='actualizapreins':
                try:

                    url_pre = URL_PRE_INSCRIPCION
                    ruta_pre = RUTA_PRE_INSCRIPCION
                    url = (url_pre)

                    # Crea el archivo dato.txt
                    # urllib.urlretrieve(url,"dato.txt")
                    urllib.urlretrieve(url,ruta_pre)
                    #
                    # Archivo web
                    # SITE_ROOT = os.path.dirname(os.path.realpath(__file__))

                    # csv_filepathname= "dato.txt"

                    # csv_filepathname="dato.txt"
                    csv_filepathname=ruta_pre

                    # your_djangoproject_home=os.path.split(SITE_ROOT)[0]

                    # sys.path.append(your_djangoproject_home)
                    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

                    dataReader = csv.reader(open(csv_filepathname), delimiter=';')

                    LINE = -1
                    for row in dataReader:
                        try:
                            if row:
                                # LINE += 1
                                # if LINE==1:
                                #     continue
                                cedula = (row[8].lstrip().strip()).zfill(10)
                                datos = requests.get('https://crm.itb.edu.ec/api',
                                            params={'a': 'verificarprospecto', 'identificacion': cedula},verify=False)
                                if datos.status_code == 200:
                                   datos=datos.json()
                                   if datos['result']=='ok':
                                        canton = None
                                        provincia = None
                                        tipoanuncio = None
                                        if Carrera.objects.filter(nombre=row[0].upper()).exists():
                                            carrera = Carrera.objects.filter(nombre=row[0].upper())[:1].get()
                                        else:
                                            carrera = Carrera.objects.all()[:1].get()

                                        if Modalidad.objects.filter(nombre=row[1].upper()).exists():
                                            modalidad= Modalidad.objects.filter(nombre=row[1].upper())[:1].get()
                                        else:
                                            modalidad = Modalidad.objects.all()[:1].get()

                                        if row[25] != '':
                                            if Canton.objects.filter(pk=row[25]).exists():
                                                canton= Canton.objects.filter(pk=row[25])[:1].get()
                                        if row[26] != '':
                                            if Provincia.objects.filter(pk=row[26]).exists():
                                                provincia= Provincia.objects.filter(pk=row[26])[:1].get()
                                        try:
                                            if row[27] != '':
                                                if TipoAnuncio.objects.filter(pk=row[27]).exists():
                                                    tipoanuncio= TipoAnuncio.objects.filter(pk=row[27])[:1].get()
                                        except :
                                            pass

                                        # if Sesion.objects.filter(nombre=row[2].upper()).exists():
                                        #     seccion= Sesion.objects.filter(nombre=row[2].upper())[:1].get()
                                        # else:
                                        #     seccion = Sesion.objects.all()[:1].get()

                                        if Grupo.objects.filter(nombre=row[3].upper()).exists():
                                            grupo= Grupo.objects.filter(nombre=row[3].upper())[:1].get()
                                            seccion = grupo.sesion
                                        else:
                                            grupo = Grupo.objects.all()[:1].get()
                                            seccion = Sesion.objects.all()[:1].get()

                                        if Sexo.objects.filter(nombre=row[10].upper()).exists():
                                            sexo= Sexo.objects.filter(nombre=row[10].upper())[:1].get()
                                        else:
                                            sexo = Sexo.objects.all()[:1].get()

                                        if Especialidad.objects.filter(nombre=row[17].upper()).exists():
                                            especialidad= Especialidad.objects.filter(nombre=row[17].upper())[:1].get()
                                        else:
                                            especialidad = Especialidad.objects.all()[:1].get()


                                        hoy = str(datetime.date(datetime.now()))
                                        caducidad = (row[20])
                                        try:
                                            if (caducidad>=hoy):
                                                horaregnuv = None
                                                if row[19] != '':
                                                    horaregnuv = row[19]

                                                if not PreInscripcion.objects.filter(cedula=cedula,carrera=carrera).exists():
                                                    preinscripcion = PreInscripcion(carrera=carrera,
                                                                    modalidad=modalidad,
                                                                    seccion=seccion,
                                                                    grupo=grupo,
                                                                    inicio_clases=(row[4]),
                                                                    nombres=row[5],
                                                                    apellido1=row[6],
                                                                    apellido2=row[7],
                                                                    cedula=cedula,
                                                                    nacimiento=row[9],
                                                                    email=(row[11].lower()),
                                                                    sexo=sexo,
                                                                    telefono=row[12],
                                                                    celular=row[14],
                                                                    colegio=row[16],
                                                                    especialidad=especialidad,
                                                                    fecha_registro=row[18],
                                                                    hora_registro=horaregnuv,
                                                                    fecha_caducidad=row[20],
                                                                    calleprincipal=row[22],
                                                                    callesecundaria=row[23],
                                                                    numerocasa=row[24],
                                                                    canton=canton,
                                                                    provincia=provincia,
                                                                    tipoanuncio=tipoanuncio)
                                                else:
                                                    preinscripcion=PreInscripcion.objects.filter(cedula=cedula,carrera=carrera)[:1].get()
                                                    preinscripcion.carrera=carrera
                                                    preinscripcion.modalidad=modalidad
                                                    preinscripcion.grupo=grupo
                                                    preinscripcion.inicio_clases=row[4]
                                                    preinscripcion.nombres=row[5]
                                                    preinscripcion.apellido1=row[6]
                                                    preinscripcion.apellido2=row[7]
                                                    preinscripcion.cedula=cedula
                                                    preinscripcion.nacimiento=row[9]
                                                    preinscripcion.email=row[11].lower()
                                                    preinscripcion.sexo=sexo
                                                    preinscripcion.telefono=row[12]
                                                    preinscripcion.celular=row[14]
                                                    preinscripcion.colegio=row[16]
                                                    preinscripcion.especialidad=especialidad
                                                    preinscripcion.fecha_registro=row[18]
                                                    preinscripcion.hora_registro=horaregnuv
                                                    preinscripcion.fecha_caducidad=row[20]
                                                    preinscripcion.calleprincipal=row[22]
                                                    preinscripcion.callesecundaria=row[23]
                                                    preinscripcion.numerocasa=row[24]
                                                    preinscripcion.canton=canton
                                                    preinscripcion.provincia=provincia
                                                    preinscripcion.tipoanuncio = tipoanuncio


                                                if Graduado.objects.filter(inscripcion__persona__cedula=preinscripcion.cedula).exists():
                                                   ins = Inscripcion.objects.filter(persona__cedula=preinscripcion.cedula).order_by('-id')[:1].get()
                                                   if Graduado.objects.filter(inscripcion=ins).exists():
                                                       preinscripcion.repetido = True
                                                       preinscripcion.save()
                                                       print(preinscripcion.nombres + " " +preinscripcion.apellido1+" Guardado repetido")
                                                if Graduado.objects.filter(inscripcion__persona__pasaporte=preinscripcion.cedula).exists():
                                                   ins = Inscripcion.objects.filter(persona__pasaporte=preinscripcion.cedula).order_by('-id')[:1].get()
                                                   if Graduado.objects.filter(inscripcion=ins).exists():
                                                       preinscripcion.repetido = True
                                                       preinscripcion.save()
                                                       print(preinscripcion.nombres + " " +preinscripcion.apellido1+" Guardado repetido")

                                                if Inscripcion.objects.filter(persona__cedula=preinscripcion.cedula,carrera=carrera).exists():
                                                    for i in Inscripcion.objects.filter(persona__cedula=preinscripcion.cedula):
                                                        for ic in i.inscripciongrupo_set.all():
                                                            if not i.matricula():
                                                                if ic.grupo.carrera == preinscripcion.grupo.carrera:
                                                                    preinscripcion.repetido=True
                                                                    preinscripcion.save()
                                                                    print(preinscripcion.nombres + " " +preinscripcion.apellido1+" Guardado repetido")
                                                if PreInscripcion.objects.filter(cedula=cedula,carrera=carrera).count() < 1:
                                                    preinscripcion.save()
                                                    print(preinscripcion.nombres + " " +preinscripcion.apellido1)
                                        except Exception as ex:
                                           try:
                                                email_error(str(ex) + "ERROR1 Ced: " +str(row[8])+ " len" +str(len(row))+ " cont.len" +str(len(row[len(row)])),url_pre)
                                           except Exception as e:
                                               pass
                        except Exception as ex:
                            try:
                                email_error(str(ex) + "ERROR2 Ced: " +str(row[8])+ " len" +str(len(row))+ " cont.len" +str(len(row[len(row)])),url_pre)
                            except Exception as e:
                                pass


                    return HttpResponse(json.dumps({"result":"ok"}), content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":str(ex)}), content_type="application/json")


            elif action=='printdoc':
                docs = []
                for i in Impresion.objects.filter(usuario__id=request.GET['usuario'], impresa=False):
                    docs.append(json.loads(i.contenido))
                return HttpResponse(json.dumps(docs), content_type="application/json")
            elif action=='printdone':
                impresion = Impresion.objects.get(pk=request.GET['id'])
                impresion.impresa = True
                impresion.save()
                return HttpResponse(json.dumps({"result":"ok"}), content_type="application/json")
            elif action=='consapipedago':
                try:
                    datos = requests.get('http://api.pedagogia.edu.ec/',params={'': '' },verify=False)
                    if datos.status_code==200:
                        return HttpResponse(json.dumps({"result":"ok"}), content_type="application/json")
                    dat = datos.json()
                    return HttpResponse(json.dumps({"result":str(datos.status_code)+' '+dat['error']}), content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":str(ex)}), content_type="application/json")

            elif action == 'datos_finanzas':
                datos = []
                ban = 0
                b=0

                data = []
                mensaje = []
                try:
                    cedula = request.GET['ced']
                    if  request.GET['op'] == '0':
                        if Inscripcion.objects.filter(persona__pasaporte=cedula).exists():
                            # ins = Inscripcion.objects.filter(persona__cedula=cedula)[:1].get()
                            for ins in Inscripcion.objects.filter(persona__pasaporte=cedula):
                                    # mensaje.append({'codigo':0,'mensaje':'ok'})
                                for rubro in ins.rubros_pendientes():
                                    datos = []
                                    ban = 1
                                    datos.append(rubro.nombre())
                                    datos.append(rubro.fechavence.strftime("%d-%m-%Y"))
                                    datos.append(rubro.adeudado())
                                    data.append(datos)
                                if ban == 1:
                                    return HttpResponse(json.dumps({'codigo':0,'mensaje':'ok','rubros':data }),content_type="application/json")
                                else:
                                    return HttpResponse(json.dumps({'codigo':2,'mensaje':'No tiene valores por pagar'}),content_type="application/json")
                            if b==0:
                                return HttpResponse(json.dumps({'codigo':'7','mensaje':'No Esta matriculado'}),content_type="application/json")

                            # else:
                            #     return HttpResponse(json.dumps({'codigo':7,'mensaje':'No Esta matriculado'}),content_type="application/json")
                        else:
                            return HttpResponse(json.dumps({'codigo':1,'mensaje':'Cliente no existe'}),content_type="application/json")
                    else:
                        if Inscripcion.objects.filter(persona__cedula=cedula).exists():
                            # ins = Inscripcion.objects.filter(persona__cedula=cedula)[:1].get()
                            for ins in Inscripcion.objects.filter(persona__cedula=cedula):
                                    # mensaje.append({'codigo':0,'mensaje':'ok'})
                                for rubro in ins.rubros_pendientes():
                                    datos = []
                                    ban = 1
                                    datos.append(rubro.nombre())
                                    datos.append(rubro.fechavence.strftime("%d-%m-%Y"))
                                    datos.append(rubro.adeudado())
                                    data.append(datos)
                                if ban == 1:
                                    return HttpResponse(json.dumps({'codigo':0,'mensaje':'ok','rubros':data }),content_type="application/json")
                                else:
                                    return HttpResponse(json.dumps({'codigo':2,'mensaje':'No tiene valores por pagar'}),content_type="application/json")
                            if b==0:
                                return HttpResponse(json.dumps({'codigo':'7','mensaje':'No Esta matriculado'}),content_type="application/json")

                            # else:
                            #     return HttpResponse(json.dumps({'codigo':7,'mensaje':'No Esta matriculado'}),content_type="application/json")
                        else:
                            return HttpResponse(json.dumps({'codigo':1,'mensaje':'Cliente no existe'}),content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({'codigo':1,'mensaje':'Error' + str(e)}),content_type="application/json")

            elif action == 'datos_ingles':
                datos = []
                ban = 0
                b=0

                data = []
                mensaje = []
                try:
                    cedula = request.GET['ced']
                    if request.GET['op'] == '0':
                        if EvaluacionITB.objects.filter(materiaasignada__matricula__inscripcion__persona__pasaporte=cedula).exists():
                            for e in  EvaluacionITB.objects.filter(materiaasignada__matricula__inscripcion__persona__pasaporte=cedula):
                                if e.materiaasignada.materia.nueva_acta_buck():
                                    datos = []
                                    datos.append(e.materiaasignada.materia.asignatura.nombre)
                                    datos.append(e.n1)
                                    datos.append(e.n2)
                                    datos.append(e.n3)
                                    datos.append(e.n4)
                                    datos.append(str(e.estado))
                                    data.append(datos)
                            return HttpResponse(json.dumps({'codigo':0,'mensaje':'ok','notas':data }),content_type="application/json")
                        else:
                            return HttpResponse(json.dumps({'codigo':'7','mensaje':'No Esta matriculado'}),content_type="application/json")
                    else:
                        if EvaluacionITB.objects.filter(materiaasignada__matricula__inscripcion__persona__cedula=cedula).exists():
                            for e in  EvaluacionITB.objects.filter(materiaasignada__matricula__inscripcion__persona__cedula=cedula):
                                if e.materiaasignada.materia.nueva_acta_buck():
                                    datos = []
                                    datos.append(e.materiaasignada.materia.asignatura.nombre)
                                    datos.append(e.n1)
                                    datos.append(e.n2)
                                    datos.append(e.n3)
                                    datos.append(e.n4)
                                    datos.append(str(e.estado))
                                    data.append(datos)
                            return HttpResponse(json.dumps({'codigo':0,'mensaje':'ok','notas':data }),content_type="application/json")
                        else:
                            return HttpResponse(json.dumps({'codigo':'7','mensaje':'No Esta matriculado'}),content_type="application/json")

                except Exception as e:
                    return HttpResponse(json.dumps({'codigo':1,'mensaje':'Error' + str(e)}),content_type="application/json")
            elif action == 'online_ingles':
                datos = []
                ban = 0
                b=0

                data = []
                mensaje = []
                try:
                    cedula = request.GET['ced']
                    if request.GET['op'] == '0':
                        if EvaluacionITB.objects.filter(materiaasignada__matricula__inscripcion__persona__pasaporte=cedula,materiaasignada__matricula__inscripcion__sgaonline=True).exists():
                            for e in  EvaluacionITB.objects.filter(materiaasignada__matricula__inscripcion__persona__pasaporte=cedula,materiaasignada__matricula__inscripcion__sgaonline=True):
                                if e.materiaasignada.materia.nueva_acta_buck():
                                    datos = []
                                    datos.append(e.materiaasignada.materia.asignatura.nombre)
                                    datos.append(e.n1)
                                    datos.append(e.n2)
                                    datos.append(e.n3)
                                    datos.append(e.n4)
                                    datos.append(str(e.estado))
                                    data.append(datos)
                            return HttpResponse(json.dumps({'codigo':0,'mensaje':'ok','notas':data }), content_type ="application/json")
                        else:
                            return HttpResponse(json.dumps({'codigo':'7','mensaje':'No Esta matriculado'}), content_type="application/json")
                    else:
                        if EvaluacionITB.objects.filter(materiaasignada__matricula__inscripcion__persona__cedula=cedula,materiaasignada__matricula__inscripcion__sgaonline=True).exists():
                            for e in  EvaluacionITB.objects.filter(materiaasignada__matricula__inscripcion__persona__cedula=cedula,materiaasignada__matricula__inscripcion__sgaonline=True):
                                if e.materiaasignada.materia.nueva_acta_buck():
                                    datos = []
                                    datos.append(e.materiaasignada.materia.asignatura.nombre)
                                    datos.append(e.n1)
                                    datos.append(e.n2)
                                    datos.append(e.n3)
                                    datos.append(e.n4)
                                    datos.append(str(e.estado))
                                    data.append(datos)
                            return HttpResponse(json.dumps({'codigo':0,'mensaje':'ok','notas':data }), content_type="application/json")
                        else:
                            return HttpResponse(json.dumps({'codigo':'7','mensaje':'No Esta matriculado'}), content_type="application/json")

                except Exception as e:
                    return HttpResponse(json.dumps({'codigo':1,'mensaje':'Error' + str(e)}), content_type="application/json")
            elif action=='cajas':
                cajas = LugarRecaudacion.objects.all()
                return HttpResponse(json.dumps([model_to_dict(x) for x in cajas]), content_type="application/json")
            elif action=='facturas':
                caja = LugarRecaudacion.objects.get(pk=request.GET['caja'])
                facturas = []
                if Factura.objects.filter(caja=caja, impresa=False).exists():
                    facturas.append(Factura.objects.filter(caja=caja, impresa=False)[:1].get())
                return HttpResponse(json.dumps([representacion_factura(x) for x in facturas]),content_type="application/json")

            elif action=='facturasanuladas':
                facturascanceladas = []
                try:
                    for f in FacturaCancelada.objects.filter(fecha__month=request.GET['month'], fecha__year=request.GET['year']).order_by('id'):
                        if not f.sesion:
                            if FacturaCancelada.objects.get(id=f.id-1).sesion:      #Atrasar un lugar para coger la sesion
                                f.sesion = FacturaCancelada.objects.get(id=f.id-1).sesion
                                f.save()
                            else:
                                if FacturaCancelada.objects.get(id=f.id-2).sesion:  #Atrasar dos lugares para coger la sesion
                                    f.sesion = FacturaCancelada.objects.get(id=f.id-2).sesion
                                    f.save()

                        facturascanceladas.append((f.factura.numero, f.sesion.autorizacion))
                    return HttpResponse(json.dumps(facturascanceladas),content_type="application/json")

                except Exception as ex:
                    print(ex)
            # OCastillo NC_tipo 1_anulacion
            elif action=='notacreditotipoanula':
                notacreditotipoanula = []
                try:
                    if NotaCreditoInstitucion.objects.filter(fecha__month=request.GET['month'],fecha__year=request.GET['year']).exclude(tipo__id=TIPO_NC_DEVOLUCION).exists():
                        for nc in NotaCreditoInstitucion.objects.filter(fecha__month=request.GET['month'],fecha__year=request.GET['year']).exclude(tipo__id=TIPO_NC_DEVOLUCION).order_by('id'):
                            if nc.numero:
                                if nc.inscripcion.persona.cedula:
                                    identidad = nc.inscripcion.persona.cedula
                                else:
                                    identidad = nc.inscripcion.persona.pasaporte
                                notacreditotipoanula.append((identidad,nc.inscripcion.persona.nombre_completo_inverso(),nc.factura.numero,str(nc.fecha)))
                    return HttpResponse(json.dumps(notacreditotipoanula),content_type="application/json")

                except Exception as ex:
                    print(ex)

            # OCU 20-oct-2016 para Casade Iva 12
            elif action=='notacreditotipoanula_iva12':
                notacreditotipoanula_iva12 = []
                try:
                    if NotaCreditoInstitucion.objects.filter(fecha__month=request.GET['month'],fecha__year=request.GET['year']).exclude(tipo__id=TIPO_NC_DEVOLUCION).exists():
                        for nc in NotaCreditoInstitucion.objects.filter(fecha__month=request.GET['month'],fecha__year=request.GET['year']).exclude(tipo__id=TIPO_NC_DEVOLUCION).order_by('id'):
                            if nc.numero:
                                identidad = ''
                                if not (nc.factura.fecha > datetime(2016,5,31).date() and nc.factura.fecha <  datetime(2017,7,1).date()):
                                    if nc.inscripcion.persona.cedula:
                                        identidad = nc.inscripcion.persona.cedula
                                    else:
                                        identidad = nc.inscripcion.persona.pasaporte
                                notacreditotipoanula_iva12.append((identidad,nc.inscripcion.persona.nombre_completo_inverso(),nc.factura.numero,str(nc.fecha)))
                    return HttpResponse(json.dumps(notacreditotipoanula_iva12),content_type="application/json")

                except Exception as ex:
                    print(ex)

            # OCU 20-oct-2016 para Casade Iva 14
            elif action=='notacreditotipoanula_iva14':
                notacreditotipoanula_iva14 = []
                try:
                    if NotaCreditoInstitucion.objects.filter(fecha__month=request.GET['month'],fecha__year=request.GET['year']).exclude(tipo__id=TIPO_NC_DEVOLUCION).exists():
                        for nc in NotaCreditoInstitucion.objects.filter(fecha__month=request.GET['month'],fecha__year=request.GET['year']).exclude(tipo__id=TIPO_NC_DEVOLUCION).order_by('id'):
                            if nc.numero:
                                identidad = ''
                                if nc.factura.fecha > datetime(2016,5,31).date() and nc.factura.fecha <  datetime(2017,7,1).date():
                                    if nc.inscripcion.persona.cedula:
                                        identidad = nc.inscripcion.persona.cedula
                                    else:
                                        identidad = nc.inscripcion.persona.pasaporte
                                notacreditotipoanula_iva14.append((identidad,nc.inscripcion.persona.nombre_completo_inverso(),nc.factura.numero,str(nc.fecha)))
                    return HttpResponse(json.dumps(notacreditotipoanula_iva14),content_type="application/json")

                except Exception as ex:
                    print(ex)


            elif action=='totalncreditotipoanulabase':
                dato = []
                total = 0
                try:
                    if NotaCreditoInstitucion.objects.filter(fecha__month=request.GET['month'],fecha__year=request.GET['year']).exclude(tipo__id=TIPO_NC_DEVOLUCION).exists():
                        for nc in NotaCreditoInstitucion.objects.filter(fecha__month=request.GET['month'],fecha__year=request.GET['year']).exclude(tipo__id=TIPO_NC_DEVOLUCION):
                            if nc:
                                total = total + nc.valor
                    dato.append(total)
                    return HttpResponse(json.dumps(dato),content_type="application/json")

                except Exception as ex:
                    return HttpResponse(json.dumps(dato),content_type="application/json")


            # OCU 20-oct-2016 para Casade
            elif action=='totalncreditotipoanulabase_iva12':
                dato = []
                total = 0
                try:
                    if NotaCreditoInstitucion.objects.filter(fecha__month=request.GET['month'],fecha__year=request.GET['year']).exclude(tipo__id=TIPO_NC_DEVOLUCION).exists():
                        for nc in NotaCreditoInstitucion.objects.filter(fecha__month=request.GET['month'],fecha__year=request.GET['year']).exclude(tipo__id=TIPO_NC_DEVOLUCION):
                            if not (nc.factura.fecha > datetime(2016,5,31).date() and nc.factura.fecha <  datetime(2017,7,1).date()):
                                total = total + nc.valor
                    dato.append(total)
                    return HttpResponse(json.dumps(dato),content_type="application/json")

                except Exception as ex:
                    return HttpResponse(json.dumps(dato),content_type="application/json")

            # OCU 20-oct-2016 para Casade
            elif action=='totalncreditotipoanulabase_iva14':
                dato = []
                total = 0
                try:
                    if NotaCreditoInstitucion.objects.filter(fecha__month=request.GET['month'],fecha__year=request.GET['year']).exclude(tipo__id=TIPO_NC_DEVOLUCION).exists():
                        for nc in NotaCreditoInstitucion.objects.filter(fecha__month=request.GET['month'],fecha__year=request.GET['year']).exclude(tipo__id=TIPO_NC_DEVOLUCION):
                            if nc.factura.fecha > datetime(2016,5,31).date() and nc.factura.fecha <  datetime(2017,7,1).date():
                                total = total + nc.valor
                    dato.append(total)
                    return HttpResponse(json.dumps(dato),content_type="application/json")

                except Exception as ex:
                    return HttpResponse(json.dumps(dato),content_type="application/json")

            elif action=='ncreditotipoanulabase':

                dato = []
                total = 0
                try:
                    if NotaCreditoInstitucion.objects.filter(inscripcion__persona__cedula=request.GET['cedula'],fecha__month=request.GET['month'],fecha__year=request.GET['year']).exclude(tipo__id=TIPO_NC_DEVOLUCION).exists():
                        if request.GET['opcion']=='v':
                            for nc in NotaCreditoInstitucion.objects.filter(inscripcion__persona__cedula=request.GET['cedula'],fecha__month=request.GET['month'],fecha__year=request.GET['year']).exclude(tipo__id=TIPO_NC_DEVOLUCION):
                                if nc:
                                    total = total + nc.valor
                        else:
                            total = NotaCreditoInstitucion.objects.filter(inscripcion__persona__cedula=request.GET['cedula'],fecha__month=request.GET['month'],fecha__year=request.GET['year']).exclude(tipo__id=TIPO_NC_DEVOLUCION).count()
                    else:
                        if NotaCreditoInstitucion.objects.filter(inscripcion__persona__pasaporte=request.GET['cedula'],fecha__month=request.GET['month'],fecha__year=request.GET['year']).exclude(tipo__id=TIPO_NC_DEVOLUCION).exists():
                            if request.GET['opcion']=='v':
                                for nc in NotaCreditoInstitucion.objects.filter(inscripcion__persona__pasaporte=request.GET['cedula'],fecha__month=request.GET['month'],fecha__year=request.GET['year']).exclude(tipo__id=TIPO_NC_DEVOLUCION):
                                    if nc:
                                        total = total + nc.valor
                            else:
                                total = NotaCreditoInstitucion.objects.filter(inscripcion__persona__pasaporte=request.GET['cedula'],fecha__month=request.GET['month'],fecha__year=request.GET['year']).exclude(tipo__id=TIPO_NC_DEVOLUCION).count()

                    dato.append(total)


                    return HttpResponse(json.dumps(dato),content_type="application/json")

                except Exception as ex:
                    print(ex)

            # OCU 21-oct-2016 para Casade iva12
            elif action=='ncreditotipoanulabase_iva12':
                dato = []
                total = 0
                try:
                    if NotaCreditoInstitucion.objects.filter(inscripcion__persona__cedula=request.GET['cedula'],fecha__month=request.GET['month'],fecha__year=request.GET['year']).exclude(tipo__id=TIPO_NC_DEVOLUCION).exists():
                        if request.GET['opcion']=='v':
                            for nc in NotaCreditoInstitucion.objects.filter(inscripcion__persona__cedula=request.GET['cedula'],fecha__month=request.GET['month'],fecha__year=request.GET['year']).exclude(tipo__id=TIPO_NC_DEVOLUCION):
                                if not (nc.factura.fecha > datetime(2016,5,31).date() and nc.factura.fecha <  datetime(2017,7,1).date()):
                                    total = total + nc.valor
                        else:
                            total = NotaCreditoInstitucion.objects.filter(inscripcion__persona__cedula=request.GET['cedula'],fecha__month=request.GET['month'],fecha__year=request.GET['year']).exclude(tipo__id=TIPO_NC_DEVOLUCION).count()
                    else:
                        if NotaCreditoInstitucion.objects.filter(inscripcion__persona__pasaporte=request.GET['cedula'],fecha__month=request.GET['month'],fecha__year=request.GET['year']).exclude(tipo__id=TIPO_NC_DEVOLUCION).exists():
                            if request.GET['opcion']=='v':
                                for nc in NotaCreditoInstitucion.objects.filter(inscripcion__persona__pasaporte=request.GET['cedula'],fecha__month=request.GET['month'],fecha__year=request.GET['year']).exclude(tipo__id=TIPO_NC_DEVOLUCION):
                                    if not (nc.factura.fecha > datetime(2016,5,31).date() and nc.factura.fecha <  datetime(2017,7,1).date()):
                                        total = total + nc.valor
                            else:
                                total = NotaCreditoInstitucion.objects.filter(inscripcion__persona__pasaporte=request.GET['cedula'],fecha__month=request.GET['month'],fecha__year=request.GET['year']).exclude(tipo__id=TIPO_NC_DEVOLUCION).count()
                    dato.append(total)

                    return HttpResponse(json.dumps(dato),content_type="application/json")

                except Exception as ex:
                    print(ex)

            # OCU 21-oct-2016 para Casade iva14
            elif action=='ncreditotipoanulabase_iva14':
                dato = []
                total = 0
                try:
                    if NotaCreditoInstitucion.objects.filter(inscripcion__persona__cedula=request.GET['cedula'],fecha__month=request.GET['month'],fecha__year=request.GET['year']).exclude(tipo__id=TIPO_NC_DEVOLUCION).exists():
                        if request.GET['opcion']=='v':
                            for nc in NotaCreditoInstitucion.objects.filter(inscripcion__persona__cedula=request.GET['cedula'],fecha__month=request.GET['month'],fecha__year=request.GET['year']).exclude(tipo__id=TIPO_NC_DEVOLUCION):
                                if nc.factura.fecha > datetime(2016,5,31).date() and nc.factura.fecha <  datetime(2017,7,1).date():
                                    total = total + nc.valor
                        else:
                            total = NotaCreditoInstitucion.objects.filter(inscripcion__persona__cedula=request.GET['cedula'],fecha__month=request.GET['month'],fecha__year=request.GET['year']).exclude(tipo__id=TIPO_NC_DEVOLUCION).count()
                    else:
                        if NotaCreditoInstitucion.objects.filter(inscripcion__persona__pasaporte=request.GET['cedula'],fecha__month=request.GET['month'],fecha__year=request.GET['year']).exclude(tipo__id=TIPO_NC_DEVOLUCION).exists():
                            if request.GET['opcion']=='v':
                                for nc in NotaCreditoInstitucion.objects.filter(inscripcion__persona__pasaporte=request.GET['cedula'],fecha__month=request.GET['month'],fecha__year=request.GET['year']).exclude(tipo__id=TIPO_NC_DEVOLUCION):
                                    if nc.factura.fecha > datetime(2016,5,31).date() and nc.factura.fecha <  datetime(2017,7,1).date():
                                        total = total + nc.valor
                            else:
                                total = NotaCreditoInstitucion.objects.filter(inscripcion__persona__pasaporte=request.GET['cedula'],fecha__month=request.GET['month'],fecha__year=request.GET['year']).exclude(tipo__id=TIPO_NC_DEVOLUCION).count()
                    dato.append(total)

                    return HttpResponse(json.dumps(dato),content_type="application/json")

                except Exception as ex:
                    print(ex)


            elif action=='matriculadosanual':
                try:
                    anio = int(request.GET['y'])
                except:
                    anio = datetime.now().year
                total = {"total":Matricula.objects.filter(nivel__inicio__year=anio).count()}
                mujeres = {"mujeres":Matricula.objects.filter(nivel__inicio__year=anio, inscripcion__persona__sexo=SEXO_FEMENINO).count()}
                hombres = {"hombres":Matricula.objects.filter(nivel__inicio__year=anio, inscripcion__persona__sexo=SEXO_MASCULINO).count()}
                resultado = {}
                resultado['matriculas']=[]
                resultado['matriculas'].append(total)
                resultado['matriculas'].append(hombres)
                resultado['matriculas'].append(mujeres)
                resultado['matriculas'].append({"a":anio})
                return HttpResponse(json.dumps(resultado),content_type="application/json")

            elif action=='matriculados':
                matriculas = Matricula.objects.filter(nivel__cerrado=False)

                resultado = {}
                lista = []
                for matricula in matriculas:
                    d = {"cedula": matricula.inscripcion.persona.cedula,
                         "nombre": elimina_tildes(matricula.inscripcion.persona.nombre_completo()),
                         "genero": matricula.inscripcion.persona.sexo.nombre,
                         "carrera": elimina_tildes(matricula.nivel.carrera.nombre) if (matricula.nivel.carrera) else elimina_tildes(matricula.inscripcion.carrera.nombre),
                         "creditos": matricula.materiaasignada_set.all().aggregate(Sum('materia__creditos'))['materia__creditos__sum']

                         }
                    if matricula.becado:
                        d['becado'] = "SI"
                        d['tipobeneficio'] = matricula.tipobeneficio.nombre
                        if matricula.tipobeca:
                            d['tipobeca'] = matricula.tipobeca.nombre
                        else:
                            d['tipobeca'] = ""
                        d['porcientobeca'] = matricula.porcientobeca
                        if matricula.motivobeca:
                            d['motivobeca'] = matricula.motivobeca.nombre
                        else:
                            d['motivobeca'] = ""
                    else:
                        d['becado'] = "NO"
                        d['tipobeneficio'] = ""
                        d['tipobeca'] = ""
                        d['porcientobeca'] = ""
                        d['motivobeca'] = ""

                    if d['creditos']>0:
                        lista.append(d)
                resultado['lista'] = lista
                resultado['total'] =len(lista)
                return HttpResponse(json.dumps(resultado),content_type="application/json")

            elif action == 'tipopersona':
                try:
                    identificacion = request.GET['identificacion']
                    op = request.GET['op']
                    persona = None
                    gruposexcluidos = [PROFESORES_GROUP_ID,ALUMNOS_GROUP_ID,SISTEMAS_GROUP_ID]

                    if op == '1':
                        if Persona.objects.filter(cedula=identificacion,usuario__is_active=True).exclude(usuario__groups__id__in=gruposexcluidos).exists():
                            return HttpResponse(json.dumps({'codigo': 'ADM' }), content_type="application/json")
                        if Profesor.objects.filter(persona__cedula=identificacion,persona__usuario__is_active=True).exists():
                            return HttpResponse(json.dumps({'codigo': 'PRO' }), content_type="application/json")
                        if Graduado.objects.filter(inscripcion__persona__cedula=identificacion).exists():
                            return HttpResponse(json.dumps({'codigo': 'EXA' }), content_type="application/json")
                        if Egresado.objects.filter(inscripcion__persona__cedula=identificacion).exists():
                            return HttpResponse(json.dumps({'codigo': 'EXA' }), content_type="application/json")
                        if Inscripcion.objects.filter(persona__cedula=identificacion,persona__usuario__is_active=True).exists():
                            return HttpResponse(json.dumps({'codigo': 'INS' }), content_type="application/json")
                    else:
                        if Persona.objects.filter(pasaporte=identificacion,usuario__is_active=True).exclude(usuario__groups__id__in=gruposexcluidos).exists():
                            return HttpResponse(json.dumps({'codigo': 'ADM' }), content_type="application/json")
                        if Profesor.objects.filter(persona__pasaporte=identificacion).exists():
                            return HttpResponse(json.dumps({'codigo': 'PRO' }), content_type="application/json")
                        if Graduado.objects.filter(inscripcion__persona__pasaporte=identificacion).exists():
                            return HttpResponse(json.dumps({'codigo': 'EXA' }), content_type="application/json")
                        if Egresado.objects.filter(inscripcion__persona__pasaporte=identificacion).exists():
                            return HttpResponse(json.dumps({'codigo': 'EXA' }), content_type="application/json")
                        if Inscripcion.objects.filter(persona__pasaporte=identificacion,persona__usuario__is_active=True).exists():
                            return HttpResponse(json.dumps({'codigo': 'INS' }), content_type="application/json")

                    return HttpResponse(json.dumps({'codigo': 'NON'}), content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({'codigo':  'BAD'+ str(e)}), content_type="application/json")


            elif action=='docentes':
                lista = []
                for x in Profesor.objects.filter(profesormateria__materia__nivel__cerrado=False).distinct():
                    d = {
                        "cedula": x.persona.cedula,
                        "nombre": elimina_tildes(x.persona.nombre_completo()),
                        "dedicacion": x.dedicacion.nombre if x.dedicacion else "",
                        "categoria": x.categoria.nombre if x.categoria else "",
                        "titulos": [y.representacion_api() for y in x.titulacionprofesor_set.all()]
                    }
                    d['horas'] = x.profesormateria_set.filter(materia__nivel__cerrado=False).aggregate(Sum('materia__horas'))['materia__horas__sum']
                    d['materias'] = x.profesormateria_set.filter(materia__nivel__cerrado=False).count()
                    lista.append(d)
                resultado = {}
                resultado['lista'] = lista
                resultado['total'] =len(lista)
                return HttpResponse(json.dumps(resultado),content_type="application/json")

            elif action=='aulas':
                lista = []
                for x in Aula.objects.all():
                    d = model_to_dict(x)
                    d['sede'] = x.sede.nombre
                    d['tipo'] = x.tipo.nombre
                    lista.append(d)
                resultado = {"total": Aula.objects.all().count(), "aulas": lista}
                return HttpResponse(json.dumps(resultado),content_type="application/json")

            elif action == 'horasdocente':
                return HttpResponse(json.dumps(exportacion_datos_rol(request.GET['fecha_inicio'],request.GET['fecha_fin'],request.GET['codigo'],request.GET['fecha_vinc'])),content_type="application/json")

            elif action == 'administrativos':
                return HttpResponse(json.dumps(exportacion_datos_rol_administrativos(request.GET['fecha_inicio'],request.GET['fecha_fin'])),content_type="application/json")

            elif action=='facturacion':
                return HttpResponse(json.dumps(exportacion_datos_facturacion(request.GET['caja'],convertir_fecha(request.GET['fecha']))),content_type="application/json")

            elif action=='facturacionNewProcess':
                return HttpResponse(json.dumps(exportacion_datos_facturacion_newProcess(request.GET['caja'],convertir_fecha(request.GET['fecha']))),content_type="application/json")

            elif action=='obtenerPagosNc':
                return HttpResponse(json.dumps(exportacion_pagos_nc(request.GET['nc'])), content_type="application/json")

            elif action=='mallasitb':

                return HttpResponse(json.dumps(exportacion_datos_mallaitb()),content_type="application/json")
            elif action=='asignaturasitb':

                return HttpResponse(json.dumps(exportacion_datos_asignaturaitb(request.GET['idmalla'])),content_type="application/json")
            elif action=='historiconotasitb':

                return HttpResponse(json.dumps(exportacion_datos_historicoitb(request.GET['cedula'])),content_type="application/json")
            elif action=='factura':

                factura = Factura.objects.get(pk=request.GET['id'])
                factura.impresa = True
                factura.save()
                return HttpResponse(json.dumps({"result":"ok"}), content_type="application/json")

            elif action=='cambioidasignatura':
                try:
                    asignaturac = Asignatura.objects.filter(pk=request.GET['ac'])[:1].get()
                    asignaturam = Asignatura.objects.filter(pk=request.GET['am'])[:1].get()
                    materias = Materia.objects.filter(asignatura=asignaturam)
                    for materia in materias:
                        materia.asignatura = asignaturac
                        materia.save()
                    recordacademico = RecordAcademico.objects.filter(asignatura=asignaturam)
                    for record in recordacademico:
                        record.asignatura = asignaturac
                        record.save()
                    historicorecord = HistoricoRecordAcademico.objects.filter(asignatura = asignaturam)
                    for historico in historicorecord:
                        historico.asignatura = asignaturac
                        historico.save()
                    asignaturamalla = AsignaturaMalla.objects.filter(asignatura = asignaturac)
                    for asigm in asignaturamalla:
                        asigm.asignatura = asignaturac
                        asigm.save()
                    preciomaterias = PrecioMateria.objects.filter(asignatura = asignaturac)
                    for precm in preciomaterias:
                        precm.asignatura = asignaturac
                        precm.save()
                    asignivelcarr = AsignaturaNivelacionCarrera.objects.filter(asignatura = asignaturac)
                    for asignc in asignivelcarr:
                        asignc.asignatura = asignaturac
                        asignc.save()
                    return HttpResponse(json.dumps({"result":"ok"}), content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}), content_type="application/json")

            elif action=='actualizamateriaasignada':
                n1=0
                n2=0
                n3=0
                n4=0
                examen=0
                recuperacion=0
                cod1=0
                cod2=0
                cod3=0
                cod4=0
                observaciones=''
                data = {"error":0,"warning":0}
                if 'maa' in request.GET:
                    try:
                        maa = int(request.GET['maa'])
                        notaf=0
                        if MODELO_EVALUACION == EVALUACION_ITB:
                            cod1 = int(request.GET['cod1'])
                            cod2 = int(request.GET['cod2'])
                            cod3 = int(request.GET['cod3'])
                            cod4 = int(request.GET['cod4'])
                            n1 = int(request.GET['n1'])
                            n2 = int(request.GET['n2'])
                            n3 = int(request.GET['n3'])
                            n4 = int(request.GET['n4'])
                            examen = int(request.GET['examen'])
                            recuperacion = int(request.GET['recuperacion'])
                            observaciones = 'Materia actualizada externa'

                        if not MateriaAsignada.objects.filter(pk=maa).exists():
                            # la materia asignada no existe
                            data = {"error":0,"warning":1}
                        else:

                            maad = MateriaAsignada.objects.get(pk=maa)
                            if MODELO_EVALUACION == EVALUACION_ITB:
                                macal = maad.evaluacion_itb()
                                macal.cod1 = CodigoEvaluacion.objects.filter(pk=cod1)[:1].get()
                                macal.fecha1 = datetime.today()
                                macal.cod2 = CodigoEvaluacion.objects.filter(pk=cod2)[:1].get()
                                macal.fecha2 = datetime.today()
                                macal.cod3 = CodigoEvaluacion.objects.filter(pk=cod3)[:1].get()
                                macal.fecha3 = datetime.today()
                                macal.cod4 = CodigoEvaluacion.objects.filter(pk=cod4)[:1].get()
                                macal.fecha4 = datetime.today()
                                macal.n1 = n1
                                macal.n2 = n2
                                macal.n3 = n3
                                macal.n4 = n4
                                macal.examen = examen
                                macal.recuperacion = recuperacion
                                macal.observaciones = observaciones
                                macal.materiaasignada.cerrado = True
                                macal.save()
                                notaf=int(request.GET['n1']) +int(request.GET['n2']) + int(request.GET['n3']) +int(request.GET['n4']) + int(request.GET['examen'])
                                if (notaf >= NOTA_PARA_APROBAR) or ((notaf+int(request.GET['recuperacion']))/2) >=  NOTA_PARA_APROBAR:
                                    # asistencia
                                    try:
                                        if not Clase.objects.filter(materia = maad.materia).exists():
                                            clase = Clase(materia = maad.materia,
                                                          profesor = maad.materia.profesormateria_set.all()[:1].get().profesor,
                                                          turno = Turno.objects.all()[:1].get(),
                                                          aula = Aula.objects.all()[:1].get(),
                                                          dia = 1)
                                            clase.save()
                                        else:
                                            clase = Clase.objects.filter(materia = maad.materia)[:1].get()

                                        if not Leccion.objects.filter(clase = clase).exists():
                                            leccion = Leccion(clase = clase,
                                                              fecha = maad.materia.inicio,
                                                              horaentrada = datetime.now().time(),
                                                              horasalida = datetime.now().time(),
                                                              abierta = False,
                                                              contenido = "Materia Externa",
                                                              observaciones = "Materia Externa")
                                            leccion.save()
                                        else:
                                            leccion = Leccion.objects.filter(clase = clase).all()[:1].get()

                                        if not AsistenciaLeccion.objects.filter(leccion=leccion, matricula=maad.matricula).exists():
                                            asistencialeccion = AsistenciaLeccion(leccion=leccion, matricula=maad.matricula, asistio=True)
                                            asistencialeccion.save()
                                        else:
                                            asistencialeccion = AsistenciaLeccion.objects.filter(leccion=leccion, matricula=maad.matricula)[:1].get()
                                            asistencialeccion.asistio = True
                                            asistencialeccion.save()


                                    except Exception as ex:
                                        data = {"error":5,"x":ex.message,"warning":0}

                                # recalcula el estado de la materia
                                macal.actualiza_estado()
                    except Exception as ex:
                        # algun otro error al actualizar la materia
                        data = {"error":2,"x":ex.message,"warning":0}
                return HttpResponse(json.dumps(data), content_type="application/json")
            elif action == 'enviacorreo':
                cant_export = int(request.GET['cant_export'])
                mat = Materia.objects.get(pk=request.GET['maa'])
                if EMAIL_ACTIVE:
                     mat.notificacion_exportacion(cant_export)

            elif action=='biblioteca':
                docu = Documento.objects.all()[:1].get()
                data={}
                data['nombre'] = elimina_tildes(docu.nombre)
                data['autor'] = elimina_tildes(docu.autor)
                return HttpResponse(json.dumps(data),content_type="application/json")
            elif action=='cerrarmateria':
                data = {"error":0}
                try:
                    if 'ma' in request.GET:
                        ma = int(request.GET['ma'])
                        if Materia.objects.filter(pk=ma).exists():
                            materia = Materia.objects.filter(pk=ma)[:1].get()
                            materiaasignada = materia.materiaasignada_set.all()
                            for maa in materiaasignada:
                                if MODELO_EVALUACION == EVALUACION_ITB:
                                    maa.evaluacion_itb().actualiza_estado()
                                maa.cerrado = True
                                maa.save()
                            materia.cerrado = True
                            materia.fechacierre = datetime.today()
                            materia.horacierre = datetime.now().time()
                            materia.save()
                        else:
                            if 'matasii' in request.GET:
                                if MateriaAsignada.objects.filter(pk=request.GET['matasii']).exists():
                                    materia = MateriaAsignada.objects.filter(pk=request.GET['matasii'])[:1].get()
                                    materia.materia.cerrado = True
                                    materia.materia.fechacierre = datetime.today()
                                    materia.materia.horacierre = datetime.now().time()
                                    materia.materia.save()

                            else:
                            # no existe la materia
                                data = {"error":2}
                except:
                    data = {"error":1}
                return HttpResponse(json.dumps(data), content_type="application/json")
            elif action=='impmaterias':
                data = {}
                if 'asig' in request.GET:
                    asig = request.GET['asig']
                    asig = asig.split(',')
                    #m=(29732,33354,35307)
                    #m=(35230,34962,34716)
                    ma = Materia.objects.filter(asignatura__in=asig, nivel__cerrado=False, cerrado=False)
                    #ma = Materia.objects.filter(asignatura__in=asig, nivel__cerrado=False, cerrado=False,id__in=m)
                    #ma = Materia.objects.filter(asignatura__in=asig, nivel__cerrado=False, cerrado=False,id=34962)

                    for m in ma:
                        dma = model_to_dict(m, exclude=['nivel','creditos','observaciones','fechaalcance','rectora','horas','fechacierre','identificacion','horacierre'])
                        paralelo = Nivel.objects.filter(materia=m)[:1].get().paralelo
                        dma['inicio'] = dma['inicio'].strftime('%d-%m-%Y')
                        dma['fin'] = dma['fin'].strftime('%d-%m-%Y')
                        dma['paralelo'] = paralelo
                        data['ma_'+str(m.id)]=[]
                        data['ma_'+str(m.id)].append(dma)
                        pe = {'pe_'+str(m.id):[]}
                        maa = m.asignados_a_esta_materia()
                        for me in maa:
                            try:
                                per = me.matricula.inscripcion.persona
                                # p = model_to_dict(per,exclude=['sector','ciudad','canton','provincia','madre','padre','usuario','nacimiento','parroquia','nacionalidad','id','emailinst','sangre','num_direccion','sexo'])
                                # OCU 21-abril-2016
                                p = model_to_dict(per,exclude=['sector','ciudad','canton','provincia','madre','padre','usuario','nacimiento','parroquia','nacionalidad','id','emailinst','sangre','num_direccion','sexo','reestablecer','codigo','fecha_res','fechaultimactualizaciondatabook'])
                                p['materiaasignada']=me.id

                                p['nombres']=str(elimina_tildes(per.nombres))
                                p['apellido2']=str(elimina_tildes(per.apellido2))
                                p['apellido1']=str(elimina_tildes(per.apellido1))
                                p['cedula']=str(elimina_tildes(per.cedula))
                                p['pasaporte']=str(elimina_tildes(per.pasaporte))
                                p['extranjero']=str(elimina_tildes(per.extranjero))
                                p['direccion']=str(elimina_tildes(per.direccion).replace('/',''))
                                p['direccion2']=str(elimina_tildes(per.direccion2).replace('/',''))
                                p['telefono']=str(elimina_tildes(per.telefono).replace('/',''))
                                p['telefono_conv']=str(elimina_tildes(per.telefono_conv).replace('/',''))
                                p['email']=str(elimina_tildes(per.email).replace('/',''))

                                pers = {'p_'+str(per.id):[]}
                                pers['p_'+str(per.id)].append(p)
                                pe['pe_'+str(m.id)].append(pers)
                            except Exception as e:
                                print(e)
                                #print(per)
                        data['ma_'+str(m.id)].append(pe)
                        #print((data))
                    return HttpResponse(json.dumps(data), content_type="application/json")


            elif action == 'impgrupo':
                return HttpResponse(json.dumps(exportacion_estd_itb(request.GET['grupo'])),content_type="application/json")

            elif action == 'cambiarpass':
                idusuario=request.GET['idusuario']
                user=User.objects.get(id=int(idusuario))
                if DEFAULT_PASSWORD == 'itb' and ACTIVA_ADD_EDIT_AD:
                    user.set_password(NEW_PASSWORD)
                    if Persona.objects.filter(usuario=user).exists():
                        persona = Persona.objects.filter(usuario=user)[:1].get()
                        scriptresponse = ''
                        mensajesc = ''
                        listnombre = []
                        validacambio = True
                        try:
                            datos = {"identity": user.username,
                             "NewPassword": NEW_PASSWORD}
                            consulta = requests.put(IP_SERVIDOR_API_DIRECTORY+'/changep',json.dumps(datos), verify=False,timeout=4)
                            if consulta.status_code == 200:
                                validacambio = True
                                datos = consulta.json()
                        except requests.Timeout:
                            print("Error Timeout")
                        except requests.ConnectionError:
                            print("Error Conexion")


                        user.save()

                else:
                    user.set_password(DEFAULT_PASSWORD)
                    user.save()

            elif action == 'materias_activas_online':
                desde = request.GET['desde']
                hasta = request.GET['hasta']
                dia = request.GET['dia']
                turno_comienza = request.GET['turno_comienza']
                turno_termina = request.GET['turno_termina']
                profesor=''
                data={}
                clases=''

                if Profesor.objects.filter(persona__cedula=request.GET['profesor']).exists() or Profesor.objects.filter(persona__pasaporte=request.GET['profesor']).exists():
                    if Profesor.objects.filter(persona__cedula=request.GET['profesor']).exists():
                        profesor = Profesor.objects.get(persona__cedula=request.GET['profesor'],activo=True)
                    else:
                        profesor = Profesor.objects.get(persona__pasaporte=request.GET['profesor'],activo=True)

                    materias_activas = Materia.objects.filter(
                        (Q(inicio__lte=desde) & Q(fin__gte=desde)) |
                        (Q(inicio__lte=hasta) & Q(fin__gte=hasta)) |
                        (Q(inicio__gte=desde) & Q(fin__lte=hasta)), cerrado=False,
                        profesormateria__profesor=profesor)

                    clases = Clase.objects.filter(
                                (Q(turno__comienza__lte=turno_comienza) & Q(turno__termina__gte=turno_comienza)) |
                                (Q(turno__comienza__lte=turno_termina) & Q(turno__termina__gte=turno_termina)) |
                                (Q(turno__comienza__gte=turno_comienza) & Q(turno__termina__lte=turno_termina)),
                                materia__in=materias_activas, dia=dia)

                if clases:
                    lista_clases = [y.materia.nivel.paralelo+' ('+y.materia.nivel.nivelmalla.nombre+') - materia: '+y.materia.asignatura.nombre+' - '+str(y.turno.comienza)+' a '+str(y.turno.termina)+' - aula:'+y.aula.nombre for y in clases]
                    return HttpResponse(json.dumps({'result': 'ok', 'clases':lista_clases}), content_type="application/json")
                else:
                    return HttpResponse(json.dumps({'result': 'bad'}),content_type="application/json")

        return HttpResponse(json.dumps(['SGA','Tecnologico Bolivariano (C) Todos los derechos reservados']),content_type="application/json")

def representacion_factura(x):
    return fix_factura(model_to_dict(x,exclude='fecha'), x)

def fix_factura(obj, f):
    obj['fecha'] = f.fecha.strftime("%d-%m-%Y")
    obj['cliente'] = model_to_dict(ClienteFactura.objects.get(pk=obj['cliente']))
    formasdepago = [fix_formadepago(x) for x in obj['pagos']]
    pagos = [fix_pago(x) for x in obj['pagos']]
    obj['pagos'] = pagos
    obj['enletras'] = number_to_letter.enletras(obj['total'])
    obj['formasdepago'] = formasdepago

    return obj

def fix_formadepago(x):
    pago = Pago.objects.get(pk=x)
    return pago.nombre()


def fix_pago(x):
    pago = Pago.objects.get(pk=x)
    obj = model_to_dict(pago, exclude=['fecha', 'lugar', 'recibe', 'efectivo', 'id'])
    rubro = Rubro.objects.get(pk=obj['rubro'])
    obj['rubro'] = model_to_dict(rubro, exclude=['fecha','fechavence', 'cancelado', 'id', 'inscripcion', 'fichamedica','valor'])
    obj['rubro'].update({'nombre': rubro.nombre(), 'tipo': rubro.tipo(), 'alumno': rubro.inscripcion.persona.nombre_completo() if rubro.inscripcion else str(rubro.fichamedica)})

    return obj
def exportacion_datos_rol(fechai, fechaf,codigo,fechavinc):
    profesor = Profesor.objects.filter(activo=True).order_by('persona__apellido1','persona__apellido2','persona__nombres')
    data = []
    for p in profesor:
        # print(p)
        vtutoria  = 0
        valorv  = 0
        horasv  = 0
        horaspracticas = 0
        valormulta=0
        datos = []
        try:
            if p.persona.cedula or p.persona.pasaporte:
                if RolPerfilProfesor.objects.filter(profesor=p).exists():
                    rp = RolPerfilProfesor.objects.get(profesor=p)
                    horas = p.horasrol(fechai,fechaf)
                    salario = RolPerfilProfesor.objects.get(profesor=p).salario
                    # datos.append((p.persona.nombres, p.persona.apellido1 , p.persona.apellido2 , p.persona.cedula , p.persona.pasaporte ,p.persona.nacimiento , p.persona.sexo , p.persona.telefono_conv , p.persona.telefono , p.persona.email , p.persona.emailinst, p.fechaingreso,horas,salario ))
                    horas_clase = p.calcula_horas_clase(fechai,fechaf)
                    # salario = RolPerfilProfesor.objects.get(profesor=p).salario
                    datos.append(elimina_tildes(p.persona.nombres))
                    datos.append(elimina_tildes(p.persona.apellido1))
                    datos.append(elimina_tildes(p.persona.apellido2))
                    if p.persona.cedula:
                        datos.append(p.persona.cedula)
                    else:
                        datos.append(p.persona.pasaporte)
                    datos.append(p.persona.pasaporte)
                    if p.persona.nacimiento:
                        try:
                            datos.append(p.persona.nacimiento.strftime("%d-%m-%Y"))
                        except:
                            datos.append('')

                    else:
                        datos.append('')
                    datos.append(p.persona.sexo.nombre)
                    datos.append(p.persona.telefono_conv)
                    datos.append(p.persona.telefono)
                    datos.append(p.persona.email)
                    datos.append(p.persona.emailinst)
                    if rp.fechaafiliacion:
                        try:
                            datos.append(rp.fechaafiliacion.strftime("%d-%m-%Y"))
                        except:
                            datos.append('')
                    else:
                        datos.append('')
                    datos.append(horas)
                    datos.append(salario)
                    datos.append(horas_clase)
                    datos.append(str(rp.esfijo))
                    datos.append(str(rp.esadministrativo))
                    # PAGO HORAS VINCULACION
                    horasv = p.horas_vinculacion(fechai,fechavinc)
                    datos.append(horasv)
                    if DEFAULT_PASSWORD == 'itb':
                        valorv = horasv * VALOR_VINCULACION
                    else:
                        valorv = p.valor_vinculacion(fechai,fechavinc)
                    # OCastillo 19-09-2024 se excluye la importacion del valor de vinculacion por el momento
                    # datos.append(valorv)
                    datos.append(0)

                    if DetallePagoTutoria.objects.filter(contarol=codigo,pagotutoria__profesor=p).exists():
                        vtutoria = float(DetallePagoTutoria.objects.filter(contarol=codigo,pagotutoria__profesor=p).aggregate(Sum('valorpago'))['valorpago__sum'])
                        datos.append(vtutoria)
                    else:
                        datos.append(0)

                    #OCastillo 02-07-2020 DESCUENTO MULTA DOCENTES
                    valormulta = p.multas_docentes(fechai,fechaf)
                    datos.append(valormulta)

                    #PAGO HORAS SEMINARIOS
                    horasseminario = p.horas_seminario(fechai,fechaf)
                    datos.append(horasseminario)

                    # PAGO PRACTICAS PREPROFESIONALES
                    horaspracticas = p.pago_practicas(fechai,fechaf)
                    datos.append(horaspracticas)

                    # PAGO OTROS INGRESOS
                    otrosingresos = p.otros_ingresos(fechai,fechaf)
                    datos.append(otrosingresos)

                    # if horas_clase or rp.esfijo or horasv or horaspracticas or otrosingresos:
                    #     if horas_clase or rp.esfijo or vtutoria or horasv or valormulta or horaspracticas or otrosingresos:
                    if len(datos)>0:
                        data.append(datos)
            # print(datos)
        except Exception as ex:
            pass
    return data

def exportacion_datos_facturacion_newProcess(cajaid, fecha):
    try:
        # print('NUEVO PROCESO')
        response = []
        caja = LugarRecaudacion.objects.get(pk=cajaid)
        sesiones = caja.sesion_fecha(fecha)
        if sesiones:
            for sesion in sesiones:
                # print(sesion.id)
                data = {}
                pagos = []
                total = 0

                for f in FormaDePago.objects.all():
                    listPagos = Pago.objects.filter(sesion=sesion).values_list('id', flat=True)
                    mapaPagos = {
                        FORMA_PAGO_DEPOSITO: {'id__in': PagoTransferenciaDeposito.objects.filter(deposito=True, pagos__id__in=listPagos).values('pagos')},
                        FORMA_PAGO_TRANSFERENCIA: {'id__in': PagoTransferenciaDeposito.objects.filter(pagos__id__in=listPagos).exclude(deposito=True).values('pagos')},
                        FORMA_PAGO_CHEQUE: {'id__in': (PagoCheque.objects.filter(pagos__id__in=listPagos).annotate(pago_fecha=F('pagos__fecha')).filter(fechacobro=F('pago_fecha'))).values('pagos')},
                        FORMA_PAGO_CHEQUE_POSTFECHADO: {'id__in': (PagoCheque.objects.filter(pagos__id__in=listPagos).annotate(pago_fecha=F('pagos__fecha')).filter(~Q(fechacobro=F('pago_fecha')))).values('pagos')},
                        FORMA_PAGO_TARJETA_DEB: {'id__in': PagoTarjeta.objects.filter(tarjetadebito=True, pagos__id__in=listPagos).values('pagos')},
                        FORMA_PAGO_TARJETA: {'id__in': PagoTarjeta.objects.filter(pagos__id__in=listPagos).exclude(tarjetadebito=True).values('pagos')},
                        FORMA_PAGO_RETENCION: {'id__in': PagoRetencion.objects.filter(pagos__id__in=listPagos).values('pagos')},
                        FORMA_PAGO_NOTA_CREDITO: {'id__in': PagoNotaCreditoInstitucion.objects.filter(pagos__id__in=listPagos).values('pagos')},
                        FORMA_PAGO_RECIBOCAJAINSTITUCION: {'id__in': PagoReciboCajaInstitucion.objects.filter(pagos__id__in=listPagos).values('pagos')},
                        FORMA_PAGO_EFECTIVO: {'efectivo': True},
                        FORMA_PAGO_WESTER: {'wester': True},
                        FORMA_PAGO_PACIFICO: {'pacifico': True},
                        FORMA_PAGO_REFERIDO: {'referido': True},
                        FORMA_PAGO_PICHINCHA: {'pichincha': True},
                        FORMA_PAGO_PAGOONLINE: {'paymentez': True},
                        FORMA_PAGO_FACILITO: {'facilito': True},
                        FORMA_PAGO_ELECTRONICO: {'electronico': True}
                    }
                    filtro = mapaPagos[f.id]
                    pagosFP = Pago.objects.filter(sesion=sesion).filter(**filtro)
                    print(f.nombre+": " + str(pagosFP.aggregate(Sum('valor'))['valor__sum']))
                    for p in pagosFP:
                        total += p.valor
                        datosPago = {}
                        factura = p.factura_set.filter()[:1].get()

                        descPromo=0
                        descBeca=0
                        if DetalleDescuento.objects.filter(pago=p).exists():
                            descPromo = DetalleDescuento.objects.filter(pago=p).aggregate(Sum('valor'))['valor__sum']
                        if DetalleRubrosBeca.objects.filter(pago=p).exists():
                            descBeca = DetalleRubrosBeca.objects.filter(pago=p).aggregate(Sum('descuento'))['descuento__sum']

                        datosPago['facturaNumero'] = factura.numero
                        datosPago['inscripcionNombre'] = p.rubro.inscripcion.persona.nombre_completo()
                        datosPago['clienteRuc'] = factura.cliente.ruc
                        datosPago['clienteTelefono'] = factura.cliente.telefono
                        datosPago['clienteDireccion'] = elimina_tildes(factura.cliente.direccion)
                        datosPago['carreraId'] = p.rubro.inscripcion.carrera.id
                        datosPago['carreraNombre'] = elimina_tildes(p.rubro.inscripcion.carrera.nombre)
                        datosPago['formaPagoId'] = f.id
                        datosPago['formaPagoNombre'] = elimina_tildes(f.nombre)
                        datosPago['formaPagoCodigo'] = f.codigoformapago.codigo
                        datosPago['pagoValor'] = p.valor
                        datosPago['rubroNombre'] = elimina_tildes(p.rubro.nombre())
                        datosPago['descPromo'] = descPromo
                        datosPago['descBeca'] = descBeca
                        datosPago['esFraude'] = False
                        if p.rubro.nc:
                            if NotaCreditoInstitucion.objects.get(pk=p.rubro.nc).motivonc:
                                datosPago['esFraude'] = True if NotaCreditoInstitucion.objects.get(pk=p.rubro.nc).motivonc.id == 1 else False

                        tipoRubro = p.rubro.obtener_tipo_rubro()
                        datosPago['tipoRubroId'] = tipoRubro.id
                        datosPago['tipoRubroDescripcion'] = tipoRubro.nombre
                        # print(datosPago)

                        pagos.append(datosPago)
                data['PAGOS'] = pagos

                notasDeCredito = []
                for nc in NotaCreditoInstitucion.objects.filter(sesioncaja=sesion):
                    datosNC = {}
                    datosNC['ncId'] = nc.id
                    datosNC['ncValor'] = nc.valor
                    datosNC['ncFecha'] = str(nc.fecha)
                    datosNC['ncTipoId'] = nc.tipo.id
                    datosNC['ncTipoDescripcion'] = elimina_tildes(nc.tipo.descripcion)
                    datosNC['inscripcionCedula'] = nc.inscripcion.persona.cedula
                    datosNC['inscripcionNombre'] = nc.inscripcion.persona.nombre_completo()
                    datosNC['carreraId'] = nc.inscripcion.carrera.id
                    datosNC['carreraNombre'] = elimina_tildes(nc.inscripcion.carrera.nombre)
                    datosNC['facturaId'] = nc.factura.id
                    datosNC['facturaNumero'] = nc.factura.numero
                    datosNC['facturaFecha'] = str(nc.factura.fecha)
                    datosNC['esFraude'] = False
                    if nc.motivonc:
                        datosNC['esFraude'] = True if nc.motivonc.id == 1 else False

                    # pagos = nc.factura.pagos.all()
                    # for pago in nc.factura.pagos.filter(formapago=None):
                    #     if not pago.formapago:
                    #         pago.formapago = pago.obtener_forma_pago()
                    #         pago.save()
                    # listPagosNC = []
                    # for formaPago in FormaDePago.objects.filter(id__in=pagos.values('formapago')):
                    #     for p in Pago.objects.filter(formapago=formaPago, id__in=pagos.values_list('id', flat=True)):
                    #         datosPago = {}
                    #         factura = p.factura_set.filter()[:1].get()
                    #
                    #         descPromo = 0
                    #         descBeca = 0
                    #         if DetalleDescuento.objects.filter(pago=p).exists():
                    #             descPromo = DetalleDescuento.objects.filter(pago=p).aggregate(Sum('valor'))['valor__sum']
                    #         if DetalleRubrosBeca.objects.filter(pago=p).exists():
                    #             descBeca = DetalleRubrosBeca.objects.filter(pago=p).aggregate(Sum('descuento'))['descuento__sum']
                    #
                    #         datosPago['facturaNumero'] = factura.numero
                    #         datosPago['inscripcionNombre'] = p.rubro.inscripcion.persona.nombre_completo()
                    #         datosPago['clienteRuc'] = factura.cliente.ruc
                    #         datosPago['clienteTelefono'] = factura.cliente.telefono
                    #         datosPago['clienteDireccion'] = elimina_tildes(factura.cliente.direccion)
                    #         datosPago['carreraId'] = p.rubro.inscripcion.carrera.id
                    #         datosPago['carreraNombre'] = elimina_tildes(p.rubro.inscripcion.carrera.nombre)
                    #         datosPago['formaPagoId'] = formaPago.id
                    #         datosPago['formaPagoNombre'] = elimina_tildes(formaPago.nombre)
                    #         datosPago['formaPagoCodigo'] = formaPago.codigoformapago.codigo
                    #         datosPago['pagoValor'] = p.valor
                    #         datosPago['rubroNombre'] = elimina_tildes(p.rubro.nombre())
                    #         datosPago['descPromo'] = descPromo
                    #         datosPago['descBeca'] = descBeca
                    #
                    #         tipoRubro = p.rubro.obtener_tipo_rubro()
                    #         datosPago['tipoRubroId'] = tipoRubro.id
                    #         datosPago['tipoRubroDescripcion'] = tipoRubro.nombre
                    #         listPagosNC.append(datosPago)
                    #
                    # datosNC['pagosNC'] = listPagosNC
                    notasDeCredito.append(datosNC)
                data['NC'] = notasDeCredito

                recibosDeCaja = []
                for rc in ReciboCajaInstitucion.objects.filter(sesioncaja=sesion).exclude(activo=False):
                    if not rc.formapago:
                        try:
                            rc.formapago = Pago.objects.filter(sesion=rc.sesioncaja, rubro__inscripcion=rc.inscripcion).order_by('-id')[:1].get().obtener_forma_pago()
                            rc.save()
                        except Exception as ex:
                            print("ERROR AL GENERAR FORMA DE PAGO EN RC: "+str(ex))
                    datosRC = {}
                    datosRC['rcId'] = rc.id
                    datosRC['rcValorInicial'] = rc.valorinicial
                    datosRC['rcFecha'] = str(rc.fecha)
                    datosRC['inscripcionCedula'] = rc.inscripcion.persona.cedula
                    datosRC['inscripcionNombre'] = rc.inscripcion.persona.nombre_completo()
                    datosRC['carreraId'] = rc.inscripcion.carrera.id
                    datosRC['carreraNombre'] = elimina_tildes(rc.inscripcion.carrera.nombre)
                    datosRC['formaPagoId'] = rc.formapago.id if rc.formapago else ''
                    datosRC['formaPagoCodigo'] = rc.formapago.codigoformapago.codigo if rc.formapago else ''
                    recibosDeCaja.append(datosRC)
                data['RC'] = recibosDeCaja
                response.append(data)
        print(response)
        return response

    except Exception as ex:
        print(ex)
        return {'ERROR': str(ex)}

def exportacion_pagos_nc(nc_id):
    try:
        nc = NotaCreditoInstitucion.objects.get(pk=nc_id)
        pagos = nc.factura.pagos.all()
        for pago in nc.factura.pagos.filter(formapago=None):
            if not pago.formapago:
                pago.formapago = pago.obtener_forma_pago()
                pago.save()
        listPagosNC = []
        for formaPago in FormaDePago.objects.filter(id__in=pagos.values('formapago')):
            for p in Pago.objects.filter(formapago=formaPago, id__in=pagos.values_list('id', flat=True)):
                datosPago = {}
                factura = p.factura_set.filter()[:1].get()

                descPromo = 0
                descBeca = 0
                if DetalleDescuento.objects.filter(pago=p).exists():
                    descPromo = DetalleDescuento.objects.filter(pago=p).aggregate(Sum('valor'))['valor__sum']
                if DetalleRubrosBeca.objects.filter(pago=p).exists():
                    descBeca = DetalleRubrosBeca.objects.filter(pago=p).aggregate(Sum('descuento'))['descuento__sum']

                datosPago['facturaNumero'] = factura.numero
                datosPago['inscripcionNombre'] = p.rubro.inscripcion.persona.nombre_completo()
                datosPago['clienteRuc'] = factura.cliente.ruc
                datosPago['clienteTelefono'] = factura.cliente.telefono
                datosPago['clienteDireccion'] = elimina_tildes(factura.cliente.direccion)
                datosPago['carreraId'] = p.rubro.inscripcion.carrera.id
                datosPago['carreraNombre'] = elimina_tildes(p.rubro.inscripcion.carrera.nombre)
                datosPago['formaPagoId'] = formaPago.id
                datosPago['formaPagoNombre'] = elimina_tildes(formaPago.nombre)
                datosPago['formaPagoCodigo'] = formaPago.codigoformapago.codigo
                datosPago['pagoValor'] = p.valor
                datosPago['rubroNombre'] = elimina_tildes(p.rubro.nombre())
                datosPago['descPromo'] = descPromo
                datosPago['descBeca'] = descBeca

                tipoRubro = p.rubro.obtener_tipo_rubro()
                datosPago['tipoRubroId'] = tipoRubro.id
                datosPago['tipoRubroDescripcion'] = tipoRubro.nombre
                listPagosNC.append(datosPago)
        return listPagosNC
    except Exception as e:
        print(e)
        return {'ERROR': str(e)}

def exportacion_datos_facturacion(cajaid, fecha):
    try:
        data = []
        caja = LugarRecaudacion.objects.get(pk=cajaid)
        # Guardar datos
        sesiones = caja.sesion_fecha(fecha)
        if sesiones:

            for sesion in sesiones:

                pagos = Pago.objects.filter(sesion=sesion)
                for pago in pagos:

                    ret_iva = 0
                    ret_fuente = 0
                    rec_csv = []
                    elec=0
                    faci=0
                    paci=0
                    py=0

                    if pago.es_chequepostfechado():
                        rec_csv.append('3')
                    elif pago.es_chequevista():
                        rec_csv.append('1')
                    elif pago.es_recibocajainst():
                        rec_csv.append('4')
                    elif pago.es_notacreditoinst():
                        rec_csv.append('6')
                    # elif pago.es_retencion():
                    #     rec_csv.append('8')
                    elif  pago.es_retencion():
                        if pago.tipo_retencion()==TIPO_RETENCION_IVA:
                           rec_csv.append('8')
                        else:
                            rec_csv.append('9')
                    else:
                        rec_csv.append('1')


                    if pago.es_especievalorada():
                        rec_csv.append('CER')
                    elif  pago.rubro.es_matricula():
                        rec_csv.append("MAT")
                    elif pago.rubro.es_inscripcion():
                        rec_csv.append("INS")
                    elif pago.rubro.es_otro():
                        rubro = pago.rubro.rubrootro_set.all()[:1].get()
                        tipo = rubro.tipo
                        rec_csv.append(tipo.nombre[:3].upper())
                    elif pago.rubro.es_materia():
                        rec_csv.append("ARR")
                    elif pago.rubro.es_notadebito():
                        rec_csv.append("NDB")
                    elif pago.rubro.es_cuota():
                        rec_csv.append("CUO")
                    else:
                        rec_csv.append('FAC')

                    rec_csv.append(sesion.fecha.strftime('%d-%m-%Y'))

                    inscripcion = pago.rubro.inscripcion
                    if inscripcion:
                        rec_csv.append(elimina_tildes(inscripcion.persona.nombre_completo()))

                        factura = pago.dbf_factura()
                        if factura:
                            rec_csv.append(factura.numero)

                            efec = pago.valor if pago.efectivo or pago.referido and not pago.electronico and not pago.wester and not pago.facilito and not pago.pacifico else 0
                            elec = pago.valor if pago.electronico else 0
                            wes = pago.valor if pago.wester else 0
                            pich = pago.valor if pago.pichincha else 0
                            faci = pago.valor if pago.facilito else 0
                            paci = pago.valor if pago.pacifico else 0
                            chv = pago.valor if pago.es_chequevista() or pago.es_chequepostfechado() else 0
                            tar = pago.valor if pago.es_tarjeta() else 0
                            rc = pago.valor if pago.es_recibocajainst() else 0
                            tr = pago.valor if pago.es_transferencia() else 0
                            dp = pago.valor if pago.es_deposito() else 0
                            nc = pago.valor if pago.es_notacreditoinst() else 0
                            # ret = pago.valor if pago.es_retencion() else 0
                            if  pago.es_retencion():
                                if pago.tipo_retencion()==TIPO_RETENCION_IVA:
                                    ret_iva = pago.valor if  pago.valor else 0
                                else:
                                    ret_fuente=pago.valor if  pago.valor else 0


                            rec_csv.append(efec)
                            rec_csv.append(chv)
                            rec_csv.append(tar)
                            rec_csv.append(rc)
                            rec_csv.append(tr)
                            rec_csv.append(dp)
                            rec_csv.append(nc)
                            rec_csv.append(round(efec + chv + tar + rc + tr + dp + nc + ret_iva + ret_fuente  +elec +wes+faci+pich +paci + py, 2))
                            rec_csv.append(inscripcion.carrera.alias)
                            rec_csv.append(factura.cliente.ruc)
                            if factura.cliente.direccion:
                                rec_csv.append(elimina_tildes(factura.cliente.direccion).replace('#',''))
                            else:
                                rec_csv.append('')
                            rec_csv.append(factura.cliente.telefono)
                            rec_csv.append(ret_iva)
                            rec_csv.append(ret_fuente)
                            rec_csv.append(elec)
                            rec_csv.append(wes)
                            rec_csv.append(faci)
                            rec_csv.append(pich)
                            rec_csv.append(paci)
                            rec_csv.append(py)

                            data.append(rec_csv)

                        else:
                            rec_csv.append('')

                            efec = pago.valor if pago.efectivo  or pago.referido and not pago.electronico and not pago.wester and not pago.facilito and not pago.pacifico else 0
                            elec = pago.valor if pago.electronico  else 0
                            wes = pago.valor if pago.wester  else 0
                            pich = pago.valor if pago.pichincha  else 0
                            faci = pago.valor if pago.facilito  else 0
                            paci = pago.valor if pago.pacifico  else 0
                            chv = pago.valor if pago.es_chequevista() or pago.es_chequepostfechado() else 0
                            tar = pago.valor if pago.es_tarjeta() else 0
                            rc = pago.valor if pago.es_recibocajainst() else 0
                            tr = pago.valor if pago.es_transferencia() else 0
                            dp = pago.valor if pago.es_deposito() else 0
                            nc = pago.valor if pago.es_notacreditoinst() else 0
                            # ret = pago.valor if pago.es_retencion() else 0
                            if  pago.es_retencion():
                               if pago.tipo_retencion()==TIPO_RETENCION_IVA:
                                   ret_iva = pago.valor if  pago.valor else 0
                               else:
                                   ret_fuente=pago.valor if  pago.valor else 0

                            rec_csv.append(efec)
                            rec_csv.append(chv)
                            rec_csv.append(tar)
                            rec_csv.append(rc)
                            rec_csv.append(tr)
                            rec_csv.append(dp)
                            rec_csv.append(nc)

                            rec_csv.append(round(efec + chv + tar + rc + tr + dp + nc + ret_iva + ret_fuente + elec + wes +faci + pich+ paci + py, 2))
                            rec_csv.append(inscripcion.carrera.alias)
                            rec_csv.append('')
                            rec_csv.append('')
                            rec_csv.append('')
                            rec_csv.append(ret_iva)
                            rec_csv.append(ret_fuente)
                            rec_csv.append(elec)
                            rec_csv.append(wes)
                            rec_csv.append(faci)
                            rec_csv.append(pich)
                            rec_csv.append(paci)
                            rec_csv.append(py)

                            data.append(rec_csv)

                    else:
                        pass

                # Cheques a la fecha cobrados este dia
                pagos_cheques_post_hoy = Pago.objects.filter(pagocheque__protestado=False, sesion__caja=caja, pagocheque__fechacobro=fecha)
                for pago in pagos_cheques_post_hoy:
                    if not pago.es_chequepostfechado():
                        continue
                    rec_csv = []

                    if pago.es_chequepostfechado():
                        rec_csv.append('2')
                    elif pago.es_recibocajainst():
                        rec_csv.append('4')
                    elif pago.es_notacreditoinst():
                        rec_csv.append('6')
                    # elif pago.es_retencion():
                    #     rec_csv.append('8')
                    elif  pago.es_retencion():
                        if pago.tipo_retencion()==TIPO_RETENCION_IVA:
                           rec_csv.append('8')
                        else:
                            rec_csv.append('9')

                    else:
                        rec_csv.append('1')

                    if pago.es_especievalorada():
                        rec_csv.append('CER')
                    elif pago.rubro.es_matricula():
                        rec_csv.append("MAT")
                    elif pago.rubro.es_inscripcion():
                        rec_csv.append("INS")
                    elif pago.rubro.es_otro():
                        rubro = pago.rubro.rubrootro_set.all()[:1].get()
                        tipo = rubro.tipo
                        rec_csv.append(tipo.nombre[:3].upper())
                    elif pago.rubro.es_cuota():
                        rec_csv.append("CUO")
                    else:
                        rec_csv.append('FAC')

                    rec_csv.append(sesion.fecha.strftime("%d-%m-%Y"))

                    inscripcion = pago.rubro.inscripcion
                    if inscripcion:
                        rec_csv.append(elimina_tildes(inscripcion.persona.nombre_completo()))

                        factura = pago.dbf_factura()
                        if factura:
                            rec_csv.append(factura.numero)
                            py=0
                            efec = pago.valor if pago.efectivo  or pago.referido and not pago.electronico and not pago.wester and not pago.facilito and not pago.pacifico else 0
                            elec = pago.valor if pago.electronico  else 0
                            wes = pago.valor if pago.wester  else 0
                            pich = pago.valor if pago.pichincha  else 0
                            faci = pago.valor if pago.facilito  else 0
                            paci = pago.valor if pago.pacifico  else 0
                            chv = pago.valor if pago.es_chequevista() or pago.es_chequepostfechado() else 0
                            tar = pago.valor if pago.es_tarjeta() else 0
                            rc = pago.valor if pago.es_recibocajainst() else 0
                            tr = pago.valor if pago.es_transferencia() else 0
                            dp = pago.valor if pago.es_deposito() else 0
                            nc = pago.valor if pago.es_notacreditoinst() else 0
                            # ret = pago.valor if pago.es_retencion() else 0
                            ret_iva=0
                            ret_fuente=0
                            if  pago.es_retencion():
                               if pago.tipo_retencion()==TIPO_RETENCION_IVA:
                                   ret_iva = pago.valor if  pago.valor else 0
                               else:
                                   ret_fuente = pago.valor if  pago.valor else 0

                            rec_csv.append(efec)
                            rec_csv.append(chv)
                            rec_csv.append(tar)
                            rec_csv.append(rc)
                            rec_csv.append(tr)
                            rec_csv.append(dp)
                            rec_csv.append(nc)

                            rec_csv.append(round(efec + chv + tar + rc + tr + dp + nc + ret_iva + ret_fuente + elec+wes + faci + pich+ paci + py,  2))
                            rec_csv.append(inscripcion.carrera.alias)
                            rec_csv.append(factura.cliente.ruc)
                            if factura.cliente.direccion:
                                rec_csv.append(elimina_tildes(factura.cliente.direccion).replace('#',''))
                            else:
                                rec_csv.append('')
                            rec_csv.append(factura.cliente.telefono)
                            # rec_csv.append(ret)
                            data.append(rec_csv)

                        else:
                            pass

                # Recibos de Caja
                for rci in sesion.recibocajainstitucion_set.all().exclude(activo=False):
                    rec_csv = []

                    rec_csv.append('5')
                    rec_csv.append('RCF')
                    rec_csv.append(rci.fecha.strftime("%d-%m-%Y"))

                    inscripcion = rci.inscripcion
                    if inscripcion:
                        rec_csv.append(elimina_tildes(inscripcion.persona.nombre_completo()))

                        rec_csv.append('')

                        efec = 0
                        elec = 0
                        wes = 0
                        faci=0
                        paci=0
                        py=0
                        chv = 0
                        tar = 0
                        rc = rci.valorinicial
                        tr = 0
                        dp = 0
                        nc = 0
                        ret_iva = 0
                        ret_fuente = 0
                        pich = 0

                        rec_csv.append(efec)
                        rec_csv.append(chv)
                        rec_csv.append(tar)
                        rec_csv.append(rc)
                        rec_csv.append(tr)
                        rec_csv.append(dp)
                        rec_csv.append(nc)
                        rec_csv.append(round(efec + chv + tar + rc + tr + dp + nc + ret_iva + ret_fuente + elec + wes+faci+pich+paci + py, 2))
                        rec_csv.append(inscripcion.carrera.alias)
                        rec_csv.append('')
                        rec_csv.append('')
                        rec_csv.append('')
                        rec_csv.append(ret_iva)
                        rec_csv.append(ret_fuente)
                        rec_csv.append(elec)
                        rec_csv.append(wes)
                        rec_csv.append(faci)
                        rec_csv.append(pich)
                        rec_csv.append(paci)
                        rec_csv.append(py)

                        data.append(rec_csv)

                    else:
                        pass


                # Notas de Creditos
                for nc in sesion.notacreditoinstitucion_set.filter(anulada=False).exclude(tipo__id=TIPO_NC_ANULACION):
                    rec_csv = []
                    if nc.factura.fecha > datetime(2016,5,31).date() and nc.factura.fecha <  datetime(2017,7,1).date() and DEFAULT_PASSWORD=='casade':
                        rec_csv.append('7-1')
                    else:
                        rec_csv.append('7')
                    rec_csv.append('NCF')
                    rec_csv.append(nc.fecha.strftime("%d-%m-%Y"))

                    inscripcion = nc.inscripcion
                    if inscripcion:
                        rec_csv.append(elimina_tildes(inscripcion.persona.nombre_completo()))

                        rec_csv.append('')

                        efec = 0
                        elec = 0
                        wes = 0
                        faci = 0
                        paci = 0
                        py = 0
                        chv = 0
                        tar = 0
                        rc = 0
                        tr = 0
                        dp = 0
                        ret_iva = 0
                        ret_fuente = 0
                        pich = 0
                        nc = nc.valor

                        rec_csv.append(efec)
                        rec_csv.append(chv)
                        rec_csv.append(tar)
                        rec_csv.append(rc)
                        rec_csv.append(tr)
                        rec_csv.append(dp)
                        rec_csv.append(nc)
                        rec_csv.append(round(efec + chv + tar + rc + tr + dp + nc + ret_iva + ret_fuente + elec + wes + faci + pich + paci + py, 2))
                        rec_csv.append(inscripcion.carrera.alias)
                        rec_csv.append(inscripcion.persona.cedula)
                        rec_csv.append('')
                        rec_csv.append('')
                        rec_csv.append(ret_iva)
                        rec_csv.append(ret_fuente)
                        rec_csv.append(elec)
                        rec_csv.append(wes)
                        rec_csv.append(faci)
                        rec_csv.append(pich)
                        rec_csv.append(paci)
                        rec_csv.append(py)

                        data.append(rec_csv)

                for ncr in sesion.notacreditoinstitucion_set.filter(anulada=False).exclude(tipo__id=TIPO_NC_DEVOLUCION):
                    rec_csv = []
                    if ncr.factura.fecha > datetime(2016,5,31).date() and ncr.factura.fecha <  datetime(2017,7,1).date() and DEFAULT_PASSWORD=='casade':
                        rec_csv.append('10-1')
                    else:
                        rec_csv.append('10')
                    # rec_csv.append('10')
                    rec_csv.append('NCD')
                    rec_csv.append(ncr.fecha.strftime("%d-%m-%Y"))
                    invoice = representacion_factura_str2(ncr.factura)

                    inscripcion = ncr.inscripcion
                    if inscripcion:
                        rec_csv.append(elimina_tildes(inscripcion.persona.nombre_completo()))

                        rec_csv.append('')

                        efec = 0
                        elec = 0
                        faci=0
                        pich=0
                        paci=0
                        py=0
                        wes = 0
                        chv = 0
                        tar = 0
                        rc = 0
                        tr = 0
                        dp = 0

                        vesp = 0
                        vins = 0
                        vmat = 0
                        vcuo = 0
                        votr = 0
                        varr = 0
                        vexa = 0
                        vper = 0
                        vgeo = 0
                        vbox = 0
                        vtra = 0
                        vsol = 0
                        vcon = 0
                        vcre = 0

                        ret_iva = 0
                        ret_fuente = 0
                        nc = ncr.valor

                        rec_csv.append(efec)
                        rec_csv.append(chv)
                        rec_csv.append(tar)
                        rec_csv.append(rc)
                        rec_csv.append(tr)
                        rec_csv.append(dp)
                        rec_csv.append(nc)
                        rec_csv.append(round(efec + chv + tar + rc + tr + dp + nc + ret_iva + ret_fuente  + elec+wes + faci + pich + paci + py, 2))
                        rec_csv.append(inscripcion.carrera.alias)
                        rec_csv.append(inscripcion.persona.cedula)
                        rec_csv.append('')
                        rec_csv.append('')
                        rec_csv.append(ret_iva)
                        rec_csv.append(ret_fuente)
                        rec_csv.append(elec)
                        rec_csv.append(wes)
                        rec_csv.append(faci)
                        rec_csv.append(pich)
                        rec_csv.append(paci)
                        rec_csv.append(py)


                        for pagos in invoice['pagos']:
                            if pagos['rubro']['tipo'] == 'ESPECIE' and pagos['rubro']['fp'] != 2:
                                vesp = vesp + pagos['valor']

                            elif pagos['rubro']['tipo'] == 'INSCRIPCION' and pagos['rubro']['fp'] != 2:
                                vins = vins + pagos['valor']

                            elif pagos['rubro']['tipo'] == 'MATRICULA' and pagos['rubro']['fp'] != 2:
                                vmat = vmat + pagos['valor']

                            elif (pagos['rubro']['tipo'] == 'CUOTA' or pagos['rubro']['tipo'] == 'CONVALIDACION') and pagos['rubro']['fp'] != 2:
                                vcuo = vcuo + pagos['valor']

                            elif pagos['rubro']['tipo'] == 'MATERIA' and pagos['rubro']['fp'] != 2:
                                varr = varr + pagos['valor']

                            elif pagos['rubro']['tipo'] == 'EXAMEN PSICOSENSOMETRICO' and pagos['rubro']['fp'] != 2:
                                vexa = vexa + pagos['valor']

                            elif pagos['rubro']['tipo'] == 'PERMISO DE CONDUCCION' and pagos['rubro']['fp'] != 2:
                                vper = vper + pagos['valor']

                            elif pagos['rubro']['tipo'] == 'GEOGRAFIA DEL ECUADOR' and pagos['rubro']['fp'] != 2:
                                vgeo = vgeo + pagos['valor']

                            elif pagos['rubro']['tipo'] == 'BOX CONSULTA' and pagos['rubro']['fp'] != 2:
                                vbox = vbox+ pagos['valor']

                            elif pagos['rubro']['tipo'] == 'TRATAMIENTO' and pagos['rubro']['fp'] != 2:
                                vtra = vtra+ pagos['valor']

                            elif pagos['rubro']['tipo'] == 'SOLICITUD ONLINE' and pagos['rubro']['fp'] != 2:
                                vsol = vsol+ pagos['valor']

                            elif pagos['rubro']['tipo'] == 'CONGRESO' and pagos['rubro']['fp'] != 2:
                                vcon = vcon+ pagos['valor']

                            elif pagos['rubro']['tipo'] == 'CREDENCIAL' and pagos['rubro']['fp'] != 2:
                                vcre = vcre+ pagos['valor']


                            else :
                                # pagos['rubro']['tipo'] == 'OTRO'
                                if  pagos['rubro']['fp'] != 2:
                                    votr = votr + pagos['valor']



                        # if vesp:
                        rec_csv.append("CER")
                        rec_csv.append(vesp)

                        # if vins:
                        rec_csv.append("INS")
                        rec_csv.append(vins)

                        # if vmat:
                        rec_csv.append("MAT")
                        rec_csv.append(vmat)

                        # if vcuo:
                        rec_csv.append("CUO")
                        rec_csv.append(vcuo)

                        # if votr:
                        rec_csv.append("FAC")
                        rec_csv.append(votr)

                        # if varr:
                        rec_csv.append("ARR")
                        rec_csv.append(varr)

                        rec_csv.append("EXA")
                        rec_csv.append(vexa)

                        rec_csv.append("PER")
                        rec_csv.append(vper)

                        rec_csv.append("GEO")
                        rec_csv.append(vgeo)

                        rec_csv.append("BOX")
                        rec_csv.append(vbox)

                        rec_csv.append("TRA")
                        rec_csv.append(vtra)
                        rec_csv.append("SOL")
                        rec_csv.append(vsol)
                        rec_csv.append("CON")
                        rec_csv.append(vcon)

                        rec_csv.append("CRE")
                        rec_csv.append(vcre)
                        e = 0
                        el = 0
                        we = 0
                        ch = 0
                        tar = 0
                        r = 0
                        tra = 0
                        d = 0
                        n = 0
                        py=0
                        for p in  ncr.factura.pagos.all() :
                            if p.efectivo or p.referido or p.es_chequevista()  :
                                e = e + p.valor
                            if  p.es_chequepostfechado():
                                ch = ch + p.valor
                            if p.es_tarjeta():
                                tar =  tar + p.valor
                            if p.es_recibocajainst():
                                r = r + p.valor
                            if p.es_transferencia():
                                tra = tra + p.valor
                            if p.es_deposito() :
                                d = d + p.valor
                            if p.es_notacreditoinst():
                                n = n + p.valor
                            if p.electronico:
                               el = el + p.valor
                            if p.wester:
                               we = we + p.valor
                            if p.facilito:
                               faci = faci + p.valor

                            if p.pichincha:
                               pich = pich + p.valor

                            if p.pacifico:
                               paci = paci + p.valor
                        rec_csv.append("EFE")
                        rec_csv.append(e)
                        rec_csv.append("CHE")
                        rec_csv.append(ch)
                        rec_csv.append("TAR")
                        rec_csv.append(tar)
                        rec_csv.append("REC")
                        rec_csv.append(r)
                        rec_csv.append("TRA")
                        rec_csv.append(tra)
                        rec_csv.append("DEP")
                        rec_csv.append(d)
                        rec_csv.append("NC")
                        rec_csv.append(n)
                        rec_csv.append("ELE")
                        rec_csv.append(el)
                        rec_csv.append("WES")
                        rec_csv.append(we)
                        rec_csv.append("FACI")
                        rec_csv.append(faci)
                        rec_csv.append("PICH")
                        rec_csv.append(pich)
                        rec_csv.append("PACI")
                        rec_csv.append(paci)
                        rec_csv.append("PAY")
                        rec_csv.append(py)
                        data.append(rec_csv)

                    else:
                        pass

        return data
    except Exception as ex:
        print(ex)
        return {}

def exportacion_estd_itb (grupo):
    ma = Matricula.objects.filter(nivel__cerrado=False, nivel__grupo__nombre=grupo).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')
    data = []
    for m in ma:
        datos = []
        try:
            # datos.append(m.inscripcion.persona.apellido1.encode("ascii","ignore"))
            # datos.append(m.inscripcion.persona.apellido2.encode("ascii","ignore"))
            # datos.append(m.inscripcion.persona.nombres.encode("ascii","ignore"))

            datos.append(m.inscripcion.persona.apellido1)
            datos.append(m.inscripcion.persona.apellido2)
            datos.append(m.inscripcion.persona.nombres)
            if m.inscripcion.persona.cedula:
                datos.append(m.inscripcion.persona.cedula)
            else:
                datos.append(m.inscripcion.persona.pasaporte)
            datos.append(m.inscripcion.persona.pasaporte)
            datos.append(m.inscripcion.persona.telefono_conv)
            datos.append(m.inscripcion.persona.telefono)
            datos.append(m.inscripcion.persona.email)
            datos.append(m.inscripcion.persona.direccion)
            datos.append(m.inscripcion.persona.direccion2)
            data.append(datos)
        except Exception as ex:
            pass
    return data

def autenticaAD(request):
    try:
        import requests
        listnombre = []
        for p in Persona.objects.filter(usuario__date_joined__year=datetime.now().year,usuario__date_joined__month=datetime.now().month,usuario__date_joined__day=datetime.now().day,activedirectory=False)[:1]:
            nombre= p.nombres
            apellido= p.apellido1 +" "+p.apellido2
            password= NEW_PASSWORD
            usertipo= "ADMINISTRATIVO"
            if Inscripcion.objects.filter(persona=p).exists():
                usertipo= "INSCRIPCION"
            if Profesor.objects.filter(persona=p).exists():
                usertipo= "DOCENTE"
            newuser= p.usuario.username

            import subprocess
            # if you want output
            userdata = {"nombre": nombre, "apellido": apellido, "password": password,
                        "usertipo": usertipo, "newuser": newuser}
            # proc = subprocess.Popen("C:/xampp/php/php.exe " + SITE_ROOT + "/scriptphpadd.php " + json.dumps(userdata), shell=True, stdout=subprocess.PIPE).stdout.read()
            try:
                script_response1 = subprocess.check_output(["/bin/php", MEDIA_ROOT + "/scriptphp/scriptphpadd.php",json.dumps(userdata)])
                scriptresponse = str(script_response1.decode())
                if 'Usuario creado' in scriptresponse:
                    p.activedirectory = True
                    p.save()
                print(script_response1)
            except Exception as ex:
                scriptresponse = "Error Ex " + str(ex)
            listnombre.append((p.nombre_completo(),scriptresponse,usertipo))
        # script_response = proc.stdout.read()
        if EMAIL_ACTIVE and listnombre:
            print("eemail")
            tipo = TipoIncidencia.objects.get(pk=16)
            hoy = datetime.now().today()
            contenido = "REPORTE DE CREACION DE USUARIOS EN ACTIVE DIRECTORY"
            send_html_mail("CREACION DE USUARIOS EN ACTIVE DIRECTORY",
                "emails/addactivedirectory.html", {'lista': listnombre, 'fecha': hoy,'contenido': contenido},tipo.correo.split(","))
        return HttpResponse(json.dumps({"result":"ok","nombres":json.dumps(listnombre)}), content_type="application/json")

    except Exception as ex:
        return HttpResponse(json.dumps({"result": str(ex)}), content_type="application/json")

def editclaveAD(request):
    try:
        import requests
        nombre= "Juan Jose"
        apellido= "Urgiles Arizabal"
        password= "0924774532"
        usertipo= "ADMINISTRATIVO"
        newuser= "jjurgiles859"
        userdata = nombre,apellido,password,usertipo,newuser
        import subprocess

        # if the script don't need output.
        pathphp = SITE_ROOT
        # if you want output
        userdata = {"user": "jurgesh", "oldpassword": "MyPassword1234",
                    "newassword": "MypassWord4321", "newasswordcnf": "MypassWord4321"}
        # proc = subprocess.Popen("C:/xampp/php/php.exe " + SITE_ROOT + "/scriptphpadd.php " + json.dumps(userdata), shell=True, stdout=subprocess.PIPE).stdout.read()
        script_response1 = subprocess.check_output(["/bin/php", MEDIA_ROOT + "/scriptphp/scriptphpeditclave.php",json.dumps(userdata)])
        print("ejecuto script")
        print(script_response1)
        # script_response = proc.stdout.read()
        return HttpResponse(json.dumps({"script_response1":str(script_response1.decode())}), content_type="application/json")

    except Exception as ex:
        return HttpResponse(json.dumps({"result": str(ex)}), content_type="application/json")

def exportacion_datos_rol_administrativos(fechai, fechaf):
    data = {}
    datos = []
    asistentes_cobranzas = AsistAsuntoEstudiant.objects.filter(estado=True).order_by('asistente__apellido1')
    personal = Persona.objects.filter(id__in=asistentes_cobranzas.values('asistente'))
    for p in personal:
        datos_ind = {}
        if AsistAsuntoEstudiant.objects.filter(asistente=p).exists():
            asist_cobranzas = AsistAsuntoEstudiant.objects.filter(asistente=p)[:1].get()
            datos_ind['valor'] =  asist_cobranzas.valor_comision_xfecha(fechai, fechaf)
            datos_ind['identificacion'] = p.cedula if p.cedula else p.pasaporte
            datos.append(datos_ind)
    data['comision_cobranzas'] = datos
    return data

def cerrar_materias(request):
    #OCU 09-junio-2020 funcion para el cierre automatico de la materia a 4 dias de la fecha de fin de la misma
    diferencia = 0
    hoy=datetime.now().date()

    #Primero verifico que las multas por materia cerrada esten vigentes sino cambiar estado a inactiva
    fechahoy=datetime.now()

    if MultaDocenteMateria.objects.filter(tipomulta=4,activo=True).exists():
        for mat in MultaDocenteMateria.objects.filter(tipomulta=4,activo=True):
            if not fechahoy <= mat.fechahasta:
                mat.activo=False
                mat.save()
                materia= Materia.objects.get(pk=mat.materia.id)
                if not materia.cerrado:
                    materia.cerrado=True
                    materia.save()

    #Luego las multas por 24 horas que ya no esten vigentes cambiar estado a inactiva
    if MultaDocenteMateria.objects.filter(tipomulta=MULTA24H,activo=True).exists():
        for multa24h in MultaDocenteMateria.objects.filter(tipomulta=MULTA24H,activo=True):
            if not fechahoy <= multa24h.fechahasta:
                multa24h.activo=False
                multa24h.save()

    #Luego las multas por 48 horas que ya no esten vigentes cambiar estado a inactiva
    if MultaDocenteMateria.objects.filter(tipomulta=MULTA48H,activo=True).exists():
        for multa48h in MultaDocenteMateria.objects.filter(tipomulta=MULTA48H,activo=True):
            if not fechahoy <= multa48h.fechahasta:
                multa48h.activo=False
                multa48h.save()
    mat=''
    if Materia.objects.filter(cerrado=False,fin__gte='2020-01-01',fin__lte=hoy).exists():
    #if Materia.objects.filter(cerrado=False,fin__gte='2020-01-01',fin__lte=hoy,pk=32315).exists():
        sid = transaction.savepoint()
        try:
            for mat in Materia.objects.filter(cerrado=False,fin__gte='2020-01-01',fin__lte=hoy).order_by('fin'):
            #for mat in Materia.objects.filter(cerrado=False,fin__gte='2020-01-01',fin__lte=hoy,pk=32315).order_by('fin'):
                #print(mat)
                totencurso=0
                totrecuperacion=0
                totalalumnoabs=0
                totalalumnos=0
                totalexamen=0
                promedioaprobado=0
                promedioreprobado=0
                promediorecuperacion=0
                promedioexamen=0
                totestudiantes=0
                fecha_cierre=mat.fin
                diferencia=(datetime.now().date()- fecha_cierre).days

                if diferencia>=4:
                    if not mat.nivel.cerrado and not mat.cerrado:
                        profesormateria=''
                        if MateriaAsignada.objects.filter(materia=mat).exists():
                            nivel=MateriaAsignada.objects.filter(materia=mat)[:1].get().matricula.nivel
                            inscrip=Inscripcion.objects.filter(id__in=MateriaAsignada.objects.filter(materia=mat).values("matricula__inscripcion")).exclude(retiradomatricula__activo=False,retiradomatricula__nivel=nivel).values('id')
                            if ProfesorMateria.objects.filter(materia=mat).exists():
                                if ProfesorMateria.objects.filter(materia=mat,profesor_aux=None).exists():
                                    profesormateria=ProfesorMateria.objects.filter(materia=mat,profesor_aux=None)[:1].get()
                                else:
                                    if ProfesorMateria.objects.filter(materia=mat).exists():
                                        profesormateria = ProfesorMateria.objects.filter(materia=mat)[:1].get()
                                    else:
                                        profesormateria=''

                                if  profesormateria!='':
                                    if profesormateria.segmento.id == TIPOSEGMENTO_PRACT:
                                        promedioreprobado = int(round(round(MateriaAsignada.objects.filter(Q(matricula__inscripcion__id__in=inscrip,materia=mat,notafinal__lt=NOTA_PARA_APROBAR),Q(absentismo=None)|Q(absentismo=False)).count()*100)/round(MateriaAsignada.objects.filter(Q(matricula__inscripcion__id__in=inscrip,materia=mat),Q(absentismo=None)|Q(absentismo=False)).count())))
                                        promedioaprobado = int(round(round(MateriaAsignada.objects.filter(Q(matricula__inscripcion__id__in=inscrip,materia=mat,notafinal__gte=NOTA_PARA_APROBAR),Q(absentismo=None)|Q(absentismo=False)).count()*100)/round(MateriaAsignada.objects.filter(Q(matricula__inscripcion__id__in=inscrip,materia=mat),Q(absentismo=None)|Q(absentismo=False)).count())))
                                        totalreprobado = MateriaAsignada.objects.filter(Q(matricula__inscripcion__id__in=inscrip,materia=mat,notafinal__lt=NOTA_PARA_APROBAR,asistenciafinal__lt=ASIST_PARA_APROBAR),Q(absentismo=None)|Q(absentismo=False)).count()
                                        totalaprobado = MateriaAsignada.objects.filter(Q(matricula__inscripcion__id__in=inscrip,materia=mat,notafinal__gte=NOTA_PARA_APROBAR),Q(absentismo=None)|Q(absentismo=False)).count()
                                        resumreprobadoasist = 0
                                        resumreprobadonota = MateriaAsignada.objects.filter(Q(matricula__inscripcion__id__in=inscrip,materia=mat),Q(notafinal__lt=NOTA_PARA_APROBAR),Q(absentismo=None)|Q(absentismo=False)).count()
                                    else:
                                        materiaasignada=MateriaAsignada.objects.filter(Q(materia=mat),Q(absentismo=None)|Q(absentismo=False)).values('id')
                                        totencurso= EvaluacionITB.objects.filter(materiaasignada__id__in=materiaasignada,materiaasignada__matricula__inscripcion__id__in=inscrip,estado=NOTA_ESTADO_EN_CURSO).count()
                                        totrecuperacion= EvaluacionITB.objects.filter(materiaasignada__id__in=materiaasignada,materiaasignada__matricula__inscripcion__id__in=inscrip,estado=NOTA_ESTADO_SUPLETORIO).count()
                                        totalreprobado= EvaluacionITB.objects.filter(materiaasignada__id__in=materiaasignada,materiaasignada__matricula__inscripcion__id__in=inscrip,estado=NOTA_ESTADO_REPROBADO).count()
                                        totalexamen= EvaluacionITB.objects.filter(materiaasignada__id__in=materiaasignada,materiaasignada__matricula__inscripcion__id__in=inscrip,estado=NOTA_ESTADO_DERECHOEXAMEN).count()
                                        totalaprobado= (EvaluacionITB.objects.filter(Q(materiaasignada__id__in=materiaasignada,materiaasignada__matricula__inscripcion__id__in=inscrip,estado=NOTA_ESTADO_APROBADO),Q(materiaasignada__absentismo=None)|Q(materiaasignada__absentismo=False)).count())
                            else:
                                pass

                            if profesormateria!='':
                                totalalumnos = MateriaAsignada.objects.filter(matricula__inscripcion__id__in=inscrip,materia=mat).count()
                                totalalumnoabs = MateriaAsignada.objects.filter(matricula__inscripcion__id__in=inscrip,materia=mat,absentismo=True).count()
                                totalbecados = MateriaAsignada.objects.filter(Q(matricula__inscripcion__id__in=inscrip,materia=mat,matricula__becado=True),Q(absentismo=None)|Q(absentismo=False)).count()
                                totestudiantes=totalalumnos-totencurso-totalalumnoabs

                            if totestudiantes>0:
                                promedioaprobado = int(round((round(totalaprobado*100)/totestudiantes)))
                                promedioreprobado = int(round((round(totalreprobado*100)/totestudiantes)))
                                promediorecuperacion = int(round((round(totrecuperacion*100)/totestudiantes)))
                                promedioexamen = int(round((round(totalexamen*100)/totestudiantes)))
                        else:
                            mat.cerrado=True
                            mat.fechacierre = datetime.now()
                            mat.horacierre = datetime.now().time()
                            mat.save()
                            mat.fechaalcance =mat.fechacierre + timedelta(days=14)
                            mat.save()
                            if DEFAULT_PASSWORD == 'itb':
                                if profesormateria!='':
                                    mat.cerrado=True
                                    mat.fechacierre = datetime.now()
                                    mat.horacierre = datetime.now().time()
                                    mat.save()
                                    mat.fechaalcance =mat.fechacierre + timedelta(days=14)
                                    mat.save()
                                    mat.correo_cierre_sistema(totalalumnos,totalalumnoabs,totalaprobado,promedioaprobado,promedioreprobado,profesormateria,totalbecados,totalreprobado,totencurso,totrecuperacion,totestudiantes,promediorecuperacion,totalexamen,promedioexamen)
            return False
        except Exception as ex :
            transaction.savepoint_rollback(sid)
            print(mat)
    else:
        return False

def verifica_absentismos(request):
    ids=[]
    if Absentismo.objects.filter(finalizado=False).exists():
        try:
            asistentes = PersonaAsuntos.objects.filter(estado=True).distinct('id').values('id')
            contador = PersonaAsuntos.objects.filter(estado=True).distinct('id').values('id').count()
            contaasi = 0
            absentismos = Absentismo.objects.filter(finalizado=False)
            for a in absentismos:
                if RecordAcademico.objects.filter(aprobada=True, inscripcion=a.materiaasignada.matricula.inscripcion, asignatura=a.materiaasignada.materia.asignatura).exists()\
                    or MateriaAsignada.objects.filter(materia__asignatura=a.materiaasignada.materia.asignatura, matricula__inscripcion=a.materiaasignada.matricula.inscripcion,
                                                  materia__inicio__gt=a.materiaasignada.materia.inicio).exclude(materia=a.materiaasignada.materia).exists()\
                    or a.materiaasignada.materia.cerrado or not a.materiaasignada.matricula.inscripcion.persona.usuario.is_active or a.materiaasignada.materia.fin < datetime.now().date():

                    a.finalizado = True
                    ids.append(a.id)
                    a.save()
                else:

        # ----------ASIGNAR ASISTENTES-------------------------------------------------
                    if contaasi > contador -1:
                        contaasi = 0
                    if not a.materiaasignada.matricula.inscripcion.personaasuntos:
                        asis = PersonaAsuntos.objects.filter(pk=asistentes[contaasi]['id'])[:1].get()
                        a.materiaasignada.matricula.inscripcion.personaasuntos = asis
                        a.materiaasignada.matricula.inscripcion.save()
                        contaasi = contaasi +1
            print(ids)
        except Exception as ex:
            print(ex)
            pass

    if SeguimientoAbsentismoDetalle.objects.filter(seguimientoabsentismo__estado=True, finalizado=False).exclude(absentismo__fechareintegro=None).exists():
        seguimientos_detalle = SeguimientoAbsentismoDetalle.objects.filter(seguimientoabsentismo__estado=True, finalizado=False).exclude(absentismo__fechareintegro=None)
        for f in seguimientos_detalle:
            if f.fecha_posiblereintegro >= datetime.now().date():
                if Leccion.objects.filter(fecha=f.absentismo.fecha).exists():
                    fechas = []
                    fecha_seguimiento = f.seguimientoabsentismo.fecha
                    if f.fecha_posiblereintegro <= f.absentismo.materiaasignada.materia.fin:
                        fecha_ultima_clase = f.fecha_posiblereintegro
                    else:
                        fecha_ultima_clase = f.absentismo.materiaasignada.materia.fin

                    clases = Clase.objects.filter(materia=f.absentismo.materiaasignada.materia)
                    print(fecha_seguimiento)
                    fecha = fecha_seguimiento
                    for i in range(((f.absentismo.fechareintegro - fecha_seguimiento).days+1)):
                        print(fecha)
                        if clases.filter(dia=fecha.isoweekday()).exists():
                            fechas.append(str(fecha))
                            # if AsistenciaLeccion.objects.filter(leccion__fecha=fecha, asistio=True, matricula=f.absentismo.materiaasignada.matricula, leccion__clase__materia=f.absentismo.materiaasignada.materia).exists():
                        fecha = fecha + timedelta(days=1)

                    num_dias = len(fechas)
                    if CategoriaAbsentismo.objects.filter(estado=True, numdiasminimo__lte=num_dias, numdiasmaximo__gte=num_dias).exists():
                        categoria = CategoriaAbsentismo.objects.filter(estado=True, numdiasminimo__lte=num_dias, numdiasmaximo__gte=num_dias)[:1].get()
                        f.categoria = categoria
                    f.comision = True
                    f.finalizado = True
                    f.save()
                    print(fechas)
            else:
                f.finalizado = True
                f.save()

    # ----------FINALIZAR SEGUIMIENTOS-------------------------------------------------
    if SeguimientoAbsentismo.objects.filter(estado=True).exists():
        for s in SeguimientoAbsentismo.objects.filter(estado=True):
            if SeguimientoAbsentismoDetalle.objects.filter(seguimientoabsentismo=s).exists():
                seg = SeguimientoAbsentismoDetalle.objects.filter(seguimientoabsentismo=s)
                if seg.count() == seg.filter(finalizado=True).count():
                    s.estado = False
                    s.save()
            else:
                s.estado = False
                s.save()