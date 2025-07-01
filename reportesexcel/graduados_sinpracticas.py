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
from settings import UTILIZA_GRUPOS_ALUMNOS, EMAIL_ACTIVE,MEDIA_ROOT, ASIG_VINCULACION, ASIG_PRATICA,JR_USEROUTPUT_FOLDER,MEDIA_URL, SITE_ROOT, HORAS_VINCULACION, HORAS_PRACTICA,CONSUMIDOR_FINAL
from sga.commonviews import addUserData, ip_client_address
from sga.forms import RangoFacturasForm,RangoNCForm, VinculacionExcelForm
from sga.models import Inscripcion,convertir_fecha,Factura,ClienteFactura,TituloInstitucion,ReporteExcel,NotaCreditoInstitucion, Persona,TipoNotaCredito, Carrera, Matricula, RecordAcademico, RetiradoMatricula, EstudianteVinculacion, Graduado, Tutoria, Pago
from sga.reportes import elimina_tildes
from fpdf import FPDF

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    """

    :param request:
    :return:
    """
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action =='generarexcel':
                try:
                    # inscritos = Inscripcion.objects.filter(Q(pk=19741,carrera__carrera=True,carrera__id=4,persona__usuario__is_active=True,graduado=None,egresado=None,retiradomatricula=None)|Q(pk=19741,carrera__carrera=True,carrera__id=4,persona__usuario__is_active=True,graduado=None,egresado=None,retiradomatricula__activo=False)).exclude(pk=23498).order_by('carrera__nombre')
                    graduados = Graduado.objects.filter().order_by('inscripcion__carrera__nombre','inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')
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
                    ws.write_merge(1, 1,0,m+2, 'LISTADO DE ESTUDIANTES SIN HORAS DE VINCULACION Y PRACTICAS ', titulo2)
                    ws.write(4, 0,  'CARRERA', titulo)
                    ws.write(4, 1,  'CEDULA', titulo)
                    ws.write(4, 2,  'NOMBRES', titulo)
                    ws.write(4, 3,  'GRUPO', titulo)
                    ws.write(4, 4,  'PRACTICAS', titulo)
                    ws.write(4, 5,  'TUTORIAS', titulo)
                    ws.write(4, 6,  'PAGOS', titulo)
                    ws.write(4, 7,  'TIENE DEUDA', titulo)
                    ws.write(4, 8,  'ADEUDADO', titulo)
                    ws.write(4, 9,  'VINCULACION', titulo)

                    fila = 5
                    detalle = 5
                    totnopractica=0
                    totnotutoria=0
                    totnopago=0
                    tottienedeuda=0
                    totnovinc=0

                    for g in graduados:
                        # print(insc)
                        insc = g.inscripcion

                        practica=None
                        tutoria=None
                        pagos = None
                        tienedeuda = None
                        vinculacion = None
                        adeudado = 0

                        columna=0

                        if not RecordAcademico.objects.filter(asignatura__id=ASIG_PRATICA,aprobada=True,inscripcion=insc).exists():
                            practica = 'NO TIENE PRACTICA'
                            totnopractica = totnopractica +1

                        if not RecordAcademico.objects.filter(asignatura__id=ASIG_VINCULACION,aprobada=True,inscripcion=insc).exists():
                            vinculacion = 'NO TIENE VINCULACION'
                            totnovinc = totnovinc +1

                        if not Tutoria.objects.filter(estudiante=insc).exists():
                            tutoria = 'NO TIENE TUTORIAS'
                            totnotutoria = totnotutoria +1

                        if not Pago.objects.filter(rubro__inscripcion=insc).exists():
                            pagos = 'NO TIENE PAGOS'
                            totnopago = totnopago +1
                        if insc.tiene_deuda_matricula():
                           tienedeuda = True
                           adeudado = insc.total_adeudado()
                           totnopago = totnopago +1

                        if (pagos or  tutoria or practica or tienedeuda or vinculacion):
                             if insc.persona.cedula:
                                identificacion=elimina_tildes(insc.persona.cedula)
                             else:
                                identificacion=elimina_tildes(insc.persona.pasaporte)
                             ws.write(fila,0,elimina_tildes(insc.carrera.nombre))
                             ws.write(fila,1,identificacion)
                             ws.write(fila,2, elimina_tildes(insc.persona.nombre_completo_inverso()))
                             ws.write(fila,3, elimina_tildes(insc.grupo().nombre))
                             if practica:
                                ws.write(fila,4, 'NO TIENE PRACTICA')
                             if tutoria:
                                ws.write(fila,5, 'NO TIENE TUTORIAS')

                             if pagos:
                                ws.write(fila,6, 'NO TIENE PAGOS')

                             if tienedeuda:
                                ws.write(fila,7, 'TIENE DEUDA')
                                ws.write(fila,8, adeudado)
                                tottienedeuda=tottienedeuda+1

                             if vinculacion:
                                ws.write(fila,9, 'NO TIENE VINCULACION')
                             fila = fila +1

                    fila = fila + 2
                    ws.write(fila,0, 'TOTAL SIN PRACTICAS',subtitulo)
                    ws.write(fila,1, totnopractica,subtitulo)
                    ws.write(fila+1,0, 'TOTAL SIN TUTORIAS',subtitulo)
                    ws.write(fila+1,1, totnotutoria,subtitulo)
                    ws.write(fila+2,0, 'TOTAL SIN PAGOS',subtitulo)
                    ws.write(fila+2,1, totnopago,subtitulo)
                    ws.write(fila+3,0, 'TOTAL CON DEUDA',subtitulo)
                    ws.write(fila+3,1, tottienedeuda,subtitulo)
                    ws.write(fila+4,0, 'TOTAL SIN VINCULACION',subtitulo)
                    ws.write(fila+4,1, totnovinc,subtitulo)

                    detalle = detalle + fila

                    ws.write(detalle, 0, "Fecha Impresion", subtitulo)
                    ws.write(detalle, 2, str(datetime.now()), subtitulo)
                    detalle=detalle +1
                    ws.write(detalle, 0, "Usuario", subtitulo)
                    ws.write(detalle, 2, str(request.user), subtitulo)

                    nombre ='graduadossinpracticas'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")


        else:
            data = {'title': 'Listado Graduados sin Practicas'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                return render(request ,"reportesexcel/graduadosinpractica.html" ,  data)

            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

