import json
from datetime import datetime
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
    RubroMatricula, Pago, RubroCuota, RubroInscripcion, Descuento, DetalleDescuento, InscripcionBecario, TIPOS_PAGO_NIVEL
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
                    ws = wb.add_sheet('Listado',cell_overwrite_ok=True)
                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,m, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,m, 'LISTADO DE ALUMNOS BECADOS POR PROMOCION (GADS MUNICIPIOS)',titulo2)
                    ws.write(3, 0,'Desde:   ' +str(fechai.date()), subtitulo)
                    ws.write(4, 0,'Hasta:   ' +str(fechaf.date()), subtitulo)

                    ws.write(6,0,"ESTUDIANTE",subtitulo3)
                    ws.write(6,1,"IDENTIFICACION",subtitulo3)
                    ws.write(6,2,"TELF. CONV",subtitulo3)
                    ws.write(6,3,"CELULAR",subtitulo3)
                    ws.write(6,4,"PROMOCION",subtitulo3)
                    ws.write(6,5,"EMPRESA CONVENIO",subtitulo3)
                    ws.write(6,6,"% DESCUENTO CONVENIO",subtitulo3)
                    ws.write(6,7,"CUOTAS NIVEL",subtitulo3)
                    ws.write(6,8,"DESCUENTO",subtitulo3)
                    ws.write(6,9,"VALOR CARRERA",subtitulo3)

                    convencional = ''
                    celular = ''
                    fila = 7
                    detalle = 2
                    porcentaje = ''
                    promocion = ''
                    empresa = ''
                    descuento_convenio = ''
                    prueba = ''
                    identificacion=''
                    valorcuotastotal=0
                    valorrubrototal=0
                    descuentototal=0

                    # matriculas_guayaquil = Inscripcion.objects.filter(id__in=[91406],fecha__gte=fechai, fecha__lte=fechaf, becamunicipio=True,persona__usuario__is_active=True).order_by('persona__apellido1')
                    matriculas_guayaquil = Inscripcion.objects.filter(fecha__gte=fechai, fecha__lte=fechaf, becamunicipio=True,persona__usuario__is_active=True).order_by('persona__apellido1')
                    # matriculas_otros = Inscripcion.objects.filter(id__in=[91406],fecha__gte=fechai, fecha__lte=fechaf, persona__usuario__is_active=True).exclude(empresaconvenio=None).exclude(empresaconvenio__id__in=[2,4,16,18,19,21,25]).exclude(empresaconvenio__esempresa=True).order_by('persona__apellido1')
                    matriculas_otros = Inscripcion.objects.filter(fecha__gte=fechai, fecha__lte=fechaf, persona__usuario__is_active=True).exclude(empresaconvenio=None).exclude(empresaconvenio__id__in=[2,4,16,18,19,21,25]).exclude(empresaconvenio__esempresa=True).order_by('persona__apellido1')
                    matriculas = (matriculas_guayaquil|matriculas_otros)
                    print(matriculas_guayaquil.count())
                    print(matriculas_otros.count())
                    print(matriculas.count())
                    lista2=[]
                    for pn in TIPOS_PAGO_NIVEL:
                        if 'CUOTA' in pn[1]:
                            lista2.append(pn[0])

                    for m in matriculas:
                        # print(m)
                        mensaje=''
                        valorcuotas=0
                        valorrubro=0
                        descuento=0
                        porcentaje=''
                        nombre = elimina_tildes(m.persona.nombre_completo_inverso())
                        try:
                            if m.persona.cedula:
                                identificacion = elimina_tildes(m.persona.cedula)
                            else:
                                identificacion = elimina_tildes(m.persona.pasaporte)
                        except:
                            pass
                        try:
                            if m.persona.telefono_conv:
                                convencional = elimina_tildes(m.persona.telefono_conv)
                        except:
                            pass
                        try:
                            if m.persona.telefono:
                                celular = elimina_tildes(m.persona.telefono)
                        except:
                            pass
                        try:
                            if m.promocion:
                                promocion = elimina_tildes(m.promocion.descripcion)
                                porcentaje= m.descuentoporcent
                        except:
                            print('ERROR: '+str(m.id))
                        try:
                            if m.empresaconvenio:
                                empresa = elimina_tildes(m.empresaconvenio.nombre)
                                porcentaje= m.descuentoporcent
                            else:
                                if m.becamunicipio:
                                    empresa = 'MUNICIPIO DE GUAYAQUIL'
                        except:
                            print('ERROR: '+str(m.id))
                        try:
                            if m.descuentoconvenio:
                                descuento_convenio = elimina_tildes(m.descuentoconvenio.descripcion)
                        except:
                            print('ERROR: '+str(m.id))

                        if RubroCuota.objects.filter(matricula__inscripcion=m).exists():
                            for rc in RubroCuota.objects.filter(matricula__inscripcion=m):
                                if DetalleDescuento.objects.filter(rubro=rc.rubro).exists():
                                    valorcuotas+=rc.rubro.valor + DetalleDescuento.objects.filter(rubro=rc.rubro)[:1].get().valor
                                    valorcuotastotal+=rc.rubro.valor + DetalleDescuento.objects.filter(rubro=rc.rubro)[:1].get().valor
                                    valorrubro+=rc.rubro.valor
                                    valorrubrototal+=rc.rubro.valor
                                    descuento+=DetalleDescuento.objects.filter(rubro=rc.rubro)[:1].get().valor
                                    descuentototal+=DetalleDescuento.objects.filter(rubro=rc.rubro)[:1].get().valor
                                else:
                                    if Matricula.objects.filter(inscripcion=m,becado=True,liberada=False).exists():
                                        for matri in Matricula.objects.filter(inscripcion=m,becado=True,liberada=False):
                                            porcentaje=matri.porcientobeca
                                            if matri.nivel.pagonivel_set.filter(tipo__in=lista2).exists():
                                                for pago in  matri.nivel.pagonivel_set.filter(tipo__in=lista2):
                                                    if pago.tipo!=0:
                                                        valorcuotas+= pago.valor
                                                        valorcuotastotal+=pago.valor
                                                        desc= round(((pago.valor * porcentaje)/100),2)
                                                        valorrubro+=pago.valor - desc
                                                        valorrubrototal+=pago.valor - desc
                                                        descuento+= round(((pago.valor * porcentaje)/100),2)
                                                        descuentototal+= round(((pago.valor * porcentaje)/100),2)
                                            else:
                                                mensaje='NO HAY CRONOGRAMA DE PAGOS'
                                    else:
                                        if m.empresaconvenio is not None and porcentaje==0:
                                            mensaje='NO HAY PORCENTAJE EN ESE CONVENIO'
                        else:
                            if Matricula.objects.filter(inscripcion=m,becado=True,liberada=False).exists():
                                for matri in Matricula.objects.filter(inscripcion=m,becado=True,liberada=False):
                                    porcentaje=matri.porcientobeca
                                    if matri.nivel.pagonivel_set.filter(tipo__in=lista2).exists():
                                        for pago in  matri.nivel.pagonivel_set.filter(tipo__in=lista2):
                                            if pago.tipo!=0:
                                                valorcuotas+= pago.valor
                                                valorcuotastotal+=pago.valor
                                                desc= round(((pago.valor * porcentaje)/100),2)
                                                valorrubro+=pago.valor - desc
                                                valorrubrototal+=pago.valor - desc
                                                descuento+= round(((pago.valor * porcentaje)/100),2)
                                                descuentototal+= round(((pago.valor * porcentaje)/100),2)
                                    else:
                                        mensaje='NO HAY CRONOGRAMA DE PAGOS'
                            else:
                                if m.promocion:
                                    if Matricula.objects.filter(inscripcion=m).exists():
                                        for matri in Matricula.objects.filter(inscripcion=m):
                                            for pago in  matri.nivel.pagonivel_set.filter(tipo__in=lista2):
                                                if pago.tipo!=0:
                                                    des = ((100-porcentaje)/100.0)
                                                    descuento = round(((pago.valor * porcentaje)/100),2)
                                                    valorcuotas+= pago.valor
                                                    valorcuotas+=rc.rubro.valor
                                                    valorcuotastotal+=rc.rubro.valor
                                                    valorrubro+=pago.valor-descuento
                                                    valorrubrototal+=pago.valor-descuento
                                                    descuentototal+=descuento
                                    else:
                                        mensaje='NO ESTA MATRICULADO'
                        ws.write(fila, 0, nombre, subtitulo3)
                        ws.write(fila, 1, identificacion, subtitulo3)
                        ws.write(fila, 2, convencional, subtitulo3)
                        ws.write(fila, 3, celular, subtitulo3)
                        ws.write(fila, 4, promocion, subtitulo3)
                        ws.write(fila, 5, empresa, subtitulo3)
                        ws.write(fila, 6, porcentaje, subtitulo3)
                        ws.write(fila, 7, valorcuotas, subtitulo3)
                        ws.write(fila, 8, descuento, subtitulo3)
                        ws.write(fila, 9, valorrubro, subtitulo3)
                        ws.write(fila, 10, mensaje, subtitulo3)

                        fila = fila+1

                    ws.write(fila, 5, "TOTAL ", subtitulo)
                    ws.write(fila, 7, valorcuotastotal, subtitulo3)
                    ws.write(fila, 8, descuentototal, subtitulo3)
                    ws.write(fila, 9, valorrubrototal, subtitulo3)

                    detalle = detalle + fila
                    ws.write(detalle,0, "Fecha Impresion", subtitulo)
                    ws.write(detalle,1, str(datetime.now()), subtitulo)
                    detalle = detalle+1
                    ws.write(detalle,0, "Usuario", subtitulo)
                    ws.write(detalle,1, str(request.user), subtitulo)

                    nombre ='pagos_nivelseminario_descuento'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")

        else:
            data = {'title': 'Listado de Alumnos Becados Promocion(GADS MUNICIPIOS)'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform']=RangoFacturasForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
                return render(request ,"reportesexcel/xls_inscripciones_gads.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

