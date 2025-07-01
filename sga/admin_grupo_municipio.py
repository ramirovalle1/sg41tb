from datetime import datetime
import json
import os
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.template import RequestContext
from decorators import secure_module
from settings import LISTA_GRUPO_MUNICIPO, MEDIA_ROOT
from sga.commonviews import addUserData
from sga.models import Grupo, Materia, Nivel, TituloInstitucion, RecordAcademico
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpResponseRedirect
import xlwt
from decimal import Decimal
from django.db.models.query_utils import Q

@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    if request.method=='POST':
        action = request.POST['action']
        data = {'title': ''}
        addUserData(request,data)
        if action =='generarexcel':
            periodo = request.session['periodo']
            data['periodo'] = periodo
            try:
                grupo=Grupo.objects.filter(id__in=LISTA_GRUPO_MUNICIPO).order_by('-nombre').distinct()
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
                fila = 5
                col = 0

                ws.write(0, 1, 'INSTITUTO TECNOLOGICO BOLIVARIANO', titulo)
                ws.write(1, 1, 'LISTADO TOTALIZADO DE GRUPOS MUNICIPIO', titulo)

                ws.write(fila - 2, col, "GRUPO", titulo)
                ws.write(fila - 2, col+1, "PROMEDIO ASISTENCIA GENERAL", titulo)
                ws.write(fila - 2, col+2, "PROMEDIO SIN ASISTENCIA", titulo)
                ws.write(fila - 2, col+3, "PROMEDIO REPROBADOS POR ASISTENCIA", titulo)
                ws.write(fila - 2, col+4, "PROMEDIO REPROBADOS POR APROVECHAMIENTO", titulo)
                # ws.write(fila - 2, col+5, "PROMEDIO GENERAL", titulo)



                totalpromedio=0
                totalmetriaasistencia=0
                totalpromediosinasistencia=0
                totalmetriasinasistencia=0
                totalpromedioreprobadas=0
                totalmetriareprobadas=0
                totalpromedioreprobadasaprove=0
                totalmetriareprobadasaprove=0
                totalpromediogenerla=0
                totalmetriageneral=0
                for c in grupo:
                    ws.write(fila, col, str(c.nombre))
                    if Nivel.objects.filter(periodo=periodo,grupo=c).exists():
                        nivel = Nivel.objects.get(periodo=periodo,grupo=c)
                        materias = nivel.materia_set.all().order_by('inicio', 'id')
                        for d in materias:
                            if d.porciento_asistencia_materia()>0:
                                totalmetriaasistencia=totalmetriaasistencia+1
                                totalpromedio=totalpromedio+d.porciento_asistencia_materia()
                        if  totalmetriaasistencia>0:
                            ws.write(fila, col+1, str(Decimal((totalpromedio)/totalmetriaasistencia).quantize(Decimal(10)**-2)))
                        else:
                            ws.write(fila, col+1, str('0.00'))
                    else:
                        ws.write(fila, col+1, str('0.00'))

                    if Nivel.objects.filter(periodo=periodo,grupo=c).exists():
                        nivel = Nivel.objects.get(periodo=periodo,grupo=c)
                        materias = nivel.materia_set.all().order_by('inicio', 'id')
                        for d in materias:
                            if d.porciento_asistencia_materia()>0:
                                # if d.sin_asistencia_materia()>0:
                                totalmetriasinasistencia=totalmetriasinasistencia+1
                                totalpromediosinasistencia=totalpromediosinasistencia+d.sin_asistencia_materia()
                        if totalmetriasinasistencia>0:
                            ws.write(fila, col+2, str(Decimal((totalpromediosinasistencia)/totalmetriasinasistencia).quantize(Decimal(10)**-2)))
                        else:
                            ws.write(fila, col+2, str('0.00'))
                    else:
                        ws.write(fila, col+2, str('0.00'))


                    if Nivel.objects.filter(periodo=periodo,grupo=c).exists():
                        nivel = Nivel.objects.get(periodo=periodo,grupo=c)
                        materias = nivel.materia_set.all().order_by('inicio', 'id')
                        for d in materias:
                            if d.porciento_asistencia_materia()>0:
                                # if d.porciento_asistencia_materia_reprobados()>0:
                                totalmetriareprobadas=totalmetriareprobadas+1
                                totalpromedioreprobadas=totalpromedioreprobadas+d.porciento_asistencia_materia_reprobados()
                        if totalmetriareprobadas>0:
                            ws.write(fila, col+3, str(Decimal((totalpromedioreprobadas)/totalmetriareprobadas).quantize(Decimal(10)**-2)))
                        else:
                            ws.write(fila, col+3, str('0.00'))
                    else:
                        ws.write(fila, col+3, str('0.00'))


                    if Nivel.objects.filter(periodo=periodo,grupo=c).exists():
                        nivel = Nivel.objects.get(periodo=periodo,grupo=c)
                        materias = nivel.materia_set.all().order_by('inicio', 'id')
                        for d in materias:
                            if d.porciento_asistencia_materia()>0:
                                # if d.reprobados_aprovechamiento()>0:
                                totalmetriareprobadasaprove=totalmetriareprobadasaprove+1
                                totalpromedioreprobadasaprove=totalpromedioreprobadasaprove+d.reprobados_aprovechamiento()
                        if totalmetriareprobadasaprove>0:
                            ws.write(fila, col+4, str(Decimal((totalpromedioreprobadasaprove)/totalmetriareprobadasaprove).quantize(Decimal(10)**-2)))
                        else:
                            ws.write(fila, col+4, str('0.00'))
                    else:
                        ws.write(fila, col+4, str('0.00'))



                    # if Nivel.objects.filter(periodo=periodo,grupo=c).exists():
                    #     nivel = Nivel.objects.get(periodo=periodo,grupo=c)
                    #     materias = nivel.materia_set.all().order_by('inicio', 'id')
                    #     for d in materias:
                    #         if d.porciento_asistencia_materia()>0:
                    #             # if d.promedio_por_materia()>0:
                    #             totalmetriageneral=totalmetriageneral+1
                    #             totalpromediogenerla=totalpromediogenerla+d.promedio_por_materia()
                    #     if totalmetriageneral>0:
                    #         ws.write(fila, col+5, str(Decimal((totalpromediogenerla)/totalmetriageneral).quantize(Decimal(10)**-2)))
                    #     else:
                    #         ws.write(fila, col+5, str('0.00'))
                    # else:
                    #     ws.write(fila, col+5, str('0.00'))


                    totalpromedio=0
                    totalmetriaasistencia=0
                    totalmetriasinasistencia=0
                    totalpromediosinasistencia=0
                    totalpromedioreprobadas=0
                    totalmetriareprobadas=0
                    totalpromedioreprobadasaprove=0
                    totalmetriareprobadasaprove=0
                    # totalpromediogenerla=0
                    # totalmetriageneral=0
                    fila = fila + 1
                cont = fila + 3


                ws.write(cont, 0, "Fecha Impresion", subtitulo)
                ws.write(cont, 2, str(datetime.now()), subtitulo)
                cont = cont + 1
                ws.write(cont, 0, "Usuario", subtitulo)
                ws.write(cont, 2, str(request.user), subtitulo)

                nombre = 'grupomunicipio' + str(datetime.now()).replace(" ", "").replace(".", "").replace(":","") + '.xls'
                carpeta = MEDIA_ROOT + '/reportes_excel/'
                try:
                    os.makedirs(carpeta)
                except:
                    pass
                wb.save(carpeta + nombre)

                return HttpResponse(
                    json.dumps({"result": "ok", "url": "/media/reportes_excel/" + nombre}),
                    content_type="application/json")

            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}),
                                    content_type="application/json")


        elif action == 'listadoestudiante':

            periodo = request.session['periodo']
            data['periodo'] = periodo
            try:
                grupo = Grupo.objects.get(pk=int(request.POST['idgrupo']))
                if Nivel.objects.filter(periodo=periodo,grupo=grupo).exists():
                    nivel = Nivel.objects.get(periodo=periodo,grupo=grupo)
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
                                    ws.write(fila, aux2,  str(Decimal("0").quantize(Decimal(10)**-2)))
                                aux2=aux2+1

                            if suma>0:
                                ws.write(fila, aux2, str(Decimal((suma)/existerecord).quantize(Decimal(10)**-2)))
                            else:
                                ws.write(fila, aux2, str(Decimal("0").quantize(Decimal(10)**-2)))
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

                else:
                    return HttpResponse(
                        json.dumps({"result": "bad", "error": "no existe datos para generar el archivo "}),
                        content_type="application/json")

            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}),
                                    content_type="application/json")

    else:
        data = {'title': 'Listado de Grupos'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='verdatos':
                data['title'] = 'Ver Datos del Grupo Municipio'
                periodo = request.session['periodo']
                data['periodo'] = periodo
                grupo = Grupo.objects.get(pk=request.GET['id'])
                if Nivel.objects.filter(periodo=periodo,grupo=grupo).exists():
                    nivel = Nivel.objects.get(periodo=periodo,grupo=grupo)
                    materias = nivel.materia_set.all().order_by('inicio', 'id')
                    data['materias'] = materias
                    data['nivel'] = nivel
                return render(request ,"municipio/materias_municipio.html" ,  data)

            elif action=='estadistica':
                data['title'] = 'Ver Datos del Grupo Municipio'
                periodo = request.session['periodo']
                data['periodo'] = periodo
                listaasistencia=[]
                listasinasistencia=[]
                listasinasistenciareprobado=[]
                listasinasistenciaprovecha=[]

                totalmetriaasistencia=0
                totalpromedio=0
                totalpromediosinasistencia=0
                totalmetriasinasistencia=0
                totalpromedioreprobadas=0
                totalmetriareprobadas=0
                totalpromedioreprobadasaprove=0
                totalmetriareprobadasaprove=0
                grupo=Grupo.objects.filter(id__in=LISTA_GRUPO_MUNICIPO, carrera__grupocoordinadorcarrera__group__in=data['persona'].usuario.groups.all()).order_by('-nombre').distinct()
                for c in grupo:
                    if Nivel.objects.filter(periodo=periodo,grupo=c).exists():
                        nivel = Nivel.objects.get(periodo=periodo,grupo=c)
                        materias = nivel.materia_set.all().order_by('inicio', 'id')
                        for d in materias:
                            if d.porciento_asistencia_materia()>0:
                                totalmetriaasistencia=totalmetriaasistencia+1
                                totalpromedio=totalpromedio+d.porciento_asistencia_materia()

                    if totalmetriaasistencia>0:

                        listaasistencia.append({"nombregrupo":c.nombre,"totalasistencia":str(Decimal((totalpromedio)/totalmetriaasistencia).quantize(Decimal(10)**-2))})
                    else:
                        listaasistencia.append({"nombregrupo":c.nombre,"totalasistencia":0})

                    if Nivel.objects.filter(periodo=periodo,grupo=c).exists():
                        nivel = Nivel.objects.get(periodo=periodo,grupo=c)
                        materias = nivel.materia_set.all().order_by('inicio', 'id')
                        for d in materias:
                            if d.porciento_asistencia_materia()>0:
                                # if d.sin_asistencia_materia()>0:
                                totalmetriasinasistencia=totalmetriasinasistencia+1
                                totalpromediosinasistencia=totalpromediosinasistencia+d.sin_asistencia_materia()
                        if totalmetriasinasistencia>0:
                            listasinasistencia.append({"nombregrupo":c.nombre,"totalsinasistencia":str(Decimal((totalpromediosinasistencia)/totalmetriasinasistencia).quantize(Decimal(10)**-2))})

                    if Nivel.objects.filter(periodo=periodo,grupo=c).exists():
                        nivel = Nivel.objects.get(periodo=periodo,grupo=c)
                        materias = nivel.materia_set.all().order_by('inicio', 'id')
                        for d in materias:
                            if d.porciento_asistencia_materia()>0:
                                # if d.porciento_asistencia_materia_reprobados()>0:
                                totalmetriareprobadas=totalmetriareprobadas+1
                                totalpromedioreprobadas=totalpromedioreprobadas+d.porciento_asistencia_materia_reprobados()
                        if totalmetriareprobadas>0:
                            listasinasistenciareprobado.append({"nombregrupo":c.nombre,"totalasistenciareprobada":str(Decimal((totalpromedioreprobadas)/totalmetriareprobadas).quantize(Decimal(10)**-2))})


                    if Nivel.objects.filter(periodo=periodo,grupo=c).exists():
                        nivel = Nivel.objects.get(periodo=periodo,grupo=c)
                        materias = nivel.materia_set.all().order_by('inicio', 'id')
                        for d in materias:
                            if d.porciento_asistencia_materia()>0:
                                # if d.reprobados_aprovechamiento()>0:
                                totalmetriareprobadasaprove=totalmetriareprobadasaprove+1
                                totalpromedioreprobadasaprove=totalpromedioreprobadasaprove+d.reprobados_aprovechamiento()
                        if totalmetriareprobadasaprove>0:
                           listasinasistenciaprovecha.append({"nombregrupo":c.nombre,"totalasistenciaaprove":str(Decimal((totalpromedioreprobadasaprove)/totalmetriareprobadasaprove).quantize(Decimal(10)**-2))})


                    totalmetriaasistencia=0
                    totalpromedio=0
                    totalpromediosinasistencia=0
                    totalmetriasinasistencia=0
                    totalpromedioreprobadas=0
                    totalmetriareprobadas=0
                    totalpromedioreprobadasaprove=0
                    totalmetriareprobadasaprove=0

                data['listasistencia']= listaasistencia
                data['listasinasistencia']= listasinasistencia
                data['listasinasistenciareprobado']= listasinasistenciareprobado
                data['listasinasistenciaprovecha']= listasinasistenciaprovecha

                listasinasistencia
                return render(request ,"municipio/estadisticas_municipio.html" ,  data)


        else:
            search = None
            total_grupo = 0
            persona=data['persona'].usuario.groups.all()

            if 's' in request.GET:
                search = request.GET['s']
                grupos = Grupo.objects.filter(id__in=LISTA_GRUPO_MUNICIPO).filter(Q(nombre__icontains=search) | Q(carrera__nombre__icontains=search) | Q(modalidad__nombre__icontains=search) | Q(sesion__nombre__icontains=search)).order_by('-nombre').distinct()

            else:
                grupos = Grupo.objects.filter(id__in=LISTA_GRUPO_MUNICIPO).order_by('-nombre').distinct()


            paging = Paginator(grupos, 50)
            p=1
            try:
                if 'page' in request.GET:
                    p = int(request.GET['page'])
                page = paging.page(p)
            except:
                page = paging.page(1)

            data['paging'] = paging
            data['page'] = page
            data['search'] = search if search else ""
            data['grupos'] = page.object_list
            data['persona']=persona

            return render(request ,"municipio/grupos_municipio.html" ,  data)
