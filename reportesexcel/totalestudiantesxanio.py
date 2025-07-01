from datetime import datetime
import json
import xlwt
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from settings import MEDIA_ROOT
from sga.commonviews import addUserData
from sga.forms import ListadoDocentexCoordinacion, TotalEstudiantesXAnioForm
from sga.models import TituloInstitucion,ReporteExcel,Coordinacion, Profesor, RolPerfilProfesor, Inscripcion, Carrera, MONTH_CHOICES, Modalidad, Grupo, InscripcionGrupo


@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']

            if action  =='generarexcel':
                try:
                    carrera = request.POST['carrera']
                    modalidad = request.POST['modalidad']
                    grupo  = request.POST['grupo']

                    titulo = xlwt.easyxf('font: name Times New Roman, bold on;align: wrap on, vert centre, horiz center')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulocabecera = xlwt.easyxf('font: name Times New Roman, bold on; align: wrap on, vert centre, horiz right')
                    titulocabecera2 = xlwt.easyxf('font: name Times New Roman, bold on; align: wrap on, vert centre, horiz left')

                    # BORDES
                    borders = xlwt.Borders()
                    # borders.left = xlwt.Borders.THIN
                    # borders.right = xlwt.Borders.THIN
                    borders.top = xlwt.Borders.THIN
                    borders.bottom = xlwt.Borders.THIN

                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    titulocabecera.font.height = 20 * 11
                    titulocabecera.borders = borders
                    titulo.borders = borders
                    titulocabecera2.borders = borders
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo2 = xlwt.easyxf('font: name Times New Roman, colour black, bold on;align: wrap on, vert centre, horiz left')
                    subtitulo3 = xlwt.easyxf('font: name Times New Roman, colour black, bold on;align: wrap on, vert centre, horiz right')

                    subtitulo.font.height = 20*10
                    subtitulo2.font.height = 20*10
                    subtitulo3.font.height = 20*10

                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('LISTADO',cell_overwrite_ok=True)

                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,14, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,14, 'LISTADO ANUAL DE ESTUDIANTES', titulo2)

                    fila =3

                    if carrera=='True' and modalidad =='False':
                        ws.write(fila, 0,  'Desglose por Carrera', titulo)
                    elif modalidad =='True' and carrera=='False':
                        ws.write(fila, 0,  'Desglose por Modalidad', titulo)
                    else:
                        ws.write(fila, 0,  'Analisis Anual General', titulo)

                    ws.col(0).width = 10 * 900

                    ws.write(fila, 1,  'ENERO', titulo)
                    ws.col(1).width = 10 * 400
                    ws.write(fila, 2,  'FEBERO', titulo)
                    ws.col(2).width = 10 * 400
                    ws.write(fila, 3,  'MARZO', titulo)
                    ws.col(3).width = 10 * 400
                    ws.write(fila, 4,  'ABRIL', titulo)
                    ws.col(4).width = 10 * 400
                    ws.write(fila, 5,  'MAYO', titulo)
                    ws.col(5).width = 10 * 400
                    ws.write(fila, 6,  'JUNIO', titulo)
                    ws.col(6).width = 10 * 400
                    ws.write(fila, 7,  'JULIO', titulo)
                    ws.col(7).width = 10 * 400
                    ws.write(fila, 8,  'AGOSTO', titulo)
                    ws.col(8).width = 10 * 400
                    ws.write(fila, 9,  'SEPTIEMBRE', titulo)
                    ws.col(9).width = 10 * 600
                    ws.write(fila, 10,  'OCTUBRE', titulo)
                    ws.col(10).width = 10 * 400
                    ws.write(fila, 11,  'NOVIEMBRE', titulo)
                    ws.col(11).width = 10 * 400
                    ws.write(fila, 12,  'DICIEMBRE', titulo)
                    ws.col(12).width = 10 * 400
                    if grupo =='True':
                        ws.write(fila, 13,  'GRUPOS INSCRISTOS', titulo)
                        ws.col(13).width = 10 * 600
                        ws.write(fila, 14,  'TOTAL', titulo)
                    else:
                        ws.write(fila, 13,  'TOTAL', titulo)

                    anio_string = request.POST['anio']
                    anios = anio_string.split(',')
                    arrayanios = [int(anio) for anio in anios]

                    meses = MONTH_CHOICES
                    for a in arrayanios:
                        estudiantes = Inscripcion.objects.filter(fecha__year=a)
                        totalestudiante = estudiantes.count()
                        inscripciongrupo = Grupo.objects.filter(id__in = InscripcionGrupo.objects.filter(inscripcion__id__in= estudiantes).values('grupo'))
                        totalgrupost= inscripciongrupo.count()

                        if carrera =='True':
                            carreras= Carrera.objects.filter(id__in=estudiantes.values('carrera'))
                            for c in carreras:
                                estudiantes_carrera = estudiantes.filter(carrera=c)
                                enerototal= estudiantes_carrera.filter(fecha__month=meses[0][0]).count()
                                febrerototal =estudiantes_carrera.filter(fecha__month=meses[1][0]).count()
                                marzototal =estudiantes_carrera.filter(fecha__month=meses[2][0]).count()
                                abriltotal =estudiantes_carrera.filter(fecha__month=meses[3][0]).count()
                                mayototal =estudiantes_carrera.filter(fecha__month=meses[4][0]).count()
                                juniototal =estudiantes_carrera.filter(fecha__month=meses[5][0]).count()
                                juliototal =estudiantes_carrera.filter(fecha__month=meses[6][0]).count()
                                agostototal =estudiantes_carrera.filter(fecha__month=meses[7][0]).count()
                                septiembretotal =estudiantes_carrera.filter(fecha__month=meses[8][0]).count()
                                octubretotal =estudiantes_carrera.filter(fecha__month=meses[9][0]).count()
                                noviembretotal =estudiantes_carrera.filter(fecha__month=meses[10][0]).count()
                                diciembretotal =estudiantes_carrera.filter(fecha__month=meses[11][0]).count()

                                inscripciongrupoxcarrera = Grupo.objects.filter(id__in = InscripcionGrupo.objects.filter(inscripcion__id__in= estudiantes_carrera).values('grupo'))
                                totalgrupos= inscripciongrupoxcarrera.count()


                                if modalidad =='True':
                                    modalidades = Modalidad.objects.filter(id__in = estudiantes_carrera.values('modalidad'))
                                    for m in modalidades:
                                        estudiantes_modalidad=estudiantes_carrera.filter(modalidad=m)
                                        inscripciongrupoxmodalidad = Grupo.objects.filter(id__in = InscripcionGrupo.objects.filter(inscripcion__id__in= estudiantes_modalidad).values('grupo'))
                                        totalgrupos= inscripciongrupoxmodalidad.count()

                                        enerototalm= estudiantes_modalidad.filter(fecha__month=meses[0][0]).count()
                                        febrerototalm =estudiantes_modalidad.filter(fecha__month=meses[1][0]).count()
                                        marzototalm =estudiantes_modalidad.filter(fecha__month=meses[2][0]).count()
                                        abriltotalm =estudiantes_modalidad.filter(fecha__month=meses[3][0]).count()
                                        mayototalm =estudiantes_modalidad.filter(fecha__month=meses[4][0]).count()
                                        juniototalm =estudiantes_modalidad.filter(fecha__month=meses[5][0]).count()
                                        juliototalm =estudiantes_modalidad.filter(fecha__month=meses[6][0]).count()
                                        agostototalm =estudiantes_modalidad.filter(fecha__month=meses[7][0]).count()
                                        septiembretotalm =estudiantes_modalidad.filter(fecha__month=meses[8][0]).count()
                                        octubretotalm =estudiantes_modalidad.filter(fecha__month=meses[9][0]).count()
                                        noviembretotalm =estudiantes_modalidad.filter(fecha__month=meses[10][0]).count()
                                        diciembretotalm =estudiantes_modalidad.filter(fecha__month=meses[11][0]).count()
                                        fila = fila + 1
                                        ws.write(fila, 0, m.nombre)
                                        ws.write(fila, 1, enerototalm)
                                        ws.write(fila, 2, febrerototalm)
                                        ws.write(fila, 3, marzototalm)
                                        ws.write(fila, 4, abriltotalm)
                                        ws.write(fila, 5, mayototalm)
                                        ws.write(fila, 6, juniototalm)
                                        ws.write(fila, 7, juliototalm)
                                        ws.write(fila, 8, agostototalm)
                                        ws.write(fila, 9, septiembretotalm)
                                        ws.write(fila, 10, octubretotalm)
                                        ws.write(fila, 11, noviembretotalm)
                                        ws.write(fila, 12, diciembretotalm)
                                        if grupo =='True':
                                            ws.write(fila, 13, totalgrupos)
                                            ws.write(fila, 14, estudiantes_modalidad.count())
                                        else:
                                            ws.write(fila, 13, estudiantes_modalidad.count())

                                fila = fila + 1
                                ws.write(fila, 0, c.alias,subtitulo2)
                                ws.write(fila, 1, enerototal,subtitulo3)
                                ws.write(fila, 2, febrerototal, subtitulo3)
                                ws.write(fila, 3, marzototal, subtitulo3)
                                ws.write(fila, 4, abriltotal, subtitulo3)
                                ws.write(fila, 5, mayototal,subtitulo3)
                                ws.write(fila, 6, juniototal, subtitulo3)
                                ws.write(fila, 7, juliototal, subtitulo3)
                                ws.write(fila, 8, agostototal,subtitulo3)
                                ws.write(fila, 9, septiembretotal,subtitulo3)
                                ws.write(fila, 10, octubretotal, subtitulo3)
                                ws.write(fila, 11, noviembretotal, subtitulo3)
                                ws.write(fila, 12, diciembretotal,subtitulo3)
                                if grupo=='True':
                                    ws.write(fila, 13, totalgrupos,subtitulo3)
                                    ws.write(fila, 14, estudiantes_carrera.count(),subtitulo3)
                                else:
                                    ws.write(fila, 13, estudiantes_carrera.count(),subtitulo3)

                        if modalidad=='True' and carrera=='False':
                            modalidades = Modalidad.objects.filter(id__in = estudiantes.values('modalidad'))
                            for m in modalidades:
                                estudiantes_modalidad=estudiantes.filter(modalidad=m)

                                inscripciongrupoxmodalidad = Grupo.objects.filter(id__in = InscripcionGrupo.objects.filter(inscripcion__id__in= estudiantes_modalidad).values('grupo'))
                                totalgrupos= inscripciongrupoxmodalidad.count()
                                enerototal= estudiantes_modalidad.filter(fecha__month=meses[0][0]).count()
                                febrerototal =estudiantes_modalidad.filter(fecha__month=meses[1][0]).count()
                                marzototal =estudiantes_modalidad.filter(fecha__month=meses[2][0]).count()
                                abriltotal =estudiantes_modalidad.filter(fecha__month=meses[3][0]).count()
                                mayototal =estudiantes_modalidad.filter(fecha__month=meses[4][0]).count()
                                juniototal =estudiantes_modalidad.filter(fecha__month=meses[5][0]).count()
                                juliototal =estudiantes_modalidad.filter(fecha__month=meses[6][0]).count()
                                agostototal =estudiantes_modalidad.filter(fecha__month=meses[7][0]).count()
                                septiembretotal =estudiantes_modalidad.filter(fecha__month=meses[8][0]).count()
                                octubretotal =estudiantes_modalidad.filter(fecha__month=meses[9][0]).count()
                                noviembretotal =estudiantes_modalidad.filter(fecha__month=meses[10][0]).count()
                                diciembretotal =estudiantes_modalidad.filter(fecha__month=meses[11][0]).count()
                                fila = fila + 1
                                ws.write(fila, 0, m.nombre,subtitulo2)
                                ws.write(fila, 1, enerototal)
                                ws.write(fila, 2, febrerototal)
                                ws.write(fila, 3, marzototal)
                                ws.write(fila, 4, abriltotal)
                                ws.write(fila, 5, mayototal)
                                ws.write(fila, 6, juniototal)
                                ws.write(fila, 7, juliototal)
                                ws.write(fila, 8, agostototal)
                                ws.write(fila, 9, septiembretotal)
                                ws.write(fila, 10, octubretotal)
                                ws.write(fila, 11, noviembretotal)
                                ws.write(fila, 12, diciembretotal)
                                if grupo =='True':
                                    ws.write(fila, 13, totalgrupos)
                                    ws.write(fila, 14, estudiantes_modalidad.count())
                                else:
                                    ws.write(fila, 13, estudiantes_modalidad.count())

                        enerototal= estudiantes.filter(fecha__month=meses[0][0]).count()
                        febrerototal =estudiantes.filter(fecha__month=meses[1][0]).count()
                        marzototal =estudiantes.filter(fecha__month=meses[2][0]).count()
                        abriltotal =estudiantes.filter(fecha__month=meses[3][0]).count()
                        mayototal =estudiantes.filter(fecha__month=meses[4][0]).count()
                        juniototal =estudiantes.filter(fecha__month=meses[5][0]).count()
                        juliototal =estudiantes.filter(fecha__month=meses[6][0]).count()
                        agostototal =estudiantes.filter(fecha__month=meses[7][0]).count()
                        septiembretotal =estudiantes.filter(fecha__month=meses[8][0]).count()
                        octubretotal =estudiantes.filter(fecha__month=meses[9][0]).count()
                        noviembretotal =estudiantes.filter(fecha__month=meses[10][0]).count()
                        diciembretotal =estudiantes.filter(fecha__month=meses[11][0]).count()
                        fila = fila+1
                        ws.write(fila, 0, 'ANIO ' + str(a), titulocabecera2)
                        ws.write(fila, 1, enerototal, titulocabecera)
                        ws.write(fila, 2, febrerototal, titulocabecera)
                        ws.write(fila, 3, marzototal, titulocabecera)
                        ws.write(fila, 4, abriltotal,titulocabecera)
                        ws.write(fila, 5, mayototal, titulocabecera)
                        ws.write(fila, 6, juniototal, titulocabecera)
                        ws.write(fila, 7, juliototal, titulocabecera)
                        ws.write(fila, 8, agostototal,titulocabecera)
                        ws.write(fila, 9, septiembretotal, titulocabecera)
                        ws.write(fila, 10, octubretotal, titulocabecera)
                        ws.write(fila, 11, noviembretotal,titulocabecera)
                        ws.write(fila, 12, diciembretotal,titulocabecera)
                        if grupo=='True':
                            ws.write(fila, 13, totalgrupost,titulocabecera)
                            ws.write(fila, 14, totalestudiante,titulocabecera)
                        else:
                            ws.write(fila, 13, totalestudiante,titulocabecera)

                    detalle = fila + 2
                    ws.write(detalle,0, "Fecha Impresion", subtitulo)
                    ws.write(detalle,1, str(datetime.now()), subtitulo)
                    detalle=detalle+1
                    ws.write(detalle,0, "Usuario", subtitulo)
                    ws.write(detalle,1, str(request.user), subtitulo)

                    nombre ='totalestudiantesxanio'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}), content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)}), content_type="application/json")
        else:
            data = {'title': 'Listado Anual de Estudiantes '}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['form'] = TotalEstudiantesXAnioForm()
                return render(request,"reportesexcel/totalestudiantesxanio.html", data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))
