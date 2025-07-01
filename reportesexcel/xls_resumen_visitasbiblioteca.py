from datetime import datetime,timedelta,time
import json
import xlwt


from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from settings import MEDIA_ROOT, TIPO_ADMINISTRATIVO, TIPO_ESTUDIANTE, TIPO_DOCENTE
from sga.commonviews import addUserData
from sga.forms import ResumenVisitasBibliotecaForm

from sga.models import convertir_fecha, TituloInstitucion, ReporteExcel, Carrera, Sede, DetalleVisitasBiblioteca, \
    Inscripcion, Persona, TipoPersona, TipoVisitasBiblioteca, TipoArticulo
from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            inicio = request.POST['desde']
            fin = request.POST['hasta']

            if action == 'generarexcel':
                try:
                    fechai = convertir_fecha(inicio)
                    fechaf = convertir_fecha(fin)
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10

                    # Establecer el estilo de borde
                    borders = xlwt.Borders()
                    borders.left = xlwt.Borders.THIN
                    borders.right = xlwt.Borders.THIN
                    borders.top = xlwt.Borders.THIN
                    borders.bottom = xlwt.Borders.THIN

                    textonormal = xlwt.easyxf('font: name Times New Roman, colour black, bold off;')
                    textonormal.borders = borders
                    textocenter = xlwt.easyxf('font: name Times New Roman, colour black, bold off; align: wrap on, vert centre, horiz center;')
                    textocenter.borders = borders
                    textocenterbold = xlwt.easyxf('font: name Times New Roman, colour black, bold on; '
                                                  'align: wrap on, vert centre, horiz center;')
                    titulocabecera = xlwt.easyxf('font: name Times New Roman, colour black, bold on; '
                                                 'align: wrap on, vert centre, horiz center;'
                                                 'pattern: pattern solid, fore_colour silver_ega;')
                    titulocabecera.font.height = 20 * 11
                    titulocabecera.borders = borders
                    subtitulocabecera = xlwt.easyxf('font: name Times New Roman, colour black, bold on; '
                                                 'align: wrap on, vert centre, horiz center;'
                                                 'pattern: pattern solid, fore_colour silver_ega;')
                    subtitulocabecera.font.height = 14 * 10
                    subtitulocabecera.borders = borders

                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('LISTADO',cell_overwrite_ok=True)

                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,8, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,8, 'RESUMEN DE VISITAS A BIBLIOTECA', titulo2)

                    fila =3
                    # ws.write(fila,0, 'CAMPUS:', titulo)
                    # ws.write(fila,1, elimina_tildes(campus.nombre), titulo)

                    # ws.write(fila+1,0, 'CARRERA:', titulo)
                    # ws.write(fila+1,1, str(carrera.alias), titulo)

                    ws.write(fila+2, 0, 'DESDE:', titulo)
                    ws.write(fila+2, 1, str((fechai.date())), titulo)
                    ws.write(fila+3, 0, 'HASTA:', titulo)
                    ws.write(fila+3, 1, str((fechaf.date())), titulo)

                    fila=8

                    # -------- FILTRO BASE PARA LAS VISITAS -------- #
                    detallevisitas = DetalleVisitasBiblioteca.objects.filter(fecha__gte=fechai, fecha__lte=fechaf, tipoarticulo__tipovisitabiblioteca__id__isnull=False)

                    # ----------- RESUMEN POR TIPO PERSONA ------------ #
                    ws.write(fila, 0,  'SEDE', titulocabecera)
                    ws.col(0).width = 10 * 500

                    col = 1
                    # guarda el tipo de persona y en que columna está para ir llenando la info
                    coltipopersona = []
                    listaperfiles = [TIPO_DOCENTE, TIPO_ESTUDIANTE, TIPO_ADMINISTRATIVO]
                    for tp in TipoPersona.objects.filter(id__in=listaperfiles):
                        ws.write(fila, col,  elimina_tildes(tp.descripcion.upper()), titulocabecera)
                        ws.col(col).width = 10 * 500
                        coltipopersona.append({"id": tp.id, "col": col, "tipopersona": tp.descripcion.upper(), "total": 0})
                        col = col + 1


                    # se llena la columna de las sedes
                    sedes = Sede.objects.filter(solobodega=False).order_by('nombre')
                    filasede = []
                    numfilasede = fila + 1
                    filatotalsedes = numfilasede + sedes.count()  # la columna final de las sedes para poner totales
                    for s in sedes:
                        ws.write(numfilasede, 0, elimina_tildes(s.nombre), textonormal)
                        filasede.append({"id": s.id, "fila": numfilasede})

                        for c in coltipopersona:
                            # detallealumnos = DetalleVisitasBiblioteca.objects.filter(fecha__gte=fechai, fecha__lte=fechaf, visitabiblioteca__tipopersona__id=c['id'],
                            #                                                          sede__id=s.id).distinct('visitabiblioteca__cedula').count()
                            detallealumnos = detallevisitas.filter(visitabiblioteca__tipopersona__id=c['id'], sede__id=s.id).count()
                            c['total'] = c['total'] + detallealumnos
                            ws.write(numfilasede, c['col'], detallealumnos, textocenter)
                            # ingreso del total por tipo persona
                            ws.write(filatotalsedes, c['col'], c['total'], textocenterbold)

                        numfilasede = numfilasede + 1

                    ws.write(numfilasede, 0, "TOTAL", titulocabecera)


                    # ---------- RESUMEN TIPO VISITA POR PERFIL Y TIPO VISITA --------- #
                    filaresumentipovisita = numfilasede + 5

                    # filaadministrativo = filaresumentipovisita + 1
                    # ws.write(filaadministrativo, 0, 'ADMINISTRATIVOS', titulocabecera)
                    #
                    # filaalumno = filaadministrativo + 1
                    # ws.write(filaalumno, 0, 'ADMINISTRATIVOS', titulocabecera)
                    #
                    # filadocente = filaalumno + 1
                    # ws.write(filadocente, 0, 'DOCENTES', titulocabecera)
                    #
                    # filatotaltipovivista = filadocente + 1
                    # ws.write(filatotaltipovivista, 0, 'TOTAL', titulocabecera)


                    coltipovisita = 1 # empiezan los tipos de visita
                    # for tv in TipoVisitasBiblioteca.objects.filter():
                    #     # cabecera de la tabla
                    #     ws.write(filaresumentipovisita, coltipovisita, elimina_tildes(tv.descripcion), titulocabecera)
                    #     ws.col(coltipovisita).width = 10 * 500
                    #
                    #     for c in coltipopersona:
                    #         ws.write(filaresumentipovisita, 0, c['tipopersona'], titulocabecera)
                    #         visitaxperfilytipo = detallevisitas.filter(visitabiblioteca__tipopersona__id=c['id'], tipovisitabiblioteca=tv.id).count()
                    #         ws.write(filaresumentipovisita, coltipovisita, visitaxperfilytipo, textocenterbold)
                    #
                    #     filaresumentipovisita = filaresumentipovisita + 1
                        # administrativos
                        # detalleadmin = detallevisitas.filter(visitabiblioteca__tipopersona__id=TIPO_ADMINISTRATIVO, tipovisitabiblioteca=tv.id).count()
                        # ws.write(filaadministrativo, coltipovisita, detalleadmin, textocenterbold)
                        #
                        # # alumnos
                        # detallealumnos = detallevisitas.filter(visitabiblioteca__tipopersona__id=TIPO_ESTUDIANTE, tipovisitabiblioteca=tv.id).count()
                        # ws.write(filaalumno, coltipovisita, detallealumnos, textocenterbold)
                        #
                        # # DOCENTES
                        # detalledocente = detallevisitas.filter(visitabiblioteca__tipopersona__id=TIPO_DOCENTE, tipovisitabiblioteca=tv.id).count()
                        # ws.write(filadocente, coltipovisita, detalledocente, textocenterbold)

                        # TOTAL POR TIPO DE VISITA
                        # ws.write(filatotaltipovivista, coltipovisita, detalleadmin + detallealumnos + detalledocente, textocenterbold)

                        # coltipovisita = coltipovisita + 1

                    cabeceraTipoVisita = []
                    cabeceraArticulo = []
                    indiceTipovivista = 0
                    listavisitaid = []
                    for tv in TipoVisitasBiblioteca.objects.filter().distinct('id'):
                        # cabecera de la tabla
                        cabeceraTipoVisita.append({"id": tv.id, "nombre": elimina_tildes(tv.descripcion), "col_inicio": coltipovisita, "col_fin": coltipovisita, "total": 0})
                        for a in TipoArticulo.objects.filter(tipovisitabiblioteca__id=tv.id, estado=True):
                            cabeceraArticulo.append({"id": a.id, "articulo": elimina_tildes(a.descripcion), "col": coltipovisita, "tipovisitaid": tv.id})

                            # Buscar si el id ya existe en cabeceraTipoVisita para definir su nueva columna fin
                            if tv.id in listavisitaid:
                                cabeceraTipoVisita[indiceTipovivista]['col_fin'] = coltipovisita

                            # subcabecera  tipo de articulo
                            ws.write(filaresumentipovisita, coltipovisita, elimina_tildes(a.descripcion), subtitulocabecera)

                            # cabecera tipo de visita
                            ws.write_merge(filaresumentipovisita - 1, filaresumentipovisita - 1, cabeceraTipoVisita[indiceTipovivista]['col_inicio'], cabeceraTipoVisita[indiceTipovivista]['col_fin'],
                                           elimina_tildes(tv.descripcion), titulocabecera)

                            coltipovisita = coltipovisita + 1
                            if not tv.id in listavisitaid:
                                listavisitaid.append(tv.id)
                        indiceTipovivista = indiceTipovivista + 1


                    filaresumentipovisita = filaresumentipovisita + 1
                    # filatotaltipovisita = filaresumentipovisita + len(coltipopersona)
                    perfilactual = 0
                    perfilanterior = 0
                    for c in coltipopersona:
                        perfilactual = c['id']
                        # col de cabecera lateral para los tipos de persona
                        ws.write(filaresumentipovisita, 0, c['tipopersona'], textonormal)
                        filaresumentipovisita = filaresumentipovisita + 1
                        ws.write(filaresumentipovisita, 0, 'TOTAL ', subtitulocabecera)

                        # llena la tabla por tipo de articulo
                        for ca in cabeceraArticulo:
                            numdetallvisita = detallevisitas.filter(visitabiblioteca__tipopersona__id=c['id'], tipovisitabiblioteca=ca['tipovisitaid'], tipoarticulo=ca['id']).count()
                            ws.write(filaresumentipovisita - 1, ca['col'], numdetallvisita, textocenter)

                            articulo_encontrado = next((tipovisit for tipovisit in cabeceraTipoVisita if tipovisit["id"] == ca['tipovisitaid']), None)
                            articulo_encontrado['total'] = articulo_encontrado['total'] + numdetallvisita
                            ws.write_merge(filaresumentipovisita, filaresumentipovisita, articulo_encontrado['col_inicio'], articulo_encontrado['col_fin'], articulo_encontrado['total'], titulocabecera)


                        filaresumentipovisita = filaresumentipovisita + 1
                        if perfilanterior == 0 or perfilanterior != perfilactual:
                            # recorrer todos porque se resetea de todos los articulos
                            for tipovisit in cabeceraTipoVisita:
                                tipovisit['total'] = 0
                        perfilanterior = c['id']


                    fila = filaresumentipovisita + 3

                    # ws.write(fila,0, "Total de Visitas", subtitulo)
                    # ws.write(fila,1, totalvisitas, subtitulo)
                    detalle = fila + 3
                    ws.write(detalle,0, "Fecha Impresion", subtitulo)
                    ws.write(detalle,1, str(datetime.now()), subtitulo)
                    detalle=detalle+1
                    ws.write(detalle,0, "Usuario", subtitulo)
                    ws.write(detalle,1, str(request.user), subtitulo)

                    nombre ='xls_resumenvisitasbiblioteca'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")
        else:
            data = {'title': 'Resumen Visitas a Biblioteca'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['formbiblio'] = ResumenVisitasBibliotecaForm(initial={'desde': datetime.now().date(), 'hasta': datetime.now().date()})
                return render(request ,"reportesexcel/xls_resumen_visitasbiblioteca.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))
