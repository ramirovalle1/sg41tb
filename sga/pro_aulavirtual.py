import sys
import json
from decimal import Decimal
from django.db.models import Q
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.template.loader import get_template
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from decorators import secure_module
from django.forms import model_to_dict
from django.core.exceptions import ObjectDoesNotExist
from sga.commonviews import log_audit_action
from sga.funciones import null_to_decimal, actualizar_nota_cuadro_calificacion
from django.db import transaction
from django.db.models import Count, PROTECT, Sum, Avg, Min, Max, F, OuterRef, Subquery, FloatField, Exists


@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    from .models import Profesor
    from sga.commonviews import addUserData
    data = {}
    addUserData(request, data)
    persona = request.session['persona']
    data['profesor'] = profesor = Profesor.objects.get(persona=persona)
    periodo = request.session['periodo']
    if request.method == 'POST':
        action = request.POST['action']
        if action == 'traer_alumnos_eva':
            from sga.models import Materia, MateriaAsignada
            try:
                id = request.POST.get('id', 0)
                try:
                    materia = Materia.objects.get(pk=id)
                except ObjectDoesNotExist:
                    raise NameError(u"No se encontro la materia")
                estudiantes = MateriaAsignada.objects.filter(materia=materia).order_by('matricula__inscripcion__persona__apellido1', 'matricula__inscripcion__persona__apellido2', 'matricula__inscripcion__persona__nombres')
                # if DEBUG:
                # estudiantes = estudiantes.filter(matricula__inscripcion__persona__cedula__in=['0953492162', '0929047454', '0955363775'])
                # estudiantes = estudiantes.filter(matricula__inscripcion__persona__cedula__in=['0953492162'])
                primerestudiante = estudiantes.first()
                bandera = True
                modelo_mood = ''
                modelo_sga = ''
                listaenviar = []
                for estudiante in estudiantes.order_by('matricula__inscripcion__persona__apellido1'):
                    listaenviar.append({'id': estudiante.id,
                                        'apellido1': estudiante.matricula.inscripcion.persona.apellido1,
                                        'apellido2': estudiante.matricula.inscripcion.persona.apellido2,
                                        'nombres': estudiante.matricula.inscripcion.persona.nombres,
                                        })
                return JsonResponse({"isSuccess": True, "cantidad": len(listaenviar), "inscritos": listaenviar})
            except Exception as ex:
                return JsonResponse({"isSuccess": False, "message": f"Error al obtener los datos. {ex.__str__()}"})

        elif action == 'traer_nota_individual':
            from sga.models import Materia, MateriaAsignada
            try:
                idi = request.POST.get('idi', 0)
                idm = request.POST.get('idm', 0)
                try:
                    eMateria = Materia.objects.get(pk=idm)
                except ObjectDoesNotExist:
                    raise NameError(u"No se encontro la materia")
                try:
                    eMateriaAsignada = MateriaAsignada.objects.get(pk=idi)
                except ObjectDoesNotExist:
                    raise NameError(u"No se encontro la matricula asignada")
                notas_eva = eMateria.notas_de_moodle(eMateriaAsignada.matricula.inscripcion.persona)
                if len(notas_eva):
                    for nota_eva in notas_eva:
                        campo = eMateriaAsignada.campo(nota_eva['campo'].upper().strip())
                        if type(nota_eva['nota']) is Decimal:
                            if null_to_decimal(campo.valor) != float(nota_eva['nota']) or (eMateriaAsignada.asistenciafinal < campo.detallemodeloevaluativo.modelo.asistencia_aprobar):
                                result = actualizar_nota_cuadro_calificacion(eMateriaAsignada.id, nota_eva['campo'].upper().strip(), nota_eva['nota'])
                                isSuccess = result.get('isSuccess', False)
                                message = result.get('message', 'Ocurrio un error en el proceso')
                                if not isSuccess:
                                    raise NameError(message)
                        else:
                            if null_to_decimal(campo.valor) != float(0) or (eMateriaAsignada.asistenciafinal < campo.detallemodeloevaluativo.modelo.asistencia_aprobar):
                                result = actualizar_nota_cuadro_calificacion(eMateriaAsignada.id, nota_eva['campo'].upper().strip(), nota_eva['nota'])
                                isSuccess = result.get('isSuccess', False)
                                message = result.get('message', 'Ocurrio un error en el proceso')
                                if not isSuccess:
                                    raise NameError(message)
                else:
                    for eDetalleModeloEvaluativo in eMateria.modelo_evaluativo.detallemodeloevaluativo_set.filter(puede_migrar_moodle=True):
                        campo = eMateriaAsignada.campo(eDetalleModeloEvaluativo.nombre)
                        result = actualizar_nota_cuadro_calificacion(eMateriaAsignada.id, eDetalleModeloEvaluativo.nombre, 0)
                        isSuccess = result.get('isSuccess', False)
                        message = result.get('message', 'Ocurrio un error en el proceso')
                        if not isSuccess:
                            raise NameError(message)
                return JsonResponse({"isSuccess": True, "message": f"Se obtuvo la calificación correctamente"})
            except Exception as ex:
                print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
                return JsonResponse({"isSuccess": False, "message": f"Error al obtener los datos. {ex.__str__()}"})

        elif action == 'addSilabo':
            with transaction.atomic():
                try:
                    from .models import PlanAnalitico, Silabo, AprobarSilabo
                    id = request.POST.get('id', 0)
                    try:
                        plananalitico = PlanAnalitico.objects.get(pk=id)
                    except ObjectDoesNotExist:
                        raise NameError(u"No se encontro plan analítico")
                    menssage = "Se creado el Sílabo correctamente"
                    if Silabo.objects.filter(plananalitico=plananalitico, profesor=profesor, materia_id=request.POST.get('idm')).exists():
                        return JsonResponse({"isSuccess": False, "message": u"Ya existe un Sílabo con las mismas caracteristicas con este plan analítico: %s" % plananalitico})
                    silabo = Silabo(plananalitico=plananalitico,
                                    profesor=profesor,
                                    materia_id=request.POST.get('idm'),
                                    estado=1
                                    )
                    silabo.save()
                    aprobarSilabo = AprobarSilabo(silabo=silabo,
                                                  observacion='Creado',
                                                  fecha=datetime.now(),
                                                  persona=profesor.persona,
                                                  estadoaprobacion=1)
                    aprobarSilabo.save()
                    return JsonResponse({"isSuccess": True, "message": menssage})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"isSuccess": False, "message": u"Error al procesar los datos: %s" % ex})

        elif action == 'delSilabo':
            with transaction.atomic():
                try:
                    from .models import Silabo
                    id = request.POST.get('id', 0)
                    try:
                        silabo = Silabo.objects.get(pk=id)
                    except ObjectDoesNotExist:
                        raise NameError(u"No existe Sílabo a eliminar")
                    silabo.delete()
                    return JsonResponse({"isSuccess": True, "message": u"Se elimino correctamente el Sílabo"})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"isSuccess": False, "message": u"Error al eliminar el Sílabo: %s" % ex})

        elif action == 'addPlanificacionSemanal':
            with transaction.atomic():
                try:
                    from .models import Silabo, SilaboSemanal, CronograAcademicoDetalle, DetalleSilaboSemanalTema, DetalleSilaboSemanalSubTema, RecursosDidacticosSemanal
                    from .forms import SilaboSemanalForm
                    form = SilaboSemanalForm(request.POST)
                    errors_frm = {}
                    if not form.is_valid():
                        errors_frm = form.toArray()
                        raise NameError("Debe ingresar la información en todos los campos.")
                    ids = request.POST.get('ids', 0)
                    idc = request.POST.get('idc', 0)
                    try:
                        silabo = Silabo.objects.get(pk=ids)
                    except ObjectDoesNotExist:
                        raise NameError(u"No se encontró el sílabo")
                    try:
                        cronograma = CronograAcademicoDetalle.objects.get(pk=idc)
                    except ObjectDoesNotExist:
                        raise NameError(u"No se encontró el cronograma académico")
                    """Silabo semanal"""
                    silabosemana = SilaboSemanal(silabo_id=silabo.id,
                                                 numsemana=cronograma.numsemana,
                                                 semana=cronograma.inicio.isocalendar()[1],
                                                 fechainiciosemana=cronograma.inicio,
                                                 fechafinsemana=cronograma.fin,
                                                 objetivoaprendizaje=form.cleaned_data['objetivoaprendizaje'],
                                                 enfoque=form.cleaned_data['enfoque'],
                                                 enfoquedos=form.cleaned_data['enfoquedos'],
                                                 enfoquetres=form.cleaned_data['enfoquetres'],
                                                 recursos=form.cleaned_data['recursos'],
                                                 evaluacion=form.cleaned_data['evaluacion'],
                                                 examen=cronograma.examen,
                                                 parcial=cronograma.parcial,
                                                 fecha_creacion=datetime.now(),
                                                 recursotutor = None
                                                 )
                    silabosemana.save()
                    """
                    Registro de temas y subtemas
                    """
                    lista_items1 = json.loads(request.POST['lista_items2'])
                    for item in lista_items1:
                        idt = item.get('id_t', '')
                        try:
                            temasilabosemal = DetalleSilaboSemanalTema.objects.get(silabosemanal=silabosemana, plananaliticotema_id=idt)
                        except ObjectDoesNotExist:
                            temasilabosemal = DetalleSilaboSemanalTema(silabosemanal=silabosemana, plananaliticotema_id=idt)
                            temasilabosemal.save()
                        lista_item2 = item.get('subtemas')
                        for item_subt in lista_item2:
                            idst = item_subt.get('id_st')
                            try:
                                subtemasilabosemal = DetalleSilaboSemanalSubTema.objects.get(silabosemanal=silabosemana, plananaliticosubtema_id=idst)
                            except ObjectDoesNotExist:
                                subtemasilabosemal = DetalleSilaboSemanalSubTema(silabosemanal=silabosemana, plananaliticosubtema_id=idst)
                                subtemasilabosemal.save()
                    """
                    Registro de recursos didacticos
                    """
                    lista_items2 = json.loads(request.POST['lista_items1'])
                    for item in lista_items2:
                        descripcion = item.get('nombreCorto')
                        enlace = item.get('enlace')
                        try:
                            recurso = RecursosDidacticosSemanal.objects.get(silabosemanal=silabosemana, descripcion=descripcion)
                        except ObjectDoesNotExist:
                            recurso = RecursosDidacticosSemanal(silabosemanal=silabosemana, descripcion=descripcion, link=enlace)
                            recurso.save()
                    return JsonResponse({"isSuccess": True, "message": u"Se agrego con exito la semana # %s (%s - %s)"% (silabosemana.numsemana, silabosemana.fechainiciosemana, silabosemana.fechafinsemana)})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"isSuccess": False, "message": u"Error al adicionar una semana del Sílabo: %s" % ex})

        elif action == 'editPlanificacionSemanal':
            with transaction.atomic():
                try:
                    from .models import Silabo, SilaboSemanal, CronograAcademicoDetalle, DetalleSilaboSemanalTema, DetalleSilaboSemanalSubTema, RecursosDidacticosSemanal
                    from .forms import SilaboSemanalForm
                    form = SilaboSemanalForm(request.POST)
                    if not form.is_valid():
                        raise NameError("Debe ingresar la información en todos los campos.")
                    ids = request.POST.get('ids', 0)
                    idc = request.POST.get('idc', 0)
                    try:
                        silabosemanal = SilaboSemanal.objects.get(pk=ids)
                    except ObjectDoesNotExist:
                        raise NameError(u"No se encontró el sílabo semanal")
                    try:
                        cronograma = CronograAcademicoDetalle.objects.get(pk=idc)
                    except ObjectDoesNotExist:
                        raise NameError(u"No se encontró el cronograma académico")
                    """Silabo semanal"""
                    silabosemanal.numsemana=cronograma.numsemana
                    silabosemanal.semana=cronograma.inicio.isocalendar()[1]
                    silabosemanal.fechainiciosemana=cronograma.inicio
                    silabosemanal.fechafinsemana=cronograma.fin
                    silabosemanal.objetivoaprendizaje=form.cleaned_data['objetivoaprendizaje']
                    silabosemanal.enfoque=form.cleaned_data['enfoque']
                    silabosemanal.enfoquedos=form.cleaned_data['enfoquedos']
                    silabosemanal.enfoquetres=form.cleaned_data['enfoquetres']
                    silabosemanal.recursos=form.cleaned_data['recursos']
                    silabosemanal.evaluacion=form.cleaned_data['evaluacion']
                    silabosemanal.examen=cronograma.examen
                    silabosemanal.parcial=cronograma.parcial
                    silabosemanal.save()
                    """
                    Registro de temas y subtemas
                    """
                    lista_temas, lista_subtemas = [], []
                    lista_items1 = json.loads(request.POST['lista_items2'])
                    for item in lista_items1:
                        idt = item.get('id_t', '')
                        lista_temas.append(idt)
                        try:
                            temasilabosemal = DetalleSilaboSemanalTema.objects.get(silabosemanal=silabosemanal, plananaliticotema_id=idt)
                        except ObjectDoesNotExist:
                            temasilabosemal = DetalleSilaboSemanalTema(silabosemanal=silabosemanal, plananaliticotema_id=idt)
                            temasilabosemal.save()
                        lista_item2 = item.get('subtemas')
                        for item_subt in lista_item2:
                            idst = item_subt.get('id_st')
                            lista_subtemas.append(idst)
                            try:
                                subtemasilabosemal = DetalleSilaboSemanalSubTema.objects.get(silabosemanal=silabosemanal, plananaliticosubtema_id=idst)
                            except ObjectDoesNotExist:
                                subtemasilabosemal = DetalleSilaboSemanalSubTema(silabosemanal=silabosemanal, plananaliticosubtema_id=idst)
                                subtemasilabosemal.save()
                    """Eliminar temas y subtemas no seleccionados"""
                    DetalleSilaboSemanalTema.objects.filter(silabosemanal=silabosemanal).exclude(plananaliticotema_id__in=lista_temas).delete()
                    DetalleSilaboSemanalSubTema.objects.filter(silabosemanal=silabosemanal).exclude(plananaliticosubtema_id__in=lista_subtemas).delete()
                    """
                    Registro de recursos didacticos
                    """
                    lista_items2 = json.loads(request.POST['lista_items1'])
                    for item in lista_items2:
                        descripcion = item.get('nombreCorto')
                        enlace = item.get('enlace')
                        try:
                            recurso = RecursosDidacticosSemanal.objects.get(silabosemanal=silabosemanal, descripcion=descripcion, link=enlace)
                        except ObjectDoesNotExist:
                            recurso = RecursosDidacticosSemanal(silabosemanal=silabosemanal, descripcion=descripcion, link=enlace)
                            recurso.save()
                    return JsonResponse({"isSuccess": True, "message": u"Se actualizo con exito la semana # %s (%s - %s)"% (silabosemanal.numsemana, silabosemanal.fechainiciosemana, silabosemanal.fechafinsemana)})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"isSuccess": False, "message": u"Error al actualizar la semana del Sílabo: %s" % ex})

        elif action == 'delPlanificacionSemanal':
            with transaction.atomic():
                try:
                    from .models import SilaboSemanal
                    id = request.POST.get('id', 0)
                    try:
                        silabosemanal = SilaboSemanal.objects.get(pk=id)
                    except ObjectDoesNotExist:
                        raise NameError(u"No existe la semana planificada")
                    silabosemanal.delete()
                    return JsonResponse({"isSuccess": True, "message": u"Se elimino correctamente la semana planificada"})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"isSuccess": False, "message": u"Error al eliminar la semana planificada: %s" % ex})

        elif action == 'changeOjetivoTema':
            with transaction.atomic():
                try:
                    from .models import DetalleSilaboSemanalTema
                    id = request.POST.get('id', 0)
                    objetivoaprendizaje = request.POST.get('obj', '')
                    try:
                        detalleTema = DetalleSilaboSemanalTema.objects.get(pk=id)
                    except ObjectDoesNotExist:
                        raise NameError(u"No existe el tema planificado")
                    detalleTema.objetivoaprendizaje = objetivoaprendizaje
                    detalleTema.save()
                    return JsonResponse({"isSuccess": True, "message": u"Se actualizo correctamente  el objetivo de aprendizaje del tema %s" % detalleTema.plananaliticotema})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"isSuccess": False, "message": u"Error al el objetivo de aprendizaje: %s" % ex})

        elif action == 'editEnfoqueMetodologico':
            with transaction.atomic():
                try:
                    from .models import SilaboSemanal
                    from .forms import EnfoqueMetodologicoForm

                    f = None
                    id = request.POST.get('id', 0)
                    try:
                        eSilaboSemanal = SilaboSemanal.objects.get(pk=id)
                    except ObjectDoesNotExist:
                        raise NameError(u"No existe semana planificada")
                    f = EnfoqueMetodologicoForm(request.POST)
                    if not f.is_valid():
                        f.addErrors(f.errors.get_json_data(escape_html=True))
                        raise NameError("Debe ingresar la información en todos los campos.")
                    eSilaboSemanal.enfoque = f.cleaned_data['inicio']
                    eSilaboSemanal.enfoquedos = f.cleaned_data['desarrollo']
                    eSilaboSemanal.enfoquetres = f.cleaned_data['cierre']
                    eSilaboSemanal.save()
                    return JsonResponse({"isSuccess": True, "message": u"Se actualizo correctamente  el enfoque metodologico de la semana %s" % eSilaboSemanal})
                except Exception as ex:
                    transaction.set_rollback(True)
                    forms = f.toArray() if f else {}
                    return JsonResponse(
                        {"isSuccess": False, 'message': u'Error al guardar los datos %s' % ex, "forms": forms})

        elif action == 'changeRecurso':
            with transaction.atomic():
                try:
                    from .models import SilaboSemanal
                    id = request.POST.get('id', 0)
                    recursos = request.POST.get('rec', 0)
                    try:
                        eSilaboSemanal = SilaboSemanal.objects.get(pk=id)
                    except ObjectDoesNotExist:
                        raise NameError(u"No existe la semana planificada")
                    eSilaboSemanal.recursos = recursos
                    eSilaboSemanal.save()
                    return JsonResponse({"isSuccess": True, "message": u"Se actualizó correctamente los recursos didácticos de la semana %s" % eSilaboSemanal})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"isSuccess": False, "message": u"Error al actualizar los recursos didácticos: %s" % ex})

        elif action == 'viewListaRecursoLink':
            try:
                from .models import SilaboSemanal
                if 'id' in request.POST:
                    data['title'] = u'Imprortar sílabos de otros periodos'
                    data['semana'] = SilaboSemanal.objects.get(pk=int(request.POST['id']))
                    template = get_template("pro_aulavirtual/listalinks.html")
                    json_content = template.render(data)
                    return JsonResponse({"isSuccess": True, 'data': json_content})
                else:
                    return JsonResponse({"isSuccess": True, "message": u"Error al obtener los datos de recursos didácticos (link)"})
            except Exception as ex:
                return JsonResponse({"isSuccess": False, "message": u"Error al consultar los datos de recursos didácticos (link): %s" % ex})

        elif action == 'listarrecursolink':
            try:
                from .models import SilaboSemanal
                if 'id' in request.POST:
                    listalink = []
                    silabosemana = SilaboSemanal.objects.get(pk=request.POST['id'])
                    for link in silabosemana.recursosdidacticossemanal_set.all():
                        listalink.append([link.id, str(link), str(link.link)])
                    data = {"isSuccess": True, 'listalink': listalink}
                    return JsonResponse(data)
                else:
                    return JsonResponse({"isSuccess": True, "message": u"Error al obtener los datos de recursos didácticos (link)"})
            except Exception as ex:
                return JsonResponse({"isSuccess": False, "message": u"Error al consultar los datos de recursos didácticos (link): %s" % ex})

        elif action == 'editrecursolink':
            with transaction.atomic():
                try:
                    from .models import SilaboSemanal, RecursosDidacticosSemanal
                    if 'id' in request.POST:
                        semana = SilaboSemanal.objects.get(pk=int(request.POST['id']))
                        if 'lista_items1' in request.POST:
                            for link in json.loads(request.POST['lista_items1']):
                                if not RecursosDidacticosSemanal.objects.values("id").filter(silabosemanal=semana, descripcion=link['descripcion'].strip(), link=link['link'].strip()).exists():
                                    rlink = RecursosDidacticosSemanal(silabosemanal=semana,
                                                                      descripcion=str(link['descripcion'].strip()),
                                                                      link=str(link['link'].strip()))
                                    rlink.save(request)
                            listalink = []
                            for link in json.loads(request.POST['lista_items1']):
                                if semana.recursosdidacticossemanal_set.filter(descripcion=link['descripcion'].strip(), link=link['link'].strip()).exists():
                                    listalink.append(semana.recursosdidacticossemanal_set.filter(descripcion=link['descripcion'].strip(), link=link['link'].strip())[0].id)
                            if semana.recursosdidacticossemanal_set.all().exclude(id__in=listalink):
                                for link in semana.recursosdidacticossemanal_set.all().exclude(id__in=listalink):
                                    semana.recursosdidacticossemanal_set.all().exclude(id__in=listalink).delete()
                            return JsonResponse({"isSuccess": True, "message": u"Se actualizó correctamente los recursos didácticos link de la semana %s" % semana})
                    else:
                        return JsonResponse({"isSuccess": False, "message": u"Error al actualizar los recursos didácticos link de la semana"})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"isSuccess": False, "message": u"Error al actualizar los recursos didácticos: %s" % ex})

        elif action == 'delrecursolink':
            with transaction.atomic():
                try:
                    from .models import RecursosDidacticosSemanal
                    id = request.POST.get('id', 0)
                    try:
                        recurso = RecursosDidacticosSemanal.objects.get(pk=id)
                    except ObjectDoesNotExist:
                        raise NameError(u"No existe el recurso didactico link")
                    recurso.delete()
                    return JsonResponse({"isSuccess": True, "message": u"Se elimino correctamente la recurso link"})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"isSuccess": False, "message": u"Error al eliminar el recurso : %s" % ex})

        # Recursos de la semana
        elif action == 'addDiapositivaVirtual':
            with transaction.atomic():
                try:
                    from .models import SilaboSemanal, DiapositivaSilaboSemanal
                    from .forms import DiapositivaSilaboSemanalForm
                    from .funciones import generar_nombre
                    f = None
                    f = DiapositivaSilaboSemanalForm(request.POST, request.FILES)
                    f.set_tipomaterial(int(request.POST.get('tipomaterial', '1')), True)
                    if not f.is_valid():
                        f.addErrors(f.errors.get_json_data(escape_html=True))
                        raise NameError("Debe ingresar la información en todos los campos.")
                    ids = request.POST.get("id")
                    try:
                        silabosemanal = SilaboSemanal.objects.get(pk=ids)
                    except ObjectDoesNotExist:
                        raise NameError(u"No existe el la semana planificada en el sílado para esta materia")
                    if DiapositivaSilaboSemanal.objects.values("id").filter(silabosemanal=silabosemanal, nombre=f.cleaned_data['nombre']).exists():
                        raise NameError("No se puede actualizar la presentación debido que ya existe un registro con la misma descripción en la semana, revise y vuelva.")

                    tipomaterial = int(f.cleaned_data['tipomaterial'])
                    archivodiapositiva = None
                    url = None
                    if tipomaterial == 1:
                        archivodiapositiva = request.FILES['archivodiapositiva']
                        archivodiapositiva._name = generar_nombre("archivopresentacion", archivodiapositiva._name)
                    else:
                        url = f.cleaned_data['url']

                    diapositiva = DiapositivaSilaboSemanal(silabosemanal_id=ids,
                                                           nombre=f.cleaned_data['nombre'],
                                                           estado_id=1,
                                                           tipomaterial=f.cleaned_data['tipomaterial'],
                                                           descripcion=f.cleaned_data['descripcion'],
                                                           url=url,
                                                           archivodiapositiva=archivodiapositiva
                                                           )
                    diapositiva.save()
                    diapositiva.historial_aprobacion_save(persona.id)
                    diapositiva.estado_id = 2
                    diapositiva.save()
                    diapositiva.historial_aprobacion_save(persona.id, observacion='Cambio de estado')
                    log_audit_action(request, diapositiva, f'Se registro una nueva presentación en la semana {silabosemanal.__str__()} ')
                    return JsonResponse({"isSuccess": True, "message": "Se actualizó correctamente lapresentación en la semana %s" % silabosemanal})
                except Exception as ex:
                    transaction.set_rollback(True)
                    forms = f.toArray() if f else {}
                    return JsonResponse({"isSuccess": False, 'message': u'Error al guardar los datos %s' % ex, "forms": forms})

        elif action == 'editDiapositivaVirtual':
            with transaction.atomic():
                try:
                    from .models import SilaboSemanal, DiapositivaSilaboSemanal
                    from .forms import DiapositivaSilaboSemanalForm
                    from .funciones import generar_nombre
                    from moodle.recursos import GestionMoodle
                    f = None
                    f = DiapositivaSilaboSemanalForm(request.POST, request.FILES)
                    f.set_tipomaterial(int(request.POST.get('tipomaterial', '1')))
                    if not f.is_valid():
                        f.addErrors(f.errors.get_json_data(escape_html=True))
                        raise NameError("Debe ingresar la información en todos los campos.")

                    ids = request.POST.get("ids")
                    try:
                        silabosemanal = SilaboSemanal.objects.get(pk=ids)
                    except ObjectDoesNotExist:
                        raise NameError(u"No existe el la semana planificada en el sílado para esta materia")
                    id = request.POST.get("id")
                    try:
                        diapositiva = DiapositivaSilaboSemanal.objects.get(pk=id)
                    except ObjectDoesNotExist:
                        raise NameError(u"No existe la presentación")
                    if DiapositivaSilaboSemanal.objects.values("id").filter(silabosemanal=silabosemanal, nombre=f.cleaned_data['nombre']).exclude(id=diapositiva.id).exists():
                        raise NameError("No se puede actualizar la presentación debido que ya existe un registro con la misma descripción en la semana, revise y vuelva.")
                    tipomaterial = int(f.cleaned_data['tipomaterial'])
                    if tipomaterial == 1:
                        if not 'archivodiapositiva' in request.FILES and not diapositiva.archivodiapositiva:
                            raise NameError("El archivo de la presentación es obligatorio.")
                        archivodiapositiva = request.FILES.get('archivodiapositiva', None)
                        if archivodiapositiva:
                            archivodiapositiva._name = generar_nombre("archivopresentacion", archivodiapositiva._name)
                            diapositiva.archivodiapositiva = archivodiapositiva
                        diapositiva.url = None
                    else:
                        url = f.cleaned_data['url']
                        diapositiva.url = url
                        diapositiva.archivodiapositiva = None
                    diapositiva.nombre = f.cleaned_data['nombre']
                    if diapositiva.estado_id == 3:
                        diapositiva.estado_id = 2
                    diapositiva.tipomaterial = tipomaterial
                    diapositiva.descripcion = f.cleaned_data['descripcion']
                    diapositiva.save()
                    diapositiva.historial_aprobacion_save(persona.id)
                    if diapositiva.estado_id == 4:
                        eMateria = silabosemanal.silabo.materia
                        eGestionMoodle = GestionMoodle(eMateria=eMateria, ePersona=persona)
                        value, msg = eGestionMoodle.migrar_presentacion(diapositiva)
                        if not value:
                            raise NameError(msg)
                    log_audit_action(request, diapositiva, f'Se actualizo la presentación de la semana {silabosemanal.__str__()} ')
                    return JsonResponse({"isSuccess": True, "message": "Se actualizó correctamente la presentación en la semana %s" % silabosemanal})
                except Exception as ex:
                    transaction.set_rollback(True)
                    forms = f.toArray() if f else {}
                    return JsonResponse({"isSuccess": False, 'message': u'Error al guardar los datos %s' % ex, "forms": forms})

        elif action == 'delDiapositivaVirtual':
            try:
                from .models import DiapositivaSilaboSemanal
                id = request.POST.get('id', 0)
                try:
                    diapositivo = DiapositivaSilaboSemanal.objects.get(pk=id)
                except ObjectDoesNotExist:
                    raise NameError(u"No se encontro la presentacion que quiere eliminar")
                diapositivo.delete()
                return JsonResponse({"isSuccess": True, "message": u"Se elimino correctamente la presentación"})
            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse({"isSuccess": False, "message": u"Error al eliminar el recurso : %s" % ex})

        elif action == 'addCompendioVirtual':
            with transaction.atomic():
                try:
                    from .models import SilaboSemanal, CompendioSilaboSemanal
                    from .forms import CompendioSilaboSemanalForm
                    from .funciones import generar_nombre
                    f = None
                    f = CompendioSilaboSemanalForm(request.POST, request.FILES)
                    f.set_required()
                    if not f.is_valid():
                        f.addErrors(f.errors.get_json_data(escape_html=True))
                        raise NameError("Debe ingresar la información en todos los campos.")
                    ids = request.POST.get("id")
                    try:
                        silabosemanal = SilaboSemanal.objects.get(pk=ids)
                    except ObjectDoesNotExist:
                        raise NameError(u"No existe el la semana planificada en el sílado para esta materia")
                    if CompendioSilaboSemanal.objects.values("id").filter(silabosemanal=silabosemanal, nombre=f.cleaned_data['nombre']).exists():
                        raise NameError(u"No se puede actualizar este compendio debido que ya esiste un registro con la misma descripción en la semana, revise y vuelva.")
                    archivocompendio = request.FILES['archivocompendio']
                    archivocompendio._name = generar_nombre("archivocompendio", archivocompendio._name)
                    archivoplagio = request.FILES['archivoplagio']
                    archivoplagio._name = generar_nombre("archivoplagio", archivoplagio._name)
                    compendio = CompendioSilaboSemanal(silabosemanal=silabosemanal,
                                                       nombre=f.cleaned_data['nombre'],
                                                       estado_id=1,
                                                       descripcion=f.cleaned_data['descripcion'],
                                                       archivocompendio=archivocompendio,
                                                       archivoplagio=archivoplagio,
                                                       porcentaje=f.cleaned_data['porcentaje']
                                                       )
                    compendio.save()
                    compendio.historial_aprobacion_save(persona.id)
                    compendio.estado_id = 2
                    compendio.save()
                    compendio.historial_aprobacion_save(persona.id, observacion='Cambio de estado')
                    log_audit_action(request, compendio,f'Se registro un nuevo convenio en la semana {silabosemanal.__str__()} ')
                    return JsonResponse({"isSuccess": True,
                                         "message": "Se actualizó correctamente el compendio en la semana %s" % silabosemanal})
                except Exception as ex:
                    transaction.set_rollback(True)
                    forms = f.toArray() if f else {}
                    return JsonResponse({"isSuccess": False, 'message': u'Error al guardar los datos %s' % ex, "forms": forms})

        elif action == 'editCompendioVirtual':
            with transaction.atomic():
                try:
                    from .models import SilaboSemanal, CompendioSilaboSemanal
                    from .forms import CompendioSilaboSemanalForm
                    from .funciones import generar_nombre
                    from moodle.recursos import GestionMoodle
                    f = None
                    f = CompendioSilaboSemanalForm(request.POST, request.FILES)
                    if not f.is_valid():
                        f.addErrors(f.errors.get_json_data(escape_html=True))
                        raise NameError("Debe ingresar la información en todos los campos.")

                    ids = request.POST.get("ids")
                    try:
                        silabosemanal = SilaboSemanal.objects.get(pk=ids)
                    except ObjectDoesNotExist:
                        raise NameError(u"No existe el la semana planificada en el sílado para esta materia")

                    id = request.POST.get("id")
                    try:
                        compendio = CompendioSilaboSemanal.objects.get(pk=id)
                    except ObjectDoesNotExist:
                        raise NameError(u"No existe el compendio")
                    if CompendioSilaboSemanal.objects.values("id").filter(silabosemanal=silabosemanal, nombre=f.cleaned_data['nombre']).exclude(id=compendio.id).exists():
                        raise NameError(u"No se puede actualizar este compendio debido que ya esiste un registro con la misma descripción en la semana, revise y vuelva.")
                    if not 'archivocompendio' in request.FILES and not compendio.archivocompendio:
                        raise NameError("El archivo del compendio es obligatorio.")
                    if not 'archivoplagio' in request.FILES and not compendio.archivoplagio:
                        raise NameError("El archivo de plagio del compendio es obligatorio.")
                    archivocompendio = request.FILES.get('archivocompendio', None)
                    if archivocompendio:
                        archivocompendio._name = generar_nombre("archivocompendio", archivocompendio._name)
                        compendio.archivocompendio = archivocompendio
                    archivoplagio = request.FILES.get('archivoplagio', None)
                    if archivoplagio:
                        archivoplagio._name = generar_nombre("archivoplagio", archivoplagio._name)
                        compendio.archivoplagio = archivoplagio
                    compendio.nombre = f.cleaned_data['nombre']
                    compendio.descripcion = f.cleaned_data['descripcion']
                    compendio.porcentaje = f.cleaned_data['porcentaje']
                    if compendio.estado_id == 3:
                        compendio.estado_id = 2
                    compendio.save()
                    compendio.historial_aprobacion_save(persona.id)
                    if compendio.estado_id == 4:
                        eMateria = silabosemanal.silabo.materia
                        eGestionMoodle = GestionMoodle(eMateria=eMateria, ePersona=persona)
                        value, msg = eGestionMoodle.migrar_compendio(compendio)
                        if not value:
                            raise NameError(msg)
                    log_audit_action(request, compendio, f'Actualizó el registro de convenio en la semana {silabosemanal.__str__()} ')
                    return JsonResponse({"isSuccess": True, "message": "Se actualizó correctamente el compendio en la semana %s" % silabosemanal})
                except Exception as ex:
                    transaction.set_rollback(True)
                    forms = f.toArray() if f else {}
                    return JsonResponse({"isSuccess": False, 'message': u'Error al guardar los datos %s' % ex, "forms": forms})

        elif action == 'delCompendioVirtual':
            with transaction.atomic():
                try:
                    from .models import CompendioSilaboSemanal
                    id = request.POST.get('id', 0)
                    try:
                        compendio = CompendioSilaboSemanal.objects.get(pk=id)
                    except ObjectDoesNotExist:
                        raise NameError(u"No existe el recurso a eliminar")
                    compendio.delete()
                    return JsonResponse({"isSuccess": True, "message": u"Se elimino correctamente el compendio"})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"isSuccess": False, "message": u"Error al eliminar el recurso : %s" % ex})

        elif action == 'addVideoMagistralVirtual':
            with transaction.atomic():
                try:
                    from .models import SilaboSemanal, VideoMagistralSilaboSemanal
                    from .forms import VideoMagistralSilaboSemanalForm
                    from .funciones import generar_nombre
                    f = None
                    f = VideoMagistralSilaboSemanalForm(request.POST, request.FILES)
                    f.set_tipomaterial(int(request.POST.get('tipomaterial', '1')), True)
                    if not f.is_valid():
                        f.addErrors(f.errors.get_json_data(escape_html=True))
                        raise NameError("Debe ingresar la información en todos los campos.")
                    video = None
                    url = None

                    ids = request.POST.get("id")
                    try:
                        silabosemanal = SilaboSemanal.objects.get(pk=ids)
                    except ObjectDoesNotExist:
                        raise NameError(u"No existe el la semana planificada en el sílado para esta materia")
                    nombre =f'VIDEOMAGISTRAL_S {silabosemanal.numsemana}'
                    if VideoMagistralSilaboSemanal.objects.values("id").filter(silabosemanal=silabosemanal, nombre=nombre).exists():
                        raise NameError(u"No se puede actualizar este video magistral debido que ya esiste un registro con la misma descripción en la semana, revise y vuelva.")
                    tipomaterial = int(f.cleaned_data['tipomaterial'])
                    if tipomaterial == 1:
                        video = request.FILES['archivovideo']
                        video._name = generar_nombre("archivopresentacionvideomagistral", video._name)
                    else:
                        url = f.cleaned_data['url']

                    vidmagistral = VideoMagistralSilaboSemanal(silabosemanal=silabosemanal,
                                                               nombre=nombre,
                                                               estado_id=1,
                                                               tipomaterial=f.cleaned_data['tipomaterial'],
                                                               tipovideo=f.cleaned_data['tipovideo'],
                                                               tipograbacion=f.cleaned_data['tipograbacion'],
                                                               descripcion=f.cleaned_data['descripcion'],
                                                               url=url,
                                                               archivovideo=video,
                                                               validado=True
                                                               )
                    vidmagistral.save()
                    vidmagistral.historial_aprobacion_save(persona.id)
                    vidmagistral.estado_id = 2
                    vidmagistral.save()
                    vidmagistral.historial_aprobacion_save(persona.id, observacion='Cambio de estado')
                    log_audit_action(request, vidmagistral, f'Se registro un nuevo video magistral de la semana {silabosemanal.__str__()} ')
                    return JsonResponse({"isSuccess": True, "message": "Se actualizó correctamente el video gaistral en la semana %s" % silabosemanal})
                except Exception as ex:
                    transaction.set_rollback(True)
                    forms = f.toArray() if f else {}
                    return JsonResponse({"isSuccess": False, 'message': u'Error al guardar los datos %s' % ex, "forms": forms})

        elif action == 'editVideoMagistralVirtual':
            with transaction.atomic():
                try:
                    from .models import SilaboSemanal, VideoMagistralSilaboSemanal
                    from .forms import VideoMagistralSilaboSemanalForm
                    from .funciones import generar_nombre
                    from moodle.recursos import GestionMoodle
                    f = None
                    f = VideoMagistralSilaboSemanalForm(request.POST, request.FILES)
                    f.set_tipomaterial(int(request.POST.get('tipomaterial', '1')))
                    if not f.is_valid():
                        f.addErrors(f.errors.get_json_data(escape_html=True))
                        raise NameError("Debe ingresar la información en todos los campos.")
                    ids = request.POST.get("ids")
                    try:
                        silabosemanal = SilaboSemanal.objects.get(pk=ids)
                    except ObjectDoesNotExist:
                        raise NameError(u"No existe el la semana planificada en el sílado para esta materia")
                    id = request.POST.get("id")
                    try:
                        videomagistral = VideoMagistralSilaboSemanal.objects.get(pk=id)
                    except ObjectDoesNotExist:
                        raise NameError(u"No existe el video magistral")
                    nombre = f'VIDEOMAGISTRAL_S {silabosemanal.numsemana}'
                    if VideoMagistralSilaboSemanal.objects.values("id").filter(silabosemanal=silabosemanal, nombre=nombre).exclude(id=videomagistral.id).exists():
                        raise NameError(u"No se puede actualizar este video magistral debido que ya esiste un registro con la misma descripción en la semana, revise y vuelva.")
                    tipomaterial = int(f.cleaned_data['tipomaterial'])
                    if tipomaterial == 1:
                        if not 'archivovideo' in request.FILES and not videomagistral.archivovideo:
                            raise NameError("El archivo del video es obligatorio.")
                        video = request.FILES.get('archivovideo', None)
                        if video:
                            video._name = generar_nombre("archivopresentacionvideomagistral", video._name)
                            videomagistral.archivovideo = video
                        videomagistral.url = None
                    else:
                        videomagistral.url = f.cleaned_data['url']
                        videomagistral.archivovideo = None
                    videomagistral.nombre = nombre
                    videomagistral.tipomaterial = int(f.cleaned_data['tipomaterial'])
                    videomagistral.tipovideo = int(f.cleaned_data['tipovideo'])
                    videomagistral.tipograbacion = int(f.cleaned_data['tipograbacion'])
                    videomagistral.descripcion = f.cleaned_data['descripcion']
                    if videomagistral.estado_id == 3:
                        videomagistral.estado_id = 2
                    videomagistral.save()
                    videomagistral.historial_aprobacion_save(persona.id, u'Actualizo el recurso de video magistral')
                    if videomagistral.estado_id == 4:
                        eMateria = silabosemanal.silabo.materia
                        eGestionMoodle = GestionMoodle(eMateria=eMateria, ePersona=persona)
                        value, msg = eGestionMoodle.migrar_video_magistral(videomagistral)
                        if not value:
                            raise NameError(msg)
                    log_audit_action(request, videomagistral,f'Se Modificado un nuevo video magistral de la semana {silabosemanal.__str__()} ')
                    return JsonResponse({"isSuccess": True, "message": "Se actualizó correctamente el video gaistral en la semana %s" % silabosemanal})
                except Exception as ex:
                    transaction.set_rollback(True)
                    forms = f.toArray() if f else {}
                    return JsonResponse({"isSuccess": False, 'message': u'Error al guardar los datos %s' % ex, "forms": forms})

        elif action == 'delVideoMagistralVirtual':
            with transaction.atomic():
                try:
                    from .models import VideoMagistralSilaboSemanal
                    id = request.POST.get('id', 0)
                    try:
                        videomagistral = VideoMagistralSilaboSemanal.objects.get(pk=id)
                    except ObjectDoesNotExist:
                        raise NameError(u"No existe el recurso a eliminar")
                    videomagistral.delete()
                    return JsonResponse({"isSuccess": True, "message": u"Se elimino correctamente la recurso link"})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"isSuccess": False, "message": u"Error al eliminar el recurso : %s" % ex})

        elif action == 'addGuiaEstudianteVirtual':
            with transaction.atomic():
                try:
                    from .models import SilaboSemanal, GuiaEstudianteSilaboSemanal
                    from .forms import GuiaEstudianteSilaboSemanalForm
                    from .funciones import generar_nombre
                    f = None
                    f = GuiaEstudianteSilaboSemanalForm(request.POST, request.FILES)
                    f.set_required()
                    if not f.is_valid():
                        f.addErrors(f.errors.get_json_data(escape_html=True))
                        raise NameError("Debe ingresar la información en todos los campos.")

                    ids = request.POST.get("id")
                    try:
                        silabosemanal = SilaboSemanal.objects.get(pk=ids)
                    except ObjectDoesNotExist:
                        raise NameError(u"No existe el la semana planificada en el sílado para esta materia")
                    if GuiaEstudianteSilaboSemanal.objects.values("id").filter(silabosemanal=silabosemanal, nombre=f.cleaned_data['nombre']).exists():
                        raise NameError(u"No se puede crear este guía de estudiante debido que ya esiste un registro con la misma descripción en la semana, revise y vuelva.")

                    archivoguiaestudiante = request.FILES['archivoguiaestudiante']
                    archivoguiaestudiante._name = generar_nombre("archivoguiaestudioest", archivoguiaestudiante._name)

                    guiaEstudianteSilaboSemanal = GuiaEstudianteSilaboSemanal(silabosemanal=silabosemanal,
                                                                              nombre=f.cleaned_data['nombre'],
                                                                              estado_id=1,
                                                                              objetivo=f.cleaned_data['objetivo'],
                                                                              archivoguiaestudiante=archivoguiaestudiante
                                                                              )
                    guiaEstudianteSilaboSemanal.save()
                    guiaEstudianteSilaboSemanal.historial_aprobacion_save(persona.id)
                    guiaEstudianteSilaboSemanal.estado_id = 2
                    guiaEstudianteSilaboSemanal.save()
                    guiaEstudianteSilaboSemanal.historial_aprobacion_save(persona.id, observacion='Cambio de estado')
                    log_audit_action(request, guiaEstudianteSilaboSemanal, f'Se registro una guía de estudiante en la semana {silabosemanal.__str__()} ')
                    return JsonResponse({"isSuccess": True, "message": "Se registro un nuevo registro de guía de estudiante correctamente el compendio en la semana %s" % silabosemanal})
                except Exception as ex:
                    transaction.set_rollback(True)
                    forms = f.toArray() if f else {}
                    return JsonResponse({"isSuccess": False, 'message': u'Error al guardar los datos %s' % ex, "forms": forms})

        elif action == 'editGuiaEstudianteVirtual':
            with transaction.atomic():
                try:
                    from .models import SilaboSemanal, GuiaEstudianteSilaboSemanal
                    from .forms import GuiaEstudianteSilaboSemanalForm
                    from .funciones import generar_nombre
                    from moodle.recursos import GestionMoodle
                    f = None
                    f = GuiaEstudianteSilaboSemanalForm(request.POST, request.FILES)
                    if not f.is_valid():
                        f.addErrors(f.errors.get_json_data(escape_html=True))
                        raise NameError("Debe ingresar la información en todos los campos.")

                    ids = request.POST.get("ids")
                    try:
                        silabosemanal = SilaboSemanal.objects.get(pk=ids)
                    except ObjectDoesNotExist:
                        raise NameError(u"No existe el la semana planificada en el sílado para esta materia")

                    id = request.POST.get("id")
                    try:
                        guiaEstudianteSilaboSemanal = GuiaEstudianteSilaboSemanal.objects.get(pk=id)
                    except ObjectDoesNotExist:
                        raise NameError(u"No existe el compendio")

                    if GuiaEstudianteSilaboSemanal.objects.values("id").filter(silabosemanal=silabosemanal, nombre=f.cleaned_data['nombre']).exclude(id=guiaEstudianteSilaboSemanal.id).exists():
                        raise NameError(u"No se puede crear este guía de estudiante debido que ya esiste un registro con la misma descripción en la semana, revise y vuelva.")
                    if not 'archivoguiaestudiante' in request.FILES and not guiaEstudianteSilaboSemanal.archivoguiaestudiante:
                        raise NameError("El archivo de la guía de estudiante es obligatorio.")
                    if 'archivoguiaestudiante' in request.FILES:
                        archivoguiaestudiante = request.FILES['archivoguiaestudiante']
                        archivoguiaestudiante._name = generar_nombre("archivocompendio", archivoguiaestudiante._name)
                        guiaEstudianteSilaboSemanal.archivoguiaestudiante = archivoguiaestudiante
                    guiaEstudianteSilaboSemanal.nombre = f.cleaned_data['nombre']
                    guiaEstudianteSilaboSemanal.objetivo = f.cleaned_data['objetivo']
                    if guiaEstudianteSilaboSemanal.estado_id == 3:
                        guiaEstudianteSilaboSemanal.estado_id = 2
                    guiaEstudianteSilaboSemanal.save()
                    guiaEstudianteSilaboSemanal.historial_aprobacion_save(persona.id, u'Actualizo el recurso de guia de estudiante')
                    if guiaEstudianteSilaboSemanal.estado_id == 4:
                        eMateria = silabosemanal.silabo.materia
                        eGestionMoodle = GestionMoodle(eMateria=eMateria, ePersona=persona)
                        value, msg = eGestionMoodle.migrar_guia_estudiante(guiaEstudianteSilaboSemanal)
                        if not value:
                            raise NameError(msg)
                    log_audit_action(request, guiaEstudianteSilaboSemanal, f'Actualizó el registro de la guia de estudio en la semana {silabosemanal.__str__()} ')
                    return JsonResponse({"isSuccess": True, "message": "Se actualizó correctamente la guia de estudiante en la semana %s" % silabosemanal})
                except Exception as ex:
                    transaction.set_rollback(True)
                    forms = f.toArray() if f else {}
                    return JsonResponse({"isSuccess": False, 'message': u'Error al guardar los datos %s' % ex, "forms": forms})

        elif action == 'delGuiaEstudianteVirtual':
            with transaction.atomic():
                try:
                    from .models import GuiaEstudianteSilaboSemanal
                    id = request.POST.get('id', 0)
                    try:
                        guiaEstudianteSilaboSemanalndio = GuiaEstudianteSilaboSemanal.objects.get(pk=id)
                    except ObjectDoesNotExist:
                        raise NameError(u"No existe el recurso a eliminar")
                    guiaEstudianteSilaboSemanalndio.delete()
                    return JsonResponse({"isSuccess": True, "message": u"Se elimino correctamente la guia de estudio"})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"isSuccess": False, "message": u"Error al eliminar el recurso : %s" % ex})

        elif action == 'addTestVirtual':
            with transaction.atomic():
                try:
                    from .models import TestSilaboSemanal, SilaboSemanal
                    from .forms import TestSilaboSemanalForm
                    f = None
                    ids = request.POST.get("id")
                    try:
                        silabosemanal = SilaboSemanal.objects.get(pk=ids)
                    except ObjectDoesNotExist:
                        raise NameError(u"No existe el la semana planificada en el sílado para esta materia")
                    detalles_modelo = silabosemanal.silabo.materia.modelo_evaluativo.detallemodeloevaluativo_set.filter(es_dependiente=False).exclude(alternativa__id__in=[1,2]).order_by('orden')

                    f = TestSilaboSemanalForm(request.POST)
                    f.item_evaluativo(detalles_modelo)
                    if not f.is_valid():
                        f.addErrors(f.errors.get_json_data(escape_html=True))
                        raise NameError("Debe ingresar la información en todos los campos.")
                    num_test = TestSilaboSemanal.objects.only("id").filter(silabosemanal=silabosemanal).count() + 1
                    nombre = f"S{silabosemanal.numsemana}-TEST_{num_test}"
                    if TestSilaboSemanal.objects.filter(silabosemanal=silabosemanal, detallemodelo=f.cleaned_data['detallemodelo'], nombre=nombre).exists():
                        raise NameError(u"Ya existe un test con las mismas características, revise y vuelva a intentarlo ")
                    testSilaboSemanal = TestSilaboSemanal(silabosemanal=silabosemanal,
                                                          detallemodelo=f.cleaned_data['detallemodelo'],
                                                          nombre=nombre,
                                                          estado_id=1,
                                                          instruccion=f.cleaned_data['instruccion'],
                                                          recomendacion=f.cleaned_data['recomendacion'],
                                                          desde=f.cleaned_data['desde'],
                                                          hasta=f.cleaned_data['hasta'],
                                                          vecesintento=f.cleaned_data['vecesintento'],
                                                          tiempoduracion=f.cleaned_data['tiempoduracion'],
                                                          calificar=True,
                                                          navegacion=f.cleaned_data['navegacion'],
                                                          fecha_creacion=datetime.now(),
                                                          fecha_modificacion=datetime.now())
                    testSilaboSemanal.save()
                    testSilaboSemanal.historial_aprobacion_save(persona.id)
                    testSilaboSemanal.estado_id = 2
                    testSilaboSemanal.save()
                    testSilaboSemanal.historial_aprobacion_save(persona.id, observacion='Cambio de estado')
                    log_audit_action(request, testSilaboSemanal, f'Se creó un nuevo test en la semana {silabosemanal.__str__()} ')
                    return JsonResponse({"isSuccess": True, "message": "Se actualizó correctamente el test en la semana %s" % silabosemanal})
                except Exception as ex:
                    transaction.set_rollback(True)
                    forms = f.toArray() if f else {}
                    return JsonResponse({"isSuccess": False, 'message': u'Error al guardar los datos %s' % ex, "forms": forms})

        elif action == 'editTestVirtual':
            with transaction.atomic():
                try:
                    from .models import TestSilaboSemanal, SilaboSemanal
                    from .forms import TestSilaboSemanalForm
                    from moodle.recursos import GestionMoodle
                    f = None
                    ids = request.POST.get("ids")
                    try:
                        silabosemanal = SilaboSemanal.objects.get(pk=ids)
                    except ObjectDoesNotExist:
                        raise NameError(u"No existe el la semana planificada en el sílado para esta materia")
                    detalles_modelo = silabosemanal.silabo.materia.modelo_evaluativo.detallemodeloevaluativo_set.filter(es_dependiente=False).exclude(alternativa__id__in=[1,2]).order_by('orden')
                    f = TestSilaboSemanalForm(request.POST)
                    f.item_evaluativo(detalles_modelo)
                    if not f.is_valid():
                        f.addErrors(f.errors.get_json_data(escape_html=True))
                        raise NameError("Debe ingresar la información en todos los campos.")
                    id = request.POST.get("id")
                    try:
                        testSilaboSemanal = TestSilaboSemanal.objects.get(pk=id)
                    except ObjectDoesNotExist:
                        raise NameError(u"No encontro el foro para editar")

                    if TestSilaboSemanal.objects.filter(silabosemanal=silabosemanal, detallemodelo=f.cleaned_data['detallemodelo'], nombre=testSilaboSemanal.nombre).exclude(id=testSilaboSemanal.id).exists():
                        raise NameError(u"Ya existe un test con las mismas características, revise y vuelva a intentarlo ")

                    testSilaboSemanal.detallemodelo = f.cleaned_data['detallemodelo']
                    testSilaboSemanal.instruccion = f.cleaned_data['instruccion']
                    testSilaboSemanal.recomendacion = f.cleaned_data['recomendacion']
                    testSilaboSemanal.desde = f.cleaned_data['desde']
                    testSilaboSemanal.hasta = f.cleaned_data['hasta']
                    testSilaboSemanal.vecesintento = f.cleaned_data['vecesintento']
                    testSilaboSemanal.tiempoduracion = f.cleaned_data['tiempoduracion']
                    testSilaboSemanal.calificar = True
                    testSilaboSemanal.navegacion = f.cleaned_data['navegacion']
                    testSilaboSemanal.fecha_modificacion = datetime.now()
                    if testSilaboSemanal.estado_id == 3:
                        testSilaboSemanal.estado_id = 2
                    testSilaboSemanal.save()
                    testSilaboSemanal.historial_aprobacion_save(persona.id, f'Actualizo el test')
                    if testSilaboSemanal.estado_id == 4:
                        eMateria = silabosemanal.silabo.materia
                        eGestionMoodle = GestionMoodle(eMateria=eMateria, ePersona=persona)
                        value, msg = eGestionMoodle.migrar_test(testSilaboSemanal)
                        if not value:
                            raise NameError(msg)
                    log_audit_action(request, testSilaboSemanal, f'Editó el test {testSilaboSemanal.nombre} de la semana {silabosemanal.__str__()} ')
                    return JsonResponse({"isSuccess": True, "message": "Se actualizó correctamente el test en la semana %s" % silabosemanal})
                except Exception as ex:
                    transaction.set_rollback(True)
                    forms = f.toArray() if f else {}
                    return JsonResponse({"isSuccess": False, 'message': u'Error al guardar los datos %s' % ex, "forms": forms})

        elif action == 'delTestVirtual':
            with transaction.atomic():
                try:
                    from .models import TestSilaboSemanal
                    id = request.POST.get('id', 0)
                    try:
                        testSilaboSemanal = TestSilaboSemanal.objects.get(pk=id)
                    except ObjectDoesNotExist:
                        raise NameError(u"No existe el recurso a eliminar")
                    testSilaboSemanal.delete()
                    return JsonResponse({"isSuccess": True, "message": f"Se elimino correctamente el test"})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"isSuccess": False, "message": u"Error al eliminar el recurso : %s" % ex})

        elif action == 'addForoVirtual':
            with transaction.atomic():
                try:
                    from .models import ForoSilaboSemanal, SilaboSemanal
                    from .forms import ForoSilaboSemanalForm
                    from .funciones import generar_nombre
                    f = None
                    ids = request.POST.get("ids")
                    try:
                        silabosemanal = SilaboSemanal.objects.get(pk=ids)
                    except ObjectDoesNotExist:
                        raise NameError(u"No existe el la semana planificada en el sílado para esta materia")
                    detalles_modelo = silabosemanal.silabo.materia.modelo_evaluativo.detallemodeloevaluativo_set.filter(es_dependiente=False).exclude(alternativa__id__in=[1,2]).order_by('orden')
                    f = ForoSilaboSemanalForm(request.POST, request.FILES)
                    f.item_evaluativo(detalles_modelo)
                    if not f.is_valid():
                        f.addErrors(f.errors.get_json_data(escape_html=True))
                        raise NameError("Debe ingresar la información en todos los campos.")

                    num_foro = ForoSilaboSemanal.objects.only("id").filter(silabosemanal=silabosemanal).count() + 1
                    nombre = f"S{silabosemanal.numsemana}-FORO_{num_foro}"

                    if ForoSilaboSemanal.objects.filter(silabosemanal=silabosemanal, detallemodelo=f.cleaned_data['detallemodelo'], nombre=nombre).exists():
                        raise NameError(u"Ya existe un foro con las mismas características, revise y vuelva a intentarlo ")

                    archivorubrica = None
                    if 'archivorubrica' in request.FILES:
                        archivorubrica = request.FILES['archivorubrica']
                        archivorubrica._name = generar_nombre("archivorubrica", archivorubrica._name)

                    archivoforo = None
                    if 'archivoforo' in request.FILES:
                        archivoforo = request.FILES['archivoforo']
                        archivoforo._name = generar_nombre("archivoforo", archivoforo._name)

                    foroSilaboSemanal = ForoSilaboSemanal(silabosemanal = silabosemanal,
                                                          detallemodelo = f.cleaned_data['detallemodelo'],
                                                          nombre = nombre,
                                                          estado_id=1,
                                                          instruccion = f.cleaned_data['instruccion'],
                                                          recomendacion = f.cleaned_data['recomendacion'],
                                                          objetivo = f.cleaned_data['objetivo'],
                                                          rubrica = f.cleaned_data['rubrica'],
                                                          desde = f.cleaned_data['desde'],
                                                          hasta = f.cleaned_data['hasta'],
                                                          tipoforo = f.cleaned_data['tipoforo'],
                                                          tipoconsolidacion = f.cleaned_data['tipoconsolidacion'],
                                                          calificar = True,
                                                          archivorubrica = archivorubrica,
                                                          archivoforo = archivoforo,
                                                          fecha_creacion = datetime.now(),
                                                          fecha_modificacion = datetime.now()
                                                          )
                    foroSilaboSemanal.save()
                    foroSilaboSemanal.historial_aprobacion_save(persona.id)
                    foroSilaboSemanal.estado_id = 2
                    foroSilaboSemanal.save()
                    foroSilaboSemanal.historial_aprobacion_save(persona.id, observacion='Cambio de estado')
                    log_audit_action(request, foroSilaboSemanal, f'Se creó un nuevo foro en la semana {silabosemanal.__str__()} ')
                    return JsonResponse({"isSuccess": True, "message": "Se actualizó correctamente el foro en la semana %s" % silabosemanal})
                except Exception as ex:
                    transaction.set_rollback(True)
                    forms = f.toArray() if f else {}
                    return JsonResponse({"isSuccess": False, 'message': u'Error al guardar los datos %s' % ex, "forms": forms})

        elif action == 'editForoVirtual':
            with transaction.atomic():
                try:
                    from .models import ForoSilaboSemanal, SilaboSemanal
                    from .forms import ForoSilaboSemanalForm
                    from .funciones import generar_nombre
                    from moodle.recursos import GestionMoodle
                    f = None
                    ids = request.POST.get("ids")
                    try:
                        silabosemanal = SilaboSemanal.objects.get(pk=ids)
                    except ObjectDoesNotExist:
                        raise NameError(u"No existe el la semana planificada en el sílado para esta materia")
                    detalles_modelo = silabosemanal.silabo.materia.modelo_evaluativo.detallemodeloevaluativo_set.filter(es_dependiente=False).exclude(alternativa__id__in=[1,2]).order_by('orden')
                    f = ForoSilaboSemanalForm(request.POST, request.FILES)
                    f.item_evaluativo(detalles_modelo)
                    if not f.is_valid():
                        f.addErrors(f.errors.get_json_data(escape_html=True))
                        raise NameError("Debe ingresar la información en todos los campos.")

                    id = request.POST.get("id")
                    try:
                        foroSilaboSemanal = ForoSilaboSemanal.objects.get(pk=id)
                    except ObjectDoesNotExist:
                        raise NameError(u"No existe el foro para editar")

                    if ForoSilaboSemanal.objects.filter(silabosemanal=silabosemanal, detallemodelo=f.cleaned_data['detallemodelo'], nombre=foroSilaboSemanal.nombre).exclude(id=foroSilaboSemanal.id).exists():
                        raise NameError(u"Ya existe un foro con las mismas características, revise y vuelva a intentarlo ")

                    if 'archivorubrica' in request.FILES:
                        archivorubrica = request.FILES['archivorubrica']
                        archivorubrica._name = generar_nombre("archivorubrica", archivorubrica._name)
                        foroSilaboSemanal.archivorubrica = archivorubrica

                    if 'archivoforo' in request.FILES:
                        archivoforo = request.FILES['archivoforo']
                        archivoforo._name = generar_nombre("archivoforo", archivoforo._name)
                        foroSilaboSemanal.archivoforo = archivoforo

                    foroSilaboSemanal.detallemodelo = f.cleaned_data['detallemodelo']
                    foroSilaboSemanal.instruccion = f.cleaned_data['instruccion']
                    foroSilaboSemanal.recomendacion = f.cleaned_data['recomendacion']
                    foroSilaboSemanal.objetivo = f.cleaned_data['objetivo']
                    foroSilaboSemanal.rubrica = f.cleaned_data['rubrica']
                    foroSilaboSemanal.desde = f.cleaned_data['desde']
                    foroSilaboSemanal.hasta = f.cleaned_data['hasta']
                    foroSilaboSemanal.calificar = True
                    foroSilaboSemanal.tipoforo = f.cleaned_data['tipoforo']
                    foroSilaboSemanal.tipoconsolidacion = f.cleaned_data['tipoconsolidacion']
                    foroSilaboSemanal.fecha_modificacion = datetime.now()
                    if foroSilaboSemanal.estado_id == 3:
                        foroSilaboSemanal.estado_id = 2
                    foroSilaboSemanal.save()
                    foroSilaboSemanal.historial_aprobacion_save(persona.id, f'Actualizo el foro')
                    if foroSilaboSemanal.estado_id == 4:
                        eMateria = silabosemanal.silabo.materia
                        eGestionMoodle = GestionMoodle(eMateria=eMateria, ePersona=persona)
                        value, msg = eGestionMoodle.migrar_foro(foroSilaboSemanal)
                        if not value:
                            raise NameError(msg)
                    log_audit_action(request, foroSilaboSemanal, f'Editó el foro {foroSilaboSemanal.nombre} de la semana {silabosemanal.__str__()} ')
                    return JsonResponse({"isSuccess": True, "message": "Se actualizó correctamente el foro en la semana %s" % silabosemanal})
                except Exception as ex:
                    transaction.set_rollback(True)
                    forms = f.toArray() if f else {}
                    return JsonResponse({"isSuccess": False, 'message': u'Error al guardar los datos %s' % ex, "forms": forms})

        elif action == 'delForoVirtual':
            with transaction.atomic():
                try:
                    from .models import ForoSilaboSemanal
                    id = request.POST.get('id', 0)
                    try:
                        foroSilaboSemanal = ForoSilaboSemanal.objects.get(pk=id)
                    except ObjectDoesNotExist:
                        raise NameError(u"No existe el recurso a eliminar")
                    foroSilaboSemanal.delete()
                    return JsonResponse({"isSuccess": True, "message": f"Se eliminó correctamente el foro"})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"isSuccess": False, "message": u"Error al eliminar el recurso : %s" % ex})

        elif action == 'addTareaVirtual':
            with transaction.atomic():
                try:
                    from .models import TareaSilaboSemanal, SilaboSemanal
                    from .funciones import generar_nombre
                    from .forms import TareaSilaboSemanalForm
                    from .funciones import generar_nombre
                    f = None
                    ids = request.POST.get("ids")
                    try:
                        silabosemanal = SilaboSemanal.objects.get(pk=ids)
                    except ObjectDoesNotExist:
                        raise NameError(u"No existe el la semana planificada en el sílado para esta materia")
                    detalles_modelo = silabosemanal.silabo.materia.modelo_evaluativo.detallemodeloevaluativo_set.filter(es_dependiente=False).exclude(alternativa__id__in=[1,2]).order_by('orden')
                    f = TareaSilaboSemanalForm(request.POST, request.FILES)
                    f.item_evaluativo(detalles_modelo)
                    if not f.is_valid():
                        f.addErrors(f.errors.get_json_data(escape_html=True))
                        raise NameError("Debe ingresar la información en todos los campos.")

                    tp = int(request.POST.get('tp', 0))
                    if tp == 0:
                        raise NameError("Error el tipo de actividad no existe")

                    verbose = u'Tarea'
                    verbose_nombre = u'TAREA'
                    if tp == 2:
                        verbose = u'Taller'
                        verbose_nombre = u'TALLER'
                    elif tp == 3:
                        verbose = u'Proyecto de investigación'
                        verbose_nombre = u'PROYECTO_INVESTIGACION'
                    elif tp == 4:
                        verbose = u'Análisis de caso'
                        verbose_nombre = u'ANALISIS_CASO'
                    num_tarea = TareaSilaboSemanal.objects.only("id").filter(silabosemanal=silabosemanal, tiporecurso=tp).count() + 1
                    nombre = f"S{silabosemanal.numsemana}-{verbose_nombre}_{num_tarea}"
                    if TareaSilaboSemanal.objects.filter(silabosemanal=silabosemanal, detallemodelo=f.cleaned_data['detallemodelo'], nombre=nombre, tiporecurso=tp).exists():
                        raise NameError(f"Ya existe un/una {verbose.lower()} con las mismas características, revise y vuelva a intentarlo ")

                    archivorubrica, archivotarea = None, None
                    if 'archivorubrica' in request.FILES:
                        archivorubrica = request.FILES['archivorubrica']
                        archivorubrica._name = generar_nombre("archivoRubicaForo", archivorubrica._name)

                    if 'archivotareasilabo' in request.FILES:
                        archivotarea = request.FILES['archivotareasilabo']
                        archivotarea._name = generar_nombre("archivoForo", archivotarea._name)
                    todos = (f.cleaned_data['word'] and f.cleaned_data['pdf'] and f.cleaned_data['excel'] and f.cleaned_data['powerpoint'])
                    tareaSilaboSemanal = TareaSilaboSemanal(silabosemanal=silabosemanal,
                                                            tiporecurso=tp,
                                                            detallemodelo=f.cleaned_data['detallemodelo'],
                                                            nombre=nombre,
                                                            estado_id=1,
                                                            instruccion=f.cleaned_data['instruccion'],
                                                            recomendacion=f.cleaned_data['recomendacion'],
                                                            objetivo=f.cleaned_data['objetivo'],
                                                            rubrica=f.cleaned_data['rubrica'],
                                                            desde=f.cleaned_data['desde'],
                                                            hasta=f.cleaned_data['hasta'],
                                                            word=f.cleaned_data['word'],
                                                            pdf=f.cleaned_data['pdf'],
                                                            excel=f.cleaned_data['excel'],
                                                            powerpoint=f.cleaned_data['powerpoint'],
                                                            todos=todos,
                                                            calificar=True,
                                                            archivorubrica=archivorubrica,
                                                            archivotareasilabo=archivotarea,
                                                            fecha_creacion=datetime.now(),
                                                            fecha_modificacion=datetime.now()
                                                            )
                    tareaSilaboSemanal.save()
                    tareaSilaboSemanal.historial_aprobacion_save(persona.id)
                    tareaSilaboSemanal.estado_id = 2
                    tareaSilaboSemanal.save()
                    tareaSilaboSemanal.historial_aprobacion_save(persona.id, observacion='Cambio de estado')
                    log_audit_action(request, tareaSilaboSemanal, f'Se creó un nueva {verbose.lower()} en la semana {silabosemanal.__str__()} ')
                    return JsonResponse({"isSuccess": True, "message": "Se creo correctamente la actividad en la semana %s" % silabosemanal})
                except Exception as ex:
                    transaction.set_rollback(True)
                    forms = f.toArray() if f else {}
                    return JsonResponse({"isSuccess": False, 'message': u'Error al guardar los datos %s' % ex, "forms": forms})

        elif action == 'editTareaVirtual':
            with transaction.atomic():
                try:
                    from .models import TareaSilaboSemanal, SilaboSemanal
                    from.funciones import generar_nombre
                    from .forms import TareaSilaboSemanalForm
                    from .funciones import generar_nombre
                    from moodle.recursos import GestionMoodle
                    f = None
                    ids = request.POST.get("ids")
                    try:
                        silabosemanal = SilaboSemanal.objects.get(pk=ids)
                    except ObjectDoesNotExist:
                        raise NameError(u"No existe el la semana planificada en el sílado para esta materia")
                    detalles_modelo = silabosemanal.silabo.materia.modelo_evaluativo.detallemodeloevaluativo_set.filter(es_dependiente=False).exclude(alternativa__id__in=[1, 2]).order_by('orden')
                    f = TareaSilaboSemanalForm(request.POST, request.FILES)
                    f.item_evaluativo(detalles_modelo)
                    if not f.is_valid():
                        f.addErrors(f.errors.get_json_data(escape_html=True))
                        raise NameError("Debe ingresar la información en todos los campos.")

                    id = request.POST.get("id")
                    try:
                        tareaSilaboSemanal = TareaSilaboSemanal.objects.get(pk=id)
                    except ObjectDoesNotExist:
                        raise NameError(u"No existe la tarea ha editar")

                    verbose = u'Tarea'
                    if tareaSilaboSemanal.tiporecurso == 2:
                        verbose = u'Taller'
                    elif tareaSilaboSemanal.tiporecurso == 3:
                        verbose = u'Proyecto de investigación'
                    elif tareaSilaboSemanal.tiporecurso == 4:
                        verbose = u'Análisis de caso'

                    if TareaSilaboSemanal.objects.filter(silabosemanal=silabosemanal, detallemodelo=f.cleaned_data['detallemodelo'], nombre=tareaSilaboSemanal.nombre).exclude(id=tareaSilaboSemanal.id).exists():
                        raise NameError(f"Ya existe un/una {verbose.lower()} con las mismas características, revise y vuelva a intentarlo ")

                    if 'archivorubrica' in request.FILES:
                        archivorubrica = request.FILES['archivorubrica']
                        archivorubrica._name = generar_nombre("archivoRubica", archivorubrica._name)
                        tareaSilaboSemanal.archivorubrica = archivorubrica

                    if 'archivotareasilabo' in request.FILES:
                        archivotarea = request.FILES['archivotareasilabo']
                        archivotarea._name = generar_nombre("archivoTarea", archivotarea._name)
                        tareaSilaboSemanal.archivotareasilabo = archivotarea
                    todos = (f.cleaned_data['word'] and f.cleaned_data['pdf'] and f.cleaned_data['excel'] and f.cleaned_data['powerpoint'])
                    tareaSilaboSemanal.detallemodelo = f.cleaned_data['detallemodelo']
                    tareaSilaboSemanal.instruccion = f.cleaned_data['instruccion']
                    tareaSilaboSemanal.recomendacion = f.cleaned_data['recomendacion']
                    tareaSilaboSemanal.objetivo = f.cleaned_data['objetivo']
                    tareaSilaboSemanal.rubrica = f.cleaned_data['rubrica']
                    tareaSilaboSemanal.desde = f.cleaned_data['desde']
                    tareaSilaboSemanal.hasta = f.cleaned_data['hasta']
                    tareaSilaboSemanal.word = f.cleaned_data['word']
                    tareaSilaboSemanal.pdf = f.cleaned_data['pdf']
                    tareaSilaboSemanal.excel = f.cleaned_data['excel']
                    tareaSilaboSemanal.powerpoint = f.cleaned_data['powerpoint']
                    tareaSilaboSemanal.todos = todos
                    tareaSilaboSemanal.fecha_modificacion = datetime.now()
                    if tareaSilaboSemanal.estado_id == 3:
                        tareaSilaboSemanal.estado_id = 2
                    tareaSilaboSemanal.save()
                    tareaSilaboSemanal.historial_aprobacion_save(persona.id, f'Actualizo el/la {verbose.lower()}')
                    if tareaSilaboSemanal.estado_id == 4:
                        eMateria = silabosemanal.silabo.materia
                        eGestionMoodle = GestionMoodle(eMateria=eMateria, ePersona=persona)
                        value, msg = eGestionMoodle.migrar_tarea(tareaSilaboSemanal)
                        if not value:
                            raise NameError(msg)
                    log_audit_action(request, tareaSilaboSemanal, f'Editó el/la {verbose.lower()} {tareaSilaboSemanal.nombre} de la semana {silabosemanal.__str__()} ')
                    return JsonResponse({"isSuccess": True, "message": u"Se actualizó correctamente la actividad en la semana %s" % silabosemanal})
                except Exception as ex:
                    transaction.set_rollback(True)
                    forms = f.toArray() if f else {}
                    return JsonResponse({"isSuccess": False, 'message': u'Error al guardar los datos %s' % ex, "forms": forms})

        elif action == 'delTareaVirtual':
            with transaction.atomic():
                try:
                    from .models import TareaSilaboSemanal
                    id = request.POST.get('id', 0)
                    try:
                        tareaSilaboSemanal = TareaSilaboSemanal.objects.get(pk=id)
                    except ObjectDoesNotExist:
                        raise NameError(u"No existe la tarea a eliminar")
                    tareaSilaboSemanal.delete()
                    return JsonResponse({"isSuccess": True, "message": f"Se eliminó correctamente la tarea"})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"isSuccess": False, "message": u"Error al eliminar la tarea: %s" % ex})

        elif action == 'addcomponenteevaluacion':
            try:
                from .models import SilaboSemanal, EvaluacionAprendizajeSilaboSemanal
                id = request.POST.get('id', None)
                try:
                    silaboSemanal = SilaboSemanal.objects.get(pk=id)
                except SilaboSemanal.DoesNotExist:
                    raise ValueError("No se encuentra la semana")
                if EvaluacionAprendizajeSilaboSemanal.objects.filter(silabosemanal=silaboSemanal, tiporecurso=request.POST['tipoactividad']).exists():
                    raise ValueError("Ya se encuentra registrada una actividad para esta semana")
                evaluacionAprendizajeSilaboSemanal = EvaluacionAprendizajeSilaboSemanal(silabosemanal=silaboSemanal,
                                                                                        tiporecurso=request.POST['tipoactividad'],
                                                                                        numactividad=request.POST['numeroactividad'])
                evaluacionAprendizajeSilaboSemanal.save()

                return JsonResponse({"isSuccess": True, "message": u"Se migro correctamente el recurso en moodle"})
            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse({"isSuccess": False, "message": u"Error al crear el recuro : %s" % ex})

        elif action == 'delComponeteEvaluacion':
            try:
                from .models import EvaluacionAprendizajeSilaboSemanal
                id = request.POST.get('id', 0)
                try:
                    evaluacionAprendizajeSilaboSemanal = EvaluacionAprendizajeSilaboSemanal.objects.get(pk=id)
                except ObjectDoesNotExist:
                    raise NameError(u"No existe la actividad")
                with transaction.atomic():
                    evaluacionAprendizajeSilaboSemanal.delete()
                    return JsonResponse({"isSuccess": True,
                                         "message": f"Se eliminó correctamente la tarea {evaluacionAprendizajeSilaboSemanal.get_tiporecurso_display()}"})
            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse(
                    {"isSuccess": False, "message": u"Error al eliminar la tarea, %s" % ex})

        elif action == 'migrar_presentacion_moodle':
            with transaction.atomic():
                try:
                    from sga.models import DiapositivaSilaboSemanal
                    from moodle.recursos import GestionMoodle
                    id = request.POST.get('id', 0)
                    try:
                        eDiapositivaSilaboSemanal = DiapositivaSilaboSemanal.objects.get(pk=id)
                    except DiapositivaSilaboSemanal.DoesNotExist:
                        raise ValueError("No se encuentra el recurso a migrar")
                    eMateria = eDiapositivaSilaboSemanal.silabosemanal.silabo.materia
                    eGestionMoodle = GestionMoodle(eMateria=eMateria, ePersona=persona)
                    value, msg = eGestionMoodle.migrar_presentacion(eDiapositivaSilaboSemanal)
                    if not value:
                        raise NameError(msg)
                    return JsonResponse({"isSuccess": True, "message": u"Se migro correctamente el recurso en moodle"})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"isSuccess": False, "message": u"Error al crear el recuro : %s" % ex})

        elif action == 'migrar_compendio_moodle':
            with transaction.atomic():
                try:
                    from sga.models import CompendioSilaboSemanal
                    from moodle.recursos import GestionMoodle
                    id = request.POST.get('id', 0)
                    try:
                        eCompendioSilaboSemanal = CompendioSilaboSemanal.objects.get(pk=id)
                    except CompendioSilaboSemanal.DoesNotExist:
                        raise ValueError("No se encuentra el recurso a migrar")
                    eMateria = eCompendioSilaboSemanal.silabosemanal.silabo.materia
                    eGestionMoodle = GestionMoodle(eMateria=eMateria, ePersona=persona)
                    value, msg = eGestionMoodle.migrar_compendio(eCompendioSilaboSemanal)
                    if not value:
                        raise NameError(msg)
                    return JsonResponse({"isSuccess": True, "message": u"Se migro correctamente el recurso en moodle"})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"isSuccess": False, "message": u"Error al crear el recuro : %s" % ex})

        elif action == 'migrar_videomagistral_moodle':
            with transaction.atomic():
                try:
                    from sga.models import VideoMagistralSilaboSemanal
                    from moodle.recursos import GestionMoodle
                    id = request.POST.get('id', 0)
                    try:
                        eVideoMagistralSilaboSemanal = VideoMagistralSilaboSemanal.objects.get(pk=id)
                    except VideoMagistralSilaboSemanal.DoesNotExist:
                        raise ValueError("No se encuentra el recurso a migrar")
                    eMateria = eVideoMagistralSilaboSemanal.silabosemanal.silabo.materia
                    eGestionMoodle = GestionMoodle(eMateria=eMateria, ePersona=persona)
                    value, msg = eGestionMoodle.migrar_video_magistral(eVideoMagistralSilaboSemanal)
                    if not value:
                        raise NameError(msg)
                    return JsonResponse({"isSuccess": True, "message": u"Se migro correctamente el recurso en moodle"})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"isSuccess": False, "message": u"Error al crear el recuro : %s" % ex})

        elif action == 'migrar_guiaestudiante_moodle':
            with transaction.atomic():
                try:
                    from sga.models import GuiaEstudianteSilaboSemanal
                    from moodle.recursos import GestionMoodle
                    id = request.POST.get('id', 0)
                    try:
                        eGuiaEstudianteSilaboSemanal = GuiaEstudianteSilaboSemanal.objects.get(pk=id)
                    except GuiaEstudianteSilaboSemanal.DoesNotExist:
                        raise ValueError("No se encuentra el recurso a migrar")
                    eMateria = eGuiaEstudianteSilaboSemanal.silabosemanal.silabo.materia
                    eGestionMoodle = GestionMoodle(eMateria=eMateria, ePersona=persona)
                    value, msg = eGestionMoodle.migrar_guia_estudiante(eGuiaEstudianteSilaboSemanal)
                    if not value:
                        raise NameError(msg)
                    return JsonResponse({"isSuccess": True, "message": u"Se migro correctamente el recurso en moodle"})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"isSuccess": False, "message": u"Error al crear el recuro : %s" % ex})

        elif action == 'migrar_test_moodle':
            with transaction.atomic():
                try:
                    from sga.models import TestSilaboSemanal
                    from moodle.recursos import GestionMoodle
                    id = request.POST.get('id', 0)
                    try:
                        eTestSilaboSemanal = TestSilaboSemanal.objects.get(pk=id)
                    except TestSilaboSemanal.DoesNotExist:
                        raise ValueError("No se encuentra el recurso a migrar")
                    eMateria = eTestSilaboSemanal.silabosemanal.silabo.materia
                    eGestionMoodle = GestionMoodle(eMateria=eMateria, ePersona=persona)
                    value, msg = eGestionMoodle.migrar_test(eTestSilaboSemanal)
                    if not value:
                        raise NameError(msg)
                    return JsonResponse({"isSuccess": True, "message": u"Se migro correctamente el recurso en moodle"})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"isSuccess": False, "message": u"Error al crear el recuro : %s" % ex})

        elif action == 'migrar_foro_moodle':
            with transaction.atomic():
                try:
                    from sga.models import ForoSilaboSemanal
                    from moodle.recursos import GestionMoodle
                    id = request.POST.get('id', 0)
                    try:
                        eForoSilaboSemanal = ForoSilaboSemanal.objects.get(pk=id)
                    except ForoSilaboSemanal.DoesNotExist:
                        raise ValueError("No se encuentra el recurso a migrar")
                    eMateria = eForoSilaboSemanal.silabosemanal.silabo.materia
                    eGestionMoodle = GestionMoodle(eMateria=eMateria, ePersona=persona)
                    value, msg = eGestionMoodle.migrar_foro(eForoSilaboSemanal)
                    if not value:
                        raise NameError(msg)
                    return JsonResponse({"isSuccess": True, "message": u"Se migro correctamente el recurso en moodle"})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"isSuccess": False, "message": u"Error al crear el recuro : %s" % ex})

        elif action == 'migrar_tarea_moodle':
            with transaction.atomic():
                try:
                    from sga.models import TareaSilaboSemanal
                    from moodle.recursos import GestionMoodle
                    id = request.POST.get('id', 0)
                    try:
                        eTareaSilaboSemanal = TareaSilaboSemanal.objects.get(pk=id)
                    except TareaSilaboSemanal.DoesNotExist:
                        raise ValueError("No se encuentra el recurso a migrar")
                    eMateria = eTareaSilaboSemanal.silabosemanal.silabo.materia
                    eGestionMoodle = GestionMoodle(eMateria=eMateria, ePersona=persona)
                    value, msg = eGestionMoodle.migrar_tarea(eTareaSilaboSemanal)
                    if not value:
                        raise NameError(msg)
                    return JsonResponse({"isSuccess": True, "message": u"Se migro correctamente el recurso en moodle"})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"isSuccess": False, "message": u"Error al crear el recuro : %s" % ex})

        elif action == 'actualizar_silabo_eva':
            with transaction.atomic():
                try:
                    from sga.models import Materia
                    from moodle.functions import crear_estilo_tarjeta, crear_actualizar_silabo
                    try:
                        eMateria = Materia.objects.get(pk=request.POST.get('id', 0))
                    except ObjectDoesNotExist:
                        raise NameError(u"Materia no encontrada")
                    crear_estilo_tarjeta(eMateria)
                    crear_actualizar_silabo(eMateria)
                    return JsonResponse({"isSuccess": True, "message": "Se actualizo correctamente el sílabo en EVA"})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"isSuccess": False, "message": u"Error al actualizar el sílabo en EVA: %s" % ex.__str__()})

        elif action == 'uploadChangeBanner':
            with transaction.atomic():
                try:
                    from sga.models import Materia
                    from sga.forms import BannerMateriaForm
                    f = None
                    id = request.POST.get("id", 0)
                    try:
                        eMateria = Materia.objects.get(pk=id)
                    except ObjectDoesNotExist:
                        raise NameError(u"No existe la materia")
                    f = BannerMateriaForm(request.POST, request.FILES)
                    if not f.is_valid():
                        f.addErrors(f.errors.get_json_data(escape_html=True))
                        raise NameError("Debe ingresar la información en todos los campos.")
                    eMateria.banner = request.FILES['banner']
                    eMateria.save()
                    # ActualizarBannerCurso(materia_.idcursomoodle, periodo, tipourl, materia_.banner,
                    #                       request.FILES['banner']._name)
                    return JsonResponse({"isSuccess": True, "message": f"Se cambio portada correctamente"})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"isSuccess": False, "message": u"Error al procesar los datos: %s" % ex})

        return JsonResponse({"isSuccess": False, "message": f"Acción no encontrada"})

    elif 'action' in request.GET:
        action = request.GET['action']
        if action == 'matriculados':
            try:
                from sga.models import MateriaAsignada, Materia
                data['title'] = u'Lista de estudiantes matriculados'
                data['materia'] = Materia.objects.get(pk=request.GET['id'])
                data['matriculados'] = MateriaAsignada.objects.filter(materia_id=request.GET['id'])
                return render(request, "pro_aulavirtual/matriculados.html", data)
            except Exception as ex:
                pass

        elif action == 'silabo':
            try:
                from .models import Silabo, Materia
                data['title'] = u'Sílabos'
                data['materia'] = materia = Materia.objects.get(pk=request.GET['id'])
                data['tiene_modelo_evaluativo'] = True if materia.modelo_evaluativo else False
                data['tiene_cronograma_academico'] = materia.tiene_cronograma_academico()
                data['silabos'] = Silabo.objects.filter(materia_id=request.GET['id'])
                return render(request, "pro_aulavirtual/silabo.html", data)
            except Exception as ex:
                return HttpResponseRedirect(f"{request.path}?info={str(ex)}")

        elif action == 'addSilabo':
            try:
                from .models import PlanAnalitico
                id = request.GET.get('id', 0)
                try:
                    plananaliticos = PlanAnalitico.objects.filter(activo=True, asignaturamalla__asignatura__id=id).distinct()
                except ObjectDoesNotExist:
                    raise NameError(u"No se encontro el plan analítico a editar")
                data['plananaliticos'] = plananaliticos
                template = get_template("pro_aulavirtual/listaplananalitico.html")
                json_content = template.render(request=request, context=data)
                return JsonResponse({"result": "ok", 'html': json_content})
            except Exception as ex:
                return HttpResponseRedirect(f"{request.path}?action=silabo&id={id}&info={ex.__str__()}")

        elif action == 'planificacionsilabo':
            try:
                from .models import Silabo, SilaboSemanal, CronograAcademicoDetalle
                data['title'] = u'Plan Temático'
                data['idsilabo'] = id = request.GET.get('id', 0)
                materia = None
                try:
                    silabo = Silabo.objects.get(pk=id)
                except ObjectDoesNotExist:
                    raise NameError(u"No se encontró el sílabo a planificar")
                materia = silabo.materia
                try:
                    cronogramaacademico = materia.cronograacademicomateria_set.all()[0].cronogramaacademico
                except ObjectDoesNotExist:
                    raise NameError(u"No se encontró el cronograma académico")
                semana, semana_crono = None, None
                data['cronogramasemanal'] = semanas_cronograma = cronogramaacademico.semanas()

                fecha = datetime.now().today()

                if 'ids' in request.GET:
                    semana_crono = semanas_cronograma.get(id=request.GET['ids'])
                elif semanas_cronograma.filter(inicio__lte=fecha, fin__gte=fecha).exists():
                    semana_crono = semanas_cronograma.filter(inicio__lte=fecha, fin__gte=fecha).distinct().first()
                elif semanas_cronograma:
                    semana_crono = semanas_cronograma[0]
                if semana_crono:
                    semana = silabo.semana(semana_crono.inicio, semana_crono.fin)
                    data['ids_sel'] = semana_crono.id
                data['semana_crono'] = semana_crono
                data['semana'] = semana
                data['tienesemanas'] = silabo.silabosemanal_set.values("id").exists()
                data['silabo'] = silabo
                data['puede_editar_platematico'] = silabo.puede_editar_platematico()
                data['porcentaje_planificacion_silabo'] = silabo.porcentaje_planificacion_silabo()
                return render(request, "pro_aulavirtual/planificacionsilabo.html", data)
            except Exception as ex:
                if materia:
                    return HttpResponseRedirect(f"{request.path}?action=silabo&id={materia.id}&info={ex.__str__()}")
                return HttpResponseRedirect(f"{request.path}?info={ex.__str__()}")

        elif action == 'addPlanificacionSemanal':
            try:
                from .models import Silabo, CronograAcademicoDetalle, PlanAnaliticoResulAprend
                from .forms import SilaboSemanalForm
                data['title'] = u'Adicionar la Semanal'
                id = request.GET.get('id', 0)
                data['silabo'] = silabo = Silabo.objects.get(pk=id)
                data['cronograma_academico'] = CronograAcademicoDetalle.objects.get(cronogramaacademico__cronograacademicomateria__materia_id=silabo.materia_id, pk=int(request.GET['ids']))
                data['form'] = SilaboSemanalForm()
                return render(request, "pro_aulavirtual/addplanificacionsemanal.html", data)
            except Exception as ex:
                return HttpResponseRedirect(f"{request.path}?action=silabo&id={silabo.id}&info={ex.__str__()}")

        elif action == 'editPlanificacionSemanal':
            try:
                from .models import SilaboSemanal, CronograAcademicoDetalle
                from .forms import SilaboSemanalForm
                data['title'] = u'Editar la Semanal'
                id = request.GET.get('id', 0)
                data['silabosemanal'] = silabosemanal = SilaboSemanal.objects.get(pk=id)
                data['idcronograma'] = int(request.GET['ids'])
                data['form'] = SilaboSemanalForm(initial={
                    'objetivoaprendizaje': silabosemanal.objetivoaprendizaje,
                    'enfoque': silabosemanal.enfoque,
                    'enfoquedos': silabosemanal.enfoquedos,
                    'enfoquetres': silabosemanal.enfoquetres,
                    'recursos': silabosemanal.recursos,
                    'evaluacion': silabosemanal.evaluacion,
                })
                return render(request, "pro_aulavirtual/editplanificacionsemanal.html", data)
            except Exception as ex:
                return HttpResponseRedirect(f"/?info={ex.__str__()}")

        elif action == 'editEnfoqueMetodologico':
            try:
                from .models import SilaboSemanal
                from .forms import EnfoqueMetodologicoForm
                id = request.GET.get('id', 0)
                try:
                    eSilaboSemanal = SilaboSemanal.objects.get(pk=id)
                except ObjectDoesNotExist:
                    raise NameError(u"No se encontro la semana")

                form = EnfoqueMetodologicoForm(initial={
                    'inicio': eSilaboSemanal.enfoque,
                    'desarrollo': eSilaboSemanal.enfoquedos,
                    'cierre': eSilaboSemanal.enfoquetres,
                })
                data['eSilaboSemanal'] = eSilaboSemanal
                data['form'] = form
                data['frmName'] = "formEnfoqueMetodlogico"
                template = get_template("pro_aulavirtual/modal/enfoquemetodologico.html")
                json_content = template.render(request=request, context=data)
                return JsonResponse({"isSuccess": True,
                                     "message": "Se construyo correctamente los datos",
                                     'html': json_content})
            except Exception as ex:
                return JsonResponse({"isSuccess": False, 'message': u'Error al construir los datos %s' % ex})

        elif action == 'notas_moodle':
            try:
                from sga.models import MateriaAsignada, Materia
                from moodle.functions import obtener_categorias_curso
                id = request.GET.get('id', 0)
                try:
                    eMateria = Materia.objects.get(pk=id)
                except ObjectDoesNotExist:
                    raise NameError(u"No se encontro la materia")
                data['title'] = f'Notas de EVA'
                data['eMateria'] = eMateria
                eMateriaAsignadas = MateriaAsignada.objects.filter(materia=eMateria).order_by('matricula__inscripcion__persona__apellido1', 'matricula__inscripcion__persona__apellido2', 'matricula__inscripcion__persona__nombres')
                # if DEBUG:
                #     eMateriaAsignadas = eMateriaAsignadas.filter(matricula__inscripcion__persona__cedula__in=['0953492162', '0929047454', '0955363775'])
                data['eMateriaAsignadas'] = eMateriaAsignadas
                data['habilitado_ingreso_calificaciones'] = habilitado_ingreso_calificaciones = True
                data['puede_importar_notas_moodle'] = puede_importar_notas_moodle = True
                data['mostrar_boton_importar_notas'] = mostrar_boton_importar_notas = True
                data['utiliza_validacion_calificaciones'] = utiliza_validacion_calificaciones = True
                data['categorias'] = categorias = obtener_categorias_curso(eMateria)
                data['total_categorias'] = len(categorias)
                return render(request, "pro_aulavirtual/notas_eva.html", data)
            except Exception as ex:
                return HttpResponseRedirect(f"{request.path}/?info={ex.__str__()}")

        elif action == 'planrecursoclasevirtual':
            try:
                from .models import Silabo
                data['examenfinal'] = None
                data['title'] = u'Planificación de Recursos'
                fecha_actual = datetime.now().today()
                data['fechahoy'] = datetime.now().date()
                data['periodoseleccionado'] = periodo
                data['silabo'] = silabo = Silabo.objects.select_related('materia').get(pk=int(request.GET['id']))
                data['puede_editar_recursos'] = silabo.puede_editar_recursos()
                data['semanasSilabos'] = silabosemanal = silabo.silabosemanal_set.all().order_by('numsemana')
                semana = None
                if 'ids' in request.GET:
                    semana = silabosemanal.get(id=request.GET['ids'])
                elif silabosemanal.filter(fechainiciosemana__lte=fecha_actual, fechafinsemana__gte=fecha_actual).exists():
                    semana = silabosemanal.filter(fechainiciosemana__lte=fecha_actual, fechafinsemana__gte=fecha_actual).distinct().first()
                elif silabosemanal:
                    semana = silabosemanal[0]
                if semana:
                    data['id_sem'] = semana.id
                data['semana'] = semana
                return render(request, "pro_aulavirtual/plansemanal.html", data)
            except Exception as ex:
                return HttpResponseRedirect(f"{request.path}?action=silabo&id={silabo.id}&info={ex.__str__()}")

        elif action == 'addDiapositivaVirtual':
            try:
                from .models import SilaboSemanal
                from .forms import DiapositivaSilaboSemanalForm
                data['title'] = u'Adicionar presentación'

                id = request.GET.get('id')
                try:
                    silaboSemanal = SilaboSemanal.objects.get(pk=id)
                except ObjectDoesNotExist:
                    silaboSemanal = None
                    raise NameError(u"No se encontró la semana planificada del sílabo")

                data['silabosemanal'] = silaboSemanal
                form = DiapositivaSilaboSemanalForm(initial={'tipomaterial': 1})
                data['form'] = form
                return render(request, "pro_aulavirtual/recursos/presentacion/add.html", data)
            except Exception as ex:
                if silaboSemanal:
                    return HttpResponseRedirect(f"{request.path}?action=planrecursoclasevirtual&id={silaboSemanal.silabo.id}&ids={silaboSemanal.id}&info={ex.__str__()}")
                return HttpResponseRedirect(f"{request.path}?info={ex.__str__()}")

        elif action == 'editDiapositivaVirtual':
            try:
                from .models import SilaboSemanal, DiapositivaSilaboSemanal
                from .forms import DiapositivaSilaboSemanalForm
                data['title'] = u'Editar presentación'

                ids = request.GET.get('ids')
                try:
                    silaboSemanal = SilaboSemanal.objects.get(pk=ids)
                except ObjectDoesNotExist:
                    silaboSemanal = None
                    raise NameError(u"No se encontró la semana planificada del sílabo")

                data['silabosemanal'] = silaboSemanal

                id = request.GET.get('id')
                try:
                    diapositivaSilaboSemanal = DiapositivaSilaboSemanal.objects.get(pk=id)
                except ObjectDoesNotExist:
                    raise NameError(u"No se encontró la presentación en la semana %s" % silaboSemanal)
                data['idd'] = id
                form = DiapositivaSilaboSemanalForm(initial={
                    'nombre': diapositivaSilaboSemanal.nombre,
                    'descripcion': diapositivaSilaboSemanal.descripcion,
                    'tipomaterial': diapositivaSilaboSemanal.tipomaterial,
                    'archivodiapositiva': diapositivaSilaboSemanal.archivodiapositiva,
                    'url': diapositivaSilaboSemanal.url
                })

                data['form'] = form
                return render(request, "pro_aulavirtual/recursos/presentacion/edit.html", data)
            except Exception as ex:
                if silaboSemanal:
                    return HttpResponseRedirect(
                        f"{request.path}?action=planrecursoclasevirtual&id={silaboSemanal.silabo.id}&ids={silaboSemanal.id}&info={ex.__str__()}")
                return HttpResponseRedirect(f"{request.path}?info={ex.__str__()}")

        elif action == 'viewDetallePresentacion':
            try:
                from .models import SilaboSemanal, DiapositivaSilaboSemanal
                ids = request.GET.get("ids")
                try:
                    silabosemanal = SilaboSemanal.objects.get(pk=ids)
                except ObjectDoesNotExist:
                    raise NameError(u"No se encontró la semana planificada")

                id = request.GET.get("id")
                try:
                    diapositivaSilaboSemanal = DiapositivaSilaboSemanal.objects.get(pk=id, silabosemanal_id=ids)
                except ObjectDoesNotExist:
                    raise NameError(u"No se encontró el video magistral")

                data['diapositivaSilaboSemanal'] = diapositivaSilaboSemanal
                data['historialaprobacion'] = diapositivaSilaboSemanal.historialaprobaciondiapositiva_set.all().order_by('id')
                template = get_template("pro_aulavirtual/recursos/presentacion/detalle.html")
                json_content = template.render(request=request, context=data)
                return JsonResponse({"isSuccess": True,
                                     "message": "Se construyo correctamente los datos",
                                     'html': json_content,
                                     'title': 'Detalle de presentación'
                                     })
            except Exception as ex:
                return JsonResponse({"isSuccess": False, 'message': u'Error al construir los datos %s' % ex})

        elif action == 'addVideoMagistralVirtual':
            try:
                from .models import SilaboSemanal
                from .forms import VideoMagistralSilaboSemanalForm
                data['title'] = u'Adicionar video magistral'
                id = request.GET.get('id')
                try:
                    silaboSemanal = SilaboSemanal.objects.get(pk=id)
                except ObjectDoesNotExist:
                    silaboSemanal = None
                    raise NameError(u"No se encontró la semana planificada del sílabo")
                data['silabosemanal'] = silaboSemanal
                form = VideoMagistralSilaboSemanalForm()
                data['form'] = form
                return render(request, "pro_aulavirtual/recursos/video_magistral/add.html", data)
            except Exception as ex:
                if silaboSemanal:
                    return HttpResponseRedirect(
                        f"{request.path}?action=planrecursoclasevirtual&id={silaboSemanal.silabo.id}&ids={silaboSemanal.id}&info={ex.__str__()}")
                return HttpResponseRedirect(f"{request.path}?info={ex.__str__()}")

        elif action == 'editVideoMagistralVirtual':
            try:
                from .models import VideoMagistralSilaboSemanal, SilaboSemanal
                from .forms import VideoMagistralSilaboSemanalForm
                data['title'] = u'Editar video magistral'
                ids = request.GET.get("ids")

                try:
                    silaboSemanal = SilaboSemanal.objects.get(pk=ids)
                except ObjectDoesNotExist:
                    silaboSemanal = None
                    raise NameError(u"No se encontró la semana planificada del sílabo")

                data['silabosemanal'] = silaboSemanal

                id = request.GET.get("id")
                try:
                    videomagistral = VideoMagistralSilaboSemanal.objects.get(pk=id)
                except ObjectDoesNotExist:
                    raise NameError(u"No se encontró el vodeo magistral")
                data['id'] = id

                data['form'] = VideoMagistralSilaboSemanalForm(initial={
                    'descripcion': videomagistral.descripcion,
                    'archivovideo': videomagistral.archivovideo,
                    'url': videomagistral.url,
                    'tipomaterial': videomagistral.tipomaterial,
                    'tipograbacion': videomagistral.tipograbacion,
                    'tipovideo': videomagistral.tipovideo
                })
                return render(request, "pro_aulavirtual/recursos/video_magistral/edit.html", data)
            except Exception as ex:
                if silaboSemanal:
                    return HttpResponseRedirect(
                        f"{request.path}?action=planrecursoclasevirtual&id={silaboSemanal.silabo.id}&ids={silaboSemanal.id}&info={ex.__str__()}")
                return HttpResponseRedirect(f"{request.path}?info={ex.__str__()}")

        elif action == 'viewDetalleVideoMagistral':
            try:
                from .models import SilaboSemanal, VideoMagistralSilaboSemanal
                ids = request.GET.get("ids")
                try:
                    silabosemanal = SilaboSemanal.objects.get(pk=ids)
                except ObjectDoesNotExist:
                    raise NameError(u"No se encontró la semana planificada")

                id = request.GET.get("id")
                try:
                    videoMagistralSilaboSemanal = VideoMagistralSilaboSemanal.objects.get(pk=id, silabosemanal_id=ids)
                except ObjectDoesNotExist:
                    raise NameError(u"No se encontró el video magistral")

                data['videomagistral'] = videoMagistralSilaboSemanal
                data['historialaprobacion'] = videoMagistralSilaboSemanal.historialaprobacionvideomagistral_set.all().order_by('id')
                template = get_template("pro_aulavirtual/recursos/video_magistral/detalle.html")
                json_content = template.render(request=request, context=data)
                return JsonResponse({"isSuccess": True,
                                     "message": "Se construyo correctamente los datos",
                                     'html': json_content,
                                     'title': 'Detalle del Video Magistral'
                                     })
            except Exception as ex:
                return JsonResponse({"isSuccess": False, 'message': u'Error al construir los datos %s' % ex})

        elif action == 'addCompendioVirtual':
            try:
                from .models import SilaboSemanal, CompendioSilaboSemanal
                from .forms import CompendioSilaboSemanalForm
                data['title'] = u'Adicionar compendio'

                id = request.GET.get('id')
                try:
                    silaboSemanal = SilaboSemanal.objects.get(pk=id)
                except ObjectDoesNotExist:
                    raise NameError(u"No se encontró la semana")

                data['silabosemanal'] = silaboSemanal
                form = CompendioSilaboSemanalForm()
                data['form'] = form
                return render(request, "pro_aulavirtual/recursos/compendio/add.html", data)
            except Exception as ex:
                if silaboSemanal:
                    return HttpResponseRedirect(
                        f"{request.path}?action=planrecursoclasevirtual&id={silaboSemanal.silabo.id}&ids={silaboSemanal.id}&info={ex.__str__()}")
                return HttpResponseRedirect(f"{request.path}?info={ex.__str__()}")

        elif action == 'editCompendioVirtual':
            try:
                from .models import CompendioSilaboSemanal, SilaboSemanal
                from .forms import CompendioSilaboSemanalForm
                data['title'] = u'Editar Compendio'
                ids = request.GET.get("ids")

                try:
                    silabosemanal = SilaboSemanal.objects.get(pk=ids)
                except ObjectDoesNotExist:
                    raise NameError(u"No se encontró la semana planificada del sílabo")

                data['silabosemanal'] = silabosemanal

                id = request.GET.get("id")
                try:
                    conpendio = CompendioSilaboSemanal.objects.get(pk=id)
                except ObjectDoesNotExist:
                    raise NameError(u"No se encontró el conpendio")
                data['id'] = id

                data['form'] = CompendioSilaboSemanalForm(initial={
                    'nombre': conpendio.nombre,
                    'descripcion': conpendio.descripcion,
                    'archivocompendio': conpendio.archivocompendio,
                    'archivoplagio': conpendio.archivoplagio,
                    'porcentaje': conpendio.porcentaje
                })
                return render(request, "pro_aulavirtual/recursos/compendio/edit.html", data)
            except Exception as ex:
                if silaboSemanal:
                    return HttpResponseRedirect(
                        f"{request.path}?action=planrecursoclasevirtual&id={silaboSemanal.silabo.id}&ids={silaboSemanal.id}&info={ex.__str__()}")
                return HttpResponseRedirect(f"{request.path}?info={ex.__str__()}")

        elif action == 'ViewDetalleCompendio':
            try:
                from .models import SilaboSemanal, CompendioSilaboSemanal
                ids = request.GET.get("ids")
                try:
                    silabosemanal = SilaboSemanal.objects.get(pk=ids)
                except ObjectDoesNotExist:
                    raise NameError(u"No se encontró la semana planificada")

                id = request.GET.get("id")
                try:
                    compendioSilaboSemanal = CompendioSilaboSemanal.objects.get(pk=id, silabosemanal_id=ids)
                except ObjectDoesNotExist:
                    raise NameError(u"No se encontró el video magistral")

                data['compendioSilaboSemanal'] = compendioSilaboSemanal
                data['historialaprobacion'] = compendioSilaboSemanal.historialaprobacioncompendio_set.all().order_by('id')
                template = get_template("pro_aulavirtual/recursos/compendio/detalle.html")
                json_content = template.render(request=request, context=data)
                return JsonResponse({"isSuccess": True,
                                     "message": "Se construyo correctamente los datos",
                                     'html': json_content,
                                     'title': 'Detalle del Compendio'
                                     })
            except Exception as ex:
                return JsonResponse({"isSuccess": False, 'message': u'Error al construir los datos %s' % ex})

        elif action == 'addGuiaEstudianteVirtual':
            try:
                from .models import SilaboSemanal, GuiaEstudianteSilaboSemanal
                from .forms import GuiaEstudianteSilaboSemanalForm
                data['title'] = u'Adicionar guía del estudiante'

                id = request.GET.get('id')
                try:
                    silaboSemanal = SilaboSemanal.objects.get(pk=id)
                except ObjectDoesNotExist:
                    raise NameError(u"No se encontró la semana")

                data['silabosemanal'] = silaboSemanal
                form = GuiaEstudianteSilaboSemanalForm()
                data['form'] = form
                return render(request, "pro_aulavirtual/recursos/guia_estudiante/add.html", data)
            except Exception as ex:
                if silaboSemanal:
                    return HttpResponseRedirect(
                        f"{request.path}?action=planrecursoclasevirtual&id={silaboSemanal.silabo.id}&ids={silaboSemanal.id}&info={ex.__str__()}")
                return HttpResponseRedirect(f"{request.path}?info={ex.__str__()}")

        elif action == 'editGuiaEstudianteVirtual':
            try:
                from .models import SilaboSemanal, GuiaEstudianteSilaboSemanal
                from .forms import GuiaEstudianteSilaboSemanalForm
                data['title'] = u'Editar guía del estudiante'
                ids = request.GET.get('ids')
                try:
                    silabosemanal = SilaboSemanal.objects.get(pk=ids)
                except ObjectDoesNotExist:
                    raise NameError(u"No se encontró la semana planificada del sílabo")

                data['silabosemanal'] = silabosemanal

                id = request.GET.get("id")
                try:
                    guiaEstudianteSilaboSemanal = GuiaEstudianteSilaboSemanal.objects.get(pk=id)
                except ObjectDoesNotExist:
                    raise NameError(u"No se encontró el la guía de estudio")
                data['id'] = id

                data['form'] = GuiaEstudianteSilaboSemanalForm(initial={
                    'nombre': guiaEstudianteSilaboSemanal.nombre,
                    'objetivo': guiaEstudianteSilaboSemanal.objetivo,
                    'archivoguiaestudiante': guiaEstudianteSilaboSemanal.archivoguiaestudiante
                })
                return render(request, "pro_aulavirtual/recursos/guia_estudiante/edit.html", data)
            except Exception as ex:
                if silaboSemanal:
                    return HttpResponseRedirect(
                        f"{request.path}?action=planrecursoclasevirtual&id={silaboSemanal.silabo.id}&ids={silaboSemanal.id}&info={ex.__str__()}")
                return HttpResponseRedirect(f"{request.path}?info={ex.__str__()}")

        elif action == 'viewDetalleGuiaEstudiante':
            try:
                from .models import SilaboSemanal, GuiaEstudianteSilaboSemanal
                ids = request.GET.get("ids")
                try:
                    silabosemanal = SilaboSemanal.objects.get(pk=ids)
                except ObjectDoesNotExist:
                    raise NameError(u"No se encontró la semana planificada")

                id = request.GET.get("id")
                try:
                    guiaEstudianteSilaboSemanal = GuiaEstudianteSilaboSemanal.objects.get(pk=id, silabosemanal=silabosemanal)
                except ObjectDoesNotExist:
                    raise NameError(u"No se encontró la guía del estudiante")

                data['guiaEstudianteSilaboSemanal'] = guiaEstudianteSilaboSemanal
                data['historialaprobacion'] = guiaEstudianteSilaboSemanal.historialaprobacionguiaestudiante_set.order_by('id')
                template = get_template("pro_aulavirtual/recursos/guia_estudiante/detalle.html")
                json_content = template.render(request=request, context=data)
                return JsonResponse({"isSuccess": True,
                                     "message": "Se construyo correctamente los datos",
                                     'html': json_content,
                                     'title': 'Detalle de Guía del Estudiante'
                                     })
            except Exception as ex:
                return JsonResponse({"isSuccess": False, 'message': u'Error al construir los datos %s' % ex})

        elif action == 'addTestVirtual':
            try:
                from .models import SilaboSemanal, TestSilaboSemanal
                from .forms import TestSilaboSemanalForm
                data['title'] = u'Adicionar Test'

                id = request.GET.get('id')
                try:
                    silaboSemanal = SilaboSemanal.objects.get(pk=id)
                except ObjectDoesNotExist:
                    raise NameError(u"No se encontró la semana")
                data['silabosemanal'] = silaboSemanal
                detalles_modelo = silaboSemanal.silabo.materia.modelo_evaluativo.detallemodeloevaluativo_set.filter(es_dependiente=False).exclude(alternativa__id__in=[1,2]).order_by('orden')
                form = TestSilaboSemanalForm(initial={'detallemodelo': detalles_modelo})
                form.item_evaluativo(detalles_modelo)
                data['form'] = form
                return render(request, "pro_aulavirtual/a_c_d/test/add.html", data)
            except Exception as ex:
                if silaboSemanal:
                    return HttpResponseRedirect(
                        f"{request.path}?action=planrecursoclasevirtual&id={silaboSemanal.silabo.id}&ids={silaboSemanal.id}&info={ex.__str__()}")
                return HttpResponseRedirect(f"{request.path}?info={ex.__str__()}")

        elif action == 'editTestVirtual':
            try:
                from .models import SilaboSemanal, TestSilaboSemanal
                from .forms import TestSilaboSemanalForm
                data['title'] = u'Editar Test'

                ids = request.GET.get('ids')
                try:
                    silaboSemanal = SilaboSemanal.objects.get(pk=ids)
                except ObjectDoesNotExist:
                    raise NameError(u"No se encontró la semana")

                id = request.GET.get('id')
                try:
                    testSilaboSemanal = TestSilaboSemanal.objects.get(pk=id)
                except ObjectDoesNotExist:
                    raise NameError(u"No se encontró el test a editar")
                data['silabosemanal'] = silaboSemanal
                data['id'] = id
                detalles_modelo = silaboSemanal.silabo.materia.modelo_evaluativo.detallemodeloevaluativo_set.filter(es_dependiente=False).exclude(alternativa__id__in=[1,2]).order_by('orden')
                form = TestSilaboSemanalForm(initial={'nombre': testSilaboSemanal.nombre,
                                                      'instruccion': testSilaboSemanal.instruccion,
                                                      'recomendacion': testSilaboSemanal.recomendacion,
                                                      'desde': testSilaboSemanal.desde,
                                                      'hasta': testSilaboSemanal.hasta,
                                                      'vecesintento': testSilaboSemanal.vecesintento,
                                                      'tiempoduracion': testSilaboSemanal.tiempoduracion,
                                                      'detallemodelo': testSilaboSemanal.detallemodelo,
                                                      'navegacion': testSilaboSemanal.navegacion
                                                      })
                form.item_evaluativo(detalles_modelo)
                data['form'] = form
                return render(request, "pro_aulavirtual/a_c_d/test/edit.html", data)
            except Exception as ex:
                if silaboSemanal:
                    return HttpResponseRedirect(
                        f"{request.path}?action=planrecursoclasevirtual&id={silaboSemanal.silabo.id}&ids={silaboSemanal.id}&info={ex.__str__()}")
                return HttpResponseRedirect(f"{request.path}?info={ex.__str__()}")

        elif action == 'viewDetalleTest':
            try:
                from .models import SilaboSemanal, TestSilaboSemanal
                ids = request.GET.get("ids")
                try:
                    silabosemanal = SilaboSemanal.objects.get(pk=ids)
                except ObjectDoesNotExist:
                    raise NameError(u"No se encontró la semana planificada")

                id = request.GET.get("id")
                try:
                    testSilaboSemanal = TestSilaboSemanal.objects.get(pk=id, silabosemanal=silabosemanal)
                except ObjectDoesNotExist:
                    raise NameError(u"No se encontró el test")

                data['testSilaboSemanal'] = testSilaboSemanal
                data['historialaprobacion'] = testSilaboSemanal.historialaprobaciontest_set.order_by('id')
                template = get_template("pro_aulavirtual/a_c_d/test/detalle.html")
                json_content = template.render(request=request, context=data)
                return JsonResponse({"isSuccess": True,
                                     "message": "Se construyo correctamente los datos",
                                     'html': json_content,
                                     'title': 'Detalle de Test'
                                     })
            except Exception as ex:
                return JsonResponse({"isSuccess": False, 'message': u'Error al construir los datos %s' % ex})

        elif action == 'addForoVirtual':
            try:
                from .models import SilaboSemanal
                from .forms import ForoSilaboSemanalForm
                data['title'] = u'Adicionar Foro'

                id = request.GET.get('id')
                try:
                    silaboSemanal = SilaboSemanal.objects.get(pk=id)
                except ObjectDoesNotExist:
                    raise NameError(u"No se encontró la semana")
                data['silabosemanal'] = silaboSemanal
                detalles_modelo = silaboSemanal.silabo.materia.modelo_evaluativo.detallemodeloevaluativo_set.filter(es_dependiente=False).exclude(alternativa__id__in=[1,2]).order_by('orden')
                form = ForoSilaboSemanalForm(initial={'detallemodelo': detalles_modelo})
                form.item_evaluativo(detalles_modelo)
                data['form'] = form
                return render(request, "pro_aulavirtual/a_a/foro/add.html", data)
            except Exception as ex:
                if silaboSemanal:
                    return HttpResponseRedirect(
                        f"{request.path}?action=planrecursoclasevirtual&id={silaboSemanal.silabo.id}&ids={silaboSemanal.id}&info={ex.__str__()}")
                return HttpResponseRedirect(f"{request.path}?info={ex.__str__()}")

        elif action == 'editForoVirtual':
            try:
                from .models import SilaboSemanal, ForoSilaboSemanal
                from .forms import ForoSilaboSemanalForm
                data['title'] = u'Editar Foro'
                ids = request.GET.get('ids')
                try:
                    silaboSemanal = SilaboSemanal.objects.get(pk=ids)
                except ObjectDoesNotExist:
                    raise NameError(u"No se encontró la semana")
                id = request.GET.get('id')
                try:
                    foroSilaboSemanal = ForoSilaboSemanal.objects.get(pk=id)
                except ObjectDoesNotExist:
                    raise NameError(u"No se encontró el test a editar")
                data['silabosemanal'] = silaboSemanal
                data['id'] = id
                detalles_modelo = silaboSemanal.silabo.materia.modelo_evaluativo.detallemodeloevaluativo_set.filter(es_dependiente=False).exclude(alternativa__id__in=[1,2]).order_by('orden')
                form = ForoSilaboSemanalForm(initial={'nombre': foroSilaboSemanal.nombre,
                                                      'instruccion': foroSilaboSemanal.instruccion,
                                                      'recomendacion': foroSilaboSemanal.recomendacion,
                                                      'desde': foroSilaboSemanal.desde,
                                                      'hasta': foroSilaboSemanal.hasta,
                                                      'objetivo': foroSilaboSemanal.objetivo,
                                                      'rubrica': foroSilaboSemanal.rubrica,
                                                      'detallemodelo': foroSilaboSemanal.detallemodelo,
                                                      'tipoforo': foroSilaboSemanal.tipoforo,
                                                      'tipoconsolidacion': foroSilaboSemanal.tipoconsolidacion,
                                                      'calificar': foroSilaboSemanal.calificar,
                                                      'archivorubrica': foroSilaboSemanal.archivorubrica,
                                                      'archivoforo': foroSilaboSemanal.archivoforo,
                                                      })
                form.item_evaluativo(detalles_modelo)
                data['form'] = form
                return render(request, "pro_aulavirtual/a_a/foro/edit.html", data)
            except Exception as ex:
                if silaboSemanal:
                    return HttpResponseRedirect(
                        f"{request.path}?action=planrecursoclasevirtual&id={silaboSemanal.silabo.id}&ids={silaboSemanal.id}&info={ex.__str__()}")
                return HttpResponseRedirect(f"{request.path}?info={ex.__str__()}")

        elif action == 'viewDetalleForo':
            try:
                from .models import SilaboSemanal, ForoSilaboSemanal
                ids = request.GET.get("ids")
                try:
                    silabosemanal = SilaboSemanal.objects.get(pk=ids)
                except ObjectDoesNotExist:
                    raise NameError(u"No se encontró la semana planificada")

                id = request.GET.get("id")
                try:
                    foroSilaboSemanal = ForoSilaboSemanal.objects.get(pk=id, silabosemanal=silabosemanal)
                except ObjectDoesNotExist:
                    raise NameError(u"No se encontró el test")

                data['foroSilaboSemanal'] = foroSilaboSemanal
                data['historialaprobacion'] = foroSilaboSemanal.historialaprobacionforo_set.order_by('id')
                template = get_template("pro_aulavirtual/a_a/foro/detalle.html")
                json_content = template.render(request=request, context=data)
                return JsonResponse({"isSuccess": True,
                                     "message": "Se construyo correctamente los datos",
                                     'html': json_content,
                                     'title': 'Detalle del Foro'
                                     })
            except Exception as ex:
                return JsonResponse({"isSuccess": False, 'message': u'Error al construir los datos %s' % ex})

        elif action == 'addTareaVirtual':
            try:
                from .models import SilaboSemanal
                from .forms import TareaSilaboSemanalForm
                tipo = int(request.GET.get("tp", 0))
                frm_title = u'Adicionar Tarea'
                if tipo == 2:
                    frm_title = u'Adicionar Taller'
                elif tipo == 3:
                    frm_title = u'Adicionar Trabajo de Investigación'
                elif tipo == 3:
                    frm_title = u'Adicionar Análisis de Caso'
                data['frm_title'] = frm_title
                data['tp'] = tipo
                id = request.GET.get('id')
                try:
                    silaboSemanal = SilaboSemanal.objects.get(pk=id)
                except ObjectDoesNotExist:
                    raise NameError(u"No se encontró la semana")
                data['silabosemanal'] = silaboSemanal
                detalles_modelo = silaboSemanal.silabo.materia.modelo_evaluativo.detallemodeloevaluativo_set.filter(es_dependiente=False).exclude(alternativa__id__in=[1,2]).order_by('orden')
                form = TareaSilaboSemanalForm(initial={'detallemodelo': detalles_modelo})
                form.item_evaluativo(detalles_modelo)
                data['form'] = form
                return render(request, "pro_aulavirtual/a_a/tarea/add.html", data)
            except Exception as ex:
                if silaboSemanal:
                    return HttpResponseRedirect(
                        f"{request.path}?action=planrecursoclasevirtual&id={silaboSemanal.silabo.id}&ids={silaboSemanal.id}&info={ex.__str__()}")
                return HttpResponseRedirect(f"{request.path}?info={ex.__str__()}")

        elif action == 'editTareaVirtual':
            try:
                from .models import SilaboSemanal, TareaSilaboSemanal
                from .forms import TareaSilaboSemanalForm
                ids = request.GET.get('ids')
                try:
                    silaboSemanal = SilaboSemanal.objects.get(pk=ids)
                except ObjectDoesNotExist:
                    raise NameError(u"No se encontró la semana")

                id = request.GET.get('id')
                try:
                    tareaSilaboSemanal = TareaSilaboSemanal.objects.get(pk=id)
                except ObjectDoesNotExist:
                    raise NameError(u"No se encontró el test a editar")
                tipo=tareaSilaboSemanal.tiporecurso
                titulo = u'Editar Tarea'
                if tipo == 2:
                    titulo = u'Editar Taller'
                elif tipo == 3:
                    titulo = u'Editar Proyecto de Investigación'
                elif tipo == 4:
                    titulo = u'Editar Análisis de Caso'
                data['frm_title'] = titulo
                data['silabosemanal'] = silaboSemanal
                data['id'] = id
                detalles_modelo = silaboSemanal.silabo.materia.modelo_evaluativo.detallemodeloevaluativo_set.filter(es_dependiente=False).exclude(alternativa__id__in=[1,2]).order_by('orden')
                form = TareaSilaboSemanalForm(initial={'nombre': tareaSilaboSemanal.nombre,
                                                       'instruccion': tareaSilaboSemanal.instruccion,
                                                       'recomendacion': tareaSilaboSemanal.recomendacion,
                                                       'desde': tareaSilaboSemanal.desde,
                                                       'hasta': tareaSilaboSemanal.hasta,
                                                       'objetivo': tareaSilaboSemanal.objetivo,
                                                       'rubrica': tareaSilaboSemanal.rubrica,
                                                       'detallemodelo': tareaSilaboSemanal.detallemodelo,
                                                       'word': tareaSilaboSemanal.word,
                                                       'pdf': tareaSilaboSemanal.pdf,
                                                       'excel': tareaSilaboSemanal.excel,
                                                       'powerpoint': tareaSilaboSemanal.powerpoint,
                                                       'calificar': tareaSilaboSemanal.calificar,
                                                       'archivorubrica': tareaSilaboSemanal.archivorubrica,
                                                       'archivotareasilabo': tareaSilaboSemanal.archivotareasilabo,
                                                       })
                form.item_evaluativo(detalles_modelo)
                data['form'] = form
                return render(request, "pro_aulavirtual/a_a/tarea/edit.html", data)
            except Exception as ex:
                if silaboSemanal:
                    return HttpResponseRedirect(
                        f"{request.path}?action=planrecursoclasevirtual&id={silaboSemanal.silabo.id}&ids={silaboSemanal.id}&info={ex.__str__()}")
                return HttpResponseRedirect(f"{request.path}?info={ex.__str__()}")

        elif action == 'viewDetalleTarea':
            try:
                from .models import SilaboSemanal, TareaSilaboSemanal
                ids = request.GET.get("ids")
                try:
                    silabosemanal = SilaboSemanal.objects.get(pk=ids)
                except ObjectDoesNotExist:
                    raise NameError(u"No se encontró la semana planificada")

                id = request.GET.get("id")
                try:
                    tareaSilaboSemanal = TareaSilaboSemanal.objects.get(pk=id, silabosemanal=silabosemanal)
                except ObjectDoesNotExist:
                    raise NameError(u"No se encontró el test")
                tipo = tareaSilaboSemanal.tiporecurso
                titulo = u'Detalle de la Tarea'
                if tipo == 2:
                    titulo = u'Detalle del Taller'
                elif tipo == 3:
                    titulo = u'Detalle del Proyecto de Investigación'
                elif tipo == 4:
                    titulo = u'Detalle del Análisis de Caso'
                data['tareaSilaboSemanal'] = tareaSilaboSemanal
                data['historialaprobacion'] = tareaSilaboSemanal.historialaprobaciontarea_set.order_by('id')
                template = get_template("pro_aulavirtual/a_a/tarea/detalle.html")
                json_content = template.render(request=request, context=data)
                return JsonResponse({"isSuccess": True,
                                     "message": "Se construyo correctamente los datos",
                                     'html': json_content,
                                     'title': titulo
                                     })
            except Exception as ex:
                return JsonResponse({"isSuccess": False, 'message': u'Error al construir los datos %s' % ex})

        elif action == 'loadChangeBanner':
            try:
                from sga.models import Materia
                from sga.forms import BannerMateriaForm
                data['id'] = id = request.GET['id']
                id = request.GET.get('id', 0)
                try:
                    eMateria = Materia.objects.get(pk=id)
                except ObjectDoesNotExist:
                    raise NameError(u"No se encontro la materia")
                form = BannerMateriaForm(initial=model_to_dict(eMateria))
                data['eMateria'] = eMateria
                data['form'] = form
                data['frmName'] = "frmUploadBanner"
                template = get_template("pro_aulavirtual/modal/changebanner.html")
                json_content = template.render(request=request, context=data)
                return JsonResponse({"isSuccess": True,
                                     "message": "Se construyo correctamente los datos",
                                     'html': json_content})
            except Exception as ex:
                return JsonResponse({"isSuccess": False, 'message': u'Error al construir los datos %s' % ex})

        elif action == 'consultacomponentes':
            from .models import EvaluacionAprendizajeComponente, SilaboSemanal, TIPO_RECURSO
            try:
                silaboSemanal = SilaboSemanal.objects.get(pk=int(request.GET['id']))
                listaseleccionados = list(silaboSemanal.evaluacionaprendizajesilabosemanal_set.values_list("tiporecurso", flat=True).all())
                # data['listadocomponentes'] = EvaluacionAprendizajeComponente.objects.all().exclude(id__in=listaseleccionados)
                data['ids'] = silaboSemanal.id
                data['tiporecursos'] = [(id, nombre) for id, nombre in TIPO_RECURSO if id not in listaseleccionados]
                template = get_template("pro_aulavirtual/addcomponente.html")
                json_content = template.render(request=request, context=data)
                return JsonResponse({"isSuccess": True, 'html': json_content})
            except Exception as ex:
                return HttpResponseRedirect(f"{request.path}?action=planificacionsilabo?id={silaboSemanal.silabo_id}&info={ex.__str__()}")



    else:
        from sga.models import Materia
        data['title'] = u'Planificación de tareas y actividades del profesor'
        filtro = Q(nivel__periodo__id=periodo.id, profesormateria__profesor=profesor)
        data['materias'] = Materia.objects.filter(filtro).distinct().order_by('nivel__carrera', 'asignatura')
        return render(request, "pro_aulavirtual/view_new.html", data)
