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
from sga.forms import DistributivoForm, AbsentosExcelForm
from sga.models import Inscripcion,convertir_fecha,TituloInstitucion,ReporteExcel,DetalleRetiradoMatricula,Absentismo,Carrera,NivelMalla
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
                    ws.write_merge(1, 1,0,m, 'Estudiantes Absentos por Rango de Fechas',titulo2)
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
                    carreras=''
                    cab = 16
                    ws.write(8,0,"Identificacion",titulo)
                    ws.write(8,1,"Nombres",titulo)
                    ws.write(8,2,"Convencional",titulo)
                    ws.write(8,3,"Celular",titulo)
                    ws.write(8,4,"Email Inst",titulo)
                    ws.write(8,5,"Email 1",titulo)
                    ws.write(8,6,"Nivel",titulo)
                    ws.write(8,7,"Grupo",titulo)
                    ws.write(8,8,"Materia",titulo)
                    fila=8
                    totabsentosnivel=0

                    if request.POST['todos']=="1":
                        carreras = Absentismo.objects.filter(fecha__gte=fechai,fecha__lte=fechaf,finalizado=False).order_by('materiaasignada__matricula__inscripcion__carrera').distinct().values('materiaasignada__matricula__inscripcion__carrera')
                    else:
                        if request.POST['carrera']:
                            carreras= Carrera.objects.filter(pk=request.POST['carrera'])
                    for carrera in carreras:
                        if request.POST['todos']=="1":
                            nombrecarrera=Carrera.objects.filter(pk=carrera['materiaasignada__matricula__inscripcion__carrera'])[:1].get()
                        else:
                            nombrecarrera=Carrera.objects.filter(pk=carrera.id)[:1].get()
                        fila=fila+1
                        ws.write(fila,0,nombrecarrera.nombre,titulo1)
                        nivelesmalla = NivelMalla.objects.filter().order_by('nombre').exclude(id__in=[11,12]).distinct().values('id')
                        for nivelmalla in nivelesmalla:
                            nombrenivel=NivelMalla.objects.filter(pk=nivelmalla['id'])[:1].get()

                            if request.POST['todos']=="1":
                                # absentos = Inscripcion.objects.filter(persona__usuario__is_active=True,pk__in=Absentismo.objects.filter(fecha__gte=fechai,fecha__lte=fechaf,finalizado=False,materiaasignada__matricula__nivel__carrera__id=carrera['materiaasignada__matricula__inscripcion__carrera'],materiaasignada__matricula__nivel__nivelmalla__id=nivelmalla['id']).distinct('materiaasignada__matricula__inscripcion').values('materiaasignada__matricula__inscripcion')).order_by('persona__apellido1','persona__apellido2','persona__nombres')
                                totabsentosnivel = Inscripcion.objects.filter(persona__usuario__is_active=True,pk__in=Absentismo.objects.filter(fecha__gte=fechai,fecha__lte=fechaf,finalizado=False,materiaasignada__matricula__nivel__carrera__id=carrera['materiaasignada__matricula__inscripcion__carrera'],materiaasignada__matricula__nivel__nivelmalla__id=nivelmalla['id']).distinct().values('materiaasignada__matricula__inscripcion')).count()
                                absentos = Absentismo.objects.filter(materiaasignada__matricula__inscripcion__persona__usuario__is_active=True,fecha__gte=fechai,fecha__lte=fechaf,finalizado=False,materiaasignada__matricula__nivel__carrera__id=carrera['materiaasignada__matricula__inscripcion__carrera'],materiaasignada__matricula__nivel__nivelmalla__id=nivelmalla['id']).distinct().order_by('materiaasignada__matricula__inscripcion')
                            else:
                                # absentos = Inscripcion.objects.filter(persona__usuario__is_active=True,pk__in=Absentismo.objects.filter(fecha__gte=fechai,fecha__lte=fechaf,finalizado=False,materiaasignada__matricula__nivel__carrera__id=carrera.id,materiaasignada__matricula__nivel__nivelmalla__id=nivelmalla['id']).distinct('materiaasignada__matricula__inscripcion').values('materiaasignada__matricula__inscripcion')).order_by('persona__apellido1','persona__apellido2','persona__nombres')
                                totabsentosnivel = Inscripcion.objects.filter(persona__usuario__is_active=True,pk__in=Absentismo.objects.filter(fecha__gte=fechai,fecha__lte=fechaf,finalizado=False,materiaasignada__matricula__nivel__carrera__id=carrera.id,materiaasignada__matricula__nivel__nivelmalla__id=nivelmalla['id']).distinct().values('materiaasignada__matricula__inscripcion')).count()
                                absentos = Absentismo.objects.filter(materiaasignada__matricula__inscripcion__persona__usuario__is_active=True,fecha__gte=fechai,fecha__lte=fechaf,finalizado=False,materiaasignada__matricula__nivel__carrera__id=carrera.id,materiaasignada__matricula__nivel__nivelmalla__id=nivelmalla['id']).distinct().order_by('materiaasignada__matricula__inscripcion')


                            estudiantes=0
                            for absento in absentos:
                                fila=fila+1
                                # print(absento)

                                if absento.materiaasignada.matricula.inscripcion.persona.cedula:
                                    identificacion=absento.materiaasignada.matricula.inscripcion.persona.cedula
                                else:
                                    identificacion=absento.materiaasignada.matricula.inscripcion.persona.pasaporte
                                ws.write(fila,0,str(identificacion) , subtitulo3)
                                ws.write(fila,1,elimina_tildes(absento.materiaasignada.matricula.inscripcion.persona.nombre_completo_inverso()), subtitulo3)

                                try:
                                    if absento.materiaasignada.matricula.inscripcion.persona.telefono_conv:
                                        convencional=absento.materiaasignada.matricula.inscripcion.persona.telefono_conv.replace("-","")
                                    else:
                                        convencional=''
                                    ws.write(fila,2,convencional,subtitulo3)
                                except Exception as ex:
                                    pass

                                try:
                                    if absento.materiaasignada.matricula.inscripcion.persona.telefono:
                                        celular=absento.materiaasignada.matricula.inscripcion.persona.telefono.replace("-","")
                                    else:
                                        celular=''
                                    ws.write(fila,3,celular,subtitulo3)
                                except Exception as ex:
                                    pass

                                try:
                                    if absento.materiaasignada.matricula.inscripcion.persona.emailinst:
                                        correo1=absento.materiaasignada.matricula.inscripcion.persona.emailinst
                                    else:
                                        correo1=''
                                    ws.write(fila,4,correo1,subtitulo3)
                                except Exception as ex:
                                    pass

                                try:
                                    if absento.materiaasignada.matricula.inscripcion.persona.email:
                                        correo2=absento.materiaasignada.matricula.inscripcion.persona.email
                                    else:
                                        correo2=''
                                    ws.write(fila,5,correo2,subtitulo3)
                                except Exception as ex:
                                    pass

                                ws.write(fila,6,nombrenivel.nombre,subtitulo3)
                                try:
                                    # if Absentismo.objects.filter(fecha__gte=fechai,fecha__lte=fechaf,finalizado=False,materiaasignada__matricula__inscripcion=absento).exists():
                                    #     inscrip_grupo=Absentismo.objects.filter(fecha__gte=fechai,fecha__lte=fechaf,finalizado=False,materiaasignada__matricula__inscripcion=absento)[:1].get()
                                    grupo=absento.materiaasignada.matricula.nivel.grupo.nombre
                                    ws.write(fila,7,grupo,subtitulo3)
                                except Exception as ex:
                                    pass

                                ws.write(fila,8,elimina_tildes(absento.materiaasignada.materia.asignatura.nombre) ,subtitulo3)

                            if totabsentosnivel>0:
                                fila = fila +1
                                ws.write(fila,0,"Total en: " +str(nombrenivel),titulo)
                                ws.write(fila,1,totabsentosnivel,titulo)
                                fila = fila +1

                    detalle = detalle + fila
                    ws.write(detalle,0, "Fecha Impresion", subtitulo)
                    ws.write(detalle,1, str(datetime.now()), subtitulo)
                    detalle=detalle+2
                    ws.write(detalle,0, "Usuario", subtitulo)
                    ws.write(detalle,1, str(request.user), subtitulo)

                    nombre ='absentos_porrangofecha'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")
        else:
            data = {'title': 'Estudiantees Absentos por Rango de Fechas'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform']=AbsentosExcelForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
                return render(request ,"reportesexcel/absentos_porrangofecha.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

