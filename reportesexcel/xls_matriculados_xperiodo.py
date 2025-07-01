from datetime import datetime
import json
import xlwt
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from settings import MEDIA_ROOT
from sga.commonviews import addUserData
from sga.funciones import two_decimals
from sga.models import TituloInstitucion, ReporteExcel, Carrera, Matricula, MateriaAsignada, Periodo, ProfesorMateria, PerfilInscripcion
import re

from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action  =='generarexcel':
                try:
                    inicio = datetime.now()
                    titulo = xlwt.easyxf('font: name Times New Roman, bold on; align: wrap on, vert centre, horiz center')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')

                    subtitulo.font.height = 20*10
                    wb = xlwt.Workbook()

                    tit = TituloInstitucion.objects.all()[:1].get()

                    periodo = Periodo.objects.get(pk=request.POST['periodo'])

                    matriculas = Matricula.objects.filter(nivel__periodo=periodo).order_by('inscripcion__carrera__nombre', 'nivel__nivelmalla__nombre', 'nivel__paralelo')
                    carreras = Carrera.objects.filter(id__in=matriculas.values('inscripcion__carrera')).order_by('nombre')
                    if 'carrera' in request.POST:
                        carreras = Carrera.objects.filter(pk=request.POST['carrera'])
                        # matriculas = matriculas.filter(inscripcion__carrera=carrera)
                    contador = 1
                    for carrera in carreras:
                        if matriculas.filter(inscripcion__carrera=carrera).exists():
                            matriculas_carrera = matriculas.filter(inscripcion__carrera=carrera)
                            nombre_hoja = str(contador)+'. '+elimina_tildes(carrera.alias.replace('-', ''))
                            nombre_hoja = re.sub(r'[:\\/*?[\]]', '', nombre_hoja)
                            nombre_hoja = nombre_hoja[:31]
                            nombre_hoja = nombre_hoja.strip()
                            ws = wb.add_sheet(nombre_hoja, cell_overwrite_ok=True)
                            contador += 1
                            ws.write_merge(0, 0, 0, 11, tit.nombre, titulo2)
                            ws.write_merge(1, 1, 0, 11, 'MATRICULADOS POR PERIODO', titulo2)
                            fila = 3
                            ws.write(fila, 0, 'PERIODO: ' + elimina_tildes(periodo.nombre), subtitulo)
                            fila += 1
                            ws.write(fila, 0, 'CARRERA: ' + elimina_tildes(carrera.nombre), subtitulo)
                            fila += 2
                            ws.write(fila, 0, 'Nombre', subtitulo)
                            ws.write(fila, 1, 'Cedula', subtitulo)
                            ws.write(fila, 2, 'Nacionalidad', subtitulo)
                            ws.write(fila, 3, 'Ciudad Residencia', subtitulo)
                            ws.write(fila, 4, 'Sexo', subtitulo)
                            ws.write(fila, 5, 'Ficha Socioeconomica Completa', subtitulo)
                            ws.write(fila, 6, 'Nivel Sopcioeconomico', subtitulo)
                            ws.write(fila, 7, 'F. Nacimiento', subtitulo)
                            ws.write(fila, 8, 'Retirado', subtitulo)

                            ws.write(fila, 9, 'Discapacitado', subtitulo)
                            ws.write(fila, 10, 'Tipo', subtitulo)
                            ws.write(fila, 11, 'Porcentaje', subtitulo)
                            ws.write(fila, 12, 'Carnet', subtitulo)

                            ws.write(fila, 13, 'Becado', subtitulo)
                            ws.write(fila, 14, '% Beca', subtitulo)
                            ws.write(fila, 15, 'Tipo Beca', subtitulo)
                            ws.write(fila, 16, 'Motivo Beca', subtitulo)

                            ws.write(fila, 17, 'Materia', subtitulo)
                            ws.write(fila, 18, 'Nivel Materia', subtitulo)
                            ws.write(fila, 19, 'Desde', subtitulo)
                            ws.write(fila, 20, 'Hasta', subtitulo)
                            ws.write(fila, 21, 'Docente', subtitulo)
                            ws.write(fila, 22, 'Cedula Docente', subtitulo)
                            ws.write(fila, 23, '# Matriculas en Materia', subtitulo)
                            ws.write(fila, 24, 'N1', subtitulo)
                            ws.write(fila, 25, 'N2', subtitulo)
                            ws.write(fila, 26, 'N3', subtitulo)
                            ws.write(fila, 27, 'N4', subtitulo)
                            ws.write(fila, 28, 'Examen', subtitulo)
                            ws.write(fila, 29, 'Recuperacion', subtitulo)
                            ws.write(fila, 30, 'N. Final', subtitulo)
                            ws.write(fila, 31, 'Asist.', subtitulo)
                            fila += 1

                            for m in matriculas_carrera:
                                # print(m.id)
                                grupoeconomico = ''
                                if m.inscripcion.inscripcionfichasocioeconomica_set.exists():
                                    grupoeconomico = m.inscripcion.inscripcionfichasocioeconomica_set.all()[:1].get().grupoeconomico.nombre

                                tieneDiscapacidad = 'NO'
                                tipoDiscapacidad = ''
                                porcientoDiscapacidad = ''
                                carnetDiscapacidad = ''

                                if PerfilInscripcion.objects.filter(inscripcion=m.inscripcion).exists():
                                    perfilInscripcion = PerfilInscripcion.objects.filter(inscripcion=m.inscripcion).order_by('-id')[:1].get()
                                    if perfilInscripcion.tienediscapacidad:
                                        tieneDiscapacidad = 'SI'
                                        tipoDiscapacidad = perfilInscripcion.tipodiscapacidad.nombre if perfilInscripcion.tipodiscapacidad else ''
                                        porcientoDiscapacidad = perfilInscripcion.porcientodiscapacidad
                                        carnetDiscapacidad = perfilInscripcion.carnetdiscapacidad

                                persona = m.inscripcion.persona
                                asignadas = MateriaAsignada.objects.filter(matricula=m).order_by('materia__asignatura__nombre')
                                for asignada in asignadas:

                                    ws.write(fila, 0, elimina_tildes(persona.nombre_completo_inverso()))
                                    ws.write(fila, 1, str(persona.cedula) if persona.cedula else persona.pasaporte)
                                    ws.write(fila, 2, elimina_tildes(persona.nacionalidad))
                                    ws.write(fila, 3, elimina_tildes(persona.cantonresid))
                                    ws.write(fila, 4, elimina_tildes(persona.sexo))
                                    ws.write(fila, 5, 'SI' if not m.inscripcion.datos_socioeconomicos_incompletos() else 'NO')
                                    ws.write(fila, 6, grupoeconomico)
                                    ws.write(fila, 7, str(persona.nacimiento))
                                    ws.write(fila, 8, 'SI' if m.esta_retirado_inscripcion() else 'NO')

                                    ws.write(fila, 9, tieneDiscapacidad)
                                    ws.write(fila, 10, tipoDiscapacidad)
                                    ws.write(fila, 11, porcientoDiscapacidad)
                                    ws.write(fila, 12, carnetDiscapacidad)

                                    ws.write(fila, 13, 'SI' if m.becado else 'NO')
                                    ws.write(fila, 14, m.porcientobeca if m.porcientobeca else '')
                                    ws.write(fila, 15, m.tipobeca.nombre if m.tipobeca else '')
                                    ws.write(fila, 16, m.motivobeca.nombre if m.motivobeca else '')

                                    nombreProfesor = ''
                                    cedulaProfesor = ''
                                    if ProfesorMateria.objects.filter(materia=asignada.materia).exists():
                                        profesor = ProfesorMateria.objects.filter(materia=asignada.materia).order_by('-id')[:1].get().profesor
                                        nombreProfesor = profesor.persona.nombre_completo_inverso()
                                        cedulaProfesor = profesor.persona.cedula if profesor.persona.cedula else profesor.persona.pasaporte
                                    ws.write(fila, 17, elimina_tildes(asignada.materia.asignatura.nombre))
                                    ws.write(fila, 18, asignada.materia.nivel.nivelmalla.nombre if asignada.materia.nivel.nivelmalla else '')
                                    ws.write(fila, 19, str(asignada.materia.inicio))
                                    ws.write(fila, 20, str(asignada.materia.fin))
                                    ws.write(fila, 21, elimina_tildes(nombreProfesor))
                                    ws.write(fila, 22, str(cedulaProfesor))
                                    ws.write(fila, 23, MateriaAsignada.objects.filter(materia=asignada.materia).count())
                                    ws.write(fila, 24, asignada.evaluacion().n1)
                                    ws.write(fila, 25, asignada.evaluacion().n2)
                                    ws.write(fila, 26, asignada.evaluacion().n3)
                                    ws.write(fila, 27, asignada.evaluacion().n4)
                                    ws.write(fila, 28, asignada.evaluacion().examen)
                                    ws.write(fila, 29, asignada.evaluacion().recuperacion)
                                    ws.write(fila, 30, asignada.notafinal)
                                    ws.write(fila, 31, two_decimals(asignada.porciento_asistencia()))

                                    fila += 1

                    fin = datetime.now()
                    tiempo = (fin - inicio).total_seconds()
                    print("TIEMPO DE EJECUCION: "+str(tiempo))

                    nombre ='matriculas'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")


        else:
            data = {'title': 'Matriculados por Periodo'}
            addUserData(request,data)
            data['periodo'] = Periodo.objects.filter().order_by('-id')[:15]
            # if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
            # reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
            # data['reportes'] = reportes

            return render(request ,"reportesexcel/xls_matriculados_xperiodo.html" ,  data)
            # return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

