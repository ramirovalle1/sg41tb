from datetime import datetime, timedelta
import json
import xlwt
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from settings import MEDIA_ROOT
from sga.commonviews import addUserData
from sga.forms import RangoFacturasForm
from sga.models import convertir_fecha,TituloInstitucion, PagoPymentez, Rubro, Carrera, SeguimientoGraduado, Graduado, Persona, ReporteExcel, Matricula, PerfilInscripcion, Inscripcion
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

                    ws.write(fila, 0,  'CARRERA', titulo)
                    ws.write(fila, 1,  'GRUPO', titulo)
                    ws.write(fila, 2,  'NIVEL', titulo)
                    ws.write(fila, 3,  'NOMBRE', titulo)
                    ws.write(fila, 4,  'CELULAR', titulo)
                    ws.write(fila, 5,  'TELEFONO CONVENCIONAL', titulo)
                    ws.write(fila, 6,  'CORREO INSTITUCIONAL', titulo)
                    ws.write(fila, 7,  'CORREO PERSONAL', titulo)
                    ws.write(fila, 8,  'DOMICILIO', titulo)
                    ws.write(fila, 9,  'CANTON', titulo)
                    ws.write(fila, 10, 'PARROQUIA', titulo)

                    inscritos = Inscripcion.objects.filter(persona__usuario__is_active=True, fecha__gte=fechai,fecha__lte=fechaf, carrera__carrera=True).order_by('carrera','persona__canton','persona__parroquia','persona__apellido1','persona__apellido2')
                    for i in inscritos:
                        if Matricula.objects.filter(inscripcion=i).exists():
                            matricula =  Matricula.objects.filter(inscripcion=i).order_by('-id')[:1].get()
                        fila=fila+1
                        try:
                            ws.write(fila, 0, elimina_tildes(i.carrera.nombre))
                        except:
                            ws.write(fila, 0, '')
                        try:
                            ws.write(fila, 1, matricula.nivel.paralelo)
                        except:
                            ws.write(fila, 1, '')
                        try:
                            ws.write(fila, 2, matricula.nivel.nivelmalla.nombre)
                        except:
                            ws.write(fila, 2, '')
                        try:
                            ws.write(fila, 3, elimina_tildes(i.persona.nombre_completo_inverso()))
                        except:
                            ws.write(fila, 3, '')
                        try:
                            ws.write(fila, 4, i.persona.telefono)
                        except:
                            ws.write(fila, 4, '')
                        try:
                            ws.write(fila, 5, i.persona.telefono_conv)
                        except:
                            ws.write(fila, 5, '')
                        try:
                            ws.write(fila, 6, elimina_tildes(i.persona.emailinst))
                        except:
                            ws.write(fila, 6, '')
                        try:
                            ws.write(fila, 7, elimina_tildes(i.persona.email))
                        except:
                            ws.write(fila, 7, '')
                        try:
                            ws.write(fila, 8, elimina_tildes(i.persona.direccion_completa()))
                        except:
                            ws.write(fila, 8, '')
                        try:
                            ws.write(fila, 9, elimina_tildes(i.persona.canton))
                        except:
                            ws.write(fila, 9, '')
                        try:
                            ws.write(fila, 10, elimina_tildes(i.persona.parroquia))
                        except:
                            ws.write(fila, 10, '')

                    fila=fila+3


                    nombre ='informacion_estudiantes'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(ex)
                    return HttpResponse(json.dumps({"result":str(ex) + " "+  str(i.inscripcion)}),content_type="application/json")
        else:
            data = {'title': 'Informacion Estudiantes'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['generarform']=RangoFacturasForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
                return render(request ,"reportesexcel/informacion_alumnos.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")
    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))


