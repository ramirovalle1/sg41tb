from datetime import datetime, timedelta
import json
import xlwt
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from settings import MEDIA_ROOT
from sga.commonviews import addUserData
from sga.forms import RangoFacturasForm
from sga.models import convertir_fecha,TituloInstitucion, PagoPymentez, Rubro
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
                    fechai = convertir_fecha(inicio)
                    fechaf = convertir_fecha(fin)+timedelta(hours=23,minutes=59)
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('Facturas',cell_overwrite_ok=True)

                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,16, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,16, 'LISTADO DE PAGOS EN LINEA', titulo2)
                    ws.write(3, 0, 'DESDE', titulo)
                    ws.write(3, 1, str((fechai.date())), titulo)
                    ws.write(4, 0, 'HASTA:', titulo)
                    ws.write(4, 1, str((fechaf.date())), titulo)

                    ws.write(6, 0,  'FECHA TRANSACCION', titulo)
                    ws.write(6, 1,  'NOMBRES ALUMNO', titulo)
                    ws.write(6, 2,  'CEDULA', titulo)
                    ws.write(6, 3,  'FACTURA', titulo)
                    ws.write(6, 4,  'FECHA DE FACTURA', titulo)
                    ws.write(6, 5,  'MONTO', titulo)
                    ws.write(6, 6,  'CODIGO AUTORIZACION', titulo)
                    ws.write(6, 7,  'REFERENCIA DEV', titulo)
                    ws.write(6, 8,  'RUBROS', titulo)
                    ws.write(6, 9,  'MENSAJE', titulo)
                    ws.write(6, 10, 'REFERENCIA TRANSACCION', titulo)
                    ws.write(6, 11, 'TIPO', titulo)
                    ws.write(6, 12, 'CORREO FACTURA', titulo)
                    ws.write(6, 13, 'PERSONA FACTURA', titulo)
                    ws.write(6, 14, 'DIRECCION', titulo)
                    ws.write(6, 15, 'RUC', titulo)
                    ws.write(6, 16, 'TELEFONO', titulo)
                    ws.write(6, 17, 'FECHA', titulo)
                    ws.write(6, 18, 'ANULADO', titulo)
                    ws.write(6, 19, 'MOTIVO', titulo)
                    ws.write(6, 20, 'DETALLE', titulo)
                    ws.write(6, 21, 'USUARIO ANULA', titulo)
                    ws.write(6, 22, 'FECHA ANULACION', titulo)
                    ws.write(6, 23, 'LOTE', titulo)
                    fila = 6
                    pagos = PagoPymentez.objects.filter(fechatransaccion__gte=fechai,fechatransaccion__lte=fechaf, estado='success', detalle_estado='3').order_by('fechatransaccion')
                    for p in pagos:
                        fila = fila +1
                        columna=0
                        if pagos:
                            ws.write(fila,columna , str(elimina_tildes(p.fechatransaccion.date())))
                            ws.write(fila,columna+1 , str(elimina_tildes(p.inscripcion.persona.nombre_completo_inverso())))
                            cedula = str(elimina_tildes(p.inscripcion.persona.cedula))
                            if not cedula:
                                pasaporte = str(elimina_tildes(p.inscripcion.persona.pasaporte))
                                identificacion = pasaporte
                            else:
                                identificacion = cedula
                            ws.write(fila,columna+2, identificacion)

                            try:
                                factura = str(elimina_tildes(p.factura.numero))
                            except:
                                factura = ''
                            ws.write(fila,columna+3, factura)

                            try:
                                factura_fecha = str(elimina_tildes(p.factura.fecha))
                            except:
                                factura_fecha = ''
                            ws.write(fila,columna+4, factura_fecha)
                            ws.write(fila,columna+5, str(p.monto))
                            try:
                                codigo = str(p.codigo_aut)
                            except:
                                codigo = ''
                            ws.write(fila,columna+6, codigo)
                            try:
                                ref = str(p.referencia_dev)
                            except:
                                ref = ''
                            ws.write(fila,columna+7, ref)

                            rub = ''
                            rubro = p.rubros
                            rubros = rubro.split(',')
                            for r in rubros:
                                if Rubro.objects.filter(pk=r).exists():
                                    rubro = Rubro.objects.filter(pk=r)[:1].get()
                                    rub = rub + (str(elimina_tildes(rubro.nombre()))) + ' | '
                            ws.write(fila, columna+8, rub)

                            try:
                                mensaje = str(elimina_tildes(p.mensaje))
                            except:
                                mensaje = ''
                            ws.write(fila, columna+9, mensaje)
                            ws.write(fila, columna+10, str(elimina_tildes(p.referencia_tran)))
                            ws.write(fila, columna+11, str(elimina_tildes(p.tipo)))
                            ws.write(fila, columna+12, str(elimina_tildes(p.correo)))
                            ws.write(fila, columna+13, str(elimina_tildes(p.nombre)))
                            try:
                                direccion = str(elimina_tildes(p.direccion))
                            except:
                                direccion = ''
                            ws.write(fila, columna+14, direccion)
                            ws.write(fila, columna+15, str(elimina_tildes(p.ruc)))
                            ws.write(fila, columna+16, str(elimina_tildes(p.telefono)))
                            try:
                                fecha = str(elimina_tildes(p.fecha.date()))
                            except:
                                fecha = ''
                            ws.write(fila, columna+17, fecha)
                            if p.anulado == True:
                                ws.write(fila, columna+18, 'SI')
                                ws.write(fila, columna+19, str(elimina_tildes(p.motivo)))
                                ws.write(fila, columna+20, str(elimina_tildes(p.detalle)))
                                try:
                                    user = str(elimina_tildes(p.usuarioanula.username))
                                except:
                                    user = ''
                                ws.write(fila, columna+21, user)
                                try:
                                    fecha_anula = str(elimina_tildes(p.fechaanula.date()))
                                except:
                                    fecha_anula = ''
                                ws.write(fila, columna+22, fecha_anula)
                            else:
                                ws.write(fila, columna+18, 'NO')
                            ws.write(fila, columna+23, p.lote)
                    ws.write(fila+2, 0, "Fecha Impresion: ", subtitulo)
                    ws.write(fila+2, 1, str(datetime.now()), subtitulo)
                    ws.write(fila+3, 0, "Usuario: ", subtitulo)
                    ws.write(fila+3, 1, str(request.user), subtitulo)

                    nombre ='Pagos en linea'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    return HttpResponse(json.dumps({"result":str(ex) + " "+  str(p.inscripcion)}),content_type="application/json")
        else:
            data = {'title': 'Consultas de Pagos en Linea'}
            addUserData(request,data)
            if PagoPymentez.objects.filter(estado='success',detalle_estado='3').exists():
                pagos = PagoPymentez.objects.filter(estado='success',detalle_estado='3').exists()
                data['pagos'] = pagos
                data['generarform']=RangoFacturasForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
                return render(request ,"reportesexcel/pagopymentez.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")
    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

