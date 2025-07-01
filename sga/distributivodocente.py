import json
from django.db.models import Q
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.template.loader import get_template
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from decorators import secure_module
from django.db.models import Count, PROTECT, Sum, Avg, Min, Max, F, OuterRef, Subquery, FloatField, Exists

from sga.models import CriterioPeriodo


@login_required(redirect_field_name='ret', login_url='/login')
@secure_module

def view(request):
    from .models import Profesor
    from sga.commonviews import addUserData
    data = {}
    addUserData(request, data)
    persona = request.session['persona']
    periodo = request.session['periodo']
    if request.method == 'POST':
        action = request.POST['action']
        if action == 'addcriterio':
            with transaction.atomic():
                try:
                    from .models import Criterio
                    from .forms import CriterioForm
                    form = CriterioForm(request.POST)
                    if not form.is_valid():
                        return JsonResponse({"isSuccess": False, "message": u"Error¡  Revise que se encuentre lleno correctamente el formulario, y vuelva a intentarlo"})
                    if Criterio.objects.values("id").filter(nombre=form.cleaned_data['nombre']).exists():
                        return JsonResponse({"isSuccess": False, "message": u"Error¡  El criterio ya se encuentra registrado"})
                    criterio = Criterio(nombre=form.cleaned_data['nombre'],
                                        dedicacion=form.cleaned_data['dedicacion'],
                                        tipocriterio=form.cleaned_data['tipocriterio']
                                        )
                    criterio.save()
                    return JsonResponse({"isSuccess": True, "message": u"Se guardo correctamente el criterio"})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return HttpResponseRedirect(u"/distributivodocente?action=criterio&id=%s&error=Error Vuelva  intentarlo" % int(request.POST['id']))

        elif action == 'editcriterio':
            with transaction.atomic():
                try:
                    from .models import Criterio
                    from .forms import CriterioForm
                    form = CriterioForm(request.POST)
                    if not form.is_valid():
                        return JsonResponse({"isSuccess": False, "message": u"Error¡  Revise que se encuentre lleno correctamente el formulario, y vuelva a intentarlo"})
                    id = request.POST.get('id', 0)
                    try:
                        criterio = Criterio.objects.get(pk=id)
                    except ObjectDoesNotExist:
                        raise NameError(u"No se encontro el criterio")
                    if Criterio.objects.values("id").filter(nombre=form.cleaned_data['nombre']).exclude(id=criterio.id).exists():
                        return JsonResponse({"isSuccess": False, "message": u"Error¡  El criterio ya se encuentra registrado"})
                    criterio.nombre=form.cleaned_data['nombre']
                    criterio.dedicacion=form.cleaned_data['dedicacion']
                    criterio.tipocriterio=form.cleaned_data['tipocriterio']
                    criterio.save()
                    return JsonResponse({"isSuccess": True, "message": u"Se actualizó correctamente el criterio"})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return HttpResponseRedirect(u"/distributivodocente?action=criterio&id=%s&error=Error Vuelva  intentarlo" % int(request.POST['id']))

        elif action == 'delcriterio':
            with transaction.atomic():
                try:
                    from .models import Criterio
                    id = request.POST.get('id', 0)
                    try:
                        criterio = Criterio.objects.get(pk=id)
                    except ObjectDoesNotExist:
                        raise NameError(u"No existe el criterio a eliminar")
                    if criterio.en_uso():
                        return JsonResponse({"isSuccess": False, "message": u"No puede eliminar el criterio, se encuentra en uso"})
                    criterio.delete()
                    return JsonResponse({"isSuccess": True, "message": u"Se elimino correctamente el criterio "})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"isSuccess": False, "message": u"Error al eliminar el criterio: %s" % ex})

        elif action == 'addcriterioperiodo':
            with transaction.atomic():
                try:
                    from .models import Criterio
                    if not 'lista_items1' in request.POST:
                        return JsonResponse({"isSuccess": False, "message": u"Error¡  Revise que se encuentre selecionado correctamente los criterios, y vuelva a intentarlo"})
                    id = request.POST.get('id', 0)
                    listaCriterios = json.loads(request.POST['lista_items1'])
                    for item in listaCriterios:
                        try:
                            criterio = Criterio.objects.get(pk=int(item.get("id")))
                        except ObjectDoesNotExist:
                            raise NameError(u"No existe el criterio")
                        criterioPeriodo = CriterioPeriodo(criterio=criterio,
                                                          periodo=periodo,
                                                          tipocriterio=id
                                                          )
                        criterioPeriodo.save()
                    return JsonResponse({"isSuccess": True, "message": u"Se asignó correctamente los criterio"})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"isSuccess": False, "message": f"Error al obtener los datos. {ex.__str__()}"})

        elif action == 'delcriterioperiodo':
            with transaction.atomic():
                try:
                    id = request.POST.get('id', 0)
                    try:
                        criterioperiodo = CriterioPeriodo.objects.get(pk=id)
                    except ObjectDoesNotExist:
                        raise NameError(u"No existe el criterio docente en el periodo %s, paraa eliminar" %periodo)
                    criterioperiodo.delete()
                    return JsonResponse({"isSuccess": True, "message": u"Se elimino correctamente el criterio docente"})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"isSuccess": False, "message": u"Error al eliminar el criterio: %s" % ex})

        elif action == 'addminimo':
            with transaction.atomic():
                try:
                    id = request.POST.get('id', 0)
                    try:
                        criterioperiodo = CriterioPeriodo.objects.get(pk=id)
                    except ObjectDoesNotExist:
                        raise NameError(u"No existe el criterio" % id)
                    minimo = int(request.POST.get('value', 0))
                    if not minimo >= 0:
                        raise NameError(u"Error el número no es correcto, por favor ingrese un número valido")
                    if criterioperiodo.maximo < minimo:
                        raise NameError(u"El valor mínimo debe ser menor al máximo")
                    criterioperiodo.minimo = minimo
                    criterioperiodo.save()
                    return JsonResponse({"isSuccess": True, "message": u"Se actualizó correctamente el mínimo"})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"isSuccess": False, "message": u"Error al actualizar el mínimo del criterio: %s" % ex})

        elif action == 'addmaximo':
            with transaction.atomic():
                try:
                    id = request.POST.get('id', 0)
                    try:
                        criterioperiodo = CriterioPeriodo.objects.get(pk=id)
                    except ObjectDoesNotExist:
                        raise NameError(u"No existe el criterio" % id)
                    maximo = int(request.POST.get('value', 0))
                    if not maximo >= 0:
                        raise NameError(u"Error el número no es correcto, por favor ingrese un número valido")
                    if criterioperiodo.minimo > maximo:
                        raise NameError(u"El valor máximo debe ser mayor al mínimo")
                    criterioperiodo.maximo = int(maximo)
                    criterioperiodo.save()
                    return JsonResponse({"isSuccess": True, "message": u"Se actualizó correctamente el máximo"})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"isSuccess": False, "message": u"Error al actualizar el máximo del criterio: %s" % ex})

        elif action == 'addprofesor':
            try:
                from .models import ProfesorDistributivoHoras
                from .forms import CriterioDocenteForm
                form = CriterioDocenteForm(request.POST)
                if not form.is_valid():
                    form.addErrors(form.errors.get_json_data(escape_html=True))
                    raise NameError(u"Error¡  Revise que se encuentre lleno correctamente el formulario, y vuelva a intentarlo")
                if ProfesorDistributivoHoras.objects.values("id").filter(profesor=form.cleaned_data['profesor']).exists():
                    raise NameError(u"El profesor ya existe")
                with transaction.atomic():
                    eProfesorDistributivoHoras = ProfesorDistributivoHoras(
                        profesor=form.cleaned_data['profesor'],
                        fechainiciocontrato=form.cleaned_data['desde'],
                        fechafincontrato=form.cleaned_data['hasta']
                    )
                eProfesorDistributivoHoras.save()
                return JsonResponse({"isSuccess": True, "message": u"Se actualizó correctamente el máximo"})
            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse({"isSuccess": False, "message": u"Error al actualizar el máximo del criterio: %s" % ex})

        return JsonResponse({"isSuccess": False, "message": f"Acción no encontrada"})
    elif 'action' in request.GET:
        action = request.GET['action']
        if action == 'criterio':
            try:
                from .models import Criterio
                data['title'] = u'Criterio de actividades docente'
                data['criterios'] = Criterio.objects.all().order_by('nombre')
                return render(request, "distributivodocente/view_criterio.html", data)
            except Exception as ex:
                return HttpResponseRedirect(f"{request.path}/?info={ex.__str__()}")

        elif action == 'addcriterio':
            try:
                from .forms import CriterioForm
                data['title'] = u'Criterio de actividades docente'
                data['form'] = CriterioForm()
                return render(request, "distributivodocente/addcriterio.html", data)
            except Exception as ex:
                return HttpResponseRedirect(f"{request.path}/?info={ex.__str__()}")

        elif action == 'editcriterio':
            try:
                from .models import Criterio
                from .forms import CriterioForm
                data['idcriterio'] = id = request.GET.get('id', 0)
                try:
                    criterio = Criterio.objects.get(pk=id)
                except ObjectDoesNotExist:
                    raise NameError(u"No se encontro la el criterio")
                data['title'] = u'Criterio de actividades docente'
                data['form'] = CriterioForm(initial={'nombre': criterio.nombre,
                                                     'dedicacion': criterio.dedicacion,
                                                     'tipocriterio': criterio.tipocriterio
                                                     })
                return render(request, "distributivodocente/editcriterio.html", data)
            except Exception as ex:
                return HttpResponseRedirect(f"{request.path}/?info={ex.__str__()}")

        elif action == 'criterioperiodo':
            try:
                from .models import Criterio, TIPO_CRITERIO
                from .forms import CriterioForm
                data['title'] = u'Configuración de criterios'
                data['lista'] = TIPO_CRITERIO
                data['criterios_planificados'] = CriterioPeriodo.objects.filter(periodo_id=periodo.id).distinct()
                return render(request, "distributivodocente/view_criterioperiodo.html", data)
            except Exception as ex:
                return HttpResponseRedirect(f"{request.path}/?info={ex.__str__()}")

        elif action == 'addcriterioperiodo':
            try:
                from .models import Criterio
                from .forms import CriterioForm
                data['item'] = itemT = request.GET.get('item', 0)
                data['criterios'] = Criterio.objects.filter(tipocriterio=itemT).distinct().order_by("nombre")
                data['title'] = u'Adicionar Criterio de docente'
                return render(request, "distributivodocente/addcriterioperiodo.html", data)
            except Exception as ex:
                return HttpResponseRedirect(f"{request.path}/?info={ex.__str__()}")

        elif action == 'addprofesor':
            try:
                from .forms import CriterioDocenteForm
                data['title'] = u'Adicionar profesor'
                data['form'] = CriterioDocenteForm()
                return render(request, "distributivodocente/addprofesor.html", data)
            except Exception as ex:
                return HttpResponseRedirect(f"{request.path}/?info={ex.__str__()}")

    else:
        from .models import TIPO_CRITERIO
        data['title'] = u'Distributivo Docente'
        return render(request, "distributivodocente/view.html", data)

