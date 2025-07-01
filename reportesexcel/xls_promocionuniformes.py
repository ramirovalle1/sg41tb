from datetime import datetime,timedelta
import json
import xlwt

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from settings import MEDIA_ROOT, TIPO_RUBRO_MATERIALAPOYO
from sga.commonviews import addUserData
from sga.forms import RangoFacturasForm
from sga.models import convertir_fecha, TituloInstitucion, ReporteExcel, RubroOtro, RubroInscripcion, DetalleDescuento
from sga.reportes import elimina_tildes
from django.db.models.query_utils import Q

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action :
                inicio = request.POST['inicio']
                fin = request.POST['fin']
                try:
                    fechai = convertir_fecha(inicio)
                    fechaf = convertir_fecha(fin)
                    m = 5
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10
                    style1 = xlwt.easyxf('',num_format_str='DD-MMM-YY')
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('PromoUniformes',cell_overwrite_ok=True)

                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,m+2, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,m+2, 'Listado de Estudiantes pago Inscripcion y Promo Uniformes', titulo2)
                    ws.write(3, 0, 'DESDE', titulo)
                    ws.write(3, 1, str((fechai.date())), titulo)
                    ws.write(4, 0, 'HASTA:', titulo)
                    ws.write(4, 1, str((fechaf.date())), titulo)

                    ws.write(7, 0, 'IDENTIFICACION', titulo)
                    ws.write(7, 1, 'ESTUDIANTE', titulo)
                    ws.write(7, 2, 'INSCRIPCION', titulo)
                    ws.write(7, 3, 'V.PROMOCION', titulo)
                    ws.write(7, 4, 'CARRERA', titulo)
                    ws.write(7, 5, 'FACULTAD', titulo)

                    detalle = 3
                    totalvalorinscripcion = 0
                    totalvalorpromocion = 0
                    fila = 7
                    identificacion=''
                    estudiante = ''
                    valorinscripcion = 0
                    valorpromocion = 0
                    carrera =''
                    facultad=''
                    rubros = RubroInscripcion.objects.filter(Q(rubro__pago__fecha__gte=fechai,rubro__pago__fecha__lte=fechaf,rubro__cancelado=True)|Q(rubro__inscripcion__fecha__gte=fechai,rubro__inscripcion__fecha__lte=fechaf,rubro__cancelado=True)).distinct('rubro__inscripcion__persona__apellido1', 'rubro__inscripcion__persona__apellido2').order_by('rubro__inscripcion__persona__apellido1', 'rubro__inscripcion__persona__apellido2')
                    # for ri in RubroInscripcion.objects.filter(rubro__pago__fecha__gte=fechai,rubro__pago__fecha__lte=fechaf,rubro__cancelado=True).order_by('rubro__inscripcion__persona__apellido1', 'rubro__inscripcion__persona__apellido2'):
                    for ri in rubros:
                    # for ri in RubroInscripcion.objects.filter(rubro__inscripcion__id=99909,rubro__pago__fecha__gte=fechai,rubro__pago__fecha__lte=fechaf,rubro__cancelado=True).order_by('rubro__inscripcion__persona__apellido1', 'rubro__inscripcion__persona__apellido2'):
                        if ri.rubro.inscripcion.promocion:
                            if not ri.rubro.inscripcion.promocion.todos_niveles and ri.rubro.inscripcion.promocion.descuentomaterial and ri.rubro.inscripcion.promocion.valdescuentomaterial > 0:
                                print(ri.rubro.inscripcion)
                                valorinscripcion = 0
                                valorpromocion = 0
                                estudiante = elimina_tildes(ri.rubro.inscripcion.persona.nombre_completo_inverso())
                                carrera=elimina_tildes(ri.rubro.inscripcion.carrera.alias)
                                try:
                                    if ri.rubro.inscripcion.carrera.coordinacion_pertenece():
                                        facultad=elimina_tildes(ri.rubro.inscripcion.carrera.coordinacion_pertenece().nombre)
                                    else:
                                        facultad='SIN FACULTAD'
                                except:
                                    pass
                                try:
                                    if ri.rubro.inscripcion.persona.cedula:
                                        identificacion = elimina_tildes(ri.rubro.inscripcion.persona.cedula)
                                    else:
                                        identificacion = elimina_tildes(ri.rubro.inscripcion.persona.pasaporte)
                                except:
                                    pass
                                valorinscripcion=ri.rubro.valor
                                totalvalorinscripcion=totalvalorinscripcion+valorinscripcion

                                if RubroOtro.objects.filter(tipo__id=TIPO_RUBRO_MATERIALAPOYO,rubro__inscripcion=ri.rubro.inscripcion).exists():
                                    ro=RubroOtro.objects.filter(tipo__id=TIPO_RUBRO_MATERIALAPOYO,rubro__inscripcion=ri.rubro.inscripcion)[:1].get()
                                    if DetalleDescuento.objects.filter(rubro=ro.rubro).exists():
                                        valorpromocion=DetalleDescuento.objects.filter(rubro=ro.rubro)[:1].get()
                                        valorpromocion=valorpromocion.valor
                                        totalvalorpromocion=totalvalorpromocion+valorpromocion

                                fila = fila + 1
                                ws.write(fila, 0, str(identificacion))
                                ws.write(fila, 1, str(estudiante))
                                ws.write(fila, 2, valorinscripcion)
                                ws.write(fila, 3, valorpromocion)
                                ws.write(fila, 4, carrera)
                                ws.write(fila, 5, facultad)
                            else:
                                pass
                        else:
                            pass

                    fila = fila + 1
                    ws.write(fila,0, 'TOTAL',titulo)
                    ws.write(fila,2, totalvalorinscripcion,titulo)
                    ws.write(fila,3, totalvalorpromocion,titulo)
                    fila = fila + 1
                    detalle = detalle + fila
                    ws.write(detalle, 0, "Fecha Impresion", subtitulo)
                    ws.write(detalle, 2, str(datetime.now()), subtitulo)
                    detalle=detalle +1
                    ws.write(detalle, 0, "Usuario", subtitulo)
                    ws.write(detalle, 2, str(request.user), subtitulo)

                    nombre ='promouniformes'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex) + " ")
                    return HttpResponse(json.dumps({"result":str(ex) }),content_type="application/json")
        else:
            data = {'title': 'Listado Promocion Uniformes'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform']=RangoFacturasForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
                return render(request ,"reportesexcel/promocionuniformes.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

