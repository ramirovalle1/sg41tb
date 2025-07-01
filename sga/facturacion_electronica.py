from datetime import datetime
import os
import subprocess
from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
# from pyjasper import JasperGenerator
from requests import request
from decorators import secure_module
from settings import DATABASES, JR_DB_TYPE, JR_RUN, JR_JAVA_COMMAND, JR_USEROUTPUT_FOLDER, MEDIA_URL, FACTURACION_ELECTRONICA, FECHA_ELECT_FAC
from sga.commonviews import addUserData
from sga.dbf import elimina_tildes
from sga.facturacionelectronica import facturacionelectronicaeject, notacreditoelectronica
from sga.forms import ClaveFacturacionForm
from sga.models import ClienteFactura, Factura, NotaCreditoInstitucion, Inscripcion, Reporte, SesionCaja, ViewFacturaNotacredito
from sga.reportes import transform
import xml.etree.ElementTree as ET
from django.http import HttpResponse
import json
# from pyjasper.client_subreport import *

class MiPaginador(Paginator):
    def __init__(self, object_list, per_page, orphans=0, allow_empty_first_page=True, rango=5):
        super(MiPaginador,self).__init__(object_list, per_page, orphans=orphans, allow_empty_first_page=allow_empty_first_page)
        self.rango = rango
        self.paginas = []
        self.primera_pagina = False
        self.ultima_pagina = False

    def rangos_paginado(self, pagina):
        left = pagina - self.rango
        right = pagina + self.rango
        if left<1:
            left=1
        if right>self.num_pages:
            right = self.num_pages
        self.paginas = range(left, right+1)
        self.primera_pagina = True if left>1 else False
        self.ultima_pagina = True if right<self.num_pages else False
        self.ellipsis_izquierda = left-1
        self.ellipsis_derecha = right+1
@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    if request.method=='POST':
        action = request.POST['action']
        if action =='clave':
            pass

        return HttpResponseRedirect("/consultafactura")
    else:
        try:
            data = {'title': 'Consulta de Facturas Electronicas'}
            if 'action' in request.GET:
                action = request.GET['action']
                try:
                    listerroproved=''
                    if action == 'autorizar':
                         if FACTURACION_ELECTRONICA:
                             if DATABASES['default']['HOST'] == '10.10.9.45':
                                notacreditoelectronica()
                                facturacionelectronicaeject()
                         html='<h3>Documentos Autorizados.</h3>'
                         if listerroproved:
                            html= html +'<h5>Existen documentos sin autorizar.</h5>'
                         else:
                            html='Documentos Autorizados.'
                         return HttpResponse(json.dumps({'result':'ok','html':html}),content_type="application/json")

                except Exception as e:
                    print('Error excepcion autorizafact'+str(e))
                    return HttpResponse(json.dumps({'result':'bad','message':'Error en excepcion '+str(e)}),content_type="application/json")

            else:
                addUserData(request,data)
                try:
                    data['currenttime'] = datetime.now()
                    factura= False
                    notacredito= False

                    if ViewFacturaNotacredito.objects.filter(notacredito=False).exists():
                        factura=True
                    if ViewFacturaNotacredito.objects.filter(notacredito=True).exists():
                        notacredito=True
                    if 'g' in request.GET:
                        grupoid = request.GET['g']
                        if grupoid =='fac':
                            facturanotacredito = ViewFacturaNotacredito.objects.filter(notacredito=False).order_by('-fecha','-numero')
                            data['grupo']='fac'
                        if grupoid =='nota':
                            facturanotacredito = ViewFacturaNotacredito.objects.filter(notacredito=True).order_by('-fecha','-numero')
                            data['grupo']='nota'
                    elif 'sesion' in request.GET:
                        if request.GET['sesion'] != '':
                            sesion = request.GET['sesion']
                            data['sesionid'] = int(sesion) if sesion else ""
                            data['sesion'] = SesionCaja.objects.get(pk=sesion) if sesion else ""
                            data['tfacturas'] = ViewFacturaNotacredito.objects.filter(fecha=data['sesion'].fecha,sesionid=data['sesion'].caja.id,notacredito=False).count()
                            data['tfautorizada'] = ViewFacturaNotacredito.objects.filter(fecha=data['sesion'].fecha,estado='AUTORIZADO',sesionid=data['sesion'].caja.id,notacredito=False).count()
                            data['tfnovali'] = ViewFacturaNotacredito.objects.filter(fecha=data['sesion'].fecha,estado='NO ENVIADOVALI',sesionid=data['sesion'].caja.id,notacredito=False).count()
                            data['tfdevuelta'] = ViewFacturaNotacredito.objects.filter(fecha=data['sesion'].fecha,estado='DEVUELTA',sesionid=data['sesion'].caja.id,notacredito=False).count()
                            data['tfnoaut'] = ViewFacturaNotacredito.objects.filter(fecha=data['sesion'].fecha,estado='NO ENVIADOAUT',sesionid=data['sesion'].caja.id,notacredito=False).count()
                            data['tfnoenv'] = ViewFacturaNotacredito.objects.filter(fecha=data['sesion'].fecha,estado='',sesionid=data['sesion'].caja.id,notacredito=False).count()
                            data['tncredito'] = ViewFacturaNotacredito.objects.filter(sesionid=data['sesion'].id,notacredito=True).count()
                            data['tnnovali'] = ViewFacturaNotacredito.objects.filter(sesionid=data['sesion'].id,notacredito=True,estado='NO ENVIADOVALI').count()
                            data['tndevuelta'] = ViewFacturaNotacredito.objects.filter(sesionid=data['sesion'].id,notacredito=True,estado='DEVUELTA').count()
                            data['tnnoaut'] = ViewFacturaNotacredito.objects.filter(sesionid=data['sesion'].id,notacredito=True,estado='NO ENVIADOAUT').count()
                            data['tnautorizada'] = ViewFacturaNotacredito.objects.filter(sesionid=data['sesion'].id,notacredito=True,estado='AUTORIZADO').count()
                            data['tnnoenv'] = ViewFacturaNotacredito.objects.filter(sesionid=data['sesion'].id,notacredito=True,estado='').count()


                            facturanotacredito = ViewFacturaNotacredito.objects.filter(Q(fecha=data['sesion'].fecha,sesionid=data['sesion'].caja.id,notacredito=False)|Q(sesionid=data['sesion'].id,notacredito=True)).order_by('-fecha','-numero')
                    elif 'e' in request.GET:
                        estado = request.GET['e']
                        parametro = ''
                        if estado =='aut':
                            data['estado']='aut'
                            parametro = 'AUTORIZADO'
                        if estado =='noenv':
                            data['estado']='noenv'
                            parametro = 'NO ENVIADOVALI'
                        if estado =='dev':
                            data['estado']='dev'
                            parametro = 'DEVUELTA'
                        if estado =='noaut':
                            data['estado']='noaut'
                            parametro = 'NO ENVIADOAUT'

                        facturanotacredito = ViewFacturaNotacredito.objects.filter(estado=parametro).order_by('-fecha','-numero')

                    elif 's' in request.GET:
                        search = request.GET['s']
                        data['search'] = request.GET['s']
                        if search:
                            ss = search.split(' ')
                            while '' in ss:
                                ss.remove('')
                        facturanotacredito = ViewFacturaNotacredito.objects.filter(numero__icontains=search).order_by('-fecha','-numero')
                    else:
                        facturanotacredito = ViewFacturaNotacredito.objects.all().order_by('-fecha','-numero')

                    paging = MiPaginador(facturanotacredito, 30)
                    p = 1
                    try:
                        if 'page' in request.GET:
                            p = int(request.GET['page'])
                        page = paging.page(p)
                    except:
                        page = paging.page(p)

                    data['paging'] = paging
                    data['rangospaging'] = paging.rangos_paginado(p)
                    data['page'] = page



                    data['documento']=  page.object_list
                    data['factura']=factura
                    data['notacredi']=notacredito
                    data['fechaactual']=datetime.now()
                    # data['sesionescaja'] = SesionCaja.objects.all().order_by('-fecha')
                    return render(request ,"consultafactura/consultafacturas.html" ,  data)

                except Exception as ex:
                    return HttpResponseRedirect("/")

        except Exception as ex:
            return HttpResponseRedirect("/")



