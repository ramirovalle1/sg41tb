from datetime import datetime
import json
from requests.packages.urllib3 import request
import xlwt
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from settings import MEDIA_ROOT
from sga.commonviews import addUserData
from sga.forms import EntregaUniformeExcelForm
from sga.models import Inscripcion,convertir_fecha,TituloInstitucion, ReferidosInscripcion, Graduado
from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action =='generarexcel':
                    nombre = ejecutar(request.POST['desde'], request.POST['hasta'], request.user)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

        else:
            data = {'title': 'Comision Referidos'}
            addUserData(request,data)
            # if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
            #     reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
            #     data['reportes'] = reportes
            data['generarform']=EntregaUniformeExcelForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
            return render(request ,"reportesexcel/xls_referidos_cobro.html" ,  data)
            # return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

def ejecutar(desde, hasta, usuario):
    try:
        # desde = request.POST['desde']
        # hasta = request. POST['hasta']
        fechai = convertir_fecha(desde)
        fechaf = convertir_fecha(hasta)

        titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on;align: wrap on, vert centre, horiz center')
        titulo1 = xlwt.easyxf('font: bold on,colour green, bold on; align: wrap on, vert centre, horiz center')
        titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
        titulo.font.height = 20*11
        titulo2.font.height = 20*11
        subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
        subtitulo3 = xlwt.easyxf('font: name Times New Roman; align: wrap on, vert centre, horiz center')
        subtitulo.font.height = 20*10
        wb = xlwt.Workbook()
        ws = wb.add_sheet('Listado', cell_overwrite_ok=True)

        tit = TituloInstitucion.objects.all()[:1].get()
        ws.write_merge(0, 0, 0, 6, tit.nombre , titulo2)
        ws.write_merge(1, 1, 0, 6, 'Comision Referidos por Rango de Fechas',titulo2)
        ws.write(3, 0, 'Desde:   ' +str(fechai.date()), subtitulo)
        ws.write(4, 0, 'Hasta:   ' +str(fechaf.date()), subtitulo)

        referidosCobro = ReferidosInscripcion.objects.filter(pagocomision=True, fecha__gte=fechai, fecha__lte=fechaf).order_by('fecha')
        graduados = Graduado.objects.filter(inscripcion__id__in=referidosCobro.values('inscripcion'))

        ws.write(6, 0, "Total de referidos que cobraron $25: "+str(referidosCobro.count()), subtitulo)
        ws.write(7, 0, "Total de inspripciones que ingresaron referidos: "+str(len(referidosCobro.order_by('inscripcion__id').distinct('inscripcion').values('inscripcion'))), subtitulo)
        ws.write(8, 0, "Total de inspripciones que ingresaron referidos y son graduados: "+str(graduados.count()), subtitulo)

        ws.write(10, 0, "Persona Refiere", titulo)
        ws.write(10, 1, "Cedula", titulo)
        ws.write(10, 2, "Graduado", titulo)
        ws.write(10, 3, "Tipo", titulo)
        ws.write(10, 4, "Incripcion Referida", titulo)
        ws.write(10, 5, "Fecha", titulo)
        fila=11

        for r in referidosCobro:
            ws.write(fila, 0, elimina_tildes(r.inscripcion.persona if r.inscripcion else r.administrativo))
            if r.inscripcion:
                ws.write(fila, 1, r.inscripcion.persona.cedula if r.inscripcion.persona.cedula else r.inscripcion.persona.pasaporte)
                ws.write(fila, 2, "SI" if Graduado.objects.filter(inscripcion=r.inscripcion).exists() else "NO")
            else:
                ws.write(fila, 1, r.administrativo.cedula if r.administrativo.cedula else r.administrativo.pasaporte)
                ws.write(fila, 2, "NO APLICA")
            ws.write(fila, 3, "ALUMNO" if r.inscripcion else "ADMINISTRATIVO")
            ws.write(fila, 4, elimina_tildes(r.inscripcionref.persona if r.inscripcionref else r.apellido1+' '+r.apellido2+' '+r.nombres))
            ws.write(fila, 5, str(r.fecha))
            fila += 1

        fila += 1
        ws.write(fila,0, "Fecha Impresion", subtitulo)
        ws.write(fila,1, str(datetime.now()), subtitulo)
        ws.write(fila+1,0, "Usuario", subtitulo)
        ws.write(fila+1,1, str(usuario), subtitulo)

        nombre ='referidos'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
        wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
        return nombre
        # return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

    except Exception as ex:
        print(str(ex))
        return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")
