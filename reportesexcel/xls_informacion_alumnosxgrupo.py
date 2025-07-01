from datetime import datetime, timedelta
import json
import xlwt
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from settings import MEDIA_ROOT
from sga.commonviews import addUserData
from sga.forms import RangoFacturasForm
from sga.models import convertir_fecha,TituloInstitucion, ReporteExcel,Matricula, Grupo,Nivel,Inscripcion,InscripcionGrupo
from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action :
                try:
                    grupo = Grupo.objects.filter(pk=request.POST['grupo'])[:1].get()
                    inscritos = InscripcionGrupo.objects.filter(grupo=grupo).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')
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
                    ws.write_merge(1, 1,0,14, 'LISTADO DE ALUMNOS POR GRUPO', titulo2)
                    ws.write(2, 0, 'GRUPO: ', titulo)
                    ws.write(2, 1, elimina_tildes((grupo.nombre)), titulo)
                    fila=5

                    ws.write(fila, 0,  'CI/PAS', titulo)
                    ws.write(fila, 1,  'ESTUDIANTE', titulo)
                    ws.write(fila, 2,  'EMAIL PERSONAL', titulo)
                    ws.write(fila, 3,  'EMAIL INSTITUCIONAL', titulo)
                    ws.write(fila, 4,  'F. NACIMIENTO', titulo)
                    ws.write(fila, 5,  'PROVINCIA', titulo)
                    ws.write(fila, 6,  'PARROQUIA', titulo)
                    ws.write(fila, 7,  'DIRECCION', titulo)
                    matri=None
                    i=None

                    for i in inscritos:
                        estudiante=''
                        identificacion=''
                        email=''
                        emailinst=''
                        nacimiento=''
                        provincia=''
                        parroquia=''
                        direccion=''
                        estudiante=elimina_tildes(i.inscripcion.persona.nombre_completo())
                        print(estudiante)
                        fila=fila+1
                        if i.inscripcion.persona.cedula:
                            identificacion=i.inscripcion.persona.cedula
                        else:
                            identificacion=i.inscripcion.persona.pasaporte

                        ws.write(fila, 0, str(identificacion))
                        ws.write(fila, 1, estudiante)
                        try:
                            emailinst = elimina_tildes(i.inscripcion.persona.emailinst)
                        except:
                            emailinst = ''
                        try:
                            email= elimina_tildes(i.inscripcion.persona.email)
                        except:
                            email = ''

                        ws.write(fila, 2, email)
                        ws.write(fila, 3, emailinst)
                        try:
                            nacimiento = str(i.inscripcion.persona.nacimiento)
                        except:
                            nacimiento = ''
                        try:
                            provincia = elimina_tildes(i.inscripcion.persona.provinciaresid)
                        except:
                            provincia = ''
                        try:
                            parroquia = elimina_tildes(i.inscripcion.persona.parroquia)
                        except:
                            parroquia = ''
                        try:
                            direccion = elimina_tildes(i.inscripcion.persona.direccion_completa())
                        except:
                            direccion = ''

                        ws.write(fila, 4, elimina_tildes(nacimiento))
                        ws.write(fila, 5, provincia)
                        ws.write(fila, 6, parroquia)
                        ws.write(fila, 7, direccion)

                    fila=fila+3

                    nombre ='informacion_estudiantesxgrupo'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(ex)
                    return HttpResponse(json.dumps({"result":str(ex) + " "+  str(i)}),content_type="application/json")
        else:
            data = {'title': 'Informacion de Estudiantes por Grupo'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                return render(request ,"reportesexcel/informacion_alumnosxgrupo.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")
    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))


