from datetime import datetime
import json
import xlwt
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from settings import MEDIA_ROOT
from sga.commonviews import addUserData
from sga.forms import TotalEstudiantesXAnioForm, RangoFacturasForm
from sga.models import TituloInstitucion, ReporteExcel, SesionCaja, convertir_fecha


@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']

            if action  =='generarexcel':
                try:
                    inicio = request.POST['inicio']
                    fin = request.POST['fin']
                    fechai = convertir_fecha(inicio)
                    fechaf = convertir_fecha(fin)

                    #TITULO
                    titulo = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20 * 11
                    #CABECERA DE LA TABLA
                    titulocabecera =  xlwt.easyxf('font: name Times New Roman, colour black, bold on; align: wrap on, vert centre, horiz center')
                    titulocabecera.font.height = 20*11
                    # CONTENIDO DE LA TABLA
                    contenido = xlwt.easyxf('font: name Times New Roman')
                    contenido.font.height = 20 * 11
                    #ADICIONALS
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10

                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('LISTADO',cell_overwrite_ok=True)

                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,14, tit.nombre , titulo)
                    ws.write_merge(1, 1,0,14, 'SESIONES DE COBRANZA EN CAJA', titulo)
                    ws.write(2, 0, 'Desde:   ' + str(fechai), subtitulo)
                    ws.write(3, 0, 'Hasta:   ' + str(fechaf), subtitulo)

                    fila =5
                    ws.write(fila, 0,  'NUMERO', titulocabecera)
                    ws.write(fila, 1,  'CAJA', titulocabecera)
                    ws.col(1).width = 10 * 2100
                    ws.write(fila, 2,  'FECHA INICIO', titulocabecera)
                    ws.col(2).width = 10 * 450
                    ws.write(fila, 3,  'HORA INICIO', titulocabecera)
                    ws.col(3).width = 10 * 400
                    ws.write(fila, 4,  'FECHA FIN', titulocabecera)
                    ws.col(4).width = 10 * 350
                    ws.write(fila, 5,  'HORA FIN', titulocabecera)
                    ws.write(fila, 6,  'FONDO', titulocabecera)
                    ws.write(fila, 7,  'FACTURA COMIENZA', titulocabecera)
                    ws.col(7).width = 10 * 600
                    ws.write(fila, 8,  'FACTURA TERMINA', titulocabecera)
                    ws.col(8).width = 10 * 600
                    ws.write(fila, 9,  'ABIERTA', titulocabecera)

                    sesiones = SesionCaja.objects.filter(fecha__gte= fechai,fecha__lte= fechaf).order_by('-id','-fecha','-hora')
                    totalsesiones = sesiones.count()
                    fondo=0
                    fila =6
                    for s in sesiones:
                        if s.id:
                            numero = s.id
                        else:
                            numero =''
                        caja_venta = str(s.caja)+ str(s.caja.puntoventa)
                        if s.fecha:
                            fecha_inicio = s.fecha
                        else:
                            fecha_inicio =''
                        if s.hora:
                            hora_inicio = s.hora.strftime('%H:%M')
                        else:
                            hora_inicio = ''
                        cierre_sesion =s.cierre_sesion()
                        if cierre_sesion:
                            fecha_cierre =cierre_sesion.fecha
                            hora_cierre = cierre_sesion.hora.strftime('%H:%M')
                        else:
                            fecha_cierre=''
                            hora_cierre =''
                        if s.fondo:
                            fondo = s.fondo
                        else:
                            fondo = 0
                        if s.facturaempieza:
                            factura_empieza = s.facturaempieza
                        else:
                            factura_empieza =''
                        if s.facturatermina:
                            factura_termina = s.facturatermina
                        else:
                            factura_termina =''
                        if s.abierta:
                            sesion_abierta = "SI"
                        else:
                            sesion_abierta = "NO"
                        ws.write(fila, 0, numero, contenido)
                        ws.write(fila, 1, caja_venta, contenido)
                        ws.write(fila, 2, str(fecha_inicio), contenido)
                        ws.write(fila, 3, str(hora_inicio), contenido)
                        ws.write(fila, 4, str(fecha_cierre),contenido)
                        ws.write(fila, 5, str(hora_cierre), contenido)
                        ws.write(fila, 6, "$"+ str(fondo), contenido)
                        ws.write(fila, 7, factura_empieza, contenido)
                        ws.write(fila, 8, factura_termina,contenido)
                        ws.write(fila, 9, sesion_abierta, contenido)
                        fila = fila + 1

                    fila = fila + 1
                    ws.write(fila,0, "Sesiones: "+ str(totalsesiones), subtitulo)
                    fila = fila + 1
                    ws.write(fila,0, "Fecha Impresion", subtitulo)
                    ws.write(fila,1, str(datetime.now()), subtitulo)
                    fila = fila + 1
                    ws.write(fila,0, "Usuario", subtitulo)
                    ws.write(fila,1, str(request.user), subtitulo)

                    nombre ='sessionescobranzacaja'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}), content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)}), content_type="application/json")
        else:
            data = {'title': 'Sesiones de Cobranza en Caja '}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform'] = RangoFacturasForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
                return render(request,"reportesexcel/xls_sesiones_caja.html", data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))
