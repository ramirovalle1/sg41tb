from datetime import datetime, timedelta
import json
from django.db.models import F, Q
from django.http import HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from settings import ID_TIPO_ESPECIE_REG_NOTA, ESPECIE_ASENTAMIENTOCONVENIO_SINVALOR, \
    ESPECIE_ASENTAMIENTOCONVENIO_CONVALOR, TIPOSEGMENTO_TEORIA, TIPO_CURSOS_RUBRO, TIPO_RUBRO_CREDENCIAL, \
    TIPO_CONGRESO_RUBRO, ALUMNOS_GROUP_ID, COORDINACION_UASSS, ASIG_VINCULACION, UTILIZA_FICHA_SOCIOECONOMICA, \
    DIAS_ESPECIE, VALOR_COMISION_REFERIDO, TIPO_RUBRO_MATERIALAPOYO, TIPO_CUOTA_RUBRO, EMAIL_ACTIVE, \
    NIVEL_MALLA_UNO
from sga.funciones import sumar_mes
from sga.models import NotificacionPersona, GestionTramite, Notificacion, elimina_tildes, Periodo, Carrera, Materia, \
    Profesor, PeriodoEvaluacion, CoordinadorCarreraPeriodo, EvaluacionCoordinadorDocente, EvaluacionDocentePeriodo, \
    EvaluacionDirectivoPeriodo, Inscripcion, Rubro, Persona, LeccionGrupo, MateriaAsignada, EvaluacionAlumno, \
    ProfesorMateria, EvaluacionMateria, MateriaRecepcionActaNotas, Coordinacion, ReferidosInscripcion, RubroSeguimiento, \
    AsistAsuntoEstudiant, RubroEspecieValorada, EvaluacionAlcance, DirferidoRubro, RubroOtro, InscripcionTestIngreso, \
    EncuestaItb, Matricula, Nivel, DetalleTutoriaPedagogica, TutoriaPedagogica
from sga.tasks import send_html_mail


def change_sesion_notificaciones(request):
    request.session['bloquea_notificaciones'] = not request.session['bloquea_notificaciones']

def view(request):
    if request.method == 'POST':
        if 'action' in request.POST:
            a = request.POST['action']
            if a == 'mostrar_detalle':
                try:
                    notificacion = Notificacion.objects.get(pk=request.POST['id'])
                    funcion = globals()[notificacion.funcion]
                    detalle = funcion(request, True, notificacion.id)

                    return HttpResponse(json.dumps({"result":"ok", 'detalle':detalle}), content_type="application/json")
                except Exception as e:
                    print("ERROR mostrar_detalle: "+str(e))
                    return HttpResponse(json.dumps({"result":"bad", 'mensaje':str(e)}), content_type="application/json")

            elif a == 'update_periodo':
                try:
                    request.session['periodo'] = Periodo.objects.get(pk=int(request.POST['periodo_id']))
                    return HttpResponse(json.dumps({"result":"ok"}), content_type="application/json")
                except Exception as e:
                    print("ERROR mostrar_detalle: "+str(e))
                    return HttpResponse(json.dumps({"result":"bad", 'mensaje':str(e)}), content_type="application/json")

            elif a == 'save_convenio_pago':
                try:
                    print(request.POST)
                    inscripcion = Inscripcion.objects.filter(persona__usuario__is_active=True, persona__usuario=request.user)[:1].get()
                    diferido = DirferidoRubro.objects.filter(rubroespecie__disponible=True, aprobado=None, fechaaprobacion=None, rubroespecie__rubro__inscripcion=inscripcion).exclude(seguimiento__cerrada=True).exclude(seguimiento__cerrada=True).exclude(rubroespecie__aplicada=True).order_by('-id')[:1].get()
                    nuevos_rubros = []
                    if request.POST['tipo'] == 'aceptar':
                        rubros = Rubro.objects.filter(id__in=diferido.rubrosanteriores.split(','))
                        for r in rubros:
                            r.valor = r.total_pagado()
                            r.cancelado = True
                            r.save()

                        valor = diferido.totaldiferido/diferido.num_cuotas
                        fecha = diferido.fechaprimerpago
                        for x in range(diferido.num_cuotas):
                            rubro = Rubro(fecha=datetime.today().date(),
                                          valor=valor,
                                          inscripcion=inscripcion,
                                          cancelado=False,
                                          fechavence=fecha)
                            rubro.save()
                            rubro_otro = RubroOtro(rubro=rubro,
                                                   tipo_id=TIPO_CUOTA_RUBRO,
                                                   descripcion='DIFERIDO CONVENIO PAGO #'+str(x+1))
                            rubro_otro.save()
                            fecha = sumar_mes(fecha)
                            nuevos_rubros.append(rubro.id)

                        diferido.rubrosactuales = ','.join(map(str, nuevos_rubros))
                        diferido.aprobado = True
                        diferido.fechaaprobacion = datetime.now().date()
                        diferido.save()

                        diferido.rubroespecie.autorizado = True
                        diferido.rubroespecie.obsautorizar = "ALUMNO APRUEBA CONVENIO DE PAGO"
                        diferido.rubroespecie.usrautoriza = inscripcion.persona.usuario
                        diferido.rubroespecie.fechafinaliza = datetime.now().date()
                        diferido.rubroespecie.aplicada = True
                        diferido.rubroespecie.disponible = False
                        diferido.rubroespecie.save()

                    elif request.POST['tipo'] == 'rechazar':
                        diferido.aprobado = False
                        diferido.fechaaprobacion = datetime.now().date()
                        diferido.save()

                        diferido.rubroespecie.autorizado = False
                        diferido.rubroespecie.obsautorizar = "ALUMNO RECHAZA CONVENIO DE PAGO"
                        diferido.rubroespecie.usrautoriza = inscripcion.persona.usuario
                        diferido.rubroespecie.fechafinaliza = datetime.now().date()
                        diferido.rubroespecie.aplicada = True
                        diferido.rubroespecie.disponible = False
                        diferido.rubroespecie.save()

                    asistente = Persona.objects.filter(usuario=diferido.seguimiento.usuario)[:1].get()
                    if EMAIL_ACTIVE:
                        send_html_mail('Notificacion - Convenio de Pago',
                                       'emails/convenio_pago.html',
                                       {
                                           'diferido':diferido,
                                           'rubros':Rubro.objects.filter(id__in=nuevos_rubros),
                                           'gestor':asistente,
                                           'inscripcion':inscripcion
                                       },
                                       # [asistente.emailinst, inscripcion.persona.emailinst, inscripcion.persona.email]
                                       ['lgomez@bolivariano.edu.ec']
                        )

                    return HttpResponse(json.dumps({"result":"ok"}), content_type="application/json")
                except Exception as e:
                    print("ERROR save_convenio_pago: "+str(e))
                    return HttpResponse(json.dumps({"result":"bad", 'mensaje':str(e)}), content_type="application/json")
    else:
        if 'action' in request.GET:
            data = {}
            a = request.GET['action']
            if a == 'convenio_pago':
                inscripcion = Inscripcion.objects.filter(persona__usuario__is_active=True, persona__usuario=request.user)[:1].get()
                diferido = DirferidoRubro.objects.filter(rubroespecie__disponible=True, aprobado=None, fechaaprobacion=None, rubroespecie__rubro__inscripcion=inscripcion).exclude(seguimiento__cerrada=True).exclude(seguimiento__cerrada=True).exclude(rubroespecie__aplicada=True).order_by('-id')[:1].get()
                rubros = Rubro.objects.filter(id__in=diferido.rubrosanteriores.split(','))
                cuotas = []
                fecha = diferido.fechaprimerpago
                for x in range(diferido.num_cuotas):
                    cuota = {
                                'nombreRubro': 'Diferido Convenio Pago #'+str(x+1),
                                'valor':diferido.totaldiferido/diferido.num_cuotas,
                                'fecha':fecha
                            }
                    cuotas.append(cuota)
                    fecha = sumar_mes(fecha)
                data['cuotas'] = cuotas
                return render(request,"notificaciones/convenio_pago.html", data)

def notificaciones(request):
    try:
        request.session['bloquea_notificaciones'] = False
        usuario = request.user
        response = []
        if usuario.groups.filter(id__in=[ALUMNOS_GROUP_ID]).exists():
            notificaciones = Notificacion.objects.filter(estado=True)
            for notificacion in notificaciones:
                if notificacion.grupos:
                    if str(ALUMNOS_GROUP_ID) in notificacion.grupos.split(','):
                        funcion = globals()[notificacion.funcion]
                        result = funcion(request, False, notificacion.id)
                        if result:
                            response.append(result)

        else:
            notificaciones_persona = NotificacionPersona.objects.filter(persona__usuario=usuario, notificacion__estado=True, estado=True)
            for notificacion in notificaciones_persona:
                funcion = globals()[notificacion.notificacion.funcion]
                result = funcion(request, False, notificacion.notificacion.id)
                if result:
                    response.append(result)
        return response
    except Exception as e:
        print("ERROR NOTIFICACIONES: "+str(e))
        return {"error": str(e)}

def convenio_pago(request, utiliza_detalle, notificacion_id):
    try:
        notificacion = Notificacion.objects.get(pk= notificacion_id)
        inscripcion = Inscripcion.objects.filter(persona__usuario__is_active=True, persona__usuario=request.user)[:1].get() #accede
        if DirferidoRubro.objects.filter(rubroespecie__disponible=True, aprobado=None, fechaaprobacion=None, rubroespecie__rubro__inscripcion=inscripcion).exclude(seguimiento__cerrada=True).exclude(seguimiento__cerrada=True).exclude(rubroespecie__aplicada=True).exists():
            diferido = DirferidoRubro.objects.filter(rubroespecie__disponible=True, aprobado=None, fechaaprobacion=None, rubroespecie__rubro__inscripcion=inscripcion).exclude(seguimiento__cerrada=True).exclude(seguimiento__cerrada=True).exclude(rubroespecie__aplicada=True).order_by('-id')[:1].get()

            if utiliza_detalle:
                detalle = []
                data = {}
                data['cabecera_tabla'] = ['Rubros Diferidos', 'Valor', 'Fecha Vencimiento'] #aqui se arma el encabezado de la tabla que aparecera en el detalle de la notificacion.
                for rubro in Rubro.objects.filter(id__in=diferido.rubrosanteriores.split(',')):
                    detalle.append( #Aqui va el detalle, contiene dos diccionarios
                        {
                            'detalle_tabla':[ #diccionario #1: contiene el detalle de la tabla. Debe estar en el orden de la cabecera ingresada en la linea 69.
                                elimina_tildes(rubro.nombre()),
                                "$"+str(rubro.adeudado()),
                                str(rubro.fechavence)
                            ],

                            'otros': { #diccionario #2: informacion variada, no cambiar los indices.
                                'periodo': False,
                                'url': False, #enviar la url de cada detalle si se requere, caso contrario enviar "".
                                'utiliza_url': False #true si desea mostrar un boton para redirigir a al url q envia en la linea anterior, false si no desea que aparezca en la web.
                            }
                        })
                data['detalle'] = detalle
                return data


            return {
                'notificacion_titulo': notificacion.nombre,
                'notificacion_descripcion': "Tiene un convenio de pago por un valor total de $"+str(diferido.totaldiferido)+" diferido a "+str(diferido.num_cuotas)+" cuotas. Los rubros a diferir se listan en el detalle.",
                'urls': [{'url':'/convenio_pago', 'name':'Ver Convenio', 'title':'Convenio de Pago', 'tipo':'info', 'icono':'eye-open'}], #url de modulo.
                'tipo': 'info', #danger, warning, info, success. Esto cambia el color e iconos de las alertas mostradas.
                'utiliza_detalle': True, #true si la notificacion debe desplegar un detalle.
                'id': notificacion.id, #si hay detalle enviar id de lo que se debe filtrar.
                'modal': True
            }
        return None
    except Exception as e:
        print("ERROR convenio_pago: "+str(e))
        return {"error": str(e)}


def aprobar_alcance_notas(request, utiliza_detalle, notificacion_id):
    try:
        notificacion = Notificacion.objects.get(pk= notificacion_id)
        if CoordinadorCarreraPeriodo.objects.filter(persona__usuario=request.user).exists() and request.user.has_perm('sga.change_evaluacionalcance'):
            coordinador_carreras = CoordinadorCarreraPeriodo.objects.filter(persona__usuario=request.user)
            carreras = Carrera.objects.filter(id__in=coordinador_carreras.values('carrera'))
            especies = RubroEspecieValorada.objects.filter(disponible=True, autorizado=True, rubro__cancelado=True).exclude(aplicada=True).exclude(materia=None)
            if EvaluacionAlcance.objects.filter(fecha__gte=datetime.strptime('2024-04-08', "%Y-%m-%d"),
                                                enviado=True,
                                                aprobado=False,
                                                materiaasignada__matricula__inscripcion__carrera__id__in=carreras,
                                                materiaasignada__id__in=especies.values('materia')).exists():
                return {
                    'notificacion_titulo': notificacion.nombre,
                    'notificacion_descripcion': notificacion.descripcion,
                    'urls': [{'url':'/alcance_notas?aprobacion', 'name':'Ir a Modulo', 'title':'', 'tipo':'info'}], #url de modulo.
                    'tipo': 'info', #danger, warning, info, success. Esto cambia el color e iconos de las alertas mostradas.
                    'utiliza_detalle': False, #true si la notificacion debe desplegar un detalle.
                    'id': notificacion.id #si hay detalle enviar id de lo que se debe filtrar.
                }
        return None
    except Exception as e:
        print("ERROR materias_pendientes: "+str(e))
        return {"error": str(e)}

def materias_pendientes(request, utiliza_detalle, notificacion_id):
    try:
        usuario = request.user
        notificacion = Notificacion.objects.get(pk= notificacion_id)
        profesor = Profesor.objects.filter(persona__usuario = usuario)[:1].get()
        # if Materia.objects.filter(profesormateria__profesor=profesor, fin__lt=datetime.now().date(),cerrado = False,profesormateria__segmento__id=TIPOSEGMENTO_TEORIA).exclude(profesormateria__profesor__persona__apellido1__icontains='BUCKINGHAM').exists() or  Materia.objects.filter(profesormateria__profesor_aux=profesor.id, fin__lt=datetime.now().date(),cerrado = False,profesormateria__segmento__id=TIPOSEGMENTO_TEORIA).exclude(profesormateria__profesor__persona__apellido1__icontains='BUCKINGHAM').exists():
        if Materia.objects.filter(profesormateria__aceptacion=True, profesormateria__profesor=profesor, fin__lt=datetime.now().date(), cerrado=False, profesormateria__segmento__id=TIPOSEGMENTO_TEORIA).exists():
            materias = Materia.objects.filter(profesormateria__aceptacion=True, profesormateria__profesor=profesor, fin__lt=datetime.now().date(),cerrado = False,profesormateria__segmento__id=TIPOSEGMENTO_TEORIA).order_by('asignatura__nombre')
            # else:
            #      materias=Materia.objects.filter(profesormateria__profesor_aux=profesor.id, fin__lt=datetime.now().date(),cerrado = False,profesormateria__segmento__id=TIPOSEGMENTO_TEORIA ).order_by('asignatura__nombre')
            if utiliza_detalle:
                detalle = []
                data = {}
                data['cabecera_tabla'] = ['Materia', 'Grupo', 'Inicio', 'Fin', 'Periodo'] #aqui se arma el encabezado de la tabla que aparecera en el detalle de la notificacion.
                for materia in materias:

                    detalle.append( #Aqui va el detalle, contiene dos diccionarios
                        {
                            'detalle_tabla':[ #diccionario #1: contiene el detalle de la tabla. Debe estar en el orden de la cabecera ingresada en la linea 69.
                                elimina_tildes(materia.asignatura.nombre),
                                materia.nivel.paralelo,
                                str(materia.inicio),
                                str(materia.fin),
                                materia.nivel.periodo.nombre
                            ],

                            'otros': { #diccionario #2: informacion variada, no cambiar los indices.
                                'periodo': materia.nivel.periodo.id,
                                'url': '/pro_evaluaciones', #enviar la url de cada detalle si se requere, caso contrario enviar "".
                                'utiliza_url': True #true si desea mostrar un boton para redirigir a al url q envia en la linea anterior, false si no desea que aparezca en la web.
                            }
                        })
                data['detalle'] = detalle
                return data
            return {
                'notificacion_titulo': notificacion.nombre,
                'notificacion_descripcion': notificacion.descripcion,
                'urls': [{'url':'/pro_evaluaciones','name':'Ir a clases', 'title':'Materias Pendientes ', 'tipo':'info'}], #url de modulo.
                'tipo': 'info', #danger, warning, info, success. Esto cambia el color e iconos de las alertas mostradas.
                'utiliza_detalle': True, #true si la notificacion debe desplegar un detalle.
                'id': notificacion.id #si hay detalle enviar id de lo que se debe filtrar.
            }
        return None
    except Exception as e:
        print("ERROR materias_pendientes: "+str(e))
        return {"error": str(e)}
def tutoria_pedagogica(request,utiliza_detalle,notificacion_id):
    # detalle = []
    # data = {}
    usuario = request.user
    notificacion = Notificacion.objects.get(pk=notificacion_id)
    if Profesor.objects.filter(persona__usuario=usuario).exists():
        profesor = Profesor.objects.filter(persona__usuario=usuario)[:1].get()
        # listatutoria = []
        if TutoriaPedagogica.objects.filter(profesor=profesor, aceptada=None).exists():
            # request.session['bloquea_notificaciones'] = True
            return {
                'notificacion_titulo': notificacion.nombre,
                'notificacion_descripcion': notificacion.descripcion,
                'urls': [{'url': '/pedagogica_tutoria', 'name': 'Ir Modulo', 'title': 'Ir Modulo',
                          'tipo': 'success', 'icono': 'arrow-up'}],
                'tipo': 'warning',
                # danger, warning, info, success. Esto cambia el color e iconos de las alertas mostradas.
                'utiliza_detalle': False,  # true si la notificacion debe desplegar un detalle.
                'id': notificacion.id  # si hay detalle enviar id de lo que se debe filtrar.
            }
        return None

def tutoria_pedagogica_programada(request,utiliza_detalle,notificacion_id):
    # detalle = []
    # data = {}
    usuario = request.user
    notificacion = Notificacion.objects.get(pk=notificacion_id)
    if Profesor.objects.filter(persona__usuario=usuario).exists():
        profesor = Profesor.objects.filter(persona__usuario=usuario)[:1].get()
        # listatutoria = []
        if TutoriaPedagogica.objects.filter(profesor=profesor, aceptada=True, finalizado=False).exists():
            tutoria=TutoriaPedagogica.objects.filter(profesor=profesor, aceptada=True, finalizado=False)
            fecha_actual = datetime.now()
            fecha_hace_72_horas = fecha_actual - timedelta(hours=72)
            listadetalle = []
            for t in tutoria:
                if DetalleTutoriaPedagogica.objects.filter(tutoria=t,fecha_tutoria__gte=fecha_hace_72_horas, finalizado=False).exists():
                    detalle=DetalleTutoriaPedagogica.objects.filter(tutoria=t,fecha_tutoria__gte=fecha_hace_72_horas,finalizado=False)
                    for d in detalle:
                        listadetalle.append(d)
                    print(listadetalle)

            # request.session['bloquea_notificaciones'] = True
            return {
                'notificacion_titulo': notificacion.nombre,
                'notificacion_descripcion': notificacion.descripcion ,
                'urls': [{'url': '/pedagogica_tutoria', 'name': 'Ver Informacion', 'title': 'Ver Informacion',
                          'tipo': 'success', 'icono': 'arrow-up'}],
                'tipo': 'warning',
                # danger, warning, info, success. Esto cambia el color e iconos de las alertas mostradas.
                'utiliza_detalle': False,  # true si la notificacion debe desplegar un detalle.
                'id': notificacion.id  # si hay detalle enviar id de lo que se debe filtrar.
            }
        return None
# OBLIGATORIO
def periodos_evaluacion(request, utiliza_detalle, notificacion_id):
    try:
        usuario = request.user
        notificacion = Notificacion.objects.get(pk= notificacion_id)
        evaluaciones=[]
        periodoseval=[]
        evaval=[]
        periodosevallist=[]
        profesor = Profesor.objects.filter(persona__usuario = usuario)[:1].get()
        if PeriodoEvaluacion.objects.filter(evaluaciondoc__estado=True).exists():
            for per in PeriodoEvaluacion.objects.filter(evaluaciondoc__estado=True):
                permaes=[]
                peri=[]
                peri = ProfesorMateria.objects.filter(materia__cerrado=True, profesor=profesor,
                                                       materia__nivel__periodo=per.periodo).distinct('materia__nivel__periodo').values('materia__nivel__periodo')
                # periodoseval = PeriodoEvaluacion.objects.filter(evaluaciondoc__estado=True).values('periodo')
                if PeriodoEvaluacion.objects.filter(Q(evaluaciondoc__estado=True,periodo__id__in=peri)|Q(evaluaciondoc__estado=True,periodo__id__in=permaes)).exists():
                    periodosevallist.append(per.id)
            if len(periodosevallist) >0:
                print((2))
                if EvaluacionDocentePeriodo.objects.filter(profesor=profesor,finalizado=True).exists():
                    evaval=EvaluacionDocentePeriodo.objects.filter(profesor=profesor,finalizado=True).values('evaluaciondocente')
                    periodoseval=EvaluacionDocentePeriodo.objects.filter(profesor=profesor,finalizado=True).values('periodo')
                evaluaciones =PeriodoEvaluacion.objects.filter(evaluaciondoc__docente=True,id__in=periodosevallist).exclude(evaluaciondoc__id__in=evaval,periodo__id__in=periodoseval)

        if evaluaciones:
            if utiliza_detalle:
                detalle = []
                data = {}
                data['cabecera_tabla'] = ['Periodo'] #aqui se arma el encabezado de la tabla que aparecera en el detalle de la notificacion.
                for evaluacion in evaluaciones:

                    detalle.append( #Aqui va el detalle, contiene dos diccionarios
                        {
                            'detalle_tabla':[ #diccionario #1: contiene el detalle de la tabla. Debe estar en el orden de la cabecera ingresada en la linea 69.
                                evaluacion.periodo.nombre
                            ],
                            'otros': { #diccionario #2: informacion variada, no cambiar los indices.
                                'periodo': evaluacion.periodo.id,
                                'url': '/doc_evaluaciondocente?action=evaluar&acc2=1&id='+str(evaluacion.id), #enviar la url de cada detalle si se requere, caso contrario enviar "".
                                'utiliza_url': True #true si desea mostrar un boton para redirigir a al url q envia en la linea anterior, false si no desea que aparezca en la web.
                            }
                        })

                data['detalle'] = detalle
                return data
            request.session['bloquea_notificaciones'] = True
            return {
                'notificacion_titulo': notificacion.nombre,
                'notificacion_descripcion': notificacion.descripcion,
                'urls': [{'url':'/doc_evaluaciondocente', 'name':'Ir a Evaluacion del Docente', 'title':'Modulo de Evaluacion Docente', 'tipo':'info'}], #url de modulo.
                'tipo': 'danger', #danger, warning, info, success. Esto cambia el color e iconos de las alertas mostradas.
                'utiliza_detalle': True, #true si la notificacion debe desplegar un detalle.
                'id': notificacion.id #si hay detalle enviar id de lo que se debe filtrar.
            }
        return None
    except Exception as e:
        print("ERROR periodos_evaluacion: "+str(e))
        return {"error": str(e)}
# OBLIGATORIO
def evaluacion_docente_coordinador(request, utiliza_detalle, notificacion_id):
    usuario = request.user
    notificacion = Notificacion.objects.get(pk= notificacion_id)
    # notificacion_persona =  NotificacionPersona.objects.filter(persona__usuario=usuario, notificacion=notificacion)[:1].get()

    if CoordinadorCarreraPeriodo.objects.filter(persona__usuario=usuario).exists():
        coordinadorid=CoordinadorCarreraPeriodo.objects.filter(persona__usuario=usuario).values('id')
        coord = CoordinadorCarreraPeriodo.objects.filter(persona__usuario=usuario)[:1].get()
        if EvaluacionCoordinadorDocente.objects.filter(coordinador__id__in=coordinadorid).exists():
            if EvaluacionCoordinadorDocente.objects.filter(coordinador__id__in=coordinadorid).exists():
                profesorescoor = EvaluacionCoordinadorDocente.objects.filter(coordinador__id__in=coordinadorid).exclude(profesor__persona=coord.persona).values('profesor')
                periodoscoor = EvaluacionCoordinadorDocente.objects.filter(coordinador__id__in=coordinadorid).values('evaluacion__periodo')
                canteval=EvaluacionDocentePeriodo.objects.filter(evaluaciondocente__docente=True,evaluaciondocente__estado=True, periodo__id__in=periodoscoor,profesor__id__in=profesorescoor)
                print(canteval)
            if EvaluacionDirectivoPeriodo.objects.filter(evaluaciondocenteperiodo__evaluaciondocente__docente=True,evaluaciondocenteperiodo__evaluaciondocente__estado=True,evaluaciondocenteperiodo__id__in=canteval.values('id'),finalizado=True).count() < canteval.count():
                request.session['bloquea_notificaciones'] = True
                return {
                    'notificacion_titulo': notificacion.nombre,
                    'notificacion_descripcion': notificacion.descripcion,
                    'urls': [{'url':'/dire_evaluaciondocente?action=evaluacioncoordinador', 'name':'Evaluacion Docente', 'title':'Modulo Evaluacion Docente', 'tipo':'info'}],
                    'tipo': 'danger', #danger, warning, info, success. Esto cambia el color e iconos de las alertas mostradas.
                    'utiliza_detalle': False, #true si la notificacion debe desplegar un detalle.
                    'id': notificacion.id #si hay detalle enviar id de lo que se debe filtrar.
                }

def pendientes_bandeja_docente(request, utiliza_detalle, notificacion_id):
    try:
        usuario = request.user
        notificacion = Notificacion.objects.get(pk=notificacion_id)

        fecha_limite = datetime.now().date() - timedelta(days=DIAS_ESPECIE)
        gestiones = GestionTramite.objects.filter(tramite__autorizado=True, profesor__usuario=usuario, tramite__rubro__fecha__gte=fecha_limite).exclude(finalizado=True).exclude(tramite__aplicada=True).exclude(tramite__materia=None)
        list_gestiones = []
        for carrera in Carrera.objects.filter(id__in=gestiones.values('tramite__rubro__inscripcion__carrera')):
            fecha_maxima = datetime.now() - timedelta(days=carrera.diasgestion)
            if GestionTramite.objects.filter(fechaasignacion__lt=fecha_maxima, tramite__rubro__inscripcion__carrera=carrera, tramite__autorizado=True, profesor__usuario=usuario).exclude(finalizado=True).exclude(tramite__aplicada=True).exclude(tramite__materia=None).exists():
                print(carrera.diasgestion)
                gestion_tramite = GestionTramite.objects.filter(fechaasignacion__lt=fecha_maxima, tramite__rubro__inscripcion__carrera=carrera, tramite__autorizado=True, profesor__usuario=usuario).exclude(finalizado=True).exclude(tramite__aplicada=True).exclude(tramite__materia=None).order_by('-id')
                for x in gestion_tramite:
                    list_gestiones.append(x.id)

        if list_gestiones:
            gestion_tramite = GestionTramite.objects.filter(id__in=list_gestiones)
            # request.session['bloquea_notificaciones'] = True
            if utiliza_detalle:
                detalle = []
                url = '/pro_especies'
                data = {}
                data['cabecera_tabla'] = ['Alumno', 'Especie', 'Asignacion', 'Materia'] #aqui se arma el encabezado de la tabla que aparecera en el detalle de la notificacion.
                for gestion in gestion_tramite:
                    if gestion.tramite.tipoespecie.id in [ID_TIPO_ESPECIE_REG_NOTA, ESPECIE_ASENTAMIENTOCONVENIO_SINVALOR, ESPECIE_ASENTAMIENTOCONVENIO_CONVALOR]:
                        if gestion.tramite.materia.materia.nivel.cerrado:
                            url = '/alcance_notas?nivel-cerrado=1&id='+str(gestion.tramite.materia.materia.id)
                        else:
                            url = '/alcance_notas?id='+str(gestion.tramite.materia.materia.id)

                    detalle.append( #Aqui va el detalle, contiene dos diccionarios
                        {
                            'detalle_tabla':[ #diccionario #1: contiene el detalle de la tabla. Debe estar en el orden de la cabecera ingresada en la linea 69.
                                elimina_tildes(gestion.tramite.rubro.inscripcion.persona.nombre_completo_inverso()),
                                elimina_tildes(gestion.tramite.tipoespecie.nombre)+'<br><span class="label label-info">'+str(gestion.tramite.serie)+'</span>',
                                str(gestion.fechaasignacion.strftime('%d-%m-%Y')),
                                elimina_tildes(gestion.tramite.materia.materia.asignatura.nombre)
                            ],
                            'otros': { #diccionario #2: informacion variada, no cambiar los indices.
                                'periodo': gestion.tramite.materia.materia.nivel.periodo.id if gestion.tramite.materia else False, #Enviar id de periodo si la url necesita realizar un cambio en el periodo de la sesion.
                                'url': url, #enviar la url de cada detalle si se requere, caso contrario enviar "".
                                'utiliza_url': True #true si desea mostrar un boton para redirigir a al url q envia en la linea anterior, false si no desea que aparezca en la web.
                            }
                        })
                data['detalle'] = detalle
                return data

            return {
                'notificacion_titulo': notificacion.nombre,
                'notificacion_descripcion': notificacion.descripcion,
                'urls': [{'url':'/pro_especies', 'name':'Ir a bandeja', 'title':'Modulo Bandeja de Atencion', 'tipo':'danger', 'icono':'share'}], #url de modulo.
                'tipo': 'info', #danger, warning, info, success. Esto cambia el color e iconos de las alertas mostradas.
                'utiliza_detalle': True, #true si la notificacion debe desplegar un detalle.
                'id': notificacion.id #si hay detalle enviar id de lo que se debe filtrar.
            }
        return None

    except Exception as e:
        print("ERROR pendientes_bandeja_docente: "+str(e))
        return {"error": str(e)}




def actualiza_notificaciones_personal(request):
    try:
        if GestionTramite.objects.filter(fechaasignacion__lte=F('fechaasignacion')+timedelta(days=F('tramite__rubro__inscripcion__carrera__diasgestion')), profesor__usuario__is_active=True).exclude(finalizado=True).exists():
            gestiones =  GestionTramite.objects.filter(fechaasignacion__lte=F('fechaasignacion')+timedelta(days=F('tramite__rubro__inscripcion__carrera__diasgestion')), profesor__usuario__is_active=True).exclude(finalizado=True).order_by('profesor__id')
            print(gestiones.count())
            for x in gestiones:
                print(x.profesor)
        # print("POSI")
        # # grupos = Group.objects.filter(id__in=[PROFESORES_GROUP_ID])
        #
        # personal = Persona.objects.filter(usuario__is_active=True, usuario__groups__id=PROFESORES_GROUP_ID)
        # print(personal.count())
        # notificacion = Notificacion.objects.get(pk=1)
        # for p in personal:
        #     print(p)
        #     notificacion_persona = NotificacionPersona(notificacion=notificacion,
        #                                        persona=p)
        #     notificacion_persona.save()
    except Exception as e:
        print("ERROR actualiza_notificaciones_personal: "+str(e))


# NOTIFICACIONES PARA ESTUDIANTES - DEUDA - OBLIGATORIO
def estudiante_tiene_deuda(request, utiliza_detalle, notificacion_id):
    try:
        usuario = request.user

        notificacion = Notificacion.objects.get(pk= notificacion_id)
        if Inscripcion.objects.filter(persona__usuario__is_active=True, persona__usuario=usuario).exists():
            inscripcion = Inscripcion.objects.filter(persona__usuario__is_active=True, persona__usuario=usuario)[:1].get() #accede
            hoy = datetime.now().date()
            if Rubro.objects.filter(inscripcion=inscripcion, cancelado=False, valor__gt=0, fechavence__lt=hoy).exclude(rubrootro__tipo__id__in=[TIPO_CURSOS_RUBRO, TIPO_CONGRESO_RUBRO, TIPO_RUBRO_CREDENCIAL,TIPO_RUBRO_MATERIALAPOYO]).exclude(rubrootro__descripcion__icontains='TALLER').exists():
                rb_seguimiento = Rubro.objects.filter(inscripcion=inscripcion, cancelado=False, valor__gt=0,fechavence__lt=hoy).exclude(rubrootro__tipo__id__in=[TIPO_CURSOS_RUBRO, TIPO_CONGRESO_RUBRO, TIPO_RUBRO_CREDENCIAL,TIPO_RUBRO_MATERIALAPOYO]).exclude(rubrootro__descripcion__icontains='TALLER')
                print(rb_seguimiento)

                if utiliza_detalle:
                    detalle = []
                    data = {}
                    data['cabecera_tabla'] = ['Rubros Vencido','Fecha Vencido','Valor Deuda'] #aqui se arma el encabezado de la tabla que aparecera en el detalle de la notificacion.
                    for rubros in rb_seguimiento:

                        detalle.append( #Aqui va el detalle, contiene dos diccionarios
                            {
                                'detalle_tabla':[ #diccionario #1: contiene el detalle de la tabla. Debe estar en el orden de la cabecera ingresada en la linea 69.
                                    rubros.nombre(),
                                    str(rubros.fechavence),
                                    '$'+str(rubros.adeudado())
                                ],
                                'otros': { #diccionario #2: informacion variada, no cambiar los indices.
                                    'periodo': False,
                                    'url': '/online', #enviar la url de cada detalle si se requere, caso contrario enviar "".
                                    'utiliza_url': True #true si desea mostrar un boton para redirigir a al url q envia en la linea anterior, false si no desea que aparezca en la web.
                                }
                            })

                    data['detalle'] = detalle
                    return data
                request.session['bloquea_notificaciones'] = True
                return {
                    'notificacion_titulo': notificacion.nombre,
                    'notificacion_descripcion': notificacion.descripcion+' Si desea realizar PAGOS CON TARJETA dar clik en el boton PAGAR EN LINEA. '
                    'Si Necesita soporte del departamento de Tics dar clik en el boton MESA DE AYUDA.',
                    'urls': [{'url':'/online', 'name':'Pago en Linea', 'title':'Modulo de Pago en Linea', 'tipo':'danger', 'icono':'money'},
                             {'url':'/requersoporte', 'name':'Mesa de Ayuda', 'title':'Modulo Mesa Ayuda', 'tipo':'primary', 'icono':'eye-open'},
                             {'url':'/pagowester', 'name':'Registrar Pagos Wester', 'title':'Modulo Registrar Pagos Wester', 'tipo':'success', 'icono':'money'},
                             {'url':'/alu_medical', 'name':'Ficha Medica', 'title':'Modulo Ficha Medica', 'tipo':'info', 'icono':'eye-open'},
                             {'url':'/solicitudonline', 'name':'Bandeja de Atencion ', 'title':'Modulo Bandeja de Atencion', 'tipo':'primary','icono':'file'},
                             {'url':'/alu_referidos', 'name':'Ingresar Referido', 'title':'Modulo de Referido', 'tipo':'success','icono':'eye-open'},
                             {'url':'/alu_finanzas', 'name':'Ver Finanzas', 'title':'Modulo de Finanzas', 'tipo':'info', 'icono':'eye-open'},
                             # {'url':'/alu_cronograma', 'name':'Ver Cronograma', 'title':'Modulo de Cronograma', 'tipo':'warning', 'icono':'eye-open'},
                    ], #url de modulo.
                    'tipo': 'danger', #danger, warning, info, success. Esto cambia el color e iconos de las alertas mostradas.
                    'utiliza_detalle': True, #true si la notificacion debe desplegar un detalle.
                    'id': notificacion.id #si hay detalle enviar id de lo que se debe filtrar.
                }
            return None
    except Exception as e:
        print("ERROR estudiante_tiene_deuda: "+str(e))
        return {"error": str(e)}

# NOTIFICACIONES PARA DOCENTES -NO OBLIGATORIO
def actas_sin_entregar(request, utiliza_detalle, notificacion_id):
    try:
        usuario = request.user
        notificacion = Notificacion.objects.get(pk= notificacion_id)
        # notificacion_persona =  NotificacionPersona.objects.filter(persona__usuario=usuario, notificacion=notificacion)[:1].get()
        profesor = Profesor.objects.filter(persona__usuario = usuario)[:1].get()
        fecha = datetime.now().date() + timedelta(days=-3)
        profesor=ProfesorMateria.objects.filter(profesor=profesor,profesor_aux=None,materia__cerrado=True,segmento__id=TIPOSEGMENTO_TEORIA,materia__fechacierre__gte='2019-05-01',materia__fechacierre__lte=fecha).exclude(profesor__persona__nombres__icontains='DEFINIR').exclude(profesor__persona__apellido1__icontains='BUCKINGHAM').exclude(aceptacion=False).order_by('materia__asignatura__nombre')
        materias=[]
        for prof in profesor:
            #en la UASS el responsable del acta es el docente del segmento teoria
            carrera=  prof.materia.nivel.carrera
            if Coordinacion.objects.filter(carrera=carrera).exists():
                if prof.materia.nivel.coordinacion().id==COORDINACION_UASSS:
                    for  materia in Materia.objects.filter(pk=prof.materia.id,cerrado=True).exclude(asignatura__id__in=[ASIG_VINCULACION,817]):
                        for mate in MateriaRecepcionActaNotas.objects.filter(materia=materia,entregada=False,materia__cerrado=True,materia__fechacierre__gte='2019-05-01',materia__fechacierre__lte=fecha).exclude(materia__asignatura__id=ASIG_VINCULACION).order_by('materia__asignatura__nombre'):
                            materias.append(mate)
                            # materias = MateriaRecepcionActaNotas.objects.filter(materia=materia,entregada=False,materia__cerrado=True)
                else:
                    for  materia in Materia.objects.filter(pk=prof.materia.id,fin=prof.hasta,cerrado=True).exclude(asignatura__id__in=[ASIG_VINCULACION,817]):
                        for mate in MateriaRecepcionActaNotas.objects.filter(materia=materia,entregada=False,materia__cerrado=True):
                            materias.append(mate)
                            # materias = MateriaRecepcionActaNotas.objects.filter(materia=materia,entregada=False,materia__cerrado=True)
        if materias:
            if utiliza_detalle:
                detalle = []
                data = {}
                data['cabecera_tabla'] = ['Materia', 'Nivel', 'Grupo', 'F. Cierre', 'Carrera'] #aqui se arma el encabezado de la tabla que aparecera en el detalle de la notificacion.
                for mat in materias:
                    detalle.append( #Aqui va el detalle, contiene dos diccionarios
                        {
                            'detalle_tabla':[ #diccionario #1: contiene el detalle de la tabla. Debe estar en el orden de la cabecera ingresada en la linea 69.
                                mat.materia.asignatura.nombre,
                                mat.materia.nivel.nivelmalla.nombre,
                                mat.materia.nivel.paralelo,
                                str((mat.materia.fechacierre).date()),
                                mat.materia.nivel.carrera.nombre
                            ],
                            'otros': { #diccionario #2: informacion variada, no cambiar los indices.
                                'periodo':mat.materia.nivel.periodo.id,
                                'url': '/pro_entrega_acta', #enviar la url de cada detalle si se requere, caso contrario enviar "".
                                'utiliza_url': True #true si desea mostrar un boton para redirigir a al url q envia en la linea anterior, false si no desea que aparezca en la web.
                            }
                        })
                data['detalle'] = detalle
                return data
            return {
                'notificacion_titulo': notificacion.nombre,
                'notificacion_descripcion': notificacion.descripcion,
                'urls': [{'url':'/pro_entrega_acta', 'name':'Ir a Entrega de Actas', 'title':'Modulo de Entrega de Actas de Notas', 'tipo':'info'}], #url de modulo.
                'tipo': 'info', #danger, warning, info, success. Esto cambia el color e iconos de las alertas mostradas.
                'utiliza_detalle': True, #true si la notificacion debe desplegar un detalle.
                'id': notificacion.id #si hay detalle enviar id de lo que se debe filtrar.
            }
        return None

    except Exception as e:
        print("ERROR actas_sin_entregar: "+str(e))
        return {"error": str(e)}
# NO OBLIGATORIO
def clases_abiertas(request, utiliza_detalle, notificacion_id):
    try:
        usuario = request.user
        notificacion = Notificacion.objects.get(pk= notificacion_id)
        profesor = Profesor.objects.filter(persona__usuario = usuario)[:1].get()
        if LeccionGrupo.objects.filter(profesor=profesor,abierta=True, fecha__lt=datetime.now()).exists():
            lecciones=  LeccionGrupo.objects.filter(profesor=profesor, abierta=True,fecha__lt=datetime.now()).order_by('-fecha')
            if utiliza_detalle:
                detalle = []
                data = {}
                data['cabecera_tabla'] = ['Materia', 'Grupo','Dia','Periodo','Entrada'] #aqui se arma el encabezado de la tabla que aparecera en el detalle de la notificacion.
                for lec in lecciones:
                    detalle.append( #Aqui va el detalle, contiene dos diccionarios
                        {
                            'detalle_tabla':[ #diccionario #1: contiene el detalle de la tabla. Debe estar en el orden de la cabecera ingresada en la linea 69.
                                lec.materia.asignatura.nombre,
                                lec.materia.nivel.paralelo,
                                str(lec.fecha),
                                lec.materia.nivel.periodo.nombre,
                                str(lec.horaentrada.strftime("%H:%M"))
                            ],
                            'otros': { #diccionario #2: informacion variada, no cambiar los indices.
                                'periodo':lec.materia.nivel.periodo.id,
                                'url': '/pro_clases', #enviar la url de cada detalle si se requere, caso contrario enviar "".
                                'utiliza_url': True #true si desea mostrar un boton para redirigir a al url q envia en la linea anterior, false si no desea que aparezca en la web.
                            }
                        })
                data['detalle'] = detalle
                return data
            # request.session['bloquea_notificaciones'] = True
            return {
                'notificacion_titulo': notificacion.nombre,
                'notificacion_descripcion': notificacion.descripcion,
                'urls': [{'url':'/pro_clases', 'name':'Ir a Clases Abiertas', 'title':'Modulo de Clases', 'tipo':'success'}], #url de modulo.
                'tipo': 'info', #danger, warning, info, success. Esto cambia el color e iconos de las alertas mostradas.
                'utiliza_detalle': True, #true si la notificacion debe desplegar un detalle.
                'id': notificacion.id #si hay detalle enviar id de lo que se debe filtrar.
            }
        return None
    except Exception as e:
        print("ERROR clases_abiertas: "+str(e))
        return {"error": str(e)}
#ACEPTA PROTECCION DE DATOS - OBLIGATORIO
def acepta_protecciondedatos(request,utiliza_detalle, notificacion_id):
    try:
        usuario = request.user
        notificacion = Notificacion.objects.get(pk= notificacion_id)
        if Persona.objects.filter(usuario = usuario).exclude(aceptaprotecciondatos=True).exists():
            request.session['bloquea_notificaciones'] = True
            if utiliza_detalle:
                detalle = []
                data = {}
                data['cabecera_tabla'] = ['<img src="/static/images/itb_logo.png">Protecci&oacuten de Datos']
                data['utiliza_url'] = False

                detalle.append(
                    {
                        'detalle_tabla':[
                            '<p style="text-align:justify">'
                            'En cumplimiento con <b>La Ley Org&aacute;nica de Protecci&oacute;n de Datos Personales del Ecuador, </b>se le informa que los datos personales '
                            'proporcionados a trav&eacute;s de este sitio web ser&aacute;n tratados de forma confidencial y pasar&aacute;n a formar parte de un registro de datos de <b>ITB</b>. '
                            'La finalidad del tratamiento de los datos es la gesti&oacute;n y env&iacute;o de informaci&oacute;n sobre los programas acad&eacute;micos que ofrece el <b>ITB</b>, as&iacute; como el env&iacute;o de informaci&oacute;n sobre eventos,'
                            'actividades y noticias relacionadas con el <b>ITB</b>, siempre y cuando nos haya autorizado expresamente para ello. '
                            'La informaci&oacute;n que proporcione ser&aacute; utilizada &uacute;nicamente para los fines mencionados anteriormente y no ser&aacute; cedida a terceros sin su consentimiento previo y expreso, salvo obligaci&oacute;n legal. '
                            'Al proporcionarnos sus datos, usted declara que ha le&iacute;do y comprendido la presente cl&aacute;usula y acepta expresamente el tratamiento de sus datos personales en los t&eacute;rminos descritos.'
                            '<b> Para conocer m&aacute;s sobre las pol&iacute;ticas de privacidad y la forma de como ejercer sus derechos, haga click en el siguiente enlace:</b></p>'
                            '<a href="https://www.itb.edu.ec/Politicas" target="_blank"> https://www.itb.edu.ec/Politicas </a>',
                        ],
                        'otros': {
                            'periodo': False, #Enviar id de periodo si la url necesita realizar un cambio en el periodo de la sesion.
                            'url': "", #enviar la url de cada detalle si se requere, caso contrario enviar "".
                            'utiliza_url': False #true si desea mostrar un boton para redirigir a al url q envia en la linea anterior, false si no desea que aparezca en la web.
                        }
                    })

                data['detalle'] = detalle
                return data
            return {
                'notificacion_titulo': notificacion.nombre,
                'notificacion_descripcion': notificacion.descripcion,
                'urls': [{'url':'/account?action=proteccion&id=', 'name':'Aceptar Uso de Datos', 'title':'Aceptar ', 'tipo':'success', 'icono':'check'}],
                'tipo': 'warning', #danger, warning, info, success. Esto cambia el color e iconos de las alertas mostradas.
                'utiliza_detalle': True, #true si la notificacion debe desplegar un detalle.
                'id': notificacion.id #si hay detalle enviar id de lo que se debe filtrar.
            }
    except Exception as e:
        print("ERROR acepta_protecciondedatos: "+str(e))
        return {"error": str(e)}
#LLENAR DATOS - OBLIGATORIO
def llenar_datos_estudiantes(request, utiliza_detalle, notificacion_id):
    try:
        usuario = request.user
        notificacion = Notificacion.objects.get(pk= notificacion_id)
        if Inscripcion.objects.filter(persona__usuario=usuario).exists():
            inscripcion = Inscripcion.objects.filter(persona__usuario=usuario)[:1].get()
            if not inscripcion.persona.telefono or  not inscripcion.persona.email or not  inscripcion.persona.provinciaresid or \
                    not  inscripcion.persona.cantonresid  or not  inscripcion.persona.parroquia or\
                    not  inscripcion.persona.sectorresid or not inscripcion.anuncio or not inscripcion.raza():
                request.session['bloquea_notificaciones'] = True
                return {
                    'notificacion_titulo': notificacion.nombre,
                    'notificacion_descripcion': notificacion.descripcion,
                    'urls': [{'url':'/account', 'name':'Completar Informacion', 'title':'Complete la informacion', 'tipo':'success', 'icono':'arrow-up'}],
                    'tipo': 'warning', #danger, warning, info, success. Esto cambia el color e iconos de las alertas mostradas.
                    'utiliza_detalle': False, #true si la notificacion debe desplegar un detalle.
                    'id': notificacion.id #si hay detalle enviar id de lo que se debe filtrar.
                }
            return None
    except Exception as e:
        print("ERROR llenar_datos_estudiantes: "+str(e))
        return {"error": str(e)}
#DATOS SOCIOECONOMICOS INCOMPLETOS - OBLIGATORIO
def datos_socioeconomicosincompl(request,utiliza_detalle, notificacion_id):
    try:
        usuario = request.user
        notificacion = Notificacion.objects.get(pk= notificacion_id)
        if UTILIZA_FICHA_SOCIOECONOMICA:
            inscripcion= Inscripcion.objects.filter(persona__usuario__is_active=True, persona__usuario=usuario)[:1].get()
            if not 'CONGRESO' in inscripcion.carrera.nombre:
                if inscripcion.datos_socioeconomicos_incompletos():
                    if utiliza_detalle:
                        detalle = []
                        data = {}
                        data['utiliza_url'] = False
                        data['cabecera_tabla'] = ['<span class="label label-important" style="text-align: center">ENCUESTA INCOMPLETA</span>']

                        detalle.append(
                            {
                                'detalle_tabla':[
                                    '<p style="text-align:justify">Esta Encuesta tiene como objetivo principal conocer la realidad del estudiantado del Instituto Superior Tecnologico Bolivariano de Tecnologia.'
                                    ' Para ello estimado estudiante, por favor ingrese al m&oacutedulo de <b style="color:red">FICHA SOCIOECONOMICA</b> y proceda a llenar todas las casillas de la encuesta.<br>'
                                    ' El estudiante, bajo su responsabilidad, declarar&aacute; que la informaci&oacute;n a proporcionar corresponde absolutamente con la realidad.</p>'
                                ],
                                'otros': {
                                    'periodo': False, #Enviar id de periodo si la url necesita realizar un cambio en el periodo de la sesion.
                                    'url': "/alu_socioecon", #enviar la url de cada detalle si se requere, caso contrario enviar "".
                                    'utiliza_url': False #true si desea mostrar un boton para redirigir a al url q envia en la linea anterior, false si no desea que aparezca en la web.
                                }
                            })
                        data['detalle'] = detalle
                        return data
                    request.session['bloquea_notificaciones'] = True
                    return {
                        'notificacion_titulo': notificacion.nombre,
                        'notificacion_descripcion': notificacion.descripcion,
                        'urls': [{'url':'/alu_socioecon', 'name':'Ir a Ficha', 'title':'Ir a Ficha Socioeconomica', 'tipo':'success', 'icono':'arrow-up'}
                        ],
                        'tipo': 'warning', #danger, warning, info, success. Esto cambia el color e iconos de las alertas mostradas.
                        'utiliza_detalle': True, #true si la notificacion debe desplegar un detalle.
                        'id': notificacion.id #si hay detalle enviar id de lo que se debe filtrar.
                    }
                return None
    except Exception as e:
        print("ERROR datos_socioeconomicosincompl: "+str(e))
        return {"error": str(e)}
#EVALUACIONES PENDIENTES A DOCENTES REALIZADA POR ALUMNOS -OBLIGATORIO
def alum_evaluaciondocente(request, utiliza_detalle, notificacion_id):
    try:
        usuario = request.user
        notificacion = Notificacion.objects.get(pk= notificacion_id)
        inscripcion = Inscripcion.objects.filter(persona__usuario=usuario)[:1].get()
        materiaeval = EvaluacionMateria.objects.filter(evaluaciondocente__estado=True).values('materia')
        ids = []
        hoy = datetime.now().date()
        for m in MateriaAsignada.objects.filter(matricula__inscripcion=inscripcion, materia__in=materiaeval):
            # fmateria_mas30 = m.materia.fechacierre + timedelta(30)
            if ((m.matricula.liberada and m.evaluacion_itb().examen > 0 or m.evaluacion_itb().recuperacion > 0) or (not m.matricula.liberada)):
            # not m.matricula.liberada) and fmateria_mas30 >= hoy):
                ids.append(m.id)

        materiasasgi = MateriaAsignada.objects.filter(id__in=ids).values('materia')
        evaluacion = EvaluacionAlumno.objects.filter(inscripcion=inscripcion, finalizado=True).values('profesormateria')
        profesores = ProfesorMateria.objects.filter(materia__in=materiasasgi).exclude(id__in=evaluacion).order_by('profesor__persona__apellido1', 'profesor__persona__apellido2',
                                    'profesor__persona__nombres')
        if profesores:
            if utiliza_detalle:
                detalle = []
                data = {}
                data['cabecera_tabla'] = ['Materia', 'Profesor']
                for p in profesores:
                    detalle.append(
                        {
                            'detalle_tabla':[ #diccionario #1: contiene el detalle de la tabla. Debe estar en el orden de la cabecera ingresada en la linea 69.
                                p.materia.asignatura.nombre,
                                p.profesor.persona.nombre_completo_inverso()
                            ],
                            'otros': { #diccionario #2: informacion variada, no cambiar los indices.
                                'periodo': p.materia.nivel.periodo.id, #Enviar id de periodo si la url necesita realizar un cambio en el periodo de la sesion.
                                'url': '/alu_evaluaciondocente?action=evaluar&id='+str(p.id), #enviar la url de cada detalle si se requere, caso contrario enviar "".
                                'utiliza_url': True #true si desea mostrar un boton para redirigir a al url q envia en la linea anterior, false si no desea que aparezca en la web.
                            }
                        })
                data['detalle'] = detalle
                return data
            request.session['bloquea_notificaciones'] = True
            return {
                'notificacion_titulo': notificacion.nombre,
                'notificacion_descripcion': notificacion.descripcion,
                'urls': [{'url':'/alu_evaluaciondocente', 'name':'Ir a Evaluaciones Docentes', 'title':'Modulo Evaluacion Docente', 'tipo':'danger','icono':'arrow-up'}], #url de modulo.
                'tipo': 'danger', #danger, warning, info, success. Esto cambia el color e iconos de las alertas mostradas.
                'utiliza_detalle': True, #true si la notificacion debe desplegar un detalle.
                'id': notificacion.id #si hay detalle enviar id de lo que se debe filtrar.
            }
        return None
    except Exception as e:
        print("ERROR alum_evaluaciondocente: "+str(e))
        return {"error": str(e)}
#DATOS MEDICOS - OBLIGATORIO
def datos_medicos(request,utiliza_detalle, notificacion_id):
    try:
        usuario = request.user
        notificacion = Notificacion.objects.get(pk= notificacion_id)
        persona = Persona.objects.filter(usuario= usuario)[:1].get()
        if not 'CONGRESO' in persona.inscripcion().carrera.nombre:
            if persona.datos_medicos_incompletos():
                request.session['bloquea_notificaciones'] = True
                return {
                    'notificacion_titulo': notificacion.nombre,
                    'notificacion_descripcion': notificacion.descripcion +' Datos por completar:'+ str(persona.datos_medicos_incompletos()),
                    'urls': [{'url':'/alu_medical', 'name':'Ir a la Ficha Medica', 'title':'Ficha Medica', 'tipo':'success','icono':'share-alt'}],
                    'tipo': 'warning', #danger, warning, info, success. Esto cambia el color e iconos de las alertas mostradas.
                    'utiliza_detalle': False,
                    'id': notificacion.id
                }
            return None
    except Exception as e:
        print("ERROR datos_medicos: "+str(e))
        return {"error": str(e)}
#ACEPTA TERMINOS-CONDICIONES Y CONSTANCIA - OBLIGATORIO
def acepta_termino_constancia(request, utiliza_detalle, notificacion_id):
    try:
        usuario = request.user
        notificacion = Notificacion.objects.get(pk= notificacion_id)
        fechainicitermino='2020-05-03'
        fechainiciaconstancia='2021-08-10'
        inscripcion= Inscripcion.objects.filter(persona__usuario__is_active=True, persona__usuario= usuario)[:1].get()
        fechacorin=str(inscripcion.fecha)
        if fechacorin > str(fechainicitermino) or fechacorin> str(fechainiciaconstancia):
            if not inscripcion.aceptatermino or not inscripcion.aceptaconstancia:
                if utiliza_detalle:
                    detalle = []
                    data = {}
                    data['cabecera_tabla'] = ['Estimado Estudiante, Acepte los t&eacuterminos y condiciones']
                    data['utiliza_url'] = False
                    if not inscripcion.aceptatermino:
                        detalle.append(
                            {
                                'detalle_tabla':[
                                    '<p style="text-align:justify">En calidad de estudiante del ITB declaro que conozco y acepto lo establecido en el REGLAMENTO DE MATR&Iacute;CULAS, ARANCELES Y ARANCELES DIFERENCIADOS PARA LOS ESTUDIANTES DEL INSTITUTO SUPERIOR TECNOL&Oacute;GICO BOLIVARIANO DE TECNOLOG&Iacute;A as&iacute; como los dem&aacute;s instrumentos legales del ITB constan en </p>'
                                    '<a href="https://www.itb.edu.ec/public/docs/reglamento_interno_de_aranceles_ITB_0803.pdf" target="_blank"> https://www.itb.edu.ec/public/docs/reglamento_interno_de_aranceles_ITB_0803.pdf</a><br>'
                                    '<a href="/account?action=termino&id='+str(inscripcion.id)+'" class="btn btn-success" ><i class="icon-money"></i> Aceptar Terminos </a>'
                                ],
                                'otros': {
                                    'periodo': False, #Enviar id de periodo si la url necesita realizar un cambio en el periodo de la sesion.
                                    'url': "", #enviar la url de cada detalle si se requere, caso contrario enviar "".
                                    'utiliza_url': False #true si desea mostrar un boton para redirigir a al url q envia en la linea anterior, false si no desea que aparezca en la web.
                                }
                            })
                    if not inscripcion.aceptaconstancia:
                        detalle.append(
                            {
                                'detalle_tabla':[
                                    '<p style="text-align:justify">En calidad de estudiante del ITB declaro que he leido y acepto las disposiciones generales indicadas en el siguiente link</p>'
                                    '<a href="https://www.itb.edu.ec/public/docs/constancia_presencial.pdf" target="_blank"> https://www.itb.edu.ec/public/docs/constancia_presencial.pdf</a> <br>'
                                     '<a href="/account?action=constancia&id='+str(inscripcion.id)+'" class="btn btn-success" ><i class="icon-money"></i> Aceptar Constancia </a>'
                                ],
                                'otros': {
                                    'periodo': False, #Enviar id de periodo si la url necesita realizar un cambio en el periodo de la sesion.
                                    'url': "", #enviar la url de cada detalle si se requere, caso contrario enviar "".
                                    'utiliza_url': False #true si desea mostrar un boton para redirigir a al url q envia en la linea anterior, false si no desea que aparezca en la web.
                                }
                            })

                    data['detalle'] = detalle
                    return data
                request.session['bloquea_notificaciones'] = True
                return {
                    'notificacion_titulo': notificacion.nombre,
                    'notificacion_descripcion': notificacion.descripcion,
                    # 'urls': [{'url':'/account?action=termino&id='+str(inscripcion.id), 'name':'Aceptar Terminos', 'title':'Aceptar Terminos', 'tipo':'success', 'icono':'money'} if not inscripcion.aceptatermino else False,
                    #          {'url':'/account?action=constancia&id='+str(inscripcion.id), 'name':'Aceptar Constancia', 'title':'Aceptar Constancia', 'tipo':'success', 'icono':'money'} if not inscripcion.aceptaconstancia else False],
                    'tipo': 'warning', #danger, warning, info, success. Esto cambia el color e iconos de las alertas mostradas.
                    'utiliza_detalle': True, #true si la notificacion debe desplegar un detalle.
                    'id': notificacion.id #si hay detalle enviar id de lo que se debe filtrar.
                }
            return None
    except Exception as e:
        print("ERROR acepta_termino_constancia: "+str(e))
        return {"error": str(e)}
#NO OBLIGATORIO
def referidos_estudiantes(request, utiliza_detalle, notificacion_id):
    try:
        usuario = request.user
        notificacion = Notificacion.objects.get(pk= notificacion_id)
        persona = Persona.objects.filter(usuario=usuario)[:1].get()
        inscrito=False
        matricula=False
        if Inscripcion.objects.filter(persona__usuario= usuario).exists():
            inscripcion = Inscripcion.objects.filter(persona__usuario = usuario)[:1].get()
            referidos = ReferidosInscripcion.objects.filter(activo=True,inscripcion=inscripcion,pagocomision=False,aprobado_pago=True)
            valor_referido = ReferidosInscripcion.objects.filter(activo=True,inscripcion=inscripcion,pagocomision=False,aprobado_pago=True).count() * VALOR_COMISION_REFERIDO

        else:
            referidos = ReferidosInscripcion.objects.filter(activo=True,administrativo=persona,pagocomision=False,aprobado_pago=True)

        if referidos:
            for r in referidos:
                if r.online:
                    inscrito=r.verificar_inscrip_online()
                    matricula= r.verificar_pago_online()
                    if inscrito and matricula:
                        break
                else:
                    inscrito=r.inscrito
                    matricula=r.verificar_pago_matricula()
                    if inscrito and matricula:
                        break
            if inscrito and matricula:
                return {
                        'notificacion_titulo': notificacion.nombre,
                        'notificacion_descripcion': notificacion.descripcion + ' El valor es de $'+ str(valor_referido),
                        'urls': [{'url':'/alu_referidos', 'name':'Ir a Referidos', 'title':'Referidos', 'tipo':'success', 'icono':'check'}],
                        'tipo': 'info', #danger, warning, info, success. Esto cambia el color e iconos de las alertas mostradas.
                        'utiliza_detalle': False, #true si la notificacion debe desplegar un detalle.
                        'id': notificacion.id #si hay detalle enviar id de lo que se debe filtrar.
                    }
            return None
    except Exception as e:
        print("ERROR referidos_estudiantes: "+str(e))
        return {"error": str(e)}
# NO OBLIGATORIO
def nueva_informacion(request, utiliza_detalle, notificacion_id):
    try:
        usuario = request.user
        notificacion = Notificacion.objects.get(pk= notificacion_id)
        inscripcion = Inscripcion.objects.filter(persona__usuario__is_active=True, persona__usuario = usuario)[:1].get()
        if not inscripcion.tiene_deuda():
            return {
                'notificacion_titulo': notificacion.nombre,
                'notificacion_descripcion': notificacion.descripcion,
                'urls': [{'url':'/solicitudonline', 'name':'Ir a Bandeja de Atencion', 'tipo':'info', 'icono':'share-alt'}],
                'tipo': 'info', #danger, warning, info, success. Esto cambia el color e iconos de las alertas mostradas.
                'utiliza_detalle': False, #true si la notificacion debe desplegar un detalle.
                'id': notificacion.id #si hay detalle enviar id de lo que se debe filtrar.
            }
        return None
    except Exception as e:
        print("ERROR nueva_informacion: "+str(e))
        return {"error": str(e)}
# OBLIGATORIO
def suspension(request, utiliza_detalle, notificacion_id):
    try:
        usuario = request.user
        notificacion = Notificacion.objects.get(pk= notificacion_id)
        if Inscripcion.objects.filter(persona__usuario__is_active=True, persona__usuario = usuario).exists():
            inscripcion = Inscripcion.objects.filter(persona__usuario__is_active=True, persona__usuario = usuario)[:1].get()
            if inscripcion.suspension:
                request.session['bloquea_notificaciones'] = True
                return {
                    'notificacion_titulo': notificacion.nombre,
                    'notificacion_descripcion': notificacion.descripcion,
                    'urls': [{'url':'/solicitudonline', 'name':'Ir a Bandeja de Atencion', 'tipo':'danger', 'icono':'share-alt'}],
                    'tipo': 'danger', #danger, warning, info, success. Esto cambia el color e iconos de las alertas mostradas.
                    'utiliza_detalle': False, #true si la notificacion debe desplegar un detalle.
                    'id': notificacion.id #si hay detalle enviar id de lo que se debe filtrar.
                }
            return None
    except Exception as e:
        print("ERROR nueva_informacion: "+str(e))
        return {"error": str(e)}

#INFORMATIVO
def gestor_cobro(request, utiliza_detalle, notificacion_id):
    try:
        usuario = request.user
        notificacion = Notificacion.objects.get(pk= notificacion_id)
        inscripcion = Inscripcion.objects.filter(persona__usuario__is_active=True, persona__usuario = usuario)[:1].get()
        hoy = datetime.now().date()
        if RubroSeguimiento.objects.filter(rubro__inscripcion=inscripcion,rubro__cancelado=False,fechaposiblepago=hoy,fechapago=None, estado=True).exists():
            rb_seguimiento =  RubroSeguimiento.objects.filter(rubro__inscripcion=inscripcion,rubro__cancelado=False,fechaposiblepago=hoy,fechapago=None, estado=True)[:1].get()
            if AsistAsuntoEstudiant.objects.filter(asistente__usuario=rb_seguimiento.seguimiento.usuario).exists():
                gestor_cobros=AsistAsuntoEstudiant.objects.filter(asistente__usuario=rb_seguimiento.seguimiento.usuario)[:1].get()
                if utiliza_detalle:
                    detalle = []
                    data = {}
                    data['cabecera_tabla'] = ['Nombre del Gestor', 'Telefono', 'Email']
                    data['utiliza_url'] = False
                    if gestor_cobros:
                        detalle.append(
                            {
                                'detalle_tabla':[ #diccionario #1: contiene el detalle de la tabla. Debe estar en el orden de la cabecera ingresada en la linea 69.
                                    str(gestor_cobros.asistente.nombre_completo_inverso()),
                                    gestor_cobros.telefono,
                                    gestor_cobros.asistente.emailinst
                                ],
                                'otros': { #diccionario #2: informacion variada, no cambiar los indices.
                                    'periodo': False, #Enviar id de periodo si la url necesita realizar un cambio en el periodo de la sesion.
                                    'url': "", #enviar la url de cada detalle si se requere, caso contrario enviar "".
                                    'utiliza_url': False #true si desea mostrar un boton para redirigir a al url q envia en la linea anterior, false si no desea que aparezca en la web.
                                }
                            })
                    data['detalle'] = detalle
                    return data
            return {
                'notificacion_titulo': notificacion.nombre,
                'notificacion_descripcion': notificacion.descripcion,
                # 'urls': [{'url':'/solicitudonline', 'name':'Ir a Bandeja de Atencion', 'tipo':'info', 'icono':'share-alt'}],
                'tipo': 'info', #danger, warning, info, success. Esto cambia el color e iconos de las alertas mostradas.
                'utiliza_detalle': True, #true si la notificacion debe desplegar un detalle.
                'id': notificacion.id #si hay detalle enviar id de lo que se debe filtrar.
            }
        return None
    except Exception as e:
        print("ERROR gestor_cobro: "+str(e))
        return {"error": str(e)}

# ENCUESTA DE INGRESO A ITB
def encuestaitb(request, utiliza_detalle,notificacion_id):
    try:
        usuario = request.user
        notificacion = Notificacion.objects.get(pk=notificacion_id)
        inscripcion = Inscripcion.objects.filter(persona__usuario__is_active=True, persona__usuario=usuario).exclude(carrera__nombre='CONGRESO')[:1].get()
        fecha_hoy = datetime.now()
        # inscripcion = Inscripcion.objects.filter(pk=74994)[:1].get()
        if Matricula.objects.filter(inscripcion=inscripcion, nivel__nivelmalla=NIVEL_MALLA_UNO,nivel__periodo__activo=True, nivel__cerrado =False).exists():  #and inscripcion.id== 74994
            matricula = Matricula.objects.filter(inscripcion=inscripcion, nivel__nivelmalla=NIVEL_MALLA_UNO, nivel__periodo__activo=True, nivel__cerrado=False)[:1].get()
            if matricula.materia_asignada_testingreso(fecha_hoy):
                encuesta=EncuestaItb.objects.filter(inscripcion=matricula.inscripcion, estadorealizado=True)
            # listtestingreso = InscripcionTestIngreso.objects.filter(persona__usuario=usuario,horafincronometro=None).exclude(id=TESTDESERCION)
                if not encuesta: # listtestingreso
                    request.session['bloquea_notificaciones'] = True # OBLIGATORIO
                    return {
                        'notificacion_titulo': notificacion.nombre,
                        'notificacion_descripcion': notificacion.descripcion,
                        'urls': [{'url': '/encuestaitb', 'name': 'Ir al Test Ingreso', 'title': 'Ir al Test Ingreso',
                                  'tipo': 'success', 'icono': 'arrow-up'}
                                 ],
                        'tipo': 'warning',
                        'utiliza_detalle': False,  # true si la notificacion debe desplegar un detalle.
                        'id': notificacion.id  # si hay detalle enviar id de lo que se debe filtrar.
                    }
                return None
    except Exception as e:
        print("ERROR encuestaitb: " + str(e))
        return {"error": str(e)}

