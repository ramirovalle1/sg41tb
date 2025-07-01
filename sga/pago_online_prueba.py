from datetime import datetime
import json
from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models.aggregates import Sum
from django.forms.models import model_to_dict
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.utils.encoding import force_str
import requests
from decorators import secure_module
from settings import ACEPTA_PAGO_EFECTIVO, VALIDAR_ENTRADA_SISTEMA_CON_DEUDA, DEFAULT_PASSWORD, TIPO_CONGRESO_RUBRO, FACTURACION_ELECTRONICA, CAJA_ONLINE, PROMOCION_GYM
from sga import pypagos
from sga.api import abrir_caja
from sga.commonviews import addUserData, ip_client_address
from sga.facturacionelectronica import mail_errores_autorizacion
from sga.forms import VerificaPagoForm
from sga.models import Matricula, RecordAcademico, Inscripcion, Periodo, MateriaAsignada, Profesor, Rubro, Banco, Pago, InscripcionDescuentoRef, Persona, Factura, PagoPymentez, ClienteFactura, PagoTarjeta, TipoTarjetaBanco, ProcesadorPagoTarjeta, LugarRecaudacion, PromoGym
from django.shortcuts import render

@transaction.atomic()
@login_required(redirect_field_name='ret', login_url='/login')
# @secure_module
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
                if rubroconsult.rubrootro_set.all()[:1].get().tipo.id == TIPO_CONGRESO_RUBRO or 'TALLER' in rubroconsult.rubrootro_set.all()[:1].get().descripcion:
                    return HttpResponse(json.dumps({"result":"ok"}), content_type="application/json")

            if rubroconsult.tipo() == "ESPECIE":
                return HttpResponse(json.dumps({"result":"ok"}), content_type="application/json")

            for rubro in rubros:
                if rubro.rubrootro_set.exists():
                    if rubro.rubrootro_set.all()[:1].get().tipo.id == TIPO_CONGRESO_RUBRO or 'TALLER' in rubro.rubrootro_set.all()[:1].get().descripcion:
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

        elif action =='eliminarid':
            if PagoPymentez.objects.filter(pk=request.POST['pagopy']).exists():
                PagoPymentez.objects.filter(pk=request.POST['pagopy']).delete()
            return HttpResponse(json.dumps({"result":"ok"}), content_type="application/json")

        elif action == 'verificarcodigo':
            try:
                if PagoPymentez.objects.filter(pk=request.POST['id']).exists():
                    pagopy = PagoPymentez.objects.filter(pk=request.POST['id'])[:1].get()
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
                    estado =transaccion['status']
                    # detalle =3
                    detalle =transaccion['status_detail']
                    if estado == 'success' and detalle == 3:
                        for r in Rubro.objects.filter(pk__in=pagopy.rubros.split(",")):
                            r.cancelado =True
                            r.save()
                        pagopy.inscripcion.notificacion_pago_online(pagopy.correo,transaccion['id'],transaccion['authorization_code'], transaccion['amount'])
                        pagopy.inscripcion.notificacion_pago_online_adm(transaccion['id'],transaccion['authorization_code'], transaccion['amount'])
                        pagopy.estado =estado
                        pagopy.detalle_estado = detalle
                        pagopy.save()
                        pagopy.monto = transaccion['amount']
                        pagopy.codigo_aut = transaccion['authorization_code']
                        pagopy.referencia_dev = transaccion['dev_reference']
                        pagopy.idref = transaccion['id']
                        pagopy.mensaje = transaccion['message']
                        # pagopy.fecha_pay = fecha_pay
                        pagopy.detalle_estado = transaccion['status_detail']
                        pagopy.referencia_tran = transaccion['id']
                        pagopy.tipo = tarjeta['type']
                        pagopy.save()
                        return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
            except Exception as e:
                print("errorpago: " + str(e))
                return HttpResponse(json.dumps({"result":"error"}),content_type="application/json")


        elif action == 'pagar':
            if 'transaction' in json.loads(request.POST['datos']):
                transaccion = json.loads(request.POST['datos'])['transaction']
                tarjeta = json.loads(request.POST['datos'])['card']

                try:
                    if PagoPymentez.objects.filter(pk=request.POST['pagopy']).exists():
                        pagopy = PagoPymentez.objects.filter(pk=request.POST['pagopy'])[:1].get()
                        pagopy.estado = transaccion['status']
                        pagopy.monto = transaccion['amount']
                        pagopy.detalle_estado = transaccion['status_detail']
                        pagopy.idref = transaccion['id']
                        pagopy.save()
                        transaction.commit()
                        if  transaccion['status'] == 'pending' and transaccion['status_detail'] == 31 :
                            return HttpResponse(json.dumps({"result":"pendiente",'pypago':str(pagopy.id)}),content_type="application/json")
                        if transaccion['status'] != 'success':
                            return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

                        if transaccion['status_detail'] != 3:
                            return HttpResponse(json.dumps({"result": "bad"}), content_type="application/json")

                        pagopy.codigo_aut = transaccion['authorization_code']
                        pagopy.referencia_dev = transaccion['dev_reference']
                        pagopy.mensaje = transaccion['message']
                        pagopy.fecha_pay = transaccion['payment_date']
                        pagopy.referencia_tran = tarjeta['transaction_reference']
                        pagopy.tipo = tarjeta['type']
                        # pagopy.rubros = request.POST['ids']
                        # pagopy.correo = request.POST['correo']
                        # pagopy.direccion = request.POST['direccion']
                        # pagopy.nombre = request.POST['nombre']
                        # pagopy.ruc = request.POST['ruc']
                        # pagopy.telefono = request.POST['telefono']
                        pagopy.fecha = datetime.now()
                        pagopy.save()
                        if transaccion['status'] == 'success':
                            for r in Rubro.objects.filter(pk__in=pagopy.rubros.split(",")):
                                r.cancelado =True
                                r.save()
                        transaction.commit()
                        # print(transaccion['status'])
                        pagopy.inscripcion.notificacion_pago_online(request.POST['correo'],transaccion['id'],transaccion['authorization_code'], transaccion['amount'])
                        pagopy.inscripcion.notificacion_pago_online_adm(transaccion['id'],transaccion['authorization_code'], transaccion['amount'])
                        client_address = ip_client_address(request)
                        # Log de ADICIONAR GRADUADO
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(pagopy).pk,
                            object_id       = pagopy.id,
                            object_repr     = force_str(pagopy),
                            action_flag     = ADDITION,
                            change_message  = 'Adicionado Pago en Linea PRUEBA(' + client_address + ')' )

                        #     return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                        # return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                        try:
                            if abrir_caja(114):
                                caja = abrir_caja(114)
                            else:
                                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                        except:
                             return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                        try:

                            cliente = ClienteFactura.objects.filter(ruc1=pagopy.ruc)[:1].get()
                            cliente.nombre =pagopy.nombre
                            cliente.direccion =pagopy.direccion
                            cliente.telefono =pagopy.telefono
                            cliente.correo =pagopy.correo
                            if cliente.contrasena == None:
                                cliente.contrasena =pagopy.ruc
                                cliente.numcambio = 0
                            cliente.save()
                        except :
                            cliente = ClienteFactura(ruc=pagopy.ruc, nombre=pagopy.nombre,
                                direccion=pagopy.direccion, telefono= pagopy.telefono,
                                correo=pagopy.correo,contrasena=pagopy.ruc,numcambio=0)
                            cliente.save()

                        if not Factura.objects.filter(numero=caja.caja.puntoventa.strip()+"-"+str(caja.caja.numerofact).zfill(9)).exists():
                            factura = Factura(numero = caja.caja.puntoventa.strip()+"-"+str(caja.caja.numerofact).zfill(9), fecha = datetime.now().date(),
                                                    valida = True, cliente = cliente,
                                                    subtotal = pagopy.monto , iva = 0, total = pagopy.monto ,
                                                    impresa=False, caja=caja.caja, estado = '', mensaje = '',dirfactura='')
                            factura.save()
                            if Factura.objects.filter(numero= factura.numero).count()>1:
                                mail_errores_autorizacion("FACTURA REPETIDA "+DEFAULT_PASSWORD,"Existe mas de una factura repetida verificar en factura PAGO ONLINE",factura.numero)
                                transaction.set_rollback(True)
                                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
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
                                tp.pagos.add(pago2)
                                factura.pagos.add(pago2)
                                if r.adeudado() == 0:
                                    if not r.vencido():
                                        if r.es_cuota() or r.es_matricula():
                                            promogim = 1
                                    r.cancelado = True
                                    r.save()

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
                                change_message  = 'Adicionada Factura Pagos-Online pRUEBA '+  ' (' + client_address + ')' )
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

                                transaction.commit()
                                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                                # factura.notificacion_pago_online(rubro)
                            except Exception as ex:
                                transaction.set_rollback(True)
                                # errores.append(('Ocurrio un Error.. Intente Nuevamente' + str(ex) ,d['ci']))
                                # email_error_pagoonline(errores,'ONLINE')
                                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                            #         return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
                        else:
                            transaction.set_rollback(True)
                            return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
                except Exception as e:
                    transaction.set_rollback(True)
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")

            elif 'error' in json.loads(request.POST['datos']):
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
            else:
                pass

            # transccion[]
    else:
        data = {'title': ' Pago online'}
        addUserData(request, data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action =='terminos':
                try:
                    inscripcion = Inscripcion.objects.get(persona=data['persona'])
                    data['inscripcion'] = inscripcion
                    pagopy = PagoPymentez(inscripcion=data['inscripcion'],
                                          rubros=request.GET['ids'],
                                          correo = request.GET['correo'],
                                          direccion = request.GET['direccion'][:50],
                                          nombre = request.GET['nombre'],
                                          ruc = request.GET['ruc'],
                                          telefono = request.GET['telefono'],
                                          fechatransaccion=datetime.now())
                    pagopy.save()
                    data['pagopy']=pagopy

                    return render(request ,"pagoonline/terminos_prueba.html" ,  data)
                except Exception as e:
                    return HttpResponse(json.dumps(2),content_type="application/json")

        else:
            data['title'] = 'Pago En Linea'
            if Inscripcion.objects.filter(persona=data['persona']).exists():
                inscripcion = Inscripcion.objects.get(persona=data['persona'])
        # cart = Cart(request.session)51287
                data['rubros'] =Rubro.objects.filter(cancelado=False,inscripcion=inscripcion).order_by('fechavence')
                # data['rubros'] =Rubro.objects.filter(cancelado=False,inscripcion__id=26154)
                data['inscripcion'] =inscripcion
                # data['facturas'] = Factura.objects.filter(pagos__rubro__inscripcion=data['inscripcion'])[:5]

                persona = Persona.objects.filter(usuario=request.user)[:1].get()
                data['persona']=persona

                # cart.add( Rubro.objects.filter(cancelado=False)[:1].get(), price=20)
                # data['cart']=cart
                data['frmverify'] = VerificaPagoForm()
                if 'info' in request.GET:
                    data['info']='OCURRIO UN ERROR'
                return render(request, 'pagoonline/show-cart_prueba.html',data)
            return HttpResponseRedirect("/?info=MODULO SOLO DISPONIBLE PARA ESTUDIANTE")
