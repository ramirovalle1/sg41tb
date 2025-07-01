from datetime import datetime
import os
import subprocess
from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
# from pyjasper import JasperGenerator
from requests import request
from settings import DATABASES, JR_DB_TYPE, JR_RUN, JR_JAVA_COMMAND, JR_USEROUTPUT_FOLDER, MEDIA_URL
from sga.commonviews import addUserData
from sga.dbf import elimina_tildes
from sga.forms import ClaveFacturacionForm
from sga.models import ClienteFactura, Factura, NotaCreditoInstitucion, Inscripcion, Reporte
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
def view(request):
    if request.method=='POST':
        action = request.POST['action']
        if action =='clave':
            try:
                f = ClaveFacturacionForm(request.POST)
                if f.is_valid():
                    for cli in  ClienteFactura.objects.filter(ruc=request.POST['ced']):
                    # if ClienteFactura.objects.filter(id=request.POST['ced']).exists():
                    #     cli=ClienteFactura.objects.get(id=request.POST['ced'])
                        # if f.cleaned_data['nueva']!=cli.contrasena:
                        # Log de CAMBIO DE CLAVE
                        cli.contrasena = f.cleaned_data['nueva']
                        if cli.numcambio == None:
                            cli.numcambio=1
                        else:
                            cli.numcambio = cli.numcambio+1
                        cli.save()

                        # else:
                        #     return HttpResponseRedirect("/consultafactura?action=clave&ced="+str(cli.ruc)+"error=ERROR CAMBIAR CLAVE")
                    else:
                        return HttpResponseRedirect("/consultafactura")
                return HttpResponseRedirect("/consultafactura")
            except Exception as ex:
                return HttpResponseRedirect("/consultafactura")

        return HttpResponseRedirect("/consultafactura")
    else:
        try:
            data = {'title': 'Consulta de Finanzas'}
            action=''
            if 'action' in request.GET:
                action = request.GET['action']
                if action=='clave':
                    error=''
                    data['form']= ClaveFacturacionForm()
                    cli = ClienteFactura.objects.filter(ruc=request.GET['ced']).exclude(contrasena=None)[:1].get()
                    data['cli'] = cli
                    data['nombfac']=cli
                    data['currenttime'] = datetime.now()
                    return render(request ,"consultafactura/clavefactura.html" ,  data)
                elif action=='run':
                    # Ejecutar Reporte
                    try:
                        errores =[]
                        if 'n' in request.GET:
                            reporte = Reporte.objects.get(nombre=request.GET['n'])
                        else:
                            reporte = Reporte.objects.get(pk=request.GET['rid'])
                        tipo = request.GET['rt']
                        cedula = request.session['usuario']
                        if not ClienteFactura.objects.filter(ruc=cedula).exists():
                            return HttpResponseRedirect("/")
                        try:
                            cli= ClienteFactura.objects.get(ruc=cedula)
                        except Exception as e:
                            fact=Factura.objects.get(pk=request.GET['factura'])
                            cli=ClienteFactura.objects.get(id=fact.cliente.id)
                            errores.append(('CLIENTE FACTURA DUPLICADO',cedula))
                        # if errores:
                        #     email_error_congreso(errores,'CLENTE FACTURA')

                        output_folder = os.path.join(JR_USEROUTPUT_FOLDER,str(elimina_tildes(cli.nombre)).split(" ")[0])
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
                            return HttpResponseRedirect("/".join([MEDIA_URL,'documentos','userreports',str(elimina_tildes(cli.nombre)).split(" ")[0], pdfname+"."+tipo]))

                    # /////////////////////////////////////////////////////////////////////////////////
                    except Exception as ex:
                        return HttpResponseRedirect("/")


            else:

                if 'usuario' in request.session :
                    cedula = request.session['usuario']
                    if not ClienteFactura.objects.filter(ruc=cedula).exists():
                        return HttpResponseRedirect("/")
                    data['currenttime'] = datetime.now()
                    cli = ClienteFactura.objects.filter(ruc=cedula).exclude(contrasena=None)[:1].get()
                    if ClienteFactura.objects.filter(ruc=cedula,numcambio=0).exists():
                    # if cli.numcambio < 1:
                        return HttpResponseRedirect("/consultafactura?action=clave&ced="+str(request.session['usuario']))
                    data['cli'] = ClienteFactura.objects.filter(ruc=cedula).exclude(contrasena=None)[:1].get()
                    factura=''
                    notacredito=''
                    inscripcion=None
                    if Factura.objects.filter(cliente__ruc= cli.ruc,estado='AUTORIZADO').exists():
                        factura = Factura.objects.filter(cliente__ruc= cli.ruc,estado='AUTORIZADO').exclude((Q(dirfactura=None)|Q(dirfactura=''))).values('id','numero','fecha','dirfactura','numautorizacion')
                        # factura = Factura.objects.filter(cliente= cli.id,estado='AUTORIZADO').exclude((Q(dirfactura=None)|Q(dirfactura=''))).values('id','numero','fecha','dirfactura','numautorizacion')
                    if Inscripcion.objects.filter(persona__cedula=cli.ruc).exists():
                        inscripcion=Inscripcion.objects.filter(persona__cedula=cli.ruc).order_by('id').distinct('id').values('id')
                    if inscripcion:
                        if NotaCreditoInstitucion.objects.filter(inscripcion__id__in=inscripcion,estado='AUTORIZADO').exists():
                           notacredito  = NotaCreditoInstitucion.objects.filter(inscripcion__id__in=inscripcion,estado='AUTORIZADO').exclude((Q(dirnotacredito=None)|Q(dirnotacredito='')))
                        else:
                            if NotaCreditoInstitucion.objects.filter(inscripcion__id__in=inscripcion,estado='AUTORIZADO').exists():
                                notacredito = NotaCreditoInstitucion.objects.filter(inscripcion__id__in=inscripcion,estado='AUTORIZADO').exclude((Q(dirnotacredito=None)|Q(dirnotacredito='')))
                    lista=[]

                    if 'g' in request.GET:
                        grupoid = request.GET['g']
                        if grupoid =='fac':
                            for f in factura:
                                lista.append((f,'FACTURA'))
                            data['grupo']='fac'
                        if grupoid =='nota':
                            for n in notacredito:
                                lista.append((n,'NOTACREDITO'))
                            data['grupo']='nota'
                    elif 's' in request.GET:
                        search = request.GET['s']
                        data['search'] = request.GET['s']
                        if search:
                            ss = search.split(' ')
                            while '' in ss:
                                ss.remove('')
                        if Factura.objects.filter(Q(numero__icontains=search)).exists():
                            fact= Factura.objects.filter(numero__icontains=search,cliente__ruc= cli.ruc,estado='AUTORIZADO').exclude((Q(dirfactura=None)|Q(dirfactura=''))).values('id','numero','fecha','dirfactura','numautorizacion')
                            for fac in fact:
                                lista.append((fac,'FACTURA'))
                        if NotaCreditoInstitucion.objects.filter(Q(numero__icontains=search)).exists():
                            if NotaCreditoInstitucion.objects.filter(numero__icontains=search,inscripcion=Inscripcion.objects.filter(persona__pasaporte=cli.ruc),estado='AUTORIZADO').exclude((Q(dirnotacredito=None)|Q(dirnotacredito=''))).exists():
                                nota = NotaCreditoInstitucion.objects.filter(numero__icontains=search,inscripcion=Inscripcion.objects.filter(persona__pasaporte=cli.ruc),estado='AUTORIZADO').exclude((Q(dirnotacredito=None)|Q(dirnotacredito='')))
                            else:
                                nota = NotaCreditoInstitucion.objects.filter(numero__icontains=search,inscripcion=Inscripcion.objects.filter(persona__cedula=cli.ruc),estado='AUTORIZADO').exclude((Q(dirnotacredito=None)|Q(dirnotacredito='')))
                            for no in nota:
                                lista.append((no,'NOTACREDITO'))

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
                    data['nombfac']=cli
                    data['factura']=factura
                    data['notacredi']=notacredito
                    data['extra'] = 1
                    return render(request ,"consultafactura/consultafactura.html" ,  data)
                else:
                    return HttpResponseRedirect("/")
        except Exception as ex:
            return HttpResponseRedirect("/")





