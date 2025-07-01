from datetime import datetime
import json
import xlwt
import os
import locale
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from settings import MEDIA_ROOT,UTILIZA_FACTURACION_CON_FPDF,JR_USEROUTPUT_FOLDER,MEDIA_URL, SITE_ROOT
from sga.commonviews import addUserData
from sga.forms import AsistenciaPeriodoCarreraExcelForm
from sga.models import convertir_fecha,Materia,MateriaAsignada,TituloInstitucion,ReporteExcel,Periodo,Carrera,Nivel,EvaluacionITB,ProfesorMateria,AsignaturaMalla, HistoricoRecordAcademico, Grupo, NivelMalla, Matricula, AsistenciaLeccion
from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action  =='generarexcel':
                try:
                    grupo = Grupo.objects.get(pk=request.POST['grupo'])
                    nivelMalla = NivelMalla.objects.get(pk=request.POST['nivelMalla'])
                    nivel = Nivel.objects.filter(grupo=grupo, nivelmalla=nivelMalla)[:1].get()
                    matriculas = Matricula.objects.filter(nivel=nivel).order_by('inscripcion__persona__apellido1', 'inscripcion__persona__apellido2')
                    materias = Materia.objects.filter(nivel=nivel).order_by('asignatura__nombre')

                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo3 = xlwt.easyxf('font: name Times New Roman; align: wrap on, vert centre, horiz center')
                    subtitulo.font.height = 20*10
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('Registros',cell_overwrite_ok=True)
                    tit = TituloInstitucion.objects.all()[:1].get()

                    ws.write_merge(0, 0, 0, 2+(materias.count()*2), tit.nombre , titulo2)
                    ws.write_merge(1, 1, 0, 2+(materias.count()*2), 'LISTADO DE CALIFICACIONES Y ASISTENCIAS DE ESTUDIANTES POR GRUPO Y NIVEL',titulo2)
                    ws.write(3, 0,'GRUPO: ' +nivel.paralelo, subtitulo)
                    ws.write(4, 0,'NIVEL: ' +elimina_tildes(nivelMalla.nombre), subtitulo)



                    ws.write_merge(6, 7, 0, 0, 'ALUMNO', subtitulo)
                    ws.write_merge(6, 7, 1, 1, 'CEDULA', subtitulo)
                    ws.write_merge(6, 7, 2, 2, 'SEXO', subtitulo)

                    columMaterias = 3
                    for m in materias:
                        ws.write_merge(6, 6, columMaterias, columMaterias+1, elimina_tildes(m.asignatura.nombre), subtitulo)
                        ws.write(7, columMaterias, 'NOTA', subtitulo)
                        ws.write(7, columMaterias+1, 'ASIST.', subtitulo)
                        columMaterias += 2

                    fila = 8
                    detalle = 3

                    for matricula in matriculas:
                        alumno = matricula.inscripcion.persona.nombre_completo_inverso()
                        identificacion = matricula.inscripcion.persona.cedula if matricula.inscripcion.persona.cedula else matricula.inscripcion.persona.pasaporte
                        ws.write(fila, 0, elimina_tildes(alumno))
                        ws.write(fila, 1, identificacion)
                        ws.write(fila, 2, matricula.inscripcion.persona.sexo.nombre)

                        columMaterias = 3
                        for m in materias:
                            if HistoricoRecordAcademico.objects.filter(inscripcion=matricula.inscripcion, asignatura=m.asignatura).exists():
                                historico = HistoricoRecordAcademico.objects.filter(inscripcion=matricula.inscripcion, asignatura=m.asignatura).order_by('-id')[:1].get()
                                ws.write(fila, columMaterias, historico.nota)
                                ws.write(fila, columMaterias+1, historico.asistencia)
                            elif EvaluacionITB.objects.filter(materiaasignada__materia=m, materiaasignada__matricula=matricula).exists():
                                evaluacionITB = EvaluacionITB.objects.filter(materiaasignada__materia=m, materiaasignada__matricula=matricula).order_by('-id')[:1].get()
                                ws.write(fila, columMaterias, evaluacionITB.nota_final())
                                ws.write(fila, columMaterias+1, matricula.porciento_asistencia())
                            columMaterias += 2
                        fila += 1


                    detalle = detalle + fila
                    ws.write(detalle,0, "Fecha Impresion", subtitulo)
                    ws.write(detalle,1, str(datetime.now()), subtitulo)
                    detalle=detalle+1
                    ws.write(detalle,0, "Usuario", subtitulo)
                    ws.write(detalle,1, str(request.user), subtitulo)

                    nombre ='xls_asistenciasxperiodoycarrera'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")

            elif action =='cargarNiveles':
                grupo = Grupo.objects.get(pk=request.POST['id'])
                niveles = Nivel.objects.filter(grupo=grupo).order_by('id')
                result = {}
                datos = []
                for n in niveles:
                    data = {}
                    data['nombreNivelMalla'] = n.nivelmalla.nombre
                    data['idNivelMalla'] = n.nivelmalla.id
                    datos.append(data)
                result['result'] = 'ok'
                result['nivelesMalla'] = datos
                return HttpResponse(json.dumps(result),content_type="application/json")


        else:
            data = {'title': 'Listado de Calificaciones y Asistencias por Periodo Carrera y Nivel'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                return render(request ,"reportesexcel/calificaciones_xnivel.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))


















