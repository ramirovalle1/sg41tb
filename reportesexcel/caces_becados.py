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
from sga.models import Periodo, convertir_fecha,TituloInstitucion,ReporteExcel,Canton,Provincia,Coordinacion,Matricula,total_matriculadosfil,total_matriculadosfilnullprovin,total_matriculadosfilprovinporcent, Inscripcion, ConvalidacionInscripcion, DetalleRubrosBeca
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
                    periodo=None
                    inicio=''
                    fin=''
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
                    ws.write(2, 5, 'CODIGO_BECA', titulo)
                    ws.write(2, 6, 'ANIO', titulo)
                    ws.write(2, 7, 'FECHA_INICIO_PERIODO_ACADEMICO', titulo)
                    ws.write(2, 8, 'FECHA_FIN_PERIODO_ACADEMICO', titulo)
                    ws.write(2, 9, 'TIPO_AYUDA ', titulo)
                    ws.write(2, 10, 'MOTIVO_BECA ', titulo)
                    ws.write(2, 11, 'OTRO_MOTIVO ', titulo)
                    ws.write(2, 12, 'MONTO RECIBIDO ', titulo)
                    ws.write(2, 13, 'PORCENTAJE_VALOR_ARANCEL', titulo)
                    ws.write(2, 14, 'PORCENTAJE_MANUTENCION', titulo)
                    ws.write(2, 15, 'TIPO_FINANCIAMIENTO', titulo)
                    ws.write(2, 16, 'CARRERA', titulo)
                    ws.write(2, 17, 'PRIMER_APELLIDO', titulo)
                    ws.write(2, 18, 'SEGUNDO_APELLIDO', titulo)
                    ws.write(2, 19, 'NOMBRES', titulo)
                    ws.write(2, 20, 'MODALIDAD', titulo)


                    # periodo= Periodo.objects.filter(pk=request.POST['periodo'])[:1].get()

                    cont = 3
                    c=1
                    # print(Matricula.objects.filter(nivel__periodo__inicio__gte=inicio,nivel__periodo__inicio__lte=fin,nivel__nivelmalla__in=(1,2,3,4,5,6),nivel__carrera__carrera=True).distinct('inscripcion').values('inscripcion').count())
                    if request.POST['periodo'] != '':
                        periodo= Periodo.objects.filter(pk=request.POST['periodo'])[:1].get()
                        inscripid = Matricula.objects.filter(becado=True,nivel__periodo=periodo,nivel__nivelmalla__in=(1,2,3,4,5,6,10),nivel__carrera__carrera=True).distinct('inscripcion').values('inscripcion')
                    else:
                        print('fecha')
                        inicio = convertir_fecha( request.POST['inicio'])
                        fin = convertir_fecha(request.POST['fin'])
                        inscripid = Matricula.objects.filter(becado=True,nivel__periodo__inicio__gte=inicio,nivel__periodo__inicio__lte=fin,nivel__nivelmalla__in=(1,2,3,4,5,6,10),nivel__carrera__carrera=True).distinct('inscripcion').values('inscripcion')
                    codigocarrera=''
                    # for matricula in Matricula.objects.filter(nivel__periodo=periodo,nivel__nivelmalla__in=(1,2,3,4,5,6),nivel__periodo__tipo__id=2).order_by('id'):
                    for inscripcion in Inscripcion.objects.filter(id__in=inscripid):
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
                        if periodo:
                            matricula = Matricula.objects.filter(inscripcion=inscripcion,nivel__periodo=periodo)[:1].get()
                        else:
                            matricula=Matricula.objects.filter(inscripcion=inscripcion,nivel__periodo__inicio__gte=inicio,nivel__periodo__inicio__lte=fin,nivel__nivelmalla__in=(1,2,3,4,5,6),nivel__carrera__carrera=True)[:1].get()
                        codigobeca = 'S'+str(inscripcion.numerom)
                        anio = ''
                        tipoayuda=''
                        tipobeca=''
                        montorecibido=''
                        porcentaje=''
                        if matricula.becado:

                            anio = matricula.fecha.year
                            if matricula.porcientobeca == 100:
                                tipoayuda = 'BECA COMPLETA'
                            else:
                                tipoayuda = 'BECA PARCIAL'
                            tipobeca =''
                            if matricula.tipobeca:
                                # tipobeca = matricula.tipobeca.nombre
                                tipobeca = matricula.motivobeca.nombrematriz
                            montorecibido =DetalleRubrosBeca.objects.filter(matricula=matricula).aggregate(Sum('descuento'))['descuento__sum']
                            porcentaje = matricula.porcientobeca
                        inicioperiodo=matricula.nivel.periodo.inicio.strftime('%d-%m-%Y')
                        finperiodo=matricula.nivel.periodo.fin.strftime('%d-%m-%Y')
                        carrera = elimina_tildes(inscripcion.carrera)
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
                        if inscripcion.modalidad:
                            modalidad=inscripcion.modalidad.nombre
                        else:
                            modalidad=''
                        if inscripcion.carrera.codigocarrera:
                            codigocarrera=elimina_tildes(inscripcion.carrera.codigocarrera)
                        else:
                            codigocarrera=''
                        ws.write(cont, 0, '')
                        ws.write(cont, 1, codigocarrera)
                        ws.write(cont, 2, '')
                        ws.write(cont, 3, tipoDocumentoId)
                        ws.write(cont, 4, numeroIdentificacion)
                        ws.write(cont, 5, codigobeca)
                        ws.write(cont, 6, anio)
                        ws.write(cont, 7, inicioperiodo)
                        ws.write(cont, 8, finperiodo)
                        ws.write(cont, 9, tipoayuda)
                        ws.write(cont, 10, tipobeca)
                        ws.write(cont, 11,'')
                        ws.write(cont, 12,montorecibido)
                        ws.write(cont, 13,porcentaje)
                        ws.write(cont, 14,'')
                        ws.write(cont, 15, '')
                        ws.write(cont, 16,carrera)
                        ws.write(cont, 17, apellido1)
                        ws.write(cont, 18, apellido2)
                        ws.write(cont, 19, nombre)
                        ws.write(cont, 20, modalidad)
                        cont=cont+1
                        print(cont)

                    nombre ='caces_becados'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    return HttpResponse(json.dumps({"result":str(ex)+str(inscripcion)}),content_type="application/json")
        else:
                data = {'title': 'Caces Becados'}
                addUserData(request,data)
                if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                    reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                    data['reportes'] = reportes
                    data['generarform']= CacesRangoPeriodoForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
                    return render(request ,"reportesexcel/caces_becados.html" ,  data)
                return HttpResponseRedirect("/reporteexcel")


    except Exception as e:
        print((e))
        return HttpResponseRedirect('/?info='+str(e))