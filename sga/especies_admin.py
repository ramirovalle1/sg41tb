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
from suds.client import Client
from decorators import secure_module
from settings import CENTRO_EXTERNO, RUBRO_TIPO_OTRO_MODULO_INTERNO, RUBRO_TIPO_OTRO_INSCRIPCION, DEFAULT_PASSWORD, PROFESORES_GROUP_ID, ALUMNOS_GROUP_ID, UTILIZA_GRUPOS_ALUMNOS, REPORTE_CERTIFICADO_INSCRIPCION, EMAIL_ACTIVE, EVALUACION_ITB, REGISTRO_HISTORIA_NOTAS, NOTA_ESTADO_EN_CURSO, GENERAR_RUBROS_PAGO, GENERAR_RUBRO_INSCRIPCION, GENERAR_RUBRO_INSCRIPCION_MARGEN_DIAS, MODELO_EVALUACION, EVALUACION_IAVQ, EVALUACION_ITS, UTILIZA_NIVEL0_PROPEDEUTICO, TIPO_PERIODO_PROPEDEUTICO, NOTA_ESTADO_APROBADO, UTILIZA_FICHA_MEDICA, EVALUACION_TES, CORREO_INSTITUCIONAL, USA_CORREO_INSTITUCIONAL, INSCRIPCION_CONDUCCION, NIVEL_MALLA_CERO, SISTEMAS_GROUP_ID
from sga.alu_malla import aprobadaAsignatura
from sga.commonviews import addUserData, ip_client_address
from sga.docentes import calculate_username
from sga.finanzas import convertir_fecha

from sga.forms import  TipoEspecieForm, DepartamentoGrupoForm, AsistAsuntoEstudiantForm, DepartamentoForm, GrupoUsuarioForm
from sga.models import Carrera,Malla, Matricula, TipoOtroRubro, Inscripcion, Rubro, RubroOtro, RubroMasivo, DetalleRubroMasivo, TipoCulminacionEstudio, TipoEspecieValorada, EspecieGrupo, DepartamentoGroup, Departamento, AsistenteDepartamento, Persona, CoordinacionDepartamento
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
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action=='add':
                if int(request.POST['edit'])== 0:
                    f = TipoEspecieForm(request.POST)
                else :
                    f = TipoEspecieForm(request.POST, instance=TipoEspecieValorada.objects.get(pk=request.POST['edit']))
                if f.is_valid():
                    try:
                        f.save()
                    except Exception as e:
                        print(e)

                return HttpResponseRedirect("/especies_admin")
            elif action == 'addgrupo':
                result = {}
                try:
                    tipoespecie = TipoEspecieValorada.objects.filter(pk=request.POST['tid'])[:1].get()
                    grupo = Departamento.objects.filter(pk=request.POST['g'])[:1].get()
                    todas = False

                    especieg = EspecieGrupo(tipoe = tipoespecie,
                                            departamento=grupo)
                    especieg.save()
                    result['result']  = "ok"
                    return HttpResponse(json.dumps(result), content_type="application/json")
                except Exception as e:
                    result['result']  = str(e)
                    return HttpResponse(json.dumps(result), content_type="application/json")

            elif action == 'eliminagrupo':
                result = {}
                try:
                    especiegrupo =EspecieGrupo.objects.filter(pk=request.POST['gid'])
                    especiegrupo.delete()
                    result['result']  = "ok"
                    return HttpResponse(json.dumps(result), content_type="application/json")
                except Exception as e:
                    result['result']  = str(e)
                    return HttpResponse(json.dumps(result), content_type="application/json")



            elif action == 'existe':
                try:
                    departamento=Departamento.objects.filter(pk=request.GET['departamento'])[:1].get()
                    if request.POST['editar'] == '0':
                        if AsistenteDepartamento.objects.filter(persona__id=request.POST['idasis'],departamento=departamento).exists():
                            return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                    else:
                        if AsistenteDepartamento.objects.filter(persona__id=request.POST['idasis'],departamento=departamento).exclude(pk=request.POST['editar']).exists():
                            return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
                except:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

            elif action == 'existegrupo':
                try:
                    if request.POST['editar'] == '0':
                        if DepartamentoGroup.objects.filter(group_id=request.POST['idasis']).exists():
                            return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                    else:
                        if DepartamentoGroup.objects.filter(group_id=request.POST['idasis']).exclude(pk=request.POST['editar']).exists():
                            return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
                except:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

            elif action == 'existecoordinacion':
                try:
                    if request.POST['editar'] == '0':
                        if CoordinacionDepartamento.objects.filter(departamento__id=request.GET['departamento'],coordinacion_id=request.POST['idasis']).exists():
                            return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                    else:
                        if CoordinacionDepartamento.objects.filter(departamento__id=request.GET['departamento'],coordinacion_id=request.POST['idasis']).exclude(pk=request.POST['editar']).exists():
                            return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
                except Exception as e:
                    print((e))
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
            elif action == 'addasistente':
                    departamento = Departamento.objects.filter(pk=request.POST['departamento'])[:1].get()
                    try:
                        if request.POST['editar'] == '0':
                            asistestudiant = AsistenteDepartamento(persona_id=request.POST['idsolici'],departamento=departamento)
                            asistestudiant.cantidad=0
                            asistestudiant.cantidadsol=0
                            mensaje = 'Ingreso asistente'
                        else:
                            asistestudiant = AsistenteDepartamento.objects.get(pk=request.POST['editar'])
                            asistestudiant.persona_id = request.POST['idsolici']

                            mensaje = 'Edicion asistente'
                        if request.POST['puedereasignar'] == '0':
                            asistestudiant.puedereasignar = False
                        else:
                            asistestudiant.puedereasignar = True
                        asistestudiant.save()


                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(asistestudiant).pk,
                            object_id       = asistestudiant.id,
                            object_repr     = force_str(asistestudiant),
                            action_flag     = ADDITION,
                            change_message  = mensaje+' (' + client_address + ')' )

                        return HttpResponseRedirect('/especies_admin?action=verasistentes&did='+str(departamento.id))
                    except Exception as ex:
                        return HttpResponseRedirect('/especies_admin?action=verasistentes&did='+str(departamento.id)+"&error=Error al ingresar el asistente vuelva a intentarlo")

            elif action == 'addgroup':
                departamento = Departamento.objects.filter(pk=request.POST['departamento'])[:1].get()
                try:
                    if request.POST['editar'] == '0':
                        asistestudiant = DepartamentoGroup(group_id=request.POST['idsolici'],departamento=departamento)
                        mensaje = 'Ingreso group'
                    else:
                        asistestudiant = DepartamentoGroup.objects.get(pk=request.POST['editar'])
                        asistestudiant.group_id = request.POST['idsolici']

                        mensaje = 'Edicion group'
                    asistestudiant.save()

                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(asistestudiant).pk,
                        object_id       = asistestudiant.id,
                        object_repr     = force_str(asistestudiant),
                        action_flag     = ADDITION,
                        change_message  = mensaje+' (' + client_address + ')' )

                    return HttpResponseRedirect('/especies_admin?action=vergruposusuario&did='+str(departamento.id))
                except Exception as ex:
                    return HttpResponseRedirect('/especies_admin?action=vergruposusuario&did='+str(departamento.id)+"&error=Error al ingresar el grupo vuelva a intentarlo")

            elif action == 'addcoordinacion':
                departamento = Departamento.objects.filter(pk=request.POST['departamento'])[:1].get()
                try:
                    if request.POST['editar'] == '0':
                        asistestudiant = CoordinacionDepartamento(coordinacion_id=request.POST['idsolici'],departamento=departamento)
                        mensaje = 'Ingreso Coordinacion Departamento'
                    else:
                        asistestudiant = CoordinacionDepartamento.objects.get(pk=request.POST['editar'])
                        asistestudiant.group_id = request.POST['idsolici']

                        mensaje = 'Edicion Coordinacion Departamento'
                    asistestudiant.save()

                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(asistestudiant).pk,
                        object_id       = asistestudiant.id,
                        object_repr     = force_str(asistestudiant),
                        action_flag     = ADDITION,
                        change_message  = mensaje+' (' + client_address + ')' )

                    return HttpResponseRedirect('/especies_admin?action=vercoordinacion&did='+str(departamento.id))
                except Exception as ex:
                    return HttpResponseRedirect('/especies_admin?action=vergruposusuario&did='+str(departamento.id)+"&error=Error al ingresar el grupo vuelva a intentarlo")
            elif action =='adddpto':
                if int(request.POST['editar'])== 0:
                    dpto = Departamento(descripcion=request.POST['nombre'])
                    dpto.save()
                    mensaje = 'Adcionado Departamento'
                else:
                    dpto = Departamento.objects.filter(pk=request.POST['editar'])[:1].get()
                    dpto.descripcion = request.POST['nombre']
                    dpto.save()
                    mensaje = 'Editado Departamento'
                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(dpto).pk,
                    object_id       = dpto.id,
                    object_repr     = force_str(dpto),
                    action_flag     = ADDITION,
                    change_message  = mensaje+' (' + client_address + ')' )

                return HttpResponseRedirect('/especies_admin?action=departamentos')
            return HttpResponseRedirect("/especies_admin")
        else:
            data = {'title': 'Listado de Tipos de Especies'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']

                if action=='add':
                    data['title'] = 'Nuevo Tipo'
                    form =TipoEspecieForm()
                    form.for_tipo()
                    data['form'] =form
                    data['titulo'] = 'Adicionar Nueva Tipo de Especie'
                    data['editar']  = 0
                    return render(request ,"especies_admin/add_especie.html" ,  data)

                elif action=='edit':
                    data['title'] = 'Editar Tipo '
                    tipoespecie = TipoEspecieValorada.objects.get(pk=request.GET['id'])
                    tipoespecief = TipoEspecieForm(instance=tipoespecie)
                    data['form'] = tipoespecief
                    data['titulo'] = 'Editar Tipo '
                    data['editar']  = tipoespecie.id
                    return render(request ,"especies_admin/add_especie.html" ,  data)

                elif action=='departamentos':
                    data['title'] = 'Grupos'
                    departamento = Departamento.objects.filter(controlespecies=True)
                    data['departamento'] = departamento
                    data['form'] = DepartamentoForm()
                    if 'error' in request.GET:
                        data['error'] = request.GET
                    return render(request ,"especies_admin/departamentos.html" ,  data)

                elif action == 'eliminarasistente':
                    try:
                        asistente =AsistenteDepartamento.objects.filter(pk=request.GET['aid'])[:1].get()
                        dpto=asistente.departamento.id
                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(asistente).pk,
                            object_id       = asistente.id,
                            object_repr     = force_str(asistente),
                            action_flag     = DELETION,
                            change_message  = 'Eliminado Asistente'+' (' + client_address + ')' )
                        asistente.activo=False
                        asistente.save()

                        return HttpResponseRedirect('/especies_admin?action=verasistentes&did='+str(dpto))

                    except Exception as e:
                        return HttpResponseRedirect('/especies_admin?action=verasistentes&did='+str(dpto)+"&error=Error al ingresar el asistente vuelva a intentarlo")
                elif action == 'eliminargroup':
                       try:
                            dptogroup =DepartamentoGroup.objects.filter(pk=request.GET['aid'])[:1].get()
                            dpto=dptogroup.departamento.id
                            client_address = ip_client_address(request)
                            LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(dptogroup).pk,
                                object_id       = dptogroup.id,
                                object_repr     = force_str(dptogroup),
                                action_flag     = DELETION,
                                change_message  = 'Eliminado Grupo'+' (' + client_address + ')' )
                            dptogroup.delete()

                            return HttpResponseRedirect('/especies_admin?action=vergruposusuario&did='+str(dpto))

                       except Exception as e:
                            return HttpResponseRedirect('/especies_admin?=action=vergruposusuario&error=Error... vuelva a intentarlo: ->'+ str(e))

                elif action == 'eliminardpto':
                    try:
                        departamento =Departamento.objects.filter(pk=request.GET['did'])[:1].get()
                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(departamento).pk,
                            object_id       = departamento.id,
                            object_repr     = force_str(departamento),
                            action_flag     = DELETION,
                            change_message  = 'Eliminado Departamento'+' (' + client_address + ')' )
                        departamento.delete()

                        return HttpResponseRedirect('/especies_admin?action=departamentos')

                    except Exception as e:
                        return HttpResponseRedirect('/especies_admin?=action=departamentos&error=Error... vuelva a intentarlo: ->'+ str(e))

                elif action == 'eliminacoor':
                    try:
                        coordinacion =CoordinacionDepartamento.objects.filter(pk=request.GET['aid'])[:1].get()
                        dpto=coordinacion.departamento.id
                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(coordinacion).pk,
                            object_id       = coordinacion.id,
                            object_repr     = force_str(coordinacion),
                            action_flag     = DELETION,
                            change_message  = 'Eliminada Coordinacion de Departamento'+' (' + client_address + ')' )
                        coordinacion.delete()

                        return HttpResponseRedirect('/especies_admin?action=vercoordinacion&did='+str(dpto))

                    except Exception as e:
                        return HttpResponseRedirect('/especies_admin?=action=vercoordinacion&error=Error... vuelva a intentarlo: ->'+ str(e))

                elif action == 'vergrupos':
                    try:
                        especie = TipoEspecieValorada.objects.get(pk=request.GET['tid'])
                        # if CarreraTipoCulminacion.objects.filter(carrera=carrera).exists():
                        data['grupos'] = EspecieGrupo.objects.filter(tipoe=especie)
                        return render(request ,"especies_admin/grupos.html" ,  data)
                        # else:
                        #     return render(request ,"inscripciones/panel.html" ,  data)
                    except:
                        return render(request ,"especies_admin/grupos.html" ,  data)

                elif action == 'verasistentes':
                    departamento = Departamento.objects.get(pk=request.GET['did'])
                    # if CarreraTipoCulminacion.objects.filter(carrera=carrera).exists():
                    data['asistentes'] = AsistenteDepartamento.objects.filter(departamento=departamento,activo=True)
                    data['departamento']=departamento
                    gruposexcluidos = [PROFESORES_GROUP_ID,ALUMNOS_GROUP_ID,SISTEMAS_GROUP_ID]
                    data['form']=AsistAsuntoEstudiantForm()
                    data['gruposexcluidos'] = list(Persona.objects.filter().exclude(usuario__groups__id__in=gruposexcluidos).order_by('apellido1').values_list('id', flat=True))
                    if 'error' in request.GET:
                        data['error'] = request.GET
                    return render(request ,"especies_admin/usuarios.html" ,  data)

                elif action == 'vergruposusuario':
                    departamento = Departamento.objects.get(pk=request.GET['did'])
                    departamentogrupo = DepartamentoGroup.objects.filter(departamento=departamento)
                    # if CarreraTipoCulminacion.objects.filter(carrera=carrera).exists():
                    data['departamentogrupo'] =departamentogrupo
                    data['departamento']=departamento
                    data['form']=GrupoUsuarioForm()
                    if 'error' in request.GET:
                        data['error'] = request.GET
                    return render(request ,"especies_admin/grupousuario.html" ,  data)

                elif action == 'vercoordinacion':
                    departamento = Departamento.objects.get(pk=request.GET['did'])
                    coordinacion = CoordinacionDepartamento.objects.filter(departamento=departamento)
                    # if CarreraTipoCulminacion.objects.filter(carrera=carrera).exists():
                    data['coordinacion'] =coordinacion
                    data['departamento']=departamento
                    data['form']=GrupoUsuarioForm()
                    if 'error' in request.GET:
                        data['error'] = request.GET
                    return render(request ,"especies_admin/coordinacion.html" ,  data)


            else:
                search = None
                todos = None

                if 's' in request.GET:
                    search = request.GET['s']
                if 't' in request.GET:
                    todos = request.GET['t']
                if search:
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')
                    tipoespecie = TipoEspecieValorada.objects.filter(nombre__icontains=search).order_by('-activa','nombre')
                else:
                     tipoespecie = TipoEspecieValorada.objects.all().order_by('-activa', 'nombre')
                if 'e' in request.GET:
                    tipoespecie = tipoespecie.filter(es_especie=True).order_by('-activa','nombre')
                    data['e'] = request.GET['e']

                if 'sol' in request.GET:
                    tipoespecie = tipoespecie.filter(es_especie=False).order_by('-activa','nombre')
                    data['sol'] = request.GET['sol']

                paging = MiPaginador(tipoespecie, 30)
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
                data['tipoespecie'] = page.object_list
                data['fecha'] = datetime.now().date()
                data['form'] = DepartamentoGrupoForm()
                return render(request ,"especies_admin/especies_admin.html" ,  data)

    except:
        return HttpResponseRedirect('/especies_admin')
