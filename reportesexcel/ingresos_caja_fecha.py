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
from sga.commonviews import addUserData, ip_client_address
from sga.forms import FechaForm
from sga.models import convertir_fecha,TituloInstitucion,ReporteExcel,Carrera, Matricula, RecordAcademico, Egresado, Malla, AsignaturaMalla, NivelMalla, MateriaAsignada, Asignatura, Nivel, Periodo, ProfesorMateria, PagoNivel, Rubro, RubroMatricula, Pago, RubroCuota, SesionCaja, Factura, PagoReciboCajaInstitucion, PagoNotaCredito, PagoTransferenciaDeposito, PagoRetencion, PagoTarjeta, PagoCheque, ValeCaja, Coordinacion

from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action :
                try:
                    fecha = convertir_fecha(request.POST['fecha']).date()
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
                    ws.write_merge(1, 1,0,13, 'INGRESO DE CAJA',titulo2)
                    ws.write(2,0,'FECHA',subtitulo3)
                    ws.write(2,1,str(fecha),subtitulo3)
                    ws.write(4,0,"CAJA",subtitulo3)
                    ws.write(4,1,"EFECTIVO",subtitulo3)
                    ws.write(5,1,"VALOR",subtitulo3)
                    ws.write_merge(4,4,2,3,"CHEQUE",subtitulo3)
                    ws.write(5,2,"VALOR",subtitulo3)
                    ws.write(5,3,"CANT",subtitulo3)
                    ws.write_merge(4,4,4,5,"TARJETA",subtitulo3)
                    ws.write(5,4,"VALOR",subtitulo3)
                    ws.write(5,5,"CANT",subtitulo3)
                    ws.write_merge(4,4,6,7,"DEPOSITO",subtitulo3)
                    ws.write(5,6,"VALOR",subtitulo3)
                    ws.write(5,7,"CANT",subtitulo3)
                    ws.write_merge(4,4,8,9,"TRANSFERENCIA",subtitulo3)
                    ws.write(5,8,"VALOR",subtitulo3)
                    ws.write(5,9,"CANT",subtitulo3)
                    ws.write_merge(4,4,10,11,"RECIBO CAJA",subtitulo3)
                    ws.write(5,10,"VALOR",subtitulo3)
                    ws.write(5,11,"CANT",subtitulo3)
                    ws.write_merge(4,4,12,13,"NOTA CREDITO",subtitulo3)
                    ws.write(5,12,"VALOR",subtitulo3)
                    ws.write(5,13,"CANT",subtitulo3)
                    ws.write(4,14,"FACTURAS",subtitulo3)
                    ws.write(4,15,"TOTAL",subtitulo3)



                    #sesiones del dia con algun valor final
                    sesiones =[x for x in SesionCaja.objects.filter(fecha=fecha).order_by('caja__nombre') if x.total_sesion()]


                    fila =6
                    com = 7
                    detalle = 3
                    columna=3
                    matri=''
                    identificacion=''

                    for sesion in sesiones:

                        ws.write(fila,0, elimina_tildes(sesion.caja),subtitulo3)
                        ws.write(fila,1, sesion.total_efectivo_sesion(),subtitulo3)
                        ws.write(fila,2, sesion.cantidad_cheques_sesion() , subtitulo3)
                        ws.write(fila,3, sesion.total_cheque_sesion(),subtitulo3)
                        ws.write(fila,4, sesion.cantidad_tarjetas_sesion(),subtitulo3)
                        ws.write(fila,5, sesion.total_tarjeta_sesion(),subtitulo3)
                        ws.write(fila,6, sesion.cantidad_depositos_sesion() ,subtitulo3)
                        ws.write(fila,7, sesion.total_deposito_sesion() ,subtitulo3)
                        ws.write(fila,8, sesion.cantidad_transferencias_sesion() ,subtitulo3)
                        ws.write(fila,9, sesion.total_transferencia_sesion() ,subtitulo3)
                        ws.write(fila,10, sesion.cantidad_recibocaja_sesion(),subtitulo3)
                        ws.write(fila,11, sesion.total_recibocaja_sesion(),subtitulo3)
                        ws.write(fila,12, sesion.cantidad_notasdecredito_sesion(),subtitulo3)
                        ws.write(fila,13, sesion.total_notasdecredito_sesion(),subtitulo3)
                        ws.write(fila,14, sesion.cantidad_facturas_sesion() ,subtitulo3)
                        ws.write(fila,15, sesion.total_sesion() ,subtitulo3)
                        fila = fila +1

                    fila=fila+1
                    total_efectivo_dia = Pago.objects.filter(sesion__fecha=fecha, efectivo=True).aggregate(Sum('valor'))['valor__sum'] if Pago.objects.filter(sesion__fecha=fecha, efectivo=True).exists() else 0
                    cantidad_cheques_dia= PagoCheque.objects.filter(pagos__sesion__fecha=fecha).distinct().count()
                    total_cheque_dia= PagoCheque.objects.filter(pagos__sesion__fecha=fecha).aggregate(Sum('pagos__valor'))['pagos__valor__sum'] if PagoCheque.objects.filter(pagos__sesion__fecha=fecha).exists() else 0
                    cantidad_tarjetas_dia = PagoTarjeta.objects.filter(pagos__sesion__fecha=fecha).distinct().count()
                    total_tarjeta_dia = PagoTarjeta.objects.filter(pagos__sesion__fecha=fecha).aggregate(Sum('pagos__valor'))['pagos__valor__sum'] if PagoTarjeta.objects.filter(pagos__sesion__fecha=fecha).exists() else 0
                    cantidad_depositos_dia = PagoTransferenciaDeposito.objects.filter(pagos__sesion__fecha=fecha, deposito=True).distinct().count()
                    total_deposito_dia = PagoTransferenciaDeposito.objects.filter(pagos__sesion__fecha=fecha, deposito=True).aggregate(Sum('pagos__valor'))['pagos__valor__sum'] if  PagoTransferenciaDeposito.objects.filter(pagos__sesion__fecha=fecha, deposito=True).exists() else 0
                    cantidad_transferencias_dia = PagoTransferenciaDeposito.objects.filter(pagos__sesion__fecha=fecha, deposito=False).distinct().count()
                    total_transferencia_dia = PagoTransferenciaDeposito.objects.filter(pagos__sesion__fecha=fecha, deposito=False).aggregate(Sum('pagos__valor'))['pagos__valor__sum'] if PagoTransferenciaDeposito.objects.filter(pagos__sesion__fecha=fecha, deposito=False).exists() else 0
                    cantidad_recibocaja_dia = PagoReciboCajaInstitucion.objects.filter(pagos__sesion__fecha=fecha).distinct().count()
                    total_recibocaja_dia =  PagoReciboCajaInstitucion.objects.filter(pagos__sesion__fecha=fecha).aggregate(Sum('pagos__valor'))['pagos__valor__sum'] if PagoReciboCajaInstitucion.objects.filter(pagos__sesion__fecha=fecha).exists() else 0

                    cantidad_notadecredito_dia=PagoNotaCredito.objects.filter(pagos__sesion__fecha=fecha).count()
                    total_notadecredito_dia=PagoNotaCredito.objects.filter(pagos__sesion__fecha=fecha).aggregate(Sum('pagos__valor'))['pagos__valor__sum'] if PagoNotaCredito.objects.filter(pagos__sesion__fecha=fecha).exists() else 0

                    cantidad_facturas_dia =  Factura.objects.filter(pagos__sesion__fecha=fecha).distinct().count()
                    total_dia = total_efectivo_dia + total_cheque_dia+ total_deposito_dia + total_transferencia_dia + total_tarjeta_dia + total_notadecredito_dia + total_recibocaja_dia
                    ws.write(fila,1, total_efectivo_dia ,subtitulo3)
                    ws.write(fila,2, cantidad_cheques_dia ,subtitulo3)
                    ws.write(fila,3, total_cheque_dia ,subtitulo3)
                    ws.write(fila,4, cantidad_tarjetas_dia ,subtitulo3)
                    ws.write(fila,5, total_tarjeta_dia ,subtitulo3)
                    ws.write(fila,6, cantidad_depositos_dia ,subtitulo3)
                    ws.write(fila,7, total_deposito_dia ,subtitulo3)
                    ws.write(fila,8, cantidad_transferencias_dia ,subtitulo3)
                    ws.write(fila,9, total_transferencia_dia ,subtitulo3)
                    ws.write(fila,10, cantidad_recibocaja_dia ,subtitulo3)
                    ws.write(fila,11, total_recibocaja_dia ,subtitulo3)
                    ws.write(fila,12, cantidad_notadecredito_dia ,subtitulo3)
                    ws.write(fila,13, total_notadecredito_dia ,subtitulo3)
                    ws.write(fila,14, cantidad_facturas_dia ,subtitulo3)
                    ws.write(fila,15, total_dia ,subtitulo3)
                    fila =fila + 4
                    ws.write_merge(fila,fila,0,5,"RESUMEN DEL DIA POR COORDINACIONES",subtitulo3)
                    fila = fila+2
                    ws.write(fila,0, 'COORDINACION' ,subtitulo3)
                    ws.write(fila,1, 'FACTURAS' ,subtitulo3)
                    ws.write(fila,2, 'VALORES' ,subtitulo3)
                    ws.write(fila,3, 'MATRICULA' ,subtitulo3)
                    total_matriculados=0
                    for c in Coordinacion.objects.all().order_by('id'):
                        fila = fila+1
                        ws.write(fila,0,elimina_tildes(c.nombre) ,subtitulo3)
                        ws.write(fila,1,(c.cantidad_facturas_dia()) ,subtitulo3)
                        ws.write(fila,2,(c.total_pagos_dia()) ,subtitulo3)
                        ws.write(fila,3,(c.cantidad_matriculados()) ,subtitulo3)
                        total_matriculados = total_matriculados+c.cantidad_matriculados()


                    fila = fila+1
                    ws.write(fila,0, 'TOTALES' ,subtitulo3)
                    ws.write(fila,1, cantidad_facturas_dia ,subtitulo3)
                    ws.write(fila,2, total_dia ,subtitulo3)
                    ws.write(fila,3, total_matriculados ,subtitulo3)

                    fila =fila + 4
                    ws.write_merge(fila,fila,0,5,"RESUMEN DEL DIA POR CARRERAS",subtitulo3)
                    fila = fila+2
                    ws.write(fila,0, 'CARRERA' ,subtitulo3)
                    ws.write(fila,1, 'FACTURAS' ,subtitulo3)
                    ws.write(fila,2, 'VALORES' ,subtitulo3)
                    ws.write(fila,3, 'MATRICULA' ,subtitulo3)
                    total_matriculados_ca=0
                    for ca in Carrera.objects.all().order_by('id'):
                        fila = fila+1
                        ws.write(fila,0,elimina_tildes(ca.nombre) ,subtitulo3)
                        ws.write(fila,1,(ca.cantidad_facturas()) ,subtitulo3)
                        ws.write(fila,2,(ca.total_pagos()) ,subtitulo3)
                        ws.write(fila,3,(ca.mat_carrera2()) ,subtitulo3)
                        total_matriculados_ca = total_matriculados_ca+ca.mat_carrera2()


                    fila = fila+1
                    ws.write(fila,0, 'TOTALES' ,subtitulo3)
                    ws.write(fila,1, cantidad_facturas_dia ,subtitulo3)
                    ws.write(fila,2, total_dia ,subtitulo3)
                    ws.write(fila,3, total_matriculados_ca ,subtitulo3)




                    detalle = detalle + fila
                    ws.write(detalle,0, "Fecha Impresion", subtitulo)
                    ws.write(detalle,1, str(datetime.now()), subtitulo)
                    detalle=detalle+2
                    ws.write(detalle,0, "Usuario", subtitulo)
                    ws.write(detalle,1, str(request.user), subtitulo)

                    nombre ='ingresos_por_dia'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")

        else:
            data = {'title': 'Ingresos de Caja por Fecha'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform']=FechaForm(initial={'fecha':datetime.now().date()})
                return render(request ,"reportesexcel/ingresos_caja_fecha.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

