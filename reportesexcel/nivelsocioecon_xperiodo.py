from datetime import datetime
import json
import xlwt
import os
import locale
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from settings import MEDIA_ROOT,UTILIZA_FACTURACION_CON_FPDF,JR_USEROUTPUT_FOLDER,MEDIA_URL, SITE_ROOT
from sga.commonviews import addUserData
from sga.forms import XLSPeriodoForm
from sga.models import convertir_fecha,TituloInstitucion,ReporteExcel,Periodo,Matricula,Carrera
from socioecon.models import InscripcionFichaSocioeconomica,GrupoSocioEconomico
from sga.reportes import elimina_tildes
from fpdf import FPDF

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action  =='generarexcel':
                try:
                    periodo = Periodo.objects.filter(pk=request.POST['periodo'])[:1].get()
                    m = 11

                    #matriculados= Matricula.objects.filter(nivel__periodo=periodo).order_by('inscripcion__carrera__nombre')
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black')
                    subtitulo3 = xlwt.easyxf('font: name Times New Roman; align: wrap on, vert centre, horiz center')
                    subtitulo.font.height = 20*10
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('Registros',cell_overwrite_ok=True)

                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,m, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,m, 'RESUMEN GRUPOS SOCIOECONOMICOS DE ESTUDIANTES POR PERIODO '+str(periodo),titulo2)
                    fila =4
                    detalle =5

                    tot_coninternet=0
                    tot_sininternet=0
                    tot_discapacidad=0
                    tot_adultosmayores=0
                    tot_menoredad=0
                    tot_madresoltera=0
                    carrera=''

                    ws.write(3,0,"CARRERA",titulo)
                    ws.write(3,1,"GRUPO A",titulo)
                    ws.write(3,2,"GRUPO B",titulo)
                    ws.write(3,3,"GRUPO C+",titulo)
                    ws.write(3,4,"GRUPO C-",titulo)
                    ws.write(3,5,"GRUPO D",titulo)

                    totalgrupo1=0
                    totalgrupo2=0
                    totalgrupo3=0
                    totalgrupo4=0
                    totalgrupo5=0

                    for carrera in Carrera.objects.filter(activo=True,carrera=True):
                        totcarrera_grupo1=0
                        totcarrera_grupo2=0
                        totcarrera_grupo3=0
                        totcarrera_grupo4=0
                        totcarrera_grupo5=0
                        columna=1
                        ws.write(fila,columna-1,elimina_tildes(carrera), titulo)

                        for grupo in GrupoSocioEconomico.objects.all():
                            tot_carreraxgrupo=0
                            tot_carreraxgrupo=Matricula.objects.filter(nivel__periodo=periodo,nivel__cerrado=False,inscripcion__inscripcionfichasocioeconomica__grupoeconomico=grupo,nivel__carrera=carrera).count()

                            if grupo.codigo=='A':
                                totalgrupo1+=tot_carreraxgrupo
                                totcarrera_grupo1=totcarrera_grupo1+totalgrupo1
                            if grupo.codigo=='B':
                                totalgrupo2+=tot_carreraxgrupo
                                totcarrera_grupo2=totcarrera_grupo2+totalgrupo2
                            if grupo.codigo=='C+':
                                totalgrupo3+=tot_carreraxgrupo
                                totcarrera_grupo3=totcarrera_grupo3+totalgrupo3
                            if grupo.codigo=='C-':
                                totalgrupo4+=tot_carreraxgrupo
                                totcarrera_grupo4=totcarrera_grupo4+totalgrupo4
                            if grupo.codigo=='D':
                                totalgrupo5+=tot_carreraxgrupo
                                totcarrera_grupo5=totcarrera_grupo5+totalgrupo5

                            ws.write(fila,columna,tot_carreraxgrupo, subtitulo)
                            columna=columna+1

                        fila=fila+1

                    columna=1
                    ws.write(fila,columna-1,'TOTALES', titulo)
                    ws.write(fila,columna,totalgrupo1, titulo)
                    ws.write(fila,columna+1,totalgrupo2, titulo)
                    ws.write(fila,columna+2,totalgrupo3, titulo)
                    ws.write(fila,columna+3,totalgrupo4, titulo)
                    ws.write(fila,columna+4,totalgrupo5, titulo)

                    columna=0
                    detalle = detalle + fila
                    ws.write(detalle,0, "Fecha Impresion", subtitulo)
                    ws.write(detalle,1, str(datetime.now()), subtitulo)
                    detalle=detalle+2
                    ws.write(detalle,0, "Usuario", subtitulo)
                    ws.write(detalle,1, str(request.user), subtitulo)

                    nombre ='nivelsocioecon_xperiodo'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(carrera)}),content_type="application/json")

        else:
            data = {'title': 'Totales Grupos Socioeconomicos por Periodo'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform']=XLSPeriodoForm()
                return render(request ,"reportesexcel/nivelsocioecon_xperiodo.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))


















