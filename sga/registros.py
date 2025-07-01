from datetime import datetime, timedelta, time
from itertools import chain
import json
import decimal
from django.contrib.admin.models import ADDITION, LogEntry, CHANGE

from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator

from django.db import transaction
from django.db.models import Sum, Max
from django.db.models.query_utils import Q

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render

from django.template import RequestContext
from django.utils.encoding import force_str
import psycopg2

from decorators import secure_module
from reportesexcel.compromisopagos_xfechas import ejecutar
from reportesexcel.xls_gestorescategoria import ejecutar_inscripcioncategoria
from settings import CENTRO_EXTERNO,  DEFAULT_PASSWORD, \
    UTILIZA_GRUPOS_ALUMNOS, REPORTE_CERTIFICADO_INSCRIPCION, \
    MODELO_EVALUACION, \
    UTILIZA_FICHA_MEDICA,\
    EVALUACION_TES,INSCRIPCION_CONDUCCION,\
    CARRERAS_ID_EXCLUIDAS_INEC, EMAIL_ACTIVE, INCIDENCIA_CAB, INCIDENCIA_COBRANZAS, SITE_ROOT, MEDIA_ROOT, ID_TIPO_ESPECIE_CONVENIO_PAGO
# from sga.api import exportacion_comision

from sga.commonviews import addUserData, ip_client_address
from sga.forms import DescuentoGestionForm, RespuestaForm, GestorForm,EntregaUniformeExcelForm
from sga.funciones import MiPaginador
from sga.models import Inscripcion, RecordAcademico, DocumentosDeInscripcion, HistoricoRecordAcademico, HistoriaNivelesDeInscripcion, \
    Grupo, \
    Rubro, \
    Sexo,\
    AtencionCliente, OpcionRespuesta, OpcionEstadoLlamada, EstadoLlamada,  RegistroSeguimiento, LlamadaUsuario, TipoRespuesta,CitaLlamada, AsistAsuntoEstudiant, RubroSeguimiento, \
    convertir_fecha, DescuentoSeguimiento, CategoriaRubro, TipoIncidencia, NacionalidadDataBooks, EstadoCivilDataBooks, ProfesionDataBooks, DivisionDataBooks, ActividadDataBooks,\
    TipoPersonaDataBooks,DemograficoDataBooks,RelacionDependenciaDataBooks,RelacionInDependenciaDataBooks,MediosContactoDataBooks,EmpleadorDataBooks,MediosDataBooks, Persona, RetiradoMatricula, Pago, HistoricoRubroSeguimiento, RubroEspecieValorada, TipoEspecieValorada, DirferidoRubro, SolicitudOnline, SolicitudEstudiante

from sga.tasks import send_html_mail
from decimal import Decimal

@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
@transaction.atomic()
def view(request):
    if request.method=='POST':
        action = request.POST['action']
        try:
            if action == 'guardar':
                try:
                    inscripcion = Inscripcion.objects.get(pk=request.POST['id'])
                    estadollamada = EstadoLlamada.objects.get(pk=request.POST['estado'])
                    seguimiento= RegistroSeguimiento(inscripcion=inscripcion,
                                                     estadollamada=estadollamada,
                                                     observacion=request.POST['nota'],
                                                     usuario=request.user,
                                                     fecha=datetime.now(),
                                                     finalizar=False)
                    seguimiento.save()

                    if 'archivo' in request.FILES:
                        seguimiento.archivo = request.FILES['archivo']
                        seguimiento.save()

                    inscripcion.persona.email = request.POST['email']
                    inscripcion.persona.telefono = request.POST['celular']
                    inscripcion.persona.telefono_conv = request.POST['fonod']
                    inscripcion.persona.save()

                    if request.POST['tiporespuesta']!= '0':
                        tipor = TipoRespuesta.objects.get(pk=int(request.POST['tiporespuesta']))
                        seguimiento.tiporespuesta = tipor
                        seguimiento.finalizar = True
                        seguimiento.cerrada = True
                        seguimiento.save()
                        seguimiento.inscripcion.persona.usuario.is_active = False
                        seguimiento.inscripcion.persona.usuario.save()

                    rubros = json.loads(request.POST['rubros'])

                    if request.POST['diferido'] == '0':
                        for r in rubros:
                            descuento=0
                            rubro = Rubro.objects.filter(pk=r['rubroid'])[:1].get()
                            categoria = rubro.diasvencimiento()
                            aplicadescuento = False
                            if r['aplica_descuento']=='1':
                                descuento = rubro.valor*((float(categoria.porcentaje)*float(categoria.factor))/100)
                                aplicadescuento = True
                            rubroseg = RubroSeguimiento(seguimiento=seguimiento,
                                                        rubro=rubro,
                                                        categoria=categoria,
                                                        valorgestionado=rubro.adeudado(),
                                                        fechaposiblepago=convertir_fecha(r['fechap']),
                                                        valordesc=descuento,
                                                        aplicadescuentocategoria=aplicadescuento)
                            rubroseg.save()
                            if request.POST['descuento_adicional'] > '0':
                                rubroseg.porcentajedescuentoadd =  request.POST['descuento_adicional']
                                rubroseg.save()

                            historico = HistoricoRubroSeguimiento(rubroseguimiento=rubroseg,
                                                                  observacion="GESTION INICIAL",
                                                                  fecha=datetime.now(),
                                                                  fechaposiblepago=convertir_fecha(r['fechap']),
                                                                  estado=False)
                            historico.save()

                    elif request.POST['diferido'] == '1':
                        list_rubros = [x['rubroid'] for x in rubros]
                        rubros_model = Rubro.objects.filter(id__in=list_rubros)

                        total = Rubro.objects.filter(id__in=list_rubros).aggregate(Sum('valor'))['valor__sum'] - (Pago.objects.filter(rubro__id__in=list_rubros).aggregate(Sum('valor'))['valor__sum'] if Pago.objects.filter(rubro__id__in=list_rubros) else 0)
                        valor = 0
                        list_gestionan = []

                        rubros_a_diferir = []
                        for r in rubros:
                            rubro = Rubro.objects.filter(pk=r['rubroid'])[:1].get()
                            valor += rubro.adeudado()
                            if valor <= total/2:
                                list_gestionan.append(rubro.id)

                                # LO MISMO
                                descuento=0
                                categoria = rubro.diasvencimiento()
                                aplicadescuento = False
                                if r['aplica_descuento']=='1':
                                    descuento = rubro.valor*((float(categoria.porcentaje)*float(categoria.factor))/100)
                                    aplicadescuento = True
                                rubroseg = RubroSeguimiento(seguimiento=seguimiento,
                                                            rubro=rubro,
                                                            categoria=categoria,
                                                            valorgestionado=rubro.adeudado(),
                                                            fechaposiblepago=convertir_fecha(r['fechap']),
                                                            valordesc=descuento,
                                                            aplicadescuentocategoria=aplicadescuento)
                                rubroseg.save()
                                if request.POST['descuento_adicional'] > '0':
                                    rubroseg.porcentajedescuentoadd =  request.POST['descuento_adicional']
                                    rubroseg.save()

                                historico = HistoricoRubroSeguimiento(rubroseguimiento=rubroseg,
                                                                      observacion="GESTION INICIAL",
                                                                      fecha=datetime.now(),
                                                                      fechaposiblepago=convertir_fecha(r['fechap']),
                                                                      estado=False)
                                historico.save()

                            else:
                                rubros_a_diferir.append(r['rubroid'])

                        if rubros_a_diferir:
                            adeudado = Rubro.objects.filter(id__in=rubros_a_diferir).aggregate(Sum('valor'))['valor__sum'] - (Pago.objects.filter(rubro__id__in=rubros_a_diferir).aggregate(Sum('valor'))['valor__sum'] if Pago.objects.filter(rubro__id__in=rubros_a_diferir) else 0)
                            tipo_especie = TipoEspecieValorada.objects.get(pk=ID_TIPO_ESPECIE_CONVENIO_PAGO)

                            solicitud_online = SolicitudOnline.objects.get(pk=3)

                            rub = Rubro(fecha=datetime.now().date(),
                                        valor=0,
                                        inscripcion=inscripcion,
                                        cancelado=True,
                                        fechavence=datetime.now().date())
                            rub.save()

                            solicitud_est = SolicitudEstudiante(solicitud=solicitud_online,
                                                                tipoe=tipo_especie,
                                                                inscripcion=inscripcion,
                                                                correo=inscripcion.persona.emailinst,
                                                                fecha=datetime.now(),
                                                                observacion="Convenio de Pago. Dpto. Asuntos Estudiantiles.",
                                                                solicitado=True,
                                                                rubro=rub)
                            solicitud_est.save()

                            serie = 0
                            valor = RubroEspecieValorada.objects.filter(rubro__fecha__year=rub.fecha.year).aggregate(Max('serie'))
                            if valor['serie__max']!=None:
                                serie = valor['serie__max']+1

                            rubro_especie = RubroEspecieValorada(rubro=rub,
                                                                 tipoespecie=tipo_especie,
                                                                 serie=serie,
                                                                 autorizado=False)
                            rubro_especie.save()

                            fecha_primer_pago = convertir_fecha(request.POST['fechaPrimerPago'])
                            diferido = DirferidoRubro(fecha=datetime.now().date(),
                                                      seguimiento=seguimiento,
                                                      rubroespecie=rubro_especie,
                                                      rubrosanteriores=','.join(map(str, rubros_a_diferir)),
                                                      num_cuotas=int(request.POST['numCuotas']),
                                                      totaldiferido=adeudado,
                                                      aprobado=None,
                                                      fechaprimerpago=fecha_primer_pago)
                            diferido.save()

                    if EMAIL_ACTIVE:
                        tipo = TipoIncidencia.objects.get(pk=INCIDENCIA_COBRANZAS)
                        hoy = datetime.now().today()
                        contenido = 'GESTION REALIZADA'
                        send_html_mail(contenido, "emails/gestion_cobranzas.html", {'fecha':hoy, 'contenido':contenido, 'usuario':request.user, 'gestion': seguimiento}, tipo.correo.split(","))

                    client_address = ip_client_address(request)
                    # Log de ADICIONAR SEGUIMIENTO
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(seguimiento).pk,
                        object_id       = seguimiento.id,
                        object_repr     = force_str(seguimiento),
                        action_flag     = ADDITION,
                        change_message  = 'Registro Seguimiento(' + client_address + ')' )

                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as ex:
                    print(ex)
                    return HttpResponse(json.dumps({"result":"bad" ,'error':str(ex)}),content_type="application/json")
            elif action == 'consulta':
                try:
                    lista=[]
                    if OpcionEstadoLlamada.objects.filter(estadollamada__id=request.POST['id']).exists():
                        for op in OpcionEstadoLlamada.objects.filter(estadollamada__id=request.POST['id']):
                            lista.append((op.id , op.descripcion))
                        return HttpResponse(json.dumps({"result":"ok","lista":lista }),content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({"result":"nodata" }),content_type="application/json")


                except Exception as e :
                    return HttpResponse(json.dumps({"result":"bad" , 'error':str(e)}),content_type="application/json")

            elif action == 'reasignar_gestor':
                try:
                    result = {}
                    inscripcion = Inscripcion.objects.get(pk=request.POST['inscripcion'])
                    gestor = AsistAsuntoEstudiant.objects.get(pk=request.POST['asistente'])
                    gestor_anterior = inscripcion.asistente.asistente.usuario.username
                    inscripcion.asistente = gestor
                    inscripcion.save()

                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id=request.user.pk,
                        content_type_id=ContentType.objects.get_for_model(inscripcion).pk,
                        object_id=inscripcion.id,
                        object_repr=force_str(inscripcion),
                        action_flag=CHANGE,
                        change_message='REASIGNACION DE GESTOR: '+gestor_anterior+' a '+inscripcion.asistente.asistente.usuario.username+' (' + client_address + ')')

                    result['result'] ="ok"
                    return HttpResponse(json.dumps(result),content_type="application/json")
                except Exception as e:
                    print(e)
                    result['result'] = str(e)
                    return HttpResponse(json.dumps(result),content_type="application/json")

            elif action == 'aprobar_descuentoadicional':
                try:
                    result = {}
                    seguimientos = json.loads(request.POST['seguimientos'])
                    for idseguimiento in seguimientos:
                        rs = RubroSeguimiento.objects.get(pk=int(idseguimiento['id']))
                        descuento = 0
                        descuento_add = 0
                        if rs.aplicadescuentocategoria and rs.categoria.porcentaje>0:
                            descuento = float(rs.categoria.porcentaje)*float(rs.categoria.factor)
                        if rs.porcentajedescuentoadd:
                            descuento_add = rs.porcentajedescuentoadd
                        porcentaje_descuento = descuento + descuento_add
                        nuevo_valordescuento = round(float(rs.valorgestionado) * (porcentaje_descuento/100.00),2)
                        rs.aprobardescuentoadd = True
                        rs.valordesc = nuevo_valordescuento
                        rs.save()

                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(rs).pk,
                        object_id       = rs.id,
                        object_repr     = force_str(rs),
                        action_flag     = CHANGE,
                        change_message  = 'APROBAR DESCUENTO ADICIONAL'+' (' + client_address + ')' )
                        result['result'] ="ok"
                        result['cedula'] = rs.rubro.inscripcion.persona.cedula
                    return HttpResponse(json.dumps(result),content_type="application/json")
                except Exception as e:
                    result['result'] = str(e)
                    return HttpResponse(json.dumps(result),content_type="application/json")

            elif action == 'aprobar_descuentocategoria':
                try:
                    result = {}
                    seguimientos = json.loads(request.POST['seguimientos'])
                    for idseguimiento in seguimientos:
                        print(idseguimiento['id'])
                        rs = RubroSeguimiento.objects.get(pk=int(idseguimiento['id']))
                        descuento = 0
                        descuento_add = 0
                        if rs.categoria.porcentaje>0:
                            descuento = float(rs.categoria.porcentaje)*float(rs.categoria.factor)
                        if rs.porcentajedescuentoadd:
                            descuento_add = rs.porcentajedescuentoadd
                        porcentaje_descuento = descuento + descuento_add
                        nuevo_valordescuento = round(float(rs.valorgestionado) * (porcentaje_descuento/100.00),2)
                        rs.aplicadescuentocategoria = True
                        rs.valordesc = nuevo_valordescuento
                        rs.save()
                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(rs).pk,
                        object_id       = rs.id,
                        object_repr     = force_str(rs),
                        action_flag     = CHANGE,
                        change_message  = 'APLICAR DESCUENTO CATEGORIA'+' (' + client_address + ')' )
                    result['result'] ="ok"
                    return HttpResponse(json.dumps(result),content_type="application/json")
                except Exception as e:
                    result['result'] = str(e)
                    return HttpResponse(json.dumps(result),content_type="application/json")

            elif action == 'report_compromisospagos':
                try:
                    nombre = ejecutar(request, request.POST['desde'], request.POST['hasta'],request.user)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")
                except Exception as e:
                    print(e)
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

            elif action == 'report_categoriascedulas':
                try:
                    nombre = ejecutar_inscripcioncategoria(request,request.user)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")
                except Exception as e:
                    print(e)
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

            elif action == 'edit_fechaposiblepago':
                try:
                    rs = RubroSeguimiento.objects.get(pk=request.POST['id'])
                    rs.fechaposiblepago = request.POST['nuevafecha']
                    rs.save()
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as e:
                    print(e)
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

            elif action == 'desactiva_rubroseguimiento':
                try:
                    print(request.POST)
                    rs = RubroSeguimiento.objects.get(pk=request.POST['id'])
                    rs.estado = False
                    rs.save()
                    return HttpResponse(json.dumps({"result":"ok",'identificacion':rs.rubro.inscripcion.persona.cedula if rs.rubro.inscripcion.persona.cedula else rs.rubro.inscripcion.persona.pasaporte }),content_type="application/json")
                except Exception as e:
                    print(e)
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

            elif action == 'addCategoriaRubro':
                sid = transaction.savepoint()
                try:
                    desde = datetime.strptime(request.POST['fecha'], "%d-%m-%Y").date()
                    hasta = datetime.strptime("2100-01-01", "%Y-%m-%d").date()
                    categoriasAntiguas = CategoriaRubro.objects.filter(estado=True)
                    categoriasAntiguas.update(hasta=desde-timedelta(days=1))
                    categoriasAntiguas.update(estado=False)

                    for c in json.loads(request.POST['categorias']):
                        newCategoria = CategoriaRubro(categoria=c['categoria'],
                                                   porcentaje=c['porcentaje'],
                                                   factor=Decimal(c['factor']),
                                                   numdiasminimo=c['diaDesde'],
                                                   numdiasmaximo=c['diaHasta'],
                                                   desde=desde,
                                                   hasta=hasta,
                                                   estado=True)
                        newCategoria.save()
                    transaction.savepoint_commit(sid)
                    # transaction.set_rollback(True)
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as e:
                    print(e)
                    transaction.savepoint_rollback(sid)
                    return HttpResponse(json.dumps({"result":"bad", "error":str(e)}),content_type="application/json")

            elif action == 'habilita_gestion':
                inscripcion = Inscripcion.objects.get(pk=request.POST['id'])
                gestion = RegistroSeguimiento.objects.filter(inscripcion=inscripcion).order_by('-id')[:1].get()
                gestion.cerrada = False
                gestion.finalizar = False
                gestion.observacion = ''
                gestion.save()
                gestion.inscripcion.persona.usuario.is_active = True
                gestion.inscripcion.persona.usuario.save()
                return HttpResponse(json.dumps({"result":"ok", 'cedula':str(inscripcion.persona.cedula if inscripcion.persona.cedula else inscripcion.persona.pasaporte)}),content_type="application/json")

            elif action == 'add_historial_seguimiento':
                try:
                    print(request.POST)
                    fechaPago = datetime.strptime(str(request.POST['fecha']), '%d-%m-%Y').date()

                    for id in json.loads(request.POST['ids']):
                        rubroSeguimiento = RubroSeguimiento.objects.get(pk=id)
                        historial = HistoricoRubroSeguimiento(rubroseguimiento=rubroSeguimiento,
                                                              fechaposiblepago=fechaPago,
                                                              fecha=datetime.now(),
                                                              observacion=request.POST['observacion'])
                        historial.save()
                        if 'archivo' in request.FILES:
                            historial.archivo = request.FILES['archivo']
                            historial.save()

                        rubroSeguimiento.fechaposiblepago = fechaPago
                        rubroSeguimiento.categoria = rubroSeguimiento.rubro.diasvencimiento()
                        rubroSeguimiento.save()

                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as ex:
                    print(ex)

            elif action =='obtener_gestiones':
                try:
                    print(request.POST)
                    inicio = datetime.strptime(request.POST['inicio'], '%d-%m-%Y').date()
                    fin = datetime.strptime(request.POST['fin'], '%d-%m-%Y').date()
                    inicio2 = datetime.combine(inicio, datetime.min.time())
                    fin2 = datetime.combine(fin, datetime.min.time()) + timedelta(hours=23, minutes=59, seconds=59)
                    gestor = AsistAsuntoEstudiant.objects.get(pk=request.POST['id'])
                    gestiones = HistoricoRubroSeguimiento.objects.filter(rubroseguimiento__seguimiento__usuario=gestor.asistente.usuario, fecha__gte=inicio2, fecha__lte=fin2).order_by('fecha', 'rubroseguimiento__seguimiento__inscripcion__persona__apellido1')
                    print(gestiones.count())
                    data = [
                                {
                                    'nombre':x.rubroseguimiento.rubro.inscripcion.persona.nombre_completo_inverso(),
                                    'rubro':x.rubroseguimiento.rubro.nombre(),
                                    'valor':str(x.rubroseguimiento.valorgestionado),
                                    'categoria':x.rubroseguimiento.categoria.categoria,
                                    'fecha':str(x.fecha.date()),
                                    'soporte': str(x.archivo) if x.archivo else str(x.rubroseguimiento.seguimiento.archivo)
                                 }
                        for x in gestiones
                    ]
                    print(data)
                    return HttpResponse(json.dumps({"result": "ok", 'gestiones':data}), content_type="application/json")
                except Exception as ex:
                    print('ERROR: '+str(ex))
                    return HttpResponse(json.dumps({"result": "bad", 'mensaje':str(ex)}), content_type="application/json")

        except:
            return HttpResponseRedirect("/seguimiento")
    else:
        data = {'title': 'Gestion de Cartera'}
        addUserData(request,data)
        try:
            if 'action' in request.GET:
                action = request.GET['action']

                if action=='inscritos':

                    if 'addseguimiento' in request.GET:

                        return render(request ,"seguimiento/observaciones.html" ,  data)
                    else:
                        search = None
                        todos = None
                        activos = None
                        inactivos = None
                        band=0
                        if 's' in request.GET:
                            search = request.GET['s']
                            band=1
                        if 'a' in request.GET:
                            activos = request.GET['a']
                        if 'i' in request.GET:
                            inactivos = request.GET['i']
                        if 't' in request.GET:
                            todos = request.GET['t']
                        if search:
                            ss = search.split(' ')
                            while '' in ss:
                                ss.remove('')
                            if len(ss)==1:
                                inscripciones = Inscripcion.objects.filter(Q(Q(persona__nombres__icontains=search) | Q(persona__apellido1__icontains=search) | Q(persona__apellido2__icontains=search) | Q(persona__cedula__icontains=search) | Q(persona__pasaporte__icontains=search) | Q(identificador__icontains=search) | Q(inscripciongrupo__grupo__nombre__icontains=search) | Q(carrera__nombre__icontains=search) | Q(persona__usuario__username__icontains=search)),registra_pago=False).exclude(carrera__id__in=CARRERAS_ID_EXCLUIDAS_INEC).order_by('persona__apellido1')
                            else:
                                inscripciones = Inscripcion.objects.filter(Q(Q(persona__apellido1__icontains=ss[0]) & Q(persona__apellido2__icontains=ss[1])),registra_pago=False).exclude(carrera__id__in=CARRERAS_ID_EXCLUIDAS_INEC).order_by('persona__apellido1','persona__apellido2','persona__nombres')

                        else:
                            fech=datetime.now().year
                            fecha= '2014-12-01'
                            inscripciones = Inscripcion.objects.filter(persona__usuario__is_active=True,registra_pago=False,pk__in=Inscripcion.objects.filter(persona__usuario__is_active=True,fecha__gte=fecha).values('pk')).exclude(carrera__id__in=CARRERAS_ID_EXCLUIDAS_INEC).order_by('persona__apellido1')
                            # inscripciones = Inscripcion.objects.filter(persona__usuario__is_active=True,fecha__gte=fecha).order_by('persona__apellido1')[:100]

                        if 'g' in request.GET:
                            grupoid = request.GET['g']
                            data['grupo'] = Grupo.objects.get(pk=request.GET['g'])
                            data['grupoid'] = int(grupoid) if grupoid else ""
                            inscripciones = inscripciones.filter(carrera__grupocoordinadorcarrera__group__in=request.user.groups.all(), inscripciongrupo__grupo=data['grupo']).distinct()
                        # else:
                        #     inscripciones = inscripciones.filter(carrera__grupocoordinadorcarrera__group__in=request.user.groups.all()).distinct()

                        if todos:
                            inscripciones = Inscripcion.objects.filter(registra_pago=False).exclude(carrera__id__in=CARRERAS_ID_EXCLUIDAS_INEC).order_by('persona__apellido1')
                        if activos:
                            inscripciones = Inscripcion.objects.filter(persona__usuario__is_active=True,registra_pago=False).exclude(carrera__id__in=CARRERAS_ID_EXCLUIDAS_INEC).order_by('persona__apellido1')
                        if inactivos:
                            inscripciones = Inscripcion.objects.filter(persona__usuario__is_active=False,registra_pago=False).exclude(carrera__id__in=CARRERAS_ID_EXCLUIDAS_INEC).order_by('persona__apellido1')

                        if CENTRO_EXTERNO and not ('s' in request.GET):
                            inscripciones = Inscripcion.objects.all().order_by('persona__apellido1')

                        paging = MiPaginador(inscripciones, 30)
                        p = 1
                        try:
                            if 'page' in request.GET:
                                p = int(request.GET['page'])
                                # if band==0:
                                #     inscripciones = Inscripcion.objects.all().order_by('persona__apellido1')
                                paging = MiPaginador(inscripciones, 30)
                            page = paging.page(p)
                        except Exception as ex:
                            page = paging.page(1)

                        # Para atencion al cliente
                        atiende=False
                        idpresona=data['persona'].id
                        if AtencionCliente.objects.filter(persona=idpresona,estado=True).exists():
                            atiende=True
                        data['atiende'] = atiende

                        data['paging'] = paging
                        data['rangospaging'] = paging.rangos_paginado(p)
                        data['page'] = page
                        data['search'] = search if search else ""
                        data['todos'] = todos if todos else ""
                        data['activos'] = activos if activos else ""
                        data['inactivos'] = inactivos if inactivos else ""
                        data['inscripciones'] = page.object_list
                        data['utiliza_grupos_alumnos'] = UTILIZA_GRUPOS_ALUMNOS
                        data['reporte_ficha_id'] = REPORTE_CERTIFICADO_INSCRIPCION
                        data['clave'] = DEFAULT_PASSWORD
                        data['usafichamedica'] = UTILIZA_FICHA_MEDICA
                        data['centroexterno'] = CENTRO_EXTERNO
                        data['matriculalibre'] = MODELO_EVALUACION==EVALUACION_TES
                        data['grupos'] = Grupo.objects.all().order_by('nombre')
                        data['inscripcion_conduccion'] = INSCRIPCION_CONDUCCION
                        data['extra'] = 1

                        return render(request ,"seguimiento/seguimiento.html" ,  data)

                elif action == 'gestionar':
                    try:
                        i = Inscripcion.objects.filter(id=request.GET['id'])[:1].get()
                        rubros = []
                        total = 0
                        porcategoria = 0
                        counterNotA2 = 0
                        for r in Rubro.objects.filter(inscripcion=i,cancelado=False,rubroespecievalorada=None, fechavence__lt=datetime.now().date()).order_by('fechavence'):
                            vencimiento = r.diasvencimiento()
                            if vencimiento:
                                categoria = r.diasvencimiento().categoria
                                if porcategoria < vencimiento.porcentaje:
                                    porcategoria = vencimiento.porcentaje
                                    data['porcategoria']=porcategoria
                                if not RubroSeguimiento.objects.filter(rubro=r, estado=True).exists() and not DirferidoRubro.objects.filter(rubrosanteriores__contains=str(r.id)).exists():
                                    rubros.append((r,vencimiento.categoria))
                                    total = total + r.adeudado()
                                if vencimiento.categoria != 'A2':
                                    counterNotA2 += 1

                        data['opcrespuesta'] = OpcionRespuesta.objects.all()
                        data['estadollamada'] = EstadoLlamada.objects.all()
                        data['opcllamada'] = OpcionEstadoLlamada.objects.all()
                        data['tiporespuesta'] = TipoRespuesta.objects.all()

                        data['inscripcion'] = i
                        data['total'] = total
                        # data['pudeaplicar'] = False
                        # if total >= 100 :
                        #     data['pudeaplicar'] =True

                        data['rubros'] = rubros if counterNotA2 >= 1 else []
                        data['hoy'] = datetime.today().date()
                        if RegistroSeguimiento.objects.filter(inscripcion=i).exists():
                            data['registrollamada'] = RegistroSeguimiento.objects.filter(inscripcion=i).order_by('fecha')

                        if RegistroSeguimiento.objects.filter(inscripcion=i,cerrada=True).exists():
                            data['cerrada'] = 1
                        else:
                            data['cerrada'] = 2
                        if i.asistente.asistente.usuario != request.user:
                            data['cerrada'] = 1
                        data['descuento'] = DescuentoGestionForm(initial={'fechadesc':datetime.now().date()})
                        return render(request ,"registros/ficha.html" ,  data)
                    except Exception as ex:
                        print(ex)

                elif action == 'tiporespuesta':
                    data['title'] = 'Registros'
                    data['tiporespuesta'] = TipoRespuesta.objects.all()
                    data['frmtipores'] = RespuestaForm()
                    search = None
                    if 's' in request.GET:
                        search=request.GET['s']
                        data['tiporespuesta']  =TipoRespuesta.objects.filter(descripcion__icontains=search)
                    data['search'] = search if search else ""
                    return render(request ,"registros/tiporespuesta.html" ,  data)

                elif action == 'estadisticas':
                    try:
                        hoy = datetime.now().date()
                        data['title'] = 'Estadisticas'
                        gestores = AsistAsuntoEstudiant.objects.filter(estado=True).order_by('asistente__apellido1')
                        data['gestores'] = gestores
                        data['categorias'] = CategoriaRubro.objects.filter(desde__lte=hoy, hasta__gte=hoy).order_by('categoria')
                        data['now'] = datetime.now().date()
                        if 'inicio' in request.GET and 'fin' in request.GET:
                            inicio = datetime.strptime(request.GET['inicio'], '%d-%m-%Y').date()
                            fin = datetime.strptime(request.GET['fin'], '%d-%m-%Y').date()
                            data['inicio'] = inicio
                            data['fin'] = fin
                            rubros_seguimiento = RubroSeguimiento.objects.filter(fechapago__gte=inicio, fechapago__lte=fin)
                            data['rubros_seguimiento'] = rubros_seguimiento

                        if 'c' in request.GET:
                            categoria = CategoriaRubro.objects.get(pk=request.GET['c'])
                            data['categoria'] = categoria

                        return render(request ,"registros/estadistica.html" ,  data)
                    except Exception as ex:
                        print(ex)

                elif action == 'detalle_estadisticas':
                    try:
                        hoy = datetime.now().date()
                        data['title'] = 'Detalle Estadisticas'
                        inicio = datetime.strptime(request.GET['inicio'], '%d-%m-%Y').date()
                        fin = datetime.strptime(request.GET['fin'], '%d-%m-%Y').date()
                        if 'id' in request.GET:
                            gestor = AsistAsuntoEstudiant.objects.get(pk=request.GET['id'])
                            rubros_seguimientos = RubroSeguimiento.objects.filter(seguimiento__usuario=gestor.asistente.usuario, fechapago__gte=inicio, fechapago__lte=fin, rubro__cancelado=True, estado=True).exclude(fechapago=None)
                            data['gestor'] = gestor
                            data['rubros_seguimientos'] = rubros_seguimientos
                        else:
                            data['totales'] = True
                        categorias = CategoriaRubro.objects.filter(desde__lte=hoy, hasta__gte=hoy).order_by('categoria')
                        data['categorias'] = categorias
                        data['now'] = datetime.now().date()
                        data['inicio'] = inicio
                        data['fin'] = fin
                        return render(request ,"registros/detalle_estadistica.html" ,  data)
                    except Exception as ex:
                        print(ex)

                elif action == 'categorias':
                    try:
                        data['title'] = 'Categoria Rubros'
                        categorias = CategoriaRubro.objects.filter().order_by('-estado','-hasta', 'categoria')
                        data['categorias'] = categorias
                        data['fechaActual'] = datetime.now().date()+timedelta(days=1)
                        return render(request ,"registros/categorias.html" ,  data)
                    except Exception as ex:
                        print(ex)

                elif action == 'gestiones':
                    try:
                        print(request.GET)
                        data['title'] = 'Gestiones Cobranzas'
                        data['inscripcion'] = Inscripcion.objects.get(pk=request.GET['id'])
                        data['registrollamada'] = RegistroSeguimiento.objects.filter(inscripcion=data['inscripcion'] ).order_by('fecha')
                        return render(request ,"seguimiento/gestiones.html" ,  data)
                    except Exception as ex:
                        print(ex)

                elif action == 'vergestion':
                    data = {}
                    data['inscripcion'] = Inscripcion.objects.get(id=request.GET['id'])
                    data['registrollamada'] = RegistroSeguimiento.objects.filter(inscripcion=data['inscripcion'] ).order_by('fecha')
                    return render(request ,"seguimiento/vergestion.html" ,  data)

                elif action == 'diferidos':
                    seguimiento = RegistroSeguimiento.objects.get(pk=request.GET['id'])
                    diferido = DirferidoRubro.objects.filter(seguimiento=seguimiento)[:1].get()
                    return render(request, 'registros/diferidos.html', {'diferido':diferido})

                # elif action == 'reintegro':
                #     try:
                #         print(request.GET)
                #         data['title'] = 'Reintegro de Alumnos Inactivos'
                #         retirados = RetiradoMatricula.objects.filter(activo=True)
                #         inscripciones = Inscripcion.objects.filter(persona__usuario__is_active=False).exclude(id__in=retirados.values('inscripcion'))
                #         inscripciones2 = Inscripcion.objects.filter(persona__usuario__is_active=False).exclude(id__in=retirados.values('inscripcion'))
                #         print(inscripciones.count())
                #         for i in inscripciones:
                #             if Pago.objects.filter(rubro__inscripcion=i).exists():
                #                 ultimo_pago = Pago.objects.filter(rubro__inscripcion=i).order_by('-id')[:1].get()
                #                 dias = (datetime.date(datetime.now()) - ultimo_pago.fecha).days
                #                 if dias > 365:
                #                     inscripciones2 = inscripciones2.exclude(id=i.id)
                #         print(inscripciones2.count())
                #
                #         # return render(request ,"registros.html" ,  data)
                #         return HttpResponseRedirect("/registros")
                #     except Exception as ex:
                #         print(ex)

            else:
                try:
                    search = None
                    if 's' in request.GET:
                        search=request.GET['s']

                    op=None
                    asistente=None
                    manana = datetime.now().date() +  timedelta(1)
                    hoy = datetime.now().date()

                    # seguimientos = RegistroSeguimiento.objects.filter(usuario__id__in=AsistAsuntoEstudiant.objects.filter(estado=False).values('asistente__usuario__id')).values('inscripcion__id')
                    if AsistAsuntoEstudiant.objects.filter(asistente__usuario=request.user).exists():
                        asistente = AsistAsuntoEstudiant.objects.filter(asistente__usuario=request.user)[:1].get()
                        data['asistente'] = asistente
                        inscripciones = Inscripcion.objects.filter(asistente = asistente, persona__usuario__is_active=True).exclude(asistente=None)
                        if RubroSeguimiento.objects.filter(rubro__inscripcion__in=inscripciones,rubro__cancelado=False,fechaposiblepago=manana,fechapago=None, estado=True).exists():
                            data['porvencer'] = RubroSeguimiento.objects.filter(rubro__inscripcion__in=inscripciones,rubro__cancelado=False,fechaposiblepago=manana,fechapago=None, estado=True)
                    else:
                        inscripciones = Inscripcion.objects.filter().exclude(asistente=None).exclude(asistente=None)
                        if RubroSeguimiento.objects.filter(rubro__cancelado=False,fechaposiblepago=manana,fechapago=None, estado=True).exists():
                            data['porvencer'] =  RubroSeguimiento.objects.filter(rubro__cancelado=False,fechaposiblepago=manana,fechapago=None, estado=True)

                    if 'op' in request.GET:
                        op=1
                        if request.GET['op'] == 'cerrados':
                            registros = RegistroSeguimiento.objects.filter(cerrada=True).values('inscripcion')
                            data['cerrados'] = True
                            if asistente:
                                inscripciones = Inscripcion.objects.filter(id__in=registros,asistente = asistente)
                            else:
                                inscripciones = Inscripcion.objects.filter(id__in=registros)
                        if request.GET['op'] == 'buscar':
                            asistentefilter =AsistAsuntoEstudiant.objects.get(pk=request.GET['asist'])
                            data['asistentefilter'] = asistentefilter
                            inscripciones = Inscripcion.objects.filter(asistente = asistentefilter)

                    if search:
                        ss = search.split(' ')
                        while '' in ss:
                            ss.remove('')
                        if len(ss)==1:
                            inscripciones = inscripciones.filter(Q(persona__nombres__icontains=search) | Q(persona__apellido1__icontains=search) | Q(persona__apellido2__icontains=search) | Q(persona__cedula__icontains=search) | Q(persona__pasaporte__icontains=search) | Q(identificador__icontains=search) | Q(inscripciongrupo__grupo__nombre__icontains=search) | Q(carrera__nombre__icontains=search) | Q(persona__usuario__username__icontains=search)).exclude(asistente=None).order_by('persona__apellido1')
                        else:
                            inscripciones = inscripciones.filter(Q(persona__apellido1__icontains=ss[0]) & Q(persona__apellido2__icontains=ss[1])).exclude(asistente=None).order_by('persona__apellido1','persona__apellido2','persona__nombres')

                    if 'c' in request.GET:
                        categoria = CategoriaRubro.objects.get(pk=request.GET['c'])
                        hasta = datetime.today().date()-timedelta(days=categoria.numdiasminimo)
                        if categoria.numdiasmaximo:
                            desde = datetime.today().date()-timedelta(days=categoria.numdiasmaximo)
                            rubros = Rubro.objects.filter(fechavence__gte=desde, fechavence__lte=hasta,rubroespecievalorada=None, inscripcion__id__in=inscripciones, cancelado=False,inscripcion__persona__usuario__is_active=True)
                        else:
                            rubros = Rubro.objects.filter(rubroespecievalorada=None, fechavence__lte=hasta, cancelado=False,inscripcion__persona__usuario__is_active=True)
                        inscripciones = inscripciones.filter(id__in=rubros.values('inscripcion')).exclude(asistente=None)
                        data['categoria'] = categoria

                    if 'd' in request.GET:
                        seguimientos = RubroSeguimiento.objects.filter(porcentajedescuentoadd__gt=0, aprobardescuentoadd=False).exclude(porcentajedescuentoadd=None)
                        inscripciones = inscripciones.filter(id__in=seguimientos.values('rubro__inscripcion')).exclude(asistente=None)
                        data['desc_add'] = True

                    paging = MiPaginador(inscripciones, 30)
                    p = 1
                    try:
                        if 'page' in request.GET:
                            p = int(request.GET['page'])
                        page = paging.page(p)
                    except:
                        page = paging.page(1)
                    if 'op' in request.GET:
                        op =request.GET['op']
                    data['paging'] = paging
                    data['rangospaging'] = paging.rangos_paginado(p)
                    data['page'] = page
                    data['search'] = search if search else ""
                    data['op'] = op if op else ""
                    data['inscripciones'] = page.object_list
                    data['asistentes'] = AsistAsuntoEstudiant.objects.filter(estado=True).order_by('asistente__apellido1','asistente__apellido2')
                    data['form'] = GestorForm
                    data['generarform']=EntregaUniformeExcelForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
                    data['categorias'] = CategoriaRubro.objects.filter(estado=True).order_by('categoria')
                    data['num_descuentosvalidar'] = RubroSeguimiento.objects.filter(porcentajedescuentoadd__gt=0, aprobardescuentoadd=False).exclude(porcentajedescuentoadd=None).count()

                    data['fecha'] = hoy
                    data['puede_gestionar'] = True
                    if RubroSeguimiento.objects.filter(fechaposiblepago__lte=hoy, estado=True, seguimiento__cerrada=False, seguimiento__usuario=request.user).exclude(rubro__cancelado=True).exists():
                        data['puede_gestionar'] = False
                        data['pendientes'] = RubroSeguimiento.objects.filter(fechaposiblepago__lte=hoy, estado=True, seguimiento__cerrada=False, seguimiento__usuario=request.user).exclude(rubro__cancelado=True).order_by('fechaposiblepago').values('fechaposiblepago').distinct()
                    if 'fecha' in request.GET:
                        fecha = datetime.strptime(str(request.GET['fecha']), '%d-%m-%Y').date()
                        data['tomorrow'] = fecha + timedelta(days=1)
                        data['ayer'] = fecha - timedelta(days=1)
                        data['seguimientos_fecha'] = True
                        data['fecha'] = fecha

                        # if RubroSeguimiento.objects.filter(fechaposiblepago=fecha, estado=True, fechapago=None, rubro__cancelado=False).exists():
                        #     data['seguimientos'] = RubroSeguimiento.objects.filter(fechaposiblepago=fecha, estado=True, fechapago=None, rubro__cancelado=False)

                        if RubroSeguimiento.objects.filter(fechaposiblepago=fecha, estado=True).exists():
                            if AsistAsuntoEstudiant.objects.filter(asistente__usuario=request.user).exists():
                                data['seguimientos'] = RubroSeguimiento.objects.filter(fechaposiblepago=fecha, estado=True, seguimiento__usuario__username=request.user).order_by('rubro__cancelado', 'rubro__inscripcion__persona__apellido1', 'rubro__inscripcion__persona__apellido2')
                            else:
                                if 'asist' in request.GET:
                                    asist = AsistAsuntoEstudiant.objects.get(pk=request.GET['asist'])
                                    data['asist'] = asist
                                    data['seguimientos'] = RubroSeguimiento.objects.filter(fechaposiblepago=fecha, estado=True, seguimiento__usuario=asist.asistente.usuario).order_by('seguimiento__usuario__username', 'rubro__cancelado', 'rubro__inscripcion__persona__apellido1', 'rubro__inscripcion__persona__apellido2')
                                else:
                                    historico = HistoricoRubroSeguimiento.objects.filter(fecha__gte=datetime.combine(fecha, datetime.min.time()), estado=True, fecha__lte=datetime.combine(fecha, datetime.max.time()))
                                    seguimientos_total = RubroSeguimiento.objects.filter(Q(estado=True, id__in=historico.values('rubroseguimiento'))|Q(fechaposiblepago=fecha, estado=True))
                                    data['seguimientos'] = seguimientos_total
                    elif 'convenios' in request.GET:
                        convenios = DirferidoRubro.objects.exclude(seguimiento=None)
                        data['convenios'] = True
                        registros_convenios = RegistroSeguimiento.objects.filter(id__in=convenios.values('seguimiento')).order_by('-id')
                        if AsistAsuntoEstudiant.objects.filter(asistente__usuario=request.user).exists():
                            registros_convenios = registros_convenios.filter(usuario__username=request.user).order_by('-id')
                        if search:
                            ss = search.split(' ')
                            while '' in ss:
                                ss.remove('')
                            if len(ss)==1:
                                registros_convenios = registros_convenios.filter(Q(inscripcion__persona__nombres__icontains=search) | Q(inscripcion__persona__apellido1__icontains=search) | Q(inscripcion__persona__apellido2__icontains=search) | Q(inscripcion__persona__cedula__icontains=search) | Q(inscripcion__persona__pasaporte__icontains=search))
                            else:
                                registros_convenios = registros_convenios.filter(Q(inscripcion__persona__apellido1__icontains=ss[0]) & Q(inscripcion__persona__apellido2__icontains=ss[1]))

                        data['seguimientos_convenio'] = registros_convenios

                    data['media_root'] = MEDIA_ROOT

                    return render(request ,"registros/registros.html" ,  data)

                except Exception as e:
                    print(e)
                    return HttpResponseRedirect("/registros")


        except Exception as ex:
            print(ex)
            return HttpResponseRedirect("/registros")
