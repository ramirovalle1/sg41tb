from datetime import datetime,timedelta,time
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
from settings import MEDIA_ROOT
from sga.commonviews import addUserData
from sga.forms import InscritosProvinciaForm
from sga.models import convertir_fecha,TituloInstitucion,ReporteExcel,Provincia, Inscripcion
from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action :
                try:
                    provincia = Provincia.objects.get(pk=request.POST['provincia'])
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
                    ws.write_merge(0, 0,0,9, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,9, 'Listado de Alumnos Inscritos por Provincia', titulo2)
                    ws.write(4, 0,  'PROVINCIA: '+ elimina_tildes(provincia.nombre), subtitulo)

                    ws.write(8, 0,  'CEDULA', titulo)
                    ws.write(8, 1,  'NOMBRE', titulo)
                    ws.write(8, 2,  'CARRERA', titulo)
                    ws.write(8, 3,  'MODALIDAD', titulo)
                    ws.write(8, 4,  'GRUPO', titulo)
                    ws.write(8, 5,  'CELULAR', titulo)
                    ws.write(8, 6,  'CONVENCIONAL', titulo)
                    ws.write(8, 7,  'EMAIL PERSONAL', titulo)
                    ws.write(8, 8,  'EMAIL INSTITUCIONAL', titulo)
                    ws.write(8, 9,  'CANTON',titulo)

                    # inscripciones = Inscripcion.objects.filter(pk=80397,fecha__gte=fechai, fecha__lte=fechaf, persona__provincia=provincia,carrera__carrera=True).order_by('carrera__nombre', 'persona__apellido1', 'persona__apellido2')
                    # inscripciones = Inscripcion.objects.filter(fecha__gte=fechai, fecha__lte=fechaf, persona__provincia=provincia,carrera__carrera=True).order_by('carrera__nombre', 'persona__apellido1', 'persona__apellido2')
                    inscripciones = Inscripcion.objects.filter(persona__sectorresid__parroquia__canton__provincia=provincia,carrera__carrera=True).exclude(persona__sectorresid=None).order_by('carrera__nombre', 'persona__apellido1', 'persona__apellido2')
                    # print(inscripciones.count())
                    fila = 9
                    canton=''
                    modalidad=''
                    grupo=''
                    telefono=''
                    convencional=''
                    email=''
                    email2=''
                    for i in inscripciones:
                        # print((i))
                        if i.persona.cedula:
                            ws.write(fila, 0, elimina_tildes(i.persona.cedula))
                        else:
                            ws.write(fila, 0, elimina_tildes(i.persona.pasaporte))
                        ws.write(fila, 1, elimina_tildes(i.persona.nombre_completo_inverso()))
                        ws.write(fila, 2, elimina_tildes(i.carrera.nombre))
                        if i.modalidad:
                            ws.write(fila, 3, elimina_tildes(i.modalidad.nombre))
                        if i.grupo():
                            ws.write(fila, 4, elimina_tildes(i.grupo().nombre))
                        try:
                            if i.persona.telefono:
                                telefono = elimina_tildes(i.persona.telefono)
                        except Exception as e:
                            telefono=''
                            pass
                        ws.write(fila, 5, telefono)

                        try:
                            if i.persona.telefono_conv:
                                convencional = elimina_tildes(i.persona.telefono_conv)
                        except Exception as e:
                            convencional=''
                            pass
                        ws.write(fila, 6, convencional)

                        try:
                            if i.persona.email:
                                email=elimina_tildes(i.persona.email)
                        except Exception as e:
                            email=''
                            pass
                        ws.write(fila, 7, email)

                        try:
                            if i.persona.emailinst:
                                email2=elimina_tildes(i.persona.emailinst)
                        except Exception as e:
                            email2=''
                            pass
                        ws.write(fila,8, email2)

                        if i.persona.sectorresid.parroquia.canton:
                            canton=elimina_tildes(i.persona.sectorresid.parroquia.canton.nombre)
                        else:
                            canton=''
                        ws.write(fila, 9, canton)
                        fila = fila+1

                    fila=fila+1
                    ws.write(fila, 0, "Fecha Impresion", subtitulo)
                    ws.write(fila, 1, str(datetime.now()), subtitulo)
                    ws.write(fila+1, 0, "Usuario", subtitulo)
                    ws.write(fila+1, 1, str(request.user), subtitulo)

                    nombre ='inscripciones'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    return HttpResponse(json.dumps({"result":str(ex)+str(i)}),content_type="application/json")
        else:
                data = {'title': 'Alumnos Inscritos por Provincia'}
                addUserData(request,data)
                if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                    reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                    data['reportes'] = reportes
                    data['generarform']=InscritosProvinciaForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
                    return render(request ,"reportesexcel/xls_inscritos_xprovincia.html" ,  data)
                return HttpResponseRedirect("/reporteexcel")
    except Exception as e:
        print((e))
        return HttpResponseRedirect('/?info='+str(e))