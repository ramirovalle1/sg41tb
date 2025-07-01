from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.shortcuts import render
from decorators import secure_module
from settings import SECRETARIA_EMAIL, EMAIL_ACTIVE, VALIDAR_ENTRADA_SISTEMA_CON_DEUDA, VALIDA_DEUDA_EXAM_ASIST, ID_TIPO_SOLICITUD, SISTEMAS_GROUP_ID
from sga.commonviews import addUserData
from django.forms import model_to_dict
from sga.tasks import send_html_mail
from sga.forms import SolicitudSecretariaAlumnosForm
from sga.models import SolicitudSecretariaDocente, Inscripcion, TipoSolicitudSecretariaDocente, SolicitudesGrupo, ModuloGrupo
from django.template import RequestContext


@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    if request.method=='POST':
        if 'action' in request.POST:
            action = request.POST['action']
            if action=='solicitar':
                adjunto=False
                try:
                    f = SolicitudSecretariaAlumnosForm(request.POST,request.FILES)
                    if f.is_valid():
                        if not 'pr' in request.POST:
                            solicitud = SolicitudSecretariaDocente(persona=request.session['persona'],
                                                                   tipo=f.cleaned_data['tipo'],
                                                                   descripcion=f.cleaned_data['descripcion'],
                                                                   fecha = datetime.now(),
                                                                   hora = datetime.now().time(),
                                                                   cerrada = False)
                            solicitud.save()
                        else:
                            tipoespecie = TipoSolicitudSecretariaDocente.objects.get(pk=ID_TIPO_SOLICITUD)
                            solicitud = SolicitudSecretariaDocente(persona=request.session['persona'],
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
                        inscripcion=Inscripcion.objects.filter(persona=solicitud.persona_id)[:1].get()

                    # f.instance.persona = request.session['persona']
                    # f.instance.fecha = datetime.now()
                    # f.instance.hora = datetime.now().time()
                    # f.instance.cerrada = False
                    # if f.is_valid():
                    #     f.save()

                        if EMAIL_ACTIVE:
                            # f.instance.mail_subject_nuevo()
                            #OCastillo 17-05-2019
                            gruposexcluidos = [SISTEMAS_GROUP_ID]
                            lista=''

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
                                    if solicitud.tipo.sistema==True:
                                        grupo_solicitud=SolicitudesGrupo.objects.filter(tiposolic=solicitud.tipo,todas_carreras=True).values('grupo')
                                    else:
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
                            # descripcion = solicitud.descripcion
                            # if adjunto:
                            #      descripcion = descripcion +   " Archivo adjunto"
                            #     # descripcion = solicitud.descripcion +  "Estudiante ha realizado solicitud. Revisar el detalle de la misma en el Modulo Solicitudes de Alumnos. Archivo adjunto"
                            send_html_mail(contenido,
                                "emails/nuevasolicitud.html", {'d': solicitud, 'fecha': hoy,'contenido': contenido,'adjunto':adjunto,'opcion':'2'},lista.split(','))

                except Exception as e:
                    print(str(e))
                    return HttpResponseRedirect("/alu_solicitudes")
        if not 'pr' in request.POST:
            return HttpResponseRedirect("/alu_solicitudes")
        else:
            return HttpResponseRedirect("/")
    else:
        data = {'title': 'Solicitudes'}
        try:
            addUserData(request, data)
            if 'action' in request.GET:
                action = request.GET['action']
                if action=='solicitar':
                    data['title'] = 'Nueva Solicitud'
                    # solicitud = SolicitudSecretariaDocente()
                    # data['form'] = SolicitudSecretariaAlumnosForm(instance=solicitud)
                    data['form'] = SolicitudSecretariaAlumnosForm()
                    return render(request ,"alu_solicitudes/adicionarbs.html" ,  data)
            else:

                if Inscripcion.objects.filter(persona=data['persona']).exists():
                    inscripcion = Inscripcion.objects.get(persona=data['persona'])

                    #Comprobar que no tenga deudas para que no pueda usar el sistema
                    if VALIDAR_ENTRADA_SISTEMA_CON_DEUDA and inscripcion.tiene_deuda():
                        # if inscripcion.matriculado() and not VALIDA_DEUDA_EXAM_ASIST:
                        # if VALIDA_DEUDA_EXAM_ASIST:

                        data['pr']=1
                        tipoespecie = TipoSolicitudSecretariaDocente.objects.get(id=ID_TIPO_SOLICITUD)

                        data['title'] = 'Nueva Solicitud'
                        data['form'] = SolicitudSecretariaAlumnosForm(initial={'tipo':tipoespecie})
                        data['form'] = SolicitudSecretariaAlumnosForm()
                        return render(request ,"alu_solicitudes/adicionarbs.html" ,  data)
                solicitudes = SolicitudSecretariaDocente.objects.filter(persona=data['persona']).order_by('-fecha','-hora')
                paging = Paginator(solicitudes, 30)
                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                    page = paging.page(p)
                except:
                    page = paging.page(1)
                data['paging'] = paging
                data['page'] = page
                data['solicitudes'] = page.object_list
                data['form'] = SolicitudSecretariaAlumnosForm()

                return render(request ,"alu_solicitudes/solicitudesbs.html" ,  data)
        except:
            return HttpResponseRedirect("/")



