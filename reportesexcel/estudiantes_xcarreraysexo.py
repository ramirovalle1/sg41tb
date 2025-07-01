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
from sga.forms import RangoFacturasForm,RangoNCForm, VinculacionExcelForm, GestionExcelForm, MatriculadosporCarreraExcelForm
from sga.models import Inscripcion,convertir_fecha,Factura,ClienteFactura,TituloInstitucion,ReporteExcel,NotaCreditoInstitucion, Persona,TipoNotaCredito, Carrera, Matricula, RecordAcademico, Egresado, Malla, AsignaturaMalla, NivelMalla, MateriaAsignada, Asignatura, Nivel, Periodo, ProfesorMateria, PagoNivel, Rubro, RubroMatricula, Pago, RubroCuota

from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action :
                try:
                    m = 10
                    carrera= Carrera.objects.filter(pk=request.POST['carrera'])[:1].get()
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
                    ws.write_merge(1, 1,0,m, 'MATRICULADOS POR CARRERA Y SEXO',titulo2)
                    ws.write(3, 0,'Carrera: ' +carrera.nombre , subtitulo)
                    ws.write(6,5,"NIVEL",subtitulo3)
                    ws.write(6,6,"FEMENINO",subtitulo3)
                    ws.write(6,7,"MASCULINO",subtitulo3)

                    fila = 7
                    com = 7
                    detalle = 3
                    columna=5
                    mujeres=0
                    hombres=0
                    nom_periodo= ''
                    nom_nivelmalla= ''

                    periodos = Periodo.objects.filter(inicio__gte='2014-01-01').order_by('nombre')
                    nivelmalla= NivelMalla.objects.filter().order_by('nombre')
                    for peri in periodos:
                        for nivel in nivelmalla:
                            mujeres= Matricula.objects.filter(nivel__carrera=carrera,nivel__nivelmalla=nivel,nivel__periodo=peri,inscripcion__persona__sexo__id=1).count()
                            hombres= Matricula.objects.filter(nivel__carrera=carrera,nivel__nivelmalla=nivel,nivel__periodo=peri,inscripcion__persona__sexo__id=2).count()
                            if mujeres>0 and hombres>0:
                                ws.write_merge(com, fila,0,3,str(peri.nombre), subtitulo)
                                ws.write(fila,columna,str(nivel.nombre),subtitulo3)
                                ws.write(fila,columna+1,mujeres,subtitulo3)
                                ws.write(fila,columna+2,hombres,subtitulo3)
                                com=fila+1
                                fila=fila+1

                    detalle = detalle + fila
                    ws.write(detalle,0, "Fecha Impresion", subtitulo)
                    ws.write(detalle,1, str(datetime.now()), subtitulo)
                    detalle=detalle+2
                    ws.write(detalle,0, "Usuario", subtitulo)
                    ws.write(detalle,1, str(request.user), subtitulo)

                    nombre ='matriculados_carrera_sexo'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")

        else:
            data = {'title': 'Matriculados Por Carrera y Sexo'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform']=MatriculadosporCarreraExcelForm()
                return render(request ,"reportesexcel/estudiantes_xcarreraysexo.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

