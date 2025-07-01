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
from sga.forms import RangoPagoTarjetasForm
from sga.models import Inscripcion,convertir_fecha,Factura,ClienteFactura,TituloInstitucion,ReporteExcel,Pago, PagoTarjeta,TipoTarjetaBanco, PagoPymentez
from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action :
                inicio = request.POST['inicio']
                fin = request.POST['fin']
                try:
                    m = 4
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10
                    style1 = xlwt.easyxf('',num_format_str='DD-MMM-YY')
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('Tarjetas',cell_overwrite_ok=True)
                    fechai = convertir_fecha(inicio)
                    fechaf = convertir_fecha(fin)+timedelta(hours=23,minutes=59)
                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,m+2, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,m+2, 'LISTADO DE PAGOS EN LINEA', titulo2)
                    ws.write(3, 0, 'DESDE', titulo)
                    ws.write(3, 1, str((fechai.date())), titulo)
                    ws.write(4, 0, 'HASTA:', titulo)
                    ws.write(4, 1, str((fechaf.date())), titulo)
                    ws.write(5, 0,  'FECHA TRANSACCION', titulo)
                    ws.write(5, 1,  'MONTO', titulo)
                    ws.write(5, 2,  'AUTORIZACION', titulo)
                    ws.write(5, 3,  'REFERENCIA', titulo)
                    ws.write(5, 4,  'TIPO TARJETA', titulo)
                    ws.write(5, 5,  'FACTURA', titulo)
                    ws.write(5, 6,  'LOTE', titulo)

                    cab = 5
                    fila = 6


                    for pp in PagoPymentez.objects.filter(fechatransaccion__gte=fechai,fechatransaccion__lte=fechaf,estado='success').order_by('fechatransaccion'):
                        tot = 0
                        totaltarjetas=0
                        pgt = TipoTarjetaBanco.objects.filter(alias=pp.tipo.upper())[:1].get()
                        numero =''
                        if pp.factura:
                            numero = pp.factura.numero

                        # for pagos in pagospy:
                        totaltarjetas=0
                        ws.write(fila,0,str(pp.fechatransaccion))
                        ws.write(fila,1, pp.monto)
                        ws.write(fila,2, pp.codigo_aut)
                        ws.write(fila,3, pp.referencia_tran)
                        ws.write(fila,4, pgt.nombre)
                        ws.write(fila,5,numero )
                        ws.write(fila,6,pp.lote )
                        # sin lote da error

                        fila=fila + 1
                        # ws.write(fila-1,c, totaltarjetas)

                    # detalle = detalle + fila
                    # ws.write(detalle, 0, "Fecha Impresion", subtitulo)
                    # ws.write(detalle, 1, str(datetime.now()), subtitulo)
                    # detalle=detalle +1
                    # ws.write(detalle, 0, "Usuario", subtitulo)
                    # ws.write(detalle, 1, str(request.user), subtitulo)

                    nombre ='pagoonline'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")
                #
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")

        else:
            data = {'title': 'Registro de Pagos Online'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
            data['generarform']=RangoPagoTarjetasForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
            return render(request ,"reportesexcel/pagoonline.html" ,  data)

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

