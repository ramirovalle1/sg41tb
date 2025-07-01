from datetime import datetime,timedelta,date
import json
import xlrd
import xlwt
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
from settings import MEDIA_ROOT
from sga.commonviews import addUserData
from sga.forms import XLSPeriodoForm
from sga.models import Periodo, convertir_fecha,TituloInstitucion,ReporteExcel,Canton,Provincia,Coordinacion,Matricula,total_matriculadosfil,total_matriculadosfilnullprovin,total_matriculadosfilprovinporcent, Graduado, ConvalidacionInscripcion, Inscripcion
from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):

    try:
        if request.method=='POST':
            action = request.POST['action']
            if action :
                inscripcion= ''
                try:
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10
                    style1 = xlwt.easyxf('',num_format_str='DD-MMM-YY')
                    wb = xlwt.Workbook()

                    # ezxf = easyxf
                    center = xlwt.easyxf('align: horiz center')
                    ws = wb.add_sheet('EST01_carga_masiva_estudiantes',cell_overwrite_ok=True)
                    # writer = XLSWriter()

                    # data = ["Negrilla", "Centrada", u"Centrada y con corte de linea"]
                    # format = [ezxf('font: bold on'), ezxf('align: horiz center'), ezxf('align: wrap on, horiz center')]
                    # writer.append(data, format)

                    ws.write_merge(0, 0, 0, 10,)
                    ws.write_merge(1, 1, 0, 10,)
                    ws.write (0, 0, 'INSTITUTO TECNOLOGICO BOLIVARIANO',center )
                    ws.write(1, 0, 'MATRIZ CPE01_carga_masiva_carreras_estudiante 2015 -20199 ' ,center)
                    ws.write(2, 0, 'IDENTIFICACION', titulo)
                    ws.write(2, 1, 'CARRERA', titulo)
                    ws.write(2, 2, 'FECHA INICIO PRIMER NIVEL', titulo)
                    ws.write(2, 3, 'NIVEL', titulo)
                    ws.write(2, 4, 'FECHA CONVALIDACION', titulo)
                    ws.write(2, 5, 'FECHA GRADUACION', titulo)
                    ws.write(2, 6, 'NUMERO REGISTRO SENESCYT', titulo)
                    ws.write(2, 7, 'GRUPO', titulo)
                    ws.write(2, 8, 'MODALIDAD', titulo)

                    cont = 3
                    # print(Graduado.objects.filter(fechagraduado__gte=periodo.inicio, fechagraduado__lte=periodo.fin).count())
                    inicio = date(2015,1,1)
                    fin = date(2019,12,31)
                    inscripid = Matricula.objects.filter(nivel__periodo__inicio__gte=inicio,nivel__periodo__inicio__lte=fin,nivel__nivelmalla__in=(1,2,3,4,5,6),nivel__carrera__carrera=True).distinct('inscripcion').values('inscripcion')
                    for inscripcion in Inscripcion.objects.filter(id__in=inscripid):
                    # for graduado in Graduado.objects.filter(fechagraduado__gte=periodo.inicio, fechagraduado__lte=periodo.fin):

                        inscripcion = inscripcion

                        if inscripcion.persona.pasaporte:
                            tipoDocumentoId = 'PASAPORTE'
                            try:
                                numeroIdentificacion = inscripcion.persona.pasaporte
                            except:
                                numeroIdentificacion= 'ERROR AL OBTENER PASAPORTE '
                        else:
                            tipoDocumentoId = 'CEDULA'
                            try:
                                numeroIdentificacion = inscripcion.persona.cedula
                            except:
                                numeroIdentificacion= 'ERROR AL OBTENER CEDULA '
                        fechaconvalidacion=''
                        fechaInicioCarrera=''
                        nivel=''
                        grupo=''
                        modalidad=''
                        if ConvalidacionInscripcion.objects.filter(record__inscripcion=inscripcion).exists():
                            conval =ConvalidacionInscripcion.objects.filter(record__inscripcion=inscripcion).order_by('id')[:1].get()
                            try:
                                if conval.fecha:
                                    fechaconvalidacion = conval.fecha.strftime('%Y-%m-%d')
                                else:
                                    fechaconvalidacion =str(conval.anno)
                            except:
                                fechaconvalidacion= 'ERROR AL OBTENER FECHA '
                        else:
                            if Matricula.objects.filter(inscripcion=inscripcion,nivel__nivelmalla__id=1).exists():
                                matfech = Matricula.objects.filter(inscripcion=inscripcion,nivel__nivelmalla__id=1).order_by('id')[:1].get()
                            else:
                                if  Matricula.objects.filter(inscripcion=inscripcion,nivel__nivelmalla__id__in=(1,2,3,4,5,6)).exists():
                                    matfech = Matricula.objects.filter(inscripcion=inscripcion,nivel__nivelmalla__id__in=(1,2,3,4,5,6)).order_by('id')[:1].get()
                            if matfech !='':
                                try:
                                    fechaInicioCarrera = matfech.nivel.periodo.inicio.strftime('%Y-%m-%d')
                                    try:
                                        nivel = matfech.nivel.nivelmalla.nombre
                                        grupo = matfech.nivel.grupo.nombre
                                        modalidad=matfech.nivel.grupo.modalidad.nombre
                                    except Exception as e:
                                        nivel = 'NO SE PUDO OBTENER EL NIVEL'
                                        grupo=''
                                        modalidad=''
                                except:
                                    fechaInicioCarrera = 'NO SE PUDO OBTENER FECHA'
                                    try:
                                        nivel = matfech.nivel.nivelmalla.nombre
                                        grupo = matfech.nivel.grupo.nombre
                                        modalidad=matfech.nivel.grupo.modalidad.nombre
                                    except Exception as e:
                                        nivel = 'NO SE PUDO OBTENER EL NIVEL'
                                        grupo=''
                                        modalidad=''
                        fechag=''
                        registro=''
                        if Graduado.objects.filter(inscripcion=inscripcion).exists():
                            graduado=Graduado.objects.filter(inscripcion=inscripcion)[:1].get()
                            try:
                                fechag = graduado.fechagraduado.strftime('%d-%m-%Y')
                            except:
                                fechag='ERROR AL OBTENER FECHA'
                            try:
                                registro = graduado.registro
                            except:
                                registro='ERROR AL OBTENER CODIGO SENESCYT'
                        ws.write(cont, 0, numeroIdentificacion, titulo)
                        ws.write(cont, 1, elimina_tildes(inscripcion.carrera))
                        ws.write(cont, 2, str(fechaInicioCarrera))
                        ws.write(cont, 3, str(nivel))
                        ws.write(cont, 4, str(fechaconvalidacion))
                        ws.write(cont, 5, str(fechag))
                        ws.write(cont, 6, str(registro))
                        ws.write(cont, 7, str(grupo))
                        ws.write(cont, 8, str(modalidad))

                        cont=cont+1
                        print('CPE ' + str(cont))
                    nombre ='reporte'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    return HttpResponse(json.dumps({"result":str(ex)+str(inscripcion)}),content_type="application/json")
        else:
                data = {'title': 'Matriz CPE01 '}
                addUserData(request,data)
                if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                    reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                    data['reportes'] = reportes
                # data['generarform']=XLSPeriodoForm()
                    return render(request ,"reportesexcel/cpe_carga_masiva_carreras_estudiante .html" ,  data)
                return HttpResponseRedirect("/reporteexcel")


    except Exception as e:
        print((e))
        return HttpResponseRedirect('/?info='+str(e))