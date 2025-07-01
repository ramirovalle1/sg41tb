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
from sga.models import convertir_fecha,Materia,MateriaAsignada,TituloInstitucion,ReporteExcel,Periodo,Carrera,Nivel,EvaluacionITB,ProfesorMateria,AsignaturaMalla, HistoricoRecordAcademico
from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action  =='generarexcel':
                try:
                    periodo= Periodo.objects.filter(pk=request.POST['periodo'])[:1].get()
                    carrera= Carrera.objects.filter(pk=request.POST['carrera'])[:1].get()
                    niveles= Nivel.objects.filter(carrera=carrera,periodo=periodo).order_by('nivelmalla')
                    m = 14
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
                    ws.write_merge(0, 0,0,m, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,m, 'LISTADO DE CALIFICACIONES Y ASISTENCIAS DE ESTUDIANTES POR PERIODO CARRERA Y NIVEL',titulo2)
                    ws.write(3, 0,'PERIODO: ' +periodo.nombre, subtitulo)
                    ws.write(4, 0,'CARRERA: ' +elimina_tildes(carrera.nombre)  , subtitulo)

                    ws.write(7, 0,'NIVEL ', subtitulo)
                    ws.write(7, 1,'GRUPO ', subtitulo)
                    ws.write(7, 2,'MATERIA ', subtitulo)
                    ws.write(7, 3,'DOCENTE ', subtitulo)
                    ws.write(7, 4,'ALUMNO ', subtitulo)
                    ws.write(7, 5,'ASISTENCIA ', subtitulo)
                    ws.write(7, 6,'NOTA1 ', subtitulo)
                    ws.write(7, 7,'NOTA2 ', subtitulo)
                    ws.write(7, 8,'NOTA3 ', subtitulo)
                    ws.write(7, 9,'NOTA4 ', subtitulo)
                    ws.write(7, 10,'EXAMEN ', subtitulo)
                    ws.write(7, 11,'TOTAL ', subtitulo)
                    ws.write(7, 12,'RECUPERACION ', subtitulo)
                    ws.write(7, 13,'NOTA FINAL ', subtitulo)
                    ws.write(7, 14,'N.F. HISTORICO', subtitulo)
                    fila = 8
                    detalle = 3
                    historico=''
                    c=6
                    for nivel in niveles:
                        asigna=AsignaturaMalla.objects.filter(malla__carrera=carrera,nivelmalla=nivel.nivelmalla).values('asignatura')
                        for materia in Materia.objects.filter(asignatura__id__in=asigna,nivel=nivel).order_by('asignatura__nombre'):
                            # print(materia)
                            docente=''
                            if ProfesorMateria.objects.filter(materia=materia,aceptacion=True).exists():
                                docente=ProfesorMateria.objects.filter(materia=materia,aceptacion=True).order_by('-id')[:1].get()
                                docente=elimina_tildes(docente.profesor.persona.nombre_completo_inverso())
                            for mate in MateriaAsignada.objects.filter(materia=materia).distinct().order_by('matricula__inscripcion'):
                                total=0
                                nota1=0
                                nota2=0
                                nota3=0
                                nota4=0
                                examen=0
                                notafinal=0
                                recuperacion=0
                                # print(mate)
                                ws.write(fila,0,elimina_tildes(nivel.nivelmalla.nombre))
                                ws.write(fila,1,elimina_tildes(nivel.paralelo))
                                ws.write(fila,2,elimina_tildes(materia.nombre_completo()))
                                ws.write(fila,3,docente)
                                ws.write(fila,4,elimina_tildes(mate.matricula.inscripcion))
                                if EvaluacionITB.objects.filter(materiaasignada=mate).exists():
                                    evaluacion=EvaluacionITB.objects.filter(materiaasignada=mate)[:1].get()
                                    nota1=evaluacion.n1
                                    nota2=evaluacion.n2
                                    nota3=evaluacion.n3
                                    nota4=evaluacion.n4
                                    examen=evaluacion.examen
                                    recuperacion=evaluacion.recuperacion
                                    total=nota1+nota2+nota3+nota4+examen
                                    historico=''
                                    if HistoricoRecordAcademico.objects.filter(inscripcion=mate.matricula.inscripcion, asignatura=mate.materia.asignatura).exists():
                                        historico = HistoricoRecordAcademico.objects.filter(inscripcion=mate.matricula.inscripcion, asignatura=mate.materia.asignatura).order_by('-id')[:1].get().nota
                                else:
                                    nota1=0
                                    nota2=0
                                    nota3=0
                                    nota4=0
                                    examen=0
                                    recuperacion=0
                                ws.write(fila,5,mate.asistenciafinal)
                                ws.write(fila,6,nota1)
                                ws.write(fila,7,nota2)
                                ws.write(fila,8,nota3)
                                ws.write(fila,9,nota4)
                                ws.write(fila,10,examen)
                                ws.write(fila,11,total)
                                ws.write(fila,12,recuperacion)
                                ws.write(fila,13,mate.notafinal)
                                ws.write(fila,14,historico)
                                fila = fila +1

                    detalle = detalle + fila
                    ws.write(detalle,0, "Fecha Impresion", subtitulo)
                    ws.write(detalle,1, str(datetime.now()), subtitulo)
                    detalle=detalle+2
                    ws.write(detalle,0, "Usuario", subtitulo)
                    ws.write(detalle,1, str(request.user), subtitulo)

                    nombre ='xls_asistenciasxperiodoycarrera'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")

        else:
            data = {'title': 'Listado de Calificacines y Asistencias por Periodo Carrera y Nivel'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                return render(request ,"reportesexcel/calificacionesyasistencias.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))


















