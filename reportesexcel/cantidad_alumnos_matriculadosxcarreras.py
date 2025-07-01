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
from sga.models import Periodo, convertir_fecha,TituloInstitucion,ReporteExcel,Matricula,Modalidad
from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):

    try:
        if request.method=='POST':
            action = request.POST['action']
            if action :
                periodo= Periodo.objects.filter(pk=request.POST['periodo'])[:1].get()
                inscripcion= ''
                try:
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10
                    style1 = xlwt.easyxf('',num_format_str='DD-MMM-YY')
                    wb = xlwt.Workbook()

                    center = xlwt.easyxf('align: horiz center')
                    ws = wb.add_sheet('condensado_matriculadosxcarrera',cell_overwrite_ok=True)

                    ws.write_merge(0, 0, 0, 14,)
                    ws.write_merge(1, 1, 0, 14,)
                    ws.write (0, 0, 'INSTITUTO TECNOLOGICO BOLIVARIANO',center )
                    ws.write(1, 0, 'CONDENSADO DE ALUMNOS MATRICULADOS POR CARRERA - ' + elimina_tildes(periodo.periodo_repr()),center)
                    ws.write(3, 0, 'CODIGO IST', titulo)
                    ws.write(3, 1, 'NOMBRE IST', titulo)
                    ws.write(3, 2, 'CODIGO CARRERA', titulo)
                    ws.write(3, 3, 'NOMBRE CARRERA', titulo)
                    ws.write(3, 4, 'MODALIDAD', titulo)
                    ws.write(3, 5, 'P1', titulo)
                    ws.write(3, 6, 'P2', titulo)
                    ws.write(3, 7, 'P3', titulo)
                    ws.write(3, 8, 'P4', titulo)
                    ws.write(3, 9, 'P5', titulo)
                    ws.write(3, 10, 'P6', titulo)
                    ws.write(3, 11, 'MASCULINO', titulo)
                    ws.write(3, 12, 'FEMENINO', titulo)
                    ws.write(3, 13, 'TOTAL', titulo)
                    ws.write(3, 14, 'DURACION SEMESTRES', titulo)

                    cont = 4
                    detalle = 3
                    #for carrera in Matricula.objects.filter(nivel__periodo=periodo,nivel__nivelmalla__in=(1,2,3,4,5,6),nivel__carrera__carrera=True,nivel__carrera__id=31).order_by('nivel__carrera__alias').distinct('nivel__carrera').values('nivel__carrera'):
                    for carrera in Matricula.objects.filter(nivel__periodo=periodo,nivel__nivelmalla__in=(1,2,3,4,5,6),nivel__carrera__carrera=True).order_by('nivel__carrera__alias').distinct().values('nivel__carrera'):
                        #print(carrera)
                        for modalidad in Matricula.objects.filter(nivel__periodo=periodo,nivel__carrera__id=carrera['nivel__carrera'],nivel__nivelmalla__in=(1,2,3,4,5,6),nivel__carrera__carrera=True).order_by('nivel__grupo__modalidad').distinct().values('nivel__grupo__modalidad'):
                            print(modalidad)
                            nivel1=0
                            nivel2=0
                            nivel3=0
                            nivel4=0
                            nivel5=0
                            nivel6=0
                            hombres=0
                            mujeres=0
                            total=0
                            nombrecarrera=''
                            for matricula in Matricula.objects.filter(nivel__periodo=periodo,nivel__carrera__id=carrera['nivel__carrera'],nivel__nivelmalla__in=(1,2,3,4,5,6),nivel__carrera__carrera=True,nivel__grupo__modalidad__id=modalidad['nivel__grupo__modalidad']).order_by('nivel__nivelmalla__orden'):
                                #print(matricula.inscripcion)
                                nombrecarrera=elimina_tildes(matricula.inscripcion.carrera)
                                if matricula.nivel.nivelmalla.orden==2:
                                    nivel1+=1
                                if matricula.nivel.nivelmalla.orden==3:
                                    nivel2+=1
                                if matricula.nivel.nivelmalla.orden==4:
                                    nivel3+=1
                                if matricula.nivel.nivelmalla.orden==5:
                                    nivel4+=1
                                if matricula.nivel.nivelmalla.orden==6:
                                    nivel5+=1
                                if matricula.nivel.nivelmalla.orden==7:
                                    nivel6+=1

                                if matricula.inscripcion.persona.sexo.id==2:
                                    hombres+=1
                                else:
                                    mujeres+=1
                            nombremodalidad=Modalidad.objects.filter(pk=modalidad['nivel__grupo__modalidad'])[:1].get()
                            total=nivel1+nivel2+nivel3+nivel4+nivel5+nivel6
                            ws.write(cont, 0, '2397')
                            ws.write(cont, 1, elimina_tildes('INSTITUTO SUPERIOR TECNOLOGICO BOLIVARIANO DE TECNOLOGIA') )
                            ws.write(cont, 2, '')
                            ws.write(cont, 3, str(nombrecarrera))
                            ws.write(cont, 4, str(nombremodalidad.nombre))
                            ws.write(cont, 5, nivel1)
                            ws.write(cont, 6, nivel2)
                            ws.write(cont, 7, nivel3)
                            ws.write(cont, 8, nivel4)
                            ws.write(cont, 9, nivel5)
                            ws.write(cont, 10, nivel6)
                            ws.write(cont, 11, hombres)
                            ws.write(cont, 12, mujeres)
                            ws.write(cont, 13, total)
                            cont=cont+1

                    detalle = detalle + cont
                    ws.write(detalle,0, "Fecha Impresion", subtitulo)
                    ws.write(detalle,1, str(datetime.now()), subtitulo)
                    detalle=detalle+2
                    ws.write(detalle,0, "Usuario", subtitulo)
                    ws.write(detalle,1, str(request.user), subtitulo)

                    nombre ='reporte'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    return HttpResponse(json.dumps({"result":str(ex)+str(inscripcion)}),content_type="application/json")
        else:
                data = {'title': 'Condensado de Matriculados por Periodo '}
                addUserData(request,data)
                if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                    reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                    data['reportes'] = reportes
                data['generarform']=XLSPeriodoForm()
                return render(request ,"reportesexcel/cantidad_alumnos_matriculadosxcarreras.html" ,  data)

    except Exception as e:
        print((e))
        return HttpResponseRedirect('/?info='+str(e))