import csv
from decimal import Decimal
import os
from django.db import transaction
import json
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.forms import model_to_dict
from django.utils.encoding import force_str
import xlrd
import xlwt
from sga.api import abrir_caja
from sga.facturacioncron import mail_errores_autorizacion
from sga.models import Oficio, PagoWester,Inscripcion, ArchivoWester, Rubro, elimina_tildes,TipoIncidencia, ArchivoPichincha, RecaudacionPichincha, ClienteFactura, Factura, DetalleDescuento, Descuento, LugarRecaudacion, ReciboCajaInstitucion, Pago, FormaDePago
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.core.paginator import Paginator
from sga.commonviews import addUserData, ip_client_address
from django.template import RequestContext
from sga.forms import ArchivoPichinchaForm
from datetime import datetime, date, timedelta
from django.db.models import Q, Avg
from settings import EMAIL_ACTIVE, MEDIA_ROOT, SITE_ROOT, INCIDENCIA_FACT, HABILITA_APLICA_DESCUE, TESIS_URL, CAJA_PICHINCHA, PORCENTAJE_DESCUENTO, PORCENTAJE_DESCUENTO15, FACTURACION_ELECTRONICA, DEFAULT_PASSWORD
from sga.pre_inscripciones import email_error_congreso
from sga.tasks import send_html_mail
from decorators import secure_module


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
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action == 'generar':
                if  not ArchivoPichincha.objects.filter(fecha=datetime.now()).exists():
                    try:
                        matricula =Inscripcion.objects.filter(persona__usuario__is_active=True).order_by('persona__apellido1','persona__apellido2','persona__nombres')

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

                                fec=datetime.now().date()
                                fec=datetime.now().date()  + timedelta(days=30)
                                tipo=''
                                inden=''
                                nombre=''
                                cont = 0
                                print((m))

                                if m.persona.cedula or   m.persona.pasaporte:
                                    for r in Rubro.objects.filter(inscripcion=m,cancelado=False,fechavence__lte=fec,valor__gt=0).order_by('cancelado','fechavence'):
                                        adeuda=0
                                        if HABILITA_APLICA_DESCUE:
                                            if r.aplicadescuento(None)[1] > 0:
                                                adeuda = str(Decimal(r.aplicadescuento(None)[0]).quantize(Decimal(10) ** -2)).replace(".","")
                                            else:
                                                adeuda = str(Decimal(r.adeudado()).quantize(Decimal(10)**-2)).replace(".","")
                                        else:
                                            adeuda = str(Decimal(r.adeudado()).quantize(Decimal(10)**-2)).replace(".","")

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
                                        nombre = str(elimina_tildes(m.persona.nombre_completo()))[:41]
                                        datos.write('CO'+'\t'+str(inden)+'\t'+'USD' +'\t'+ str(adeuda)+'\t'+ 'REC' +'\t'+'\t'+'\t'+"S"+str(r.id)+'\t'+str(tipo)+'\t'+str(inden)+'\t'+str(nombre)+'\n')
                            except Exception as ex:
                                mail_errores(str(m.inscripcion),ex)
                                print(ex)
                                pass
                        datos.close()
                        archivow = ArchivoPichincha(fecha=datetime.now(),
                                                 archivo='registro'+str(datetime.now().date())+'.txt')
                        archivow.save()
                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(archivow).pk,
                            object_id       = archivow.id,
                            object_repr     = force_str(archivow),
                            action_flag     = DELETION,
                            change_message  = 'Generado Archivo Recaudacion B. Pichincha'+' (' + client_address + ')' )
                        return HttpResponse(json.dumps({"result":"ok", "url": "/media/archivopichincha/"+datos.name}),content_type="application/json")
                    except Exception as ex:
                        print((ex))
                        return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")
                else:
                    return HttpResponse(json.dumps({"result":"Ya Existe un Arcivo en esta fecha"}),content_type="application/json")
            elif action =='factura_pichincha':
                errores  =[]
                for pagop in RecaudacionPichincha.objects.filter(archivo__gestionado=False,factura=None).exclude(cuenta=None):
                    sid = transaction.savepoint()
                    try:
                        b= 0
                        if abrir_caja(CAJA_PICHINCHA):
                            caja = abrir_caja(CAJA_PICHINCHA)
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
                                                        valida = True, cliente = cliente,hora = datetime.now().time(),
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
                                t = pagop.cuenta
                                adeudado = r.adeudado()
                                detalle = None
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
                                else:
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
                                                        pichincha=True,
                                                        facilito=False)
                                pago2.save()
                                factura.pagos.add(pago2)
                                if detalle:
                                    detalle.pago = pago2
                                    detalle.save()

                                if r.adeudado()==0:
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
                                                               sesioncaja=abrir_caja(CAJA_PICHINCHA),
                                                               fecha=datetime.now().date(),
                                                               hora=datetime.now().time(),
                                                               valorinicial = float(valorrecibo),
                                                               saldo=float(valorrecibo),
                                                               formapago=FormaDePago.objects.get(pk=12))
                                        rc.save()
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
                            errores.append(('error pago en recuadacion pichincga - caja cerrada inscid: ' +str(pagop.id ), elimina_tildes(pagop.cuenta.inscripcion.persona.nombre_completo())))
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
            elif action == 'eliminar':
                result = {}
                try:
                    archivo =ArchivoPichincha.objects.filter(pk=request.POST['idarchivo'])[:1].get()
                    if not archivo.tiene_factura():
                        mensaje = 'Recaudacion Pichincha Eliminada'
                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(archivo).pk,
                            object_id       = archivo.id,
                            object_repr     = force_str(archivo),
                            action_flag     = DELETION,
                            change_message  = mensaje+' (' + client_address + ')' )
                        if not archivo.tiene_factura():
                            RecaudacionPichincha.objects.filter(archivo=archivo).delete()
                            result['result']  = "ok"
                            archivo.archivorecaudacion = None
                            archivo.save()
                            return HttpResponse(json.dumps(result), content_type="application/json")
                        if os.path.exists(MEDIA_ROOT+'/media/archivopichincha/'+str(archivo.archivorecaudacion)):
                            os.remove(MEDIA_ROOT+'/media/archivopichincha/'+str(archivo.archivorecaudacion))
                        if os.path.exists("https://tesoreria.itb.edu.ec/media/archivopichincha/"   + str(archivo.nombre_archivo_recaudacion())):
                            os.remove("https://tesoreria.itb.edu.ec/media/archivopichincha/"   + str(archivo.nombre_archivo_recaudacion()))
                        archivo.archivorecaudacion = None
                        archivo.save()
                    result['result']  = "Archivo ya tiene registros facturados"
                    return HttpResponse(json.dumps(result), content_type="application/json")
                except Exception as e:
                    result['result']  = str(e)
                    return HttpResponse(json.dumps(result), content_type="application/json")

            elif action =='cambiargestion':
                result = {}
                try:
                    archivo =ArchivoPichincha.objects.filter(pk=request.POST['archivoid'])[:1].get()
                    archivo.gestionado=False
                    archivo.save()
                    result['result']  = "ok"
                    mensaje="Cambio de Estado en Gestion"
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(archivo).pk,
                        object_id       = archivo.id,
                        object_repr     = force_str(archivo),
                        action_flag     = CHANGE,
                        change_message  = mensaje+' (' + client_address + ')' )
                    return HttpResponse(json.dumps(result),content_type="application/json")
                except Exception as e:
                    result['result']  = str(e)
                    return HttpResponse(json.dumps(result), content_type="application/json")

            elif action == 'archivopichincha':
                f = ArchivoPichinchaForm(request.POST,request.FILES)
                if f.is_valid():
                    sid = transaction.savepoint()
                    try:
                        errores  =[]
                        archivop = ArchivoPichincha.objects.get(id=request.POST['idarc'])
                        if 'archivo' in request.FILES:
                            archivo = request.FILES['archivo']
                            archivop.archivorecaudacion = archivo
                            archivop.fecharecaudacion = datetime.now().date()
                            archivop.save()
                            csv_filepathname=(os.path.join(MEDIA_ROOT+'/',str(archivop.archivorecaudacion)))
                            dataReader = csv.reader(open(csv_filepathname), delimiter='\t')
                            for row in dataReader:
                                cuenta = str(row[33]).split('|')[0] #rubro
                                if 'S' in cuenta:
                                    cuenta = cuenta[1:len(cuenta)] #rubro
                                    if Rubro.objects.filter(pk=cuenta).exists():
                                        rubro = Rubro.objects.filter(pk=cuenta)[:1].get()
                                        rubroid = rubro.id
                                    else:
                                        rubroid = cuenta
                                        rubro=None
                                        errores.append(('No existe rubro : '+row[5]  ,str(cuenta)))
                                        # fechadia = (row[2]).split(" ")
                                    fechap=(str(row[24][0:2]) + "-" +str(row[24][3:5])+ "-"+ str(row[24][6:10]))

                                    # dec = row[27][len(row[27])-2:]
                                    # ent = row[27][:len(row[27])-2]
                                    valor = row[27]
                                    archivor = RecaudacionPichincha(archivo=archivop,
                                                                    nombre=row[5],
                                                                    fecha = datetime.now(),
                                                                    tipopago = row[9],
                                                                    estadoproceso = row[12],
                                                                    referencia = row[0],
                                                                    id_sobre = row[14],
                                                                    id_item = row[5],
                                                                    id_contrato = row[13],
                                                                    cuenta  =rubro,
                                                                    eliminado = row[17],
                                                                    numeroidentificacion = row[11],
                                                                    canal = row[18],
                                                                    medio = row[19],
                                                                    numerodocumento= row[20],
                                                                    horario = row[21],
                                                                    mensaje = row[22],
                                                                    oficina = row[23],
                                                                    fechaproceso = fechap,
                                                                    horaproceso = row[26],
                                                                    valorprocesado =valor,
                                                                    formapago = row[29],
                                                                    banco  = row[32],
                                                                    referenciaadicional  = row[33],
                                                                    secuencialcobro = row[34],
                                                                    numerocomprobante  = row[37],
                                                                    # numerocuenta  = row[38],
                                                                    numdocumento  = row[37],
                                                                    tipocuenta  = row[38],
                                                                    numerocuenta  = row[39],
                                                                    condicionproceso  = row[40],
                                                                    numerotransaccion = row[41],
                                                                    numerosri  = row[42],
                                                                    direccioncliente  = row[43],
                                                                    rubroid=rubroid,
                                                                    numeroautorizacion =row[44])
                                    archivor.save()


                            client_address = ip_client_address(request)
                            LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(archivop).pk,
                                object_id       = archivop.id,
                                object_repr     = force_str(archivop),
                                action_flag     = ADDITION,
                                change_message  = 'Adicionado Archivo de Recaudacion de Pichincha (' + client_address + ')' )
                            transaction.savepoint_commit(sid)
                            if errores:
                                mail_errores(errores,'SE ENCONTRARON ERRORES AL GUARDAR LA INFORMACION')
                            return HttpResponseRedirect('/archivopichincha?error=SE GUARDO CORRECTAMENTE')
                    except Exception as e:
                        print((e))
                        transaction.savepoint_rollback(sid)
                        return HttpResponseRedirect('/archivopichincha?error='+str(e))
                else:
                    return HttpResponseRedirect('/archivopichincha?error=el archivo no tiene el formato correcto')
            if action=='editarid':
                result={}
                try:
                    if RecaudacionPichincha.objects.filter(pk=request.POST['pago']).exists():
                        recaupich = RecaudacionPichincha.objects.filter(pk=request.POST['pago'])[:1].get()
                        if Rubro.objects.filter(pk=request.POST['cuenta']).exists():
                            rub=Rubro.objects.filter(pk=request.POST['cuenta'])[:1].get()
                            recaupich.cuenta= rub
                            recaupich.save()

                            client_address = ip_client_address(request)

                            LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(recaupich).pk,
                            object_id       = recaupich.id,
                            object_repr     = force_str(recaupich),
                            action_flag     = ADDITION,
                            change_message  = ' (' + client_address + ')' )
                            result['result']  = "ok"
                            return HttpResponse(json.dumps(result), content_type="application/json")
                        result['result']="EL ID DEL RUBRO NO ES CORRECTO"
                        return HttpResponse(json.dumps(result), content_type="application/json")
                    result['result']="EL ID DEL PAGO NO ES VALIDO"
                    return HttpResponse(json.dumps(result), content_type="application/json")
                except Exception as ex:
                    print(ex)
                    result['result']  = str(ex)
                    return HttpResponse(json.dumps(result), content_type="application/json")


        else:
            data = {'title': 'Registro de Pagos'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']
                if action =='ver':
                    data['archivo']=ArchivoPichincha.objects.filter(id=request.GET['id'])[:1].get()
                    search = None
                    todos = None
                    facturado = None
                    if 'error' in request.GET:
                        data['error'] = request.GET['error']

                    if 's' in request.GET:
                        search = request.GET['s']
                    if 'pen' in request.GET:
                        facturado = False
                        data['pen'] =1
                    if 'fac' in request.GET:
                        facturado = True
                        data['fac'] =1
                    if 't' in request.GET:
                        todos = request.GET['t']
                    if search:
                        ss = search.split(' ')
                        while '' in ss:
                            ss.remove('')
                        if len(ss)==1:
                            registros = RecaudacionPichincha.objects.filter(Q(cuenta__inscripcion__persona__nombres__icontains=search) | Q(cuenta__inscripcion__persona__apellido1__icontains=search) | Q(cuenta__inscripcion__persona__apellido2__icontains=search) | Q(cuenta__inscripcion__persona__cedula__icontains=search) | Q(cuenta__inscripcion__persona__pasaporte__icontains=search),archivo__id=request.GET['id']).order_by('cuenta__inscripcion__persona__apellido1')
                        else:
                            registros = RecaudacionPichincha.objects.filter(Q(cuenta__inscripcion__persona__apellido1__icontains=ss[0]) & Q(cuenta__inscripcion__persona__apellido2__icontains=ss[1]),archivo__id=request.GET['id']).order_by('cuenta__inscripcion__persona__apellido1','cuenta__inscripcion__persona__apellido2','cuenta__inscripcion__persona__nombres')
                    elif facturado != None:
                        registros =RecaudacionPichincha.objects.filter(archivo__id=request.GET['id'],facturado=facturado)
                    else:
                        registros =RecaudacionPichincha.objects.filter(archivo__id=request.GET['id'])

                    paging = MiPaginador(registros, 30)
                    p = 1
                    try:
                        if 'page' in request.GET:
                            p = int(request.GET['page'])
                        page = paging.page(p)
                    except:
                        page = paging.page(p)

                    data['paging'] = paging
                    data['rangospaging'] = paging.rangos_paginado(p)
                    data['page'] = page
                    data['search'] = search if search else ""
                    data['todos'] = todos if todos else ""
                    data['registros'] = page.object_list
                    if 'id' in request.GET:
                        data['id'] = request.GET['id']
                    return render(request ,"archivopichincha/registroarchivo.html" ,  data)

            else:
                search = None
                todos = None
                if 'error' in request.GET:
                    data['error'] = request.GET['error']

                if 's' in request.GET:
                    search = request.GET['s']
                if 't' in request.GET:
                    todos = request.GET['t']
                if search:
                    archivo = ArchivoPichincha.objects.filter(fecha=convertir_fecha(search)).order_by('-fecha')
                else:

                    archivo = ArchivoPichincha.objects.all().order_by('-fecha')
                if ArchivoPichincha.objects.filter(fecha=datetime.now()).exists():
                    data['ban'] = 1

                paging = MiPaginador(archivo, 30)
                p = 1
                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                    page = paging.page(p)
                except:
                    page = paging.page(p)

                data['paging'] = paging
                data['rangospaging'] = paging.rangos_paginado(p)
                data['page'] = page
                data['search'] = search if search else ""
                data['todos'] = todos if todos else ""
                data['archivo'] = page.object_list
                data['frmarchivowester'] = ArchivoPichinchaForm()
                if 'info' in request.GET:
                    data['info'] =request.GET['info']

                return render(request ,"archivopichincha/registro.html" ,  data)
    except Exception as e:
        return HttpResponseRedirect("/")

def convertir_fecha(s):
    try:
        return datetime(int(s[-4:]), int(s[3:5]), int(s[:2]))
    except:
        return datetime.now()

def mail_errores(errores,op):
        if TipoIncidencia.objects.filter(pk=50).exists():
            tipo=TipoIncidencia.objects.get(pk=50)
            hoy = datetime.now().today()
            send_html_mail("SE ENCONTRARON ERRORES AL  SUBIR RECAUDACION DE BANCO PICHINCHA",
                "emails/error_congreso.html", {'contenido': "Recaudacion B. Pichincha", 'errores': errores,'op':op},tipo.correo.split(","))