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
from socioecon.models import InscripcionFichaSocioeconomica
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
                    ws.write_merge(1, 1,0,m, 'TOTALES SEGUN FICHA SOCIOECONOMICA DE ESTUDIANTES POR PERIODO '+str(periodo),titulo2)
                    fila =4
                    detalle =5
                    columna=1
                    tot_coninternet=0
                    tot_celulares=0
                    tot_sininternet=0
                    tot_discapacidad=0
                    tot_adultosmayores=0
                    tot_menoredad=0
                    tot_madresoltera=0
                    carrera=''

                    ws.write(3,0,"CARRERA",titulo)
                    ws.write(3,1,"CON ACCESO A INTERNET",titulo)
                    ws.write(3,2,"SIN ACCESO A INTERNET",titulo)
                    ws.write(3,3,"CON DISCAPACIDAD",titulo)
                    ws.write(3,4,"ADULTOS MAYORES",titulo)
                    ws.write(3,5,"MENORES DE EDAD",titulo)
                    ws.write(3,6,"MADRES SOLTERAS",titulo)
                    ws.write(3,7,"TIENE CELULAR",titulo)

                    for carrera in Carrera.objects.filter(activo=True,carrera=True):
                        totcarrera_coninternet=0
                        totcarrera_sininternet=0
                        totcarrera_discapacidad=0
                        totcarrera_adultosmayores=0
                        totcarrera_menoredad=0
                        totcarrera_madresoltera=0
                        tot_celulares_carrera=0
                        ws.write(fila,columna-1,elimina_tildes(carrera), titulo)

                        for matri in Matricula.objects.filter(nivel__periodo=periodo,nivel__cerrado=False,inscripcion__carrera=carrera).order_by('inscripcion__carrera__nombre'):
                            for ficha in InscripcionFichaSocioeconomica.objects.filter(inscripcion=matri.inscripcion):
                                if ficha.tieneinternet:
                                    tot_coninternet+=1
                                    totcarrera_coninternet+=1
                                else:
                                    tot_sininternet+=1
                                    totcarrera_sininternet+=1

                                if ficha.p_msoltera:
                                    tot_madresoltera+=1
                                    totcarrera_madresoltera+=1

                                if ficha.cantcelulares:
                                    tot_celulares +=1
                                    tot_celulares_carrera +=1


                            if matri.inscripcion.tienediscapacidad:
                                tot_discapacidad+=1
                                totcarrera_discapacidad+=1

                            if matri.inscripcion.persona.edad_actual()>=65:
                                tot_adultosmayores+=1
                                totcarrera_adultosmayores+=1

                            if matri.inscripcion.persona.edad_actual()<18:
                                tot_menoredad+=1
                                totcarrera_menoredad+=1

                        ws.write(fila,columna,totcarrera_coninternet, subtitulo)
                        ws.write(fila,columna+1,totcarrera_sininternet, subtitulo)
                        ws.write(fila,columna+2,totcarrera_discapacidad, subtitulo)
                        ws.write(fila,columna+3,totcarrera_adultosmayores, subtitulo)
                        ws.write(fila,columna+4,totcarrera_menoredad, subtitulo)
                        ws.write(fila,columna+5,totcarrera_madresoltera, subtitulo)
                        ws.write(fila,columna+6,tot_celulares_carrera, subtitulo)
                        fila=fila+1

                    ws.write(fila,columna,tot_coninternet, subtitulo)
                    ws.write(fila,columna+1,tot_sininternet, subtitulo)
                    ws.write(fila,columna+2,tot_discapacidad, subtitulo)
                    ws.write(fila,columna+3,tot_adultosmayores, subtitulo)
                    ws.write(fila,columna+4,tot_menoredad, subtitulo)
                    ws.write(fila,columna+5,tot_madresoltera, subtitulo)
                    ws.write(fila,columna+6,tot_celulares, subtitulo)

                    fila = fila +1


                    matriculasinficha = Matricula.objects.filter(nivel__cerrado=False,inscripcion__inscripcionfichasocioeconomica__inscripcion=None,nivel__periodo=periodo).count()

                    ws.write(fila+2,0,'ESTUDIANTES QUE NO HAN LLENADO FICHA', subtitulo)
                    ws.write(fila+2,1,matriculasinficha, subtitulo)

                    columna=0
                    detalle = detalle + fila
                    ws.write(detalle,0, "Fecha Impresion", subtitulo)
                    ws.write(detalle,1, str(datetime.now()), subtitulo)
                    detalle=detalle+2
                    ws.write(detalle,0, "Usuario", subtitulo)
                    ws.write(detalle,1, str(request.user), subtitulo)

                    nombre ='indicadores_fichasocioecon'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(carrera)}),content_type="application/json")

        else:
            data = {'title': 'Totales Indicadores Ficha Socioeconomica por Periodo'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform']=XLSPeriodoForm()
                return render(request ,"reportesexcel/indicadores_fichasocioecon.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))


















