from datetime import datetime, timedelta
import os
import json
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.http import JsonResponse
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from decorators import secure_module
from sga.commonviews import addUserData
from sga.models import Materia
from django.template.loader import get_template


@login_required(redirect_field_name='ret', login_url='/login')
@secure_module

def view(request):
    from  .models import Profesor
    data = {}
    addUserData(request, data)
    persona = request.session['persona']
    periodo = request.session['periodo']
    if request.method == 'POST':
        action = request.POST['action']
        if action == 'apro_rec_silabo':
            with transaction.atomic():
                try:
                    from .models import Silabo, AprobarSilabo
                    id = request.POST.get('id', 0)
                    try:
                        silabo = Silabo.objects.get(pk=id)
                    except ObjectDoesNotExist:
                        raise NameError(u"No se encontro el silabo")
                    estado = request.POST.get('idest', None)
                    if int(estado) == 2:
                        menssage = "Se aprobó el sílabo correctamente"
                    else:
                        menssage = "Se rechazo el sílabo correctamente, para modificación"
                        # if PlanAnalitico.objects.filter(asignaturamalla=ePlanAnalitico.asignaturamalla, activo=True).exists():
                        #     raise NameError(u"No es permitido activar el plan analítico mientras exista otro activo")
                    silabo.estado = estado
                    silabo.save()
                    aprobarSilabo = AprobarSilabo(silabo=silabo,
                                                  observacion=request.POST.get('obs', None),
                                                  persona_id=persona.id,
                                                  estadoaprobacion=estado,
                                                  fecha=datetime.now())
                    aprobarSilabo.save()
                    return JsonResponse({"isSuccess": True, "message": menssage})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"isSuccess": False, "message": u"Error al procesar los datos: %s" % ex})

        return HttpResponse(json.dumps({'result': 'bad', 'mensaje': u'Solicitud incorrecta'}), content_type="application/json")

    elif 'action' in request.GET:
        action = request.GET['action']

        if action == 'silabosemanal':
            try:
                from .models import Silabo
                data['title'] = u'Planificación semanal del sílabo'
                id = request.GET.get('id')
                try:
                    materia = Materia.objects.get(pk=id)
                except ObjectDoesNotExist:
                    raise NameError(u"No se encontró la materia")
                data['materia'] = materia

                ids = request.GET.get('ids')
                try:
                    silabo = Silabo.objects.get(pk=ids)
                except ObjectDoesNotExist:
                    raise NameError(u"No se encontró el sílabo")
                data['silabo'] = silabo

                try:
                    cronogramaacademico = materia.cronograacademicomateria_set.all()[0].cronogramaacademico
                except ObjectDoesNotExist:
                    raise NameError(u"No se encontró el cronograma académico")
                semana, semana_crono = None, None
                data['cronogramasemanal'] = semanas_cronograma = cronogramaacademico.semanas()

                if 'idsem' in request.GET:
                    semana_crono = semanas_cronograma.get(id=request.GET['idsem'])
                elif semanas_cronograma:
                    semana_crono = semanas_cronograma[0]
                if semana_crono:
                    semana = silabo.semana(semana_crono.inicio, semana_crono.fin)
                    data['ids_sel'] = semana_crono.id

                data['semana_crono'] = semana_crono
                data['semana'] = semana
                data['tienesemanas'] = silabo.silabosemanal_set.values("id").exists()
                data['silabo'] = silabo
                data['porcentaje_planificacion_silabo'] = silabo.porcentaje_planificacion_silabo()

                return render(request, "aprobarsilabo/silabosemanal.html", data)
            except Exception as ex:
                return HttpResponseRedirect(f"{request.path}?info={ex.__str__()}")

        elif action == 'apro_rec_silabo':
            try:
                from .models import Silabo, ESTADO_APROBACION_SILABO
                id = request.GET.get("id")
                try:
                    silabo = Silabo.objects.get(pk=id)
                except ObjectDoesNotExist:
                    raise NameError(u"No se encontró el sílabo")

                data['silabo'] = silabo
                data['estados'] = ESTADO_APROBACION_SILABO[1:3]
                data['historialprobacionSilabo'] = silabo.aprobarsilabo_set.all().order_by('-id')
                template = get_template("aprobarsilabo/aprobar_rechazar_silabo.html")
                json_content = template.render(request=request, context=data)
                return JsonResponse({"result": "ok", 'html': json_content})
            except Exception as ex:
                return HttpResponseRedirect(f"{request.path}/?info={ex.__str__()}")

        return HttpResponseRedirect(request.path)
    else:
        try:
            data['title'] = u'Listado de sílabos'
            data['materias'] = Materia.objects.filter(nivel__periodo=periodo, asignatura__asignaturamalla__isnull=False, silabo__isnull=False).distinct().order_by('asignatura')[:25]
            return render(request, "aprobarsilabo/view.html", data)
        except Exception as ex:
            return HttpResponseRedirect(f"{request.path}?info={ex.__str__()}")

