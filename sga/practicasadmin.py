from datetime import datetime, timedelta
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
from settings import CENTRO_EXTERNO, RUBRO_TIPO_OTRO_MODULO_INTERNO, RUBRO_TIPO_OTRO_INSCRIPCION, DEFAULT_PASSWORD, PROFESORES_GROUP_ID, ALUMNOS_GROUP_ID, UTILIZA_GRUPOS_ALUMNOS, REPORTE_CERTIFICADO_INSCRIPCION, EMAIL_ACTIVE, EVALUACION_ITB, REGISTRO_HISTORIA_NOTAS, NOTA_ESTADO_EN_CURSO, GENERAR_RUBROS_PAGO, GENERAR_RUBRO_INSCRIPCION, GENERAR_RUBRO_INSCRIPCION_MARGEN_DIAS, MODELO_EVALUACION, EVALUACION_IAVQ, EVALUACION_ITS, UTILIZA_NIVEL0_PROPEDEUTICO, TIPO_PERIODO_PROPEDEUTICO, NOTA_ESTADO_APROBADO, UTILIZA_FICHA_MEDICA, EVALUACION_TES, CORREO_INSTITUCIONAL, USA_CORREO_INSTITUCIONAL, INSCRIPCION_CONDUCCION, PROFE_PRACT_CONDUCCION, NEW_PASSWORD, ACTIVA_ADD_EDIT_AD
from sga.alu_malla import aprobadaAsignatura
from sga.commonviews import addUserData, ip_client_address
from sga.docentes import calculate_username

from sga.forms import PersonaForm, InscripcionForm, RecordAcademicoForm, HistoricoRecordAcademicoForm, HistoriaNivelesDeInscripcionForm, \
                      CargarFotoForm, EmpresaInscripcionForm, EstudioInscripcionForm, DocumentoInscripcionForm, ActividadesInscripcionForm, \
                      PadreClaveForm, ConvalidacionInscripcionForm, HistoricoNotasITBForm, GraduadoDatosForm, EgresadoForm, InscripcionSenescytForm,\
                      RetiradoMatriculaForm, InscripcionCextForm, BecarioForm, InscripcionPracticaForm, ObservacionInscripcionForm, ProcesoDobeForm,  \
                      VisitaBibliotecaForm, SesionPracticaForm, TurnoPracticaForm, VehiculoForm,ProfesorForm
from sga.models import Profesor, ProcesoDobe, Persona, Inscripcion, RecordAcademico, DocumentosDeInscripcion, HistoricoRecordAcademico, HistoriaNivelesDeInscripcion, FotoPersona, EmpresaInscripcion, EstudioInscripcion, DocumentoInscripcion, Archivo, TipoArchivo, Grupo, InscripcionGrupo, PerfilInscripcion, HistoricoNotasITB, PadreClave, Malla, ConvalidacionInscripcion, TipoEstado, Rubro, RubroInscripcion, NivelMalla, EjeFormativo, AsignaturaMalla, Egresado, Asignatura, InscripcionSenescyt, RetiradoMatricula, Carrera, Modalidad, Sesion, Especialidad, Materia, Nivel, TipoOtroRubro, Matricula, MateriaAsignada, RubroOtro, Graduado, InscripcionBecario, InscripcionPracticas, ObservacionInscripcion, InscripcionConduccion, VisitaBiblioteca, TipoVisitasBiblioteca, DetalleVisitasBiblioteca, TipoPersona, SesionPractica, TurnoPractica, Vehiculo, GrupoPractica, Practica
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
        if action=='seccionadd':
            if int(request.POST['edit'])== 0:
                f = SesionPracticaForm(request.POST)
            else :
                f = SesionPracticaForm(request.POST, instance=SesionPractica.objects.get(pk=request.POST['edit']))
            if f.is_valid():
                f.save()
                sesion=f.instance
                client_address = ip_client_address(request)

                # Log de ADICIONAR NIVEL
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(sesion).pk,
                    object_id       = sesion.id,
                    object_repr     = force_str(sesion),
                    action_flag     = ADDITION,
                    change_message  = 'Adicionar/Editar Seccion (' + client_address + ')' )
                return HttpResponseRedirect("/practicasadmin?action=seccion")


        elif action=='turnoadd':
            if int(request.POST['edit'])== 0:
                f = TurnoPracticaForm(request.POST)
            else :
                f = TurnoPracticaForm(request.POST, instance=TurnoPractica.objects.get(pk=request.POST['edit']))
            if f.is_valid():
                f.save()
                turno=f.instance
                client_address = ip_client_address(request)

                # Log de ADICIONAR NIVEL
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(turno).pk,
                    object_id       = turno.id,
                    object_repr     = force_str(turno),
                    action_flag     = ADDITION,
                    change_message  = 'Adicionar/Editar Turno (' + client_address + ')' )
                return HttpResponseRedirect("/practicasadmin?action=turno")

        elif action=='vehiculoadd':
            if int(request.POST['edit'])== 0:
                f = VehiculoForm(request.POST)
            else :
                f = VehiculoForm(request.POST, instance=Vehiculo.objects.get(pk=request.POST['edit']))
            if f.is_valid():
                f.save()
                vehiculo=f.instance
                practica= Practica.objects.get(pk=request.POST['practica'])
                id=practica.grupopracticas.id
                client_address = ip_client_address(request)

                # Log de ADICIONAR NIVEL
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(vehiculo).pk,
                    object_id       = vehiculo.id,
                    object_repr     = force_str(vehiculo),
                    action_flag     = ADDITION,
                    change_message  = 'Adicionar/Editar Vehiculo (' + client_address + ')' )
                return HttpResponseRedirect("/practicasadmin?action=vehiculo&id="+str(id)+"&practica="+str(practica.id))


        elif action == 'add':
            f = ProfesorForm(request.POST)
            if f.is_valid():
                persona = Persona(nombres=f.cleaned_data['nombres'],
                                  apellido1=f.cleaned_data['apellido1'],
                                  apellido2=f.cleaned_data['apellido2'],
                                  extranjero=f.cleaned_data['extranjero'],
                                  cedula=f.cleaned_data['cedula'],
                                  pasaporte=f.cleaned_data['pasaporte'],
                                  nacimiento=f.cleaned_data['nacimiento'],
                                  provincia=f.cleaned_data['provincia'],
                                  canton=f.cleaned_data['canton'],
                                  sexo=f.cleaned_data['sexo'],
                                  nacionalidad=f.cleaned_data['nacionalidad'],
                                  madre=f.cleaned_data['madre'],
                                  padre=f.cleaned_data['padre'],
                                  direccion=f.cleaned_data['direccion'],
                                  direccion2=f.cleaned_data['direccion2'],
                                  num_direccion=f.cleaned_data['num_direccion'],
                                  sector=f.cleaned_data['sector'],
                                  ciudad=f.cleaned_data['ciudad'],
                                  telefono=f.cleaned_data['telefono'],
                                  telefono_conv=f.cleaned_data['telefono_conv'],
                                  email=f.cleaned_data['email'],
                                  sangre=f.cleaned_data['sangre'],
                                  parroquia=f.cleaned_data['parroquia'])
                persona.save()
                username = calculate_username(persona)
                password = DEFAULT_PASSWORD
                user = User.objects.create_user(username, persona.email, password)
                user.save()
                persona.usuario = user
                if USA_CORREO_INSTITUCIONAL:
                    persona.emailinst = user.username + '' + CORREO_INSTITUCIONAL
                else:
                    persona.emailinst = ''
                persona.save()
                profesor = Profesor(persona=persona,
                                    activo=True,
                                    fechaingreso=f.cleaned_data['fechaingreso'],
                                    dedicacion=f.cleaned_data['dedicacion'],
                                    categoria=f.cleaned_data['categoria'],
                                    numerocontrato=f.cleaned_data['numerocontrato'],
                                    relaciontrab=f.cleaned_data['relaciontrab'])
                profesor.save()
                g = Group.objects.get(pk=PROFESORES_GROUP_ID)
                g.user_set.add(user)
                g.save()

                #Comprobar si es discapacitado
                if f.cleaned_data['tienediscapacidad']==True:
                    profesor.tienediscapacidad = f.cleaned_data['tienediscapacidad']
                    profesor.tipodiscapacidad = f.cleaned_data['tipodiscapacidad']
                    profesor.porcientodiscapacidad = f.cleaned_data['porcientodiscapacidad']
                    profesor.carnetdiscapacidad = f.cleaned_data['carnetdiscapacidad']
                else:
                    profesor.tienediscapacidad = False
                    profesor.tipodiscapacidad = None
                    profesor.porcientodiscapacidad = 0
                    profesor.carnetdiscapacidad = ''

                profesor.save()

                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de ADICIONAR PROFESOR
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(profesor).pk,
                    object_id       = profesor.id,
                    object_repr     = force_str(profesor),
                    action_flag     = CHANGE,
                    change_message  = 'Adicionado Instructor (' + client_address + ')')

                if profesor.persona.cedula:
                    return HttpResponseRedirect("/practicasadmin?action=instructores&s="+str(profesor.persona.cedula))
                else:
                    return HttpResponseRedirect("/practicasadmin?action=instructores&s="+str(profesor.persona.pasaporte))

            else:
                return HttpResponseRedirect("/practicasadmin?action=add")
        elif action == 'edit':
            profesor = Profesor.objects.get(pk=request.POST['id'])
            f = ProfesorForm(request.POST)
            if f.is_valid():
                profesor.persona.nombres = f.cleaned_data['nombres']
                profesor.persona.apellido1 = f.cleaned_data['apellido1']
                profesor.persona.apellido2 = f.cleaned_data['apellido2']
                profesor.persona.extranjero = f.cleaned_data['extranjero']
                profesor.persona.cedula = f.cleaned_data['cedula']
                profesor.persona.pasaporte = f.cleaned_data['pasaporte']
                profesor.persona.nacimiento = f.cleaned_data['nacimiento']
                profesor.persona.provincia = f.cleaned_data['provincia']
                profesor.persona.canton = f.cleaned_data['canton']
                profesor.persona.sexo = f.cleaned_data['sexo']
                profesor.persona.nacionalidad = f.cleaned_data['nacionalidad']
                profesor.persona.madre = f.cleaned_data['madre']
                profesor.persona.padre = f.cleaned_data['padre']
                profesor.persona.direccion = f.cleaned_data['direccion']
                profesor.persona.direccion2 = f.cleaned_data['direccion2']
                profesor.persona.num_direccion = f.cleaned_data['num_direccion']
                profesor.persona.sector = f.cleaned_data['sector']
                profesor.persona.ciudad = f.cleaned_data['ciudad']
                profesor.persona.telefono = f.cleaned_data['telefono']
                profesor.persona.telefono_conv = f.cleaned_data['telefono_conv']
                profesor.persona.email = f.cleaned_data['email']
                # profesor.persona.emailinst = f.cleaned_data['emailinst']
                profesor.persona.sangre = f.cleaned_data['sangre']
                profesor.persona.parroquia = f.cleaned_data['parroquia']
                profesor.persona.save()
                profesor.fechaingreso = f.cleaned_data['fechaingreso']
                profesor.dedicacion = f.cleaned_data['dedicacion']
                profesor.categoria = f.cleaned_data['categoria']
                profesor.numerocontrato = f.cleaned_data['numerocontrato']
                profesor.relaciontrab = f.cleaned_data['relaciontrab']
                profesor.save()

                #Comprobar si es discapacitado
                if f.cleaned_data['tienediscapacidad']==True:
                    profesor.tienediscapacidad = True
                    profesor.tipodiscapacidad = f.cleaned_data['tipodiscapacidad']
                    profesor.porcientodiscapacidad = f.cleaned_data['porcientodiscapacidad']
                    profesor.carnetdiscapacidad = f.cleaned_data['carnetdiscapacidad']
                else:
                    profesor.tienediscapacidad = False
                    profesor.tipodiscapacidad = None
                    profesor.porcientodiscapacidad = 0
                    profesor.carnetdiscapacidad = ''

                profesor.save()

                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de EDITAR PROFESOR
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(profesor).pk,
                    object_id       = profesor.id,
                    object_repr     = force_str(profesor),
                    action_flag     = CHANGE,
                    change_message  = 'Editado Instructor (' + client_address + ')')

                if profesor.persona.cedula:
                    return HttpResponseRedirect("/practicasadmin?action=instructores&s="+str(profesor.persona.cedula))
                else:
                    return HttpResponseRedirect("/practicasadmin?action=instructores&s="+str(profesor.persona.pasaporte))
            else:
                return HttpResponseRedirect("/practicasadmin?action=edit&id="+str(profesor.id))
    else:
        data = {'title': 'Mantenimiento de Seccion'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='seccion':
                search = None
                if 's' in request.GET:
                    search = request.GET['s']
                if search:
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')
                    if len(ss)==1:
                        sesion = SesionPractica.objects.filter(nombre__icontains=search).order_by('nombre')
                    else:
                        sesion = SesionPractica.objects.all().order_by('comienza')
                else:
                    sesion = SesionPractica.objects.all().order_by('comienza')

                paging = MiPaginador(sesion, 30)
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
                data['title'] = 'Mantenimiento de Seccion'
                data['seccion'] = page.object_list
                return render(request ,"practicasadmin/sesionprac.html" ,  data)

            elif action=='seccionadd':
                data['title'] = 'Nueva Seccion'
                seccion = SesionPracticaForm()
                data['form'] = seccion
                data['titulo'] = 'Adicionar Nueva Seccion'
                data['editar']  = 0
                return render(request ,"practicasadmin/addseccion.html" ,  data)

            elif action=='editseccion':
                data['title'] = 'Editar Seccion'
                sesion = SesionPractica.objects.get(pk=request.GET['id'])
                seccion = SesionPracticaForm(instance=sesion)
                data['form'] = seccion
                data['titulo'] = 'Editar Seccion'
                data['editar']  = sesion.id
                return render(request ,"practicasadmin/addseccion.html" ,  data)

            elif action=='delseccion':
                sesion = SesionPractica.objects.get(pk=request.GET['id'])
                client_address = ip_client_address(request)

                # Log de ADICIONAR NIVEL
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(sesion).pk,
                    object_id       = sesion.id,
                    object_repr     = force_str(sesion),
                    action_flag     = ADDITION,
                    change_message  = 'Eliminar Seccion (' + client_address + ')' )
                sesion.delete()
                return HttpResponseRedirect('/practicasadmin?action=seccion')

            elif action=='turno':
                search = None
                if 's' in request.GET:
                    search = request.GET['s']
                if search:
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')
                    if len(ss)==1:
                        turno = TurnoPractica.objects.filter(sesionpracticas__nombre__icontains=search).order_by('sesionpracticas','turno')
                    else:
                        turno = TurnoPractica.objects.all().order_by('sesionpracticas','turno')
                else:
                    turno = TurnoPractica.objects.all().order_by('sesionpracticas','turno')

                paging = MiPaginador(turno, 30)
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
                data['title'] = 'Mantenimiento de Turnos'
                data['turno'] = turno
                data['editar'] = 0
                return render(request ,"practicasadmin/turnoprac.html" ,  data)

            elif action=='turnoadd':
                data['title'] = 'Nuevo Turno'
                turno = TurnoPracticaForm()
                data['form'] = turno
                data['editar']  = 0
                data['sesion']  = 0
                data['titulo'] = 'Adicionar Nuevo Turno'
                return render(request ,"practicasadmin/addturno.html" ,  data)

            elif action=='editturno':
                data['title'] = 'Editar Turno'
                turno = TurnoPractica.objects.get(pk=request.GET['id'])
                practica = 0
                if GrupoPractica.objects.filter(sesionpracticas=turno.sesionpracticas.id).exists():
                    grupo = GrupoPractica.objects.get(sesionpracticas=turno.sesionpracticas.id)
                    if Practica.objects.filter(grupopracticas=grupo).exists():
                        practica=turno.sesionpracticas.id
                turnof = TurnoPracticaForm(instance=turno)
                data['form'] = turnof
                data['titulo'] = 'Editar Seccion'
                data['editar']  = turno.id
                data['sesion']  = practica
                return render(request ,"practicasadmin/addturno.html" ,  data)

            elif action=='delturno':
                turno = TurnoPractica.objects.get(pk=request.GET['id'])
                client_address = ip_client_address(request)

                # Log de ADICIONAR NIVEL
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(turno).pk,
                    object_id       = turno.id,
                    object_repr     = force_str(turno),
                    action_flag     = ADDITION,
                    change_message  = 'Eliminar Seccion (' + client_address + ')' )
                turno.delete()
                return HttpResponseRedirect('/practicasadmin?action=turno')
            elif action=='vehiculo':
                search = None
                if 's' in request.GET:
                    search = request.GET['s']
                if search:
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')
                    if len(ss)==1:
                        vehiculo = Vehiculo.objects.filter(Q(placa__icontains=search)|Q(codigo__icontains=search)).order_by('placa')
                    else:
                        vehiculo = Vehiculo.objects.all().order_by('placa')
                else:
                    vehiculo = Vehiculo.objects.all().order_by('placa')

                paging = MiPaginador(vehiculo, 30)
                p = 1

                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                    page = paging.page(p)
                except:
                        page = paging.page(p)
                grupopractica = GrupoPractica.objects.get(pk=request.GET['id'])
                practica = Practica.objects.get(pk=request.GET['practica'])
                data['paging'] = paging
                data['rangospaging'] = paging.rangos_paginado(p)
                data['page'] = page
                data['title'] = 'Mantenimiento de Vehiculos'
                data['vehiculo'] = vehiculo
                data['grupopractica'] = grupopractica
                data['practica'] =  practica
                return render(request ,"practicasadmin/vehiculo.html" ,  data)

            elif action=='vehiculoadd':
                data['title'] = 'Nuevo Vehiculo'
                vehiculo = VehiculoForm()
                data['form'] = vehiculo
                data['titulo'] = 'Adicionar Nuevo Vehiculo'
                data['editar']  = 0
                data['practica'] = Practica.objects.get(pk=request.GET['practica'])
                return render(request ,"practicasadmin/addvehiculo.html" ,  data)

            elif action=='editvehiculo':
                data['title'] = 'Editar Vehiculo'
                vehiculo = Vehiculo.objects.get(pk=request.GET['id'])
                vehiculof = VehiculoForm(instance=vehiculo)
                data['form'] = vehiculof
                data['titulo'] = 'Editar Vehiculo'
                data['practica'] = Practica.objects.get(pk=request.GET['practica'])
                data['editar']  = vehiculo.id
                return render(request ,"practicasadmin/addvehiculo.html" ,  data)

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
                    change_message  = 'Eliminar Seccion (' + client_address + ')' )
                vehiculo.delete()
                practica= Practica.objects.filter(pk=request.GET['practica'])[:1].get()
                id=practica.grupopracticas.id
                return HttpResponseRedirect('/practicasadmin?action=vehiculo&&id='+str(id)+'&practica='+str(practica.id))

            elif action == 'instructores':
                search = None
                todos = None
                activos = None
                inactivos = None
                periodo = request.session['periodo']
                sin_coordinadores = Carrera.objects.all().exclude(coordinadorcarrera__periodo=periodo)
                if 's' in request.GET:
                    search = request.GET['s']
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
                    if len(ss) == 1:
                        profesores = Profesor.objects.filter(Q(persona__nombres__icontains=search) |
                                                             Q(persona__apellido1__icontains=search) |
                                                             Q(persona__apellido2__icontains=search) |
                                                             Q(persona__cedula__icontains=search) |
                                                             Q(persona__pasaporte__icontains=search)).order_by('persona__apellido1')
                    else:
                        profesores = Profesor.objects.filter(Q(persona__apellido1__icontains=ss[0]) &
                                                             Q(persona__apellido2__icontains=ss[1])).order_by('persona__apellido1', 'persona__apellido2', 'persona__nombres')
                else:
                    profesores = Profesor.objects.filter(activo=True,dedicacion=PROFE_PRACT_CONDUCCION).order_by('persona__apellido1')
                if todos:
                    profesores = Profesor.objects.filter(dedicacion=PROFE_PRACT_CONDUCCION).order_by('persona__apellido1')
                if activos:
                    profesores = Profesor.objects.filter(activo=True,dedicacion=PROFE_PRACT_CONDUCCION).order_by('persona__apellido1')
                if inactivos:
                    profesores = Profesor.objects.filter(activo=False,dedicacion=PROFE_PRACT_CONDUCCION).order_by('persona__apellido1')
                paging = MiPaginador(profesores, 30)
                p=1
                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                    page = paging.page(p)
                except:
                    page = paging.page(p)
                data['paging'] = paging
                data['search'] = search if search else ""
                data['todos'] = todos if todos else ""
                data['activos'] = activos if activos else ""
                data['inactivos'] = inactivos if inactivos else ""
                data['profesores'] = page.object_list
                data['clave'] = DEFAULT_PASSWORD
                data['alum'] = 0
                data['carreras']= sin_coordinadores
                data['usafichamedica'] = UTILIZA_FICHA_MEDICA
                data['cantidadcarreras'] = sin_coordinadores.count()
                return render(request ,"practicasadmin/instructores.html" ,  data)
            if action == 'activation':
                d = Profesor.objects.get(pk=request.GET['id'])
                d.activo = not d.activo
                d.save()
                return HttpResponseRedirect("/practicasadmin?action=instructores")
            elif action == 'add':
                data['title'] = 'Adicionar Instructor'
                form = ProfesorForm()
                form.filtra_instructor(PROFE_PRACT_CONDUCCION)
                data['form'] = form
                return render(request ,"practicasadmin/adicionar.html" ,  data)

            elif action == 'edit':
                p = Profesor.objects.get(pk=request.GET['id'])
                initial = model_to_dict(p)
                initial.update(model_to_dict(p.persona))
                form = ProfesorForm(initial=initial)
                form.filtra_instructor(PROFE_PRACT_CONDUCCION)
                data['form'] = form
                data['profesor'] = p
                return render(request ,"practicasadmin/editainstruc.html" ,  data)

            #Horas de diferentes actividades que realiza el docente
        else:


            if 'g' in request.GET:
                grupoid = request.GET['g']
                data['grupo'] = TipoPersona.objects.get(pk=request.GET['g'])
                data['grupoid'] = int(grupoid) if grupoid else ""
                visitabiblioteca = VisitaBiblioteca.objects.filter(tipopersona=data['grupo'])
            else:
                 visitabiblioteca = VisitaBiblioteca.objects.all().order_by('nombre')

            paging = MiPaginador(visitabiblioteca, 30)
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
            data['visitabiblioteca'] = page.object_list
            data['utiliza_grupos_alumnos'] = UTILIZA_GRUPOS_ALUMNOS
            data['reporte_ficha_id'] = REPORTE_CERTIFICADO_INSCRIPCION
            data['clave'] = DEFAULT_PASSWORD
            data['usafichamedica'] = UTILIZA_FICHA_MEDICA
            data['centroexterno'] = CENTRO_EXTERNO
            data['matriculalibre'] = MODELO_EVALUACION==EVALUACION_TES
            data['grupos'] = TipoPersona.objects.all().order_by('descripcion')
            return render(request ,"practicasadmin/modificaciones1.html" ,  data)
