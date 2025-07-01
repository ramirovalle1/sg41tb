from datetime import datetime, timedelta,date
import json
import os

from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Avg
from django.db.models.aggregates import Sum
from django.db import transaction
from django.db.models.query_utils import Q
from django.forms.models import model_to_dict
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template import RequestContext

from django.utils.encoding import force_str
from decorators import secure_module
from settings import MEDIA_ROOT, ID_TIPO_SOLICITUD, GRUPO_CAJEROS, EMAIL_ACTIVE, SISTEMAS_GROUP_ID, UTILIZA_GRUPOS_ALUMNOS, ASIST_PARA_APROBAR, EJE_PRACTICA, DEFAULT_PASSWORD, ASIGNATURA_INTRODUCCION
from sga.alu_malla import aprobadaAsignatura, horaspracticas
from sga.commonviews import ip_client_address, addUserData
from sga.forms import InscripcionForm, SolicitudSecretariaAlumnosForm, ExamenForm, EspecieUniversalForm
from sga.models import Inscripcion, Persona, Grupo, InscripcionGrupo, NivelMalla, \
    EjeFormativo, AsignaturaMalla, MatriculaTutor, Matricula, Rubro, MateriaAsignada, ParametroSeguimiento, \
    SeguimientoTutor, CabSeguimiento, DetSeguimiento, TipoSolicitudSecretariaDocente, SolicitudSecretariaDocente, \
    SolicitudesGrupo, ModuloGrupo, CronogramaAlumno,NivelPeriodoEx, EvaluacionITB, TipoEspecieValorada, SolicitudOnline, SolicitudEstudiante, Coordinacion, \
    CoordinacionDepartamento, EspecieGrupo, AsistenteDepartamento, SesionCaja, HorarioAsistenteSolicitudes, \
    InscripcionPracticas, EstudianteVinculacion, AprobacionVinculacion, NivelTutor
from sga.tasks import gen_passwd, send_html_mail
from decimal import Decimal
from sga.reportes import elimina_tildes

def convertir_fecha(s):
    return datetime(int(s[6:10]), int(s[3:5]), int(s[0:2])).date()

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
# @secure_module
def view(request):
    hoy = datetime.today().date()
    # documentosestudiante = list()
    if request.method=='POST':
        action = request.POST['action']
        try:
            if action == 'verifica':
                result = {}
                try:
                    if ParametroSeguimiento.objects.filter(pk=request.POST['idp']).exists():
                        parametro =  ParametroSeguimiento.objects.filter(pk=request.POST['idp'])[:1].get()
                        if  int(request.POST['puntaje']) <= parametro.ptomax and int(request.POST['puntaje']) >= parametro.ptomin :
                            result['result'] = 'ok'
                            return HttpResponse(json.dumps(result), content_type="application/json")
                except Exception as e:
                    result['result'] = 'bad'
                return HttpResponse(json.dumps(result), content_type="application/json")

            elif action == 'addexamen':
                evaluacion = EvaluacionITB.objects.get(id=request.POST['evaluacionid'])
                f = ExamenForm(request.POST, request.FILES)
                if f.is_valid():
                    mensaje=''
                    if 'archivo' in request.FILES:
                        archivo = request.FILES['archivo']
                        if evaluacion.archiexamen:
                            mensaje = 'Editado'
                            if (MEDIA_ROOT + '/' + str(evaluacion.archiexamen)) and archivo:
                                os.remove(MEDIA_ROOT + '/' + str(evaluacion.archiexamen))
                        else:
                            mensaje = 'Adicionado'
                        evaluacion.archiexamen = archivo
                        evaluacion.save()

                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id=request.user.pk,
                            content_type_id=ContentType.objects.get_for_model(evaluacion).pk,
                            object_id=evaluacion.id,
                            object_repr=force_str(evaluacion),
                            action_flag=ADDITION,
                            change_message=mensaje + ' Examen (' + client_address + ')')

                        return HttpResponseRedirect('/alum_tutorias?action=notas&id='+str(evaluacion.materiaasignada.matricula.inscripcion.id)+"&mensaje=Archivo " + mensaje + " Correctamente")
                else:
                    return HttpResponseRedirect('/alum_tutorias?action=notas&id='+str(evaluacion.materiaasignada.matricula.inscripcion.id)+"&error=Error en el Formato del Archivo")
            elif action == 'eliminaseg':
                result = {}
                sid = transaction.savepoint()
                try:
                    if CabSeguimiento.objects.filter(pk=request.POST['idc']).exists:
                        cab = CabSeguimiento.objects.filter(pk=request.POST['idc'])[:1].get()
                        detalle = DetSeguimiento.objects.filter(cabseguimiento=cab)
                        # Obtain client ip address
                        client_address = ip_client_address(request)

                        # Log de Elimina Seguimiento
                        LogEntry.objects.log_action(
                            user_id=request.user.pk,
                            content_type_id=ContentType.objects.get_for_model(cab).pk,
                            object_id=cab.id,
                            object_repr=force_str(cab),
                            action_flag=DELETION,
                            change_message='Eliminado Seguimiento (' + client_address + ')')
                        detalle.delete()
                        seg = cab.seguimiento
                        cab.delete()
                        if not CabSeguimiento.objects.filter(seguimiento=seg).exists():
                            seg.delete()
                        result['result'] = 'ok'
                        transaction.savepoint_commit(sid)
                        return HttpResponse(json.dumps(result), content_type="application/json")
                except Exception as e:
                    result['result'] = 'bad'
                    transaction.savepoint_rollback(sid)
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}), content_type="application/json")

            elif action=='edit':
                try:

                    inscripcion = Inscripcion.objects.get(pk=request.POST['id'])
                    initial = model_to_dict(inscripcion)
                    initial.update(model_to_dict(inscripcion.persona))
                    f = InscripcionForm(request.POST, initial=initial)

                    try:
                        if f.is_valid():

                            if f.cleaned_data['estcolegio']:
                                inscripcion.estcolegio_id = f.cleaned_data['estcolegio_id']
                                inscripcion.save()

                            inscripcion.persona.nombres=f.cleaned_data['nombres']
                            inscripcion.persona.apellido1=f.cleaned_data['apellido1']
                            inscripcion.persona.apellido2=f.cleaned_data['apellido2']
                            if 'sectorresid' in f.cleaned_data :
                                inscripcion.persona.sectorresid=f.cleaned_data['sectorresid']
                            if 'parroquia' in f.cleaned_data:
                                inscripcion.persona.parroquia = f.cleaned_data['parroquia']

                            inscripcion.persona.direccion=f.cleaned_data['direccion']
                            inscripcion.persona.direccion2=f.cleaned_data['direccion2']
                            inscripcion.persona.num_direccion=f.cleaned_data['num_direccion']

                            inscripcion.persona.provinciaresid=f.cleaned_data['provinciaresid']
                            inscripcion.persona.cantonresid=f.cleaned_data['cantonresid']

                            inscripcion.persona.telefono=f.cleaned_data['telefono']
                            inscripcion.persona.telefono_conv=f.cleaned_data['telefono_conv']
                            inscripcion.persona.email=f.cleaned_data['email']
                            inscripcion.persona.email1=f.cleaned_data['email1']
                            inscripcion.persona.email2=f.cleaned_data['email2']
                            inscripcion.persona.sangre=f.cleaned_data['sangre']

                            inscripcion.persona.save()

                        #Obtain client ip address
                        client_address = ip_client_address(request)

                        # Log Editar Inscripcion
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(inscripcion).pk,
                            object_id       = inscripcion.id,
                            object_repr     = force_str(inscripcion),
                            action_flag     = CHANGE,
                            change_message  = 'Modificada Inscripcion (' + client_address + ')' )



                        if inscripcion.persona.cedula:
                            return HttpResponseRedirect("/alum_tutorias?s="+str(inscripcion.persona.cedula))
                        else:
                            return HttpResponseRedirect("/alum_tutorias?s="+str(inscripcion.persona.pasaporte))

                    except Exception as ex:
                        return HttpResponseRedirect("/alum_tutorias?action=edit&id="+str(inscripcion.id)+"&error="+str(ex))
                except Exception as e:
                    print(e)
                    return HttpResponseRedirect("/inscripciones?action=edit&id=" + request.POST['id'] + "&error=" + str(e))
            elif action == 'guardar':
                result = {}
                sid = transaction.savepoint()
                try:
                    data = json.loads(request.POST['data'])
                    # inscripcion = Inscripcion.objects.filter(pk=int(request.POST['inscripcion']))[:1].get()
                    matricula = Matricula.objects.get(pk=request.POST['matricula'])
                    if not matricula.nivel.cerrado and not matricula.liberada:
                        if AsistenteDepartamento.objects.filter(persona__usuario=request.user).exists():
                            tutor = AsistenteDepartamento.objects.filter(persona__usuario=request.user)[:1].get()
                            niveltutor = NivelTutor.objects.get(nivel=matricula.nivel, tutor=tutor)
                            if SeguimientoTutor.objects.filter(matricula=matricula,niveltutor__tutor=niveltutor).exists():
                                seguimiento = SeguimientoTutor.objects.filter(matricula=matricula,niveltutor=niveltutor)[:1].get()
                            else:
                                seguimiento = SeguimientoTutor(matricula=matricula,
                                                               niveltutor = niveltutor)
                                seguimiento.save()

                            cabseguimiento = CabSeguimiento(seguimiento=seguimiento,
                                                            fecha = datetime.now().date(),
                                                            observacion=request.POST['obs'])
                            cabseguimiento.save()
                            for d in data['datos']:
                                parametro = ParametroSeguimiento.objects.get(pk=d['id'])
                                detalle = DetSeguimiento(cabseguimiento=cabseguimiento,
                                                         parametro=parametro,
                                                         puntaje=int(d['puntaje']))

                                detalle.save()
                            result['result'] = 'ok'
                            transaction.savepoint_commit(sid)
                            # Obtain client ip address
                            client_address = ip_client_address(request)

                            # Log de ADICIONAR PROFESOR
                            LogEntry.objects.log_action(
                                user_id=request.user.pk,
                                content_type_id=ContentType.objects.get_for_model(cabseguimiento).pk,
                                object_id=cabseguimiento.id,
                                object_repr=force_str(cabseguimiento),
                                action_flag=ADDITION,
                                change_message='Adicionado Seguimiento (' + client_address + ')')
                            return HttpResponse(json.dumps(result), content_type="application/json")
                except Exception as e:
                    result['result'] = 'bad'
                    transaction.savepoint_rollback(sid)
                    return HttpResponse(json.dumps(result), content_type="application/json")

            elif action == 'subirarchivo':
                result = {}
                try:
                    inscripcion = Inscripcion.objects.get(id=request.POST['id'])
                    if 'file' in request.FILES:
                        print('FILE')
                        if os.path.exists(MEDIA_ROOT + '/' + str(inscripcion.titulo)) and str(inscripcion.titulo):
                            os.remove(MEDIA_ROOT + '/' + str(inscripcion.titulo))
                        inscripcion.titulo = request.FILES['file']

                    if 'fileced' in request.FILES:
                        print('FILECED')
                        if os.path.exists(MEDIA_ROOT + '/' + str(inscripcion.archcedula)) and str(
                                inscripcion.archcedula):
                            os.remove(MEDIA_ROOT + '/' + str(inscripcion.archcedula))
                        inscripcion.archcedula = request.FILES['fileced']

                    if 'filepasa' in request.FILES:
                        print('FILEPASA')
                        if os.path.exists(MEDIA_ROOT + '/' + str(inscripcion.archpasaport)) and str(
                                inscripcion.archpasaport):
                            os.remove(MEDIA_ROOT + '/' + str(inscripcion.archpasaport))
                        inscripcion.archpasaport = request.FILES['filepasa']

                    if 'filevota' in request.FILES:
                        print('FILEVOTA')
                        if os.path.exists(MEDIA_ROOT + '/' + str(inscripcion.votacion)) and str(
                                inscripcion.archpasaport):
                            os.remove(MEDIA_ROOT + '/' + str(inscripcion.votacion))
                        inscripcion.votacion = request.FILES['filevota']

                    if 'filefot' in request.FILES:
                        print('FILEFOTO')
                        if os.path.exists(MEDIA_ROOT + '/' + str(inscripcion.foto)) and str(inscripcion.foto):
                            os.remove(MEDIA_ROOT + '/' + str(inscripcion.foto))
                        inscripcion.foto = request.FILES['filefot']
                    inscripcion.save()
                    result['result'] = 'ok'
                    return HttpResponse(json.dumps(result), content_type="application/json")
                except Exception as e:
                    result['result'] = str(e)
                    return HttpResponse(json.dumps(result), content_type="application/json")

            elif action == 'addtramite':
                try:
                    print(request.POST)
                    inscripcion = Inscripcion.objects.filter(pk=request.POST['idinscrip'])[:1].get()
                    solicitud = SolicitudOnline.objects.filter(pk=3)[:1].get()

                    f = EspecieUniversalForm(request.POST)

                    if not 'comprobante' in request.FILES or len(request.POST['observacion']) == 0:
                        return HttpResponseRedirect("/tutorias?action=ingresacomprobante&idins=" + str(inscripcion.id) + "&error=TODOS LOS CAMPOS SON OBLIGATORIOS")
                    if len(request.POST['observacion']) > 500:
                        return HttpResponseRedirect("/alum_tutorias?action=ingresacomprobante&idins=" + str( inscripcion.id) + "&error=LA OBSERVACION EXCEDE DE LOS CARATERES PERMITIDOS(500)")
                    solicitudest = SolicitudEstudiante(solicitud=solicitud,
                                                       inscripcion=inscripcion,
                                                       fecha=datetime.now(),
                                                       observacion=(request.POST['observacion']),
                                                       tipoe_id=ID_TIPO_SOLICITUD)
                    solicitudest.save()

                    solicitudsec = SolicitudSecretariaDocente(persona=inscripcion.persona,
                                                              solicitudestudiante=solicitudest,
                                                              tipo=solicitudest.tipoe.tiposolicitud,
                                                              descripcion=solicitudest.observacion,
                                                              fecha=datetime.now(),
                                                              hora=datetime.now().time(),
                                                              cerrada=False)
                    solicitudsec.save()
                    adjunto = False
                    solicitudest.solicitado = True
                    solicitudest.save()
                    if 'comprobante' in request.FILES:
                        solicitudsec.comprobante = request.FILES['comprobante']
                        solicitudsec.save()
                        adjunto = True
                    listasolicitudes = []
                    coordinacion = Coordinacion.objects.filter(
                        carrera=solicitudsec.solicitudestudiante.inscripcion.carrera)[:1].get()
                    for cdp in CoordinacionDepartamento.objects.filter(coordinacion=coordinacion):
                        if EspecieGrupo.objects.filter(departamento=cdp.departamento,tipoe=solicitudsec.solicitudestudiante.tipoe).exists():
                            asistentes = None
                            if cdp.departamento.id == GRUPO_CAJEROS:
                                cajeros = SesionCaja.objects.filter(abierta=True).values('caja__persona')
                                if HorarioAsistenteSolicitudes.objects.filter(fecha=datetime.now().date(),
                                                                              horainicio__lte=datetime.now().time(),
                                                                              horafin__gte=datetime.now().time()).exists():
                                    horarioasis = HorarioAsistenteSolicitudes.objects.filter(
                                        fecha=datetime.now().date(), horainicio__lte=datetime.now().time(),
                                        horafin__gte=datetime.now().time()).values('usuario')
                                    asistentes = AsistenteDepartamento.objects.filter(departamento=cdp.departamento,
                                                                                      persona__usuario__id__in=horarioasis,
                                                                                      persona__id__in=cajeros).exclude(
                                        puedereasignar=True).order_by('cantidadsol')

                            if asistentes:
                                for asis in asistentes:
                                    asis.cantidadsol = asis.cantidadsol + 1
                                    solicitudsec.usuario = asis.persona.usuario
                                    solicitudsec.personaasignada = asis.persona
                                    solicitudsec.asignado = True
                                    solicitudsec.fechaasignacion = datetime.now()
                                    solicitudsec.usuarioasigna = asis.persona.usuario
                                    solicitudsec.save()
                                    asis.save()
                                    listasolicitudes.append(asis.persona.emailinst)
                                    break
                    if listasolicitudes:
                        try:
                            hoy = datetime.now().today()
                            contenido = "  Solicitudes Asignadas"
                            descripcion = "Ud. tiene solicitudes por atender"
                            send_html_mail(contenido,"emails/notificacion_solicitud_adm.html",{'fecha': hoy, 'contenido': contenido, 'descripcion': descripcion,'opcion': '1'}, listasolicitudes)
                        except Exception as e:
                            print(e)
                            pass
                    if EMAIL_ACTIVE:
                        # f.instance.mail_subject_nuevo()
                        # OCastillo 17-05-2019
                        gruposexcluidos = [SISTEMAS_GROUP_ID]
                        lista = ''
                        persona = Persona.objects.filter(usuario=request.user)[:1].get()
                        lista = str(persona.email)
                        hoy = datetime.now().today()
                        contenido = "Nueva Solicitud"
                        descripcion = "Estimado/a estudiante. Su solicitud ha sido recibida. Sera asignada al Departamento correspondiente. Puede ver el estado de la misma en el Sistema."
                        send_html_mail(contenido,"emails/nuevasolicitud.html",{'d': solicitudsec, 'fecha': hoy, 'contenido': contenido,'descripcion': descripcion, 'opcion': '1'}, lista.split(','))

                        # traigo el correo del grupo a quien le corresponde el tipo de solicitud
                        if SolicitudesGrupo.objects.filter(tiposolic=solicitudsec.tipo,
                                                           carrera=inscripcion.carrera.id).exists():
                            grupo_solicitud = SolicitudesGrupo.objects.filter(tiposolic=solicitudsec.tipo,
                                                                              carrera=inscripcion.carrera.id).values(
                                'grupo')
                            if ModuloGrupo.objects.filter(grupos__in=grupo_solicitud).exists():
                                correo_solicitud = []
                                for correo_grupo in ModuloGrupo.objects.filter(grupos__in=grupo_solicitud):
                                    correo_solicitud.append(correo_grupo.correo)
                                    if lista:
                                        lista = lista + ',' + correo_grupo.correo
                                    else:
                                        lista = correo_grupo.correo
                        else:
                            # Para el caso de una solicitud tipo general para todas las carreras
                            if SolicitudesGrupo.objects.filter(tiposolic=solicitudsec.tipo,
                                                               todas_carreras=True).exists():
                                if solicitudsec.tipo.sistema == True:
                                    grupo_solicitud = SolicitudesGrupo.objects.filter(tiposolic=solicitudsec.tipo,
                                                                                      todas_carreras=True).values(
                                        'grupo')
                                else:
                                    grupo_solicitud = SolicitudesGrupo.objects.filter(tiposolic=solicitudsec.tipo,
                                                                                      todas_carreras=True).exclude(
                                        grupo__id__in=gruposexcluidos).values('grupo')
                                if ModuloGrupo.objects.filter(grupos__in=grupo_solicitud).exists():
                                    correo_solicitud = []
                                    for correo_grupo in ModuloGrupo.objects.filter(grupos__in=grupo_solicitud):
                                        correo_solicitud.append(correo_grupo.correo)
                                        if lista:
                                            lista = lista + ',' + correo_grupo.correo
                                        else:
                                            lista = correo_grupo.correo

                        hoy = datetime.now().today()
                        contenido = "Nueva Solicitud"
                        # descripcion = solicitud.descripcion
                        # if adjunto:
                        #      descripcion = descripcion +   " Archivo adjunto"
                        #     # descripcion = solicitud.descripcion +  "Estudiante ha realizado solicitud. Revisar el detalle de la misma en el Modulo Solicitudes de Alumnos. Archivo adjunto"
                        send_html_mail(contenido,
                                       "emails/nuevasolicitud.html",
                                       {'d': solicitudsec, 'fecha': hoy, 'contenido': contenido, 'adjunto': adjunto,
                                        'opcion': '2'}, lista.split(','))
                        if 'comprobante' in request.FILES:
                            pass

                        return HttpResponseRedirect("/alum_tutorias?info=SE AGREGO CORRECTAMENTE")
                    else:
                        return HttpResponseRedirect("/alum_tutorias?action=ingresacomprobante&idins=" + str(inscripcion.id))
                    # else:
                    #     # print(f)
                    #     return HttpResponseRedirect("/inscripciones?action=ingresacomprobante&idins="+str(inscripcion.id)+"&error=TODOS LOS CAMPOS SON OBLIGATORIOS")
                except Exception as e:
                    print('ERROR: '+str(e))
                    return HttpResponseRedirect("/alum_tutorias?action=ingresacomprobante&idins=" + str(inscripcion.id) + "&error=" + str(e))

            elif action=='solicitar':
                adjunto=False
                try:
                    f = SolicitudSecretariaAlumnosForm(request.POST,request.FILES)
                    if f.is_valid():
                        inscripcion = Inscripcion.objects.get(id=request.POST['idinscrip'])
                        if not 'pr' in request.POST:
                            solicitud = SolicitudSecretariaDocente(persona=inscripcion.persona,
                                                                   tipo=f.cleaned_data['tipo'],
                                                                   descripcion=f.cleaned_data['descripcion'],
                                                                   fecha = datetime.now(),
                                                                   hora = datetime.now().time(),
                                                                   cerrada = False)
                            solicitud.save()
                        else:
                            tipoespecie = TipoSolicitudSecretariaDocente.objects.get(pk=ID_TIPO_SOLICITUD)
                            solicitud = SolicitudSecretariaDocente(persona=inscripcion.persona,
                                                                   tipo=tipoespecie,
                                                                   descripcion=f.cleaned_data['descripcion'],
                                                                   fecha = datetime.now(),
                                                                   hora = datetime.now().time(),
                                                                   cerrada = False)
                            solicitud.save()

                        opcion='Alumno'

                        if 'comprobante' in request.FILES:
                            solicitud.comprobante= request.FILES['comprobante']
                            solicitud.save()
                            adjunto=True

                        if EMAIL_ACTIVE:
                            # f.instance.mail_subject_nuevo()
                            lista=''
                            # OCastillo 17-05-2019
                            gruposexcluidos = [SISTEMAS_GROUP_ID]
                            lista = ''

                            lista = str(solicitud.persona.email)
                            hoy = datetime.now().today()
                            contenido = "Nueva Solicitud"
                            descripcion = "Estimado/a estudiante. Su solicitud ha sido recibida. Sera asignada al Departamento correspondiente. Puede ver el estado de la misma en el Sistema."
                            send_html_mail(contenido,
                                "emails/nuevasolicitud.html", {'d': solicitud, 'fecha': hoy,'contenido': contenido,'descripcion':descripcion,'opcion':'1'},lista.split(','))

                            #traigo el correo del grupo a quien le corresponde el tipo de solicitud
                            if SolicitudesGrupo.objects.filter(tiposolic=solicitud.tipo,carrera=inscripcion.carrera.id).exists():
                                grupo_solicitud=SolicitudesGrupo.objects.filter(tiposolic=solicitud.tipo,carrera=inscripcion.carrera.id).values('grupo')
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
                                if SolicitudesGrupo.objects.filter(tiposolic=solicitud.tipo,todas_carreras=True).exists():
                                    grupo_solicitud=SolicitudesGrupo.objects.filter(tiposolic=solicitud.tipo,todas_carreras=True).exclude(grupo__id__in=gruposexcluidos).values('grupo')
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

                            send_html_mail(contenido,"emails/nuevasolicitud.html", {'d': solicitud, 'fecha': hoy,'contenido': contenido,'adjunto':adjunto,'opcion':'2'},lista.split(','))
                            return HttpResponseRedirect("/alum_tutorias")
                    else:
                        if not 'pr' in request.POST:
                            return HttpResponseRedirect("/alum_tutorias")
                        else:
                            return HttpResponseRedirect("/alum_tutorias?error= Error en el formulario fichero o tamano no permitido")
                except Exception as e:
                    print(str(e))
                    return HttpResponseRedirect("/alum_tutorias?error= Error ingrese nuevamente")

            elif action == 'actualizar':
                result = {}
                try:
                    niveltutor = NivelTutor.objects.filter(activo=True, nivel__cerrado=False)
                    contador = 0
                    for n in niveltutor:
                        matriculas = Matricula.objects.filter(nivel=n.nivel)
                        for i in matriculas:
                            if not MatriculaTutor.objects.filter(niveltutor=n, matricula=i).exists():
                                matricula_tutor = MatriculaTutor(niveltutor=n, matricula=i, activo=True)
                                matricula_tutor.save()
                                contador = contador+1

                    result['result']  = "Se agregaron "+str(contador)+" inscripciones al modulo"
                    return HttpResponse(json.dumps(result), content_type="application/json")
                except Exception as e:
                    result['result']  = str(e)
                    return HttpResponse(json.dumps(result), content_type="application/json")

        except Exception as e:
            return HttpResponseRedirect("/?info="+str(e))


    else:
        data = {'title': 'Listado de Tutoriados'}
        addUserData(request,data)
        try:
            if 'action' in request.GET:
                action = request.GET['action']
                if action=='activation':
                    pass
                    # d.activo = not d.activo
                    # d.save()

                if action == 'verdatos':
                    try:
                        data['bandera'] = 0
                        matricula = Matricula.objects.filter(pk=request.GET['id'])[:1].get()
                        data['estudiant'] = matricula.inscripcion.id
                        data['inscripcion'] = matricula.inscripcion
                        data['personal'] = matricula.inscripcion.persona
                        if not matricula.nivel.cerrado:
                            data['materiasignada'] = MateriaAsignada.objects.filter(matricula=matricula,cerrado=False).order_by('materia__inicio')
                            data['matricula'] = matricula
                            data['num'] = data['materiasignada'].count()

                        rubros = Rubro.objects.filter(inscripcion=matricula.inscripcion).order_by('cancelado', 'fechavence')
                        data['rubros'] = rubros
                        return render(request ,"tutorias/registroestudiante.html" ,  data)
                    except Exception as ex:
                        print(ex)

                elif action == 'datos':
                    inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                    initial = model_to_dict(inscripcion)
                    initial.update(model_to_dict(inscripcion.persona))

                    if UTILIZA_GRUPOS_ALUMNOS and inscripcion.inscripciongrupo_set.exists():
                        initial.update({'grupo': inscripcion.grupo})
                    data['grupos_abiertos'] = Grupo.objects.all()
                    data['utiliza_grupos_alumnos'] = UTILIZA_GRUPOS_ALUMNOS

                    insf = InscripcionForm(initial=initial)

                    data['form'] = insf
                    data['inscripcion'] = inscripcion
                    data['matriculado'] = inscripcion.matriculado()
                    return render(request ,"tutorias/datos.html" ,  data)

                elif action == 'addseguimiento':
                    try:
                        data['title'] = 'Seguimiento'
                        matricula = Matricula.objects.get(pk=request.GET['id'])
                        if MatriculaTutor.objects.filter(matricula=matricula, activo=True).exists():
                            tutor = MatriculaTutor.objects.filter(matricula=matricula, activo=True)[:1].get()
                            if AsistenteDepartamento.objects.filter(persona__usuario=request.user).exists():
                                asistente = AsistenteDepartamento.objects.filter(persona__usuario=request.user)[:1].get()
                                if asistente != tutor.niveltutor.tutor:
                                    return HttpResponseRedirect("/alum_tutorias")
                                parametros = ParametroSeguimiento.objects.filter(activo=True).order_by('descripcion')
                                data['parametros'] = parametros
                                data['matricula'] = matricula
                                data['tutor'] = asistente
                                data['hoy'] = datetime.now().date()
                                return render(request ,"tutorias/seguimiento.html" ,  data)
                        return HttpResponseRedirect("/alum_tutorias")
                    except Exception as ex:
                        print("addseguimiento: "+str(ex))

                elif action == 'alumalla':
                    try:
                        data['title'] = 'Malla del Alumno'
                        inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                        inscripcionmalla = inscripcion.malla_inscripcion()
                        # Comprobar que exista la malla en la carrera de la inscripcion
                        if not inscripcionmalla:
                            return HttpResponseRedirect("/?info=Este estudiante no tiene ninguna malla asociada")
                        malla = inscripcionmalla.malla

                        data['inscripcion'] = inscripcion
                        data['inscripcion_malla'] = inscripcionmalla
                        data['malla'] = malla

                        data['nivelesdemallas'] = NivelMalla.objects.all().order_by('orden')
                        data['ejesformativos'] = EjeFormativo.objects.all().order_by('nombre')
                        data['asignaturasmallas'] = [(x, aprobadaAsignatura(x, inscripcion), horaspracticas(x, inscripcion))
                                                     for x in AsignaturaMalla.objects.filter(malla=malla)]
                        resumenNiveles = [{'id': x.id, 'horas': x.total_horas(malla), 'creditos': x.total_creditos(malla)}
                                          for x in NivelMalla.objects.all().order_by('orden')]
                        data['resumenes'] = resumenNiveles
                        data['title'] = "Ver Malla Curricular : " + malla.carrera.nombre
                        data['ASIST_PARA_APROBAR'] = ASIST_PARA_APROBAR
                        if InscripcionPracticas.objects.filter(inscripcion=inscripcion).exists():
                            practicas = \
                            InscripcionPracticas.objects.filter(inscripcion=inscripcion).aggregate(Sum('horas'))[
                                'horas__sum']
                            data['practicas'] = practicas
                        if EstudianteVinculacion.objects.filter(inscripcion=inscripcion).exists():
                            data['vinculacion'] = EstudianteVinculacion.objects.filter(inscripcion=inscripcion)
                            # OCastillo 15-oct-2019 presentar las horas de vinculacion asi no esten terminadas
                            if AprobacionVinculacion.objects.filter(inscripcion=inscripcion).exists():
                                vinculacion = \
                                EstudianteVinculacion.objects.filter(inscripcion=inscripcion).aggregate(Sum('horas'))['horas__sum']
                                data['tohorasvin'] = vinculacion
                        data['EJE_PRACTICA'] = EJE_PRACTICA
                        return render(request ,"tutorias/mallabs.html" ,  data)
                    except Exception as ex:
                        print(ex)

                elif action == 'verseguimiento':
                    data['title'] = 'Registro de Seguimiento'
                    matricula = Matricula.objects.get(pk=request.GET['id'])
                    inscripcion = matricula.inscripcion
                    if 'n' in request.GET:
                        nivel = NivelMalla.objects.get(id=request.GET['n'])
                        data['nivel']=nivel
                        data['nivelid']=nivel.id
                        seguimiento = SeguimientoTutor.objects.filter(matricula__nivel__nivelmalla=nivel)
                    else:
                        seguimiento = SeguimientoTutor.objects.filter(matricula__inscripcion = inscripcion)
                    data['matricula'] = matricula
                    data['seguimiento'] = seguimiento
                    data['parametros'] =  ParametroSeguimiento.objects.filter(activo=True).order_by('descripcion')
                    data['niveles'] = NivelMalla.objects.all().order_by('orden')
                    return render(request ,"tutorias/registroseguimiento.html" ,  data)

                elif action=='verarchivotutor':
                    try:
                        data = {}
                        data['title'] = 'Archivo Tutor'
                        data['inscripcion'] = Inscripcion.objects.filter(id=request.GET['id'])[:1].get()
                        return render(request ,"inscripciones/verarchivo.html" ,  data)
                    except Exception as ex:
                        print('error -'+str(ex))
                elif action == 'resetear':
                    data['title'] = 'Resetear Clave del Usuario'
                    inscripcion = Inscripcion.objects.get(pk=int(request.GET['id']))
                    user = inscripcion.persona.usuario
                    user.set_password(DEFAULT_PASSWORD)
                    user.save()
                    if inscripcion.persona.cedula:
                        return HttpResponseRedirect("/cons_inscripciones?s=" + str(inscripcion.persona.cedula))
                    else:
                        return HttpResponseRedirect("/cons_inscripciones?s=" + str(inscripcion.persona.pasaporte))

                elif action == 'notas':
                    data['title'] = 'Notas del Alumno'
                    matricula = Matricula.objects.get(id=request.GET['id'])
                    if not matricula.nivel.cerrado and not matricula.liberada:
                        if 'error' in request.GET:
                            data['error'] = request.GET['error']

                        if 'mensaje' in request.GET:
                            data['mensaje'] = request.GET['mensaje']
                        materiasAsignadas = matricula.materiaasignada_set.all().order_by('materia__asignatura__nombre')
                        data['materiasasignadas'] = materiasAsignadas
                        data['matricula'] = matricula
                        data['form']  = ExamenForm()
                        return render(request ,"tutorias/materias.html" ,  data)
                elif action == 'horario':
                    data['title'] = 'Horario de Examen'
                    inscripcion = Inscripcion.objects.filter(id=request.GET['id'])[:1].get()
                    fechasid = []
                    fechasidrec = []
                    fechas = []
                    fechasrec = []
                    materias = []
                    materiasrec = []
                    data['inscripcion']=inscripcion
                    if inscripcion.matricula():
                        matricula= inscripcion.matricula()
                        if NivelPeriodoEx.objects.filter(nivel=matricula.nivel).exists():
                            if CronogramaAlumno.objects.filter(matricula=matricula):
                                cronogramaexamen = CronogramaAlumno.objects.filter(matricula=matricula,recuperacion=False)
                                cronogramarecuperacion = CronogramaAlumno.objects.filter(matricula=matricula,recuperacion=True)
                                data['cronogramaexamen'] = cronogramaexamen
                                data['cronogramarecuperacion'] = cronogramarecuperacion
                                data['sede'] = cronogramaexamen[:1].get().cronogramaexamen.provincia
                                materias = cronogramaexamen.values('cronogramaexamen__materia')
                                materiasrec = cronogramarecuperacion.values('cronogramaexamen__materia')
                            pendientes = matricula.materia_asignada().exclude(materia__id__in=materias).exclude(
                                materia__id__in=materiasrec).exclude(materia__asignatura__id=ASIGNATURA_INTRODUCCION)
                            if pendientes.count() >0:
                                data['pendientes']= pendientes
                    return render(request ,"tutorias/horario_examen.html" ,  data)
                elif action == 'ingresacomprobante':
                    if Inscripcion.objects.filter(id=request.GET['idins']).exists():
                        inscripcion = Inscripcion.objects.get(id=request.GET['idins'])
                        data['pr'] = 1
                        tipoespecie = TipoEspecieValorada.objects.get(id=ID_TIPO_SOLICITUD)
                        data['title'] = 'Nuevo Tramite'
                        data['form'] = EspecieUniversalForm(initial={'tipoe': tipoespecie})
                        data['urlaccion'] = 'tutorias'
                        data['inscripcion'] = inscripcion
                        if "error" in request.GET:
                            data['error'] = request.GET['error']
                        return render(request ,"tutorias/adicionartramite.html" ,  data)
                    return HttpResponseRedirect("/inscripciones?error=No existe la Inscripcion")

                elif action == 'vercomprobante':
                    data['inscripcion'] = Inscripcion.objects.get(id=request.GET['id'])
                    data['solicitudes'] = SolicitudSecretariaDocente.objects.filter(persona=data['inscripcion'].persona,solicitudestudiante__tipoe__id=ID_TIPO_SOLICITUD).exclude(
                        solicitudestudiante=None)
                    return render(request ,"tutorias/vercomprobante.html" ,  data)
            else:
                search = None
                todos = None
                activos = None
                inactivos = None
                gruposc = None
                band=0
                inscrip=[]
                matric = ''
                if AsistenteDepartamento.objects.filter(persona__usuario=request.user).exists():
                    asistente = AsistenteDepartamento.objects.filter(persona__usuario=request.user)[:1].get()
                    data['asistente'] = asistente
                    if MatriculaTutor.objects.filter(niveltutor__tutor=asistente,activo=True).exists():
                        matric = MatriculaTutor.objects.filter(niveltutor__tutor=asistente,activo=True).values('matricula')
                else:
                    if 'tid' in request.GET:
                        if AsistenteDepartamento.objects.filter(id=request.GET['tid']).exists():
                            asistente = AsistenteDepartamento.objects.filter(id=request.GET['tid'])[:1].get()
                            niveltutor = NivelTutor.objects.filter(tutor=asistente)
                            data['tutorid'] = asistente.id
                            data['tutor'] = asistente
                            if MatriculaTutor.objects.filter(niveltutor__tutor=asistente, activo=True).exists():
                                matric = MatriculaTutor.objects.filter(niveltutor__tutor=asistente, activo=True).values('matricula')

                    else:
                        if MatriculaTutor.objects.filter(activo=True).exists():
                            matric = MatriculaTutor.objects.filter(activo=True).values('matricula')


                if 's' in request.GET:
                    search = request.GET['s']
                    band=1
                if 'a' in request.GET:
                    activos = request.GET['a']
                if 'i' in request.GET:
                    inactivos = request.GET['i']
                if 't' in request.GET:
                    todos = request.GET['t']
                if search:
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')
                    if len(ss)==1:
                            matriculas = Matricula.objects.filter(Q(inscripcion__persona__nombres__icontains=search) | Q(inscripcion__persona__apellido1__icontains=search) | Q(inscripcion__persona__apellido2__icontains=search) | Q(inscripcion__persona__cedula__icontains=search) | Q(inscripcion__persona__pasaporte__icontains=search) | Q(inscripcion__identificador__icontains=search) | Q(inscripcion__inscripciongrupo__grupo__nombre__icontains=search) | Q(inscripcion__carrera__nombre__icontains=search) | Q(inscripcion__persona__usuario__username__icontains=search),inscripcion__persona__usuario__is_active=True,
                                                               id__in=matric).order_by('inscripcion__persona__apellido1')[:100]
                    else:
                            matriculas = Matricula.objects.filter(Q(inscripcion__persona__apellido1__icontains=ss[0]) & Q(inscripcion__persona__apellido2__icontains=ss[1]),inscripcion__persona__usuario__is_active=True,
                                                               id__in=matric).exclude(inscripcion__matricula__inscripcion=None).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')

                else:
                    matriculas = Matricula.objects.filter(inscripcion__persona__usuario__is_active=True,id__in=matric).exclude(inscripcion__matricula__inscripcion=None).order_by('inscripcion__persona__apellido1')

                paging = MiPaginador(matriculas, 30)
                p = 1
                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                        paging = MiPaginador(matriculas, 30)
                    page = paging.page(p)
                except Exception as ex:
                    page = paging.page(1)

                # Para atencion al cliente
                atiende=False
                idpresona=data['persona'].id


                data['paging'] = paging
                data['rangospaging'] = paging.rangos_paginado(p)
                data['page'] = page
                data['search'] = search if search else ""
                data['todos'] = todos if todos else ""
                data['matriculas'] = page.object_list
                data['total'] = matriculas.count()
                data['tutores']=AsistenteDepartamento.objects.filter(estutor=True)
                data['extra'] = 1
                if 'info' in request.GET:
                    data['info'] = request.GET['info']
                if 'ins' in request.GET:
                    data['ins'] = request.GET['ins']
                if "error" in request.GET:
                    data['error'] = request.GET['error']
                return render(request ,"tutorias/inscritos.html" ,  data)

        except Exception as e:
            print(e)
            return HttpResponseRedirect("/?info="+str(e))
