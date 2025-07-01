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
from sga.forms import XLSPeriodoForm, RangoGestionForm, RangoCobrosForm
from sga.models import Periodo, convertir_fecha,TituloInstitucion,ReporteExcel,Canton,Provincia,Coordinacion,Matricula,total_matriculadosfil,total_matriculadosfilnullprovin,total_matriculadosfilprovinporcent, Inscripcion, ConvalidacionInscripcion, MateriaAsignada, RetiradoMatricula
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
                    ws.write(2, 0, 'CODIGO_IES', titulo)
                    ws.write(2, 1, 'CODIGO_CARRERA', titulo)
                    ws.write(2, 2, 'CIUDAD_CARRERA', titulo)
                    ws.write(2, 3, 'TIPO_IDENTIFICACION', titulo)
                    ws.write(2, 4, 'IDENTIFICACION', titulo)
                    ws.write(2, 5, 'TOTAL_CREDITOS_APROBADOS', titulo)
                    ws.write(2, 6, 'CREDITOS_APROBADOS', titulo)
                    ws.write(2, 7, 'TIPO_MATRICULA', titulo)
                    ws.write(2, 8, 'PARALELO', titulo)
                    ws.write(2, 9, 'NIVEL_ACADEMICO', titulo)
                    ws.write(2, 10, 'DURACION_PERIODO_ACADEMICO', titulo)
                    ws.write(2, 11, 'NUM_MATERIAS_SEGUNDA_MATRICULA', titulo)
                    ws.write(2, 12, 'NUM_MATERIAS_TERCERA_MATRICULA', titulo)
                    ws.write(2, 13, 'PERDIDA_GRATUIDAD', titulo)
                    ws.write(2, 14, 'PENSION_DIFERENCIADA', titulo)
                    ws.write(2, 15, 'PLAN_CONTINGENCIA', titulo)
                    ws.write(2, 16, 'INGRESO_TOTAL_HOGAR', titulo)
                    ws.write(2, 17, 'ORIGEN_RECURSOS_ESTUDIOS', titulo)
                    ws.write(2, 18, 'TERMINO_PERIODO', titulo)
                    ws.write(2, 19, 'TOTAL_HORAS_APROBADAS', titulo)
                    ws.write(2, 20, 'HORAS_APROBADAS_PERIODO', titulo)
                    ws.write(2, 21, 'MONTO_AYUDA_ECONOMICA', titulo)
                    ws.write(2, 22, 'MONTO_CREDITO_EDUCATIVO', titulo)
                    ws.write(2, 23, 'ESTADO', titulo)
                    ws.write(2, 24, 'CARRERA', titulo)
                    ws.write(2, 25, 'MODALIDAD', titulo)

                    periodo= Periodo.objects.filter(pk=request.POST['periodo'])[:1].get()
                    # inicio = convertir_fecha( request.POST['inicio'])
                    # fin = convertir_fecha(request.POST['fin'])
                    cont = 3
                    c=1
                    # print(Matricula.objects.filter(nivel__periodo__inicio__gte=inicio,nivel__periodo__inicio__lte=fin,nivel__nivelmalla__in=(1,2,3,4,5,6),nivel__carrera__carrera=True).distinct('inscripcion').values('inscripcion').count())
                    # inscripid = Matricula.objects.filter(nivel__periodo__inicio__gte=inicio,nivel__periodo__inicio__lte=fin,nivel__nivelmalla__in=(1,2,3,4,5,6),nivel__carrera__carrera=True).distinct('inscripcion').values('inscripcion')
                    for matricula in Matricula.objects.filter(nivel__periodo=periodo,nivel__nivelmalla__in=(1,2,3,4,5,6,10),nivel__periodo__tipo__id=2).order_by('id'):
                    # for inscripcion in Inscripcion.objects.filter(id__in=inscripid):
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
                        carrera = elimina_tildes(inscripcion.carrera)

                        creditosaprobados =MateriaAsignada.objects.filter(matricula=matricula).aggregate(Sum('materia__creditos'))['materia__creditos__sum']
                        totcreditosaprobados =MateriaAsignada.objects.filter(matricula__inscripcion=matricula.inscripcion).exclude(matricula=matricula).aggregate(Sum('materia__creditos'))['materia__creditos__sum']
                        if matricula.fecha > matricula.nivel.fechatopematricula:
                            tipo = 'EXTRAORDINARIA'
                        else:
                            tipo = 'ORDINARIA'
                        paralelo = matricula.nivel.paralelo
                        nivelacademico = matricula.nivel.nivelmalla.nombrematriz
                        duracionperiodo=''
                        segundamat=0
                        tercermat=0
                        perdida = ''
                        pensiondiferenciada = ''
                        plancontingencia = ''
                        ingresohogar ='NO REGISTRA'
                        personacubre='NO REGISTRA'
                        terminoperiodo = 'SI'
                        horas =MateriaAsignada.objects.filter(matricula=matricula).aggregate(Sum('materia__horas'))['materia__horas__sum']
                        totalhoras =MateriaAsignada.objects.filter(matricula__inscripcion=matricula.inscripcion).exclude(matricula=matricula).aggregate(Sum('materia__horas'))['materia__horas__sum']
                        if InscripcionFichaSocioeconomica.objects.filter(inscripcion=matricula.inscripcion).exists():
                            inscripcionfichasocioeconomica = InscripcionFichaSocioeconomica.objects.filter(inscripcion=matricula.inscripcion)[:1].get()
                            ingresohogar = inscripcionfichasocioeconomica.total_ingresos_sustentahogar()
                            if inscripcionfichasocioeconomica.personacubregasto:
                                personacubre = inscripcionfichasocioeconomica.personacubregasto.nombrematriz
                        estado=''
                        if RetiradoMatricula.objects.filter(nivel=matricula.nivel).exists():
                            terminoperiodo = 'NO'
                            estado= 'RETIRADO'
                        montoayuda = 0
                        montocredito = 0
                        if inscripcion.persona.usuario.is_active:
                            estado='APROBADO'
                        if matricula.inscripcion.carrera.codigocarrera:
                            codigocarrera=elimina_tildes (matricula.inscripcion.carrera.codigocarrera)
                        else:
                            codigocarrera=''
                        ws.write(cont, 0, '')
                        ws.write(cont, 1,codigocarrera)
                        ws.write(cont, 2, '')
                        ws.write(cont, 3, tipoDocumentoId)
                        ws.write(cont, 4, numeroIdentificacion)
                        ws.write(cont, 5, totcreditosaprobados)
                        ws.write(cont, 6, creditosaprobados)
                        ws.write(cont, 7, tipo)
                        ws.write(cont, 8, paralelo)
                        ws.write(cont, 9, nivelacademico)
                        ws.write(cont, 10, duracionperiodo)
                        ws.write(cont, 11,segundamat)
                        ws.write(cont, 12,tercermat)
                        ws.write(cont, 13,perdida)
                        ws.write(cont, 14,pensiondiferenciada)
                        ws.write(cont, 15, plancontingencia)
                        ws.write(cont, 16, ingresohogar)
                        ws.write(cont, 17, personacubre)
                        ws.write(cont, 18, terminoperiodo)
                        ws.write(cont, 19, totalhoras)
                        ws.write(cont, 20, horas)
                        ws.write(cont, 21, montoayuda)
                        ws.write(cont, 22, montocredito)
                        ws.write(cont, 23, estado)
                        ws.write(cont, 24,carrera)
                        ws.write(cont, 25,elimina_tildes(inscripcion.modalidad.nombre))
                        cont=cont+1
                        print(cont)
                    nombre ='caces_estudiantes_periodo'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    return HttpResponse(json.dumps({"result":str(ex)+str(inscripcion)}),content_type="application/json")
        else:
                data = {'title': 'Caces Estudiantes Periodo'}
                addUserData(request,data)
                if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                    reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                    data['reportes'] = reportes
                    data['generarform']= XLSPeriodoForm()
                    return render(request ,"reportesexcel/caces_estudiantes_periodo.html" ,  data)
                return HttpResponseRedirect("/reporteexcel")


    except Exception as e:
        print((e))
        return HttpResponseRedirect('/?info='+str(e))