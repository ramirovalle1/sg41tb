import json
from django.contrib.admin.models import LogEntry, ADDITION,CHANGE
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_str
from decorators import secure_module
from settings import TIPO_PERIODO_REGULAR
from sga.models import TipoMedicamento,TipoOficio,Periodo
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.core.paginator import Paginator
from sga.commonviews import addUserData, log_audit_action
from django.template import RequestContext
from sga.forms import TipoMedicamentoForm, TipoOficioForm, PeriodoForm
from datetime import datetime
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse

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
        if request.method=='POST':
            action = request.POST['action']
            if action == 'editperiodo':
                with transaction.atomic():
                    errors_frm = {}
                    try:
                        from .forms import PeriodoActForm
                        form = PeriodoActForm(request.POST)
                        if not form.is_valid():
                            errors_frm = form.toArray()
                            raise NameError("Debe ingresar la información en todos los campos.")
                        try:
                            periodo = Periodo.objects.get(pk=int(request.POST['id']))
                        except ObjectDoesNotExist:
                            raise NameError(u"No se encontro el periodo a editar")

                        periodo.nombre = form.cleaned_data['nombre']
                        periodo.inicio = form.cleaned_data['inicio']
                        periodo.fin = form.cleaned_data['fin']
                        periodo.tipo = form.cleaned_data['tipo']
                        periodo.accion = form.cleaned_data['activo']
                        periodo.save()
                        log_audit_action(request, periodo, 'Edición de Periodo')

                        return JsonResponse({"isSuccess": True, "message": u"Se guardo correctamente el periodo"})
                    except Exception as ex:
                        transaction.set_rollback(True)
                        return JsonResponse(
                            {"isSuccess": False, "message": u"Error al guardar los datos: %s" % ex, 'form': errors_frm})

            elif action == 'changeEstadoPeriodo':
                with transaction.atomic():
                    try:
                        id = request.POST.get('id', 0)
                        try:
                            periodo_estado = Periodo.objects.get(pk=id)
                        except ObjectDoesNotExist:
                            raise NameError(u"No se encontro el periodo")
                        value = request.POST.get('value', None)
                        if not value or not value in ('activate', 'deactivate'):
                            raise NameError(u"Operación no encontrada")
                        estado = False
                        menssage = "Se inactivo el periodo correctamente"
                        if value == 'activate':
                            estado = True
                            menssage = "Se activo el periodo correctamente"
                        periodo_estado.activo = estado
                        periodo_estado.save()
                        log_audit_action(request, periodo_estado, 'Cambio de estado de periodo')
                        return JsonResponse({"isSuccess": True, "message": menssage})
                    except Exception as ex:
                        transaction.set_rollback(True)
                        return JsonResponse({"isSuccess": False, "message": u"Error al procesar los datos: %s" % ex})


            elif action == 'addcomponenteevaluacion':
                try:
                    from .forms import EvaluacionComponentePeriodoFrom
                    from .models import EvaluacionComponentePeriodo
                    form = EvaluacionComponentePeriodoFrom(request.POST)
                    if not form.is_valid():
                        errors_frm = form.toArray()
                        raise NameError("Debe ingresar la información en todos los campos.")
                    id = request.POST.get("id", None)
                    if not id:
                        raise NameError("No se encontro el código del periodo")
                    try:
                        periodo = Periodo.objects.get(id=id)
                    except ObjectDoesNotExist:
                        raise NameError(u"No se encontro el periodo")
                    if EvaluacionComponentePeriodo.objects.values("id").filter(periodo_id=id, componente=form.cleaned_data['componente'], parcial=form.cleaned_data['parcial']).exists():
                        return JsonResponse({"isSuccess": False, "message": u"El registro ya existe"})
                    with transaction.atomic():
                        evaluacionComponentePeriodo = EvaluacionComponentePeriodo(
                            periodo_id=id,
                            componente=form.cleaned_data['componente'],
                            parcial=form.cleaned_data['parcial']
                        )
                        evaluacionComponentePeriodo.save()
                        log_audit_action(request, evaluacionComponentePeriodo, 'Adicionó un nuevo componente al periodo %s' % periodo )
                        return JsonResponse({"isSuccess": True, "message": u"El componente se creó correctamente"})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse(
                        {"isSuccess": False, "message": u"Error al eliminar el recurso link: %s" % ex})

            elif action == 'editcomponenteevaluacion':
                try:
                    from .forms import EvaluacionComponentePeriodoFrom
                    from .models import EvaluacionComponentePeriodo
                    form = EvaluacionComponentePeriodoFrom(request.POST)
                    if not form.is_valid():
                        errors_frm = form.toArray()
                        raise NameError("Debe ingresar la información en todos los campos.")
                    id = request.POST.get("id", None)
                    if not id:
                        raise NameError("No se encontro el código del periodo")
                    try:
                        evaluacionComponentePeriodo = EvaluacionComponentePeriodo.objects.get(id=id)
                    except ObjectDoesNotExist:
                        raise NameError(u"No se encontro el periodo")
                    if EvaluacionComponentePeriodo.objects.values("id").filter(periodo_id=id,
                                                                               componente=form.cleaned_data['componente'],
                                                                               parcial=form.cleaned_data[
                                                                                   'parcial']).exclude(id=evaluacionComponentePeriodo.id).exists():
                        return JsonResponse({"isSuccess": False, "message": u"El registro ya existe"})
                    with transaction.atomic():
                        evaluacionComponentePeriodo.componente=form.cleaned_data['componente']
                        evaluacionComponentePeriodo.parcial=form.cleaned_data['parcial']
                        evaluacionComponentePeriodo.save()
                        log_audit_action(request, evaluacionComponentePeriodo,
                                         'Editó el componente %s' % evaluacionComponentePeriodo)
                        return JsonResponse({"isSuccess": True, "message": u"El componente se modificó correctamente"})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse(
                        {"isSuccess": False, "message": u"Error al inesperado al guardar los datos %s" % ex})

            elif action == 'delcomponenteevaluacion':
                try:
                    from .models import EvaluacionComponentePeriodo
                    try:
                        evaluacionComponentePeriodo = EvaluacionComponentePeriodo.objects.get(pk=request.POST['id'])
                    except ObjectDoesNotExist:
                        raise NameError(u"No se encontro el componente")
                    if not evaluacionComponentePeriodo.en_uso():
                        return JsonResponse({"isSuccess": True, "message": u"El componente se encuentra en uso"})
                    with transaction.atomic():
                        evaluacionComponentePeriodo.delete()
                        return JsonResponse({"isSuccess": True, "message": u"El componente se eliminó correctamente"})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse(
                    {"isSuccess": False, "message": u"Error al inesperado al guardar los datos %s" % ex})

        else:
            data = {'title': 'Listado de  Periodos'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']
                if action == 'editperiodo':
                    try:
                        from .forms import PeriodoActForm
                        data['title'] = u'Editar periodo'
                        id = request.GET.get('id', None)
                        try:
                            periodo = Periodo.objects.get(pk=id)
                        except ObjectDoesNotExist:
                            raise NameError(u"No se encontro el periodo a editar")
                        data['periodo'] = periodo
                        data['form'] = PeriodoActForm(initial={
                            'nombre': periodo.nombre,
                            'inicio': periodo.inicio,
                            'fin': periodo.fin,
                            'activo': periodo.activo,
                            'tipo': periodo.tipo
                        })
                        return render(request, "periodo/edit.html", data)
                    except Exception as ex:
                        return HttpResponseRedirect(f"{request.path}&info={ex.__str__()}")

                elif action == 'addcomponenteevaluacion':
                    try:
                        from .forms import EvaluacionComponentePeriodoFrom
                        data['title'] = u'Adicionar componente'
                        id = request.GET.get('id', None)
                        try:
                            periodo = Periodo.objects.get(pk=int(id))
                        except ObjectDoesNotExist:
                            raise NameError(u"No se encontro el periodo a editar")
                        data['periodo_id'] = id
                        data['form'] = EvaluacionComponentePeriodoFrom()
                        return render(request, "periodo/addcomponenteevaluacion.html", data)
                    except Exception as ex:
                        return HttpResponseRedirect(f"{request.path}&info={ex.__str__()}")

                elif action == 'editcomponenteevaluacion':
                    try:
                        from .forms import EvaluacionComponentePeriodoFrom
                        from .models import EvaluacionComponentePeriodo
                        data['title'] = u'Editar componente'
                        id = request.GET.get('id', None)
                        try:
                            evaluacionComponentePeriodo = EvaluacionComponentePeriodo.objects.get(pk=int(id))
                        except ObjectDoesNotExist:
                            raise NameError(u"No se encontro el componente")
                        data['componente_id'] = id
                        data['form'] = EvaluacionComponentePeriodoFrom(initial={
                            'componente': evaluacionComponentePeriodo.componente,
                            'parcial': evaluacionComponentePeriodo.parcial,
                            'nivelacion': evaluacionComponentePeriodo.nivelacion
                        })
                        return render(request, "periodo/editcomponenteevaluacion.html", data)
                    except Exception as ex:
                        return HttpResponseRedirect(f"{request.path}&info={ex.__str__()}")

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

                    periodo = Periodo.objects.filter(nombre__icontains=search).order_by('nombre')
                else:
                    periodo = Periodo.objects.all().order_by('-activo', '-id')

                paging = MiPaginador(periodo, 30)
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
                data['periodo'] = page.object_list

                data['formperiodo'] = PeriodoForm(initial={"inicio": datetime.now(), "fin": datetime.now()})
                data['regular'] = TIPO_PERIODO_REGULAR

                return render(request,"periodo/periodo.html", data)
    except Exception as ex:
        return HttpResponseRedirect("/periodo")
