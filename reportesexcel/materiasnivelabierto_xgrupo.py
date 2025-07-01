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
                    m = 4
                    grupo = Grupo.objects.filter(pk=request.POST['grupo'])[:1].get()
                    nivel = Nivel.objects.filter(grupo=grupo,cerrado=False).order_by('-id')[:1].get()
                    if nivel.matriculados()!=None:
                        total=nivel.matriculados().count()
                    else:
                        total=0
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
                    ws.write_merge(0, 0,0,m+total, tit.nombre , titulo2)
                    nivelesmalla =  NivelMalla.objects.filter(pk__in=AsignaturaMalla.objects.filter(malla=nivel.malla.id,nivelmalla=nivel.nivelmalla.id).distinct('nivelmalla').values('nivelmalla'),orden__lte=nivel.nivelmalla.orden).order_by('orden')
                    ws.write_merge(1, 1,0,m+total, 'CALIFICACIONES POR GRUPO DE ESTUDIANTES DE NIVEL ABIERTO',titulo2)
                    ws.write(3, 0,'CARRERA: ' +nivel.carrera.nombre , subtitulo)
                    ws.write(4, 0,'GRUPO:   ' +nivel.grupo.nombre, subtitulo)
                    ws.write(5, 0,'NIVEL:   ' +nivel.nivelmalla.nombre, subtitulo)

                    fila = 8
                    com = 9
                    detalle = 3
                    c=0
                    columna=1
                    estudiante=''
                    for nm in nivelesmalla:
                        asignaturas = Asignatura.objects.filter(pk__in=AsignaturaMalla.objects.filter(nivelmalla=nm,malla__carrera=nivel.carrera).distinct('asignatura').values('asignatura'))
                        for a in asignaturas:
                            fila = fila +1
                            c=3
                            ws.write_merge(fila, fila,columna,columna+3, a.nombre , subtitulo)
                            if nivel.matriculados():
                                for matri in nivel.matriculados():
                                    estudiante=matri.inscripcion
                                    telefono1=''
                                    telefono2=''
                                    matricula = Matricula.objects.get(pk=matri.id)
                                    if MateriaAsignada.objects.filter(materia__asignatura=a,matricula=matri).exists():
                                        matasig=MateriaAsignada.objects.filter(materia__asignatura=a,matricula=matri)[:1].get()
                                        if matasig.notafinal>=NOTA_PARA_APROBAR and matasig.asistenciafinal>=ASIST_PARA_APROBAR:
                                           estado="A"
                                        else:
                                           estado="R"
                                    else:
                                        estado="P"

                                    c=c+1
                                    if estado=="R":
                                        if matasig.notafinal<NOTA_PARA_APROBAR and matasig.asistenciafinal<ASIST_PARA_APROBAR:
                                            estado="RN  RA"
                                        elif matasig.notafinal<NOTA_PARA_APROBAR:
                                            estado="RN"
                                        ws.write(fila,columna+c,estado,subtitulo4)
                                    else:
                                        ws.write(fila,columna+c,estado,subtitulo3)

                                    ws.write_merge(6,8,columna+c,columna + c, matri.inscripcion.persona.nombre_completo_inverso(),subtitulo3)

                                    if matri.inscripcion.persona.telefono_conv:
                                        telefono1=matri.inscripcion.persona.telefono_conv

                                    if matri.inscripcion.persona.telefono:
                                        telefono2=matri.inscripcion.persona.telefono

                                    ws.write(fila+1,columna+c,str(telefono1), subtitulo3)
                                    ws.write(fila+2,columna+c,str(telefono2), subtitulo3)

                        ws.write_merge(com, fila,0,0, nm.nombre , subtitulo3)
                        com=fila+1
                    ws.write(fila+1,columna+3,"TELF. CONV", subtitulo3)
                    ws.write(fila+2,columna+3,"CELULAR", subtitulo3)
                    detalle = detalle + fila

                    ws.write(detalle, 0, "Equivalencia", subtitulo)
                    ws.write(detalle+1, 1, "A: Aprobado", subtitulo)
                    ws.write(detalle+2, 1, "RN: Reprobado por Nota", subtitulo)
                    ws.write(detalle+3, 1, "RA: Reprobado por Asistencia", subtitulo)
                    ws.write(detalle+4, 1, "C: En Curso", subtitulo)
                    ws.write(detalle+5, 1, "P: Pendiente", subtitulo)

                    ws.write(detalle+6, 1, "Fecha Impresion", subtitulo)
                    ws.write(detalle+6, 2, str(datetime.now()), subtitulo)
                    ws.write(detalle+7, 1, "Usuario", subtitulo)
                    ws.write(detalle+7, 2, str(request.user), subtitulo)

                    nombre ='materiasnivelabierto_xgrupo'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")

        else:
            data = {'title': 'Materia de Nivel Abierto por Grupo'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
            return render(request ,"reportesexcel/materiasnivelabierto_xgrupo.html" ,  data)
        return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))


