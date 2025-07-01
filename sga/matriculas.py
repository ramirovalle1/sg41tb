from datetime import datetime, timedelta
from datetime import datetime, timedelta
from decimal import Decimal
import json
import os
from django.contrib.admin.models import LogEntry, ADDITION, DELETION, CHANGE
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.db.transaction import rollback
from django.forms.models import model_to_dict
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template.context import RequestContext
from django.utils.encoding import force_str
import xlrd
import xlwt
from decorators import secure_module
from settings import UTILIZA_GRUPOS_ALUMNOS, GENERAR_RUBROS_PAGO, TIPO_OTRO_RUBRO, TIPO_DERECHOEXAMEN_RUBRO, \
    VALOR_DERECHOEXAMEN_RUBRO, GENERAR_RUBRO_DERECHO, \
    NOTA_PARA_APROBAR, TIPO_AYUDA_FINANCIERA, MODULO_FINANZAS_ACTIVO, EMAIL_ACTIVE, UTILIZA_NIVEL0_PROPEDEUTICO, \
    MODELO_EVALUACION, EVALUACION_TES, TIPO_MORA_RUBRO, \
    UTILIZA_MATRICULA_RECARGO, UTILIZA_FICHA_MEDICA, TIPO_BECA_SENESCYT, EVALUACION_ITS, EVALUACION_IGAD, \
    EVALUACION_ITB, EVALUACION_IAVQ, NIVEL_MALLA_UNO, NUMERO_POSIBLE_DESERTOR, \
    MODELO_EVALUACION, EVALUACION_CASADE, NIVEL_MALLA_CERO, DEFAULT_PASSWORD, VALIDA_MATERIA_APROBADA, NIVEL_SEMINARIO, \
    ASIST_PARA_APROBAR, VALIDA_PRECEDENCIA, MEDIA_ROOT, \
    TIPO_OBSERVACION_CRITICA_ID, NOTA_PARA_SUPLET, NOTA_ESTADO_SUPLETORIO, ID_FUNDACION_CRISFE, LISTA_TIPO_BECA, \
    LISTA_GRUPO_MUNICIPO, EXCLUIR_TIPO_PAGO, \
    HABILITA_DESC_MATRI, DESCUENTO_MATRIC_PORCENT, SITE_ROOT, ID_GESTION_SECRETARIA, ID_GESTION_ANALSIS, \
    ID_TIPO_SOLICITUD_BECA, TIPO_RUBRO_CREDENCIAL, NIVEL_GRADUACION, ID_CONVENIO_BECA_TECT, \
    GENERAR_RUBRO_INSCRIPCION_MARGEN_DIAS, ID_TIPO_BENEFICICO_BECA, ID_TIPOBECA, ID_MOTIVO_BECA_TEC, \
    TIPO_RUBRO_MATERIALAPOYO, VALOR_MATERIALAPOYO
from sga.commonviews import addUserData, ip_client_address
from sga.forms import MatriculaForm, MatriculaEditForm, RetiradoMatriculaForm, MatriculaMultipleForm, MatriculaBecaForm, MatriculaProxNivelForm, \
     MatriculaLibreForm, MatriculaExtraForm, EliminacionMatriculaForm,ObservacionMatriculaForm,BecaParcialForm,DetalleDescuentoForm, RubrosCambioProgramacionForm, \
     MotivoLiberadaForm,CargaMasivaGraduacionForm
from sga.models import Nivel, Carrera, Sede, Matricula, MateriaAsignada, RecordAcademico, Materia, Leccion, AsistenciaLeccion, RetiradoMatricula, \
    Asignatura, Inscripcion, Rubro, RubroMatricula, HistoricoRecordAcademico, RubroCuota, RubroOtro, TipoOtroRubro, TipoBeneficio, Coordinacion,\
    AsignaturaMalla, NivelMalla, EstudiantesXDesertar, EliminacionMatricula, RubroEspecieValorada, DetalleRetiradoMatricula,Periodo,Egresado,Graduado,\
    ObservacionMatricula, InscripcionDescuentoRef, ReferidosInscripcion,DescuentoReferido,DetalleRubrosBeca,TipoBeca,MotivoBeca,MateriaNivel, elimina_tildes,\
    ObservacionInscripcion, Persona, PreInscripcion, DatosPersonaCongresoIns, TipoIncidencia, PagoNivel, Descuento, DetalleDescuento,SolicitudBeca,\
    PersonAutorizaBecaAyuda,HistorialGestionBeca,DetalleEliminaMatricula,TablaDescuentoBeca,HistoricoNotasITB,HistorialGestionAyudaEconomica, \
    AsistenteDepartamento, ExamenConvalidacionIngreso,RubroOtro, TIPOS_PAGO_NIVEL, MatriculaLiberada, Grupo,RubroInscripcion, ArchivoExcelBecadosMunicipio, \
    InscripcionesCAB, CuotaCAB, InscripcionGrupo,ArchivoRubroOtroMasivos, InscripcionTestIngreso
from django.db import transaction


from sga.tasks import gen_passwd, send_html_mail

def mail_cargarubrosenlote(user,listadoerror,listadocorrecto,cantvalidos,cantinvalidos,tipotrorubro):
        if listadoerror!='ELIMINADO':
            op='2'
            tipo = TipoIncidencia.objects.get(pk=72)
            # tipo = TipoIncidencia.objects.get(pk=70)
            hoy = datetime.now()
            contenido = "NOTIFICACION - CARGA MASIVA DE RUBROS"

            send_html_mail("GENERADO RUBRO EN FINANZAS ",
                    "emails/rubrosmasivos.html", {'fecha':hoy,'contenido':contenido,'listadoerror':listadoerror,'listadocorrecto':listadocorrecto,'validos':cantvalidos,'invalidos':cantinvalidos,'usuario':user,'tipotrorubro':tipotrorubro,'op':op},tipo.correo.split(","))
        else:
            #ojo para el mantenimiento opcion eliminar
            op='3'
            tipo = TipoIncidencia.objects.get(pk=72)
            hoy = datetime.now()
            contenido = "NOTIFICACION - CARGA MASIVA DE RUBROS ELIMINADO"

            send_html_mail("RUBRO MASIVO ELIMINADO ",
                    "emails/rubrosmasivos.html", {'fecha':hoy,'contenido':contenido,'listadoerror':listadoerror,'listadocorrecto':listadocorrecto,'validos':cantvalidos,'invalidos':cantinvalidos,'usuario':user,'tipotrorubro':tipotrorubro,'op':op},tipo.correo.split(","))


def convertir_fecha(s):
    return datetime(int(s[6:10]), int(s[3:5]), int(s[0:2]))


@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
@transaction.atomic()
def view(request):

    if request.method=='POST':
        try:
            if 'action' in request.POST:
                action = request.POST['action']
                if action=='addmatriculalibre':
                    f = MatriculaLibreForm(request.POST)
                    if f.is_valid():
                        nivel = Nivel.objects.get(pk=request.POST['nivel'])
                        inscripcion = Inscripcion.objects.get(pk=request.POST['inscripcion_id'])
                        # if inscripcion.carrera.validacionprofesional:
                        #     if not ExamenConvalidacionIngreso.objects.filter(inscripcion=inscripcion,aprobada=True).exists():
                        #         return HttpResponseRedirect('/matriculas?action=addmatriculalibre&id='+str(nivel.id)+'&error=4')

                        if not inscripcion.tiene_deuda_matricula():
                            if not inscripcion.matriculado():

                                matricula = Matricula(inscripcion=inscripcion,
                                                        nivel=nivel,
                                                        pago=False,
                                                        iece=False,
                                                        becado=False,
                                                        porcientobeca=0)
                                matricula.save()

                                for m in request.POST.getlist('ins'):
                                    materia = Materia.objects.get(pk=int(m))
                                    asignatura = materia.asignatura
                                    if not inscripcion.ya_aprobada(asignatura):
                                        # Si no la tiene aprobada aun
                                        pendientes = inscripcion.recordacademico_set.filter(asignatura__in=asignatura.precedencia.all(),aprobada=False)
                                        if pendientes.count()==0:
                                            asign = MateriaAsignada(matricula=matricula,materia=materia,notafinal=0,asistenciafinal=0,supletorio=0)
                                            asign.save()

                                            # Correccion de Lecciones ya impartidas
                                            leccionesYaDadas = Leccion.objects.filter(clase__materia=asign.materia)
                                            for leccion in leccionesYaDadas:
                                                asistenciaLeccion = AsistenciaLeccion(leccion=leccion,matricula=matricula,asistio=False)
                                                asistenciaLeccion.save()
                                        else:
                                            recordPendiente = RecordAcademico(inscripcion=inscripcion,asignatura=asignatura,nota=0,asistencia=0,fecha=datetime.now(),convalidacion=False,aprobada=False,pendiente=True)
                                            recordPendiente.save()

                                matricula.recalcular_rubros_segun_creditos()

                                # buscar si existe matricula en el mismo nivel para no crear los rubros
                                crearubro=True
                                datomatricu=None
                                #listmatricula = Matricula.objects.filter(inscripcion=inscripcion).exclude(id=matricula.id)
                                #OCastillo 01-03-2021 verificar matricula de niveles abiertos
                                listmatricula = Matricula.objects.filter(inscripcion=inscripcion,nivel__cerrado=False).exclude(id=matricula.id)

                                #OCastillo 01-03-2021 si tiene reingtegro variable crea rubro en true
                                if RetiradoMatricula.objects.filter(inscripcion=inscripcion,activo=True).exists():
                                   retirado =RetiradoMatricula.objects.filter(inscripcion=inscripcion,activo=True)[:1].get()
                                   if DetalleRetiradoMatricula.objects.filter(retirado=retirado,estado='REINTEGRO').order_by('-id').exists():
                                        crearubro=True
                                else:
                                    if len(listmatricula)>0:
                                        for matri in listmatricula:
                                            if matri.nivel.nivelmalla.id==nivel.nivelmalla.id:
                                                crearubro=False
                                                datomatricu=matri
                                                break


                                # buscar
                                solicitudbeca=None
                                if SolicitudBeca.objects.filter(inscripcion=inscripcion,nivel__nivelmalla__id=nivel.nivelmalla.id,tiposolicitud=1).order_by('-fecha').exists():
                                     if SolicitudBeca.objects.filter(inscripcion=inscripcion,nivel__nivelmalla__id=nivel.nivelmalla.id,tiposolicitud=1,aprobado=True,aprobacionestudiante=True,asignaciontarficadescuento=True).order_by('-fecha').exists():
                                        solicitudbeca = SolicitudBeca.objects.filter(inscripcion=inscripcion,nivel__nivelmalla__id=nivel.nivelmalla.id,tiposolicitud=1,aprobado=True,aprobacionestudiante=True).order_by('-fecha')[:1].get()
                                     else:
                                         if SolicitudBeca.objects.filter(inscripcion=inscripcion,nivel__nivelmalla__id=nivel.nivelmalla.id,tiposolicitud=2,aprobado=True,aprobacionestudiante=True,asignaciontarficadescuento=True).order_by('-fecha').exists():
                                            solicitudbeca = SolicitudBeca.objects.filter(inscripcion=inscripcion,nivel__nivelmalla__id=nivel.nivelmalla.id,tiposolicitud=2,aprobado=True,aprobacionestudiante=True).order_by('-fecha')[:1].get()

                                if solicitudbeca:
                                    # si el estado de la solicitud ya fue aprobado y aplicada por secretaria
                                    if solicitudbeca.estadosolicitud==7:
                                        if datomatricu:
                                            matricula.becado=True
                                            matricula.tipobeneficio=datomatricu.tipobeneficio
                                            matricula.tipobeca=datomatricu.tipobeca
                                            matricula.motivobeca=datomatricu.motivobeca
                                            matricula.porcientobeca=datomatricu.porcientobeca
                                            matricula.fechabeca=datomatricu.fechabeca

                                            matricula.save()


                                if solicitudbeca:
                                    rcuot = matricula.rubrocuota_set.all()
                                    tabladescuentobeca=TablaDescuentoBeca.objects.filter(solicitudbeca=solicitudbeca)
                                    # actualizar la tabla de descuento por lo nuevos rubros
                                    if crearubro:
                                        for rc in rcuot:
                                            for tbdes in tabladescuentobeca:
                                                  if rc.cuota == tbdes.cuota:
                                                      tbdes.rubro=rc.rubro
                                                      tbdes.save()

                                    solicitudbeca.nivel=nivel
                                    solicitudbeca.save()

                                #OC 07-febrero-2019 enviar correo a soporte cuando la matricula es en el primer nivel
                                if EMAIL_ACTIVE:
                                    if nivel.nivelmalla.id == NIVEL_MALLA_UNO and DEFAULT_PASSWORD == 'itb':
                                        esmunicipio=False
                                        grupomunicipio =Grupo.objects.filter(id__in=LISTA_GRUPO_MUNICIPO)

                                        hoy = datetime.now().today()
                                        estudiante= elimina_tildes(inscripcion.persona.nombre_completo_inverso())
                                        nivel_matri=nivel.nivelmalla.nombre
                                        carrera=nivel.carrera.nombre
                                        grupo=nivel.paralelo
                                        personarespon = Persona.objects.filter(usuario=request.user)[:1].get()

                                        # correo= ('ocastillo@bolivariano.edu.ec')
                                        correo_inst=str(inscripcion.persona.emailinst)
                                        op='1'

                                        for grup in grupomunicipio:
                                            if nivel.grupo_id==grup.id:
                                                esmunicipio=True
                                                break

                                        if esmunicipio:
                                            if TipoIncidencia.objects.filter(pk=68).exists():
                                                tipo = TipoIncidencia.objects.filter(pk=68)[:1].get()
                                                correo = tipo.correo

                                            send_html_mail("ESTUDIANTE MATRICULADO A " +nivel_matri+" "+"BECA MUNICIPIO",
                                            "emails/correo_matricula_primernivel.html", {'contenido': "ESTUDIANTE MATRICULADO A "+nivel_matri+" "+"BECA MUNICIPIO",'op':op, 'estudiante': estudiante, 'nivel': nivel_matri,'grupo':grupo,'correo_inst':correo_inst,'personarespon': personarespon, 'fecha': hoy,'carrera':carrera},correo.split(','))
                                        else:
                                            correo= str('soporteitb@bolivariano.edu.ec')

                                            send_html_mail("ESTUDIANTE MATRICULADO A PRIMER NIVEL",
                                            "emails/correo_matricula_primernivel.html", {'contenido': "ESTUDIANTE MATRICULADO A PRIMER NIVEL",'op':op, 'estudiante': estudiante, 'nivel': nivel_matri,'grupo':grupo,'correo_inst':correo_inst,'personarespon': personarespon, 'fecha': hoy,'carrera':carrera},correo.split(','))
                                    else:
                                        esmunicipio=False
                                        grupomunicipio =Grupo.objects.filter(id__in=LISTA_GRUPO_MUNICIPO)

                                        for grup in grupomunicipio:
                                            if nivel.grupo_id==grup.id:
                                                esmunicipio=True
                                                break
                                        if esmunicipio:
                                             hoy = datetime.now().today()
                                             estudiante= elimina_tildes(inscripcion.persona.nombre_completo_inverso())
                                             nivel_matri=nivel.nivelmalla.nombre
                                             carrera=nivel.carrera.nombre
                                             grupo=nivel.paralelo
                                             personarespon = Persona.objects.filter(usuario=request.user)[:1].get()
                                             correo_inst=str(inscripcion.persona.emailinst)
                                             if TipoIncidencia.objects.filter(pk=68).exists():
                                                tipo = TipoIncidencia.objects.filter(pk=68)[:1].get()
                                                correo = tipo.correo

                                             send_html_mail("ESTUDIANTE MATRICULADO A "+nivel_matri+" "+"BECA MUNICIPIO" ,
                                            "emails/correo_matricula_municipio.html", {'contenido': "ESTUDIANTE MATRICULADO A "+nivel_matri+" "+"BECA MUNICIPIO", 'estudiante': estudiante, 'nivel': nivel_matri,'grupo':grupo,'correo_inst':correo_inst,'personarespon': personarespon, 'fecha': hoy,'carrera':carrera},correo.split(','))

                                return HttpResponseRedirect('/matriculas?action=matricula&id='+str(nivel.id))
                            else:
                                nivel = Nivel.objects.get(pk=request.POST['nivel'])
                                return HttpResponseRedirect('/matriculas?action=addmatriculalibre&id='+str(nivel.id)+'&error=1')
                        else:
                            nivel = Nivel.objects.get(pk=request.POST['nivel'])
                            return HttpResponseRedirect('/matriculas?action=addmatriculalibre&id='+str(nivel.id)+'&error=2')
                    else:
                        nivel = Nivel.objects.get(pk=request.POST['nivel'])
                        return HttpResponseRedirect('/matriculas?action=addmatriculalibre&id='+str(nivel.id)+'&error=1')
                elif action=='checkmat':
                    inscripcion = Inscripcion.objects.get(pk=request.POST['iid'])
                    data = {}
                    if inscripcion.matricula():
                        data['result'] = 'ok'
                        matricula = inscripcion.matricula() #inscripcion.matricula_periodo(request.session['periodo'])
                        if matricula:
                            data['matricula'] = str(matricula.nivel)
                            data['periodo'] = matricula.nivel.periodo.nombre
                            data['cantidadmaterias'] = matricula.materiaasignada_set.count()
                        else:
                            data['result'] = "bad"
                    else:
                        data['result'] = 'bad'
                        data['plan12'] = inscripcion.plan12activo()
                        if data['plan12']:
                            plan = inscripcion.plan12activo_obj()
                            data['cupoplan12'] = plan.materiastotales - plan.materiascursadas
                    return HttpResponse(json.dumps(data),content_type="application/json")

                elif action=='filtrarmaterias':
                    inscripcion = Inscripcion.objects.get(pk=request.POST['idi'])
                    carrera = inscripcion.carrera
                    asignaturas = AsignaturaMalla.objects.filter(malla__carrera=carrera)
                    data = {"result":"ok", 'filtromaterias': [x.asignatura.id for x in asignaturas]}
                    return HttpResponse(json.dumps(data),content_type="application/json")


                elif action=='addmatriculamulti':
                    form = MatriculaMultipleForm(request.POST)
                    f = form
                    alumnos_correo=[]
                    #OCastillo 27-04-2023 se crea una lista con los rubros adicionales que no son matricula ni cuotas
                    lista2=[]
                    for pn in TIPOS_PAGO_NIVEL:
                        if not 'CUOTA' in pn[1] and not  'MATRICULA' in pn[1] :
                            lista2.append(pn[0])

                    if f.is_valid():
                        nivel_actual=Nivel.objects.filter(pk=f.cleaned_data['nivel'].id)[:1].get()
                        nivel_matri=nivel_actual.nivelmalla.nombre
                        grupo=nivel_actual.paralelo
                        carrera=nivel_actual.carrera.nombre
                        for inscripcion_id in request.POST.getlist('ins'):
                            inscripcion = Inscripcion.objects.get(pk=int(inscripcion_id))
                            # b=1
                            # if inscripcion.carrera.validacionprofesional:
                            #     if not ExamenConvalidacionIngreso.objects.filter(inscripcion=inscripcion,aprobada=True).exists():
                            #         b=0
                            if not Matricula.objects.filter(nivel=nivel_actual,inscripcion=inscripcion).exists():
                                if not inscripcion.tiene_deuda_matricula() :
                                    if not inscripcion.matriculado():
                                        matricula = Matricula(inscripcion=inscripcion,
                                                        nivel=f.cleaned_data['nivel'],
                                                        pago=f.cleaned_data['pago'],
                                                        iece=f.cleaned_data['iece'],
                                                        becado=False,
                                                        porcientobeca=0)

                                        matricula.save()
                                        if inscripcion.tienediscapacidad and EMAIL_ACTIVE:
                                            matricula.nivel.mail_matricula_discapacidad(inscripcion)

                                        #Obtain client ip address
                                        client_address = ip_client_address(request)

                                        # Log de ADICIONAR MATRICULAS MULTIPLES
                                        LogEntry.objects.log_action(
                                            user_id         = request.user.pk,
                                            content_type_id = ContentType.objects.get_for_model(matricula).pk,
                                            object_id       = matricula.id,
                                            object_repr     = force_str(matricula),
                                            action_flag     = ADDITION,
                                            change_message  = 'Adicionada Matricula Multiple (' + client_address + ')'  )

                                        nivel = matricula.nivel
                                        materias = nivel.materia_set.filter(Q(cerrado=False)|Q(cerrado=None))
                                        inscripcion = matricula.inscripcion

                                        alumnos_correo.append((elimina_tildes(matricula.inscripcion.persona.nombre_completo_inverso()),matricula.inscripcion.persona.emailinst))
                                        #Actualizar el registro de InscripcionMalla con la malla correspondiente
                                        im = inscripcion.malla_inscripcion()
                                        im.malla = matricula.nivel.malla
                                        im.save()

                                        # buscar si existe matricula en el mismo nivel para no crear los rubros
                                        crearubro=True
                                        datomatricu=None
                                        #listmatricula = Matricula.objects.filter(inscripcion=inscripcion).exclude(id=matricula.id)
                                        #OCastillo 01-03-2021 verificar matricula de niveles abiertos
                                        listmatricula = Matricula.objects.filter(inscripcion=inscripcion,nivel__cerrado=False).exclude(id=matricula.id)

                                        #OCastillo 01-03-2021 si tiene reingtegro variable crea rubro en true
                                        if RetiradoMatricula.objects.filter(inscripcion=inscripcion,activo=True).exists():
                                           retirado =RetiradoMatricula.objects.filter(inscripcion=inscripcion,activo=True)[:1].get()
                                           if DetalleRetiradoMatricula.objects.filter(retirado=retirado,estado='REINTEGRO').order_by('-id').exists():
                                                crearubro=True
                                        else:
                                            if len(listmatricula)>0:
                                                for matri in listmatricula:
                                                    if matri.nivel.nivelmalla.id==nivel.nivelmalla.id:
                                                        crearubro=False
                                                        datomatricu=matri
                                                        break

                                        # buscar
                                        solicitudbeca=None
                                        if SolicitudBeca.objects.filter(inscripcion=inscripcion,nivel__nivelmalla__id=nivel.nivelmalla.id,tiposolicitud=1).order_by('-fecha').exists():
                                             if SolicitudBeca.objects.filter(inscripcion=inscripcion,nivel__nivelmalla__id=nivel.nivelmalla.id,tiposolicitud=1,aprobado=True,aprobacionestudiante=True,asignaciontarficadescuento=True).order_by('-fecha').exists():
                                                solicitudbeca = SolicitudBeca.objects.filter(inscripcion=inscripcion,nivel__nivelmalla__id=nivel.nivelmalla.id,tiposolicitud=1,aprobado=True,aprobacionestudiante=True).order_by('-fecha')[:1].get()
                                             else:
                                                 if SolicitudBeca.objects.filter(inscripcion=inscripcion,nivel__nivelmalla__id=nivel.nivelmalla.id,tiposolicitud=2,aprobado=True,aprobacionestudiante=True,asignaciontarficadescuento=True).order_by('-fecha').exists():
                                                    solicitudbeca = SolicitudBeca.objects.filter(inscripcion=inscripcion,nivel__nivelmalla__id=nivel.nivelmalla.id,tiposolicitud=2,aprobado=True,aprobacionestudiante=True).order_by('-fecha')[:1].get()

                                        if solicitudbeca:
                                            # si el estado de la solicitud ya fue aprobado y aplicada por secretaria
                                            if datomatricu:
                                                if solicitudbeca.estadosolicitud==7:
                                                    matricula.becado=True
                                                    matricula.tipobeneficio=datomatricu.tipobeneficio
                                                    matricula.tipobeca=datomatricu.tipobeca
                                                    matricula.motivobeca=datomatricu.motivobeca
                                                    matricula.porcientobeca=datomatricu.porcientobeca
                                                    matricula.fechabeca=datomatricu.fechabeca
                                                    matricula.observaciones=datomatricu.observaciones

                                                    matricula.save()

                                        # Materias Asignadas
                                        if not 'CONGRESO' in nivel.carrera.nombre:
                                            for materia in materias:
                                                asignatura = materia.asignatura
                                                if not inscripcion.ya_aprobada(asignatura):
                                                    # Si no la tiene aprobada aun
                                                    pendientes = inscripcion.recordacademico_set.filter(asignatura__in=asignatura.precedencia.all(),aprobada=False)
                                                    if pendientes.count()==0:
                                                        asign = MateriaAsignada(matricula=matricula,materia=materia,notafinal=0,asistenciafinal=0,supletorio=0)
                                                        asign.save()

                                                        # Correccion de Lecciones ya impartidas
                                                        leccionesYaDadas = Leccion.objects.filter(clase__materia=asign.materia)
                                                        for leccion in leccionesYaDadas:
                                                            asistenciaLeccion = AsistenciaLeccion(leccion=leccion,matricula=matricula,asistio=False)
                                                            asistenciaLeccion.save()
                                                    else:
                                                        recordPendiente = RecordAcademico(inscripcion=inscripcion,asignatura=asignatura,nota=0,asistencia=0,fecha=datetime.now(),convalidacion=False,aprobada=False,pendiente=True)
                                                        recordPendiente.save()

                                            for materia in MateriaNivel.objects.filter(nivel=nivel):
                                                if datetime.now().date() <= materia.materia.inicio + timedelta(days =5):

                                                    asignatura = materia.materia.asignatura
                                                    if not inscripcion.ya_aprobada(asignatura):
                                                        # Si no la tiene aprobada aun
                                                        pendientes = inscripcion.recordacademico_set.filter(asignatura__in=asignatura.precedencia.all(),aprobada=False)
                                                        if pendientes.count()==0:
                                                            if not MateriaAsignada.objects.filter(materia__asignatura=materia.materia.asignatura,matricula=matricula).exists():
                                                                asign = MateriaAsignada(matricula=matricula,materia=materia.materia,notafinal=0,asistenciafinal=0,supletorio=0)
                                                                asign.save()

                                                            # Correccion de Lecciones ya impartidas
                                                            leccionesYaDadas = Leccion.objects.filter(clase__materia=asign.materia)
                                                            for leccion in leccionesYaDadas:
                                                                asistenciaLeccion = AsistenciaLeccion(leccion=leccion,matricula=matricula,asistio=False)
                                                                asistenciaLeccion.save()
                                                        else:
                                                            if not  RecordAcademico.objects.filter(inscripcion=inscripcion,asignatura=asignatura).exists():
                                                                recordPendiente = RecordAcademico(inscripcion=inscripcion,asignatura=asignatura,nota=0,asistencia=0,fecha=datetime.now(),convalidacion=False,aprobada=False,pendiente=True)
                                                                recordPendiente.save()
                                        sec = 1
                                        # Crear Rubro
                                        if GENERAR_RUBROS_PAGO and not inscripcion.beca_senescyt().tienebeca:
                                             if matricula.inscripcion.empresaconvenio_id!=ID_CONVENIO_BECA_TECT:
                                                if crearubro:
                                                    pp = 1.0 if not matricula.becado else ((100-matricula.porcientobeca)/100.0)

                                                    #OCastillo 27-04-2023 se excluyen los rubros adicionales de la lista previa para no usar ids
                                                    # for pago in nivel.pagonivel_set.all().exclude(tipo__in=[13,14,15,16,17]):
                                                    for pago in nivel.pagonivel_set.all().exclude(tipo__in=lista2):
                                                        if pago.tipo==0 or (pago.tipo>0 and pp>0):
                                                            rubro = Rubro(fecha=datetime.today().date(),
                                                                        valor = pago.valor, inscripcion=inscripcion,
                                                                        cancelado = False, fechavence = pago.fecha,tiponivelpago=pago.tipo)
                                                            rubro.save()

                                                            if InscripcionesCAB.objects.filter(inscripcion=inscripcion, estado=True).exists() and inscripcion.cab:
                                                                cab = InscripcionesCAB.objects.filter(inscripcion=inscripcion, estado=True).order_by('-id')[:1].get()
                                                                cuota_cab = CuotaCAB(descripcion='CUOTA CAB #'+str(sec),
                                                                                     rubro=rubro,
                                                                                     inscripcioncab=cab,
                                                                                     fechavence=rubro.fechavence,
                                                                                     valor=cab.monto,
                                                                                     nivel=matricula.nivel)
                                                                cuota_cab.save()
                                                                sec = sec + 1

                                                            #Aplica la promocion a todos  los niveles excepto el 1 que lo aplica en la parte de abajo
                                                            if matricula.inscripcion.promocion:
                                                                if pago.tipo!=0 and matricula.inscripcion.promocion.todos_niveles and DEFAULT_PASSWORD == 'itb' and matricula.nivel.nivelmalla.id != NIVEL_MALLA_UNO:
                                                                    #OCastillo 20-04-2023 para el caso de todos los niveles asi este inactiva la promocion se mantiene excepto graduacion y seminario
                                                                    if matricula.nivel.nivelmalla.id != NIVEL_GRADUACION and matricula.nivel.nivelmalla.id != NIVEL_SEMINARIO:
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

                                                            # #OCastillo 02-12-2021 Descuento por convenio empresas
                                                            if matricula.inscripcion.descuentoconvenio:
                                                                if matricula.inscripcion.descuentoconvenio and DEFAULT_PASSWORD == 'itb' and pago.tipo!=0:
                                                                    descuento = round(((rubro.valor * matricula.inscripcion.descuentoconvenio.descuento)/100),2)
                                                                    rubro.valor = rubro.valor - round(((rubro.valor * matricula.inscripcion.descuentoconvenio.descuento)/100),2)
                                                                    rubro.save()

                                                                    desc = Descuento(inscripcion = inscripcion,
                                                                                              motivo ='DESCUENTO EN CUOTAS',
                                                                                              total = rubro.valor,
                                                                                              fecha = datetime.today().date())
                                                                    desc.save()
                                                                    detalle = DetalleDescuento(descuento =desc,
                                                                                                rubro =rubro,
                                                                                                valor = descuento,
                                                                                                porcentaje = matricula.inscripcion.descuentoconvenio.descuento)
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
                                                                        #OCastillo 04-10-2021 no aplica descuento por grupo que no este marcado
                                                                        if inscripcion.grupo().descuento:
                                                                            #OCastillo 02-12-2021 se debe excluir de descuento por convenio empresas rubro matricula
                                                                            if not inscripcion.descuentoconvenio:
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
                                                else:
                                                    # actualizar el id rubro matricual con la nueva matricula
                                                    if RubroMatricula.objects.filter(matricula=datomatricu).exists():
                                                        for rubromatri in RubroMatricula.objects.filter(matricula=datomatricu):
                                                            rubromatri.matricula=matricula
                                                            rubromatri.save()
                                                    else:
                                                        pp = 1.0 if not matricula.becado else ((100-matricula.porcientobeca)/100.0)

                                                        for pago in nivel.pagonivel_set.all().exclude(tipo__in=EXCLUIR_TIPO_PAGO):
                                                            if pago.tipo==0 or (pago.tipo>0 and pp>0):
                                                                rubro = Rubro(fecha=datetime.today().date(),
                                                                            valor = pago.valor, inscripcion=inscripcion,
                                                                            cancelado = False, fechavence = pago.fecha,tiponivelpago=pago.tipo)
                                                                rubro.save()

                                                                #Aplica la promocion a todos  los niveles excepto el 1 que lo aplica en la parte de abajo
                                                                if matricula.inscripcion.promocion:
                                                                    if  pago.tipo!=0 and matricula.inscripcion.promocion.todos_niveles and DEFAULT_PASSWORD == 'itb' and matricula.nivel.nivelmalla.id != NIVEL_MALLA_UNO:
                                                                        #OCastillo 20-04-2023 para el caso de todos los niveles asi este inactiva la promocion se mantiene excepto graduacion y seminario
                                                                        if matricula.nivel.nivelmalla.id != NIVEL_GRADUACION and matricula.nivel.nivelmalla.id != NIVEL_SEMINARIO:
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


                                                    # actualizar el id rubro cuota
                                                    if RubroCuota.objects.filter(matricula=datomatricu).exclude():
                                                        for rubrocuotaact in RubroCuota.objects.filter(matricula=datomatricu):

                                                            rubrocuotaact.matricula=matricula
                                                            rubrocuotaact.save()
                                                    else:

                                                        pp = 1.0 if not matricula.becado else ((100-matricula.porcientobeca)/100.0)

                                                        #OCastillo 27-04-2023 se excluyen los rubros adicionales de la lista previa para no usar ids
                                                        # for pago in nivel.pagonivel_set.all().exclude(tipo__in=[13,14,15,16,17]):
                                                        for pago in nivel.pagonivel_set.all().exclude(tipo__in=lista2):
                                                            if pago.tipo==1 or (pago.tipo>1 and pp>0):
                                                                rubro = Rubro(fecha=datetime.today().date(),
                                                                            valor = pago.valor, inscripcion=inscripcion,
                                                                            cancelado = False, fechavence = pago.fecha,tiponivelpago=pago.tipo)
                                                                rubro.save()

                                                                #Aplica la promocion a todos  los niveles excepto el 1 que lo aplica en la parte de abajo
                                                                if matricula.inscripcion.promocion:
                                                                    if  pago.tipo!=0 and matricula.inscripcion.promocion.todos_niveles and DEFAULT_PASSWORD == 'itb' and matricula.nivel.nivelmalla.id != NIVEL_MALLA_UNO:
                                                                        #OCastillo 20-04-2023 para el caso de todos los niveles asi este inactiva la promocion se mantiene excepto graduacion y seminario
                                                                        if matricula.nivel.nivelmalla.id != NIVEL_GRADUACION and matricula.nivel.nivelmalla.id != NIVEL_SEMINARIO:
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

                                                                # #OCastillo 02-12-2021 Descuento por convenio empresas
                                                                if matricula.inscripcion.descuentoconvenio:
                                                                    if matricula.inscripcion.descuentoconvenio and DEFAULT_PASSWORD == 'itb'and pago.tipo!=0:
                                                                        descuento = round(((rubro.valor * matricula.inscripcion.descuentoconvenio.descuento)/100),2)
                                                                        rubro.valor = rubro.valor - round(((rubro.valor * matricula.inscripcion.descuentoconvenio.descuento)/100),2)
                                                                        rubro.save()

                                                                        desc = Descuento(inscripcion = inscripcion,
                                                                                                  motivo ='DESCUENTO EN CUOTAS',
                                                                                                  total = rubro.valor,
                                                                                                  fecha = datetime.today().date())
                                                                        desc.save()
                                                                        detalle = DetalleDescuento(descuento =desc,
                                                                                                    rubro =rubro,
                                                                                                    valor = descuento,
                                                                                                    porcentaje = matricula.inscripcion.descuentoconvenio.descuento)
                                                                        detalle.save()

                                                                # Beca
                                                                if matricula.becado and pago.tipo!=0:
                                                                    rubro.valor = rubro.valor * pp
                                                                    rubro.save()

                                                                # CUOTA MENSUAL
                                                                rc = RubroCuota(rubro=rubro, matricula=matricula, cuota=pago.tipo)
                                                                rc.save()


                                        if matricula.nivel.nivelmalla.id == NIVEL_MALLA_UNO and DEFAULT_PASSWORD == 'itb':
                                            if  Matricula.objects.filter(inscripcion=inscripcion,nivel__nivelmalla__id=NIVEL_MALLA_CERO).exists():
                                                mat =  Matricula.objects.filter(inscripcion=inscripcion,nivel__nivelmalla__id=NIVEL_MALLA_CERO)[:1].get()
                                                # if  mat.becado and inscripcion.tienediscapacidad:
                                                # SE APLICA A TODOS LOS BECADOS 30/06/2017
                                                if  mat.becado :
                                                    matricula.becado = True
                                                    matricula.porcientobeca = mat.porcientobeca
                                                    matricula.tipobeca = mat.tipobeca
                                                    matricula.motivobeca  = mat.motivobeca
                                                    matricula.tipobeneficio  = mat.tipobeneficio
                                                    matricula.fechabeca = datetime.now()
                                                    matricula.save()

                                                    if GENERAR_RUBROS_PAGO:
                                                        pp = (100-matricula.porcientobeca)/100.0

                                                        # Aplicar el % de Beca por cada Rubro Real q tenga el estudiante matriculado
                                                        for rubro in matricula.inscripcion.rubro_set.all():
                                                            #El tipo Otro es solo para pasar los historicos, luego quitarlo y dejar solo si es cuota
                                                            if rubro.es_cuota() and rubro.total_pagado()==0:
                                                                if pp==0:
                                                                    rubro.delete()
                                                                else:
                                                                    rubro.valor *= pp
                                                                    rubro.save()

                                            for rubro in  matricula.rubrocuota_set.all():
                                                if rubro.rubro.es_cuota() and rubro.rubro.total_pagado()==0:
                                                    if matricula.inscripcion.promocion and matricula.inscripcion.promocion.activo:
                                                        des = ((100-matricula.inscripcion.descuentoporcent)/100.0)
                                                        descuento = round(((rubro.rubro.valor * matricula.inscripcion.descuentoporcent)/100),2)
                                                        rubro.rubro.valor *= des
                                                        rubro.rubro.save()

                                                        desc = Descuento(inscripcion = inscripcion,
                                                                                  motivo ='DESCUENTO EN CUOTAS',
                                                                                  total = rubro.rubro.valor,
                                                                                  fecha = datetime.today().date())
                                                        desc.save()
                                                        detalle = DetalleDescuento(descuento =desc,
                                                                                    rubro =rubro.rubro,
                                                                                    valor = descuento,
                                                                                    porcentaje = matricula.inscripcion.descuentoporcent)
                                                        detalle.save()

                                        if matricula.inscripcion.carrera.nombre == 'CONGRESO DE PEDAGOGIA':
                                            p=None
                                            if PreInscripcion.objects.filter(cedula = matricula.inscripcion.persona.cedula,tipodoc='c').exists():
                                                p = PreInscripcion.objects.filter(cedula = matricula.inscripcion.persona.cedula,tipodoc='c')[:1].get()
                                            if PreInscripcion.objects.filter(cedula = matricula.inscripcion.persona.pasaporte,tipodoc='p').exists():
                                                p = PreInscripcion.objects.filter(cedula =  matricula.inscripcion.persona.pasaporte,tipodoc='p')[:1].get()
                                            if p:
                                                grupo = matricula.inscripcion.grupo()
                                                matins =matricula
                                                if p.valor:
                                                    if RubroMatricula.objects.filter(matricula=matins).exists():
                                                        rubromatins = RubroMatricula.objects.filter(matricula=matins)[:1].get()
                                                        rubromatins.rubro.valor = p.valor
                                                        rubromatins.rubro.save()
                                                if DatosPersonaCongresoIns.objects.filter(preinscripcion=p,grupo=grupo).exists():
                                                    for dpi in  DatosPersonaCongresoIns.objects.filter(preinscripcion=p,grupo=grupo):
                                                        dpi.inscripcion = inscripcion
                                                        dpi.save()
                                        #buscar en pago nivel si tiene pago con tipo 13 y 14
                                        # cantidadcoutaotra= matricula.nivel.pagonivel_set.filter(tipo__in=[13,14]).count()
                                        # if cantidadcoutaotra>0:
                                        #     auxcuota=13
                                        #     for i in range(cantidadcoutaotra):
                                        #          auxcuota=auxcuota+i
                                        #OCastillo 27-04-2023 se crean los rubros adicionales cargados en el plan de pagos del nivel con la lista previa
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
                                              # solo se aplica para los estudiante que estan becado por becas Tec
                                              hoy = datetime.today().date()
                                              # rubro cuota////////

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
                                            # actualizar la tabla de descuento por lo nuevos rubros
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
                                                    if not DetalleRubrosBeca.objects.filter(rubro=rc.rubro).exists():
                                                        # Si beca es 100%
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

                                            solicitudbeca.nivel=nivel_actual
                                            solicitudbeca.save()

                                        #OC 07-febrero-2019 enviar correo a soporte cuando la matricula es en el primer nivel
                                        if EMAIL_ACTIVE:
                                            if nivel_actual.nivelmalla.id == NIVEL_MALLA_UNO and DEFAULT_PASSWORD == 'itb':
                                                if len(alumnos_correo)>0:
                                                    op='2'

                                                    hoy = datetime.now().today()
                                                    personarespon = Persona.objects.filter(usuario=request.user)[:1].get()

                                                    esmunicipio=False
                                                    grupomunicipio =Grupo.objects.filter(id__in=LISTA_GRUPO_MUNICIPO)
                                                    for grup in grupomunicipio:
                                                        if nivel_actual.grupo_id==grup.id:
                                                            esmunicipio=True
                                                            break
                                                    # correo= ('ocastillo@bolivariano.edu.ec')
                                                    if esmunicipio:
                                                         nivel_matri=nivel_actual.nivelmalla.nombre
                                                         if TipoIncidencia.objects.filter(pk=68).exists():
                                                            tipo = TipoIncidencia.objects.filter(pk=68)[:1].get()
                                                            correo = tipo.correo

                                                         send_html_mail("ESTUDIANTES MATRICULADOS A "+nivel_matri+" "+"BECA MUNICIPIO",
                                                         "emails/correo_matricula_primernivel.html", {'contenido': "ESTUDIANTES MATRICULADOS A "+nivel_matri+" "+"BECA MUNICIPIO",'op':op, 'estudiante': alumnos_correo, 'nivel': nivel_matri,'grupo':grupo,'personarespon': personarespon, 'fecha': hoy,'carrera':carrera},correo.split(','))

                                                    else:
                                                        correo= str('soporteitb@bolivariano.edu.ec')
                                                        send_html_mail("ESTUDIANTES MATRICULADOS A PRIMER NIVEL",
                                                        "emails/correo_matricula_primernivel.html", {'contenido': "ESTUDIANTES MATRICULADOS A PRIMER NIVEL",'op':op, 'estudiante': alumnos_correo, 'nivel': nivel_matri,'grupo':grupo,'personarespon': personarespon, 'fecha': hoy,'carrera':carrera},correo.split(','))

                                            else:
                                                 esmunicipio=False
                                                 grupomunicipio =Grupo.objects.filter(id__in=LISTA_GRUPO_MUNICIPO)
                                                 for grup in grupomunicipio:
                                                        if nivel_actual.grupo_id==grup.id:
                                                            esmunicipio=True
                                                            break

                                                 if esmunicipio:
                                                     if len(alumnos_correo)>0:
                                                        op='2'
                                                        hoy = datetime.now().today()
                                                        personarespon = Persona.objects.filter(usuario=request.user)[:1].get()
                                                        nivel_matri=nivel_actual.nivelmalla.nombre

                                                        # correo= str('soporteitb@bolivariano.edu.ec')
                                                        # correo= ('ocastillo@bolivariano.edu.ec')
                                                        if TipoIncidencia.objects.filter(pk=68).exists():
                                                            tipo = TipoIncidencia.objects.filter(pk=68)[:1].get()
                                                            correo = tipo.correo
                                                        send_html_mail("ESTUDIANTES MATRICULADOS A "+nivel_matri+" "+"BECA MUNICIPIO",
                                                        "emails/correo_matricula_municipio.html", {'contenido': "ESTUDIANTES MATRICULADOS A "+nivel_matri+" "+"BECA MUNICIPIO",'op':op, 'estudiante': alumnos_correo, 'nivel': nivel_matri,'grupo':grupo,'personarespon': personarespon, 'fecha': hoy,'carrera':carrera},correo.split(','))
                                        if inscripcion.promocion:
                                            try:
                                                if inscripcion.promocion.descuentomaterial and inscripcion.promocion.valdescuentomaterial > 0 and  matricula.nivel.nivelmalla.id == NIVEL_MALLA_UNO:
                                                    if RubroOtro.objects.filter(matricula=matricula.id,tipo__id=TIPO_RUBRO_MATERIALAPOYO,rubro__inscripcion=inscripcion).exists():
                                                        rmaterial = RubroOtro.objects.filter(matricula=matricula.id,tipo_id=TIPO_RUBRO_MATERIALAPOYO,rubro__inscripcion=inscripcion)[:1].get()
                                                        rubro = rmaterial.rubro
                                                    else:
                                                        # nuevo campo material apoyo
                                                        valormaterialapoyo = inscripcion.promocion.valormaterialapoyo
                                                        rubro = Rubro(fecha=datetime.today().date(),
                                                                      valor=valormaterialapoyo,
                                                                      inscripcion=inscripcion,
                                                                      cancelado=True, fechavence=datetime.now())

                                                        rubro.save()
                                                        rmaterial = RubroOtro(rubro=rubro, matricula=matricula.id,tipo_id=TIPO_RUBRO_MATERIALAPOYO,descripcion='MATERIALES DE APOYO')
                                                        rmaterial.save()
                                                    if rmaterial:
                                                        descuento = round(((rubro.valor * inscripcion.promocion.valdescuentomaterial) / 100),2)
                                                        rubro.valor = rubro.valor - round(((rubro.valor * inscripcion.promocion.valdescuentomaterial) / 100),2)
                                                        rubro.save()
                                                        desc = Descuento(inscripcion=inscripcion,
                                                                         motivo='DESCUENTO PROMOCION',
                                                                         total=rubro.valor,
                                                                         fecha=datetime.today().date())
                                                        desc.save()
                                                        detalle = DetalleDescuento(descuento=desc,
                                                                                   rubro=rubro,
                                                                                   valor=descuento,
                                                                                   porcentaje=inscripcion.promocion.valdescuentomaterial)
                                                        detalle.save()
                                            except Exception as e:
                                                from sga.pre_inscripciones import email_error_congreso
                                                print(e)
                                                pass
                                                errores = []
                                                errores.append((
                                                    'Error al generar descuento en material de apoyo ' + str(matricula.id),str(inscripcion.id)))
                                                if errores:
                                                    email_error_congreso(errores,
                                                                         'ERROR EN MATRICULAS GENERAR DESCUENTO')
                        return HttpResponseRedirect('/matriculas?action=matricula&id='+str(f.cleaned_data['nivel'].id))
                    else:
                        return HttpResponseRedirect('/matriculas?action=addmatricula&id='+str(f.cleaned_data['nivel'].id)+'&error=1')

                elif action =='exportar_grupo':
                    grupo = open(os.path.join(MEDIA_ROOT, 'grupo.txt'), 'w')

                    for i in Inscripcion.objects.filter(inscripciongrupo__grupo__nombre=(request.POST['g']).upper()).exclude(persona__usuario__is_active=False).order_by('persona__apellido1','persona__apellido2','persona__nombres'):
                        try:
                            grupo.write(elimina_tildes(i.persona.usuario.username) +"," +str(i.persona.cedula) +"," + elimina_tildes(i.persona.apellido1) +" " + elimina_tildes(i.persona.apellido2) +"," + elimina_tildes(i.persona.nombres) +"," + elimina_tildes(i.persona.emailinst)+ '\n')
                        except Exception as e:
                            pass
                    grupo.close()

                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/grupo.txt"}),content_type="application/json")

                elif action =='descuentonivel':
                    try:
                        nivel = Nivel.objects.get(id=request.POST['idnivel'])

                        condescuento = 0
                        idcon = []
                        idsin = []
                        sindescuento = 0

                        if request.POST['ids'] !='':
                            idtipo = PagoNivel.objects.filter(id__in=request.POST['ids'].split(',')).values('tipo')
                            for r in RubroCuota.objects.filter(matricula__nivel=nivel,cuota__in=idtipo).order_by('rubro__inscripcion','cuota'):
                                pagonivel = PagoNivel.objects.filter(tipo=r.cuota,nivel=r.matricula.nivel)[:1].get()
                                if r.rubro.puede_eliminarse():
                                    if r.rubro.valor == pagonivel.valor:
                                        porcentaje = float(r.rubro.valor*int(request.POST['porcentaje']))/100
                                        r.rubro.valor = r.rubro.valor - porcentaje
                                        descuento = Descuento(inscripcion = r.rubro.inscripcion,
                                                                motivo = request.POST['observacion'],
                                                                total = porcentaje,
                                                                fecha = datetime.now())
                                        descuento.save()
                                        detalledescuento = DetalleDescuento(descuento = descuento,
                                                                            rubro = r.rubro,
                                                                            valor = porcentaje,
                                                                            porcentaje = float(request.POST['porcentaje']),
                                                                            usuario=request.user,
                                                                            descuota_nivel=True)
                                        detalledescuento.save()
                                        r.rubro.save()
                                        #Obtain client ip address
                                        client_address = ip_client_address(request)

                                        # Log de ADICIONAR MATRICULAS MULTIPLES
                                        LogEntry.objects.log_action(
                                            user_id         = request.user.pk,
                                            content_type_id = ContentType.objects.get_for_model(r.rubro).pk,
                                            object_id       = r.rubro.id,
                                            object_repr     = force_str(r.rubro),
                                            action_flag     = ADDITION,
                                            change_message  = 'Descuento al Nivel desde el modulo de matricula (' + client_address + ')'  )
                                        if not r.rubro.inscripcion.id in idcon:
                                            if r.rubro.inscripcion.id in idsin:
                                                idsin.remove(r.rubro.inscripcion.id)
                                                sindescuento = sindescuento - 1
                                            idcon.append(r.rubro.inscripcion.id)
                                            condescuento = condescuento + 1
                                    else:
                                        if not r.rubro.inscripcion.id in idsin and not r.rubro.inscripcion.id in idcon :
                                            idsin.append(r.rubro.inscripcion.id)
                                            sindescuento = sindescuento + 1
                                else:
                                    if not r.rubro.inscripcion.id in idsin and not r.rubro.inscripcion.id in idcon:
                                        idsin.append(r.rubro.inscripcion.id)
                                        sindescuento = sindescuento + 1
                        condescuentomat = 0
                        idconmat = []
                        idsinmat = []
                        sindescuento = 0
                        sindescuentomat = 0
                        if request.POST['porcentajemat'] > 0 and  request.POST['idsm'] !='':

                            for r in RubroMatricula.objects.filter(matricula__nivel=nivel).order_by():
                                pagonivel = PagoNivel.objects.filter(tipo=0,nivel=r.matricula.nivel)[:1].get()
                                if r.rubro.puede_eliminarse():
                                    if r.rubro.valor == pagonivel.valor:
                                        porcentaje = float(r.rubro.valor*int(request.POST['porcentajemat']))/100
                                        r.rubro.valor = r.rubro.valor - porcentaje
                                        descuento = Descuento(inscripcion = r.rubro.inscripcion,
                                                                motivo = request.POST['observacion'],
                                                                total = porcentaje,
                                                                fecha = datetime.now())
                                        descuento.save()
                                        detalledescuento = DetalleDescuento(descuento = descuento,
                                                                            rubro = r.rubro,
                                                                            valor = porcentaje,
                                                                            porcentaje = float(request.POST['porcentajemat']),
                                                                            usuario=request.user,
                                                                            descuota_nivel=True)
                                        detalledescuento.save()
                                        r.rubro.save()
                                        #Obtain client ip address
                                        client_address = ip_client_address(request)

                                        # Log de ADICIONAR MATRICULAS MULTIPLES
                                        LogEntry.objects.log_action(
                                            user_id         = request.user.pk,
                                            content_type_id = ContentType.objects.get_for_model(r.rubro).pk,
                                            object_id       = r.rubro.id,
                                            object_repr     = force_str(r.rubro),
                                            action_flag     = ADDITION,
                                            change_message  = 'Descuento al Nivel desde el modulo de Nivel Pago (' + client_address + ')'  )
                                        if not r.rubro.inscripcion.id in idconmat:
                                            if r.rubro.inscripcion.id in idsinmat:
                                                idsinmat.remove(r.rubro.inscripcion.id)
                                                sindescuentomat = sindescuentomat - 1
                                            idconmat.append(r.rubro.inscripcion.id)
                                            condescuentomat = condescuentomat + 1
                                    else:
                                        if not r.rubro.inscripcion.id in idsin and not r.rubro.inscripcion.id in idcon :
                                            idsinmat.append(r.rubro.inscripcion.id)
                                            sindescuentomat = sindescuentomat + 1
                                else:
                                    if not r.rubro.inscripcion.id in idsin and not r.rubro.inscripcion.id in idcon:
                                        idsinmat.append(r.rubro.inscripcion.id)
                                        sindescuentomat = sindescuentomat + 1
                        return HttpResponse(json.dumps({"result":"ok","sindescuento":str(sindescuento),"condescuento":str(condescuento),"sindescuentomat":str(sindescuentomat),"condescuentomat":str(condescuentomat),}),content_type="application/json")
                    except Exception as e:
                        print(e)
                        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

                elif action == 'liberar':
                    f = MotivoLiberadaForm(request.POST)
                    if f.is_valid():
                        matricula = Matricula.objects.filter(id=request.POST['matid'])[:1].get()
                        matricula.liberada = True
                        matricula.motivoliberada = f.cleaned_data['motivoliberada']
                        matricula.save()
                        liberada = MatriculaLiberada(matricula = matricula,
                                                     observacion =f.cleaned_data['motivoliberada'] ,
                                                     fecha = datetime.now(),
                                                     usuario  = request.user)
                        liberada.save()

                        #Obtain client ip address
                        client_address = ip_client_address(request)

                        # Log de ADICIONAR COLEGIO
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(matricula).pk,
                            object_id       = matricula.id,
                            object_repr     = force_str(matricula),
                            action_flag     = ADDITION,
                            change_message  = 'Matricula Liberada (' + client_address + ')' )

                        return HttpResponseRedirect("/matriculas?action=matricula&id="+str(matricula.nivel.id))

                elif action == 'quitarliberar':
                    f = MotivoLiberadaForm(request.POST)
                    if f.is_valid():
                        matricula = Matricula.objects.filter(id=request.POST['matid'])[:1].get()
                        matricula.liberada = False
                        matricula.motivoliberada = ""
                        matricula.save()
                        liberada = MatriculaLiberada(matricula = matricula,
                                                     observacion =f.cleaned_data['motivoliberada'] ,
                                                     fecha = datetime.now(),
                                                     liberada = False,
                                                     usuario  = request.user)
                        liberada.save()

                        #Obtain client ip address
                        client_address = ip_client_address(request)

                        # Log de ADICIONAR COLEGIO
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(matricula).pk,
                            object_id       = matricula.id,
                            object_repr     = force_str(matricula),
                            action_flag     = ADDITION,
                            change_message  = 'Eliminadaa Matricula Liberada (' + client_address + ')' )
                        return HttpResponseRedirect("/matriculas?action=matricula&id="+str(matricula.nivel.id))
                elif action =='exportar_grupocsv':
                    grupocsv = open(os.path.join(MEDIA_ROOT, 'grupocorreo.txt'), 'w')
                    grupocsv.write ("firstname"+","+"lastname"+","+"username"+"," +"email"+","+"password"+"," +"ou"+ '\n')
                    for m in Matricula.objects.filter(nivel__grupo__nombre=(request.POST['gcsv']).upper(),nivel__periodo__activo=True,nivel__carrera__carrera=True,inscripcion__persona__usuario__is_active=True).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres'):
                        try:
                            grupocsv.write (elimina_tildes(m.inscripcion.persona.nombres) +"," + elimina_tildes(m.inscripcion.persona.apellido1) + " " + elimina_tildes(m.inscripcion.persona.apellido2)+"," + elimina_tildes(m.inscripcion.persona.usuario.username) + "," + elimina_tildes(m.inscripcion.persona.emailinst) +"," +str(m.inscripcion.persona.cedula) +"," +'"' +"CN=Users,DC=itb,DC=edu,DC=ec"+'"'  + '\n')
                        except Exception as e:
                            pass
                    grupocsv.close()

                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/grupocorreo.txt"}),content_type="application/json")


                elif action=='addmatricula':
                    horas=None
                    asign = None
                    f = MatriculaForm(request.POST)
                    if f.is_valid():
                        #OCastillo 26-04-2023 se crea una lista con los rubros adicionales que no son matricula ni cuotas
                        lista2=[]
                        for pn in TIPOS_PAGO_NIVEL:
                            if not 'CUOTA' in pn[1] and not  'MATRICULA' in pn[1] :
                                lista2.append(pn[0])

                        inscripcion = f.cleaned_data['inscripcion']
                        # if inscripcion.carrera.validacionprofesional:
                        #         if not ExamenConvalidacionIngreso.objects.filter(inscripcion=inscripcion).exists():
                        #             return HttpResponseRedirect('/matriculas?action=addmatricula&id='+str(f.instance.nivel_id)+'&error=4')
                        #         else:
                        #             if not ExamenConvalidacionIngreso.objects.filter(inscripcion=inscripcion,aprobada=True).exists():
                        #                 return HttpResponseRedirect('/matriculas?action=addmatricula&id='+str(f.instance.nivel_id)+'&error=5')

                        #OCastillo 15-02-2023 validaciones para carrera de optometria nivel graduacion
                        #OCastillo 15-04-2023 validaciones para todas las carreras nivel graduacion
                        # if Nivel.objects.filter(pk=f.instance.nivel_id,nivelmalla__id=NIVEL_GRADUACION) and inscripcion.carrera.id==48:
                        if Nivel.objects.filter(pk=f.instance.nivel_id,nivelmalla__id=NIVEL_GRADUACION):
                            if not inscripcion.tiene_certificacion_ingles():
                                return HttpResponseRedirect('/matriculas?action=addmatricula&id='+str(f.instance.nivel_id)+'&error=6')
                            if inscripcion.h_practicas_vinculacion() == 0 or inscripcion.h_practicas_vinculacion_segunmalla() == 0 :
                                horas=str(inscripcion.h_practicas_vinculacion())
                                return HttpResponseRedirect('/matriculas?action=addmatricula&id='+str(f.instance.nivel_id)+'&error=7'+'&hvin='+horas)
                            if inscripcion.h_practicas_vinculacion()< inscripcion.h_practicas_vinculacion_segunmalla():
                                horas=str(inscripcion.h_practicas_vinculacion())
                                return HttpResponseRedirect('/matriculas?action=addmatricula&id='+str(f.instance.nivel_id)+'&error=7'+'&hvin='+horas)
                            if not inscripcion.mallacompleta():
                                return HttpResponseRedirect('/matriculas?action=addmatricula&id='+str(f.instance.nivel_id)+'&error=8')
                            if not inscripcion.tiene_documentacion():
                                return HttpResponseRedirect('/matriculas?action=addmatricula&id='+str(f.instance.nivel_id)+'&error=9')
                        if  not inscripcion.tiene_deuda_matricula():
                            if not inscripcion.matriculado():

                                # #Comprobar si ha llenado su ficha medica y su valoracion medica - solicitado para la acreditacion
                                # if UTILIZA_FICHA_MEDICA:
                                #     if inscripcion.persona.datos_medicos_incompletos():
                                #         return HttpResponseRedirect('/matriculas?action=addmatricula&id='+str(f.instance.nivel_id)+'&ficha=1')
                                #     elif inscripcion.persona.valoracion_medica_incompleta():
                                #         return HttpResponseRedirect('/matriculas?action=addmatricula&id='+str(f.instance.nivel_id)+'&valoracion=1')


                                f.save()
                                matricula = f.instance
                                nivel = matricula.nivel
                                materias = nivel.materia_set.filter(Q(cerrado=False)|Q(cerrado=None))
                                inscripcion = matricula.inscripcion

                                #Actualizar el registro de InscripcionMalla con la malla correspondiente
                                if matricula.nivel.malla:
                                    im = inscripcion.malla_inscripcion()
                                    im.malla = matricula.nivel.malla
                                    im.save()

                                # buscar si existe matricula en el mismo nivel para no crear los rubros
                                crearubro=True
                                datomatricu=None
                                #listmatricula = Matricula.objects.filter(inscripcion=inscripcion).exclude(id=matricula.id)
                                #OCastillo 01-03-2021 verificar matricula de niveles abiertos
                                listmatricula = Matricula.objects.filter(inscripcion=inscripcion,nivel__cerrado=False).exclude(id=matricula.id)

                                #OCastillo 01-03-2021 si tiene reingtegro variable crea rubro en true
                                if RetiradoMatricula.objects.filter(inscripcion=inscripcion,activo=True).exists():
                                   retirado =RetiradoMatricula.objects.filter(inscripcion=inscripcion,activo=True)[:1].get()
                                   if DetalleRetiradoMatricula.objects.filter(retirado=retirado,estado='REINTEGRO').order_by('-id').exists():
                                        crearubro=True
                                else:
                                    if len(listmatricula)>0:
                                        for matri in listmatricula:
                                            if matri.nivel.nivelmalla.id==nivel.nivelmalla.id:
                                                crearubro=False
                                                datomatricu=matri
                                                break

                                if inscripcion.tienediscapacidad and EMAIL_ACTIVE:
                                    nivel.mail_matricula_discapacidad(inscripcion)


                                solicitudbeca=None
                                if matricula.tipobeneficio==TipoBeneficio.objects.get(pk=1) or  matricula.tipobeneficio==TipoBeneficio.objects.get(pk=3):
                                    if SolicitudBeca.objects.filter(inscripcion=inscripcion,nivel__nivelmalla__id=nivel.nivelmalla.id,tiposolicitud=1).order_by('-fecha').exists():
                                         if SolicitudBeca.objects.filter(inscripcion=inscripcion,nivel__nivelmalla__id=nivel.nivelmalla.id,tiposolicitud=1,aprobado=True,aprobacionestudiante=True,asignaciontarficadescuento=True).order_by('-fecha').exists():
                                            solicitudbeca = SolicitudBeca.objects.filter(inscripcion=inscripcion,nivel__nivelmalla__id=nivel.nivelmalla.id,tiposolicitud=1,aprobado=True,aprobacionestudiante=True).order_by('-fecha')[:1].get()
                                         else:
                                             if SolicitudBeca.objects.filter(inscripcion=inscripcion,nivel__nivelmalla__id=nivel.nivelmalla.id,tiposolicitud=2,aprobado=True,aprobacionestudiante=True,asignaciontarficadescuento=True).order_by('-fecha').exists():
                                                solicitudbeca = SolicitudBeca.objects.filter(inscripcion=inscripcion,nivel__nivelmalla__id=nivel.nivelmalla.id,tiposolicitud=2,aprobado=True,aprobacionestudiante=True).order_by('-fecha')[:1].get()
                                    else:
                                        return HttpResponseRedirect('/matriculas?action=addmatricula&id='+str(nivel.id)+'&error=7')

                                if solicitudbeca:
                                    # si el estado de la solicitud ya fue aprobado y aplicada por secretaria
                                    # if solicitudbeca.estadosolicitud==7:
                                    matricula.becado=True
                                    matricula.tipobeneficio=matricula.tipobeneficio
                                    matricula.tipobeca=matricula.tipobeca
                                    matricula.motivobeca=matricula.motivobeca
                                    matricula.porcientobeca=matricula.porcientobeca
                                    matricula.fechabeca=matricula.fechabeca

                                    matricula.save()

                                    solicitudbeca.estadosolicitud=7
                                    solicitudbeca.nivel=nivel
                                    solicitudbeca.save()

                                #Obtain client ip address
                                client_address = ip_client_address(request)

                                # Log de ADICIONAR MATRICULA
                                LogEntry.objects.log_action(
                                    user_id         = request.user.pk,
                                    content_type_id = ContentType.objects.get_for_model(matricula).pk,
                                    object_id       = matricula.id,
                                    object_repr     = force_str(matricula),
                                    action_flag     = ADDITION,
                                    change_message  = 'Adicionada Matricula (' + client_address + ')' )
                                if matricula.nivel.nivelmalla.id == NIVEL_SEMINARIO :
                                    matricula.correo_semimario()

                                # Materias Asignadas
                                if not 'CONGRESO' in nivel.carrera.nombre:
                                    for materia in materias:
                                        asignatura = materia.asignatura
                                        if not inscripcion.ya_aprobada(asignatura):
                                            # Si no la tiene aprobada aun
                                            pendientes = inscripcion.recordacademico_set.filter(asignatura__in=asignatura.precedencia.all(),aprobada=False)
                                            if pendientes.count()==0:
                                                asign = MateriaAsignada(matricula=matricula,materia=materia,notafinal=0,asistenciafinal=0,supletorio=0)
                                                asign.save()

                                                # Correccion de Lecciones ya impartidas
                                                leccionesYaDadas = Leccion.objects.filter(clase__materia=asign.materia)
                                                for leccion in leccionesYaDadas:
                                                    asistenciaLeccion = AsistenciaLeccion(leccion=leccion,matricula=matricula,asistio=False)
                                                    asistenciaLeccion.save()
                                            else:
                                                recordPendiente = RecordAcademico(inscripcion=inscripcion,asignatura=asignatura,nota=0,asistencia=0,fecha=datetime.now(),convalidacion=False,aprobada=False,pendiente=True)
                                                recordPendiente.save()
                                    for materia in MateriaNivel.objects.filter(nivel=nivel):
                                        if datetime.now().date() <= materia.materia.inicio + timedelta(days =5):

                                            asignatura = materia.materia.asignatura
                                            if not inscripcion.ya_aprobada(asignatura):
                                                # Si no la tiene aprobada aun
                                                pendientes = inscripcion.recordacademico_set.filter(asignatura__in=asignatura.precedencia.all(),aprobada=False)
                                                if pendientes.count()==0:
                                                    if not MateriaAsignada.objects.filter(materia__asignatura=materia.materia.asignatura,matricula=matricula).exists():
                                                        asign = MateriaAsignada(matricula=matricula,materia=materia.materia,notafinal=0,asistenciafinal=0,supletorio=0)
                                                        asign.save()

                                                    # Correccion de Lecciones ya impartidas
                                                    leccionesYaDadas = Leccion.objects.filter(clase__materia=asign.materia)
                                                    for leccion in leccionesYaDadas:
                                                        asistenciaLeccion = AsistenciaLeccion(leccion=leccion,matricula=matricula,asistio=False)
                                                        asistenciaLeccion.save()
                                                else:
                                                    recordPendiente = RecordAcademico(inscripcion=inscripcion,asignatura=asignatura,nota=0,asistencia=0,fecha=datetime.now(),convalidacion=False,aprobada=False,pendiente=True)
                                                    recordPendiente.save()

                                # Crear Rubro
                                if GENERAR_RUBROS_PAGO and not matricula.tipobeneficio==TipoBeneficio.objects.get(pk=TIPO_BECA_SENESCYT) and not inscripcion.beca_senescyt().tienebeca:
                                     if matricula.inscripcion.empresaconvenio_id!=ID_CONVENIO_BECA_TECT:
                                        if crearubro:
                                                pp = 1.0 if not matricula.becado else ((100-matricula.porcientobeca)/100.0)
                                                sec = 1
                                                #OCastillo 26-04-2023 se excluyen los rubros adicionales de la lista previa para no usar ids
                                                # for pago in nivel.pagonivel_set.all().exclude(tipo__in=[13,14,15,16,17]):
                                                for pago in nivel.pagonivel_set.all().exclude(tipo__in=lista2):
                                                    if pago.tipo==0 or (pago.tipo>0 and pp>0):
                                                        valor = pago.valor
                                                        if inscripcion.beca_asignada():
                                                            beca = inscripcion.beca_asignada_obj()
                                                            valor = pago.valor * (1-(beca.porciento/100.0))

                                                        rubro = Rubro(fecha=datetime.today().date(),
                                                                    valor = valor, inscripcion=inscripcion,
                                                                    cancelado = False, fechavence = pago.fecha,tiponivelpago=pago.tipo)

                                                        rubro.save()

                                                        if InscripcionesCAB.objects.filter(inscripcion=inscripcion, estado=True).exists() and inscripcion.cab:
                                                            cab = InscripcionesCAB.objects.filter(inscripcion=inscripcion, estado=True).order_by('-id')[:1].get()
                                                            cuota_cab = CuotaCAB(descripcion='CUOTA CAB #'+str(sec),
                                                                                 rubro=rubro,
                                                                                 inscripcioncab=cab,
                                                                                 fechavence=rubro.fechavence,
                                                                                 valor=cab.monto,
                                                                                 nivel=matricula.nivel)
                                                            cuota_cab.save()
                                                            sec = sec + 1
                                                        #Aplica la promocion a todos  los niveles excepto el 1 que lo aplica en la parte de abajo
                                                        if matricula.inscripcion.promocion:
                                                            if pago.tipo!=0 and matricula.inscripcion.promocion.todos_niveles and DEFAULT_PASSWORD == 'itb' and matricula.nivel.nivelmalla.id != NIVEL_MALLA_UNO:
                                                                #OCastillo 20-04-2023 para el caso de todos los niveles asi este inactiva la promocion se mantiene excepto graduacion y seminario
                                                                if matricula.nivel.nivelmalla.id != NIVEL_GRADUACION and matricula.nivel.nivelmalla.id != NIVEL_SEMINARIO:
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

                                                        #OCastillo 01-12-2021 Descuento por convenio empresas
                                                        if matricula.inscripcion.descuentoconvenio:
                                                            if pago.tipo!=0 and matricula.inscripcion.descuentoconvenio and DEFAULT_PASSWORD == 'itb' and pago.tipo!=0:
                                                                descuento = round(((rubro.valor * matricula.inscripcion.descuentoconvenio.descuento)/100),2)
                                                                rubro.valor = rubro.valor - round(((rubro.valor * matricula.inscripcion.descuentoconvenio.descuento)/100),2)
                                                                rubro.save()

                                                                desc = Descuento(inscripcion = inscripcion,
                                                                                          motivo ='DESCUENTO EN CUOTAS',
                                                                                          total = rubro.valor,
                                                                                          fecha = datetime.today().date())
                                                                desc.save()
                                                                detalle = DetalleDescuento(descuento =desc,
                                                                                            rubro =rubro,
                                                                                            valor = descuento,
                                                                                            porcentaje = matricula.inscripcion.descuentoconvenio.descuento)
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
                                                                    #OCastillo 04-10-2021 no aplica descuento por grupo que no este marcado
                                                                    if inscripcion.grupo().descuento:
                                                                        #OCastillo 02-12-2021 se debe excluir de descuento por convenio empresas rubro matricula
                                                                        if not inscripcion.descuentoconvenio:
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
                                        else:
                                            # actualizar el id rubro matricual con la nueva matricula
                                            if RubroMatricula.objects.filter(matricula=datomatricu).exists():
                                                for rubromatri in RubroMatricula.objects.filter(matricula=datomatricu):
                                                    rubromatri.matricula=matricula
                                                    rubromatri.save()
                                            else:
                                                pp = 1.0 if not matricula.becado else ((100-matricula.porcientobeca)/100.0)

                                                for pago in nivel.pagonivel_set.all().exclude(tipo__in=EXCLUIR_TIPO_PAGO):
                                                    if pago.tipo==0 or (pago.tipo>0 and pp>0):
                                                        rubro = Rubro(fecha=datetime.today().date(),
                                                                    valor = pago.valor, inscripcion=inscripcion,
                                                                    cancelado = False, fechavence = pago.fecha,tiponivelpago=pago.tipo)
                                                        rubro.save()

                                                        #Aplica la promocion a todos  los niveles excepto el 1 que lo aplica en la parte de abajo
                                                        if matricula.inscripcion.promocion:
                                                            if  pago.tipo!=0 and matricula.inscripcion.promocion.todos_niveles and DEFAULT_PASSWORD == 'itb' and matricula.nivel.nivelmalla.id != NIVEL_MALLA_UNO:
                                                                #OCastillo 20-04-2023 para el caso de todos los niveles asi este inactiva la promocion se mantiene excepto graduacion y seminario
                                                                if matricula.nivel.nivelmalla.id != NIVEL_GRADUACION and matricula.nivel.nivelmalla.id != NIVEL_SEMINARIO:
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


                                            # actualizar el id rubro cuota
                                            if RubroCuota.objects.filter(matricula=datomatricu).exclude():
                                                for rubrocuotaact in RubroCuota.objects.filter(matricula=datomatricu):

                                                    rubrocuotaact.matricula=matricula
                                                    rubrocuotaact.save()
                                            else:

                                                pp = 1.0 if not matricula.becado else ((100-matricula.porcientobeca)/100.0)

                                                #OCastillo 26-04-2023 se excluyen los rubros adicionales de la lista previa para no usar ids
                                                # for pago in nivel.pagonivel_set.all().exclude(tipo__in=[13,14,15,16,17]):
                                                for pago in nivel.pagonivel_set.all().exclude(tipo__in=lista2):
                                                    if pago.tipo==1 or (pago.tipo>1 and pp>0):
                                                        rubro = Rubro(fecha=datetime.today().date(),
                                                                    valor = pago.valor, inscripcion=inscripcion,
                                                                    cancelado = False, fechavence = pago.fecha,tiponivelpago=pago.tipo)
                                                        rubro.save()

                                                        #Aplica la promocion a todos  los niveles excepto el 1 que lo aplica en la parte de abajo
                                                        if matricula.inscripcion.promocion:
                                                            if  pago.tipo!=0 and matricula.inscripcion.promocion.todos_niveles and DEFAULT_PASSWORD == 'itb' and matricula.nivel.nivelmalla.id != NIVEL_MALLA_UNO:
                                                                #OCastillo 20-04-2023 para el caso de todos los niveles asi este inactiva la promocion se mantiene excepto graduacion y seminario
                                                                if matricula.nivel.nivelmalla.id != NIVEL_GRADUACION and matricula.nivel.nivelmalla.id != NIVEL_SEMINARIO:
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

                                                        # CUOTA MENSUAL
                                                        rc = RubroCuota(rubro=rubro, matricula=matricula, cuota=pago.tipo)
                                                        rc.save()

                                if matricula.nivel.nivelmalla.id == NIVEL_MALLA_UNO and DEFAULT_PASSWORD == 'itb':
                                    if  Matricula.objects.filter(inscripcion=inscripcion,nivel__nivelmalla__id=NIVEL_MALLA_CERO).exists():
                                        mat =  Matricula.objects.filter(inscripcion=inscripcion,nivel__nivelmalla__id=NIVEL_MALLA_CERO)[:1].get()
                                        # if  mat.becado and inscripcion.tienediscapacidad:
                                        # SE APLICA A TODOS LOS BECADOS 30/06/2017
                                        if  mat.becado :
                                            matricula.becado = True
                                            matricula.porcientobeca = mat.porcientobeca
                                            matricula.tipobeca = mat.tipobeca
                                            matricula.motivobeca  = mat.motivobeca
                                            matricula.tipobeneficio  = mat.tipobeneficio
                                            matricula.fechabeca = datetime.now()
                                            matricula.save()

                                            if GENERAR_RUBROS_PAGO:
                                                pp = (100-matricula.porcientobeca)/100.0

                                                # Aplicar el % de Beca por cada Rubro Real q tenga el estudiante matriculado

                                                #OCastillo 26-04-2023 se excluyen los rubros adicionales de la lista previa para no usar ids
                                                # for rubro in matricula.inscripcion.rubro_set.all().exclude(tipo__in=[13,14,15,16,17]):
                                                for rubro in matricula.inscripcion.rubro_set.all().exclude(tipo__in=lista2):
                                                    #El tipo Otro es solo para pasar los historicos, luego quitarlo y dejar solo si es cuota
                                                    if rubro.es_cuota() and rubro.total_pagado()==0:
                                                        if pp==0:
                                                            rubro.delete()
                                                        else:
                                                            rubro.valor *= pp
                                                            rubro.save()

                                    for rubro in  matricula.rubrocuota_set.all():
                                        if rubro.rubro.es_cuota() and rubro.rubro.total_pagado()==0:
                                            if matricula.inscripcion.promocion and matricula.inscripcion.promocion.activo:
                                                des = ((100-matricula.inscripcion.descuentoporcent)/100.0)
                                                descuento = round(((rubro.rubro.valor * matricula.inscripcion.descuentoporcent)/100),2)
                                                rubro.rubro.valor *= des
                                                rubro.rubro.save()
                                                desc = Descuento(inscripcion = inscripcion,
                                                                          motivo ='DESCUENTO EN CUOTAS',
                                                                          total = rubro.rubro.valor,
                                                                          fecha = datetime.today().date())
                                                desc.save()
                                                detalle = DetalleDescuento(descuento =desc,
                                                                            rubro =rubro.rubro,
                                                                            valor = descuento,
                                                                            porcentaje = matricula.inscripcion.descuentoporcent)
                                                detalle.save()



                                #buscar en pago nivel si tiene pago con tipo 13 y 14
                                # cantidadcoutaotra= matricula.nivel.pagonivel_set.filter(tipo__in=[13,14,15,16,17]).count()

                                #OCastillo 26-04-2023 se crean los rubros adicionales cargados en el plan de pagos del nivel con la lista previa
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
                                      # solo se aplica para los estudiante que estan becado por becas Tec
                                      hoy = datetime.today().date()
                                      # rubro cuota////////

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




                                #OC 07-febrero-2019 enviar correo a soporte cuando la matricula es en el primer nivel
                                if EMAIL_ACTIVE:
                                    if matricula.nivel.nivelmalla.id == NIVEL_MALLA_UNO and DEFAULT_PASSWORD == 'itb':
                                        hoy = datetime.now().today()
                                        estudiante=elimina_tildes(inscripcion.persona.nombre_completo_inverso())
                                        nivel_matri=matricula.nivel.nivelmalla.nombre
                                        grupo= matricula.nivel.paralelo
                                        carrera=matricula.nivel.carrera.nombre
                                        personarespon = Persona.objects.filter(usuario=request.user)[:1].get()

                                        # correo= str('ocastillo@bolivariano.edu.ec')
                                        correo_inst=str(inscripcion.persona.emailinst)
                                        op='1'
                                        esmunicipio=False
                                        grupomunicipio =Grupo.objects.filter(id__in=LISTA_GRUPO_MUNICIPO)

                                        for grup in grupomunicipio:
                                            if nivel.grupo_id==grup.id:
                                                esmunicipio=True
                                                break

                                        if esmunicipio:
                                            if TipoIncidencia.objects.filter(pk=68).exists():
                                                tipo = TipoIncidencia.objects.filter(pk=68)[:1].get()
                                                correo = tipo.correo

                                            send_html_mail("ESTUDIANTE MATRICULADO A "+nivel_matri+" "+"BECA MUNICIPIO",
                                            "emails/correo_matricula_primernivel.html", {'contenido': "ESTUDIANTE MATRICULADO A "+nivel_matri+" "+"BECA MUNICIPIO",'op':op, 'estudiante': estudiante, 'nivel': nivel_matri,'grupo':grupo,'correo_inst':correo_inst,'personarespon': personarespon, 'fecha': hoy,'carrera':carrera},correo.split(','))


                                        else:
                                            correo= str('soporteitb@bolivariano.edu.ec')
                                            send_html_mail("ESTUDIANTE MATRICULADO A PRIMER NIVEL",
                                            "emails/correo_matricula_primernivel.html", {'contenido': "ESTUDIANTE MATRICULADO A PRIMER NIVEL",'op':op, 'estudiante': estudiante, 'nivel': nivel_matri,'grupo':grupo,'correo_inst':correo_inst,'personarespon': personarespon, 'fecha': hoy,'carrera':carrera},correo.split(','))
                                    else:
                                        esmunicipio=False
                                        grupomunicipio =Grupo.objects.filter(id__in=LISTA_GRUPO_MUNICIPO)

                                        for grup in grupomunicipio:
                                            if nivel.grupo_id==grup.id:
                                                esmunicipio=True
                                                break

                                        if esmunicipio:
                                             hoy = datetime.now().today()
                                             estudiante=elimina_tildes(inscripcion.persona.nombre_completo_inverso())
                                             nivel_matri=matricula.nivel.nivelmalla.nombre
                                             grupo= matricula.nivel.paralelo
                                             carrera=matricula.nivel.carrera.nombre
                                             personarespon = Persona.objects.filter(usuario=request.user)[:1].get()
                                             correo_inst=str(inscripcion.persona.emailinst)

                                             if TipoIncidencia.objects.filter(pk=68).exists():
                                                tipo = TipoIncidencia.objects.filter(pk=68)[:1].get()
                                                correo = tipo.correo

                                             send_html_mail("ESTUDIANTE MATRICULADO A "+nivel_matri+" "+"BECA MUNICIPIO" ,
                                            "emails/correo_matricula_municipio.html", {'contenido': "ESTUDIANTE MATRICULADO A "+nivel_matri+" "+"BECA MUNICIPIO", 'estudiante': estudiante, 'nivel': nivel_matri,'grupo':grupo,'correo_inst':correo_inst,'personarespon': personarespon, 'fecha': hoy,'carrera':carrera},correo.split(','))

                                if inscripcion.promocion:
                                    try:
                                        if inscripcion.promocion.descuentomaterial and inscripcion.promocion.valdescuentomaterial > 0 and  matricula.nivel.nivelmalla.id == NIVEL_MALLA_UNO:
                                            if RubroOtro.objects.filter(matricula=matricula.id,tipo__id=TIPO_RUBRO_MATERIALAPOYO,rubro__inscripcion=matricula.inscripcion).exists():
                                                rmaterial = RubroOtro.objects.filter(matricula=matricula.id,tipo__id=TIPO_RUBRO_MATERIALAPOYO,rubro__inscripcion=matricula.inscripcion)[:1].get()
                                                rubro = rmaterial.rubro
                                            else:
                                                valormaterialapoyo= inscripcion.promocion.valormaterialapoyo
                                                rubro = Rubro(fecha=datetime.today().date(),
                                                              valor=valormaterialapoyo,
                                                              inscripcion=inscripcion,
                                                              cancelado=True, fechavence=datetime.now())

                                                rubro.save()
                                                rmaterial = RubroOtro(rubro=rubro, matricula=matricula.id,tipo_id=TIPO_RUBRO_MATERIALAPOYO,descripcion='MATERIALES DE APOYO')
                                                rmaterial.save()
                                            if rmaterial:
                                                descuento = round(((rubro.valor * inscripcion.promocion.valdescuentomaterial) / 100),2)
                                                rubro.valor = rubro.valor - round(((rubro.valor * inscripcion.promocion.valdescuentomaterial) / 100),2)
                                                rubro.save()
                                                desc = Descuento(inscripcion=inscripcion,
                                                                 motivo='DESCUENTO PROMOCION',
                                                                 total=rubro.valor,
                                                                 fecha=datetime.today().date())
                                                desc.save()
                                                detalle = DetalleDescuento(descuento=desc,
                                                                           rubro=rubro,
                                                                           valor=descuento,
                                                                           porcentaje=inscripcion.promocion.valdescuentomaterial)
                                                detalle.save()
                                    except Exception as e:
                                        from sga.pre_inscripciones import email_error_congreso
                                        errores = []
                                        errores.append((
                                            'Error al generar descuento en material de apoyo ' + str(
                                                matricula.id),
                                            str(inscripcion.id)))
                                        if errores:
                                            email_error_congreso(errores,
                                                                 'ERROR EN MATRICULAS GENERAR DESCUENTO')
                            return HttpResponseRedirect('/matriculas?action=matricula&id='+str(f.instance.nivel_id))
                        else:
                            return HttpResponseRedirect('/matriculas?action=addmatricula&id='+str(f.instance.nivel_id)+'&error=2')
                    else:
                        return HttpResponseRedirect('/matriculas?action=addmatricula&id='+str(f.instance.nivel_id)+'&error=1')

                elif action=='addmatriculaextra':
                    nivel = Nivel.objects.get(pk=request.POST['id'])
                    f = MatriculaExtraForm(request.POST)
                    if f.is_valid():
                        #OCastillo 27-04-2023 se crea una lista con los rubros adicionales que no son matricula ni cuotas
                        lista2=[]
                        for pn in TIPOS_PAGO_NIVEL:
                            if not 'CUOTA' in pn[1] and not  'MATRICULA' in pn[1] :
                                lista2.append(pn[0])

                        inscripcion = f.cleaned_data['inscripcion']
                        recargo = f.cleaned_data['recargo']
                        if not inscripcion.tiene_deuda_matricula():

                            if not inscripcion.matriculado():

                                #Comprobar si ha llenado su ficha medica y valoracion medica - solicitado para la acreditacion
                                # if UTILIZA_FICHA_MEDICA:
                                #     if inscripcion.persona.datos_medicos_incompletos():
                                #         return HttpResponseRedirect('/matriculas?action=addmatriculaextra&id='+str(nivel.id)+'&ficha=1')
                                #     elif inscripcion.persona.valoracion_medica_incompleta():
                                #         return HttpResponseRedirect('/matriculas?action=addmatriculaextra&id='+str(nivel.id)+'&valoracion=1')

                                matricula = Matricula(inscripcion=inscripcion, nivel=nivel,
                                                      pago=False, iece=False, becado=False)
                                matricula.save()
                                materias = nivel.materia_set.filter(Q(cerrado=False)|Q(cerrado=None))

                                #Actualizar el registro de InscripcionMalla con la malla correspondiente
                                im = inscripcion.malla_inscripcion()
                                im.malla = matricula.nivel.malla
                                im.save()
                                if inscripcion.tienediscapacidad and EMAIL_ACTIVE:
                                    nivel.mail_matricula_discapacidad(inscripcion)


                                # buscar si existe matricula en el mismo nivel para no crear los rubros
                                crearubro=True
                                datomatricu=None
                                #listmatricula = Matricula.objects.filter(inscripcion=inscripcion).exclude(id=matricula.id)
                                #OCastillo 01-03-2021 verificar matricula de niveles abiertos
                                listmatricula = Matricula.objects.filter(inscripcion=inscripcion,nivel__cerrado=False).exclude(id=matricula.id)

                                #OCastillo 01-03-2021 si tiene reingtegro variable crea rubro en true
                                if RetiradoMatricula.objects.filter(inscripcion=inscripcion,activo=True).exists():
                                   retirado =RetiradoMatricula.objects.filter(inscripcion=inscripcion,activo=True)[:1].get()
                                   if DetalleRetiradoMatricula.objects.filter(retirado=retirado,estado='REINTEGRO').order_by('-id').exists():
                                        crearubro=True
                                else:
                                    if len(listmatricula)>0:
                                        for matri in listmatricula:
                                            if matri.nivel.nivelmalla.id==nivel.nivelmalla.id:
                                                crearubro=False
                                                datomatricu=matri
                                                break


                                #Obtain client ip address
                                client_address = ip_client_address(request)

                                # Log de ADICIONAR MATRICULA
                                LogEntry.objects.log_action(
                                    user_id         = request.user.pk,
                                    content_type_id = ContentType.objects.get_for_model(matricula).pk,
                                    object_id       = matricula.id,
                                    object_repr     = force_str(matricula),
                                    action_flag     = ADDITION,
                                    change_message  = 'Adicionada Matricula Extraordinaria (' + client_address + ')' )

                                # Materias Asignadas
                                if not 'CONGRESO' in nivel.carrera.nombre:
                                    for materia in materias:
                                        asignatura = materia.asignatura
                                        if not inscripcion.ya_aprobada(asignatura):
                                            # Si no la tiene aprobada aun
                                            pendientes = inscripcion.recordacademico_set.filter(asignatura__in=asignatura.precedencia.all(),aprobada=False)
                                            if pendientes.count()==0:
                                                asign = MateriaAsignada(matricula=matricula,materia=materia,notafinal=0,asistenciafinal=0,supletorio=0)
                                                asign.save()

                                                # Correccion de Lecciones ya impartidas
                                                leccionesYaDadas = Leccion.objects.filter(clase__materia=asign.materia)
                                                for leccion in leccionesYaDadas:
                                                    asistenciaLeccion = AsistenciaLeccion(leccion=leccion,matricula=matricula,asistio=False)
                                                    asistenciaLeccion.save()
                                            else:
                                                recordPendiente = RecordAcademico(inscripcion=inscripcion,asignatura=asignatura,nota=0,asistencia=0,fecha=datetime.now(),convalidacion=False,aprobada=False,pendiente=True)
                                                recordPendiente.save()
                                    for materia in MateriaNivel.objects.filter(nivel=nivel):
                                        if datetime.now().date() <= materia.materia.inicio + timedelta(days =5):

                                            asignatura = materia.materia.asignatura
                                            if not inscripcion.ya_aprobada(asignatura):
                                                # Si no la tiene aprobada aun
                                                pendientes = inscripcion.recordacademico_set.filter(asignatura__in=asignatura.precedencia.all(),aprobada=False)
                                                if pendientes.count()==0:
                                                    if not MateriaAsignada.objects.filter(materia__asignatura=materia.materia.asignatura,matricula=matricula).exists():
                                                        asign = MateriaAsignada(matricula=matricula,materia=materia.materia,notafinal=0,asistenciafinal=0,supletorio=0)
                                                        asign.save()

                                                    # Correccion de Lecciones ya impartidas
                                                    leccionesYaDadas = Leccion.objects.filter(clase__materia=asign.materia)
                                                    for leccion in leccionesYaDadas:
                                                        asistenciaLeccion = AsistenciaLeccion(leccion=leccion,matricula=matricula,asistio=False)
                                                        asistenciaLeccion.save()
                                                else:
                                                    if not  RecordAcademico.objects.filter(inscripcion=inscripcion,asignatura=asignatura).exists():
                                                        recordPendiente = RecordAcademico(inscripcion=inscripcion,asignatura=asignatura,nota=0,asistencia=0,fecha=datetime.now(),convalidacion=False,aprobada=False,pendiente=True)
                                                        recordPendiente.save()

                                # Crear Rubro
                                if GENERAR_RUBROS_PAGO and not matricula.tipobeneficio==TipoBeneficio.objects.get(pk=TIPO_BECA_SENESCYT) and not inscripcion.beca_senescyt().tienebeca:
                                    if crearubro:
                                        pp = 1.0 if not matricula.becado else ((100-matricula.porcientobeca)/100.0)

                                        #OCastillo 27-04-2023 se excluyen los rubros adicionales de la lista previa ya que no son rubros tipo cuota
                                        # for pago in nivel.pagonivel_set.all():
                                        for pago in nivel.pagonivel_set.all().exclude(tipo__in=lista2):
                                            if pago.tipo==0 or (pago.tipo>0 and pp>0):
                                                rubro = Rubro(fecha=datetime.today().date(),
                                                            valor = pago.valor, inscripcion=inscripcion,
                                                            cancelado = False, fechavence = pago.fecha,tiponivelpago=pago.tipo)

                                                rubro.save()

                                                #Aplica la promocion a todos  los niveles excepto el 1 que lo aplica en la parte de abajo
                                                if matricula.inscripcion.promocion:
                                                    if  pago.tipo!=0 and matricula.inscripcion.promocion.todos_niveles and DEFAULT_PASSWORD == 'itb' and matricula.nivel.nivelmalla.id != NIVEL_MALLA_UNO:
                                                        #OCastillo 20-04-2023 para el caso de todos los niveles asi este inactiva la promocion se mantiene excepto graduacion y seminario
                                                        if matricula.nivel.nivelmalla.id != NIVEL_GRADUACION and matricula.nivel.nivelmalla.id != NIVEL_SEMINARIO:
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

                                                # #OCastillo 02-12-2021 Descuento por convenio empresas
                                                if matricula.inscripcion.descuentoconvenio:
                                                    if matricula.inscripcion.descuentoconvenio and DEFAULT_PASSWORD == 'itb' and pago.tipo!=0:
                                                        descuento = round(((rubro.valor * matricula.inscripcion.descuentoconvenio.descuento)/100),2)
                                                        rubro.valor = rubro.valor - round(((rubro.valor * matricula.inscripcion.descuentoconvenio.descuento)/100),2)
                                                        rubro.save()

                                                        desc = Descuento(inscripcion = inscripcion,
                                                                                  motivo ='DESCUENTO EN CUOTAS',
                                                                                  total = rubro.valor,
                                                                                  fecha = datetime.today().date())
                                                        desc.save()
                                                        detalle = DetalleDescuento(descuento =desc,
                                                                                    rubro =rubro,
                                                                                    valor = descuento,
                                                                                    porcentaje = matricula.inscripcion.descuentoconvenio.descuento)
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
                                                            #OCastillo 04-10-2021 no aplica descuento por grupo que no este marcado
                                                            if inscripcion.grupo().descuento:
                                                                #OCastillo 03-12-2021 se debe excluir de descuento por convenio empresas rubro matricula
                                                                if not inscripcion.descuentoconvenio:
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

                                        # Crear un Rubro de tipo Otro que representara el Recargo (Mora) por matricularse despues de fecha
                                        hoy = datetime.today().date()
                                        if recargo >0:
                                            rubrorecargo = Rubro(fecha=hoy, valor=recargo, inscripcion=inscripcion,
                                                                cancelado=False, fechavence=hoy)
                                            rubrorecargo.save()

                                            OTRO_RUBRO = TipoOtroRubro.objects.get(pk=TIPO_MORA_RUBRO)
                                            descripcion = "MATRICULA EXTRAORDINARIA (" + hoy.strftime('%d-%m-%Y') + ")"
                                            rubrootrorecargo = RubroOtro(rubro=rubrorecargo, tipo=OTRO_RUBRO, descripcion=descripcion)
                                            rubrootrorecargo.save()

                                    else:
                                        # actualizar el id rubro matricual con la nueva matricula
                                        if RubroMatricula.objects.filter(matricula=datomatricu).exists():
                                            for rubromatri in RubroMatricula.objects.filter(matricula=datomatricu):
                                                rubromatri.matricula=matricula
                                                rubromatri.save()
                                        else:
                                            pp = 1.0 if not matricula.becado else ((100-matricula.porcientobeca)/100.0)

                                            for pago in nivel.pagonivel_set.all().exclude(tipo__in=EXCLUIR_TIPO_PAGO):
                                                if pago.tipo==0 or (pago.tipo>0 and pp>0):
                                                    rubro = Rubro(fecha=datetime.today().date(),
                                                                valor = pago.valor, inscripcion=inscripcion,
                                                                cancelado = False, fechavence = pago.fecha,tiponivelpago=pago.tipo)
                                                    rubro.save()

                                                    #Aplica la promocion a todos  los niveles excepto el 1 que lo aplica en la parte de abajo
                                                    if matricula.inscripcion.promocion:
                                                        if  pago.tipo!=0 and matricula.inscripcion.promocion.todos_niveles and DEFAULT_PASSWORD == 'itb' and matricula.nivel.nivelmalla.id != NIVEL_MALLA_UNO:
                                                            #OCastillo 20-04-2023 para el caso de todos los niveles asi este inactiva la promocion se mantiene excepto graduacion y seminario
                                                            if matricula.nivel.nivelmalla.id != NIVEL_GRADUACION and matricula.nivel.nivelmalla.id != NIVEL_SEMINARIO:
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


                                        # actualizar el id rubro cuota
                                        if RubroCuota.objects.filter(matricula=datomatricu).exclude():
                                            for rubrocuotaact in RubroCuota.objects.filter(matricula=datomatricu):

                                                rubrocuotaact.matricula=matricula
                                                rubrocuotaact.save()
                                        else:

                                            pp = 1.0 if not matricula.becado else ((100-matricula.porcientobeca)/100.0)

                                            #OCastillo 27-04-2023 se excluyen los rubros adicionales de la lista previa para no usar ids
                                            # for pago in nivel.pagonivel_set.all().exclude(tipo__in=[13,14]):
                                            for pago in nivel.pagonivel_set.all().exclude(tipo__in=lista2):
                                                if pago.tipo==1 or (pago.tipo>1 and pp>0):
                                                    rubro = Rubro(fecha=datetime.today().date(),
                                                                valor = pago.valor, inscripcion=inscripcion,
                                                                cancelado = False, fechavence = pago.fecha,tiponivelpago=pago.tipo)
                                                    rubro.save()

                                                    #Aplica la promocion a todos  los niveles excepto el 1 que lo aplica en la parte de abajo
                                                    if matricula.inscripcion.promocion:
                                                        if  pago.tipo!=0 and matricula.inscripcion.promocion.todos_niveles and DEFAULT_PASSWORD == 'itb' and matricula.nivel.nivelmalla.id != NIVEL_MALLA_UNO:
                                                            #OCastillo 20-04-2023 para el caso de todos los niveles asi este inactiva la promocion se mantiene excepto graduacion y seminario
                                                            if matricula.nivel.nivelmalla.id != NIVEL_GRADUACION and matricula.nivel.nivelmalla.id != NIVEL_SEMINARIO:
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

                                                    # CUOTA MENSUAL
                                                    rc = RubroCuota(rubro=rubro, matricula=matricula, cuota=pago.tipo)
                                                    rc.save()


                                if matricula.nivel.nivelmalla.id == NIVEL_MALLA_UNO and DEFAULT_PASSWORD == 'itb':
                                    if  Matricula.objects.filter(inscripcion=inscripcion,nivel__nivelmalla__id=NIVEL_MALLA_CERO).exists():
                                        mat =  Matricula.objects.filter(inscripcion=inscripcion,nivel__nivelmalla__id=NIVEL_MALLA_CERO)[:1].get()
                                        # if  mat.becado and inscripcion.tienediscapacidad:
                                        # SE APLICA A TODOS LOS BECADOS 30/06/2017
                                        if  mat.becado :
                                            matricula.becado = True
                                            matricula.porcientobeca = mat.porcientobeca
                                            matricula.tipobeca = mat.tipobeca
                                            matricula.motivobeca  = mat.motivobeca
                                            matricula.tipobeneficio  = mat.tipobeneficio
                                            matricula.fechabeca = datetime.now()
                                            matricula.save()

                                            if GENERAR_RUBROS_PAGO:
                                                pp = (100-matricula.porcientobeca)/100.0

                                                # Aplicar el % de Beca por cada Rubro Real q tenga el estudiante matriculado
                                                for rubro in matricula.inscripcion.rubro_set.all():
                                                    #El tipo Otro es solo para pasar los historicos, luego quitarlo y dejar solo si es cuota
                                                    if rubro.es_cuota() and rubro.total_pagado()==0:
                                                        if pp==0:
                                                            rubro.delete()
                                                        else:
                                                            rubro.valor *= pp
                                                            rubro.save()
                                    for rubro in  matricula.rubrocuota_set.all():
                                        if rubro.rubro.es_cuota() and rubro.rubro.total_pagado()==0:
                                            if matricula.inscripcion.promocion and matricula.inscripcion.promocion.activo:
                                                des = ((100-matricula.inscripcion.descuentoporcent)/100.0)
                                                rubro.rubro.valor *= des
                                                rubro.rubro.save()

                                    #OCastillo 27-04-2023 se crean los rubros adicionales cargados en el plan de pagos del nivel con la lista previa
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


                                #OC 07-febrero-2019 enviar correo a soporte cuando la matricula es en el primer nivel
                                if EMAIL_ACTIVE:
                                    if matricula.nivel.nivelmalla.id == NIVEL_MALLA_UNO and DEFAULT_PASSWORD == 'itb':
                                        hoy = datetime.now().today()
                                        estudiante= elimina_tildes(inscripcion.persona.nombre_completo_inverso())
                                        nivel_matri=matricula.nivel.nivelmalla.nombre
                                        grupo=matricula.nivel.paralelo
                                        carrera=matricula.nivel.carrera.nombre
                                        personarespon = Persona.objects.filter(usuario=request.user)[:1].get()
                                        correo= str('soporteitb@bolivariano.edu.ec')
                                        # correo= ('ocastillo@bolivariano.edu.ec')
                                        correo_inst=str(inscripcion.persona.emailinst)
                                        op='1'

                                        esmunicipio=False
                                        grupomunicipio =Grupo.objects.filter(id__in=LISTA_GRUPO_MUNICIPO)

                                        for grup in grupomunicipio:
                                            if nivel.grupo_id==grup.id:
                                                esmunicipio=True
                                                break

                                        if esmunicipio:

                                            if TipoIncidencia.objects.filter(pk=68).exists():
                                                tipo = TipoIncidencia.objects.filter(pk=68)[:1].get()
                                                correo = tipo.correo

                                            send_html_mail("ESTUDIANTE MATRICULADO A "+nivel_matri+" "+"BECA MUNICIPIO" ,
                                            "emails/correo_matricula_primernivel.html", {'contenido': "ESTUDIANTE MATRICULADO A "+nivel_matri+" "+"BECA MUNICIPIO",'op':op, 'estudiante': estudiante, 'nivel': nivel_matri,'grupo':grupo,'correo_inst':correo_inst,'personarespon': personarespon, 'fecha': hoy,'carrera':carrera},correo.split(','))

                                        else:

                                            send_html_mail("ESTUDIANTE MATRICULADO A PRIMER NIVEL",
                                            "emails/correo_matricula_primernivel.html", {'contenido': "ESTUDIANTE MATRICULADO A PRIMER NIVEL",'op':op, 'estudiante': estudiante, 'nivel': nivel_matri,'grupo':grupo,'correo_inst':correo_inst,'personarespon': personarespon, 'fecha': hoy,'carrera':carrera},correo.split(','))

                                    else:
                                         esmunicipio=False
                                         grupomunicipio =Grupo.objects.filter(id__in=LISTA_GRUPO_MUNICIPO)

                                         for grup in grupomunicipio:
                                            if nivel.grupo_id==grup.id:
                                                esmunicipio=True
                                                break

                                         if esmunicipio:

                                            hoy = datetime.now().today()
                                            estudiante= elimina_tildes(inscripcion.persona.nombre_completo_inverso())
                                            nivel_matri=matricula.nivel.nivelmalla.nombre
                                            grupo=matricula.nivel.paralelo
                                            carrera=matricula.nivel.carrera.nombre
                                            personarespon = Persona.objects.filter(usuario=request.user)[:1].get()

                                            if TipoIncidencia.objects.filter(pk=68).exists():
                                                tipo = TipoIncidencia.objects.filter(pk=68)[:1].get()
                                                correo = tipo.correo

                                            send_html_mail("ESTUDIANTE MATRICULADO A "+nivel_matri+" "+"BECA MUNICIPIO" ,
                                            "emails/correo_matricula_municipio.html", {'contenido': "ESTUDIANTE MATRICULADO A "+nivel_matri+" "+"BECA MUNICIPIO", 'estudiante': estudiante, 'nivel': nivel_matri,'grupo':grupo,'correo_inst':correo_inst,'personarespon': personarespon, 'fecha': hoy,'carrera':carrera},correo.split(','))


                            return HttpResponseRedirect('/matriculas?action=matricula&id='+str(nivel.id))
                        else:
                            return HttpResponseRedirect('/matriculas?action=addmatriculaextra&id='+str(nivel.id)+'&error=2')
                    else:
                        return HttpResponseRedirect('/matriculas?action=addmatriculaextra&id='+str(nivel.id)+'&error=1')

                elif action=='beca':
                    try:
                        if 'p' in request.POST:
                             persona = request.session['persona']
                             matricula = Matricula.objects.get(inscripcion=request.POST['inscripcion'],nivel=request.POST['nivel'])
                             datos = json.loads(request.POST['datos'])



                             matricula.becado = datos['becado']
                             matricula.tipobeneficio_id = datos['tipobeneficio']
                             matricula.porcientobeca = datos['porcientobeca']
                             matricula.tipobeca_id =datos['tipobeca']
                             matricula.motivobeca_id = datos['motivobeca']
                             matricula.fechabeca =convertir_fecha(datos['fechabeca']).date()
                             matricula.observaciones = datos['observaciones']
                             matricula.becaparcial = datos['becaparcial']
                             matricula.save()

                             #OCU Para traer los rubros que se les aplica el descuento y grabarlo en la tabla de detalle
                             # if not matricula.tipobeneficio==TipoBeneficio.objects.get(pk=TIPO_BECA_SENESCYT) and not matricula.porcientobeca == 100:
                             for d in datos['detalle']:
                                rubro = Rubro.objects.get(pk=int(d['rubro']))
                                rubro_anterior = rubro.valor
                                descriprubro = rubro.nombre()
                                rubro.valor= Decimal(rubro.valor) - Decimal(d['valor'])
                                if rubro.valor==0:
                                    indice_rubro = None
                                    rubro.delete()

                                    detalle = DetalleRubrosBeca(matricula=matricula,
                                                           rubro = indice_rubro,
                                                           descripcion=descriprubro,
                                                           descuento = Decimal(d['valor']),
                                                           porcientobeca = Decimal(d['porc']),
                                                           valorrubro=rubro_anterior,
                                                           fecha = datetime.now(),
                                                           usuario = request.user)
                                    detalle.save()

                                else:
                                    indice_rubro = rubro
                                    rubro.save()

                                    detalle = DetalleRubrosBeca(matricula=matricula,
                                                               rubro = indice_rubro,
                                                               descripcion=descriprubro,
                                                               descuento = Decimal(d['valor']),
                                                               porcientobeca = Decimal(d['porc']),
                                                               valorrubro=rubro_anterior,
                                                               fecha = datetime.now(),
                                                               usuario = request.user)
                                    detalle.save()

                             # OCastillo 20-enero-2017 agregar rubros a correo ayuda financiera
                             rubrosaplicados = DetalleRubrosBeca.objects.filter(matricula=matricula)
                             tipo_beca='Beca Parcial a rubros'

                             #Enviar correo
                             # matricula.mail_beca
                             matricula.mail_beca(persona,rubrosaplicados,tipo_beca)

                             if matricula.tipobeneficio==TipoBeneficio.objects.get(pk=1) or  matricula.tipobeneficio==TipoBeneficio.objects.get(pk=3):
                                if SolicitudBeca.objects.filter(inscripcion=matricula.inscripcion,nivel__nivelmalla__id=matricula.nivel.nivelmalla.id,tiposolicitud=1).order_by('-fecha').exists():
                                     if SolicitudBeca.objects.filter(inscripcion=matricula.inscripcion,nivel__nivelmalla__id=matricula.nivel.nivelmalla.id,tiposolicitud=1).order_by('-fecha').exists():
                                            lista = []
                                            solicitudbeca = SolicitudBeca.objects.filter(inscripcion=matricula.inscripcion,nivel__nivelmalla__id=matricula.nivel.nivelmalla.id,tiposolicitud=1).order_by('-fecha')[:1].get()
                                            if solicitudbeca.inscripcion.tienediscapacidad:
                                                lispersona= PersonAutorizaBecaAyuda.objects.filter(personadiscapacidad=True)
                                                for list in lispersona:
                                                    lista.append([list.correo])
                                            else:
                                                lispersona= PersonAutorizaBecaAyuda.objects.filter(personadiscapacidad=True)
                                                for list in lispersona:
                                                    lista.append([list.correo])

                                            lista[0][0]=str(lista[0][0])+','+str('dobe@bolivariano.edu.ec')
                                            solicitudbeca.estadosolicitud=8
                                            solicitudbeca.save()

                                            loshistorial= HistorialGestionBeca(solicitudbeca=solicitudbeca,inscripcion=solicitudbeca.inscripcion,
                                                                                fecha=datetime.now(),estado=9, usuario=request.user,comentariocorreo='BECA APLICADA POR SECRETARIA')
                                            loshistorial.save()
                                            mail_correosolicitudsecretariaaplica(str('BECA APLICADA POR SECRETARIA'), str(lista[0][0]),request.user, elimina_tildes(solicitudbeca.inscripcion.persona.nombre_completo()),elimina_tildes(solicitudbeca.inscripcion.carrera.nombre),solicitudbeca.inscripcion.persona.emailinst,solicitudbeca)





                             #Obtain client ip address
                             client_address = ip_client_address(request)

                             # Log de ADICIONAR BECA PARCIAL
                             LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(matricula).pk,
                                object_id       = matricula.id,
                                object_repr     = force_str(matricula),
                                action_flag     = ADDITION,
                                change_message  = 'Asignada Beca Parcial (' + client_address + ')' )

                             data = {}
                             data['result']='ok'
                             data['urlma']='/matriculas?action=matricula&id='+str(matricula.nivel_id)
                             return HttpResponse(json.dumps(data),content_type="application/json")
                    except Exception as ex:
                            data['result']='bad'
                            return HttpResponse(json.dumps(data),content_type="application/json")

                    else:
                        f = MatriculaBecaForm(request.POST)
                        persona = request.session['persona']

                    if not 'p' in request.POST:
                        matricula = Matricula.objects.get(id=request.POST['id'])

                        solicitudbeca=None
                        if f.is_valid():

                            if f.cleaned_data['tipobeneficio']==TipoBeneficio.objects.get(pk=1) or f.cleaned_data['tipobeneficio']==TipoBeneficio.objects.get(pk=3) or f.cleaned_data['tipobeneficio']==TipoBeneficio.objects.get(pk=2):
                                if f.cleaned_data['tipobeneficio']==TipoBeneficio.objects.get(pk=1) or f.cleaned_data['tipobeneficio']==TipoBeneficio.objects.get(pk=3):
                                    if SolicitudBeca.objects.filter(inscripcion=matricula.inscripcion,nivel__nivelmalla__id=matricula.nivel.nivelmalla.id,tiposolicitud=1).order_by('-fecha').exists():
                                         if SolicitudBeca.objects.filter(inscripcion=matricula.inscripcion,nivel__nivelmalla__id=matricula.nivel.nivelmalla.id,tiposolicitud=1,aprobado=True,aprobacionestudiante=True,asignaciontarficadescuento=True).order_by('-fecha').exists():
                                                lista = []
                                                solicitudbeca = SolicitudBeca.objects.filter(inscripcion=matricula.inscripcion,nivel__nivelmalla__id=matricula.nivel.nivelmalla.id,tiposolicitud=1,aprobado=True,aprobacionestudiante=True).order_by('-fecha')[:1].get()
                                                if solicitudbeca.inscripcion.tienediscapacidad:
                                                    lispersona= PersonAutorizaBecaAyuda.objects.filter(personadiscapacidad=True)
                                                    for list in lispersona:
                                                        lista.append([list.correo])
                                                else:
                                                    lispersona= PersonAutorizaBecaAyuda.objects.filter(personadiscapacidad=True)
                                                    for list in lispersona:
                                                        lista.append([list.correo])

                                                lista[0][0]=str(lista[0][0])+','+str('dobe@bolivariano.edu.ec')
                                                solicitudbeca.estadosolicitud_id=8
                                                solicitudbeca.nivel=matricula.nivel


                                                loshistorial= HistorialGestionBeca(solicitudbeca=solicitudbeca,inscripcion=solicitudbeca.inscripcion,
                                                                                    fecha=datetime.now(),estado_id=9, usuario=request.user,comentariocorreo='BECA APLICADA POR SECRETARIA')
                                                loshistorial.save()

                                                solicitudbeca.idgestion=loshistorial.id

                                                solicitudbeca.save()

                                         else:
                                             data = {}
                                             data['nopuedeaplicarbecanoaprobado']=True
                                             data['matricula'] = matricula
                                             initial = model_to_dict(matricula)
                                             initial.update({'fechabeca': datetime.now()})
                                             data['form'] = MatriculaBecaForm(initial=initial)

                                             data['tipo_ayuda_financiera'] = TIPO_AYUDA_FINANCIERA
                                             data['tipo_beca_senescyt'] = TIPO_BECA_SENESCYT
                                             return render(request ,"matriculas/aplicar_beca.html" ,  data)
                                    else:
                                        data = {}
                                        data['nopuedeaplicarbeca']=True
                                        data['matricula'] = matricula
                                        initial = model_to_dict(matricula)
                                        initial.update({'fechabeca': datetime.now()})
                                        data['form'] = MatriculaBecaForm(initial=initial)

                                        data['tipo_ayuda_financiera'] = TIPO_AYUDA_FINANCIERA
                                        data['tipo_beca_senescyt'] = TIPO_BECA_SENESCYT


                                        return render(request ,"matriculas/aplicar_beca.html" ,  data)
                                else:

                                    if SolicitudBeca.objects.filter(inscripcion=matricula.inscripcion,nivel__nivelmalla__id=matricula.nivel.nivelmalla.id,tiposolicitud=2).order_by('-fecha').exists():
                                         if SolicitudBeca.objects.filter(inscripcion=matricula.inscripcion,nivel__nivelmalla__id=matricula.nivel.nivelmalla.id,tiposolicitud=2,aprobado=True,aprobacionestudiante=True,asignaciontarficadescuento=True).order_by('-fecha').exists():
                                                lista = []
                                                solicitudbeca = SolicitudBeca.objects.filter(inscripcion=matricula.inscripcion,nivel__nivelmalla__id=matricula.nivel.nivelmalla.id,tiposolicitud=2,aprobado=True,aprobacionestudiante=True).order_by('-fecha')[:1].get()
                                                if solicitudbeca.inscripcion.tienediscapacidad:
                                                    lispersona= PersonAutorizaBecaAyuda.objects.filter(personadiscapacidad=True)
                                                    for list in lispersona:
                                                        lista.append([list.correo])
                                                else:
                                                    lispersona= PersonAutorizaBecaAyuda.objects.filter(personadiscapacidad=True)
                                                    for list in lispersona:
                                                        lista.append([list.correo])

                                                lista[0][0]=str(lista[0][0])+','+str('dobe@bolivariano.edu.ec')
                                                solicitudbeca.estadosolicitud_id=8
                                                solicitudbeca.nivel=matricula.nivel


                                                loshistorial= HistorialGestionAyudaEconomica(solicitudbeca=solicitudbeca,inscripcion=solicitudbeca.inscripcion,
                                                                                    fecha=datetime.now(),estado_id=9, usuario=request.user,comentariocorreo='BECA APLICADA POR SECRETARIA')
                                                loshistorial.save()

                                                solicitudbeca.idgestion=loshistorial.id

                                                solicitudbeca.save()

                                         else:
                                             data = {}
                                             data['nopuedeaplicarbecanoaprobado']=True
                                             data['matricula'] = matricula
                                             initial = model_to_dict(matricula)
                                             initial.update({'fechabeca': datetime.now()})
                                             data['form'] = MatriculaBecaForm(initial=initial)

                                             data['tipo_ayuda_financiera'] = TIPO_AYUDA_FINANCIERA
                                             data['tipo_beca_senescyt'] = TIPO_BECA_SENESCYT
                                             return render(request ,"matriculas/aplicar_beca.html" ,  data)
                                    else:
                                        data = {}
                                        data['nopuedeaplicarbeca']=True
                                        data['matricula'] = matricula
                                        initial = model_to_dict(matricula)
                                        initial.update({'fechabeca': datetime.now()})
                                        data['form'] = MatriculaBecaForm(initial=initial)

                                        data['tipo_ayuda_financiera'] = TIPO_AYUDA_FINANCIERA
                                        data['tipo_beca_senescyt'] = TIPO_BECA_SENESCYT


                                        return render(request ,"matriculas/aplicar_beca.html" ,  data)




                            matricula.becado = f.cleaned_data['becado']
                            matricula.tipobeneficio = f.cleaned_data['tipobeneficio']
                            matricula.porcientobeca = f.cleaned_data['porcientobeca']
                            matricula.tipobeca = f.cleaned_data['tipobeca']
                            matricula.motivobeca = f.cleaned_data['motivobeca']
                            matricula.fechabeca = f.cleaned_data['fechabeca']
                            matricula.observaciones = f.cleaned_data['observaciones']
                            matricula.becaparcial = f.cleaned_data['becaparcial']
                            matricula.save()

                        #Si es BECA SENESCYT no se pueden crear Rubros y se deben borrar todos los Rubros sin saldos si tiene
                        if matricula.tipobeneficio==TipoBeneficio.objects.get(pk=TIPO_BECA_SENESCYT):
                            #Enviar correo
                            matricula.mail_beca_senescyt(persona)
                            if  matricula.porcientobeca == 100:
                                # Borrarle los rubros sin abono y el que haya abonado cancelado en True
                                # for rubro in matricula.inscripcion.rubro_set.filter(cancelado=False):
                                    # if rubro.total_pagado()>0:
                                    #     rubro.valor = rubro.total_pagado()
                                    #     rubro.cancelado = True
                                    #     rubro.save()
                                    #     indice_rubro = rubro.id
                                rmat = matricula.rubromatricula_set.all()
                                rcuot = matricula.rubrocuota_set.all()
                                # Rubros de matricula en Beca Senescyt OCU 23-oct-2017
                                for rm in rmat:
                                    if rm.rubro.puede_eliminarse():
                                        descriprubro=rm.rubro.nombre() + " BECA SENESCYT"
                                        rubro_anterior = rm.rubro.valor
                                        descuento= rm.rubro.valor
                                        indice_rubro = None
                                        # OCU grabo los rubros modificados en la tabla de detalle Beca 100%
                                        detalle = DetalleRubrosBeca(matricula=matricula,
                                                  rubro = indice_rubro,
                                                  descripcion=descriprubro,
                                                  descuento = descuento,
                                                  porcientobeca = matricula.porcientobeca,
                                                  valorrubro=rubro_anterior,
                                                  fecha = datetime.now(),
                                                  usuario = request.user)
                                        detalle.save()
                                        rm.rubro.delete()

                                # Rubros de cuotas en Beca Senescyt OCU 23-oct-2017
                                for rc in rcuot:
                                    if rc.rubro.puede_eliminarse():
                                        descriprubro=rc.rubro.nombre() + " BECA SENESCYT"
                                        rubro_anterior = rc.rubro.valor
                                        descuento= rc.rubro.valor
                                        indice_rubro = None

                                        # OCU grabo los rubros modificados en la tabla de detalle Beca 100%
                                        detalle = DetalleRubrosBeca(matricula=matricula,
                                                  rubro = indice_rubro,
                                                  descripcion=descriprubro,
                                                  descuento = descuento,
                                                  porcientobeca = matricula.porcientobeca,
                                                  valorrubro=rubro_anterior,
                                                  fecha = datetime.now(),
                                                  usuario = request.user)
                                        detalle.save()
                                        rc.rubro.delete()

                            else:
                            # ReCalcular Rubros en funcion del porciento de Beca aplicado
                                if GENERAR_RUBROS_PAGO:
                                    pp = (100-matricula.porcientobeca)/100.0
                                    rmat = matricula.rubromatricula_set.all()
                                    rcuot = matricula.rubrocuota_set.all()

                                    # Aplicar el % de Beca por cada Rubro Real q tenga el estudiante matriculado
                                    # for rubro in matricula.inscripcion.rubro_set.all():
                                    #El tipo Otro es solo para pasar los historicos, luego quitarlo y dejar solo si es cuota
                                    # Rubros de matricula Beca Senescyt de diferente porcentaje OCU 23-oct-2017
                                    for rm in rmat:
                                        if rm.rubro.puede_eliminarse():
                                            descriprubro=rm.rubro.nombre()
                                            rubro_anterior = rm.rubro.valor
                                            indice_rubro = rm.rubro.id
                                            rm.rubro.valor *= pp
                                            descuento= rubro_anterior - rm.rubro.valor
                                            rm.rubro.save()

                                            # if rubro.es_cuota() and rubro.total_pagado()==0:
                                            # if pp==0:
                                            #     rubro.delete()
                                            # OCU grabo los rubros modificados en la tabla de detalle Beca
                                            detalle = DetalleRubrosBeca(matricula=matricula,
                                                      rubro_id = indice_rubro,
                                                      descripcion=descriprubro,
                                                      descuento = descuento,
                                                      porcientobeca = matricula.porcientobeca,
                                                      valorrubro=rubro_anterior,
                                                      fecha = datetime.now(),
                                                      usuario = request.user)
                                            detalle.save()

                                    # Rubros de cuotas en Beca Senescyt de diferente porcentaje OCU 23-oct-2017
                                    for rc in rcuot:
                                        if rc.rubro.puede_eliminarse():
                                            descriprubro=rc.rubro.nombre()
                                            rubro_anterior = rc.rubro.valor
                                            indice_rubro = rc.rubro.id
                                            rc.rubro.valor *= pp
                                            descuento= rubro_anterior - rc.rubro.valor
                                            rc.rubro.save()

                                            # OCU grabo los rubros modificados en la tabla de detalle Beca
                                            detalle = DetalleRubrosBeca(matricula=matricula,
                                                      rubro_id = indice_rubro,
                                                      descripcion=descriprubro,
                                                      descuento = descuento,
                                                      porcientobeca = matricula.porcientobeca,
                                                      valorrubro=rubro_anterior,
                                                      fecha = datetime.now(),
                                                      usuario = request.user)
                                            detalle.save()

                            # Correo detalle de rubros aplicados Beca Senescyt OCU 23-oct-2017
                            rubrosaplicados = DetalleRubrosBeca.objects.filter(matricula=matricula)
                            tipo_beca='Beca a todos los rubros'
                            matricula.mail_beca(persona,rubrosaplicados,tipo_beca)

                            #Obtain client ip address
                            client_address = ip_client_address(request)

                            # Log de ADICIONAR BECA SENESCYT
                            LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(matricula).pk,
                                object_id       = matricula.id,
                                object_repr     = force_str(matricula),
                                action_flag     = ADDITION,
                                change_message  = 'Asignada Beca Senescyt (' + client_address + ')' )

                            return HttpResponseRedirect('/matriculas?action=matricula&id='+str(matricula.nivel_id))

                        else:
                            # ReCalcular Rubros en funcion del porciento de Beca aplicado
                            if GENERAR_RUBROS_PAGO:
                                pp = (100-matricula.porcientobeca)/100.0

                                # Aplicar el % de Beca por cada Rubro Real q tenga el estudiante matriculado
                                # for rubro in matricula.inscripcion.rubro_set.all():
                                #El tipo Otro es solo para pasar los historicos, luego quitarlo y dejar solo si es cuota
                                # if rubro.es_cuota() and rubro.total_pagado()==0:
                                        #     descriprubro=rubro.nombre()
                                        # if pp==0:
                                        #     rubro_anterior = rubro.valor
                                        #     descuento = rubro.valor
                                        #     indice_rubro = ''
                                        #     rubro.delete()

                                #OCU 24-oct-2017 Ojo queda programado para el caso de aplicar a matricula, para los otros tipos de beca
                                # rmat = matricula.rubromatricula_set.all()
                                # for rm in rmat:
                                #     if rm.rubro.puede_eliminarse():
                                #         descriprubro=rm.rubro.nombre()
                                #         rubro_anterior = rm.rubro.valor
                                #         indice_rubro = rm.rubro.id
                                #         rm.rubro.valor *= pp
                                #         descuento= rubro_anterior - rm.rubro.valor
                                #         rm.rubro.save()
                                #
                                #         # OCU grabo los rubros modificados en la tabla de detalle
                                #         detalle = DetalleRubrosBeca(matricula=matricula,
                                #                    rubro_id = indice_rubro,
                                #                    descripcion=descriprubro,
                                #                    descuento = descuento,
                                #                    porcientobeca = matricula.porcientobeca,
                                #                    valorrubro=rubro_anterior,
                                #                    fecha = datetime.now(),
                                #                    usuario = request.user)
                                #         detalle.save()
                                rubrotodo= Rubro.objects.filter(inscripcion=matricula.inscripcion,cancelado=False).values_list('id')
                                ruboincrip= RubroInscripcion.objects.filter(rubro__id__in=rubrotodo)
                                rcuot = matricula.rubrocuota_set.all()
                                rmat = matricula.rubromatricula_set.all()
                                if f.cleaned_data['tipobeneficio']==TipoBeneficio.objects.get(pk=1) or f.cleaned_data['tipobeneficio']==TipoBeneficio.objects.get(pk=3) or f.cleaned_data['tipobeneficio']==TipoBeneficio.objects.get(pk=2):
                                    if solicitudbeca:
                                        tabladescuentobeca=TablaDescuentoBeca.objects.filter(solicitudbeca=solicitudbeca)
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

                                            for rm in rmat:
                                                if not DetalleRubrosBeca.objects.filter(rubro=rm.rubro).exists():
                                                     for tbdes in tabladescuentobeca:
                                                      if rm.rubro.id == tbdes.rubro.id:
                                                        pp = (100-tbdes.descuento)/100.0
                                                        if rm.rubro.puede_eliminarse():
                                                            descriprubro=rm.rubro.nombre()
                                                            rubro_anterior = rm.rubro.valor
                                                            indice_rubro = rm.rubro.id
                                                            rm.rubro.valor *= pp
                                                            descuento= rubro_anterior - rm.rubro.valor
                                                            rm.rubro.save()

                                                            # if rubro.es_cuota() and rubro.total_pagado()==0:
                                                            # if pp==0:
                                                            #     rubro.delete()
                                                            # OCU grabo los rubros modificados en la tabla de detalle Beca
                                                            detalle = DetalleRubrosBeca(matricula=matricula,
                                                                      rubro_id = indice_rubro,
                                                                      descripcion=descriprubro,
                                                                      descuento = descuento,
                                                                      porcientobeca = matricula.porcientobeca,
                                                                      valorrubro=rubro_anterior,
                                                                      fecha = datetime.now(),
                                                                      usuario = request.user)
                                                            detalle.save()

                                            for rinsp in ruboincrip:

                                                if not DetalleRubrosBeca.objects.filter(rubro=rinsp.rubro).exists():
                                                     for tbdes in tabladescuentobeca:
                                                      if rinsp.rubro.id == tbdes.rubro.id:
                                                        pp = (100-tbdes.descuento)/100.0
                                                        if rinsp.rubro.puede_eliminarse():
                                                            descriprubro=rinsp.rubro.nombre()
                                                            rubro_anterior = rinsp.rubro.valor
                                                            indice_rubro = rinsp.rubro.id
                                                            rinsp.rubro.valor *= pp
                                                            descuento= rubro_anterior - rinsp.rubro.valor
                                                            rinsp.rubro.save()

                                                            # if rubro.es_cuota() and rubro.total_pagado()==0:
                                                            # if pp==0:
                                                            #     rubro.delete()
                                                            # OCU grabo los rubros modificados en la tabla de detalle Beca
                                                            detalle = DetalleRubrosBeca(matricula=matricula,
                                                                      rubro_id = indice_rubro,
                                                                      descripcion=descriprubro,
                                                                      descuento = descuento,
                                                                      porcientobeca = matricula.porcientobeca,
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

                                            for rm in rmat:
                                                if not DetalleRubrosBeca.objects.filter(rubro=rm.rubro).exists():
                                                    if rm.rubro.puede_eliminarse():
                                                        descriprubro=rm.rubro.nombre()
                                                        rubro_anterior = rm.rubro.valor
                                                        indice_rubro = rm.rubro.id
                                                        rm.rubro.valor *= pp
                                                        descuento= rubro_anterior - rm.rubro.valor
                                                        rm.rubro.save()

                                                        # if rubro.es_cuota() and rubro.total_pagado()==0:
                                                        # if pp==0:
                                                        #     rubro.delete()
                                                        # OCU grabo los rubros modificados en la tabla de detalle Beca
                                                        detalle = DetalleRubrosBeca(matricula=matricula,
                                                                  rubro_id = indice_rubro,
                                                                  descripcion=descriprubro,
                                                                  descuento = descuento,
                                                                  porcientobeca = matricula.porcientobeca,
                                                                  valorrubro=rubro_anterior,
                                                                  fecha = datetime.now(),
                                                                  usuario = request.user)
                                                        detalle.save()


                                            for rinsp in ruboincrip:
                                                if not DetalleRubrosBeca.objects.filter(rubro=rinsp.rubro).exists():
                                                    if rinsp.rubro.puede_eliminarse():
                                                        descriprubro=rinsp.rubro.nombre()
                                                        rubro_anterior = rinsp.rubro.valor
                                                        indice_rubro = rinsp.rubro.id
                                                        rinsp.rubro.valor *= pp
                                                        descuento= rubro_anterior - rinsp.rubro.valor
                                                        rinsp.rubro.save()

                                                        # if rubro.es_cuota() and rubro.total_pagado()==0:
                                                        # if pp==0:
                                                        #     rubro.delete()
                                                        # OCU grabo los rubros modificados en la tabla de detalle Beca
                                                        detalle = DetalleRubrosBeca(matricula=matricula,
                                                                  rubro_id = indice_rubro,
                                                                  descripcion=descriprubro,
                                                                  descuento = descuento,
                                                                  porcientobeca = matricula.porcientobeca,
                                                                  valorrubro=rubro_anterior,
                                                                  fecha = datetime.now(),
                                                                  usuario = request.user)
                                                        detalle.save()


                                        mail_correosolicitudsecretariaaplica(str('BECA APLICADA POR SECRETARIA'), str(lista[0][0]),request.user, elimina_tildes(solicitudbeca.inscripcion.persona.nombre_completo()),elimina_tildes(solicitudbeca.inscripcion.carrera.nombre),solicitudbeca.inscripcion.persona.emailinst,solicitudbeca)

                                else:
                                            # rc.rubro.delete()
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

                                    for rm in rmat:
                                        if not DetalleRubrosBeca.objects.filter(rubro=rm.rubro).exists():
                                            if rm.rubro.puede_eliminarse():
                                                descriprubro=rm.rubro.nombre()
                                                rubro_anterior = rm.rubro.valor
                                                indice_rubro = rm.rubro.id
                                                rm.rubro.valor *= pp
                                                descuento= rubro_anterior - rm.rubro.valor
                                                rm.rubro.save()

                                                # if rubro.es_cuota() and rubro.total_pagado()==0:
                                                # if pp==0:
                                                #     rubro.delete()
                                                # OCU grabo los rubros modificados en la tabla de detalle Beca
                                                detalle = DetalleRubrosBeca(matricula=matricula,
                                                          rubro_id = indice_rubro,
                                                          descripcion=descriprubro,
                                                          descuento = descuento,
                                                          porcientobeca = matricula.porcientobeca,
                                                          valorrubro=rubro_anterior,
                                                          fecha = datetime.now(),
                                                          usuario = request.user)
                                                detalle.save()

                                    for rinsp in ruboincrip:

                                           if not DetalleRubrosBeca.objects.filter(rubro=rinsp.rubro).exists():
                                            if rinsp.rubro.puede_eliminarse():
                                                descriprubro=rinsp.rubro.nombre()
                                                rubro_anterior = rinsp.rubro.valor
                                                indice_rubro = rinsp.rubro.id
                                                rinsp.rubro.valor *= pp
                                                descuento= rubro_anterior - rinsp.rubro.valor
                                                rinsp.rubro.save()

                                                # if rubro.es_cuota() and rubro.total_pagado()==0:
                                                # if pp==0:
                                                #     rubro.delete()
                                                # OCU grabo los rubros modificados en la tabla de detalle Beca
                                                detalle = DetalleRubrosBeca(matricula=matricula,
                                                          rubro_id = indice_rubro,
                                                          descripcion=descriprubro,
                                                          descuento = descuento,
                                                          porcientobeca = matricula.porcientobeca,
                                                          valorrubro=rubro_anterior,
                                                          fecha = datetime.now(),
                                                          usuario = request.user)
                                                detalle.save()



                        #Enviar correo al Dobe
                        if matricula.tipobeneficio==TipoBeneficio.objects.get(pk=TIPO_AYUDA_FINANCIERA) and EMAIL_ACTIVE:

                            # OCastillo 19-enero-2017 agregar rubros a correo ayuda financiera
                            rubrosaplicados = DetalleRubrosBeca.objects.filter(matricula=matricula)
                            tipo_beca='Beca a todos los rubros'

                            #Enviar correo
                            # matricula.mail_ayuda_financiera(persona)
                            matricula.mail_ayuda_financiera(persona,rubrosaplicados,tipo_beca)

                            #Obtain client ip address
                            client_address = ip_client_address(request)

                            # Log de ADICIONAR Ayuda Financiera
                            LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(matricula).pk,
                                object_id       = matricula.id,
                                object_repr     = force_str(matricula),
                                action_flag     = ADDITION,
                                change_message  = 'Asignada Ayuda Financiera (' + client_address + ')' )

                        else:
                            # matricula.mail_beca(persona)
                            # OCastillo 19-enero-2017 agregar rubros a correo ayuda financiera
                            rubrosaplicados = DetalleRubrosBeca.objects.filter(matricula=matricula)
                            tipo_beca='Beca a todos los rubros'

                            #Enviar correo
                            # matricula.mail_beca
                            matricula.mail_beca(persona,rubrosaplicados,tipo_beca)

                            #Obtain client ip address
                            client_address = ip_client_address(request)

                            # Log de ADICIONAR BECA NORMAL
                            LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(matricula).pk,
                                object_id       = matricula.id,
                                object_repr     = force_str(matricula),
                                action_flag     = ADDITION,
                                change_message  = 'Asignada Beca (' + client_address + ')' )

                        return HttpResponseRedirect('/matriculas?action=matricula&id='+str(matricula.nivel_id))
                    else:
                        return HttpResponseRedirect('/matriculas')


                elif action=='editmatricula':
                    matricula = Matricula.objects.get(pk=request.POST['id'])
                    f = MatriculaEditForm(request.POST)
                    persona = request.session['persona']
                    if f.is_valid():
                        matricula.nivel = f.cleaned_data['nivel']
                        matricula.pago = f.cleaned_data['pago']
                        matricula.iece = f.cleaned_data['iece']
                        matricula.becado = f.cleaned_data['becado']
                        matricula.porcientobeca = f.cleaned_data['porcientobeca']
                        matricula.tipobeca = f.cleaned_data['tipobeca']
                        matricula.motivobeca = f.cleaned_data['motivobeca']
                        matricula.tipobeneficio = f.cleaned_data['tipobeneficio']
                        matricula.observaciones = f.cleaned_data['observaciones']
                        matricula.save()

                        #Actualizar el registro de InscripcionMalla con la malla correspondiente
                        im = matricula.inscripcion.malla_inscripcion()
                        im.malla = matricula.nivel.malla
                        im.save()

                        #Si es becado entonces verificar q tipo de Beneficio es, para aplicar Nota de Credito o Porcientos de descuentos en Rubros
                        if matricula.becado and MODULO_FINANZAS_ACTIVO:
                        #Si es BECA SENESCYT no se pueden crear Rubros y se deben borrar todos los Rubros sin saldos si tiene
                            if matricula.tipobeneficio==TipoBeneficio.objects.get(pk=TIPO_BECA_SENESCYT):
                                for rubro in matricula.inscripcion.rubro_set.filter(cancelado=False):
                                    if rubro.total_pagado()>0:
                                        rubro.valor = rubro.total_pagado()
                                        rubro.cancelado = True
                                        rubro.save()
                                    else:
                                        rubro.delete()
                            else:
                                # ReCalcular Rubros en funcion del porciento de Beca aplicado
                                if GENERAR_RUBROS_PAGO:
                                    pp = (100-matricula.porcientobeca)/100.0

                                    # Aplicar el % de Beca por cada Rubro Real q tenga el estudiante matriculado
                                    for rubro in matricula.inscripcion.rubro_set.all():
                                        #El tipo Otro es solo para pasar los historicos, luego quitarlo y dejar solo si es cuota
                                        if rubro.es_cuota() and rubro.total_pagado()==0:
                                            if pp==0:
                                                rubro.delete()
                                            else:
                                                rubro.valor *= pp
                                                rubro.save()

                                    #Enviar correo al Dobe
                                    if matricula.tipobeneficio==TipoBeneficio.objects.get(pk=TIPO_AYUDA_FINANCIERA) and EMAIL_ACTIVE:
                                        matricula.mail_ayuda_financiera(persona)
                                    else:
                                        matricula.mail_beca(persona)

                        return HttpResponseRedirect("/matriculas?action=matricula&id="+str(matricula.nivel_id))
                    else:
                        return HttpResponseRedirect("/matriculas?action=editmatricula&id="+request.POST['id'])

                elif action=='delmateria':
                    materiaasignada = MateriaAsignada.objects.get(pk=request.POST['id'])
                    # if materiaasignada.obtener_rubroespecie_asentamientonotas():
                    if RubroEspecieValorada.objects.filter(materia=materiaasignada).exists():
                        especie = RubroEspecieValorada.objects.filter(materia=materiaasignada)[:1].get()
                        mensaje='tiene especie pendiente (' + str(especie.serie)  + ')'
                        return HttpResponse(json.dumps({'result': 'bad', 'mensaje': str(mensaje)}),content_type="application/json")
                    matricula = materiaasignada.matricula

                    # Log de ELIMINAR MATERIA ASIGNADA
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(materiaasignada).pk,
                        object_id       = materiaasignada.id,
                        object_repr     = force_str(materiaasignada),
                        action_flag     = DELETION,
                        change_message  = 'Eliminada Materia Asignada - '+str(materiaasignada.materia.id)+ ' - '+elimina_tildes(matricula.inscripcion.persona.nombre_completo_inverso()))

                    if materiaasignada.materiaenplan12_set.exists():
                        mp = materiaasignada.materiaenplan12_set.all()[:1].get()
                        plan = mp.plan
                        plan.materiascursadas = plan.materiascursadas - 1
                        plan.save()


                    materiaasignada.delete()
                    return HttpResponse(json.dumps({'result': 'ok'}), content_type="application/json")
                    # return HttpResponseRedirect("/matriculas?action=materias&id="+str(matricula.id))

                elif action=='demote':
                    materiaAsignada = MateriaAsignada.objects.get(pk=request.POST['id'])
                    matriculaid = materiaAsignada.matricula.id
                    # if materiaAsignada.ver_especienotas():
                    if RubroEspecieValorada.objects.filter(materia=materiaAsignada).exists():
                        especie = RubroEspecieValorada.objects.filter(materia=materiaAsignada)[:1].get()
                        mensaje = 'tiene especie relacionada (' + str(especie.serie) + ')'
                        return HttpResponse(json.dumps({'result': 'bad', 'mensaje': str(mensaje)}),content_type="application/json")
                    if not RecordAcademico.objects.filter(inscripcion=materiaAsignada.matricula.inscripcion, asignatura=materiaAsignada.materia.asignatura).exists():
                        record = RecordAcademico(inscripcion=materiaAsignada.matricula.inscripcion,
                                                asignatura=materiaAsignada.materia.asignatura,
                                                nota=0,
                                                asistencia=0,
                                                fecha=datetime.now(),
                                                convalidacion=False,
                                                aprobada=False,
                                                pendiente=True)
                        record.save()

                    # Log de DEJAR PENDIENTE MATERIA ASIGNADA
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(materiaAsignada).pk,
                        object_id       = materiaAsignada.id,
                        object_repr     = force_str(materiaAsignada),
                        action_flag     = DELETION,
                        change_message  = 'Pasada a Pendiente Materia')

                    if materiaAsignada.materiaenplan12_set.exists():
                        mp = materiaAsignada.materiaenplan12_set.all()[:1].get()
                        plan = mp.plan
                        plan.materiascursadas = plan.materiascursadas - 1
                        plan.save()

                    materiaAsignada.delete()
                    # return HttpResponseRedirect("/matriculas?action=materias&id="+str(matriculaid))
                    return HttpResponse(json.dumps({'result': 'ok'}),content_type="application/json")

                elif action=='delmatricula':
                    if Matricula.objects.filter(pk=request.POST['id']).exists():
                        matricula = Matricula.objects.get(pk=request.POST['id'])
                        id_matricula=matricula.id
                        asignadas = matricula.materiaasignada_set.all()
                        inscripcion = matricula.inscripcion
                        eliminacion=''

                        f = EliminacionMatriculaForm(request.POST)
                        if f.is_valid():
                            if not EliminacionMatricula.objects.filter(inscripcion=inscripcion,nivel=matricula.nivel,fecha=f.cleaned_data['fecha']).exists():
                                eliminacion = EliminacionMatricula(inscripcion=inscripcion, nivel=matricula.nivel,
                                                                   fecha=f.cleaned_data['fecha'],
                                                                   motivo=f.cleaned_data['motivo'])
                                eliminacion.save()

                            for materiaAsignada in asignadas:
                                if materiaAsignada.notafinal>0:
                                    #OCastillo 23-06-2020 se omite esta parte porque afeta en el promedio al aplicar beca
                                    #record = RecordAcademico(inscripcion=inscripcion,asignatura=materiaAsignada.materia.asignatura,
                                    #                    nota=materiaAsignada.notafinal,asistencia=materiaAsignada.asistenciafinal,fecha=datetime.now(),
                                    #                    convalidacion=False, aprobada=(materiaAsignada.notafinal >= NOTA_PARA_APROBAR), pendiente=(materiaAsignada.notafinal==0))
                                    #record.save()
                                    #historico = HistoricoRecordAcademico(inscripcion=inscripcion, asignatura=materiaAsignada.materia.asignatura,
                                    #                    nota=materiaAsignada.notafinal, asistencia=materiaAsignada.asistenciafinal,fecha=datetime.now(),
                                    #                    convalidacion=False, aprobada=(materiaAsignada.notafinal >= NOTA_PARA_APROBAR), pendiente=(materiaAsignada.notafinal==0))
                                    #historico.save()
                                    detalle = DetalleEliminaMatricula(eliminadamatriculada=eliminacion,
                                                                      asignatura=materiaAsignada.materia.asignatura,
                                                                      n1 = materiaAsignada.evaluacion_itb().n1,
                                                                      n2 = materiaAsignada.evaluacion_itb().n2,
                                                                      n3 = materiaAsignada.evaluacion_itb().n3,
                                                                      n4 = materiaAsignada.evaluacion_itb().n4,
                                                                      examen = materiaAsignada.evaluacion_itb().examen,
                                                                      recuperacion = materiaAsignada.evaluacion_itb().recuperacion,
                                                                      notafinal = materiaAsignada.notafinal,
                                                                      asistenciafinal = materiaAsignada.asistenciafinal,
                                                                      fecha=datetime.now(),
                                                                      usuario=request.user)
                                    detalle.save()


                            nivelid = matricula.nivel_id
                            inscripcion = matricula.inscripcion
                            for record in inscripcion.recordacademico_set.all():
                                if record.esta_pendiente():
                                    record.delete()

                            # validar que tenga y que tenga ingresado los rubro de descuento
                            solicitudbeca=None

                            if SolicitudBeca.objects.filter(nivel__nivelmalla__id=matricula.nivel.nivelmalla.id,inscripcion=matricula.inscripcion,tiposolicitud__in=LISTA_TIPO_BECA).exists():
                                if SolicitudBeca.objects.filter(inscripcion=matricula.inscripcion,nivel__nivelmalla__id=matricula.nivel.nivelmalla.id,tiposolicitud=1).order_by('-fecha').exists():
                                    solicitudbeca = SolicitudBeca.objects.filter(inscripcion=matricula.inscripcion,nivel__nivelmalla__id=matricula.nivel.nivelmalla.id,tiposolicitud=1).order_by('-fecha')[:1].get()
                                else:
                                    solicitudbeca = SolicitudBeca.objects.filter(inscripcion=matricula.inscripcion,nivel__nivelmalla__id=matricula.nivel.nivelmalla.id,tiposolicitud=2).order_by('-fecha')[:1].get()

                            if solicitudbeca:
                                if TablaDescuentoBeca.objects.filter(solicitudbeca=solicitudbeca).exists():
                                    tabladescuentobeca=TablaDescuentoBeca.objects.filter(solicitudbeca=solicitudbeca)
                                    # actulizar el id del rubro para que no se elimine
                                    if tabladescuentobeca:
                                          for tbdes in tabladescuentobeca:
                                              tbdes.rubro=None
                                              tbdes.save()


                            # Corregir Rubros de existir

                            rmat = matricula.rubromatricula_set.all()
                            rcuot = matricula.rubrocuota_set.all()

                            if MODELO_EVALUACION==EVALUACION_CASADE:
                                OTRO_RUBRO = TipoOtroRubro.objects.get(pk=2)

                            else:
                                OTRO_RUBRO = TipoOtroRubro.objects.get(pk=TIPO_OTRO_RUBRO)

                            for r in rmat:
                                if not r.rubro.puede_eliminarse():
                                    if matricula.inscripcion.promocion and matricula.nivel.nivelmalla.id == NIVEL_MALLA_CERO and DEFAULT_PASSWORD == 'itb':
                                        if matricula.inscripcion.promocion.directo:
                                            ro = RubroOtro(rubro=r.rubro, tipo=OTRO_RUBRO, descripcion=r.rubro.nombre())
                                            ro.save()
                                        else:
                                            ro = RubroOtro(rubro=r.rubro, tipo=OTRO_RUBRO, descripcion=r.rubro.nombre()+" (MATRICULA BORRADA)")
                                            ro.save()
                                    else:
                                        ro = RubroOtro(rubro=r.rubro, tipo=OTRO_RUBRO, descripcion=r.rubro.nombre()+" (MATRICULA BORRADA)")
                                        ro.save()
                                else:
                                    if matricula.inscripcion.promocion and matricula.nivel.nivelmalla.id == NIVEL_MALLA_CERO and DEFAULT_PASSWORD == 'itb':
                                        if matricula.inscripcion.promocion.directo:
                                            ro = RubroOtro(rubro=r.rubro, tipo=OTRO_RUBRO, descripcion=r.rubro.nombre())
                                            ro.save()
                                        else:
                                            rubro = r.rubro
                                            rubro.delete()
                                    else:
                                        rubro = r.rubro
                                        rubro.delete()

                            for r in rcuot:
                                if not r.rubro.puede_eliminarse():
                                    ro = RubroOtro(rubro=r.rubro, tipo=OTRO_RUBRO, descripcion=r.rubro.nombre()+" (MATRICULA BORRADA)")
                                    ro.save()
                                else:
                                    try:
                                        rubro = r.rubro
                                        rubro.delete()
                                    except Exception as ex:
                                        pass

                            # eliminar rubro 13 y 14 si tienen
                            #OCastillo 26-04-2023 se eliminan los rubros extra en el nivel correspondientes a la matricula
                            lista2=[]
                            for pn in TIPOS_PAGO_NIVEL:
                                if not 'CUOTA' in pn[1] and not  'MATRICULA' in pn[1] :
                                    lista2.append(pn[0])
                            rotrorubro=None
                            if Rubro.objects.filter(inscripcion=inscripcion,tiponivelpago__in=lista2).exists():
                                rotrorubro= Rubro.objects.filter(inscripcion=inscripcion,tiponivelpago__in=lista2)

                            if rotrorubro:
                                for rotro in rotrorubro:
                                    if not rotro.puede_eliminarse():
                                        if RubroOtro.objects.filter(rubro=rotro,matricula=id_matricula).exists():
                                            ro = RubroOtro.objects.get(rubro=rotro,matricula=id_matricula)
                                            ro.descripcion=rotro.nombre()+" (MATRICULA BORRADA)"
                                            ro.save()
                                    else:
                                        try:
                                            rubro = rotro
                                            rubro.delete()
                                        except Exception as ex:
                                            pass


                            #Obtain client ip address
                            client_address = ip_client_address(request)

                            # Log de ELIMINAR MATRICULA
                            LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(matricula).pk,
                                object_id       = matricula.id,
                                object_repr     = force_str(matricula),
                                action_flag     = DELETION,
                                change_message  = 'Eliminada Matricula (' + client_address + ')' )

                            eliminacion = EliminacionMatricula(inscripcion=inscripcion, nivel=matricula.nivel, fecha=f.cleaned_data['fecha'], motivo=f.cleaned_data['motivo'])
                            eliminacion.save()

                            if MateriaAsignada.objects.filter(matricula=matricula).exists():
                                ids = MateriaAsignada.objects.filter(matricula=matricula).values('id')
                                for r in RubroEspecieValorada.objects.filter(materia__id__in=ids):
                                    r.materia = None
                                    r.save()
                            matricula.delete()

                            return HttpResponseRedirect("/matriculas?action=matricula&id="+str(nivelid))





                elif action=='retirar_matricula':
                    try:
                        matricula = Matricula.objects.get(pk=request.POST['id'])
                        #OCastillo 27-03-2020 se quita valicacion de especie
                        if not request.POST['especie']:
                            especie=0
                        else:
                            especie = request.POST['especie']
                        codigo = request.POST['codigoe']
                        motivo = request.POST['motivo']
                        fecha = request.POST['fecha']
                        datos = json.loads(request.POST['datos'])
                        asignadas = matricula.materiaasignada_set.all()
                        hoy = datetime.now().date()
                        if  RubroEspecieValorada.objects.filter(serie=especie,rubro__inscripcion=matricula.inscripcion,aplicada=False).exists():
                            #OCastillo 27-03-2020 se quita valicacion de especie
                            #if not DetalleRetiradoMatricula.objects.filter(especie=especie,fecha__year=hoy.year).exists():
                            if not DetalleRetiradoMatricula.objects.filter(retirado__inscripcion=matricula.inscripcion,retirado__activo=True).exists():
                                for materiaAsignada in asignadas:
                                    evaluacion = materiaAsignada.evaluacion_itb()
                                    #OCastillo 03-08-2020 se pasan notas al historico cuando esten completas las 4 notas parciales y el examen
                                    #segun se indico en reunion con Inge Stefy el 29-07-2020
                                    #if materiaAsignada.notafinal>0:
                                    if evaluacion.n1>0 and evaluacion.n2>0 and evaluacion.n3>0 and evaluacion.n4>0 and evaluacion.examen>0 :
                                        record = RecordAcademico(inscripcion=materiaAsignada.matricula.inscripcion,
                                                 asignatura=materiaAsignada.materia.asignatura,
                                                 nota=materiaAsignada.notafinal,asistencia=materiaAsignada.asistenciafinal,fecha=datetime.now(),
                                                 convalidacion=False, aprobada=materiaAsignada.esta_aprobado_final(),pendiente=(materiaAsignada.notafinal==0))
                                        record.save()

                                        historico = HistoricoRecordAcademico(inscripcion=record.inscripcion,
                                                    asignatura=record.asignatura,nota=record.nota,
                                                    asistencia=record.asistencia,fecha=record.fecha,
                                                    aprobada=record.aprobada,convalidacion=record.convalidacion,
                                                    pendiente=record.pendiente)
                                        historico.save()

                                        if HistoricoNotasITB.objects.filter(historico=historico).exists():
                                            hn = HistoricoNotasITB.objects.filter(historico=historico)[:1].get()
                                        else:
                                            hn = HistoricoNotasITB(historico=historico)
                                            hn.save()

                                            hn.cod1 = evaluacion.cod1.id if evaluacion.cod1 else 3
                                            hn.cod2 = evaluacion.cod2.id if evaluacion.cod2 else 5
                                            hn.cod3 = evaluacion.cod3.id if evaluacion.cod3 else 10
                                            hn.cod4 = evaluacion.cod4.id if evaluacion.cod4 else 11
                                            hn.n1=evaluacion.n1
                                            hn.n2=evaluacion.n2
                                            hn.n3=evaluacion.n3
                                            hn.n4=evaluacion.n4
                                            hn.n5=evaluacion.examen
                                            hn.recup=0
                                            hn.total = historico.nota
                                            hn.notafinal = historico.nota
                                            hn.save()
                                            hn.estado=evaluacion.estado
                                            hn.save()

                                nivelid = matricula.nivel_id
                                inscripcion = matricula.inscripcion
                                for record in inscripcion.recordacademico_set.all():
                                    if record.esta_pendiente():
                                        record.delete()
                                if RetiradoMatricula.objects.filter(inscripcion=inscripcion, nivel=matricula.nivel).exists():
                                    r = RetiradoMatricula.objects.filter(inscripcion=inscripcion, nivel=matricula.nivel)[:1].get()
                                    r.activo=False
                                    r.save()

                                else:
                                    r = RetiradoMatricula(inscripcion=inscripcion,
                                                          nivel=matricula.nivel,
                                                          activo=False)
                                    r.save()
                                dr = DetalleRetiradoMatricula(retirado=r,
                                                              motivo=motivo,
                                                              fecha=convertir_fecha(fecha),
                                                              especie = especie,
                                                              estado='RETIRO',
                                                              usuario=request.user)
                                dr.save()

                                # retiro = RetiradoMatricula(inscripcion=inscripcion, nivel=matricula.nivel, fecha=f.cleaned_data['fecha'], motivo=f.cleaned_data['motivo'])
                                # retiro.save()

                                # Corregir Rubros de existir

                                rmat = matricula.rubromatricula_set.all()
                                rcuot = matricula.rubrocuota_set.all()
                                if MODELO_EVALUACION==EVALUACION_CASADE:
                                    OTRO_RUBRO = TipoOtroRubro.objects.get(pk=2)

                                else:
                                    OTRO_RUBRO = TipoOtroRubro.objects.get(pk=TIPO_OTRO_RUBRO)


                                for r in rmat:
                                    ro = RubroOtro(rubro=r.rubro, tipo=OTRO_RUBRO, descripcion=r.rubro.nombre()+" (MATRICULA RETIRADA)")
                                    ro.save()

                                for r in rcuot:
                                    ro = RubroOtro(rubro=r.rubro, tipo=OTRO_RUBRO, descripcion=r.rubro.nombre()+" (MATRICULA RETIRADA)")
                                    ro.save()

                                for d in datos['detalle']:
                                    try:
                                        rubro = Rubro.objects.filter(pk=d['rubro'])[:1].get()
                                        if rubro.puede_eliminarse():
                                            if RubroOtro.objects.filter(rubro=rubro).exists():
                                                RubroOtro.objects.filter(rubro=rubro)[:1].get().delete()
                                            rubro.delete()
                                    except:
                                        pass

                                #OCastillo 27-03-2020 se quita valicacion de especie
                                if RubroEspecieValorada.objects.filter(serie=especie,rubro__inscripcion=matricula.inscripcion).exists():
                                    rubroespecie = RubroEspecieValorada.objects.filter(serie=especie,rubro__inscripcion=matricula.inscripcion)[:1].get()
                                    rubroespecie.codigoe=codigo.upper()
                                    rubroespecie.observaciones=motivo
                                    rubroespecie.aplicada= True
                                    rubroespecie.fecha=datetime.now().date()
                                    rubroespecie.usuario=request.user
                                    rubroespecie.fechafinaliza = datetime.now()
                                    rubroespecie.save()

                                    asis =  AsistenteDepartamento.objects.filter(persona__usuario=rubroespecie.usrasig)[:1].get()
                                    asis.cantidad = asis.cantidad - 1
                                    asis.save()

                                #Obtain client ip address
                                client_address = ip_client_address(request)

                                # Log de RETIRAR MATRICULA
                                LogEntry.objects.log_action(
                                    user_id         = request.user.pk,
                                    content_type_id = ContentType.objects.get_for_model(matricula).pk,
                                    object_id       = matricula.id,
                                    object_repr     = force_str(matricula),
                                    action_flag     = DELETION,
                                    change_message  = 'Retirada la Matricula (' + client_address + ')')
                                tipo=''
                                correo=''
                                if Coordinacion.objects.filter(carrera=inscripcion.carrera).exists():
                                    correocoordinacion=Coordinacion.objects.filter(carrera=inscripcion.carrera)[:1].get()
                                    if TipoIncidencia.objects.filter(pk=57).exists():
                                        tipo = TipoIncidencia.objects.get(pk=57)
                                    correo=str(inscripcion.persona.emailinst)+','+tipo.correo+','+correocoordinacion.correo
                                    matricula.correo_retirado(correo,request.user,motivo)
                                # inscripcion.retirado(request.user)

                                if ReferidosInscripcion.objects.filter(inscripcionref=matricula.inscripcion).exists()  :
                                    if Matricula.objects.filter(inscripcion=inscripcion).count() == 1:
                                        r = ReferidosInscripcion.objects.filter(inscripcionref=matricula.inscripcion)[:1].get()
                                        r.activo = False
                                        r.save()
                                        d=None
                                        if ReferidosInscripcion.objects.filter(inscripcion=r.inscripcion,activo=True,pago=True,inscrito=True).exists():
                                            c = ReferidosInscripcion.objects.filter(inscripcion=r.inscripcion,activo=True,pago=True,inscrito=True).count()
                                            if DescuentoReferido.objects.filter(desde__lte=c,hasta__gte=c).exists():
                                                d = DescuentoReferido.objects.get(desde__lte=c,hasta__gte=c)

                                            if InscripcionDescuentoRef.objects.filter(inscripcion=r.inscripcion,aplicado=False).exists():
                                                des = InscripcionDescuentoRef.objects.filter(inscripcion=r.inscripcion,aplicado=False)[:1].get()
                                                if d:
                                                    des.descuento=d
                                                    des.save()
                                                else:
                                                    des.delete()
                                        if InscripcionDescuentoRef.objects.filter(inscripcion=r.inscripcion,aplicado=True).exists():
                                            des = InscripcionDescuentoRef.objects.filter(inscripcion=r.inscripcion,aplicado=True)[:1].get()
                                            rant = ReferidosInscripcion.objects.filter(inscripcion=r.inscripcion,pago=True,inscrito=True).count()
                                            dant = DescuentoReferido.objects.get(desde__lte=rant,hasta__gte=rant)
                                            if EMAIL_ACTIVE:
                                                des.correo(matricula.inscripcion,dant,d)


                                # matricula.delete()
                                # buscar la encuesta para ponerla como aplicada y sea valida para las estadisticas agregado por Manuel Flores
                                if RubroEspecieValorada.objects.filter(serie=especie,rubro__inscripcion=matricula.inscripcion).exists():
                                   rubroespecie = RubroEspecieValorada.objects.filter(serie=especie,rubro__inscripcion=matricula.inscripcion)[:1].get()
                                   if InscripcionTestIngreso.objects.filter(rubroespecie=rubroespecie.id).exists():
                                      inscriptesde=InscripcionTestIngreso.objects.filter(rubroespecie=rubroespecie.id)[:1].get()
                                      inscriptesde.aplicada=True
                                      inscriptesde.save()

                            else:
                                return HttpResponse(json.dumps({"result":"bad",'error':"3"}),content_type="application/json")
                                # return HttpResponseRedirect("/matriculas?action=retirar&error=3&id="+str(request.POST['id']))
                            # return HttpResponseRedirect("/matriculas?action=matricula&id="+str(nivelid))
                            return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                        else:
                            return HttpResponse(json.dumps({"result":"bad",'error':"1"}),content_type="application/json")
                                # return HttpResponseRedirect("/matriculas?action=retirar&error=1&id="+str(request.POST['id']))
                    except Exception as e:
                        rollback()
                        return HttpResponse(json.dumps({"result":"error",'msj':str(e)}),content_type="application/json")
                        # return HttpResponseRedirect("/matriculas?action=retirar&error=2&id="+str(request.POST['id']))

                #OCU 09-marzo-2016 Observaciones en matriculas a Estudiantes Absentos
                elif action=='obs_absento':
                    matricula = Matricula.objects.get(pk=request.POST['id'])
                    f = ObservacionMatriculaForm(request.POST)
                    if f.is_valid():
                        observacion = ObservacionMatricula(matricula=matricula,
                                                           observaciones=f.cleaned_data['observaciones'],
                                                           fecha = datetime.now(),
                                                           usuario = request.user)
                        observacion.save()

                        #Obtain client ip address
                        client_address = ip_client_address(request)

                        # Log de ADICIONAR OBSERVACION
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(observacion).pk,
                            object_id       = observacion.id,
                            object_repr     = force_str(observacion),
                            action_flag     = ADDITION,
                            change_message  = 'Adicionada Observacion de Matricula Absento (' + client_address + ')' )

                        # return HttpResponseRedirect("/inscripciones?action=observaciones&id="+str(inscripcion.id))
                        # return HttpResponseRedirect("/matriculas")
                        return HttpResponseRedirect("/matriculas?action=matricula&id="+str(matricula.nivel.id))
                    else:
                        # return HttpResponseRedirect("/matriculas?action=obs_absento")
                        # return HttpResponseRedirect("/matriculas")
                        return HttpResponseRedirect("/matriculas?action=matricula&id="+str(matricula.nivel.id))

                elif action=='editobs_absento':
                    observacion = ObservacionMatricula.objects.get(pk=request.POST['id'])
                    matricula = observacion.matricula
                    f = ObservacionMatriculaForm(request.POST)
                    if f.is_valid():
                        observacion.observaciones = f.cleaned_data['observaciones']
                        observacion.fecha = datetime.now()
                        observacion.usuario= request.user
                        observacion.save()

                        #Obtain client ip address
                        client_address = ip_client_address(request)

                        # Log de EDITAR OBSERVACION
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(observacion).pk,
                            object_id       = observacion.id,
                            object_repr     = force_str(observacion),
                            action_flag     = CHANGE,
                            change_message  = 'Editada Observacion de Matricula (' + client_address + ')' )

                        # return HttpResponseRedirect("/matriculas")
                        return HttpResponseRedirect("/matriculas?action=matricula&id="+str(matricula.nivel.id))
                    else:
                        # return HttpResponseRedirect("/inscripciones?action=editobs_absento&id="+str(observacion.id))
                        # return HttpResponseRedirect("/matriculas")
                        return HttpResponseRedirect("/matriculas?action=matricula&id="+str(matricula.nivel.id))

                elif action=='delobs_absento':
                    observacion = ObservacionMatricula.objects.get(pk=request.POST['id'])
                    matricula = observacion.matricula

                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de ELIMINAR OBSERVACION
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(observacion).pk,
                        object_id       = observacion.id,
                        object_repr     = force_str(observacion),
                        action_flag     = CHANGE,
                        change_message  = 'Eliminada Observacion de Matricula (' + client_address + ')' )

                    observacion.delete()
                    return HttpResponseRedirect("/matriculas?action=matricula&id="+str(matricula.nivel.id))

                elif action=='matproxnivel':
                    nivel_anterior = Nivel.objects.get(pk=request.POST['id'])
                    matriculados_anterior = nivel_anterior.matriculados()
                    alumnos_pasan = []
                    alumnos_nopasan = []
                    alumnos_obscritica=[]
                    alumnos_correo=[]
                    nivel_actual=''

                    f = MatriculaProxNivelForm(request.POST)
                    if f.is_valid():
                        nivel_nuevo = f.cleaned_data['niveldestino']
                        nivel_actual=Nivel.objects.filter(pk=nivel_nuevo.id)[:1].get()
                        nivel_matri=nivel_actual.nivelmalla.nombre
                        grupo=nivel_actual.paralelo
                        carrera=nivel_actual.carrera.nombre
                        for matricula in matriculados_anterior:
                            if not matricula.inscripcion.suspension:
                                if matricula.todas_materias_aprobadas() == True :
                                    matricula.inscripcion.matricular(nivel_nuevo)
                                    alumnos_pasan.append(matricula.inscripcion)
                                    alumnos_correo.append((elimina_tildes(matricula.inscripcion.persona.nombre_completo_inverso()),matricula.inscripcion.persona.emailinst))
                                else:
                                    materias_aprobadas = matricula.cantidad_materias_aprobadas()
                                    materias_reprobadas = matricula.cantidad_materias_reprobadas()
                                    mensaje=''
                                    if matricula.todas_materias_aprobadas() != True:
                                        mensaje = matricula.todas_materias_aprobadas()
                                    alumnos_nopasan.append((matricula.inscripcion, materias_aprobadas, materias_reprobadas,mensaje))
                                    if materias_reprobadas > NUMERO_POSIBLE_DESERTOR:
                                        # usuario = User.objects.filter(username=request.user)
                                        if not EstudiantesXDesertar.objects.filter(matricula=matricula,inscripcion=matricula.inscripcion).exists():
                                            estudiantesxdesertar = EstudiantesXDesertar(inscripcion=matricula.inscripcion,
                                                                            matricula=matricula,
                                                                            usuario=request.user,
                                                                            fecha=datetime.now(),
                                                                            materiareprobada = materias_reprobadas)
                                            estudiantesxdesertar.save()
                            else:
                                if matricula.inscripcion.tiene_obscritica():
                                    obs = ObservacionInscripcion.objects.filter(inscripcion=matricula.inscripcion,tipo=TIPO_OBSERVACION_CRITICA_ID,activa=True).order_by('-fecha').get()
                                    alumnos_obscritica.append((matricula.inscripcion,elimina_tildes(obs.observaciones)))

                        #Enviar correo a Secretaria Docentes
                        if EMAIL_ACTIVE:
                            nivel_nuevo.mail_matriculas(alumnos_pasan, alumnos_nopasan, nivel_anterior,alumnos_obscritica)
                            #OC 07-febrero-2019 enviar correo a soporte cuando la matricula es en el primer nivel
                            if nivel_actual.nivelmalla.id == NIVEL_MALLA_UNO and DEFAULT_PASSWORD == 'itb':
                                if len(alumnos_correo)>0:
                                    op='2'
                                    hoy = datetime.now().today()
                                    personarespon = Persona.objects.filter(usuario=request.user)[:1].get()
                                    correo= str('soporteitb@bolivariano.edu.ec')
                                    # correo= ('ocastillo@bolivariano.edu.ec')
                                    send_html_mail("ESTUDIANTES MATRICULADOS A PRIMER NIVEL",
                                    "emails/correo_matricula_primernivel.html", {'contenido': "ESTUDIANTES MATRICULADOS A PRIMER NIVEL",'op':op, 'estudiante': alumnos_correo, 'nivel': nivel_matri,'grupo':grupo,'personarespon': personarespon, 'fecha': hoy,'carrera':carrera},correo.split(','))
                        return HttpResponseRedirect('matriculas?action=matricula&id='+ str(nivel_nuevo.id))

                elif action=='buscaobs':
                    # OCastillo 06-09-2018 se verifica si estudiante tiene obs critica y presentarla
                    obs=""
                    msj=""
                    inscripcion = Inscripcion.objects.get(pk=request.POST['inscrip'])
                    if inscripcion.tiene_obscritica():
                        obs = ObservacionInscripcion.objects.filter(inscripcion=inscripcion,tipo=TIPO_OBSERVACION_CRITICA_ID,activa=True).order_by('-fecha')[:1].get()
                        obs= elimina_tildes(obs.observaciones)

                    if inscripcion.carrera.validacionprofesional:
                        if ExamenConvalidacionIngreso.objects.filter(inscripcion=inscripcion).exists():
                            exa =ExamenConvalidacionIngreso.objects.filter(inscripcion=inscripcion).order_by('id')[:1].get()
                            msj ='Estudiante tiene examen de validacion profesional con nota ' + str(exa.nota)
                        else:
                            msj ='Estudiante no tiene registrada nota de examen de validacion profesional '


                    if  obs =="" and msj== "" :
                        return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({"result":"bad","obs":obs ,"msj":msj}),content_type="application/json")

                elif action=='consutabladescuento':
                    data = {}
                    matricula = Matricula.objects.get(id=request.POST['idmatricula'])
                    if SolicitudBeca.objects.filter(inscripcion=matricula.inscripcion,nivel=matricula.nivel,tiposolicitud=1).order_by('-fecha').exists():
                        solicitudbeca = SolicitudBeca.objects.filter(inscripcion=matricula.inscripcion,nivel=matricula.nivel,tiposolicitud=1).order_by('-fecha')[:1].get()
                        if TablaDescuentoBeca.objects.filter(solicitudbeca=solicitudbeca).exists():
                             data['aplicarcontabla'] = '1'
                        else:
                             data['aplicarcontabla'] = '2'

                        data['result'] = 'ok'
                    elif SolicitudBeca.objects.filter(inscripcion=matricula.inscripcion,nivel=matricula.nivel,tiposolicitud=2).order_by('-fecha').exists():
                        solicitudbeca = SolicitudBeca.objects.filter(inscripcion=matricula.inscripcion,nivel=matricula.nivel,tiposolicitud=2).order_by('-fecha')[:1].get()
                        if TablaDescuentoBeca.objects.filter(solicitudbeca=solicitudbeca).exists():
                             data['aplicarcontabla'] = '1'
                        else:
                             data['aplicarcontabla'] = '2'

                        data['result'] = 'ok'
                    else:
                        data['result'] = 'bad'
                    return HttpResponse(json.dumps(data),content_type="application/json")

                elif action == 'xls_becasmunicipio':
                    result = {}
                    try:
                        excel = ArchivoExcelBecadosMunicipio(archivo=request.FILES['archivo'])
                        excel.save()

                        ruta = xlrd.open_workbook(SITE_ROOT + excel.archivo.url)
                        hoja1 = ruta.sheet_by_index(0)

                        titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                        titulo2 = xlwt.easyxf('font: bold on; align: vert centre, horiz center')
                        titulo.font.height = 20*11
                        titulo2.font.height = 20*11
                        subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                        subtitulo3 = xlwt.easyxf('font: name Times New Roman; align: wrap on, vert centre, horiz center')
                        subtitulo.font.height = 20*10

                        wb = xlwt.Workbook()
                        ws = wb.add_sheet(hoja1.name,cell_overwrite_ok=True)

                        num_filas = hoja1.nrows
                        lista = []
                        cedulas = []
                        for i in range (2,num_filas):
                            if hoja1.cell_value(i,0):
                                if hoja1.cell_value(i,1):
                                    cedulas.append(hoja1.cell_value(i,1))
                                    ws.write(i,0, hoja1.cell_value(i,0))
                                    ws.write(i,1, hoja1.cell_value(i,1))
                                    ws.write(i,2, hoja1.cell_value(i,2))
                                    ws.write(i,3, hoja1.cell_value(i,3))

                                    if Inscripcion.objects.filter(persona__cedula=hoja1.cell_value(i,1)).exists() or Inscripcion.objects.filter(persona__pasaporte=hoja1.cell_value(i,1)).exists():
                                        try:
                                            if Inscripcion.objects.filter(persona__cedula=hoja1.cell_value(i,1)).exists():
                                                inscripcion = Inscripcion.objects.filter(persona__cedula=hoja1.cell_value(i,1)).order_by('-id')[:1].get()
                                            else:
                                                inscripcion = Inscripcion.objects.filter(persona__pasaporte=hoja1.cell_value(i,1)).order_by('-id')[:1].get()
                                            if inscripcion.persona.telefono:
                                                ws.write(i,4, elimina_tildes(inscripcion.persona.telefono))
                                            if inscripcion.persona.telefono_conv:
                                                ws.write(i,5, elimina_tildes(inscripcion.persona.telefono_conv))
                                            if inscripcion.persona.email:
                                                ws.write(i,6, elimina_tildes(inscripcion.persona.email))
                                            if inscripcion.persona.emailinst:
                                                ws.write(i,7, elimina_tildes(inscripcion.persona.emailinst))
                                            if inscripcion.tienediscapacidad:
                                                ws.write(i,8, 'SI')
                                            else:
                                                ws.write(i,8, 'NO')
                                            if inscripcion.persona.direccion_completa():
                                                ws.write(i,9, elimina_tildes(inscripcion.persona.direccion_completa()))
                                            if inscripcion.persona.parroquia:
                                                ws.write(i,10, elimina_tildes(inscripcion.persona.parroquia.nombre))

                                            if inscripcion:
                                                inscrgrupo=InscripcionGrupo.objects.filter(inscripcion=inscripcion)[:1].get()
                                                ws.write(i,11, elimina_tildes(inscrgrupo.grupo.sesion))
                                            else:
                                                ws.write(i,11, str('--------------'))

                                        except Exception as ex:
                                            print(ex)
                                            print(inscripcion.id)

                                else:
                                    cedulas.append(hoja1.cell_value(i,0))
                                    ws.write(i,0, hoja1.cell_value(i,0),titulo)
                                continue
                            if cedulas:
                                lista.append(cedulas)
                                cedulas = []

                        ws.write_merge(0,0,0,10, hoja1.cell_value(0,0),titulo2)
                        ws.write(1,0, hoja1.cell_value(1,0),titulo)
                        ws.write(1,1, hoja1.cell_value(1,1),titulo)
                        ws.write(1,2, hoja1.cell_value(1,2),titulo)
                        ws.write(1,3, hoja1.cell_value(1,3),titulo)
                        ws.write(1,4, 'CELULAR',titulo)
                        ws.write(1,5, 'CONVENCIONAL',titulo)
                        ws.write(1,6, 'CORREO PERSONAL',titulo)
                        ws.write(1,7, 'CORREO INSTITUCIONAL',titulo)
                        ws.write(1,8, 'TIENE DISCAPACIDAD',titulo)
                        ws.write(1,9, 'DOMICILIO',titulo)
                        ws.write(1,10, 'PARROQUIA',titulo)
                        ws.write(1,11, 'JORNADA',titulo)
                        print('posi')
                        nombre = str((elimina_tildes(excel.archivo).split('.'))[0][19:])+'_procesado.xls'
                        wb.save(MEDIA_ROOT+'/xls_becasmunicipio/'+nombre)
                        return HttpResponse(json.dumps({"result":"ok", "url": "/media/xls_becasmunicipio/"+nombre}),content_type="application/json")

                    except Exception as ex:
                        print(ex)
                        result['result'] = 'bad'
                        return HttpResponse(json.dumps(result),content_type="application/json")

                elif action == 'cargaderubromatriculados':
                    result = {}
                    valorcredencial=8
                    est=0
                    try:
                        matriculados=Matricula.objects.filter(nivel__cerrado=False, nivel__periodo__activo=True, inscripcion__persona__usuario__is_active=True,liberada=False,nivel__carrera__activo=True,nivel__carrera__carrera=True).exclude(nivel__nivelmalla__in=[9,10,11,12,13]).exclude(nivel__carrera__in=[66]).exclude(inscripcion__id__in=[65147,78313,74284,81702,61109,84602,78760,75598,65513,84676]).distinct('inscripcion').order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2').values('inscripcion')
                        for mat in matriculados:
                            est=est+1
                            print(mat)
                            # if Inscripcion.objects.filter(pk=mat['inscripcion']).exists():
                            #     inscripcion = Inscripcion.objects.filter(pk=mat['inscripcion'])[:1].get()
                            #
                            #     rubro = Rubro( fecha = datetime.now().date(),
                            #             valor = valorcredencial,
                            #             inscripcion = inscripcion,
                            #             cancelado = False,
                            #             fechavence = datetime.now().date()+ timedelta(days=5))
                            #     rubro.save()
                            #     rubrootro = RubroOtro(rubro=rubro,
                            #                 tipo=TipoOtroRubro.objects.get(pk=TIPO_RUBRO_CREDENCIAL),
                            #                 descripcion='CREDENCIAL ESTUDIANTE')
                            #     rubrootro.save()
                        result['result'] = 'ok'
                        print(est)
                        return HttpResponse(json.dumps(result),content_type="application/json")
                    except Exception as ex:
                        print(ex)
                        result['result'] = 'bad'
                        return HttpResponse(json.dumps(result),content_type="application/json")

                #OCastillo 28-octubre-2022 para subir rubros masivos a estudiantes listado en excel
                elif action=='subirrubrosmasivos':
                    identificacion=''
                    listadoerror=[]
                    listadocorrecto=[]
                    tipotrorubro=None
                    registrosvalidos=0
                    registrosinvalidos=0
                    try:
                        ex=''
                        nombrescompletos=''
                        data = {}
                        addUserData(request, data)
                        valor = Decimal(request.POST['valor']).quantize(Decimal(10)**-2)
                        descripcion = elimina_tildes(request.POST['descripcion']).upper()
                        fecharubro = request.POST['fecha']
                        fecharubro = convertir_fecha(fecharubro)
                        fechavencimiento = request.POST['fechavencimiento']
                        fechavencimiento = convertir_fecha(fechavencimiento)
                        tipotrorubro = TipoOtroRubro.objects.get(pk=request.POST['tipootrorubro'])

                        archlote = ArchivoRubroOtroMasivos(archivo=request.FILES["file"],tipotrorubro=tipotrorubro,fecha=fecharubro,descripcion=descripcion,
                                                           fechavencimiento=fechavencimiento,valor=valor,usuario=request.user,fecharegistro=datetime.now())
                        archlote.save()

                        # para produccion
                        wb = xlrd.open_workbook(MEDIA_ROOT + '/' + str(archlote.archivo))
                        #para local
                        # wb = xlrd.open_workbook(MEDIA_ROOT + '\\' + str(archlote.archivo))
                        hoja = wb.sheet_by_index(0)
                        # registrosvalidos=0
                        # registrosinvalidos=0
                        for i in range(0, hoja.nrows):
                            inscripcion=None
                            if i>0:
                                # print((i))
                                nombrescompletos=str(elimina_tildes(hoja.cell_value(i, 2))).strip().strip().replace(" ",'')
                                identificacion=str(hoja.cell_value(i,2)).strip().strip().replace(" ",'')
                                if  Inscripcion.objects.filter(Q(persona__cedula=identificacion)|Q(persona__pasaporte=identificacion),persona__usuario__is_active=True).exists():
                                    inscripcion = Inscripcion.objects.filter(Q(persona__cedula=identificacion)|Q(persona__pasaporte=identificacion),persona__usuario__is_active=True).exclude(carrera__id=66)[:1].get()

                                if inscripcion==None:
                                    listadoerror.append(elimina_tildes(hoja.cell_value(i, 2)).strip().strip().replace(" ",''))
                                    registrosinvalidos+=1
                                else:
                                    rubro = Rubro( fecha = fecharubro,
                                            valor = valor,
                                            inscripcion = inscripcion,
                                            cancelado = False,
                                            fechavence = fechavencimiento)
                                    rubro.save()
                                    rubrootro = RubroOtro(rubro=rubro,
                                                tipo=TipoOtroRubro.objects.get(pk=tipotrorubro.id),
                                                descripcion=descripcion)
                                    rubrootro.save()

                                    #Obtener el ip de donde estan accediendo
                                    try:
                                        # case server externo
                                        client_address = request.META['HTTP_X_FORWARDED_FOR']
                                    except:
                                        # case localhost o 127.0.0.1
                                        client_address = request.META['REMOTE_ADDR']

                                    # Log de ADICIONAR PRESTAMO INSTITUCIONAL EN LOTE
                                    LogEntry.objects.log_action(
                                        user_id         = request.user.pk,
                                        content_type_id = ContentType.objects.get_for_model(rubro).pk,
                                        object_id       = rubro.id,
                                        object_repr     = force_str(rubro),
                                        action_flag     = ADDITION,
                                        change_message  = 'Adicionado Rubro en Lote (' + client_address + ')' )
                                registrosvalidos+=1
                                listadocorrecto.append(elimina_tildes(hoja.cell_value(i, 2)).strip().strip().replace(" ",''))


                        mail_cargarubrosenlote(request.user,listadoerror,listadocorrecto,registrosvalidos,registrosinvalidos,tipotrorubro)
                        return HttpResponse(json.dumps({'result': 'ok'}), content_type="application/json")
                        # else:
                        #     mail_cargarubrosenlote(request.user,listadoerror,listadocorrecto,registrosvalidos,registrosinvalidos,tipotrorubro)
                        #     return HttpResponse(json.dumps({'result': 'ok'}), content_type="application/json")

                    except Exception as ex:
                        print(identificacion)
                        # if listadoerror :
                        #     mail_cargarubrosenlote(request.user,listadoerror,listadocorrecto,registrosvalidos,registrosinvalidos,tipotrorubro)
                        #     return HttpResponse(json.dumps({'result': 'ok'}), content_type="application/json")
                        # else:
                        #     mail_cargarubrosenlote(request.user,listadoerror,listadocorrecto,registrosvalidos,registrosinvalidos,tipotrorubro)
                        #     return HttpResponse(json.dumps({'result': 'ok'}), content_type="application/json")
                        return HttpResponse(json.dumps({'result': 'bad','mensaje':str(ex)+"& error en fila="+str(nombrescompletos)}), content_type="application/json")

                elif action=='actualizarbecatec':
                    result = {}
                    try:
                        nivel = Nivel.objects.get(pk=request.POST['idnivel'])

                        matriculados=Matricula.objects.filter(nivel=nivel,inscripcion_empresaconvenio_id=ID_CONVENIO_BECA_TECT).order_by('inscripcion__persona__apellido1')

                        for mat in matriculados:
                            if mat.inscripcion.empresaconvenio.id==ID_CONVENIO_BECA_TECT:
                                 if not mat.becado:
                                      # rubro cuota////////

                                      # buscar el rubro del periodo anterior
                                      matriculaant = Matricula.objects.filter(inscripcion = mat.inscripcion,nivel__cerrado=True).order_by('-fecha')[:1].get()
                                      rubroanterior=RubroCuota.objects.filter(matricula=matriculaant).order_by('-id')[:1].get()

                                      rubrocuota = Rubro(fecha=datetime.today().date(),
                                                           valor=rubroanterior.rubro.valor, inscripcion=mat.inscripcion,
                                                           cancelado=False, fechavence=mat.nivel.fin)

                                      rubrocuota.save()



                                      rc = RubroCuota(rubro=rubrocuota, matricula=mat, cuota=1)
                                      rc.save()

                                      # actualizamos la matricula actual con la beca que fue acreditada por el gobierno becas tec
                                      mat.becado=True
                                      mat.fechabeca=datetime.now()
                                      mat.tipobeneficio_id=ID_TIPO_BENEFICICO_BECA
                                      mat.tipobeca_id=ID_TIPOBECA
                                      mat.motivobeca_id=ID_MOTIVO_BECA_TEC
                                      mat.porcientobeca=100
                                      mat.save()


                        result['result'] = 'ok'

                        return HttpResponse(json.dumps(result),content_type="application/json")
                    except Exception as ex:
                        print(ex)
                        result['result'] = 'bad'
                        return HttpResponse(json.dumps(result),content_type="application/json")


            return HttpResponseRedirect("/?info="+request.POST['action'])

        except Exception as e:
            return HttpResponseRedirect("/?info="+str(e))
    else:
        try:
            data = {'title': 'Matriculas de Alumnos'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']
                if action=='matricula':
                    data['title'] = 'Matricula de Nivel Academico'
                    nivel = Nivel.objects.get(pk=request.GET['id'])
                    ret = None
                    if 'ret' in request.GET:
                        ret = request.GET['ret']
                    periodo = request.session['periodo']
                    data['nivel'] = nivel
                    data['periodo'] = periodo
                    data['tipo_ayuda_financiera'] = TIPO_AYUDA_FINANCIERA
                    data['usa_modulo_finanzas'] = MODULO_FINANZAS_ACTIVO
                    data['matriculas'] = Matricula.objects.filter(nivel=nivel).order_by('inscripcion__persona__apellido1')
                    data['pagoniveles'] = PagoNivel.objects.filter(nivel=nivel).exclude(tipo=0).order_by('fecha')
                    data['ret'] = ret if ret else ""
                    data['matriculalibre'] = MODELO_EVALUACION==EVALUACION_TES
                    data['usa_matricula_recargo'] = UTILIZA_MATRICULA_RECARGO
                    data['NIVEL_SEMINARIO'] = NIVEL_SEMINARIO
                    data['pagomatricula'] = PagoNivel.objects.filter(nivel=nivel,tipo=0).order_by('fecha')
                    data['MODELO_EVALUATIVO'] = [MODELO_EVALUACION, EVALUACION_IAVQ, EVALUACION_ITB, EVALUACION_ITS, EVALUACION_TES, EVALUACION_IGAD]
                    data['NIVEL_UNO'] = NIVEL_MALLA_UNO
                    return render(request ,"matriculas/matriculabs.html" ,  data)
                elif action=='addmatricula':
                    data['title'] = 'Matricular Alumno'

                    if 'id' in request.GET:
                        nivel = Nivel.objects.get(pk=request.GET['id'])
                        data['nivel'] = nivel
                        form = MatriculaForm(initial={'nivel':nivel})

                        if UTILIZA_GRUPOS_ALUMNOS:
                            grupo = nivel.grupo
                            form.for_grupo(grupo)

                        data['form'] = form
                    else:
                        if 'inscrip' in request.GET:
                            inscripcion = Inscripcion.objects.get(pk=request.GET['inscrip'])
                            data['form'] = MatriculaForm(instance=Matricula(inscripcion=inscripcion), periodo=data['periodo'])
                        else:
                            data['form'] = MatriculaForm(instance=Matricula(), periodo=data['periodo'])

                    #Si viene este error es pq el alumno ya esta matriculado
                    if 'error' in request.GET:
                        if request.GET['error'] == '2' :
                            data['fail'] = 1
                            data['error'] = request.GET['error']
                        else:
                            data['error'] = request.GET['error']
                    if 'hvin' in request.GET:
                        data['hvin'] = request.GET['hvin']

                    #Si viene esta variable es pq el estudiante no ha llenado la ficha medica
                    if 'ficha' in request.GET:
                        data['ficha'] = request.GET['ficha']
                    #Si viene esta variable es pq el dpto medico no ha llenado la valoracion medica
                    if 'valoracion' in request.GET:
                        data['valoracion'] = request.GET['valoracion']

                    return render(request ,"matriculas/adicionar_matriculabs.html" ,  data)
                elif action=='addmatriculalibre':
                    data['title'] = 'Matricular Estudiante'

                    nivel = Nivel.objects.get(pk=request.GET['id'])
                    data['nivel'] = nivel
                    form = MatriculaLibreForm()

                    data['form'] = form

                    if 'error' in request.GET:
                        if request.GET['error'] == '2':
                            data['fail'] = 1
                            data['error'] = request.GET['error']
                        else:
                            data['error'] = request.GET['error']

                    # Matriculacion Libre
                    data['coordinaciones'] = [[c, Nivel.objects.filter(periodo=data['periodo'], nivellibrecoordinacion__coordinacion=c).order_by('-sesion__id','paralelo')] for c in Coordinacion.objects.all().order_by('nombre')]
                    materias = Materia.objects.filter(cerrado=False, nivel__periodo=data['periodo']).order_by('asignatura__nombre')
                    data['materias'] = [m for m in materias if m.tiene_capacidad()]
                    data['micoordinacion'] = nivel.coordinacion()

                    return render(request ,"matriculas/adicionar_matricula_librebs.html" ,  data)

                elif action=='addmatriculaextra':
                    data['title'] = 'Matricula Extraordinaria de un Alumno con Recargo'

                    nivel = Nivel.objects.get(pk=request.GET['id'])
                    form = MatriculaExtraForm()

                    if UTILIZA_GRUPOS_ALUMNOS:
                        grupo = nivel.grupo
                        form.for_grupo(grupo)

                    if 'error' in request.GET:
                        data['fail'] =1

                    data['nivel'] = nivel
                    data['form'] = form

                    #Si viene esta variable es pq el estudiante no ha llenado la ficha medica
                    if 'ficha' in request.GET:
                        data['ficha'] = request.GET['ficha']

                    #Si viene esta variable es pq el dpto medico no ha llenado la valoracion medica
                    if 'valoracion' in request.GET:
                        data['valoracion'] = request.GET['valoracion']

                    return render(request ,"matriculas/adicionar_matriculaextrabs.html" ,  data)

                elif action=='addmatriculamulti':
                    data['title'] = 'Matricular Estudiantes en Lote'

                    nivel = Nivel.objects.get(pk=request.GET['id'])
                    data['nivel'] = nivel

                    form = MatriculaMultipleForm(initial={'nivel':nivel})
                    data['form'] = form

                    if 'error' in request.GET:
                        data['error'] = request.GET['error']
                    data['NIVEL_GRADUACION'] = NIVEL_GRADUACION

                    return render(request ,"matriculas/adicionar_matricula_multiplebs.html" ,  data)
                elif action=='editmatricula':
                    data['title'] = 'Editar Matricula de Estudiante'
                    matricula = Matricula.objects.get(pk=request.GET['id'])
                    periodo = request.session['periodo']
                    nivel = matricula.nivel
                    data['nivel'] = nivel
                    data['matricula'] = matricula
                    initial = model_to_dict(matricula)
                    data['form'] = MatriculaEditForm(initial=initial)
                    data['form'].for_nivel(periodo.tipo_id)
                    data['tipo_ayuda_financiera'] = TIPO_AYUDA_FINANCIERA
                    lista = []
                    lista.append(['dobe@bolivariano.edu.ec'])
                    lista[0][0]=str(lista[0][0])+','+str('mfloresv@bolivariano.edu.ec')

                    mail_correocrisfe(str('VERIFICAR CASO DE CRISFE ANTE DE ELIMINAR LA MATRICULA'), str(lista[0][0]),request.user, elimina_tildes(matricula.inscripcion.persona.nombre_completo()),elimina_tildes(matricula.inscripcion.carrera.nombre),matricula.inscripcion.persona.emailinst,matricula)

                    return render(request ,"matriculas/editar_matriculabs.html" ,  data)

                elif action=='delmatricula':
                    data['title'] = 'Borrar Matricula de Estudiante'
                    if Matricula.objects.filter(pk=request.GET['id']).exists():
                        matricula = Matricula.objects.get(pk=request.GET['id'])

                        if SolicitudBeca.objects.filter(nivel=matricula.nivel,inscripcion=matricula.inscripcion,tiposolicitud__in=LISTA_TIPO_BECA,eliminado=False).exists():
                           if Matricula.objects.filter(inscripcion = matricula.inscripcion,nivel__cerrado=True).exists():
                               matriculaant = Matricula.objects.filter(inscripcion = matricula.inscripcion,nivel__cerrado=True).order_by('-fecha')[:1].get()
                               if not Matricula.objects.filter(inscripcion=matricula.inscripcion,nivel=matriculaant.nivel,motivobeca__id=ID_FUNDACION_CRISFE).exists():
                                    data['matricula'] = matricula
                                    data['form'] =EliminacionMatriculaForm(initial={'fecha': datetime.now().strftime("%d-%m-%Y")})
                                    data['tiene_evaluacion'] = matricula.tiene_evaluacion()
                                    return render(request ,"matriculas/borrar_matriculabs.html" ,  data)
                               else:
                                   if SolicitudBeca.objects.filter(nivel__nivelmalla__id=matricula.nivel.nivelmalla.id,inscripcion=matriculaant.inscripcion,tiposolicitud=1,autorizacioneliminarcrisfe=False,eliminado=False).exists():
                                        nivel=matricula.nivel
                                        ret = None
                                        if 'ret' in request.GET:
                                            ret = request.GET['ret']
                                        periodo = request.session['periodo']
                                        data['nivel'] = nivel
                                        data['periodo'] = periodo
                                        data['tipo_ayuda_financiera'] = TIPO_AYUDA_FINANCIERA
                                        data['usa_modulo_finanzas'] = MODULO_FINANZAS_ACTIVO
                                        data['matriculas'] = Matricula.objects.filter(nivel=nivel).order_by('inscripcion__persona__apellido1')
                                        data['pagoniveles'] = PagoNivel.objects.filter(nivel=nivel).exclude(tipo=0).order_by('fecha')
                                        data['ret'] = ret if ret else ""
                                        data['matriculalibre'] = MODELO_EVALUACION==EVALUACION_TES
                                        data['usa_matricula_recargo'] = UTILIZA_MATRICULA_RECARGO
                                        data['NIVEL_SEMINARIO'] = NIVEL_SEMINARIO
                                        data['MODELO_EVALUATIVO'] = [MODELO_EVALUACION, EVALUACION_IAVQ, EVALUACION_ITB, EVALUACION_ITS, EVALUACION_TES, EVALUACION_IGAD]
                                        data['errorbecacrisfe'] = True
                                        lista = []
                                        lista.append(['dobe@bolivariano.edu.ec'])
                                        lista[0][0]=str(lista[0][0])+','+str('mfloresv@bolivariano.edu.ec')


                                        mail_correocrisfe(str('VERIFICAR CASO DE CRISFE ANTES DE ELIMINAR LA MATRICULA'), str(lista[0][0]),request.user, elimina_tildes(matricula.inscripcion.persona.nombre_completo()),elimina_tildes(matricula.inscripcion.carrera.nombre),matricula.inscripcion.persona.emailinst,matricula)


                                        return render(request ,"matriculas/matriculabs.html" ,  data)
                                   else:
                                        data['matricula'] = matricula
                                        data['form'] =EliminacionMatriculaForm(initial={'fecha': datetime.now().strftime("%d-%m-%Y")})
                                        data['tiene_evaluacion'] = matricula.tiene_evaluacion()
                                        return render(request ,"matriculas/borrar_matriculabs.html" ,  data)
                           else:
                               return HttpResponseRedirect("/?info=Tiene una solicitud de Beca y/o Ayuda Financiera en proceso " + elimina_tildes(matricula.inscripcion))


                        else:
                            data['matricula'] = matricula
                            data['form'] =EliminacionMatriculaForm(initial={'fecha': datetime.now().strftime("%d-%m-%Y")})
                            data['tiene_evaluacion'] = matricula.tiene_evaluacion()
                            return render(request ,"matriculas/borrar_matriculabs.html" ,  data)


                elif action=='recontruirpago':
                    if Matricula.objects.filter(pk=request.GET['id']).exists():
                        matricula = Matricula.objects.get(pk=request.GET['id'])
                        nivelid = matricula.nivel_id
                        nivel=matricula.nivel
                        i=0
                        for i in range(6):
                            if i>1 :
                                rubro = Rubro.objects.get(inscripcion=matricula.inscripcion,tiponivelpago=i)
                                # CUOTA MENSUAL
                                rc = RubroCuota(rubro=rubro, matricula=matricula, cuota=i)
                                rc.save()


                        return HttpResponseRedirect("/matriculas?action=matricula&id="+str(nivelid))

                elif action=='beca':
                    data['title'] = 'Aplicar Porciento de Beca a Estudiantes'
                    matricula = Matricula.objects.get(pk=request.GET['id'])
                    data['matricula'] = matricula
                    initial = model_to_dict(matricula)
                    initial.update({'fechabeca': datetime.now()})
                    data['form'] = MatriculaBecaForm(initial=initial)

                    data['tipo_ayuda_financiera'] = TIPO_AYUDA_FINANCIERA
                    data['tipo_beca_senescyt'] = TIPO_BECA_SENESCYT


                    if SolicitudBeca.objects.filter(inscripcion=matricula.inscripcion,
                                                              nivel=matricula.nivel,
                                                              estadosolicitud=ID_GESTION_SECRETARIA).exists():
                        # obtengo la informacion de la beca
                        solicitudbeca = SolicitudBeca.objects.get(inscripcion=matricula.inscripcion,
                                                                  nivel=matricula.nivel,
                                                                  estadosolicitud=ID_GESTION_SECRETARIA)
                        data['infsolicitudbeca'] = solicitudbeca

                        # obtengo la informacion del ultimo analisis aprobado
                        if solicitudbeca.tiposolicitud==ID_TIPO_SOLICITUD_BECA:

                            if HistorialGestionBeca.objects.filter(solicitudbeca=solicitudbeca,estado=ID_GESTION_ANALSIS).exists():

                               ultimagestion= HistorialGestionBeca.objects.filter(solicitudbeca=solicitudbeca,
                                                                                  estado=ID_GESTION_ANALSIS).order_by(
                                    '-fecha')[:1].get()
                        else:

                            if HistorialGestionAyudaEconomica.objects.filter(solicitudbeca=solicitudbeca,estado=ID_GESTION_ANALSIS).exists():

                               ultimagestion= HistorialGestionAyudaEconomica.objects.filter(solicitudbeca=solicitudbeca,
                                                                                  estado=ID_GESTION_ANALSIS).order_by(
                                    '-fecha')[:1].get()

                        data['datosanalisis'] = ultimagestion


                        initial.update({'observaciones': ultimagestion.comentariocorreo})

                        return render(request ,"matriculas/aplicar_beca_auto.html" ,  data)

                    else:

                        return render(request ,"matriculas/aplicar_beca.html" ,  data)


                elif action=='retirar':
                    data['title'] = 'Retirar Matricula de Estudiante'
                    matricula = Matricula.objects.get(pk=request.GET['id'])
                    if 'error' in request.GET:
                        data['error'] = request.GET['error']
                    data['matricula'] = matricula
                    data['form'] = RetiradoMatriculaForm(initial={'fecha': datetime.now().strftime("%d-%m-%Y")})
                    rubros = Rubro.objects.filter(inscripcion= matricula.inscripcion,cancelado=False).values('id')
                    form2 = RubrosCambioProgramacionForm()
                    form2.rubros_list(rubros)
                    data['form2']=form2
                    data['op']='mat'
                    data['rubros']= Rubro.objects.filter(inscripcion= matricula.inscripcion,cancelado=False)
                    return render(request ,"matriculas/retiro_matricula.html" ,  data)
                    # return render(request ,"matriculas/retirar_matriculabs.html" ,  data)
                elif action=='obs_absento':
                    data['title'] = 'Adicionar Observacion del Estudiante'
                    matricula = Matricula.objects.get(pk=request.GET['id'])
                    data['form'] = ObservacionMatriculaForm()
                    data['matricula'] = matricula
                    return render(request ,"matriculas/addobservacion.html" ,  data)

                elif action=='editobs_absento':
                    data['title'] = 'Editar Observacion en Matricula del Estudiante'
                    observacion = ObservacionMatricula.objects.get(pk=request.GET['id'])
                    initial = model_to_dict(observacion)
                    data['form'] = ObservacionMatriculaForm(initial=initial)
                    data['observacion'] = observacion
                    return render(request ,"matriculas/editobservacion.html" ,  data)

                elif action=='observaciones':
                    data['title'] = 'Observaciones de Estudiantes'
                    matricula = Matricula.objects.get(pk=request.GET['id'])
                    data['observaciones'] = matricula.observacionmatricula_set.all()
                    data['matricula'] = matricula
                    return render(request ,"matriculas/observaciones.html" ,  data)

                elif action=='delobs_absento':
                    data['title'] = 'Eliminar Observacion de Matricula'
                    data['observacion'] = ObservacionMatricula.objects.get(pk=request.GET['id'])
                    return render(request ,"matriculas/delobservacion.html" ,  data)

                elif action=='materias':
                    ret_nivel = None
                    if 'ret_nivel' in request.GET:
                        ret_nivel = request.GET['ret_nivel']
                    data['ret_nivel'] = ret_nivel if ret_nivel else ""
                    matricula = Matricula.objects.get(pk=request.GET['id'])
                    materias = matricula.materiaasignada_set.all()
                    if 'conf' in request.GET:
                        data['conf']= request.GET['conf']
                    data['matricula'] = matricula
                    data['materias'] = materias
                    if matricula.nivel.nivelmalla_id == NIVEL_MALLA_UNO:
                        materiasnodisponibles = Materia.objects.filter(cerrado=False)
                    else:
                        materiasnodisponibles = Materia.objects.filter(cerrado=False, nivel__periodo=matricula.nivel.periodo)

                    disponibles = []
                    for materiad in materiasnodisponibles:
                        if not materiad.asignatura.id in disponibles:
                            disponibles.append(materiad.asignatura.id)
                    tomadas=[]
                    for materiad in materias:
                        if not materiad.materia.asignatura.id in tomadas:
                            tomadas.append(materiad.materia.asignatura.id)

                    data['asignaturaslibres'] = Asignatura.objects.filter(id__in=disponibles).exclude(recordacademico__inscripcion=matricula.inscripcion).exclude(materia__materiaasignada__matricula=matricula).distinct().order_by('nombre')

                    data['records'] = RecordAcademico.objects.filter(inscripcion=matricula.inscripcion,aprobada=False).order_by('asignatura').exclude(asignatura__id__in=tomadas)

                    data['recordsp'] = RecordAcademico.objects.filter(inscripcion=matricula.inscripcion,aprobada=True).order_by('asignatura')
                    data['genera_rubro_derecho'] = GENERAR_RUBRO_DERECHO
                    return render(request ,"matriculas/materiasbs.html" ,  data)
                elif action=='derechoexamen':
                    materiaasignada = MateriaAsignada.objects.get(pk=request.GET['id'])
                    paralelo = materiaasignada.matricula.nivel.paralelo
                    inscripcion = materiaasignada.matricula.inscripcion
                    asignatura = materiaasignada.materia.asignatura.nombre
                    tipo_derecho = TipoOtroRubro.objects.get(pk=TIPO_DERECHOEXAMEN_RUBRO)
                    hoy = datetime.now().today()
                    vence = materiaasignada.materia.fin
                    #Se crea el Rubro con la fecha de hoy y el vencimiento es la fecha fin de la materia
                    rubro = Rubro(fecha=hoy,valor=VALOR_DERECHOEXAMEN_RUBRO,inscripcion=inscripcion,cancelado=False,fechavence=vence)
                    rubro.save()
                    #Se crea el tipo de Rubro Otro q es de tipo Derecho Examen
                    rubroo = RubroOtro(rubro=rubro, tipo=tipo_derecho, descripcion=asignatura+"-"+paralelo)
                    rubroo.save()
                    return HttpResponseRedirect("/matriculas?action=materias&id="+str(materiaasignada.matricula.id)+"&conf=Rubro adicionado correctamente.")
                elif action=='delmateria':
                    data['title'] = 'Eliminar Materia de Asignadas'
                    data['materiaasignada'] = MateriaAsignada.objects.get(pk=request.GET['id'])
                    return render(request ,"matriculas/borrar_materiabs.html" ,  data)

                elif action=='promote':
                    try:
                        recordAcademico = RecordAcademico.objects.get(pk=request.GET['record'])
                        matricula = Matricula.objects.get(pk=request.GET['matricula'])
                        data['title'] = 'Seleccion de Materia'
                        asignatura = recordAcademico.asignatura
                        data['materias'] = Materia.objects.filter(asignatura=asignatura, nivel__periodo__activo=True, cerrado=False, nivel__cerrado=False)
                        data['matricula'] = matricula
                        data['asignatura'] = asignatura
                        return render(request ,"matriculas/seleccionar_materiabs.html" ,  data)
                    except Exception as ex:
                        return HttpResponseRedirect("/")
                elif action=='freepromote':
                    asignatura = Asignatura.objects.get(pk=request.GET['asignatura'])
                    matricula = Matricula.objects.get(pk=request.GET['matricula'])
                    data['title'] = 'Seleccion de Materia'
                    if VALIDA_MATERIA_APROBADA:
                        data['materias'] = Materia.objects.filter(asignatura=asignatura, nivel__periodo__activo=True,aprobada=True)
                    else:
                        data['materias'] = Materia.objects.filter(asignatura=asignatura, nivel__periodo__activo=True)
                    data['matricula'] = matricula
                    data['asignatura'] = asignatura
                    return render(request ,"matriculas/seleccionar_materiabs.html" ,  data)
                elif action=='promote2':
                    materia = Materia.objects.get(pk=request.GET['materia'])
                    matricula = Matricula.objects.get(pk=request.GET['matricula'])
                    inscripcion = matricula.inscripcion
                    # if inscripcion.recordacademico_set.filter(asignatura=materia.asignatura).exists():
                    #     recordAcademico = inscripcion.recordacademico_set.filter(asignatura=materia.asignatura)[:1].get()
                    #     materiaAsignada = MateriaAsignada(matricula=matricula,materia=materia,
                    #                             notafinal=recordAcademico.nota,asistenciafinal=recordAcademico.asistencia,supletorio=0)
                    #     materiaAsignada.save()
                    #     recordAcademico.delete()
                    # else:
                    materiaAsignada = MateriaAsignada(matricula=matricula,materia=materia,
                                                    notafinal=0,asistenciafinal=0,supletorio=0)
                    materiaAsignada.save()

                    # Log de ADICIONAR MATERIA ASIGNADA
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(materiaAsignada).pk,
                        object_id       = materiaAsignada.id,
                        object_repr     = force_str(materiaAsignada),
                        action_flag     = ADDITION,
                        change_message  = 'Adicionada Materia Asignada')

                    return HttpResponseRedirect("/matriculas?action=materias&id="+str(matricula.id))

                elif action=='matproxnivel':
                    nivel = Nivel.objects.get(pk=request.GET['id'])
                    form = MatriculaProxNivelForm()
                    form.for_carrera(nivel)
                    data['form'] = form
                    data['nivel'] = nivel
                    return render(request ,"matriculas/matproxnivel.html" ,  data)

                elif action=='liberar':
                    try:
                        data['title'] = 'Liberar Matricula'
                        matricula = Matricula.objects.get(pk=request.GET['id'])
                        data['matricula'] = matricula
                        form = MotivoLiberadaForm()
                        data['form'] = form
                        data['accion'] = 'liberar'

                        return render(request ,"matriculas/liberarmatricula.html" ,  data)
                    except Exception as ex:
                        return HttpResponseRedirect("/")

                elif action=='quitarliberar':
                    try:
                        data['title'] = 'Eliminar Liberar Matricula'
                        matricula = Matricula.objects.get(pk=request.GET['id'])
                        data['matricula'] = matricula
                        form = MotivoLiberadaForm()
                        data['form'] = form
                        data['accion'] =  'quitarliberar'
                        return render(request ,"matriculas/liberarmatricula.html" ,  data)
                    except Exception as ex:
                        return HttpResponseRedirect("/")

                elif action=='descuento':
                    data['inscripcion'] = Inscripcion.objects.get(pk=request.GET['id'])

                    data['matricula']= Matricula.objects.filter(id=request.GET['matricula']).values('id')
                    data['url'] = 'matriculas?action=matricula&id='+ request.GET['nivel']
                    data['form1'] = BecaParcialForm()

                    rubros = Rubro.objects.filter(inscripcion=data['inscripcion'],cancelado=False).values('id')
                    form = DetalleDescuentoForm()
                    form.rubros_list(rubros)
                    if 'tipobeca' in request.GET:
                        data['tipobeca']=TipoBeca.objects.get(pk=request.GET['tipobeca'])
                    if 'tipobeneficio' in request.GET:
                        data['tipobeneficio']=TipoBeneficio.objects.get(pk=request.GET['tipobeneficio'])
                    if 'porcientobeca' in request.GET:
                        data['porcientobeca']=request.GET['porcientobeca']
                    if 'motivobeca' in request.GET:
                        data['motivobeca']=MotivoBeca.objects.get(pk=request.GET['motivobeca'])

                    if 'observaciones' in request.GET:
                        data['observaciones']=request.GET['observaciones']

                    if 'fechabeca' in request.GET:
                        data['fechabeca'] = str(request.GET['fechabeca'])

                    if 'nivel' in request.GET:
                        data['nivel']= (request.GET['nivel'])

                    if 'becado' in request.GET:
                        data['becado']= (request.GET['becado'])

                    if 'becaparcial' in request.GET:
                        data['becaparcial']= (request.GET['becaparcial'])

                    data['rubros']= Rubro.objects.filter(inscripcion=data['inscripcion'],cancelado=False)
                    data['form']= form
                    return render(request ,"matriculas/beca_parcial.html" ,  data)

                elif action=='recalcularubroscreditos':
                    matricula = Matricula.objects.get(pk=request.GET['id'])
                    matricula.recalcular_rubros_segun_creditos()
                    return HttpResponseRedirect("/matriculas?action=matricula&id="+str(matricula.nivel.id))

                elif action == 'actualizapromocion':
                    #OCastillo 15-05-2023 aplica la promocion descuento en cuota a todos los niveles a estudiantes matriculados luego del cambio en validacion
                    matricula = Matricula.objects.filter(id=request.GET['id'])[:1].get()
                    lista2=[]
                    for pn in TIPOS_PAGO_NIVEL:
                        if 'CUOTA' in pn[1]:
                            lista2.append(pn[0])

                    if matricula.inscripcion.promocion:

                        inscripcion = matricula.inscripcion
                        if inscripcion.promocion.descuentomaterial and inscripcion.promocion.valdescuentomaterial > 0 and matricula.nivel.nivelmalla.id == NIVEL_MALLA_UNO:
                            try:
                                if RubroOtro.objects.filter(matricula=matricula.id,
                                                            tipo__id=TIPO_RUBRO_MATERIALAPOYO,
                                                            rubro__inscripcion=matricula.inscripcion).exists():
                                    rmaterial = RubroOtro.objects.filter(matricula=matricula.id,
                                                                         tipo_id=TIPO_RUBRO_MATERIALAPOYO,
                                                                         rubro__inscripcion=matricula.inscripcion)[
                                                :1].get()
                                    rubro = rmaterial.rubro
                                else:
                                    valormaterialapoyo= inscripcion.promocion.valormaterialapoyo
                                    rubro = Rubro(fecha=datetime.today().date(),
                                                  valor=valormaterialapoyo,
                                                  inscripcion=inscripcion,
                                                  cancelado=True, fechavence=datetime.now())

                                    rubro.save()
                                    rmaterial = RubroOtro(rubro=rubro, matricula=matricula.id,
                                                          tipo_id=TIPO_RUBRO_MATERIALAPOYO,
                                                          descripcion='MATERIALES DE APOYO'
                                                          )
                                    rmaterial.save()
                                if rmaterial:
                                    if not DetalleDescuento.objects.filter(rubro=rubro).exists():
                                        descuento = round(((
                                                                   rubro.valor * inscripcion.promocion.valdescuentomaterial) / 100),
                                                          2)
                                        rubro.valor = rubro.valor - round(
                                            ((
                                                     rubro.valor * inscripcion.promocion.valdescuentomaterial) / 100),
                                            2)
                                        rubro.save()
                                        desc = Descuento(inscripcion=matricula.inscripcion,
                                                         motivo='DESCUENTO PROMOCION',
                                                         total=rubro.valor,
                                                         fecha=datetime.today().date())
                                        desc.save()
                                        detalle = DetalleDescuento(descuento=desc,
                                                                   rubro=rubro,
                                                                   valor=descuento,
                                                                   porcentaje=inscripcion.promocion.valdescuentomaterial)
                                        detalle.save()
                                        msj = 'Actualiza Descuento promocion material ('
                                    else:
                                        msj = 'No se actualizo el valor ('
                            except Exception as e:
                                from sga.pre_inscripciones import email_error_congreso
                                print(e)
                                pass
                                errores = []
                                errores.append((
                                    'Error al generar descuento en materiasl de apoyo ' + str(
                                        matricula.id),
                                    str(inscripcion.id)))
                                if errores:
                                    email_error_congreso(errores,
                                                 'ERROR EN MATRICULAS GENERAR DESCUENTO')
                        else:
                            for pago in matricula.nivel.pagonivel_set.filter(tipo__in=lista2):
                                if pago.tipo!=0 and matricula.inscripcion.promocion.todos_niveles and DEFAULT_PASSWORD == 'itb' and matricula.nivel.nivelmalla.id != NIVEL_MALLA_UNO:
                                    if matricula.nivel.nivelmalla.id != NIVEL_GRADUACION and matricula.nivel.nivelmalla.id != NIVEL_SEMINARIO:
                                        if Rubro.objects.filter(inscripcion=matricula.inscripcion,cancelado=False,tiponivelpago=pago.tipo).exists():
                                           r = Rubro.objects.get(inscripcion=matricula.inscripcion,cancelado=False,tiponivelpago=pago.tipo)
                                           if not DetalleDescuento.objects.filter(rubro =r,porcentaje = matricula.inscripcion.descuentoporcent).exists():
                                                des = ((100-matricula.inscripcion.descuentoporcent)/100.0)
                                                descuento = round(((r.valor * matricula.inscripcion.descuentoporcent)/100),2)
                                                r.valor *= des
                                                r.save()

                                                desc = Descuento(inscripcion = matricula.inscripcion,
                                                             motivo ='DESCUENTO EN CUOTAS',
                                                             total = r.valor,
                                                             fecha = datetime.today().date())
                                                desc.save()

                                                detalle = DetalleDescuento(descuento =desc,
                                                                       rubro =r,
                                                                       valor = descuento,
                                                                       porcentaje = matricula.inscripcion.descuentoporcent)
                                                detalle.save()
                                                msj='Actualiza rubros promocion todos los niveles ('
                        #Obtain client ip address
                        client_address = ip_client_address(request)

                        # Log de CAMBIAR RUBROS PROMOCION TODOS LOS NIVELES
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(matricula).pk,
                            object_id       = matricula.id,
                            object_repr     = force_str(matricula),
                            action_flag     = ADDITION,
                            change_message  =  msj + client_address + ')' )

                    return HttpResponseRedirect("/matriculas?action=matricula&id="+str(matricula.nivel.id))


                return HttpResponseRedirect("/matriculas")
            else:
                if MODELO_EVALUACION==EVALUACION_TES:
                    return HttpResponseRedirect("/niveles")
    #            data['periodo'] = Periodo.periodo_vigente()
                periodo = Periodo.objects.get(pk=request.session['periodo'].id)
                carreras = Carrera.objects.filter(grupocoordinadorcarrera__group__in=request.user.groups.all()).exclude(activo=False).distinct().order_by('nombre')
                data['carreras'] = carreras
                niveles = Nivel.objects.filter(periodo=data['periodo'], carrera__in=data['carreras']).order_by('paralelo')
                data['niveles'] = niveles
                sedes = Sede.objects.filter(solobodega=False)
                data['sedes'] = sedes
                data['niveles_abiertos'] = niveles.filter(cerrado=False).order_by('paralelo')
                data['usa_nivel0'] = UTILIZA_NIVEL0_PROPEDEUTICO
                # data['inscritos'] = Inscripcion.objects.filter(fecha__gte=data['periodo'].inicio,fecha__lte=data['periodo'].fin).count()
                data['matriculados'] = Matricula.objects.filter(nivel__periodo=data['periodo']).count()
                data['becados'] = Matricula.objects.filter(nivel__periodo=data['periodo'],becado=True).count()
                data['egresados'] = Egresado.objects.filter(fechaegreso__gte=data['periodo'].inicio,fechaegreso__lte=data['periodo'].fin).count()
                data['graduados'] = Graduado.objects.filter(fechagraduado__gte=data['periodo'].inicio,fechagraduado__lte=data['periodo'].fin).count()
                data['inactivos'] = Matricula.objects.filter(nivel__periodo=data['periodo'],inscripcion__persona__usuario__is_active=False).count()
                data['retirados'] = RetiradoMatricula.objects.filter(nivel__periodo=data['periodo']).count()

                if 'c' in request.GET:
                    if request.GET['c'] != 0:
                        data['carreras'] = carreras.filter(pk=request.GET['c'])
                        data['niveles'] = niveles.filter(carrera__in=data['carreras'])
                        niveless = niveles.filter(carrera__in=data['carreras'])
                        data['sedes'] = sedes
                        if sedes.filter(id__in=niveless.values('sede')).exists():
                            data['sede'] = sedes.filter(id__in=niveless.values('sede'))[:1].get()
                        data['filtro'] = True

                if 'n' in request.GET:
                    data['niveles'] = ''
                    data['filtro'] = True
                    nivel = Nivel.objects.filter(pk=request.GET['n'])
                    if nivel.filter(periodo=periodo).exists():
                        data['carreras'] = carreras.filter(id__in=nivel.values('carrera'))
                        data['niveles'] = nivel
                        data['sedes'] = sedes.filter(id__in=nivel.values('sede'))
                        data['sede'] = sedes.filter(id__in=nivel.values('sede'))[:1].get()
                    else:
                        print('NO EXISTE NIVEL EN ESTE PERIODO')
                        data['msj']='EL NIVEL '+nivel[:1].get().paralelo+' SE ENCUENTRA EN EL PERIODO: '+nivel[:1].get().periodo.nombre

                data['formcargamasiva'] = CargaMasivaGraduacionForm(initial={'fecha':datetime.now().date(),'fechavencimiento':datetime.now().date()})
                return render(request ,"matriculas/matriculasbs.html" ,  data)

        except Exception as e:
            return HttpResponseRedirect('/?info='+str(e))


def mail_correosolicitudsecretariaaplica(contenido,email,user,estudiante,carrera,email_estudiante,nivel_est):
        hoy = datetime.now().today()
        persona = Persona.objects.get(usuario=user)
        send_html_mail(str('ENVIO INFORMACION DE LA BECA QUE SE APLICO'),"emails/correoaplicosecretaria.html", {'fecha': hoy,"user":user,'contenido': contenido,'persona':persona,'estudiante':estudiante,'carrera':carrera,'email_estudiante':email_estudiante,'nivel_est':nivel_est},email.split(","))


def mail_correocrisfe(contenido,email,user,estudiante,carrera,email_estudiante,nivel_est):
        hoy = datetime.now().today()
        persona = Persona.objects.get(usuario=user)
        send_html_mail(str('ENVIO INFORMACION CASO CRISFE'),"emails/correoparaverificarcasocrisfe.html", {'fecha': hoy,"user":user,'contenido': contenido,'persona':persona,'estudiante':estudiante,'carrera':carrera,'email_estudiante':email_estudiante,'nivel_est':nivel_est},email.split(","))

