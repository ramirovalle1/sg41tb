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
from sga.forms import FormasdePagoForm
from sga.models import Inscripcion,convertir_fecha,Factura,ClienteFactura,TituloInstitucion,ReporteExcel,Pago,PagoTarjeta,TipoTarjetaBanco,FormaDePago,ListaFormaDePago
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
                    m = 12
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
                    if elimina_tildes(formapago.nombre)=="WESTERN UNION":
                        ws.write(7, 0,  'FECHA', titulo)
                        ws.write(7, 1,  'CEDULA', titulo)
                        ws.write(7, 2,  'NOMBRE', titulo)
                        ws.write(7, 3,  'FACTURA', titulo)
                        ws.write(7, 4,  'FACTURADO', titulo)
                        ws.write(7, 5,  'CEDULA', titulo)
                        ws.write(7, 6,  'MONTO', titulo)

                    if elimina_tildes(formapago.nombre)=="TARJETA DE CREDITO/DEBITO":
                        ws.write(7, 0,  'FECHA', titulo)
                        ws.write(7, 1,  'CEDULA', titulo)
                        ws.write(7, 2,  'NOMBRE', titulo)
                        ws.write(7, 3,  'T.TARJETA', titulo)
                        ws.write(7, 4,  'NOMBRE TARJETA', titulo)
                        ws.write(7, 5,  'BANCO TARJETA', titulo)
                        ws.write(7, 6,  'PROCESADOR TARJETA', titulo)
                        ws.write(7, 7,  'FACTURA', titulo)
                        ws.write(7, 8,  'FACTURADO', titulo)
                        ws.write(7, 9,  'CEDULA', titulo)
                        ws.write(7, 10,  'MONTO', titulo)
                        ws.write(7, 11,  'CAJA', titulo)
                    fila = 8
                    pagos=''
                    totalregistros=0
                    totalpagado=0
                    if elimina_tildes(formapago.nombre)=="WESTERN UNION":
                        pagos= Pago.objects.filter(fecha__gte=fechai,fecha__lte=fechaf,wester=True).order_by('fecha','rubro__inscripcion__persona__apellido1','rubro__inscripcion__persona__apellido2')
                        fechapago=''
                        identificacion=''
                        estudiante=''
                        factura=''
                        cliente=''
                        identificacioncliente=''
                        valor=0
                        totalregistros=0
                        totalpagado=0
                        for pago in pagos:
                            totalregistros+=1
                            fechapago=pago.fecha
                            if pago.rubro.inscripcion.persona.cedula:
                                identificacion=pago.rubro.inscripcion.persona.cedula
                            else:
                                identificacion=pago.rubro.inscripcion.persona.pasaporte

                            estudiante=pago.rubro.inscripcion.persona.nombre_completo_inverso()
                            factura= Factura.objects.filter(pagos=pago)[:1].get()
                            cliente = ClienteFactura.objects.filter(id=factura.cliente_id)[:1].get()
                            valor=pago.valor
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
                            fila=fila+1

                    if elimina_tildes(formapago.nombre)=="TARJETA DE CREDITO/DEBITO":
                        pgt= PagoTarjeta.objects.filter(pagos__fecha__gte=fechai,pagos__fecha__lte=fechaf).values('pagos').order_by('pagos__fecha','pagos__rubro__inscripcion__persona__apellido1','pagos__rubro__inscripcion__persona__apellido2')
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
                        identificacioncliente=''
                        caja=''
                        valor=0
                        totalregistros=0
                        totalpagado=0

                        for pagos in pgt:
                            #print((pagos['pagos']))
                            pgt=PagoTarjeta.objects.filter(pagos=pagos['pagos'])[:1].get()
                            if pgt.tarjetadebito==True:
                               tipotarjeta='DEBITO'
                            else:
                               tipotarjeta='CREDITO'

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
                            for pago in Pago.objects.filter(pk=pagos['pagos']).order_by('fecha','rubro__inscripcion__persona__apellido1','rubro__inscripcion__persona__apellido2'):
                                #print((pago.fecha))
                                caja = elimina_tildes(pago.sesion.caja.nombre)
                                if fila==65500:
                                    num_hoja=num_hoja+1
                                    hoja='Registros'+str(num_hoja)
                                    ws = wb.add_sheet(hoja,cell_overwrite_ok=True)
                                    fila=8
                            #for pago in Pago.objects.filter(pk=1421917).order_by('fecha','rubro__inscripcion__persona__apellido1','rubro__inscripcion__persona__apellido2'):

                                totalregistros+=1
                                fechapago=pago.fecha
                                if pago.rubro.inscripcion.persona.cedula:
                                    identificacion=pago.rubro.inscripcion.persona.cedula
                                else:
                                    identificacion=pago.rubro.inscripcion.persona.pasaporte

                                estudiante=pago.rubro.inscripcion.persona.nombre_completo_inverso()
                                if Factura.objects.filter(pagos=pago).exists():
                                    factura= Factura.objects.filter(pagos=pago)[:1].get()
                                    numerofactura=str(factura.numero)
                                    cliente = ClienteFactura.objects.filter(id=factura.cliente_id)[:1].get()
                                    try:
                                        identificacioncliente=cliente.ruc
                                        cliente = elimina_tildes(cliente.nombre)
                                    except:
                                        cliente = "Error en nombre cliente"
                                else:
                                    numerofactura=''
                                    cliente=''
                                    identificacioncliente=''
                                valor=pago.valor
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
                                fila=fila+1

                    ws.write(fila,0,  'TRANSACCIONES EN TOTAL', titulo)
                    ws.write(fila,3,totalregistros, titulo)
                    if elimina_tildes(formapago.nombre)=='WESTERN UNION':
                        ws.write(fila,4,'TOTAL '+elimina_tildes(formapago.nombre), titulo)
                        ws.write(fila,6,totalpagado, titulo)
                    if elimina_tildes(formapago.nombre)=="TARJETA DE CREDITO/DEBITO":
                        ws.write(fila,6,'TOTAL '+elimina_tildes(formapago.nombre), titulo)
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
                data['generarform']=FormasdePagoForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
                return render(request ,"reportesexcel/ingresos_formadepago.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")
    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

