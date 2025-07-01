from datetime import datetime, timedelta
import os
import json
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.http import JsonResponse
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from django.db.models.query_utils import Q
from decorators import secure_module
from sga.commonviews import addUserData
from core.my_pager import MyPaginator
from sga.models import (CronograAcademico, CronograAcademicoDetalle, CronograAcademicoMateria, Profesor,
                        Malla, CronograAcademicoMateria, NivelMalla, CronograAcademico, Materia)
from sga.forms import CronograAcademicoDetalleForm, CronogramaAcademicoForm


@login_required(redirect_field_name='ret', login_url='/login')
# @secure_module

def view(request):
    from  .models import Profesor
    data = {}
    addUserData(request, data)
    persona = request.session['persona']
    periodo = request.session['periodo']
    if request.method == 'POST':
        action = request.POST['action']
        if action == 'addcronograma':
            with transaction.atomic():
                try:
                    errors_frm = {}
                    form = CronogramaAcademicoForm(request.POST)
                    if not form.is_valid():
                        errors_frm = form.toArray()
                        raise NameError("Debe ingresar la información en todos los campos.")
                    if CronograAcademico.objects.values("id").filter(periodo=periodo, nombre=form.cleaned_data['nombre']).exists():
                        raise NameError(u"Ya existe un cronograma con el mismo nombre.")
                    cronograma = CronograAcademico(nombre=form.cleaned_data['nombre'], periodo=periodo)
                    cronograma.save()
                    return JsonResponse({"isSuccess": True, "message": u"Se guardo correctamente el cronograma"})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"isSuccess": False, "message": u"Error al guardar los datos: %s" % ex, 'form': errors_frm})

        if action == 'editcronograma':
            with transaction.atomic():
                try:
                    errors_frm = {}
                    form = CronogramaAcademicoForm(request.POST)
                    if not form.is_valid():
                        errors_frm = form.toArray()
                        raise NameError("Debe ingresar la información en todos los campos.")
                    try:
                        cronograma = CronograAcademico.objects.get(pk=int(request.POST['id']))
                    except ObjectDoesNotExist:
                        raise NameError(u"No se encontro conograma a editar")
                    if CronograAcademico.objects.values("id").filter(periodo=periodo, nombre=form.cleaned_data['nombre']).exclude(id=cronograma.id).exists():
                        raise NameError(u"Ya existe un cronograma con el mismo nombre.")
                    cronograma.nombre = form.cleaned_data['nombre']
                    cronograma.save()
                    return JsonResponse({"isSuccess": True, "message": u"Se guardo correctamente el cronograma"})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"isSuccess": False, "message": u"Error al guardar los datos: %s" % ex, 'form': errors_frm})

        elif action == 'delcronograma':
            with transaction.atomic():
                try:
                    try:
                        cronograma = CronograAcademico.objects.get(pk=int(request.POST['id']))
                    except ObjectDoesNotExist:
                        raise NameError(u"No se encontro cronograma a eliminar")
                    if cronograma.en_uso():
                        raise NameError(u"Cronograma se encuentra en uso")
                    cronograma.delete()
                    return JsonResponse({"isSuccess": True, "message": "Se elimino correctamente el cronograma"})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"isSuccess": False, "message": u"%s" % ex.__str__()})

        elif action == 'addsemana':
            with transaction.atomic():
                try:
                    errors_frm = {}
                    form = CronograAcademicoDetalleForm(request.POST)
                    if not form.is_valid():
                        errors_frm = form.toArray()
                        raise NameError("Debe ingresar la información en todos los campos.")
                    if CronograAcademicoDetalle.objects.values("id").filter(cronogramaacademico_id=request.POST['id'], descripcion=form.cleaned_data['descripcion']).exists():
                        raise NameError("Ya existe una semana con estas caracteristicas.")
                    cronograma = CronograAcademicoDetalle(cronogramaacademico_id=request.POST['id'],
                                                          inicio=form.cleaned_data['inicio'],
                                                          descripcion=form.cleaned_data['descripcion'],
                                                          fin=form.cleaned_data['fin'],
                                                          parcial=form.cleaned_data['parcial'],
                                                          numsemana=form.cleaned_data['numsemana'],
                                                          examen=form.cleaned_data['examen'])
                    cronograma.save()
                    return JsonResponse({"isSuccess": True, "message": u"Se guardo correctamente el cronograma"})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"isSuccess": False, "message": u"Error al guardar los datos: %s" % ex, 'form': errors_frm})

        elif action == 'editsemana':
            with transaction.atomic():
                try:
                    errors_frm = {}
                    form = CronograAcademicoDetalleForm(request.POST)
                    if not form.is_valid():
                        errors_frm = form.toArray()
                        raise NameError("Debe ingresar la información en todos los campos.")
                    cronogramaacademicodetalle = CronograAcademicoDetalle.objects.get(pk=request.POST['id'])
                    if CronograAcademicoDetalle.objects.values("id").filter(cronogramaacademico_id=request.POST['id'], descripcion=form.cleaned_data['descripcion']).exclude(id=cronogramaacademicodetalle.id).exists():
                        raise NameError("Ya existe una semana con estas caracteristicas.")
                    cronogramaacademicodetalle.descripcion = request.POST['descripcion']
                    cronogramaacademicodetalle.inicio = form.cleaned_data['inicio']
                    cronogramaacademicodetalle.fin = form.cleaned_data['fin']
                    cronogramaacademicodetalle.parcial = form.cleaned_data['parcial']
                    cronogramaacademicodetalle.numsemana = form.cleaned_data['numsemana']
                    cronogramaacademicodetalle.examen = form.cleaned_data['examen']
                    cronogramaacademicodetalle.save()
                    return JsonResponse({"isSuccess": True, "message": u"Se guardo correctamente el cronograma"})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"isSuccess": False, "message": u"Error al guardar los datos: %s" % ex, 'form': errors_frm})

        elif action == 'delsemana':
            with transaction.atomic():
                try:
                    try:
                        cronogramaacademicodetalle = CronograAcademicoDetalle.objects.get(pk=int(request.POST['id']))
                    except ObjectDoesNotExist:
                        raise NameError(u"No se encontro cronograma semanal")
                    if cronogramaacademicodetalle.en_uso():
                        raise NameError(u"Semana del cronograma se encuentra en uso")
                    cronogramaacademicodetalle.delete()
                    return JsonResponse({"isSuccess": True, "message": "Se elimino correctamente la semana del cronograma"})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"isSuccess": False, "message": u"%s" % ex.__str__()})

        elif action == 'asignarmateria':
            with transaction.atomic():
                try:
                    lista = []
                    for item in json.loads(request.POST['lista']):
                        lista.append(int(item))
                        if not CronograAcademicoMateria.objects.filter(cronogramaacademico_id=request.POST['id'], materia_id=item).exists():
                            cm = CronograAcademicoMateria(cronogramaacademico_id=request.POST['id'], materia_id=item)
                            cm.save()
                    CronograAcademicoMateria.objects.filter(cronogramaacademico_id=request.POST['id']).exclude(materia__id__in=lista).delete()
                    return JsonResponse({"isSuccess": True, "message": "Las materias asignadas correctamente."})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"isSuccess": True, "message": f"{ex.__str__()}"})

        elif action == 'quitarMateria':
            with transaction.atomic():
                try:
                    id = int(request.POST.get('id', '0'))
                    try:
                        eCronograAcademicoMateria = CronograAcademicoMateria.objects.get(pk=id)
                    except ObjectDoesNotExist:
                        raise NameError(u"No se encontro la materia en el cronograma académico")
                    eCronograAcademicoMateria.delete()
                    return JsonResponse({"isSuccess": True, "message": "Se quito materia del cronograma académico."})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"isSuccess": True, "message": f"{ex.__str__()}"})

        elif action == 'agregarMateria':
            with transaction.atomic():
                try:
                    idc = int(request.POST.get('idc', '0'))
                    idm = int(request.POST.get('idm', '0'))
                    try:
                        eCronograAcademico = CronograAcademico.objects.get(pk=idc)
                    except ObjectDoesNotExist:
                        raise NameError(u"No se encontro el cronograma académico")
                    try:
                        eMateria = Materia.objects.get(pk=idm)
                    except ObjectDoesNotExist:
                        raise NameError(u"No se encontro la materia")
                    if not CronograAcademicoMateria.objects.only("id").filter(cronogramaacademico=eCronograAcademico, materia=eMateria).exists():
                        eCronograAcademicoMateria = CronograAcademicoMateria(cronogramaacademico=eCronograAcademico, materia=eMateria)
                        eCronograAcademicoMateria.save()
                    return JsonResponse({"isSuccess": True, "message": "Se agrego materia al cronograma académico."})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"isSuccess": True, "message": f"{ex.__str__()}"})

        return JsonResponse({"isSuccess": False, "message": f"Solicitud incorrecta"})

    elif 'action' in request.GET:
        action = request.GET['action']

        if action == 'addcronograma':
            try:
                data['title'] = u'Adicionar Cronograma'
                data['form'] = CronogramaAcademicoForm()
                return render(request, "adm_cronogramaacademico/addcronograma.html", data)
            except Exception as ex:
                return HttpResponseRedirect(f"{request.path}?info={ex.__str__()}")

        elif action == 'editcronograma':
            try:
                data['title'] = u'Editar Cronograma'
                data['cronograma'] = coronograma = dict(CronograAcademico.objects.values("id", "nombre").get(pk=int(request.GET['id'])))
                data['form'] = CronogramaAcademicoForm(initial=coronograma)
                return render(request, "adm_cronogramaacademico/editcronograma.html", data)
            except Exception as ex:
                return HttpResponseRedirect(f"{request.path}?info={ex.__str__()}")

        elif action == 'addsemana':
            try:
                data['title'] = u'Adicionar semana'
                data['id'] = id = request.GET['id']
                try:
                    cronograma = CronograAcademico.objects.get(pk=id)
                except ObjectDoesNotExist:
                    raise NameError(u"No se encontro la el criterio")
                numsemana = CronograAcademicoDetalle.objects.values("id").filter(cronogramaacademico_id=id).count() + 1
                inicio = datetime.now().date()
                if CronograAcademicoDetalle.objects.values("id").filter(cronogramaacademico_id=id).exists():
                    inicio = CronograAcademicoDetalle.objects.values("inicio").filter(cronogramaacademico_id=id).order_by('-numsemana').first().get("inicio")
                inicio = inicio + timedelta(days=1)
                fin = inicio + timedelta(days=7)
                data['form'] = CronograAcademicoDetalleForm(initial={
                    'numsemana': numsemana,
                    'inicio': inicio,
                    'fin': fin
                })
                return render(request, "adm_cronogramaacademico/addsemana.html", data)
            except Exception as ex:
                return HttpResponseRedirect(f"{request.path}?info={ex.__str__()}")

        elif action == 'editsemana':
            try:
                data['title'] = u'Editar semana'
                data['semana'] = dictCronograma = dict(CronograAcademicoDetalle.objects.values("id", "descripcion", "inicio", "fin", "parcial", "numsemana", "examen").get(pk=int(request.GET['id'])))
                data['form'] = CronograAcademicoDetalleForm(initial=dictCronograma)
                return render(request, "adm_cronogramaacademico/editsemana.html", data)
            except Exception as ex:
                return HttpResponseRedirect(f"{request.path}?info={ex.__str__()}")

        elif action == 'view_materias':
            try:
                data['title'] = u'Asignación de materias'
                id, filtros, s, idm, idn, url_vars = request.GET.get('id', '0'), Q(), request.GET.get('s', ''), request.GET.get('idm', '0'), request.GET.get('idn', '0'), ''
                try:
                    id = int(id)
                except ValueError:
                    id = 0
                try:
                    eCronograAcademico = CronograAcademico.objects.get(pk=id)
                except ObjectDoesNotExist:
                    raise NameError(u"No se encontro el cronograma académico")
                url_vars += f"&action=view_materias&id={id}"
                data['eCronograAcademico'] = eCronograAcademico
                eBaseLista = CronograAcademicoMateria.objects.filter(cronogramaacademico=eCronograAcademico)
                filtro_malla = Q(nivel__periodo_id=periodo.id) & Q(id__in=eBaseLista.values_list('materia__nivel__malla__id', flat=True).distinct())
                eMallas = Malla.objects.filter(filtro_malla).distinct().order_by("carrera")
                eNivelMallas = NivelMalla.objects.filter(id__in=eBaseLista.values_list('materia__nivel__nivelmalla__id', flat=True).distinct()).distinct().order_by("orden")
                filtros &= Q(cronogramaacademico=eCronograAcademico)
                if s:
                    if s.isdigit():
                        filtros &= (Q(id=s))
                    else:
                        filtros &= (Q(materia__asignatura__nombre__icontains=s) | Q(materia__identificacion__icontains=s))
                    data['s'] = f"{s}"
                    url_vars += f"&s={s}"
                try:
                    idm = int(idm)
                except ValueError:
                    idm = 0
                if idm > 0:
                    filtros &= Q(materia__nivel__malla__id=idm)
                try:
                    idn = int(idn)
                except ValueError:
                    idn = 0

                if idn > 0:
                    filtros &= Q(materia__nivel__nivelmalla__id=idn)
                url_vars += f"&id={id}&idm={idm}&idn={idn}"
                eCronograAcademicoMaterias = CronograAcademicoMateria.objects.filter(filtros).order_by("materia__nivel__malla__carrera", "materia__nivel__nivelmalla", "materia__asignatura__nombre")
                paging = MyPaginator(eCronograAcademicoMaterias, 25)
                p = 1
                try:
                    sessionPage = 1
                    if 'pager' in request.session:
                        sessionPage = int(request.session['pager'])
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                    else:
                        p = sessionPage
                    try:
                        page = paging.page(p)
                    except:
                        p = 1
                    page = paging.page(p)
                except:
                    page = paging.page(p)
                request.session['pager'] = p
                data['paging'] = paging
                data['page'] = page
                data['paged_ranges'] = paging.paginated_ranges(p)
                data['eCronograAcademicoMaterias'] = page.object_list
                data['url_vars'] = url_vars
                data['eMallas'] = eMallas
                data['eNivelMallas'] = eNivelMallas
                data['idm'] = idm
                data['idn'] = idn
                ids_exclude = CronograAcademicoMateria.objects.values_list("materia__id", flat=True).filter(cronogramaacademico=eCronograAcademico).distinct()
                eMaterias = Materia.objects.filter(nivel__periodo_id=periodo.id).exclude(id__in=ids_exclude).distinct()
                data['eMallas_filter'] = Malla.objects.filter(id__in=eMaterias.values_list('nivel__malla__id', flat=True).distinct()).distinct().order_by("carrera")
                data['eNivelMallas_filter'] = NivelMalla.objects.filter(id__in=eMaterias.values_list('nivel__nivelmalla__id', flat=True).distinct()).distinct().order_by("orden")
                return render(request, "adm_cronogramaacademico/materia/view.html", data)
            except Exception as ex:
                return HttpResponseRedirect(f"{request.path}?info={ex.__str__()}")

        elif action == 'loadDataTable':
            try:
                id = request.GET.get('id', '0')
                idm = request.GET.get('idm', '0')
                idn = request.GET.get('idn', '0')
                try:
                    id = int(id)
                except ValueError:
                    id = 0
                try:
                    idm = int(idm)
                except ValueError:
                    idm = 0
                try:
                    idn = int(idn)
                except ValueError:
                    idn = 0
                try:
                    eCronograAcademico = CronograAcademico.objects.get(pk=id)
                except ObjectDoesNotExist:
                    raise NameError(u"No se encontro el cronograma académico")
                search = request.GET.get('sSearch', '')
                limit = int(request.GET.get('iDisplayLength', '25'))
                offset = int(request.GET.get('iDisplayStart', '0'))
                aaData = []
                tCount = 0
                filtros = Q(nivel__periodo=periodo)
                if search:
                    filtros &= (Q(asignatura__nombre__icontains=search) | Q(identificacion__icontains=search))
                if idm:
                    filtros &= Q(nivel__malla__id=idm)
                if idn:
                    filtros &= Q(nivel__nivelmalla__id=idn)
                ids_exclude = CronograAcademicoMateria.objects.values_list("materia__id", flat=True).filter(cronogramaacademico=eCronograAcademico).distinct()
                eMaterias = Materia.objects.filter(filtros).exclude(id__in=ids_exclude).distinct().order_by("nivel__malla__carrera", "nivel__nivelmalla", "asignatura__nombre")
                tCount = eMaterias.values("id").count()
                if offset == 0:
                    rows = eMaterias[offset:limit]
                else:
                    rows = eMaterias[offset:offset + limit]
                aaData = []
                rc = 0
                for row in rows:
                    rc += 1
                    aaData.append([rc,
                                   {
                                       'asignatura': row.nombre_completo(),
                                       'malla': row.nivel.malla.carrera.__str__() if row.nivel.malla.carrera else None,
                                       'horas': row.horas,
                                       'creditos': row.creditos,
                                   },
                                   row.nivel.nivelmalla.nombre,
                                   {
                                       'inicio': row.inicio.strftime('%d/%m/%Y') if row.inicio else None,
                                       'fin': row.fin.strftime('%d/%m/%Y') if row.fin else None,
                                   },
                                   {
                                       "id": row.id,
                                       "name": row.nombre_completo()
                                   },
                                   ])

                return JsonResponse({"isSuccess": True,
                                     "message": f"Carga de datos",
                                     "aaData": aaData,
                                     "iTotalRecords": tCount,
                                     "iTotalDisplayRecords": tCount})
            except Exception as ex:
                return JsonResponse({"isSuccess": False,
                                     "message": ex.__str__(),
                                     "aaData": [],
                                     "iTotalRecords": 0,
                                     "iTotalDisplayRecords": 0})

        return HttpResponseRedirect(request.path)
    else:
        try:
            data['title'] = u'Planificación de Sílabo'
            data['cronogramas'] = CronograAcademico.objects.all().order_by('id')
            return render(request, "adm_cronogramaacademico/view.html", data)
        except Exception as ex:
            return HttpResponseRedirect(f"/?info={ex.__str__()}")

