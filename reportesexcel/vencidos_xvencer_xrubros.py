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
from settings import UTILIZA_GRUPOS_ALUMNOS, EMAIL_ACTIVE,MEDIA_ROOT, SITE_ROOT,INSCRIPCION_CONDUCCION,TIPO_CONGRESO_RUBRO,TIPO_CUOTA_RUBRO
from sga.commonviews import addUserData, ip_client_address
from sga.forms import MatriculadosporCarreraExcelForm, DistributivoForm
from sga.models import Inscripcion, convertir_fecha, TituloInstitucion, ReporteExcel, Carrera, Matricula, Rubro, \
    RubroMatricula, RubroCuota, RubroOtro, RubroInscripcion, EstudiantesFamiliar
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
                    ws.write_merge(1, 1,0,m+2, 'RESUMEN DE VALORES VENCIDOS Y POR VENCER TOTALIZADOS POR CARRERA Y TIPO DE RUBRO', titulo2)
                    ws.write(4, 0,'Desde:   ' +str(fechai.date()), subtitulo)
                    ws.write(5, 0,'Hasta:   ' +str(fechaf.date()), subtitulo)
                    ws.write(6, 0,  'CARRERA', titulo)
                    ws.write(6, 1,  'MATRICULA', titulo)
                    ws.write(6, 2,  'CUOTA', titulo)
                    ws.write(6, 3,  'CONGRESO', titulo)
                    ws.write(6, 4,  'INSCRIPCION', titulo)
                    ws.write(6, 5,  'OTROS', titulo)
                    ws.write(6, 6,  'POR VENCER MATRICULA', titulo)
                    ws.write(6, 7,  'POR VENCER CUOTA', titulo)
                    ws.write(6, 8,  'POR VENCER CONGRESO', titulo)
                    ws.write(6, 9,  'POR VENCER INSCRIPCION', titulo)
                    ws.write(6, 10,  'POR VENCER OTROS', titulo)
                    detalle = 4
                    fila = 7
                    matri=''
                    from django.db import connection
                    cur = connection.cursor()
                    cur.execute("REFRESH MATERIALIZED VIEW estudiantesfamiliar;")
                    try:
                        connection.commit()
                    except Exception as e:
                        print("Error al actualizar la vista materializada estudiantesfamiliar:", str(e))
                        connection.rollback()
                    if INSCRIPCION_CONDUCCION:
                        carreras=Carrera.objects.filter(activo=True).order_by('nombre')
                    else:
                        # carreras=Carrera.objects.filter(pk=21,carrera=True,activo=True).order_by('nombre')
                        carreras=Carrera.objects.filter(carrera=True,activo=True).order_by('nombre')

                    for carrera in carreras:
                        print(elimina_tildes(carrera.nombre))
                        total_vencido_xcarrera = 0
                        totalmatrixcarrera=0
                        totalcuotaxcarrera=0
                        totalcongresoxcarrera=0
                        totalinscripcionxcarrera=0
                        totalotrosxcarrera=0
                        totalxvencer_matriculaxcarrera=0
                        totalxvencer_cuotaaxcarrera=0
                        totalxvencer_congresoxcarrera=0
                        totalxvencer_inscripcionxcarrera=0
                        totalxvencer_otrosrubrosxcarrera=0

                        matriculados1 = Matricula.objects.filter(inscripcion__persona__usuario__is_active=True,nivel__carrera=carrera,fecha__gte=fechai,fecha__lte=fechaf).select_related('nivel__carrera').order_by('inscripcion').distinct().values('inscripcion')
                        # matriculados1 = Matricula.objects.filter(inscripcion__id=47410, inscripcion__persona__usuario__is_active=True,nivel__carrera=carrera,fecha__gte=fechai,fecha__lte=fechaf).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2').distinct('inscripcion').values('inscripcion')
                        # matriculados = Inscripcion.objects.filter(pk__in=matriculados1)
                        matriculados = EstudiantesFamiliar.objects.filter(inscripcion_id__in=matriculados1)

                        fechafin =  datetime(fechaf.year, 12, 31).date()
                        for matric in matriculados:
                            vencido_xcarrera=0
                            xvencer_xcarrera=0
                            matriculaxcarrera=0
                            cuotaxcarrera=0
                            congresoxcarrera=0
                            inscripcionxcarrera=0
                            otrosxcarrera=0
                            xvencer_matriculaxcarrera=0
                            xvencer_cuotaxcarrera=0
                            xvencer_congresoxcarrera=0
                            xvencer_inscripcionxcarrera=0
                            xvencer_otrosrubrosxcarrera=0

                            # print(matric)

                            matri =Matricula.objects.filter(inscripcion=matric.inscripcion_id).select_related('inscripcion').order_by('-id')[:1].get()
                            if not matri.absentismo() and not matri.esta_retirado():

                                # Rubro tipo matricula
                                rubromatricula = RubroMatricula.objects.filter(matricula=matri,rubro__cancelado=False,rubro__fecha__gte=fechai,rubro__fecha__lte=fechaf,rubro__fechavence__lte=fechaf).select_related('rubro')
                                if rubromatricula:
                                    rm= rubromatricula.filter()[:1].get()
                                    rmdeuda =rm.rubro.adeudado()
                                    if rmdeuda>0:
                                        matriculaxcarrera+=rmdeuda

                                # Rubro tipo cuota
                                rubrocuota =RubroCuota.objects.filter(matricula=matri,rubro__cancelado=False,rubro__fecha__gte=fechai,rubro__fecha__lte=fechaf,rubro__fechavence__lte=fechaf).select_related('rubro')
                                if rubrocuota:
                                    for rc in rubrocuota:
                                        rcdeuda=rc.rubro.adeudado()
                                        if rcdeuda>0:
                                            cuotaxcarrera+=rcdeuda
                                matriculainscripcion = matri.inscripcion
                                # Rubro tipo congreso
                                rubrocongreso =RubroOtro.objects.filter(rubro__inscripcion=matriculainscripcion,tipo__id=TIPO_CONGRESO_RUBRO,rubro__cancelado=False,rubro__fecha__gte=fechai,rubro__fecha__lte=fechaf,rubro__fechavence__lte=fechaf).select_related('rubro')
                                if rubrocongreso:
                                    for rcong in rubrocongreso:
                                        rcongdeuda =rcong.rubro.adeudado()
                                        if rcongdeuda>0:
                                           congresoxcarrera+=rcongdeuda

                                # Rubro tipo inscripcion
                                rubroinscripcion=RubroInscripcion.objects.filter(rubro__inscripcion=matriculainscripcion,rubro__cancelado=False,rubro__fecha__gte=fechai,rubro__fecha__lte=fechaf,rubro__fechavence__lte=fechaf).select_related('rubro')
                                if rubroinscripcion:
                                    for rinscrip in rubroinscripcion:
                                        rinscripdeuda=rinscrip.rubro.adeudado()
                                        if rinscripdeuda>0:
                                           inscripcionxcarrera+=rinscripdeuda

                                # Otros rubros excluye congreso
                                otrorubros =RubroOtro.objects.filter(rubro__inscripcion=matriculainscripcion,rubro__cancelado=False,rubro__fecha__gte=fechai,rubro__fecha__lte=fechaf,rubro__fechavence__lte=fechaf).exclude(tipo__id=TIPO_CONGRESO_RUBRO).select_related('rubro')
                                if otrorubros:
                                      for rotro in otrorubros:
                                          rotrodeuda =rotro.rubro.adeudado()
                                          if rotrodeuda >0:
                                              otrosxcarrera+= rotrodeuda

                                # Rubros por vencer
                                # Rubros por vencer tipo matricula
                                rubromatriculavence =RubroMatricula.objects.filter(matricula=matri,rubro__cancelado=False,rubro__fecha__gte=fechai,rubro__fecha__lte=fechaf,rubro__fechavence__gt=fechaf,rubro__fechavence__lte=fechafin).select_related('rubro')
                                if rubromatriculavence:
                                    rm=rubromatriculavence.filter()[:1].get()
                                    rm2deuda =rm.rubro.adeudado()
                                    if rm2deuda >0:
                                        xvencer_matriculaxcarrera+=rm2deuda

                                # Rubros por vencer tipo cuota
                                rubrocuotavence= RubroCuota.objects.filter(matricula=matri, rubro__cancelado=False,rubro__fecha__gte=fechai,rubro__fecha__lte=fechaf,rubro__fechavence__gt=fechaf,rubro__fechavence__lte=fechafin).select_related('rubro')
                                if rubrocuotavence:
                                    for rc in rubrocuotavence:
                                        rc2deuda =rc.rubro.adeudado()
                                        if rc2deuda>0:
                                            xvencer_cuotaxcarrera+=rc2deuda

                                # Rubro por vencer tipo congreso
                                rubrocongresovence=RubroOtro.objects.filter(rubro__inscripcion=matriculainscripcion,tipo__id=TIPO_CONGRESO_RUBRO,rubro__cancelado=False,rubro__fecha__gte=fechai,rubro__fecha__lte=fechaf,rubro__fechavence__gt=fechaf,rubro__fechavence__lte=fechafin).select_related('rubro')
                                if rubrocongresovence:
                                    for rcong in rubrocongresovence:
                                        rcong2deuda =rcong.rubro.adeudado()
                                        if rcong2deuda>0:
                                           xvencer_congresoxcarrera+=rcong2deuda

                                # Rubro por vencer tipo inscripcion
                                rubroinscripcionvence =RubroInscripcion.objects.filter(rubro__inscripcion=matriculainscripcion,rubro__cancelado=False,rubro__fecha__gte=fechai,rubro__fecha__lte=fechaf,rubro__fechavence__gt=fechaf,rubro__fechavence__lte=fechafin).select_related('rubro')
                                if rubroinscripcionvence:
                                    for rinscrip in rubroinscripcionvence:
                                        rinscrip2deuda =rinscrip.rubro.adeudado()
                                        if rinscrip2deuda>0:
                                           xvencer_inscripcionxcarrera+=rinscrip2deuda

                                # Otros rubros por vencer excluye congreso
                                otrorubrosvence =RubroOtro.objects.filter(rubro__inscripcion=matriculainscripcion,rubro__cancelado=False,rubro__fecha__gte=fechai,rubro__fecha__lte=fechaf,rubro__fechavence__gt=fechaf,rubro__fechavence__lte=fechafin).exclude(tipo__id=TIPO_CONGRESO_RUBRO).select_related('rubro')
                                if otrorubrosvence:
                                      for rotro in otrorubrosvence:
                                          rotro2deuda=rotro.rubro.adeudado()
                                          if rotro2deuda>0:
                                              xvencer_otrosrubrosxcarrera+=rotro2deuda

                            total_vencido_xcarrera += vencido_xcarrera
                            totalmatrixcarrera += matriculaxcarrera
                            totalcuotaxcarrera += cuotaxcarrera
                            totalcongresoxcarrera += congresoxcarrera
                            totalinscripcionxcarrera += inscripcionxcarrera
                            totalotrosxcarrera += otrosxcarrera
                            totalxvencer_matriculaxcarrera+= xvencer_matriculaxcarrera
                            totalxvencer_cuotaaxcarrera+= xvencer_cuotaxcarrera
                            totalxvencer_congresoxcarrera+= xvencer_congresoxcarrera
                            totalxvencer_inscripcionxcarrera+= xvencer_inscripcionxcarrera
                            totalxvencer_otrosrubrosxcarrera+= xvencer_otrosrubrosxcarrera

                        ws.write(fila,0, elimina_tildes(carrera.nombre))
                        ws.write(fila,1, totalmatrixcarrera)
                        ws.write(fila,2, totalcuotaxcarrera)
                        ws.write(fila,3, totalcongresoxcarrera)
                        ws.write(fila,4, totalinscripcionxcarrera)
                        ws.write(fila,5, totalotrosxcarrera)
                        ws.write(fila,6, totalxvencer_matriculaxcarrera)
                        ws.write(fila,7, totalxvencer_cuotaaxcarrera)
                        ws.write(fila,8, totalxvencer_congresoxcarrera)
                        ws.write(fila,9, totalxvencer_inscripcionxcarrera)
                        ws.write(fila,10, totalxvencer_otrosrubrosxcarrera)
                        fila=fila + 1

                    detalle = detalle + fila
                    ws.write(detalle, 0, "Fecha Impresion", subtitulo)
                    ws.write(detalle, 1, str(datetime.now()), subtitulo)
                    detalle=detalle +1
                    ws.write(detalle, 0, "Usuario", subtitulo)
                    ws.write(detalle, 1, str(request.user), subtitulo)

                    nombre ='valoresxrubros'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(ex)
                    return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")

        else:
            data = {'title': 'Valores Vencidos y por Vencer Totalizados por Carrera y Tipo de Rubros'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform']=DistributivoForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
            return render(request ,"reportesexcel/vencidos_xvencer_xrubros.html" ,  data)

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

