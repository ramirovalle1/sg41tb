import json
import string
from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import Count, Q
from django.db.models.aggregates import Sum
from django.forms.models import model_to_dict
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.encoding import force_str
import requests
from settings import MODELO_EVALUACION, EVALUACION_ITB, VALIDAR_ASISTENCIAS, SEXO_MASCULINO, SEXO_FEMENINO, GRUPO_USUARIOS_IMPRESION, TIPO_RETENCION_IVA, NOTA_PARA_APROBAR, TIPO_NC_ANULACION, TIPO_NC_DEVOLUCION,DEFAULT_PASSWORD,EMAIL_ACTIVE, CAJA_PACIFICO, FACTURACION_ELECTRONICA, TIPO_CUOTA_RUBRO

from sga import number_to_letter
from datetime import datetime, timedelta
from sga.commonviews import ip_client_address
from sga.facturacionelectronica import mail_errores_autorizacion

from sga.models import AsistenciaLeccion, Clase, Leccion, Aula, Turno, LeccionGrupo, EvaluacionITB, LugarRecaudacion, Factura, ClienteFactura, Pago, Rubro, Inscripcion, Nivel, Materia, MateriaAsignada, CodigoEvaluacion, LeccionGrupo, AsistenciaLeccion, ChequeProtestado, RubroNotaDebito, Matricula, total_matriculados, Profesor, Impresion, Asignatura, RecordAcademico, HistoricoRecordAcademico, AsignaturaMalla, PrecioMateria, AsignaturaNivelacionCarrera, FacturaCancelada, PagoRetencion, RolPerfilProfesor, NotaCreditoInstitucion,DetallePagoTutoria, SesionCaja, TipoNotaCredito, TipoOtroRubro, RubroOtro, Persona, CierreSesionCaja, RegistroExterno, RubroInscripcion, RubroMatricula, ViewGeneralwsdl, DetalleDescuento, Descuento
from sga.reportes import elimina_tildes
from decimal import Decimal


def fix_factura_str(obj, f):
    obj['fecha'] = f.fecha.strftime("%d-%m-%Y")
    obj['cliente'] = model_to_dict(ClienteFactura.objects.get(pk=obj['cliente']))
    formasdepago = [fix_formadepago_str(x) for x in obj['pagos']]
    pagos = [fix_pago_str(x) for x in obj['pagos']]
    obj['pagos'] = pagos
    obj['enletras'] = number_to_letter.enletras(obj['total'])
    obj['formasdepago'] = formasdepago
    return obj

def fix_formadepago_str(x):
    pago = Pago.objects.get(pk=x.id)
    return pago.nombre()

def fix_pago_str(x):
    pago = Pago.objects.get(pk=x.id)
    if pago.es_retencion():
        fp = 1
    else :
        fp = 0
    obj = model_to_dict(pago, exclude=['fecha', 'lugar', 'recibe','efectivo','id'])
    rubro = Rubro.objects.get(pk=obj['rubro'])
    obj['rubro'] = model_to_dict(rubro, exclude=['fecha','fechavence', 'cancelado','inscripcion','valor'])
    obj['rubro'].update({'nombre': rubro.nombre() , 'tipo': rubro.tipo(), 'alumno': rubro.inscripcion.persona.nombre_completo(),'fp':fp,'id':rubro.id})

    return obj

def convertir_fecha(s):
    return datetime.datetime(int(s[6:10]), int(s[3:5]), int(s[0:2])).date()


def representacion_factura_str(x):
    return fix_factura_str(model_to_dict(x,exclude='fecha'), x)
def abrir_caja():
    lugarRecaudacion=LugarRecaudacion.objects.filter(pk=CAJA_PACIFICO)[:1].get()
    if not SesionCaja.objects.filter(caja=lugarRecaudacion,fecha=datetime.now().date()).exists():
        sc = SesionCaja(caja=lugarRecaudacion, fecha=datetime.now(), hora=datetime.now().time(),
                        fondo=0,
                        facturaempieza=lugarRecaudacion.numerofact,
                        facturatermina=lugarRecaudacion.numerofact,
                        abierta=True)
        sc.save()
    else:
        if SesionCaja.objects.filter(caja=lugarRecaudacion,fecha=datetime.now().date(),abierta=True).exists():
            sc = SesionCaja.objects.filter(caja=lugarRecaudacion,fecha=datetime.now().date(),abierta=True)[:1].get()
        else:
            return False
    return  sc

def cerrar_caja(request):
    lugarRecaudacion=LugarRecaudacion.objects.filter(pk=CAJA_PACIFICO)[:1].get()
    if SesionCaja.objects.filter(caja=lugarRecaudacion,fecha=datetime.now().date(),abierta=True).exists():
        sc= SesionCaja.objects.filter(caja=lugarRecaudacion,fecha=datetime.now().date(),abierta=True)[:1].get()
        cs = CierreSesionCaja(sesion=sc,
                              enmonedas = (sc.total_sesion_pacifico()),
                              total = float(sc.total_sesion_pacifico()),
                              fecha=datetime.now(),
                              hora=datetime.now().time())
        cs.save()

        sc.facturatermina -= 1
        sc.abierta = False
        sc.save()
        return  cs
    return ''
@transaction.atomic()
def view (request):
    try:
        if request.method == 'POST':
            if 'a' in request.POST:
                action=request.POST['a']
                mensaje=''
                if action == 'abrircaja':
                    abrir_caja()

                elif action == 'consultageneral':
                    if ViewGeneralwsdl.objects.filter(documento=request.POST['documento']).exists():
                        registros = []
                        data = {}
                        for i in ViewGeneralwsdl.objects.filter(documento=request.POST['documento']).order_by('fechavence'):
                            valoradeuda = i.valorrubro - i.valor
                            if valoradeuda > 0:
                                valorpagar = 0
                                if i.referencia02 == "PRESENCIAL":
                                    rubro = Rubro.objects.get(id=i.rubro_id)
                                    valorpagar = rubro.aplicadescuento(None)[0]
                                elif i.referencia02 == "CONDUCCION":
                                    valorpagar = valoradeuda
                                elif i.referencia02 == "EDUCACONTINUA":
                                    valorpagar = valoradeuda
                                elif i.referencia02 == "SGAONLINE":
                                    try:
                                        datos = requests.post('https://sgaonline.itb.edu.ec/api',
                                                              {'a': 'descuentorubro','idrub': str(i.rubro_id)}, timeout=300,
                                                              verify=False)
                                        if datos.status_code == 200:
                                            datos = datos.json()
                                            if datos['result'] == 'ok':
                                                valorpagar = float(datos['adeuda'])
                                    except requests.Timeout:
                                        print("Error Timeout")
                                        pass
                                    except requests.ConnectionError:
                                        print("Error Conexion")
                                        pass


                                if valorpagar > 0:
                                    registros.append({'nombres': i.nombre, 'valorpagar': str(valorpagar),
                                                      'tipodocumentacion': i.tipodocumentacion,
                                                      'documento': i.documento, 'referencia01': i.nombrerubro,
                                                      'codigo': str(i.rubro_id),
                                                      'referencia02': i.referencia02})
                        if registros:
                            data['result'] = "ok"
                            data['codmensaje'] = "0001"
                            data['registros'] = registros
                            data['mensaje'] = "Proceso realizado con exito"
                            return HttpResponse(json.dumps(data),content_type="application/json")
                    return HttpResponse(
                        json.dumps({'result': "bad", 'mensaje': 'No existen datos', "codmensaje": "0047"}),
                       content_type="application/json")
                elif action=='pago':
                    sid = transaction.savepoint()
                    try:
                        cedula=request.POST['cedula']
                        cantidad=request.POST['cantrubr']
                        valortot = Decimal(request.POST['valpago'])
                        if not Inscripcion.objects.filter(persona__cedula=cedula).exclude(persona__cedula=None).exclude(persona__cedula='').exists():
                            if not Inscripcion.objects.filter(persona__pasaporte=cedula).exclude(persona__pasaporte=None).exclude(persona__pasaporte='').exists():
                                return HttpResponse(json.dumps({'result':"bad",'mensaje':'No existen datos' , "codmensaje":"0047"}),content_type="application/json")
                        rubronum= request.POST['rubrocod']
                        rubro = Rubro.objects.get(id=rubronum)
                        valor = request.POST['valpago']
                        secuencia = request.POST['numerotransaccion']

                        adeudado = rubro.adeudado()
                        if rubro.aplicadescuento(datetime.now().date())[1]:
                            valorfun,aplicanivcut,valdescuento,porcentajedescuento = rubro.calculadescuento([],datetime.now().date())
                            adeudado = (rubro.adeudado() - valdescuento)
                        if valortot > adeudado:
                            if rubro.cancelado:
                                return HttpResponse(json.dumps({'result':"bad", "codmensaje":"0025",'mensaje':'RUBRO CANCELADO'}),content_type="application/json")
                            else:
                                return HttpResponse(json.dumps({'result':"bad", "codmensaje":"0022",'mensaje':'EXCEDE EL VALOR DEL PAGO'}),content_type="application/json")
                        if rubro.inscripcion.rubros_pendientes().order_by('fechavence','id')[:1].get().fechavence < rubro.fechavence:
                            return HttpResponse(json.dumps({'result':"bad", "codmensaje":"0023",'mensaje':'EXISTEN RUBROS CON FECHA DE VENCIMIENTO INFERIOR'}),content_type="application/json")

                        if abrir_caja():
                            caja = abrir_caja()
                        else:
                            return HttpResponse(json.dumps({'result':"bad", "codmensaje":"0021",'mensaje':'CAJA CERRADA'}),content_type="application/json")

                        if  Pago.objects.filter(secuenciapago=secuencia,pacifico=True).exists():
                             transaction.savepoint_rollback(sid)
                             return HttpResponse(json.dumps({'result':"bad",'mensaje':'LA TRANSACCION TIENE ESTADO PAGADO, POR LO CUAL NO PUEDE SER PROCESADA.', "codmensaje":"9277"}),content_type="application/json")

                        recepcion = ''
                        dirfactur=''
                        mensajerecep=''
                        try:
                            cliente = ClienteFactura.objects.filter(ruc=rubro.inscripcion.persona.cedula)[:1].get()
                            cliente.nombre =rubro.inscripcion.persona.nombre_completo()
                            cliente.direccion =rubro.inscripcion.persona.direccion
                            cliente.telefono = rubro.inscripcion.persona.telefono
                            cliente.correo =rubro.inscripcion.persona.email
                            if cliente.contrasena == None:
                                cliente.contrasena = rubro.inscripcion.persona.cedula
                                cliente.numcambio = 0
                            cliente.save()
                        except :
                            cliente = ClienteFactura(ruc=rubro.inscripcion.persona.cedula, nombre=rubro.inscripcion.persona.nombre_completo(),
                                direccion=rubro.inscripcion.persona.direccion, telefono=rubro.inscripcion.persona.telefono,
                                correo=rubro.inscripcion.persona.email,contrasena=rubro.inscripcion.persona.cedula,numcambio=0)
                            cliente.save()

                        factura = Factura(numero = caja.caja.puntoventa.strip()+"-"+str(caja.caja.numerofact).zfill(9), fecha = datetime.now().date(),
                                                valida = True, cliente = cliente, hora = datetime.now().time(),
                                                subtotal = valortot, iva = 0, total = valortot,
                                                impresa=False, caja=caja.caja, estado = recepcion, mensaje = mensajerecep,dirfactura=dirfactur)
                        factura.save()
                        if  Pago.objects.filter(secuenciapago=secuencia,pacifico=True).exists():
                             transaction.savepoint_rollback(sid)
                             return HttpResponse(json.dumps({'result':"bad",'mensaje':'LA TRANSACCION TIENE ESTADO PAGADO, POR LO CUAL NO PUEDE SER PROCESADA.', "codmensaje":"9277"}),content_type="application/json")

                        if adeudado <= 0:
                            transaction.savepoint_rollback(sid)
                            return HttpResponse(json.dumps({'result':"bad", "codmensaje":"0025",'mensaje':'RUBRO CANCELADO'}), content_type="application/json")
                        monto = float(Decimal(valortot))
                        r = rubro
                        adeudado = r.adeudado()

                        detalle = None
                        if r.aplicadescuento(datetime.now().date())[1]:

                            valorfun,aplicanivcut,valdescuento,porcentajedescuento = r.calculadescuento([],datetime.now().date())
                            if float(monto) >= float(adeudado - valdescuento):
                                monto = monto - (r.adeudado() - valdescuento)
                                adeudado = (r.adeudado() - valdescuento)
                            else:
                                adeudado = monto
                            descripdeta = 'PROMOCION ' + str(porcentajedescuento) + ' DESCUENTO POR PAGO DE CUOTAS'
                            if round(float(valortot), 2)>= round(float(adeudado), 2):
                                if not DetalleDescuento.objects.filter(rubro =r).exists():
                                    desc = Descuento(inscripcion = r.inscripcion,
                                                              motivo =descripdeta,
                                                              total = valdescuento,
                                                              fecha = datetime.now())
                                    desc.save()
                                    detalle = DetalleDescuento(descuento =desc,
                                                                rubro =r,
                                                                valor = valdescuento,
                                                                porcentaje = porcentajedescuento)
                                    detalle.save()

                                    adeudado = r.adeudado()  - valdescuento
                                    r.valor = (r.valor - valdescuento)
                                    r.save()

                        pago2 = Pago(fecha=datetime.now().date(),
                                                recibe=caja.caja.persona,
                                                valor=valor,
                                                rubro=rubro,
                                                efectivo=False,
                                                wester=False,
                                                sesion=caja,
                                                electronico=False,
                                                facilito=False,
                                                pacifico=True,
                                                secuenciapago=secuencia)
                        pago2.save()
                        factura.pagos.add(pago2)
                        if detalle:
                            detalle.pago = pago2
                            detalle.save()
                        caja.facturatermina= int(caja.caja.numerofact)+1
                        caja.save()
                        if rubro.adeudado()==0:
                            rubro.cancelado = True
                            rubro.save()
                        if FACTURACION_ELECTRONICA or caja.caja.numerofact  != None:
                            for luga in LugarRecaudacion.objects.all():
                                if luga.puntoventa == caja.caja.puntoventa:
                                    luga.numerofact = int(caja.caja.numerofact)+1
                                    luga.save()
                        client_address = ip_client_address(request)

                        # Log de CREACION DE NOTA DE CREDITO INSTITUCIONAL
                        LogEntry.objects.log_action(
                            # user_id         = request.user.pk,
                            user_id         = caja.caja.persona.usuario.pk,
                            content_type_id = ContentType.objects.get_for_model(factura).pk,
                            object_id       = factura.id,
                            object_repr     = force_str(factura),
                            action_flag     = ADDITION,
                            change_message  = 'Adicionada Factura Red Pacifico '+  ' (' + client_address + ')' )
                        try:
                            if Factura.objects.filter(numero= factura.numero).count()>1:
                                mail_errores_autorizacion("FACTURA REPETIDA DESDE PAGO PACIFICO"+DEFAULT_PASSWORD,"Existe mas de una factura repetida verificar en factura",factura.numero)
                                transaction.savepoint_rollback(sid)
                                return HttpResponse(json.dumps({'result':"bad",'mensaje':'PROCESO NO REALIZADO' , "codmensaje":"0024"}),content_type="application/json")
                            transaction.savepoint_commit(sid)
                            factura.notificacion_pacifico(rubro)
                        except Exception as ex:
                            transaction.savepoint_rollback(sid)
                            return HttpResponse(json.dumps({'result':"bad",'mensaje':'ERROR EN API, EXCEPCION ' + str(ex), "codmensaje":"0020"}),content_type="application/json")
                        return HttpResponse(json.dumps({'result':"ok",'mensaje':'Proceso realizado con exito',"codmensaje":"0001",'idpago':str(pago2.id) }),content_type="application/json")

                    except Exception as e:
                        return HttpResponse(json.dumps({'result':"bad",'mensaje':'ERROR EN API, EXCEPCION ' + str(e), "codmensaje":"0020"}),content_type="application/json")

                elif action == 'anulacion':
                    cuenta =  request.POST['rubrocod']
                    sid = transaction.savepoint()
                    try:
                        rubro = Rubro.objects.filter(pk=cuenta)[:1].get()
                        cedula=request.POST['cedula']
                        if not Inscripcion.objects.filter(persona__cedula=cedula).exclude(persona__cedula=None).exclude(persona__cedula='').exists():
                            if not Inscripcion.objects.filter(persona__pasaporte=cedula).exclude(persona__pasaporte=None).exclude(persona__pasaporte='').exists():
                                return HttpResponse(json.dumps({'result':"bad",'mensaje':' No existen datos' , "codmensaje":"0047"}),content_type="application/json")
                        valor =  request.POST['valpago']
                        caja = abrir_caja()
                        lugar=caja.caja
                        dirnota = ''
                        recepcion = ''
                        mensajerecep = ''
                        tipo = TipoNotaCredito.objects.get(pk=TIPO_NC_ANULACION)
                        tiponcre = True
                        tiporu = None
                        codigo_aut = request.POST['idpago']
                        if Pago.objects.filter(pk=codigo_aut).exists():
                            pago = Pago.objects.filter(pk=codigo_aut)[:1].get()
                            factura=pago.factura_set.all()[:1].get()
                            if pago.fecha != datetime.now().date():
                                return HttpResponse(json.dumps({'result':"bad",'codmensaje':"0505",'mensaje':'EL REVERSO DEL PAGO SOLO PUEDE SER EL MISMO DIA '}),content_type="application/json")
                            if factura.nota_credito_devol():
                                return HttpResponse(json.dumps({'result':"bad",'codmensaje':"0027",'mensaje':'EL PAGO YA FUE REVERSADO'}),content_type="application/json")
                            if pago.valor != float(valor):
                                return HttpResponse(json.dumps({'result':"bad",'codmensaje':"9282",'mensaje':'ERROR AL PROCESAR EL REVERSO'}),content_type="application/json")

                            for luga in LugarRecaudacion.objects.all():
                                if luga.puntoventa == lugar.puntoventa:
                                    luga.numeronotacre=int(lugar.numeronotacre)+1
                                    luga.save()
                            numeronotacredito= lugar.puntoventa+'-'+str(caja.caja.numerofact).zfill(9)
                            nc = NotaCreditoInstitucion(inscripcion=rubro.inscripcion,
                                                        numero=numeronotacredito,
                                                        motivo='Anulacion Red Pacifico',
                                                        fecha=datetime.today().date(),
                                                        hora=datetime.now().time(),
                                                        valor=float(valor),
                                                        factura=factura,
                                                        sesioncaja=caja,
                                                        beneficiario=rubro.inscripcion,
                                                        usuario=caja.caja.persona.usuario,
                                                        estado = recepcion,
                                                        mensaje = mensajerecep,
                                                        dirnotacredito =dirnota,
                                                        cancelada =tiponcre,
                                                        tipo = tipo)
                            nc.save()
                            client_address = ip_client_address(request)

                            # Log de CREACION DE NOTA DE CREDITO INSTITUCIONAL
                            LogEntry.objects.log_action(
                                user_id         = caja.caja.persona.usuario.pk,
                                content_type_id = ContentType.objects.get_for_model(nc).pk,
                                object_id       = nc.id,
                                object_repr     = force_str(nc),
                                action_flag     = ADDITION,
                                change_message  = 'Adicionada Nota de Credito Red Pacifico- Tipo: '+ str(nc.tipo) + ' (' + client_address + ')' )

                            # invoice = representacion_factura_str1(factura)

                            invoice = representacion_factura_str(factura)
                            desc = 'NCA FAC- '
                            val = 0
                            for pagos in invoice['pagos']:
                                if pagos['rubro']['tipo'] != 'ESPECIE':
                                    desc = desc + pagos['rubro']['nombre']
                                    val = val +  pagos['valor']
                                    if TipoOtroRubro.objects.filter(nombre=pagos['rubro']['tipo']).exists():
                                        tiporu=TipoOtroRubro.objects.filter(nombre=pagos['rubro']['tipo'])[:1].get().id
                            if val :
                                r1 = Rubro( fecha = rubro.fecha,
                                            valor = val,
                                            inscripcion = rubro.inscripcion,
                                            cancelado = False,
                                            fechavence =rubro.fechavence)
                                r1.save()
                                if  not tiporu:
                                    tiporu = TIPO_CUOTA_RUBRO
                                r1otro = RubroOtro(rubro=r1,
                                                   tipo=TipoOtroRubro.objects.get(pk=tiporu),
                                                   descripcion=desc)
                                r1otro.save()
                            try:
                                transaction.savepoint_commit(sid)
                            except Exception as ex:
                                transaction.savepoint_rollback(sid)
                                return HttpResponse(json.dumps({'result':"bad",'codmensaje':"9282",'mensaje':'ERROR AL PROCESAR EL REVERSO'}),content_type="application/json")
                            return HttpResponse(json.dumps({'result':"ok",'codmensaje':"0001",'mensaje':'Proceso realizado con exito' }),content_type="application/json")
                        else:
                            transaction.savepoint_rollback(sid)
                            return HttpResponse(json.dumps({'result':"bad",'codmensaje':"0026",'mensaje':'EL PAGO NO ESTA REGISTRADO' }),content_type="application/json")
                    except Exception as e:
                        transaction.savepoint_rollback(sid)
                        return HttpResponse(json.dumps({'result':"bad",'codmensaje':"9282",'mensaje':'ERROR AL PROCESAR EL REVERSO' }),content_type="application/json")
                elif action == 'consulta_aux':
                    nombres=''
                    apellidos=''
                    identificacion=None
                    usuario = request.POST['usuario']
                    clave = request.POST['clave']
                    user = authenticate(username=string.lower(usuario), password=clave)
                    if user is not None:
                        if user.is_active:
                           if Persona.objects.filter(usuario=user).count()>0:
                                persona = Persona.objects.get(usuario=user)
                                login(request,user)
                                request.session['persona'] = persona
                                request.session['last_touch'] = datetime.now()
                        else:
                            return HttpResponse(json.dumps({'codigo':9,'mensaje':'Usuario Inactivo'}),content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({'codigo':10,'mensaje':'Credenciales Incorrectas'}),content_type="application/json")
                    if 'nombres' in request.POST:
                        nombres = request.POST['nombres']
                    if 'apellidos' in request.POST:
                        apellidos = request.POST['apellidos']
                    if 'identificacion' in request.POST:
                        identificacion = request.POST['identificacion']
                    inscripciones=''
                    data = []

                    if nombres:
                        inscripciones = Inscripcion.objects.filter(persona__nombres__icontains=nombres).order_by('persona__apellido1','persona__apellido2','persona__nombres')
                    if apellidos:
                        ap=apellidos.split(" ")
                        while '' in ap:
                            ap.remove('')
                        if len(ap)==1:

                            if inscripciones:
                                inscripciones = inscripciones.filter(Q(persona__apellido1__icontains=apellidos) | Q(persona__apellido2__icontains=apellidos)).order_by('persona__apellido1','persona__apellido2','persona__nombres')
                            else:
                                inscripciones = Inscripcion.objects.filter(Q(persona__apellido1__icontains=apellidos) | Q(persona__apellido2__icontains=apellidos)).order_by('persona__apellido1','persona__apellido2','persona__nombres')
                        else:
                            if inscripciones:
                                inscripciones = inscripciones.filter(Q(persona__apellido1=ap[0]) & Q(persona__apellido2__icontains=ap[1])).order_by('persona__apellido1','persona__apellido2','persona__nombres')
                            else:
                                inscripciones = Inscripcion.objects.filter(Q(persona__apellido1__icontains=ap[0])& Q(persona__apellido2__icontains=ap[1])).order_by('persona__apellido1','persona__apellido2','persona__nombres')
                    if identificacion:
                        inscripciones = Inscripcion.objects.filter(Q(persona__cedula=identificacion)|Q(persona__pasaporte=identificacion))
                    if inscripciones:
                        for i in inscripciones:
                            datos = []
                            if i.matricula():
                                datos.append(i.persona.cedula)
                                datos.append(i.persona.nombre_completo())
                                data.append(datos)
                        if data:
                            return HttpResponse(json.dumps({'codigo':0,'mensaje':'ok','registros':data}),content_type="application/json")
                        else:
                            return HttpResponse(json.dumps({'codigo':7,'mensaje':'No Esta matriculado'}),content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({'codigo':12,'mensaje':'No existen coincidencias'}),content_type="application/json")

                elif action == 'consulta_pagos':
                    data = []
                    usuario = request.POST['usuario']
                    clave = request.POST['clave']
                    fecha = request.POST['fecha']
                    try:
                        user = authenticate(username=string.lower(usuario), password=clave)
                        if user is not None:
                            if user.is_active:
                               if Persona.objects.filter(usuario=user).count()>0:
                                    persona = Persona.objects.get(usuario=user)
                                    login(request,user)
                                    request.session['persona'] = persona
                                    request.session['last_touch'] = datetime.now()
                               pagos = Pago.objects.filter(fecha=fecha,recibe__usuario=user)
                               if pagos:
                                    for p in pagos:
                                        fac = p.factura_set.all()[:1].get()
                                        if not fac.notacreditoinstitucion_set.filter().exists():
                                            datos = []
                                            datos.append(p.secuenciapago)
                                            datos.append(p.rubro.id)
                                            datos.append(p.valor)
                                            data.append(datos)
                                    return HttpResponse(json.dumps({'codigo':0,'mensaje':'ok','pagos':data}),content_type="application/json")
                               else:
                                    return HttpResponse(json.dumps({'codigo':8,'mensaje':'No existen Pagos'}),content_type="application/json")
                            else:
                                return HttpResponse(json.dumps({'codigo':9,'mensaje':'Usuario Inactivo'}),content_type="application/json")
                        else:
                            return HttpResponse(json.dumps({'codigo':10,'mensaje':'Credenciales Incorrectas'}),content_type="application/json")
                    except Exception as e:
                        return HttpResponse(json.dumps({'codigo':13,'mensaje':'Ocurrio un Error.. Intente Nuevamente '+str(e)}),content_type="application/json")
                elif action == 'consulta_cedula':
                    identificacion = request.POST['identificacion']
                    try:
                        if  RegistroExterno.objects.filter(identificacion=identificacion).exists():
                            re = RegistroExterno.objects.filter(identificacion=identificacion)[:1].get()
                            if re.rubro:
                                if re.rubro.cancelado:
                                    return HttpResponse(json.dumps({'mensaje':'1'}),content_type="application/json")
                                else:
                                    return HttpResponse(json.dumps({'mensaje':'0'}),content_type="application/json")
                            return HttpResponse(json.dumps({'mensaje':'No tiene rubro creado'}),content_type="application/json")
                        else:
                            return HttpResponse(json.dumps({'mensaje':'No esta registrado'}),content_type="application/json")
                    except Exception as e:
                        return HttpResponse(json.dumps({'mensaje':'Ocurrio un error'+str(e)}),content_type="application/json")
                elif action == 'facturar':
                    if 'a' in request.POST:
                        action =request.POST['a']
                        if action == 'facturar':
                            if request.POST['opcion'] == 'pedagogia':
                                try:
                                    d = json.loads(request.POST['datos'])
                                    tipo = d['tipodni']
                                    tipo = d['ci']
                                    tipo = d['sexo'].upper()
                                    tipo = d['codigo'].upper()
                                    tipo = d['nombre']
                                    tipo = d['paterno']
                                    tipo = d['materno']
                                    tipo = d['fecha']
                                    tipo = d['direccion']
                                    tipo = d['cell']
                                    tipo = d['telefono']
                                    tipo = d['email']
                                    tipo = d['discapacidad']
                                    tipo = d['fac_nombre']
                                    tipo = d['fac_direcion']
                                    tipo = d['telefono']
                                    tipo = d['fac_email']
                                    tipo = d['fac_ci']
                                    tipo = d['valor']
                                    tipo = d['trj_tipo']
                                    tipo = d['trj_nombre']
                                    tipo = d['trj_referencia']
                                    return HttpResponse(json.dumps({'codigo':1,'mensaje':'ok'}),content_type="application/json")
                                except Exception as e:
                                    return HttpResponse(json.dumps({'codigo':0,'mensaje':'Ocurrio un error' + str(e)}),content_type="application/json")


                elif action == 'consulta_cedula_congreso':
                    identificacion = request.POST['identificacion']
                    try:
                        data = []
                        inscripcion = None
                        if Inscripcion.objects.filter(persona__cedula=identificacion,inscripciongrupo__grupo__carrera__nombre='CONGRESO DE PEDAGOGIA').exists():
                            inscripcion = Inscripcion.objects.filter(persona__cedula=identificacion,inscripciongrupo__grupo__carrera__nombre='CONGRESO DE PEDAGOGIA')[:1].get()
                        else:
                            if Inscripcion.objects.filter(persona__pasaporte=identificacion,inscripciongrupo__grupo__carrera__nombre='CONGRESO DE PEDAGOGIA',persona__extranjero=True).exists():
                                inscripcion = Inscripcion.objects.filter(persona__pasaporte=identificacion,inscripciongrupo__grupo__carrera__nombre='CONGRESO DE PEDAGOGIA',persona__extranjero=True)[:1].get()
                        if inscripcion:

                            if RubroInscripcion.objects.filter(rubro__inscripcion=inscripcion).exists():
                                    nombre=''
                                    rubroins= RubroInscripcion.objects.filter(rubro__inscripcion=inscripcion)[:1].get()
                                    if rubroins.rubro.fecha.year == 2015:
                                        nombre= '1ER CONGRESO DE PEDAGOGIA'
                                    if rubroins.rubro.fecha.year == 2016:
                                        nombre= '2DO CONGRESO DE PEDAGOGIA'
                                    if rubroins.rubro.fecha.year == 2017:
                                        nombre= '3ER CONGRESO DE PEDAGOGIA'
                                    if rubroins.rubro.fecha.year == 2018:
                                        nombre= '4TO CONGRESO DE PEDAGOGIA'
                                    if rubroins.rubro.fecha.year == 2019:
                                        nombre= '5TO CONGRESO DE PEDAGOGIA'
                                    if not nombre:
                                        nombre = elimina_tildes(rubroins.rubro.nombre())
                                    if rubroins.rubro.cancelado:
                                        cancelado = 'PAGADO'
                                    else:
                                        cancelado = 'NO PAGADO'
                                    datos = []
                                    datos.append(nombre)
                                    datos.append(cancelado)
                                    data.append(datos)
                            for m in Matricula.objects.filter(inscripcion=inscripcion).order_by('id'):
                                if RubroMatricula.objects.filter(matricula=m).exists():
                                    datos = []
                                    matri = RubroMatricula.objects.filter(matricula=m)[:1].get()
                                    nombre = elimina_tildes(m.nivel.grupo.nombre)
                                    if matri.rubro.cancelado:
                                        cancelado = 'PAGADO'
                                    else:
                                        cancelado = 'NO PAGADO'
                                    datos.append(nombre)
                                    datos.append(cancelado)
                                    data.append(datos)
                            if data:
                                return HttpResponse(json.dumps({'mensaje':'ok','pagos':data}),content_type="application/json")
                            else:
                                return HttpResponse(json.dumps({'mensaje':'No existen pagos'}),content_type="application/json")
                        else:
                            return HttpResponse(json.dumps({'mensaje':'No existe insripcion'}),content_type="application/json")

                    except Exception as e:
                        return HttpResponse(json.dumps({'mensaje':'Ocurrio un error'+str(e)}),content_type="application/json")
        else:
            return HttpResponse(json.dumps({'codigo':2,'mensaje':'Error No viene por el post'}),content_type="application/json")
    except Exception as e:
        return HttpResponse(json.dumps({'codigo':2,'mensaje':'Error fin' + str(e)}),content_type="application/json")
