from datetime import datetime
import json
import xlwt

from django.contrib.auth.decorators import login_required

from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from settings import MEDIA_ROOT
from sga.commonviews import addUserData, ip_client_address
from sga.forms import RangoPagoTarjetasForm, CoordinacionForm
from sga.models import TituloInstitucion,ReporteExcel,Graduado,PerfilInscripcion, convertir_fecha, Absentismo, Coordinacion, MateriaAsignada, Carrera, Inscripcion, Nivel, Matricula
from socioecon.models import  InscripcionFichaSocioeconomica
from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action :
                try:
                    m = 5
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10

                    coordinacion = Coordinacion.objects.get(pk=request.POST['coordinacion'])
                    carreras = coordinacion.carrera.filter(carrera=True).order_by('id').exclude(validacionprofesional=True)
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('DEUDA ALUMNOS',cell_overwrite_ok=True)
                    fila=3

                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,6, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,6, 'LISTADO DEUDA DE ALUMNOS', titulo2)

                    ws.write(fila, 0,'CARRERA', titulo)
                    ws.write(fila, 1,'GRUPO', titulo)
                    ws.write(fila, 2,'NIVEL', titulo)
                    ws.write(fila, 3,'ALUMNO', titulo)
                    ws.write(fila, 4,'CEDULA', titulo)
                    ws.write(fila, 5,'TELEFONO', titulo)
                    ws.write(fila, 6,'DEUDA', titulo)

                    for c in carreras:
                        if c.existencias_nivel():
                            fila = fila+1
                            nivel = ''
                            nivelmalla = ''
                            identificacion = ''
                            telefono = ''


                            matriculas = Matricula.objects.filter(inscripcion__carrera=c, inscripcion__persona__usuario__is_active=True, nivel__cerrado=False).order_by('nivel__paralelo','inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')
                            for i in matriculas:
                                deuda = 0
                                try:
                                    if i.inscripcion.ultima_matricula_pararetiro():
                                        nivel = i.inscripcion.ultima_matricula_pararetiro().nivel.paralelo
                                        nivelmalla = i.inscripcion.ultima_matricula_pararetiro().nivel.nivelmalla.nombre
                                except:
                                    pass
                                try:
                                    if i.inscripcion.persona.cedula:
                                        identificacion = elimina_tildes(i.inscripcion.persona.cedula)
                                    else:
                                        identificacion = elimina_tildes(i.inscripcion.persona.pasaporte)
                                except: pass
                                try:
                                    if i.inscripcion.persona.telefono:
                                        telefono = elimina_tildes(i.inscripcion.persona.telefono)
                                except:
                                    pass
                                try:
                                    if i.inscripcion.adeuda_a_la_fecha():
                                        deuda = i.inscripcion.adeuda_a_la_fecha()
                                except:
                                    pass
                                try:
                                    nombre = elimina_tildes(i.inscripcion.persona.nombre_completo_inverso())
                                except:
                                    nombre = ''

                                ws.write(fila, 0, elimina_tildes(c.nombre), subtitulo)
                                ws.write(fila, 1, nivel, subtitulo)
                                ws.write(fila, 2, nivelmalla, subtitulo)
                                ws.write(fila, 3, nombre, subtitulo)
                                ws.write(fila, 4, identificacion, subtitulo)
                                ws.write(fila, 5, telefono, subtitulo)
                                ws.write(fila, 6, deuda, subtitulo)

                                fila = fila+1

                            ws.write(fila+1, 0, "Fecha Impresion", subtitulo)
                            ws.write(fila+1, 2, str(datetime.now()), subtitulo)
                            ws.write(fila+2, 0, "Usuario", subtitulo)
                            ws.write(fila+2, 2, str(request.user), subtitulo)

                    nombre ='deuda_inscripciones_xfacultad'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")
                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)+" "+str(i)}),content_type="application/json")

        else:
            data = {'title': 'Deudas de Alumnos por Facultad'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform'] = CoordinacionForm
                return render(request ,"reportesexcel/xls_deudasinscripciones_xcoordinacion.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

