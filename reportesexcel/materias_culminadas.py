from datetime import datetime
import json
import xlwt

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from settings import MEDIA_ROOT,NOTA_PARA_APROBAR,ASIST_PARA_APROBAR
from sga.commonviews import addUserData
from sga.models import TituloInstitucion,ReporteExcel, Persona,TipoNotaCredito, Carrera, Matricula, RecordAcademico, Egresado, Malla, AsignaturaMalla, NivelMalla, MateriaAsignada, Asignatura, Nivel, Periodo, ProfesorMateria, Grupo, Materia, MateriaRecepcionActaNotas
from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action :
                try:
                    m = 4
                    nivel = Nivel.objects.get(pk=request.POST['nivel'])
                    asignaturas = Asignatura.objects.filter(pk__in=AsignaturaMalla.objects.filter(nivelmalla=nivel.nivelmalla,malla__carrera=nivel.carrera).distinct('asignatura').values('asignatura'))
                    materias = Materia.objects.filter(nivel=nivel).order_by('asignatura__nombre')

                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo4 = xlwt.easyxf('font: name Times New Roman;align: wrap on, vert centre, horiz center')
                    subtitulo3 = xlwt.easyxf('font: name Times New Roman,colour black, bold on; align: wrap on, vert centre, horiz center')
                    subtitulo.font.height = 20*10
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('Listado',cell_overwrite_ok=True)
                    tit = TituloInstitucion.objects.all()[:1].get()

                    ws.write_merge(0, 0,0,materias.count(), tit.nombre , titulo2)
                    # nivelesmalla =  NivelMalla.objects.filter(pk__in=AsignaturaMalla.objects.filter(malla=nivel.malla.id,nivelmalla=nivel.nivelmalla.id).distinct('nivelmalla').values('nivelmalla'),orden__lte=nivel.nivelmalla.orden).order_by('orden')
                    ws.write_merge(1, 1,0,materias.count(), 'LISTADO DE MATERIAS CULMINADAS (DETALLE ACTA DE NOTAS)',titulo2)

                    estado_nivel = '(NIVEL ABIERTO)'
                    if nivel.cerrado:
                        estado_nivel = '(NIVEL CERRADO)'
                    ws.write(3, 0,'GRUPO:', subtitulo)
                    ws.write(3, 1, nivel.paralelo, subtitulo)
                    ws.write(4, 0,'NIVEL:', subtitulo)
                    ws.write(4, 1, str(nivel.nivelmalla.nombre)+' '+str(estado_nivel), subtitulo)

                    fila=6
                    ws.write_merge(fila, fila+1,0,2, 'MATERIA' , subtitulo3)
                    ws.write_merge(fila, fila+1,3,5, 'DOCENTE' , subtitulo3)
                    ws.write_merge(fila, fila+1,6,6, 'CERRADA' , subtitulo3)
                    ws.write_merge(fila, fila,7,8, 'ACTAS' , subtitulo3)
                    ws.write(fila+1, 7,'ENTREGADA', subtitulo3)
                    ws.write(fila+1, 8,'VALIDADA', subtitulo3)

                    fila=8
                    for m in materias:
                        ws.write_merge(fila, fila,0,2, elimina_tildes(m.asignatura.nombre))
                        profesor=''
                        if ProfesorMateria.objects.filter(materia=m,aceptacion=True).exists():
                            profesor = ProfesorMateria.objects.filter(materia=m,aceptacion=True).order_by('-id')[:1].get().profesor.persona.nombre_completo_inverso()
                        ws.write_merge(fila, fila,3,5, profesor)
                        if m.cerrado:
                            ws.write(fila, 6, 'SI')
                        else:
                            ws.write(fila, 6, 'NO')
                        if MateriaRecepcionActaNotas.objects.filter(materia=m).exclude(entrega=None).exists() or MateriaRecepcionActaNotas.objects.filter(materia=m).exclude(entrega='').exists():
                            ws.write(fila, 7, 'SI')
                            if MateriaRecepcionActaNotas.objects.filter(materia=m, entregada=True).exists():
                                ws.write(fila, 8, 'SI')
                            else:
                                ws.write(fila, 8, 'NO')
                        else:
                            ws.write(fila, 7, 'NO')
                            ws.write(fila, 8, '-')
                        fila = fila+1


                    ws.write(fila+1, 0, "Fecha Impresion", subtitulo)
                    ws.write(fila+1, 1, str(datetime.now()), subtitulo)
                    ws.write(fila+2, 0, "Usuario", subtitulo)
                    ws.write(fila+2, 1, str(request.user), subtitulo)

                    nombre ='detalle_acta'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(ex)
                    return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")

        else:
            data = {'title': 'Asignaturas Culminadas (Detalle Entrega de Actas)'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                return render(request ,"reportesexcel/materias_culminadas.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))


