from datetime import datetime,timedelta
import json
import xlrd
import xlwt
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
from settings import UTILIZA_GRUPOS_ALUMNOS, EMAIL_ACTIVE,MEDIA_ROOT, SITE_ROOT,INSCRIPCION_CONDUCCION
from sga.commonviews import addUserData, ip_client_address
from sga.forms import MatriculadosporCarreraExcelForm, DistributivoForm
from sga.models import Inscripcion,convertir_fecha,TituloInstitucion,ReporteExcel,Carrera,Matricula,Rubro
from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):

    try:
        if request.method=='POST':
            action = request.POST['action']
            if action :
                try:
                    desde = request.POST['desde']
                    hasta = request.POST['hasta']
                    fechai = convertir_fecha(desde)
                    fechaf = convertir_fecha(hasta)
                    m = 8
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10
                    style1 = xlwt.easyxf('',num_format_str='DD-MMM-YY')
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('Informacion',cell_overwrite_ok=True)
                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,m+2, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,m+2, 'RESUMEN DE VALORES VENCIDOS Y POR VENCER DE ESTUDIANTES TOTALIZADOS POR CARRERA', titulo2)
                    ws.write(4, 0,'Desde:   ' +str(fechai.date()), subtitulo)
                    ws.write(5, 0,'Hasta:   ' +str(fechaf.date()), subtitulo)

                    ws.write(6, 0,  'CARRERA', titulo)
                    ws.write(6, 1,  'VENCIDOS', titulo)
                    ws.write(6, 2,  'POR VENCER', titulo)

                    detalle = 4
                    fila = 7

                    matri=''
                    total_carrera=0
                    total_vencido_xcarrera=0
                    total_xvencer_xcarrera=0
                    vencido_xcarrera=0
                    xvencer_xcarrera=0

                    if INSCRIPCION_CONDUCCION:
                        carreras=Carrera.objects.filter(activo=True).order_by('nombre')
                    else:
                        carreras=Carrera.objects.filter(carrera=True,activo=True).order_by('nombre')

                    for carrera in carreras:
                        # print(elimina_tildes(carrera.nombre))
                        total_vencido_xcarrera = 0
                        total_xvencer_xcarrera = 0

                        matriculados1 = Matricula.objects.filter(inscripcion__persona__usuario__is_active=True,nivel__carrera=carrera,fecha__gte=fechai,fecha__lte=fechaf).order_by('inscripcion').distinct().values('inscripcion')
                        matriculados = Inscripcion.objects.filter(pk__in=matriculados1)

                        fechafin =  datetime(fechaf.year, 12, 31).date()
                        for matric in matriculados:
                            vencido_xcarrera=0
                            xvencer_xcarrera=0
                            # print(matric.id)
                            matri =Matricula.objects.filter(inscripcion=matric).order_by('-id')[:1].get()
                            if not matri.absentismo() and not matri.esta_retirado():
                                if Rubro.objects.filter(inscripcion=matri.inscripcion,cancelado=False,fecha__gte=fechai,fecha__lte=fechaf,fechavence__lte=fechaf).exists():
                                    for deudavencida in Rubro.objects.filter(inscripcion=matri.inscripcion,cancelado=False,fecha__gte=fechai,fecha__lte=fechaf,fechavence__lte=fechaf):
                                        if deudavencida.adeudado()>0:
                                            vencido_xcarrera+=deudavencida.adeudado()

                                if Rubro.objects.filter(inscripcion=matri.inscripcion,cancelado=False,fecha__gte=fechai,fecha__lte=fechaf,fechavence__gt=fechaf,fechavence__lte=fechafin).exists():
                                    for deudaxvencer in Rubro.objects.filter(inscripcion=matri.inscripcion,cancelado=False,fecha__gte=fechai,fecha__lte=fechaf,fechavence__gt=fechaf,fechavence__lte=fechafin):
                                        if deudaxvencer.adeudado()>0:
                                            xvencer_xcarrera+=deudaxvencer.adeudado()

                            total_vencido_xcarrera += vencido_xcarrera
                            total_xvencer_xcarrera += xvencer_xcarrera

                        ws.write(fila,0, elimina_tildes(carrera.nombre))
                        ws.write(fila,1, total_vencido_xcarrera)
                        ws.write(fila,2, total_xvencer_xcarrera)

                        fila=fila + 1

                    detalle = detalle + fila
                    ws.write(detalle, 0, "Fecha Impresion", subtitulo)
                    ws.write(detalle, 1, str(datetime.now()), subtitulo)
                    detalle=detalle +1
                    ws.write(detalle, 0, "Usuario", subtitulo)
                    ws.write(detalle, 1, str(request.user), subtitulo)

                    nombre ='vencidos_xvencer'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(ex)
                    return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")

        else:
            data = {'title': 'Valor Vencidos y por Vencer Totalizados por Carrera'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform']=DistributivoForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
            return render(request ,"reportesexcel/vencimiento_xvencer_estudiantes.html" ,  data)

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

