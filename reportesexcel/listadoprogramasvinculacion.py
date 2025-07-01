__author__ = 'vgonzalez'
from datetime import datetime, timedelta
import json
import xlwt
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from settings import MEDIA_ROOT
from sga.commonviews import addUserData
from sga.models import TituloInstitucion, ReporteExcel, TipoPrograma


@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            print(request.POST)
            action = request.POST['action']
            if action =='generarexcel':
                try:
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('LISTADO',cell_overwrite_ok=True)

                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,8, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,8, 'LISTADO PROGRAMAS DE VINCULACION', titulo2)

                    fila =3

                    ws.write(fila, 0,  'NOMBRE', titulo)
                    ws.write(fila, 1,  'OBJETIVO', titulo)
                    ws.write(fila, 2,  'ESTADO', titulo)

                    programa = TipoPrograma.objects.all().order_by('-activo','nombre')

                    for pr in programa:
                        fila=fila+1
                        ws.write(fila, 0, pr.nombre)
                        ws.write(fila, 1, pr.objetivo)
                        ws.write(fila, 2, pr.activo)
                        if pr.activo:
                            ws.write(fila, 2, "ACTIVO")
                        else:
                            ws.write(fila, 2, "INACTIVO")

                    fila=fila+2
                    ws.write(fila, 0, "Fecha Impresion", subtitulo)
                    ws.write(fila, 1, str(datetime.now()), subtitulo)
                    ws.write(fila+1, 0, "Usuario", subtitulo)
                    ws.write(fila+1, 1, str(request.user), subtitulo)

                    nombre ='listadoprogramasvinculacion'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(ex)
                    return HttpResponse(json.dumps({"result":str(ex) }),content_type="application/json")
        else:
            data = {'title': 'Listado Programas Vinculacion'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                return render(request ,"reportesexcel/listadoprogramasvinculacion.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))


