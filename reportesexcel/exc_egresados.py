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
from settings import UTILIZA_GRUPOS_ALUMNOS, EMAIL_ACTIVE,MEDIA_ROOT, ASIG_VINCULACION, ASIG_PRATICA,JR_USEROUTPUT_FOLDER,MEDIA_URL, SITE_ROOT
from sga.commonviews import addUserData, ip_client_address
from sga.forms import RangoFacturasForm,RangoNCForm, VinculacionExcelForm
from sga.models import Inscripcion,convertir_fecha,Factura,ClienteFactura,TituloInstitucion,ReporteExcel,NotaCreditoInstitucion, Persona,TipoNotaCredito, Carrera, \
     Matricula, RecordAcademico, Egresado
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
                    egresados = Egresado.objects.filter(inscripcion__carrera=carrera).exclude(inscripcion__graduado__inscripcion__carrera=carrera).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2')
                    #egresados = Egresado.objects.filter(inscripcion__carrera=carrera).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2')
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
                    ws.write_merge(1, 1,0,m+2, 'LISTADO DE EGRESADOS ', titulo2)
                    ws.write(2, 0, 'CARRERA', titulo)
                    ws.write(2, 1, carrera.nombre, titulo)
                    ws.write(4, 0,  '#', titulo)
                    ws.write(4, 2,  'CEDULA', titulo)
                    ws.write(4, 1,  'NOMBRES', titulo)
                    ws.write(4, 3,  'TIPO DE TITULACION', titulo)
                    ws.write(4, 4,  'FECHA DE EGRESO', titulo)
                    ws.write(4, 5,  'MALLA', titulo)
                    ws.write(4, 6,  'CELULAR', titulo)
                    ws.write(4, 7,  'EMAIL', titulo)

                    fila = 4
                    detalle = 3
                    c=0
                    email=''
                    celular=''
                    for e in egresados:
                        c=c+1
                        if e.inscripcion.puede_egresar():
                            malla='SI'
                        else:
                            malla ='NO'
                        fila = fila +1
                        columna=0
                        ws.write(fila,columna , c)
                        ws.write(fila,columna+2 , str(e.inscripcion.persona.cedula))
                        ws.write(fila,columna+1, e.inscripcion.persona.nombre_completo_inverso())
                        ws.write(fila,columna+3, str(e.inscripcion.grupo().modalidad))
                        ws.write(fila,columna+4, str(e.fechaegreso))
                        ws.write(fila,columna+5, e.inscripcion.puede_egresar())

                        try:
                            if e.inscripcion.persona.telefono:
                                celular=e.inscripcion.persona.telefono.replace("-","")
                            else:
                                celular=''
                        except Exception as ex:
                            pass

                        if e.inscripcion.persona.email:
                            email=e.inscripcion.persona.email
                        else:
                            email=''

                        ws.write(fila,columna+6, celular)
                        ws.write(fila,columna+7, email)



                    detalle = detalle + fila
                    ws.write(detalle, 0, "Fecha Impresion", subtitulo)
                    ws.write(detalle, 2, str(datetime.now()), subtitulo)
                    detalle=detalle +1
                    ws.write(detalle, 0, "Usuario", subtitulo)
                    ws.write(detalle, 2, str(request.user), subtitulo)

                    nombre ='egresados'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
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
                    egresados = Egresado.objects.filter(inscripcion__carrera=carrera).exclude(inscripcion__graduado__inscripcion__carrera=carrera).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2')
                    # tit = TituloInstitucion.objects.all()[:1].get()
                    pdf.text(120,30,"EFICIENCIA GRADUADOS")
                    # pdf.ln(15)  # Salto de linea
                    pdf.text(1,35,"CARRERA: "  + str(elimina_tildes(carrera)))
                    fechahoy=datetime.now()
                    fechahoy = fechahoy.strftime('%d/%m/%Y %H:%M:%S%p') # formato dd/mm/yyyy hh:mm:ss am o fm
                    pdf.text(1,40,"Fecha de Impresion: "+ str(fechahoy))
                    pdf.ln(40)  # Salto de linea

                    # para pruebas en desarrollo OCU
                    # locale.setlocale( locale.LC_ALL, '' )

                    # para produccion
                    locale.setlocale( locale.LC_ALL, 'en_US.UTF-8' )

                    # cabecera de la tabla
                    cabecera = ["#","IDENTIFICACION","NOMBRES","TIPO DE TITULACION","FECHA DE EGRESO","MALLA"]
                    w = [5,25,60,40,30,60]
                    for i in range(0, len(cabecera)):
                        pdf.cell(w[i], 5, cabecera[i], 1, 0, 'C', 0)
                    pdf.ln()
                    malla=''
                    c=0

                    for e in egresados:
                        # print(e)
                        c=c+1
                        if e.inscripcion.puede_egresar():
                            malla='SI'
                        else:
                            malla ='NO'

                        if e.inscripcion.persona.cedula:
                            identificacion=e.inscripcion.persona.cedula
                        else:
                            identificacion=e.inscripcion.persona.pasaporte

                        pdf.set_font('Arial', '', 6)  # Arial bold 6
                        pdf.set_fill_color(170, 235, 210) # verde agua

                        pdf.cell(5,  5,  str(c), 'LR',0,'C')
                        pdf.cell(25,  5,  str(identificacion), 'LR',0,'C')
                        pdf.cell(60, 5, str(elimina_tildes(e.inscripcion.persona.nombre_completo_inverso())), 'LR')
                        pdf.cell(40, 5, str( e.inscripcion.grupo().modalidad), 'LR',0,'C')
                        pdf.cell(30, 5, str(e.fechaegreso), 'LR',0,'C')
                        pdf.cell(60, 5, str(e.inscripcion.puede_egresar()), 'LR',0,'C')
                        pdf.ln()

                    pdf.ln(10)
                    pdf.set_font('Arial','B',12)  # Arial bold 12
                    pdf.set_font('')  # restauro la fuente

                    d = datetime.now()
                    pdfname = 'exc_egresados' + '_' + d.strftime('%Y%m%d_%H%M%S') + '.pdf'
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
            data = {'title': 'Egresados por Carrera'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform']=VinculacionExcelForm()
                return render(request ,"reportesexcel/egresados.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

