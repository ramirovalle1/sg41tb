from datetime import datetime,timedelta
import json
import xlrd
import xlwt
from decimal import Decimal
from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.db.models import Sum
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from django.utils.encoding import force_str
from decorators import secure_module
from settings import UTILIZA_GRUPOS_ALUMNOS, EMAIL_ACTIVE,MEDIA_ROOT, SITE_ROOT
from sga.commonviews import addUserData, ip_client_address
from sga.forms import FormasdePagoGeneralForm
from sga.models import Inscripcion,convertir_fecha,Factura,ClienteFactura,TituloInstitucion,ReporteExcel,Pago,PagoTarjeta,PagoCheque,PagoReciboCajaInstitucion,\
     PagoTransferenciaDeposito,PagoPymentez,TipoTarjetaBanco,FormaDePago,ListaFormaDePago
from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action :
                formapago=ListaFormaDePago.objects.filter(pk=request.POST['formapago'])[:1].get()
                inicio = request.POST['inicio']
                fin = request.POST['fin']
                try:
                    m = 11
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10
                    style1 = xlwt.easyxf('',num_format_str='DD-MMM-YY')
                    wb = xlwt.Workbook()
                    num_hoja=1
                    hoja='Registros'+str(num_hoja)
                    ws = wb.add_sheet(hoja,cell_overwrite_ok=True)
                    fechai = convertir_fecha(inicio)
                    fechaf = convertir_fecha(fin)
                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,m+2, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,m+2, 'LISTADO DE PAGOS POR FORMA DE PAGO', titulo2)
                    ws.write(3, 0, 'DESDE', titulo)
                    ws.write(3, 1, str((fechai.date())), titulo)
                    ws.write(4, 0, 'HASTA:', titulo)
                    ws.write(4, 1, str((fechaf.date())), titulo)
                    ws.write(5, 0,'FORMA DE PAGO: ' + elimina_tildes(formapago.nombre), titulo)
                    formadepago=elimina_tildes(formapago.nombre)
                    # 1 efectivo 5 pagos con recibos 13 dinero electronico 14 western 15 facilito
                    if formapago.id==1 or formapago.id==5 or formapago.id==13 or formapago.id==14 or formapago.id==15:
                        ws.write(7, 0, 'FECHA', titulo)
                        ws.write(7, 1, 'CEDULA', titulo)
                        ws.write(7, 2, 'NOMBRE', titulo)
                        ws.write(7, 3, 'FACTURA', titulo)
                        ws.write(7, 4, 'FACTURADO', titulo)
                        ws.write(7, 5, 'IDENTIFICACION', titulo)
                        ws.write(7, 6, 'MONTO', titulo)
                        ws.write(7, 7, 'CAJA', titulo)
                    if elimina_tildes(formapago.nombre)=="TARJETA DE CREDITO/DEBITO":
                        ws.write(7, 0, 'FECHA', titulo)
                        ws.write(7, 1, 'CEDULA', titulo)
                        ws.write(7, 2, 'NOMBRE', titulo)
                        ws.write(7, 3, 'T.TARJETA', titulo)
                        ws.write(7, 4, 'NOMBRE TARJETA', titulo)
                        ws.write(7, 5, 'BANCO TARJETA', titulo)
                        ws.write(7, 6, 'PROCESADOR TARJETA', titulo)
                        ws.write(7, 7, 'FACTURA', titulo)
                        ws.write(7, 8, 'FACTURADO', titulo)
                        ws.write(7, 9, 'IDENTIFICACION', titulo)
                        ws.write(7, 10,'MONTO', titulo)
                        ws.write(7, 11,'CAJA', titulo)
                        ws.write(7, 12,'REFERENCIA', titulo)
                        ws.write(7, 13,'LOTE', titulo)
                        ws.write(7, 14,'AUTORIZACION', titulo)
                    if elimina_tildes(formapago.nombre)=="CHEQUE":
                        ws.write(7, 0, 'FECHA', titulo)
                        ws.write(7, 1, 'CEDULA', titulo)
                        ws.write(7, 2, 'NOMBRE', titulo)
                        ws.write(7, 3, 'BANCO', titulo)
                        ws.write(7, 4, 'NUMERO CHEQUE', titulo)
                        ws.write(7, 5, 'FACTURA', titulo)
                        ws.write(7, 6, 'FACTURADO', titulo)
                        ws.write(7, 7, 'IDENTIFICACION', titulo)
                        ws.write(7, 8, 'MONTO', titulo)
                        ws.write(7, 9, 'CAJA', titulo)
                    if elimina_tildes(formapago.nombre)=="TRANSFERENCIA Y DEPOSITO":
                        ws.write(7, 0, 'FECHA', titulo)
                        ws.write(7, 1, 'CEDULA', titulo)
                        ws.write(7, 2, 'NOMBRE', titulo)
                        ws.write(7, 3, 'TRANSF/DEP', titulo)
                        ws.write(7, 4, 'NOMBRE BANCO', titulo)
                        ws.write(7, 5, 'NUMERO CUENTA', titulo)
                        ws.write(7, 6, 'REFERENCIA', titulo)
                        ws.write(7, 7, 'FACTURA', titulo)
                        ws.write(7, 8, 'FACTURADO', titulo)
                        ws.write(7, 9, 'IDENTIFICACION', titulo)
                        ws.write(7, 10,'MONTO', titulo)
                        ws.write(7, 11,'CAJA', titulo)
                    fila = 8
                    pagos=''
                    totalregistros=0
                    totalpagado=0
                    # 1 efectivo 2 credito/deb 3 cheque 4 trans/dep 5 pagos con recibo 13 dinero elec 14 western 15 facilito
                    pagos= Factura.objects.filter(fecha__gte=fechai,fecha__lte=fechaf).order_by('fecha','numero')
                    fechapago=''
                    identificacion=''
                    estudiante=''
                    factura=''
                    cliente=''
                    identificacioncliente=''
                    valor=0
                    totalregistros=0
                    totalpagado=0
                    pago=None
                    total=0
                    for f in pagos:
                        total=0
                        #EFECTIVO
                        if formapago.id==1:
                            if Pago.objects.filter(id__in=f.pagos.all(),efectivo=True).exists():
                                pago=Pago.objects.filter(id__in=f.pagos.all(),efectivo=True)[:1].get()
                                total=f.dbf_efectivo()
                        #ELECTRONICO
                        if formapago.id==13:
                            pago=f.pagos.filter(electronico=True)[:1].get()
                            if Pago.objects.filter(id__in=f.pagos.all(),electronico=True).exists():
                                pago=Pago.objects.filter(id__in=f.pagos.all(),electronico=True)[:1].get()
                                total=f.dbf_electronico()
                        #WESTERN
                        if formapago.id==14:
                            if Pago.objects.filter(id__in=f.pagos.all(),wester=True).exists():
                                pago=Pago.objects.filter(id__in=f.pagos.all(),wester=True)[:1].get()
                                total=f.dbf_western()
                        #FACILITO
                        if formapago.id==15:
                            if Pago.objects.filter(id__in=f.pagos.all(),facilito=True).exists():
                                pago=Pago.objects.filter(id__in=f.pagos.all(),facilito=True)[:1].get()
                                total=f.dbf_facilito()
                        if (formapago.id==1 or formapago.id==13 or formapago.id==14 or formapago.id==15) and total>0:
                            caja = elimina_tildes(pago.sesion.caja.nombre)
                            totalregistros+=1
                            fechapago=pago.fecha
                            if pago.rubro.inscripcion.persona.cedula:
                                identificacion=pago.rubro.inscripcion.persona.cedula
                            else:
                                identificacion=pago.rubro.inscripcion.persona.pasaporte

                            estudiante=pago.rubro.inscripcion.persona.nombre_completo_inverso()
                            factura= f
                            cliente = ClienteFactura.objects.filter(id=factura.cliente.id)[:1].get()
                            valor=total
                            totalpagado=totalpagado+valor
                            try:
                                identificacioncliente=cliente.ruc
                                cliente = elimina_tildes(cliente.nombre)
                            except:
                                cliente = "Error en nombre cliente"

                            ws.write(fila,0,str(fechapago))
                            ws.write(fila,1,identificacion)
                            ws.write(fila,2,elimina_tildes(estudiante))
                            ws.write(fila,3,str(factura.numero))
                            ws.write(fila,4,str(cliente))
                            ws.write(fila,5,str(identificacioncliente))
                            ws.write(fila,6,valor)
                            ws.write(fila,7,caja)
                            fila=fila+1

                        # RECIBOS
                        if formapago.id==5:
                            if PagoReciboCajaInstitucion.objects.filter(pagos__in=f.pagos.all()).exists():
                                pgrec =PagoReciboCajaInstitucion.objects.filter(pagos__in=f.pagos.all()).values('pagos__id')[:1].get()
                                pago=Pago.objects.filter(pk=pgrec['pagos__id'])[:1].get()
                                total=f.dbf_recibocajainst()
                                fechapago=''
                                identificacion=''
                                estudiante=''
                                factura=''
                                numerofactura=''
                                cliente=''
                                identificacioncliente=''
                                caja=''
                                caja = elimina_tildes(pago.sesion.caja.nombre)
                                if fila==65500:
                                    num_hoja=num_hoja+1
                                    hoja='Registros'+str(num_hoja)
                                    ws = wb.add_sheet(hoja,cell_overwrite_ok=True)
                                    fila=8
                                totalregistros+=1
                                fechapago=pago.fecha
                                if pago.rubro.inscripcion.persona.cedula:
                                    identificacion=pago.rubro.inscripcion.persona.cedula
                                else:
                                    identificacion=pago.rubro.inscripcion.persona.pasaporte

                                estudiante=pago.rubro.inscripcion.persona.nombre_completo_inverso()
                                factura= f
                                numerofactura=str(factura.numero)
                                cliente = ClienteFactura.objects.filter(id=factura.cliente.id)[:1].get()
                                try:
                                    identificacioncliente=cliente.ruc
                                    cliente = elimina_tildes(cliente.nombre)
                                except:
                                    cliente = "Error en nombre cliente"

                                valor=total
                                totalpagado=totalpagado+valor

                                ws.write(fila,0,str(fechapago))
                                ws.write(fila,1,identificacion)
                                ws.write(fila,2,elimina_tildes(estudiante))
                                ws.write(fila,3,numerofactura)
                                ws.write(fila,4,cliente)
                                ws.write(fila,5,str(identificacioncliente))
                                ws.write(fila,6,valor)
                                ws.write(fila,7,caja)
                                fila=fila+1
                        #CHEQUE
                        if formapago.id==3 :
                            if PagoCheque.objects.filter(pagos__in=f.pagos.all()).exists():
                                pgch =PagoCheque.objects.filter(pagos__in=f.pagos.all()).values('pagos__id')[:1].get()
                                pago=Pago.objects.filter(pk=pgch['pagos__id'])[:1].get()
                                total=f.dbf_cheques()
                                fechapago=''
                                identificacion=''
                                estudiante=''
                                factura=''
                                numerofactura=''
                                cliente=''
                                numerocheque=''
                                bancocheque=''
                                identificacioncliente=''
                                caja=''
                                valor=0
                                pgc=PagoCheque.objects.filter(pagos=pgch['pagos__id'])[:1].get()
                                if pgc.numero:
                                   numerocheque=elimina_tildes(pgc.numero)
                                if pgc.banco:
                                   bancocheque=elimina_tildes(pgc.banco)
                                caja = elimina_tildes(pago.sesion.caja.nombre)
                                if fila==65500:
                                    num_hoja=num_hoja+1
                                    hoja='Registros'+str(num_hoja)
                                    ws = wb.add_sheet(hoja,cell_overwrite_ok=True)
                                    fila=8
                                totalregistros+=1
                                fechapago=pago.fecha
                                if pago.rubro.inscripcion.persona.cedula:
                                    identificacion=pago.rubro.inscripcion.persona.cedula
                                else:
                                    identificacion=pago.rubro.inscripcion.persona.pasaporte
                                estudiante=pago.rubro.inscripcion.persona.nombre_completo_inverso()
                                factura=f
                                numerofactura=str(factura.numero)
                                cliente = ClienteFactura.objects.filter(id=factura.cliente.id)[:1].get()
                                try:
                                    identificacioncliente=cliente.ruc
                                    cliente = elimina_tildes(cliente.nombre)
                                except:
                                    cliente = "Error en nombre cliente"
                                valor=total
                                totalpagado=totalpagado+valor
                                ws.write(fila,0,str(fechapago))
                                ws.write(fila,1,identificacion)
                                ws.write(fila,2,elimina_tildes(estudiante))
                                ws.write(fila,3,str(bancocheque))
                                ws.write(fila,4,numerocheque)
                                ws.write(fila,5,numerofactura)
                                ws.write(fila,6,cliente)
                                ws.write(fila,7,str(identificacioncliente))
                                ws.write(fila,8,valor)
                                ws.write(fila,9,caja)
                                fila=fila+1
                        #TRANSFERENCIA/DEPOSITO
                        total=0
                        if formapago.id==4:
                            if PagoTransferenciaDeposito.objects.filter(pagos__in=f.pagos.all()).exists():
                                pgtd =PagoTransferenciaDeposito.objects.filter(pagos__in=f.pagos.all()).values('pagos__id')[:1].get()
                                pago=Pago.objects.filter(pk=pgtd['pagos__id'])[:1].get()
                                fechapago=''
                                identificacion=''
                                estudiante=''
                                factura=''
                                numerofactura=''
                                cliente=''
                                tipotransaccion=''
                                nombrebanco=''
                                numerocuenta=''
                                referencia=''
                                identificacioncliente=''
                                caja=''
                                valor=0
                                pgtd=PagoTransferenciaDeposito.objects.filter(pagos=pgtd['pagos__id'])[:1].get()
                                if pgtd.deposito==True:
                                   tipotransaccion='DEPOSITO'
                                   total=f.dbf_deposito()
                                else:
                                   tipotransaccion='TRANSFERENCIA'
                                   total=f.dbf_transferencia()

                                if pgtd.cuentabanco:
                                    nombrebanco=elimina_tildes(pgtd.cuentabanco.banco)
                                    numerocuenta=str(pgtd.cuentabanco.numero)
                                else:
                                    nombrebanco=''
                                    numerocuenta=''

                                if pgtd.referencia:
                                    referencia=elimina_tildes(pgtd.referencia)
                                else:
                                    referencia=''
                                caja = elimina_tildes(pago.sesion.caja.nombre)
                                if fila==65500:
                                    num_hoja=num_hoja+1
                                    hoja='Registros'+str(num_hoja)
                                    ws = wb.add_sheet(hoja,cell_overwrite_ok=True)
                                    fila=8
                                totalregistros+=1
                                fechapago=pago.fecha
                                if pago.rubro.inscripcion.persona.cedula:
                                    identificacion=pago.rubro.inscripcion.persona.cedula
                                else:
                                    identificacion=pago.rubro.inscripcion.persona.pasaporte

                                estudiante=pago.rubro.inscripcion.persona.nombre_completo_inverso()
                                factura= f
                                numerofactura=str(factura.numero)
                                cliente = ClienteFactura.objects.filter(id=factura.cliente.id)[:1].get()
                                try:
                                    identificacioncliente=cliente.ruc
                                    cliente = elimina_tildes(cliente.nombre)
                                except:
                                    cliente = "Error en nombre cliente"
                                valor=total
                                totalpagado=totalpagado+valor

                                ws.write(fila,0,str(fechapago))
                                ws.write(fila,1,identificacion)
                                ws.write(fila,2,elimina_tildes(estudiante))
                                ws.write(fila,3,str(tipotransaccion))
                                ws.write(fila,4,nombrebanco)
                                ws.write(fila,5,numerocuenta)
                                ws.write(fila,6,referencia)
                                ws.write(fila,7,numerofactura)
                                ws.write(fila,8,cliente)
                                ws.write(fila,9,str(identificacioncliente))
                                ws.write(fila,10,valor)
                                ws.write(fila,11,caja)
                                fila=fila+1

                        #Pagos con Tarjetas
                        total=0
                        if elimina_tildes(formapago.nombre)=="TARJETA DE CREDITO/DEBITO":
                            if PagoTarjeta.objects.filter(pagos__in=f.pagos.all()).exists():
                                pgt =PagoTarjeta.objects.filter(pagos__in=f.pagos.all()).values('pagos__id')[:1].get()
                                pago=Pago.objects.filter(pk=pgt['pagos__id'])[:1].get()
                                fechapago=''
                                identificacion=''
                                estudiante=''
                                factura=''
                                numerofactura=''
                                cliente=''
                                tipotarjeta=''
                                nombretipotarjeta=''
                                bancotarjeta=''
                                procesadortarjeta=''
                                referencia=''
                                lote=''
                                autorizacion=''
                                autorizacionpay=''
                                lotepay=''
                                identificacioncliente=''
                                caja=''
                                pgt=PagoTarjeta.objects.filter(pagos=pgt['pagos__id'])[:1].get()
                                if pgt.tarjetadebito==True:
                                   tipotarjeta='DEBITO'
                                   total=f.dbf_tarjetas()
                                else:
                                   tipotarjeta='CREDITO'
                                   total=f.dbf_tarjetas()
                                if pgt.referencia:
                                    referencia=pgt.referencia
                                    if PagoPymentez.objects.filter(referencia_tran=referencia).exists():
                                        pgpay=PagoPymentez.objects.filter(referencia_tran=referencia)[:1].get()
                                        lotepay=pgpay.lote
                                        autorizacionpay=pgpay.codigo_aut
                                    else:
                                        lotepay=''
                                        autorizacionpay=''
                                else:
                                    referencia=''

                                if pgt.lote:
                                    lote=pgt.lote
                                else:
                                    lote=''
                                if pgt.autorizacion:
                                    autorizacion=elimina_tildes(pgt.autorizacion)
                                else:
                                    autorizacion=''
                                if pgt.tipo:
                                    nombretipotarjeta=pgt.tipo.nombre
                                else:
                                    nombretipotarjeta=''
                                if pgt.procesadorpago:
                                    procesadortarjeta=str(pgt.procesadorpago.nombre)
                                else:
                                    procesadortarjeta=''
                                if pgt.banco:
                                    bancotarjeta=elimina_tildes(pgt.banco.nombre)
                                else:
                                    bancotarjeta=''

                                caja = elimina_tildes(pago.sesion.caja.nombre)
                                if fila==65500:
                                    num_hoja=num_hoja+1
                                    hoja='Registros'+str(num_hoja)
                                    ws = wb.add_sheet(hoja,cell_overwrite_ok=True)
                                    fila=8
                                totalregistros+=1
                                fechapago=pago.fecha
                                if pago.rubro.inscripcion.persona.cedula:
                                    identificacion=pago.rubro.inscripcion.persona.cedula
                                else:
                                    identificacion=pago.rubro.inscripcion.persona.pasaporte

                                estudiante=pago.rubro.inscripcion.persona.nombre_completo_inverso()
                                factura= f
                                numerofactura=str(factura.numero)
                                cliente = ClienteFactura.objects.filter(id=factura.cliente.id)[:1].get()
                                try:
                                    identificacioncliente=cliente.ruc
                                    cliente = elimina_tildes(cliente.nombre)
                                except:
                                    cliente = "Error en nombre cliente"
                                valor=total
                                totalpagado=totalpagado+valor

                                ws.write(fila,0,str(fechapago))
                                ws.write(fila,1,identificacion)
                                ws.write(fila,2,elimina_tildes(estudiante))
                                ws.write(fila,3,str(tipotarjeta))
                                ws.write(fila,4,nombretipotarjeta)
                                ws.write(fila,5,bancotarjeta)
                                ws.write(fila,6,procesadortarjeta)
                                ws.write(fila,7,numerofactura)
                                ws.write(fila,8,cliente)
                                ws.write(fila,9,str(identificacioncliente))
                                ws.write(fila,10,valor)
                                ws.write(fila,11,caja)
                                ws.write(fila,12,referencia)
                                if lote!='':
                                    ws.write(fila,13,lote)
                                else:
                                    ws.write(fila,13,lotepay)
                                if autorizacion!='':
                                    ws.write(fila,14,autorizacion)
                                else:
                                    ws.write(fila,14,autorizacionpay)
                                fila=fila+1

                    ws.write(fila,0,  'TRANSACCIONES EN TOTAL', titulo)
                    ws.write(fila,3,totalregistros, titulo)
                    # 1 efectivo 5 pagos con recibo 13 dinero elec 14 western 15 facilito
                    if formapago.id==1 or formapago.id==5 or formapago.id==13 or formapago.id==14 or formapago.id==15:
                        ws.write(fila,4,'TOTAL '+elimina_tildes(formapago.nombre), titulo)
                        ws.write(fila,6,totalpagado, titulo)
                    #Cheque
                    if formapago.id==3:
                        ws.write(fila,4,'TOTAL '+elimina_tildes(formadepago), titulo)
                        ws.write(fila,8,totalpagado, titulo)
                    #Tarjetas cred/deb Trans/dep
                    if formapago.id==2 or formapago.id==4:
                        ws.write(fila,6,'TOTAL '+elimina_tildes(formadepago), titulo)
                        ws.write(fila,10,totalpagado, titulo)

                    detalle = 4
                    detalle = detalle + fila
                    ws.write(detalle, 0, "Fecha Impresion", subtitulo)
                    ws.write(detalle, 1, str(datetime.now()), subtitulo)
                    detalle=detalle +1
                    ws.write(detalle, 0, "Usuario", subtitulo)
                    ws.write(detalle, 1, str(request.user), subtitulo)

                    nombre ='tipopagos'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")

        else:
            data = {'title': 'Ingresos por Forma de Pago'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform']=FormasdePagoGeneralForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
                return render(request ,"reportesexcel/formasdepago_ingresos.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")
    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

