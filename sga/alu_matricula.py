from datetime import datetime, timedelta
from decimal import Decimal
from itertools import chain
import json
from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Sum, Q
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.utils.encoding import force_str
from decorators import secure_module
from settings import NOTA_PARA_EXAMEN_CONDUCCION, NUMERO_PREGUNTA, ASIGNATURA_EXAMEN_GRADO_CONDU, ASIGNATURA_PRACTICA_CONDUCCION, NIVEL_MALLA_CERO, \
     DEFAULT_PASSWORD, EXAMEN_PRACTI_COMPLEX, EXAMEN_TEORI_COMPLEX, EXAMEN_PRACTIPORC_COMPLEX, EXAMEN_TEORIPORC_COMPLEX, NOTA_PARA_APROBAR, ASIST_PARA_APROBAR, \
     PROMEDIO_ASISTENCIAS_CONDU,INSCRIPCION_CONDUCCION, NIVEL_MALLA_UNO, GENERAR_RUBROS_PAGO, EMAIL_ACTIVE, SISTEMAS_GROUP_ID, NIVEL_SEMINARIO, HABILITA_DESC_MATRI, \
     DESCUENTO_MATRIC_PORCENT,NIVEL_GRADUACION, ID_CONVENIO_BECA_TECT, ID_TIPO_BENEFICICO_BECA, ID_TIPOBECA, ID_MOTIVO_BECA_TEC
from sga.commonviews import addUserData, ip_client_address
from sga.forms import SolicutudMatriculaForm
from sga.models import TituloExamenCondu, PreguntaExamen, Inscripcion, InscripcionExamen, RespuestaExamen, DetalleExamen, HistoricoRecordAcademico, RecordAcademico, \
     Aula, AsignaturaMalla, ExamenPractica, TipoAula, TipAulaExamen, Nivel, MateriaAsignada, Matricula, Materia, Rubro, RubroCuota, RubroMatricula, \
     SolicitudSecretariaDocente, SolicitudesGrupo, ModuloGrupo, Descuento, DetalleDescuento, TIPOS_PAGO_NIVEL, RubroOtro, TipoOtroRubro, SolicitudBeca, \
     TablaDescuentoBeca, DetalleRubrosBeca, RetiradoMatricula, DetalleRetiradoMatricula
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
@transaction.atomic()
@secure_module
def view(request):
    try:
        if request.method == 'POST':
            action = request.POST['action']

            if action == 'matricular':
                result={}
                sid = transaction.savepoint()
                try:
                    inscripcion = Inscripcion.objects.filter(pk=request.POST['inscripcion'])[:1].get()
                    nivel = Nivel.objects.filter(pk=request.POST['nivel'])[:1].get()
                    # variables para buscar si existe matricula en el mismo nivel para no crear los rubros
                    crearubro=True
                    datomatricu=None
                    if  nivel.mat_nivel() >= nivel.capacidadmatricula :
                        result['result'] ="bad"
                        return HttpResponse(json.dumps(result), content_type="application/json")
                    matricula = Matricula(inscripcion=inscripcion,
                                    nivel=nivel,
                                    pago=False,
                                    iece=False,
                                    fecha = datetime.now().date(),
                                    becado=False,
                                    porcientobeca=0)

                    matricula.save()

                    solicitudbeca=None
                    if SolicitudBeca.objects.filter(inscripcion=inscripcion,nivel__nivelmalla__id=nivel.nivelmalla.id,tiposolicitud=1).order_by('-fecha').exists():
                         if SolicitudBeca.objects.filter(inscripcion=inscripcion,nivel__nivelmalla__id=nivel.nivelmalla.id,tiposolicitud=1,aprobado=True,aprobacionestudiante=True,asignaciontarficadescuento=True).order_by('-fecha').exists():
                            solicitudbeca = SolicitudBeca.objects.filter(inscripcion=inscripcion,nivel__nivelmalla__id=nivel.nivelmalla.id,tiposolicitud=1,aprobado=True,aprobacionestudiante=True).order_by('-fecha')[:1].get()
                         else:
                             if SolicitudBeca.objects.filter(inscripcion=inscripcion,nivel__nivelmalla__id=nivel.nivelmalla.id,tiposolicitud=2,aprobado=True,aprobacionestudiante=True,asignaciontarficadescuento=True).order_by('-fecha').exists():
                                solicitudbeca = SolicitudBeca.objects.filter(inscripcion=inscripcion,nivel__nivelmalla__id=nivel.nivelmalla.id,tiposolicitud=2,aprobado=True,aprobacionestudiante=True).order_by('-fecha')[:1].get()


                    materias=[]
                    for m in  json.loads(request.POST['ver']):
                        materias.append(m['id'])
                    for m in Materia.objects.filter(id__in=materias):
                        pendientes = inscripcion.recordacademico_set.filter(asignatura__in=m.asignatura.precedencia.all(),aprobada=False)
                        if pendientes.count()==0:
                            if not MateriaAsignada.objects.filter(materia__asignatura=m.asignatura,matricula=matricula).exists():
                                asign = MateriaAsignada(matricula=matricula,materia=m,notafinal=0,asistenciafinal=0,supletorio=0)
                                asign.save()
                    pendientes=[]
                    pendientes2=[]
                    for p in  json.loads(request.POST['pendientes']):
                        pendientes.append(p['id'])


                    for pendiente in Materia.objects.filter(id__in=pendientes):
                        recordPendiente = RecordAcademico(inscripcion=inscripcion,asignatura=pendiente.asignatura,nota=0,asistencia=0,fecha=datetime.now(),convalidacion=False,aprobada=False,pendiente=True)
                        recordPendiente.save()

                    for p in  json.loads(request.POST['pendientes2']):
                        pendientes2.append(p['id'])

                    for pendiente in Materia.objects.filter(id__in=pendientes2):
                        recordPendiente = RecordAcademico(inscripcion=inscripcion,asignatura=pendiente.asignatura,nota=0,asistencia=0,fecha=datetime.now(),convalidacion=False,aprobada=False,pendiente=True)
                        recordPendiente.save()
                    rubros =[]
                    pp = 1.0 if not matricula.becado else ((100-matricula.porcientobeca)/100.0)
                    #OCastillo 13-03-2023 se crea una lista con los rubros adicionales que no son matricula ni cuotas al igual que en modulo matricula
                    lista2=[]
                    for pn in TIPOS_PAGO_NIVEL:
                        if not 'CUOTA' in pn[1] and not  'MATRICULA' in pn[1] :
                            lista2.append(pn[0])

                    # for pago in nivel.pagonivel_set.all().order_by('fecha'):
                    #OCastillo 13-03-2024 se excluyen los rubros adicionales de la lista previa
                    for pago in nivel.pagonivel_set.all().exclude(tipo__in=lista2):
                        if pago.tipo==0 or (pago.tipo>0 and pp>0):
                            rubro = Rubro(fecha=datetime.today().date(),
                                        valor = pago.valor, inscripcion=inscripcion,
                                        cancelado = False, fechavence = pago.fecha,tiponivelpago=pago.tipo)

                            rubro.save()
                            #Aplica la promocion a todos  los niveles excepto el 1 que lo aplica en la parte de abajo
                            if matricula.inscripcion.promocion:
                                if  pago.tipo!=0 and matricula.inscripcion.promocion.todos_niveles and DEFAULT_PASSWORD == 'itb' and matricula.nivel.nivelmalla.id != NIVEL_MALLA_UNO:
                                    des = ((100-matricula.inscripcion.descuentoporcent)/100.0)
                                    descuento = round(((rubro.valor * matricula.inscripcion.descuentoporcent)/100),2)
                                    rubro.valor *= des
                                    rubro.save()

                                    desc = Descuento(inscripcion = inscripcion,
                                                                  motivo ='DESCUENTO EN CUOTAS',
                                                                  total = rubro.valor,
                                                                  fecha = datetime.today().date())
                                    desc.save()
                                    detalle = DetalleDescuento(descuento =desc,
                                                                rubro =rubro,
                                                                valor = descuento,
                                                                porcentaje = matricula.inscripcion.descuentoporcent)
                                    detalle.save()

                            # Beca
                            if matricula.becado and pago.tipo!=0:
                                rubro.valor = rubro.valor * pp
                                rubro.save()

                            if pago.tipo==0:
                                rm = RubroMatricula(rubro=rubro, matricula=matricula)
                                rm.save()
                                if HABILITA_DESC_MATRI:
                                    if not inscripcion.carrera.validacionprofesional:
                                        descuento = round(((rubro.valor * DESCUENTO_MATRIC_PORCENT) /100),2)
                                        rubro.valor = rubro.valor - round(((rubro.valor * DESCUENTO_MATRIC_PORCENT) /100),2)
                                        rubro.save()
                                        desc = Descuento(inscripcion = inscripcion,
                                                                  motivo ='DESCUENTO EN MATRICULA',
                                                                  total = rubro.valor,
                                                                  fecha = datetime.today().date())
                                        desc.save()
                                        detalle = DetalleDescuento(descuento =desc,
                                                                    rubro =rubro,
                                                                    valor = descuento,
                                                                    porcentaje = DESCUENTO_MATRIC_PORCENT)
                                        detalle.save()
                            else:
                                # CUOTA MENSUAL
                                rc = RubroCuota(rubro=rubro, matricula=matricula, cuota=pago.tipo)
                                rc.save()

                            rubros.append((rubro.nombre(),rubro.valor,rubro.fechavence.strftime("%d-%m-%Y")))

                    #OCastillo 13-03-2024 se crean los rubros adicionales cargados en el plan de pagos del nivel con la lista previa
                    if matricula.inscripcion.empresaconvenio_id!=ID_CONVENIO_BECA_TECT:
                        for i in lista2:
                            if matricula.nivel.pagonivel_set.filter(tipo=i).exists():
                                 pago = matricula.nivel.pagonivel_set.filter(tipo=i)[:1].get()
                                 if not RubroOtro.objects.filter(matricula=matricula.id,rubro__tiponivelpago=i).exists():
                                     rubro = Rubro(fecha=datetime.today().date(),valor=pago.valor, inscripcion=matricula.inscripcion,
                                                cancelado=False, fechavence=pago.fecha,tiponivelpago=i)
                                     rubro.save()

                                     nombrerubro= TIPOS_PAGO_NIVEL[int(i)][1]
                                     if  TipoOtroRubro.objects.filter(nombre__icontains=nombrerubro).exists():
                                         tipootro=TipoOtroRubro.objects.filter(nombre__icontains=nombrerubro)[:1].get()
                                     else:
                                         tipootro=TipoOtroRubro(nombre=nombrerubro)
                                         tipootro.save()

                                     ruotro=RubroOtro(rubro = rubro,tipo =tipootro, descripcion =str(TIPOS_PAGO_NIVEL[int(i)][1]),matricula=matricula.id)
                                     ruotro.save()
                    else:
                    # OCastillo 03-04-2024 se incluye en este proceso a estudiantes becas del gobierno
                    # solo se aplica para los estudiante que estan becado por becas Tec
                          hoy = datetime.today().date()
                          # buscar el rubro del periodo anterior
                          matriculaant = Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=True).order_by('-fecha')[:1].get()
                          rubroanterior=RubroCuota.objects.filter(matricula=matriculaant).order_by('-id')[:1].get()

                          rubrocuota = Rubro(fecha=datetime.today().date(),
                                               valor=rubroanterior.rubro.valor, inscripcion=matricula.inscripcion,
                                               cancelado=False, fechavence=matricula.nivel.fin)

                          rubrocuota.save()

                          rc = RubroCuota(rubro=rubrocuota, matricula=matricula, cuota=1)
                          rc.save()

                          # actualizamos la matricula actual con la beca que fue acreditada por el gobierno becas tec
                          matricula.becado=True
                          matricula.fechabeca=datetime.now()
                          matricula.tipobeneficio_id=ID_TIPO_BENEFICICO_BECA
                          matricula.tipobeca_id=ID_TIPOBECA
                          matricula.motivobeca_id=ID_MOTIVO_BECA_TEC
                          matricula.porcientobeca=100
                          matricula.save()

                    # preguntar si encontro la solicitud beca
                    if solicitudbeca:
                        tabladescuentobeca=TablaDescuentoBeca.objects.filter(solicitudbeca=solicitudbeca)
                        if crearubro:
                            rcuot = matricula.rubrocuota_set.all()
                            for rc in rcuot:
                                for tbdes in tabladescuentobeca:
                                      if rc.cuota == tbdes.cuota:
                                          tbdes.rubro=rc.rubro
                                          tbdes.save()
                        else:
                             matri= Matricula.objects.filter(inscripcion=inscripcion,nivel__nivelmalla__id=datomatricu.nivel.nivelmalla.id).exclude(id=matricula.id)[:1].get()
                             rcuot = matri.rubrocuota_set.all()


                        if tabladescuentobeca:
                            for rc in rcuot:
                                # Si beca es 100%
                              if not DetalleRubrosBeca.objects.filter(rubro=rc.rubro).exists():
                                  for tbdes in tabladescuentobeca:
                                      if rc.rubro.id == tbdes.rubro.id:
                                        pp = (100-tbdes.descuento)/100.0

                                        if pp==0:
                                            if rc.rubro.puede_eliminarse():
                                                descriprubro=rc.rubro.nombre()
                                                rubro_anterior = rc.rubro.valor
                                                indice_rubro = rc.rubro.id
                                                # indice_rubro = None
                                                rc.rubro.valor *= pp
                                                # descuento= rubro_anterior - rc.rubro.valor
                                                descuento= rubro_anterior
                                                rc.rubro.save()

                                                # OCU grabo los rubros modificados en la tabla de detalle
                                                detalle = DetalleRubrosBeca(matricula=matricula,
                                                           rubro_id = indice_rubro,
                                                           descripcion=descriprubro,
                                                           descuento = descuento,
                                                           porcientobeca = tbdes.descuento,
                                                           valorrubro=rubro_anterior,
                                                           fecha = datetime.now(),
                                                           usuario = request.user)
                                                detalle.save()
                                                rc.rubro.delete()
                                        else:
                                            if rc.rubro.puede_eliminarse():
                                                descriprubro=rc.rubro.nombre()
                                                rubro_anterior = rc.rubro.valor
                                                indice_rubro = rc.rubro.id
                                                rc.rubro.valor *= pp
                                                descuento= rubro_anterior - rc.rubro.valor
                                                rc.rubro.save()

                                                # OCU grabo los rubros modificados en la tabla de detalle
                                                detalle = DetalleRubrosBeca(matricula=matricula,
                                                           rubro_id = indice_rubro,
                                                           descripcion=descriprubro,
                                                           descuento = descuento,
                                                           porcientobeca = tbdes.descuento,
                                                           valorrubro=rubro_anterior,
                                                           fecha = datetime.now(),
                                                           usuario = request.user)
                                                detalle.save()

                        else:
                            for rc in rcuot:
                                # Si beca es 100%
                                if not DetalleRubrosBeca.objects.filter(rubro=rc.rubro).exists():
                                    if pp==0:
                                        if rc.rubro.puede_eliminarse():
                                            descriprubro=rc.rubro.nombre()
                                            rubro_anterior = rc.rubro.valor
                                            indice_rubro = rc.rubro.id
                                            # indice_rubro = None
                                            rc.rubro.valor *= pp
                                            # descuento= rubro_anterior - rc.rubro.valor
                                            descuento= rubro_anterior
                                            rc.rubro.save()

                                            # OCU grabo los rubros modificados en la tabla de detalle
                                            detalle = DetalleRubrosBeca(matricula=matricula,
                                                       rubro_id = indice_rubro,
                                                       descripcion=descriprubro,
                                                       descuento = descuento,
                                                       porcientobeca = matricula.porcientobeca,
                                                       valorrubro=rubro_anterior,
                                                       fecha = datetime.now(),
                                                       usuario = request.user)
                                            detalle.save()
                                            rc.rubro.delete()
                                    else:
                                        if rc.rubro.puede_eliminarse():
                                            descriprubro=rc.rubro.nombre()
                                            rubro_anterior = rc.rubro.valor
                                            indice_rubro = rc.rubro.id
                                            rc.rubro.valor *= pp
                                            descuento= rubro_anterior - rc.rubro.valor
                                            rc.rubro.save()

                                            # OCU grabo los rubros modificados en la tabla de detalle
                                            detalle = DetalleRubrosBeca(matricula=matricula,
                                                       rubro_id = indice_rubro,
                                                       descripcion=descriprubro,
                                                       descuento = descuento,
                                                       porcientobeca = matricula.porcientobeca,
                                                       valorrubro=rubro_anterior,
                                                       fecha = datetime.now(),
                                                       usuario = request.user)
                                            detalle.save()

                            # mail_correosolicitudsecretariaaplica(str('BECA APLICADA POR SECRETARIA'), str(lista[0][0]),request.user, elimina_tildes(solicitudbeca.inscripcion.persona.nombre_completo()),elimina_tildes(solicitudbeca.inscripcion.carrera.nombre),solicitudbeca.inscripcion.persona.emailinst,solicitudbeca)

                    if len(rubros) == 0:
                        matricula.correo_nocronograma()
                    client_address = ip_client_address(request)
                        # Log de ADICIONAR GRADUADO
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(matricula).pk,
                        object_id       = matricula.id,
                        object_repr     = force_str(matricula),
                        action_flag     = ADDITION,
                        change_message  = 'Adicionada Matricula En Linea(' + client_address + ')' )

                    matricula.correo_matricula(rubros)
                    matricula.correo_matricula_online(rubros,request.user)

                    result['result'] = 'ok'
                    transaction.savepoint_commit(sid)
                    return HttpResponse(json.dumps(result), content_type="application/json")
                except Exception as e:
                    result['error'] = str(e)
                    result['result'] ="bad"
                    transaction.savepoint_rollback(sid)
                    return HttpResponse(json.dumps(result), content_type="application/json")

            elif action == 'addsolicitud':
                f = SolicutudMatriculaForm(request.POST)
                try:
                    if f.is_valid():
                         solicitud = SolicitudSecretariaDocente(persona=request.session['persona'],
                                                                   tipo_id=17,
                                                                   descripcion=f.cleaned_data['observaciones'],
                                                                   fecha = datetime.now(),
                                                                   hora = datetime.now().time(),
                                                                   cerrada = False)
                         solicitud.save()
                         correo=''
                         if EMAIL_ACTIVE:
                            # f.instance.mail_subject_nuevo()
                            #OCastillo 17-05-2019
                            gruposexcluidos = [SISTEMAS_GROUP_ID]
                            lista=''

                            lista = str(solicitud.persona.email)
                            hoy = datetime.now().today()
                            contenido = "Nueva Solicitud "
                            descripcion = "Estimado/a estudiante. Su solicitud ha sido recibida. Sera asignada al Departamento correspondiente. Puede ver el estado de la misma en el Sistema."
                            send_html_mail(contenido,
                                "emails/nuevasolicitud.html", {'d': solicitud, 'fecha': hoy,'contenido': contenido,'descripcion':descripcion,'opcion':'1'},lista.split(','))
                            inscripcion = Inscripcion.objects.filter(persona=request.session['persona'])[:1].get()
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
                                if SolicitudesGrupo.objects.filter(tiposolic_id=17,todas_carreras=True).exists():
                                    grupo=SolicitudesGrupo.objects.filter(tiposolic=17,todas_carreras=True).values('grupo')
                                    if ModuloGrupo.objects.filter(grupos__in=grupo).exists():
                                        correo_solicitud=[]
                                        for correo_grupo in ModuloGrupo.objects.filter(grupos__in=grupo):
                                            correo_solicitud.append(correo_grupo.correo)
                                            if correo:
                                                correo = correo+','+correo_grupo.correo
                                            else:
                                                correo = correo_grupo.correo

                            hoy = datetime.now().today()
                            contenido = "Nueva Solicitud - Proceso de Matricula"
                            # descripcion = solicitud.descripcion
                            # if adjunto:
                            #      descripcion = descripcion +   " Archivo adjunto"
                            #     # descripcion = solicitud.descripcion +  "Estudiante ha realizado solicitud. Revisar el detalle de la misma en el Modulo Solicitudes de Alumnos. Archivo adjunto"
                            send_html_mail(contenido,
                                "emails/nuevasolicitud.html", {'d': solicitud, 'fecha': hoy,'contenido': contenido,'adjunto':False,'opcion':'2'},lista.split(','))
                         return  HttpResponseRedirect("/alu_matricula?info=SOLICITUD ENVIADA CORRECTAMENTE")
                except Exception as e:
                    return  HttpResponseRedirect("/alu_matricula?info=OCURRIO UN ERROR INTENTE NUEVAMENTE")
            elif action == 'consultanivel':
                materias=[]
                materiaspendientes=[]
                result={}
                try:
                    inscripcion = Inscripcion.objects.filter(pk=request.POST['inscripcion'])[:1].get()
                    nivel = Nivel.objects.filter(pk=request.POST['idnivel'])[:1].get()

                    if  nivel.mat_nivel() >= nivel.capacidadmatricula :
                        result['result'] ="bad"
                        result['error'] = 'NOY HA CUPO DISPONIBLE PARA MATRICULARSE'
                        return HttpResponse(json.dumps(result), content_type="application/json")
                    for m in nivel.materia_set.filter(Q(cerrado=False)|Q(cerrado=None)):
                        pendientes = inscripcion.recordacademico_set.filter(asignatura__in=m.asignatura.precedencia.all(),aprobada=True)
                        if pendientes.count()== m.asignatura.precedencia.all().count():
                             if m.asignatura.titulacion:
                                if not RecordAcademico.objects.filter(aprobada=False).exists():
                                    materias.append({'id':m.id, 'nombre':m.asignatura.nombre })
                                else:
                                    materiaspendientes.append({'id':m.id, 'nombre':m.asignatura.nombre })
                             else:
                                    materias.append({'id':m.id, 'nombre':m.asignatura.nombre })
                        else:
                             materiaspendientes.append({'id':m.id, 'nombre':m.asignatura.nombre })
                    result['result'] ="ok"
                    result['materiaspendientes'] = materiaspendientes
                    result['materias'] =materias
                    return HttpResponse(json.dumps(result), content_type="application/json")
                    # else:
                    #     result['result'] ="bad"
                    #     result['error'] ='NOY HA CUPO DISPONIBLE PARA MATRICULARSE'
                    #     return HttpResponse(json.dumps(result), content_type="application/json")
                except Exception as e:
                    result['result'] ="bad"
                    result['error'] =str(e)
                    return HttpResponse(json.dumps(result), content_type="application/json")

        else:
            data={'title':'Matricula'}
            addUserData(request,data)
            if Inscripcion.objects.filter(persona__usuario=request.user).exists():
                inscripcion = Inscripcion.objects.filter(persona__usuario=request.user)[:1].get()
                if  not inscripcion.tiene_deuda_matricula():
                    materias=[]
                    materiaspendientes=[]
                    if inscripcion.matricula():
                        return  HttpResponseRedirect('/?info=Ud. ya se encuentra matriculado ')
                    else:
                        hoy = datetime.now().date()
                        grupo = inscripcion.grupo()
                        nivelliberado = Matricula.objects.filter(inscripcion=inscripcion,liberada=True).values('nivel')
                        if Nivel.objects.filter(cerrado=False,fechatopematriculaex__gte=hoy,grupo=grupo).exclude(nivelmalla__id=NIVEL_MALLA_UNO).exclude(id__in=nivelliberado).exists():
                            nivel = Nivel.objects.filter(cerrado=False,fechatopematriculaex__gte=hoy,grupo=grupo)[:1].get()
                            if nivel.nivelmalla.id == NIVEL_SEMINARIO:
                                return  HttpResponseRedirect('/')
                            #OCastillo 15-02-2023 para nivel graduacion y carrera optometria
                            #OCastillo 05-04-2023 para nivel graduacion y todas las carreras
                            # if nivel.nivelmalla.id == NIVEL_GRADUACION and inscripcion.carrera.id==48:
                            if nivel.nivelmalla.id == NIVEL_GRADUACION:
                                # return  HttpResponseRedirect('/')
                                return  HttpResponseRedirect('/?info=DEBE VERIFICAR CON SECRETARIA QUE CUMPLA LOS REQUISITOS PARA MATRICULA NIVEL GRADUACION')
                            if  nivel.mat_nivel() >= nivel.capacidadmatricula :
                                return  HttpResponseRedirect('/?info=NOY HA CUPO DISPONIBLE PARA MATRICULARSE')
                            a = AsignaturaMalla.objects.filter(malla=nivel.malla,asignatura__promedia=True,nivelmalla__orden__lt=nivel.nivelmalla.orden).exclude(nivelmalla__id=NIVEL_MALLA_CERO).distinct('asignatura').values('asignatura')
                            record=RecordAcademico.objects.filter(inscripcion=inscripcion,aprobada=True,asignatura__id__in=a,nota__gte=NOTA_PARA_APROBAR).distinct('asignatura').values('asignatura').count()
                            print(record)
                            print(len(a))
                            if record < len(a):
                                msj=''
                                reprobada= RecordAcademico.objects.filter(inscripcion=inscripcion,asignatura__promedia=True,nota__lt=NOTA_PARA_APROBAR,asignatura__id__in=a).distinct('asignatura').count()
                                print(reprobada)
                                if reprobada <=2  :
                                    msj = 'Estudiante debe contactar con su coordinacion para que autoricen su matricula'

                                elif reprobada > 2:
                                    msj='NO SE PUEDE MATRICULAR POR TENER '+ str(reprobada)+ ' MATERIAS REPROBADAS'
                                return  HttpResponseRedirect('/?info='+msj)
                            for m in nivel.materia_set.filter(Q(cerrado=False)|Q(cerrado=None)):
                                pendientes = inscripcion.recordacademico_set.filter(asignatura__in=m.asignatura.precedencia.all(),aprobada=True)

                                if pendientes.count()== m.asignatura.precedencia.all().count():
                                     if m.asignatura.titulacion:
                                        if not RecordAcademico.objects.filter(aprobada=False).exists():
                                            materias.append(m)
                                     else:
                                        materias.append(m)
                                else:
                                     materiaspendientes.append(m)
                            if not materias:
                                return  HttpResponseRedirect('/?info=NO HAY MATERIAS DISPONIBLES PARA MATRICULARSE')
                            data['materias'] = materias
                            data['materiaspendientes'] = materiaspendientes
                            data['nivel']=nivel
                            data['inscripcion']=inscripcion
                        else:
                            return  HttpResponseRedirect('/?info=NO HAY NIVEL DISPONIBLE PARA MATRICULARSE')
                        data['form'] = SolicutudMatriculaForm()
                        if 'info' in request.GET:
                            data['info'] = request.GET['info']

                    return render(request ,"alu_matricula/menu.html" ,  data)
                return HttpResponseRedirect('/?info=ESTUDIANTE TIENE DEUDA  NO SE PUEDE MATRICULAR')
            return  HttpResponseRedirect('/?info=MODULO SOLO DISPONIBLE PARA ALUMNOS')
    except Exception as ex:
        return  HttpResponseRedirect('/?info='+str(ex))
