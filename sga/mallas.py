from datetime import datetime
import os
import json
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
from decorators import secure_module
from settings import MEDIA_ROOT
from sga.commonviews import addUserData, ip_client_address
from sga.forms import MallaForm, AsignaturaMallaForm, SyllabusForm
from sga.funciones import logEntry
from sga.models import Malla, NivelMalla, EjeFormativo, AsignaturaMalla, Carrera,OrganizacionAsignaturaMalla,OrganizacionAprendizaje

@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    if request.method=='POST':
        action = request.POST['action']
        if action == 'add':
            m = MallaForm(request.POST)
            if m.is_valid():
                m.save()
                malla = Malla.objects.latest('id')

                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de ADICIONAR MALLA CURRICULAR
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(malla).pk,
                    object_id       = malla.id,
                    object_repr     = force_str(malla),
                    action_flag     = ADDITION,
                    change_message  = 'Adicionada Malla Curricular (' + client_address + ')'  )
            else:
                return HttpResponseRedirect("/mallas?action=add&error=1")

        elif action=='actualizaorg':
            am = AsignaturaMalla.objects.get(pk=request.POST['id'])
            am.organizacionaprendizaje()
            if OrganizacionAsignaturaMalla.objects.filter(organizacion__id=int(request.POST['idh']),asignaturamalla__id=int(request.POST['id'])).exists():
                o = OrganizacionAsignaturaMalla.objects.filter(organizacion__id=int(request.POST['idh']),asignaturamalla__id=int(request.POST['id']))[:1].get()
                horasant = o.horas
                o.horas = request.POST['horas']
                # print((request.POST['horas']))
                o.save()
                cantorg=OrganizacionAsignaturaMalla.objects.filter(asignaturamalla__id=int(request.POST['id']),horas__gt=0).count()
                if o.asignaturamalla.totalhoras() > o.asignaturamalla.horas:
                    o.horas=horasant
                    o.save()
                    return HttpResponse(json.dumps({'result': 'bad', 'horas':str(o.asignaturamalla.horas),'horasant':str(horasant)}), content_type="application/json")
                if cantorg==3:
                    return HttpResponse(json.dumps({'result': 'ok'}),content_type="application/json")

        elif action == 'addasign':
            m = AsignaturaMallaForm(request.POST)
            if m.is_valid():
                m.save()

                asigmalla = AsignaturaMalla.objects.latest('id')

                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de ADICIONAR ASIGNATURA EN MALLA
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(asigmalla).pk,
                    object_id       = asigmalla.id,
                    object_repr     = force_str(asigmalla),
                    action_flag     = ADDITION,
                    change_message  = 'Adicionada Asignatura en Malla (' + client_address + ')'  )

                return HttpResponseRedirect("/mallas?action=edit&id="+str(m.cleaned_data['malla'].id))
            else:
                return HttpResponseRedirect("/mallas?action=addasign&id="+str(m.cleaned_data['malla'].id))

        elif action=='editasign':
            m = AsignaturaMallaForm(request.POST, instance=AsignaturaMalla.objects.get(pk=request.POST['id']))
            if m.is_valid():
                m.save()

                asigmalla = AsignaturaMalla.objects.get(pk=request.POST['id'])

                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de EDITAR ASIGNATURA EN MALLA
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(asigmalla).pk,
                    object_id       = asigmalla.id,
                    object_repr     = force_str(asigmalla),
                    action_flag     = CHANGE,
                    change_message  = 'Editada Asignatura en Malla (' + client_address + ')'  )

                return HttpResponseRedirect("/mallas?action=edit&id="+str(m.cleaned_data['malla'].id))
            else:
                return HttpResponseRedirect("/mallas")

        elif action == 'delete':
            malla = Malla.objects.get(pk=request.POST['id'])

            #Obtain client ip address
            client_address = ip_client_address(request)

            # Log de ELIMINAR MALLA
            LogEntry.objects.log_action(
                user_id         = request.user.pk,
                content_type_id = ContentType.objects.get_for_model(malla).pk,
                object_id       = malla.id,
                object_repr     = force_str(malla),
                action_flag     = DELETION,
                change_message  = 'Eliminada Malla Curricular (' + client_address + ')'  )

            malla.delete()

        elif action=='addsyllabus':
            f = SyllabusForm(request.POST,request.FILES)
            if f.is_valid():
                matasig = AsignaturaMalla.objects.get(pk=request.POST['idmat'])
                # malla = Malla.objects.get(pk=request.POST['malla'])
                if 'archivo' in request.FILES:
                    archivo = request.FILES['archivo']
                    if matasig.syllabus :
                        mensaje = 'Editado'
                        if (MEDIA_ROOT + '/' + str(matasig.syllabus)) and archivo:
                            os.remove(MEDIA_ROOT + '/' + str(matasig.syllabus))
                    else:
                        mensaje = 'Adicionado'
                    matasig.syllabus = archivo
                    matasig.save()

                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(matasig).pk,
                        object_id       = matasig.id,
                        object_repr     = force_str(matasig),
                        action_flag     = ADDITION,
                        change_message  = mensaje +' Syllabys (' + client_address + ')' )

                    return HttpResponseRedirect("/mallas?action=edit&id="+str(request.POST['malla']))

        elif action=='cambiarhoras':
            try:
                am = AsignaturaMalla.objects.get(pk=request.POST['id'])
                am.horas=float(request.POST['horas'])
                am.save()

                client_address = ip_client_address(request)

                # Log de CAMBIAR HORAS EN LA ASIGNATURA
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(am).pk,
                    object_id       = am.id,
                    object_repr     = force_str(am),
                    action_flag     = CHANGE,
                    change_message  = 'Cambio de Horas(' + client_address + ')'  )

                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            except Exception as e:
                    return HttpResponse(json.dumps({"result":"bad","mensaje":e.message}),content_type="application/json")

        elif action == 'addpea':
            with transaction.atomic():
                try:
                    from .models import (PlanAnalitico, PlanAnaliticoRAI, PlanAnaliticoRAC, PlanAnaliticoObjetivo,
                                         PlanAnaliticoResulAprend, PlanAnaliticoUnidad, PlanAnaliticoTema,
                                         PlanAnaliticoSubTema)
                    from .forms import PlanAnaliticoForm
                    errors_frm = {}
                    form = PlanAnaliticoForm(request.POST)
                    if not form.is_valid():
                        errors_frm = form.toArray()
                        raise NameError("Debe ingresar la información en todos los campos.")
                    # if PlanAnalitico.objects.values("id").filter(asignaturamalla_id=int(request.POST['id']), activo=True).exists():
                    #     raise NameError(u"Existe un plan analítico activo")
                    plananalitico = PlanAnalitico(asignaturamalla_id=int(request.POST['id']),
                                                  formacionprofesional=form.cleaned_data['formacionprofesional'],
                                                  metodologia=form.cleaned_data['metodologia'],
                                                  evidencialogro=form.cleaned_data['evidencialogro']
                                                  )
                    plananalitico.save()
                    """
                        Resultado de aprendizaje institucional RAI
                    """
                    # lista_items1 = form.cleaned_data['lista_items1']
                    # for item in lista_items1:
                    #     descripcion = item.get('descripcion', '')
                    #     try:
                    #         plananalitico_rai = PlanAnaliticoRAI.objects.get(plananalitico=plananalitico, descripcion=descripcion)
                    #     except ObjectDoesNotExist:
                    #         plananalitico_rai = PlanAnaliticoRAI(plananalitico=plananalitico, descripcion=descripcion)
                    #         plananalitico_rai.save()
                    """
                        Resultado de aprendizaje carrera RAC
                    """
                    # lista_items2 = form.cleaned_data['lista_items2']
                    # for item in lista_items2:
                    #     descripcion = item.get('descripcion', '')
                    #     try:
                    #         plananalitico_rac = PlanAnaliticoRAC.objects.get(plananalitico=plananalitico, descripcion=descripcion)
                    #     except ObjectDoesNotExist:
                    #         plananalitico_rac = PlanAnaliticoRAC(plananalitico=plananalitico, descripcion=descripcion)
                    #         plananalitico_rac.save()
                    """
                        Objetivos
                    """
                    # lista_items3 = form.cleaned_data['lista_items3']
                    # for item in lista_items3:
                    #     descripcion = item.get('descripcion', '')
                    #     try:
                    #         plananalitico_obj = PlanAnaliticoObjetivo.objects.get(plananalitico=plananalitico, descripcion=descripcion)
                    #     except ObjectDoesNotExist:
                    #         plananalitico_obj = PlanAnaliticoObjetivo(plananalitico=plananalitico, descripcion=descripcion)
                    #         plananalitico_obj.save()
                    """
                        Metodologias
                    """
                    # lista_items4 = form.cleaned_data['lista_items4']
                    # for item in lista_items4:
                    #     descripcion = item.get('descripcion', '')
                    #     try:
                    #         plananalitico_met = PlanAnaliticoMetodologia.objects.get(plananalitico=plananalitico, descripcion=descripcion)
                    #     except ObjectDoesNotExist:
                    #         plananalitico_met = PlanAnaliticoMetodologia(plananalitico=plananalitico, descripcion=descripcion)
                    #         plananalitico_met.save()

                    lista_items5 = form.cleaned_data['lista_items5']
                    for resultado in lista_items5:
                        resultadopro = PlanAnaliticoResulAprend(plananalitico=plananalitico, descripcion=resultado.get("resultado"), orden=resultado.get("indice_resultado"))
                        resultadopro.save()
                        for dataunidad in resultado.get("unidades"):
                            unidad = PlanAnaliticoUnidad(resultadoaprend=resultadopro, descripcion=dataunidad.get('unidad'), orden=dataunidad.get('indice'))
                            unidad.save()
                            for datatema in dataunidad.get("temas"):
                                tema = PlanAnaliticoTema(unidad=unidad, descripcion=datatema.get('tema'), orden=datatema.get('indice'))
                                tema.save()
                                for datasubtema in datatema.get('subtemas'):
                                    subtema = PlanAnaliticoSubTema(tema=tema, descripcion=datasubtema.get('subtema'), orden=datasubtema.get('indice'))
                                    subtema.save()
                    return JsonResponse({"isSuccess": True, "message": u"Se guardo correctamente el plan analítico"})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"isSuccess": False, "message": u"Error al guardar los datos: %s" % ex, 'forms': errors_frm})

        elif action == 'editpea':
            with transaction.atomic():
                try:
                    from .models import PlanAnalitico, PlanAnaliticoRAI, PlanAnaliticoRAC, PlanAnaliticoObjetivo
                    from .forms import PlanAnaliticoForm
                    errors_frm = {}
                    form = PlanAnaliticoForm(request.POST)
                    if not form.is_valid():
                        errors_frm = form.toArray()
                        raise NameError("Debe ingresar la información en todos los campos.")
                    id = request.POST.get('id', '0')
                    try:
                        plananalitico = PlanAnalitico.objects.get(pk=int(id))
                    except ObjectDoesNotExist:
                        raise NameError(u"No se encontro pla analítico a editar")
                    plananalitico.formacionprofesional = form.cleaned_data['formacionprofesional']
                    plananalitico.evidencialogro = form.cleaned_data['evidencialogro']
                    plananalitico.metodologia = form.cleaned_data['metodologia']
                    plananalitico.save()
                    """
                        Resultado de aprendizaje institucional RAI
                    """
                    # lista_items1 = form.cleaned_data['lista_items1']
                    # ids_item1 = []
                    # for item in lista_items1:
                    #     id = item.get('id', 0)
                    #     descripcion = item.get('descripcion', '')
                    #     try:
                    #         plananalitico_rai = PlanAnaliticoRAI.objects.get(plananalitico=plananalitico, id=id)
                    #         plananalitico_rai.descripcion = descripcion
                    #     except ObjectDoesNotExist:
                    #         plananalitico_rai = PlanAnaliticoRAI(plananalitico=plananalitico, descripcion=descripcion)
                    #     plananalitico_rai.save()
                    #     ids_item1.append(plananalitico_rai.id)
                    # PlanAnaliticoRAI.objects.filter(plananalitico=plananalitico).exclude(pk__in=ids_item1).delete()
                    """
                        Resultado de aprendizaje carrera RAC
                    """
                    # lista_items2 = form.cleaned_data['lista_items2']
                    # ids_item2 = []
                    # for item in lista_items2:
                    #     id = item.get('id', 0)
                    #     descripcion = item.get('descripcion', '')
                    #     try:
                    #         plananalitico_rac = PlanAnaliticoRAC.objects.get(plananalitico=plananalitico, id=id)
                    #         plananalitico_rac.descripcion = descripcion
                    #     except ObjectDoesNotExist:
                    #         plananalitico_rac = PlanAnaliticoRAC(plananalitico=plananalitico, descripcion=descripcion)
                    #     plananalitico_rac.save()
                    #     ids_item2.append(plananalitico_rac.id)
                    # PlanAnaliticoRAC.objects.filter(plananalitico=plananalitico).exclude(pk__in=ids_item2).delete()
                    """
                        Objetivos
                    """
                    # lista_items3 = form.cleaned_data['lista_items3']
                    # ids_item3 = []
                    # for item in lista_items3:
                    #     id = item.get('id', 0)
                    #     descripcion = item.get('descripcion', '')
                    #     try:
                    #         plananalitico_obj = PlanAnaliticoObjetivo.objects.get(plananalitico=plananalitico, id=id)
                    #         plananalitico_obj.descripcion = descripcion
                    #     except ObjectDoesNotExist:
                    #         plananalitico_obj = PlanAnaliticoObjetivo(plananalitico=plananalitico,
                    #                                                   descripcion=descripcion)
                    #     plananalitico_obj.save()
                    #     ids_item3.append(plananalitico_obj.id)
                    # PlanAnaliticoObjetivo.objects.filter(plananalitico=plananalitico).exclude(pk__in=ids_item3).delete()
                    """
                        Metodologias
                    """
                    # lista_items4 = form.cleaned_data['lista_items4']
                    # ids_item4 = []
                    # for item in lista_items4:
                    #     id = item.get('id', 0)
                    #     descripcion = item.get('descripcion', '')
                    #     try:
                    #         plananalitico_met = PlanAnaliticoMetodologia.objects.get(plananalitico=plananalitico, id=id)
                    #         plananalitico_met.descripcion = descripcion
                    #     except ObjectDoesNotExist:
                    #         plananalitico_met = PlanAnaliticoMetodologia(plananalitico=plananalitico,
                    #                                                      descripcion=descripcion)
                    #     plananalitico_met.save()
                    #     ids_item4.append(plananalitico_met.id)
                    # PlanAnaliticoMetodologia.objects.filter(plananalitico=plananalitico).exclude(pk__in=ids_item4).delete()
                    """
                        Contenido programatico del plan analitico  que se compone de Resultados, Unidades, Temas y Subtemas
                    """
                    lista_items5 = form.cleaned_data['lista_items5']
                    from .models import PlanAnaliticoResulAprend, PlanAnaliticoUnidad, PlanAnaliticoTema, \
                        PlanAnaliticoSubTema
                    lista_resultado, lista_unidades, lista_temas, lista_subtemas = [], [], [], []
                    for resultado in lista_items5:
                        exists_resultado = PlanAnaliticoResulAprend.objects.values("id").filter(plananalitico=plananalitico, descripcion=resultado.get("resultado"), orden=resultado.get("indice_resultado")).exists()
                        if not exists_resultado:
                            resultadopro = PlanAnaliticoResulAprend(plananalitico=plananalitico,
                                                                    descripcion=resultado.get("resultado"),
                                                                    orden=resultado.get("indice_resultado"))
                            resultadopro.save()
                        elif exists_resultado:
                            resultadopro = PlanAnaliticoResulAprend.objects.get(plananalitico=plananalitico, descripcion=resultado.get("resultado"),orden=resultado.get("indice_resultado"))
                        lista_resultado.append(resultadopro.id)
                        lista_unidades = []
                        for dataunidad in resultado.get("unidades"):
                            exist_unidad = PlanAnaliticoUnidad.objects.values("id").filter(resultadoaprend=resultadopro, descripcion=dataunidad.get('unidad'), orden=dataunidad.get('indice')).exists()
                            if not exist_unidad:
                                unidad = PlanAnaliticoUnidad(resultadoaprend=resultadopro,
                                                             descripcion=dataunidad.get('unidad'),
                                                             orden=dataunidad.get('indice'))
                                unidad.save()
                            elif exist_unidad:
                                unidad = PlanAnaliticoUnidad.objects.get(resultadoaprend=resultadopro, descripcion=dataunidad.get('unidad'), orden=dataunidad.get('indice'))
                            lista_unidades.append(unidad.id)
                            lista_temas = []
                            for datatema in dataunidad.get("temas"):
                                exists_tema = PlanAnaliticoTema.objects.values("id").filter(unidad=unidad, descripcion=datatema.get('tema'), orden=datatema.get('indice')).exists()
                                if not exists_tema:
                                    tema = PlanAnaliticoTema(unidad=unidad, descripcion=datatema.get('tema'),
                                                             orden=datatema.get('indice'))
                                    tema.save()
                                elif exists_tema:
                                    tema = PlanAnaliticoTema.objects.get(unidad=unidad, descripcion=datatema.get('tema'), orden=datatema.get('indice'))
                                lista_temas.append(tema.id)
                                lista_subtemas = []
                                for datasubtema in datatema.get('subtemas'):
                                    exists_subtema = PlanAnaliticoSubTema.objects.values("id").filter(tema=tema, descripcion=datasubtema.get('subtema'), orden=datasubtema.get('indice')).exists()
                                    if not exists_subtema:
                                        subtema = PlanAnaliticoSubTema(tema=tema, descripcion=datasubtema.get('subtema'),
                                                                       orden=datasubtema.get('indice'))
                                        subtema.save()
                                    elif exists_subtema:
                                        subtema = PlanAnaliticoSubTema.objects.get(tema=tema, descripcion=datasubtema.get('subtema'), orden=datasubtema.get('indice'))
                                    lista_subtemas.append(subtema.id)
                                subtemas_eliminar = PlanAnaliticoSubTema.objects.filter(tema__unidad__resultadoaprend__plananalitico=plananalitico, tema=tema).exclude(id__in=lista_subtemas)
                                subtemas_eliminar.delete()
                            temas_eliminar = PlanAnaliticoTema.objects.filter(unidad__resultadoaprend__plananalitico=plananalitico, unidad=unidad).exclude(id__in=lista_temas)
                            temas_eliminar.delete()
                        unidades_eliminar = PlanAnaliticoUnidad.objects.filter(resultadoaprend__plananalitico=plananalitico, resultadoaprend=resultadopro).exclude(id__in=lista_unidades)
                        unidades_eliminar.delete()
                    resultado_eliminar = PlanAnaliticoResulAprend.objects.filter(plananalitico=plananalitico).exclude(id__in=lista_resultado)
                    if resultado_eliminar:
                        resultado_eliminar.delete()
                    return JsonResponse({"isSuccess": True, "message": u"Se guardo correctamente el plan analítico"})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"isSuccess": False, "message": u"Error al guardar los datos: %s" % ex, 'form': errors_frm})

        elif action == 'delplananalitico':
            with transaction.atomic():
                try:
                    from .models import PlanAnalitico
                    id = request.POST.get('id', 0)
                    try:
                        plananalitico = PlanAnalitico.objects.get(pk=id)
                    except ObjectDoesNotExist:
                        raise NameError(u"No existe plan analítico a eliminar")
                    plananalitico.delete()
                    return JsonResponse({"isSuccess": True, "message": u"Se elimino correctamente el plan analítico"})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"isSuccess": False, "message": u"Error al eliminar el plan analítico: %s" % ex})

        elif action == 'addbibliografiaapa':
            with transaction.atomic():
                try:
                    from .models import PlanAnaliticoApa
                    from .forms import BibliografiaApaForm
                    form = BibliografiaApaForm(request.POST)
                    if form.is_valid():
                        if not PlanAnaliticoApa.objects.values("id").filter(plananalitico_id=int(request.POST['id']), descripcion=form.cleaned_data['descripcion']).exists():
                            plananaliticoapa = PlanAnaliticoApa(plananalitico_id=int(request.POST['id']),
                                                                descripcion=form.cleaned_data['descripcion'],
                                                                fecha_creacion=datetime.now(),
                                                                fecha_ultimamodificacion=datetime.now())
                            plananaliticoapa.save()
                            return JsonResponse({"isSuccess": True, "message": u"Se guardo correctamente la blibliografía apa"})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return HttpResponseRedirect(u"/mallas?action=bibliografiaapa&id=%s&error=Error Vuelva  intentarlo" % int(request.POST['id']))

        elif action == 'editbibliografiaapa':
            with transaction.atomic():
                try:
                    from .models import PlanAnaliticoApa
                    from .forms import BibliografiaApaForm
                    form = BibliografiaApaForm(request.POST)
                    if form.is_valid():
                        apa = PlanAnaliticoApa.objects.get(pk=request.POST['id'])
                        if not PlanAnaliticoApa.objects.values("id").filter(plananalitico_id=int(request.POST['id']), descripcion=form.cleaned_data['descripcion']).exclude(id=apa.id).exists():
                            apa.descripcion=form.cleaned_data['descripcion']
                            apa.fecha_ultimamodificacion=datetime.now()
                            apa.save()
                            return JsonResponse({"isSuccess": True, "message": u"Se guardo correctamente la blibliografía apa"})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return HttpResponseRedirect(u"/mallas?action=bibliografiaapa&id=%s&error=Error Vuelva  intentarlo" % int(request.POST['id']))

        elif action == 'delbibliografiaapa':
            with transaction.atomic():
                try:
                    from .models import PlanAnaliticoApa
                    id = request.POST.get('id', 0)
                    try:
                        plananalitico = PlanAnaliticoApa.objects.get(pk=id)
                    except ObjectDoesNotExist:
                        raise NameError(u"No existe la bibligrafía apa")
                    plananalitico.delete()
                    return JsonResponse({"isSuccess": True, "message": u"Se elimino correctamente la bibligrafía apa "})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"isSuccess": False, "message": u"Error al eliminar la bibligrafía apa: %s" % ex})

        elif action == 'changeEstadoPlan':
            with transaction.atomic():
                try:
                    from .models import PlanAnalitico
                    id = request.POST.get('id', 0)
                    try:
                        ePlanAnalitico = PlanAnalitico.objects.get(pk=id)
                    except ObjectDoesNotExist:
                        raise NameError(u"No se encontro plan analítico")
                    value = request.POST.get('value', None)
                    if not value or not value in ('activate', 'desactivate'):
                        raise NameError(u"Operación no encontrada")
                    estado = False
                    menssage = "Se inactivo el plan analítico correctamente"
                    if value == 'activate':
                        estado = True
                        menssage = "Se activo el plan analítico correctamente"
                        if PlanAnalitico.objects.filter(asignaturamalla=ePlanAnalitico.asignaturamalla, activo=True).exists():
                            raise NameError(u"No es permitido activar el plan analítico mientras exista otro activo")
                    ePlanAnalitico.activo = estado
                    ePlanAnalitico.save()
                    return JsonResponse({"isSuccess": True, "message": menssage})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"isSuccess": False, "message": u"Error al procesar los datos: %s" % ex})

        return HttpResponseRedirect("/mallas")
    else:
        data = {'title': 'Mallas Curriculares'}
        addUserData(request,data)
        if "error" in request.GET:
            data['error'] = request.GET['error']
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='add':
                data['title'] = 'Adicionar Malla Curricular'
                data['form'] = MallaForm(instance=Malla(inicio=datetime.now()))
                return render(request ,"mallas/adicionarbs.html" ,  data)
            elif action=='delasign':
                am = AsignaturaMalla.objects.get(pk=request.GET['id'])
                mid = am.malla_id

                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de ELIMINAR ASIGNATURA MALLA
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(am).pk,
                    object_id       = am.id,
                    object_repr     = force_str(am),
                    action_flag     = DELETION,
                    change_message  = 'Eliminada Asignatura en Malla (' + client_address + ')'  )

                am.delete()
                return HttpResponseRedirect('/mallas?action=edit&id='+str(mid))
            elif action == 'cambiaestado':
                malla = Malla.objects.get(pk=request.GET['id'])
                malla.nueva_malla = not malla.nueva_malla
                malla.save()
                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de ELIMINAR ASIGNATURA MALLA
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(malla).pk,
                    object_id       = malla.id,
                    object_repr     = force_str(malla),
                    action_flag     = DELETION,
                    change_message  = 'Cambia Estado Malla Actual(' + client_address + ')'  )

                return HttpResponseRedirect("/mallas")
            elif action=='delete':
                data['title'] = 'Borrar Malla Curricular'
                data['malla'] = Malla.objects.get(pk=request.GET['id'])
                return render(request ,"mallas/borrarbs.html" ,  data)
            # elif action == 'actualiza':
            #     for m in Malla.objects.filter(nueva_malla=True):
            #         for am in AsignaturaMalla.objects.filter(malla=m):
            #             if 'PREPROFESIONALES' in am.asignatura.nombre:
            #                 am.ejeformativo_id=  8
            #                 am.save()

            elif action=='edit':
                data['malla'] = Malla.objects.get(pk=request.GET['id'])
                data['nivelesdemallas'] = NivelMalla.objects.all().order_by('orden')
                data['ejesformativos'] = EjeFormativo.objects.all().order_by('orden')
                data['asignaturasmallas'] = AsignaturaMalla.objects.filter(malla=data['malla'])
                resumenNiveles = [{'id':x.id, 'horas': x.total_horas(data['malla']), 'creditos': x.total_creditos(data['malla'])} for x in NivelMalla.objects.all().order_by('orden')]
                data['resumenes'] = resumenNiveles
                data['title'] = "Editar Malla Curricular : "+data['malla'].carrera.nombre
                data['frm'] =SyllabusForm()
                data['organizacionaprendizaje'] =OrganizacionAprendizaje.objects.all().order_by('id')
                return render(request ,"mallas/editarbs.html" ,  data)
            elif action=='addasign':
                data['title'] = 'Adicionar Asignatura a Malla Curricular'
                malla = Malla.objects.get(pk=request.GET['id'])
                data['malla'] = malla
                form = AsignaturaMallaForm(instance=AsignaturaMalla(malla=malla,nivelmalla=NivelMalla.objects.get(pk=request.GET['nivel']), ejeformativo=EjeFormativo.objects.get(pk=request.GET['eje'])))
                data['form'] = form
                return render(request ,"mallas/adicionar_asignaturabs.html" ,  data)
            elif action=='editasign':
                data['title'] = 'Editar Asignatura a Malla Curricular'
                am = AsignaturaMalla.objects.get(pk=request.GET['id'])
                data['malla'] = am.malla
                data['form'] = AsignaturaMallaForm(instance=am)
                data['asignaturamalla'] = am
                return render(request ,"mallas/edit_asignaturabs.html" ,  data)

            elif action=='verorganizacion':
                data['title'] = 'Organizacion Aprendizaje Asignatura'
                am = AsignaturaMalla.objects.get(pk=request.GET['id'])
                data['asignaturamalla'] = am
                data['organizacion'] = OrganizacionAsignaturaMalla.objects.filter(asignaturamalla=am).order_by('organizacion__id')
                return render(request,"mallas/verdetalleorg.html",  data)

            elif action == 'pea':
                try:
                    from .models import PlanAnalitico
                    id = int(request.GET.get('id', '0'))
                    try:
                        eAsignaturaMalla = AsignaturaMalla.objects.get(pk=id)
                    except AsignaturaMalla.DoesNotExist:
                        raise NameError('No se encontro la asigantura en malla')
                    data['eAsignaturaMalla'] = eAsignaturaMalla
                    data['title'] = u'Programa de estudio de la asignatura'
                    data['listado'] = PlanAnalitico.objects.filter(asignaturamalla=eAsignaturaMalla).order_by('fecha_creacion')
                    return render(request, "mallas/pea/listado.html", data)
                except Exception as ex:
                    return HttpResponseRedirect(f"{request.path}?info={ex.__str__()}")

            elif action == 'addpea':
                try:
                    from .forms import PlanAnaliticoForm
                    data['title'] = f'Adicionar programa de estudio de la asignatura'
                    id = request.GET.get('id', 0)
                    try:
                        asignaturamalla = AsignaturaMalla.objects.get(pk=id)
                    except AsignaturaMalla.DoesNotExist:
                        raise NameError(u"No se encontro la asignatura en la malla")

                    data['asignaturamalla'] = asignaturamalla
                    form = PlanAnaliticoForm()
                    form.build()
                    data['form'] = form
                    return render(request, "mallas/pea/add.html", data)
                except Exception as ex:
                    return HttpResponseRedirect(f"{request.path}?action=pea&id={id}&info={ex.__str__()}")

            elif action == 'editpea':
                try:
                    from .models import (PlanAnalitico, PlanAnaliticoRAI, PlanAnaliticoRAC, PlanAnaliticoObjetivo)
                    from .forms import PlanAnaliticoForm
                    data['title'] = u'Editar plan analítico'
                    id = request.GET.get('id', 0)
                    ida = request.GET.get('ida', 0)
                    data['id'] = id
                    data['ida'] = ida
                    try:
                        plananalitico = PlanAnalitico.objects.get(pk=id)
                    except ObjectDoesNotExist:
                        raise NameError(u"No se encontro el plan analítico a editar")
                    data['plananalitico'] = plananalitico
                    form = PlanAnaliticoForm(initial={'formacionprofesional': plananalitico.formacionprofesional,
                                                      'evidencialogro': plananalitico.evidencialogro,
                                                      'metodologia': plananalitico.metodologia})
                    form.build()
                    data['form'] = form
                    # data['rais'] = PlanAnaliticoRAI.objects.filter(plananalitico_id=id).order_by('id')
                    # data['racs'] = PlanAnaliticoRAC.objects.filter(plananalitico_id=id).order_by('id')
                    # data['objetivos'] = PlanAnaliticoObjetivo.objects.filter(plananalitico_id=id).order_by('id')
                    # data['metodologias'] = PlanAnaliticoMetodologia.objects.filter(plananalitico_id=id).order_by('id')
                    return render(request, "mallas/pea/edit.html", data)
                except Exception as ex:
                    return HttpResponseRedirect(f"{request.path}?action=pea&id={ida}&info={ex.__str__()}")

            elif action == 'delplananalitico':
                try:
                    from .models import PlanAnalitico
                    data['title'] = u'Eliminar Planificación Analítico'
                    data['plananalitico'] = PlanAnalitico.objects.get(pk=int(request.GET['id']))
                    return render(request, "mallas/delplananalitico.html", data)
                except Exception as ex:
                    pass

            elif action == 'bibliografiaapa':
                try:
                    from .models import PlanAnalitico
                    data['title'] = u'Bibliografía APA'
                    data['plananalitico'] = plananalitico = PlanAnalitico.objects.get( pk=int(request.GET['id']))
                    data['bibliografias'] = plananalitico.plananaliticoapa_set.all().order_by('id')
                    return render(request, "mallas/bibliografiaapa.html", data)
                except Exception as ex:
                    pass

            elif action == 'addbibliografiaapa':
                try:
                    from .models import PlanAnalitico
                    from .forms import BibliografiaApaForm
                    data['title'] = u'Adicionar Bibliografia Apa'
                    data['plananalitico'] = PlanAnalitico.objects.get(pk=int((request.GET['id'])))
                    data['form'] = BibliografiaApaForm()
                    return render(request, "mallas/addbibliografiaapa.html", data)
                except Exception as ex:
                    pass

            elif action == 'editbibliografiaapa':
                try:
                    from .models import PlanAnaliticoApa
                    from .forms import BibliografiaApaForm
                    data['title'] = u'Editar Bibliografia Apa'
                    data['plaanaliticoapa'] = apa = PlanAnaliticoApa.objects.get(pk=int(request.GET['id']))
                    data['form'] = BibliografiaApaForm(initial={'descripcion': apa.descripcion})
                    return render(request, "mallas/editbibliografiaapa.html", data)
                except Exception as ex:
                    pass

            elif action == 'delbibliografiaapa':
                try:
                    from .models import PlanAnaliticoApa
                    data['title'] = u'Eliminar Bibliografia apa'
                    data['plananaliticoapa'] = PlanAnaliticoApa.objects.get(pk=int(request.GET['id']))
                    return render(request, "mallas/delbibliografiaapa.html", data)
                except Exception as ex:
                    pass


            elif action=='editararticulada':
                data['title'] = 'Editar Asignatura a Malla Curricular'
                am = AsignaturaMalla.objects.get(pk=request.GET['id'])
                if am.articulada:
                    am.articulada=False
                else:
                    am.articulada=True

                am.save()

                client_address = ip_client_address(request)

                # Log de CAMBIAR ESTADO ARTICULADO MATERIA
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(am).pk,
                    object_id       = am.id,
                    object_repr     = force_str(am),
                    action_flag     = CHANGE,
                    change_message  = 'Cambia Estado Articulada(' + client_address + ')'  )

                return HttpResponseRedirect("/mallas?action=edit&id="+str(am.malla.id))

            else:
                return HttpResponseRedirect("/mallas")


        else:
            carreras = Carrera.objects.filter(grupocoordinadorcarrera__group__in=request.user.groups.all()).distinct().order_by('nombre')
            data['mallas'] = Malla.objects.filter(carrera__in=carreras).order_by('carrera__nombre','-inicio')
            return render(request ,"mallas/mallasbs.html" ,  data)