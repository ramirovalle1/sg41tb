from datetime import datetime
from django.contrib.contenttypes.models import ContentType
from settings import EMAIL_ACTIVE, PORCIENTO_NOTA2, PORCIENTO_NOTA1, PORCIENTO_NOTA4, PORCIENTO_NOTA3, PORCIENTO_NOTA5, NOTA_PARA_APROBAR, NOTA_MAXIMA, SECRETARIAGENERAL_GROUP_ID
from sga.models import Asignatura, CoordinadorCarreraPeriodo, AsignaturaMalla, SolicitudMateriaOnline, Inscripcion, InscripcionMalla, Persona, HistoricoRecordAcademico, RecordAcademico, Malla, elimina_tildes
import json
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models.query_utils import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.utils.encoding import force_str
from django.template import RequestContext
from decorators import secure_module
from sga.commonviews import addUserData, ip_client_address
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

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action == 'addsolicitud': # agregar una solicitud
                try:
                    coord = CoordinadorCarreraPeriodo.objects.filter(persona__usuario=request.user)[:1].get()
                    solicitud = SolicitudMateriaOnline(asignatura_id=request.POST['asignatura'],
                                                       inscripcion_id=request.POST['estudiante'],
                                                       grupo=request.POST['grupo'],
                                                       observacion=request.POST['observacion'],
                                                       fecha=datetime.now().date(),
                                                       coordinador_id= coord.persona.id)
                    solicitud.save()

                    if "evidencia" in request.FILES:
                        solicitud.archivo = request.FILES['evidencia']
                        solicitud.save()

                    #Obtain client ip address
                    client_address = ip_client_address(request)
                     # Log de SOLICITUD MATERIA
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(solicitud).pk,
                        object_id       = solicitud.id,
                        object_repr     = force_str(solicitud),
                        action_flag     = ADDITION,
                        change_message  = 'Ingreso Solicitud Materia Online (' + client_address + ')')
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as e:
                    print(e)
                    return HttpResponse(json.dumps({'result':'bad','message':str(e)}), content_type="application/json")

            elif action=='consultaasignatura': #consulta asignatura por estudiante
                data = {}
                try:
                    inscripcion = Inscripcion.objects.filter(pk=request.POST['estudiante'])[:1].get()
                    asignaturas = []
                    for a in AsignaturaMalla.objects.filter(malla__carrera= inscripcion.carrera).order_by('asignatura__nombre'):
                        asignaturas.append(
                            {'id': a.id,
                             'asignatura': elimina_tildes(a.asignatura.nombre)
                            })
                    data['result']='ok'
                    data['asignaturas']=asignaturas
                    return HttpResponse(json.dumps(data), content_type="application/json")
                except Exception as e:
                    print(e)
                    return HttpResponse(json.dumps(data), content_type="application/json")

            elif action =='addnotas':# Ingreso una nota y lo guardo en la solicitud
                try:
                    notafinal =float(request.POST['nota1'])+float(request.POST['nota2'])+float(request.POST['nota3'])+float(request.POST['nota4'])+float(request.POST['examen'])
                    asistencia= request.POST['asistencia']
                    add = SolicitudMateriaOnline.objects.get(pk =request.POST['ids'])
                    add.nota1 =float(request.POST['nota1'])
                    add.nota2 =float(request.POST['nota2'])
                    add.nota3 =float(request.POST['nota3'])
                    add.nota4 =float(request.POST['nota4'])
                    add.examen =float(request.POST['examen'])
                    add.asistencia= asistencia
                    add.notafinal=notafinal
                    add.save()

                    fecha = datetime.now().date()
                    inscripcion = Inscripcion.objects.get(id= request.POST['idinscr'])
                    asignatura = Asignatura.objects.get(id=request.POST['asig'])

                    # PARA GUARDAR NOTA HISTORICO Y RECORD
                    historico = HistoricoRecordAcademico(inscripcion=inscripcion,asignatura=asignatura,nota=notafinal,asistencia=asistencia,
                                                        fecha=fecha,aprobada=False,convalidacion=False,pendiente=False)

                    if add.notafinal >= NOTA_PARA_APROBAR:
                        historico.aprobada=True

                    historico.save()

                    record = RecordAcademico(inscripcion=historico.inscripcion,asignatura=historico.asignatura,nota=historico.nota,
                                            asistencia=historico.asistencia, fecha=historico.fecha,aprobada=historico.aprobada,
                                            convalidacion=False,pendiente=False)
                    record.save()

                    mensaje = 'Adiciona de Solicitud Materia Online'
                    # Obtain client ip address
                    client_address = ip_client_address(request)
                    # Log de INGRESO DE SOLICITUD DE MATERIA
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(add).pk,
                        object_id       = add.id,
                        object_repr     = force_str(add),
                        action_flag     = ADDITION,
                        change_message  = mensaje+' (' + client_address + ')')
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")

                except Exception as e:
                    print(e)
                    return HttpResponse(json.dumps({"result":"bad"}), content_type="application/json")

            elif action =='editnotas': #edita las notas ingresadas
                try:
                    notafinal =float(request.POST['nota1'])+float(request.POST['nota2'])+float(request.POST['nota3'])+float(request.POST['nota4'])+float(request.POST['examen'])
                    edit = SolicitudMateriaOnline.objects.get(pk =request.POST['ids'])
                    edit.nota1 =float(request.POST['nota1'])
                    edit.nota2 =float(request.POST['nota2'])
                    edit.nota3 =float(request.POST['nota3'])
                    edit.nota4 =float(request.POST['nota4'])
                    edit.examen =float(request.POST['examen'])
                    edit.notafinal=notafinal
                    edit.save()
                    fecha = datetime.now().date()
                    historico = HistoricoRecordAcademico(inscripcion=edit.inscripcion,asignatura=edit.asignatura.asignatura,nota=notafinal,asistencia=edit.asistencia,
                                                        fecha=fecha,aprobada=False,convalidacion=False,pendiente=False)

                    if edit.notafinal >= NOTA_PARA_APROBAR:
                        historico.aprobada=True

                    historico.save()

                    record = RecordAcademico(inscripcion=historico.inscripcion,asignatura=historico.asignatura,nota=historico.nota,
                                            asistencia=historico.asistencia, fecha=historico.fecha,aprobada=historico.aprobada,
                                            convalidacion=False,pendiente=False)
                    record.save()

                    mensaje = 'Edicion de Solicitud Materia Online'
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(edit).pk,
                    object_id       = edit.id,
                    object_repr     = force_str(edit),
                    action_flag     = CHANGE,
                    change_message  = mensaje+' (' + client_address + ')' )
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as e:
                    print(e)
                    return HttpResponse(json.dumps({"result":"bad"}), content_type="application/json")

            elif action =='enviar': # luego de ingresar nota se envia a secretaria
                try:
                    solicitud = SolicitudMateriaOnline.objects.get(pk = request.POST['ids'])
                    hoy = datetime.now().date()
                    # mail= str('secretariageneral@bolivariano.edu.ec')+','+ str('szuniga@bolivariano.edu.ec')+','+ str('mmora@bolivariano.edu.ec') +','+ str('floresvillamarinm@gmail.com')
                    mail = str('vsgonzalezm@ube.edu.ec')
                    if EMAIL_ACTIVE:
                        solicitud.enviado= True
                        solicitud.save()
                        send_html_mail("SE SOLICITA LA APROBACION PARA QUE EL ESTUDIANTE PUEDA VER LA MATERIA EN EL SGAONLINE",
                                    "emails/correo_solicitudmateria.html", {'contenido': "A CONTINUACION SE DETALLA LA INFORMACION DEL ESTUDIANTE, PARA APROBAR LA SOLICITUD INGRESE AL MODULO SOLICITUD MATERIA ONLINE ", 'estudiante': solicitud.inscripcion.persona.nombre_completo_inverso(),'asignatura':solicitud.asignatura.asignatura.nombre,
                                                                            'grupo':solicitud.grupo, 'observacion':solicitud.observacion,'nota': solicitud.notafinal, 'fecha': hoy},mail.split())

                        # LOG  de envio de correo a Secretaria
                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(solicitud).pk,
                            object_id       = solicitud.id,
                            object_repr     = force_str(solicitud),
                            action_flag     = ADDITION,
                            change_message  = 'Solicitud de materia online (' + client_address + ')' )
                        return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                    return HttpResponse(json.dumps({'result':'bad'}), content_type="application/json")
                except Exception as e:
                    print(e)
                    return HttpResponse(json.dumps({'result':'bad','message':str(e)}), content_type="application/json")

            # APROBADO SOLICITUD
            elif action == 'aprobacionSolicitud':
                try:
                    if SolicitudMateriaOnline.objects.filter(aprobado= False).exists():
                        solicitud = SolicitudMateriaOnline.objects.get(id=request.POST['ids'])
                        tipo = int(request.POST['tipo'])
                        observacion = request.POST['observacion']

                        coordinador =Persona.objects.get(pk=solicitud.coordinador.id)
                        hoy = datetime.now().today()
                        secretaria = Persona.objects.filter(usuario=request.user,usuario__is_active=True)[:1].get()
                        # correo=coordinador.emailinst+','+str(secretaria.emailinst)
                        correo = str('vsgonzalezm@ube.edu.ec')

                        if tipo==1:
                            if EMAIL_ACTIVE:
                                inscripcion = solicitud.inscripcion.persona.nombre_completo_inverso()
                                asignatura =solicitud.asignatura.asignatura.nombre
                                grupo = solicitud.grupo
                                descripcion = solicitud.observacion
                                nota = solicitud.notafinal
                                if not solicitud.aprobado:
                                    solicitud.aprobado=True
                                    solicitud.fechaaprobacion=hoy
                                    solicitud.observacionaprob=observacion
                                    solicitud.usuarioapruba = secretaria
                                solicitud.save()
                                send_html_mail("SOLICITUD DE MATERIA ONLINE APROBADA", "emails/correo_solicitudmateriaaprob.html",
                                        {'contenido': "LA SOLICITUD INGRESA FUE APROBADA POR SECRETARIA", 'estudiante': inscripcion,'asignatura':asignatura,'grupo':grupo,'descripcion':descripcion,'nota':nota, 'fecha': hoy},correo.split())

                                # LOG  de envio de correo a Secretaria
                                client_address = ip_client_address(request)
                                LogEntry.objects.log_action(
                                    user_id         = request.user.pk,
                                    content_type_id = ContentType.objects.get_for_model(solicitud).pk,
                                    object_id       = solicitud.id,
                                    object_repr     = force_str(solicitud),
                                    action_flag     = ADDITION,
                                    change_message  = 'Aprobacion de Solicitud de materia online (' + client_address + ')' )

                                return HttpResponse(json.dumps({'result':'ok'}), content_type="application/json")
                            return HttpResponse(json.dumps({'result':'bad'}), content_type="application/json")
                        else:
                            if EMAIL_ACTIVE:
                                inscripcion = solicitud.inscripcion.persona.nombre_completo_inverso()
                                asignatura =solicitud.asignatura.asignatura.nombre
                                grupo = solicitud.grupo
                                descripcion = solicitud.observacion
                                nota = solicitud.notafinal
                                if not solicitud.aprobado:
                                    solicitud.aprobado=False
                                    solicitud.observacionaprob=observacion #observacion de reprobado
                                    solicitud.usuarioapruba = secretaria
                                    solicitud.enviado= False
                                solicitud.save()
                                send_html_mail("SOLICITUD DE MATERIA ONLINE REPROBADA", "emails/correo_solicitudmateriaaprob.html",
                                        {'contenido': "LA SOLICITUD INGRESADA FUE REPROBADA POR SECRETARIA, INGRESE LA SOLICITUD NUEVAMENTE Y ACTUALICE LAS NOTAS", 'estudiante': inscripcion,'asignatura':asignatura,'grupo':grupo,'descripcion':descripcion,'nota':nota, 'fecha': hoy},correo.split())

                                # LOG  de envio de correo a Secretaria
                                client_address = ip_client_address(request)
                                LogEntry.objects.log_action(
                                    user_id         = request.user.pk,
                                    content_type_id = ContentType.objects.get_for_model(solicitud).pk,
                                    object_id       = solicitud.id,
                                    object_repr     = force_str(solicitud),
                                    action_flag     = ADDITION,
                                    change_message  = 'No Aprobacion de Solicitud de materia online (' + client_address + ')' )

                                return HttpResponse(json.dumps({'result':'ok'}), content_type="application/json")
                            return HttpResponse(json.dumps({'result':'bad'}), content_type="application/json")
                    return HttpResponse(json.dumps({'result':'bad'}), content_type="application/json")
                except Exception as e:
                    print(e)
                    return HttpResponse(json.dumps({'result':'bad','message':str(e)}), content_type="application/json")

        else:
            data = {'title': 'Listado de Solicitud'}
            addUserData(request,data)

            if 'action' in request.GET:
                action = request.GET['action']
                if action=='vernotas':
                    try:
                        solicitudest= SolicitudMateriaOnline.objects.get(pk= request.GET['id'])
                        data['solicitudest']=solicitudest

                        return render(request,"solicitud_materiaonline/vernotasolicitud.html", data)
                    except Exception as e:
                        print(e)
                        return HttpResponse(json.dumps({"result":"bad"}), content_type="application/json")

            else:
                asignatura=[]
                coord=[]
                carreras_coord=[]
                inscripcion=[]
                inscripciones=[]
                secretaria = Persona.objects.filter(usuario=request.user, usuario__groups__id = SECRETARIAGENERAL_GROUP_ID, usuario__is_active=True) #secretaria
                if CoordinadorCarreraPeriodo.objects.filter(persona__usuario=request.user).exists():
                    coord = CoordinadorCarreraPeriodo.objects.filter(persona__usuario=request.user)[:1].get()
                    carreras_coord =list(CoordinadorCarreraPeriodo.objects.filter(persona__usuario=request.user).values_list('carrera__id', flat=True))
                    data['coordid']=carreras_coord
                    # asignatura = AsignaturaMalla.objects.filter(malla__carrera__id__in= carreras_coord).distinct('asignatura__id').order_by('asignatura__nombre')#147 rgistros
                    # asignatura = Asignatura.objects.filter(id__in= asignatur)
                    # inscripciones = InscripcionMalla.objects.filter(malla__carrera__id__in= carreras_coord).distinct('inscripcion').values_list('inscripcion').order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2')
                    # inscripcion = Inscripcion.objects.filter(id__in=inscripciones)

                search = None
                if 's' in request.GET:
                    search = request.GET['s']
                solicitud=[]
                if search:
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')
                    if len(ss)==1:
                        if coord:
                            solicitud = SolicitudMateriaOnline.objects.filter(Q(inscripcion__persona__apellido1__icontains=search)| Q(inscripcion__persona__apellido2__icontains=search)| Q(inscripcion__persona__nombres__icontains= search)| Q(asignatura__asignatura__nombre__icontains= search), coordinador = coord.persona).order_by('-id','inscripcion__persona__apellido1')
                        elif secretaria:
                            solicitud = SolicitudMateriaOnline.objects.filter(Q(inscripcion__persona__apellido1__icontains=search)| Q(inscripcion__persona__apellido2__icontains=search)| Q(inscripcion__persona__nombres__icontains= search)| Q(asignatura__asignatura__nombre__icontains= search)).order_by('-id','inscripcion__persona__apellido1')
                    else:
                        if coord:
                            solicitud = SolicitudMateriaOnline.objects.filter(Q(inscripcion__persona__apellido1__icontains=ss[0]) & Q(inscripcion__persona__apellido2__icontains=ss[1]),coordinador = coord.persona).order_by('-id','inscripcion__persona__apellido1') #asignatura__malla__carrera__id__in = carreras_coord
                        elif secretaria:
                            solicitud = SolicitudMateriaOnline.objects.filter(Q(inscripcion__persona__apellido1__icontains=ss[0]) & Q(inscripcion__persona__apellido2__icontains=ss[1])).order_by('-id','inscripcion__persona__apellido1')
                else:
                    if coord:
                        solicitud = SolicitudMateriaOnline.objects.filter(coordinador = coord.persona).order_by('-id', 'inscripcion__persona__apellido1')
                    elif secretaria:
                        solicitud = SolicitudMateriaOnline.objects.filter().order_by('-id', 'inscripcion__persona__apellido1')


                paging = MiPaginador(solicitud,30)
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

                # idinscri = Inscripcion.objects.filter(id__in=inscripciones).values_list('id',flat=True)
                # data['inscripciones']= list(idinscri)
                # print(idinscri)
                data['solicitudmateria']=solicitud
                data['porcnota1']= PORCIENTO_NOTA1
                data['porcnota2']= PORCIENTO_NOTA2
                data['porcnota3']= PORCIENTO_NOTA3
                data['porcnota4']= PORCIENTO_NOTA4
                data['porcnota5']= PORCIENTO_NOTA5
                data['asistencia'] = NOTA_MAXIMA

                return render(request,"solicitud_materiaonline/solicitud_materiaonline.html", data)

    except Exception as ex:
        print(ex)
        return HttpResponseRedirect('/solicitud_materiaonline')

