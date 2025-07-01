from datetime import datetime,timedelta, date
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
def calculaedad(fecha,fechai):
    a= int(fecha.year)
    m=int(fecha.month)
    d=int(fecha.day)

    mm = fechai.month - 1
    if mm == 0:
        mm = 1
    fecha = date(a,m,d)

    if int(fecha.month) > fechai.month:
        anios =(fechai.year - (fecha).year)-1
    else:
        if m == fechai.month and d > fechai.day :
            anios =(fechai.year - (fecha).year) -1

        else:
            anios =(fechai.year - (fecha).year)
    if m >= fechai.month:

        if m > fechai.month:
            meses =  fecha.month - fechai.month
            meses =  12 - meses
        else:
            if d <= fechai.day :
                meses = 0
            else:
                meses = 11

    else:
        meses = (fechai.month -  fecha.month)-1

    if  m == fechai.month  and d <= fechai.day:
        mm = fechai.month

    fechanueva =date( fechai.year,mm,int(fecha.day))

    dia = (date(fechai.year,fechai.month+1,1) +timedelta(-1)).day -  (fechanueva - fechai).days
    if dia < 0:
        dia = dia * -1
    if dia >= (date(fechai.year,fechai.month+1,1) +timedelta(-1)).day :
        if dia > (date(fechai.year,fechai.month+1,1) +timedelta(-1)).day:
            dia = dia -(date(fechai.year,fechai.month+1,1) +timedelta(-1)).day
        else:
            dia=0
    return (str(anios)+',' +str(meses) + ',')

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
                    inscritos =Inscripcion.objects.filter(persona__usuario__is_active=True).exclude(carrera__id=16).exclude(recordacademico__aprobada=False)
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
                    ws.write_merge(1, 1,0,m+2, 'LISTADO DE ESTUDIANTES MALLA COMPLETA(NO HA PASADO EL TIEMPO DE SU CARRERA) ', titulo2)
                    ws.write(4, 0,  'CARRERA', titulo)
                    ws.write(4, 1,  'CEDULA', titulo)
                    ws.write(4, 2,  'NOMBRES', titulo)
                    ws.write(4, 3,  'GRUPO', titulo)
                    ws.write(4, 4,  'DEUDA', titulo)
                    ws.write(4, 5,  'FECHA INSCRIPCION', titulo)
                    ws.write(4, 6,  'FECHA HISTORICO', titulo)
                    ws.write(4, 7,  'TIEMPO', titulo)

                    fila = 5
                    detalle = 5
                    totmalla=0

                    for insc in inscritos:
                        if insc.mallacompleta():
                            record = RecordAcademico.objects.filter(inscripcion=insc).order_by('-fecha')[:1].get()
                            fecha = record.fecha
                            try:
                                # tiempo = calculaedad(insc.fecha,fecha)
                                tiempo = (fecha - insc.fecha).days
                                if tiempo <= 912:
                                # if insc.fecha - fecha
                                    totmalla = totmalla +1
                                    print(round(float(float(tiempo) /365),1))
                                    if insc.persona.cedula:
                                        identificacion=elimina_tildes(insc.persona.cedula)
                                    else:
                                        identificacion=elimina_tildes(insc.persona.pasaporte)
                                    ws.write(fila,0,elimina_tildes(insc.carrera.nombre))
                                    ws.write(fila,1,identificacion)
                                    ws.write(fila,2, elimina_tildes(insc.persona.nombre_completo()))
                                    ws.write(fila,3, elimina_tildes(insc.grupo().nombre))
                                    if insc.tiene_deuda_matricula():
                                        ws.write(fila,4, insc.total_adeudado())
                                    ws.write(fila,5, str(insc.fecha) )
                                    ws.write(fila,6, str(fecha) )
                                    ws.write(fila,7, (round(float(float(tiempo) /365),1))  )

                                    fila = fila +1
                            except Exception as e:
                                pass


                    fila = fila + 2

                    ws.write(fila,0, 'TOTAL',subtitulo)
                    ws.write(fila,1, totmalla,subtitulo)

                    detalle = detalle + fila

                    ws.write(detalle, 0, "Fecha Impresion", subtitulo)
                    ws.write(detalle, 2, str(datetime.now()), subtitulo)
                    detalle=detalle +1
                    ws.write(detalle, 0, "Usuario", subtitulo)
                    ws.write(detalle, 2, str(request.user), subtitulo)

                    nombre ='mallacompleta'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")


        else:
            data = {'title': 'Estudiantes con malla completa '}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                return render(request ,"reportesexcel/mallacompletaconsulta.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

