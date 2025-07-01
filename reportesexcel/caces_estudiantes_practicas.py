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
from sga.models import Periodo, convertir_fecha,TituloInstitucion,ReporteExcel,Canton,Provincia,Coordinacion,Matricula,total_matriculadosfil,total_matriculadosfilnullprovin,total_matriculadosfilprovinporcent, Inscripcion, ConvalidacionInscripcion, InscripcionPracticas
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
                    periodo=None
                    inicio=''
                    fin=''
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
                    ws.write(2, 5, 'NOMBRE_INSTITUCION', titulo)
                    ws.write(2, 6, 'TIPO_INSTITUCION', titulo)
                    ws.write(2, 7, 'FECHA_INICIO', titulo)
                    ws.write(2, 8, 'FECHA_FIN', titulo)
                    ws.write(2, 9, 'NUMERO_HORAS', titulo)
                    ws.write(2, 10, 'CAMPO_ESPECIFICO', titulo)
                    ws.write(2, 11, 'IDENTIFICACION_DOCENTE_TUTOR', titulo)
                    ws.write(2, 12, 'CARRERA', titulo)
                    ws.write(2, 13, 'MODALIDAD', titulo)

                    # periodo= Periodo.objects.filter(pk=request.POST['periodo'])[:1].get()

                    cont = 3
                    c=1
                    # print(Matricula.objects.filter(nivel__periodo__inicio__gte=inicio,nivel__periodo__inicio__lte=fin,nivel__nivelmalla__in=(1,2,3,4,5,6),nivel__carrera__carrera=True).distinct('inscripcion').values('inscripcion').count())
                    print('prac')
                    if request.POST['periodo'] != '':
                        periodo= Periodo.objects.filter(pk=request.POST['periodo'])[:1].get()
                        inscripid = Matricula.objects.filter(nivel__nivelmalla__in=(1,2,3,4,5,6,10),nivel__carrera__carrera=True).distinct('inscripcion').values('inscripcion')
                        # inscripid = Matricula.objects.filter(nivel__periodo=periodo,nivel__nivelmalla__in=(1,2,3,4,5,6,10),nivel__carrera__carrera=True).distinct('inscripcion').values('inscripcion')
                        # practicas = InscripcionPracticas.objects.filter(Q(inicio__gte=periodo.inicio, inicio__lte=periodo.fin) | Q(fin__gte=periodo.inicio, fin__lte=periodo.fin)| Q(inicio__lte=periodo.fin, fin__gte=periodo.inicio),inscripcion__id__in=inscripid)
                        practicas = InscripcionPracticas.objects.filter(Q(inicio__lte=periodo.inicio, fin__gte=periodo.inicio) | Q(inicio__lte=periodo.fin, fin__gte=periodo.fin)| Q(inicio__gte=periodo.inicio, fin__lte=periodo.fin),inscripcion__id__in=inscripid)
                    else:
                        print('fecha')
                        inicio = convertir_fecha( request.POST['inicio'])
                        fin = convertir_fecha(request.POST['fin'])
                        inscripid = Matricula.objects.filter(nivel__periodo__inicio__gte=inicio,nivel__periodo__inicio__lte=fin,nivel__nivelmalla__in=(1,2,3,4,5,6,10),nivel__carrera__carrera=True).distinct('inscripcion').values('inscripcion')
                        practicas = InscripcionPracticas.objects.filter(Q(inicio__gte=inicio, inicio__lte=fin) | Q(fin__gte=inicio, fin__lte=fin)| Q(inicio__lte=fin, fin__gte=inicio),inscripcion__id__in=inscripid)
                    # for matricula in Matricula.objects.filter(nivel__periodo=periodo,nivel__nivelmalla__in=(1,2,3,4,5,6),nivel__periodo__tipo__id=2).order_by('id'):

                    for p in practicas:
                        inscripcion = p.inscripcion
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
                        if periodo:
                            matricula = Matricula.objects.filter(inscripcion=inscripcion)[:1].get()
                        else:
                            matricula=Matricula.objects.filter(inscripcion=inscripcion,nivel__periodo__inicio__gte=inicio,nivel__periodo__inicio__lte=fin,nivel__nivelmalla__in=(1,2,3,4,5,6,10),nivel__carrera__carrera=True)[:1].get()
                        nombreins = ''
                        tipoins = ''
                        fechainicio = ''
                        fechafin = ''
                        campoespecifico = ''
                        horaspracticas = ''
                        identificaciondocente = ''
                        carrera = elimina_tildes(matricula.inscripcion.carrera)

                        tienepractica = 1
                        practica = p
                        nombreins = practica.lugar
                        tipoins = ''
                        fechainicio=practica.inicio.strftime('%d-%m-%Y')
                        fechafin=practica.fin.strftime('%d-%m-%Y')
                        horaspracticas = practica.horas
                        campoespecifico = ''
                        identificaciondocente = practica.profesor.persona.cedula
                        if matricula.inscripcion.carrera.codigocarrera:
                            codigocarrera=elimina_tildes(matricula.inscripcion.carrera.codigocarrera)
                        else:
                            codigocarrera=''
                        ws.write(cont, 0, '')
                        ws.write(cont, 1, codigocarrera)
                        ws.write(cont, 2, '')
                        ws.write(cont, 3, tipoDocumentoId)
                        ws.write(cont, 4, numeroIdentificacion)
                        ws.write(cont, 5, nombreins)
                        ws.write(cont, 6, tipoins)
                        ws.write(cont, 7, fechainicio)
                        ws.write(cont, 8, fechafin)
                        ws.write(cont, 9, horaspracticas)
                        ws.write(cont, 10, campoespecifico)
                        ws.write(cont, 11,identificaciondocente)
                        ws.write(cont, 12,carrera)
                        ws.write(cont, 13,elimina_tildes(matricula.inscripcion.modalidad.nombre))
                        cont=cont+1
                        print(cont)

                    nombre ='caces_estudiantes_practicas'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    return HttpResponse(json.dumps({"result":str(ex)+str(inscripcion)}),content_type="application/json")
        else:
                data = {'title': 'Caces Estudiantes Practicas'}
                addUserData(request,data)
                if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                    reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                    data['reportes'] = reportes
                    data['generarform']= CacesRangoPeriodoForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
                    return render(request ,"reportesexcel/caces_estudiantes_practicas.html" ,  data)
                return HttpResponseRedirect("/reporteexcel")


    except Exception as e:
        print((e))
        return HttpResponseRedirect('/?info='+str(e))