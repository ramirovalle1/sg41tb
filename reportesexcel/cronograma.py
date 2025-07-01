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
from sga.models import convertir_fecha,Materia,TituloInstitucion,ReporteExcel, Profesor, Materia,  Periodo, ProfesorMateria,Clase,Carrera, RolPerfilProfesor
from sga.reportes import elimina_tildes
from fpdf import FPDF



@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action  =='generar':
                try:
                    inicio = convertir_fecha(request.POST['inicio'])
                    fin = convertir_fecha(request.POST['fin'])
                    # carrera =Carrera.objects.get(pk=request.POST['carrera'])
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo3 = xlwt.easyxf('font: name Times New Roman, colour blue, bold on')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10
                    style1 = xlwt.easyxf('',num_format_str='DD-MMM-YY')
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('Distributivo',cell_overwrite_ok=True)

                    ws.write_merge(1, 1,0,8, 'LISTADO DISTRIBUTIVO POR PROFESOR', titulo2)
                    ws.write(3, 0, 'FECHA INICIO', titulo)
                    ws.write(3, 1, str(inicio.date()), titulo)
                    ws.write(4, 0, 'FECHA FIN', titulo)
                    ws.write(4, 1, str(fin.date()), titulo)

                    # ws.write(5, 1, str(carrera), titulo)
                    cont =7
                    prof = Clase.objects.filter(materia__profesormateria__hasta__gte=inicio).distinct('materia__profesormateria__profesor').values('materia__profesormateria__profesor')
                    # prof = Clase.objects.filter(materia__nivel__carrera__id=request.POST['carrera'],materia__profesormateria__desde__gte=inicio,materia__profesormateria__hasta__gte=fin).distinct('materia__profesormateria__profesor').values('materia__profesormateria__profesor')
                    materias = Clase.objects.filter(materia__profesormateria__hasta__gte=inicio).distinct().values('materia').order_by('materia__nivel__periodo','materia__nivel__carrera')
                    # materias = Clase.objects.filter(materia__nivel__carrera__id=request.POST['carrera'],materia__profesormateria__desde__gte=inicio,materia__profesormateria__hasta__gte=fin).distinct('materia').values('materia')
                    profesor = Profesor.objects.filter(id__in=prof).order_by('persona__apellido1','persona__apellido2','persona__nombres')

                    c=1
                    for p in profesor:
                        tot = 0
                        totvalor = 0
                        th = 0
                        if c > 0:
                            c=0
                            cont = cont+2
                            ws.write(cont, 0, 'PERIODO', titulo)
                            ws.write(cont, 1, 'CARRERA', titulo)
                            ws.write(cont, 2, 'PROFESOR', titulo)
                            ws.write(cont, 3, 'TIPO DE CONTRATO', titulo)
                            ws.write(cont, 4, 'MATERIA', titulo)
                            ws.write(cont, 5, 'DESDE', titulo)
                            ws.write(cont, 6, 'HASTA', titulo)
                            ws.write(cont, 7, 'GRUPO', titulo)
                            ws.write(cont, 8, 'NIVEL', titulo)
                            ws.write(cont, 9, 'HORAS', titulo)
                            ws.write(cont, 10, 'VALOR', titulo)
                            ws.write(cont, 11, 'TURNO ENTRADA', titulo)
                            ws.write(cont, 12, 'TURNO SALIDA', titulo)
                            ws.write(cont, 13, 'CON HORARIO?', titulo)
                        tienehorario='No'
                        horainicia=''
                        horatermina=''
                        for pm in ProfesorMateria.objects.filter(hasta__gte=inicio,profesor=p,materia__id__in=materias):
                            th=th+1
                            if pm.materia.horas_materia_rangofecha(pm,inicio,fin)[0] > 0:
                            # if pm.materia.horas_materia_rangofecha(pm,inicio,fin,request.POST['carrera']) > 0:
                                c=c+1
                                cont = cont + 1
                                ws.write(cont, 0, str(pm.materia.nivel.periodo))
                                ws.write(cont, 1, str(elimina_tildes(pm.materia.nivel.carrera)))
                                ws.write(cont, 2, p.persona.nombre_completo())
                                ws.write(cont, 3, p.categoria.nombre)
                                ws.write(cont, 4, str(elimina_tildes(pm.materia.asignatura)))
                                ws.write(cont, 5, str(pm.desde))
                                ws.write(cont, 6, str(pm.hasta))
                                ws.write(cont, 7, str(elimina_tildes(pm.materia.nivel.paralelo)) )
                                ws.write(cont, 8, str(elimina_tildes(pm.materia.nivel.nivelmalla)))
                                ws.write(cont, 9, pm.materia.horas_materia_rangofecha(pm,inicio,fin)[0])
                                ws.write(cont, 10, pm.materia.horas_materia_rangofecha(pm,inicio,fin)[1])

                                clases = Clase.objects.filter(materia=pm.materia).order_by('turno__id')
                                comienza = ''
                                termina= ''
                                num_turno = 0
                                for clase in clases:
                                    if clase.materia.asignatura.id==876:
                                        if comienza == '':
                                            num_turno = num_turno + 1
                                            comienza = 'TURNO'+str(num_turno)+'('+str(clase.turno.comienza)+') '
                                            termina = 'TURNO'+str(num_turno)+'('+str(clase.turno.termina)+') '
                                        elif not clase.turno.comienza == comienza:
                                            num_turno = num_turno + 1
                                            comienza = comienza+'TURNO'+str(num_turno)+'('+str(clase.turno.comienza)+') '
                                            termina = termina+'TURNO'+str(num_turno)+'('+str(clase.turno.termina)+') '
                                    else:
                                        if not clase.turno.comienza == comienza:
                                            num_turno = num_turno + 1
                                            comienza = str(clase.turno.comienza)
                                            termina = str(clase.turno.termina)

                                ws.write(cont, 11, comienza)
                                ws.write(cont, 12, termina)
                                if pm.profesor.conhorario:
                                    if th==1:
                                        horainicia = pm.profesor.horainicio
                                        horatermina = pm.profesor.horafin
                                        ws.write(cont-1, 14, 'Desde: '+ str(horainicia)+ ' Hasta: '+ str(horatermina),titulo3)
                                # ws.write(cont, 8, pm.materia.horas_materia_rangofecha(pm,inicio,fin,request.POST['carrera']))

                                tot = tot +pm.materia.horas_materia_rangofecha(pm,inicio,fin)[0]
                                totvalor = totvalor +pm.materia.horas_materia_rangofecha(pm,inicio,fin)[1]
                                # tot = tot +pm.materia.horas_materia_rangofecha(pm,inicio,fin,request.POST['carrera'])
                        if tot > 0:
                            cont = cont +1
                            ws.write_merge(cont,cont,0 ,7, "TOTAL HORAS",titulo)
                            ws.write(cont,8,str(tot),titulo)
                            ws.write(cont,9,str(totvalor),titulo)
                    if c == 0:
                        ws.write(cont, 0, '')
                        ws.write(cont, 1, '')
                        ws.write(cont,2, '')
                        ws.write(cont, 3, '')
                        ws.write(cont,4, '')
                        ws.write(cont,5, '')
                        ws.write(cont, 6, '')
                        ws.write(cont, 7, '')

                    nombre ='cronogramamaterias'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")
                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")

            elif action  =='generarpdf':
                try:
                    inicio = convertir_fecha(request.POST['inicio'])
                    fin = convertir_fecha(request.POST['fin'])

                    pdf = FPDF()
                    pdf.add_page('Landscape')
                    pdf.set_font('Arial', 'B', 8)  # Arial bold 8
                    # pdf.SetAutoPageBreak(boolean auto [, float margin])
                    pdf.alias_nb_pages(alias='pag_total')
                    # pdf.set_auto_page_break(1,15)
                    prof = Clase.objects.filter(materia__profesormateria__hasta__gte=inicio).distinct('materia__profesormateria__profesor').values('materia__profesormateria__profesor')
                    materias = Clase.objects.filter(materia__profesormateria__hasta__gte=inicio).distinct('materia').values('materia').order_by('materia__nivel__periodo','materia__nivel__carrera')
                    profesor = Profesor.objects.filter(id__in=prof).order_by('persona__apellido1','persona__apellido2','persona__nombres')
                    # profesor = Profesor.objects.filter(id__in=prof).order_by('persona__apellido1','persona__apellido2','persona__nombres')[:10]
                    profesor_pdf=profesor
                    profesor_pdf = str(profesor_pdf)
                    pdf.image(SITE_ROOT+'/media/reportes/encabezados_pies/logo.png', 5, 5, 20,20)  # Logo
                    pdf.ln(30)  # Salto de linea
                    pdf.text(120,30,"LISTADO DISTRIBUTIVO POR PROFESOR")
                    pdf.text(1,35,"DESDE: "  + str(inicio.date()))
                    pdf.text(1,40,"HASTA: "+ str(fin.date()))
                    fechahoy=datetime.now()
                    fechahoy = fechahoy.strftime('%d/%m/%Y %H:%M:%S%p') # formato dd/mm/yyyy hh:mm:ss am o fm
                    pdf.text(1,45,"Fecha de Impresion: "+ str(fechahoy))
                    pdf.ln(10)  # Salto de linea

                    # para pruebas en desarrollo OCU
                    # locale.setlocale( locale.LC_ALL, '' )

                    # para produccion
                    locale.setlocale( locale.LC_ALL, 'en_US.UTF-8' )

                    # cabecera de la tabla
                    cabecera = ["PERIODO","CARRERA","PROFESOR","MATERIA","DESDE","HASTA","GRUPO","NIVEL","HORAS","VALOR"]
                    w = [60,35,48,55,15,15,12,20,10,10]
                    for i in range(0, len(cabecera)):
                        pdf.cell(w[i], 5, cabecera[i], 1, 0, 'C', 0)
                    pdf.ln()

                    for p in profesor:
                        tot = 0
                        totvalor = 0
                        for pm in ProfesorMateria.objects.filter(hasta__gte=inicio,profesor=p,materia__id__in=materias):
                            mat=ProfesorMateria.objects.filter(hasta__gte=inicio,profesor=p,materia__id__in=materias)
                            pdf.set_font('Arial', '', 6)  # Arial bold 6
                            # pdf.set_fill_color(62, 255, 175) # color verde
                            # pdf.set_fill_color(255, 0, 0) #color rojo
                            pdf.set_fill_color(170, 235, 210) # verde agua

                            if pm.materia.horas_materia_rangofecha(pm,inicio,fin)[0] > 0:
                                pdf.cell(60, 5,str(pm.materia.nivel.periodo.nombre), 'LR')
                                pdf.cell(35, 5, str(elimina_tildes(pm.materia.nivel.carrera.alias)), 'LR')
                                pdf.cell(48, 5, p.persona.nombre_completo(), 'LR')
                                pdf.cell(55, 5, str(elimina_tildes(pm.materia.asignatura.nombre))[0:45], 'LR')
                                pdf.cell(15, 5, str(pm.desde), 'LR', 0, 'R')
                                pdf.cell(15, 5, str(pm.hasta), 'LR', 0, 'R')
                                pdf.cell(12, 5, str(elimina_tildes(pm.materia.nivel.paralelo)), 'LR', 0, 'C')
                                pdf.cell(20, 5, str(elimina_tildes(pm.materia.nivel.nivelmalla)), 'LR', 0, 'C')
                                pdf.cell(10, 5, str (pm.materia.horas_materia_rangofecha(pm,inicio,fin)[0]),'LR',0,'C')
                                pdf.cell(10, 5, str(pm.materia.horas_materia_rangofecha(pm,inicio,fin)[1]),'LR',0,'C')
                                pdf.ln()

                                tot = tot +pm.materia.horas_materia_rangofecha(pm,inicio,fin)[0]
                                totvalor = totvalor +pm.materia.horas_materia_rangofecha(pm,inicio,fin)[1]

                        if tot > 0:
                            pdf.set_font('Arial', 'B', 9)  # Arial bold 9
                            # fill en 1 indica fondo a la tabla
                            pdf.cell(198,5,"TOTAL HORAS:",'LR',0,'R')
                            pdf.cell(82,5,str(str(tot)+" - "+str(totvalor)),'LR',0,'R')
                            pdf.set_font('')  # restauro la fuente
                            pdf.ln(7)

                            # este paginado funciona pero se monta en la data ojojojo
                            # pdf.set_font('Arial','',7)  # Arial bold 8
                            # paginado = u'Pagina {0} de pag_total'.format(pdf.page_no())
                            # pdf.text(250,45,str(paginado))
                            # pdf.set_font('')  # restauro la fuente

                    pdf.ln(10)
                    pdf.set_font('Arial','B',12)  # Arial bold 12
                    pdf.cell(80,5,"Revisado por: ",'1','LR',0,'C')
                    pdf.set_font('')  # restauro la fuente

                    d = datetime.now()
                    pdfname = 'cronograma' + '_' + d.strftime('%Y%m%d_%H%M%S') + '.pdf'
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
            data = {'title': 'Distributivo Docentes'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform']=DistributivoForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
                return render(request ,"reportesexcel/cronograma.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))


















