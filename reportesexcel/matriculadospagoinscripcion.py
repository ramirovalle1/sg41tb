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
from sga.models import convertir_fecha,TituloInstitucion, PagoPymentez, Rubro, Carrera, SeguimientoGraduado, Graduado, Persona, ReporteExcel, Matricula, PerfilInscripcion, Inscripcion, MONTH_CHOICES, Pago, RubroInscripcion
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
                    ws.write_merge(0, 0,0,7, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,7, 'LISTADO DE ALUMNOS QUE SOLO HAN PAGADO INSCRIPCION ' +str(anio), titulo2)
                    fila=2

                    ws.write(fila, 0,  'FECHA INSCRIPCION', titulo)
                    ws.write(fila, 1,  'ESTUDIANTE', titulo)
                    ws.write(fila, 2,  'FECHA MATRICULA', titulo)
                    ws.write(fila, 3,  'GRUPO', titulo)
                    ws.write(fila, 4,  'NIVEL', titulo)
                    # ws.write(fila, 3,  '%', titulo)
                    # ws.write(fila, 4,  'POR PAGAR', titulo)
                    # ws.write(fila, 5,  '%', titulo)
                    totinscritos = 0
                    totpagado = 0
                    totporpagar = 0
                    meses = MONTH_CHOICES

                    pagado = 0
                    rubros = 0
                    idinscritos = Matricula.objects.filter(inscripcion__persona__usuario__is_active=True, inscripcion__fecha__year=anio).values('inscripcion')
                    idmatriculados = Matricula.objects.filter(inscripcion__persona__usuario__is_active=True, inscripcion__fecha__year=anio).values('id')
                    fila=fila+1
                    pcuota=Pago.objects.filter(rubro__rubrocuota__rubro__inscripcion__id__in=idinscritos).distinct('rubro__inscripcion').values('rubro__inscripcion')
                    pmatricula=Pago.objects.filter(rubro__rubromatricula__rubro__inscripcion__id__in=idinscritos).distinct('rubro__inscripcion').values('rubro__inscripcion')


                    for m in Matricula.objects.filter(inscripcion__id__in=idinscritos).exclude(inscripcion__id__in=pcuota).exclude(inscripcion__id__in=pmatricula).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres').order_by('id'):
                        if (m.becado and m.porcientobeca != 100) or not m.becado:
                            if RubroInscripcion.objects.filter(rubro__inscripcion=m.inscripcion).exists():
                                if RubroInscripcion.objects.filter(rubro__inscripcion=m.inscripcion,rubro__cancelado=True).exists():
                                    # print(m)
                                    ws.write(fila, 0,str(m.inscripcion.fecha))
                                    ws.write(fila, 1,elimina_tildes(m.inscripcion.persona))
                                    ws.write(fila, 2,str(m.fecha))
                                    ws.write(fila, 3,elimina_tildes(m.nivel.paralelo))
                                    ws.write(fila, 4,m.nivel.nivelmalla.nombre)

                                    fila=fila+1

                    nombre ='matriculadospago'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(ex)
                    return HttpResponse(json.dumps({"result":str(ex) }),content_type="application/json")
        else:
            data = {'title': 'Estudiantes Matriculados'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['generarform']=InscritosAnioForm()
                return render(request ,"reportesexcel/matriculadospagoinscripcion.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")
    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))


