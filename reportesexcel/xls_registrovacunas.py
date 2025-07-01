from datetime import datetime
import json
import xlwt
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from settings import MEDIA_ROOT, PROFESORES_GROUP_ID, ALUMNOS_GROUP_ID, SISTEMAS_GROUP_ID
from sga.commonviews import addUserData, ip_client_address
from sga.models import TituloInstitucion,ReporteExcel,convertir_fecha,Persona,RegistroVacunas

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action :
                try:
                    m = 5
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10
                    administrativos = RegistroVacunas.objects.filter().exclude(usuario__groups__id__in=[PROFESORES_GROUP_ID,ALUMNOS_GROUP_ID,SISTEMAS_GROUP_ID])
                    docentes = RegistroVacunas.objects.filter(usuario__groups__id__in=[PROFESORES_GROUP_ID])
                    estudiantes = RegistroVacunas.objects.filter(usuario__groups__id__in=[ALUMNOS_GROUP_ID])

                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('ADMINISTRATIVOS',cell_overwrite_ok=True)
                    wsd = wb.add_sheet('DOCENTES',cell_overwrite_ok=True)
                    wse = wb.add_sheet('ALUMNOS',cell_overwrite_ok=True)

                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,5, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,5, 'LISTADO PERSONAL ADMINISTRATIVO', titulo2)

                    a=''
                    d=''
                    est=''

                    fila=3
                    ws.write(fila, 0,'PRIMERA DOSIS', titulo)
                    ws.write(fila, 1,'SEGUNDA DOSIS', titulo)
                    ws.write(fila, 2,'TERCERA DOSIS', titulo)
                    ws.write(fila, 3,'NO VACUNADOS', titulo)
                    ws.write(fila, 4,'HA TENIDO COVID', titulo)

                    fila=4
                    primeradosis = 0
                    segundadosis = 0
                    terceradosis = 0
                    novacunados = 0
                    hatenidocovid = 0

                    for a in administrativos:
                        if a.primeradosis:
                            primeradosis = primeradosis + 1
                        if a.segundadosis:
                            segundadosis = segundadosis + 1
                        if a.terceradosis:
                            terceradosis = terceradosis + 1
                        if not a.estavacunado:
                            novacunados = novacunados + 1
                        if a.hatenidocovid:
                            hatenidocovid = hatenidocovid + 1

                    ws.write(fila, 0, primeradosis, subtitulo)
                    ws.write(fila, 1, segundadosis, subtitulo)
                    ws.write(fila, 2, terceradosis, subtitulo)
                    ws.write(fila, 3, novacunados,  subtitulo)
                    ws.write(fila, 4, hatenidocovid, subtitulo)

                    fila = fila+1

                    ws.write(fila+1, 0, "Fecha Impresion", subtitulo)
                    ws.write(fila+1, 2, str(datetime.now()), subtitulo)
                    ws.write(fila+2, 0, "Usuario", subtitulo)
                    ws.write(fila+2, 2, str(request.user), subtitulo)

# ------------------------------------------------------- DOCENTES ------------------------------------------------------
                    wsd.write_merge(0, 0,0,5, tit.nombre , titulo2)
                    wsd.write_merge(1, 1,0,5, 'LISTADO PERSONAL DOCENTE', titulo2)

                    fila=3
                    wsd.write(fila, 0,'PRIMERA DOSIS', titulo)
                    wsd.write(fila, 1,'SEGUNDA DOSIS', titulo)
                    wsd.write(fila, 2,'TERCERA DOSIS', titulo)
                    wsd.write(fila, 3,'NO VACUNADOS', titulo)
                    wsd.write(fila, 4,'HA TENIDO COVID', titulo)

                    fila=4
                    primeradosis = 0
                    segundadosis = 0
                    terceradosis = 0
                    novacunados = 0
                    hatenidocovid = 0

                    for d in docentes:
                        if d.primeradosis:
                            primeradosis = primeradosis + 1
                        if d.segundadosis:
                            segundadosis = segundadosis + 1
                        if d.terceradosis:
                            terceradosis = terceradosis + 1
                        if not d.estavacunado:
                            novacunados = novacunados + 1
                        if d.hatenidocovid:
                            hatenidocovid = hatenidocovid + 1

                    wsd.write(fila, 0, primeradosis, subtitulo)
                    wsd.write(fila, 1, segundadosis, subtitulo)
                    wsd.write(fila, 2, terceradosis, subtitulo)
                    wsd.write(fila, 3, novacunados, subtitulo)
                    wsd.write(fila, 4, hatenidocovid, subtitulo)

                    fila = fila+1

                    wsd.write(fila+1, 0, "Fecha Impresion", subtitulo)
                    wsd.write(fila+1, 2, str(datetime.now()), subtitulo)
                    wsd.write(fila+2, 0, "Usuario", subtitulo)
                    wsd.write(fila+2, 2, str(request.user), subtitulo)

                    # ------------------------------------------------------- ALUMNOS ------------------------------------------------------
                    wse.write_merge(0, 0,0,5, tit.nombre , titulo2)
                    wse.write_merge(1, 1,0,5, 'LISTADO ALUMNOS', titulo2)

                    fila=3
                    wse.write(fila, 0,'PRIMERA DOSIS', titulo)
                    wse.write(fila, 1,'SEGUNDA DOSIS', titulo)
                    wse.write(fila, 2,'TERCERA DOSIS', titulo)
                    wse.write(fila, 3,'NO VACUNADOS', titulo)
                    wse.write(fila, 4,'HA TENIDO COVID', titulo)

                    fila=4
                    primeradosis = 0
                    segundadosis = 0
                    terceradosis = 0
                    novacunados = 0
                    hatenidocovid = 0

                    for est in estudiantes:
                        if est.primeradosis:
                            primeradosis = primeradosis + 1
                        if est.segundadosis:
                            segundadosis = segundadosis + 1
                        if est.terceradosis:
                            terceradosis = terceradosis + 1
                        if not est.estavacunado:
                            novacunados = novacunados + 1
                        if est.hatenidocovid:
                            hatenidocovid = hatenidocovid + 1

                    wse.write(fila, 0, primeradosis, subtitulo)
                    wse.write(fila, 1, segundadosis, subtitulo)
                    wse.write(fila, 2, terceradosis, subtitulo)
                    wse.write(fila, 3, novacunados, subtitulo)
                    wse.write(fila, 4, hatenidocovid, subtitulo)

                    fila = fila+1

                    wse.write(fila+1, 0, "Fecha Impresion", subtitulo)
                    wse.write(fila+1, 2, str(datetime.now()), subtitulo)
                    wse.write(fila+2, 0, "Usuario", subtitulo)
                    wse.write(fila+2, 2, str(request.user), subtitulo)

                    nombre ='vacunados_covid'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")
                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)+" "+str(ex)}),content_type="application/json")

        else:
            data = {'title': 'Registro de Vacunados Covid'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                return render(request ,"reportesexcel/registro_vacunas.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

