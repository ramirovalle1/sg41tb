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
from sga.models import Inscripcion, convertir_fecha, Factura, ClienteFactura, TituloInstitucion, ReporteExcel, \
    NotaCreditoInstitucion, Persona, TipoNotaCredito, Carrera, Matricula, RecordAcademico, RetiradoMatricula, \
    EstudianteVinculacion, Graduado, Egresado, InscripcionPracticas
from sga.reportes import elimina_tildes
from fpdf import FPDF

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action =='generarexcel':
                try:
                    carrera = Carrera.objects.filter(pk=request.POST['carrera'])[:1].get()
                    # inscritos = Inscripcion.objects.filter(Q(pk=19741,carrera__carrera=True,carrera__id=4,persona__usuario__is_active=True,graduado=None,egresado=None,retiradomatricula=None)|Q(pk=19741,carrera__carrera=True,carrera__id=4,persona__usuario__is_active=True,graduado=None,egresado=None,retiradomatricula__activo=False)).exclude(pk=23498).order_by('carrera__nombre')
                    matricula = Matricula.objects.filter(nivel__carrera__carrera=True,nivel__cerrado=False).select_related('inscripcion').values('inscripcion')
                    inscritos = Inscripcion.objects.filter(Q(retiradomatricula__activo=False)|Q(retiradomatricula=None),persona__usuario__is_active=True,carrera__carrera=True,graduado=None,egresado=None,pk__in=matricula, carrera = carrera).exclude(pk=CONSUMIDOR_FINAL).order_by('carrera__nombre','persona__apellido1','persona__apellido2','persona__nombres')
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
                    ws.write(4, 4,  'NIVEL', titulo)
                    ws.write(4, 5,  'HORAS PRACTICA', titulo)
                    ws.write(4, 6,  'HORAS VINCULACION', titulo)

                    fila = 4
                    detalle = 3

                    print(inscritos.count())
                    for insc in inscritos:
                        # print(insc)
                        vinculacion=''
                        practica=''
                        identificacion=''
                        h_vincula = 0
                        h_practica = 0
                        columna=0
                        estudiantevin =EstudianteVinculacion.objects.filter(inscripcion = insc).select_related('inscripcion')
                        if estudiantevin:
                            h_vinculan = estudiantevin.filter().aggregate(Sum('horas'))['horas__sum']
                            if h_vinculan < HORAS_VINCULACION:
                                h_vincula = h_vinculan
                            else:
                                h_vincula= h_vinculan
                        else:
                            vinculacion='NO TIENE VINCULACION'

                        estudianteprac = InscripcionPracticas.objects.filter(inscripcion= insc).select_related('inscripcion')
                        if estudianteprac:
                            insc_pract=  estudianteprac.filter().aggregate(Sum('horas'))['horas__sum']
                            if insc_pract < HORAS_PRACTICA:
                                h_practica = insc_pract
                            else:
                                h_practica = insc_pract
                        else:
                            practica = 'NO TIENE PRACTICA'
                        ################  ANTES  ############################
                        # tiene_vinculacion = insc.tiene_actvinculacion()
                        # if tiene_vinculacion:
                        #     insc_vinculacion =insc.horas_vinculacion()
                        #     if insc_vinculacion < HORAS_VINCULACION :
                        #         h_vincula=insc_vinculacion
                        #     else:
                        #         h_vincula=insc.horas_vinculacion()
                        # else:
                        #     vinculacion='NO TIENE VINCULACION'
                        #
                        # if insc.tiene_practicas():
                        #     if insc.horas_practicas()< HORAS_PRACTICA :
                        #         h_practica=insc.horas_practicas()
                        #     else:
                        #         h_practica=insc.horas_practicas()
                        # else:
                        #     practica='NO TIENE PRACTICA'

                        if insc.persona.cedula:
                            identificacion=str(insc.persona.cedula)
                        else:
                            identificacion=str(insc.persona.pasaporte)
                        inscri_matri = insc.matricula()
                        if inscri_matri:
                            nivel = inscri_matri.nivel.nivelmalla.nombre
                        else:
                            nivel = 'NO ESTA MATRICULADO'
                        if (h_vincula+h_practica)<(HORAS_PRACTICA+HORAS_VINCULACION):
                            fila = fila +1
                            ws.write(fila,columna, elimina_tildes(insc.carrera.nombre))
                            ws.write(fila,columna+1,  identificacion)
                            ws.write(fila,columna+2, elimina_tildes(insc.persona.nombre_completo_inverso()))
                            insc_grupo = insc.grupo()
                            if insc_grupo!=None:
                                ws.write(fila,columna+3, elimina_tildes(insc_grupo.nombre))
                            else:
                                ws.write(fila,columna+3, 'NO TIENE GRUPO')
                            ws.write(fila,columna+4, elimina_tildes(nivel))

                            if h_practica==0:
                                ws.write(fila,columna+5, practica)
                            else:
                                 ws.write(fila,columna+5,str(h_practica))

                            if h_vincula==0:
                                ws.write(fila,columna+6, vinculacion)
                            else:
                                ws.write(fila,columna+6,  str(h_vincula))

                    detalle = detalle + fila
                    ws.write(detalle, 0, "Fecha Impresion", subtitulo)
                    ws.write(detalle, 2, str(datetime.now()), subtitulo)
                    detalle=detalle +1
                    ws.write(detalle, 0, "Usuario", subtitulo)
                    ws.write(detalle, 2, str(request.user), subtitulo)

                    nombre ='sinvinculacion_sinpractica'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")


        else:
            data = {'title': 'Listado Estudiantes sin Horas Vinculacion y Practicas'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['generarform']=VinculacionExcelForm
                data['reportes'] = reportes
                return render(request ,"reportesexcel/sinvinculacion_sinpracticas_general.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

