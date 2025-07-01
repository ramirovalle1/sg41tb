from datetime import datetime, timedelta
import json
import xlwt
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from settings import MEDIA_ROOT
from sga.commonviews import addUserData
from sga.forms import RangoFacturasForm
from sga.models import convertir_fecha,TituloInstitucion, PagoPymentez, Rubro, Carrera, SeguimientoGraduado, Graduado, Persona, ReporteExcel, Matricula, PerfilInscripcion
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
                    ws.write_merge(0, 0,0,14, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,14, 'LISTADO DE ALUMNOS POR ETNIA', titulo2)
                    ws.write(2, 0, 'DESDE', titulo)
                    ws.write(2, 1, str((fechai.date())), titulo)
                    ws.write(3, 0, 'HASTA:', titulo)
                    ws.write(3, 1, str((fechaf.date())), titulo)
                    fila=5

                    matriculas = Matricula.objects.filter(inscripcion__persona__usuario__is_active=True,inscripcion__fecha__gte=fechai,inscripcion__fecha__lte=fechaf).distinct('inscripcion__persona__apellido1','inscripcion__persona__apellido2').order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2')
                    ws.write(fila, 0,  'FECHA', titulo)
                    ws.write(fila, 1,  'NOMBRE ALUMNO', titulo)
                    ws.write(fila, 2,  'IDENTIFICACION', titulo)
                    ws.write(fila, 3, 'ETNIA', titulo)

                    for m in matriculas:
                        fila=fila+1
                        try:
                            ws.write(fila, 0, str(m.inscripcion.fecha))
                        except:
                            ws.write(fila, 0, '')
                        try:
                            ws.write(fila, 1, elimina_tildes(m.inscripcion.persona.nombre_completo_inverso()))
                        except:
                            ws.write(fila, 1, '')
                        try:
                            if m.inscripcion.persona.cedula:
                                ws.write(fila, 2, elimina_tildes(m.inscripcion.persona.cedula))
                            else:
                                ws.write(fila, 2, elimina_tildes(m.inscripcion.persona.pasaporte))
                        except:
                            ws.write(fila, 2, '')
                        if PerfilInscripcion.objects.filter(inscripcion=m.inscripcion).exists():
                            ins = PerfilInscripcion.objects.filter(inscripcion=m.inscripcion)[:1].get()
                        else:
                            ins = ''
                        print(ins)
                        try:
                            ws.write(fila, 3, elimina_tildes(ins.raza.nombre))
                        except:
                            ws.write(fila, 3, '')

                    fila=fila+3


                    nombre ='_alumnos_por_etnia'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(ex)
                    # return HttpResponse(json.dumps({"result":str(ex) + " "+  str(p.inscripcion)}),content_type="application/json")
        else:
            data = {'title': 'Listado de alumnos por etnia'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['generarform']=RangoFacturasForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
                return render(request ,"reportesexcel/alumnos_xetnia.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")
    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))


