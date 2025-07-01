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
from med.models import PersonaExtension
from settings import MEDIA_ROOT
from sga.commonviews import addUserData
from sga.forms import XLSPeriodoForm, RangoGestionForm, RangoCobrosForm, CacesRangoPeriodoForm
from sga.models import Periodo, convertir_fecha,TituloInstitucion,ReporteExcel,Canton,Provincia,Coordinacion,Matricula,total_matriculadosfil,total_matriculadosfilnullprovin,total_matriculadosfilprovinporcent, Inscripcion, ConvalidacionInscripcion
from sga.reportes import elimina_tildes
from socioecon.models import InscripcionFichaSocioeconomica


@login_required(redirect_field_name='ret', login_url='/login')
def view(request):

    try:
        if request.method=='POST':
            action = request.POST['action']
            if action :
                # periodo= Periodo.objects.filter(pk=request.POST['periodo'])[:1].get()
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
                    # writer = XLSWriter()

                    # data = ["Negrilla", "Centrada", u"Centrada y con corte de linea"]
                    # format = [ezxf('font: bold on'), ezxf('align: horiz center'), ezxf('align: wrap on, horiz center')]
                    # writer.append(data, format)

                    ws = wb.add_sheet('Matriz',cell_overwrite_ok=True)
                    # sheet_name.write_merge(fila_inicial, fila_final, columna_inicial, columna_final,).
                    ws.write_merge(0, 0, 0, 30,)
                    ws.write_merge(1, 1, 0, 30,)
                    ws.write (0, 0, 'INSTITUTO TECNOLOGICO BOLIVARIANO',center )
                    if request.POST['periodo'] != '':
                        periodo= Periodo.objects.filter(pk=request.POST['periodo'])[:1].get()
                        ws.write (1, 0, 'Periodo: ' + str(periodo.nombre),center )
                    else:
                        inicio = convertir_fecha( request.POST['inicio'])
                        fin = convertir_fecha(request.POST['fin'])
                        ws.write (1, 0, 'Desde: ' + str(inicio.date()) + " Hasta: " + str(fin.date()),center  )


                    ws.write(2, 0, 'CODIGO_IES', titulo)
                    ws.write(2, 1, 'CODIGO_CARRERA', titulo)
                    ws.write(2, 2, 'CIUDAD_CARRERA', titulo)
                    ws.write(2, 3, 'TIPO_IDENTIFICACION', titulo)
                    ws.write(2, 4, 'IDENTIFICACION', titulo)
                    ws.write(2, 5, 'PRIMER_APELLIDO', titulo)
                    ws.write(2, 6, 'SEGUNDO_APELLIDO', titulo)
                    ws.write(2, 7, 'NOMBRES', titulo)
                    ws.write(2, 8, 'SEXO', titulo)
                    ws.write(2, 9, 'FECHA_NACIMIENTO', titulo)
                    ws.write(2, 10, 'PAIS_ORIGEN', titulo)
                    ws.write(2, 11, 'DISCAPACIDAD', titulo)
                    ws.write(2, 12, 'PORCENTAJE_DISCAPACIDAD', titulo)
                    ws.write(2, 13, 'NUMERO_CONADIS', titulo)
                    ws.write(2, 14, 'ETNIA', titulo)
                    ws.write(2, 15, 'NACIONALIDAD', titulo)
                    ws.write(2, 16, 'DIRECCION', titulo)
                    ws.write(2, 17, 'EMAIL_PERSONAL', titulo)
                    ws.write(2, 18, 'EMAIL_INSTITUCIONAL', titulo)
                    ws.write(2, 19, 'FECHA_INICIO_PRIMER_NIVEL', titulo)
                    ws.write(2, 20, 'FECHA_INGRESO_CONVALIDACION', titulo)
                    ws.write(2, 21, 'PAIS_RESIDENCIA', titulo)
                    ws.write(2, 22, 'PROVINCIA_RESIDENCIA', titulo)
                    ws.write(2, 23, 'CANTON_RESIDENCIA', titulo)
                    ws.write(2, 24, 'CELULAR', titulo)
                    ws.write(2, 25, 'NIVEL_FORMACION_PADRE', titulo)
                    ws.write(2, 26, 'NIVEL_FORMACION_MADRE', titulo)
                    ws.write(2, 27, 'CANTIDAD_MIEMBROS_HOGAR', titulo)
                    ws.write(2, 28, 'TIPO_COLEGIO', titulo)
                    ws.write(2, 29, 'POLITICA_CUOTA', titulo)
                    ws.write(2, 30, 'CARRERA', titulo)
                    ws.write(2, 31, 'MODALIDAD', titulo)
                    ws.write(2, 32, 'NIVEL_ACADEMICO', titulo)

                    # periodo= Periodo.objects.filter(pk=request.POST['periodo'])[:1].get()

                    cont = 3
                    c=1
                    desde=''
                    hasta=''
                    periodo=''
                    # print(Matricula.objects.filter(nivel__periodo__inicio__gte=inicio,nivel__periodo__inicio__lte=fin,nivel__nivelmalla__in=(1,2,3,4,5,6),nivel__carrera__carrera=True).distinct('inscripcion').values('inscripcion').count())
                    if request.POST['periodo'] != '':
                        periodo= Periodo.objects.filter(pk=request.POST['periodo'])[:1].get()
                        inscripid = Matricula.objects.filter(nivel__periodo=periodo,nivel__nivelmalla__in=(1,2,3,4,5,6,10),nivel__carrera__carrera=True).distinct('inscripcion').values('inscripcion')
                        desde=periodo.inicio
                        hasta=periodo.fin
                        pr=True
                    else:
                        # print('fecha')
                        inicio = convertir_fecha( request.POST['inicio'])
                        fin = convertir_fecha(request.POST['fin'])
                        desde=inicio
                        hasta=fin
                        inscripid = Matricula.objects.filter(nivel__periodo__inicio__gte=inicio,nivel__periodo__inicio__lte=fin,nivel__nivelmalla__in=(1,2,3,4,5,6,10),nivel__carrera__carrera=True).distinct('inscripcion').values('inscripcion')
                    # for matricula in Matricula.objects.filter(nivel__periodo=periodo,nivel__nivelmalla__in=(1,2,3,4,5,6),nivel__periodo__tipo__id=2).order_by('id'):

                    for inscripcion in Inscripcion.objects.filter(id__in=inscripid):
                        nivelacademico = ''
                        # print((inscripcion))
                        # inscripcion = matricula.inscripcion
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
                        porcdiscapacidad = ''
                        if inscripcion.nee():
                            if inscripcion.nee().tienediscapacidad:
                                porcdiscapacidad = inscripcion.nee().porcientodiscapacidad
                                carnetdiscapacidad = inscripcion.nee().carnetdiscapacidad
                                if inscripcion.nee().tipodiscapacidad:
                                    try:
                                        discapacidad = elimina_tildes(inscripcion.nee().tipodiscapacidad.nombrematriz)
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

                        etniaId ='NO REGISTRA'
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
                                paisNacionalidadId = 'ECUADOR'
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
                                paisNacionalidadId = 'ARGENTINA'
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
                            nacimiento = str(inscripcion.persona.nacimiento.strftime('%d-%m-%Y'))
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

                        try:
                            direccion = inscripcion.persona.direccion_completa()
                        except:
                            direccion ='ERROR EN DIRECCION'
                        carrera = elimina_tildes(inscripcion.carrera)
                        fechaInicioCarrera=''
                        fechaconvalidacion=''
                        if ConvalidacionInscripcion.objects.filter(record__inscripcion=inscripcion).exists():
                            conval =ConvalidacionInscripcion.objects.filter(record__inscripcion=inscripcion).order_by('id')[:1].get()
                            try:
                                if conval.fecha:
                                    fechaconvalidacion = conval.fecha.strftime('%d-%m-%Y')
                                else:
                                    fechaconvalidacion =str(conval.anno)
                            except:
                                pass
                        else:
                            matfech = Matricula.objects.filter(inscripcion=inscripcion,nivel__nivelmalla__in=(1,2,3,4,5,6,10)).order_by('id')[:1].get()
                            fechaInicioCarrera = matfech.nivel.periodo.inicio.strftime('%d-%m-%Y')
                        try:
                            if not pr:
                                if Matricula.objects.filter(inscripcion=inscripcion,nivel__nivelmalla__in=(1,2,3,4,5,6,10),fecha__gte=desde,fecha__lte=hasta).order_by('-id').exists():
                                    nivelacademico = Matricula.objects.filter(inscripcion=inscripcion,nivel__nivelmalla__in=(1,2,3,4,5,6,10),fecha__gte=desde,fecha__lte=hasta).order_by('-id')[:1].get()
                                    nivelacademico = nivelacademico.nivel.nivelmalla.nombrematriz
                                else:
                                    nivelacademico=''
                            else:
                                if Matricula.objects.filter(inscripcion=inscripcion,nivel__nivelmalla__in=(1,2,3,4,5,6,10),nivel__periodo=periodo).order_by('-id').exists():
                                    nivelacademico = Matricula.objects.filter(inscripcion=inscripcion,nivel__nivelmalla__in=(1,2,3,4,5,6,10),nivel__periodo=periodo).order_by('-id')[:1].get()
                                    nivelacademico = nivelacademico.nivel.nivelmalla.nombrematriz
                                else:
                                    nivelacademico=''
                        except:
                             nivelacademico=''

                        nivelFormacionPadre = ""
                        nivelFormacionMadre = ""
                        if PersonaExtension.objects.filter(persona=inscripcion.persona).exists():
                            personaextension = PersonaExtension.objects.filter(persona=inscripcion.persona)[:1].get()
                            if personaextension.educacionpadre:
                                if personaextension.educacionpadre:
                                    nivelFormacionPadre = personaextension.educacionpadre.nombre

                            if personaextension.educacionmadre:
                                if personaextension.educacionmadre:
                                    nivelFormacionMadre = personaextension.educacionmadre.nombre
                        paisResidencia = "ECUADOR"
                        cantonResidencia = ""
                        if inscripcion.persona.cantonresid:
                            cantonResidencia = elimina_tildes(inscripcion.persona.cantonresid.nombre)
                        ProvinciaResidencia = ""
                        if inscripcion.persona.provinciaresid:
                            ProvinciaResidencia = elimina_tildes(inscripcion.persona.provinciaresid.nombre)
                        cantidadmiembros=''
                        if InscripcionFichaSocioeconomica.objects.filter(inscripcion=inscripcion).exists():
                            inscripcionfichasocioeconomica = InscripcionFichaSocioeconomica.objects.filter(inscripcion=inscripcion)[:1].get()
                            if  inscripcionfichasocioeconomica.cantidadmiembros:
                                cantidadmiembros=inscripcionfichasocioeconomica.cantidadmiembros
                        tipoColegio='NO REGISTRA'
                        if inscripcion.estcolegio:
                            if  inscripcion.estcolegio.tipo:
                                tipoColegio= inscripcion.estcolegio.tipo.nombre
                        if inscripcion.carrera.codigocarrera:
                            codigocarrera=elimina_tildes(inscripcion.carrera.codigocarrera)
                        else:
                            codigocarrera=''
                        ws.write(cont, 0, '')
                        ws.write(cont, 1, codigocarrera)
                        ws.write(cont, 2, '')
                        ws.write(cont, 3, tipoDocumentoId)
                        ws.write(cont, 4, numeroIdentificacion)
                        ws.write(cont, 5, apellido1)
                        ws.write(cont, 6, apellido2)
                        ws.write(cont, 7, nombre)
                        ws.write(cont, 8, sexoId)
                        ws.write(cont, 9, nacimiento)
                        ws.write(cont, 10, paisNacionalidadId)
                        ws.write(cont, 11,discapacidad)
                        ws.write(cont, 12,porcdiscapacidad)
                        ws.write(cont, 13,carnetdiscapacidad)
                        ws.write(cont, 14,etniaId)
                        ws.write(cont, 15, 'NO APLICA')
                        ws.write(cont, 16, direccion)
                        ws.write(cont, 17, email)
                        ws.write(cont, 18, emailinst)
                        ws.write(cont, 19, fechaInicioCarrera)
                        ws.write(cont, 20, fechaconvalidacion)
                        ws.write(cont, 21, paisResidencia)
                        ws.write(cont, 22, ProvinciaResidencia)
                        ws.write(cont, 23, cantonResidencia)
                        ws.write(cont, 24, inscripcion.persona.telefono)
                        ws.write(cont, 25, nivelFormacionPadre)
                        ws.write(cont, 26, nivelFormacionMadre)
                        ws.write(cont, 27, cantidadmiembros)
                        ws.write(cont, 28, tipoColegio)
                        ws.write(cont, 29, 'NINGUNA')
                        ws.write(cont, 30,carrera)
                        ws.write(cont, 31,elimina_tildes(inscripcion.modalidad.nombre))
                        ws.write(cont, 32,nivelacademico)
                        cont=cont+1
                        # print(cont)

                    nombre ='caces_estudiantes_rangofecha'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    return HttpResponse(json.dumps({"result":str(ex)+str(inscripcion)}),content_type="application/json")
        else:
                data = {'title': 'Caces Estudiantes Rango Fecha'}
                addUserData(request,data)
                if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                    reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                    data['reportes'] = reportes
                    data['generarform']= CacesRangoPeriodoForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
                    return render(request ,"reportesexcel/caces_estudiantes_rangofecha.html" ,  data)
                return HttpResponseRedirect("/reporteexcel")


    except Exception as e:
        print((e))
        return HttpResponseRedirect('/?info='+str(e))