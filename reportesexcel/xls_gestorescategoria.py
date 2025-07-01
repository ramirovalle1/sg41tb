from datetime import datetime,timedelta, date
import json
from requests.packages.urllib3 import request
import xlwt
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from settings import MEDIA_ROOT
from sga.commonviews import addUserData
from sga.forms import EntregaUniformeExcelForm
from sga.models import Inscripcion,convertir_fecha,TituloInstitucion, RubroSeguimiento, AsistAsuntoEstudiant, CategoriaRubro, Rubro
from fpdf import FPDF
from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action =='generarexcel':
                    nombre = ejecutar_inscripcioncategoria(request,request.POST['desde'], request.POST['hasta'],request.user)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

        else:
            data = {'title': 'Estudiantees Absentos por Rango de Fechas'}
            addUserData(request,data)
            # if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
            #     reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
            #     data['reportes'] = reportes
            data['generarform']=EntregaUniformeExcelForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
            return render(request ,"reportesexcel/compromisopagos_xfecha.html" ,  data)
            # return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

def ejecutar_inscripcioncategoria(request,usuario):
    try:
        titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on;align: wrap on, vert centre, horiz center')
        titulo1 = xlwt.easyxf('font: bold on,colour green, bold on; align: wrap on, vert centre, horiz center')
        titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
        titulo.font.height = 20*11
        titulo2.font.height = 20*11
        subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
        subtitulo3 = xlwt.easyxf('font: name Times New Roman; align: wrap on, vert centre, horiz center')
        subtitulo.font.height = 20*10
        wb = xlwt.Workbook()


        categorias = CategoriaRubro.objects.filter(hasta__gte=convertir_fecha('2022-07-29')).order_by('-categoria')
        tit = TituloInstitucion.objects.all()[:1].get()

        for g in AsistAsuntoEstudiant.objects.filter(estado=True).order_by('fecha'):
            columna = 1
            ws = wb.add_sheet(g.asistente.usuario.username, cell_overwrite_ok=True)
            ws.write_merge(0, 0, 0, 6, tit.nombre , titulo2)
            ws.write_merge(1, 1, 0, 6, 'Listado de Alumnos por Categoria de Rubro',titulo2)
            for c in categorias:
                ws.write(3, 0, 'GESTOR',titulo)
                ws.write(3, columna, c.categoria,titulo)
                columna = columna + 1

            columna = 1
            ids = []

            for c in categorias:
                try:
                    fecha_actual = datetime.now()
                    antiguedad = fecha_actual.year - 5
                    desde = fecha_actual.replace(antiguedad)

                    rubro_vencimiento_desde = date.today() - timedelta(c.numdiasmaximo)
                    rubro_vencimiento_hasta = date.today() - timedelta(c.numdiasminimo)

                    rubros = Rubro.objects.filter(cancelado=False, fechavence__gte=rubro_vencimiento_desde, fechavence__lte=rubro_vencimiento_hasta, inscripcion__fecha__gte=desde).order_by('-inscripcion__fecha')
                    inscripciones = Inscripcion.objects.filter(id__in=rubros.values('inscripcion'), asistente=g).exclude(id__in=ids).order_by('-fecha')

                    fila = 4

                    for i in inscripciones:
                        ids.append(i.id)
                        if i.persona.cedula:
                            identificacion = i.persona.cedula
                        else:
                            identificacion = i.persona.pasaporte

                        ws.write(fila, 0, g.asistente.nombre_completo_inverso())
                        ws.write(fila, columna, identificacion)
                        fila = fila + 1

                    columna = columna + 1
                except Exception as ex:
                    print(ex)

        nombre ='cedulas_xcategoria'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
        wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
        return nombre
        # return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

    except Exception as ex:
        print(str(ex))
        return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")
