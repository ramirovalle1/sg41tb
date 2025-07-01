from datetime import datetime, date, timedelta
from decimal import Decimal
import json
from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.db.models.aggregates import Sum, Max
from django.forms.models import model_to_dict
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.utils.encoding import force_str
import requests
from decorators import secure_module
from settings import ACEPTA_PAGO_EFECTIVO, VALIDAR_ENTRADA_SISTEMA_CON_DEUDA, DEFAULT_PASSWORD, TIPO_CONGRESO_RUBRO, \
    FACTURACION_ELECTRONICA, \
    CAJA_ONLINE, PROMOCION_GYM, INICIO_DIFERIR, FIN_DIFERIR, PORCENTAJE_DESCUENTO, VALIDAR_PAGO_RUBRO, CANTIDAD_CUOTAS, \
    FECHA_DIFERIR, TIPO_CUOTA_RUBRO, \
    FECHA_INCIO_DIFERIR, NIVEL_MALLA_UNO, HABILITA_APLICA_DESCUE, VALIDA_PROMOCION_EMERG, CUOTAS_CANCELAR, \
    PORCENTAJE_DESC_CUOTAS, PORCENTAJE_DESCUENTO15, \
    TIPO_RUBRO_CREDENCIAL, TIPO_OTRO_FRAUDE, ID_TIPO_ESPECIE_FRAUDE_TARJETA
from sga import pypagos
from sga.api import abrir_caja
from sga.commonviews import addUserData, ip_client_address
from sga.facturacionelectronica import mail_errores_autorizacion
from sga.forms import VerificaPagoForm
from sga.funciones import two_decimals
from sga.models import Matricula, RecordAcademico, Inscripcion, Periodo, MateriaAsignada, Profesor, Rubro, Banco, Pago, \
    InscripcionDescuentoRef, Persona, Factura, PagoPymentez, ClienteFactura, PagoTarjeta, TipoTarjetaBanco, \
    ProcesadorPagoTarjeta, \
    LugarRecaudacion, PromoGym, elimina_tildes, DetalleDescuento, Descuento, RubroOtro, DirferidoRubro, \
    DetalleRubrosBeca, \
    ParametroDescuento, RubroSeguimiento, RegistroAceptacionPagoenLinea, ReciboCajaInstitucion, FormaDePago, ReciboPago, \
    RegistroPlagioTarjetas, TipoEspecieValorada, SolicitudOnline, SolicitudEstudiante, RubroEspecieValorada, \
    NotaCreditoInstitucion
from django.shortcuts import render

@transaction.atomic()
@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    if request.method=='POST':
        action = request.POST['action']
        if action=='validarfecha':
            inscripcion = Inscripcion.objects.filter(id=request.POST['id'])[:1].get()

            rubroconsult = Rubro.objects.filter(id=request.POST['idrub'])[:1].get()
            bandera = 0
            congreso = 0
            datos = json.loads(request.POST['data'])
            rubros = Rubro.objects.filter(inscripcion=inscripcion,cancelado=False).exclude(id__in=datos) if request.POST['check'] == "true" else Rubro.objects.filter(inscripcion=inscripcion,cancelado=False,id__in=datos)

            if rubroconsult.rubrootro_set.exists():
                if rubroconsult.rubrootro_set.all()[:1].get().tipo.id == TIPO_CONGRESO_RUBRO or 'TALLER' in rubroconsult.rubrootro_set.all()[:1].get().descripcion or rubroconsult.rubrootro_set.all()[:1].get().tipo.id == TIPO_RUBRO_CREDENCIAL:
                    return HttpResponse(json.dumps({"result":"ok"}), content_type="application/json")

            if rubroconsult.tipo() == "ESPECIE":
                return HttpResponse(json.dumps({"result":"ok"}),content_type='application/json')
            if VALIDAR_PAGO_RUBRO:
                for rubro in rubros:

                    if request.POST['check'] == "true":
                        if rubro.fechavence < rubroconsult.fechavence and rubroconsult.tipo() != "ESPECIE" and rubro.rubrootro_set.all()[:1].get().tipo.id != TIPO_RUBRO_CREDENCIAL:
                            bandera = 1
                            break
                    else:
                        if rubro.fechavence > rubroconsult.fechavence and rubroconsult.tipo() != "ESPECIE":
                            bandera = 1
                            break

            if bandera == 1:
                return HttpResponse(json.dumps({"result":"bad"}),content_type='application/json')
            return HttpResponse(json.dumps({"result":"ok"}),content_type='application/json')
        elif action=='descuentos':
            porcedescuen = 0
            rubroconsult = Rubro.objects.filter(id=request.POST['idrub'])[:1].get()
            if rubroconsult.aplicadescuento('None')[1]:
                datos = json.loads(request.POST['data'])
                valor,aplicanivcut,valordescuent,porcedescuen = rubroconsult.calculadescuento(datos,None)
            else:
                valor = rubroconsult.aplicadescuento('None')[0]
                aplicanivcut = False
            return HttpResponse(json.dumps({"result":"ok","valor":str(valor),"aplicanivcut":aplicanivcut,"porcedescuen":porcedescuen}),content_type='application/json')

        elif action=='abonarrubros':

            porcedescuen = 0
            rubroconsult = Rubro.objects.filter(id=request.POST['idrub'])[:1].get()
            idrubroselec = json.loads(request.POST['rubroselec'])
            datos = json.loads(request.POST['data'])
            rubroselec = Rubro.objects.filter(id__in=idrubroselec)
            totalpagar = sum([x.calculadescuento(datos, None)[0] for x in rubroselec])
            if rubroconsult.aplicadescuento('None')[1]:
                if float(totalpagar) > float(request.POST['valpago']):
                    idrubr = Rubro.objects.filter(id__in=idrubroselec).order_by('-fechavence')[:1].get()
                    if idrubr.aplicadescuento('None')[1]:
                        datos.remove(str(idrubr.id))
                valor, aplicanivcut,valordescuent,porcedescuen = rubroconsult.calculadescuento(datos,None)
            else:
                valor = rubroconsult.aplicadescuento('None')[0]
                aplicanivcut = False
            return HttpResponse(json.dumps({"result":"ok","valor":str(valor),"aplicanivcut":aplicanivcut,"porcedescuen":porcedescuen}),content_type='application/json')

        elif action =='eliminarid':
            if PagoPymentez.objects.filter(pk=request.POST['pagopy']).exists():
                PagoPymentez.objects.filter(pk=request.POST['pagopy']).delete()
            return HttpResponse(json.dumps({"result":"ok"}), content_type="application/json")

        elif action == 'verificarcodigo':
            try:
                if PagoPymentez.objects.filter(pk=request.POST['id']).exists():
                    pagopy = PagoPymentez.objects.filter(pk=request.POST['id'])[:1].get()
                    tipotarjeta=''
                    estadopagoonline=''
                    cajapagoonline=''
                    import requests

                    import time
                    # import OpenSSL

                    import hashlib
                    from base64 import b64encode
                    # paymentez_server_application_code = 'KRISTY-EC-SERVER'
                    paymentez_server_application_code = 'ITB-EC-SERVER'
                    # paymentez_server_app_key = 'gFUy6QyZ6zfd31KsMPWgFPCRaKJOU5'
                    paymentez_server_app_key = '3jnXITEpaAtTxJhufMKgonlsu8qRXW'
                    unix_timestamp = str(int(time.time()))
                    uniq_token_string = paymentez_server_app_key + unix_timestamp
                    uniq_token_hash = hashlib.sha256(uniq_token_string).hexdigest()
                    auth_token = b64encode('%s;%s;%s' % (paymentez_server_application_code,
                    unix_timestamp, uniq_token_hash))
                    from getpass import getpass
                    # Definimos la URL
                    # url = "https://ccapi-stg.paymentez.com/v2/transaction/refund/"
                    url = "https://ccapi.paymentez.com/v2/transaction/verify"
                    # url = "https://ccapi-stg.paymentez.com/v2/transaction/verify"
                    # Solicitamos los datos del usuario

                    # Definimos la cabecera y el diccionario con los datos
                    # cabecera1 = {'Content-type': 'application/json','Auth-Token': auth_token}
                    datos={}
                    datos['user'] = {"id":str(pagopy.inscripcion.persona.usuario.id) }
                    datos['transaction'] = {"id": str(pagopy.idref) }
                    datos['type'] = "BY_OTP"
                    datos['value'] = request.POST['codigo']
                    datos['more_info'] = True
                    # print(datos)
                    # print(json.dumps(datos))
                    response = requests.post(url, data=json.dumps(datos),headers={"Content-Type": "application/json",'Auth-Token': auth_token}, verify=False)
                    # print(response)
                    resp = response.json()
                    print(resp)
                    transaccion= resp['transaction']
                    tarjeta= resp['card']
                    # print(tarjeta)

                    # print(respuesta)
                    # estado =1
                    try:
                        if 'message' in transaccion:
                            pagopy.mensaje = transaccion['message']
                    except Exception as e:
                        pass

                    estado =transaccion['status']
                    # detalle =3
                    detalle =transaccion['status_detail']
                    detallerubros=[]
                    if estado == 'success' and detalle == 3:
                        monto = float(pagopy.monto)
                        estadopagoonline='Aprobado'

                        rubroselec = Rubro.objects.filter(id__in=pagopy.rubros.split(","))
                        idrubrdesc = []
                        for rubsel in rubroselec:
                            if rubsel.aplicadescuento(None)[1]:
                                idrubrdesc.append(rubsel.id)
                        totalpagar = sum([x.calculadescuento(idrubrdesc, None)[0] for x in rubroselec])
                        if round(float(totalpagar),2) > round(float(monto),2):
                            idrubr = Rubro.objects.filter(id__in=pagopy.rubros.split(",")).order_by('-fechavence')[:1].get()
                            if idrubr.aplicadescuento(None)[1]:
                                idrubrdesc.remove(idrubr.id)
                        for r in Rubro.objects.filter(pk__in=pagopy.rubros.split(",")).order_by('fechavence'):
                            try:
                                adeudado = r.adeudado()
                                if r.aplicadescuento(None)[1]:
                                    valor,aplicanivcut,valdescuento,porcentajedescuento = r.calculadescuento(idrubrdesc, None)
                                    if round(float(monto),2) >= round(float(adeudado - valdescuento),2):
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
                                else:
                                    monto = monto - r.adeudado()

                                if r.adeudado() == adeudado and monto >= 0 :
                                    r.cancelado = True
                                    r.save()
                                    if RubroSeguimiento.objects.filter(rubro=r, estado=True).exists():
                                        rubroseg = RubroSeguimiento.objects.filter(rubro=r, estado=True).order_by('-id')[:1].get()
                                        rubroseg.fechapago = datetime.now().date()
                                        rubroseg.save()


                                detallerubros.append(('Rubro: '+ elimina_tildes(r.nombre()),'valor: '+ str(adeudado)))
                            except Exception as e:
                                print("Error al aplicar descuento " +str(e))
                                pass
                        pagopy.inscripcion.notificacion_pago_online(pagopy.correo,transaccion['id'],transaccion['authorization_code'], transaccion['amount'])
                        # pagopy.inscripcion.notificacion_pago_online_adm(transaccion['id'],transaccion['authorization_code'], transaccion['amount'])
                        pagopy.estado =estado
                        pagopy.detalle_estado = detalle
                        pagopy.save()
                        try:
                            pagopy.monto = transaccion['amount']
                            pagopy.save()
                        except Exception as e:
                            pass
                        try:
                            pagopy.codigo_aut = transaccion['authorization_code']
                            pagopy.save()
                        except Exception as e:
                            pass
                        try:
                            pagopy.referencia_dev = transaccion['dev_reference']
                            pagopy.save()
                        except Exception as e:
                            pass
                        try:
                            pagopy.idref = transaccion['id']
                            pagopy.save()
                        except Exception as e:
                            pass
                        try:
                            pagopy.mensaje = transaccion['message']
                            pagopy.save()
                        except Exception as e:
                            pass
                        # pagopy.fecha_pay = fecha_pay
                        try:
                            pagopy.detalle_estado = transaccion['status_detail']
                            pagopy.save()
                        except Exception as e:
                            pass
                        try:
                            pagopy.referencia_tran = transaccion['id']
                            pagopy.save()
                        except Exception as e:
                            pass
                        try:
                            pagopy.tipo = tarjeta['type']
                            tipotarjeta=pagopy.tipo
                            pagopy.save()
                        except Exception as e:
                            pass
                        # pagopy.save()
                        pagopy.inscripcion.notificacion_pago_online_adm(transaccion['id'],transaccion['authorization_code'], transaccion['amount'],detallerubros,tipotarjeta,estadopagoonline,cajapagoonline)
                        return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                    if pagopy.mensaje:
                        return HttpResponse(json.dumps({"result":"bad",'msj':elimina_tildes(pagopy.mensaje)}),content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
            except Exception as e:
                print("errorpago: " + str(e))
                return HttpResponse(json.dumps({"result":"error",'msj':elimina_tildes(e)}),content_type="application/json")


        elif action == 'pagar':
            if 'transaction' in json.loads(request.POST['datos']):
                transaccion = json.loads(request.POST['datos'])['transaction']
                tarjeta = json.loads(request.POST['datos'])['card']
                detallerubros=[]
                estadopagoonline=''
                tipotarjeta=''
                cajapagoonline=''
                formapago = FormaDePago.objects.get(id=16)
                try:
                    if PagoPymentez.objects.filter(pk=request.POST['pagopy']).exists():
                        sid = transaction.savepoint()
                        pagopy = PagoPymentez.objects.filter(pk=request.POST['pagopy'])[:1].get()
                        pagopy.estado = transaccion['status']
                        pagopy.monto = transaccion['amount']
                        pagopy.detalle_estado = transaccion['status_detail']
                        pagopy.idref = transaccion['id']
                        try:
                            if 'message' in transaccion:
                                pagopy.mensaje = transaccion['message']
                        except Exception as e:
                            pass
                        pagopy.save()
                        transaction.savepoint_commit(sid)
                        mensaje=''
                        if pagopy.mensaje:
                            mensaje =elimina_tildes(pagopy.mensaje)
                        if  transaccion['status'] == 'pending' and transaccion['status_detail'] == 31 :
                            return HttpResponse(json.dumps({"result":"pendiente",'pypago':str(pagopy.id)}),content_type="application/json")
                        if transaccion['status'] != 'success':
                            return HttpResponse(json.dumps({"result":"bad",'msj':mensaje}),content_type="application/json")

                        if transaccion['status_detail'] != 3:
                            return HttpResponse(json.dumps({"result": "bad",'msj':mensaje}), content_type="application/json")
                        try:
                            pagopy.codigo_aut = transaccion['authorization_code']
                            pagopy.save()
                        except Exception as e:
                            pass
                        try:
                            pagopy.referencia_dev = transaccion['dev_reference']
                            pagopy.save()
                        except Exception as e:
                            pass
                        try:
                            pagopy.mensaje = transaccion['message']
                            pagopy.save()
                        except Exception as e:
                            pass
                        try:
                            pagopy.fecha_pay = transaccion['payment_date']
                            pagopy.save()
                        except Exception as e:
                            pass
                        try:
                            pagopy.referencia_tran = tarjeta['transaction_reference']
                            pagopy.save()
                        except Exception as e:
                            pass
                        try:
                            pagopy.tipo = tarjeta['type']
                            pagopy.save()
                            tipotarjeta=pagopy.tipo
                        except Exception as e:
                            pass
                        # pagopy.rubros = request.POST['ids']
                        # pagopy.correo = request.POST['correo']
                        # pagopy.direccion = request.POST['direccion']
                        # pagopy.nombre = request.POST['nombre']
                        # pagopy.ruc = request.POST['ruc']
                        # pagopy.telefono = request.POST['telefono']
                        try:
                            pagopy.fecha = datetime.now()
                            pagopy.save()
                        except Exception as e:
                            pass
                        # pagopy.save()
                        if transaccion['status'] == 'success':
                            monto = Decimal(pagopy.monto).quantize(Decimal(10)**-2)
                            estadopagoonline='Aprobado'
                        rubroselec = Rubro.objects.filter(id__in=pagopy.rubros.split(","))
                        idrubrdesc = []
                        for rubsel in rubroselec:
                            if rubsel.aplicadescuento(None)[1]:
                                idrubrdesc.append(rubsel.id)
                        totalpagar = sum([x.calculadescuento(idrubrdesc, None)[0] for x in rubroselec])
                        if Decimal(totalpagar).quantize(Decimal(10)**-2) > Decimal(monto).quantize(Decimal(10)**-2):
                            idrubr = Rubro.objects.filter(id__in=pagopy.rubros.split(",")).order_by('-fechavence')[:1].get()
                            if idrubr.aplicadescuento(None)[1]:
                                idrubrdesc.remove(idrubr.id)
                        inscripcion=None
                        pago2=None
                        for r in Rubro.objects.filter(pk__in=pagopy.rubros.split(",")).order_by('fechavence'):
                            inscripcion=r.inscripcion
                            try:
                                adeudado = Decimal(r.adeudado()).quantize(Decimal(10)**-2)
                                if r.aplicadescuento(None)[1]:

                                    valor,aplicanivcut,valdescuento,porcentajedescuento = r.calculadescuento(idrubrdesc, None)
                                    if Decimal(monto).quantize(Decimal(10)**-2) >= Decimal(adeudado - valdescuento).quantize(Decimal(10)**-2):
                                        monto = monto - (Decimal(r.adeudado()).quantize(Decimal(10)**-2) - Decimal(valdescuento).quantize(Decimal(10)**-2))
                                    else:
                                        adeudado = monto
                                    descripdeta = 'PROMOCION ' + str(porcentajedescuento) + ' DESCUENTO POR PAGO DE CUOTAS'
                                    if Decimal(r.adeudado()).quantize(Decimal(10)**-2) == adeudado:
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
                                            valdescuento=Decimal(valdescuento).quantize(Decimal(10)**-2)
                                            adeudado = Decimal(r.adeudado()).quantize(Decimal(10)**-2)  - valdescuento
                                            r.valor = (r.valor - valdescuento)
                                            r.save()
                                else:
                                    monto = monto - Decimal(r.adeudado()).quantize(Decimal(10)**-2)


                                if  Decimal(r.adeudado()).quantize(Decimal(10)**-2) == adeudado and monto >= 0 :
                                    r.cancelado = True
                                    r.save()
                                    if RubroSeguimiento.objects.filter(rubro=r, estado=True).exists():
                                        rubroseg = RubroSeguimiento.objects.filter(rubro=r, estado=True).order_by('-id')[:1].get()
                                        rubroseg.fechapago = datetime.now().date()
                                        rubroseg.save()
                                detallerubros.append(('Rubro: '+ elimina_tildes(r.nombre()),'valor: '+ str(adeudado)))
                            except Exception as e:
                                print("Error al aplicar descuento " +str(e))
                                pass
                        # transaction.commit()
                        # print(transaccion['status'])
                        pagopy.inscripcion.notificacion_pago_online(request.POST['correo'],transaccion['id'],transaccion['authorization_code'], transaccion['amount'])
                        # pagopy.inscripcion.notificacion_pago_online_adm(transaccion['id'],transaccion['authorization_code'], transaccion['amount'])
                        client_address = ip_client_address(request)
                        # Log de ADICIONAR GRADUADO
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(pagopy).pk,
                            object_id       = pagopy.id,
                            object_repr     = force_str(pagopy),
                            action_flag     = ADDITION,
                            change_message  = 'Adicionado Pago en Linea (' + client_address + ')' )

                            # return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                        # return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                        try:
                            if abrir_caja(CAJA_ONLINE):
                                caja = abrir_caja(CAJA_ONLINE)
                            else:
                                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                        except:
                             return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                        try:

                            if ClienteFactura.objects.filter(ruc= pagopy.ruc).exists():
                                cliente = ClienteFactura.objects.filter(ruc=pagopy.ruc)[:1].get()
                                cliente.nombre = elimina_tildes(pagopy.nombre)
                                cliente.direccion =elimina_tildes(pagopy.direccion)
                                cliente.telefono =elimina_tildes(pagopy.telefono)
                                cliente.correo =pagopy.correo
                                if cliente.contrasena == None:
                                    cliente.contrasena =pagopy.ruc
                                    cliente.numcambio = 0
                                cliente.save()
                                if Persona.objects.filter(Q(cedula= pagopy.ruc)| Q(pasaporte=pagopy.ruc)).exists():
                                    persona = Persona.objects.filter(Q(cedula= pagopy.ruc)| Q(pasaporte=pagopy.ruc))[:1].get()
                                    persona.direccion = elimina_tildes(pagopy.direccion)
                                    persona.save()
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
                            monto = Decimal(pagopy.monto).quantize(Decimal(10)**-2)
                            sumaPagos = Decimal(0)
                            for r in Rubro.objects.filter(pk__in=pagopy.rubros.split(",")).order_by('fechavence'):
                                if Decimal(monto).quantize(Decimal(10)**-2) >= Decimal(r.adeudado()).quantize(Decimal(10)**-2):
                                    adeudado = r.adeudado()
                                    monto = monto - Decimal(r.adeudado()).quantize(Decimal(10)**-2)
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
                                if r.adeudado() == 0:
                                    if not r.vencido():
                                        if r.es_cuota() or r.es_matricula():
                                            promogim = 1
                                    r.cancelado = True
                                    r.save()

                                    if DetalleDescuento.objects.filter(rubro=r).exists():
                                        detDesc = DetalleDescuento.objects.filter(rubro=r)[:1].get()
                                        detDesc.pago = pago2
                                        detDesc.save()

                                    if DetalleRubrosBeca.objects.filter(rubro=r).exists():
                                        detRubroBeca = DetalleRubrosBeca.objects.filter(rubro=r)[:1].get()
                                        detRubroBeca.pago = pago2
                                        detRubroBeca.save()

                            caja.facturatermina= int(caja.caja.numerofact)+1
                            caja.save()
                            factura.total=sumaPagos
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
                                    # transaction.set_rollback(True)
                                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")

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
                                    # transaction.set_rollback(True)
                                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                                # transaction.commit()
                                pagopy.factura = factura
                                pagopy.save()
                                # transaction.commit()
                                cajapagoonline=caja
                                pagopy.inscripcion.notificacion_pago_online_adm(transaccion['id'],transaccion['authorization_code'], transaccion['amount'],detallerubros,tipotarjeta,estadopagoonline,cajapagoonline)

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

                                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                                # factura.notificacion_pago_online(rubro)
                            except Exception as ex:

                                transaction.savepoint_rollback(sid)
                                # errores.append(('Ocurrio un Error.. Intente Nuevamente' + str(ex) ,d['ci']))
                                # email_error_pagoonline(errores,'ONLINE')

                            #         return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

                            return HttpResponse(json.dumps({"result": "ok"}), content_type="application/json")
                        else:
                            # transaction.set_rollback(True)
                            return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
                except Exception as e:
                    # transaction.set_rollback(True)
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")

            elif 'error' in json.loads(request.POST['datos']):
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
            else:
                pass

            # transccion[]
        elif action == 'consulta_descuentocab':
            try:
                print(request.POST)
                rubro = Rubro.objects.get(pk=request.POST['id'])
                if RubroSeguimiento.objects.filter(rubro=rubro, estado=True, aplicadescuentocategoria=True).exists() or RubroSeguimiento.objects.filter(rubro=rubro, estado=True, aprobardescuentoadd=True).exists():
                    return HttpResponse(json.dumps({"result":"si"}),content_type="application/json")
                return HttpResponse(json.dumps({"result":"no"}),content_type="application/json")
            except Exception as ex:
                print(ex)
                return HttpResponse(json.dumps({"result":"bad","error":str(ex)}),content_type="application/json")

        elif action =='aceptapagoenlinea':
            try:
                hoy=datetime.now().date()
                inscripcion = Inscripcion.objects.filter(id=request.POST['id'])[:1].get()
                if not RegistroAceptacionPagoenLinea.objects.filter(inscripcion=inscripcion,fecha=hoy,acepta=True).exists():
                    registro=RegistroAceptacionPagoenLinea(inscripcion=inscripcion,fecha=hoy,acepta=True,usuario=request.user)
                    registro.save()
                    return HttpResponse(json.dumps({"result":"ok"}), content_type="application/json")
            except Exception as ex:
                print(ex)
                return HttpResponse(json.dumps({"result":"bad","error":str(ex)}),content_type="application/json")

        elif action == 'generar_especie_fraude':
            try:
                fraude = RegistroPlagioTarjetas.objects.get(pk=request.POST['fraude'])
                inscripcion = Inscripcion.objects.get(id=request.POST['id'])
                tipo_especie = TipoEspecieValorada.objects.get(pk=ID_TIPO_ESPECIE_FRAUDE_TARJETA)
                solicitud_online = SolicitudOnline.objects.get(pk=3)

                rubro = Rubro(fecha=datetime.now().date(),
                              valor=tipo_especie.precio,
                              inscripcion=inscripcion,
                              cancelado=False,
                              fechavence=datetime.now().date())
                rubro.save()

                solicitud_est = SolicitudEstudiante(solicitud=solicitud_online,
                                                    tipoe=tipo_especie,
                                                    inscripcion=inscripcion,
                                                    correo=inscripcion.persona.emailinst,
                                                    fecha=datetime.now(),
                                                    observacion="Especie generada por pago con tarjeta de forma fraudulenta para habilitar modulo de pago en linea",
                                                    solicitado=True,
                                                    rubro=rubro)
                solicitud_est.save()

                serie = 0
                valor = RubroEspecieValorada.objects.filter(rubro__fecha__year=rubro.fecha.year).aggregate(Max('serie'))
                if valor['serie__max'] != None:
                    serie = valor['serie__max'] + 1

                rubro_especie = RubroEspecieValorada(rubro=rubro,
                                                     tipoespecie=tipo_especie,
                                                     serie=serie,
                                                     autorizado=False)
                rubro_especie.save()
                fraude.rubroespecie = rubro_especie
                fraude.save()
                return HttpResponse(json.dumps({"result": "ok"}), content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({"result": "bad", 'mensaje':str(e)}), content_type="application/json")

    else:
        data = {'title': ' Pago online'}
        addUserData(request, data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action =='terminos':
                 # inscripcion = Inscripcion.objects.get(id=7)
                sid = transaction.savepoint()
                try:
                    inscripcion = Inscripcion.objects.get(persona=data['persona'])
                    data['inscripcion'] = inscripcion
                    pagopy = PagoPymentez(inscripcion=data['inscripcion'],
                                          rubros=request.GET['ids'],
                                          correo=request.GET['correo'],
                                          direccion=request.GET['direccion'][:50],
                                          nombre=request.GET['nombre'],
                                          ruc=request.GET['ruc'],
                                          telefono=request.GET['telefono'],
                                          fechatransaccion=datetime.now())
                    pagopy.save()
                    data['pagopy'] = pagopy
                    transaction.savepoint_commit(sid)
                    return render(request ,"pagoonline/terminos.html" ,  data)
                except Exception as e:
                    transaction.savepoint_rollback(sid)
                    return HttpResponseRedirect('/online')
        else:
            data['title'] = 'Pago En Linea'
            hoy=datetime.now().date()
            if Inscripcion.objects.filter(persona=data['persona']).exists():
                inscripcion = Inscripcion.objects.get(persona=data['persona'])
        # cart = Cart(request.session)51287
                for r in Rubro.objects.filter(inscripcion=inscripcion, cancelado=False):
                    if r.verifica_adeudado() == 0:
                        r.cancelado = True
                        r.save()

                data['rubros'] =Rubro.objects.filter(cancelado=False,inscripcion=inscripcion).order_by('fechavence')
                # data['rubros'] =Rubro.objects.filter(cancelado=False,inscripcion__id=26154)
                data['inscripcion'] =inscripcion
                if inscripcion.plagiotarjeta:
                    data['plagio']=True
                else:
                    data['plagio']=False
                # data['facturas'] = Factura.objects.filter(pagos__rubro__inscripcion=data['inscripcion'])[:5]

                persona = Persona.objects.filter(usuario=request.user)[:1].get()
                data['persona']=persona
                data['VALIDAR_PAGO_RUBRO']=VALIDAR_PAGO_RUBRO

                # cart.add( Rubro.objects.filter(cancelado=False)[:1].get(), price=20)
                # data['cart']=cart
                data['frmverify'] = VerificaPagoForm()
                if 'info' in request.GET:
                    data['info']='OCURRIO UN ERROR'
                data['HABILITA_APLICA_DESCUE'] = HABILITA_APLICA_DESCUE
                # //////////// para descuento promocion nivel
                data['PORCENTAJE_DESC_CUOTAS'] = PORCENTAJE_DESC_CUOTAS
                data['CUOTAS_CANCELAR'] = CUOTAS_CANCELAR
                if Matricula.objects.filter(inscripcion=inscripcion).order_by('-id').filter():
                    matricula = Matricula.objects.filter(inscripcion=inscripcion).order_by('-id')[:1].get()
                    if matricula.nivel.pagonivel_set.all().exclude(tipo=0):
                        pagonivel = matricula.nivel.pagonivel_set.all().exclude(tipo=0)
                        rubrosmin = Rubro.objects.filter(inscripcion=inscripcion).order_by('-fechavence')[:3]
                        rubrostod = Rubro.objects.filter(inscripcion=inscripcion).order_by('-fechavence')[:pagonivel.count()]
                        data['pagonivelnum'] = pagonivel.count()
                        data['valdistriubu'] = pagonivel.filter()[:1].get().valor
                        data['rubrosmin'] = rubrosmin
                        data['rubrostod'] = rubrostod

                if RegistroAceptacionPagoenLinea.objects.filter(inscripcion=inscripcion,fecha=hoy,acepta=True).exists():
                    data['aceptapagar'] = True
                else:
                    data['aceptapagar'] = False

                try:
                    listFraude = []
                    if RegistroPlagioTarjetas.objects.filter(inscripcion=inscripcion).exists():
                        fraudes = RegistroPlagioTarjetas.objects.filter(inscripcion=inscripcion).order_by('id')

                        ncs = NotaCreditoInstitucion.objects.filter(inscripcion=inscripcion, tipo__id=1, motivonc__id=1)
                        rubros_nc = Rubro.objects.filter(inscripcion=inscripcion, cancelado=False, nc__in=ncs.values_list('id'))
                        rubros_penalizacion = Rubro.objects.filter(inscripcion=inscripcion, cancelado=False, id__in=fraudes.values('rubro'))
                        # rubros_especie = Rubro.objects.filter(cancelado=False, id__in=RubroEspecieValorada.objects.filter(tipoespecie__id=93).values('rubro'))
                        rubros = rubros_nc | rubros_penalizacion
                        for rubro in rubros:
                            listFraude.append(
                                {
                                    'accion': 'PAGAR',
                                    'descripcion': rubro.nombre(),
                                    'valor': two_decimals(rubro.valor),
                                    'fraude_id': None
                                }
                            )

                        if fraudes.count() > 1:
                            contador = 1
                            for fraude in fraudes:
                                if not NotaCreditoInstitucion.objects.filter(factura=fraude.factura).exists():
                                    listFraude.append(
                                        {
                                            'accion': 'PENDIENTE ANULAR FACTURA',
                                            'descripcion': 'Pendiente anulacion de factura: ' + str(fraude.factura.numero) + '($' + str(two_decimals(fraude.factura.total)) + ')',
                                            'valor': two_decimals(fraude.factura.total),
                                            'fraude_id': fraude.id
                                        }
                                    )
                                if contador > 1:
                                    if not fraude.rubroespecie:
                                        listFraude.append(
                                            {
                                                'accion': 'SOLICITAR ACCESO',
                                                'descripcion': 'Solicitar especie ($5.00) para habilitar modulo Pago en Linea. <br>Factura: ' + str(fraude.factura.numero) + '($' + str(two_decimals(fraude.factura.total)) + ')',
                                                'valor': None,
                                                'fraude_id': fraude.id
                                            }
                                        )
                                    else:
                                        if not fraude.rubroespecie.rubro.cancelado:
                                            listFraude.append(
                                                {
                                                    'accion': 'PAGAR',
                                                    'descripcion': fraude.rubroespecie.rubro.nombre() + '<br>Factura: ' + str(fraude.factura.numero) + '($' + str(two_decimals(fraude.factura.total)) + ')',
                                                    'valor': two_decimals(fraude.rubroespecie.rubro.valor),
                                                    'fraude_id': fraude.id
                                                }
                                            )
                                        else:
                                            solicitud = SolicitudEstudiante.objects.get(rubro=fraude.rubroespecie.rubro)
                                            if not solicitud.aprobado or not solicitud.aplicada:
                                                listFraude.append(
                                                    {
                                                        'accion': 'PENDIENTE APROBACION',
                                                        'descripcion': fraude.rubroespecie.tipoespecie.nombre + '<br>Factura: ' + str(fraude.factura.numero) + '($' + str(two_decimals(fraude.factura.total)) + ')',
                                                        'valor': two_decimals(fraude.rubroespecie.rubro.valor),
                                                        'fraude_id': fraude.id
                                                    }
                                                )
                                contador += 1
                        # data['fraudes'] = listFraude
                        data['bloqueo_pago_online'] = True
                except Exception as e:
                    print(e)
                return render(request, 'pagoonline/show-cart.html',data)

            return HttpResponseRedirect("/?info=MODULO SOLO DISPONIBLE PARA ESTUDIANTE")
