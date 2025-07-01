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
from sga.models import Periodo, convertir_fecha,TituloInstitucion,ReporteExcel,Canton,Provincia,Coordinacion,Matricula,total_matriculadosfil,total_matriculadosfilnullprovin,total_matriculadosfilprovinporcent, MateriaAsignada, SesionJornada
from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):

    try:
        if request.method=='POST':
            action = request.POST['action']
            if action :
                periodo= Periodo.objects.filter(pk=request.POST['periodo'])[:1].get()
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

                    ws.write_merge(0, 0, 0, 15,)
                    ws.write_merge(1, 1, 0, 15,)
                    ws.write (0, 0, 'INSTITUTO TECNOLOGICO BOLIVARIANO',center )
                    ws.write(1, 0, 'MATRIZ EST01_carga_masiva_estudiantes - ' + elimina_tildes(periodo.periodo_repr()),center)
                    ws.write(2, 0, 'IDENTIFICACION', titulo)
                    ws.write(2, 1, 'CODIGO CARRERA', titulo)
                    ws.write(2, 2, 'CODIGO MATRICULA', titulo)
                    ws.write(2, 3, 'NUMERO CREDITOS APROBADOS', titulo)
                    ws.write(2, 4, 'SESION', titulo)
                    ws.write(2, 5, 'GRUPO', titulo)
                    ws.write(2, 6, 'MODALIDAD', titulo)

                    cont = 3
                    # print(Matricula.objects.filter(nivel__periodo=periodo,nivel__nivelmalla__in=(1,2,3,4,5,6),nivel__carrera__carrera=True).count())
                    for matricula in Matricula.objects.filter(nivel__periodo=periodo,nivel__nivelmalla__in=(1,2,3,4,5,6),nivel__carrera__carrera=True):
                        inscripcion = matricula.inscripcion
                        if inscripcion.persona.pasaporte:
                            try:
                                numeroIdentificacion = inscripcion.persona.pasaporte
                            except:
                                numeroIdentificacion= 'ERROR AL OBTENER PASAPORTE '
                        else:
                            try:
                                numeroIdentificacion = inscripcion.persona.cedula
                            except:
                                numeroIdentificacion= 'ERROR AL OBTENER CEDULA '

                        creditos =MateriaAsignada.objects.filter(matricula=matricula).aggregate(Sum('materia__creditos'))['materia__creditos__sum']
                        if SesionJornada.objects.filter(sesion=inscripcion.sesion).exists():
                           jornada = SesionJornada.objects.filter(sesion=inscripcion.sesion)[:1].get()
                           sesion = elimina_tildes(jornada.jornada.nombre)
                        else:
                            sesion =elimina_tildes(inscripcion.sesion.nombre)
                        grupo=matricula.nivel.grupo.nombre
                        modalidad=matricula.nivel.grupo.modalidad.nombre
                        # if inscripcion.sesion.nombre ==
                        ws.write(cont, 0, numeroIdentificacion)
                        ws.write(cont, 1, elimina_tildes(inscripcion.carrera) )
                        ws.write(cont, 2, inscripcion.numerom)
                        ws.write(cont, 3, creditos)
                        ws.write(cont, 4, sesion)
                        ws.write(cont, 5, grupo)
                        ws.write(cont, 6, modalidad)
                        cont=cont+1
                        print('MAT' + str(cont))
                    nombre ='reporte'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    return HttpResponse(json.dumps({"result":str(ex)+str(inscripcion)}),content_type="application/json")
        else:
                data = {'title': 'Matriz MAT01 '}
                addUserData(request,data)
                if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                    reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                    data['reportes'] = reportes
                data['generarform']=XLSPeriodoForm()
                return render(request ,"reportesexcel/mat_carga_masiva_matriculas.html" ,  data)
                # return HttpResponseRedirect("/reporteexcel")


    except Exception as e:
        print((e))
        return HttpResponseRedirect('/?info='+str(e))