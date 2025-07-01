from datetime import datetime
import json
import xlwt
import locale
import os
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from settings import MEDIA_ROOT,JR_USEROUTPUT_FOLDER,MEDIA_URL, SITE_ROOT
from sga.commonviews import addUserData
from sga.models import convertir_fecha,Factura,ClienteFactura,TituloInstitucion,ReporteExcel, Profesor, DatoInstrumentoEvaluacion, EvaluacionProfesor, Periodo, IndicadorEvaluacion, CalificacionEvaluacion
from sga.reportes import elimina_tildes
from fpdf import FPDF

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action =='generarexcel':
                periodo = Periodo.objects.get(id=request.POST['periodo'])
                m = 5
                titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                titulo.font.height = 20*11
                titulo2.font.height = 20*11
                subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                subtitulo.font.height = 20*10
                style1 = xlwt.easyxf('',num_format_str='DD-MMM-YY')
                wb = xlwt.Workbook()
                ws = wb.add_sheet('Evaluacion',cell_overwrite_ok=True)

                ws.write_merge(1, 1,0,m+2, 'CONSOLIDADO DE EVALUACION', titulo2)
                ws.write(3, 0, 'Periodo', titulo)
                ws.write(3, 1, str(periodo.nombre), titulo)

                ws.write(7, 0,  'INDICADOR', titulo)
                ws.write(7, 1,  'MAL', titulo)
                ws.write(7, 2,  'REGULAR', titulo)
                ws.write(7, 3,  'BIEN', titulo)
                ws.write(7, 4,  'MUY BIEN', titulo)
                ws.write(7, 5,  'EXCELENTE', titulo)
                ws.write(7, 6,  'TOTAL DOCENTE', titulo)
                cont =9
                tot1=0
                tot2=0
                tot3=0
                tot4=0
                tot5=0
                try:
                    if Profesor.objects.filter(persona__profesor__profesormateria__materia__nivel__periodo=periodo).exists():
                        proceso = periodo.proceso_evaluativo()
                        for ambito in proceso.instrumento_alumno().ambitoinstrumentoevaluacion_set.all():
                            cont =cont +1
                            ws.write(cont, 0, ambito.ambito.nombre)
                            for ind in ambito.indicadores():
                                profesor = Profesor.objects.filter(persona__profesor__profesormateria__materia__nivel__periodo=periodo).distinct('id').values('id')
                                for p in  Profesor.objects.filter(persona__profesor__profesormateria__materia__nivel__periodo=periodo)[:150]:
                                    numero1=0
                                    numero2=0
                                    numero3=0
                                    numero4=0
                                    numero5=0

                                #for dato in DatoInstrumentoEvaluacion.objects.filter(indicador__id=ind.id,evaluacion__in=EvaluacionProfesor.objects.filter(proceso=proceso, profesor__id__in=profesor, instrumento=proceso.instrumento_alumno()
                                    #for dato in DatoInstrumentoEvaluacion.objects.filter(valor = 1,indicador__id=ind.id,evaluacion__in=EvaluacionProfesor.objects.filter(proceso=proceso, profesor=p, instrumento=proceso.instrumento_alumno())):
                                    numero1 = DatoInstrumentoEvaluacion.objects.filter(valor = 1,indicador__id=ind.id,evaluacion__in=EvaluacionProfesor.objects.filter(proceso=proceso, profesor=p, instrumento=proceso.instrumento_alumno())).count()
                                    numero2 = DatoInstrumentoEvaluacion.objects.filter(valor =2,indicador__id=ind.id,evaluacion__in=EvaluacionProfesor.objects.filter(proceso=proceso, profesor=p, instrumento=proceso.instrumento_alumno())).count()
                                    numero3 = DatoInstrumentoEvaluacion.objects.filter(valor = 3,indicador__id=ind.id,evaluacion__in=EvaluacionProfesor.objects.filter(proceso=proceso, profesor=p, instrumento=proceso.instrumento_alumno())).count()
                                    numero4 = DatoInstrumentoEvaluacion.objects.filter(valor = 4,indicador__id=ind.id,evaluacion__in=EvaluacionProfesor.objects.filter(proceso=proceso, profesor=p, instrumento=proceso.instrumento_alumno())).count()
                                    numero5 = DatoInstrumentoEvaluacion.objects.filter(valor = 5,indicador__id=ind.id,evaluacion__in=EvaluacionProfesor.objects.filter(proceso=proceso, profesor=p, instrumento=proceso.instrumento_alumno())).count()
                                    if numero1 > numero2 and   numero1 > numero3 and  numero1 > numero4  and  numero1 > numero5:
                                        tot1 = tot1 +1
                                    if numero2 > numero1 and   numero2 > numero3 and  numero2 > numero4  and  numero2 > numero5:
                                        tot2 = tot2 +1
                                    if numero3 > numero1 and   numero3 > numero2 and  numero3 > numero4  and  numero3 > numero5:
                                        tot3 = tot3 +1
                                    if numero4 > numero1 and   numero4 > numero2 and  numero4 > numero3  and  numero4 > numero5:
                                        tot4 = tot4 +1
                                    if numero5 > numero1 and   numero5 > numero2 and  numero5 > numero3  and  numero5 > numero4:
                                        tot5 = tot5 +1
                                cont =cont +1
                                ws.write(cont, 0, ind.indicador.nombre)
                                ws.write(cont,1, tot1)
                                ws.write(cont,2 ,tot2)
                                ws.write(cont,3, tot3)
                                ws.write(cont,4 ,tot4)
                                ws.write(cont,5 ,tot5)
                                ws.write(cont,6 ,tot1+tot2+tot3+tot4+tot5)
                                tot1=0
                                tot2=0
                                tot3=0
                                tot4=0
                                tot5=0
                    nombre ='evaluaciondocente'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")
                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")


            elif action  =='generarpdf':
                try:
                    pdf = FPDF()
                    pdf.add_page('Landscape')
                    pdf.set_font('Arial', 'B', 5)  # Arial bold 8
                    pdf.alias_nb_pages(alias='pag_total')
                    pdf.image(SITE_ROOT+'/media/reportes/encabezados_pies/logo.png', 5, 5, 20,20)  # Logo

                    periodo = Periodo.objects.get(id=request.POST['periodo'])
                    pdf.ln(30)  # Salto de linea
                    pdf.text(120,30,"CONSOLIDADO DE EVALUACION" )
                    pdf.text(1,35,"PERIODO: "  + str(periodo.nombre))
                    fechahoy=datetime.now()
                    fechahoy = fechahoy.strftime('%d/%m/%Y %H:%M:%S%p') # formato dd/mm/yyyy hh:mm:ss am o fm
                    pdf.text(1,50,"Fecha de Impresion: "+ str(fechahoy))
                    pdf.ln(20)  # Salto de linea

                    # para pruebas en desarrollo OCU
                    # locale.setlocale( locale.LC_ALL, '' )

                    # para produccion
                    locale.setlocale( locale.LC_ALL, 'en_US.UTF-8' )

                    # cabecera de la tabla
                    cabecera = ["INDICADOR","MAL","REGULAR","BIEN","MUY BIEN","EXCELENTE","TOTAL DOCENTE"]
                    w = [150,20,20,20,20,20,20]
                    for i in range(0, len(cabecera)):
                        pdf.cell(w[i], 5, cabecera[i], 1, 0, 'C', 0)
                    pdf.ln()

                    tot1=0
                    tot2=0
                    tot3=0
                    tot4=0
                    tot5=0
                    total=0

                    if Profesor.objects.filter(persona__profesor__profesormateria__materia__nivel__periodo=periodo).exists():
                        proceso = periodo.proceso_evaluativo()
                        for ambito in proceso.instrumento_alumno().ambitoinstrumentoevaluacion_set.all():
                            pdf.cell(270, 5, str(elimina_tildes(ambito.ambito.nombre)), 'LR',0,'L')
                            pdf.ln()
                            for ind in ambito.indicadores():
                                profesor = Profesor.objects.filter(persona__profesor__profesormateria__materia__nivel__periodo=periodo).distinct('id').values('id')
                                for p in  Profesor.objects.filter(persona__profesor__profesormateria__materia__nivel__periodo=periodo)[:150]:
                                    numero1=0
                                    numero2=0
                                    numero3=0
                                    numero4=0
                                    numero5=0

                                    numero1 = DatoInstrumentoEvaluacion.objects.filter(valor = 1,indicador__id=ind.id,evaluacion__in=EvaluacionProfesor.objects.filter(proceso=proceso, profesor=p, instrumento=proceso.instrumento_alumno())).count()
                                    numero2 = DatoInstrumentoEvaluacion.objects.filter(valor =2,indicador__id=ind.id,evaluacion__in=EvaluacionProfesor.objects.filter(proceso=proceso, profesor=p, instrumento=proceso.instrumento_alumno())).count()
                                    numero3 = DatoInstrumentoEvaluacion.objects.filter(valor = 3,indicador__id=ind.id,evaluacion__in=EvaluacionProfesor.objects.filter(proceso=proceso, profesor=p, instrumento=proceso.instrumento_alumno())).count()
                                    numero4 = DatoInstrumentoEvaluacion.objects.filter(valor = 4,indicador__id=ind.id,evaluacion__in=EvaluacionProfesor.objects.filter(proceso=proceso, profesor=p, instrumento=proceso.instrumento_alumno())).count()
                                    numero5 = DatoInstrumentoEvaluacion.objects.filter(valor = 5,indicador__id=ind.id,evaluacion__in=EvaluacionProfesor.objects.filter(proceso=proceso, profesor=p, instrumento=proceso.instrumento_alumno())).count()
                                    if numero1 > numero2 and   numero1 > numero3 and  numero1 > numero4  and  numero1 > numero5:
                                        tot1 = tot1 +1
                                    if numero2 > numero1 and   numero2 > numero3 and  numero2 > numero4  and  numero2 > numero5:
                                        tot2 = tot2 +1
                                    if numero3 > numero1 and   numero3 > numero2 and  numero3 > numero4  and  numero3 > numero5:
                                        tot3 = tot3 +1
                                    if numero4 > numero1 and   numero4 > numero2 and  numero4 > numero3  and  numero4 > numero5:
                                        tot4 = tot4 +1
                                    if numero5 > numero1 and   numero5 > numero2 and  numero5 > numero3  and  numero5 > numero4:
                                        tot5 = tot5 +1

                                pdf.cell(150, 5, str(elimina_tildes(ind.indicador.nombre)), 'LR',0)
                                pdf.cell(20, 5, str(tot1), 'LR',0,'C')
                                pdf.cell(20, 5, str(tot2), 'LR',0,'C')
                                pdf.cell(20, 5, str(tot3), 'LR',0,'C')
                                pdf.cell(20, 5, str(tot4), 'LR',0,'C')
                                pdf.cell(20, 5, str(tot5), 'LR',0,'C')
                                total = tot1+tot2+tot3+tot4+tot5
                                pdf.cell(20, 5, str(total),'LR',0,'C')

                                tot1=0
                                tot2=0
                                tot3=0
                                tot4=0
                                tot5=0
                                total=0
                                pdf.ln()

                    pdf.ln(10)
                    pdf.set_font('Arial','B',12)  # Arial bold 12
                    pdf.set_font('')  # restauro la fuente
                    d = datetime.now()
                    pdfname = 'eval_alumdoce_resumen' + '_' + d.strftime('%Y%m%d_%H%M%S') + '.pdf'
                    output_folder = os.path.join(JR_USEROUTPUT_FOLDER, elimina_tildes(request.user.username))
                    try:
                        os.makedirs(output_folder)
                    except Exception as ex:
                        pass
                    pdf.output(os.path.join(output_folder, pdfname))
                    return HttpResponse(json.dumps({'result': 'ok','reportfile': '/'.join([MEDIA_URL,'documentos',
                                                                                           'userreports',
                                                                                           request.user.username,
                                                                                           pdfname])}),content_type="application/json")
                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")

        else:
            data = {'title': 'Consulta de Evaluacion'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                return render(request ,"reportesexcel/eval_alumdoce_resumen.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))


















