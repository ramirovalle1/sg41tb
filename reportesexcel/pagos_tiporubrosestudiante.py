from datetime import datetime,timedelta
import json
import xlrd
import xlwt
import locale
import os
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
from settings import MEDIA_ROOT, GESTION_INDIVIDUAL, GESTION_DESCUENTO
from sga.commonviews import addUserData
from sga.forms import RangoReferidoForm
from sga.models import RubroSeguimiento, convertir_fecha, TituloInstitucion, Persona, elimina_tildes, ReporteExcel,Rubro,Pago

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action =='generarexcel':
                try:
                    desde = request.POST['desde']
                    hasta = request.POST['hasta']
                    fechai = convertir_fecha(desde)
                    fechaf = convertir_fecha(hasta)
                    #registros= RubroSeguimiento.objects.filter(fechapago__gte=fechai,fechapago__lte=fechaf,rubro__cancelado=True).exclude(fechapago=None).order_by('rubro__inscripcion__persona__apellido1','rubro__inscripcion__persona__apellido2','fechapago')
                    registros= Rubro.objects.filter(pago__fecha__gte=fechai,pago__fecha__lte=fechaf).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2')
                    m = 9
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('Registros',cell_overwrite_ok=True)

                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,m, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,m, 'Rubros Pagados por Categoria de Alumnos por Rango de Fechas',titulo2)
                    ws.write(4, 0,'Desde:   ' +str(fechai.date()), subtitulo)
                    ws.write(5, 0,'Hasta:   ' +str(fechaf.date()), subtitulo)

                    fila = 6
                    ws.write(fila, 0,'Identificacion', subtitulo)
                    ws.write_merge(fila,fila,1,2,"Estudiante",titulo)
                    ws.write(fila, 3,'Rubro', subtitulo)
                    ws.write(fila, 4,'Valor Cancelado', subtitulo)
                    ws.write(fila, 5,'Fecha Pago', subtitulo)
                    ws.write(fila, 6,'Valor Rubro', subtitulo)
                    ws.write(fila, 7,'Categoria', subtitulo)

                    fila =fila +1
                    totpagado=0
                    totvalorrubro=0
                    valorpagado=0
                    fechapago=''
                    for r in registros:
                        estudiante =  r.inscripcion.persona.nombre_completo_inverso()
                        if r.inscripcion.persona.cedula:
                            identificacion = r.inscripcion.persona.cedula
                        else:
                            identificacion = r.inscripcion.persona.pasaporte
                        ws.write(fila,0,str(identificacion))
                        ws.write_merge(fila,fila,1,2,elimina_tildes(estudiante))
                        ws.write(fila,3,elimina_tildes(r.nombre()))
                        if Pago.objects.filter(rubro=r).order_by('-fecha').exists():
                            pagos = Pago.objects.filter(rubro=r).order_by('-fecha')[:1].get()

                        if r.cancelado==True:
                            valorpagado=r.valor
                        else:
                            valorpagado=Pago.objects.filter(rubro=r).aggregate(Sum('valor'))['valor__sum']
                            if valorpagado==None:
                                valorpagado=0

                        ws.write(fila,4,valorpagado)
                        ws.write(fila,5,str(pagos.fecha))
                        ws.write(fila,6,r.valor)
                        ws.write(fila,7,str(r.diasvencimiento()))
                        totpagado+=valorpagado
                        totvalorrubro+=r.valor

                        fila = fila +1
                    ws.write(fila,0,'TOTALES:',subtitulo)
                    ws.write(fila,4,totpagado,subtitulo)
                    ws.write(fila,6,totvalorrubro,subtitulo)
                    fila = fila +1
                    detalle = 2 + fila
                    ws.write(detalle, 0, "Fecha Impresion", subtitulo)
                    ws.write(detalle, 2, str(datetime.now()), subtitulo)
                    detalle=detalle +1
                    ws.write(detalle, 0, "Usuario", subtitulo)
                    ws.write(detalle, 2, str(request.user), subtitulo)

                    nombre ='pagostiporubros'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")
                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")

        else:
            data = {'title': 'Pagos por Tipo de Rubros'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform']=RangoReferidoForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
                return render(request ,"reportesexcel/pagos_tiporubrosestudiante.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

