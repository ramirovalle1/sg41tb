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
from settings import UTILIZA_GRUPOS_ALUMNOS, EMAIL_ACTIVE,MEDIA_ROOT, ASIG_VINCULACION, ASIG_PRATICA,JR_USEROUTPUT_FOLDER,MEDIA_URL, SITE_ROOT,NIVEL_SEMINARIO,NIVEL_GRADUACION
from sga.commonviews import addUserData, ip_client_address
from sga.forms import RangoFacturasForm,RangoNCForm, VinculacionExcelForm, GestionExcelForm
from sga.models import Inscripcion,convertir_fecha,Factura,ClienteFactura,TituloInstitucion,ReporteExcel,NotaCreditoInstitucion, Persona,TipoNotaCredito, Carrera, \
    Matricula, RecordAcademico, Egresado, Malla, AsignaturaMalla, NivelMalla, MateriaAsignada, Asignatura, Nivel, Periodo, ProfesorMateria, PagoNivel, Rubro, \
    RubroMatricula, Pago, RubroCuota, RubroInscripcion, Descuento, DetalleDescuento
from fpdf import FPDF

from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action  =='generarexcel':
                try:
                    # nivel = Nivel.objects.filter(pk=request.POST['nivel'])[:1].get()
                    inicio = request.POST['inicio']
                    fin = request.POST['fin']
                    fechai = convertir_fecha(inicio)
                    fechaf = convertir_fecha(fin)
                    m = 14
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
                    ws.write_merge(1, 1,0,m, 'PAGOS POR NIVEL SEMINARIO Y DESCUENTOS',titulo2)
                    ws.write(3, 0,'Desde:   ' +str(fechai.date()), subtitulo)
                    ws.write(4, 0,'Hasta:   ' +str(fechaf.date()), subtitulo)
                    fila = 7
                    com = 7
                    detalle = 3
                    columna=0
                    # columna2=0
                    # pago_nivel=PagoNivel.objects.filter(nivel=nivel).order_by('fecha')
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
                    ws.write(6,0,"IDENTIFICACION",subtitulo3)
                    ws.write(6,1,"ESTUDIANTE",subtitulo3)
                    ws.write(6,2,"TELF. CONV",subtitulo3)
                    ws.write(6,3,"CELULAR",subtitulo3)
                    ws.write(6,4,"RUBRO",subtitulo3)
                    ws.write(6,5,"VALOR PAGADO",subtitulo3)
                    ws.write(6,6,"SALDO",subtitulo3)
                    ws.write(6,7,"F. VENCE",subtitulo3)
                    ws.write(6,8,"F. PAGO",subtitulo3)
                    ws.write(6,9,"VALOR RUBRO",subtitulo3)
                    ws.write(6,10,"VALOR DESCUENTO",subtitulo3)
                    ws.write(6,11,"% DESCUENTO",subtitulo3)
                    ws.write(6,12,"codigo",subtitulo3)
                    total_matricula=0
                    total_inscripcion=0
                    # for matri in nivel.matriculados():
                    # for matri in Matricula.objects.filter(inscripcion__id=52519,fecha__gte=fechai,fecha__lte=fechaf,nivel__nivelmalla__id__in=[NIVEL_SEMINARIO,NIVEL_GRADUACION]).order_by('nivel__grupo__nombre','inscripcion__persona__apellido1', 'inscripcion__persona__apellido2', 'inscripcion__persona__nombres'):
                    for matri in Matricula.objects.filter(fecha__gte=fechai,fecha__lte=fechaf,nivel__nivelmalla__id__in=[NIVEL_SEMINARIO,NIVEL_GRADUACION]).order_by('nivel__grupo__nombre','inscripcion__persona__apellido1', 'inscripcion__persona__apellido2', 'inscripcion__persona__nombres'):
                        # print(matri)
                        pagado_inscripcion=0
                        totalpagadoalumno=0
                        totaldeudaalumno=0
                        if matri.inscripcion.persona.cedula:
                            identificacion=matri.inscripcion.persona.cedula
                        else:
                            identificacion=matri.inscripcion.persona.pasaporte

                        if matri.inscripcion.persona.telefono_conv:
                            telefono1=elimina_tildes(matri.inscripcion.persona.telefono_conv)
                        else:
                            telefono1='NO TIENE'

                        if matri.inscripcion.persona.telefono:
                            telefono2=elimina_tildes(matri.inscripcion.persona.telefono)
                        else:
                            telefono2='NO TIENE'

                        if matri.nivel:
                            nivel=elimina_tildes(matri.nivel.nivelmalla.nombre)
                            grupo=elimina_tildes(matri.nivel.grupo.nombre)
                        else:
                            nivel='NO TIENE'
                            grupo='NO TIENE'

                        rbfechaabono=''
                        fecha_vence=''
                        # columna2 = columna+2
                        estado=0
                        pagado_matri=0
                        fecha_vence=''
                        rbfechaabono=''
                        valorrubro=0
                        saldo=0
                        valordescuento=0
                        porcentajedescuento=0
                        codigo=0
                        if RubroMatricula.objects.filter(matricula=matri).exists():
                            rb=RubroMatricula.objects.filter(matricula=matri)[:1].get()
                            fecha_vence=rb.rubro.fechavence
                            if Pago.objects.filter(rubro=rb.rubro).order_by('-fecha').exists():
                                pagado_matri=Pago.objects.filter(rubro=rb.rubro).aggregate(Sum('valor'))['valor__sum']
                                fechaabono=Pago.objects.filter(rubro=rb.rubro).order_by('-fecha')[:1].get()
                                rbfechaabono=fechaabono.fecha
                                if pagado_matri==None:
                                    pagado_matri=0
                                estado=rb.rubro.valor - pagado_matri
                                # total_matricula=total_matricula+estado
                                # total_alumno=total_alumno+estado
                            if DetalleDescuento.objects.filter(rubro=rb.rubro).exists():
                                descuento=DetalleDescuento.objects.get(rubro=rb.rubro)
                                valorrubro=rb.rubro.valor+descuento.valor
                                valordescuento=descuento.valor
                                porcentajedescuento=descuento.porcentaje
                            else:
                                valorrubro=rb.rubro.valor
                                valordescuento=0
                                porcentajedescuento=0
                            if rb.rubro.cancelado:
                                saldo=0
                            else:
                                saldo=rb.rubro.valor-pagado_matri
                            totalpagadoalumno=totalpagadoalumno+pagado_matri
                            totaldeudaalumno=totaldeudaalumno+saldo
                            codigo=rb.rubro.id
                            ws.write(fila,columna,str(identificacion) , subtitulo)
                            ws.write(fila,columna+1,matri.inscripcion.persona.nombre_completo_inverso(), subtitulo)
                            ws.write(fila,columna+2,str(telefono1), subtitulo3)
                            ws.write(fila,columna+3,str(telefono2), subtitulo3)
                            ws.write(fila,columna+4,elimina_tildes(rb.rubro.nombre()),subtitulo3)
                            ws.write(fila,columna+5,pagado_matri,subtitulo3)
                            ws.write(fila,columna+6,saldo,subtitulo3)
                            ws.write(fila,columna+7,str(fecha_vence),subtitulo3)
                            ws.write(fila,columna+8,str(rbfechaabono),subtitulo3)
                            ws.write(fila,columna+9,valorrubro,subtitulo3)
                            ws.write(fila,columna+10,valordescuento,subtitulo3)
                            ws.write(fila,columna+11,porcentajedescuento,subtitulo3)
                            ws.write(fila,columna+12,codigo,subtitulo3)
                        # else:
                        #     estado=0
                        fecha_vence=''
                        rbfechaabono=''
                        if RubroCuota.objects.filter(matricula=matri).exists():
                            for rc in RubroCuota.objects.filter(matricula=matri).order_by('rubro__fechavence'):
                                fila=fila+1
                                saldo=0
                                pagado_cuota=0
                                valorrubro=0
                                valordescuento=0
                                porcentajedescuento=0
                                fecha_vence=rc.rubro.fechavence
                                if Pago.objects.filter(rubro=rc.rubro).order_by('-fecha').exists():
                                    pagado_cuota=Pago.objects.filter(rubro=rc.rubro).aggregate(Sum('valor'))['valor__sum']
                                    fechaabono=Pago.objects.filter(rubro=rc.rubro).order_by('-fecha')[:1].get()
                                    rbfechaabono=fechaabono.fecha
                                else:
                                    pagado_cuota=0
                                if DetalleDescuento.objects.filter(rubro=rc.rubro).exists():
                                    descuento=DetalleDescuento.objects.get(rubro=rc.rubro)
                                    valorrubro=rc.rubro.valor+descuento.valor
                                    valordescuento=descuento.valor
                                    porcentajedescuento=descuento.porcentaje
                                else:
                                    valorrubro=rc.rubro.valor
                                    valordescuento=0
                                    porcentajedescuento=0
                                if rc.rubro.cancelado:
                                    saldo=0
                                else:
                                    saldo=rc.rubro.valor-pagado_cuota
                                totalpagadoalumno=totalpagadoalumno+pagado_cuota
                                totaldeudaalumno=totaldeudaalumno+saldo
                                codigo=rc.rubro.id
                                ws.write(fila,columna, str(identificacion) , subtitulo)
                                ws.write(fila,columna+1,matri.inscripcion.persona.nombre_completo_inverso(), subtitulo)
                                ws.write(fila,columna+2,str(telefono1), subtitulo3)
                                ws.write(fila,columna+3,str(telefono2), subtitulo3)
                                ws.write(fila,columna+4,elimina_tildes(rc.rubro.nombre()),subtitulo3)
                                ws.write(fila,columna+5,pagado_cuota,subtitulo3)
                                ws.write(fila,columna+6,saldo,subtitulo3)
                                ws.write(fila,columna+7,str(fecha_vence),subtitulo3)
                                ws.write(fila,columna+8,str(rbfechaabono),subtitulo3)
                                ws.write(fila,columna+9,valorrubro,subtitulo3)
                                ws.write(fila,columna+10,valordescuento,subtitulo3)
                                ws.write(fila,columna+11,porcentajedescuento,subtitulo3)
                                ws.write(fila,columna+12,codigo,subtitulo3)
                        # fila= fila+1
                        # ws.write(fila,columna+1,'TOTAL POR ALUMNO',titulo)
                        # ws.write(fila,columna+5,totalpagadoalumno,titulo)
                        # ws.write(fila,columna+6,totaldeudaalumno,titulo)
                        fila= fila+1
                        com=fila

                    columna=6
                    # ws.write_merge(com, fila,0,3, "TOTALES:" ,titulo2)
                    # ws.write(fila,columna,total_inscripcion,titulo2)
                    # ws.write(fila,columna+1,total_matricula,titulo2)
                    # ws.write(fila,columna+2,total_cuota1,titulo2)
                    # ws.write(fila,columna+3,total_cuota2,titulo2)
                    # ws.write(fila,columna+4,total_cuota3,titulo2)
                    # if total_cuota4>0:
                    #     ws.write(fila,columna+5,total_cuota4,titulo2)
                    # if total_cuota5>0:
                    #     ws.write(fila,columna+6,total_cuota5,titulo2)
                    # if total_cuota6>0:
                    #     ws.write(fila,columna+7,total_cuota6,titulo2)

                    detalle = detalle + fila
                    ws.write(detalle,0, "Fecha Impresion", subtitulo)
                    ws.write(detalle,1, str(datetime.now()), subtitulo)
                    detalle=detalle+2
                    ws.write(detalle,0, "Usuario", subtitulo)
                    ws.write(detalle,1, str(request.user), subtitulo)

                    nombre ='pagos_nivelseminario_descuento'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")

        else:
            data = {'title': 'Pagos por Nivel Seminario y Descuentos Aplicados'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform']=RangoFacturasForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
                return render(request ,"reportesexcel/xls_pagos_nivel_descuento.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

