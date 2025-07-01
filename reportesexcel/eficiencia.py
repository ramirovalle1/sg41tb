from datetime import datetime,timedelta
import json
import xlrd
import xlwt
import locale
import os
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
from settings import UTILIZA_GRUPOS_ALUMNOS, EMAIL_ACTIVE,MEDIA_ROOT, ASIG_VINCULACION, ASIG_PRATICA,UTILIZA_FACTURACION_CON_FPDF,JR_USEROUTPUT_FOLDER,MEDIA_URL, SITE_ROOT
from sga.commonviews import addUserData, ip_client_address
from sga.forms import RangoFacturasForm,RangoNCForm, VinculacionExcelForm, MatriculadosExcelForm, EficienciaExcelForm
from sga.models import Inscripcion,convertir_fecha,Factura,ClienteFactura,TituloInstitucion,ReporteExcel,NotaCreditoInstitucion, Persona,TipoNotaCredito, Carrera, Matricula, RecordAcademico, NivelMalla, Graduado
from sga.reportes import elimina_tildes
from fpdf import FPDF

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action  =='generarexcel':
                try:
                    carrera= Carrera.objects.filter(pk=request.POST['carrera'])[:1].get()
                    nivelmalla= NivelMalla.objects.filter(pk=10)[:1].get()
                    inicio = request.POST['inicio']
                    fin = request.POST['fin']
                    fechai = convertir_fecha(inicio)
                    fechaf = convertir_fecha(fin)
                    matriculas = Matricula.objects.filter(nivel__carrera=carrera,nivel__nivelmalla=nivelmalla,fecha__gte=fechai,fecha__lte=fechaf).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2')
                    m = 5
                    ef=0
                    mat=0
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
                    ws.write_merge(1, 1,0,m+2, 'EFICIENCIA GRADUADOS ', titulo2)
                    ws.write(2, 0, 'CARRERA:', titulo)
                    ws.write(2, 1, carrera.nombre, titulo)
                    ws.write(3, 0, 'DESDE', titulo)
                    ws.write(3, 1, str((fechai.date())), titulo)
                    ws.write(4, 0, 'HASTA:', titulo)
                    ws.write(4, 1, str((fechaf.date())), titulo)
                    ws.write(6, 0,  'CEDULA', titulo)
                    ws.write(6, 1,  'NOMBRES', titulo)
                    ws.write(6, 2,  'GRADUADO', titulo)
                    ws.write(6, 3,  'NOTA SEMINARIO', titulo)
                    fila = 6
                    detalle = 3
                    c=0
                    eficiencia=0
                    for m in matriculas:
                        record=0
                        fila = fila +1
                        columna=0
                        mat=mat +1
                        c=c+1
                        ws.write(fila,columna , str(m.inscripcion.persona.cedula))
                        ws.write(fila,columna+1, m.inscripcion.persona.nombre_completo_inverso())
                        if RecordAcademico.objects.filter(asignatura__id=521,inscripcion=m.inscripcion).exists():
                            record =RecordAcademico.objects.filter(asignatura__id=521,inscripcion=m.inscripcion)[:1].get().nota
                        if Graduado.objects.filter(inscripcion=m.inscripcion).exists():
                            graduado = 'SI'
                            ef=ef+1
                        else:
                            graduado = 'NO'
                        ws.write(fila,columna+2 ,graduado)
                        ws.write(fila,columna+3 ,record)
                    if mat >0:
                        eficiencia =( ef*100)/mat
                    detalle = detalle + fila
                    ws.write(detalle+1, 0, "Eficiencia", subtitulo)
                    ws.write(detalle+1, 1, eficiencia, subtitulo)
                    ws.write(detalle+3, 0, "Fecha Impresion", subtitulo)
                    ws.write(detalle+3, 1, str(datetime.now()), subtitulo)
                    ws.write(detalle+4, 0, "Usuario", subtitulo)
                    ws.write(detalle+4, 1, str(request.user), subtitulo)

                    nombre ='eficiencia_graduados'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")
                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")

            elif action  =='generarpdf':
                try:
                    pdf = FPDF()
                    pdf.add_page('Landscape')
                    pdf.set_font('Arial', 'B', 8)  # Arial bold 8
                    pdf.alias_nb_pages(alias='pag_total')
                    pdf.image(SITE_ROOT+'/media/reportes/encabezados_pies/logo.png', 5, 5, 20,20)  # Logo
                    carrera= Carrera.objects.filter(pk=request.POST['carrera'])[:1].get()
                    nivelmalla= NivelMalla.objects.filter(pk=10)[:1].get()
                    inicio = request.POST['inicio']
                    fin = request.POST['fin']
                    fechai = convertir_fecha(inicio)
                    fechaf = convertir_fecha(fin)
                    matriculas = Matricula.objects.filter(nivel__carrera=carrera,nivel__nivelmalla=nivelmalla,fecha__gte=fechai,fecha__lte=fechaf).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2')

                    pdf.ln(30)  # Salto de linea
                    pdf.text(120,30,"EFICIENCIA GRADUADOS")
                    pdf.text(1,35,"CARRERA: "  + str(carrera))
                    pdf.text(1,40,"DESDE: "+ str(fechai))
                    pdf.text(1,45,"HASTA: "+ str(fechaf))
                    fechahoy=datetime.now()
                    fechahoy = fechahoy.strftime('%d/%m/%Y %H:%M:%S%p') # formato dd/mm/yyyy hh:mm:ss am o fm
                    pdf.text(1,50,"Fecha de Impresion: "+ str(fechahoy))
                    pdf.ln(20)  # Salto de linea

                    # para pruebas en desarrollo OCU
                    # locale.setlocale( locale.LC_ALL, '' )

                    # para produccion
                    locale.setlocale( locale.LC_ALL, 'en_US.UTF-8' )

                    # cabecera de la tabla
                    cabecera = ["IDENTIFICACION","NOMBRES","GRADUADO","NOTA SEMINARIO"]
                    w = [25,60,40,40]
                    for i in range(0, len(cabecera)):
                        pdf.cell(w[i], 5, cabecera[i], 1, 0, 'C', 0)
                    pdf.ln()

                    eficiencia=0
                    ef=0
                    mat=0
                    for m in matriculas:
                        record=0
                        identificacion=''
                        mat=mat +1
                        if m.inscripcion.persona.cedula:
                            identificacion=m.inscripcion.persona.cedula
                        else:
                            identificacion=m.inscripcion.persona.pasaporte

                        if RecordAcademico.objects.filter(asignatura__id=521,inscripcion=m.inscripcion).exists():
                            record =RecordAcademico.objects.filter(asignatura__id=521,inscripcion=m.inscripcion)[:1].get().nota
                        if Graduado.objects.filter(inscripcion=m.inscripcion).exists():
                            graduado = 'SI'
                            ef=ef+1
                        else:
                            graduado = 'NO'

                        if mat >0:
                            eficiencia =( ef*100)/mat

                        pdf.set_font('Arial', '', 6)  # Arial bold 6
                        pdf.set_fill_color(170, 235, 210) # verde agua

                        pdf.cell(25, 5, str(identificacion), 'LR',0,'C')
                        pdf.cell(60, 5, str(elimina_tildes(m.inscripcion.persona.nombre_completo_inverso())), 'LR')
                        pdf.cell(40, 5, str(graduado), 'LR',0,'C')
                        pdf.cell(40, 5, str(record), 'LR',0,'C')
                        pdf.ln()

                    pdf.ln(10)
                    pdf.set_font('Arial','B',12)  # Arial bold 12
                    pdf.cell(85,5,"Eficiencia: ",'LR',0,'C')
                    pdf.cell(85,5,str(eficiencia),'LR',0,'C')
                    pdf.set_font('')  # restauro la fuente

                    d = datetime.now()
                    pdfname = 'eficiencia' + '_' + d.strftime('%Y%m%d_%H%M%S') + '.pdf'
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
                    return HttpResponse(json.dumps({"result":"ok"}), content_type="application/json")



        else:
            data = {'title': 'Eficiencia Graduados por Carrera'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform']=EficienciaExcelForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
                return render(request ,"reportesexcel/eficiencia.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

