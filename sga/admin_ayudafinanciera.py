
from datetime import datetime,time
import json
import decimal
import os
from django.contrib.admin.models import LogEntry, ADDITION,DELETION,CHANGE
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
from decorators import secure_module
from med.models import PersonaEstadoCivil
from settings import PUNTAJE_BECA_DISCAPA, PUNTAJE_BECA_NORMAL,TIPO_ESPECIE_BECA, MEDIA_ROOT, EMAIL_ACTIVE, ID_VIVIPROPIA_BECA, ID_VIVIARREN_BECA, ID_VIVICEDIDA_BECA, ID_TIPVIVOTRO_BECA, ID_DATOECONOTRO_BECA,SISTEMAS_GROUP_ID,SECRETARIAGENERAL_GROUP_ID,DOBE_GROUP_ID, NIVEL_MALLA_UNO
from sga.commonviews import addUserData, ip_client_address
from sga.forms import SolicitudBecaForm, ResponSolicBecaForm, CroquisForm,AusenciaJustificadaForm, SolicitudBecaNuevaForm,SolicitudAyudaFinancieraForm,ResponSolicAyudaEconomicaForm,SolicitudArchivoAyudaForm, BecaParcialForm, DetalleDescuentoBecaForm, SolicitudRevisionAplicada
from sga.models import SolicitudBeca, Inscripcion, Matricula, MateriaAsignada,TipoDocumenBeca, ArchivoSoliciBeca,Persona, TenenciaVivienda,TipoIngresoVivienda,TipoEgresoVivienda,SectorVivienda, \
     Canton,HistoricoRecordAcademico,Rubro,Nivel,RubroEspecieValorada, RecordAcademico, AsignaturaMalla,HistorialGestionAyudaEconomica,ArchivoSoliciAyudaFinanciera,PersonAutorizaBecaAyuda,ArchivoVerificadoBecaAyuda, TablaDescuentoBeca, ArchivoSoliciAnalisisBeca, Resolucionbeca,PerfilInscripcion, RubroOtro, RubroInscripcion, Pago, RubroCuota, RubroMatricula, TipoEstadoSolicitudBeca, ArchivoSolicitudBeca, TipoGestionBeca
from django.db.models.aggregates import Sum, Avg
from decimal import Decimal
from sga.tasks import send_html_mail
from sga.reportes import elimina_tildes
from socioecon.models import ParentezcoPersona, OcupacionJefeHogar, NivelEstudio, FormaTrabajo, TipoVivienda, PersonaCubreGasto, InscripcionFichaSocioEconomicaBeca, DatoResidente, DatoTrabajo, Detallevivienda, DetalleIngrexEgres, EnfermedadFamilia,ReferenciaBeca,DatosAcademicos,ReferenciaPersonal,InscripcionFichaSocioeconomica
from django.contrib.auth.models import User



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
                            tabadescuento=  TablaDescuentoBeca(solicitudbeca=solicitudbeca,inscripcion=inscripcion,
                                                              rubro=rubro,valorubro=rubro.valor,
                                                              descuento=d['porc'],fecha = datetime.now(),estado=True,
                                                              usuario=request.user,descripcion=rubro.nombre())
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
                        loshistorial= HistorialGestionAyudaEconomica(solicitudbeca=solicitudbeca,inscripcion=solicitudbeca.inscripcion,
                                                                    fecha=datetime.now(),estado_id=3, usuario=request.user,archivoanalisis=archivobeca,comentariocorreo=request.POST['comentario'],
                                                                    tipobeca_id=int(request.POST['idtipobeca']),motivobeca_id=int(request.POST['idtipomotivo']),
                                                                    porcentajebeca=Decimal(request.POST['porcentajebeca']).quantize(Decimal(10)**-2))
                        loshistorial.save()

                        resolucionbeca = Resolucionbeca(solicitudbeca=solicitudbeca,fecha=datetime.now())
                        resolucionbeca.save()
                        numerosolucion= 'ITB-BO-'+str(datetime.now().year)+'-00'+str(resolucionbeca.id)
                        resolucionbeca.numerosolucion=numerosolucion
                        resolucionbeca.save()
                        solicitudbeca.idgestion=loshistorial.id
                        solicitudbeca.save()
                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(solicitudbeca).pk,
                            object_id       = solicitudbeca.id,
                            object_repr     = force_str(solicitudbeca),
                            action_flag     = ADDITION,
                            change_message  = 'Ingreso archivo de analisis ayuda financiera (' + client_address + ')' )



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



            elif action == 'addrevision':
                solicitudbeca=SolicitudBeca.objects.get(id=request.POST['solicitudinscrip'])


                loshistorial= HistorialGestionAyudaEconomica(solicitudbeca=solicitudbeca,inscripcion=solicitudbeca.inscripcion,
                                                                fecha=datetime.now(),estado_id=26, usuario=request.user,
                                                                comentariocorreo=elimina_tildes(request.POST['comentario']))
                loshistorial.save()

                solicitudbeca.estadosolicitud_id=7
                solicitudbeca.idgestion=loshistorial.id
                solicitudbeca.save()

                return HttpResponseRedirect('/admin_ayudafinanciera?opcion=adm&id='+str(solicitudbeca.inscripcion.id))


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
                        if xtipo.tipo_id==4:
                            datorubo.tiponivelpago=0
                        else:
                            i=i+1
                            datorubo.tiponivelpago=i
                        datorubo.save()



                    for x in rubroactualizar:
                        if x.rubro.tiponivelpago>0:
                            if not RubroCuota.objects.filter(rubro=x.rubro).exists():
                                rubcu=RubroCuota(rubro=x.rubro,matricula=matriculaactual,cuota=x.rubro.tiponivelpago)
                                rubcu.save()
                        else:

                             if not RubroMatricula.objects.filter(rubro=x.rubro).exists():
                                rubma=RubroMatricula(rubro=x.rubro,matricula=matriculaactual)
                                rubma.save()


                    if RubroOtro.objects.filter(rubro__in=idrubrotro).exists():
                       rubrootro=RubroOtro.objects.filter(rubro__in=idrubrotro)
                       rubrootro.delete()

                    result['cargarurl']='/admin_ayudafinanciera?opcion=adm&id='+str(solicitudbeca.inscripcion_id)
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
                        mail_correosolicitudayuda(request.POST['descripcion'], str("Proceso Solicitud de Beca"), str(strcorreo),request.user, elimina_tildes(inscripcion.persona.nombre_completo()),elimina_tildes(inscripcion.carrera.nombre),email_estudiante,nivel_est)
                        solicitudbeca.estadosolicitud_id =2

                    if(int(request.POST['idtipogestion'])) == 8: # en secretaria
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
                        if HistorialGestionAyudaEconomica.objects.filter(solicitudbeca=solicitudbeca,estado__id=1,aprobado=True).exists():
                            result['result'] ="bad"
                            result['message'] ="No se puede ingresar la gestion porque ya esta en ese estado"
                            return HttpResponse(json.dumps(result),content_type="application/json")

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

                    loshistorial= HistorialGestionAyudaEconomica(solicitudbeca=solicitudbeca,inscripcion=solicitudbeca.inscripcion,
                                                                fecha=datetime.now(), estado_id=int(request.POST['idtipogestion']), usuario=request.user,comentariocorreo=request.POST['descripcion'])
                    loshistorial.save()
                    solicitudbeca.idgestion = loshistorial.id
                    solicitudbeca.save()
                    result['result'] ="ok"
                    return HttpResponse(json.dumps(result),content_type="application/json")
                except Exception as e:
                    result['result'] ="bad"
                    return HttpResponse(json.dumps(result),content_type="application/json")

            elif action == 'tienearchivo':
                try:
                    if ArchivoSoliciBeca.objects.filter(solicitudbeca__id = request.POST['id']).exists():
                        return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
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
                        loshistorial= HistorialGestionAyudaEconomica(solicitudbeca=solicitudbeca,inscripcion=solicitudbeca.inscripcion,
                                                                    fecha=datetime.now(),estado_id=3, usuario=request.user,archivoanalisis=archivobeca,comentariocorreo=request.POST['comentario'],
                                                                    tipobeca_id=int(request.POST['idtipobeca']),motivobeca_id=int(request.POST['idtipomotivo']),
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
                            change_message  = 'Ingreso archivo de analisis ayuda financiera (' + client_address + ')' )



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


            elif action == 'guardarmanualtabladescuentobeca':
                try:

                    rubro = Rubro.objects.get(pk=int(request.POST['rubroid']))
                    solicitudbeca= SolicitudBeca.objects.get(id=int(request.POST['becaid']))

                    if not TablaDescuentoBeca.objects.filter(solicitudbeca=solicitudbeca, rubro=rubro).exists():
                        tabadescuento=  TablaDescuentoBeca(solicitudbeca=solicitudbeca,inscripcion=solicitudbeca.inscripcion,
                                                          rubro=rubro,valorubro=rubro.valor,
                                                          descuento=request.POST['porcentaje'],fecha = datetime.now(),estado=True,
                                                          usuario=request.user)
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




            elif action == 'guardareditartabladescuentobeca':
                try:

                    tabadescuento=  TablaDescuentoBeca.objects.get(id=int(request.POST['rubroid']))
                    tabadescuento.descuento=request.POST['porcentaje']
                    tabadescuento.save()

                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(tabadescuento).pk,
                        object_id       = tabadescuento.id,
                        object_repr     = force_str(tabadescuento),
                        action_flag     = CHANGE,
                        change_message  = 'Edicion tabla de descuento ayuda financiera (' + client_address + ')' )

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
                        change_message  = 'Eliminacion rubro tabla de descuento ayuda financiera beca (' + client_address + ')' )

                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")


            elif action == 'aprobarsolicitudestudiante':

                    try:
                        result = {}
                        result['result'] ="ok"
                        solicitudbeca = SolicitudBeca.objects.filter(pk=int(request.POST['idssolic']),tiposolicitud=2).get()
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

                        result['cargarurl']='/admin_ayudafinanciera'

                        loshistorial= HistorialGestionAyudaEconomica(solicitudbeca=solicitudbeca,inscripcion=solicitudbeca.inscripcion,
                                                            fecha=datetime.now(),estado_id=18, usuario=request.user,comentariocorreo=request.POST['contenido'])
                        loshistorial.save()
                        solicitudbeca.idgestion=loshistorial.id
                        solicitudbeca.save()
                        email_estudiante=solicitudbeca.inscripcion.persona.emailinst
                        nivel_est=solicitudbeca

                        mail_correosolicitudayuda(elimina_tildes(request.POST['contenido']), str('APROBACION POR EL ESTUDIANTE DE SOLICITUD DE BECA'), str(lista[0][0]),request.user, elimina_tildes(solicitudbeca.inscripcion.persona.nombre_completo()),elimina_tildes(solicitudbeca.inscripcion.carrera.nombre),email_estudiante,nivel_est)

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



            elif action == 'aprobratabladescuento':
                try:
                    inscripcion = Inscripcion.objects.get(id=int(request.POST['inscripcion']))
                    solicitudbeca= SolicitudBeca.objects.get(id=int(request.POST['becaid']))

                    # llenar el log de historial de la solicitud beca
                    loshistorial= HistorialGestionAyudaEconomica(solicitudbeca=solicitudbeca,inscripcion=solicitudbeca.inscripcion,
                                                                fecha=datetime.now(),estado_id=20, usuario=request.user,comentariocorreo='APROBACION DE TABLA DE DESCUENTO DE BECA POR JEFE DOBE')
                    loshistorial.save()
                    solicitudbeca.idgestion=loshistorial.id
                    solicitudbeca.asignaciontarficadescuento=True
                    solicitudbeca.save()

                    resolucionbeca = Resolucionbeca.objects.get(solicitudbeca=solicitudbeca)
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
                        change_message  = 'Aprobacion tabla de descuento ayuda beca (' + client_address + ')' )

                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")


            elif action == 'rechazartabladescuento':
                try:
                    inscripcion = Inscripcion.objects.get(id=int(request.POST['inscripcion']))
                    solicitudbeca= SolicitudBeca.objects.get(id=int(request.POST['becaid']))

                    # llenar el log de historial de la solicitud beca
                    loshistorial= HistorialGestionAyudaEconomica(solicitudbeca=solicitudbeca,inscripcion=solicitudbeca.inscripcion,
                                                                fecha=datetime.now(),estado_id=21, usuario=request.user,comentariocorreo='APROBACION DE TABLA DE DESCUENTO DE BECA POR JEFE DOBE')
                    loshistorial.save()
                    solicitudbeca.idgestion=loshistorial.id
                    solicitudbeca.asignaciontarficadescuento=False
                    solicitudbeca.envioanalisis=False
                    solicitudbeca.save()

                    resolucionbeca = Resolucionbeca.objects.get(solicitudbeca=solicitudbeca)
                    resolucionbeca.estado=False
                    resolucionbeca.save()

                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(solicitudbeca).pk,
                        object_id       = solicitudbeca.id,
                        object_repr     = force_str(solicitudbeca),
                        action_flag     = ADDITION,
                        change_message  = 'Rechazo tabla de descuento ayuda beca (' + client_address + ')' )

                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")


            elif action == 'addsolicitud':
                f = SolicitudAyudaFinancieraForm(request.POST,request.FILES)
                inscripcion = Inscripcion.objects.get(id=request.POST['inscrip'])
                autorizacionbode= False
                aprobacionayudadobe=False
                if inscripcion.autorizacionbecadobe:
                    autorizacionbode=True

                if inscripcion.aprobacionayudadobe:
                    aprobacionayudadobe=True

                puntaje = 0
                try:
                    solicitudbeca = None
                    archivobeca = None
                    if f.is_valid():
                        nivel = None

                        if not 'edit' in request.POST :



                            if not inscripcion.matriculado():
                                return HttpResponseRedirect("/?info=No puede acceder a una ayuda economica porque no se encuentra matriculado")

                            if inscripcion.matriculado():
                                if SolicitudBeca.objects.filter(nivel=inscripcion.matricula().nivel,inscripcion=inscripcion,tiposolicitud=2,eliminado=False).exists():
                                    return HttpResponseRedirect("/?info=Ya tiene Ingresar una ayuda en el nivel ")

                            # esta matriculo
                            if Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=False).exists():
                                matriculaactual = Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=False).order_by('-fecha')[:1].get()
                                nivel = matriculaactual.nivel
                            # data['matriculaactual'] = matriculaactual


                            if SolicitudBeca.objects.filter(inscripcion=inscripcion,renovarbeca=True,nivel=nivel,aprobado=False,eliminado=False).exists():
                                return HttpResponseRedirect("/?info=Ya existe una renovacion de solicitud en el nivel y esta en proceso")

                            # validar que no tenga solicitud de beca ingresada ya en el nivel
                            if SolicitudBeca.objects.filter(nivel=inscripcion.matricula().nivel,inscripcion=inscripcion,tiposolicitud=1).exists():
                               if not SolicitudBeca.objects.filter(nivel=inscripcion.matricula().nivel,inscripcion=inscripcion,tiposolicitud=1,estadosolicitud__id=3,aprobado=False,eliminado=False).exists():
                                    return HttpResponseRedirect("/?info=No puede acceder a una ayuda economica porque tiene una solicitud de beca ingresada en el nivel matriculado")


                            # evaluar que no tenga solicitud ayuda en el nivel actual que se encuentra
                            if SolicitudBeca.objects.filter(inscripcion = inscripcion,nivel=inscripcion.matricula().nivel,tiposolicitud=2,eliminado=False).exists():
                                if not SolicitudBeca.objects.filter(inscripcion = inscripcion,nivel=inscripcion.matricula().nivel,tiposolicitud=2,estadosolicitud__id=3,aprobado=False,eliminado=False).exists():
                                    return HttpResponseRedirect("/?info=No puede acceder a una ayuda economica porque ya se encuentra registra una en el nivel")


                            #  si tiene discapacidad
                            if not inscripcion.tienediscapacidad or not autorizacionbode:
                                if aprobacionayudadobe == False:
                                    if RecordAcademico.objects.filter(inscripcion=inscripcion,asignatura__promedia=True,aprobada=False,fecha__lt=inscripcion.matricula().fecha).exists():
                                            return HttpResponseRedirect("/?info=No puede acceder a una beca tiene materias reprobadas en su record academico")

                                # OCU validacion 3 matriculado en Seminario no aplica beca ok
                                if Nivel.objects.filter(pk=matriculaactual.nivel.id,nivelmalla__id=10).exists() and not inscripcion.existe_solicitud_beca():
                                    return HttpResponseRedirect("/?info=Las becas son solamente para los niveles de la carrera. No se aplica en Seminario de Graduacion")
                            else:
                                # si tiene matriculdo en el segundo nivel
                                if inscripcion.matricula().nivel.nivelmalla_id > 1:
                                    if aprobacionayudadobe == False:
                                        if RecordAcademico.objects.filter(inscripcion=inscripcion,asignatura__promedia=True,aprobada=False,fecha__lt=inscripcion.matricula().fecha).exists():
                                            return HttpResponseRedirect("/?info=No puede acceder a una beca tiene materias reprobadas en su record academico")

                                        if Nivel.objects.filter(pk=matriculaactual.nivel.id,nivelmalla__id=10).exists() and not inscripcion.existe_solicitud_beca():
                                            return HttpResponseRedirect("/?info=Las becas son solamente para los niveles de la carrera. No se aplica en Seminario de Graduacion")

                        if 'edit' in request.POST :
                            solicitudbeca = SolicitudBeca.objects.get(id = request.POST['edit'])
                            solicitudbeca.motivo =  f.cleaned_data['motivo']
                            solicitudbeca.puntaje = 0
                            solicitudbeca.fecha = datetime.now()
                            mensaje = 'Edicion'

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
                                                        puntaje = 0,
                                                        estadosolicitud_id=1,
                                                        fecha = datetime.now(),
                                                        tiposolicitud=2)
                        solicitudbeca.save()

                    else:
                        return HttpResponseRedirect("/admin_ayudafinanciera?action=addsolibeca&error=EL tipo al guardar la solicitud de ayuda&id="+str(inscripcion.id))
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(solicitudbeca).pk,
                    object_id       = solicitudbeca.id,
                    object_repr     = force_str(solicitudbeca),
                    action_flag     = ADDITION,
                    change_message  = mensaje +' de Solicitude de ayuda financiera (' + client_address + ')' )
                    if EMAIL_ACTIVE:
                        lista = str('dobe@bolivariano.edu.ec')
                        # lista = str('floresvillamarinm@gmail.com')
                        # lista = str('ocastillo@bolivariano.edu.ec')
                        hoy = datetime.now().today()
                        contenido = "SOLICITUD DE AYUDA ECONOMICA"
                        send_html_mail(contenido,
                            "emails/solicitudayudafinanciera.html", {'solicitudayuda': solicitudbeca, 'fecha': hoy,'contenido': contenido},lista.split(','))
                    return HttpResponseRedirect("/admin_ayudafinanciera")

                except Exception as ex:
                    if solicitudbeca:
                        solicitudbeca.delete()
                    if archivobeca:
                        archivobeca.delete()
                    return HttpResponseRedirect("/admin_ayudafinanciera?action=addsolibeca&error=Ocurrio un error intentelo nuevamente&id="+str(inscripcion.id))

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

                    if 'inscfichadita' in request.POST:
                        return HttpResponseRedirect('/admin_ayudafinanciera?action=verfichasocioecono&id='+str(inscripficha.inscripcion.id)+'&pag=4')
                    else:
                        return HttpResponseRedirect('/admin_ayudafinanciera?action=fichasocioecono&id='+str(inscripficha.inscripcion.id)+'&pag=4')
                else:
                    return HttpResponseRedirect('/admin_ayudafinanciera?error=el archivo no tiene el formato correcto')

            elif action == 'addarchivo':
                f = ResponSolicAyudaEconomicaForm(request.POST,request.FILES)
                if f.is_valid():
                    solicitudbeca = SolicitudBeca.objects.get(id=request.POST['idsolici'])
                    if 'archivoanalisis' in request.FILES:
                        archivo = request.FILES['archivoanalisis']
                        archivobeca= ArchivoSoliciAyudaFinanciera(
                                                    solicitudbeca = solicitudbeca,
                                                    archivo = request.FILES['archivoanalisis'],
                                                    fecha = datetime.now())

                    archivobeca.save()
                    solicitudbeca.estadosolicitud_id=5
                    solicitudbeca.save()

                    # llenar el log de historial de la solicitud ayuda economica
                    loshistorial= HistorialGestionAyudaEconomica(solicitudbeca=solicitudbeca,inscripcion=solicitudbeca.inscripcion,
                                                                fecha=datetime.now(),estado_id=3, usuario=request.user,archivoanalisis=archivobeca)
                    loshistorial.save()
                    solicitudbeca.idgestion=loshistorial.id
                    solicitudbeca.save()
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(archivobeca).pk,
                        object_id       = archivobeca.id,
                        object_repr     = force_str(archivobeca),
                        action_flag     = ADDITION,
                        change_message  = 'Ingreso archivo de analisis ayuda financiera (' + client_address + ')' )

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
                            "emails/solicitudbecarchivo.html", {'solicitudbeca': solicitudbeca, 'archivobeca':archivobeca, 'fecha': hoy,'contenido': 'ANALISIS DE LA SOLICITUD'},email.split(","))

                    return HttpResponseRedirect('/admin_ayudafinanciera')

                else:
                    return HttpResponseRedirect('/admin_ayudafinanciera?error=el archivo no tiene el formato correcto')


            elif action == 'addarchivoestudiante':
                f = SolicitudBecaNuevaForm(request.POST,request.FILES)
                if f.is_valid():
                    solicitudbeca = SolicitudBeca.objects.get(id=request.POST['idsolici'])
                    if 'archivo' in request.FILES:
                        archivo = request.FILES['archivo']
                    else:
                        archivo = ''
                    if ArchivoSoliciBeca.objects.filter().exists():
                        idarch= ArchivoSoliciBeca.objects.filter().order_by('-fecha')[:1].get().id +1
                    else:
                        idarch=1
                    if request.POST['editar'] == '0':
                        archivobeca= ArchivoSoliciBeca(id=idarch,
                                                    solicitudbeca = solicitudbeca,
                                                    tipodocumenbeca = f.cleaned_data['tipo'],
                                                    archivo = request.FILES['archivo'],
                                                    fecha = datetime.now())
                        mensaje = 'Ingreso'
                        archivobeca.save()
                        # llenar el log de historial de la solicitud beca
                        loshistorial= HistorialGestionAyudaEconomica(solicitudbeca=solicitudbeca,inscripcion=solicitudbeca.inscripcion,
                                                                    fecha=datetime.now(),estado_id=6, usuario=request.user,archivosubeestudiante=archivobeca)
                        loshistorial.save()
                        solicitudbeca.idgestion=loshistorial.id
                        solicitudbeca.save()
                        contenido = "EL ESTUDIANTE ADJUNTO ARCHIVO " + str(f.cleaned_data['tipo'])
                    else:
                        archivobeca = ArchivoSoliciBeca.objects.get(id = request.POST['editar'])

                        if str(archivobeca.archivo):
                            if (MEDIA_ROOT + '/' + str(archivobeca.archivo)) and archivo:
                                os.remove(MEDIA_ROOT + '/' + str(archivobeca.archivo))

                        if archivo:
                            archivobeca.archivo = archivo
                            archivobeca.fecha = datetime.now()
                        archivobeca.tipodocumenbeca_id = request.POST['tipo']

                        mensaje = 'Edicion'
                        archivobeca.save()
                        loshistorial= HistorialGestionAyudaEconomica(solicitudbeca=solicitudbeca,inscripcion=solicitudbeca.inscripcion,
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

                    if request.POST['editar'] == '0':
                        return HttpResponseRedirect('/admin_ayudafinanciera')
                    else:
                        return HttpResponseRedirect('/admin_ayudafinanciera?edit='+str(request.POST['editar']))
                else:
                    return HttpResponseRedirect('/admin_ayudafinanciera?error=el archivo no tiene el formato correcto')

            elif action == 'addrespuest':
                solicitudbeca = SolicitudBeca.objects.get(pk=int(request.POST['idsolicires']))
                f = ResponSolicAyudaEconomicaForm(request.POST)
                if f.is_valid():

                    if f.cleaned_data['aprobado']==True:
                        if solicitudbeca.asignaciontarficadescuento==False or solicitudbeca.asignaciontarficadescuento==None :
                            data = {'title':'Solicitud de beca'}
                            inscripciones = Inscripcion.objects.filter(id__in=SolicitudBeca.objects.filter(tiposolicitud=2,eliminado=False).distinct('puntaje').values('inscripcion__id')).order_by('solicitudbeca__puntaje','-solicitudbeca__fecha')
                            data['inscripciones'] = inscripciones
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


                            return render(request ,"ayudafinanciera/solicitud_ayudafinanciera.html" ,  data)



                    solicitudbeca.aprobado = f.cleaned_data['aprobado']
                    solicitudbeca.observacion = f.cleaned_data['observacion']
                    solicitudbeca.fechaproces = datetime.now()
                    solicitudbeca.usuario = request.user
                    solicitudbeca.estadosolicitud_id=3
                    solicitudbeca.save()

                    if solicitudbeca.aprobado:
                        mensaje="aprobada"
                    else:
                        mensaje = "no aprobada"
                        solicitudbeca.asignaciontarficadescuento=False

                    solicitudbeca.save()

                    # llenar el log de historial de la solicitud ayuda economica
                    loshistorial= HistorialGestionAyudaEconomica(solicitudbeca=solicitudbeca,inscripcion=solicitudbeca.inscripcion,
                                                                fecha=datetime.now(),estado_id=1, usuario=request.user,aprobado=solicitudbeca.aprobado,comentariocorreo=f.cleaned_data['observacion'])
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
                        change_message  = 'Solicitud de beca Ayuda Economica'+ mensaje +' (' + client_address + ')' )
                    if EMAIL_ACTIVE:
                        if solicitudbeca.inscripcion.persona.emailinst:
                            if solicitudbeca.aprobado:
                                solicitudbeca.mail_aprobacionayudafinancieraalumno('TE COMUNICAMOS QUE TU BECA HA SIDO PREAPROBADA. NECESITAMOS QUE INGRESES A TU SGA AL MODULO SOLICITUD DE BECAS Y EN LAS ACCIONES ESCOGER ACEPTAR TERMINOS Y CONDICIONES DE BECA, PARA QUE CONTINUE EL TRAMITE, CASO CONTRARIO NO SE CONTINUARA CON EL PROCESO',request.user)
                            else:
                                solicitudbeca.mail_aprobacionayudafinanciera('AYUDA FINNACIERA NO APROBADA',request.user)

                    return HttpResponseRedirect('/admin_ayudafinanciera')

            elif action == 'correosolicitud':
                try:
                    solicitudbeca = SolicitudBeca.objects.get(pk=int(request.POST['insc']))
                    inscripcion =solicitudbeca.inscripcion
                    result = {}
                    result['result'] ="ok"

                    usuario = request.user
                    user=Persona.objects.get(usuario=usuario)
                    if EMAIL_ACTIVE:
                        lista = []
                        if inscripcion.persona.emailinst:
                            lista.append([inscripcion.persona.emailinst])
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
                            result['cargarurl']='/admin_ayudafinanciera?opcion=adm&id='+str(solicitudbeca.inscripcion_id)
                            solicitudbeca.fechaenviocorreo=datetime.now()
                            solicitudbeca.usuarioenviocorreo=usuario
                            solicitudbeca.estadosolicitud_id=2
                            solicitudbeca.save()
                            # llenar el log de historial de la solicitud ayuda economica
                            loshistorial= HistorialGestionAyudaEconomica(solicitudbeca=solicitudbeca,inscripcion=solicitudbeca.inscripcion,
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
                                change_message  = 'Solicitud de ayuda financiera '+ 'envio de mensaje' +' (' + client_address + ')' )
                            mail_correosolicitudayuda(request.POST['contenido'], request.POST['asunto'], str(lista[0][0]),request.user, elimina_tildes(inscripcion.persona.nombre_completo()),elimina_tildes(inscripcion.carrera.nombre),email_estudiante,nivel_est)
                        else:
                            return HttpResponse(json.dumps({"result":"noexist"}),content_type="application/json")

                    return HttpResponse(json.dumps(result),content_type="application/json")
                except:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")


            elif action == 'eliminarayuda':
                  try:
                        result = {}
                        result['result'] ="ok"
                        solicitudbeca = SolicitudBeca.objects.filter(pk=request.POST['idssolic'],tiposolicitud=2).get()
                        solicitudbeca.eliminado=True
                        solicitudbeca.estadosolicitud_id=3
                        solicitudbeca.save()

                        loshistorial= HistorialGestionAyudaEconomica(solicitudbeca=solicitudbeca,inscripcion=solicitudbeca.inscripcion,
                                                            fecha=datetime.now(),estado_id=17, usuario=request.user,comentariocorreo=request.POST['contenido'])
                        loshistorial.save()
                        solicitudbeca.idgestion=loshistorial.id
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

                        email_estudiante=solicitudbeca.inscripcion.persona.emailinst
                        nivel_est=solicitudbeca

                        result['cargarurl']='/admin_ayudafinanciera?opcion=adm&id='+str(solicitudbeca.inscripcion_id)

                        mail_correosolicitudayuda(request.POST['contenido'], 'ELIMINACION DE SOLICITUD DE BECA', str(lista[0][0]),request.user, elimina_tildes(solicitudbeca.inscripcion.persona.nombre_completo()),elimina_tildes(solicitudbeca.inscripcion.carrera.nombre),email_estudiante,nivel_est)


                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(solicitudbeca).pk,
                        object_id       = solicitudbeca.id,
                        object_repr     = force_str(solicitudbeca),
                        action_flag     = DELETION,
                        change_message  = 'Solicitud' +' de Ayuda Financiera Eliminada (' + client_address + ')' )


                        return HttpResponse(json.dumps(result),content_type="application/json")

                  except Exception as e:
                    result['result'] ="bad"
                    return HttpResponse(json.dumps(result),content_type="application/json")


            elif action == 'correoenviosecretaria':
                try:
                    result = {}
                    result['result'] ="ok"
                    usuario = request.user
                    user=Persona.objects.get(usuario=usuario)
                    if EMAIL_ACTIVE:
                        lista = []
                        lista = []
                        solicitudbeca = SolicitudBeca.objects.get(pk=int(request.POST['idssolic']))
                        # lispersona= PersonAutorizaBecaAyuda.objects.filter(personasecretaria=True)
                        # for list in lispersona:
                        # lista.append(['secretariageneral@bolivariano.edu.ec'])
                        # lista[0][0]=str(lista[0][0])+','+str('sga@bolivariano.edu.ec')
                        mail= str('secretariageneral@bolivariano.edu.ec')+','+ str('szuniga@bolivariano.edu.ec')+','+ str('mmora@bolivariano.edu.ec') +','+ str('floresvillamarinm@gmail.com')


                        result['cargarurl']='/admin_ayudafinanciera?opcion=adm&id='+str(solicitudbeca.inscripcion_id)
                        solicitudbeca.estadosolicitud_id=6
                        solicitudbeca.save()

                        loshistorial= HistorialGestionAyudaEconomica(solicitudbeca=solicitudbeca,inscripcion=solicitudbeca.inscripcion,
                                                            fecha=datetime.now(),estado_id=8, usuario=request.user,comentariocorreo=request.POST['contenido'])
                        loshistorial.save()

                        tabladescuento= TablaDescuentoBeca.objects.filter(solicitudbeca=solicitudbeca)

                        historialultima= HistorialGestionAyudaEconomica.objects.filter(solicitudbeca=solicitudbeca,estado__id=3).order_by('-fecha')[:1].get()
                        solicitudbeca.idgestion=loshistorial.id
                        solicitudbeca.save()

                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(solicitudbeca).pk,
                            object_id       = solicitudbeca.id,
                            object_repr     = force_str(solicitudbeca),
                            action_flag     = ADDITION,
                            change_message  = 'Solicitud de ayuda financiera '+ 'envio de mensaje a secretaria' +' (' + client_address + ')' )

                        mail_correosolicitudsecretaria(str(elimina_tildes(request.POST['contenido'])), mail,request.user, elimina_tildes(solicitudbeca.inscripcion.persona.nombre_completo()),elimina_tildes(solicitudbeca.inscripcion.carrera.nombre),solicitudbeca.inscripcion.persona.emailinst,solicitudbeca,tabladescuento,historialultima)


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

                        solicitudbeca.estadosolicitud_id=7
                        solicitudbeca.save()
                        result['cargarurl']='/admin_ayudafinanciera?opcion=adm&id='+str(solicitudbeca.inscripcion_id)
                        loshistorial= HistorialGestionAyudaEconomica(solicitudbeca=solicitudbeca,inscripcion=solicitudbeca.inscripcion,
                                                            fecha=datetime.now(),estado_id=9, usuario=request.user,comentariocorreo=request.POST['contenido'])
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
                            change_message  = 'Aplicaciob Solicitud de beca '+ 'por secretaria' +' (' + client_address + ')' )
                        mail_correosolicitudsecretariaaplica(str(elimina_tildes(request.POST['contenido'])), str(lista[0][0]),request.user, elimina_tildes(solicitudbeca.inscripcion.persona.nombre_completo()),elimina_tildes(solicitudbeca.inscripcion.carrera.nombre),solicitudbeca.inscripcion.persona.emailinst,solicitudbeca)


                    return HttpResponse(json.dumps(result),content_type="application/json")
                except:
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
                                if idexist.id == int(d['iddatoresi']):
                                    existe = 1
                                    break
                            if existe == 0:
                                idexist.delete()

                        for d in datos:

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
                                if idexist.id == int(d['iddatoref']):
                                    existe = 1
                                    break
                            if existe == 0:
                                idexist.delete()

                        for d in datos:

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
                                if idexist.id == int(d['iddatoref']):
                                    existe = 1
                                    break
                            if existe == 0:
                                idexist.delete()

                        for d in datos:

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


            elif action == 'guardareditartabladescuentobecaayuda':
                try:

                    f = SolicitudArchivoAyudaForm(request.POST, request.FILES)
                    if f.is_valid():

                        solicitudbeca = SolicitudBeca.objects.get(id=int(request.POST['becaid']))
                        archivobeca = None
                        tabadescuento = TablaDescuentoBeca.objects.filter(solicitudbeca=solicitudbeca)

                        if 'id_archivoanalisis' in request.FILES:
                            archivobeca = ArchivoSoliciAyudaFinanciera(
                                solicitudbeca=solicitudbeca,
                                archivo=request.FILES['id_archivoanalisis'],
                                fecha=datetime.now())

                            archivobeca.save()

                        datoshistorial=HistorialGestionAyudaEconomica.objects.get(pk=int(request.POST['idhistorial']))

                        if 'id_archivoanalisis' in request.FILES:
                            datoshistorial.archivoanalisis=archivobeca

                        datoshistorial.comentariocorreo=request.POST['comentario']
                        datoshistorial.tipobeca_id=int(request.POST['idtipobeca'])
                        datoshistorial.motivobeca_id=int(request.POST['idtipomotivo'])
                        datoshistorial.porcentajebeca=Decimal(request.POST['porcentajebeca']).quantize(Decimal(10) ** -2)


                        datoshistorial.save()

                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id=request.user.pk,
                            content_type_id=ContentType.objects.get_for_model(solicitudbeca).pk,
                            object_id=solicitudbeca.id,
                            object_repr=force_str(solicitudbeca),
                            action_flag=CHANGE,
                            change_message='Analisis de Ayuda Editado (' + client_address + ')')

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



                            send_html_mail('ENVIO DE CORREO  ANALISIS DE AYUDA FINANCIERA POR EDICION',
                                           "emails/solicitudanalisis.html",
                                           {'solicitudbeca': solicitudbeca, 'archivobeca': archivobeca, 'fecha': hoy,
                                            'contenido': 'ANALISIS DE LA AYUDA FINANCIERA EDITADA', 'descuentobeca': tabadescuento,
                                            'comentarioanalisis': elimina_tildes(request.POST['comentario'])}, email.split(","))

                            return HttpResponse(json.dumps({"result": "ok"}), content_type="application/json")

                    else:
                        return HttpResponse(json.dumps({"result": "archivobad"}), content_type="application/json")

                except Exception as ex:
                    return HttpResponse(json.dumps({"result": "bad"}), content_type="application/json")



            elif action=='fechaespecie':
                # OCastillo 02-mayo-2017 para nueva validez de especie 45 dias
                fechaespecie=request.POST['fechaespecie']
                fe=(convertir_fecha(fechaespecie)).date()
                diasvalidez = (datetime.now().date()- fe).days

                if diasvalidez >45:
                   return HttpResponse(json.dumps({"result":"bad","dias":diasvalidez}),content_type="application/json")
                else:
                   return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")



            elif action == 'eliminar':
                    archivobeca = ArchivoSoliciBeca.objects.get(id=request.GET['id'])
                    solicitudbeca = archivobeca.solicitudbeca
                    if archivobeca.archivo:
                        if (MEDIA_ROOT + '/' + str(archivobeca.archivo)):
                                os.remove(MEDIA_ROOT + '/' + str(archivobeca.archivo))
                    archivobeca.delete()

                    if not ArchivoSoliciBeca.objects.filter(solicitudbeca=solicitudbeca).exists():
                        return HttpResponseRedirect('/admin_ayudafinanciera?elim=1')
                    else:
                        idarch = ArchivoSoliciBeca.objects.filter(solicitudbeca=solicitudbeca)[:1].get().id
                        return HttpResponseRedirect('/admin_ayudafinanciera?edit='+str(idarch))











        else:
            data = {'title':'Solicitud de Ayuda Financiera'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']

                if action == 'fichasocioecono':

                    data['title'] = 'Ficha Socio-Economica de Beca'
                    inscripcion = Inscripcion.objects.get(id=request.GET['id'])
                    autorizacionbode= False
                    aprobacionayudadobe=False

                    if inscripcion.autorizacionbecadobe:
                        autorizacionbode=True

                    if inscripcion.aprobacionayudadobe:
                        aprobacionayudadobe=True

                    #OCastillo 19-05-2023 solo con la promocion todos los niveles no puede acceder a beca
                    if inscripcion.promocion!=None:
                        if inscripcion.promocion.todos_niveles:
                            return HttpResponseRedirect("/?info=No puede acceder a una ayuda economica porque tiene una promocion para todos los niveles " + elimina_tildes(inscripcion.promocion.descripcion))
                        # else:
                        #    if inscripcion.matricula().nivel.nivelmalla_id==NIVEL_MALLA_UNO:
                        #        return HttpResponseRedirect("/?info=No puede acceder a una ayuda economica porque tiene una promocion " + elimina_tildes(inscripcion.promocion.descripcion))

                    try:
                        if (inscripcion.persona.usuario == request.user) or (inscripcion.persona.usuario != request.user and InscripcionFichaSocioEconomicaBeca.objects.filter(inscripcion=inscripcion,completo=True).exists()):
                            if inscripcion.persona.usuario == request.user:
                                if not Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=False).exists():
                                   return HttpResponseRedirect("/?info=No puede acceder a una ayuda economica porque no se encuentra matriculado")

                                if SolicitudBeca.objects.filter(inscripcion=inscripcion,renovarbeca=True,aprobado=False).exists():
                                       return HttpResponseRedirect("/?info=Ya existe una renovacion de solicitud en el nivel en proceso")

                                # esta matriculo
                                if Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=False).exists():
                                    matriculaactual = Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=False).order_by('-fecha')[:1].get()
                                data['matriculaactual'] = matriculaactual


                                if  SolicitudBeca.objects.filter(inscripcion = inscripcion,nivel=inscripcion.matricula().nivel,tiposolicitud=2,eliminado=False).exists():
                                    return HttpResponseRedirect("/?info=No puede acceder a una ayuda economica porque ya se encuentra registra una en el nivel actual")

                                if SolicitudBeca.objects.filter(nivel=inscripcion.matricula().nivel,inscripcion=inscripcion,tiposolicitud=1).exists():
                                   if not SolicitudBeca.objects.filter(nivel=inscripcion.matricula().nivel,inscripcion=inscripcion,tiposolicitud=1,estadosolicitud__id=3,aprobado=False).exists():
                                    return HttpResponseRedirect("/?info=No puede acceder a una ayuda economica porque tiene una solicitud de beca ingresada en el nivel matriculado")


                                #  si tiene discapacidad
                                if not inscripcion.tienediscapacidad or not autorizacionbode:

                                    if Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=False).exists():
                                        matriculaactual = Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=False).order_by('-fecha')[:1].get()
                                        if Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=True).order_by('-fecha').exists():
                                            matriculaant = Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=True).order_by('-fecha')[:1].get()
                                        else:
                                            matriculaant=''

                                    if inscripcion.matricula().nivel.nivelmalla_id > 1:
                                        if autorizacionbode== False:
                                            if not matriculaant:
                                                return HttpResponseRedirect("/?info=No tiene un nivel anterior para calcular promedio")

                                            puntajevar =calculopromedio(matriculaant,matriculaant.nivel.malla, matriculaant.nivel.nivelmalla)

                                            if puntajevar>= PUNTAJE_BECA_NORMAL:
                                                return HttpResponseRedirect("/?info=Estimado estudiante, por su promedio de calificaciones, usted esta apto para solicitar una beca. Por favor dirijase al modulo de solicitud de Beca " + " SU PUNTAJE ES: "+ str(decimal.Decimal(puntajevar)))


                                            if Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=True).exists():
                                              if aprobacionayudadobe==False:
                                                  if RecordAcademico.objects.filter(inscripcion__id=matriculaactual.inscripcion_id,asignatura__promedia=True,aprobada=False,fecha__lte=matriculaactual.fecha).exists():
                                                       return HttpResponseRedirect("/?info=No puede acceder a una ayuda economica porque tiene materia reprobada")

                                            # OCU validacion 3 matriculado en Seminario no aplica beca ok
                                            if Nivel.objects.filter(pk=matriculaactual.nivel.id,nivelmalla__id=10).exists() and not inscripcion.existe_solicitud_beca():
                                                return HttpResponseRedirect("/?info=Las becas son solamente para los niveles de la carrera. No se aplica en Seminario de Graduacion")
                                else:

                                    if Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=False).exists():
                                        matriculaactual = Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=False).order_by('-fecha')[:1].get()
                                        if Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=True).order_by('-fecha').exists():
                                            matriculaant = Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=True).order_by('-fecha')[:1].get()



                                    # si tiene matriculdo en el segundo nivel
                                    if inscripcion.matricula().nivel.nivelmalla_id > 1:

                                        if autorizacionbode== False:

                                            if not matriculaant:
                                                return HttpResponseRedirect("/?info=No tiene un nivel anterior para calcular promedio")

                                            puntajevar =calculopromedio(matriculaant,matriculaant.nivel.malla, matriculaant.nivel.nivelmalla)

                                            if puntajevar>= PUNTAJE_BECA_DISCAPA:
                                                return HttpResponseRedirect("/?info=Estimado estudiante, por su promedio de calificaciones, usted esta acto para solicitar una beca. Por favor diriaje al modulo de solicitud de Beca " + " SU PUNTAJE ES: "+ str(decimal.Decimal(puntajevar)))



                                            if Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=True).exists():
                                              if aprobacionayudadobe==False:
                                                  if RecordAcademico.objects.filter(inscripcion__id=matriculaactual.inscripcion_id,asignatura__promedia=True,aprobada=False,fecha__lte=matriculaactual.fecha).exists():
                                                       return HttpResponseRedirect("/?info=No puede acceder a una ayuda economica porque tiene materia reprobada")

                                            if Nivel.objects.filter(pk=matriculaactual.nivel.id,nivelmalla__id=10).exists() and not inscripcion.existe_solicitud_beca():
                                                return HttpResponseRedirect("/?info=Las becas son solamente para los niveles de la carrera. No se aplica en Seminario de Graduacion")


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
                                data['inscripcionficha'] = InscripcionFichaSocioEconomicaBeca.objects.filter(inscripcion=inscripcion)[:1].get()
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

                                if DatosAcademicos.objects.filter(fichabeca=data['inscripcionficha']).exists():
                                    data['datosacademicos'] = DatosAcademicos.objects.filter(fichabeca=data['inscripcionficha'])[:1].get()
                                if DatoTrabajo.objects.filter(fichabeca=data['inscripcionficha'],actual=False).exists():
                                    data['datotrabajoant'] = DatoTrabajo.objects.filter(fichabeca=data['inscripcionficha'],actual=False)[:1].get()
                                data['frmcro'] =CroquisForm()

                             # permiso de registrar una nueva solicitud
                            if not SolicitudBeca.objects.filter(nivel=inscripcion.matricula().nivel,inscripcion=inscripcion,tiposolicitud=2,eliminado=False).exists():
                               data['puedesoliayuda'] = 'ok'


                            data['user'] = request.user
                            return render(request ,"ayudafinanciera/fichasocio_economicabeca.html" ,  data)
                        else:

                            # evaluar que no tenga solicitud ayuda en el nivel actual que se encuentra

                            if SolicitudBeca.objects.filter(inscripcion = inscripcion,nivel=inscripcion.matricula().nivel,tiposolicitud=2,estadosolicitud__id=3,aprobado=False).exists():
                                if not SolicitudBeca.objects.filter(inscripcion = inscripcion,nivel=inscripcion.matricula().nivel,tiposolicitud=2,estadosolicitud__id=3,aprobado=False).exists():
                                    return HttpResponseRedirect("/?info=No puede acceder a una ayuda economica porque ya se encuentra registra una en el nivel actual")


                            data['inscripcion'] = inscripcion
                            data['form'] = SolicitudAyudaFinancieraForm()
                            return render(request ,"ayudafinanciera/addsolibeca.html" ,  data)

                    except Exception as e:
                        return HttpResponseRedirect("/?info= error contacte con el administrador " + str(e))


                if action == 'verfichasocioecono':

                    data['title'] = 'Ficha Socio-Economica de Beca'
                    inscripcion = Inscripcion.objects.get(id=request.GET['id'])
                    try:

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
                                data['inscripcionficha'] = InscripcionFichaSocioEconomicaBeca.objects.filter(inscripcion=inscripcion)[:1].get()
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

                                if DatosAcademicos.objects.filter(fichabeca=data['inscripcionficha']).exists():
                                    data['datosacademicos'] = DatosAcademicos.objects.filter(fichabeca=data['inscripcionficha'])[:1].get()
                                if DatoTrabajo.objects.filter(fichabeca=data['inscripcionficha'],actual=False).exists():
                                    data['datotrabajoant'] = DatoTrabajo.objects.filter(fichabeca=data['inscripcionficha'],actual=False)[:1].get()
                                data['frmcro'] =CroquisForm()


                            data['user'] = request.user

                            # permiso de registrar una nueva solicitud
                            if not SolicitudBeca.objects.filter(nivel=inscripcion.matricula().nivel,inscripcion=inscripcion,tiposolicitud=2,eliminado=False).exists():
                               data['puedesoliayuda'] = 'ok'

                            return render(request ,"ayudafinanciera/fichasocio_economicabecaeditar.html" ,  data)


                    except Exception as e:
                        return HttpResponseRedirect("/?info= error contacte con el administrador " + str(e))



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
                                        # lista = str('floresvillamarin@gamil.edu.ec')
                                        # lista = str('ocastillo@bolivariano.edu.ec')
                                        hoy = datetime.now().today()
                                        contenido = "FICHA SOCIO-ECONOMICA COMPLETADA - MODULO AYUDA FINANCIERA"
                                        send_html_mail(contenido,
                                            "emails/fichasocioeconomicacompleta.html", {'inscripcion': inscripcion, 'fecha': hoy,'contenido': contenido},lista.split(','))
                                data['form'] = SolicitudAyudaFinancieraForm()

                                return render(request ,"ayudafinanciera/addsolibeca.html" ,  data)
                    return HttpResponseRedirect('admin_ayudafinanciera')
                elif action=='editsolibeca':
                    data['title'] = 'Editar Datos'
                    solicitudbeca = SolicitudBeca.objects.get(id=request.GET['id'])
                    data['solicitudbeca'] = solicitudbeca
                    data['inscripcion'] = solicitudbeca.inscripcion
                    data['form'] = SolicitudAyudaFinancieraForm(initial={'motivo':solicitudbeca.motivo})
                    return render(request ,"ayudafinanciera/editsolibeca.html" ,  data)

                #INGRESAR GESTION
                elif action=='ingresar_gestionbeca':
                    solicitudbeca = SolicitudBeca.objects.get(pk=int(request.GET['idpreregistro']))
                    data['solicitudbeca']=solicitudbeca
                    data['tipogestionbeca'] = TipoGestionBeca.objects.filter(estado=True)
                    return render(request ,"ayudafinanciera/ingresargestionayuda.html" ,  data)

                elif action=='ver_gestionayuda':
                    historial = HistorialGestionAyudaEconomica.objects.filter(solicitudbeca__id=int(request.GET['idpreregistro'])).order_by('-fecha')
                    data['historial']=historial
                    data['tipogestionbeca'] = TipoGestionBeca.objects.filter()
                    data['infosolicitud']=SolicitudBeca.objects.get(id=request.GET['idpreregistro'])
                    return render(request ,"ayudafinanciera/vergestionayuda.html" ,  data)

                elif action=='verresolucionbeca':

                     solicitudbeca = SolicitudBeca.objects.get(id=int(request.GET['idpreregistro']),tiposolicitud=2)
                     data['inscripcion']=solicitudbeca.inscripcion
                     data['solicitud']=solicitudbeca
                     data['historialanalisis']= HistorialGestionAyudaEconomica.objects.filter(solicitudbeca=solicitudbeca,estado__id=3).order_by('-fecha')[:1].get()
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
                     data['perfilinscripcion']= PerfilInscripcion.objects.filter(inscripcion = solicitudbeca.inscripcion)
                     data['fichasocio']=InscripcionFichaSocioeconomica.objects.filter(inscripcion = solicitudbeca.inscripcion)
                     resolucionbeca = Resolucionbeca.objects.get(solicitudbeca=solicitudbeca)
                     data['resolucionbeca']=resolucionbeca

                     return render(request ,"ayudafinanciera/resolucionbeca.html" ,  data)


                elif action=='ver_verificacionarchivo':

                    solicitudbeca = SolicitudBeca.objects.get(id=int(request.GET['idpreregistro']),tiposolicitud=2)
                    data['tipoarchivosolicitud'] = ArchivoSolicitudBeca.objects.filter()
                    listaarchivo= ArchivoSoliciBeca.objects.filter(solicitudbeca=solicitudbeca)
                    data['becaverificacion']=solicitudbeca
                    data['listaarchivo']=listaarchivo

                    return render(request ,"ayudafinanciera/verificacionarchivo.html" ,  data)

                elif action=='validararchivo':

                    solicitudbeca = SolicitudBeca.objects.get(id=int(request.GET['idpreregistro']),tiposolicitud=2)
                    tipoarchivosol=ArchivoSolicitudBeca.objects.get(pk=int(request.GET['idtipoarchivo']))
                    if not ArchivoVerificadoBecaAyuda.objects.filter(solicitudbeca=solicitudbeca,tipoarchivosolicitudbeca=tipoarchivosol).exists():
                            verifico=  ArchivoVerificadoBecaAyuda (solicitudbeca=solicitudbeca,tipoarchivosolicitudbeca=tipoarchivosol, estado=True,
                                                                  usuario=request.user )
                            verifico.save()
                    else:
                        verifico=  ArchivoVerificadoBecaAyuda.objects.filter(solicitudbeca=solicitudbeca,tipoarchivosolicitudbeca=tipoarchivosol)[:1].get()
                        verifico.estado=True
                        verifico.save()
                        # llenar el log de historial de la solicitud ayuda economica
                    loshistorial= HistorialGestionAyudaEconomica(solicitudbeca=solicitudbeca,inscripcion=solicitudbeca.inscripcion,
                                                                fecha=datetime.now(),estado_id=23, usuario=request.user,comentariocorreo=str('APROBACION')+str(tipoarchivosol.nombre))
                    loshistorial.save()
                    solicitudbeca.idgestion=loshistorial.id
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



                    email_estudiante=solicitudbeca.inscripcion.persona.emailinst
                    nivel_est=solicitudbeca

                    mail_correosolicitudayuda('DOCUMENTO ACEPTADO', 'AYUDA FINANCIERA DOCUMENTO ACEPTADO'+' '+str(tipoarchivosol.nombre), str(lista[0][0]),request.user, elimina_tildes(solicitudbeca.inscripcion.persona.nombre_completo()),elimina_tildes(solicitudbeca.inscripcion.carrera.nombre),email_estudiante,nivel_est)
                    # mail_correosolicitudayuda('DOCUMENTO ACEPTADO', 'AYUDA FINANCIERA DOCUMENTO ACEPTADO'+' '+str(tipoarchivosol.nombre), str(lista[0][0]),request.user, elimina_tildes(solicitudbeca.inscripcion.persona.nombre_completo()),elimina_tildes(solicitudbeca.inscripcion.carrera.nombre),email_estudiante,nivel_est)


                    return render(request ,"ayudafinanciera/verificacionarchivo.html" ,  data)

                elif action=='rechazararchivo':

                    solicitudbeca = SolicitudBeca.objects.get(id=int(request.GET['idpreregistro']),tiposolicitud=2)
                    tipoarchivosol=ArchivoSolicitudBeca.objects.get(pk=int(request.GET['idtipoarchivo']))
                    if not ArchivoVerificadoBecaAyuda.objects.filter(solicitudbeca=solicitudbeca,tipoarchivosolicitudbeca=tipoarchivosol).exists():
                            verifico=  ArchivoVerificadoBecaAyuda (solicitudbeca=solicitudbeca,tipoarchivosolicitudbeca=tipoarchivosol, estado=False,
                                                                  usuario=request.user )
                            verifico.save()
                    else:
                        verifico=  ArchivoVerificadoBecaAyuda.objects.filter(solicitudbeca=solicitudbeca,tipoarchivosolicitudbeca=tipoarchivosol)[:1].get()
                        verifico.estado=False
                        verifico.save()
                    loshistorial= HistorialGestionAyudaEconomica(solicitudbeca=solicitudbeca,inscripcion=solicitudbeca.inscripcion,
                                                                fecha=datetime.now(),estado_id=23, usuario=request.user,comentariocorreo=str('RECHAZO')+str(tipoarchivosol.nombre))
                    loshistorial.save()
                    data['etinia'] = solicitudbeca.aprobadoetnia
                    solicitudbeca.idgestion=loshistorial.id
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



                    email_estudiante=solicitudbeca.inscripcion.persona.emailinst
                    nivel_est=solicitudbeca

                    mail_correosolicitudayuda(request.GET['comentario'], ' AYUDA FINANCIERA RECHAZO DE DOCUMENTO'+' '+str(tipoarchivosol.nombre), str(lista[0][0]),request.user, elimina_tildes(solicitudbeca.inscripcion.persona.nombre_completo()),elimina_tildes(solicitudbeca.inscripcion.carrera.nombre),email_estudiante,nivel_est)

                    return render(request ,"ayudafinanciera/verificacionarchivo.html" ,  data)

                elif action=='detallearch':
                        data = {}
                        data['archarchivbec'] = ArchivoSoliciBeca.objects.filter(solicitudbeca__id=request.GET['id']).order_by('fecha')
                        data['solicitudbeca'] = SolicitudBeca.objects.get(id=request.GET['id'])
                        data['opc'] = request.GET['opc']
                        data['TIPO_ESPECIE_BECA'] = TIPO_ESPECIE_BECA
                        return render(request ,"ayudafinanciera/detallearchivbec.html" ,  data)

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

                    lista[0][0]=str(lista[0][0])+','+str('dobe@bolivariano.edu.ec')+','+str('floresvilamarinm@gmail.com')

                    # llenar el log de historial de la solicitud ayuda economica
                    loshistorial= HistorialGestionAyudaEconomica(solicitudbeca=solicitudbeca,inscripcion=solicitudbeca.inscripcion,
                                                        fecha=datetime.now(),estado_id=12, usuario=request.user,comentariocorreo='APROBACION FINAL DE LOS DOCUMENTOS DE LA SOLICITUD')
                    loshistorial.save()
                    solicitudbeca.idgestion=loshistorial.id
                    solicitudbeca.save()
                    email_estudiante=solicitudbeca.inscripcion.persona.emailinst
                    nivel_est=solicitudbeca

                    mail_correosolicitudayuda('SE REALIZO LA VERIFICACION Y APROBACION DE TODO LOS DOCUMENTOS ADJUNTO A LA AYUDA FINANCIERA.EN EL TRANSCRUSO DE 7 DIAS TENDRA LA RESOLUCION A SU SOLICITUD. ES NECESARIO QUE ESTE PENDIENTE DE LOS MENSAJES EN SU CORREO ELECTRONICO', 'APROBACION FINAL DE TODO LOS DOCUMENTO ADJUNTO', str(lista[0][0]),request.user, elimina_tildes(solicitudbeca.inscripcion.persona.nombre_completo()),elimina_tildes(solicitudbeca.inscripcion.carrera.nombre),email_estudiante,nivel_est)

                    return HttpResponseRedirect('/admin_ayudafinanciera?opcion=adm&id='+str(solicitudbeca.inscripcion.id)+'&pag=4')


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

                    rubros = Rubro.objects.filter(inscripcion=inscripcion,cancelado=False).values('id').exclude(id__in=rubrootro).exclude(id__in=rubroinscripcion).exclude(id__in=rubroespecie)

                    pagosrubro=Pago.objects.filter(rubro__id__in=rubroaux).values_list('rubro_id')

                    rubros=rubros.filter().exclude(id__in=pagosrubro)

                    form = DetalleDescuentoBecaForm()
                    form.rubros_list(rubros)

                    if PerfilInscripcion.objects.filter(inscripcion = solicitudbeca.inscripcion).exists():
                        data['perfilinscripcion']= PerfilInscripcion.objects.get(inscripcion = solicitudbeca.inscripcion)

                    else:

                       inscripciones = Inscripcion.objects.filter(id__in=SolicitudBeca.objects.filter(tiposolicitud=2,eliminado=False).distinct('puntaje').values('inscripcion__id')).order_by('solicitudbeca__puntaje','-solicitudbeca__fecha')
                       data['inscripciones'] = inscripciones
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
                       return render(request ,"ayudafinanciera/solicitud_ayudafinanciera.html" ,  data)


                    data['rubros']= Rubro.objects.filter(inscripcion=data['inscripcion'],cancelado=False).exclude(id__in=rubrootro)
                    data['form']= form
                    return render(request ,"ayudafinanciera/descuentopagobeca.html" ,  data)

                elif action == 'editarvalordescuento':

                    data['inscripcion'] = Inscripcion.objects.get(pk=request.GET['id'])

                    inscripcion=Inscripcion.objects.get(pk=request.GET['id'])

                    solicitudbeca=SolicitudBeca.objects.get(id=request.GET['idsolictudbeca'])

                    data['solicitudbeca'] = solicitudbeca

                    data['descuentobeca']= TablaDescuentoBeca.objects.filter(solicitudbeca=solicitudbeca)

                    data['historialanalisis']= HistorialGestionAyudaEconomica.objects.filter(solicitudbeca=solicitudbeca,estado__id=3).order_by('-fecha')[:1].get()

                    data['form1'] = BecaParcialForm()


                    # buscar rubro de otro tipo que no sean cuotas para que no se presente como rubro para la beca
                    rubroaux = Rubro.objects.filter(inscripcion=inscripcion, cancelado=False).values_list('id')
                    rubrootro = RubroOtro.objects.filter(rubro__id__in=rubroaux).values_list('rubro_id')
                    rubroespecie=RubroEspecieValorada.objects.filter(rubro__id__in=rubroaux).values_list('rubro_id')
                    rubroinscripcion=RubroInscripcion.objects.filter(rubro__id__in=rubroaux).values_list('rubro_id')

                    rubros = Rubro.objects.filter(inscripcion=inscripcion,cancelado=False).values('id').exclude(id__in=rubrootro).exclude(id__in=rubroinscripcion).exclude(id__in=rubroespecie)

                    pagosrubro=Pago.objects.filter(rubro__id__in=rubroaux).values_list('rubro_id')

                    rubros=rubros.filter().exclude(id__in=pagosrubro)

                    form = DetalleDescuentoBecaForm()
                    form.rubros_list(rubros)
                    personaautoriza= Persona.objects.get(usuario=request.user)
                    if PersonAutorizaBecaAyuda.objects.filter(persona=personaautoriza,personadiscapacidad=True).exists():
                        data['enviosecr'] = True
                    if PersonAutorizaBecaAyuda.objects.filter(persona=personaautoriza,personadiscapacidad=False).exists():
                        data['enviosecr'] = True


                    data['rubros']= Rubro.objects.filter(inscripcion=data['inscripcion'],cancelado=False)
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

                    data['perfilinscripcion']= PerfilInscripcion.objects.filter(inscripcion = solicitudbeca.inscripcion)
                    data['fichasocio']=InscripcionFichaSocioeconomica.objects.filter(inscripcion = solicitudbeca.inscripcion)

                    formarchivoanilisis = SolicitudArchivoAyudaForm()

                    data['formanalisisarchivo'] = formarchivoanilisis


                    return render(request ,"ayudafinanciera/editardescuentopagobeca.html" ,  data)


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

                    rubros = Rubro.objects.filter(inscripcion=inscripcion,cancelado=False).values('id').exclude(id__in=rubrootro).exclude(id__in=rubroinscripcion).exclude(id__in=rubroespecie)

                    pagosrubro=Pago.objects.filter(rubro__id__in=rubroaux).values_list('rubro_id')
                    rubros=rubros.filter().exclude(id__in=pagosrubro)
                    form = DetalleDescuentoBecaForm()
                    form.rubros_list(rubros)
                    personaautoriza= Persona.objects.get(usuario=request.user)
                    if PersonAutorizaBecaAyuda.objects.filter(persona=personaautoriza,personadiscapacidad=True).exists():
                        data['enviosecr'] = True
                    if PersonAutorizaBecaAyuda.objects.filter(persona=personaautoriza,personadiscapacidad=False).exists():
                        data['enviosecr'] = True


                    data['rubros']= Rubro.objects.filter(inscripcion=data['inscripcion'],cancelado=False)
                    data['form']= form
                    return render(request ,"ayudafinanciera/reenviaranalisis.html" ,  data)


                elif action == 'ingresarrevision':
                    solicitudbeca=SolicitudBeca.objects.get(id=request.GET['idsolictudbeca'])
                    data['solicitudbeca']=solicitudbeca
                    formrevision=SolicitudRevisionAplicada()
                    data['form']= formrevision

                    return render(request ,"ayudafinanciera/agregarrevision.html" ,  data)


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
                            inscripciones = SolicitudBeca.objects.filter(Q(Q(inscripcion__persona__nombres__icontains=search) | Q(inscripcion__persona__apellido1__icontains=search) | Q(inscripcion__persona__apellido2__icontains=search) | Q(inscripcion__persona__cedula__icontains=search) | Q(inscripcion__persona__pasaporte__icontains=search)),tiposolicitud=2, eliminado=False).order_by('-fecha')
                        else:
                            inscripciones = SolicitudBeca.objects.filter(Q(Q(inscripcion__persona__nombres__icontains=search) | Q(inscripcion__persona__apellido1__icontains=search) | Q(inscripcion__persona__apellido2__icontains=search) | Q(inscripcion__persona__cedula__icontains=search) | Q(inscripcion__persona__pasaporte__icontains=search)),tiposolicitud=2, eliminado=False, estadosolicitud__id=idestado).order_by('-fecha')

                    else:
                        if idestado==0:
                            inscripciones = SolicitudBeca.objects.filter(Q(Q(inscripcion__persona__nombres__icontains=search) | Q(inscripcion__persona__apellido1__icontains=search) | Q(inscripcion__persona__apellido2__icontains=search) | Q(inscripcion__persona__cedula__icontains=search) | Q(inscripcion__persona__pasaporte__icontains=search)),tiposolicitud=2,eliminado=False).order_by('-fecha')
                        else:
                            inscripciones = SolicitudBeca.objects.filter(Q(Q(inscripcion__persona__nombres__icontains=search) | Q(inscripcion__persona__apellido1__icontains=search) | Q(inscripcion__persona__apellido2__icontains=search) | Q(inscripcion__persona__cedula__icontains=search) | Q(inscripcion__persona__pasaporte__icontains=search)),tiposolicitud=2,eliminado=False, estadosolicitud__id=idestado).order_by('-fecha')
                else:
                   if idestado==0:
                        inscripciones = SolicitudBeca.objects.filter(tiposolicitud=2,eliminado=False).order_by('-fecha')
                   else:
                        inscripciones = SolicitudBeca.objects.filter(tiposolicitud=2,eliminado=False,estadosolicitud__id=idestado).order_by('-fecha')

                data['idestado']=idestado

                if Inscripcion.objects.filter(persona__usuario=request.user).exists():
                    inscripcion = Inscripcion.objects.get(persona__usuario=request.user)
                    solicitudbeca = SolicitudBeca.objects.filter(inscripcion = inscripcion,tiposolicitud=2,eliminado=False).order_by('-fecha')
                    aprobacionayudadobe=False
                    if inscripcion.aprobacionayudadobe:
                        aprobacionayudadobe=True


                    if not inscripcion.tienediscapacidad:

                        if Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=False,liberada=False).exists():
                            matriculaactual = Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=False,liberada=False).order_by('-fecha')[:1].get()
                        else:
                            matriculaactual = ''

                        if not matriculaactual:
                            return HttpResponseRedirect("/?info=No esta matriculado actualmente")
                        data['matriculaactual'] = matriculaactual

                        # if not solicitudbeca:
                        if Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=True).exists():
                          if aprobacionayudadobe==False:
                            if RecordAcademico.objects.filter(inscripcion__id=matriculaactual.inscripcion_id,asignatura__promedia=True,aprobada=False,fecha__lt=matriculaactual.fecha).exists():
                               return HttpResponseRedirect("/?info=No puede acceder a una ayuda economica porque tiene materia reprobada")

                    else:
                        if Matricula.objects.filter(inscripcion = inscripcion).count()>1:
                            if Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=False).exists():
                                matriculaactual = Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=False).order_by('-fecha')[:1].get()
                            else:
                                matriculaactual = ''

                            if not matriculaactual:
                                return HttpResponseRedirect("/?info=No esta matriculado actualmente")
                            data['matriculaactual'] = matriculaactual

                            # if not solicitudbeca:

                            if Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=False).exists():
                              if aprobacionayudadobe==False:
                                if RecordAcademico.objects.filter(inscripcion__id=matriculaactual.inscripcion_id,asignatura__promedia=True,aprobada=False,fecha__lt=matriculaactual.fecha).exists():
                                   return HttpResponseRedirect("/?info=No puede acceder a una ayuda economica porque tiene materia reprobada")

                    if inscripcion.empresaconvenio!=None:
                        if inscripcion.empresaconvenio.id!=4:
                            return HttpResponseRedirect("/?info=No puede acceder a una ayuda economica porque tiene convenio" + str(inscripcion.empresaconvenio.nombre))


                    if inscripcion.promocion!=None:
                        if inscripcion.promocion.todos_niveles:
                            return HttpResponseRedirect("/?info=No puede acceder a una ayuda economica porque tiene una promocion para todo los nivel " + elimina_tildes(inscripcion.promocion.descripcion))
                        # else:
                        #    if matriculaactual.nivel.nivelmalla_id==NIVEL_MALLA_UNO:
                        #        return HttpResponseRedirect("/?info=No puede acceder a una ayuda economica porque tiene una promocion " + elimina_tildes(inscripcion.promocion.descripcion))

                    # permiso de registrar una nueva solicitud
                    if not SolicitudBeca.objects.filter(nivel=inscripcion.matricula().nivel,inscripcion=inscripcion,tiposolicitud=2,eliminado=False).exists():
                                data['puedesoliayuda'] = 'ok'


                    form = SolicitudBecaForm()

                    data['form3'] =form

                    data['inscripcion'] = inscripcion

                    if 'elim' in request.GET:
                        data['error'] = 'El registro fue eliminado'
                    if 'edit' in request.GET:
                        archivo = ArchivoSoliciBeca.objects.get(id=request.GET['edit'])
                        data['edit'] = archivo
                    data['opcion'] = 'inscrip'

                elif not 'opcion' in request.GET:

                    paging = MiPaginador(inscripciones, 30)
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
                    data['form1'] = ResponSolicAyudaEconomicaForm()
                    formarchivoayuda=SolicitudArchivoAyudaForm()
                    data['formayudaarchivo'] =formarchivoayuda

                    data['aux'] = True

                    personaautoriza= Persona.objects.get(usuario=request.user)
                    if PersonAutorizaBecaAyuda.objects.filter(persona=personaautoriza,personadiscapacidad=True).exists():
                        data['autorizaapurebadis'] = True
                        data['autorizaapurebanodis'] = True
                        data['aux'] = False
                        data['enviosecr'] = True

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
                        data['noveringresotabla'] = True
                        data['aux'] = False

                    if usuario.groups.filter(id__in=[DOBE_GROUP_ID ]).exists():
                        data['aux'] = False
                        data['noveringresotabla'] = True


                    data['usuario'] = usuario
                    data['tipogestion'] = TipoEstadoSolicitudBeca.objects.filter()

                    return render(request ,"ayudafinanciera/solicitud_ayudafinanciera.html" ,  data)
                else:
                    solicitudbeca = SolicitudBeca.objects.filter(inscripcion=request.GET['id'],tiposolicitud=2,eliminado=False).order_by('-fecha')
                    data['inscrificha'] = Inscripcion.objects.get(id=request.GET['id'])

                paging = MiPaginador(solicitudbeca, 30)

                data['solicitudbecas'] = solicitudbeca
                form31=SolicitudBecaNuevaForm()
                data['form31'] =form31
                data['hoy'] = datetime.now()
                if 'error' in request.GET:
                    data['error'] = request.GET['error']

                return render(request ,"ayudafinanciera/ayuda_financiera.html" ,  data)




    except Exception as e:
        return HttpResponseRedirect("/?info= error contacte con el administrador " + str(e))

def mail_correosolicitudayuda(contenido,asunto,email,user,estudiante,carrera,email_estudiante,nivel_est):
        hoy = datetime.now().today()
        persona = Persona.objects.get(usuario=user)
        send_html_mail(str(asunto),"emails/correoalumnoayuda.html", {'fecha': hoy,"user":user,'contenido': contenido, 'asunto': asunto,'persona':persona,'estudiante':estudiante,'carrera':carrera,'email_estudiante':email_estudiante,'nivel_est':nivel_est},email.split(","))

def mail_correosolicitudsecretaria(contenido,email,user,estudiante,carrera,email_estudiante,nivel_est,tabladescuento,historialultima):
        hoy = datetime.now().today()
        persona = Persona.objects.get(usuario=user)
        send_html_mail(str('ENVIO DE LA INFORMACION DE BECA AYUDA FINANCIERA PARA SU REVISION'),"emails/correosecretaria.html", {'fecha': hoy,"user":user,'contenido': contenido,'persona':persona,'estudiante':estudiante,'carrera':carrera,'email_estudiante':email_estudiante,'nivel_est':nivel_est,'descuentobeca':tabladescuento,'ultimoanalisis':historialultima},email.split(","))




def mail_correosolicitudsecretariaaplica(contenido,email,user,estudiante,carrera,email_estudiante,nivel_est):
        hoy = datetime.now().today()
        persona = Persona.objects.get(usuario=user)
        send_html_mail(str('ENVIO INFORMACION DE LA AYUDA FINANCIERA QUE SE APLICO'),"emails/correosecretaria.html", {'fecha': hoy,"user":user,'contenido': contenido,'persona':persona,'estudiante':estudiante,'carrera':carrera,'email_estudiante':email_estudiante,'nivel_est':nivel_est},email.split(","))


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
