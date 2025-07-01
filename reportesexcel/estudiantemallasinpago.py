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
                    inscritos =Inscripcion.objects.filter().exclude(carrera__id=16).exclude(id__in=Pago.objects.filter().order_by('rubro__inscripcion').distinct().values('rubro__inscripcion'))
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
                    ws.write_merge(1, 1,0,m+2, 'LISTADO DE ESTUDIANTES MALLA COMPLETA SIN PAGOS ', titulo2)
                    ws.write(4, 0,  'CARRERA', titulo)
                    ws.write(4, 1,  'CEDULA', titulo)
                    ws.write(4, 2,  'NOMBRES', titulo)
                    ws.write(4, 3,  'GRUPO', titulo)
                    ws.write(4, 4,  'TIENE DEUDA', titulo)
                    ws.write(4, 5,  'FECHA INSCRIPCION', titulo)
                    # ws.write(4, 6,  'USUARIO INSCRIBE', titulo)

                    fila = 5
                    detalle = 5
                    totmalla=0

                    for insc in inscritos:
                        if insc.mallacompleta():
                            totmalla = totmalla +1
                            if insc.persona.cedula:
                                identificacion=elimina_tildes(insc.persona.cedula)
                            else:
                                identificacion=elimina_tildes(insc.persona.pasaporte)
                            ws.write(fila,0,elimina_tildes(insc.carrera.nombre))
                            ws.write(fila,1,identificacion)
                            ws.write(fila,2, elimina_tildes(insc.persona.nombre_completo()))
                            ws.write(fila,3, elimina_tildes(insc.grupo().nombre))
                            if insc.tiene_deuda_matricula():
                                ws.write(fila,4, insc.total_adeudado(),subtitulo)
                            ws.write(fila,5, elimina_tildes(insc.fecha))
                            # ws.write(fila,6, elimina_tildes(insc.user))

                            fila = fila +1

                    fila = fila + 2

                    ws.write(fila,0, 'TOTAL',subtitulo)
                    ws.write(fila,1, totmalla,subtitulo)

                    detalle = detalle + fila

                    ws.write(detalle, 0, "Fecha Impresion", subtitulo)
                    ws.write(detalle, 2, str(datetime.now()), subtitulo)
                    detalle=detalle +1
                    ws.write(detalle, 0, "Usuario", subtitulo)
                    ws.write(detalle, 2, str(request.user), subtitulo)

                    nombre ='estudiantemallasinpago'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")


        else:
            data = {'title': 'Estudiantes con malla completa sin pagos'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                return render(request ,"reportesexcel/estudiantesinmallapago.html" ,  data)

            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

