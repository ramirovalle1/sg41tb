from datetime import datetime,timedelta
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
from settings import UTILIZA_GRUPOS_ALUMNOS, EMAIL_ACTIVE,MEDIA_ROOT, ASIG_VINCULACION, ASIG_PRATICA
from sga.commonviews import addUserData, ip_client_address
from sga.forms import FacultadRangoFechasExcelForm
from sga.models import convertir_fecha,TituloInstitucion,ReporteExcel,Coordinacion,Carrera,LeccionGrupo,Profesor

from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            inicio = convertir_fecha(request.POST['desde'])
            fin = convertir_fecha(request.POST['hasta'])
            coordinacion = Coordinacion.objects.get(pk=request.POST['coordinacion'])
            carreras = Carrera.objects.filter(coordinacion__id = coordinacion.id).order_by('carrera__nombre').values('id')
            cont = 5
            prof = LeccionGrupo.objects.filter(materia__nivel__periodo__activo=True,profesor__activo=True,fecha__gte=inicio,fecha__lte=fin,materia__nivel__carrera__in=carreras,abierta=False,cierresistema=False,minutoscierre__gte=5).order_by('profesor__persona__apellido1','profesor__persona__apellido2','profesor__persona__nombres').values('profesor')
            profesor = Profesor.objects.filter(id__in=prof).order_by('persona__apellido1','persona__apellido2','persona__nombres')

            if action :
                wb = xlwt.Workbook()
                ws = wb.add_sheet('Registros',cell_overwrite_ok=True)
                try:
                    m = 14
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo3 = xlwt.easyxf('font: name Times New Roman; align: wrap on, vert centre, horiz center')
                    subtitulo.font.height = 20*10

                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,m, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,m,'LISTADO DE CIERRE DE CLASES ANTICIPADO REALIZADO POR DOCENTES POR FACULTAD',titulo2)
                    ws.write(3, 0,'Desde:   ' +str(inicio.date()), subtitulo)
                    ws.write(3, 1,'Hasta:   ' +str(fin.date()), subtitulo)
                    ws.write(4, 0,'Facultad:' +str(coordinacion.nombre), subtitulo)

                    cont = cont+2
                    ws.write(cont, 0, 'IDENTIFICACION', titulo)
                    ws.write(cont, 1, 'DOCENTE', titulo)
                    ws.write(cont, 2, 'CARRERA', titulo)
                    ws.write(cont, 3, 'NIVEL', titulo)
                    ws.write(cont, 4, 'PARALELO', titulo)
                    ws.write(cont, 5, 'ASIGNATURA', titulo)
                    ws.write(cont, 6, 'FECHA APERTURA', titulo)
                    ws.write(cont, 7, 'HORA APERTURA', titulo)
                    ws.write(cont, 8, 'FECHA CIERRE', titulo)
                    ws.write(cont, 9, 'HORA CIERRE', titulo)
                    ws.write(cont, 10, 'TURNO ENTRADA', titulo)
                    ws.write(cont, 11, 'TURNO SALIDA', titulo)
                    ws.write(cont, 12, 'HORAS TURNO', titulo)
                    ws.write(cont, 13, 'MINUTOS FALTANTES', titulo)
                    ws.write(cont, 14, 'VALOR HORA', titulo)
                    ws.write(cont, 15, 'A DESCONTAR', titulo)

                    fila = 8
                    detalle=3

                    for p in profesor:
                        # print(p)
                        identificacion=''
                        nombrecompleto=''
                        totdctodocente=0
                        clases=0
                        try:
                            if p.persona.cedula:
                                identificacion=elimina_tildes(p.persona.cedula)
                            else:
                                identificacion=elimina_tildes(p.persona.pasaporte)
                        except:
                            identificacion=''
                        try:
                            nombrecompleto=elimina_tildes(p.persona.nombre_completo_inverso())
                        except:
                            nombrecompleto=''

                        for lg in LeccionGrupo.objects.filter(materia__nivel__periodo__activo=True,profesor=p,fecha__gte=inicio,fecha__lte=fin,materia__nivel__carrera__in=carreras,abierta=False,cierresistema=False,minutoscierre__gte=5).order_by('fecha', 'horaentrada'):
                            try:
                                if lg.fecha==lg.fechasalida and lg.horasalida < lg.turno.termina:
                                    # print(lg)
                                    clases=clases+1
                                    carrera=''
                                    nivel=''
                                    paralelo=''
                                    asignatura=''
                                    fechaabre=''
                                    horaabre=''
                                    fechacierre=''
                                    horacierre=''
                                    hentradaturno=''
                                    hsalidaturno=''
                                    horasturno=0
                                    minutosclases=0
                                    costohora=0
                                    valordescuento=0
                                    try:
                                        carrera = elimina_tildes(lg.materia.nivel.carrera.nombre)
                                    except:
                                        carrera = ''
                                    try:
                                        nivel = elimina_tildes(lg.materia.nivel.nivelmalla)
                                    except:
                                        nivel = ''
                                    try:
                                        paralelo = elimina_tildes(lg.materia.nivel.grupo.nombre)
                                    except:
                                        paralelo = ''
                                    try:
                                        asignatura = elimina_tildes(lg.materia.asignatura.nombre)
                                    except:
                                        asignatura = ''
                                    try:
                                        fechaabre=str(lg.fecha)
                                        horaabre=str(lg.horaentrada)
                                        fechacierre=str(lg.fechasalida)
                                        horacierre=str(lg.horasalida)
                                        hentradaturno=str(lg.turno.comienza)
                                        hsalidaturno=str(lg.turno.termina)
                                        horasturno=lg.turno.horas
                                        minutosclases=lg.minutoscierre
                                        costohora=(lg.costo_profesor_dia(lg.fecha)/horasturno)
                                        valordescuento=Decimal((minutosclases*costohora)/60).quantize(Decimal(10)**-2)
                                        totdctodocente=totdctodocente+valordescuento
                                    except:
                                        fechaabre=''
                                        horaabre=''
                                        fechacierre=''
                                        horacierre=''
                                        hentradaturno=''
                                        hsalidaturno=''
                                        horasturno=''

                                    ws.write(fila,0,(identificacion),subtitulo3)
                                    ws.write(fila,1,(nombrecompleto),subtitulo3)
                                    ws.write(fila,2,carrera,subtitulo3)
                                    ws.write(fila,3,nivel,subtitulo3)
                                    ws.write(fila,4,paralelo,subtitulo3)
                                    ws.write(fila,5,asignatura,subtitulo3)
                                    ws.write(fila,6,fechaabre,subtitulo3)
                                    ws.write(fila,7,horaabre,subtitulo3)
                                    ws.write(fila,8,fechacierre,subtitulo3)
                                    ws.write(fila,9,horacierre,subtitulo3)
                                    ws.write(fila,10,hentradaturno,subtitulo3)
                                    ws.write(fila,11,hsalidaturno,subtitulo3)
                                    ws.write(fila,12,str(horasturno),subtitulo3)
                                    ws.write(fila,13,minutosclases,subtitulo3)
                                    ws.write(fila,14,costohora,subtitulo3)
                                    ws.write(fila,15,valordescuento,subtitulo3)
                                    fila=fila+1
                            except:
                                print((identificacion))
                                pass
                        if clases>0:
                            ws.write(fila, 0, 'TOTAL CLASES', titulo)
                            ws.write(fila, 1, nombrecompleto, titulo)
                            ws.write(fila, 2, clases, titulo)
                            ws.write(fila, 14,'TOTAL', titulo)
                            ws.write(fila, 15, totdctodocente, titulo)
                            fila=fila+1
                    detalle = detalle + fila
                    ws.write(detalle,0, "Fecha Impresion", subtitulo)
                    ws.write(detalle,1, str(datetime.now()), subtitulo)
                    ws.write(fila+5,0, "Usuario", subtitulo)
                    ws.write(fila+6,1, str(request.user), subtitulo)

                except Exception as ex:
                    print(str(ex))
                    pass
                nombre ='cierreclases_docentes'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

        else:
            data = {'title': 'Cierre Clases Realizado por Docentes por Facultad'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform']=FacultadRangoFechasExcelForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
                return render(request ,"reportesexcel/cierreclases_pordocentes.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

