import datetime
import json
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
import xlwt
from settings import MEDIA_ROOT
from sga.commonviews import addUserData
from sga.forms import GestionExcelForm, EntregaUniformeExcelForm
from sga.inscripciones import convertir_fecha
from sga.models import  TituloInstitucion, EntregaUniformeMunicipo, ReporteExcel


@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action =='generarexcel':
                try:

                    fechaDesde= convertir_fecha(request.POST['fechainicio'])
                    fechaHasta=convertir_fecha(request.POST['fechafin'])
                    m = 5
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('Registros',cell_overwrite_ok=True)

                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,m+10, tit.nombre , subtitulo)
                    ws.write_merge(1, 1,0,m+10, 'LISTADO ENTREGA DE UNIFORME  ' , subtitulo)
                    ws.write(3, 0,  'ESTUDIANTE', subtitulo)
                    ws.write(3, 1,  'CARRERA', subtitulo)
                    ws.write(3, 2,  'FECHA REGISTRO', subtitulo)
                    ws.write(3, 3,  'USUARIO', subtitulo)
                    ws.write(3, 4,  'OBSERVACION', subtitulo)


                    entregauniforme = EntregaUniformeMunicipo.objects.filter(fecha__gte=fechaDesde, fecha__lte=fechaHasta).order_by("fecha")
                    fila=4
                    for c in entregauniforme:
                        columna=0
                        ws.write(fila, columna , str(c.inscripcion.persona.nombre_completo_inverso()))
                        ws.write(fila, columna+1 , str(c.inscripcion.carrera.nombre))
                        ws.write(fila, columna+2 , str(c.fecha))
                        ws.write(fila, columna+3 , str(c.usuario))
                        ws.write(fila, columna+4 , str(c.observacion))

                        fila = fila + 1
                    cont = fila + 3


                    ws.write(cont, 0, "Fecha Impresion", subtitulo)
                    ws.write(cont, 2, str(datetime.datetime.now()), subtitulo)
                    cont=cont +1
                    ws.write(cont, 0, "Usuario", subtitulo)
                    ws.write(cont, 2, str(request.user), subtitulo)

                    nombre ='entregauniforme'+str(datetime.datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")



        else:
            data = {'title': 'Entrega Uniforme Municipio'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform']=EntregaUniformeExcelForm(initial={'inicio':datetime.datetime.now(),'fin':datetime.datetime.now()})
                return render(request ,"reportesexcel/entrega_uniforme.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))
