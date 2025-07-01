from datetime import datetime, timedelta
import json
from django.db.models import Sum
import xlwt
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from settings import MEDIA_ROOT
from sga.commonviews import addUserData
from sga.forms import InscritosAnioForm
from sga.models import convertir_fecha,TituloInstitucion, PagoPymentez, Rubro, Carrera, SeguimientoGraduado, Graduado, Persona, ReporteExcel, Matricula, PerfilInscripcion, Inscripcion, MONTH_CHOICES, Pago
from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action :
                try:
                    anio = request.POST['anio']
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('Listado',cell_overwrite_ok=True)

                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,5, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,5, 'TOTALES DE ALUMNOS INSCRITOS ' +str(anio), titulo2)
                    fila=2

                    ws.write(fila, 0,  'MES', titulo)
                    ws.write(fila, 1,  'INSCRITOS', titulo)
                    ws.write(fila, 2,  'PAGADO A LA FECHA', titulo)
                    ws.write(fila, 3,  '%', titulo)
                    ws.write(fila, 4,  'POR PAGAR', titulo)
                    ws.write(fila, 5,  '%', titulo)
                    totinscritos = 0
                    totpagado = 0
                    totporpagar = 0
                    meses = MONTH_CHOICES
                    for m in meses:
                        pagado = 0
                        rubros = 0
                        if Inscripcion.objects.filter(persona__usuario__is_active=True, fecha__year=anio,fecha__month=m[0]).order_by('carrera','persona__canton','persona__parroquia','persona__apellido1','persona__apellido2').exists():
                            fila=fila+1
                            inscritos = Inscripcion.objects.filter(persona__usuario__is_active=True, fecha__year=anio,fecha__month=m[0]).order_by('carrera','persona__canton','persona__parroquia','persona__apellido1','persona__apellido2')
                            idinscritos = Inscripcion.objects.filter(persona__usuario__is_active=True, fecha__year=anio,fecha__month=m[0]).values('id')
                            totinscritos =totinscritos +  inscritos.count()
                            if Pago.objects.filter(rubro__inscripcion__id__in=idinscritos).exists():
                                pagado = Pago.objects.filter(rubro__inscripcion__id__in=idinscritos).aggregate(Sum('valor'))['valor__sum']
                            totpagado =totpagado +  pagado
                            if Rubro.objects.filter(inscripcion__id__in=idinscritos).exists():
                                rubros = Rubro.objects.filter(inscripcion__id__in=idinscritos).aggregate(Sum('valor'))['valor__sum']
                            porpagar = rubros - pagado
                            porpagado = round(((pagado*100) / rubros),2)
                            porxpagar = round(((porpagar*100) / rubros),2)
                            totporpagar = totporpagar + porpagar


                            ws.write(fila, 0, m[1])
                            ws.write(fila, 1,inscritos.count())
                            ws.write(fila, 2,pagado)
                            ws.write(fila, 3,porpagado)
                            ws.write(fila, 4,porpagar)
                            ws.write(fila, 5,porxpagar)
                    fila=fila+1
                    ws.write(fila, 0, "TOTALES",titulo2)
                    ws.write(fila, 1, totinscritos,titulo2)
                    ws.write(fila, 2, totpagado,titulo2 )
                    ws.write(fila, 4, totporpagar,titulo2 )



                    nombre ='totalinscritosxanio'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(ex)
                    return HttpResponse(json.dumps({"result":str(ex) }),content_type="application/json")
        else:
            data = {'title': 'Total Inscritos'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['generarform']=InscritosAnioForm()
                return render(request ,"reportesexcel/inscritosporanio.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")
    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))


