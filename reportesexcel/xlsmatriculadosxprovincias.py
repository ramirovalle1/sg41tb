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
from decorators import secure_module
from settings import MEDIA_ROOT
from sga.commonviews import addUserData
from sga.forms import XLSPeriodoForm
from sga.models import Periodo, convertir_fecha,TituloInstitucion,ReporteExcel,Canton,Provincia,Coordinacion,Matricula,total_matriculadosfil,total_matriculadosfilnullprovin,total_matriculadosfilprovinporcent
from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):

    try:
        if request.method=='POST':
            action = request.POST['action']
            if action :
                periodo= Periodo.objects.filter(pk=request.POST['periodo'])[:1].get()
                try:
                    m = 8
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10
                    style1 = xlwt.easyxf('',num_format_str='DD-MMM-YY')
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('Informacion',cell_overwrite_ok=True)
                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,m+2, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,m+2, 'MATRICULADOS POR PERIODO Y PROVINCIAS ', titulo2)
                    ws.write(3, 0,  'PERIODO: ' +periodo.nombre , subtitulo)
                    filaprov=6
                    ws.write(5, 0,  'PROVINCIAS', titulo)
                    ws.write(5, 1,  'FAAS', titulo)
                    ws.write(5, 2,  'FAECAC', titulo)
                    ws.write(5, 3,  'FATV', titulo)
                    coordinaciones = Coordinacion.objects.filter().exclude(id__in=[2,4]).order_by('id')
                    provincias = Provincia.objects.all().order_by('nombre')
                    tot_coordinacion=0
                    provincia=''
                    detalle=0
                    totalgeneral=0
                    tot_provcoordinacion1=0
                    tot_provcoordinacion2=0
                    tot_provcoordinacion3=0
                    tot_provinciacoord1=0
                    tot_provinciacoord2=0
                    tot_provinciacoord3=0

                    for provincia in provincias:
                        colcoord=1
                        ws.write(filaprov,0,elimina_tildes(provincia), titulo)
                        coord=0
                        for coordinacion in coordinaciones:
                            coord=coord+1
                            tot_coordinacion=0
                            tot_coordinacion1=0
                            tot_coordinacion2=0
                            tot_coordinacion3=0
                            #tot_provincia=Matricula.objects.filter(nivel__periodo=periodo,nivel__cerrado=False,inscripcion__persona__provincia=provincia,inscripcion__carrera__in=coordinacion.carrera.all()).count()
                            tot_provincia=Matricula.objects.filter(nivel__periodo=periodo,inscripcion__persona__provincia=provincia,inscripcion__carrera__in=coordinacion.carrera.all()).count()
                            ws.write(filaprov,colcoord,tot_provincia)
                            tot_coordinacion=tot_provincia
                            if coord==1:
                                tot_coordinacion=tot_coordinacion
                                tot_coordinacion1=tot_coordinacion
                            if coord==2:
                                tot_coordinacion2=tot_coordinacion
                            if coord==3:
                                tot_coordinacion3=tot_coordinacion
                            colcoord=colcoord+1
                            totalgeneral=totalgeneral+tot_coordinacion
                            tot_provcoordinacion1=tot_provcoordinacion1+tot_coordinacion1
                            tot_provcoordinacion2=tot_provcoordinacion2+tot_coordinacion2
                            tot_provcoordinacion3=tot_provcoordinacion3+tot_coordinacion3
                        filaprov=filaprov+1
                        tot_provinciacoord1+=tot_provinciacoord1
                        tot_provinciacoord2+=tot_provinciacoord2
                        tot_provinciacoord3+=tot_provinciacoord3

                    coord=0
                    colcoord=1
                    for coordinacion in coordinaciones:
                        coord=coord+1
                        tot_provincia=0
                        #tot_provincia=Matricula.objects.filter(nivel__periodo=periodo,nivel__cerrado=False,inscripcion__persona__provincia=None,inscripcion__carrera__in=coordinacion.carrera.all()).count()
                        tot_provincia=Matricula.objects.filter(nivel__periodo=periodo,inscripcion__persona__provincia=None,inscripcion__carrera__in=coordinacion.carrera.all()).count()
                        ws.write(filaprov,colcoord,tot_provincia)
                        tot_coordinacion=tot_provincia
                        if coord==1:
                            tot_coordinacion=tot_coordinacion
                            tot_coordinacion1=tot_coordinacion
                        if coord==2:
                            tot_coordinacion2=tot_coordinacion
                        if coord==3:
                            tot_coordinacion3=tot_coordinacion
                        colcoord=colcoord+1
                        totalgeneral=totalgeneral+tot_coordinacion
                    tot_provcoordinacion1=tot_provcoordinacion1+tot_coordinacion1
                    tot_provcoordinacion2=tot_provcoordinacion2+tot_coordinacion2
                    tot_provcoordinacion3=tot_provcoordinacion3+tot_coordinacion3

                    tot_provinciacoord1+=tot_provinciacoord1
                    tot_provinciacoord2+=tot_provinciacoord2
                    tot_provinciacoord3+=tot_provinciacoord3

                    filaprov=filaprov+1

                    col=1
                    ws.write(filaprov-1,0,"SIN PROVINCIA",titulo)
                    ws.write(filaprov,0,"TOTALES",titulo)
                    ws.write(filaprov,col,tot_provcoordinacion1,titulo)
                    ws.write(filaprov,col+1,tot_provcoordinacion2,titulo)
                    ws.write(filaprov,col+2,tot_provcoordinacion3,titulo)
                    ws.write(filaprov,col+3,totalgeneral,titulo)

                    detalle = detalle + filaprov+3
                    ws.write(detalle, 0, "Fecha Impresion", subtitulo)
                    ws.write(detalle, 1, str(datetime.now()), subtitulo)
                    detalle=detalle +1
                    ws.write(detalle, 0, "Usuario", subtitulo)
                    ws.write(detalle, 1, str(request.user), subtitulo)

                    nombre ='reporte'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    return HttpResponse(json.dumps({"result":str(ex)+str(provincia)}),content_type="application/json")
        else:
                data = {'title': 'Matriculados por Periodo y Provincias '}
                addUserData(request,data)
                if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                    reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                    data['reportes'] = reportes
                    data['generarform']=XLSPeriodoForm()
                    return render(request ,"reportesexcel/xlsmatriculadosxprovincias.html" ,  data)
                return HttpResponseRedirect("/reporteexcel")


    except Exception as e:
        print((e))
        return HttpResponseRedirect('/?info='+str(e))