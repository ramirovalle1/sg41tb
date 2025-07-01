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
from settings import UTILIZA_GRUPOS_ALUMNOS, EMAIL_ACTIVE,MEDIA_ROOT, SITE_ROOT
from sga.commonviews import addUserData, ip_client_address
from sga.forms import ConveniosExcelForm
from sga.models import Inscripcion,convertir_fecha,TituloInstitucion,ReporteExcel,EmpresaConvenio,Persona,Canton,Provincia
from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):

    try:
        if request.method=='POST':
            action = request.POST['action']
            if action :
                print(request.POST)
                desde = request.POST['desde']
                hasta = request.POST['hasta']
                fechai = convertir_fecha(desde)
                fechaf = convertir_fecha(hasta)
                try:
                    if request.POST['usaconvenio'] == '1':
                        convenio= EmpresaConvenio.objects.filter(pk=request.POST['convenio'])[:1].get()
                        inscritos = Inscripcion.objects.filter(fecha__gte=fechai,fecha__lte=fechaf,empresaconvenio=convenio).order_by('persona__apellido1','persona__apellido2','persona__nombres')
                    else:
                        convenio = EmpresaConvenio.objects.filter().order_by()
                        inscritos = Inscripcion.objects.filter(fecha__gte=fechai,fecha__lte=fechaf).exclude(empresaconvenio__id=4).exclude(empresaconvenio=None).order_by('persona__apellido1','persona__apellido2','persona__nombres')
                    m = 8
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10
                    style1 = xlwt.easyxf('',num_format_str='DD-MMM-YY')
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('Informacion',cell_overwrite_ok=True)
                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,m+2, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,m+2, 'INFORMACION DE ESTUDIANTES POR CONVENIO', titulo2)
                    ws.write(6, 0, 'CONVENIO ', subtitulo)
                    ws.write(6, 1, 'IDENTIFICACION', titulo)
                    ws.write(6, 2, 'ESTUDIANTE', titulo)
                    ws.write(6, 3, 'CARRERA', titulo)
                    ws.write(6, 4, 'PARALELO', titulo)
                    ws.write(6, 5, 'CONVENCIONAL', titulo)
                    ws.write(6, 6, 'CELULAR', titulo)
                    ws.write(6, 7, 'Email Institucional', titulo)
                    ws.write(6, 8, 'Email Personal', titulo)
                    ws.write(6, 9,  'Fecha de Inscripcion', titulo)
                    ws.write(6, 10,  'PROVINCIA RESIDENCIA', titulo)
                    ws.write(6, 11, 'CANTON RESIDENCIA', titulo)
                    ws.write(6, 12, 'PROVINCIA NACIMIENTO', titulo)
                    ws.write(6, 13, 'CANTON NACIMIENTO', titulo)
                    ws.write(6, 14, 'PROMOCION', titulo)
                    ws.write(6, 15, 'DESCUENTO INSCRIPCION', titulo)
                    ws.write(6, 16, 'DESCUENTO CUOTAS', titulo)
                    ws.write(6, 17, 'ASESOR', titulo)

                    #inscritos = Inscripcion.objects.filter(pk=64436,fecha__gte=fechai,fecha__lte=fechaf,empresaconvenio=convenio).order_by('persona__apellido1','persona__apellido2','persona__nombres')
                    detalle = 4
                    fila = 7

                    identificacion=''
                    estudiante=''
                    carrera=''
                    paralelo=''
                    emailinst=''
                    email=''
                    telefono=''
                    celular=''
                    fechainscripcion=''
                    inscrito=''
                    inscritopor=''
                    promocion=''
                    descuento=''
                    canton_residencia=''
                    provincia_residencia=''
                    parroquia_residencia=''
                    canton_nacimiento=''
                    provincia_nacimiento=''
                    desc_cuotas=0
                    for inscrito in inscritos:
                        if inscrito.persona.cedula:
                            identificacion=inscrito.persona.cedula
                        else:
                            identificacion=inscrito.persona.pasaporte

                        estudiante=elimina_tildes(inscrito.persona.nombre_completo_inverso())
                        carrera=elimina_tildes(inscrito.carrera.nombre)
                        paralelo=inscrito.grupo().nombre
                        fechainscripcion=inscrito.fecha

                        try:
                            if inscrito.persona.telefono_conv:
                                telefono=inscrito.persona.telefono_conv.replace("-","")
                            else:
                                telefono=''
                        except Exception as ex:
                            pass

                        try:
                            if inscrito.persona.telefono:
                                celular=inscrito.persona.telefono.replace("-","")
                            else:
                                celular=''
                        except Exception as ex:
                            pass

                        try:
                            emailinst=inscrito.persona.emailinst
                        except:
                            emailinst=''

                        try:
                            email=inscrito.persona.email
                        except:
                            email=''
                        try:
                            convenio = elimina_tildes(inscrito.empresaconvenio.nombre)
                        except:
                            convenio = ''

                        ws.write(fila,0, convenio)
                        ws.write(fila,1, str(identificacion))
                        ws.write(fila,2, elimina_tildes(estudiante))
                        ws.write(fila,3, carrera)
                        ws.write(fila,4, paralelo)
                        ws.write(fila,5, telefono)
                        ws.write(fila,6, celular)
                        ws.write(fila,7, emailinst)
                        ws.write(fila,8, email)
                        ws.write(fila,9, str(fechainscripcion))

                        if inscrito.persona.cantonresid:
                            canton_residencia= Canton.objects.get(id=inscrito.persona.cantonresid.id)
                        else:
                            canton_residencia=''

                        if inscrito.persona.provinciaresid:
                            provincia_residencia= Provincia.objects.get(id=inscrito.persona.provinciaresid.id)
                        else:
                            provincia_residencia=''

                        if inscrito.persona.provincia:
                            provincia_nacimiento= Provincia.objects.get(id=inscrito.persona.provincia.id)
                        else:
                            provincia_nacimiento=''

                        if inscrito.persona.canton:
                            canton_nacimiento= Canton.objects.get(id=inscrito.persona.canton.id)
                        else:
                            canton_nacimiento=''

                        inscritopor=inscrito.user
                        if inscrito.user!=None:
                            if Persona.objects.filter(usuario=inscritopor).exists():
                                inscritopor=Persona.objects.filter(usuario=inscritopor)[:1].get()
                                inscritopor= inscritopor.nombre_completo_inverso()
                        else:
                            inscritopor=''

                        if inscrito.promocion:
                            promocion=inscrito.promocion.descripcion
                            descuento=inscrito.promocion.val_inscripcion
                        else:
                            promocion=''
                            descuento=0

                        if inscrito.descuentoporcent:
                            desc_cuotas=inscrito.descuentoporcent
                        else:
                            desc_cuotas=0

                        ws.write(fila,10,elimina_tildes(provincia_residencia))
                        ws.write(fila,11,elimina_tildes(canton_residencia))
                        ws.write(fila,12,elimina_tildes(provincia_nacimiento))
                        ws.write(fila,13,elimina_tildes(canton_nacimiento))
                        ws.write(fila,14,elimina_tildes(promocion))
                        ws.write(fila,15,elimina_tildes(descuento))
                        ws.write(fila,16,elimina_tildes(desc_cuotas))
                        ws.write(fila,17,elimina_tildes(inscritopor))
                        fila=fila + 1

                    detalle = detalle + fila
                    ws.write(detalle, 0, "Fecha Impresion", subtitulo)
                    ws.write(detalle, 1, str(datetime.now()), subtitulo)
                    detalle=detalle +1
                    ws.write(detalle, 0, "Usuario", subtitulo)
                    ws.write(detalle, 1, str(request.user), subtitulo)

                    nombre ='informacion'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(ex)
                    return HttpResponse(json.dumps({"result":str(ex)+str(inscrito)}),content_type="application/json")
        else:
            data = {'title': 'Informacion de Estudiantes por Convenios'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform']=ConveniosExcelForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
                return render(request ,"reportesexcel/estudiantesxconvenios.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

