from datetime import datetime, date, timedelta
import json
from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.db.models.aggregates import Sum
from django.forms.models import model_to_dict
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
import requests
from decorators import secure_module
from settings import ACEPTA_PAGO_EFECTIVO, VALIDAR_ENTRADA_SISTEMA_CON_DEUDA, DEFAULT_PASSWORD, TIPO_CONGRESO_RUBRO, FACTURACION_ELECTRONICA, CAJA_ONLINE, PROMOCION_GYM, INICIO_DIFERIR, FIN_DIFERIR, PORCENTAJE_DESCUENTO, VALIDAR_PAGO_RUBRO, CANTIDAD_CUOTAS, FECHA_DIFERIR, TIPO_CUOTA_RUBRO, FECHA_INCIO_DIFERIR, NIVEL_MALLA_UNO, HABILITA_APLICA_DESCUE, VALIDA_PROMOCION_EMERG, CUOTAS_CANCELAR, PORCENTAJE_DESC_CUOTAS
from sga import pypagos
from sga.api import abrir_caja
from sga.commonviews import addUserData, ip_client_address
from sga.facturacionelectronica import mail_errores_autorizacion
from sga.forms import VerificaPagoForm
from sga.models import Matricula, RecordAcademico, Inscripcion, Periodo, MateriaAsignada, Profesor, Rubro, Banco, Pago, \
     InscripcionDescuentoRef, Persona, Factura, PagoConduccion, ClienteFactura, PagoTarjeta, TipoTarjetaBanco, ProcesadorPagoTarjeta, \
     LugarRecaudacion, PromoGym, elimina_tildes, DetalleDescuento, Descuento, RubroOtro, DirferidoRubro, DetalleRubrosBeca,RegistroAceptacionPagoenLineaConduccion
from django.shortcuts import render

@transaction.atomic()
#@secure_module
def view(request):
    if request.method=='POST':
        action = request.POST['action']

        if action =='eliminarid':
            if PagoConduccion.objects.filter(pk=request.POST['pagopy']).exists():
                PagoConduccion.objects.filter(pk=request.POST['pagopy']).delete()
            return HttpResponse(json.dumps({"result":"ok"}), content_type="application/json")

        elif action == 'verificarcodigo':
            try:
                if PagoConduccion.objects.filter(pk=request.POST['id']).exists():
                    pagopy = PagoConduccion.objects.filter(pk=request.POST['id'])[:1].get()
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
                    datos['user'] = {"id":str(request.POST['usuarioid']) }
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
                    if estado == 'success' and detalle == 3:
                        pagopy.notificacion_pago_online(pagopy.correo,transaccion['id'],transaccion['authorization_code'], transaccion['amount'])
                        pagopy.notificacion_pago_online_adm(transaccion['id'],transaccion['authorization_code'], transaccion['amount'])
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
                    if pagopy.mensaje:
                        return HttpResponse(json.dumps({"result":"bad",'msj':elimina_tildes(pagopy.mensaje)}),content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
            except Exception as e:
                print("errorpago: " + str(e))
                return HttpResponse(json.dumps({"result":"error",'msj':elimina_tildes(e)}),content_type="application/json")

        if action=='anular':
            try:
                if PagoConduccion.objects.filter(pk=request.POST['tid']).exists():
                    pago = PagoConduccion.objects.filter(pk=request.POST['tid'])[:1].get()
                    import requests

                    import time
                    # import OpenSSL

                    import hashlib
                    from base64 import b64encode
                    paymentez_server_application_code = 'ITB-EC-SERVER'
                    paymentez_server_app_key = '3jnXITEpaAtTxJhufMKgonlsu8qRXW'
                    unix_timestamp = str(int(time.time()))
                    uniq_token_string = paymentez_server_app_key + unix_timestamp
                    uniq_token_hash = hashlib.sha256(uniq_token_string).hexdigest()
                    auth_token = b64encode('%s;%s;%s' % (paymentez_server_application_code,
                    unix_timestamp, uniq_token_hash))
                    from getpass import getpass
                    # Definimos la URL
                    # url = "https://ccapi-stg.paymentez.com/v2/transaction/refund/"
                    url = "https://ccapi.paymentez.com/v2/transaction/refund/"
                    # Solicitamos los datos del usuario

                    # Definimos la cabecera y el diccionario con los datos
                    cabecera1 = {'Content-type': 'application/json','Auth-Token': auth_token}
                    datos={}
                    datos['transaction'] = {"id":pago.idref }

                    response = requests.post(url, data=json.dumps(datos),headers={"Content-Type": "application/json",'Auth-Token': auth_token})
                    respuesta = response.json()
                    print(respuesta)
                    estado =respuesta['status']
                    detalle =respuesta['detail']
                    # estado='success'
                    # detalle='detalle'
                    if estado == 'success':
                        pago.motivo = request.POST['motivo']
                        pago.usuarioanula = request.user
                        pago.detalle =detalle
                        pago.anulado=True
                        pago.fechaanula = datetime.now()
                        pago.save()
                          # Log de ADICIONAR GRADUADO
                        client_address = ip_client_address(request)
                        # Log de ADICIONAR GRADUADO
                        LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(pago).pk,
                        object_id       = pago.id,
                        object_repr     = force_str(pago),
                        action_flag     = ADDITION,
                        change_message  = 'Anulado Pago en Linea Conduce (' + client_address + ')' )
                        return HttpResponse(json.dumps({"result":"ok","estado":estado,'detalle':detalle}),content_type="application/json")
                    return HttpResponse(json.dumps({"result":"bad2","estado":estado,'detalle':detalle}),content_type="application/json")
            except Exception as ex:
               return HttpResponse(json.dumps({"result":"bad","error":"excepcion"+str(ex)}),content_type="application/json")

        elif action == 'pagar':
            if 'transaction' in json.loads(request.POST['datos']):
                transaccion = json.loads(request.POST['datos'])['transaction']
                tarjeta = json.loads(request.POST['datos'])['card']

                try:
                    sid = transaction.savepoint()
                    if PagoConduccion.objects.filter(pk=request.POST['pagopy']).exists():
                        pagopy = PagoConduccion.objects.filter(pk=request.POST['pagopy'])[:1].get()
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

                        pagopy.codigo_aut = transaccion['authorization_code']
                        pagopy.referencia_dev = transaccion['dev_reference']
                        pagopy.mensaje = transaccion['message']
                        pagopy.fecha_pay = transaccion['payment_date']
                        pagopy.referencia_tran = tarjeta['transaction_reference']
                        pagopy.tipo = tarjeta['type']
                        pagopy.notificacion_pago_online(pagopy.correo,transaccion['id'],transaccion['authorization_code'], transaccion['amount'])
                        pagopy.notificacion_pago_online_adm(transaccion['id'],transaccion['authorization_code'], transaccion['amount'])
                        # pagopy.rubros = request.POST['ids']
                        # pagopy.correo = request.POST['correo']
                        # pagopy.direccion = request.POST['direccion']
                        # pagopy.nombre = request.POST['nombre']
                        # pagopy.ruc = request.POST['ruc']
                        # pagopy.telefono = request.POST['telefono']
                        pagopy.fecha = datetime.now()
                        pagopy.save()
                        transaction.savepoint_commit(sid)

                        if transaccion['status'] == 'success':
                            return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
                except Exception as e:
                    if transaccion['status'] == 'success':
                            return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

            elif 'error' in json.loads(request.POST['datos']):
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
            else:
                pass

            # transccion[]
    else:
        data = {'title': ' Pago online'}
        # addUserData(request, data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action =='terminos':
                try:
                    data['usuario'] = request.GET['usuario']
                    data['usuarioid'] = request.session['usuarioid']
                    data['currenttime'] = datetime.now()
                    data['remoteaddr'] = request.META['REMOTE_ADDR']

                    pagopy = PagoConduccion(usuario=data['usuario'],
                                          fechatransaccion=datetime.now(),
                                          usuarioid=request.session['usuarioid'],
                                          nombres=request.session['nombre'],
                                          correo=request.session['email'],
                                          direccion=request.GET['obs'])
                    pagopy.save()
                    data['pagopy']=pagopy
                    data['usuarioid']=request.GET['usuarioid']

                    data['totalapagar'] =  request.GET['deuda']
                    return render(request ,"pagoonline/terminoscondu.html" ,  data)
                except Exception as e:
                    return HttpResponse(json.dumps(2),content_type="application/json")

            elif action =='aceptapagoenlinea':
                try:
                    hoy=datetime.now().date()
                    if not RegistroAceptacionPagoenLineaConduccion.objects.filter(usuario=request.GET['usuario'],usuarioid=request.GET['usuarioid'],fecha=hoy,acepta=True).exists():
                        registro=RegistroAceptacionPagoenLineaConduccion(usuario=request.GET['usuario'],usuarioid=request.GET['usuarioid'],fecha=hoy,acepta=True)
                        registro.save()
                        return HttpResponse(json.dumps({"result":"ok"}), content_type="application/json")
                except Exception as ex:
                    print(ex)
                    return HttpResponse(json.dumps({"result":"bad","error":str(ex)}),content_type="application/json")


        if request.session['nombre']:

            return HttpResponseRedirect("/logincondu")
        return HttpResponseRedirect("/")
