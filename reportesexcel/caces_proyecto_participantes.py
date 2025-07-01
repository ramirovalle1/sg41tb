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
from sga.models import Periodo, convertir_fecha,TituloInstitucion,ReporteExcel,Canton,Provincia,Coordinacion,Matricula,total_matriculadosfil,total_matriculadosfilnullprovin,total_matriculadosfilprovinporcent, Inscripcion, ConvalidacionInscripcion, MateriaAsignada, RetiradoMatricula, ActividadVinculacion, EstudianteVinculacion, Programa, DocenteVinculacion, Profesor, Persona
from sga.reportes import elimina_tildes
from socioecon.models import InscripcionFichaSocioeconomica


@login_required(redirect_field_name='ret', login_url='/login')
def view(request):

    """

    :param request:
    :return:
    """
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
                    ws.write_merge(0, 0, 0, 10,)
                    ws.write_merge(1, 1, 0, 10,)
                    ws.write (0, 0, 'INSTITUTO TECNOLOGICO BOLIVARIANO',center )
                    ws.write(2, 0, 'CODIGO_IES', titulo)
                    ws.write(2, 1, 'CODIGO', titulo)
                    ws.write(2, 2, 'NOMBRE', titulo)
                    ws.write(2, 3, 'TIPO_PROYECTOS', titulo)
                    ws.write(2, 4, 'TIPO_PARTICIPANTE', titulo)
                    ws.write(2, 5, 'IDENTIFICACION_CODIGO', titulo)
                    ws.write(2, 6, 'HORAS', titulo)
                    ws.write(2, 7, 'GRUPO_INVESTIGACION', titulo)


                    periodo= Periodo.objects.filter(pk=request.POST['periodo'])[:1].get()
                    ws.write (1, 0, 'Periodo: ' + str(periodo.nombre),center )
                    # inicio = convertir_fecha( request.POST['inicio'])
                    # fin = convertir_fecha(request.POST['fin'])
                    cont = 3
                    c=1
                    # print(Matricula.objects.filter(nivel__periodo__inicio__gte=inicio,nivel__periodo__inicio__lte=fin,nivel__nivelmalla__in=(1,2,3,4,5,6),nivel__carrera__carrera=True).distinct('inscripcion').values('inscripcion').count())
                    # inscripid = Matricula.objects.filter(nivel__periodo__inicio__gte=inicio,nivel__periodo__inicio__lte=fin,nivel__nivelmalla__in=(1,2,3,4,5,6),nivel__carrera__carrera=True).distinct('inscripcion').values('inscripcion')
                    listaprograma=[]
                    id_estudiantes = EstudianteVinculacion.objects.filter(Q(actividad__inicio__gte=periodo.inicio, actividad__inicio__lte=periodo.fin) | Q(actividad__fin__gte=periodo.inicio, actividad__fin__lte=periodo.fin)| Q(actividad__inicio__lte=periodo.fin, actividad__fin__gte=periodo.inicio)).distinct('inscripcion').values('inscripcion')
                    # print(len(id_estudiantes))
                    for matricula in Matricula.objects.filter(nivel__periodo=periodo,nivel__nivelmalla__in=(1,2,3,4,5,6,10),nivel__periodo__tipo__id=2,inscripcion__id__in=id_estudiantes).order_by('id'):

                    # for inscripcion in Inscripcion.objects.filter(id__in=inscripid):
                        inscripcion = matricula.inscripcion
                        if  EstudianteVinculacion.objects.filter(Q(actividad__inicio__gte=periodo.inicio, actividad__inicio__lte=periodo.fin) | Q(actividad__fin__gte=periodo.inicio, actividad__fin__lte=periodo.fin)| Q(actividad__inicio__lte=periodo.fin, actividad__fin__gte=periodo.inicio),inscripcion=inscripcion).exclude(actividad__programa=None).exists():
                            proyectosid = EstudianteVinculacion.objects.filter(Q(actividad__inicio__gte=periodo.inicio, actividad__inicio__lte=periodo.fin) | Q(actividad__fin__gte=periodo.inicio, actividad__fin__lte=periodo.fin)| Q(actividad__inicio__lte=periodo.fin, actividad__fin__gte=periodo.inicio),inscripcion=inscripcion).exclude(actividad__programa=None).distinct('actividad__programa').values('actividad__programa')
                            for p in Programa.objects.filter(id__in=proyectosid):
                                if not p.id in listaprograma:
                                    listaprograma.append(p.id)
                                nombre = elimina_tildes(p.nombre)
                                tipo=''
                                tipoparticipante = 'ESTUDIANTE'
                                horasestudiante =  EstudianteVinculacion.objects.filter(Q(actividad__inicio__gte=periodo.inicio, actividad__inicio__lte=periodo.fin) | Q(actividad__fin__gte=periodo.inicio, actividad__fin__lte=periodo.fin)| Q(actividad__inicio__lte=periodo.fin, actividad__fin__gte=periodo.inicio),inscripcion=inscripcion,actividad__programa=p).aggregate(Sum('horas'))['horas__sum']

                                # iddocentes =  DocenteVinculacion.objects.filter(Q(actividad__inicio__gte=periodo.inicio, actividad__inicio__lte=periodo.fin) | Q(actividad__fin__gte=periodo.inicio, actividad__fin__lte=periodo.fin)| Q(actividad__inicio__lte=periodo.fin, actividad__fin__gte=periodo.inicio),actividad__programa=p).distinct('persona').values('persona')

                                grupoinvestigacion=''
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
                                if inscripcion.carrera.codigocarrera:
                                    codigocarrera = elimina_tildes(inscripcion.carrera.codigocarrera)
                                else:
                                    codigocarrera = ''

                                ws.write(cont, 0, '')
                                ws.write(cont, 1, codigocarrera)
                                ws.write(cont, 2,nombre)
                                ws.write(cont, 3, '')
                                ws.write(cont, 4, tipoparticipante)
                                ws.write(cont, 5, numeroIdentificacion)
                                ws.write(cont, 6, horasestudiante)
                                ws.write(cont, 7,'')


                                cont=cont+1

                                print(cont)
                    for programa in Programa.objects.filter(id__in=listaprograma):
                        docentesid=DocenteVinculacion.objects.filter(Q(actividad__inicio__gte=periodo.inicio, actividad__inicio__lte=periodo.fin) | Q(actividad__fin__gte=periodo.inicio, actividad__fin__lte=periodo.fin)| Q(actividad__inicio__lte=periodo.fin, actividad__fin__gte=periodo.inicio),actividad__programa=programa).distinct('persona').values('persona')

                        for profesor in Persona.objects.filter(id__in=docentesid):
                            horasdocente = DocenteVinculacion.objects.filter(Q(actividad__inicio__gte=periodo.inicio, actividad__inicio__lte=periodo.fin) | Q(actividad__fin__gte=periodo.inicio, actividad__fin__lte=periodo.fin)| Q(actividad__inicio__lte=periodo.fin, actividad__fin__gte=periodo.inicio),actividad__programa=programa,persona=profesor).aggregate(Sum('horas'))['horas__sum']
                            nombre = elimina_tildes(programa.nombre)
                            tipo=''
                            tipoparticipante = 'DOCENTE'
                            if profesor.pasaporte:
                                tipoDocumentoId = 'PASAPORTE'
                                try:
                                    numeroIdentificacion = profesor.pasaporte
                                except:
                                    numeroIdentificacion= 'ERROR AL OBTENER PASAPORTE '
                            else:
                                tipoDocumentoId = 'CEDULA'
                                try:
                                    numeroIdentificacion = profesor.cedula
                                except:
                                    numeroIdentificacion= 'ERROR AL OBTENER CEDULA '
                            ws.write(cont, 0, '')
                            ws.write(cont, 1, '')
                            ws.write(cont, 2,nombre)
                            ws.write(cont, 3, '')
                            ws.write(cont, 4, tipoparticipante)
                            ws.write(cont, 5, numeroIdentificacion)
                            ws.write(cont, 6, horasdocente)
                            ws.write(cont, 7,'')

                            cont=cont+1
                    nombre ='caces_proyecto_participantes'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(ex)
                    return HttpResponse(json.dumps({"result":str(ex)+str(inscripcion)}),content_type="application/json")
        else:
                data = {'title': 'Caces Proyecto Participantes'}
                addUserData(request,data)
                if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                    reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                    data['reportes'] = reportes
                    data['generarform']= XLSPeriodoForm()
                    return render(request ,"reportesexcel/caces_proyecto_participantes.html" ,  data)
                return HttpResponseRedirect("/reporteexcel")


    except Exception as e:
        print((e))
        return HttpResponseRedirect('/?info='+str(e))