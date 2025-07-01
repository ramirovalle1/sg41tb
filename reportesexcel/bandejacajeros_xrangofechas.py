from datetime import datetime,timedelta,time
import json
from django.contrib.auth.models import User, Group
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
from settings import UTILIZA_GRUPOS_ALUMNOS, EMAIL_ACTIVE,MEDIA_ROOT, ASIG_VINCULACION, ASIG_PRATICA,JR_USEROUTPUT_FOLDER,MEDIA_URL, SITE_ROOT, ID_TIPO_SOLICITUD
from sga.commonviews import addUserData, ip_client_address
from sga.forms import RangoFacturasForm
from sga.models import convertir_fecha,TituloInstitucion,ReporteExcel,RequerimientoSoporte,RequerimSolucion, RubroEspecieValorada, SolicitudSecretariaDocente, Persona, Departamento
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
                    ws.write_merge(1, 1,0,m, 'Revision Solicitudes Cajeros por Rango de Fechas',titulo2)
                    ws.write(4, 0,'Desde:   ' +str(fechai.date()), subtitulo)
                    ws.write(5, 0,'Hasta:   ' +str(fechaf.date()), subtitulo)

                    ws.write(8,0,"CAJERO",titulo)
                    ws.write(8,1,"USUARIO",titulo)
                    ws.write(8,2,"ASIGNADOS",titulo)
                    ws.write(8,3,"FINALIZADOS",titulo)
                    ws.write(8,4,"PENDIENTES",titulo)

                    fila=9
                    # requerimientos = RubroEspecieValorada.objects.filter(fecha__gte=fechai, fecha__lte=fechaf,usuario__id__in=User.objects.filter(groups__id__in=[27])).order_by('soporte__soporte__persona__apellido1','soporte__soporte__persona__apellido2','fecha')
                    departamento = Departamento.objects.get(pk=27)
                    requerimientos = SolicitudSecretariaDocente.objects.filter(fecha__gte=fechai, fecha__lte=fechaf,departamento=departamento, solicitudestudiante__tipoe__id=ID_TIPO_SOLICITUD).exclude(solicitudestudiante=None)
                    cajeros = Persona.objects.filter(id__in=requerimientos.values('personaasignada')).order_by('apellido1','apellido2','nombres')

                    # requerimientos = SolicitudSecretariaDocente.objects.filter(fecha__gte=fechai, fecha__lte=fechaf, solicitudestudiante__tipoe__id=ID_TIPO_SOLICITUD).exclude(solicitudestudiante=None)
                    # cajeros = Persona.objects.filter(id__in=requerimientos.values('personaasignada'), usuario__groups__id__in=Group.objects.filter(pk=7).values('pk')).order_by('apellido1','apellido2','nombres')

                    if cajeros:
                        for c in cajeros:
                            # print('-------------------------')
                            req_asignados = requerimientos.filter(personaasignada=c)
                            req_finalizados = requerimientos.filter(personaasignada=c, cerrada=True)
                            req_pendientes = requerimientos.filter(personaasignada=c, cerrada=False)
                            # print(req_asignados.count())
                            # print(req_finalizados.count())
                            ws.write(fila,0, elimina_tildes(c.nombre_completo_inverso()))
                            ws.write(fila,1, elimina_tildes(c.usuario.username))
                            ws.write(fila,2, req_asignados.count())
                            ws.write(fila,3, req_finalizados.count())
                            ws.write(fila,4, req_pendientes.count())

                            fila=fila+1


                    # ws.write(detalle,0, "Fecha Impresion", subtitulo)
                    # ws.write(detalle,1, str(datetime.now()), subtitulo)
                    # detalle=detalle+2
                    # ws.write(detalle,0, "Usuario", subtitulo)
                    # ws.write(detalle,1, str(request.user), subtitulo)

                    nombre ='solicitudes_cajeros'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")
        else:
            data = {'title': 'Revision Solicitudes Cajeros'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform']=RangoFacturasForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
                return render(request ,"reportesexcel/bandejacajeros_xrangofechas.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

