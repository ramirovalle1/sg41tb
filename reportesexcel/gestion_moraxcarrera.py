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
from settings import UTILIZA_GRUPOS_ALUMNOS, EMAIL_ACTIVE,MEDIA_ROOT, ASIG_VINCULACION, ASIG_PRATICA,JR_USEROUTPUT_FOLDER,MEDIA_URL, SITE_ROOT, TIPO_CONGRESO_RUBRO
from sga.commonviews import addUserData, ip_client_address
from sga.forms import RangoFacturasForm,RangoNCForm, VinculacionExcelForm, GestionExcelForm, MatriculadosporCarreraExcelForm
from sga.models import Inscripcion,convertir_fecha,Factura,ClienteFactura,TituloInstitucion,ReporteExcel,NotaCreditoInstitucion, Persona,TipoNotaCredito, Carrera, Matricula, RecordAcademico, Egresado, Malla, AsignaturaMalla, NivelMalla, MateriaAsignada, Asignatura, Nivel, Periodo, ProfesorMateria, PagoNivel, Rubro, RubroMatricula, Pago, RubroCuota, Coordinacion, RubroInscripcion, RubroOtro, InscripcionGrupo
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
                    # nivelactual = Nivel.objects.filter(pk=request.POST['nivel'])
                    carrera = Carrera.objects.filter(pk=request.POST['carrera'],carrera=True)[:1].get()
                    m = 10
                    # total=nivel.matriculados().count()
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo3 = xlwt.easyxf('font: name Times New Roman; align: wrap on, vert centre, horiz center')
                    subtitulo.font.height = 20*10
                    wb = xlwt.Workbook()
                    num_hoja=1
                    hoja='Registros'+str(num_hoja)
                    # ws = wb.add_sheet('Registros',cell_overwrite_ok=True)
                    ws = wb.add_sheet(hoja,cell_overwrite_ok=True)

                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,m, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,m, 'GESTION DE MORA POR CARRERA',titulo2)
                    ws.write(3, 0,'CARRERA: ' +carrera.nombre , subtitulo)
                    # ws.write(4, 0,'GRUPO:   ' +nivel.grupo.nombre, subtitulo)
                    # ws.write(5, 0,'NIVEL:   ' +nivel.nivelmalla.nombre, subtitulo)

                    fila = 7
                    com = 7
                    detalle = 3
                    columna=0
                    # pago_nivel=PagoNivel.objects.filter(nivel=nivel).order_by('fecha')
                    c=5
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
                    ws.write(6,0,"UNIDAD ACADEMICA",subtitulo3)
                    # ws.write(6,1,"PERIODO",subtitulo3)
                    # ws.write(6,2,"CARRERA",subtitulo3)
                    # ws.write_merge(6,6,3,6,"ESTUDIANTE",subtitulo3)
                    ws.write(6,1,"ESTUDIANTE",subtitulo3)
                    # ws.write(6,4,"NIVEL",subtitulo3)
                    ws.write(6,2,"GRUPO",subtitulo3)
                    ws.write(6,3,"TIPO DE RUBRO",subtitulo3)
                    ws.write(6,4,"VALOR",subtitulo3)
                    ws.write(6,5,"ABONO",subtitulo3)
                    ws.write(6,6,"SALDO",subtitulo3)
                    ws.write(6,7,"F. VENCIMIENTO",subtitulo3)
                    ws.write(6,8,"F. PAGO",subtitulo3)
                    ws.write(6,9,"F. ABONO",subtitulo3)
                    ws.write(6,10,"DIAS VENCIDOS",subtitulo3)
                    ws.write(6,11,"CALIFICACION",subtitulo3)
                    ws.write(6,12,"TEL.CELULAR",subtitulo3)
                    ws.write(6,13,"TEL.CONVENCIONAL",subtitulo3)
                    ws.write(6,14,"TIPO BECA",subtitulo3)
                    ws.write(6,15,"% BECA",subtitulo3)

                    #este es el filtro general
                    inscritos= Inscripcion.objects.filter(persona__usuario__is_active=True,carrera=carrera).order_by('persona__apellido1','persona__apellido2','persona__nombres')
                    # prueba con 1 estudiante
                    # inscritos= Inscripcion.objects.filter(pk=23628,persona__usuario__is_active=True,carrera=carrera).order_by('persona__apellido1','persona__apellido2','persona__nombres')
                    for inscrip in inscritos:
                        for rubro in  Rubro.objects.filter(inscripcion=inscrip).order_by('fechavence'):
                            print(fila)
                            if fila==65500:
                                num_hoja=num_hoja+1
                                hoja='Registros'+str(num_hoja)
                                ws = wb.add_sheet(hoja,cell_overwrite_ok=True)
                                fila=7
                        # for rubro in  Rubro.objects.filter(pk=852236,inscripcion=inscrip).order_by('fechavence'):
                            rbnombre=''
                            rbvalor=0
                            abono=0
                            saldo=0
                            pagototal=0
                            rbabono=0
                            rbfechavence=''
                            rbfechapago=''
                            rbfabono=''
                            diasvence=0
                            vencimiento=''
                            grupo=''
                            conbeca=''
                            telefono1=''
                            telefono2=''
                            tipobeca=''
                            porcientobeca=''
                            # print(inscrip)

                            try:
                                if inscrip.persona.telefono_conv:
                                    telefono1=inscrip.persona.telefono_conv.replace('-','').replace(' ','').replace('+','')
                                else:
                                    telefono1=''
                            except Exception as ex:
                                pass

                            try:
                                if inscrip.persona.telefono:
                                    telefono2=inscrip.persona.telefono.replace('-','').replace(' ','').replace('+','')
                                else:
                                    telefono2=''
                            except Exception as ex:
                                pass

                            #para datos de beca
                            if Matricula.objects.filter(inscripcion=inscrip,nivel__cerrado=False).exists():
                                conbeca=Matricula.objects.filter(inscripcion=inscrip,nivel__cerrado=False).order_by('-id')[:1].get()
                                if conbeca.becado:
                                    tipobeca=str(conbeca.tipobeca)
                                    porcientobeca=str(conbeca.porcientobeca)
                            ws.write(fila,columna+14,tipobeca,subtitulo3)
                            ws.write(fila,columna+15,porcientobeca,subtitulo3)

                            grupo=InscripcionGrupo.objects.get(inscripcion=inscrip)

                            try:
                                if rubro.tipo() and rubro.nombre():
                                    rbnombre= str(elimina_tildes(rubro.tipo().replace('-','').replace(' ','').replace('+','')) + " " + elimina_tildes(rubro.nombre().replace('-','').replace(' ','').replace('+','').replace(u"\u2013",' ')))
                                else:
                                    rbnombre=''
                            except Exception as ex:
                                pass

                            rbvalor=rubro.valor
                            rbfechavence=rubro.fechavence

                            if rubro.cancelado==True:
                                if Pago.objects.filter(rubro=rubro).order_by('-fecha').exists():
                                    rbfechapago=Pago.objects.filter(rubro=rubro).order_by('-fecha')[:1].get()
                                    rbfechapago=rbfechapago.fecha
                                    rbfechavence=rubro.fechavence
                                    abono=Pago.objects.filter(rubro=rubro).aggregate(Sum('valor'))['valor__sum']
                                    vencimiento = "A1"
                            else:
                                if Pago.objects.filter(rubro=rubro).order_by('-fecha').exists():
                                    abono=Pago.objects.filter(rubro=rubro).aggregate(Sum('valor'))['valor__sum']
                                    rbfechaabono=Pago.objects.filter(rubro=rubro).order_by('-fecha')[:1].get()
                                    rbfabono=rbfechaabono.fecha
                                    diasvence=(datetime.now().date()- rubro.fechavence).days
                                    if diasvence<0:
                                        diasvence=0
                                    vencimiento = rubro.diasvencimiento()
                                else:
                                    abono=0
                                    diasvence=(datetime.now().date()- rubro.fechavence).days
                                    if diasvence<0:
                                        diasvence=0
                                    vencimiento = rubro.diasvencimiento()
                            saldo=rubro.valor - abono

                            ws.write(fila,columna,str(elimina_tildes(carrera.coordinacion_pertenece())),subtitulo3)
                            # ws.write(fila,columna+1,str(nv.periodo.nombre),subtitulo3)
                            # ws.write(fila,columna+2,str(nv.carrera.alias),subtitulo3)
                            ws.write(fila,columna+1,elimina_tildes(inscrip.persona.nombre_completo_inverso()), subtitulo)
                            # ws.write(fila,columna+4,str(nv.nivelmalla.nombre),subtitulo3)
                            ws.write(fila,columna+2,str(grupo.grupo.nombre),subtitulo3)
                            ws.write(fila,columna + 12,telefono1, subtitulo3)
                            ws.write(fila,columna + 13,telefono2, subtitulo3)
                            #para datos de beca
                            ws.write(fila,columna+14,tipobeca,subtitulo3)
                            ws.write(fila,columna+15,porcientobeca,subtitulo3)

                            ws.write(fila,3,str(rbnombre))
                            ws.write(fila,4,rbvalor)
                            ws.write(fila,5,abono)
                            ws.write(fila,6,saldo)
                            ws.write(fila,7,str(rbfechavence))
                            ws.write(fila,8,str(rbfechapago))
                            ws.write(fila,9,str(rbfabono))
                            ws.write(fila,10,diasvence)
                            ws.write(fila,11,vencimiento)

                            fila = fila + 1

                    com=fila+1
                    fila = fila +1
                    columna=6

                    detalle = detalle + fila
                    ws.write(detalle,0, "Fecha Impresion", subtitulo)
                    ws.write(detalle,1, str(datetime.now()), subtitulo)
                    detalle=detalle+2
                    ws.write(detalle,0, "Usuario", subtitulo)
                    ws.write(detalle,1, str(request.user), subtitulo)

                    nombre ='gestion_moraxnivel'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    # return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")
                    return HttpResponse(json.dumps({"result":str(ex)+' '+ str(inscrip)+' '+ str(rubro.id)}),content_type="application/json")


        else:
            data = {'title': 'Gestion Mora por Carrera'}
            addUserData(request,data)
            # if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
            #     reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
            #     data['reportes'] = reportes
            data['form']=MatriculadosporCarreraExcelForm()
            return render(request ,"reportesexcel/gestion_moraxnivel.html" ,  data)
        return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

