from datetime import datetime,timedelta
import json
import xlrd
import xlwt
import requests
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
from settings import UTILIZA_GRUPOS_ALUMNOS, EMAIL_ACTIVE,MEDIA_ROOT, ASIG_VINCULACION, ASIG_PRATICA, NOTA_PARA_APROBAR, ASIST_PARA_APROBAR,DEFAULT_PASSWORD
from sga.commonviews import addUserData, ip_client_address
from sga.forms import RangoFacturasForm,RangoNCForm, VinculacionExcelForm, GestionExcelForm
from sga.models import Inscripcion,convertir_fecha,Factura,ClienteFactura,TituloInstitucion,ReporteExcel,NotaCreditoInstitucion, Persona,TipoNotaCredito, Carrera, Matricula, RecordAcademico, Egresado, Malla, AsignaturaMalla, NivelMalla, MateriaAsignada, Asignatura, Nivel, Periodo, ProfesorMateria, InscripcionPracticas, EstudianteVinculacion

from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action :
                try:
                    nivel = Nivel.objects.filter(pk=request.POST['nivel'])[:1].get()
                    nivelesmalla =  NivelMalla.objects.filter(pk__in=AsignaturaMalla.objects.filter(malla=nivel.malla.id).distinct('nivelmalla').values('nivelmalla')).order_by('orden')
                    m = 4
                    total=nivel.matriculados().count()
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo4 = xlwt.easyxf('font: name Times New Roman, colour red, bold on;align: wrap on, vert centre, horiz center')
                    subtitulo3 = xlwt.easyxf('font: name Times New Roman; align: wrap on, vert centre, horiz center')
                    subtitulo.font.height = 20*10
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('Registros',cell_overwrite_ok=True)

                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,m+total, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,m+total, 'ESTADO DE MATERIAS POR NIVELES',titulo2)
                    ws.write(3, 1,'CARRERA: ' +nivel.carrera.nombre , subtitulo)
                    ws.write(4, 1,'GRUPO:   ' +nivel.grupo.nombre, subtitulo)
                    ws.write(5, 1,'NIVEL:   ' +nivel.nivelmalla.nombre, subtitulo)

                    fila = 8
                    com = 9
                    detalle = 3
                    c=0
                    columna=1
                    estudiante=''
                    data={}
                    for nm in nivelesmalla:
                        asignaturas = Asignatura.objects.filter(pk__in=AsignaturaMalla.objects.filter(nivelmalla=nm,malla__carrera=nivel.carrera,malla__vigente=True).distinct('asignatura').values('asignatura'))
                        for a in asignaturas:
                            fila = fila +1
                            c=3
                            ws.write_merge(fila, fila,columna,columna+3, a.nombre , subtitulo)
                            for matri in nivel.matriculados():
                                estudiante=matri.inscripcion
                                telefono1=''
                                telefono2=''
                                if RecordAcademico.objects.filter(asignatura=a,inscripcion=matri.inscripcion).exists():
                                    record=RecordAcademico.objects.filter(asignatura=a,inscripcion=matri.inscripcion)[:1].get()
                                    if record.aprobada:
                                        estado="A"
                                    else:
                                        estado="R"
                                elif MateriaAsignada.objects.filter(materia__asignatura=a,matricula=matri).exists():
                                        estado="C"
                                else:
                                        estado="P"
                                c=c+1

                                if 'PREPROFESIONALES' in a.nombre and matri.inscripcion.tiene_malla_nueva():
                                    if InscripcionPracticas.objects.filter(inscripcion=matri.inscripcion, nivelmalla=nm).exists():
                                        estado = "A"
                                    elif EstudianteVinculacion.objects.filter(inscripcion=matri.inscripcion, nivelmalla=nm).exists():
                                        estado = "A"
                                    else:
                                        estado = "P"

                                if estado=="R":
                                    if record.nota<NOTA_PARA_APROBAR and record.asistencia<ASIST_PARA_APROBAR:
                                        estado="RN  RA"
                                    elif record.nota<NOTA_PARA_APROBAR:
                                        estado="RN"
                                    else:
                                        estado="RA"
                                    ws.write(fila,columna+c,estado,subtitulo4)
                                else:
                                    ws.write(fila,columna+c,estado,subtitulo3)
                                ws.write_merge(6,8,columna+c,columna + c, matri.inscripcion.persona.nombre_completo_inverso(),subtitulo3)

                                if matri.inscripcion.persona.telefono_conv:
                                    telefono1=matri.inscripcion.persona.telefono_conv

                                if matri.inscripcion.persona.telefono:
                                    telefono2=matri.inscripcion.persona.telefono

                                #ws.write(fila+1,columna+c,str(telefono1), subtitulo3)
                                #ws.write(fila+2,columna+c,str(telefono2), subtitulo3)

                        ws.write_merge(com, fila,0,0, nm.nombre , subtitulo3)
                        com=fila+1
                    c=3
                    estado=''
                    for matri in nivel.matriculados():

                        c=c+1
                        telefono1=''
                        telefono2=''
                        fila=com
                        if DEFAULT_PASSWORD == 'itb':
                            try:
                                if matri.inscripcion.persona.extranjero:
                                    ced = matri.inscripcion.persona.pasaporte
                                    op=0
                                else:
                                    op=1
                                    ced = matri.inscripcion.persona.cedula
                                datos = requests.get('http://sga.buckcenter.com.ec/api',params={'a': 'datos_ingles', 'ced':ced , 'op':op })
                                if datos.status_code==200:
                                    otrasnotas=datos.json()['notas']
                                    for on in otrasnotas:
                                        if on[5]=='APROBADO':
                                            estado='A'
                                        elif on[5]=='REPROBADO':
                                            estado='R'
                                        else:
                                            estado='C'
                                        ws.write(fila,columna+c,on [0]+' '+estado)
                                        fila=fila+1
                            except Exception as e:
                                pass
                        if matri.inscripcion.persona.telefono_conv:
                            telefono1=matri.inscripcion.persona.telefono_conv

                        if matri.inscripcion.persona.telefono:
                            telefono2=matri.inscripcion.persona.telefono
                        fila=fila+1
                        ws.write(fila,columna+c,str(telefono1), subtitulo3)
                        ws.write(fila+1,columna+c,str(telefono2), subtitulo3)

                    ws.write(fila,columna+3,"TELF. CONV", subtitulo3)
                    ws.write(fila+1,columna+3,"CELULAR", subtitulo3)
                    detalle = detalle + fila

                    ws.write(detalle, 0, "Equivalencia", subtitulo)
                    ws.write(detalle+1, 1, "A: Aprobado", subtitulo)
                    ws.write(detalle+2, 1, "RN: Reprobado por Nota", subtitulo)
                    ws.write(detalle+3, 1, "RA: Reprobado por Asistencia", subtitulo)
                    ws.write(detalle+4, 1, "C: En Curso", subtitulo)
                    ws.write(detalle+5, 1, "P: Pendiente", subtitulo)

                    ws.write(detalle+7, 0, "Fecha Impresion", subtitulo)
                    ws.write(detalle+7, 1, str(datetime.now()), subtitulo)
                    detalle=detalle +8
                    ws.write(detalle, 0, "Usuario", subtitulo)
                    ws.write(detalle, 1, str(request.user), subtitulo)

                    nombre ='mat_x_grupo'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(estudiante)}),content_type="application/json")

        else:
            data = {'title': 'Materias por Grupo'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                return render(request ,"reportesexcel/materias_grupo.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

