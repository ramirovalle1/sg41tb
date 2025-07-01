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
from settings import CENTRO_EXTERNO, RUBRO_TIPO_OTRO_MODULO_INTERNO, RUBRO_TIPO_OTRO_INSCRIPCION, DEFAULT_PASSWORD, PROFESORES_GROUP_ID, ALUMNOS_GROUP_ID, UTILIZA_GRUPOS_ALUMNOS, REPORTE_CERTIFICADO_INSCRIPCION, EMAIL_ACTIVE, EVALUACION_ITB, REGISTRO_HISTORIA_NOTAS, NOTA_ESTADO_EN_CURSO, GENERAR_RUBROS_PAGO, GENERAR_RUBRO_INSCRIPCION, GENERAR_RUBRO_INSCRIPCION_MARGEN_DIAS, MODELO_EVALUACION, EVALUACION_IAVQ, EVALUACION_ITS, UTILIZA_NIVEL0_PROPEDEUTICO, TIPO_PERIODO_PROPEDEUTICO, NOTA_ESTADO_APROBADO, UTILIZA_FICHA_MEDICA, EVALUACION_TES, CORREO_INSTITUCIONAL, USA_CORREO_INSTITUCIONAL, INSCRIPCION_CONDUCCION,TIPO_AYUDA_FINANCIERA
from sga.alu_malla import aprobadaAsignatura
from sga.commonviews import addUserData, ip_client_address
from sga.docentes import calculate_username
from sga.forms import PersonaForm, InscripcionForm, RecordAcademicoForm, HistoricoRecordAcademicoForm, HistoriaNivelesDeInscripcionForm, CargarFotoForm, EmpresaInscripcionForm, EstudioInscripcionForm, DocumentoInscripcionForm, ActividadesInscripcionForm, PadreClaveForm, ConvalidacionInscripcionForm, HistoricoNotasITBForm, GraduadoDatosForm, EgresadoForm, InscripcionSenescytForm, RetiradoMatriculaForm, InscripcionCextForm, BecarioForm, InscripcionPracticaForm, ObservacionInscripcionForm, ProcesoDobeForm,  ActivaInactivaUsuarioForm, MatriculaBecaForm,\
     MatBecaForm,DetalleRubrosPagadosForm,DetalleBecaCompletaForm

from sga.models import Profesor, ProcesoDobe, Persona, Inscripcion, RecordAcademico, DocumentosDeInscripcion, HistoricoRecordAcademico, HistoriaNivelesDeInscripcion, FotoPersona, EmpresaInscripcion, EstudioInscripcion, DocumentoInscripcion, Archivo, TipoArchivo, Grupo, InscripcionGrupo, PerfilInscripcion, HistoricoNotasITB, PadreClave, Malla, ConvalidacionInscripcion, TipoEstado, Rubro, RubroInscripcion, NivelMalla, EjeFormativo, AsignaturaMalla, Egresado, Asignatura, InscripcionSenescyt, RetiradoMatricula, Carrera, Modalidad, Sesion, Especialidad, Materia, Nivel, TipoOtroRubro, Matricula, MateriaAsignada, RubroOtro, Graduado, InscripcionBecario, InscripcionPracticas, ObservacionInscripcion, InscripcionConduccion, InactivaActivaUsr, TipoBeneficio,DetalleRubrosBeca
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

def convertir_fecha(s):
    return datetime(int(s[6:10]), int(s[3:5]), int(s[0:2]))

@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
@transaction.atomic()
def view(request):
    if request.method=='POST':
        action = request.POST['action']


        if action=='delpracticas':
            practica = InscripcionPracticas.objects.get(pk=request.POST['id'])
            inscripcion = practica.inscripcion
            practica.delete()
            return HttpResponseRedirect("/becas_matricula?action=practicas&id="+str(inscripcion.id))
        elif action=='beca':
                matricula = Matricula.objects.get(pk=request.POST['id'])
                inscripcion = Inscripcion.objects.get(pk=matricula.inscripcion_id)
                matriculas = Matricula.objects.filter(inscripcion=inscripcion)
                data={}
                data['inscripcion'] = inscripcion
                data['matriculas'] = matriculas
                f = MatriculaBecaForm(request.POST)


                if f.is_valid():

                    #Obtain client ip address
                    client_address = ip_client_address(request)
                    if matricula.becado:
                        # Log de ADICIONAR RECORD
                        LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(matricula).pk,
                        object_id       = matricula.id,
                        object_repr     = force_str(matricula),
                        action_flag     = ADDITION,
                        change_message  = 'Editar Informacion de Beca (' + client_address + ')' )
                    else:
                        # Log de ADICIONAR RECORD
                        LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(matricula).pk,
                        object_id       = matricula.id,
                        object_repr     = force_str(matricula),
                        action_flag     = ADDITION,
                        change_message  = 'Adicionadar Informacion de Beca (' + client_address + ')' )
                    matricula.becado = f.cleaned_data['becado']
                    matricula.tipobeneficio = f.cleaned_data['tipobeneficio']
                    matricula.porcientobeca = f.cleaned_data['porcientobeca']
                    matricula.tipobeca = f.cleaned_data['tipobeca']
                    matricula.motivobeca = f.cleaned_data['motivobeca']
                    matricula.fechabeca = f.cleaned_data['fechabeca']
                    matricula.observaciones = f.cleaned_data['observaciones']
                    matricula.save()

                    return HttpResponseRedirect("/becas_matricula?action=estudio&id="+str(inscripcion.id))


                    # return render(request ,"becas_matricula/estudiobs.html" ,  data)
                        # return HttpResponseRedirect("/becas_matricula?action=estudio&id="+str(matricula.inscripcion.id))
                    #Estudios Realizados del estudiante

        elif action=='becarubrospagados':
                try:
                    if 'p' in request.POST:
                         matricula = Matricula.objects.get(pk=request.POST['matricula'])
                         datos = json.loads(request.POST['datos'])
                         #OCU Para traer los rubros que se les aplica el descuento y grabarlo en la tabla de detalle
                         for d in datos['detalle']:
                            rubro = Rubro.objects.get(pk=int(d['rubro']))
                            descriprubro = rubro.nombre()

                            if d['porcentaje']:
                                pp =Decimal((100.0-float( d['porcentaje']))/100.0)
                                descuento=Decimal(d['valorrubro'])
                                descuento *= pp
                                descuento=Decimal(d['valorrubro'])-Decimal(descuento)
                                porcentaje=Decimal(d['porcentaje'])
                            else:
                                descuento=d['descuento']
                                if not d['porcentaje']:
                                    porcentaje=0

                            detalle = DetalleRubrosBeca(matricula=matricula,
                                                       rubro = rubro,
                                                       descripcion=descriprubro,
                                                       descuento = float(descuento),
                                                       porcientobeca = porcentaje,
                                                       valorrubro=Decimal(d['valorrubro']),
                                                       fecha = datetime.now(),
                                                       usuario = request.user)
                            detalle.save()

                         #Obtain client ip address
                         client_address = ip_client_address(request)

                         # Log de ADICIONAR BECA PARCIAL
                         LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(matricula).pk,
                            object_id       = matricula.id,
                            object_repr     = force_str(matricula),
                            action_flag     = ADDITION,
                            change_message  = 'Asignada Beca Rubros Pagados (' + client_address + ')' )

                         # return HttpResponseRedirect("/becas_matricula?action=estudio&id="+str(matricula.inscripcion_id))
                         data = {}
                         data['result']='ok'
                         data['urlma']='/becas_matricula?action=estudio&id='+str(matricula.inscripcion_id)
                         return HttpResponse(json.dumps(data),content_type="application/json")

                except Exception as ex:
                         data['result']='bad'
                         return HttpResponse(json.dumps(data),content_type="application/json")

        elif action=='buscarrubro':
                rubroexiste=request.POST['rubro']
                if rubroexiste:
                    # OCastillo 13-09-2016 para validar que no se repitan los rubros en la tb detallerubro
                    if DetalleRubrosBeca.objects.filter(rubro=rubroexiste).exists():
                        return HttpResponse(json.dumps({"result":"bad","rubro": str(rubroexiste)}),content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")

        elif action == 'deleterubro':

                detalle = DetalleRubrosBeca.objects.get(pk=request.POST['id'])
                matricula =detalle.matricula
                if  detalle:
                    detalle.delete()

                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de Eliminar CERRAR MATERIA
                    LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(detalle).pk,
                    object_id       = detalle.id,
                    object_repr     = force_str(detalle),
                    action_flag     = DELETION,
                    change_message  = 'Elimanado Rubro Pagado Beca (' + client_address + ')' )


                    return HttpResponseRedirect("/becas_matricula?action=verrubros&id="+str(matricula.id))

                else:
                    return HttpResponseRedirect("/becas_matricula"+"&error=1")


        elif action=='becacompleta':
        # OCastillo 06-01-2017 para el registro de valores de beca completa por matricula
                try:
                    if 'matricula' in request.POST:
                         matricula = Matricula.objects.get(pk=request.POST['matricula'])
                         descuento=Decimal(request.POST['valorrubro'])
                         porcentaje=100
                         detalle = request.POST['detalle']
                         detalle = detalle.upper( )

                         detalle = DetalleRubrosBeca(matricula=matricula,
                                                   descripcion=detalle,
                                                   descuento = float(descuento),
                                                   porcientobeca = porcentaje,
                                                   valorrubro=float(descuento),
                                                   fecha = datetime.now(),
                                                   usuario = request.user)
                         detalle.save()

                         #Obtain client ip address
                         client_address = ip_client_address(request)

                         # Log de ADICIONAR VALORES BECA 100%
                         LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(matricula).pk,
                            object_id       = matricula.id,
                            object_repr     = force_str(matricula),
                            action_flag     = ADDITION,
                            change_message  = 'Asignada Beca 100% (' + client_address + ')' )

                         data = {}
                         data['result']='ok'
                         return HttpResponseRedirect("/becas_matricula?action=estudio&id="+str(matricula.inscripcion.id))

                except Exception as ex:
                         data['result']='bad'
                         return HttpResponse(json.dumps(data),content_type="application/json")





    else:
        data = {'title': 'Listado de Matriculas'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='activation':
                d = Profesor.objects.get(pk=request.GET['id'])
                d.activo = not d.activo
                d.save()
                return HttpResponseRedirect("/docentes")


            elif action=='estudio':
                inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                data['inscripcion'] = inscripcion
                matricula = Matricula.objects.filter(inscripcion=inscripcion)
                data['matriculas'] = matricula
                return render(request ,"becas_matricula/estudiobs.html" ,  data)


            elif action=='eliminarbeca':
                matricula = Matricula.objects.get(pk=request.GET['id'])
                inscripcion = Inscripcion.objects.get(pk=matricula.inscripcion.id)
                data['inscripcion'] = inscripcion
                data['matriculas'] = matricula
                matricula.becado = False
                matricula.tipobeneficio = None
                matricula.porcientobeca = None
                matricula.tipobeca =None
                matricula.motivobeca = None
                matricula.fechabeca = None
                matricula.observaciones = None
                matricula.save()

                detalle = DetalleRubrosBeca.objects.filter(matricula=matricula)
                detalle.delete()

                client_address = ip_client_address(request)

                LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(matricula).pk,
                        object_id       = matricula.id,
                        object_repr     = force_str(matricula),
                        action_flag     = DELETION,
                        change_message  = 'Eliminar Informacion de Beca (' + client_address + ')' )
                return HttpResponseRedirect("/becas_matricula?action=estudio&id="+str(inscripcion.id))


            elif action=='asignarbeca':

                data['title'] = 'Aplicar Porciento de Beca a Estudiantes'
                matricula = Matricula.objects.get(pk=request.GET['id'])
                data['matricula'] = matricula
                initial = model_to_dict(matricula)
                data['form'] = MatBecaForm(initial=initial)
                data['tipo_ayuda_financiera'] = TIPO_AYUDA_FINANCIERA
                return render(request ,"becas_matricula/aplicar_beca.html" ,  data)

                # data['title'] = 'Asignar una Beca'
                # inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                # data['inscripcion'] = inscripcion
                # data['form'] = BecarioForm()
                # return render(request ,"becas_matricula/asignarbeca.html" ,  data)

            elif action=='agregarrubros':

                    data['title'] = 'Agregar Becas de Rubros Cancelados a Estudiantes'
                    matricula = Matricula.objects.get(pk=request.GET['id'])
                    data['inscripcion'] = Inscripcion.objects.get(id=matricula.inscripcion_id)
                    data['matricula']=   matricula

                    rubros = Rubro.objects.filter(inscripcion=data['inscripcion'],cancelado=True).values('id')
                    form = DetalleRubrosPagadosForm()
                    form.rubros_list(rubros)

                    data['rubros']= Rubro.objects.filter(inscripcion=data['inscripcion'],cancelado=True)
                    data['form']= form

                    #OCU 05-enero-2017 para ingresar rubros de beca del 100%
                    if not matricula.porcientobeca == 100:
                        return render(request ,"becas_matricula/rubrospagados.html" ,  data)
                    else:
                        data['title'] = 'Agregar  Rubros a Becas de 100%'
                        form =DetalleBecaCompletaForm()
                        data['form']= form
                        return render(request ,"becas_matricula/becacompleta.html" ,  data)


            elif action == 'verrubros':
                    data['title'] = 'Detalle    Rubros del Estudiante'
                    detrubros = DetalleRubrosBeca.objects.filter(matricula=request.GET['id'])
                    matricula = Matricula.objects.get(pk=request.GET['id'])
                    inscripcion = Inscripcion.objects.get(pk=matricula.inscripcion.id)
                    search = None

                    paging = Paginator(detrubros, 50)
                    p = 1
                    try:
                        if 'page' in request.GET:
                            p = int(request.GET['page'])
                        page = paging.page(p)
                    except:
                        page = paging.page(1)
                    data['paging'] = paging
                    data['page'] = page
                    data['detrubros'] = page.object_list
                    data['detalle'] = detrubros
                    data['matricula'] = matricula
                    data['inscripcion']=inscripcion

                    if 'error' in request.GET:
                        data['error'] = 1
                    return render(request ,"becas_matricula/verrubros.html" ,  data)

            elif action == 'deleterubro':
                    data['title'] = 'Borrar Rubro Beca Aplicada'
                    data['detalle'] = DetalleRubrosBeca.objects.get(pk=request.GET['id'])
                    detallemat = DetalleRubrosBeca.objects.get(pk=request.GET['id'])
                    data['matricula']= Matricula.objects.get(pk=detallemat.matricula.id)
                    return render(request ,"becas_matricula/borrar_rubros.html" ,  data)

            return HttpResponseRedirect("/becas_matricula")

        else:
            search = None
            todos = None
            activos = None
            inactivos = None

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
                if len(ss)==1:
                    becas_matricula = Inscripcion.objects.filter(Q(persona__nombres__icontains=search) | Q(persona__apellido1__icontains=search) | Q(persona__apellido2__icontains=search) | Q(persona__cedula__icontains=search) | Q(persona__pasaporte__icontains=search) | Q(identificador__icontains=search) | Q(inscripciongrupo__grupo__nombre__icontains=search) | Q(carrera__nombre__icontains=search) | Q(persona__usuario__username__icontains=search)).order_by('persona__apellido1')
                else:
                    becas_matricula = Inscripcion.objects.filter(Q(persona__apellido1__icontains=ss[0]) & Q(persona__apellido2__icontains=ss[1])).order_by('persona__apellido1','persona__apellido2','persona__nombres')

            else:
                becas_matricula = Inscripcion.objects.filter(persona__usuario__is_active=True).order_by('persona__apellido1')

            if 'g' in request.GET:
                grupoid = request.GET['g']
                data['grupo'] = Grupo.objects.get(pk=request.GET['g'])
                data['grupoid'] = int(grupoid) if grupoid else ""
                becas_matricula = becas_matricula.filter(carrera__grupocoordinadorcarrera__group__in=request.user.groups.all(), inscripciongrupo__grupo=data['grupo']).distinct()
            # else:
            #     becas_matricula = becas_matricula.filter(carrera__grupocoordinadorcarrera__group__in=request.user.groups.all()).distinct()

            if todos:
                becas_matricula = Inscripcion.objects.all().order_by('persona__apellido1')
            if activos:
                becas_matricula = Inscripcion.objects.filter(persona__usuario__is_active=True).order_by('persona__apellido1')
            if inactivos:
                becas_matricula = Inscripcion.objects.filter(persona__usuario__is_active=False).order_by('persona__apellido1')

            if CENTRO_EXTERNO and not ('s' in request.GET):
                becas_matricula = Inscripcion.objects.all().order_by('persona__apellido1')

            paging = MiPaginador(becas_matricula, 30)
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
            data['search'] = search if search else ""
            data['todos'] = todos if todos else ""
            data['activos'] = activos if activos else ""
            data['inactivos'] = inactivos if inactivos else ""
            data['becas_matricula'] = page.object_list
            data['utiliza_grupos_alumnos'] = UTILIZA_GRUPOS_ALUMNOS
            data['reporte_ficha_id'] = REPORTE_CERTIFICADO_INSCRIPCION
            data['clave'] = DEFAULT_PASSWORD
            data['usafichamedica'] = UTILIZA_FICHA_MEDICA
            data['centroexterno'] = CENTRO_EXTERNO
            data['matriculalibre'] = MODELO_EVALUACION==EVALUACION_TES
            data['grupos'] = Grupo.objects.all().order_by('nombre')
            return render(request ,"becas_matricula/inscripcionesbs.html" ,  data)
