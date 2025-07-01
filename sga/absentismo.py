from datetime import datetime, date, timedelta
import json
from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from django.utils.encoding import force_str
from decorators import secure_module
from settings import UTILIZA_GRUPOS_ALUMNOS, EMAIL_ACTIVE, SISTEMAS_GROUP_ID, PROFESORES_GROUP_ID, ALUMNOS_GROUP_ID
from sga.commonviews import addUserData, ip_client_address
from sga.forms import AbsentismoForm, ProyeccionForm, AsistAsuntoEstudiantForm
from sga.models import Inscripcion,Absentismo, MateriaAsignada, convertir_fecha, Carrera, elimina_tildes, CategoriaRubro, Rubro, OpcionRespuesta, EstadoLlamada, OpcionEstadoLlamada, Matricula, RecordAcademico, Leccion, Clase, SeguimientoAbsentismo, SeguimientoAbsentismoDetalle, PersonaAsuntos, Persona

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
@transaction.atomic()
def view(request):
    try:
        if request.method == 'POST':
           action = request.POST['action']

           if action == 'addobserva' :
               try:
                   absentismo = Absentismo.objects.get(id=request.POST['idmateriasig'])
                   absentismo.observaadmin = request.POST['observacion']
                   absentismo.fechaobserv = datetime.now()
                   if request.POST['reintegro'] == 'true':
                       reintegro = True
                   else:
                       reintegro = False
                   absentismo.reintegro = reintegro
                   absentismo.finalizado = True
                   absentismo.save()

                   client_address = ip_client_address(request)
                   #Log de ADICIONAR INSCRIPCION
                   LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(absentismo).pk,
                        object_id       = absentismo.id,
                        object_repr     = force_str(absentismo),
                        action_flag     = ADDITION,
                        change_message  = 'Finalizando absentismo (' + client_address + ')')
                   if EMAIL_ACTIVE:
                      try:
                        absentismo.email_observacionadmin(request.user)
                      except Exception as ex:
                          pass
                   return HttpResponse(json.dumps({"result": "ok","idins":str(absentismo.materiaasignada.matricula.inscripcion.id)}),content_type="application/json")
               except Exception as ex:
                   return HttpResponse(json.dumps({"result": "bad"}),content_type="application/json")

           elif action == 'add':
               materiaasignada = MateriaAsignada.objects.get(id=request.POST['materia'])
               if not Absentismo.objects.filter(materiaasignada=materiaasignada).exists():
                   absentismo = Absentismo(materiaasignada_id = materiaasignada.id ,
                                           observacion = request.POST['observacion'],
                                           fecha = datetime.now(),
                                           manual=True)
                   absentismo.save()
                   materiaasignada.absentismo = True
                   materiaasignada.save()
                   client_address = ip_client_address(request)
                   #Log de ADICIONAR INSCRIPCION
                   LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(absentismo).pk,
                        object_id       = absentismo.id,
                        object_repr     = force_str(absentismo),
                        action_flag     = ADDITION,
                        change_message  = 'Adicionado Absentismo  (' + client_address + ')')
                   return HttpResponseRedirect("/absentismo?s="+materiaasignada.matricula.inscripcion.persona.cedula)
               else:
                   return HttpResponseRedirect("/absentismo?action=add&id="+str(materiaasignada.matricula.inscripcion.id)+"&error")

           elif action == 'valida_fecha_seguimiento':
               try:
                   absentismo = Absentismo.objects.get(id=request.POST['absentismo'])
                   hoy = datetime.today().date()
                   fecha = datetime.strptime(request.POST['fecha'],'%d-%m-%Y').date()

                   if Leccion.objects.filter(fecha=absentismo.fecha).exists() and fecha>=hoy and fecha<=absentismo.materiaasignada.materia.fin:
                       return HttpResponse(json.dumps({"result": "ok"}),content_type="application/json")

                   return HttpResponse(json.dumps({"result": "bad", 'mensaje':'Fecha no disponible, materia culmina el '+str(absentismo.materiaasignada.materia.fin)}),content_type="application/json")
               except Exception as ex:
                   print(ex)
                   return HttpResponse(json.dumps({"result": "bad", 'mensaje':ex}),content_type="application/json")

           elif action == 'add_seguimiento':
               try:
                    datos = json.loads(request.POST['absentismos'])
                    inscripcion = Inscripcion.objects.get(pk=request.POST['inscripcion'])
                    estado_llamada = EstadoLlamada.objects.get(pk=request.POST['estado_llamada'])
                    observacion = request.POST['observacion']
                    hoy = datetime.today().date()

                    seguimiento = SeguimientoAbsentismo(inscripcion=inscripcion,
                                                        estadollamada=estado_llamada,
                                                        observacion = observacion,
                                                        usuario=request.user,
                                                        fecha=hoy,
                                                        estado=True)
                    seguimiento.save()

                    for d in datos:
                        if len(datos) > 0:
                            if Absentismo.objects.filter(pk=d['absentismo']).exists():
                                absentismo = Absentismo.objects.get(pk=d['absentismo'])
                                fecha_reingreso = datetime.strptime(d['fecha_reingreso'],'%d-%m-%Y').date()

                                seguimiento_detalle = SeguimientoAbsentismoDetalle(seguimientoabsentismo=seguimiento,
                                                                                   absentismo=absentismo,
                                                                                   fecha_posiblereintegro=fecha_reingreso)
                                seguimiento_detalle.save()

                    return HttpResponse(json.dumps({"result": "ok"}),content_type="application/json")
               except Exception as ex:
                   print(ex)
                   return HttpResponse(json.dumps({"result": "bad", 'mensaje':ex}),content_type="application/json")

           elif action == 'add_asistente':
               try:
                   persona = Persona.objects.get(pk=request.POST['idsolici'])

                   if 'estado' in request.POST:
                       estado = True
                   else:
                       estado = False
                   if request.POST['editar'] == '0':
                       asistestudiant = PersonaAsuntos(persona=persona, fecha=request.POST['fecha'], estado=estado)
                       mensaje = 'Ingreso asistente de asunto estudiantil'
                   else:
                       asistestudiant = PersonaAsuntos.objects.get(pk=request.POST['editar'])
                       asistestudiant.persona = persona
                       asistestudiant.fecha=request.POST['fecha']
                       asistestudiant.estado=estado
                       mensaje = 'Edicion asistente de asunto estudiantil'
                   asistestudiant.save()

                   client_address = ip_client_address(request)
                   LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(asistestudiant).pk,
                        object_id       = asistestudiant.id,
                        object_repr     = force_str(asistestudiant),
                        action_flag     = ADDITION,
                        change_message  = mensaje+' (' + client_address + ')' )

                   return HttpResponseRedirect('/absentismo?action=asistentes')
               except Exception as ex:
                   print(ex)

           elif action == 'reasignar':
               try:
                    asistente = PersonaAsuntos.objects.filter(persona__usuario__id=request.POST['usuario'])[:1].get()
                    asistrecibe = PersonaAsuntos.objects.filter(persona__usuario__id=request.POST['asistrecibe'])[:1].get()
                    cantidad = request.POST['cantidad']
                    if int(cantidad) > (asistente.asignados() - asistente.gestionados()):
                        return HttpResponse(json.dumps({"result":"bad",'mensaje': 'Cantidad excede las inscripciones asignadas'}),content_type="application/json")
                    inscripcion = Inscripcion.objects.filter(personaasuntos = asistente)[:cantidad]
                    # if request.POST['carrera'] != '':
                    #     carrera = Carrera.objects.get(pk=request.POST['carrera'])
                    #     inscripcion = Inscripcion.objects.filter(asistente = asistente,registroseguimiento__inscripcion=None, carrera=carrera)[:cantidad]
                    for i in inscripcion:
                        i.personaasuntos = asistrecibe
                        i.save()
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(asistente).pk,
                        object_id       = asistente.id,
                        object_repr     = force_str(asistente),
                        action_flag     = ADDITION,
                        change_message  = 'Se ha reasignado ' + cantidad + ' registros de '+ elimina_tildes(asistente.persona.nombre_completo()) + 'a ' + elimina_tildes  (asistrecibe.persona.nombre_completo()) + ' ('+ client_address + ')' )
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")

               except Exception as e:
                    return HttpResponse(json.dumps({"result":"bad",'mensaje': str(e)}),content_type="application/json")

        else:
            data = {'title':'Lista de Estudiantes en absentismo'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']
                if action=='detalleabsent':
                    data = {}
                    data['inscripcion'] = Inscripcion.objects.filter(id=request.GET['id'])[:1].get()
                    data['absentismos'] = Absentismo.objects.filter(materiaasignada__matricula__inscripcion=request.GET['id']).order_by('id')
                    return render(request ,"absentismo/detalle.html" ,  data)
                elif action =='verproyeccion':
                    try:
                        desde  =convertir_fecha(request.GET['desde'])
                        hasta  = convertir_fecha(request.GET['hasta'])
                        absento=Absentismo.objects.filter(fechaobserv__gte=desde,fechaobserv__lte=hasta,reintegro=True).distinct('materiaasignada').distinct('materiaasignada__matricula__inscripcion').values('materiaasignada__matricula__inscripcion').order_by('materiaasignada__matricula__inscripcion__persona__apellido1','materiaasignada__matricula__inscripcion__persona__apellido2')
                        fila = []
                        carrera = []
                        carrera_por_recuperar_nivel = []
                        carrera_por_recuperar = []
                        carrera_recuperado = []
                        por_recuperar = 0
                        por_recuperar_nivel = 0
                        recuperado = 0
                        inscritos = Inscripcion.objects.filter(pk__in=absento)
                        carreras_id=Inscripcion.objects.filter(pk__in=absento).order_by('carrera').distinct('carrera').values('carrera')

                        arraycarrera_por_recuperar_nivel = {}
                        arraycarrera_por_recuperar = {}
                        arraycarrera_recuperado = {}
                        for c in Carrera.objects.filter(id__in=carreras_id):
                            tot_ca=inscritos.filter(carrera=c).count()
                            arraycarrera_por_recuperar_nivel['variable'+str(c.id)]={'nombre':c.nombre,'valor':0}
                            arraycarrera_recuperado['variable'+str(c.id)]={'nombre':c.nombre,'valor':0}
                            arraycarrera_por_recuperar['variable'+str(c.id)]={'nombre':c.nombre,'valor':0}
                            carrera.append(((c.nombre),str(tot_ca)))

                        for i in absento:

                            reintegro=''
                            mensaje =''
                            ins =Inscripcion.objects.filter(pk=i['materiaasignada__matricula__inscripcion'])[:1].get()
                            # ins =Inscripcion.objects.filter(pk=75579)[:1].get()
                            # print(ins)
                            if ins.absentismo_reintegro():
                                reintegro = str(ins.absentismo_reintegro().materiaasignada.matricula.nivel.nivelmalla) +" - "+ ins.absentismo_reintegro().materiaasignada.matricula.nivel.paralelo
                            if ins.falta_reintegrar():
                                mensaje='Faltan Materias por Recuperar'
                            arraycarrera_por_recuperar_nivel['variable'+str(ins.carrera.id)]['valor'] = arraycarrera_por_recuperar_nivel['variable'+str(ins.carrera.id)]['valor'] +  ins.por_recuperar_nivel()
                            arraycarrera_recuperado['variable'+str(ins.carrera.id)]['valor'] = arraycarrera_recuperado['variable'+str(ins.carrera.id)]['valor'] +  ins.recuperado(desde,hasta)
                            arraycarrera_por_recuperar['variable'+str(ins.carrera.id)]['valor'] = arraycarrera_por_recuperar['variable'+str(ins.carrera.id)]['valor'] + ins.por_recuperar()
                            fila.append((ins,mensaje,str(ins.carrera),reintegro, ins.por_recuperar_nivel(),ins.recuperado(desde,hasta), ins.ultimo_nivel(),ins.por_recuperar(),ins.carrera.id))

                            por_recuperar_nivel = por_recuperar_nivel +  ins.por_recuperar_nivel()
                            recuperado = recuperado + ins.recuperado(desde,hasta)
                            por_recuperar = por_recuperar + ins.por_recuperar()

                        for c in Carrera.objects.filter(id__in=carreras_id):

                             carrera_por_recuperar_nivel.append((arraycarrera_por_recuperar_nivel['variable'+str(c.id)]['nombre'],arraycarrera_por_recuperar_nivel['variable'+str(c.id)]['valor']))
                             carrera_recuperado.append((arraycarrera_recuperado['variable'+str(c.id)]['nombre'],arraycarrera_recuperado['variable'+str(c.id)]['valor']))
                             carrera_por_recuperar.append((arraycarrera_por_recuperar['variable'+str(c.id)]['nombre'],arraycarrera_por_recuperar['variable'+str(c.id)]['valor']))

                        data['total'] = Inscripcion.objects.filter(id__in=absento).count()
                        data['inscripcion'] =fila
                        data['desde']=desde
                        data['hasta']=hasta
                        data['por_recuperar_nivel']=por_recuperar_nivel
                        data['por_recuperar']=por_recuperar
                        data['recuperado']=recuperado
                        data['carrera']=carrera
                        data['carrera_por_recuperar_nivel']=carrera_por_recuperar_nivel
                        data['carrera_recuperado']=carrera_recuperado
                        data['carrera_por_recuperar']=carrera_por_recuperar
                        data['frmproyeccion'] = ProyeccionForm(initial={'desde':datetime.now().date(), 'hasta':datetime.now().date()})
                        return render(request ,"absentismo/proyeccion.html" ,  data)
                    except Exception as e:
                        print(str(e))
                        HttpResponseRedirect("/?info="+str(e))

                elif action=='add':
                    i = Inscripcion.objects.get(pk=request.GET['id'])
                    data['title'] = 'Adicionar Registro Absentismo'
                    data['mat'] = MateriaAsignada.objects.filter(matricula = i.matricula()).order_by('materia__asignatura__nombre')
                    data['form']=AbsentismoForm(initial={'fecha':datetime.now().strftime('%d-%m-%Y')})
                    data['matricula'] = i.matricula()
                    if 'error' in request.GET:
                        data['error']=1
                    data['i']=i
                    return render(request ,"absentismo/add.html" ,  data)

                elif action == 'gestionar':
                    try:
                        inscripcion = Inscripcion.objects.get(id=request.GET['id'])
                        ma = Absentismo.objects.filter(materiaasignada__matricula__inscripcion=inscripcion, materiaasignada__absentismo=True, finalizado=False).distinct('materiaasignada').values('materiaasignada')
                        absentismos = Absentismo.objects.filter(materiaasignada__id__in=ma)
                        # absentismos1 = Absentismo.objects.filter(materiaasignada__matricula__inscripcion=inscripcion, materiaasignada__absentismo=True, finalizado=False, materiaasignada__materia__cerrado=False, reasignar_materia=False)
                        # absentismos2 = Absentismo.objects.filter(materiaasignada__matricula__inscripcion=inscripcion, materiaasignada__absentismo=True, finalizado=False, materiaasignada__materia__cerrado=True, reasignar_materia=True)
                        # absentismos = absentismos1.order_by('-id')|absentismos2.order_by('-id')

                        data['opcrespuesta'] = OpcionRespuesta.objects.all()
                        data['estadollamada'] = EstadoLlamada.objects.all()
                        data['opcllamada'] = OpcionEstadoLlamada.objects.all()
                        # data['tiporespuesta'] = TipoRespuesta.objects.all()
                        data['ultima_matricula']  = Matricula.objects.filter(inscripcion=inscripcion).order_by('-id')[:1].get()
                        data['inscripcion'] = inscripcion
                        data['absentismos'] = absentismos
                        data['hoy'] = datetime.today().date()

                        return render(request ,"absentismo/ficha.html" ,  data)
                    except Exception as ex:
                        print(ex)

                elif action == 'detalle_asistencias':
                    try:
                        absentismo = Absentismo.objects.get(pk=request.GET['absentismo'])
                        materia = absentismo.materiaasignada.materia
                        data['profesor'] = absentismo.materiaasignada.materia.profesormateria_set.filter()[:1].get
                        data['materia'] = materia
                        data['asignadomateria']  = absentismo.materiaasignada
                        # data['materiaasignada']  = materia.asignados_a_esta_materia()
                        data['totalestmateria'] = materia.asignados_a_esta_materia().count()
                        data['absentos']= MateriaAsignada.objects.filter(materia=materia,absentismo=True).count()
                        data['absentosver']= MateriaAsignada.objects.filter(materia=materia,absentismo=True)

                        # data['form'] = AusenciaJustificadaForm()
                        # data['usa_modulo_justificacion_ausencias'] = USA_MODULO_JUSTIFICACION_AUSENCIAS
                        # data['conduccion']=INSCRIPCION_CONDUCCION
                        return render(request ,"absentismo/detalle_asistencias.html" ,  data)
                    except Exception as ex:
                        print(ex)

                elif action == 'ver_seguimiento':
                    try:
                        inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                        seguimientos = SeguimientoAbsentismo.objects.filter(inscripcion=inscripcion).order_by('-fecha')
                        data['inscripcion'] = inscripcion
                        data['seguimientos'] = seguimientos
                        return render(request ,"absentismo/ver_seguimiento.html" ,  data)
                    except Exception as ex:
                        print(ex)

                elif action == 'asistentes':
                    try:
                        asistentes = PersonaAsuntos.objects.filter(estado=True).order_by('persona__apellido1','persona__apellido2')
                        if 'i' in request.GET:
                            asistentes = PersonaAsuntos.objects.filter(estado=False).order_by('persona__apellido1','persona__apellido2')
                            data['inactivos'] = True
                        data['asistentes'] = asistentes
                        data['hoy'] = datetime.today().date()
                        data['form']=AsistAsuntoEstudiantForm(initial={'fecha':datetime.now().date()})
                        gruposexcluidos = [PROFESORES_GROUP_ID,ALUMNOS_GROUP_ID,SISTEMAS_GROUP_ID]
                        data['gruposexcluidos'] = list(Persona.objects.filter().exclude(usuario__groups__id__in=gruposexcluidos).order_by('apellido1').values_list('id', flat=True))
                        return render(request ,"absentismo/asistentes.html" ,  data)
                    except Exception as ex:
                        print(ex)

                elif action == 'asistente_existe':
                    try:
                        if request.POST['editar'] == '0':
                            if PersonaAsuntos.objects.filter(persona__id=request.POST['idasis']).exists():
                                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                        else:
                            if PersonaAsuntos.objects.filter(persona__id=request.POST['idasis']).exclude(pk=request.POST['editar']).exists():
                                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
                    except:
                        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

                if action == 'eliminar':
                    asisten = PersonaAsuntos.objects.filter(pk=request.GET['id'])[:1].get()
                    asisten.estado = False
                    asisten.save()
                return HttpResponseRedirect('/absentismo?action=asistentes')

            else:
                search = None

                inactivos = None
                finalizados = None

                if 's' in request.GET:
                    search = request.GET['s']
                    data['search'] = search
                if 'i' in request.GET:
                    inactivos = request.GET['i']

                if 'f' in request.GET:
                    finalizados = request.GET['f']

                inscripciones = Inscripcion.objects.filter(persona__usuario__is_active=True,
                                                           pk__in=Absentismo.objects.filter(materiaasignada__absentismo=True)
                                                           .distinct('materiaasignada__matricula__inscripcion').values('materiaasignada__matricula__inscripcion')).order_by('-id')

                if search:
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')
                    if len(ss)==1:
                        inscripciones = inscripciones.filter(Q(persona__nombres__icontains=search) | Q(persona__apellido1__icontains=search) | Q(persona__apellido2__icontains=search) | Q(persona__cedula__icontains=search) | Q(persona__pasaporte__icontains=search) | Q(identificador__icontains=search) | Q(inscripciongrupo__grupo__nombre__icontains=search) | Q(carrera__nombre__icontains=search) | Q(persona__usuario__username__icontains=search),pk__in=Absentismo.objects.filter().distinct('materiaasignada__matricula__inscripcion').values('materiaasignada__matricula__inscripcion')).order_by('persona__apellido1')
                    else:
                        inscripciones = inscripciones.filter(Q(persona__apellido1__icontains=ss[0]) & Q(persona__apellido2__icontains=ss[1]),pk__in=Absentismo.objects.filter().distinct('materiaasignada__matricula__inscripcion').values('materiaasignada__matricula__inscripcion')).order_by('persona__apellido1','persona__apellido2','persona__nombres')
                if inactivos:
                    inscripciones = Inscripcion.objects.filter(persona__usuario__is_active=True,pk__in=Absentismo.objects.filter(materiaasignada__absentismo=False).exclude(materiaasignada__matricula__inscripcion__in=Absentismo.objects.filter(materiaasignada__absentismo=True).distinct('materiaasignada__matricula__inscripcion').values('materiaasignada__matricula__inscripcion')).distinct('materiaasignada__matricula__inscripcion').values('materiaasignada__matricula__inscripcion')).order_by('persona__apellido1')
                    data['inactivos'] = inactivos

                if finalizados:
                    inscripciones = Inscripcion.objects.filter(persona__usuario__is_active=True, pk__in=Absentismo.objects.filter(finalizado=True).exclude(materiaasignada__absentismo=False).distinct('materiaasignada__matricula__inscripcion').values('materiaasignada__matricula__inscripcion')).order_by('-id').order_by('persona__apellido1')
                    data['finalizados'] = finalizados

                if 'a2' in request.GET:
                    data['a2'] = True
                    fecha_actual = datetime.now()
                    antiguedad = fecha_actual.year - 5
                    desde = fecha_actual.replace(antiguedad)
                    categoria = CategoriaRubro.objects.get(pk=25)

                    rubro_vencimiento_desde = date.today() - timedelta(8)

                    rubros_excluidos = Rubro.objects.filter(cancelado=False, fechavence__gte=rubro_vencimiento_desde, inscripcion__id__in=inscripciones)
                    try:
                        # absentos1 = Absentismo.objects.filter(materiaasignada__absentismo=True, finalizado=False, materiaasignada__materia__cerrado=False, reasignar_materia=False)
                        # absentos2 = Absentismo.objects.filter(materiaasignada__absentismo=True, finalizado=False, materiaasignada__materia__cerrado=True, reasignar_materia=True)
                        absentos = Absentismo.objects.filter(materiaasignada__absentismo=True, finalizado=False,materiaasignada__matricula__inscripcion__in=rubros_excluidos.values('inscripcion'))
                        # if SeguimientoAbsentismoDetalle.objects.filter(absentismo__in=absentos, finalizado=False).exists():
                        #     seguimientos_detalles = SeguimientoAbsentismoDetalle.objects.filter(absentismo__in=absentos, finalizado=False)
                        #     absentos = absentos.filter().exclude(id__in=seguimientos_detalles.values('absentismo__id'))

                        if inscripciones.filter(persona__usuario__is_active=True, id__in=absentos.values('materiaasignada__matricula__inscripcion')).order_by('persona__apellido1').exists():
                            inscripciones = inscripciones.filter(persona__usuario__is_active=True, id__in=absentos.values('materiaasignada__matricula__inscripcion')).order_by('persona__apellido1')
                    except Exception as ex:
                        print('Error: '+ str(ex))

                # GESTIONADOS
                if 'g' in request.GET:
                    data['g'] = True
                    if SeguimientoAbsentismo.objects.filter().exists():
                        inscripciones = inscripciones.filter(id__in=SeguimientoAbsentismo.objects.filter().values('inscripcion'))

                if PersonaAsuntos.objects.filter(persona__usuario__username=request.user).exists():
                    inscripciones = inscripciones.filter(personaasuntos=PersonaAsuntos.objects.filter(persona__usuario__username=request.user)[:1].get())
                    data['persona_asuntos'] = True

                #POR GESTIONAR
                if 'pg' in request.GET:
                    data['pg'] = True
                    if Absentismo.objects.filter(materiaasignada__absentismo=True, finalizado=False, materiaasignada__matricula__inscripcion__personaasuntos__persona__usuario__username=request.user).exclude(id__in=SeguimientoAbsentismoDetalle.objects.filter(finalizado=False, seguimientoabsentismo__estado=True).values('absentismo')).exists():
                        absentismos = Absentismo.objects.filter(materiaasignada__absentismo=True, finalizado=False, materiaasignada__matricula__inscripcion__personaasuntos__persona__usuario__username=request.user).exclude(id__in=SeguimientoAbsentismoDetalle.objects.filter(finalizado=False, seguimientoabsentismo__estado=True).values('absentismo'))
                        inscripciones = inscripciones.filter(id__in=absentismos.values('materiaasignada__matricula__inscripcion'))

                if 'asis' in request.GET:
                    asistente = PersonaAsuntos.objects.get(pk=request.GET['asis'])
                    inscripciones = inscripciones.filter(personaasuntos=asistente)
                    data['asistente'] = asistente

                data['usuario'] = request.user
                paging = MiPaginador(inscripciones, 30)
                p = 1
                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                        # if band==0:
                        #     inscripciones = Inscripcion.objects.all().order_by('persona__apellido1')
                        paging = MiPaginador(inscripciones, 30)
                    page = paging.page(p)
                except Exception as ex:
                    page = paging.page(1)

                data['paging'] = paging
                data['rangospaging'] = paging.rangos_paginado(p)
                data['page'] = page

                data['inscripciones'] = page.object_list
                data['utiliza_grupos_alumnos'] = UTILIZA_GRUPOS_ALUMNOS
                data['frmproyeccion'] = ProyeccionForm(initial={'desde':datetime.now().date(), 'hasta':datetime.now().date()})
                data['asistentes'] = PersonaAsuntos.objects.filter(estado=True).order_by('persona__apellido1')

                return render(request ,"absentismo/listainscripcion.html" ,  data)

    except Exception as e:
        print(e)
        return HttpResponseRedirect('/')

