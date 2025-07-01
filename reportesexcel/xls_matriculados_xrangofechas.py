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
from sga.forms import  EficienciaExcelForm
from sga.models import convertir_fecha,TituloInstitucion,ReporteExcel,Carrera, Matricula, RecordAcademico, Egresado, Malla, AsignaturaMalla, NivelMalla, MateriaAsignada, Asignatura, Nivel, Periodo, ProfesorMateria, PagoNivel, Rubro, RubroMatricula, Pago, RubroCuota

from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action :
                try:
                    carrera= Carrera.objects.filter(pk=request.POST['carrera'])[:1].get()
                    inicio = convertir_fecha(request.POST['inicio'])
                    fin = convertir_fecha(request.POST['fin'])
                    m = 8
                    matriculas = Matricula.objects.filter(nivel__carrera=carrera,fecha__gte=inicio,fecha__lte=fin).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2')
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
                    ws.write_merge(1, 1,0,m, 'MATRICULADOS POR RANGO DE FECHAS',titulo2)
                    ws.write(3, 0,'CARRERA: ' +carrera.nombre , subtitulo)
                    ws.write(6,0,"APELLIDO PATERNO",subtitulo3)
                    ws.write(6,1,"APELLIDO MATERNO",subtitulo3)
                    ws.write(6,2,"NOMBRES",subtitulo3)
                    ws.write(6,3,"CEDULA",subtitulo3)
                    ws.write(6,4,"FECHA DE NACIMIENTO",subtitulo3)
                    ws.write(6,5,"SEXO",subtitulo3)
                    ws.write(6,6,"NIVEL",subtitulo3)

                    fila = 7
                    com = 7
                    detalle = 3
                    columna=3
                    matri=''
                    identificacion=''

                    for matri in matriculas:
                        # print(matri)

                        if matri.inscripcion.persona.cedula:
                            identificacion=matri.inscripcion.persona.cedula
                        else:
                            identificacion=elimina_tildes(matri.inscripcion.persona.pasaporte)

                        ws.write(fila,0,elimina_tildes(matri.inscripcion.persona.apellido1),subtitulo3)
                        ws.write(fila,1,elimina_tildes(matri.inscripcion.persona.apellido2),subtitulo3)
                        ws.write(fila,2,elimina_tildes(matri.inscripcion.persona.nombres), subtitulo3)
                        ws.write(fila,3,identificacion,subtitulo3)
                        ws.write(fila,4,str(matri.inscripcion.persona.nacimiento),subtitulo3)
                        ws.write(fila,5,str(matri.inscripcion.persona.sexo.nombre),subtitulo3)
                        ws.write(fila,6,str(matri.nivel.nivelmalla.nombre),subtitulo3)

                        fila=fila+1

                    detalle = detalle + fila
                    ws.write(detalle,0, "Fecha Impresion", subtitulo)
                    ws.write(detalle,1, str(datetime.now()), subtitulo)
                    detalle=detalle+2
                    ws.write(detalle,0, "Usuario", subtitulo)
                    ws.write(detalle,1, str(request.user), subtitulo)

                    nombre ='matriculados_xrangofechas'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)+' '+ str(matri)}),content_type="application/json")

        else:
            data = {'title': 'Matriculados por Rango de Fechas'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform']=EficienciaExcelForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
                return render(request ,"reportesexcel/xls_matriculadosxrango.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

