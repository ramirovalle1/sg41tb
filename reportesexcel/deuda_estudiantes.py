from datetime import datetime, timedelta
import json
import xlwt
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from settings import MEDIA_ROOT
from sga.commonviews import addUserData
from sga.forms import RangoFacturasForm
from sga.models import convertir_fecha,TituloInstitucion, PagoPymentez, Rubro, Canton, Inscripcion, Matricula, Provincia, ReporteExcel
from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action :
                try:
                    inicio = request.POST['inicio']
                    fin = request.POST['fin']
                    fechai = convertir_fecha(inicio)
                    fechaf = convertir_fecha(fin)+timedelta(hours=23,minutes=59)
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('Listado',cell_overwrite_ok=True)

                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,9, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,9, 'DEUDA DE ESTUDIANTES', titulo2)
                    ws.write(2, 0, 'DESDE', titulo)
                    ws.write(2, 1, str((fechai.date())), titulo)
                    ws.write(3, 0, 'HASTA:', titulo)
                    ws.write(3, 1, str((fechaf.date())), titulo)

                    ws.write(5, 0,  'CARRERA', titulo)
                    ws.write(5, 1,  'GRUPO', titulo)
                    ws.write(5, 2,  'NOMBRES', titulo)
                    ws.write(5, 3,  'CEDULA', titulo)
                    ws.write(5, 4,  'CELULAR', titulo)
                    ws.write(5, 5,  'CONVENCIONAL', titulo)
                    ws.write(5, 6,  'EMAIL PERSONAL', titulo)
                    ws.write(5, 7,  'EMAIL INSTITUCIONAL', titulo)
                    ws.write(5, 8,  'VALOR DEUDA', titulo)
                    ws.write(5, 9,  '# RUBROS VENCIDOS', titulo)
                    ws.write(5, 10,  'ULTIMA FECHA VENCIDA', titulo)

                    fila=5
                    hoy = datetime.today().date()
                    ins = Matricula.objects.filter(nivel__cerrado=False, nivel__carrera__carrera=True).values('inscripcion')
                    inscripcion = Inscripcion.objects.filter(id__in=ins, persona__usuario__is_active=True).order_by('persona__apellido1','persona__apellido2')
                    prueba=0
                    for i in inscripcion:
                        matricula = Matricula.objects.filter(inscripcion=i, nivel__cerrado=False)[:1].get()
                        rubro = Rubro.objects.filter(inscripcion=i, cancelado=False, fechavence__lte=fechaf, fechavence__gte=fechai).order_by('fechavence')
                        if rubro.filter(fechavence__lte=hoy).exists():
                            prueba=prueba+1
                            fila = fila+1
                            rub = 0
                            num = 0
                            for r in rubro:
                                rub = rub + r.valor
                                num = num + 1
                                if num >= rubro.count():
                                    print(r.id)
                                    try:
                                        ws.write(fila, 0, elimina_tildes(r.inscripcion.carrera.nombre))
                                    except:
                                        ws.write(fila, 0, '')
                                    try:
                                        ws.write(fila, 1, matricula.nivel.grupo.nombre)
                                    except:
                                        ws.write(fila, 1, '')
                                    try:
                                        ws.write(fila, 2, elimina_tildes(r.inscripcion.persona.nombre_completo_inverso()))
                                    except:
                                        ws.write(fila, 2, '')
                                    try:
                                        if r.inscripcion.persona.cedula:
                                            ws.write(fila, 3, elimina_tildes(r.inscripcion.persona.cedula))
                                        else:
                                            ws.write(fila, 3, elimina_tildes(r.inscripcion.persona.pasaporte))
                                    except:
                                        ws.write(fila, 3, '')
                                    try:
                                        ws.write(fila, 4, elimina_tildes(r.inscripcion.persona.telefono))
                                    except:
                                        ws.write(fila, 4, '')
                                    try:
                                        ws.write(fila, 5, elimina_tildes(r.inscripcion.persona.telefono_conv))
                                    except:
                                        ws.write(fila, 5, '')
                                    try:
                                        ws.write(fila, 6, elimina_tildes(r.inscripcion.persona.email))
                                    except:
                                        ws.write(fila, 6, '')
                                    try:
                                        ws.write(fila, 7, elimina_tildes(r.inscripcion.persona.emailinst))
                                    except:
                                        ws.write(fila, 7, '')
                                    try:
                                        ws.write(fila, 8, rub)
                                    except:
                                        ws.write(fila, 8, '')
                                    try:
                                        ws.write(fila, 9, num)
                                    except:
                                        ws.write(fila, 9, '')
                                    try:
                                        ws.write(fila, 10, str(r.fechavence))
                                    except:
                                        ws.write(fila, 10, '')

                    print(prueba)

                    nombre ='Deuda estudiantes'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(ex)
                    pass

        else:
            data = {'title': 'Consultas de Pagos en Linea'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                data['generarform']=RangoFacturasForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
                return render(request ,"reportesexcel/deuda_estudiantes.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")
    except Exception as e:
        print(e)
        return HttpResponseRedirect('/?info='+str(e))

