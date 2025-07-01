from datetime import datetime,timedelta,time
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
from settings import UTILIZA_GRUPOS_ALUMNOS, EMAIL_ACTIVE,MEDIA_ROOT, ASIG_VINCULACION, ASIG_PRATICA,JR_USEROUTPUT_FOLDER,MEDIA_URL, SITE_ROOT
from sga.commonviews import addUserData, ip_client_address
from sga.forms import RangoFacturasForm
from sga.models import convertir_fecha,TituloInstitucion,ReporteExcel,RequerimientoSoporte,RequerimSolucion
from fpdf import FPDF
from sga.reportes import elimina_tildes

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

                    fechai=datetime.combine(fechai,time(23,59,0,1))
                    fechaf=datetime.combine(fechaf,time(23,59,0,1))

                    m = 16
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on;align: wrap on, vert centre, horiz center')
                    titulo1 = xlwt.easyxf('font: bold on,colour green, bold on; align: wrap on, vert centre, horiz center')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo3 = xlwt.easyxf('font: name Times New Roman; align: wrap on, vert centre, horiz center')
                    subtitulo.font.height = 20*10
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('Registros',cell_overwrite_ok=True)

                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,m, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,m, 'Requerimientos de Mesa de Ayuda por Rango de Fechas',titulo2)
                    ws.write(4, 0,'Desde:   ' +str(fechai.date()), subtitulo)
                    ws.write(5, 0,'Hasta:   ' +str(fechaf.date()), subtitulo)

                    fila = 9
                    com = 9
                    detalle = 3
                    columna=12
                    c=9
                    cab = 16
                    ws.write(8,0,"Fecha Requerimiento",titulo)
                    ws.write(8,1,"Soporte",titulo)
                    ws.write(8,2,"Tipo de Requerimiento",titulo)
                    ws.write(8,3,"Solicitado por",titulo)
                    ws.write(8,4,"Requerimiento",titulo)
                    ws.write(8,5,"Estado",titulo)
                    ws.write(8,6,"Calificacion",titulo)
                    ws.write(8,7,"Fecha Reasignacion",titulo)
                    ws.write(8,8,"Soporte Reasignado",titulo)
                    ws.write(8,9,"Solucion",titulo)
                    ws.write(8,10,"Fecha Solucion",titulo)
                    ws.write(8,11,"Estado",titulo)
                    fila=8
                    # requerimientos = RequerimientoSoporte.objects.filter(fecha__gte=fechai,fecha__lte=fechaf,pk=13844).order_by('soporte__soporte__persona__apellido1','soporte__soporte__persona__apellido2','fecha')
                    requerimientos = RequerimientoSoporte.objects.filter(fecha__gte=fechai,fecha__lte=fechaf).order_by('soporte__soporte__persona__apellido1','soporte__soporte__persona__apellido2','fecha')
                    for req in requerimientos:
                        fila=fila+1
                        # print(req.id)
                        solicitadopor=''
                        soporteasignado=''
                        estado1=''
                        estado2=''
                        calificacion=''
                        reasignado=''
                        solucion=''
                        fecha=req.fecha
                        freasignacion=''
                        fsolucion=''
                        requerimiento=''
                        resolucion=''
                        ws.write(fila,0,str(fecha), subtitulo3)
                        if req.soporte:
                            soporteasignado=elimina_tildes(req.soporte.soporte.persona.nombre_completo_inverso())
                        else:
                            soporteasignado='Soporte no ha sido asignado'

                        ws.write(fila,1,soporteasignado, subtitulo3)
                        ws.write(fila,2,elimina_tildes(req.tipoproblema.descripcion), subtitulo3)
                        ws.write(fila,3,elimina_tildes(req.persona.nombre_completo_inverso()), subtitulo3)
                        try:
                            if req.requerimiento:
                                requerimiento=elimina_tildes(req.requerimiento).replace("/","").replace("\ "," ")
                            else:
                                requerimiento=''
                        except:
                            requerimiento='Error en requerimiento'

                        ws.write(fila,4,elimina_tildes(requerimiento), subtitulo3)

                        if req.finalizado:
                            estado1='Finalizado'
                        else:
                            estado1='Pendiente'

                        ws.write(fila,5,estado1,subtitulo3)
                        if req.calificacion:
                            calificacion=elimina_tildes(req.calificacion.descripcion)
                        else:
                            calificacion=''
                        ws.write(fila,6,calificacion,subtitulo3)

                        try:
                            if req.soporreasig:
                                reasignado=elimina_tildes(req.soporreasig.soporte.persona.nombre_completo_inverso())
                                freasignacion=str(req.fecharesignacion)
                            else:
                                reasignado=''
                                freasignacion=''
                        except:
                            reasignado=''
                            freasignacion=''

                        ws.write(fila,7,freasignacion,subtitulo3)
                        ws.write(fila,8,reasignado,subtitulo3)

                        if RequerimSolucion.objects.filter(requerimiento=req).exists():
                            solucion=RequerimSolucion.objects.filter(requerimiento=req)[:1].get()
                            if solucion.finalizado:
                                estado2='Finalizado'
                                fsolucion=solucion.fecha
                            else:
                                estado2='Pendiente'

                            try:
                                if solucion.solucion:
                                    resolucion=elimina_tildes(solucion.solucion).replace("/","").replace("\ "," ")
                                else:
                                    resolucion=''
                            except:
                                resolucion='Error en Solucion'
                        else:
                            resolucion=''

                        ws.write(fila,9,elimina_tildes(resolucion),subtitulo3)
                        ws.write(fila,10,str(fsolucion),subtitulo3)
                        ws.write(fila,11,str(estado2),subtitulo3)

                    detalle = detalle + fila
                    ws.write(detalle,0, "Fecha Impresion", subtitulo)
                    ws.write(detalle,1, str(datetime.now()), subtitulo)
                    detalle=detalle+2
                    ws.write(detalle,0, "Usuario", subtitulo)
                    ws.write(detalle,1, str(request.user), subtitulo)

                    nombre ='mesadeayuda_porrangofecha'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")
        else:
            data = {'title': 'Mesa de Ayuda por Rango de Fechas'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform']=RangoFacturasForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
                return render(request ,"reportesexcel/mesadeayuda_porrangofechas.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

