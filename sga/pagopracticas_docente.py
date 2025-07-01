from datetime import datetime
from itertools import chain
import json
from django.contrib.admin.models import LogEntry, ADDITION, DELETION, CHANGE
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
from decorators import secure_module
from settings import ASIG_PRATICA, HORAS_PRACTICA, COORDINACION_UACED
from sga.commonviews import addUserData, ip_client_address
from sga.forms import PagoPracticasForm, InscripcionPracticaForm, InscripcionPracticasForm, InscripcionPracticasDistribucionForm, PracticasDistribucionHorasForm, AsignarMateriaGrupoForm, NivelPagoPPPForm, ProyeccionForm
from sga.gruposcurso import convert_fecha
from sga.models import PagoPracticasDocente, Profesor, InscripcionPracticas, Asignatura, HistoricoRecordAcademico, RecordAcademico, Inscripcion, Matricula, AsignaturaMalla, NivelMalla, NivelPracticaInduccion, Nivel, Periodo, Coordinacion, NivelPagoPracticasDocente, RubroCuota, RolPago


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
@transaction.atomic()

def view(request):
    if request.method=='POST':
        action = request.POST['action']

        if action == 'add':
            try:
                print(request.POST)
                print(request.FILES)
                f = PagoPracticasForm(request.POST, request.FILES)
                if PagoPracticasDocente.objects.filter(pk=request.POST['idpago']).exists():
                    pago = PagoPracticasDocente.objects.get(pk=request.POST['idpago'])
                    pago.descripcion=request.POST['descripcion']
                    pago.inicio=convert_fecha(request.POST['inicio'])
                    pago.fin=convert_fecha(request.POST['fin'])
                    if 'valor' in request.POST:
                        pago.valor=request.POST['valor']
                    if 'archivo' in request.FILES:
                        pago.archivo = request.FILES['archivo']
                    pago.save()
                else:
                    profesor = Profesor.objects.get(pk=request.POST['profesor'])
                    # if PagoPracticasDocente.objects.filter(Q(inicio__gt=convert_fecha(request.POST['inicio']), fin__gte=convert_fecha(request.POST['fin']))|Q (inicio__lte=convert_fecha(request.POST['inicio']), fin__gte=convert_fecha(request.POST['fin']))|Q (inicio__lte=convert_fecha(request.POST['inicio']), fin__lt=convert_fecha(request.POST['fin'])),profesor=profesor).exists():
                    if PagoPracticasDocente.objects.filter(Q(inicio__lte=convert_fecha(request.POST['inicio']), fin__gte=convert_fecha(request.POST['fin'])),profesor=profesor).exists():
                        return HttpResponseRedirect('/pagopracticas_docente?error=El docente: '+str(profesor)+' ya se encuentra registrado en el rango de fechas seleccionado')
                    else:
                        pago = PagoPracticasDocente(descripcion=request.POST['descripcion'],
                                                    profesor=profesor,
                                                    inicio=convert_fecha(request.POST['inicio']),
                                                    fin=convert_fecha(request.POST['fin']),
                                                    pagoaprobado=False)
                        pago.save()

                        if 'archivo' in request.FILES:
                            pago.archivo=request.FILES['archivo']
                        if request.POST['valor'] != '':
                            pago.valor = request.POST['valor']
                        pago.save()

                        mensaje = 'Ingreso de pago Practicas Pre-Profesionales al docente: '+str(profesor)
                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(profesor).pk,
                        object_id       = profesor.id,
                        object_repr     = force_str(profesor),
                        action_flag     = CHANGE,
                        change_message  = mensaje+' (' + client_address + ')' )

                return HttpResponseRedirect('/pagopracticas_docente')
            except Exception as ex:
                print("ERROR: "+str(ex))
                return HttpResponseRedirect('/pagopracticas_docente?error='+str(ex))

        elif action == 'eliminar':
            try:
                pago = PagoPracticasDocente.objects.get(pk=request.POST['id'])
                if not pago.rol==True:
                    pago.delete()
                else:
                    return HttpResponse(json.dumps({"result":"bad", "mensaje":"Pago de Practicas del docente se encuentra actualizado al rol actual"}),content_type="application/json")
                mensaje = 'Elimacion de pago Practicas Pre-Profesionales del docente: '+str(pago.profesor)

                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                user_id         = request.user.pk,
                content_type_id = ContentType.objects.get_for_model(pago).pk,
                object_id       = pago.id,
                object_repr     = force_str(pago),
                action_flag     = DELETION,
                change_message  = mensaje+' (' + client_address + ')' )

                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            except Exception as ex:
                print(ex)
                return HttpResponse(json.dumps({"result":"bad", "mensaje":"Error: "+str(ex)}),content_type="application/json")

        elif action == 'aprobar_pago':
            try:
                pago = PagoPracticasDocente.objects.get(pk=request.POST['id'])
                if pago.num_practicas()==0:
                    return HttpResponse(json.dumps({"result":"bad", "mensaje":"Docente no cuenta con practicas asignadas en el rango de fechas seleccionado"}),content_type="application/json")
                elif pago.valor==0:
                    return HttpResponse(json.dumps({"result":"bad", "mensaje":"Debe ingresar pago del docente"}),content_type="application/json")
                elif not pago.archivo:
                    return HttpResponse(json.dumps({"result":"bad", "mensaje":"Falta subir el informe general por parte del docente"}),content_type="application/json")
                else:
                    pago.pagoaprobado = not pago.pagoaprobado
                    pago.fechaaprobacion = datetime.now()
                    if pago.pagoaprobado:
                        pago.habilitar = False
                        mensaje = 'Pago del docente: '+str(pago.profesor)+' ha sido aprobado'
                    else:
                        pago.habilitar = True
                        mensaje = 'Pago del docente: '+str(pago.profesor)+' ha sido desaprobado'
                    pago.save()
                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                user_id         = request.user.pk,
                content_type_id = ContentType.objects.get_for_model(pago).pk,
                object_id       = pago.id,
                object_repr     = force_str(pago),
                action_flag     = CHANGE,
                change_message  = mensaje+' (' + client_address + ')' )

                rol = RolPago.objects.filter().order_by('-id')[:1].get()
                if pago.pagoaprobado:
                    if pago.fechaaprobacion.date() >= rol.inicio and pago.fechaaprobacion.date() <= rol.fin:
                        msj = 'Pago aprobado, el cual sera cancelado en el rol vigente: '+str(rol.nombre)+' ('+str(rol.inicio)+' al '+str(rol.fin)+')'
                    else:
                        msj = 'Pago aprobado, (No entrara dentro del rol vigente)'
                else:
                    msj = 'Pago desaprobado'

                return HttpResponse(json.dumps({"result":"ok", "mensaje":msj}),content_type="application/json")
            except Exception as ex:
                print(ex)
                return HttpResponse(json.dumps({"result":"bad", "mensaje":"Error: "+str(ex)}),content_type="application/json")

        elif action == 'eliminar_practica':
            try:
                practica = InscripcionPracticas.objects.get(pk=request.POST['id'])
                inscripcion = practica.inscripcion
                practica.correo_practica(request.user,'SE HA ELIMINADO LA NOTA DE PRACTICAS PREPROFESIONALES')
                asig = Asignatura.objects.get(pk=ASIG_PRATICA)
                if HistoricoRecordAcademico.objects.filter(inscripcion=inscripcion, asignatura=asig).exists():
                    HistoricoRecordAcademico.objects.filter(inscripcion=inscripcion, asignatura=asig)[:1].get().delete()
                if RecordAcademico.objects.filter(inscripcion=inscripcion,asignatura=asig).exists():
                    RecordAcademico.objects.filter(inscripcion=inscripcion,asignatura=asig)[:1].get().delete()

                client_address = ip_client_address(request)
                # Log de ELIMINAR PRACTICAS OCastillo 17-08-2020
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(practica).pk,
                    object_id       = practica.id,
                    object_repr     = force_str(practica),
                    action_flag     = DELETION,
                    change_message  = 'Eliminada Nota de Practica (' + client_address + ')' )
                practica.delete()
                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            except Exception as ex:
                print(ex)
                return HttpResponse(json.dumps({"result":"bad", "mensaje":"Error: "+str(ex)}),content_type="application/json")

        elif action == 'comprobar_inscripcion':
            try:
                pago = PagoPracticasDocente.objects.get(pk=request.POST['pago'])
                inscripcion = Inscripcion.objects.get(pk=request.POST['inscripcion'])
                if inscripcion.malla_inscripcion().malla.nueva_malla:
                    nivelmalla = True
                else:
                    nivelmalla = False
                if InscripcionPracticas.objects.filter(inscripcion=inscripcion).exists():
                    horas_practicas = InscripcionPracticas.objects.filter(inscripcion=inscripcion).aggregate(Sum('horas'))
                    if horas_practicas['horas__sum'] >= HORAS_PRACTICA:
                        return HttpResponse(json.dumps({"result":"bad", "mensaje":"ALUMNO CUENTA CON "+str(horas_practicas['horas__sum'])+" HORAS PRACTICAS REGISTRADAS","usa_nivelmalla":nivelmalla}),content_type="application/json")
                niveles = []
                if Matricula.objects.filter(inscripcion=inscripcion).exists():
                    malla = inscripcion.ultima_matricula_pararetiro().nivel.malla
                    asignaturamalla = AsignaturaMalla.objects.filter(asignatura__nombre__icontains='PREPRO', malla=malla)
                    for n in asignaturamalla:
                        niveles.append(n.nivelmalla.id)
                return HttpResponse(json.dumps({"result":"ok", "niveles":niveles, "usa_nivelmalla":nivelmalla}),content_type="application/json")
            except Exception as ex:
                print(ex)
                return HttpResponse(json.dumps({"result":"bad", "mensaje":""}),content_type="application/json")

        elif action == 'comprobar_horas':
            try:
                print(request.POST)
                inscripcion = Inscripcion.objects.get(pk=request.POST['inscripcion'])
                horas = int(request.POST['horas'])
                horas_practicas = 0
                if InscripcionPracticas.objects.filter(inscripcion=inscripcion).exists():
                    horas_practicas = InscripcionPracticas.objects.filter(inscripcion=inscripcion).aggregate(Sum('horas'))
                    horas_practicas =  int(horas_practicas['horas__sum'])
                    if horas_practicas >= HORAS_PRACTICA:
                        return HttpResponse(json.dumps({"result":"bad", "mensaje":"ALUMNO "+str(inscripcion.persona.nombre_completo_inverso())+" CUENTA CON "+str(horas_practicas)+" HORAS PRACTICAS REGISTRADAS"}),content_type="application/json")
                if (horas + horas_practicas) > HORAS_PRACTICA:
                    return HttpResponse(json.dumps({"result":"bad", "mensaje":"HORAS INGRESADAS SUPERAN LAS 240"}),content_type="application/json")
                return HttpResponse(json.dumps({"result":"ok", "mensaje":str(horas_practicas)+" HORAS PRACTICAS REGISTRADAS"}),content_type="application/json")
            except Exception as ex:
                print(ex)
                return HttpResponse(json.dumps({"result":"bad", "mensaje":"Error: "+str(ex)}),content_type="application/json")

        if action == 'add_practica':
            try:
                print(request.POST)
                pago = PagoPracticasDocente.objects.get(pk=request.POST['pago'])
                inscripcion = Inscripcion.objects.get(pk=request.POST['inscripcion_id'])
                nivelmalla = NivelMalla.objects.get(pk=request.POST['nivelmalla'])
                f = InscripcionPracticasForm(request.POST, request.FILES)
                if f.is_valid():
                    practica = InscripcionPracticas(profesor=pago.profesor,
                                                 inscripcion=inscripcion,
                                                 horas=f.cleaned_data['horas'],
                                                 lugar=f.cleaned_data['lugar'],
                                                 inicio=f.cleaned_data['inicio'],
                                                 fin=f.cleaned_data['fin'],
                                                 observaciones=f.cleaned_data['observaciones'],
                                                 equipamiento=f.cleaned_data['equipamiento'],
                                                 nivelmalla=f.cleaned_data['nivelmalla'])
                    practica.save()

                    if 'archivo' in request.FILES:
                        practica.archivo = request.FILES['archivo']
                        practica.save()

                    practica.correo_practica(request.user,'SE HA AGREGO PRACTICAS PREPROFESIONALES')
                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de ADICIONAR DOCUMENTO
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(practica).pk,
                        object_id       = practica.id,
                        object_repr     = force_str(practica),
                        action_flag     = ADDITION,
                        change_message  = 'Adicionada Practica (' + client_address + ')' )

                    if not inscripcion.malla_inscripcion().malla.nueva_malla:
                        if ASIG_PRATICA > 0:
                            asig = Asignatura.objects.get(pk=ASIG_PRATICA)
                            if HistoricoRecordAcademico.objects.filter(inscripcion=inscripcion, asignatura=asig).exists():
                                historico = HistoricoRecordAcademico.objects.filter(inscripcion=inscripcion, asignatura=asig)[:1].get()
                                historico.asignatura=asig
                                historico.nota=100
                                historico.asistencia=100
                                historico.fecha=practica.fin
                                historico.aprobada=True
                                historico.convalidacion=False
                                historico.pendiente=False
                            else:
                                historico = HistoricoRecordAcademico(inscripcion=inscripcion,
                                                            asignatura=asig,
                                                            nota=100,
                                                            asistencia=100,
                                                            fecha=practica.fin,
                                                            aprobada=True,
                                                            convalidacion=False,
                                                            pendiente=False)
                            historico.save()

                            if RecordAcademico.objects.filter(inscripcion=inscripcion,asignatura=asig).exists():
                                record = RecordAcademico.objects.filter(inscripcion=inscripcion,asignatura=asig)[:1].get()
                                record.nota=100
                                record.asistencia=100
                                record.fecha=practica.fin
                                record.aprobada=True
                                record.convalidacion=False
                                record.pendiente=False
                            else:
                                record = RecordAcademico(inscripcion=inscripcion, asignatura=asig,
                                                    nota=100, asistencia=100,
                                                    fecha=practica.fin, aprobada=True,
                                                    convalidacion=False, pendiente=False)
                            record.save()
                            if practica.horas < HORAS_PRACTICA:
                                record.delete()
                                historico.delete()
                            else:
                                client_address = ip_client_address(request)
                                # Log de Aprobacion Vinculacion
                                LogEntry.objects.log_action(
                                     user_id         = request.user.pk,
                                     content_type_id = ContentType.objects.get_for_model(inscripcion).pk,
                                     object_id       = inscripcion.id,
                                     object_repr     = force_str(inscripcion),
                                     action_flag     = ADDITION,
                                     change_message  = 'Adicionada Nota de Practica (' + client_address + ')'  )
                        #     else:
                        #         practica.correo_practica(request.user,'SE HA AGREGADO LA NOTA DE  PRACTICAS PREPROFESIONALES')

                return HttpResponseRedirect("/pagopracticas_docente?action=ver_practicas&id="+str(pago.id))
            except Exception as ex:
                print("ERROR: "+str(ex))
                return HttpResponseRedirect('/pagopracticas_docente?action=ver_practicas&id='+str(pago.id)+'&error='+str(ex))

        elif action == 'habilitar_registros':
            try:
                print(request.POST)
                pago = PagoPracticasDocente.objects.get(pk=request.POST['id'])
                pago.habilitar = not pago.habilitar
                pago.save()
                if pago.habilitar:
                    mensaje = 'SE HA HABILITADO LOS REGISTROS DOCENTES EN EL RANGO DE FECHAS DEL '+str(pago.inicio)+' AL '+str(pago.fin)
                else:
                    mensaje = 'SE HA DESHABILITADO LOS REGISTROS DOCENTES EN EL RANGO DE FECHAS DEL '+str(pago.inicio)+' AL '+str(pago.fin)

                client_address = ip_client_address(request)
                # Log de Aprobacion Vinculacion
                LogEntry.objects.log_action(
                     user_id         = request.user.pk,
                     content_type_id = ContentType.objects.get_for_model(pago).pk,
                     object_id       = pago.id,
                     object_repr     = force_str(pago),
                     action_flag     = CHANGE,
                     change_message  = 'Adicionada Nota de Practica (' + client_address + ')'  )
                return HttpResponse(json.dumps({"result":"ok", "mensaje":mensaje}),content_type="application/json")
            except Exception as ex:
                print(ex)
                return HttpResponse(json.dumps({"result":"bad", "mensaje":"Error: "+str(ex)}),content_type="application/json")

        elif action == 'inscripciones_verificafecha':
            try:
                print(request.POST)
                profesor = Profesor.objects.get(pk=request.POST['profesor'])
                # if PagoPracticasDocente.objects.filter(profesor=profesor, inicio__lte=convert_fecha(request.POST['inicio']), inicio__gte=convert_fecha(request.POST['fin']),fin__gte=convert_fecha(request.POST['fin']), fin__lte=convert_fecha(request.POST['inicio'])).exists():
                if PagoPracticasDocente.objects.filter(profesor=profesor).exists():
                    print(1)
                    # if PagoPracticasDocente.objects.filter(inicio__lte=convert_fecha(request.POST['inicio']), inicio__lte=convert_fecha(request.POST['fin']),fin__gte=convert_fecha(request.POST['fin']), fin__gt=convert_fecha(request.POST['inicio'])).exists():
                    if PagoPracticasDocente.objects.filter(profesor=profesor, inicio__lte=convert_fecha(request.POST['inicio']),fin__gte=convert_fecha(request.POST['fin'])).exists():
                        pagos = PagoPracticasDocente.objects.filter(profesor=profesor, inicio__lte=convert_fecha(request.POST['inicio']),fin__gte=convert_fecha(request.POST['fin']))
                        print(pagos.count())
                        if pagos.filter(pagoaprobado=True).exists():
                            return HttpResponse(json.dumps({"result":"bad", "mensaje":"Su pago ya ha sido aprobado en el rango de fechas seleccionado, consulte con el administrador de practicas"}),content_type="application/json")
                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            except Exception as ex:
                print(ex)
                return HttpResponse(json.dumps({"result":"bad", "mensaje":"Error: "+str(ex)}),content_type="application/json")

        elif action == 'actualizar_niveles_induccion':
            try:
                nivelmalla_4to = NivelMalla.objects.get(pk=4)
                nivelmalla_5to = NivelMalla.objects.get(pk=5)
                coordinacion = Coordinacion.objects.filter(pk=COORDINACION_UACED).values('carrera')
                # niveles_4to = Nivel.objects.filter(cerrado=False,nivelmalla=nivelmalla_4to, carrera__id__in=coordinacion).exclude(carrera__id=36)
                niveles_4to = Nivel.objects.filter(cerrado=False, nivelmalla=nivelmalla_4to, carrera__id__in=coordinacion)
                niveles_5to = Nivel.objects.filter(cerrado=False, nivelmalla=nivelmalla_5to, carrera__id=36)
                contador = 0
                for n in niveles_4to:
                    if not NivelPracticaInduccion.objects.filter(nivel=n).exists():
                        contador = contador+1
                        induccion = NivelPracticaInduccion(nivel=n)
                        induccion.save()
                for n in niveles_5to:
                    if not NivelPracticaInduccion.objects.filter(nivel=n).exists():
                        contador = contador+1
                        induccion = NivelPracticaInduccion(nivel=n)
                        induccion.save()
                return HttpResponse(json.dumps({"result":"ok","mensaje":str(contador)+" grupos fueron agregados"}),content_type="application/json")
            except Exception as ex:
                print(ex)
                return HttpResponse(json.dumps({"result":"bad", "mensaje":"Error: "+str(ex)}),content_type="application/json")

        elif action == 'activar_induccion_todos':
            niveles_induccion = NivelPracticaInduccion.objects.filter(induccion=False)
            for n in niveles_induccion:
                n.induccion = True
                n.fecha = datetime.now()
                n.save()
            return HttpResponse(json.dumps({"result":"ok","mensaje":"Con "+str(niveles_induccion.count())+" grupos se ha compartido la induccion de practicas"}),content_type="application/json")

        elif action == 'activar_induccion':
            nivel_induccion = NivelPracticaInduccion.objects.get(pk=request.POST['id'])
            nivel_induccion.induccion = not nivel_induccion.induccion
            nivel_induccion.fecha = datetime.now()
            nivel_induccion.save()
            if nivel_induccion.induccion:
                mensaje = 'Induccion de practicas Pre-Profesionales Compartida'
            else:
                mensaje = 'Aun no se ha compartido la induccion de practicas'
            return HttpResponse(json.dumps({"result":"ok","mensaje":mensaje}),content_type="application/json")

        elif action=='updatefecha':
            try:
                nivel_induccion = NivelPracticaInduccion.objects.get(pk=request.POST['id'])
                if request.POST['desde'].lower()=='true':
                    nivel_induccion.desde = convert_fecha(request.POST['fecha'])
                else:
                    nivel_induccion.hasta = convert_fecha(request.POST['fecha'])
                nivel_induccion.save()

                client_address = ip_client_address(request)

                 # LOG DE CAMBIAR FECHA MATREIA
                LogEntry.objects.log_action(
                user_id         = request.user.pk,
                content_type_id = ContentType.objects.get_for_model(nivel_induccion).pk,
                object_id       = nivel_induccion.id,
                object_repr     = force_str(nivel_induccion),
                action_flag     = CHANGE,
                change_message  = 'Editada fecha induccion practicas (' + client_address + ')' )

                return HttpResponse(json.dumps({'result':'ok','Desde': nivel_induccion.desde.strftime("%d-%m-%Y"), 'Hasta': nivel_induccion.hasta.strftime("%d-%m-%Y")}),content_type="application/json")
            except Exception as ex:
                print(ex)

        elif action == 'add_docente':
            try:
                profesor = Profesor.objects.get(pk=request.POST['profesor'])
                nivel_induccion = NivelPracticaInduccion.objects.get(pk=request.POST['nivelinduccion'])
                nivel_induccion.profesor = profesor
                nivel_induccion.save()
                mensaje = 'Agregar docente a induccion de practicas'

                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                user_id         = request.user.pk,
                content_type_id = ContentType.objects.get_for_model(nivel_induccion).pk,
                object_id       = nivel_induccion.id,
                object_repr     = force_str(nivel_induccion),
                action_flag     = CHANGE,
                change_message  = mensaje+' (' + client_address + ')' )

                return HttpResponse(json.dumps({"result":"ok","mensaje":mensaje}),content_type="application/json")
            except Exception as ex:
                print(ex)
                return HttpResponse(json.dumps({"result":"bad", "mensaje":"Error: "+str(ex)}),content_type="application/json")

        elif action == 'eliminar_nivelinduccion':
            nivel_induccion = NivelPracticaInduccion.objects.get(pk=request.POST['id'])
            nivel_induccion.delete()
            mensaje = 'Registro Eliminado'

            client_address = ip_client_address(request)
            LogEntry.objects.log_action(
            user_id         = request.user.pk,
            content_type_id = ContentType.objects.get_for_model(nivel_induccion).pk,
            object_id       = nivel_induccion.id,
            object_repr     = force_str(nivel_induccion),
            action_flag     = DELETION,
            change_message  = mensaje+' (' + client_address + ')' )
            return HttpResponse(json.dumps({"result":"ok","mensaje":mensaje}),content_type="application/json")

        elif action == 'add_niveldepago':
            try:
                pago = PagoPracticasDocente.objects.get(pk=request.POST['pago'])
                nivel = Nivel.objects.get(pk=request.POST['nivel'])
                if NivelPagoPracticasDocente.objects.filter(pago=pago, nivel=nivel).exists():
                    return HttpResponse(json.dumps({"result":"bad","mensaje":"Nivel ya se encuentra registrado en pago seleccionado"}),content_type="application/json")
                else:
                    nivel_pago = NivelPagoPracticasDocente(pago=pago, nivel=nivel)
                    nivel_pago.save()
                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            except Exception as ex:
                print(ex)

        elif action == 'eliminar_niveldepago':
            niveldepago = NivelPagoPracticasDocente.objects.get(pk=request.POST['id'])
            niveldepago.delete()
            return HttpResponse(json.dumps({"result":"ok","mensaje":'Nivel eliminado del pago seleccionado'}),content_type="application/json")

        elif action == 'cambiar_fechas':
            try:
                print(request.POST)
                pago = PagoPracticasDocente.objects.get(pk=request.POST['idpago'])
                f = ProyeccionForm(request.POST)
                if f.is_valid():
                    if f.cleaned_data['desde']<f.cleaned_data['hasta']:
                        pago.inicio = f.cleaned_data['desde']
                        pago.fin = f.cleaned_data['hasta']
                        pago.save()
                    else:
                        return HttpResponseRedirect("/pagopracticas_docente?action=ver_practicas&id="+str(pago.id)+'&error=Fecha de inicio es mayor a fecha final')
                return HttpResponseRedirect("/pagopracticas_docente?action=ver_practicas&id="+str(pago.id))
            except Exception as ex:
                print(ex)
                return HttpResponseRedirect("/pagopracticas_docente?action=ver_practicas&id="+str(pago.id)+'error='+str(ex))

    else:
        data = {'title': 'Pago Practicas a Docentes'}
        addUserData(request, data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action == 'ver_practicas':
                try:
                    pago = PagoPracticasDocente.objects.get(pk=request.GET['id'])
                    practicas = InscripcionPracticas.objects.filter(profesor=pago.profesor, inicio__gte=pago.inicio, fin__lte=pago.fin).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2')
                    if NivelPagoPracticasDocente.objects.filter(pago=pago):
                        nivel_pago = NivelPagoPracticasDocente.objects.filter(pago=pago)
                        matriculas = Matricula.objects.filter(nivel__grupo__id__in=nivel_pago.values('nivel__grupo__id'))
                        practicas = practicas.filter(inscripcion__id__in=matriculas.values('inscripcion__id'))
                    else:
                        practicas = None

                    search = None
                    if 's' in request.GET:
                        search = request.GET['s']
                    if search:
                        ss = search.split(' ')
                        while '' in ss:
                            ss.remove('')
                        if len(ss)==1:
                            practicas = practicas.filter(Q(inscripcion__persona__nombres__icontains=search) | Q(inscripcion__persona__apellido1__icontains=search) | Q(inscripcion__persona__apellido2__icontains=search) | Q(inscripcion__persona__cedula__icontains=search) | Q(inscripcion__persona__pasaporte__icontains=search) | Q(inscripcion__persona__usuario__username__icontains=search)).order_by('inscripcion__persona__apellido1')[:100]
                        else:
                            practicas = practicas.filter(Q(inscripcion__persona__apellido1__icontains=ss[0]) & Q(inscripcion__persona__apellido2__icontains=ss[1])).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')[:100]

                    data['pago'] = pago
                    data['practicas'] = practicas
                    data['search'] = search if search else ""
                    form = InscripcionPracticasDistribucionForm(initial={'horas': 0, 'inicio': pago.inicio, 'fin': pago.fin})
                    formhorasnivel=PracticasDistribucionHorasForm(initial={'horasnivel': 0})
                    data['listnivel'] = NivelMalla.objects.filter(id__in=AsignaturaMalla.objects.filter(Q(asignatura__nombre__icontains='LABORALES')|Q(asignatura__nombre__icontains='PREPRO')).values('nivelmalla'))
                    data['formhorasnivel'] = formhorasnivel
                    data['fechasform'] = ProyeccionForm


                    data['form'] = form
                    data['horas_practicas'] = HORAS_PRACTICA

                    if 'error' in request.GET:
                        data['error'] = request.GET['error']

                    return render(request ,"pagopracticas_docente/ver_practicas.html" ,  data)
                except Exception as ex:
                    print(ex)
                    return HttpResponseRedirect('/pagopracticas_docente?error='+str(ex))

            elif action == 'ver_niveles':
                try:
                    niveles_induccion = NivelPracticaInduccion.objects.filter().order_by('-nivel__periodo','-nivel__fin')
                    search = None
                    if 's' in request.GET:
                        search = request.GET['s']
                    if search:
                        niveles_induccion = niveles_induccion.filter(nivel__paralelo__icontains=search).order_by('induccion','-nivel__periodo','nivel__paralelo')[:100]
                    if 'p' in request.GET:
                        periodo = Periodo.objects.get(pk=request.GET['p'])
                        niveles_induccion = niveles_induccion.filter(nivel__periodo=periodo)
                        data['periodo'] = True

                    data['niveles_induccion'] = niveles_induccion
                    data['search'] = search if search else ""
                    if 'error' in request.GET:
                        data['error'] = 1

                    return render(request ,"pagopracticas_docente/ver_niveles.html" ,  data)
                except Exception as ex:
                    print(ex)
                    return HttpResponseRedirect('/pagopracticas_docente?error='+str(ex))

            elif action == 'ver_nivelesdepago':
                pago = PagoPracticasDocente.objects.get(pk=request.GET['id'])
                if NivelPagoPracticasDocente.objects.filter(pago=pago).exists():
                    nivelpago = NivelPagoPracticasDocente.objects.filter(pago=pago).order_by('nivel__paralelo')
                    data['nivelpagos'] = nivelpago
                data['pago'] = pago
                if 'error' in request.GET:
                    data['error'] = 1
                return render(request ,"pagopracticas_docente/ver_nivelesdepago.html" ,  data)

        else:
            try:
                hoy = datetime.date(datetime.now())
                search = None
                pagos = PagoPracticasDocente.objects.filter().order_by('-id')
                if 's' in request.GET:
                    search = request.GET['s']
                if search:
                    pagos = pagos.filter(Q(descripcion__icontains=search)|Q(profesor__persona__apellido1__icontains=search)|Q(profesor__persona__apellido2__icontains=search)|Q(profesor__persona__nombres__icontains=search)|Q(profesor__persona__cedula__icontains=search)).order_by('profesor__persona__apellido1','profesor__persona__apellido2')

                paging = Paginator(pagos, 20)
                p = 1
                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                    page = paging.page(p)
                except:
                    page = paging.page(1)

                data['paging'] = paging
                data['page'] = page
                data['pagos'] = page.object_list
                data['search'] = search if search else ""
                data['form'] = PagoPracticasForm
                data['nivelesform'] = NivelPagoPPPForm
                data['rol'] = RolPago.objects.filter().order_by('-id')[:1].get()
                data['hoy'] = hoy
                if 'error' in request.GET:
                    data['error'] = request.GET['error']

                return render(request ,"pagopracticas_docente/pagopracticas_docentebs.html" ,  data)
            except Exception as ex:
                print(ex)
                return HttpResponseRedirect("/pagopracticas_docente?error="+str(ex))
