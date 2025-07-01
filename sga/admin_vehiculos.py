from datetime import datetime, timedelta
from decimal import Decimal
import json
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Avg
from django.db.models.aggregates import Sum
from django.db import transaction
from django.db.models.query_utils import Q
from django.forms.models import model_to_dict
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.utils.encoding import force_str
from django.template import RequestContext
from decorators import secure_module
from settings import CENTRO_EXTERNO, RUBRO_TIPO_OTRO_MODULO_INTERNO, RUBRO_TIPO_OTRO_INSCRIPCION, DEFAULT_PASSWORD, PROFESORES_GROUP_ID, ALUMNOS_GROUP_ID, UTILIZA_GRUPOS_ALUMNOS, REPORTE_CERTIFICADO_INSCRIPCION, EMAIL_ACTIVE, EVALUACION_ITB, REGISTRO_HISTORIA_NOTAS, NOTA_ESTADO_EN_CURSO, GENERAR_RUBROS_PAGO, GENERAR_RUBRO_INSCRIPCION, GENERAR_RUBRO_INSCRIPCION_MARGEN_DIAS, MODELO_EVALUACION, EVALUACION_IAVQ, EVALUACION_ITS, UTILIZA_NIVEL0_PROPEDEUTICO, TIPO_PERIODO_PROPEDEUTICO, NOTA_ESTADO_APROBADO, UTILIZA_FICHA_MEDICA, EVALUACION_TES, CORREO_INSTITUCIONAL, USA_CORREO_INSTITUCIONAL, INSCRIPCION_CONDUCCION, PROFE_PRACT_CONDUCCION
from sga.alu_malla import aprobadaAsignatura
from sga.commonviews import addUserData, ip_client_address
from sga.docentes import calculate_username

from sga.forms import PersonaForm, InscripcionForm, RecordAcademicoForm, HistoricoRecordAcademicoForm, HistoriaNivelesDeInscripcionForm, \
                      CargarFotoForm, EmpresaInscripcionForm, EstudioInscripcionForm, DocumentoInscripcionForm, ActividadesInscripcionForm, \
                      PadreClaveForm, ConvalidacionInscripcionForm, HistoricoNotasITBForm, GraduadoDatosForm, EgresadoForm, InscripcionSenescytForm,\
                      RetiradoMatriculaForm, InscripcionCextForm, BecarioForm, InscripcionPracticaForm, ObservacionInscripcionForm, ProcesoDobeForm,  \
                      VisitaBibliotecaForm, SesionPracticaForm, TurnoPracticaForm, VehiculoForm, RegistroVehiculoForm, PolizaForm, AdicionarVehiForm, PersonaConduccionForm
from sga.models import Profesor, ProcesoDobe, Persona, Inscripcion, RecordAcademico, DocumentosDeInscripcion, HistoricoRecordAcademico, HistoriaNivelesDeInscripcion, FotoPersona, EmpresaInscripcion, EstudioInscripcion, DocumentoInscripcion, Archivo, TipoArchivo, Grupo, InscripcionGrupo, PerfilInscripcion, HistoricoNotasITB, PadreClave, Malla, ConvalidacionInscripcion, TipoEstado, Rubro, RubroInscripcion, NivelMalla, EjeFormativo, AsignaturaMalla, Egresado, Asignatura, InscripcionSenescyt, RetiradoMatricula, Carrera, Modalidad, Sesion, Especialidad, Materia, Nivel, TipoOtroRubro, Matricula, MateriaAsignada, RubroOtro, Graduado, InscripcionBecario, InscripcionPracticas, ObservacionInscripcion, InscripcionConduccion, VisitaBiblioteca, TipoVisitasBiblioteca, DetalleVisitasBiblioteca, TipoPersona, SesionPractica, TurnoPractica, Vehiculo, GrupoPractica, Practica, RegistroVehiculo, Poliza, PolizaVehiculo, PersonaConduccion, CategoriaVehiculo
from sga.tasks import gen_passwd


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
# @secure_module
@transaction.atomic()
def view(request):
    if request.method=='POST':
        action = request.POST['action']
        if action=='vehiculoadd':
            f = VehiculoForm(request.POST,request.FILES)
            if f.is_valid():
                if int(request.POST['edit'])== 0:
                    vehiculo=Vehiculo(placa = f.cleaned_data['placa'],
                                      categoria = f.cleaned_data['categoria'],
                                      combustible = f.cleaned_data['combustible'],
                                      codigo = f.cleaned_data['codigo'],
                                      valor = f.cleaned_data['valor'],
                                      marca = f.cleaned_data['marca'],
                                      modelo = f.cleaned_data['modelo'],
                                      color = f.cleaned_data['color'],
                                      motor = f.cleaned_data['motor'],
                                      chasis = f.cleaned_data['chasis'],
                                      anio = f.cleaned_data['anio'])
                else:
                    vehiculo=Vehiculo.objects.get(pk=request.POST['edit'])
                    vehiculo.placa=f.cleaned_data['placa']
                    vehiculo.categoria = f.cleaned_data['categoria']
                    vehiculo.combustible = f.cleaned_data['combustible']
                    vehiculo.codigo=f.cleaned_data['codigo']
                    vehiculo.marca = f.cleaned_data['marca']
                    vehiculo.modelo = f.cleaned_data['modelo']
                    vehiculo. color = f.cleaned_data['color']
                    vehiculo.motor = f.cleaned_data['motor']
                    vehiculo.chasis = f.cleaned_data['chasis']
                    vehiculo.valor = f.cleaned_data['valor']
                    vehiculo.anio = f.cleaned_data['anio']
                vehiculo.save()
                if 'imagen' in request.FILES:
                     vehiculo.imagen=request.FILES['imagen']
                     vehiculo.save()
                client_address = ip_client_address(request)

                # Log de ADICIONAR Vehiculo
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(vehiculo).pk,
                    object_id       = vehiculo.id,
                    object_repr     = force_str(vehiculo),
                    action_flag     = ADDITION,
                    change_message  = 'Adicionar/Editar Vehiculo (' + client_address + ')' )
                return HttpResponseRedirect("/admin_vehiculos")
        elif action == 'addregistro':
            f = RegistroVehiculoForm(request.POST,request.FILES)
            if f.is_valid():
                if int(request.POST['edit'])== 0:
                    try:
                        rvehiculo = RegistroVehiculo(vehiculo=f.cleaned_data['vehiculo'],
                                                     chofervehiculo = f.cleaned_data['chofervehiculo'],
                                                     solicitante=f.cleaned_data['solicitante'],
                                                     beneficiario=f.cleaned_data['beneficiario'],
                                                     origen=f.cleaned_data['origen'],
                                                     destino=f.cleaned_data['destino'],
                                                     fsalida=f.cleaned_data['fsalida'],
                                                     hsalida=f.cleaned_data['hsalida'],
                                                     fllegada=f.cleaned_data['fllegada'],
                                                     hllegada=f.cleaned_data['hllegada'],
                                                     kmsalida=Decimal(f.cleaned_data['kmsalida']),
                                                     kmllegada=Decimal(f.cleaned_data['kmllegada']),
                                                     consumocomb=Decimal(f.cleaned_data['consumocomb']),
                                                     costocomb=Decimal(f.cleaned_data['costocomb']),
                                                     observacion=f.cleaned_data['observacion'])
                        mensaje = 'Adicionado'
                        if Decimal(f.cleaned_data['kmllegada']) < Decimal(f.cleaned_data['kmsalida']) and Decimal(f.cleaned_data['kmllegada']) != 0:
                            return HttpResponseRedirect("/admin_vehiculos?action=registro&addregistro&errorkm")
                        rvehiculo.save()
                    except Exception as e:
                       return HttpResponseRedirect("/admin_vehiculos?action=registro&addregistro&error")
                else:
                    try:
                        rvehiculo = RegistroVehiculo.objects.get(pk=request.POST['edit'])
                        rvehiculo.vehiculo=f.cleaned_data['vehiculo']
                        rvehiculo.chofervehiculo = f.cleaned_data['chofervehiculo']
                        rvehiculo.solicitante=f.cleaned_data['solicitante']
                        rvehiculo.beneficiario=f.cleaned_data['beneficiario']
                        rvehiculo.origen=f.cleaned_data['origen']
                        rvehiculo.destino=f.cleaned_data['destino']
                        rvehiculo.fsalida=f.cleaned_data['fsalida']
                        rvehiculo.hsalida=f.cleaned_data['hsalida']
                        rvehiculo.fllegada=f.cleaned_data['fllegada']
                        rvehiculo.hllegada=f.cleaned_data['hllegada']
                        rvehiculo.kmsalida=Decimal(f.cleaned_data['kmsalida'])
                        rvehiculo.kmllegada=Decimal(f.cleaned_data['kmllegada'])
                        rvehiculo.costocomb=Decimal(f.cleaned_data['costocomb'])
                        rvehiculo.observacion=f.cleaned_data['observacion']
                        mensaje = 'Editado'
                        if Decimal(f.cleaned_data['kmllegada']) < Decimal(f.cleaned_data['kmsalida'])  and Decimal(f.cleaned_data['kmllegada']) != 0:
                            return HttpResponseRedirect("/admin_vehiculos?action=registro&editregistro&errorkm&id="+str(rvehiculo.id))
                        rvehiculo.save()
                    except Exception as e:
                        return HttpResponseRedirect("/admin_vehiculos?action=registro&editregistro&error&id="+str(rvehiculo.id))
                if 'salida' in request.FILES:
                    rvehiculo.salida = request.FILES['salida']

                if 'llegada' in request.FILES:
                    rvehiculo.llegada = request.FILES['llegada']
                rvehiculo.save()
                client_address = ip_client_address(request)

                # Log de ADICIONAR Vehiculo
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(rvehiculo).pk,
                    object_id       = rvehiculo.id,
                    object_repr     = force_str(rvehiculo),
                    action_flag     = ADDITION,
                    change_message  = mensaje + ' Registro de vehiculo (' + client_address + ')' )
                return HttpResponseRedirect("/admin_vehiculos?action=registro")
            else:
                if int(request.POST['edit'])== 0:
                    return HttpResponseRedirect("/admin_vehiculos?action=registro&addregistro&errorform")
                else:
                    return HttpResponseRedirect("/admin_vehiculos?action=registro&editregistro&errorform&id="+(request.POST['edit']))
        elif action == 'addpolivehic':
                try:
                    p = Poliza.objects.get(pk=request.POST['id'])
                    v = Vehiculo.objects.get(pk=request.POST['vehic'])

                    pv = PolizaVehiculo(poliza=p,vehiculo=v)
                    pv.save()

                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de BORRAR HISTORICO
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(pv).pk,
                        object_id       = pv.id,
                        object_repr     = force_str(pv),
                        action_flag     = ADDITION,
                        change_message  = 'Agregado Poliza Vehiculo (' + client_address + ')')
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
        elif action == 'eliminarpolvehi':
            polizavehic = PolizaVehiculo.objects.get(pk=request.POST['id'])
            #Obtain client ip address
            client_address = ip_client_address(request)

            # Log de BORRAR HISTORICO
            LogEntry.objects.log_action(
                user_id         = request.user.pk,
                content_type_id = ContentType.objects.get_for_model(polizavehic).pk,
                object_id       = polizavehic.id,
                object_repr     = force_str(polizavehic),
                action_flag     = ADDITION,
                change_message  = 'Eliminado Poliza Vehiculo (' + client_address + ')')
            polizavehic.delete()
            return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
        elif action == 'eliminapoliza':
            poliza = Poliza.objects.get(pk=request.POST['id'])
            #Obtain client ip address
            client_address = ip_client_address(request)

            # Log de BORRAR HISTORICO
            LogEntry.objects.log_action(
                user_id         = request.user.pk,
                content_type_id = ContentType.objects.get_for_model(poliza).pk,
                object_id       = poliza.id,
                object_repr     = force_str(poliza),
                action_flag     = ADDITION,
                change_message  = 'Eliminada Poliza (' + client_address + ')')
            poliza.delete()
            return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")

        elif action == 'delpersona':
            persona = PersonaConduccion.objects.get(pk=request.POST['id'])
            #Obtain client ip address
            client_address = ip_client_address(request)

            # Log de BORRAR HISTORICO
            LogEntry.objects.log_action(
                user_id         = request.user.pk,
                content_type_id = ContentType.objects.get_for_model(persona).pk,
                object_id       = persona.id,
                object_repr     = force_str(persona),
                action_flag     = ADDITION,
                change_message  = 'Eliminada Persona (' + client_address + ')')
            persona.delete()
            return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
        elif action == 'addpoliza':
            f = PolizaForm(request.POST)
            if f.is_valid():
                if int(request.POST['edit'])== 0:
                    try:
                        poliza = Poliza(descripcion=f.cleaned_data['descripcion'],
                                 inicio = f.cleaned_data['inicio'],
                                 fin = f.cleaned_data['fin'],
                                 proveedor=f.cleaned_data['proveedor'],
                                 valor=f.cleaned_data['valor'])
                        mensaje = 'Adicionado'
                        poliza.save()
                    except Exception as e:
                       return HttpResponseRedirect("/admin_vehiculos?action=poliza&addpoliza&error")
                else:
                    try:
                        poliza = Poliza.objects.get(pk=request.POST['edit'])
                        poliza.descripcion=f.cleaned_data['descripcion']
                        poliza.inicio = f.cleaned_data['inicio']
                        poliza.fin = f.cleaned_data['fin']
                        poliza.proveedor =f.cleaned_data['proveedor']
                        poliza.valor =f.cleaned_data['valor']
                        mensaje = 'Editado'
                        poliza.save()
                    except Exception as e:
                        return HttpResponseRedirect("/admin_vehiculos?action=poliza&addpoliza&error")
                if 'vigente' in request.POST:
                    poliza.vigente = True
                else:
                    poliza.vigente = False
                poliza.save()
                client_address = ip_client_address(request)

                # Log de ADICIONAR Vehiculo
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(poliza).pk,
                    object_id       = poliza.id,
                    object_repr     = force_str(poliza),
                    action_flag     = ADDITION,
                    change_message  = mensaje + ' Poliza (' + client_address + ')' )
                return HttpResponseRedirect("/admin_vehiculos?action=poliza")
            else:
                if int(request.POST['edit'])== 0:
                    return HttpResponseRedirect("/admin_vehiculos?action=poliza&addpoliza&errorform")
                else:
                    return HttpResponseRedirect("/admin_vehiculos?action=poliza&editpoliza&errorform")
        elif action == 'addpersona':
            f = PersonaConduccionForm(request.POST,request.FILES)
            if f.is_valid():
                if int(request.POST['edit'])== 0:
                    try:
                        persona = PersonaConduccion(identificacion=f.cleaned_data['identificacion'],
                                 nombres = f.cleaned_data['nombres'],
                                 categorialicencia= f.cleaned_data['categorialicencia'],
                                 telefono = f.cleaned_data['telefono'],
                                 email=f.cleaned_data['email'])
                        mensaje = 'Adicionado'
                        persona.save()
                    except Exception as e:
                       return HttpResponseRedirect("/admin_vehiculos?action=personas&addpersona&error")
                else:
                    try:
                        persona = PersonaConduccion.objects.get(pk=request.POST['edit'])
                        persona.identificacion=f.cleaned_data['identificacion']
                        persona.nombres = f.cleaned_data['nombres']
                        persona.telefono = f.cleaned_data['telefono']
                        persona.email =f.cleaned_data['email']
                        persona.categorialicencia= f.cleaned_data['categorialicencia']
                        mensaje = 'Editado'
                        persona.save()
                    except Exception as e:
                        return HttpResponseRedirect("/admin_vehiculos?action=personas&addpersona&error")
                if 'chofer' in request.POST:
                    persona.chofer = True
                else:
                    persona.chofer = False
                if 'licencia' in request.FILES:
                    persona.licencia = request.FILES['licencia']
                persona.save()
                client_address = ip_client_address(request)

                # Log de ADICIONAR Vehiculo
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(persona).pk,
                    object_id       = persona.id,
                    object_repr     = force_str(persona),
                    action_flag     = ADDITION,
                    change_message  = mensaje + ' Persona (' + client_address + ')' )
                return HttpResponseRedirect("/admin_vehiculos?action=personas")
            else:
                if int(request.POST['edit'])== 0:
                    return HttpResponseRedirect("/admin_vehiculos?action=personas&addpersona&errorform")
                else:
                    return HttpResponseRedirect("/admin_vehiculos?action=personas&editpersona&errorform")



    else:
        data = {'title': 'Mantenimiento de Vehiculo'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='vehiculoadd':
                data['title'] = 'Nuevo Vehiculo'
                vehiculo = VehiculoForm(initial={'valor':'0.00'})
                data['form'] = vehiculo
                data['titulo'] = 'Adicionar Nuevo Vehiculo'
                data['editar']  = 0

                return render(request ,"admin_vehiculos/addvehiculo.html" ,  data)

            elif action=='editvehiculo':
                data['title'] = 'Editar Vehiculo'
                vehiculo = Vehiculo.objects.get(pk=request.GET['id'])
                initial = model_to_dict(vehiculo)
                vehiculof = VehiculoForm(initial=initial)
                data['form'] = vehiculof
                data['titulo'] = 'Editar Vehiculo'
                data['editar']  = vehiculo.id
                return render(request ,"admin_vehiculos/addvehiculo.html" ,  data)

            elif action =='poliza':
                if 'addpoliza' in request.GET:
                    data['title'] = 'Nueva Poliza'
                    poliza = PolizaForm(initial={'inicio':datetime.now().strftime('%d-%m-%Y'),'fin':datetime.now().strftime('%d-%m-%Y')})
                    data['form'] = poliza
                    data['titulo'] = 'Adicionar Nueva Poliza'
                    data['editar']  = 0
                    return render(request ,"admin_vehiculos/addpoliza.html" ,  data)

                if 'editpoliza' in request.GET:
                    data['title'] = 'Editar Poliza'
                    poliza = Poliza.objects.get(pk=request.GET['id'])
                    initial = model_to_dict(poliza)
                    data['form'] = PolizaForm(initial=initial)
                    data['editar']  = poliza.id
                    data['poliza']=poliza
                    if 'error' in request.GET:
                        data['error']=1
                    if 'errorform' in request.GET:
                        data['errorform']=1
                    return render(request ,"admin_vehiculos/addpoliza.html" ,  data)
                else:
                    search = None
                    if 's' in request.GET:
                        search = request.GET['s']
                    if search:

                        poliza = Poliza.objects.filter(Q(proveedor__icontains=search)|Q(descripcion__icontains=search)).order_by('descripcion')
                    else:
                        poliza = Poliza.objects.all().order_by('descripcion')

                    paging = MiPaginador(poliza, 30)
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
                    data['title'] = 'Registro de Poliza'
                    data['poliza'] = page.object_list
                    data['search'] = search if search else ""
                    data['formvehic'] = AdicionarVehiForm()
                    return render(request ,"admin_vehiculos/poliza.html" ,  data)

            elif action =='personas':
                if 'addpersona' in request.GET:
                    data['title'] = 'Nueva Persona'
                    persona = PersonaConduccionForm()
                    data['form'] = persona
                    data['titulo'] = 'Adicionar Nueva Persona'
                    data['editar']  = 0
                    if 'error' in request.GET:
                        data['error']=1
                    if 'errorform' in request.GET:
                        data['errorform']=1
                    return render(request ,"admin_vehiculos/addpersona.html" ,  data)

                if 'editpersona' in request.GET:
                    data['title'] = 'Editar Persona'
                    persona = PersonaConduccion.objects.get(pk=request.GET['id'])
                    initial = model_to_dict(persona)
                    data['form'] = PersonaConduccionForm(initial=initial)
                    data['editar']  = persona.id
                    data['persona']=persona
                    if 'error' in request.GET:
                        data['error']=1
                    if 'errorform' in request.GET:
                        data['errorform']=1
                    return render(request ,"admin_vehiculos/addpersona.html" ,  data)
                else:
                    search = None
                    if 's' in request.GET:
                        search = request.GET['s']
                    if search:

                        personas = PersonaConduccion.objects.filter(Q(nombres__icontains=search)|Q(identificacion__icontains=search)).order_by('nombres')
                    else:
                        personas = PersonaConduccion.objects.all().order_by('nombres')

                    paging = MiPaginador(personas, 30)
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
                    data['title'] = 'Registro de Personas'
                    data['personas'] = page.object_list
                    data['search'] = search if search else ""
                    return render(request ,"admin_vehiculos/persona.html" ,  data)


            elif action=='delvehiculo':
                vehiculo = Vehiculo.objects.get(pk=request.GET['id'])
                client_address = ip_client_address(request)

                # Log de ADICIONAR NIVEL
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(vehiculo).pk,
                    object_id       = vehiculo.id,
                    object_repr     = force_str(vehiculo),
                    action_flag     = ADDITION,
                    change_message  = 'Eliminado Vehiculo (' + client_address + ')' )
                vehiculo.delete()

                return HttpResponseRedirect('/admin_vehiculos')

            elif action=='verfotovehic':
                if INSCRIPCION_CONDUCCION:
                     vehiculo = Vehiculo.objects.get(pk=request.GET['id'])
                     data['vehiculo'] = vehiculo
                     data['conduccion'] = 'SI'
                     return render(request ,"admin_vehiculos/fotobs.html" ,  data)
            elif action == 'verpoliza':
                    try:
                        vehiculo = Vehiculo.objects.get(pk=request.GET['id'])
                        if PolizaVehiculo.objects.filter(vehiculo=vehiculo).exists():
                            data['poliza'] = Poliza.objects.filter(id__in=PolizaVehiculo.objects.filter(vehiculo=vehiculo).values('poliza')).order_by('-vigente')
                            return render(request ,"admin_vehiculos/verpoliza.html" ,  data)
                        else:
                            return render(request ,"admin_vehiculos/verpoliza.html" ,  data)
                    except:
                        return render(request ,"admin_vehiculos/verpoliza.html" ,  data)
            elif action == 'registro':

                if 'addregistro' in request.GET:
                    data['title'] = 'Nuevo Registro'
                    vehiculo = RegistroVehiculoForm(initial={'fllegada':datetime.now().strftime('%d-%m-%Y'),'fsalida':datetime.now().strftime('%d-%m-%Y'),'kmsalida':'0.00','kmllegada':'0.00','consumocomb':'0.00','costocomb':'0.00','hsalida':'00:00:00','hllegada':'00:00:00'})
                    data['form'] = vehiculo
                    data['titulo'] = 'Adicionar Nuevo Registro'
                    data['editar']  = 0
                    if 'error' in request.GET:
                        data['error']=1
                    if 'errorform' in request.GET:
                        data['errorform']=1
                    if 'errorkm' in request.GET:
                        data['errorkm']=1
                    return render(request ,"admin_vehiculos/addregistro.html" ,  data)
                elif 'editregistro' in request.GET:
                    data['title'] = 'Editar Registro'
                    rvehiculo = RegistroVehiculo.objects.get(pk=request.GET['id'])
                    initial = model_to_dict(rvehiculo)
                    data['form'] = RegistroVehiculoForm(initial=initial)
                    data['editar']  = rvehiculo.id
                    data['rvehiculo']=rvehiculo
                    if 'error' in request.GET:
                        data['error']=1
                    if 'errorform' in request.GET:
                        data['errorform']=1
                    if 'errorkm' in request.GET:
                        data['errorkm']=1
                    return render(request ,"admin_vehiculos/addregistro.html" ,  data)
                elif 'delregvehiculo' in request.GET:
                    rvehiculo = RegistroVehiculo.objects.get(pk=request.GET['id'])
                    client_address = ip_client_address(request)

                    # Log de ADICIONAR NIVEL
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(rvehiculo).pk,
                        object_id       = rvehiculo.id,
                        object_repr     = force_str(rvehiculo),
                        action_flag     = ADDITION,
                        change_message  = 'Eliminado Registro Vehiculo (' + client_address + ')' )
                    rvehiculo.delete()

                    return HttpResponseRedirect('/admin_vehiculos?action=registro')
                else:
                    search = None
                    if 's' in request.GET:
                        search = request.GET['s']
                    if search:
                        ss = search.split(' ')
                        while '' in ss:
                            ss.remove('')
                        if len(ss)==1:
                            regvehiculo = RegistroVehiculo.objects.filter(Q(vehiculo__placa__icontains=search)|Q(vehiculo__codigo__icontains=search)|Q(chofervehiculo__nombres__icontains=search)).order_by('vehiculo__codigo')
                        else:
                            regvehiculo = RegistroVehiculo.objects.all().order_by('vehiculo__codigo')
                    else:
                        regvehiculo = RegistroVehiculo.objects.all().order_by('vehiculo__codigo')
                    paging = MiPaginador(regvehiculo, 30)
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
                    data['title'] = 'Registro de Vehiculo'
                    data['regvehiculo'] = regvehiculo
                    data['regvehiculo'] = page.object_list
                    data['search'] = search if search else ""

                    return render(request ,"admin_vehiculos/registro_vehiculo.html" ,  data)


        else:
            search = None
            cat = None
            if 's' in request.GET:
                search = request.GET['s']
            if 'cat' in request.GET:
                cat = request.GET['cat']
            if search:
                ss = search.split(' ')
                while '' in ss:
                    ss.remove('')
                if len(ss)==1:
                    vehiculo = Vehiculo.objects.filter(Q(placa__icontains=search)|Q(codigo__icontains=search)).order_by('codigo')
                else:
                    vehiculo = Vehiculo.objects.all().order_by('codigo')
            elif cat:
                vehiculo = Vehiculo.objects.filter(categoria=cat).order_by('codigo')
                data['categoriaid'] = cat if cat else ""
                data['categoria'] = CategoriaVehiculo.objects.get(pk=cat) if cat else ""
            else:
                vehiculo = Vehiculo.objects.all().order_by('codigo')

            paging = MiPaginador(vehiculo, 30)
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
            data['title'] = 'Mantenimiento de Vehiculos'
            data['vehiculo'] = vehiculo
            data['vehiculo'] = page.object_list
            data['categorias'] = CategoriaVehiculo.objects.all()
            data['search'] = search if search else ""

            return render(request ,"admin_vehiculos/vehiculo.html" ,  data)
