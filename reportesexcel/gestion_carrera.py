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
from sga.forms import RangoFacturasForm,RangoNCForm, VinculacionExcelForm, GestionExcelForm
from sga.models import Inscripcion,convertir_fecha,Factura,ClienteFactura,TituloInstitucion,ReporteExcel,NotaCreditoInstitucion, Persona,TipoNotaCredito, Carrera, Matricula, RecordAcademico, Egresado, Malla, AsignaturaMalla, NivelMalla, MateriaAsignada, Asignatura, Nivel, Periodo, ProfesorMateria
from sga.reportes import elimina_tildes
from fpdf import FPDF

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action =='generarexcel':
                try:
                    carrera= Carrera.objects.filter(pk=request.POST['carrera'])[:1].get()
                    periodo= Periodo.objects.filter(pk=request.POST['periodo'])[:1].get()
                    malla = Malla.objects.filter(carrera=carrera,vigente=True)[:1].get()
                    nivelesmalla =  NivelMalla.objects.filter(pk__in=AsignaturaMalla.objects.filter(malla=malla).distinct('nivelmalla').values('nivelmalla')).order_by('orden')
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
                    ws.write_merge(0, 0,0,m+10, tit.nombre , subtitulo)
                    ws.write_merge(1, 1,0,m+10, 'MATRIZ DE GESTION - PERIODO ' + periodo.nombre, subtitulo)
                    ws.write(3, 1, '# ', subtitulo)
                    ws.write(3, 2, 'CARRERA ' +carrera.nombre , subtitulo)
                    ws.write(3, 3,  'SEDE', subtitulo)
                    ws.write(3, 4,  'GRUPOS', subtitulo)
                    ws.write(3, 5,  'HORARIO', subtitulo)
                    ws.write(3, 6,  'DOCENTE ASIGNADO', subtitulo)
                    ws.write(3, 7,  '# ESTUDIANTES INICIAL', subtitulo)
                    ws.write(3, 8,  '# ESTUDIANTES ACTUAL MATRICULADOS', subtitulo)
                    ws.write(3, 9,  '# ESTUDIANTES BECADOS', subtitulo)
                    ws.write(3, 10,  '% ASISTENCIA ESTUDIANTES', subtitulo)
                    ws.write(3, 11,  '% ASISTENCIA DOCENTE', subtitulo)
                    ws.write(3, 12,  'ESTADO DE LA ASIGNATURA', subtitulo)
                    ws.write(3, 13,  'VALORES VENCIDOS', subtitulo)
                    ws.write(3, 14,  'INICIO', subtitulo)
                    ws.write(3, 15,  'FIN', subtitulo)

                    fila = 3
                    com = 3
                    detalle = 3
                    c=0
                    for nm in nivelesmalla:
                        c=c+1
                        numasig=0
                        asignaturas = Asignatura.objects.filter(pk__in=MateriaAsignada.objects.filter(materia__nivel__nivelmalla=nm,materia__nivel__carrera=carrera,materia__nivel__periodo=periodo).distinct('materia__asignatura').values('materia__asignatura'))
                        for a in asignaturas:
                            fila = fila +1
                            columna=0
                            numasig  = numasig+1
                            ws.write(fila,columna+2 , a.nombre)
                            ws.write(fila,columna+1 , numasig)
                            vencido=0

                            for niv in Nivel.objects.filter(pk__in=MateriaAsignada.objects.filter(materia__asignatura=a,materia__nivel__carrera=carrera,materia__nivel__periodo=periodo).distinct('materia__nivel').values('materia__nivel')):
                                for matr in niv.matriculados():
                                    vencido = vencido + matr.inscripcion.adeuda_a_la_fecha()
                                ws.write(fila,columna+3 , (niv.sede.nombre))
                                ws.write(fila,columna+4 , (niv.paralelo))
                                ws.write(fila,columna+5, niv.sesion.nombre)
                                docente = ''
                                lecciones = ''
                                for d in ProfesorMateria.objects.filter(materia__asignatura=a,materia__nivel=niv,materia__nivel__periodo=periodo):
                                    docente = docente + "  " + d.profesor.persona.nombre_completo()
                                    if d.cantidad_lecciones()==None:
                                       lecciones = lecciones
                                    else:
                                        lecciones = lecciones + " " + str(d.cantidad_lecciones())
                                    # lecciones = lecciones + " " + str(d.cantidad_lecciones())

                                ws.write(fila,columna+6, docente)
                                cant = MateriaAsignada.objects.filter(materia__nivel=niv,materia__nivel__periodo=periodo,materia__asignatura=a).count()
                                materia =  MateriaAsignada.objects.filter(materia__nivel=niv,materia__nivel__periodo=periodo,materia__asignatura=a)[:1].get()
                                if materia.materia.cerrado:
                                    estado='CERRADA'
                                else:
                                    estado='ABIERTA'

                                asis = Decimal(((MateriaAsignada.objects.filter(materia__nivel=niv,materia__nivel__periodo=periodo,materia__asignatura=a).aggregate(Sum('asistenciafinal'))['asistenciafinal__sum']) *100)/(cant*100)).quantize(Decimal(10)**-2)
                                ws.write(fila,columna+7, cant)
                                matr = niv.matriculados().count()
                                ws.write(fila,columna+8, matr)
                                becados = niv.matriculados().filter(becado=True).count()
                                ws.write(fila,columna+9, becados)
                                ws.write(fila,columna+10, asis)
                                ws.write(fila,columna+11, lecciones)
                                ws.write(fila,columna+12, estado)
                                ws.write(fila,columna+13,"$"+ str(vencido))
                                ws.write(fila,columna+14, str(materia.materia.inicio))
                                ws.write(fila,columna+15, str(materia.materia.fin))
                                fila= fila +1

                        if not asignaturas:
                            fila = fila +1
                            com=fila
                        print(str(com) +" - " + str(fila))

                        ws.write_merge(com, fila,0,0, nm.nombre , subtitulo)
                        com=fila+1

                    detalle = detalle + fila
                    ws.write(detalle, 0, "Fecha Impresion", subtitulo)
                    ws.write(detalle, 2, str(datetime.now()), subtitulo)
                    detalle=detalle +1
                    ws.write(detalle, 0, "Usuario", subtitulo)
                    ws.write(detalle, 2, str(request.user), subtitulo)

                    nombre ='gestioncarrera'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
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

                    carrera= Carrera.objects.filter(pk=request.POST['carrera'])[:1].get()
                    periodo= Periodo.objects.filter(pk=request.POST['periodo'])[:1].get()
                    malla = Malla.objects.filter(carrera=carrera,vigente=True)[:1].get()
                    nivelesmalla =  NivelMalla.objects.filter(pk__in=AsignaturaMalla.objects.filter(malla=malla).distinct('nivelmalla').values('nivelmalla')).order_by('orden')

                    pdf.ln(30)  # Salto de linea
                    pdf.text(120,30,"MATRIZ DE GESTION - PERIODO " + str(periodo.nombre) )
                    pdf.text(1,35,"CARRERA: "  + str(carrera))
                    fechahoy=datetime.now()
                    fechahoy = fechahoy.strftime('%d/%m/%Y %H:%M:%S%p') # formato dd/mm/yyyy hh:mm:ss am o fm
                    pdf.text(1,50,"Fecha de Impresion: "+ str(fechahoy))
                    pdf.ln(20)  # Salto de linea

                    # para pruebas en desarrollo OCU
                    # locale.setlocale( locale.LC_ALL, '' )

                    # para produccion
                    locale.setlocale( locale.LC_ALL, 'en_US.UTF-8' )

                    # cabecera de la tabla
                    cabecera = ["#","ASIGNATURA","SEDE","GRUPOS","HORARIO","DOCENTE ASIGNADO","#EST.INICIO","#EST.MATRI","#EST.BECA","%ASIST.EST","%ASIST.DOCENTE","ESTADO ASIG","VENCIDOS","INICIO","FIN"]
                    w = [5,30,30,15,35,40,15,15,15,15,15,15,15,10,10]
                    for i in range(0, len(cabecera)):
                        pdf.cell(w[i], 5, cabecera[i], 1, 0, 'C', 0)
                    pdf.ln()

                    for nm in nivelesmalla:
                        numasig=0
                        asignaturas = Asignatura.objects.filter(pk__in=MateriaAsignada.objects.filter(materia__nivel__nivelmalla=nm,materia__nivel__carrera=carrera,materia__nivel__periodo=periodo).distinct('materia__asignatura').values('materia__asignatura'))
                        for a in asignaturas:
                            numasig  = numasig+1
                            pdf.cell(5, 5, str(numasig), 'LR',0,'C')
                            print(a.nombre)
                            pdf.cell(30, 5, str(a.nombre), 'LR',0,'C')
                            vencido=0

                            for niv in Nivel.objects.filter(pk__in=MateriaAsignada.objects.filter(materia__asignatura=a,materia__nivel__carrera=carrera,materia__nivel__periodo=periodo).distinct('materia__nivel').values('materia__nivel')):
                                for matr in niv.matriculados():
                                    vencido = vencido + matr.inscripcion.adeuda_a_la_fecha()
                                pdf.cell(30, 5, str(niv.sede.nombre), 'LR',0,'C')
                                pdf.cell(15, 5, str(niv.paralelo), 'LR',0,'C')
                                pdf.cell(35, 5, str(niv.sesion.nombre), 'LR',0,'C')

                                docente = ''
                                lecciones = ''
                                for d in ProfesorMateria.objects.filter(materia__asignatura=a,materia__nivel=niv,materia__nivel__periodo=periodo):
                                    docente = docente + "  " + d.profesor.persona.nombre_completo()
                                    if d.cantidad_lecciones()==None:
                                       lecciones = lecciones
                                    else:
                                        lecciones = lecciones + " " + str(d.cantidad_lecciones())

                                pdf.cell(40, 5, elimina_tildes(docente), 'LR',0,'C')
                                cant = MateriaAsignada.objects.filter(materia__nivel=niv,materia__nivel__periodo=periodo,materia__asignatura=a).count()
                                materia =  MateriaAsignada.objects.filter(materia__nivel=niv,materia__nivel__periodo=periodo,materia__asignatura=a)[:1].get()
                                if materia.materia.cerrado:
                                    estado='CERRADA'
                                else:
                                    estado='ABIERTA'

                                asis = Decimal(((MateriaAsignada.objects.filter(materia__nivel=niv,materia__nivel__periodo=periodo,materia__asignatura=a).aggregate(Sum('asistenciafinal'))['asistenciafinal__sum']) *100)/(cant*100)).quantize(Decimal(10)**-2)

                                pdf.cell(15, 5, str(cant), 'LR',0,'C')
                                matr = niv.matriculados().count()
                                pdf.cell(15, 5, str(matr), 'LR',0,'C')
                                becados = niv.matriculados().filter(becado=True).count()
                                pdf.cell(15, 5, str(becados), 'LR',0,'C')
                                pdf.cell(15, 5, str(asis), 'LR',0,'C')
                                pdf.cell(15, 5, str(lecciones), 'LR',0,'C')
                                pdf.cell(15, 5, str(estado), 'LR',0,'C')
                                pdf.cell(15, 5, str(vencido), 'LR',0,'C')
                                pdf.cell(10, 5, str(materia.materia.inicio), 'LR',0,'C')
                                pdf.cell(10, 5, str(materia.materia.fin), 'LR',0,'C')
                            pdf.ln()

                    pdf.ln(10)
                    pdf.set_font('Arial','B',12)  # Arial bold 12
                    pdf.set_font('')  # restauro la fuente
                    d = datetime.now()
                    pdfname = 'gestion_carrera' + '_' + d.strftime('%Y%m%d_%H%M%S') + '.pdf'
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
            data = {'title': 'Gestion Carrera'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform']=GestionExcelForm()
                return render(request ,"reportesexcel/gestion_carrera.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

