from datetime import datetime
import json
import xlwt

from django.contrib.auth.decorators import login_required

from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from settings import MEDIA_ROOT
from sga.commonviews import addUserData, ip_client_address
from sga.forms import RangoPagoTarjetasForm, CoordinacionForm,CarrerasporCoordinacionForm
from sga.models import TituloInstitucion,ReporteExcel,Graduado,PerfilInscripcion, convertir_fecha, Absentismo, Coordinacion, MateriaAsignada, Carrera, Inscripcion, Nivel, Periodo, ProfesorMateria
from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action == 'generarexcel' :
                try:
                    m = 5
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10

                    if request.POST['carrera']!='':
                        carrera = request.POST['carrera']
                        carrera = Carrera.objects.filter(pk=carrera)[:1].get()
                    else:
                        carrera=''

                    if request.POST['periodo']!='':
                        periodo = request.POST['periodo']
                        periodos = Periodo.objects.filter(pk=periodo)
                    else:
                        periodos=Periodo.objects.filter(activo=True).order_by('-id')

                    coordinacion = Coordinacion.objects.get(pk=request.POST['coordinacion'])

                    if carrera!='':
                        carreras = coordinacion.carrera.filter(carrera=True,pk=carrera.id).order_by('id').exclude(validacionprofesional=True)
                    else:
                        carreras = coordinacion.carrera.filter(carrera=True).order_by('id').exclude(validacionprofesional=True)
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('ASISTENCIAS',cell_overwrite_ok=True)
                    fila=3

                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,8, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,8, 'LISTADO ASISTENCIAS DE ALUMNOS', titulo2)

                    for c in carreras:
                        if c.existencias_nivel():
                            fila = fila+1
                            nivel = ''
                            nivelmalla = ''
                            identificacion = ''
                            telefono = ''
                            materia = ''
                            profesor=''
                            asistencia = 0
                            for periodo in  periodos:
                                # mat_asignadas = MateriaAsignada.objects.filter(matricula__inscripcion__carrera=c, matricula__inscripcion__persona__usuario__is_active=True, matricula__nivel__cerrado=False).order_by('matricula__nivel__paralelo','materia__asignatura__nombre','matricula__inscripcion__persona__apellido1','matricula__inscripcion__persona__apellido2','matricula__inscripcion__persona__nombres')
                                mat_asignadas = MateriaAsignada.objects.filter(matricula__inscripcion__carrera=c, matricula__inscripcion__persona__usuario__is_active=True, matricula__nivel__cerrado=False,matricula__nivel__periodo=periodo).order_by('matricula__nivel__paralelo','materia__asignatura__nombre','matricula__inscripcion__persona__apellido1','matricula__inscripcion__persona__apellido2','matricula__inscripcion__persona__nombres')
                                if mat_asignadas.count()>0:
                                    print(mat_asignadas.count())
                                    ws.write(fila, 0, "Periodo:", titulo)
                                    ws.write(fila, 1, elimina_tildes(periodo.nombre), titulo)
                                    fila = fila+1
                                    ws.write(fila, 0,'CARRERA', titulo)
                                    ws.write(fila, 1,'GRUPO', titulo)
                                    ws.write(fila, 2,'NIVEL', titulo)
                                    ws.write(fila, 3,'ALUMNO', titulo)
                                    ws.write(fila, 4,'CEDULA', titulo)
                                    ws.write(fila, 5,'TELEFONO', titulo)
                                    ws.write(fila, 6,'MATERIA', titulo)
                                    ws.write(fila, 7,'DOCENTE', titulo)
                                    ws.write(fila, 8,'ASISTENCIA', titulo)
                                    fila = fila+1
                                for i in mat_asignadas:
                                    # print(i)
                                    deuda = 0
                                    try:
                                        if i.matricula.inscripcion.ultima_matricula_pararetiro():
                                            nivel = i.matricula.inscripcion.ultima_matricula_pararetiro().nivel.paralelo
                                            nivelmalla = i.matricula.inscripcion.ultima_matricula_pararetiro().nivel.nivelmalla.nombre
                                    except:
                                        pass
                                    try:
                                        nombre = elimina_tildes(i.matricula.inscripcion.persona.nombre_completo_inverso())
                                    except:
                                        nombre = ''
                                    try:
                                        if i.matricula.inscripcion.persona.cedula:
                                            identificacion = elimina_tildes(i.matricula.inscripcion.persona.cedula)
                                        else:
                                            identificacion = elimina_tildes(i.matricula.inscripcion.persona.pasaporte)
                                    except: pass
                                    try:
                                        if i.matricula.inscripcion.persona.telefono:
                                            telefono = elimina_tildes(i.matricula.inscripcion.persona.telefono)
                                    except:
                                        pass
                                    try:
                                        if i.materia.asignatura:
                                            materia = i.materia.asignatura.nombre
                                    except:
                                        pass
                                    if ProfesorMateria.objects.filter(materia=i.materia).exists():
                                        profesor = ProfesorMateria.objects.filter(materia=i.materia).order_by('id')[:1].get().profesor.persona.nombre_completo_inverso()
                                    try:
                                        asistencia = i.porciento_asistencia()
                                    except:
                                        pass

                                    ws.write(fila, 0, elimina_tildes(c.nombre))
                                    ws.write(fila, 1, nivel)
                                    ws.write(fila, 2, nivelmalla)
                                    ws.write(fila, 3, nombre)
                                    ws.write(fila, 4, identificacion)
                                    ws.write(fila, 5, telefono)
                                    ws.write(fila, 6, elimina_tildes(materia))
                                    ws.write(fila, 7, elimina_tildes(profesor))
                                    ws.write(fila, 8, elimina_tildes(asistencia))

                                    fila = fila+1

                            ws.write(fila+1, 0, "Fecha Impresion", subtitulo)
                            ws.write(fila+1, 2, str(datetime.now()), subtitulo)
                            ws.write(fila+2, 0, "Usuario", subtitulo)
                            ws.write(fila+2, 2, str(request.user), subtitulo)

                    nombre ='asistencias_xfacultad'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")
                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)+" "+str(i)}),content_type="application/json")

            elif action =='buscarCarreras':
                coordinacion = Coordinacion.objects.get(pk=request.POST['id'])
                # niveles = Nivel.objects.filter(grupo=grupo).order_by('id')
                carreras = Carrera.objects.filter(coordinacion__id = coordinacion.id,activo=True, carrera=True).exclude(id__in=[66,64,63]).order_by('nombre')
                result = {}
                datos = []
                for c in carreras:
                    data = {}
                    data['nombrecarrera'] = elimina_tildes(c.nombre)
                    data['idcarrera'] = c.id
                    datos.append(data)
                result['result'] = 'ok'
                result['carreras'] = datos
                return HttpResponse(json.dumps(result),content_type="application/json")

        else:
            data = {'title': 'Asistencias de Alumnos por Facultad'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform'] = CarrerasporCoordinacionForm()
                return render(request ,"reportesexcel/xls_asistencias_xcoordinacion.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

