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
from sga.models import Inscripcion, convertir_fecha, Factura, ClienteFactura, TituloInstitucion, ReporteExcel, \
    NotaCreditoInstitucion, Persona, TipoNotaCredito, Carrera, Matricula, RecordAcademico, EstudianteVinculacion, \
    InscripcionPracticas
from sga.reportes import elimina_tildes
from fpdf import FPDF

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):

    try:
        if request.method=='POST':
            action = request.POST['action']
            if action =='generarexcel':
                idinscrip=''
                try:
                    print(request.POST)
                    carrera=None
                    desde = str(request.POST['inicio'])
                    hasta = str(request.POST['fin'])


                    if request.POST['chkcarrera'] == 'true':
                        carrera= Carrera.objects.filter(pk=request.POST['carrera'])[:1].get()
                        matriculas = Matricula.objects.filter(nivel__carrera=carrera).select_related('inscripcion').order_by('fecha','inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')
                        if request.POST['chkcerrado'] == 'true':
                            print(1)
                            matriculas = matriculas.filter(nivel__cerrado=False)
                            # Matricula.objects.filter(nivel__carrera=carrera,nivel__cerrado=False).order_by('fecha','inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')
                        else:
                            print(2)
                            if request.POST['chkabierto'] == 'true':
                                matriculas = matriculas.filter(nivel__cerrado=True)
                                # Matricula.objects.filter(nivel__carrera=carrera,nivel__cerrado=True).order_by('fecha','inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres'))
                    elif desde:
                        desde = convertir_fecha(request.POST['inicio'])
                        hasta = convertir_fecha(request.POST['fin'])

                        matriculas = Matricula.objects.filter(fecha__gte=desde,fecha__lte=hasta).select_related('inscripcion').order_by('fecha','inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')

                    else:
                        matriculas = Matricula.objects.filter().select_related('inscripicion').order_by('fecha','inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')
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
                    ws.write_merge(0, 0,0,14, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,14, 'LISTADO DE HORAS DE VINCULACION Y PRACTICAS ', titulo2)
                    if carrera:
                        ws.write(2, 0, 'CARRERA:', titulo)
                        ws.write(2, 1, carrera.nombre, titulo)
                    if desde:
                        print(desde)
                        print(45)
                        ws.write(3, 0, 'INICO:', titulo)
                        ws.write(3, 1, str(desde), titulo)
                        ws.write(4, 0, 'FIN:', titulo)
                        ws.write(4, 1, str(hasta), titulo)

                    ws.write(6, 0,  'IDENTIFICACION', titulo)
                    ws.write(6, 1,  'NOMBRES', titulo)
                    ws.write(6, 2,  'CELULAR', titulo)
                    ws.write(6, 3,  'CONVENCIONAL', titulo)
                    ws.write(6, 4,  'CORREO INSTITUCIONAL', titulo)
                    ws.write(6, 5,  'CORREO PERSONAL', titulo)
                    ws.write(6, 6,  'PROVINCIA', titulo)
                    ws.write(6, 7,  'CANTON', titulo)
                    ws.write(6, 8,  'PARROQUIA', titulo)
                    ws.write(6, 9,  'NIVEL', titulo)
                    ws.write(6, 10, 'PARALELO', titulo)
                    ws.write(6, 11, 'HORAS PRACTICA', titulo)
                    ws.write(6, 12, 'NOTA PRACTICA', titulo)
                    ws.write(6, 13, 'HORAS VINCULACION', titulo)
                    ws.write(6, 14, 'NOTA VINCULACION', titulo)

                    fila = 6
                    detalle = 3

                    for m in matriculas:
                        fila = fila +1
                        columna=0
                        h_vincula=0
                        insc_pract = 0
                        matri_inscripcion= m.inscripcion
                        # print(matri_inscripcion)
                        acad_vinculacion =RecordAcademico.objects.filter(inscripcion=matri_inscripcion,asignatura__id=ASIG_VINCULACION)
                        if acad_vinculacion:
                            n_vinculacion= acad_vinculacion.filter()[:1].get().nota
                        else:
                            n_vinculacion='NO TIENE NOTA'
                        acad_practica =RecordAcademico.objects.filter(inscripcion=matri_inscripcion,asignatura__id=ASIG_PRATICA)
                        if acad_practica:
                            n_practica= acad_practica.filter()[:1].get().nota
                        else:
                            n_practica='NO TIENE NOTA'
                        idinscrip = m.inscripcion.id

                        tieneviculacion = EstudianteVinculacion.objects.filter(inscripcion=matri_inscripcion).select_related('inscripcion')
                        if tieneviculacion:
                            h_vincula = tieneviculacion.filter().aggregate(Sum('horas'))['horas__sum'] #horas vinculacion

                        estudianteprac = InscripcionPracticas.objects.filter(inscripcion=matri_inscripcion).select_related('inscripcion')
                        if estudianteprac:
                            insc_pract = estudianteprac.filter().aggregate(Sum('horas'))['horas__sum'] # horas practicas
                            # print(h_vinculanuevo)
                        ################  ANTES  ############################
                        # if matri_inscripcion.tiene_vinculacion():
                        #     h_vincula = m.inscripcion.estudiantevinculacion_set.all().aggregate(Sum('horas'))['horas__sum']
                        #     print(h_vincula)

                        matri_inscripcionp=m.inscripcion.persona
                        if matri_inscripcionp.cedula:
                            ws.write(fila,columna , str(matri_inscripcionp.cedula))
                        else:
                            ws.write(fila,columna , str(matri_inscripcionp.pasaporte))
                        try:
                            ws.write(fila,columna+1 , str(matri_inscripcionp.nombre_completo_inverso()))
                        except Exception as ex:
                            ws.write(fila,columna+1, '')
                        try:
                            ws.write(fila,columna+2, elimina_tildes(matri_inscripcionp.telefono))
                        except Exception as ex:
                            ws.write(fila,columna+2, '')
                        try:
                            ws.write(fila,columna+3, elimina_tildes(matri_inscripcionp.telefono_conv))
                        except Exception as ex:
                            ws.write(fila,columna+3, '')
                        try:
                            ws.write(fila,columna+4, elimina_tildes(matri_inscripcionp.emailinst))
                        except Exception as ex:
                            ws.write(fila,columna+4, '')
                        try:
                            ws.write(fila,columna+5, elimina_tildes(matri_inscripcionp.email))
                        except Exception as ex:
                            ws.write(fila,columna+5, '')
                        try:
                            ws.write(fila,columna+6, elimina_tildes(matri_inscripcionp.provincia.nombre))
                        except Exception as ex:
                            ws.write(fila,columna+6, '')
                        try:
                            ws.write(fila,columna+7, elimina_tildes(matri_inscripcionp.canton.nombre))
                        except Exception as ex:
                            ws.write(fila,columna+7, '')
                        try:
                            ws.write(fila,columna+8, elimina_tildes(matri_inscripcionp.parroquia.nombre))
                        except Exception as ex:
                            ws.write(fila,columna+8, '')
                        nivelmalla=m.nivel.nivelmalla
                        if nivelmalla:
                            ws.write(fila,columna+9, nivelmalla.nombre)
                        nivelparalelo =m.nivel.paralelo
                        if nivelparalelo:
                            ws.write(fila,columna+10, nivelparalelo)

                        ws.write(fila,columna+11, insc_pract)
                        ws.write(fila,columna+12,n_practica)
                        ws.write(fila,columna+13,h_vincula)
                        ws.write(fila,columna+14,n_vinculacion)

                    detalle = detalle + fila
                    ws.write(detalle, 0, "Fecha Impresion", subtitulo)
                    ws.write(detalle, 2, str(datetime.now()), subtitulo)
                    detalle=detalle +1
                    ws.write(detalle, 0, "Usuario", subtitulo)
                    ws.write(detalle, 2, str(request.user), subtitulo)

                    nombre ='horas_vinculacion_practica'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex) + str(idinscrip) }),content_type="application/json")

            elif action  =='generarpdf':
                try:
                    pdf = FPDF()
                    pdf.add_page('Landscape')
                    pdf.set_font('Arial', 'B', 7)  # Arial bold 8
                    pdf.alias_nb_pages(alias='pag_total')
                    pdf.image(SITE_ROOT+'/media/reportes/encabezados_pies/logo.png', 5, 5, 20,20)  # Logo

                    carrera= Carrera.objects.filter(pk=request.POST['carrera'])[:1].get()
                    matriculas = Matricula.objects.filter(nivel__carrera=carrera,nivel__cerrado=False).order_by('fecha')

                    pdf.ln(30)  # Salto de linea
                    pdf.text(120,30,"LISTADO DE HORAS DE VINCULACION Y PRACTICAS" )
                    pdf.text(1,35,"CARRERA: "  + elimina_tildes(carrera))
                    fechahoy=datetime.now()
                    fechahoy = fechahoy.strftime('%d/%m/%Y %H:%M:%S%p') # formato dd/mm/yyyy hh:mm:ss am o fm
                    pdf.text(1,50,"Fecha de Impresion: "+ str(fechahoy))
                    pdf.ln(20)  # Salto de linea

                    # para pruebas en desarrollo OCU
                    # locale.setlocale( locale.LC_ALL, '' )

                    # para produccion
                    locale.setlocale( locale.LC_ALL, 'en_US.UTF-8' )

                    # cabecera de la tabla
                    cabecera = ["CEDULA","NOMBRES","NIVEL","PARALELO","HORAS PRACTICA","NOTA PRACTICA","HORAS VINCULACION","NOTA VINCULACION"]
                    w = [20,60,25,20,30,30,30,30]
                    for i in range(0, len(cabecera)):
                        pdf.cell(w[i], 5, cabecera[i], 1, 0, 'C', 0)
                    pdf.ln()

                    for m in matriculas:
                        print(m)
                        insc_pract=0
                        identificacion=''
                        if RecordAcademico.objects.filter(inscripcion=m.inscripcion,asignatura__id=ASIG_VINCULACION).exists():
                            n_vinculacion= RecordAcademico.objects.filter(inscripcion=m.inscripcion,asignatura__id=ASIG_VINCULACION)[:1].get().nota
                        else:
                            n_vinculacion='NO TIENE NOTA'
                        if RecordAcademico.objects.filter(inscripcion=m.inscripcion,asignatura__id=ASIG_PRATICA).exists():
                            n_practica= RecordAcademico.objects.filter(inscripcion=m.inscripcion,asignatura__id=ASIG_PRATICA)[:1].get().nota
                        else:
                            n_practica='NO TIENE NOTA'
                        if m.inscripcion.tiene_vinculacion():
                            insc_pract = m.inscripcion.estudiantevinculacion_set.all().aggregate(Sum('horas'))['horas__sum']

                        if m.inscripcion.persona.cedula:
                            identificacion=m.inscripcion.persona.cedula
                        else:
                            identificacion=m.inscripcion.persona.pasaporte
                        nombre =''
                        try:
                            nombre = elimina_tildes(m.inscripcion.persona.nombre_completo())
                        except:
                            pass
                        pdf.cell(20, 5, str(identificacion), 'LR',0,'C')
                        pdf.cell(60, 5, nombre, 'LR',0,'C')
                        pdf.cell(25, 5, str(str(m.nivel.nivelmalla)), 'LR',0,'C')
                        pdf.cell(20, 5, str(str(m.nivel.paralelo)), 'LR',0,'C')
                        pdf.cell(30, 5, str(str(m.inscripcion.horas_practicas())), 'LR',0,'C')
                        pdf.cell(30, 5, str(n_practica), 'LR',0,'C')
                        pdf.cell(30, 5, str(insc_pract), 'LR', 0, 'C')
                        pdf.cell(30, 5, str(n_vinculacion), 'LR',0,'C')
                        pdf.ln()

                    pdf.ln(10)
                    pdf.set_font('Arial','B',12)  # Arial bold 12
                    pdf.set_font('')  # restauro la fuente
                    d = datetime.now()
                    pdfname = 'vinculacion_practicas' + '_' + d.strftime('%Y%m%d_%H%M%S') + '.pdf'
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
            data = {'title': 'Listado de Horas Vinculacion-Practicas'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform']=VinculacionExcelForm()
                return render(request ,"reportesexcel/vinculacion_practicas.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

