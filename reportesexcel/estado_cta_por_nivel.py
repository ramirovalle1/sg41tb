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
from settings import UTILIZA_GRUPOS_ALUMNOS, EMAIL_ACTIVE,MEDIA_ROOT, ASIG_VINCULACION, ASIG_PRATICA,JR_USEROUTPUT_FOLDER,MEDIA_URL, SITE_ROOT
from sga.commonviews import addUserData, ip_client_address
from sga.forms import RangoFacturasForm,RangoNCForm, VinculacionExcelForm, GestionExcelForm
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
                    nivel = Nivel.objects.filter(pk=request.POST['nivel'])[:1].get()
                    # nivel = Nivel.objects.filter(pk=7270)[:1].get()
                    nivelesmalla =  NivelMalla.objects.filter(pk__in=AsignaturaMalla.objects.filter(malla=nivel.malla.id).distinct('nivelmalla').values('nivelmalla')).order_by('orden')
                    m = 14
                    total=nivel.matriculados().count()
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
                    ws.write_merge(1, 1,0,m, 'ESTADO DE CUENTA POR NIVEL',titulo2)
                    ws.write(3, 0,'CARRERA: ' +elimina_tildes(nivel.carrera.nombre) , subtitulo)
                    ws.write(4, 0,'GRUPO:   ' +elimina_tildes(nivel.grupo.nombre), subtitulo)
                    ws.write(5, 0,'NIVEL:   ' +elimina_tildes(nivel.nivelmalla.nombre), subtitulo)

                    fila = 7
                    com = 7
                    detalle = 3
                    columna=4
                    columna2=0
                    pago_nivel=PagoNivel.objects.filter(nivel=nivel).order_by('fecha')
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
                    ws.write(6,4,"TELF. CONV",subtitulo3)
                    ws.write(6,5,"CELULAR",subtitulo3)
                    ws.write(6,6,"INSCRIPCION",subtitulo3)
                    for pn in pago_nivel:
                        if pn.tipo==0:
                            tipo_cuota='MATRICULA'
                            fecha=pn.fecha
                        else:
                            tipo_cuota='CUOTA'+" " +str(pn.tipo)
                            fecha=pn.fecha
                        ws.write(6,c,elimina_tildes(tipo_cuota) + " " + str(pn.fecha),subtitulo3)
                        c= c +1
                    total_matricula=0
                    total_inscripcion=0
                    for matri in nivel.matriculados():
                    # for matri in Matricula.objects.filter(id=248118):
                        #print(matri)
                        pagado_inscripcion=0
                        total_alumno=0
                        if matri.inscripcion.persona.cedula:
                            identificacion=matri.inscripcion.persona.cedula
                        else:
                            identificacion=matri.inscripcion.persona.pasaporte

                        if matri.inscripcion.persona.telefono_conv:
                            telefono1=elimina_tildes(matri.inscripcion.persona.telefono_conv)
                        else:
                            telefono1='NO TIENE'
                        try:
                            if matri.inscripcion.persona.telefono:
                                telefono2=elimina_tildes(matri.inscripcion.persona.telefono)
                            else:
                                telefono2='NO TIENE'
                        except:
                            pass

                        ws.write_merge(com, fila,0,0, str(identificacion) , subtitulo)
                        ws.write_merge(com, fila,1,3, elimina_tildes(matri.inscripcion.persona.nombre_completo_inverso()), subtitulo)
                        ws.write(fila,columna,elimina_tildes(telefono1), subtitulo3)
                        ws.write(fila,columna+1,elimina_tildes(telefono2), subtitulo3)
                        # rubro inscripcion
                        if RubroInscripcion.objects.filter(rubro__inscripcion=matri.inscripcion).exists():
                            rb=RubroInscripcion.objects.filter(rubro__inscripcion=matri.inscripcion)[:1].get()
                            if rb.rubro.cancelado==True:
                                estado="P"
                            else:
                                pagado_inscripcion=Pago.objects.filter(rubro=rb.rubro).aggregate(Sum('valor'))['valor__sum']
                                if pagado_inscripcion==None:
                                    pagado_inscripcion=0
                                estado=rb.rubro.valor - pagado_inscripcion
                                total_inscripcion=total_inscripcion+estado
                                total_alumno=total_alumno+estado
                            ws.write(fila,columna+2,estado,subtitulo3)
                        else:
                            ws.write(fila,columna+2,"SIN RUBRO", subtitulo3)

                        columna2 = columna+2
                        estado=0
                        for pn in pago_nivel:
                            estado=0
                            # para rubros tipo matricula
                            columna2=columna2+1
                            if RubroMatricula.objects.filter(matricula=matri,rubro__fechavence=pn.fecha).exists():
                                rb=RubroMatricula.objects.filter(matricula=matri,rubro__fechavence=pn.fecha)[:1].get()
                                if rb.rubro.cancelado==True and rb.rubro.fechavence==pn.fecha:
                                    estado="P"
                                else:
                                    pagado_matri=Pago.objects.filter(rubro=rb.rubro).aggregate(Sum('valor'))['valor__sum']
                                    if pagado_matri==None:
                                        pagado_matri=0
                                    estado=rb.rubro.valor - pagado_matri
                                    total_matricula=total_matricula+estado
                                    total_alumno=total_alumno+estado
                                ws.write(fila,columna2,estado,subtitulo3)
                            else:
                                estado=0
                                ws.write(fila,columna2,estado,subtitulo3)
                            # para rubros tipo cuota
                            if RubroCuota.objects.filter(matricula=matri,rubro__fechavence=pn.fecha,cuota=pn.tipo).exists():
                                rc=RubroCuota.objects.filter(matricula=matri,rubro__fechavence=pn.fecha)[:1].get()
                                if rc.rubro.cancelado==True and rc.rubro.fechavence==pn.fecha:
                                    estado="P"
                                else:
                                    pagado_cuota=Pago.objects.filter(rubro=rc.rubro).aggregate(Sum('valor'))['valor__sum']
                                    if pagado_cuota==None:
                                        pagado_cuota=0
                                    estado=rc.rubro.valor - pagado_cuota
                                    if pn.tipo==1:
                                        total_cuota1=total_cuota1+estado
                                        total_alumno=total_alumno+estado
                                    if pn.tipo==2:
                                        total_cuota2=total_cuota2+estado
                                        total_alumno=total_alumno+estado
                                    if pn.tipo==3:
                                        total_cuota3=total_cuota3+estado
                                        total_alumno=total_alumno+estado
                                    if pn.tipo==4:
                                        total_cuota4=total_cuota4+estado
                                        total_alumno=total_alumno+estado
                                    if pn.tipo==5:
                                        total_cuota5=total_cuota5+estado
                                        total_alumno=total_alumno+estado
                                    if pn.tipo==6:
                                        total_cuota6=total_cuota6+estado
                                        total_alumno=total_alumno+estado
                                ws.write(fila,columna2,estado,subtitulo3)
                        ws.write(fila,columna2+1,total_alumno,titulo)
                        fila= fila+1
                        com=fila

                    columna=6
                    ws.write_merge(com, fila,0,3, "TOTALES:" ,titulo2)
                    ws.write(fila,columna,total_inscripcion,titulo2)
                    ws.write(fila,columna+1,total_matricula,titulo2)
                    ws.write(fila,columna+2,total_cuota1,titulo2)
                    ws.write(fila,columna+3,total_cuota2,titulo2)
                    ws.write(fila,columna+4,total_cuota3,titulo2)
                    if total_cuota4>0:
                        ws.write(fila,columna+5,total_cuota4,titulo2)
                    if total_cuota5>0:
                        ws.write(fila,columna+6,total_cuota5,titulo2)
                    if total_cuota6>0:
                        ws.write(fila,columna+7,total_cuota6,titulo2)

                    detalle = detalle + fila
                    ws.write(detalle,0, "Fecha Impresion", subtitulo)
                    ws.write(detalle,1, str(datetime.now()), subtitulo)
                    detalle=detalle+2
                    ws.write(detalle,0, "Usuario", subtitulo)
                    ws.write(detalle,1, str(request.user), subtitulo)

                    nombre ='est_cta_x_nivel'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")

            elif action  =='generarpdf':
                try:
                    pdf = FPDF()
                    pdf.add_page('Landscape')
                    pdf.set_font('Arial', 'B', 6)  # Arial bold 8
                    pdf.alias_nb_pages(alias='pag_total')

                    pdf.image(SITE_ROOT+'/media/reportes/encabezados_pies/logo.png', 5, 5, 20,20)  # Logo

                    nivel = Nivel.objects.filter(pk=request.POST['nivel'])[:1].get()
                    nivelesmalla =  NivelMalla.objects.filter(pk__in=AsignaturaMalla.objects.filter(malla=nivel.malla.id).distinct('nivelmalla').values('nivelmalla')).order_by('orden')
                    m = 10
                    total=nivel.matriculados().count()

                    pdf.text(120,30,"ESTADO DE CUENTA POR NIVEL")
                    pdf.text(1,35,"CARRERA: "  + str(elimina_tildes(nivel.carrera.nombre)))
                    pdf.text(1,40,"GRUPO: "  + str(elimina_tildes(nivel.grupo.nombre)))
                    pdf.text(1,45,"NIVEL: "  + str(elimina_tildes(nivel.nivelmalla.nombre)))
                    fechahoy=datetime.now()
                    fechahoy = fechahoy.strftime('%d/%m/%Y %H:%M:%S%p') # formato dd/mm/yyyy hh:mm:ss am o fm
                    pdf.text(1,50,"Fecha de Impresion: "+ str(fechahoy))
                    pdf.ln(50)  # Salto de linea

                    # para pruebas en desarrollo OCU
                    # locale.setlocale( locale.LC_ALL, '' )

                    # para produccion
                    locale.setlocale( locale.LC_ALL, 'en_US.UTF-8' )

                    # cabecera de la tabla
                    cabecera = ["IDENTIFICACION","NOMBRES","TELF. CONV.","CELULAR"]
                    pnc=[]
                    d=0
                    fecha=""
                    total_matricula=0
                    total_cuota1=0
                    total_cuota2=0
                    total_cuota3=0
                    total_cuota4=0
                    total_cuota5=0
                    total_cuota6=0
                    telefono1=''
                    telefono2=''

                    w = [25,50,30,30]
                    c = [25,25,25,25,25,25]
                    for i in range(0, len(cabecera)):
                        pdf.cell(w[i], 5, cabecera[i], 1, 0, 'C', 0)
                    pago_nivel=PagoNivel.objects.filter(nivel=nivel).order_by('fecha')

                    for pn in pago_nivel:
                        pnc.append(pn.tipo)

                    for pg in pago_nivel:
                        if pg.tipo==0:
                            tipo_cuota='MATRIC'
                            fecha=pg.fecha
                            tipo_cuota=tipo_cuota+" "+str(fecha)+" "
                        else:
                            tipo_cuota='CUOTA'+" " +str(pg.tipo)+" "
                            fecha=pg.fecha
                            tipo_cuota=tipo_cuota+" "+str(fecha)
                        pdf.cell(c[d], 5, tipo_cuota, 1, 0, 'C', 0)
                        d=d+1
                    pdf.ln()

                    for matri in nivel.matriculados():
                        total_alumno=0
                        if matri.inscripcion.persona.cedula:
                            identificacion=matri.inscripcion.persona.cedula
                        else:
                            identificacion=matri.inscripcion.persona.pasaporte

                        if matri.inscripcion.persona.telefono_conv:
                            telefono1=matri.inscripcion.persona.telefono_conv

                        if matri.inscripcion.persona.telefono:
                            telefono2=matri.inscripcion.persona.telefono

                        pdf.cell(25, 5, str(identificacion), 'LR',0,'C')
                        pdf.cell(50, 5, str(elimina_tildes(matri.inscripcion.persona.nombre_completo_inverso())), 'LR',0,'C')
                        pdf.cell(30, 5, str(telefono1), 'LR',0,'C')
                        pdf.cell(30, 5, str(telefono2), 'LR',0,'C')

                        for pn in pago_nivel:
                            # para rubros tipo matricula
                            estado=''
                            if RubroMatricula.objects.filter(matricula=matri,rubro__fechavence=pn.fecha).exists():
                                rb=RubroMatricula.objects.filter(matricula=matri,rubro__fechavence=pn.fecha)[:1].get()
                                if rb.rubro.cancelado==True and rb.rubro.fechavence==pn.fecha:
                                    estado="P"
                                else:
                                    pagado_matri=Pago.objects.filter(rubro=rb.rubro).aggregate(Sum('valor'))['valor__sum']
                                    if pagado_matri==None:
                                        pagado_matri=0
                                    estado=rb.rubro.valor - pagado_matri
                                    total_matricula=total_matricula+estado
                                    total_alumno=total_alumno+estado
                                pdf.cell(25, 5, str(estado), 'LR',0,'C')

                            # para rubros tipo cuota
                            if RubroCuota.objects.filter(matricula=matri,rubro__fechavence=pn.fecha,cuota=pn.tipo).exists():
                                rc=RubroCuota.objects.filter(matricula=matri,rubro__fechavence=pn.fecha)[:1].get()
                                if rc.rubro.cancelado==True and rc.rubro.fechavence==pn.fecha:
                                    estado="P"
                                else:
                                    pagado_cuota=Pago.objects.filter(rubro=rc.rubro).aggregate(Sum('valor'))['valor__sum']
                                    if pagado_cuota==None:
                                        pagado_cuota=0
                                    estado=rc.rubro.valor - pagado_cuota
                                    if pn.tipo==1:
                                        total_cuota1=total_cuota1+estado
                                        total_alumno=total_alumno+estado
                                    if pn.tipo==2:
                                        total_cuota2=total_cuota2+estado
                                        total_alumno=total_alumno+estado
                                    if pn.tipo==3:
                                        total_cuota3=total_cuota3+estado
                                        total_alumno=total_alumno+estado
                                    if pn.tipo==4:
                                        total_cuota4=total_cuota4+estado
                                        total_alumno=total_alumno+estado
                                    if pn.tipo==5:
                                        total_cuota5=total_cuota5+estado
                                        total_alumno=total_alumno+estado
                                    if pn.tipo==6:
                                        total_cuota6=total_cuota6+estado
                                        total_alumno=total_alumno+estado

                                pdf.cell(25, 5, str(estado), 'LR',0,'C')
                        pdf.ln()
                    pdf.ln(5)
                    pdf.cell(135, 5, "TOTALES:", 'LR',0,'C')
                    pdf.cell(25, 5, str(total_matricula), 'LR',0,'C')
                    pdf.cell(25, 5, str(total_cuota1), 'LR',0,'C')
                    pdf.cell(25, 5, str(total_cuota2), 'LR',0,'C')
                    pdf.cell(25, 5, str(total_cuota3), 'LR',0,'C')
                    pdf.cell(25, 5, str(total_cuota4), 'LR',0,'C')
                    pdf.cell(25, 5, str(total_cuota5), 'LR',0,'C')

                    if total_cuota6>0:
                        pdf.cell(25, 5, str(total_cuota6), 'LR',0,'C')

                    pdf.ln(10)
                    pdf.set_font('Arial','B',12)  # Arial bold 12
                    pdf.set_font('')  # restauro la fuente

                    d = datetime.now()
                    pdfname = 'estado_cta_por_nivel' + '_' + d.strftime('%Y%m%d_%H%M%S') + '.pdf'
                    output_folder = os.path.join(JR_USEROUTPUT_FOLDER, elimina_tildes(request.user.username))
                    try:
                        os.makedirs(output_folder)
                    except Exception as ex:
                        pass
                    pdf.output(os.path.join(output_folder, pdfname))
                    return HttpResponse(json.dumps({'result': 'ok','reportfile': '/'.join([MEDIA_URL,'documentos',
                                                                                           'userreports',
                                                                                           request.user.username,
                                                                                           pdfname])}),content_type="application/json")
                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":"ok"}), content_type="application/json")

        else:
            data = {'title': 'Estado de Cuenta por Nivel'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                return render(request ,"reportesexcel/estado_cta_nivel.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

