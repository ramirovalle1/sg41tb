import json
import os
import xlrd
import xlwt
from datetime import datetime,timedelta
from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
import unicodedata
from django.utils.encoding import force_str
import psycopg2
from django.contrib.admin.models import LogEntry, ADDITION, DELETION, CHANGE
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models.query_utils import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template.context import RequestContext
from django.utils.encoding import force_str
from fpdf import FPDF
from decorators import secure_module
from settings import UTILIZA_FACTURACION_CON_FPDF, JR_USEROUTPUT_FOLDER, MEDIA_URL, POSICIONES_IMPRESION, FACTURACION_CON_IVA, CENTRO_EXTERNO, FACTURACION_ELECTRONICA, RUBRO_TIPO_CURSOS,TIPO_OTRO_RUBRO, TIPO_NC_ANULACION, TIPO_NC_DEVOLUCION,TIPO_CUOTA_RUBRO,COEFICIENTE_CALCULO_BASE_IMPONIBLE
from sga.commonviews import addUserData, ip_client_address
from sga.facturacionelectronica import notacreditoelectronica, facturacionelectronicaeject, representacion_factura_str1
from sga.finanzas import representacion_factura_str
# from sga.forms import FacturaCanceladaForm, NotaCreditoInstitucionForm, EditarFacturaForm, PagoNotaCreditodevoluForm, CabezNotaCreditoInstitucionForm, EditarTransferenciaForm,EditarTarjetaForm,EditarChequesForm
# from sga.inscripciones import MiPaginador
from sga.models import Factura, FacturaCancelada, NotaCreditoInstitucion, Inscripcion, LugarRecaudacion, ClienteFactura, Rubro, RubroOtro, TipoOtroRubro, TipoNotaCredito, DetalleNotacredDevol,PagoTransferenciaDeposito, PagoTarjeta, PagoCheque,ReporteExcel,GrupoReporteExcel, Reporte
from sga.reportes import elimina_tildes



@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    if 'action' in request.GET:
        action = request.GET['action']
        if action=='data':
            try:
                m = request.GET['model']
                if 'q' in request.GET:
                    q = request.GET['q'].upper()
                    if ':' in m:
                        sp = m.split(':')
                        model = eval(sp[0])
                        query = model.flexbox_query(q)
                        # query = eval('query.filter(%s)'%(sp[1]))
                        for n in range(1,len(sp)):                      # query = eval('query.filter(%s)'%(sp[1]))
                            query = eval('query.filter(%s)'%(sp[n]))    #query = query.filter(eval(sp[1].replace('[uid]',str(request.user.id)))).distinct()
                    else:
                        model = eval(request.GET['model'])
                        query = model.flexbox_query(q)
                else:
                    model = eval(request.GET['model'])
                    query = model.flexbox_query('')

                # data = {'results': [ {'id': x.id, 'name': x.flexbox_repr()} for x in query ]}
                data = {"results": [{"id": x.id, "name": x.flexbox_repr(), "alias": x.flexbox_alias() } for x in query]}
                return HttpResponse(json.dumps(data),content_type="application/json")

            except Exception as ex:
                return HttpResponse(json.dumps({'result':'bad' }),content_type="application/json")

        elif action=='run':
            try:

                if EMAIL_ACTIVE and 'correorol' in request.GET:
                    rolpago = RolPago.objects.filter(id=request.GET['rol_id'])[:1].get()
                    if request.GET['correorol'] == '1':
                        try:
                            # case server externo
                            client_address = request.META['HTTP_X_FORWARDED_FOR']
                        except:
                            # case localhost o 127.0.0.1
                            client_address = request.META['REMOTE_ADDR']
                        rolpago.ingreso_rolemail('Reporte de Rol de Pago Administrativo',request.user,client_address)
                    elif request.GET['correorol'] == '2':
                        try:
                            # case server externo
                            client_address = request.META['HTTP_X_FORWARDED_FOR']
                        except:
                            # case localhost o 127.0.0.1
                            client_address = request.META['REMOTE_ADDR']
                        rolpago.ingreso_rolemail('Reporte de Rol de Pago Docente',request.user,client_address)
                    elif request.GET['correorol'] == '3':
                        try:
                            # case server externo
                            client_address = request.META['HTTP_X_FORWARDED_FOR']
                        except:
                            # case localhost o 127.0.0.1
                            client_address = request.META['REMOTE_ADDR']
                        rolpago.ingreso_rolemail('Reporte de Rol de Pago Docentes Servicios Prestados',request.user,client_address)

                if 'n' in request.GET:
                    reporte = Reporte.objects.get(nombre=request.GET['n'])
                else:
                    reporte = Reporte.objects.get(pk=request.GET['rid'])
                tipo = request.GET['rt']
                output_folder = os.path.join(JR_USEROUTPUT_FOLDER, elimina_tildes(request.user.username)) #output_folder = os.path.join(JR_USEROUTPUT_FOLDER,request.user.username)
                try:
                    os.makedirs(output_folder)
                except :
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
                except:
                    return HttpResponse(json.dumps({'result': 'bad'}),content_type="application/json")

                sp = os.path.split(reporte.archivo.file.name)


                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de EDICION PROCESO
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(reporte).pk,
                    object_id       = reporte.id,
                    object_repr     = force_str(reporte),
                    action_flag     = ADDITION,
                    change_message  = 'Reporte Ejecutado (' + client_address + ')' )
                if tipo == 'xlsx':
                   pass

                if 'direct' in request.GET:
                    return HttpResponseRedirect('/'.join([MEDIA_URL,
                                                         'documentos',
                                                         'userreports',
                                                         elimina_tildes(request.user.username),
                                                         pdfname + '.' + tipo]))

                return HttpResponse(json.dumps({'result': 'ok',
                                        'reportfile': '/'.join([MEDIA_URL,
                                                                'documentos',
                                                                'userreports',
                                                                request.user.username,
                                                                pdfname + '.' + tipo])}),content_type="application/json")
            # ///////////////////////////////////////////////////////////////////////////////////////////////
            # /////////////////////////////////////////////////////////////////////////////////
            except :
                if 'direct' in request.GET:
                    return HttpResponseRedirect("/?error=3")
                return HttpResponse(json.dumps({'result':'bad'}),content_type="application/json")
                # pass


        return HttpResponseRedirect('/reportes')
    else:
        data = {'title': 'Reportes en Excel'}
        addUserData(request,data)

        categorias = []

        reportes = ReporteExcel.objects.filter(gruporeporteexcel__grupos__in=request.user.groups.all(),activo=True).order_by('descripcion')
        # reportes = ReporteExcel.objects.filter(activo=True).order_by('descripcion')

        data['reportes'] = reportes
        return render(request ,"reportesexcel/reportesbs.html" ,  data)