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
from sga.models import convertir_fecha, Materia, MateriaAsignada, TituloInstitucion, ReporteExcel, Periodo, Carrera, \
    Nivel, Leccion, AsistenciaLeccion
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
                    niveles = Nivel.objects.filter(periodo=periodo,carrera=carrera).select_related('nivelmalla','grupo').order_by('nivelmalla__orden')

                    m = 10
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
                    ws.write_merge(1, 1,0,m, 'LISTADO DE ASISTENCIAS DE ESTUDIANTES POR PERIODO Y CARRERA',titulo2)
                    ws.write(3, 0,'PERIODO: ' +periodo.nombre, subtitulo)
                    ws.write(4, 0,'CARRERA: ' +carrera.nombre , subtitulo)

                    fila = 7
                    com = 7
                    detalle = 3
                    columna=6
                    c=6

                    for nivel in niveles:
                        ws.write_merge(com,fila,0,1,elimina_tildes(nivel.nivelmalla.nombre)+' '+elimina_tildes(nivel.grupo.nombre),subtitulo)
                        materias = Materia.objects.filter(nivel=nivel).order_by('inicio')
                        for materia in materias:
                            ws.write_merge(com,fila,2,6,elimina_tildes(materia.nombre_completo()),subtitulo)
                            lecciones = materia.lecciones()
                            for leccion in lecciones:
                                ws.write(fila,columna,str(leccion.fecha), subtitulo)
                                columna=columna+1
                            com=fila+1
                            fila = fila +1
                            columna=6
                            materiasignada =MateriaAsignada.objects.filter(materia=materia).select_related('matricula__inscripcion').distinct().order_by('matricula__inscripcion')
                            for mate in materiasignada:
                                inscripcion =elimina_tildes(mate.matricula.inscripcion)
                                ws.write_merge(com,fila,2,6,inscripcion,subtitulo)
                                # asistencia = mate.asistencias()
                                lecciones = Leccion.objects.filter(clase__materia=mate.materia)
                                if lecciones:
                                    asistencia = AsistenciaLeccion.objects.filter(matricula=mate.matricula, leccion__clase__materia=mate.materia).select_related('leccion').order_by('leccion__fecha','leccion__horaentrada')
                                    for maat in asistencia:
                                        if maat.asistio:
                                            ws.write(fila, columna, str('x'), subtitulo3)
                                        else:
                                            ws.write(fila, columna, '', subtitulo3)
                                        columna = columna + 1
                                # for mat in asistencia:
                                #     if mat.asistio:
                                #         ws.write(fila,columna,str('x'), subtitulo3)
                                #     else:
                                #         ws.write(fila,columna,'', subtitulo3)
                                #     columna=columna+1
                                columna=6
                                com=fila+1
                                fila = fila +1
                            columna=6
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
            data = {'title': 'Listado de Asistencias por Periodo y Carrera'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform']=AsistenciaPeriodoCarreraExcelForm()
            return render(request ,"reportesexcel/asistenciasxperiodoycarrera.html" ,  data)
        return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))


















