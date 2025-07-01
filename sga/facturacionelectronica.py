
from email.mime.base import MIMEBase
from django.forms import model_to_dict
from suds.client import Client
import unicodedata
from settings import AMBIENTE_FACTURACION, EMISION_ELECTRONICA, CODIGO_INFORMACION_INSTITUTO, CODIGO_NUMERICO_ELEC, \
     IDENTIFICACION_COMPRADOR, FACTURACION_CON_IVA, COEFICIENTE_CALCULO_BASE_IMPONIBLE, IVA_FACTU_ELECTRONICA, ATS_PATH, EMAIL_ACTIVE, \
     DIR_COMPRO, AMBIENTE_DESCRIPCION, INCIDENCIA_FACT,SITE_ROOT, TIPO_NC_ANULACION,FECHA_ELECT_FAC, URL_WEBSERVICE_FIRMA, DEFAULT_PASSWORD
from sga import number_to_letter
import csv

from sga.models import Factura, TituloInstitucion, LugarRecaudacion, Persona, Rubro, ClienteFactura, Pago, TipoIncidencia, NotaCreditoInstitucion, DetalleNotacredDevol, FormaDePago
from xml.etree import ElementTree
from xml.etree.ElementTree import Element, Comment, SubElement, tostring

from decimal import Decimal
import datetime
# from datetime import datetime
import os
import base64

from sga.tasks import send_html_mail

__author__ = 'jurgiles'


def facturacionelectronicaeject():
    # facturas = Factura.objects.filter(pk__in=[1452107,1452108,1452109],fecha__gte=FECHA_ELECT_FAC).exclude(estado=None).exclude(estado='AUTORIZADO').exclude(mensaje='CLAVE ACCESO REGISTRADA').order_by('id')
    facturas = Factura.objects.filter(fecha__gte=FECHA_ELECT_FAC).exclude(estado=None).exclude(estado='AUTORIZADO').exclude(mensaje='CLAVE ACCESO REGISTRADA').order_by('id')
    for facturaenv in facturas:
        mensajerecep=''
        recepcion = ''
        dirfactur=''
        numautorizacion=''
        clave=''
        fechautorizacion=''
        if facturaenv.mensaje != 'ERROR SECUENCIAL REGISTRADO' :
            if facturaenv.estado != 'NO ENVIADOAUT':
                try:
                    invoice = representacion_factura_str1(facturaenv)
                    fecha = invoice['fecha']
                    dia = fecha[:2]
                    mes = fecha[3:5]
                    anno = fecha[-4:]

                    lugar = LugarRecaudacion.objects.get(id=facturaenv.caja_id)

            # ///////////////////////////////////////////////////////////////XML FACTURACION ELECTRONICA///////////////////////////////////////////////////////////
            # /////////////////////////////////////////////////////////////////////////////////////////////////////////////////
                # //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
                # ///////////////////////////////////////////////////SECCION INFORMA CION TRIBUTARIA//////////////////////////////////////////////////////////////////////////////

                    factura = Element('factura')
                    factura.set('id', 'comprobante')
                    factura.set('version','1.0.0')

                    # comment = Comment('Generated for GIDTec ITB')
                    # iva.append(comment)

                    #ENCABEZADO ATS (Identificacion del Informante)
                    infoTributaria=SubElement(factura, 'infoTributaria')
                    ambiente = SubElement(infoTributaria,'ambiente')
                    ambiente.text = str(AMBIENTE_FACTURACION)
                    tipoEmision = SubElement(infoTributaria, 'tipoEmision')
                    tipoEmision.text = str(EMISION_ELECTRONICA)

                    # ////////////////////SECCION DE INFORMACION DE EMPRESA/////////////
                    empresa = TituloInstitucion.objects.get(pk=CODIGO_INFORMACION_INSTITUTO)
                    razonSocial = SubElement(infoTributaria,'razonSocial')
                    razonSocial.text = str(elimina_tildes1(empresa.nombre))
                    if empresa.nombrecomercial:
                        nombreComercial = SubElement(infoTributaria,'nombreComercial')
                        nombreComercial.text =str(elimina_tildes1(empresa.nombrecomercial))
                    ruc = SubElement(infoTributaria,'ruc')
                    ruc.text = empresa.ruc

                    # ////////////////////TERMINO DE SECCION//////////////////////
                    # ////////////////////SECCION DE CLAVE DE ACCESO/////////////
                    # lugar = LugarRecaudacion.objects.

                    clave= dia+mes+str(anno)+'01'+empresa.ruc+str(AMBIENTE_FACTURACION)\
                           +str(facturaenv.numero.strip().split("-")[0])+str(facturaenv.numero.strip().split("-")[1])\
                           +str(facturaenv.numero.strip().split("-")[2])+CODIGO_NUMERICO_ELEC+str(EMISION_ELECTRONICA)

                    pivote = 7
                    b=1
                    cantidadTotal=0
                    c=0
                    while ( c < len(clave)):

                        if pivote == 1:
                            pivote = 7

                        temporal = int(clave[c])
                        c = c+ 1
                        temporal *= pivote
                        pivote = pivote-1
                        cantidadTotal += temporal

                    cantidadTotal = 11 - (cantidadTotal % 11)
                    if cantidadTotal == 10:
                        cantidadTotal= 1
                    if cantidadTotal == 11:
                        cantidadTotal= 0
                    clave=clave + str(cantidadTotal)
                    claveAcceso = SubElement(infoTributaria,'claveAcceso')
                    claveAcceso.text=clave
                    # ////////////////////TERMINO DE SECCION/////////////
                    codDoc = SubElement(infoTributaria,'codDoc')
                    codDoc.text='01'
                    estab = SubElement(infoTributaria,'estab')
                    estab.text=str(facturaenv.numero.strip().split("-")[0])
                    ptoEmi = SubElement(infoTributaria,'ptoEmi')
                    ptoEmi.text=str(facturaenv.numero.strip().split("-")[1])
                    secuencial = SubElement(infoTributaria,'secuencial')
                    secuencial.text=str(facturaenv.numero.strip().split("-")[2])

                    dirMatriz = SubElement(infoTributaria,'dirMatriz')
                    dirMatriz.text=str(elimina_tildes1(empresa.direccion))
                # /////////////////////////////////////////////////////FIN DE SECCION/////////////////////////////////////////////////////////////////////////////
                # ///////////////////////////////////////////////////SECCION INFORMACION DE FACTURA//////////////////////////////////////////////////////////////////////////////
                    infoFactura=SubElement(factura, 'infoFactura')
                    fechaEmision = SubElement(infoFactura,'fechaEmision')

                    fechaEmision.text = str(str(dia)+'/'+str(mes)+'/'+str(anno))
                    dirEstablecimiento = SubElement(infoFactura, 'dirEstablecimiento')
                    dirEstablecimiento.text = lugar.direccion
                    if empresa.contribu_especial:
                        contribuyenteEspecial = SubElement(infoFactura, 'contribuyenteEspecial')
                        contribuyenteEspecial.text = str(empresa.contribu_especial)
                    obligadoContabilidad = SubElement(infoFactura, 'obligadoContabilidad')
                    obligadoContabilidad.text = empresa.contabilidad
                    # ///////////////////////////////////////////////////////
                    # //////////////////////////////FACTURA O PASAPORTE//////
                    identificador=IDENTIFICACION_COMPRADOR
                    if Persona.objects.filter(cedula=facturaenv.cliente.ruc).exists():
                        identificador='05'
                    elif len(str(facturaenv.cliente.ruc)) == 13:
                        identificador = '04'
                    elif len(str(facturaenv.cliente.ruc)) == 10:
                        identificador='05'
                    else:
                        identificador = '06'
                    tipoIdentificacionComprador = SubElement(infoFactura, 'tipoIdentificacionComprador')
                    tipoIdentificacionComprador.text = identificador
                    razonSocialComprador = SubElement(infoFactura, 'razonSocialComprador')
                    razonSocialComprador.text =str(elimina_tildes1((facturaenv.cliente.nombre)))
                    identificacionComprador = SubElement(infoFactura, 'identificacionComprador')
                    identificacionComprador.text = str(facturaenv.cliente.ruc)
                    if facturaenv.cliente.direccion:
                        direccionComprador = SubElement(infoFactura, 'direccionComprador')
                        direccionComprador.text = elimina_tildes1(facturaenv.cliente.direccion)

                    # /////////////////////////////TOTAL SINIMPUESTO////////////////
                    totalim=Decimal(0)
                    valorimp=Decimal(0)
                    for pagos in invoice['pagos']:
                        # for pag in pago['pagos']:
                        t = Decimal(pagos['valor']).quantize(Decimal(10)**-2)
                        totalim= Decimal(t+totalim).quantize(Decimal(10)**-2)
                    if FACTURACION_CON_IVA:
                        valorimp=Decimal(facturaenv.iva).quantize(Decimal(10)**-2)
                        totalim =Decimal(facturaenv.subtotal).quantize(Decimal(10)**-2)

                    totalSinImpuestos = SubElement(infoFactura, 'totalSinImpuestos')
                    totalSinImpuestos.text = str(totalim)
                    totalDescuento = SubElement(infoFactura, 'totalDescuento')
                    totalDescuento.text = '0.00'
                    totalConImpuestos = SubElement(infoFactura, 'totalConImpuestos')
                    totalImpuesto = SubElement(totalConImpuestos, 'totalImpuesto')
                    codigo = SubElement(totalImpuesto, 'codigo')
                    codigo.text = '2'

                    codigoPorcentaje = SubElement(totalImpuesto, 'codigoPorcentaje')

                    if FACTURACION_CON_IVA:
                        codigoPorcentaje.text = '2'
                    else:
                        codigoPorcentaje.text = '0'
                    baseImponible = SubElement(totalImpuesto, 'baseImponible')
                    baseImponible.text = str(totalim)
                    valor = SubElement(totalImpuesto, 'valor')
                    valor.text = str(valorimp)
                    propina = SubElement(infoFactura, 'propina')
                    propina.text = '0.00'
                    importeTotal = SubElement(infoFactura, 'importeTotal')
                    importeTotal.text = str(Decimal(totalim+valorimp).quantize(Decimal(10)**-2))
                    moneda = SubElement(infoFactura, 'moneda')
                    moneda.text = empresa.moneda
                    # ///////////////////////////////////////////////////NUEVO PAGOS//////////////////////////////////////////////////////////////////////////////
                    pagossub = SubElement(infoFactura, 'pagos')
                    listformapago = []
                    for pago in invoice['pagos']:
                        pagomod = Pago.objects.get(id=pago['id'])
                        formapagomodel = FormaDePago.objects.filter(nombre=pagomod.tipo())[:1].get()
                        totalfomrpag = 0.00
                        if not formapagomodel.codigoformapago.codigo in listformapago :
                            pago = SubElement(pagossub,'pago')
                            formaPago = SubElement(pago,'formaPago')
                            formaPago.text = formapagomodel.codigoformapago.codigo
                            listformapago.append(formapagomodel.codigoformapago.codigo)
                            for pago1 in invoice['pagos']:
                                pagomod1 = Pago.objects.get(id=pago1['id'])
                                formapagomodel1 = FormaDePago.objects.filter(nombre=pagomod1.tipo())[:1].get()
                                if formapagomodel1.codigoformapago.codigo in listformapago and formapagomodel.codigoformapago.codigo == formapagomodel1.codigoformapago.codigo :
                                    totalfomrpag =  Decimal(Decimal(totalfomrpag) + Decimal(pagomod1.valor)).quantize(Decimal(10)**-2)
                            totalform = SubElement(pago,'total')
                            totalform.text = str(totalfomrpag)
                            plazo = SubElement(pago,'plazo')
                            plazo.text = str(0)
                            unidadTiempo = SubElement(pago,'unidadTiempo')
                            unidadTiempo.text = 'Dias'
                # ///////////////////////////////////////////////////SECCION DETALLE DE FACTURA//////////////////////////////////////////////////////////////////////////////
                    totalim=Decimal(0)
                    valorimp=Decimal(0)
                    detalles=SubElement(factura, 'detalles')
                    detalle = ""
                    lista=[]
                    for pagos in invoice['pagos']:
                        # for rub in pago['pagos']:
                        if not pagos['rubro']['id'] in lista :
                            if len(lista)>0:
                                if FACTURACION_CON_IVA:
                                    valorimp=Decimal(totalim * Decimal(COEFICIENTE_CALCULO_BASE_IMPONIBLE).quantize(Decimal(10)**-2)).quantize(Decimal(10)**-2)
                                    totalim =Decimal(totalim - valorimp).quantize(Decimal(10)**-2)
                                precioUnitario = SubElement(detalle,'precioUnitario')
                                precioUnitario.text = str(totalim)
                                descuento = SubElement(detalle,'descuento')
                                descuento.text = '0.00'
                                precioTotalSinImpuesto = SubElement(detalle,'precioTotalSinImpuesto')
                                precioTotalSinImpuesto.text = str(totalim)
                                impuestos = SubElement(detalle,'impuestos')
                                impuesto = SubElement(impuestos,'impuesto')
                                codigo = SubElement(impuesto,'codigo')
                                codigo.text = '2'

                                codigoPorcentaje = SubElement(impuesto, 'codigoPorcentaje')
                                iva='0.00'
                                if FACTURACION_CON_IVA:
                                    codigoPorcentaje.text = '2'
                                    iva=IVA_FACTU_ELECTRONICA
                                else:
                                    codigoPorcentaje.text = '0'
                                tarifa = SubElement(impuesto,'tarifa')
                                tarifa.text = iva
                                baseImponible = SubElement(impuesto,'baseImponible')
                                baseImponible.text = str(totalim)
                                valor = SubElement(impuesto,'valor')
                                valor.text = str(valorimp)
                                totalim=Decimal(0)
                                valorimp=Decimal(0)

                            lista.append(pagos['rubro']['id'])
                            rubro = Rubro.objects.get(pk=pagos['rubro']['id'])
                            detalle = SubElement(detalles,'detalle')
                            codigoPrincipal = SubElement(detalle,'codigoPrincipal')
                            codigoPrincipal.text = str(rubro.id)
                            descripcion = SubElement(detalle,'descripcion')
                            if len(str(elimina_tildes1(rubro.nombre())))-1 == str(elimina_tildes1(rubro.nombre())).rfind("\n"):
                                descripcion.text = str(str(elimina_tildes1(rubro.nombre()))[0:len(str(elimina_tildes1(rubro.nombre())))-1].replace("\n",''))
                            else:
                                descripcion.text = str(str(elimina_tildes1(rubro.nombre())).replace("\n",' '))
                            # descripcion.text = str(elimina_tildes1(rubro.nombre()))
                            cantidad = SubElement(detalle,'cantidad')
                            cantidad.text = '1'
                        totalim=(totalim+Decimal(pagos['valor']).quantize(Decimal(10)**-2)).quantize(Decimal(10)**-2)

                        if FACTURACION_CON_IVA:
                            totalsim=Decimal(totalim / Decimal(COEFICIENTE_CALCULO_BASE_IMPONIBLE).quantize(Decimal(10)**-2)).quantize(Decimal(10)**-2)
                            valorimp =Decimal(totalim - totalsim).quantize(Decimal(10)**-2)
                            totalim = totalsim
                    precioUnitario = SubElement(detalle,'precioUnitario')
                    precioUnitario.text = str(totalim)
                    descuento = SubElement(detalle,'descuento')
                    descuento.text = '0.00'
                    precioTotalSinImpuesto = SubElement(detalle,'precioTotalSinImpuesto')
                    precioTotalSinImpuesto.text = str(totalim)
                    impuestos = SubElement(detalle,'impuestos')
                    impuesto = SubElement(impuestos,'impuesto')
                    codigo = SubElement(impuesto,'codigo')
                    codigo.text = '2'

                    codigoPorcentaje = SubElement(impuesto, 'codigoPorcentaje')
                    iva='0.00'
                    if FACTURACION_CON_IVA:
                        codigoPorcentaje.text = '2'
                        iva=str(int(Decimal(IVA_FACTU_ELECTRONICA)))
                    else:
                        codigoPorcentaje.text = '0'
                    tarifa = SubElement(impuesto,'tarifa')
                    tarifa.text = iva
                    baseImponible = SubElement(impuesto,'baseImponible')
                    baseImponible.text = str(Decimal(totalim).quantize(Decimal(10)**-2))
                    valor = SubElement(impuesto,'valor')
                    valor.text = str(Decimal(valorimp).quantize((Decimal(10)**-2)))
                    # ficheroats = open(os.path.join(ATS_PATH, 'FAC'+str(facturaenv.numero)+str(mes).zfill(2)+str(anno)+'.xml'), 'w')
                    #
                    #
                    # ficheroats.write('<?xml version="1.0" encoding="UTF-8" ?>')
                    # ficheroats.write(tostring(factura).decode())
                    # ficheroats.close()
                    # var = 'media/comprobantes/'+'FAC'+str(facturaenv.numero)+str(mes).zfill(2)+str(datetime.datetime.today().year)+'.xml'
                    try:
                        # CONSUMIR WEB SERVICES PARA FIRMA
                        recepcion = 'NO FIRMADO'
                        i=0
                        docume =''
                        while ( i < 5):
                            try:
                                docume = Client(URL_WEBSERVICE_FIRMA).service.xml(ElementTree.tostring(factura).decode())
                                i=5
                            except Exception as ex:
                                i = i+1
                                if i==5:
                                   if EMAIL_ACTIVE:
                                        fact= str(facturaenv.numero)
                                        mail_errores_autorizacion(recepcion,'EL DOCUMENTO NO FUE ENVIADO A FIRMAR PROBLEMAS CON EL WEBSERVICE ERROR'+str(ex),fact)
                                        break
                                pass
                        archi=ElementTree.tostring(Element(docume), 'utf-8').decode()
                        archi = ''.join(archi.split("<",1))
                        archi = archi.replace(" />",'')
                        arch = base64.encodebytes(archi.encode('utf-8')).decode()
                        # /////////NUEVO OFFLINE/////////
                        ficheroats = open(os.path.join(ATS_PATH, str(clave)+'.xml'), 'w')
                        # # ficheroats.write(prettify(factura))
                        ficheroats.write((archi))
                        ficheroats.close()
                        dirfactur = str(DIR_COMPRO+str(clave)+'.xml')
                        facturaenv.dirfactura=dirfactur
                        facturaenv.claveacceso=clave
                        facturaenv.numautorizacion=clave
                        facturaenv.fechaautorizacion=datetime.datetime.now()
                        facturaenv.save()
                        recepcion = 'NO ENVIADOVALI'
                        i=0
                        comprobar=''

                        while (i < 5):
                            try:
                                # ssl.wrap_socket = sslwrap(ssl.wrap_socket)
                                headers = {'Content-Type': 'application/soap+xml; charset="UTF-8"'}
                                client = Client('https://cel.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantesOffline?wsdl')
                                # client = Client('https://celcer.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantesOffline?wsdl',headers=headers)
                                # try:
                                comprobar = client.service.validarComprobante(arch)
                                # except Exception as ex:
                                #     mail_errores_autorizacion(str(ex),'EL DOCUMENTO NO FUE ENVIADO A VALIDAR PROBLEMAS CON EL SRI',facturaenv.numero)
                                i=5
                            except Exception as ex:
                                print('ERROR CONSUMO WEBSERVICE SRI '+str(ex))
                                i = i+1
                                if i==5:
                                   if EMAIL_ACTIVE:
                                        fact= str(facturaenv.numero)
                                        mail_errores_autorizacion(recepcion,'EL DOCUMENTO NO FUE ENVIADO A VALIDAR PROBLEMAS CON EL SRI '+str(ex),fact)
                                pass
                        # VALIDACIONES Y VARIABLE DE MENSAJES SI ENVIAN Y RECEPTA INFORMACION DESDE EL WEB SERVICE
                        if comprobar.estado == 'DEVUELTA':
                            recepcion = 'DEVUELTA'
                            mensajerecep='DEVUELTA'

                            try:
                                if str(comprobar['comprobantes'].comprobante[0]['mensajes']['mensaje'][0].identificador) == '70' or (str(comprobar['comprobantes'].comprobante[0]['mensajes']['mensaje'][0].identificador) == '43'):
                                   recepcion = 'NO ENVIADOAUT'
                                mensajerecep ='Codigo de Error '+comprobar['comprobantes'].comprobante[0]['mensajes']['mensaje'][0].identificador+' '+comprobar['comprobantes'].comprobante[0]['mensajes']['mensaje'][0].informacionAdicional
                            except:
                                mensajerecep ='Codigo de Error '+comprobar['comprobantes'].comprobante[0]['mensajes']['mensaje'][0].identificador+' mensaje '+\
                                              comprobar['comprobantes'].comprobante[0]['mensajes']['mensaje'][0].mensaje
                                if comprobar['comprobantes'].comprobante[0]['mensajes']['mensaje'][0].mensaje == 'CLAVE ACCESO REGISTRADA':
                                    recepcion = 'CLAVE ACCESO REGISTRADA'
                                    mensajerecep='CLAVE ACCESO REGISTRADA'
                                pass
                            if 'CLAVE ACCESO REGISTRADA' in comprobar['comprobantes'].comprobante[0]['mensajes']['mensaje'][0].mensaje:
                                if Factura.objects.filter(numero= facturaenv.numero).count()>1:
                                    mail_errores_autorizacion("FACTURA REPETIDA "+DEFAULT_PASSWORD,"Existe mas de una factura repetida verificar en factura",facturaenv.numero)
                            if EMAIL_ACTIVE:
                                if recepcion != 'NO ENVIADOAUT':
                                    mail_errores_autorizacion(recepcion,mensajerecep,facturaenv.numero)
                        else:
                            try:
                                if EMAIL_ACTIVE:
                                    mail_autorizacion(facturaenv.cliente.correo,facturaenv.numero)
                            except:
                                pass
                            recepcion = 'NO ENVIADOAUT'
                            respuesta_autorizacion = ''
                            i=0
                            while ( i < 5):
                                try:
                                    headers = {'Content-Type': 'application/soap+xml+json; charset="UTF-8"'}
                                    clie = Client('https://cel.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantesOffline?wsdl')
                                    # clie = Client('https://cel.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantesOffline?wsdl')
                                    try:
                                        respuesta_autorizacion = clie.service.autorizacionComprobante(clave)
                                    except Exception as ex:
                                        if EMAIL_ACTIVE:
                                            fact= facturaenv.numero
                                            mail_errores_autorizacion(recepcion,'EL ERROR EN AUTORIZACOMPROBANTE'+str(ex),facturaenv.numero)
                                    i=5
                                except:
                                    i = i+1
                                    if i==5:
                                        if EMAIL_ACTIVE:
                                            fact= facturaenv.numero
                                            # mail_errores_autorizacion(recepcion,'EL DOCUMENTO NO FUE ENVIADO A AUTORIZAR PROBLEMAS CON EL SRI',fact)
                                    pass

                            autorizacion = Element('autorizacion')

                            estado=SubElement(autorizacion, 'estado')
                            try:
                                estado.text = str(respuesta_autorizacion['autorizaciones'].autorizacion[0].estado)
                            except Exception as ex:
                            #     mail_errores_autorizacion('Error',str(ex),facturaenv.numero)
                                if EMAIL_ACTIVE:
                                    fact= str(facturaenv.numero)
                            if estado.text == 'AUTORIZADO':
                                numeroAutorizacion = SubElement(autorizacion, 'numeroAutorizacion')
                                numeroAutorizacion.text= str(respuesta_autorizacion['autorizaciones'].autorizacion[0].numeroAutorizacion)
                                recepcion = 'AUTORIZADO'
                                dirfactur = str(DIR_COMPRO+str(clave)+'.xml')
                                numautorizacion = str(respuesta_autorizacion['autorizaciones'].autorizacion[0].numeroAutorizacion)
                                fechautorizacion = str(str(respuesta_autorizacion['autorizaciones'].autorizacion[0]['fechaAutorizacion']))
                            else:
                                recepcion = 'NO ENVIADOAUT'

                            fechaAutorizacion = SubElement(autorizacion, 'fechaAutorizacion')
                            fechaAutorizacion.set('class', 'fechaAutorizacion')
                            fechaAutorizacion.text= str(respuesta_autorizacion['autorizaciones'].autorizacion[0]['fechaAutorizacion'].date()).split('-')[2]+'/'+str(respuesta_autorizacion['autorizaciones'].autorizacion[0]['fechaAutorizacion'].date()).split('-')[1]+'/'+str(respuesta_autorizacion['autorizaciones'].autorizacion[0]['fechaAutorizacion'].date()).split('-')[0]+' '+str(respuesta_autorizacion['autorizaciones'].autorizacion[0]['fechaAutorizacion'].time())
                            ambiente = SubElement(autorizacion, 'ambiente')
                            ambiente.text= AMBIENTE_DESCRIPCION
                            comprobante = SubElement(autorizacion, 'comprobante')
                            # cdata = CDATA(archi)
                            comprobante.text=archi
                            # elem = SubElement(comprobante, '![CDATA[')
                            # elem.text = archi
                            try:
                                r=respuesta_autorizacion['autorizaciones'].autorizacion[0]['mensajes'].mensaje
                                mensajes = SubElement(autorizacion, 'mensajes')
                                mensaje = SubElement(mensajes, 'mensaje')
                                c=0
                                for mensajeaut in respuesta_autorizacion['autorizaciones'].autorizacion[0]['mensajes'].mensaje:
                                    if c+1== 1 and estado.text != 'AUTORIZADO' :
                                        mensajerecep= mensajeaut.mensaje
                                        c=c+1
                                        if EMAIL_ACTIVE:
                                            menad='NO AUTORIZADO'
                                            try:
                                                menad= mensajeaut.informacionAdicional
                                            except:
                                                pass
                                            if mensajerecep != 'FIRMA INVALIDA':
                                                mail_errores_autorizacion(mensajeaut.mensaje,menad,facturaenv.numero)

                                    mensaje1 = SubElement(mensaje, 'mensaje')
                                    identificador = SubElement(mensaje1, 'identificador')
                                    identificador.text= mensajeaut.identificador
                                    mensaje2 = SubElement(mensaje1, 'mensaje')
                                    mensaje2.text= mensajeaut.mensaje
                                    tipo = SubElement(mensaje1, 'tipo')
                                    tipo.text= mensajeaut.tipo

                            except:
                                pass
                            # tipoEmision.text = str(EMISION_ELECTRONICA)
                            ficheroats = open(os.path.join(ATS_PATH, str(clave)+'.xml'), 'w')
                            ficheroats.write('<?xml version="1.0" encoding="UTF-8" ?>')
                            # ficheroats.write(prettify(factura))
                            ficheroats.write(tostring(autorizacion).decode())
                            ficheroats.close()
                        if EMAIL_ACTIVE:
                            mail_autorizacion(facturaenv.cliente.correo,facturaenv.numero)
                    except:
                        if recepcion == 'NO ENVIADOVALI' and facturaenv.id != 296339 :
                            fecha1=datetime.datetime.strptime(str(str(fecha).split("-")[0]+'/'+str(fecha).split("-")[1]+'/'+str(fecha).split("-")[2]),'%d/%m/%Y')  + datetime.timedelta(days=1)
                            if fecha1 < datetime.datetime.today():
                                if EMAIL_ACTIVE:
                                    fact= str(facturaenv.numero)
                                    mail_errores_autorizacion(recepcion,'FACTURA: EL DOCUMENTO NO FUE ENVIADO A VALIDAR PROBLEMAS CON EL SRI...... ',fact)
                        pass
                    # if mensajerecep != 'CLAVE ACCESO REGISTRADA':
                    facturaenv.estado = recepcion
                    facturaenv.mensaje = mensajerecep
                    facturaenv.dirfactura =  dirfactur
                    facturaenv.numautorizacion =  numautorizacion
                    if fechautorizacion != '':
                        facturaenv.fechaautorizacion =  fechautorizacion
                    facturaenv.claveacceso =  clave
                    facturaenv.save()

                except Exception as ex:
                    mail_errores_autorizacion('Error desde la excepcion',str(ex),facturaenv.numero)
                    pass

            else:
                try:
                    recepcion = 'NO ENVIADOAUT'
                    mensajerecep = ''
                    respuesta_autorizacion = ''
                    invoice = representacion_factura_str1(facturaenv)
                    fecha = invoice['fecha']
                    dia = fecha[:2]
                    mes = fecha[3:5]
                    anno = fecha[-4:]
                    empresa = TituloInstitucion.objects.get(pk=CODIGO_INFORMACION_INSTITUTO)
                    lugar = LugarRecaudacion.objects.get(id=facturaenv.caja_id)
                    clave= dia+mes+str(anno)+'01'+empresa.ruc+str(AMBIENTE_FACTURACION)\
                           +str(facturaenv.numero.strip().split("-")[0])+str(facturaenv.numero.strip().split("-")[1])\
                           +str(facturaenv.numero.strip().split("-")[2])+CODIGO_NUMERICO_ELEC+str(EMISION_ELECTRONICA)

                    pivote = 7
                    b=1
                    cantidadTotal=0
                    c=0
                    while ( c < len(clave)):

                        if pivote == 1:
                            pivote = 7

                        temporal = int(clave[c])
                        c = c+ 1
                        temporal *= pivote
                        pivote = pivote-1
                        cantidadTotal += temporal

                    cantidadTotal = 11 - (cantidadTotal % 11)
                    if cantidadTotal == 10:
                        cantidadTotal= 1
                    if cantidadTotal == 11:
                        cantidadTotal= 0
                    clave=clave + str(cantidadTotal)
                    i=0
                    while ( i < 5):
                        try:
                            # ssl.wrap_socket = sslwrap(ssl.wrap_socket)
                            headers = {'Content-Type': 'application/soap+xml+json; charset="UTF-8"'}
                            clie = Client('https://cel.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantesOffline?wsdl')
                            # clie = Client('https://cel.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantesOffline?wsdl')
                            respuesta_autorizacion = clie.service.autorizacionComprobante (clave)
                            i=5
                        except:
                            i = i+1
                            if i==5:
                                if EMAIL_ACTIVE:
                                    fact= str(facturaenv.numero)
                                    # mail_errores_autorizacion(recepcion,'EL DOCUMENTO NO FUE ENVIADO A AUTORIZAR PROBLEMAS CON EL SRI',fact)
                            pass

                    autorizacion = Element('autorizacion')

                    estado=SubElement(autorizacion, 'estado')
                    try:
                        estado.text = str(respuesta_autorizacion['autorizaciones'].autorizacion[0].estado)
                    except:
                        if EMAIL_ACTIVE:
                            fact= str(facturaenv.numero)
                            # mail_errores_autorizacion(recepcion,'EL DOCUMENTO NO FUE ENVIADO A AUTORIZAR PROBLEMAS CON EL SRI',fact)
                    # estado.text = str(respuesta_autorizacion['autorizaciones'].autorizacion[0].estado)
                    if estado.text == 'AUTORIZADO':
                        numeroAutorizacion = SubElement(autorizacion, 'numeroAutorizacion')
                        numeroAutorizacion.text= str(respuesta_autorizacion['autorizaciones'].autorizacion[0].numeroAutorizacion)
                        recepcion = 'AUTORIZADO'
                        dirfactur = str(DIR_COMPRO+str(clave)+'.xml')
                        numautorizacion = str(respuesta_autorizacion['autorizaciones'].autorizacion[0].numeroAutorizacion)
                        fechautorizacion = str(respuesta_autorizacion['autorizaciones'].autorizacion[0]['fechaAutorizacion'])
                        if EMAIL_ACTIVE:
                            mail_autorizacion(facturaenv.cliente.correo,facturaenv.numero)
                    else:
                        recepcion = 'NO ENVIADOAUT'
                        fecha1=datetime.datetime.strptime(str(str(fecha).split("-")[0]+'/'+str(fecha).split("-")[1]+'/'+str(fecha).split("-")[2]),'%d/%m/%Y')  + datetime.timedelta(days=2)
                        if fecha1 < datetime.datetime.today():
                           recepcion = 'NO ENVIADO'
                    fechaAutorizacion = SubElement(autorizacion, 'fechaAutorizacion')
                    fechaAutorizacion.set('class', 'fechaAutorizacion')
                    fechaAutorizacion.text= str(respuesta_autorizacion['autorizaciones'].autorizacion[0]['fechaAutorizacion'].date()).split('-')[2]+'/'+str(respuesta_autorizacion['autorizaciones'].autorizacion[0]['fechaAutorizacion'].date()).split('-')[1]+'/'+str(respuesta_autorizacion['autorizaciones'].autorizacion[0]['fechaAutorizacion'].date()).split('-')[0]+' '+str(respuesta_autorizacion['autorizaciones'].autorizacion[0]['fechaAutorizacion'].time())
                    ambiente = SubElement(autorizacion, 'ambiente')
                    ambiente.text= AMBIENTE_DESCRIPCION
                    comprobante = SubElement(autorizacion, 'comprobante')
                    # cdata = CDATA(archi)
                    comprobante.text= str(respuesta_autorizacion['autorizaciones'].autorizacion[0].comprobante)
                    # elem = SubElement(comprobante, '![CDATA[')
                    # elem.text = archi
                    mensajes = SubElement(autorizacion, 'mensajes')
                    mensaje = SubElement(mensajes, 'mensaje')
                    c=0
                    try:
                        for mensajeaut in respuesta_autorizacion['autorizaciones'].autorizacion[0]['mensajes'].mensaje:
                            if c+1== 1 and estado.text != 'AUTORIZADO' :
                                mensajerecep= mensajeaut.mensaje
                                c=c+1
                                if EMAIL_ACTIVE:
                                    menad=''
                                    try:
                                        menad= mensajeaut.informacionAdicional
                                    except:
                                        pass
                                    if mensajerecep != 'FIRMA INVALIDA':
                                        mail_errores_autorizacion(mensajeaut.mensaje,menad,facturaenv.numero)

                            mensaje1 = SubElement(mensaje, 'mensaje')
                            identificador = SubElement(mensaje1, 'identificador')
                            identificador.text= mensajeaut.identificador
                            mensaje2 = SubElement(mensaje1, 'mensaje')
                            mensaje2.text= mensajeaut.mensaje
                            tipo = SubElement(mensaje1, 'tipo')
                            tipo.text= mensajeaut.tipo
                    except:
                        pass

                    # tipoEmision.text = str(EMISION_ELECTRONICA)
                    ficheroats = open(os.path.join(ATS_PATH, str(clave)+'.xml'), 'w')
                    ficheroats.write('<?xml version="1.0" encoding="UTF-8" ?>')
                    # ficheroats.write(prettify(factura))
                    ficheroats.write(tostring(autorizacion).decode())
                    ficheroats.close()
                    # facturaenv.estado = recepcion
                    # facturaenv.mensaje = mensajerecep
                    # facturaenv.dirfactura =  dirfactur
                    # facturaenv.save()
                except:
                    pass
                # if mensajerecep != 'CLAVE ACCESO REGISTRADA':
                if mensajerecep=='FIRMA INVALIDA':
                     recepcion = 'NO ENVIADO'


                facturaenv.estado = recepcion
                facturaenv.mensaje = mensajerecep
                facturaenv.dirfactura =  dirfactur
                facturaenv.numautorizacion =  numautorizacion
                if fechautorizacion != '':
                        facturaenv.fechaautorizacion =  fechautorizacion
                facturaenv.claveacceso =  clave
                facturaenv.save()


    facturas = Factura.objects.filter(mensaje='CLAVE ACCESO REGISTRADA',fecha__gte=FECHA_ELECT_FAC).order_by('id')
    for facturaenv in facturas:
        enviarmail = False
        recepcion = 'NO ENVIADOAUT'
        mensajerecep = ''
        respuesta_autorizacion = ''
        dirfactur=''
        numautorizacion = ''
        i=0
        try:
            while ( i < 5):
                try:
                    # ssl.wrap_socket = sslwrap(ssl.wrap_socket)
                    headers = {'Content-Type': 'application/soap+xml+json; charset="UTF-8"'}
                    clie = Client('https://cel.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantesOffline?wsdl')
                    # clie = Client('https://cel.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantesOffline?wsdl')
                    respuesta_autorizacion = clie.service.autorizacionComprobante(str(facturaenv.claveacceso))

                    i=5
                except Exception as ex:
                    i = i+1
                    if i==5:
                        if EMAIL_ACTIVE:
                            mail_errores_autorizacion(recepcion,'error salido por excepcion y numeros 10 '+str(ex),str(facturaenv.numero))
                            fact= str(facturaenv.numero)
                            fecha1=datetime.datetime.strptime(str(str(facturaenv.fecha).split("-")[2]+'/'+str(facturaenv.fecha).split("-")[1]+'/'+str(facturaenv.fecha).split("-")[0]),'%d/%m/%Y')  + datetime.timedelta(days=2)
                            if fecha1 < datetime.datetime.today():
                                fechdias = facturaenv.fecha + datetime.timedelta(days=5)
                                if datetime.datetime.today().date() > fechdias:
                                    facturaenv.mensaje = ''
                                    facturaenv.estado = 'NO'
                                    facturaenv.save()
                                mail_errores_autorizacion(recepcion,'EL DOCUMENTO NO FUE ENVIADO A AUTORIZAR PROBLEMAS CON EL SRI '+str(ex),fact)
                    pass
            for mensajeaut in respuesta_autorizacion['autorizaciones'].autorizacion:
                if mensajeaut.estado=='AUTORIZADO':
                    autorizacion = Element('autorizacion')

                    estado=SubElement(autorizacion, 'estado')
                    try:
                        estado.text =mensajeaut.estado
                    except:
                        if EMAIL_ACTIVE:
                            fact= str(facturaenv.numero)
                            # mail_errores_autorizacion(recepcion,'EL DOCUMENTO NO FUE ENVIADO A AUTORIZAR PROBLEMAS CON EL SRI',fact)
                    # estado.text = str(respuesta_autorizacion['autorizaciones'].autorizacion[0].estado)

                    numeroAutorizacion = SubElement(autorizacion, 'numeroAutorizacion')
                    numeroAutorizacion.text= mensajeaut.numeroAutorizacion
                    recepcion = 'AUTORIZADO'
                    dirfactur = str(DIR_COMPRO+str(facturaenv.claveacceso)+'.xml')
                    numautorizacion = mensajeaut.numeroAutorizacion
                    fechautorizacion = str(mensajeaut['fechaAutorizacion'])


                    fechaAutorizacion = SubElement(autorizacion, 'fechaAutorizacion')
                    fechaAutorizacion.set('class', 'fechaAutorizacion')
                    fechaAutorizacion.text= str(mensajeaut['fechaAutorizacion'].date()).split('-')[2]+'/'+str(mensajeaut['fechaAutorizacion'].date()).split('-')[1]+'/'+str(mensajeaut['fechaAutorizacion'].date()).split('-')[0]+' '+str(mensajeaut['fechaAutorizacion'].time())
                    ambiente = SubElement(autorizacion, 'ambiente')
                    ambiente.text= AMBIENTE_DESCRIPCION
                    comprobante = SubElement(autorizacion, 'comprobante')
                    # cdata = CDATA(archi)
                    # comprobante.text=open(SITE_ROOT+'/'+facturaenv.dirfactura).read()
                    comprobante.text=str(respuesta_autorizacion['autorizaciones'].autorizacion[0].comprobante)
                    # elem = SubElement(comprobante, '![CDATA[')
                    # elem.text = archi
                    try:
                        mensajes = SubElement(autorizacion, 'mensajes')
                        mensaje = SubElement(mensajes, 'mensaje')
                        mensaje1 = SubElement(mensaje, 'mensaje')
                        identificador = SubElement(mensaje1, 'identificador')
                        identificador.text= str(mensajeaut['mensajes'].mensaje[0].identificador)
                        mensaje2 = SubElement(mensaje1, 'mensaje')
                        mensaje2.text= str(mensajeaut['mensajes'].mensaje[0].mensaje)
                        tipo = SubElement(mensaje1, 'tipo')
                        tipo.text= str(mensajeaut['mensajes'].mensaje[0].tipo)
                    except:
                        pass


                    # tipoEmision.text = str(EMISION_ELECTRONICA)
                    enviarmail = True
                    ficheroats = open(os.path.join(ATS_PATH, str(facturaenv.claveacceso)+'.xml'), 'w')
                    ficheroats.write('<?xml version="1.0" encoding="UTF-8" ?>')
                    # ficheroats.write(prettify(factura))
                    ficheroats.write(tostring(autorizacion).decode())
                    ficheroats.close()
                    enviarmail = False
                    if mensajerecep=='FIRMA INVALIDA':
                        recepcion = 'NO ENVIADO'
                    facturaenv.estado = recepcion

                    facturaenv.mensaje = mensajerecep
                    facturaenv.dirfactura =  dirfactur
                    facturaenv.numautorizacion =  numautorizacion
                    if fechautorizacion != '':
                            facturaenv.fechaautorizacion =  fechautorizacion
                    facturaenv.save()

        except Exception as ex:
            if enviarmail and EMAIL_ACTIVE:
                mail_errores_autorizacion(recepcion,'NO SE GUARDO EL ARCHIVO '+str(ex),facturaenv.numero)
            pass






def notacreditoelectronica():

    notacreditos = NotaCreditoInstitucion.objects.filter(fecha__gte=FECHA_ELECT_FAC).exclude(estado=None).exclude(estado='AUTORIZADO').order_by('id')
    # notacreditos = NotaCreditoInstitucion.objects.filter(pk__in=[10857,10858,10859],fecha__gte=FECHA_ELECT_FAC).exclude(estado=None).exclude(estado='AUTORIZADO').order_by('id')
    dirnota = ''
    mensajerecep = ''
    recepcion = ''
    numautorizacion = ''
    fechautorizacion = ''
    clave = ''
    for notacreditoreen in notacreditos:
    # ///////////////////////////////////////////////////////////////XML FACTURACION ELECTRONICA///////////////////////////////////////////////////////////
    #/////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        # //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        # ///////////////////////////////////////////////////SECCION INFORMA CION TRIBUTARIA//////////////////////////////////////////////////////////////////////////////
        if notacreditoreen.mensaje != 'ERROR SECUENCIAL REGISTRADO' :
            if notacreditoreen.mensaje != 'CLAVE ACCESO REGISTRADA':
                if notacreditoreen.estado != 'NO ENVIADOAUT':
                    try:
                        factura= Factura.objects.get(id=notacreditoreen.factura.id)
                        lugar = LugarRecaudacion.objects.get(id=notacreditoreen.sesioncaja.caja_id)
                        notaCredito = Element('notaCredito')
                        notaCredito.set('id', 'comprobante')
                        notaCredito.set('version','1.0.0')

                        # comment = Comment('Generated for GIDTec ITB')
                        # iva.append(comment)

                        #ENCABEZADO  (Identificacion del Informante)
                        infoTributaria=SubElement(notaCredito, 'infoTributaria')
                        ambiente = SubElement(infoTributaria,'ambiente')
                        ambiente.text = str(AMBIENTE_FACTURACION)
                        tipoEmision = SubElement(infoTributaria, 'tipoEmision')
                        tipoEmision.text = str(EMISION_ELECTRONICA)

                        # ////////////////////SECCION DE INFORMACION DE EMPRESA/////////////
                        empresa = TituloInstitucion.objects.get(pk=CODIGO_INFORMACION_INSTITUTO)
                        razonSocial = SubElement(infoTributaria,'razonSocial')
                        razonSocial.text = elimina_tildes1(empresa.nombre)
                        if empresa.nombrecomercial:
                            nombreComercial = SubElement(infoTributaria,'nombreComercial')
                            nombreComercial.text = elimina_tildes1(empresa.nombrecomercial)
                        ruc = SubElement(infoTributaria,'ruc')
                        ruc.text = empresa.ruc

                        # ////////////////////TERMINO DE SECCION//////////////////////
                        # ////////////////////SECCION DE CLAVE DE ACCESO/////////////
                        # lugar = LugarRecaudacion.objects.
                        dia=str(notacreditoreen.fecha.day).zfill(2)
                        mes=str(notacreditoreen.fecha.month).zfill(2)
                        clave= dia+mes+str(notacreditoreen.fecha.year)+'04'+empresa.ruc+str(AMBIENTE_FACTURACION)\
                               +str(notacreditoreen.numero.strip().split("-")[0])+str(notacreditoreen.numero.strip().split("-")[1])\
                               +str(notacreditoreen.numero.strip().split("-")[2])+CODIGO_NUMERICO_ELEC+str(EMISION_ELECTRONICA)

                        pivote = 7
                        b=1
                        cantidadTotal=0
                        c=0
                        while ( c < len(clave)):

                            if pivote == 1:
                                pivote = 7

                            temporal = int(clave[c])
                            c = c+ 1
                            temporal *= pivote
                            pivote = pivote-1
                            cantidadTotal += temporal

                        cantidadTotal = 11 - (cantidadTotal % 11)
                        if cantidadTotal == 10:
                            cantidadTotal= 1
                        if cantidadTotal == 11:
                            cantidadTotal= 0
                        clave=clave + str(cantidadTotal)
                        claveAcceso = SubElement(infoTributaria,'claveAcceso')
                        claveAcceso.text=clave
                        # ////////////////////TERMINO DE SECCION/////////////
                        codDoc = SubElement(infoTributaria,'codDoc')
                        codDoc.text='04'
                        estab = SubElement(infoTributaria,'estab')
                        estab.text=str(lugar.puntoventa.strip().split("-")[0])
                        ptoEmi = SubElement(infoTributaria,'ptoEmi')
                        ptoEmi.text=str(lugar.puntoventa.strip().split("-")[1])
                        secuencial = SubElement(infoTributaria,'secuencial')
                        secuencial.text=str(notacreditoreen.numero.split("-")[2])

                        dirMatriz = SubElement(infoTributaria,'dirMatriz')
                        dirMatriz.text=elimina_tildes1(empresa.direccion)
                    # /////////////////////////////////////////////////////FIN DE SECCION/////////////////////////////////////////////////////////////////////////////
                    # ///////////////////////////////////////////////////SECCION INFORMACION DE FACTURA//////////////////////////////////////////////////////////////////////////////
                        infoNotaCredito=SubElement(notaCredito, 'infoNotaCredito')
                        fechaEmision = SubElement(infoNotaCredito,'fechaEmision')
                        fechaEmision.text =  str(str(notacreditoreen.fecha.day).zfill(2)+'/'+str(notacreditoreen.fecha.month).zfill(2)+'/'+str(notacreditoreen.fecha.year))
                        dirEstablecimiento = SubElement(infoNotaCredito, 'dirEstablecimiento')
                        dirEstablecimiento.text = elimina_tildes1(lugar.direccion)
                        # ///////////////////////////////////////////////////////
                        # //////////////////////////////CEDULA O PASAPORTE//////
                        if (len(factura.cliente.ruc))==13:
                            identificador='04'
                        else:
                            if (len(factura.cliente.ruc))==10:
                                identificador=IDENTIFICACION_COMPRADOR
                            else:
                                identificador = '06'
                        numerocomprador=factura.cliente.ruc
                        tipoIdentificacionComprador = SubElement(infoNotaCredito, 'tipoIdentificacionComprador')
                        tipoIdentificacionComprador.text = identificador
                        razonSocialComprador = SubElement(infoNotaCredito, 'razonSocialComprador')
                        razonSocialComprador.text = elimina_tildes1((factura.cliente.nombre))
                        identificacionComprador = SubElement(infoNotaCredito, 'identificacionComprador')
                        identificacionComprador.text = str(numerocomprador)
                        if DEFAULT_PASSWORD != 'itf':
                            contribuyenteEspecial = SubElement(infoNotaCredito, 'contribuyenteEspecial')
                            contribuyenteEspecial.text = str(empresa.contribu_especial)
                        obligadoContabilidad = SubElement(infoNotaCredito, 'obligadoContabilidad')
                        obligadoContabilidad.text = empresa.contabilidad
                        codDocModificado = SubElement(infoNotaCredito, 'codDocModificado')
                        codDocModificado.text = '01'
                        numDocModificado = SubElement(infoNotaCredito, 'numDocModificado')
                        numDocModificado.text = factura.numero.split('-')[0]+'-'+factura.numero.split('-')[1]+'-'+factura.numero.split('-')[2].zfill(9)
                        fechaEmisionDocSustento = SubElement(infoNotaCredito, 'fechaEmisionDocSustento')
                        fechaEmisionDocSustento.text = str(factura.fecha.day).zfill(2)+'/'+str(factura.fecha.month).zfill(2)+'/'+str(factura.fecha.year)
                        # /////////////////////////////TOTAL SINIMPUESTO////////////////

                        invoice = representacion_factura_str1(factura)
                        totalim=Decimal(0)
                        valorimp=Decimal(0)
                        # for pago in invoice['pagos']:
                        #     t = Decimal(pago['valor']).quantize(Decimal(10)**-2)
                        #     totalim= Decimal(t+totalim).quantize(Decimal(10)**-2)
                        totalim= Decimal(notacreditoreen.valor).quantize(Decimal(10)**-2)
                        if FACTURACION_CON_IVA:
                            valorimp=Decimal(totalim * Decimal(COEFICIENTE_CALCULO_BASE_IMPONIBLE).quantize(Decimal(10)**-2)).quantize(Decimal(10)**-2)
                            totalim =Decimal(totalim - valorimp).quantize(Decimal(10)**-2)

                        totalSinImpuestos = SubElement(infoNotaCredito, 'totalSinImpuestos')
                        totalSinImpuestos.text = str(totalim)
                        valorModificacion = SubElement(infoNotaCredito, 'valorModificacion')
                        valorModificacion.text = str(Decimal(notacreditoreen.valor).quantize(Decimal(10)**-2))
                        moneda = SubElement(infoNotaCredito, 'moneda')
                        moneda.text = empresa.moneda
                        totalConImpuestos = SubElement(infoNotaCredito, 'totalConImpuestos')
                        totalImpuesto = SubElement(totalConImpuestos, 'totalImpuesto')
                        codigo = SubElement(totalImpuesto, 'codigo')
                        codigo.text = '2'

                        codigoPorcentaje = SubElement(totalImpuesto, 'codigoPorcentaje')

                        if FACTURACION_CON_IVA:
                            codigoPorcentaje.text = '2'
                        else:
                            codigoPorcentaje.text = '0'
                        baseImponible = SubElement(totalImpuesto, 'baseImponible')
                        baseImponible.text = str(totalim)
                        valor = SubElement(totalImpuesto, 'valor')
                        valor.text = str(valorimp)
                    # ///////////////////////////////////////////////////SECCION DETALLE DE FACTURA//////////////////////////////////////////////////////////////////////////////
                        totalim=Decimal(0)
                        valorimp=Decimal(0)
                        detalles=SubElement(notaCredito, 'detalles')
                        detalle = ""
                        lista=[]
                        obj=[]
                        fact=model_to_dict(factura,exclude='fecha')
                        if notacreditoreen.tipo.id == TIPO_NC_ANULACION:
                            for pago in fact['pagos']:
                                pago = Pago.objects.get(pk=pago.id)
                                obj = model_to_dict(pago, exclude=['fecha', 'lugar', 'recibe','efectivo','id'])
                                rubro = Rubro.objects.get(pk=obj['rubro'])
                                if not rubro.id in lista :
                                    if len(lista)>0:
                                        if FACTURACION_CON_IVA:
                                            valorimp=Decimal(totalim * Decimal(COEFICIENTE_CALCULO_BASE_IMPONIBLE).quantize(Decimal(10)**-2)).quantize(Decimal(10)**-2)
                                            totalim =Decimal(totalim - valorimp).quantize(Decimal(10)**-2)
                                        precioUnitario = SubElement(detalle,'precioUnitario')
                                        precioUnitario.text = str(totalim)
                                        descuento = SubElement(detalle,'descuento')
                                        descuento.text = '0.00'
                                        precioTotalSinImpuesto = SubElement(detalle,'precioTotalSinImpuesto')
                                        precioTotalSinImpuesto.text = str(totalim)
                                        impuestos = SubElement(detalle,'impuestos')
                                        impuesto = SubElement(impuestos,'impuesto')
                                        codigo = SubElement(impuesto,'codigo')
                                        codigo.text = '2'

                                        codigoPorcentaje = SubElement(impuesto, 'codigoPorcentaje')
                                        iva='0.00'
                                        if FACTURACION_CON_IVA:
                                            codigoPorcentaje.text = '2'
                                            iva=IVA_FACTU_ELECTRONICA
                                        else:
                                            codigoPorcentaje.text = '0'
                                        tarifa = SubElement(impuesto,'tarifa')
                                        tarifa.text = iva
                                        baseImponible = SubElement(impuesto,'baseImponible')
                                        baseImponible.text = str(totalim)
                                        valor = SubElement(impuesto,'valor')
                                        valor.text = str(valorimp)
                                        totalim=Decimal(0)
                                        valorimp=Decimal(0)

                                    lista.append(rubro.id)
                                    # rubro = Rubro.objects.get(pk=rubro.id)
                                    detalle = SubElement(detalles,'detalle')
                                    codigoInterno = SubElement(detalle,'codigoInterno')
                                    codigoInterno.text = str(rubro.id)
                                    descripcion = SubElement(detalle,'descripcion')
                                    if len(str(elimina_tildes1(rubro.nombre())))-1 == str(elimina_tildes1(rubro.nombre())).rfind("\n"):
                                        descripcion.text = str(str(elimina_tildes1(rubro.nombre()))[0:len(str(rubro.nombre()))-1].replace("\n",''))
                                    else:
                                        descripcion.text = str(str(elimina_tildes1((rubro.nombre()))).replace("\n",' '))
                                    # descripcion.text = elimina_tildes1((rubro.nombre()))
                                    cantidad = SubElement(detalle,'cantidad')
                                    cantidad.text = '1'
                                totalim=(totalim+Decimal(pago.valor).quantize(Decimal(10)**-2)).quantize(Decimal(10)**-2)
                        else:
                            for detallrubro in DetalleNotacredDevol.objects.filter(notacredito=notacreditoreen):
                                rubro = detallrubro.rubro
                                if not rubro.id in lista :
                                    if len(lista)>0:
                                        if FACTURACION_CON_IVA:
                                            valorimp=Decimal(totalim * Decimal(COEFICIENTE_CALCULO_BASE_IMPONIBLE).quantize(Decimal(10)**-2)).quantize(Decimal(10)**-2)
                                            totalim =Decimal(totalim - valorimp).quantize(Decimal(10)**-2)
                                        precioUnitario = SubElement(detalle,'precioUnitario')
                                        precioUnitario.text = str(totalim)
                                        descuento = SubElement(detalle,'descuento')
                                        descuento.text = '0.00'
                                        precioTotalSinImpuesto = SubElement(detalle,'precioTotalSinImpuesto')
                                        precioTotalSinImpuesto.text = str(totalim)
                                        impuestos = SubElement(detalle,'impuestos')
                                        impuesto = SubElement(impuestos,'impuesto')
                                        codigo = SubElement(impuesto,'codigo')
                                        codigo.text = '2'

                                        codigoPorcentaje = SubElement(impuesto, 'codigoPorcentaje')
                                        iva='0.00'
                                        if FACTURACION_CON_IVA:
                                            codigoPorcentaje.text = '2'
                                            iva=IVA_FACTU_ELECTRONICA
                                        else:
                                            codigoPorcentaje.text = '0'
                                        tarifa = SubElement(impuesto,'tarifa')
                                        tarifa.text = iva
                                        baseImponible = SubElement(impuesto,'baseImponible')
                                        baseImponible.text = str(totalim)
                                        valor = SubElement(impuesto,'valor')
                                        valor.text = str(valorimp)
                                        totalim=Decimal(0)
                                        valorimp=Decimal(0)

                                    lista.append(rubro.id)
                                    # rubro = Rubro.objects.get(pk=rubro.id)
                                    detalle = SubElement(detalles,'detalle')
                                    codigoInterno = SubElement(detalle,'codigoInterno')
                                    codigoInterno.text = str(rubro.id)
                                    descripcion = SubElement(detalle,'descripcion')
                                    if len(str(elimina_tildes1(rubro.nombre())))-1 == str(elimina_tildes1(rubro.nombre())).rfind("\n"):
                                        descripcion.text = str(str(elimina_tildes1(rubro.nombre()))[0:len(str(rubro.nombre()))-1].replace("\n",''))
                                    else:
                                        descripcion.text = str(str(elimina_tildes1((rubro.nombre()))).replace("\n",' '))
                                    # descripcion.text = elimina_tildes1((rubro.nombre()))
                                    cantidad = SubElement(detalle,'cantidad')
                                    cantidad.text = '1'
                                totalim=(totalim+Decimal(detallrubro.valor).quantize(Decimal(10)**-2)).quantize(Decimal(10)**-2)

                        if FACTURACION_CON_IVA:
                            valorimp=Decimal(totalim * Decimal(COEFICIENTE_CALCULO_BASE_IMPONIBLE).quantize(Decimal(10)**-2)).quantize(Decimal(10)**-2)
                            totalim =Decimal(totalim - valorimp).quantize(Decimal(10)**-2)
                        precioUnitario = SubElement(detalle,'precioUnitario')
                        precioUnitario.text = str(totalim)
                        descuento = SubElement(detalle,'descuento')
                        descuento.text = '0.00'
                        precioTotalSinImpuesto = SubElement(detalle,'precioTotalSinImpuesto')
                        precioTotalSinImpuesto.text = str(totalim)
                        impuestos = SubElement(detalle,'impuestos')
                        impuesto = SubElement(impuestos,'impuesto')
                        codigo = SubElement(impuesto,'codigo')
                        codigo.text = '2'

                        codigoPorcentaje = SubElement(impuesto, 'codigoPorcentaje')
                        iva='0.00'
                        if FACTURACION_CON_IVA:
                            codigoPorcentaje.text = '2'
                            iva=IVA_FACTU_ELECTRONICA
                        else:
                            codigoPorcentaje.text = '0'
                        tarifa = SubElement(impuesto,'tarifa')
                        tarifa.text = iva
                        baseImponible = SubElement(impuesto,'baseImponible')
                        baseImponible.text = str(Decimal(totalim).quantize(Decimal(10)**-2))
                        valor = SubElement(impuesto,'valor')
                        valor.text = str(Decimal(valorimp).quantize((Decimal(10)**-2)))
                        motivo = SubElement(infoNotaCredito,'motivo')
                        motivo.text = elimina_tildes1((notacreditoreen.motivo))


                        # ficheroats = open(os.path.join(ATS_PATH, 'NC'+str(notacreditoreen.numero)+str(mes).zfill(2)+str(notacreditoreen.fecha.year)+'.xml'), 'w')
                        # ficheroats.write('<?xml version="1.0" encoding="UTF-8" ?>')
                        # ficheroats.write(tostring(notaCredito))
                        # ficheroats.close()

                        try:
                            # CONSUMIR WEB SERVICES PARA FIRMA
                            recepcion = 'NO FIRMADO'
                            i=0
                            docume =''
                            while ( i < 5):
                                try:
                                    docume = Client(URL_WEBSERVICE_FIRMA).service.xml(ElementTree.tostring(notaCredito).decode())
                                    i=5
                                except:
                                    i = i+1
                                    if i==5:
                                       if EMAIL_ACTIVE:
                                            fact= str(notacreditoreen.numero)
                                            mail_errores_autorizacion(recepcion,'EL DOCUMENTO NO FUE ENVIADO A FIRMAR PROBLEMAS CON EL WEBSERVICE',fact)
                                    pass
                            archi=ElementTree.tostring(Element(docume), 'utf-8').decode()
                            archi = ''.join(archi.split("<",1))
                            archi = archi.replace(" />",'')
                            arch = base64.encodebytes(archi.encode('utf-8')).decode()
                            # ////////////NUEVO OFFLINE ///////////////

                            ficheroats = open(os.path.join(ATS_PATH, str(clave)+'.xml'), 'w')
                            # # ficheroats.write(prettify(factura))
                            ficheroats.write((archi))
                            ficheroats.close()
                            dirnota = str(DIR_COMPRO+str(clave)+'.xml')
                            notacreditoreen.dirnotacredito = dirnota
                            notacreditoreen.claveacceso = clave
                            notacreditoreen.numautorizacion = clave
                            notacreditoreen.fechaautorizacion = datetime.datetime.now()
                            notacreditoreen.save()

                            recepcion = 'NO ENVIADOVALI'
                            i=0
                            comprobar=''

                            while ( i < 5):
                                try:
                                    try:
                                        if EMAIL_ACTIVE:
                                            if notacreditoreen.inscripcion:
                                                mail_autorizacion(notacreditoreen.inscripcion.persona.emailinst,str(notacreditoreen.numero))
                                            else:
                                                mail_autorizacion(notacreditoreen.fichamedica.email,str(notacreditoreen.numero))
                                    except:
                                        pass
                                    # ssl.wrap_socket = sslwrap(ssl.wrap_socket)
                                    client = Client('https://cel.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantesOffline?wsdl')
                                    comprobar = client.service.validarComprobante(arch)
                                    i=5
                                except:
                                    i = i+1
                                    if i==5:
                                       if EMAIL_ACTIVE:
                                            fact=str(notacreditoreen.numero)
                                            # mail_errores_autorizacion(recepcion,'EL DOCUMENTO NO FUE ENVIADO A VALIDAR PROBLEMAS CON EL SRI',fact)
                                    pass
                            # VALIDACIONES Y VARIABLE DE MENSAJES SI ENVIAN Y RECEPTA INFORMACION DESDE EL WEB SERVICE
                            if comprobar.estado == 'DEVUELTA':
                                recepcion = 'DEVUELTA'
                                try:
                                    if (str(comprobar['comprobantes'].comprobante[0]['mensajes']['mensaje'][0].identificador) == '70') or (str(comprobar['comprobantes'].comprobante[0]['mensajes']['mensaje'][0].identificador) == '43'):
                                       recepcion = 'NO ENVIADOAUT'
                                    mensajerecep = 'Codigo de Error '+comprobar['comprobantes'].comprobante[0]['mensajes']['mensaje'][0].identificador+' '+comprobar['comprobantes'].comprobante[0]['mensajes']['mensaje'][0].informacionAdicional
                                except:
                                    mensajerecep ='Codigo de Error '+comprobar['comprobantes'].comprobante[0]['mensajes']['mensaje'][0].identificador+' mensaje '+\
                                                  comprobar['comprobantes'].comprobante[0]['mensajes']['mensaje'][0].mensaje
                                    if mensajerecep == 'CLAVE ACCESO REGISTRADA':
                                        recepcion = 'CLAVE ACCESO REGISTRADA'
                                    pass
                                if 'CLAVE ACCESO REGISTRADA' in comprobar['comprobantes'].comprobante[0]['mensajes']['mensaje'][0].mensaje:
                                    if NotaCreditoInstitucion.objects.filter(numero= fact).count()>1:
                                        mail_errores_autorizacion("NOTA CREDITO REPETIDA "+DEFAULT_PASSWORD,"Existe mas de una nota de credito repetida verificar",fact)
                                if EMAIL_ACTIVE:
                                    if recepcion != 'NO ENVIADOAUT':
                                        fact= str(notacreditoreen.numero)
                                        mail_errores_autorizacion(recepcion,mensajerecep,fact)
                            else:
                                recepcion = 'NO ENVIADOAUT'
                                respuesta_autorizacion = ''
                                i=0
                                while ( i < 5):
                                    try:
                                        headers = {'Content-Type': 'application/soap+xml+json; charset="UTF-8"'}
                                        clie = Client('https://cel.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantesOffline?wsdl')
                                        # clie = Client('https://cel.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantesOffline?wsdl')
                                        respuesta_autorizacion = clie.service.autorizacionComprobante (clave)
                                        i=5
                                    except:
                                        i = i+1
                                        if i==5:
                                            if EMAIL_ACTIVE:
                                                fact= str(notacreditoreen.numero)
                                                # mail_errores_autorizacion(recepcion,'EL DOCUMENTO NO FUE ENVIADO A AUTORIZAR PROBLEMAS CON EL SRI',fact)
                                        pass

                                # autorizacion = Element('autorizacion')

                                autorizacion = Element('autorizacion')

                                estado=SubElement(autorizacion, 'estado')
                                estado.text = str(respuesta_autorizacion['autorizaciones'].autorizacion[0].estado)
                                if estado.text == 'AUTORIZADO':
                                    numeroAutorizacion = SubElement(autorizacion, 'numeroAutorizacion')
                                    numeroAutorizacion.text= str(respuesta_autorizacion['autorizaciones'].autorizacion[0].numeroAutorizacion)
                                    recepcion = 'AUTORIZADO'
                                    dirnota = str(DIR_COMPRO+str(clave)+'.xml')
                                    numautorizacion = str(respuesta_autorizacion['autorizaciones'].autorizacion[0].numeroAutorizacion)
                                    fechautorizacion = str(respuesta_autorizacion['autorizaciones'].autorizacion[0]['fechaAutorizacion'])

                                else:
                                    recepcion = 'NO ENVIADOAUT'


                                fechaAutorizacion = SubElement(autorizacion, 'fechaAutorizacion')
                                fechaAutorizacion.set('class', 'fechaAutorizacion')
                                fechaAutorizacion.text= str(respuesta_autorizacion['autorizaciones'].autorizacion[0]['fechaAutorizacion'].date()).split('-')[2]+'/'+str(respuesta_autorizacion['autorizaciones'].autorizacion[0]['fechaAutorizacion'].date()).split('-')[1]+'/'+str(respuesta_autorizacion['autorizaciones'].autorizacion[0]['fechaAutorizacion'].date()).split('-')[0]+' '+str(respuesta_autorizacion['autorizaciones'].autorizacion[0]['fechaAutorizacion'].time())
                                ambiente = SubElement(autorizacion, 'ambiente')
                                ambiente.text= AMBIENTE_DESCRIPCION
                                comprobante = SubElement(autorizacion, 'comprobante')
                                # cdata = CDATA(archi)
                                comprobante.text=archi
                                # elem = SubElement(comprobante, '![CDATA[')
                                # elem.text = archi
                                mensajes = SubElement(autorizacion, 'mensajes')
                                mensaje = SubElement(mensajes, 'mensaje')
                                c=0
                                try:
                                    for mensajeaut in respuesta_autorizacion['autorizaciones'].autorizacion[0]['mensajes'].mensaje:
                                        if c+1== 1 and estado.text != 'AUTORIZADO' :
                                            mensajerecep= mensajeaut.mensaje
                                            c=c+1
                                            if EMAIL_ACTIVE:
                                                fact= str(notacreditoreen.numero)
                                                menad='NO AUTORIZADO'
                                                try:
                                                    menad= mensajeaut.informacionAdicional
                                                except:
                                                    pass
                                                if mensajerecep != 'FIRMA INVALIDA':
                                                    mail_errores_autorizacion(mensajeaut.mensaje,menad,fact)
                                        mensaje1 = SubElement(mensaje, 'mensaje')
                                        identificador = SubElement(mensaje1, 'identificador')
                                        identificador.text= mensajeaut.identificador
                                        mensaje2 = SubElement(mensaje1, 'mensaje')
                                        mensaje2.text= mensajeaut.mensaje
                                        tipo = SubElement(mensaje1, 'tipo')
                                        tipo.text= mensajeaut.tipo
                                except:
                                    pass

                                # tipoEmision.text = str(EMISION_ELECTRONICA)
                                ficheroats = open(os.path.join(ATS_PATH, str(clave)+'.xml'), 'w')
                                ficheroats.write('<?xml version="1.0" encoding="UTF-8" ?>')
                                # ficheroats.write(prettify(factura))
                                ficheroats.write(tostring(autorizacion).decode())
                                ficheroats.close()

                            if EMAIL_ACTIVE:
                                if notacreditoreen.inscripcion:
                                    mail_autorizacion(notacreditoreen.inscripcion.persona.emailinst,str(notacreditoreen.numero))
                                else:
                                    mail_autorizacion(notacreditoreen.fichamedica.email,str(notacreditoreen.numero))


                        except:
                            if recepcion == 'NO ENVIADOVALI':
                                fecha1=datetime.datetime.strptime(str(str(notacreditoreen.fecha).split("-")[0]+'/'+str(notacreditoreen.fecha).split("-")[1]+'/'+str(notacreditoreen.fecha).split("-")[2]),'%d/%m/%Y')  + datetime.timedelta(days=1)
                                if fecha1 < datetime.datetime.today():
                                    if EMAIL_ACTIVE:
                                        fact=str(notacreditoreen.numero)
                                        mail_errores_autorizacion(recepcion,'NOTA CREDITO: EL DOCUMENTO NO FUE ENVIADO A VALIDAR PROBLEMAS CON EL SRI',fact)
                            pass

                        # if mensajerecep != 'CLAVE ACCESO REGISTRADA':
                        if mensajerecep=='FIRMA INVALIDA':
                            recepcion = 'NO ENVIADO'
                        notacreditoreen.estado = recepcion
                        notacreditoreen.mensaje = mensajerecep
                        notacreditoreen.dirnotacredito = dirnota
                        notacreditoreen.numautorizacion = numautorizacion
                        if fechautorizacion != '':
                            notacreditoreen.fechaautorizacion = fechautorizacion
                        notacreditoreen.claveacceso = clave
                        notacreditoreen.save()

                    except Exception as ex:
                            mail_errores_autorizacion('Error desde la excepcion',str(ex),notacreditoreen.numero)
                            pass
                else:
                    try:
                        dirnota=''
                        mensajerecep=''
                        recepcion='NO ENVIADOAUT'
                        factura= Factura.objects.get(id=notacreditoreen.factura.id)
                        lugar = LugarRecaudacion.objects.get(id=factura.caja_id)
                        empresa = TituloInstitucion.objects.get(pk=CODIGO_INFORMACION_INSTITUTO)
                        dia=str(notacreditoreen.fecha.day).zfill(2)
                        mes=str(notacreditoreen.fecha.month).zfill(2)
                        clave= dia+mes+str(notacreditoreen.fecha.year)+'04'+empresa.ruc+str(AMBIENTE_FACTURACION)\
                               +str(notacreditoreen.numero.strip().split("-")[0])+str(notacreditoreen.numero.strip().split("-")[1])\
                               +str(notacreditoreen.numero.split("-")[2])+CODIGO_NUMERICO_ELEC+str(EMISION_ELECTRONICA)

                        pivote = 7
                        b=1
                        cantidadTotal=0
                        c=0
                        while ( c < len(clave)):

                            if pivote == 1:
                                pivote = 7

                            temporal = int(clave[c])
                            c = c+ 1
                            temporal *= pivote
                            pivote = pivote-1
                            cantidadTotal += temporal

                        cantidadTotal = 11 - (cantidadTotal % 11)
                        if cantidadTotal == 10:
                            cantidadTotal= 1
                        if cantidadTotal == 11:
                            cantidadTotal= 0
                        clave=clave + str(cantidadTotal)
                        respuesta_autorizacion = ''
                        i=0
                        while ( i < 5):
                            try:
                                # ssl.wrap_socket = sslwrap(ssl.wrap_socket)
                                headers = {'Content-Type': 'application/soap+xml+json; charset="UTF-8"'}
                                clie = Client('https://cel.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantesOffline?wsdl')
                                # clie = Client('https://cel.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantesOffline?wsdl')
                                respuesta_autorizacion = clie.service.autorizacionComprobante (clave)
                                i=5
                            except:
                                i = i+1
                                if i==5:
                                    if EMAIL_ACTIVE:
                                        fact= str(notacreditoreen.numero)
                                        # mail_errores_autorizacion(recepcion,'EL DOCUMENTO NO FUE ENVIADO A AUTORIZAR PROBLEMAS CON EL SRI',fact)
                                pass

                        # autorizacion = Element('autorizacion')

                        autorizacion = Element('autorizacion')

                        estado=SubElement(autorizacion, 'estado')
                        try:
                            estado.text = str(respuesta_autorizacion['autorizaciones'].autorizacion[0].estado)
                        except:
                            if EMAIL_ACTIVE:
                                fact= str(notacreditoreen.numero)
                                # mail_errores_autorizacion(recepcion,'EL DOCUMENTO NO FUE ENVIADO A AUTORIZAR PROBLEMAS CON EL SRI',fact)
                            pass
                        if estado.text == 'AUTORIZADO':
                            numeroAutorizacion = SubElement(autorizacion, 'numeroAutorizacion')
                            numeroAutorizacion.text= str(respuesta_autorizacion['autorizaciones'].autorizacion[0].numeroAutorizacion)
                            recepcion = 'AUTORIZADO'
                            dirnota = str(DIR_COMPRO+str(clave)+'.xml')
                            numautorizacion = str(respuesta_autorizacion['autorizaciones'].autorizacion[0].numeroAutorizacion)
                            fechautorizacion = str(respuesta_autorizacion['autorizaciones'].autorizacion[0]['fechaAutorizacion'])
                            if EMAIL_ACTIVE:
                                if notacreditoreen.inscripcion:
                                    mail_autorizacion(notacreditoreen.inscripcion.persona.emailinst,str(notacreditoreen.numero))
                                else:
                                    mail_autorizacion(notacreditoreen.fichamedica.email,str(notacreditoreen.numero))

                        else:
                            recepcion = 'NO ENVIADOAUT'
                            fecha1=datetime.datetime.strptime(str(dia+'/'+mes+'/'+str(notacreditoreen.fecha.year)),'%d/%m/%Y')  + datetime.timedelta(days=2)
                            if fecha1 < datetime.datetime.today():
                               recepcion = 'NO ENVIADO'
                        fechaAutorizacion = SubElement(autorizacion, 'fechaAutorizacion')
                        fechaAutorizacion.set('class', 'fechaAutorizacion')
                        fechaAutorizacion.text= str(respuesta_autorizacion['autorizaciones'].autorizacion[0]['fechaAutorizacion'].date()).split('-')[2]+'/'+str(respuesta_autorizacion['autorizaciones'].autorizacion[0]['fechaAutorizacion'].date()).split('-')[1]+'/'+str(respuesta_autorizacion['autorizaciones'].autorizacion[0]['fechaAutorizacion'].date()).split('-')[0]+' '+str(respuesta_autorizacion['autorizaciones'].autorizacion[0]['fechaAutorizacion'].time())
                        ambiente = SubElement(autorizacion, 'ambiente')
                        ambiente.text= AMBIENTE_DESCRIPCION
                        comprobante = SubElement(autorizacion, 'comprobante')
                        # cdata = CDATA(archi)
                        comprobante.text=str(respuesta_autorizacion['autorizaciones'].autorizacion[0].comprobante)
                        # elem = SubElement(comprobante, '![CDATA[')
                        # elem.text = archi
                        mensajes = SubElement(autorizacion, 'mensajes')
                        mensaje = SubElement(mensajes, 'mensaje')
                        c=0
                        try:
                            for mensajeaut in respuesta_autorizacion['autorizaciones'].autorizacion[0]['mensajes'].mensaje:
                                if c+1== 1 and estado.text != 'AUTORIZADO' :
                                    mensajerecep= mensajeaut.mensaje
                                    c=c+1
                                    if EMAIL_ACTIVE:
                                        fact= str(notacreditoreen.numero)
                                        menad='NO AUTORIZADO'
                                        try:
                                            menad= mensajeaut.informacionAdicional
                                        except:
                                            pass
                                        if mensajerecep != 'FIRMA INVALIDA':
                                            mail_errores_autorizacion(mensajeaut.mensaje,menad,fact)
                                mensaje1 = SubElement(mensaje, 'mensaje')
                                identificador = SubElement(mensaje1, 'identificador')
                                identificador.text= mensajeaut.identificador
                                mensaje2 = SubElement(mensaje1, 'mensaje')
                                mensaje2.text= mensajeaut.mensaje
                                tipo = SubElement(mensaje1, 'tipo')
                                tipo.text= mensajeaut.tipo
                        except:
                            pass


                        # tipoEmision.text = str(EMISION_ELECTRONICA)
                        ficheroats = open(os.path.join(ATS_PATH, str(clave)+'.xml'), 'w')
                        ficheroats.write('<?xml version="1.0" encoding="UTF-8" ?>')
                        # ficheroats.write(prettify(factura))
                        ficheroats.write(tostring(autorizacion).decode())
                        ficheroats.close()
                        # if mensajerecep != 'CLAVE ACCESO REGISTRADA':
                        if mensajerecep=='FIRMA INVALIDA':
                            recepcion = 'NO ENVIADO'
                        notacreditoreen.estado = recepcion
                        notacreditoreen.mensaje = mensajerecep
                        notacreditoreen.dirnotacredito = dirnota
                        notacreditoreen.numautorizacion = numautorizacion
                        if fechautorizacion != '':
                            notacreditoreen.fechaautorizacion = fechautorizacion
                        notacreditoreen.claveacceso = clave
                        notacreditoreen.save()
                    except:
                        if mensajerecep =='FIRMA INVALIDA':
                            recepcion = 'NO ENVIADO'
                        notacreditoreen.estado = recepcion
                        notacreditoreen.mensaje = mensajerecep
                        notacreditoreen.dirnotacredito = dirnota
                        notacreditoreen.numautorizacion = numautorizacion
                        if fechautorizacion != '':
                            notacreditoreen.fechaautorizacion = fechautorizacion
                        notacreditoreen.claveacceso = clave
                        notacreditoreen.save()
                        pass


    notacreditos = NotaCreditoInstitucion.objects.filter(mensaje='CLAVE ACCESO REGISTRADA',fecha__gte=FECHA_ELECT_FAC).order_by('id')
    for notacre in notacreditos:
        recepcion = 'NO ENVIADOAUT'
        mensajerecep = ''
        respuesta_autorizacion = ''
        dirfactur=''
        numautorizacion = ''
        i=0
        try:
            while ( i < 5):
                try:
                    # ssl.wrap_socket = sslwrap(ssl.wrap_socket)
                    headers = {'Content-Type': 'application/soap+xml+json; charset="UTF-8"'}
                    clie = Client('https://cel.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantesOffline?wsdl')
                    # clie = Client('https://cel.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantesOffline?wsdl')
                    respuesta_autorizacion = clie.service.autorizacionComprobante(str(notacre.claveacceso))
                    i=5
                except:
                    i = i+1
                    if i==5:
                        if EMAIL_ACTIVE:
                            fact= str(notacre.numero)
                            # mail_errores_autorizacion(recepcion,'EL DOCUMENTO NO FUE ENVIADO A AUTORIZAR PROBLEMAS CON EL SRI',fact)
                    pass
            for mensajeaut in respuesta_autorizacion['autorizaciones'].autorizacion:
                if mensajeaut.estado=='AUTORIZADO':
                    autorizacion = Element('autorizacion')

                    estado=SubElement(autorizacion, 'estado')
                    try:
                        estado.text =mensajeaut.estado
                    except:
                        if EMAIL_ACTIVE:
                            fact= str(notacre.numero)
                            # mail_errores_autorizacion(recepcion,'EL DOCUMENTO NO FUE ENVIADO A AUTORIZAR PROBLEMAS CON EL SRI',fact)
                    # estado.text = str(respuesta_autorizacion['autorizaciones'].autorizacion[0].estado)

                    numeroAutorizacion = SubElement(autorizacion, 'numeroAutorizacion')
                    numeroAutorizacion.text= mensajeaut.numeroAutorizacion
                    recepcion = 'AUTORIZADO'
                    dirfactur = str(DIR_COMPRO+str(notacre.claveacceso)+'.xml')
                    numautorizacion = mensajeaut.numeroAutorizacion
                    fechautorizacion = str(mensajeaut['fechaAutorizacion'])


                    fechaAutorizacion = SubElement(autorizacion, 'fechaAutorizacion')
                    fechaAutorizacion.set('class', 'fechaAutorizacion')
                    fechaAutorizacion.text= str(mensajeaut['fechaAutorizacion'].date()).split('-')[2]+'/'+str(mensajeaut['fechaAutorizacion'].date()).split('-')[1]+'/'+str(mensajeaut['fechaAutorizacion'].date()).split('-')[0]+' '+str(mensajeaut['fechaAutorizacion'].time())
                    ambiente = SubElement(autorizacion, 'ambiente')
                    ambiente.text= AMBIENTE_DESCRIPCION
                    comprobante = SubElement(autorizacion, 'comprobante')
                    # cdata = CDATA(archi)
                    comprobante.text=str(respuesta_autorizacion['autorizaciones'].autorizacion[0].comprobante)
                    # elem = SubElement(comprobante, '![CDATA[')
                    # elem.text = archi
                    try:
                        mensajes = SubElement(autorizacion, 'mensajes')
                        mensaje = SubElement(mensajes, 'mensaje')
                        mensaje1 = SubElement(mensaje, 'mensaje')
                        identificador = SubElement(mensaje1, 'identificador')
                        identificador.text= str(mensajeaut['mensajes'].mensaje[0].identificador)
                        mensaje2 = SubElement(mensaje1, 'mensaje')
                        mensaje2.text= str(mensajeaut['mensajes'].mensaje[0].mensaje)
                        tipo = SubElement(mensaje1, 'tipo')
                        tipo.text= str(mensajeaut['mensajes'].mensaje[0].tipo)
                    except:
                        pass


                    # tipoEmision.text = str(EMISION_ELECTRONICA)
                    ficheroats = open(os.path.join(ATS_PATH, str(notacre.claveacceso)+'.xml'), 'w')
                    ficheroats.write('<?xml version="1.0" encoding="UTF-8" ?>')
                    # ficheroats.write(prettify(factura))
                    ficheroats.write(tostring(autorizacion).decode())
                    ficheroats.close()
                    notacre.estado = recepcion

                    notacre.mensaje = mensajerecep
                    notacre.dirnotacredito =  dirfactur
                    notacre.numautorizacion =  numautorizacion
                    if fechautorizacion != '':
                            notacre.fechaautorizacion =  fechautorizacion
                    notacre.save()

        except:
            pass


def convertir_fecha(s):
    return datetime.datetime(int(s[6:10]), int(s[3:5]), int(s[0:2])).date()


def representacion_factura_str1(x):
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
    obj = model_to_dict(pago, exclude=['fecha', 'lugar', 'recibe','efectivo'])
    rubro = Rubro.objects.get(pk=obj['rubro'])
    obj['rubro'] = model_to_dict(rubro, exclude=['fecha','fechavence', 'cancelado','inscripcion','fichamedica','valor'])
    obj['rubro'].update({'nombre': rubro.nombre(), 'tipo': rubro.tipo(), 'alumno': rubro.inscripcion.persona.nombre_completo() if rubro.inscripcion else str(rubro.fichamedica),'fp':fp,'id':rubro.id})

    return obj

def mail_errores_autorizacion(cabecera,cuerpo,factura):

    if TipoIncidencia.objects.filter(pk=INCIDENCIA_FACT).exists():
        tipo = TipoIncidencia.objects.get(pk=INCIDENCIA_FACT)
        hoy = datetime.datetime.today()
        contenido = "ERROR EN DOCUMENTO No"+' '+ factura
        send_html_mail("PROBLEMA CON DOCUMENTO DE FACTURACION",
            "emails/facturacionelectronicamail.html", { 'fecha': hoy,'contenido': contenido, 'cuerpo': cuerpo, 'cabecera':cabecera},tipo.correo.split(","))


def elimina_tildes1(cadena):
    s = ''.join((c for c in unicodedata.normalize('NFD',str(cadena)) if unicodedata.category(c) != 'Mn'))
    return s

def mail_autorizacion(correo,factura):

    hoy = datetime.datetime.today()
    contenido = "DOCUMENTO No "+' '+ factura
    send_html_mail("DOCUMENTO No "+factura,
        "emails/facturacionelectronicamail.html", { 'fecha': hoy,'contenido': contenido, 'cuerpo': 'para descargar su documento visitenos en el siguiente link https://sga.itb.edu.ec/login?ret=/&fac=25 su clave es su numero de cedula', 'cabecera':'Documento autorizado por el SRI ambiente de '+AMBIENTE_DESCRIPCION},correo.split(","))

    # mail_comprobar(factura)

def mail_comprobar(factura):
    correo=TipoIncidencia.objects.get(pk=INCIDENCIA_FACT)
    hoy = datetime.datetime.today()
    contenido = "DOCUMENTO No "+' '+ factura
    send_html_mail("DOCUMENTO No "+factura,
        "emails/facturacionelectronicamail.html", { 'fecha': hoy,'contenido': contenido, 'cuerpo': 'Prueba de autorizacion', 'cabecera':'Documento autorizado por el SRI ambiente de '+AMBIENTE_DESCRIPCION},correo.correo.split(","))