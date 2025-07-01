from datetime import datetime,timedelta
import json
import xlrd
import xlwt
import locale
import os
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
from settings import UTILIZA_GRUPOS_ALUMNOS, EMAIL_ACTIVE,MEDIA_ROOT, ASIG_VINCULACION, ASIG_PRATICA,JR_USEROUTPUT_FOLDER,MEDIA_URL, \
     SITE_ROOT,CONSUMIDOR_FINAL
from sga.commonviews import addUserData, ip_client_address
from sga.forms import RangoFacturasForm
from sga.models import Inscripcion,convertir_fecha,Factura,ClienteFactura,TituloInstitucion,ReporteExcel,NotaCreditoInstitucion, Persona,TipoNotaCredito, Carrera, Matricula, RecordAcademico, Egresado, Malla, AsignaturaMalla, NivelMalla, MateriaAsignada, Asignatura, Nivel, Periodo, ProfesorMateria, PagoNivel, Rubro, RubroMatricula, Pago, RubroCuota, RubroInscripcion
from fpdf import FPDF

from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action  =='generarexcel':
                try:
                    carreras = Carrera.objects.filter(activo=True,carrera=True).order_by('nombre')
                    #carreras = Carrera.objects.filter(pk=39).order_by('nombre')
                    fechahoy = datetime.now().date()
                    inicio = convertir_fecha(request.POST['inicio'])
                    fin = convertir_fecha(request.POST['fin'])
                    m = 11

                    #inscritos = Inscripcion.objects.filter(Q(retiradomatricula__activo=False)|Q(retiradomatricula=None),persona__usuario__is_active=True,carrera__carrera=True,carrera__activo=True,graduado=None,egresado=None,pk__in=Matricula.objects.filter(nivel__carrera__carrera=True,nivel__carrera__activo=True,nivel__cerrado=False).values('inscripcion')).exclude(pk=CONSUMIDOR_FINAL).order_by('carrera__nombre')
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on; align: wrap on, vert centre, horiz center')
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
                    ws.write_merge(1, 1,0,m, 'RUBROS POR VENCER DE MATRICULADOS ACTIVOS',titulo2)
                    ws.write(3, 0,'Desde:   ' +str(inicio.date()), subtitulo)
                    ws.write(4, 0,'Hasta:   ' +str(fin.date()), subtitulo)

                    filacarr = 7
                    comcarr = 7
                    fila = 8
                    com = 8
                    detalle = 3
                    columna=4
                    columna2=0
                    c=7
                    tipo_cuota=""
                    fecha=""
                    total_cuota1=0
                    total_cuota2=0
                    total_cuota3=0
                    total_cuota4=0
                    total_cuota5=0
                    total_cuota6=0
                    telefono1=''
                    telefono2=''
                    ws.write(6,4,"NIVEL",subtitulo3)
                    ws.write(6,5,"GRUPO",subtitulo3)
                    ws.write(6,6,"INSCRIPCION",subtitulo3)
                    ws.write(6,7,"ABONO",subtitulo3)
                    ws.write(6,8,"MATRICULA",subtitulo3)
                    ws.write(6,9,"ABONO",subtitulo3)
                    ws.write(6,10,"CUOTAS",subtitulo3)
                    ws.write(6,11,"ABONO",subtitulo3)
                    ws.write(6,12,"No.CUOTAS",subtitulo3)
                    total_matricula=0
                    total_inscripcion=0
                    matri=''
                    inscrip_total=0
                    abono_inscrip_total=0
                    matri_total=0
                    abono_matri_total=0
                    cuota_total=0
                    abono_cuota_total=0
                    tot_carrera=0

                    inscrip_carrera=0
                    abono_inscrip_carrera=0
                    matri_carrera=0
                    abono_matri_carrera=0
                    cuota_carrera=0
                    abono_cuota_carrera=0

                    for carrera in carreras:
                        inscrip_total+=inscrip_carrera
                        abono_inscrip_total+=abono_inscrip_carrera
                        matri_total+=matri_carrera
                        abono_matri_total+=abono_matri_carrera
                        cuota_total+=cuota_carrera
                        abono_cuota_total+=abono_cuota_carrera
                        ws.write_merge(comcarr, filacarr,0,3,elimina_tildes(carrera.nombre), subtitulo)
                        inscrip_carrera=0
                        abono_inscrip_carrera=0
                        matri_carrera=0
                        abono_matri_carrera=0
                        cuota_carrera=0
                        abono_cuota_carrera=0

                        matriculas2 = Matricula.objects.filter(inscripcion__persona__usuario__is_active=True,fecha__gte=inicio,fecha__lte=fin,nivel__cerrado=False,nivel__carrera=carrera).exclude(inscripcion__id=CONSUMIDOR_FINAL,inscripcion__retiradomatricula__activo=False,inscripcion__retiradomatricula=None).order_by('nivel__nivelmalla','nivel__paralelo','inscripcion__persona__apellido1','inscripcion__persona__apellido2')
                        tot_carrera=matriculas2.count()
                        print(tot_carrera)
                        #matriculas2 = Matricula.objects.filter(pk=191972,inscripcion__persona__usuario__is_active=True,fecha__gte=inicio,fecha__lte=fin,nivel__cerrado=False,nivel__carrera=carrera).exclude(inscripcion__id=CONSUMIDOR_FINAL,inscripcion__retiradomatricula__activo=False,inscripcion__retiradomatricula=None).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2')
                        for matri in matriculas2:
                            cuota_estud=0
                            cant_cuota=0
                            abono_inscrip=0
                            abono_cuota=0
                            inscrip_estud=0
                            pagado_inscripcion=0
                            rbinscrip=0
                            abono_matri=0
                            total_alumno=0
                            if matri.inscripcion.persona.cedula:
                                identificacion=matri.inscripcion.persona.cedula
                            else:
                                identificacion=matri.inscripcion.persona.pasaporte

                            if matri.inscripcion.persona.telefono_conv:
                                telefono1=matri.inscripcion.persona.telefono_conv
                            else:
                                telefono1='NO TIENE'

                            if matri.inscripcion.persona.telefono:
                                telefono2=matri.inscripcion.persona.telefono
                            else:
                                telefono2='NO TIENE'

                            ws.write_merge(com, fila,0,0, str(identificacion) , subtitulo)
                            ws.write_merge(com, fila,1,3,elimina_tildes(matri.inscripcion.persona.nombre_completo_inverso()), subtitulo3)
                            ws.write(fila,columna,str(matri.nivel.nivelmalla.nombre), subtitulo3)
                            ws.write(fila,columna+1,str(matri.nivel.paralelo), subtitulo3)
                            # rubro inscripcion
                            rub_inscripcion =RubroInscripcion.objects.filter(rubro__inscripcion=matri.inscripcion,rubro__cancelado=False,rubro__fechavence__gte=fechahoy)
                            if rub_inscripcion:
                                rbinscrip=rub_inscripcion.filter()[:1].get()
                                if not rbinscrip.rubro.cancelado==True:
                                    abono_inscrip=Pago.objects.filter(rubro=cuota.rubro).aggregate(Sum('valor'))['valor__sum']
                                    if abono_inscrip==None:
                                        abono_inscrip=0
                                    abono_inscrip_carrera+=abono_inscrip
                                    if rbinscrip.rubro.adeudado() >0:
                                        inscrip_estud=rbinscrip.rubro.valor
                                inscrip_carrera+=inscrip_estud
                                ws.write(fila,columna+2,inscrip_estud,subtitulo3)
                            else:
                                ws.write(fila,columna+2,"PAGADO", subtitulo3)
                            ws.write(fila,columna+3,abono_inscrip,subtitulo3)

                            rubro_matricula=RubroMatricula.objects.filter(matricula=matri,rubro__cancelado=False,rubro__fechavence__gte=fechahoy)
                            if rubro_matricula:
                                rbmatri=rubro_matricula.filter()[:1].get()
                                if not rbmatri.rubro.cancelado==True:
                                    abono_matri=Pago.objects.filter(rubro=rbmatri.rubro).aggregate(Sum('valor'))['valor__sum']
                                    if abono_matri==None:
                                        abono_matri=0
                                    abono_matri_carrera+=abono_matri
                                    if rbmatri.rubro.adeudado() >0:
                                        matri_estud=rbmatri.rubro.valor
                                matri_carrera+=matri_estud
                                ws.write(fila,columna+4,matri_estud,subtitulo3)
                            else:
                                ws.write(fila,columna+4,"PAGADO", subtitulo3)
                            ws.write(fila,columna+5,abono_matri,subtitulo3)

                            # para rubros tipo cuota
                            if RubroCuota.objects.filter(matricula=matri,rubro__fechavence__gte=fechahoy,rubro__cancelado=False).exists():
                                rb_cuotas=RubroCuota.objects.filter(matricula=matri,rubro__fechavence__gte=fechahoy,rubro__cancelado=False)
                                for cuota in rb_cuotas:
                                    if not cuota.rubro.cancelado==True:
                                        abono_cuota=Pago.objects.filter(rubro=cuota.rubro).aggregate(Sum('valor'))['valor__sum']
                                        if abono_cuota==None:
                                            abono_cuota=0
                                        abono_cuota_carrera+=abono_cuota

                                    if cuota.rubro.adeudado() >0:
                                        cant_cuota=cant_cuota+1
                                        cuota_estud=cuota_estud+cuota.rubro.valor
                                cuota_carrera+=cuota_estud
                                ws.write(fila,columna+6,cuota_estud,subtitulo3)
                            else:
                                ws.write(fila,columna+6,"PAGADO", subtitulo3)
                            ws.write(fila,columna+7,abono_cuota,subtitulo3)
                            ws.write(fila,columna+8,cant_cuota,subtitulo3)

                            fila= fila+1
                            com=fila
                        #if tot_carrera>0:
                        #    ws.write_merge(com, fila,0,3,elimina_tildes(carrera.nombre), subtitulo)
                        #if inscrip_carrera>0:
                        #    ws.write(fila,columna+2,inscrip_carrera,subtitulo)
                        #if abono_inscrip_carrera>0:
                        #    ws.write(fila,columna+3,abono_inscrip_carrera,subtitulo)
                        #if matri_carrera>0:
                        #    ws.write(fila,columna+4,matri_carrera,subtitulo)
                        #if abono_matri_carrera>0:
                        #    ws.write(fila,columna+5,abono_matri_carrera,subtitulo)
                        #if cuota_carrera>0:
                        #    ws.write(fila,columna+6,cuota_carrera,subtitulo)
                        #if abono_cuota_carrera>0:
                        #    ws.write(fila,columna+7,abono_cuota_carrera,subtitulo)


                        ws.write_merge(com, fila,0,3,elimina_tildes(carrera.nombre), subtitulo)
                        ws.write(fila,columna+2,inscrip_carrera,subtitulo)
                        ws.write(fila,columna+3,abono_inscrip_carrera,subtitulo)
                        ws.write(fila,columna+4,matri_carrera,subtitulo)
                        ws.write(fila,columna+5,abono_matri_carrera,subtitulo)
                        ws.write(fila,columna+6,cuota_carrera,subtitulo)
                        ws.write(fila,columna+7,abono_cuota_carrera,subtitulo)

                        fila= fila+2
                        com=fila

                        filacarr = fila
                        comcarr = com

                    columna=6
                    fila= fila+1
                    com=fila
                    ws.write_merge(com, fila,0,3, "TOTALES:" ,titulo2)
                    ws.write(fila,columna,inscrip_total,titulo2)
                    ws.write(fila,columna+1,abono_inscrip_total,titulo2)
                    ws.write(fila,columna+2,matri_total,titulo2)
                    ws.write(fila,columna+3,abono_matri_total,titulo2)
                    ws.write(fila,columna+4,cuota_total,titulo2)
                    ws.write(fila,columna+5,abono_cuota_total,titulo2)

                    detalle = detalle + fila
                    ws.write(detalle,0, "Fecha Impresion", subtitulo)
                    ws.write(detalle,1, str(datetime.now()), subtitulo)
                    detalle=detalle+2
                    ws.write(detalle,0, "Usuario", subtitulo)
                    ws.write(detalle,1, str(request.user), subtitulo)

                    nombre ='rubros_xvencer_matriculados'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")

        else:
            data = {'title': 'Rubros Por Vencer Matriculados'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform']=RangoFacturasForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
                return render(request ,"reportesexcel/rubros_xvencer_matriculados.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

