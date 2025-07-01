import json
from datetime import datetime
import os
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import RequestContext
import xlwt
from settings import MEDIA_ROOT
from sga.commonviews import addUserData
from sga.dbf import elimina_tildes
from sga.models import ReferidosInscripcion, InscripcionTipoTest, Inscripcion, Grupo, Persona, ArchivoTestConduccion

__author__ = 'mfloresv'

class MiPaginador(Paginator):
    def __init__(self, object_list, per_page, orphans=0, allow_empty_first_page=True, rango=5):
        super(MiPaginador,self).__init__(object_list, per_page, orphans=orphans, allow_empty_first_page=allow_empty_first_page)
        self.rango = rango
        self.paginas = []
        self.primera_pagina = False
        self.ultima_pagina = False

    def rangos_paginado(self, pagina):
        left = pagina - self.rango
        right = pagina + self.rango
        if left<1:
            left=1
        if right>self.num_pages:
            right = self.num_pages
        self.paginas = range(left, right+1)
        self.primera_pagina = True if left>1 else False
        self.ultima_pagina = True if right<self.num_pages else False
        self.ellipsis_izquierda = left-1
        self.ellipsis_derecha = right+1

def view(request):
    if request.method=='POST':
        action = request.POST['action']
        if action == 'generararchivo':
           try:
                data = {'title': ''}

                listresultado = json.loads(request.POST['listaresultado'])

                #nombreconductor = request.POST['nombreestudiante']
                #nomgrupo= request.POST['nombregrupo']
                inscripcion = Inscripcion.objects.get(id=int(request.POST['idinscripcion']))

                titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                titulo.font.height = 20 * 11
                subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                subtitulo.font.height = 20 * 10
                wb = xlwt.Workbook()

                ws = wb.add_sheet('Resultado Test', cell_overwrite_ok=True)

                ws.write(0, 1, 'CONDUCE ECUADOR', titulo)
                ws.write(1, 1, 'RESULTADO DE LOS TEST', titulo)

                ws.write(2, 0, 'NOMBRE', titulo)
                ws.write(2, 1, elimina_tildes(inscripcion.persona.nombre_completo_inverso()) , titulo)

                ws.write(3, 0, 'GRUPO', titulo)
                ws.write(3, 1, inscripcion.grupo().nombre, titulo)

                fila = 6
                col = 0

                ws.write(fila - 1, col, "NOMBRE TEST", titulo)
                ws.write(fila - 1, col + 1, "PUNTAJE", titulo)
                ws.write(fila - 1, col + 2, "OBSERVACION", titulo)


                for c in listresultado:

                    ws.write(fila, col, str(elimina_tildes(c['test'])))
                    ws.write(fila, col + 1, str(c['puntaje']))
                    ws.write(fila, col + 2, str(elimina_tildes(c['observacion'])))

                    fila = fila + 1
                cont  = fila + 3

                ws.write(cont, 0, "Fecha Impresion", subtitulo)
                ws.write(cont, 2, str(datetime.now()), subtitulo)
                cont = cont + 1
                ws.write(cont, 0, "Usuario", subtitulo)
                ws.write(cont, 2, str(request.user), subtitulo)

                nombre = 'informe_test' + str(datetime.now()).replace(" ", "").replace(".", "").replace(":","")+'.xls'
                carpeta=MEDIA_ROOT + '/reportes_excel/'
                try:
                    os.makedirs(carpeta)
                except:
                    pass
                wb.save(carpeta + nombre)


                return HttpResponse(json.dumps({"result": "ok", "url": "/media/reportes_excel/" + nombre}),
                                    content_type="application/json")
           except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}), content_type="application/json")

        elif action == 'subir':
                try:
                    data = {'title': ''}
                    #persona = Persona.objects.get(usuario=request.user)
                    inscripcion = Inscripcion.objects.get(id=int(request.POST['idinscripcion']))
                    if "file" in request.FILES:
                        if not ArchivoTestConduccion.objects.filter(inscripcion=inscripcion).exists():
                            subirarch = ArchivoTestConduccion(inscripcion=inscripcion,informe=request.FILES["file"],usuario=request.user,fecharegistro=datetime.now())
                            subirarch.save()
                        else:
                            archivosubir= ArchivoTestConduccion.objects.get(inscripcion=inscripcion)
                            archivosubir.informe=request.FILES["file"]
                            archivosubir.save()

                    data['result'] = 'ok'
                    return HttpResponse(json.dumps(data), content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}), content_type="application/json")


        elif action == 'decargararchivo':
                try:
                    data = {'title': ''}
                    #persona = Persona.objects.get(usuario=request.user)
                    inscripcion = Inscripcion.objects.get(id=int(request.POST['idinscripcion']))
                    if  ArchivoTestConduccion.objects.filter(inscripcion=inscripcion).exists():
                        archivosubir= ArchivoTestConduccion.objects.get(inscripcion=inscripcion)
                        return HttpResponse(json.dumps({"result": "ok", "url": "/media/informetest/" + archivosubir.informe}),
                                        content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({'result': 'bad', 'message': 'No tiene archivo'}), content_type="application/json")

                except Exception as e:
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}), content_type="application/json")


        elif action == 'generararchivogrupo':
                try:
                    data = {'title': ''}
                    grupoid = request.POST['idgruposeleccion']
                    lista=InscripcionTipoTest.objects.filter(estado=True).distinct('inscripcion').values('inscripcion_id')
                    if int(grupoid)>0:
                        #gruponom= Grupo.objects.get(pk=int(request.POST['idgruposeleccion']))
                        data['grupo'] = Grupo.objects.get(pk=int(request.POST['idgruposeleccion']))
                        data['grupoid'] = int(grupoid) if grupoid else ""
                        lisinscrip =  Inscripcion.objects.filter(carrera__grupocoordinadorcarrera__group__in=request.user.groups.all(), inscripciongrupo__grupo=data['grupo']).distinct()
                    else:
                        lisinscrip = Inscripcion.objects.filter()

                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo.font.height = 20 * 11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20 * 10
                    wb = xlwt.Workbook()

                    ws = wb.add_sheet('Resultado Test', cell_overwrite_ok=True)

                    ws.write(0, 1, 'CONDUCE ECUADOR', titulo)
                    ws.write(1, 1, 'LISTA DE INFORME DEL TEST', titulo)

                    fila = 6
                    col = 0


                    ws.write(fila - 1, col, "CEDULA", titulo)
                    ws.write(fila - 1, col + 1, "NOMBRE", titulo)
                    ws.write(fila - 1, col + 2, "GRUPO", titulo)
                    ws.write(fila - 1, col + 3, "TEST", titulo)
                    ws.write(fila - 1, col + 4, "ARCHIVO", titulo)


                    for c in lisinscrip:

                        ws.write(fila, col, str(c.persona.cedula))
                        ws.write(fila, col + 1, str(elimina_tildes(c.persona.nombre_completo_inverso())))
                        ws.write(fila, col + 2, str(c.grupo().nombre))
                        ws.write(fila, col + 3, str(c.tiene_test_completo()))
                        ws.write(fila, col + 4, str(c.verificararchivotest()))


                        fila = fila + 1
                    cont  = fila + 3


                    ws.write(cont, 0, "Total Estudiante con Test", subtitulo)
                    if int(grupoid)>0:
                        ws.write(cont, 2, Inscripcion.objects.filter(carrera__grupocoordinadorcarrera__group__in=request.user.groups.all(), inscripciongrupo__grupo=data['grupo'],id__in=lista).distinct().count(), subtitulo)
                    else:
                        ws.write(cont, 2, Inscripcion.objects.filter(id__in=lista).count(), subtitulo)
                    cont = cont + 1
                    ws.write(cont, 0, "Total Estudiante ", subtitulo)
                    if int(grupoid)>0:
                        ws.write(cont, 2, Inscripcion.objects.filter(carrera__grupocoordinadorcarrera__group__in=request.user.groups.all(), inscripciongrupo__grupo=data['grupo']).distinct().count(), subtitulo)
                    else:
                        ws.write(cont, 2, Inscripcion.objects.filter().count(), subtitulo)
                    cont = cont + 1

                    ws.write(cont, 0, "Fecha Impresion", subtitulo)
                    ws.write(cont, 2, str(datetime.now()), subtitulo)
                    cont = cont + 1

                    ws.write(cont, 0, "Usuario", subtitulo)
                    ws.write(cont, 2, str(request.user), subtitulo)

                    nombre = 'informe_test_grupo' + str(datetime.now()).replace(" ", "").replace(".", "").replace(":","")+'.xls'
                    carpeta=MEDIA_ROOT + '/reportes_excel/'
                    try:
                        os.makedirs(carpeta)
                    except:
                        pass
                    wb.save(carpeta + nombre)


                    return HttpResponse(json.dumps({"result": "ok", "url": "/media/reportes_excel/" + nombre}),
                                        content_type="application/json")

                except Exception as e:
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}), content_type="application/json")






    else:
        data = {'title': 'Listado de Test Efectuado'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']


        else:
            try:

                search = None
                lista=InscripcionTipoTest.objects.filter(estado=True).distinct('inscripcion').values('inscripcion_id')
                # lista=InscripcionTipoTest.objects.filter(estado=True,inscripcion__id=7156).distinct('inscripcion').values('inscripcion_id')


                if 'info' in request.GET:
                    data['error'] = 1
                    data['info'] = request.GET['info']
                else:
                    data['error'] = 0

                if 's' in request.GET:
                    search = request.GET['s']

                if 't' in request.GET:
                    todos = request.GET['t']


                if search:
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')
                    if len(ss)==1:
                        pruebas = Inscripcion.objects.filter(Q(persona__nombres__icontains=search) | Q(persona__apellido1__icontains=search) | Q(persona__apellido2__icontains=search) | Q(persona__cedula__icontains=search),id__in=lista)
                    else:
                        pruebas = Inscripcion.objects.filter(Q(persona__apellido1__icontains=ss[0]) | Q(persona__apellido2__icontains=ss[1]),id__in=lista).order_by('-fecha','persona__apellido1','persona__apellido2','persona__nombres')

                else:

                    pruebas = Inscripcion.objects.filter(id__in=lista)


                if 'g' in request.GET:
                    grupoid = request.GET['g']
                    data['grupo'] = Grupo.objects.get(pk=request.GET['g'])
                    data['grupoid'] = int(grupoid) if grupoid else ""

                    pruebas =  Inscripcion.objects.filter(carrera__grupocoordinadorcarrera__group__in=request.user.groups.all(), inscripciongrupo__grupo=data['grupo'],id__in=lista).distinct()



                paging = MiPaginador(pruebas, 30)
                p = 1
                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                    page = paging.page(p)
                except:
                    page = paging.page(1)

                data['paging'] = paging

                data['grupos'] = Grupo.objects.all().order_by('nombre')
                data['rangospaging'] = paging.rangos_paginado(p)
                data['page'] = page
                data['search'] = search if search else ""
                data['pruebaspsicologicas'] = page.object_list



                return render(request ,"examenexterno/pruebapsicologicas.html" ,  data)

            except Exception as e:
                return HttpResponseRedirect("/?info="+str(e))
