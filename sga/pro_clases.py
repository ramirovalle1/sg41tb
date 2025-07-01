# -*- coding: latin-1 -*-
from datetime import datetime, date, timedelta
import json
from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db.models.aggregates import Sum, Avg
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render
from django.utils.encoding import force_str
from decorators import secure_module, inhouse_check, inclassroom_check, inclassroom_check_docente
from settings import PAGO_ESTRICTO, DATOS_ESTRICTO, EMAIL_ACTIVE, ARCHIVO_TIPO_DEBERES, CLASES_CIERRE_ANTES, MODULO_FINANZAS_ACTIVO, FICHA_MEDICA_ESTRICTA, \
     ASIST_PARA_APROBAR, ABRIR_CLASES_DESDE_AULA, MODELO_EVALUACION, EVALUACION_CASADE,PROFE_PRACT_CONDUCCION,VALIDA_MATERIAS, DEFAULT_PASSWORD,SEGUIMIENTO_SYLLABUS, \
     ARCHIVO_TIPO_PLANCLASE, ARCHIVO_TIPO_MATERIALAPOYO, VALIDA_ABRIR_CLASES, TIPO_PERIODO_PROPEDEUTICO,VERIFICA_ACTAENTREGA,TIPOSEGMENTO_PRACT, VALIDA_DEUDA_EXAM_ASIST
from sga.commonviews import addUserData, ip_client_address
from sga.forms import ArchivoDeberForm, ArchivoForm, MotivoApertura, MotivoForm
from sga.models import Profesor, Clase, Leccion, AsistenciaLeccion, EvaluacionLeccion, Turno, Sede, Aula, LeccionGrupo, Materia, Periodo, TipoIncidencia, Incidencia,\
     Archivo, TipoArchivo, Especialidad,ProfesorMateria, Absentismo,MateriaAsignada,Syllabus, CapituloSyllabus, TemaSyllabus,SubTemaSyll,DetalleSubTemaSyll, \
     SeguimientoSyllabus, SeguimientoTema, SeguimientoDetalleTema, DetalleTema, SeguimientoSubTema, SeguimientoDetalleSubTema,MateriaRecepcionActaNotas
from sga.tasks import send_html_mail
from django.db.models.query_utils import Q


@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    """

    """
    if request.method=='POST':
        if 'action' in request.POST:
            action = request.POST['action']
            if action=='asistencia':
                asistenciaLeccion = AsistenciaLeccion.objects.get(pk=request.POST['id'])
                asistenciaLeccion.asistio = request.POST['val'] == 'y'
                asistenciaLeccion.save()

                if MODELO_EVALUACION==EVALUACION_CASADE:
                    porcientoasist = asistenciaLeccion.horas_asistencia_actual()
                else:
                    porcientoasist = asistenciaLeccion.porciento_asistencia_actual()

                for materiaasignada in asistenciaLeccion.matricula.materiaasignada_set.all():
                    materiaasignada.save()

                #OCastillo 07-feb-2022 cuando docente marque asistencia a estudiante absento quitar el absentismo
                if request.POST['val'] == 'y':
                    if Absentismo.objects.filter(materiaasignada__matricula__inscripcion=asistenciaLeccion.matricula.inscripcion, materiaasignada__materia=asistenciaLeccion.leccion.clase.materia,reintegro=False).exists():
                        absento = Absentismo.objects.filter(materiaasignada__matricula__inscripcion=asistenciaLeccion.matricula.inscripcion, materiaasignada__materia=asistenciaLeccion.leccion.clase.materia,reintegro=False)[:1].get()
                        absento.reintegro=True
                        absento.observaadmin='REINTEGRO AUTOMATICO AL DOCENTE MARCAR ASISTENCIA'
                        absento.fechaobserv = datetime.now()
                        absento.finalizado=True
                        absento.fechareintegro = datetime.now().date()
                        absento.materiaasignada.absentismo = False
                        absento.save()
                        absento.materiaasignada.save()
                return HttpResponse(json.dumps({"result":"ok", "porcientoasist": porcientoasist}), content_type="application/json")

            elif action == 'detsubtema':
                try:
                    b = 0
                    detalle2 = SeguimientoDetalleSubTema.objects.get(pk=request.POST['id'])
                    if detalle2.leccion:
                        if not detalle2.leccion.id == int(request.POST['lec']):
                            detalle = SeguimientoDetalleSubTema(seguimientosubtema=detalle2.seguimientosubtema,
                                                                detsubtema=detalle2.detsubtema )
                            detalle.save()
                            b=1
                        else:
                            detalle = detalle2
                    else:
                        detalle = detalle2
                    if request.POST['op'] == '0':
                        detalle.finalizado = False
                    else:
                        detalle.finalizado = True

                    detalle.leccion_id = request.POST['lec']
                    detalle.save()
                    if not detalle.seguimientosubtema.seguimientotema.seguimiento.inicio and b == 0:
                        detalle.seguimientosubtema.seguimientotema.seguimiento.inicio = datetime.now()
                        detalle.seguimientosubtema.seguimientotema.seguimiento.save()
                    if  not detalle.seguimientosubtema.inicio and b == 0:
                        detalle.seguimientosubtema.inicio = datetime.now()
                        detalle.seguimientosubtema.save()
                    if not detalle.seguimientosubtema.seguimientotema.inicio and b == 0:
                        detalle.seguimientosubtema.seguimientotema.inicio = datetime.now()
                        detalle.seguimientosubtema.seguimientotema.save()
                    c = DetalleSubTemaSyll.objects.filter(subtema=detalle.detsubtema.subtema).count()
                    if SeguimientoDetalleSubTema.objects.filter(detsubtema__subtema=detalle.detsubtema.subtema,finalizado=True,seguimientosubtema__seguimientotema__seguimiento__profesor=detalle.seguimientosubtema.seguimientotema.seguimiento.profesor).count() == c:
                       detalle.seguimientosubtema.fin = datetime.now()
                       detalle.seguimientosubtema.finalizado =True
                       detalle.seguimientosubtema.save()
                    detalle.save()

                    cs = SubTemaSyll.objects.filter(tema=detalle.seguimientosubtema.seguimientotema.tema).count()
                    if SeguimientoSubTema.objects.filter(subtema__tema=detalle.seguimientosubtema.seguimientotema.tema,finalizado=True,
                                                         seguimientotema__seguimiento__profesor=detalle.seguimientosubtema.seguimientotema.seguimiento.profesor).count() == cs:
                        detalle.seguimientosubtema.seguimientotema.finalizado = True
                        detalle.seguimientosubtema.seguimientotema.fin =datetime.now()
                        detalle.seguimientosubtema.seguimientotema.save()
                        detalle.seguimientosubtema.finalizado  =True
                        detalle.seguimientosubtema.fin  = datetime.now()
                        detalle.seguimientosubtema.save()

                    t = TemaSyllabus.objects.filter(capitulo__syllabus=detalle.seguimientosubtema.seguimientotema.seguimiento.syllabus,capitulo=detalle.seguimientosubtema.seguimientotema.seguimiento.capitulo).count()
                    if SeguimientoTema.objects.filter(tema__capitulo__syllabus=detalle.seguimientosubtema.seguimientotema.seguimiento.syllabus, tema__capitulo=detalle.seguimientosubtema.seguimientotema.seguimiento.capitulo,finalizado=True,
                                                     seguimiento__profesor=detalle.seguimientosubtema.seguimientotema.seguimiento.profesor).count() == t :
                        detalle.seguimientosubtema.seguimientotema.seguimiento.fin = datetime.now()
                        detalle.seguimientosubtema.seguimientotema.seguimiento.finalizado = True
                        detalle.seguimientosubtema.seguimientotema.seguimiento.save()
                    return HttpResponse(json.dumps({"result":"ok"}), content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({"result":"bad" }), content_type="application/json")

            elif action == 'subtema':
                try:
                    b=0
                    subtema2 = SeguimientoSubTema.objects.get(pk=request.POST['id'])
                    if subtema2.leccion:
                        if not subtema2.leccion.id == int(request.POST['lec']):
                            subtema = SeguimientoSubTema(seguimientotema=subtema2.seguimientotema,
                                                         subtema=subtema2.subtema)
                            subtema.save()
                            b=1
                        else:
                            subtema=subtema2
                    else:
                        subtema=subtema2

                    if request.POST['op'] == '0':
                        subtema.finalizado = False
                    else:
                        subtema.finalizado = True

                    if not SeguimientoDetalleSubTema.objects.filter(seguimientosubtema=subtema).exists() and subtema.finalizado:
                        subtema.fin = datetime.now()
                        subtema.save()


                    subtema.leccion_id = request.POST['lec']
                    subtema.save()
                    if  not subtema.inicio and b == 0:
                        subtema.inicio = datetime.now()
                        subtema.save()
                    if not subtema. seguimientotema.inicio and b == 0:
                        subtema.seguimientotema.inicio=datetime.now()
                        subtema.seguimientotema.save()
                    c = SubTemaSyll.objects.filter(tema=subtema.subtema.tema).count()
                    if SeguimientoSubTema.objects.filter(subtema__tema=subtema.subtema.tema,finalizado=True,
                                                         seguimientotema__seguimiento__profesor=subtema.seguimientotema.seguimiento.profesor).count() == c:
                        subtema.fin = datetime.now()
                        subtema.finalizado =True
                        subtema.save()
                        subtema.seguimientotema.finalizado = True
                        subtema.seguimientotema.fin = datetime.now()
                        subtema.seguimientotema.save()

                    t =  TemaSyllabus.objects.filter(capitulo__syllabus=subtema.seguimientotema.seguimiento.syllabus,capitulo=subtema.seguimientotema.seguimiento.capitulo).count()
                    if SeguimientoTema.objects.filter(tema__capitulo__syllabus=subtema.seguimientotema.seguimiento.syllabus,tema__capitulo=subtema.seguimientotema.seguimiento.capitulo,finalizado=True,
                                                      seguimiento__profesor=subtema.seguimientotema.seguimiento.profesor).count() == t :
                        subtema.seguimientotema.seguimiento.fin = datetime.now()
                        subtema.seguimientotema.seguimiento.finalizado = True
                        subtema.seguimientotema.seguimiento.save()
                    return HttpResponse(json.dumps({"result":"ok"}), content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({"result":"bad" }), content_type="application/json")


            elif action=='addincidencia':
                lecciongrupo = LeccionGrupo.objects.get(pk=request.POST['lecciongrupo'])
                tipo = TipoIncidencia.objects.get(pk=request.POST['tipo'])
                incidencia = Incidencia(lecciongrupo=lecciongrupo, tipo=tipo, contenido=request.POST['contenido'],cerrada=False,fechaingreso=datetime.now())
                incidencia.save()
                if EMAIL_ACTIVE:
                    incidencia.mail_nuevo()

                return HttpResponse(json.dumps({"result":"ok", "tipo": tipo.nombre, "contenido": incidencia.contenido}),content_type="application/json")
            elif action=='evaluar':
                try:
                    valor = float(request.POST['val'])

                    asistenciaLeccion = AsistenciaLeccion.objects.get(pk=request.POST['id'])
                    evaluacionLeccion = EvaluacionLeccion(leccion=asistenciaLeccion.leccion,
                                                        matricula=asistenciaLeccion.matricula,
                                                        evaluacion=valor)
                    evaluacionLeccion.save()
                    return HttpResponse(json.dumps({"result":"ok", "evalid": evaluacionLeccion.id, "promedio": int(asistenciaLeccion.promedio_evaluacion())}), content_type="application/json")
                except:
                    return HttpResponse(json.dumps({"result":"error"}), content_type="application/json")
            elif action=="borrarevaluacion":
                try:
                    asistenciaLeccion = AsistenciaLeccion.objects.get(pk=request.POST['asisid'])
                    evaluacion = EvaluacionLeccion.objects.get(pk=request.POST['evalid'])
                    evaluacion.delete()

                    return HttpResponse(json.dumps({"result":"ok", "promedio": int(asistenciaLeccion.promedio_evaluacion())}), content_type="application/json")
                except:
                    return HttpResponse(json.dumps({"result":"error"}), content_type="application/json")
            elif action=='contenido':
                try:
                    leccionGrupo = LeccionGrupo.objects.get(pk=request.POST['id'])
                    leccionGrupo.contenido = request.POST['val']
                    leccionGrupo.save()
                    return HttpResponse(json.dumps({"result":"ok"}), content_type="application/json")
                except leccionGrupo.DoesNotExist:
                    return HttpResponseRedirect('/')
            elif action=='observaciones':
                leccionGrupo = LeccionGrupo.objects.get(pk=request.POST['id'])
                leccionGrupo.observaciones = request.POST['val']
                leccionGrupo.save()
                return HttpResponse(json.dumps({"result":"ok"}), content_type="application/json")
            elif action=='cerrar':
                leccionGrupo = LeccionGrupo.objects.get(pk=request.POST['id'])
#                ahora = datetime.now().time()
#                fin_rango = (datetime.combine(date.today(), leccionGrupo.turno.termina) + timedelta(minutes=CLASES_CIERRE_ANTES)).time()

#                if ahora > fin_rango:
                return HttpResponse(json.dumps({"result":"ok"}), content_type="application/json")
#                else:
#                    return HttpResponse(json.dumps({"result":"bad"}), content_type="application/json")
            elif action=='nuevaleccion':
                data = {'title': 'Listado de Clases'}
                addUserData(request,data)
                f = MotivoForm(request.POST)
                ban = 0
                if  f.is_valid():
                    hoy = datetime.now().date()
                    profesor = Profesor.objects.get(pk=request.POST['profesor'])
                    turno = Turno.objects.get(pk=request.POST['turno'])
                    aula = Aula.objects.get(pk=request.POST['aula'])
                    clase = Clase.objects.get(pk=request.POST['claseid'])
                    hoy = datetime.now().date()
                    if VALIDA_MATERIAS:
                        if profesor.materias_pendientes():
                            for m in profesor.materias_pendientes():
                                for pm in ProfesorMateria.objects.filter(materia=m,profesor=profesor):
                                    fecha=datetime.strptime(str(str(pm.hasta.day)+'/'+str(pm.hasta.month)+'/'+str((pm.hasta.year))),'%d/%m/%Y')  + timedelta(days=3)
                                    if fecha <  datetime.now():
                                        clase = Clase.objects.filter(Q(materia__nivel__periodo__activo=True, materia__inicio__lte=hoy, materia__fin__gte=hoy, turno=turno, dia=int(request.GET['dia']), aula=aula, materia__profesormateria__desde__lte=hoy, materia__profesormateria__hasta__gte=hoy) & (Q(materia__profesormateria__profesor=profesor,materia__profesormateria__profesor_aux=None) | Q(materia__profesormateria__profesor_aux=profesor.id)))
                                        profesor.mail_aperturafallida(str(clase))
                                        return HttpResponseRedirect("/pro_horarios?info=Tiene materias pendientes de cerrar con fecha superior a 72 horas")
                    if ABRIR_CLASES_DESDE_AULA and not clase.virtual:
                            if not inclassroom_check_docente(request):
                                return HttpResponseRedirect("/?info=Esta funcion solo es accesible desde las aulas autorizadas")

                    # profesor = Profesor.objects.get(pk=request.GET['profesor'])

                    if LeccionGrupo.objects.filter(profesor=profesor,abierta=True).exists():
                        return HttpResponseRedirect("/?info=Ya tiene una clase abierta")


                    if profesor.categoria.id == PROFE_PRACT_CONDUCCION:
                        clases = Clase.objects.filter(materia__nivel__periodo__activo=True, materia__inicio__lte=hoy, materia__fin__gte=hoy, turno=turno, dia=int(request.POST['dia']), aula=aula, materia__profesormateria__profesor_aux=profesor.id, materia__profesormateria__desde__lte=hoy, materia__profesormateria__hasta__gte=hoy)
                    else:
                        clases = Clase.objects.filter(Q(materia__nivel__periodo__activo=True, materia__inicio__lte=hoy, materia__fin__gte=hoy, turno=turno, dia=int(request.POST['dia']), aula=aula, materia__profesormateria__desde__lte=hoy, materia__profesormateria__hasta__gte=hoy) & (Q(materia__profesormateria__profesor=profesor,materia__profesormateria__profesor_aux=None) | Q(materia__profesormateria__profesor_aux=profesor.id)))
                    ids = []
                    # if Materia.objects.filter(pk=clases[0].materia.id).exists():
                    #     m= Materia.objects.filter(pk=clases[0].materia.id)[:1].get()
                    #     if LeccionGrupo.objects.filter(materia=clases[0].materia).exists():
                    #         l=LeccionGrupo.objects.filter(materia=clases[0].materia).aggregate(Sum('turno__horas'))['turno__horas__sum']
                    #         if l >= m.horas :
                    #             return HttpResponseRedirect("/?info=Ha completado el numero de horas establecidas para esa materia ")

                    if ProfesorMateria.objects.filter(materia=clases[0].materia,profesor=profesor,desde__lte=hoy,hasta__gte=hoy,aceptacion=True).exists():
                        pm = ProfesorMateria.objects.get(materia=clases[0].materia,profesor=profesor,desde__lte=hoy,hasta__gte=hoy,aceptacion=True)
                        if ABRIR_CLASES_DESDE_AULA and DEFAULT_PASSWORD == 'itb' and pm.segmento.id != 2 :
                            if not clase.virtual:
                                if not inclassroom_check_docente(request):
                                    return HttpResponseRedirect("/?info=Esta funcion solo es accesible desde las aulas autorizadas")

                        if request.POST['valida']=='1' and pm.segmento.id==2:
                            return HttpResponseRedirect("/pro_horarios?action=horariobs&error=Acceso Denegado encienda el gps")
                        if  LeccionGrupo.objects.filter(materia=clases[0].materia, profesor=profesor, turno=turno,
                                             dia=request.POST['dia'], fecha=datetime.now().date()).exists():
                            return HttpResponseRedirect("/pro_horarios?action=horariobs&error=Ya Existe una clase abierta en este turno y dia")
                    leccionGrupo = LeccionGrupo(materia=clases[0].materia, profesor=profesor, turno=turno,
                                                aula=aula, dia=request.POST['dia'], fecha=datetime.now(),
                                                horaentrada=datetime.now().time(), abierta=True,
                                                contenido='', observaciones='')
                    leccionGrupo.save()
                    if ProfesorMateria.objects.filter(materia=clases[0].materia,profesor_aux__gt=0,profesor=profesor,desde__lte=hoy,hasta__gte=hoy).exists():
                        pm = ProfesorMateria.objects.get(materia=clases[0].materia,profesor_aux__gt=0,profesor=profesor,desde__lte=hoy,hasta__gte=hoy)
                        if pm.profesor_aux:
                            prof=Profesor.objects.get(pk=pm.profesor_aux)
                            leccionGrupo.profesor=  prof
                            leccionGrupo.save()

                    for clase in clases:
                        leccion = Leccion(clase=clase, fecha=datetime.now(),
                                            horaentrada=datetime.now().time(),
                                            abierta=True, contenido='',
                                            observaciones='')
                        leccion.save()
                        leccionGrupo.lecciones.add(leccion)
                        materia = clase.materia
                        asignadas = materia.materiaasignada_set.all()
                        for asignada in asignadas:
                            matricula = asignada.matricula
                            asistenciaLeccion = AsistenciaLeccion(leccion=leccion,
                                                                  matricula=matricula,
                                                                  asistio=False)
                            asistenciaLeccion.save()

                        ids.append(leccion.id)
                    leccionGrupo.save()

                    try:
                        if SEGUIMIENTO_SYLLABUS:
                            if Syllabus.objects.filter(asigmalla__malla=pm.materia.nivel.malla,asigmalla__asignatura=pm.materia.asignatura).exists():
                                syllabus =Syllabus.objects.filter(asigmalla__malla=pm.materia.nivel.malla,asigmalla__asignatura=pm.materia.asignatura)[:1].get()
                                capitulo = CapituloSyllabus.objects.filter(syllabus=syllabus,tiene_detalle=True).order_by('-orden')[:1].get()
                                if not SeguimientoSyllabus.objects.filter(profesor=pm).exists():
                                    seguimiento = SeguimientoSyllabus(profesor =pm,
                                                                      syllabus = syllabus,
                                                                      capitulo = capitulo,
                                                                      inicio=datetime.now())
                                    seguimiento.save()
                                else:
                                    seguimiento = SeguimientoSyllabus.objects.filter(profesor=pm)[:1].get()

                                data['seguimiento'] =seguimiento.id

                                if not SeguimientoTema.objects.filter(seguimiento=seguimiento).exists():
                                    for tema in TemaSyllabus.objects.filter(capitulo=seguimiento.capitulo).order_by('orden'):
                                        segtema = SeguimientoTema(seguimiento=seguimiento,
                                                                  tema = tema)
                                        segtema.save()
                                        if not SeguimientoDetalleTema.objects.filter(seguimientotema=segtema).exists():
                                            for det in DetalleTema.objects.filter(tema=segtema.tema):
                                                segdettema = SeguimientoDetalleTema(seguimientotema=segtema,
                                                                                    detalletema=det)
                                                segdettema.save()
                                        if not SeguimientoSubTema.objects.filter(seguimientotema=segtema).exists():
                                            for  st in SubTemaSyll.objects.filter(tema=segtema.tema).order_by('numero'):
                                                segsubtema = SeguimientoSubTema(seguimientotema = segtema,
                                                                                subtema = st)
                                                segsubtema.save()

                                                if not SeguimientoDetalleSubTema.objects.filter(seguimientosubtema=segsubtema).exists():
                                                    for dst in DetalleSubTemaSyll.objects.filter(subtema=segsubtema.subtema).order_by('numero'):
                                                        segdetsubtema = SeguimientoDetalleSubTema(seguimientosubtema=segsubtema,
                                                                                                  detsubtema = dst)
                                                        segdetsubtema.save()

                    except Exception as e:
                        pass

                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de ABRIR CLASE
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(leccionGrupo).pk,
                        object_id       = leccionGrupo.id,
                        object_repr     = force_str(leccionGrupo),
                        action_flag     = ADDITION,
                        change_message  = 'Abierta Clase Docente - Motivo: '+ f.cleaned_data['motivo'] + ' (' + client_address + ')')
                    if EMAIL_ACTIVE:
                        usuario = request.user
                        leccionGrupo.mail_apertura_docente(usuario,f.cleaned_data['motivo'],client_address)

                    return HttpResponseRedirect("/pro_clases?action=view&id="+str(leccionGrupo.id))
            elif action=='addabsen':
                try:
                    mensaje = "Inactivando"
                    if request.POST['absencheck'] == 'true':
                        activo = True
                        mensaje = "Desactivando"
                    else:
                        activo = False
                    absentismo = Absentismo(
                                    materiaasignada_id = request.POST['idmateriasig'],
                                    observacion = request.POST['observacion'],
                                    fecha = datetime.now()
                                    )
                    absentismo.save()

                    materiaasignada = MateriaAsignada.objects.get(id=request.POST['idmateriasig'])
                    materiaasignada.absentismo = activo
                    materiaasignada.save()
                    client_address = ip_client_address(request)
                    #Log de ADICIONAR INSCRIPCION
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(absentismo).pk,
                        object_id       = absentismo.id,
                        object_repr     = force_str(absentismo),
                        action_flag     = ADDITION,
                        change_message  = mensaje +' absentismo (' + client_address + ')')
                    try:
                        if EMAIL_ACTIVE:
                            absentismo.email_observacion(request.user)
                    except Exception as e:
                        pass
                    return HttpResponse(json.dumps({"result":"ok"}), content_type="application/json")
                except Exception as e:
                   return HttpResponse(json.dumps({"result":"bad"}), content_type="application/json")
            elif action=='adddeberes':
                form = ArchivoDeberForm(request.POST, request.FILES)
                if form.is_valid():
                    try:
                        lecciongrupo = LeccionGrupo.objects.filter(pk=request.POST['lecciongrupo'])[:1].get()
                        lecciones = Leccion.objects.filter(lecciongrupo=request.POST['lecciongrupo'])
                        for lec in lecciones:
                            archivo = Archivo(nombre=form.cleaned_data['nombre'],
                                              materia=lec.clase.materia,
                                              lecciongrupo=lecciongrupo,
                                              fecha=datetime.now(),
                                              archivo = request.FILES['archivo'],
                                              tipo = TipoArchivo.objects.get(pk=ARCHIVO_TIPO_DEBERES),
                                              fechaentrega=form.cleaned_data['fechaentrega'])
                            archivo.save()

                        return HttpResponseRedirect("/pro_clases?action=view&id="+request.POST['lecciongrupo'])
                    except Exception as ex:
                        pass
                return HttpResponseRedirect("/pro_clases?action=adddeberes&id="+request.POST['lecciongrupo']+"&error=1")

            elif action=='addplanclase':
                form = ArchivoForm(request.POST, request.FILES)
                if form.is_valid():
                    try:
                        lecciongrupo = LeccionGrupo.objects.filter(pk=request.POST['lecciongrupo'])[:1].get()
                        lecciones = Leccion.objects.filter(lecciongrupo=request.POST['lecciongrupo'])
                        for lec in lecciones:
                            archivo = Archivo(nombre='PLAN DE CLASE',
                                              materia=lec.clase.materia,
                                              lecciongrupo=lecciongrupo,
                                              fecha=datetime.now(),
                                              archivo = request.FILES['archivo'],
                                              tipo = TipoArchivo.objects.get(pk=ARCHIVO_TIPO_PLANCLASE))
                            archivo.save()

                        return HttpResponseRedirect("/pro_clases?action=view&id="+request.POST['lecciongrupo'])
                    except Exception as ex:
                        pass
                return HttpResponseRedirect("/pro_clases?action=addplanclase&id="+request.POST['lecciongrupo']+"&error=1")

            elif action=='addmaterial':
                form = ArchivoForm(request.POST, request.FILES)
                if form.is_valid():
                    try:
                        lecciongrupo = LeccionGrupo.objects.filter(pk=request.POST['lecciongrupo'])[:1].get()
                        lecciones = Leccion.objects.filter(lecciongrupo=request.POST['lecciongrupo'])
                        for lec in lecciones:
                            archivo = Archivo(nombre='MATERIAL DE APOYO',
                                              materia=lec.clase.materia,
                                              lecciongrupo=lecciongrupo,
                                              fecha=datetime.now(),
                                              archivo = request.FILES['archivo'],
                                              tipo = TipoArchivo.objects.get(pk=ARCHIVO_TIPO_MATERIALAPOYO))
                            archivo.save()

                        return HttpResponseRedirect("/pro_clases?action=view&id="+request.POST['lecciongrupo'])
                    except Exception as ex:
                        pass
                return HttpResponseRedirect("/pro_clases?action=addmaterial&id="+request.POST['lecciongrupo']+"&error=1")
    else:
        data = {'title': 'Listado de Clases'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='nuevaleccion':
                profesor = Profesor.objects.get(pk=request.GET['profesor'])
                turno = Turno.objects.get(pk=request.GET['turno'])
                aula = Aula.objects.get(pk=request.GET['aula'])
                hoy = datetime.now().date()
                if VALIDA_MATERIAS:
                    if profesor.materias_pendientes():
                        for m in profesor.materias_pendientes():
                            for pm in ProfesorMateria.objects.filter(materia=m,profesor=profesor):
                                fecha=datetime.strptime(str(str(pm.hasta.day)+'/'+str(pm.hasta.month)+'/'+str((pm.hasta.year))),'%d/%m/%Y')  + timedelta(days=3)
                                if fecha <  datetime.now():
                                    clase = Clase.objects.filter(Q(materia__nivel__periodo__activo=True, materia__inicio__lte=hoy, materia__fin__gte=hoy, turno=turno, dia=int(request.GET['dia']), aula=aula, materia__profesormateria__desde__lte=hoy, materia__profesormateria__hasta__gte=hoy) & (Q(materia__profesormateria__profesor=profesor,materia__profesormateria__profesor_aux=None) | Q(materia__profesormateria__profesor_aux=profesor.id)))
                                    profesor.mail_aperturafallida(str(clase))
                                    return HttpResponseRedirect("/pro_horarios?info=Tiene materias pendientes de cerrar con fecha superior a 72 horas")
                clase = Clase.objects.get(pk=request.GET['claseid'])
                if ABRIR_CLASES_DESDE_AULA and DEFAULT_PASSWORD != 'itb':
                    if not inclassroom_check_docente(request):
                        return HttpResponseRedirect("/?info=Esta funcion solo es accesible desde las aulas autorizadas")

                # profesor = Profesor.objects.get(pk=request.GET['profesor'])

                if LeccionGrupo.objects.filter(profesor=profesor,abierta=True).exists():
                    return HttpResponseRedirect("/?info=Ya tiene una clase abierta")


                if profesor.categoria.id == PROFE_PRACT_CONDUCCION:
                    clases = Clase.objects.filter(materia__nivel__periodo__activo=True, materia__inicio__lte=hoy, materia__fin__gte=hoy, turno=turno, dia=int(request.GET['dia']), aula=aula, materia__profesormateria__profesor_aux=profesor.id, materia__profesormateria__desde__lte=hoy, materia__profesormateria__hasta__gte=hoy)
                else:
                    # clases = Clase.objects.filter(Q(materia__nivel__periodo__activo=True, materia__inicio__lte=hoy, materia__fin__gte=hoy, turno=turno, dia=int(request.GET['dia']), aula=aula, materia__profesormateria__desde__lte=hoy, materia__profesormateria__hasta__gte=hoy) & (Q(materia__profesormateria__profesor=profesor,materia__profesormateria__profesor_aux=None) | Q(materia__profesormateria__profesor_aux=profesor.id)))
                    clases = Clase.objects.filter(Q(materia__nivel__periodo__activo=True, profesormateria__desde__lte=hoy, profesormateria__hasta__gte=hoy, turno=turno, dia=int(request.GET['dia']), aula=aula) & (Q(profesormateria__profesor=profesor,profesormateria__profesor_aux=None) | Q(profesormateria__profesor_aux=profesor.id)))
                ids = []
                # if Materia.objects.filter(pk=clases[0].materia.id).exists():
                #     m= Materia.objects.filter(pk=clases[0].materia.id)[:1].get()
                #     if LeccionGrupo.objects.filter(materia=clases[0].materia).exists():
                #         l=LeccionGrupo.objects.filter(materia=clases[0].materia).aggregate(Sum('turno__horas'))['turno__horas__sum']
                #         if l >= m.horas :
                #             return HttpResponseRedirect("/?info=Ha completado el numero de horas establecidas para esa materia ")

                if ProfesorMateria.objects.filter(materia=clases[0].materia,profesor=profesor,desde__lte=hoy,hasta__gte=hoy).exists():
                    pm = ProfesorMateria.objects.get(materia=clases[0].materia,profesor=profesor,desde__lte=hoy,hasta__gte=hoy)
                    if ABRIR_CLASES_DESDE_AULA and DEFAULT_PASSWORD == 'itb' and pm.segmento.id != 2:
                        if not clase.virtual:
                            if not inclassroom_check_docente(request):
                                return HttpResponseRedirect("/?info=Esta funcion solo es accesible desde las aulas autorizadas")

                    if request.GET['valida']=='1' and pm.segmento.id==2:
                        return HttpResponseRedirect("/pro_horarios?action=horariobs&error=Acceso Denegado encienda el gps")
                if  LeccionGrupo.objects.filter(materia=clases[0].materia, profesor=profesor, turno=turno,
                                             dia=request.GET['dia'], fecha=datetime.now().date()).exists():
                        return HttpResponseRedirect("/pro_horarios?action=horariobs&error=Ya Existe una Clase Abierta en este turno y dia")


                leccionGrupo = LeccionGrupo(materia=clases[0].materia, profesor=profesor, turno=turno,
                                            aula=aula, dia=request.GET['dia'], fecha=datetime.now(),
                                            horaentrada=datetime.now().time(), abierta=True,
                                            contenido='', observaciones='')
                leccionGrupo.save()
                if ProfesorMateria.objects.filter(materia=clases[0].materia,profesor_aux__gt=0,profesor=profesor,desde__lte=hoy,hasta__gte=hoy).exists():
                    pm = ProfesorMateria.objects.get(materia=clases[0].materia,profesor_aux__gt=0,profesor=profesor,desde__lte=hoy,hasta__gte=hoy)
                    if pm.profesor_aux:
                        prof=Profesor.objects.get(pk=pm.profesor_aux)
                        leccionGrupo.profesor=  prof
                        leccionGrupo.save()

                for clase in clases:
                    leccion = Leccion(clase=clase, fecha=datetime.now(),
                                        horaentrada=datetime.now().time(),
                                        abierta=True, contenido='',
                                        observaciones='')
                    leccion.save()
                    leccionGrupo.lecciones.add(leccion)
                    materia = clase.materia
                    asignadas = materia.materiaasignada_set.all()
                    for asignada in asignadas:
                        matricula = asignada.matricula
                        asistenciaLeccion = AsistenciaLeccion(leccion=leccion,
                                                              matricula=matricula,
                                                              asistio=False)
                        asistenciaLeccion.save()

                    ids.append(leccion.id)
                leccionGrupo.save()

                try:
                    if SEGUIMIENTO_SYLLABUS:
                        if Syllabus.objects.filter(asigmalla__malla=pm.materia.nivel.malla,asigmalla__asignatura=pm.materia.asignatura).exists():
                            syllabus =Syllabus.objects.filter(asigmalla__malla=pm.materia.nivel.malla,asigmalla__asignatura=pm.materia.asignatura)[:1].get()
                            capitulo = CapituloSyllabus.objects.filter(syllabus=syllabus,tiene_detalle=True).order_by('-orden')[:1].get()
                            if not SeguimientoSyllabus.objects.filter(profesor=pm).exists():
                                seguimiento = SeguimientoSyllabus(profesor =pm,
                                                                  syllabus = syllabus,
                                                                  capitulo = capitulo,
                                                                  inicio=datetime.now())
                                seguimiento.save()
                            else:
                                seguimiento = SeguimientoSyllabus.objects.filter(profesor=pm)[:1].get()

                            data['seguimiento'] =seguimiento.id

                            if not SeguimientoTema.objects.filter(seguimiento=seguimiento).exists():
                                for tema in TemaSyllabus.objects.filter(capitulo=seguimiento.capitulo).order_by('orden'):
                                    segtema = SeguimientoTema(seguimiento=seguimiento,
                                                              tema = tema)
                                    segtema.save()
                                    if not SeguimientoDetalleTema.objects.filter(seguimientotema=segtema).exists():
                                        for det in DetalleTema.objects.filter(tema=segtema.tema):
                                            segdettema = SeguimientoDetalleTema(seguimientotema=segtema,
                                                                                detalletema=det)
                                            segdettema.save()
                                    if not SeguimientoSubTema.objects.filter(seguimientotema=segtema).exists():
                                        for  st in SubTemaSyll.objects.filter(tema=segtema.tema).order_by('numero'):
                                            segsubtema = SeguimientoSubTema(seguimientotema = segtema,
                                                                            subtema = st)
                                            segsubtema.save()

                                            if not SeguimientoDetalleSubTema.objects.filter(seguimientosubtema=segsubtema).exists():
                                                for dst in DetalleSubTemaSyll.objects.filter(subtema=segsubtema.subtema).order_by('numero'):
                                                    segdetsubtema = SeguimientoDetalleSubTema(seguimientosubtema=segsubtema,
                                                                                              detsubtema = dst)
                                                    segdetsubtema.save()

                except Exception as e:
                    pass

                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de ABRIR CLASE
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(leccionGrupo).pk,
                    object_id       = leccionGrupo.id,
                    object_repr     = force_str(leccionGrupo),
                    action_flag     = ADDITION,
                    change_message  = 'Abierta la Clase (' + client_address + ')' )

                return HttpResponseRedirect("/pro_clases?action=view&id="+str(leccionGrupo.id))
            elif action =='nuevaclase':
                profesor = Profesor.objects.get(pk=request.GET['profesor'])
                turno = Turno.objects.get(pk=request.GET['turno'])
                aula = Aula.objects.get(pk=request.GET['aula'])
                hoy = datetime.now().date()
                clasehoy = Clase.objects.get(pk=request.GET['claseid'])
                materias_cerradassinactas=[]

                #OC 15-08-2018 verifica si hay materias cerradas sin acta de notas entregadas y no les permit abrir clase
                if VERIFICA_ACTAENTREGA:
                    if profesor.materias_cerradasagosto2018():
                        for mc in profesor.materias_cerradasagosto2018():
                            for pmc in ProfesorMateria.objects.filter(materia=mc,profesor=profesor).exclude(segmento__id=TIPOSEGMENTO_PRACT):
                                    fecha=datetime.strptime(str(str(pmc.hasta.day)+'/'+str(pmc.hasta.month)+'/'+str((pmc.hasta.year))),'%d/%m/%Y')  + timedelta(days=5)
                                    if fecha <  datetime.now():
                                        if MateriaRecepcionActaNotas.objects.filter(materia=pmc.materia).exists():
                                            if MateriaRecepcionActaNotas.objects.filter(materia=pmc.materia,entregada=False):
                                                materias_cerradassinactas.append((pmc.materia.asignatura.nombre,pmc.materia.nivel.nivelmalla.nombre,pmc.materia.nivel.grupo.nombre,pmc.materia.fechacierre))
                                        else:
                                            materias_cerradassinactas.append((pmc.materia.asignatura.nombre,pmc.materia.nivel.nivelmalla.nombre,pmc.materia.nivel.grupo.nombre,pmc.materia.fechacierre))

                        clase = Clase.objects.filter(Q(materia__nivel__periodo__activo=True, materia__inicio__lte=hoy, materia__fin__gte=hoy, turno=turno, dia=int(request.GET['dia']), aula=aula, materia__profesormateria__desde__lte=hoy, materia__profesormateria__hasta__gte=hoy) & (Q(materia__profesormateria__profesor=profesor,materia__profesormateria__profesor_aux=None) | Q(materia__profesormateria__profesor_aux=profesor.id)))
                        profesor.mail_materias_cerradassinactanotas(str(clase),materias_cerradassinactas)
                        return HttpResponseRedirect("/?info=No puede abrir clase. Tiene materias cerradas pendientes de entregar Acta de Notas")

                # # if ABRIR_CLASES_DESDE_AULA :
                        # if not inclassroom_check_docente(request) and not clasehoy.virtual:
                          #   return HttpResponseRedirect("/?info=Esta funcion solo es accesible desde las aulas autorizadas")
                data['title'] = 'Motivo Apertura de Clase'
                data['form'] = MotivoForm()
                data['turno'] = turno
                data['profesor'] = profesor
                data['aula'] = aula
                data['dia'] = request.GET['dia']
                data['valida'] = request.GET['valida']
                data['claseid'] = request.GET['claseid']
                return render(request ,"pro_clases/motivo_apertura.html" ,  data)
               ## else:
                   # return HttpResponseRedirect("/pro_clases")
            elif action=='view':
                data['title'] = 'Leccion'
                if 'ret' in request.GET:
                    data['ret'] = request.GET['ret']
                if 'reg' in request.GET:
                    data['reg'] = request.GET['reg']
                hoy = datetime.now().date()
                leccionGrupo = LeccionGrupo.objects.get(pk=request.GET['id'])
                if not leccionGrupo.profesor.persona.usuario == request.user:
                    return HttpResponseRedirect("/pro_horarios?action=horariobs&error=Acceso Denegado")

                if ProfesorMateria.objects.filter(materia=leccionGrupo.materia,profesor=leccionGrupo.profesor,aceptacion=True).exists():
                    try:
                        data['profesormateria'] = ProfesorMateria.objects.get(materia=leccionGrupo.materia,profesor=leccionGrupo.profesor,desde__lte=hoy,hasta__gte=hoy,aceptacion=True)
                    except:
                        data['profesormateria'] = ProfesorMateria.objects.filter(materia=leccionGrupo.materia,profesor=leccionGrupo.profesor,aceptacion=True)[:1].get()
                else:
                    try:
                        data['profesormateria'] = ProfesorMateria.objects.get(materia=leccionGrupo.materia,profesor_aux=leccionGrupo.profesor.id,desde__lte=hoy,hasta__gte=hoy,aceptacion=True)
                    except:
                        data['profesormateria'] = ProfesorMateria.objects.filter(materia=leccionGrupo.materia,profesor_aux=leccionGrupo.profesor.id,aceptacion=True)[:1].get()

                if 'valida' in request.GET:
                    if request.GET['valida']=='1' and data['profesormateria'].segmento.id==2:
                        return HttpResponseRedirect("/pro_horarios?action=horariobs&error=Acceso Denegado encienda el gps")
                lecciones = leccionGrupo.lecciones.all()

                data['lecciongrupo'] = leccionGrupo
                data['lecciones'] = lecciones
                data['tiposincidencias'] = TipoIncidencia.objects.filter(tipocorreo=False)
                if Incidencia.objects.filter(lecciongrupo=leccionGrupo).exists():
                    data['incidencias'] = Incidencia.objects.filter(lecciongrupo=leccionGrupo)
                else:
                    data['incidencias'] = []
                if Archivo.objects.filter(lecciongrupo=leccionGrupo,tipo__id=ARCHIVO_TIPO_DEBERES).exists():
                    data['deber'] = Archivo.objects.filter(lecciongrupo=leccionGrupo,tipo__id=ARCHIVO_TIPO_DEBERES)[:1].get()
                else:
                    data['deber'] = None

                if Archivo.objects.filter(lecciongrupo=leccionGrupo,tipo__id=ARCHIVO_TIPO_PLANCLASE).exists():
                    data['planclase'] = Archivo.objects.filter(lecciongrupo=leccionGrupo,tipo__id=ARCHIVO_TIPO_PLANCLASE)[:1].get()
                else:
                    data['planclase'] = None

                if Archivo.objects.filter(lecciongrupo=leccionGrupo,tipo__id=ARCHIVO_TIPO_MATERIALAPOYO).exists():
                    data['material'] = Archivo.objects.filter(lecciongrupo=leccionGrupo,tipo__id=ARCHIVO_TIPO_MATERIALAPOYO)[:1].get()
                else:
                    data['material'] = None
                data['ARCHIVO_TIPO_PLANCLASE'] = ARCHIVO_TIPO_PLANCLASE
                data['lec'] = LeccionGrupo.objects.filter(materia__nivel__periodo__activo=True,materia=leccionGrupo.materia,profesor=leccionGrupo.profesor).count()

                #Variables del settings para el control o no de pagos, datos personales y ficha medica de estudiantes
                data['incluyepago'] = PAGO_ESTRICTO
                data['VALIDA_DEUDA_EXAM_ASIST'] = VALIDA_DEUDA_EXAM_ASIST
                data['incluyedatos'] = DATOS_ESTRICTO
                data['incluyedatosmedicos'] = FICHA_MEDICA_ESTRICTA
                data['modulofinanzas'] = MODULO_FINANZAS_ACTIVO
                if leccionGrupo.materia.nivel.carrera.online:
                    data['ASISTENCIA_APROBAR'] = 0
                else:
                    data['ASISTENCIA_APROBAR'] = ASIST_PARA_APROBAR
                    # Si usa o no las Finanzas

                data['DEFAULT_PASSWORD'] = DEFAULT_PASSWORD
                data['MODELO_EVALUATIVO'] = [MODELO_EVALUACION, EVALUACION_CASADE]
                data['SEGUIMIENTO_SYLLABUS'] =SEGUIMIENTO_SYLLABUS
                if SeguimientoSyllabus.objects.filter(profesor=data['profesormateria']).exists():
                     data['seguimiento'] = SeguimientoSyllabus.objects.filter(profesor=data['profesormateria'])[:1].get()
                     data['seguimientotema'] = SeguimientoTema.objects.filter(seguimiento=data['seguimiento'] )
                     data['seguimientodettema'] = SeguimientoDetalleTema.objects.filter(seguimientotema__in= data['seguimientotema'] )
                     data['seguimientosubtema'] = SeguimientoSubTema.objects.filter(seguimientotema__in= data['seguimientotema'])
                     data['seguimientodetsubtema'] = SeguimientoDetalleSubTema.objects.filter(seguimientosubtema__in=data['seguimientosubtema'] )
                     if SeguimientoTema.objects.filter(seguimiento=data['seguimiento'],finalizado=False ).exists():
                        data['tema'] =  SeguimientoTema.objects.filter(seguimiento=data['seguimiento'],finalizado=False ).order_by('tema__orden')[:1].get()
                        if  SeguimientoSubTema.objects.filter(seguimientotema__in= data['seguimientotema'],subtema__tema=data['tema'].tema ,finalizado=False ).exists():
                            st  =  SeguimientoSubTema.objects.filter(seguimientotema__in= data['seguimientotema'],subtema__tema=data['tema'].tema ,finalizado=True ).distinct('subtema').values('subtema')
                            data['subtema'] = SeguimientoSubTema.objects.filter(seguimientotema__in= data['seguimientotema'],subtema__tema=data['tema'].tema ,finalizado=False ).exclude(subtema__in=st).order_by('subtema__numero','-id')[:1].get()
                            v = SeguimientoDetalleSubTema.objects.filter(seguimientosubtema__in=data['seguimientosubtema'], detsubtema__subtema=data['subtema'].subtema,finalizado=True).distinct('detsubtema').values('detsubtema')
                            if SeguimientoDetalleSubTema.objects.filter(seguimientosubtema__in=data['seguimientosubtema'], detsubtema__subtema=data['subtema'].subtema,finalizado=False).exclude(detsubtema__in=v).exists():
                                data['detsubtema'] = SeguimientoDetalleSubTema.objects.filter(seguimientosubtema__in=data['seguimientosubtema'], detsubtema__subtema=data['subtema'].subtema,finalizado=False).exclude(detsubtema__in=v).order_by('detsubtema__numero','-id')[:1].get()
                            # else:
                return render(request ,"pro_clases/leccionbs.html" ,  data)

            elif action=='adddeberes':
                data['title'] = 'Adicionar Deberes'
                lecciongrupo = LeccionGrupo.objects.get(pk=request.GET['id'])
                materia = lecciongrupo.materia
                data['materia'] = materia
                data['lecciongrupo'] = lecciongrupo
                data['form'] = ArchivoDeberForm(initial={'fechaentrega':datetime.now()})
                if 'error' in request.GET:
                    data['formerror'] = "Los archivos que son subidos no deben tener tildes, '&ntilde;' u otros caracteres especiales en su nombre, ser del tipo especificado y no exceder el tama&ntildeo m&aacute;ximo."
                return render(request ,"pro_clases/adddeberesbs.html" ,  data)

            elif action=='addplanclase':
                data['title'] = 'Adicionar Plan de Clase'
                lecciongrupo = LeccionGrupo.objects.get(pk=request.GET['id'])
                materia = lecciongrupo.materia
                data['materia'] = materia
                data['lecciongrupo'] = lecciongrupo
                data['form'] = ArchivoForm()
                if 'error' in request.GET:
                    data['formerror'] = "Los archivos que son subidos no deben tener tildes, '&ntilde;' u otros caracteres especiales en su nombre, ser del tipo especificado y no exceder el tama&ntildeo m&aacute;ximo."
                return render(request ,"pro_clases/adddplanclase.html" ,  data)

            elif action=='addmaterial':
                data['title'] = 'Adicionar Plan de Clase'
                lecciongrupo = LeccionGrupo.objects.get(pk=request.GET['id'])
                materia = lecciongrupo.materia
                data['materia'] = materia
                data['lecciongrupo'] = lecciongrupo
                data['form'] = ArchivoForm()
                if 'error' in request.GET:
                    data['formerror'] = "Los archivos que son subidos no deben tener tildes, '&ntilde;' u otros caracteres especiales en su nombre, ser del tipo especificado y no exceder el tama&ntildeo m&aacute;ximo."
                return render(request ,"pro_clases/addmaterial.html" ,  data)

            elif action == 'avanzarsyll':
                    seguimiento = SeguimientoSyllabus.objects.get(pk=request.GET['id'])
                    seguimiento.finalizado=True
                    seguimiento.save()
                    subtema=None
                    nuevodetalle=None

                    if seguimiento.detallesyll:
                        # s = SeguimientoSyllabus.objects.filter(lecciongrupo=seguimiento.lecciongrupo)
                        d= SeguimientoSyllabus.objects.filter(detallesyll__subtema__tema=seguimiento.detallesyll.subtema.tema).values('detallesyll__id')
                        # if DetalleSubTemaSyll.objects.filter(detallesyll=seguimiento.detallesyll,lecciongrupo=lecciongrupo)
                        if DetalleSubTemaSyll.objects.filter(subtema=seguimiento.detallesyll.subtema).exclude(id__in=d).exists():
                            # detalle= DetalleSubTemaSyll.objects.filter(subtema=seguimiento.detallesyll.subtema).exclude(id=seguimiento.detallesyll.id).values('id')
                            nuevodetalle = DetalleSubTemaSyll.objects.filter(subtema=seguimiento.detallesyll.subtema).exclude(id__in=d).order_by('numero')[:1].get()

                        else:
                            t = TemaSyllabus.objects.filter(capitulo=seguimiento.detallesyll.subtema.tema.capitulo).values('id')
                            if  SubTemaSyll.objects.filter(tema=seguimiento.detallesyll.subtema.tema.id).exclude(id__in=DetalleSubTemaSyll.objects.filter(id__in=d).values('subtema')).exists():
                                subtema = SubTemaSyll.objects.filter(tema=seguimiento.detallesyll.subtema.tema.id).exclude(id__in=DetalleSubTemaSyll.objects.filter(id__in=d).values('subtema')).order_by('numero')[:1].get()
                                if  DetalleSubTemaSyll.objects.filter(subtema=subtema).exists():
                                    nuevodetalle = DetalleSubTemaSyll.objects.filter(subtema=subtema).order_by('numero')[:1].get()


                            elif TemaSyllabus.objects.filter(capitulo=seguimiento.detallesyll.subtema.tema.capitulo).exclude(id__in=t).exists():
                                tema=TemaSyllabus.objects.filter(capitulo=seguimiento.detallesyll.subtema.tema.capitulo).exclude(id__in=t).order_by('numero')[:1].get()
                                if  SubTemaSyll.objects.filter(tema=tema).exists():
                                    subtema = SubTemaSyll.objects.filter(tema=tema).order_by('numero')[:1].get()
                                    if  DetalleSubTemaSyll.objects.filter(subtema=subtema).exists():
                                        nuevodetalle = DetalleSubTemaSyll.objects.filter(subtema=subtema).order_by('numero')[:1].get()

                        # elif TemaSyllabus.objects.get(capitulo=seguimiento.detallesyll.subtema.tema.capitulo).exc
                        #     pass
                        # return HttpResponseRedirect("/pro_clases?action=view&id="+str(seguimiento.lecciongrupo.id))
                    elif seguimiento.subtema:
                        s= SeguimientoSyllabus.objects.filter(subtema__tema=seguimiento.subtema.tema).values('subtema__id')
                        if DetalleSubTemaSyll.objects.filter(subtema=seguimiento.subtema).exclude(id__in=s).exists():
                        # detalle= DetalleSubTemaSyll.objects.filter(subtema=seguimiento.detallesyll.subtema).exclude(id=seguimiento.detallesyll.id).values('id')
                            nuevodetalle = DetalleSubTemaSyll.objects.filter(subtema=seguimiento.subtema).exclude(id__in=s).order_by('numero')[:1].get()
                        else:
                            ts = TemaSyllabus.objects.filter(capitulo=seguimiento.subtema.tema.capitulo).values('id')
                            if  SubTemaSyll.objects.filter(tema=seguimiento.subtema.tema.id).exclude(id__in=DetalleSubTemaSyll.objects.filter(id__in=ts).values('subtema')).exists():
                                subtema = SubTemaSyll.objects.filter(tema=seguimiento.subtema.tema.id).exclude(id__in=DetalleSubTemaSyll.objects.filter(id__in=ts).values('subtema')).order_by('numero')[:1].get()
                                if  DetalleSubTemaSyll.objects.filter(subtema=subtema).exists():
                                    nuevodetalle = DetalleSubTemaSyll.objects.filter(subtema=subtema).order_by('numero')[:1].get()


                            elif TemaSyllabus.objects.filter(capitulo=seguimiento.subtema.tema.capitulo).exclude(id__in=ts).exists():
                                tema=TemaSyllabus.objects.filter(capitulo=seguimiento.subtema.tema.capitulo).exclude(id__in=ts).order_by('numero')[:1].get()
                                if  SubTemaSyll.objects.filter(tema=tema).exists():
                                    subtema = SubTemaSyll.objects.filter(tema=tema).order_by('numero')[:1].get()
                                    if  DetalleSubTemaSyll.objects.filter(subtema=subtema).exists():
                                        nuevodetalle = DetalleSubTemaSyll.objects.filter(subtema=subtema).order_by('numero')[:1].get()


                    if subtema and not nuevodetalle:
                        nuevoseguimiento = SeguimientoSyllabus(lecciongrupo=seguimiento.lecciongrupo,
                                                                     subtema=subtema)
                        nuevoseguimiento.save()
                    elif nuevodetalle:
                    # if not SeguimientoSyllabus.objects.filter(lecciongrupo=seguimiento.lecciongrupo,detallesyll=nuevodetalle).exists():
                        nuevoseguimiento = SeguimientoSyllabus(lecciongrupo=seguimiento.lecciongrupo,
                                                                     detallesyll=nuevodetalle)
                        nuevoseguimiento.save()
                    return HttpResponseRedirect("/pro_clases?action=view&id="+str(seguimiento.lecciongrupo.id))

            elif action=='deldeber':
                try:
                    archivo = Archivo.objects.filter(lecciongrupo=request.GET['id'],tipo__id=ARCHIVO_TIPO_DEBERES)
                    archivo.delete()
                except:
                    pass
                return HttpResponseRedirect("/pro_clases?action=view&id="+request.GET['id'])

            elif action=='delplanclase':
                try:
                    archivo = Archivo.objects.filter(lecciongrupo=request.GET['id'],tipo__id=ARCHIVO_TIPO_PLANCLASE)
                    archivo.delete()
                except:
                    pass
                return HttpResponseRedirect("/pro_clases?action=view&id="+request.GET['id'])

            elif action=='delmaterial':
                try:
                    archivo = Archivo.objects.filter(lecciongrupo=request.GET['id'],tipo__id=ARCHIVO_TIPO_MATERIALAPOYO)
                    archivo.delete()
                except:
                    pass
                return HttpResponseRedirect("/pro_clases?action=view&id="+request.GET['id'])

            elif action=='cerrar':
                leccionGrupo = LeccionGrupo.objects.get(pk=request.GET['id'])
                absentismo = []
                deuda = []
                absentismoclas= MateriaAsignada.objects.filter(absentismo=True,materia=leccionGrupo.materia).count()
                # materiaasignada=MateriaAsignada.objects.filter(pk=request.POST['id'])
                asistenciato= leccionGrupo.asistencia_real()
                faltas=leccionGrupo.inasistencia_real()
                totalasis= leccionGrupo.totales_estudiantes()

                if leccionGrupo.abierta:
                    leccionGrupo.abierta = False
                    horasturno= ((datetime.combine(leccionGrupo.fecha,leccionGrupo.turno.termina) - datetime.combine (leccionGrupo.fecha, leccionGrupo.turno.comienza)).seconds)/60
                    leccionGrupo.horasalida = datetime.now().time()
                    leccionGrupo.fechasalida = datetime.now().date()
                    leccionGrupo.save()

                    if leccionGrupo.horaentrada<leccionGrupo.turno.comienza:
                        fechaentrada=datetime.combine(leccionGrupo.fecha,leccionGrupo.turno.comienza)
                    else:
                        fechaentrada=datetime.combine(leccionGrupo.fecha,leccionGrupo.horaentrada)

                    fechasalida=datetime.combine(leccionGrupo.fechasalida,leccionGrupo.horasalida)

                    minutosleccion = ((fechasalida-fechaentrada).seconds)/60
                    minutoscierre=horasturno-minutosleccion

                    leccionGrupo.minutosleccion=minutosleccion
                    leccionGrupo.minutoscierre=minutoscierre
                    leccionGrupo.save()

                    for leccion in leccionGrupo.lecciones.all():
                        leccion.abierta = False
                        leccion.horasalida = datetime.now().time()
                        leccion.save()
                    if leccionGrupo.materia.nivel.periodo.tipo.id != TIPO_PERIODO_PROPEDEUTICO :
                        for asignadomateria in leccionGrupo.materia.asignados_a_esta_materia():
                            if not asignadomateria.absentismo :
                                al = AsistenciaLeccion.objects.filter(matricula=asignadomateria.matricula, leccion__clase__materia=asignadomateria.materia).order_by('-leccion__fecha').values('id')[0:3]
                                if  AsistenciaLeccion.objects.filter(matricula=asignadomateria.matricula, leccion__clase__materia=asignadomateria.materia,pk__in=al,asistio=False).count() >=3:
                                    absentismo.append((asignadomateria.matricula.inscripcion.persona.nombre_completo_inverso(),asignadomateria.matricula.inscripcion.persona.telefono,asignadomateria.matricula.inscripcion.persona.telefono_conv))
                                    if not Absentismo.objects.filter(materiaasignada=asignadomateria).exists():
                                        absentismofalta = Absentismo(materiaasignada = asignadomateria,
                                            observacion = 'ABSENTISMO GUARDADO POR CONTAR CON MAS DE 3 FALTAS',
                                            fecha = datetime.now())
                                        absentismofalta.save()
                                        asignadomateria.absentismo=True
                                        asignadomateria.save()

                            if asignadomateria.matricula.inscripcion.tiene_deuda():
                                deuda.append((asignadomateria.matricula.inscripcion.persona.nombre_completo_inverso(),str(asignadomateria.matricula.inscripcion.adeuda_a_la_fecha()),asignadomateria.matricula.inscripcion.persona.telefono,asignadomateria.matricula.inscripcion.persona.telefono_conv))

                        if len(absentismo)>0:
                            mail_absentos(absentismo,leccionGrupo)

                        if len(deuda)>0:
                            mail_deuda(deuda,leccionGrupo)
                    leccionGrupo.resumen_clase(absentismoclas,asistenciato,faltas,totalasis)
                    client_address = ip_client_address(request)

                    # Log de ABRIR CLASE
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(leccionGrupo).pk,
                        object_id       = leccionGrupo.id,
                        object_repr     = force_str(leccionGrupo),
                        action_flag     = ADDITION,
                        change_message  = 'Clase Cerrada (' + client_address + ')' )

            return HttpResponseRedirect("/pro_clases")
        else:
            persona = data['persona']
            try:
                profesor = Profesor.objects.get(persona=persona)
                filtro = None
                if 'filter' in request.GET:
                    filtro = request.GET['filter']
                if filtro:
                    materia = Materia.objects.get(pk=filtro)
                    leccionesGrupo = LeccionGrupo.objects.filter(materia__nivel__periodo__activo=True,materia=materia,profesor=profesor).order_by('-fecha', '-horaentrada')
                else:
                    leccionesGrupo = LeccionGrupo.objects.filter(profesor=profesor, materia__nivel__periodo__activo=True).order_by('-fecha', '-horaentrada')
                paging = Paginator(leccionesGrupo, 50)
                p=1
                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                    page = paging.page(p)
                except:
                    page = paging.page(1)
                data['paging'] = paging
                data['page'] = page
                data['leccionesgrupo'] = page.object_list
                data['filter'] = materia if filtro else ""
                materias = Materia.objects.filter(Q(nivel__cerrado=False)& (Q(profesormateria__profesor=profesor,profesormateria__profesor_aux=None) | Q(profesormateria__profesor_aux=profesor.id)))
                data['materias'] = materias
                return render(request ,"pro_clases/clasesbs.html" ,  data)
            except Exception as ex:
                print(ex)
                return HttpResponseRedirect("/")

def mail_absentos(absentos,leccionGrupo):
    correo=TipoIncidencia.objects.get(pk=52)
    hoy = datetime.now().date()
    contenido = "ESTUDIANTES CON 3 O MAS FALTAS EN LAS ULTIMAS CLASES"
    send_html_mail("NOTIFICACION ABSENTOS",
        "emails/notificacion_absento.html", { 'fecha': hoy,'contenido': contenido,'absentos':absentos,'leccionGrupo':leccionGrupo},correo.correo.split(","))

def mail_deuda(deuda,leccionGrupo):
    correo=TipoIncidencia.objects.get(pk=51)
    hoy = datetime.now().date()
    contenido = "ESTUDIANTES CON DEUDA"
    send_html_mail("NOTIFICACION ESTUDIANTES CON DEUDA",
        "emails/notificacion_deuda.html", { 'fecha': hoy,'contenido': contenido,'deuda':deuda,'leccionGrupo':leccionGrupo},correo.correo.split(","))


def procesoquitarabsentimo(request):
    if request.method == 'GET':
        absento=''
        try:
            for absento in Absentismo.objects.filter(finalizado=False):
                identificacion=''
                if absento.materiaasignada.matricula.inscripcion.persona.cedula:
                    identificacion=absento.materiaasignada.matricula.inscripcion.persona.cedula
                else:
                    identificacion=absento.materiaasignada.matricula.inscripcion.persona.pasaporte

                if not absento.materiaasignada.matricula.esta_retirado_inscripcion():
                    if AsistenciaLeccion.objects.filter(Q(asistio=True,matricula__inscripcion__persona__cedula=identificacion)|Q(asistio=True,matricula__inscripcion__persona__pasaporte=identificacion),leccion__fecha__gte=absento.fecha.date()).exists():
                        absento.reintegro=True
                        absento.observaadmin='ABSENTISMO FINALIZADO POR PROCESO AUTOMATICO'
                        absento.fechaobserv = datetime.now()
                        absento.finalizado=True
                        absento.save()
                        absento.materiaasignada.absentismo=False
                        absento.materiaasignada.save()
                        # print(absento.materiaasignada.matricula.inscripcion.persona.nombre_completo_inverso())
            return HttpResponseRedirect('/?info=Proceso ok')
        except Exception as e:
            print(str(e))
            return HttpResponseRedirect('/?info=Proceso no ok'+str(absento))
    else:
        return HttpResponseRedirect("/")
