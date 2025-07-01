import json


from django.contrib.admin.models import LogEntry, CHANGE, ADDITION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import Q, Max
from django.http import HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from datetime import datetime
from django.utils.encoding import force_str
from sga.commonviews import ip_client_address, addUserData
from sga.models import Persona, Inscripcion,  SolicitudAntencion, TipoIdentificacion, TipoServicioCarrera, Pais, Provincia, EvidenciaSolicitudAntencion, elimina_tildes
from sga.panel import MiPaginador


@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    if request.method == 'POST':
        action = request.POST['action']

        if action == 'doctores':
            try:
                ss = request.POST['q'].split(' ')
                while '' in ss:
                    ss.remove('')
                if len(ss) == 1:

                    persona = Persona.objects.filter(Q(cedula__icontains=request.POST['q']) | Q(
                        pasaporte__icontains=request.POST['q']) | Q(
                        nombres__icontains=request.POST['q']) | Q(
                        apellido1__icontains=request.POST['q']) | Q(
                        apellido2__icontains=request.POST['q']),usuario__is_active=True).order_by(
                        'apellido1',
                        'apellido2')
                else:

                    persona = Persona.objects.filter(
                        Q(pellido1__icontains=ss[0]) & Q(
                            apellido2__icontains=ss[1]), usuario__is_active=True).order_by(
                        'apellido1',
                        'apellido2')


                persona=persona.filter().exclude(id__in=Inscripcion.objects.filter(persona__id__in=persona.filter().values_list('id',flat=True)).values('persona_id'))

                paging = MiPaginador(persona, 30)
                p = 1
                try:
                    if 'page' in request.POST:
                        p = int(request.POST['page'])
                    page = paging.page(p)
                except:
                    page = paging.page(p)

                lista = [{"id": d.id, "nombre": str(d)} for d in
                         page.object_list]

                return HttpResponse(json.dumps({'result': 'ok', 'items': lista, 'page': p}),
                                    content_type="application/json")

            except Exception as ex:
                return HttpResponse(json.dumps({"result": "bad", "message": ex}), content_type="application/json")






        if action == 'agregarasignacion':
            try:
                data = {'title': ''}
                solicitudatencion=SolicitudAntencion.objects.get(pk=int(request.POST['idsolici']))
                solicitudatencion.profesoratiende_id=int(request.POST['iddocente'])
                solicitudatencion.save()
                # if  solicitudatencion.profesoratiende.emailinst:
                #     solicitudatencion.mail_asignaciondocente()
                data['result'] = 'ok'
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}), content_type="application/json")





        if action == 'agregarasignaciondoctor':
            try:
                data = {'title': ''}
                solicitudatencion=SolicitudAntencion.objects.get(pk=int(request.POST['idsolici']))
                persona=Persona.objects.filter(pk=int(request.POST['idingreso']))[:1].get()
                solicitudatencion.usuarioatiende=persona.usuario
                solicitudatencion.fechaasignacion=datetime.now()
                solicitudatencion.save()

                # enviar correo de la persona que va atender la solicitud
                # if solicitudatencion.persona.emailinst:
                #     solicitudatencion.mail_asignaciondoctorself()


                data['result'] = 'ok'
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}), content_type="application/json")


        if action == 'eliminarsolicitud':
            try:
                data = {'title': ''}
                solicitudatencion=SolicitudAntencion.objects.get(pk=int(request.POST['idsolicitud']))
                # Obtain client ip address
                client_address = ip_client_address(request)

                # Log de ELIMINAR BENEFICIARIO
                LogEntry.objects.log_action(
                    user_id=request.user.pk,
                    content_type_id=ContentType.objects.get_for_model(solicitudatencion).pk,
                    object_id=solicitudatencion.id,
                    object_repr=force_str(solicitudatencion),
                    action_flag=CHANGE,
                    change_message='Eliminado Solicitud de atencion  (' + client_address + ')')
                solicitudatencion.delete()
                data['result'] = 'ok'
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}), content_type="application/json")


        elif action == 'agregarevidencia':
            try:
                data = {'title': ''}
                solicitud = SolicitudAntencion.objects.get(pk=int(request.POST['idsolicitud']))




                evidencia = EvidenciaSolicitudAntencion(solicitud=solicitud,
                                                 nombre=elimina_tildes(request.POST['nombre']).upper(),
                                                        observacion=elimina_tildes(request.POST['observacion']).upper(),
                                                 fecha=datetime.now(),usuario=request.user
                                                        )
                evidencia.save()

                if 'archivo' in request.FILES:
                    evidencia.foto = request.FILES['archivo']
                    evidencia.save()



                solicitud.finalizado=True
                hora_actual = datetime.now().time()
                solicitud.horafinaliza= hora_actual.strftime('%H:%M')
                solicitud.usuarioatiende=request.user
                solicitud.fechafinalizacion=datetime.now()
                solicitud.idevidencia=evidencia.id
                solicitud.save()

                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                    user_id=request.user.pk,
                    content_type_id=ContentType.objects.get_for_model(solicitud).pk,
                    object_id=solicitud.id,
                    object_repr=force_str(solicitud),
                    action_flag=ADDITION,
                    change_message=" Adicionada Evidencia Solicitud" + '(' + client_address + ')')

                data['result'] = 'ok'
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}),
                                    content_type="application/json")





    else:
        data = {'title': 'Solicitudes de Atencion'}
        addUserData(request, data)
        search = None
        if 'action' in request.GET:
            action = request.GET['action']



            if action == 'verdiagnostico':

                try:
                    data = {'title': ''}
                    solici = SolicitudAntencion.objects.get(pk=int(request.GET['idps']))

                    data['listdiagnostico'] = EvidenciaSolicitudAntencion.objects.filter(solicitud=solici).order_by(
                        '-fecha')

                    return render(request ,"teleatencion/verdiagnostico.html" ,  data)

                except Exception as e:
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}),
                                        content_type="application/json")




        else:

            try:


                solicitudatencion = SolicitudAntencion.objects.filter().order_by('-fecha')

                if 's' in request.GET:
                    search = request.GET['s']

                    solicitudatencion=solicitudatencion.filter( Q(nombres__icontains=search) | Q(apellidos__icontains=search) |
                       Q(identificacion__icontains=search) | Q(
                        celular__icontains=search) | Q(email__icontains=search),
                        ).order_by('-fecha')

                paging = MiPaginador(solicitudatencion, 30)
                p = 1
                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                        paging = MiPaginador(solicitudatencion, 30)
                    page = paging.page(p)
                except Exception as ex:
                    page = paging.page(1)

                data['paging'] = paging
                data['rangospaging'] = paging.rangos_paginado(p)
                data['page'] = page
                data['solicitudatencion'] = page.object_list
                data['fechah'] = datetime.now().strftime("%Y-%m-%d")
                hora_actual = datetime.now().time()
                data['horactual'] = hora_actual.strftime('%H:%M')
                data['search'] = search if search else ""
                data['listtipoidentificacion'] = TipoIdentificacion.objects.filter(estado=True)
                data['listtiposervicio'] = TipoServicioCarrera.objects.filter(estado=True)
                data['listpais'] = Pais.objects.filter(pk=1)
                data['lisprovincia'] = Provincia.objects.filter()


                return render(request ,"teleatencion/solictudadmin.html" ,  data)

            except Exception as ex:
                print(ex)


