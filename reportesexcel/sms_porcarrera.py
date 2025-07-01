from datetime import datetime,timedelta
import json
import xlrd
import xlwt
from decimal import Decimal
from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.db.models import Sum
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from django.utils.encoding import force_str
from decorators import secure_module
from settings import UTILIZA_GRUPOS_ALUMNOS, EMAIL_ACTIVE,MEDIA_ROOT, ASIG_VINCULACION, ASIG_PRATICA
from sga.commonviews import addUserData, ip_client_address
from sga.forms import MatriculadosporCarreraExcelForm
from sga.models import ReporteExcel,Carrera,TituloInstitucion,convertir_fecha,Matricula,Nivel, Inscripcion

from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action :
                try:
                    detallado = request.POST['detallado']
                    resumido = request.POST['resumido']
                    if detallado != '':
                        carrera = Carrera.objects.filter(pk=request.POST['carrera'])[:1].get()
                        matriculas = Matricula.objects.filter(nivel__carrera=carrera,nivel__cerrado=False).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2')
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

                        tit = TituloInstitucion.objects.all()[:1].get()
                        ws.write_merge(0, 0,0,m, tit.nombre , titulo2)
                        ws.write_merge(1, 1,0,m, 'MATRICULADOS por Carrera SMS',titulo2)
                        ws.write(3, 0,'CARRERA: ' +carrera.nombre , subtitulo)

                        ws.write(6,0,"CEDULA",subtitulo)
                        ws.write_merge(6,6,1,3, "NOMBRE ALUMNO",subtitulo)
                        ws.write(6,4,"CELULAR",subtitulo)
                        ws.write(6,5,"EMAIL INST",subtitulo)
                        ws.write(6,6,"EMAIL 1",subtitulo)
                        ws.write(6,7,"EMAIL 2",subtitulo)
                        ws.write(6,8,"EMAIL 3",subtitulo)
                        ws.write(6,9,"PERIODO MATRICULACION",subtitulo)

                        fila = 7
                        com = 7
                        detalle = 3
                        columna=3
                        matri=''

                        for matri in matriculas:
                            celular=''
                            correo1=''
                            correo2=''
                            correo3=''
                            correo4=''
                            if matri.inscripcion.persona.telefono:
                                celular=matri.inscripcion.persona.telefono
                            else:
                                celular=''

                            if matri.inscripcion.persona.emailinst:
                                correo1=matri.inscripcion.persona.emailinst
                            else:
                                correo1=''

                            if matri.inscripcion.persona.email:
                                correo2=matri.inscripcion.persona.email
                            else:
                                correo2=''

                            if matri.inscripcion.persona.email1:
                                correo3=matri.inscripcion.persona.email1
                            else:
                                correo3=''

                            if matri.inscripcion.persona.email2:
                                correo4=matri.inscripcion.persona.email2
                            else:
                                correo4=''

                            try:
                                if matri.inscripcion.persona.cedula:
                                    identificacion = matri.inscripcion.persona.cedula
                                else:
                                    identificacion = matri.inscripcion.persona.pasaporte
                            except Exception as ex:
                                identificacion = ''

                            if matri.nivel.periodo:
                                periodo = matri.nivel.periodo.nombre
                            else:
                                periodo = ''

                            ws.write(fila,0, identificacion )
                            ws.write_merge(com, fila,1,3,str(elimina_tildes(matri.inscripcion.persona.nombre_completo_inverso())))
                            ws.write(fila,columna+1, celular )
                            ws.write(fila,columna+2, correo1 )
                            ws.write(fila,columna+3, correo2 )
                            ws.write(fila,columna+4, correo3 )
                            ws.write(fila,columna+5, correo4 )
                            ws.write(fila,columna+6, periodo )
                            com=fila+1
                            fila=fila+1

                        detalle = detalle + fila
                        ws.write(detalle,0, "Fecha Impresion", subtitulo)
                        ws.write(detalle,1, str(datetime.now()), subtitulo)
                        detalle=detalle+1
                        ws.write(detalle,0, "Usuario", subtitulo)
                        ws.write(detalle,1, str(request.user), subtitulo)

                    elif resumido != '':
                        m = 10
                        titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                        titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                        titulo.font.height = 20 * 11
                        titulo2.font.height = 20 * 11
                        subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                        subtitulo3 = xlwt.easyxf('font: name Times New Roman; align: wrap on, vert centre, horiz center')
                        subtitulo.font.height = 20 * 10
                        wb = xlwt.Workbook()
                        ws = wb.add_sheet('Registros', cell_overwrite_ok=True)

                        tit = TituloInstitucion.objects.all()[:1].get()
                        ws.write_merge(0, 0, 0, m, tit.nombre, titulo2)
                        ws.write_merge(1, 1, 0, m, 'TOTAL ALUMNOS POR CARRERA', titulo2)

                        ws.write(3, 0, "CARRERA", subtitulo)
                        ws.write(3, 1, "INSCRITOS ACTIVOS", subtitulo)
                        ws.write(3, 2, "MATRICULADOS", subtitulo)

                        fila = 4
                        detalle = 3

                        carreras = Carrera.objects.filter(activo=True, carrera=True).order_by('nombre')
                        for c in carreras:
                            matriculas = Matricula.objects.filter(inscripcion__persona__usuario__is_active=True, inscripcion__carrera=c, nivel__cerrado=False)
                            inscritos = Inscripcion.objects.filter(persona__usuario__is_active=True, carrera=c)
                            ws.write(fila, 0, elimina_tildes(c.nombre))
                            ws.write(fila, 1, inscritos.count())
                            ws.write(fila, 2, matriculas.count())
                            fila=fila+1

                        detalle = detalle + fila
                        ws.write(detalle,0, "Fecha Impresion", subtitulo)
                        ws.write(detalle,1, str(datetime.now()), subtitulo)
                        detalle=detalle+1
                        ws.write(detalle,0, "Usuario", subtitulo)
                        ws.write(detalle,1, str(request.user), subtitulo)

                    nombre ='matriculados_sms'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)+' '+ str(matri)}),content_type="application/json")

        else:
            data = {'title': 'Matriculados por Carrera SMS'}
            addUserData(request,data)

            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform']=MatriculadosporCarreraExcelForm()
                return render(request ,"reportesexcel/sms_porcarrera.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

