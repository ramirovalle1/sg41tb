from datetime import datetime,timedelta
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.contrib.contenttypes.models import ContentType
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
from decorators import secure_module
from sga.commonviews import addUserData, ip_client_address
from sga.forms import SolicitudSecretariaDocenteForm, PersonalSolicitudForm, SeguimientoEspecieForm, AprobacionSolicitudForm
from sga.models import SolicitudSecretariaDocente, AsistAsuntoEstudiant, IncidenciaAsignada, DepartamentoIncidenciaAsig,SolicitudesGrupo, TipoSolicitudSecretariaDocente, GrupoCorreo, Persona, Inscripcion, ModuloGrupo, AsistenteDepartamento, Departamento, elimina_tildes, SesionCaja, HorarioAsistenteSolicitudes, DatosTransfereciaDeposito, CuentaBanco, PagoTransferenciaDeposito, convertir_fecha
from django.db.models.query_utils import Q
from settings import EMAIL_ACTIVE, PROFESORES_GROUP_ID, ALUMNOS_GROUP_ID, ID_DEPARTAMENTO_ASUNTO_ESTUDIANT, SISTEMAS_GROUP_ID, ID_TIPO_SOLICITUD
from sga.tasks import gen_passwd, send_html_mail
import json
from django.http import HttpResponse, HttpResponseRedirect

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
@secure_module
def view(request):
    """

    :param request:
    :return:
    """
    data = {'title': 'Solicitudes de Estudiantes'}
    addUserData(request, data)
    if request.method=='POST':
        if 'action' in request.POST:
            action = request.POST['action']
            if action=='autorizar':
               try:

                   solicitud = SolicitudSecretariaDocente.objects.filter(pk=request.POST['ids'])[:1].get()

                   if request.POST['opcion'] == 'adicionar':
                       asistente = AsistenteDepartamento.objects.filter(persona__usuario=request.user)[:1].get()
                   else :
                       asistente =   AsistenteDepartamento.objects.filter(persona__usuario=solicitud.usuario)[:1].get()
                   if request.POST['autorizado'] == '1':
                       cuenta = CuentaBanco.objects.filter(pk=request.POST['cuentabanco'])[:1].get()
                       if request.POST['opcion'] == 'adicionar':
                           # asistente = AsistenteDepartamento.objects.filter(persona__usuario=request.user)[:1].get()
                           datos = DatosTransfereciaDeposito(solicitud=solicitud,
                                                             referencia = request.POST['referencia'],
                                                             fecha = datetime.now(),
                                                             cuentabanco = cuenta,
                                                             fechadeposito = convertir_fecha(request.POST['fechadeposito']),
                                                             valor = request.POST['valor'])
                           datos.save()
                           client_address = ip_client_address(request)
                           LogEntry.objects.log_action(
                           user_id         = request.user.pk,
                           content_type_id = ContentType.objects.get_for_model(datos).pk,
                           object_id       = datos.id,
                           object_repr     = force_str(datos),
                           action_flag     = ADDITION,
                           change_message  = 'Adicionada Aprobacion de Solicitud (' + client_address + ')' )
                       else:
                           datos = DatosTransfereciaDeposito.objects.filter(pk=request.POST['idresol'])[:1].get()
                           datos.referencia = request.POST['referencia']
                           datos.fecha = datetime.now()
                           datos.cuentabanco = cuenta
                           datos.valor = request.POST['valor']
                           datos.fechadeposito = convertir_fecha(request.POST['fechadeposito'])
                           datos.save()
                           client_address = ip_client_address(request)
                           LogEntry.objects.log_action(
                           user_id         = request.user.pk,
                           content_type_id = ContentType.objects.get_for_model(datos).pk,
                           object_id       = datos.id,
                           object_repr     = force_str(datos),
                           action_flag     = ADDITION,
                           change_message  = 'Editada Aprobacion de Solicitud (' + client_address + ')' )
                       if request.POST['deposito'] == '1':
                           datos.deposito = True

                       if request.POST['transferencia'] == '1':
                           datos.deposito = False

                       datos.save()

                       solicitud.autorizado = True
                       solicitud.save()
                   else:
                       if DatosTransfereciaDeposito.objects.filter(solicitud=solicitud).exists():
                           datos = DatosTransfereciaDeposito.objects.filter(solicitud=solicitud)[:1].get()
                           datos.delete()
                       solicitud.autorizado = False
                       solicitud.observacion = request.POST['motivoautoriza']
                       solicitud.resolucion ='SOLICITUD NO APROBADA'
                       solicitud.fechacierre = datetime.now()
                       solicitud.hora = datetime.now().time()
                       solicitud.usuario = request.user
                       solicitud.personaasignada =  asistente.persona
                       solicitud.cerrada = True
                   solicitud.asistenteautoriza = asistente
                   solicitud.motivoautoriza = request.POST['motivoautoriza']


                   solicitud.save()
                   client_address = ip_client_address(request)
                   LogEntry.objects.log_action(
                        user_id=request.user.pk,
                        content_type_id=ContentType.objects.get_for_model(solicitud).pk,
                        object_id=solicitud.id,
                        object_repr=force_str(solicitud),
                        action_flag=ADDITION,
                        change_message='Datos de Solicitud Aprobados '+' (' + client_address + ')')
                   return HttpResponse(json.dumps({'result':'ok','solicitud':solicitud.id}),content_type="application/json")
               except Exception as e:

                    return HttpResponse(json.dumps({'result':'bad','error':str(e)}),content_type="application/json")


            elif action=='verificareferencia':
                if request.POST['numero'] != '' and request.POST['ctabanco'] != '':
                    ref=request.POST['numero'].upper()
                    solicitud = SolicitudSecretariaDocente.objects.filter(pk=request.POST['ids'])[:1].get()
                    ctbanco=CuentaBanco.objects.filter(pk=request.POST['ctabanco'])[:1].get()
                    i = Inscripcion.objects.filter(persona=solicitud.persona)[:1].get()
                    if PagoTransferenciaDeposito.objects.filter(referencia=ref,cuentabanco=ctbanco).exists():
                        return HttpResponse(json.dumps({'result':'bad'}),content_type="application/json")
                    else:
                        if  DatosTransfereciaDeposito.objects.filter(referencia=ref,cuentabanco=ctbanco).exists():
                            return HttpResponse(json.dumps({'result':'bad'}),content_type="application/json")
                        else:
                            return HttpResponse(json.dumps({'result':'ok'}),content_type="application/json")
                else:
                    return HttpResponse(json.dumps({'result':'bad2'}),content_type="application/json")

            return HttpResponseRedirect("/revisionsolicitudpagos")
    else:
        data = {'title': 'Solicitudes de Estudiantes'}
        addUserData(request, data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='cerrar':
                solicitud = SolicitudSecretariaDocente.objects.get(pk=request.GET['id'])
                solicitud.fechacierre = datetime.now()
                solicitud.cerrada = True
                solicitud.save()
                solicitud.mail_subject_respuesta()
                return HttpResponseRedirect("/solicitudes")
            # elif action == 'actualizahora':
            #     c=0
            #     for s in SolicitudSecretariaDocente.objects.filter(cerrada=True).exclude(fechaasignacion=None).exclude(solicitudestudiante=None):
            #         try:
            #             log = LogEntry.objects.filter(object_id=s.id,change_message__icontains='Solicitud Alumno finalizado')[:1].get()
            #             s.hora=log.action_time.time()
            #             s.save()
            #             c=c+1
            #             print(s)
            #         except Exception as e:
            #             print(e)
            #             pass
            #     print(c)
            elif action=='verasistentes':
                data = {}
                data['asistentes'] = IncidenciaAsignada.objects.filter(solicitusecret__id=request.GET['idinfo'])
                return render(request ,"asuntoestudiantil/verasistentes.html" ,  data)

            elif action == 'vergestion':
                solicitud = SolicitudSecretariaDocente.objects.filter(pk=request.GET['ide'])[:1].get()
                seguimiento= IncidenciaAsignada.objects.filter(solicitusecret=solicitud).order_by('-fecha')

                data['solicitud']=solicitud
                data['seguimiento']=seguimiento
                return render(request ,"solicitudes/detalle_gestion.html" ,  data)

            elif action=='comentar':
                data['title'] = 'Comentar Solicitud a Secretaria Docente'
                solicitud = SolicitudSecretariaDocente.objects.get(pk=request.GET['id'])
                solicitud.save()
                data['form'] = SolicitudSecretariaDocenteForm(instance=solicitud)
                data['solicitud'] = solicitud
                return render(request ,"solicitudes/comentarbs.html" ,  data)

        else:
            # solicitudes=None
            tipoid = None
            todos = None
            if 's' in request.GET:
                solicitudes = SolicitudSecretariaDocente.objects.filter(solicitudestudiante__tipoe__id=ID_TIPO_SOLICITUD).exclude(solicitudestudiante=None).order_by('-fecha','-hora')
            else:
                solicitudes = SolicitudSecretariaDocente.objects.filter(solicitudestudiante__tipoe__id=ID_TIPO_SOLICITUD).exclude(solicitudestudiante=None).order_by('-fecha','-hora')
                if AsistenteDepartamento.objects.filter(persona__usuario=request.user).exists() and not request.user.has_perm('sga.change_asistentedepartamento') :
                    persona = Persona.objects.get(usuario=request.user)
                    solicitudes = solicitudes.filter(personaasignada=persona,asistenteautoriza=None).order_by('fecha')

            op=''
            if 'op' in request.GET:
                data['op']= request.GET['op']
                if  request.GET['op'] == 'p':
                    solicitudes = solicitudes.filter(asistenteautoriza=None).exclude(cerrada=True)
                if  request.GET['op'] == 'pf':
                    ids=DatosTransfereciaDeposito.objects.filter(solicitud__autorizado=True,solicitud__asistenteautoriza__persona__usuario=request.user,pago=None).values('solicitud')
                    solicitudes = SolicitudSecretariaDocente.objects.filter(id__in=ids).exclude(cerrada=True)
                if  request.GET['op'] == 'c':
                    solicitudes = solicitudes.filter(cerrada=True)
                if  request.GET['op'] == 'g':
                    solicitudes = solicitudes.filter().exclude(asistenteautoriza=None)

            if 's' in request.GET:
                search = request.GET['s']
                if len(search) >0:
                    ss = search.split(' ')
                    data['search']=search
                    try:
                        if int(search):
                            numero = int(search)
                            solicitudes = solicitudes.filter(Q (id=numero)).order_by('cerrada','-fecha','-hora')

                    except Exception as e:
                        while '' in ss:
                            ss.remove('')
                        if len(ss)==1:
                            solicitudes = solicitudes.filter(Q (persona__apellido1__icontains=search)).order_by('cerrada','-fecha','-hora')
                        else:
                            solicitudes = solicitudes.filter(Q(persona__apellido1__icontains=ss[0]) & Q (persona__apellido2__icontains=ss[1])|Q (persona__cedula__icontains=ss[0])|Q (persona__pasaporte__icontains=ss[0]) |Q (datostransfereciadeposito__referencia=ss[0])).order_by('cerrada','-fecha','-hora')
            paging = MiPaginador(solicitudes, 30)
            p = 1
            try:
                if 'page' in request.GET:
                    p = int(request.GET['page'])
                page = paging.page(p)
            except:
                page = paging.page(1)

            data['paging'] = paging
            data['rangospaging'] = paging.rangos_paginado(p)
            data['page'] = page
            data['solicitudes'] = page.object_list
            data['usuario'] = request.user
            data['fechaactual'] = datetime.now().date()
            data['form'] = AprobacionSolicitudForm(initial={'fechadeposito': datetime.now().strftime("%d-%m-%Y")})

            return render(request ,"revisionsolicitud/solicitudesbs.html" ,  data)