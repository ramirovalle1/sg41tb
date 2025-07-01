from datetime import datetime, timedelta
import json
from django.db.models import Sum, Q
import xlwt
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from settings import MEDIA_ROOT
from sga.commonviews import addUserData
from sga.forms import GraduadosAnioCarreraForm, CoordinacionForm
from sga.models import TituloInstitucion, Rubro, Inscripcion, MONTH_CHOICES, Pago, Graduado, Carrera, Persona, RolPerfilProfesor, CoordinacionDepartamento, DepartamentoGroup, Profesor, SolicitudEstudiante, RubroEspecieValorada, GestionTramite, Coordinacion, ReporteExcel


@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            print(request.POST)
            action = request.POST['action']
            if action :
                try:
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on; align: wrap on, vert center, horiz center')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert center, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('Listado',cell_overwrite_ok=True)

                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,5, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,5, 'LISTADO DE SOLICITUDES PENDIENTES DOCENTES', titulo2)

                    coordinacion = Coordinacion.objects.get(pk=request.POST['coordinacion'])
                    ws.write(3, 0, 'Facultad:', subtitulo)
                    ws.write(3, 1, coordinacion.nombre, subtitulo)

                    fila=5
                    ws.write(fila, 0, 'DOCENTE', titulo)
                    ws.write(fila, 1, 'TRAMITES PENDIENTES AUTORIZADOS', titulo)
                    ws.write(fila, 2, 'TRAMITES PROCESADOS', titulo)
                    ws.write(fila, 3, 'TIEMPO ATENCION PROMEDIO (HORAS)', titulo)

                    rol_profesor = RolPerfilProfesor.objects.filter(coordinacion=coordinacion)
                    profesores = Profesor.objects.filter(id__in=rol_profesor.values('profesor'),activo=True).order_by('persona__apellido1','persona__apellido2','persona__nombres')
                    # profesores = Profesor.objects.filter(id__in=[457,458]).order_by('persona__apellido1','persona__apellido2','persona__nombres')

                    # print(profesores.count())
                    for p in profesores:
                        fila=fila+1
                        cont=0
                        contador=0
                        tiempo = timedelta(seconds=0).seconds
                        tiempo2 = timedelta(seconds=0).seconds
                        hour = 0
                        minutes = 0
                        solicitudes_estudiantes = 0
                        # solicitudes_estudiantes = SolicitudEstudiante.objects.filter(Q(profesor=p)|Q(rubro__rubroespecievalorada__usrasig=p.persona.usuario))
                        if SolicitudEstudiante.objects.filter(Q(profesor=p,rubro__rubroespecievalorada__aplicada=True)|Q(rubro__rubroespecievalorada__aplicada=True,rubro__rubroespecievalorada__usrasig=p.persona.usuario)).exists():
                            solicitudes_estudiantes = SolicitudEstudiante.objects.filter(Q(profesor=p,rubro__rubroespecievalorada__aplicada=True)|Q(rubro__rubroespecievalorada__aplicada=True,rubro__rubroespecievalorada__usrasig=p.persona.usuario)).order_by('-rubro__rubroespecievalorada__serie','-rubro__rubroespecievalorada__fecha')
                            for solicitud in solicitudes_estudiantes:
                                if solicitud.rubro.especie_valorada().tienegestion_docente():
                                    # if solicitud.rubro.especie_valorada().aplicada:
                                    gestion = solicitud.rubro.especie_valorada().tienegestion_docente()
                                    if gestion.fecharespuesta and gestion.fechaasignacion:
                                        cont = cont+1
                                        tiempo =  tiempo+(gestion.fecharespuesta - gestion.fechaasignacion).seconds
                                    else:
                                        contador = contador + 1

                            solicitudes_estudiantes = solicitudes_estudiantes.count()

                            if cont>0:
                                tiempo_promedio = float(tiempo)/cont
                                dias = tiempo_promedio * (1/86400)
                                seconds = tiempo_promedio % (24 * 3600)
                                hour = seconds // 3600
                                seconds %= 3600
                                minutes = seconds // 60
                                seconds %= 60
                                especie = SolicitudEstudiante.objects.filter().order_by('-rubro__fecha','rubro__inscripcion__persona__apellido1')

                                hora_total = (tiempo_promedio)/3600

                        ws.write(fila, 0, p.persona.nombre_completo_inverso(), subtitulo)
                        ws.write(fila, 1, SolicitudEstudiante.objects.filter(Q(profesor=p,rubro__rubroespecievalorada__aplicada=False)|Q(rubro__rubroespecievalorada__aplicada=False,rubro__rubroespecievalorada__usrasig=p.persona.usuario)).count(), subtitulo)
                        ws.write(fila, 2, cont, subtitulo)
                        ws.write(fila, 3, float(str(int(hour))+'.'+str(int(minutes))), subtitulo)
                        # ws.write(fila, 5, str(dias)+' dias, '+str(hour)+' horas, '+str(minutes)+' minutos, '+str(seconds)+'segundos', subtitulo)


                    fila=fila+3
                    ws.write(fila, 0, "Fecha Impresion", subtitulo)
                    ws.write(fila, 1, str(datetime.now()), subtitulo)
                    ws.write(fila+1, 0, "Usuario", subtitulo)
                    ws.write(fila+1, 1, str(request.user), subtitulo)



                    nombre ='resumen_tramitesdocentes'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(ex)
                    return HttpResponse(json.dumps({"result":str(ex) }),content_type="application/json")
        else:
            data = {'title': 'Promedio solicitudes bandeja atencion docente'}
            addUserData(request,data)

            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['generarform']=CoordinacionForm()
                return render(request ,"reportesexcel/tiemporespuesta_bandejadocente.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")
    except Exception as e:
        print(e)
        return HttpResponseRedirect('/?info='+str(e))