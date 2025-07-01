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
from sga.models import convertir_fecha,TituloInstitucion,ReporteExcel,Periodo,Matricula,Carrera, Descuento, DetalleDescuento
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
                    ws.write_merge(1, 1,0,m, 'ALUMNOS CON PROMOCION '+str(periodo),titulo2)
                    fila =4
                    detalle = 3
                    columna=1
                    tot_coninternet=0
                    tot_sininternet=0
                    tot_discapacidad=0
                    tot_adultosmayores=0
                    tot_menoredad=0
                    tot_madresoltera=0
                    carrera=''

                    ws.write(3,0,"ETUDIANTE",titulo)
                    ws.write(3,1,"RUBRO",titulo)
                    ws.write(3,2,"VALOR",titulo)

                    columna=0
                    for det in Descuento.objects.filter(inscripcion__matricula__nivel__periodo=periodo,inscripcion__matricula__nivel__cerrado=False).distinct('motivo').values('motivo'):
                        fila=fila +1
                        ws.write(fila,columna,elimina_tildes(str(det['motivo'])), subtitulo)
                        for matri in Descuento.objects.filter(inscripcion__matricula__nivel__periodo=periodo,inscripcion__matricula__nivel__cerrado=False,motivo=str(det['motivo'])).order_by('motivo','inscripcion__carrera__nombre'):
                            for d in DetalleDescuento.objects.filter(descuento=matri):
                                ws.write(fila,columna,str(d.descuento.inscripcion), subtitulo)
                                ws.write(fila,columna+1,str(d.rubro), subtitulo)
                                ws.write(fila,columna+2,d.valor, subtitulo)
                                fila=fila+1


                    columna=0

                    fila = fila +2
                    ws.write(fila,columna,'TOTALES', subtitulo)
                    fila = fila +1
                    for det in Descuento.objects.filter(inscripcion__matricula__nivel__periodo=periodo,inscripcion__matricula__nivel__cerrado=False).distinct('motivo').values('motivo'):
                        tot = Descuento.objects.filter(inscripcion__matricula__nivel__periodo=periodo,inscripcion__matricula__nivel__cerrado=False,motivo=str(det['motivo'])).distinct('inscripcion').values('inscripcion').count()
                        ws.write(fila,columna,str(det['motivo']), subtitulo)
                        ws.write(fila,columna+1,tot, subtitulo)

                    detalle = detalle + fila
                    ws.write(detalle,0, "Fecha Impresion", subtitulo)
                    ws.write(detalle,1, str(datetime.now()), subtitulo)
                    detalle=detalle+2
                    ws.write(detalle,0, "Usuario", subtitulo)
                    ws.write(detalle,1, str(request.user), subtitulo)

                    nombre ='estudiantespromo'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str('bad')}),content_type="application/json")

        else:
            data = {'title': 'Totales Indicadores Ficha Socioeconomica por Periodo'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform']=XLSPeriodoForm()
                return render(request ,"reportesexcel/estudiantespromo.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))


















