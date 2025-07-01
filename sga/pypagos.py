from datetime import datetime, timedelta
import json
from django.contrib.auth.decorators import login_required
from django.db.models.query_utils import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
import xlrd
from decorators import secure_module
from settings import  MEDIA_ROOT
from sga.carrera_admi import MiPaginador
from sga.commonviews import addUserData
from sga.forms import PymentezForm, PagoPyForms
from sga.models import PagoPymentez, Inscripcion, HistoriaArchivoPymentez, Factura, TipoIncidencia
from sga.commonviews import addUserData, ip_client_address
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_str
from django.template import RequestContext
from sga.api import factura_online
from sga.tasks import send_html_mail
from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
@secure_module

def view(request):
    """
    :param request:
    :return:
    """
    if request.method=='POST':
        action = request.POST['action']
        if action=='anular':
            try:
                if PagoPymentez.objects.filter(pk=request.POST['tid']).exists():
                    pago =  PagoPymentez.objects.filter(pk=request.POST['tid'])[:1].get()
                    import requests

                    import time
                    # import OpenSSL

                    import hashlib
                    from base64 import b64encode
                    paymentez_server_application_code = 'ITB-EC-SERVER'
                    paymentez_server_app_key = '3jnXITEpaAtTxJhufMKgonlsu8qRXW'
                    unix_timestamp = str(int(time.time()))
                    uniq_token_string = paymentez_server_app_key + unix_timestamp
                    uniq_token_hash = hashlib.sha256(uniq_token_string).hexdigest()
                    auth_token = b64encode('%s;%s;%s' % (paymentez_server_application_code,
                    unix_timestamp, uniq_token_hash))
                    from getpass import getpass
                    # Definimos la URL
                    # url = "https://ccapi-stg.paymentez.com/v2/transaction/refund/"
                    url = "https://ccapi.paymentez.com/v2/transaction/refund/"
                    # Solicitamos los datos del usuario

                    # Definimos la cabecera y el diccionario con los datos
                    cabecera1 = {'Content-type': 'application/json','Auth-Token': auth_token}
                    datos={}
                    datos['transaction'] = {"id":pago.idref }

                    response = requests.post(url, data=json.dumps(datos),headers={"Content-Type": "application/json",'Auth-Token': auth_token})
                    respuesta = response.json()
                    print(respuesta)
                    estado =respuesta['status']
                    detalle =respuesta['detail']
                    # estado='success'
                    # detalle='detalle'
                    if estado == 'success':
                        pago.motivo = request.POST['motivo']
                        pago.usuarioanula = request.user
                        pago.detalle =detalle
                        pago.anulado=True
                        pago.fechaanula = datetime.now()
                        pago.save()
                          # Log de ADICIONAR GRADUADO
                        client_address = ip_client_address(request)
                        # Log de ADICIONAR GRADUADO
                        LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(pago).pk,
                        object_id       = pago.id,
                        object_repr     = force_str(pago),
                        action_flag     = ADDITION,
                        change_message  = 'Anulado Pago en Linea (' + client_address + ')' )
                        return HttpResponse(json.dumps({"result":"ok","estado":estado,'detalle':detalle}),content_type="application/json")
                    return HttpResponse(json.dumps({"result":"bad2","estado":estado,'detalle':detalle}),content_type="application/json")
            except Exception as ex:
               return HttpResponse(json.dumps({"result":"bad","error":"excepcion"+str(ex)}),content_type="application/json")

        elif action =='existefact':
            p=PagoPyForms(request.POST)
            if p.is_valid():
                try:
                    if PagoPymentez.objects.filter(factura_id=p.cleaned_data['factura']).exists():
                        return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
            else:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

        elif action=='editar':
            p=PagoPyForms(request.POST)
            if p.is_valid():
                try:
                    if request.POST['idpagopy']=='':
                        idpagopy=0
                    else:
                        idpagopy=request.POST['idpagopy']
                    if PagoPymentez.objects.filter(pk=idpagopy).exists():
                        edit = PagoPymentez.objects.get(pk=idpagopy)
                        factura=None
                        # if Factura.objects.filter(pk=p.cleaned_data['factura']).exists():
                        #     factura= Factura.objects.filter(pk=p.cleaned_data['factura'])[:1].get()
                        # edit.inscripcion=p.cleaned_data['inscripicion']
                        edit.estado = p.cleaned_data['estado']
                        edit.idref=p.cleaned_data['idref']
                        edit.codigo_aut = p.cleaned_data['codigo_aut']
                        edit.mensaje = p.cleaned_data['mensaje']
                        edit.factura = factura

                        edit.monto = p.cleaned_data['monto']
                        edit.referencia_dev = p.cleaned_data['referencia_dev']

                        edit.detalle_estado = p.cleaned_data['detalle_estado']
                        edit.referencia_tran = p.cleaned_data['referencia_tran']
                        edit.tipo = p.cleaned_data['tipo']
                        edit.rubros = p.cleaned_data['rubros']
                        edit.correo = p.cleaned_data['correo']
                        edit.nombre = p.cleaned_data['nombre']
                        edit.direccion = p.cleaned_data['direccion']
                        edit.ruc = p.cleaned_data['ruc']
                        edit.telefono = p.cleaned_data['telefono']
                        edit.motivo = p.cleaned_data['motivo']
                        edit.detalle = p.cleaned_data['detalle']

                        edit.lote = p.cleaned_data['lote']
                        mensaje = 'Edicion de Pago'
                        edit.save()
                        if p.cleaned_data['factura']=='':
                            edit.factura= factura
                            edit.save()
                        else:
                            if Factura.objects.filter(pk=int(p.cleaned_data['factura'])).exists():
                                factura = Factura.objects.filter(pk=p.cleaned_data['factura'])[:1].get()
                                edit.factura = factura
                                edit.save()
                        # Log de Editar Pago Paymentez
                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(edit).pk,
                        object_id       = edit.id,
                        object_repr     = force_str(edit),
                        action_flag     = CHANGE,
                        change_message  = mensaje+' (' + client_address + ')' )
                        return HttpResponseRedirect("/pypagos")
                except Exception as e:
                    return HttpResponseRedirect("/pypagos?error="+str(e))
            else:
                return HttpResponseRedirect("/pypagos?error=Error en el formulario")

        elif action =='addarchivo':
            registro=None
            cont = 0
            try:
                if 'archivo' in request.FILES:
                    archivo = request.FILES['archivo']
                    registro= HistoriaArchivoPymentez(
                                usuario = request.user,
                                archivo = archivo,
                                fecha = datetime.now())

                    registro.save()
                    book = xlrd.open_workbook(MEDIA_ROOT + '/'+ str(registro.archivo))
                    sh = book.sheet_by_index(0)
                    c=0
                    ca=0
                    l=0
                    for rw in range(sh.nrows):
                         filaex = sh.row(rw)
                         if int(rw)==0:
                               for f in filaex:
                                   if 'lote' in f.value:
                                       l=c
                                   # OCastillo 01-12-2022 se cambio numero de autorizacion por este campo porque la data del dashboard viene
                                    # sin el 0 a la izquierda y la comparacion falla
                                   if 'carrier_tr_id' in f.value:
                                       ca=c
                                   c=c+1
                         elif int(rw)>0:#  Pasa el Excel a una tabla
                               cedula=''
                               # if filaex[2].value == '116':
                               if str(filaex[ca].value) != '':
                                   if PagoPymentez.objects.filter(idref=str(filaex[ca].value)).exists():
                                       pagopy = PagoPymentez.objects.filter(idref=str(filaex[ca].value))[:1].get()
                                       if filaex[l].value != '':
                                            pagopy.lote =  str(int(filaex[l].value))
                                            pagopy.save()
                                            cont = cont + 1
                                            client_address = ip_client_address(request)
                                        # Log de ADICIONAR GRADUADO
                                            LogEntry.objects.log_action(
                                            user_id         = request.user.pk,
                                            content_type_id = ContentType.objects.get_for_model(pagopy).pk,
                                            object_id       = pagopy.id,
                                            object_repr     = force_str(pagopy),
                                            action_flag     = ADDITION,
                                            change_message  = 'Actualizado Lote (' + client_address + ')' + 'Codigo Aut: ' + str(pagopy.codigo_aut) + " Lote: " + str(pagopy.lote))
                    return HttpResponse(json.dumps({"result":"ok" ,"cont":cont}),content_type="application/json")
            except Exception as e:
                if registro:
                    registro.delete()
                return HttpResponse(json.dumps({"result":"bad","error":str(e)}),content_type="application/json")


        elif action == 'actualizar_pendientes':
            try:
                pagos = PagoPymentez.objects.filter(factura=None, estado='success', detalle_estado=3).order_by('id').exclude(anulado=True)
                dataerror = []
                done = []
                deuda_del_grupo=[]
                realizado=0
                for pago in pagos:
                    act = factura_online(request)
                    if act is None:
                        realizado=realizado+1
                    else:
                        dataerror.append((' Estudiante: '+(elimina_tildes(pago.inscripcion.persona.nombre_completo_inverso())),' id: ' + str(pago.id)))
                if len(dataerror)>0:
                    tipo = TipoIncidencia.objects.filter(pk=67)[:1].get()
                    op=''
                    send_html_mail("SE ENCONTRARON ERRORES",
                                   "emails/error_pagoonlinecongreso.html",
                                   {'contenido': "ERRORES EN ACTUALIZACIÓN DE PAGOS EN LINEA", 'errores': dataerror,'op': op}, tipo.correo.split(","))
                return HttpResponse(json.dumps({"result":"ok",'realizados':str(realizado), 'norealizados':str(len(dataerror))}), content_type="application/json")
            except Exception as ex:
                print("ERROR: "+str(ex))
                return HttpResponse(json.dumps({"result":"bad", "msg":str(ex)}), content_type="application/json")

        return HttpResponseRedirect("/pypagos")



    else:
        data = {'title': 'Pagos Pymentez'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
        else:
            # horatran = PagoPymentez.objects.filter(estado='').order_by('-id')[:1].get().fechatransaccion
            hoy = datetime.now() - timedelta(1)

            # pagos = PagoPymentez.objects.filter(estado='',fechatransaccion__lte = hoy)
            # pagos.delete()


            search = None
            pagopy = None
            if 's' in request.GET:
                search = request.GET['s']
                try:
                    search=int(search)
                    pagopy = PagoPymentez.objects.filter(Q(id=search)|Q(inscripcion__persona__cedula__icontains=search)|Q(codigo_aut__icontains=str(search))).order_by('-id')
                except Exception as e:
                    data['search'] = search
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')
                    if len(ss)==1:
                            pagopy = PagoPymentez.objects.filter(Q(inscripcion__persona__nombres__icontains=search) | Q(inscripcion__persona__apellido1__icontains=search) | Q(inscripcion__persona__apellido2__icontains=search) | Q(inscripcion__persona__cedula__icontains=search) | Q(inscripcion__persona__pasaporte__icontains=search)| Q(codigo_aut__icontains=search)| Q(codigo_aut__icontains=search)| Q(idref__icontains=search)).order_by('-id')
                    else:
                            pagopy = PagoPymentez.objects.filter(Q(inscripcion__persona__apellido1__icontains=ss[0]) & Q(inscripcion__persona__apellido2__icontains=ss[1])| Q(codigo_aut__icontains=search)| Q(idref__icontains=search)).order_by('-id')
            # if search:
                    # pagopy = PagoPymentez.objects.filter(Q(idref=search)|Q()).order_by('-estado','-fechatransaccion','inscripcion__persona__apellido1', 'inscripcion__persona__apellido2', 'inscripcion__persona__nombres')

            elif 'p' in request.GET:
                pagopy = PagoPymentez.objects.filter(factura=None, estado='success', detalle_estado=3).order_by('-id')
                if len(pagopy)>0:
                    data['pendientes'] = True
            elif 'id' in request.GET:
                pagopy = PagoPymentez.objects.filter(id__in=str(request.GET['id']).split(','))
            else:
                pagopy = PagoPymentez.objects.filter().order_by('-id','-estado','-fechatransaccion', 'inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')


            paging = MiPaginador(pagopy, 30)
            p = 1
            try:
                if 'page' in request.GET:
                    p = int(request.GET['page'])
                    # if band==0:
                    #     inscripciones = Inscripcion.objects.all().order_by('persona__apellido1')
                    paging = MiPaginador(pagopy, 30)
                page = paging.page(p)
            except Exception as ex:
                page = paging.page(1)
            data['paging'] = paging
            data['rangospaging'] = paging.rangos_paginado(p)
            data['page'] = page
            data['pagopy'] = page.object_list
            data['usuario'] = request.user
            data['form'] = PymentezForm()
            data['formedit'] = PagoPyForms()
            return render(request ,"pypagos/registros.html" ,  data)
