from django.contrib.contenttypes.models import ContentType
from settings import MEDIA_ROOT

__author__ = 'wferruzola'
from datetime import datetime, timedelta, time
import json
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
import xlwt
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
import psycopg2
from sga.commonviews import addUserData, ip_client_address

from sga.models import ActividadesHorasExtra, TituloInstitucion, elimina_tildes, Persona, SupervisorGrupos, RolPago, \
    MONTH_CHOICES, ViewVacaciones


# @transaction.atomic()
# @secure_module

def calcular_horas_timedelta(horas_totales):
    sin_milisegundos = str(horas_totales).split(".")[0]
    horas = int(str(sin_milisegundos).split(' days,')[1].split(':')[0]) if horas_totales.days > 1 else int(
        str(sin_milisegundos).split(' day,')[1].split(':')[0])
    dias_totales = horas + (horas_totales.days * 24)
    return str(dias_totales) + ":" + str(horas_totales).split(",")[1].split(':')[1] + ":" + str(horas_totales).split(",")[1].split(':')[2]

def quitar_hora_almuerzo(horas_totales):
    horas_totales = str(horas_totales)
    hora_timedelta =  timedelta(hours=int(horas_totales.split(':')[0]), minutes=int(horas_totales.split(':')[1]), seconds=float(horas_totales.split(':')[2]))
    if hora_timedelta.days >= 1:
        horas_totales = str(int(str(horas_totales).split(':')[0]) - (1 * hora_timedelta.days)) + ":" + str(horas_totales).split(':')[1] + ":" + str(horas_totales).split(':')[2].split('.')[0]
        return horas_totales
    else:
        if hora_timedelta.total_seconds() // 3600  >= 9:
            horas_totales = str(int(str(horas_totales).split(':')[0]) - 1)+":"+str(horas_totales).split(':')[1]+":"+ str(horas_totales).split(':')[2].split('.')[0]
            return horas_totales
        else:
            return horas_totales


def view(request):
    try:
        if request.method == 'POST':
            action = request.POST['action']
            if action == 'add':
                data = {}
                try:
                    fecha_inicio = datetime.now()
                    actividad = ActividadesHorasExtra(usuario=request.user,
                                                      descripcion=request.POST['descripcion'].strip(),
                                                      fecha_inicio=fecha_inicio)
                    actividad.save()
                    data['result'] = 'ok'
                    client_address = ip_client_address(request)
                    # Log de ADD Hora Extra
                    LogEntry.objects.log_action(
                        user_id=request.user.pk,
                        content_type_id=ContentType.objects.get_for_model(actividad).pk,
                        object_id=actividad.id,
                        object_repr=force_str(actividad),
                        action_flag=ADDITION,
                        change_message='Agregar Actividad de Horas Extras (' + client_address + ')')

                    return HttpResponse(json.dumps(data),content_type="application/json")
                except Exception as ex:
                    print(ex)
                    return HttpResponse(json.dumps(data),content_type="application/json")
            if action == 'add_actividad_atrasada':
                data = {}
                try:
                    fecha_inicio = datetime.strptime(
                        str(request.POST['fechainicio']) + ' ' + str(request.POST['horainicio']), '%Y-%m-%d %H:%M')
                    fecha_fin = datetime.strptime(str(request.POST['fechafin']) + ' ' + str(request.POST['horafin']),
                                                  '%Y-%m-%d %H:%M')
                    horas_totales = (fecha_fin - fecha_inicio)
                    if horas_totales.days > 0:
                        horas_totales = calcular_horas_timedelta(horas_totales)

                    horas_totales = quitar_hora_almuerzo(horas_totales)
                    actividad = ActividadesHorasExtra(usuario=request.user,
                                                      descripcion=request.POST['descripcion'].strip(),
                                                      finalizado=True,
                                                      fecha_inicio=fecha_inicio,
                                                      fecha_fin=fecha_fin,
                                                      horas_extras=str(horas_totales))

                    actividad.save()
                    data['result'] = 'ok'
                    client_address = ip_client_address(request)
                    # Log de ADD Hora Extra
                    LogEntry.objects.log_action(
                        user_id=request.user.pk,
                        content_type_id=ContentType.objects.get_for_model(actividad).pk,
                        object_id=actividad.id,
                        object_repr=force_str(actividad),
                        action_flag=ADDITION,
                        change_message='Actividad Atrasada de Horas Extras (' + client_address + ')')

                    return HttpResponse(json.dumps(data),content_type="application/json")
                except Exception as ex:
                    print(ex)
                    return HttpResponse(json.dumps(data),content_type="application/json")
            elif action == 'editar':
                data = {}
                try:
                    actividad = ActividadesHorasExtra.objects.get(id=int(request.POST['id']))
                    actividad.descripcion = request.POST['descripcion'].strip()
                    actividad.fecha_inicio = datetime.strptime(request.POST['fechainicio'],'%Y-%m-%d %H:%M')
                    actividad.fecha_fin = datetime.strptime(request.POST['fechafin'],'%Y-%m-%d %H:%M')
                    horas_totales = (actividad.fecha_fin - actividad.fecha_inicio)
                    if horas_totales.days > 0:
                        horas_totales = calcular_horas_timedelta(horas_totales)
                    horas_totales = quitar_hora_almuerzo(horas_totales)
                    actividad.usuario_modifica = request.user
                    actividad.horas_extras = horas_totales
                    actividad.save()

                    data['result'] = 'ok'
                    client_address = ip_client_address(request)
                    # Log de Edit Hora Extra
                    LogEntry.objects.log_action(
                        user_id=request.user.pk,
                        content_type_id=ContentType.objects.get_for_model(actividad).pk,
                        object_id=actividad.id,
                        object_repr=force_str(actividad),
                        action_flag=CHANGE,
                        change_message='Editar Actividad de Horas Extras (' + client_address + ')')
                    return HttpResponse(json.dumps(data),content_type="application/json")
                except Exception as ex:
                    print(ex)
                    return HttpResponse(json.dumps(data),content_type="application/json")
            elif action == 'eliminar':
                data = {}
                try:
                    actividad = ActividadesHorasExtra.objects.get(id=request.POST['id'])
                    actividad.delete()
                    data['result'] = 'ok'
                    client_address = ip_client_address(request)
                    # Log de Edit Hora Extra
                    LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(actividad).pk,
                            object_id       = actividad.id,
                            object_repr     = force_str(actividad),
                            action_flag     = DELETION,
                            change_message  = 'Eliminar Actividad de Horas Extras (' + client_address + ')')
                    return HttpResponse(json.dumps(data),content_type="application/json")
                except Exception as ex:
                    print(ex)
                    return HttpResponse(json.dumps(data),content_type="application/json")

            elif action == 'finalizar':
                data = {}
                try:
                    fecha_fin = datetime.now()

                    actividad = ActividadesHorasExtra.objects.get(id=int(request.POST['id']))
                    actividad.fecha_fin = fecha_fin
                    # actividad.usuario_modifica = request.user
                    actividad.finalizado = True
                    horas_totales = (actividad.fecha_fin - actividad.fecha_inicio)
                    if horas_totales.days > 0:
                        horas_totales = calcular_horas_timedelta(horas_totales)
                    else:
                        horas_totales = str(horas_totales).split(".")[0]
                    horas_totales = quitar_hora_almuerzo(horas_totales)
                    actividad.horas_extras = horas_totales
                    actividad.save()

                    data['result'] = 'ok'
                    client_address = ip_client_address(request)
                    # Log de Finalizar Hora Extra
                    LogEntry.objects.log_action(
                        user_id=request.user.pk,
                        content_type_id=ContentType.objects.get_for_model(actividad).pk,
                        object_id=actividad.id,
                        object_repr=force_str(actividad),
                        action_flag=CHANGE,
                        change_message='Finalizar Actividad de Horas Extras (' + client_address + ')')
                    return HttpResponse(json.dumps(data),content_type="application/json")
                except Exception as ex:
                    print(ex)
                    return HttpResponse(json.dumps(data),content_type="application/json")

            elif action == 'excel':

                try:


                    anio = datetime.now().year
                    # rol = RolPago.objects.filter(fin__year = anio, fin__month = int(request.POST['mescorte']) )[:1].get()
                    #
                    # fecha_desde = rol.inicio
                    # fecha_hasta = rol.fin

                    if RolPago.objects.filter(fin__year=int(request.POST['aniocorte']), fin__month=int(request.POST['mescorte'])).exists():
                        rol = RolPago.objects.filter(fin__year=int(request.POST['aniocorte']), fin__month=int(request.POST['mescorte']))[:1].get()
                        fecha_desde = rol.inicio
                        fecha_hasta = datetime.combine(rol.fin, time(23, 59, 59))
                    else:
                        meshasta = int(request.POST['mescorte'])
                        if int(request.POST['mescorte']) != 1:
                            fecha_desde = datetime(int(request.POST['aniocorte']),int(request.POST['mescorte']) - 1, 22).date()
                        else:
                            fecha_desde = datetime(int(request.POST['aniocorte']) - 1, 12, 22).date()
                        fecha_hasta = datetime(int(request.POST['aniocorte']), int(request.POST['mescorte']), 21,23,59,59)


                    if request.POST['tipo'] == 'director':
                        if request.POST['actividades'] == '1':
                            supervisor = SupervisorGrupos.objects.filter(director__usuario = request.user).values_list('grupo')
                            actividades = ActividadesHorasExtra.objects.filter(fecha_inicio__gte=fecha_desde,
                                                                               fecha_fin__lte=fecha_hasta,
                                                                               finalizado=True,

                                                                               enviar_supervisor = True,
                                                                               enviar_director = True,
                                                                               aprobado_director = True,
                                                                               usuario__groups__in = supervisor ).order_by('usuario')
                        else:
                            supervisor = SupervisorGrupos.objects.filter(director__usuario = request.user).values_list('grupo')
                            actividades = ActividadesHorasExtra.objects.filter(fecha_inicio__gte=fecha_desde,
                                                                               fecha_fin__lte=fecha_hasta,
                                                                               finalizado=True,

                                                                               enviar_supervisor = True,
                                                                               enviar_director = False,
                                                                               aprobado_director = True,
                                                                               usuario__groups__in = supervisor ).order_by('usuario')
                    elif request.POST['tipo'] == 'supervisor':
                        if request.POST['actividades'] == '1':
                            supervisor = SupervisorGrupos.objects.filter(supervisor__usuario = request.user).values_list('grupo')
                            actividades = ActividadesHorasExtra.objects.filter(fecha_inicio__gte=fecha_desde,
                                                                               fecha_fin__lte=fecha_hasta,
                                                                               finalizado=True,

                                                                               enviar_supervisor = True,
                                                                               aprobado_supervisor = True,
                                                                               usuario__groups__in = supervisor ).order_by('usuario')
                        else:
                            supervisor = SupervisorGrupos.objects.filter(supervisor__usuario = request.user).values_list('grupo')
                            actividades = ActividadesHorasExtra.objects.filter(fecha_inicio__gte=fecha_desde,
                                                                               fecha_fin__lte=fecha_hasta,
                                                                               finalizado=True,

                                                                               enviar_supervisor = False,
                                                                               aprobado_supervisor = True,
                                                                               usuario__groups__in = supervisor ).order_by('usuario')
                    elif request.POST['tipo'] == 'talento':
                        if request.POST['actividades'] == '1':
                            supervisor = SupervisorGrupos.objects.filter().values_list('grupo')
                            actividades = ActividadesHorasExtra.objects.filter(fecha_inicio__gte=fecha_desde,
                                                                               fecha_fin__lte=fecha_hasta,
                                                                               finalizado=True,

                                                                               enviar_director = True,
                                                                               enviar_talento = True,
                                                                               aprobado_talento = True,
                                                                               usuario__groups__in = supervisor ).order_by('usuario')
                        else:
                            supervisor = SupervisorGrupos.objects.filter().values_list('grupo')
                            actividades = ActividadesHorasExtra.objects.filter(fecha_inicio__gte=fecha_desde,
                                                                               fecha_fin__lte=fecha_hasta,
                                                                               finalizado=True,

                                                                               enviar_director = True,
                                                                               enviar_talento = False,
                                                                               aprobado_talento = True,
                                                                               usuario__groups__in = supervisor ).order_by('usuario')
                    elif request.POST['tipo'] == 'auditor':
                         if request.POST['actividades'] == '1':
                            supervisor = SupervisorGrupos.objects.filter().values_list('grupo')
                            actividades = ActividadesHorasExtra.objects.filter(fecha_inicio__gte=fecha_desde,
                                                                               fecha_fin__lte=fecha_hasta,
                                                                               finalizado=True,

                                                                               enviar_talento = True,
                                                                               enviar_auditoria = True,
                                                                               aprobado_auditoria = True,
                                                                               usuario__groups__in = supervisor ).order_by('usuario')
                         else:
                            supervisor = SupervisorGrupos.objects.filter().values_list('grupo')
                            actividades = ActividadesHorasExtra.objects.filter(fecha_inicio__gte=fecha_desde,
                                                                               fecha_fin__lte=fecha_hasta,
                                                                               finalizado=True,

                                                                               enviar_talento = True,
                                                                               enviar_auditoria = False,
                                                                               aprobado_auditoria = True,
                                                                               usuario__groups__in = supervisor ).order_by('usuario')


                    if actividades:
                        personas_actividades = actividades.distinct('usuario').values_list('usuario', flat=True)

                        borders = xlwt.Borders()
                        borders.left = xlwt.Borders.THIN
                        borders.right = xlwt.Borders.THIN
                        borders.top = xlwt.Borders.THIN
                        borders.bottom = xlwt.Borders.THIN

                        m = 10
                        titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                        titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                        titulo.font.height = 20 * 11
                        titulo2.font.height = 20 * 11
                        subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                        subtitulo3 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center;'
                                                 'pattern: pattern solid, fore_colour silver_ega;')
                        subtitulo.font.height = 20 * 10
                        celdas = xlwt.easyxf('font: name Times New Roman')
                        celdas.borders = borders
                        subtitulo3.borders = borders

                        vacaciones = xlwt.easyxf('font: name Times New Roman, colour red')
                        vacaciones.borders = borders

                        tit = TituloInstitucion.objects.all()[:1].get()

                        wb = xlwt.Workbook()
                        for x in personas_actividades:
                            ws = wb.add_sheet(str(Persona.objects.filter(usuario=x)[:1].get().usuario.username),
                                              cell_overwrite_ok=True)

                            ws.write_merge(0, 0, 0, m, tit.nombre, titulo2)
                            ws.write_merge(1, 1, 0, m, 'LISTADO DE ACTIVIDADES DE HORAS EXTRA', titulo2)
                            perfiles = ''
                            per = Persona.objects.filter(usuario=x)[:1].get().usuario.groups.values_list('name',
                                                                                                        flat=True)
                            lista= []
                            try:
                                fecha_desde_ = fecha_desde.strftime('%Y-%m-%d')
                                fecha_hasta_ = fecha_hasta.strftime('%Y-%m-%d')
                                personaid = Persona.objects.filter(usuario=x)[:1].get()

                                if ViewVacaciones.objects.filter(fechasalida__gte= fecha_desde_, fecharegreso__lte=fecha_hasta_, cedula= str(personaid.cedula)).exists():
                                    dato =ViewVacaciones.objects.filter(fechasalida__gte= fecha_desde_, fecharegreso__lte=fecha_hasta_, cedula= str(personaid.cedula))

                                    for fila in dato:
                                        fechasalida_dato = fila.fechasalida
                                        fecharegreso_dato = fila.fecharegreso
                                        lista.append({'fs': fechasalida_dato, 'fr': fecharegreso_dato})
                            except Exception as ex:
                                print(ex)
                                pass
                            #
                            for p in per:
                                if per.count() > 1:
                                    perfiles = perfiles + str(p) + ', '
                                else:
                                    perfiles = perfiles + str(p)
                            ws.write(3, 0, 'PERFILES: ', subtitulo)
                            ws.write(3, 1, perfiles)
                            ws.write(4, 0, 'NOMBRE COMPLETO:   ', subtitulo)
                            ws.write(4, 1, str(Persona.objects.filter(usuario=x)[:1].get()))

                            ws.write(5, 0, 'FECHA DESDE:   ', subtitulo)
                            ws.write(5, 1, fecha_desde.strftime('%Y-%m-%d'))
                            ws.write(6, 0, 'FECHA HASTA:   ', subtitulo)
                            ws.write(6, 1, fecha_hasta.strftime('%Y-%m-%d'))

                            ws.write_merge(8, 9, 0, 0, 'Actividad', subtitulo3)
                            ws.col(0).width = 10 * 700
                            ws.write_merge(8, 8, 1, 2, 'Inicio', subtitulo3)
                            ws.write(9, 1, 'Fecha', subtitulo3)
                            ws.write(9, 2, 'Hora', subtitulo3)
                            ws.write_merge(8, 8, 3, 4, 'Fin', subtitulo3)
                            ws.write(9, 3, 'Fecha', subtitulo3)
                            ws.write(9, 4, 'Hora', subtitulo3)
                            ws.write_merge(8, 9, 5, 5, 'Hora Laboradas', subtitulo3)
                            if lista:
                                ws.write_merge(8,9,6,6, 'Vacaciones', subtitulo3)
                                ws.col(6).width = 10 * 1300
                            fila = 10
                            hora_extra_total = timedelta(hours=0, minutes=0, seconds=0)
                            # actividades = actividades.filter(usuario__groups__in=supervisor.filter().values_list('grupo'),enviar_supervisor=True,enviar_director=False)
                            for act in actividades.filter(usuario=x):
                                ws.write(fila, 0, elimina_tildes(act.descripcion), celdas)
                                ws.write(fila, 1, str(act.fecha_inicio.strftime('%Y-%m-%d')), celdas)
                                ws.write(fila, 2, str(act.fecha_inicio.strftime('%H:%M:%S')), celdas)
                                ws.write(fila, 3, str(act.fecha_fin.strftime('%Y-%m-%d')), celdas)
                                ws.write(fila, 4, str(act.fecha_fin.strftime('%H:%M:%S')), celdas)

                                if lista:
                                    for item in lista :
                                        fecha_inicio =str(act.fecha_inicio.strftime('%Y-%m-%d'))
                                        fecha_fin =str(act.fecha_fin.strftime('%Y-%m-%d'))
                                        fecha_inicio_vacaciones =str(item['fs'].strftime('%Y-%m-%d'))
                                        fecha_fin_vacaciones =str(item['fr'].strftime('%Y-%m-%d'))
                                        if fecha_inicio >= fecha_inicio_vacaciones and fecha_fin  <= fecha_fin_vacaciones:
                                            mensaje = "Se encuentra en su periodo de vacaciones: " + fecha_inicio_vacaciones +" - "+ fecha_fin_vacaciones
                                            ws.write(fila,6, mensaje, vacaciones)
                                        else:
                                            ws.write(fila, 6, ' ', vacaciones)


                                if act.horas_extras:

                                    timedelta_resultante = timedelta(hours=int(act.horas_extras.split(':')[0]),
                                                                     minutes=int(act.horas_extras.split(':')[1]),
                                                                     seconds=int(act.horas_extras.split(':')[2]))
                                    ws.write(fila, 5, str(act.horas_extras), celdas)
                                    hora_extra_total += timedelta_resultante
                                else:
                                    ws.write(fila, 5, '', celdas)

                                fila = fila + 1

                            ws.write_merge(fila, fila, 0, 4, 'TOTAL', subtitulo3)
                            if hora_extra_total.days > 0:
                                ws.write(fila, 5, str(calcular_horas_timedelta(hora_extra_total)), subtitulo3)
                            else:
                                ws.write(fila, 5, str(hora_extra_total), subtitulo3)

                            fila = 3 + fila
                            ws.write(fila, 0, "Fecha Impresion", subtitulo)
                            ws.write(fila, 1, str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

                        nombre = 'xls_horasextras' + str(datetime.now()).replace(" ", "").replace(".", "").replace(":",
                                                                                                                   "") + '.xls'
                        wb.save(MEDIA_ROOT + '/reporteexcel/' + nombre)
                        # if personas_actividades:
                        return HttpResponse(json.dumps({"result": "ok", "url": "/media/reporteexcel/" + nombre}),
                                           content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({"result": "No se han encontrado Actividades "}),
                                           content_type="application/json")

                except Exception as ex:
                    print(ex)
                    return HttpResponse(json.dumps({"result": str(ex) + 'id: ' +str(act.id)}),content_type="application/json")

            elif action == 'enviar_aprobaciones':
                data = {}
                try:
                    supervisor = SupervisorGrupos.objects.filter(
                        supervisor=Persona.objects.filter(id=int(request.POST['supervisor']))[:1].get())[:1].get()

                    actividades_super = None
                    datos_post = request.POST['data'].split(',')
                    desde = datetime.strptime(datos_post[0], '%Y-%m-%d')
                    hasta = datetime.strptime(datos_post[1], '%Y-%m-%d %H:%M:%S')
                    if request.POST['aprueba'] == 'supervisor':
                        actividades_super = ActividadesHorasExtra.objects.filter(
                            usuario=Persona.objects.filter(id=int(request.POST['persona']))[:1].get().usuario,
                            rechazado=False, enviar_supervisor=False,
                            fecha_inicio__gte=desde,
                            fecha_fin__lte=hasta,
                            usuario__groups__in=supervisor.grupo.all()).order_by('usuario', 'fecha_inicio')
                    elif request.POST['aprueba'] == 'director':
                        actividades_super = ActividadesHorasExtra.objects.filter(
                            usuario=Persona.objects.filter(id=int(request.POST['persona']))[:1].get().usuario,
                            rechazado=False, aprobado_supervisor=True, enviar_supervisor=True, enviar_director=False,
                            fecha_inicio__gte=desde,
                            fecha_fin__lte=hasta,
                            usuario__groups__in=supervisor.grupo.all()).order_by('usuario', 'fecha_inicio')
                    elif request.POST['aprueba'] == 'talento':
                        actividades_super = ActividadesHorasExtra.objects.filter(
                            usuario=Persona.objects.filter(id=int(request.POST['persona']))[:1].get().usuario,
                            rechazado=False, aprobado_supervisor=True, aprobado_director=True,
                            enviar_director=True, enviar_supervisor=True, enviar_talento=False,
                            fecha_inicio__gte=desde,
                            fecha_fin__lte=hasta,
                            usuario__groups__in=supervisor.grupo.all()).order_by('usuario', 'fecha_inicio')
                    elif request.POST['aprueba'] == 'auditoria':
                        actividades_super = ActividadesHorasExtra.objects.filter(
                            usuario=Persona.objects.filter(id=int(request.POST['persona']))[:1].get().usuario,
                            rechazado=False, aprobado_supervisor=True, aprobado_director=True,
                            enviar_director=True, enviar_supervisor=True, enviar_talento=True, aprobado_talento=True,
                            fecha_inicio__gte=desde,
                            fecha_fin__lte=hasta,
                            usuario__groups__in=supervisor.grupo.all()).order_by('usuario', 'fecha_inicio')

                    for a in actividades_super:
                        if request.POST['aprueba'] == 'supervisor':
                            if a.aprobado_supervisor:
                                a.enviar_supervisor = True
                                a.rechazado = False
                            else:
                                a.enviar_supervisor = False
                                a.usuario_rechaza = request.user
                                a.departamento_rechaza = 'Supervisor'
                                a.rechazado = True
                        elif request.POST['aprueba'] == 'director':
                            if a.aprobado_director:
                                a.enviar_director = True
                                a.rechazado = False
                            else:
                                a.enviar_director = False
                                a.usuario_rechaza = request.user
                                a.departamento_rechaza = 'Director'
                                a.rechazado = True
                        elif request.POST['aprueba'] == 'talento':
                            if a.aprobado_talento:
                                a.enviar_talento = True
                                a.rechazado = False
                            else:
                                a.enviar_talento = False
                                a.usuario_rechaza = request.user
                                a.departamento_rechaza = 'Talento Humano'
                                a.rechazado = True
                        elif request.POST['aprueba'] == 'auditoria':
                            if a.aprobado_talento:
                                a.enviar_auditoria = True
                                a.rechazado = False
                                a.fecha_aprobado_auditoria = datetime.now()
                            else:
                                a.enviar_auditoria = False
                                a.usuario_rechaza = request.user
                                a.departamento_rechaza = 'Auditoria'
                                a.rechazado = True

                        a.save()

                    data['result'] = 'ok'
                    # client_address = ip_client_address(request)
                    # LogEntry.objects.log_action(
                    #         user_id         = request.user.pk,
                    #         content_type_id = ContentType.objects.get_for_model(actividad).pk,
                    #         object_id       = actividad.id,
                    #         object_repr     = force_str(actividad),
                    #         action_flag     = CHANGE,
                    #         change_message  = 'Finalizar Actividad de Horas Extras (' + client_address + ')')
                    return HttpResponse(json.dumps(data),content_type="application/json")
                except Exception as ex:
                    print(ex)
                    return HttpResponse(json.dumps(data),content_type="application/json")
            elif action == 'aprobar_actividad':
                data = {}
                try:


                    actividad = ActividadesHorasExtra.objects.get(id=int(request.POST['id']))
                    if request.POST['aprobacion_tipo'] == 'supervisor':
                        if request.POST['estado'] == 'True':
                            actividad.aprobado_supervisor = False
                            actividad.observacion = str(request.POST['observacion'])

                            actividad.rechazado = True
                            actividad.usuario_rechaza = request.user
                            actividad.departamento_rechaza = 'Supervisor'
                        else:
                            actividad.aprobado_supervisor = True

                            actividad.rechazado = False
                            actividad.usuario_rechaza = None
                            actividad.departamento_rechaza = ''

                    elif request.POST['aprobacion_tipo'] == 'director':
                        if request.POST['estado'] == 'True':
                            actividad.aprobado_director = False
                            actividad.observacion = str(request.POST['observacion'])

                            actividad.rechazado = True
                            actividad.usuario_rechaza = request.user
                            actividad.departamento_rechaza = 'Director'
                        else:
                            actividad.aprobado_director = True

                            actividad.rechazado = False
                            actividad.usuario_rechaza = None
                            actividad.departamento_rechaza = ''

                    elif request.POST['aprobacion_tipo'] == 'talento':
                        if request.POST['estado'] == 'True':
                            actividad.aprobado_talento = False
                            actividad.observacion = str(request.POST['observacion'])

                            actividad.rechazado = True
                            actividad.usuario_rechaza = request.user
                            actividad.departamento_rechaza = 'Talento Humano'
                        else:
                            actividad.aprobado_talento = True

                            actividad.rechazado = False
                            actividad.usuario_rechaza = None
                            actividad.departamento_rechaza = ''

                    elif request.POST['aprobacion_tipo'] == 'auditoria':
                        if request.POST['estado'] == 'True':
                            actividad.aprobado_auditoria = False
                            actividad.observacion = str(request.POST['observacion'])

                            actividad.rechazado = True
                            actividad.usuario_rechaza = request.user
                            actividad.departamento_rechaza = 'Auditoria'
                        else:
                            actividad.aprobado_auditoria = True

                            actividad.rechazado = False
                            actividad.usuario_rechaza = None
                            actividad.departamento_rechaza = ''

                    actividad.save()

                    data['result'] = 'ok'
                    # client_address = ip_client_address(request)
                    # LogEntry.objects.log_action(
                    #         user_id         = request.user.pk,
                    #         content_type_id = ContentType.objects.get_for_model(actividad).pk,
                    #         object_id       = actividad.id,
                    #         object_repr     = force_str(actividad),
                    #         action_flag     = CHANGE,
                    #         change_message  = 'Finalizar Actividad de Horas Extras (' + client_address + ')')
                    return HttpResponse(json.dumps(data),content_type="application/json")
                except Exception as ex:
                    print(ex)
                    return HttpResponse(json.dumps(data),content_type="application/json")



        else:
            # fechadesde = datetime.strptime('2023-12-22', "%Y-%m-%d")
            # fechahasta = datetime.strptime('2024-01-21', "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            #
            #
            # for acti in ActividadesHorasExtra.objects.filter(fecha_inicio__gte=fechadesde,fecha_fin__lte=fechahasta):
            #     acti.enviar_supervisor = False
            #     acti.save()
            data = {'title': ' Actividades Horas Extras'}
            addUserData(request, data)
            if 'action' in request.GET:
                action = request.GET['action']
            else:
                hoy = datetime.now()
                search = None
                data['meses'] = MONTH_CHOICES

                if request.user.has_perm('sga.delete_actividadeshorasextra') \
                    or SupervisorGrupos.objects.filter(Q(director__usuario=request.user) |
                                Q(supervisor__usuario=request.user)).exists() \
                    or request.user.has_perm('sga.change_actividadeshorasextra'):
                    data['noadmin'] = True if 'noadmin' in request.GET else False

                    if not 'admin' in request.GET and not 'noadmin' in request.GET:
                        return render(request ,"actividades_horasextra/tipo_acceso.html" ,  data)
                    if 'admin' in request.GET:

                        data['hoy'] = hoy

                        if 'mescorte' in request.GET or 'anio' in request.GET:
                            if RolPago.objects.filter(fin__year=int(request.GET['anio']), fin__month=int(request.GET['mescorte'])).exists():
                                rol = RolPago.objects.filter(fin__year = int(request.GET['anio']), fin__month = int(request.GET['mescorte']) )[:1].get()
                                meshasta = int(request.GET['mescorte'])
                                desde = rol.inicio
                                hasta = datetime.combine(rol.fin, time(23, 59, 59))
                                fechamax = rol.fechamax
                            else:
                                meshasta = int(request.GET['mescorte'])

                                if int(request.GET['mescorte']) != 1:
                                    desde = datetime(int(request.GET['anio']), int(request.GET['mescorte']) - 1, 22).date()
                                else:
                                    desde = datetime(int(request.GET['anio']) - 1, 12, 22).date()
                                hasta = datetime(int(request.GET['anio']), int(request.GET['mescorte']), 21,23,59,59)
                                fechamax = datetime(int(request.GET['anio']), meshasta, 26).date()

                        else:
                            if RolPago.objects.filter(fin__year=hoy.year, fin__month=hoy.month).exists() and hoy.date().day < 21:
                                rol = RolPago.objects.filter(fin__year = hoy.year, fin__month =hoy.month )[:1].get()
                                meshasta = rol.fin.month
                                desde = rol.inicio
                                hasta = datetime.combine(rol.fin, time(23, 59, 59))
                                fechamax = rol.fechamax
                            else:
                                # ultimopago = RolPago.objects.filter().order_by('-id')[:1].get().fin
                                # rol = RolPago.objects.filter(fin__year=ultimopago.year, fin__month=ultimopago.month)[:1].get()
                                if hoy.date().day > 21:
                                    desde = datetime(hoy.date().year, hoy.month, 22).date()
                                    if hoy.month != 12:
                                        hasta = datetime(hoy.date().year, hoy.month + 1, 21,23,59,59)
                                    else:
                                        hasta = datetime(hoy.date().year + 1, (hoy + timedelta(weeks=1)).month,
                                                         21,23,59,59)

                                else:
                                    if hoy.month == 1:
                                        desde = datetime(hoy.date().year - 1, 12, 22).date()
                                    else:
                                        desde = datetime(hoy.date().year, hoy.month - 1, 22).date()
                                    # desde = datetime(hoy.date().year, hoy.month - 1, 22).date()
                                    hasta = datetime(hoy.date().year, hoy.month, 21,23,59,59)

                                fechamax = datetime(hasta.year, hoy.month, 26).date()
                                meshasta = hasta.month




                        data['data'] = str(desde) + ',' + str(hasta)
                        data['mes'] = meshasta
                        data['anio'] = str(hasta.year)

                        if 'rechazadas' in request.GET:
                            data['rechazadas'] = True
                            actividades = ActividadesHorasExtra.objects.filter(rechazado=True,
                                                                               fecha_inicio__gte=desde,
                                                                               fecha_fin__lte=hasta) \
                                .exclude(usuario_rechaza=request.user)
                        else:
                            actividades = ActividadesHorasExtra.objects.filter(Q(rechazado=False,
                                                                                 fecha_inicio__gte=desde,
                                                                                 fecha_fin__lte=hasta) |
                                                                               Q(rechazado=True,
                                                                                 usuario_rechaza=request.user,
                                                                                 fecha_inicio__gte=desde,
                                                                                 fecha_fin__lte=hasta))

                        if 's' in request.GET:
                            search = request.GET['s']
                            actividades = actividades.filter(Q(descripcion__icontains=search) | Q(
                                usuario__persona__nombres__icontains=search)).order_by('-id')

                        #director
                        if SupervisorGrupos.objects.filter(director__usuario=request.user).exists():
                            actividades_director = actividades

                            data['director'] = True
                            data['data'] = data['data'] + "," + "director"
                            if 'rechazadas' in request.GET:
                                actividades = actividades.filter(enviar_director=True)
                            else:
                                 if 'enviadas' in request.GET:
                                    data['enviadas'] = True
                                    actividades = actividades.filter(enviar_supervisor=True,
                                                                 enviar_director=True)
                                 else:
                                    actividades_director = actividades.filter(enviar_supervisor=True,
                                                                 enviar_director=True)
                                    actividades = actividades.filter(enviar_supervisor=True,
                                                                     enviar_director=False)


                            data['supervisores'] = SupervisorGrupos.objects.filter(director__usuario=request.user,
                                                                                   grupo__in=actividades.values(
                                                                                       'usuario__groups').distinct(
                                                                                       'usuario__groups')).distinct(
                                'jefe')

                            lista_supervisor_actividades = []
                            for supervisor in data['supervisores']:
                                actividades_supervisor = actividades.filter(
                                    usuario__groups__in=supervisor.grupo.all()).order_by('usuario', 'fecha_inicio')

                                personas = actividades_supervisor.filter(
                                    usuario__groups__in=supervisor.grupo.all()).order_by('usuario').distinct(
                                    'usuario').values_list('usuario', flat=True)
                                lista_personas = []
                                for p in personas:
                                    hora_extra_total = timedelta(hours=0, minutes=0, seconds=0)
                                    for actvh in actividades_supervisor.filter(usuario__id=p,
                                                                               horas_extras__isnull=False,
                                                                               aprobado_director=True):
                                        # tiempo = datetime.strptime(actvh.horas_extras, "%H:%M:%S").time()
                                        timedelta_resultante = timedelta(hours=int(actvh.horas_extras.split(':')[0]),
                                                                         minutes=int(actvh.horas_extras.split(':')[1]),
                                                                         seconds=int(actvh.horas_extras.split(':')[2]))
                                        hora_extra_total += timedelta_resultante

                                    personas_actividades = {'personas': Persona.objects.get(usuario__id=p),
                                                            'actividades': list(
                                                                actividades_supervisor.filter(usuario__id=p)),
                                                            'hora_extra_total': str(calcular_horas_timedelta(
                                                                hora_extra_total)) if hora_extra_total.days > 0 else str(
                                                                hora_extra_total),
                                                            'actividades_aprobadas': actividades_supervisor.filter(
                                                                usuario__id=p, aprobado_director=True).count(),
                                                            'actividades_reprobadas': actividades_supervisor.filter(
                                                                usuario__id=p, aprobado_director=False).count(),
                                                            'no_aprobado_auditoria': True if (actividades_director.filter(usuario__id=p, enviar_talento = True).count() > 0 or fechamax <= datetime.date(datetime.now())) else False }
                                    lista_personas.append(personas_actividades)
                                supervisor_actividades = {'supervisor': supervisor,
                                                          'personas': lista_personas}
                                lista_supervisor_actividades.append(supervisor_actividades)
                            data['supervisor_actividades'] = lista_supervisor_actividades
                        elif SupervisorGrupos.objects.filter(supervisor__usuario=request.user).exists():

                            if 'rechazadas' in request.GET:
                                actividades = actividades.filter(Q(enviar_supervisor=True))
                            else:
                                if 'enviadas' in request.GET:
                                    data['enviadas'] = True
                                    actividades = actividades.filter(enviar_supervisor=True)
                                else:
                                    actividades = actividades.filter(enviar_supervisor=False)


                            data['data'] = data['data'] + "," + "supervisor"
                            data['supervisor'] = True
                            data['supervisores'] = SupervisorGrupos.objects.filter(supervisor__usuario=request.user,
                                                                                   grupo__in=actividades.filter().values(
                                                                                       'usuario__groups').distinct(
                                                                                       'usuario__groups')).distinct(
                                'supervisor')

                            lista_supervisor_actividades = []

                            for supervisor in data['supervisores']:
                                lista_personas = []
                                actividades_supervisor = actividades.filter(
                                    usuario__groups__in=supervisor.grupo.all()).order_by('usuario', 'fecha_inicio')
                                personas = actividades_supervisor.filter(
                                    usuario__groups__in=supervisor.grupo.all()).order_by('usuario').distinct(
                                    'usuario').values_list('usuario', flat=True)
                                for p in personas:
                                    hora_extra_total = timedelta(hours=0, minutes=0, seconds=0)
                                    for actvh in actividades_supervisor.filter(usuario__id=p,
                                                                               horas_extras__isnull=False,
                                                                               aprobado_supervisor=True):
                                        # tiempo = datetime.strptime(actvh.horas_extras, "%H:%M:%S").time()
                                        timedelta_resultante = timedelta(hours=int(actvh.horas_extras.split(':')[0]),
                                                                         minutes=int(actvh.horas_extras.split(':')[1]),
                                                                         seconds=int(actvh.horas_extras.split(':')[2]))
                                        hora_extra_total += timedelta_resultante

                                    personas_actividades = {'personas': Persona.objects.get(usuario__id=p),
                                                            'actividades': list(
                                                                actividades_supervisor.filter(usuario__id=p)),
                                                            'hora_extra_total': str(calcular_horas_timedelta(
                                                                hora_extra_total)) if hora_extra_total.days > 0 else str(
                                                                hora_extra_total),
                                                            'actividades_aprobadas': actividades_supervisor.filter(
                                                                usuario__id=p, aprobado_supervisor=True).count(),
                                                            'actividades_reprobadas': actividades_supervisor.filter(
                                                                usuario__id=p, aprobado_supervisor=False).count()}
                                    lista_personas.append(personas_actividades)

                                supervisor_actividades = {'supervisor': supervisor, 'personas': lista_personas}
                                lista_supervisor_actividades.append(supervisor_actividades)
                            data['supervisor_actividades'] = lista_supervisor_actividades


                        elif request.user.has_perm('sga.change_actividadeshorasextra'):
                            if 'rechazadas' in request.GET:
                                actividades = actividades.filter(enviar_talento = True)

                            else:
                                if 'enviadas' in request.GET:
                                    data['enviadas'] = True
                                    actividades = actividades.filter(enviar_director = True,
                                                                     enviar_talento = True )
                                else:
                                    actividades = actividades.filter(enviar_director = True,
                                                                     enviar_talento = False )
                            # hoy = datetime.today()
                            #
                            # roles = RolPago.objects.filter(fechamax__year = hoy.year, fechamax__month =hoy.month )

                            lista_supervisor_actividades = []

                            # if roles:
                            #     rol = RolPago.objects.filter(fechamax__year = hoy.year, fechamax__month =hoy.month )[:1].get()
                            #     if rol.fechamaxvin <= datetime.date(datetime.now()):
                            data['data'] = data['data'] + "," + "talento"
                            data['talento'] = True
                            data['supervisores'] = SupervisorGrupos.objects.filter(
                                grupo__in=actividades.filter().values('usuario__groups').distinct(
                                    'usuario__groups')).distinct('supervisor')

                            for supervisor in data['supervisores']:
                                lista_personas = []
                                actividades_supervisor = actividades.filter(
                                    usuario__groups__in=supervisor.grupo.all()).order_by('usuario', 'fecha_inicio')
                                personas = actividades_supervisor.filter(
                                    usuario__groups__in=supervisor.grupo.all()).order_by('usuario').distinct(
                                    'usuario').values_list('usuario', flat=True)
                                for p in personas:
                                    hora_extra_total = timedelta(hours=0, minutes=0, seconds=0)
                                    for actvh in actividades_supervisor.filter(usuario__id=p,
                                                                               horas_extras__isnull=False,
                                                                               aprobado_talento=True):
                                        # tiempo = datetime.strptime(actvh.horas_extras, "%H:%M:%S").time()
                                        timedelta_resultante = timedelta(hours=int(actvh.horas_extras.split(':')[0]),
                                                                         minutes=int(actvh.horas_extras.split(':')[1]),
                                                                         seconds=int(actvh.horas_extras.split(':')[2]))
                                        hora_extra_total += timedelta_resultante

                                    personas_actividades = {'personas': Persona.objects.get(usuario__id=p),
                                                            'actividades': list(
                                                                actividades_supervisor.filter(usuario__id=p)),
                                                            'hora_extra_total': str(calcular_horas_timedelta(
                                                                hora_extra_total)) if hora_extra_total.days > 0 else str(
                                                                hora_extra_total),
                                                            'actividades_aprobadas': actividades_supervisor.filter(
                                                                usuario__id=p, aprobado_talento=True).count(),
                                                            'actividades_reprobadas': actividades_supervisor.filter(
                                                                usuario__id=p, aprobado_talento=False).count()}
                                    lista_personas.append(personas_actividades)
                                supervisor_actividades = {'supervisor': supervisor, 'personas': lista_personas}
                                lista_supervisor_actividades.append(supervisor_actividades)

                            data['supervisor_actividades'] = lista_supervisor_actividades
                        elif request.user.has_perm('sga.delete_actividadeshorasextra'):
                            if 'rechazadas' in request.GET:
                                actividades = actividades.filter(aprobado_auditoria = True)
                                #
                                # actividades = actividades.filter(aprobado_supervisor=True,
                                #                                  enviar_supervisor=True,
                                #                                  aprobado_director=True,
                                #                                  enviar_talento=True,
                                #                                  enviar_director=True)

                            else:
                                if 'enviadas' in request.GET:
                                    data['enviadas'] = True
                                    actividades = actividades.filter(enviar_talento = True, enviar_auditoria = True )
                                else:
                                    actividades = actividades.filter(enviar_talento = True, enviar_auditoria = False)
                            # hoy = datetime.today()

                            # roles = RolPago.objects.filter(fechamax__year = hoy.year, fechamax__month =hoy.month )

                            lista_supervisor_actividades = []

                            # if roles:
                            #     rol = RolPago.objects.filter(fechamax__year = hoy.year, fechamax__month =hoy.month )[:1].get()
                            #     if rol.fechamaxvin <= datetime.date(datetime.now()):
                            data['data'] = data['data'] + "," + "auditor"
                            data['auditor'] = True
                            data['supervisores'] = SupervisorGrupos.objects.filter(
                                grupo__in=actividades.filter(aprobado_supervisor=True,
                                                             enviar_supervisor=True,
                                                             aprobado_director=True,
                                                             enviar_director=True,
                                                             aprobado_talento=True,
                                                             enviar_talento=True,
                                                             enviar_auditoria=False).values('usuario__groups').distinct(
                                    'usuario__groups')).distinct('supervisor')
                            actividades = actividades.filter(aprobado_supervisor=True, enviar_supervisor=True,
                                                             aprobado_director=True, enviar_director=True,
                                                             aprobado_talento=True, enviar_talento=True,
                                                             enviar_auditoria=False)
                            for supervisor in data['supervisores']:
                                lista_personas = []
                                actividades_supervisor = actividades.filter(
                                    usuario__groups__in=supervisor.grupo.all()).order_by('usuario', 'fecha_inicio')
                                personas = actividades_supervisor.filter(
                                    usuario__groups__in=supervisor.grupo.all()).order_by('usuario').distinct(
                                    'usuario').values_list('usuario', flat=True)
                                for p in personas:
                                    hora_extra_total = timedelta(hours=0, minutes=0, seconds=0)
                                    for actvh in actividades_supervisor.filter(usuario__id=p,
                                                                               horas_extras__isnull=False,
                                                                               aprobado_auditoria=True):
                                        # tiempo = datetime.strptime(actvh.horas_extras, "%H:%M:%S").time()
                                        timedelta_resultante = timedelta(hours=int(actvh.horas_extras.split(':')[0]),
                                                                         minutes=int(actvh.horas_extras.split(':')[1]),
                                                                         seconds=int(actvh.horas_extras.split(':')[2]))
                                        hora_extra_total += timedelta_resultante

                                    personas_actividades = {'personas': Persona.objects.get(usuario__id=p),
                                                            'actividades': list(
                                                                actividades_supervisor.filter(usuario__id=p)),
                                                            'hora_extra_total': str(calcular_horas_timedelta(
                                                                hora_extra_total)) if hora_extra_total.days > 0 else str(
                                                                hora_extra_total),
                                                            'actividades_aprobadas': actividades_supervisor.filter(
                                                                usuario__id=p, aprobado_auditoria=True).count(),
                                                            'actividades_reprobadas': actividades_supervisor.filter(
                                                                usuario__id=p, aprobado_auditoria=False).count()}
                                    lista_personas.append(personas_actividades)
                                supervisor_actividades = {'supervisor': supervisor, 'personas': lista_personas}
                                lista_supervisor_actividades.append(supervisor_actividades)

                            data['supervisor_actividades'] = lista_supervisor_actividades

                        data['search'] = search if search else ""

                        return render(request ,"actividades_horasextra/actividades_adm.html" ,  data)

                if 's' in request.GET:
                    search = request.GET['s']
                    actividades = ActividadesHorasExtra.objects.filter(usuario=request.user,
                                                                       descripcion__icontains=search).order_by('-id')

                else:
                    actividades = ActividadesHorasExtra.objects.filter(usuario=request.user).order_by('-id')

                if 'rechazado' in request.GET:
                    data['rechazado'] = True
                    actividades = actividades.filter(rechazado=True)
                else:
                    actividades = actividades.filter(rechazado=False)

                if 'mes' in request.GET or 'anio' in request.GET:
                    if RolPago.objects.filter(fin__year=int(request.GET['anio']), fin__month=int(request.GET['mes'])).exists():
                        rol = RolPago.objects.filter(fin__year=int(request.GET['anio']), fin__month=int(request.GET['mes']))[:1].get()
                        desde = rol.inicio
                        hasta = datetime.combine(rol.fin, time(23, 59, 59))
                    else:
                        if int(request.GET['mes']) != 1:
                            desde = datetime(int(request.GET['anio']), int(request.GET['mes']) - 1 , 22).date()
                        else:
                            desde = datetime(int(request.GET['anio']) - 1,  12, 22).date()
                        hasta = datetime(int(request.GET['anio']), int(request.GET['mes']), 21,23,59,59)
                else:

                    if RolPago.objects.filter(fin__year=hoy.year, fin__month=hoy.month).exists() and hoy.date().day < 21:
                        rol = RolPago.objects.filter(fin__year=hoy.year, fin__month=hoy.month)[:1].get()
                        desde = rol.inicio
                        hasta = datetime.combine(rol.fin, time(23, 59, 59))
                    else:
                        if hoy.date().day > 21:
                            desde = datetime(hoy.date().year, hoy.month , 22).date()
                            if hoy.month != 12:
                                hasta = datetime(hoy.date().year, hoy.month+1  , 21,23,59,59)
                            else:
                                hasta = datetime(hoy.date().year + 1, (hoy + timedelta(weeks=1)).month   , 21,23,59,59)

                        else:
                            if hoy.month == 1:
                                desde = datetime(hoy.date().year - 1, 12, 22).date()
                            else:
                                desde = datetime(hoy.date().year, hoy.month - 1, 22).date()
                            # desde = datetime(hoy.date().year, hoy.month - 1, 22).date()
                            hasta = datetime(hoy.date().year, hoy.month, 21,23,59,59)

                data['mes'] = hasta.month
                data['anio'] = str(hasta.year)
                print(hasta)
                actividades = actividades.filter(fecha_inicio__gte=desde, fecha_fin__lte=hasta)
                hora_extra_total = timedelta(hours=0, minutes=0, seconds=0)
                for actvh in actividades.filter():
                    print(actvh)
                    timedelta_resultante = timedelta(hours=int(actvh.horas_extras.split(':')[0]),
                                                     minutes=int(actvh.horas_extras.split(':')[1]),
                                                     seconds=int(actvh.horas_extras.split(':')[2]))
                    hora_extra_total += timedelta_resultante

                data['hora_extra_total'] = str(calcular_horas_timedelta(hora_extra_total)) if hora_extra_total.days > 0 else str(hora_extra_total)

                paging = Paginator(actividades, 50)
                p = 1
                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                    page = paging.page(p)
                except:
                    page = paging.page(1)

                data['paging'] = paging
                data['page'] = page
                data['search'] = search if search else ""
                data['actividades'] = page.object_list
                data['ultimaactividad'] = ActividadesHorasExtra.objects.filter(usuario=request.user).order_by('-id')[:1].get() if ActividadesHorasExtra.objects.filter(usuario=request.user) else None

                return render(request ,"actividades_horasextra/actividades.html" ,  data)
    except Exception as ex:
        print(ex)


