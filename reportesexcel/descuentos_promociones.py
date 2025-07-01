from datetime import datetime,timedelta
import json
import xlwt
import xlrd
from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render

from sga.forms import  RangoPagoTarjetasForm
from sga.models import TituloInstitucion, Inscripcion, elimina_tildes, ReporteExcel, convertir_fecha, Carrera, Descuento,DetalleDescuento
from sga.commonviews import addUserData
from settings import MEDIA_ROOT


@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action :

                inicio = request.POST['inicio']
                fin = request.POST['fin']
                fechai = convertir_fecha(inicio)
                fechaf = convertir_fecha(fin)
                carrera=''
                try:
                    m = 3
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10
                    style1 = xlwt.easyxf('',num_format_str='DD-MMM-YY')
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('Promociones',cell_overwrite_ok=True)
                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,m+2, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,m+2, 'TOTAL PROMOCIONES POR CARRERA ', titulo2)
                    detalle = 4
                    fila = 2
                    totaldescuentos=0
                    for carrera in Carrera.objects.filter(carrera=True).exclude(id__in=[63,66]).order_by('nombre'):
                        # print(carrera)
                        descuentocarrera=0
                        if DetalleDescuento.objects.filter(descuento__fecha__gte=fechai,descuento__fecha__lte=fechaf,descuento__inscripcion__carrera=carrera).exists():
                            descuentocarrera = DetalleDescuento.objects.filter(descuento__fecha__gte=fechai,descuento__fecha__lte=fechaf,descuento__inscripcion__carrera=carrera).aggregate(Sum('valor'))['valor__sum']
                            totaldescuentos+=descuentocarrera
                        ws.write(fila, 0, elimina_tildes(carrera.nombre))
                        ws.write(fila, 1, descuentocarrera )
                        fila=fila + 1

                    ws.write(fila, 0, 'TOTALES:',subtitulo)
                    ws.write(fila, 1, totaldescuentos,subtitulo )

                    detalle = detalle + fila
                    ws.write(detalle, 0, "Fecha Impresion", subtitulo)
                    ws.write(detalle, 1, str(datetime.now()), subtitulo)
                    detalle=detalle +1
                    ws.write(detalle, 0, "Usuario", subtitulo)
                    ws.write(detalle, 1, str(request.user), subtitulo)

                    nombre ='datos'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    return HttpResponse(json.dumps({"result":str(ex)+str(carrera)}), content_type="application/json")

        else:
            data = {'title': 'Descuentos en Promociones por Carrera y Rango de Fechas '}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform'] = RangoPagoTarjetasForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
                return render(request ,"reportesexcel/descuentos_promociones.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        print((e))
        return HttpResponseRedirect('/?info='+str(e))