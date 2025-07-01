from datetime import datetime, timedelta
import json
import os
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models.query_utils import Q
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.utils.encoding import force_str
from decorators import secure_module
from settings import EMAIL_ACTIVE, MEDIA_ROOT
from sga.commonviews import addUserData, ip_client_address
from sga.forms import ActividadForm, ParticipanteActividadForm
from sga.funciones import MiPaginador, custom_render_to_response
from sga.models import Actividad,Persona, ParticipanteActividad, AulaAdministra, Aula, Clase, Materia, DIAS_CHOICES
from sga.reportes import elimina_tildes


@login_required(redirect_field_name='ret', login_url='/login')
# @secure_module
@transaction.atomic()
def view(request):
    if request.method == 'POST':
        action = request.POST['action']
        if action == 'add':
            try:
                f = ActividadForm(request.POST,request.FILES)
                msjaula=[]
                horario=[]
                if f.is_valid():
                    if f.cleaned_data['aula']  and f.cleaned_data['es_aula']:
                        act = Actividad.objects.filter(
                                    (Q(inicio__lte=f.cleaned_data['fechainicio']) & Q(fin__gte=f.cleaned_data['fechainicio'])) |
                                    (Q(inicio__lte=f.cleaned_data['fechafin']) & Q(fin__gte=f.cleaned_data['fechafin'])) |
                                    (Q(inicio__gte=f.cleaned_data['fechainicio']) & Q(fin__lte=f.cleaned_data['fechafin'])),auditorio= f.cleaned_data['aula'])
                        for acti in act:
                            if Actividad.objects.filter(
                                    Q((Q(horainicio=f.cleaned_data['horainicio']) & Q(horafin__gte=f.cleaned_data['horainicio'])) |
                                (Q(horainicio__lte=f.cleaned_data['horafin']) & Q(horafin__gte=f.cleaned_data['horafin'])) |
                                (Q(horainicio__gte=f.cleaned_data['horainicio']) & Q(horafin__lte=f.cleaned_data['horafin']))),Q(
                                Q(lunes=f.cleaned_data['lunes'])
                                |Q(martes=f.cleaned_data['martes'])
                                |Q( miercoles=f.cleaned_data['miercoles'])
                                |Q(viernes=f.cleaned_data['viernes'])
                                |Q(sabado=f.cleaned_data['sabado'])
                                |Q(domingo=f.cleaned_data['domingo'])), pk=acti.id).exists():
                                    return HttpResponseRedirect('/adm_calendario?action=add&formerror=Aula ocupada en ese horario ')

                    actividad = Actividad(periodo= f.cleaned_data['periodo'],
                                          nombre= f.cleaned_data['nombre'],
                                          inicio= f.cleaned_data['fechainicio'],
                                          horainicio= f.cleaned_data['horainicio'],
                                          fin=f.cleaned_data['fechafin'],
                                          horafin=f.cleaned_data['horafin'],
                                          tipo=f.cleaned_data['tipo'],
                                          lunes=f.cleaned_data['lunes'],
                                          martes=f.cleaned_data['martes'],
                                          miercoles=f.cleaned_data['miercoles'],
                                          jueves=f.cleaned_data['jueves'],
                                          viernes=f.cleaned_data['viernes'],
                                          sabado=f.cleaned_data['sabado'],
                                          domingo=f.cleaned_data['domingo'],
                                          departamento=f.cleaned_data['departamento'],
                                          usuario_id = request.user.pk,
                                          responsable_id = request.POST['rid'],
                                          lugar = f.cleaned_data['lugar'],
                                          adicional = f.cleaned_data['adicional'])
                    actividad.save()
                    if 'archivo' in request.FILES:
                        actividad.archivo = request.FILES['archivo']
                    if f.cleaned_data['auditorio']:
                        actividad.auditorio =f.cleaned_data['auditorio']
                    if f.cleaned_data['aula']:
                        actividad.auditorio =f.cleaned_data['aula']
                    actividad.save()
                    if actividad.auditorio:
                        if actividad.auditorio.tipo.id != 9:
                            aula = actividad.auditorio
                            fecha = actividad.inicio
                            dia=[]

                            while (fecha <= actividad.fin):
                                if datetime.weekday(fecha)== 0  and actividad.lunes :
                                    if not 1 in dia:
                                        dia.append(1)
                                if datetime.weekday(fecha)== 1  and actividad.martes :
                                    if not 2 in dia:
                                        dia.append(2)
                                if datetime.weekday(fecha)== 1  and actividad.miercoles :
                                    if not 3 in dia:
                                        dia.append(3)
                                if datetime.weekday(fecha)== 3  and actividad.jueves :
                                    if not 4 in dia:
                                        dia.append(4)
                                if datetime.weekday(fecha)== 4  and actividad.viernes :
                                    if not 5 in dia:
                                        dia.append(5)
                                if datetime.weekday(fecha)== 5  and actividad.sabado :
                                    if not 6 in dia:
                                        dia.append(6)
                                if datetime.weekday(fecha)== 6 and actividad.domingo :
                                    if not 7 in dia:
                                        dia.append(7)
                                fecha =fecha + timedelta(days=1)




                            materias_activas = Materia.objects.filter(
                                (Q(inicio__lte=actividad.inicio) & Q(fin__gte=actividad.inicio)) |
                                (Q(inicio__lte=actividad.fin) & Q(fin__gte=actividad.fin)) |
                                (Q(inicio__gte=actividad.inicio) & Q(fin__lte=actividad.fin)),
                                cerrado=False)
                            clases = Clase.objects.filter(
                                (Q(turno__comienza__lte=actividad.horainicio) & Q(turno__termina__gte=actividad.horainicio)) |
                                (Q(turno__comienza__lte=actividad.horafin) & Q(turno__termina__gte=actividad.horafin)) |
                                (Q(turno__comienza__gte=actividad.horainicio) & Q(turno__termina__lte=actividad.horafin)), materia__in=materias_activas,dia__in=dia,aula=aula,materia__inicio__gte=actividad.inicio).order_by('dia')
                            if clases.count()>0:
                                for x in clases:
                                    horario.append((x.materia.nivel.nivelmalla.nombre,x.materia.nivel.paralelo,x.materia.asignatura.nombre,x.turno.comienza,x.turno.termina,DIAS_CHOICES[x.dia-1][1]))

                    if f.cleaned_data['es_auditorio']:

                        fecha = actividad.inicio
                        while (fecha <= actividad.fin):
                            aulaadministra=None
                            if datetime.weekday(fecha)== 0  and actividad.lunes :
                                 aulaadministra = AulaAdministra(
                                                aula_id = request.POST['auditorio'],
                                                motivo = actividad.nombre,
                                                fecha = fecha,
                                                horainicio = actividad.horainicio,
                                                horafin = actividad.horafin,
                                                user = request.user,
                                                fechaingreso = datetime.now(),
                                                actividad=actividad)
                            if datetime.weekday(fecha)== 1 and actividad.martes :
                                 aulaadministra = AulaAdministra(
                                                aula_id = request.POST['auditorio'],
                                                motivo = actividad.nombre,
                                                fecha = fecha,
                                                horainicio = actividad.horainicio,
                                                horafin = actividad.horafin,
                                                user = request.user,
                                                fechaingreso = datetime.now(),
                                                actividad=actividad)
                            if datetime.weekday(fecha)== 2 and actividad.miercoles :
                                 aulaadministra = AulaAdministra(
                                                aula_id = request.POST['auditorio'],
                                                motivo = actividad.nombre,
                                                fecha = fecha,
                                                horainicio = actividad.horainicio,
                                                horafin = actividad.horafin,
                                                user = request.user,
                                                fechaingreso = datetime.now(),
                                                actividad=actividad)
                            if datetime.weekday(fecha)== 3 and actividad.jueves :
                                 aulaadministra = AulaAdministra(
                                                aula_id = request.POST['auditorio'],
                                                motivo = actividad.nombre,
                                                fecha = fecha,
                                                horainicio = actividad.horainicio,
                                                horafin = actividad.horafin,
                                                user = request.user,
                                                fechaingreso = datetime.now(),
                                                actividad=actividad)
                            if datetime.weekday(fecha)== 4 and actividad.viernes :
                                 aulaadministra = AulaAdministra(
                                                aula_id = request.POST['auditorio'],
                                                motivo = actividad.nombre,
                                                fecha = fecha,
                                                horainicio = actividad.horainicio,
                                                horafin = actividad.horafin,
                                                user = request.user,
                                                fechaingreso = datetime.now(),
                                                actividad=actividad)
                            if datetime.weekday(fecha)== 5 and actividad.sabado :
                                 aulaadministra = AulaAdministra(
                                                aula_id = request.POST['auditorio'],
                                                motivo = actividad.nombre,
                                                fecha = fecha,
                                                horainicio = actividad.horainicio,
                                                horafin = actividad.horafin,
                                                user = request.user,
                                                fechaingreso = datetime.now(),
                                                actividad=actividad)
                            if datetime.weekday(fecha)== 6 and actividad.domingo :
                                 aulaadministra = AulaAdministra(
                                                aula_id = request.POST['auditorio'],
                                                motivo = actividad.nombre,
                                                fecha = fecha,
                                                horainicio = actividad.horainicio,
                                                horafin = actividad.horafin,
                                                user = request.user,
                                                fechaingreso = datetime.now(),
                                                actividad=actividad)
                            if aulaadministra:

                                if AulaAdministra.objects.filter(Q(aula= request.POST['auditorio']),Q(fecha=fecha),
                                                         (Q(horainicio__lte=actividad.horainicio) & Q(horafin__gte=actividad.horainicio)) |
                                                         (Q(horainicio__lte=actividad.horafin) & Q(horafin__gte=actividad.horafin)) |
                                                         (Q(horainicio__gte=actividad.horainicio) & Q(horafin__lte=actividad.horafin))).exists():
                                    msjaula.append((fecha,actividad.horainicio,actividad.horafin, Aula.objects.filter(pk=request.POST['auditorio'])[:1].get()))
                                else:
                                    aulaadministra.save()

                            fecha =fecha + timedelta(days=1)

                    client_address = ip_client_address(request)

                    if EMAIL_ACTIVE:
                        if actividad.responsable.emailinst:
                            actividad.mail_responsactividad("RESPONSABLE DE ACTIVIDAD")
                        if msjaula:
                            actividad.notificacion(msjaula,'AUDITORIO SE ENCUENTRA OCUPADO EN LAS SIGUIENTES FECHAS',1)
                        if horario:
                            actividad.notificacion(horario,'AULA  SE ENCUENTRA OCUPADA EN LAS SIGUIENTES FECHAS',0)


                    # LOG DE CREAR UNA ACTIVIDAD
                    LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(actividad).pk,
                    object_id       = actividad.id,
                    object_repr     = force_str(actividad),
                    action_flag     = ADDITION,
                    change_message  = 'Creada una Actividad (' + client_address + ')' )
                    if 'participante' in request.POST:
                        return HttpResponseRedirect("/adm_calendario?action=addparticipante&id="+str(actividad.id))
                    else:
                        return HttpResponseRedirect('/adm_calendario?id='+str(actividad.id))
                raise
            except Exception as e:
                transaction.set_rollback(True)
                return HttpResponseRedirect('/adm_calendario?action=add&formerror=0')

        elif action == 'edit':
            try:
                actividad = Actividad.objects.get(pk=request.POST['id'])
                f = ActividadForm(request.POST,request.FILES)
                msjaula=[]
                horario=[]
                if f.is_valid():
                    if f.cleaned_data['aula'] and f.cleaned_data['es_aula']:
                        act = Actividad.objects.filter(
                                    (Q(inicio__lte=f.cleaned_data['fechainicio']) & Q(fin__gte=f.cleaned_data['fechainicio'])) |
                                    (Q(inicio__lte=f.cleaned_data['fechafin']) & Q(fin__gte=f.cleaned_data['fechafin'])) |
                                    (Q(inicio__gte=f.cleaned_data['fechainicio']) & Q(fin__lte=f.cleaned_data['fechafin'])),auditorio= f.cleaned_data['aula']).exclude(id=actividad.id)
                        for acti in act:
                            if Actividad.objects.filter(
                                    Q((Q(horainicio=f.cleaned_data['horainicio']) & Q(horafin__gte=f.cleaned_data['horainicio'])) |
                                (Q(horainicio__lte=f.cleaned_data['horafin']) & Q(horafin__gte=f.cleaned_data['horafin'])) |
                                (Q(horainicio__gte=f.cleaned_data['horainicio']) & Q(horafin__lte=f.cleaned_data['horafin']))),Q(
                                Q(lunes=f.cleaned_data['lunes'])
                                |Q(martes=f.cleaned_data['martes'])
                                |Q( miercoles=f.cleaned_data['miercoles'])
                                |Q(viernes=f.cleaned_data['viernes'])
                                |Q(sabado=f.cleaned_data['sabado'])
                                |Q(domingo=f.cleaned_data['domingo'])), pk=acti.id).exclude(id=actividad.id).exists():
                                    return HttpResponseRedirect('/adm_calendario?action=add&formerror=Aula ocupada en ese horario ')
                    responsable = actividad.responsable_id
                    actividad.periodo = f.cleaned_data['periodo']
                    actividad.nombre = f.cleaned_data['nombre']
                    actividad.tipo = f.cleaned_data['tipo']
                    actividad.inicio = f.cleaned_data['fechainicio']
                    actividad.horainicio = f.cleaned_data['horainicio']
                    actividad.fin = f.cleaned_data['fechafin']
                    actividad.horafin = f.cleaned_data['horafin']
                    actividad.lunes = f.cleaned_data['lunes']
                    actividad.martes = f.cleaned_data['martes']
                    actividad.miercoles = f.cleaned_data['miercoles']
                    actividad.jueves = f.cleaned_data['jueves']
                    actividad.viernes = f.cleaned_data['viernes']
                    actividad.sabado = f.cleaned_data['sabado']
                    actividad.domingo = f.cleaned_data['domingo']
                    actividad.departamento = f.cleaned_data['departamento']
                    actividad.responsable_id = request.POST['rid']
                    actividad.usuario_id = request.user.pk
                    actividad.lugar = f.cleaned_data['lugar']
                    actividad.adicional = f.cleaned_data['adicional']
                    actividad.save()
                    if actividad.archivo:
                        if (MEDIA_ROOT + '/' + str(actividad.archivo)):
                            os.remove(MEDIA_ROOT + '/' + str(actividad.archivo))
                    if f.cleaned_data['auditorio']:
                        actividad.auditorio =f.cleaned_data['auditorio']
                    if f.cleaned_data['aula']:
                        actividad.auditorio =f.cleaned_data['aula']
                    actividad.save()
                    aulaadmin = AulaAdministra.objects.filter(actividad=actividad)
                    aulaadmin.delete()
                    if 'archivo' in request.FILES:
                        actividad.archivo = request.FILES['archivo']
                    else:
                        actividad.archivo=''
                    actividad.save()
                    if actividad.auditorio:
                        if actividad.auditorio.tipo.id != 9:
                            aula = actividad.auditorio
                            fecha = actividad.inicio
                            dia=[]
                            while (fecha <= actividad.fin):
                                if datetime.weekday(fecha)== 0  and actividad.lunes :
                                    if not 1 in dia:
                                        dia.append(1)
                                if datetime.weekday(fecha)== 1  and actividad.martes :
                                    if not 2 in dia:
                                        dia.append(2)
                                if datetime.weekday(fecha)== 1  and actividad.miercoles :
                                    if not 3 in dia:
                                        dia.append(3)
                                if datetime.weekday(fecha)== 3  and actividad.jueves :
                                    if not 4 in dia:
                                        dia.append(4)
                                if datetime.weekday(fecha)== 4  and actividad.viernes :
                                    if not 5 in dia:
                                        dia.append(5)
                                if datetime.weekday(fecha)== 5  and actividad.sabado :
                                    if not 6 in dia:
                                        dia.append(6)
                                if datetime.weekday(fecha)== 6 and actividad.domingo :
                                    if not 7 in dia:
                                        dia.append(7)
                                fecha =fecha + timedelta(days=1)
                            materias_activas = Materia.objects.filter(
                                (Q(inicio__lte=actividad.inicio) & Q(fin__gte=actividad.inicio)) |
                                (Q(inicio__lte=actividad.fin) & Q(fin__gte=actividad.fin)) |
                                (Q(inicio__gte=actividad.inicio) & Q(fin__lte=actividad.fin)),
                                cerrado=False)
                            clases = Clase.objects.filter(
                                (Q(turno__comienza__lte=actividad.horainicio) & Q(turno__termina__gte=actividad.horainicio)) |
                                (Q(turno__comienza__lte=actividad.horafin) & Q(turno__termina__gte=actividad.horafin)) |
                                (Q(turno__comienza__gte=actividad.horainicio) & Q(turno__termina__lte=actividad.horafin)), materia__in=materias_activas,dia__in=dia,aula=aula,materia__inicio__gte=actividad.inicio).order_by('dia')
                            if clases.count()>0:
                                for x in clases:
                                    horario.append((x.materia.nivel.nivelmalla.nombre,x.materia.nivel.paralelo,x.materia.asignatura.nombre,x.turno.comienza,x.turno.termina,DIAS_CHOICES[x.dia-1][1]))


                    if f.cleaned_data['es_auditorio']:

                        fecha = actividad.inicio
                        while (fecha <= actividad.fin):
                            aulaadministra =None
                            if datetime.weekday(fecha)== 0  and actividad.lunes :
                                 aulaadministra = AulaAdministra(
                                                aula_id = request.POST['auditorio'],
                                                motivo = actividad.nombre,
                                                fecha = fecha,
                                                horainicio = actividad.horainicio,
                                                horafin = actividad.horafin,
                                                user = request.user,
                                                fechaingreso = datetime.now(),
                                                actividad=actividad)
                            if datetime.weekday(fecha)== 1 and actividad.martes :
                                 aulaadministra = AulaAdministra(
                                                aula_id = request.POST['auditorio'],
                                                motivo = actividad.nombre,
                                                fecha = fecha,
                                                horainicio = actividad.horainicio,
                                                horafin = actividad.horafin,
                                                user = request.user,
                                                fechaingreso = datetime.now(),
                                                actividad=actividad)
                            if datetime.weekday(fecha)== 2 and actividad.miercoles :
                                 aulaadministra = AulaAdministra(
                                                aula_id = request.POST['auditorio'],
                                                motivo = actividad.nombre,
                                                fecha = fecha,
                                                horainicio = actividad.horainicio,
                                                horafin = actividad.horafin,
                                                user = request.user,
                                                fechaingreso = datetime.now(),
                                                actividad=actividad)
                            if datetime.weekday(fecha)== 3 and actividad.jueves :
                                 aulaadministra = AulaAdministra(
                                                aula_id = request.POST['auditorio'],
                                                motivo = actividad.nombre,
                                                fecha = fecha,
                                                horainicio = actividad.horainicio,
                                                horafin = actividad.horafin,
                                                user = request.user,
                                                fechaingreso = datetime.now(),
                                                actividad=actividad)
                            if datetime.weekday(fecha)== 4 and actividad.viernes :
                                 aulaadministra = AulaAdministra(
                                                aula_id = request.POST['auditorio'],
                                                motivo = actividad.nombre,
                                                fecha = fecha,
                                                horainicio = actividad.horainicio,
                                                horafin = actividad.horafin,
                                                user = request.user,
                                                fechaingreso = datetime.now(),
                                                actividad=actividad)
                            if datetime.weekday(fecha)== 5 and actividad.sabado :
                                 aulaadministra = AulaAdministra(
                                                aula_id = request.POST['auditorio'],
                                                motivo = actividad.nombre,
                                                fecha = fecha,
                                                horainicio = actividad.horainicio,
                                                horafin = actividad.horafin,
                                                user = request.user,
                                                fechaingreso = datetime.now(),
                                                actividad=actividad)
                            if datetime.weekday(fecha)== 6 and actividad.domingo :
                                 aulaadministra = AulaAdministra(
                                                aula_id = request.POST['auditorio'],
                                                motivo = actividad.nombre,
                                                fecha = fecha,
                                                horainicio = actividad.horainicio,
                                                horafin = actividad.horafin,
                                                user = request.user,
                                                fechaingreso = datetime.now(),
                                                actividad=actividad)
                            if aulaadministra:

                                if AulaAdministra.objects.filter(Q(aula= request.POST['auditorio']),Q(fecha=fecha),
                                                         (Q(horainicio__lte=actividad.horainicio) & Q(horafin__gte=actividad.horafin)) |
                                                         (Q(horainicio__lte=actividad.horafin) & Q(horafin__gte=actividad.horafin)) |
                                                         (Q(horainicio__gte=actividad.horainicio) & Q(horafin__lte=actividad.horafin))).exists():
                                    msjaula.append((fecha,actividad.horainicio,actividad.horafin, Aula.objects.filter(pk=request.POST['auditorio'])[:1].get()))
                                else:
                                    aulaadministra.save()

                            fecha =fecha + timedelta(days=1)

                    client_address = ip_client_address(request)
                    if EMAIL_ACTIVE:
                        if msjaula:
                            actividad.notificacion(msjaula,'AUDOTORIO  SE ENCUENTRA OCUPADO EN LAS SIGUIENTES FECHAS',1)
                        if horario:
                            actividad.notificacion(horario,'AULA  SE ENCUENTRA OCUPADA EN LAS SIGUIENTES FECHAS',0)
                        if responsable != int(request.POST['rid']):
                            if EMAIL_ACTIVE:
                                if actividad.responsable.emailinst:
                                    actividad.mail_responsactividad("RESPONSABLE DE ACTIVIDAD")

                    # LOG DE EDITAR UNA ACTIVIDAD
                    LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(actividad).pk,
                    object_id       = actividad.id,
                    object_repr     = force_str(actividad),
                    action_flag     = CHANGE,
                    change_message  = 'Editada una Actividad (' + client_address + ')' )

                    if 'participante' in request.POST:
                        return HttpResponseRedirect("/adm_calendario?action=addparticipante&id="+str(actividad.id))
                    else:
                        return HttpResponseRedirect('/adm_calendario?id='+str(actividad.id))
                raise
            except Exception as e:
                print(e)
                transaction.set_rollback(True)
                return HttpResponseRedirect('/adm_calendario?action=edit&formerror='+str(e)+'&id=' + request.POST['id'])

        elif action =='addparticipante':
            try:
                datos = json.loads(request.POST['datos'])
                actividad = Actividad.objects.get(id=request.POST['actividad'])
                if datos != "":
                    if ParticipanteActividad.objects.filter(actividad = actividad).exists():
                        for part in ParticipanteActividad.objects.filter(actividad = actividad):
                            exist= 0
                            for d in datos:
                                if part.participante_id == int(d['persona']):
                                    exist = 1
                            if exist == 0:
                                part.delete()

                    for d in datos:
                        if not ParticipanteActividad.objects.filter(actividad = actividad,participante__id = int(d['persona'])).exists():
                            participanteact = ParticipanteActividad(
                                            actividad = actividad,
                                            participante_id = int(d['persona']))
                            participanteact.save()


                            if EMAIL_ACTIVE:
                                if participanteact.participante.emailinst:
                                    participanteact.mail_particiactividad("PARTICIPANTE DE ACTIVIDAD")

                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                else:
                    return HttpResponse(json.dumps({"result":"badreg"}),content_type="application/json")
            except Exception as ex:
                transaction.set_rollback(True)
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
        elif action == 'listparti':
            try:
                data={}

                data["personas"]=[{"persona": str(str(x.participante.id)+' - '+elimina_tildes(x.participante.nombre_completo())) } for x in ParticipanteActividad.objects.filter(actividad__id=request.POST['id'])]
                data['result'] = "ok"

                return HttpResponse(json.dumps(data),content_type="application/json")
            except:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
        elif action == 'del':
            try:
                actividad = Actividad.objects.get(pk=request.POST['id'])
                if AulaAdministra.objects.filter(actividad=actividad).exists():
                    AulaAdministra.objects.filter(actividad=actividad).delete()

                client_address = ip_client_address(request)

                # LOG DE ELIMINAR UNA ACTIVIDAD
                LogEntry.objects.log_action(
                user_id         = request.user.pk,
                content_type_id = ContentType.objects.get_for_model(actividad).pk,
                object_id       = actividad.id,
                object_repr     = force_str(actividad),
                action_flag     = DELETION,
                change_message  = 'Eliminada una Actividad (' + client_address + ')' )

                actividad.delete()
                return HttpResponseRedirect('/adm_calendario?error=Registro Eliminado con Exito')
            except:
                transaction.set_rollback(True)
                return HttpResponseRedirect('/adm_calendario?action=del&formerror=0&id=' + request.POST['id'])

        return HttpResponseRedirect('/adm_calendario')
    else:
        data = {}
        addUserData(request, data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action == 'add':
                try:
                    data['title'] = 'Adicionar Actividad'
                    form = ActividadForm(initial={'fechainicio': datetime.now().date(),
                                                  'fechafin': datetime.now().date(),
                                                  'periodo': data['periodo']})
                    data['form'] = form
                    return custom_render_to_response('adm_calendario/adicionarbs.html', data, request)
                except:
                    pass

            elif action == 'del':
                try:
                    data['title'] = 'Eliminar Actividad'
                    data['actividad'] = Actividad.objects.get(pk=request.GET['id'])
                    if AulaAdministra.objects.filter(actividad=data['actividad']).exists():
                        data['aula'] = AulaAdministra.objects.filter(actividad=data['actividad']).count()

                    return custom_render_to_response('adm_calendario/borrarbs.html', data, request)
                except:
                    return HttpResponseRedirect('/adm_calendario?error=Ocurrio un error al eliminar.. Favor vuelva a intentarlo&id='+str(request.GET['id']))

            elif action == 'addparticipante':
                addUserData(request,data)
                data['title'] = 'Agregar Participantes'
                data['actividad'] = Actividad.objects.get(id=request.GET['id'])
                data['personasact'] = Persona.objects.filter().exclude(usuario__groups__id=6)
                form = ParticipanteActividadForm()
                data['form'] = form

                return custom_render_to_response("adm_calendario/participantes.html", data,request)

            elif action == 'editparticipante':
                addUserData(request,data)
                data['title'] = 'Agregar Participantes'
                data['actividad'] = Actividad.objects.get(id=request.GET['id'])
                data['participantes'] = ParticipanteActividad.objects.filter(actividad=data['actividad'])
                data['personasact'] = Persona.objects.filter().exclude(usuario__groups__id=6)
                form = ParticipanteActividadForm()
                data['form'] = form

                return custom_render_to_response("adm_calendario/participantes.html", data,request)

            elif action == 'edit':
                try:
                    data['title'] = 'Editar Actividad'
                    actividad = Actividad.objects.get(pk=request.GET['id'])
                    auditorio=''
                    aula=''
                    if actividad.auditorio:
                        if actividad.auditorio.tipo.id==9:
                            auditorio = actividad.auditorio
                        else:
                            aula = actividad.auditorio
                    form = ActividadForm(initial={'periodo': actividad.periodo,
                                                 'nombre': actividad.nombre,
                                                 'tipo': actividad.tipo,
                                                 'auditorio': auditorio,
                                                 'aula' : aula,
                                                 'fechainicio': actividad.inicio,
                                                 'horainicio': actividad.horainicio,
                                                 'fechafin': actividad.fin,
                                                 'horafin': actividad.horafin,
                                                 'lunes': actividad.lunes,
                                                 'martes': actividad.martes,
                                                 'miercoles': actividad.miercoles,
                                                 'jueves': actividad.jueves,
                                                 'viernes': actividad.viernes,
                                                 'sabado': actividad.sabado,
                                                 'domingo': actividad.domingo,
                                                 'departamento': actividad.departamento,
                                                 'responsable': actividad.responsable,
                                                 'archivo': actividad.archivo,
                                                 'lugar': actividad.lugar,
                                                 'adicional': actividad.adicional})
                    data['form'] = form
                    data['actividad'] = actividad
                    return custom_render_to_response('adm_calendario/editarbs.html', data, request)
                except:
                    pass

            return HttpResponseRedirect('/adm_calendario')

        else:
            data['title'] = 'CALENDARIO DE ACTIVIDADES'
            # data['periodo'] = request.session['periodo']
            search = None
            if 's' in request.GET:
                search = request.GET['s']
            if 'error' in request.GET:
                data['error'] = request.GET['error']
            if search:
                actividades = Actividad.objects.filter(nombre__icontains=search).order_by('-inicio')
            else:
                if 'id' in request.GET:
                    actividades = Actividad.objects.filter(pk=request.GET['id']).order_by('-inicio')
                else:

                    actividades = Actividad.objects.all().order_by('-inicio')

            paging = MiPaginador(actividades, 50)
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
            data['usuarioelim'] = request.user.pk
            data['actividades'] = page.object_list
            data['search'] = search if search else ""

            return custom_render_to_response('adm_calendario/actividadesbs.html', data, request)
