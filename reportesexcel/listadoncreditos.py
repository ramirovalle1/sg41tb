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
from sga.forms import RangoFacturasForm,RangoNCForm
from sga.models import Inscripcion,convertir_fecha,Factura,ClienteFactura,TituloInstitucion,ReporteExcel,NotaCreditoInstitucion, Persona,TipoNotaCredito
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
                    fechaf = convertir_fecha(fin)
                    # totalvalornc=0
                    # totalvalornc = NotaCreditoInstitucion.objects.filter(fecha__gte=fechai,fecha__lte=fechaf).aggregate(Sum('valor'))['valor__sum']

                    ncreditos = NotaCreditoInstitucion.objects.filter(fecha__gte=fechai,fecha__lte=fechaf).order_by('fecha','numero')
                    m = 5
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10
                    style1 = xlwt.easyxf('',num_format_str='DD-MMM-YY')
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('Facturas',cell_overwrite_ok=True)

                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,m+2, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,m+2, 'LISTADO DE NOTAS DE CREDITOS', titulo2)
                    ws.write(3, 0, 'DESDE', titulo)
                    ws.write(3, 1, str((fechai.date())), titulo)
                    ws.write(4, 0, 'HASTA:', titulo)
                    ws.write(4, 1, str((fechaf.date())), titulo)

                    ws.write(7, 0,  'FECHA', titulo)
                    ws.write(7, 1,  'NUMERO', titulo)
                    ws.write(7, 2,  'MOTIVO', titulo)
                    ws.write(7, 3,  'No. FACTURA', titulo)
                    ws.write(7, 4,  'IDENTIF. ESTUDIANTE', titulo)
                    ws.write(7, 5,  'NOMBRE ESTUDIANTE', titulo)
                    ws.write(7, 6,  'IDENTIF. BENEFICIARIO', titulo)
                    ws.write(7, 7,  'NOMBRE BENEFICIARIO', titulo)
                    ws.write(7, 8,  'TIPO NC', titulo)
                    ws.write(7, 9,  'VALOR', titulo)

                    cabecera = 1
                    fila = 7
                    columna = 0
                    tot =0
                    detalle = 6
                    anterior = 0
                    actual = 0

                    descripcion=''
                    factura=''
                    cedulaest =''
                    pasaporteest=''
                    identificacionest=''
                    estudiante=''

                    cedulabenef =''
                    pasaportebenef=''
                    identificacionbenef=''
                    beneficiario=''

                    for nc in ncreditos:
                        fila = fila +1
                        columna=0

                        ws.write(fila,columna , str(nc.fecha))
                        ws.write(fila,columna+1, nc.numero)
                        descripcion = str(elimina_tildes(nc.motivo))
                        ws.write(fila,columna+2, descripcion)
                        factura=str(nc.factura.numero)
                        ws.write(fila,columna+3, factura)

                        cedulaest = str(elimina_tildes(nc.inscripcion.persona.cedula))
                        if not cedulaest:
                            pasaporteest = str(elimina_tildes(nc.inscripcion.persona.pasaporte))
                            identificacionest = pasaporteest
                        else:
                            identificacionest = cedulaest
                        ws.write(fila,columna+4, identificacionest)

                        estudiante= str(elimina_tildes(nc.inscripcion.persona))
                        ws.write(fila,columna+5, estudiante)

                        cedulabenef = str(elimina_tildes(nc.beneficiario.persona.cedula))
                        if not cedulabenef:
                            pasaportebenef = str(elimina_tildes(nc.beneficiario.persona.pasaporte))
                            identificacionbenef = pasaportebenef
                        else:
                            identificacionbenef = cedulabenef

                        ws.write(fila,columna+6, identificacionbenef)

                        beneficiario= str(elimina_tildes(nc.beneficiario.persona))
                        ws.write(fila,columna+7, beneficiario)

                        ws.write(fila,columna+8,nc.tipo.descripcion)
                        ws.write(fila,columna+9, nc.valor)

                    detalle = detalle + fila
                    ws.write(detalle, 0, "Fecha Impresion", subtitulo)
                    ws.write(detalle, 2, str(datetime.now()), subtitulo)
                    detalle=detalle +1
                    ws.write(detalle, 0, "Usuario", subtitulo)
                    ws.write(detalle, 2, str(request.user), subtitulo)

                    nombre ='ncreditos'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")

        else:
            data = {'title': 'Consulta de Notas de Creditos'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform']=RangoNCForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
                return render(request ,"reportesexcel/listadoncreditos.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

