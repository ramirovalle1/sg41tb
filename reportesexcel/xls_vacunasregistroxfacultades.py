from datetime import datetime
import json
import xlwt
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from settings import MEDIA_ROOT, PROFESORES_GROUP_ID, ALUMNOS_GROUP_ID, SISTEMAS_GROUP_ID
from sga.commonviews import addUserData, ip_client_address
from sga.models import TituloInstitucion,ReporteExcel,convertir_fecha,Persona,RegistroVacunas,Coordinacion,Carrera,InscripcionGrupo,\
    Matricula, Inscripcion,elimina_tildes
from sga.forms import  VacunadosporCoordinacionExcelForm

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            coordinacion = Coordinacion.objects.get(pk=request.POST['coordinacion'])
            carreras = Carrera.objects.filter(coordinacion__id = coordinacion.id,activo=True, carrera=True).exclude(id__in=[66,64,63]).order_by('nombre')
            # carreras = Carrera.objects.filter(coordinacion__id = coordinacion.id,activo=True, carrera=True,pk__in=[58,59]).exclude(id__in=[66,64,63]).order_by('nombre')
            resumido = str(request.POST['resumido'])

            if action :
                try:
                    m = 5
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10
                    # estudiantes = RegistroVacunas.objects.filter(usuario__groups__id__in=[ALUMNOS_GROUP_ID])

                    if resumido != '':
                        m = 5
                        titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                        titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                        titulo.font.height = 20 * 11
                        titulo2.font.height = 20 * 11
                        subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                        subtitulo.font.height = 20 * 10
                        wb = xlwt.Workbook()
                        ws = wb.add_sheet('Registros', cell_overwrite_ok=True)

                        tit = TituloInstitucion.objects.all()[:1].get()
                        ws.write_merge(0, 0, 0, m, tit.nombre, titulo2)
                        ws.write_merge(1, 1, 0, m, 'TOTAL ALUMNOS VACUNADOS POR FACULTAD', titulo2)
                        fila=3
                        ws.write(fila, 0,'CARRERA', titulo)
                        ws.write(fila, 1,'MUJERES', titulo)
                        ws.write(fila, 2,'HOMBRES', titulo)
                        ws.write(fila, 3,'PRIMERA DOSIS', titulo)
                        ws.write(fila, 4,'SEGUNDA DOSIS', titulo)
                        ws.write(fila, 5,'TERCERA DOSIS', titulo)
                        ws.write(fila, 6,'NO VACUNADOS', titulo)
                        ws.write(fila, 7,'HA TENIDO COVID', titulo)
                        fila=4
                        totfacultad_primeradosis = 0
                        totfacultad_segundadosis = 0
                        totfacultad_terceradosis = 0
                        totfacultad_novacunados = 0
                        totfacultad_hatenidocovid = 0
                        totfacultad_hombres = 0
                        totfacultad_mujeres = 0
                        detalle = 3
                        nomcarrera=''
                        for c in carreras:
                            nomcarrera= elimina_tildes(c.alias)
                            totcarrera_primeradosis = 0
                            totcarrera_segundadosis = 0
                            totcarrera_terceradosis = 0
                            totcarrera_novacunados = 0
                            totcarrera_hatenidocovid = 0
                            totcarrera_hombres = 0
                            totcarrera_mujeres = 0

                            for inscrito in Inscripcion.objects.filter(carrera=c):
                                if RegistroVacunas.objects.filter(usuario__groups__id__in=[ALUMNOS_GROUP_ID],persona=inscrito.persona).exists():
                                    print(inscrito)
                                    est = RegistroVacunas.objects.filter(usuario__groups__id__in=[ALUMNOS_GROUP_ID],persona=inscrito.persona)[:1].get()
                                    if est.primeradosis:
                                        totcarrera_primeradosis += 1
                                    if est.segundadosis:
                                        totcarrera_segundadosis +=1
                                    if est.terceradosis:
                                        totcarrera_terceradosis+=1
                                    if not est.estavacunado:
                                        totcarrera_novacunados+=1
                                    if est.hatenidocovid:
                                        totcarrera_hatenidocovid+=1
                                    if est.persona.sexo.id==1:
                                       totcarrera_mujeres+=1
                                    else:
                                        totcarrera_hombres+=1

                            ws.write(fila, 0, nomcarrera, subtitulo)
                            ws.write(fila, 1, totcarrera_mujeres, subtitulo)
                            ws.write(fila, 2, totcarrera_hombres, subtitulo)
                            ws.write(fila, 3, totcarrera_primeradosis, subtitulo)
                            ws.write(fila, 4, totcarrera_segundadosis, subtitulo)
                            ws.write(fila, 5, totcarrera_terceradosis, subtitulo)
                            ws.write(fila, 6, totcarrera_novacunados, subtitulo)
                            ws.write(fila, 7, totcarrera_hatenidocovid, subtitulo)
                            totfacultad_primeradosis += totcarrera_primeradosis
                            totfacultad_segundadosis += totcarrera_segundadosis
                            totfacultad_terceradosis += totcarrera_terceradosis
                            totfacultad_novacunados += totcarrera_novacunados
                            totfacultad_hatenidocovid += totcarrera_hatenidocovid
                            totfacultad_hombres += totcarrera_hombres
                            totfacultad_mujeres += totcarrera_mujeres
                            fila = fila+1
                        ws.write(fila, 0, 'TOTAL ' +str(coordinacion.nombre), subtitulo)
                        ws.write(fila, 1, totfacultad_mujeres, subtitulo)
                        ws.write(fila, 2, totfacultad_hombres, subtitulo)
                        ws.write(fila, 3, totfacultad_primeradosis, subtitulo)
                        ws.write(fila, 4, totfacultad_segundadosis, subtitulo)
                        ws.write(fila, 5, totfacultad_terceradosis, subtitulo)
                        ws.write(fila, 6, totfacultad_novacunados, subtitulo)
                        ws.write(fila, 7, totfacultad_hatenidocovid, subtitulo)

                        ws.write(fila+2, 0, "Fecha Impresion", subtitulo)
                        ws.write(fila+2, 2, str(datetime.now()), subtitulo)
                        ws.write(fila+3, 0, "Usuario", subtitulo)
                        ws.write(fila+3, 2, str(request.user), subtitulo)

                        nombre ='vacunados_facultades'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                        wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                        return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")
                    else:
                        #detallado
                        m = 5
                        titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                        titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                        titulo.font.height = 20 * 11
                        titulo2.font.height = 20 * 11
                        subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                        subtitulo.font.height = 20 * 10
                        wb = xlwt.Workbook()
                        ws = wb.add_sheet('Registros', cell_overwrite_ok=True)

                        tit = TituloInstitucion.objects.all()[:1].get()
                        ws.write_merge(0, 0, 0, m, tit.nombre, titulo2)
                        ws.write_merge(1, 1, 0, m, 'TOTAL ALUMNOS VACUNADOS POR FACULTAD', titulo2)
                        fila=3
                        ws.write(fila, 0,'CARRERA', titulo)
                        ws.write(fila, 1,'GRUPO', titulo)
                        ws.write(fila, 2,'MUJERES', titulo)
                        ws.write(fila, 3,'HOMBRES', titulo)
                        ws.write(fila, 4,'PRIMERA DOSIS', titulo)
                        ws.write(fila, 5,'SEGUNDA DOSIS', titulo)
                        ws.write(fila, 6,'TERCERA DOSIS', titulo)
                        ws.write(fila, 7,'NO VACUNADOS', titulo)
                        ws.write(fila, 8,'HA TENIDO COVID', titulo)
                        fila=4
                        totfacultad_primeradosis = 0
                        totfacultad_segundadosis = 0
                        totfacultad_terceradosis = 0
                        totfacultad_novacunados = 0
                        totfacultad_hatenidocovid = 0
                        totfacultad_hombres = 0
                        totfacultad_mujeres = 0
                        detalle = 3
                        nomcarrera=''
                        nombre_grupo=''

                        for c in carreras:
                            nivel_grupo = Matricula.objects.filter(nivel__carrera=c).order_by('nivel__grupo').distinct('nivel__grupo').values('nivel__grupo')
                            nomcarrera= elimina_tildes(c.alias)
                            totcarrera_primeradosis = 0
                            totcarrera_segundadosis = 0
                            totcarrera_terceradosis = 0
                            totcarrera_novacunados = 0
                            totcarrera_hatenidocovid = 0
                            tot_hombrescarrera = 0
                            tot_mujerescarrera = 0

                            for grupo in nivel_grupo:
                                h_grupo = 0
                                m_grupo = 0
                                totgrupo_primeradosis = 0
                                totgrupo_segundadosis = 0
                                totgrupo_terceradosis = 0
                                totgrupo_novacunados = 0
                                totgrupo_hatenidocovid = 0
                                # matriculas = Matricula.objects.filter(nivel__grupo__id=grupo['nivel__grupo']).values('inscripcion').distinct('inscripcion')
                                inscritos = InscripcionGrupo.objects.filter(grupo__id=grupo['nivel__grupo']).values('inscripcion').distinct('inscripcion')
                                if inscritos.count()>0:
                                   for inscrito in inscritos:
                                        nombre_grupo = elimina_tildes(InscripcionGrupo.objects.filter(inscripcion=inscrito['inscripcion'])[:1].get().grupo.nombre)
                                        estudiante=Inscripcion.objects.get(pk=inscrito['inscripcion'])
                                        if RegistroVacunas.objects.filter(usuario__groups__id__in=[ALUMNOS_GROUP_ID],persona=estudiante.persona).exists():
                                            print(estudiante)
                                            est = RegistroVacunas.objects.filter(usuario__groups__id__in=[ALUMNOS_GROUP_ID],persona=estudiante.persona)[:1].get()
                                            if est.primeradosis:
                                                totgrupo_primeradosis += 1
                                            if est.segundadosis:
                                                totgrupo_segundadosis +=1
                                            if est.terceradosis:
                                                totgrupo_terceradosis+=1
                                            if not est.estavacunado:
                                                totgrupo_novacunados+=1
                                            if est.hatenidocovid:
                                                totgrupo_hatenidocovid+=1
                                            if est.persona.sexo.id==1:
                                               m_grupo+=1
                                            else:
                                                h_grupo+=1
                                if m_grupo>0 or h_grupo>0:
                                    ws.write(fila, 0, nomcarrera, subtitulo)
                                    ws.write(fila, 1, nombre_grupo, subtitulo)
                                    ws.write(fila, 2, m_grupo, subtitulo)
                                    ws.write(fila, 3, h_grupo, subtitulo)
                                    ws.write(fila, 4, totgrupo_primeradosis)
                                    ws.write(fila, 5, totgrupo_segundadosis)
                                    ws.write(fila, 6, totgrupo_terceradosis)
                                    ws.write(fila, 7, totgrupo_novacunados)
                                    ws.write(fila, 8, totgrupo_hatenidocovid)
                                    fila=fila+1

                                totcarrera_primeradosis+=totgrupo_primeradosis
                                totcarrera_segundadosis+=totgrupo_segundadosis
                                totcarrera_terceradosis+=totgrupo_terceradosis
                                totcarrera_novacunados+=totgrupo_novacunados
                                totcarrera_hatenidocovid+=totgrupo_hatenidocovid
                                tot_hombrescarrera+=h_grupo
                                tot_mujerescarrera+=m_grupo

                            ws.write(fila, 0, nomcarrera, subtitulo)
                            if tot_mujerescarrera>0 or tot_hombrescarrera>0:
                                ws.write(fila, 2, tot_mujerescarrera, subtitulo)
                                ws.write(fila, 3, tot_hombrescarrera, subtitulo)
                                ws.write(fila, 4, totcarrera_primeradosis, subtitulo)
                                ws.write(fila, 5, totcarrera_segundadosis, subtitulo)
                                ws.write(fila, 6, totcarrera_terceradosis, subtitulo)
                                ws.write(fila, 7, totcarrera_novacunados, subtitulo)
                                ws.write(fila, 8, totcarrera_hatenidocovid, subtitulo)
                                totfacultad_primeradosis += totcarrera_primeradosis
                                totfacultad_segundadosis += totcarrera_segundadosis
                                totfacultad_terceradosis += totcarrera_terceradosis
                                totfacultad_novacunados += totcarrera_novacunados
                                totfacultad_hatenidocovid += totcarrera_hatenidocovid
                                totfacultad_mujeres += tot_mujerescarrera
                                totfacultad_hombres += tot_hombrescarrera
                                fila = fila+1
                        ws.write(fila, 0, 'TOTAL ' +str(coordinacion.nombre), subtitulo)
                        ws.write(fila, 2, totfacultad_mujeres, subtitulo)
                        ws.write(fila, 3, totfacultad_hombres, subtitulo)
                        ws.write(fila, 4, totfacultad_primeradosis, subtitulo)
                        ws.write(fila, 5, totfacultad_segundadosis, subtitulo)
                        ws.write(fila, 6, totfacultad_terceradosis, subtitulo)
                        ws.write(fila, 7, totfacultad_novacunados, subtitulo)
                        ws.write(fila, 8, totfacultad_hatenidocovid, subtitulo)

                        ws.write(fila+2, 0, "Fecha Impresion", subtitulo)
                        ws.write(fila+2, 2, str(datetime.now()), subtitulo)
                        ws.write(fila+3, 0, "Usuario", subtitulo)
                        ws.write(fila+3, 2, str(request.user), subtitulo)

                        nombre ='vacunados_facultades'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
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
                data['generarform']=VacunadosporCoordinacionExcelForm()
                return render(request ,"reportesexcel/vacunasxfacultades.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

