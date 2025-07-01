import calendar
import random
from datetime import datetime
import json

from dateutil import relativedelta
from django.contrib.auth.decorators import login_required
from django.db.models import OuterRef, Subquery
from django.http import HttpResponse
from django.shortcuts import render

from django.template import RequestContext
import psycopg2
import xlwt

from decorators import secure_module
from settings import MEDIA_ROOT, ID_TEST_ENCUESTA_DESERCION, TIPO_ESPECIE_RETIRO_MATRICULA

from sga.commonviews import addUserData
from sga.models import PreguntaTestIngreso, Periodo, Nivel, RespuestaTestIngreso, InscripcionTestIngreso, \
    RespuestaInscripcionTest, TituloInstitucion, NivelMalla, Matricula, Carrera, AsistenciaLeccion, MateriaAsignada, \
    Grupo, Inscripcion, RetiradoMatricula, Sexo, Raza, EstratoSociocultural, DetalleRetiradoMatricula, \
    RubroEspecieValorada, SolicitudEstudiante


# def aculumarcantidadmatriculadonivel(listamatricula,id):
#     cantidad=0
#     for i in range(id):
#         cantidad=cantidad+listamatricula.filter(nivel__nivelmalla__id=i+1).count()
#
#     return cantidad

def aculumarcantidadmatriculadonivel(listamatricula,id):
    return listamatricula.filter(nivel__nivelmalla__id=id).count()

def obtenernomatriculado(listamatricula, id,idcarrera):

    listidnivelmalla=[]
    for i in range(id):
        if (i+1)!=id:
            listidnivelmalla.append(i+1)

    listmat=listamatricula.filter(nivel__nivelmalla__id__in=listidnivelmalla).exclude(liberada=True).values_list('inscripcion_id',flat=True)
    if idcarrera>0:
        listamatriculadonivelactual = Matricula.objects.filter(nivel__nivelmalla__id=id,nivel__carrera__id=idcarrera,inscripcion__id__in=listmat).values_list('inscripcion_id',flat=True)
    else:
        listamatriculadonivelactual = Matricula.objects.filter(nivel__nivelmalla__id=id,
                                                               inscripcion__id__in=listmat).values_list(
            'inscripcion_id', flat=True)
    cantidad=listmat.count()-listamatriculadonivelactual.count()

    return cantidad

def obtenerasistencia(listamatricula,idcarrera, id):
    # Create listidnivelmalla more efficiently
    listidnivelmalla = list(range(1, id + 1))

    # Filter and exclude in one step
    listmat = listamatricula.filter(
        nivel__nivelmalla__id__in=listidnivelmalla
    ).exclude(liberada=True).values_list('id', flat=True)
    if idcarrera>0:
        listmat=listmat.filter(nivel__carrera__id=idcarrera)
    # Use a single query to count the distinct matricula_ids with the required condition
    cantidad = MateriaAsignada.objects.filter(matricula__nivel__nivelmalla__id=id,
        matricula__id__in=listmat,
        asistenciafinal__gte=75
    ).distinct('matricula_id').count()


    return cantidad


@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):

    if request.method == 'POST':
        action = request.POST['action']

        if action == 'generar_excel':
            try:

                perido= Periodo.objects.filter(pk=int(request.POST['idperiodo']))[:1].get()

                inicio =str(perido.inicio)+ ' ' + '23:59:00'
                fin = str(perido.fin)+ ' ' + '23:59:00'

                titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                titulo.font.height = 20*11
                titulo2.font.height = 20*11
                subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                subtitulo.font.height = 20*10
                wb = xlwt.Workbook()
                ws = wb.add_sheet('Listado',cell_overwrite_ok=True)



                tit = TituloInstitucion.objects.all()[:1].get()
                ws.write_merge(0, 0,0,14, tit.nombre , titulo2)
                ws.write_merge(1, 1,0,14, 'LISTADO DE ENCUESTA DE DESERCION', titulo2)
                ws.write(2, 0, 'DESDE', titulo)
                ws.write(2, 1, str((perido.inicio)), titulo)
                ws.write(3, 0, 'HASTA:', titulo)
                ws.write(3, 1, str((perido.fin)), titulo)
                fila=5

                listapreguntas=PreguntaTestIngreso.objects.filter(testingreso__id=ID_TEST_ENCUESTA_DESERCION).exclude(id=26).order_by('orden')

                inscripdeser=InscripcionTestIngreso.objects.filter(fecha__gt=inicio,
                                                                       fecha__lt=fin,test__id=ID_TEST_ENCUESTA_DESERCION,aplicada=True)
                if listapreguntas.exists():
                    for r in listapreguntas:
                        fila=fila+1
                        fila2=fila+1
                        ws.write(fila, 0,  str(r.pregunta), titulo)
                        contacolumna=0
                        for d in RespuestaTestIngreso.objects.filter(test__id=ID_TEST_ENCUESTA_DESERCION,pregunta=r).order_by('orden'):
                          contacolumna=contacolumna+1
                          ws.write(fila, contacolumna,  str(d.respuesta).lower())
                          ws.write(fila2, contacolumna,  RespuestaInscripcionTest.objects.filter(inscripciontest__id__in=inscripdeser,pregunta=d.pregunta,
                                                                                    orden=d.orden).count())
                        fila =fila2


                nombre ='desercionmatricula'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}), content_type="application/json")

            except Exception as ex:
                print(ex)

        elif action == 'buscarperiodoano':
            try:
                data = {'title': ''}
                listPeriodo = []
                listCarrera = []
                listGrupo = []
                if int(request.POST['idano'])>0:
                    id_periodo = Nivel.objects.filter(periodo__inicio__year=request.POST['idano'],periodo__tipo__id=2).values_list('periodo_id', flat=True)
                    id_carrera=Nivel.objects.filter(periodo__inicio__year=request.POST['idano'],periodo__tipo__id=2).values_list('carrera_id', flat=True)
                    id_grupo=Nivel.objects.filter(periodo__inicio__year=request.POST['idano'],periodo__tipo__id=2,nivelmalla__ordenestadistica=1).values_list('grupo_id', flat=True)
                else:
                    id_periodo = Nivel.objects.filter(periodo__tipo__id=2).values_list(
                        'periodo_id', flat=True)
                    id_carrera = Nivel.objects.filter(periodo__tipo__id=2).values_list(
                        'carrera_id', flat=True)
                    id_grupo = Nivel.objects.filter(periodo__tipo__id=2,nivelmalla__ordenestadistica=1).values_list('grupo_id',flat=True)

                listPeriodo.append({"id": 0, "nombre": "TODOS"})
                listCarrera.append({"id": 0, "nombre": "TODOS"})
                listGrupo.append({"id": 0, "nombre": "TODOS"})
                for a in Periodo.objects.filter(id__in=id_periodo, tipo__id=2).order_by('tipo', '-id'):
                    listPeriodo.append({"id": a.id, "nombre": str(a)})

                for x in Carrera.objects.filter(id__in=id_carrera,activo=True,carrera=True).order_by('-id'):
                    listCarrera.append({"id": x.id, "nombre": str(x)})

                for m in Grupo.objects.filter(id__in=id_grupo).order_by('-id'):
                    listGrupo.append({"id": m.id, "nombre": str(m.nombre)})

                data['listPeriodo'] = listPeriodo
                data['listCarrera'] = listCarrera
                data['listGrupo'] = listGrupo
                data['result'] = 'ok'
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}), content_type="application/json")


        elif action == 'buscarcarreraperiodo':
            try:
                data = {'title': ''}

                listCarrera = []
                listGrupo = []
                if int(request.POST['idperiodo'])>0:
                    periodo=Periodo.objects.get(pk=int(request.POST['idperiodo']),tipo__id=2)
                    id_carrera=Nivel.objects.filter(periodo=periodo).values_list('carrera_id', flat=True)
                    id_grupo=Nivel.objects.filter(periodo=periodo,nivelmalla__ordenestadistica=1).values_list('carrera_id', flat=True).values_list('grupo_id', flat=True)
                else:

                    if int(request.POST['idano'])>0:
                        id_carrera = Nivel.objects.filter(periodo__inicio__year=request.POST['idano'],periodo__tipo__id=2).values_list('carrera_id', flat=True)
                        id_grupo = Nivel.objects.filter(periodo__inicio__year=request.POST['idano'],nivelmalla__ordenestadistica=1,periodo__tipo__id=2).values_list('carrera_id', flat=True).values_list(
                        'grupo_id', flat=True)
                    else:
                        id_carrera = Nivel.objects.filter(periodo__tipo__id=2).values_list(
                            'carrera_id', flat=True)
                        id_grupo = Nivel.objects.filter(nivelmalla__ordenestadistica=1,periodo__tipo__id=2).values_list(
                            'carrera_id', flat=True).values_list(
                            'grupo_id', flat=True)

                listCarrera.append({"id": 0, "nombre": "TODOS"})
                listGrupo.append({"id": 0, "nombre": "TODOS"})

                for x in Carrera.objects.filter(id__in=id_carrera, activo=True,carrera=True).order_by('-id'):
                    listCarrera.append({"id": x.id, "nombre": str(x)})

                for m in Grupo.objects.filter(id__in=id_grupo).order_by('-id'):
                    listGrupo.append({"id": m.id, "nombre": str(m.nombre)})

                data['listCarrera'] = listCarrera
                data['listGrupo'] = listGrupo
                data['result'] = 'ok'
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}), content_type="application/json")

        elif action == 'buscargrupo':
            try:
                data = {'title': ''}

                listGrupo = []
                if int(request.POST['idcarrera'])>0:
                    carrera=Carrera.objects.get(pk=int(request.POST['idcarrera']))
                    id_grupo=Nivel.objects.filter(periodo__inicio__year=request.POST['idano'],nivelmalla__ordenestadistica=1,carrera=carrera).values_list('grupo_id', flat=True)
                else:
                    id_grupo = Nivel.objects.filter(periodo__inicio__year=request.POST['idano'],nivelmalla__ordenestadistica=1
                                                    ).values_list('grupo_id', flat=True)
                listGrupo.append({"id": 0, "nombre": "TODOS"})

                for m in Grupo.objects.filter(id__in=id_grupo).order_by('-id'):
                    listGrupo.append({"id": m.id, "nombre": str(m.nombre)})

                data['listGrupo'] = listGrupo
                data['result'] = 'ok'
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}), content_type="application/json")


        elif action == 'buscarInscrMatricu':
            try:
                data = {'title': ''}


                data['seranano'] = request.POST['idano']
                anosstr = request.POST['idano']


                if int(request.POST['idperiodo']) > 0:
                        periodo = Periodo.objects.get(pk=int(request.POST['idperiodo']))


                        lismatricula = Matricula.objects.filter(nivel__periodo=periodo,
                                                     nivel__periodo__tipo__id=2,nivel__nivelmalla__ordenestadistica=1).distinct('inscripcion__id')

                        # listnivelperiodo = Nivel.objects.filter(periodo=periodo)
                else:
                    id_periodo = Nivel.objects.filter(periodo__inicio__year=anosstr,
                                                      periodo__tipo__id=2).values_list('periodo_id',
                                                                                              flat=True)
                    # listnivelperiodo = Nivel.objects.filter(periodo__id__in=id_periodo,periodo__tipo__id=2)

                    lismatricula = Matricula.objects.filter(nivel__periodo__id__in=id_periodo,nivel__nivelmalla__ordenestadistica=1,nivel__periodo__tipo__id=2).distinct('inscripcion__id')

                listnivelperiodo = Nivel.objects.filter().distinct('nivelmalla__ordenestadistica').exclude(
                    nivelmalla__ordenestadistica=0).order_by('nivelmalla__ordenestadistica')
                # carrera
                if int(request.POST['idcarrera']) > 0:
                    carrera = Carrera.objects.get(pk=int(request.POST['idcarrera']))
                    lismatricula = lismatricula.filter(nivel__carrera=carrera)

                    listnivelperiodo = listnivelperiodo.filter(carrera=carrera)

                # grupo
                if int(request.POST['idgrupo']) > 0:
                    grupo = Grupo.objects.get(pk=int(request.POST['idgrupo']))
                    lismatricula = lismatricula.filter(nivel__grupo=grupo)
                    listnivelperiodo = listnivelperiodo.filter(grupo=grupo)



                idnivelperiodo = listnivelperiodo.filter(carrera__activo=True,carrera__carrera=True).values_list(
                    'nivelmalla__ordenestadistica', flat=True)

                data['listamatricu'] = [{"nombrenivel": str(x.nombre),
                                         "cantidadmatriculado": str(
                                             aculumarcantidadmatriculadonivel(lismatricula, 1)-obtenernomatriculado(lismatricula.filter(), x.id,int(request.POST['idcarrera']))) if x.id > 1 else str(
                                             lismatricula.filter(nivel__nivelmalla__id=1).count()),
                                         "cantidadnomatriculado": str(obtenernomatriculado(lismatricula.filter(), x.id,int(request.POST['idcarrera'])))
                                         if x.id > 1
                                         else "0"} for x in
                                        NivelMalla.objects.filter(
                                            ordenestadistica__in=idnivelperiodo).order_by(
                                            'ordenestadistica').exclude(ordenestadistica=0)]


                data['result'] = 'ok'
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}), content_type="application/json")

        elif action == 'buscarMatricuAsis':
            try:
                data = {'title': ''}


                data['seranano'] = request.POST['idano']
                anosstr = request.POST['idano']


                if int(request.POST['idperiodo']) > 0:
                        periodo = Periodo.objects.get(pk=int(request.POST['idperiodo']))


                        lismatricula = Matricula.objects.filter(nivel__periodo=periodo,nivel__periodo__inicio__year=anosstr,
                                                     nivel__periodo__tipo__id=2,nivel__nivelmalla__ordenestadistica=1).distinct('inscripcion__id')

                        # listnivelperiodo = Nivel.objects.filter(periodo=periodo)
                else:
                    id_periodo = Nivel.objects.filter(periodo__inicio__year=anosstr
                                                      ,periodo__tipo__id=2).values_list('periodo_id',
                                                                                              flat=True)


                    lismatricula = Matricula.objects.filter(nivel__nivelmalla__ordenestadistica=1,nivel__periodo__id__in=id_periodo,nivel__periodo__tipo__id=2).distinct('inscripcion__id')

                listnivelperiodo = Nivel.objects.filter(nivelmalla__ordenestadistica=1).distinct('nivelmalla__ordenestadistica').exclude(
                    nivelmalla__ordenestadistica=0).order_by('nivelmalla__ordenestadistica')

                # carrera
                if int(request.POST['idcarrera']) > 0:
                    carrera = Carrera.objects.get(pk=int(request.POST['idcarrera']))
                    lismatricula = lismatricula.filter(nivel__carrera=carrera)
                    listnivelperiodo = listnivelperiodo.filter(carrera=carrera)

                # grupo
                if int(request.POST['idgrupo']) > 0:
                    grupo = Grupo.objects.get(pk=int(request.POST['idgrupo']))
                    lismatricula = lismatricula.filter(nivel__grupo=grupo)
                    listnivelperiodo = listnivelperiodo.filter(grupo=grupo)

                idnivelperiodo = listnivelperiodo.filter(carrera__activo=True,carrera__carrera=True).values_list(
                    'nivelmalla__ordenestadistica', flat=True)

                data['listamatricuasistencia'] = [{"nombrenivel": str(x.nombre).upper(),
                                                   "cantidadmatriculado": str(
                                                       aculumarcantidadmatriculadonivel(lismatricula,
                                                                                       1) - obtenernomatriculado(
                                                           lismatricula.filter(), x.id,
                                                           int(request.POST['idcarrera']))) if x.id > 1 else str(
                                                       lismatricula.filter(nivel__nivelmalla__id=x.id).count()),
                                                   "cantidadasistencia": str(
                                                       obtenerasistencia(lismatricula.filter(), int(request.POST['idcarrera']), x.id))
                                                   } for x in NivelMalla.objects.filter(
                    ordenestadistica__in=idnivelperiodo).order_by('ordenestadistica')]


                data['result'] = 'ok'
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}), content_type="application/json")


        elif action == 'buscarDesercionprograma':
            try:
                data = {'title': ''}


                data['seranano'] = request.POST['idano']
                anosstr = request.POST['idano']


                if int(request.POST['idperiodo']) > 0:
                        periodo = Periodo.objects.get(pk=int(request.POST['idperiodo']))


                        lismatricula = Matricula.objects.filter(nivel__periodo=periodo,nivel__nivelmalla__ordenestadistica=1,nivel__periodo__tipo__id=2).exclude(nivel__nivelmalla__ordenestadistica=0).distinct('inscripcion__id')


                else:
                    if int(request.POST['idano'])>0:
                        id_periodo = Nivel.objects.filter(periodo__inicio__year=anosstr,periodo__tipo__id=2
                                                          ).values_list('periodo_id',
                                                                                                  flat=True)
                    else:
                        id_periodo = Nivel.objects.filter(periodo__tipo__id=2).values_list('periodo_id', flat=True)


                    lismatricula = Matricula.objects.filter(nivel__periodo__id__in=id_periodo,nivel__nivelmalla__ordenestadistica=1,nivel__periodo__tipo__id=2).exclude(nivel__nivelmalla__ordenestadistica=0).distinct('inscripcion__id')



                # carrera
                if int(request.POST['idcarrera']) > 0:
                    carrera = Carrera.objects.get(pk=int(request.POST['idcarrera']))
                    lismatricula = lismatricula.filter(nivel__carrera=carrera)

                listacarrera = Carrera.objects.filter(id__in=lismatricula.values('nivel__carrera__id'),activo=True,carrera=True).order_by('nombre')

                retiro_matricula_subquery = RetiradoMatricula.objects.filter(
                    inscripcion__id__in=lismatricula.filter(nivel__carrera__activo=True,nivel__carrera__carrera=True).values_list('inscripcion__id', flat=True),
                    nivel__periodo__tipo__id=2
                    ).distinct('inscripcion_id')



                data['listdesecionprograma'] = [{"nombrecarrera": str(c.nombre),
                                                 "cantidadinscritos": str(
                                                            lismatricula.filter(nivel__carrera=c).exclude(
                                                                inscripcion__id__in=Subquery(retiro_matricula_subquery.filter(nivel__carrera=c).values_list('inscripcion_id', flat=True))
                                                            ).count()
                                                        ),
                                                         "cantidadretiro": str(
                                                    retiro_matricula_subquery.filter(nivel__carrera=c).count())}
                                                for c in listacarrera]


                data['result'] = 'ok'
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}), content_type="application/json")


        elif action == 'buscarDeserciongenero':
            try:
                data = {'title': ''}


                data['seranano'] = request.POST['idano']
                anosstr = request.POST['idano']

                listaretiro_ids = RetiradoMatricula.objects.filter(
                    nivel__periodo__tipo__id=2
                ).exclude(
                    nivel__nivelmalla__ordenestadistica=0
                ).values_list('id', flat=True).distinct('inscripcion_id')

                # Filter on the subquery
                retiro_matricula_subquery = DetalleRetiradoMatricula.objects.filter(
                    retirado__id__in=listaretiro_ids,
                    estado__icontains='RETIRO'
                )

                if int(request.POST['idano']) > 0:
                    id_periodo = Nivel.objects.filter(periodo__inicio__year=anosstr,
                                                      periodo__tipo__id=2).values_list('periodo_id', flat=True)

                    retiro_matricula_subquery = retiro_matricula_subquery.filter(retirado__nivel__periodo__id__in=id_periodo
                                                                                        )

                if int(request.POST['idperiodo']) > 0:
                        periodo = Periodo.objects.get(pk=int(request.POST['idperiodo']))

                        retiro_matricula_subquery=retiro_matricula_subquery.filter(retirado__nivel__periodo=periodo)



                # carrera
                if int(request.POST['idcarrera']) > 0:
                    carrera = Carrera.objects.get(pk=int(request.POST['idcarrera']))
                    retiro_matricula_subquery = retiro_matricula_subquery.filter(retirado__nivel__carrera=carrera)

                listacarrera = Carrera.objects.filter(id__in=retiro_matricula_subquery.values('retirado__nivel__carrera__id'), activo=True, carrera=True).order_by('nombre')



                data['listdesecionporhombres'] = str(retiro_matricula_subquery.filter(
                    retirado__inscripcion__persona__sexo__id=2,retirado__nivel__carrera__id__in=listacarrera.values_list('id',flat=True)).count())

                data['listdesecionpormujeres'] = str(retiro_matricula_subquery.filter(
                    retirado__inscripcion__persona__sexo__id=1,retirado__nivel__carrera__id__in=listacarrera.values_list('id',flat=True)).count())

                data['listdesecionporgenero'] = [{"nombrecarrera": str(c.nombre),
                                                  "cantidadretiradomas": str(retiro_matricula_subquery.filter(retirado__inscripcion__persona__sexo__id=2,retirado__nivel__carrera=c).count()),
                                                  "cantidadretiradofemi": str(
                                                      retiro_matricula_subquery.filter(retirado__inscripcion__persona__sexo__id=1,retirado__nivel__carrera=c).count())}
                                                 for c in listacarrera]


                data['result'] = 'ok'
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}), content_type="application/json")


        elif action == 'buscarDesercionetnia':
            try:
                data = {'title': ''}


                data['seranano'] = request.POST['idano']
                anosstr = request.POST['idano']

                listaretiro_ids = RetiradoMatricula.objects.filter(
                    nivel__periodo__tipo__id=2
                ).exclude(
                    nivel__nivelmalla__ordenestadistica=0
                ).values_list('id', flat=True).distinct('inscripcion_id')

                # Filter on the subquery
                retiro_matricula_subquery = DetalleRetiradoMatricula.objects.filter(
                    retirado__id__in=listaretiro_ids,
                    estado__icontains='RETIRO'
                )

                if int(request.POST['idano']) > 0:
                    id_periodo = Nivel.objects.filter(periodo__inicio__year=anosstr,
                                                      periodo__tipo__id=2).values_list('periodo_id', flat=True)

                    retiro_matricula_subquery = retiro_matricula_subquery.filter(
                        retirado__nivel__periodo__id__in=id_periodo
                        )

                if int(request.POST['idperiodo']) > 0:
                    periodo = Periodo.objects.get(pk=int(request.POST['idperiodo']))

                    retiro_matricula_subquery = retiro_matricula_subquery.filter(retirado__nivel__periodo=periodo)

                    # carrera
                if int(request.POST['idcarrera']) > 0:
                    carrera = Carrera.objects.get(pk=int(request.POST['idcarrera']))
                    retiro_matricula_subquery = retiro_matricula_subquery.filter(retirado__nivel__carrera=carrera)

                data['listdesecionporetnia'] = [{"raza": str(c.nombre),
                                                 "cantidad": str(retiro_matricula_subquery.filter(retirado__inscripcion__perfilinscripcion__raza=c).count())
                                                 } for c in Raza.objects.filter()]



                data['result'] = 'ok'
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}), content_type="application/json")



        elif action == 'buscarDesercionestrato':
            try:
                data = {'title': ''}


                data['seranano'] = request.POST['idano']
                anosstr = request.POST['idano']

                listaretiro_ids = RetiradoMatricula.objects.filter(
                    nivel__periodo__tipo__id=2
                ).exclude(
                    nivel__nivelmalla__ordenestadistica=0
                ).values_list('id', flat=True).distinct('inscripcion_id')

                # Filter on the subquery
                retiro_matricula_subquery = DetalleRetiradoMatricula.objects.filter(
                    retirado__id__in=listaretiro_ids,
                    estado__icontains='RETIRO'
                )

                if int(request.POST['idano']) > 0:
                    id_periodo = Nivel.objects.filter(periodo__inicio__year=anosstr,
                                                      periodo__tipo__id=2).values_list('periodo_id', flat=True)

                    retiro_matricula_subquery = retiro_matricula_subquery.filter(
                        retirado__nivel__periodo__id__in=id_periodo
                    )

                if int(request.POST['idperiodo']) > 0:
                    periodo = Periodo.objects.get(pk=int(request.POST['idperiodo']))

                    retiro_matricula_subquery = retiro_matricula_subquery.filter(retirado__nivel__periodo=periodo)

                    # carrera
                if int(request.POST['idcarrera']) > 0:
                    carrera = Carrera.objects.get(pk=int(request.POST['idcarrera']))
                    retiro_matricula_subquery = retiro_matricula_subquery.filter(retirado__nivel__carrera=carrera)


                data['listdesecionporestrato'] = [{"estrato": str(c.nombre),
                                                 "cantidad": str(retiro_matricula_subquery.filter(retirado__inscripcion__perfilinscripcion__estrato=c).count())
                                                 }
                                                for c in EstratoSociocultural.objects.filter()]


                data['result'] = 'ok'
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}), content_type="application/json")

        elif action == 'buscartrimestre':
            try:
                data = {'title': ''}
                anosstrbandeja = 2017
                listaano=[]
                colors = ['#008FFB', '#00E396', '#FEB019', '#FF4560', '#775DD0', '#00D9E9', '#FF66C3','#FFA07A','#7FFF00','#8B0000','#F08080','#7B68EE','#4169E1','#FF6347','#FFFF00','#B0C4DE']
                fecha_inicialbandeja = datetime(2017, 1, 1)
                tiempobandeja = relativedelta.relativedelta(datetime.now().date(), fecha_inicialbandeja)
                tiempotranscubandeja = tiempobandeja.years + 1
                for c in range(tiempotranscubandeja):
                    listaano.append(anosstrbandeja + c)
                idseleccion = json.loads(request.POST['idselecc'])
                listacantidadano=[]
                for id in idseleccion:
                    listapercen=[]
                    for perce in range(12):
                        fechainciames= datetime(int(listaano[id]), int(perce+1), 1)
                        last_day = calendar.monthrange(int(listaano[id]), int(perce+1))
                        fechafinalmes = datetime(int(listaano[id]), int(perce+1), int(last_day[1]))
                        listapercen.append({"x":str("Q")+str(int(perce+1)),"y":str(SolicitudEstudiante.objects.filter(rubro__rubroespecievalorada__tipoespecie__id=21,rubro__fecha__year=str(listaano[id]),rubro__fecha__gte=fechainciames.date(),rubro__fecha__lte=fechafinalmes.date()).count())})
                    listacantidadano.append({"name":str(listaano[id]),"quarters":listapercen,"color":str(colors[id])})

                data['listapercentiles']=listacantidadano

                data['result'] = 'ok'
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}), content_type="application/json")





    else:

        data = {'title': 'Estadisticas Administrativas'}
        addUserData(request, data)
        search = None
        if 'action' in request.GET:
            action = request.GET['action']

            if action=='verdesercion':
                try:

                   id_periodo=Nivel.objects.filter(cerrado=True).values_list('periodo_id',flat=True)

                   if 'id' in request.GET:
                        data['id']=int(request.GET['id'])
                        perido= Periodo.objects.filter(pk=int(request.GET['id']))[:1].get()
                        inicio=str(perido.inicio)+ ' ' + '23:59:00'
                        fin = str(perido.fin)+ ' ' + '23:59:00'
                   else:
                        perido= Periodo.objects.filter(id__in=id_periodo,tipo__id=2).order_by('tipo', '-id')[:1].get()
                        inicio=str(perido.inicio)+ ' ' + '23:59:00'
                        fin = str(perido.fin)+ ' ' + '23:59:00'

                    # buscar las preguntas que pertence al test
                   listapreguntas=PreguntaTestIngreso.objects.filter(testingreso__id=ID_TEST_ENCUESTA_DESERCION).exclude(id=26).order_by('orden')
                   data['listapreguntas']=listapreguntas


                   idinscriptest=InscripcionTestIngreso.objects.filter(fecha__gt=inicio,
                                                                       fecha__lt=fin,test__id=ID_TEST_ENCUESTA_DESERCION).values_list('id',flat=True)

                   data['listadesercion'] = [{"idpregunta": x.pregunta_id,"nompregunta":str(x.pregunta.pregunta),"escala":x.respuesta,
                                "cantidad": RespuestaInscripcionTest.objects.filter(inscripciontest__id__in=idinscriptest,pregunta=x.pregunta,
                                                                                    orden=x.orden).count()} for x in RespuestaTestIngreso.objects.filter(test__id=ID_TEST_ENCUESTA_DESERCION).order_by('pregunta__id')]

                   data['listadesercionresumen'] = [
                       {"nompregunta": str(x.pregunta),
                        "cantidad": RespuestaInscripcionTest.objects.filter(
                                                                            pregunta=x,
                                                                            orden=1).count() } for x in
                       listapreguntas.order_by('pregunta')]

                   return render(request, "estadisticasadmin/estadisticadesercion.html", data)

                except Exception as ex:
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(ex)}), content_type="application/json")

            elif action=='veratios':

                   anosstr = 2012
                   anosstrbandeja=2017
                   fecha_inicial = datetime(2012, 1, 1)
                   fecha_inicialbandeja = datetime(2017, 1, 1)
                   tiempo=relativedelta.relativedelta( datetime.now().date(), fecha_inicial)
                   tiempotranscu=tiempo.years+1
                   tiempobandeja = relativedelta.relativedelta(datetime.now().date(), fecha_inicialbandeja)
                   tiempotranscubandeja = tiempobandeja.years + 1
                   idcarrera=0
                   data['listano'] = [{"anograduacion": anosstr + i} for i in
                                       range(tiempotranscu)]



                   id_periodo = Nivel.objects.filter(periodo__inicio__year=anosstr,
                                                     periodo__tipo__id=2).values_list('periodo_id',
                                                                                             flat=True)
                   id_carrera=Nivel.objects.filter(periodo__inicio__year=anosstr,
                                                     periodo__tipo__id=2).values_list('carrera_id',
                                                                                             flat=True)
                   id_grupos=Nivel.objects.filter(periodo__inicio__year=anosstr,
                                                     periodo__tipo__id=2).values_list('grupo_id',
                                                                                             flat=True)

                   data['listperiodo']=Periodo.objects.filter(id__in=id_periodo, tipo__id=2).order_by('tipo',
                                                                                                            '-id')

                   listnivelperiodo = Nivel.objects.filter(periodo__tipo__id=2,grupo__id__in=id_grupos)

                   lismatricula = Matricula.objects.filter(nivel__periodo__id__in=id_periodo,nivel__nivelmalla__ordenestadistica=1,nivel__grupo__id__in=id_grupos)


                   lismatricula = lismatricula.filter(nivel__carrera__id__in=id_carrera)
                   listnivelperiodo=listnivelperiodo.filter(carrera__id__in=id_carrera)

                   lismatricula = lismatricula.filter(nivel__grupo__id__in=id_grupos)
                   listnivelperiodo = listnivelperiodo.filter(grupo__id__in=id_grupos)


                   idnivelperiodo=listnivelperiodo.filter().distinct('nivelmalla__ordenestadistica').exclude(nivelmalla__ordenestadistica=0).order_by('nivelmalla__ordenestadistica').values_list('nivelmalla__ordenestadistica',flat=True)

                   data['listamatricu'] = [{"nombrenivel": x.nombre,
                                            "cantidadmatriculado": str(aculumarcantidadmatriculadonivel(lismatricula,1) - obtenernomatriculado(lismatricula.filter(),x.id,idcarrera)) if x.id > 1 else  str(lismatricula.filter(nivel__nivelmalla__id=1).count()) ,
                                            "cantidadnomatriculado": str(obtenernomatriculado(lismatricula.filter(),x.id,idcarrera))
                                            if x.id > 1
                                            else "0"} for x in
                                           NivelMalla.objects.filter(ordenestadistica__in=idnivelperiodo).order_by(
                                               'ordenestadistica')]

                   data['listamatricuasistencia'] = [{"nombrenivel": x.nombre,
                                                      "cantidadmatriculado": str(aculumarcantidadmatriculadonivel(lismatricula,1) - obtenernomatriculado(lismatricula.filter(),x.id,idcarrera)) if x.id > 1 else  str(lismatricula.filter(nivel__nivelmalla__id=x.id).count()),
                                                      "cantidadasistencia": str(obtenerasistencia(lismatricula.filter(), idcarrera, x.id))
                                                      } for x in NivelMalla.objects.filter(
                       ordenestadistica=1).order_by('ordenestadistica')]

                   listacarrera=Carrera.objects.filter(id__in=id_carrera, activo=True, carrera=True).order_by('nombre')

                   # desercion

                   listaretiro_ids = RetiradoMatricula.objects.filter(
                       nivel__periodo__tipo__id=2
                   ).exclude(
                       nivel__nivelmalla__ordenestadistica=0
                   ).values_list('id', flat=True).distinct('inscripcion_id')

                   # Filter on the subquery
                   retiro_matricula_subquery = DetalleRetiradoMatricula.objects.filter( retirado__nivel__periodo__id__in=id_periodo,
                       retirado__id__in=listaretiro_ids,
                       estado__icontains='RETIRO'
                   )


                   data['listdesecionprograma'] = [{"nombrecarrera": str(c.nombre),
                                                    "cantidadinscritos":str(
                                                            lismatricula.filter(nivel__carrera=c).exclude(
                                                                inscripcion__id__in=Subquery(retiro_matricula_subquery.filter(retirado__nivel__carrera=c).values_list('retirado__inscripcion__id', flat=True))
                                                            ).count()
                                                        ),
                                                    "cantidadretiro": str(
                                                        retiro_matricula_subquery.filter(retirado__nivel__carrera=c).count())}
                                                   for c in listacarrera]






                   data['listdesecionporhombres'] = str(retiro_matricula_subquery.filter(
                                                         retirado__inscripcion__persona__sexo__id=2,).count())

                   data['listdesecionpormujeres'] = str(retiro_matricula_subquery.filter(
                       retirado__inscripcion__persona__sexo__id=1).count())

                   data['listdesecionporgenero'] = [{"nombrecarrera": str(c.nombre),
                                                     "cantidadretiradomas": str(retiro_matricula_subquery.filter(
                                                         retirado__inscripcion__persona__sexo__id=2, retirado__nivel__carrera=c).count())
                                                        ,
                                                     "cantidadretiradofemi": str(
                                                         retiro_matricula_subquery.filter(
                                                             retirado__inscripcion__persona__sexo__id=1,
                                                             retirado__nivel__carrera=c).count())}
                                                    for c in listacarrera]


                   period_ids = Nivel.objects.filter(periodo__tipo__id=2).exclude(
                       nivelmalla__ordenestadistica=0).values_list('periodo__id', flat=True)


                   retiro_subquery = DetalleRetiradoMatricula.objects.filter( retirado__nivel__periodo__id__in=period_ids,
                       retirado__id__in=listaretiro_ids,
                       estado__icontains='RETIRO'
                   )

                   data['listdesecionporgeneroresumen'] = [{"genero": str(c.nombre),
                                                     "cantidad": str(retiro_subquery.filter(retirado__inscripcion__persona__sexo=c).exclude(retirado__inscripcion__persona__sexo=None).count())
                                                     }
                                                    for c in Sexo.objects.filter()]


                   data['listdesecionporetnia'] = [{"raza": str(c.nombre),
                                                           "cantidad": str(
                                                               retiro_matricula_subquery.filter(
                                                                   retirado__inscripcion__perfilinscripcion__raza=c).count())
                                                           }
                                                          for c in Raza.objects.filter()]


                   data['listdesecionporetniaresumen'] = [{"raza": str(c.nombre),
                                                           "cantidad":str(retiro_subquery.filter(retirado__inscripcion__perfilinscripcion__raza=c)
                                                                          .exclude(retirado__inscripcion__perfilinscripcion__raza=None).count())
                                                           }
                                                          for c in Raza.objects.filter()]

                   data['listdesecionporestrato'] = [{"estrato": str(c.nombre),
                                                    "cantidad":str(
                                                               retiro_matricula_subquery.filter(
                                                                   retirado__inscripcion__perfilinscripcion__estrato=c).count())
                                                    }
                                                   for c in EstratoSociocultural.objects.filter()]


                   data['listdesecionporestratoresumen'] = [{"estrato": str(c.nombre),
                                                           "cantidad":str(retiro_subquery.
                                                                          filter(retirado__inscripcion__perfilinscripcion__estrato=c).
                                                                          exclude(retirado__inscripcion__perfilinscripcion__estrato=None).count())

                                                           }
                                                          for c in EstratoSociocultural.objects.filter()]

                   data['listcarrera']=listacarrera
                   data['listcarrerasolicitud']=Carrera.objects.filter(activo=True, carrera=True).order_by('nombre')

                   data['listgrupo']= Grupo.objects.filter(id__in=id_grupos)
                   colors = ['#008FFB', '#00E396', '#FEB019', '#FF4560', '#775DD0', '#00D9E9', '#FF66C3','#FFA07A','#7FFF00','#8B0000','#F08080','#7B68EE','#4169E1','#FF6347','#FFFF00','#B0C4DE']
                   data['listacantidadsolicitudes'] = [{"ano": str(anosstrbandeja + c),
                                                             "cantidad": str(SolicitudEstudiante.objects.filter(rubro__rubroespecievalorada__tipoespecie__id=21,rubro__fecha__year=str(anosstrbandeja + c),rubro__rubroespecievalorada__aplicada=True).count()),
                                                             "color":str(colors[c])
                                                             }
                                                            for c in range(tiempotranscubandeja)]

                   data['totalsolicitudesatendidas'] = str(SolicitudEstudiante.objects.filter(rubro__rubroespecievalorada__tipoespecie__id=21,rubro__rubroespecievalorada__aplicada=True).count())

                   return render(request, "estadisticasadmin/verratios.html", data)


        else:
            try:

                    return render(request,"estadisticasadmin/estadisticasadminbs.html", data)

            except Exception as ex:
                print(ex)
