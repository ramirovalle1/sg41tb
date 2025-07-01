import datetime
from datetime import timedelta, date
from decimal import Decimal
import xlwt
import locale
import os
from django.db import transaction
from django.utils.encoding import force_str
import json
import threading
from django.contrib.admin.models import LogEntry, DELETION, ADDITION, CHANGE
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models.aggregates import Max, Sum
from django.db.models.query_utils import Q
from django.forms.models import model_to_dict
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render
from django.template import RequestContext

from fpdf import FPDF
import requests
from suds.client import Client

from decorators import secure_module, inhouse_only
from settings import ACEPTA_PAGO_TARJETA, ACEPTA_PAGO_CHEQUE, ACEPTA_PAGO_EFECTIVO, FORMA_PAGO_EFECTIVO, \
    FORMA_PAGO_TARJETA, FORMA_PAGO_CHEQUE, \
    FORMA_PAGO_DEPOSITO, FORMA_PAGO_TRANSFERENCIA, FORMA_PAGO_NOTA_CREDITO, TIPO_MORA_RUBRO, RECTORADO_GROUP_ID, \
    SISTEMAS_GROUP_ID, \
    TIPO_AYUDA_FINANCIERA, TIPO_BECA_SENESCYT, CENTRO_EXTERNO, FORMA_PAGO_RECIBOCAJAINSTITUCION, MODELO_IMPRESION_NUEVO, \
    FACTURACION_CON_IVA, \
    COEFICIENTE_CALCULO_BASE_IMPONIBLE, UTILIZA_FACTURACION_CON_FPDF, JR_USEROUTPUT_FOLDER, MEDIA_URL, \
    POSICIONES_IMPRESION, FORMA_PAGO_RETENCION, \
    EVALUACION_CASADE, MODELO_EVALUACION, EMAIL_ACTIVE, AMBIENTE_FACTURACION, EMISION_ELECTRONICA, CODIGO_NUMERICO_ELEC, \
    CONSUMIDOR_FINAL, \
    IDENTIFICACION_COMPRADOR, IVA_FACTU_ELECTRONICA, ATS_PATH, CODIGO_INFORMACION_INSTITUTO, FACTURACION_ELECTRONICA, \
    DIR_COMPRO, EXCLUYE_NIVEL, FORMA_PAGO_WESTER, \
    INSCRIPCION_CONDUCCION, VALOR_PERMISO_CONDU, FORMA_PAGO_TARJETA_DEB, FORMA_PAGO_ELECTRONICO, VALIDA_IP_CAJA, \
    VALIDAR_PAGO_RUBRO, TIPO_CONGRESO_RUBRO, \
    DEFAULT_PASSWORD, ESPECIE_CAMBIO_PROGRAMACION, VALIDA_DEUDA_EXAM_ASIST, ID_TIPO_ESPECIE_REG_NOTA, ENVIAR_CODIGO_CEL, \
    PROMOCION_GYM, DIAS_ESPECIE, \
    HABILITA_APLICA_DESCUE, PORCENTAJE_DESCUENTO, CUOTAS_CANCELAR, PORCENTAJE_DESC_CUOTAS, VALIDA_PROMOCION_EMERG, \
    INICIO_DIFERIR, FIN_DIFERIR, TIPO_NC_DEVOLUCION, \
    CAJA_ONLINE, MEDIA_ROOT, PORCENTAJE_DESCUENTO15, ESPECIE_TRAMITES_VARIOS, NIVEL_MALLA_UNO, HABILITA_DESC_MATRI, \
    DESCUENTO_MATRIC_PORCENT, TIPO_RUBRO_CREDENCIAL, CP_PROFILE_DIR, TIPO_OTRO_FRAUDE,TIPO_RUBRO_MATERIALAPOYO
from sga import number_to_letter
from sga.commonviews import addUserData, ip_client_address,process_request
from sga.facturacionelectronica import facturacionelectronicaeject, mail_errores_autorizacion, notacreditoelectronica
from sga.forms import PagoForm, EspecieForm, RubroForm, NotaCreditoForm, FormaPagoForm, DonacionForm, DonacionporAplicarForm, ReciboCajaInstitucionForm, DescuentoForm, \
     DetalleDescuentoForm, FormaPagoPermForm, RubroFechaForm, EliminaRubroForm,MotivoAnulacionForm, LiquidaRubroForm,CambioPromocionForm, AutorizarWesterForm, \
     InscripcionFlaForm, CambioValoresRecibosForm,CambioValorRubroForm,DescuentoDobeForm
from sga.inscripciones import MiPaginador
from sga.models import Inscripcion, Rubro, Pago, Banco, ProcesadorPagoTarjeta, Matricula, MateriaAsignada, TipoOtroRubro,\
    RubroMatricula, RubroMateria, RubroOtro, LugarRecaudacion, SesionCaja, Persona, ClienteFactura,RubroReceta,RecetaVisitaBox, \
    PagoTarjeta, PagoCheque, Factura,InscripcionFlags, RubroEspecieValorada, NotaCredito, PagoTransferenciaDeposito,\
    PagoNotaCredito, TipoTarjetaBanco, CuentaBanco, TipoEspecieValorada, RubroNotaDebito, Donacion, PagoReciboCajaInstitucion,\
    ReciboCajaInstitucion, PagoNotaCreditoInstitucion, NotaCreditoInstitucion, PagoRetencion, TipoRetencion,prettify,TituloInstitucion,LugarRecaudacion,RubroAdicional, \
    Descuento, DetalleDescuento, InscripcionSeminario,ReciboPermisoCondu, ReferidosInscripcion,PagoWester,RegistroWester, FormaDePago, RegistroExterno, MensajesEnviado, \
    PagoExternoPedagogia, Grupo, PromoGym, DescuentoSeguimiento,RubroSeguimiento, Coordinacion, DirferidoRubro, SolicitudEstudiante, SolicitudOnline, RubroLog, \
    DatosTransfereciaDeposito, ModuloGrupo, SolicitudesGrupo,InscripcionMotivoCambioPromocion,Promocion, SolicitudSecretariaDocente, \
    CuotaCAB,DescuentoDOBE, DetalleRubrosBeca, ReciboPago
from sga.printdoc import imprimir_contenido
from sga.reportes import elimina_tildes
from sga.tasks import send_html_mail


class EspecieSerieGenerador:
    def __init__(self):
        self.__lock = threading.RLock()

    def generar_especie(self, rubro, tipo):
        self.__lock.acquire()
        try:
            serie = 0
            valor = RubroEspecieValorada.objects.filter(rubro__fecha__year=rubro.fecha.year).aggregate(Max('serie'))
            if valor['serie__max']!=None:
                serie = valor['serie__max']+1

                # OCU 09-junio-2017 para evitar que la serie de la especie se duplique
            if not RubroEspecieValorada.objects.filter(rubro__fecha__year=rubro.fecha.year,serie=serie).exists():

                rubroe = RubroEspecieValorada(rubro=rubro, tipoespecie=tipo, serie=serie)
                if tipo.id == ESPECIE_CAMBIO_PROGRAMACION:
                    rubroe.autorizado = False
                rubroe.save()

                return rubroe
            else:
                rubro.delete()
        finally:
            self.__lock.release()


generador_especies = EspecieSerieGenerador()

def convertir_fecha(s):
    return datetime.datetime(int(s[6:10]), int(s[3:5]), int(s[0:2])).date()


def representacion_factura_str(x):
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

def fix_formadepago_str(x):
    pago = Pago.objects.get(pk=x.id)
    return pago.nombre()

def fix_pago_str(x):
    pago = Pago.objects.get(pk=x.id)
    if pago.es_retencion():
        fp = 1
    else :
        fp = 0
    obj = model_to_dict(pago, exclude=['fecha', 'lugar', 'recibe','efectivo','id'])
    rubro = Rubro.objects.get(pk=obj['rubro'])
    obj['rubro'] = model_to_dict(rubro, exclude=['fecha','fechavence', 'cancelado','inscripcion','fichamedica','valor'])
    obj['rubro'].update({'nombre': rubro.nombre(), 'tipo': rubro.tipo(), 'alumno': rubro.inscripcion.persona.nombre_completo() if rubro.inscripcion else str(rubro.fichamedica),'fp':fp,'id':rubro.id})

    return obj

@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
@transaction.atomic()
def view(request):
    start_time = datetime.datetime.now().time()
    # profile_dir = CP_PROFILE_DIR
    # output_file = os.path.join(profile_dir, 'output.pstats')
    # import cProfile
    # Inicia el perfilador
    # profiler = cProfile.Profile()
    # profiler.enable()
    if request.method=='POST':
        action = request.POST['action']
        if action=='addmatricula':
            try:
                matricula = Matricula.objects.get(pk=request.POST['mid'])
                inscripcion = Inscripcion.objects.get(pk=request.POST['id'])
                a = request.POST['fe']
                rubro = Rubro(fecha=datetime.datetime.now(), valor=float(request.POST['valor']),
                                inscripcion=inscripcion, cancelado=False, fechavence=datetime.datetime(int(a[6:10]), int(a[3:5]), int(a[0:2])))
                rubro.save()
                rubromatricula = RubroMatricula(rubro=rubro, matricula=matricula)
                rubromatricula.save()
                if HABILITA_DESC_MATRI:
                    if not inscripcion.carrera.validacionprofesional:
                        descuento = round(((rubro.valor * DESCUENTO_MATRIC_PORCENT) /100),2)
                        rubro.valor = rubro.valor - round(((rubro.valor * DESCUENTO_MATRIC_PORCENT) /100),2)
                        rubro.save()
                        desc = Descuento(inscripcion = inscripcion,
                                                  motivo ='DESCUENTO EN MATRICULA',
                                                  total = rubro.valor,
                                                  fecha = datetime.datetime.now())
                        desc.save()
                        detalle = DetalleDescuento(descuento =desc,
                                                    rubro =rubro,
                                                    valor = descuento,
                                                    porcentaje = DESCUENTO_MATRIC_PORCENT)
                        detalle.save()

                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de ADICIONAR RUBRO MATRICULA
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(rubromatricula).pk,
                    object_id       = rubromatricula.id,
                    object_repr     = force_str(rubromatricula),
                    action_flag     = ADDITION,
                    change_message  = 'Adicionado Rubro Matricula -'+ str(inscripcion) + ' (' + client_address + ')' )

                return HttpResponse(json.dumps({'result':'ok'}),content_type="application/json")
            except :
                return HttpResponse(json.dumps({'result':'bad'}),content_type="application/json")



        elif action=='liquidar':
            rubro = Rubro.objects.get(pk=request.POST['id'])
            f = LiquidaRubroForm(request.POST)
            if f.is_valid():
                rubro.valor = rubro.total_pagado()
                rubro.cancelado = True
                rubro.save()

                logr = RubroLog(rubro=rubro,motivo='Liquidado: ' + f.cleaned_data['motivo'],
                                    autoriza= f.cleaned_data['autoriza'],
                                    fecha=datetime.datetime.now(),
                                    usuario=request.user)
                logr.save()

                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(rubro).pk,
                    object_id       = rubro.id,
                    object_repr     = force_str(rubro),
                    action_flag     = CHANGE,
                    change_message  = 'Rubro Liquidado - ' +str(rubro.inscripcion) + ' ('  + client_address + ')')

                return HttpResponseRedirect("/finanzas?action=rubros&id="+str(rubro.inscripcion.id))
            else:
                return HttpResponseRedirect("/finanzas?action=liquida&id="+str(rubro.id))
        elif action=='ccnc':
            nc = NotaCreditoInstitucion.objects.get(pk=request.POST['nc'])
            valor = float(request.POST['valor'])
            if nc.saldo>=valor:
            # if nc.valor>=valor:
                return HttpResponse(json.dumps({'result':'ok'}),content_type="application/json")
            else:
                return HttpResponse(json.dumps({'result':'bad'}),content_type="application/json")
        elif action=='consultawes':
            pw = PagoWester.objects.get(pk=request.POST['id'])
            if pw.datos:
                return HttpResponse(json.dumps({'result':'ok','cedula':str(pw.identificacion),'nombre':str(pw.nombre),
                                                'direccion':str(pw.direccion),'telefono':str(pw.telefono),'email':str(pw.email)}),content_type="application/json")
            else:
                return HttpResponse(json.dumps({'result':'bad'}),content_type="application/json")


        elif action=='ccrecibo':
            rc = ReciboCajaInstitucion.objects.get(pk=request.POST['rc'])
            valor = float(request.POST['valor'])
            if rc.saldo>=valor:
                return HttpResponse(json.dumps({'result':'ok'}),content_type="application/json")
            else:
                return HttpResponse(json.dumps({'result':'bad'}),content_type="application/json")
        elif action == 'descontar':
            try:
                datos = json.loads(request.POST['datos'])
                descuento = Descuento(inscripcion_id = int(datos['inscripcion']),
                                      motivo = datos['motivo'],
                                      total = Decimal(datos['total']),
                                      fecha= datetime.datetime.now())
                descuento.save()

                for d in datos['detalle']:
                    detalle = DetalleDescuento(descuento=descuento,
                                               rubro_id= int(d['rubro']),
                                               valor =Decimal(d['valor']),
                                               porcentaje = Decimal(d['porc']))
                    detalle.save()
                    rubro = Rubro.objects.get(pk=int(d['rubro']))
                    rubro.valor= Decimal(rubro.valor) - Decimal(d['valor'])
                    rubro.save()

                client_address = ip_client_address(request)

                    # Log de CREACION AUTOMATICA DE RECIBO DE CAJA POR EXCEDENTE
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(descuento).pk,
                    object_id       = descuento.id,
                    object_repr     = force_str(descuento),
                    action_flag     = ADDITION,
                    change_message  = 'Generado Descuento (' + client_address + ')')

                if  EMAIL_ACTIVE:
                    descuento.correo(request.user.username)


                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            except Exception as ex:

                return HttpResponse(json.dumps({"result":"bad",'mensaje':str(ex)}),content_type="application/json")


        elif action =='consuvalor':
                tienepago=0
                if Rubro.objects.filter(pk=request.POST['rubro']).exists():
                    rubro = Rubro.objects.get(pk=request.POST['rubro'])
                    if Pago.objects.filter(rubro=rubro).exists():
                        tienepago=1;
                    return HttpResponse(json.dumps({"result":"ok","valor":str(rubro.valor),"tienepago":tienepago}),content_type="application/json")
                else:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

        elif action =='consurubro':
                if Rubro.objects.filter(pk=request.POST['rubro']).exists():
                    rubro = Rubro.objects.get(pk=request.POST['rubro'])
                    if rubro.pago_set.exists():
                        return HttpResponse(json.dumps({"result":"bad2"}),content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({"result":"ok","valor":str(rubro.valor)}),content_type="application/json")
                else:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

        elif action=='cnch':
            banco = Banco.objects.get(pk=request.POST['banco'])
            if PagoCheque.objects.filter(numero=request.POST['numero'], banco=banco, emite=request.POST['emite']).exists():
                return HttpResponse(json.dumps({'result':'bad'}),content_type="application/json")
            else:
                return HttpResponse(json.dumps({'result':'ok'}),content_type="application/json")

        elif action == 'fechawester':
            try:
                pagowester = PagoWester.objects.filter(id=request.POST['id'])[:1].get()
                pagowester.fechapago = convertir_fecha(request.POST['fecha'])
                pagowester.save()
                #Obtain client ip address
                client_address = ip_client_address(request)


                # Log de CREACION AUTOMATICA DE RECIBO DE CAJA POR EXCEDENTE
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(pagowester).pk,
                    object_id       = pagowester.id,
                    object_repr     = force_str(pagowester),
                    action_flag     = ADDITION,
                    change_message  = 'Agregada Fecha Pago Wester '+ str(pagowester.fechapago) + ' (' + client_address + ')')
                return HttpResponse(json.dumps({'result':'ok'}),content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({'result':'bad','error': e}),content_type="application/json")

        elif action=='cntr':
            ref=request.POST['numero'].upper()
            ref=(ref.replace(' ', ''))
            #OC 11-07-2018 para eliminar los espacios en blanco
            # if PagoTransferenciaDeposito.objects.filter(referencia=request.POST['numero'].upper()).exists():
            ctbanco=CuentaBanco.objects.filter(pk=request.POST['ctabanco'])[:1].get()
            if PagoTransferenciaDeposito.objects.filter(referencia=ref,cuentabanco=ctbanco).exists():
                return HttpResponse(json.dumps({'result':'bad'}),content_type="application/json")
            else:
                if  DatosTransfereciaDeposito.objects.filter(referencia=ref,cuentabanco=ctbanco,disponible=False).exists():
                    return HttpResponse(json.dumps({'result':'bad'}),content_type="application/json")
                else:
                    return HttpResponse(json.dumps({'result':'ok'}),content_type="application/json")
        elif action=='recargo':
            rubro = Rubro.objects.get(pk=request.POST['id'])
            inscripcion = rubro.inscripcion
            f = RubroForm(request.POST)
            if f.is_valid():
                tipootro = TipoOtroRubro.objects.get(pk=TIPO_MORA_RUBRO)
                descripcion = 'RECARGO: ' + rubro.nombre()
                rubro2 = Rubro(fecha=datetime.datetime.now(), valor=f.cleaned_data['valor'],
                              inscripcion=inscripcion, cancelado=False, fechavence=rubro.fechavence)
                rubro2.save()
                rubrootro = RubroOtro(rubro=rubro2, tipo=tipootro, descripcion=descripcion)
                rubrootro.save()
                return HttpResponseRedirect("/finanzas?action=rubros&id="+str(inscripcion.id))
            else:
                return HttpResponseRedirect("/finanzas?action=recargo&id="+str(inscripcion.id))

        elif action =='consultadatos':
            try:
                datos = DatosTransfereciaDeposito.objects.filter(pk=request.POST['id'])[:1].get()
                return HttpResponse(json.dumps({"result":"ok",'referencia':str(datos.referencia), 'cta': str(datos.cuentabanco.id) ,'valor' : str(datos.valor)}),content_type="application/json")
            except Exception as ex:
                return HttpResponse(json.dumps({"result":"bad",'mensaje':str(ex)}),content_type="application/json")
        elif action=='pagaryfacturar':
            var = ""
            sid = transaction.savepoint()
            try:
                data = json.loads(request.POST['data'])
                pagos = data['pagos']
                fechasol= None
                if 'solicitud' in request.POST:
                    solicitud = SolicitudSecretariaDocente.objects.filter(id=request.POST['solicitud'])[:1].get()
                    data['solicitud']  = solicitud
                    fechasol= solicitud.datosaprobacion().fechadeposito
                else:
                    if 'fechawester' in request.POST:
                        print(request.POST['fechawester'])
                        fechasol = convertir_fecha(request.POST['fechawester'])
                        print(fechasol)
                    else:
                        if 'pagowestercaja' in request.POST:
                            print(request.POST['pagowestercaja'])
                            fechasol = convertir_fecha(request.POST['pagowestercaja'])
                            print(fechasol)
                        else:
                            fechasol= None
                idrubro = []
                for pagrubdet in pagos:
                    for pagrub in pagrubdet['pagos']:
                        rubrocons = Rubro.objects.get(id=pagrub['rubro']['id'])
                        if rubrocons.total_pagado() > rubrocons.valor:
                            return HttpResponse(json.dumps({'result':'bad', "error": "No se puede realizar el pago, la suma de los pagos del rubro "+ rubrocons.nombre() +" supera el valor a pagar."}),content_type="application/json")
                        elif float(pagrub['valor']) < 0:
                            return HttpResponse(json.dumps({'result':'bad', "error": "No se puede realizar el pago, el rubro "+ rubrocons.nombre() +" esta en negativo, revisar las finanzas"}),content_type="application/json")
                        if not pagrub['rubro']['id'] in idrubro:
                            if rubrocons.aplicadescuento(fechasol)[1]:
                                idrubro.append(pagrub['rubro']['id'])
                caja = request.session['persona'].lugarrecaudacion_set.filter(activa=True)[:1].get()
                lugar = LugarRecaudacion.objects.filter(persona=request.session['persona'],activa=True)[:1].get()
                sesion_caja = caja.sesion_caja()

                inscripcion = None

                for pago in pagos:
                    pagosdesglosados = pago['pagos']
                    for pagorubro in pagosdesglosados:
                        rubro = Rubro.objects.get(pk=pagorubro['rubro']['id'])
                        if RubroReceta.objects.filter(rubrootro__rubro = rubro).exists():
                            receta = RubroReceta.objects.filter(rubrootro__rubro = rubro)[:1].get()
                            for r in RecetaVisitaBox.objects.filter(visita=receta.detallebox):
                                if r.detalle:
                                    if r.detalle.stock <= 0:
                                        return HttpResponse(json.dumps({'result':'bad', "error": "stock no disponible para para la receta."}),content_type="application/json")

                                elif r.traslado:
                                    if r.traslado.stock <= 0:
                                        return HttpResponse(json.dumps({'result':'bad', "error": "stock no disponible para la receta."}),content_type="application/json")

                # Factura
                notadebito = data['notadebito']

                if FACTURACION_ELECTRONICA:
                    recepcion = ''
                    dirfactur=''
                    mensajerecep=''
                else:
                    recepcion=None
                    dirfactur=None
                    mensajerecep=None
                factnumero=0
                if not notadebito:
                    if Factura.objects.filter(numero=caja.puntoventa+"-"+str(data['factura']['numero']).zfill(9)).exists():
                        return HttpResponse(json.dumps({'result':'badexist', "error": "Numero de Factura ya existe."}),content_type="application/json")
                    try:
                        if ClienteFactura.objects.filter(ruc=data['factura']['ruc']).exists():
                            cliente = ClienteFactura.objects.filter(ruc=data['factura']['ruc'])[:1].get()
                            cliente.nombre = elimina_tildes(data['factura']['nombre'])
                            cliente.direccion = elimina_tildes(data['factura']['direccion'])
                            cliente.telefono = elimina_tildes(data['factura']['telefono'])
                            cliente.correo = data['factura']['correo']
                            if cliente.contrasena == None:
                                cliente.contrasena = data['factura']['ruc']
                                cliente.numcambio = 0
                            cliente.save()
                            if Persona.objects.filter( Q(cedula= data['factura']['ruc'])| Q(pasaporte=data['factura']['ruc'])).exists():# Actualiza la direccion en la tabla persona
                                pr = Persona.objects.filter( Q(cedula= data['factura']['ruc'])| Q(pasaporte=data['factura']['ruc']))[:1].get()
                                pr.direccion= elimina_tildes(data['factura']['direccion'])
                                pr.save()
                        else:
                            cliente = ClienteFactura(ruc=data['factura']['ruc'], nombre=elimina_tildes(data['factura']['nombre']),
                                direccion=elimina_tildes(data['factura']['direccion']), telefono=elimina_tildes(data['factura']['telefono']),
                                correo=data['factura']['correo'],contrasena=data['factura']['ruc'],numcambio=0)
                            cliente.save()
                    except :
                        cliente = ClienteFactura(ruc=data['factura']['ruc'], nombre=elimina_tildes(data['factura']['nombre']),
                            direccion=elimina_tildes(data['factura']['direccion']), telefono=elimina_tildes(data['factura']['telefono']),
                            correo=data['factura']['correo'],contrasena=data['factura']['ruc'],numcambio=0)
                        cliente.save()

                    # Chequear numero de factura

                    if FACTURACION_ELECTRONICA:
                        if lugar.numerofact == None:
                            lugar.numerofact = data['factura']['numero']
                            lugar.save()
                        factnumero = lugar.numerofact
                    else:
                        factnumero = int(data['factura']['numero'])

                    factura = Factura(numero = caja.puntoventa.strip()+"-"+str(factnumero).zfill(9), fecha = datetime.datetime.today().date(),
                                    valida = True, cliente = cliente,
                                    subtotal = 0, iva = 0, total = 0, hora=datetime.datetime.today().time(),
                                    impresa=False, caja=caja, estado = recepcion, mensaje = mensajerecep,dirfactura=dirfactur)

                    if MODELO_IMPRESION_NUEVO:
                        factura.impresa = True

                    factura.save()

                    total_factura = 0

                enviar_mensaje=False
                seguimiento =False
                ultimaFormaPago = None
                for pago in pagos:
                    tp = None
                    if pago['formadepago']==FORMA_PAGO_EFECTIVO or pago['formadepago']==FORMA_PAGO_ELECTRONICO or  pago['formadepago']==FORMA_PAGO_WESTER :
                        pass
                    elif pago['formadepago']==FORMA_PAGO_CHEQUE:
                        hoy = datetime.datetime.today().date()
                        f_cobro =convertir_fecha(pago['fechacobro'])

                        tp = PagoCheque(numero=pago['numero'],banco=Banco.objects.get(pk=pago['bancocheque']),
                                        fecha=datetime.datetime.today().date(),
                                        fechacobro=convertir_fecha(pago['fechacobro']),
                                        emite=pago['emite'], valor=float(pago['valor']), protestado=False)
                        tp.save()

                        if f_cobro!= hoy:
                             tp.recibido=False
                        else:
                             tp.recibido=True
                        tp.save()

                    elif pago['formadepago']==FORMA_PAGO_DEPOSITO:
                        tp = PagoTransferenciaDeposito(referencia=pago['referencia'],
                                        fecha=datetime.datetime.today().date(),
                                        cuentabanco=CuentaBanco.objects.get(pk=pago['cuentabanco']),
                                        valor=float(pago['valor']),
                                        deposito=True)
                        tp.save()
                        if 'solicitudep' in pago:
                            if pago['solicitudep'] != '':
                                if  DatosTransfereciaDeposito.objects.filter(pk=pago['solicitudep'] ).exists():
                                    solicitudtr = DatosTransfereciaDeposito.objects.filter(pk=pago['solicitudep'])[:1].get()
                                    solicitudtr.disponible = False
                                    solicitudtr.pago = tp
                                    solicitudtr.save()
                                    solicitud = solicitudtr.solicitud
                                    solicitud.observacion = 'SOLICITUD APROBADA'
                                    solicitud.resolucion = 'SU PAGO HA SIDO PROCESADO'
                                    solicitud.fechacierre = datetime.datetime.now()
                                    solicitud.hora = datetime.datetime.now().time()
                                    solicitud.usuario = request.user
                                    solicitud.cerrada = True
                                    solicitud.save()
                                    solicitudsecretariamail(solicitudtr.solicitud,request)
                    elif pago['formadepago']==FORMA_PAGO_TRANSFERENCIA:
                        tp = PagoTransferenciaDeposito(referencia=pago['referencia'],
                            fecha=datetime.datetime.today().date(),
                            cuentabanco=CuentaBanco.objects.get(pk=pago['cuentabanco']),
                            valor=float(pago['valor']),
                            deposito=False)
                        tp.save()
                        if 'solicitudtr' in pago:
                            if pago['solicitudtr'] != '':
                                if  DatosTransfereciaDeposito.objects.filter(pk=pago['solicitudtr'] ).exists():
                                    solicitudtr = DatosTransfereciaDeposito.objects.filter(pk=pago['solicitudtr'])[:1].get()
                                    solicitudtr.disponible = False
                                    solicitudtr.pago = tp
                                    solicitudtr.save()
                                    solicitud = solicitudtr.solicitud
                                    solicitud.observacion = 'SOLICITUD APROBADA'
                                    solicitud.resolucion = 'SU PAGO HA SIDO PROCESADO'
                                    solicitud.fechacierre = datetime.datetime.now()
                                    solicitud.hora = datetime.datetime.now().time()
                                    solicitud.usuario = request.user
                                    solicitud.cerrada = True
                                    solicitud.save()
                                    solicitudsecretariamail(solicitudtr.solicitud,request)

                    elif pago['formadepago']==FORMA_PAGO_TARJETA or pago['formadepago']==FORMA_PAGO_TARJETA_DEB:
                        if pago['formadepago']==FORMA_PAGO_TARJETA:
                            tarjetadebito = False

                        else:
                            tarjetadebito = True
                        tp = PagoTarjeta(banco=Banco.objects.get(pk=pago['bancotarjeta']),
                                tipo=TipoTarjetaBanco.objects.get(pk=pago['tipotarjeta']),
                                poseedor=pago['poseedor'],
                                valor = float(pago['valor']),
                                procesadorpago=ProcesadorPagoTarjeta.objects.get(pk=pago['procesadorpago']),
                                referencia=pago['referencia'],
                                tarjetadebito=tarjetadebito,
                                fecha=datetime.datetime.today().date(),
                                lote=pago['lote'],adquiriente=pago['adquiriente'],autorizacion=pago['autorizacion'])
                        tp.save()

                    elif pago['formadepago']==FORMA_PAGO_RETENCION:
                        tp = PagoRetencion(autorizacion=pago['autorizacion'],
                                numerot = pago['numerot'],
                                tiporetencion=TipoRetencion.objects.get(pk=pago['tiporetencion']),
                                valor = float(pago['valor']),
                                fecha=datetime.datetime.today().date())
                        tp.save()

                    elif pago['formadepago']==FORMA_PAGO_NOTA_CREDITO:
                        tp = PagoNotaCreditoInstitucion(notacredito=NotaCreditoInstitucion.objects.get(pk=pago['notacredito']),
                                                       valor = float(pago['valor']),
                                                       fecha = datetime.datetime.today().date())
                        tp.save()
                        ncp = tp.notacredito
                        # # ncp.valor = round(ncp.valor - float(pago['valor']),2)
                        # # if ncp.valor <= 0:
                        # ncp.cancelada = True
                        # ncp.save()
                        ncp.saldo = ncp.saldo - tp.valor
                        # ncp.valor = round(ncp.valor - float(pago['valor']),2)
                        if ncp.saldo == 0:
                            ncp.cancelada = True
                        ncp.save()

                    elif pago['formadepago']==FORMA_PAGO_RECIBOCAJAINSTITUCION:
                        tp = PagoReciboCajaInstitucion(recibocaja=ReciboCajaInstitucion.objects.get(pk=pago['recibocaja']),
                                                    valor = float(pago['valor']),
                                                    fecha = datetime.datetime.today().date())
                        tp.save()
                        rc = tp.recibocaja
                        rc.saldo = round(rc.saldo - float(pago['valor']),2)
                        rc.save()

                    pagosdesglosados = pago['pagos']

                    promogim = 0
                    for pagorubro in pagosdesglosados:
                        rubro = Rubro.objects.get(pk=pagorubro['rubro']['id'])
                        if rubro.tipo() != 'ESPECIE':
                            enviar_mensaje=True
                        if inscripcion==None:
                            inscripcion = rubro.inscripcion
                        electronico=False
                        wester = False
                        efectivo=False
                        if tp==None:
                            if  pago['formadepago']==FORMA_PAGO_ELECTRONICO:
                                electronico=True
                            elif  pago['formadepago']==FORMA_PAGO_WESTER:
                                wester=True
                            else:
                                efectivo = True


                        # ///////////////////////////////////////////////////
                        # //////////////////////////////////////////////////
                        pago2 = Pago(fecha=datetime.datetime.today().date(),
                                    recibe=request.session['persona'],
                                    valor=float(pagorubro['valor']),
                                    rubro=rubro,
                                    efectivo=efectivo,
                                    wester=wester,
                                    sesion=sesion_caja,
                                    electronico=electronico)
                        pago2.save()

                        if pago2.wester :
                            if request.POST['ban'] == 'NORMAL':
                                if PagoWester.objects.filter(pk=pago['wester']).exists():
                                    pwester = PagoWester.objects.filter(pk=pago['wester'])[:1].get()
                                    pwester.factura = factura
                                    pago2.secuenciapago = pwester.codigo
                                    pwester.save()
                            else:
                                for r in RegistroWester.objects.filter(codigo=str(pago['wester']).lstrip()):
                                    r.facturado=True
                                    r.pago=pago2
                                    r.save()

                            # if RegistroWester.objects.filter(pk=pago['wester'],)


                        if not notadebito:
                            total_factura = round(total_factura+float(pagorubro['valor']),2)

                        pago2.save()


                        if rubro.aplicadescuento(fechasol)[1]:
                                valortotpaga = float(0)
                                for pagrubdet in pagos:
                                    for pagrub in pagrubdet['pagos']:
                                        if rubro == Rubro.objects.get(pk=pagrub['rubro']['id']):
                                            valortotpaga = valortotpaga + float(pagrub['valor'])
                                valor, aplicanivcut, valdescuento, porcentajedescuento = rubro.calculadescuento(idrubro,fechasol)
                                descripdeta = 'PROMOCION ' + str(porcentajedescuento) + ' DESCUENTO POR PAGO DE CUOTAS'
                                sumar = Pago.objects.filter(rubro=rubro).exclude(id=pago2.id).aggregate(
                                    Sum('valor'))
                                pagadoval = sumar['valor__sum'] if sumar['valor__sum'] else 0
                                if round(float(valortotpaga), 2) >= round(float(rubro.valor - valdescuento - pagadoval), 2) and valdescuento>0:
                                    desc = Descuento(inscripcion = inscripcion,
                                                              motivo =descripdeta,
                                                              total = valdescuento,
                                                              fecha = datetime.datetime.now().date())
                                    desc.save()
                                    detalle = DetalleDescuento(descuento =desc,
                                                                rubro =rubro,
                                                                valor = valdescuento,
                                                                porcentaje = porcentajedescuento,
                                                                pago=pago2)
                                    detalle.save()

                                    rubro.valor = (rubro.valor - valdescuento)
                                    rubro.save()

                        if RubroSeguimiento.objects.filter(rubro=rubro, estado=True).exists():
                            seguimiento = True
                        if rubro.adeudado()==0:
                            if not rubro.vencido():
                                if rubro.es_cuota() or rubro.es_matricula():
                                    promogim = 1
                            if RubroSeguimiento.objects.filter(rubro=rubro, estado=True).exists():
                                rubroseg = RubroSeguimiento.objects.filter(rubro=rubro, estado=True)[:1].get()
                                rubroseg.fechapago = datetime.datetime.now().date()
                                rubroseg.save()
                                seguimiento = True
                            rubro.cancelado = True
                            rubro.save()
                            #OCastillo 11-04-2022 despues de pagar la especie sumar dias de vigencia
                            if rubro.tipo() == 'ESPECIE'and rubro.especie_valorada().vencida() < DIAS_ESPECIE :
                                rubro.fechavence = rubro.fecha + timedelta(DIAS_ESPECIE)
                                rubro.save()
                            if rubro.tipo() == 'ESPECIE' and not VALIDA_DEUDA_EXAM_ASIST:
                                if RubroEspecieValorada.objects.filter(rubro=rubro,tipoespecie__id=ID_TIPO_ESPECIE_REG_NOTA,disponible=False).exists():
                                    rubroespecie = RubroEspecieValorada.objects.filter(rubro=rubro,tipoespecie__id=ID_TIPO_ESPECIE_REG_NOTA,disponible=False)[:1].get()
                                    rubroespecie.disponible = True
                                    rubroespecie.fecha = datetime.datetime.today()
                                    rubroespecie.save()
                            #OCastillo 10-06-2022 si la especie esta vencida actualizar fecha para que se presente activa
                            if rubro.tipo() == 'ESPECIE' and rubro.especie_valorada().vencida() > DIAS_ESPECIE :
                                rubro.fecha =datetime.datetime.now().date()
                                rubro.fechavence = rubro.fecha + timedelta(DIAS_ESPECIE)
                                rubro.save()
                                if RubroEspecieValorada.objects.filter(rubro=rubro).exists():
                                    rubroespecie = RubroEspecieValorada.objects.filter(rubro=rubro)[:1].get()
                                    rubroespecie.fechaasigna = datetime.datetime.today()
                                    rubroespecie.save()
                            try:
                                if PagoExternoPedagogia.objects.filter(rubro=rubro).exists():
                                    datos = requests.post('http://api.pedagogia.edu.ec',{'action': 'add',"pagado":"0", 'codigo':elimina_tildes(rubro.inscripcion.grupo().nombre), "ci": str(rubro.inscripcion.persona.cedula) })
                            except:
                                pass
                            if RubroReceta.objects.filter(rubrootro__rubro = rubro).exists():
                                receta = RubroReceta.objects.filter(rubrootro__rubro = rubro)[:1].get()
                                for r in RecetaVisitaBox.objects.filter(visita=receta.detallebox):
                                    # if r.factura:
                                    r.registro.cantidad = r.registro.cantidad - r.cantidad
                                    if r.detalle:
                                        r.detalle.stock = r.detalle.stock - r.cantidad
                                        r.detalle.save()
                                    elif r.traslado:
                                        r.traslado.stock = r.traslado.stock - r.cantidad
                                        r.traslado.save()
                                    r.registro.save()

                            if DetalleRubrosBeca.objects.filter(rubro=rubro).exists():
                                detRubroBeca = DetalleRubrosBeca.objects.filter(rubro=rubro)[:1].get()
                                detRubroBeca.pago = pago2
                                detRubroBeca.save()

                        if tp!=None:
                            tp.pagos.add(pago2)

                        if not notadebito:
                            factura.pagos.add(pago2)

                        # Agregar $1 como beneficio a la caja de ahorro por pago puntual
                        if rubro.cancelado and CuotaCAB.objects.filter(rubro=rubro) and pago2.rubro.fechavence>=pago2.fecha:
                            cuota_cab = CuotaCAB.objects.filter(rubro=rubro)[:1].get()
                            cuota_cab.valor_benef = 1
                            cuota_cab.fecha_benef = datetime.datetime.now().date()
                            cuota_cab.save()

                    #Establecer los valores de la factura Total y SubTotal
                    if not notadebito:
                        if FACTURACION_CON_IVA:
                            factura.total = total_factura
                            factura.subtotal = round(factura.total / COEFICIENTE_CALCULO_BASE_IMPONIBLE, 2)
                            factura.iva = round(factura.total - factura.subtotal, 2)
                        else:
                            factura.subtotal = total_factura
                            factura.total = total_factura
                        factura.save()
                        if PROMOCION_GYM:
                            if promogim:
                                inicio = datetime.datetime.now().date()
                                fin = datetime.datetime.now().date() + datetime.timedelta(30)
                                promo = PromoGym(inscripcion=inscripcion,
                                                 inicio=inicio,
                                                 fin=fin,
                                                 factura=factura)
                                promo.save()

                    ultimaFormaPago = FormaDePago.objects.get(pk=pago['formadepago'])

                #OCastillo 27-nov-2019 si hay mas de 6 pagos de especies de registro de notas de la misma materia enviar correo a coordinacion
                if DEFAULT_PASSWORD=='itb':
                    hoy=datetime.datetime.today()
                    if RubroEspecieValorada.objects.filter(tipoespecie__id=ID_TIPO_ESPECIE_REG_NOTA,rubro__cancelado=True,fecha=hoy).exists():
                        especieasentamiento=RubroEspecieValorada.objects.filter(tipoespecie__id=ID_TIPO_ESPECIE_REG_NOTA,rubro__cancelado=True,fecha=hoy)[:1].get()
                        asentamiento=RubroEspecieValorada.objects.filter(tipoespecie__id=ID_TIPO_ESPECIE_REG_NOTA,rubro__cancelado=True,fecha=hoy).order_by('materia__materia__id').distinct('materia__materia__id').values('materia__materia__id')
                        for mat in asentamiento:
                             total= RubroEspecieValorada.objects.filter(tipoespecie__id=ID_TIPO_ESPECIE_REG_NOTA,rubro__cancelado=True,fecha=hoy,materia__materia__id=mat['materia__materia__id']).count()
                             if total == 6:
                                 if  EMAIL_ACTIVE:
                                     carrera=especieasentamiento.materia.matricula.inscripcion.carrera
                                     grupo=especieasentamiento.materia.matricula.nivel.grupo.nombre
                                     nivel=especieasentamiento.materia.matricula.nivel.nivelmalla.nombre
                                     coord= Coordinacion.objects.filter(carrera=carrera)[:1].get()
                                     email_coordinacion=coord.correo
                                     especieasentamiento.correoasentamientonotas(carrera,grupo,nivel,email_coordinacion)

                # Si hay excedente entonces adicionar un Recibo de Caja Institucional
                if float(data['excedente'])>0 and inscripcion!=None:

                    rc = ReciboCajaInstitucion(inscripcion=inscripcion,
                                               motivo='PAGO ANTICIPADO DE CUOTAS',
                                               sesioncaja=sesion_caja,
                                               fecha=datetime.datetime.today().date(),
                                               hora=datetime.datetime.now().time(),
                                               valorinicial = float(data['excedente']),
                                               saldo=float(data['excedente']),
                                               formapago=ultimaFormaPago)
                    rc.save()
                    recibopago = ReciboPago(pago=pago2, recibocaja=rc)
                    recibopago.save()

                    #Obtain client ip address
                    client_address = ip_client_address(request)


                    # Log de CREACION AUTOMATICA DE RECIBO DE CAJA POR EXCEDENTE
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(rc).pk,
                        object_id       = rc.id,
                        object_repr     = force_str(rc),
                        action_flag     = ADDITION,
                        change_message  = 'Generado Recibo Caja Automatico por excedente (' + client_address + ')')

                # Incrementar el numero de Factura
                if not notadebito:
                    sesion_caja.facturatermina = int(factnumero)+1
                    sesion_caja.save()
                    if FACTURACION_ELECTRONICA or lugar.numerofact  != None:
                        for luga in LugarRecaudacion.objects.all():
                            if luga.puntoventa == lugar.puntoventa:
                                luga.numerofact = int(factnumero)+1
                                luga.save()

                #Para imprimir a traves de un modelo (plantillas html) pero con el programa java
                if MODELO_IMPRESION_NUEVO:
                    imprimir_contenido(request.user, 'factura', factura.id)

                #Para imprimir directo convirtiendo antes en un pdf usando libreria FPDF
                if UTILIZA_FACTURACION_CON_FPDF:
                    if not notadebito:
                        invoice = representacion_factura_str(factura)
                        fecha = invoice['fecha']
                        dia = fecha[:2]
                        mes = fecha[3:5]
                        anno = fecha[-4:]
                        pdf = FPDF()
                        pdf.add_page(orientation=POSICIONES_IMPRESION['orientacion'])
                        pdf.set_font(POSICIONES_IMPRESION['fuente'][0],'',POSICIONES_IMPRESION['fuente'][1])
                        #Datos de Numero y Fecha de Factura
                        pdf.text(POSICIONES_IMPRESION['numerofactura'][0],POSICIONES_IMPRESION['numerofactura'][1],invoice['numero'])
                        pdf.text(POSICIONES_IMPRESION['dia'][0],POSICIONES_IMPRESION['dia'][1],dia)
                        pdf.text(POSICIONES_IMPRESION['mes'][0],POSICIONES_IMPRESION['mes'][1],mes)
                        pdf.text(POSICIONES_IMPRESION['anno'][0],POSICIONES_IMPRESION['anno'][1],anno)
                        #Datos del Cliente de Factura
                        pdf.text(POSICIONES_IMPRESION['nombrecliente'][0],POSICIONES_IMPRESION['nombrecliente'][1],invoice['cliente']['nombre'])
                        pdf.text(POSICIONES_IMPRESION['ruccliente'][0],POSICIONES_IMPRESION['ruccliente'][1],invoice['cliente']['ruc'])

                        pdf.text(POSICIONES_IMPRESION['telefonocliente'][0],POSICIONES_IMPRESION['telefonocliente'][1],invoice['cliente']['telefono'])
                        if len(invoice['cliente']['direccion']) < 40:
                            pdf.text(POSICIONES_IMPRESION['direccioncliente'][0],POSICIONES_IMPRESION['direccioncliente'][1],invoice['cliente']['direccion'])
                        else:
                            pdf.text(POSICIONES_IMPRESION['direccioncliente'][2],POSICIONES_IMPRESION['direccioncliente'][3],invoice['cliente']['direccion'][1:41] + '-')
                            pdf.text(POSICIONES_IMPRESION['direccioncliente'][4],POSICIONES_IMPRESION['direccioncliente'][5],invoice['cliente']['direccion'][41:])

                        #Rubros
                        i = 0
                        # locale.setlocale( locale.LC_ALL, '' )
                        locale.setlocale( locale.LC_ALL, 'en_US.UTF-8' )
                        if MODELO_EVALUACION == EVALUACION_CASADE:
                            for pagos in invoice['pagos']:
                                p= 0
                                if pagos['rubro']['fp'] == 1:
                                    p = pagos['valor']
                            for pagos in invoice['pagos']:

                                if pagos['rubro']['fp'] == 0:
                                    pagos['valor'] = pagos['valor'] + p
                                    p=0
                                    pdf.text(POSICIONES_IMPRESION['rubroalumno'][0],POSICIONES_IMPRESION['rubroalumno'][1],pagos['rubro']['alumno'])
                                    pdf.text(POSICIONES_IMPRESION['rubrotipo'][0],POSICIONES_IMPRESION['rubrotipo'][1] + (i * 7),str(i+1)  + pagos['rubro']['nombre'])
                                    if FACTURACION_CON_IVA:
                                        pdf.text(POSICIONES_IMPRESION['rubrovalor'][0],POSICIONES_IMPRESION['rubrovalor'][1] + (i * 7),locale.currency((pagos['valor']/1.12), grouping=True))
                                    else:
                                        pdf.text(POSICIONES_IMPRESION['rubrovalor'][0],POSICIONES_IMPRESION['rubrovalor'][1] + (i * 7),locale.currency((pagos['valor']), grouping=True))
                                    i += 1
                        else:
                            for pagos in invoice['pagos']:
                                if (pagos['valor']):
                                    pdf.text(POSICIONES_IMPRESION['rubroalumno'][0],POSICIONES_IMPRESION['rubroalumno'][1],pagos['rubro']['alumno'])
                                    pdf.text(POSICIONES_IMPRESION['rubrotipo'][0],POSICIONES_IMPRESION['rubrotipo'][1] + (i * 7),str(i+1)  + pagos['rubro']['nombre'])
                                    if FACTURACION_CON_IVA:
                                        pdf.text(POSICIONES_IMPRESION['rubrovalor'][0],POSICIONES_IMPRESION['rubrovalor'][1] + (i * 7),locale.currency((pagos['valor']/1.12), grouping=True))
                                    else:
                                        pdf.text(POSICIONES_IMPRESION['rubrovalor'][0],POSICIONES_IMPRESION['rubrovalor'][1] + (i * 7),locale.currency((pagos['valor']), grouping=True))
                                    i += 1

                        #Pie de pagina de Factura
                        pdf.text(POSICIONES_IMPRESION['enletras'][0],POSICIONES_IMPRESION['enletras'][1],invoice['enletras'])
                        # pdf.text(POSICIONES_IMPRESION['subtotal'][0],POSICIONES_IMPRESION['subtotal'][1],locale.currency(invoice['subtotal'], grouping=True))
                        # pdf.text(POSICIONES_IMPRESION['total'][0],POSICIONES_IMPRESION['total'][1],locale.currency(invoice['total'], grouping=True))
                        # if FACTURACION_CON_IVA:
                        #     pdf.text(POSICIONES_IMPRESION['iva'][0],POSICIONES_IMPRESION['iva'][1],locale.currency(invoice['iva'], grouping=True))
                        # Sin locale.currency()
                        pdf.text(POSICIONES_IMPRESION['subtotal'][0],POSICIONES_IMPRESION['subtotal'][1],"%.2f"%invoice['subtotal'])
                        pdf.text(POSICIONES_IMPRESION['total'][0],POSICIONES_IMPRESION['total'][1],"%.2f"%invoice['total'])
                        if FACTURACION_CON_IVA:
                            pdf.text(POSICIONES_IMPRESION['iva'][0],POSICIONES_IMPRESION['iva'][1],"%.2f"%invoice['iva'])

                        d = datetime.datetime.now()
                        pdfname = 'factura-' + invoice['numero'] + '_' + d.strftime('%Y%m%d_%H%M%S') + '.pdf'
                        output_folder = os.path.join(JR_USEROUTPUT_FOLDER, elimina_tildes(request.user.username))
                        try:
                            os.makedirs(output_folder)
                        except Exception as ex:
                            pass
                        pdf.output(os.path.join(output_folder, pdfname))

                        factura.impresa = True
                        factura.save()
                        if FACTURACION_ELECTRONICA and not notadebito:
                            if Factura.objects.filter(numero= factura.numero).count()>1:
                                mail_errores_autorizacion("FACTURA REPETIDA "+DEFAULT_PASSWORD,"Existe mas de una factura repetida verificar en factura",factura.numero)
                        # signed_xml = sign_file(template_file='FAC13112014.xml',key_file='clave_privada.key', cert_file='certificado2.pem', password='Vanessa24')
                        # print(signed_xml)
                        return HttpResponse(json.dumps({'result': 'ok','reportfile': '/'.join([MEDIA_URL,'documentos',
                                                                                                   'userreports',
                                                                                               request.user.username,
                                                                                               pdfname])}),content_type="application/json")
                else:
                    if FACTURACION_ELECTRONICA and not notadebito:
                        if ReferidosInscripcion.objects.filter(inscripcionref=factura.estudiante(), pago=False).exists():
                            ref = ReferidosInscripcion.objects.filter(inscripcionref=factura.estudiante())[:1].get()
                            ref.pago = True
                            ref.save()

                        if Factura.objects.filter(numero= factura.numero).count()>1:
                            mail_errores_autorizacion("FACTURA REPETIDA "+DEFAULT_PASSWORD,"Existe mas de una factura repetida verificar en factura",factura.numero)
                            transaction.savepoint_rollback(sid)
                            return HttpResponse(json.dumps({'result':'badexist', "error": "Numero de Factura ya existe."}),content_type="application/json")
                        # if DEFAULT_PASSWORD == 'itb' and enviar_mensaje and not notadebito and ENVIAR_CODIGO_CEL:
                        #     enviarmensajeitb(inscripcion,request.user,factura.total)
                        if request.POST['descuento'] != '':
                            if DescuentoSeguimiento.objects.filter(pk=request.POST['descuento']).exists():
                                descuento = DescuentoSeguimiento.objects.filter(pk=request.POST['descuento'])[:1].get()
                                descuento.fechapago = datetime.datetime.now().date()
                                descuento.pagado = True
                                descuento.save()
                        if seguimiento:
                            if DescuentoSeguimiento.objects.filter(seguimiento__inscripcion=inscripcion).exists():
                                if request.POST['descuento'] == '':
                                    if EMAIL_ACTIVE:
                                        descuentos = DescuentoSeguimiento.objects.filter(seguimiento__inscripcion=inscripcion)[:1].get()
                                        descuentos.eliminado_descuento()
                                        descuentos.delete()




                        transaction.savepoint_commit(sid)

                        return HttpResponse(json.dumps({'result':'fac','id':factura.id}),content_type="application/json")
                        # return HttpResponseRedirect('/reportes?action=run&direct=true&n=factura_sri_comprobante&rt=pdf&factura='+str(factura.id ))
                    # OCU 01-07-2015 para impresion de facturas en buck
                    if CENTRO_EXTERNO  and not notadebito:
                        return HttpResponse(json.dumps({'result':'buck','id':factura.id}),content_type="application/json")
                if not notadebito:
                    if Factura.objects.filter(numero= factura.numero).count()>1:
                        mail_errores_autorizacion("FACTURA REPETIDA "+DEFAULT_PASSWORD,"Existe mas de una factura repetida verificar en factura",factura.numero)
                        transaction.savepoint_rollback(sid)
                        return HttpResponse(json.dumps({'result':'bad', "error": "Numero de Factura ya existe."}),content_type="application/json")
                # profiler.disable()
                # Guarda los resultados del perfil en un archivo
                # profiler.dump_stats(output_file)
                transaction.savepoint_commit(sid)
                end_time = datetime.datetime.now().time()
                print("DURACION DE PROCESO PAGAR Y FACTURAR "+str(start_time)+" - "+str(end_time))
                return HttpResponse(json.dumps({'result':'ok'}),content_type="application/json")
            except Exception as ex :
                transaction.savepoint_rollback(sid)
                return HttpResponse(json.dumps({'result':'bad', "error": str(ex)}),content_type="application/json")

        elif action == 'generar_wester':
                try:
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo.font.height = 20*11
                    subtitulo = xlwt.easyxf(num_format_str="@")

                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('Hoja1',cell_overwrite_ok=True)
                    cont =-1
                    no_ruc = open(os.path.join(MEDIA_ROOT, 'error.txt'), 'w')
                    fec=datetime.datetime.now().date()
                    fec=datetime.datetime.now().date()  + timedelta(days=30)
                    i = Inscripcion.objects.filter(pk=request.POST['id'])[:1].get()
                    inscripcion = i
                    if i.persona.cedula or  i.persona.pasaporte:
                        for r in Rubro.objects.filter(inscripcion=inscripcion,cancelado=False).order_by('cancelado','fechavence'):
                            cont =cont +1
                            adeuda=0
                            if HABILITA_APLICA_DESCUE:
                                if r.aplicadescuento('None')[1] > 0:
                                    adeuda = str(Decimal(r.aplicadescuento('None')[1]).quantize(Decimal(10) ** -2)).replace(",",".")
                            else:
                                adeuda = str(Decimal(r.adeudado()).quantize(Decimal(10)**-2)).replace(",",".")

                            if adeuda > 0:
                                if i.persona.cedula:
                                    ws.write(cont, 0, str(i.persona.cedula),subtitulo)
                                else:
                                    ws.write(cont, 0, str(i.persona.pasaporte),subtitulo)

                                try:
                                    nombrecompleto = i.persona.nombre_completo_inverso()
                                except Exception as e:
                                    nombrecompleto = str(elimina_tildes(i.persona.nombre_completo()))
                                ws.write(cont, 1, nombrecompleto,subtitulo)
                                # ws.row(cont).set_cell_text()
                                if HABILITA_APLICA_DESCUE:
                                    adeuda = str(Decimal(r.aplicadescuento('None')[1]).quantize(Decimal(10) ** -2)).replace(",",".")
                                else:
                                    adeuda = str(Decimal(r.adeudado()).quantize(Decimal(10)**-2)).replace(",",".")
                                ws.write(cont, 2, adeuda,subtitulo)
                                ws.write(cont, 3,"0.00",subtitulo)
                                ws.write(cont, 4,"0.00",subtitulo)
                                try:
                                    fecha2=datetime.datetime(int(datetime.datetime.now().date().year+1) ,r.fechavence.month,r.fechavence.day).date()
                                except :
                                    r.fechavence = r.fechavence - timedelta(1)
                                    fecha2=datetime.datetime(int(datetime.datetime.now().date().year+1) ,r.fechavence.month,r.fechavence.day).date()
                                ws.write(cont, 5,str(fecha2).replace('-',''),subtitulo)
                                #OCastillo 26-07-2022 campo hora de vencimiento
                                ws.write(cont, 6,"23:59",subtitulo)
                                ws.write(cont, 7,r.id,subtitulo)
                                try:
                                    nombrerubro = r.nombre()
                                except:
                                    nombrerubro = elimina_tildes(r.nombre())
                                ws.write(cont, 8,nombrerubro,subtitulo)
                    else:
                        no_ruc.write(str(inscripcion) + '\n')
                    no_ruc.close()
                    # nombre fechanueva=datetime.now().date() + timedelta(days=1) ='clientes'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    fechanueva=datetime.datetime.now().date() + timedelta(days=1)
                    nombre ='141'+str(datetime.datetime.now().time())+'.xls'
                    wb.save(MEDIA_ROOT+'/archivowester/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/archivowester/"+nombre}),content_type="application/json")
                except Exception as ex:
                    # return HttpResponse(json.dumps({"result":str(ex + " "+ str(inscripcion.persona.nombre_completo()))}),content_type="application/json")
                    return HttpResponse(json.dumps({"result":"bad" }),content_type="application/json")


        elif action=='facturartrico':
            var = ""
            sid = transaction.savepoint()
            try:
                data = json.loads(request.POST['data'])
                pagos = data['pagos']
                caja = request.session['persona'].lugarrecaudacion_set.filter(activa=True)[:1].get()
                lugar = LugarRecaudacion.objects.filter(persona=request.session['persona'],activa=True)[:1].get()
                sesion_caja = caja.sesion_caja()

                fichamedica = None

                notadebito = data['notadebito']

                if FACTURACION_ELECTRONICA:
                    recepcion = ''
                    dirfactur=''
                    mensajerecep=''
                else:
                    recepcion=None
                    dirfactur=None
                    mensajerecep=None
                factnumero=0
                if not notadebito:
                    if Factura.objects.filter(numero=caja.puntoventa+"-"+str(data['factura']['numero']).zfill(9)).exists():
                        return HttpResponse(json.dumps({'result':'badexist', "error": "Numero de Factura ya existe."}),content_type="application/json")
                    try:
                        if ClienteFactura.objects.filter(ruc=data['factura']['ruc']).exists():
                            cliente = ClienteFactura.objects.filter(ruc=data['factura']['ruc'])[:1].get()
                            cliente.nombre = elimina_tildes(data['factura']['nombre'])
                            cliente.direccion = elimina_tildes(data['factura']['direccion'])
                            cliente.telefono = elimina_tildes(data['factura']['telefono'])
                            cliente.correo = data['factura']['correo']
                            if cliente.contrasena == None:
                                cliente.contrasena = data['factura']['ruc']
                                cliente.numcambio = 0
                            cliente.save()
                        else:
                            cliente = ClienteFactura(ruc=data['factura']['ruc'], nombre=elimina_tildes(data['factura']['nombre']),
                                direccion=elimina_tildes(data['factura']['direccion']), telefono=elimina_tildes(data['factura']['telefono']),
                                correo=data['factura']['correo'],contrasena=data['factura']['ruc'],numcambio=0)
                            cliente.save()
                    except :
                        cliente = ClienteFactura(ruc=data['factura']['ruc'], nombre=elimina_tildes(data['factura']['nombre']),
                            direccion=elimina_tildes(data['factura']['direccion']), telefono=elimina_tildes(data['factura']['telefono']),
                            correo=data['factura']['correo'],contrasena=data['factura']['ruc'],numcambio=0)
                        cliente.save()

                    # Chequear numero de factura

                    if FACTURACION_ELECTRONICA:
                        if lugar.numerofact == None:
                            lugar.numerofact = data['factura']['numero']
                            lugar.save()
                        factnumero = lugar.numerofact
                    else:
                        factnumero = int(data['factura']['numero'])

                    factura = Factura(numero = caja.puntoventa.strip()+"-"+str(factnumero).zfill(9), fecha = datetime.datetime.today().date(),
                                    valida = True, cliente = cliente,
                                    subtotal = 0, iva = 0, total = 0, hora=datetime.datetime.today().time(),
                                    impresa=False, caja=caja, estado = recepcion, mensaje = mensajerecep,dirfactura=dirfactur)

                    if MODELO_IMPRESION_NUEVO:
                        factura.impresa = True

                    factura.save()

                    total_factura = 0

                for pago in pagos:
                    tp = None
                    if pago['formadepago']==FORMA_PAGO_EFECTIVO or pago['formadepago']==FORMA_PAGO_ELECTRONICO or  pago['formadepago']==FORMA_PAGO_WESTER :
                        pass
                    elif pago['formadepago']==FORMA_PAGO_CHEQUE:
                        hoy = datetime.datetime.today().date()
                        f_cobro =convertir_fecha(pago['fechacobro'])

                        tp = PagoCheque(numero=pago['numero'],banco=Banco.objects.get(pk=pago['bancocheque']),
                                        fecha=datetime.datetime.today().date(),
                                        fechacobro=convertir_fecha(pago['fechacobro']),
                                        emite=pago['emite'], valor=float(pago['valor']), protestado=False)
                        tp.save()

                        if f_cobro!= hoy:
                             tp.recibido=False
                        else:
                             tp.recibido=True
                        tp.save()

                    elif pago['formadepago']==FORMA_PAGO_DEPOSITO:
                        tp = PagoTransferenciaDeposito(referencia=pago['referencia'],
                                        fecha=datetime.datetime.today().date(),
                                        cuentabanco=CuentaBanco.objects.get(pk=pago['cuentabanco']),
                                        valor=float(pago['valor']),
                                        deposito=True)
                        tp.save()
                    elif pago['formadepago']==FORMA_PAGO_TRANSFERENCIA:
                        tp = PagoTransferenciaDeposito(referencia=pago['referencia'],
                            fecha=datetime.datetime.today().date(),
                            cuentabanco=CuentaBanco.objects.get(pk=pago['cuentabanco']),
                            valor=float(pago['valor']),
                            deposito=False)
                        tp.save()
                    elif pago['formadepago']==FORMA_PAGO_TARJETA or pago['formadepago']==FORMA_PAGO_TARJETA_DEB:
                        if pago['formadepago']==FORMA_PAGO_TARJETA:
                            tarjetadebito = False
                        else:
                            tarjetadebito = True
                        tp = PagoTarjeta(banco=Banco.objects.get(pk=pago['bancotarjeta']),
                                tipo=TipoTarjetaBanco.objects.get(pk=pago['tipotarjeta']),
                                poseedor=pago['poseedor'],
                                valor = float(pago['valor']),
                                procesadorpago=ProcesadorPagoTarjeta.objects.get(pk=pago['procesadorpago']),
                                referencia=pago['referencia'],
                                tarjetadebito=tarjetadebito,
                                fecha=datetime.datetime.today().date(),
                                lote=pago['lote'],adquiriente=pago['adquiriente'])
                        tp.save()

                    elif pago['formadepago']==FORMA_PAGO_RETENCION:
                        tp = PagoRetencion(autorizacion=pago['autorizacion'],
                                numerot = pago['numerot'],
                                tiporetencion=TipoRetencion.objects.get(pk=pago['tiporetencion']),
                                valor = float(pago['valor']),
                                fecha=datetime.datetime.today().date())
                        tp.save()

                    elif pago['formadepago']==FORMA_PAGO_NOTA_CREDITO:
                        tp = PagoNotaCreditoInstitucion(notacredito=NotaCreditoInstitucion.objects.get(pk=pago['notacredito']),
                                                       valor = float(pago['valor']),
                                                       fecha = datetime.datetime.today().date())
                        tp.save()
                        ncp = tp.notacredito
                        # ncp.valor = round(ncp.valor - float(pago['valor']),2)
                        # if ncp.valor <= 0:
                        ncp.cancelada = True
                        ncp.save()



                    pagosdesglosados = pago['pagos']


                    for pagorubro in pagosdesglosados:
                        rubro = Rubro.objects.get(pk=pagorubro['rubro']['id'])
                        if rubro.tipo() != 'ESPECIE':
                            enviar_mensaje=True
                        if fichamedica==None:
                            fichamedica = rubro.fichamedica
                        electronico=False
                        wester = False
                        efectivo=False
                        if tp==None:
                            if  pago['formadepago']==FORMA_PAGO_ELECTRONICO:
                                electronico=True
                            elif  pago['formadepago']==FORMA_PAGO_WESTER:
                                wester=True
                            else:
                                efectivo = True


                        # ///////////////////////////////////////////////////
                        # //////////////////////////////////////////////////
                        pago2 = Pago(fecha=datetime.datetime.today().date(),
                                    recibe=request.session['persona'],
                                    valor=float(pagorubro['valor']),
                                    rubro=rubro,
                                    efectivo=efectivo,
                                    wester=wester,
                                    sesion=sesion_caja,
                                    electronico=electronico)



                        if not notadebito:
                            total_factura = round(total_factura+float(pagorubro['valor']),2)

                        pago2.save()
                        if rubro.adeudado()==0:
                            rubro.cancelado = True
                            from clinicaestetica.models import RubroEstetico
                            rubroestetico = RubroEstetico.objects.filter(rubro=rubro.id)[:1].get()
                            rubroestetico.pago = datetime.datetime.today()
                            rubroestetico.save()
                            rubro.save()

                        if tp!=None:
                            tp.pagos.add(pago2)

                        if not notadebito:
                            factura.pagos.add(pago2)

                    #Establecer los valores de la factura Total y SubTotal
                    if not notadebito:
                        if FACTURACION_CON_IVA:
                            factura.total = total_factura
                            factura.subtotal = round(factura.total / COEFICIENTE_CALCULO_BASE_IMPONIBLE, 2)
                            factura.iva = round(factura.total - factura.subtotal, 2)
                        else:
                            factura.subtotal = total_factura
                            factura.total = total_factura
                        factura.save()



                # Incrementar el numero de Factura
                if not notadebito:
                    sesion_caja.facturatermina = int(factnumero)+1
                    sesion_caja.save()
                    if FACTURACION_ELECTRONICA or lugar.numerofact  != None:
                        for luga in LugarRecaudacion.objects.all():
                            if luga.puntoventa == lugar.puntoventa:
                                luga.numerofact = int(factnumero)+1
                                luga.save()


                if FACTURACION_ELECTRONICA and not notadebito:

                    if Factura.objects.filter(numero= factura.numero).count()>1:
                        mail_errores_autorizacion("FACTURA REPETIDA "+DEFAULT_PASSWORD,"Existe mas de una factura repetida verificar en factura",factura.numero)
                        transaction.savepoint_rollback(sid)
                        return HttpResponse(json.dumps({'result':'badexist', "error": "Numero de Factura ya existe."}),content_type="application/json")
                    transaction.savepoint_commit(sid)
                    return HttpResponse(json.dumps({'result':'fac','id':factura.id}),content_type="application/json")

                if not notadebito:
                    if Factura.objects.filter(numero= factura.numero).count()>1:
                        mail_errores_autorizacion("FACTURA REPETIDA "+DEFAULT_PASSWORD,"Existe mas de una factura repetida verificar en factura",factura.numero)
                        transaction.savepoint_rollback(sid)
                        return HttpResponse(json.dumps({'result':'bad', "error": "Numero de Factura ya existe."}),content_type="application/json")

                transaction.savepoint_commit(sid)
                return HttpResponse(json.dumps({'result':'ok'}),content_type="application/json")
            except Exception as ex :
                transaction.savepoint_rollback(sid)
                return HttpResponse(json.dumps({'result':'bad', "error": str(ex)}),content_type="application/json")

        elif action=='addrecibocaja':
            inscripcion = Inscripcion.objects.get(pk=request.POST['id'])
            try:
                # caja = request.session['persona'].lugarrecaudacion_set.get()
                caja = request.session['persona'].lugarrecaudacion_set.filter(activa=True)[:1].get()
                sesion_caja = caja.sesion_caja()
                f = ReciboCajaInstitucionForm(request.POST)
                if f.is_valid():
                    rc = ReciboCajaInstitucion(inscripcion=inscripcion,
                                               motivo=f.cleaned_data['motivo'],
                                               sesioncaja=sesion_caja,
                                               fecha=datetime.datetime.today().date(),
                                               hora=datetime.datetime.now().time(),
                                               valorinicial=f.cleaned_data['valorinicial'],
                                               saldo=f.cleaned_data['valorinicial'])
                    rc.save()

                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de CREACION DE RECIBO DE CAJA INSTITUCIONAL
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(rc).pk,
                        object_id       = rc.id,
                        object_repr     = force_str(rc),
                        action_flag     = ADDITION,
                        change_message  = 'Adicionado Recibo de Caja ' + str(inscripcion) + '(' + client_address + ')')

                    return HttpResponseRedirect("/finanzas?action=rubros&id="+str(inscripcion.id))
                else:
                    return HttpResponseRedirect("/finanzas?action=addrecibocaja&id="+str(inscripcion.id))
            except:
                return HttpResponseRedirect("/finanzas?action=addrecibocaja&id="+str(inscripcion.id))


        elif action=='addpago':
            # Adicionar Pago
            rubro = Rubro.objects.get(pk=request.POST['rubroid'])
            caja = request.session['persona'].lugarrecaudacion_set.get()
            sesion_caja = caja.sesion_caja()

            f = PagoForm(request.POST)

            if f.is_valid():
                pago = Pago(fecha=datetime.datetime.now(), lugar=caja, recibe=caja.persona,
                            valor=f.cleaned_data['valor'], rubro=rubro,
                            efectivo=f.cleaned_data['formadepago'].id==FORMA_PAGO_EFECTIVO)
                pago.save()

                # Tarjeta
                if f.cleaned_data['formadepago'].id==FORMA_PAGO_TARJETA:
                    pagoTarjeta = PagoTarjeta(banco=f.cleaned_data['bancotarjeta'],
                                            tipo=f.cleaned_data['tipo'], poseedor=f.cleaned_data['poseedor'],
                                            valor=f.cleaned_data['valor'], procesadorpago=f.cleaned_data['procesadorpago'],
                                            referencia=f.cleaned_data['referencia'], fecha=datetime.datetime.now(),
                                            lote=f.cleaned_data['lote'],adquiriente=f.cleaned_data['adquiriente'],autorizacion=f.cleaned_data['autorizacion'])
                    pagoTarjeta.save()
                    pagoTarjeta.pagos.add(pago)

                # Cheque
                elif f.cleaned_data['formadepago'].id==FORMA_PAGO_CHEQUE:
                    pagoCheque = PagoCheque(banco=f.cleaned_data['bancocheque'],
                                        numero=f.cleaned_data['numero'], fecha=datetime.datetime.now(),
                                        fechacobro=f.cleaned_data['fechacobro'], emite=f.cleaned_data['emite'],
                                        valor=f.cleaned_data['valor'], protestado=False)
                    pagoCheque.save()
                    pagoCheque.pagos.add(pago)

                # Deposito
                elif f.cleaned_data['formadepago'].id==FORMA_PAGO_DEPOSITO:
                    pagoDeposito = PagoTransferenciaDeposito(referencia = f.cleaned_data['referenciatransferencia'],
                        fecha = datetime.datetime.now(), cuentabanco=f.cleaned_data['cuentabanco'],
                        valor = f.cleaned_data['valor'], deposito = True)
                    pagoDeposito.save()

                # Transferencia
                elif f.cleaned_data['formadepago'].id==FORMA_PAGO_TRANSFERENCIA:
                    pagoTransferencia = PagoTransferenciaDeposito(referencia = f.cleaned_data['referenciatransferencia'],
                        fecha = datetime.datetime.now(), cuentabanco=f.cleaned_data['cuentabanco'],
                        valor = f.cleaned_data['valor'], deposito = False)
                    pagoTransferencia.save()
                    pagoTransferencia.pagos.add(pago)

                # Recibo Caja
                elif f.cleaned_data['formadepago'].id==FORMA_PAGO_RECIBOCAJAINSTITUCION:
                    pagoRecibo = PagoReciboCajaInstitucion(recibocaja = f.cleaned_data['recibocaja'],
                                                            fecha = datetime.datetime.now(),
                                                            valor = f.cleaned_data['valor'])
                    pagoRecibo.save()
                    pagoRecibo.pagos.add(pago)

                # Notas de Credito
                elif f.cleaned_data['formadepago'].id==FORMA_PAGO_NOTA_CREDITO:
                    pagonc = PagoNotaCreditoInstitucion(notacredito=f.cleaned_data['notacredito'],
                                                        fecha = datetime.datetime.now(),
                                                        valor = f.cleaned_data['valor'])
                    pagonc.save()
                    pagonc.pagos.add(pago)


                if rubro.adeudado()==0.0:
                    rubro.cancelado = True
                else:
                    rubro.cancelado = False
                rubro.save()


                # Facturar
                # Cliente de Factura
                try:
                    if ClienteFactura.objects.filter(ruc= f.cleaned_data['facturaruc']).exists():
                        cliente = ClienteFactura.objects.filter(ruc=f.cleaned_data['facturaruc'])[:1].get()
                        cliente.nombre = elimina_tildes(f.cleaned_data['facturanombre'])
                        cliente.direccion = elimina_tildes(f.cleaned_data['facturadireccion'])
                        cliente.telefono = elimina_tildes(f.cleaned_data['facturatelefono'])
                        cliente.save()
                    else:
                        cliente = ClienteFactura(ruc=f.cleaned_data['facturaruc'], nombre=elimina_tildes(f.cleaned_data['facturanombre']),
                                        direccion=elimina_tildes(f.cleaned_data['facturadireccion']), telefono=elimina_tildes(f.cleaned_data['facturatelefono']))
                        cliente.save()
                except :
                    cliente = ClienteFactura(ruc=f.cleaned_data['facturaruc'], nombre=elimina_tildes(f.cleaned_data['facturanombre']),
                                        direccion=elimina_tildes(f.cleaned_data['facturadireccion']), telefono=elimina_tildes(f.cleaned_data['facturatelefono']))
                    cliente.save()

                factura = Factura(numero = f.cleaned_data['factura'], fecha = datetime.datetime.now(),
                                 valida = True, cliente = cliente,
                                subtotal = pago.valor, iva = 0, total = pago.valor,hora=datetime.datetime.now().time(),
                                impresa=False, caja=caja)
                factura.save()
                factura.pagos.add(pago)

                sesion_caja.facturatermina = int(f.cleaned_data['factura'])+1
                sesion_caja.save()

            return HttpResponseRedirect("/finanzas?s="+str(rubro.inscripcion.persona.cedula))
        elif action == 'rubroadd':

            if request.POST['codigo']:
                try:
                    rubroad = RubroAdicional.objects.get(pk=request.POST['rubroad'])
                    inscripcion = Inscripcion.objects.get(pk=request.POST['inscripcion'])
                    rubro = Rubro(fecha=datetime.datetime.now(),
                                    valor=rubroad.valor,
                                    inscripcion = inscripcion,
                                    cancelado=False,
                                    fechavence=datetime.datetime.now())
                    rubro.save()
                    rubrootro = RubroOtro(rubro=rubro, tipo_id=12, descripcion=(rubroad.descripcion+ " - " + str(request.POST['codigo'])) ,extra =str(request.POST['codigo']))
                    rubrootro.save()
                    return HttpResponseRedirect("/finanzas?action=rubros&id="+str(inscripcion.id))
                except:
                    return HttpResponseRedirect("/finanzas?action=rubros&id="+request.POST['inscripcion'])
            else:
                return HttpResponseRedirect("/finanzas?action=rubros&error2=1&id="+request.POST['inscripcion'])

        if action=='chequepro':
            try:
                cheque=InscripcionFlaForm(request.POST)
                if cheque.is_valid():

                    if Inscripcion.objects.filter(pk=request.POST['id']).exists():
                        ins=Inscripcion.objects.filter(pk=request.POST['id'])[:1].get()
                        if InscripcionFlags.objects.filter(inscripcion=ins).exists():
                            inscheque=InscripcionFlags.objects.filter(inscripcion=ins)[:1].get()
                            if inscheque.tienechequeprotestado:
                                inscheque.tienechequeprotestado=False
                                inscheque.save()
                                msj='Cheque Protestado Editado'
                                client_address = ip_client_address(request)
                                LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(inscheque).pk,
                                object_id       = inscheque.id,
                                object_repr     = force_str(inscheque),
                                action_flag     = ADDITION,
                                change_message  = msj + ' (' + client_address + ')')

                                return HttpResponseRedirect('/finanzas')
                    return HttpResponseRedirect('/finanzas?errorcheque=no se encontro el id de la inscripcion')
                return HttpResponseRedirect('/finanzas?errorcheque=Error en el formulario')
            except Exception as e:
                return HttpResponseRedirect('/finanzas'+str(e))

        if action=='deletedescuento':

            try:
                f = EliminaRubroForm(request.POST)
                if f.is_valid():
                    if Rubro.objects.filter(pk=request.POST['id']).exists():
                        rubro= Rubro.objects.filter(pk=request.POST['id'])[:1].get()
                        if DetalleDescuento.objects.filter(rubro=rubro).exists():
                            if not rubro.cancelado:
                                val=0
                                for detades in DetalleDescuento.objects.filter(rubro=rubro):

                                    rubro.valor=rubro.valor+detades.valor
                                    rubro.save()
                                    descuento=detades.descuento

                                    val=detades.valor+val
                                    detades.delete()
                                    if not DetalleDescuento.objects.filter(descuento__id=descuento.id).exists():
                                        descuento.delete()

                                mensaje = 'Descuento Eliminado '+ str(val)
                                inscripcion=rubro.inscripcion
                                client_address = ip_client_address(request)
                                LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(rubro).pk,
                                object_id       = rubro.id,
                                object_repr     = force_str(rubro),
                                action_flag     = DELETION,
                                change_message  = mensaje +inscripcion.persona.nombre_completo() + ' Motivo: '+ f.cleaned_data['motivo'].upper() +' Autoriza: '+ f.cleaned_data['autoriza'].upper()+' (' +client_address + ')')
                                return HttpResponseRedirect("/finanzas?action=rubros&id="+str(request.POST['idins']))
                            return HttpResponseRedirect("/finanzas?action=rubros&errordescuento=EL RUBRO ESTA CANCELADO &id="+str(request.POST['idins']))
                        return HttpResponseRedirect("/finanzas?action=rubros&errordescuento=NO EXISTE DESCUENTO &id="+str(request.POST['idins']))
                    return HttpResponseRedirect("/finanzas?action=rubros&errordescuento=EL RUBRO NO EXISTE &id="+str(request.POST['idins']))
                return HttpResponseRedirect("/finanzas?action=rubros&errordescuento=El FORMULARIO NO ES VALIDO &id="+str(request.POST['idins']))

            except Exception as e:

                return HttpResponseRedirect("/finanzas?action=rubros&error=OCURRIO UN ERROR INTENTE NUEVAMENTE"+str(e)+ "&id="+str(request.POST['idins']))


        elif action=='addespecie':
            # Adicionar Especie Valorada
            if int(request.POST['especie'])>0:
                tipoEspecie = TipoEspecieValorada.objects.get(pk=request.POST['especie'])
                inscripcion = Inscripcion.objects.get(pk=request.POST['inscripcion'])


                rubro = Rubro(fecha=datetime.datetime.now(),
                            valor=tipoEspecie.precio,
                            inscripcion = inscripcion,
                            cancelado=tipoEspecie.precio==0,
                            fechavence=datetime.datetime.now())
                rubro.save()
                solicitud = SolicitudOnline.objects.filter(pk=3)[:1].get()
                solicitudest = SolicitudEstudiante(solicitud=solicitud,
                                                                  inscripcion=inscripcion,
                                                                  observacion=str('SOLICITUD GENERADA POR SECRETARIA'),
                                                                  tipoe_id=ESPECIE_TRAMITES_VARIOS,
                                                                  correo=inscripcion.persona.emailinst,
                                                                  celular=inscripcion.persona.telefono,
                                                                  fecha=datetime.datetime.now())
                solicitudest.save()
                solicitudest.rubro = rubro
                solicitudest.solicitado=True

                solicitudest.save()

                # Rubro especie valorada
                rubroenot = generador_especies.generar_especie(rubro=rubro, tipo=tipoEspecie)
                rubroenot.autorizado=False
                rubroenot.save()
                if tipoEspecie.id == ID_TIPO_ESPECIE_REG_NOTA:
                    if rubroenot:
                        rubroenot.disponible = False
                        rubroenot.aplicada = False
                        rubroenot.fecha = datetime.datetime.now()
                        rubroenot.usuario = request.user
                        rubroenot.materia_id = request.POST['materiaasignregid']
                        rubroenot.save()
                #Obtain client ip address
                client_address = ip_client_address(request)

                #Log crear rubro especie OCU 08-nov-2017
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(tipoEspecie).pk,
                    object_id       = tipoEspecie.id,
                    object_repr     = force_str(tipoEspecie),
                    action_flag     = ADDITION,
                    change_message  =  "Creado Rubro Especie  " +  '(' + str(inscripcion) + ')' + '(' +  client_address + ')' )

                return HttpResponseRedirect("/finanzas?action=rubros&id="+str(inscripcion.id))
            else:
                return HttpResponseRedirect("/finanzas?action=rubros&id="+request.POST['inscripcion'])

        elif action=='addmateria':
            try:
                materiaasignada = MateriaAsignada.objects.get(pk=request.POST['mid'])
                inscripcion = Inscripcion.objects.get(pk=request.POST['id'])
                a = request.POST['fe']
                rubro = Rubro(fecha=datetime.datetime.now(), valor=float(request.POST['valor']),
                    inscripcion=inscripcion, cancelado=False, fechavence=datetime.datetime(int(a[6:10]), int(a[3:5]), int(a[0:2])))
                rubro.save()
                rubromateriaasignada = RubroMateria(rubro=rubro, materiaasignada=materiaasignada)
                rubromateriaasignada.save()

                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de ADICIONAR RUBRO MATERIA
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(rubromateriaasignada).pk,
                    object_id       = rubromateriaasignada.id,
                    object_repr     = force_str(rubromateriaasignada),
                    action_flag     = ADDITION,
                    change_message  = 'Adicionado Rubro Materiaasignada ' + str(inscripcion) + ' (' + client_address + ')' )

                return HttpResponse(json.dumps({'result':'ok'}),content_type="application/json")
            except :
                return HttpResponse(json.dumps({'result':'bad'}),content_type="application/json")
        elif action=='addotro':
            try:
                tipootro = TipoOtroRubro.objects.get(pk=request.POST['tid'])
                inscripcion = Inscripcion.objects.get(pk=request.POST['id'])
                a = request.POST['fe']
                rubro = Rubro(fecha=datetime.datetime.now(), valor=float(request.POST['valor']),
                    inscripcion=inscripcion, cancelado=False, fechavence=datetime.datetime(int(a[6:10]), int(a[3:5]), int(a[0:2])))
                rubro.save()
                rubrootro = RubroOtro(rubro=rubro, tipo=tipootro, descripcion=request.POST['ta'])
                rubrootro.save()

                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de ADICIONAR RUBRO OTRO
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(rubrootro).pk,
                    object_id       = rubrootro.id,
                    object_repr     = force_str(rubrootro.rubro),
                    action_flag     = ADDITION,
                    change_message  = 'Adicionado Rubro Otro ' + str(inscripcion) + '(' + client_address + ')' )

                return HttpResponse(json.dumps({'result':'ok'}),content_type="application/json")
            except :
                return HttpResponse(json.dumps({'result':'bad'}),content_type="application/json")


        elif action=='editrubro':
            rubro = Rubro.objects.get(pk=request.POST['id'])
            f = RubroForm(request.POST)
            if f.is_valid():
                persona = request.session['persona']
                # if EMAIL_ACTIVE:
                rubro.mail_editrubro(persona.nombre_completo(),f.cleaned_data['valor'],f.cleaned_data['motivo'].upper(),f.cleaned_data['autoriza'].upper())

                # rubro.fechavence = f.cleaned_data['fechavence']
                rubro.valor = f.cleaned_data['valor']
                rubro.save()
                logr = RubroLog(rubro=rubro,motivo=f.cleaned_data['motivo'],
                                autoriza= f.cleaned_data['autoriza'],
                                fecha=datetime.datetime.now(),
                                usuario=request.user)
                logr.save()
                if not CENTRO_EXTERNO:
                    rubro.inscripcion.actualiza_estadistica() #Actualiza la estadistica del alumno en el modelo InscripcionEstadistica

                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de EDICION DE RUBRO
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(rubro).pk,
                    object_id       = rubro.id,
                    object_repr     = force_str(rubro),
                    action_flag     = CHANGE,
                    change_message  = 'Modificado Rubro ' + str(rubro.inscripcion) + '(' + client_address + ')' )

                return HttpResponseRedirect("/finanzas?action=rubros&id="+str(rubro.inscripcion.id))
            else:
                return HttpResponseRedirect("/finanzas?action=editrubros&id="+str(rubro.id))

        elif action=='editfecha':
            rubro = Rubro.objects.get(pk=request.POST['id'])
            f = RubroFechaForm(request.POST)
            if f.is_valid():
                persona = request.session['persona']
                fecha = rubro.fechavence
                rubro.fechavence = f.cleaned_data['fechavence']
                # rubro.valor = f.cleaned_data['valor']
                rubro.save()
                if EMAIL_ACTIVE:
                    rubro.mail_editfecha(persona.nombre_completo(),fecha,f.cleaned_data['motivo'].upper(),f.cleaned_data['autoriza'].upper())
                if not CENTRO_EXTERNO:
                    rubro.inscripcion.actualiza_estadistica() #Actualiza la estadistica del alumno en el modelo InscripcionEstadistica

                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de EDICION DE RUBRO
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(rubro).pk,
                    object_id       = rubro.id,
                    object_repr     = force_str(rubro),
                    action_flag     = CHANGE,
                    change_message  = 'Modificado Fecha Rubro ' + str(rubro.inscripcion) + '(' + client_address + ')' )

                return HttpResponseRedirect("/finanzas?action=rubros&id="+str(rubro.inscripcion.id))
            else:
                return HttpResponseRedirect("/finanzas?action=editfecha&id="+str(rubro.id))

        elif action=='addnc':
            inscripcion = Inscripcion.objects.get(pk=request.POST['id'])
            f = NotaCreditoForm(request.POST)
            if f.is_valid():
                nc = NotaCredito(inscripcion=inscripcion, fecha=f.cleaned_data['fecha'],
                                valorinicial=f.cleaned_data['valorinicial'], saldo=f.cleaned_data['valorinicial'],
                                motivo=f.cleaned_data['motivo'])
                nc.save()

                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de CREACION NOTA DE CREDITO
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(nc).pk,
                    object_id       = nc.id,
                    object_repr     = force_str(nc),
                    action_flag     = ADDITION,
                    change_message  = 'Adicionada Nota de Credito ' + str(inscripcion) + ' (' + client_address + ')')
                return HttpResponseRedirect("/finanzas?action=rubros&id="+str(inscripcion.id))
            else:
                return HttpResponseRedirect("/finanzas?action=addnc&id="+str(inscripcion.id))

        elif action =='adddonacion':
            inscripcion = Inscripcion.objects.get(pk=request.POST['id'])
            f = DonacionForm(request.POST)
            if f.is_valid():
                donacion = Donacion(inscripcion=inscripcion,
                                    valor=f.cleaned_data['valor'],
                                    motivo=f.cleaned_data['motivo'],
                                    fecha=datetime.datetime.now(),
                                    usuario=request.user.username)
                donacion.save()

                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de CREACION DONACION
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(donacion).pk,
                    object_id       = donacion.id,
                    object_repr     = force_str(donacion),
                    action_flag     = ADDITION,
                    change_message  = 'Creada una Donacion (' + client_address + ')')

                return HttpResponseRedirect("/finanzas?s="+str(inscripcion.persona.cedula))

        elif action=='addrecibo_condu':
            try:
                num_recibo =ReciboPermisoCondu.objects.all().exclude(numero=None)

                if not num_recibo:
                   num_recibo = 0
                else:
                   recibo_permiso = ReciboPermisoCondu.objects.all().order_by('-numero').exclude(numero=None)[:1].get()
                   num_recibo = recibo_permiso.numero

                i = Inscripcion.objects.get(pk=request.POST['id'])
                banco = None
                if request.POST['bancotarjetaperm'] != '':
                    banco = request.POST['bancotarjetaperm']
                if request.POST['bancochequeperm'] != '':
                    banco = request.POST['bancochequeperm']

                recibo = ReciboPermisoCondu(inscripcion=i,
                                  numero=num_recibo +1,
                                  fecha=datetime.datetime.now(),
                                  usuario=request.user,
                                  valor = Decimal(VALOR_PERMISO_CONDU),
                                  formadepago_id = request.POST['formadepagoperm'],
                                  numerocheq = request.POST['numerocheq'],
                                  emite = request.POST['emiteperm'],
                                  referencia = request.POST['referenciaperm'],
                                  tipotarje_id = request.POST['tipoperm'],
                                  poseedor = request.POST['poseedorperm'],
                                  procesadorpago_id = request.POST['procesadorpagoperm'],
                                  banco_id = banco,
                                  referenciatransferencia = request.POST['referenciatransferenciaperm'],
                                  cuentabanco_id = request.POST['cuentabancoperm'])
                recibo.save()
                if request.POST['fechacobroperm']:
                    recibo.fechacobro = request.POST['fechacobroperm']
                    recibo.save()
                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de ADICIONAR RECIBO PERMISO CONDUCCION
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(recibo).pk,
                    object_id       = recibo.id,
                    object_repr     = force_str(recibo),
                    action_flag     = ADDITION,
                    change_message  = 'Genera Recibo Permiso Conduccion (' + client_address + ')' )

                return HttpResponse(json.dumps({"result":"ok","id":str(i.id)}),content_type="application/json")
            except Exception as ex:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")


        elif action=='actualizafecha':
            rubro = Rubro.objects.get(pk=request.POST['rid'])
            rubro.fechavence = convertir_fecha(request.POST['fecha'])
            rubro.save()

            #Obtain client ip address
            client_address = ip_client_address(request)

            # Log de EDICION DE FECHA VENCIMIENTO RUBRO
            LogEntry.objects.log_action(
                user_id         = request.user.pk,
                content_type_id = ContentType.objects.get_for_model(rubro).pk,
                object_id       = rubro.id,
                object_repr     = force_str(rubro),
                action_flag     = CHANGE,
                change_message  = 'Cambio de Fecha de Vencimiento '+str(rubro.inscripcion) + ' (' + client_address + ')')

            data = {"result": "ok", "rid": rubro.id, "fecha": rubro.fechavence.strftime("%d-%m-%Y"), "vencido": rubro.vencido()}
            return HttpResponse(json.dumps(data),content_type="application/json")

        elif action =='pagar':
            tipo = request.POST['tipo']
            rubro = Rubro.objects.get(pk=request.POST['rubro'])

            if tipo == '1':
                persona = request.session['persona']
                lugar = persona.lugarrecaudacion_set.get()
                pago = Pago(fecha=datetime.datetime.now(),valor=float(request.POST['valor']),
                            rubro=rubro,efectivo=True,recibe=persona,lugar=lugar)
                pago.save()

            rubro.chequea_cancelacion()
            return HttpResponse(json.dumps({"result":"ok"}), content_type="application/json")

        elif action=='chart':
            hoy = datetime.datetime.today().date()
            #Sesiones del dia con algun valor final
            data = {"results": [{"id": x.id, "caja":x.caja.nombre, "efectivo":x.total_efectivo_sesion(), "cheque":x.total_cheque_sesion(),
                                 "tarjeta":x.total_tarjeta_sesion(),"deposito":x.total_deposito_sesion(),"transf":x.total_transferencia_sesion(),
                                 "ncredito":x.total_notadecredito_sesion()} for x in SesionCaja.objects.filter(fecha=hoy).order_by('caja__nombre') if x.total_sesion()]}
            return HttpResponse(json.dumps(data), content_type="application/json")

        elif action=='validarfecha':
            try:
                inscripcion = Inscripcion.objects.filter(id=request.POST['id'])[:1].get()
                if inscripcion.id == CONSUMIDOR_FINAL:
                    return HttpResponse(json.dumps({"result":"ok"}), content_type="application/json")

                rubroconsult = Rubro.objects.get(id=request.POST['idrub'])
                if rubroconsult.fraude_pendiente():
                    return HttpResponse(json.dumps({"result": "ok"}), content_type="application/json")
                bandera = 0
                congreso = 0
                datos = json.loads(request.POST['data'])
                rubros = Rubro.objects.filter(inscripcion=inscripcion,cancelado=False).exclude(id__in=datos) if request.POST['check'] == "true" else Rubro.objects.filter(inscripcion=inscripcion,cancelado=False,id__in=datos)
                if rubroconsult.rubrootro_set.exists():
                    if rubroconsult.rubrootro_set.all()[:1].get().tipo.id == TIPO_CONGRESO_RUBRO or 'TALLER' in rubroconsult.rubrootro_set.all()[:1].get().descripcion or rubroconsult.rubrootro_set.all()[:1].get().tipo.id == TIPO_RUBRO_CREDENCIAL or rubroconsult.rubrootro_set.all()[:1].get().tipo.id == TIPO_RUBRO_MATERIALAPOYO:
                        return HttpResponse(json.dumps({"result":"ok"}), content_type="application/json")

                if rubroconsult.tipo() == "ESPECIE":
                    return HttpResponse(json.dumps({"result":"ok"}), content_type="application/json")

                for rubro in rubros:
                    if rubro.adeudado() < 0:
                        return HttpResponse(json.dumps({"result": "bad1","mens":"Rubro en negativo contacte con el administrador"}),content_type="application/json")
                    if rubro.rubrootro_set.exists():
                        if rubro.rubrootro_set.all()[:1].get().tipo.id == TIPO_CONGRESO_RUBRO or rubro.rubrootro_set.all()[:1].get().tipo.id == TIPO_RUBRO_CREDENCIAL or rubro.rubrootro_set.all()[:1].get().tipo.id == TIPO_RUBRO_MATERIALAPOYO or 'TALLER' in rubro.rubrootro_set.all()[:1].get().descripcion:
                            congreso = 1
                        if rubroconsult.rubrootro_set.exists():
                            if rubroconsult.rubrootro_set.all()[:1].get().tipo.id == TIPO_RUBRO_CREDENCIAL or rubroconsult.rubrootro_set.all()[:1].get().tipo.id == TIPO_RUBRO_MATERIALAPOYO:
                                congreso = 1

                    if request.POST['check'] == "true":
                        if rubro.fechavence < rubroconsult.fechavence and congreso == 0 and rubroconsult.tipo() != "ESPECIE":
                            bandera = 1
                            break
                    else:
                        if rubro.fechavence > rubroconsult.fechavence and congreso == 0 and rubroconsult.tipo() != "ESPECIE":
                            bandera = 1
                            break
                    congreso = 0
                if bandera == 1:
                    return HttpResponse(json.dumps({"result":"bad"}), content_type="application/json")
                return HttpResponse(json.dumps({"result":"ok"}), content_type="application/json")
            except Exception as e:
                print(e)

        elif action=='delrubro':
            rubro = Rubro.objects.get(pk=request.POST['id'])
            f = EliminaRubroForm(request.POST)
            if f.is_valid():
                if Rubro.objects.filter(pk=request.POST['id']).exists():
                    rubro = Rubro.objects.get(pk=request.POST['id'])
                    inscripcion = rubro.inscripcion
                    persona = request.session['persona']
                    if ReferidosInscripcion.objects.filter(inscripcionref=inscripcion).exists():
                        if RubroMatricula.objects.filter(rubro=rubro,matricula__nivel__nivelmalla__id=NIVEL_MALLA_UNO).exists():
                            # if rubro.es_matricula():
                                return HttpResponseRedirect("/finanzas?action=rubros&errorreferido=NO PUEDE ELIMINAR EL RUBRO DE MATRICULA DE UNA PERSONA REFERIDA&id="+str(rubro.inscripcion.id))
                    if rubro.puede_eliminarse():
                        #Obtain client ip address
                        client_address = ip_client_address(request)

                        # Log de BORRADO DE RUBRO
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(rubro).pk,
                            object_id       = rubro.id,
                            object_repr     = force_str(rubro),
                            action_flag     = DELETION,
                            change_message  = 'Eliminado Rubro - ' +inscripcion.persona.nombre_completo() + ' Motivo: '+ f.cleaned_data['motivo'].upper() +' Autoriza: '+ f.cleaned_data['autoriza'].upper()+' (' +client_address + ')')
                        if EMAIL_ACTIVE:
                            rubro.mail_delrubro(persona.nombre_completo(),f.cleaned_data['motivo'].upper(),f.cleaned_data['autoriza'].upper(),client_address)
                        rubro.delete() # Borra el Rubro
                        if not CENTRO_EXTERNO:
                            inscripcion.actualiza_estadistica() #Actualiza estadistica del estudiante InscripcionEstadistica

                        return HttpResponseRedirect("/finanzas?action=rubros&id="+str(rubro.inscripcion.id))
                else:
                    return HttpResponseRedirect("/finanzas?action=rubros&error=1&id="+str(rubro.inscripcion.id))

        elif action =='consulta_tarjeta':
                result =  {}
                try:
                    result  = {"procesador": [{"id": x.id, "nombre": x.nombre } for x in TipoTarjetaBanco.objects.filter(procesador__id=request.POST['id']).order_by('nombre')]}
                    result['result']  = 'ok'
                    return HttpResponse(json.dumps(result), content_type="application/json")
                except Exception as e:
                    result['result']  = 'bad'
                    return HttpResponse(json.dumps(result), content_type="application/json")

        #OCastillo 07-06-2019 para eliminar recibos de conduccion
        elif  action=='eliminarecibo':
                try:
                    recibo = ReciboPermisoCondu.objects.get(pk=request.POST['id'])
                    #Obtener el ip de donde estan accediendo
                    try:
                        # case server externo
                        client_address = request.META['HTTP_X_FORWARDED_FOR']
                    except:
                        # case localhost o 127.0.0.1
                        client_address = request.META['REMOTE_ADDR']

                    # Log de ELIMINAR RECIBOS VEHICULARES
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(recibo).pk,
                        object_id       = recibo.id,
                        object_repr     = force_str(recibo),
                        action_flag     = DELETION,
                        change_message  = 'Eliminado Recibo Vehicular '+ elimina_tildes(recibo.inscripcion.persona.nombre_completo_inverso()) + ' Motivo: ' + elimina_tildes(request.POST['motivo']) +' (' + client_address + ')' )

                    recibo.delete()
                    return HttpResponse(json.dumps({"result": "ok"}),content_type="application/json")

                except Exception as e:
                    return HttpResponse(json.dumps({"result": "bad","error":str(e)}),content_type="application/json")

        elif action == 'eliminar_recibocaja':
            result = {}
            try:
                #OCastillo 22-oct-2020 cambio de eliminacion a anulacion
                #eliminar = ReciboCajaInstitucion.objects.filter(pk=request.POST['rid'])[:1].get()
                rcaja = ReciboCajaInstitucion.objects.filter(pk=request.POST['rid'])[:1].get()
                rcaja.activo=False
                rcaja.fechaanula=datetime.datetime.now()
                rcaja.usuario=request.user
                rcaja.motivoanulacion=request.POST['motivo']

                mensaje = 'Anulacion Recibo Caja'
                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(rcaja).pk,
                    object_id       = rcaja.id,
                    object_repr     = force_str(rcaja),
                    action_flag     = CHANGE,
                    change_message  = mensaje+' (' + client_address + ')' )
                #eliminar.delete()
                rcaja.save()
                result['result']  = "ok"
                return HttpResponse(json.dumps(result), content_type="application/json")
            except Exception as e:
                result['result']  = str(e)
                return HttpResponse(json.dumps(result), content_type="application/json")

        elif action == 'cambiovalores_recibocaja':
            result = {}
            try:
                #OCastillo 31-enero-2022 cambio en valores de recibos
                rcaja = ReciboCajaInstitucion.objects.filter(pk=request.POST['rid'])[:1].get()
                rcaja.fechacambio=datetime.datetime.now()
                rcaja.usuariocambio=request.user
                rcaja.motivocambio=request.POST['motivocambio']
                mensaje = 'Cambio en valores Recibo Caja'
                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(rcaja).pk,
                    object_id       = rcaja.id,
                    object_repr     = force_str(rcaja),
                    action_flag     = CHANGE,
                    change_message  = mensaje+' (' + client_address + ')' )
                rcaja.save()
                if request.POST['valorinicial']!="":
                    rcaja.valorinicial=request.POST['valorinicial']
                    rcaja.save()

                if request.POST['saldo']!="":
                    rcaja.saldo=request.POST['saldo']
                    rcaja.save()

                result['result']  = "ok"
                return HttpResponse(json.dumps(result), content_type="application/json")
            except Exception as e:
                result['result']  = str(e)
                return HttpResponse(json.dumps(result), content_type="application/json")

        elif action == 'cambiovalorrubro':
            result = {}
            try:
                # OCastillo 09-febrero-2022 cambio en valores de rubros
                rubro = Rubro.objects.filter(pk=request.POST['rid'])[:1].get()
                rubro.valor = Decimal(request.POST['valor']).quantize(Decimal(10) ** -2)
                rubro.save()
                mensaje = 'Cambio en valor de Rubro'
                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                    user_id=request.user.pk,
                    content_type_id=ContentType.objects.get_for_model(rubro).pk,
                    object_id=rubro.id,
                    object_repr=force_str(rubro),
                    action_flag=CHANGE,
                    change_message=mensaje + ' (' + client_address + ')')

                result['result'] = "ok"
                return HttpResponse(json.dumps(result), content_type="application/json")
            except Exception as e:
                result['result'] = str(e)
                return HttpResponse(json.dumps(result), content_type="application/json")

        elif action == 'aplicadescuentodobe':
            result = {}
            try:
                # OCastillo 07-marzo-2023 descuento especial DOBE
                rubro = Rubro.objects.filter(pk=request.POST['rid'])[:1].get()
                estudiante=Inscripcion.objects.get(pk=rubro.inscripcion.id)
                porcentaje=int(request.POST['porcentaje'])
                descuento=Decimal(request.POST['descuento']).quantize(Decimal(10) ** -2)

                descuentodobe= DescuentoDOBE(inscripcion=estudiante,rubro=rubro,valorrubro=rubro.valor,
                                             porcentaje=porcentaje,descuento=descuento,
                                             fecha=datetime.datetime.now(),usuario=request.user)
                descuentodobe.save()
                rubro.valor = Decimal(Decimal(rubro.valor).quantize(Decimal(10) ** -2)-descuento).quantize(Decimal(10) ** -2)
                rubro.save()
                mensaje = 'Descuento DOBE en Rubro'
                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                    user_id=request.user.pk,
                    content_type_id=ContentType.objects.get_for_model(rubro).pk,
                    object_id=rubro.id,
                    object_repr=force_str(rubro),
                    action_flag=CHANGE,
                    change_message=mensaje + ' (' + client_address + ')')

                result['result'] = "ok"
                return HttpResponse(json.dumps(result), content_type="application/json")
            except Exception as e:
                result['result'] = str(e)
                return HttpResponse(json.dumps(result), content_type="application/json")


        if action == 'edit_descuento':
            print(request.POST)
            try:
                inscripcion = Inscripcion.objects.filter(pk=request.POST['id'])[:1].get()
                inscripcion.descuentoporcent=request.POST['descuento']
                mensaje = 'Edicion Porcentaje Descuento'
                inscripcion.save()
                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                user_id         = request.user.pk,
                content_type_id = ContentType.objects.get_for_model(inscripcion).pk,
                object_id       = inscripcion.id,
                object_repr     = force_str(inscripcion),
                action_flag     = CHANGE,
                change_message  = mensaje+' (' + client_address + ')' )

                return HttpResponseRedirect("/finanzas?action=rubros&id="+request.POST['id']+"&ret=1")
            except Exception as ex:
                return HttpResponseRedirect("/finanzas?action=rubros&id="+request.POST['id']+"&ret=1&error=Ocurrio un error, intentelo nuevamente.")

        if action == 'edit_promocion':
            #print(request.POST)
            result = {}
            try:
                inscripcion = Inscripcion.objects.filter(pk=request.POST['id'])[:1].get()
                promocion= Promocion.objects.filter(pk=int(request.POST['promocion']))[:1].get()
                inscripcion.promocion=promocion
                mensaje = 'Cambio de Promocion'
                inscripcion.save()
                inscripcambio = InscripcionMotivoCambioPromocion(inscripcion=inscripcion,promocion=promocion,motivo=request.POST['motivo'].upper(),
                                                                       fecha=datetime.datetime.now(),usuario=request.user)
                inscripcambio.save()
                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                user_id         = request.user.pk,
                content_type_id = ContentType.objects.get_for_model(inscripcion).pk,
                object_id       = inscripcion.id,
                object_repr     = force_str(inscripcion),
                action_flag     = CHANGE,
                change_message  = mensaje+' (' + client_address + ')' )

                result['result']  = "ok"
                return HttpResponse(json.dumps(result), content_type="application/json")
            except Exception as ex:
                result['result']  = "bad"
                return HttpResponse(json.dumps(result), content_type="application/json")

        elif action=='addrecibo_cab':
            try:
                num_recibo = CuotaCAB.objects.all().exclude(numero_recibo=None)
                if not num_recibo:
                   num_recibo = 0
                else:
                   recibo_permiso = CuotaCAB.objects.all().order_by('-numero_recibo').exclude(numero_recibo=None)[:1].get()
                   num_recibo = recibo_permiso.numero_recibo

                i = Inscripcion.objects.get(pk=request.POST['id'])
                banco = None

                if request.POST['bancotarjetaperm'] != '':
                    banco = request.POST['bancotarjetaperm']
                if request.POST['bancochequeperm'] != '':
                    banco = request.POST['bancochequeperm']

                cuotacab = CuotaCAB.objects.get(pk=request.POST['idcuota'])
                cuotacab.numero_recibo = num_recibo + 1
                cuotacab.fecha_recibo = datetime.datetime.now()
                cuotacab.usuario = request.user
                cuotacab.formadepago_id = request.POST['formadepagoperm']
                cuotacab.numerocheq = request.POST['numerocheq']
                cuotacab.emite = request.POST['emiteperm']
                cuotacab.referencia = request.POST['referenciaperm']
                cuotacab.tipotarje_id = request.POST['tipoperm']
                cuotacab.poseedor = request.POST['poseedorperm']
                cuotacab.procesadorpago_id = request.POST['procesadorpagoperm']
                cuotacab.banco_id = banco
                cuotacab.referenciatransferencia = request.POST['referenciatransferenciaperm']
                cuotacab.cuentabanco_id = request.POST['cuentabancoperm']
                cuotacab.cancelado = True
                cuotacab.fechapago = datetime.datetime.now()
                cuotacab.save()

                if int(request.POST['formadepagoperm'])==FORMA_PAGO_RECIBOCAJAINSTITUCION:
                    recibocaja=ReciboCajaInstitucion.objects.filter(inscripcion=i,activo=True)[:1].get()
                    if recibocaja.saldo>=Decimal(cuotacab.valor):
                        tp = PagoReciboCajaInstitucion(recibocaja=recibocaja,
                                                       valor = float(Decimal(cuotacab.valor)),
                                                       fecha = datetime.datetime.today().date())
                        tp.save()
                        rc = tp.recibocaja
                        rc.saldo = round(rc.saldo - float(Decimal(cuotacab.valor)),2)
                        rc.save()
                    else:
                        tp = PagoReciboCajaInstitucion(recibocaja=recibocaja,
                                                        valor = recibocaja.saldo,
                                                        fecha = datetime.datetime.today().date())
                        tp.save()
                        rc = tp.recibocaja
                        rc.saldo = round(rc.saldo - float(Decimal(recibocaja.saldo)),2)
                        rc.save()

                if request.POST['fechacobroperm']:
                    cuotacab.fechacobro = request.POST['fechacobroperm']
                    cuotacab.save()
                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de ADICIONAR RECIBO PERMISO CONDUCCION
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(cuotacab).pk,
                    object_id       = cuotacab.id,
                    object_repr     = force_str(cuotacab),
                    action_flag     = ADDITION,
                    change_message  = 'Genera Recibo CAB (' + client_address + ')' )

                return HttpResponse(json.dumps({"result":"ok","id":str(cuotacab.id)}),content_type="application/json")
            except Exception as ex:
                print(ex)
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

        elif action == 'obtener_nc':
            inscripcion = Rubro.objects.get(pk=request.POST['id']).inscripcion
            nca = NotaCreditoInstitucion.objects.filter(tipo__id=1, inscripcion=inscripcion).order_by('fecha') #solo para nca

            lista_nc = [
                {
                    'id': x.id,
                    'value': str(x.fecha) + ' | ' + x.numero
                } for x in nca
            ]
            return HttpResponse(json.dumps({"result": "ok", "ncList": lista_nc}), content_type="application/json")

        elif action == 'add_nc':
            try:
                rubro = Rubro.objects.get(pk=request.POST['id'])
                nc = NotaCreditoInstitucion.objects.get(pk=request.POST['nc'])
                rubro.nc = nc.id
                rubro.save()

                # Obtain client ip address
                client_address = ip_client_address(request)

                # Log de ADICIONAR NC A RUBRO
                LogEntry.objects.log_action(
                    user_id=request.user.pk,
                    content_type_id=ContentType.objects.get_for_model(rubro).pk,
                    object_id=rubro.id,
                    object_repr=force_str(rubro),
                    action_flag=CHANGE,
                    change_message='Add NC a rubro (' + client_address + ')')
                return HttpResponse(json.dumps({"result": "ok"}), content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({"result": "bad", "mensaje": str(e)}), content_type="application/json")

        return HttpResponseRedirect("/finanzas")
    else:
        data = {'title': 'Consulta de Finanzas'}
        addUserData(request,data)
        if 'action' in request.GET:

            action = request.GET['action']
            if action=='segmatriculas':
                inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                data['inscripcion'] = inscripcion
                data['matriculas'] = [x for x in Matricula.objects.filter(inscripcion=inscripcion) if not x.ya_cobrada()]
                data['hoy'] = datetime.datetime.today().date()
                return render(request ,"finanzas/segmatriculasbs.html" ,  data)
            if action=='chequepro':
                if Inscripcion.objects.filter(pk=request.GET['id']).exists():
                    inscripcion=Inscripcion.objects.filter(pk=request.GET['id'])[:1].get()
                    data['form'] = InscripcionFlaForm()
                    data['inscripcion'] = inscripcion
                    return render(request ,"finanzas/chequepro.html" ,  data)
            if action=='deletedescuento':
                if Rubro.objects.filter(pk=request.GET['id']).exists():
                    rubro=Rubro.objects.filter(pk=request.GET['id'])[:1].get()
                    data['form'] = EliminaRubroForm()
                    data['rubro'] = rubro
                    return render(request ,"finanzas/deletedescuento.html" ,  data)
            elif action=='delrubro':
                data['title'] = 'Eliminar de Rubro del Estudiante'
                rubro = Rubro.objects.get(pk=request.GET['id'])
                initial = model_to_dict(rubro)
                data['form'] = EliminaRubroForm(initial=initial)
                data['rubro'] = rubro
                if ReferidosInscripcion.objects.filter(inscripcionref=rubro.inscripcion).exists():
                    if RubroMatricula.objects.filter(rubro=rubro,matricula__nivel__nivelmalla__id=NIVEL_MALLA_UNO).exists():
                        # if rubro.es_matricula():
                            return HttpResponseRedirect("/finanzas?action=rubros&errorreferido=NO PUEDE ELIMINAR EL RUBRO DE MATRICULA DE UNA PERSONA REFERIDA&id="+str(rubro.inscripcion.id))
                return render(request ,"finanzas/eliminarubro.html" ,  data)
            elif action=='editrubro':
                data['title'] = 'Editar Rubro del Estudiante'
                rubro = Rubro.objects.get(pk=request.GET['id'])
                initial = model_to_dict(rubro)
                data['form'] = RubroForm(initial=initial)
                data['rubro'] = rubro
                return render(request ,"finanzas/editarrubrobs.html" ,  data)

            elif action=='editfecha':
                data['title'] = 'Editar Fecha de Rubro del Estudiante'
                rubro = Rubro.objects.get(pk=request.GET['id'])
                initial = model_to_dict(rubro)
                data['form'] = RubroFechaForm(initial=initial)
                data['rubro'] = rubro
                return render(request ,"finanzas/editarfecha.html" ,  data)

            elif action=='inforubro':
                try:
                    rubro = Rubro.objects.get(pk=request.GET['rid'])
                    datos = {"result": "ok"}
                    caja = request.session['persona'].lugarrecaudacion_set.get()
                    sesion_caja = caja.sesion_caja()
                    datos['rubroid'] = rubro.id
                    datos['factura'] = sesion_caja.facturatermina
                    datos['valor'] = rubro.adeudado()
                    datos['ruc'] = rubro.inscripcion.persona.cedula
                    datos['nombre'] = rubro.inscripcion.persona.nombre_completo()
                    datos['direccion'] = rubro.inscripcion.persona.direccion
                    datos['telefono'] = rubro.inscripcion.persona.telefono
                    datos['rubro'] = rubro.nombre()
                    datos['fecharubro'] = rubro.fechavence.strftime("%d-%m-%Y")
                    datos['vencehoy'] = rubro.fechavence==datetime.datetime.now().date()
                    datos['tienechequeprotestado'] = rubro.inscripcion.tiene_cheque_protestado()
                    return HttpResponse(json.dumps(datos),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad", "error": str(ex)}),content_type="application/json")

            elif action=='infoespecie':
                try:
                    inscripcion = Inscripcion.objects.get(pk=request.GET['iid'])
                    datos = {"result": "ok"}
                    caja = request.session['persona'].lugarrecaudacion_set.get()
                    sesion_caja = caja.sesion_caja()
                    datos['factura'] = sesion_caja.facturatermina
                    datos['ruc'] = inscripcion.persona.cedula
                    datos['nombre'] = inscripcion.persona.nombre_completo()
                    datos['direccion'] = inscripcion.persona.direccion
                    datos['telefono'] = inscripcion.persona.telefono

                    return HttpResponse(json.dumps(datos),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad", "error": str(ex)}),content_type="application/json")

            elif action=='inforuc':
                ruc = request.GET['ruc']
                if Persona.objects.filter(cedula=ruc).exists():
                    persona = Persona.objects.filter(cedula=ruc)[:1].get()
                    datos = {"result": "ok"}
                    datos['nombre'] = persona.nombre_completo()
                    # Completar datos factura si no existe en Persona buscarlo en ClienteFactura
                    if not persona.direccion and ClienteFactura.objects.filter(ruc=ruc).exists():
                        cliente = ClienteFactura.objects.filter(ruc=ruc)[:1].get()
                        persona.direccion = cliente.direccion
                        persona.save()
                    if not persona.telefono and ClienteFactura.objects.filter(ruc=ruc).exists():
                        cliente = ClienteFactura.objects.filter(ruc=ruc)[:1].get()
                        persona.telefono = cliente.telefono
                        persona.save()
                    if not persona.emailinst and ClienteFactura.objects.filter(ruc=ruc).exists():
                        cliente = ClienteFactura.objects.filter(ruc=ruc)[:1].get()
                        persona.emailinst = cliente.correo
                        persona.save()
                    datos['direccion'] = persona.direccion
                    datos['telefono'] = persona.telefono
                    datos['correo'] = persona.emailinst
                    return HttpResponse(json.dumps(datos),content_type="application/json")
                elif Persona.objects.filter(pasaporte=ruc).exists():
                    persona = Persona.objects.filter(pasaporte=ruc)[:1].get()
                    datos = {"result": "ok"}
                    datos['nombre'] = persona.nombre_completo()
                    # Completar datos factura si no existe en Persona buscarlo en ClienteFactura
                    if not persona.direccion and ClienteFactura.objects.filter(ruc=ruc).exists():
                        cliente = ClienteFactura.objects.filter(ruc=ruc)[:1].get()
                        persona.direccion = cliente.direccion
                        persona.save()
                    if not persona.telefono and ClienteFactura.objects.filter(ruc=ruc).exists():
                        cliente = ClienteFactura.objects.filter(ruc=ruc)[:1].get()
                        persona.telefono = cliente.telefono
                        persona.save()
                    if not persona.emailinst and ClienteFactura.objects.filter(ruc=ruc).exists():
                        cliente = ClienteFactura.objects.filter(ruc=ruc)[:1].get()
                        persona.emailinst = cliente.correo
                        persona.save()
                    datos['direccion'] = persona.direccion
                    datos['telefono'] = persona.telefono
                    datos['correo'] = persona.emailinst
                    return HttpResponse(json.dumps(datos),content_type="application/json")
                elif ClienteFactura.objects.filter(ruc=ruc).exists():
                    cliente = ClienteFactura.objects.filter(ruc=ruc)[:1].get()
                    datos = {"result": "ok"}
                    datos['nombre'] = cliente.nombre
                    datos['direccion'] = cliente.direccion
                    datos['telefono'] = cliente.telefono
                    datos['correo'] = cliente.correo
                    return HttpResponse(json.dumps(datos),content_type="application/json")
                else:
                    datos = {"result": "no"}
                    return HttpResponse(json.dumps(datos),content_type="application/json")
            elif action=='segmaterias':
                try:
                    inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                    data['inscripcion'] = inscripcion
                    data['materiasasignadas'] = [x for x in MateriaAsignada.objects.filter(matricula__inscripcion=inscripcion) if not x.ya_cobrada()]
                    data['hoy'] = datetime.datetime.today().date()
                    return render(request ,"finanzas/segmateriasbs.html" ,  data)
                except Exception as ex:
                    return HttpResponseRedirect("/")
            elif action=='segotros':
                inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                data['inscripcion'] = inscripcion
                data['tiposotros'] = TipoOtroRubro.objects.all()
                data['hoy'] = datetime.datetime.today().date()
                return render(request ,"finanzas/segotrosbs.html" ,  data)

            # Adicionar Recibos de Caja Institucionales
            elif action=='addrecibocaja':
                data['title'] = 'Adicionar Recibo de Caja Institucional'
                inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                data['inscripcion'] = inscripcion
                data['form'] = ReciboCajaInstitucionForm()
                return render(request ,"finanzas/addrecibo.html" ,  data)

            #Notas de Credito
            elif action=='addnc':
                data['title'] = 'Adicionar Nota de Credito a Estudiantes'
                inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                data['inscripcion'] = inscripcion
                data['form'] = NotaCreditoForm(initial={'fecha': datetime.datetime.now()})
                return render(request ,"finanzas/addncbs.html" ,  data)

            #OCastillo 07-06-2019 para eliminar recibos de conduccion
            elif action=='eliminarecibo':
                recibos = ReciboPermisoCondu.objects.filter(inscripcion__id=request.GET['id'])
                data['permisos'] = recibos
                return render(request ,"finanzas/permisos.html" ,  data)


            elif action=='rubros':
                try:
                    nivel = None
                    ret = None

                    if 'errorreferido' in request.GET:
                        data['errorreferido'] = request.GET['errorreferido']

                    if 'errorsolicitud' in request.GET:
                        data['errorsolicitud'] = request.GET['errorsolicitud']

                    if 'ret' in request.GET:
                        ret = request.GET['ret']

                    if 'error2' in request.GET:
                        data['error2'] = request.GET['error2']


                    if 'solicitud' in request.GET:
                        solicitud = SolicitudSecretariaDocente.objects.filter(id=request.GET['solicitud'])[:1].get()
                        data['solicitud']  = solicitud
                        data['fechasol'] = solicitud.datosaprobacion().fechadeposito
                    else:
                        if 'pagowestercaja' in request.GET:
                            pagowestercaja = PagoWester.objects.filter(pk=request.GET['pagowestercaja'])[:1].get()
                            data['fechasol'] = pagowestercaja.fechapago
                            data['pagowestercaja']=pagowestercaja
                        else:
                            data['fechasol'] = 'None'

                    if 'info' in request.GET:
                        data['info'] = request.GET['info']

                    if 'error' in request.GET:
                        data['err'] = 'EL RUBRO TIENE PAGO RELACIONADOS'

                    if 'errordescuento' in request.GET:
                        data['err'] = request.GET['errordescuento']

                    if 'errorcheque' in request.GET:
                        data['err']=  request.GET['errorcheque']

                    if 'nivel' in request.GET:
                        nivel = request.GET['nivel']
                    # Listar los rubros de pago de un alumno
                    if Inscripcion.objects.filter(pk=request.GET['id']).exists():
                        inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                        if int(request.GET['id']) == CONSUMIDOR_FINAL:
                            if INSCRIPCION_CONDUCCION:
                                rubros = Rubro.objects.filter(inscripcion=inscripcion).order_by('-id','cancelado','fechavence')[:20]
                            else:
                                for r in Rubro.objects.filter(inscripcion=inscripcion).order_by('cancelado','fechavence'):
                                    if r.puede_eliminarse() and r.vencido():
                                         if RubroReceta.objects.filter(rubrootro__rubro = r).exists():
                                             receta = RubroReceta.objects.filter(rubrootro__rubro = r)[:1].get()
                                             for rec in RecetaVisitaBox.objects.filter(visita=receta.detallebox):
                                                 rec.delete()
                                         if DEFAULT_PASSWORD == 'itb':
                                            r.delete()
                                if 'desc' in request.GET:
                                    r = RubroOtro.objects.filter(descripcion__contains=request.GET['desc']).values('rubro')
                                    rubros = Rubro.objects.filter(id__in = r)
                                    data['desc']=request.GET['desc']
                                else:
                                    rubros = Rubro.objects.filter(inscripcion=inscripcion,cancelado=False).order_by('cancelado','fechavence')
                        else:
                            # if DescuentoSeguimiento.objects.filter(seguimiento__inscripcion=inscripcion).exists():
                            #     descuento = DescuentoSeguimiento.objects.filter(seguimiento__inscripcion=inscripcion)[:1].get()
                            #     for rub in RubroSeguimiento.objects.filter(seguimiento=descuento.seguimiento,rubro__aplicadod=True):
                            #         rub.rubro.valor = Decimal(rub.rubro.valor) + rub.valordesc
                            #         rub.rubro.aplicadod = False
                            #         rub.rubro.save()
                            #         rub.save()
                            rubros = Rubro.objects.filter(inscripcion=inscripcion).order_by('cancelado','fechavence')
                        for r in Rubro.objects.filter(inscripcion=inscripcion,cancelado=False):
                            if r.verifica_adeudado()==0:
                                r.cancelado = True
                            r.save()
                        data['title'] = 'Listado de Rubros del Alumno: '+str(inscripcion.persona)
                        # rubros = Rubro.objects.filter(inscripcion=inscripcion).order_by('cancelado','fechavence')
                        data['inscripcion'] = inscripcion
                        paging = Paginator(rubros, 50)
                        p=1
                        try:
                            if 'page' in request.GET:
                                p = int(request.GET['page'])
                            page = paging.page(p)
                        except:
                            page = paging.page(1)
                        data['paging'] = paging
                        data['page'] = page
                        data['rubros'] = rubros
                        data['hoy'] = datetime.datetime.today().date()
                        data['nivel'] = nivel if nivel else ""
                        data['ret'] = ret if ret else ""
                        data['HABILITA_APLICA_DESCUE'] = HABILITA_APLICA_DESCUE
                        data['reciboscaja'] = ReciboCajaInstitucion.objects.filter(inscripcion=inscripcion).order_by('fecha')
                        if FACTURACION_ELECTRONICA:
                            data['notascredito'] = NotaCreditoInstitucion.objects.filter(beneficiario=inscripcion, cancelada=False, anulada = False).order_by('fecha')
                        else:
                            data['notascredito'] = NotaCreditoInstitucion.objects.filter(beneficiario=inscripcion, cancelada=False, anulada = False).order_by('fecha')
                        data['puede_pagar'] = data['persona'].puede_recibir_pagos()
                        # OCU 30-oct-2015 para excluir especie Materias Aprobadas a estudiantes matriculados en 6to Nivel, Seminario y Graduacion
                        # if Matricula.objects.filter(inscripcion=inscripcion,nivel__cerrado=False,nivel__nivelmalla__in=EXCLUYE_NIVEL).exists():
                        #     data['especies'] = TipoEspecieValorada.objects.filter(activa=True).exclude(id=4)
                        # else:
                        data['especies'] = TipoEspecieValorada.objects.filter(id=ESPECIE_TRAMITES_VARIOS,activa=True)

                        data['rubrosadiconales'] = RubroAdicional.objects.filter(activo=True)
                        data['tiene_deuda_externa'] = inscripcion.tiene_deuda_externa() if inscripcion.tiene_deuda_externa() else ""
                        data['tiene_nota_debito'] = RubroNotaDebito.objects.filter(rubro__inscripcion=inscripcion, rubro__cancelado=False).exists()
                        data['pagowester'] = PagoWester.objects.filter(inscripcion=inscripcion,factura=None)
                        # for rp in RegistroWester.objects.filter(cedula=inscripcion.persona.cedula,facturado=False).distinct('codigo').values('codigo'):
                        if inscripcion.persona.cedula:
                            data['registrowester'] = RegistroWester.objects.filter(cedula=inscripcion.persona.cedula,facturado=False).distinct('codigo').values('codigo')
                        else:
                            data['registrowester'] = RegistroWester.objects.filter(cedula=inscripcion.persona.pasaporte,facturado=False).distinct('codigo').values('codigo')
                        #OCastillo 17-04-2023 si estudiante tiene marca de plagio no puede realizar pagos con tarjetas
                        if inscripcion.plagiotarjeta:
                            data['plagio']=True
                        else:
                            data['plagio']=False

                        data['tipo_ayuda_financiera'] = TIPO_AYUDA_FINANCIERA
                        data['tipo_beca_senescyt'] = TIPO_BECA_SENESCYT
                        data['centroexterno'] = CENTRO_EXTERNO
                        data['extra'] = 1
                        data['lugarrecaudacion'] = ''
                        if  request.session['persona'].lugarrecaudacion_set.filter(activa=True).exists():
                            data['lugarrecaudacion'] = request.session['persona'].lugarrecaudacion_set.filter(activa=True)[:1].get()
                        data['client_address'] = ip_client_address(request)
                        data['FACTURACION_ELECTRONICA'] = FACTURACION_ELECTRONICA
                        data['VALIDA_IP_CAJA'] = VALIDA_IP_CAJA
                        if inscripcion.id == CONSUMIDOR_FINAL:
                            data['CONSUMIDOR_FINAL'] = CONSUMIDOR_FINAL
                        data['VALIDAR_PAGO_RUBRO'] = VALIDAR_PAGO_RUBRO
                        data['INSCRIPCION_CONDUCCION'] = INSCRIPCION_CONDUCCION
                        data['ID_TIPO_ESPECIE_REG_NOTA'] = ID_TIPO_ESPECIE_REG_NOTA
                        data['VALIDA_DEUDA_EXAM_ASIST'] = VALIDA_DEUDA_EXAM_ASIST
                        data['DEFAULT_PASSWORD'] = DEFAULT_PASSWORD
                        data['verifica_total_pagado'] = inscripcion.verifica_total_pagado()
                        data['verifica_adeudado'] = inscripcion.verifica_adeudado()
                        if DescuentoSeguimiento.objects.filter(seguimiento__inscripcion=inscripcion,pagado=False).exists():
                            detdescuento = DescuentoSeguimiento.objects.filter(seguimiento__inscripcion=inscripcion,pagado=False)[:1].get()
                            data['detdescuento'] = detdescuento

                        if DEFAULT_PASSWORD == 'itb':
                            if inscripcion.matricula():
                                tipoespecie = TipoEspecieValorada.objects.get(id=ID_TIPO_ESPECIE_REG_NOTA)
                                fechamax = datetime.datetime.now() - timedelta(days=DIAS_ESPECIE)
                                if RubroEspecieValorada.objects.filter(tipoespecie=tipoespecie,rubro__inscripcion=inscripcion, aplicada=False,fecha__gte=fechamax).exclude(materia=None).exists():
                                    materiaid = RubroEspecieValorada.objects.filter(tipoespecie=tipoespecie,rubro__inscripcion=inscripcion,
                                                                                   aplicada=False,fecha__gte=fechamax).distinct('materia').values('materia')

                                    data['materias'] = inscripcion.matricula().materia_asignada().filter().exclude(id__in=materiaid)
                                else:
                                    data['materias'] = inscripcion.matricula().materia_asignada().filter()

                            # if inscripcion.carrera.nombre == 'CONGRESO DE PEDAGOGIA':
                            #     errores =[]
                            #     try:
                            #         datos = requests.post('http://api.pedagogia.edu.ec',{'action': 'ci_comprobante',"pagado":"0", 'codigo':inscripcion.grupo().nombre,"ci":str(inscripcion.persona.cedula)})
                            #         if datos.status_code==200:
                            #             grupo=None
                            #             fecha = datetime.datetime.now().date().year
                            #             d = datos.json()['response'][0]
                            #             if Grupo.objects.filter(nombre=d['codigo'].upper()).exists():
                            #                 grupo= Grupo.objects.filter(nombre=d['codigo'].upper())[:1].get()
                            #             try:
                            #                 valor = Decimal(d['valor'])
                            #             except:
                            #                 valor = None
                            #             if grupo :
                            #                 if inscripcion.grupo() == grupo:
                            #                     inscripcion =inscripcion
                            #                 # if Inscripcion.objects.filter(persona__cedula=str(inscripcion.persona.cedula)).exists():
                            #                 #     inscripcion =  Inscripcion.objects.filter(persona__cedula=str(inscripcion.persona.cedula),carrera__grupo=grupo)[:1].get()
                            #                     if not PagoExternoPedagogia.objects.filter(inscripcion=inscripcion,grupo=grupo).exists():
                            #                         pagoped = PagoExternoPedagogia(inscripcion=inscripcion,
                            #                                                        grupo=grupo,
                            #                                                        nombresruc = d['fac_nombre'],
                            #                                                         documento = d['comprobante'],
                            #                                                         identificacionruc =  d['fac_ci'],
                            #                                                         emailruc =  d['fac_email'],
                            #                                                         fonoruc = d['telefono'],
                            #                                                         fecha=datetime.datetime.now().date(),
                            #                                                         direccionruc = d['fac_direcion'])
                            #                         pagoped.save()
                            #                     else:
                            #                         pagoped = PagoExternoPedagogia.objects.filter(inscripcion=inscripcion,grupo=grupo)[:1].get()
                            #                         pagoped.nombresruc = d['fac_nombre']
                            #                         pagoped.documento = d['comprobante']
                            #                         pagoped.identificacionruc =  d['fac_ci']
                            #                         pagoped.emailruc =  d['fac_email']
                            #                         pagoped.fonoruc = d['telefono']
                            #                         pagoped.direccionruc = d['fac_direcion']
                            #                         pagoped.save()
                            #                     data['pagoped']=pagoped
                            #                     if valor:
                            #                         pagoped.valor=valor
                            #                         pagoped.save()
                            #                     if inscripcion.matricula():
                            #                         if RubroMatricula.objects.filter(matricula = inscripcion.matricula(),matricula__fecha__year=fecha).exists():
                            #                             rubro = RubroMatricula.objects.filter(matricula = inscripcion.matricula(),matricula__fecha__year=fecha)[:1].get()
                            #                             if not rubro.rubro.cancelado:
                            #                                 pagoped.rubro = rubro.rubro
                            #                                 pagoped.save()
                            #     except Exception as e:
                            #         pass
                            #         errores.append((e,elimina_tildes(inscripcion.persona.nombre_completo())))
                            #     if errores:
                            #         from sga.pre_inscripciones import email_error_congreso
                            #         email_error_congreso(errores,'FACTURACION')
                            try:
                                if inscripcion.persona.extranjero:
                                    ced = inscripcion.persona.pasaporte
                                    op=0
                                else:
                                    op=1
                                    ced = inscripcion.persona.cedula

                                # datos = requests.get('https://sga.buckcenter.com.ec/api',params={'a': 'datos_finanzas', 'ced':ced,'op': op })
                                # if datos.status_code==200:
                                #     data['otrosrubros']=datos.json()['rubros']
                            except Exception as e:
                                pass
                            data['motivoanulacionform'] =MotivoAnulacionForm()
                            data['cambiopromocionform'] =CambioPromocionForm()
                            data['autorizarwesterform'] =AutorizarWesterForm(initial={'fecha': datetime.datetime.now()})
                            data['usuario']=request.user
                            data['cambiovaloresrecibos'] = CambioValoresRecibosForm()
                            data['cambiovaloresrubros'] = CambioValorRubroForm()
                            if CuotaCAB.objects.filter(rubro__inscripcion=inscripcion).exists():
                                cuotas_cab = CuotaCAB.objects.filter(rubro__inscripcion=inscripcion).order_by('fechavence')
                                data['cuotas_cab'] = cuotas_cab
                                data['form1'] = FormaPagoPermForm(initial={'fechacobroperm': datetime.datetime.now()})
                                data['pago_efectivo_id'] = FORMA_PAGO_EFECTIVO
                                data['pago_electronico_id'] = FORMA_PAGO_ELECTRONICO
                                data['pago_tarjeta_id'] = FORMA_PAGO_TARJETA
                                data['pago_tarjetadeb_id'] = FORMA_PAGO_TARJETA_DEB
                                data['pago_cheque_id'] = FORMA_PAGO_CHEQUE
                                data['pago_deposito_id'] = FORMA_PAGO_DEPOSITO
                                data['pago_transferencia_id'] = FORMA_PAGO_TRANSFERENCIA
                                data['pago_nota_credito_id'] = FORMA_PAGO_NOTA_CREDITO
                                data['pago_recibo_caja_id'] = FORMA_PAGO_RECIBOCAJAINSTITUCION
                                data['pago_retencion_id'] = FORMA_PAGO_RETENCION
                                data['pago_wester_id'] = FORMA_PAGO_WESTER
                                try:
                                    data['caja'] = LugarRecaudacion.objects.filter(persona=data['persona'],activa=True)[:1].get()
                                    if SesionCaja.objects.filter(caja=data['caja'], abierta=True).exists():
                                        data['sesion'] = SesionCaja.objects.get(caja=data['caja'], abierta=True)
                                except:
                                    pass
                            #OCastillo 28-02-2023 descuento DOBE
                            formdobe = DescuentoDobeForm()
                            data['formdobe'] = formdobe
                            data['ID_TIPORUBRO_FRAUDE'] = TIPO_OTRO_FRAUDE
                        return render(request ,"finanzas/rubrosbs.html" ,  data)
                except Exception as e:
                    print(e)

            elif action=='tricorubros':
                from clinicaestetica.models import FichaMedica
                if 'info' in request.GET:
                    data['info'] = request.GET['info']

                if 'error' in request.GET:
                    data['err'] = 'EL RUBRO TIENE PAGO RELACIONADOS'

                # Listar los rubros de pago de un alumno
                if FichaMedica.objects.filter(pk=request.GET['id']).exists():
                    fichamedica = FichaMedica.objects.get(pk=request.GET['id'])
                    rubros = Rubro.objects.filter(fichamedica=fichamedica).order_by('cancelado','fechavence')
                    for r in Rubro.objects.filter(fichamedica=fichamedica,cancelado=False):
                        # if r.adeudado()==0:
                        #     r.cancelado = True
                        r.save()
                    data['title'] = 'Listado de Rubros del Paciente: '+str(fichamedica)
                    # rubros = Rubro.objects.filter(inscripcion=inscripcion).order_by('cancelado','fechavence')
                    data['fichamedica'] = fichamedica
                    paging = Paginator(rubros, 50)
                    p=1
                    try:
                        if 'page' in request.GET:
                            p = int(request.GET['page'])
                        page = paging.page(p)
                    except:
                        page = paging.page(1)
                    data['paging'] = paging
                    data['page'] = page
                    data['rubros'] = rubros
                    data['hoy'] = datetime.datetime.today().date()
                    if FACTURACION_ELECTRONICA:
                        data['notascredito'] = NotaCreditoInstitucion.objects.filter(fichamedica=fichamedica, cancelada=False, anulada = False).order_by('fecha')

                    data['lugarrecaudacion'] = ''
                    if  request.session['persona'].lugarrecaudacion_set.filter(activa=True).exists():
                        data['lugarrecaudacion'] = request.session['persona'].lugarrecaudacion_set.filter(activa=True)[:1].get()
                    data['client_address'] = ip_client_address(request)
                    data['FACTURACION_ELECTRONICA'] = FACTURACION_ELECTRONICA
                    data['VALIDA_IP_CAJA'] = VALIDA_IP_CAJA
                    data['puede_pagar'] = data['persona'].puede_recibir_pagos()
                    return render(request ,"finanzas/tricorubros.html" ,  data)

            elif action=='facturarexterno':
                cliente=''
                externo = RegistroExterno.objects.filter(pk=request.GET['id'])[:1].get()
                inscripcion =Inscripcion.objects.filter(id = CONSUMIDOR_FINAL)[:1].get()
                if not externo.rubro:
                    tipootro = TipoOtroRubro.objects.get(pk=18)

                    rubro = Rubro(fecha=datetime.datetime.now(), valor=float(externo.valor),
                                  inscripcion=inscripcion, cancelado=False, fechavence=datetime.datetime.now().date())
                    rubro.save()
                    rubrootro = RubroOtro(rubro=rubro, tipo=tipootro, descripcion=externo.titulo + " - " + externo.identificacion )
                    rubrootro.save()
                    externo.rubro = rubro
                    externo.save()
                rubros = Rubro.objects.filter(pk=externo.rubro.id)
                data['title'] = 'Pago de Rubros del Alumno: '+str(inscripcion.persona)
                data['inscripcion'] = inscripcion
                data['rubros'] = rubros
                data['puede_pagar'] = data['persona'].puede_recibir_pagos()
                # Formulario de Pago
                data['form'] = FormaPagoForm(initial={'fechacobro': datetime.datetime.now()})
                personausuario = Persona.objects.filter(usuario=request.user)[:1].get()
                data['form'].para_inscripcion(inscripcion,personausuario)
                # data['form'].notacredito_inscripcion(inscripcion)
                data['pago_efectivo_id'] = FORMA_PAGO_EFECTIVO
                data['pago_electronico_id'] = FORMA_PAGO_ELECTRONICO
                data['pago_tarjeta_id'] = FORMA_PAGO_TARJETA
                data['pago_tarjetadeb_id'] = FORMA_PAGO_TARJETA_DEB
                data['pago_cheque_id'] = FORMA_PAGO_CHEQUE
                data['pago_deposito_id'] = FORMA_PAGO_DEPOSITO
                data['pago_transferencia_id'] = FORMA_PAGO_TRANSFERENCIA
                data['pago_nota_credito_id'] = FORMA_PAGO_NOTA_CREDITO
                data['pago_recibo_caja_id'] = FORMA_PAGO_RECIBOCAJAINSTITUCION
                data['pago_retencion_id'] = FORMA_PAGO_RETENCION
                data['pago_wester_id'] = FORMA_PAGO_WESTER
                # data['tiene_cheque_protestado'] = False
                data['externo'] = externo
                data['tiene_cheque_protestado'] = inscripcion.tiene_cheque_protestado()

                caja = request.session['persona'].lugarrecaudacion_set.filter(activa=True)[:1].get()
                lugar = LugarRecaudacion.objects.filter(persona=request.session['persona'],activa=True)[:1].get()
                sesion_caja = caja.sesion_caja()
                if FACTURACION_ELECTRONICA:
                    if lugar.numerofact == None:
                        data['factura'] = sesion_caja.facturatermina
                    else:
                        data['factura'] = lugar.numerofact
                else:
                    data['factura'] = sesion_caja.facturatermina
                if externo.identificacion :
                    data['facturaruc'] = externo.identificacion
                if ClienteFactura.objects.filter(ruc=data['facturaruc']).exists():
                    cliente = ClienteFactura.objects.filter(ruc=data['facturaruc'])[:1].get()
                data['facturanombre'] = externo.apellidos + " " +  externo.nombres
                if externo.direccion:
                    data['facturadireccion'] = externo.direccion
                else:
                    if cliente:
                        data['facturadireccion']= cliente.direccion
                if externo.fono:
                    data['facturatelefono'] = externo.fono
                else:
                    if cliente:
                        data['facturatelefono']= cliente.telefono
                if externo.email:
                    data['facturacorreo'] = externo.email
                data['FACTURACION_ELECTRONICA'] = FACTURACION_ELECTRONICA
                data['totalapagar'] = sum([x.aplicadescuento() if HABILITA_APLICA_DESCUE else x.adeudado() for x in rubros])

                if sum([x.es_notadebito() for x in rubros])==rubros.count():
                    data['tiene_nota_debito'] = True

                data['codigo']=""
                if externo.cuenta:
                    data['fp']= FORMA_PAGO_DEPOSITO
                    data['pagowes']=1
                data['valor']= externo.valor
                data['HABILITA_APLICA_DESCUE'] = HABILITA_APLICA_DESCUE
                data['tiene20desc'] =False
                data['tipo_beca_senescyt'] = TIPO_BECA_SENESCYT
                if RubroSeguimiento.objects.filter(rubro__id__in=rubros, estado=True, aplicadescuentocategoria=True).exists() or RubroSeguimiento.objects.filter(rubro__id__in=rubros, estado=True, aprobardescuentoadd=True).exists():
                    data['descuento_cobranza'] = True
                return render(request ,"finanzas/pagarbs.html" ,  data)

            elif action=='pagar':
                try:
                    cliente=''
                    ids = request.GET['ids'].split(",")
                    rubros = Rubro.objects.filter(id__in=ids).order_by('fechavence')
                    inscripcion = rubros[0].inscripcion

                    data['title'] = 'Pago de Rubros del Alumno: '+str(inscripcion.persona)
                    data['inscripcion'] = inscripcion
                    data['rubros'] = rubros
                    data['puede_pagar'] = data['persona'].puede_recibir_pagos()
                    # Formulario de Pago
                    data['form'] = FormaPagoForm(initial={'fechacobro': datetime.datetime.now()})

                    #OCastillo 17-04-2023 si estudiante tiene marca de plagio no puede realizar pagos con tarjetas
                    #OCastillo 28-04-2023 se permite a estudiante que tiene marca de plagio realizar pagos con tarjetas
                    if inscripcion.plagiotarjeta:
                        data['plagio']=False
                    else:
                        data['plagio']=False
                    personausuario = Persona.objects.filter(usuario=request.user)[:1].get()
                    if 'solicitud' in request.GET:
                        solicitud = SolicitudSecretariaDocente.objects.filter(id=request.GET['solicitud'])[:1].get()
                        #OCastillo 16-01-2023 validacion proceso pago por medio de solicitud que pertenezca a mismo estudiante
                        if inscripcion!= solicitud.inscripcion():
                            return HttpResponseRedirect("/finanzas?action=rubros&errorsolicitud=NO PUEDE PROCESAR SOLICITUD A OTRO ESTUDIANTE&id="+str(inscripcion.id))
                        data['form'].solicitud(solicitud.datosaprobacion().id)
                    else:
                        if 'pagowestercaja' in request.GET:
                            pagowestercaja = PagoWester.objects.filter(pk=request.GET['pagowestercaja'])[:1].get()
                            data['form'].westercaja(pagowestercaja.id)
                        else:
                            data['form'].para_inscripcion(inscripcion,personausuario)
                    # data['form'].notacredito_inscripcion(inscripcion)
                    data['pago_efectivo_id'] = FORMA_PAGO_EFECTIVO
                    data['pago_electronico_id'] = FORMA_PAGO_ELECTRONICO
                    data['pago_tarjeta_id'] = FORMA_PAGO_TARJETA
                    data['pago_tarjetadeb_id'] = FORMA_PAGO_TARJETA_DEB
                    data['pago_cheque_id'] = FORMA_PAGO_CHEQUE
                    data['pago_deposito_id'] = FORMA_PAGO_DEPOSITO
                    data['pago_transferencia_id'] = FORMA_PAGO_TRANSFERENCIA
                    data['pago_nota_credito_id'] = FORMA_PAGO_NOTA_CREDITO
                    data['pago_recibo_caja_id'] = FORMA_PAGO_RECIBOCAJAINSTITUCION
                    data['pago_retencion_id'] = FORMA_PAGO_RETENCION
                    data['pago_wester_id'] = FORMA_PAGO_WESTER
                    # data['tiene_cheque_protestado'] = False

                    data['tiene_cheque_protestado'] = inscripcion.tiene_cheque_protestado()

                    caja = request.session['persona'].lugarrecaudacion_set.filter(activa=True)[:1].get()
                    lugar = LugarRecaudacion.objects.filter(persona=request.session['persona'],activa=True)[:1].get()
                    sesion_caja = caja.sesion_caja()
                    if FACTURACION_ELECTRONICA:
                        if lugar.numerofact == None:
                            data['factura'] = sesion_caja.facturatermina
                        else:
                            data['factura'] = lugar.numerofact
                    else:
                        data['factura'] = sesion_caja.facturatermina
                    if inscripcion.persona.cedula:
                        data['facturaruc'] = inscripcion.persona.cedula
                    else:
                        data['facturaruc'] = inscripcion.persona.pasaporte
                    if ClienteFactura.objects.filter(ruc=data['facturaruc']).exists():
                        cliente = ClienteFactura.objects.filter(ruc=data['facturaruc'])[:1].get()
                    data['facturanombre'] = inscripcion.persona.nombre_completo()
                    if inscripcion.persona.direccion:
                        data['facturadireccion'] = inscripcion.persona.direccion
                    else:
                        if cliente:
                            data['facturadireccion']= cliente.direccion
                    if inscripcion.persona.telefono:
                        data['facturatelefono'] = inscripcion.persona.telefono
                    else:
                        if cliente:
                            data['facturatelefono']= cliente.telefono
                    data['facturacorreo'] = inscripcion.persona.emailinst
                    data['FACTURACION_ELECTRONICA'] = FACTURACION_ELECTRONICA
                    idrubro = []
                    if 'solicitud' in request.GET:
                        solicitud = SolicitudSecretariaDocente.objects.filter(id=request.GET['solicitud'])[:1].get()
                        data['solicitud'] = solicitud
                        fechasol = solicitud.datosaprobacion().fechadeposito
                        for x in rubros:
                            if x.aplicadescuento(fechasol)[1]:
                                idrubro.append(x.id)

                        data['fechasol'] = fechasol
                        data['totalapagar'] = sum([x.calculadescuento(idrubro,fechasol)[0] for x in rubros])
                    else:
                        if 'pagowestercaja' in request.GET:
                            pagowestercaja = PagoWester.objects.filter(pk=request.GET['pagowestercaja'])[:1].get()
                            data['fechasol'] = pagowestercaja.fechapago
                            data['pagowestercaja'] = pagowestercaja
                            for x in rubros:
                                if x.aplicadescuento( pagowestercaja.fechapago)[1]:
                                    idrubro.append(x.id)
                            data['totalapagar'] = sum([x.calculadescuento(idrubro, pagowestercaja.fechapago)[0] for x in rubros])
                        else:

                            data['fechasol'] = 'None'
                            for x in rubros:
                                if x.aplicadescuento(None)[1]:
                                    idrubro.append(x.id)
                            data['totalapagar'] = sum([x.calculadescuento(idrubro,None)[0] for x in rubros])
                    #data['totalapagar'] = sum([x.aplicadescuento() if HABILITA_APLICA_DESCUE else x.adeudado() for x in rubros])
                    data['idrubros'] = idrubro
                    if sum([x.es_notadebito() for x in rubros])==rubros.count():
                        data['tiene_nota_debito'] = True
                    data['HABILITA_APLICA_DESCUE'] = HABILITA_APLICA_DESCUE
                    data['tipo_beca_senescyt'] = TIPO_BECA_SENESCYT
                    data['sesion_caja']= sesion_caja

                    if RubroSeguimiento.objects.filter(rubro__id__in=rubros, estado=True, aplicadescuentocategoria=True).exists() or RubroSeguimiento.objects.filter(rubro__id__in=rubros, estado=True, aprobardescuentoadd=True).exists():
                        data['descuento_cobranza'] = True
                    return render(request ,"finanzas/pagarbs.html" ,  data)
                except Exception as ex:
                    print(ex)

            elif action=='pagartrico':
                cliente=''
                ids = request.GET['ids'].split(",")
                rubros = Rubro.objects.filter(id__in=ids).order_by('fechavence')
                fichamedica = rubros[0].fichamedica
                data['title'] = 'Pago de Rubros del Paciente: '+str(fichamedica)
                data['fichamedica'] = fichamedica
                data['rubros'] = rubros
                # Formulario de Pago
                data['form'] = FormaPagoForm(initial={'fechacobro': datetime.datetime.now()})
                data['form'].para_fichamedica(fichamedica)
                # data['form'].notacredito_inscripcion(inscripcion)
                data['pago_efectivo_id'] = FORMA_PAGO_EFECTIVO
                data['pago_electronico_id'] = FORMA_PAGO_ELECTRONICO
                data['pago_tarjeta_id'] = FORMA_PAGO_TARJETA
                data['pago_tarjetadeb_id'] = FORMA_PAGO_TARJETA_DEB
                data['pago_cheque_id'] = FORMA_PAGO_CHEQUE
                data['pago_deposito_id'] = FORMA_PAGO_DEPOSITO
                data['pago_transferencia_id'] = FORMA_PAGO_TRANSFERENCIA
                data['pago_nota_credito_id'] = FORMA_PAGO_NOTA_CREDITO
                data['pago_recibo_caja_id'] = FORMA_PAGO_RECIBOCAJAINSTITUCION
                data['pago_retencion_id'] = FORMA_PAGO_RETENCION
                data['pago_wester_id'] = FORMA_PAGO_WESTER
                # data['tiene_cheque_protestado'] = False
                data['puede_pagar'] = data['persona'].puede_recibir_pagos()
                caja = request.session['persona'].lugarrecaudacion_set.filter(activa=True)[:1].get()
                lugar = LugarRecaudacion.objects.filter(persona=request.session['persona'],activa=True)[:1].get()
                sesion_caja = caja.sesion_caja()
                if FACTURACION_ELECTRONICA:
                    if lugar.numerofact == None:
                        data['factura'] = sesion_caja.facturatermina
                    else:
                        data['factura'] = lugar.numerofact
                else:
                    data['factura'] = sesion_caja.facturatermina
                data['facturaruc'] = fichamedica.numdocumento
                if ClienteFactura.objects.filter(ruc=data['facturaruc']).exists():
                    cliente = ClienteFactura.objects.filter(ruc=data['facturaruc'])[:1].get()
                data['facturanombre'] = fichamedica.nombres+' '+fichamedica.apellidos
                if fichamedica.direccion:
                    data['facturadireccion'] = fichamedica.direccion
                else:
                    if cliente:
                        data['facturadireccion']= cliente.direccion
                if fichamedica.telefono:
                    data['facturatelefono'] = fichamedica.telefono
                else:
                    if cliente:
                        data['facturatelefono']= cliente.telefono
                data['facturacorreo'] = fichamedica.email
                data['FACTURACION_ELECTRONICA'] = FACTURACION_ELECTRONICA
                data['totalapagar'] = sum([x.adeudado() for x in rubros])

                if sum([x.es_notadebito() for x in rubros])==rubros.count():
                    data['tiene_nota_debito'] = True
                data['tipo_beca_senescyt'] = TIPO_BECA_SENESCYT
                if RubroSeguimiento.objects.filter(rubro__id__in=rubros, estado=True, aplicadescuentocategoria=True).exists() or RubroSeguimiento.objects.filter(rubro__id__in=rubros, estado=True, aprobardescuentoadd=True).exists():
                    data['descuento_cobranza'] = True
                return render(request ,"finanzas/pagarbstrico.html" ,  data)

            elif action=='pagos':
                rubro = Rubro.objects.get(pk=request.GET['id'])
                data['title'] = rubro.nombre()
                data['rubro'] = rubro
                pagos = Pago.objects.filter(rubro=rubro).order_by('fecha')
                data['pagos'] = pagos
                data['acepta_pagos'] = (ACEPTA_PAGO_EFECTIVO,
                                        ACEPTA_PAGO_CHEQUE,
                                        ACEPTA_PAGO_TARJETA)
                data['bancos'] = Banco.objects.all().order_by('nombre')

                data['procesadorespago'] = ProcesadorPagoTarjeta.objects.all().order_by('nombre')
                return render(request ,"finanzas/pagosbs.html" ,  data)

            elif action=='recargo':
                data['title'] = 'Recargar Rubro a Estudiante por Vencimiento de Cuota'
                rubro = Rubro.objects.get(pk=request.GET['id'])
                data['inscripcion'] = rubro.inscripcion
                data['rubro'] = rubro
                data['form'] = RubroForm(initial={'fechavence': datetime.datetime.now()})
                return render(request ,"finanzas/recargobs.html" ,  data)

            elif action=='liquida':
                data['title'] = 'Liquidar Rubro a Estudiante '
                rubro = Rubro.objects.get(pk=request.GET['id'])
                data['inscripcion'] = rubro.inscripcion
                data['rubro'] = rubro
                data['form'] = LiquidaRubroForm()
                return render(request ,"finanzas/liquidarrubrobs.html" ,  data)

            elif action=='adddonacion':
                data['inscripcion'] = Inscripcion.objects.get(pk=request.GET['id'])
                data['form'] = DonacionForm()
                return render(request ,"finanzas/adddonacion.html" ,  data)

            elif action=='descuento':
                data['inscripcion'] = Inscripcion.objects.get(pk=request.GET['id'])
                data['url'] = 'matriculas?action=matricula&id='+ request.GET['nivel']
                data['form1'] = DescuentoForm()
                rubros = Rubro.objects.filter(inscripcion=data['inscripcion'],cancelado=False).values('id')
                form = DetalleDescuentoForm()
                form.rubros_list(rubros)
                data['rubros']= Rubro.objects.filter(inscripcion=data['inscripcion'],cancelado=False)
                data['form']= form
                return render(request ,"finanzas/descuento.html" ,  data)

            elif action=='donaciones':
                inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                data['donaciones'] = inscripcion.donaciones()
                return render(request ,"finanzas/donacionesinsc.html" ,  data)
            elif action == 'facturawester':
                cliente=''
                codigo = request.GET['codigo']
                registro=RegistroWester.objects.filter(codigo= request.GET['codigo']).values('cuenta')

                rubros = Rubro.objects.filter(id__in=registro).order_by('fechavence')
                inscripcion = rubros[0].inscripcion
                data['title'] = 'Pago de Rubros del Alumno: '+str(inscripcion.persona)
                data['inscripcion'] = inscripcion
                data['rubros'] = rubros
                data['puede_pagar'] = data['persona'].puede_recibir_pagos()
                # Formulario de Pago
                data['form'] = FormaPagoForm(initial={'fechacobro': datetime.datetime.now()})
                personausuario = Persona.objects.filter(usuario=request.user)[:1].get()
                data['form'].para_inscripcion(inscripcion,personausuario)
                # data['form'].notacredito_inscripcion(inscripcion)
                data['pago_efectivo_id'] = FORMA_PAGO_EFECTIVO
                data['pago_electronico_id'] = FORMA_PAGO_ELECTRONICO
                data['pago_tarjeta_id'] = FORMA_PAGO_TARJETA
                data['pago_tarjetadeb_id'] = FORMA_PAGO_TARJETA_DEB
                data['pago_cheque_id'] = FORMA_PAGO_CHEQUE
                data['pago_deposito_id'] = FORMA_PAGO_DEPOSITO
                data['pago_transferencia_id'] = FORMA_PAGO_TRANSFERENCIA
                data['pago_nota_credito_id'] = FORMA_PAGO_NOTA_CREDITO
                data['pago_recibo_caja_id'] = FORMA_PAGO_RECIBOCAJAINSTITUCION
                data['pago_retencion_id'] = FORMA_PAGO_RETENCION
                data['pago_wester_id'] = FORMA_PAGO_WESTER
                # data['tiene_cheque_protestado'] = False

                data['tiene_cheque_protestado'] = inscripcion.tiene_cheque_protestado()

                caja = request.session['persona'].lugarrecaudacion_set.filter(activa=True)[:1].get()
                lugar = LugarRecaudacion.objects.filter(persona=request.session['persona'],activa=True)[:1].get()
                sesion_caja = caja.sesion_caja()
                if FACTURACION_ELECTRONICA:
                    if lugar.numerofact == None:
                        data['factura'] = sesion_caja.facturatermina
                    else:
                        data['factura'] = lugar.numerofact
                else:
                    data['factura'] = sesion_caja.facturatermina
                if inscripcion.persona.cedula:
                    data['facturaruc'] = inscripcion.persona.cedula
                else:
                    data['facturaruc'] = inscripcion.persona.pasaporte
                if ClienteFactura.objects.filter(ruc=data['facturaruc']).exists():
                    cliente = ClienteFactura.objects.filter(ruc=data['facturaruc'])[:1].get()
                data['facturanombre'] = inscripcion.persona.nombre_completo()
                if inscripcion.persona.direccion:
                    data['facturadireccion'] = inscripcion.persona.direccion
                else:
                    if cliente:
                        data['facturadireccion']= cliente.direccion
                if inscripcion.persona.telefono:
                    data['facturatelefono'] = inscripcion.persona.telefono
                else:
                    if cliente:
                        data['facturatelefono']= cliente.telefono
                data['facturacorreo'] = inscripcion.persona.emailinst
                data['FACTURACION_ELECTRONICA'] = FACTURACION_ELECTRONICA
                idrubro = []
                idrubreg = RegistroWester.objects.filter(codigo= request.GET['codigo']).values_list('cuenta')
                rw = RegistroWester.objects.filter(codigo= request.GET['codigo'])[:1].get()
                data['fechasol'] = rw.fecha
                for x in rubros:
                    if x.aplicadescuento(rw.fecha)[1]:
                        idrubro.append(x.id)

                data['totalapagar'] = sum([x.calculadescuento(idrubro,rw.fecha)[0] for x in rubros])
                data['idrubros'] = idrubro
                if sum([x.es_notadebito() for x in rubros])==rubros.count():
                    data['tiene_nota_debito'] = True
                data['pagowes']=1
                data['codigo']=str(request.GET['codigo'])
                data['fp']= FORMA_PAGO_WESTER
                data['HABILITA_APLICA_DESCUE'] = HABILITA_APLICA_DESCUE
                data['valor']= RegistroWester.objects.filter(codigo= request.GET['codigo']).aggregate(Sum('valor'))['valor__sum']
                data['tiene20desc'] =False
                data['tipo_beca_senescyt'] = TIPO_BECA_SENESCYT
                if RubroSeguimiento.objects.filter(rubro__id__in=rubros, estado=True, aplicadescuentocategoria=True).exists() or RubroSeguimiento.objects.filter(rubro__id__in=rubros, estado=True, aprobardescuentoadd=True).exists():
                        data['descuento_cobranza'] = True
                return render(request ,"finanzas/pagarbs.html" ,  data)

            elif action == 'aplicardescuento':
                cliente=''
                registro=[]
                descuento=DescuentoSeguimiento.objects.filter(pk=request.GET['id'])[:1].get()
                data['descuento']=descuento
                rubros = Rubro.objects.filter(id__in=descuento.rubros.split(",")).order_by('fechavence')
                inscripcion = rubros[0].inscripcion
                data['title'] = 'Pago de Rubros del Alumno: '+str(inscripcion.persona)
                data['inscripcion'] = inscripcion
                data['rubros'] = rubros
                data['puede_pagar'] = data['persona'].puede_recibir_pagos()
                # Formulario de Pago
                data['form'] = FormaPagoForm(initial={'fechacobro': datetime.datetime.now()})
                personausuario = Persona.objects.filter(usuario=request.user)[:1].get()
                data['form'].para_inscripcion(inscripcion,personausuario)
                # data['form'].notacredito_inscripcion(inscripcion)
                data['pago_efectivo_id'] = FORMA_PAGO_EFECTIVO
                data['pago_electronico_id'] = FORMA_PAGO_ELECTRONICO
                data['pago_tarjeta_id'] = FORMA_PAGO_TARJETA
                data['pago_tarjetadeb_id'] = FORMA_PAGO_TARJETA_DEB
                data['pago_cheque_id'] = FORMA_PAGO_CHEQUE
                data['pago_deposito_id'] = FORMA_PAGO_DEPOSITO
                data['pago_transferencia_id'] = FORMA_PAGO_TRANSFERENCIA
                data['pago_nota_credito_id'] = FORMA_PAGO_NOTA_CREDITO
                data['pago_recibo_caja_id'] = FORMA_PAGO_RECIBOCAJAINSTITUCION
                data['pago_retencion_id'] = FORMA_PAGO_RETENCION
                data['pago_wester_id'] = FORMA_PAGO_WESTER
                # data['tiene_cheque_protestado'] = False

                data['tiene_cheque_protestado'] = inscripcion.tiene_cheque_protestado()

                caja = request.session['persona'].lugarrecaudacion_set.filter(activa=True)[:1].get()
                lugar = LugarRecaudacion.objects.filter(persona=request.session['persona'],activa=True)[:1].get()
                sesion_caja = caja.sesion_caja()
                if FACTURACION_ELECTRONICA:
                    if lugar.numerofact == None:
                        data['factura'] = sesion_caja.facturatermina
                    else:
                        data['factura'] = lugar.numerofact
                else:
                    data['factura'] = sesion_caja.facturatermina
                if inscripcion.persona.cedula:
                    data['facturaruc'] = inscripcion.persona.cedula
                else:
                    data['facturaruc'] = inscripcion.persona.pasaporte
                if ClienteFactura.objects.filter(ruc=data['facturaruc']).exists():
                    cliente = ClienteFactura.objects.filter(ruc=data['facturaruc'])[:1].get()
                data['facturanombre'] = inscripcion.persona.nombre_completo()
                if inscripcion.persona.direccion:
                    data['facturadireccion'] = inscripcion.persona.direccion
                else:
                    if cliente:
                        data['facturadireccion']= cliente.direccion
                if inscripcion.persona.telefono:
                    data['facturatelefono'] = inscripcion.persona.telefono
                else:
                    if cliente:
                        data['facturatelefono']= cliente.telefono
                data['facturacorreo'] = inscripcion.persona.emailinst
                data['FACTURACION_ELECTRONICA'] = FACTURACION_ELECTRONICA
                for rub in Rubro.objects.filter(id__in=descuento.rubros.split(","),aplicadod=False).order_by('fechavence'):
                    rub.valor = rub.valor -  ((rub.adeudado() * descuento.pordesc)/100)
                    rub.aplicadod = True
                    rub.save()

                data['totalapagar'] = sum([x.aplicadescuento() if HABILITA_APLICA_DESCUE else x.adeudado() for x in rubros])

                if sum([x.es_notadebito() for x in rubros])==rubros.count():
                    data['tiene_nota_debito'] = True
                data['HABILITA_APLICA_DESCUE'] = HABILITA_APLICA_DESCUE
                data['tiene20desc'] =False
                data['tipo_beca_senescyt'] = TIPO_BECA_SENESCYT
                if RubroSeguimiento.objects.filter(rubro__id__in=rubros, estado=True, aplicadescuentocategoria=True).exists() or RubroSeguimiento.objects.filter(rubro__id__in=rubros, estado=True, aprobardescuentoadd=True).exists():
                    data['descuento_cobranza'] = True
                return render(request ,"finanzas/pagarbs.html" ,  data)

            elif action == 'facturaped':
                pagopedagogia=PagoExternoPedagogia.objects.get(pk= request.GET['id'])
                if not pagopedagogia.rubro.cancelado:
                    data['title'] = 'Pago de Rubros del Alumno: '+str(pagopedagogia.inscripcion.persona)
                    data['inscripcion'] = pagopedagogia.rubro.inscripcion
                    rubros = Rubro.objects.filter(id=pagopedagogia.rubro.id).order_by('fechavence')
                    data['rubros'] = rubros
                    data['puede_pagar'] = data['persona'].puede_recibir_pagos()
                    # Formulario de Pago
                    data['form'] = FormaPagoForm(initial={'fechacobro': datetime.datetime.now()})
                    personausuario = Persona.objects.filter(usuario=request.user)[:1].get()
                    data['form'].para_inscripcion(pagopedagogia.rubro.inscripcion,personausuario)
                    # data['form'].notacredito_inscripcion(inscripcion)
                    data['pago_efectivo_id'] = FORMA_PAGO_EFECTIVO
                    data['pago_electronico_id'] = FORMA_PAGO_ELECTRONICO
                    data['pago_tarjeta_id'] = FORMA_PAGO_TARJETA
                    data['pago_tarjetadeb_id'] = FORMA_PAGO_TARJETA_DEB
                    data['pago_cheque_id'] = FORMA_PAGO_CHEQUE
                    data['pago_deposito_id'] = FORMA_PAGO_DEPOSITO
                    data['pago_transferencia_id'] = FORMA_PAGO_TRANSFERENCIA
                    data['pago_nota_credito_id'] = FORMA_PAGO_NOTA_CREDITO
                    data['pago_recibo_caja_id'] = FORMA_PAGO_RECIBOCAJAINSTITUCION
                    data['pago_retencion_id'] = FORMA_PAGO_RETENCION
                    data['pago_wester_id'] = FORMA_PAGO_WESTER
                    # data['tiene_cheque_protestado'] = False

                    data['tiene_cheque_protestado'] = pagopedagogia.rubro.inscripcion.tiene_cheque_protestado()

                    caja = request.session['persona'].lugarrecaudacion_set.filter(activa=True)[:1].get()
                    lugar = LugarRecaudacion.objects.filter(persona=request.session['persona'],activa=True)[:1].get()
                    sesion_caja = caja.sesion_caja()
                    if FACTURACION_ELECTRONICA:
                        if lugar.numerofact == None:
                            data['factura'] = sesion_caja.facturatermina
                        else:
                            data['factura'] = lugar.numerofact
                    else:
                        data['factura'] = sesion_caja.facturatermina
                    # if pagopedagogia.rubro.inscripcion.persona.cedula:
                    data['facturaruc'] = pagopedagogia.identificacionruc
                    # else:
                    #     data['facturaruc'] = pagopedagogia.rubro.inscripcion.persona.pasaporte
                    if ClienteFactura.objects.filter(ruc=data['facturaruc']).exists():
                        cliente = ClienteFactura.objects.filter(ruc=data['facturaruc'])[:1].get()
                    data['facturanombre'] = pagopedagogia.nombresruc
                    # if pagopedagogia.rubro.inscripcion.persona.direccion:
                    data['facturadireccion'] = pagopedagogia.direccionruc
                    # else:
                    #     if cliente:
                    #         data['facturadireccion']= cliente.direccion
                    # if inscripcion.persona.telefono:
                    data['facturatelefono'] = pagopedagogia.fonoruc
                    # else:
                    #     if cliente:
                    #         data['facturatelefono']= cliente.telefono
                    data['facturacorreo'] = pagopedagogia.emailruc
                    data['FACTURACION_ELECTRONICA'] = FACTURACION_ELECTRONICA


                    data['totalapagar'] = sum([x.aplicadescuento(None) if HABILITA_APLICA_DESCUE else x.adeudado() for x in rubros])

                    if sum([x.es_notadebito() for x in rubros])==rubros.count():
                        data['tiene_nota_debito'] = True
                    data['pagopedagogia']=pagopedagogia
                    data['HABILITA_APLICA_DESCUE'] = HABILITA_APLICA_DESCUE
                    data['tiene20desc'] =False
                    data['tipo_beca_senescyt'] = TIPO_BECA_SENESCYT
                    if RubroSeguimiento.objects.filter(rubro__id__in=rubros, estado=True, aplicadescuentocategoria=True).exists() or RubroSeguimiento.objects.filter(rubro__id__in=rubros, estado=True, aprobardescuentoadd=True).exists():
                        data['descuento_cobranza'] = True
                    return render(request ,"finanzas/pagarbs.html" ,  data)
                else:
                    return HttpResponseRedirect("/finanzas?action=rubros&id="+str(pagopedagogia.inscripcion.id))

            elif action=='aplicardonacion':
                donacion = Donacion.objects.get(pk=request.GET['id'])
                #Recalcular rubros de inscripcion de acuerdo a la donacion escogida
                donacion.recalcula_rubros()
                donacion.aplicada = True
                donacion.usuarioaplica = request.user.username
                donacion.save()

                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de APLICAR DONACION
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(donacion).pk,
                    object_id       = donacion.id,
                    object_repr     = force_str(donacion),
                    action_flag     = CHANGE,
                    change_message  = 'Aplicada una Donacion (' + client_address + ')')

                return HttpResponseRedirect("/finanzas?s="+str(donacion.inscripcion.persona.cedula))

            return HttpResponseRedirect("/finanzas")
        else:
            search = None
            if 's' in request.GET:
                search = request.GET['s']
            if search:
                ss = search.split(' ')
                while '' in ss:
                    ss.remove('')
                if len(ss)==1:
                    inscripciones = Inscripcion.objects.filter(Q(persona__nombres__icontains=search) | Q(persona__apellido1__icontains=search) | Q(persona__apellido2__icontains=search) | Q(persona__cedula__icontains=search) | Q(persona__pasaporte__icontains=search) | Q(identificador__icontains=search) | Q(carrera__nombre__icontains=search)).order_by('persona__apellido1')
                else:
                    inscripciones = Inscripcion.objects.filter(Q(persona__apellido1__icontains=ss[0]) & Q(persona__apellido2__icontains=ss[1])).order_by('persona__apellido1','persona__apellido2','persona__nombres')

            else:
                # inscripciones = Inscripcion.objects.all().order_by('persona__apellido1')
                fech=datetime.datetime.now().year
                fecha= '2014-12-01'
                inscripciones = Inscripcion.objects.filter(persona__usuario__is_active=True).order_by('persona__apellido1')

            # inscripciones = inscripciones.filter(graduado=None)
            paging = MiPaginador(inscripciones, 30)
            p = 1
            try:
                if 'page' in request.GET:
                    p = int(request.GET['page'])
                page = paging.page(p)
            except:
                page = paging.page(1)

            paging.rangos_paginado(p)

            data['paging'] = paging
            data['page'] = page
            data['search'] = search if search else ""
            inscripcionespage = page.object_list
            for i in inscripcionespage:
                i.matriculains=i.matricula()
                i.grupoins=i.grupo()
                i.nombrecompleto=i.persona.nombre_completo()
                i.nombrecompletoinverso=i.persona.nombre_completo_inverso()
                i.becasenescyt=i.beca_senescyt()
                i.numerodocumento = i.persona.cedula if i.persona.cedula else i.persona.pasaporte
                i.totalrubros = i.total_rubros()
                i.verificatotal_pagado = i.verifica_total_pagado()
                i.creditoalafecha = i.credito_a_la_fecha()
                i.tienedeuda = i.tiene_deuda()
                i.adeudaalafecha = i.adeuda_a_la_fecha() if i.tienedeuda else 0.00
                i.tienechequeprotestado = i.tiene_cheque_protestado()
                i.tienedonacion = i.tiene_donacion()
                i.recibogenerado = i.recibo_generado()
                i.cantidadrecibo = i.cantidad_recibo()
            data['inscripciones'] = inscripcionespage
            try:
                data['caja'] = LugarRecaudacion.objects.filter(persona=data['persona'],activa=True)[:1].get()
                #Para los cajeros que tengan sesion de caja abierta
                if SesionCaja.objects.filter(caja=data['caja'], abierta=True).exists():
                    sesion = SesionCaja.objects.get(caja=data['caja'], abierta=True)
                    data['total_efectivo_sesion'] = sesion.total_efectivo_sesion()
                    data['cantidad_facturas_sesion'] = sesion.cantidad_facturas_sesion()
                    data['cantidad_cheques_sesion'] = sesion.cantidad_cheques_sesion()
                    data['total_cheque_sesion'] = sesion.total_cheque_sesion()
                    data['cantidad_tarjetas_sesion'] = sesion.cantidad_tarjetas_sesion()
                    data['total_tarjeta_sesion'] = sesion.total_tarjeta_sesion()
                    data['cantidad_depositos_sesion'] = sesion.cantidad_depositos_sesion()
                    data['total_deposito_sesion'] = sesion.total_deposito_sesion()
                    data['cantidad_transferencias_sesion'] = sesion.cantidad_transferencias_sesion()
                    data['total_transferencia_sesion'] = sesion.total_transferencia_sesion()
                    data['cantidad_recibocaja_sesion'] = sesion.cantidad_recibocaja_sesion()
                    data['total_recibocaja_sesion'] = sesion.total_recibocaja_sesion()
                    data['cantidad_notasdecredito_sesion'] = sesion.cantidad_notasdecredito_sesion()
                    data['total_notasdecredito_sesion'] = sesion.total_notasdecredito_sesion()
                    data['cantidad_retencion_sesion'] = sesion.cantidad_retencion_sesion()
                    data['total_retencion_sesion'] = sesion.total_retencion_sesion()
                    data['total_sesion'] = sesion.total_sesion()
                    data['sesion'] = sesion
            except :
                pass
            # if FACTURACION_ELECTRONICA:
            #     facturacionelectronicaeject()
            #     notacreditoelectronica()
            # Formulario de Pago
            data['form'] = PagoForm(initial={'fechacobro': datetime.datetime.now()})
            data['especieform'] = EspecieForm(initial={'fechacobroe': datetime.datetime.now()})

            data['pago_efectivo_id'] = FORMA_PAGO_EFECTIVO
            data['pago_electronico_id'] = FORMA_PAGO_ELECTRONICO
            data['pago_tarjeta_id'] = FORMA_PAGO_TARJETA
            data['pago_tarjetadeb_id'] = FORMA_PAGO_TARJETA_DEB
            data['pago_cheque_id'] = FORMA_PAGO_CHEQUE
            data['pago_deposito_id'] = FORMA_PAGO_DEPOSITO
            data['pago_transferencia_id'] = FORMA_PAGO_TRANSFERENCIA
            data['pago_recibo_caja_id'] = FORMA_PAGO_RECIBOCAJAINSTITUCION
            data['centroexterno'] = CENTRO_EXTERNO
            data['conduccion'] = INSCRIPCION_CONDUCCION
            data['extra'] = 1
            data['valor'] =VALOR_PERMISO_CONDU
            data['form1'] = FormaPagoPermForm(initial={'fechacobroperm': datetime.datetime.now()})

            # data['form'].para_inscripcion(inscripcion)

            end_time = datetime.datetime.now().time()
            print("Duracion de proceso "+str(start_time)+" - "+str(end_time))
            return render(request ,"finanzas/inscripcionesbs.html" ,  data)

def enviarmensajeitb(inscripcion,user,total):
    try:
        data = {}
        data['result'] = 'ok'
        listapersona = []
        client = Client('http://online.publimes.com:5000/Service.svc?wsdl')
        c = 0
        i = 0
        fecha = datetime.datetime.now()
        fecha = str(fecha.day).zfill(2)+"/"+str(fecha.month).zfill(2)+"/"+str(fecha.year)+" "+str(fecha.hour).zfill(2)+":"+str(fecha.minute).zfill(2)+":"+str(fecha.second).zfill(2)
        comprobar = ""
        mensaje = "ITB agradece su pago de $"+str(total)+" realizado "+fecha+u". Revise en sga.itb.edu.ec SOMOS ITB!!!"
        while ( i < 10):
            try:
                comprobar =  client.service.EnviarMensaje( 79,'TECBO14593', 'C', str(inscripcion.persona.telefono), mensaje)
                # comprobar =  client.service.EnviarMensaje( 79,'TECBO14593', 'C', '0986656832' , mensaje)
                # comprobar =  '3'
                i = 10
            except Exception as e:
                i = i + 1
            if comprobar == '4':
                pass
        if comprobar != '0':
            pass

        elif comprobar == '0':
            mensajeenviado = MensajesEnviado(nombre = elimina_tildes(inscripcion.persona.nombre_completo()),
                                            celular = inscripcion.persona.telefono,
                                            filtro = "FACTURAITB",
                                            mensaje = mensaje,
                                            fecha = datetime.datetime.now(),
                                            user = user)
            mensajeenviado.save()
    except Exception as e:
        pass

def solicitudsecretariamail(solicitud,request):
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

        hoy = datetime.datetime.today()
        personarespon = Persona.objects.filter(usuario=request.user)[:1].get()

        send_html_mail("FINALIZACION DE SOLICITUD",
            "emails/correo_finsolicituddpto.html", {'contenido': "FINALIZACION DE SOLICITUD", 'self': solicitud, 'personarespon': personarespon.nombre_completo(), 'fecha': hoy},correo.split())
