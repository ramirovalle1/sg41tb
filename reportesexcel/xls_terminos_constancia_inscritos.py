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
from sga.forms import DistributivoForm
from sga.models import Inscripcion,convertir_fecha,Factura,ClienteFactura,TituloInstitucion,ReporteExcel,NotaCreditoInstitucion, Persona,TipoNotaCredito, Carrera, Matricula, RecordAcademico, Egresado, Malla, AsignaturaMalla, NivelMalla, MateriaAsignada, Asignatura, Nivel, Periodo, ProfesorMateria, PagoNivel, Rubro, RubroMatricula, Pago, RubroCuota, RubroInscripcion, InscripcionVendedor, InscripcionGrupo, ViewCrmProspectos
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
                    inscritos = Inscripcion.objects.filter(persona__usuario__is_active=True,fecha__gte=fechai,fecha__lte=fechaf,carrera__carrera=True).order_by('persona__apellido1','persona__apellido2')
                    total_inscritos=0
                    m = 17
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
                    ws.write_merge(1, 1,0,m, 'Aceptacion Terminos y Constancia de Estudiantes Inscritos por Rango de Fechas',titulo2)
                    ws.write(4, 0,'Desde:   ' +str(fechai.date()), subtitulo)
                    ws.write(5, 0,'Hasta:   ' +str(fechaf.date()), subtitulo)

                    fila = 9
                    com = 9
                    detalle = 3
                    columna=12
                    c=9
                    telefono1=''
                    telefono2=''
                    emailinst=''
                    emailpersonal=''
                    identificacion=''
                    ws.write(8,0,"CEDULA",titulo)
                    ws.write_merge(8,8,1,3,"NOMBRES",titulo)
                    ws.write_merge(8,8,4,7,"CARRERA",titulo)
                    ws.write(8,8, "Paralelo",titulo)
                    ws.write(8,9, "Fecha Inscripcion",titulo)
                    ws.write(8,10,"Acepta Terminos",titulo)
                    ws.write(8,11,"Fecha Acepta Terminos",titulo)
                    ws.write(8,12,"Acepta Constancia",titulo)
                    ws.write(8,13,"Fecha Acepta Constancia",titulo)
                    ws.write(8,14,"CONVENCIONAL",titulo)
                    ws.write(8,15,"CELULAR",titulo)
                    ws.write(8,16,"EMAIL INST",titulo)
                    ws.write(8,17,"EMAIL PERSONAL",titulo)
                    inscri=None
                    for inscri in inscritos:
                        # print(inscri)
                        aceptatermino=''
                        aceptaconstancia=''
                        fechainscripcion=''
                        fechaaceptatermino=''
                        fechaaceptaconstancia=''
                        total_inscritos=total_inscritos+1

                        if inscri.persona.cedula:
                            identificacion=inscri.persona.cedula
                        else:
                            identificacion=inscri.persona.pasaporte

                        ws.write_merge(com, fila,0,0, str(identificacion) , subtitulo3)
                        ws.write_merge(com, fila,1,3,elimina_tildes(inscri.persona.nombre_completo_inverso()), subtitulo3)
                        ws.write_merge(com, fila,4,7,elimina_tildes(inscri.carrera), subtitulo3)
                        grupoinsc=InscripcionGrupo.objects.filter(inscripcion=inscri).get()
                        ws.write_merge(com, fila,8,8,elimina_tildes(grupoinsc.grupo.nombre), subtitulo3)

                        if inscri.fecha:
                            fechainscripcion=inscri.fecha
                        ws.write_merge(com, fila,9,9,str(fechainscripcion), subtitulo3)

                        if inscri.aceptatermino:
                            aceptatermino='SI'
                            fechaaceptatermino=inscri.fechaceptatermino

                        if inscri.aceptaconstancia:
                            aceptaconstancia='SI'
                            fechaaceptaconstancia=inscri.fechaceptaconstancia

                        ws.write_merge(com, fila,10,10,aceptatermino, subtitulo3)
                        ws.write_merge(com, fila,11,11,str(fechaaceptatermino) , subtitulo3)
                        ws.write_merge(com, fila,12,12,aceptaconstancia, subtitulo3)
                        ws.write_merge(com, fila,13,13,str(fechaaceptaconstancia), subtitulo3)

                        try:
                            if inscri.persona.telefono_conv:
                                telefono1=inscri.persona.telefono_conv.replace("-","")
                            else:
                                telefono1=''
                            ws.write_merge(com,fila,14,14,telefono1,subtitulo3)
                        except Exception as ex:
                            pass

                        try:
                            if inscri.persona.telefono:
                                telefono2=inscri.persona.telefono.replace("-","")
                            else:
                                telefono2=''
                            ws.write_merge(com,fila,15,15,telefono2,subtitulo3)
                        except Exception as ex:
                            pass

                        try:
                            if inscri.persona.emailinst:
                                correo1=inscri.persona.emailinst
                            else:
                                correo1=''
                            ws.write_merge(com,fila,16,16,correo1,subtitulo3)
                        except Exception as ex:
                            pass

                        try:
                            if inscri.persona.email:
                                correo2=inscri.persona.email
                            else:
                                correo2=''
                            ws.write_merge(com,fila,17,17,correo2,subtitulo3)
                        except Exception as ex:
                            pass

                        com=fila+1
                        fila = fila +1


                    ws.write_merge(com, fila,0,3, "TOTALES:" ,titulo2)
                    ws.write_merge(com,fila,4,5,str(total_inscritos) +" Estudiantes",titulo2)

                    detalle = detalle + fila
                    ws.write(detalle,0, "Fecha Impresion", subtitulo)
                    ws.write(detalle,1, str(datetime.now()), subtitulo)
                    detalle=detalle+2
                    ws.write(detalle,0, "Usuario", subtitulo)
                    ws.write(detalle,1, str(request.user), subtitulo)

                    nombre ='aceptacion_terminos_constancia'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)+" "+str(inscri)}),content_type="application/json")
        else:
            data = {'title': 'Acepta Terminos y Constancia en Inscritos'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform']=DistributivoForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
                return render(request ,"reportesexcel/xls_terminos_constancia_inscritos.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

