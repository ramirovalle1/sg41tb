from datetime import datetime,time
import decimal
import json
import os
from django.contrib.admin.models import LogEntry, ADDITION,DELETION,CHANGE
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render

from django.utils.encoding import force_str
from decorators import secure_module
from med.models import PersonaEstadoCivil
from settings import PUNTAJE_BECA_DISCAPA, PUNTAJE_BECA_NORMAL, TIPO_ESPECIE_BECA, MEDIA_ROOT, EMAIL_ACTIVE, \
    ID_VIVIPROPIA_BECA, ID_VIVIARREN_BECA, ID_VIVICEDIDA_BECA, ID_TIPVIVOTRO_BECA, ID_DATOECONOTRO_BECA, \
    SISTEMAS_GROUP_ID, SECRETARIAGENERAL_GROUP_ID, DOBE_GROUP_ID, TIPO_BECA_SENESCYT, LISTA_TIPO_BECA, NIVEL_MALLA_UNO, \
    ID_AUDITOR_INTERNO
from sga.commonviews import addUserData, ip_client_address
from sga.forms import SolicitudBecaForm, ResponSolicBecaForm, CroquisForm,AusenciaJustificadaForm, SolicitudBecaNuevaForm,SolicitudArchivoAyudaForm,SolicitudBecaRenovarForm, BecaParcialForm, DetalleDescuentoBecaForm, SolicitudBecaFormAddArchivo, SolicitudRevisionAplicada
from sga.models import SolicitudBeca, Inscripcion, Matricula,TipoDocumenBeca, ArchivoSoliciBeca,Persona, TenenciaVivienda,TipoIngresoVivienda,TipoEgresoVivienda,SectorVivienda, \
     Canton,Rubro,Nivel,RubroEspecieValorada, RecordAcademico, AsignaturaMalla,PersonAutorizaBecaAyuda,HistorialGestionBeca,ArchivoSoliciAnalisisBeca,TipoBeneficio,ArchivoVerificadoBecaAyuda,TipoBeca, TablaDescuentoBeca,Resolucionbeca,PerfilInscripcion, RubroCuota, RubroMatricula, RubroOtro, RubroInscripcion, Pago, TipoEstadoSolicitudBeca, ArchivoSolicitudBeca, TipoGestionBeca


from decimal import Decimal
from sga.tasks import send_html_mail
from sga.reportes import elimina_tildes
from socioecon.models import ParentezcoPersona, OcupacionJefeHogar, NivelEstudio, FormaTrabajo, TipoVivienda, PersonaCubreGasto, InscripcionFichaSocioEconomicaBeca, DatoResidente, DatoTrabajo, Detallevivienda, DetalleIngrexEgres, EnfermedadFamilia,ReferenciaBeca,DatosAcademicos,ReferenciaPersonal,InscripcionFichaSocioeconomica
from django.contrib.auth.models import User

__author__ = 'jurgiles'

def convertir_fecha(s):
    try:
        return datetime(int(s[-4:]), int(s[3:5]), int(s[:2]))
    except:
        return None


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
        if Inscripcion.objects.filter(persona__usuario=request.user).exists():
            inscripcion = Inscripcion.objects.get(persona__usuario=request.user)
            if inscripcion.rubros_vencidos():
                return HttpResponseRedirect("/?info=No tiene permiso para acceder al modulo")
        hoy = datetime.today().date()
        if request.method == 'POST':
            action = request.POST['action']
            if action == 'addtipo':
                try:
                    mensaje = ''
                    if request.POST['edit'] == '0':
                        tipo = TipoDocumenBeca(descripcion = request.POST['descripcion'])
                        tipo.save()
                        mensaje = 'Ingreso'
                    else:
                        tipo = TipoDocumenBeca.objects.get(id = request.POST['edit'])
                        tipo.descripcion = str(request.POST['descripcion'])
                        tipo.save()
                        mensaje = 'Edicion'
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(tipo).pk,
                        object_id       = tipo.id,
                        object_repr     = force_str(tipo),
                        action_flag     = ADDITION,
                        change_message  = mensaje +' de tipo de documento para beca (' + client_address + ')' )
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
            elif action == 'addtenencia':
                try:
                    mensaje = ''
                    if request.POST['edit'] == '0':
                        tenen = TenenciaVivienda(descripcion = request.POST['descripcion'])
                        tenen.save()
                        mensaje = 'Ingreso'
                    else:
                        tenen = TenenciaVivienda.objects.get(id = request.POST['edit'])
                        tenen.descripcion = str(request.POST['descripcion'])
                        tenen.save()
                        mensaje = 'Edicion'
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(tenen).pk,
                        object_id       = tenen.id,
                        object_repr     = force_str(tenen),
                        action_flag     = ADDITION,
                        change_message  = mensaje +' de tenencia de la vivienda (' + client_address + ')' )
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
            elif action == 'addtipoingresovivi':
                try:
                    mensaje = ''
                    if request.POST['edit'] == '0':
                        tipingre = TipoIngresoVivienda(descripcion = request.POST['descripcion'])
                        tipingre.save()
                        mensaje = 'Ingreso'
                    else:
                        tipingre = TipoIngresoVivienda.objects.get(id = request.POST['edit'])
                        tipingre.descripcion = str(request.POST['descripcion'])
                        tipingre.save()
                        mensaje = 'Edicion'
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(tipingre).pk,
                        object_id       = tipingre.id,
                        object_repr     = force_str(tipingre),
                        action_flag     = ADDITION,
                        change_message  = mensaje +' de tipo de ingreso en la vivienda (' + client_address + ')' )
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
            elif action == 'addsectorvivi':
                try:
                    mensaje = ''
                    if request.POST['edit'] == '0':
                        sector = SectorVivienda(descripcion = request.POST['descripcion'])
                        sector.save()
                        mensaje = 'Ingreso'
                    else:
                        sector = SectorVivienda.objects.get(id = request.POST['edit'])
                        sector.descripcion = str(request.POST['descripcion'])
                        sector.save()
                        mensaje = 'Edicion'
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(sector).pk,
                        object_id       = sector.id,
                        object_repr     = force_str(sector),
                        action_flag     = ADDITION,
                        change_message  = mensaje +' de sector de vivienda (' + client_address + ')' )
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
            elif action == 'addtipoegresovivi':
                try:
                    mensaje = ''
                    if request.POST['edit'] == '0':
                        tipegre = TipoEgresoVivienda(descripcion = request.POST['descripcion'],
                                                     ejemplo = request.POST['ejemplo'])
                        tipegre.save()
                        mensaje = 'Ingreso'
                    else:
                        tipegre = TipoEgresoVivienda.objects.get(id = request.POST['edit'])
                        tipegre.descripcion = str(request.POST['descripcion'])
                        tipegre.ejemplo = request.POST['ejemplo']
                        tipegre.save()
                        mensaje = 'Edicion'
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(tipegre).pk,
                        object_id       = tipegre.id,
                        object_repr     = force_str(tipegre),
                        action_flag     = ADDITION,
                        change_message  = mensaje +' de tipo de egreso en la vivienda (' + client_address + ')' )
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
            elif action == 'existtipo':
                try:
                    if ArchivoSoliciBeca.objects.filter(solicitudbeca__id = request.POST['idsoli'],tipodocumenbeca__id = request.POST['idtipo']).exists():
                        return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

            elif action == 'tienearchivo':
                try:
                    if ArchivoSoliciBeca.objects.filter(solicitudbeca__id = request.POST['id']).exists():
                        return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")


            elif action == 'guardartabladescuentobeca':
                try:

                    f = SolicitudArchivoAyudaForm(request.POST,request.FILES)
                    if f.is_valid():

                        inscripcion = Inscripcion.objects.get(id=int(request.POST['inscripcion']))
                        solicitudbeca= SolicitudBeca.objects.get(id=int(request.POST['becaid']))
                        datos = json.loads(request.POST['datos'])
                        archivobeca=None
                        tabadescuento=None
                        for d in datos['detalle']:
                            rubro = Rubro.objects.get(pk=int(d['rubro']))
                            if RubroCuota.objects.filter(rubro=rubro).exists():
                                rubrocuota=RubroCuota.objects.get(rubro=rubro)
                                tabadescuento=  TablaDescuentoBeca(solicitudbeca=solicitudbeca,inscripcion=inscripcion,
                                                                  rubro=rubro,valorubro=rubro.valor,
                                                                  descuento=d['porc'],fecha = datetime.now(),estado=True,
                                                                  usuario=request.user,descripcion=rubro.nombre(),cuota=rubrocuota.cuota)
                            else:


                                tabadescuento=  TablaDescuentoBeca(solicitudbeca=solicitudbeca,inscripcion=inscripcion,
                                                                  rubro=rubro,valorubro=rubro.valor,
                                                                  descuento=d['porc'],fecha = datetime.now(),estado=True,
                                                                  usuario=request.user,descripcion=rubro.nombre(),cuota=0)

                            tabadescuento.save()

                        if 'id_archivoanalisis' in request.FILES:
                            archivobeca= ArchivoSoliciAnalisisBeca(
                                                        solicitudbeca = solicitudbeca,
                                                        archivo = request.FILES['id_archivoanalisis'],
                                                        fecha = datetime.now())

                            archivobeca.save()

                        solicitudbeca.estadosolicitud_id=5
                        solicitudbeca.envioanalisis=True
                        solicitudbeca.save()

                        tabadescuento= TablaDescuentoBeca.objects.filter(solicitudbeca=solicitudbeca)

                        # llenar el log de historial de la solicitud beca
                        loshistorial= HistorialGestionBeca(solicitudbeca=solicitudbeca,inscripcion=solicitudbeca.inscripcion,
                                                                    fecha=datetime.now(),estado_id=3, usuario=request.user,archivoanalisis=archivobeca,comentariocorreo=request.POST['comentario'],
                                                                    tipobeca_id=int(request.POST['idtipobeca']),motivobeca_id=int(request.POST['idtipomotivo']),
                                                                    puntajerenovacion=Decimal(request.POST['puntajerenova']).quantize(Decimal(10)**-2),porcentajebeca=Decimal(request.POST['porcentajebeca']).quantize(Decimal(10)**-2))

                        loshistorial.save()

                        resolucionbeca = Resolucionbeca(solicitudbeca=solicitudbeca,fecha=datetime.now())
                        resolucionbeca.save()
                        numerosolucion= 'ITB-BO-'+str(datetime.now().year)+'-00'+str(resolucionbeca.id)
                        resolucionbeca.numerosolucion=numerosolucion
                        solicitudbeca.idgestion=loshistorial.id
                        solicitudbeca.save()
                        resolucionbeca.save()


                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(solicitudbeca).pk,
                            object_id       = solicitudbeca.id,
                            object_repr     = force_str(solicitudbeca),
                            action_flag     = ADDITION,
                            change_message  = 'Ingreso de analisis solicitud beca (' + client_address + ')' )



                        if EMAIL_ACTIVE:
                            hoy = datetime.now().today()
                            lista=[]
                            if solicitudbeca.inscripcion.tienediscapacidad:

                                lispersona= PersonAutorizaBecaAyuda.objects.filter(personadiscapacidad=True)
                                for list in lispersona:
                                    lista.append([list.correo])
                            else:
                                lispersona= PersonAutorizaBecaAyuda.objects.filter(personadiscapacidad=True)
                                for list in lispersona:
                                    lista.append([list.correo])

                            lista[0][0]=str(lista[0][0])+','+str('dobe@bolivariano.edu.ec')
                            email= str(lista[0][0])


                            send_html_mail('ENVIO DE CORREO PARA ANALISIS DE SOLICITUD',
                                "emails/solicitudanalisis.html", {'solicitudbeca': solicitudbeca, 'archivobeca':archivobeca, 'fecha': hoy,'contenido': 'ANALISIS DE LA SOLICITUD','descuentobeca':tabadescuento,'comentarioanalisis':request.POST['comentario']},email.split(","))

                            return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")

                    else:
                        return HttpResponse(json.dumps({"result":"archivobad"}),content_type="application/json")

                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")


            elif action == 'guardartabladescuentobecarenvio':
                try:

                    f = SolicitudArchivoAyudaForm(request.POST,request.FILES)
                    if f.is_valid():

                        inscripcion = Inscripcion.objects.get(id=int(request.POST['inscripcion']))
                        solicitudbeca= SolicitudBeca.objects.get(id=int(request.POST['becaid']))
                        archivobeca=None
                        tabadescuento= TablaDescuentoBeca.objects.filter(solicitudbeca=solicitudbeca)

                        if 'id_archivoanalisis' in request.FILES:
                            archivobeca= ArchivoSoliciAnalisisBeca(
                                                        solicitudbeca = solicitudbeca,
                                                        archivo = request.FILES['id_archivoanalisis'],
                                                        fecha = datetime.now())

                            archivobeca.save()

                        solicitudbeca.estadosolicitud_id=5
                        solicitudbeca.envioanalisis=True
                        solicitudbeca.save()


                        # llenar el log de historial de la solicitud beca
                        loshistorial= HistorialGestionBeca(solicitudbeca=solicitudbeca,inscripcion=solicitudbeca.inscripcion,
                                                                    fecha=datetime.now(),estado_id=3, usuario=request.user,archivoanalisis=archivobeca,comentariocorreo=request.POST['comentario'],
                                                                    tipobeca_id=int(request.POST['idtipobeca']),motivobeca_id=int(request.POST['idtipomotivo']),
                                                                     puntajerenovacion=Decimal(request.POST['puntajerenova']).quantize(Decimal(10)**-2),
                                                                     porcentajebeca=Decimal(request.POST['porcentajebeca']).quantize(Decimal(10)**-2))
                        loshistorial.save()

                        solicitudbeca.idgestion=loshistorial.id
                        solicitudbeca.save()


                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(solicitudbeca).pk,
                            object_id       = solicitudbeca.id,
                            object_repr     = force_str(solicitudbeca),
                            action_flag     = ADDITION,
                            change_message  = 'Renvio de analaisis de beca (' + client_address + ')' )



                        if EMAIL_ACTIVE:
                            hoy = datetime.now().today()
                            lista=[]
                            if solicitudbeca.inscripcion.tienediscapacidad:

                                lispersona= PersonAutorizaBecaAyuda.objects.filter(personadiscapacidad=True)
                                for list in lispersona:
                                    lista.append([list.correo])
                            else:
                                lispersona= PersonAutorizaBecaAyuda.objects.filter(personadiscapacidad=True)
                                for list in lispersona:
                                    lista.append([list.correo])

                            lista[0][0]=str(lista[0][0])+','+str('dobe@bolivariano.edu.ec')
                            email= str(lista[0][0])

                            send_html_mail('ENVIO DE CORREO PARA ANALISIS DE SOLICITUD',
                                "emails/solicitudanalisis.html", {'solicitudbeca': solicitudbeca, 'archivobeca':archivobeca, 'fecha': hoy,'contenido': 'ANALISIS DE LA SOLICITUD','descuentobeca':tabadescuento,'comentarioanalisis':request.POST['comentario']},email.split(","))

                            return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")

                    else:
                        return HttpResponse(json.dumps({"result":"archivobad"}),content_type="application/json")

                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")


            elif action == 'guardareditartabladescuentobeca':
                try:

                    f = SolicitudArchivoAyudaForm(request.POST, request.FILES)
                    if f.is_valid():

                        solicitudbeca = SolicitudBeca.objects.get(id=int(request.POST['becaid']))
                        archivobeca = None
                        tabadescuento = TablaDescuentoBeca.objects.filter(solicitudbeca=solicitudbeca)

                        if 'id_archivoanalisis' in request.FILES:
                            archivobeca = ArchivoSoliciAnalisisBeca(
                                solicitudbeca=solicitudbeca,
                                archivo=request.FILES['id_archivoanalisis'],
                                fecha=datetime.now())

                            # archivobeca.save()

                        datoshistorial=HistorialGestionBeca.objects.get(pk=int(request.POST['idhistorial']))

                        if 'id_archivoanalisis' in request.FILES:
                            datoshistorial.archivoanalisis=archivobeca

                        datoshistorial.comentariocorreo=request.POST['comentario']
                        datoshistorial.tipobeca_id=int(request.POST['idtipobeca'])
                        datoshistorial.motivobeca_id=int(request.POST['idtipomotivo'])
                        datoshistorial.porcentajebeca=Decimal(request.POST['porcentajebeca']).quantize(Decimal(10) ** -2)
                        datoshistorial.puntajerenovacion=Decimal(request.POST['puntajerenova']).quantize(Decimal(10) ** -2)

                        datoshistorial.save()

                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id=request.user.pk,
                            content_type_id=ContentType.objects.get_for_model(solicitudbeca).pk,
                            object_id=solicitudbeca.id,
                            object_repr=force_str(solicitudbeca),
                            action_flag=CHANGE,
                            change_message='Analisis de Beca Editado (' + client_address + ')')

                        if EMAIL_ACTIVE:
                            hoy = datetime.now().today()
                            lista = []
                            if solicitudbeca.inscripcion.tienediscapacidad:

                                lispersona = PersonAutorizaBecaAyuda.objects.filter(personadiscapacidad=True)
                                for list in lispersona:
                                    lista.append([list.correo])
                            else:
                                lispersona = PersonAutorizaBecaAyuda.objects.filter(personadiscapacidad=True)
                                for list in lispersona:
                                    lista.append([list.correo])

                            lista[0][0] = str(lista[0][0]) + ',' + str('dobe@bolivariano.edu.ec')
                            email = str(lista[0][0])



                            send_html_mail('ENVIO DE CORREO  ANALISIS DE SOLICITUD POR EDICION',
                                           "emails/solicitudanalisis.html",
                                           {'solicitudbeca': solicitudbeca, 'archivobeca': archivobeca, 'fecha': hoy,
                                            'contenido': 'ANALISIS DE LA SOLICITUD EDITADA', 'descuentobeca': tabadescuento,
                                            'comentarioanalisis': elimina_tildes(request.POST['comentario'])}, email.split(","))

                            return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")

                    else:
                         return HttpResponse(json.dumps({"result":"archivobad"}),content_type="application/json")

                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")




            elif action == 'guardarmanualtabladescuentobeca':
                try:

                    rubro = Rubro.objects.get(pk=int(request.POST['rubroid']))

                    if Pago.objects.filter(rubro=rubro).exists():
                        if request.POST['porcentaje']>=100:
                            return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

                    solicitudbeca= SolicitudBeca.objects.get(id=int(request.POST['becaid']))

                    if not TablaDescuentoBeca.objects.filter(solicitudbeca=solicitudbeca, rubro=rubro).exists():
                        if RubroCuota.objects.filter(rubro=rubro).exists():
                            rubrocuota=RubroCuota.objects.get(rubro=rubro)
                            tabadescuento=  TablaDescuentoBeca(solicitudbeca=solicitudbeca,inscripcion=solicitudbeca.inscripcion,
                                                          rubro=rubro,valorubro=rubro.valor,
                                                          descuento=request.POST['porcentaje'],fecha = datetime.now(),estado=True,
                                                          usuario=request.user,cuota=rubrocuota.cuota,descripcion=rubro.nombre())
                        elif RubroMatricula.objects.filter(rubro=rubro).exists() :
                            # rubrocuota=RubroMatricula.objects.get(rubro=rubro)
                            tabadescuento=  TablaDescuentoBeca(solicitudbeca=solicitudbeca,inscripcion=solicitudbeca.inscripcion,
                                                          rubro=rubro,valorubro=rubro.valor,
                                                          descuento=request.POST['porcentaje'],fecha = datetime.now(),estado=True,
                                                          usuario=request.user,cuota=0,descripcion=rubro.nombre())

                        else:
                            # rubroinscripcion=RubroInscripcion.objects.get(rubro=rubro)
                            tabadescuento=  TablaDescuentoBeca(solicitudbeca=solicitudbeca,inscripcion=solicitudbeca.inscripcion,
                                                          rubro=rubro,valorubro=rubro.valor,
                                                          descuento=request.POST['porcentaje'],fecha = datetime.now(),estado=True,
                                                          usuario=request.user,cuota=0,descripcion=rubro.nombre())


                        tabadescuento.save()
                    else:

                         return HttpResponse(json.dumps({"result":"bad1"}),content_type="application/json")

                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(solicitudbeca).pk,
                        object_id       = solicitudbeca.id,
                        object_repr     = force_str(solicitudbeca),
                        action_flag     = ADDITION,
                        change_message  = 'Se ingreso rubo manual a la tabla de descuento solictud beca (' + client_address + ')' )

                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")




            elif action == 'guardareditartabladescuentobecarubro':
                try:

                    tabadescuento=  TablaDescuentoBeca.objects.get(id=int(request.POST['rubroid']))
                    if Pago.objects.filter(rubro=tabadescuento.rubro).exists():
                        if request.POST['porcentaje']>=100:
                            return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

                    tabadescuento.descuento=request.POST['porcentaje']
                    tabadescuento.save()
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(tabadescuento).pk,
                        object_id       = tabadescuento.id,
                        object_repr     = force_str(tabadescuento),
                        action_flag     = CHANGE,
                        change_message  = 'Edicion tabla de descuento solictud beca (' + client_address + ')' )

                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

            elif action == 'eliminarrubro':
                try:

                    tabadescuento=  TablaDescuentoBeca.objects.get(id=int(request.POST['rubroid']))
                    tabadescuento.delete()

                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(tabadescuento).pk,
                        object_id       = tabadescuento.id,
                        object_repr     = force_str(tabadescuento),
                        action_flag     = CHANGE,
                        change_message  = 'Eliminacion rubro tabla de descuento solictud beca (' + client_address + ')' )

                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")


            elif action == 'aprobratabladescuento':
                try:
                    inscripcion = Inscripcion.objects.get(id=int(request.POST['inscripcion']))
                    solicitudbeca= SolicitudBeca.objects.get(id=int(request.POST['becaid']))

                    # llenar el log de historial de la solicitud beca
                    loshistorial= HistorialGestionBeca(solicitudbeca=solicitudbeca,inscripcion=solicitudbeca.inscripcion,
                                                                fecha=datetime.now(),estado_id=20, usuario=request.user,comentariocorreo='APROBACION DE TABLA DE DESCUENTO DE BECA POR JEFE DOBE')
                    loshistorial.save()

                    solicitudbeca.asignaciontarficadescuento=True
                    solicitudbeca.idgestion=loshistorial.id
                    solicitudbeca.save()

                    resolucionbeca = Resolucionbeca.objects.filtro(solicitudbeca=solicitudbeca).order_by('-id')[:1].get()
                    resolucionbeca.fechaprobacion=datetime.now()
                    resolucionbeca.estado=True
                    resolucionbeca.save()

                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(solicitudbeca).pk,
                        object_id       = solicitudbeca.id,
                        object_repr     = force_str(solicitudbeca),
                        action_flag     = ADDITION,
                        change_message  = 'Aprobacion tabla de descuento solictud beca (' + client_address + ')' )

                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")


            elif action == 'rechazartabladescuento':
                try:
                    inscripcion = Inscripcion.objects.get(id=int(request.POST['inscripcion']))
                    solicitudbeca= SolicitudBeca.objects.get(id=int(request.POST['becaid']))

                    # llenar el log de historial de la solicitud beca
                    loshistorial= HistorialGestionBeca(solicitudbeca=solicitudbeca,inscripcion=solicitudbeca.inscripcion,
                                                                fecha=datetime.now(),estado_id=21, usuario=request.user,comentariocorreo='APROBACION DE TABLA DE DESCUENTO DE BECA POR JEFE DOBE')
                    loshistorial.save()

                    solicitudbeca.asignaciontarficadescuento=False
                    solicitudbeca.envioanalisis=False
                    solicitudbeca.idgestion=loshistorial.id
                    solicitudbeca.save()

                    resolucionbeca = Resolucionbeca.objects.filter(solicitudbeca=solicitudbeca).order_by('-id')[:1].get()
                    resolucionbeca.estado=False
                    resolucionbeca.save()

                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(solicitudbeca).pk,
                        object_id       = solicitudbeca.id,
                        object_repr     = force_str(solicitudbeca),
                        action_flag     = ADDITION,
                        change_message  = 'Rechazo tabla de descuento solictud beca (' + client_address + ')' )

                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")




            elif action == 'addsolicitud':
                f = SolicitudBecaForm(request.POST,request.FILES)
                inscripcion = Inscripcion.objects.get(id=request.POST['inscrip'])
                autorizacionbode= False
                autorizacionbecasenecyt= False

                if inscripcion.autorizacionbecadobe:
                    autorizacionbode=True

                if inscripcion.autorizacionbecasenecyt:
                    autorizacionbecasenecyt=True
                puntaje = 0
                idsoli=0
                try:
                    solicitudbeca = None
                    archivobeca = None
                    matriculaac=''
                    if f.is_valid():
                        nivel = None
                        if Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=False).exists():
                            matriculaactual = Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=False).order_by('-fecha')[:1].get()
                            nivel = matriculaactual.nivel
                        if Matricula.objects.filter(Q(nivel__cerrado=True) | Q(liberada=True),inscripcion = inscripcion).exists():

                            if autorizacionbode==False and autorizacionbecasenecyt==False:

                                matriculaac = Matricula.objects.filter(Q(nivel__cerrado=True) | Q(liberada=True),inscripcion = inscripcion).order_by('-fecha')[:1].get()
                                #validar que sean de nivel diferente
                                if inscripcion.matricula().nivel.nivelmalla_id==matriculaac.nivel.nivelmalla_id:
                                    if inscripcion.matricula().nivel.nivelmalla_id>1:
                                        matriculaac = Matricula.objects.filter(Q(nivel__cerrado=True) | Q(liberada=True),inscripcion = inscripcion,nivel__nivelmalla__id =inscripcion.matricula().nivel.nivelmalla_id).order_by('-fecha')[:1].get()
                                nivelmalla= matriculaac.nivel.nivelmalla
                                malla=matriculaac.nivel.malla
                                idasigntauramalla = AsignaturaMalla.objects.filter(asignatura__promedia=True,malla=malla,nivelmalla=nivelmalla).values('asignatura_id')
                                lista = RecordAcademico.objects.filter(inscripcion__id=matriculaac.inscripcion_id,asignatura__promedia=True,asignatura__id__in=idasigntauramalla,aprobada=True)
                                sumanota = 0
                                for recordacedmi in lista:
                                    datarecor= RecordAcademico.objects.get(pk=recordacedmi.id)
                                    sumanota=sumanota+datarecor.nota

                                puntaje = Decimal(sumanota/len(idasigntauramalla)).quantize(Decimal(10)**-2)


                        # validar que no tenga solicitud de beca ingresada ya en el nivel
                        if SolicitudBeca.objects.filter(inscripcion = inscripcion,nivel=inscripcion.matricula().nivel,tiposolicitud=2).exists():
                            if not SolicitudBeca.objects.filter(nivel=inscripcion.matricula().nivel,inscripcion=inscripcion,tiposolicitud=2,estadosolicitud=3,aprobado=False,eliminado=True).exists():
                                return HttpResponseRedirect("/?info=No puede acceder a una beca porque tiene una solicitud de ayuda financiera ingresada en el nivel matriculado")


                        #OCU 12-enero-2017 presentar mensaje a estudiante de no acceso a beca por puntaje
                        if matriculaac:
                            if matriculaac.tipobeneficio==TipoBeneficio.objects.get(pk=TIPO_BECA_SENESCYT) or matriculaac.tipobeca==TipoBeca.objects.get(pk=7):
                                auxmateria=True
                            else:
                                auxmateria=False
                        else:
                            auxmateria=False
                        if puntaje >= PUNTAJE_BECA_NORMAL or inscripcion.tienediscapacidad or not inscripcion.empresaconvenio== None or auxmateria or autorizacionbode or autorizacionbecasenecyt  :
                            if 'edit' in request.POST and puntaje:
                                solicitudbeca = SolicitudBeca.objects.get(id = request.POST['edit'])
                                solicitudbeca.motivo =  f.cleaned_data['motivo']
                                # solicitudbeca.nivel = nivel
                                solicitudbeca.puntaje = puntaje
                                solicitudbeca.fecha = datetime.now()
                                mensaje = 'Edicion'
                            elif SolicitudBeca.objects.filter(inscripcion=inscripcion,nivel=nivel,estadosolicitud__id=3,aprobado=False,eliminado=True).exists():
                                if not SolicitudBeca.objects.filter(inscripcion=inscripcion,nivel=nivel,estadosolicitud__id=3,aprobado=False,eliminado=True).exists():
                                      return HttpResponseRedirect("/?info=Su solicitud de beca esta ingresada, por favor verique en su SGA el estado de la misma, el dpto. de Bienestar estudiantil se comunicara con Ud")
                                else:
                                     if SolicitudBeca.objects.filter().exists():
                                        idsoli= SolicitudBeca.objects.filter().order_by('-id')[:1].get().id +1
                                     else:
                                        idsoli=1

                                     mensaje = 'Ingreso'
                                     solicitudbeca = SolicitudBeca(id=idsoli,
                                                                inscripcion = inscripcion,
                                                                motivo =  f.cleaned_data['motivo'],
                                                                nivel = nivel,
                                                                puntaje = puntaje,
                                                                estadosolicitud_id=1,
                                                                fecha = datetime.now(),
                                                                estadoverificaciondoc=False)
                            else:
                                if SolicitudBeca.objects.filter().exists():
                                    idsoli= SolicitudBeca.objects.filter().order_by('-id')[:1].get().id +1
                                else:
                                    idsoli=1
                                mensaje = 'Ingreso'
                                solicitudbeca = SolicitudBeca(id=idsoli,
                                                            inscripcion = inscripcion,
                                                            motivo =  f.cleaned_data['motivo'],
                                                            nivel = nivel,
                                                            puntaje = puntaje,
                                                            estadosolicitud_id=1,
                                                            fecha = datetime.now(),
                                                            estadoverificaciondoc=False)
                            solicitudbeca.save()

                            if 'archivo' in request.FILES:
                                if ArchivoSoliciBeca.objects.filter().exists():
                                    idarch= ArchivoSoliciBeca.objects.filter().order_by('-id')[:1].get().id +1
                                else:
                                    idarch=1
                                archivobeca= ArchivoSoliciBeca(id=idarch,
                                                        solicitudbeca = solicitudbeca,
                                                        tipodocumenbeca = f.cleaned_data['tipo'],
                                                        archivo = request.FILES['archivo'],
                                                        fecha = datetime.now())
                                archivobeca.save()
                        else:
                            return HttpResponseRedirect("/?info=No puede acceder a una beca puntaje actual es: "+str(decimal.Decimal(puntaje)))
                    else:
                        if 'archivo' in f.errors:
                             return HttpResponseRedirect("/beca_solicitud?action=addsolibeca&error=EL tipo de archivo no tiene el formato correcto&id="+str(inscripcion.id))
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(solicitudbeca).pk,
                    object_id       = solicitudbeca.id,
                    object_repr     = force_str(solicitudbeca),
                    action_flag     = ADDITION,
                    change_message  = mensaje +' de Solicitude de Beca (' + client_address + ')' )
                    if EMAIL_ACTIVE:
                        lista = str('dobe@bolivariano.edu.ec')
                        # lista = str('ocastillo@bolivariano.edu.ec')
                        hoy = datetime.now().today()
                        contenido = "SOLICITUD DE BECA"
                        send_html_mail(contenido,
                            "emails/solicitudbeca.html", {'solicitudbeca': solicitudbeca, 'fecha': hoy,'contenido': contenido},lista.split(','))

                    data = {'title':'Solicitud de beca'}
                    data['title'] = 'Adjuntos Archivos a la  Solicitud de Beca'
                    data['form'] = SolicitudBecaFormAddArchivo()
                    data['solicitudbeca']=solicitudbeca

                    return render(request ,"beca_solicitud/addarchivosolibeca.html" ,  data)

                except Exception as ex:
                    if solicitudbeca:
                        solicitudbeca.delete()
                    if archivobeca:
                        archivobeca.delete()
                    return HttpResponseRedirect("/beca_solicitud?action=addsolibeca&error=Ocurrio un error intentelo nuevamente&id="+str(inscripcion.id))


            elif action == 'addarchivosolicitud':
                f = SolicitudBecaFormAddArchivo(request.POST,request.FILES)
                solicitudbeca = SolicitudBeca.objects.get(id=request.POST['idsolicitudbeca'])

                if f.is_valid():


                    if 'cedula' in request.FILES:
                        cedula= request.FILES['cedula']

                        archivobeca= ArchivoSoliciBeca(
                                                        solicitudbeca = solicitudbeca,
                                                        tipodocumenbeca_id = 2,
                                                        archivo = cedula,
                                                        fecha = datetime.now())
                        archivobeca.save()

                    if 'cedulahijo' in request.FILES:
                        cedulahijo= request.FILES['cedulahijo']

                        archivobeca= ArchivoSoliciBeca(
                                                        solicitudbeca = solicitudbeca,
                                                        tipodocumenbeca_id = 5,
                                                        archivo = cedulahijo,
                                                        fecha = datetime.now())
                        archivobeca.save()

                    if 'rolpago' in request.FILES:
                        rolpago= request.FILES['rolpago']

                        archivobeca= ArchivoSoliciBeca(
                                                        solicitudbeca = solicitudbeca,
                                                        tipodocumenbeca_id = 6,
                                                        archivo = rolpago,
                                                        fecha = datetime.now())
                        archivobeca.save()


                    if 'partidanacimiento' in request.FILES:
                        partidanacimiento= request.FILES['partidanacimiento']

                        archivobeca= ArchivoSoliciBeca(
                                                        solicitudbeca = solicitudbeca,
                                                        tipodocumenbeca_id = 4,
                                                        archivo = partidanacimiento,
                                                        fecha = datetime.now())
                        archivobeca.save()

                    if 'carnetdiscapacidad' in request.FILES:
                        carnetdiscapacidad= request.FILES['carnetdiscapacidad']

                        archivobeca= ArchivoSoliciBeca(
                                                        solicitudbeca = solicitudbeca,
                                                        tipodocumenbeca_id = 3,
                                                        archivo = carnetdiscapacidad,
                                                        fecha = datetime.now())
                        archivobeca.save()


                    if 'certificado' in request.FILES:
                        certificado= request.FILES['certificado']

                        archivobeca= ArchivoSoliciBeca(
                                                        solicitudbeca = solicitudbeca,
                                                        tipodocumenbeca_id = 8,
                                                        archivo = certificado,
                                                        fecha = datetime.now())
                        archivobeca.save()


                    return HttpResponseRedirect("/beca_solicitud")


                else:
                     return HttpResponseRedirect("/beca_solicitud?error=EL tipo de archivo no tiene el formato correcto&id="+str(solicitudbeca.inscripcion.id))




            elif action == 'addsolicitudrenovar':
                f = SolicitudBecaRenovarForm(request.POST,request.FILES)
                inscripcion = Inscripcion.objects.get(id=request.POST['inscrip'])
                autorizacionbode= False
                autorizacionbecasenecyt=False

                if inscripcion.autorizacionbecadobe:
                    autorizacionbode=True

                if inscripcion.autorizacionbecasenecyt:
                    autorizacionbecasenecyt=True

                #OCastillo 19-05-2023 solo con la promocion todos los niveles no puede acceder a beca
                if inscripcion.promocion!=None:
                    if inscripcion.promocion.todos_niveles:
                        return HttpResponseRedirect("/?info=No puede acceder a una beca porque tiene una promocion para todos los niveles " + str(inscripcion.promocion.descripcion))
                    # else:
                    #    if inscripcion.matricula().nivel.nivelmalla_id==NIVEL_MALLA_UNO:
                    #        return HttpResponseRedirect("/?info=No puede acceder a una beca porque tiene una promocion " + str(inscripcion.promocion.descripcion))
                    #


                puntaje = 0
                try:
                    solicitudbeca = None
                    archivobeca = None
                    if f.is_valid():
                        nivel = None
                        if Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=False).exists():
                            matriculaactual = Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=False).order_by('-fecha')[:1].get()
                            nivel = matriculaactual.nivel
                        if Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=True).exists():
                            if Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=True).exclude(liberada=True).exists():
                                matriculaac = Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=True).exclude(liberada=True).order_by('-fecha')[:1].get()
                            else:
                                matriculaac = Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=True).order_by('-fecha')[:1].get()
                            #validar que sean de nivel diferente
                            if inscripcion.matricula().nivel.nivelmalla_id==matriculaac.nivel.nivelmalla_id:
                                if inscripcion.matricula().nivel.nivelmalla_id>1:
                                    matriculaac = Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=True,nivel__nivelmalla__id =inscripcion.matricula().nivel.nivelmalla_id).order_by('-fecha')[:1].get()
                            nivelmalla= matriculaac.nivel.nivelmalla
                            malla=matriculaac.nivel.malla
                            idasigntauramalla = AsignaturaMalla.objects.filter(asignatura__promedia=True,malla=malla,nivelmalla=nivelmalla).values('asignatura_id')
                            lista = RecordAcademico.objects.filter(inscripcion__id=matriculaac.inscripcion_id,asignatura__promedia=True,asignatura__id__in=idasigntauramalla,aprobada=True)
                            sumanota = 0
                            for recordacedmi in lista:
                                datarecor= RecordAcademico.objects.get(pk=recordacedmi.id)
                                sumanota=sumanota+datarecor.nota

                        # validar que no tenga solicitud de beca ingresada ya en el nivel
                        if SolicitudBeca.objects.filter(inscripcion = inscripcion,nivel=inscripcion.matricula().nivel,tiposolicitud=2).exists():
                            if not SolicitudBeca.objects.filter(nivel=inscripcion.matricula().nivel,inscripcion=inscripcion,tiposolicitud=2,estadosolicitud__id=3,aprobado=False,eliminado=True).exists():
                                return HttpResponseRedirect("/?info=No puede acceder a una beca porque tiene una solicitud de ayuda financiera ingresada en el nivel matriculado")

                        puntaje = Decimal(sumanota/len(idasigntauramalla)).quantize(Decimal(10)**-2)
                        #OCU 12-enero-2017 presentar mensaje a estudiante de no acceso a beca por puntaje
                        if matriculaac:
                            if matriculaac.tipobeneficio==TipoBeneficio.objects.get(pk=TIPO_BECA_SENESCYT) or matriculaac.tipobeca==TipoBeca.objects.get(pk=7):
                                auxmateria=True
                            else:
                                auxmateria=False
                        else:
                            auxmateria=False
                        if puntaje >= PUNTAJE_BECA_NORMAL or inscripcion.tienediscapacidad or not inscripcion.empresaconvenio== None or auxmateria or autorizacionbode or autorizacionbecasenecyt :
                            if 'edit' in request.POST and puntaje:
                                solicitudbeca = SolicitudBeca.objects.get(id = request.POST['edit'])
                                solicitudbeca.motivo =  f.cleaned_data['motivo']
                                # solicitudbeca.nivel = nivel
                                solicitudbeca.puntaje = puntaje
                                solicitudbeca.fecha = datetime.now()
                                mensaje = 'Edicion'
                            elif SolicitudBeca.objects.filter(inscripcion=inscripcion,nivel=nivel,estadosolicitud__id=3,aprobado=False,eliminado=True).exists():
                                if not SolicitudBeca.objects.filter(inscripcion=inscripcion,nivel=nivel,estadosolicitud__id=3,aprobado=False,eliminado=True).exists():
                                      return HttpResponseRedirect("/?info=Su solicitud de beca esta ingresada, por favor verique en su SGA el estado de la misma, el dpto. de Bienestar estudiantil se comunicara con Ud")
                                else:
                                    if SolicitudBeca.objects.filter().exists():
                                        idsoli= SolicitudBeca.objects.filter().order_by('-id')[:1].get().id +1
                                    else:
                                        idsoli=1

                                    mensaje = 'Ingreso'
                                    solicitudbeca = SolicitudBeca(id=idsoli,
                                                                inscripcion = inscripcion,
                                                                motivo =  f.cleaned_data['motivo'],
                                                                nivel = nivel,
                                                                puntaje = puntaje,
                                                                estadosolicitud_id=1,
                                                                fecha = datetime.now(),
                                                                estadoverificaciondoc=False)
                            else:
                                if SolicitudBeca.objects.filter().exists():
                                    idsoli= SolicitudBeca.objects.filter().order_by('-id')[:1].get().id +1
                                else:
                                    idsoli=1
                                mensaje = 'Ingreso'


                                solicitudbeca = SolicitudBeca(id=idsoli,
                                                            inscripcion = inscripcion,
                                                            motivo =  f.cleaned_data['motivo'],
                                                            nivel = inscripcion.matricula().nivel,
                                                            puntaje = puntaje,
                                                            renovarbeca=True,
                                                            estadosolicitud_id=1,
                                                            fecha = datetime.now(),
                                                            estadoverificaciondoc=False)
                            solicitudbeca.save()

                            if 'archivo' in request.FILES:
                                if ArchivoSoliciBeca.objects.filter().exists():
                                    idarch= ArchivoSoliciBeca.objects.filter().order_by('-id')[:1].get().id +1
                                else:
                                    idarch=1
                                archivobeca= ArchivoSoliciBeca(id=idarch,
                                                        solicitudbeca = solicitudbeca,
                                                        tipodocumenbeca = f.cleaned_data['tipo'],
                                                        archivo = request.FILES['archivo'],
                                                        fecha = datetime.now())
                                archivobeca.save()
                        else:
                            return HttpResponseRedirect("/?info=No puede acceder a una beca puntaje actual es: "+str(decimal.Decimal(puntaje)))
                    else:
                        if 'archivo' in f.errors:
                             return HttpResponseRedirect("/beca_solicitud?action=addsolibecanenovar&error=EL tipo de archivo no tiene el formato correcto&id="+str(inscripcion.id))
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(solicitudbeca).pk,
                    object_id       = solicitudbeca.id,
                    object_repr     = force_str(solicitudbeca),
                    action_flag     = ADDITION,
                    change_message  = mensaje +' de Solicitude de Renovacion Beca (' + client_address + ')' )
                    if EMAIL_ACTIVE:
                        lista = str('dobe@bolivariano.edu.ec')
                        # lista = str('ocastillo@bolivariano.edu.ec')
                        hoy = datetime.now().today()
                        contenido = "SOLICITUD DE RENOVACION DE BECA"
                        send_html_mail(contenido,
                            "emails/solicitudbeca.html", {'solicitudbeca': solicitudbeca, 'fecha': hoy,'contenido': contenido},lista.split(','))

                    data = {'title':'Renovacion Solicitud de beca'}
                    data['title'] = 'Adjuntos Archivos a la  Solicitud de Beca'
                    data['form'] = SolicitudBecaFormAddArchivo()
                    data['solicitudbeca']=solicitudbeca

                    return render(request ,"beca_solicitud/addarchivosolibeca.html" ,  data)

                    # return HttpResponseRedirect("/beca_solicitud")

                except Exception as ex:
                    if solicitudbeca:
                        solicitudbeca.delete()
                    if archivobeca:
                        archivobeca.delete()
                    return HttpResponseRedirect("/beca_solicitud?action=addsolibecanenovar&error=Ocurrio un error intentelo nuevamente&id="+str(inscripcion.id))

            elif action == 'addcroquis':
                f = CroquisForm(request.POST,request.FILES)
                if f.is_valid():
                    inscripficha = InscripcionFichaSocioEconomicaBeca.objects.get(id=request.POST['inscficha'])
                    if 'croquis' in request.FILES:
                        archivo = request.FILES['croquis']
                        if inscripficha.croquis :
                            mensaje = 'Editado'
                            if (MEDIA_ROOT + '/' + str(inscripficha.croquis)) and archivo:
                                os.remove(MEDIA_ROOT + '/' + str(inscripficha.croquis))
                        else:
                            mensaje = 'Adicionado'
                        inscripficha.croquis = archivo
                        inscripficha.save()



                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(inscripficha).pk,
                        object_id       = inscripficha.id,
                        object_repr     = force_str(inscripficha),
                        action_flag     = ADDITION,
                        change_message  = mensaje +' Croquis (' + client_address + ')' )

                    return HttpResponseRedirect('/beca_solicitud?action=fichasocioecono&id='+str(inscripficha.inscripcion.id)+'&pag=4')
                else:
                    return HttpResponseRedirect('/beca_solicitud?error=el archivo no tiene el formato correcto')



            elif action == 'addarchivo':
                # f = SolicitudBecaForm(request.POST,request.FILES)
                f = SolicitudBecaNuevaForm(request.POST,request.FILES)
                if f.is_valid():
                    solicitudbeca = SolicitudBeca.objects.get(id=request.POST['idsoliciar'])
                    if 'archivo' in request.FILES:
                        archivo = request.FILES['archivo']
                    else:
                        archivo = ''
                    # if ArchivoSoliciBeca.objects.filter().exists():
                    #     idarch= ArchivoSoliciBeca.objects.filter().order_by('-fecha')[:1].get().id +1
                    # else:
                    #     idarch=1
                    if request.POST['editararch'] == '0':
                        try:
                            archivobeca= ArchivoSoliciBeca(
                                                        solicitudbeca = solicitudbeca,
                                                        tipodocumenbeca = f.cleaned_data['tipo'],
                                                        archivo = request.FILES['archivo'],
                                                        fecha = datetime.now())
                            mensaje = 'Ingreso'
                            archivobeca.save()

                        except Exception as ex:
                             return HttpResponseRedirect('/beca_solicitud?error=problema al guardar el archivo')

                        # llenar el log de historial de la solicitud beca
                        loshistorial= HistorialGestionBeca(solicitudbeca=solicitudbeca,inscripcion=solicitudbeca.inscripcion,
                                                                    fecha=datetime.now(),estado_id=6, usuario=request.user,archivosubeestudiante=archivobeca)
                        loshistorial.save()
                        solicitudbeca.idgestion=loshistorial.id
                        solicitudbeca.save()
                        contenido = "EL ESTUDIANTE ADJUNTO ARCHIVO " + str(f.cleaned_data['tipo'])

                    else:
                        archivobeca = ArchivoSoliciBeca.objects.get(id = request.POST['editararch'])

                        if str(archivobeca.archivo):
                            if (MEDIA_ROOT + '/' + str(archivobeca.archivo)) and archivo:
                                os.remove(MEDIA_ROOT + '/' + str(archivobeca.archivo))

                        if archivo:
                            archivobeca.archivo = archivo
                            archivobeca.fecha = datetime.now()
                        archivobeca.tipodocumenbeca_id = request.POST['tipo']

                        mensaje = 'Edicion'
                        archivobeca.save()
                        loshistorial= HistorialGestionBeca(solicitudbeca=solicitudbeca,inscripcion=solicitudbeca.inscripcion,
                                                                    fecha=datetime.now(),estado_id=7, usuario=request.user,archivosubeestudiante=archivobeca)
                        loshistorial.save()
                        solicitudbeca.idgestion=loshistorial.id
                        solicitudbeca.save()

                        contenido = "EL ESTUDIANTE EDITO ADJUNTO ARCHIVO " + str(f.cleaned_data['tipo'])

                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(archivobeca).pk,
                        object_id       = archivobeca.id,
                        object_repr     = force_str(archivobeca),
                        action_flag     = ADDITION,
                        change_message  = mensaje +' archivo de Resolucion (' + client_address + ')' )

                    if EMAIL_ACTIVE:
                        hoy = datetime.now().today()
                        lista=[]
                        if solicitudbeca.inscripcion.tienediscapacidad:

                            lispersona= PersonAutorizaBecaAyuda.objects.filter(personadiscapacidad=True)
                            for list in lispersona:
                                lista.append([list.correo])
                        else:
                            lispersona= PersonAutorizaBecaAyuda.objects.filter(personadiscapacidad=True)
                            for list in lispersona:
                                lista.append([list.correo])

                        lista[0][0]=str(lista[0][0])+','+str('dobe@bolivariano.edu.ec')
                        email= str(lista[0][0])

                        send_html_mail(contenido,
                            "emails/solicitudbecarchivo.html", {'solicitudbeca': solicitudbeca, 'archivobeca':archivobeca, 'fecha': hoy,'contenido': contenido},email.split(","))

                    if request.POST['editararch'] == '0':
                        return HttpResponseRedirect('/beca_solicitud')
                    else:
                        return HttpResponseRedirect('/beca_solicitud?edit='+str(request.POST['editararch']))
                else:
                    return HttpResponseRedirect('/beca_solicitud?error=el archivo no tiene el formato correcto')

            elif action == 'addrespuest':
                solicitudbeca = SolicitudBeca.objects.get(id=request.POST['idsolicires'])
                f = ResponSolicBecaForm(request.POST,request.FILES)
                if f.is_valid():

                    if f.cleaned_data['aprobado']==True:
                        if solicitudbeca.asignaciontarficadescuento==False or solicitudbeca.asignaciontarficadescuento==None :
                            data = {'title':'Solicitud de beca'}
                            solicitudbecaotra = SolicitudBeca.objects.filter(inscripcion=solicitudbeca.inscripcion,tiposolicitud=1).order_by('-fecha')
                            data['solicitudbecas'] = solicitudbecaotra
                            data['TIPO_ESPECIE_BECA'] = TIPO_ESPECIE_BECA
                            data['form1'] = ResponSolicBecaForm()
                            data['hoy'] = datetime.now()
                            # data['form'] = AusenciaJustificadaForm(initial={'fechae': datetime.now().strftime("%d-%m-%Y")})
                            data['form'] = AusenciaJustificadaForm()
                            data['infoaprueba'] = True



                            personaautoriza= Persona.objects.get(usuario=request.user)
                            if PersonAutorizaBecaAyuda.objects.filter(persona=personaautoriza,personadiscapacidad=True).exists():
                                data['autorizaapurebadis'] = True
                                data['autorizaapurebanodis'] = True
                                data['aux'] = False
                                data['enviosecr'] = True
                                data['noveringresotabla'] = False

                            if PersonAutorizaBecaAyuda.objects.filter(persona=personaautoriza,personadiscapacidad=False).exists():
                                data['autorizaapurebanodis'] = True
                                data['autorizaapurebadis'] = True
                                data['aux'] = False
                                data['enviosecr'] = True
                                data['noveringresotabla'] = False

                            usuario = User.objects.get(pk=request.user.id)

                            if usuario.groups.filter(id__in=[SECRETARIAGENERAL_GROUP_ID ]).exists():
                                data['secretaria'] = True


                            if usuario.groups.filter(id__in=[SISTEMAS_GROUP_ID ]).exists():
                                data['permitiraprobacion'] = True
                                data['autorizaapurebadis'] = False
                                data['autorizaapurebanodis'] = False
                                data['aux'] = False

                            if usuario.groups.filter(id__in=[DOBE_GROUP_ID ]).exists():
                                data['aux'] = False
                                data['noveringresotabla'] = True




                            data['form31'] = SolicitudBecaNuevaForm()
                            return render(request ,"beca_solicitud/beca_solicitud.html" ,  data)




                    solicitudbeca.aprobado = f.cleaned_data['aprobado']
                    solicitudbeca.observacion = f.cleaned_data['observacion']
                    solicitudbeca.fechaproces = datetime.now()
                    solicitudbeca.usuario = request.user
                    solicitudbeca.estadosolicitud_id=3

                    if solicitudbeca.aprobado:
                        mensaje="aprobada"
                    else:
                        mensaje = "no aprobada"
                        solicitudbeca.asignaciontarficadescuento=False

                    solicitudbeca.save()



                    # llenar el log de historial de la solicitud beca
                    loshistorial= HistorialGestionBeca(solicitudbeca=solicitudbeca,inscripcion=solicitudbeca.inscripcion,
                                                                fecha=datetime.now(),estado_id=1, usuario=request.user,aprobado=solicitudbeca.aprobado)
                    loshistorial.save()
                    solicitudbeca.idgestion=loshistorial.id
                    solicitudbeca.save()

                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(solicitudbeca).pk,
                        object_id       = solicitudbeca.id,
                        object_repr     = force_str(solicitudbeca),
                        action_flag     = ADDITION,
                        change_message  = 'Solicitud de beca '+ mensaje +' (' + client_address + ')' )
                    if EMAIL_ACTIVE:
                        if solicitudbeca.inscripcion.persona.emailinst:
                            if solicitudbeca.aprobado:
                               #solicitudbeca.mail_aprobacionbecaalumno('TE COMUNICAMOS QUE TU BECA HA SIDO PREAPROBADA. NECESITAMOS QUE INGRESES A TU SGA AL MODULO SOLICITUD DE BECAS Y EN LAS ACCIONES ESCOGER ACEPTAR TERMINOS Y CONDICIONES DE BECA, PARA QUE CONTINUE EL TRAMITE, CASO CONTRARIO NO SE CONTINUARA CON EL PROCESO',request.user)
                               #OCastillo 16-03-2021 cambio en texto segun requerimiento de R.Garcia
                               solicitudbeca.mail_aprobacionbecaalumno('LE COMUNICAMOS QUE SU BECA FUE PREAPROBADA. PARA CONCLUIRLA ES NECESARIO QUE INGRESE A SU SGA Y EN EL MODULO SOLICITUD DE BECA, VAYA A ACCIONES Y ESCOJA APROBAR TERMINOS Y CONDICIONES PARA QUE CONTINUE EL TRAMITE, CASO CONTRARIO NO SE ACREDITARA EL DESCUENTO.',request.user)
                            else:
                               solicitudbeca.mail_aprobacionbeca('BECA NO APROBADA',request.user)
                return HttpResponseRedirect('/beca_solicitud?opcion=adm&id='+str(solicitudbeca.inscripcion_id))

            elif action == 'correosolicitud':
                try:
                    inscripcion = Inscripcion.objects.get(id=request.POST['insc'])

                    result = {}
                    result['result'] ="ok"

                    solicitudbeca = SolicitudBeca.objects.get(pk=int(request.POST['inscolicitud']),tiposolicitud=1)
                    usuario = request.user
                    user=Persona.objects.get(usuario=usuario)

                    if EMAIL_ACTIVE:
                        # if inscripcion.persona.emailinst:
                        #     mail_correosolicitud(request.POST['contenido'],request.POST['asunto'],str(inscripcion.persona.emailinst),user)
                        # else:
                        #     return HttpResponse(json.dumps({"result":"noexist"}),content_type="application/json")

                        lista = []
                        # OCU 19-01-2017 para enviar correo con copia a grupo Dobe
                        if inscripcion.persona.emailinst:
                            lista.append([inscripcion.persona.emailinst])
                            # lista[0][0]=str(lista[0][0])+','+str('dobe@bolivariano.edu.ec')
                            if inscripcion.persona.email1:
                                lista.append([inscripcion.persona.email1])

                            if solicitudbeca.inscripcion.tienediscapacidad:
                                lispersona= PersonAutorizaBecaAyuda.objects.filter(personadiscapacidad=True)
                                for list in lispersona:
                                    lista.append([list.correo])
                            else:
                                lispersona= PersonAutorizaBecaAyuda.objects.filter(personadiscapacidad=True)
                                for list in lispersona:
                                    lista.append([list.correo])

                            lista[0][0]=str(lista[0][0])+','+str('dobe@bolivariano.edu.ec')
                            email_estudiante=inscripcion.persona.emailinst
                            nivel_est=solicitudbeca
                            result['cargarurl']='/beca_solicitud?opcion=adm&id='+str(solicitudbeca.inscripcion_id)
                            solicitudbeca.fechaenviocorreo=datetime.now()
                            solicitudbeca.usuarioenviocorreo=usuario
                            solicitudbeca.estadosolicitud_id=2
                            solicitudbeca.save()

                            # llenar el log de historial de la solicitud ayuda economica
                            loshistorial= HistorialGestionBeca(solicitudbeca=solicitudbeca,inscripcion=solicitudbeca.inscripcion,
                                                                fecha=datetime.now(),estado_id=2, usuario=request.user,comentariocorreo=request.POST['contenido'])
                            loshistorial.save()
                            solicitudbeca.idgestion=loshistorial.id
                            solicitudbeca.save()

                            client_address = ip_client_address(request)
                            LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(solicitudbeca).pk,
                                object_id       = solicitudbeca.id,
                                object_repr     = force_str(solicitudbeca),
                                action_flag     = ADDITION,
                                change_message  = 'Solicitud de beca '+ 'envio de mensaje' +' (' + client_address + ')' )
                            mail_correosolicitud(request.POST['contenido'], request.POST['asunto'], str(lista[0][0]),request.user, elimina_tildes(inscripcion.persona.nombre_completo()),elimina_tildes(inscripcion.carrera.nombre),email_estudiante,nivel_est)
                        else:
                            return HttpResponse(json.dumps({"result":"noexist"}),content_type="application/json")

                    return HttpResponse(json.dumps(result),content_type="application/json")
                except:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")


            elif action == 'correoenviosecretaria':
                try:
                    result = {}
                    result['result'] ="ok"
                    usuario = request.user
                    user=Persona.objects.get(usuario=usuario)
                    if EMAIL_ACTIVE:
                        lista = []
                        solicitudbeca = SolicitudBeca.objects.get(pk=int(request.POST['idssolic']))
                        # lispersona= PersonAutorizaBecaAyuda.objects.filter(personasecretaria=True)
                        # for list in lispersona:
                        # lista.append(['secretariageneral@bolivariano.edu.ec',])
                        mail= str('secretariageneral@bolivariano.edu.ec')+','+ str('szuniga@bolivariano.edu.ec')+','+ str('mmora@bolivariano.edu.ec') +','+ str('floresvillamarinm@gmail.com')
                        # lista[0][0]=str(lista[0][0])+','+str('szuniga@bolivariano.edu.ec')+','+str('mmora@bolivariano.edu.ec')+','+str('floresvillamarinm@gmail.com')+','+str('ttapia@bolivariano.edu.ec')+','+str('ttapia@itb.edu.ec')


                        tabladescuento=TablaDescuentoBeca.objects.filter(solicitudbeca=solicitudbeca)

                        result['cargarurl']='/beca_solicitud?opcion=adm&id='+str(solicitudbeca.inscripcion_id)
                        solicitudbeca.estadosolicitud_id=6
                        solicitudbeca.save()

                        loshistorial= HistorialGestionBeca(solicitudbeca=solicitudbeca,inscripcion=solicitudbeca.inscripcion,
                                                            fecha=datetime.now(),estado_id=8, usuario=request.user,comentariocorreo=request.POST['contenido'])
                        loshistorial.save()

                        historialultima= HistorialGestionBeca.objects.filter(solicitudbeca=solicitudbeca,estado__id=3).order_by('-fecha')[:1].get()
                        solicitudbeca.idgestion=loshistorial.id
                        solicitudbeca.save()

                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(solicitudbeca).pk,
                            object_id       = solicitudbeca.id,
                            object_repr     = force_str(solicitudbeca),
                            action_flag     = ADDITION,
                            change_message  = 'Solicitud de beca '+ 'envio de mensaje a secretaria' +' (' + client_address + ')' )

                        mail_correosolicitudsecretaria(str(elimina_tildes(request.POST['contenido'])), mail,request.user, elimina_tildes(solicitudbeca.inscripcion.persona.nombre_completo()),elimina_tildes(solicitudbeca.inscripcion.carrera.nombre),solicitudbeca.inscripcion.persona.emailinst,solicitudbeca,tabladescuento,historialultima)


                    return HttpResponse(json.dumps(result),content_type="application/json")
                except:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")


            elif action == 'finalizacionautomatico':
                try:
                    result = {}
                    result['result'] ="ok"
                    usuario = request.user
                    user=Persona.objects.get(usuario=usuario)
                    solicitudbeca = SolicitudBeca.objects.get(pk=int(request.POST['idssolic']))
                    result['cargarurl']='/beca_solicitud?opcion=adm&id='+str(solicitudbeca.inscripcion_id)
                    solicitudbeca.estadosolicitud_id=7
                    solicitudbeca.aprobado=True
                    solicitudbeca.save()
                    loshistorial= HistorialGestionBeca(solicitudbeca=solicitudbeca,inscripcion=solicitudbeca.inscripcion,
                                                            fecha=datetime.now(),estado_id=26, usuario=request.user,comentariocorreo='APLICADO AUTOMATICAMENTE')
                    loshistorial.save()
                    solicitudbeca.idgestion=loshistorial.id
                    solicitudbeca.save()

                    # client_address = ip_client_address(request)
                    # LogEntry.objects.log_action(
                    #     user_id         = request.user.pk,
                    #     content_type_id = ContentType.objects.get_for_model(solicitudbeca).pk,
                    #     object_id       = solicitudbeca.id,
                    #     object_repr     = force_str(solicitudbeca),
                    #     action_flag     = ADDITION,
                    #     change_message  = 'Finalizacion automatica de solicitud de beca ' +' (' + client_address + ')' )

                    return HttpResponse(json.dumps(result),content_type="application/json")
                except:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")


            elif action == 'cambiocrisfe':
                try:
                    result = {}
                    result['result'] ="ok"
                    usuario = request.user
                    user=Persona.objects.get(usuario=usuario)
                    solicitudbeca = SolicitudBeca.objects.get(pk=int(request.POST['idssolic']))
                    result['cargarurl']='/beca_solicitud?opcion=adm&id='+str(solicitudbeca.inscripcion_id)
                    solicitudbeca.autorizacioneliminarcrisfe=True
                    solicitudbeca.save()


                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(solicitudbeca).pk,
                        object_id       = solicitudbeca.id,
                        object_repr     = force_str(solicitudbeca),
                        action_flag     = ADDITION,
                        change_message  = 'Cambio programacion Crisfe ' +' (' + client_address + ')' )

                    return HttpResponse(json.dumps(result),content_type="application/json")
                except:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")


            elif action == 'aplicarbeca':
                try:
                    result = {}
                    result['result'] ="ok"
                    usuario = request.user
                    user=Persona.objects.get(usuario=usuario)
                    if EMAIL_ACTIVE:
                        lista = []
                        solicitudbeca = SolicitudBeca.objects.get(pk=int(request.POST['idssolic']))
                        # lispersona= PersonAutorizaBecaAyuda.objects.filter(personasecretaria=True)
                        # for list in lispersona:
                        if solicitudbeca.inscripcion.tienediscapacidad:
                            lispersona= PersonAutorizaBecaAyuda.objects.filter(personadiscapacidad=True)
                            for list in lispersona:
                                lista.append([list.correo])
                        else:
                            lispersona= PersonAutorizaBecaAyuda.objects.filter(personadiscapacidad=True)
                            for list in lispersona:
                                lista.append([list.correo])

                        lista[0][0]=str(lista[0][0])+','+str('dobe@bolivariano.edu.ec')
                        result['cargarurl']='/beca_solicitud?opcion=adm&id='+str(solicitudbeca.inscripcion_id)
                        solicitudbeca.estadosolicitud_id=7
                        solicitudbeca.save()

                        loshistorial= HistorialGestionBeca(solicitudbeca=solicitudbeca,inscripcion=solicitudbeca.inscripcion,
                                                            fecha=datetime.now(),estado_id=9, usuario=request.user,comentariocorreo=request.POST['contenido'])
                        loshistorial.save()
                        solicitudbeca.idgestion= loshistorial.id
                        solicitudbeca.save()

                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(solicitudbeca).pk,
                            object_id       = solicitudbeca.id,
                            object_repr     = force_str(solicitudbeca),
                            action_flag     = ADDITION,
                            change_message  = 'Aplicaciob Solicitud de beca '+ 'por secretaria' +' (' + client_address + ')' )
                        mail_correosolicitudsecretariaaplica(str(elimina_tildes(request.POST['contenido'])), str(lista[0][0]),request.user, elimina_tildes(solicitudbeca.inscripcion.persona.nombre_completo()),elimina_tildes(solicitudbeca.inscripcion.carrera.nombre),solicitudbeca.inscripcion.persona.emailinst,solicitudbeca)


                    return HttpResponse(json.dumps(result),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")



            elif action == 'datopersonal':
                try:
                    inscripcion = Inscripcion.objects.get(id=request.POST['insc'])
                    if request.POST['edit'] == '0':
                        inscripficha = InscripcionFichaSocioEconomicaBeca(
                                                inscripcion = inscripcion,
                                                edad = request.POST['edad'],
                                                estadocivil_id = request.POST['estadocivil'],
                                                ciudad_id = request.POST['cantonresid'],
                                                direccion = request.POST['calleurba'],
                                                numero = request.POST['numero'],
                                                sector_id = request.POST['sector'],
                                                telefono = request.POST['teldomic'],
                                                celular = request.POST['celular'],
                                                email = request.POST['email'],
                                                emailpersona= request.POST['emailpersonal'])
                        mensaje = 'Ingreso'
                    else :
                        inscripficha = InscripcionFichaSocioEconomicaBeca.objects.get(id = request.POST['edit'])
                        inscripficha.inscripcion = inscripcion
                        inscripficha.edad = request.POST['edad']
                        inscripficha.estadocivil_id = request.POST['estadocivil']
                        inscripficha.ciudad_id = request.POST['cantonresid']
                        inscripficha.direccion = request.POST['calleurba']
                        inscripficha.numero = request.POST['numero']
                        inscripficha.sector_id = request.POST['sector']
                        inscripficha.telefono = request.POST['teldomic']
                        inscripficha.celular = request.POST['celular']
                        inscripficha.email = request.POST['email']
                        inscripcion.emailpersona=request.POST['emailpersonal']
                        mensaje = 'Edicion'
                    inscripficha.save()
                    persona= inscripcion.persona
                    persona.email1=request.POST['emailpersonal']
                    persona.save()
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(inscripficha).pk,
                        object_id       = inscripficha.id,
                        object_repr     = force_str(inscripficha),
                        action_flag     = ADDITION,
                        change_message  = mensaje +' de Ficha Socio-Economica para Beca (' + client_address + ')' )
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

            elif action == 'situacionfamilia':
                try:
                    inscripficha = InscripcionFichaSocioEconomicaBeca.objects.get(id=request.POST['inscrificha'])
                    datos = json.loads(request.POST['datos'])
                    if datos != "":
                        for idexist in DatoResidente.objects.filter(fichabeca=inscripficha):
                            existe=0
                            for d in datos:
                                if 'iddatoresi' in d:
                                    if idexist.id == int(d['iddatoresi']):
                                        existe = 1
                                        break
                            if existe == 0:
                                idexist.delete()

                        for d in datos:
                             if 'iddatoresi' in d:
                                if d['iddatoresi'] == '0':
                                    datoresident = DatoResidente(
                                                        fichabeca = inscripficha,
                                                        nombres = d['nombre'],
                                                        edad = d['edadsitu'],
                                                        estadocivil_id = d['estadocivil'],
                                                        parentesco_id = d['parentesco'],
                                                        instruccion_id = d['instruccion'],
                                                        ocupacion_id = d['ocupacion'],
                                                        lugar = d['empreinsti'])
                                else:
                                    datoresident = DatoResidente.objects.get(id=d['iddatoresi'])
                                    datoresident.fichabeca = inscripficha
                                    datoresident.nombres = d['nombre']
                                    datoresident.edad = d['edadsitu']
                                    datoresident.estadocivil_id = d['estadocivil']
                                    datoresident.parentesco_id = d['parentesco']
                                    datoresident.instruccion_id = d['instruccion']
                                    datoresident.ocupacion_id = d['ocupacion']
                                    datoresident.lugar = d['empreinsti']
                                datoresident.save()

                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(datoresident).pk,
                            object_id       = datoresident.id,
                            object_repr     = force_str(datoresident),
                            action_flag     = ADDITION,
                            change_message  = ' Ingresado Datos de Residentes del Hogar (' + client_address + ')' )
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

            elif action == 'addreferencia':
                try:
                    inscripficha = InscripcionFichaSocioEconomicaBeca.objects.get(id=request.POST['inscrificha'])
                    datos = json.loads(request.POST['datos'])
                    if datos != "":
                        for idexist in ReferenciaBeca.objects.filter(fichabeca=inscripficha):
                            existe=0
                            for d in datos:
                                if 'iddatoref' in d:
                                    if idexist.id == int(d['iddatoref']):
                                        existe = 1
                                        break
                            if existe == 0:
                                idexist.delete()

                        for d in datos:

                            if 'iddatoref' in d:
                                if d['iddatoref'] == '0':
                                    referencia = ReferenciaBeca(
                                                        fichabeca = inscripficha,
                                                        telefono = d['telefono'],
                                                        parentesco_id = d['parentesco'])
                                else:
                                    referencia = ReferenciaBeca.objects.get(id=d['iddatoref'])
                                    referencia.telefono =  d['telefono']
                                    referencia.parentesco.id =  d['parentesco']

                                referencia.save()

                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(referencia).pk,
                            object_id       = referencia.id,
                            object_repr     = force_str(referencia),
                            action_flag     = ADDITION,
                            change_message  = ' Ingresado Datos de Referencia (' + client_address + ')' )
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

            elif action == 'addreferenciaper':
                try:
                    inscripficha = InscripcionFichaSocioEconomicaBeca.objects.get(id=request.POST['inscrificha'])
                    datos = json.loads(request.POST['datos'])
                    if datos != "":
                        for idexist in ReferenciaPersonal.objects.filter(fichabeca=inscripficha):
                            existe=0
                            for d in datos:
                                 if 'iddatoref' in d:
                                    if idexist.id == int(d['iddatoref']):
                                        existe = 1
                                        break
                            if existe == 0:
                                idexist.delete()

                        for d in datos:
                            if 'iddatoref' in d:
                                if d['iddatoref'] == '0':
                                    referencia = ReferenciaPersonal(
                                                        fichabeca = inscripficha,
                                                        telefono = d['telefono'],
                                                        celular = d['celular'],
                                                        nombre = d['nombre'],
                                                        parentesco_id = d['parentesco'])
                                    mensaje = 'Ingresado'
                                else:
                                    referencia = ReferenciaPersonal.objects.get(id=d['iddatoref'])
                                    referencia.telefono =  d['telefono']
                                    referencia.parentesco.id =  d['parentesco']
                                    referencia.nombre =  d['nombre']
                                    referencia.celular =  d['celular']
                                    mensaje = 'Editado'

                                referencia.save()
                        inscripficha.completo=True
                        inscripficha.datecomple= datetime.now()
                        inscripficha.save()


                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(referencia).pk,
                            object_id       = referencia.id,
                            object_repr     = force_str(referencia),
                            action_flag     = ADDITION,
                            change_message  = mensaje +  ' Datos de Referencia Personales (' + client_address + ')' )
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

            elif action == 'situlabora':
                try:
                    inscripficha = InscripcionFichaSocioEconomicaBeca.objects.get(id=request.POST['inscficha'])
                    if request.POST['trabalabo'] == '0':
                        trabaja = False
                        tipotrabajo = None
                    else:
                        trabaja = True
                        tipotrabajo =  request.POST['trabalabo']
                    if request.POST['edit'] == '0':
                        datotrabajo = DatoTrabajo(
                                        fichabeca = inscripficha,
                                        trabaja = trabaja,
                                        tipotrabajo_id = tipotrabajo,
                                        empresa = request.POST['empresa'],
                                        direccion = request.POST['direccion'],
                                        telefono = request.POST['telefono'],
                                        cargo = request.POST['cargo'],
                                        fecha = convertir_fecha(request.POST['fecha']),
                                        tiempolab = request.POST['tiempo'])
                        mensaje='Ingreso'
                    else:
                        if request.POST['op'] == '1':
                            actual = True
                        else:
                            actual = False
                        datotrabajo = DatoTrabajo.objects.get(id=request.POST['edit'],actual=actual)
                        datotrabajo.fichabeca = inscripficha
                        datotrabajo.trabaja = trabaja
                        datotrabajo.tipotrabajo_id = tipotrabajo
                        datotrabajo.empresa = request.POST['empresa']
                        datotrabajo.direccion = request.POST['direccion']
                        datotrabajo.telefono = request.POST['telefono']
                        datotrabajo.cargo = request.POST['cargo']
                        datotrabajo.fecha = convertir_fecha(request.POST['fecha'])
                        datotrabajo.tiempolab = request.POST['tiempo']
                        mensaje='Edicion'
                    if request.POST['op'] == '1':
                        datotrabajo.actual=True
                    else:
                        datotrabajo.actual=False
                    datotrabajo.save()

                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(inscripficha).pk,
                        object_id       = inscripficha.id,
                        object_repr     = force_str(inscripficha),
                        action_flag     = ADDITION,
                        change_message  = mensaje+' de Datos de Situacion Laboral(' + client_address + ')' )
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

            elif action == 'datoacademico':
                try:
                    inscripficha = InscripcionFichaSocioEconomicaBeca.objects.get(id=request.POST['inscficha'])
                    if  request.POST['otrac']=='false':
                        otrac = False
                    else:
                        otrac = True

                    if  request.POST['fiscal']=='false':
                        fiscal = False
                    else:
                        fiscal = True
                    if request.POST['edit'] == '0':
                        datoacademico = DatosAcademicos(
                                        fichabeca = inscripficha,
                                        otracarrera = otrac,
                                        carrera = request.POST['carrera'],
                                        universidad = request.POST['univer'],
                                        colegio = request.POST['colegio'],
                                        lugar = request.POST['lugar'],
                                        nota = request.POST['nota'],
                                        anio = request.POST['grad'],
                                        fiscal = fiscal)
                        mensaje='Ingreso'
                    else:


                        datoacademico = DatosAcademicos.objects.get(id=request.POST['edit'])
                        datoacademico.otracarrera = otrac
                        datoacademico.carrera = request.POST['carrera']
                        datoacademico.universidad = request.POST['univer']
                        datoacademico.colegio = request.POST['colegio']
                        datoacademico.nota = request.POST['nota']
                        datoacademico.anio = request.POST['grad']
                        datoacademico.lugar = request.POST['lugar']
                        datoacademico.fiscal = fiscal

                        mensaje='Edicion'

                    datoacademico.save()

                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(inscripficha).pk,
                        object_id       = inscripficha.id,
                        object_repr     = force_str(inscripficha),
                        action_flag     = ADDITION,
                        change_message  = mensaje+' de Datos Academicos(' + client_address + ')' )
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

            elif action == 'situhabita':
                try:
                    inscripficha = InscripcionFichaSocioEconomicaBeca.objects.get(id=request.POST['inscficha'])
                    inscripficha.teneciaviviend_id = request.POST['tenvivend']
                    inscripficha.tipovivienda_id = request.POST['tipovivi']
                    inscripficha.descriptipo = request.POST['tipotrodescr']
                    if request.POST['numinquili']:
                        inquilino = True
                        numeroinqui = request.POST['numinquili']
                    else:
                        inquilino = False
                        numeroinqui = None
                    if request.POST['valarrien']:
                        valorarrie = request.POST['valarrien']
                    else:
                        valorarrie = None
                    if request.POST['edit'] == '0':
                        detallevivien = Detallevivienda(
                                        fichabeca = inscripficha,
                                        inquilino = inquilino,
                                        numeroinqui = numeroinqui,
                                        valorarriendo = valorarrie,
                                        cedidadescrip = request.POST['descedida'],
                                        numerodormit = request.POST['numdorm'])
                        mensaje='Ingreso'
                    else:
                        detallevivien = Detallevivienda.objects.get(id=request.POST['edit'])
                        detallevivien.fichabeca = inscripficha
                        detallevivien.inquilino = inquilino
                        detallevivien.numeroinqui = numeroinqui
                        detallevivien.valorarriendo = valorarrie
                        detallevivien.cedidadescrip = request.POST['descedida']
                        detallevivien.numerodormit = request.POST['numdorm']
                        mensaje='Edicion'
                    detallevivien.save()
                    inscripficha.save()
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(inscripficha).pk,
                        object_id       = inscripficha.id,
                        object_repr     = force_str(inscripficha),
                        action_flag     = ADDITION,
                        change_message  = mensaje+' de Datos de Situacion Habitacional(' + client_address + ')' )
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

            elif action == 'datoeconomi':
                try:
                    inscripficha = InscripcionFichaSocioEconomicaBeca.objects.get(id=request.POST['inscficha'])
                    if request.POST['edit'] == '0':
                        inscripficha.personacubregasto_id = request.POST['cubregastoid']
                        inscripficha.descripcubregasto = request.POST['expligasto']
                        mensaje='Ingreso'
                    else:
                        inscripficha.personacubregasto_id = request.POST['cubregastoid']
                        inscripficha.descripcubregasto = request.POST['expligasto']
                        mensaje='Edicion'
                    inscripficha.save()
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(inscripficha).pk,
                        object_id       = inscripficha.id,
                        object_repr     = force_str(inscripficha),
                        action_flag     = ADDITION,
                        change_message  = mensaje+' de Datos Economicos del Estudiante(' + client_address + ')' )
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

            elif action == 'detallingrxegre':
                try:
                    inscripficha = InscripcionFichaSocioEconomicaBeca.objects.get(id=request.POST['inscrificha'])
                    datos = json.loads(request.POST['datos'])
                    if datos != "":
                        for d in datos:
                            if d['valoringre'] != '':
                                valoringre = d['valoringre']
                            else:
                                valoringre = None
                            if d['valoregre'] != '':
                                valoregre = d['valoregre']
                            else:
                                valoregre = None

                            if d['iddetingre'] != '':
                                idtipoingre = d['iddetingre']
                            else:
                                idtipoingre = None
                            if d['iddetegre'] != '':
                                idtipoegre = d['iddetegre']
                            else:
                                idtipoegre = None
                            if 'iddetalleingre' in d:
                                if d['iddetalleingre'] == '0':
                                    detalleingrexegres = DetalleIngrexEgres(
                                                            fichabeca = inscripficha,
                                                            tipoingreso_id = idtipoingre,
                                                            valoringreso = valoringre,
                                                            tipoegreso_id =idtipoegre,
                                                            valoregreso =valoregre )
                                    mensaje = 'Ingreso'
                                else:
                                    detalleingrexegres = DetalleIngrexEgres.objects.get(id=d['iddetalleingre'])
                                    detalleingrexegres.fichabeca = inscripficha
                                    detalleingrexegres.tipoingreso_id = idtipoingre
                                    detalleingrexegres.valoringreso = valoringre
                                    detalleingrexegres.tipoegreso_id =idtipoegre
                                    detalleingrexegres.valoregreso = valoregre
                                    mensaje = 'Edicion'
                                detalleingrexegres.save()
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(inscripficha).pk,
                        object_id       = inscripficha.id,
                        object_repr     = force_str(inscripficha),
                        action_flag     = ADDITION,
                        change_message  = mensaje+' de Detalle de Ingresos y Egresos Familiares(' + client_address + ')' )
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

            elif action == 'situsaludfami':
                try:
                    inscripficha = InscripcionFichaSocioEconomicaBeca.objects.get(id=request.POST['inscficha'])
                    if request.POST['parentescosalud1']:
                        problemsalud = True
                        idparentesco = request.POST['parentescosalud1']
                    else:
                        problemsalud = False
                        idparentesco = None
                    if request.POST['edit'] == '0':
                        enfermedadfamilia = EnfermedadFamilia(
                                                            fichabeca = inscripficha,
                                                            problemsalud = problemsalud,
                                                            descripcion = request.POST['nombreenfermedad'],
                                                            parentesco_id = idparentesco )
                        mensaje='Ingreso'
                    else:
                        enfermedadfamilia = EnfermedadFamilia.objects.get(id=request.POST['edit'])
                        enfermedadfamilia.fichabeca = inscripficha
                        enfermedadfamilia.problemsalud = problemsalud
                        enfermedadfamilia.descripcion = request.POST['nombreenfermedad']
                        enfermedadfamilia.parentesco_id = idparentesco
                        mensaje='Edicion'
                    enfermedadfamilia.save()

                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(inscripficha).pk,
                        object_id       = inscripficha.id,
                        object_repr     = force_str(inscripficha),
                        action_flag     = ADDITION,
                        change_message  = mensaje+' de Situacion de Salud del Grupo Familiar(' + client_address + ')' )
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

            # OCastillo 25-mayo-2017 registrar la especie de Becas
            elif action=='registrar':
                try:
                    solicitudbeca = SolicitudBeca.objects.filter(pk=request.POST['inssolic']).get()
                    inscripcion = Inscripcion.objects.get(id=request.POST['insespe'])
                    numeroespecie = int(request.POST['numeroe'])
                    codigoespecie = str(request.POST['codigoe']).upper()

                    if not RubroEspecieValorada.objects.filter(rubro__inscripcion=inscripcion,tipoespecie__id=9,serie=numeroespecie,rubro__cancelado=True,aplicada=True,disponible=False).exists():

                       fespecie= RubroEspecieValorada.objects.filter(rubro__inscripcion=inscripcion,tipoespecie__id=9,serie=numeroespecie,rubro__cancelado=True).order_by('-id')[:1].get().rubro.fecha
                       diasvalidez = (datetime.now().date()- fespecie).days
                       fechaespecie = convertir_fecha(request.POST['fechaespe'])
                       observaciones = request.POST['observaciones'].upper()
                       usuario = request.user
                       if diasvalidez < 45:
                            try:
                                if not RubroEspecieValorada.objects.filter(serie=numeroespecie,codigoe=codigoespecie,tipoespecie__id=9,rubro__inscripcion=inscripcion,rubro__cancelado=True,aplicada=False,disponible=True).exists():
                                    # OCU Grabo datos de especie en la solicitud
                                    solicitudbeca.serieespecie = numeroespecie
                                    solicitudbeca.codigoespecie = codigoespecie
                                    solicitudbeca.obsespecie =  observaciones
                                    solicitudbeca.fechaespecie = fechaespecie
                                    solicitudbeca.f_registroespe = datetime.now()
                                    solicitudbeca.usrregistroespe = usuario
                                    solicitudbeca.save()
                                    # OCU Grabo la solicitud en la especie y actualizo su estado
                                    especie =RubroEspecieValorada.objects.filter(rubro__inscripcion=inscripcion,tipoespecie__id=9,serie=numeroespecie,rubro__cancelado=True).order_by('-id')[:1].get()
                                    especie.aplicada=True
                                    especie.observaciones=observaciones
                                    especie.becasolicitud=solicitudbeca
                                    especie.codigoe=codigoespecie
                                    especie.disponible=False
                                    especie.fecha=datetime.now()
                                    especie.usuario=usuario
                                    especie.save()

                                    client_address = request.META['REMOTE_ADDR']

                                    # Log de ADICIONAR Registro Especie Beca
                                    LogEntry.objects.log_action(
                                        user_id         = request.user.pk,
                                        content_type_id = ContentType.objects.get_for_model(especie).pk,
                                        object_id       = especie.id,
                                        object_repr     = force_str(especie),
                                        action_flag     = ADDITION,
                                        change_message  = 'Registro de Especie Tipo Beca '+ especie.rubro.inscripcion.persona.nombre_completo() +' (' + client_address + ')'  )
                                    return HttpResponse(json.dumps({"result": "ok"}),content_type="application/json")
                                else:
                                    return HttpResponse(json.dumps({"result": "badespecie", "numeroespecie": str(numeroespecie),"codigoespecie":str(codigoespecie)}),content_type="application/json")
                            except Exception as ex:
                                return HttpResponse(json.dumps({"result": "bad"}),content_type="application/json")
                       else:
                           return HttpResponse(json.dumps({"result": "badfechas", "numeroespecie": str(numeroespecie),"fespecie":str(fespecie)}),content_type="application/json")
                    else:
                                    return HttpResponse(json.dumps({"result": "badespecie","numeroespecie": str(numeroespecie),"codigoespecie":str(codigoespecie)}),content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({"result": "bad"}),content_type="application/json")

            elif action=='fechaespecie':
                # OCastillo 02-mayo-2017 para nueva validez de especie 45 dias
                fechaespecie=request.POST['fechaespecie']
                fe=(convertir_fecha(fechaespecie)).date()
                diasvalidez = (datetime.now().date()- fe).days

                if diasvalidez >45:
                   return HttpResponse(json.dumps({"result":"bad","dias":diasvalidez}),content_type="application/json")
                else:
                   return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")

            elif action == 'eliminarsolicitud':

                try:
                    result = {}
                    result['result'] ="ok"
                    solicitudbeca = SolicitudBeca.objects.filter(pk=int(request.POST['idssolic']),tiposolicitud=1).get()
                    solicitudbeca.eliminado=True
                    solicitudbeca.estadosolicitud_id=3
                    solicitudbeca.save()


                    lista = []
                    if solicitudbeca.inscripcion.tienediscapacidad:
                        lispersona= PersonAutorizaBecaAyuda.objects.filter(personadiscapacidad=True)
                        for list in lispersona:
                            lista.append([list.correo])
                    else:
                        lispersona= PersonAutorizaBecaAyuda.objects.filter(personadiscapacidad=True)
                        for list in lispersona:
                            lista.append([list.correo])

                    lista[0][0]=str(lista[0][0])+','+str('dobe@bolivariano.edu.ec')

                    result['cargarurl']='/beca_solicitud?opcion=adm&id='+str(solicitudbeca.inscripcion_id)

                    loshistorial= HistorialGestionBeca(solicitudbeca=solicitudbeca,inscripcion=solicitudbeca.inscripcion,
                                                        fecha=datetime.now(),estado_id=17, usuario=request.user,comentariocorreo=request.POST['contenido'])
                    loshistorial.save()
                    solicitudbeca.idgestion=loshistorial.id
                    solicitudbeca.save()
                    email_estudiante=solicitudbeca.inscripcion.persona.emailinst
                    nivel_est=solicitudbeca

                    mail_correosolicitud(request.POST['contenido'], 'ELIMINACION DE SOLICITUD DE BECA', str(lista[0][0]),request.user, elimina_tildes(solicitudbeca.inscripcion.persona.nombre_completo()),elimina_tildes(solicitudbeca.inscripcion.carrera.nombre),email_estudiante,nivel_est)

                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(solicitudbeca).pk,
                    object_id       = solicitudbeca.id,
                    object_repr     = force_str(solicitudbeca),
                    action_flag     = DELETION,
                    change_message  = 'Solicitud' +' de beca Eliminada (' + client_address + ')' )

                    return HttpResponse(json.dumps(result),content_type="application/json")

                except Exception as e:
                    result['result'] ="bad"
                    return HttpResponse(json.dumps(result),content_type="application/json")



            elif action == 'addrevision':
                    solicitudbeca=SolicitudBeca.objects.get(id=request.POST['solicitudinscrip'])


                    loshistorial= HistorialGestionBeca(solicitudbeca=solicitudbeca,inscripcion=solicitudbeca.inscripcion,
                                                                    fecha=datetime.now(),estado_id=26, usuario=request.user,
                                                                    comentariocorreo=elimina_tildes(request.POST['comentario']))
                    loshistorial.save()

                    solicitudbeca.estadosolicitud_id=7
                    solicitudbeca.idgestion=loshistorial.id
                    solicitudbeca.save()

                    return HttpResponseRedirect('/beca_solicitud?opcion=adm&id='+str(solicitudbeca.inscripcion.id))


            elif action == 'aprobarsolicitudestudiante':

                try:
                    result = {}
                    result['result'] ="ok"
                    solicitudbeca = SolicitudBeca.objects.filter(pk=int(request.POST['idssolic']),tiposolicitud=1).get()
                    solicitudbeca.aprobacionestudiante=True
                    solicitudbeca.estadosolicitud_id=9
                    solicitudbeca.save()


                    lista = []
                    if solicitudbeca.inscripcion.tienediscapacidad:
                        lispersona= PersonAutorizaBecaAyuda.objects.filter(personadiscapacidad=True)
                        for list in lispersona:
                            lista.append([list.correo])
                    else:
                        lispersona= PersonAutorizaBecaAyuda.objects.filter(personadiscapacidad=True)
                        for list in lispersona:
                            lista.append([list.correo])

                    lista[0][0]=str(lista[0][0])+','+str('dobe@bolivariano.edu.ec')

                    result['cargarurl']='/beca_solicitud?opcion=adm&id='+str(solicitudbeca.inscripcion_id)

                    loshistorial= HistorialGestionBeca(solicitudbeca=solicitudbeca,inscripcion=solicitudbeca.inscripcion,
                                                        fecha=datetime.now(),estado_id=18, usuario=request.user,comentariocorreo=request.POST['contenido'])
                    loshistorial.save()
                    solicitudbeca.idgestion=loshistorial.id
                    solicitudbeca.save()
                    email_estudiante=solicitudbeca.inscripcion.persona.emailinst
                    nivel_est=solicitudbeca

                    mail_correosolicitud(elimina_tildes(request.POST['contenido']), str('APROBACION POR EL ESTUDIANTE DE SOLICITUD DE BECA'), str(lista[0][0]),request.user, elimina_tildes(solicitudbeca.inscripcion.persona.nombre_completo()),elimina_tildes(solicitudbeca.inscripcion.carrera.nombre),email_estudiante,nivel_est)

                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(solicitudbeca).pk,
                    object_id       = solicitudbeca.id,
                    object_repr     = force_str(solicitudbeca),
                    action_flag     = DELETION,
                    change_message  = 'Solicitud' +' de beca aprobada por el estudiante (' + client_address + ')' )

                    return HttpResponse(json.dumps(result),content_type="application/json")

                except Exception as e:
                    result['result'] ="bad"
                    return HttpResponse(json.dumps(result),content_type="application/json")


            elif action == 'actualizarrubro':

                try:
                    result = {}
                    solicitudbeca=SolicitudBeca.objects.get(id=request.POST['idssolic'])
                    matriculaactual = Matricula.objects.filter(inscripcion = solicitudbeca.inscripcion,nivel__cerrado=False,liberada=False).order_by('-fecha')[:1].get()
                    rubro=Rubro.objects.filter(inscripcion=solicitudbeca.inscripcion,cancelado=False)
                    # solo tomar cuota y matricula
                    rubroactualizar=RubroOtro.objects.filter(rubro__in=rubro,tipo__in=[2,19,4]).order_by('rubro')
                    idrubrotro=rubroactualizar.filter().values_list('rubro',flat=True)

                    # actualizar tipo nivel pago
                    i=0
                    for xtipo in rubroactualizar:
                        datorubo=xtipo.rubro
                        # rubro matricula
                        if xtipo.tipo_id==4 or xtipo.tipo_id==19:
                            datorubo.tiponivelpago=0
                        else:
                            i=i+1
                            datorubo.tiponivelpago=i
                        datorubo.save()



                    for x in rubroactualizar:
                        if x.rubro.tiponivelpago>0:
                            if not RubroCuota.objects.filter(rubro=x.rubro).exists():
                                rubcu=RubroCuota(rubro=x.rubro,matricula=matriculaactual,cuota= x.rubro.tiponivelpago)
                                rubcu.save()
                        else:

                             if not RubroMatricula.objects.filter(rubro=x.rubro).exists():
                                rubma=RubroMatricula(rubro=x.rubro,matricula=matriculaactual)
                                rubma.save()


                    if RubroOtro.objects.filter(rubro__in=idrubrotro).exists():
                       rubrootro=RubroOtro.objects.filter(rubro__in=idrubrotro)
                       rubrootro.delete()



                    result['cargarurl']='/beca_solicitud?opcion=adm&id='+str(solicitudbeca.inscripcion_id)
                    result['result'] ="ok"

                    return HttpResponse(json.dumps(result),content_type="application/json")

                except Exception as e:
                    result['result'] ="bad"
                    return HttpResponse(json.dumps(result),content_type="application/json")

            elif action == 'agregargestion':
                try:
                    result = {}
                    solicitudbeca=SolicitudBeca.objects.get(id=request.POST['idsolic'])
                    inscripcion = solicitudbeca.inscripcion

                    if(int(request.POST['idtipogestion'])) == 3: #analisis
                        solicitudbeca.estadosolicitud_id = 5
                    if(int(request.POST['idtipogestion'])) == 2: #envio correo
                        lista = []
                        strcorreo = None
                        if inscripcion.persona.emailinst:
                            strcorreo = inscripcion.persona.emailinst
                        if inscripcion.persona.email1:
                            strcorreo = str(strcorreo) + str(',') + str(inscripcion.persona.email1)
                        lispersona= PersonAutorizaBecaAyuda.objects.filter(personadiscapacidad=True)[:1].get()
                        strcorreo = str(strcorreo) + str(',') + str(lispersona) + str(',') + str('dobe@bolivariano.edu.ec')
                        nivel_est=solicitudbeca
                        email_estudiante=inscripcion.persona.emailinst
                        solicitudbeca.fechaenviocorreo=datetime.now()
                        solicitudbeca.usuarioenviocorreo=request.user
                        mail_correosolicitud(request.POST['descripcion'], str("Proceso Solicitud de Beca"), str(strcorreo),request.user, elimina_tildes(inscripcion.persona.nombre_completo()),elimina_tildes(inscripcion.carrera.nombre),email_estudiante,nivel_est)
                        solicitudbeca.estadosolicitud_id =2
                    if(int(request.POST['idtipogestion'])) == 8: # enviar a secretaria
                         if solicitudbeca.aprobacionestudiante == False:
                            return HttpResponse(
                                json.dumps(
                                    {'result': 'bad',
                                     'message': 'No se puede ingresar esta gestion porque el estudiante aun no acepto la resolucion de la beca'}),
                                content_type="application/json")
                         solicitudbeca.estadosolicitud_id =6
                    if(int(request.POST['idtipogestion'])) == 27: # en rechazo
                        solicitudbeca.estadosolicitud_id = 4
                    if(int(request.POST['idtipogestion'])) == 1: # en pre-aprobacion


                        if solicitudbeca.asignaciontarficadescuento==False:
                            result['result'] ="bad"
                            result['message'] ="No se puede aprobar la solicitud porque no se encuentra aprobada la tabla de descuento ir a la accion, Ver Tabla de Descuento y aprobarla"
                            return HttpResponse(json.dumps(result),content_type="application/json")

                        if solicitudbeca.aprobacionestudiante == True:
                             result['result'] ="bad"
                             result['message'] ="No se puede ingresar la gestion porque ya el estudiante acepto la resolucion de la beca"
                             return HttpResponse(json.dumps(result),content_type="application/json")

                        solicitudbeca.estadosolicitud_id = 3
                        solicitudbeca.aprobado=True
                        solicitudbeca.fechaproces = datetime.now()
                        solicitudbeca.usuario = request.user

                        solicitudbeca.save()


                    loshistorial= HistorialGestionBeca(solicitudbeca=solicitudbeca,inscripcion=solicitudbeca.inscripcion,
                                                                fecha=datetime.now(), estado_id=int(request.POST['idtipogestion']), usuario=request.user,comentariocorreo=request.POST['descripcion'])
                    loshistorial.save()

                    solicitudbeca.idgestion = loshistorial.id

                    solicitudbeca.save()


                    result['result'] ="ok"
                    return HttpResponse(json.dumps(result),content_type="application/json")
                except Exception as e:
                    result['result'] ="bad"
                    return HttpResponse(json.dumps(result),content_type="application/json")



        else:
            data = {'title':'Solicitud de beca'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']

                if action == 'fichasocioecono':
                    data['title'] = 'Ficha Socio-Economica de Beca'
                    inscripcion = Inscripcion.objects.get(id=request.GET['id'])
                    autorizacionbode= False
                    autorizacionbecasenecyt= False

                    if inscripcion.autorizacionbecadobe:
                        autorizacionbode=True

                    if inscripcion.autorizacionbecasenecyt:
                        autorizacionbecasenecyt=True

                    if autorizacionbode==False:

                        if inscripcion.matricula().nivel.nivelmalla.id >6 :
                             return HttpResponseRedirect("/?info=No puede acceder a renovar la beca porque no aplica para este nivel")


                    if inscripcion.promocion!=None:
                        if inscripcion.promocion.todos_niveles:
                            return HttpResponseRedirect("/?info=No puede acceder a una beca porque tiene una promocion para todo los nivel " + str(inscripcion.promocion.descripcion))
                        # else:
                        #    if inscripcion.matricula().nivel.nivelmalla_id==NIVEL_MALLA_UNO:
                        #        return HttpResponseRedirect("/?info=No puede acceder a una beca porque tiene una promocion " + str(inscripcion.promocion.descripcion))

                    if (inscripcion.persona.usuario == request.user) or (inscripcion.persona.usuario != request.user and InscripcionFichaSocioEconomicaBeca.objects.filter(inscripcion=inscripcion,completo=True).exists()):
                        matriculaant=None
                        # if Matricula.objects.filter(inscripcion = inscripcion).count() > 2 and Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=False).exists() and inscripcion.persona.usuario == request.user:
                        if Matricula.objects.filter(inscripcion = inscripcion).count() > 2 and inscripcion.persona.usuario == request.user:
                            matricula = Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=True).order_by('-fecha')[:1].get()
                            matriculaactual = ''
                            if Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=False).exists():
                                matriculaactual = Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=False).order_by('-fecha')[:1].get()
                                if Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=True).order_by('-fecha').exists():
                                    matriculaant = Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=True).order_by('-fecha')[:1].get()
                                    #validar que sean de nivel diferente
                                    if inscripcion.matricula().nivel.nivelmalla_id==matriculaant.nivel.nivelmalla_id:
                                        if inscripcion.matricula().nivel.nivelmalla_id>1:
                                            matriculaant = Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=True,nivel__nivelmalla__id =inscripcion.matricula().nivel.nivelmalla_id).order_by('-fecha')[:1].get()
                            data['matriculaactual'] = matriculaactual
                            if SolicitudBeca.objects.filter(inscripcion=inscripcion,nivel=matricula.nivel,renovarbeca=True,aprobado=False).exists():
                                       return HttpResponseRedirect("/?info=Ya existe una renovacion de solicitud en el nivel en proceso")
                            if autorizacionbode==False:
                                if RecordAcademico.objects.filter(inscripcion__id=matricula.inscripcion_id,asignatura__promedia=True,aprobada=False,fecha__lt=matriculaactual.fecha).exists():
                                        return HttpResponseRedirect("/?info=No puede acceder a una beca tiene materias reprobadas en su record academico")
                            # OCU validacion 1 no tenga ninguna cuota cancelada ok
                            # if not matricula.cantidad_cuotas() and  not inscripcion.existe_solicitud_beca():
                            #     return HttpResponseRedirect("/?info=Las becas se aplican por niveles completos, tiene una o varias cuotas pagadas")

                            # OCU validacion 2 de fecha de aplicacion falten 15 dias para vencer cuota ok
                            # if Rubro.objects.filter(inscripcion=matriculaactual.inscripcion,cancelado=False).order_by('fechavence').exists() and  not inscripcion.existe_solicitud_beca():
                            #     cuotas=Rubro.objects.filter(inscripcion=matriculaactual.inscripcion,cancelado=False).order_by('fechavence')[:1].get()
                            #     dias= (cuotas.fechavence-hoy).days
                            #     if dias<16:
                            #         return HttpResponseRedirect("/?info=Las becas se aplican minimo 15 dias antes de vencer la primera cuota")

                            # OCU validacion 3 matriculado en Seminario no aplica beca ok
                            if not matriculaant:
                                return HttpResponseRedirect("/?info=No tiene un nivel anterior para calcular promedio")
                            if autorizacionbecasenecyt==False and autorizacionbode==False:
                                puntajevar =calculopromedio(matriculaant,matriculaant.nivel.malla, matriculaant.nivel.nivelmalla)


                            if matriculaant:
                                if matriculaant.tipobeneficio==TipoBeneficio.objects.get(pk=TIPO_BECA_SENESCYT) or matriculaant.tipobeca==TipoBeca.objects.get(pk=7):
                                    auxmateria=True
                                else:
                                    auxmateria=False
                            else:
                                auxmateria=False

                            if (not inscripcion.tienediscapacidad and (inscripcion.empresaconvenio==None or inscripcion.empresaconvenio.id==4 )) and ( not auxmateria) and (not autorizacionbode) and (not autorizacionbecasenecyt):
                                if puntajevar< PUNTAJE_BECA_NORMAL:
                                    return HttpResponseRedirect("/?info=No puede acceder a una beca la nota general del nivel anterior debe ser mayor o igual a "+str(PUNTAJE_BECA_NORMAL) + "SU PUNTAJE ES: "+ str(decimal.Decimal(puntajevar)))
                                else:
                                    if inscripcion.rubros_vencidos():
                                        return HttpResponseRedirect("/?info=No puede acceder a una beca tiene rubros vencidos por pagar")

                                if Nivel.objects.filter(pk=matriculaactual.nivel.id,nivelmalla__id=10).exists() and not inscripcion.existe_solicitud_beca():
                                    return HttpResponseRedirect("/?info=Las becas son solamente para los niveles de la carrera. No se aplica en Seminario de Graduacion")
                            else:
                                if autorizacionbode== False and autorizacionbecasenecyt== False:
                                    if puntajevar < PUNTAJE_BECA_DISCAPA:
                                        return HttpResponseRedirect("/?info=No puede acceder a una beca la nota general del nivel anterior debe ser mayor o igual a "+str(PUNTAJE_BECA_DISCAPA)+ "SU PUNTAJE ES: "+ str(decimal.Decimal(puntajevar)))
                                    else:
                                        if inscripcion.rubros_vencidos():
                                            return HttpResponseRedirect("/?info=No puede acceder a una beca tiene rubros vencidos por pagar")
                        else:
                            if inscripcion.persona.usuario == request.user:
                                matriculaant=None
                                if Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=False).exists():
                                    matriculaactual = Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=False).order_by('-fecha')[:1].get()
                                    if Matricula.objects.filter(Q(nivel__cerrado=True) | Q(liberada=True),inscripcion = inscripcion).order_by('-fecha').exists():
                                        matriculaant = Matricula.objects.filter(Q(nivel__cerrado=True) | Q(liberada=True),inscripcion = inscripcion).order_by('-fecha')[:1].get()
                                        #validar que sean de nivel diferente
                                        if inscripcion.matricula().nivel.nivelmalla_id==matriculaant.nivel.nivelmalla_id:
                                            if inscripcion.matricula().nivel.nivelmalla_id>1:
                                                matriculaant = Matricula.objects.filter(Q(nivel__cerrado=True) | Q(liberada=True),inscripcion = inscripcion,nivel__nivelmalla__id =inscripcion.matricula().nivel.nivelmalla_id).order_by('-fecha')[:1].get()


                                if matriculaant:
                                    if (not inscripcion.tienediscapacidad and (inscripcion.empresaconvenio==None or inscripcion.empresaconvenio.id==4 )) and ( not matriculaant.tipobeneficio==TipoBeneficio.objects.get(pk=TIPO_BECA_SENESCYT)) and (not autorizacionbode) and (not autorizacionbecasenecyt):
                                        if not matriculaant:
                                            return HttpResponseRedirect("/?info=No tiene un nivel anterior para calcular promedio")
                                        puntajevar =calculopromedio(matriculaant,matriculaant.nivel.malla, matriculaant.nivel.nivelmalla)
                                    # if not inscripcion.tienediscapacidad or Matricula.objects.filter(inscripcion = inscripcion).count() == 1:
                                    #     return HttpResponseRedirect("/?info=No puede acceder a una beca porque se encuentre matricula en el primer nivel, para mas informacion acercarse a Bienestar Estudiantil")
                                    # else:
                                    #     if not Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=False).exists():
                                    #             return HttpResponseRedirect("/?info=No puede acceder a una beca no se encuentra matriculado")
                                else:
                                    if (not inscripcion.tienediscapacidad and (inscripcion.empresaconvenio==None or inscripcion.empresaconvenio.id==4 )) and (not autorizacionbode) and (not autorizacionbecasenecyt):
                                        if not matriculaant:
                                            return HttpResponseRedirect("/?info=No tiene un nivel anterior para calcular promedio")
                                        puntajevar =calculopromedio(matriculaant,matriculaant.nivel.malla, matriculaant.nivel.nivelmalla)

                                if matriculaant:

                                    if (not inscripcion.tienediscapacidad and inscripcion.empresaconvenio==None) and ( not matriculaant.tipobeneficio==TipoBeneficio.objects.get(pk=TIPO_BECA_SENESCYT)) and (not autorizacionbode) and (not autorizacionbecasenecyt):
                                        if puntajevar < PUNTAJE_BECA_NORMAL:
                                            return HttpResponseRedirect("/?info=No puede acceder a una beca la nota general del nivel anterior debe ser mayor o igual a "+str(PUNTAJE_BECA_NORMAL) + "SU PUNTAJE ES: "+ str(decimal.Decimal(puntajevar)))
                                        else:
                                            if inscripcion.rubros_vencidos():
                                                return HttpResponseRedirect("/?info=No puede acceder a una beca tiene rubros vencidos por pagar")
                                    else:
                                        if Matricula.objects.filter(inscripcion = inscripcion).count() > 2:
                                            if autorizacionbode== False and autorizacionbecasenecyt== False:
                                                if puntajevar < PUNTAJE_BECA_DISCAPA:
                                                    return HttpResponseRedirect("/?info=No puede acceder a una beca la nota general del nivel anterior debe ser mayor o igual a "+str(PUNTAJE_BECA_DISCAPA)+ "SU PUNTAJE ES: "+ str(decimal.Decimal(puntajevar)))
                                                if inscripcion.rubros_vencidos():
                                                    return HttpResponseRedirect("/?info=No puede acceder a una beca tiene rubros vencidos por pagar")
                                else:

                                    if (not inscripcion.tienediscapacidad and (inscripcion.empresaconvenio==None or inscripcion.empresaconvenio.id==4 )) and  (not autorizacionbode) and (not autorizacionbecasenecyt):
                                        if puntajevar < PUNTAJE_BECA_NORMAL:
                                            return HttpResponseRedirect("/?info=No puede acceder a una beca la nota general del nivel anterior debe ser mayor o igual a "+str(PUNTAJE_BECA_NORMAL) + "SU PUNTAJE ES: "+ str(decimal.Decimal(puntajevar)))
                                        else:
                                            if inscripcion.rubros_vencidos():
                                                return HttpResponseRedirect("/?info=No puede acceder a una beca tiene rubros vencidos por pagar")
                                    else:
                                        if Matricula.objects.filter(inscripcion = inscripcion).count() > 2:
                                            if autorizacionbode== False and autorizacionbecasenecyt== False:
                                                if puntajevar < PUNTAJE_BECA_DISCAPA:
                                                    return HttpResponseRedirect("/?info=No puede acceder a una beca la nota general del nivel anterior debe ser mayor o igual a "+str(PUNTAJE_BECA_DISCAPA)+ "SU PUNTAJE ES: "+ str(decimal.Decimal(puntajevar)))
                                                if inscripcion.rubros_vencidos():
                                                    return HttpResponseRedirect("/?info=No puede acceder a una beca tiene rubros vencidos por pagar")


                        data['ID_VIVIPROPIA_BECA'] = ID_VIVIPROPIA_BECA
                        data['ID_VIVIARREN_BECA'] = ID_VIVIARREN_BECA
                        data['ID_VIVICEDIDA_BECA'] = ID_VIVICEDIDA_BECA
                        data['ID_TIPVIVOTRO_BECA'] = ID_TIPVIVOTRO_BECA
                        data['ID_DATOECONOTRO_BECA'] = ID_DATOECONOTRO_BECA
                        data['inscripcion'] = inscripcion
                        data['parentesco'] = ParentezcoPersona.objects.all()
                        data['ocupacion'] = OcupacionJefeHogar.objects.all()
                        data['instruccion'] = NivelEstudio.objects.all()
                        data['estadocivil'] = PersonaEstadoCivil.objects.all()
                        data['tipotrabajo'] = FormaTrabajo.objects.all()
                        data['tipovivienda'] = TipoVivienda.objects.filter(id__in=(2,3,4,7))
                        data['teneciavivienda'] = TenenciaVivienda.objects.all()
                        data['personacubregasto'] = PersonaCubreGasto.objects.all()
                        data['tipoingresovivi'] = TipoIngresoVivienda.objects.all()
                        data['tipoegresosvivi'] = TipoEgresoVivienda.objects.all()
                        data['sectorvivi'] = SectorVivienda.objects.all()
                        data['cantonresid'] = Canton.objects.all()
                        if InscripcionFichaSocioEconomicaBeca.objects.filter(inscripcion=inscripcion).exists():
                            inscripcionficha = InscripcionFichaSocioEconomicaBeca.objects.filter(inscripcion=inscripcion).order_by('-id')[:1].get()
                            data['inscripcionficha'] = inscripcionficha
                            if DatoResidente.objects.filter(fichabeca=data['inscripcionficha']).exists():
                                data['datoresidentes'] = DatoResidente.objects.filter(fichabeca=data['inscripcionficha'])
                            if 'pag' in request.GET:
                                data['pag'] = request.GET['pag']
                            if DatoTrabajo.objects.filter(fichabeca=data['inscripcionficha'],actual=True).exists():
                                data['datotrabajo'] = DatoTrabajo.objects.filter(fichabeca=data['inscripcionficha'],actual=True)[:1].get()
                            if Detallevivienda.objects.filter(fichabeca=data['inscripcionficha']).exists():
                                data['detallevivienda'] = Detallevivienda.objects.filter(fichabeca=data['inscripcionficha'])[:1].get()
                            if DetalleIngrexEgres.objects.filter(fichabeca=data['inscripcionficha']).exists():
                                data['detalleingrexegres'] = DetalleIngrexEgres.objects.filter(fichabeca=data['inscripcionficha'])
                            if EnfermedadFamilia.objects.filter(fichabeca=data['inscripcionficha']).exists():
                                data['enfermedadfamilia'] = EnfermedadFamilia.objects.filter(fichabeca=data['inscripcionficha'])[:1].get()
                            if ReferenciaBeca.objects.filter(fichabeca=data['inscripcionficha']).exists():
                                data['referenciab'] = ReferenciaBeca.objects.filter(fichabeca=data['inscripcionficha'])
                            if ReferenciaPersonal.objects.filter(fichabeca=data['inscripcionficha']).exists():
                                data['referenciaper'] = ReferenciaPersonal.objects.filter(fichabeca=data['inscripcionficha'])
                                if not inscripcionficha.completo:
                                    inscripcionficha.completo=True
                                    inscripcionficha.datecomple= datetime.now()
                                    inscripcionficha.save()
                            if DatosAcademicos.objects.filter(fichabeca=data['inscripcionficha']).exists():
                                data['datosacademicos'] = DatosAcademicos.objects.filter(fichabeca=data['inscripcionficha'])[:1].get()
                            if DatoTrabajo.objects.filter(fichabeca=data['inscripcionficha'],actual=False).exists():
                                data['datotrabajoant'] = DatoTrabajo.objects.filter(fichabeca=data['inscripcionficha'],actual=False)[:1].get()
                            data['frmcro'] =CroquisForm()


                        data['user'] = request.user
                        data['puedesoli'] = None
                        if inscripcion.matriculado():
                            if not SolicitudBeca.objects.filter(nivel=inscripcion.matricula().nivel,inscripcion=inscripcion,eliminado=False).exists():
                                data['puedesoli'] = 'ok'
                        return render(request ,"beca_solicitud/fichasocio_economicabeca.html" ,  data)
                    return HttpResponseRedirect('beca_solicitud')

                if action == 'fichasocioeconorenovar':
                    data['title'] = 'Ficha Socio-Economica de Beca'
                    inscripcion = Inscripcion.objects.get(id=request.GET['id'])
                    autorizacionbode= False
                    autorizacionbecasenecyt=False

                    if inscripcion.autorizacionbecadobe:
                        autorizacionbode=True

                    if inscripcion.autorizacionbecasenecyt:
                        autorizacionbecasenecyt=True


                    if autorizacionbode==False:
                        if inscripcion.matricula().nivel.nivelmalla.id >6 :
                             return HttpResponseRedirect("/?info=No puede acceder a renovar la beca porque no aplica para este nivel")

                    if (inscripcion.persona.usuario == request.user) or (inscripcion.persona.usuario != request.user and InscripcionFichaSocioEconomicaBeca.objects.filter(inscripcion=inscripcion,completo=True).exists()):
                        matriculaant=None
                        # if Matricula.objects.filter(inscripcion = inscripcion).count() > 2 and Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=False).exists() and inscripcion.persona.usuario == request.user:
                        if Matricula.objects.filter(inscripcion = inscripcion).count() > 2 and inscripcion.persona.usuario == request.user:
                            matricula = Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=True).order_by('-fecha')[:1].get()
                            matriculaactual = ''
                            if Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=False).exists():
                                matriculaactual = Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=False).order_by('-fecha')[:1].get()
                                if Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=True).order_by('-fecha').exists():
                                    matriculaant = Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=True).order_by('-fecha')[:1].get()
                            data['matriculaactual'] = matriculaactual
                            if SolicitudBeca.objects.filter(inscripcion=inscripcion,nivel=matricula.nivel,renovarbeca=True,aprobado=False).exists():
                                       return HttpResponseRedirect("/?info=Ya existe una renovacion de solicitud en el nivel en proceso")
                            if autorizacionbode==False:
                                if RecordAcademico.objects.filter(inscripcion__id=matricula.inscripcion_id,asignatura__promedia=True,aprobada=False,fecha__lt=matriculaactual.fecha).exists():
                                    return HttpResponseRedirect("/?info=No puede acceder a una beca tiene materias reprobadas en su record academico")
                            # OCU validacion 1 no tenga ninguna cuota cancelada ok
                            # if not matricula.cantidad_cuotas() and  not inscripcion.existe_solicitud_beca():
                            #     return HttpResponseRedirect("/?info=Las becas se aplican por niveles completos, tiene una o varias cuotas pagadas")

                            # OCU validacion 2 de fecha de aplicacion falten 15 dias para vencer cuota ok
                            # if Rubro.objects.filter(inscripcion=matriculaactual.inscripcion,cancelado=False).order_by('fechavence').exists() and  not inscripcion.existe_solicitud_beca():
                            #     cuotas=Rubro.objects.filter(inscripcion=matriculaactual.inscripcion,cancelado=False).order_by('fechavence')[:1].get()
                            #     dias= (cuotas.fechavence-hoy).days
                            #     if dias<16:
                            #         return HttpResponseRedirect("/?info=Las becas se aplican minimo 15 dias antes de vencer la primera cuota")

                            # OCU validacion 3 matriculado en Seminario no aplica beca ok
                            if not matriculaant:
                                return HttpResponseRedirect("/?info=No tiene un nivel anterior para calcular promedio")

                            puntajevar =calculopromedio(matriculaant,matriculaant.nivel.malla, matriculaant.nivel.nivelmalla)
                            if Nivel.objects.filter(pk=matriculaactual.nivel.id,nivelmalla__id=10).exists() and not inscripcion.existe_solicitud_beca():
                                return HttpResponseRedirect("/?info=Las becas son solamente para los niveles de la carrera. No se aplica en Seminario de Graduacion")

                            if matriculaant:
                                if matriculaant.tipobeneficio==TipoBeneficio.objects.get(pk=TIPO_BECA_SENESCYT) or matriculaant.tipobeca==TipoBeca.objects.get(pk=7):
                                    auxmateria=True
                                else:
                                    auxmateria=False
                            else:
                                auxmateria=False

                            if (not inscripcion.tienediscapacidad and (inscripcion.empresaconvenio==None or inscripcion.empresaconvenio.id==4 )) and ( not auxmateria) and (not autorizacionbode):
                                if puntajevar< PUNTAJE_BECA_NORMAL:
                                    return HttpResponseRedirect("/?info=No puede acceder a una beca la nota general del nivel anterior debe ser mayor o igual a "+str(PUNTAJE_BECA_NORMAL) + "SU PUNTAJE ES: "+ str(decimal.Decimal(puntajevar)))
                                else:
                                    if inscripcion.rubros_vencidos():
                                        return HttpResponseRedirect("/?info=No puede acceder a una beca tiene rubros vencidos por pagar")
                            else:
                                if autorizacionbode== False and autorizacionbecasenecyt== False:
                                    if puntajevar < PUNTAJE_BECA_DISCAPA:
                                        return HttpResponseRedirect("/?info=No puede acceder a una beca la nota general del nivel anterior debe ser mayor o igual a "+str(PUNTAJE_BECA_DISCAPA)+ "SU PUNTAJE ES: "+ str(decimal.Decimal(puntajevar)))

                                    if inscripcion.rubros_vencidos():
                                        return HttpResponseRedirect("/?info=No puede acceder a una beca tiene rubros vencidos por pagar")
                        else:
                            if inscripcion.persona.usuario == request.user:
                                matriculaant=None
                                if Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=False).exists():
                                    matriculaactual = Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=False).order_by('-fecha')[:1].get()
                                    if Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=True).order_by('-fecha').exists():
                                        matriculaant = Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=True).order_by('-fecha')[:1].get()
                                        #validar que sean de nivel diferente
                                        if inscripcion.matricula().nivel.nivelmalla_id==matriculaant.nivel.nivelmalla_id:
                                            if inscripcion.matricula().nivel.nivelmalla_id>1:

                                                matriculaant = Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=True,nivel__nivelmalla__id =inscripcion.matricula().nivel.nivelmalla_id).order_by('-fecha')[:1].get()

                                if (not inscripcion.tienediscapacidad and (inscripcion.empresaconvenio==None or inscripcion.empresaconvenio.id==4 )) and ( not matriculaant.tipobeneficio==TipoBeneficio.objects.get(pk=TIPO_BECA_SENESCYT)) and (not autorizacionbode):
                                    if not matriculaant:
                                        return HttpResponseRedirect("/?info=No tiene un nivel anterior para calcular promedio")
                                    puntajevar =calculopromedio(matriculaant,matriculaant.nivel.malla, matriculaant.nivel.nivelmalla)
                                # if not inscripcion.tienediscapacidad or Matricula.objects.filter(inscripcion = inscripcion).count() == 1:
                                #     return HttpResponseRedirect("/?info=No puede acceder a una beca porque se encuentre matricula en el primer nivel, para mas informacion acercarse a Bienestar Estudiantil")
                                # else:
                                #     if not Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=False).exists():
                                #             return HttpResponseRedirect("/?info=No puede acceder a una beca no se encuentra matriculado")


                                if (not inscripcion.tienediscapacidad and (inscripcion.empresaconvenio==None or inscripcion.empresaconvenio.id==4 )) and ( not matriculaant.tipobeneficio==TipoBeneficio.objects.get(pk=TIPO_BECA_SENESCYT)) and (not autorizacionbode):
                                    if puntajevar < PUNTAJE_BECA_NORMAL:
                                        return HttpResponseRedirect("/?info=No puede acceder a una beca la nota general del nivel anterior debe ser mayor o igual a "+str(PUNTAJE_BECA_NORMAL) + "SU PUNTAJE ES: "+ str(decimal.Decimal(puntajevar)))
                                    else:
                                        if inscripcion.rubros_vencidos():
                                            return HttpResponseRedirect("/?info=No puede acceder a una beca tiene rubros vencidos por pagar")
                                else:
                                    if Matricula.objects.filter(inscripcion = inscripcion).count() > 2:
                                        if autorizacionbode== False and autorizacionbecasenecyt== False:
                                            if puntajevar < PUNTAJE_BECA_DISCAPA:
                                                return HttpResponseRedirect("/?info=No puede acceder a una beca la nota general del nivel anterior debe ser mayor o igual a "+str(PUNTAJE_BECA_DISCAPA)+ "SU PUNTAJE ES: "+ str(decimal.Decimal(puntajevar)))
                                            if inscripcion.rubros_vencidos():
                                                return HttpResponseRedirect("/?info=No puede acceder a una beca tiene rubros vencidos por pagar")

                        data['ID_VIVIPROPIA_BECA'] = ID_VIVIPROPIA_BECA
                        data['ID_VIVIARREN_BECA'] = ID_VIVIARREN_BECA
                        data['ID_VIVICEDIDA_BECA'] = ID_VIVICEDIDA_BECA
                        data['ID_TIPVIVOTRO_BECA'] = ID_TIPVIVOTRO_BECA
                        data['ID_DATOECONOTRO_BECA'] = ID_DATOECONOTRO_BECA
                        data['inscripcion'] = inscripcion
                        data['parentesco'] = ParentezcoPersona.objects.all()
                        data['ocupacion'] = OcupacionJefeHogar.objects.all()
                        data['instruccion'] = NivelEstudio.objects.all()
                        data['estadocivil'] = PersonaEstadoCivil.objects.all()
                        data['tipotrabajo'] = FormaTrabajo.objects.all()
                        data['tipovivienda'] = TipoVivienda.objects.filter(id__in=(2,3,4,7))
                        data['teneciavivienda'] = TenenciaVivienda.objects.all()
                        data['personacubregasto'] = PersonaCubreGasto.objects.all()
                        data['tipoingresovivi'] = TipoIngresoVivienda.objects.all()
                        data['tipoegresosvivi'] = TipoEgresoVivienda.objects.all()
                        data['sectorvivi'] = SectorVivienda.objects.all()
                        data['cantonresid'] = Canton.objects.all()
                        if InscripcionFichaSocioEconomicaBeca.objects.filter(inscripcion=inscripcion).exists():
                            inscripcionficha = InscripcionFichaSocioEconomicaBeca.objects.filter(inscripcion=inscripcion)[:1].get()
                            data['inscripcionficha'] = inscripcionficha
                            if DatoResidente.objects.filter(fichabeca=data['inscripcionficha']).exists():
                                data['datoresidentes'] = DatoResidente.objects.filter(fichabeca=data['inscripcionficha'])
                            if 'pag' in request.GET:
                                data['pag'] = request.GET['pag']
                            if DatoTrabajo.objects.filter(fichabeca=data['inscripcionficha'],actual=True).exists():
                                data['datotrabajo'] = DatoTrabajo.objects.filter(fichabeca=data['inscripcionficha'],actual=True)[:1].get()
                            if Detallevivienda.objects.filter(fichabeca=data['inscripcionficha']).exists():
                                data['detallevivienda'] = Detallevivienda.objects.filter(fichabeca=data['inscripcionficha'])[:1].get()
                            if DetalleIngrexEgres.objects.filter(fichabeca=data['inscripcionficha']).exists():
                                data['detalleingrexegres'] = DetalleIngrexEgres.objects.filter(fichabeca=data['inscripcionficha'])
                            if EnfermedadFamilia.objects.filter(fichabeca=data['inscripcionficha']).exists():
                                data['enfermedadfamilia'] = EnfermedadFamilia.objects.filter(fichabeca=data['inscripcionficha'])[:1].get()
                            if ReferenciaBeca.objects.filter(fichabeca=data['inscripcionficha']).exists():
                                data['referenciab'] = ReferenciaBeca.objects.filter(fichabeca=data['inscripcionficha'])
                            if ReferenciaPersonal.objects.filter(fichabeca=data['inscripcionficha']).exists():
                                data['referenciaper'] = ReferenciaPersonal.objects.filter(fichabeca=data['inscripcionficha'])
                                if not inscripcionficha.completo:
                                    inscripcionficha.completo=True
                                    inscripcionficha.datecomple= datetime.now()
                                    inscripcionficha.save()
                            if DatosAcademicos.objects.filter(fichabeca=data['inscripcionficha']).exists():
                                data['datosacademicos'] = DatosAcademicos.objects.filter(fichabeca=data['inscripcionficha'])[:1].get()
                            if DatoTrabajo.objects.filter(fichabeca=data['inscripcionficha'],actual=False).exists():
                                data['datotrabajoant'] = DatoTrabajo.objects.filter(fichabeca=data['inscripcionficha'],actual=False)[:1].get()
                            data['frmcro'] =CroquisForm()


                        data['user'] = request.user
                        data['puedesoli'] = None
                        if inscripcion.matriculado():
                             data['puedesoli'] = 'ok'
                        return render(request ,"beca_solicitud/fichasocio_economicabecarenovar.html" ,  data)
                    return HttpResponseRedirect('beca_solicitud')

                if action == 'addsolibeca':
                    data['title'] = 'Ingresar Datos'
                    if Inscripcion.objects.filter(id=request.GET['id']).exists():
                        inscripcion = Inscripcion.objects.get(id=request.GET['id'])
                        if InscripcionFichaSocioEconomicaBeca.objects.filter(inscripcion = inscripcion,completo=True).exists():
                            if inscripcion.persona.usuario == request.user:
                                data['inscripcion'] = inscripcion
                                if 'error' in request.GET:
                                    data['error'] = request.GET['error']
                                else:
                                    if EMAIL_ACTIVE:
                                        lista = str('dobe@bolivariano.edu.ec')
                                        # lista = str('ocastillo@bolivariano.edu.ec')
                                        hoy = datetime.now().today()
                                        contenido = "FICHA SOCIO-ECONOMICA COMPLETADA - MODULO BECA"
                                        send_html_mail(contenido,
                                            "emails/fichasocioeconomicacompleta.html", {'inscripcion': inscripcion, 'fecha': hoy,'contenido': contenido},lista.split(','))

                                data['form'] = SolicitudBecaForm(initial={'tipo':TIPO_ESPECIE_BECA})




                                return render(request ,"beca_solicitud/addsolibeca.html" ,  data)



                    return HttpResponseRedirect('beca_solicitud')

                if action == 'addsolibecanenovar':
                    data['title'] = 'Ingresar Datos'
                    if Inscripcion.objects.filter(id=request.GET['id']).exists():
                        inscripcion = Inscripcion.objects.get(id=request.GET['id'])
                        if InscripcionFichaSocioEconomicaBeca.objects.filter(inscripcion = inscripcion,completo=True).exists():
                            if inscripcion.persona.usuario == request.user:
                                data['inscripcion'] = inscripcion
                                if 'error' in request.GET:
                                    data['error'] = request.GET['error']
                                # else:
                                #     if EMAIL_ACTIVE:
                                #         lista = str('dobe@bolivariano.edu.ec')
                                #         # lista = str('ocastillo@bolivariano.edu.ec')
                                #         hoy = datetime.now().today()
                                #         contenido = "FICHA SOCIO-ECONOMICA COMPLETADA - MODULO BECA"
                                #         send_html_mail(contenido,
                                #             "emails/fichasocioeconomicacompleta.html", {'inscripcion': inscripcion, 'fecha': hoy,'contenido': contenido},lista.split(','))
                                data['form'] = SolicitudBecaRenovarForm()


                                return render(request ,"beca_solicitud/addrenovarbeca.html" ,  data)
                    return HttpResponseRedirect('beca_solicitud')

                elif action=='editsolibeca':
                    data['title'] = 'Editar Datos'
                    solicitudbeca = SolicitudBeca.objects.get(id=request.GET['id'])
                    data['solicitudbeca'] = solicitudbeca
                    data['inscripcion'] = solicitudbeca.inscripcion
                    data['form'] = SolicitudBecaForm(initial={'motivo':solicitudbeca.motivo})
                    return render(request ,"beca_solicitud/editsolibeca.html" ,  data)

                elif action=='editsolibecarenovar':
                    data['title'] = 'Editar Datos'
                    solicitudbeca = SolicitudBeca.objects.get(id=request.GET['id'])
                    data['solicitudbeca'] = solicitudbeca
                    data['inscripcion'] = solicitudbeca.inscripcion
                    data['form'] = SolicitudBecaRenovarForm(initial={'motivo':solicitudbeca.motivo})
                    return render(request ,"beca_solicitud/editsolibecareno.html" ,  data)

                #INGRESAR UNA GESTION BECA
                elif action=='ingresar_gestion':
                    solicitudbeca = SolicitudBeca.objects.get(pk=int(request.GET['idpreregistro']))
                    data['solicitudbeca']=solicitudbeca
                    data['tipogestionbeca'] = TipoGestionBeca.objects.filter(estado=True)
                    return render(request ,"beca_solicitud/ingresargestionbeca.html" ,  data)
                #VER GESTION BECA
                elif action=='ver_gestionayuda':
                    historial = HistorialGestionBeca.objects.filter(solicitudbeca__id=int(request.GET['idpreregistro'])).order_by('-fecha')
                    data['historial']=historial
                    data['tipogestionbeca'] = TipoGestionBeca.objects.filter()
                    return render(request ,"beca_solicitud/vergestionayuda.html" ,  data)

                elif action=='verresolucionbeca':

                     solicitudbeca = SolicitudBeca.objects.get(id=int(request.GET['idpreregistro']),tiposolicitud=1)
                     data['inscripcion']=solicitudbeca.inscripcion
                     data['solicitud']=solicitudbeca
                     data['historialanalisis']= HistorialGestionBeca.objects.filter(solicitudbeca=solicitudbeca,estado__id=3).order_by('-fecha')[:1].get()
                     tabadescuento= TablaDescuentoBeca.objects.filter(solicitudbeca=solicitudbeca)
                     data['tabadescuento']=tabadescuento


                     if Matricula.objects.filter(inscripcion = solicitudbeca.inscripcion,nivel__cerrado=True).order_by('-fecha').exists():
                         matriculaant = Matricula.objects.filter(inscripcion = solicitudbeca.inscripcion,nivel__cerrado=True).order_by('-fecha')[:1].get()
                         data['matriculaant']=matriculaant
                         nivelmalla= matriculaant.nivel.nivelmalla
                         malla=matriculaant.nivel.malla
                         idasigntauramalla = AsignaturaMalla.objects.filter(asignatura__promedia=True,malla=malla,nivelmalla=nivelmalla).values('asignatura_id')
                         lista = RecordAcademico.objects.filter(inscripcion__id=matriculaant.inscripcion_id,asignatura__promedia=True,asignatura__id__in=idasigntauramalla,aprobada=True)
                         sumanota = 0
                         for recordacedmi in lista:
                                datarecor= RecordAcademico.objects.get(pk=recordacedmi.id)
                                sumanota=sumanota+datarecor.asistencia

                         asistencia = Decimal(sumanota/len(idasigntauramalla)).quantize(Decimal(10)**-2)
                         data['asistencia']=asistencia
                     if PerfilInscripcion.objects.filter(inscripcion = solicitudbeca.inscripcion).exists():
                        data['perfilinscripcion']= PerfilInscripcion.objects.filter(inscripcion = solicitudbeca.inscripcion).order_by('-id')[:1].get()
                     if InscripcionFichaSocioeconomica.objects.filter(inscripcion = solicitudbeca.inscripcion).exists():
                        data['fichasocio']=InscripcionFichaSocioeconomica.objects.filter(inscripcion = solicitudbeca.inscripcion).order_by('-id')[:1].get()
                     resolucionbeca = Resolucionbeca.objects.filter(solicitudbeca=solicitudbeca).order_by('-fecha')[:1].get()
                     data['resolucionbeca']=resolucionbeca

                     return render(request ,"beca_solicitud/resolucionbeca.html" ,  data)



                elif action=='ver_verificacionarchivo':

                    solicitudbeca = SolicitudBeca.objects.get(id=int(request.GET['idpreregistro']),tiposolicitud=1)
                    data['tipoarchivosolicitud'] = ArchivoSolicitudBeca.objects.filter()
                    listaarchivo= ArchivoSoliciBeca.objects.filter(solicitudbeca=solicitudbeca)
                    data['becaverificacion']=solicitudbeca
                    data['listaarchivo']=listaarchivo
                    data['etinia']=solicitudbeca.aprobadoetnia

                    return render(request ,"beca_solicitud/verificacionarchivo.html" ,  data)

                elif action=='validararchivo':

                    solicitudbeca =SolicitudBeca.objects.get(id=int(request.GET['idpreregistro']), tiposolicitud=1)
                    tipoarchivosol=ArchivoSolicitudBeca.objects.get(pk=int(request.GET['idtipoarchivo']))
                    if not ArchivoVerificadoBecaAyuda.objects.filter(solicitudbeca=solicitudbeca, tipoarchivosolicitudbeca=tipoarchivosol).exists():
                        verifico=  ArchivoVerificadoBecaAyuda (solicitudbeca=solicitudbeca,tipoarchivosolicitudbeca=tipoarchivosol, estado=True,
                                                                  usuario=request.user )
                        verifico.save()
                    else:
                        verifico=  ArchivoVerificadoBecaAyuda.objects.filter(solicitudbeca=solicitudbeca,tipoarchivosolicitudbeca=tipoarchivosol)[:1].get()
                        verifico.estado=True
                        verifico.save()

                    loshistorial= HistorialGestionBeca(solicitudbeca=solicitudbeca,inscripcion=solicitudbeca.inscripcion,
                                                                fecha=datetime.now(),estado_id=23, usuario=request.user,comentariocorreo=str('APROBACION')+str(tipoarchivosol.nombre))
                    loshistorial.save()
                    solicitudbeca.idgestion=loshistorial.id
                    solicitudbeca.save()
                    data['etinia'] = solicitudbeca.aprobadoetnia


                    lista = []
                    if solicitudbeca.inscripcion.tienediscapacidad:
                        lispersona= PersonAutorizaBecaAyuda.objects.filter(personadiscapacidad=True)
                        for list in lispersona:
                            lista.append([list.correo])
                    else:
                        lispersona= PersonAutorizaBecaAyuda.objects.filter(personadiscapacidad=True)
                        for list in lispersona:
                            lista.append([list.correo])

                    lista[0][0]=str(lista[0][0])+','+str('dobe@bolivariano.edu.ec')



                    email_estudiante=solicitudbeca.inscripcion.persona.emailinst
                    nivel_est=solicitudbeca

                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(solicitudbeca).pk,
                        object_id       = solicitudbeca.id,
                        object_repr     = force_str(solicitudbeca),
                        action_flag     = ADDITION,
                        change_message  = 'Aceptado el Documento ' +' (' + client_address + ')' )

                    mail_correosolicitud('DOCUMENTO ACEPTADO', 'DOCUMENTO ACEPTADO'+' '+str(tipoarchivosol.nombre), str(lista[0][0]),request.user, elimina_tildes(solicitudbeca.inscripcion.persona.nombre_completo()),elimina_tildes(solicitudbeca.inscripcion.carrera.nombre),email_estudiante,nivel_est)


                    return render(request ,"beca_solicitud/verificacionarchivo.html" ,  data)

                elif action=='rechazararchivo':

                    solicitudbeca = SolicitudBeca.objects.get(id=int(request.GET['idpreregistro']),tiposolicitud=1)
                    tipoarchivosol=ArchivoSolicitudBeca.objects.get(pk=int(request.GET['idtipoarchivo']))
                    if not ArchivoVerificadoBecaAyuda.objects.filter(solicitudbeca=solicitudbeca,tipoarchivosolicitudbeca=tipoarchivosol).exists():
                            verifico=  ArchivoVerificadoBecaAyuda (solicitudbeca=solicitudbeca,tipoarchivosolicitudbeca=tipoarchivosol, estado=False,
                                                                  usuario=request.user )
                            verifico.save()
                    else:
                        verifico=  ArchivoVerificadoBecaAyuda.objects.filter(solicitudbeca=solicitudbeca,tipoarchivosolicitudbeca=tipoarchivosol)[:1].get()
                        verifico.estado=False
                        verifico.save()
                    loshistorial= HistorialGestionBeca(solicitudbeca=solicitudbeca,inscripcion=solicitudbeca.inscripcion,
                                                                fecha=datetime.now(),estado_id=23, usuario=request.user,comentariocorreo=str('RECHAZO')+str(tipoarchivosol.nombre))
                    loshistorial.save()
                    solicitudbeca.idgestion=loshistorial.id
                    solicitudbeca.save()
                    data['etinia'] = solicitudbeca.aprobadoetnia

                    lista = []
                    if solicitudbeca.inscripcion.tienediscapacidad:
                        lispersona= PersonAutorizaBecaAyuda.objects.filter(personadiscapacidad=True)
                        for list in lispersona:
                            lista.append([list.correo])
                    else:
                        lispersona= PersonAutorizaBecaAyuda.objects.filter(personadiscapacidad=True)
                        for list in lispersona:
                            lista.append([list.correo])

                    lista[0][0]=str(lista[0][0])+','+str('dobe@bolivariano.edu.ec')


                    email_estudiante=solicitudbeca.inscripcion.persona.emailinst
                    nivel_est=solicitudbeca

                    mail_correosolicitud(request.GET['comentario'], 'RECHAZO DE DOCUMENTO'+' '+str(tipoarchivosol.nombre), str(lista[0][0]),request.user, elimina_tildes(solicitudbeca.inscripcion.persona.nombre_completo()),elimina_tildes(solicitudbeca.inscripcion.carrera.nombre),email_estudiante,nivel_est)

                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(solicitudbeca).pk,
                        object_id       = solicitudbeca.id,
                        object_repr     = force_str(solicitudbeca),
                        action_flag     = ADDITION,
                        change_message  = 'Rechazado el Documento ' +' (' + client_address + ')' )


                    return render(request ,"beca_solicitud/verificacionarchivo.html" ,  data)

                elif action=='detallearch':
                        data = {}
                        data['archarchivbec'] = ArchivoSoliciBeca.objects.filter(solicitudbeca__id=request.GET['id']).order_by('fecha')
                        data['solicitudbeca'] = SolicitudBeca.objects.get(id=request.GET['id'])
                        data['opc'] = request.GET['opc']
                        data['puedeeditar'] = True
                        data['TIPO_ESPECIE_BECA'] = TIPO_ESPECIE_BECA
                        return render(request ,"beca_solicitud/detallearchivbec.html" ,  data)

                elif action=='detallearchver':
                        data = {}
                        data['archarchivbec'] = ArchivoSoliciBeca.objects.filter(solicitudbeca__id=request.GET['id']).order_by('fecha')
                        data['solicitudbeca'] = SolicitudBeca.objects.get(id=request.GET['id'])
                        data['opc'] = request.GET['opc']
                        data['puedeeditar'] = False
                        data['TIPO_ESPECIE_BECA'] = TIPO_ESPECIE_BECA
                        return render(request ,"beca_solicitud/detallearchivbec.html" ,  data)

                elif action=='renovar':
                        data['title'] = 'Ingresar Datos'
                        if Inscripcion.objects.filter(id=request.GET['id']).exists():
                            inscripcion = Inscripcion.objects.get(id=request.GET['id'])


                            if inscripcion.promocion!=None:
                                if inscripcion.promocion.todos_niveles:
                                    return HttpResponseRedirect("/?info=No puede acceder a una beca porque tiene una promocion para todo los nivel " + str(inscripcion.promocion.descripcion))
                                # else:
                                #    if inscripcion.matricula().nivel.nivelmalla_id==NIVEL_MALLA_UNO:
                                #        return HttpResponseRedirect("/?info=No puede acceder a una beca porque tiene una promocion " + str(inscripcion.promocion.descripcion))



                            if Matricula.objects.filter(inscripcion=inscripcion,nivel=inscripcion.matricula().nivel,becado=True).exists():
                                return HttpResponseRedirect("/?info=No puede acceder a renovar la beca porque ya tiene una en el nivel")


                            if inscripcion.autorizacionbecadobe==False:
                                if inscripcion.matricula().nivel.nivelmalla.id >6 :
                                     return HttpResponseRedirect("/?info=No puede acceder a renovar la beca porque no aplica para este nivel")


                            if InscripcionFichaSocioEconomicaBeca.objects.filter(inscripcion = inscripcion,completo=True).exists():
                                if inscripcion.persona.usuario == request.user:

                                    if inscripcion.matriculado():
                                        if SolicitudBeca.objects.filter(nivel=inscripcion.matricula().nivel,inscripcion=inscripcion,renovarbeca=True,tiposolicitud=1,eliminado=False).exists():
                                            return HttpResponseRedirect("/?info=No puede acceder a renovar la beca porque ya tiene una en el nivel")

                                        if SolicitudBeca.objects.filter(nivel=inscripcion.matricula().nivel,inscripcion=inscripcion,tiposolicitud=1,eliminado=False).exists():
                                            return HttpResponseRedirect("/?info=No puede acceder a una la beca porque ya tiene una en el nivel")


                                    if Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=False,fecha__lt=inscripcion.matricula().fecha,liberada=False).order_by('-fecha').exists():
                                        return HttpResponseRedirect("/?info=No puede acceder a renovar la beca porque el nivel anterior no esta cerrado")

                                    if inscripcion.rubros_vencidos():
                                        return HttpResponseRedirect("/?info=No puede acceder a  renovar la beca porque tiene rubros vencidos por pagar")


                                    if SolicitudBeca.objects.filter(inscripcion=inscripcion).exists():

                                        data['inscripcion'] = inscripcion
                                        data['form'] = SolicitudBecaRenovarForm()
                                        return render(request ,"beca_solicitud/addrenovarbeca.html" ,  data)

                                    else:
                                        data['inscripcion'] = inscripcion
                                        data['form'] = SolicitudBecaRenovarForm()
                                        return render(request ,"beca_solicitud/addrenovarbeca.html" ,  data)
                            else:

                                # if Nivel.objects.filter(pk=inscripcion.matricula().nivel.id,nivelmalla__id=10).exists():
                                #     return HttpResponseRedirect("/?info=Las becas son solamente para los niveles de la carrera. No se aplica en Seminario de Graduacion")

                                data['ID_VIVIPROPIA_BECA'] = ID_VIVIPROPIA_BECA
                                data['ID_VIVIARREN_BECA'] = ID_VIVIARREN_BECA
                                data['ID_VIVICEDIDA_BECA'] = ID_VIVICEDIDA_BECA
                                data['ID_TIPVIVOTRO_BECA'] = ID_TIPVIVOTRO_BECA
                                data['ID_DATOECONOTRO_BECA'] = ID_DATOECONOTRO_BECA
                                data['inscripcion'] = inscripcion
                                data['parentesco'] = ParentezcoPersona.objects.all()
                                data['ocupacion'] = OcupacionJefeHogar.objects.all()
                                data['instruccion'] = NivelEstudio.objects.all()
                                data['estadocivil'] = PersonaEstadoCivil.objects.all()
                                data['tipotrabajo'] = FormaTrabajo.objects.all()
                                data['tipovivienda'] = TipoVivienda.objects.filter(id__in=(2,3,4,7))
                                data['teneciavivienda'] = TenenciaVivienda.objects.all()
                                data['personacubregasto'] = PersonaCubreGasto.objects.all()
                                data['tipoingresovivi'] = TipoIngresoVivienda.objects.all()
                                data['tipoegresosvivi'] = TipoEgresoVivienda.objects.all()
                                data['sectorvivi'] = SectorVivienda.objects.all()
                                data['cantonresid'] = Canton.objects.all()
                                if InscripcionFichaSocioEconomicaBeca.objects.filter(inscripcion=inscripcion).exists():
                                    inscripcionficha = InscripcionFichaSocioEconomicaBeca.objects.filter(inscripcion=inscripcion)[:1].get()
                                    data['inscripcionficha'] = inscripcionficha
                                    if DatoResidente.objects.filter(fichabeca=data['inscripcionficha']).exists():
                                        data['datoresidentes'] = DatoResidente.objects.filter(fichabeca=data['inscripcionficha'])
                                    if 'pag' in request.GET:
                                        data['pag'] = request.GET['pag']
                                    if DatoTrabajo.objects.filter(fichabeca=data['inscripcionficha'],actual=True).exists():
                                        data['datotrabajo'] = DatoTrabajo.objects.filter(fichabeca=data['inscripcionficha'],actual=True)[:1].get()
                                    if Detallevivienda.objects.filter(fichabeca=data['inscripcionficha']).exists():
                                        data['detallevivienda'] = Detallevivienda.objects.filter(fichabeca=data['inscripcionficha'])[:1].get()
                                    if DetalleIngrexEgres.objects.filter(fichabeca=data['inscripcionficha']).exists():
                                        data['detalleingrexegres'] = DetalleIngrexEgres.objects.filter(fichabeca=data['inscripcionficha'])
                                    if EnfermedadFamilia.objects.filter(fichabeca=data['inscripcionficha']).exists():
                                        data['enfermedadfamilia'] = EnfermedadFamilia.objects.filter(fichabeca=data['inscripcionficha'])[:1].get()
                                    if ReferenciaBeca.objects.filter(fichabeca=data['inscripcionficha']).exists():
                                        data['referenciab'] = ReferenciaBeca.objects.filter(fichabeca=data['inscripcionficha'])
                                    if ReferenciaPersonal.objects.filter(fichabeca=data['inscripcionficha']).exists():
                                        data['referenciaper'] = ReferenciaPersonal.objects.filter(fichabeca=data['inscripcionficha'])
                                        if not inscripcionficha.completo:
                                            inscripcionficha.completo=True
                                            inscripcionficha.datecomple= datetime.now()
                                            inscripcionficha.save()
                                    if DatosAcademicos.objects.filter(fichabeca=data['inscripcionficha']).exists():
                                        data['datosacademicos'] = DatosAcademicos.objects.filter(fichabeca=data['inscripcionficha'])[:1].get()
                                    if DatoTrabajo.objects.filter(fichabeca=data['inscripcionficha'],actual=False).exists():
                                        data['datotrabajoant'] = DatoTrabajo.objects.filter(fichabeca=data['inscripcionficha'],actual=False)[:1].get()
                                    data['frmcro'] =CroquisForm()


                                data['user'] = request.user
                                data['puedesoli'] = None
                                if inscripcion.matriculado():
                                        data['puedesoli'] = 'ok'
                                return render(request ,"beca_solicitud/fichasocio_economicabecarenovar.html" ,  data)



                        return HttpResponseRedirect('beca_solicitud')

                elif action == 'eliminar':
                    archivobeca = ArchivoSoliciBeca.objects.get(id=request.GET['id'])
                    solicitudbeca = archivobeca.solicitudbeca
                    if archivobeca.archivo:
                        if (MEDIA_ROOT + '/' + str(archivobeca.archivo)):
                                os.remove(MEDIA_ROOT + '/' + str(archivobeca.archivo))
                    archivobeca.delete()

                    if not ArchivoSoliciBeca.objects.filter(solicitudbeca=solicitudbeca).exists():
                        return HttpResponseRedirect('/beca_solicitud?elim=1')


                    loshistorial= HistorialGestionBeca(solicitudbeca=solicitudbeca,inscripcion=solicitudbeca.inscripcion,
                                                                    fecha=datetime.now(),estado_id=25, usuario=request.user)
                    loshistorial.save()
                    solicitudbeca.idgestion=loshistorial.id
                    solicitudbeca.save()

                    return HttpResponseRedirect('/beca_solicitud')

                elif action == 'aceptarsolibeca':
                    solicitudbeca = SolicitudBeca.objects.get(id=request.GET['id'])
                    solicitudbeca.estadoverificaciondoc=True
                    solicitudbeca.save()
                    inscripcion =Inscripcion.objects.get(pk=solicitudbeca.inscripcion.id)

                    lista = []

                    if inscripcion.persona.emailinst:
                        lista.append([inscripcion.persona.emailinst])
                        # lista[0][0]=str(lista[0][0])+','+str('dobe@bolivariano.edu.ec')
                        if inscripcion.persona.email1:
                            lista.append([inscripcion.persona.email1])

                    if solicitudbeca.inscripcion.tienediscapacidad:
                        lispersona= PersonAutorizaBecaAyuda.objects.filter(personadiscapacidad=True)
                        for list in lispersona:
                            lista.append([list.correo])
                    else:
                        lispersona= PersonAutorizaBecaAyuda.objects.filter(personadiscapacidad=True)
                        for list in lispersona:
                            lista.append([list.correo])

                    lista[0][0]=str(lista[0][0])+','+str('dobe@bolivariano.edu.ec')+','+str('floresvillamarinm@gmail.com')

                    # llenar el log de historial de la solicitud ayuda economica
                    loshistorial= HistorialGestionBeca(solicitudbeca=solicitudbeca,inscripcion=solicitudbeca.inscripcion,
                                                        fecha=datetime.now(),estado_id=12, usuario=request.user,comentariocorreo='APROBACION FINAL DE LOS DOCUMENTOS DE LA SOLICITUD')
                    loshistorial.save()
                    solicitudbeca.idgestion=loshistorial.id
                    solicitudbeca.save()
                    email_estudiante=solicitudbeca.inscripcion.persona.emailinst
                    nivel_est=solicitudbeca

                    mail_correosolicitud('SE REALIZO LA VERIFICACION Y APROBACION DE TODO LOS DOCUMENTOS ADJUNTO A LA SOLICITUD. EN EL TRANSCRUSO DE 7 DIAS TENDRA LA RESOLUCION A SU SOLICITUD. ES NECESARIO QUE ESTE PENDIENTE DE LOS MENSAJES EN SU CORREO ELECTRONICO', 'APROBACION FINAL DE TODO LOS DOCUMENTO ADJUNTO', str(lista[0][0]),request.user, elimina_tildes(solicitudbeca.inscripcion.persona.nombre_completo()),elimina_tildes(solicitudbeca.inscripcion.carrera.nombre),email_estudiante,nivel_est)

                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(solicitudbeca).pk,
                        object_id       = solicitudbeca.id,
                        object_repr     = force_str(solicitudbeca),
                        action_flag     = ADDITION,
                        change_message  = 'Aceptacion final de los Documentos ' +' (' + client_address + ')' )

                    return HttpResponseRedirect('/beca_solicitud?opcion=adm&id='+str(solicitudbeca.inscripcion.id)+'&pag=4')

                elif action == 'agregarvalordescuento':

                    data['inscripcion'] = Inscripcion.objects.get(pk=request.GET['id'])

                    inscripcion=Inscripcion.objects.get(pk=request.GET['id'])

                    solicitudbeca=SolicitudBeca.objects.get(id=request.GET['idsolictudbeca'])

                    data['solicitudbeca'] = solicitudbeca

                    formarchivoanilisis=SolicitudArchivoAyudaForm()
                    data['formanalisisarchivo'] =formarchivoanilisis


                    data['form1'] = BecaParcialForm()

                    # buscar rubro de otro tipo que no sean cuotas para que no se presente como rubro para la beca
                    rubroaux = Rubro.objects.filter(inscripcion=inscripcion, cancelado=False).values_list('id')
                    rubrootro = RubroOtro.objects.filter(rubro__id__in=rubroaux).values_list('rubro_id')
                    rubroespecie=RubroEspecieValorada.objects.filter(rubro__id__in=rubroaux).values_list('rubro_id')
                    rubroinscripcion=RubroInscripcion.objects.filter(rubro__id__in=rubroaux).values_list('rubro_id')

                    if inscripcion.autorizacionbecadobe==False:
                        rubros = Rubro.objects.filter(inscripcion=inscripcion,cancelado=False).values('id').exclude(id__in=rubrootro).exclude(id__in=rubroinscripcion).exclude(id__in=rubroespecie)
                    else:
                        rubros = Rubro.objects.filter(inscripcion=inscripcion,cancelado=False).values('id')

                    pagosrubro=Pago.objects.filter(rubro__id__in=rubroaux,rubro__cancelado=True).values_list('rubro_id')

                    if not inscripcion.matricula():
                             return HttpResponseRedirect("/?info=Actualmente no se encuentra matriculado el nivel que solicito la beca")

                    rubros=rubros.filter().exclude(id__in=pagosrubro)

                    form = DetalleDescuentoBecaForm()
                    form.rubros_list(rubros)

                    if PerfilInscripcion.objects.filter(inscripcion = solicitudbeca.inscripcion).exists():
                        data['perfilinscripcion']= PerfilInscripcion.objects.filter(inscripcion = solicitudbeca.inscripcion).order_by('-id')[:1].get()

                    else:
                        if solicitudbeca.asignaciontarficadescuento == False:


                           solicitudbecaotra = SolicitudBeca.objects.filter(inscripcion=solicitudbeca.inscripcion,tiposolicitud=1).order_by('-fecha')
                           data['solicitudbecas'] = solicitudbecaotra
                           data['TIPO_ESPECIE_BECA'] = TIPO_ESPECIE_BECA
                           data['form1'] = ResponSolicBecaForm()
                           data['hoy'] = datetime.now()
                           # data['form'] = AusenciaJustificadaForm(initial={'fechae': datetime.now().strftime("%d-%m-%Y")})
                           data['form'] = AusenciaJustificadaForm()
                           data['infoactulizaenita'] = True



                           personaautoriza= Persona.objects.get(usuario=request.user)
                           if PersonAutorizaBecaAyuda.objects.filter(persona=personaautoriza,personadiscapacidad=True).exists():
                                data['autorizaapurebadis'] = True
                                data['autorizaapurebanodis'] = True
                                data['aux'] = False
                                data['enviosecr'] = True
                                data['noveringresotabla'] = False

                           if PersonAutorizaBecaAyuda.objects.filter(persona=personaautoriza,personadiscapacidad=False).exists():
                                data['autorizaapurebanodis'] = True
                                data['autorizaapurebadis'] = True
                                data['aux'] = False
                                data['enviosecr'] = True
                                data['noveringresotabla'] = False

                           usuario = User.objects.get(pk=request.user.id)

                           if usuario.groups.filter(id__in=[SECRETARIAGENERAL_GROUP_ID ]).exists():
                                data['secretaria'] = True


                           if usuario.groups.filter(id__in=[SISTEMAS_GROUP_ID ]).exists():
                                data['permitiraprobacion'] = True
                                data['autorizaapurebadis'] = False
                                data['autorizaapurebanodis'] = False
                                data['aux'] = False

                           if usuario.groups.filter(id__in=[DOBE_GROUP_ID ]).exists():
                                data['aux'] = False
                                data['noveringresotabla'] = True




                           data['form31'] = SolicitudBecaNuevaForm()
                           return render(request ,"beca_solicitud/beca_solicitud.html" ,  data)

                    if inscripcion.autorizacionbecadobe==False:
                        data['rubros']= Rubro.objects.filter(inscripcion=data['inscripcion'],cancelado=False).exclude(id__in=rubrootro)
                    else:
                        data['rubros']= Rubro.objects.filter(inscripcion=data['inscripcion'],cancelado=False)
                    data['form']= form
                    return render(request ,"beca_solicitud/descuentopagobeca.html" ,  data)

                elif action == 'editarvalordescuento':

                    data['inscripcion'] = Inscripcion.objects.get(pk=request.GET['id'])

                    inscripcion=Inscripcion.objects.get(pk=request.GET['id'])

                    solicitudbeca=SolicitudBeca.objects.get(id=request.GET['idsolictudbeca'])

                    data['solicitudbeca'] = solicitudbeca

                    data['descuentobeca']= TablaDescuentoBeca.objects.filter(solicitudbeca=solicitudbeca)



                    data['historialanalisis']= HistorialGestionBeca.objects.filter(solicitudbeca=solicitudbeca,estado__id=3).order_by('-fecha')[:1].get()

                    data['form1'] = BecaParcialForm()

                    # buscar rubro de otro tipo que no sean cuotas para que no se presente como rubro para la beca
                    rubroaux = Rubro.objects.filter(inscripcion=inscripcion, cancelado=False).values_list('id')
                    rubrootro = RubroOtro.objects.filter(rubro__id__in=rubroaux).values_list('rubro_id')
                    rubroespecie=RubroEspecieValorada.objects.filter(rubro__id__in=rubroaux).values_list('rubro_id')
                    rubroinscripcion=RubroInscripcion.objects.filter(rubro__id__in=rubroaux).values_list('rubro_id')

                    if inscripcion.autorizacionbecadobe==False:
                        rubros = Rubro.objects.filter(inscripcion=inscripcion,cancelado=False).values('id').exclude(id__in=rubrootro).exclude(id__in=rubroinscripcion).exclude(id__in=rubroespecie)
                    else:
                        rubros = Rubro.objects.filter(inscripcion=inscripcion,cancelado=False).values('id')


                    pagosrubro=Pago.objects.filter(rubro__id__in=rubroaux,rubro__cancelado=True).values_list('rubro_id')

                    rubros=rubros.filter().exclude(id__in=pagosrubro)

                    form = DetalleDescuentoBecaForm()
                    form.rubros_list(rubros)
                    personaautoriza= Persona.objects.get(usuario=request.user)
                    if PersonAutorizaBecaAyuda.objects.filter(persona=personaautoriza,personadiscapacidad=True).exists():
                        data['enviosecr'] = True
                    if PersonAutorizaBecaAyuda.objects.filter(persona=personaautoriza,personadiscapacidad=False).exists():
                        data['enviosecr'] = True


                    data['rubros']= Rubro.objects.filter(inscripcion=data['inscripcion'],cancelado=False).exclude(id__in=rubrootro)
                    data['form']= form
                    resolucionbeca=None
                    if Resolucionbeca.objects.filter(solicitudbeca=solicitudbeca).exists():
                        resolucionbeca = Resolucionbeca.objects.filter(solicitudbeca=solicitudbeca).order_by('-fecha')[:1].get()
                    else:
                         resolucionbeca = Resolucionbeca(solicitudbeca=solicitudbeca,fecha=datetime.now())
                         resolucionbeca.save()
                         numerosolucion= 'ITB-BO-'+str(datetime.now().year)+'-00'+str(resolucionbeca.id)
                         resolucionbeca.numerosolucion=numerosolucion
                         resolucionbeca.save()

                    data['resolucionbeca']=resolucionbeca

                    if Matricula.objects.filter(inscripcion = solicitudbeca.inscripcion,nivel__cerrado=True).order_by('-fecha').exists():
                        matriculaant = Matricula.objects.filter(inscripcion = solicitudbeca.inscripcion,nivel__cerrado=True).order_by('-fecha')[:1].get()
                        #validar que sean de nivel diferente
                        if inscripcion.matricula():
                            if inscripcion.matricula().nivel.nivelmalla_id==matriculaant.nivel.nivelmalla_id:
                                 if inscripcion.matricula().nivel.nivelmalla_id>1:

                                    matriculaant = Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=True,nivel__nivelmalla__id =inscripcion.matricula().nivel.nivelmalla_id).order_by('-fecha')[:1].get()
                        else:
                             matriculaant = Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=True).order_by('-fecha')[:1].get()
                        data['matriculaant']=matriculaant
                        nivelmalla= matriculaant.nivel.nivelmalla
                        malla=matriculaant.nivel.malla
                        idasigntauramalla = AsignaturaMalla.objects.filter(asignatura__promedia=True,malla=malla,nivelmalla=nivelmalla).values('asignatura_id')
                        lista = RecordAcademico.objects.filter(inscripcion__id=matriculaant.inscripcion_id,asignatura__promedia=True,asignatura__id__in=idasigntauramalla,aprobada=True)
                        sumanota = 0
                        for recordacedmi in lista:
                                datarecor= RecordAcademico.objects.get(pk=recordacedmi.id)
                                sumanota=sumanota+datarecor.asistencia

                        if len(idasigntauramalla)>0:
                            asistencia = Decimal(sumanota/len(idasigntauramalla)).quantize(Decimal(10)**-2)
                        else:
                            asistencia=0
                        data['asistencia']=asistencia

                    if PerfilInscripcion.objects.filter(inscripcion = solicitudbeca.inscripcion).exists():
                        data['perfilinscripcion']= PerfilInscripcion.objects.filter(inscripcion = solicitudbeca.inscripcion).order_by('-id')[:1].get()

                    if InscripcionFichaSocioeconomica.objects.filter(inscripcion = solicitudbeca.inscripcion).exists():
                        data['fichasocio']=InscripcionFichaSocioeconomica.objects.filter(inscripcion = solicitudbeca.inscripcion).order_by('-id')[:1].get()

                    if ArchivoSoliciAnalisisBeca.objects.filter(solicitudbeca=solicitudbeca).exists():
                       data['archivoanalisis']=ArchivoSoliciAnalisisBeca.objects.filter(solicitudbeca=solicitudbeca).order_by('-id')[:1].get()

                    formarchivoanilisis = SolicitudArchivoAyudaForm()

                    data['formanalisisarchivo'] = formarchivoanilisis

                    return render(request ,"beca_solicitud/editardescuentopagobeca.html" ,  data)


                elif action == 'reenviaranalisis':

                    data['inscripcion'] = Inscripcion.objects.get(pk=request.GET['id'])

                    inscripcion=Inscripcion.objects.get(pk=request.GET['id'])

                    solicitudbeca=SolicitudBeca.objects.get(id=request.GET['idsolictudbeca'])

                    data['solicitudbeca'] = solicitudbeca

                    formarchivoanilisis=SolicitudArchivoAyudaForm()
                    data['formanalisisarchivo'] =formarchivoanilisis

                    data['descuentobeca']= TablaDescuentoBeca.objects.filter(solicitudbeca=solicitudbeca)

                    data['form1'] = BecaParcialForm()

                    # buscar rubro de otro tipo que no sean cuotas para que no se presente como rubro para la beca
                    rubroaux = Rubro.objects.filter(inscripcion=inscripcion, cancelado=False).values_list('id')
                    rubrootro = RubroOtro.objects.filter(rubro__id__in=rubroaux).values_list('rubro_id')
                    rubroespecie=RubroEspecieValorada.objects.filter(rubro__id__in=rubroaux).values_list('rubro_id')
                    rubroinscripcion=RubroInscripcion.objects.filter(rubro__id__in=rubroaux).values_list('rubro_id')

                    if inscripcion.autorizacionbecadobe==False:
                        rubros = Rubro.objects.filter(inscripcion=inscripcion,cancelado=False).values('id').exclude(id__in=rubrootro).exclude(id__in=rubroinscripcion).exclude(id__in=rubroespecie)
                    else:
                        rubros = Rubro.objects.filter(inscripcion=inscripcion,cancelado=False).values('id')


                    pagosrubro=Pago.objects.filter(rubro__id__in=rubroaux).values_list('rubro_id')
                    rubros=rubros.filter().exclude(id__in=pagosrubro)
                    form = DetalleDescuentoBecaForm()
                    form.rubros_list(rubros)
                    personaautoriza= Persona.objects.get(usuario=request.user)
                    if PersonAutorizaBecaAyuda.objects.filter(persona=personaautoriza,personadiscapacidad=True).exists():
                        data['enviosecr'] = True
                    if PersonAutorizaBecaAyuda.objects.filter(persona=personaautoriza,personadiscapacidad=False).exists():
                        data['enviosecr'] = True

                    if inscripcion.autorizacionbecadobe==False:
                        data['rubros']= Rubro.objects.filter(inscripcion=data['inscripcion'],cancelado=False).exclude(id__in=rubrootro)
                    else:
                        data['rubros']= Rubro.objects.filter(inscripcion=data['inscripcion'],cancelado=False)
                    data['form']= form
                    return render(request ,"beca_solicitud/reenviaranalisis.html" ,  data)

                elif action == 'versolicitudesbecasecretaria':

                    inscripciones = Inscripcion.objects.filter(id__in=SolicitudBeca.objects.filter(tiposolicitud__in=LISTA_TIPO_BECA,estadosolicitud__id=6).values('inscripcion'),).order_by('-solicitudbeca__fecha')

                    data['inscripciones']=inscripciones


                    return render(request ,"beca_solicitud/consultabecasecretaria.html" ,  data)


                elif action == 'ingresarrevision':
                    solicitudbeca=SolicitudBeca.objects.get(id=request.GET['idsolictudbeca'])
                    data['solicitudbeca']=solicitudbeca
                    formrevision=SolicitudRevisionAplicada()
                    data['form']= formrevision

                    return render(request ,"beca_solicitud/agregarrevision.html" ,  data)




                elif action == 'tipodocumenbeca':
                    search = None
                    todos = None

                    if 's' in request.GET:
                        search = request.GET['s']

                    if search:
                        ss = search.split(' ')
                        while '' in ss:
                            ss.remove('')

                        tipodocu = TipoDocumenBeca.objects.filter(descripcion__icontains=search).order_by('descripcion')
                    else:
                        tipodocu = TipoDocumenBeca.objects.all().order_by('descripcion')

                    paging = MiPaginador(tipodocu, 30)
                    p = 1
                    try:
                        if 'page' in request.GET:
                            p = int(request.GET['page'])
                        page = paging.page(p)
                    except:
                        page = paging.page(1)

                    data['paging'] = paging
                    data['rangospaging'] = paging.rangos_paginado(p)
                    data['page'] = page
                    data['search'] = search if search else ""
                    data['todos'] = todos if todos else ""
                    data['tipodocu'] = page.object_list
                    return render(request ,"beca_solicitud/tipodocumbeca.html" ,  data)


                elif action == 'tenencia':
                    search = None
                    todos = None

                    if 's' in request.GET:
                        search = request.GET['s']

                    if search:
                        ss = search.split(' ')
                        while '' in ss:
                            ss.remove('')

                        tenenciavivi = TenenciaVivienda.objects.filter(descripcion__icontains=search).order_by('descripcion')
                    else:
                        tenenciavivi = TenenciaVivienda.objects.all().order_by('descripcion')

                    paging = MiPaginador(tenenciavivi, 30)
                    p = 1
                    try:
                        if 'page' in request.GET:
                            p = int(request.GET['page'])
                        page = paging.page(p)
                    except:
                        page = paging.page(1)

                    data['paging'] = paging
                    data['rangospaging'] = paging.rangos_paginado(p)
                    data['page'] = page
                    data['search'] = search if search else ""
                    data['todos'] = todos if todos else ""
                    data['tenenciavivi'] = page.object_list
                    return render(request ,"beca_solicitud/tenenciavivienda.html" ,  data)


                elif action == 'ingresovivienda':
                    search = None
                    todos = None

                    if 's' in request.GET:
                        search = request.GET['s']

                    if search:
                        ss = search.split(' ')
                        while '' in ss:
                            ss.remove('')

                        tipoingresosvivi = TipoIngresoVivienda.objects.filter(descripcion__icontains=search).order_by('descripcion')
                    else:
                        tipoingresosvivi = TipoIngresoVivienda.objects.all().order_by('descripcion')

                    paging = MiPaginador(tipoingresosvivi, 30)
                    p = 1
                    try:
                        if 'page' in request.GET:
                            p = int(request.GET['page'])
                        page = paging.page(p)
                    except:
                        page = paging.page(1)

                    data['paging'] = paging
                    data['rangospaging'] = paging.rangos_paginado(p)
                    data['page'] = page
                    data['search'] = search if search else ""
                    data['todos'] = todos if todos else ""
                    data['tipoingresosvivi'] = page.object_list
                    return render(request ,"beca_solicitud/tipoingresovivienda.html" ,  data)


                elif action == 'egresovivienda':
                    search = None
                    todos = None

                    if 's' in request.GET:
                        search = request.GET['s']

                    if search:
                        ss = search.split(' ')
                        while '' in ss:
                            ss.remove('')

                        tipoegresosvivi = TipoEgresoVivienda.objects.filter(descripcion__icontains=search).order_by('descripcion')
                    else:
                        tipoegresosvivi = TipoEgresoVivienda.objects.all().order_by('descripcion')

                    paging = MiPaginador(tipoegresosvivi, 30)
                    p = 1
                    try:
                        if 'page' in request.GET:
                            p = int(request.GET['page'])
                        page = paging.page(p)
                    except:
                        page = paging.page(1)

                    data['paging'] = paging
                    data['rangospaging'] = paging.rangos_paginado(p)
                    data['page'] = page
                    data['search'] = search if search else ""
                    data['todos'] = todos if todos else ""
                    data['tipoegresosvivi'] = page.object_list
                    return render(request ,"beca_solicitud/tipoegresovivienda.html" ,  data)



                elif action == 'sectorvivienda':
                    search = None
                    todos = None

                    if 's' in request.GET:
                        search = request.GET['s']

                    if search:
                        ss = search.split(' ')
                        while '' in ss:
                            ss.remove('')

                        sectorvivi = SectorVivienda.objects.filter(descripcion__icontains=search).order_by('descripcion')
                    else:
                        sectorvivi = SectorVivienda.objects.all().order_by('descripcion')

                    paging = MiPaginador(sectorvivi, 30)
                    p = 1
                    try:
                        if 'page' in request.GET:
                            p = int(request.GET['page'])
                        page = paging.page(p)
                    except:
                        page = paging.page(1)

                    data['paging'] = paging
                    data['rangospaging'] = paging.rangos_paginado(p)
                    data['page'] = page
                    data['search'] = search if search else ""
                    data['todos'] = todos if todos else ""
                    data['sectorvivi'] = page.object_list
                    return render(request ,"beca_solicitud/sectorvivienda.html" ,  data)
            else:

                search = None
                todos = None
                if 'idestado' in request.GET:
                    idestado=int(request.GET['idestado'])
                else:
                    idestado=0

                if 's' in request.GET:
                    search = request.GET['s']

                if search:
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')
                    if len(ss)==1:
                       if  idestado==0:
                            inscripciones = SolicitudBeca.objects.filter(Q(Q(inscripcion__persona__nombres__icontains=search) | Q(inscripcion__persona__apellido1__icontains=search) | Q(inscripcion__persona__apellido2__icontains=search) | Q(inscripcion__persona__cedula__icontains=search) | Q(inscripcion__persona__pasaporte__icontains=search)),tiposolicitud=1).order_by('-fecha')
                       else:
                           inscripciones = SolicitudBeca.objects.filter(Q(Q(inscripcion__persona__nombres__icontains=search) | Q(inscripcion__persona__apellido1__icontains=search) | Q(inscripcion__persona__apellido2__icontains=search) | Q(inscripcion__persona__cedula__icontains=search) | Q(inscripcion__persona__pasaporte__icontains=search)),tiposolicitud=1, estadosolicitud__id=idestado).order_by('-fecha')
                    else:
                       if  idestado==0:
                            inscripciones = SolicitudBeca.objects.filter(Q(Q(inscripcion__persona__nombres__icontains=search) | Q(inscripcion__persona__apellido1__icontains=ss[0]) | Q(inscripcion__persona__apellido2__icontains=ss[1]) | Q(inscripcion__persona__cedula__icontains=search) | Q(inscripcion__persona__pasaporte__icontains=search)),tiposolicitud=1,eliminado=False).order_by('-fecha')
                       else:
                            inscripciones = SolicitudBeca.objects.filter(Q(Q(inscripcion__persona__nombres__icontains=search) | Q(inscripcion__persona__apellido1__icontains=ss[0]) | Q(inscripcion__persona__apellido2__icontains=ss[1]) | Q(inscripcion__persona__cedula__icontains=search) | Q(inscripcion__persona__pasaporte__icontains=search)),tiposolicitud=1,eliminado=False, estadosolicitud__id=idestado).order_by('-fecha')
                else:
                    if idestado==0:
                        inscripciones = SolicitudBeca.objects.filter(tiposolicitud=1,eliminado=False).order_by('-fecha')
                    else:
                        inscripciones = SolicitudBeca.objects.filter(tiposolicitud=1,eliminado=False, estadosolicitud__id=idestado).order_by('-fecha')
                data['idestado']=idestado

                if Inscripcion.objects.filter(persona__usuario=request.user).exists():
                    matriculaant = ''
                    inscripcion = Inscripcion.objects.get(persona__usuario=request.user)
                    autorizacionbode= False
                    autorizacionbecasenecyt= False

                    if inscripcion.autorizacionbecadobe:
                        autorizacionbode=True

                    if inscripcion.autorizacionbecasenecyt:
                        autorizacionbecasenecyt=True


                    solicitudbeca = SolicitudBeca.objects.filter(inscripcion = inscripcion,tiposolicitud=1,eliminado=False).order_by('-fecha')
                    if Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=False,liberada=False).exists():
                        matriculaactual = Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=False,liberada=False).order_by('-fecha')[:1].get()
                        if Matricula.objects.filter(Q(nivel__cerrado=True) | Q(liberada=True),inscripcion = inscripcion).order_by('-fecha').exists():
                            matriculaant = Matricula.objects.filter(Q(nivel__cerrado=True) | Q(liberada=True),inscripcion = inscripcion).order_by('-fecha')[:1].get()

                            #validar que sean de nivel diferente
                            if matriculaactual.nivel.nivelmalla_id==matriculaant.nivel.nivelmalla_id:
                                if matriculaactual.nivel.nivelmalla_id>1:
                                    idniecel=matriculaactual.nivel.nivelmalla_id-1
                                    matriculaant = Matricula.objects.filter(Q(nivel__cerrado=True) | Q(liberada=True),inscripcion = inscripcion,nivel__nivelmalla__id =idniecel).order_by('-fecha')[:1].get()

                    else:
                        matriculaactual = ''


                    if not matriculaactual:
                        return HttpResponseRedirect("/?info=No esta matriculado actualmente")



                    # prueba
                    data['matriculaactual'] = matriculaactual
                    puntajevar=0

                    if matriculaant:
                        if matriculaant.tipobeneficio==TipoBeneficio.objects.get(pk=TIPO_BECA_SENESCYT) or matriculaant.tipobeca==TipoBeca.objects.get(pk=7):
                            auxmateria=True
                        else:
                            auxmateria=False
                    else:
                        auxmateria=False

                    if (not inscripcion.tienediscapacidad and (inscripcion.empresaconvenio==None or inscripcion.empresaconvenio.id==4 )) and (not auxmateria) and (not autorizacionbode) and (not autorizacionbecasenecyt):
                        if not matriculaant:
                            return HttpResponseRedirect("/?info=No tiene un nivel anterior para sacar promedio")
                        puntajevar =calculopromedio(matriculaant,matriculaant.nivel.malla, matriculaant.nivel.nivelmalla)
                        if puntajevar>100:
                            return HttpResponseRedirect("/?info=No se ingresar al modulo porque el promedio del nivel anterior es mayor a 100 ")

                        if puntajevar< PUNTAJE_BECA_NORMAL:
                                        return HttpResponseRedirect("/?info=No puede acceder a una beca la nota general del nivel anterior debe ser mayor o igual a "+ str(PUNTAJE_BECA_NORMAL) + "SU PUNTAJE ES: "+ str(decimal.Decimal(puntajevar)))
                        # else:
                        #     if inscripcion.rubros_vencidos():
                        #         return HttpResponseRedirect("/?info=No puede acceder a una beca tiene rubros vencidos por pagar")
                        #     else:
                        #         if not Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=False).exists():
                        #             return HttpResponseRedirect("/?info=No puede acceder a una beca no se encuentra matriculado")

                    if not solicitudbeca:
                        # if Matricula.objects.filter(inscripcion = inscripcion).count() > 2 and Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=False).exists():
                        if Matricula.objects.filter(inscripcion = inscripcion).count() > 2:
                            matricula = Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=True).order_by('-fecha')[:1].get()
                            if (not inscripcion.tienediscapacidad and (inscripcion.empresaconvenio==None or inscripcion.empresaconvenio.id==4 )) and (not auxmateria) and (not autorizacionbode) and (not autorizacionbecasenecyt):
                                #OCastillo 30-05-2019 verifica si hay materias reprobadas en el historico
                                if not RecordAcademico.objects.filter(inscripcion__id=matricula.inscripcion_id,asignatura__promedia=True,aprobada=False,fecha__lt=matriculaactual.fecha).exists():
                                    # if RecordAcademico.objects.filter(inscripcion__id=matricula.inscripcion_id,asignatura__promedia=True,asignatura__id__in=MateriaAsignada.objects.filter(matricula=matricula).values('materia__asignatura')).aggregate(Avg('nota'))['nota__avg'] < PUNTAJE_BECA_NORMAL:
                                    if puntajevar< PUNTAJE_BECA_NORMAL:
                                        return HttpResponseRedirect("/?info=No puede acceder a una beca la nota general del nivel anterior debe ser mayor o igual a "+ str(PUNTAJE_BECA_NORMAL) + "SU PUNTAJE ES: "+ str(decimal.Decimal(puntajevar)))
                                    else:
                                        if inscripcion.rubros_vencidos():
                                            return HttpResponseRedirect("/?info=No puede acceder a una beca tiene rubros vencidos por pagar")
                                        # else:
                                        #     if not Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=False).exists():
                                        #         return HttpResponseRedirect("/?info=No puede acceder a una beca no se encuentra matriculado")
                                else:
                                    return HttpResponseRedirect("/?info=No puede acceder a una beca tiene materias reprobadas en su record academico")
                            else:
                                # if RecordAcademico.objects.filter(inscripcion__id=matricula.inscripcion_id,asignatura__promedia=True,asignatura__id__in=MateriaAsignada.objects.filter(matricula=matricula).values('materia__asignatura')).aggregate(Avg('nota'))['nota__avg'] < PUNTAJE_BECA_DISCAPA:

                                if Matricula.objects.filter(inscripcion = inscripcion).count() > 2:

                                    if autorizacionbode== False and autorizacionbecasenecyt== False:
                                        puntajevar =calculopromedio(matriculaant,matriculaant.nivel.malla, matriculaant.nivel.nivelmalla)
                                        if puntajevar< PUNTAJE_BECA_DISCAPA:
                                            return HttpResponseRedirect("/?info=No puede acceder a una beca la nota general del nivel anterior debe ser mayor o igual a "+ str(PUNTAJE_BECA_DISCAPA)  + "SU PUNTAJE ES: "+ str(decimal.Decimal(puntajevar)))
                                        else:
                                            if inscripcion.rubros_vencidos():
                                                return HttpResponseRedirect("/?info=No puede acceder a una beca tiene rubros vencidos por pagar")
                                            else:
                                                if not Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=False).exists():
                                                    return HttpResponseRedirect("/?info=No puede acceder a una beca no se encuentra matriculado")

                        else:
                            if autorizacionbode== False and autorizacionbecasenecyt== False:
                                if RecordAcademico.objects.filter(inscripcion=inscripcion,asignatura__promedia=True,aprobada=False,fecha__lt=inscripcion.matricula().fecha).exists():
                                        return HttpResponseRedirect("/?info=No puede acceder a una beca tiene materias reprobadas en su record academico")

                    else:

                        if autorizacionbode== False and autorizacionbecasenecyt== False:
                            if RecordAcademico.objects.filter(inscripcion=inscripcion,asignatura__promedia=True,aprobada=False,fecha__lt=inscripcion.matricula().fecha).exists():
                                        return HttpResponseRedirect("/?info=No puede acceder a una beca tiene materias reprobadas en su record academico")


                        form = SolicitudBecaForm()

                        data['form3'] =form
                        form31=SolicitudBecaNuevaForm()
                        data['form31'] =form31

                    if inscripcion.empresaconvenio!=None:
                        if inscripcion.empresaconvenio.id!=4:
                                return HttpResponseRedirect("/?info=No puede acceder a una beca porque tiene convenio " + str(inscripcion.empresaconvenio.nombre))



                    if inscripcion.promocion!=None:
                        if inscripcion.promocion.todos_niveles:
                            return HttpResponseRedirect("/?info=No puede acceder a una beca porque tiene una promocion para todo los nivel " + str(inscripcion.promocion.descripcion))
                        # else:
                        #    if matriculaactual.nivel.nivelmalla_id==NIVEL_MALLA_UNO:
                        #        return HttpResponseRedirect("/?info=No puede acceder a una beca porque tiene una promocion " + str(inscripcion.promocion.descripcion))



                    # permiso de registrar una nueva solicitud
                    if not SolicitudBeca.objects.filter(nivel=inscripcion.matricula().nivel,inscripcion=inscripcion,tiposolicitud=1,eliminado=False).exists():
                            data['puedesoli'] = 'ok'

                    data['inscripcion'] = inscripcion

                    if 'elim' in request.GET:
                        data['error'] = 'El registro fue eliminado'
                    if 'edit' in request.GET:
                        archivo = ArchivoSoliciBeca.objects.get(id=request.GET['edit'])
                        data['edit'] = archivo
                    data['opcion'] = 'inscrip'

                elif not 'opcion' in request.GET:
                    paging = MiPaginador(inscripciones, 30)
                    if 'inicio' in request.GET and 'fin' in request.GET:
                        inicio = request.GET['inicio']
                        fin = request.GET['fin']
                        inscripciones = inscripciones.filter(fecha__gte=inicio, fecha__lte=fin)
                        data['inicio'] = datetime.strptime(inicio,'%Y-%m-%d').date()
                        data['fin'] = datetime.strptime(fin,'%Y-%m-%d').date()
                        paging = MiPaginador(inscripciones, 300)

                    p = 1
                    try:
                        if 'page' in request.GET:
                            p = int(request.GET['page'])
                        page = paging.page(p)
                    except:
                        page = paging.page(1)

                    data['paging'] = paging
                    data['rangospaging'] = paging.rangos_paginado(p)
                    data['page'] = page
                    data['search'] = search if search else ""
                    data['todos'] = todos if todos else ""
                    data['inscripciones'] = page.object_list
                    data['opcion'] = 'adm'

                    data['tipogestion'] = TipoEstadoSolicitudBeca.objects.filter()
                    return render(request,"beca_solicitud/inscripcionbeca.html",  data)
                else:
                    solicitudbeca = SolicitudBeca.objects.filter(inscripcion=request.GET['id'],tiposolicitud=1,eliminado=False).order_by('-fecha')
                    data['inscrificha'] = Inscripcion.objects.get(id=request.GET['id'])
                    # data['form'] = AusenciaJustificadaForm(initial={'fechae': datetime.now().strftime("%d-%m-%Y")})
                    data['form'] = AusenciaJustificadaForm()

                paging = MiPaginador(solicitudbeca, 30)

                data['solicitudbecas'] = solicitudbeca
                data['TIPO_ESPECIE_BECA'] = TIPO_ESPECIE_BECA
                data['form1'] = ResponSolicBecaForm()
                data['hoy'] = datetime.now()
                # data['form'] = AusenciaJustificadaForm(initial={'fechae': datetime.now().strftime("%d-%m-%Y")})
                data['form'] = AusenciaJustificadaForm()
                if 'error' in request.GET:
                    data['error'] = request.GET['error']
                data['aux'] = True


                personaautoriza= Persona.objects.get(usuario=request.user)
                if PersonAutorizaBecaAyuda.objects.filter(persona=personaautoriza,personadiscapacidad=True).exists():
                    data['autorizaapurebadis'] = True
                    data['autorizaapurebanodis'] = True
                    data['aux'] = False
                    data['enviosecr'] = True
                    data['noveringresotabla'] = False
                    data['permitircambioprogramacion'] = True
                    data['finalizarautomatico'] = True

                if PersonAutorizaBecaAyuda.objects.filter(persona=personaautoriza,personadiscapacidad=False).exists():
                    data['autorizaapurebanodis'] = True
                    data['autorizaapurebadis'] = True
                    data['aux'] = False
                    data['enviosecr'] = True
                    data['finalizarautomatico'] = True
                    data['noveringresotabla'] = False
                    data['permitircambioprogramacion'] = True

                usuario = User.objects.get(pk=request.user.id)

                if usuario.groups.filter(id__in=[SECRETARIAGENERAL_GROUP_ID ]).exists():
                    data['secretaria'] = True


                if usuario.groups.filter(id__in=[SISTEMAS_GROUP_ID ]).exists():
                    data['permitiraprobacion'] = True
                    data['autorizaapurebadis'] = False
                    data['autorizaapurebanodis'] = False
                    data['aux'] = False
                    data['noveringresotabla'] = True
                    data['finalizarautomatico'] = True
                    data['permitircambioprogramacion'] = True
                    data['verresolucion'] = True


                if usuario.groups.filter(id__in=[DOBE_GROUP_ID ]).exists():
                    data['aux'] = False
                    data['noveringresotabla'] = True
                    data['finalizarautomatico'] = True
                    data['verresolucion'] = True

                if usuario.groups.filter(id__in=[ID_AUDITOR_INTERNO]).exists():
                    data['eliminar'] = False
                else:
                    data['eliminar'] = True

                data['usuario'] = usuario




                data['form31'] = SolicitudBecaNuevaForm()
                return render(request,"beca_solicitud/beca_solicitud.html",data)

    except Exception as e:
        return HttpResponseRedirect("/?info= error contacte con el administrador " + str(e))

def mail_correosolicitud(contenido,asunto,email,user,estudiante,carrera,email_estudiante,nivel_est):
        hoy = datetime.now().today()
        persona = Persona.objects.get(usuario=user)
        send_html_mail(str(asunto),"emails/correoalumno.html", {'fecha': hoy,"user":user,'contenido': contenido, 'asunto': asunto,'persona':persona,'estudiante':estudiante,'carrera':carrera,'email_estudiante':email_estudiante,'nivel_est':nivel_est},email.split(","))

def mail_correosolicitudsecretaria(contenido,email,user,estudiante,carrera,email_estudiante,nivel_est,tabladescuento,historialultima):
        hoy = datetime.now().today()
        persona = Persona.objects.get(usuario=user)
        send_html_mail(str('ENVIO DE LA INFORMACION DE BECA PARA SU REVISION'),"emails/correosecretaria.html", {'fecha': hoy,"user":user,'contenido': contenido,'persona':persona,'estudiante':estudiante,'carrera':carrera,'email_estudiante':email_estudiante,'nivel_est':nivel_est,'descuentobeca':tabladescuento,'ultimoanalisis':historialultima},email.split(","))

def mail_correosolicitudsecretariaaplica(contenido,email,user,estudiante,carrera,email_estudiante,nivel_est):
        hoy = datetime.now().today()
        persona = Persona.objects.get(usuario=user)
        send_html_mail(str('ENVIO INFORMACION DE LA BECA QUE SE APLICO'),"emails/correoaplicosecretaria.html", {'fecha': hoy,"user":user,'contenido': contenido,'persona':persona,'estudiante':estudiante,'carrera':carrera,'email_estudiante':email_estudiante,'nivel_est':nivel_est},email.split(","))



def calculopromedio(matriculaac,malla,nivelmalla):
    lista=[]
    idasigntauramalla = AsignaturaMalla.objects.filter(asignatura__promedia=True,malla=malla,nivelmalla=nivelmalla).values('asignatura_id')
    lista = RecordAcademico.objects.filter(inscripcion__id=matriculaac.inscripcion_id,asignatura__promedia=True,asignatura__id__in=idasigntauramalla,aprobada=True)
    sumanota = 0
    puntaje = 0
    for recordacedmi in lista:
        datarecor= RecordAcademico.objects.get(pk=recordacedmi.id)
        sumanota=sumanota+datarecor.nota
    if idasigntauramalla:
        puntaje = Decimal(sumanota/len(idasigntauramalla)).quantize(Decimal(10)**-2)

    return puntaje
