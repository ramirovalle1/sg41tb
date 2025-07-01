from datetime import datetime,time
import json
from django.contrib.admin.models import LogEntry
import xlwt
import os
import locale
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from settings import MEDIA_ROOT,TIPOSEGMENTO_PRACT,UTILIZA_FACTURACION_CON_FPDF,JR_USEROUTPUT_FOLDER,MEDIA_URL, SITE_ROOT, COSTO_SEGMENTO_PRACTICA
from sga.commonviews import addUserData
from sga.forms import HorasDictadasForm
from sga.models import convertir_fecha,Materia,TituloInstitucion,ReporteExcel,RolPago, Profesor,RolPagoProfesor,RolPagoDetalleProfesor,Materia,  Periodo, ProfesorMateria,Clase,Carrera,LeccionGrupo,Sede,TitulacionProfesor, RolPerfilProfesor
from sga.reportes import elimina_tildes
from fpdf import FPDF



@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action  =='generar':
                try:
                    prof=None
                    docente=''
                    rol = request.POST['rol']
                    rolpago=RolPago.objects.filter(pk=rol)[:1].get()
                    doc=False
                    if request.POST['profesor']!='':
                        docente = request.POST['profesor']
                        docente = Profesor.objects.filter(pk=docente)[:1].get()
                        prof = LeccionGrupo.objects.filter(materia__nivel__periodo__activo=True,profesor=docente,fecha__gte=rolpago.inicio,fecha__lte=rolpago.fin,turno__practica=True).order_by('materia').distinct().values('materia')
                        doc=True
                    else:
                        prof = LeccionGrupo.objects.filter(materia__nivel__periodo__activo=True,fecha__gte=rolpago.inicio,fecha__lte=rolpago.fin,turno__practica=True).distinct().order_by('profesor').values('profesor')

                    inicio=datetime.combine(rolpago.inicio,time(0,0,0,1))
                    fin=datetime.combine(rolpago.fin,time(0,0,0,1))
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10
                    style1 = xlwt.easyxf('',num_format_str='DD-MMM-YY')
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('practicas',cell_overwrite_ok=True)
                    m = 12
                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,m, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,m, 'LISTADO CLASES PRACTICAS', titulo2)
                    ws.write(3, 0, 'Rol Pago:', titulo)
                    ws.write(3, 1, elimina_tildes(rolpago.nombre), titulo)

                    cont =3
                    detalle = 3

                    c=1
                    cont = cont+2
                    ws.write(cont, 0,  'IDENTIFICACION', titulo)
                    ws.write(cont, 1,  'DOCENTE', titulo)
                    ws.write(cont, 2,  'ASIGNATURA', titulo)
                    ws.write(cont, 3,  'SEGMENTO', titulo)
                    ws.write(cont, 4,  'DESDE', titulo)
                    ws.write(cont, 5,  'HASTA', titulo)
                    ws.write(cont, 6,  'NIVEL/PARALELO', titulo)
                    ws.write(cont, 7,  'CARRERA', titulo)
                    ws.write(cont, 8,  'COSTOHORA', titulo)
                    ws.write(cont, 9,  'HORAS', titulo)
                    ws.write(cont, 10,  '% DCTO', titulo)
                    ws.write(cont, 11, 'VALOR TOTAL', titulo)
                    cont=cont+1
                    valormateria=0
                    totalhoras=0
                    totalhorasgeneral=0
                    totalvalorgeneral=0
                    materia=''
                    materiainicia=''
                    materiatermina=''
                    segmento=''
                    carrera=''
                    nivelmalla=''
                    grupo=''
                    costohora=0
                    profesor=''
                    descuento=0
                    for p in prof:
                        # print((p))
                        pm=''
                        pr=''
                        if docente:
                            if ProfesorMateria.objects.filter(profesor=docente,segmento__id=TIPOSEGMENTO_PRACT,materia=p['materia']).exists():
                                pm = ProfesorMateria.objects.filter(profesor=docente,segmento__id=TIPOSEGMENTO_PRACT,materia=p['materia'])
                        else:
                            if ProfesorMateria.objects.filter(profesor=p['profesor'],segmento__id=TIPOSEGMENTO_PRACT).exists():
                                pm = ProfesorMateria.objects.filter(profesor=p['profesor'],segmento__id=TIPOSEGMENTO_PRACT).order_by('materia')
                        if pm!='':
                            for pr in pm:
                                valormateria=0
                                materiainicia=str(pr.desde)
                                materiatermina=str(pr.hasta)
                                segmento=pr.segmento.descripcion
                                lg=''
                                materia=''
                                carrera=''
                                nivelmalla=''
                                grupo=''
                                descuento=''
                                for lg in LeccionGrupo.objects.filter(materia__nivel__periodo__activo=True,profesor=pr.profesor,fecha__gte=inicio,fecha__lte=fin,materia=pr.materia,turno__practica=True).order_by('materia__nivel__grupo'):
                                    # print((lg))
                                    valormateria+= lg.costo_profesor_dia(lg.fecha)
                                    materia=str(elimina_tildes(lg.materia.asignatura.nombre))
                                    nivelmalla= str(elimina_tildes(lg.materia.nivel.nivelmalla.nombre))
                                    carrera=str(elimina_tildes(lg.materia.nivel.carrera.nombre))
                                    grupo=str(elimina_tildes(lg.materia.nivel.paralelo))
                                    #OCastillo 20-09-2023 se incluye descuento por motivo de cierre
                                    if lg.motivocierre!=None:
                                        if lg.motivocierre.id>0:
                                            if lg.motivocierre.porcentajedescuento>0:
                                                descuento=0
                                                # descuento=lg.motivocierre.porcentajedescuento
                                if lg!='':
                                    # totalhoras=RolPagoDetalleProfesor.objects.filter(rolprof__rol=rolpago,materia=lg.materia)[:1].get()
                                    totalhoras=lg.calcula_horas_materia_practica(pr.profesor,inicio,fin)
                                    totalhorasgeneral+=totalhoras
                                    totalvalorgeneral+=valormateria
                                    #OCastillo agosto-2023 el valor por hora para el segmento practica queda en 10 para todos
                                    costohora=COSTO_SEGMENTO_PRACTICA
                                    # if pr.valorporhora:
                                    #     costohora=pr.valor
                                    # else:
                                    #     costohora=valormateria/totalhoras
                                    c=c+1
                                    profesor=str(elimina_tildes(pr.profesor.persona.nombre_completo_inverso()))
                                    ws.write(cont,0,str(elimina_tildes(pr.profesor.persona.cedula)),titulo)
                                    ws.write(cont,1,profesor,titulo)
                                    ws.write(cont,2,materia)
                                    ws.write(cont,3,segmento)
                                    ws.write(cont,4, materiainicia)
                                    ws.write(cont,5, materiatermina)
                                    ws.write(cont,6, nivelmalla+' '+grupo)
                                    ws.write(cont,7, carrera)
                                    ws.write(cont,8, costohora)
                                    ws.write(cont,9, totalhoras)
                                    ws.write(cont,10, descuento)
                                    ws.write(cont,11, valormateria)
                                    cont = cont + 1
                            if c!=1 and not doc:
                                ws.write(cont,0,'TOTAL:',titulo)
                                ws.write(cont,1,profesor,titulo)
                                ws.write(cont,9, totalhorasgeneral,titulo)
                                ws.write(cont,11, totalvalorgeneral,titulo)
                                totalhorasgeneral=0
                                totalvalorgeneral=0
                                c=1
                                cont=cont+1
                    if c!=1:
                        ws.write(cont,0,'TOTAL:',titulo)
                        ws.write(cont,1,profesor,titulo)
                        ws.write(cont,9, totalhorasgeneral,titulo)
                        ws.write(cont,11, totalvalorgeneral,titulo)
                        totalhorasgeneral=0
                        totalvalorgeneral=0
                        c=1
                        cont=cont+1

                    detalle = detalle + cont
                    ws.write(detalle, 0, "Fecha Impresion", subtitulo)
                    ws.write(detalle, 1, str(datetime.now()), subtitulo)
                    detalle=detalle +1
                    ws.write(detalle, 0, "Usuario", subtitulo)
                    ws.write(detalle, 1, str(request.user), subtitulo)

                    nombre ='horaspracticas'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")
                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")

            elif action  =='generarpdf':
                try:
                    pdf = FPDF()
                    pdf.add_page('Landscape')
                    pdf.set_font('Arial', 'B', 7)  # Arial bold 8
                    pdf.alias_nb_pages(alias='pag_total')
                    pdf.image(SITE_ROOT+'/media/reportes/encabezados_pies/logo.png', 5, 5, 20,20)

                    prof=None
                    docente=''
                    rol = request.POST['rol']
                    rolpago=RolPago.objects.filter(pk=rol)[:1].get()
                    doc=False
                    if request.POST['profesor']!='':
                        docente = request.POST['profesor']
                        docente = Profesor.objects.filter(pk=docente)[:1].get()
                        prof = LeccionGrupo.objects.filter(materia__nivel__periodo__activo=True,profesor=docente,fecha__gte=rolpago.inicio,fecha__lte=rolpago.fin,turno__practica=True).order_by('materia').distinct().values('materia')
                        doc=True
                    else:
                        prof = LeccionGrupo.objects.filter(materia__nivel__periodo__activo=True,fecha__gte=rolpago.inicio,fecha__lte=rolpago.fin,turno__practica=True).distinct().order_by('profesor').values('profesor')

                    inicio=datetime.combine(rolpago.inicio,time(0,0,0,1))
                    fin=datetime.combine(rolpago.fin,time(0,0,0,1))

                    pdf.ln(30)  # Salto de linea
                    pdf.text(120,30,"LISTADO CLASES PRACTICAS" )
                    pdf.text(1,35,"ROL PAGO: "  + elimina_tildes(rolpago.nombre))
                    fechahoy=datetime.now()
                    fechahoy = fechahoy.strftime('%d/%m/%Y %H:%M:%S%p') # formato dd/mm/yyyy hh:mm:ss am o fm
                    pdf.text(1,50,"Fecha de Impresion: "+ str(fechahoy))
                    pdf.text(1,55,"Usuario: "+ str(request.user))
                    pdf.ln(20)  # Salto de linea

                    # para pruebas en desarrollo OCU
                    # locale.setlocale( locale.LC_ALL, '' )

                    # para produccion
                    locale.setlocale( locale.LC_ALL, 'en_US.UTF-8' )

                    # cabecera de la tabla
                    # cabecera = ["IDENTIFICACION","DOCENTE","ASIGNATURA","SEGMENTO","DESDE","HASTA","NIVEL/PARALELO","CARRERA","C. HORA","HORAS","V. TOTAL"]
                    cabecera = ["IDENTIFICACION","DOCENTE","ASIGNATURA","DESDE","HASTA","NIVEL/PARALELO","CARRERA","C. HORA","HORAS","%DCTO","V. TOTAL"]
                    w = [20,60,40,15,15,35,40,15,15,15,15]
                    for i in range(0, len(cabecera)):
                        pdf.cell(w[i], 5, cabecera[i], 1, 0, 'C', 0)
                    pdf.ln()

                    valormateria=0
                    totalhoras=0
                    totalhorasgeneral=0
                    totalvalorgeneral=0
                    materia=''
                    materiainicia=''
                    materiatermina=''
                    segmento=''
                    carrera=''
                    nivelmalla=''
                    grupo=''
                    costohora=0
                    profesor=''
                    descuento=''
                    c=1
                    for p in prof:
                        # print((p))
                        pm=''
                        pr=''
                        if docente:
                            if ProfesorMateria.objects.filter(profesor=docente,segmento__id=TIPOSEGMENTO_PRACT,materia=p['materia']).exists():
                                pm = ProfesorMateria.objects.filter(profesor=docente,segmento__id=TIPOSEGMENTO_PRACT,materia=p['materia'])
                        else:
                            if ProfesorMateria.objects.filter(profesor=p['profesor'],segmento__id=TIPOSEGMENTO_PRACT).exists():
                                pm = ProfesorMateria.objects.filter(profesor=p['profesor'],segmento__id=TIPOSEGMENTO_PRACT).order_by('materia')
                        if pm!='':
                            for pr in pm:
                                valormateria=0
                                materiainicia=str(pr.desde)
                                materiatermina=str(pr.hasta)
                                segmento=pr.segmento.descripcion
                                lg=''
                                materia=''
                                carrera=''
                                nivelmalla=''
                                grupo=''
                                descuento=''
                                for lg in LeccionGrupo.objects.filter(materia__nivel__periodo__activo=True,profesor=pr.profesor,fecha__gte=inicio,fecha__lte=fin,materia=pr.materia,turno__practica=True).order_by('materia__nivel__grupo'):
                                    # print((lg))
                                    valormateria+= lg.costo_profesor_dia(lg.fecha)
                                    materia=str(elimina_tildes(lg.materia.asignatura.nombre))
                                    nivelmalla= str(elimina_tildes(lg.materia.nivel.nivelmalla.nombre))
                                    carrera=str(elimina_tildes(lg.materia.nivel.carrera.alias))
                                    grupo=str(elimina_tildes(lg.materia.nivel.paralelo))
                                    #OCastillo 20-09-2023 se incluye descuento por motivo de cierre
                                    if lg.motivocierre!=None:
                                        if lg.motivocierre.id>0:
                                            if lg.motivocierre.porcentajedescuento>0:
                                                # descuento=str(lg.motivocierre.porcentajedescuento)
                                                descuento=0
                                if lg!='':
                                    # totalhoras=RolPagoDetalleProfesor.objects.filter(rolprof__rol=rolpago,materia=lg.materia)[:1].get()
                                    totalhoras=lg.calcula_horas_materia_practica(pr.profesor,inicio,fin)
                                    totalhorasgeneral+=totalhoras
                                    totalvalorgeneral+=valormateria
                                    #OCastillo agosto-2023 el valor por hora para el segmento practica queda en 10 para todos
                                    costohora=COSTO_SEGMENTO_PRACTICA
                                    # if pr.valorporhora:
                                    #     costohora=pr.valor
                                    # else:
                                    #     costohora=valormateria/totalhoras
                                    c=c+1
                                    profesor=str(elimina_tildes(pr.profesor.persona.nombre_completo_inverso()))

                                    pdf.cell(20, 5, str(elimina_tildes(pr.profesor.persona.cedula)), 'LR',0,'C')
                                    pdf.cell(60, 5, profesor, 'LR',0,'C')
                                    pdf.cell(40, 5, materia, 'LR',0,'C')
                                    # pdf.cell(15, 5, segmento, 'LR',0,'C')
                                    pdf.cell(15, 5, materiainicia, 'LR',0,'C')
                                    pdf.cell(15, 5, materiatermina, 'LR',0,'C')
                                    pdf.cell(35, 5, nivelmalla+' '+grupo, 'LR',0,'C')
                                    pdf.cell(40, 5, carrera, 'LR',0,'C')
                                    pdf.cell(15, 5, str(costohora), 'LR',0,'C')
                                    pdf.cell(15, 5, str(totalhoras), 'LR',0,'C')
                                    pdf.cell(15, 5, str(descuento), 'LR',0,'C')
                                    pdf.cell(15, 5, str(valormateria), 'LR',0,'C')
                                    pdf.ln()

                            if c!=1 and not doc:
                                pdf.cell(20, 5, 'TOTAL', 1, 0, 'C', 0)
                                pdf.cell(60, 5, profesor, 1, 0, 'C', 0)
                                pdf.cell(40, 5, ' ', 1, 0, 'C', 0)
                                # pdf.cell(15, 5, ' ', 1, 0, 'C', 0)
                                pdf.cell(15, 5, ' ', 1, 0, 'C', 0)
                                pdf.cell(15, 5, ' ', 1, 0, 'C', 0)
                                pdf.cell(35, 5, ' ', 1, 0, 'C', 0)
                                pdf.cell(40, 5, ' ', 1, 0, 'C', 0)
                                pdf.cell(15, 5, ' ', 1, 0, 'C', 0)
                                pdf.cell(15, 5, str(totalhorasgeneral), 1, 0, 'C', 0)
                                pdf.cell(15, 5, ' ', 1, 0, 'C', 0)
                                pdf.cell(15, 5, str(totalvalorgeneral), 1, 0, 'C', 0)
                                pdf.ln()
                                totalhorasgeneral=0
                                totalvalorgeneral=0
                                c=1

                    if c!=1:
                        pdf.cell(20, 5, 'TOTAL', 1, 0, 'C', 0)
                        pdf.cell(60, 5, profesor,1, 0, 'C', 0)
                        pdf.cell(40, 5, ' ', 1, 0, 'C', 0)
                        # pdf.cell(15, 5, ' ', 1, 0, 'C', 0)
                        pdf.cell(15, 5, ' ', 1, 0, 'C', 0)
                        pdf.cell(15, 5, ' ', 1, 0, 'C', 0)
                        pdf.cell(35, 5, ' ', 1, 0, 'C', 0)
                        pdf.cell(40, 5, ' ', 1, 0, 'C', 0)
                        pdf.cell(15, 5, ' ', 1, 0, 'C', 0)
                        pdf.cell(15, 5, str(totalhorasgeneral), 1, 0, 'C', 0)
                        pdf.cell(15, 5, ' ', 1, 0, 'C', 0)
                        pdf.cell(15, 5, str(totalvalorgeneral), 1, 0, 'C', 0)
                        pdf.ln()

                        totalhorasgeneral=0
                        totalvalorgeneral=0
                        c=1

                    pdf.ln(10)
                    pdf.set_font('Arial','B',12)  # Arial bold 12
                    pdf.set_font('')  # restauro la fuente
                    d = datetime.now()
                    pdfname = 'horaspracticas' + '_' + d.strftime('%Y%m%d_%H%M%S') + '.pdf'
                    output_folder = os.path.join(JR_USEROUTPUT_FOLDER, elimina_tildes(request.user.username))
                    try:
                        os.makedirs(output_folder)
                    except Exception as ex:
                        pass
                    pdf.output(os.path.join(output_folder, pdfname))
                    return HttpResponse(json.dumps({'result': 'ok','reportfile': '/'.join([MEDIA_URL,'documentos','userreports',request.user.username,pdfname])}),content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":"ok"}), content_type="application/json")

        else:
            data = {'title': 'Horas Materias Practicas '}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform']=HorasDictadasForm()
                return render(request ,"reportesexcel/horaspracticasporrol.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))


















