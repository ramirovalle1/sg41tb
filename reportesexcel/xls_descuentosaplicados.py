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
from settings import MEDIA_ROOT, SITE_ROOT
from sga.commonviews import addUserData, ip_client_address
from sga.forms import RangoPagoTarjetasForm
from sga.models import convertir_fecha,TituloInstitucion,ReporteExcel,DetalleDescuento
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
                    ws = wb.add_sheet('Registro',cell_overwrite_ok=True)
                    fechai = convertir_fecha(inicio)
                    fechaf = convertir_fecha(fin)+timedelta(hours=23,minutes=59)
                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,m+2, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,m+2, 'VALORES TOTALES DE DESCUENTOS APLICADOS', titulo2)
                    ws.write(3, 0, 'DESDE', titulo)
                    ws.write(3, 1, str((fechai.date())), titulo)
                    ws.write(4, 0, 'HASTA:', titulo)
                    ws.write(4, 1, str((fechaf.date())), titulo)

                    ws.write(6, 0,  'ENERO', titulo)
                    ws.write(7, 0,  'FEBRERO', titulo)
                    ws.write(8, 0,  'MARZO', titulo)
                    ws.write(9, 0,  'ABRIL', titulo)
                    ws.write(10,0,  'MAYO', titulo)
                    ws.write(11,0,  'JUNIO', titulo)
                    ws.write(12,0,  'JULIO', titulo)
                    ws.write(13,0,  'AGOSTO', titulo)
                    ws.write(14,0,  'SEPTIEMBRE', titulo)
                    ws.write(15,0,  'OCTUBRE', titulo)
                    ws.write(16,0,  'NOVIEMBRE', titulo)
                    ws.write(17,0,  'DICIEMBRE', titulo)

                    #cab = 5
                    fila = 6
                    detalle=5
                    enero=0
                    febrero=0
                    marzo=0
                    abril=0
                    mayo=0
                    junio=0
                    julio=0
                    agosto=0
                    septiembre=0
                    octubre=0
                    noviembre=0
                    diciembre=0
                    total=0
                    for detcto in DetalleDescuento.objects.filter(descuento__fecha__gte=fechai,descuento__fecha__lte=fechaf).order_by('descuento__fecha'):
                        #print(detcto)
                        if detcto.descuento.fecha.month == 1:
                            enero+=detcto.valor
                        elif detcto.descuento.fecha.month == 2:
                            febrero+=detcto.valor
                        elif detcto.descuento.fecha.month == 3:
                            marzo+=detcto.valor
                        elif detcto.descuento.fecha.month == 4:
                            abril+=detcto.valor
                        elif detcto.descuento.fecha.month == 5:
                            mayo+=detcto.valor
                        elif detcto.descuento.fecha.month == 6:
                            junio+=detcto.valor
                        elif detcto.descuento.fecha.month == 7:
                            julio+=detcto.valor
                        elif detcto.descuento.fecha.month == 8:
                            agosto+=detcto.valor
                        elif detcto.descuento.fecha.month == 9:
                            septiembre+=detcto.valor
                        elif detcto.descuento.fecha.month == 10:
                            octubre+=detcto.valor
                        elif detcto.descuento.fecha.month == 11:
                            noviembre+=detcto.valor
                        elif detcto.descuento.fecha.month == 12:
                            diciembre+=detcto.valor

                    total=enero+febrero+marzo+abril+mayo+junio+julio+agosto+septiembre+octubre+noviembre+diciembre

                    ws.write(fila,1,enero)
                    ws.write(fila+1,1,febrero)
                    ws.write(fila+2,1,marzo)
                    ws.write(fila+3,1,abril)
                    ws.write(fila+4,1,mayo)
                    ws.write(fila+5,1,junio )
                    ws.write(fila+6,1,julio )
                    ws.write(fila+7,1,agosto )
                    ws.write(fila+8,1,septiembre )
                    ws.write(fila+9,1,octubre )
                    ws.write(fila+10,1,noviembre )
                    ws.write(fila+11,1,diciembre )

                    fila=fila+12
                    ws.write(fila,0,'TOTAL',subtitulo )
                    ws.write(fila,1,total,subtitulo )
                    detalle = detalle + fila
                    ws.write(detalle, 0, "Fecha Impresion", subtitulo)
                    ws.write(detalle, 1, str(datetime.now()), subtitulo)
                    detalle=detalle +1
                    ws.write(detalle, 0, "Usuario", subtitulo)
                    ws.write(detalle, 1, str(request.user), subtitulo)

                    nombre ='descuentos'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")
                #
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")

        else:
            data = {'title': 'Descuentos por Rango de Fechas'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform']=RangoPagoTarjetasForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
                return render(request ,"reportesexcel/descuentosaplicados.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

