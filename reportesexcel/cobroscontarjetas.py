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
from sga.models import Inscripcion,convertir_fecha,Factura,ClienteFactura,TituloInstitucion,ReporteExcel,Pago, PagoTarjeta,TipoTarjetaBanco
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
                    m = 12
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
                    fechaf = convertir_fecha(fin)
                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,m+2, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,m+2, 'LISTADO DE PAGOS CON TARJETAS CREDITO/DEBITO', titulo2)
                    ws.write(3, 0, 'DESDE', titulo)
                    ws.write(3, 1, str((fechai.date())), titulo)
                    ws.write(4, 0, 'HASTA:', titulo)
                    ws.write(4, 1, str((fechaf.date())), titulo)
                    ws.write(7, 0,  'FECHA', titulo)
                    ws.write(7, 1,  'CAJA', titulo)
                    ws.write(7, 2,  'LOTE', titulo)
                    ws.write(7, 3,  'PROCESADOR', titulo)
                    ws.write(7, 4,  'TIPO TARJETA', titulo)

                    cab = 5

                    tipotarjeta = TipoTarjetaBanco.objects.filter().order_by('nombre')
                    # tipotarjeta = TipoTarjetaBanco.objects.filter().exclude(id=5).order_by('nombre')
                    for tipotarj in tipotarjeta:
                        ws.write(7,cab,str(tipotarj.nombre),titulo)
                        cab = cab +1

                    ws.write(7, cab,  'TOTAL', titulo)

                    detalle = 6
                    fila = 8
                    fecha=''
                    tptarjeta=''
                    cajero='cajero'
                    lote = ''
                    procesadorpago=''
                    totaltarjetas=0
                    lote2=None

                    for s in PagoTarjeta.objects.filter(fecha__gte=fechai,fecha__lte=fechaf).order_by('pagos__sesion').distinct('pagos__sesion').values('pagos__sesion'):

                        tot = 0
                        totaltarjetas=0
                        pgt=PagoTarjeta.objects.filter(fecha__gte=fechai,fecha__lte=fechaf,pagos__sesion__id=s['pagos__sesion'])[:1].get()
                        fecha=pgt.fecha
                        procesadorpago=pgt.procesadorpago.nombre
                        if pgt.tarjetadebito==True:
                           tptarjeta='DEBITO'
                        else:
                           tptarjeta='CREDITO'

                        for pagos in pgt.pagos.all():
                          cajero = pagos.sesion.caja.persona.nombre_completo_inverso()
                        ws.write(fila,0,str(fecha))
                        ws.write(fila,1, cajero)

                        for  l in PagoTarjeta.objects.filter(fecha__gte=fechai,fecha__lte=fechaf,pagos__sesion__id=s['pagos__sesion']).distinct('lote').values('lote').order_by('lote'):
                            c = 5
                            totaltarjetas=0
                            ws.write(fila,0,str(fecha))
                            ws.write(fila,1, cajero)
                            ws.write(fila,2, l['lote'])
                            ws.write(fila,3, procesadorpago)
                            ws.write(fila,4, tptarjeta)
                            # sin lote da error
                            if not l['lote']:
                                l['lote']=lote2

                            for p in  TipoTarjetaBanco.objects.filter().values('nombre').order_by('nombre'):
                                if  PagoTarjeta.objects.filter(tipo__nombre=p['nombre'],lote=l['lote']).exists():
                                    tot = float(0)
                                    for pt in PagoTarjeta.objects.filter(tipo__nombre=p['nombre'],lote=l['lote']):
                                        if pt.pagos.filter(sesion__id=s['pagos__sesion']).exists():
                                            tot = tot + pt.pagos.filter(sesion__id=s['pagos__sesion']).aggregate(Sum('valor'))['valor__sum']
                                    totaltarjetas=totaltarjetas+tot
                                else:
                                    tot = 0

                                ws.write(fila,c,tot)
                                c = c +1
                            ws.write(fila,c, totaltarjetas)
                            fila=fila + 1
                        ws.write(fila-1,c, totaltarjetas)

                    detalle = detalle + fila
                    ws.write(detalle, 0, "Fecha Impresion", subtitulo)
                    ws.write(detalle, 1, str(datetime.now()), subtitulo)
                    detalle=detalle +1
                    ws.write(detalle, 0, "Usuario", subtitulo)
                    ws.write(detalle, 1, str(request.user), subtitulo)

                    nombre ='tarjetas'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")

        else:
            data = {'title': 'Cobros con Tarjetas Credito Debito'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform']=RangoPagoTarjetasForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
            return render(request ,"reportesexcel/cobroscontarjetas.html" ,  data)

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

