from datetime import datetime,timedelta
import json
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
from settings import UTILIZA_GRUPOS_ALUMNOS, EMAIL_ACTIVE,MEDIA_ROOT
from sga.commonviews import addUserData, ip_client_address, facturas_total_fecha, pagos_total_fecha, total_pagos_rango_fechas
from sga.forms import RangoFacturasForm
from sga.models import convertir_fecha,TituloInstitucion, Jornada

from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action :
                try:
                    m = 8
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo3 = xlwt.easyxf('font: name Times New Roman; align: wrap on, vert centre, horiz center')
                    subtitulo.font.height = 20*10
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('Registros',cell_overwrite_ok=True)

                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,13, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,13, 'INGRESO DE CAJA POR FECHA Y JORNADA',titulo2)

                    finicio = convertir_fecha( request.POST['inicio'])
                    ffin = convertir_fecha(request.POST['fin'])
                    jornada = Jornada.objects.all().order_by('nombre')

                    iterfecha = finicio
                    fila=2
                    col = 1
                    fila = fila +1
                    ws.write(fila,0,'FECHAS',titulo2)
                    for j in jornada:
                        ws.write(fila,col,j.nombre[:7],titulo2)
                        col=col+1
                    ws.write(fila,col,'TOTALES',titulo2)
                    while iterfecha <= ffin:
                        fila = fila +1
                        col = 1
                        ws.write(fila,0,str(iterfecha.date()))
                        for j in jornada:
                            totjornada = j.total_pagos_fecha_jornada(iterfecha)  + j.total_recibo_fecha(iterfecha) - j.total_ncpagos_fecha(iterfecha)
                            ws.write(fila,col,totjornada)
                            col=col+1
                        ws.write(fila,col,pagos_total_fecha(iterfecha))
                        iterfecha += timedelta(1)
                    fila = fila + 1
                    col = 1
                    ws.write(fila,0,'TOTALES',titulo2)
                    for j in jornada:
                        totpagogencar = j.total_pagos_rango_fechas_jornada(finicio,ffin)+j.total_recibo_rango_fechas(finicio,ffin) - j.total_ncpagos_rango_fechas(finicio,ffin)
                        ws.write(fila,col,totpagogencar)
                        col = col  +1
                    ws.write(fila,col,total_pagos_rango_fechas(finicio, ffin))
                    detalle = 3
                    detalle = detalle + fila
                    ws.write(detalle,0, "Fecha Impresion", subtitulo)
                    ws.write(detalle,1, str(datetime.now()), subtitulo)
                    detalle=detalle+2
                    ws.write(detalle,0, "Usuario", subtitulo)
                    ws.write(detalle,1, str(request.user), subtitulo)

                    nombre ='ingresos_por_jornada'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")
                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")

        else:
            data = {'title': 'Ingresos por Rango de Fecha'}
            addUserData(request,data)
            #if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                 #reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                 #data['reportes'] = reportes
            data['generarform']=RangoFacturasForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
            return render(request ,"reportesexcel/cobros_rango_fecha_jornada.html" ,  data)
            #return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

