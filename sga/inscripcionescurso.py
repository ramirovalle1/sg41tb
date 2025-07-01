from datetime import datetime, timedelta
import json
import os
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
from settings import CENTRO_EXTERNO, RUBRO_TIPO_OTRO_MODULO_INTERNO, RUBRO_TIPO_OTRO_INSCRIPCION, DEFAULT_PASSWORD, PROFESORES_GROUP_ID, \
    ALUMNOS_GROUP_ID, UTILIZA_GRUPOS_ALUMNOS, REPORTE_CERTIFICADO_INSCRIPCION, EMAIL_ACTIVE, EVALUACION_ITB, REGISTRO_HISTORIA_NOTAS, \
    NOTA_ESTADO_EN_CURSO, GENERAR_RUBROS_PAGO, GENERAR_RUBRO_INSCRIPCION, GENERAR_RUBRO_INSCRIPCION_MARGEN_DIAS, MODELO_EVALUACION, \
    EVALUACION_IAVQ, EVALUACION_ITS, UTILIZA_NIVEL0_PROPEDEUTICO, TIPO_PERIODO_PROPEDEUTICO, NOTA_ESTADO_APROBADO, UTILIZA_FICHA_MEDICA,\
    EVALUACION_TES, CORREO_INSTITUCIONAL, USA_CORREO_INSTITUCIONAL, INSCRIPCION_CONDUCCION,PORCIENTO_NOTA1,PORCIENTO_NOTA2,PORCIENTO_NOTA3,\
    PORCIENTO_NOTA4,PORCIENTO_NOTA5,PORCIENTO_RECUPERACION,ASIGNATURA_PRACTICA_CONDUCCION, RUBRO_TIPO_CURSOS
from sga.alu_malla import aprobadaAsignatura
from sga.commonviews import addUserData, ip_client_address
from sga.docentes import calculate_username
from sga.forms import PersonaForm, InscripcionForm, RecordAcademicoForm, HistoricoRecordAcademicoForm, HistoriaNivelesDeInscripcionForm, CargarFotoForm, EmpresaInscripcionForm, EstudioInscripcionForm, DocumentoInscripcionForm, ActividadesInscripcionForm, PadreClaveForm, ConvalidacionInscripcionForm, HistoricoNotasITBForm, GraduadoDatosForm, EgresadoForm, InscripcionSenescytForm, RetiradoMatriculaForm, InscripcionCextForm, BecarioForm, InscripcionPracticaForm, ObservacionInscripcionForm, ProcesoDobeForm,  ActivaInactivaUsuarioForm, HistoricoNotasPracticaForm, InscripcionCursoForm, AsignarGrupoForm
from sga.models import Profesor, ProcesoDobe, Persona, Inscripcion, RecordAcademico, DocumentosDeInscripcion, HistoricoRecordAcademico, HistoriaNivelesDeInscripcion, \
    FotoPersona, EmpresaInscripcion, EstudioInscripcion, DocumentoInscripcion, Archivo, TipoArchivo, Grupo, InscripcionGrupo, PerfilInscripcion, HistoricoNotasITB,\
    PadreClave, Malla, ConvalidacionInscripcion, TipoEstado, Rubro, RubroInscripcion, NivelMalla, EjeFormativo, AsignaturaMalla, Egresado, Asignatura, InscripcionSenescyt, \
    RetiradoMatricula, Carrera, Modalidad, Sesion, Especialidad, Materia, Nivel, TipoOtroRubro, Matricula, MateriaAsignada, RubroOtro, Graduado, InscripcionBecario, \
    InscripcionPracticas, ObservacionInscripcion, InscripcionConduccion, InactivaActivaUsr,PreInscripcion,EstudianteXEgresar, Sexo,HistoricoNotasPractica,DetallePagos, GrupoCurso
from sga.tasks import gen_passwd
from sga.models import PagosCurso,Rubro,RubroOtro,TipoOtroRubro,InscripcionMateria,MateriaCurso

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
        try:
            if action=='add':
                data={}
                f = InscripcionCursoForm(request.POST)
                if f.is_valid():
                    if Persona.objects.filter(cedula = f.cleaned_data['cedula']).exists():
                        persona = Persona.objects.filter(cedula = f.cleaned_data['cedula'])[:1].get()

                    else:
                        persona = Persona(nombres=f.cleaned_data['nombres'],
                                            apellido1=f.cleaned_data['apellido1'],
                                            apellido2=f.cleaned_data['apellido2'],
                                            extranjero=f.cleaned_data['extranjero'],
                                            cedula=f.cleaned_data['cedula'],
                                            pasaporte=f.cleaned_data['pasaporte'],
                                            nacimiento=f.cleaned_data['nacimiento'],
                                            sexo=f.cleaned_data['sexo'],
                                            nacionalidad=f.cleaned_data['nacionalidad'],
                                            telefono=f.cleaned_data['telefono'],
                                            telefono_conv=f.cleaned_data['telefono_conv'],
                                            email=f.cleaned_data['email'])
                        persona.save()
                    carrera = Carrera.objects.get(pk=2)
                    modalidad = Modalidad.objects.get(pk=1)
                    sesion = Sesion.objects.get(pk=1)
                    if  Inscripcion.objects.filter(persona=persona).exists():
                       inscripcion= Inscripcion.objects.filter(persona=persona)[:1].get()
                       return HttpResponseRedirect("/inscripcionescurso?action=add&error=1")
                    else:
                        inscripcion = Inscripcion(persona=persona,
                                                  fecha=f.cleaned_data['fecha'],
                                                  carrera=carrera,
                                                  modalidad = modalidad,
                                                  sesion=sesion)

                        inscripcion.save()
                    if PagosCurso.objects.filter(grupocurso=f.cleaned_data['curso']).exists():
                        pagocurso = PagosCurso.objects.filter(grupocurso=f.cleaned_data['curso'])
                        hoy = datetime.now().date()
                        for p in pagocurso:
                            detallepagos = DetallePagos(inscripcion = inscripcion,
                                                        grupocurso=p.grupocurso,
                                                        pagocurso=p)
                            detallepagos.save()
                            if detallepagos.grupocurso.activo:
                                detallepagos.activo=True
                                detallepagos.save()
                                r1 = Rubro( fecha =hoy,
                                                            valor = p.valor,
                                                            inscripcion = inscripcion,
                                                            cancelado = False,
                                                            fechavence = p.fechavence)
                                r1.save()
                                r1otro = RubroOtro(rubro=r1,
                                                   tipo=TipoOtroRubro.objects.get(pk=RUBRO_TIPO_CURSOS),
                                                   descripcion= p.grupocurso.nombre + " - " + p.nombre)
                                r1otro.save()
                                detallepagos.rubro = r1
                                detallepagos.save()
                        if p.grupocurso.activo:
                            if MateriaCurso.objects.filter(grupocurso=detallepagos.grupocurso).exists():
                                for m in MateriaCurso.objects.filter(grupocurso=detallepagos.grupocurso):
                                            imateria = InscripcionMateria(inscripcion=inscripcion,
                                                                          materia=m,
                                                                          fecha=hoy)
                                            imateria.save()


                                    #Obtain client ip address
                        client_address = ip_client_address(request)

                            # Log de ADICIONAR INSCRIPCION
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(inscripcion).pk,
                            object_id       = inscripcion.id,
                            object_repr     = force_str(inscripcion),
                            action_flag     = ADDITION,
                            change_message  = 'Adicionada Inscripcion a curso '+ str(p.grupocurso.nombre)  + '(' + client_address + ')' )
                        data['detallepago'] = DetallePagos.objects.filter(inscripcion=inscripcion , grupocurso=p.grupocurso)
                        data['pagocurso']=pagocurso[:1]
                        data['inscripcion']=inscripcion

                        return HttpResponseRedirect("/inscripcionescurso?action=pagoscurso&id="+str(inscripcion.id))
                        # return render(request ,"inscripcionescurso/pagoscurso.html" ,  data)
                else:
                    return HttpResponseRedirect("/inscripciones?action=add")
            elif action=='buscainscripcion':
                if Inscripcion.objects.filter(persona__cedula=request.POST['num']).exists():
                    persona = Inscripcion.objects.filter(persona__cedula=request.POST['num'])[:1].get()
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                else:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
            elif action == 'agregar':
                if Inscripcion.objects.filter(pk=request.POST['id']).exists():
                    inscripcion = Inscripcion.objects.filter(pk=request.POST['id'])[:1].get()
                    f = AsignarGrupoForm(request.POST)
                    if f.is_valid():
                        if PagosCurso.objects.filter(grupocurso=f.cleaned_data['grupo']).exists():
                            pagocurso = PagosCurso.objects.filter(grupocurso=f.cleaned_data['grupo'])
                            hoy = datetime.now().date()
                            for p in pagocurso:
                                detallepagos = DetallePagos(inscripcion = inscripcion,
                                                            grupocurso=p.grupocurso,
                                                            pagocurso=p)
                                detallepagos.save()
                                if detallepagos.grupocurso.activo:
                                    detallepagos.activo=True
                                    detallepagos.save()
                                    r1 = Rubro( fecha =hoy,
                                                                valor = p.valor,
                                                                inscripcion = inscripcion,
                                                                cancelado = False,
                                                                fechavence = p.fechavence)
                                    r1.save()
                                    r1otro = RubroOtro(rubro=r1,
                                                       tipo=TipoOtroRubro.objects.get(pk=RUBRO_TIPO_CURSOS),
                                                       descripcion= p.grupocurso.nombre + " - " + p.nombre)
                                    r1otro.save()
                                    detallepagos.rubro = r1
                                    detallepagos.save()

                        if detallepagos.grupocurso.activo:
                            for m in MateriaCurso.objects.filter(grupocurso=detallepagos.grupocurso):
                                        imateria = InscripcionMateria(inscripcion=inscripcion,
                                                                      materia=m,
                                                                      fecha=hoy)
                                        imateria.save()

                            client_address = ip_client_address(request)

                                # Log de ADICIONAR INSCRIPCION
                            LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(inscripcion).pk,
                                object_id       = inscripcion.id,
                                object_repr     = force_str(inscripcion),
                                action_flag     = ADDITION,
                                change_message  = 'Adicionado Curso ' +str(p.grupocurso.nombre)  + ' a ' + str(inscripcion) + '(' + client_address + ')' )
                            data ={}
                            data['detallepago'] = DetallePagos.objects.filter(inscripcion=inscripcion , grupocurso=p.grupocurso)
                            data['pagocurso']=pagocurso[:1]
                            data['inscripcion']=inscripcion

                            return HttpResponseRedirect("/inscripcionescurso?action=pagoscurso&id="+str(inscripcion.id))


        except Exception as ex:
            return HttpResponseRedirect("/inscripcionescurso")
    else:
        data = {'title': 'Listado de Inscripciones'}
        addUserData(request,data)
        try:
            if 'action' in request.GET:
                action = request.GET['action']
                if action=='activation':
                    pass
                    # return HttpResponseRedirect("/docentes")

                elif action=='add':
                    data['title'] = 'Nueva Inscripcion de Alumno'
                    if 'error' in request.GET:
                        data['error'] = request.GET['error']
                    insf = InscripcionCursoForm(initial={'fecha': datetime.now()})
                    data['form'] = insf
                    return render(request ,"inscripcionescurso/adicionarbs.html" ,  data)

                elif action=='edit':
                    if 'graduado' in request.GET:
                        data['graduado'] = request.GET['graduado']

                    inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                    if INSCRIPCION_CONDUCCION:
                        documentos = inscripcion.documentos_entregados_conduccion()
                        initial = model_to_dict(inscripcion)
                        initial.update(model_to_dict(inscripcion.persona))
                        initial.update({'copia_cedula': documentos.copia_cedula, 'titulo': documentos.titulo,
                                        'fotos2': documentos.fotos2, 'licencia': documentos.licencia,
                                        'votacion': documentos.votacion, 'carnetsangre': documentos.carnetsangre,
                                        'ex_psicologico': documentos.ex_psicologico,
                                        'val_psicosometrica': documentos.val_psicosometrica,
                                        'val_medica': documentos.val_medica})

                    else:

                        documentos = inscripcion.documentos_entregados()
                        initial = model_to_dict(inscripcion)
                        initial.update(model_to_dict(inscripcion.persona))
                        initial.update({'cedula2': documentos.cedula, 'titulo': documentos.titulo,
                                        'acta': documentos.acta, 'votacion': documentos.votacion,
                                        'actaconv': documentos.actaconv, 'partida_nac': documentos.partida_nac,
                                        'fotos': documentos.fotos})

                    if UTILIZA_GRUPOS_ALUMNOS and inscripcion.inscripciongrupo_set.exists():
                        initial.update({'grupo': inscripcion.grupo})
                    data['grupos_abiertos'] = Grupo.objects.all()
                    data['utiliza_grupos_alumnos'] = UTILIZA_GRUPOS_ALUMNOS

                    insf = InscripcionForm(initial=initial)

                    data['form'] = insf
                    data['inscripcion'] = inscripcion
                    data['inscripcion_conduccion'] = INSCRIPCION_CONDUCCION
                    data['matriculado'] = inscripcion.matriculado()
                    return render(request ,"inscripciones/editarbs.html" ,  data)

                elif action=='pagoscurso':
                    if Inscripcion.objects.filter(pk=request.GET['id']).exists():
                        inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                        pagos = DetallePagos.objects.filter(inscripcion=inscripcion)
                        p = DetallePagos.objects.filter(inscripcion=inscripcion)[:1].get()

                        data['detallepago'] = pagos
                        data['grupocurso'] =p.pagocurso.grupocurso
                        data['inscripcion'] = inscripcion

                        return render(request ,"inscripcionescurso/pagoscurso.html" ,  data)

                elif action=='agregar':
                    if Inscripcion.objects.filter(pk=request.GET['id']).exists():
                        data['inscripcion'] = Inscripcion.objects.get(pk=request.GET['id'])
                        i = Inscripcion.objects.get(pk=request.GET['id'])
                        form = AsignarGrupoForm()
                        form.verifica_grupo(i)
                        data['form'] =form

                        return render(request ,"inscripcionescurso/asignarcurso.html" ,  data)
                elif action=='vercurso':
                    data={}
                    detalle = DetallePagos.objects.filter(inscripcion__id=request.GET['id']).values('grupocurso')
                    data['cursos'] =  GrupoCurso.objects.filter(id__in = detalle)
                    return render(request ,"inscripcionescurso/vercursos.html" ,  data)

                elif action=='agregarpago':
                    pagos = DetallePagos.objects.get(pk=request.GET['id'])
                    pagos.activo=True
                    pagos.save()
                    hoy = datetime.now().date()
                    r1 = Rubro( fecha =hoy,
                                valor = pagos.pagocurso.valor,
                                inscripcion = request.GET['i'],
                                cancelado = False,
                                fechavence = pagos.pagocurso.fechavence)
                    r1.save()
                    r1otro = RubroOtro(rubro=r1,
                                       tipo=TipoOtroRubro.objects.get(pk=RUBRO_TIPO_CURSOS),
                                       descripcion= pagos.grupocurso.nombre + " - " + pagos.pagocurso.nombre)
                    r1otro.save()

                    # for m in MateriaCurso.objects.filter(grupocurso=detallepagos.grupocurso):
                    #             imateria = InscripcionMateria(inscripcion=inscripcion,
                    #                                           materia=m,
                    #                                           fecha=hoy)
                    #             imateria.save()


                    #Record e Historico estudiantes
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
                        i = DetallePagos.objects.filter(Q(inscripcion__persona__nombres__icontains=search) | Q(inscripcion__persona__apellido1__icontains=search) | Q(inscripcion__persona__apellido2__icontains=search) | Q(inscripcion__persona__cedula__icontains=search) | Q(inscripcion__persona__pasaporte__icontains=search)).order_by('inscripcion__persona__apellido1').values('inscripcion').distinct('inscripcion')
                        inscripcionescurso = Inscripcion.objects.filter(pk__in=i).order_by('persona__apellido1')
                    else:
                        i = DetallePagos.objects.filter(Q(inscripcion__persona__nombres__icontains=search) | Q(inscripcion__persona__apellido1__icontains=search) | Q(inscripcion__persona__apellido2__icontains=search) | Q(inscripcion__persona__cedula__icontains=search) | Q(inscripcion__persona__pasaporte__icontains=search)).order_by('inscripcion__persona__apellido1').values('inscripcion').distinct('inscripcion')
                        inscripcionescurso = Inscripcion.objects.filter(pk__in=i).order_by('persona__apellido1')


                if todos:
                    i = DetallePagos.objects.filter(Q(inscripcion__persona__nombres__icontains=search) | Q(inscripcion__persona__apellido1__icontains=search) | Q(inscripcion__persona__apellido2__icontains=search) | Q(inscripcion__persona__cedula__icontains=search) | Q(inscripcion__persona__pasaporte__icontains=search)).order_by('inscripcion__persona__apellido1').values('inscripcion').distinct('inscripcion')
                    inscripcionescurso = Inscripcion.objects.filter(pk__in=i).order_by('persona__apellido1')

                if CENTRO_EXTERNO and not ('s' in request.GET):
                    i = DetallePagos.objects.all().values('inscripcion').distinct('inscripcion')
                    inscripcionescurso = Inscripcion.objects.filter(pk__in=i).order_by('persona__apellido1')

                paging = MiPaginador(inscripcionescurso, 30)
                p = 1
                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                        # if band==0:
                        #     inscripciones = Inscripcion.objects.all().order_by('persona__apellido1')
                        paging = MiPaginador(inscripcionescurso, 30)
                    page = paging.page(p)
                except Exception as ex:
                    page = paging.page(1)

                data['paging'] = paging
                data['rangospaging'] = paging.rangos_paginado(p)
                data['page'] = page
                data['search'] = search if search else ""
                data['todos'] = todos if todos else ""
                data['activos'] = activos if activos else ""
                data['inactivos'] = inactivos if inactivos else ""
                data['inscripcionescurso'] = page.object_list
                data['utiliza_grupos_alumnos'] = UTILIZA_GRUPOS_ALUMNOS
                data['reporte_ficha_id'] = REPORTE_CERTIFICADO_INSCRIPCION
                data['clave'] = DEFAULT_PASSWORD
                data['usafichamedica'] = UTILIZA_FICHA_MEDICA
                data['centroexterno'] = CENTRO_EXTERNO
                data['matriculalibre'] = MODELO_EVALUACION==EVALUACION_TES
                data['grupos'] = Grupo.objects.all().order_by('nombre')
                data['inscripcion_conduccion'] = INSCRIPCION_CONDUCCION

                return render(request ,"inscripcionescurso/inscripcionescurso.html" ,  data)

        except:
            return HttpResponseRedirect("/inscripcionescurso")