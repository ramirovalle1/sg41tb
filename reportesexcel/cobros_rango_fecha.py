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
from settings import UTILIZA_GRUPOS_ALUMNOS, EMAIL_ACTIVE,MEDIA_ROOT, ASIG_VINCULACION, ASIG_PRATICA
from sga.commonviews import addUserData, ip_client_address, facturas_total_fecha, pagos_total_fecha, cantidad_facturas_total_fechas, total_pagos_rango_fechas, pagos_nctotal_fecha, total_ncpagos_rango_fechas, pagos_recibo_fecha, total_recibo_rango_fechas, total_pagos_rango_fechas_xls,total_pagos_facturas_rango_fechas,pagos_total_fecha2
from sga.forms import RangoCobrosForm
from sga.models import convertir_fecha,TituloInstitucion,ReporteExcel,Carrera, Matricula, RecordAcademico, Egresado, Malla, AsignaturaMalla, NivelMalla, MateriaAsignada, Asignatura, Nivel, Periodo, ProfesorMateria, PagoNivel, Rubro, RubroMatricula, Pago, RubroCuota, SesionCaja, Factura, PagoReciboCajaInstitucion, PagoNotaCredito, PagoTransferenciaDeposito, PagoRetencion, PagoTarjeta, PagoCheque, ValeCaja, Coordinacion

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
                    ws.write_merge(1, 1,0,13, 'INGRESO DE CAJA POR FECHA',titulo2)
                    carreras = [x for x in Carrera.objects.all().order_by('id') if x.mat_carrera2()]
                    finicio = convertir_fecha( request.POST['inicio'])
                    ffin = convertir_fecha(request.POST['fin'])
                    iterfecha = finicio
                    fila=2
                    col = 1
                    if request.POST['carrera'] == '1':
                        ws.write_merge(fila, fila,0,13, 'INGRESOS POR CARRERA',titulo2)
                        fila = fila +1
                        ws.write(fila,0,'FECHAS',titulo2)
                        for ca in carreras:
                            ws.write_merge(fila,fila,col,col+1,ca.alias,titulo2)
                            ws.write(fila+1,col,'FACTURAS',titulo2)
                            ws.write(fila+1,col+1,'VALORES',titulo2)
                            col=col+2
                        ws.write_merge(fila,fila,col,col+1,'TOTALES',titulo2)
                        ws.write(fila+1,col,'FACTURAS',titulo2)
                        ws.write(fila+1,col+1,'VALORES',titulo2)

                        fila = fila +1
                        while iterfecha <= ffin:
                            fila = fila +1
                            col = 1
                            ws.write(fila,0,str(iterfecha.date()))
                            for carrera in carreras:
                                 print(carrera)
                                 totcarrera = carrera.total_pagos_fecha2(iterfecha)  # + carrera.total_recibo_fecha(iterfecha) - carrera.total_ncpagos_fecha(iterfecha)
                                 ws.write(fila,col,carrera.cantidad_facturas_fecha(iterfecha))
                                 ws.write(fila,col+1,totcarrera )
                                 col=col+2
                            totpago =pagos_total_fecha2(iterfecha)  #+ pagos_recibo_fecha(iterfecha)- pagos_nctotal_fecha(iterfecha)
                            ws.write(fila,col,facturas_total_fecha(iterfecha))
                            ws.write(fila,col+1,totpago)
                            iterfecha += timedelta(1)
                        fila = fila + 1
                        col = 1
                        ws.write(fila,0,'TOTALES',titulo2)
                        for carrera in carreras:
                            totpagogencar = carrera.total_pagos_rango_fechas2(finicio,ffin) #+carrera.total_recibo_rango_fechas(finicio,ffin) - carrera.total_ncpagos_rango_fechas(finicio,ffin)
                            ws.write(fila,col,carrera.cantidad_facturas_rango_fechas(finicio, ffin))
                            ws.write(fila,col+1,totpagogencar)
                            col = col  +2
                        totpagogen = total_pagos_facturas_rango_fechas(finicio, ffin) #arreglado  #+ total_recibo_rango_fechas(finicio, ffin) #- total_ncpagos_rango_fechas(finicio, ffin)
                        ws.write(fila,col,cantidad_facturas_total_fechas(finicio, ffin))
                        ws.write(fila,col+1,totpagogen)

                    if request.POST['coord'] == '1':
                        ws.write_merge(fila, fila,0,13, 'INGRESOS POR FACULTAD',titulo2)
                        fila = fila +1
                        ws.write(fila,0,'FECHAS',titulo2)
                        for co in  Coordinacion.objects.all().order_by('id'):
                            ws.write_merge(fila,fila,col,col+1,co.nombre)
                            ws.write(fila+1,col,'FACTURAS',titulo2)
                            ws.write(fila+1,col+1,'VALORES',titulo2)
                            col=col+2
                        ws.write_merge(fila,fila,col,col+1,'TOTALES',titulo2)
                        ws.write(fila+1,col,'FACTURAS',titulo2)
                        ws.write(fila+1,col+1,'VALORES',titulo2)
                        fila=fila +1
                        iterfecha = finicio
                        while iterfecha <= ffin:
                            fila = fila +1
                            col = 1
                            ws.write(fila,0,str(iterfecha.date()))
                            for coordinacion in  Coordinacion.objects.all().order_by('id'):
                                 print(coordinacion)
                                 totocpr = coordinacion.total_pagos_fecha2(iterfecha) #+coordinacion.total_recibo_fecha(iterfecha) - coordinacion.total_ncpagos_fecha(iterfecha)
                                 ws.write(fila,col,coordinacion.cantidad_facturas_fecha(iterfecha))
                                 ws.write(fila,col+1,totocpr)
                                 col=col+2
                            tot = pagos_total_fecha2(iterfecha)  #+pagos_recibo_fecha(iterfecha) - pagos_nctotal_fecha(iterfecha)
                            ws.write(fila,col,facturas_total_fecha(iterfecha))
                            ws.write(fila,col+1,tot)
                            iterfecha += timedelta(1)
                        fila = fila + 1
                        col = 1
                        ws.write(fila,0,'TOTALES',titulo2)
                        for co in  Coordinacion.objects.all().order_by('id'):
                            totgcoor = co.total_pagos_rango_fechas2(finicio,ffin) #+ co.total_recibo_rango_fechas(finicio,ffin) - co.total_ncpagos_rango_fechas(finicio,ffin)
                            ws.write(fila,col,co.cantidad_facturas_rango_fechas(finicio, ffin))
                            ws.write(fila,col+1,totgcoor)
                            col = col  +2
                        totgencoor = total_pagos_facturas_rango_fechas(finicio, ffin) #+total_recibo_rango_fechas(finicio, ffin) - total_ncpagos_rango_fechas(finicio, ffin)
                        ws.write(fila,col,cantidad_facturas_total_fechas(finicio, ffin))
                        ws.write(fila,col+1,totgencoor)
                    detalle = 2
                    detalle = detalle + fila
                    ws.write(detalle,0, "Fecha Impresion", subtitulo)
                    ws.write(detalle,1, str(datetime.now()), subtitulo)
                    detalle=detalle+2
                    ws.write(detalle,0, "Usuario", subtitulo)
                    ws.write(detalle,1, str(request.user), subtitulo)

                    nombre ='cobros_rango_fecha'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")

        else:
            data = {'title': 'Ingresos por Rango de Fecha'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                 reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                 data['reportes'] = reportes
                 data['generarform']=RangoCobrosForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
                 return render(request ,"reportesexcel/cobros_rango_fecha.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

