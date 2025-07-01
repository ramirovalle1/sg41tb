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
from sga.models import ClienteFactura, Factura, NotaCreditoInstitucion, Inscripcion, Reporte, SesionCaja
from sga.pre_inscripciones import email_error_congreso
from sga.reportes import transform_jasperstarter
import xml.etree.ElementTree as ET
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
        try:
            data = {'title': 'Consulta de Facturas Electronicas'}
            action=''
            addUserData(request,data)
            if 'action' in request.GET:
                action=request.GET['action']
                if action=='run':
                    errores =[]
                    # Ejecutar Reporte
                    try:
                        if 'n' in request.GET:
                            reporte = Reporte.objects.get(nombre=request.GET['n'])
                        else:
                            reporte = Reporte.objects.get(pk=request.GET['rid'])
                        tipo = request.GET['rt']
                        persona = request.session['persona']
                        if not ClienteFactura.objects.filter(ruc=persona.cedula).exists():
                            # return HttpResponseRedirect("/")
                            cli = persona
                            output_folder = os.path.join(JR_USEROUTPUT_FOLDER,str(elimina_tildes(cli.usuario.username)).split(" ")[0])
                            nombres = cli.usuario.username
                        else:

                            try:
                                cli= ClienteFactura.objects.get(ruc=persona.cedula)
                            except Exception as e:
                                fact=Factura.objects.get(pk=request.GET['factura'])
                                cli=ClienteFactura.objects.get(id=fact.cliente.id)
                                errores.append(('CLIENTE FACTURA DUPLICADO',persona.cedula))
                            # if errores:
                            #     email_error_congreso(errores,'CLENTE FACTURA')
                            output_folder = os.path.join(JR_USEROUTPUT_FOLDER,str(elimina_tildes(cli.nombre)).split(" ")[0])
                            nombres = cli.nombre
                        try:
                            os.makedirs(output_folder)
                        except :
                            # return HttpResponse(json.dumps({'result':'bad'}),content_type="application/json")
                            pass

                        d = datetime.now()
                        pdfname = reporte.nombre+d.strftime('%Y%m%d_%H%M%S')

                        runjrcommand = [JR_JAVA_COMMAND,'-jar',
                                os.path.join(JR_RUN, 'jasperstarter.jar'),
                                 'pr', reporte.archivo.file.name,
                                 '--jdbc-dir', JR_RUN,
                                 '-f', tipo,
                                 '-t', 'postgres',
                                 '-H', DATABASES['default']['HOST'],
                                 '-n', DATABASES['default']['NAME'],
                                 '-u', DATABASES['default']['USER'],
                                 '-p', DATABASES['default']['PASSWORD'],
                                 '-o', output_folder + os.sep + pdfname]
                        parametros = reporte.parametros()
                        paramlist = [ transform_jasperstarter(p, request) for p in parametros ]
                        if paramlist:
                            runjrcommand.append('-P')
                            for parm in paramlist:
                                runjrcommand.append(parm)
                        try:
                            mensaje = ''
                            for m in runjrcommand:
                                mensaje += ' ' + m

                            runjr = subprocess.call(mensaje, shell=True)
                        except Exception as ex:
                            return HttpResponseRedirect("/")
                        sp = os.path.split(reporte.archivo.file.name)
                        if 'direct' in request.GET:
                            return HttpResponseRedirect("/".join([MEDIA_URL,'documentos','userreports',str(elimina_tildes(nombres)).split(" ")[0], pdfname+"."+tipo]))

                    # /////////////////////////////////////////////////////////////////////////////////
                    except Exception as ex:
                        return HttpResponseRedirect("/")
            else:
                data['currenttime'] = datetime.now()
                persona = request.session['persona']
                factura=''
                notacredito=''

                if persona.extranjero:

                    factura = Factura.objects.filter(cliente__ruc=persona.pasaporte,estado='AUTORIZADO',fecha__gte =FECHA_ELECT_FAC).order_by('-fecha').values('id','numero','fecha','estado','dirfactura','numautorizacion')
                    if NotaCreditoInstitucion.objects.filter(inscripcion__persona__pasaporte=persona.pasaporte,estado='AUTORIZADO').exists():
                        notacredito  =NotaCreditoInstitucion.objects.filter(inscripcion__persona__pasaporte=persona.pasaporte,estado='AUTORIZADO')
                else:
                    factura = Factura.objects.filter(cliente__ruc=persona.cedula,estado='AUTORIZADO',fecha__gte =FECHA_ELECT_FAC).order_by('-fecha').values('id','numero','fecha','estado','dirfactura','numautorizacion')
                    if NotaCreditoInstitucion.objects.filter(inscripcion__persona__cedula=persona.cedula,estado='AUTORIZADO').exists():
                        notacredito  =NotaCreditoInstitucion.objects.filter(inscripcion__persona__cedula=persona.cedula,estado='AUTORIZADO')

                lista=[]

                if 's' in request.GET:
                    search = request.GET['s']
                    data['search'] = request.GET['s']
                    if search:
                        ss = search.split(' ')
                        while '' in ss:
                            ss.remove('')
                    if Factura.objects.filter(Q(numero__icontains=search,cliente__ruc=persona.cedula,estado='AUTORIZADO',fecha__gte =FECHA_ELECT_FAC)).exists():
                        fact =Factura.objects.filter(Q(numero__icontains=search,cliente__ruc=persona.cedula,estado='AUTORIZADO',fecha__gte =FECHA_ELECT_FAC))
                        for fac in fact:
                            lista.append((fac,'FACTURA'))
                    if NotaCreditoInstitucion.objects.filter(Q(numero__icontains=search,inscripcion__persona__cedula=persona.cedula,estado='AUTORIZADO',fecha__gte =FECHA_ELECT_FAC)).exists():
                        nota =  NotaCreditoInstitucion.objects.filter(numero__icontains=search,inscripcion__persona__cedula=persona.cedula,fecha__gte =FECHA_ELECT_FAC,estado='AUTORIZADO').values('id','numero','fecha','estado','dirnotacredito','numautorizacion')

                        for no in nota:
                            lista.append((no,'NOTACREDITO'))
                elif 'g' in request.GET:
                    grupoid = request.GET['g']
                    if grupoid =='fac':
                        for f in factura:
                            lista.append((f,'FACTURA'))
                        data['grupo']='fac'
                    if grupoid =='nota':
                        for n in notacredito:
                            lista.append((n,'NOTACREDITO'))
                        data['grupo']='nota'
                else:
                    for f in factura:
                        lista.append((f,'FACTURA'))
                    for n in notacredito:
                        lista.append((n,'NOTACREDITO'))

                paging = MiPaginador(lista, 30)
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
                return render(request ,"consultafactura/alu_consultafacturas.html" ,  data)

        except Exception as ex:
            return HttpResponseRedirect("/")




