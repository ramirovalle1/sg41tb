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
from sga.forms import RangoFacturasForm, DistributivoForm
from sga.models import convertir_fecha,Materia,TituloInstitucion,ReporteExcel, Profesor, Materia,Nivel,Periodo,ProfesorMateria,Clase,Carrera
from sga.reportes import elimina_tildes
from fpdf import FPDF



@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action  =='generarexcel':
                try:
                    nivel = Nivel.objects.filter(pk=request.POST['nivel'])[:1].get()
                    m = 10
                    total=nivel.matriculados().count()
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo3 = xlwt.easyxf('font: name Times New Roman; align: wrap on, vert centre, horiz center')
                    subtitulo.font.height = 20*10
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('Registros',cell_overwrite_ok=True)

                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,m, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,m, 'LISTADO DE ESTUDIANTES POR NIVEL',titulo2)
                    ws.write(3, 0,'CARRERA: ' +nivel.carrera.nombre , subtitulo)
                    ws.write(4, 0,'GRUPO:   ' +nivel.grupo.nombre, subtitulo)
                    ws.write(5, 0,'NIVEL:   ' +nivel.nivelmalla.nombre, subtitulo)

                    fila = 7
                    com = 7
                    detalle = 3
                    columna=6
                    c=6
                    telefono1=''
                    telefono2=''
                    correo1=''
                    correo2=''
                    ws.write(6,4,"TELF. CONV",subtitulo3)
                    ws.write(6,5,"CELULAR",subtitulo3)
                    ws.write(6,7,"EMAIL PERSONAL",subtitulo3)
                    ws.write(6,10,"EMAIL INSTITUCIONAL",subtitulo3)

                    for matri in nivel.matriculados():
                        columna=columna+1

                        if matri.inscripcion.persona.cedula:
                            identificacion=matri.inscripcion.persona.cedula
                        else:
                            identificacion=matri.inscripcion.persona.pasaporte

                        if matri.inscripcion.persona.telefono_conv:
                            telefono1=matri.inscripcion.persona.telefono_conv
                        else:
                            telefono1=''

                        if matri.inscripcion.persona.telefono:
                            telefono2=matri.inscripcion.persona.telefono
                        else:
                            telefono2=''

                        if matri.inscripcion.persona.email:
                            correo1=matri.inscripcion.persona.email
                        else:
                            correo1=''

                        if matri.inscripcion.persona.emailinst:
                            correo2=matri.inscripcion.persona.emailinst
                        else:
                            correo2=''

                        ws.write_merge(com, fila,0,0, str(identificacion) , subtitulo)
                        ws.write_merge(com, fila,1,3,matri.inscripcion.persona.nombre_completo_inverso(), subtitulo)
                        ws.write(fila,columna-3,str(telefono1), subtitulo3)
                        ws.write(fila,columna-2,str(telefono2), subtitulo3)
                        ws.write_merge(com, fila,6,8,str(correo1), subtitulo3)
                        ws.write_merge(com, fila,9,11,str(correo2), subtitulo3)

                        com=fila+1
                        fila = fila +1
                        columna=6

                    detalle = detalle + fila
                    ws.write(detalle,0, "Fecha Impresion", subtitulo)
                    ws.write(detalle,1, str(datetime.now()), subtitulo)
                    detalle=detalle+2
                    ws.write(detalle,0, "Usuario", subtitulo)
                    ws.write(detalle,1, str(request.user), subtitulo)

                    nombre ='alumnosporgrupo'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
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
                    nivel = Nivel.objects.filter(pk=request.POST['nivel'])[:1].get()
                    pdf.ln(30)  # Salto de linea
                    pdf.text(120,30,"LISTADO DE ESTUDIANTES POR NIVEL")
                    pdf.text(1,35,"CARRERA: "  + str(nivel.carrera.nombre))
                    pdf.text(1,40,"GRUPO: "+ str(nivel.grupo.nombre))
                    pdf.text(1,45,"NIVEL: "+ str(nivel.nivelmalla.nombre))
                    fechahoy=datetime.now()
                    fechahoy = fechahoy.strftime('%d/%m/%Y %H:%M:%S%p') # formato dd/mm/yyyy hh:mm:ss am o fm
                    pdf.text(1,50,"Fecha de Impresion: "+ str(fechahoy))
                    pdf.ln(20)  # Salto de linea

                    # para pruebas en desarrollo OCU
                    # locale.setlocale( locale.LC_ALL, '' )

                    # para produccion
                    locale.setlocale( locale.LC_ALL, 'en_US.UTF-8' )

                    # cabecera de la tabla
                    cabecera = ["IDENTIFICACION","ESTUDIANTE","TELF. CONV","CELULAR","EMAIL PERSONAL","EMAIL INSTITUCIONAL"]
                    w = [25,60,35,60,50,50]
                    for i in range(0, len(cabecera)):
                        pdf.cell(w[i], 5, cabecera[i], 1, 0, 'C', 0)
                    pdf.ln()

                    for matri in nivel.matriculados():
                        identificacion=''
                        telefono1=''
                        telefono2=''
                        correo1=''
                        correo2=''
                        if matri.inscripcion.persona.cedula:
                            identificacion=matri.inscripcion.persona.cedula
                        else:
                            identificacion=matri.inscripcion.persona.pasaporte

                        if matri.inscripcion.persona.telefono_conv:
                            telefono1=matri.inscripcion.persona.telefono_conv
                        else:
                            telefono1=''

                        if matri.inscripcion.persona.telefono:
                            telefono2=matri.inscripcion.persona.telefono
                        else:
                            telefono2=''

                        if matri.inscripcion.persona.email:
                            correo1=matri.inscripcion.persona.email
                        else:
                            correo1=''

                        if matri.inscripcion.persona.emailinst:
                            correo2=matri.inscripcion.persona.emailinst
                        else:
                            correo2=''

                        pdf.set_font('Arial', '', 6)  # Arial bold 6
                        pdf.set_fill_color(170, 235, 210) # verde agua

                        pdf.cell(25, 5, str(identificacion), 'LR',0,'C')
                        pdf.cell(60, 5, str(elimina_tildes(matri.inscripcion.persona.nombre_completo_inverso())), 'LR')
                        pdf.cell(35, 5, str(telefono1), 'LR',0,'C')
                        pdf.cell(60, 5, str(telefono2), 'LR')
                        pdf.cell(50, 5, str(correo1), 'LR', 0, 'C')
                        pdf.cell(50, 5, str(correo2), 'LR', 0, 'C')
                        pdf.ln()

                    pdf.ln(10)
                    pdf.set_font('Arial','B',12)  # Arial bold 12
                    pdf.set_font('')  # restauro la fuente

                    d = datetime.now()
                    pdfname = 'alumnosporgrupo' + '_' + d.strftime('%Y%m%d_%H%M%S') + '.pdf'
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
            data = {'title': 'Listado de Alumnos por Grupo'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                return render(request ,"reportesexcel/alumnosporgrupo.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))


















