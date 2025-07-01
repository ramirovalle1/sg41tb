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
from settings import UTILIZA_GRUPOS_ALUMNOS, EMAIL_ACTIVE,MEDIA_ROOT
from sga.commonviews import addUserData, ip_client_address
from sga.forms import RangoFacturasForm, RangoFacturasxFormaPagoForm
from sga.models import Inscripcion, convertir_fecha, Factura, ClienteFactura, TituloInstitucion, ReporteExcel, \
    PagoNivel, RubroCuota, RubroInscripcion, RubroMatricula, RubroOtro
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
                    formapago= False
                    if request.POST['formapago'] == 'true':
                        formapago = True
                    fechai = convertir_fecha(inicio)
                    fechaf = convertir_fecha(fin)
                    # totalfacturado=0
                    # totalfacturado = Factura.objects.filter(fecha__gte=fechai,fecha__lte=fechaf).aggregate(Sum('total'))['total__sum']
                    facturas = Factura.objects.filter(fecha__gte=fechai,fecha__lte=fechaf).order_by('fecha','numero')
                    m = 5
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10
                    titulo_rojo = xlwt.easyxf('font: name Times New Roman, colour red')

                    style1 = xlwt.easyxf('',num_format_str='DD-MMM-YY')
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('Facturas',cell_overwrite_ok=True)

                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,m+2, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,m+2, 'LISTADO DE FACTURAS', titulo2)
                    ws.write(3, 0, 'DESDE', titulo)
                    ws.write(3, 1, str((fechai.date())), titulo)
                    ws.write(4, 0, 'HASTA:', titulo)
                    ws.write(4, 1, str((fechaf.date())), titulo)

                    ws.write(7, 0,  'FECHA', titulo)
                    ws.write(7, 1,  'NUMERO', titulo)
                    ws.write(7, 2,  'IDENTIFICACION', titulo)
                    ws.write(7, 3,  'ESTUDIANTE', titulo)
                    ws.write(7, 4,  'CARRERA', titulo)
                    ws.write(7, 5, 'COORDINACION', titulo)
                    ws.write(7, 6,  'CLIENTE', titulo)
                    ws.write(7, 7,  'DESCRIPCION PAGO', titulo)
                    ws.write(7, 8,  'SUBTOTAL', titulo)
                    ws.write(7, 9,  'IVA', titulo)
                    ws.write(7, 10,  'TOTAL', titulo)
                    ws.write(7, 11, 'PAGADO', titulo)
                    if formapago:
                        ws.write(7, 13, 'FORMA DE PAGO', titulo)
                    ws.write(7, 12, 'DIAS VENCIDOS', titulo)
                    cabecera = 1
                    columna = 0
                    tot =0
                    detalle = 6
                    anterior = 0
                    actual = 0
                    fila = 7
                    descripcion=''
                    estudiante=''
                    carrera=''
                    identificacion=''
                    cedula =''
                    pasaporte=''

                    for factura in facturas:
                        fila = fila +1
                        columna=0

                        cliente = ClienteFactura.objects.filter(id=factura.cliente_id)[:1].get()
                        fila2=fila - 1
                        for pago in factura.pagos.all():
                            fila2=fila2 + 1
                            if pago:
                                ws.write(fila2,columna , str(factura.fecha))
                                ws.write(fila2,columna+1, factura.numero)
                                cedula = str(elimina_tildes(pago.rubro.inscripcion.persona.cedula))
                                if not cedula:
                                    pasaporte = str(elimina_tildes(pago.rubro.inscripcion.persona.pasaporte))
                                    identificacion = pasaporte
                                else:
                                    identificacion = cedula

                                ws.write(fila2,columna+2, identificacion)
                                try:
                                    estudiante= str(elimina_tildes(pago.rubro.inscripcion.persona))
                                except:
                                    estudiante = 'Error'
                                ws.write(fila2,columna+3, estudiante)
                                try:
                                    carrera = str(elimina_tildes(pago.rubro.inscripcion.carrera.nombre))
                                except:
                                    carrera ='Error'

                                ws.write(fila2,columna+4, carrera)
                                # COORDINACION
                                try:
                                    coord =pago.rubro.inscripcion.carrera.coordinacion_pertenece()
                                    if coord:
                                        coordinacion = str(elimina_tildes(coord.nombre))
                                    else:
                                        coordinacion = ''
                                except:
                                    coordinacion =''

                                ws.write(fila2, columna + 5, coordinacion)

                                try:
                                    nombre = cliente.nombre
                                except:
                                    nombre = "Error"

                                ws.write(fila2,columna+6,nombre)
                                # OCU 09-ene-2017
                                try:
                                    descripcion=str(elimina_tildes(pago.rubro))
                                except:
                                    descripcion = 'Error en descripcion'
                                ws.write(fila2,columna+7, descripcion)

                                ws.write(fila2,columna+8, factura.subtotal)
                                ws.write(fila2,columna+9, factura.iva)
                                ws.write(fila2,columna+10, factura.total)

                                ws.write(fila2,columna+11, pago.valor)
                                if formapago:
                                    forma_pago= pago.obtener_forma_pago()
                                    if forma_pago:
                                        formapagonombre = forma_pago.nombre
                                        ws.write(fila2,columna+13, str(formapagonombre))

                                rubroid = pago.rubro
                                fechapago = pago.fecha  # en que realizo el pago
                                tiporubro = pago.rubro.obtener_tipo_rubro()

                                if tiporubro.cuota and RubroCuota.objects.filter(rubro = rubroid).exists():
                                    tipos_rubros = RubroCuota.objects.filter(rubro = rubroid)[:1].get()
                                    tipo = tipos_rubros.cuota
                                    nivel = tipos_rubros.matricula.nivel
                                    if PagoNivel.objects.filter(tipo=tipo, nivel=nivel).exists():
                                        pago_cronograma = PagoNivel.objects.filter(tipo=tipo, nivel=nivel)[:1].get()
                                        fechacronograma = pago_cronograma.fecha  # pago del cronograma
                                    else:
                                        fechacronograma = pago.rubro.fechavence
                                elif tiporubro.matricula and RubroMatricula.objects.filter(rubro=rubroid).exists():
                                    tipos_rubros =  RubroMatricula.objects.filter(rubro=rubroid)[:1].get()
                                    tipo = 0 # matricula
                                    nivel = tipos_rubros.matricula.nivel
                                    if  PagoNivel.objects.filter(tipo=tipo, nivel=nivel).exists():
                                        pago_cronograma = PagoNivel.objects.filter(tipo=tipo, nivel=nivel)[:1].get()
                                        fechacronograma= pago_cronograma.fecha
                                    else:
                                        fechacronograma = pago.rubro.fechavence  # pago del cronograma
                                else:
                                    fechacronograma = pago.rubro.fechavence  # fecha del rubro

                                if fechapago > fechacronograma:
                                    dias_vencidos = (fechapago - fechacronograma).days
                                else:
                                    dias_vencidos = ''
                                ws.write(fila2, columna + 12, str(dias_vencidos), titulo_rojo)

                        fila=fila2
                    detalle = detalle + fila
                    ws.write(detalle, 0, "Fecha Impresion", subtitulo)
                    ws.write(detalle, 2, str(datetime.now()), subtitulo)
                    detalle=detalle +1
                    ws.write(detalle, 0, "Usuario", subtitulo)
                    ws.write(detalle, 2, str(request.user), subtitulo)

                    nombre ='facturas'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex) + " "+  str(factura.numero))
                    return HttpResponse(json.dumps({"result":str(ex) + " "+  str(factura.numero)}),content_type="application/json")


        else:
            data = {'title': 'Consulta de Facturas'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform']=RangoFacturasxFormaPagoForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
                return render(request ,"reportesexcel/listadofacturas.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

