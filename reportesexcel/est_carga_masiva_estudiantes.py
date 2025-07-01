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
from sga.models import Periodo, convertir_fecha,TituloInstitucion,ReporteExcel,Canton,Provincia,Coordinacion,Matricula,total_matriculadosfil,total_matriculadosfilnullprovin,total_matriculadosfilprovinporcent
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
                    ws.write(2, 0, 'TIPO IDENTIFICACION', titulo)
                    ws.write(2, 1, 'IDENTIFICACION', titulo)
                    ws.write(2, 2, 'NOMBRES', titulo)
                    ws.write(2, 3, 'PRIMER APELLIDO', titulo)
                    ws.write(2, 4, 'SEGUNDO APELLIDO', titulo)
                    ws.write(2, 5, 'FECHA NACIMIENTO', titulo)
                    ws.write(2, 6, 'SEXO', titulo)
                    ws.write(2, 7, 'DISCAPACIDAD', titulo)
                    ws.write(2, 8, 'NUMERO CONADIS', titulo)
                    ws.write(2, 9, 'EMAIL PERSONAL', titulo)
                    ws.write(2, 10, 'ETNIA', titulo)
                    ws.write(2, 11, 'PAIS ORIGEN', titulo)
                    ws.write(2, 12, 'EMAIL INSTITUCIONAL', titulo)
                    cont = 3
                    print(Matricula.objects.filter(nivel__periodo=periodo,nivel__nivelmalla__in=(1,2,3,4,5,6),nivel__carrera__carrera=True).count())
                    for matricula in Matricula.objects.filter(nivel__periodo=periodo,nivel__nivelmalla__in=(1,2,3,4,5,6),nivel__carrera__carrera=True):

                        inscripcion = matricula.inscripcion

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
                        if inscripcion.persona.sexo.nombre == "FEMENINO":
                            sexoId = 'MUJER'
                        else:
                            sexoId = 'HOMBRE'

                        discapacidad='NINGUNA '
                        carnetdiscapacidad = ''
                        tipodiscapacidad = ''
                        if inscripcion.nee():
                            if inscripcion.nee().tienediscapacidad:
                                porcdiscapacidad = inscripcion.nee().porcientodiscapacidad
                                carnetdiscapacidad = inscripcion.nee().carnetdiscapacidad
                                if inscripcion.nee().tipodiscapacidad:
                                    try:
                                        discapacidad = elimina_tildes(inscripcion.nee().tipodiscapacidad.nombre)
                                    except :
                                       discapacidad= 'ERROR AL OBTENER DISCAPACIDAD'
                        # ////////////////////////////////////////////////////////////////
                        # //////////////////etniaId///////////////////////////////////
                        try:
                            email = inscripcion.persona.email
                        except:
                            try:
                                email = elimina_tildes(inscripcion.persona.emailinst)
                            except:
                                email='ERROR EN EMAIL '

                        try:
                            emailinst = inscripcion.persona.emailinst
                        except:
                            emailinst = 'ERROR EN EMAIL INST'

                        etniaId ='OTRO'
                        if inscripcion.nee():
                            if inscripcion.nee().raza:
                                try:
                                    etniaId =elimina_tildes(inscripcion.nee().raza)
                                except:
                                    etniaId = 'ERROR AL OBTENER ETNIA'
                        # /////////////////////////////////////////////////////////////
                        # ////////////////////paisNacionalidadId/////////////////////////////////
                        paisNacionalidadId = ''
                        if inscripcion.persona.nacionalidad:
                            if inscripcion.persona.nacionalidad.id == 1:
                                paisNacionalidadId = 'ECUADO'
                            elif inscripcion.persona.nacionalidad.id == 2:
                                paisNacionalidadId = 'CUBA'
                            elif inscripcion.persona.nacionalidad.id == 3:
                                paisNacionalidadId = 'COLOMBIA'
                            elif inscripcion.persona.nacionalidad.id == 4:
                                paisNacionalidadId = 'VENEZUELA'
                            elif inscripcion.persona.nacionalidad.id == 5:
                                paisNacionalidadId = 'COREA'
                            elif inscripcion.persona.nacionalidad.id == 6:
                                paisNacionalidadId = 'PERU'
                            elif inscripcion.persona.nacionalidad.id == 8:
                                paisNacionalidadId = 'ESPANOLA'
                            elif inscripcion.persona.nacionalidad.id == 9:
                                paisNacionalidadId = 'BRASILENA'
                            elif inscripcion.persona.nacionalidad.id == 10:
                                paisNacionalidadId = 'AREGENTINA'
                            elif inscripcion.persona.nacionalidad.id == 11:
                                paisNacionalidadId = 'ESTADOS UNIDOS'
                            elif inscripcion.persona.nacionalidad.id == 12:
                                paisNacionalidadId = 'COSTA RICA'
                            elif inscripcion.persona.nacionalidad.id == 13:
                                paisNacionalidadId = 'CHINA'
                            elif inscripcion.persona.nacionalidad.id == 14:
                                paisNacionalidadId = 'PARAGUAY'
                        # periodoId=1
                        try:
                            nacimiento = str(inscripcion.persona.nacimiento.strftime('%Y-%m-%d'))
                        except:
                            nacimiento ='ERROR EN FECHA DE NACIMIENTO'
                        try:
                            nombre = elimina_tildes(inscripcion.persona.nombres)
                        except:
                            nombre ='ERROR EN NOMBRE'
                        try:
                            apellido1 = elimina_tildes(inscripcion.persona.apellido1)
                        except:
                            apellido1 ='ERROR EN APELLIDO1'

                        try:
                            apellido2 = elimina_tildes(inscripcion.persona.apellido2)
                        except:
                            apellido2 ='ERROR EN APELLIDO2'
                        ws.write(cont, 0, tipoDocumentoId)
                        ws.write(cont, 1, numeroIdentificacion, titulo)
                        ws.write(cont, 2,nombre )
                        ws.write(cont, 3, apellido1)
                        ws.write(cont, 4,apellido2)
                        ws.write(cont, 5, nacimiento)
                        ws.write(cont, 6, sexoId)
                        ws.write(cont, 7, discapacidad)
                        ws.write(cont, 8, carnetdiscapacidad)
                        ws.write(cont, 9, elimina_tildes(email))
                        ws.write(cont, 10, etniaId)
                        ws.write(cont, 11, paisNacionalidadId)
                        ws.write(cont, 12, elimina_tildes(emailinst))
                        cont=cont+1
                        print('EST' + str(cont))
                    nombre ='reporte'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    return HttpResponse(json.dumps({"result":str(ex)+str(inscripcion)}),content_type="application/json")
        else:
                data = {'title': 'Matriz EST01 '}
                addUserData(request,data)
                if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                    reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                    data['reportes'] = reportes
                    data['generarform']=XLSPeriodoForm()
                    return render(request ,"reportesexcel/est_carga_masiva_estudiantes.html" ,  data)
                return HttpResponseRedirect("/reporteexcel")


    except Exception as e:
        print((e))
        return HttpResponseRedirect('/?info='+str(e))