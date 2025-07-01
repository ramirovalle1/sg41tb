from datetime import datetime, timedelta
import json
from django.db.models import Q
import xlwt
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from settings import MEDIA_ROOT
from sga.commonviews import addUserData
from sga.models import TituloInstitucion, Grupo,InscripcionGrupo, ViewCursosIngles, ViewCertificacionesIngles, ReporteExcel
from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action :
                try:
                    grupo = Grupo.objects.get(pk=request.POST['grupo'])
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('Listado',cell_overwrite_ok=True)
                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,14, elimina_tildes(tit.nombre), titulo2)
                    ws.write_merge(1, 1,0,14, 'LISTADO DE ALUMNOS INSCRITOS EN CURSOS DE INGLES', titulo2)
                    ws.write(3, 0, 'GRUPO: ', titulo)
                    ws.write(3, 1, elimina_tildes(grupo.nombre))

                    inscripciones = InscripcionGrupo.objects.filter(grupo=grupo).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')
                    asignaturas = ViewCursosIngles.objects.filter(cedula__in=inscripciones.values('inscripcion__persona__cedula')).order_by('asignatura').values('asignatura').distinct('asignatura')
                    columna = 2
                    ws.write(5, 0,  'CEDULA', titulo)
                    ws.write(5, 1,  'NOMBRE', titulo)
                    for c in asignaturas:
                        ws.write(5, columna,  c['asignatura'], titulo)
                        ws.write(5, columna+1,  'ESTADO', titulo)
                        columna = columna+2

                    certificaciones = ViewCertificacionesIngles.objects.filter().order_by('tipo').values('tipo').distinct('tipo')
                    for c in certificaciones:
                        ws.write(5, columna,  c['tipo'], titulo)
                        columna = columna + 1

                    fila = 6
                    for ig in inscripciones:
                        if ig.inscripcion.persona.cedula:
                            identificacion = ig.inscripcion.persona.cedula
                        else:
                            identificacion = ig.inscripcion.persona.pasaporte
                        ws.write(fila, 0, identificacion)
                        ws.write(fila, 1, elimina_tildes(ig.inscripcion.persona.nombre_completo_inverso()))

                        columna = 2
                        for c in asignaturas:
                            if ViewCursosIngles.objects.filter(cedula=identificacion, asignatura=c['asignatura']).exists():
                                curso = ViewCursosIngles.objects.filter(cedula=identificacion, asignatura=c['asignatura'])[:1].get()
                                ws.write(fila, columna, curso.asignatura)
                                ws.write(fila, columna+1,  curso.estado)
                            else:
                                ws.write(fila, columna, 'SIN VER')
                                ws.write(fila, columna+1, '-', titulo2)
                            columna = columna+2

                        for c in certificaciones:
                            if ViewCertificacionesIngles.objects.filter(cedula=identificacion, tipo=c['tipo']).exists():
                                cert = ViewCertificacionesIngles.objects.filter(cedula=identificacion, tipo=c['tipo']).order_by('certificacion')
                                cert_realizadas = ''
                                for cer in cert:
                                    cert_realizadas = cert_realizadas+" "+cer.certificacion
                                ws.write(fila, columna, cert_realizadas)
                            else:
                                ws.write(fila, columna, 'NINGUNA')
                            columna = columna + 1

                        fila = fila + 1

                    nombre ='cursos_ingles'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(ex)
                    return HttpResponse(json.dumps({"result":str(ex) + " "+  str('')}),content_type="application/json")
        else:
            data = {'title': 'Inscripciones en Cursos de Ingles'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                return render(request ,"reportesexcel/inscritos_cursosingles.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))


