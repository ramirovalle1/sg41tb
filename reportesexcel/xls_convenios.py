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
from settings import UTILIZA_GRUPOS_ALUMNOS, EMAIL_ACTIVE,MEDIA_ROOT, ASIG_VINCULACION, ASIG_PRATICA
from sga.commonviews import addUserData, ip_client_address
from sga.forms import ConveniosForm
from sga.models import ReporteExcel,TituloInstitucion,convertir_fecha,Convenio

from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action :
                try:
                    conv = None
                    anio = ''
                    convenios=None

                    if request.POST['anio']!='':
                        anio = request.POST['anio']
                        convenios = Convenio.objects.filter(inicio__year=anio).order_by('inicio','nombre')
                    else:
                        convenios = Convenio.objects.filter().order_by('nombre')
                    m = 10
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
                    if anio!='':
                        ws.write_merge(1, 1,0,m, 'LISTADO DE CONVENIOS POR ANIO',titulo2)
                        ws.write(3, 0,'Anio: ' +anio , subtitulo)
                    else:
                        ws.write_merge(1, 1,0,m, 'LISTADO DE CONVENIOS GENERAL',titulo2)

                    ws.write(5,0,"INSTITUCION",subtitulo)
                    ws.write(5,1,"OBJETIVO",subtitulo)
                    ws.write(5,2,"NACIONAL",subtitulo)
                    ws.write(5,3,"DESDE",subtitulo)
                    ws.write(5,4,"HASTA",subtitulo)
                    ws.write(5,5,"CONTACTO",subtitulo)
                    ws.write(5,6,"TELF. CONTACTO",subtitulo)
                    ws.write(5,7,"EMAIL CONTACTO",subtitulo)
                    ws.write(5,8,"PAIS",subtitulo)
                    ws.write(5,9,"CANTON",subtitulo)
                    ws.write(5,10,"PROLONGA",subtitulo)
                    ws.write(5,11,"ACTIVO",subtitulo)

                    fila = 6
                    com = 6
                    detalle = 3
                    for conv in convenios:
                        institucion=''
                        objetivo=''
                        nacional=''
                        desde=''
                        hasta=''
                        contacto=''
                        tlfcontacto=''
                        emailcontacto=''
                        pais=''
                        canton=''
                        prolonga=''
                        activo=''

                        try:
                            if conv.institucion:
                                institucion = elimina_tildes(conv.institucion)
                            else:
                                institucion = ''
                        except Exception as ex:
                            institucion = ''

                        try:
                            if conv.objetivo:
                                objetivo = elimina_tildes(conv.objetivo)
                            else:
                                objetivo = ''
                        except Exception as ex:
                            objetivo = ''

                        try:
                            if conv.nacional:
                                nacional = 'SI'
                            else:
                                nacional = 'NO'
                        except Exception as ex:
                            nacional = ''

                        try:
                            if conv.inicio:
                                desde = str(conv.inicio)
                            else:
                                desde = ''
                        except Exception as ex:
                            desde = ''

                        try:
                            if conv.fin:
                                hasta = str(conv.fin)
                            else:
                                hasta = ''
                        except Exception as ex:
                            hasta = ''

                        try:
                            if conv.contacto:
                                contacto = elimina_tildes(conv.contacto)
                            else:
                                contacto = ''
                        except Exception as ex:
                            contacto = ''

                        try:
                            if conv.contactofono:
                                tlfcontacto = elimina_tildes(conv.contactofono)
                            else:
                                tlfcontacto = ''
                        except Exception as ex:
                            tlfcontacto = ''

                        try:
                            if conv.contactoemail:
                                emailcontacto = elimina_tildes(conv.contactoemail)
                            else:
                                emailcontacto = ''
                        except Exception as ex:
                            emailcontacto = ''

                        try:
                            if conv.pais:
                                pais = elimina_tildes(conv.pais.nombre)
                            else:
                                pais = ''
                        except Exception as ex:
                            pais = ''

                        try:
                            if conv.canton:
                                canton = elimina_tildes(conv.canton.nombre)
                            else:
                                canton = ''
                        except Exception as ex:
                            canton = ''

                        try:
                            if conv.prolonga:
                                prolonga = elimina_tildes(conv.prolonga)
                            else:
                                prolonga = ''
                        except Exception as ex:
                            prolonga = ''

                        try:
                            if conv.activo:
                                activo = 'SI'
                            else:
                                activo = 'NO'
                        except Exception as ex:
                            activo = ''

                        ws.write(fila,0, institucion )
                        ws.write(fila,1,objetivo)
                        ws.write(fila,2, nacional)
                        ws.write(fila,3, desde)
                        ws.write(fila,4, hasta)
                        ws.write(fila,5, contacto)
                        ws.write(fila,6, tlfcontacto)
                        ws.write(fila,7, emailcontacto)
                        ws.write(fila,8, pais)
                        ws.write(fila,9, canton)
                        ws.write(fila,10, prolonga)
                        ws.write(fila,11, activo)
                        fila=fila+1

                    detalle = detalle + fila
                    ws.write(detalle,0, "Fecha Impresion", subtitulo)
                    ws.write(detalle,1, str(datetime.now()), subtitulo)
                    detalle=detalle+1
                    ws.write(detalle,0, "Usuario", subtitulo)
                    ws.write(detalle,1, str(request.user), subtitulo)

                    nombre ='convenios'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)+' '+ str(conv)}),content_type="application/json")

        else:
            data = {'title': 'Convenios por Anio'}
            addUserData(request,data)

            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform']=ConveniosForm()
                return render(request ,"reportesexcel/convenios.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

