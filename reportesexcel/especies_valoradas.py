from datetime import datetime,timedelta
import json
import xlwt

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from settings import MEDIA_ROOT
from sga.commonviews import addUserData
from sga.forms import RangoFacturasForm
from sga.models import convertir_fecha,TituloInstitucion,ReporteExcel, RubroEspecieValorada
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
                    # totalfacturado=0
                    # totalfacturado = Factura.objects.filter(fecha__gte=fechai,fecha__lte=fechaf).aggregate(Sum('total'))['total__sum']
                    m = 5
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10
                    style1 = xlwt.easyxf('',num_format_str='DD-MMM-YY')
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('EspeciesValoradas',cell_overwrite_ok=True)

                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,m+2, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,m+2, 'Listado de Especies Valoradas', titulo2)
                    ws.write(3, 0, 'DESDE', titulo)
                    ws.write(3, 1, str((fechai.date())), titulo)
                    ws.write(4, 0, 'HASTA:', titulo)
                    ws.write(4, 1, str((fechaf.date())), titulo)

                    ws.write(7, 0,  'FECHA', titulo)
                    ws.write(7, 1,  'TIPO', titulo)
                    ws.write(7, 2,  'ESTUDIANTE', titulo)
                    ws.write(7, 3,  'SERIE', titulo)
                    ws.write(7, 4,  'MONTO', titulo)

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

                    for re in  RubroEspecieValorada.objects.filter(rubro__fecha__gte=fechai,rubro__fecha__lte=fechaf).order_by('tipoespecie'):
                        columna=0
                        if re.rubro.cancelado:
                            fila = fila +1
                            ws.write(fila,0 ,str(re.rubro.fecha))
                            ws.write(fila,1 ,elimina_tildes(re.tipoespecie.nombre))
                            try:
                                nombreest = elimina_tildes(re.rubro.inscripcion.persona.nombre_completo())
                            except:
                                nombreest ='Error Nombre'

                            ws.write(fila,2 ,nombreest)
                            ws.write(fila,3 ,str(re.serie))
                            ws.write(fila,4 ,str(re.rubro.valor))
                    detalle = detalle + fila
                    ws.write(detalle, 0, "Fecha Impresion", subtitulo)
                    ws.write(detalle, 2, str(datetime.now()), subtitulo)
                    detalle=detalle +1
                    ws.write(detalle, 0, "Usuario", subtitulo)
                    ws.write(detalle, 2, str(request.user), subtitulo)

                    nombre ='especiresvaloradas'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex) + " ")
                    return HttpResponse(json.dumps({"result":str(ex) }),content_type="application/json")
        else:
            data = {'title': 'Consulta de Especies Valoradas'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform']=RangoFacturasForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
                return render(request ,"reportesexcel/especiesvaloradas.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

