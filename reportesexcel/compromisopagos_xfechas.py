from datetime import datetime,timedelta
import json
from requests.packages.urllib3 import request
import xlwt
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from settings import MEDIA_ROOT
from sga.commonviews import addUserData
from sga.forms import EntregaUniformeExcelForm
from sga.models import Inscripcion,convertir_fecha,TituloInstitucion, RubroSeguimiento, AsistAsuntoEstudiant
from fpdf import FPDF
from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action =='generarexcel':
                    nombre = ejecutar(request,request.POST['desde'], request.POST['hasta'],request.user)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

        else:
            data = {'title': 'Estudiantees Absentos por Rango de Fechas'}
            addUserData(request,data)
            # if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
            #     reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
            #     data['reportes'] = reportes
            data['generarform']=EntregaUniformeExcelForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
            return render(request ,"reportesexcel/compromisopagos_xfecha.html" ,  data)
            # return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

def ejecutar(request,desde,hasta,usuario):
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
        ws.write_merge(1, 1, 0, 6, 'Rubros por Vencer su Gestion',titulo2)
        ws.write(3, 0,'Desde:   ' +str(fechai.date()), subtitulo)
        ws.write(4, 0,'Hasta:   ' +str(fechaf.date()), subtitulo)

        ws.write(6,0,"Inscripcion",titulo)
        ws.write(6,1,"Cedula",titulo)
        ws.write(6,2,"Rubro",titulo)
        ws.write(6,3,"Valor",titulo)
        ws.write(6,4,"Categoria",titulo)
        ws.write(6,5,"Fecha Posible Pago",titulo)
        ws.write(6,6,"Pagado",titulo)
        ws.write(6,7,"Fecha Pago",titulo)
        ws.write(6,8,"Gestor",titulo)

        fila=7
        asistente = None
        manana = datetime.now().date() +  timedelta(1)
        if AsistAsuntoEstudiant.objects.filter(asistente__usuario=request.user).exists():
            asistente = AsistAsuntoEstudiant.objects.filter(asistente__usuario=request.user)[:1].get()
        if RubroSeguimiento.objects.filter(rubro__cancelado=False,fechaposiblepago__gte=fechai, fechaposiblepago__lte=fechaf,fechapago=None).exists():
            rubros_seguimiento = RubroSeguimiento.objects.filter(rubro__cancelado=False,fechaposiblepago__gte=fechai, fechaposiblepago__lte=fechaf,fechapago=None)
            if asistente:
                rubros_seguimiento = rubros_seguimiento.filter(seguimiento__usuario=asistente.asistente.usuario)
            for rs in rubros_seguimiento:
                pagado=''
                f_pago=''
                try:
                    inscripcion = rs.rubro.inscripcion.persona.nombre_completo_inverso()
                    if rs.rubro.inscripcion.persona.cedula:
                        identificacion = elimina_tildes(rs.rubro.inscripcion.persona.cedula)
                    else:
                        identificacion = rs.rubro.inscripcion.persona.pasaporte
                    rubro = elimina_tildes(rs.rubro.nombre())
                    valor = rs.rubro.valor
                    categoria = rs.categoria.categoria
                    fecha = str(rs.fechaposiblepago)
                    gestor = rs.seguimiento.usuario.username
                    if rs.rubro.cancelado:
                        pagado='SI'
                        pago = rs.rubro.ultimo_pago()
                        f_pago=str(pago.fecha)
                    else:
                        pagado='NO'
                        f_pago=''
                    ws.write(fila, 0, inscripcion)
                    ws.write(fila, 1, identificacion)
                    ws.write(fila, 2, rubro)
                    ws.write(fila, 3, valor)
                    ws.write(fila, 4, categoria)
                    ws.write(fila, 5, fecha)
                    ws.write(fila, 6, pagado)
                    ws.write(fila, 7, f_pago)
                    ws.write(fila, 8, gestor)
                    fila = fila + 1
                except Exception as ex:
                    print('ERROR: '+str(ex)+' - ('+str(rs.id)+')')

        fila = fila + 1
        ws.write(fila,0, "Fecha Impresion", subtitulo)
        ws.write(fila,1, str(datetime.now()), subtitulo)
        ws.write(fila+1,0, "Usuario", subtitulo)
        ws.write(fila+1,1, str(usuario), subtitulo)

        nombre ='compromiso_pagos'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
        wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
        return nombre
        # return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

    except Exception as ex:
        print(str(ex))
        return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")
