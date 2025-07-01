from datetime import datetime, timedelta
import json
import xlwt
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from settings import MEDIA_ROOT
from sga.commonviews import addUserData
from sga.forms import EstudiantesProgramaVinculacionForm
from sga.models import convertir_fecha, TituloInstitucion, ActividadVinculacion, ReporteExcel, AprobacionVinculacion, \
    Programa
from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action :
                inicio = request.POST['inicio']
                fin = request.POST['fin']
                programa = request.POST['programa']
                a=''
                try:
                    fechai = convertir_fecha(inicio)
                    fechaf = convertir_fecha(fin)+timedelta(hours=23,minutes=59)
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('registros',cell_overwrite_ok=True)
                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,8, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,8, 'LISTADO DE ESTUDIANTES VINCULACION POR PROYECTO', titulo2)
                    ws.write(3, 0, 'DESDE', titulo)
                    ws.write(3, 1, str((fechai.date())), titulo)
                    ws.write(4, 0, 'HASTA:', titulo)
                    ws.write(4, 1, str((fechaf.date())), titulo)
                    fila = 6
                    programa = Programa.objects.filter(pk=programa).order_by('-inicio')[:1].get()
                    actividad = ActividadVinculacion.objects.filter(inicio__gte=fechai,inicio__lte=fechaf,fin__lte=datetime.now(),programa=programa).order_by('inicio')
                    for a in actividad:
                        est_vinculacion = AprobacionVinculacion.objects.filter(estudiantevinculacion__actividad=a,revisionestudiante=True,revisionproyecto=True,revisiondocente=True).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2')
                        if est_vinculacion.exists():
                            try:
                                ws.write(fila,0 , 'ACTIVIDAD:', titulo)
                                ws.write(fila,1 , elimina_tildes(a.nombre))
                            except:
                                ws.write(fila,1 , '')
                            try:
                                ws.write(fila+1,0 , 'PROYECTO:', titulo)
                                ws.write(fila+1,1 , elimina_tildes(a.programa.nombre))
                            except:
                                ws.write(fila+1,1 , '')
                            try:
                                ws.write(fila+2,0 , 'CONVENIO:', titulo)
                                ws.write(fila+2,1 , elimina_tildes(a.convenio.institucion))
                            except:
                                ws.write(fila+2,1 , '')
                            try:
                                ws.write(fila+3,0 , 'LUGAR:', titulo)
                                ws.write(fila+3,1 , elimina_tildes(a.lugar))
                            except:
                                ws.write(fila+3,1 , '')
                            try:
                                ws.write(fila+4,0 , 'FECHA INICIO:', titulo)
                                ws.write(fila+4,1 , str(a.inicio))
                            except:
                                ws.write(fila+4,1 , '')
                            try:
                                ws.write(fila+5,0 , 'FECHA FIN:', titulo)
                                ws.write(fila+5,1 , str(a.fin))
                            except:
                                ws.write(fila+5,1 , '')
                            try:
                                ws.write(fila+6,0 , 'LIDER:', titulo)
                                ws.write(fila+6,1 , elimina_tildes(a.lider))
                            except:
                                ws.write(fila+6,1 , '')
                            try:
                                ws.write(fila+7,0 , 'OBJETIVO:', titulo)
                                ws.write(fila+7,1 , elimina_tildes(a.objetivo))
                            except:
                                ws.write(fila+7,1 , '')
                            try:
                                ws.write(fila+8,0 , 'CARRERA:', titulo)
                                ws.write(fila+8,1 , elimina_tildes(a.carrera.nombre))
                            except:
                                ws.write(fila+8,1 , '')
                            try:
                                ws.write(fila+9,0 , 'FACULTAD:', titulo)
                                ws.write(fila+9,1 , elimina_tildes(a.carrera.coordinacion_pertenece()))
                            except:
                                ws.write(fila+9,1 , '')

                            fila = fila+10
                            ws.write(fila, 0, 'FECHA REGISTRO', titulo)
                            ws.write(fila, 1, 'ESTUDIANTE', titulo)
                            ws.write(fila, 2, 'CEDULA', titulo)
                            ws.write(fila, 3, 'CELULAR', titulo)
                            ws.write(fila, 4, 'EMAIL', titulo)
                            ws.write(fila, 5, 'REVISION ESTUDIANTE', titulo)
                            ws.write(fila, 6, 'REVISION PROYECTO', titulo)
                            ws.write(fila, 7, 'REVISION DOCENTE', titulo)
                            ws.write(fila, 8, 'APROBADO', titulo)
                            ws.write(fila, 9, 'HORAS ACTIVIDAD', titulo)
                            fila=fila+1
                            for e in est_vinculacion:
                                try:
                                    ws.write(fila,0 , str(e.fecha.date()))
                                except:
                                    ws.write(fila,0 , '')
                                try:
                                    ws.write(fila,1 , elimina_tildes(e.inscripcion.persona.nombre_completo_inverso()))
                                except:
                                    ws.write(fila,1 , '')
                                try:
                                    if e.inscripcion.persona.cedula:
                                        ws.write(fila,2 , elimina_tildes(e.inscripcion.persona.cedula))
                                    else:
                                        ws.write(fila,2 , elimina_tildes(e.inscripcion.persona.pasaporte))
                                except:
                                    ws.write(fila,2 , '')
                                try:
                                    ws.write(fila,3 , elimina_tildes(e.inscripcion.persona.telefono))
                                except:
                                    ws.write(fila,3 , '')
                                try:
                                    ws.write(fila,4 , elimina_tildes(e.inscripcion.persona.email))
                                except:
                                    ws.write(fila,4 , '')
                                try:
                                    if e.revisionestudiante==True:
                                        ws.write(fila,5 , 'SI')
                                    else:
                                        ws.write(fila,5 , 'NO')
                                except:
                                    ws.write(fila,5 , '')
                                try:
                                    if e.revisionproyecto==True:
                                        ws.write(fila,6 , 'SI')
                                    else:
                                        ws.write(fila,6 , 'NO')
                                except:
                                    ws.write(fila,6 , '')
                                try:
                                    if e.revisiondocente==True:
                                        ws.write(fila,7 , 'SI')
                                    else:
                                        ws.write(fila,7 , 'NO')
                                except:
                                    ws.write(fila,7 , '')
                                try:
                                    if e.revisionestudiante==True and e.revisiondocente==True and e.revisionproyecto==True:
                                        ws.write(fila,8 , 'SI')
                                    else:
                                        ws.write(fila,8 , 'NO')
                                except:
                                    ws.write(fila,8 , '')
                                try:
                                    if e.estudiantevinculacion.horas:
                                        horas=e.estudiantevinculacion.horas
                                        ws.write(fila,9 , str(horas))
                                    else:
                                        horas=''
                                        ws.write(fila,9 , horas)
                                except:
                                    ws.write(fila,9 , '')
                                fila = fila +1
                            fila = fila +1

                    ws.write(fila, 0, "Fecha Impresion: ", subtitulo)
                    ws.write(fila, 1, str(datetime.now()), subtitulo)
                    ws.write(fila+1, 0, "Usuario: ", subtitulo)
                    ws.write(fila+1, 1, str(request.user), subtitulo)
                    nombre ='actividades_porproyecto'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    return HttpResponse(json.dumps({"result":str(ex) + " "+  str(a.inscripcion)}),content_type="application/json")
        else:
            data = {'title': 'Actividades por Proyecto Vinculacion'}
            addUserData(request,data)
            reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
            data['reportes'] = reportes
            data['generarform']=EstudiantesProgramaVinculacionForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
            return render(request ,"reportesexcel/listadoproyectosvinculacion.html" ,  data)
        return HttpResponseRedirect("/reporteexcel")
    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))