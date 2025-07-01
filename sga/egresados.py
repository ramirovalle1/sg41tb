from datetime import datetime
import json
from django.contrib.admin.models import LogEntry, CHANGE, DELETION, ADDITION
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models.query_utils import Q
from django.forms.models import model_to_dict
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.utils.encoding import force_str
from decorators import secure_module
from sga.reportes import elimina_tildes
from settings import DEFAULT_PASSWORD, PROFESORES_GROUP_ID, ALUMNOS_GROUP_ID, EXAMEN_PRACTI_COMPLEX, EXAMEN_TEORI_COMPLEX, NIVEL_MALLA_CERO, \
    ASIGNATURA_EXAMEN_GRADO_CONDU,CARRERAS_ID_EXCLUIDAS_INEC, EXAMEN_TEORIPORC_COMPLEX, EXAMEN_PRACTIPORC_COMPLEX,ASIST_PARA_APROBAR, NUMERO_PREGUNTA, \
    NOTA_PARA_APROBAR, EMAIL_ACTIVE,TIPO_OTRO_RUBRO
from sga.commonviews import addUserData, ip_client_address
from django.template import RequestContext
from sga.forms import PersonaForm, InscripcionForm, RecordAcademicoForm, HistoricoRecordAcademicoForm, GraduadoForm, EgresadoForm,IngresoDocenteForm
from sga.models import Profesor, Persona, Inscripcion, RecordAcademico, DocumentosDeInscripcion, HistoricoRecordAcademico, Graduado, Carrera,\
    Egresado, ExamenPractica, ExamenPracticaDet, DetExamenVali, InscripcionExamen, DetalleExamen, Detvalidaexamen, AsignaturaMalla, IndicEvaluacionExamen,\
    NivelMalla,EjeFormativo, ProfeExamenPractica, NotasComplexivo, NotasComplexivoDet, TituloExamenCondu,SolicitudOnline,SolicitudEstudiante,TipoEspecieValorada,\
    Rubro,RubroEspecieValorada,RubroOtro

from django.db.models.aggregates import Sum, Max
from sga.alu_malla import aprobadaAsignatura
import threading

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

class EspecieSerieGenerador:
    def __init__(self):
        self.__lock = threading.RLock()

    def generar_especie(self, rubro, tipo):
        self.__lock.acquire()
        try:
            serie = 0
            valor = RubroEspecieValorada.objects.filter(rubro__fecha__year=rubro.fecha.year).aggregate(Max('serie'))
            if valor['serie__max']!=None:
                serie = valor['serie__max']+1

            # OCU 09-junio-2017 para evitar que la serie de la especie se duplique
            if not RubroEspecieValorada.objects.filter(rubro__fecha__year=rubro.fecha.year,serie=serie).exists():
                rubroe = RubroEspecieValorada(rubro=rubro, tipoespecie=tipo, serie=serie)
                rubroe.save()

                return rubroe
            else:
                rubro.delete()
        finally:
            self.__lock.release()


generador_especies = EspecieSerieGenerador()

@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    if request.method=='POST':
        action = request.POST['action']
        if action=='edit':
            egresado = Egresado.objects.get(pk=request.POST['id'])
            f = EgresadoForm(request.POST)
            if f.is_valid():
                egresado.notaegreso = f.cleaned_data['notaegreso']
                egresado.fechaegreso = f.cleaned_data['fechaegreso']
                egresado.save()

                # Log de EDITAR EGRESADO
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(egresado).pk,
                    object_id       = egresado.id,
                    object_repr     = force_str(egresado),
                    action_flag     = CHANGE,
                    change_message  = 'Editado Egresado' )


            else:
                return HttpResponseRedirect("/egresados?action=edit&id="+str(request.POST['id']))

        elif action=='del':
            egresado = Egresado.objects.get(pk=request.POST['id'])
            egresado.delete()

            # Log de BORRAR EGRESADO
            LogEntry.objects.log_action(
                user_id         = request.user.pk,
                content_type_id = ContentType.objects.get_for_model(egresado).pk,
                object_id       = egresado.id,
                object_repr     = force_str(egresado),
                action_flag     = DELETION,
                change_message  = 'Eliminado Egresado' )
        elif action=='exampract':
            try:
                data = json.loads(request.POST['data'])
                if ExamenPractica.objects.filter(inscripcion__id = request.POST['idinscrip'],valida=True).exists():
                    return HttpResponse(json.dumps({'result':'bad', "error": str('El estudiante ya fue ingresado')}),content_type="application/json")
                examenpractica = ExamenPractica(inscripcion_id = request.POST['idinscrip'],
                                                titulo = data['titutdescr'],
                                                caso = data['casopracti'],
                                                puntaje = data['totatprome'],
                                                fecha = datetime.now(),
                                                valida=True)
                examenpractica.save()
                for doce in data['docen']:
                    profeexamenpractica = ProfeExamenPractica(profesor_id = doce['docente'],
                                                         examenpractica = examenpractica)
                    profeexamenpractica.save()
                for dato in data['datos']:
                    examenpracticadet = ExamenPracticaDet(examenpractica = examenpractica,
                                                          metodevalua = dato['metodevalua'],
                                                          escala = dato['escala'],
                                                          calif1 = dato['calificacion1'],
                                                          calif2 = dato['calificacion2'],
                                                          promedio = dato['promedio'])
                    examenpracticadet.save()

                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de ADICIONAR RUBRO OTRO
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(examenpractica).pk,
                    object_id       = examenpractica.id,
                    object_repr     = force_str(examenpractica),
                    action_flag     = ADDITION,
                    change_message  = 'Adicionado Examen practico ' + str(examenpractica) + '(' + client_address + ')' )
                return HttpResponse(json.dumps({'result':'ok'}),content_type="application/json")
            except Exception as ex:
                return HttpResponse(json.dumps({'result':'bad', "error": str('Error al Ingresar Datos')}),content_type="application/json")

        elif action=='add_complexivo':
            try:
                indice_t = IndicEvaluacionExamen.objects.get(pk=request.POST['indice_t'])
                indice_p1 = IndicEvaluacionExamen.objects.get(pk=request.POST['indice_p1'])
                indice_p2 = IndicEvaluacionExamen.objects.get(pk=request.POST['indice_p2'])
                nota_t = float(request.POST['nota_t'])
                nota_p1 = float(request.POST['nota_p1'])
                nota_p2 = float(request.POST['nota_p2'])
                if TituloExamenCondu.objects.filter(pk=request.POST['titulo_examen']).exists():
                    tituloexamencondu = TituloExamenCondu.objects.get(pk=request.POST['titulo_examen'])
                    suma_p = nota_p1+nota_p2
                    total = (suma_p*0.6)+(nota_t*0.4)
                    egresado=Egresado.objects.get(pk=request.POST['egresado'])
                    # profesor = Profesor.objects.get(pk=request.POST['profesor'])

                    # if NotasComplexivo.objects.filter(egresado=egresado).exists():
                    #     return HttpResponse(json.dumps({'result':'bad', "error": str('Estudiante ya cuenta con nota de titulacion subida')}),content_type="application/json")

                    if 'id' in request.POST:
                        notas_complexivo = NotasComplexivo.objects.get(pk=request.POST['id'])
                        notas_complexivo.teorico = nota_t
                        notas_complexivo.practico = suma_p
                        notas_complexivo.total = total
                        notas_complexivo.fecha = datetime.now().date()
                        notas_complexivo.tituloexamencondu = tituloexamencondu
                        notas_complexivo.observacion = request.POST['observacion']
                        notas_complexivo.save()

                        teorico = NotasComplexivoDet.objects.get(notascomplexivo=notas_complexivo, indiceevaluacion=indice_t)
                        teorico.calificacion = nota_t
                        teorico.save()

                        p1 = NotasComplexivoDet.objects.get(notascomplexivo=notas_complexivo, indiceevaluacion=indice_p1)
                        p1.calificacion = nota_p1
                        p1.save()

                        p2 = NotasComplexivoDet.objects.get(notascomplexivo=notas_complexivo, indiceevaluacion=indice_p2)
                        p2.calificacion = nota_p2
                        p2.save()

                        mensaje = 'Modificar notas examen complexivo'
                    else:
                        notas_complexivo = NotasComplexivo(egresado=egresado,
                                            teorico=nota_t,
                                            practico=suma_p,
                                            total=total,
                                            fecha=datetime.now().date(),
                                            tituloexamencondu=tituloexamencondu,
                                            observacion=request.POST['observacion'])
                        notas_complexivo.save()

                        teorico = NotasComplexivoDet(notascomplexivo=notas_complexivo,
                                                   indiceevaluacion=indice_t,
                                                   calificacion=nota_t)
                        teorico.save()

                        p1 = NotasComplexivoDet(notascomplexivo=notas_complexivo,
                                                   indiceevaluacion=indice_p1,
                                                   calificacion=nota_p1)
                        p1.save()

                        p2 = NotasComplexivoDet(notascomplexivo=notas_complexivo,
                                                   indiceevaluacion=indice_p2,
                                                   calificacion=nota_p2)
                        p2.save()
                        mensaje = 'Adicionar notas examen complexivo'

                    if int(notas_complexivo.total) >= int(70):
                        aprobado = True
                    else:
                        aprobado = False

                    if RecordAcademico.objects.filter(inscripcion=egresado.inscripcion, asignatura=notas_complexivo.tituloexamencondu.asignatura).exists():
                        print('EXISTE RECORD')
                        recordacademico = RecordAcademico.objects.filter(inscripcion=egresado.inscripcion, asignatura=notas_complexivo.tituloexamencondu.asignatura)[:1].get()
                        recordacademico.nota= float(notas_complexivo.total)
                        recordacademico.aprobada=aprobado
                        recordacademico.fecha=datetime.now().date()
                        recordacademico.asistencia=100
                        # mensaje = "Editando"
                        recordacademico.save()
                    else:
                        recordacademico=RecordAcademico(inscripcion=egresado.inscripcion,
                                                        asignatura=notas_complexivo.tituloexamencondu.asignatura,
                                                        nota= float(notas_complexivo.total),
                                                        aprobada=aprobado,
                                                        fecha=datetime.now().date(),
                                                        convalidacion=False,
                                                        pendiente=False,
                                                        asistencia=100)
                        recordacademico.save()
                    if HistoricoRecordAcademico.objects.filter(inscripcion=egresado.inscripcion, asignatura=notas_complexivo.tituloexamencondu.asignatura).exists():
                        print('EXISTE TEORICO')
                        historico = HistoricoRecordAcademico.objects.filter(inscripcion=egresado.inscripcion, asignatura=notas_complexivo.tituloexamencondu.asignatura)[:1].get()
                        historico.nota=float(notas_complexivo.total)
                        historico.aprobada=aprobado
                        historico.fecha=datetime.now().date()
                        historico.asistencia=100
                        # mensaje = "Editando"
                        historico.save()
                    else:
                        historico = HistoricoRecordAcademico(inscripcion=egresado.inscripcion,
                                                        asignatura=notas_complexivo.tituloexamencondu.asignatura,
                                                        nota= float(notas_complexivo.total),
                                                        aprobada=aprobado,
                                                        fecha=datetime.now().date(),
                                                        convalidacion=False,
                                                        pendiente=False,
                                                        asistencia=100)
                        historico.save()
                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de ADICIONAR EXAMEN
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(notas_complexivo).pk,
                        object_id       = notas_complexivo.id,
                        object_repr     = force_str(notas_complexivo),
                        action_flag     = ADDITION,
                        change_message  = mensaje+' ' + str(notas_complexivo) + '(' + client_address + ')' )

                    if 'id' in request.POST and EMAIL_ACTIVE:
                        notas_complexivo.correo_cambio_notas()
                    if notas_complexivo.egresado.inscripcion.persona.cedula:
                        identificacion = notas_complexivo.egresado.inscripcion.persona.cedula
                    else:
                        identificacion = notas_complexivo.egresado.inscripcion.persona.pasaporte
                    return HttpResponse(json.dumps({'result':'ok', 'cedula':str(identificacion)}),content_type="application/json")
                else:
                    print('no existe titulo')
                    return HttpResponse(json.dumps({'result':'bad', "error": str('No existe Titulo de examen para esta carrera')}),content_type="application/json")

            except Exception as ex:
                print(ex)
                return HttpResponse(json.dumps({'result':'bad', "error": str('Error al Ingresar Datos')}),content_type="application/json")

        elif action=='editexampract':
            try:
                data = json.loads(request.POST['data'])
                examenpractica = ExamenPractica.objects.filter(id=request.POST['idexamen'],inscripcion__id = request.POST['idinscrip'])[:1].get()
                examenpractica.titulo = data['titutdescr']
                examenpractica.caso = data['casopracti']
                examenpractica.puntaje = data['totatprome']
                examenpractica.fecha = datetime.now()
                examenpractica.save()
                # for det in ExamenPracticaDet.objects.filter(examenpractica = examenpractica):
                #     for dato in data['datos']:
                #         if det.id != dato['examenpractdetid']:

                lista=[]
                for doce in data['docen']:
                    if ProfeExamenPractica.objects.filter(id = doce['profeexame']).exists():
                        profeexamenpractica = ProfeExamenPractica.objects.filter(id = doce['profeexame'])[:1].get()
                        profeexamenpractica.profesor_id = doce['docente']

                    else:
                        profeexamenpractica = ProfeExamenPractica(profesor_id = doce['docente'],
                                                         examenpractica = examenpractica)
                    profeexamenpractica.save()
                    lista.append(profeexamenpractica.id)
                profeexamenpractica = ProfeExamenPractica.objects.filter(examenpractica = examenpractica).exclude(id__in=lista)
                profeexamenpractica.delete()

                lista=[]
                for dato in data['datos']:
                    if ExamenPracticaDet.objects.filter(id = dato['examenpractdetid']).exists():
                        examenpracticadet = ExamenPracticaDet.objects.filter(id = dato['examenpractdetid'])[:1].get()
                        examenpracticadet.metodevalua = dato['metodevalua']
                        examenpracticadet.escala = dato['escala']
                        examenpracticadet.calif1 = dato['calificacion1']
                        examenpracticadet.calif2 = dato['calificacion2']
                        examenpracticadet.promedio = dato['promedio']
                    else:
                        examenpracticadet = ExamenPracticaDet(examenpractica = examenpractica,
                                                          metodevalua = dato['metodevalua'],
                                                          escala = dato['escala'],
                                                          calif1 = dato['calificacion1'],
                                                          calif2 = dato['calificacion2'],
                                                          promedio = dato['promedio'])
                    examenpracticadet.save()
                    lista.append(examenpracticadet.id)
                examenpracticadet = ExamenPracticaDet.objects.filter(examenpractica = examenpractica).exclude(id__in=lista)
                examenpracticadet.delete()
                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de ADICIONAR RUBRO OTRO
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(examenpractica).pk,
                    object_id       = examenpractica.id,
                    object_repr     = force_str(examenpractica),
                    action_flag     = ADDITION,
                    change_message  = 'Editando Examen practico ' + str(examenpractica) + '(' + client_address + ')' )
                return HttpResponse(json.dumps({'result':'ok'}),content_type="application/json")
            except Exception as ex:
                return HttpResponse(json.dumps({'result':'bad', "error": str('Error al Ingresar Datos')}),content_type="application/json")
        elif action == 'validoexamen':
            try:
                examenpractica = ExamenPractica.objects.filter(id=request.POST['idexam'])[:1].get()
                if not examenpractica.valida:
                    for ex in ExamenPractica.objects.filter(valida=True,inscripcion = examenpractica.inscripcion):
                        ex.valida = False
                        ex.save()
                mensaje = 'Activando Examen' if examenpractica.valida else 'Desactivando Examen'
                examenpractica.valida = not examenpractica.valida
                examenpractica.save()
                detexamenvali = DetExamenVali(
                                            examenpractica = examenpractica,
                                            observacion = request.POST['observacionvali'],
                                            usuario = request.user,
                                            fecha = datetime.now(),
                                            activo = examenpractica.valida)
                detexamenvali.save()



                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de ADICIONAR RUBRO OTRO
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(detexamenvali).pk,
                    object_id       = detexamenvali.id,
                    object_repr     = force_str(detexamenvali),
                    action_flag     = ADDITION,
                    change_message  = mensaje+' practico ' + str(detexamenvali) + '(' + client_address + ')' )
                return HttpResponse(json.dumps({'result':'ok'}),content_type="application/json")
            except Exception as ex:
                return HttpResponse(json.dumps({'result':'bad', "error": str('Error al Ingresar Datos')}),content_type="application/json")

        elif action == 'validoexamenteor':
            try:
                # cantreprobado=0
                # data = {}
                inscripcionexamen = InscripcionExamen.objects.get(id=request.POST['idexam'])
                if not inscripcionexamen.valida:
                    for i in InscripcionExamen.objects.filter(valida=True,tituloexamencondu=inscripcionexamen.tituloexamencondu,inscripcion=inscripcionexamen.inscripcion):
                        i.valida = False
                        i.save()
                    inscripcionexamen.valida = True
                    examenpractica = ExamenPractica.objects.filter(valida=True,inscripcion=inscripcionexamen.inscripcion)[:1].get()
                    puntajenota = 0
                    if inscripcionexamen.puntaje == None:
                        inscripcionexamen.puntaje = 0
                    if int(inscripcionexamen.puntaje) >= int(EXAMEN_TEORI_COMPLEX):
                        aprobado = True
                        puntajenota = float((inscripcionexamen.puntaje*EXAMEN_TEORIPORC_COMPLEX)/100) + float((examenpractica.puntaje*EXAMEN_PRACTIPORC_COMPLEX)/100)
                    else:
                        aprobado = False
                    mensaje = 'Activando Examen'
                else:
                    inscripcionexamen.valida = False
                    mensaje = 'Desactivando Examen'
                    aprobado = False
                    puntajenota = 0

                inscripcionexamen.save()



                if RecordAcademico.objects.filter( inscripcion=inscripcionexamen.inscripcion,asignatura=inscripcionexamen.tituloexamencondu.asignatura).exists():
                        recordacademico = RecordAcademico.objects.filter(inscripcion=inscripcionexamen.inscripcion,asignatura=inscripcionexamen.tituloexamencondu.asignatura)[:1].get()
                        recordacademico.nota=float(puntajenota)
                        recordacademico.aprobada=aprobado
                        recordacademico.fecha=datetime.now().date()
                        # mensaje = "Editando"
                        recordacademico.save()
                if HistoricoRecordAcademico.objects.filter( inscripcion=inscripcionexamen.inscripcion,asignatura=inscripcionexamen.tituloexamencondu.asignatura).exists():
                    historico = HistoricoRecordAcademico.objects.filter(inscripcion=inscripcionexamen.inscripcion,asignatura=inscripcionexamen.tituloexamencondu.asignatura)[:1].get()
                    historico.nota=float(puntajenota)
                    historico.aprobada=aprobado
                    historico.fecha=datetime.now().date()
                    # mensaje = "Editando"
                    historico.save()
                detvalidaexamen = Detvalidaexamen(
                                    inscripcionexamen = inscripcionexamen,
                                    observacion = request.POST['observacionvali'],
                                    usuario = request.user,
                                    fecha = datetime.now(),
                                    activo = inscripcionexamen.valida)
                detvalidaexamen.save()
                #OCastillo 18-07-2022 si hay mas de 2 examenes reprobados se debe generar especie de complexivo
                # if HistoricoRecordAcademico.objects.filter( inscripcion=inscripcionexamen.inscripcion,asignatura=inscripcionexamen.tituloexamencondu.asignatura,aprobada=False).exists():
                #     if HistoricoRecordAcademico.objects.filter(inscripcion=inscripcionexamen.inscripcion,asignatura=inscripcionexamen.tituloexamencondu.asignatura,aprobada=False).count()>=2:
                #         cantreprobado=HistoricoRecordAcademico.objects.filter(inscripcion=inscripcionexamen.inscripcion,asignatura=inscripcionexamen.tituloexamencondu.asignatura,aprobada=False).count()
                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de Graduar en Conduccion
                LogEntry.objects.log_action(
                   user_id         = request.user.pk,
                   content_type_id = ContentType.objects.get_for_model(inscripcionexamen).pk,
                   object_id       = inscripcionexamen.id,
                   object_repr     = force_str(inscripcionexamen),
                   action_flag     = DELETION,
                   change_message  = mensaje+' Terorico (' + client_address + ')' )
                # if cantreprobado>=2:
                #     data['result'] = 'ok2'
                #     data['cantreprobado']=cantreprobado
                #     return HttpResponse(json.dumps(data), content_type="application/json")
                # else:
                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            except Exception as ex:
                print(ex)
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

        elif action=='ingresodocente':
            examen = ExamenPractica.objects.get(pk=int(request.POST['id']))
            f = IngresoDocenteForm(request.POST)
            if f.is_valid():
                try:
                    examen.profesor_id = request.POST['id_prof']
                except Exception as e:
                    pass
                examen.save()
        return HttpResponseRedirect("/egresados")
    else:
        data = {'title': 'Listado de Egresados'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='edit':
                data['title'] = 'Editar Egreso'
                egresado = Egresado.objects.get(pk=request.GET['id'])
                initial = model_to_dict(egresado)
                form = EgresadoForm(initial=initial)
                data['egresado'] = egresado
                data['form'] = form
                return render(request ,"egresados/editarbs.html" ,  data)
            elif action=='del':
                data['title'] = 'Borrar Egreso'
                data['egresado'] = Egresado.objects.get(pk=request.GET['id'])
                return render(request ,"egresados/borrarbs.html" ,  data)
            elif action=='exampract':
                data['title'] = 'Ingreso Examen Complexivo'
                egresado = Egresado.objects.get(pk=request.GET['id'])
                carrera=egresado.inscripcion.carrera

                if HistoricoRecordAcademico.objects.filter( inscripcion=egresado.inscripcion).exists():
                    c = 0
                    mallainscripcion = egresado.inscripcion.malla_inscripcion()
                    if not mallainscripcion:
                        return  HttpResponseRedirect('/egresados?info=No tiene una malla asociada')
                    if len(AsignaturaMalla.objects.filter(malla=mallainscripcion.malla).exclude(nivelmalla=NIVEL_MALLA_CERO).exclude(asignatura__id__in=ASIGNATURA_EXAMEN_GRADO_CONDU).exclude(asignatura__nivelacion=True).exclude(asignatura__promedia=False).exclude(asignatura__titulacion=True).distinct('asignatura').values('asignatura')) > len(HistoricoRecordAcademico.objects.filter( inscripcion=egresado.inscripcion).exclude(asignatura__id__in=ASIGNATURA_EXAMEN_GRADO_CONDU).exclude(asignatura__nivelacion=True).exclude(asignatura__promedia=False).exclude(asignatura__titulacion=True).distinct('asignatura').values('asignatura')):
                        return  HttpResponseRedirect('/egresados?info=Malla Incompleta no Puede Ingresar examen ')
                    # for historico in HistoricoRecordAcademico.objects.filter( inscripcion=data['inscripcion']).exclude(asignatura__id__in=ASIGNATURA_EXAMEN_GRADO_CONDU).exclude(asignatura__id=ASIGNATURA_PRACTICA_CONDUCCION):
                    # asignaturaidpro = AsignaturaMalla.objects.filter(malla=mallainscripcion.malla,nivelmalla=NIVEL_MALLA_CERO).distinct('asignatura_id').values('asignatura_id')
                    # for historico in HistoricoRecordAcademico.objects.filter( inscripcion=egresado.inscripcion).exclude(asignatura__id__in=asignaturaidpro).exclude(asignatura__id__in=ASIGNATURA_EXAMEN_GRADO_CONDU):
                    #     if historico.comprobar_aprobado():
                    #         c =c+1
                        # else:
                        #     break
                    if mallainscripcion.malla.carrera.online:
                        asistenciaparaaprobar = 0
                    else:
                        asistenciaparaaprobar = ASIST_PARA_APROBAR
                    a=AsignaturaMalla.objects.filter(malla__id=mallainscripcion.malla.id).exclude(nivelmalla__id=NIVEL_MALLA_CERO).exclude(asignatura__id__in=ASIGNATURA_EXAMEN_GRADO_CONDU).exclude(asignatura__nivelacion=True).exclude(asignatura__promedia=False).exclude(asignatura__titulacion=True).values('asignatura')
                    c = HistoricoRecordAcademico.objects.filter(asignatura__in=a, nota__gte=NOTA_PARA_APROBAR, asistencia__gte=asistenciaparaaprobar,inscripcion=egresado.inscripcion).exclude(asignatura__id__in=ASIGNATURA_EXAMEN_GRADO_CONDU).exclude(asignatura__nivelacion=True).exclude(asignatura__promedia=False).exclude(asignatura__titulacion=True).distinct('asignatura').values('asignatura')
                    if a.count() > c.count():
                    # if c < len(AsignaturaMalla.objects.filter(malla=mallainscripcion.malla).exclude(nivelmalla=NIVEL_MALLA_CERO).exclude(asignatura__id__in=ASIGNATURA_EXAMEN_GRADO_CONDU)):
                        return  HttpResponseRedirect('/egresados?info=Tiene Asignaturas Reprobadas, No puede Ingresar examen ')
                else:
                    return  HttpResponseRedirect('/egresados?info=Malla Incompleta no Puede Ingresar examen ')
                if egresado.inscripcion.tiene_deuda():
                    return  HttpResponseRedirect('/egresados?info=Tiene Deuda no puede ingresar examen ')
                if egresado.inscripcion.tiene_deudaotros():
                    data['deudaotro']=" Tiene deuda de Taller o Congreso desea continuar"
                if not egresado.inscripcion.documentos_entregados().titulo or not egresado.inscripcion.documentos_entregados().cedula \
                    or not egresado.inscripcion.documentos_entregados().votacion or not egresado.inscripcion.documentos_entregados().fotos:
                    data['deudadocu']=" Falta documentos por entregar desea continuar"
                data['egresado'] = egresado
                if not IndicEvaluacionExamen.objects.filter(estado = True,teorico = False, coordinacion=1,carrera=carrera).exists():
                    data['indicevaluacionexamenes'] = IndicEvaluacionExamen.objects.filter(estado = True,teorico = False, coordinacion=1).exclude(carrera__gte=0).order_by('prioridad')
                else:
                    if IndicEvaluacionExamen.objects.filter(estado = True,teorico = False, coordinacion=1,carrera=carrera).exists():
                        data['indicevaluacionexamenes'] = IndicEvaluacionExamen.objects.filter(estado = True,teorico = False, coordinacion=1,carrera=carrera).order_by('prioridad')
                return render(request ,"egresados/complexpract.html" ,  data)

            # PARA CARRERAS FAECAC FATV
            elif action=='add_complexivo':
                try:
                    print(request.GET)
                    data['title'] = 'Ingreso Examen Complexivo'
                    egresado = Egresado.objects.get(pk=request.GET['id'])
                    if egresado.inscripcion.puede_egresar() != "":
                        return  HttpResponseRedirect('/egresados?info= '+str(egresado.inscripcion.puede_egresar()))
                    if egresado.inscripcion.tiene_deuda():
                        return  HttpResponseRedirect('/egresados?info=Tiene Deuda no puede ingresar examen ')
                    if egresado.inscripcion.tiene_deudaotros():
                        data['deudaotro']=" Tiene deuda de Taller o Congreso desea continuar"
                    if not egresado.inscripcion.documentos_entregados().titulo or not egresado.inscripcion.documentos_entregados().cedula \
                        or not egresado.inscripcion.documentos_entregados().votacion or not egresado.inscripcion.documentos_entregados().fotos:
                        data['deudadocu']=" Falta documentos por entregar desea continuar"
                    data['egresado'] = egresado
                    data['indicevaluacionexamenes'] = IndicEvaluacionExamen.objects.filter(estado=True).exclude(coordinacion=1).order_by('-teorico','prioridad')
                    data['num_indicevaluacionexamenes'] = IndicEvaluacionExamen.objects.filter(estado=True).exclude(coordinacion=1).count()
                    num = 0
                    for i in IndicEvaluacionExamen.objects.filter(estado=True).exclude(coordinacion=1).order_by('-teorico','prioridad'):
                        num=num+1
                        data['id'+str(num)] = i.id
                        data['escala'+str(num)] = i.escala
                    # if egresado.inscripcion.carrera.coordinacion_pertenece().id==5:
                    #     titulo_examen = 16
                    # elif egresado.inscripcion.carrera.coordinacion_pertenece().id==3:
                    #     titulo_examen = 0 #no existe aun para carreras administrativas
                    # data['titulo_examen'] = titulo_examen
                    if TituloExamenCondu.objects.filter(carrera=egresado.inscripcion.carrera).exists():
                        titulo_examen = TituloExamenCondu.objects.get(carrera=egresado.inscripcion.carrera)
                        data['titulo_examen'] = titulo_examen
                    else:
                        return  HttpResponseRedirect('/egresados?info=Falta agregar un titulo de examen para la carrera: '+elimina_tildes(egresado.inscripcion.carrera.nombre))
                    return render(request ,"egresados/addcomplexivo_FAECAC_FATV.html" ,  data)
                except Exception as ex:
                    return  HttpResponseRedirect('/egresados?info='+str(ex))

            elif action=='verexampract':
                data['title'] = 'Ver Examen Complexivo'
                data['examenpracticos'] = ExamenPractica.objects.filter(inscripcion__id=request.GET['idinscrip'])
                data['nota_examen_pract']=EXAMEN_PRACTI_COMPLEX
                data['DEFAULT_PASSWORD']=DEFAULT_PASSWORD
                inscripcion = Inscripcion.objects.get(pk=request.GET['idinscrip'])
                if InscripcionExamen.objects.filter(inscripcion=inscripcion).exists():
                    data['inscripcionexamen'] = InscripcionExamen.objects.filter(inscripcion=inscripcion).order_by('tituloexamencondu','fecha')
                    data['nota_examen_teorico']=EXAMEN_TEORI_COMPLEX
                return render(request ,"egresados/verexamenpract.html" ,  data)

            elif action=='vercomplexivo_fatv': #FATV y FAECAC
                try:
                    data['title'] = 'Ver Examen Complexivo'
                    egresado = Egresado.objects.get(pk=request.GET['id'])
                    data['nota_paraaprobar']=70
                    data['DEFAULT_PASSWORD']=DEFAULT_PASSWORD
                    data['egresado'] = egresado
                    data['notascomplexivo'] = NotasComplexivo.objects.get(egresado=egresado)
                    data['notascomplexivodet'] = NotasComplexivoDet.objects.filter(notascomplexivo=data['notascomplexivo']).order_by('-indiceevaluacion__teorico','indiceevaluacion__prioridad')
                    data['indicevaluacionexamenes'] = IndicEvaluacionExamen.objects.filter(estado=True).exclude(coordinacion=1).order_by('-teorico','prioridad')
                    data['num_indicevaluacionexamenes'] = IndicEvaluacionExamen.objects.filter(estado=True).exclude(coordinacion=1).count()
                    num = 0
                    for i in IndicEvaluacionExamen.objects.filter(estado=True).exclude(coordinacion=1).order_by('-teorico','prioridad'):
                        num=num+1
                        data['id'+str(num)] = i.id
                        data['escala'+str(num)] = i.escala
                    if egresado.inscripcion.carrera.coordinacion_pertenece().id==5:
                        titulo_examen = 16
                    elif egresado.inscripcion.carrera.coordinacion_pertenece().id==3:
                        titulo_examen = 0 #no existe aun para carreras administrativas
                        data['titulo_examen'] = titulo_examen
                    return render(request ,"egresados/vercomplexivo_fatv.html" ,  data)
                except Exception as ex:
                    print(ex)
                    return  HttpResponseRedirect("/egresados?error="+str(ex))


            elif action=='verdetexamen':
                data['title'] = 'Ver Examen Complexivo'
                data['examenpractico'] = ExamenPractica.objects.filter(id=request.GET['id'])[:1].get()
                data['detalleexamen'] = ExamenPracticaDet.objects.filter(examenpractica=data['examenpractico']).order_by("id")
                data['profeexamen'] = ProfeExamenPractica.objects.filter(examenpractica=data['examenpractico'])
                data['EXAMEN_PRACTI_COMPLEX'] = EXAMEN_PRACTI_COMPLEX
                return render(request ,"egresados/verdetexapra.html" ,  data)

            elif action == 'detavaliexa':
                    try:
                        examenpractica = ExamenPractica.objects.get(pk=request.GET['id'])
                        if examenpractica.detallevalexamenexist():
                            data['detallevalida'] = examenpractica.detallevalexamenexist().order_by('fecha')
                            return render(request ,"egresados/detallexamenvali.html" ,  data)

                    except Exception as ex:
                        return  HttpResponseRedirect("/egresados")
            elif action == 'examen':


                    data['inscripcion']=Inscripcion.objects.filter(id=request.GET['idins'])[:1].get()
                        # if InscripcionExamen.objects.filter(inscripcion=data['inscripcion'],tituloexamencondu=tituloexamencondu,valida=True,finalizado=True).exists():
                        #     return  HttpResponseRedirect('/examen_conduc?info=Usted ya realizo este examen')

                    inscripcionexamen = InscripcionExamen.objects.filter(id=request.GET['id'])[:1].get()

                    preguntaexamen = DetalleExamen.objects.filter(inscripcionexamen=inscripcionexamen).order_by('id')


                    data['tituloexamencondu'] = inscripcionexamen.tituloexamencondu

                    paging = MiPaginador(preguntaexamen, NUMERO_PREGUNTA)
                    p = 1
                    try:
                        if 'page' in request.GET:
                            p = int(request.GET['page'])
                        page = paging.page(p)
                    except:
                        page = paging.page(1)
                    data['paging'] = paging
                    data['rangospaging'] = paging.rangos_paginado(p)
                    data['page'] = page
                    data['preguntaexamen'] = page.object_list
                    data['NOTA_PARA_EXAMEN_CONDUCCION'] = EXAMEN_TEORI_COMPLEX
                    data['EXAMEN_TEORIPORC_COMPLEX'] = EXAMEN_TEORIPORC_COMPLEX
                    data['DEFAULT_PASSWORD'] = DEFAULT_PASSWORD

                    return render(request ,"inscripciones/verexamencondu.html" ,  data)

            elif action=='alumalla':
                    data['title'] = 'Malla del Alumno'
                    inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                    inscripcionmalla = inscripcion.malla_inscripcion()
                    #Comprobar que exista la malla en la carrera de la inscripcion
                    if not inscripcionmalla:
                        return HttpResponseRedirect("/?info=Este estudiante no tiene ninguna malla asociada")
                    malla = inscripcionmalla.malla

                    data['inscripcion'] = inscripcion
                    data['inscripcion_malla'] = inscripcionmalla
                    data['malla'] = malla

                    data['nivelesdemallas'] = NivelMalla.objects.all().order_by('nombre')
                    data['ejesformativos'] = EjeFormativo.objects.all().order_by('nombre')
                    data['asignaturasmallas'] = [(x, aprobadaAsignatura(x, inscripcion)) for x in AsignaturaMalla.objects.filter(malla=malla)]
                    resumenNiveles = [{'id':x.id, 'horas': x.total_horas(malla), 'creditos': x.total_creditos(malla)} for x in NivelMalla.objects.all().order_by('nombre')]
                    data['resumenes'] = resumenNiveles
                    data['title'] = "Ver Malla Curricular : "+malla.carrera.nombre
                    if malla.carrera.online:
                        data['ASIST_PARA_APROBAR'] = 0
                    else:
                        data['ASIST_PARA_APROBAR'] = ASIST_PARA_APROBAR
                    return render(request ,"inscripciones/mallabs.html" ,  data)

            elif action=='ingresodocente':
                data['title'] = 'Ingresar Docente Evaluador'
                examenpractica = ExamenPractica.objects.get(inscripcion__id=request.GET['id'])
                initial = model_to_dict(examenpractica)
                form = IngresoDocenteForm(initial=initial)
                data['examen'] = examenpractica
                data['form'] = form
                return render(request ,"egresados/ingresarprofesor.html" ,  data)

            #OCastillo 18-07-2022 generar tramite examen complexivo
            # elif action=='generartramite':
            #     data = {}
            #     inscripcionexamen = InscripcionExamen.objects.get(id=request.GET['idexam'])
            #     inscripcion = inscripcionexamen.inscripcion
            #     solicitud= SolicitudOnline.objects.get(pk=3)
            #     solicitudestudiante=SolicitudEstudiante(inscripcion=inscripcion,solicitud=solicitud,tipoe_id=85,solicitado=True,fecha=datetime.now(),
            #                                             observacion='GENERADA DESDE MODULO EGRESADOS')
            #     solicitudestudiante.save()
            #     rubro = None
            #     tipoEspecie = TipoEspecieValorada.objects.get(pk=solicitudestudiante.tipoe.id)
            #
            #     rubro = Rubro(fecha=datetime.now().date(),
            #                 valor=tipoEspecie.precio,
            #                 inscripcion = solicitudestudiante.inscripcion,
            #                 cancelado=tipoEspecie.precio==0,
            #                 fechavence=datetime.now().date())
            #     rubro.save()
            #     # Rubro especie valorada
            #     rubroespecie = generador_especies.generar_especie(rubro=rubro, tipo=tipoEspecie)
            #     rubroespecie.autorizado=False
            #     rubroespecie.save()
            #
            #     if tipoEspecie.id==85:
            #         rubronuevo = Rubro(fecha=datetime.now().date(),valor=10,
            #                 inscripcion = solicitudestudiante.inscripcion,cancelado=tipoEspecie.precio==0,
            #                 fechavence=datetime.now().date())
            #         rubronuevo.save()
            #
            #         rubrootro = RubroOtro(rubro=rubronuevo,
            #                 tipo_id = TIPO_OTRO_RUBRO,
            #                 descripcion='DERECHO A COMPLEXIVO')
            #         rubrootro.save()
            #         if rubro:
            #             solicitud.rubro = rubro
            #             solicitud.save()
            #         client_address = ip_client_address(request)
            #         LogEntry.objects.log_action(
            #             user_id         = request.user.pk,
            #             content_type_id = ContentType.objects.get_for_model(solicitud).pk,
            #             object_id       = solicitud.id,
            #             object_repr     = force_str(solicitud),
            #             action_flag     = ADDITION,
            #             change_message  = 'Generada Especie desde Egresados (' + client_address + ')' )
            #
            #         data['result'] = 'ok'
            #         return HttpResponse(json.dumps(data),content_type="application/json")

        else:
            search = None
            if 's' in request.GET:
                search = request.GET['s']

            g=Graduado.objects.all().values('inscripcion')
            filtro = None
            if 'filter' in request.GET:
                filtro = request.GET['filter']

            if search:
                ss = search.split(' ')
                while '' in ss:
                    ss.remove('')
                if len(ss)==1:
                    #OCastillo 13-08-2020 se quita exclusion de graduados
                    #egresados = Egresado.objects.filter(Q(inscripcion__persona__nombres__icontains=search) | Q(inscripcion__persona__apellido1__icontains=search) | Q(inscripcion__persona__apellido2__icontains=search) | Q(inscripcion__persona__cedula__icontains=search) | Q(inscripcion__persona__pasaporte__icontains=search)).exclude(inscripcion__in=g).order_by('inscripcion__persona__apellido1')
                    egresados = Egresado.objects.filter(Q(inscripcion__persona__nombres__icontains=search) | Q(inscripcion__persona__apellido1__icontains=search) | Q(inscripcion__persona__apellido2__icontains=search) | Q(inscripcion__persona__cedula__icontains=search) | Q(inscripcion__persona__pasaporte__icontains=search)).order_by('inscripcion__persona__apellido1')
                else:
                    #OCastillo 13-08-2020 se quita exclusion de graduados
                    #egresados = Egresado.objects.filter(Q(inscripcion__persona__apellido1__icontains=ss[0]) & Q(inscripcion__persona__apellido2__icontains=ss[1])).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres').exclude(inscripcion__in=g)
                    egresados = Egresado.objects.filter(Q(inscripcion__persona__apellido1__icontains=ss[0]) & Q(inscripcion__persona__apellido2__icontains=ss[1])).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')
            else:
                egresados = Egresado.objects.all().exclude(inscripcion__in=g).order_by('inscripcion__persona')

            if filtro:
                if  Carrera.objects.filter(pk=filtro).exists():
                    carrera = Carrera.objects.get(pk=filtro)
                else:
                    carrera = Carrera.objects.all()[:1].get()
                #OCastillo 13-08-2020 se quita exclusion de graduados
                #egresados = Egresado.objects.filter(inscripcion__carrera=carrera).exclude(inscripcion__in=g).order_by('inscripcion__persona__apellido1', 'inscripcion__persona__apellido2')
                # egresados = Egresado.objects.filter(inscripcion__carrera=carrera).order_by('inscripcion__persona__apellido1', 'inscripcion__persona__apellido2')
                egresados = Egresado.objects.filter(inscripcion__carrera=carrera).order_by('-fechaegreso','inscripcion__persona__apellido1', 'inscripcion__persona__apellido2')

            paging = MiPaginador(egresados, 30)
            p=1
            try:
                if 'page' in request.GET:
                    p = int(request.GET['page'])
                page = paging.page(p)
            except:
                page = paging.page(1)

            paging.rangos_paginado(p)
            data['paging'] = paging
            data['page'] = page
            data['search'] = search if search else ""
            data['egresados'] = page.object_list
            data['DEFAULT_PASSWORD'] = DEFAULT_PASSWORD
            if 'info' in request.GET:
                data['info'] = request.GET['info']
            if 'idexam' in request.GET:
                data['examenpractica'] = ExamenPractica.objects.filter(id=request.GET['idexam'])[:1].get()

            if 'error' in request.GET:
                data['error'] = request.GET['error']

            data['filter'] = carrera if filtro else ""
            data['carreras'] = Carrera.objects.filter(activo=True).exclude(id__in = CARRERAS_ID_EXCLUIDAS_INEC).order_by('nombre')
            return render(request ,"egresados/egresadosbs.html" ,  data)