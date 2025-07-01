from datetime import datetime, timedelta
import json
import xlwt
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from settings import MEDIA_ROOT
from sga.commonviews import addUserData
from sga.forms import RangoFacturasForm
from sga.models import convertir_fecha,TituloInstitucion, PagoPymentez, Rubro, Carrera, SeguimientoGraduado, Graduado, Persona, SesionCaja, Pago, PagoCheque, ReciboCajaInstitucion, PagoTransferenciaDeposito, ValeCaja, NotaCreditoInstitucion, PagoNotaCreditoInstitucion, Factura, PagoTarjeta, PagoReciboCajaInstitucion
from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action :
                try:
                    inicio = request.POST['inicio']
                    fin = request.POST['fin']
                    fechai = convertir_fecha(inicio)
                    fechaf = convertir_fecha(fin)+timedelta(hours=23,minutes=59)
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on; align: wrap on, vert center, horiz center')
                    titulo2 = xlwt.easyxf('font: bold on; align: vert center, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('Listado',cell_overwrite_ok=True)

                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,19, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,19, 'INFORME DE SESIONES DE CAJA POR RANGO DE FECHAS ', titulo2)
                    ws.write(2, 0, 'DESDE', titulo2)
                    ws.write(3, 0, 'HASTA:', titulo2)
                    ws.write(2, 1, str((fechai.date())), titulo2)
                    ws.write(3, 1, str((fechaf.date())), titulo2)

                    fila=9

                    ws.write_merge(fila, fila+1, 0,0,   'SESION', titulo)
                    ws.write_merge(fila, fila+1, 1,1,   'USUARIO',titulo)
                    ws.write_merge(fila, fila, 2,3,     'FACTURAS', titulo)
                    ws.write(fila+1, 2,                 'DESDE', titulo)
                    ws.write(fila+1, 3,                 'HASTA', titulo)
                    ws.write_merge(fila, fila+1, 4,4,   'EFECTIVO', titulo)
                    ws.write_merge(fila, fila+1, 5,5,   'TARJETA', titulo)
                    ws.write_merge(fila, fila+1, 6,6,   'CHEQUE', titulo)
                    ws.write_merge(fila, fila+1, 7,7,   'RECIBOS CAJA', titulo)
                    ws.write_merge(fila, fila+1, 8,8,   'TRANSFERENCIA O DEPOSITO', titulo)
                    ws.write_merge(fila, fila+1, 9,9,   'PICHINCHA', titulo)
                    ws.write_merge(fila, fila+1, 10,10, 'ELECTRONICO', titulo)
                    ws.write_merge(fila, fila+1, 11,11, 'WESTER', titulo)
                    ws.write_merge(fila, fila+1, 12,12, 'FACILITO', titulo)
                    ws.write_merge(fila, fila+1, 13,13, 'VALES', titulo)
                    ws.write_merge(fila, fila+1, 14,14, 'NC. ANULACION', titulo)
                    ws.write_merge(fila, fila+1, 15,15, 'PAGOS NC.', titulo)
                    ws.write_merge(fila, fila+1, 16,16, 'PAGOS REC.', titulo)
                    ws.write_merge(fila, fila+1, 17,17, 'REFERIDOS.', titulo)
                    ws.write_merge(fila, fila+1, 18,18, 'TOTAL CAJERO', titulo)
                    ws.write_merge(fila, fila+1, 19,19, 'TOTAL FACTURADO',titulo)

                    fila=11
                    sesioncaja = SesionCaja.objects.filter(fecha__gte=fechai, fecha__lte=fechaf).order_by('id')
                    ultima_sesion = sesioncaja.order_by('-id')[:1].get()
                    fecha = ''
                    fecha_nueva = ''
                    primer_valor=1
                    tot_valor4 = 0
                    tot_valor5 = 0
                    tot_valor6 = 0
                    tot_valor7 = 0
                    tot_valor8 = 0
                    tot_valor9 = 0
                    tot_valor10 = 0
                    tot_valor11 = 0
                    tot_valor12 = 0
                    tot_valor13 = 0
                    tot_valor14 = 0
                    tot_valor15 = 0
                    tot_valor16 = 0
                    tot_valor17 = 0
                    tot_valor18 = 0
                    tot_valor19 = 0

                    total_recibosgenerados=0
                    total_cruces=0
                    total_pendientes=0

                    total4=0
                    total5=0
                    total6=0
                    total7=0
                    total8=0
                    total9=0
                    total10=0
                    total11=0
                    total12=0
                    total13=0
                    total14=0
                    total15=0
                    total16=0
                    total17=0
                    total18=0
                    total19=0

                    for s in sesioncaja:
                        valor17=0
                        valor18=0
                        fecha = s.fecha
                        if fecha != fecha_nueva and primer_valor!=1:
                            ws.write_merge(fila, fila, 0,3,   'TOTAL DEL DIA: '+str((fecha)-(timedelta(hours=24))), titulo)
                            ws.write(fila, 4, (tot_valor4), titulo)
                            ws.write(fila, 5, (tot_valor5), titulo)
                            ws.write(fila, 6, (tot_valor6), titulo)
                            ws.write(fila, 7, (tot_valor7), titulo)
                            ws.write(fila, 8, (tot_valor8), titulo)
                            ws.write(fila, 9, (tot_valor9), titulo)
                            ws.write(fila, 10, (tot_valor10), titulo)
                            ws.write(fila, 11, (tot_valor11), titulo)
                            ws.write(fila, 12, (tot_valor12), titulo)
                            ws.write(fila, 13, (tot_valor13), titulo)
                            ws.write(fila, 14, (tot_valor14), titulo)
                            ws.write(fila, 15, (tot_valor15), titulo)
                            ws.write(fila, 16, (tot_valor16), titulo)
                            ws.write(fila, 17, (tot_valor17), titulo)
                            ws.write(fila, 18, (tot_valor18), titulo)
                            ws.write(fila, 19, (tot_valor19), titulo)
                            tot_valor4 = 0
                            tot_valor5 = 0
                            tot_valor6 = 0
                            tot_valor7 = 0
                            tot_valor8 = 0
                            tot_valor9 = 0
                            tot_valor10 = 0
                            tot_valor11 = 0
                            tot_valor12 = 0
                            tot_valor13 = 0
                            tot_valor14 = 0
                            tot_valor15 = 0
                            tot_valor16 = 0
                            tot_valor17 = 0
                            tot_valor18 = 0
                            tot_valor19 = 0
                            fila=fila+2
                            ws.write(fila, 0, str(s.fecha),titulo)
                            fila=fila+1
                        elif primer_valor==1:
                            ws.write(fila, 0, str(s.fecha),titulo)
                            fila=fila+1

                        ws.write(fila, 0, str(s.id))
                        try:
                            ws.write(fila, 1, str(s.caja.persona.usuario.username))
                        except:
                            ws.write(fila, 1, '')
                        try:
                            empieza=str(s.caja.puntoventa)+' | '+str(s.facturaempieza)
                            ws.write(fila, 2, empieza)
                        except:
                            ws.write(fila, 2, '')
                        try:
                            termina=str(s.caja.puntoventa)+' | '+str(s.facturatermina)
                            ws.write(fila, 3, termina)
                        except:
                            ws.write(fila, 3, '')
                        try:
                            pagos = Pago.objects.filter(fecha__gte=fechai, fecha__lte=fechaf, sesion=s, efectivo=True).order_by('fecha')
                            valor4=0
                            for p in pagos:
                                if p.valor:
                                    valor4 = valor4 + p.valor
                            ws.write(fila, 4, (valor4))
                        except:
                            ws.write(fila, 4, '')
                        try:
                            pagos = Pago.objects.filter(fecha__gte=fechai, fecha__lte=fechaf, sesion=s, efectivo=False).order_by('fecha')
                            valor5=0
                            for p in pagos:
                                if p.valor:
                                    if PagoTarjeta.objects.filter(pagos=p).exists():
                                        valor5 = valor5 + p.valor
                            ws.write(fila, 5, (valor5))
                        except:
                            ws.write(fila, 5, '')
                        try:
                            pagos = Pago.objects.filter(fecha__gte=fechai, fecha__lte=fechaf, sesion=s, efectivo=False).order_by('fecha')
                            valor6=0
                            for p in pagos:
                                if p.valor:
                                    if PagoCheque.objects.filter(fecha__gte=fechai, fecha__lte=fechaf, pagos=p).exists():
                                            valor6 = valor6 + p.valor
                            ws.write(fila, 6, (valor6))
                        except:
                            ws.write(fila, 6, '')
                        try:
                            valor7=0
                            if ReciboCajaInstitucion.objects.filter(sesioncaja=s).exists():
                                recibos = ReciboCajaInstitucion.objects.filter(sesioncaja=s).order_by('sesioncaja')
                                for r in recibos:
                                    total_recibosgenerados = total_recibosgenerados+1
                                    if r.saldo == 0:
                                        total_cruces = total_cruces+1
                                    elif r.saldo > 0:
                                        total_pendientes = total_pendientes+1
                                    if r.valorinicial:
                                        valor7 = valor7+r.valorinicial
                            ws.write(fila, 7, (valor7))
                        except:
                            ws.write(fila, 7, '')
                        try:
                            pagos = Pago.objects.filter(fecha__gte=fechai, fecha__lte=fechaf, sesion=s, efectivo=False).order_by('fecha')
                            valor8=0
                            for p in pagos:
                                if p.valor:
                                    if PagoTransferenciaDeposito.objects.filter(fecha__gte=fechai, fecha__lte=fechaf, pagos=p).exists():
                                        valor8 = valor8 + p.valor
                            ws.write(fila, 8, (valor8))
                        except:
                            ws.write(fila, 8, '')

                        try:
                            pagos = Pago.objects.filter(fecha__gte=fechai, fecha__lte=fechaf, sesion=s, efectivo=False, pichincha=True).order_by('fecha')
                            valor9=0
                            for p in pagos:
                                if p.valor:
                                    valor9 = valor9 + p.valor
                            ws.write(fila, 9, (valor9))
                        except:
                            ws.write(fila, 9, '')

                        try:
                            pagos = Pago.objects.filter(fecha__gte=fechai, fecha__lte=fechaf, sesion=s, efectivo=False, electronico=True).order_by('fecha')
                            valor10=0
                            for p in pagos:
                                if p.valor:
                                    valor10 = valor10 + p.valor
                            ws.write(fila, 10, (valor10))
                        except:
                            ws.write(fila, 10, '')
                        try:
                            pagos = Pago.objects.filter(fecha__gte=fechai, fecha__lte=fechaf, sesion=s, efectivo=False, wester=True).order_by('fecha')
                            valor11=0
                            for p in pagos:
                                if p.valor:
                                    valor11 = valor11 + p.valor
                            ws.write(fila, 11, (valor11))
                        except:
                            ws.write(fila, 11, '')
                        try:
                            pagos = Pago.objects.filter(fecha__gte=fechai, fecha__lte=fechaf, sesion=s, efectivo=False, facilito=True).order_by('fecha')
                            valor12=0
                            for p in pagos:
                                if p.valor:
                                    valor12 = valor12 + p.valor
                            ws.write(fila, 12, (valor12))
                        except:
                            ws.write(fila, 12, '')
                        try:
                            valescaja = ValeCaja.objects.filter(sesion=s, anulado=False, pendiente=True)
                            valor13=0
                            for v in valescaja:
                                if v.valor:
                                    valor13 = valor13 + v.valor
                            ws.write(fila, 13, (valor13))
                        except Exception as ex:
                            ws.write(fila, 13, '')
                        try:
                            notascredito = NotaCreditoInstitucion.objects.filter(sesioncaja=s, tipo__id=1).order_by('fecha')
                            valor14=0
                            for nc in notascredito:
                                if nc.valor:
                                    valor14 = valor14 + nc.valor
                            ws.write(fila, 14, (valor14))
                        except:
                            ws.write(fila, 14, '')
                        try:
                            pagos = Pago.objects.filter(fecha__gte=fechai, fecha__lte=fechaf, sesion=s).order_by('fecha')
                            valor15=0
                            for p in pagos:
                                if p.valor:
                                    if PagoNotaCreditoInstitucion.objects.filter(pagos=p, notacredito__sesioncaja=s).exists() and Factura.objects.filter(pagos=p):
                                        valor15 = valor15 + p.valor
                            ws.write(fila, 15, (valor15))
                        except Exception as ex:
                            ws.write(fila, 15, '')
                        try:
                            pagos = Pago.objects.filter(fecha__gte=fechai, fecha__lte=fechaf, sesion=s).order_by('fecha')
                            valor16=0
                            for p in pagos:
                                if p.valor:
                                    if PagoReciboCajaInstitucion.objects.filter(pagos=p).exists():
                                        valor16 = valor16 + p.valor
                            ws.write(fila, 16, (valor16))
                        except Exception as ex:
                            ws.write(fila, 16, '')

                        try:
                            pagos = Pago.objects.filter(sesion=s, referido=True).order_by('fecha')
                            valor17=0
                            for p in pagos:
                                if p.valor:
                                    if Factura.objects.filter(pagos=p).exists():
                                        valor17 = valor17 + p.valor
                            ws.write(fila, 17, (valor17))
                        except Exception as ex:
                            ws.write(fila, 17, '')

                        valor18 = valor4+valor5+valor6+valor7+valor8+valor9+valor10+valor11+valor12+valor14+valor15+valor16+valor17-valor13
                        ws.write(fila, 18, (valor18))
                        valor19 = valor4+valor5+valor6+valor8+valor9+valor10+valor11+valor12+valor14+valor15+valor16+valor17
                        ws.write(fila, 19, (valor19))

                        tot_valor4 = tot_valor4 + valor4
                        tot_valor5 = tot_valor5 + valor5
                        tot_valor6 = tot_valor6 + valor6
                        tot_valor7 = tot_valor7 + valor7
                        tot_valor8 = tot_valor8 + valor8
                        tot_valor9 = tot_valor9 + valor9
                        tot_valor10 = tot_valor10 + valor10
                        tot_valor11 = tot_valor11 + valor11
                        tot_valor12 = tot_valor12 + valor12
                        tot_valor13 = tot_valor13 + valor13
                        tot_valor14 = tot_valor14 + valor14
                        tot_valor15 = tot_valor15 + valor15
                        tot_valor16 = tot_valor16 + valor16
                        tot_valor17 = tot_valor17 + valor17
                        tot_valor18 = tot_valor18 + valor18
                        tot_valor19 = tot_valor19 + valor19

                        total4 = total4 + valor4
                        total5 = total5 + valor5
                        total6 = total6 + valor6
                        total7 = total7 + valor7
                        total8 = total8 + valor8
                        total9 = total9 + valor9
                        total10 = total10 + valor10
                        total11 = total11 + valor11
                        total12 = total12 + valor12
                        total13 = total13 + valor13
                        total14 = total14 + valor14
                        total15 = total15 + valor15
                        total16 = total16 + valor16
                        total17 = total17 + valor17
                        total18 = total18 + valor18
                        total19 = total19 + valor19

                        primer_valor=2
                        fecha_nueva = s.fecha
                        fila=fila+1

                        if ultima_sesion==s:
                            ws.write_merge(fila, fila, 0,3,   'TOTAL DEL DIA: '+str(fecha), titulo)
                            ws.write(fila, 4, (tot_valor4), titulo)
                            ws.write(fila, 5, (tot_valor5), titulo)
                            ws.write(fila, 6, (tot_valor6), titulo)
                            ws.write(fila, 7, (tot_valor7), titulo)
                            ws.write(fila, 8, (tot_valor8), titulo)
                            ws.write(fila, 9, (tot_valor9), titulo)
                            ws.write(fila, 10, (tot_valor10), titulo)
                            ws.write(fila, 11, (tot_valor11), titulo)
                            ws.write(fila, 12, (tot_valor12), titulo)
                            ws.write(fila, 13, (tot_valor13), titulo)
                            ws.write(fila, 14, (tot_valor14), titulo)
                            ws.write(fila, 15, (tot_valor15), titulo)
                            ws.write(fila, 16, (tot_valor16), titulo)
                            ws.write(fila, 17, (tot_valor17), titulo)
                            ws.write(fila, 18, (tot_valor18), titulo)
                            ws.write(fila, 19, (tot_valor19), titulo)

                            fila = fila+2
                            ws.write_merge(fila, fila, 0,3,   'TOTAL GENERAL: ', titulo)
                            ws.write(fila, 4, (total4), titulo)
                            ws.write(fila, 5, (total5), titulo)
                            ws.write(fila, 6, (total6), titulo)
                            ws.write(fila, 7, (total7), titulo)
                            ws.write(fila, 8, (total8), titulo)
                            ws.write(fila, 9, (total9), titulo)
                            ws.write(fila, 10, (total10), titulo)
                            ws.write(fila, 11, (total11), titulo)
                            ws.write(fila, 12, (total12), titulo)
                            ws.write(fila, 13, (total13), titulo)
                            ws.write(fila, 14, (total14), titulo)
                            ws.write(fila, 15, (total15), titulo)
                            ws.write(fila, 16, (total16), titulo)
                            ws.write(fila, 17, (total17), titulo)
                            ws.write(fila, 18, (total18), titulo)
                            ws.write(fila, 19, (total19), titulo)


                    ws.write_merge(5,5, 0,1, 'RECIBOS GENERADOS:', titulo2)
                    ws.write(5, 2, total_recibosgenerados, titulo2)
                    ws.write_merge(6,6, 0,1, 'CRUCES REALIZADOS:', titulo2)
                    ws.write(6, 2, total_cruces, titulo2)
                    ws.write_merge(7,7, 0,1, 'PENDIENTES DE CRUZAR:', titulo2)
                    ws.write(7, 2, total_pendientes, titulo2)

                    nombre ='resumen_sesionescajas'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(ex)
                    return HttpResponse(json.dumps({"result":str(ex) + " "+  str(s.id)}),content_type="application/json")
        else:
            data = {'title': 'Resumen Sesiones de Caja'}
            addUserData(request,data)
            if PagoPymentez.objects.filter(estado='success',detalle_estado='3').exists():
                data['generarform']=RangoFacturasForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
                return render(request ,"reportesexcel/resumen_sesionescajas.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")
    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))


