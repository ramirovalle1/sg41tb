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
from settings import CENTRO_EXTERNO, RUBRO_TIPO_OTRO_MODULO_INTERNO, RUBRO_TIPO_OTRO_INSCRIPCION, DEFAULT_PASSWORD, PROFESORES_GROUP_ID, ALUMNOS_GROUP_ID, UTILIZA_GRUPOS_ALUMNOS, REPORTE_CERTIFICADO_INSCRIPCION, EMAIL_ACTIVE, EVALUACION_ITB, REGISTRO_HISTORIA_NOTAS, NOTA_ESTADO_EN_CURSO, GENERAR_RUBROS_PAGO, GENERAR_RUBRO_INSCRIPCION, GENERAR_RUBRO_INSCRIPCION_MARGEN_DIAS, MODELO_EVALUACION, EVALUACION_IAVQ, EVALUACION_ITS, UTILIZA_NIVEL0_PROPEDEUTICO, TIPO_PERIODO_PROPEDEUTICO, NOTA_ESTADO_APROBADO, UTILIZA_FICHA_MEDICA, EVALUACION_TES, CORREO_INSTITUCIONAL, USA_CORREO_INSTITUCIONAL, INSCRIPCION_CONDUCCION,TIPO_AYUDA_FINANCIERA, NOTA_PARA_APROBAR
from sga.alu_malla import aprobadaAsignatura
from sga.commonviews import addUserData, ip_client_address
from sga.docentes import calculate_username
from sga.forms import PersonaForm, InscripcionForm, RecordAcademicoForm, HistoricoRecordAcademicoForm, HistoriaNivelesDeInscripcionForm, \
     CargarFotoForm, EmpresaInscripcionForm, EstudioInscripcionForm, DocumentoInscripcionForm, ActividadesInscripcionForm, \
     PadreClaveForm, ConvalidacionInscripcionForm, HistoricoNotasITBForm, GraduadoDatosForm, EgresadoForm, \
     InscripcionSenescytForm, RetiradoMatriculaForm, InscripcionCextForm, BecarioForm, InscripcionPracticaForm, \
     ObservacionInscripcionForm, ProcesoDobeForm,  ActivaInactivaUsuarioForm, MatriculaBecaForm, \
     EstudiantesXDesertarObservacionForm,RegistroLlamadasForm
from sga.models import Profesor, ProcesoDobe, Persona, Inscripcion, RecordAcademico, DocumentosDeInscripcion, HistoricoRecordAcademico, \
     HistoriaNivelesDeInscripcion, FotoPersona, EmpresaInscripcion, EstudioInscripcion, DocumentoInscripcion, Archivo, TipoArchivo, \
     Grupo, InscripcionGrupo, PerfilInscripcion, HistoricoNotasITB, PadreClave, Malla, ConvalidacionInscripcion, TipoEstado, \
     Rubro, RubroInscripcion, NivelMalla, EjeFormativo, AsignaturaMalla, Egresado, Asignatura, InscripcionSenescyt, RetiradoMatricula, \
     Carrera, Modalidad, Sesion, Especialidad, Materia, Nivel, TipoOtroRubro, Matricula, MateriaAsignada, RubroOtro, Graduado, \
     InscripcionBecario, InscripcionPracticas, ObservacionInscripcion, InscripcionConduccion, InactivaActivaUsr, EstudiantesXDesertar, \
     EstudiantesXDesertarObservacion,RegistroLlamadas,DetalleRegistroLlamadas
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

        elif action == 'reintegro':
            try:
                estudiantesxdesertar = EstudiantesXDesertar.objects.filter(pk=request.POST['id'])[:1].get()
                estudiantesxdesertar.reintegro=True
                estudiantesxdesertar.observacion=request.POST['obs']
                estudiantesxdesertar.save()
                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(estudiantesxdesertar).pk,
                    object_id       = estudiantesxdesertar.id,
                    object_repr     = force_str(estudiantesxdesertar),
                    action_flag     = DELETION,
                    change_message  = 'Reintegrado Estudiante por Desertar (' + client_address + ')' )
                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

        elif action=='addobservacion':
            estudiantesxdesertar = EstudiantesXDesertar.objects.filter(pk=request.POST['id'])[:1].get()
            f = EstudiantesXDesertarObservacionForm(request.POST)
            if f.is_valid():
                estudiantesxdesertarobs = EstudiantesXDesertarObservacion(estudiantesxdesertar=estudiantesxdesertar,
                                                     usuario=request.user,
                                                     fecha = datetime.now(),
                                                     observacion=f.cleaned_data['observaciones'])

                estudiantesxdesertarobs.save()

                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de ADICIONAR OBSERVACION
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(estudiantesxdesertarobs).pk,
                    object_id       = estudiantesxdesertarobs.id,
                    object_repr     = force_str(estudiantesxdesertarobs),
                    action_flag     = ADDITION,
                    change_message  = 'Observacion Adicionada a Posibles Desertores (' + client_address + ')' )

                return HttpResponseRedirect("/estudiantesxdesertar?action=observaciones&id="+str(estudiantesxdesertar.id))
            else:
                return HttpResponseRedirect("/estudiantesxdesertar?action=addobservaciones")

        elif action == 'add_registro':
            f = RegistroLlamadasForm(request.POST)
            try:
                inscripcion = Inscripcion.objects.get(pk=request.POST['id'])
                registro = RegistroLlamadas(inscripcion=inscripcion)
                registro.save()

                dr = DetalleRegistroLlamadas(registro=registro,
                                             respuesta=request.POST['registro'].upper(),
                                             fecha = datetime.now(),usuario=request.user)
                dr.save()

                mensaje = 'Adicionado'
                # Log Agregar registro de llamadas
                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(registro).pk,
                    object_id       = registro.id,
                    object_repr     = force_str(registro),
                    action_flag     = ADDITION,
                    change_message  = mensaje + " registro de llamadas" +  '(' + client_address + ')' )
                #return HttpResponseRedirect("/estudiantesxdesertar?action=registrollamadas")

                datos = {"result": "ok"}
                return HttpResponse(json.dumps(datos),content_type="application/json")
            except Exception as ex:
                pass
                datos = {"result": "bad"}
                return HttpResponse(json.dumps(datos),content_type="application/json")

        elif action == 'add_seguimiento':
            f = RegistroLlamadasForm(request.POST)
            #if f.is_valid():
            try:
                #inscripcion = Inscripcion.objects.get(pk=request.POST['id'])
                registro = RegistroLlamadas.objects.get(pk=request.POST['id'])

                dr = DetalleRegistroLlamadas(registro=registro,
                                             respuesta=request.POST['registro'].upper(),
                                             fecha = datetime.now(),usuario=request.user)
                dr.save()

                mensaje = 'Adicionado Seguimiento'
                # Log Agregar Seguimiento de llamadas
                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(registro).pk,
                    object_id       = registro.id,
                    object_repr     = force_str(registro),
                    action_flag     = ADDITION,
                    change_message  = mensaje + " Adicionado Seguimiento de llamadas" +  '(' + client_address + ')' )

                datos = {"result": "ok"}
                return HttpResponse(json.dumps(datos),content_type="application/json")
            except Exception as ex:
                pass
                datos = {"result": "bad"}
                return HttpResponse(json.dumps(datos),content_type="application/json")

    else:
        data = {'title': 'Listado de Desertores'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='observaciones':
                data['title'] = 'Observaciones de Posibles Desertores'
                estudiantesxdesertar = EstudiantesXDesertar.objects.get(pk=request.GET['id'])
                data['observaciones'] = estudiantesxdesertar.estudiantesxdesertarobservacion_set.all()
                data['estudiantesxdesertar'] = estudiantesxdesertar
                return render(request ,"estudiantesxdesertar/observaciones.html" ,  data)

            elif action=='addobservacion':
                data['title'] = 'Adicionar Observacion del Estudiante'
                estudiantesxdesertar = EstudiantesXDesertar.objects.get(pk=request.GET['id'])
                data['form'] = EstudiantesXDesertarObservacionForm()
                data['estudiantesxdesertar'] = estudiantesxdesertar
                return render(request ,"estudiantesxdesertar/addobservacion.html" ,  data)

            elif action=='asignatura':
                data = {}
                estudiantesxdesertar = EstudiantesXDesertar.objects.filter(pk=request.GET['asig'])[:1].get()
                p=estudiantesxdesertar.matricula.materia_asignada()

                data['estudiantesxdesertar']= estudiantesxdesertar.matricula.materia_asignada()
                data['notaaprobar']= NOTA_PARA_APROBAR
                # data['profesor']= estudiantesxdesertar.matricula.materia_asignada()


                return render(request ,"estudiantesxdesertar/asignaturadetalle.html" ,  data)


            elif action=='registrollamadas':
                data['registro'] = RegistroLlamadas.objects.all().order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')
                data['form'] = RegistroLlamadasForm(initial={"fecha":datetime.now().date()})
                if 'error' in request.GET:
                    data['error'] = "Debe Ingresar Estudiante"
                return render(request ,"estudiantesxdesertar/registrollamadas.html" ,  data)

            elif action == 'ver':
                data={}
                data['detalle'] = DetalleRegistroLlamadas.objects.filter(registro__id=request.GET['id'])
                return render(request ,"estudiantesxdesertar/detalleregistro.html" ,  data)

            return HttpResponseRedirect("/estudiantesxdesertar")

        else:
            search = None
            todos = None
            activos = None
            reintegrados = None
            nreintegrados = None

            if 's' in request.GET:
                search = request.GET['s']
            if 'r' in request.GET:
                reintegrados = request.GET['r']

            if 'nr' in request.GET:
                nreintegrados = request.GET['nr']
            if 't' in request.GET:
                todos = request.GET['t']
            if search:
                ss = search.split(' ')
                while '' in ss:
                    ss.remove('')
                if len(ss)==1:
                    estudiantesxdesertar = EstudiantesXDesertar.objects.filter(Q(inscripcion__persona__nombres__icontains=search) | Q(inscripcion__persona__apellido1__icontains=search) | Q(inscripcion__persona__apellido2__icontains=search) | Q(inscripcion__persona__cedula__icontains=search) | Q(inscripcion__persona__pasaporte__icontains=search)).order_by('inscripcion__persona__apellido1', 'inscripcion__persona__apellido2')
                else:
                    estudiantesxdesertar = EstudiantesXDesertar.objects.filter(Q(inscripcion__persona__apellido1__icontains=ss[0]) & Q(inscripcion__persona__apellido2__icontains=ss[1])).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')
            elif reintegrados:
                estudiantesxdesertar = EstudiantesXDesertar.objects.filter(reintegro=True).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')

            elif nreintegrados:
                estudiantesxdesertar = EstudiantesXDesertar.objects.filter(reintegro=False).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')
            else:
                estudiantesxdesertar = EstudiantesXDesertar.objects.filter().order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')


            paging = MiPaginador(estudiantesxdesertar, 30)
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
            data['reintegrados'] = reintegrados if reintegrados else ""
            data['nreintegrados'] = nreintegrados if nreintegrados else ""
            data['todos'] = todos if todos else ""
            data['form'] = EstudiantesXDesertarObservacionForm
            data['estudiantesxdesertar'] = page.object_list
            return render(request ,"estudiantesxdesertar/estudiantexdesertar.html" ,  data)
