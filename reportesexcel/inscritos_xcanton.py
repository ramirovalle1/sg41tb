from datetime import datetime,timedelta,time
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
from settings import MEDIA_ROOT
from sga.commonviews import addUserData
from sga.forms import XLSPeriodoForm, XLSInscritosCantonForm
from sga.models import Periodo, convertir_fecha,TituloInstitucion,ReporteExcel,Canton,Provincia,Coordinacion,Matricula,total_matriculadosfil,total_matriculadosfilnullprovin,total_matriculadosfilprovinporcent, Inscripcion
from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):

    try:
        if request.method=='POST':
            action = request.POST['action']
            if action :
                try:
                    print(request.POST)
                    desde = request.POST['desde']
                    hasta = request.POST['hasta']
                    fechai = convertir_fecha(desde)
                    fechaf = convertir_fecha(hasta)

                    fechai=datetime.combine(fechai,time(23,59,0,1))
                    fechaf=datetime.combine(fechaf,time(23,59,0,1))

                    provincia = Provincia.objects.get(pk=request.POST['provincia'])
                    canton = Canton.objects.get(pk=request.POST['canton'])

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
                    ws.write_merge(0, 0,0,7, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,7, 'Listado de Alumnos Inscritos por Canton', titulo2)
                    ws.write(3, 0,  'DESDE: ' +str(fechai), subtitulo)
                    ws.write(4, 0,  'HASTA: ' +str(fechaf), subtitulo)
                    ws.write(5, 0,  'PROVINCIA: '+ elimina_tildes(provincia.nombre), subtitulo)
                    ws.write(6, 0,  'CANTON: '+ elimina_tildes(canton.nombre), subtitulo)

                    ws.write(8, 0,  'NOMBRE', titulo)
                    ws.write(8, 1,  'CEDULA', titulo)
                    ws.write(8, 2,  'CARRERA', titulo)
                    ws.write(8, 3,  'DIRECCION', titulo)
                    ws.write(8, 4,  'CELULAR', titulo)
                    ws.write(8, 5,  'CONVENCIONAL', titulo)
                    ws.write(8, 6,  'EMAIL PERSONAL', titulo)
                    ws.write(8, 7,  'EMAIL INSTITUCIONAL', titulo)

                    inscripciones = Inscripcion.objects.filter(fecha__gte=fechai, fecha__lte=fechaf, persona__provincia=provincia, persona__canton=canton, carrera__carrera=True).order_by('persona__canton', 'carrera__nombre', 'persona__apellido1', 'persona__apellido2')
                    print(inscripciones.count())

                    fila = 9
                    for i in inscripciones:
                        ws.write(fila, 0, elimina_tildes(i.persona.nombre_completo_inverso()))
                        if i.persona.cedula:
                            ws.write(fila, 1, elimina_tildes(i.persona.cedula))
                        else:
                            ws.write(fila, 1, elimina_tildes(i.persona.pasaporte))
                        ws.write(fila, 2, elimina_tildes(i.carrera.nombre))
                        ws.write(fila, 3, i.persona.direccion_completa())
                        if i.persona.telefono:
                            ws.write(fila, 4, elimina_tildes(i.persona.telefono))
                        if i.persona.telefono_conv:
                            ws.write(fila, 5, elimina_tildes(i.persona.telefono_conv))
                        if i.persona.email:
                            ws.write(fila, 6, elimina_tildes(i.persona.email))
                        if i.persona.emailinst:
                            ws.write(fila, 7, elimina_tildes(i.persona.emailinst))

                        fila = fila+1

                    fila=fila+1
                    ws.write(fila, 0, "Fecha Impresion", subtitulo)
                    ws.write(fila, 1, str(datetime.now()), subtitulo)
                    ws.write(fila+1, 0, "Usuario", subtitulo)
                    ws.write(fila+1, 1, str(request.user), subtitulo)

                    nombre ='inscripciones'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    return HttpResponse(json.dumps({"result":str(ex)+str(provincia)}),content_type="application/json")
        else:
                data = {'title': 'Alumnos Inscritos por Canton'}
                addUserData(request,data)
                # if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                #     reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                #     data['reportes'] = reportes
                data['generarform']=XLSInscritosCantonForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
                return render(request ,"reportesexcel/inscritos_xcanton.html" ,  data)
                return HttpResponseRedirect("/reporteexcel")


    except Exception as e:
        print((e))
        return HttpResponseRedirect('/?info='+str(e))