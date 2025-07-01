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
from settings import UTILIZA_GRUPOS_ALUMNOS, EMAIL_ACTIVE,MEDIA_ROOT, ASIG_VINCULACION, ASIG_PRATICA,NOTA_PARA_APROBAR,ASIST_PARA_APROBAR
from sga.commonviews import addUserData, ip_client_address
from sga.forms import RangoFacturasForm,RangoNCForm, VinculacionExcelForm, GestionExcelForm
from sga.models import Inscripcion,convertir_fecha,Factura,ClienteFactura,TituloInstitucion,ReporteExcel,NotaCreditoInstitucion, Persona,TipoNotaCredito, Carrera, Matricula, RecordAcademico, Egresado, Malla, AsignaturaMalla, NivelMalla, MateriaAsignada, Asignatura, Nivel, Periodo, ProfesorMateria, Grupo, RubroMatricula, RubroCuota

from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action :
                try:
                    m = 5
                    grupo = Grupo.objects.filter(pk=request.POST['grupo'])[:1].get()
                    nivel = Nivel.objects.filter(grupo=grupo).order_by('-id')[:1].get()
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo4 = xlwt.easyxf('font: name Times New Roman;align: wrap on, vert centre, horiz center')
                    subtitulo3 = xlwt.easyxf('font: name Times New Roman,colour black, bold on; align: wrap on, vert centre, horiz center')
                    subtitulo.font.height = 20*10
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('Registros',cell_overwrite_ok=True)
                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,3,m+4, tit.nombre , titulo2)
                    ws.write_merge(1, 1,3,m+4, 'INFORMACION DE ESTUDIANTES POR GRUPO',titulo2)
                    ws.write(3, 0,'CARRERA: ' +nivel.carrera.nombre , subtitulo)
                    ws.write(4, 0,'GRUPO:   ' +nivel.grupo.nombre, subtitulo)

                    ws.write(7, 0,'IDENTIFICACION', subtitulo)
                    ws.write(7, 1,'NOMBRES Y APELLIDOS', subtitulo)
                    ws.write(7, 6,'CONVENCIONAL', subtitulo)
                    ws.write(7, 7,'CELULAR', subtitulo)
                    ws.write(7, 8,'DIRECCION', subtitulo)
                    ws.write(7, 9,'TIPO DE SANGRE', subtitulo)
                    ws.write(7, 10,'EMAIL INSTITUCIONAL', subtitulo)
                    ws.write(7, 11,'EMAIL PERSONAL', subtitulo)

                    fila = 8
                    com = 9
                    detalle = 3
                    c=0
                    columna=0
                    estudiante=''
                    for matri in nivel.matriculados():
                        estudiante=matri.inscripcion
                        # print(estudiante)
                        telefono1=''
                        telefono2=''
                        cedula=''
                        pasaporte=''
                        tiposangre=''
                        if matri.inscripcion.persona.cedula:
                            identificacion=matri.inscripcion.persona.cedula
                        else:
                            identificacion=matri.inscripcion.persona.pasaporte

                        ws.write(fila,columna,str(identificacion))
                        ws.write_merge(fila,fila,columna+1,columna+5,elimina_tildes(matri.inscripcion.persona.nombre_completo()))
                        ws.write(fila,columna+5,str(matri.inscripcion.sesion.nombre))

                        if matri.inscripcion.persona.telefono_conv:
                            telefono1=matri.inscripcion.persona.telefono_conv

                        if matri.inscripcion.persona.telefono:
                            telefono2=matri.inscripcion.persona.telefono

                        if matri.inscripcion.persona.sangre:
                            tiposangre=matri.inscripcion.persona.sangre

                        ws.write(fila,columna+6,str(telefono1))
                        ws.write(fila,columna+7,str(telefono2))
                        ws.write(fila,columna+8,elimina_tildes(matri.inscripcion.persona.direccion))
                        ws.write(fila,columna+9,elimina_tildes(tiposangre))
                        ws.write(fila,columna+10,elimina_tildes(matri.inscripcion.persona.emailinst))
                        ws.write(fila,columna+11,elimina_tildes(matri.inscripcion.persona.email))

                        com=fila+1
                        fila = fila + 1
                    detalle = detalle + fila

                    ws.write(detalle, 1, "Fecha Impresion", subtitulo)
                    ws.write(detalle, 2, str(datetime.now()), subtitulo)
                    ws.write(detalle+1, 1, "Usuario", subtitulo)
                    ws.write(detalle+1, 2, str(request.user), subtitulo)

                    nombre ='estudiantes_xgrupo'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")

        else:
            data = {'title': 'Informacion de Estudiantes por Grupo'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
            return render(request ,"reportesexcel/estudiantes_xgrupo.html" ,  data)
        return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))


