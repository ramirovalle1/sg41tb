from datetime import datetime
from decimal import Decimal
import json
import os

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
import xlwt
from settings import MEDIA_ROOT
from sga.commonviews import addUserData
from sga.forms import   GrupoReporteForm
from sga.models import TituloInstitucion,   ReporteExcel, Nivel,  Materia, RecordAcademico


@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action :
                try:
                    idnivel = request.POST['idnivel']
                    nivel = Nivel.objects.get(pk=int(idnivel))
                    if Materia.objects.filter(nivel=nivel).exists():
                        materias=Materia.objects.filter(nivel=nivel)
                        titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                        titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                        titulo.font.height = 20*11
                        titulo2.font.height = 20*11
                        subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                        subtitulo.font.height = 20*10
                        wb = xlwt.Workbook()
                        ws = wb.add_sheet('Listado',cell_overwrite_ok=True)
                        fila = 6
                        col = 0

                        tit = TituloInstitucion.objects.all()[:1].get()
                        ws.write_merge(0, 0,0,9, tit.nombre , titulo2)
                        ws.write_merge(1, 1,0,9, 'LISTADO ESTUDIANTE POR GRUPO'+' '+str(nivel.grupo), titulo2)


                        ws.write_merge(5, 5,0,4,  'ESTUDIANTE', titulo)
                        aux=6
                        for m in materias:
                            ws.write(5, aux,  m.asignatura.nombre, titulo)
                            aux=aux+1

                        ws.write(5, aux, 'PROMEDIO', titulo)
                        for matri in nivel.matricula_set.all().order_by('inscripcion__persona'):
                            aux2=6
                            suma=0
                            existerecord=0
                            ws.write_merge(fila, fila,0,4, matri.inscripcion.persona.nombre_completo_inverso())

                            for m in materias:
                                if RecordAcademico.objects.filter(asignatura=m.asignatura,inscripcion=matri.inscripcion,asignatura__promedia=True).exists():
                                    record= RecordAcademico.objects.get(asignatura=m.asignatura,inscripcion=matri.inscripcion,asignatura__promedia=True)
                                    suma=suma+record.nota
                                    existerecord=existerecord+1
                                    ws.write(fila, aux2,  record.nota)
                                else:
                                    ws.write(fila, aux2,  0)
                                aux2=aux2+1

                            if suma>0:
                                ws.write(fila, aux2, str(Decimal((suma)/existerecord).quantize(Decimal(10)**-2)))
                            else:
                                ws.write(fila, aux2, 0)
                            fila = fila + 1
                        cont = fila + 3

                        ws.write(cont, 0, "Fecha Impresion", subtitulo)
                        ws.write(cont, 2, str(datetime.now()), subtitulo)
                        cont = cont + 1
                        ws.write(cont, 0, "Usuario", subtitulo)
                        ws.write(cont, 2, str(request.user), subtitulo)


                    nombre = 'listadoalumnogrupo' + str(datetime.now()).replace(" ", "").replace(".", "").replace(":","") + '.xls'
                    carpeta = MEDIA_ROOT + '/reportes_excel/'
                    try:
                        os.makedirs(carpeta)
                    except:
                        pass
                    wb.save(carpeta + nombre)

                    return HttpResponse(
                        json.dumps({"result": "ok", "url": "/media/reportes_excel/" + nombre}),
                        content_type="application/json")

                except Exception as ex:
                    print(ex)
                    pass

        else:
            data = {'title': 'Consulta de Alumnos por Grupo'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                data['generarform']=GrupoReporteForm()
                return render(request ,"reportesexcel/listadoalumnosgrupo.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")
    except Exception as e:
        print(e)
        return HttpResponseRedirect('/?info='+str(e))
