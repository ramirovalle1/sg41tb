from datetime import date, datetime
import json
from django.http import HttpResponse, HttpResponseRedirect

from django.shortcuts import render
from requests.packages.urllib3 import request
import xlwt
from settings import MEDIA_ROOT
from sga.commonviews import addUserData

from settings import MEDIA_ROOT, CARRERAS_ID_EXCLUIDAS_INEC
from sga.commonviews import addUserData
from sga.models import Carrera, elimina_tildes, Inscripcion, Matricula, TituloInstitucion, ReporteExcel
from socioecon.models import GrupoSocioEconomico, cantidad_gruposocioeconomico_carrera_general, InscripcionFichaSocioeconomica


def view(request):
    try:
        if request.method == 'POST':
            action = request.POST['action']
            if action == 'generaexcelsocioeco':
                inscripcion = ''
                try:
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo.font.height = 20 * 11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20 * 10
                    titulo2 = xlwt.easyxf(' font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20 * 11
                    titulo2.font.height = 20 * 11
                    style1 = xlwt.easyxf('', num_format_str='DD-MMM-YY')
                    wb = xlwt.Workbook()
                    hoja='alummos_socioeco'
                    ws = wb.add_sheet(hoja,cell_overwrite_ok=True)
                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,6, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,6, 'MATRICULADOS - NIVEL SOCIOECONOMICO POR CARRERAS  ', titulo2)
                    ws.write_merge(2, 3,0,0, ' CARRERAS ', titulo2)
                    ws.write_merge(2, 2,1,5, ' GRUPO SOCIECONOMICO ', titulo2)
                    grupeco = 1
                    for grupo in GrupoSocioEconomico.objects.all():
                        ws.write(3, grupeco, grupo.codigo)
                        grupeco = grupeco + 1
                    grupcar = 4

                    for carrera in Carrera.objects.all().exclude(id__in=CARRERAS_ID_EXCLUIDAS_INEC).order_by(
                            'coordinacion'):
                        ws.write(grupcar, 0, elimina_tildes(carrera.nombre))
                        grupsoc = 1
                        for grupo in GrupoSocioEconomico.objects.all():
                            matri=Matricula.objects.filter(nivel__carrera=carrera,nivel__cerrado=False,inscripcion__persona__usuario__is_active=True).distinct('inscripcion').values('inscripcion')
                            inscrip=InscripcionFichaSocioeconomica.objects.filter(grupoeconomico=grupo, inscripcion__id__in=matri).count()

                            ws.write(grupcar, grupsoc, inscrip)
                            grupsoc = grupsoc + 1
                        grupcar = grupcar + 1
                    grupeco = 1
                    ws.write(grupcar, 0, 'TOTAL', titulo2)
                    for socioeco in GrupoSocioEconomico.objects.all():

                        matric=Matricula.objects.filter(nivel__cerrado=False,inscripcion__persona__usuario__is_active=True).distinct('inscripcion').values('inscripcion')
                        insc1=InscripcionFichaSocioeconomica.objects.filter(grupoeconomico=socioeco, inscripcion__id__in=matric).count()
                        ws.write(grupcar, grupeco, insc1)
                        grupeco = grupeco + 1
                    detalle = grupcar + 3
                    ws.write(detalle, 0, "Fecha Impresion", subtitulo)
                    ws.write(detalle, 1, str(datetime.now()), subtitulo)
                    detalle = detalle + 2
                    ws.write(detalle, 0, "Usuario", subtitulo)
                    ws.write(detalle, 1, str(request.user), subtitulo)

                    nombre = 'alumososxnivelsocioeconomicomatriculados' + str(datetime.now()).replace(" ", "").replace(".", "").replace(":", "") + '.xls'
                    wb.save(MEDIA_ROOT + '/reporteexcel/' + nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    return HttpResponse(json.dumps({"result":str(ex)+str(inscripcion)}),content_type="application/json")

        else:
                data = {'title': 'Listado de alumnos matriculados por carrera '}
                addUserData(request, data)
                if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                    reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                    data['reportes'] = reportes
                    return render(request ,"reportesexcel/alumnos_socioeconomico.html" ,  data)
                return HttpResponseRedirect("/reporteexcel")
    except Exception as e:
        print((e))
        return HttpResponseRedirect('/?info=' + str(e))