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
from sga.forms import RangoFacturasForm,RangoNCForm, VinculacionExcelForm, GestionExcelForm
from sga.models import Inscripcion,convertir_fecha,Factura,ClienteFactura,TituloInstitucion,ReporteExcel,NotaCreditoInstitucion, Persona,TipoNotaCredito, Carrera, Matricula, RecordAcademico, Egresado, Malla, AsignaturaMalla, NivelMalla, MateriaAsignada, Asignatura, Nivel, Periodo, ProfesorMateria, Grupo, RubroMatricula, RubroCuota, Profesor

from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action :
                try:
                    grupo = Grupo.objects.filter(pk=request.POST['grupo'])[:1].get()
                    nivel = Nivel.objects.filter(grupo=grupo).order_by('-id')[:1].get()

                    nivelesmalla =  NivelMalla.objects.filter(pk__in=AsignaturaMalla.objects.filter(malla=nivel.malla.id).distinct('nivelmalla').values('nivelmalla'),orden__lte=nivel.nivelmalla.orden).order_by('orden')
                    m = 4
                    # total=nivel.matriculados().count()
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
                    ws.write_merge(0, 0,0,m+8, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,m+8, 'SEGUIMIENTO DE GRUPO',titulo2)
                    ws.write(3, 0,'CARRERA: ' +nivel.carrera.nombre , subtitulo)
                    ws.write(4, 0,'GRUPO:   ' +nivel.grupo.nombre, subtitulo)
                    ws.write(5, 0,'NIVEL:   ' +nivel.nivelmalla.nombre, subtitulo)

                    ws.write_merge(6,7,0,0,'NIVEL',subtitulo3)
                    ws.write_merge(6,7,1,4,'ASIGNATURAS',subtitulo3)
                    ws.write_merge(6,7,5,5,'DOCENTE',subtitulo3)
                    ws.write_merge(6,7,6,6,'MATRICULADOS',subtitulo3)
                    ws.write_merge(6,7,7,7,'ASIGNADOS',subtitulo3)
                    ws.write_merge(6,7,8,8,'BECADOS',subtitulo3)
                    ws.write_merge(6,7,9,9,'ASISTENCIA',subtitulo3)
                    ws.write_merge(6,7,10,10,'RECAUDADO',subtitulo3)
                    ws.write_merge(6,7,11,11,'VENCIDO',subtitulo3)
                    ws.write_merge(6,7,12,12,'ESTADO',subtitulo3)
                    ws.write_merge(6,7,13,13,'INICIO',subtitulo3)
                    ws.write_merge(6,7,14,14,'FIN',subtitulo3)
                    fila = 7
                    com = 8
                    columna=1
                    for nm in nivelesmalla:
                        cnv=0
                        becados=0
                        nv=None
                        r_matri=0
                        r_cuota=0
                        r_matri_ven=0
                        r_cuota_ven=0
                        recaudado=0
                        vencido=0
                        asignaturas = Asignatura.objects.filter(pk__in=AsignaturaMalla.objects.filter(nivelmalla=nm,malla__carrera=nivel.carrera).distinct('asignatura').values('asignatura'))
                        if Nivel.objects.filter(nivelmalla=nm,grupo=grupo).exists():
                           nv= Nivel.objects.filter(nivelmalla=nm,grupo=grupo)[:1].get()
                           cnv=nv.matriculados().count()
                           becados = nv.matriculados().filter(becado=True).count()
                           if RubroMatricula.objects.filter(matricula__nivel=nv,rubro__cancelado=True).exists():
                                r_matri =RubroMatricula.objects.filter(matricula__nivel=nv,rubro__cancelado=True).aggregate(Sum('rubro__valor'))['rubro__valor__sum']
                           if RubroCuota.objects.filter(matricula__nivel=nv,rubro__cancelado=True).exists():
                                r_cuota =RubroCuota.objects.filter(matricula__nivel=nv,rubro__cancelado=True).aggregate(Sum('rubro__valor'))['rubro__valor__sum']
                           if RubroCuota.objects.filter(matricula__nivel=nv,rubro__cancelado=False).exists():
                                r_cuota_ven =RubroCuota.objects.filter(matricula__nivel=nv,rubro__cancelado=False).aggregate(Sum('rubro__valor'))['rubro__valor__sum']
                           if RubroMatricula.objects.filter(matricula__nivel=nv,rubro__cancelado=False).exists():
                                r_matri_ven =RubroMatricula.objects.filter(matricula__nivel=nv,rubro__cancelado=False).aggregate(Sum('rubro__valor'))['rubro__valor__sum']

                           recaudado =r_matri + r_cuota
                           vencido =r_matri_ven + r_cuota_ven
                        for a in asignaturas:
                            fila = fila +1
                            c=3
                            asis=0
                            cant=0
                            docente=''
                            if nv:
                                cant = MateriaAsignada.objects.filter(materia__nivel=nv,materia__asignatura=a,matricula__nivel__grupo=grupo).count()
                                if MateriaAsignada.objects.filter(materia__nivel=nv,matricula__nivel__grupo=grupo,materia__asignatura=a).exists():
                                    asis = Decimal(((MateriaAsignada.objects.filter(materia__nivel=nv,matricula__nivel__grupo=grupo,materia__asignatura=a).aggregate(Sum('asistenciafinal'))['asistenciafinal__sum']) *100)/(cant*100)).quantize(Decimal(10)**-2)
                                    materia =  MateriaAsignada.objects.filter(materia__nivel=nv,matricula__nivel__grupo=grupo,materia__asignatura=a)[:1].get()
                                    profesor=ProfesorMateria.objects.filter(materia=materia.materia).distinct('profesor__persona__id').values('profesor__id')
                                    for p in Profesor.objects.filter(id__in=profesor):
                                        docente=docente+' '+p.persona.apellido1 +' '+p.persona.nombres+' '
                                    if materia.materia.cerrado:
                                        estado='CERRADA'
                                    else:
                                        estado='ABIERTA'
                                    ws.write(fila,12,  estado,subtitulo4 )
                                    ws.write(fila,13,  str(materia.materia.fin),subtitulo4 )
                                    ws.write(fila,14,  str(materia.materia.fin),subtitulo4 )
                            ws.write_merge(fila, fila,columna,columna+3, a.nombre )
                            ws.write_merge(fila, fila,5,5, docente )
                            ws.write(fila, columna+6, cant,subtitulo4 )
                            ws.write( fila,9, str(asis),subtitulo4 )
                        ws.write_merge(com, fila,0, 0, nm.nombre,subtitulo4 )
                        ws.write_merge(com, fila,6, 6, str(cnv),subtitulo4 )
                        ws.write_merge(com, fila,8, 8, str(becados),subtitulo4 )
                        ws.write_merge(com, fila,10, 10,"$" + str(recaudado),subtitulo4 )
                        ws.write_merge(com, fila,11, 11,"$"+ str(vencido),subtitulo4 )

                        com=fila+1

                    ws.write(fila+4, 0, "Fecha Impresion", subtitulo)
                    ws.write(fila+4, 1, str(datetime.now()), subtitulo)
                    ws.write(fila+5, 0, "Usuario", subtitulo)
                    ws.write(fila+5, 1, str(request.user), subtitulo)

                    nombre ='seguimiento_grupo'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")

        else:
            data = {'title': 'Seguimiento por Grupo'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                return render(request ,"reportesexcel/seguimiento_grupo.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

