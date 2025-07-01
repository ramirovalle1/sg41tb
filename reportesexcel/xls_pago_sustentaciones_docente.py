
from datetime import datetime,timedelta
import json
import xlrd
import xlwt

from django.contrib.auth.decorators import login_required

from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from settings import UTILIZA_GRUPOS_ALUMNOS, EMAIL_ACTIVE,MEDIA_ROOT, ASIG_VINCULACION, ASIG_PRATICA
from sga.commonviews import addUserData, ip_client_address
from sga.forms import RangoFacturasForm,RangoNCForm, VinculacionExcelForm
from sga.models import Inscripcion,convertir_fecha,Factura,ClienteFactura,TituloInstitucion,ReporteExcel,Graduado, Persona,SeguimientoGraduado, Carrera, Matricula, RecordAcademico, PagoSustentacionesDocente
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
                    ws = wb.add_sheet('Pago Sustentaciones',cell_overwrite_ok=True)

                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,8, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,8, 'LISTADO DE PAGO SUSTENTACIONES A DOCENTES', titulo2)
                    ws.write(3, 0, 'DESDE', titulo)
                    ws.write(3, 1, str((fechai.date())), titulo)
                    ws.write(4, 0, 'HASTA:', titulo)
                    ws.write(4, 1, str((fechaf.date())), titulo)

                    fila = 6
                    ws.write(6, 0,  'FECHA', titulo)
                    ws.write(6, 1,  'DOCENTE', titulo)
                    ws.write(6, 2,  'IDENTIFICACION DOCENTE', titulo)
                    ws.write(6, 3,  'TELEFONO DOCENTE', titulo)
                    ws.write(6, 4,  'VALOR/ALUMNO', titulo)
                    ws.write(6, 5,  '# ALUMNOS', titulo)
                    ws.write(6, 6,  'TOTAL', titulo)
                    ws.write(6, 7,  'APROBADO POR DECANA', titulo)

                    pagos = PagoSustentacionesDocente.objects.filter(fecha__gte=fechai,fecha__lte=fechaf).order_by('fecha')
                    for p in pagos:
                        print(p.id)
                        identificacion = ''
                        telefono = ''

                        fila = fila +1
                        columna=0
                        fecha=str(p.fecha.date())
                        profe=elimina_tildes(p.profesor.persona.nombre_completo_inverso())
                        if p.profesor.persona.cedula:
                            identificacion=elimina_tildes(p.profesor.persona.cedula)
                        else:
                            identificacion=elimina_tildes(p.profesor.persona.pasaporte)
                        if p.profesor.persona.telefono:
                            telefono=str(p.profesor.persona.telefono)

                        ws.write(fila,0 , fecha)
                        ws.write(fila,1 , profe)
                        ws.write(fila,2 , identificacion)
                        ws.write(fila,3 , telefono)
                        ws.write(fila,4 , str(p.valorxestudiante))
                        ws.write(fila,5 , str(p.numestudiantes))
                        ws.write(fila,6 , str(p.valortotal))
                        if p.aprobado:
                            ws.write(fila,7 , 'SI')
                        else:
                            ws.write(fila,7 , 'NO')

                    fila=fila+2
                    ws.write(fila, 0, "Fecha Impresion", subtitulo)
                    ws.write(fila, 2, str(datetime.now()), subtitulo)
                    ws.write(fila+1, 0, "Usuario", subtitulo)
                    ws.write(fila+1, 2, str(request.user), subtitulo)

                    nombre ='pago_sustentaciones'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")

        else:
            data = {'title': 'Listado Pago Sustentaciones a Docentes'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform']=RangoFacturasForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
                return render(request ,"reportesexcel/pago_sustentaciones_docente.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

