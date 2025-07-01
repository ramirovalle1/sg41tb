from datetime import datetime, date
from decimal import Decimal
import json
import locale
import os
from django.contrib.admin.models import LogEntry, ADDITION, DELETION, CHANGE
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models.query_utils import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template.context import RequestContext
from django.utils.encoding import force_str
from fpdf import FPDF
from decorators import secure_module
from settings import UTILIZA_FACTURACION_CON_FPDF, JR_USEROUTPUT_FOLDER, MEDIA_URL, POSICIONES_IMPRESION, FACTURACION_CON_IVA, CENTRO_EXTERNO, FACTURACION_ELECTRONICA, RUBRO_TIPO_CURSOS,TIPO_OTRO_RUBRO, TIPO_NC_ANULACION, TIPO_NC_DEVOLUCION,TIPO_CUOTA_RUBRO,COEFICIENTE_CALCULO_BASE_IMPONIBLE, PORCENTAJE_DESCUENTO, INICIO_DIFERIR, FIN_DIFERIR
from sga.commonviews import addUserData, ip_client_address
from sga.facturacionelectronica import notacreditoelectronica, facturacionelectronicaeject, representacion_factura_str1
from sga.finanzas import representacion_factura_str
from sga.forms import FacturaCanceladaForm, NotaCreditoInstitucionForm, EditarFacturaForm, PagoNotaCreditodevoluForm, CabezNotaCreditoInstitucionForm, EditarTransferenciaForm,EditarTarjetaForm,EditarChequesForm, ObservacionForm, ObservacionDepositoForm
from sga.inscripciones import MiPaginador
from sga.models import Factura, FacturaCancelada, NotaCreditoInstitucion, Inscripcion, LugarRecaudacion, ClienteFactura, \
    Rubro, RubroOtro, TipoOtroRubro, TipoNotaCredito, DetalleNotacredDevol, \
    PagoTransferenciaDeposito, PagoTarjeta, PagoCheque, RubroReceta, RecetaVisitaBox, PagoPymentez, Descuento, \
    DetalleDescuento, TipoMotivoNotaCredito
from sga.reportes import elimina_tildes


@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    if request.method=='POST':
        action = request.POST['action']
        if action=='anular':
            factura = Factura.objects.get(pk=request.POST['id'])
            f = FacturaCanceladaForm(request.POST)
            if f.is_valid():

                sesion = factura.sesion()   #Obtener la sesion antes de borrar los pagos asociados

                for pago in factura.pagos.all():
                    pago.rubro.cancelado = False
                    pago.rubro.save()
                    if pago.pagocheque_set.all().exists():
                        pago.pagocheque_set.all().delete()
                    if pago.pagotarjeta_set.all().exists():
                        pago.pagotarjeta_set.all().delete()
                    if pago.pagotransferenciadeposito_set.all().exists():
                        pago.pagotransferenciadeposito_set.all().delete()
                    if pago.pagonotacredito_set.all().exists():
                        for pago_cred in pago.pagonotacredito_set.all():
                            nc = pago_cred.notacredito
                            nc.saldo += pago_cred.valor
                            nc.save()
                        pago.pagonotacredito_set.all().delete()

                    pago.delete()    #Eliminar todos los pagos asociados a la factura


                #Invalidar la Factura
                factura.valida=False
                factura.save()

                #Ingresar en el modelo de Facturas Canceladas
                facturacancelada = FacturaCancelada(factura=factura, motivo=f.cleaned_data['motivo'], fecha=datetime.now(), sesion=sesion)
                facturacancelada.save()

                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de ANULAR FACTURA
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(facturacancelada).pk,
                    object_id       = facturacancelada.id,
                    object_repr     = force_str(facturacancelada),
                    action_flag     = DELETION,
                    change_message  = 'Anulada Factura (' + client_address + ')')
        elif action=='editar':
            factura = Factura.objects.get(pk=request.POST['id'])
            f = EditarFacturaForm(request.POST)
            if f.is_valid():
                factura.numero=f.cleaned_data['numero']
                factura.cliente.ruc = f.cleaned_data['ruc']
                factura.cliente.nombre=f.cleaned_data['cliente']
                factura.save()
                factura.cliente.save()

                #Obtain client ip address
                client_address = ip_client_address(request)
                 # Log de ANULAR FACTURA
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(factura).pk,
                    object_id       = factura.id,
                    object_repr     = force_str(factura),
                    action_flag     = CHANGE,
                    change_message  = 'Editada Factura (' + client_address + ')')

                return HttpResponseRedirect("/facturas?s="+str(factura.numero))

        elif action=='modificardep':
            factura = Factura.objects.get(pk=request.POST['id'])
            f = EditarTransferenciaForm(request.POST)
            pago_transf = PagoTransferenciaDeposito.objects.get(pk=request.POST['dep'])
            if f.is_valid():
                pago_transf.referencia=f.cleaned_data['referencia']
                pago_transf.fecha = f.cleaned_data['fecha']
                pago_transf.cuentabanco_id = f.cleaned_data['cuentabanco_id']
                pago_transf.save()

                #Obtain client ip address
                client_address = ip_client_address(request)
                 # Log de ANULAR FACTURA
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(factura).pk,
                    object_id       = factura.id,
                    object_repr     = force_str(factura),
                    action_flag     = CHANGE,
                    change_message  = 'Modifica Transf o Deposito (' + client_address + ')')

                return HttpResponseRedirect("/facturas?s="+str(factura.numero))

        elif action =='consutardep':
            try:
                obs = request.POST['obs']
                if PagoTransferenciaDeposito.objects.filter(referencia=obs).exists():
                    dep = PagoTransferenciaDeposito.objects.filter(referencia=obs)[:1].get()
                    f=Factura.objects.filter(pagos__in= dep.pagos.all())[:1].get()
                    return HttpResponse(json.dumps({'result':'ok','factura':f.numero }),content_type="application/json")
                else:
                    return HttpResponse(json.dumps({'result':'bad' }),content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({'result':'bad' }),content_type="application/json")
        elif action=='modificartarj':
            factura = Factura.objects.get(pk=request.POST['id'])
            f = EditarTarjetaForm(request.POST)
            pago_tarj = PagoTarjeta.objects.get(pk=request.POST['tar'])
            if f.is_valid():
                pago_tarj.banco_id= f.cleaned_data['banco_id']
                pago_tarj.tipo_id= f.cleaned_data['tipotarjeta_id']
                pago_tarj.referencia = f.cleaned_data['referencia']
                pago_tarj.fecha = f.cleaned_data['fecha']
                pago_tarj.procesadorpago_id = f.cleaned_data['procesador_id']
                pago_tarj.lote = f.cleaned_data['lote']
                pago_tarj.autorizacion = f.cleaned_data['autorizacion']
                pago_tarj.save()

                #Obtain client ip address
                client_address = ip_client_address(request)
                 # Log de ANULAR FACTURA
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(factura).pk,
                    object_id       = factura.id,
                    object_repr     = force_str(factura),
                    action_flag     = CHANGE,
                    change_message  = 'Modifica Pago Tarjeta  (' + client_address + ')')

                return HttpResponseRedirect("/facturas?s="+str(factura.numero))

        elif action=='modificarch':
            factura = Factura.objects.get(pk=request.POST['id'])
            f = EditarChequesForm(request.POST)
            pago_ch = PagoCheque.objects.get(pk=request.POST['ch'])
            if f.is_valid():
                pago_ch.numero= f.cleaned_data['numero']
                pago_ch.banco_id= f.cleaned_data['banco_id']
                pago_ch.fechacobro = f.cleaned_data['fechacobro']
                pago_ch.emite = f.cleaned_data['emite']
                pago_ch.observacion = f.cleaned_data['observacion']
                pago_ch.recibido = f.cleaned_data['recibido']
                pago_ch.save()

                #Obtain client ip address
                client_address = ip_client_address(request)
                 # Log de Modificar Cheque
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(factura).pk,
                    object_id       = factura.id,
                    object_repr     = force_str(factura),
                    action_flag     = CHANGE,
                    change_message  = 'Modifica Pago Cheque  (' + client_address + ')')

                return HttpResponseRedirect("/facturas?s="+str(factura.numero))


        elif action=='addnc':
            receta = None
            factura = Factura.objects.get(pk=request.POST['id'])
            tiporu = None
            motivonc = None
            if request.POST['tipo'] == 'a' :
                tipo = TipoNotaCredito.objects.get(pk=TIPO_NC_ANULACION)
                tiponcre = True

            else:
                tipo = TipoNotaCredito.objects.get(pk=TIPO_NC_DEVOLUCION)
                tiponcre = False
            try:
                persona = request.session['persona']
                # beneficiario = Inscripcion.objects.get(pk=request.POST['bid'])
                if request.session['persona'].lugarrecaudacion_set.exists():
                    caja = request.session['persona'].lugarrecaudacion_set.filter(activa=True)[:1].get()
                    sesion_caja = caja.sesion_caja()
                    inscripcion = None
                    fichamedica = None
                    try:
                        if factura.estudiante().numdocumento:
                            fichamedica = factura.estudiante()
                    except:
                        pass
                    try:
                        if factura.estudiante().persona:
                            inscripcion = factura.estudiante()
                    except:
                        pass

                    lugar = LugarRecaudacion.objects.filter(persona=request.session['persona'],activa=True)[:1].get()

                    f = NotaCreditoInstitucionForm(request.POST)
                    if FACTURACION_ELECTRONICA:
                        dirnota = ''
                        mensajerecep = ''
                        recepcion = ''
                    else:
                        dirnota = None
                        mensajerecep =None
                        recepcion = None
                    from clinicaestetica.models import FichaMedica
                    if f.is_valid():
                        if NotaCreditoInstitucion.objects.filter(numero=(lugar.puntoventa+'-'+str(f.cleaned_data['numero']).zfill(9))).exists():
                            return  HttpResponseRedirect("/?info=Numero de Nota de Credito ya Existe")
                        numeronotacredito= str(f.cleaned_data['numero'])
                        if FACTURACION_ELECTRONICA:
                            for luga in LugarRecaudacion.objects.all():
                                if luga.puntoventa == lugar.puntoventa:
                                    luga.numeronotacre=int(lugar.numeronotacre)+1
                                    luga.save()
                            numeronotacredito= lugar.puntoventa+'-'+str(f.cleaned_data['numero']).zfill(9)
                        nc = NotaCreditoInstitucion(inscripcion=inscripcion,
                                                    fichamedica=fichamedica,
                                                    numero=numeronotacredito,
                                                    motivo=f.cleaned_data['motivo'],
                                                    fecha=datetime.today().date(),
                                                    hora=datetime.now().time(),
                                                    valor=f.cleaned_data['valor'],
                                                    factura=factura,
                                                    sesioncaja=sesion_caja,
                                                    usuario=elimina_tildes(persona.usuario.username),
                                                    estado = recepcion,
                                                    mensaje = mensajerecep,
                                                    dirnotacredito =dirnota,
                                                    cancelada =tiponcre,
                                                    saldo = Decimal(0),
                                                    tipo = tipo,
                                                    motivonc=motivonc)
                        if Inscripcion.objects.filter(pk=request.POST['bid']).exists():
                            beneficiario = Inscripcion.objects.get(pk=request.POST['bid'])
                            nc.beneficiario = beneficiario
                        else:
                            beneficiario = FichaMedica.objects.get(pk=request.POST['bid'])
                            nc.fichamedica = beneficiario
                        nc.save()

                        #OCastillo 28-04-2023 para nc anulacion motivo de NC
                        if tiponcre:
                            if f.cleaned_data['motivonc'] :
                                motnc = f.cleaned_data['motivonc'].id
                                motivoanulacion = TipoMotivoNotaCredito.objects.filter(pk=motnc)[:1].get()
                                nc.motivonc=motivoanulacion
                                nc.save()

                        for pago in nc.factura.pagos.all():
                            if RubroReceta.objects.filter(rubrootro__rubro = pago.rubro).exists():
                                receta = RubroReceta.objects.filter(rubrootro__rubro = pago.rubro)[:1].get()

                                for r in RecetaVisitaBox.objects.filter(visita=receta.detallebox,factura=True):
                                    if r.factura:
                                        r.registro.cantidad = r.registro.cantidad + r.cantidad
                                        if r.detalle:
                                            r.detalle.stock = r.detalle.stock + r.cantidad
                                            r.detalle.save()
                                        elif r.traslado:
                                            r.traslado.stock = r.traslado.stock + r.cantidad
                                            r.traslado.save()

                                        r.registro.save()

                        # try:
                        #     if ClienteFactura.objects.filter(ruc=beneficiario.persona.cedula).exists():
                        #         clie =  ClienteFactura.objects.get(ruc=beneficiario.persona.cedula)
                        #         if clie.contrasena==None:
                        #             clie.contrasena=beneficiario.persona.cedula
                        #             clie.numcambio=0
                        #     else:
                        #         clie =  ClienteFactura.objects.get(ruc=beneficiario.persona.pasaporte)
                        #         if clie.contrasena==None:
                        #             clie.contrasena=beneficiario.persona.pasaporte
                        #             clie.numcambio=0
                        #     clie.save()
                        # except:
                        #
                        #     ruc= beneficiario.persona.cedula if beneficiario.persona.cedula=='' else beneficiario.persona.pasaporte
                        #     cliente = ClienteFactura(ruc=ruc, nombre=beneficiario.persona.nombre_completo(),
                        #     direccion=beneficiario.persona.direccion, telefono=beneficiario.persona.telefono,
                        #     correo=beneficiario.persona.emailinst,contrasena=ruc,numcambio=0)
                        #     cliente.save()



                        #Obtain client ip address
                        if receta:
                            receta.correo('Nota de credito Generada','Se ha generado una nota de credito',37,request.user,'nc',nc.factura)
                        client_address = ip_client_address(request)

                        # Log de CREACION DE NOTA DE CREDITO INSTITUCIONAL
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(nc).pk,
                            object_id       = nc.id,
                            object_repr     = force_str(nc),
                            action_flag     = ADDITION,
                            change_message  = 'Adicionada Nota de Credito - Tipo: '+ str(nc.tipo) + ' (' + client_address + ')' )

                        # invoice = representacion_factura_str1(factura)

                        invoice = representacion_factura_str(factura)
                        val = 0
                        rubrosidlist = []
                        totfac=0
                        nuevor=[]
                        l=''
                        for pagos in invoice['pagos']:
                            desc = 'NCA - '


                            if pagos['rubro']['tipo'] != 'ESPECIE':
                                if not pagos['rubro']['id'] in rubrosidlist:
                                    val = 0
                                    rubrosidlist.append(pagos['rubro']['id'])
                                    desc = desc + pagos['rubro']['nombre']
                                    if TipoOtroRubro.objects.filter(nombre=pagos['rubro']['tipo']).exists():
                                        tiporu = TipoOtroRubro.objects.filter(nombre=pagos['rubro']['tipo'])[:1].get().id
                        # if val:
                                    for pag in invoice['pagos']:
                                        if pagos['rubro']['id']== pag['rubro']['id']:
                                            val = val + pag['valor']

                                    r1 = Rubro(fecha=datetime.today().date(),
                                               valor=val,
                                               inscripcion=inscripcion,
                                               cancelado=False,
                                               fechavence=datetime.today().date(),
                                               nc=nc.id)
                                    r1.save()
                                    if nc.motivonc.id == 1: #ID_MOTIVO_PLAGIO
                                        r1.editable = False
                                        r1.save()
                                    if not tiporu:
                                        tiporu = TIPO_CUOTA_RUBRO
                                    r1otro = RubroOtro(rubro=r1,
                                                       tipo=TipoOtroRubro.objects.get(pk=tiporu),
                                                       descripcion=desc)
                                    r1otro.save()

                        return HttpResponseRedirect("/facturas?id="+str(factura.id))
                    else:
                        return HttpResponseRedirect("/facturas?action=addnc&id="+str(factura.id))
                else:
                    return HttpResponseRedirect("/facturas?action=addnc&id="+str(factura.id))
            except Exception as ex2:
                return HttpResponseRedirect("/facturas?action=addnc&id="+str(factura.id))

        elif action =='consuvalor':
            if Factura.objects.filter(id=request.POST['id']).exists():
                factura = Factura.objects.get(id=request.POST['id'])
                invoice = representacion_factura_str(factura)
                t= invoice['pagos']
                sumpaog = 0
                valor = 0
                for nota in NotaCreditoInstitucion.objects.filter(factura=factura):
                    if DetalleNotacredDevol.objects.filter(rubro__id=int(request.POST['rubro']),notacredito=nota).exists():
                        deta = DetalleNotacredDevol.objects.get(rubro__id=int(request.POST['rubro']),notacredito=nota)
                        valor = Decimal(deta.valor)+Decimal(valor)
                for pagos in invoice['pagos']:
                    if pagos['rubro']['id'] == int(request.POST['rubro']):
                        # sumpaog = Decimal(sumpaog) + Decimal(pagos['valor'])
                        sumpaog = Decimal(sumpaog).quantize(Decimal(10)**-2) + Decimal(pagos['valor']).quantize(Decimal(10)**-2)
                val = sumpaog - valor
                return HttpResponse(json.dumps({"result":"ok","valor":str(val),"valor1":str(sumpaog)}),content_type="application/json")
            else:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")


        elif action =='addncrdevo':
            datos = json.loads(request.POST['datos'])
            factura = Factura.objects.get(pk=datos['id'])
            tipo = TipoNotaCredito.objects.get(pk=TIPO_NC_DEVOLUCION)
            tiporu=None
            from clinicaestetica.models import FichaMedica
            try:
                persona = request.session['persona']
                # beneficiario = Inscripcion.objects.get(pk=datos['beneficiario'])
                if request.session['persona'].lugarrecaudacion_set.exists():
                    caja = request.session['persona'].lugarrecaudacion_set.filter(activa=True)[:1].get()
                    sesion_caja = caja.sesion_caja()
                    inscripcion = None
                    fichamedica = None
                    try:
                        if factura.estudiante().numdocumento:
                            fichamedica = factura.estudiante()
                    except:
                        pass
                    try:
                        if factura.estudiante().persona:
                            inscripcion = factura.estudiante()
                    except:
                        pass
                    lugar = LugarRecaudacion.objects.filter(persona=request.session['persona'],activa=True)[:1].get()
                    if FACTURACION_ELECTRONICA:
                        dirnota = ''
                        mensajerecep = ''
                        recepcion = ''
                    else:
                        dirnota = None
                        mensajerecep =None
                        recepcion = None
                    if NotaCreditoInstitucion.objects.filter(numero=(lugar.puntoventa+'-'+str(datos['numero']).zfill(9))).exists():
                        return HttpResponse(json.dumps({"result":"existe"}),content_type="application/json")
                    numeronotacredito= str(datos['numero'])
                    if FACTURACION_ELECTRONICA:
                        for luga in LugarRecaudacion.objects.all():
                            if luga.puntoventa == lugar.puntoventa:
                                luga.numeronotacre=int(lugar.numeronotacre)+1
                                luga.save()
                        numeronotacredito= lugar.puntoventa+'-'+str(datos['numero']).zfill(9)


                    nc = NotaCreditoInstitucion(inscripcion=inscripcion,
                                                fichamedica=fichamedica,
                                                numero=numeronotacredito,
                                                motivo=datos['motivo'],
                                                fecha=datetime.today().date(),
                                                hora=datetime.now().time(),
                                                valor=Decimal(datos['total']),
                                                factura=factura,
                                                sesioncaja=sesion_caja,
                                                usuario=persona.usuario,
                                                estado = recepcion,
                                                mensaje = mensajerecep,
                                                dirnotacredito =dirnota,
                                                saldo= Decimal(datos['total']),
                                                tipo = tipo)

                    if Inscripcion.objects.filter(pk=datos['beneficiario']).exists():
                        beneficiario = Inscripcion.objects.get(pk=datos['beneficiario'])
                        nc.beneficiario = beneficiario
                    else:
                        beneficiario = FichaMedica.objects.get(pk=datos['beneficiario'])
                        nc.fichamedica = beneficiario
                    nc.save()

                    # try:
                    #     if ClienteFactura.objects.filter(ruc=beneficiario.persona.cedula).exists():
                    #         clie =  ClienteFactura.objects.get(ruc=beneficiario.persona.cedula)
                    #         if clie.contrasena==None:
                    #             clie.contrasena=beneficiario.persona.cedula
                    #             clie.numcambio=0
                    #     else:
                    #         clie =  ClienteFactura.objects.get(ruc=beneficiario.persona.pasaporte)
                    #         if clie.contrasena==None:
                    #             clie.contrasena=beneficiario.persona.pasaporte
                    #             clie.numcambio=0
                    #     clie.save()
                    # except:
                    #
                    #     ruc= beneficiario.persona.cedula if beneficiario.persona.cedula=='' else beneficiario.persona.pasaporte
                    #     cliente = ClienteFactura(ruc=ruc, nombre=beneficiario.persona.nombre_completo(),
                    #     direccion=beneficiario.persona.direccion, telefono=beneficiario.persona.telefono,
                    #     correo=beneficiario.persona.emailinst,contrasena=ruc,numcambio=0)
                    #     cliente.save()


                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de CREACION DE NOTA DE CREDITO INSTITUCIONAL
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(nc).pk,
                        object_id       = nc.id,
                        object_repr     = force_str(nc),
                        action_flag     = ADDITION,
                        change_message  = 'Adicionada Nota de Credito - Tipo: '+ str(nc.tipo) + ' (' + client_address + ')' )

                    invoice = representacion_factura_str1(factura)
                    if nc.tipo.id == TIPO_NC_ANULACION:
                        nc.cancelada = True
                        nc.save()
                    # DEVOLUCION NO GENERA RUBRO
                    desc = 'NCD - '
                    val = 0
                    for n in datos['detalle']:
                        rubro = Rubro.objects.get(pk=n['rubro'])
                        if rubro.tipo() != 'ESPECIE':
                             desc = desc + rubro.nombre() + ' - '
                             val = val +  Decimal(n['valor'])
                             if TipoOtroRubro.objects.filter(nombre=rubro.tipo()).exists():
                                    tiporu=TipoOtroRubro.objects.filter(nombre=rubro.tipo())[:1].get()
                    if val :
                        r1 = Rubro( fecha = datetime.today().date(),
                                    valor = val,
                                    inscripcion = inscripcion,
                                    fichamedica = fichamedica,
                                    cancelado = False,
                                    fechavence = datetime.today().date())
                        r1.save()
                        if  not tiporu:
                            tiporu = TipoOtroRubro.objects.get(pk=TIPO_CUOTA_RUBRO)
                        r1otro = RubroOtro(rubro=r1,
                                           tipo=tiporu,
                                           descripcion=desc)
                        r1otro.save()
                    for n in datos['detalle']:
                        det = DetalleNotacredDevol(
                                notacredito = nc,
                                rubro_id = n['rubro'],
                                valor = Decimal(n['valor'])
                                )
                        det.save()
                    return HttpResponse(json.dumps({"result":"ok","factura":str(factura.id)}),content_type="application/json")
                    # else:
                    #     return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
            except:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
        elif action=='reprint':
            factura = Factura.objects.get(pk=request.POST['id'])
            factura.impresa = False
            factura.save()
            #Para imprimir directo convirtiendo antes en un pdf usando libreria FPDF
            if UTILIZA_FACTURACION_CON_FPDF:
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
                for pagos in invoice['pagos']:
                    pdf.text(POSICIONES_IMPRESION['rubroalumno'][0],POSICIONES_IMPRESION['rubroalumno'][1],pagos['rubro']['alumno'])
                    pdf.text(POSICIONES_IMPRESION['rubrotipo'][0],POSICIONES_IMPRESION['rubrotipo'][1] + (i * 7),str(i+1)  + pagos['rubro']['nombre'])
                    pdf.text(POSICIONES_IMPRESION['rubrovalor'][0],POSICIONES_IMPRESION['rubrovalor'][1] + (i * 7),locale.currency(pagos['valor'], grouping=True))
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

                d = datetime.now()
                pdfname = 'factura-' + invoice['numero'] + '_' + d.strftime('%Y%m%d_%H%M%S') + '.pdf'
                output_folder = os.path.join(JR_USEROUTPUT_FOLDER, elimina_tildes(request.user.username))
                try:
                    os.makedirs(output_folder)
                except Exception as ex:
                    pass
                pdf.output(os.path.join(output_folder, pdfname))

                factura.impresa = True
                factura.save()
                return HttpResponse(json.dumps({'result': 'ok','reportfile': '/'.join([MEDIA_URL,'documentos',
                                                                                       'userreports',
                                                                                       request.user.username,
                                                                                       pdfname])}),content_type="application/json")
            else:
                if FACTURACION_ELECTRONICA:
                    return HttpResponse(json.dumps({'result':'fac','id':factura.id}),content_type="application/json")
                if CENTRO_EXTERNO :
                        return HttpResponse(json.dumps({'result':'buck','id':factura.id}),content_type="application/json")

            return HttpResponse(json.dumps({"result":"ok"}), content_type="application/json")

        return HttpResponseRedirect("/facturas")

    else:
        data = {'title': 'Listado de Facturas'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='anular':
                data['title'] = 'Anular Facturas'
                factura = Factura.objects.get(pk=request.GET['id'])
                data['factura'] = factura
                data['form'] = FacturaCanceladaForm()
                return render(request ,"facturas/anularbs.html" ,  data)

            if action=='editar':
                data['title'] = 'Editar Factura'
                factura = Factura.objects.get(pk=request.GET['id'])
                data['factura'] = factura
                data['form'] = EditarFacturaForm(initial={'numero':factura.numero, 'cliente':factura.cliente.nombre, 'ruc':factura.cliente.ruc})
                return render(request ,"facturas/editar.html" ,  data)

            if action=='modificardep':
                data['title'] = 'Modifica Referencia Pago Transferencia'
                factura = Factura.objects.get(pk=request.GET['id'])
                data['factura'] = factura

                for pago in factura.pagos.all():
                    if pago.pagotransferenciadeposito_set.all().exists():

                        for pago_transf in pago.pagotransferenciadeposito_set.all():
                            data['form'] = EditarTransferenciaForm(initial={'referencia':str(pago_transf.referencia), 'fecha':pago_transf.fecha, 'cuentabanco':str(pago_transf.cuentabanco.banco) +' '+str(pago_transf.cuentabanco.tipocuenta) + ' (' + str(pago_transf.cuentabanco.numero)+')'  })
                            data['cta'] = pago_transf.cuentabanco.id
                            data['pago_transf'] = pago_transf
                return render(request ,"facturas/modificardep.html" ,  data)

            if action=='modificartarj':
                data['title'] = 'Modifica Referencia Pago Tarjeta'
                factura = Factura.objects.get(pk=request.GET['id'])
                data['factura'] = factura

                for pago in factura.pagos.all():
                    if pago.pagotarjeta_set.all().exists():

                        for pago_tarj in pago.pagotarjeta_set.all():
                            data['form'] = EditarTarjetaForm(initial={'banco':str(pago_tarj.banco),'tipotarjeta':str(pago_tarj.tipo) ,'referencia':str(pago_tarj.referencia),'lote':str(pago_tarj.lote),'procesador':str(pago_tarj.procesadorpago),'autorizacion':str(pago_tarj.autorizacion), 'fecha':pago_tarj.fecha})
                            data['bco'] = pago_tarj.banco.id
                            data['ttarj'] = pago_tarj.tipo.id
                            data['procesador'] = pago_tarj.procesadorpago.id
                            data['pago_tarj'] = pago_tarj

                return render(request ,"facturas/modificartarj.html" ,  data)

            if action=='modificarch':
                data['title'] = 'Modifica Pago con Cheque Postfechado'
                factura = Factura.objects.get(pk=request.GET['id'])
                data['factura'] = factura

                for pago in factura.pagos.all():
                    # if pago.pagotarjeta_set.all().exists():
                    if pago.pagocheque_set.all().exists():

                        for pago_ch in pago.pagocheque_set.all():
                            data['form'] = EditarChequesForm(initial={'numero':str(pago_ch.numero),'banco':str(pago_ch.banco), 'fechacobro':pago_ch.fechacobro,'emite':pago_ch.emite, 'observacion':pago_ch.observacion})
                            data['bco'] = pago_ch.banco.id
                            data['fcobro'] = pago_ch.fechacobro
                            data['emite'] = pago_ch.emite
                            data['observacion'] = pago_ch.observacion
                            data['pago_ch'] = pago_ch

                return render(request ,"facturas/modificarch.html" ,  data)
            # elif action == 'actualizaiva':
            #     for f in Factura.objects.filter(fecha__gte='2016-06-01'):
            #         f.subtotal = Decimal(f.total/COEFICIENTE_CALCULO_BASE_IMPONIBLE).quantize(Decimal(10)**-2)
            #         f.iva = Decimal(f.total - (f.total/COEFICIENTE_CALCULO_BASE_IMPONIBLE)).quantize(Decimal(10)**-2)
            #         f.save()
            #     return HttpResponseRedirect("/facturas")

            elif action=='addnc':
                error = None
                data['title'] = 'Asociar Nota de Credito'
                if 'error' in request.GET:
                    data['error'] = request.GET['error']
                data['tipo'] = request.GET['tipo']
                lugarRecaudacion = LugarRecaudacion.objects.filter(persona=data['persona'],activa=True)[:1].get()
                f=""
                data['vari']= 0
                factura = Factura.objects.get(pk=request.GET['id'])
                data['facturacion_electronica'] = FACTURACION_ELECTRONICA
                for pago in factura.pagos.all():
                    if RubroReceta.objects.filter(rubrootro__rubro = pago.rubro).exists():
                        receta = RubroReceta.objects.filter(rubrootro__rubro = pago.rubro)[:1].get()
                        data['receta'] = receta
                # if FACTURACION_ELECTRONICA or CENTRO_EXTERNO or FACTURACION_CON_IVA:
                if lugarRecaudacion.numeronotacre==None:
                    if lugarRecaudacion.puntoventa != '001-001':
                        lugarRecaudacion.numeronotacre= 1
                    else:
                        lugarRecaudacion.numeronotacre= int(NotaCreditoInstitucion.objects.all().order_by('-id')[:1].get().numero)+1
                    lugarRecaudacion.save()
                # else:

                if data['tipo'] == 'a':
                    f = NotaCreditoInstitucionForm(initial={'numero':(int(lugarRecaudacion.numeronotacre))})
                    data['vari']= 1
                else:
                    lista = []
                    invoice = representacion_factura_str(factura)
                    t= invoice['pagos']
                    for pagos in invoice['pagos']:
                        lista.append(pagos['rubro']['id'])
                        totalim=(Decimal(pagos['valor']).quantize(Decimal(10)**-2)).quantize(Decimal(10)**-2)
                    rubros = Rubro.objects.filter(id__in=lista).order_by('fechavence')
                    data['rubros']= rubros
                    data['vari']= 1
                    form = PagoNotaCreditodevoluForm()
                    form.rubros_list(lista)
                    data['form']= form
                    data['factura'] = factura

                    data['form1']= CabezNotaCreditoInstitucionForm(initial={'numero':(int(lugarRecaudacion.numeronotacre))})

                    return render(request ,"facturas/addncdevolucion.html" ,  data)
                # else:
                #     f = NotaCreditoInstitucionForm()

                data['factura'] = factura
                data['form'] = f
                return render(request ,"facturas/addnc.html" ,  data)
        else:

            # if FACTURACION_ELECTRONICA:
            #     notacreditoelectronica()
            #     facturacionelectronicaeject()
            search = None
            ret = None
            id = None
            if 'id' in request.GET:
                id = int(request.GET['id'])
            if 'ret' in request.GET:
                ret = request.GET['ret']
            if 's' in request.GET:
                search = request.GET['s']
            if search:
                facturas = Factura.objects.filter(Q(numero__icontains=search) | Q(total__icontains=search) | Q(cliente__nombre__icontains=search) | Q(cliente__ruc__icontains=search)| Q(caja__nombre__icontains=search)| Q(caja__puntoventa__contains=search)).order_by('-fecha','-numero')
            else:
                if id:
                    facturas = Factura.objects.filter(id=id)
                else:
                    facturas = Factura.objects.all().order_by('-fecha','-numero')

            paging = MiPaginador(facturas, 70)
            p=1
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
            data['ret'] = ret if ret else ""
            data['facturas'] = page.object_list
            data['fechaactual'] = datetime.now().date()
            data['FACTURACIONELECTRONICA'] = FACTURACION_ELECTRONICA
            data['centro_externo'] = CENTRO_EXTERNO
            data['factura_iva'] = FACTURACION_CON_IVA
            data['puede_pagar'] = data['persona'].puede_recibir_pagos()
            data['obsform'] = ObservacionDepositoForm()
            try:
                caja = request.session['persona'].lugarrecaudacion_set.filter(activa=True)[:1].get()
                sesion_caja = caja.sesion_caja()
                data['sesion_caja'] = sesion_caja
            except :
                pass

            return render(request ,"facturas/facturasbs.html" ,  data)
