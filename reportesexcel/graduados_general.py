from datetime import datetime, timedelta
import json
from django.db.models import Sum
import xlwt
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from settings import MEDIA_ROOT
from sga.commonviews import addUserData
from sga.models import TituloInstitucion, Graduado, ReporteExcel,SeguimientoGraduado,convertir_fecha
from sga.reportes import elimina_tildes
from sga.forms import GraduadosGeneralForm


@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            print(request.POST)
            action = request.POST['action']
            if action :
                try:
                    desde = request.POST['desde']
                    hasta = request.POST['hasta']
                    fechai = convertir_fecha(desde)
                    fechaf = convertir_fecha(hasta)
                    todos = request.POST['todos']
                    hoy = datetime.now().date()
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
                    ws.write_merge(1, 1,0,5, 'ALUMNOS GRADUADOS GENERAL', titulo2)
                    if todos == 'False':
                        ws.write(2, 0,'Desde:   ' +str(fechai.date()), subtitulo)
                        ws.write(3, 0,'Hasta:   ' +str(fechaf.date()), subtitulo)

                    fila=5
                    ws.write(fila, 0,  'NOMBRES', titulo)
                    ws.col(0).width = 10 * 600
                    ws.write(fila, 1,  'CEDULA', titulo)
                    ws.write(fila, 2,  'EDAD', titulo)
                    ws.write(fila, 3,  'CELULAR', titulo)
                    ws.write(fila, 4,  'CONVENCIONAL', titulo)
                    ws.write(fila, 5,  'EMAIL PERSONAL', titulo)
                    ws.write(fila, 6,  'EMAIL INSTITUCIONAL', titulo)
                    ws.write(fila, 7,  'FECHA GRADUACION', titulo)
                    ws.write(fila, 8,  'CARRERA', titulo)
                    ws.write(fila, 9,  'ANIOS GRADUADO', titulo)
                    ws.write(fila, 10, 'PROVINCIA', titulo)
                    ws.write(fila, 11, 'CANTON', titulo)
                    ws.write(fila, 12, 'PARROQUIA', titulo)
                    ws.write(fila, 13, 'DIRECCION', titulo)
                    ws.write(fila, 14, 'LUGAR DE TRABAJO', titulo)
                    ws.write(fila, 15, 'EMAIL TRABAJO', titulo)
                    ws.write(fila, 16, 'TLF. TRABAJO', titulo)
                    ws.write(fila, 17, 'CARGO', titulo)
                    ws.write(fila, 18, 'SUELDO', titulo)
                    ws.write(fila, 19, 'EJERCE', titulo)
                    totalgraduado =0
                    if todos =='True':
                        graduados = Graduado.objects.filter().order_by('inscripcion__persona__apellido1', 'inscripcion__persona__apellido2','inscripcion__persona__nombres')
                        totalgraduado = graduados.count()
                    else:
                        graduados = Graduado.objects.filter(fechagraduado__gte=fechai,fechagraduado__lte=fechaf).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')
                        totalgraduado =graduados.count()
                    for g in graduados:
                        # print(g)
                        provincia=''
                        canton=''
                        parroquia=''
                        direccion=''
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

                        if g.fechagraduado:
                            fecha_graduado = g.fechagraduado
                            anios_graduado = hoy.year - fecha_graduado.year
                        else:
                            anios_graduado = ''
                        ws.write(fila, 7, str(g.fechagraduado))
                        ws.write(fila, 8, elimina_tildes(g.inscripcion.carrera.nombre))
                        ws.write(fila, 9, anios_graduado)

                        try:
                            provincia = elimina_tildes(g.inscripcion.persona.provinciaresid)
                        except:
                            provincia = ''
                        try:
                            canton = elimina_tildes(g.inscripcion.persona.cantonresid)
                        except:
                            canton = ''
                        try:
                            parroquia = elimina_tildes(g.inscripcion.persona.parroquia)
                        except:
                            parroquia = ''
                        try:
                            direccion = elimina_tildes(g.inscripcion.persona.direccion_completa())
                        except:
                            direccion = ''

                        ws.write(fila,10, provincia)
                        ws.write(fila,11, canton)
                        ws.write(fila,12, parroquia)
                        ws.write(fila,13, direccion)
                        for sg in SeguimientoGraduado.objects.filter(graduado__id=g.pk):
                                if sg:
                                    try:
                                        if sg.empresa:
                                            empresa=elimina_tildes(sg.empresa)
                                        else:
                                            empresa=''
                                        ws.write(fila,14,empresa)
                                    except Exception as ex:
                                        ws.write(fila,14, "")
                                        pass

                                    ws.write(fila,15,elimina_tildes(sg.email))
                                    ws.write(fila,16,elimina_tildes(sg.telefono))
                                    ws.write(fila,17,elimina_tildes(sg.cargo))
                                    ws.write(fila,18,sg.sueldo)
                                    if sg.ejerce==True:
                                        ejerce='Si'
                                    else:
                                        ejerce='No'
                                    ws.write(fila,19,ejerce)

                    fila=fila+1
                    ws.write(fila, 0, "Total de Graduados", subtitulo)
                    ws.write(fila, 1, totalgraduado, subtitulo)
                    fila = fila + 1
                    ws.write(fila, 0, "Fecha Impresion", subtitulo)
                    ws.write(fila, 1, str(datetime.now()), subtitulo)
                    ws.write(fila+1, 0, "Usuario", subtitulo)
                    ws.write(fila+1, 1, str(request.user), subtitulo)

                    nombre ='graduadosgeneral'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(ex)
                    return HttpResponse(json.dumps({"result":str(ex) }),content_type="application/json")
        else:
            data = {'title': 'LISTADO DE GRADUADOS'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['generarform']=GraduadosGeneralForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
                return render(request ,"reportesexcel/graduados_general.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")
    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))


