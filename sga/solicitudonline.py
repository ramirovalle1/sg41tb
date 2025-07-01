import json
import locale
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import Sum, Q, Max
from django.forms import model_to_dict
from django.utils.encoding import force_str
from decorators import secure_module
from settings import EMAIL_ACTIVE, VALIDAR_ENTRADA_SISTEMA_CON_DEUDA, TIPO_RUBRO_SOLICITUD, NIVEL_MALLA_CERO, ASIGNATURA_EXAMEN_GRADO_CONDU, NOTA_PARA_APROBAR, \
     ASIST_PARA_APROBAR, TIPO_EXAMEN_COMPLEXIVO, CULMINACION_ESTUDIOS, ESPECIE_CAMBIO_PROGRAMACION, ESPECIE_RETIRO_MATRICULA, DIAS_ESPECIE, ESPECIE_JUSTIFICA_FALTA, \
     ESPECIE_JUSTIFICA_FALTA_AU, ID_TIPO_ESPECIE_REG_NOTA, VALIDA_DEUDA_EXAM_ASIST, SISTEMAS_GROUP_ID, ID_TIPO_SOLICITUD, EXAMEN_CONVALIDACION, \
     NIVELMALLA_INICIO_PRACTICA, ID_SOLIC__ONLINE, ESPECIE_EXAMEN,ESPECIE_RECUPERACION, ESPECIE_MEJORAMIENTO, TIPO_OTRO_RUBRO, ESPECIE_ASENTAMIENTOCONVENIO_SINVALOR, ESPECIE_ASENTAMIENTOCONVENIO_CONVALOR,ESPECIES_ASUNTOS_ESTUDIANTILES, TIPO_ESPECIE_RETIRO_MATRICULA, ID_TEST_ENCUESTA_DESERCION
from sga import forms
from sga.finanzas import generador_especies
from sga.models import  SolicitudEstudiante, Inscripcion, TipoCulminacionEstudio, CarreraTipoCulminacion, Carrera, Matricula, SolicitudOnline, \
     elimina_tildes, TipoOtroRubro, Rubro, RubroOtro, HistoricoRecordAcademico, AsignaturaMalla, TipoEspecieValorada, EspecieGrupo, \
     ProfesorMateria, RubroEspecieValorada, MateriaAsignada, Persona, RecordAcademico, Profesor, Materia, LeccionGrupo, AsistenciaLeccion, \
     Leccion, SolicitudSecretariaDocente, SolicitudesGrupo, ModuloGrupo, Coordinacion, CoordinacionDepartamento, SesionCaja, \
     AsistenteDepartamento, HorarioAsistenteSolicitudes, RubroInscripcion, ExamenConvalidacionIngreso, PagoTransferenciaDeposito, \
     CuentaBanco, CalificacionSolicitudes, Departamento, InscripcionTestIngreso, Test

from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.core.paginator import Paginator
from sga.commonviews import addUserData, ip_client_address
from django.template import RequestContext
from sga.forms import   TipoCulminacionForm, RespuestaEspecieForm,  ResolucionSolForm
from datetime import datetime, timedelta
from sga.tasks import send_html_mail


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

def mail_correoalumnoespecie(solicitud,emailestudiante):
        hoy = datetime.now().today()
        email=emailestudiante
        asunto = "Estimado/a estudiante el numero de tramite es " +elimina_tildes(solicitud.rubro.especie_valorada().serie)
        contenido = "ESPECIE " + elimina_tildes(solicitud.tipoe.nombre)
        send_html_mail(str(asunto),"emails/correoalumno_especie_libre.html", {'fecha': hoy,'contenido': contenido, 'asunto': asunto,'solicitud':solicitud},email.split(","))

@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
@transaction.atomic()
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action == 'addtipo':
                result = {}
                mensaje=''
                action_flag=''
                try:
                    if request.POST['idtp'] == '0':
                        if not TipoCulminacionEstudio.objects.filter(nombre=request.POST['nombre']).exists():
                            tipo = TipoCulminacionEstudio(nombre=request.POST['nombre'])
                            tipo.save()
                            result['result']  = "ok"
                            mensaje = 'Adicionado'
                            action_flag=ADDITION
                    else:
                        tipo = TipoCulminacionEstudio.objects.filter(id=int(request.POST['idtp'] ))[:1].get()
                        tipo.nombre=request.POST['nombre']
                        tipo.save()
                        result['result']  = "ok"
                        mensaje = 'Editado'
                        action_flag=CHANGE
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(tipo).pk,
                        object_id       = tipo.id,
                        object_repr     = force_str(tipo),
                        action_flag     = action_flag,
                        change_message  = mensaje +' Tipo Culminacion de Estudios (' + client_address + ')' )
                except Exception as e:
                    result['result']  = "bad"
                return HttpResponse(json.dumps(result), content_type="application/json")
            elif action=='verificareferencia':
                if request.POST['numero'] != '' and request.POST['ctabanco'] != '':
                    ref=request.POST['numero'].upper()
                    ctbanco=CuentaBanco.objects.filter(pk=request.POST['ctabanco'])
                    i = Inscripcion.objects.filter(persona__usuario=request.user)[:1].get()
                    if PagoTransferenciaDeposito.objects.filter(referencia=ref,cuentabanco=ctbanco).exists():
                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id=request.user.pk,
                            content_type_id=ContentType.objects.get_for_model(i).pk,
                            object_id=i.id,
                            object_repr=force_str(i),
                            action_flag=ADDITION,
                            change_message=' Ha intentado ingresar una referencia existente # ' +request.POST['numero'].upper() +' (' + client_address + ')')
                        return HttpResponse(json.dumps({'result':'bad'}),content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({'result':'ok'}),content_type="application/json")
                else:
                    return HttpResponse(json.dumps({'result':'bad2'}),content_type="application/json")

            elif action == 'consultatipos':
                result = {}
                if  CarreraTipoCulminacion.objects.filter(carrera__id=request.POST['carrera'],tipo__id=request.POST['tipo']).exists():
                    result['result']  = 'ok'
                else:
                    result['result']  = 'bad'

                return HttpResponse(json.dumps(result), content_type="application/json")

            elif action =='addsolicitud':
                try:
                    inscripcion = Inscripcion.objects.filter(pk=request.POST['inscripcion'])[:1].get()
                    solicitud = SolicitudOnline.objects.filter(pk=request.POST['solicitud'])[:1].get()

                    form =getattr(forms,solicitud.form,None)
                    # if solicitud.libre:
                    #     form.for_tipo(inscripcion)
                    f = form(request.POST)
                    if f.is_valid():

                        if solicitud.id == ID_SOLIC__ONLINE:
                            if Matricula.objects.filter(inscripcion=inscripcion).order_by('-fecha').exists():
                                pass
                                # matricula = Matricula.objects.filter(inscripcion=inscripcion).order_by('-fecha')[:1].get()
                                # matricula.observacionaplaza = f.cleaned_data['observacion']
                                # matricula.aplazamiento = True
                                # matricula.fechaaplaza = datetime.now()
                                # matricula.save()
                        if f.cleaned_data['tipoe'].id == ID_TIPO_SOLICITUD or f.cleaned_data['tipoe'].id == ESPECIE_JUSTIFICA_FALTA_AU:
                            if not 'comprobante' in request.FILES:
                                return HttpResponseRedirect("/solicitudonline?generar&id=3&error=TODOS LOS CAMPOS SON OBLIGATORIOS")

                            if f.cleaned_data['tipoe'].relaciodocente:
                                if not f.cleaned_data['materia']  or  not f.cleaned_data['profesor']:
                                    return HttpResponseRedirect("/solicitudonline?generar&id=3&error=TODOS LOS CAMPOS SON OBLIGATORIOS")
                            if len(f.cleaned_data['observacion']) > 500:
                                    return HttpResponseRedirect("/solicitudonline?generar&id=3&error=LA OBSERVACION EXCEDE DE LOS CARATERES PERMITIDOS(500)")

                        if f.cleaned_data['tipoe'].id == ESPECIE_JUSTIFICA_FALTA_AU:
                            if inscripcion.matricula():
                                materiasig=MateriaAsignada.objects.filter(id=f.cleaned_data['materia'])[:1].get()
                                matricula = inscripcion.matricula()
                                leccionesGrupo = LeccionGrupo.objects.filter(fecha__lte=datetime.now(),profesor=f.cleaned_data['profesor'],materia__nivel__periodo__activo=True,lecciones__clase__materia= materiasig.materia,lecciones__asistencialeccion__matricula=matricula,lecciones__asistencialeccion__asistio=False,lecciones__asistencialeccion__fechaaprobacion=None).order_by('-fecha', '-horaentrada')
                                cantidad = leccionesGrupo.count()
                                if cantidad == 0:
                                     return  HttpResponseRedirect('/solicitudonline?generar&id=3&error=NO TIENE INASISTENCIAS CON EL DOCENTE SELECCIONADO')


                        if f.cleaned_data['tipoe'].id == ESPECIE_RETIRO_MATRICULA:
                            grupo=0
                            if inscripcion.matricula():
                                grupo=inscripcion.matricula().nivel.grupo_id
                            else:
                                matriculaant = Matricula.objects.filter(Q(nivel__cerrado=True) | Q(liberada=True),inscripcion = inscripcion).order_by('-fecha')[:1].get()
                                grupo=matriculaant.nivel.grupo_id


                            if not InscripcionTestIngreso.objects.filter(persona=inscripcion.persona,grupo=grupo).exclude(aplicada=True).exists():
                                return  HttpResponseRedirect('/solicitudonline?generar&id=3&error=DEBE LLENAR LA ENCUESTA PORQUE SE RETIRA DE LA CARRERA ')



                        # print (f)
                        # if not SolicitudEstudiant e.objects.filter(solicitud=solicitud).exists():
                        if int(request.POST['id']) != 0:
                             if solicitud.libre:
                                 solicitudest = SolicitudEstudiante.objects.filter(id=request.POST['id'])[:1].get()
                                 solicitudest.observacion=f.cleaned_data['observacion']
                                 solicitudest.tipoe = f.cleaned_data['tipoe']
                                 solicitudest.celular=f.cleaned_data['celular']
                                 solicitudest.oficina= f.cleaned_data['oficina']
                             else:
                                 solicitudest = SolicitudEstudiante.objects.filter(id=request.POST['id'])[:1].get()
                                 solicitudest.correo=f.cleaned_data['correo']
                                 solicitudest.celular=f.cleaned_data['celular']
                                 solicitudest.oficina= f.cleaned_data['oficina']
                                 solicitudest.domicilio=f.cleaned_data['domicilio']
                                 solicitudest.fecha=datetime.now()
                        else:
                            if solicitud.libre:
                                solicitudest = SolicitudEstudiante(solicitud=solicitud,
                                                                  inscripcion=inscripcion,
                                                                  observacion=f.cleaned_data['observacion'],
                                                                  tipoe = f.cleaned_data['tipoe'],
                                                                  correo=f.cleaned_data['correo'],
                                                                  celular=f.cleaned_data['celular'],
                                                                  fecha=datetime.now())
                            else:
                                solicitudest = SolicitudEstudiante(solicitud=solicitud,
                                                                  inscripcion=inscripcion,
                                                                  correo=f.cleaned_data['correo'],
                                                                  celular=f.cleaned_data['celular'],
                                                                  oficina = f.cleaned_data['oficina'],
                                                                  domicilio=f.cleaned_data['domicilio'],
                                                                  fecha=datetime.now())
                        solicitudest.save()
                        if 'comprobante' in request.FILES:
                            solicitudest.comprobante= request.FILES['comprobante']
                            solicitudest.save()
                            adjunto=True
                        inscripcion.persona.email =solicitudest.correo
                        inscripcion.persona.telefono=solicitudest.celular
                        inscripcion.persona.save()
                        if solicitudest.tipoe:
                            if solicitudest.tipoe.relaciodocente:
                                solicitudest.materia_id = f.cleaned_data['materia']
                                solicitudest.profesor= f.cleaned_data['profesor']

                            if solicitudest.tipoe.relacionaasig:
                                solicitudest.asignatura = f.cleaned_data['asignatura']
                            solicitudest.save()

                        if 'tipo' in f.cleaned_data:
                            solicitudest.tipo = f.cleaned_data['tipo']
                        if 'tema' in f.cleaned_data:
                            solicitudest.tema = f.cleaned_data['tema']
                        solicitudest.save()
                        # solicitud = SolicitudEstudiante.objects.filter(id=request.GET['id'])[:1].get()
                        if solicitudest.tipoe.id == ESPECIE_JUSTIFICA_FALTA_AU:
                            if solicitudest.inscripcion.matricula():
                                matricula = solicitudest.inscripcion.matricula()
                                leccionesGrupo = LeccionGrupo.objects.filter(fecha__lte=solicitudest.fecha,profesor=solicitudest.profesor,materia__nivel__periodo__activo=True,lecciones__clase__materia=solicitudest.materia.materia,lecciones__asistencialeccion__matricula=matricula,lecciones__asistencialeccion__asistio=False,lecciones__asistencialeccion__fechaaprobacion=None).order_by('-fecha', '-horaentrada')
                                cantidad = leccionesGrupo.count()
                                if cantidad > 5:
                                    cantidad = 5
                                # solicitudest.rubro.especie_valorada().usrasig= request.user
                                # solicitudest.rubro.especie_valorada().save()

                                return HttpResponseRedirect("/solicitudonline?solicitud&id="+str(solicitudest.id)+"&cantidad="+str(cantidad))
                        if not solicitudest.tipoe.es_especie:
                            solicitudsec = SolicitudSecretariaDocente(persona=request.session['persona'],
                                                               solicitudestudiante=solicitudest,
                                                               tipo=solicitudest.tipoe.tiposolicitud,
                                                               descripcion=solicitudest.observacion,
                                                               fecha = datetime.now(),
                                                               hora = datetime.now().time(),
                                                               cerrada = False)
                            solicitudsec.save()
                            adjunto=False
                            solicitudest.solicitado=True
                            solicitudest.save()
                            if 'comprobante' in request.FILES:
                                solicitudsec.comprobante= request.FILES['comprobante']
                                # solicitudsec.referencia = f.cleaned_data['referenciatransferencia']
                                # solicitudsec.ctabanco = f.cleaned_data['cuentabanco']
                                solicitudsec.save()
                                adjunto=True
                            listasolicitudes=[]
                            coordinacion = Coordinacion.objects.filter(carrera=solicitudsec.solicitudestudiante.inscripcion.carrera)[:1].get()
                            for cdp in  CoordinacionDepartamento.objects.filter(coordinacion=coordinacion):
                                if EspecieGrupo.objects.filter(departamento=cdp.departamento,tipoe=solicitudsec.solicitudestudiante.tipoe).exists():
                                    asistentes=None
                                    if cdp.departamento.id == 27:
                                        cajeros = SesionCaja.objects.filter(abierta=True).values('caja__persona')
                                        # asistentes  = AsistenteDepartamento.objects.filter(departamento=cdp.departamento,persona__id__in=cajeros).exclude(puedereasignar=True).order_by('cantidadsol')
                                        if HorarioAsistenteSolicitudes.objects.filter(fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time()).exists():
                                             horarioasis = HorarioAsistenteSolicitudes.objects.filter(fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time()).values('usuario')
                                             asistentes = AsistenteDepartamento.objects.filter(departamento=cdp.departamento,persona__usuario__id__in=horarioasis,persona__id__in=cajeros,activo=True).exclude(puedereasignar=True).order_by('cantidadsol')
                                    else:
                                        if HorarioAsistenteSolicitudes.objects.filter(fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time()).exists():
                                             horarioasis = HorarioAsistenteSolicitudes.objects.filter(fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time()).values('usuario')
                                             asistentes = AsistenteDepartamento.objects.filter(departamento=cdp.departamento,persona__usuario__id__in=horarioasis,activo=True).exclude(puedereasignar=True).order_by('cantidadsol')
                                    if asistentes:
                                        for asis in asistentes:
                                            asis.cantidadsol =asis.cantidadsol +1
                                            asis.save()
                                            solicitudsec.usuario = asis.persona.usuario
                                            solicitudsec.personaasignada =asis.persona
                                            solicitudsec.asignado=True
                                            solicitudsec.fechaasignacion = datetime.now()
                                            solicitudsec.usuarioasigna=asis.persona.usuario
                                            solicitudsec.departamento=asis.departamento
                                            solicitudsec.save()

                                            listasolicitudes.append(asis.persona.emailinst)
                                            break
                            if listasolicitudes:
                                try:
                                     hoy = datetime.now().today()
                                     contenido = "  Solicitudes Asignadas"
                                     descripcion = "Ud. tiene solicitudes por atender"
                                     send_html_mail(contenido,
                                        "emails/notificacion_solicitud_adm.html", {'fecha': hoy,'contenido': contenido,'descripcion':descripcion,'opcion':'1'},listasolicitudes)
                                except Exception as e:
                                    print((e))
                                    pass
                            if EMAIL_ACTIVE:
                                # f.instance.mail_subject_nuevo()
                                #OCastillo 17-05-2019
                                gruposexcluidos = [SISTEMAS_GROUP_ID]
                                lista=''

                                lista = str(solicitudsec.persona.email)
                                hoy = datetime.now().today()
                                contenido = "Nueva Solicitud"
                                descripcion = "Estimado/a estudiante. Su solicitud ha sido recibida. Sera asignada al Departamento correspondiente. Puede ver el estado de la misma en el Sistema."
                                send_html_mail(contenido,
                                    "emails/nuevasolicitud.html", {'d': solicitudsec, 'fecha': hoy,'contenido': contenido,'descripcion':descripcion,'opcion':'1'},lista.split(','))

                                #traigo el correo del grupo a quien le corresponde el tipo de solicitud
                                if SolicitudesGrupo.objects.filter(tiposolic=solicitudsec.tipo,carrera=inscripcion.carrera.id).exists():
                                    grupo_solicitud=SolicitudesGrupo.objects.filter(tiposolic=solicitudsec.tipo,carrera=inscripcion.carrera.id).values('grupo')
                                    if ModuloGrupo.objects.filter(grupos__in=grupo_solicitud).exists():
                                        correo_solicitud=[]
                                        for correo_grupo in ModuloGrupo.objects.filter(grupos__in=grupo_solicitud):
                                            correo_solicitud.append(correo_grupo.correo)
                                            if lista:
                                                lista = lista+','+correo_grupo.correo
                                            else:
                                                lista = correo_grupo.correo
                                else:
                                    #Para el caso de una solicitud tipo general para todas las carreras
                                    if SolicitudesGrupo.objects.filter(tiposolic=solicitudsec.tipo,todas_carreras=True).exists():
                                        if solicitudsec.tipo.sistema==True:
                                            grupo_solicitud=SolicitudesGrupo.objects.filter(tiposolic=solicitudsec.tipo,todas_carreras=True).values('grupo')
                                        else:
                                            grupo_solicitud=SolicitudesGrupo.objects.filter(tiposolic=solicitudsec.tipo,todas_carreras=True).exclude(grupo__id__in=gruposexcluidos).values('grupo')
                                        if ModuloGrupo.objects.filter(grupos__in=grupo_solicitud).exists():
                                           correo_solicitud=[]
                                           for correo_grupo in ModuloGrupo.objects.filter(grupos__in=grupo_solicitud):
                                               correo_solicitud.append(correo_grupo.correo)
                                               if lista:
                                                    lista = lista+','+correo_grupo.correo
                                               else:
                                                    lista = correo_grupo.correo

                                hoy = datetime.now().today()
                                contenido = "Nueva Solicitud"
                                # descripcion = solicitud.descripcion
                                # if adjunto:
                                #      descripcion = descripcion +   " Archivo adjunto"
                                #     # descripcion = solicitud.descripcion +  "Estudiante ha realizado solicitud. Revisar el detalle de la misma en el Modulo Solicitudes de Alumnos. Archivo adjunto"
                                send_html_mail(contenido,
                                    "emails/nuevasolicitud.html", {'d': solicitudsec, 'fecha': hoy,'contenido': contenido,'adjunto':adjunto,'opcion':'2'},lista.split(','))
                                if 'comprobante' in request.FILES:
                                    pass

                                return HttpResponseRedirect("/solicitudonline?action=verlibres")
                        else:
                            return HttpResponseRedirect("/solicitudonline?solicitud&id="+str(solicitudest.id))

                    else:
                        return HttpResponseRedirect("/solicitudonline?generar&id=3&error=ERROR EN EL FORMULARIO DE SOLICITUD... LA OBSERVACION NO DEBE SUPERAR LOS 500 CARACTERES, VERIFIQUE EL PESO DEL DOCUMENTO Y SU EXTENSION")
                except Exception as e:
                    print(e)
                    return HttpResponseRedirect("/solicitudonline?error="+str(e))
            elif action == 'addtipocarrera':
                result = {}
                try:
                    carrera = Carrera.objects.filter(pk=request.POST['c'])[:1].get()
                    tipo = TipoCulminacionEstudio.objects.filter(pk=request.POST['t'])[:1].get()
                    carreratipo = CarreraTipoCulminacion(carrera=carrera,
                                                         tipo=tipo)
                    carreratipo.save()

                    result['result']  = "ok"
                    return HttpResponse(json.dumps(result), content_type="application/json")
                except Exception as e:
                    result['result']  = str(e)
                    return HttpResponse(json.dumps(result), content_type="application/json")
            elif action =='consultamateria':
                materias=[]
                result={}
                especie = SolicitudEstudiante.objects.filter(pk=request.POST['idon'])[:1].get()

                # mat = Inscripcion.objects.filter(pk=request.POST['id'])[:1].get()
                # for m in mat.matricula().materia_asignada():
                #     m.profesores()
                #



                # result  = {"materias": [{"id": x.materia.id, "asig": x.materia.asignatura.nombre } for x in mat.matricula().materia_asignada()]}
                result['result']  = 'ok'
                result['materia']  = especie.materia.materia.id
                result['profesor']  = especie.profesor.id
                result['especienum']  = especie.rubro.especie_valorada().serie
                result['id']  = especie.rubro.inscripcion.id
                return HttpResponse(json.dumps(result), content_type="application/json")

            elif action =='consultamateriaant':
                materias=[]
                result={}
                mat = Inscripcion.objects.filter(pk=request.POST['id'])[:1].get()
                for m in mat.matricula().materia_asignada():
                    m.profesores()


                result  = {"materias": [{"id": x.materia.id, "asig": x.materia.asignatura.nombre } for x in mat.matricula().materia_asignada()]}
                result['result']  = 'ok'
                return HttpResponse(json.dumps(result), content_type="application/json")
            elif action =='consultaprofesor':

                result  = {"profesor": [{"id": x.profesor.id, "nombre": x.profesor.persona.nombre_completo() } for x in ProfesorMateria.objects.filter(materia__id=request.POST['id'])]}
                result['result']  = 'ok'
                return HttpResponse(json.dumps(result), content_type="application/json")


            elif action =='responder':
                result = {}
                try:
                    solicitud = SolicitudEstudiante.objects.get(pk=request.POST['idsol'])
                    if request.POST['aprobado'] =='1':
                        solicitud.aprobado=True
                    else:
                        solicitud.aprobado=False

                    solicitud.respuesta=request.POST['respuesta']
                    solicitud.fechares=datetime.now()
                    if 'nuevotipo' in  request.POST:
                        if request.POST['nuevotipo'] != "":
                            solicitud.nuevotipo_id =int(request.POST['nuevotipo'])
                    solicitud.save()
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(solicitud).pk,
                        object_id       = solicitud.id,
                        object_repr     = force_str(solicitud),
                        action_flag     = ADDITION,
                        change_message  = 'Respuesta de Solicitud (' + client_address + ')' )
                    result['result']  = "ok"
                    if solicitud.solicitud.libre:
                        solicitud.mail_respuesta_especielibre()
                    else:
                        solicitud.mail_respuesta()
                    return HttpResponse(json.dumps(result), content_type="application/json")
                except Exception as e:
                    result['result']  = str(e)
                    return HttpResponse(json.dumps(result), content_type="application/json")



            elif action =='consulta':
                data = {}
                try:
                    persona = Persona.objects.filter(usuario =request.user )[:1].get()
                    tipoespecie = TipoEspecieValorada.objects.filter(pk=request.POST['tipo'])[:1].get()
                    if tipoespecie.informacion:
                        data['informacion'] = tipoespecie.informacion
                    else:
                        data['informacion'] = 'bad'
                     # if Inscripcion.objects.filter(persona=persona).exists():
                    inscripcion = Inscripcion.objects.get(persona=persona)
                    #OCastillo 26-04-2022 validar si estudiante tiene deuda no permitir comprar especies de asentamiento de notas, examen ni recuperacion
                    if inscripcion.tiene_deuda():
                        if tipoespecie.id == ID_TIPO_ESPECIE_REG_NOTA or tipoespecie.id == ESPECIE_EXAMEN or tipoespecie.id == ESPECIE_RECUPERACION or tipoespecie.id == ESPECIE_MEJORAMIENTO:
                            data['informacion'] = 'bad'
                            data['result2'] = 'ESTIMADO ESTUDIANTE DEBE ESTAR AL DIA EN SUS PAGOS PARA REALIZAR ESTA SOLICITUD'
                            return HttpResponse(json.dumps(data), content_type="application/json")

                    if tipoespecie.id == EXAMEN_CONVALIDACION :
                        if inscripcion.carrera.validacionprofesional:
                            if ExamenConvalidacionIngreso.objects.filter(inscripcion=inscripcion,aprobada=True).exists():
                                    data['result'] = 'YA TIENE APROBADO ESTE TRAMITE'
                                    return HttpResponse(json.dumps(data), content_type="application/json")
                            if not RubroInscripcion.objects.filter(rubro__inscripcion=inscripcion,rubro__cancelado=True).exists():
                                data['result'] = 'PARA SOLICITAR EL TRAMITE DEBE CANCELAR LA INSCRIPCION'
                                return HttpResponse(json.dumps(data), content_type="application/json")
                        else:
                            data['result'] = 'SU CARRERA NO ADMITE ESTE TRAMITE'
                            return HttpResponse(json.dumps(data), content_type="application/json")



                    if tipoespecie.relaciodocente:
                        if not inscripcion.matricula() and tipoespecie.id == ESPECIE_JUSTIFICA_FALTA_AU:
                            data['result'] = 'NECESITA ESTAR MATRICULADO PARA SOLICITAR LA ESPECIE'
                            return HttpResponse(json.dumps(data), content_type="application/json")
                        materia=[]
                        inscripcion = Inscripcion.objects.get(persona=persona)
                        if tipoespecie.id == ESPECIE_JUSTIFICA_FALTA_AU:
                            m = inscripcion.matricula()
                            fechamax = datetime.now() - timedelta(days=DIAS_ESPECIE)
                            if RubroEspecieValorada.objects.filter(tipoespecie=tipoespecie,rubro__inscripcion=inscripcion, aplicada=False,fecha__gte=fechamax).exclude(materia=None).exists():
                               materiaid = RubroEspecieValorada.objects.filter(tipoespecie=tipoespecie,rubro__inscripcion=inscripcion,
                                                                           aplicada=False,fecha__gte=fechamax).distinct('materia').values('materia')

                               materias= m.materia_asignada().filter().exclude(id__in=materiaid)
                            else:
                               materias = m.materia_asignada().filter()
                            for m in materias:
                                materia.append({'id':m.id,'asignatura': elimina_tildes(m.materia.asignatura.nombre) })
                        else:

                        # if inscripcion.matricula():
                            for m in Matricula.objects.filter(inscripcion=inscripcion):
                                fechamax = datetime.now() - timedelta(days=DIAS_ESPECIE)
                                if RubroEspecieValorada.objects.filter(tipoespecie=tipoespecie,rubro__inscripcion=inscripcion, aplicada=False,fecha__gte=fechamax).exclude(materia=None).exists():
                                   materiaid = RubroEspecieValorada.objects.filter(tipoespecie=tipoespecie,rubro__inscripcion=inscripcion,
                                                                               aplicada=False,fecha__gte=fechamax).distinct('materia').values('materia')

                                   materias= m.materia_asignada().filter().exclude(id__in=materiaid)
                                else:
                                   materias = m.materia_asignada().filter()
                                for m in materias:
                                    materia.append({'id':m.id,'asignatura': elimina_tildes(m.materia.asignatura.nombre) })
                        data['result'] = 'ok'
                        data['op'] = 'materia'
                        data['materias'] = materia
                        return HttpResponse(json.dumps(data), content_type="application/json")
                    elif tipoespecie.relacionaasig :
                        malla= inscripcion.malla_inscripcion().malla
                        asigrecord = RecordAcademico.objects.filter(inscripcion=inscripcion,aprobada=True).values('asignatura')
                        asignaturas = AsignaturaMalla.objects.filter(malla=malla).exclude(asignatura__id__in=asigrecord)
                        asignatura=[]
                        for a in asignaturas:
                            asignatura.append({'id':a.asignatura.id,'asignatura': elimina_tildes(a.asignatura.nombre) })
                        data['result'] = 'ok'
                        data['op'] = 'asignatura'
                        data['asignatura'] = asignatura
                        return HttpResponse(json.dumps(data), content_type="application/json")
                    else:
                        data['result'] = 'ok'
                        return HttpResponse(json.dumps(data), content_type="application/json")
                except Exception as e:
                    data['result'] = 'e'
                    return HttpResponse(json.dumps(data), content_type="application/json")

            elif action == 'consulta_departamento':
                print(request.POST)
                data = {}
                try:
                    especies = []
                    especie_grupo=[]
                    especies.append({'id':'---','nombre': '---','valor': '----' })
                    departamento = Departamento.objects.get(pk=request.POST['depa'])
                    especie_grupo = EspecieGrupo.objects.filter(departamento=departamento)
                    tipos_especies = (TipoEspecieValorada.objects.filter(id__in=especie_grupo.values('tipoe'),activa=True)
                                      .exclude(id__in=ESPECIES_ASUNTOS_ESTUDIANTILES)
                                      .exclude(id=93)
                                      .order_by('nombre'))

                    for te in tipos_especies:
                        precio = 0
                        if te.precio:
                            if te.precio>0:
                                precio=te.precio

                        especies.append({'id':te.id,'nombre': elimina_tildes(te.nombre),'valor': precio })
                    print(especies)
                    data['result'] = 'ok'
                    data['especies'] = especies
                    return HttpResponse(json.dumps(data), content_type="application/json")

                except Exception as e:
                    print(e)
                    data['result'] = 'e'
                    return HttpResponse(json.dumps(data), content_type="application/json")


            elif action =='consultadocente':
                data = {}
                tipoespecie = TipoEspecieValorada.objects.filter(pk=request.POST['tipo'])[:1].get()
                try:
                    materiaasignada = MateriaAsignada.objects.filter(pk=request.POST['materia'])[:1].get()
                    # OCastillo 12-09-2022 para las materias en nivel cerrado solo se puede generar especie hasta       ias
                    if tipoespecie.id == ID_TIPO_ESPECIE_REG_NOTA or tipoespecie.id == ESPECIE_EXAMEN or tipoespecie.id == ESPECIE_RECUPERACION or tipoespecie.id == ESPECIE_MEJORAMIENTO:
                        if materiaasignada.matricula.nivel.cerrado==True :
                            fechacierre=materiaasignada.matricula.nivel.fechacierre
                            if (datetime.now().date() - materiaasignada.matricula.nivel.fechacierre).days > 45:
                                data['docente'] = 'bad'
                                data['mensaje'] =  'ESTIMADO ESTUDIANTE SE HA VENCIDO EL PLAZO DE ASENTAMIENTO DE NOTAS. EL NIVEL ESTA CERRADO : ' +str(fechacierre)+ ' FAVOR COMUNICARSE CON SU COORDINACION'
                                return HttpResponse(json.dumps(data), content_type="application/json")
                    profesores=[]
                    arreglo_pr=[]
                    for p in materiaasignada.materia.profesores_materia():
                        if not p.profesor.id in arreglo_pr:
                            if p.profesor.activo==True:
                                arreglo_pr.append(p.profesor.id)
                                profesores.append({'id':p.profesor.id,'profesor': elimina_tildes(p.profesor.persona.nombre_completo_inverso()) })
                    if len(profesores)!=0:
                        data['result'] = 'ok'
                        data['op'] = 'materia'
                        data['profesores'] = profesores
                        return HttpResponse(json.dumps(data), content_type="application/json")
                    else:
                       data['docente'] = 'bad'
                       data['mensaje']='Docente de la materia escogida no esta activo, favor comunicarse con su coordinacion'
                       return HttpResponse(json.dumps(data), content_type="application/json")
                except Exception as e:
                    data['result'] = 'e'
                    return HttpResponse(json.dumps(data), content_type="application/json")

            elif action =='resolucion':
                result = {}
                try:
                    solicitud = SolicitudEstudiante.objects.get(pk=request.POST['idsol'])

                    solicitud.resolucion=request.POST['resolucion']
                    solicitud.fecharesol=datetime.now()
                    solicitud.save()
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(solicitud).pk,
                        object_id       = solicitud.id,
                        object_repr     = force_str(solicitud),
                        action_flag     = ADDITION,
                        change_message  = 'Adicionada Resolucion (' + client_address + ')' )
                    result['result']  = "ok"
                    # if solicitud.solicitud.libre:
                    #     solicitud.mail_respuesta_especielibre()
                    # else:
                    #     solicitud.mail_respuesta()
                    return HttpResponse(json.dumps(result), content_type="application/json")
                except Exception as e:
                    result['result']  = str(e)
                    return HttpResponse(json.dumps(result), content_type="application/json")
            elif action == 'generaespecienot':
                result = {}
                try:
                    tipoespecie = TipoEspecieValorada.objects.get(pk=ID_TIPO_ESPECIE_REG_NOTA)
                    inscripcion = Inscripcion.objects.get(persona__usuario=request.user)
                    materiaasignada = MateriaAsignada.objects.get(id=request.POST['idmatasign'])

                    rubro = Rubro(fecha=datetime.now(),
                                valor=tipoespecie.precio,
                                inscripcion = inscripcion,
                                cancelado=tipoespecie.precio==0,
                                fechavence=datetime.now())
                    rubro.save()

                    # Rubro especie valorada
                    serie = 0
                    valor = RubroEspecieValorada.objects.filter(rubro__fecha__year=rubro.fecha.year).aggregate(Max('serie'))
                    if valor['serie__max']!=None:
                        serie = valor['serie__max']+1

                        # OCU 09-junio-2017 para evitar que la serie de la especie se duplique
                    if not RubroEspecieValorada.objects.filter(rubro__fecha__year=rubro.fecha.year,serie=serie).exists():
                        rubroe = RubroEspecieValorada(rubro=rubro,
                                                      tipoespecie=tipoespecie,
                                                      serie=serie,
                                                      aplicada = False,
                                                      fecha = datetime.now(),
                                                      usuario = request.user,
                                                      materia = materiaasignada,
                                                      disponible = False)
                                                        # profesor = models.ForeignKey(Profesor, on_delete=models.CASCADE)
                                                        # disponible = True
                                                        # f_registro = models.DateField()

                        rubroe.save()
                    else:
                        rubro.delete()
                        return HttpResponse(json.dumps({'result':'El rubro especie ya existe'}), content_type="application/json")
                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    #Log crear rubro especie OCU 08-nov-2017
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(tipoespecie).pk,
                        object_id       = tipoespecie.id,
                        object_repr     = force_str(tipoespecie),
                        action_flag     = ADDITION,
                        change_message  =  "Creado Rubro Especie Registro Nota  " +  '(' + str(inscripcion) + ')' + '(' +  client_address + ')' )
                    return HttpResponse(json.dumps({'result':'ok'}), content_type="application/json")
                except Exception as e:
                    result['result']  = str(e)
                    return HttpResponse(json.dumps(result), content_type="application/json")

            elif action == 'busqreq':
                try:
                    html=None
                    solicitud = SolicitudEstudiante.objects.get(id=request.POST['idsol'])
                    if RubroEspecieValorada.objects.filter(rubro=solicitud.rubro).exists():
                        tramite = RubroEspecieValorada.objects.filter(rubro=solicitud.rubro)[:1].get()
                        if tramite.aplicada and not solicitud.calificacion:
                            html = '<h2> Solicitud: </h2><h3>'+ solicitud.observacion +'</h3>'
                            if tramite.obsautorizar:
                                html = html + '<hr><div class="row-fluid">' \
                                              '<div class="span12"><h3>Respuesta: </h3><h4>'+ tramite.obsautorizar +'</h4></div></div>'
                            if solicitud.comprobante:
                                html = html + '<br><div class="row-fluid">' \
                                              '<div class="span4"><h3>Archivo: <a href="'+ solicitud.comprobante.url +'" class="btn btn-success">' \
                                              '<i class="icon-download"></i> Descargar</a></h3></div></div>'
                    else:
                        if solicitud.es_solicitud().cerrada:
                            html = '<h2> Solicitud: </h2><h3>'+ solicitud.observacion +'</h3>'
                            if solicitud.es_solicitud().resolucion:
                                html = html + '<hr><div class="row-fluid">' \
                                              '<div class="span12"><h3>Respuesta: </h3><h4>'+ solicitud.es_solicitud().resolucion +'</h4></div></div>'

                    return HttpResponse(json.dumps({'result': 'ok','html': html}), content_type="application/json")
                except Exception as e:
                    print(e)
                    return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")

            elif action == 'guardcalif':
                try:
                    if request.POST['observacion']=='':
                        obs='NINGUNA'
                    else:
                        obs= request.POST['observacion']
                    solicitud = SolicitudEstudiante.objects.get(id=request.POST['idsol'])
                    solicitud.calificacion_id = request.POST['calific']
                    solicitud.obscalificacion = obs
                    solicitud.save()
                    client_address = ip_client_address(request)

                    #Log de guardar calificacion en solicitud estudiante
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(solicitud).pk,
                        object_id       = solicitud.id,
                        object_repr     = force_str(solicitud),
                        action_flag     = ADDITION,
                        change_message  = 'Calificacion agregada  (' + client_address + ')' )
                    return HttpResponse(json.dumps({'result': 'ok'}), content_type="application/json")
                except Exception as e:
                    print(e)
                    return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")


        else:
            data = {'title': 'Solicitud On-Line'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']
                if action == 'eliminatipo':
                    tipo = TipoCulminacionEstudio.objects.filter(id=int(request.GET['id'] ))[:1].get()
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(tipo).pk,
                        object_id       = tipo.id,
                        object_repr     = force_str(tipo),
                        action_flag     = DELETION,
                        change_message  = ' Tipo Culminacion de Estudios (' + client_address + ')' )
                    tipo.delete()
                    result={}
                    result['result']  = "ok"
                    return HttpResponse(json.dumps(result), content_type="application/json")

                if action == 'borrartipo':
                    carreratipo = CarreraTipoCulminacion.objects.filter(id=int(request.GET['id'] ))[:1].get()
                    carr = carreratipo.carrera.nombre
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(carreratipo).pk,
                        object_id       = carreratipo.id,
                        object_repr     = force_str(carreratipo),
                        action_flag     = DELETION,
                        change_message  = 'Eliminado Tipo Culminacion de Estudios (' + client_address + ')' )
                    carreratipo.delete()
                    result={}
                    return  HttpResponseRedirect('/carrera_admi?s='+carr)
                elif action == 'verlibres':
                    persona = data['persona']
                    solicitudes = None
                    if Inscripcion.objects.filter(persona=persona).exists():
                        inscripcion = Inscripcion.objects.get(persona=persona)
                        solicitudes=SolicitudEstudiante.objects.filter(inscripcion=inscripcion,solicitud__libre=True).order_by('-fecha')
                        data['solicitudes'] = solicitudes
                        data['inscripcion']=inscripcion
                        data['ESPECIE_JUSTIFICA_FALTA_AU']=ESPECIE_JUSTIFICA_FALTA_AU
                        data['calificaciones'] = CalificacionSolicitudes.objects.filter()

                        if 'id' in request.GET:
                            solicitudes = SolicitudEstudiante.objects.filter(id=request.GET['id']).order_by('-fecha')
                            solic = SolicitudEstudiante.objects.get(id=request.GET['id'])
                            if not solic.calificacion:
                                data['solic'] = solic
                            else:
                                solicitudes = None

                        return render(request ,"solicitudonline/solicitudlibre.html" ,  data)

                elif action =='eliminarespecie':
                    persona = data['persona']
                    solicitudest = SolicitudEstudiante.objects.filter(pk=request.GET['id'])[:1].get()
                    if solicitudest.rubro.puede_eliminarse():
                        inscripcion = Inscripcion.objects.get(persona=persona)

                        solicitudes=SolicitudEstudiante.objects.filter(inscripcion=inscripcion,solicitud__libre=True)
                        data['solicitudes'] = solicitudes
                        data['inscripcion']=inscripcion
                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(solicitudest).pk,
                            object_id       = solicitudest.id,
                            object_repr     = force_str(solicitudest),
                            action_flag     = DELETION,
                            change_message  = 'Eliminada Solicitud OnLine ' + str(solicitudest.tipoe) + '(' + client_address + ')' )
                        solicitudest.rubro.delete()
                        solicitudest.delete()
                        return  HttpResponseRedirect('/solicitudonline?action=verlibres')
                elif action == 'verespecie':
                    persona = data['persona']
                    solicitudest = SolicitudEstudiante.objects.filter(pk=request.GET['id'])[:1].get()
                    data['solicitud']=solicitudest
                    data['ver'] = 1
                    data['mes']=str(solicitudest.fecha.strftime("%B")).capitalize()
                    data['anio']=solicitudest.fecha.year
                    data['dia2']=solicitudest.fecha.day
                    if solicitudest.materia:
                        materiaasignada = solicitudest.materia
                        matricula = solicitudest.materia.matricula
                        if solicitudest.tipoe.id == ESPECIE_JUSTIFICA_FALTA_AU:
                            if solicitudest.solicitado:
                                leccionesGrupo = LeccionGrupo.objects.filter(fecha__lte=solicitudest.fecha,profesor=solicitudest.profesor,materia__nivel__periodo__activo=True,lecciones__clase__materia= materiaasignada.materia,lecciones__asistencialeccion__matricula=matricula,lecciones__asistencialeccion__asistio=False,lecciones__asistencialeccion__aprobado=False).order_by('-fecha', '-horaentrada')
                            else:
                                leccionesGrupo = LeccionGrupo.objects.filter(fecha__lte=solicitudest.fecha,profesor=solicitudest.profesor,materia__nivel__periodo__activo=True,lecciones__clase__materia= materiaasignada.materia,lecciones__asistencialeccion__matricula=matricula,lecciones__asistencialeccion__asistio=False,lecciones__asistencialeccion__fechaaprobacion=None).order_by('-fecha', '-horaentrada')
                            if  leccionesGrupo.count() > 5:
                                data['cantidad'] = 5
                            else:
                                data['cantidad'] = leccionesGrupo.count()


                    return render(request ,"solicitudonline/especie_universal.html" ,  data)

                elif action == 'vertipos':
                    try:
                        carrera = Carrera.objects.get(pk=request.GET['c'])
                        # if CarreraTipoCulminacion.objects.filter(carrera=carrera).exists():
                        data['tipos'] = CarreraTipoCulminacion.objects.filter(carrera=carrera)
                        return render(request ,"solicitudonline/tipos.html" ,  data)
                        # else:
                        #     return render(request ,"inscripciones/panel.html" ,  data)
                    except:
                        return render(request ,"solicitudonline/tipos.html" ,  data)



                elif action =='generarsolicitud':
                    try:
                        solicitud = SolicitudEstudiante.objects.filter(id=request.GET['id'])[:1].get()
                        asist = None
                        if solicitud.tipoe.id == ESPECIE_JUSTIFICA_FALTA_AU:
                            if solicitud.inscripcion.matricula():
                                matricula = solicitud.inscripcion.matricula()
                                leccionesGrupo = LeccionGrupo.objects.filter(fecha__lte=solicitud.fecha,profesor=solicitud.profesor,materia__nivel__periodo__activo=True,lecciones__clase__materia=solicitud.materia.materia,lecciones__asistencialeccion__matricula=matricula,lecciones__asistencialeccion__asistio=False,lecciones__asistencialeccion__fechaaprobacion=None).order_by('-fecha', '-horaentrada')
                                asist = LeccionGrupo.objects.filter(fecha__lte=solicitud.fecha,profesor=solicitud.profesor,materia__nivel__periodo__activo=True,lecciones__clase__materia=solicitud.materia.materia,lecciones__asistencialeccion__matricula=matricula,lecciones__asistencialeccion__asistio=False,lecciones__asistencialeccion__fechaaprobacion=None).order_by('-fecha', '-horaentrada').values('lecciones__asistencialeccion')

                                if leccionesGrupo.count() == 0:
                                    return HttpResponseRedirect("/solicitudonline?error=NO TIENE INASISTENCIAS CON EL DOCENTE SELECCIONADO")
                        # if solicitud.tipoe.relaciodocente:
                        #     if not solicitud.inscripcion.matricula():
                        #         return HttpResponseRedirect("/solicitudonline?error= NECESITA ESTAR MATRICULADO PARA SOLICITAR LA ESPECIE")
                        if asist:
                            for a in AsistenciaLeccion.objects.filter(id__in=asist)[:5]:
                                    a.aprobado = False
                                    a.save()

                        hoy =datetime.now().date()
                        solicitud.solicitado=True

                        solicitud.fecha = datetime.now()
                        solicitud.save()
                        rubro = None
                        if solicitud.solicitud.libre:
                            tipoEspecie = TipoEspecieValorada.objects.get(pk=solicitud.tipoe.id)

                            rubro = Rubro(fecha=datetime.now().date(),
                                        valor=tipoEspecie.precio,
                                        inscripcion = solicitud.inscripcion,
                                        cancelado=tipoEspecie.precio==0,
                                        # fechavence=datetime.now().date()  + timedelta(45))
                                        #OCastillo 11-04-2022 se debe generar la especie con la fecha del dia
                                        fechavence=datetime.now().date())
                            rubro.save()

                            # Rubro especie valorada
                            rubroespecie = generador_especies.generar_especie(rubro=rubro, tipo=tipoEspecie)
                            rubroespecie.autorizado=False
                            rubroespecie.save()
                            #OCastillo 26-04-2022 nueva especie cambio de modalidad
                            if tipoEspecie.id==84:
                                rubronuevo = Rubro(fecha=datetime.now().date(),
                                        valor=50,
                                        inscripcion = solicitud.inscripcion,
                                        cancelado=tipoEspecie.precio==0,

                                        fechavence=datetime.now().date())
                                rubronuevo.save()

                                rubrootro = RubroOtro(rubro=rubronuevo,
                                        tipo_id = TIPO_OTRO_RUBRO,
                                        descripcion='DERECHO')
                                rubrootro.save()

                            #OCastillo 12-05-2022 nueva especie examen complexivo
                            #OCastillo 13-07-2022 otro rubro cambia a 10 examen complexivo
                            #OCastillo 15-07-2022 se cambia por id de la especie al cambiar el nombre
                            if tipoEspecie.id==85:
                                rubronuevo = Rubro(fecha=datetime.now().date(),
                                        valor=10,
                                        inscripcion = solicitud.inscripcion,
                                        cancelado=tipoEspecie.precio==0,

                                        fechavence=datetime.now().date())
                                rubronuevo.save()

                                rubrootro = RubroOtro(rubro=rubronuevo,
                                        tipo_id = TIPO_OTRO_RUBRO,
                                        descripcion='DERECHO A COMPLEXIVO')
                                rubrootro.save()

                            if solicitud.materia:
                                rubroespecie.materia = solicitud.materia
                                rubroespecie.save()


                        else:
                            if solicitud.solicitud.valor >0:
                                valor = float(solicitud.solicitud.valor)
                                tipootro = TipoOtroRubro.objects.get(pk=TIPO_RUBRO_SOLICITUD)


                                rubro = Rubro(fecha=datetime.now().date(),
                                              valor=valor,
                                                  inscripcion=solicitud.inscripcion,
                                              cancelado=False,
                                              fechavence=hoy)
                                rubro.save()
                                rubrootro = RubroOtro(rubro=rubro, tipo=tipootro, descripcion='SOLICITUD ' + elimina_tildes(solicitud.solicitud.nombre) )
                                rubrootro.save()

                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(solicitud).pk,
                            object_id       = solicitud.id,
                            object_repr     = force_str(solicitud),
                            action_flag     = ADDITION,
                            change_message  = 'Generada Solicitud OnLine '+ str(solicitud.tipoe) + '(' + client_address + ')' )


                        if rubro:
                            solicitud.rubro = rubro
                            solicitud.save()
                            if tipoEspecie.id==TIPO_ESPECIE_RETIRO_MATRICULA:
                                realizartest = Test.objects.get(pk=ID_TEST_ENCUESTA_DESERCION,estado=True)
                                grupo=0
                                if solicitud.inscripcion.matricula():
                                    grupo=solicitud.inscripcion.matricula().nivel.grupo_id
                                else:
                                    matriculaant = Matricula.objects.filter(Q(nivel__cerrado=True) | Q(liberada=True),inscripcion = solicitud.inscripcion).order_by('-fecha')[:1].get()
                                    grupo=matriculaant.nivel.grupo_id

                                inscriptest=InscripcionTestIngreso.objects.filter(persona=solicitud.inscripcion.persona,estado=True,test=realizartest,grupo=grupo)[:1].get()
                                inscriptest.rubroespecie=rubro.id
                                inscriptest.save()



                        if not solicitud.solicitud.libre:
                            solicitud.correo_estudiante()
                        else:
                            if EMAIL_ACTIVE:
                                emailestudiante=elimina_tildes(solicitud.inscripcion.persona.emailinst)+','+elimina_tildes(solicitud.inscripcion.persona.email)
                                mail_correoalumnoespecie(solicitud,emailestudiante)
                        listaespecies=[]
                        if rubro.cancelado==True :
                            coordinacion = Coordinacion.objects.filter(carrera=solicitud.inscripcion.carrera)[:1].get()
                            for cdp in  CoordinacionDepartamento.objects.filter(coordinacion=coordinacion):
                                if EspecieGrupo.objects.filter(departamento=cdp.departamento,tipoe=solicitud.tipoe).exists():
                                    asistentes=None
                                    if HorarioAsistenteSolicitudes.objects.filter(fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time()).exists():
                                         horarioasis = HorarioAsistenteSolicitudes.objects.filter(fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time()).values('usuario')
                                         asistentes = AsistenteDepartamento.objects.filter(departamento=cdp.departamento,persona__usuario__id__in=horarioasis,activo=True).exclude(puedereasignar=True).order_by('cantidad')
                                    # asistentes = AsistenteDepartamento.objects.filter(departamento=cdp.departamento).exclude(puedereasignar=True).order_by('cantidad')
                                    if asistentes:
                                        for asis in asistentes:
                                            rubroespecie.usrasig = asis.persona.usuario
                                            rubroespecie.fechaasigna = datetime.now()
                                            rubroespecie.departamento= asis.departamento
                                            rubroespecie.save()

                                            asis.cantidad =asis.cantidad +1


                                            asis.save()
                                            listaespecies.append(asis.persona.emailinst)
                                            break
                            if listaespecies:
                                try:
                                     hoy = datetime.now().today()
                                     contenido = "  Tramites Asignados"
                                     descripcion = "Ud. tiene tramites por atender"
                                     send_html_mail(contenido,
                                        "emails/notificacion_tramites_adm.html", {'fecha': hoy,'contenido': contenido,'descripcion':descripcion,'opcion':'1'},listaespecies)
                                except Exception as e:
                                    print((e))
                                    pass
                        if solicitud.solicitud.libre:
                            return HttpResponseRedirect("/solicitudonline?action=verlibres")
                        return HttpResponseRedirect("/solicitudonline")
                    except Exception as e:
                        return HttpResponseRedirect("/solicitudonline?error="+str(e))


            else:
                persona = data['persona']
                if Inscripcion.objects.filter(persona=persona).exists():
                    inscripcion = Inscripcion.objects.get(persona=persona)
                    #Comprobar que no tenga deudas para que no pueda usar el sistema
                    # if VALIDAR_ENTRADA_SISTEMA_CON_DEUDA and inscripcion.tiene_deuda():
                    # #     locale.setlocale(locale.LC_ALL,"")
                    #     if inscripcion.matriculado() and not VALIDA_DEUDA_EXAM_ASIST:
                    #         data['srn']=1
                    #         tipoespecie = TipoEspecieValorada.objects.get(id=ID_TIPO_ESPECIE_REG_NOTA)
                    #         materiaid = RubroEspecieValorada.objects.filter(tipoespecie=tipoespecie,rubro__inscripcion=inscripcion,
                    #                                                        aplicada=False).distinct('materia').values('materia')
                    #
                    #         data['materias'] = inscripcion.matricula().materia_asignada().exclude(id__in=materiaid)
                    #         return render(request ,"solicitudonline/solicitudonline.html" ,  data)
                    #     return HttpResponseRedirect("/")

                    #Comprobar que el alumno este matriculado
                    # if not inscripcion.matriculado():
                    #     return HttpResponseRedirect("/?info=Ud. aun no ha sido matriculado")
                    matricula=None
                    if  inscripcion.matricula():
                        matricula = inscripcion.matricula()
                        data['matricula']=matricula
                    data['inscripcion']=inscripcion
                    data['idtestdese'] = ID_TEST_ENCUESTA_DESERCION
                    if 'generar' in request.GET:
                        solicitud= SolicitudOnline.objects.get(pk=request.GET['id'])
                        if 'idtipo' in request.GET:
                            if  inscripcion.matricula():
                                if matricula.nivel.nivelmalla.orden >= NIVELMALLA_INICIO_PRACTICA and solicitud.id == ID_SOLIC__ONLINE:
                                    data['idtipoaplaz'] = request.GET['idtipo']
                                else:
                                     return  HttpResponseRedirect('/?info=No esta en el nivel para realizar estas solicitudes')
                            else:
                                 return  HttpResponseRedirect('/?info=No esta en el nivel para realizar estas solicitudes')
                        data['solicitud'] = solicitud
                        if not solicitud.libre :
                            data['libre'] = False
                            if not ((matricula.nivel.paralelo[0:1] == 'E' or matricula.nivel.paralelo[0:1] == 'P' or matricula.nivel.paralelo[0:1] == 'G') and matricula.nivel.nivelmalla.id ==  4)\
                            and not  ((matricula.nivel.paralelo[0:1] != 'E' or matricula.nivel.paralelo[0:1] != 'P' or matricula.nivel.paralelo[0:1] != 'G') and matricula.nivel.nivelmalla.id == 6) :
                                return  HttpResponseRedirect('/?info=No esta en el nivel para realizar estas solicitudes')
                            if SolicitudEstudiante.objects.filter(tipo__id=TIPO_EXAMEN_COMPLEXIVO,inscripcion=inscripcion,nuevotipo=None).exclude(solicitud=solicitud).exists():
                                return  HttpResponseRedirect('/?info=Su solicitud de Culminacion de Estudios no Aplica asignacion de tutor')
                            if SolicitudEstudiante.objects.filter(nuevotipo__id=TIPO_EXAMEN_COMPLEXIVO,inscripcion=inscripcion).exclude(solicitud=solicitud).exists():
                                    return  HttpResponseRedirect('/?info=Su solicitud de Culminacion de Estudios no Aplica asignacion de tutor')
                            if SolicitudEstudiante.objects.filter(nuevotipo__id=TIPO_EXAMEN_COMPLEXIVO,inscripcion=inscripcion).exclude(solicitud=solicitud).exists():
                                    return  HttpResponseRedirect('/?info=Su solicitud de Culminacion de Estudios no Aplica asignacion de tutor')

                            if not  SolicitudEstudiante.objects.filter(solicitud__id=CULMINACION_ESTUDIOS,inscripcion=inscripcion).exists() and solicitud.id != CULMINACION_ESTUDIOS:
                                return  HttpResponseRedirect('/?info=Debe primero realizar solicitud de culminacion de estudios')
                            if  SolicitudEstudiante.objects.filter(solicitud__id=CULMINACION_ESTUDIOS,inscripcion=inscripcion,aprobado=False).exists()  and solicitud.id != CULMINACION_ESTUDIOS:
                                if SolicitudEstudiante.objects.filter(solicitud__id=CULMINACION_ESTUDIOS,inscripcion=inscripcion,aprobado=False,nuevotipo=None).exists():
                                    return  HttpResponseRedirect('/?info=solicitud culminacion de estudios no esta aprobada ')
                        if not SolicitudEstudiante.objects.filter(inscripcion=inscripcion,solicitud=solicitud).exists() or solicitud.libre:
                            form =getattr(forms,solicitud.form,None)()
                            # if matricula:

                            form.for_tipo(inscripcion)
                            if solicitud.libre:
                                data['libre'] = True
                            if 'error' in request.GET:
                                data['error'] = request.GET['error']
                            data['form'] = form
                            data['soli']=0
                            if solicitud.valida_malla:
                                if HistoricoRecordAcademico.objects.filter( inscripcion=matricula.inscripcion).exists():
                                    c = 0
                                    mallainscripcion = matricula.inscripcion.malla_inscripcion()
                                    if not mallainscripcion:
                                        return  HttpResponseRedirect('/?info=No tiene una malla asociada')
                                    if len(AsignaturaMalla.objects.filter(malla=mallainscripcion.malla).exclude(nivelmalla=NIVEL_MALLA_CERO).exclude(asignatura__id__in=ASIGNATURA_EXAMEN_GRADO_CONDU).exclude(asignatura__nivelacion=True).distinct('asignatura').values('asignatura')) > len(HistoricoRecordAcademico.objects.filter( inscripcion=matricula.inscripcion).exclude(asignatura__id__in=ASIGNATURA_EXAMEN_GRADO_CONDU).exclude(asignatura__nivelacion=True).distinct('asignatura').values('asignatura')):
                                        return  HttpResponseRedirect('/?info=Malla Incompleta no Puede Realizar Solicitud ')
                                    a=AsignaturaMalla.objects.filter(malla__id=mallainscripcion.malla.id).exclude(nivelmalla__id=NIVEL_MALLA_CERO).exclude(asignatura__id__in=ASIGNATURA_EXAMEN_GRADO_CONDU).exclude(asignatura__nivelacion=True).values('asignatura')
                                    c = HistoricoRecordAcademico.objects.filter(asignatura__in=a, nota__gte=NOTA_PARA_APROBAR, asistencia__gte=ASIST_PARA_APROBAR,inscripcion=matricula.inscripcion).exclude(asignatura__id__in=ASIGNATURA_EXAMEN_GRADO_CONDU).exclude(asignatura__nivelacion=True).distinct('asignatura').values('asignatura')
                                    if a.count() > c.count():
                                        return  HttpResponseRedirect('/?info=Tiene Asignaturas Reprobadas, no Puede Realizar Solicitud')
                                else:
                                    return  HttpResponseRedirect('/?info=Malla Incompleta no Puede Realizar Solicitud ')
                            data['ESPECIE_JUSTIFICA_FALTA'] = ESPECIE_JUSTIFICA_FALTA
                            data['ESPECIE_JUSTIFICA_FALTA_AU'] = ESPECIE_JUSTIFICA_FALTA_AU
                            data['ID_TIPO_SOLICITUD']=ID_TIPO_SOLICITUD
                            data['TIPO_ESPECIE_RETIRO_MATRICULA']=TIPO_ESPECIE_RETIRO_MATRICULA

                            return render(request ,"solicitudonline/datos.html" ,  data)
                        elif SolicitudEstudiante.objects.filter(inscripcion=inscripcion,solicitud=solicitud,solicitado=False).exists():
                            solicitudest = SolicitudEstudiante.objects.filter(inscripcion=inscripcion,solicitud=solicitud)[:1].get()
                            # cul=SolicitudEstudiante.objects.filter(matricula=matricula,solicitud=solicitud)[:1].get()
                            initial = model_to_dict(solicitudest)
                            form = getattr(forms,solicitudest.solicitud.form,None)(initial=initial)
                            if solicitud.libre:
                                form.for_tipo(inscripcion)
                            else:
                                form.for_tipo(matricula.nivel.carrera)
                            data['form'] = form
                            data['soli']=solicitudest.id
                            if solicitud.libre:
                                data['libre'] = True
                            return render(request ,"solicitudonline/datos.html" ,  data)
                        else:
                            locale.setlocale(locale.LC_ALL,"")
                            solicitud=SolicitudEstudiante.objects.filter(inscripcion=inscripcion,solicitud=solicitud)[:1].get()
                            data['solicitud']=solicitud
                            if solicitud.fecha:
                                data['mes']=str(solicitud.fecha.strftime("%B")).capitalize()
                                data['anio']=solicitud.fecha.year
                                data['dia2']=solicitud.fecha.day
                            else:
                                data['dia']=str(datetime.now().date().strftime("%A")).capitalize()
                                data['mes']=str(datetime.now().date().strftime("%B")).capitalize()
                                data['anio']=datetime.now().date().year
                                data['dia2']=datetime.now().date().day

                            return render(request ,"solicitudonline/"+str(solicitud.solicitud.html)+".html" ,  data)


                    else :
                        if 'solicitud' in request.GET:
                            locale.setlocale(locale.LC_ALL,"")
                            solicitud=SolicitudEstudiante.objects.filter(id=request.GET['id'])[:1].get()
                            data['solicitud']=solicitud
                            # data['dia']=str(elimina_tildes(datetime.now().date().strftime("%A")).capitalize())
                            data['mes']=str(solicitud.fecha.strftime("%B")).capitalize()
                            data['anio']=solicitud.fecha.year
                            data['dia2']=solicitud.fecha.day
                            if 'cantidad' in request.GET:
                                data['cantidad'] = int(request.GET['cantidad'])
                            return render(request ,"solicitudonline/"+str(solicitud.solicitud.html)+".html" ,  data)


                    data['solicitudes'] = SolicitudOnline.objects.filter(activo=True).order_by('id')
                    # data['solicitudes'] = SolicitudOnline.objects.filter(activo=True,solicitudcarrera__carrera=inscripcion.grupo().carrera).order_by('id')
                    if 'error' in request.GET:
                        data['error']=request.GET['error']
                    return render(request ,"solicitudonline/solicitudonline.html" ,  data)
                else:
                    if 'tipos' in request.GET:
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
                            tipo = TipoCulminacionEstudio.objects.filter(nombre__icontains=search).order_by('nombre')
                            # else:
                            #     visitabiblioteca = VisitaBiblioteca.objects.filter(Q(persona__apellido1__icontains=ss[0]) & Q(persona__apellido2__icontains=ss[1])).order_by('persona__apellido1','persona__apellido2','persona__nombres')
                        else:
                             tipo = TipoCulminacionEstudio.objects.all().order_by('nombre')

                        paging = MiPaginador(tipo, 30)
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
                        data['tipo'] = page.object_list
                        data['fecha'] = datetime.now().date()
                        tipo = TipoCulminacionForm()
                        data['tipoform'] = tipo
                        return render(request ,"solicitudonline/tipo_culminacion.html" ,  data)
                    else:
                        if 'tiposol' in request.GET:
                            search = None
                            todos = None
                            tiposol = request.GET['tiposol']
                            data['solicitud'] = SolicitudOnline.objects.get(pk= request.GET['tiposol'])
                            solicitud= SolicitudOnline.objects.get(pk= request.GET['tiposol'])
                            data['DIAS_ESPECIE']=DIAS_ESPECIE
                            if 's' in request.GET:
                                search = request.GET['s']
                            if 't' in request.GET:
                                todos = request.GET['t']
                            if solicitud.libre:
                                # carreras = EspecieGrupo.objects.filter().values('carrera')
                                # especiecarrera = EspecieGrupo.objects.filter().values('tipoe')
                                # especielibre = EspecieGrupo.objects.filter().values('tipoe')
                                if search:
                                    ss = search.split(' ')
                                    while '' in ss:
                                        ss.remove('')
                                    try:
                                        if int(search):
                                            numero = int(search)
                                            solicitudes = SolicitudEstudiante.objects.filter(Q(rubro__rubroespecievalorada__serie=numero)).order_by('-fecha')
                                    except:
                                       if len(ss)==1:
                                            solicitudes = SolicitudEstudiante.objects.filter(Q(inscripcion__persona__nombres__icontains=search) | Q(inscripcion__persona__apellido1__icontains=search) | Q(inscripcion__persona__apellido2__icontains=search) | Q(inscripcion__persona__cedula__icontains=search)).order_by('inscripcion__persona__apellido1')
                                       else:
                                            solicitudes = SolicitudEstudiante.objects.filter(Q(inscripcion__persona__apellido1__icontains=ss[0]) & Q(inscripcion__persona__apellido2__icontains=ss[1])).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')

                                else:
                                     solicitudes = SolicitudEstudiante.objects.filter(solicitado=True,solicitud__id=tiposol).order_by('-fecha')
                                #
                                # solicitudes = solicitudes.filter(Q(solicitado=True,solicitud__id=tiposol,tipoe__id__in=especiecarrera,inscripcion__carrera__id__in=carreras)|Q(tipoe__id__in=especielibre,solicitado=True,solicitud__id=tiposol)).order_by('fecha')

                                if 'pendientes' in request.GET:
                                    data['pendientes']=1
                                    solicitudes = solicitudes.filter(solicitado=True,solicitud__id=tiposol).order_by('-fecha')

                                if 'atendidas' in request.GET:
                                    data['atendidas']=1
                                    solicitudes = solicitudes.filter(solicitado=True).exclude(fechares=None).order_by('-fecha')
                            else:
                                if search:
                                    ss = search.split(' ')
                                    while '' in ss:
                                        ss.remove('')
                                        solicitudes = SolicitudEstudiante.objects.filter(Q(inscripcion__persona__apellido1__icontains=ss[0]) & Q(inscripcion__persona__apellido2__icontains=ss[1]),solicitado=True).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')
                                    else:
                                        solicitudes = SolicitudEstudiante.objects.filter(Q(inscripcion__persona__nombres__icontains=search) | Q(inscripcion__persona__apellido1__icontains=search) | Q(inscripcion__persona__apellido2__icontains=search) | Q(inscripcion__persona__cedula__icontains=search),solicitado=True ).order_by('inscripcion__persona__apellido1')
                                else:
                                     solicitudes = SolicitudEstudiante.objects.filter(solicitado=True).order_by('-fecha')

                            paging = MiPaginador(solicitudes,30)
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
                            data['solicitudes'] = page.object_list
                            data['fecha'] = datetime.now().date()
                            tipo = RespuestaEspecieForm()
                            frmresol = ResolucionSolForm()
                            data['respform'] = tipo
                            data['reolform'] = frmresol
                            data['tipoculminacion'] = TipoCulminacionEstudio.objects.all()
                            data['VALIDAR_ENTRADA_SISTEMA_CON_DEUDA'] = VALIDAR_ENTRADA_SISTEMA_CON_DEUDA
                            data['ESPECIE_CAMBIO_PROGRAMACION'] = ESPECIE_CAMBIO_PROGRAMACION
                            data['ESPECIE_RETIRO_MATRICULA'] = ESPECIE_RETIRO_MATRICULA
                            data['ESPECIE_JUSTIFICA_FALTA'] = ESPECIE_JUSTIFICA_FALTA
                            data['ESPECIE_JUSTIFICA_FALTA_AU'] = ESPECIE_JUSTIFICA_FALTA_AU
                            if 'error' in request.GET:
                                data['error'] = request.GET['error']
                            return render(request ,"solicitudonline/solicitud.html" ,  data)
                        if 'versolicitud' in request.GET:
                            locale.setlocale(locale.LC_ALL,"")
                            solicitud=SolicitudEstudiante.objects.filter(id=request.GET['id'])[:1].get()
                            data['solicitud']=solicitud
                            # data['dia']=str(elimina_tildes(datetime.now().date().strftime("%A")).capitalize())
                            data['mes']=str(solicitud.fecha.strftime("%B")).capitalize()
                            data['anio']=solicitud.fecha.year
                            data['dia2']=solicitud.fecha.day
                            data['adm'] = 1
                            if 'tipo' in request.GET:
                                data['tipo'] = request.GET['tipo']

                            return render(request ,"solicitudonline/"+str(solicitud.solicitud.html)+".html" ,  data)
                        else:
                            data['solicitudes'] = SolicitudOnline.objects.filter(activo=True)
                            return render(request ,"solicitudonline/admsolicitud.html" ,  data)



    except Exception as ex:
        return HttpResponseRedirect("/")