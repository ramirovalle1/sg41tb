from datetime import datetime, timedelta
import json
import os
from django.contrib.admin.models import LogEntry, ADDITION, DELETION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.db.transaction import rollback
from django.forms.models import model_to_dict
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template.context import RequestContext
from django.utils.encoding import force_str
from decorators import secure_module
from settings import UTILIZA_GRUPOS_ALUMNOS, GENERAR_RUBROS_PAGO, TIPO_OTRO_RUBRO, TIPO_DERECHOEXAMEN_RUBRO, VALOR_DERECHOEXAMEN_RUBRO, GENERAR_RUBRO_DERECHO, NOTA_PARA_APROBAR, TIPO_AYUDA_FINANCIERA, MODULO_FINANZAS_ACTIVO, EMAIL_ACTIVE, UTILIZA_NIVEL0_PROPEDEUTICO, MODELO_EVALUACION, EVALUACION_TES, TIPO_MORA_RUBRO, UTILIZA_MATRICULA_RECARGO, UTILIZA_FICHA_MEDICA, TIPO_BECA_SENESCYT, EVALUACION_ITS, EVALUACION_IGAD, EVALUACION_ITB, EVALUACION_IAVQ, NIVEL_MALLA_UNO, NUMERO_POSIBLE_DESERTOR,MODELO_EVALUACION,EVALUACION_CASADE, MEDIA_ROOT
from sga.commonviews import addUserData, ip_client_address
from sga.forms import MatriculaForm, MatriculaEditForm, RetiradoMatriculaForm, MatriculaMultipleForm, MatriculaBecaForm, MatriculaProxNivelForm, MatriculaLibreForm, MatriculaExtraForm, EliminacionMatriculaForm
from sga.models import Nivel, Carrera, Sede, Matricula, MateriaAsignada, RecordAcademico, Materia, Leccion, AsistenciaLeccion, RetiradoMatricula, \
    Asignatura, Inscripcion, Rubro, RubroMatricula, HistoricoRecordAcademico, RubroCuota, RubroOtro, TipoOtroRubro, TipoBeneficio, Coordinacion,\
    AsignaturaMalla, NivelMalla, EstudiantesXDesertar, EliminacionMatricula, RubroEspecieValorada, DetalleRetiradoMatricula,Periodo,Egresado,Graduado,elimina_tildes, PagoNivel, Descuento, DetalleDescuento
from django.db import transaction


@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
@transaction.atomic()
def view(request):
    """

    :param request:
    :return:
    """
    if request.method=='POST':
        try:
            if 'action' in request.POST:
                action = request.POST['action']
                if action =='descuentonivel':
                    try:
                        nivel = Nivel.objects.get(id=request.POST['idnivel'])

                        condescuento = 0
                        idcon = []
                        idsin = []
                        sindescuento = 0

                        if request.POST['ids'] !='':
                            idtipo = PagoNivel.objects.filter(id__in=request.POST['ids'].split(',')).values('tipo')
                            for r in RubroCuota.objects.filter(matricula__nivel=nivel,cuota__in=idtipo).order_by('rubro__inscripcion','cuota'):
                                pagonivel = PagoNivel.objects.filter(tipo=r.cuota,nivel=r.matricula.nivel)[:1].get()
                                if r.rubro.puede_eliminarse():
                                    if r.rubro.valor == pagonivel.valor:
                                        porcentaje = float(r.rubro.valor*int(request.POST['porcentaje']))/100
                                        r.rubro.valor = r.rubro.valor - porcentaje
                                        descuento = Descuento(inscripcion = r.rubro.inscripcion,
                                                                motivo = request.POST['observacion'],
                                                                total = porcentaje,
                                                                fecha = datetime.now())
                                        descuento.save()
                                        detalledescuento = DetalleDescuento(descuento = descuento,
                                                                            rubro = r.rubro,
                                                                            valor = porcentaje,
                                                                            porcentaje = float(request.POST['porcentaje']),
                                                                            usuario=request.user,
                                                                            descuota_nivel=True)
                                        detalledescuento.save()
                                        r.rubro.save()
                                        #Obtain client ip address
                                        client_address = ip_client_address(request)

                                        # Log de ADICIONAR MATRICULAS MULTIPLES
                                        LogEntry.objects.log_action(
                                            user_id         = request.user.pk,
                                            content_type_id = ContentType.objects.get_for_model(r.rubro).pk,
                                            object_id       = r.rubro.id,
                                            object_repr     = force_str(r.rubro),
                                            action_flag     = ADDITION,
                                            change_message  = 'Descuento al Nivel desde el modulo de consulta matricula  (' + client_address + ')'  )
                                        if not r.rubro.inscripcion.id in idcon:
                                            if r.rubro.inscripcion.id in idsin:
                                                idsin.remove(r.rubro.inscripcion.id)
                                                sindescuento = sindescuento - 1
                                            idcon.append(r.rubro.inscripcion.id)
                                            condescuento = condescuento + 1
                                    else:
                                        if not r.rubro.inscripcion.id in idsin and not r.rubro.inscripcion.id in idcon :
                                            idsin.append(r.rubro.inscripcion.id)
                                            sindescuento = sindescuento + 1
                                else:
                                    if not r.rubro.inscripcion.id in idsin and not r.rubro.inscripcion.id in idcon:
                                        idsin.append(r.rubro.inscripcion.id)
                                        sindescuento = sindescuento + 1
                        condescuentomat = 0
                        idconmat = []
                        idsinmat = []
                        sindescuento = 0
                        sindescuentomat = 0
                        if request.POST['porcentajemat'] > 0 and  request.POST['idsm'] !='':

                            for r in RubroMatricula.objects.filter(matricula__nivel=nivel).order_by():
                                pagonivel = PagoNivel.objects.filter(tipo=0,nivel=r.matricula.nivel)[:1].get()
                                if r.rubro.puede_eliminarse():
                                    if r.rubro.valor == pagonivel.valor:
                                        porcentaje = float(r.rubro.valor*int(request.POST['porcentajemat']))/100
                                        r.rubro.valor = r.rubro.valor - porcentaje
                                        descuento = Descuento(inscripcion = r.rubro.inscripcion,
                                                                motivo = request.POST['observacion'],
                                                                total = porcentaje,
                                                                fecha = datetime.now())
                                        descuento.save()
                                        detalledescuento = DetalleDescuento(descuento = descuento,
                                                                            rubro = r.rubro,
                                                                            valor = porcentaje,
                                                                            porcentaje = float(request.POST['porcentajemat']),
                                                                            usuario=request.user,
                                                                            descuota_nivel=True)
                                        detalledescuento.save()
                                        r.rubro.save()
                                        #Obtain client ip address
                                        client_address = ip_client_address(request)

                                        # Log de ADICIONAR MATRICULAS MULTIPLES
                                        LogEntry.objects.log_action(
                                            user_id         = request.user.pk,
                                            content_type_id = ContentType.objects.get_for_model(r.rubro).pk,
                                            object_id       = r.rubro.id,
                                            object_repr     = force_str(r.rubro),
                                            action_flag     = ADDITION,
                                            change_message  = 'Descuento al Nivel desde el modulo de Nivel Pago (' + client_address + ')'  )
                                        if not r.rubro.inscripcion.id in idconmat:
                                            if r.rubro.inscripcion.id in idsinmat:
                                                idsinmat.remove(r.rubro.inscripcion.id)
                                                sindescuentomat = sindescuentomat - 1
                                            idconmat.append(r.rubro.inscripcion.id)
                                            condescuentomat = condescuentomat + 1
                                    else:
                                        if not r.rubro.inscripcion.id in idsin and not r.rubro.inscripcion.id in idcon :
                                            idsinmat.append(r.rubro.inscripcion.id)
                                            sindescuentomat = sindescuentomat + 1
                                else:
                                    if not r.rubro.inscripcion.id in idsin and not r.rubro.inscripcion.id in idcon:
                                        idsinmat.append(r.rubro.inscripcion.id)
                                        sindescuentomat = sindescuentomat + 1
                        return HttpResponse(json.dumps({"result":"ok","sindescuento":str(sindescuento),"condescuento":str(condescuento),"sindescuentomat":str(sindescuentomat),"condescuentomat":str(condescuentomat),}),content_type="application/json")
                    except Exception as e:
                        print(e)
                        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
                elif action =='exportar_grupo':
                    grupo = open(os.path.join(MEDIA_ROOT, 'grupo.txt'), 'w')
                    for i in Inscripcion.objects.filter(inscripciongrupo__grupo__nombre=(request.POST['g']).upper()).order_by('persona__apellido1','persona__apellido1'):
                        grupo.write(elimina_tildes(i.persona.usuario.username) +"," +str(i.persona.cedula) +"," + elimina_tildes(i.persona.apellido1) +"," + elimina_tildes(i.persona.nombres) +"," + elimina_tildes(i.persona.emailinst)+ '\n')
                    grupo.close()
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/grupo.txt"}),content_type="application/json")
            return HttpResponseRedirect("/matriculas")
        except:
            return HttpResponseRedirect("/matriculas")
    else:
        try:
            data = {'title': 'Matriculas de Alumnos'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']
                if action=='matricula':
                    data['title'] = 'Matricula de Nivel Academico'
                    nivel = Nivel.objects.get(pk=request.GET['id'])
                    ret = None
                    if 'ret' in request.GET:
                        ret = request.GET['ret']
                    periodo = request.session['periodo']
                    data['nivel'] = nivel
                    data['periodo'] = periodo
                    data['tipo_ayuda_financiera'] = TIPO_AYUDA_FINANCIERA
                    data['usa_modulo_finanzas'] = MODULO_FINANZAS_ACTIVO
                    data['matriculas'] = Matricula.objects.filter(nivel=nivel).order_by('inscripcion__persona__apellido1')
                    data['ret'] = ret if ret else ""
                    data['matriculalibre'] = MODELO_EVALUACION==EVALUACION_TES
                    data['usa_matricula_recargo'] = UTILIZA_MATRICULA_RECARGO
                    data['pagoniveles'] = PagoNivel.objects.filter(nivel=nivel).exclude(tipo=0).order_by('fecha')
                    data['pagomatricula'] = PagoNivel.objects.filter(nivel=nivel,tipo=0).order_by('fecha')
                    data['MODELO_EVALUATIVO'] = [MODELO_EVALUACION, EVALUACION_IAVQ, EVALUACION_ITB, EVALUACION_ITS, EVALUACION_TES, EVALUACION_IGAD]
                    return render(request ,"cons_matriculas/matriculabs.html" ,  data)

                elif action=='materias':
                    ret_nivel = None
                    if 'ret_nivel' in request.GET:
                        ret_nivel = request.GET['ret_nivel']
                    data['ret_nivel'] = ret_nivel if ret_nivel else ""
                    matricula = Matricula.objects.get(pk=request.GET['id'])
                    materias = matricula.materiaasignada_set.all()
                    if 'conf' in request.GET:
                        data['conf']= request.GET['conf']
                    data['matricula'] = matricula
                    data['materias'] = materias
                    if matricula.nivel.nivelmalla_id == NIVEL_MALLA_UNO:
                        materiasnodisponibles = Materia.objects.filter(cerrado=False)
                    else:
                        materiasnodisponibles = Materia.objects.filter(cerrado=False, nivel__periodo=matricula.nivel.periodo)

                    disponibles = []
                    for materiad in materiasnodisponibles:
                        if not materiad.asignatura.id in disponibles:
                            disponibles.append(materiad.asignatura.id)
                    tomadas=[]
                    for materiad in materias:
                        if not materiad.materia.asignatura.id in tomadas:
                            tomadas.append(materiad.materia.asignatura.id)

                    data['asignaturaslibres'] = Asignatura.objects.filter(id__in=disponibles).exclude(recordacademico__inscripcion=matricula.inscripcion).exclude(materia__materiaasignada__matricula=matricula).distinct().order_by('nombre')

                    data['records'] = RecordAcademico.objects.filter(inscripcion=matricula.inscripcion,aprobada=False).order_by('asignatura').exclude(asignatura__id__in=tomadas)

                    data['recordsp'] = RecordAcademico.objects.filter(inscripcion=matricula.inscripcion,aprobada=True).order_by('asignatura')
                    data['genera_rubro_derecho'] = GENERAR_RUBRO_DERECHO
                    return render(request ,"cons_matriculas/materiasbs.html" ,  data)


                return HttpResponseRedirect("/matriculas")
            else:
                if MODELO_EVALUACION==EVALUACION_TES:
                    return HttpResponseRedirect("/cons_niveles")
    #            data['periodo'] = Periodo.periodo_vigente()
                data['sedes'] = Sede.objects.filter(solobodega=False)
                data['carreras'] = Carrera.objects.filter(grupocoordinadorcarrera__group__in=request.user.groups.all()).exclude(activo=False).distinct().order_by('nombre')
                data['niveles'] = Nivel.objects.filter(periodo=data['periodo'], carrera__in=data['carreras']).order_by('paralelo')
                data['niveles_abiertos'] = Nivel.objects.filter(cerrado=False, periodo=data['periodo'], carrera__in=data['carreras']).order_by('paralelo')
                data['usa_nivel0'] = UTILIZA_NIVEL0_PROPEDEUTICO
                # data['inscritos'] = Inscripcion.objects.filter(fecha__gte=data['periodo'].inicio,fecha__lte=data['periodo'].fin).count()
                data['matriculados'] = Matricula.objects.filter(nivel__periodo=data['periodo']).count()
                data['becados'] = Matricula.objects.filter(nivel__periodo=data['periodo'],becado=True).count()
                data['egresados'] = Egresado.objects.filter(fechaegreso__gte=data['periodo'].inicio,fechaegreso__lte=data['periodo'].fin).count()
                data['graduados'] = Graduado.objects.filter(fechagraduado__gte=data['periodo'].inicio,fechagraduado__lte=data['periodo'].fin).count()
                data['inactivos'] = Matricula.objects.filter(nivel__periodo=data['periodo'],inscripcion__persona__usuario__is_active=False).count()
                data['retirados'] = RetiradoMatricula.objects.filter(nivel__periodo=data['periodo']).count()

                return render(request ,"cons_matriculas/matriculasbs.html" ,  data)

        except:
            return HttpResponseRedirect('/matriculas')