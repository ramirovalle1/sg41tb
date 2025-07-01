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
from settings import UTILIZA_GRUPOS_ALUMNOS, EMAIL_ACTIVE,MEDIA_ROOT, SITE_ROOT
from sga.commonviews import addUserData, ip_client_address
from sga.forms import GrupoCongresoForm
from sga.models import Inscripcion,convertir_fecha,TituloInstitucion,ReporteExcel,Carrera,Matricula,Colegio,Canton,EmpresaInscripcion, Grupo
from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):

    try:
        if request.method=='POST':
            action = request.POST['action']
            if action :
                # carrera= Carrera.objects.filter(pk=request.POST['carrera'])[:1].get()
                grupo= Grupo.objects.filter(pk=request.POST['grupo'])[:1].get()

                try:
                    m = 8
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10
                    style1 = xlwt.easyxf('',num_format_str='DD-MMM-YY')
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('Congreso',cell_overwrite_ok=True)
                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,m+2, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,m+2, 'INFORMACION ASISTENTES CONGRESO DE PEDAGOGIA', titulo2)
                    ws.write(3, 0,  'Grupo: ' +grupo.nombre , subtitulo)
                    ws.write(6, 0,  'IDENTIFICACION', titulo)
                    ws.write(6, 1,  'PERSONA', titulo)
                    ws.write(6, 2,  'CONVENCIONAL', titulo)
                    ws.write(6, 3,  'CELULAR', titulo)
                    ws.write(6, 4,  'EMAIL', titulo)

                    matriculados = Matricula.objects.filter(nivel__grupo=grupo).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2')
                    detalle = 4
                    fila = 7

                    identificacion=''
                    estudiante=''
                    matri=''
                    email=''
                    telefono=''
                    celular=''

                    for matri in matriculados:

                        if matri.inscripcion.persona.cedula:
                            identificacion=matri.inscripcion.persona.cedula
                        else:
                            identificacion=matri.inscripcion.persona.pasaporte

                        estudiante=matri.inscripcion.persona.nombre_completo_inverso()

                        try:
                            if matri.inscripcion.persona.telefono_conv:
                                telefono=matri.inscripcion.persona.telefono_conv.replace("-","")
                            else:
                                telefono=''
                        except Exception as ex:
                            pass

                        try:
                            if matri.inscripcion.persona.telefono:
                                celular=matri.inscripcion.persona.telefono.replace("-","")
                            else:
                                celular=''
                        except Exception as ex:
                            pass

                        if matri.inscripcion.persona.email:
                            email=matri.inscripcion.persona.email
                        else:
                            email=''

                        ws.write(fila,0, str(identificacion))
                        ws.write(fila,1, elimina_tildes(estudiante))
                        ws.write(fila,2, telefono)
                        ws.write(fila,3, celular)
                        ws.write(fila,4, email)
                        fila=fila + 1

                    detalle = detalle + fila
                    ws.write(detalle, 0, "Fecha Impresion", subtitulo)
                    ws.write(detalle, 1, str(datetime.now()), subtitulo)
                    detalle=detalle +1
                    ws.write(detalle, 0, "Usuario", subtitulo)
                    ws.write(detalle, 1, str(request.user), subtitulo)

                    nombre ='congreso'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    return HttpResponse(json.dumps({"result":str(ex)+str(matri)}),content_type="application/json")

        else:
            data = {'title': 'Informacion Asistentes Congreso de Pedagogia '}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform']=GrupoCongresoForm()
            return render(request ,"reportesexcel/pedagogia.html" ,  data)

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

