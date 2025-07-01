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
from settings import UTILIZA_GRUPOS_ALUMNOS, EMAIL_ACTIVE,MEDIA_ROOT, ASIG_VINCULACION, ASIG_PRATICA,ASIGNATURA_EXAMEN_GRADO_CONDU
from sga.commonviews import addUserData, ip_client_address
from sga.forms import RangoFacturasForm,RangoNCForm, VinculacionExcelForm, EficienciaExcelForm
from sga.models import Inscripcion,convertir_fecha,TituloInstitucion,ReporteExcel,Carrera, RecordAcademico,Egresado, \
     InscripcionExamen, ExamenPractica,NotasComplexivo
from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action :

                try:
                    carrera= Carrera.objects.filter(pk=request.POST['carrera'])[:1].get()
                    inicio = request.POST['inicio']
                    fin = request.POST['fin']
                    fechai = convertir_fecha(inicio)
                    fechaf = convertir_fecha(fin)
                    egresados = Egresado.objects.filter(inscripcion__carrera=carrera,fechaegreso__gte=fechai,fechaegreso__lte=fechaf).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2')
                    #egresados = Egresado.objects.filter(inscripcion__carrera=carrera,pk=13106).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2')
                    m = 7
                    eg=0
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('Registros',cell_overwrite_ok=True)

                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,m+2, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,m+2, 'LISTADO DE EGRESADOS ', titulo2)
                    ws.write(2, 0, 'CARRERA:', titulo)
                    ws.write(2, 1, carrera.nombre, titulo)
                    ws.write(3, 0, 'DESDE', titulo)
                    ws.write(3, 1, str((fechai.date())), titulo)
                    ws.write(4, 0, 'HASTA:', titulo)
                    ws.write(4, 1, str((fechaf.date())), titulo)
                    ws.write(6, 0,  'CEDULA', titulo)
                    ws.write(6, 1,  'NOMBRES', titulo)
                    ws.write(6, 2,  'FECHA EX. TEORICO', titulo)
                    ws.write(6, 3,  'NOTA EX. TEORICO', titulo)
                    ws.write(6, 4,  'FECHA EX. PRACTICO', titulo)
                    ws.write(6, 5,  'NOTA EX. PRACTICO', titulo)
                    ws.write(6, 6,  'NOTA FINAL', titulo)
                    ws.write(6, 7,  'EQUIVALENTE', titulo)
                    ws.write(6, 8,  'NOTA EN RECORD', titulo)
                    fila =6
                    detalle = 11
                    c=0
                    sob=0
                    muyb=0
                    bue=0
                    reg=0
                    otr=0
                    for e in egresados:
                        print(e.inscripcion.id)
                        equival=''
                        notateorico = 'NO TIENE EXAMEN TEORICO'
                        notapractica= 'NO TIENE EXAMEN PRACTICO'
                        f_teorico=''
                        f_practico=''
                        record=0
                        record2=0
                        fila = fila +1
                        columna=0
                        eg=eg +1
                        c=c+1
                        ws.write(fila,columna , str(e.inscripcion.persona.cedula))
                        ws.write(fila,columna+1, e.inscripcion.persona.nombre_completo_inverso())
                        if InscripcionExamen.objects.filter(inscripcion=e.inscripcion,valida=True).exists():
                            puntajeteorico =InscripcionExamen.objects.filter(inscripcion=e.inscripcion,valida=True)[:1].get().puntaje
                            if puntajeteorico:
                                notateorico = puntajeteorico
                            else:
                                notateorico = 0

                            f_teorico =  InscripcionExamen.objects.filter(inscripcion=e.inscripcion,valida=True)[:1].get().fecha
                            f_teorico=str(f_teorico.date())
                            # if RecordAcademico.objects.filter(asignatura__id=511,inscripcion=e.inscripcion).exists():
                            if RecordAcademico.objects.filter(asignatura__id__in=ASIGNATURA_EXAMEN_GRADO_CONDU,inscripcion=e.inscripcion).exists():
                                # record =RecordAcademico.objects.filter(asignatura__id=511,inscripcion=e.inscripcion)[:1].get().nota
                                record =RecordAcademico.objects.filter(asignatura__id__in=ASIGNATURA_EXAMEN_GRADO_CONDU,inscripcion=e.inscripcion)[:1].get().nota
                                record2 =RecordAcademico.objects.filter(asignatura__id__in=ASIGNATURA_EXAMEN_GRADO_CONDU,inscripcion=e.inscripcion)[:1].get().nota
                            if ExamenPractica.objects.filter(inscripcion=e.inscripcion,valida=True).exists():
                                notapractica= ExamenPractica.objects.filter(inscripcion=e.inscripcion,valida=True)[:1].get().puntaje
                                f_practico= ExamenPractica.objects.filter(inscripcion=e.inscripcion,valida=True)[:1].get().fecha
                                f_practico=str(f_practico.date())
                        else:
                            if NotasComplexivo.objects.filter(egresado=e).exists():
                                complexivo= NotasComplexivo.objects.get(egresado=e)
                                notateorico=complexivo.teorico
                                notapractica=complexivo.practico
                                f_teorico=str(complexivo.fecha.date())
                                f_practico=str(complexivo.fecha.date())
                                record=complexivo.total
                            if RecordAcademico.objects.filter(asignatura__id__in=ASIGNATURA_EXAMEN_GRADO_CONDU,inscripcion=e.inscripcion).exists():
                                # record =RecordAcademico.objects.filter(asignatura__id=511,inscripcion=e.inscripcion)[:1].get().nota
                                record2 =RecordAcademico.objects.filter(asignatura__id__in=ASIGNATURA_EXAMEN_GRADO_CONDU,inscripcion=e.inscripcion)[:1].get().nota
                        if len(str(notateorico)) >4 and len(str(notapractica)) >4:
                            otr= otr +1
                            pass
                        else:
                            if notateorico >= 70 and notapractica >= 70 :
                                if record:
                                    if record >= 70 and record <80:
                                        equival = 'REGULAR'
                                        reg = reg +1
                                    elif record >= 80 and record <90:
                                        equival = 'BUENO'
                                        bue = bue +1
                                    elif record >= 90 and record <96:
                                        equival = 'MUY BUENO'
                                        muyb = muyb + 1
                                    elif record >= 96 and record <= 700:
                                        equival = 'SOBRESALIENTE'
                                        sob=sob + 1
                                else:
                                    otr= otr +1
                            else:
                                otr= otr +1

                        ws.write(fila,columna+2 ,f_teorico)
                        ws.write(fila,columna+3 ,notateorico)
                        ws.write(fila,columna+4 ,f_practico)
                        ws.write(fila,columna+5 ,notapractica)
                        ws.write(fila,columna+6 ,record)
                        ws.write(fila,columna+7 ,equival)
                        ws.write(fila,columna+8 ,record2)

                    ws.write(fila+5,0 ,'RESUMEN',subtitulo)
                    ws.write(fila+6,0 ,'SOBRESALIENTE',subtitulo)
                    ws.write(fila+6,1 ,sob)
                    ws.write(fila+7,0 ,'MUY BUENO',subtitulo)
                    ws.write(fila+7,1 ,muyb)
                    ws.write(fila+8,0 ,'BUENO',subtitulo)
                    ws.write(fila+8,1 ,bue)
                    ws.write(fila+9,0 ,'REGULAR',subtitulo)
                    ws.write(fila+9,1 ,reg)
                    ws.write(fila+10,0 ,'OTRO',subtitulo)
                    ws.write(fila+10,1 ,otr)


                    detalle = detalle + fila
                    ws.write(detalle+1, 0, "Fecha Impresion", subtitulo)
                    ws.write(detalle+1, 1, str(datetime.now()), subtitulo)
                    ws.write(detalle+2, 0, "Usuario", subtitulo)
                    ws.write(detalle+2, 1, str(request.user), subtitulo)

                    nombre ='resumen_ex_complexivo'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")
                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")

        else:
            data = {'title': 'Estudiantes Matriculados por Nivel'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform']=EficienciaExcelForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
                return render(request ,"reportesexcel/resumen_egresados.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

