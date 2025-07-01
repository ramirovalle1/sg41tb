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
from sga.forms import RangoFacturasForm,RangoNCForm, VinculacionExcelForm, MatriculadosExcelForm
from sga.models import Inscripcion,convertir_fecha,Factura,ClienteFactura,TituloInstitucion,ReporteExcel,NotaCreditoInstitucion, Persona,TipoNotaCredito, Carrera, Matricula, RecordAcademico, NivelMalla
from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action :

                try:
                    carrera= Carrera.objects.filter(pk=request.POST['carrera'])[:1].get()
                    nivelmalla= NivelMalla.objects.filter(pk=request.POST['nivelmalla'])[:1].get()
                    matriculas = Matricula.objects.filter(nivel__carrera=carrera,nivel__nivelmalla=nivelmalla,nivel__cerrado=False).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2')
                    m = 5
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('Registros',cell_overwrite_ok=True)

                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,m+2, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,m+2, 'LISTADO DE MATRICULADOS ', titulo2)
                    ws.write(2, 0, 'CARRERA:', titulo)
                    ws.write(2, 1, carrera.nombre, titulo)
                    ws.write(3, 0, 'NIVEL:', titulo)
                    ws.write(3, 1, nivelmalla.nombre, titulo)
                    ws.write(4, 0,  '#', titulo)
                    ws.write(4, 2,  'CEDULA', titulo)
                    ws.write(4, 1,  'NOMBRES', titulo)
                    ws.write(4, 3,  'PARALELO', titulo)
                    ws.write(4, 4,  'TIPO DE TITULACION', titulo)
                    fila = 4
                    detalle = 3
                    c=0
                    for m in matriculas:
                        fila = fila +1
                        columna=0
                        c=c+1

                        ws.write(fila,columna ,c)
                        ws.write(fila,columna+2 , str(m.inscripcion.persona.cedula))
                        ws.write(fila,columna+1, m.inscripcion.persona.nombre_completo_inverso())
                        ws.write(fila,columna+3, str(m.nivel.paralelo))
                        ws.write(fila,columna+4, str(m.inscripcion.grupo().modalidad))
                    detalle = detalle + fila
                    ws.write(detalle, 0, "Fecha Impresion", subtitulo)
                    ws.write(detalle, 2, str(datetime.now()), subtitulo)
                    detalle=detalle +1
                    ws.write(detalle, 0, "Usuario", subtitulo)
                    ws.write(detalle, 2, str(request.user), subtitulo)

                    nombre ='matriculados_nivel'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")

        else:
            data = {'title': 'Estudiantes Matriculados por Nivel'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform']=MatriculadosExcelForm()
                return render(request ,"reportesexcel/proceso_titulacion.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

