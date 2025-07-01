# coding=latin-1
from itertools import chain
import json
import random
import string
from datetime import datetime, timedelta, date
from django.contrib.admin.models import ADDITION, LogEntry
from django.contrib.auth import authenticate, logout, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models.aggregates import Sum
from django.db.models.query_utils import Q
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils.encoding import force_str
import psycopg2
import requests
from bib.models import Documento, ReferenciaWeb, ConsultaBiblioteca
from moodle.models import UserAuth
from settings import NOMBRE_INSTITUCION, MANAGER_PERIODO_GROUP_ID, ALUMNOS_GROUP_ID, ARCHIVO_TIPO_GENERAL, SEXO_FEMENINO, \
    SEXO_MASCULINO, UTILIZA_FICHA_MEDICA, RECTORADO_GROUP_ID, SISTEMAS_GROUP_ID, PROFESORES_GROUP_ID, UTILIZA_MODULO_BIBLIOTECA, \
    UTILIZA_MODULO_ENCUESTAS, MODELO_EVALUACION, EVALUACION_TES, SECRETARIAGENERAL_GROUP_ID, COORDINACION_ACADEMICA_GROUP_ID, \
    VALIDAR_ENTRADA_SISTEMA_CON_DEUDA, UTILIZA_FICHA_SOCIOECONOMICA, TIPO_PERIODO_PROPEDEUTICO, TIPO_PERIODO_REGULAR, TIENE_INGRESO_PADRES,\
    INSTITUCION, UNIVERSIDAD_CIU, EMAIL_ACTIVE,TEST_INGRESO_SISTEMA, FACTURACION_ELECTRONICA,AUTO_LOGOUT_DELAY,ATENCIONCLI, FICHA_MEDICA_ESTRICTA,\
    CARRERAS_ID_EXCLUIDAS_INEC, CAMPANA_REFERIDOS, UTILIZA_MENSAJE_INICIO, OPC_MENSAJE, DEFAULT_PASSWORD, EXAMEN_EXTERNO_INGRESO, TIPO_AULA, ENVIAR_CODIGO_CEL, \
    VALIDA_DEUDA_EXAM_ASIST, CAJA_ONLINE, PROMOCION_GYM, EXCLUYE_NIVEL, MEDIA_ROOT, ACTIVA_ADD_EDIT_AD, VALOR_COMISION_REFERIDO, HABILITA_APLICA_DESCUE, \
    INICIO_DIFERIR, FECHA_INCIO_DIFERIR, TIPO_NC_ANULACION, FIN_DIFERIR, LLENAR_CAMPOS, LISTA_TIPO_BECA, ASISTENTE_SECRETARIA, NIVELMALLA_INICIO_PRACTICA, \
    VALIDA_ESCENARIO_PRACTICA, SOLICITUD_APLAZAMIEN_PRACT_ID, ID_SOLIC__ONLINE, VENTANILLA_SECRETARIA,TICS_GROUP_ID, DATABASES, NEW_PASSWORD, \
    IP_SERVIDOR_API_DIRECTORY, BIBLIOTECA_PARAMETRIZADA, HABILITA_NOTIFICACIONES, DEBUG, VALIDA_PROV_CANTON_RESI
from sga.forms import PersonaForm, CambioClaveForm, CargarFotoForm, CargarCVForm, PeriodoForm, ReestablecerClaveForm, ActualizaDatosForm, EncuestaVacunasForm,\
     EntrevistaProfesionalizacionForm
from sga.funciones import is_mounted, mount_directory
from sga.models import Persona, ModuloGrupo, Periodo, FotoPersona, Noticia, CVPersona, Profesor, Inscripcion, Archivo,\
    TipoArchivo, TituloInstitucion, Pago, Factura, PagoCheque, PagoTarjeta, PagoTransferenciaDeposito, \
    PagoNotaCredito, Matricula, InscripcionEstadistica, Incidencia, Encuesta, PagoReciboCajaInstitucion,Coordinacion,Carrera,\
    EvaluacionTES, Modulo, PagoRetencion, ValeCaja,  TipoTest, InscripcionTipoTest, RespuestaTest, ClienteFactura,AtencionCliente, Actividad, \
    MESES_CHOICES, ReferidosInscripcion, DescuentoReferido, InscripcionDescuentoRef, Aula, ExamenExterno, VideoLogin, MensajesEnviado, \
    elimina_tildes, PagoPymentez, TipoTarjetaBanco, ProcesadorPagoTarjeta, Rubro, LugarRecaudacion, PromoGym, TipoIncidencia, \
    NotaCreditoInstitucion, ReciboCajaInstitucion, PagoNotaCreditoInstitucion, RubroCuota, RubroOtro, AsistenteSoporte, HorarioAsistente, Sede, \
    TipoAnuncio, AsistenteDepartamento, HorarioAsistenteSolicitudes, SolicitudBeca, RubroEspecieValorada, SolicitudSecretariaDocente, \
    TablaDescuentoBeca, HistorialGestionBeca, GestionTramite, SolicitudEstudiante, PerfilInscripcion, Raza, Sector, \
    HistorialGestionAyudaEconomica, ArchivoSoliciBeca, ParametrosPromocion,  EscenarioPractica,RequerimientoSoporte,RequerimSolucion, \
    EncuentasCarrera, EncuestaInscripcion, RespProgramdor,VacunasCovid,RegistroVacunas,InscripcionProfesionalizacion,RegistroAceptacionPagoenLineaConduccion,\
    RegistroAceptacionProtecciondeDatos, RubroSeguimiento, AsistAsuntoEstudiant,EvaluacionMateria, MateriaAsignada,EvaluacionAlumno,ProfesorMateria, PeriodoEvaluacion, EvaluacionDocentePeriodo, CoordinadorCarrera, EvaluacionCoordinadorDocente, EvaluacionDirectivoPeriodo, CoordinadorCarreraPeriodo, RolPerfilProfesor, InscripcionTestIngreso, EvaluacionDocente
from sga.tasks import gen_passwd, send_html_mail
from sga.notificaciones import notificaciones

def mail_aceptaterminos(contenido,asunto,user,correo,estudiante,op):
        tipo = TipoIncidencia.objects.get(pk=35)
        hoy = datetime.now().today()
        correo=  correo + ',' +str(tipo.correo)
        send_html_mail(str(asunto),"emails/aceptaterminos.html", {'fecha': hoy,"user":user,'contenido': contenido,'asunto':asunto,'estudiante':estudiante,'op':op},correo.split(","))


def process_request(request, tiempo):
    expira = False
    if not request.user.is_authenticated() :
    #No se puede desloggear un usuario no loggeado
        return
    try:
        # AUTO_LOGOUT_DELAY es una variable en minutos para desloguear al usuario
        if datetime.now() - request.session['last_touch'] > timedelta( 0, tiempo* 60, 0):
            logout(request)
            expira = True


    except KeyError:
        request.session['last_touch'] = datetime.now()
        expira = False
    return expira


def login_user(request):
    # exp=process_request(request,AUTO_LOGOUT_DELAY)
    # if exp:
    #     return render(request ,"sesioncaduca.html" ,  data)
    try:
        if request.method == 'POST':
            try:
                if 'g-recaptcha-response' in request.POST:
                    if request.POST['g-recaptcha-response'] == '':
                        return HttpResponseRedirect("/login?ret="+request.POST['ret']+"&capt=3")

                user = authenticate(username=(request.POST['user']).lower(), password=request.POST['pass'])
                if user is not None:
                    if not user.is_active:
                        return HttpResponseRedirect("/login?ret="+request.POST['ret']+"&error=3")
                    else:
                        if Persona.objects.filter(usuario=user).count()>0:
                            persona = Persona.objects.get(usuario=user)
                            login(request,user)
                            request.session['persona'] = persona
                            request.session['last_touch'] = datetime.now()
                            try:
                                usermoodle = UserAuth.objects.get(user=user)
                                if not usermoodle.check_password(request.POST['pass']) or usermoodle.check_data():
                                    if not usermoodle.check_password(request.POST['pass']):
                                        usermoodle.set_password(request.POST['pass'])
                                    usermoodle.save()
                            except ObjectDoesNotExist:
                                usermoodle = UserAuth(user=user)
                                usermoodle.set_data()
                                usermoodle.set_password(request.POST['pass'])
                                usermoodle.save()

                            if persona.reestablecer:
                                persona.reestablecer = False
                                persona.codigo = ''
                                persona.fecha_res = None
                                persona.save()
                            gruposexcluidos = [ALUMNOS_GROUP_ID,SISTEMAS_GROUP_ID]
                            try:
                                print('INGRESO A CONSULTA DE MEDIA MONTADO')
                                pathmount = '/var/lib/django/repoakad/media'
                                if is_mounted(pathmount):
                                    print('Media se encuentra montado')
                                else:
                                    response = mount_directory()


                            except Exception as e:
                                print("Excpcion en montar media "+str(e))
                            if Persona.objects.filter(usuario=user).exclude(usuario__groups__id__in=gruposexcluidos).exists():
                                client_address = ip_client_address(request)
                                LogEntry.objects.log_action(
                                    user_id         = request.user.pk,
                                    content_type_id = ContentType.objects.get_for_model(persona).pk,
                                    object_id       = persona.id,
                                    object_repr     = force_str(persona),
                                    action_flag     = ADDITION,
                                    change_message  = 'Inicio de session   (' + client_address + ')' )
                            return HttpResponseRedirect(request.POST['ret'])

                        else:
                            return HttpResponseRedirect("/login?ret="+request.POST['ret']+"&error=2")
                else:
                    return HttpResponseRedirect("/login?ret="+request.POST['ret']+"&error=1")
            except Exception as ex:
                return HttpResponseRedirect("/login")

        else:
            try:
                ret = '/'
                if 'ret' in request.GET:
                    ret = request.GET['ret']
                if INSTITUCION==UNIVERSIDAD_CIU:
                    numeroimagenes = 17
                else:
                    numeroimagenes = 6
                data = {"title": "Login",
                        "return_url": ret,
                        "background": random.randint(1,numeroimagenes),
                        "error": request.GET['error'] if 'error' in request.GET else "",
                        "errorp": request.GET['errorp'] if 'errorp' in request.GET else "",
                        "errorcon": request.GET['errorcon'] if 'errorcon' in request.GET else "",
                        "capt": request.GET['capt'] if 'capt' in request.GET else "",
                        "errorfac": request.GET['errorfac'] if 'errorfac' in request.GET else "",
                        "extracaja": request.GET['extracaja'] if 'extracaja' in request.GET else "",
                        "fac": request.GET['fac'] if 'fac' in request.GET else "",
                        "persona": request.GET['persona'] if 'persona' in request.GET else "",
                        "email": request.GET['email'] if 'email' in request.GET else ""}
                data['request'] = request
                if \
                    TituloInstitucion.objects.exists():
                    tituloinst = TituloInstitucion.objects.filter()[:1].get()
                    data['institucion'] = tituloinst.nombre
                    # if FACTURACION_ELECTRONICA:
                    #     data['mail'] = 'soporteitb@bolivariano.edu.ec'
                    # else:
                    if tituloinst.correo:
                        data['mail'] = tituloinst.correo
                    else:
                        data['mail'] = ''
                d = datetime.now()
                data['noticias'] = Noticia.objects.filter(desde__lte=d, hasta__gte=d).order_by('desde','-id')[0:5]
                data['currenttime'] = datetime.now()
                data['FACTURACION_ELECTRONICA'] = FACTURACION_ELECTRONICA
                data['ingreso_padres'] = TIENE_INGRESO_PADRES
                data['UTILIZA_MENSAJE_INICIO']= UTILIZA_MENSAJE_INICIO
                data['OPC_MENSAJE']= OPC_MENSAJE
                try:
                    # case server externo
                    client_address = request.META['HTTP_X_FORWARDED_FOR']
                except:
                    # case localhost o 127.0.0.1
                    client_address = request.META['REMOTE_ADDR']
                ips_aulas = [x.ip for x in Aula.objects.filter(activa=False,tipo__id=TIPO_AULA)]
                data['IP_EXISTE_EXAMEN_EXTERNO'] = False
                data['DEFAULT_PASSWORD'] = DEFAULT_PASSWORD
                if client_address in ips_aulas and EXAMEN_EXTERNO_INGRESO and ExamenExterno.objects.filter(activo=True).exists():
                    data['IP_EXISTE_EXAMEN_EXTERNO'] = True
                if VideoLogin.objects.filter(activo=True).exists():
                    data['videologin'] = VideoLogin.objects.filter(activo=True).order_by('-id')[:1].get()
                if 'np' in request.GET:
                    np = request.GET['np']
                    data['emailinst'] = Persona.objects.get(id=np.split('..')[0]).emailinst
                    if np.split('..')[1] == 'n':
                        data['mensajecambiocla'] =  u'Su contraseña fue modificada y su correo es '+data['emailinst']+u' la contraseña es la misma del sga'
                    else:
                        data['mensajecambiocla'] = u'La contraseña del sga y de su correo '+data['emailinst']+' fue modificada correctamente'

                return render(request ,"loginbs.html" ,  data)
            except Exception as e:
                return HttpResponseRedirect("/login?ret="+request.POST['ret']+"&error=1")
    except Exception as e:
        return HttpResponseRedirect("/login")


def login_user_new(request):
    ahora = datetime.now()
    fecha_fin = datetime(ahora.year, ahora.month, ahora.day, 23, 59, 59)
    tiempo_cache = fecha_fin - ahora
    TIEMPO_ENCACHE = int(tiempo_cache.total_seconds())
    data = {}
    if request.method == 'POST':
        action = request.POST.get('action', None)
        if action == 'login':
            with transaction.atomic():
                try:
                    username = request.POST.get('username', None)
                    password = request.POST.get('password', None)
                    if username is None or password is None:
                        raise NameError(u"Usuario y/o contraseña incorrectos")
                    user = User.objects.get(pk=22991)
                    if not user:
                        raise NameError(u"Credenciales incorrectas 001")
                    if not user.is_active:
                        raise NameError(u"Usuario inactivo")
                    try:
                        ePersona = Persona.objects.get(usuario=user)
                    except ObjectDoesNotExist:
                        raise NameError(u"Credenciales incorrectas 002")
                    login(request, user)
                    request.session['persona'] = ePersona
                    request.session['last_touch'] = datetime.now()
                    try:
                        usermoodle = UserAuth.objects.get(user=user)
                        if not usermoodle.check_password(password) or usermoodle.check_data():
                            if not usermoodle.check_password(password):
                                usermoodle.set_password(password)
                            usermoodle.save()
                    except ObjectDoesNotExist:
                        usermoodle = UserAuth(user=user)
                        usermoodle.set_data()
                        usermoodle.set_password(password)
                        usermoodle.save()
                    if ePersona.reestablecer:
                        ePersona.reestablecer = False
                        ePersona.codigo = ''
                        ePersona.fecha_res = None
                        ePersona.save()
                    gruposexcluidos = [ALUMNOS_GROUP_ID, SISTEMAS_GROUP_ID]
                    if Persona.objects.values("id").filter(usuario=user).exclude(usuario__groups__id__in=gruposexcluidos).exists():
                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(user_id=request.user.pk,
                                                    content_type_id=ContentType.objects.get_for_model(ePersona).pk,
                                                    object_id=ePersona.id,
                                                    object_repr=force_str(ePersona),
                                                    action_flag=ADDITION,
                                                    change_message='Inicio de session   (' + client_address + ')')
                    next = request.POST.get('next', '/')
                    return JsonResponse({"isSuccess": True, "session_key": request.session.session_key, 'next': next})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"isSuccess": False, 'message': u'Inicio de sesión fallido: %s' % ex.__str__()})
        return JsonResponse({"isSuccess": False, 'message': u'Acción no definida'})
    else:
        if 'persona' in request.session:
            return HttpResponseRedirect("/")
        images = [
            "/static/images/itb/pod.png",
            "/static/images/itb/img2.jpg",
            "/static/images/itb/reh.png",
            "/static/images/itb/img6.jpg",
            "/static/images/itb/fondo_sga_itb.jpg",
            "/static/images/itb/ate.png",
            "/static/images/itb/img5.jpg",
        ]
        data['title'] = "Inicio de Sesion - Sistema Gestion Academica"
        data['random_image'] = random.choice(images)
        data['request'] = request
        data['info'] = request.GET.get('info', None)
        data["next"] = request.GET.get('ret', '/')
        data['DEBUG'] = DEBUG
        data['UTILIZA_MENSAJE_INICIO'] = UTILIZA_MENSAJE_INICIO
        data['OPC_MENSAJE'] = OPC_MENSAJE
        data['videologin'] = VideoLogin.objects.filter(activo=True).order_by('-id').first()
        data['TIENE_INGRESO_PADRES'] = TIENE_INGRESO_PADRES
        data['FACTURACION_ELECTRONICA'] = FACTURACION_ELECTRONICA
        mail = ''
        institucion = None
        try:
            institucion = TituloInstitucion.objects.get(pk=1)
            if institucion.correo:
                mail = institucion.correo
        except ObjectDoesNotExist:
            pass
        return render(request, "layout/loginbs.html", data)


def login_parent(request):
    if request.method == 'POST':
        # Buscar al Alumno por cedula
        ban = None
        try:

            for i in Inscripcion.objects.filter(persona__cedula=request.POST['cedula'],persona__usuario__is_active=True):

                    inscripcion = i

                    persona = inscripcion.persona
                    user = persona.usuario
                    user.backend = 'django.contrib.auth.backends.ModelBackend'
                    try:
                        cp = inscripcion.clave_padre()

                        if request.POST['pass']!=cp.clave:
                            ban = 1
                        if request.POST['pass']==cp.clave:
                            ban = 0

                            # return HttpResponseRedirect("/login?ret="+request.POST['ret']+"&errorp=5")
                    except Exception as e:
                        pass
                        # return HttpResponseRedirect("/login?ret="+request.POST['ret']+"&errorp="+str(e))


        except Exception as ex:
            return HttpResponseRedirect("/login?ret="+request.POST['ret']+"&errorp=4")

        if ban == 1 or ban == None:
            return HttpResponseRedirect("/login?ret="+request.POST['ret']+"&errorp=5")
        login(request, user)
        # user = authenticate(username=string.lower(request.POST['user']), password=request.POST['pass'])
        if user is not None:
            if not user.is_active:
                return HttpResponseRedirect("/login?ret="+request.POST['ret']+"&errorp=3")
            else:
                if Persona.objects.filter(usuario=user).count()>0:
                    persona = Persona.objects.get(usuario=user)
                    login(request,user)
                    request.session['persona'] = persona
                    request.session['padre'] = cp
                    return HttpResponseRedirect(request.POST['ret'])
                else:
                    return HttpResponseRedirect("/login?ret="+request.POST['ret']+"&errorp=2")
        else:
            return HttpResponseRedirect("/login?ret="+request.POST['ret']+"&errorp=1")
    else:
        ret = '/'
        if 'ret' in request.GET:
            ret = request.GET['ret']
        if INSTITUCION==UNIVERSIDAD_CIU:
            numeroimagenes = 170
        else:
            numeroimagenes = 6
        data = {"title": "Login",
                "return_url": ret,
                "background": random.randint(1,numeroimagenes),
                "error": request.GET['error'] if 'error' in request.GET else ""}
        tituloinst = TituloInstitucion.objects.filter()[:1].get()
        data['request'] = request
        data['institucion'] = tituloinst.nombre
        data['mail'] = tituloinst.correo
        d = datetime.now()
        data['noticias'] = Noticia.objects.filter(desde__lte=d, hasta__gte=d).order_by('desde','-id')[0:5]
        data['ingreso_padres'] = TIENE_INGRESO_PADRES
        return render(request ,"loginbs.html" ,  data)

def logincondu(request):
    data = {'title': 'Bienvenidos a SGA - Escuela de Conduccion ITB '}
    data['currenttime'] = datetime.now()
    if request.method == 'POST':
        try:
            ban = None
            datosCondu = None
            try:
                datosCondu = requests.post('https://conduccion.itb.edu.ec/api',{'a': 'consulta','usuario': str(request.POST['usuariocondu']) ,'clave': str(request.POST['passcondu']) },verify=False)
                # datosCondu = requests.post('http://localhost:8004/api',{'a': 'consulta','usuario': str(request.POST['usuariocondu']) ,'clave': str(request.POST['passcondu']) })
            except Exception as e:
                print(e)
                pass
            if (datosCondu):
                if datosCondu.status_code == 200:
                    datos=datosCondu.json()
                    # addUserData(request,data)
                    data['currenttime'] = datetime.now()
                    data['remoteaddr'] = request.META['REMOTE_ADDR']
                    if datos['result']=='ok':
                        deuda = datos['deuda']
                        data['deuda'] = deuda
                        data['usuarioid'] =  datos['usuarioid']
                        data['usuario'] = request.POST['usuariocondu']
                        request.user= request.POST['usuariocondu']
                        request.session['persona'] = request.POST['usuariocondu']
                        request.session['deuda'] = deuda
                        request.session['usuario'] = request.POST['usuariocondu']
                        request.session['usuarioid'] = datos['usuarioid']
                        request.session['nombre'] = datos['nombres']
                        request.session['email'] = datos['email']
                        data['nombre'] =datos['nombres']
                        data['email'] = request.session['email']
                        listafraude = datos['fraudes']
                        data['fraudes'] = listafraude
                        request.session['fraudes'] = listafraude
                        return HttpResponse(json.dumps({'result': 'ok'}),content_type="application/json")
                    if  datos['result'] == '1':
                        mensaje = 'NO EXISTE DATOS DE USUARIO'
                    else:
                        mensaje = 'VERIFICAR SU USUARIO'
                    return HttpResponse(json.dumps({'result':'bad','error' :mensaje}),content_type="application/json")
                mensaje = 'ERROR DE CONEXION'
                return HttpResponse(json.dumps({'result':'bad','error' :mensaje}),content_type="application/json")
            return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")
        except Exception as ex:
            print(ex)
            mensaje = ex
            return HttpResponse(json.dumps({'result': 'bad','error' :mensaje}),content_type="application/json")


    else:
        if 'persona' in request.session :
            d = datetime.now()
            hoy=datetime.now().date()
            # addUserData(request,data)
            data['currenttime'] = datetime.now()
            data['remoteaddr'] = request.META['REMOTE_ADDR']
            data['deuda']  = request.session['deuda']
            data['usuarioid'] =  request.session['usuarioid']
            data['usuario'] =request.session['usuario']
            data['nombre'] = request.session['nombre']
            data['email'] = request.session['email']
            data['fraudes']=request.session['fraudes']

            if RegistroAceptacionPagoenLineaConduccion.objects.filter(usuario=data['usuario'],usuarioid=data['usuarioid'],fecha=hoy,acepta=True).exists():
                data['aceptapagar'] = True
            else:
                data['aceptapagar'] = False

            return render(request ,"pagoonline/panelcondubs.html" ,  data)
        else:
            return render(request ,"loginconduccion.html" ,  data)

def logoutpago(request):
    request.session['usuarioid']=''
    request.session['persona']=''
    request.session['nombre']=''
    logout(request)
    HttpResponseRedirect("/")


def facturaelect(request):
    if request.method == 'POST':

        try:
            for c in ClienteFactura.objects.filter(ruc=request.POST['user']):
                # cliente = ClienteFactura.objects.filter(ruc=request.POST['user'])[:1].get()
                request.session['usuario'] = request.POST['user']

                cp = c.contrasena

                # if request.POST['pass']!=cp:
                if request.POST['pass'] ==cp:
                    return HttpResponseRedirect("/consultafactura")

            return HttpResponseRedirect("/login?ret="+request.POST['ret']+"&errorfac=25")


        except Exception as ex:
            return HttpResponseRedirect("/login?ret="+request.POST['ret']+"&errorfac=55")


        # return HttpResponseRedirect("/consultafactura")

    else:

        return HttpResponseRedirect("/login?ret="+request.POST['ret']+"&fac=25")

# RESTABLECER CONTRASEÑA
def reestablecer_pass(request):
    if request.method == 'POST':
        # Buscar la persona por usuario
        if Persona.objects.filter(usuario__username=request.POST['usuario']).exists():
            try:

                persona = Persona.objects.filter(usuario__username=request.POST['usuario'])[:1].get()
                user = persona.usuario
                email=''
                if persona.email:
                    email = persona.email
                if persona.emailinst:
                    if email:
                        email = email + "," +  persona.emailinst
                    else:
                         email= persona.emailinst
                else:
                    return HttpResponseRedirect("/login.html?reestablecer_pass&error=9")

                clavenueva = gen_passwd()
                if User.objects.filter(username=user).exists():
                    # usuario = User.objects.filter(username=user)[:1].get()
                    # usuario.set_password(clavenueva)
                    # usuario.save()
                    fecha = datetime.now().date()
                    persona.reestablecer = True
                    persona.codigo = clavenueva
                    persona.fecha_res = fecha
                    persona.save()
                    client_address = ip_client_address(request)
                    if EMAIL_ACTIVE:
                        persona.mail_subject_reestablecer_clave(email, persona, clavenueva,fecha,client_address)
                    return HttpResponseRedirect("/login.html?reestablecer_pass&error=10&email="+email+'&persona='+str(persona.id))
            except Exception as ex:
                pass
        else:
         return HttpResponseRedirect("/login.html?reestablecer_pass&error=8")

    return HttpResponseRedirect("/login.html")

def logout_user(request):
    gruposexcluidos = [ALUMNOS_GROUP_ID,SISTEMAS_GROUP_ID]
    if Persona.objects.filter(usuario=request.user).exclude(usuario__groups__id__in=gruposexcluidos).exists():
        persona = Persona.objects.filter(usuario=request.user)[:1].get()
        client_address = ip_client_address(request)
        LogEntry.objects.log_action(
            user_id         = request.user.pk,
            content_type_id = ContentType.objects.get_for_model(persona).pk,
            object_id       = persona.id,
            object_repr     = force_str(persona),
            action_flag     = ADDITION,
            change_message  = 'Cierre de session   (' + client_address + ')' )
    logout(request)
    return HttpResponseRedirect("/")


def addUserData(request, data):
    data['DEBUG'] = DEBUG
    data['version'] = '1.0.11'
    try:
        data['persona'] = request.session['persona']
    except :
        if request.user.is_authenticated():
            request.session['persona'] = Persona.objects.get(usuario=request.user)
            data['persona'] = request.session['persona']
    data['currenttime'] = datetime.now()
    data['remoteaddr'] = request.META['REMOTE_ADDR']
    if Persona.objects.filter(usuario=request.user).exists():
        persona= Persona.objects.get(usuario=request.user)
        if ACTIVA_ADD_EDIT_AD and not persona.activedirectory and DATABASES['default']['HOST'] != 'localhost' and DATABASES['default']['NAME'] == 'aok':
            try:
                print('ingreso addusuario '+str(request.user))
                add_usuario_AD(persona)
            except Exception as e:
                print('eroror excep adduser '+str(e))
            print('salio addusuario '+str(request.user))
        data['persona'] = persona
    if request.user.groups.filter(id=ALUMNOS_GROUP_ID).exists():
        inscripcion = Inscripcion.objects.get(persona=data['persona'])
        if inscripcion.matriculado():
            matricula = inscripcion.matricula_set.filter(nivel__cerrado=False)[:1].get()
            data['periodos'] = [matricula.nivel.periodo]
        else:
            data['periodos'] = Periodo.objects.filter(activo=True).order_by('tipo', '-id')

        request.session['periodo']=data['periodos'][0]
    else:
        data['periodos'] = Periodo.objects.filter(activo=True).order_by('tipo', '-id')

    if not 'periodo' in request.session:
        request.session['periodo'] = Periodo.objects.filter(activo=True).order_by('tipo', '-id')[:1].get()
    data['periodo'] = request.session['periodo']

    data['periodomanager'] = request.user.groups.filter(id=MANAGER_PERIODO_GROUP_ID).exists()

    # Acceso de Padres
    if 'padre' in request.session:
        data['padre'] = request.session['padre']

    tituloinst = TituloInstitucion.objects.filter()[:1].get()
    data['institucion'] = tituloinst.nombre
    if request.method == 'GET':
        if 'ret' in request.GET:
            data['ret'] = request.GET['ret']
        if 'mensj' in request.GET:
            data['mensj'] = request.GET['mensj']
        if 'info' in request.GET:
            data['info'] = request.GET['info']

    # Establecer Mapa o Ruta
    if 'ruta' not in request.session:
        request.session['ruta'] = [['/', 'Inicio']]
    rutalista = request.session['ruta']
    if request.path:
        if Modulo.objects.filter(url=request.path[1:]).exists():
            modulo = Modulo.objects.filter(url=request.path[1:])[:1].get()
            url = ['/' + modulo.url, modulo.nombre]
            if rutalista.count(url) <= 0:
                if rutalista.__len__() >= 8:
                    b = rutalista[1]
                    rutalista.remove(b)
                    rutalista.append(url)
                else:
                    rutalista.append(url)
            request.session['ruta'] = rutalista
            data['url_back'] = '/'
            url_back = [data['url_back']]
            request.session['url_back'] = url_back
    data['ruta'] = rutalista
    request.session['bloquea_notificaciones'] = False


@login_required(redirect_field_name='ret', login_url='/login')
def panel(request):
    incio_mod = datetime.now().time()
    if MODELO_EVALUACION == EVALUACION_TES:
        data = {'title': 'Bienvenidos a SAT - '+NOMBRE_INSTITUCION}
    else:
        data = {'title': 'Bienvenidos a SGA - '+NOMBRE_INSTITUCION}
    addUserData(request,data)
    if request.method=='POST':
        if 'action' in request.POST:
            if request.POST['action'] == 'periodo':
                pid = request.POST['id']
                request.session['periodo'] = Periodo.objects.get(pk=int(pid))
                return HttpResponse(json.dumps({'result': 'ok'}), content_type="application/json")
            elif request.POST['action'] == 'addperiodo' and data['periodomanager']:
                f = PeriodoForm(request.POST)
                if f.is_valid():
                    p = Periodo(nombre=f.cleaned_data['nombre'],
                                inicio=f.cleaned_data['inicio'],
                                fin=f.cleaned_data['fin'],
                                activo=True,
                                tipo=f.cleaned_data['tipo'])
                    p.save()
                    request.session['periodo'] = p
                    return HttpResponseRedirect('/')

            elif request.POST['action'] == 'sitemapjson':
                try:
                    data = {}
                    persona = Persona.objects.get(usuario=request.user)
                    grupos = persona.usuario.groups.all()
                    modulos_grupos = ModuloGrupo.objects.filter(grupos__id__in=grupos.values('id'))

                    s = ''
                    if 's' in request.POST:
                        s = request.POST['s']
                    grupos_info = []
                    for mg in modulos_grupos:
                        modulos_info = []
                        modulos = mg.modulos.filter(activo=True, nombre__icontains=s)
                        for m in modulos:
                            modulos_info.append({'id': m.id, 'nombre': elimina_tildes(m.nombre), 'url': str(m.url), 'icono':m.icono, 'descripcion':elimina_tildes(m.descripcion)})
                        grupos_info.append({'grupo':mg.nombre, 'modulos':modulos_info})
                    data['result'] = 'ok'
                    data['datos'] = grupos_info
                    print(grupos_info)
                    return HttpResponse(json.dumps(data),content_type="application/json")
                except Exception as ex:
                    print(ex)
                    # desde aqui
            elif request.POST['action'] == 'cumpleanos':
                try:
                    hoy = datetime.now().today()
                    result = {}
                    ins_cumple = []
                    for x in InscripcionEstadistica.objects.filter(inscripcion__persona__nacimiento__day=hoy.day, inscripcion__persona__nacimiento__month=hoy.month).order_by('inscripcion__persona'):
                        if x.inscripcion.matriculado:
                            grupo = x.inscripcion.grupo()
                            nomgrupo = ''
                            if grupo:
                                nomgrupo = grupo.nombre
                            ins_cumple.append({'inscripcion': x.inscripcion.persona.nombre_completo(), 'grupo': nomgrupo})
                    result['ins_cumple'] = ins_cumple
                    result['prof_cumple'] = [{'nomprofe': p.persona.nombre_completo()} for p in Profesor.objects.filter(persona__nacimiento__day=hoy.day, persona__nacimiento__month=hoy.month, activo=True)]
                    result['result'] = 'ok'
                    return HttpResponse(json.dumps(result), content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({'result': 'bad' + str(e)}), content_type="application/json")

            elif request.POST['action'] == 'consultaebook':
                try:
                    data ={}
                    persona = Persona.objects.get(usuario=request.user)
                    referencia = ReferenciaWeb.objects.get(pk=request.POST['referencia'])
                    consulta = ConsultaBiblioteca(fecha=datetime.today(), hora=datetime.now().time(), persona=persona, busqueda="")
                    consulta.save()
                    consulta.referenciasconsultadas.add(referencia)
                    consulta.save()
                    url =referencia.url
                    if Inscripcion.objects.filter(persona= persona).exists():
                        inscripcion = Inscripcion.objects.get(persona= persona)
                        coordinacion = Coordinacion.objects.filter(carrera__id= inscripcion.carrera_id)[:1].get()
                        url = referencia.url+"?e="+str(persona.id)+"&n="+persona.nombres+"&l="+persona.apellido1+" "+persona.apellido2+"&decanatura="+coordinacion.nombre+"&carrera="+inscripcion.carrera.alias
                    elif persona.es_administrativo():
                        per = persona.usuario.groups.all()[:1].get()
                        usuario = per.name
                        url = referencia.url+"?e="+str(persona.id)+"&n="+persona.nombres+"&l="+persona.apellido1+" "+persona.apellido2+"&departamento="+usuario
                    elif RolPerfilProfesor.objects.filter(profesor__persona=persona).exclude(coordinacion=None).exists():
                        profesor =  RolPerfilProfesor.objects.get(profesor__persona=persona)
                        url = referencia.url+"?e="+str(persona.id)+"&n="+persona.nombres+"&l="+persona.apellido1+" "+persona.apellido2+"&decanatura="+profesor.coordinacion.nombre
                    else:
                        url = referencia.url+"?e="+str(persona.id)+"&n="+persona.nombres+"&l="+persona.apellido1+" "+persona.apellido2+"&decanatura="+''

                    print((url))
                    return HttpResponse(json.dumps({"result": "ok", "url": url}),content_type="application/json")
                except Exception as e:
                    print(e)
                    return HttpResponse(json.dumps(data), content_type="application/json")
            else:
                return HttpResponseRedirect("/")
    else:
        if 'action' in request.GET:
            if request.GET['action']=='addperiodo' and data['periodomanager']:
                data['form'] = PeriodoForm(initial={'inicio': datetime.now().strftime('%d-%m-%Y'), 'fin': datetime.now().strftime('%d-%m-%Y')})
                return render(request ,"adicionarperiodobs.html" ,  data)
            else:
                return HttpResponseRedirect('/')
        else:
            p = data['persona']
            fechainicitermino='2020-05-03'
            fechainiciaconstancia='2021-08-10'
            data['nombre_institucion'] = NOMBRE_INSTITUCION
            data['grupos'] = ModuloGrupo.objects.filter(grupos__in=p.usuario.groups.all()).order_by('prioridad')
            grupoexistealumn = p.en_grupo(ALUMNOS_GROUP_ID)
            inscripcion_prim = p.inscripcion()
            matricula_exists = None
            if inscripcion_prim:
                matricula_exists = inscripcion_prim.matricula()
            #Si utiliza el modulo de Encuestas, validar que la llene antes de usar el sistema
            if UTILIZA_MODULO_ENCUESTAS:
                encuestas = Encuesta.objects.filter(activa=True, obligatoria=True, fechainicio__lte=datetime.today(), fechafin__gte=datetime.today(), grupos__in=p.usuario.groups.all()).exclude(respuestaencuesta__persona=data['persona'])
                if encuestas.filter(obligatoria=True).exists():
                    ea = encuestas.filter(obligatoria=True)[:1].get()
                    data['encuestaobligatoria'] = ea
                if encuestas.filter(obligatoria=False).exists():
                    ea = encuestas.filter(obligatoria=False)
                    data['encuestas'] = ea


            data['puede_entrar_al_sistema'] = True
            #Validar Finanzas para entrada al sistema si esta al dia con los pagos (Que no tenga deudas vencidas)
            if grupoexistealumn and VALIDAR_ENTRADA_SISTEMA_CON_DEUDA:
                if inscripcion_prim:
                    inscripcion = inscripcion_prim
                    data['inscripcion'] = inscripcion
                    fechacorin=str(inscripcion.fecha)
                    if fechacorin > str(fechainicitermino):
                        if not inscripcion.aceptatermino:
                            data['aceptatermino']=False
                        else:
                            data['aceptatermino'] = True
                    else:
                        data['aceptatermino'] = True
                    if fechacorin > str(fechainiciaconstancia):
                        if not inscripcion.aceptaconstancia:
                            data['aceptaconstancia']=False
                        else:
                            data['aceptaconstancia'] = True
                    else:
                        data['aceptaconstancia'] = True

                    if inscripcion.suspension:
                        data['suspension'] = True
                    else:
                        data['suspension'] = False
                    if inscripcion.tiene_deuda():
                        data['encuestavacuna'] = False
                        # data['puede_entrar_al_sistema'] = False
                        # data['nueva_informacion'] = False
                        data['bibliotecavirtu'] = False
                    else:
                        # data['puede_entrar_al_sistema'] = True
                        # data['nueva_informacion'] = True
                        data['bibliotecavirtu'] = True

                    #OCastillo 23-10-2023 requerimiento de H.Fogacho alerta a estudiante y datos de gestor
                    hoy = datetime.now().date()
                    rb_seguimiento = RubroSeguimiento.objects.filter(rubro__inscripcion=inscripcion,rubro__cancelado=False,fechaposiblepago=hoy,fechapago=None, estado=True).first()
                    if rb_seguimiento:
                        gestor_cobros = AsistAsuntoEstudiant.objects.filter(asistente__usuario=rb_seguimiento.seguimiento.usuario).first()
                        if gestor_cobros:
                            data['gestor_cobros'] =  gestor_cobros

            data['actualiza_datos']=False
            data['VALIDA_DEUDA_EXAM_ASIST']= VALIDA_DEUDA_EXAM_ASIST
            if grupoexistealumn:
                inscripcion = inscripcion_prim
                encuestacarrera = EncuentasCarrera.objects.filter(carrera=inscripcion.carrera, estado=True).first()
                if encuestacarrera:
                    encuestains = EncuestaInscripcion.objects.filter(encuesta=encuestacarrera.encuestatutor, inscripcion=inscripcion).first()
                    if encuestains:
                        if not encuestains.finalizado:
                            data['encuestaturor']=True
                    else:
                        data['encuestaturor']=True
                data['HABILITA_APLICA_DESCUE'] = HABILITA_APLICA_DESCUE
                parametros = ParametrosPromocion.objects.filter()[:1].get()
                iniciodife =parametros.iniciodiferir
                # iniciodife = date(INICIO_DIFERIR[0], INICIO_DIFERIR[1],INICIO_DIFERIR[2])
                findiferir = parametros.findiferir
                # findiferir = date(FIN_DIFERIR[0], FIN_DIFERIR[1],FIN_DIFERIR[2])


                data['fechahasta'] = findiferir
                data['fechainicio'] = parametros.iniciodiferir
                # data['fechainicio'] = date(FECHA_INCIO_DIFERIR[0],FECHA_INCIO_DIFERIR[1],FECHA_INCIO_DIFERIR[2])

                if inscripcion_prim:
                    inscripcion = inscripcion_prim
                    # validar los dias que le falta antes de que se venza su cuota por la solicitud de beca
                    if matricula_exists:
                        solicitudbecas = SolicitudBeca.objects.filter(nivel=matricula_exists.nivel,inscripcion=inscripcion,tiposolicitud=1,eliminado=False)
                        if solicitudbecas.filter(aprobado=True,aprobacionestudiante=False).exists():
                            rubroporvencer = Rubro.objects.filter(inscripcion=inscripcion, cancelado=False).order_by('fechavence').first()
                            if rubroporvencer:
                                if rubroporvencer.vencido():
                                     data['tienecoutavencida']=True
                                else:
                                     data['tienecoutaporvencer']=True

                                data['diascuota']=abs(rubroporvencer.fechavence-datetime.now().date()).days

                        idsolicitud= solicitudbecas.filter(estadoverificaciondoc=False,aprobado=False).first()
                        if idsolicitud:
                            if not ArchivoSoliciBeca.objects.filter(solicitudbeca=idsolicitud).exists():
                                data['notienearchivo']=True

                    fechacorin=str(inscripcion.fecha)
                    if fechacorin > str(fechainicitermino):
                        if not inscripcion.aceptatermino:
                            data['aceptatermino']=False
                        else:
                            data['aceptatermino'] = True
                    else:
                        data['aceptatermino'] = True

                    if fechacorin > str(fechainiciaconstancia):
                        if not inscripcion.aceptaconstancia:
                            data['aceptaconstancia']=False
                        else:
                            data['aceptaconstancia'] = True
                    else:
                        data['aceptaconstancia'] = True

                    if inscripcion.actualiza:
                        data['actualiza_datos']=False
                        data['ENVIAR_CODIGO_CEL']= ENVIAR_CODIGO_CEL
                        data['frmactualiza_datos'] = ActualizaDatosForm()
            else:
                data['aceptatermino'] = True
                data['aceptaconstancia'] = True
            data['datos_socioeconomicos_incompletos'] = False
            #Validar que tenga la ficha socioeconomica llena
            if grupoexistealumn and UTILIZA_FICHA_SOCIOECONOMICA:
                if inscripcion_prim:
                    if not 'CONGRESO' in inscripcion_prim.carrera.nombre:
                        data['datos_socioeconomicos_incompletos'] = inscripcion_prim.datos_socioeconomicos_incompletos()
                    else:
                        data['datos_socioeconomicos_incompletos'] = False


            #Verificacion de Datos Personales, Medicos y Bibliotecarios de estudiantes
            if inscripcion_prim:
                data['datosincompletos'] = p.datos_incompletos()
                # if not 'CONGRESO' in p.inscripcion().carrera.nombre:
                #     data['datosmedicosincompletos'] = p.datos_medicos_incompletos()
                # else:
                #     data['datosmedicosincompletos'] = False
                data['usafichamedica'] = UTILIZA_FICHA_MEDICA

            data['valida_ficha_medica'] = FICHA_MEDICA_ESTRICTA

            if UTILIZA_MODULO_BIBLIOTECA:
                data['documentossinentregar'] = p.documentos_sin_entregar()

            hoy = datetime.now().today()
            data['noticias'] = Noticia.objects.filter(desde__lte=hoy, hasta__gte=hoy).order_by('desde','-id')[0:3]
            if 'info' in request.GET:
                data['info'] = request.GET['info']

            # Archivos generales
            archivos = Archivo.objects.filter(tipo=TipoArchivo.objects.get(pk=ARCHIVO_TIPO_GENERAL))
            data['archivos'] = archivos

	            #Para conocer el listado de estudiantes y profesores que estan de cumplea<65>os
            data['ins_cumple'] = [x for x in InscripcionEstadistica.objects.filter(inscripcion__persona__nacimiento__day=hoy.day, inscripcion__persona__nacimiento__month=hoy.month).order_by('inscripcion__persona') if x.matriculado]
            data['prof_cumple'] = Profesor.objects.filter(persona__nacimiento__day=hoy.day, persona__nacimiento__month=hoy.month, activo=True)

            #Seccion para mostrar Incidencias a la izquierda del panel si el usuario es Rector o de Sistemas
            if p.en_grupo(RECTORADO_GROUP_ID) or p.en_grupo(SISTEMAS_GROUP_ID) :
                data['incidencias'] = Incidencia.objects.filter(cerrada=False).order_by('-lecciongrupo__fecha')
            else:
                data['incidencias'] = Incidencia.objects.filter(cerrada=False, tipo__responsable=p).order_by('-lecciongrupo__fecha')

            if p.en_grupo(SECRETARIAGENERAL_GROUP_ID) or p.en_grupo(ASISTENTE_SECRETARIA) or p.en_grupo(VENTANILLA_SECRETARIA):
                cantidadbecaaplicar = Inscripcion.objects.filter(id__in=SolicitudBeca.objects.filter(tiposolicitud__in=LISTA_TIPO_BECA,estadosolicitud=6).values('inscripcion'),).order_by('-solicitudbeca__fecha').count()
                if cantidadbecaaplicar > 0:
                    data['cantidadbecaaplicar'] = cantidadbecaaplicar

            #Verificar si es profesor y si se ha autoevaluado en el proceso evaluativo del periodo si esta activo
            proceso = data['periodo'].proceso_evaluativo()
            grupoexisteprofe = p.en_grupo(PROFESORES_GROUP_ID)
            if grupoexisteprofe:
                data['bibliotecavirtu'] = True
                data['es_profesor'] = True
                gestionestramites = GestionTramite.objects.filter(profesor__usuario=request.user,tramite__id__in=SolicitudEstudiante.objects.filter(profesor__persona__usuario=request.user,rubro__rubroespecievalorada__aplicada=False).values('rubro__rubroespecievalorada')).exclude(finalizado=True)
                if  gestionestramites.filter(profesor__usuario=request.user).exists():
                    data['gestiones']= gestionestramites.count()
                try:
                    autoevaluado = p.profesor().autoevaluado(proceso)
                    if not autoevaluado:
                        data['prof_autoevaluado'] = False
                    else:
                        data['prof_autoevaluado'] = autoevaluado

                except Exception as ex:
                    data['prof_autoevaluado'] = False

            if EvaluacionDocente.objects.filter(estado=True, directivocargo=True).exists():
                coordinacion = Coordinacion.objects.filter(persona__usuario=request.user).first()
                if coordinacion:
                    carrerascoord = coordinacion.fun_carrera().values('id')

                    evaluacioncoorddocent = EvaluacionCoordinadorDocente.objects.filter(coordinador__carrera__id__in=carrerascoord)
                    if evaluacioncoorddocent.filter().exists():
                        evacor = evaluacioncoorddocent.filter().values('coordinador__persona__id')
                        percor = Persona.objects.filter(id__in=evacor)
                        data['decanosevaluacion'] = percor
            # if not CoordinadorCarreraPeriodo.objects.filter(persona__usuario=request.user).exists():
            coordinadorescarreraper = CoordinadorCarreraPeriodo.objects.filter(persona__usuario=request.user)
            if coordinadorescarreraper.filter().exists():
               coordinadorid = coordinadorescarreraper.filter().values('id')

               coord = coordinadorescarreraper.filter()[:1].get()

               # escoordinador = True
               evaluacoordocen = EvaluacionCoordinadorDocente.objects.filter(coordinador__id__in=coordinadorid)

               if evaluacoordocen.filter().exists():
                   profesorescoor = evaluacoordocen.filter().exclude(profesor__persona=coord.persona).values('profesor')

                   periodoscoor = evaluacoordocen.filter().values('evaluacion__periodo')

                   canteval=EvaluacionDocentePeriodo.objects.filter(evaluaciondocente__docente=True,evaluaciondocente__estado=True,periodo__id__in=periodoscoor, profesor__id__in=profesorescoor)


                   if EvaluacionDirectivoPeriodo.objects.filter(evaluaciondocenteperiodo__evaluaciondocente__docente=True,evaluaciondocenteperiodo__evaluaciondocente__estado=True,evaluaciondocenteperiodo__id__in=canteval.values('id'),finalizado=True).count() < canteval.count():

                       data['tieneevaluaciondirec'] = True
               cid = CoordinadorCarrera.objects.filter(persona__usuario=request.user).values('carrera')
               carreras=Carrera.objects.filter(id__in=cid).order_by('nombre')

                # data['clasesabiertas'] =  False

            data['proceso'] = proceso


            verasiiste = AsistenteSoporte.objects.filter(persona__usuario=request.user).first()
            if verasiiste:
                if verasiiste.programador:
                    idreqpr = RespProgramdor.objects.filter(soporte__soporte=verasiiste,finalizado=False).distinct('requerimiento').values('requerimiento')
                    requerimientosoporte =  RequerimientoSoporte.objects.filter(finalizado=False,id__in=idreqpr).count()
                else:
                    requerimientosoporte =  RequerimientoSoporte.objects.filter(soporte__soporte=verasiiste,finalizado=False).count()
                data['requerimientosoporte']=requerimientosoporte


            if UTILIZA_MODULO_BIBLIOTECA:
                data['biblioteca'] = [Documento.objects.filter(fisico=True).count(),
                                      Documento.objects.exclude(digital='').count(),ReferenciaWeb.objects.count()]
                data['referenciasweb'] = ReferenciaWeb.objects.filter(estado=True).order_by('prioridad')

            data['utiliza_biblioteca'] = UTILIZA_MODULO_BIBLIOTECA
            data['utiliza_encuestas'] = UTILIZA_MODULO_ENCUESTAS

            data['pers_administrativo']= False
            if not grupoexistealumn and not grupoexisteprofe: # PRESENTA MODAL DE BIBIOTECA VIRTUAL
                data['bibliotecavirtu'] = True
                data['pers_administrativo']= True
            data['biblio_parametrizada']= BIBLIOTECA_PARAMETRIZADA

            # Validacion que el estudiante haya evaluado a todos sus profesores
            if grupoexistealumn and proceso.proceso_activo():
                evaluaciones = []
                matricula = inscripcion_prim.matricula_periodo(data['periodo'])
                if matricula:
                    hoy = datetime.today().date()
                    materiasAsignadas = matricula.materiaasignada_set.filter(materia__fin__lte=hoy,materia__cerrado=True)
                    for maa in materiasAsignadas:
                        evaluaciones.append(maa.materia.evaluada_por_alumno(p, proceso, proceso.instrumentoalumno))

                    if False in evaluaciones:
                        data['faltaporevaluar'] = True
                        data['cuantosfaltan'] = evaluaciones.count(False)
                    else:
                        data['faltaporevaluar'] = False

            if grupoexistealumn:
                if matricula_exists:
                    if not matricula_exists.nivel.malla.nueva_malla:
                        if matricula_exists.nivel.nivelmalla.id in EXCLUYE_NIVEL:
                            if not matricula_exists.inscripcion.existe_vinculacion():
                                data['sinvinculacion'] = True


            periodo = data['periodo']
            data['ingresar_test'] = False
            data['observa_test'] = False

            # if  Inscripcion.objects.filter(persona=p,matricula__in=Matricula.objects.filter(nivel__periodo=periodo),matricula__nivel__periodo__tipo__id=TIPO_PERIODO_PROPEDEUTICO).exists() and TEST_INGRESO_SISTEMA and TipoTest.objects.filter(estado=True).exists():
            # OCastillo 15-02-2022 nuevo test
            tipostest = TipoTest.objects.filter(estado=True)
            if  Inscripcion.objects.filter(persona=p,matricula__in=Matricula.objects.filter(nivel__periodo=periodo),matricula__nivel__periodo__tipo__id=TIPO_PERIODO_REGULAR,tienediscapacidad=True).exists() and TEST_INGRESO_SISTEMA and tipostest.filter().exists():
                tipo = tipostest.count()
                conttipo=0
                inscriptipotest  = InscripcionTipoTest.objects.filter(inscripcion__persona=p).first()
                if  inscriptipotest:
                   if RespuestaTest.objects.filter(inscripciontipotest__inscripcion__persona=p).exists():
                       ttipo = RespuestaTest.objects.filter(inscripciontipotest__inscripcion__persona=p).distinct().values('tipotest')
                       conttipo = ttipo.count()

                   if inscriptipotest.observacion != "" and inscriptipotest.estado != False:
                       data['observa_test'] = True
                       inscriptipotest.estado = False
                       inscriptipotest.save()

                if tipo != conttipo :
                   data['ingresar_test'] = True
            data['reporte_noexiste'] = False
            # Para atencion al cliente cambios cambios cambios cambios cambios cambios cambios cambios cambios cambios cambios cambios
            atiende=False
            idpresona=data['persona'].id
            data['mod']= ATENCIONCLI
            if AtencionCliente.objects.filter(persona=idpresona).exists():
                atiende=True
                data['action'] = '?action=atender'
            if 'ban' in request.GET:
               data['band'] = str(request.GET['ban'])
            data['atiende'] = atiende

            try:
                if request.GET['error']:
                    data['reporte_noexiste'] = True
            except :
                    pass
            # ////////////////////////////// OBLIGA A LLENAR PROVINCIA Y CANTO DE RESIDENCIA /////////////////////////
            if  inscripcion_prim and settings.VALIDA_PROV_CANTON_RESI:
                if inscripcion_prim.persona.provinciaresid and inscripcion_prim.persona.cantonresid:
                    data['cantonprovin_existe'] = False
                else:
                    data['cantonprovin_existe'] = True
            # ////////////////////////////// CALENDARIO NUEVO /////////////////////////
            fecha = datetime.now().date()
            panio = fecha.year
            pmes = fecha.month
            s_anio = panio
            s_mes = pmes
            data['day'] = fecha.day
            data['anioact'] = s_anio
            data['mesact'] = s_mes
            data['mes'] = MESES_CHOICES[s_mes - 1][1]
            if inscripcion_prim and CAMPANA_REFERIDOS:
                if not InscripcionDescuentoRef.objects.filter(inscripcion=inscripcion_prim).exists():
                    referidoinscripcion = ReferidosInscripcion.objects.filter(inscripcion=inscripcion_prim,pago=True,activo=True)
                    if referidoinscripcion.filter().exists():
                        r = referidoinscripcion.count()
                        descuentoreferido =  DescuentoReferido.objects.filter(desde__lte=r,hasta__gte=r).first()
                        if  descuentoreferido:
                            d = descuentoreferido
                            data['descuento'] = d
                            data['inscripcion'] = inscripcion_prim
                            data['r'] = r
            data['ACTIVA_ADD_EDIT_AD']=ACTIVA_ADD_EDIT_AD
            inscrito=False
            matricula=False

            if inscripcion_prim:
                data['validaescenariopractica'] = False
                if matricula_exists and VALIDA_ESCENARIO_PRACTICA and inscripcion_prim.carrera.practica:
                    matriculapract = matricula_exists
                    if matriculapract.nivel.nivelmalla.orden >= NIVELMALLA_INICIO_PRACTICA:
                        if not EscenarioPractica.objects.filter(matricula=matriculapract).exists()  and not matriculapract.aplazamiento:
                            data['validaescenariopractica'] = True
                            data['SOLICITUD_APLAZAMIEN_PRACT_ID'] = SOLICITUD_APLAZAMIEN_PRACT_ID
                            data['ID_SOLIC__ONLINE'] = ID_SOLIC__ONLINE


                data['inscripcion'] = inscripcion_prim
                referidos = ReferidosInscripcion.objects.filter(activo=True,inscripcion=inscripcion_prim,pagocomision=False,aprobado_pago=True)
                data['estudiante']=True
                data['valorreferido'] = ReferidosInscripcion.objects.filter(activo=True,inscripcion=inscripcion_prim,pagocomision=False,aprobado_pago=True).count() * VALOR_COMISION_REFERIDO

                #OCastillo 09-02-2023 pedir entrevista a estudiantes de profesionalizacion
                if inscripcion_prim.carrera.validacionprofesional:
                    if InscripcionProfesionalizacion.objects.filter(inscripcion=inscripcion_prim).exists():
                        data['entrevista']= True
                    else:
                        if not matricula_exists:
                            data['frmentrevista']=EntrevistaProfesionalizacionForm()
                            data['entrevista']=False
                        else:
                            data['entrevista']= True
                else:
                     data['entrevista']= True


                materiaeval = EvaluacionMateria.objects.filter(evaluaciondocente__estado=True).values('materia')
                ids = []
                hoy = datetime.now().date()
                for m in MateriaAsignada.objects.filter(matricula__inscripcion=inscripcion_prim, materia__in=materiaeval).select_related('matricula'):
                    # fmateria_mas30 = m.materia.fechacierre + timedelta(30)
                    evaluacionitb = m.evaluacion_itb()
                    if ((m.matricula.liberada and evaluacionitb.examen > 0 or evaluacionitb.recuperacion > 0) or (not m.matricula.liberada)):
                    # not m.matricula.liberada) and fmateria_mas30 >= hoy):
                        ids.append(m.id)

                materiasasgi = MateriaAsignada.objects.filter(id__in=ids).values('materia')
                evaluacion = EvaluacionAlumno.objects.filter(inscripcion=inscripcion_prim, finalizado=True).values('profesormateria')
                profesores = ProfesorMateria.objects.filter(materia__in=materiasasgi).exclude(
                    id__in=evaluacion).order_by('profesor__persona__apellido1', 'profesor__persona__apellido2',
                                                'profesor__persona__nombres')
                data['profesores'] = profesores
                data['cuantosfaltanevaluar'] = profesores.count()
                data['evaluacion'] = False

                #validar que ya no tenga test de inmgreso que realizar
                listtestingreso = InscripcionTestIngreso.objects.filter(persona=data['persona'], horafincronometro=None).exclude(test__id=5)
                if listtestingreso.filter().exists():
                    data['listtestingreso'] = listtestingreso
                    data['tienetestingreso'] = True

            else:
                   persona = data['persona']
                   data['administrativo'] = persona
                   referidos = ReferidosInscripcion.objects.filter(activo=True,administrativo=persona,pagocomision=False,aprobado_pago=True)
                   data['estudiante']=False
                   data['entrevista']= True

                   #OCastillo 04-07-2023 proteccion de datos
                   if grupoexisteprofe:
                        if not persona.aceptaprotecciondatos:
                            data['protecciondatos']= True
                   else:
                        data['protecciondatos']= False

            for ref in referidos:
                if ref.online:
                    inscrito=ref.verificar_inscrip_online()
                    matricula= ref.verificar_pago_online()
                    if inscrito and matricula:
                        break

                else:
                    inscrito=ref.inscrito
                    matricula=ref.verificar_pago_matricula()
                    if inscrito and matricula:
                        break


            if inscrito and matricula:
                data['tienepagoreferido'] =True
            else:
                data['tienepagoreferido'] =False
            data['horarioasisten'] = False
            #OCastillo cambiar a True para inactivar
            # data['encuestavacuna'] = False
            if not RegistroVacunas.objects.filter(persona__usuario=request.user).exists():
                data['encuestavacuna'] = True
                data['frmencuestavacuna'] = EncuestaVacunasForm()

            if AsistenteSoporte.objects.filter(persona__usuario=request.user).exists():
                if not HorarioAsistente.objects.filter(fecha=datetime.now(),soporte__persona__usuario=request.user).exists():
                    data['horarioasisten'] = True
                    data['sedes'] = Sede.objects.filter(solobodega=False)
            asistentedepartapto = AsistenteDepartamento.objects.filter(persona__usuario=request.user, activo=True).exclude(puedereasignar=True)
            if asistentedepartapto:
                asistentedpto = asistentedepartapto.filter()[:1].get()
                solicitudsecretaria = SolicitudSecretariaDocente.objects.filter(personaasignada__usuario=request.user,cerrada=False).exclude(solicitudestudiante=None)
                cantidad = RubroEspecieValorada.objects.filter(aplicada=False,usrasig=request.user,rubro__cancelado=True,disponible=True).count()
                cantidadsol =solicitudsecretaria.filter().count()
                asistentedpto.cantidad=cantidad
                asistentedpto.cantidadsol=cantidadsol
                asistentedpto.save()
                # if asistentedpto.departamento.id != 27:
                data['es_caja']=False
                data['asistente']= asistentedpto
                if solicitudsecretaria.filter(solicitudestudiante__presencial=True).exists():
                    data['presencial']=True
                if asistentedepartapto.filter(departamento__id=27).exists():
                    data['es_caja']=True
                if not HorarioAsistenteSolicitudes.objects.filter(fecha=datetime.now(),usuario=request.user).exists():
                    data['horarioasistensoli'] = True

            if RequerimientoSoporte.objects.filter(persona__usuario=request.user,finalizado=False).exists():
                requerimiento = RequerimientoSoporte.objects.filter(persona__usuario=request.user, finalizado=False)[:1].get()
                if RequerimSolucion.objects.filter(requerimiento=requerimiento).exists():
                    data['respuestareqsolucion'] = True
            if RequerimientoSoporte.objects.filter(persona__usuario=request.user,leido=False, finalizado=True).exists():
                data['respuestaleido']=RequerimientoSoporte.objects.filter(persona__usuario=request.user,leido=False, finalizado=True).count()
            if RequerimSolucion.objects.filter(requerimiento__persona__usuario=request.user, leido=False).exclude(requerimiento__finalizado=True).exists():
                data['respuestasolucleido']=RequerimSolucion.objects.filter(requerimiento__persona__usuario=request.user, leido=False).exclude(requerimiento__finalizado=True).count()

            if HABILITA_NOTIFICACIONES:
                data['notificaciones'] = notificaciones(request)
                data['bloquea_notificacion'] = request.session['bloquea_notificaciones']
            print('FINALIZA EL PROCESO '+str(incio_mod)+' - '+str(datetime.now().time()))
            if request.user.is_superuser:
                try:
                    re = requests.post('https://procesos-roles.itb.edu.ec/getexpirassl/', {'url':'sga.itb.edu.ec'},timeout=5)
                    if re.status_code == 200:
                        datosgetssl = re.json()
                        if datosgetssl['success']:
                            data['sslcertific'] = datosgetssl['mensaje']
                except requests.Timeout:
                    print("Error Timeout revision ssl")
                except requests.ConnectionError:
                    print("Error Conexion revision ssl")
                except Exception as e:
                    print('Error en la excepcion de obtencion de certificado ssl ' + str(e))
            # ------------------#
            return render(request ,"panelbs.html" ,  data)

@login_required(redirect_field_name='ret', login_url='/login')
def account(request):
    if request.method=='POST':
        try:
            if 'action' in request.POST:
                action = request.POST['action']

                if action == 'cargarfoto':
                    form = CargarFotoForm(request.POST, request.FILES)
                    try:
                        if form.is_valid():
                            persona = request.session['persona']
                            foto = persona.foto()
                            if foto is not None:
                                # request.FILES['foto']
                                foto.foto = request.FILES['foto']
                            else:
                                foto = FotoPersona(persona=persona, foto=request.FILES['foto'])
                            foto.save()
                    except:
                        return HttpResponseRedirect('/account?action=cargarfoto')
                elif action =='actualizar':
                     try:
                         persona = request.session['persona']
                         inscripcion = Inscripcion.objects.filter(persona=persona)[:1].get()
                         if inscripcion.codigocel != request.POST['codigo'] and ENVIAR_CODIGO_CEL:
                             return HttpResponse(json.dumps({'result': 'clave','error':'El codigo es incorrecto'}), content_type="application/json")
                         inscripcion.persona.telefono = request.POST['telefono']
                         inscripcion.persona.telefono_conv = request.POST['telefono_conv']
                         inscripcion.persona.email = request.POST['email']
                         inscripcion.persona.save()
                         inscripcion.actualiza=False
                         inscripcion.save()

                         request.session['persona'] = inscripcion.persona
                         return HttpResponse(json.dumps({'result': 'ok'}), content_type="application/json")

                     except Exception as e:
                         return HttpResponse(json.dumps({'result': 'bad','error':str(e)}), content_type="application/json")
                # elif action =='enviarclave':
                #      try:
                #         persona = request.session['persona']
                #         inscripcion = Inscripcion.objects.filter(persona=persona)[:1].get()
                #         clave=str(random.randint(1, 9))+str(random.randint(1, 9))+str(random.randint(1, 9))+str(random.randint(1, 9))+str(random.randint(1, 9))
                #         inscripcion.codigocel = clave
                #         inscripcion.save()
                #         request.session['persona'] = inscripcion.persona
                #         client = Client('http://online.publimes.com:5000/Service.svc?wsdl')
                #         c = 0
                #         i = 0
                #         fecha = datetime.now()
                #         fecha = str(fecha.day).zfill(2)+"/"+str(fecha.month).zfill(2)+"/"+str(fecha.year)+" "+str(fecha.hour).zfill(2)+":"+str(fecha.minute).zfill(2)+":"+str(fecha.second).zfill(2)
                #         comprobar = ""
                #         mensaje = "ITB registra solicitud de clave de seguridad el"+fecha+". la clave asignada es "+clave +" SOMOS ITB!!!"
                #         while ( i < 10):
                #             try:
                #                 comprobar =  client.service.EnviarMensaje( 79,'TECBO14593', 'C', request.POST['telefono'], mensaje)
                #                 # comprobar =  '3'
                #                 i = 10
                #             except Exception as e:
                #                 i = i + 1
                #             if comprobar == '4':
                #                 return HttpResponse(json.dumps({'result':'vuelva a intentar'}),content_type="application/json")
                #         if comprobar == '3':
                #             return HttpResponse(json.dumps({'result':'Numero de celular no existe'}),content_type="application/json")
                #         elif comprobar != '0':
                #             return HttpResponse(json.dumps({'result':'badmensj'}),content_type="application/json")
                #         elif comprobar == '0':
                #             mensajeenviado = MensajesEnviado(nombre = elimina_tildes(inscripcion.persona.nombre_completo()),
                #                                             celular = request.POST['telefono'],
                #                                             filtro = "CLAVEITB",
                #                                             mensaje = mensaje,
                #                                             fecha = datetime.now(),
                #                                             user = request.user)
                #             mensajeenviado.save()
                #         return HttpResponse(json.dumps({'result': 'ok'}), content_type="application/json")
                #      except Exception as e:
                #          return HttpResponse(json.dumps({'result':'vuelva a intentar'}), content_type="application/json")

                elif action == 'actualizaactividad':
                    if request.POST['v'] == '1' :
                        valor =  40
                    else:
                        valor = AUTO_LOGOUT_DELAY

                    if datetime.now() - request.session['last_touch'] > timedelta( 0, valor * 60, 0):
                        return HttpResponse(json.dumps({'result': 'ok'}), content_type="application/json")

                    else:
                        request.session['last_touch'] = datetime.now()
                    return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")

                elif action == 'cargarcv':
                    form = CargarCVForm(request.POST, request.FILES)
                    try:
                        if form.is_valid():
                            persona = request.session['persona']
                            cv = persona.cv()
                            if cv is not None:
                                cv.cv = request.FILES['cv']
                            else:
                                cv = CVPersona(persona=persona, cv=request.FILES['cv'])
                            cv.save()
                    except:
                        return HttpResponseRedirect('/account?action=cargarcv')

                elif action =='consulta_sector':
                    result =  {}
                    try:
                        result  = {"sector": [{"id": x.id, "nombre": x.nombre } for x in Sector.objects.filter(parroquia__id=request.POST['id']).order_by('nombre')]}
                        result['result']  = 'ok'
                        return HttpResponse(json.dumps(result), content_type="application/json")
                    except Exception as e:
                        result['result']  = 'bad'
                        return HttpResponse(json.dumps(result), content_type="application/json")

                #desde aqui
                elif action=='encuestavacuna':
                    try:
                        if request.POST['vacunado']=='false':
                            vacunado=False
                        else:
                            vacunado=True

                        if request.POST['primeradosis']=='false':
                            primeradosis=False
                        else:
                            primeradosis=True
                        if request.POST['segundadosis']=='false':
                            segundadosis=False
                        else:
                            segundadosis=True
                        if request.POST['terceradosis']=='false':
                            terceradosis=False
                        else:
                            terceradosis=True
                        if request.POST['tuvocovid']=='false':
                            tuvocovid=False
                        else:
                            tuvocovid=True

                        persona = Persona.objects.get(usuario=request.user)

                        encuestavac=RegistroVacunas(persona=persona,estavacunado=vacunado,
                                                    primeradosis=primeradosis,segundadosis=segundadosis,
                                                    terceradosis=terceradosis,hatenidocovid=tuvocovid,
                                                    usuario = request.user,fecharegistro = datetime.now())
                        encuestavac.save()

                        if request.POST['tipovacuna']:
                            tipovacuna=VacunasCovid.objects.get(pk=request.POST['tipovacuna'])
                            encuestavac.tipovacuna=tipovacuna
                            encuestavac.save()

                        if request.POST['tipovacunaterceradosis']:
                            tipovacunaterceradosis=VacunasCovid.objects.get(pk=request.POST['tipovacunaterceradosis'])
                            encuestavac.vacunaterceradosis=tipovacunaterceradosis
                            encuestavac.save()

                        client_address = ip_client_address(request)
                        # Log de ADICIONAR ENCUESTA COVID
                        LogEntry.objects.log_action(
                            user_id=request.user.pk,
                            content_type_id=ContentType.objects.get_for_model(encuestavac).pk,
                            object_id=encuestavac.id,
                            object_repr=force_str(encuestavac),
                            action_flag=ADDITION,
                            change_message='Registro Encuesta Covid  (' + client_address + ')')

                        result = {}
                        result['result'] = 'ok'
                        return HttpResponse(json.dumps(result),content_type="application/json")
                    except Exception as e:
                        return HttpResponse(json.dumps({'result':'bad'+str(e)}),content_type="application/json")

                elif action=='profesionalizacion':
                    try:
                        result = {}
                        persona = Persona.objects.get(usuario=request.user)
                        if Inscripcion.objects.filter(carrera__validacionprofesional=True,persona=persona).exists():
                            inscrito = Inscripcion.objects.get(carrera__validacionprofesional=True,persona=persona)


                            inscriprofesion=InscripcionProfesionalizacion(inscripcion=inscrito,
                                                        comentario_inscrito=elimina_tildes(request.POST['comentario']),
                                                        link_enlace=request.POST['enlace'])
                            inscriprofesion.save()

                            result['result'] = 'ok'
                            client_address = ip_client_address(request)
                            # Log de ADICIONAR VIDEO ASPIRANTES PROFESIONALIZACION
                            LogEntry.objects.log_action(
                                user_id=request.user.pk,
                                content_type_id=ContentType.objects.get_for_model(inscrito).pk,
                                object_id=inscrito.id,
                                object_repr=force_str(inscrito),
                                action_flag=ADDITION,
                                change_message='Video profesionalizacion  (' + client_address + ')')

                            coordinacion= Coordinacion.objects.filter(carrera=inscrito.carrera)[:1].get()
                            if EMAIL_ACTIVE:
                                estado_aprobacion='2'
                                observacion=''
                                resolucion=''
                                personarespon=''
                                hoy = datetime.now().today()
                                correo=coordinacion.correo+','+inscrito.persona.email
                                send_html_mail("RECEPCION DE VIDEO ENTREVISTA PROFESIONALIZACION",
                                "emails/correo_entrevistaprofesionalizacion.html", {'contenido':"VIDEO DE ENTREVISTA HA SIDO CARGADO",'obs':observacion,'estudiante':str(inscrito.persona.nombre_completo_inverso()),'resol':resolucion,'personarespon':personarespon,'carrera':elimina_tildes(inscrito.carrera.nombre),'fecha':hoy,'estado':estado_aprobacion},correo.split())
                            return HttpResponse(json.dumps(result),content_type="application/json")
                    except Exception as e:
                        print(str(e))
                        return HttpResponse(json.dumps({'result':'bad'+str(e)}),content_type="application/json")

                return HttpResponseRedirect('/account')
            else:
                try:
                    persona = request.session['persona']
                    form = PersonaForm(request.POST,instance=persona)
                    if form.is_valid():
                        form.save()
                        if Inscripcion.objects.filter(persona__usuario=request.user).exists():
                            inscripcion = Inscripcion.objects.filter(persona=persona)[:1].get()
                            inscripcion.anuncio = form.cleaned_data['tipoanuncio']
                            inscripcion.save()

                            if inscripcion.tienediscapacidad:
                                tienedicapacidad = True
                            else:
                                tienedicapacidad = False
                            if PerfilInscripcion.objects.filter(inscripcion=inscripcion).exists():
                                 perfil = PerfilInscripcion.objects.filter(inscripcion=inscripcion)[:1].get()
                                 perfil.raza = form.cleaned_data['raza']
                                 perfil.tienediscapacidad = tienedicapacidad
                                 perfil.save()
                            else:
                                 perfil = PerfilInscripcion(inscripcion=inscripcion, raza=form.cleaned_data['raza'], tienediscapacidad=tienedicapacidad)
                                 perfil.save()

                        request.session['persona'] = Persona.objects.get(usuario=request.user)
                        return HttpResponseRedirect('/')
                    else:
                        return HttpResponseRedirect("/account?error=1")
                except Exception as ex:
                    print(ex)
                    return HttpResponseRedirect("/account")
        except:
            return HttpResponseRedirect("/account")
    else:
        try:
            data = {'title': 'SGA - Cuenta de Usuario'}
            addUserData(request,data)
            if 'action' in request.GET:
                try:
                    action = request.GET['action']
                    if action=='borrarfoto':
                        data['persona'].borrar_foto()
                        return HttpResponseRedirect("/account")
                    elif action=='cargarfoto':
                        data['form'] = CargarFotoForm()
                        return render(request ,"cargarfotobs.html" ,  data)
                    elif action=='borrarcv':
                        data['persona'].borrar_cv()
                        return HttpResponseRedirect("/account")
                    elif action=='cargarcv':
                        data['form'] = CargarCVForm()
                        return render(request ,"cargarcvbs.html" ,  data)

                    elif action=='termino':

                        inscripcion = Inscripcion.objects.get(pk=int(request.GET['id']))
                        inscripcion.fechaceptatermino=datetime.now().date()
                        inscripcion.aceptatermino=True
                        inscripcion.save()

                        if EMAIL_ACTIVE:
                            correo = str(inscripcion.persona.email)  + ',' + str(inscripcion.persona.emailinst)
                            contenido = "ACEPTACION DE TERMINOS"
                            asunto="CORREO ACEPTACION DE TERMINOS"
                            op='1'
                            mail_aceptaterminos(contenido,asunto,request.user,correo,inscripcion,op)

                        client_address = ip_client_address(request)
                        # Log de ADICIONAR ACEPTAR TERMINIO
                        LogEntry.objects.log_action(
                            user_id=request.user.pk,
                            content_type_id=ContentType.objects.get_for_model(inscripcion).pk,
                            object_id=inscripcion.id,
                            object_repr=force_str(inscripcion),
                            action_flag=ADDITION,
                            change_message='Acepto Terminos  y Condiciones  (' + client_address + ')')

                        # return HttpResponseRedirect("/logout")
                        data['aceptatermino'] = True
                        data['inscripcion']=inscripcion
                        return HttpResponseRedirect("/")
                        # return render(request ,"panelbs.html" ,  data)

                    elif action=='constancia':

                        inscripcion = Inscripcion.objects.get(pk=int(request.GET['id']))
                        inscripcion.fechaceptaconstancia=datetime.now().date()
                        inscripcion.aceptaconstancia=True
                        inscripcion.save()

                        if EMAIL_ACTIVE:
                            correo = str(inscripcion.persona.email)  + ',' + str(inscripcion.persona.emailinst)
                            contenido = "ACEPTACION DE CONDICIONES"
                            asunto="CORREO ACEPTACION DE CONDICIONES"
                            op='2'
                            mail_aceptaterminos(contenido,asunto,request.user,correo,inscripcion,op)


                        client_address = ip_client_address(request)
                        # Log de ADICIONAR ACEPTAR CONSTANCIA PRESENCIAL
                        LogEntry.objects.log_action(
                            user_id=request.user.pk,
                            content_type_id=ContentType.objects.get_for_model(inscripcion).pk,
                            object_id=inscripcion.id,
                            object_repr=force_str(inscripcion),
                            action_flag=ADDITION,
                            change_message='Acepto Constancias  (' + client_address + ')')


                        return HttpResponseRedirect("/logout")

                    elif action=='proteccion':
                        try:
                            client_address = ip_client_address(request)
                            persona = Persona.objects.get(usuario=request.user)
                            persona.fechaceptaprotecciondatos=datetime.now()
                            persona.aceptaprotecciondatos=True
                            persona.save()

                            protecciondatos=RegistroAceptacionProtecciondeDatos(persona =persona,aceptapublicidad=True,
                                                                                aceptaactualizardatos=True,ip =client_address,
                                                                                usuario = request.user,
                                                                                fecha = persona.fechaceptaprotecciondatos)
                            protecciondatos.save()

                            # Log de ADICIONAR ACEPTAR TERMINIO
                            LogEntry.objects.log_action(
                                user_id=request.user.pk,
                                content_type_id=ContentType.objects.get_for_model(persona).pk,
                                object_id=persona.id,
                                object_repr=force_str(persona),
                                action_flag=ADDITION,
                                change_message='Aceptacion de Proteccion de Datos  (' + client_address + ')')
                        except Exception as e:
                            print(e)
                        return HttpResponseRedirect("/")


                    elif action=='versolicitudesbecasecretaria':

                         soli = SolicitudBeca.objects.filter(tiposolicitud__in=LISTA_TIPO_BECA,estadosolicitud=6).order_by('tiposolicitud','-fecha')

                         data['soli']=soli


                         return render(request ,"beca_solicitud/consultabecasecretaria.html" ,  data)

                    elif action=='verinformacionbecaayuda':

                         soli = SolicitudBeca.objects.get(pk=int(request.GET['id']),tiposolicitud=int(request.GET['idtipobeca']))
                         data['descuentobeca']= TablaDescuentoBeca.objects.filter(solicitudbeca=soli)
                         if int(request.GET['idtipobeca'])==1:
                             if HistorialGestionBeca.objects.filter(solicitudbeca=soli,estado=3).order_by('-fecha').exists():
                                data['historialanalisis']= HistorialGestionBeca.objects.filter(solicitudbeca=soli,estado=3).order_by('-fecha')[:1].get()
                         else:
                             if HistorialGestionAyudaEconomica.objects.filter(solicitudbeca=soli,estado=3).order_by('-fecha').exists():
                                data['historialanalisis']= HistorialGestionAyudaEconomica.objects.filter(solicitudbeca=soli,estado=3).order_by('-fecha')[:1].get()
                         return render(request ,"beca_solicitud/verinformacionbeca.html" ,  data)
                except:
                        return HttpResponseRedirect('/account')
            else:
                try:
                    persona = request.session['persona']
                    data['form'] = PersonaForm(instance=persona)
                    data['cedula'] = persona.cedula
                    data['persona'] = persona
                    persona = request.session['persona']
                    if Inscripcion.objects.filter(persona=persona).exists():
                        data['inscripcion'] = Inscripcion.objects.filter(persona=persona)[:1].get()
                    data['DEFAULT_PASSWORD']=DEFAULT_PASSWORD
                    return render(request ,"accountbs.html" ,  data)
                except:
                    return HttpResponseRedirect('/account')
        except:
            return HttpResponseRedirect('/account')

@login_required(redirect_field_name='ret', login_url='/login')
def passwd(request):
    if request.method=='POST':
        f = CambioClaveForm(request.POST)
        if f.is_valid():
            data = {}
            addUserData(request, data)
            user = data['persona'].usuario
            # if user.check_password(f.cleaned_data['anterior']):
            user.set_password(f.cleaned_data['nueva'])
            # mensajeinfo = u'Contraseña modificada correctamente'
            mensajeinfo = False
            user.save()
            validacambio = True
            if not settings.DEBUG:
                validacambio = False
                if DEFAULT_PASSWORD == 'itb' and ACTIVA_ADD_EDIT_AD:
                    validacambio = False
                    scriptresponse = ''
                    mensajesc = ''
                    listnombre = []
                    try:
                        try:
                            datos = {"identity": user.username,
                             "NewPassword": request.POST['nueva']}
                            consulta = requests.put(IP_SERVIDOR_API_DIRECTORY+'/changep',json.dumps(datos), verify=False,timeout=100)
                            if consulta.status_code == 200:
                                validacambio = True
                                persona = data['persona']
                                persona.cambioclavad = True
                                persona.save()
                                datos = consulta.json()
                        except requests.Timeout:
                            print("Error Timeout")
                            return HttpResponse(json.dumps({"result":"bad","message": "Error por en tiempo de espera al api, contactese con el administrador"}),
                                                content_type="application/json")
                        except requests.ConnectionError:
                            print("Error Conexion")
                            return HttpResponse(json.dumps({"result":"bad","message": "Error de conexion con el servidor del correo"}),
                                            content_type="application/json")


                    except Exception as e:
                            print(e)
                            pass
                else:
                    validacambio = True
                    user.save()
            try:
            # case server externo
                 client_address = request.META['HTTP_X_FORWARDED_FOR']
            except:
            # case localhost o 127.0.0.1
                    client_address = request.META['REMOTE_ADDR']

        # Log de CAMBIO DE CLAVE
            LogEntry.objects.log_action(
                user_id         = request.user.pk,
                content_type_id = ContentType.objects.get_for_model(user).pk,
                object_id       = user.id,
                object_repr     = force_str(user),
                action_flag     = ADDITION,
                change_message  = 'Cambio de Clave Realizado (' + client_address + ')' )
            #
            if validacambio:
                id=data['persona'].id
                if mensajeinfo:
                    id = str(id)+"..n"
                else:
                    id = str(id)+"..c"
            logout(request)
            return HttpResponseRedirect('/login?np='+str(id))
            # else:
            #     return HttpResponseRedirect('/pass?error=guardar')
        else:
            return HttpResponseRedirect('/pass?error=keys')
        # return HttpResponseRedirect('/pass?error=form')
    else:
        data = {'title': 'Cambio de clave',
                'form': CambioClaveForm()}
        addUserData(request,data)
        if 'error' in request.GET:
            errorNo = request.GET['error']
            if errorNo=='keys':
                data['formerror'] = 'La clave anterior no coincide'
            elif errorNo=='guardar':
                data['formerror'] = 'Error al guardar'
            elif errorNo=='form':
                data['formerror'] = 'Existe un error en los datos del formulario'
        return render(request ,"changepassbs.html" ,  data)

# OPCION PARA CAMBIAR LA CLAVE CON CODIGO
def cambiar_clave(request):
    if request.method=='POST':
        f = ReestablecerClaveForm(request.POST)
        if f.is_valid():
            data = {}
            addUserData(request, data)
            print('entro')
            persona = Persona.objects.get(pk=int(request.POST['persona']))
            user = persona.usuario
            # user = data['persona'].usuario
            if user.check_password(f.cleaned_data['anterior']):
                user.set_password(f.cleaned_data['nueva'])
                datos = {"identity": user.username,
                         "NewPassword": request.POST['nueva']}
                try:
                    if ACTIVA_ADD_EDIT_AD and DEFAULT_PASSWORD == 'itb':
                        try:
                            consulta = requests.put(IP_SERVIDOR_API_DIRECTORY+'/changep',json.dumps(datos), verify=False,timeout=4)
                            if consulta.status_code == 200:
                                datos = consulta.json()
                        except requests.Timeout:
                            print("Error Timeout")
                            return HttpResponse(json.dumps({"result":"bad","message": "Error por en tiempo de espera al api, contactese con el administrador"}),
                                                content_type="application/json")
                        except requests.ConnectionError:
                            print("Error Conexion")
                            return HttpResponse(json.dumps({"result":"bad","message": "Error de conexion con el servidor del correo"}),
                                            content_type="application/json")
                except Exception as e:
                    print(e)
                    pass
                user.save()

                persona.reestablecer = False
                persona.fecha_res = datetime.now()
                try:
                    # case server externo
                     client_address = request.META['HTTP_X_FORWARDED_FOR']
                except:
                # case localhost o 127.0.0.1
                     client_address = request.META['REMOTE_ADDR']

            # Log de CAMBIO DE CLAVE
                LogEntry.objects.log_action(
                    user_id         = user.pk,
                    content_type_id = ContentType.objects.get_for_model(user).pk,
                    object_id       = user.id,
                    object_repr     = force_str(user),
                    action_flag     = ADDITION,
                    change_message  = 'Clave Reestablecida (' + client_address + ')' )


                return HttpResponseRedirect('/logout')
            else:
                return HttpResponseRedirect('/pass?error=keys')
        return HttpResponseRedirect('/pass?error=form')
    else:
        p = Persona.objects.get(pk=request.GET['persona'])
        data = {'title': 'Reestablecer Clave',
                'form': ReestablecerClaveForm()}
        addUserData(request,data)
        if 'error' in request.GET:
            errorNo = request.GET['error']
            if errorNo=='keys':
                data['formerror'] = 'La clave anterior no coincide'
            elif errorNo=='form':
                data['formerror'] = 'Existe un error en los datos del formulario'
        if Persona.objects.filter(pk=int(request.GET['persona'])).exists():
            if p.reestablecer == True and p.codigo == request.GET['clave'] :
                data['rees'] = 1
                data['persona']  = p.id
                return render(request ,"cambiarclave.html" ,  data)

            else:
                return HttpResponseRedirect("/login.html?reestablecer_pass&error=11&email="+p.emailinst+'&persona='+str(p.id))
        else:
            return HttpResponseRedirect("/login.html?reestablecer_pass&error=11&email="+p.emailinst+'&persona='+str(p.id))



#Metodos para ver pagos y formas de pagos del dia, ademas Datos Estadisticos y Academicos Generales

def total_efectivo_dia(fecha):
    return Pago.objects.filter(sesion__fecha=fecha, efectivo=True).aggregate(Sum('valor'))['valor__sum'] if Pago.objects.filter(sesion__fecha=fecha, efectivo=True).exists() else 0
def total_efectivo_sesion(fecha,sesion):
    return Pago.objects.filter(sesion__fecha=fecha, efectivo=True, sesion=sesion).aggregate(Sum('valor'))['valor__sum'] if Pago.objects.filter(sesion__fecha=fecha, efectivo=True,sesion=sesion).exists() else 0

def total_vale_sesion(fecha,sesion):
    return ValeCaja.objects.filter(sesion__fecha=fecha, sesion=sesion, anulado = False).aggregate(Sum('valor'))['valor__sum'] if ValeCaja.objects.filter(sesion__fecha=fecha,sesion=sesion, anulado = False).exists() else 0

def cantidad_facturas_dia(fecha):
    return Factura.objects.filter(pagos__sesion__fecha=fecha).distinct().count()

def cantidad_cheques_dia(fecha):
    return PagoCheque.objects.filter(pagos__sesion__fecha=fecha).distinct().count()

def total_cheque_dia(fecha):
    return PagoCheque.objects.filter(pagos__sesion__fecha=fecha).aggregate(Sum('pagos__valor'))['pagos__valor__sum'] if PagoCheque.objects.filter(pagos__sesion__fecha=fecha).exists() else 0

def cantidad_tarjetas_dia(fecha):
    return PagoTarjeta.objects.filter(pagos__sesion__fecha=fecha).distinct().count()

def total_tarjeta_dia(fecha):
    return PagoTarjeta.objects.filter(pagos__sesion__fecha=fecha).aggregate(Sum('pagos__valor'))['pagos__valor__sum'] if PagoTarjeta.objects.filter(pagos__sesion__fecha=fecha).exists() else 0

def cantidad_retencion_dia(fecha):
    return PagoRetencion.objects.filter(pagos__sesion__fecha=fecha).distinct().count()

def total_retencion_dia(fecha):
    return PagoRetencion.objects.filter(pagos__sesion__fecha=fecha).aggregate(Sum('pagos__valor'))['pagos__valor__sum'] if PagoRetencion.objects.filter(pagos__sesion__fecha=fecha).exists() else 0


def cantidad_depositos_dia(fecha):
    return PagoTransferenciaDeposito.objects.filter(pagos__sesion__fecha=fecha, deposito=True).distinct().count()

def total_deposito_dia(fecha):
    return PagoTransferenciaDeposito.objects.filter(pagos__sesion__fecha=fecha, deposito=True).aggregate(Sum('pagos__valor'))['pagos__valor__sum'] if  PagoTransferenciaDeposito.objects.filter(pagos__sesion__fecha=fecha, deposito=True).exists() else 0

def cantidad_transferencias_dia(fecha):
    return PagoTransferenciaDeposito.objects.filter(pagos__sesion__fecha=fecha, deposito=False).distinct().count()

def total_transferencia_dia(fecha):
    return PagoTransferenciaDeposito.objects.filter(pagos__sesion__fecha=fecha, deposito=False).aggregate(Sum('pagos__valor'))['pagos__valor__sum'] if PagoTransferenciaDeposito.objects.filter(pagos__sesion__fecha=fecha, deposito=False).exists() else 0

def cantidad_notasdecredito_dia(fecha):
    return PagoNotaCredito.objects.filter(pagos__sesion__fecha=fecha).distinct().count()

def total_recibocaja_dia(fecha):
    return PagoReciboCajaInstitucion.objects.filter(pagos__sesion__fecha=fecha).aggregate(Sum('pagos__valor'))['pagos__valor__sum'] if PagoReciboCajaInstitucion.objects.filter(pagos__sesion__fecha=fecha).exists() else 0

def cantidad_recibocaja_dia(fecha):
    return PagoReciboCajaInstitucion.objects.filter(pagos__sesion__fecha=fecha).distinct().count()

def total_notadecredito_dia(fecha):
    return PagoNotaCredito.objects.filter(pagos__sesion__fecha=fecha).aggregate(Sum('pagos__valor'))['pagos__valor__sum'] if PagoNotaCredito.objects.filter(pagos__sesion__fecha=fecha).exists() else 0

def total_dia(fecha):
    return total_efectivo_dia(fecha) + total_cheque_dia(fecha) + total_deposito_dia(fecha) + total_transferencia_dia(fecha) + total_tarjeta_dia(fecha) + total_notadecredito_dia(fecha) + total_recibocaja_dia(fecha) + total_retencion_dia(fecha)

def facturas_total_fecha(fecha):
    return Factura.objects.filter(pagos__sesion__fecha=fecha).distinct().count() if Factura.objects.filter(pagos__sesion__fecha=fecha).exists() else 0

def nc_total_fecha(fecha):
    return NotaCreditoInstitucion.objects.filter(sesioncaja__fecha=fecha).distinct().count() if NotaCreditoInstitucion.objects.filter(sesioncaja__fecha=fecha).exists() else 0

def facturas_total_fecha(fecha):
    return Factura.objects.filter(pagos__sesion__fecha=fecha).distinct().count() if Factura.objects.filter(pagos__sesion__fecha=fecha).exists() else 0

def pagos_total_fecha(fecha):
    if Pago.objects.filter(sesion__fecha=fecha).exists():
        pago = Pago.objects.filter(sesion__fecha=fecha).aggregate(Sum('valor'))['valor__sum']
    else:
        pago = 0
    pagorecibo = total_pagos_recibo_fechas(fecha)
    pagonc = total_pagosncred_fechas(fecha)
    return  pago- pagorecibo -pagonc

def total_pagos_recibo_fechas( fecha):
    return PagoReciboCajaInstitucion.objects.filter(pagos__sesion__fecha=fecha).aggregate(Sum('valor'))['valor__sum'] if PagoReciboCajaInstitucion.objects.filter(pagos__sesion__fecha=fecha).exists() else 0

def total_pagosncred_fechas( fecha):
    return PagoNotaCreditoInstitucion.objects.filter(pagos__sesion__fecha=fecha).aggregate(Sum('valor'))['valor__sum'] if PagoNotaCreditoInstitucion.objects.filter(pagos__sesion__fecha=fecha).exists() else 0

def pagos_nctotal_fecha(fecha):
    return NotaCreditoInstitucion.objects.filter(tipo__id=TIPO_NC_ANULACION,sesioncaja__fecha=fecha).aggregate(Sum('valor'))['valor__sum'] if NotaCreditoInstitucion.objects.filter(tipo__id=TIPO_NC_ANULACION,sesioncaja__fecha=fecha).exists() else 0

def pagos_recibo_fecha(fecha):
    return ReciboCajaInstitucion.objects.filter(sesioncaja__fecha=fecha).aggregate(Sum('valorinicial'))['valorinicial__sum'] if ReciboCajaInstitucion.objects.filter(sesioncaja__fecha=fecha).exists() else 0

def cantidad_facturas_total_fechas(inicio, fin):
    return Factura.objects.filter(pagos__sesion__fecha__gte=inicio, pagos__sesion__fecha__lte=fin).distinct().count() if Factura.objects.filter(pagos__sesion__fecha__gte=inicio, pagos__sesion__fecha__lte=fin).exists() else 0

def total_pagos_rango_fechas(inicio, fin):
    if Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin).exists() :

        pago = Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin).aggregate(Sum('valor'))['valor__sum']
    else:
        pago = 0
    pagorecibo = total_pagosrecibo_rango_fechas(inicio,fin)
    pagonc = total_pagosnotac_rango_fechas(inicio,fin)

    return  pago- pagorecibo -pagonc
def total_pagos_facturas_rango_fechas(inicio, fin):
    if Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin).exists() :
        pago = Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin).aggregate(Sum('valor'))['valor__sum']
    else:
        pago = 0
    return  pago
def pagos_total_fecha2(fecha):
    if Pago.objects.filter(sesion__fecha=fecha).exists():
        pago = Pago.objects.filter(sesion__fecha=fecha).aggregate(Sum('valor'))['valor__sum']
    else:
        pago = 0
    return  pago
def total_pagosrecibo_rango_fechas(inicio, fin):
    return PagoReciboCajaInstitucion.objects.filter(pagos__sesion__fecha__gte=inicio,pagos__sesion__fecha__lte=fin).aggregate(Sum('valor'))['valor__sum'] if PagoReciboCajaInstitucion.objects.filter(pagos__sesion__fecha__gte=inicio, pagos__sesion__fecha__lte=fin).exists() else 0

def total_pagosnotac_rango_fechas(inicio, fin):
    return PagoNotaCreditoInstitucion.objects.filter(pagos__sesion__fecha__gte=inicio,pagos__sesion__fecha__lte=fin).aggregate(Sum('valor'))['valor__sum'] if PagoNotaCreditoInstitucion.objects.filter(pagos__sesion__fecha__gte=inicio, pagos__sesion__fecha__lte=fin).exists() else 0

def total_pagos_rango_fechas_xls(inicio, fin):
    return Pago.objects.filter(pagonotacreditoinstitucion__pagos=None,pagorecibocajainstitucion__pagos=None,sesion__fecha__gte=inicio, sesion__fecha__lte=fin).aggregate(Sum('valor'))['valor__sum'] if Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin,pagonotacreditoinstitucion__pagos=None,pagorecibocajainstitucion__pagos=None).exists() else 0

def total_ncpagos_rango_fechas(inicio, fin):
    return NotaCreditoInstitucion.objects.filter(tipo__id=TIPO_NC_ANULACION,sesioncaja__fecha__gte=inicio, sesioncaja__fecha__lte=fin).aggregate(Sum('valor'))['valor__sum'] if NotaCreditoInstitucion.objects.filter(tipo__id=TIPO_NC_ANULACION,sesioncaja__fecha__gte=inicio, sesioncaja__fecha__lte=fin).exists() else 0

def total_recibo_rango_fechas(inicio, fin):
    pagorecibo=0
    recibo=0
    if ReciboCajaInstitucion.objects.filter(sesioncaja__fecha__gte=inicio, sesioncaja__fecha__lte=fin).exists():
        recibo =  ReciboCajaInstitucion.objects.filter(sesioncaja__fecha__gte=inicio, sesioncaja__fecha__lte=fin).aggregate(Sum('valorinicial'))['valorinicial__sum']

    return  recibo - pagorecibo


#Totales de creditos y deudas (modelo InscripcionEstadistica)

#VALORES DEUDA - TOTAL, ACTIVOS, RETIRADOS E INACTIVOS
def valor_total_deudores():
    return  valor_total_deudores_retirados() +  valor_total_deudores_inactivos() + valor_total_deudores_activos()
    # return InscripcionEstadistica.objects.filter(deuda__gt=0).aggregate(Sum('deuda'))['deuda__sum'] if InscripcionEstadistica.objects.filter(deuda__gt=0).exists() else 0

def valor_total_deudores_retirados():
    s= 0
    for c in Carrera.objects.all():
        if Coordinacion.objects.filter(carrera=c).exists():
            s = s + c.valor_deudores_retirados()
    return  s
    # return InscripcionEstadistica.objects.filter(deuda__gt=0, retirado=True).aggregate(Sum('deuda'))['deuda__sum'] if InscripcionEstadistica.objects.filter(deuda__gt=0, retirado=True).exists() else 0

def valor_total_deudores_inactivos():
    s= 0
    for c in Carrera.objects.all():
        if Coordinacion.objects.filter(carrera=c).exists():
            s = s + c.valor_deudores_inactivos()
    return  s
    # return InscripcionEstadistica.objects.filter(deuda__gt=0, inactivo=True).aggregate(Sum('deuda'))['deuda__sum'] if InscripcionEstadistica.objects.filter(deuda__gt=0, inactivo=True).exists() else 0

def valor_total_deudores_activos():
    s= 0
    for c in Carrera.objects.all():
        if Coordinacion.objects.filter(carrera=c).exists():
            s = s + c.valor_deudores_activos()
    return  s
    # return InscripcionEstadistica.objects.filter(deuda__gt=0, retirado=False, inactivo=False).aggregate(Sum('deuda'))['deuda__sum'] if InscripcionEstadistica.objects.filter(deuda__gt=0, retirado=False, inactivo=False).exists() else 0

#VALORES PORPAGAR - TOTAL, ACTIVOS, RETIRADOS E INACTIVOS
def valor_total_creditos():
    return  valor_total_creditos_retirados()+valor_total_creditos_inactivos()+valor_total_creditos_activos()
    # return InscripcionEstadistica.objects.filter(credito__gt=0).aggregate(Sum('credito'))['credito__sum'] if InscripcionEstadistica.objects.filter(credito__gt=0).exists() else 0

def valor_total_creditos_retirados():
    s= 0
    for c in Carrera.objects.all():
        if Coordinacion.objects.filter(carrera=c).exists():
            s = s + c.valor_total_creditos_retirados()
    return  s
    # return InscripcionEstadistica.objects.filter(credito__gt=0, retirado=True).aggregate(Sum('credito'))['credito__sum'] if InscripcionEstadistica.objects.filter(credito__gt=0, retirado=True).exists() else 0

def valor_total_creditos_inactivos():
     s = 0
     for c in Carrera.objects.all():
        if Coordinacion.objects.filter(carrera=c).exists():
            s = s + c.valor_total_creditos_inactivos()
     return  s
    # return InscripcionEstadistica.objects.filter(credito__gt=0, inactivo=True).aggregate(Sum('credito'))['credito__sum'] if InscripcionEstadistica.objects.filter(credito__gt=0, inactivo=True).exists() else 0

def valor_total_creditos_activos():
     s = 0
     for c in Carrera.objects.all():
        if Coordinacion.objects.filter(carrera=c).exists():
            s = s + c.valor_total_creditos_activos()
     return  s
    # return InscripcionEstadistica.objects.filter(credito__gt=0, retirado=False, inactivo=False).aggregate(Sum('credito'))['credito__sum'] if InscripcionEstadistica.objects.filter(credito__gt=0, retirado=False, inactivo=False).exists() else 0


#NUMERO DE ESTUDIANTES CON DEUDAS - TOTAL, ACTIVOS, RETIRADOS E INACTIVOS
def cantidad_total_deudores():
    return  cantidad_total_deudores_retirados() + cantidad_total_deudores_inactivos() + cantidad_total_deudores_activos()

def cantidad_total_deudores_retirados():
     s = 0
     for c in Carrera.objects.all():
        if Coordinacion.objects.filter(carrera=c).exists():
            s = s + c.cantidad_total_deudores_retirados()
     return  s

def cantidad_total_deudores_inactivos():
    s = 0
    for c in Carrera.objects.all():
        if Coordinacion.objects.filter(carrera=c).exists():
            s = s + c.cantidad_total_deudores_inactivos()
    return  s

def cantidad_total_deudores_activos():
    s = 0
    for c in Carrera.objects.all():
        if Coordinacion.objects.filter(carrera=c).exists():
            s = s + c.cantidad_total_deudores_activos()
    return  s

#NUMERO DE ESTUDIANTES CON CREDITOS POR PAGAR - TOTAL, ACTIVOS, RETIRADOS E INACTIVOS
def cantidad_total_creditos():
    return InscripcionEstadistica.objects.filter(credito__gt=0).count()

def cantidad_total_creditos_retirados():
    return InscripcionEstadistica.objects.filter(credito__gt=0, retirado=True).count()

def cantidad_total_creditos_inactivos():
    return InscripcionEstadistica.objects.filter(credito__gt=0, inactivo=True).count()

def cantidad_total_creditos_activos():
    return InscripcionEstadistica.objects.filter(credito__gt=0, inactivo=False, retirado=False).count()

#NUMERO DE ESTUDIANTES CON DEUDAS Y CREDITOS - TOTAL, ACTIVOS, RETIRADOS E INACTIVOS
def cantidad_total_porcobrar():
    return  cantidad_total_porcobrar_retirados() + cantidad_total_porcobrar_inactivos() + cantidad_total_porcobrar_activos()

def cantidad_total_porcobrar_retirados():
    s = 0
    for c in Coordinacion.objects.filter().exclude(carrera=None):
        s = s + c.cantidad_total_porcobrar_retirados()
    return  s

def cantidad_total_porcobrar_inactivos():
    s = 0
    for c in Coordinacion.objects.filter().exclude(carrera=None):
        s = s + c.cantidad_total_porcobrar_inactivos()
    return  s

def cantidad_total_porcobrar_activos():
    s = 0
    for c in Coordinacion.objects.filter().exclude(carrera=None):
        s = s + c.cantidad_total_porcobrar_activos()
    return  s

#VALORES DE DEUDAS Y CREDITOS - TOTAL, ACTIVOS, RETIRADOS E INACTIVOS
def valor_total_porcobrar():
    return valor_total_deudores() + valor_total_creditos()

def valor_total_porcobrar_retirados():
    return valor_total_deudores_retirados() + valor_total_creditos_retirados()

def valor_total_porcobrar_inactivos():
    return valor_total_deudores_inactivos() + valor_total_creditos_inactivos()

def valor_total_porcobrar_activos():
    return valor_total_deudores_activos() + valor_total_creditos_activos()



#Datos Academicos y Administrativos
def total_matriculados():
    # return Matricula.objects.filter(nivel__cerrado=False, nivel__periodo__activo=True, inscripcion__persona__usuario__is_active=True).exclude(nivel__carrera__nombre='CONGRESO DE PEDAGOGIA').count()
    return  total_matriculados_mujeres() + total_matriculados_hombres()


def total_matriculadosprovinnull():
    return Matricula.objects.filter(nivel__cerrado=False,inscripcion__persona__provincia= None, nivel__periodo__activo=True, inscripcion__persona__usuario__is_active=True).exclude(nivel__carrera__nombre='CONGRESO DE PEDAGOGIA').count()

def total_matriculadoscantonnull():
    return Matricula.objects.filter(nivel__cerrado=False,inscripcion__persona__canton= None, nivel__periodo__activo=True, inscripcion__persona__usuario__is_active=True).exclude(nivel__carrera__nombre='CONGRESO DE PEDAGOGIA').count()

def total_matriculadosfilcanton(fechainicio,fechafin):
    return Matricula.objects.filter(nivel__cerrado=False, nivel__periodo__activo=True, inscripcion__persona__usuario__is_active=True,fecha__gte=fechainicio,fecha__lte=fechafin,inscripcion__persona__canton=None).exclude(nivel__carrera__nombre='CONGRESO DE PEDAGOGIA').count()

def total_matriculados_mujeres():
    s = 0
    for c in Coordinacion.objects.filter():
        s = s + c.cantidad_matriculados_mujeres()
    return  s

def total_matriculados_mujeresfil(fechainicio,fechafin):
    return Matricula.objects.filter(nivel__cerrado=False, nivel__periodo__activo=True, inscripcion__persona__usuario__is_active=True, inscripcion__persona__sexo=SEXO_FEMENINO,fecha__gte=fechainicio,fecha__lte=fechafin).exclude(nivel__carrera__nombre='CONGRESO DE PEDAGOGIA').count()

def total_matriculados_hombres():
    # return Matricula.objects.filter(nivel__cerrado=False, nivel__periodo__activo=True, inscripcion__persona__usuario__is_active=True, inscripcion__persona__sexo=SEXO_MASCULINO).exclude(nivel__carrera__nombre='CONGRESO DE PEDAGOGIA').count()
    s = 0
    for c in Coordinacion.objects.filter().exclude(carrera=None):
        s = s + c.cantidad_matriculados_hombres()
    return  s

def total_matriculados_hombresfil(fechainicio,fechafin):
    return Matricula.objects.filter(nivel__cerrado=False, nivel__periodo__activo=True, inscripcion__persona__usuario__is_active=True, inscripcion__persona__sexo=SEXO_MASCULINO,fecha__gte=fechainicio,fecha__lte=fechafin).exclude(nivel__carrera__nombre='CONGRESO DE PEDAGOGIA').count()

def cantidad_matriculados_beca():
    s = 0
    for c in Coordinacion.objects.filter().exclude(carrera=None):
        s = s +  Matricula.objects.filter(becado=True,nivel__cerrado=False, nivel__periodo__activo=True, inscripcion__persona__usuario__is_active=True, inscripcion__carrera__in=c.carrera.all()).count()
    return  s
    # return Matricula.objects.filter(becado=True,nivel__cerrado=False, inscripcion__persona__usuario__is_active=True ,nivel__periodo__activo=True).exclude(nivel__carrera__nombre='CONGRESO DE PEDAGOGIA').count()

def cantidad_matriculados_discapacidad():
    s = 0
    for c in Coordinacion.objects.filter().exclude(carrera=None):
        s = s + Matricula.objects.filter(inscripcion__tienediscapacidad=True,nivel__cerrado=False, nivel__periodo__activo=True, inscripcion__persona__usuario__is_active=True, inscripcion__carrera__in=c.carrera.all()).count()
    # return Matricula.objects.filter(inscripcion__tienediscapacidad=True,nivel__cerrado=False, inscripcion__persona__usuario__is_active=True ,nivel__periodo__activo=True).exclude(nivel__carrera__nombre='CONGRESO DE PEDAGOGIA').count()
    return  s
def total_matriculados_becasdiscapacidad():
    return cantidad_matriculados_beca()+ cantidad_matriculados_discapacidad()

#Matriculados por rango de edades
def matriculados_menor_30():
    s = 0
    for c in Coordinacion.objects.filter().order_by('id'):
        s = s + c.matriculados_menor_30()
            # InscripcionEstadistica.objects.filter(edad__gt=0, edad__lte=30, matriculado=True, inscripcion__persona__usuario__is_active=True).exclude(inscripcion__carrera__id__in=CARRERAS_ID_EXCLUIDAS_INEC).count()
    return  s

def matriculados_31_40():
    s = 0
    for c in Coordinacion.objects.filter():
       s = s + c.matriculados_31_40()
    return  s
    # return InscripcionEstadistica.objects.filter(edad__gt=30, edad__lte=40, matriculado=True, inscripcion__persona__usuario__is_active=True).exclude(inscripcion__carrera__id__in=CARRERAS_ID_EXCLUIDAS_INEC).count()

def matriculados_41_50():
    s = 0
    for c in Coordinacion.objects.filter():
        s = s + c.matriculados_41_50()
    return  s
    # return InscripcionEstadistica.objects.filter(edad__gt=40, edad__lte=50, matriculado=True, inscripcion__persona__usuario__is_active=True).exclude(inscripcion__carrera__id__in=CARRERAS_ID_EXCLUIDAS_INEC).count()

def matriculados_51_60():
    s = 0
    for c in Coordinacion.objects.filter():
        s = s + c.matriculados_51_60()
    return  s
    # return InscripcionEstadistica.objects.filter(edad__gt=50, edad__lte=60, matriculado=True, inscripcion__persona__usuario__is_active=True).exclude(inscripcion__carrera__id__in=CARRERAS_ID_EXCLUIDAS_INEC).count()

def matriculados_mayor_61():
    s = 0
    for c in Coordinacion.objects.filter():
        s = s + c.matriculados_mayor_61()
    return  s
    # return InscripcionEstadistica.objects.filter(edad__gt=60, matriculado=True, inscripcion__persona__usuario__is_active=True).exclude(inscripcion__carrera__id__in=CARRERAS_ID_EXCLUIDAS_INEC).count()

def total_matriculados_edades():
    return matriculados_menor_30()+ matriculados_31_40()+ matriculados_41_50()+ matriculados_51_60()+ matriculados_mayor_61()


# Metodo para obtener el Ip desde donde se conectan los usuarios
def ip_client_address(request):
    try:
        # case server externo
        client_address = request.META['HTTP_X_FORWARDED_FOR']
    except:
        # case localhost o 127.0.0.1
        client_address = request.META['REMOTE_ADDR']
    return client_address

def log_audit_action(request, instance, mensaje):
    from django.contrib.admin.models import CHANGE
    """
    Registra una entrada de auditoría en el sistema de logs de Django.

    :param request: El objeto request, que contiene el usuario y la dirección IP.
    :param instance: La instancia del modelo que ha sido modificada.
    :param mensaje: El mensaje que describe el cambio.
    """
    client_address = ip_client_address(request)

    LogEntry.objects.log_action(
        user_id=request.user.pk,
        content_type_id=ContentType.objects.get_for_model(instance).pk,
        object_id=instance.id,
        object_repr=force_str(instance),
        action_flag=CHANGE,
        change_message=f"{mensaje} {instance.__str__()} ({client_address})"
    )

@login_required(redirect_field_name='ret', login_url='/login')
def changeuser(request):
    data = {}
    addUserData(request, data)
    if data['persona'].usuario.is_superuser or data['persona'].usuario.groups.filter(id__in=[RECTORADO_GROUP_ID, SISTEMAS_GROUP_ID, SECRETARIAGENERAL_GROUP_ID, COORDINACION_ACADEMICA_GROUP_ID,TICS_GROUP_ID]).exists():
        user = User.objects.get(pk=request.GET['id'])
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request,user)
        persona = Persona.objects.get(usuario=user)

        request.session['persona'] = persona
    return HttpResponseRedirect('/')

def reestablecer(request):
    data = {}
    addUserData(request, data)
    if Persona.objects.filter(pk=request.GET['persona']).exists():
        p = Persona.objects.get(pk=request.GET['persona'])
        if p.reestablecer == True and p.codigo == request.GET['clave'] :

    # if data['persona'].usuario.is_superuser or data['persona'].usuario.groups.filter(id__in=[RECTORADO_GROUP_ID, SISTEMAS_GROUP_ID, SECRETARIAGENERAL_GROUP_ID, COORDINACION_ACADEMICA_GROUP_ID]).exists():
            user = User.objects.get(pk=p.usuario.id)
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request,user)
            persona = Persona.objects.get(usuario=user)

            request.session['persona'] = persona
            return HttpResponseRedirect('/pass')
        else:
            return HttpResponseRedirect("/login.html?reestablecer_pass&error=11")

# OPCION PARA CAMBIAR LA CLAVE PARA EL DIRECTORY
def cambiarclaveAD(request):
    if request.method=='POST':
        action = request.POST['action']
        if action == 'consultuser':
            try:
                if User.objects.filter(username=request.POST['user']).exists():
                    return HttpResponse(json.dumps({'result': 'ok','url':'https://sga.itb.edu.ec/','sistema':'sga'}), content_type="application/json")
                else:
                     cn = psycopg2.connect("host=10.10.9.45 dbname=sgaonline user=aok password=R0b3rt0.1tb$")
                     cur = cn.cursor()
                     cur.execute("select * from auth_user where username='"+str(request.POST['user'])+"'")
                     dato = cur.fetchall()
                     cur.close()
                     if len(dato)>0:
                        return HttpResponse(json.dumps({'result': 'ok','url':'https://sgaonline.itb.edu.ec/','sistema':'sgaonline'}), content_type="application/json")

                     db = psycopg2.connect("host=10.10.9.45 dbname=conduccion user=postgres password=Itb$2019")
                     cursor = db.cursor()
                     cursor.execute("select * from auth_user where username='"+str(request.POST['user'])+"'")
                     dato = cursor.fetchall()
                     db.close()
                     if len(dato) > 0:
                        return HttpResponse(json.dumps({'result': 'ok','url':'https://sgaonline.itb.edu.ec/','sistema':'sgaonline'}), content_type="application/json")
                return HttpResponse(json.dumps({'result': 'bad','error':'El usuario no existe'}), content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad','error':'Error vuelva a ingresar el usuario'}), content_type="application/json")
        elif action == 'cambiarclave':
            try:
                if request.POST['sistema'] == 'sga':
                    user = authenticate(username=string.lower(request.POST['user']), password=request.POST['passante'])
                    if user is not None:
                        if user.is_active:
                            login(request,user)
                            user.set_password(request.POST['passnew'])
                            if DEFAULT_PASSWORD == 'itb':
                                validacambio = False
                                if Persona.objects.filter(usuario=user).exists():
                                    persona = Persona.objects.filter(usuario=user)[:1].get()
                                    scriptresponse = ''
                                    mensajesc = ''
                                    listnombre = []
                                    try:
                                        datos = {"identity": user.username,
                                         "NewPassword": request.POST['passnew']}
                                        consulta = requests.put(IP_SERVIDOR_API_DIRECTORY+'/changep',json.dumps(datos), verify=False,timeout=4)
                                        if consulta.status_code == 200:
                                            validacambio = True
                                            datos = consulta.json()
                                    except requests.Timeout:
                                        print("Error Timeout")

                                    except requests.ConnectionError:
                                        print("Error Conexion")
                            logout(request)
                            return HttpResponse(json.dumps({'result': 'ok','mensaje': u'La contraseña de sga.itb.edu.ec y su correo fue cambiada correctamente'}), content_type="application/json")
                        login(request,user)
                        logout(request)
                        return HttpResponse(json.dumps({'result': 'bad','error':'el usuario no esta activo'}), content_type="application/json")
                    return HttpResponse(json.dumps({'result': 'bad','error':u'Contraseña no valida'}), content_type="application/json")
                else:
                    try:
                        datos = requests.post('https://sgaonline.itb.edu.ec/api',{'a': 'cambiarclave', 'user': request.POST['user'], 'passnew': request.POST['passnew'],
                                                                                  'passante':request.POST['passante'],'passveri':request.POST['passveri']},timeout=15,verify=False)
                    except requests.Timeout:
                        print("Error Timeout")
                        return HttpResponse(json.dumps({'result': 'bad','error': 'Error por Timeout'}),content_type="application/json")
                    except requests.ConnectionError:
                        print("Error Conexion")
                        return HttpResponse(json.dumps({'result': 'bad','error': 'Error por Timeout'}),content_type="application/json")
                    if datos.status_code == 200:
                      datos=datos.json()
                      if datos['result']=='ok':
                          return HttpResponse(json.dumps({'result': datos['result'],'mensaje':datos['mensaje']}), content_type="application/json")
                      return HttpResponse(json.dumps({'result': datos['result'],'error':datos['error']}), content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad','error':u'Error al cambiar la contraseña vuelva a intentarlo'}), content_type="application/json")

        return HttpResponse(json.dumps({'result': 'bad','error':'No existe ninguna accion'}), content_type="application/json")
    else:
        data = {'title': 'Cambio Clave', 'form': ReestablecerClaveForm()}
        # addUserData(request,data)
        if 'error' in request.GET:
            errorNo = request.GET['error']
            if errorNo=='keys':
                data['formerror'] = 'La clave anterior no coincide'
            elif errorNo=='form':
                data['formerror'] = 'Existe un error en los datos del formulario'
        data['request'] = request
        return render(request ,"cambioclaveAD.html" ,  data)

def cambio_clave_AD(persona,anterior,nueva):
    usertipo= "ADMINISTRATIVO"
    if Inscripcion.objects.filter(persona=persona).exists():
        usertipo= "INSCRIPCION"
    if Profesor.objects.filter(persona=persona).exists():
        usertipo= "DOCENTE"
    newuser= persona.usuario.username
    datos = {
         "identity": persona.usuario.username,
         "NewPassword": nueva
            }
    if DEFAULT_PASSWORD == 'itb' and ACTIVA_ADD_EDIT_AD:
        try:
            consulta = requests.put('https://api.itb.edu.ec:4443/changep',json.dumps(datos), verify=False,timeout=4)
            if consulta.status_code == 200:
                datos = consulta.json()
                return 'Su contrasena fue modificada'
        except requests.Timeout:
            print("Error Timeout")
            return HttpResponse(json.dumps({"result":"bad","message": "Error por en tiempo de espera al api, contactese con el administrador"}),
                                content_type="application/json")
        except requests.ConnectionError:
            print("Error Conexion")
            return HttpResponse(json.dumps({"result":"bad","message": "Error de conexion con el servidor del correo"}),
                            content_type="application/json")


def valida_correo_institucional(request):
    if Persona.objects.filter(emailinst__icontains=(request.POST['email']).lower()).exists():
        return HttpResponse(json.dumps({'result': 'ok'}), content_type="application/json")
    else:
        return HttpResponse(json.dumps({'result': 'bad', 'message': 'No tiene correo institucional'}),
                            content_type="application/json")

def add_usuario_AD(persona):
    print('INGRESO A ADD USUARIO DIER')
    print(persona)
    tipo = TipoIncidencia.objects.get(pk=11)
    usertipo= "ADMINISTRATIVO"
    try:
        if Inscripcion.objects.filter(persona=persona).exists():
            usertipo= "INSCRIPCION"
            EmailAddress = persona.usuario.username+'@itb.edu.ec'
        elif Profesor.objects.filter(persona=persona).exists():
            usertipo= "DOCENTE"
            EmailAddress = persona.usuario.username+'@itb.edu.ec'
        else:
            EmailAddress = persona.usuario.username+'@bolivariano.edu.ec'
            persona.emailinst= EmailAddress
            persona.save()
        try:
            nombresuario = persona.usuario.username
            print(('antes de consulta tosa '+nombresuario))
            print(('antes de 2'+ IP_SERVIDOR_API_DIRECTORY+'/api?Identity=' + persona.usuario.username))
            consulta = requests.get(IP_SERVIDOR_API_DIRECTORY+'/api?Identity=' + persona.usuario.username, timeout=5, verify=False)
            print(("consulta"))
            print(consulta)
            if consulta.status_code == 200:
                datos = consulta.json()
                print('datos despues de consult ')
                print(datos)
                if 'msg_corto' in datos:
                    if datos['msg_corto'] == 'Usuario NO existe':
                        numrep = ''
                        if persona.cedula:
                            if Persona.objects.filter(cedula=persona.cedula).count()>1:
                                numrep = Persona.objects.filter(cedula=persona.cedula).count()
                        elif persona.pasaporte:
                            if Persona.objects.filter(pasaporte=persona.pasaporte).count()>1:
                                numrep = Persona.objects.filter(pasaporte=persona.pasaporte).count()

                        UserPrincipalName = persona.usuario.username
                        # EmailAddress = persona.emailinst
                        GivenName = persona.nombres+' '+str(numrep)
                        MobilePhone = ""
                        if persona.telefono:
                            MobilePhone = persona.telefono
                        Surname = persona.apellido1 + " " + persona.apellido2
                        datos = { "username": UserPrincipalName,
                                 "AccountPassword": NEW_PASSWORD,
                                 "GivenName": GivenName,
                                 "Surname": Surname,
                                 "Description" : usertipo,
                                 "correo" : EmailAddress
                                 }
                        try:
                            print('creacion de directory para '+UserPrincipalName)
                            consulta = requests.post(IP_SERVIDOR_API_DIRECTORY+'/create', json.dumps(datos), timeout=7, verify=False)
                            print('consulta para '+UserPrincipalName)
                            print(consulta)
                            print(consulta.json())
                            if consulta.status_code == 200:
                                datos = consulta.json()
                                print('directory daos  para '+UserPrincipalName)
                                print(datos)
                                if 'msg_corto' in datos:
                                    hoy = datetime.now().today()
                                    contenido = "USUARIO EN ACTIVE DIRECTORY"
                                    send_html_mail("ACTIVE DIRECTORY",
                                                   "emails/addactivedirectory.html",
                                                   {'nombres': persona.nombre_completo(),'mensaje': datos['msg_corto'],'tipo': usertipo, 'fecha': hoy, 'contenido': contenido},
                                                   tipo.correo.split(","))
                                    if datos['msg_corto'] != 'Usuario NO Creado':
                                        persona.activedirectory = True
                                        persona.save()
                                else:
                                    hoy = datetime.now().today()
                                    contenido = "USUARIO EN ACTIVE DIRECTORY"
                                    send_html_mail("ACTIVE DIRECTORY",
                                                   "emails/addactivedirectory.html",
                                                   {'nombres': persona.nombre_completo(),'mensaje': "ERROR AL CREAR USUARIO",'tipo': usertipo, 'fecha': hoy, 'contenido': contenido},
                                                   tipo.correo.split(","))
                        except requests.Timeout:
                            print("Error Timeout al guardar")
                            hoy = datetime.now().today()
                            contenido = "NO SE CREO USUARIO EN ACTIVE DIRECTORY"
                            send_html_mail("ERROR ACTIVE DIRECTORY",
                                           "emails/addactivedirectory.html",
                                           {'nombres': persona.nombre_completo(),'mensaje': "ERROR POR TIMEOUT DESDE GUARDAR",'tipo': usertipo, 'fecha': hoy, 'contenido': contenido},
                                           tipo.correo.split(","))
                        except requests.ConnectionError:
                                print("Error ConnectionError al guardar")
                                hoy = datetime.now().today()
                                contenido = "NO SE CREO USUARIO EN ACTIVE DIRECTORY"
                                send_html_mail("ERROR ACTIVE DIRECTORY",
                                               "emails/addactivedirectory.html",
                                               {'nombres': persona.nombre_completo(), 'mensaje': "ERROR POR CONEXION DESDE GUARDAR",
                                                'tipo': usertipo, 'fecha': hoy, 'contenido': contenido},
                                               tipo.correo.split(","))
                        except Exception as e:
                            print(e)
                            pass
                    else:
                        persona.activedirectory = True
                        persona.save()
                else:
                    persona.activedirectory = True
                    persona.save()
                return 'Usuario creado'
                print("REALIZO CORRECTAMENTE DIRECTORY")
        except requests.Timeout:
            print("Error Timeout en la busqueda usuario:"+str(persona.usuario.username))
            hoy = datetime.now().today()
            contenido = "NO SE CREO USUARIO EN ACTIVE DIRECTORY"
            send_html_mail("ERROR ACTIVE DIRECTORY",
                           "emails/addactivedirectory.html",
                           {'nombres': persona.nombre_completo(),'mensaje': "ERROR POR TIMEOUT  DESDE BUSQUEDA",'tipo': usertipo, 'fecha': hoy, 'contenido': contenido},
                           tipo.correo.split(","))
        except requests.ConnectionError:
            print("Error ConnectionError  en la busqueda")
            hoy = datetime.now().today()
            contenido = "NO SE CREO USUARIO EN ACTIVE DIRECTORY"
            send_html_mail("ERROR ACTIVE DIRECTORY",
                           "emails/addactivedirectory.html",
                           {'nombres': persona.nombre_completo(), 'mensaje': "ERROR POR CONEXION  DESDE BUSQUEDA",
                            'tipo': usertipo, 'fecha': hoy, 'contenido': contenido},
                           tipo.correo.split(","))
        except Exception as e:
            print(e)
            pass

    except Exception as e:
        print("ERROR EN LA EXCEPCION GENERAL "+str(e)+" usuario:"+str(persona.usuario.username))
        hoy = datetime.now().today()
        contenido = "USUARIO EN ACTIVE DIRECTORY"
        send_html_mail("ACTIVE DIRECTORY",
                       "emails/addactivedirectory.html",
                       {'nombres': persona.nombre_completo(), 'mensaje': "ERROR AL CREAR O IDENTIFICAR AL USUARIO EN EL DIRECTORY", 'tipo': usertipo,
                        'fecha': hoy, 'contenido': contenido},
                       tipo.correo.split(","))
    # listnombre = []
    # import subprocess
    # # if you want output
    # userdata = {"nombre": nombre, "apellido": apellido, "password": password,
    #             "usertipo": usertipo, "newuser": newuser}
    # print("VER DATA USERDATA")
    # print(userdata)
    # # proc = subprocess.Popen("C:/xampp/php/php.exe " + SITE_ROOT + "/scriptphpadd.php " + json.dumps(userdata), shell=True, stdout=subprocess.PIPE).stdout.read()
    # try:
    #     script_response1 = subprocess.check_output(["/bin/php", MEDIA_ROOT + "/scriptphp/scriptphpadd.php",json.dumps(userdata)])
    #     scriptresponse = str(script_response1.decode())
    #     if 'Usuario creado' in scriptresponse:
    #         print('usuari se creo')
    #         # cambio_clave_AD(persona,password,password)
    #         if usertipo == "ADMINISTRATIVO":
    #             correo = persona.usuario.username+'@bolivariano.edu.ec'
    #         else:
    #             correo = persona.usuario.username+'@itb.edu.ec'
    #         persona.emailinst = correo
    #         persona.save()
    #         if not persona.activedirectory:
    #             persona.activedirectory = True
    #             persona.save()
    #     if '19<br />LDAP-Error: Constraint violation' in scriptresponse:
    #         if not persona.activedirectory:
    #             persona.activedirectory = True
    #             persona.save()
    #             scriptresponse = ''
    #     print("print(RESPONSE "+script_response1))
    # except Exception as ex:
    #     scriptresponse = "Error Ex " + str(ex)
    # listnombre.append((persona.nombre_completo(),scriptresponse,usertipo))
    # # script_response = proc.stdout.read()
    # return scriptresponse, listnombre

@login_required(redirect_field_name='ret', login_url='/login')
def template(request):
    data = {}
    addUserData(request, data)
    try:
        return render(request,"layout/panelbs.html" ,  data)
    except Exception as ex:
        return render(request, f"<p>{ex.__str__()}</p>")
