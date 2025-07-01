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
from settings import UTILIZA_GRUPOS_ALUMNOS, EMAIL_ACTIVE,MEDIA_ROOT, ASIG_VINCULACION, ASIG_PRATICA,JR_USEROUTPUT_FOLDER,MEDIA_URL, SITE_ROOT
from sga.commonviews import addUserData, ip_client_address
from sga.forms import DistributivoForm
from sga.models import Inscripcion,convertir_fecha,TituloInstitucion,ReporteExcel,DetalleRetiradoMatricula
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

                    m = 16
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on;align: wrap on, vert centre, horiz center')
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
                    ws.write_merge(1, 1,0,m, 'Estudiantes Retirados por Rango de Fechas',titulo2)
                    ws.write(4, 0,'Desde:   ' +str(fechai.date()), subtitulo)
                    ws.write(5, 0,'Hasta:   ' +str(fechaf.date()), subtitulo)

                    fila = 9
                    com = 9
                    detalle = 3
                    columna=12
                    c=9
                    motivo=''
                    celular=''
                    convencional=''
                    correo1=''
                    correo2=''
                    correo3=''
                    correo4=''
                    cab = 16

                    ws.write(8,0,"Identificacion",titulo)
                    ws.write(8,1,"Nombres",titulo)
                    ws.write(8,2,"Carrera",titulo)
                    ws.write(8,3,"Grupo",titulo)
                    ws.write(8,4,"Motivo Retiro",titulo)
                    ws.write(8,5,"Fecha Retiro",titulo)
                    ws.write(8,6,"Convencional",titulo)
                    ws.write(8,7,"Celular",titulo)
                    ws.write(8,8,"Email Inst",titulo)
                    ws.write(8,9,"Email 1",titulo)
                    ws.write(8,10,"Email 2",titulo)
                    ws.write(8,11,"Email 3",titulo)

                    detalleretirados = DetalleRetiradoMatricula.objects.filter(fecha__gte=fechai,fecha__lte=fechaf,retirado__activo=False).order_by('retirado__inscripcion').distinct()
                    # detalleretirados = DetalleRetiradoMatricula.objects.filter(fecha__gte=fechai,fecha__lte=fechaf,retirado__activo=False,retirado__inscripcion__id=53705).order_by('retirado__inscripcion__persona__apellido1','retirado__inscripcion__persona__apellido2','retirado__inscripcion__persona__nombres').distinct('retirado__inscripcion')

                    for retirados in detalleretirados:
                        # print(retirados)

                        if retirados.retirado.inscripcion.persona.cedula:
                            identificacion=retirados.retirado.inscripcion.persona.cedula
                        else:
                            identificacion=retirados.retirado.inscripcion.persona.pasaporte

                        ws.write(fila,0,str(identificacion) , subtitulo3)
                        ws.write(fila,1,elimina_tildes(retirados.retirado.inscripcion.persona.nombre_completo_inverso()), subtitulo3)
                        ws.write(fila,2,elimina_tildes(retirados.retirado.inscripcion.carrera), subtitulo3)
                        ws.write(fila,3,elimina_tildes(retirados.retirado.nivel.grupo.nombre), subtitulo3)
                        try:
                            if retirados.motivo:
                                motivo=elimina_tildes(retirados.motivo)
                            else:
                                motivo=''
                        except Exception as ex:
                            pass
                            motivo='REVISAR MOTIVO EN EL SISTEMA'
                        ws.write(fila,4,motivo, subtitulo3)
                        ws.write(fila,5,elimina_tildes(retirados.fecha), subtitulo3)
                        try:
                            if retirados.retirado.inscripcion.persona.telefono_conv:
                                convencional=retirados.retirado.inscripcion.persona.telefono_conv.replace("-","")
                            else:
                                convencional=''
                            ws.write(fila,6,convencional,subtitulo3)
                        except Exception as ex:
                            pass

                        try:
                            if retirados.retirado.inscripcion.persona.telefono:
                                celular=retirados.retirado.inscripcion.persona.telefono.replace("-","")
                            else:
                                celular=''
                            ws.write(fila,7,celular,subtitulo3)
                        except Exception as ex:
                            pass

                        try:
                            if retirados.retirado.inscripcion.persona.emailinst:
                                correo1=retirados.retirado.inscripcion.persona.emailinst
                            else:
                                correo1=''
                            ws.write(fila,8,correo1,subtitulo3)
                        except Exception as ex:
                            pass

                        try:
                            if retirados.retirado.inscripcion.persona.email:
                                correo2=retirados.retirado.inscripcion.persona.email
                            else:
                                correo2=''
                            ws.write(fila,9,correo2,subtitulo3)
                        except Exception as ex:
                            pass

                        try:
                            if retirados.retirado.inscripcion.persona.email1:
                                correo3=retirados.retirado.inscripcion.persona.email1
                            else:
                                correo3=''
                            ws.write(fila,10,correo3,subtitulo3)
                        except Exception as ex:
                            pass

                        try:
                            if retirados.retirado.inscripcion.persona.email2:
                                correo4=retirados.retirado.inscripcion.persona.email2
                            else:
                                correo4=''
                            ws.write(fila,11,correo4,subtitulo3)
                        except Exception as ex:
                            pass

                        fila = fila +1

                    detalle = detalle + fila
                    ws.write(detalle,0, "Fecha Impresion", subtitulo)
                    ws.write(detalle,1, str(datetime.now()), subtitulo)
                    detalle=detalle+2
                    ws.write(detalle,0, "Usuario", subtitulo)
                    ws.write(detalle,1, str(request.user), subtitulo)

                    nombre ='retirados_porrangofecha'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")
        else:
            data = {'title': 'Retirados por Rango de Fechas'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform']=DistributivoForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
                return render(request ,"reportesexcel/retirados_porrangofecha.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

