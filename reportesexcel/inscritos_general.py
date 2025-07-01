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
from sga.forms import RangoFacturasForm,RangoNCForm, VinculacionExcelForm, GestionExcelForm,InscritosGeneralForm
from sga.models import Inscripcion,convertir_fecha,Factura,ClienteFactura,TituloInstitucion,ReporteExcel,NotaCreditoInstitucion, Persona,TipoNotaCredito, Carrera, Matricula, RecordAcademico, Egresado, Malla, AsignaturaMalla, NivelMalla, MateriaAsignada, Asignatura, Nivel, Periodo, ProfesorMateria, PagoNivel, Rubro, RubroMatricula, Pago, RubroCuota, RubroInscripcion, InscripcionVendedor
from fpdf import FPDF
from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action =='generarexcel':
                try:
                    desde = request.POST['desde']
                    hasta = request.POST['hasta']
                    fechai = convertir_fecha(desde)
                    fechaf = convertir_fecha(hasta)
                    nivelmalla= NivelMalla.objects.filter(pk=request.POST['nivelmalla'])[:1].get()

                    # OC 11-junio-2018 para usuario gvlopez presentar solamente informacion de canal 3
                    usuario=request.user
                    if not usuario.username=='gvlopez':
                        matriculados = Matricula.objects.filter(inscripcion__persona__usuario__is_active=True,nivel__nivelmalla=nivelmalla,inscripcion__fecha__gte=fechai,inscripcion__fecha__lte=fechaf,liberada=False).order_by('inscripcion__user','inscripcion__persona__apellido1','inscripcion__persona__apellido2')
                        # matriculados = Matricula.objects.filter(inscripcion__persona__usuario__is_active=True,inscripcion__persona__cedula='0958231227',nivel__nivelmalla=nivelmalla,inscripcion__fecha__gte=fechai,inscripcion__fecha__lte=fechaf,liberada=False).order_by('inscripcion__user','inscripcion__persona__apellido1','inscripcion__persona__apellido2')
                    else:
                        matriculados = Matricula.objects.filter(inscripcion__persona__usuario__is_active=True,nivel__nivelmalla=nivelmalla,inscripcion__fecha__gte=fechai,inscripcion__fecha__lte=fechaf,inscripcion__promocion__id__in=(5,6)).order_by('inscripcion__user','inscripcion__persona__apellido1','inscripcion__persona__apellido2')

                    total=matriculados.count()
                    m = 16
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on;align: wrap on, vert centre, horiz center')
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
                    ws.write_merge(1, 1,0,m, 'Valores de Estudiantes Matriculados por Rango de Fechas',titulo2)
                    ws.write(4, 0,'Desde:   ' +str(fechai.date()), subtitulo)
                    ws.write(5, 0,'Hasta:   ' +str(fechaf.date()), subtitulo)
                    ws.write(6, 0,'Nivel Malla:   ' +nivelmalla.nombre, subtitulo)
                    fila = 9
                    com = 9
                    detalle = 3
                    columna=8
                    c=9
                    pagado_inscripcion=0
                    pagado_matri=0
                    telefono1=''
                    pagado_cuota=0
                    telefono2=''
                    cab = 12
                    inscritopor=''
                    inscrito=''
                    promocion=''
                    vendedor=''

                    cabcuotas = RubroCuota.objects.filter(matricula__in=matriculados).order_by('cuota').distinct('cuota').values('cuota')
                    ws.write(8,0,"CEDULA",titulo)
                    ws.write_merge(8,8,1,3,"NOMBRES",titulo)
                    ws.write_merge(8,8,4,7,"CARRERA",titulo)
                    ws.write(8,8,"INSCRIPCION",titulo)
                    ws.write(8,9,"Vence Inscripcion",titulo)
                    ws.write(8,10,"MATRICULA",titulo)
                    ws.write(8,11,"Vence Matricula",titulo)
                    for rc in cabcuotas:

                        ws.write(8,cab,"CUOTA "+str(rc['cuota']),titulo)
                        ws.write(8,cab+1,"Vencimiento CUOTA "+str(rc['cuota']),titulo)
                        cab = cab +2

                    ws.write(8,cab,"INICIO NIVEL",titulo)
                    ws.write(8,cab+1,"CONVENCIONAL",titulo)
                    ws.write(8,cab+2,"CELULAR",titulo)
                    ws.write_merge(8,8,cab+3,cab+5,"INSCRITO POR",titulo)
                    ws.write_merge(8,8,cab+6,cab+6,"PROMOCION",titulo)
                    ws.write_merge(8,8,cab+7,cab+7,"VENDEDOR",titulo)
                    total_matricula=0
                    total_inscripcion=0
                    total_cuota=0

                    for matri in matriculados:
                        # print(matri)
                        pagado_inscripcion=0
                        pagado_matri=0
                        if RubroInscripcion.objects.filter(rubro__inscripcion=matri.inscripcion).exists():
                            rb=RubroInscripcion.objects.filter(rubro__inscripcion=matri.inscripcion)[:1].get()
                            if rb.rubro.cancelado==True:
                                pagado_inscripcion=rb.rubro.valor
                            else:
                                pagado_inscripcion=Pago.objects.filter(rubro=rb.rubro).aggregate(Sum('valor'))['valor__sum']
                                if pagado_inscripcion==None:
                                    pagado_inscripcion=0

                            total_inscripcion=total_inscripcion+ pagado_inscripcion
                            if rb.rubro.adeudado() >0:
                                ws.write(fila,columna,pagado_inscripcion,subtitulo3)
                                ws.write(fila,columna+1,str(rb.rubro.fechavence),subtitulo3)
                            else:
                                ws.write_merge(fila,fila,columna,columna,pagado_inscripcion,subtitulo3)
                        else:
                            ws.write_merge(fila,fila,columna,columna,"NO TIENE RUBRO",subtitulo3)

                        if RubroMatricula.objects.filter(matricula=matri).exists():
                            rb=RubroMatricula.objects.filter(matricula=matri)[:1].get()
                            if rb.rubro.cancelado==True:
                                pagado_matri=rb.rubro.valor
                            else:
                                pagado_matri=Pago.objects.filter(rubro=rb.rubro).aggregate(Sum('valor'))['valor__sum']
                                if pagado_matri==None:
                                    pagado_matri=0

                            total_matricula=total_matricula+ pagado_matri

                            if rb.rubro.adeudado() > 0:
                                ws.write(fila,columna+2,pagado_matri,subtitulo3)
                                ws.write(fila,columna+3,str(rb.rubro.fechavence),subtitulo3)
                            else:
                               ws.write_merge(fila,fila,columna+2,columna+2,pagado_matri,subtitulo3)
                        else:
                            ws.write_merge(fila,fila,columna+2,columna+2,"NO TIENE RUBRO",subtitulo3)

                        if RubroCuota.objects.filter(matricula=matri).exists():
                            cuota=0
                            numcuotas= RubroCuota.objects.filter(matricula=matri).order_by('cuota').distinct('cuota')
                            rubrocuota=RubroCuota.objects.filter(matricula=matri).order_by('cuota')
                            for n in numcuotas:
                                if len(numcuotas)==1:
                                    for rc in RubroCuota.objects.filter(matricula=matri,cuota=n.cuota).order_by('cuota'):
                                        pagado_cuota=0
                                        cuota=Rubro.objects.filter(pk=rc.rubro.id,inscripcion=matri.inscripcion)[:1].get()
                                        if cuota.cancelado==True:
                                            pagado_cuota=cuota.valor
                                        else:
                                            pagado_cuota=Pago.objects.filter(rubro=cuota).aggregate(Sum('valor'))['valor__sum']
                                            if pagado_cuota==None:
                                                pagado_cuota=0

                                        total_cuota=total_cuota+ pagado_cuota
                                        if rc.rubro.adeudado()> 0:
                                            ws.write(fila,columna+4,pagado_cuota,subtitulo3)
                                            ws.write(fila,columna+5,str(rc.rubro.fechavence),subtitulo3)
                                        else:
                                            ws.write_merge(fila,fila,columna+4,columna+4,pagado_cuota,subtitulo3)
                                        columna=columna+1
                                else:
                                    for rc in RubroCuota.objects.filter(matricula=matri,cuota=n.cuota).order_by('cuota'):
                                        pagado_cuota=0
                                        cuota=Rubro.objects.filter(pk=rc.rubro.id,inscripcion=matri.inscripcion)[:1].get()
                                        if cuota.cancelado==True:
                                            pagado_cuota=cuota.valor
                                        else:
                                            pagado_cuota=Pago.objects.filter(rubro=cuota).aggregate(Sum('valor'))['valor__sum']
                                            if pagado_cuota==None:
                                                pagado_cuota=0

                                        total_cuota=total_cuota+ pagado_cuota
                                        if rc.rubro.adeudado()> 0:
                                            ws.write(fila,columna+4,pagado_cuota,subtitulo3)
                                            ws.write(fila,columna+5,str(rc.rubro.fechavence),subtitulo3)
                                        else:
                                            ws.write_merge(fila,fila,columna+4,columna+4,pagado_cuota,subtitulo3)
                                        columna=columna+2
                        ws.write_merge(fila,fila,cab,cab,str(matri.nivel.inicio),subtitulo3)

                        if matri.inscripcion.persona.cedula:
                            identificacion=matri.inscripcion.persona.cedula
                        else:
                            identificacion=matri.inscripcion.persona.pasaporte

                        try:
                            if matri.inscripcion.persona.telefono_conv:
                                telefono1=matri.inscripcion.persona.telefono_conv.replace("-","")
                            else:
                                telefono1=''
                            ws.write_merge(fila,fila,cab+1,cab+1,telefono1,subtitulo3)
                        except Exception as ex:
                            pass

                        try:
                            if matri.inscripcion.persona.telefono:
                                telefono2=matri.inscripcion.persona.telefono.replace("-","")
                            else:
                                telefono2=''
                            ws.write_merge(fila,fila,cab+2,cab+2,telefono2,subtitulo3)
                        except Exception as ex:
                            pass

                        inscritopor=matri.inscripcion.user
                        if matri.inscripcion.user!=None:
                            inscritopor=Persona.objects.filter(usuario=inscritopor).get()
                            inscrito= inscritopor.nombre_completo_inverso()
                        else:
                            inscrito=''
                        ws.write_merge(com, fila,cab+3,cab+5,elimina_tildes(inscrito), subtitulo3)
                        if matri.inscripcion.promocion:
                            promocion=matri.inscripcion.promocion.descripcion
                        else:
                            promocion=''

                        # OCU 27-04-2018 se agrega vendedor
                        if matri.inscripcion.vendedor():
                            vendedor=InscripcionVendedor.objects.filter(inscripcion=matri.inscripcion).get()
                            vendedor=vendedor.vendedor.nombres
                        else:
                            vendedor=''

                        ws.write_merge(com, fila,0,0, str(identificacion) , subtitulo3)
                        ws.write_merge(com, fila,1,3,elimina_tildes(matri.inscripcion.persona.nombre_completo_inverso()), subtitulo3)

                        ws.write_merge(com, fila,cab+6,cab+6,promocion, subtitulo3)
                        ws.write_merge(com, fila,cab+7,cab+7,elimina_tildes(vendedor), subtitulo3)

                        ws.write_merge(com, fila,4,7,elimina_tildes(matri.inscripcion.carrera), subtitulo3)

                        com=fila+1
                        fila = fila +1
                        columna=8
                    ws.write_merge(com, fila,0,3, "TOTALES:" ,titulo2)
                    ws.write_merge(com,fila,4,5,str(total) +" Estudiantes",titulo2)
                    ws.write(fila,columna,total_inscripcion,titulo2)
                    ws.write(fila,columna+2,total_matricula,titulo2)
                    ws.write(fila,columna+4,total_cuota,titulo2)

                    detalle = detalle + fila
                    ws.write(detalle,0, "Fecha Impresion", subtitulo)
                    ws.write(detalle,1, str(datetime.now()), subtitulo)
                    detalle=detalle+2
                    ws.write(detalle,0, "Usuario", subtitulo)
                    ws.write(detalle,1, str(request.user), subtitulo)

                    nombre ='valores_inscritos_general'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")

            elif action  =='generarpdf':
                try:
                    pdf = FPDF()
                    pdf.add_page('Landscape')
                    pdf.set_font('Arial', 'B', 4)  # Arial bold 8
                    pdf.alias_nb_pages(alias='pag_total')
                    # pdf.image(SITE_ROOT+'/media/reportes/encabezados_pies/logo.png', 5, 5, 20,20)  # Logo
                    pdf.ln(30)  # Salto de linea
                    desde = request.POST['desde']
                    hasta = request.POST['hasta']
                    fechai = convertir_fecha(desde)
                    fechaf = convertir_fecha(hasta)
                    nivelmalla= NivelMalla.objects.filter(pk=request.POST['nivelmalla'])[:1].get()

                    # OC 11-junio-2018 para usuario gvlopez presentar solamente informacion de canal 3
                    usuario=request.user
                    if not usuario.username=='gvlopez':
                        matriculados = Matricula.objects.filter(inscripcion__persona__usuario__is_active=True,nivel__nivelmalla=nivelmalla,inscripcion__fecha__gte=fechai,inscripcion__fecha__lte=fechaf).order_by('inscripcion__user','inscripcion__persona__apellido1','inscripcion__persona__apellido2')
                    else:
                        matriculados = Matricula.objects.filter(inscripcion__persona__usuario__is_active=True,nivel__nivelmalla=nivelmalla,inscripcion__fecha__gte=fechai,inscripcion__fecha__lte=fechaf,inscripcion__promocion__id__in=(5,6)).order_by('inscripcion__user','inscripcion__persona__apellido1','inscripcion__persona__apellido2')

                    pdf.text(120,30,"VALORES DE ESTUDIANTES MATRICULADOS POR RANGO DE FECHAS")
                    pdf.text(1,35,"DESDE: " + str(fechai.date()))
                    pdf.text(1,40,"HASTA: " + str(fechaf.date()))
                    pdf.text(1,45,"NIVEL MALLA: " + str(nivelmalla.nombre))

                    total=matriculados.count()
                    fechahoy=datetime.now()
                    fechahoy = fechahoy.strftime('%d/%m/%Y %H:%M:%S%p') # formato dd/mm/yyyy hh:mm:ss am o fm
                    pdf.text(1,50,"Fecha de Impresion: "+ str(fechahoy))
                    pdf.ln(20)  # Salto de linea

                    # para pruebas en desarrollo OCU
                    locale.setlocale( locale.LC_ALL, '' )

                    # para produccion
                    # locale.setlocale( locale.LC_ALL, 'en_US.UTF-8' )

                    # cabecera de la tabla

                    cabecera = ["IDENTIFICACION","ESTUDIANTE","CARRERA","INSCRIP","MATRICULA","CUOTA 1","INICIO NIVEL","CONVENCIONAL","CELULAR","INSCRITO POR","PROMOCION"]
                    w = [20,45,60,25,25,25,20,20,15,15,15]
                    for i in range(0, len(cabecera)):
                        pdf.cell(w[i], 5, cabecera[i], 1, 0, 'C', 0)
                    pdf.ln()

                    identificacion=''
                    telefono1=''
                    telefono2=''

                    total_matricula=0
                    total_inscripcion=0
                    total_cuota=0

                    for matri in matriculados:
                        print(matri)
                        pagado_inscripcion=0
                        pagado_matri=0
                        if matri.inscripcion.persona.cedula:
                            identificacion=matri.inscripcion.persona.cedula
                        else:
                            identificacion=matri.inscripcion.persona.pasaporte

                        pdf.cell(20, 5, str(identificacion), 'LR',0,'C')
                        pdf.cell(45, 5, str(elimina_tildes(matri.inscripcion.persona.nombre_completo_inverso())), 'LR')
                        pdf.cell(60, 5, str(elimina_tildes(matri.inscripcion.carrera.nombre)),'LR', 0, 'C')

                        if RubroInscripcion.objects.filter(rubro__inscripcion=matri.inscripcion).exists():
                            rb=RubroInscripcion.objects.filter(rubro__inscripcion=matri.inscripcion)[:1].get()
                            if rb.rubro.cancelado==True:
                                pagado_inscripcion=rb.rubro.valor
                            else:
                                pagado_inscripcion=Pago.objects.filter(rubro=rb.rubro).aggregate(Sum('valor'))['valor__sum']
                                if pagado_inscripcion==None:
                                    pagado_inscripcion=0

                            total_inscripcion=total_inscripcion+ pagado_inscripcion
                            if rb.rubro.adeudado() >0:
                                pdf.cell(25, 5, str(pagado_inscripcion)+"Vence "+str(rb.rubro.fechavence), 'LR',0,'C')
                            else:
                                pdf.cell(25, 5, str(pagado_inscripcion), 'LR',0,'C')
                        else:
                            # ws.write_merge(fila,fila,columna,columna,"NO TIENE RUBRO",subtitulo3
                            pdf.cell(25, 5, "NO TIENE RUBRO", 'LR',0,'C')

                        if RubroMatricula.objects.filter(matricula=matri).exists():
                            rb=RubroMatricula.objects.filter(matricula=matri)[:1].get()
                            if rb.rubro.cancelado==True:
                                pagado_matri=rb.rubro.valor
                            else:
                                pagado_matri=Pago.objects.filter(rubro=rb.rubro).aggregate(Sum('valor'))['valor__sum']
                                if pagado_matri==None:
                                    pagado_matri=0

                            total_matricula=total_matricula+ pagado_matri

                            if rb.rubro.adeudado() > 0:
                                pdf.cell(25, 5, str(pagado_matri)+" Vence "+str(rb.rubro.fechavence), 'LR',0,'C')
                            else:
                               pdf.cell(25, 5, str(pagado_matri), 'LR',0,'C')
                        else:
                            pdf.cell(25, 5, "NO TIENE RUBRO", 'LR',0,'C')

                        if RubroCuota.objects.filter(matricula=matri).exists():
                            cuota=0
                            numcuotas= RubroCuota.objects.filter(matricula=matri).order_by('cuota').distinct('cuota')
                            rubrocuota=RubroCuota.objects.filter(matricula=matri).order_by('cuota')
                            for n in numcuotas:
                                if len(numcuotas)==1:
                                    for rc in RubroCuota.objects.filter(matricula=matri,cuota=n.cuota).order_by('cuota'):
                                        pagado_cuota=0
                                        cuota=Rubro.objects.filter(pk=rc.rubro.id,inscripcion=matri.inscripcion)[:1].get()
                                        if cuota.cancelado==True:
                                            pagado_cuota=cuota.valor
                                        else:
                                            pagado_cuota=Pago.objects.filter(rubro=cuota).aggregate(Sum('valor'))['valor__sum']
                                            if pagado_cuota==None:
                                                pagado_cuota=0

                                        total_cuota=total_cuota+ pagado_cuota
                                        if rc.rubro.adeudado()> 0:
                                            pdf.cell(25, 5, str(pagado_cuota)+" Vence "+str(rc.rubro.fechavence), 'LR',0,'C')
                                        else:
                                            pdf.cell(25, 5, str(pagado_cuota), 'LR',0,'C')
                                else:
                                    for rc in RubroCuota.objects.filter(matricula=matri,cuota=n.cuota).order_by('cuota'):
                                        pagado_cuota=0
                                        cuota=Rubro.objects.filter(pk=rc.rubro.id,inscripcion=matri.inscripcion)[:1].get()
                                        if cuota.cancelado==True:
                                            pagado_cuota=cuota.valor
                                        else:
                                            pagado_cuota=Pago.objects.filter(rubro=cuota).aggregate(Sum('valor'))['valor__sum']
                                            if pagado_cuota==None:
                                                pagado_cuota=0

                                        total_cuota=total_cuota+ pagado_cuota
                                        if rc.rubro.adeudado()> 0:
                                            pdf.cell(25, 5, str(pagado_cuota)+" Vence "+str(rc.rubro.fechavence), 'LR',0,'C')
                                        else:
                                            pdf.cell(25, 5, str(pagado_cuota), 'LR',0,'C')
                        pdf.cell(20, 5, str(matri.nivel.inicio), 'LR',0,'C')

                        try:
                            if matri.inscripcion.persona.telefono_conv:
                                telefono1=matri.inscripcion.persona.telefono_conv.replace("-","")
                            else:
                                telefono1=''
                            pdf.cell(20, 5, telefono1, 'LR',0,'C')
                        except Exception as ex:
                            pass

                        try:
                            if matri.inscripcion.persona.telefono:
                                telefono2=matri.inscripcion.persona.telefono.replace("-","")
                            else:
                                telefono2=''
                            pdf.cell(20, 5, telefono2, 'LR',0,'C')
                        except Exception as ex:
                            pass

                        inscritopor=matri.inscripcion.user

                        pdf.cell(15, 5, elimina_tildes(inscritopor), 'LR')
                        if matri.inscripcion.promocion:
                            promocion=matri.inscripcion.promocion.descripcion
                        else:
                            promocion=''

                        # OCU 27-04-2018 se agrega vendedor
                        if matri.inscripcion.vendedor():
                            vendedor=InscripcionVendedor.objects.filter(inscripcion=matri.inscripcion).get()
                            vendedor=vendedor.vendedor.nombres
                        else:
                            vendedor=''

                        pdf.cell(15, 5, str(promocion), 'LR')
                        # pdf.cell(25, 5, elimina_tildes(vendedor), 'LR')
                        pdf.ln()

                    pdf.ln(10)
                    pdf.set_font('Arial','B',12)  # Arial bold 12
                    pdf.set_font('')  # restauro la fuente

                    d = datetime.now()
                    pdfname = 'inscritos_general' + '_' + d.strftime('%Y%m%d_%H%M%S') + '.pdf'
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
            data = {'title': 'Valores de Matriculados General'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform']=InscritosGeneralForm(initial={'desde':datetime.now().date(),'hasta':datetime.now().date()})
                return render(request ,"reportesexcel/inscritos_general.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

