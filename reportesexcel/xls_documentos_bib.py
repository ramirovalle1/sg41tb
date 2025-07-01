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
    ProfesorMateria,Clase,Carrera,MateriaAsignada, Sede
from sga.reportes import elimina_tildes
from unicodedata import normalize

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action  =='generarexcel':
                try:
                    # carrera = Carrera.objects.get(pk=request.POST['carrera'])
                    sede = Sede.objects.get(pk=request.POST['sede'])
                    tipo = TipoDocumento.objects.get(pk=request.POST['tipo'])

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
                    ws.write_merge(0, 0,0,5, elimina_tildes(tit.nombre), titulo2)
                    ws.write_merge(1, 1,0,5, 'LISTADO DE ASISTENCIAS DE ESTUDIANTES POR NIVEL',titulo2)
                    # ws.write(3, 0, 'CARRERA: ')
                    # ws.write(3, 1, carrera.nombre)
                    ws.write(3, 0, 'SEDE: ' +sede.nombre, subtitulo)
                    ws.write(3, 1, sede.nombre)
                    ws.write(4, 0, 'ANNO: ' +request.POST['anno'], subtitulo)
                    ws.write(4, 1, request.POST['anno'])
                    ws.write(5, 0, 'TIPO DOCUMENTO: ' +request.POST['anno'], subtitulo)
                    ws.write(5, 1, elimina_tildes(tipo.nombre))

                    ws.write(7, 0,'CARRERA')
                    ws.write(7, 1,'CODIGO')
                    ws.write(7, 2,'TESIS')
                    ws.write(7, 3,'AUTOR')
                    ws.write(7, 4,'ANNO')
                    ws.write(7, 5,'TUTOR')

                    fila = 8
                    for d in Documento.objects.filter(sede=sede, tipo=tipo, anno=int(request.POST['anno'])).order_by('id'):
                        try:
                            tesis = eliminaCaracteresEspeciales(d.nombre) if d.nombre else ""
                        except:
                            tesis = "NO SE PUDO LEER NOMBRE DE TESIS"
                        try:
                            autor = eliminaCaracteresEspeciales(d.autor) if d.autor else ""
                        except:
                            autor = "NO SE PUDO LEER NOMBRE DE AUTOR"
                        try:
                            tutor = eliminaCaracteresEspeciales(d.tutor) if d.tutor else ""
                        except:
                            tutor = "NO SE PUDO LEER NOMBRE DE TUTOR"

                        ws.write(fila, 0, elimina_tildes(d.carrera.nombre) if d.carrera else "")
                        ws.write(fila, 1, elimina_tildes(d.codigo) if d.codigo else "")
                        ws.write(fila, 2, tesis)
                        ws.write(fila, 3, autor)
                        ws.write(fila, 4, d.anno)
                        ws.write(fila, 5, tutor)
                        fila = fila + 1

                    fila = fila + 2
                    ws.write(fila,0, "Fecha Impresion", subtitulo)
                    ws.write(fila,1, str(datetime.now().date()), subtitulo)
                    fila = fila + 1
                    ws.write(fila,0, "Usuario", subtitulo)
                    ws.write(fila,1, str(request.user), subtitulo)

                    nombre ='documentos'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")

        else:
            data = {'title': 'Documentos Biblioteca'}
            addUserData(request, data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['sedes'] = Sede.objects.filter().order_by('id')[:5]
                data['tipos'] = TipoDocumento.objects.filter().order_by('nombre')
                return render(request ,"reportesexcel/xls_documentos_bib.html" ,  data)
        return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        print(e)
        return HttpResponseRedirect('/?info='+str(e))

def eliminaCaracteresEspeciales(texto):
    trans_tab = dict.fromkeys(map(ord, u'\u0301\u0308'), None)
    s = normalize('NFKC', normalize('NFKD', texto).translate(trans_tab))
    return s










