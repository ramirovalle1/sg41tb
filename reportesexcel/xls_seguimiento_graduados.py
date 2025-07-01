from datetime import datetime,timedelta
import json
import xlrd
import xlwt

from django.contrib.auth.decorators import login_required

from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from settings import UTILIZA_GRUPOS_ALUMNOS, EMAIL_ACTIVE,MEDIA_ROOT, ASIG_VINCULACION, ASIG_PRATICA
from sga.commonviews import addUserData, ip_client_address
from sga.forms import RangoFacturasForm,RangoNCForm, VinculacionExcelForm
from sga.models import Inscripcion,convertir_fecha,Factura,ClienteFactura,TituloInstitucion,ReporteExcel,Graduado, Persona,SeguimientoGraduado, Carrera, Matricula, RecordAcademico
from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action :

                try:
                    carrera= Carrera.objects.filter(pk=request.POST['carrera'])[:1].get()
                    idseguimiento = SeguimientoGraduado.objects.filter().values_list('graduado_id',flat=True)
                    graduados = Graduado.objects.filter(id__in=list(idseguimiento),inscripcion__carrera=carrera).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')
                    totalg = graduados.count()
                    m = 5
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('RegistroConSeguimiento',cell_overwrite_ok=True)
                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,m+2, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,m+2, 'LISTADO DE GRADUADOS POR CARRERA ', titulo2)
                    ws.write(2, 0, 'CON SEGUIMIENTO',titulo)
                    ws.write(3, 0, 'CARRERA', titulo)
                    ws.write(3, 1, carrera.nombre, titulo)
                    ws.write(4, 0,  'IDENTIFICACION', titulo)
                    ws.write(4, 1,  'NOMBRES', titulo)
                    ws.write(4, 2,  'F. GRADUADO', titulo)
                    ws.write(4, 3,  'EMAIL PERSONAL', titulo)
                    ws.write(4, 4,  'TLF. CONVENCIONAL', titulo)
                    ws.write(4, 5,  'CELULAR', titulo)
                    ws.write(4, 6,  'LUGAR DE TRABAJO', titulo)
                    ws.write(4, 7,  'EMAIL TRABAJO', titulo)
                    ws.write(4, 8,  'TLF. TRABAJO', titulo)
                    ws.write(4, 9,  'CARGO', titulo)
                    ws.write(4, 10, 'SUELDO', titulo)
                    ws.write(4, 11, 'EJERCE', titulo)

                    # OC 14-06-2018 se agregan los correos que tengan registrados los estudiantes
                    ws.write(4,12,"EMAIL INST",titulo)
                    ws.write(4,13,"EMAIL 1",titulo)
                    ws.write(4,14,"EMAIL 2",titulo)
                    #OCastillo 23-05-2023 nueva informacion solicitada por requerimiento
                    ws.write(4,15,"PROVINCIA",titulo)
                    ws.write(4,16,"CANTON",titulo)
                    ws.write(4,17,"PARROQUIA",titulo)
                    ws.write(4,18,"DIRECCION",titulo)
                    ws.write(4,19,"ANIOS GRADUADO",titulo)

                    fila = 4
                    detalle = 3
                    # que tiene seguimiento
                    g=None
                    hoy = datetime.now().today()
                    if graduados.count()>0:
                        for g in graduados:
                            fila = fila +1
                            correo1=''
                            correo2=''
                            correo3=''
                            telefono=''
                            telefono2=''
                            empresa=''
                            provincia=''
                            canton=''
                            parroquia=''
                            direccion=''
                            f_graduado=''
                            aniosgraduado=''
                            columna=0
                            #print(g.id)
                            if g.inscripcion.persona.emailinst:
                                correo1=elimina_tildes(g.inscripcion.persona.emailinst)
                            else:
                                correo1=''

                            if g.inscripcion.persona.email1:
                                correo2=elimina_tildes(g.inscripcion.persona.email1)
                            else:
                                correo2=''

                            if g.inscripcion.persona.email2:
                                correo3=elimina_tildes(g.inscripcion.persona.email2)
                            else:
                                correo3=''

                            if not g.inscripcion.persona.cedula:
                                documento=str(g.inscripcion.persona.pasaporte)
                            else:
                                documento=str(g.inscripcion.persona.cedula)
                            ws.write(fila,columna , documento)
                            ws.write(fila,columna+1, elimina_tildes(g.inscripcion.persona.nombre_completo_inverso()))
                            ws.write(fila,columna+2, str(g.fechagraduado))
                            try:
                                ws.write(fila,columna+3, elimina_tildes(g.inscripcion.persona.email))
                            except Exception as ex:
                                ws.write(fila,columna+3, "")

                            try:
                                if g.inscripcion.persona.telefono_conv:
                                    telefono=g.inscripcion.persona.telefono_conv.replace("-","")
                                else:
                                    telefono=''
                                ws.write(fila,columna+4, telefono)
                            except Exception as ex:
                                ws.write(fila,columna+4, "")
                                pass

                            try:
                                if g.inscripcion.persona.telefono:
                                    telefono2=g.inscripcion.persona.telefono.replace("-","")
                                else:
                                    telefono2=''
                                ws.write(fila,columna+5, telefono2)
                            except Exception as ex:
                                ws.write(fila,columna+5, "")
                                pass

                            try:
                                provincia = elimina_tildes(g.inscripcion.persona.provinciaresid)
                            except:
                                provincia = ''
                            try:
                                canton = elimina_tildes(g.inscripcion.persona.cantonresid)
                            except:
                                canton = ''
                            try:
                                parroquia = elimina_tildes(g.inscripcion.persona.parroquia)
                            except:
                                parroquia = ''
                            try:
                                direccion = elimina_tildes(g.inscripcion.persona.direccion_completa())
                            except:
                                direccion = ''
                            try:
                                f_graduado=g.fechagraduado
                                fn=(f_graduado)
                                anio = fn.year
                                mes = fn.month
                                anio_act=hoy.year
                                mes_act=hoy.month
                                if fn:
                                   aniosgraduado=(anio_act-anio)
                                   if mes_act<mes:
                                       aniosgraduado=aniosgraduado-1
                            except:
                                aniosgraduado=''

                            for sg in SeguimientoGraduado.objects.filter(graduado__id=g.pk):
                                if sg:
                                    try:
                                        if sg.empresa:
                                            empresa=elimina_tildes(sg.empresa)
                                        else:
                                            empresa=''
                                        ws.write(fila,columna+6,empresa)
                                    except Exception as ex:
                                        ws.write(fila,columna+6, "")
                                        pass

                                    ws.write(fila,columna+7,elimina_tildes(sg.email))
                                    ws.write(fila,columna+8,elimina_tildes(sg.telefono))
                                    ws.write(fila,columna+9,elimina_tildes(sg.cargo))
                                    ws.write(fila,columna+10,sg.sueldo)
                                    if sg.ejerce==True:
                                        ejerce='Si'
                                    else:
                                        ejerce='No'
                                    ws.write(fila,columna+11,ejerce)

                            ws.write(fila,columna+12,str(correo1))
                            ws.write(fila,columna+13,str(correo2))
                            ws.write(fila,columna+14,str(correo3))
                            ws.write(fila,columna+15,str(provincia))
                            ws.write(fila,columna+16,str(canton))
                            ws.write(fila,columna+17,str(parroquia))
                            ws.write(fila,columna+18,str(direccion))
                            ws.write(fila,columna+19,str(aniosgraduado))

                    detalle = detalle + fila

                    ws.write(detalle, 0, "Total con Seguimiento", subtitulo)
                    ws.write(detalle, 2, graduados.count())
                    detalle=detalle +1
                    ws.write(detalle, 0, "Fecha Impresion", subtitulo)
                    ws.write(detalle, 2, str(datetime.now()), subtitulo)
                    detalle=detalle +1
                    ws.write(detalle, 0, "Usuario", subtitulo)
                    ws.write(detalle, 2, str(request.user), subtitulo)

                    graduadosinse = Graduado.objects.filter(inscripcion__carrera=carrera).exclude(id__in=list(idseguimiento)).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')

                    ws1 = wb.add_sheet('RegistroSinSeguimiento',cell_overwrite_ok=True)
                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws1.write_merge(0, 0,0,m+2, tit.nombre , titulo2)
                    ws1.write_merge(1, 1,0,m+2, 'LISTADO DE GRADUADOS POR CARRERA ', titulo2)
                    ws1.write(2, 0, 'SIN SEGUIMIENTO',titulo)
                    ws1.write(3, 0, 'CARRERA', titulo)
                    ws1.write(3, 1, carrera.nombre, titulo)
                    ws1.write(4, 0,  'IDENTIFICACION', titulo)
                    ws1.write(4, 1,  'NOMBRES', titulo)
                    ws1.write(4, 2,  'F. GRADUADO', titulo)
                    ws1.write(4, 3,  'EMAIL PERSONAL', titulo)
                    ws1.write(4, 4,  'TLF. CONVENCIONAL', titulo)
                    ws1.write(4, 5,  'CELULAR', titulo)
                    ws1.write(4, 6,  'LUGAR DE TRABAJO', titulo)
                    ws1.write(4, 7,  'EMAIL TRABAJO', titulo)
                    ws1.write(4, 8,  'TLF. TRABAJO', titulo)
                    ws1.write(4, 9,  'CARGO', titulo)
                    ws1.write(4, 10, 'SUELDO', titulo)
                    ws1.write(4, 11, 'EJERCE', titulo)

                    # OC 14-06-2018 se agregan los correos que tengan registrados los estudiantes
                    ws1.write(4,12,"EMAIL INST",titulo)
                    ws1.write(4,13,"EMAIL 1",titulo)
                    ws1.write(4,14,"EMAIL 2",titulo)

                    fila1 = 4
                    detalle2 = 3

                    if graduadosinse.count()>0:

                        for g in graduadosinse:
                           # print(g)
                            correo1=''
                            correo2=''
                            correo3=''
                            telefono=''
                            telefono2=''
                            empresa=''
                            fila1 = fila1 +1
                            columna=0

                            if g.inscripcion.persona.emailinst:
                                correo1=elimina_tildes(g.inscripcion.persona.emailinst)
                            else:
                                correo1=''

                            if g.inscripcion.persona.email1:
                                correo2=elimina_tildes(g.inscripcion.persona.email1)
                            else:
                                correo2=''

                            if g.inscripcion.persona.email2:
                                correo3=elimina_tildes(g.inscripcion.persona.email2)
                            else:
                                correo3=''

                            if not g.inscripcion.persona.cedula:
                                documento=str(g.inscripcion.persona.pasaporte)
                            else:
                                documento=str(g.inscripcion.persona.cedula)
                            ws1.write(fila1,columna , documento)
                            ws1.write(fila1,columna+1, elimina_tildes(g.inscripcion.persona.nombre_completo_inverso()))
                            ws1.write(fila1,columna+2, str(g.fechagraduado))
                            try:
                                ws1.write(fila1,columna+3,elimina_tildes(g.inscripcion.persona.email))
                            except Exception as ex:
                                ws1.write(fila1,columna+3, "")
                            try:
                                if g.inscripcion.persona.telefono_conv:
                                    telefono=g.inscripcion.persona.telefono_conv.replace("-","")
                                else:
                                    telefono=''
                                ws.write(fila,columna+4, telefono)
                            except Exception as ex:
                                ws.write(fila,columna+4, "")
                                pass

                            try:
                                if g.inscripcion.persona.telefono:
                                    telefono2=g.inscripcion.persona.telefono.replace("-","")
                                else:
                                    telefono2=''
                                ws.write(fila,columna+5, telefono2)
                            except Exception as ex:
                                ws.write(fila,columna+5, "")
                                pass

                            for sg in SeguimientoGraduado.objects.filter(graduado__id=g.pk):
                                if sg:
                                    try:
                                        if sg.empresa:
                                            empresa=elimina_tildes(sg.empresa)
                                        else:
                                            empresa=''
                                        ws.write(fila,columna+6,empresa)
                                    except Exception as ex:
                                        ws.write(fila,columna+6, "")
                                        pass

                                    ws1.write(fila1,columna+7,elimina_tildes(sg.email))
                                    ws1.write(fila1,columna+8,elimina_tildes(sg.telefono))
                                    ws1.write(fila1,columna+9,elimina_tildes(sg.cargo))
                                    ws1.write(fila1,columna+10,sg.sueldo)
                                    if sg.ejerce==True:
                                        ejerce='Si'
                                    else:
                                        ejerce='No'
                                    ws1.write(fila1,columna+11,ejerce)

                            ws1.write(fila1,columna+12,str(correo1))
                            ws1.write(fila1,columna+13,str(correo2))
                            ws1.write(fila1,columna+14,str(correo3))


                        detalle2 = detalle2 + fila1

                        ws1.write(detalle2, 0, "Total sin Segumiento", subtitulo)
                        ws1.write(detalle2, 2, graduadosinse.count())
                        detalle2=detalle2 +1
                        ws1.write(detalle2, 0, "Fecha Impresion", subtitulo)
                        ws1.write(detalle2, 2, str(datetime.now()), subtitulo)
                        detalle2=detalle2 +1
                        ws1.write(detalle2, 0, "Usuario", subtitulo)
                        ws1.write(detalle2, 2, str(request.user), subtitulo)

                    nombre ='seguimiento'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)+" "+str(g)}),content_type="application/json")

        else:
            data = {'title': 'Listado de Seguimiento a Graduados'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform']=VinculacionExcelForm()
                return render(request ,"reportesexcel/seguimiento_graduados.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

