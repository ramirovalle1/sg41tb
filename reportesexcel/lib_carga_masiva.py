from datetime import datetime,timedelta,date
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
from bib.models import Documento
from decorators import secure_module
from settings import MEDIA_ROOT
from sga.commonviews import addUserData
from sga.forms import XLSPeriodoForm
from sga.models import Periodo, convertir_fecha,TituloInstitucion,ReporteExcel,Canton,Provincia,Coordinacion,Matricula,total_matriculadosfil,total_matriculadosfilnullprovin,total_matriculadosfilprovinporcent, MateriaAsignada, SesionJornada
from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):

    try:
        if request.method=='POST':
            action = request.POST['action']
            if action :
                try:
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10
                    style1 = xlwt.easyxf('',num_format_str='DD-MMM-YY')
                    wb = xlwt.Workbook()

                    # ezxf = easyxf
                    center = xlwt.easyxf('align: horiz center')
                    # writer = XLSWriter()

                    # data = ["Negrilla", "Centrada", u"Centrada y con corte de linea"]
                    # format = [ezxf('font: bold on'), ezxf('align: horiz center'), ezxf('align: wrap on, horiz center')]
                    # writer.append(data, format)

                    ws = wb.add_sheet('LIB01_carga_masiva_libros',cell_overwrite_ok=True)
                    # sheet_name.write_merge(fila_inicial, fila_final, columna_inicial, columna_final,).
                    ws.write_merge(0, 0, 0, 30,)
                    ws.write_merge(1, 1, 0, 30,)
                    ws.write (0, 0, 'INSTITUTO TECNOLOGICO BOLIVARIANO',center )
                    ws.write(1, 0, 'MATRIZ LIB01_carga_masiva_libros' )
                    ws.write(2, 0, 'CODIGO', titulo)
                    ws.write(2, 1, 'TIPO', titulo)
                    ws.write(2, 2, 'TITULO', titulo)
                    ws.write(2, 3, 'NOMBRE BIBLIOTECA', titulo)
                    ws.write(2, 4, 'TIPO MEDIO SOPORTE', titulo)
                    ws.write(2, 5, 'NUMERO EJEMPLARES', titulo)
                    ws.write(2, 6, 'CODIGO UBICACION FISICA', titulo)
                    cont=3
                    for d in Documento.objects.filter(anno__gte=2015).exclude(tipo__id=3):
                       try:
                           tipo = elimina_tildes(d.tipo)
                       except:
                           tipo='ERROR EN EL TIPO'

                       ws.write(cont, 0, d.codigo)
                       ws.write(cont, 1, tipo, titulo)
                       ws.write(cont, 2,d.nombre)
                       ws.write(cont, 3, elimina_tildes(d.sede))
                       ws.write(cont, 4, tipo)
                       ws.write(cont, 5, d.copias)
                       ws.write(cont, 6, elimina_tildes(d.sede))
                       cont = cont + 1
                    nombre ='reporte'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")
        else:
                data = {'title': 'Matriz LIB01 '}
                addUserData(request,data)
                # if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                #     reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                #     data['reportes'] = reportes
                # data['generarform']=XLSPeriodoForm()
                return render(request ,"reportesexcel/lib_carga_masiva.html" ,  data)
                # return HttpResponseRedirect("/reporteexcel")


    except Exception as e:
        print((e))
        return HttpResponseRedirect('/?info='+str(e))