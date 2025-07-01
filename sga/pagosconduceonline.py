from datetime import datetime, date, timedelta
import json
from django.contrib.admin.models import LogEntry, ADDITION,CHANGE
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
from sga.forms import VerificaPagoForm, PagoPyForms
from sga.models import Matricula, RecordAcademico, Inscripcion, Periodo, MateriaAsignada, Profesor, Rubro, Banco, Pago, InscripcionDescuentoRef, Persona, Factura, PagoConduccion, ClienteFactura, PagoTarjeta, TipoTarjetaBanco, ProcesadorPagoTarjeta, LugarRecaudacion, PromoGym, elimina_tildes, DetalleDescuento, Descuento, RubroOtro, DirferidoRubro, DetalleRubrosBeca
from django.shortcuts import render
from sga.carrera_admi import MiPaginador

@transaction.atomic()
#@secure_module
def view(request):
    if request.method=='POST':
        action = request.POST['action']

        if action =='eliminarid':
            if PagoConduccion.objects.filter(pk=request.POST['pagopy']).exists():
                PagoConduccion.objects.filter(pk=request.POST['pagopy']).delete()
            return HttpResponse(json.dumps({"result":"ok"}), content_type="application/json")



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

        elif action=='editar':
            p=PagoPyForms(request.POST)
            if p.is_valid():
                try:
                    if request.POST['idpagopy']=='':
                        idpagopy=0
                    else:
                        idpagopy=request.POST['idpagopy']
                    if PagoConduccion.objects.filter(pk=idpagopy).exists():
                        edit = PagoConduccion.objects.get(pk=idpagopy)
                        edit.idref=p.cleaned_data['idref']
                        edit.estado=p.cleaned_data['estado']
                        edit.codigo_aut = p.cleaned_data['codigo_aut']
                        edit.mensaje = p.cleaned_data['mensaje']
                        edit.monto = p.cleaned_data['monto']
                        edit.referencia_dev = p.cleaned_data['referencia_dev']
                        edit.detalle_estado = p.cleaned_data['detalle_estado']
                        edit.referencia_tran = p.cleaned_data['referencia_tran']
                        edit.tipo = p.cleaned_data['tipo']
                        mensaje = 'Edicion de Pago'
                        edit.save()
                        # Log de Editar Pago Paymentez Conduccion
                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(edit).pk,
                        object_id       = edit.id,
                        object_repr     = force_str(edit),
                        action_flag     = CHANGE,
                        change_message  = mensaje+' (' + client_address + ')' )
                        return HttpResponseRedirect("/pagosconduceonline")
                except Exception as e:
                    return HttpResponseRedirect("/pagosconduceonline?error="+str(e))
            else:
                return HttpResponseRedirect("/pagosconduceonline?error=Error en el formulario")


    else:
        data = {'title': ' Pago online'}
        addUserData(request, data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action =='terminos':
                try:
                    data['usuario'] = request.GET['usuario']
                    data['usuarioid'] = request.session['usuarioid']

                    pagopy = PagoConduccion(usuario=data['usuario'],
                                          fechatransaccion=datetime.now(),
                                          usuarioid=request.session['usuarioid'],
                                          nombres=request.session['nombre'],
                                          correo=request.session['email'])
                    pagopy.save()
                    data['pagopy']=pagopy
                    data['usuarioid']=request.GET['usuarioid']

                    data['totalapagar'] =  request.GET['deuda']
                    return render(request ,"pagoonline/terminoscondu.html" ,  data)
                except Exception as e:
                    return HttpResponse(json.dumps(2),content_type="application/json")

        else:

            data = {'title': 'Conduce Pagos Pymentez'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']
            else:
                # horatran = PagoPymentez.objects.filter(estado='').order_by('-id')[:1].get().fechatransaccion
                hoy = datetime.now() - timedelta(1)

                # pagos = PagoPymentez.objects.filter(estado='',fechatransaccion__lte = hoy)
                # pagos.delete()

                search = None
                if 's' in request.GET:
                    search = request.GET['s']
                    try:
                        search = int(search)
                        pagopy = PagoConduccion.objects.filter(Q(id=search) | Q(codigo_aut__icontains=str(search))).order_by('-id')
                    except Exception as e:
                        data['search'] = search
                        ss = search.split(' ')
                        while '' in ss:
                            ss.remove('')
                        if len(ss) == 1:
                            pagopy = PagoConduccion.objects.filter(Q(usuario__icontains=search) | Q(codigo_aut__icontains=search) | Q(referencia_tran__icontains=search) | Q(nombres__icontains= search) ).order_by('-id')
                        else:
                            pagopy = PagoConduccion.objects.filter(Q(nombres__icontains=ss[0]) & Q(nombres__icontains=ss[1]) | Q(codigo_aut__icontains=search) | Q(idref__icontains=search)).order_by('-id')
                else:
                    pagopy = PagoConduccion.objects.filter().order_by('-facturado','estado','-fechatransaccion', 'usuario')


                paging = MiPaginador(pagopy, 50)
                p = 1
                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                        paging = MiPaginador(pagopy, 30)
                    page = paging.page(p)
                except:
                    page = paging.page(1)
                data['paging'] = paging
                data['rangospaging'] = paging.rangos_paginado(p)
                data['page'] = page
                data['pagopy'] = page.object_list
                data['search'] = search if search else ""
                data['usuario'] = request.user
                data['formedit'] = PagoPyForms()
                return render(request ,"pagoonline/registroscondu.html" ,  data)
