from datetime import datetime, timedelta
import json
from django.db.models import Sum
import xlwt
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from settings import MEDIA_ROOT
from sga.commonviews import addUserData
from sga.forms import GraduadosAnioCarreraForm
from sga.models import TituloInstitucion, Rubro, Inscripcion, MONTH_CHOICES, Pago, Graduado, Carrera


@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            print(request.POST)
            action = request.POST['action']
            if action :
                try:
                    anio = request.POST['anio']
                    carrera = Carrera.objects.get(pk=request.POST['carrera'])

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

                    fila=3
                    ws.write(fila, 0,  'ANIO', titulo)
                    ws.write(fila, 1,  anio, titulo)
                    ws.write(fila+1, 0,  'CARRERA', titulo)
                    ws.write(fila+1, 1,  carrera.nombre, titulo)

                    fila=6
                    ws.write(fila, 0,  'NOMBRES', titulo)
                    ws.write(fila, 1,  'CEDULA', titulo)
                    ws.write(fila, 2,  'EDAD', titulo)
                    ws.write(fila, 3,  'CELULAR', titulo)
                    ws.write(fila, 4,  'CONVENCIONAL', titulo)
                    ws.write(fila, 5,  'EMAIL PERSONAL', titulo)
                    ws.write(fila, 6,  'EMAIL INSTITUCIONAL', titulo)
                    ws.write(fila, 7,  'PROVINCIA', titulo)
                    ws.write(fila, 8,  'CANTON', titulo)
                    ws.write(fila, 9,  'PARROQUIA', titulo)
                    ws.write(fila, 10,  'DIRECCION DOMICIOLIO', titulo)
                    ws.write(fila, 11,  'FECHA GRADUACION', titulo)
                    ws.write(fila, 12,  'ANIOS GRADUADO', titulo)

                    totinscritos = 0
                    totpagado = 0
                    totporpagar = 0
                    meses = MONTH_CHOICES

                    graduados = Graduado.objects.filter(inscripcion__carrera=carrera, fechagraduado__year=anio).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')
                    for g in graduados:
                        fila=fila+1
                        if g.inscripcion.persona.cedula:
                            identificacion = g.inscripcion.persona.cedula
                        else:
                            identificacion = g.inscripcion.persona.pasaporte
                        ws.write(fila, 0, g.inscripcion.persona.nombre_completo_inverso())
                        ws.write(fila, 1, identificacion)
                        ws.write(fila, 2, g.inscripcion.persona.edad())
                        ws.write(fila, 3, g.inscripcion.persona.telefono)
                        ws.write(fila, 4, g.inscripcion.persona.telefono_conv)
                        ws.write(fila, 5, g.inscripcion.persona.email)
                        ws.write(fila, 6, g.inscripcion.persona.emailinst)
                        try:
                            provincia = g.inscripcion.persona.provincia.nombre
                        except:
                            provincia = ''
                        ws.write(fila, 7, provincia)
                        try:
                            canton = g.inscripcion.persona.canton.nombre
                        except:
                            canton = ''
                        ws.write(fila, 8, canton)
                        try:
                            parroquia = g.inscripcion.persona.parroquia.nombre
                        except:
                            parroquia = ''
                        ws.write(fila, 9, parroquia)
                        ws.write(fila, 10, g.inscripcion.persona.direccion_completa())
                        hoy = datetime.now().date()

                        if g.fechagraduado:
                            fecha_graduado = g.fechagraduado
                            anios_graduado = hoy.year - fecha_graduado.year
                        else:
                            anios_graduado = ''
                        ws.write(fila, 11, str(g.fechagraduado))
                        ws.write(fila, 12, anios_graduado)

                    fila=fila+1
                    ws.write(fila, 0, "Fecha Impresion", subtitulo)
                    ws.write(fila, 1, str(datetime.now()), subtitulo)
                    ws.write(fila+1, 0, "Usuario", subtitulo)
                    ws.write(fila+1, 1, str(request.user), subtitulo)



                    nombre ='totalinscritosxanio'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(ex)
                    return HttpResponse(json.dumps({"result":str(ex) }),content_type="application/json")
        else:
            data = {'title': 'Total Inscritos'}
            addUserData(request,data)
            # if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
            #     reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
            data['generarform']=GraduadosAnioCarreraForm()
            return render(request ,"reportesexcel/xls_graduadosxanioycarrera.html" ,  data)
            # return HttpResponseRedirect("/reporteexcel")
    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))


