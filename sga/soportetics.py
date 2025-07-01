from datetime import datetime
import json
import os
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.contrib.admin.models import LogEntry, ADDITION
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
from decorators import secure_module
from settings import MEDIA_ROOT, EMAIL_ACTIVE
from sga.commonviews import addUserData, ip_client_address
from sga.models import Sede, HorarioAsistente, AsistenteSoporte, RequerimientoSoporte, RequerimSolucion, RespProgramdor, \
    VideoLogin


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

__author__ = 'jjurgiles'

@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    try:
        if request.method == 'POST':
            action = request.POST['action']
            if 'iniciolab' == action:
                try:
                    sede = None
                    asistente = AsistenteSoporte.objects.filter(persona__usuario=request.user)[:1].get()
                    if int(request.POST['sede']) > 0:
                        sede = Sede.objects.get(id=request.POST['sede'])
                    hinicio = None
                    hfin = None
                    nolabora = True
                    if request.POST['nolabora'] == "false":
                        hinicio = request.POST['hinicio']
                        hfin = request.POST['hfin']
                        nolabora = False
                    if not HorarioAsistente.objects.filter(soporte=asistente,fecha = datetime.now()).exists():
                        hinicio = request.POST['hinicio']
                        hfin = request.POST['hfin']
                        horarioasistente = HorarioAsistente(sede=sede,
                                                            soporte=asistente,
                                                            horainicio = hinicio,
                                                            horafin = hfin,
                                                            fecha = datetime.now(),
                                                            fechaingreso = datetime.now().time(),
                                                            user = request.user,
                                                            nolabora = nolabora,
                                                            programador = asistente.programador)
                        horarioasistente.save()
                        if RequerimientoSoporte.objects.filter(soporte=None,finalizado=False).exists() and not asistente.programador:
                            for r in RequerimientoSoporte.objects.filter(soporte=None,finalizado=False):
                                #OCastillo 17-08-2022 asignacion a Joseph requerimientos tipo correo y pagina web
                                if r.tipoproblema.id==5 or r.tipoproblema.id==7:
                                    if asistente.persona.pertenece_soporte_bandeja():
                                        r.soporte = horarioasistente
                                        r.save()
                                        horarioasistente.sinatender =horarioasistente.sinatender + 1
                                        horarioasistente.fechaasigna = datetime.now()
                                        horarioasistente.save()
                                        client_address = ip_client_address(request)

                                        #Log de ADICIONAR SOPORTE
                                        LogEntry.objects.log_action(
                                            user_id         = request.user.pk,
                                            content_type_id = ContentType.objects.get_for_model(r).pk,
                                            object_id       = r.id,
                                            object_repr     = force_str(r),
                                            action_flag     = ADDITION,
                                            change_message  = 'SOPORTE ASIGNADO AL INGRESAR EL TURNO  (' + client_address + ')' )
                                        if EMAIL_ACTIVE:
                                            r.mail_requerimiento()
                                else:
                                    soporte = None
                                    if HorarioAsistente.objects.filter(fecha=datetime.now().date(),nolabora=False,horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time(),sede=sede,programador=False).exists():
                                        soporte = HorarioAsistente.objects.filter(fecha=datetime.now().date(),nolabora=False,horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time(),sede=sede,programador=False).order_by('sinatender','fechaasigna')[:1].get()
                                        if soporte.soporte.persona.pertenece_soporte_bandeja():
                                            soporte = None
                                            pass
                                    elif HorarioAsistente.objects.filter(fecha=datetime.now().date(),nolabora=False,horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time(),programador=False):
                                        soporte = HorarioAsistente.objects.filter(fecha=datetime.now().date(),nolabora=False,horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time(),programador=False).order_by('sinatender','fechaasigna')[:1].get()
                                        if soporte.soporte.persona.pertenece_soporte_bandeja():
                                            soporte = None
                                            pass
                                    if soporte:
                                        r.soporte = soporte
                                        r.save()
                                        soporte.sinatender = soporte.sinatender + 1
                                        soporte.fechaasigna = datetime.now()
                                        soporte.save()
                                        client_address = ip_client_address(request)

                                        #Log de ADICIONAR SOPORTE
                                        LogEntry.objects.log_action(
                                            user_id         = request.user.pk,
                                            content_type_id = ContentType.objects.get_for_model(r).pk,
                                            object_id       = r.id,
                                            object_repr     = force_str(r),
                                            action_flag     = ADDITION,
                                            change_message  = 'SOPORTE ASIGNADO AL INGRESAR EL TURNO  (' + client_address + ')' )
                                        if EMAIL_ACTIVE:
                                            r.mail_requerimiento()


                        client_address = ip_client_address(request)

                        #Log de ADICIONAR SOPORTE
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(horarioasistente).pk,
                            object_id       = horarioasistente.id,
                            object_repr     = force_str(horarioasistente),
                            action_flag     = ADDITION,
                            change_message  = 'Horario soporte ingresado  (' + client_address + ')' )
                        return HttpResponse(json.dumps({'result': 'ok'}), content_type="application/json")
                    return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")
                except Exception as e:
                    print(e)
                    return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")
            elif 'editturno' == action:
                try:
                    sede = None
                    if 'asistente2' in request.POST:
                        asistente=AsistenteSoporte.objects.filter(id=request.POST['asistente2'])[:1].get()
                    else:
                        asistente = AsistenteSoporte.objects.filter(persona__usuario=request.user)[:1].get()
                    horarioasistente = HorarioAsistente.objects.get(id=request.POST['idhorat'])
                    if int(request.POST['sede']) > 0:
                        sede = Sede.objects.get(id=request.POST['sede'])
                    hinicio = None
                    hfin = None
                    nolabora = True
                    if request.POST['nolabora'] == "false":
                        hinicio = request.POST['hinicio']
                        hfin = request.POST['hfin']
                        nolabora = False
                    # if RequerimientoSoporte.objects.filter(soporte=horarioasistente).exists():
                    horarioasistente.sede=sede
                    horarioasistente.soporte=asistente
                    horarioasistente.horainicio = hinicio
                    horarioasistente.horafin = hfin
                    horarioasistente.fecha = datetime.now()
                    horarioasistente.user = request.user
                    horarioasistente.nolabora = nolabora
                    horarioasistente.programador = asistente.programador
                    horarioasistente.save()
                    if RequerimientoSoporte.objects.filter(soporte=None,finalizado=False).exists():
                        for r in RequerimientoSoporte.objects.filter(soporte=None,finalizado=False):
                            #OCastillo 07-11-2022 asignacion a Joseph requerimientos tipo correo y pagina web
                            if r.tipoproblema.id==5 or r.tipoproblema.id==7:
                                if asistente.persona.pertenece_soporte_bandeja():
                                    r.soporte = horarioasistente
                                    r.save()
                                    horarioasistente.sinatender =horarioasistente.sinatender + 1
                                    horarioasistente.fechaasigna = datetime.now()
                                    horarioasistente.save()
                                    client_address = ip_client_address(request)

                                    #Log de ADICIONAR SOPORTE
                                    LogEntry.objects.log_action(
                                        user_id         = request.user.pk,
                                        content_type_id = ContentType.objects.get_for_model(r).pk,
                                        object_id       = r.id,
                                        object_repr     = force_str(r),
                                        action_flag     = ADDITION,
                                        change_message  = 'SOPORTE ASIGNADO AL EDITAR EL TURNO  (' + client_address + ')' )
                                    if EMAIL_ACTIVE:
                                        r.mail_requerimiento()
                            else:
                                soporte = None
                                if HorarioAsistente.objects.filter(fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time(),sede=sede,programador=False,nolabora=False).exists():
                                    soporte = HorarioAsistente.objects.filter(fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time(),sede=sede,programador=False,nolabora=False).order_by('sinatender','fechaasigna')[:1].get()
                                    if soporte.soporte.persona.pertenece_soporte_bandeja():
                                        soporte = None
                                        pass
                                elif HorarioAsistente.objects.filter(fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time(),programador=False,nolabora=False):
                                    soporte = HorarioAsistente.objects.filter(fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time(),programador=False,nolabora=False).order_by('sinatender','fechaasigna')[:1].get()
                                    if soporte.soporte.persona.pertenece_soporte_bandeja():
                                        soporte = None
                                        pass
                                if soporte:
                                    r.soporte = soporte
                                    r.save()
                                    soporte.sinatender = soporte.sinatender + 1
                                    soporte.fechaasigna = datetime.now()
                                    soporte.save()

                                    client_address = ip_client_address(request)

                                    #Log de ADICIONAR SOPORTE
                                    LogEntry.objects.log_action(
                                        user_id         = request.user.pk,
                                        content_type_id = ContentType.objects.get_for_model(r).pk,
                                        object_id       = r.id,
                                        object_repr     = force_str(r),
                                        action_flag     = ADDITION,
                                        change_message  = 'SOPORTE ASIGNADO AL EDITAR EL TURNO  (' + client_address + ')' )
                                    if EMAIL_ACTIVE:
                                        r.mail_requerimiento()
                    if EMAIL_ACTIVE:
                        horarioasistente.mail_edit_reasg_horario()

                    client_address = ip_client_address(request)

                    #Log de ADICIONAR HORARIO
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(horarioasistente).pk,
                        object_id       = horarioasistente.id,
                        object_repr     = force_str(horarioasistente),
                        action_flag     = ADDITION,
                        change_message  = 'Horario soporte editado  (' + client_address + ')' )
                    return HttpResponse(json.dumps({'result': 'ok'}), content_type="application/json")
                    # return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")
                except Exception as e:
                    print(e)
                    return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")
            elif 'datacombo' == action:
                try:
                    list = []
                    data = {}
                    asistente = AsistenteSoporte.objects.filter(programador=True)
                    for a in asistente:
                        list.append({"id": str(a.id), "progra": str(a.programador), "nombre": str(a.persona)})

                    data['list'] = list
                    data['result'] =  'ok'
                    return HttpResponse(json.dumps(data), content_type="application/json")
                    # return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")
                except Exception as e:
                    print(e)
                    return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")
            elif 'dataregistros' == action:
                try:
                    list = []
                    data = {}
                    asistente = AsistenteSoporte.objects.filter().order_by('persona')
                    for a in asistente.order_by('persona__nombres'):
                        list.append({"horaingre": str(a.horarioingres()),"horarioactual": str(a.horarioactual()),"nombre": str(a.persona.nombre_completo()), "reg": str(a.cantrqueri(request.POST['fecha'],request.POST['general'])), "fin": str(a.cantrquerifin(request.POST['fecha'],request.POST['general']))
                                , "sin": str(a.cantrquerisin(request.POST['fecha'],request.POST['general'])), "tipo": 'programador' if a.programador else 'soporte'})


                    data['list'] = list
                    data['result'] =  'ok'
                    return HttpResponse(json.dumps(data), content_type="application/json")
                    # return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")
                except Exception as e:
                    print("ERROR DATAREG"+str(e))
                    return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")
            elif 'addgestion' == action:
                try:
                    sede = None
                    requerimiento = RequerimientoSoporte.objects.get(id=request.POST['idrequeri'])
                    finaliza = False
                    if request.POST['finaliza'] == "true":
                        finaliza = True
                    requerimientosolu = RequerimSolucion(requerimiento = requerimiento,
                                            solucion = request.POST['requerimiento'],
                                            fecha = datetime.now())
                    if finaliza:
                        requerimientosolu.finalizado = finaliza
                        requerimientosolu.requerimiento.soporte.sinatender = requerimientosolu.requerimiento.soporte.sinatender - 1
                        requerimientosolu.requerimiento.soporte.save()
                        requerimientosolu.requerimiento.finalizado = finaliza
                    if "archivo" in request.FILES:
                        if requerimientosolu.archivo:
                            if os.path.exists(MEDIA_ROOT+'/'+str(requerimientosolu.archivo)):
                                os.remove(MEDIA_ROOT+'/'+str(requerimientosolu.archivo))
                        requerimientosolu.archivo = request.FILES["archivo"]
                    requerimientosolu.save()
                    requerimientosolu.requerimiento.save()
                    if EMAIL_ACTIVE:
                        mensa = 'Solucion de Soporte'
                        requerimientosolu.mail_requerimiento(mensa,2)
                    client_address = ip_client_address(request)

                    #Log de ADICIONAR INSCRIPCION
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(requerimientosolu).pk,
                        object_id       = requerimientosolu.id,
                        object_repr     = force_str(requerimientosolu),
                        action_flag     = ADDITION,
                        change_message  = 'AGREGADO GESTION  (' + client_address + ')' )
                    return HttpResponse(json.dumps({'result': 'ok'}), content_type="application/json")
                except Exception as e:
                    print(e)
                    return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")
            elif 'reasignar' == action:
                try:
                    if request.POST['progravar'] == 'True':
                        if HorarioAsistente.objects.filter(soporte__id=request.POST['reasigsoport'],fecha=datetime.now().date()).exists():
                            horarioasistente = HorarioAsistente.objects.filter(soporte__id=request.POST['reasigsoport'],fecha=datetime.now().date())[:1].get()
                        else:
                            asistentesoporte = AsistenteSoporte.objects.get(id=request.POST['reasigsoport'])
                            horarioasistente = HorarioAsistente(sede=None,
                                                            soporte=asistentesoporte,
                                                            horainicio = None,
                                                            horafin = None,
                                                            fecha = datetime.now(),
                                                            fechaingreso = datetime.now().time(),
                                                            user = request.user,
                                                            nolabora = True,
                                                            programador = asistentesoporte.programador)
                            horarioasistente.save()
                    else:
                        horarioasistente = HorarioAsistente.objects.filter(soporte__id=request.POST['reasigsoport'])[:1].get()
                    if not horarioasistente.programador:
                        requerimiento = RequerimientoSoporte.objects.get(id=request.POST['idreareqhorar'])
                        requerimiento.soporreasig = requerimiento.soporte
                        requerimiento.soporte = horarioasistente
                        requerimiento.fecharesignacion = datetime.now()
                        requerimiento.save()
                        requerimiento.soporreasig.sinatender = requerimiento.soporreasig.sinatender - 1
                        requerimiento.soporte.sinatender = requerimiento.soporte.sinatender + 1
                        requerimiento.soporte.fechaasigna = datetime.now()
                        requerimiento.soporreasig.save()
                        requerimiento.soporte.save()
                        if EMAIL_ACTIVE:
                            requerimiento.mail_requerimiento()
                            requerimiento.mail_edit_reasg_horario()
                        client_address = ip_client_address(request)

                        #Log de ADICIONAR INSCRIPCION
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(requerimiento).pk,
                            object_id       = requerimiento.id,
                            object_repr     = force_str(requerimiento),
                            action_flag     = ADDITION,
                            change_message  = 'Reasignando requerimiento  (' + client_address + ')' )
                    else:
                        requerimiento = RequerimientoSoporte.objects.get(id=request.POST['idreareqhorar'])

                        respprogramador = RespProgramdor(requerimiento = requerimiento,
                                                         soporte = horarioasistente,
                                                         consulta =request.POST['consulta'],
                                                         fecha = datetime.now())
                        respprogramador.save()
                        if EMAIL_ACTIVE:
                            respprogramador.mail_requerimiento("Consulta de Soporte",3)
                        client_address = ip_client_address(request)

                        #Log de ADICIONAR INSCRIPCION
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(respprogramador).pk,
                            object_id       = requerimiento.id,
                            object_repr     = force_str(respprogramador),
                            action_flag     = ADDITION,
                            change_message  = 'Asignando  requerimiento a programador   (' + client_address + ')' )
                    return HttpResponse(json.dumps({'result': 'ok'}), content_type="application/json")
                except Exception as e:
                    print(e)
                    return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")

            elif 'addrespureq' == action:
                try:
                    respprogramador = RespProgramdor.objects.get(id=request.POST['idrequeri'])
                    finaliza = False
                    if request.POST['finaliza'] == "true":
                        finaliza = True

                    if finaliza:
                        respprogramador.fecharesp = datetime.now()
                        respprogramador.respuesta = request.POST['requerimiento']
                        respprogramador.finalizado = True
                        respprogramador.save()
                    if "archivo" in request.FILES:
                        if respprogramador.archivo:
                            if os.path.exists(MEDIA_ROOT+'/'+str(respprogramador.archivo)):
                                os.remove(MEDIA_ROOT+'/'+str(respprogramador.archivo))
                        respprogramador.archivo = request.FILES["archivo"]
                    respprogramador.save()
                    if EMAIL_ACTIVE:
                        respprogramador.mail_requerimiento("Respuesta de Programador",4)
                    client_address = ip_client_address(request)

                    #Log de ADICIONAR INSCRIPCION
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(respprogramador).pk,
                        object_id       = respprogramador.id,
                        object_repr     = force_str(respprogramador),
                        action_flag     = ADDITION,
                        change_message  = 'AGREGADO GESTION  (' + client_address + ')' )
                    return HttpResponse(json.dumps({'result': 'ok'}), content_type="application/json")
                except Exception as e:
                    print(e)
                    return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")

            elif 'editarvideologin' == action:
                try:
                    # chactivo= request.POST['activo']
                    # if chactivo =='true':
                    #     activo = True
                    # else:
                    #     activo = False
                    if VideoLogin.objects.filter(pk=request.POST['idvideo']).exists():
                        editvideologin = VideoLogin.objects.filter(pk=request.POST['idvideo'])[:1].get()
                        editvideologin.descripcion = request.POST['descripcion']
                        # editvideologin.activo = activo
                        editvideologin.save()

                        client_address = ip_client_address(request)
                        #Log de EDITAR VIDEO LOGIN
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(editvideologin).pk,
                            object_id       = editvideologin.id,
                            object_repr     = force_str(editvideologin),
                            action_flag     = ADDITION,
                            change_message  = 'Video Login Editado  (' + client_address + ')' )
                    return HttpResponse(json.dumps({'result': 'ok'}), content_type="application/json")
                    # return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")
                except Exception as e:
                    print(e)
                    return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")
        else:
            data = {'title':'Soporte TICS'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']
                if 'actualizar' == action:
                    try:
                        if RequerimientoSoporte.objects.filter(finalizado=False).exists():
                            for r in RequerimientoSoporte.objects.filter(finalizado=False):
                                soporte = None
                                if r.soporte:
                                    if r.soporte.sinatender > 0:
                                        r.soporte.sinatender = r.soporte.sinatender - 1
                                        r.soporte.save()
                            for r in RequerimientoSoporte.objects.filter(finalizado=False):
                                soporte = None
                                # if HorarioAsistente.objects.filter(fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time(),sede=r.sede,programador=False).exists():
                                #     soporte = HorarioAsistente.objects.filter(fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time(),sede=r.sede,programador=False).order_by('sinatender','fechaasigna')[:1].get()
                                if HorarioAsistente.objects.filter(fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time(),programador=False):
                                    soporte = HorarioAsistente.objects.filter(fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time(),programador=False).order_by('sinatender','fechaasigna')[:1].get()
                                r.soporte = soporte
                                r.save()
                                if soporte:
                                    soporte.sinatender = soporte.sinatender + 1
                                    soporte.fechaasigna = datetime.now()
                                    soporte.save()
                        asistente = AsistenteSoporte.objects.filter(persona__usuario=request.user)[:1].get()
                        client_address = ip_client_address(request)

                        #Log de ADICIONAR INSCRIPCION
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(asistente).pk,
                            object_id       = asistente.id,
                            object_repr     = force_str(asistente),
                            action_flag     = ADDITION,
                            change_message  = 'EJECUTO PROCESO DE  ACTUALIZACION (' + client_address + ')' )
                        return HttpResponseRedirect("/")
                    except Exception as e:
                        print(e)
                        return HttpResponseRedirect("/")
                elif action=='vergestion':
                    data = {}
                    requerimiento = RequerimientoSoporte.objects.get(id=request.GET['idreq'])
                    data['requerimiento'] = requerimiento
                    data['requerimientosol'] = RequerimSolucion.objects.filter(requerimiento=requerimiento)
                    data['sopor'] = True
                    return render(request ,"soportereque/reqsolucion.html" ,  data)
                elif action=='verconsulta':
                    data = {}
                    if AsistenteSoporte.objects.filter(persona__usuario=request.user).exists():
                        data['verasistentes'] = False
                        asistente = AsistenteSoporte.objects.filter(persona__usuario=request.user)[:1].get()
                        data['asistente'] = asistente
                    requerimiento = RequerimientoSoporte.objects.get(id=request.GET['idreq'])
                    data['requerimiento'] = requerimiento
                    data['respprogramdor'] = RespProgramdor.objects.filter(requerimiento=requerimiento)

                    return render(request ,"soportereque/reqsolucion.html" ,  data)

                elif action=='chatsoporte':
                    data = {}
                    # data['persona'] =data['persona']
                    addUserData(request,data)

                    return render(request ,"chat/salachatsoporte.html" ,  data)
            else:
                #OCastillo 08-02-2022 para que DNavarrete pueda ver solicitudes y reasignar
                if AsistenteSoporte.objects.filter(persona__usuario=request.user).exclude(id=3).exists():
                    data['verasistentes'] = False
                    asistente = AsistenteSoporte.objects.filter(persona__usuario=request.user)[:1].get()
                    data['asistente'] = asistente
                    soportehorarios = HorarioAsistente.objects.filter(fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time(),programador=False).exclude(soporte=asistente).order_by("soporte__persona")
                    if HorarioAsistente.objects.filter(fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time(),soporte=asistente).exists():
                        horarioasistente = HorarioAsistente.objects.filter(fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time(),soporte=asistente)[:1].get()
                        data['horarioasistente'] = horarioasistente
                        # if not RequerimientoSoporte.objects.filter(soporte=horarioasistente).exists():
                        sedes = Sede.objects.filter(solobodega=False)
                        data['sedes'] = sedes
                    elif  HorarioAsistente.objects.filter(fecha=datetime.now().date(),soporte=asistente,nolabora=True).exists():
                        horarioasistente = HorarioAsistente.objects.filter(fecha=datetime.now().date(),soporte=asistente,nolabora=True)[:1].get()
                        data['horarioasistente'] = horarioasistente
                        # if not RequerimientoSoporte.objects.filter(soporte=horarioasistente).exists():
                        sedes = Sede.objects.filter(solobodega=False)
                        data['sedes'] = sedes
                    if 'finali' in request.GET:
                        if asistente.programador:
                            data['verasistentes'] = True
                            asistententes = AsistenteSoporte.objects.filter()
                            data['asistententes'] = asistententes
                            if 'idasis' in request.GET:
                                verasiiste = AsistenteSoporte.objects.get(id=request.GET['idasis'])
                                data['verasiiste'] = verasiiste
                                if verasiiste.programador:
                                    idreqpr = RespProgramdor.objects.filter(soporte__soporte=verasiiste,finalizado=False).distinct('requerimiento').values('requerimiento')
                                    idreqprfin = RespProgramdor.objects.filter(soporte__soporte=verasiiste,finalizado=True).exclude(requerimiento__id__in=idreqpr).distinct('requerimiento').values('requerimiento')

                                    requerimientosoporte =  RequerimientoSoporte.objects.filter(Q(finalizado=True,id__in=idreqpr)| Q(id__in=idreqprfin)).order_by('-fecha')
                                else:
                                    requerimientosoporte =  RequerimientoSoporte.objects.filter(soporte__soporte=verasiiste,finalizado=True).order_by('-fecha')
                            else:
                                idreqpr = RespProgramdor.objects.filter(soporte__soporte=asistente,finalizado=False).distinct('requerimiento').values('requerimiento')
                                idreqprfin = RespProgramdor.objects.filter(soporte__soporte=asistente,finalizado=True).exclude(requerimiento__id__in=idreqpr).distinct('requerimiento').values('requerimiento')
                                requerimientosoporte =  RequerimientoSoporte.objects.filter(Q(finalizado=True,id__in=idreqpr)| Q(id__in=idreqprfin)).order_by('-fecha')
                        else:
                            requerimientosoporte =  RequerimientoSoporte.objects.filter(soporte__soporte=asistente,finalizado=True).order_by('-fecha')

                    elif 's' in request.GET:

                        search = request.GET['s']
                        data['search'] = search
                        ss = search.split(' ')
                        while '' in ss:
                            ss.remove('')
                        if asistente.programador:
                            data['verasistentes'] = True
                            asistententes = AsistenteSoporte.objects.filter()
                            data['asistententes'] = asistententes
                            if len(ss)==1:
                                requerimientosoporte = RequerimientoSoporte.objects.filter(Q(persona__nombres__icontains=search) | Q(persona__apellido1__icontains=search) | Q(persona__apellido2__icontains=search) | Q(persona__cedula__icontains=search) | Q(persona__pasaporte__icontains=search)).order_by('persona__apellido1','-fecha')
                            else:
                                requerimientosoporte = RequerimientoSoporte.objects.filter(Q(persona__apellido1__icontains=ss[0]) & Q(persona__apellido2__icontains=ss[1])).order_by('persona__apellido1','persona__apellido2','persona__nombres','-fecha')
                        else:
                            if len(ss)==1:
                                requerimientosoporte = RequerimientoSoporte.objects.filter(Q(persona__nombres__icontains=search) | Q(persona__apellido1__icontains=search) | Q(persona__apellido2__icontains=search) | Q(persona__cedula__icontains=search) | Q(persona__pasaporte__icontains=search),soporte__soporte=asistente ).order_by('persona__apellido1','-fecha')
                            else:
                                requerimientosoporte = RequerimientoSoporte.objects.filter(Q(persona__apellido1__icontains=ss[0]) & Q(persona__apellido2__icontains=ss[1]),soporte__soporte=asistente).order_by('persona__apellido1','persona__apellido2','persona__nombres','-fecha')

                    else:
                        if asistente.programador:
                            data['verasistentes'] = True
                            asistententes = AsistenteSoporte.objects.filter().order_by('persona')
                            data['asistententes'] = asistententes
                            if 'idasis' in request.GET:
                                verasiiste = AsistenteSoporte.objects.get(id=request.GET['idasis'])
                                data['verasiiste'] = verasiiste
                                # if HorarioAsistente.objects.filter(soporte=verasiiste,fecha=datetime.now().date()).exists():
                                #     data['asistente2']=HorarioAsistente.objects.filter(soporte=verasiiste,fecha=datetime.now().date())[:1].get()
                                if verasiiste.programador:
                                    idreqpr = RespProgramdor.objects.filter(soporte__soporte=verasiiste,finalizado=False).distinct('requerimiento').values('requerimiento')
                                    requerimientosoporte =  RequerimientoSoporte.objects.filter(finalizado=False,id__in=idreqpr).order_by('-fecha')
                                else:
                                    requerimientosoporte =  RequerimientoSoporte.objects.filter(soporte__soporte=verasiiste,finalizado=False).order_by('-fecha')
                            else:
                                idreqpr = RespProgramdor.objects.filter(soporte__soporte=asistente,finalizado=False).distinct('requerimiento').values('requerimiento')
                                requerimientosoporte =  RequerimientoSoporte.objects.filter(finalizado=False,id__in=idreqpr).order_by('-fecha')
                        else:
                            requerimientosoporte =  RequerimientoSoporte.objects.filter(soporte__soporte=asistente,finalizado=False).order_by('-fecha')
                else:
                    data['verasistentes'] = True
                    asistententes = AsistenteSoporte.objects.filter().order_by('persona')
                    data['asistententes'] = asistententes
                    if 'finali' in request.GET:
                        if 'idasis' in request.GET:
                            verasiiste = AsistenteSoporte.objects.get(id=request.GET['idasis'])
                            data['verasiiste'] = verasiiste
                            if verasiiste.programador:
                                idreqpr = RespProgramdor.objects.filter(soporte__soporte=verasiiste,finalizado=True).distinct('requerimiento').values('requerimiento')
                                idreqprfin = RespProgramdor.objects.filter(soporte__soporte=verasiiste,finalizado=True).exclude(requerimiento__id__in=idreqpr).distinct('requerimiento').values('requerimiento')
                                requerimientosoporte =  RequerimientoSoporte.objects.filter(Q(finalizado=True,id__in=idreqpr)| Q(id__in=idreqprfin)).order_by('-fecha')
                            else:
                                requerimientosoporte =  RequerimientoSoporte.objects.filter(soporte__soporte=verasiiste,finalizado=True).order_by('-fecha')

                        else:
                            requerimientosoporte =  RequerimientoSoporte.objects.filter(finalizado=True).order_by('-fecha')

                    elif 's' in request.GET:
                        search = request.GET['s']
                        data['search'] = search
                        ss = search.split(' ')
                        while '' in ss:
                            ss.remove('')
                        if len(ss)==1:
                            requerimientosoporte = RequerimientoSoporte.objects.filter(Q(persona__nombres__icontains=search) | Q(persona__apellido1__icontains=search) | Q(persona__apellido2__icontains=search) | Q(persona__cedula__icontains=search) | Q(persona__pasaporte__icontains=search)).order_by('persona__apellido1','-fecha')
                        else:
                            requerimientosoporte = RequerimientoSoporte.objects.filter(Q(persona__apellido1__icontains=ss[0]) & Q(persona__apellido2__icontains=ss[1])).order_by('persona__apellido1','persona__apellido2','persona__nombres','-fecha')

                    else:
                        if 'idasis' in request.GET:
                            verasiiste = AsistenteSoporte.objects.get(id=request.GET['idasis'])
                            data['verasiiste'] = verasiiste
                            if HorarioAsistente.objects.filter(soporte=verasiiste,fecha=datetime.now().date()).exists():
                                    data['asistente2']=HorarioAsistente.objects.filter(soporte=verasiiste,fecha=datetime.now().date())[:1].get()
                                    data['horarioasistente']=HorarioAsistente.objects.filter(soporte=verasiiste,fecha=datetime.now().date())[:1].get()
                            if verasiiste.programador:
                                idreqpr = RespProgramdor.objects.filter(soporte__soporte=verasiiste,finalizado=False).distinct('requerimiento').values('requerimiento')
                                requerimientosoporte =  RequerimientoSoporte.objects.filter(finalizado=False,id__in=idreqpr).order_by('-fecha')
                            else:
                                requerimientosoporte =  RequerimientoSoporte.objects.filter(soporte__soporte=verasiiste,finalizado=False)
                        else:
                            requerimientosoporte =  RequerimientoSoporte.objects.filter(finalizado=False).order_by('-fecha')
                    # soportehorarios = HorarioAsistente.objects.filter(fecha=datetime.now().date(),horainicio__lte=datetime.now().time(),horafin__gte=datetime.now().time(),programador=False).order_by("soporte__persona")
                    # OCastillo 16-nov-2021 para presentar a personal de soporte asi no tengan horario ingresado
                    soportehorarios = AsistenteSoporte.objects.filter(programador=False).order_by("persona")
                paging = MiPaginador(requerimientosoporte, 30)
                p=1
                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                    page = paging.page(p)
                except:
                    page = paging.page(1)
                if 'info' in request.GET:
                    data['info'] = request.GET['info']
                data['paging'] = paging
                data['page'] = page
                data['rangospaging'] = paging.rangos_paginado(p)
                data['finali'] = "finali" if 'finali' in request.GET else ""

                data['requerimientos'] = page.object_list
                data['soportehorarios'] = soportehorarios
                data['fechahoy'] = datetime.now()
                if VideoLogin.objects.filter(activo=True).exists():
                    data['videologin'] = VideoLogin.objects.filter(activo=True).order_by('-id')[:1].get()
                return render(request ,"soportereque/soportetics.html" ,  data)

    except Exception as e:
        print("ERROR SOPORTETICS "+str(e))
        return HttpResponseRedirect("/?info=Error comuniquese con el administrador"+str(e))