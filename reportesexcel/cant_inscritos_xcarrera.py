from datetime import datetime
import json
import re
import xlwt
import os
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from bib.models import Documento, TipoDocumento
from settings import MEDIA_ROOT,UTILIZA_FACTURACION_CON_FPDF,JR_USEROUTPUT_FOLDER,MEDIA_URL, SITE_ROOT
from sga.commonviews import addUserData
from sga.models import convertir_fecha,Materia,TituloInstitucion,ReporteExcel, Profesor, Materia,Nivel,Matricula,Periodo,\
    ProfesorMateria,Clase,Carrera,MateriaAsignada, Sede, Inscripcion, Jornada, SesionJornada, Modalidad
from sga.reportes import elimina_tildes
from unicodedata import normalize

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action  =='generarexcel':
                try:
                    periodo = Periodo.objects.get(pk=request.POST['periodo'])
                    carreras = Carrera.objects.filter(carrera=True).order_by('nombre')
                    matriculas = Matricula.objects.filter(nivel__periodo=periodo)
                    inscripciones = Inscripcion.objects.filter(id__in=matriculas.values('inscripcion'))
                    jornadas = Jornada.objects.filter().order_by('id')
                    modalidades = Modalidad.objects.filter().order_by('id')
                    tit = TituloInstitucion.objects.all()[:1].get()

                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo3 = xlwt.easyxf('font: name Times New Roman; align: wrap on, vert centre, horiz center')
                    subtitulo.font.height = 20*10
                    wb = xlwt.Workbook()

                    # REPORTE POR JORNADAS
                    ws = wb.add_sheet('por_jornada',cell_overwrite_ok=True)
                    ws.write_merge(0, 0,0,5, elimina_tildes(tit.nombre), titulo2)
                    ws.write_merge(1, 1,0,5, 'CANTIDAD DE ALUMNOS MATRICULADOS POR CARRERA',titulo2)
                    ws.write(3, 0, 'PERIODO: '+ elimina_tildes(periodo.nombre), subtitulo)
                    ws.write(4, 0, str(periodo.inicio)+" - "+str(periodo.fin), subtitulo)

                    colJornada = 1
                    ws.write(6, 0,'CARRERA', subtitulo)
                    for j in jornadas:
                        ws.write(6, colJornada, elimina_tildes(j.nombre), subtitulo)
                        colJornada += 1
                    ws.write(6, colJornada,'TOTAL', subtitulo)

                    fila = 7
                    for c in carreras:
                        tot = 0
                        colJornada = 1
                        ws.write(fila, 0, elimina_tildes(c.nombre))
                        for j in jornadas:
                            sesionJornada = SesionJornada.objects.filter(jornada=j)
                            ins = inscripciones.filter(sesion__id__in=sesionJornada.values('sesion__id'), carrera=c)
                            ws.write(fila, colJornada, (ins.count()))
                            tot += ins.count()
                            colJornada += 1
                        ws.write(fila, colJornada, (tot))
                        fila += 1

                    colJornada = 1
                    for j in jornadas:
                        sesionJornada = SesionJornada.objects.filter(jornada=j)
                        ins = inscripciones.filter(sesion__id__in=sesionJornada.values('sesion__id'))
                        ws.write(fila, colJornada, ins.count(), subtitulo)
                        colJornada += 1
                    ws.write(fila, colJornada, inscripciones.count(), subtitulo)

                    fila += 1
                    ws.write(fila+1, 0, "Fecha Impresion: "+str(datetime.now().date()), subtitulo)
                    ws.write(fila+2, 0, "Usuario: "+str(request.user), subtitulo)
                    ws.write(fila+4, 0, "Generado desde: sga.itb.edu.ec", subtitulo)


                    # REPORTE POR MODALIDADES
                    ws2 = wb.add_sheet('por_modalidad',cell_overwrite_ok=True)
                    ws2.write_merge(0, 0,0,6, elimina_tildes(tit.nombre), titulo2)
                    ws2.write_merge(1, 1,0,6, 'CANTIDAD DE ALUMNOS MATRICULADOS POR CARRERA',titulo2)
                    ws2.write(3, 0, 'PERIODO: '+ elimina_tildes(periodo.nombre), subtitulo)
                    ws2.write(4, 0, str(periodo.inicio)+" - "+str(periodo.fin), subtitulo)

                    colModalidad = 1
                    ws2.write(6, 0,'CARRERA', subtitulo)
                    # for m in modalidades:
                    #     ws.write(6, colModalidad, str(m), subtitulo)
                    #     colModalidad += 1
                    ws2.write(6, 1,'PRESENCIAL', subtitulo)
                    ws2.write(6, 2,'SEMIPRESENCIAL', subtitulo)
                    ws2.write(6, 3,'DUAL', subtitulo)
                    ws2.write(6, 4,'EN LINEA', subtitulo)
                    ws2.write(6, 5,'HIBRIDA', subtitulo)
                    ws2.write(6, 6,'TOTAL', subtitulo)

                    fila = 7
                    for c in carreras:
                        tot = 0
                        colModalidad = 1
                        ws2.write(fila, 0, elimina_tildes(c.nombre))
                        for m in modalidades:
                            ins = inscripciones.filter(modalidad=m, carrera=c)
                            ws2.write(fila, colModalidad, (ins.count()))
                            tot += ins.count()
                            colModalidad += 1
                        ws2.write(fila, colModalidad, (tot))
                        fila += 1

                    colModalidad = 1
                    for m in modalidades:
                        ins = inscripciones.filter(modalidad=m)
                        ws2.write(fila, colModalidad, ins.count(), subtitulo)
                        colModalidad += 1
                    ws2.write(fila, colModalidad, inscripciones.count(), subtitulo)

                    fila += 1
                    ws2.write(fila+1, 0, "Fecha Impresion: "+str(datetime.now().date()), subtitulo)
                    ws2.write(fila+2, 0, "Usuario: "+str(request.user), subtitulo)
                    ws2.write(fila+4, 0, "Generado desde: sga.itb.edu.ec", subtitulo)

                    nombre ='cantidad_matriculados'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")

        else:
            data = {'title': 'Cantidad Matriculas por Carrera'}
            addUserData(request, data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['periodo'] = Periodo.objects.filter().order_by('-id')[:10]
                return render(request ,"reportesexcel/cant_inscritos_xcarrera.html" ,  data)
        return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        print(e)
        return HttpResponseRedirect('/?info='+str(e))

def eliminaCaracteresEspeciales(texto):
    trans_tab = dict.fromkeys(map(ord, u'\u0301\u0308'), None)
    s = normalize('NFKC', normalize('NFKD', texto).translate(trans_tab))
    return s










