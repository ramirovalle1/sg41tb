from datetime import datetime
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
from sga.forms import GestionExcelForm
from sga.models import Inscripcion,convertir_fecha,Factura,ClienteFactura,TituloInstitucion,ReporteExcel,NotaCreditoInstitucion, Persona,TipoNotaCredito, Carrera, Matricula, RecordAcademico, Egresado, Malla, AsignaturaMalla, NivelMalla, MateriaAsignada, Asignatura, Nivel, Periodo, ProfesorMateria, PagoNivel, Rubro, RubroMatricula, Pago, RubroCuota, RubroInscripcion
from fpdf import FPDF

from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action  =='generarexcel':
                print(request.POST)
                try:
                    titulo = xlwt.easyxf('font: name Times New Roman, bold on; align: wrap on, vert centre, horiz center')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    # titulo2 = xlwt.Pattern()
                    # titulo2.pattern = xlwt.Pattern.SOLID_PATTERN
                    # titulo2.pattern_fore_colour = 2

                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo3 = xlwt.easyxf('font: name Times New Roman; align: wrap on, vert centre, horiz center')
                    subtitulo.font.height = 20*10
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('Registros',cell_overwrite_ok=True)

                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,11, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,11, 'LISTADO VALORES VENCIDOS POR CARRERA',titulo2)


                    fila = 5

                    carrera = Carrera.objects.get(pk=request.POST['carrera'])
                    periodo = Periodo.objects.get(pk=request.POST['periodo'])
                    niveles = Nivel.objects.filter(carrera=carrera, periodo=periodo).order_by('paralelo')
                    hoy = datetime.now().date()

                    for nivel in niveles:
                        pago_nivel=PagoNivel.objects.filter(nivel=nivel).order_by('fecha')
                        matriculas = Matricula.objects.filter(nivel=nivel).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')
                        c = 6
                        if matriculas.exists():
                            ws.write_merge(4,4,0,3, 'DATOS GENERALES',titulo)
                            ws.write_merge(4,4,4,11, 'VALORES VENCIDOS',titulo)
                            ws.write(fila, 0,'GRUPO', titulo)
                            ws.write(fila, 1,'NIVEL', titulo)
                            ws.write(fila, 2,'ALUMNO', titulo)
                            ws.write(fila, 3,'CEDULA', titulo)
                            ws.write(fila, 4,'TELEFONO', titulo)
                            ws.write(fila, 5,'INSCRIPCION', titulo)
                            for pn in pago_nivel:
                                if pn.tipo==0:
                                    tipo_cuota='MATRICULA'
                                    fecha=pn.fecha
                                else:
                                    tipo_cuota='CUOTA'+" " +str(pn.tipo)
                                    fecha=pn.fecha
                                ws.write(fila,c,tipo_cuota + " " + str(pn.fecha)+' ($' +str(pn.valor)+')',titulo)
                                c= c +1

                            # ws.write(5, 5,'MATRICULA', titulo)
                            # ws.write(5, 6,'CUOTA #1', titulo)
                            # ws.write(5, 7,'CUOTA #2', titulo)
                            # ws.write(5, 8,'CUOTA #3', titulo)
                            # ws.write(5, 9,'CUOTA #4', titulo)
                            # ws.write(5, 10,'CUOTA #5', titulo)
                            # ws.write(5, 11,'CUOTA #6', titulo)

                            fila = fila + 1
                            total_inscripcion = 0
                            total_alumno = 0
                            total_cuota1 = 0
                            total_cuota2 = 0
                            total_cuota3=0
                            total_cuota4=0
                            total_cuota5=0
                            total_cuota6=0
                            total_matricula=0
                            total_inscripcion=0

                            for m in matriculas:
                                print(m.id)
                                ws.write(fila, 0, nivel.grupo.nombre)
                                ws.write(fila, 1, nivel.nivelmalla.nombre)
                                ws.write(fila, 2, m.inscripcion.persona.nombre_completo_inverso())

                                if m.inscripcion.persona.cedula:
                                    ws.write(fila, 3, m.inscripcion.persona.cedula)
                                else:
                                    ws.write(fila, 3, m.inscripcion.persona.pasaporte)

                                if m.inscripcion.persona.telefono:
                                    ws.write(fila, 4, m.inscripcion.persona.telefono)
                                else:
                                    ws.write(fila, 4, '')
                                if RubroInscripcion.objects.filter(rubro__inscripcion=m.inscripcion).exists():
                                    rb=RubroInscripcion.objects.filter(rubro__inscripcion=m.inscripcion)[:1].get()
                                    if rb.rubro.cancelado==True:
                                        estado="P"
                                    else:
                                        pagado_inscripcion = Pago.objects.filter(rubro=rb.rubro).aggregate(Sum('valor'))['valor__sum']
                                        if pagado_inscripcion == None:
                                            pagado_inscripcion = 0
                                        estado = rb.rubro.valor - pagado_inscripcion
                                        total_inscripcion = total_inscripcion + estado
                                        total_alumno = total_alumno + estado
                                    ws.write(fila,5, estado,subtitulo3)
                                else:
                                    ws.write(fila,5, "SIN RUBRO", subtitulo3)
                                c=6
                                for pn in pago_nivel:
                                    p=0
                                    estado = 0
                                    if not RubroCuota.objects.filter(matricula=m,cuota=pn.tipo).exists():
                                        if RubroMatricula.objects.filter(matricula=m).exists():
                                            rubro_matricula =  RubroMatricula.objects.filter(matricula=m)
                                            if rubro_matricula.get().rubro.cancelado:
                                                ws.write(fila,c,'P',subtitulo3)
                                            else:
                                                pagado_matri = Pago.objects.filter(rubro=rubro_matricula.get().rubro).aggregate(Sum('valor'))['valor__sum']
                                                if pagado_matri == None:
                                                    pagado_matri = 0
                                                estado = rubro_matricula.get().rubro.valor - pagado_matri
                                                total_matricula = total_matricula + estado
                                                total_alumno = total_alumno + estado

                                                # if rubro_matricula.filter(rubro__fechavence__lt=hoy).exists():
                                                #     rb = rubro_matricula.filter(rubro__fechavence__lt=hoy)[:1].get()
                                                #     ws.write(fila,c, estado, subtitulo3)

                                                if rubro_matricula.filter(rubro__fechavence__lt=hoy).exists():
                                                    ws.write(fila,c, estado, subtitulo3)
                                                else:
                                                    ws.write(fila,c,'-',subtitulo3)
                                        else:
                                            estado='-'
                                            ws.write(fila,c,estado,subtitulo3)

                                    if RubroCuota.objects.filter(matricula=m,cuota=pn.tipo).exists():
                                        estado = 0
                                        c=c+1
                                        rc=RubroCuota.objects.filter(matricula=m)[:1].get()
                                        if rc.rubro.cancelado:
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

                                        if pn.fecha < hoy and not rc.rubro.cancelado:
                                            ws.write(fila,c, estado, subtitulo3)
                                        else:
                                            ws.write(fila,c, '-', subtitulo3)


                                fila = fila+1
                        fila = fila+1


                    nombre ='valores_vencidos'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")


        else:
            data = {'title': 'Estado de Cuenta por Nivel'}
            addUserData(request,data)
            # if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
            reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
            data['reportes'] = reportes
            data['form'] = GestionExcelForm

            return render(request ,"reportesexcel/valoresvencidos_xperiodo_xcoordinacion.html" ,  data)
            # return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

