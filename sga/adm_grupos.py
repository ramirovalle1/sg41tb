from datetime import datetime
from datetime import datetime
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models.query_utils import Q
from django.forms.models import model_to_dict
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
from decorators import secure_module
from settings import DEFAULT_PASSWORD, PROFESORES_GROUP_ID, ALUMNOS_GROUP_ID, NIVEL_MALLA_CERO, UTILIZA_NIVEL0_PROPEDEUTICO, REPORTE_ALUMNOS_INSCRITOS, TIPO_PERIODO_PROPEDEUTICO, TIPO_PERIODO_REGULAR
from sga.commonviews import addUserData, ip_client_address
from sga.forms import PersonaForm, InscripcionForm, RecordAcademicoForm, HistoricoRecordAcademicoForm, GraduadoForm, SeguimientoGraduadoForm, GrupoForm, GrupoEditForm, PrecioCarreraGrupoForm, UnirGruposForm, GrupoPropedeuticoForm
from sga.models import Profesor, Persona, Inscripcion, RecordAcademico, DocumentosDeInscripcion, HistoricoRecordAcademico, Graduado, SeguimientoGraduado, Grupo, Nivel, NivelMalla, Malla, Materia, Asignatura, AsignaturaNivelacionCarrera, GrupoCoordinadorCarrera, PrecioCarreraGrupo, Periodo,AsignaturaMalla, MatriculaTutor
from sga.reportes import elimina_tildes


@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    if request.method=='POST':
        action = request.POST['action']
        if action=='add':
            try:
                periodo = Periodo.objects.get(pk=request.POST['periodo'])
                if periodo.tipo_id==TIPO_PERIODO_PROPEDEUTICO:
                    f = GrupoPropedeuticoForm(request.POST)
                if periodo.tipo_id==TIPO_PERIODO_REGULAR:
                    f = GrupoForm(request.POST)
                if f.is_valid():
                    carrera = f.cleaned_data['carrera']
                    sesion = f.cleaned_data['sesion']
                    sede = f.cleaned_data['sede']
                    periodo = f.cleaned_data['periodo']
                    if 'convenio' in f.cleaned_data:
                        convenio = f.cleaned_data['convenio']
                    else:
                        convenio =None

                    if 'convenioempresa' in f.cleaned_data:
                        convempresa=f.cleaned_data['convenioempresa']
                    else:
                        convempresa=None

                    if 'online' in f.cleaned_data:
                        online=f.cleaned_data['online']
                    else:
                        online=None

                    descuento = f.cleaned_data['descuento']

                    grupo = Grupo(carrera=carrera,
                                modalidad=f.cleaned_data['modalidad'],
                                sesion=sesion,
                                nombre=f.cleaned_data['nombre'],
                                sede=sede,
                                inicio=f.cleaned_data['inicio'],
                                fin=f.cleaned_data['fin'],
                                capacidad=f.cleaned_data['capacidad'],
                                observaciones=f.cleaned_data['observaciones'],
                                abierto=True,
                                convenio=convenio,municipio=False,empresaconvenio=convempresa,descuento=descuento, online = online)
                    grupo.save()

                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de ADICIONAR GRUPO
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(grupo).pk,
                        object_id       = grupo.id,
                        object_repr     = force_str(grupo),
                        action_flag     = ADDITION,
                        change_message  = 'Adicionado Grupo (' + client_address + ')'  )

                    if UTILIZA_NIVEL0_PROPEDEUTICO:
                        nivel = Nivel(carrera=carrera,
                                    periodo=periodo,
                                    sede=sede,
                                    sesion=sesion,
                                    nivelmalla = NivelMalla.objects.get(pk=NIVEL_MALLA_CERO),
                                    malla = Malla.objects.get(carrera=carrera, vigente=True),
                                    paralelo = grupo.nombre,
                                    grupo = grupo,
                                    inicio = periodo.inicio,
                                    fin = periodo.fin
                                    )
                        nivel.save()


                        for asignaturanivelacion in AsignaturaMalla.objects.filter(malla=nivel.malla,nivelmalla__id=NIVEL_MALLA_CERO,malla__carrera=nivel.carrera):
                            m = Materia(asignatura=asignaturanivelacion.asignatura,
                                        nivel=nivel,
                                        horas=asignaturanivelacion.horas,
                                        creditos=asignaturanivelacion.creditos,
                                        rectora=False,
                                        identificacion='',
                                        inicio=periodo.inicio,
                                        fin=periodo.fin)
                            m.save()

                else:
                    return HttpResponseRedirect("/adm_grupos?action=add")
            except Exception as ex:
                print(ex)
                return HttpResponseRedirect("/adm_grupos?info="+str(ex))

        elif action=='edit':
            grupo = Grupo.objects.get(pk=request.POST['id'])
            f = GrupoEditForm(request.POST)
            if f.is_valid():

                grupo.nombre = f.cleaned_data['nombre']
                grupo.inicio=f.cleaned_data['inicio']
                grupo.fin=f.cleaned_data['fin']
                grupo.capacidad=f.cleaned_data['capacidad']
                grupo.observaciones=f.cleaned_data['observaciones']
                grupo.descuento = f.cleaned_data['descuento']

                if grupo.esta_abierto():
                    grupo.abierto = True
                else:
                    grupo.abierto = False

                if 'convenioempresa' in f.cleaned_data:
                    convempresa=f.cleaned_data['convenioempresa']
                else:
                    convempresa=None

                if 'carrera' in f.cleaned_data:
                    carrera=f.cleaned_data['carrera']
                    # Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de EDITAR GRUPO
                    LogEntry.objects.log_action(
                        user_id=request.user.pk,
                        content_type_id=ContentType.objects.get_for_model(grupo).pk,
                        object_id=grupo.id,
                        object_repr=force_str(grupo.carrera),
                        action_flag=CHANGE,
                        change_message='Modificada Carrera al Editar Grupo  '+ elimina_tildes(grupo.nombre) +' ( ' + client_address + ')')
                else:
                    carrera=grupo.carrera
                if 'online' in f.cleaned_data:
                    online=f.cleaned_data['online']
                else:
                    online=None

                grupo.empresaconvenio=convempresa
                grupo.online = online
                grupo.carrera = carrera
                grupo.save()
                # if UTILIZA_NIVEL0_PROPEDEUTICO:
                if Nivel.objects.filter(grupo=grupo,nivelmalla__id = NIVEL_MALLA_CERO).count() == 1:
                    nivel = Nivel.objects.filter(grupo=grupo,nivelmalla__id = NIVEL_MALLA_CERO)[:1].get()
                    grupo.sede=f.cleaned_data['sede']
                    grupo.save()
                    nivel.sede = grupo.sede
                    nivel.save()


                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de EDITAR GRUPO
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(grupo).pk,
                    object_id       = grupo.id,
                    object_repr     = force_str(grupo),
                    action_flag     = CHANGE,
                    change_message  = 'Modificado Grupo (' + client_address + ')' )

                """Para cuando se quiera editar el nivel 0 de un grupo, si este tiene alguno asociado"""
                if UTILIZA_NIVEL0_PROPEDEUTICO:
                    try:
                        nivel = grupo.nivel_set.all().get()
                        if nivel:
                           nivel.paralelo = grupo.nombre
                           nivel.inicio = grupo.inicio
                           nivel.fin = grupo.fin
                           nivel.save()
                    except :
                        pass

            else:
                return HttpResponseRedirect("/adm_grupos?action=edit&id="+str(request.POST['id']))

        elif action=='merge':
            f = UnirGruposForm(request.POST)
            if f.is_valid():
                fuente = f.cleaned_data['fuente']
                destino = f.cleaned_data['destino']
                for ig in fuente.inscripciongrupo_set.all():
                    ig.grupo = destino
                    ig.save()
                fuente.cerrado = True
                fuente.fechacierre = datetime.now()
                fuente.save()

                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de UNIFICAR GRUPOS
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(destino).pk,
                    object_id       = destino.id,
                    object_repr     = force_str(destino),
                    action_flag     = CHANGE,
                    change_message  = 'Unificacion Grupos desde: ' + fuente.nombre + ' (' + client_address + ')')

                return HttpResponseRedirect("/adm_grupos")
            else:
                return HttpResponseRedirect("/adm_grupos?action=merge&error="+str(f.errors))


        elif action=='del':
            grupo = Grupo.objects.get(pk=request.POST['id'])
            if grupo.abierto and not grupo.miembros().count():
                precio=PrecioCarreraGrupo.objects.get(grupo=grupo)
                precio.delete()
                grupo.delete()

        elif action=='precios':
            grupo = Grupo.objects.get(pk=request.POST['id'])
            precio = PrecioCarreraGrupo.objects.get(grupo=grupo)
            f = PrecioCarreraGrupoForm(request.POST)

            if f.is_valid():

                precio.precioinscripcion=f.cleaned_data['precioinscripcion']
                precio.preciomatricula=f.cleaned_data['preciomatricula']
                precio.precioperiodo=f.cleaned_data['precioperiodo']
                precio.cuotas=f.cleaned_data['cuotas']
                precio.save()

                # Generacion de Rubros automaticas en NIVEL PROPEDEUTICO
                if UTILIZA_NIVEL0_PROPEDEUTICO:
                    if grupo.nivel_set.filter(periodo__tipo__id=TIPO_PERIODO_PROPEDEUTICO, cerrado=False).exists():
                        nivel = grupo.nivel_set.filter(periodo__tipo__id=TIPO_PERIODO_PROPEDEUTICO, cerrado=False)[:1].get()
                        nivel.crea_cronograma_pagos()
            else:
                return HttpResponseRedirect("/adm_grupos?action=precios")

        return HttpResponseRedirect("/adm_grupos")
    else:
        data = {'title': 'Listado de Grupos'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']

            if action=='add':
                data['title'] = 'Adicionar Grupo'
                periodo = request.session['periodo']
                if periodo.tipo_id==TIPO_PERIODO_PROPEDEUTICO:
                    data['form'] = GrupoPropedeuticoForm(initial={'inicio': datetime.now(), 'fin': datetime.now()})
                if periodo.tipo_id==TIPO_PERIODO_REGULAR:
                    data['form'] = GrupoForm(initial={'inicio': datetime.now(), 'fin': datetime.now()})
                data['periodo'] = periodo
                return render(request ,"adm_grupos/adicionarbs.html" ,  data)

            elif action=='edit':
                data['title'] = 'Editar Grupo'
                grupo = Grupo.objects.get(pk=request.GET['id'])
                initial = model_to_dict(grupo)
                form = GrupoEditForm(initial=initial)
                data['form'] = form
                data['grupo'] = grupo
                return render(request ,"adm_grupos/editarbs.html" ,  data)
            elif action=='merge':
                data['title'] = 'Unir Grupos'
                data['form'] = UnirGruposForm()
                return render(request ,"adm_grupos/unirgruposbs.html" ,  data)
            elif action=='del':
                data['title'] = 'Borrar Grupo'
                data['grupo'] = Grupo.objects.get(pk=request.GET['id'])
                return render(request ,"adm_grupos/borrarbs.html" ,  data)
            elif action=='precios':
                data['title'] = 'Crear Precios de Rubros del Grupo'
                grupo = Grupo.objects.get(pk=request.GET['id'])
                precios = PrecioCarreraGrupo.objects.get(grupo=grupo)
                initial = model_to_dict(precios)
                data['form'] = PrecioCarreraGrupoForm(initial=initial)
                data['grupo'] = grupo
                return render(request ,"adm_grupos/preciosbs.html" ,  data)

        else:
            search = None
            total_grupo = 0


            if 'a' in request.GET:
                grupos = Grupo.objects.filter(carrera__grupocoordinadorcarrera__group__in=data['persona'].usuario.groups.all(),abierto=True).order_by('nombre').distinct()
                data['abierto'] = 1

            elif 'c' in request.GET:
                grupos = Grupo.objects.filter(carrera__grupocoordinadorcarrera__group__in=data['persona'].usuario.groups.all(),abierto=False).order_by('nombre').distinct()
                data['cerrado'] = 1

            elif 's' in request.GET:
                search = request.GET['s']
                grupos = Grupo.objects.filter(carrera__grupocoordinadorcarrera__group__in=data['persona'].usuario.groups.all()).filter(Q(nombre__icontains=search) | Q(carrera__nombre__icontains=search) | Q(modalidad__nombre__icontains=search) | Q(sesion__nombre__icontains=search)).order_by('nombre').distinct()
                for g in grupos:
                    total_grupo += g.miembros().count()
                data['total_grupo'] = total_grupo
            else:
                grupos = Grupo.objects.filter(carrera__grupocoordinadorcarrera__group__in=data['persona'].usuario.groups.all()).order_by('-nombre').distinct()
                data['abierto'] = 1
                data['cerrado'] = 1

            paging = Paginator(grupos, 50)
            p=1
            try:
                if 'page' in request.GET:
                    p = int(request.GET['page'])
                page = paging.page(p)
            except:
                page = paging.page(1)

            data['paging'] = paging
            data['page'] = page
            data['search'] = search if search else ""
            data['grupos'] = page.object_list
            data['reporte_inscritos_id'] = REPORTE_ALUMNOS_INSCRITOS
            return render(request ,"adm_grupos/gruposbs.html" ,  data)
