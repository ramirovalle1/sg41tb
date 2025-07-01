# -*- coding: latin-1 -*-
from datetime import datetime, timedelta
import json
from lib2to3.pytree import convert
import os
import time
import random
#import datetime
import xlwt
import xlrd
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.template.loader import get_template
from django.db.models.aggregates import Max
from django.forms.models import model_to_dict
from django.http import HttpResponseRedirect, HttpResponse, Http404, JsonResponse
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
from django.db.models.query_utils import Q
from decorators import secure_module
from settings import CALCULA_FECHA_FIN_MATERIA, REPORTE_CRONOGRAMA_MATERIAS, TIPO_PERIODO_PROPEDEUTICO, NIVEL_MALLA_CERO, EVALUACION_ITB, MODELO_EVALUACION, \
    GENERAR_RUBROS_PAGO, EVALUACION_TES, EVALUACION_IGAD, EMAIL_ACTIVE,CENTRO_EXTERNO,DEFAULT_PASSWORD,MODULO_FINANZAS_ACTIVO,ASIGNATURA_PRACTICA_CONDUCCION,\
    INSCRIPCION_CONDUCCION,NOTA_PARA_APROBAR,ASIST_PARA_APROBAR, ASIG_VINCULACION, CANTIDAD_ASIGNATURAS, DOCENTE_POR_DEFINIR, VALIDA_MATERIA_APROBADA,HABILITA_DESC_MATRI,\
    VALIDA_PRECEDENCIA,API_URL_ITB,RUBRO_TIPO_CURSOS,ASIGNATURA_SEMINARIO,COORDINADOR_GROUP_ID,NOTA_ESTADO_APROBADO,MEDIA_ROOT, TIPO_PAGOS_EXAMEN_DE_ADMISION, TIPO_PAGOS_CURSO_DE_NIVELACION, TIPO_ID_OTRO_RUBRO_EXAMEN_ADMISION, TIPO_ID_OTRO_RUBRO_CURSO_NIVELACION, TIPO_PAGOS_INGLES, TIPO_ID_OTRO_RUBRO_INGLES, TIPO_OTRO_RUBRO, VALOR_HORA_MINIMO, VALOR_HORA_MAXIMO, \
INCIDENCIA_CIERRENIVELFATV,INCIDENCIA_CIERRENIVELFACES,INCIDENCIA_CIERRENIVELFASS
from sga.commonviews import addUserData, ip_client_address
from sga.distributivo import elimina_tildes
from sga.forms import Inscripcion, NivelForm, NivelFormEdit, MateriaForm, NivelPropedeuticoForm, ProfesorMateriaFormAdd, PagoNivelForm, \
     PagoNivelEditForm, AsignarMateriaGrupoForm, NivelLibreForm, AdicionarOtroRubroForm, MateriaFormCext, ObservacionAbrirMateriaForm, \
     FechasForm, MateriaCursoBuckForm,PagoCursoForm, EstudianteInglesForm, LogQuitarAsignacionProfesorForm, TutorForm2, AgregarPagoNivelMatriculaForm,\
     ValorporMateriaForm
from sga.models import Periodo, Sede, Carrera, Nivel, Materia, Feriado, NivelMalla, Malla, AsignaturaNivelacionCarrera, ProfesorMateria, \
     MateriaAsignada, RecordAcademico, HistoricoRecordAcademico, HistoriaNivelesDeInscripcion, HistoricoNotasITB, Clase, PagoNivel, Rubro,\
     RubroMatricula, RubroCuota, Leccion, AsistenciaLeccion, Coordinacion, NivelLibreCoordinacion, RubroOtro,Matricula,Profesor,Persona,\
     TipoIncidencia,MateriaNivel,TIPOS_PAGO_NIVEL,DetalleDescuento,Asignatura,PagosCursoITB,DetallePagosITB,LogAceptacionProfesorMateria,\
     EvaluacionAlcance,TituloInstitucion,Descuento,PagoNivelLog,RegistroValorporDocente
# from time import sleep
from sga.pro_cronograma import mail_correoprofe
from sga.reportes import elimina_tildes
from ext.models import *
from sga.tasks import send_html_mail

def convert_fecha(s):
    return datetime(int(s[6:10]), int(s[3:5]), int(s[0:2]))

def convertir_aniomesdia(s):
    return datetime(int(s[6:10]), int(s[3:5]), int(s[0:2])).date()


def mail_correocronograma(contenido,asunto,email,user,materias,materiasnivel):
        hoy = datetime.now().today()
        persona = Persona.objects.get(usuario=user)
        send_html_mail(str(asunto),"emails/correocronograma.html", {'fecha': hoy,"user":user,'contenido': contenido, 'asunto': asunto,'persona':persona,'materias':materias,'materiasnivel':materiasnivel},email.split(","))


def mail_correocambioplanpago(contenido,asunto,user,pagonivel,motivo):
        tipo = TipoIncidencia.objects.get(pk=TIPO_INCIDENCIA_SECRETARIA)
        hoy = datetime.now().today()
        if Coordinacion.objects.filter(carrera=pagonivel.nivel.carrera).exists():
            coor = Coordinacion.objects.filter(carrera=pagonivel.nivel.carrera)[:1].get()
            correo=  tipo.correo + ',' + str(coor.correo)
            send_html_mail(str(asunto),"emails/cambioplanpagos.html", {'fecha': hoy,"user":user,'contenido': contenido, 'asunto': asunto,'pagonivel':pagonivel,'motivo':motivo},correo.split(","))


def mail_correoaddplanpago(contenido,asunto,user,pagonivel,motivo,pagonombre):
        tipo = TipoIncidencia.objects.get(pk=TIPO_INCIDENCIA_SECRETARIA)
        hoy = datetime.now().today()
        if Coordinacion.objects.filter(carrera=pagonivel.nivel.carrera).exists():
            coor = Coordinacion.objects.filter(carrera=pagonivel.nivel.carrera)[:1].get()
            correo=  tipo.correo + ',' + str(coor.correo)
            send_html_mail(str(asunto),"emails/addplanpago.html", {'fecha': hoy,"user":user,'contenido': contenido, 'asunto': asunto,'pagonombre':pagonombre,'nivel':pagonivel.nivel,'motivo':motivo,'pagonivel':pagonivel},correo.split(","))

def mail_correoadddescuentopago(contenido,asunto,user,pagonivel,porcentajedescuento,observacion,carrera):
        tipo = TipoIncidencia.objects.get(pk=TIPO_INCIDENCIA_SECRETARIA)
        hoy = datetime.now().today()
        if Coordinacion.objects.filter(carrera=carrera).exists():
            coor = Coordinacion.objects.filter(carrera=carrera)[:1].get()
            correo=  tipo.correo + ',' + str(coor.correo)
            send_html_mail(str(asunto),"emails/adddescuentoplanpago.html", {'fecha': hoy,"user":user,'contenido': contenido, 'asunto': asunto,'pagonivel':pagonivel,'porcentajedescuento':porcentajedescuento,'observacion':observacion},correo.split(","))






@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action=='add':
                periodo = request.session['periodo']
                if periodo.tipo.id == TIPO_PERIODO_PROPEDEUTICO:
                    f = NivelPropedeuticoForm(request.POST)
                    if f.is_valid():

                        carrera = f.cleaned_data['carrera']
                        sede = f.cleaned_data['sede']
                        sesion = f.cleaned_data['sesion']
                        grupo = f.cleaned_data['grupo']
                        if not  Nivel.objects.filter(carrera = carrera,periodo =periodo,sede =sede,sesion = sesion ,nivelmalla__id =NIVEL_MALLA_CERO ,malla = Malla.objects.get(carrera=carrera, vigente=True) ,grupo=grupo).exists():
                            nivel = Nivel(carrera=carrera,
                                        periodo=periodo,
                                        sede=sede,
                                        sesion=sesion,
                                        nivelmalla = NivelMalla.objects.get(pk=NIVEL_MALLA_CERO),
                                        malla = Malla.objects.get(carrera=carrera, vigente=True),
                                        grupo = grupo,
                                        paralelo = grupo.nombre,
                                        inicio = f.cleaned_data['inicio'],
                                        fin = f.cleaned_data['fin'])
                            nivel.save()

                            nivel.crea_cronograma_pagos() #Crea el cronograma de pagos del nivel

                            #Obtain client ip address
                            client_address = ip_client_address(request)

                            # Log de ADICIONADO CRONOGRAMA DE PAGOS
                            LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(nivel).pk,
                                object_id       = nivel.id,
                                object_repr     = force_str(nivel),
                                action_flag     = ADDITION,
                                change_message  = 'Adicionado Cronograma de Pagos (' + client_address  + ')')

                            #Obtain client ip address
                            client_address = ip_client_address(request)

                            # Log de ADICIONAR NIVEL
                            LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(nivel).pk,
                                object_id       = nivel.id,
                                object_repr     = force_str(nivel),
                                action_flag     = ADDITION,
                                change_message  = 'Adicionado Nivel (' + client_address + ')' )

                            for asignaturanivelacion in AsignaturaNivelacionCarrera.objects.filter(carrera=carrera):
                                m = Materia(asignatura=asignaturanivelacion.asignatura,
                                        nivel=nivel,
                                        horas=0,
                                        creditos=0,
                                        rectora=False,
                                        identificacion='',
                                        inicio=nivel.inicio,
                                        fin=nivel.fin)
                                m.save()
                            return HttpResponseRedirect("/niveles?action=materias&id="+str(nivel.id))
                        else:
                            return HttpResponseRedirect("/niveles?action=add&carrera="+ str(carrera.id) +"&sede="+ str(sede.id) +"&periodo="+str(periodo.id)+"&error=Ya ingreso este PARALELO")
                else:
                    f = NivelForm(request.POST)
                    if f.is_valid():
                        if not  Nivel.objects.filter(carrera = f.cleaned_data['carrera'],periodo = f.cleaned_data['periodo'],sede = f.cleaned_data['sede'],sesion = f.cleaned_data['sesion'] ,nivelmalla = f.cleaned_data['nivelmalla'] , malla = f.cleaned_data['malla'] ,grupo = f.cleaned_data['grupo']).exists():
                            f.save()
                            nivel = f.instance
                            nivel.actualizar_materias()
                            nivel.crea_cronograma_pagos()

                            #OCU 26-07-2018 mail de creacion de nivel
                            nivel.mail_creacionnivel(request.user)

                            #Obtain client ip address
                            client_address = ip_client_address(request)

                            # Log de ADICIONAR NIVEL
                            LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(nivel).pk,
                                object_id       = nivel.id,
                                object_repr     = force_str(nivel),
                                action_flag     = ADDITION,
                                change_message  = 'Adicionado Nivel (' + client_address + ')' )

                            return HttpResponseRedirect("/niveles?action=materias&id="+str(nivel.id))
                        else:
                            return HttpResponseRedirect("/niveles?action=add&carrera="+ str(f.cleaned_data['carrera'].id) +"&sede="+ str(f.cleaned_data['sede'].id) +"&periodo="+str(periodo.id)+"&error=Ya ingreso este PARALELO")
                    else:
                        return HttpResponseRedirect("/niveles?action=add&error=1")

            elif action=='fechamatriculaextra':
                fechaex = convert_fecha(request.POST['fechaordinaria']) + timedelta(30)
                return HttpResponse(json.dumps({"result":"ok", "fechamatriculaex": fechaex.strftime("%d-%m-%Y")}),content_type="application/json")


            elif action == 'correomasivo':
                try:
                    matriculas = Matricula.objects.filter(nivel__id=request.POST['nivel'])
                    result = {}
                    result['result'] ="ok"
                    result['totales']="0"
                    result['turno']  ="0"
                    lista = []
                    cont = 0
                    usuario = request.user
                    user=Persona.objects.get(usuario=usuario)
                    mat = None
                    for matricula in matriculas:
                        mat = matricula.inscripcion.id
                        if matricula.inscripcion.persona.emailinst:
                            if cont == 0:
                                cont=1
                                lista.append([matricula.inscripcion.persona.emailinst])
                                if matricula.inscripcion.persona.email and lista:
                                    lista[0][0]=str(lista[0][0])+','+str(matricula.inscripcion.persona.email)
                                else:
                                    lista.append([matricula.inscripcion.persona.email])

                            else:
                                lista[0][0]=str(lista[0][0])+','+str(matricula.inscripcion.persona.emailinst)
                                if matricula.inscripcion.persona.email:
                                    lista[0][0]=str(lista[0][0])+','+str(matricula.inscripcion.persona.email)

                    if user.emailinst and lista:
                        lista[0][0]=str(lista[0][0])+','+str(user.emailinst)
                    if user.email and lista:
                        lista[0][0]=str(lista[0][0])+','+str(user.email)

                    if EMAIL_ACTIVE:
                        # lista.append([])
                        mail_correoprofe(request.POST['contenido'],request.POST['asunto'],str(lista[0][0]),request.user)
                    return HttpResponse(json.dumps(result),content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({"result":"bad","error":str(e)+" "+str(mat)}),content_type="application/json")

            elif action=='addrubro':
                f = AdicionarOtroRubroForm(request.POST)
                nivel = Nivel.objects.get(pk=request.POST['nivel'])
                if f.is_valid():
                    for matriculado in nivel.matriculados():
                        tipootro = f.cleaned_data['tipo']
                        inscripcion = matriculado.inscripcion
                        descripcion = f.cleaned_data['descripcion']

                        if not RubroOtro.objects.filter(rubro__inscripcion=inscripcion,tipo=tipootro,descripcion=descripcion).exists():
                            fecha = f.cleaned_data['fecha']
                            rubro = Rubro(fecha=datetime.today(), valor=f.cleaned_data['valor'],
                                inscripcion=inscripcion, cancelado=False, fechavence=fecha)
                            rubro.save()
                            rubrootro = RubroOtro(rubro=rubro, tipo=tipootro, descripcion=descripcion)
                            rubrootro.save()
                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de ADICIONAR PAGOS NIVEL
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(nivel).pk,
                        object_id       = nivel.id,
                        object_repr     = force_str(nivel),
                        action_flag     = ADDITION,
                        change_message  = 'Adicionado Otro rubro GR '+ descripcion +'(' + client_address + ')' )
                    return HttpResponseRedirect('/niveles?action=materias&id='+str(nivel.id))
                else:
                    return HttpResponseRedirect('/niveles?action=addrubro&nivel='+str(nivel.id)+"&error=1")

            elif action=='delrubro':
                nivel = Nivel.objects.get(pk=request.POST['nivel'])
                f = AdicionarOtroRubroForm(request.POST)
                if f.is_valid():
                    tipootro = f.cleaned_data['tipo']
                    descripcion = f.cleaned_data['descripcion'].lstrip().strip()

                    for matriculado in nivel.matriculados():
                        if RubroOtro.objects.filter(rubro__inscripcion=matriculado.inscripcion,tipo=tipootro,descripcion=descripcion).exists():
                            rubrootro = RubroOtro.objects.filter(rubro__inscripcion=matriculado.inscripcion,tipo=tipootro,descripcion=descripcion)[:1].get()
                            if rubrootro.rubro.puede_eliminarse():
                                rubrootro.rubro.delete()

                    return HttpResponseRedirect('/niveles?action=materias&id='+str(nivel.id))
                else:
                    return HttpResponseRedirect('/niveles?action=delrubro&id='+str(nivel.id)+"&error=2")

            elif action=='recargarrubro':
                nivel = Nivel.objects.get(pk=request.POST['nivel'])
                f = AdicionarOtroRubroForm(request.POST)
                if f.is_valid():
                    tipootro = f.cleaned_data['tipo']
                    descripcion = f.cleaned_data['descripcion'].lstrip().strip()
                    numerorecargo = f.cleaned_data['numerorecargo']

                    desc_recargo = descripcion + " Recargo:" + str(numerorecargo) # formando la descripcio con el año + el numero consecutivo de recargo
                    for matriculado in nivel.matriculados():
                        if RubroOtro.objects.filter(rubro__inscripcion=matriculado.inscripcion,tipo=tipootro,descripcion=descripcion).exists():
                            rubrootro = RubroOtro.objects.filter(rubro__inscripcion=matriculado.inscripcion,tipo=tipootro,descripcion=descripcion)[:1].get()
                            if not rubrootro.rubro.cancelado:
                                fecha = f.cleaned_data['fecha']
                                #Se crea un nuevo Rubro para los Recargos con el nuevo valor y la fecha de vencimiento q hayan pasado en el formulario
                                rubro = Rubro(fecha=datetime.today(), valor=f.cleaned_data['valor'],
                                                inscripcion=matriculado.inscripcion, cancelado=False, fechavence=fecha)
                                rubro.save()
                                #Se crea un nuevo Rubro OTRO para el Recargo con la descripcion formada por el año + el numero de recargo, ya q pueden ser varios recargos
                                rubrootro = RubroOtro(rubro=rubro, tipo=tipootro, descripcion=desc_recargo)
                                rubrootro.save()

                    return HttpResponseRedirect('/niveles?action=materias&id='+str(nivel.id))
                else:
                    return HttpResponseRedirect('/niveles?action=recargarrubro&id='+str(nivel.id)+"&error=2")

            elif action=='addlibre':
                f = NivelLibreForm(request.POST)
                if f.is_valid():
                    coordinacion = Coordinacion.objects.get(pk=request.POST['coordinacion'])
                    periodo = Periodo.objects.get(pk=request.POST['periodo'])

                    nivel = Nivel(carrera=None,periodo=periodo,
                        sede=None,
                        sesion=f.cleaned_data['sesion'],
                        nivelmalla=None,
                        malla=None,
                        grupo=None,
                        inicio=f.cleaned_data['inicio'],
                        fin=f.cleaned_data['fin'],
                        paralelo=f.cleaned_data['paralelo'],
                        cerrado=False,
                        fechacierre=None,
                        fechatopematricula=f.cleaned_data['fechatopematricula'])
                    nivel.save()

                    nc = NivelLibreCoordinacion(nivel=nivel, coordinacion=coordinacion)
                    nc.save()
                    nivel.crea_cronograma_pagos()

                    return HttpResponseRedirect("/niveles?action=materias&id="+str(nivel.id))
                else:
                    return HttpResponseRedirect("/niveles?action=add&error=1")

            elif action=='addpagos':
                nivel = Nivel.objects.get(pk=request.POST['id'])
                f = PagoNivelForm(request.POST)
                if f.is_valid():
                    pagonivel = PagoNivel(nivel=nivel, tipo=f.cleaned_data['tipo'],fecha=f.cleaned_data['fecha'],valor=f.cleaned_data['valor'])
                    pagonivel.save()

                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de ADICIONAR PAGOS NIVEL
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(pagonivel.nivel).pk,
                        object_id       = pagonivel.id,
                        object_repr     = force_str(pagonivel),
                        action_flag     = ADDITION,
                        change_message  = 'Adicionado Pago Nivel (' + client_address + ')' )

                    mail_correoaddplanpago("PAGO AGREGADO","PAGO AGREGADO "+str(TIPOS_PAGO_NIVEL[int(pagonivel.tipo)][1]),request.user,pagonivel,str("PAGO AGREGADO"),str(TIPOS_PAGO_NIVEL[int(pagonivel.tipo)][1]))

                    return HttpResponseRedirect("/niveles?action=pagos&id="+str(nivel.id))
                else:
                    return HttpResponseRedirect("/niveles?action=addpagos&id="+str(nivel.id))

            elif action=='editpagos':
                pagonivel = PagoNivel.objects.get(pk=request.POST['id'])
                nivel = pagonivel.nivel
                f = PagoNivelEditForm(request.POST)
                if f.is_valid():
                    fecha = pagonivel.fecha
                    valor = pagonivel.valor
                    pagonivel.fecha=f.cleaned_data['fecha']
                    pagonivel.valor=f.cleaned_data['valor']
                    pagonivel.save()

                    # guardarLogPagonivel
                    pagonivellog= PagoNivelLog(pagonivel=pagonivel,nivel=nivel,fecha=datetime.now(),motivo=f.cleaned_data['observacion'],usuario = request.user,valor= pagonivel.valor)
                    pagonivellog.save()
                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de EDITAR PAGOS NIVEL
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(pagonivel.nivel).pk,
                        object_id       = pagonivel.id,
                        object_repr     = force_str(pagonivel),
                        action_flag     = CHANGE,
                        change_message  = 'Modificado Cronograma Pago Nivel [ fecha: '+str(fecha)+ ' => '+ str(pagonivel.fecha)+ ' ] [ valor: ' + str(valor) + '  => ' + str(pagonivel.valor) + str(TIPOS_PAGO_NIVEL[pagonivel.tipo]) + ' ] (' +client_address + ')' )

                    # Buscar rubros con este pago y actualizarles la fecha
                    if pagonivel.tipo==0:
                        for r in RubroMatricula.objects.filter(matricula__nivel=nivel):
                            r.rubro.fechavence = f.cleaned_data['fecha']
                            # if not r.rubro.inscripcion.promocion:
                            if not r.matricula.becado:
                                if not DetalleDescuento.objects.filter(rubro=r.rubro).exists():
                                    if f.cleaned_data['modificarvalorcuota']== True:
                                        if r.rubro.puede_eliminarse():
                                            r.rubro.valor = f.cleaned_data['valor']
                            r.rubro.save()
                            #guardar log de rubro
                            rubrolog = RubroLog(rubro=r.rubro,motivo=f.cleaned_data['observacion'],fecha = datetime.now(),
                                                               usuario = request.user)
                            rubrolog.save()

                    else:
                        for r in RubroCuota.objects.filter(matricula__nivel=nivel, cuota=pagonivel.tipo):
                            r.rubro.fechavence = f.cleaned_data['fecha']
                            # if not r.rubro.inscripcion.promocion:
                            if r.rubro.inscripcion.matricula():
                                if not r.rubro.inscripcion.matricula().becado:
                                    if not DetalleDescuento.objects.filter(rubro=r.rubro).exists():
                                        if f.cleaned_data['modificarvalorcuota']== True:
                                            if r.rubro.puede_eliminarse():
                                                    r.rubro.valor = f.cleaned_data['valor']
                            r.rubro.save()
                            #guardar log de rubro
                            rubrolog = RubroLog(rubro=r.rubro,motivo=f.cleaned_data['observacion'],fecha = datetime.now(),
                                                               usuario = request.user)
                            rubrolog.save()

                        matriculados=None
                        #OCastillo 26-04-2023 que se puedan editar los rubros adicionales cargados en el nivel
                        # if pagonivel.tipo ==TIPO_PAGOS_EXAMEN_DE_ADMISION or pagonivel.tipo ==TIPO_PAGOS_CURSO_DE_NIVELACION:
                        matriculados = nivel.matricula_set.all()
                       # if  pagonivel.tipo ==TIPO_PAGOS_EXAMEN_DE_ADMISION:
                        for matricula in matriculados:
                           for ruotro in Rubro.objects.filter(inscripcion=matricula.inscripcion,tiponivelpago=pagonivel.tipo):
                           # for ruotro in Rubro.objects.filter(inscripcion=matricula.inscripcion,tiponivelpago=TIPO_PAGOS_EXAMEN_DE_ADMISION):
                                #OCastillo 09-04-2021 poder modificar fecha de tipo de rubro TIPO_PAGOS_EXAMEN_DE_ADMISION
                                ruotro.fechavence = f.cleaned_data['fecha']
                                # if not ruotro.inscripcion.promocion:
                                if ruotro.inscripcion.matricula():
                                    if not ruotro.inscripcion.matricula().becado:
                                        if not DetalleDescuento.objects.filter(rubro=ruotro).exists():
                                            if f.cleaned_data['modificarvalorcuota']== True:
                                                if ruotro.puede_eliminarse():
                                                    ruotro.valor = f.cleaned_data['valor']
                                ruotro.save()
                                #guardar log de rubro
                                rubrolog = RubroLog(rubro=ruotro,motivo=f.cleaned_data['observacion'],fecha = datetime.now(),usuario = request.user)
                                rubrolog.save()
                           # else:
                           #     for matricula in matriculados:
                           #         for ruotro in Rubro.objects.filter(inscripcion=matricula.inscripcion,tiponivelpago=TIPO_PAGOS_CURSO_DE_NIVELACION):
                           #              #OCastillo 09-04-2021 poder modificar fecha de tipo de rubro TIPO_PAGOS_CURSO_DE_NIVELACION
                           #              ruotro.fechavence = f.cleaned_data['fecha']
                           #              # if not ruotro.inscripcion.promocion:
                           #              if ruotro.inscripcion.matricula():
                           #                  if not ruotro.inscripcion.matricula().becado:
                           #                      if not DetalleDescuento.objects.filter(rubro=ruotro).exists():
                           #                          if f.cleaned_data['modificarvalorcuota']== True:
                           #                              if ruotro.puede_eliminarse():
                           #                                  ruotro.valor = f.cleaned_data['valor']
                           #              ruotro.save()
                           #              #guardar log de rubro
                           #              rubrolog = RubroLog(rubro=ruotro,motivo=f.cleaned_data['observacion'],fecha = datetime.now(),usuario = request.user)
                           #              rubrolog.save()
                    # mail= str('floresvillamarinm@gmail.com')+','+ str('floresvillamarinm@gmail.com')+','+ str('floresvillamarinm@gmail.com') +','+ str('floresvillamarinm@gmail.com')
                    mail_correocambioplanpago("EDICION DE PAGO","EDICION PLAN DE PAGO "+str(TIPOS_PAGO_NIVEL[pagonivel.tipo][1]),request.user,pagonivel,f.cleaned_data['observacion'] )

                    return HttpResponseRedirect("/niveles?action=pagos&id="+str(nivel.id))
                else:
                    return HttpResponseRedirect("/niveles?action=addpagos&id="+str(nivel.id))

            elif action=='edit':
                f = NivelFormEdit(request.POST, instance=Nivel.objects.get(pk=request.POST['id']))
                if f.is_valid():
                    f.save()
                    #Obtain client ip address
                    client_address = ip_client_address(request)
                    nivel =    Nivel.objects.get(pk=request.POST['id'])
                    # Log de ADICIONADO CRONOGRAMA DE PAGOS
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(nivel).pk,
                        object_id       = nivel.id,
                        object_repr     = force_str(nivel),
                        action_flag     = ADDITION,
                        change_message  = 'Editado Nivel (' + client_address  + ')')
                    return HttpResponseRedirect("/niveles")
                else:
                    return HttpResponseRedirect("/niveles?action=edit&id="+request.POST['id'])
            elif action=='editlibre':
                f = NivelLibreForm(request.POST)
                if f.is_valid():
                    nivel = Nivel.objects.get(pk=request.POST['id'])
                    nivel.paralelo = f.cleaned_data['paralelo']
                    nivel.sesion = f.cleaned_data['sesion']
                    nivel.inicio = f.cleaned_data['inicio']
                    nivel.fin = f.cleaned_data['fin']
                    nivel.fechatopematricula = f.cleaned_data['fechatopematricula']
                    nivel.save()

                    return HttpResponseRedirect("/niveles")
                else:
                    return HttpResponseRedirect("/niveles?action=editlibre&id="+request.POST['id'])

            elif action=='delete':
                m = Nivel.objects.get(pk=request.POST['id'])
                m.delete()
                return HttpResponseRedirect('/niveles')

            elif action=='editmateria':
                f = MateriaForm(request.POST, instance=Materia.objects.get(pk=request.POST['id']))
                if f.is_valid():
                    materia = Materia.objects.get(pk=request.POST['id'])
                    if Materia.objects.filter(nivel=materia.nivel,asignatura=f.cleaned_data['asignatura']).exclude(asignatura=materia.asignatura,id =materia.id).exists():
                        return HttpResponseRedirect('/niveles?action=editmateria&error=Esta materia ya existe&id='+str(materia.id))
                    f.save()
                    return HttpResponseRedirect('/niveles?action=materias&id='+str(f.instance.nivel.id))
                else:
                    return HttpResponseRedirect("/niveles?action=editmateria&id="+request.POST['id']+"&error=1")

            elif action=='addmateria':
                nivel = Nivel.objects.get(pk=request.POST['idnivel'])
                grupo=''
                if CENTRO_EXTERNO:
                    f = MateriaCursoBuckForm(request.POST)
                    # f = MateriaFormCext(request.POST, instance=Materia(nivel=nivel))
                else:
                    f = MateriaForm(request.POST, instance=Materia(nivel=nivel))
                    f.for_modelo_evaluativo(nivel.sede)
                if f.is_valid():
                    asignatura = Asignatura.objects.filter(pk=f.cleaned_data['asignatura'].id)[:1].get()
                    if not CENTRO_EXTERNO:
                        if f.cleaned_data['asignatura'].id == ASIG_VINCULACION:
                            return HttpResponseRedirect('/niveles?action=addmateria&error=No se puede agregar esta materia&id='+str(nivel.id))
                        if Materia.objects.filter(nivel=nivel,asignatura=f.cleaned_data['asignatura']).exists():
                            return HttpResponseRedirect('/niveles?action=addmateria&error=Esta materia ya existe&id='+str(nivel.id))
                        f.save()
                        if not VALIDA_MATERIA_APROBADA:
                            f.instance.aprobada=True
                            f.instance.save()

                    else:
                        try:
                            from ext.models import MateriaExterna
                            grupo = f.cleaned_data['grupo']
                            if f.cleaned_data['sgaonline']:
                                sgaonline = True
                            else:
                                sgaonline = False
                            materia = Materia(asignatura=f.cleaned_data['asignatura'],
                                              nivel_id=1,
                                              horas=f.cleaned_data['horas'],
                                              creditos=0,
                                              rectora=False,
                                              cerrado=False,
                                              aprobada=False,
                                              sgaonline=sgaonline,
                                              inicio=f.cleaned_data['inicio'],
                                              fin=f.cleaned_data['fin'],
                                              numper = f.cleaned_data['numper'],
                                              convalida = f.cleaned_data['convalida'],
                                              grupo=grupo.upper(),
                                              modelo_evaluativo=f.cleaned_data['modelo_evaluativo'])
                            materia.save()

                            pmateria = ProfesorMateria(segmento_id=1,
                                                   materia=materia,
                                                   profesor=f.cleaned_data['instructor'],
                                                   desde=f.cleaned_data['inicio'],
                                                   hasta=f.cleaned_data['fin'])
                            pmateria.save()


                            matexterna= MateriaExterna(entidad_id = 1,
                                                       materia = materia,
                                                       materiaexterna = 1,
                                                       codigo = grupo.upper(),
                                                       exportada = False,
                                                       cantexport = 20)
                            matexterna.save()


                        except Exception as ex:
                            return HttpResponseRedirect("/?info=Error al Grabar " + str(ex))

                    mensaje = 'Adicionada Materia ('+ elimina_tildes(asignatura)
                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de ADICIONAR MATERIA
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(nivel).pk,
                        object_id       = nivel.id,
                        object_repr     = force_str(nivel),
                        action_flag     = ADDITION,
                        change_message  = mensaje + client_address + ')' )
                    if not CENTRO_EXTERNO:
                        return HttpResponseRedirect('/niveles?action=materias&id='+str(f.instance.nivel.id))
                    else:
                        return HttpResponseRedirect("/niveles?action=buscar&par="+str(materia.grupo))
                else:
                    return HttpResponseRedirect('/niveles')

            elif action=='asignaragrupo':
                materia = Materia.objects.get(pk=request.POST['id'])
                f = AsignarMateriaGrupoForm(request.POST)
                if f.is_valid():
                    nivel = f.cleaned_data['nivel']
                    matriculados = nivel.matricula_set.all()
                    for matricula in matriculados:
                        asignatura = materia.asignatura
                        #OCastillo 16-01-2023 se agrego validacion para que al unir grupos no se repita asignacion de materias
                        if not matricula.inscripcion.ya_aprobada(asignatura) and not matricula.materiaasignada_existe(materia):
                            # Si no la tiene aprobada aun
                            if VALIDA_PRECEDENCIA:
                                if matricula.inscripcion.carrera.online:
                                    asistenciaparaaprobar = 0
                                else:
                                    asistenciaparaaprobar = ASIST_PARA_APROBAR
                                if matricula.inscripcion.recordacademico_set.filter(asignatura__in=asignatura.precedencia.all().values('id'),nota__gte=NOTA_PARA_APROBAR,asistencia__gte=asistenciaparaaprobar).exists() or not asignatura.precedencia.all():
                                # if pendientes.count()==0:
                                    asign = MateriaAsignada(matricula=matricula,materia=materia,notafinal=0,asistenciafinal=0,supletorio=0)
                                    asign.save()

                                    # Correccion de Lecciones ya impartidas
                                    leccionesYaDadas = Leccion.objects.filter(clase__materia=asign.materia)
                                    for leccion in leccionesYaDadas:
                                        asistenciaLeccion = AsistenciaLeccion(leccion=leccion,matricula=matricula,asistio=False)
                                        asistenciaLeccion.save()
                            else:
                                pendientes = matricula.inscripcion.recordacademico_set.filter(asignatura__in=asignatura.precedencia.all(),aprobada=False)
                                if not pendientes.count():
                                    if not matricula.materiaasignada_set.filter(materia=materia).exists():
                                        asign = MateriaAsignada(matricula=matricula,materia=materia,notafinal=0,asistenciafinal=0,supletorio=0)
                                        asign.save()

                                        # Correccion de Lecciones ya impartidas
                                        leccionesYaDadas = Leccion.objects.filter(clase__materia=asign.materia)
                                        for leccion in leccionesYaDadas:
                                            asistenciaLeccion = AsistenciaLeccion(leccion=leccion,matricula=matricula,asistio=False)
                                            asistenciaLeccion.save()
                        #Obtain client ip address
                    client_address = ip_client_address(request)
                    materianivel = MateriaNivel(materia=materia,
                                                nivel=nivel,
                                                fecha =datetime.now())
                    materianivel.save()
                    # Log de ADICIONAR MATERIA A GRUPO
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(materia).pk,
                        object_id       = materia.id,
                        object_repr     = force_str(materia),
                        action_flag     = ADDITION,
                        change_message  = 'Asignada Materia a Grupo (' + nivel.paralelo + ' - ' + nivel.nivelmalla.nombre +' - ' + client_address + ')')


                    return HttpResponseRedirect('/niveles?action=materias&id='+str(materia.nivel.id))
                else:
                    return HttpResponseRedirect('/niveles?action=asignaragrupo&id='+str(materia.id))


            elif action=='deletemateria':
                m = Materia.objects.get(pk=request.POST['id'])
                nivelid = m.nivel_id
                m.delete()
                return HttpResponseRedirect('/niveles?action=materias&id='+str(nivelid))
            elif action=='deleteclases':
                m = Materia.objects.get(pk=request.POST['id'])
                nivelid = m.nivel_id
                clases = Clase.objects.filter(materia=m)
                clases.delete()
                return HttpResponseRedirect('/niveles?action=materias&id='+str(nivelid))

            elif action=='addprofesor':
                mensaje=''
                mensaje2=''
                mensaje3=''
                persona = Persona.objects.get(usuario=request.user)
                m = Materia.objects.get(pk=request.POST['mid'])
                f = ProfesorMateriaFormAdd(request.POST)

                if f.is_valid():
                    #OCastillo 16-01-2020 validacion
                    if not  f.cleaned_data['profesor_aux']:
                        if ProfesorMateria.objects.filter(profesor=f.cleaned_data['profesor'].id,aceptacion=True).exists():
                            docentemateria= ProfesorMateria.objects.filter(profesor=f.cleaned_data['profesor'].id,aceptacion=True)[:1].get()
                            if ProfesorMateria.objects.filter(desde=f.cleaned_data['desde'],hasta=f.cleaned_data['hasta'],profesor=docentemateria.profesor,aceptacion=True).exists():
                                matdoc=ProfesorMateria.objects.filter(desde=f.cleaned_data['desde'],hasta=f.cleaned_data['hasta'],profesor=docentemateria.profesor,aceptacion=True)[:1].get()
                                mensaje2='PROFESOR TIENE ASIGNADA OTRA MATERIA EN EL MISMO RANGO DE FECHAS ' + elimina_tildes(matdoc.materia.nombre_completo())
                    else:
                        if ProfesorMateria.objects.filter(profesor_aux=f.cleaned_data['profesor_aux'].id,aceptacion=True).exists():
                            docentemateria= ProfesorMateria.objects.filter(profesor_aux=f.cleaned_data['profesor_aux'].id,aceptacion=True)[:1].get()
                            if ProfesorMateria.objects.filter(desde=f.cleaned_data['desde'],hasta=f.cleaned_data['hasta'],profesor_aux=docentemateria.profesor_aux,aceptacion=True).exists():
                                matdoc=ProfesorMateria.objects.filter(desde=f.cleaned_data['desde'],hasta=f.cleaned_data['hasta'],profesor_aux=docentemateria.profesor_aux,aceptacion=True)[:1].get()
                                mensaje2='PROFESOR TIENE ASIGNADA OTRA MATERIA EN EL MISMO RANGO DE FECHAS ' + elimina_tildes(matdoc.materia.nombre_completo())

                    #OCastillo 05/08/2022 validar fechas de asignacion materias
                    #OCastillo 21/11/2022 se quita validacion anterior
                    # if ProfesorMateria.objects.filter(Q(desde__gte=f.cleaned_data['desde'], desde__lte=f.cleaned_data['hasta'],materia=m)|Q(hasta__gte=f.cleaned_data['desde'],hasta__lte=f.cleaned_data['hasta'],materia=m)|Q(desde__lte=f.cleaned_data['hasta'], hasta__gte=f.cleaned_data['desde']),materia=m).exists():
                    #     matdoc=ProfesorMateria.objects.filter(materia=m)[:1].get()
                    #     mensaje3='YA HAY PROFESOR ASIGNADO EN ESE RANGO DE FECHAS ' + elimina_tildes(matdoc.materia.nombre_completo())
                    #     return HttpResponseRedirect("/niveles?action=materias&id="+str(m.nivel.id)+"&msj="+mensaje3)
                    pm = ProfesorMateria(segmento=f.cleaned_data['segmento'],
                                                materia=m,
                                                profesor=f.cleaned_data['profesor'],
                                                desde=f.cleaned_data['desde'],
                                                hasta=f.cleaned_data['hasta'])
                    pm.save()
                    #OCastillo 12-09-2023 esta programacion ya no va se asigna 10 para el pago de materias segmento practica
                    # if 'valor' in request.POST:
                    #     if request.POST['valor'] !='' and  int(request.POST['valor'])>0:
                    #         pm.valorporhora=True
                    #         pm.valor=request.POST['valor']
                    #         pm.save()
                    #
                    #         if RegistroValorporDocente.objects.filter(profesor=pm.profesor,segmento=pm.segmento,activo=True).exists():
                    #             reg=RegistroValorporDocente.objects.filter(profesor=pm.profesor,segmento=pm.segmento,activo=True)[:1].get()
                    #         f2 = ValorporMateriaForm(request.POST)
                    #         if f2.is_valid():
                    #             pm.valorporhora=True
                    #             pm.valor=f2.cleaned_data['valor']
                    #             pm.save()
                    #             if reg!=None:
                    #                 if pm.valor!=reg.valor:
                    #                     reg.activo=False
                    #                     reg.fecha=datetime.now()
                    #                     reg.usuario=request.user
                    #                     reg.save()
                    #
                    #                     registro=RegistroValorporDocente(profesor=pm.profesor,segmento=pm.segmento,
                    #                                                      materia=pm.materia,valor=f2.cleaned_data['valor'],
                    #                                                      fecha=datetime.now(),usuario=request.user)
                    #                     registro.save()
                    #             else:
                    #                 registro=RegistroValorporDocente(profesor=pm.profesor,segmento=pm.segmento,
                    #                                                  materia=pm.materia,valor=f2.cleaned_data['valor'],
                    #                                                  fecha=datetime.now(),usuario=request.user)
                    #                 registro.save()
                    #
                    #     else:
                    #         pm.valorporhora=False
                    #         pm.valor=0
                    #         pm.save()

                    profesor = pm.profesor
                    if m.inicio < date(m.inicio.year,m.inicio.month,22):
                        dia2 = datetime(m.inicio.year,m.inicio.month,22)- timedelta(days=30)
                        inicio = datetime(dia2.year,dia2.month,22)
                        fin = datetime(m.inicio.year,m.inicio.month,21)
                    else:
                        dia2 = date(m.inicio.year,m.inicio.month,22) + timedelta(days=30)
                        inicio =datetime(m.inicio.year,m.inicio.month,22)
                        fin = datetime(dia2.year,dia2.month,21)
                    if f.cleaned_data['profesor_aux']:
                        pm.profesor_aux=f.cleaned_data['profesor_aux'].id
                        pm.save()
                        profesor = Profesor.objects.get(pk=pm.profesor_aux)
                    else:
                        pm.profesor_aux=None
                        pm.save()

                    if EMAIL_ACTIVE:
                        client_address = ip_client_address(request)
                        if f.cleaned_data['enviar']:
                            pm.fechacorreo=datetime.now().date()
                            pm.save()
                            #pm.mail_materiaasignada(str('floresvillamarinm@gmail.com') + ','+ str('floresvillamarinm@gmail.com')+','+str('floresvillamarinm@gmail.com')+','+str('floresvillamarinm@gmail.com')+','+str('soporteitb@bolivariano.edu.ec'),request.user)
                            pm.mail_materiaasignada(str(profesor.persona.email) + ','+ str(profesor.persona.emailinst)+','+str(persona.email)+','+str(persona.emailinst)+','+str('soporteitb@bolivariano.edu.ec'),request.user)

                        # if 'valor' in request.POST:
                        #     if pm.materia.nivel.carrera.coordinacion_pertenece().id == COORDINACION_UASSS:
                        #         correos = 'rcaicedoq@bolivariano.edu.ec,mxcajias@bolivariano.edu.ec'
                        #     elif pm.materia.nivel.carrera.coordinacion_pertenece().id == COORDINACION_UACED:
                        #         correos = 'kgutierrez@bolivariano.edu.ec, csolorzano@bolivariano.edu.ec'
                        #     else:
                        #         correos = 'michelle@bolivariano.edu.ec'
                        #     correos += ','+str(persona.emailinst)
                        #     pm.mail_valorhora_coordinacion(correos, request.user)

                     # LOG DE ADICIONAR PROFESOR
                        LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(pm).pk,
                        object_id       = pm.id,
                        object_repr     = force_str(pm),
                        action_flag     = ADDITION,
                        change_message  = 'Adicionado Profesor Materia (' + client_address + ')' )
                        if f.cleaned_data['profesor_aux']:
                            asig = ProfesorMateria.objects.filter(profesor_aux=f.cleaned_data['profesor_aux'].id,materia__cerrado=False,hasta__gte=inicio).distinct('materia__asignatura').values('materia__asignatura').count()
                        else:
                            asig = ProfesorMateria.objects.filter(profesor=f.cleaned_data['profesor'],materia__cerrado=False,hasta__gte=inicio).distinct('materia__asignatura').values('materia__asignatura').count()


                        if not((asig <= CANTIDAD_ASIGNATURAS ) or ( CANTIDAD_ASIGNATURAS == 0 ) or (f.cleaned_data['profesor'].id == DOCENTE_POR_DEFINIR)):
                            mensaje = 'Profesor: ' + str(elimina_tildes(profesor.persona.nombre_completo())) + " SUPERO EL MAXIMO DE ASIGNATURAS PERMITIDAS "  + str(asig) + " de 5"
                            return HttpResponseRedirect("/niveles?action=materias&id="+str(m.nivel.id)+"&msj="+mensaje)
                        return HttpResponseRedirect("/niveles?action=materias&id="+str(m.nivel.id)+"&msj="+mensaje2)
                    else:
                        return HttpResponseRedirect("/niveles?action=materias&id="+str(m.nivel.id))
                        # return HttpResponseRedirect("/niveles?action=addprofesor&mid="+str(m.id))
                    # else:
                    #     return HttpResponseRedirect("/niveles?action=addprofesor&mid="+str(m.id)+"&error=3")
                else:
                    return HttpResponseRedirect("/niveles?action=addprofesor&mid="+str(m.id)+"&error=1")

            elif action=='addprofesornivelcerrado':
                mensaje='Asignacion Docente Nivel Cerrado'
                desde = datetime.today().date()
                hasta=desde + timedelta(days=4)
                persona = Persona.objects.get(usuario=request.user)
                m = Materia.objects.get(pk=request.POST['mid'])
                f = ProfesorMateriaFormAdd(request.POST)
                if f.is_valid():
                    pm = ProfesorMateria(segmento=f.cleaned_data['segmento'],materia=m,
                                         profesor=f.cleaned_data['profesor'],
                                         desde=desde,hasta=hasta)
                    pm.save()
                    pm.profesor_aux=None
                    pm.save()

                    if EMAIL_ACTIVE :
                        pm.mail_materianivelcerrado(pm.profesor,str(pm.profesor.persona.email) + ','+ str(pm.profesor.persona.emailinst)+','+str(persona.email)+','+str(persona.emailinst)+','+str('secretariageneral@bolivariano.edu.ec'),request.user)
                        #pm.mail_materianivelcerrado(pm.profesor,str(pm.profesor.persona.email) + ','+ str(pm.profesor.persona.emailinst)+','+str(persona.email)+','+str(persona.emailinst),request.user)
                        client_address = ip_client_address(request)

                     # LOG DE ASIGNACION DOCENTE NIVEL CERRADO
                        LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(pm).pk,
                        object_id       = pm.id,
                        object_repr     = force_str(pm),
                        action_flag     = ADDITION,
                        change_message  = 'Adicionado Profesor en Nivel Cerrado (' + client_address + ')' )

                        return HttpResponseRedirect("/niveles?action=materias&id="+str(m.nivel.id)+"&msj="+mensaje)
                    else:
                        return HttpResponseRedirect("/niveles?action=materias&id="+str(m.nivel.id))
                else:
                    return HttpResponseRedirect("/niveles?action=addprofesor&mid="+str(m.id)+"&error=1")



            elif action=='delprofesor':
                pm = ProfesorMateria.objects.get(pk=request.POST['pmid'])
                if not pm.aceptacion:
                    # Chequear si existe un profesor secundario
        #            materia = pm.materia
        #            if materia.profesormateria_set.count()>1:
        #                # Transferir clases
        #                clases = pm.profesor.clase_set.filter(materia=materia)
        #                for c in clases:
        #                    c.profesor = materia.profesormateria_set.all()[1].profesor
        #                    c.save()
        #            else:
        #                # Borrar las clases
        #                pm.profesor.clase_set.filter(materia=materia).delete()

                    #OCastillo 05-10-2023 verificar si tiene clases dadas en el corte del rol y no dejar eliminar aquiiiiiii
                    materia = pm.materia
                    if pm.tiene_lecciones():
                        return HttpResponse(json.dumps({"result": "bad2"}),content_type="application/json")
                    client_address = ip_client_address(request)

                 # LOG DE CAMBIAR FECHA MATREIA
                    LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(pm).pk,
                    object_id       = pm.id,
                    object_repr     = force_str(pm),
                    action_flag     = DELETION,
                    change_message  = 'Eliminado Profesor Materia (' + client_address + ')' )
                    pm.delete()

                    return HttpResponse(json.dumps({"result": "ok"}),content_type="application/json")
                else:
                    return HttpResponse(json.dumps({"result": "bad"}),content_type="application/json")
            elif action=='editprofesor':
                pm = ProfesorMateria.objects.get(pk=request.POST['pmid'])
                f = ProfesorMateriaFormAdd(request.POST)
                persona = Persona.objects.get(usuario=request.user)
                mensaje2=''

                if DEFAULT_PASSWORD=='itb':
                    if not pm.aceptacion:
                        if f.is_valid():
                            #OCastillo 06-10-2023 si tiene clases no poder editar
                            if pm.profesor.id != f.cleaned_data['profesor'].id:
                                if pm.tiene_lecciones():
                                    return HttpResponseRedirect("/niveles?action=editprofesor&pmid="+str(pm.id)+"&error=3")

                            #OCastillo 06-10-2023 si tiene horario asignado no pueden editar
                            if pm.profesor.id != f.cleaned_data['profesor'].id:
                                if pm.clase_set.filter(materia=pm.materia):
                                    return HttpResponseRedirect("/niveles?action=editprofesor&pmid="+str(pm.id)+"&error=4")

                            #OCastillo 16-01-2020 validacion
                            if not  f.cleaned_data['profesor_aux']:
                                if ProfesorMateria.objects.filter(profesor=f.cleaned_data['profesor'].id,aceptacion=True).exists():
                                    docentemateria = ProfesorMateria.objects.filter(profesor=f.cleaned_data['profesor'].id,aceptacion=True)[:1].get()
                                    if ProfesorMateria.objects.filter(desde=f.cleaned_data['desde'],hasta=f.cleaned_data['hasta'],profesor=docentemateria.profesor,aceptacion=True).exists():
                                        matdoc=ProfesorMateria.objects.filter(desde=f.cleaned_data['desde'],hasta=f.cleaned_data['hasta'],profesor=docentemateria.profesor,aceptacion=True)[:1].get()
                                        mensaje2='PROFESOR TIENE ASIGNADA OTRA MATERIA EN EL MISMO RANGO DE FECHAS ' + elimina_tildes(matdoc.materia.nombre_completo())
                            else:
                                if ProfesorMateria.objects.filter(profesor_aux=f.cleaned_data['profesor_aux'].id,aceptacion=True).exists():
                                    docentemateria = ProfesorMateria.objects.filter(profesor_aux=f.cleaned_data['profesor_aux'].id,aceptacion=True)[:1].get()
                                    if ProfesorMateria.objects.filter(desde=f.cleaned_data['desde'],hasta=f.cleaned_data['hasta'],profesor_aux=docentemateria.profesor_aux,aceptacion=True).exists():
                                        matdoc=ProfesorMateria.objects.filter(desde=f.cleaned_data['desde'],hasta=f.cleaned_data['hasta'],profesor_aux=docentemateria.profesor_aux,aceptacion=True)[:1].get()
                                        mensaje2='PROFESOR TIENE ASIGNADA OTRA MATERIA EN EL MISMO RANGO DE FECHAS ' + elimina_tildes(matdoc.materia.nombre_completo())

                            #OCastillo 05/08/2022 validar fechas de asignacion materias
                            #OCastillo 21/11/2022 se quita validacion anterior
                            # if ProfesorMateria.objects.filter(desde__gte=f.cleaned_data['desde'], hasta__lte=f.cleaned_data['hasta'],materia=pm.materia,profesor=f.cleaned_data['profesor'],aceptacion=True).exists():
                            #     matdoc=ProfesorMateria.objects.filter(desde__gte=f.cleaned_data['desde'], hasta__lte=f.cleaned_data['hasta'],materia=pm.materia,profesor=f.cleaned_data['profesor'],aceptacion=True)[:1].get()
                            #     mensaje3='YA HAY PROFESOR ASIGNADO EN ESE RANGO DE FECHAS ' + elimina_tildes(matdoc.materia.nombre_completo())
                            #     return HttpResponseRedirect("/niveles?action=materias&id="+str(pm.materia.nivel.id)+"&msj="+(str(mensaje3)))

                            mensaje=''
                            pm.segmento = f.cleaned_data['segmento']
                            pm.profesor = f.cleaned_data['profesor']
                            pm.desde = f.cleaned_data['desde']
                            pm.hasta = f.cleaned_data['hasta']
                            pm.save()
                            #OCastillo 12-09-2023 esta programacion ya no se aplica
                            # if 'valor' in request.POST:
                            #     if  request.POST['valor'] !='' and  int(request.POST['valor'])>0:
                            #         pm.valorporhora=True
                            #         pm.valor=request.POST['valor']
                            #         pm.save()
                            #
                            #         if RegistroValorporDocente.objects.filter(profesor=pm.profesor,segmento=pm.segmento,activo=True).exists():
                            #             reg=RegistroValorporDocente.objects.filter(profesor=pm.profesor,segmento=pm.segmento,activo=True)[:1].get()
                            #         f2 = ValorporMateriaForm(request.POST)
                            #         if f2.is_valid():
                            #             pm.valorporhora=True
                            #             pm.valor=f2.cleaned_data['valor']
                            #             pm.save()
                            #             if reg!=None:
                            #                 if pm.valor!=reg.valor:
                            #                     reg.activo=False
                            #                     reg.fecha=datetime.now()
                            #                     reg.usuario=request.user
                            #                     reg.save()
                            #
                            #                     registro=RegistroValorporDocente(profesor=pm.profesor,segmento=pm.segmento,
                            #                                                      materia=pm.materia,valor=f2.cleaned_data['valor'],
                            #                                                      fecha=datetime.now(),usuario=request.user)
                            #                     registro.save()
                            #             else:
                            #                 registro=RegistroValorporDocente(profesor=pm.profesor,segmento=pm.segmento,
                            #                                                  materia=pm.materia,valor=f2.cleaned_data['valor'],
                            #                                                  fecha=datetime.now(),usuario=request.user)
                            #                 registro.save()
                            #
                            #     else:
                            #         pm.valorporhora=False
                            #         pm.valor=0
                            #         pm.save()

                            profesor = pm.profesor
                            if pm.materia.inicio < date(pm.materia.inicio.year,pm.materia.inicio.month,22):
                                dia2 = datetime(pm.materia.inicio.year,pm.materia.inicio.month,22)- timedelta(days=30)
                                inicio = datetime(dia2.year,dia2.month,22)
                                # fin = datetime(pm.materia.inicio.year,pm.materia.inicio.month,21)
                            else:
                                dia2 = date(pm.materia.inicio.year,pm.materia.inicio.month,22) + timedelta(days=30)
                                inicio =datetime(pm.materia.inicio.year,pm.materia.inicio.month,22)
                                # fin = datetime(dia2.year,dia2.month,21)
                            if f.cleaned_data['profesor_aux']:
                                pm.profesor_aux=f.cleaned_data['profesor_aux'].id
                                pm.save()
                                profesor = Profesor.objects.get(pk=pm.profesor_aux)
                            else:
                                pm.profesor_aux=None
                                pm.save()

                            if EMAIL_ACTIVE:
                                if f.cleaned_data['enviar']:
                                    pm.fechacorreo=datetime.now().date()
                                    pm.save()
                                    pm.mail_materiaasignada(str(profesor.persona.email) + ','+ str(profesor.persona.emailinst)+','+str(persona.email)+','+str(persona.emailinst)+','+str('soporteitb@bolivariano.edu.ec'),request.user)
                                    #pm.mail_materiaasignada(str('floresvillamarinm@gmail.com') + ','+ str('floresvillamarinm@gmail.com')+','+str('floresvillamarinm@gmail.com')+','+str('floresvillamarinm@gmail.com')+','+str('soporteitb@bolivariano.edu.ec'),request.user)
                                # if 'valor' in request.POST:
                                #     if pm.materia.nivel.carrera.coordinacion_pertenece().id == COORDINACION_UASSS:
                                        # correos = 'rcaicedoq@bolivariano.edu.ec,mxcajias@bolivariano.edu.ec'
                                    # elif pm.materia.nivel.carrera.coordinacion_pertenece().id == COORDINACION_UACED:
                                #         # correos = 'kgutierrez@bolivariano.edu.ec, csolorzano@bolivariano.edu.ec'
                                #     else:
                                #         # correos = 'michelle@bolivariano.edu.ec'
                                #     correos += ','+str(persona.emailinst)
                                #     pm.mail_valorhora_coordinacion(correos, request.user)


                            else:
                                pm.fechacorreo=None
                                pm.save()



                              #  pm.mail_materiaasignada(str(profesor.persona.email) + ','+ str(profesor.persona.emailinst)+','+str(persona.email)+','+str(persona.emailinst),request.user)
                            client_address = ip_client_address(request)

                         # LOG DE EDITAR PROFESOR
                            LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(pm).pk,
                            object_id       = pm.id,
                            object_repr     = force_str(pm),
                            action_flag     = CHANGE,
                            change_message  = 'Editado Profesor Materia (' + client_address + ')' )
                            # if f.cleaned_data['profesor_aux']:
                            if f.cleaned_data['profesor_aux']:
                                asig = ProfesorMateria.objects.filter(profesor_aux=pm.profesor_aux,materia__cerrado=False,hasta__gte=inicio).distinct('materia__asignatura').values('materia__asignatura').count()
                            else:
                                asig = ProfesorMateria.objects.filter(profesor=f.cleaned_data['profesor'],materia__cerrado=False,hasta__gte=inicio).distinct('materia__asignatura').values('materia__asignatura').count()
                            if not((asig <= CANTIDAD_ASIGNATURAS ) or ( CANTIDAD_ASIGNATURAS == 0 ) or pm.profesor.id == DOCENTE_POR_DEFINIR):
                                mensaje = 'Profesor: ' + str(elimina_tildes(profesor.persona.nombre_completo())) + "    SUPERO EL MAXIMO DE ASIGNATURAS PERMITIDAS " + str(asig) + " de 5"
                                return HttpResponseRedirect("/niveles?action=materias&id="+str(pm.materia.nivel.id)+"&msj="+mensaje+"&error=1")
                            return HttpResponseRedirect("/niveles?action=materias&id="+str(pm.materia.nivel.id)+"&msj="+(str(mensaje2)))
                            # else:
                            #     return HttpResponseRedirect("/niveles?action=editprofesor&pmid="+str(pm.id)+"&error=2")
                        else:
                            return HttpResponseRedirect("/niveles?action=editprofesor&pmid="+str(pm.id)+"&error=3")
                    else:


                        return HttpResponseRedirect("/niveles?action=editprofesor&pmid="+str(pm.id)+"&error=1")
                        # return HttpResponseRedirect('/niveles?info=NO SE PUEDE EDITAR PORQUE YA FUE ACEPTADO POR EL DOCENTE')
                else:
                    if f.is_valid():
                            #OCastillo 16-01-2020 validacion
                            if not  f.cleaned_data['profesor_aux']:
                                if ProfesorMateria.objects.filter(profesor=f.cleaned_data['profesor'].id,aceptacion=True).exists():
                                    docentemateria = ProfesorMateria.objects.filter(profesor=f.cleaned_data['profesor'].id,aceptacion=True)[:1].get()
                                    if ProfesorMateria.objects.filter(desde=f.cleaned_data['desde'],hasta=f.cleaned_data['hasta'],profesor=docentemateria.profesor,aceptacion=True).exists():
                                        matdoc=ProfesorMateria.objects.filter(desde=f.cleaned_data['desde'],hasta=f.cleaned_data['hasta'],profesor=docentemateria.profesor,aceptacion=True)[:1].get()
                                        mensaje2='PROFESOR TIENE ASIGNADA OTRA MATERIA EN EL MISMO RANGO DE FECHAS ' + elimina_tildes(matdoc.materia.nombre_completo())
                            else:
                                if ProfesorMateria.objects.filter(profesor_aux=f.cleaned_data['profesor_aux'].id,aceptacion=True).exists():
                                    docentemateria = ProfesorMateria.objects.filter(profesor_aux=f.cleaned_data['profesor_aux'].id,aceptacion=True)[:1].get()
                                    if ProfesorMateria.objects.filter(desde=f.cleaned_data['desde'],hasta=f.cleaned_data['hasta'],profesor_aux=docentemateria.profesor_aux,aceptacion=True).exists():
                                        matdoc=ProfesorMateria.objects.filter(desde=f.cleaned_data['desde'],hasta=f.cleaned_data['hasta'],profesor_aux=docentemateria.profesor_aux,aceptacion=True)[:1].get()
                                        mensaje2='PROFESOR TIENE ASIGNADA OTRA MATERIA EN EL MISMO RANGO DE FECHAS ' + elimina_tildes(matdoc.materia.nombre_completo())

                            mensaje=''
                            pm.segmento = f.cleaned_data['segmento']
                            pm.profesor = f.cleaned_data['profesor']
                            pm.desde = f.cleaned_data['desde']
                            pm.hasta = f.cleaned_data['hasta']
                            pm.save()
                            profesor = pm.profesor
                            if pm.materia.inicio < date(pm.materia.inicio.year,pm.materia.inicio.month,22):
                                dia2 = datetime(pm.materia.inicio.year,pm.materia.inicio.month,22)- timedelta(days=30)
                                inicio = datetime(dia2.year,dia2.month,22)
                                # fin = datetime(pm.materia.inicio.year,pm.materia.inicio.month,21)
                            else:
                                dia2 = date(pm.materia.inicio.year,pm.materia.inicio.month,22) + timedelta(days=30)
                                inicio =datetime(pm.materia.inicio.year,pm.materia.inicio.month,22)
                                # fin = datetime(dia2.year,dia2.month,21)

                            if f.cleaned_data['profesor_aux']:
                                pm.profesor_aux=f.cleaned_data['profesor_aux'].id
                                pm.save()
                                profesor = Profesor.objects.get(pk=pm.profesor_aux)
                            else:
                                pm.profesor_aux=None
                                pm.save()

                            if EMAIL_ACTIVE and f.cleaned_data['enviar'] :
                                pm.fechacorreo=datetime.now().date()
                                pm.save()
                                pm.mail_materiaasignada(str(profesor.persona.email) + ','+ str(profesor.persona.emailinst)+','+str(persona.email)+','+str(persona.emailinst)+','+str('soporteitb@bolivariano.edu.ec'),request.user)
                                #pm.mail_materiaasignada(str('floresvillamarinm@gmail.com') + ','+ str('floresvillamarinm@gmail.com')+','+str('floresvillamarinm@gmail.com')+','+str('floresvillamarinm@gmail.com')+','+str('soporteitb@bolivariano.edu.ec'),request.user)

                            else:
                                pm.fechacorreo=None
                                pm.save()



                              #  pm.mail_materiaasignada(str(profesor.persona.email) + ','+ str(profesor.persona.emailinst)+','+str(persona.email)+','+str(persona.emailinst),request.user)
                            client_address = ip_client_address(request)

                         # LOG DE CAMBIAR FECHA MATREIA
                            LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(pm).pk,
                            object_id       = pm.id,
                            object_repr     = force_str(pm),
                            action_flag     = CHANGE,
                            change_message  = 'Editado Profesor Materia (' + client_address + ')' )
                            if f.cleaned_data['profesor_aux']:
                                asig = ProfesorMateria.objects.filter(profesor_aux=f.cleaned_data['profesor_aux'].id,materia__cerrado=False,hasta__gte=inicio).distinct('materia__asignatura').values('materia__asignatura').count()
                            else:
                                asig = ProfesorMateria.objects.filter(profesor=f.cleaned_data['profesor'],materia__cerrado=False,hasta__gte=inicio).distinct('materia__asignatura').values('materia__asignatura').count()

                            if not((asig <= CANTIDAD_ASIGNATURAS ) or ( CANTIDAD_ASIGNATURAS == 0 ) or (f.cleaned_data['profesor'].id == DOCENTE_POR_DEFINIR)):
                                mensaje = 'Profesor: ' + str(elimina_tildes(profesor.persona.nombre_completo())) + "    SUPERO EL MAXIMO DE ASIGNATURAS PERMITIDAS " + str(asig) + " de 5"
                                return HttpResponseRedirect("/niveles?action=materias&id="+str(pm.materia.nivel.id)+"&msj="+mensaje+"&error=1")
                            return HttpResponseRedirect("/niveles?action=materias&id="+str(pm.materia.nivel.id)+"&msj="+(str(mensaje2)))
                            # else:
                            #     return HttpResponseRedirect("/niveles?action=editprofesor&pmid="+str(pm.id)+"&error=2")
                    else:
                         return HttpResponseRedirect("/niveles?action=editprofesor&pmid="+str(pm.id)+"&error=3")

            elif action == 'sendEmail':
                try:
                    print(request.POST)
                    pm = ProfesorMateria.objects.get(pk=request.POST['id'])
                    if EMAIL_ACTIVE:
                        pm.fechacorreo=datetime.now().date()
                        pm.save()
                        pm.mail_materiaasignada(str(pm.profesor.persona.email) + ','+ str(pm.profesor.persona.emailinst)+','+str(pm.profesor.persona.email)+','+str(pm.profesor.persona.emailinst)+','+str('soporteitb@bolivariano.edu.ec'), request.user)
                    return HttpResponse(json.dumps({'result':'ok'}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({'result':'bad', 'error':str(ex)}),content_type="application/json")

            elif action=='updatefecha':
                materia = Materia.objects.get(pk=request.POST['mid'])
                if request.POST['inicio'].lower()=='true' and CALCULA_FECHA_FIN_MATERIA:
                    materia.inicio = convert_fecha(request.POST['fecha'])
                    if request.POST['horas']:
                        h = request.POST['horas']
                        dias = (materia.horas / int(h)) - 1
                    else:
                        dias = 0
                    sesion = materia.nivel.sesion
                    fecha = materia.inicio
                    if dias:
                        while dias>0:
                            fecha = fecha + timedelta(1)
                            if Feriado.objects.filter(fecha=fecha).exists():
                                continue
                            weekday = fecha.weekday()+1
                            if sesion.clases_los_(weekday):
                                dias-=1
                        materia.fin = fecha


                else:
                    fechafin = convert_fecha(request.POST['fecha'])
                    if fechafin.date()>=materia.inicio:
                        materia.fin = fechafin
                    else:
                        return HttpResponse(json.dumps({'result':'bad', 'fin': materia.fin.strftime("%d-%m-%Y")}),content_type="application/json")

                materia.save()

                client_address = ip_client_address(request)

                 # LOG DE CAMBIAR FECHA MATREIA
                LogEntry.objects.log_action(
                user_id         = request.user.pk,
                content_type_id = ContentType.objects.get_for_model(materia).pk,
                object_id       = materia.id,
                object_repr     = force_str(materia),
                action_flag     = CHANGE,
                change_message  = 'Editada Fecha Materia (' + client_address + ')' )

                # Actualizar mayor fecha nivel
                nivel = materia.nivel
                maxfecha = nivel.materia_set.all().aggregate(Max('fin'))
                if maxfecha['fin__max']:
                    nivel.fin = maxfecha['fin__max']
                    nivel.save()

                # Actualizar Fechas de los Profesores
                # for pm in materia.profesormateria_set.all():
                #     # OCastillo 04-05-2022 se quita esta condicion ya que solicitan que fecha de profesor materia se actualice sin quitan la aceptacion del docente
                #     # if not pm.aceptacion:
                #     pm.desde = materia.inicio
                #     pm.hasta = materia.fin
                #     pm.save()

                return HttpResponse(json.dumps({'result':'ok','inicio': materia.inicio.strftime("%d-%m-%Y"), 'fin': materia.fin.strftime("%d-%m-%Y")}),content_type="application/json")
            elif action=='precierre':
                try:
                    nivel = Nivel.objects.get(pk=request.POST['nid'])
                    carrera= elimina_tildes(nivel.carrera.nombre)
                    materias = []
                    cantidad = 0
                    deuda_del_grupo=[]
                    deuda_total=0
                    mat=0
                    lista_estudiantes=[]
                    cont=0
                    correo = None
                    hoy = datetime.today()
                    info=''
                    html = '<br/><br/> Existen tramites pendientes por atender: <br/><br/>'
                    for materia in nivel.materia_set.all():
                        # print(materia)
                        if materia.culminacion_tit:
                             for mt in materia.nivel.matriculados():
                                mt.inscripcion.fechacuml=materia.culminacion_tit
                                mt.inscripcion.save()
                        mo = {'nombre': materia.nombre_completo(), 'id': materia.id}
                        mol = []
                        incidenciafatv = TipoIncidencia.objects.get(pk=INCIDENCIA_CIERRENIVELFATV)
                        incidenciafaces = TipoIncidencia.objects.get(pk=INCIDENCIA_CIERRENIVELFACES)
                        incidenciafass = TipoIncidencia.objects.get(pk=INCIDENCIA_CIERRENIVELFASS)
                        coordinacion =Coordinacion.objects.filter(carrera=materia.nivel.carrera)

                        if coordinacion.filter(id=COORDINACION_TRANSPORTE).exists():
                            correo = str(incidenciafatv.correo)
                        elif coordinacion.filter(id=COORDINACION_UACED).exists():
                            correo = str(incidenciafaces.correo)
                        elif coordinacion.filter(id=COORDINACION_UASSS).exists():
                            correo = str(incidenciafass.correo)


                        for asignado in materia.asignados_a_esta_materia():
                            # OCastillo 16-04-2024 esta verificacion ya no se usa por el nuevo proceso
                            # if EvaluacionAlcance.objects.filter(materiaasignada=asignado,aprobado=False,aprobadoex=False,aprobadorec=False).exclude(eliminado=True).exists():
                            #     alcance=' HAY NOTAS EN ALCANCE SIN APROBAR: '+elimina_tildes(asignado.materia.asignatura.nombre) +' ' +elimina_tildes(asignado.matricula.inscripcion.persona.nombre_completo())
                            #     return HttpResponse(json.dumps({"result": "bad", "error": str(alcance)}), content_type="application/json").
                            if asignado.obtener_rubroespecie_asentamientonotas():
                                respecie = RubroEspecieValorada.objects.filter(materia=asignado)[:1].get()
                                html = html + '<p> <b> Estudiante:</b>' + elimina_tildes(asignado.matricula.inscripcion.persona.nombre_completo_inverso()) \
                                            + '<br/> <b>Profesor: </b>' + elimina_tildes(asignado.materia.asignatura.nombre) \
                                            + '<br/> <b>Especie:  </b>' + str(respecie.serie) + '</p>'
                                lista_estudiantes.append((elimina_tildes(asignado.matricula.inscripcion.persona.nombre_completo_inverso()),
                                                          elimina_tildes(asignado.materia.asignatura.nombre),
                                                          str(respecie.serie)
                                                          ))

                            ao = {'nombre': asignado.matricula.inscripcion.persona.nombre_completo(),
                                  'id': asignado.id}
                            mol.append(ao)

                        mo['lista'] = mol
                        cantidad += len(mol)
                        materias.append(mo)
                    cont = len(lista_estudiantes)
                    if cont > 0:
                        info = 'EXISTEN ESTUDIANTES CON TRÁMITES PENDIENTES, REVISAR CORREO INFORMATIVO'  # + elimina_tildes(asignado.materia.asignatura.nombre) + ' Estudiante: ' + elimina_tildes(asignado.matricula.inscripcion.persona.nombre_completo()+ ' #Especie: ' + str(respecie.serie))
                        if EMAIL_ACTIVE:
                            send_html_mail("TRAMITES PENDIENTES PARA CERRAR EL NIVEL ",
                                           "emails/correo_tramitespendientesprecierre.html",
                                           {'contenido': "Estimado Coordinador", 'listado': lista_estudiantes, 'fecha': hoy}, correo.split(","))
                        # return HttpResponse(json.dumps({"result": "ok", "info": info}),  content_type="application/json")

                    mat=len(materias)
                    matriculados = nivel.matriculados()
                    alumnos_pasan = []
                    promedio = []
                    pasan = 0
                    correo = 0
                    abs = 0
                    abs_estudiantes = []
                    becados=0
                    estudiantes_becados = []
                    lista_becados=''
                    lista_absentos=''
                    matricula=None
                    for matricula in matriculados:
                        # print(matricula)
                        periodo = str(matricula.nivel.periodo)
                        nivelest =str(matricula.nivel.nivelmalla.nombre)
                        grupo =str(matricula.nivel.grupo.nombre)
                        matricula.inscripcion.actualiza = True
                        clave=str(random.randint(1, 9))+str(random.randint(1, 9))+str(random.randint(1, 9))+str(random.randint(1, 9))+str(random.randint(1, 9))
                        matricula.inscripcion.codigocel = clave
                        matricula.inscripcion.save()
                        if matricula.inscripcion.total_adeudado()>0:
                            deuda=matricula.inscripcion.total_adeudado()
                            deuda_del_grupo.append((elimina_tildes(matricula.inscripcion.persona.nombre_completo_inverso()),' Deuda: ' + str(deuda)))
                            deuda_total+=deuda

                        if matricula.absentismo():
                            abs_estudiantes.append(matricula.inscripcion.persona.nombre_completo())
                            lista_absentos+= elimina_tildes(matricula.inscripcion.persona.nombre_completo())+","
                        if not matricula.inscripcion.suspension and matricula.todas_materias_aprobadas_nivelactual():
                            if matricula.materias_aprobadas_nivel():
                                alumnos_pasan.append(matricula.materias_aprobadas_nivel())
                                promedio=matricula.materias_aprobadas_notas()
                                emailinst=matricula.inscripcion.persona.emailinst
                                emailpers=matricula.inscripcion.persona.email
                                estudiante=matricula.inscripcion.persona.nombre_completo()

                                # if EMAIL_ACTIVE:
                                #     usuario = request.user
                                #     nivel.mail_aprobacionnivel(usuario, promedio,estudiante,nivelest,grupo,str(emailinst) + ',' + str(emailpers))
                                #     correo = correo + 1

                                #     if correo == 5:
                                #         time.sleep(5)
                                #         correo = 0

                        if not INSCRIPCION_CONDUCCION:
                            if matricula.becado and matricula.tipobeca!=None and matricula.motivobeca!=None:
                                # OC 04-01-2019 para presentar el promedio en el correo de becados
                                    if MateriaAsignada.objects.filter(Q(matricula=matricula),Q(absentismo=None)|Q(absentismo=False)).exists():
                                        #OCastillo 16-07-2019 para el caso de estudiantes becados sin nota final
                                        materiabecados=MateriaAsignada.objects.filter(Q(matricula=matricula),Q(absentismo=None)|Q(absentismo=False))[:1].get()
                                        if materiabecados.notafinal!=None:
                                            promedio_becado=MateriaAsignada.objects.filter(Q(matricula=matricula),Q(absentismo=None)|Q(absentismo=False)).aggregate(Avg('notafinal'))
                                            promedio_becado=Decimal(promedio_becado['notafinal__avg']).quantize(Decimal(10)**-2)
                                            estudiantes_becados.append((matricula.inscripcion.persona.nombre_completo(),matricula.inscripcion.persona.telefono,matricula.inscripcion.persona.telefono_conv,matricula.tipobeca.nombre,matricula.motivobeca.nombre,matricula.cantidad_materias_aprobadas(),promedio_becado))
                                            lista_becados+= elimina_tildes(matricula.inscripcion.persona.nombre_completo())+","

                    pasan = len(alumnos_pasan)
                    abs = len(abs_estudiantes)
                    estudiantes_abs=abs_estudiantes
                    becados = len(estudiantes_becados)
                    # time.sleep(30)
                    if EMAIL_ACTIVE and DEFAULT_PASSWORD == "itb":
                        usuario = request.user
                        nivel.mail_cierrenivel(usuario, pasan,mat,periodo,abs,estudiantes_abs,carrera,deuda_del_grupo,deuda_total)
                        nivel.mail_cierrenivel_dobe(mat,periodo,becados,estudiantes_becados)

                    return HttpResponse(json.dumps({"result": "ok", "cantidad": cantidad, "materias": materias, "info":html}), content_type="application/json")

                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad", "error": str(ex)}),content_type="application/json")

            elif action=='cierrema':
                ma = MateriaAsignada.objects.get(pk=request.POST['maid'])

                if ma.materia.asignatura.asistencia and ma.notafinal >= NOTA_PARA_APROBAR:
                    asistencia = 100
                else:
                    asistencia = ma.asistenciafinal
                # Record
                b = 1
                if not ma.materia.asignatura.sin_malla:
                    if (ma.materia.asignatura.id == ASIGNATURA_PRACTICA_CONDUCCION and INSCRIPCION_CONDUCCION):
                         b=0
                    if ((ma.materia.asignatura.id == ASIG_VINCULACION  or ma.materia.asignatura.id == ASIG_PRATICA)and not INSCRIPCION_CONDUCCION) :
                        b = 0
                    if b == 1:
                    # if ((ma.materia.asignatura.id != ASIG_VINCULACION  or ma.materia.asignatura.id != ASIG_PRATICA)and not INSCRIPCION_CONDUCCION)  or (ma.materia.asignatura.id != ASIGNATURA_PRACTICA_CONDUCCION and INSCRIPCION_CONDUCCION):
                        if RecordAcademico.objects.filter(inscripcion=ma.matricula.inscripcion, asignatura=ma.materia.asignatura).exists():
                            r = RecordAcademico.objects.filter(inscripcion=ma.matricula.inscripcion, asignatura=ma.materia.asignatura)[:1].get()
                            r.nota = ma.notafinal
                            r.asistencia = asistencia
                            r.fecha = ma.matricula.nivel.fin
                            r.convalidacion = False
                            # r.aprobada = ma.esta_aprobado()
                            r.pendiente = False
                            r.save()
                            if DEFAULT_PASSWORD == 'itb':
                                r.aprobada = ma.esta_aprobado_final()
                                if ma.materia.asignatura.asistencia and ma.notafinal >= NOTA_PARA_APROBAR:
                                    r.aprobada = True
                                else:
                                    if str(ma.evaluacion().estado.nombre)=='APROBADO':
                                        r.aprobada = True
                                    else:
                                        r.aprobada = False
                            else:
                                r.aprobada = ma.esta_aprobado()
                            r.save()
                        else:
                            r = RecordAcademico(inscripcion=ma.matricula.inscripcion, asignatura=ma.materia.asignatura,
                                                nota=ma.notafinal, asistencia=asistencia,
                                                fecha=ma.matricula.nivel.fin, convalidacion=False,
                                                pendiente=False)
                            r.save()
                            if DEFAULT_PASSWORD == 'itb':
                                r.aprobada = ma.esta_aprobado_final()
                                if ma.materia.asignatura.asistencia and ma.notafinal >= NOTA_PARA_APROBAR:
                                    r.aprobada = True
                                else:
                                    if str(ma.evaluacion().estado.nombre)=='APROBADO':
                                        r.aprobada = True
                                    else:
                                        r.aprobada = False
                            else:
                                r.aprobada = ma.esta_aprobado()
                            r.save()
                        # Historico
                        if HistoricoRecordAcademico.objects.filter(inscripcion=ma.matricula.inscripcion, asignatura=ma.materia.asignatura, fecha=ma.matricula.nivel.fin).exists():
                            r = HistoricoRecordAcademico.objects.filter(inscripcion=ma.matricula.inscripcion, asignatura=ma.materia.asignatura, fecha=ma.matricula.nivel.fin)[:1].get()
                            r.nota = ma.notafinal
                            r.asistencia = asistencia
                            r.fecha = ma.matricula.nivel.fin
                            r.convalidacion = False
                            # r.aprobada = ma.esta_aprobado()
                            r.pendiente = False
                            r.save()
                            if DEFAULT_PASSWORD == 'itb':
                                r.aprobada = ma.esta_aprobado_final()
                                if ma.materia.asignatura.asistencia and ma.notafinal >= NOTA_PARA_APROBAR:
                                    r.aprobada = True
                                else:
                                    if str(ma.evaluacion().estado.nombre)=='APROBADO':
                                        r.aprobada = True
                                    else:
                                        r.aprobada = False
                            else:
                                r.aprobada = ma.esta_aprobado()
                            r.save()
                        else:
                            r = HistoricoRecordAcademico(inscripcion=ma.matricula.inscripcion, asignatura=ma.materia.asignatura,
                                                        nota=ma.notafinal, asistencia=asistencia,
                                                        fecha=ma.matricula.nivel.fin, convalidacion=False,
                                                        pendiente=False)
                            r.save()
                            if DEFAULT_PASSWORD == 'itb':
                                r.aprobada = ma.esta_aprobado_final()
                                if ma.materia.asignatura.asistencia and ma.notafinal >= NOTA_PARA_APROBAR:
                                    r.aprobada = True
                                else:
                                    if str(ma.evaluacion().estado.nombre)=='APROBADO':
                                        r.aprobada = True
                                    else:
                                        r.aprobada = False
                            else:
                                r.aprobada = ma.esta_aprobado()
                            r.save()
                        #Obtain client ip address
                        client_address = ip_client_address(request)

                        # Log de CERRAR MATERIA
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(ma.matricula).pk,
                            object_id       = ma.matricula.id,
                            object_repr     = force_str(ma.matricula),
                            action_flag     = CHANGE,
                            change_message  = 'Cerrada Materia Asignada (' + client_address + ')' )

                        # Guardar Historico Notas ITB
                        if MODELO_EVALUACION==EVALUACION_ITB:
                            if HistoricoNotasITB.objects.filter(historico=r).exists() :
                                hn = HistoricoNotasITB.objects.filter(historico=r)[:1].get()
                            else:
                                hn = HistoricoNotasITB(historico=r)
                                hn.save()

                            evaluacion = ma.evaluacion_itb()

                            hn.cod1 = evaluacion.cod1.id if evaluacion.cod1 else 3
                            hn.cod2 = evaluacion.cod2.id if evaluacion.cod2 else 5
                            hn.cod3 = evaluacion.cod3.id if evaluacion.cod3 else 10
                            hn.cod4 = evaluacion.cod4.id if evaluacion.cod4 else 11
                            hn.n1 = evaluacion.n1
                            hn.n2 = evaluacion.n2
                            hn.n3 = evaluacion.n3
                            hn.n4 = evaluacion.n4
                            hn.n5 = evaluacion.examen
                            if DEFAULT_PASSWORD == 'itb':
                                hn.total = evaluacion.nota_total_nueva()
                                hn.notafinal = evaluacion.nota_final_nueva()
                                if not ma.materia.asignatura.asistencia:
                                    hn.estado = evaluacion.estado
                                else:
                                   if ma.notafinal >= NOTA_PARA_APROBAR:
                                        hn.estado.id = NOTA_ESTADO_APROBADO
                                   else:
                                       hn.estado = evaluacion.estado
                            else:
                                hn.total = evaluacion.nota_total()
                                hn.notafinal = evaluacion.nota_final()
                            hn.recup = evaluacion.recuperacion
                            hn.save()

                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")

            elif action=='cierren':
                # Historia Niveles
                nivel = Nivel.objects.get(pk=request.POST['nid'])
                matriculas = nivel.matricula_set.all()
                n = int(nivel.nivelmalla.nombre[0]) if ('0'<=nivel.nivelmalla.nombre[0]<='9') else 0
                for matricula in matriculas:
                    if HistoriaNivelesDeInscripcion.objects.filter(inscripcion=matricula.inscripcion, nivel=n).exists():
                        h = HistoriaNivelesDeInscripcion.objects.filter(inscripcion=matricula.inscripcion, nivel=n)[:1].get()
                        h.fechaperiodo = nivel.fin
                        h.save()
                    else:
                        h = HistoriaNivelesDeInscripcion(inscripcion=matricula.inscripcion, fechaperiodo=nivel.fin,
                                                        nivel=n, observaciones='')
                        h.save()
                nivel.cerrado = True
                nivel.fechacierre = datetime.now()
                nivel.save()

                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")


            elif action == 'aprobar_materia':
                try:
                    materia = Materia.objects.get(pk=request.POST['id'])
                    mensaje = ''
                    if request.POST['op'] == 'true':
                        materia.aprobada = True
                        mensaje = 'Materia Aprobada'
                    else:
                        materia.aprobada = False
                        mensaje = 'Materia No Aprobada'
                    materia.save()
                    if EMAIL_ACTIVE:
                        if materia.aprobada :
                            materia.correo_materiaaprobada(request.user)
                        else:
                            materia.correo_materiadesaprobada(request.user)
                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de CERRAR MATERIA
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(materia).pk,
                        object_id       = materia.id,
                        object_repr     = force_str(materia),
                        action_flag     = CHANGE,
                        change_message  = mensaje +' (' + client_address + ')' )
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as e:
                    materia.aprobada=False
                    materia.save()
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
            elif action=='abrirmateria':
                materia = Materia.objects.get(pk=request.POST['id'])
                f = ObservacionAbrirMateriaForm(request.POST)
                if f.is_valid():
                    materia.cerrado = False
                    materia.fechacierre = datetime.now()
                    materia.observaciones = f.cleaned_data['observaciones']
                    materia.save()
                    if EMAIL_ACTIVE:
                        materia.correo_abrirmateria(request.user, materia.observaciones)

                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de ABRIR MATERIA
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(materia).pk,
                        object_id       = materia.id,
                        object_repr     = force_str(materia),
                        action_flag     = CHANGE,
                        change_message  = 'Abierta Materia (' + client_address + ')' )

                    return HttpResponseRedirect("/niveles?action=materias&id="+str(materia.nivel.id))

            elif action=='addrubrositb':
                #OCU 25-06-2018 Accion para crear los rubros de los nuevos grupos de importacion ITB
                materia = Materia.objects.get(pk=request.POST['id'])
                f = PagoCursoForm(request.POST)
                if f.is_valid():
                    pagoscursoitb=PagosCursoITB(materia=materia,nombre=f.cleaned_data['nombre'],fechavence=f.cleaned_data['fechavence'],valor=f.cleaned_data['valor'])
                    pagoscursoitb.save()

                    client_address = ip_client_address(request)

                    # Log de ADICIONAR Rubros a MATERIA
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(pagoscursoitb).pk,
                        object_id       = pagoscursoitb.id,
                        object_repr     = force_str(pagoscursoitb),
                        action_flag     = ADDITION,
                        change_message  = 'Adicionado Pago de Curso (' + client_address + ')' )

                    return HttpResponseRedirect("/niveles?action=buscar&par="+str(materia.grupo))

            elif action=='editrubrositb':
                pagoscursoitb = PagosCursoITB.objects.get(pk=request.POST['id'])
                materiacursoitb = pagoscursoitb.materia
                f = PagoCursoForm(request.POST)
                if f.is_valid():
                    pagoscursoitb.fechavence=f.cleaned_data['fechavence']
                    pagoscursoitb.valor=f.cleaned_data['valor']
                    pagoscursoitb.nombre=f.cleaned_data['nombre']
                    pagoscursoitb.save()

                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de EDITAR RUBROS MATERIA ITB
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(pagoscursoitb).pk,
                        object_id       = pagoscursoitb.id,
                        object_repr     = force_str(pagoscursoitb),
                        action_flag     = CHANGE,
                        change_message  = 'Modificado Rubros Materia Ingles ITB (' + client_address + ')' )

                    return HttpResponseRedirect("/niveles?action=buscar&par="+str(pagoscursoitb.materia.grupo))
                else:
                     return HttpResponseRedirect("/gruposcurso")

            elif action == 'quitarasignacionprofesor':
                try:
                    pm = ProfesorMateria.objects.get(pk=request.POST['idmaestroprofesor'])
                    pm.hasta=convertir_fecha(request.POST['fechahasta'])


                    if pm.profesor_aux:
                        profesor = Profesor.objects.get(pk=pm.profesor_aux)
                    else:
                        profesor = pm.profesor

                    if LeccionGrupo.objects.filter(profesor=profesor,materia=pm.materia,abierta=True).exists():
                        return HttpResponse(json.dumps({"result":"bad","mensaje":"Tiene clase abierta"}),content_type="application/json")


                    pm.save()

                    # eliminar los log anteriores que tiene ese profesor materia de tal formar le aparesca (aceptar y reachazar)

                    # if LogAceptacionProfesorMateria.objects.filter(profesormateria=pm).exists():
                    #
                    #     for d in LogAceptacionProfesorMateria.objects.filter(profesormateria=pm):
                    #         d.delete()

                    if pm.suspendido:
                        pm.suspendido=False
                        logaceptacion= LogAceptacionProfesorMateria(materia=pm.materia,
                                                            profesor = profesor,
                                                            fechaceptacion = datetime.now(),aceptacion=True,tipolog=4,profesormateria=pm,oberservacion=str('suspension anulada automaticamente'))

                        logquitarasignacion= LogQuitarAsignacionProfesor(materia=pm.materia,
                                                            profesor = profesor,fecha=datetime.now(),profesormateria=pm,oberservacion=request.POST['observacion'],tipolog=4,user=request.user,fechasuspension=convertir_fecha(request.POST['fechahasta']))
                    else:
                        pm.suspendido=True
                        logaceptacion= LogAceptacionProfesorMateria(materia=pm.materia,
                                                            profesor = profesor,
                                                            fechaceptacion = datetime.now(),aceptacion=True,tipolog=3,profesormateria=pm,oberservacion=str('suspension  automaticamente'))

                        logquitarasignacion= LogQuitarAsignacionProfesor(materia=pm.materia,
                                                            profesor = profesor,fecha=datetime.now(),profesormateria=pm,oberservacion=request.POST['observacion'],tipolog=3,user=request.user,fechasuspension=convertir_fecha(request.POST['fechahasta']))
                    pm.save()
                    logaceptacion.save()


                    if "file" in request.FILES:
                          logquitarasignacion.archivo = request.FILES["file"]

                    logquitarasignacion.save()


                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de quitar asignacion de materia automaticamente
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(logquitarasignacion).pk,
                        object_id       = logquitarasignacion.id,
                        object_repr     = force_str(logquitarasignacion),
                        action_flag     = ADDITION,
                        change_message  = 'ASIGNACION ELIMINADA AUTOMATICAMENTE' +' (' + client_address + ')' )


                    if Coordinacion.objects.filter(carrera=pm.materia.nivel.carrera).exists():
                         correo = Coordinacion.objects.filter(carrera=pm.materia.nivel.carrera)[:1].get().correo+','+'soporteitb@bolivariano.edu.ec'
                         #correo = 'soporteitb@bolivariano.edu.ec'
                    else:
                        correo = 'soporteitb@bolivariano.edu.ec'

                    #mail_correoeliminaasigancion('ELIMINACION DE ASIGNACION AUTOMATICA','ELIMINACION DE ASIGNACION AUTOMATICA DEL PROFESOR','floresvillamarinm@gmail.com',pm.materia,profesor,request.user,pm,logquitarasignacion.oberservacion)
                    mail_correoeliminaasigancion('SUSPENSION DE MATERIA - > SE HA SUSPENDIDO LA SIGUIENTE MATERIA','SUSPENSION DE MATERIA',correo,pm.materia,profesor,request.user,pm,logquitarasignacion.oberservacion)




                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as e:

                    return HttpResponse(json.dumps({"result":"bad","mensaje":e.message}),content_type="application/json")


            elif action == 'quitaraceptado':
                try:
                    pm = ProfesorMateria.objects.get(pk=request.POST['idmaestroprofesor'])
                    pm.aceptacion=False


                    if pm.profesor_aux:
                        profesor = Profesor.objects.get(pk=pm.profesor_aux)
                    else:
                        profesor = pm.profesor

                    if LeccionGrupo.objects.filter(profesor=profesor,materia=pm.materia,abierta=True).exists():
                        return HttpResponse(json.dumps({"result":"bad","mensaje":"Tiene clase abierta"}),content_type="application/json")


                    pm.save()


                    logaceptacion= LogAceptacionProfesorMateria(materia=pm.materia,
                                                            profesor = profesor,
                                                            fechaceptacion = datetime.now(),aceptacion=True,tipolog=2,profesormateria=pm,
                                                            oberservacion=str('Rechazo de la materia por coordinacion'),
                                                            motivo=elimina_tildes(request.POST['motivo']).upper())

                    logaceptacion.save()



                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(logaceptacion).pk,
                        object_id       = logaceptacion.id,
                        object_repr     = force_str(logaceptacion),
                        action_flag     = ADDITION,
                        change_message  = 'RECHAZO DE LA MATERIA POR COORDINACION' +' (' + client_address + ')' )



                    if Coordinacion.objects.filter(carrera=pm.materia.nivel.carrera).exists():
                         correo = Coordinacion.objects.filter(carrera=pm.materia.nivel.carrera)[:1].get().correo+','+'soporteitb@bolivariano.edu.ec'
                         #correo = 'soporteitb@bolivariano.edu.ec'
                    else:
                        correo = 'soporteitb@bolivariano.edu.ec'

                    #mail_correoeliminaasigancion('ELIMINACION DE ASIGNACION AUTOMATICA','ELIMINACION DE ASIGNACION AUTOMATICA DEL PROFESOR','floresvillamarinm@gmail.com',pm.materia,profesor,request.user,pm,logquitarasignacion.oberservacion)
                    mail_correoeliminaasigancion('ACEPTACION ELIMINADA POR COORDINACION','ACEPTACION ELIMINADA POR COORDINACION',correo,pm.materia,profesor,request.user,pm,'RECHAZO DE LA MATERIA POR COORDINACION')





                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as e:

                    return HttpResponse(json.dumps({"result":"bad","mensaje":e.message}),content_type="application/json")




            elif action=='delrubrositb':
                #OCU 26-06-2018 Accion para borrar los rubros de los nuevos grupos de importacion ITB
                pagoscursoitb = PagosCursoITB.objects.get(pk=request.POST['id'])
                grupo=pagoscursoitb.materia.grupo

                client_address = ip_client_address(request)

                # Log de ELIMINAR RUBRO DE MATERIA
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(pagoscursoitb).pk,
                    object_id       = pagoscursoitb.id,
                    object_repr     = force_str(pagoscursoitb),
                    action_flag     = DELETION,
                    change_message  = 'Eliminado Rubro de Materia ' + pagoscursoitb.materia.asignatura.nombre +' (' + client_address + ')' )

                pagoscursoitb.delete()
                return HttpResponseRedirect("/niveles?action=buscar&par="+str(grupo))

            elif action == 'correocronograma':
                try:
                    matriculas = Matricula.objects.filter(nivel__id=request.POST['nivel'])
                    nivel = Nivel.objects.get(pk=request.POST['nivel'])
                    materias = nivel.materia_set.all().order_by('inicio', 'id')
                    materiasnivel = MateriaNivel.objects.filter(nivel=nivel)

                    result = {}
                    result['result'] ="ok"
                    result['totales']="0"
                    result['turno']  ="0"
                    lista = []
                    cont = 0
                    usuario = request.user
                    user=Persona.objects.get(usuario=usuario)
                    mat = None
                    for matricula in matriculas:
                        mat = matricula.inscripcion.id
                        if matricula.inscripcion.persona.emailinst:
                            if cont == 0:
                                cont=1
                                lista.append([matricula.inscripcion.persona.emailinst])
                                if matricula.inscripcion.persona.email and lista:
                                    lista[0][0]=str(lista[0][0])+','+str(matricula.inscripcion.persona.email)
                                else:
                                    lista.append([matricula.inscripcion.persona.email])

                            else:
                                lista[0][0]=str(lista[0][0])+','+str(matricula.inscripcion.persona.emailinst)
                                if matricula.inscripcion.persona.email:
                                    lista[0][0]=str(lista[0][0])+','+str(matricula.inscripcion.persona.email)

                    if user.emailinst and lista:
                        lista[0][0]=str(lista[0][0])+','+str(user.emailinst)
                    if user.email and lista:
                        lista[0][0]=str(lista[0][0])+','+str(user.email)

                    if EMAIL_ACTIVE:
                        mail_correocronograma(request.POST['contenido'],request.POST['asunto'],str(lista[0][0]),request.user,materias,materiasnivel)
                    return HttpResponse(json.dumps(result),content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({"result":"bad","error":str(e)+" "+str(mat)}),content_type="application/json")


            elif action=='ver_historialasignacion':
                datos={'result': 'ok'}
                logquitar = LogQuitarAsignacionProfesor.objects.filter(profesormateria__id=request.POST['idprofesorhistorial'])
                datos['listahistorial']=[{'id':x.id,'materia':elimina_tildes(x.materia.asignatura.nombre),'profesor':x.profesor.persona.nombre_completo_inverso(),'fecharegistro':str(x.fecha.strftime('%Y/%m/%d %H:%M:%S')),
                                         'fechasuspencion':str(x.fechasuspension.strftime('%Y/%m/%d %H:%M:%S')) ,'usuario':x.user.username,'observacion':x.oberservacion,'archivo':str(x.archivo.url),'tipolog':'Suspendido'  if x.tipolog==3 else 'No Suspendido'} for x in LogQuitarAsignacionProfesor.objects.filter(profesormateria__id=request.POST['idprofesorhistorial'])]

                if logquitar.count()>0:

                    return HttpResponse(json.dumps(datos),
                                content_type="application/json")

                else:
                   return HttpResponse(json.dumps({'result': 'bad', 'message': str('NO TIENE HISTORIAL')}),
                                content_type="application/json")



                return HttpResponse(json.dumps({'result': 'ok'}),content_type="application/json")


            elif action =='consulta_docente':
                result = {}
                docente=''
                estado=''
                try:
                    fecha = datetime.now().date() + timedelta(days=-3)
                    #OCastillo 20-09-2021 excluye docente buck
                    profesor = ProfesorMateria.objects.filter(Q(profesor=request.POST['id'],profesor_aux=None,materia__cerrado=True,segmento__id=TIPOSEGMENTO_TEORIA,materia__fechacierre__gte='2019-05-01',materia__fechacierre__lte=fecha)|Q(profesor_aux=request.POST['id'],materia__cerrado=True,segmento__id=TIPOSEGMENTO_TEORIA,materia__fechacierre__gte='2019-05-01',materia__fechacierre__lte=fecha)).exclude(profesor__id=428).order_by('materia__asignatura__nombre')
                    for prof in profesor:
                        if prof.profesor_aux:
                            docente=Profesor.objects.get(pk=prof.profesor_aux)
                            if docente.verificaactasnotas_sinentregar():
                                estado='PENDIENTE'
                                break
                        else:
                            docente=Profesor.objects.get(pk=prof.profesor.id)
                            if docente.verificaactasnotas_sinentregar():
                                estado='PENDIENTE'
                                break

                    if estado :
                        return HttpResponse(json.dumps({"result":"ok","docente":elimina_tildes(docente.persona.nombre_completo_inverso())}),content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({"result":"no"}),content_type="application/json")
                except Exception as e:
                    result['result']  = 'bad'
                    return HttpResponse(json.dumps(result), content_type="application/json")

            elif action =='consultarvalordocente':
                #OCastillo 11-09-2023 ya no se aplica el valor asignado se asigna 10 por las materias del segmento practica desde la api
                result = {}
                try:
                    if RegistroValorporDocente.objects.filter(profesor=request.POST['id'],segmento=request.POST['idseg'],activo=True).exists():
                        registro = RegistroValorporDocente.objects.filter(profesor=request.POST['id'],segmento=request.POST['idseg'],activo=True)[:1].get()
                        docente=Profesor.objects.get(pk=registro.profesor.id)
                        valor= registro.valor
                        return HttpResponse(json.dumps({"result":"ok","docente":elimina_tildes(docente.persona.nombre_completo_inverso()),"valor":valor}),content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({"result":"no"}),content_type="application/json")
                except Exception as e:
                    result['result']  = 'bad'
                    return HttpResponse(json.dumps(result), content_type="application/json")

            elif action =='docentepracticahospital':
                result = {}
                try:
                    if Materia.objects.filter(pk=request.POST['idmat']).exists():
                        segmento = TipoSegmento.objects.filter(pk=request.POST['idseg'])[:1].get()
                        if segmento.id==TIPOSEGMENTO_TEORIA:
                            if Profesor.objects.filter(pk=request.POST['id'],activo=True,practicahospital=True).exists():
                                docente=Profesor.objects.get(pk=request.POST['id'],activo=True,practicahospital=True)
                                return HttpResponse(json.dumps({"result":"ok","docente":elimina_tildes(docente.persona.nombre_completo_inverso())}),content_type="application/json")
                        else:
                            if Profesor.objects.filter(pk=request.POST['id'],activo=True,practicahospital=True).exists():
                                docente=Profesor.objects.get(pk=request.POST['id'],activo=True,practicahospital=True)
                                return HttpResponse(json.dumps({"result":"ok2","docente":elimina_tildes(docente.persona.nombre_completo_inverso())}),content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({"result":"no"}),content_type="application/json")
                except Exception as e:
                    result['result']  = 'bad'
                    return HttpResponse(json.dumps(result), content_type="application/json")

            # elif action =='conservalordocente':
            #     # result = {}
            #     try:
            #         profesor = ProfesorMateria.objects.filter(pk=request.POST['id'])[:1].get()
            #         profesor.valor=request.POST['valor']
            #         profesor.valorporhora=True
            #         profesor.save()
            #         return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            #     except Exception as e:
            #         # result['result']  = 'bad'
            #         return HttpResponse(json.dumps({"result":"bad"}), content_type="application/json")



            elif action =='bussgaonline':
                result = {}
                try:
                    db = psycopg2.connect("host=10.10.9.45 dbname=sgaonline user=postgres password=Itb$2019")
                    cursor = db.cursor()
                    cursor.execute("select pers.nombres,pers.apellido1,pers.apellido2,pers.cedula,pers.pasaporte,pers.telefono_conv,"
                                   "pers.telefono, pers.email, pers.direccion, pers.direccion2 "
                                   "from sga_inscripcion as insc, sga_persona as pers "
                                   "where insc.persona_id = pers.id and pers.cedula = '"+ str(request.POST['numdocument'])  +"' or pers.pasaporte = '"+ str(request.POST['numdocument'])  +"' and "
                                   " insc.convalingle = True and nivelconvalid = 0 order by insc.id desc limit  1")
                    dato = cursor.fetchall()
                    db.close()
                    if len(dato) > 0:
                        result['result'] = 'ok'
                        lista = [{"nombres": dato[0][0],"apellido1": dato[0][1],"apellido2": dato[0][2],"cedula": dato[0][3],
                                  "pasaporte":dato[0][4],"telefono_conv":dato[0][5],"telefono":dato[0][6],"email":dato[0][7],
                                  "direccion":dato[0][8],"direccion2":dato[0][9]}]
                        result['datos'] = lista

                        return HttpResponse(json.dumps(result),content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
                except Exception as e:
                    result['result']  = 'bad'
                    return HttpResponse(json.dumps(result), content_type="application/json")

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
                                        change_message  = 'Descuento al Nivel desde el modulo de Nivel Pago (' + client_address + ')'  )
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
                        mail_correoadddescuentopago("DESCUENTO AGREGADO","DESCUENTO AGREGADO ",request.user,PagoNivel.objects.filter(id__in=request.POST['ids'].split(',')),int(request.POST['porcentaje']),request.POST['observacion'],nivel.carrera)
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

                        mail_correoadddescuentopago("DESCUENTO AGREGADO","DESCUENTO AGREGADO ",request.user,PagoNivel.objects.filter(id__in=request.POST['idsm'].split(',')),int(request.POST['porcentaje']),request.POST['observacion'],nivel.carrera)

                    return HttpResponse(json.dumps({"result":"ok","sindescuento":str(sindescuento),"condescuento":str(condescuento),"sindescuentomat":str(sindescuentomat),"condescuentomat":str(condescuentomat),}),content_type="application/json")
                except Exception as e:
                    print("Niveles descuentonivel error excep: "+str(e))
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

            elif action == 'aceptardocumento':
                try:

                    result = {}
                    result['result'] ="ok"

                    materialdocente= MaterialDocente.objects.get(pk=request.POST['id'])

                    materialdocente.aprobado=True

                    materialdocente.save()

                    logmateriadocente= MaterialDocenteLog(materiadocente=materialdocente,fecha=datetime.today().date(),usuario=request.user,
                                                          comentario=request.POST['comentario'])

                    logmateriadocente.save()

                    client_address = ip_client_address(request)
                    # LOG DE CAMBIAR FECHA MATREIA
                    LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(materialdocente).pk,
                    object_id       = materialdocente.id,
                    object_repr     = force_str(materialdocente),
                    action_flag     = ADDITION,
                    change_message  = 'APROBADO EL MATERIAL (' + client_address + ')' )

                    return HttpResponse(json.dumps(result),content_type="application/json")

                except Exception as ex:
                    print(ex)
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")


            elif action == 'noaceptardocumento':
                try:

                    result = {}
                    result['result'] ="ok"

                    materialdocente= MaterialDocente.objects.get(pk=request.POST['id'])

                    materialdocente.aprobado=False

                    materialdocente.save()

                    logmateriadocente= MaterialDocenteLog(materiadocente=materialdocente,fecha=datetime.today().date(),usuario=request.user,
                                                          comentario=request.POST['comentario'])

                    logmateriadocente.save()

                    client_address = ip_client_address(request)
                    # LOG DE CAMBIAR FECHA MATREIA
                    LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(materialdocente).pk,
                    object_id       = materialdocente.id,
                    object_repr     = force_str(materialdocente),
                    action_flag     = ADDITION,
                    change_message  = 'NO APROBADO EL MATERIAL (' + client_address + ')' )

                    return HttpResponse(json.dumps(result),content_type="application/json")

                except Exception as ex:
                    print(ex)
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

            elif action =='generarexcel':
                    try:
                        materia = Materia.objects.filter(pk=request.POST['matid'])[:1].get()
                        m = 10
                        titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                        titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                        titulo.font.height = 20*11
                        titulo2.font.height = 20*11
                        subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                        subtitulo3 = xlwt.easyxf('font: name Times New Roman; align: wrap on, vert centre, horiz center')
                        subtitulo.font.height = 20*10
                        wb = xlwt.Workbook()
                        ws = wb.add_sheet('Registros',cell_overwrite_ok=True)

                        tit = TituloInstitucion.objects.all()[:1].get()
                        ws.write_merge(0, 0,0,m, tit.nombre , titulo2)
                        ws.write_merge(1, 1,0,m, 'LISTADO DE ASISTENCIAS DE ESTUDIANTES POR MATERIA',titulo2)
                        ws.write(3, 0,'CARRERA: ' +materia.nivel.carrera.nombre , subtitulo)
                        ws.write(4, 0,'GRUPO:   ' +materia.nivel.grupo.nombre, subtitulo)
                        ws.write(5, 0,'NIVEL:   ' +materia.nivel.nivelmalla.nombre, subtitulo)

                        fila = 7
                        com = 7
                        detalle = 3
                        columna=6
                        c=6

                        ws.write_merge(com,fila,1,5,elimina_tildes(materia.nombre_completo()),subtitulo)
                        for leccion in materia.lecciones():
                            ws.write(fila,columna,str(leccion.fecha), subtitulo)
                            columna=columna+1
                        com=fila+1
                        fila = fila +1
                        columna=6
                        for mate in MateriaAsignada.objects.filter(materia=materia).distinct().order_by('matricula__inscripcion__persona__apellido1','matricula__inscripcion__persona__apellido2','matricula__inscripcion__persona__nombres'):
                            ws.write_merge(com,fila,1,5,elimina_tildes(mate.matricula.inscripcion),subtitulo)
                            for mat in mate.asistencias():
                                if mat.asistio:
                                    ws.write(fila,columna,str('x'), subtitulo3)
                                else:
                                    ws.write(fila,columna,'', subtitulo3)
                                columna=columna+1
                            columna=6
                            com=fila+1
                            fila = fila +1
                        columna=6
                        fila = fila +1

                        detalle = detalle + fila
                        ws.write(detalle,0, "Fecha Impresion", subtitulo)
                        ws.write(detalle,1, str(datetime.now()), subtitulo)
                        detalle=detalle+2
                        ws.write(detalle,0, "Usuario", subtitulo)
                        ws.write(detalle,1, str(request.user), subtitulo)

                        nombre ='xls_asistenciasxmateria'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                        wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                        return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                    except Exception as ex:
                        print(str(ex))
                        return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")

            elif action == 'add_idzoom':
                try:
                    result = {}
                    result['result'] ="ok"
                    profesormateria =  ProfesorMateria.objects.filter(pk=request.POST['id'])[:1].get()
                    profesormateria.idzoom = request.POST['idzoom']
                    profesormateria.save()
                    return HttpResponseRedirect('/niveles?action=materias&id='+request.POST['nivel'])
                except Exception as ex:
                    print(ex)
                    return HttpResponseRedirect('/niveles?action=materias&id='+request.POST["nivel"]+'&error:'+ex)

            elif action == 'add_tutor':
                try:
                    print(request.POST)
                    asistente = AsistenteDepartamento.objects.filter(pk=request.POST['tutor'])[:1].get()
                    nivel = Nivel.objects.filter(pk=request.POST['idnivel'])[:1].get()
                    if NivelTutor.objects.filter(nivel=nivel).exists():
                        niveltutor = NivelTutor.objects.filter(nivel=nivel)[:1].get()
                        niveltutor.tutor=asistente
                        niveltutor.save()
                        mensaje = 'Cambio de tutor'
                    else:
                        niveltutor = NivelTutor(nivel=nivel, tutor=asistente, activo=True)
                        niveltutor.save()
                        mensaje = 'Ingreso de tutor a grupo'

                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(niveltutor).pk,
                    object_id       = niveltutor.id,
                    object_repr     = force_str(niveltutor),
                    action_flag     = ADDITION,
                    change_message  = mensaje+' (' + client_address + ')' )
                    return HttpResponseRedirect('/niveles')
                except Exception as ex:
                    print(ex)
                    return HttpResponseRedirect('/niveles?error=Error al ingresar tutor, vuelva a intentarlo')

            elif action=='agregarpagos':
                    aplicar=True
                    lista2=[]
                    for pn in TIPOS_PAGO_NIVEL:
                        if not 'CUOTA' in pn[1] and not  'MATRICULA' in pn[1] :
                            lista2.append(pn[0])

                    pago = PagoNivel.objects.get(pk=request.POST['id'])
                    nivel = pago.nivel
                    f = AgregarPagoNivelMatriculaForm(request.POST)
                    if f.is_valid():
                        if GENERAR_RUBROS_PAGO:
                            matriculados = nivel.matricula_set.all()
                            # guardarLogPagonivel
                            pagonivellog= PagoNivelLog(pagonivel=pago,nivel=nivel,fecha=datetime.now(),motivo=f.cleaned_data['observacion'],usuario = request.user,valor= pago.valor)
                            pagonivellog.save()
                            for matricula in matriculados:
                                if not matricula.inscripcion.beca_senescyt().tienebeca:
                                    pp = 1.0 if not matricula.becado else ((100-matricula.porcientobeca)/100.0)

                                    if pago.tipo==0 or (pago.tipo>0 and pp>0):
                                        # Chequear que ya no lo tenga
                                        if pago.tipo==0 and RubroMatricula.objects.filter(matricula=matricula).exists():
                                            continue
                                        if pago.tipo==1 and RubroCuota.objects.filter(matricula=matricula,cuota=pago.tipo).exists():
                                            continue

                                        rubro = Rubro(fecha=datetime.today().date(),
                                                    valor = pago.valor, inscripcion=matricula.inscripcion,
                                                    cancelado = False, fechavence = pago.fecha,tiponivelpago=pago.tipo)
                                        rubro.save()

                                        # Beca
                                        if matricula.becado and pago.tipo!=0:
                                            #OCastillo 26-03-2024 excluir de beca otros rubros adicionales
                                            for l in lista2:
                                                if pago.tipo==l:
                                                    aplicar=False
                                                    break
                                            if aplicar:
                                                rubro.valor = rubro.valor * pp
                                                rubro.save()

                                        if pago.tipo==0:
                                            rm = RubroMatricula(rubro=rubro, matricula=matricula)
                                            rm.save()
                                            if HABILITA_DESC_MATRI:
                                                descuento = round(((rubro.valor * DESCUENTO_MATRIC_PORCENT) /100),2)
                                                rubro.valor = rubro.valor - round(((rubro.valor * DESCUENTO_MATRIC_PORCENT) /100),2)
                                                rubro.save()
                                                desc = Descuento(inscripcion = matricula.inscripcion,
                                                                          motivo ='DESCUENTO EN MATRICULA',
                                                                          total = rubro.valor,
                                                                          fecha = datetime.today().date())
                                                desc.save()
                                                detalle = DetalleDescuento(descuento =desc,
                                                                            rubro =rubro,
                                                                            valor = descuento,
                                                                            porcentaje = DESCUENTO_MATRIC_PORCENT)
                                                detalle.save()
                                            #guardar log de rubro
                                            rubrolog = RubroLog(rubro=rm.rubro,motivo=f.cleaned_data['observacion'],fecha = datetime.now(),
                                                                               usuario = request.user)
                                            rubrolog.save()
                                        else:
                                            # CUOTA MENSUAL
                                            if pago.tipo==1 or pago.tipo==2 or pago.tipo==3 or pago.tipo==4 or pago.tipo==5 or pago.tipo==6 or pago.tipo==7 or pago.tipo==8 or pago.tipo==9 or pago.tipo==10 or pago.tipo==11 or pago.tipo==12:
                                                rc = RubroCuota(rubro=rubro, matricula=matricula, cuota=pago.tipo)
                                                rc.save()
                                                #guardar log de rubro
                                                rubrolog = RubroLog(rubro=rc.rubro,motivo=f.cleaned_data['observacion'],fecha = datetime.now(),usuario = request.user)
                                                rubrolog.save()
                                            # elif pago.tipo==TIPO_PAGOS_EXAMEN_DE_ADMISION or pago.tipo==TIPO_PAGOS_CURSO_DE_NIVELACION:
                                            elif TipoOtroRubro.objects.filter(nombre=str(TIPOS_PAGO_NIVEL[pago.tipo][1])).exists():
                                                tiporu = TipoOtroRubro.objects.filter(nombre=str(TIPOS_PAGO_NIVEL[pago.tipo][1]))[:1].get().id
                                                rcotro = RubroOtro(rubro=rubro, tipo_id=tiporu,descripcion =str(TIPOS_PAGO_NIVEL[pago.tipo][1]))
                                                rcotro.save()
                                                rcotro.matricula=matricula.id
                                                rcotro.save()
                                                #guardar log de rubro
                                                rubrolog = RubroLog(rubro=rcotro.rubro,motivo=f.cleaned_data['observacion'],fecha = datetime.now(),usuario = request.user)
                                                rubrolog.save()

                                            else:
                                                rcotro = RubroOtro(rubro=rubro, tipo_id=TIPO_OTRO_RUBRO,descripcion =str(TIPOS_PAGO_NIVEL[pago.tipo][1]))
                                                rcotro.save()
                                                rcotro.matricula=matricula.id
                                                rcotro.save()
                                                #guardar log de rubro
                                                rubrolog = RubroLog(rubro=rcotro.rubro,motivo=f.cleaned_data['observacion'],fecha = datetime.now(),usuario = request.user)
                                                rubrolog.save()

                        return HttpResponseRedirect("/niveles?action=pagos&id="+str(nivel.id)+"&e=1")
                    else:
                        return HttpResponseRedirect("/niveles?action=pagos&id="+str(nivel.id))

            elif action=='add_valorhora':
                try:
                    pm = ProfesorMateria.objects.get(pk=request.POST['id'])
                    reg=None
                    if RegistroValorporDocente.objects.filter(profesor=pm.profesor,segmento=pm.segmento,activo=True).exists():
                        reg=RegistroValorporDocente.objects.filter(profesor=pm.profesor,segmento=pm.segmento,activo=True)[:1].get()
                    f = ValorporMateriaForm(request.POST)
                    if f.is_valid():
                        pm.valorporhora=True
                        pm.valor=f.cleaned_data['valor']
                        pm.save()
                        if reg!=None:
                            if pm.valor!=reg.valor:
                                reg.activo=False
                                reg.fecha=datetime.now()
                                reg.usuario=request.user
                                reg.save()

                                registro=RegistroValorporDocente(profesor=pm.profesor,segmento=pm.segmento,
                                                                 materia=pm.materia,valor=f.cleaned_data['valor'],
                                                                 fecha=datetime.now(),usuario=request.user)
                                registro.save()
                        else:
                            registro=RegistroValorporDocente(profesor=pm.profesor,segmento=pm.segmento,
                                                             materia=pm.materia,valor=f.cleaned_data['valor'],
                                                             fecha=datetime.now(),usuario=request.user)
                            registro.save()
                        if EMAIL_ACTIVE:
                            if pm.materia.nivel.carrera.coordinacion_pertenece().id == COORDINACION_UASSS:
                                correos = 'rcaicedoq@bolivariano.edu.ec,mxcajias@bolivariano.edu.ec'
                            elif pm.materia.nivel.carrera.coordinacion_pertenece().id == COORDINACION_UACED:
                                correos = 'kgutierrez@bolivariano.edu.ec, csolorzano@bolivariano.edu.ec'
                            else:
                                correos = 'michelle@bolivariano.edu.ec'
                            correos += ','+str(Persona.objects.get(usuario=request.user).emailinst)
                            pm.mail_valorhora_coordinacion(correos, request.user)

                        mensaje = 'Ingreso de valor por Hora $'
                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(pm).pk,
                        object_id       = pm.id,
                        object_repr     = force_str(pm),
                        action_flag     = ADDITION,
                        change_message  = mensaje+ str(pm.valor)+' (' + client_address + ')' )
                        return HttpResponse(json.dumps({"result": "ok"}),content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({"result": "bad"}),content_type="application/json")
                except Exception as e:
                    print(e)
                    return HttpResponse(json.dumps({"result": "bad"}),content_type="application/json")

            elif action == 'saveFirmaActaCalificacion':
                from firmaec.models import FirmaActaCalificacion
                from firmaec.forms import FirmaActaCalificacionForm
                with transaction.atomic():
                    try:
                        f = None
                        id = request.POST.get('id', 0)
                        idm = request.POST.get('idm', 0)
                        try:
                            eMateria = Materia.objects.get(pk=idm)
                        except ObjectDoesNotExist:
                            raise NameError(u"No se encontro materia valida")

                        f = FirmaActaCalificacionForm(request.POST)
                        f.set_responsable(request.POST.get('responsable', 0))
                        if not f.is_valid():
                            f.addErrors(f.errors.get_json_data(escape_html=True))
                            raise NameError(u"Formulario incorrecto")
                        try:
                            eFirmaActaCalificacion = FirmaActaCalificacion.objects.get(pk=id)
                            if FirmaActaCalificacion.objects.only("id").filter(materia=eMateria,responsable=f.cleaned_data['responsable']).exclude(pk=id).exists():
                                raise NameError("Responsable ya existe")
                            eFirmaActaCalificacion.materia = eMateria
                            eFirmaActaCalificacion.responsable = f.cleaned_data['responsable']
                        except ObjectDoesNotExist:
                            if FirmaActaCalificacion.objects.only("id").filter(materia=eMateria, responsable=f.cleaned_data['responsable']).exists():
                                raise NameError("Responsable ya existe")
                            eFirmaActaCalificacion = FirmaActaCalificacion(materia=eMateria,
                                                                           responsable=f.cleaned_data['responsable'])
                        eFirmaActaCalificacion.orden = f.cleaned_data['orden']
                        eFirmaActaCalificacion.tipo = f.cleaned_data['tipo']
                        eFirmaActaCalificacion.cargo = f.cleaned_data['cargo']
                        eFirmaActaCalificacion.save()
                        eMateria.mi_repositorio_acta_calificacion()
                        return JsonResponse({"isSuccess": True, "message": f"Se guardo los datos correctamente"})
                    except Exception as ex:
                        transaction.set_rollback(True)
                        forms = f.toArray() if f else {}
                        return JsonResponse({"isSuccess": False,
                                             "message": f"Error al guardar datos en el formulario. {ex.__str__()}",
                                             "forms": forms})

            elif action == 'deleteFirmaActaCalificacion':
                from sga.models import FirmaActaCalificacion
                with transaction.atomic():
                    try:
                        id = request.POST.get('id', 0)
                        try:
                            eFirmaActaCalificacion = FirmaActaCalificacion.objects.get(pk=id)
                        except ObjectDoesNotExist:
                            raise NameError("Responsable de firma de acta no encontrado")
                        eFirmaActaCalificacion.delete()
                        return JsonResponse({"isSuccess": True, "message": f"Se elimino el registro correctamente"})
                    except Exception as ex:
                        transaction.set_rollback(True)
                        return JsonResponse({"isSuccess": False, "message": f"Error al eliminar los datos. {str(ex)}"})


            return HttpResponseRedirect("/niveles")
        else:
            data = {'title': 'Niveles Academicos'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']
                if action=='add':
                    data['title'] = 'Adicionar Nivel Academico'
                    carrera = Carrera.objects.get(pk=request.GET['carrera'])
                    sede = Sede.objects.get(pk=request.GET['sede'])
                    periodo = Periodo.objects.get(pk=request.GET['periodo'])
                    if periodo.tipo.id == TIPO_PERIODO_PROPEDEUTICO:
                        form = NivelPropedeuticoForm(initial={'carrera':carrera, 'sede':sede, 'inicio': periodo.inicio, 'fin': periodo.fin})
                        form.for_grupo(carrera)
                        data['form'] = form
                    else:
                        data['form'] = NivelForm(instance=Nivel(periodo=periodo,carrera=carrera, sede=sede, inicio=periodo.inicio, fin=periodo.fin, fechatopematricula=periodo.inicio, fechatopematriculaex=periodo.inicio + timedelta(30)))
                    if 'error' in request.GET:
                        data['error']=request.GET['error']
                    return render(request ,"niveles/adicionarbs.html" ,  data)

                elif action=='cerrarmateria':
                    try:
                        materia = Materia.objects.get(pk=request.GET['id'])
                        #OCastillo 07-01-2020 multa a docente al cerrar materia la coordinacion
                        if DEFAULT_PASSWORD == 'itb':
                           materia.verificacioncuatrodias()
                        materia.cerrado = True
                        materia.fechacierre = datetime.now()
                        #materia.horacierre = datetime.now().time()
                        materia.observaciones = "Cerrada por Administrador"
                        materia.save()
                        # promedioreprobado = MateriaAsignada.objects.filter(Q(materia=materia),Q(notafinal__lt=NOTA_PARA_APROBAR)|Q(asistenciafinal__lt=ASIST_PARA_APROBAR),Q(absentismo=False)).count()*100/MateriaAsignada.objects.filter(materia=materia,absentismo=False).count()
                        # promedioaprobado = MateriaAsignada.objects.filter(materia=materia,notafinal__gte=NOTA_PARA_APROBAR,asistenciafinal__gte=ASIST_PARA_APROBAR,absentismo=False).count()*100/MateriaAsignada.objects.filter(materia=materia,absentismo=False).count()
                        # totalreprobado = MateriaAsignada.objects.filter(Q(materia=materia),Q(notafinal__lt=NOTA_PARA_APROBAR)|Q(asistenciafinal__lt=ASIST_PARA_APROBAR),Q(absentismo=False)).count()
                        # totalaprobado = MateriaAsignada.objects.filter(materia=materia,notafinal__gte=NOTA_PARA_APROBAR,asistenciafinal__gte=ASIST_PARA_APROBAR,absentismo=False).count()
                        # totalalumnos = MateriaAsignada.objects.filter(materia=materia,absentismo=False).count()
                        # if promediototal >= 40:
                        # if EMAIL_ACTIVE:
                        #     materia.correo_promedio(totalalumnos,totalaprobado,promedioaprobado,totalreprobado,promedioreprobado)
                        client_address = ip_client_address(request)

                            # Log de ABRIR MATERIA
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(materia).pk,
                            object_id       = materia.id,
                            object_repr     = force_str(materia),
                            action_flag     = CHANGE,
                            change_message  = 'Materia Cerrada por Administrador  (' + client_address + ')' )
                    except Exception as ex:
                        print(ex)
                    return HttpResponseRedirect("/niveles?action=materias&id="+str(materia.nivel.id))

                elif action=='buscar':
                    if CENTRO_EXTERNO:
                        try:
                            from ext.models import MateriaExterna
                            data['coordinador'] = Persona.objects.filter(usuario__groups__id=COORDINADOR_GROUP_ID, usuario__is_active=True,usuario=request.user)
                            filtro = request.GET['par']
                            nivel = Nivel.objects.get(pk=1)
                            data['nivel'] = nivel
                            materias = nivel.materia_set.filter(materiaexterna__codigo__icontains=filtro).order_by('-inicio', 'id')
                            data['materias']=materias
                            data['centroexterno']= CENTRO_EXTERNO
                            for materia in materias:
                                if MateriaExterna.objects.filter(materia=materia).exists():
                                    paralelo = {'paralelo': MateriaExterna.objects.filter(materia=materia)[:1].get().codigo }
                                    entidad = {'entidad': MateriaExterna.objects.filter(materia=materia)[:1].get().entidad.codigo }
                                    cantexp = {'cantexp': MateriaExterna.objects.filter(materia=materia)[:1].get().cantexport }
                                    exp_itb = {'exp_itb': ''}
                                    if MateriaExterna.objects.filter(materia=materia,cantexport=20).exists():
                                        exp_itb = {'exp_itb': MateriaExterna.objects.filter(materia=materia,cantexport=20)[:1].get().cantexport}
                                    rubros_matitb = {'rubros_matitb': ''}
                                    if PagosCursoITB.objects.filter(materia=materia).exists():
                                        rubros_matitb = {'rubros_matitb': PagosCursoITB.objects.filter(materia=materia).count()}
                                else:
                                    paralelo = {'paralelo':''}
                                    entidad = {'entidad':''}
                                    cantexp = {'cantexp':''}

                                materia.__dict__.update(paralelo)
                                materia.__dict__.update(entidad)
                                materia.__dict__.update(cantexp)
                                materia.__dict__.update(exp_itb)
                                materia.__dict__.update(rubros_matitb)

                            data['materias'] = materias

                            return render(request ,"niveles/materiasbs.html" ,  data)
                        except Exception as ex:
                            return render(request ,"niveles" ,  data)
                elif action=='addlibre':
                    data['title'] = 'Adicionar Nivel Academico'
                    coordinacion = Coordinacion.objects.get(pk=request.GET['coordinacion'])
                    periodo = Periodo.objects.get(pk=request.GET['periodo'])
                    data['form'] = NivelLibreForm(initial={'inicio': periodo.inicio, 'fin': periodo.fin, 'fechatopematricula': periodo.fin})
                    data['coordinacion'] = coordinacion
                    data['periodo'] = periodo
                    return render(request ,"niveles/libres/adicionarbs.html" ,  data)
                elif action=='abrirn':
                    n = Nivel.objects.get(pk=request.GET['nid'])
                    n.cerrado = False
                    n.save()
                    client_address = ip_client_address(request)

                    # Log de ADICIONADO CRONOGRAMA DE PAGOS
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(n).pk,
                        object_id       = n.id,
                        object_repr     = force_str(n),
                        action_flag     = DELETION,
                        change_message  = 'Abierto Nivel (' + client_address  + ')')
                    if EMAIL_ACTIVE:
                        n.mail_abrir(request.user)

                    return HttpResponseRedirect("/niveles?action=materias&id="+str(n.id))

                elif action=='edit':
                    data['title'] = 'Editar Nivel Academico'
                    nivel = Nivel.objects.get(pk=request.GET['id'])
                    form = NivelFormEdit(instance=nivel)
                    if nivel.periodo.tipo_id == TIPO_PERIODO_PROPEDEUTICO:
                        form.for_nivelacion(nivel.carrera)
                        data['form'] = form
                    else:
                        form.for_grupo(nivel.carrera)
                        data['form'] = form

                    data['nivel'] = nivel
                    return render(request ,"niveles/editarbs.html" ,  data)
                elif action=='editlibre':
                    data['title'] = 'Editar Nivel Academico'
                    nivel = Nivel.objects.get(pk=request.GET['id'])
                    form = NivelLibreForm(initial=model_to_dict(nivel))
                    data['form'] = form
                    data['nivel'] = nivel
                    return render(request ,"niveles/libres/editarbs.html" ,  data)
                elif action=='del':
                    data['title'] = 'Borrar Nivel Academico'
                    nivel = Nivel.objects.get(pk=request.GET['id'])
                    data['nivel'] = nivel
                    return render(request ,"niveles/borrarbs.html" ,  data)
                elif action=='abrirm':
                    materia = Materia.objects.get(pk=request.GET['id'])
                    materia.cerrado = False
                    materia.save()
                    return HttpResponseRedirect("/niveles")
                elif action=='tomandom':
                    data['title'] = 'Tomando la Materia'
                    materia = Materia.objects.get(pk=request.GET['id'])
                    inscripcion = Inscripcion.objects.filter(matricula__materiaasignada__materia=materia)
                    data['materia']= materia
                    data['inscripciones'] = inscripcion
                    data['grupo'] = request.GET['grupo']
                    data['coordinador'] = Persona.objects.filter(usuario__groups__id=COORDINADOR_GROUP_ID, usuario__is_active=True,usuario=request.user)
                    data['form'] = EstudianteInglesForm()
                    return render(request ,"niveles/tomandobs.html" ,  data)
                elif action=='filtrar':
                    data['title'] = 'Materias del Nivel Academico'
                    nivel = Nivel.objects.get(pk=request.GET['id'])
                    data['nivel'] = nivel
                    data['cronogramapagos'] = MODELO_EVALUACION!=EVALUACION_TES
                    data['materialibre'] = MODELO_EVALUACION==EVALUACION_TES
                    data['centroexterno'] = CENTRO_EXTERNO

                    if CENTRO_EXTERNO:
                        from ext.models import MateriaExterna
                        data['coordinador'] = Persona.objects.filter(usuario__groups__id=COORDINADOR_GROUP_ID, usuario__is_active=True,usuario=request.user)

                    if "f" in request.GET:
                        f = request.GET['f']
                        if f=='1':
                            materias = nivel.materia_set.filter(materiaexterna__cantexport__lt=3).order_by('inicio', 'id')
                        if f=='2':
                            materias = nivel.materia_set.filter(materiaexterna__cantexport__lt=3,cerrado=True).order_by('inicio', 'id')
                        if f=='3':
                            materias = nivel.materia_set.filter(cerrado=False).order_by('inicio', 'id')
                        if f=='4':
                            materias = nivel.materia_set.filter(materiaexterna__exportada=True, materiaexterna__cantexport__lt=3).order_by('inicio', 'id')



                    else:
                        materias = nivel.materia_set.filter(materiaexterna__cantexport__lt=3).order_by('inicio', 'id')

                    for materia in materias:
                        if MateriaExterna.objects.filter(materia=materia).exists():
                            paralelo = {'paralelo': MateriaExterna.objects.filter(materia=materia)[:1].get().codigo }
                            entidad = {'entidad': MateriaExterna.objects.filter(materia=materia)[:1].get().entidad.codigo }
                            cantexp = {'cantexport': MateriaExterna.objects.filter(materia=materia)[:1].get().cantexport }
                        else:
                            paralelo = {'paralelo':''}
                            entidad = {'entidad':''}
                            cantexp = {'cantexport':''}

                        materia.__dict__.update(paralelo)
                        materia.__dict__.update(entidad)
                        materia.__dict__.update(cantexp)
                    data['materias'] = materias
                    # data['frmfechas']  = FechasForm()
                    return render(request ,"niveles/materiasbs.html" ,  data)

                # elif action == 'actualiza':
                #     try:
                #         for p in ProfesorMateria.objects.filter(desde__lte='2019-12-15',desde__gte='2019-01-01').order_by('desde'):
                #             p.fechacorreo = datetime.now().date()
                #             p.aceptacion = True
                #             p.save()
                #             if p.profesor_aux:
                #                 profesor = Profesor.objects.get(pk=p.profesor_aux)
                #             else:
                #                 profesor = p.profesor
                #             log = LogAceptacionProfesorMateria(materia =p.materia,
                #                                                 profesor = profesor,
                #                                                 fechaceptacion =  datetime.now().date(),
                #                                                 aceptacion = True,
                #                                                 tipolog = 1,
                #                                                 profesormateria = p,
                #                                                 oberservacion="ACEPTACION AUTOMATICA")
                #             log.save()
                #             print(str(p.desde))
                #         return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                #     except:
                #         return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
                elif action=='eliminarbk':
                    inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                    matricula = Matricula.objects.filter(inscripcion=inscripcion)[:1].get()
                    if  MateriaAsignada.objects.filter(materia__id=request.GET['materia'],matricula=matricula).exists():
                        materiaasignada = MateriaAsignada.objects.filter(materia__id=request.GET['materia'],matricula=matricula)[:1].get()
                        client_address = ip_client_address(request)

                        # Log de ADICIONADO CRONOGRAMA DE PAGOS
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(materiaasignada).pk,
                            object_id       = materiaasignada.id,
                            object_repr     = force_str(materiaasignada),
                            action_flag     = DELETION,
                            change_message  = 'Eliminada Materia de BK (' + client_address  + ')')
                        materiaasignada.delete()
                        materia = Materia.objects.get(pk=request.GET['materia'])
                        inscripcion = Inscripcion.objects.filter(matricula__materiaasignada__materia=materia)
                        data['materia']= materia
                        data['inscripciones'] = inscripcion
                        return render(request ,"niveles/tomandobs.html" ,  data)

                elif action=='materias':
                    try:
                        data['title'] = 'Materias del Nivel Academico'
                        nivel = Nivel.objects.get(pk=request.GET['id'])
                        data['nivel'] = nivel

                        data['cronogramapagos'] = MODULO_FINANZAS_ACTIVO
                        data['materialibre'] = MODELO_EVALUACION==EVALUACION_TES
                        data['centroexterno'] = CENTRO_EXTERNO
                        data['frmquitardocente']=LogQuitarAsignacionProfesorForm(initial={'fechahasta':datetime.now().date()})
                        if 'msj' in request.GET:
                            data['mensaje'] = request.GET['msj']

                        if CENTRO_EXTERNO:
                            from ext.models import MateriaExterna
                            materias = nivel.materia_set.filter(cerrado=False).order_by('-inicio','id')
                            data['coordinador'] = Persona.objects.filter(usuario__groups__id=COORDINADOR_GROUP_ID, usuario__is_active=True,usuario=request.user)
                            for materia in materias:
                                #if materia.materiaexterna_set.all()[:1].get().exportada:
                                if MateriaExterna.objects.filter(materia=materia).exists():
                                    paralelo = {'paralelo': MateriaExterna.objects.filter(materia=materia)[:1].get().codigo }
                                    entidad = {'entidad': MateriaExterna.objects.filter(materia=materia)[:1].get().entidad.codigo }
                                    cantexport = {'cantexport': MateriaExterna.objects.filter(materia=materia)[:1].get().cantexport }
                                else:
                                    paralelo = {'paralelo':''}
                                    entidad = {'entidad':''}
                                    cantexport = {'cantexport':''}

                                materia.__dict__.update(paralelo)
                                materia.__dict__.update(entidad)
                                materia.__dict__.update(cantexport)
                        else:
                            if INSCRIPCION_CONDUCCION:
                                materias = nivel.materia_set.all().order_by('inicio', 'id').exclude(asignatura__id=ASIGNATURA_PRACTICA_CONDUCCION)
                            else:
                                materias = nivel.materia_set.all().order_by('inicio', 'id')
                        data['materias'] = materias
                        data['materianivel'] = MateriaNivel.objects.filter(nivel=nivel)
                        data['VALIDA_MATERIA_APROBADA'] = VALIDA_MATERIA_APROBADA
                        data['INSCRIPCION_CONDUCCION'] = INSCRIPCION_CONDUCCION
                        data['ASIGNATURA_SEMINARIO']= ASIGNATURA_SEMINARIO
                        data['DEFAULT_PASSWORD']= DEFAULT_PASSWORD
                        data['VALOR_HORA_MINIMO']= VALOR_HORA_MINIMO
                        data['VALOR_HORA_MAXIMO']= VALOR_HORA_MAXIMO
                        # data['fechahoy'] = datetime.now()
                        # data['frmfechas']  = FechasForm(initial={"exordinario":nivel.fin,"revision":nivel.fin,"exatrasado":nivel.fin})
                        data['valormateria']=ValorporMateriaForm()
                        return render(request ,"niveles/materiasbs.html" ,  data)
                    except Exception as ex:
                        return HttpResponseRedirect(f"/niveles?info={ex.__str__()}")

                elif action=='asignaragrupo':
                    data['title'] = 'Asignacion de Materia a otro Grupo'
                    materia = Materia.objects.get(pk=request.GET['id'])
                    data['materia'] = materia
                    data['form'] = AsignarMateriaGrupoForm()
                    return render(request ,"niveles/gruposbs.html" ,  data)
                elif action=='pagos':
                    data['title'] = 'Cronograma de Pagos del Nivel Academico'
                    nivel = Nivel.objects.get(pk=request.GET['id'])
                    data['nivel'] = nivel
                    data['pagos'] = nivel.pagonivel_set.all().order_by('tipo','fecha')
                    if 'e' in request.GET:
                        data['e'] = request.GET['e']
                    data['editable'] = MODELO_EVALUACION!=EVALUACION_TES
                    data['pagoniveles'] = PagoNivel.objects.filter(nivel=nivel).exclude(tipo=0).order_by('fecha')
                    data['pagomatricula'] = PagoNivel.objects.filter(nivel=nivel,tipo=0).order_by('fecha')
                    return render(request ,"niveles/pagosbs.html" ,  data)
                elif action=='addpagos':
                    data['title'] = 'Adicionar Cronograma de Pagos al Nivel Academico'
                    nivel = Nivel.objects.get(pk=request.GET['id'])
                    data['nivel'] = nivel
                    fecha = datetime.now()
                    data['form']= PagoNivelForm(initial={'fecha':fecha})
                    data['form'].excluir_tipos(nivel)
                    return render(request ,"niveles/addpagosbs.html" ,  data)
                elif action=='addpagosmatricula':
                    data['title'] = 'Adicionar Pago a la Matricula'
                    pagonivel = PagoNivel.objects.get(pk=request.GET['id'])
                    data['nivel'] = pagonivel.nivel
                    data['tipo'] = pagonivel.nombre
                    data['form'] = AgregarPagoNivelMatriculaForm()
                    data['pagonivel'] = pagonivel
                    return render(request ,"niveles/addpagomatriculabs.html" ,  data)
                # elif action=='agregarpagos':
                #     pago = PagoNivel.objects.get(pk=request.GET['id'])
                #     nivel = pago.nivel
                #     if GENERAR_RUBROS_PAGO:
                #         matriculados = nivel.matricula_set.all()
                #         for matricula in matriculados:
                #             if not matricula.inscripcion.beca_senescyt().tienebeca:
                #                 pp = 1.0 if not matricula.becado else ((100-matricula.porcientobeca)/100.0)
                #
                #                 if pago.tipo==0 or (pago.tipo>0 and pp>0):
                #                     # Chequear que ya no lo tenga
                #                     if pago.tipo==0 and RubroMatricula.objects.filter(matricula=matricula).exists():
                #                         continue
                #                     if pago.tipo==1 and RubroCuota.objects.filter(matricula=matricula,cuota=pago.tipo).exists():
                #                         continue
                #
                #                     rubro = Rubro(fecha=datetime.today().date(),
                #                                 valor = pago.valor, inscripcion=matricula.inscripcion,
                #                                 cancelado = False, fechavence = pago.fecha)
                #                     rubro.save()
                #
                #                     # Beca
                #                     if matricula.becado and pago.tipo!=0:
                #                         rubro.valor = rubro.valor * pp
                #                         rubro.save()
                #
                #                     if pago.tipo==0:
                #                         rm = RubroMatricula(rubro=rubro, matricula=matricula)
                #                         rm.save()
                #                     else:
                #                         # CUOTA MENSUAL
                #                         rc = RubroCuota(rubro=rubro, matricula=matricula, cuota=pago.tipo)
                #                         rc.save()
                #     return HttpResponseRedirect("/niveles?action=pagos&id="+str(nivel.id)+"&e=1")
                elif action=='editpagos':
                    data['title'] = 'Editar Cronograma de Pagos del Nivel'
                    pagonivel = PagoNivel.objects.get(pk=request.GET['id'])
                    data['nivel'] = pagonivel.nivel
                    data['tipo'] = pagonivel.nombre
                    initial = model_to_dict(pagonivel)
                    data['form'] = PagoNivelEditForm(initial=initial)
                    data['pagonivel'] = pagonivel
                    return render(request ,"niveles/editpagosbs.html" ,  data)
                elif action=='delpagos':
                    try:
                        pagonivel = PagoNivel.objects.get(pk=request.GET['id'])
                        nivel = pagonivel.nivel

                        if pagonivel.tipo==0:
                            for r in RubroMatricula.objects.filter(matricula__nivel=nivel):
                                if r.rubro.puede_eliminarse():
                                    r.rubro.delete()
                        else:
                            for r in RubroCuota.objects.filter(matricula__nivel=nivel, cuota=pagonivel.tipo):
                                if r.rubro.puede_eliminarse():
                                    r.rubro.delete()
                            #OCastillo 26-04-2023 poder eliminar los rubros adicionales del cronograma
                            matriculados = nivel.matricula_set.all()
                       # if  pagonivel.tipo ==TIPO_PAGOS_EXAMEN_DE_ADMISION:
                            for matricula in matriculados:
                                for ro in RubroOtro.objects.filter(matricula=matricula.id,rubro__tiponivelpago=pagonivel.tipo):
                                    if ro.rubro.puede_eliminarse():
                                        ro.rubro.delete()
                        pagonivel.delete()
                        client_address = ip_client_address(request)

                            # Log de ADICIONADO CRONOGRAMA DE PAGOS
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(nivel).pk,
                            object_id       = nivel.id,
                            object_repr     = force_str(nivel),
                            action_flag     = DELETION,
                            change_message  = 'Eliminado Cronograma de Pagos (' + client_address  + ')')
                        return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                    except Exception as e:
                        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

                elif action=='editmateria':
                    try:
                        data['title'] = 'Editar Materia de Nivel Academico'
                        materia = Materia.objects.get(pk=request.GET['id'])
                        if not materia.inicio and not materia.fin:
                            materia.inicio = datetime.now().date()
                            materia.fin = datetime.now().date()
                        data['materia'] = materia
                        form = MateriaForm(instance=materia)
                        form.for_modelo_evaluativo(materia.nivel.sede)
                        data['form'] = form
                        data['materialibre'] = MODELO_EVALUACION==EVALUACION_TES
                        if 'error' in request.GET:
                            data['error'] = request.GET['error']
                        data['DEFAULT_PASSWORD']= DEFAULT_PASSWORD
                        return render(request ,"niveles/edit_materiabs.html" ,  data)
                    except Exception as ex:
                        return HttpResponseRedirect(f"/niveles?action=materias&id={materia.nivel_id}")

                elif action=='addmateria':
                    try:
                        data['title'] = 'Adicionar Materia a Nivel Academico'
                        data['nivel'] = eNivel = Nivel.objects.get(pk=request.GET['id'])
                        if CENTRO_EXTERNO:
                                # data['form'] = MateriaFormCext(instance=Materia(nivel=data['nivel'], inicio=datetime.now(), fin=datetime.now(), horas=0, creditos=0))
                            fecha = datetime.now()
                            data['form'] = MateriaCursoBuckForm(initial={'inicio': fecha, 'fin': fecha})
                            data['externo'] = CENTRO_EXTERNO
                        else:
                            form = MateriaForm(instance=Materia(nivel=data['nivel'], inicio=data['nivel'].inicio, fin=data['nivel'].fin))
                            form.for_modelo_evaluativo(eNivel.sede)
                            data['form'] = form
                        data['materialibre'] = MODELO_EVALUACION==EVALUACION_TES
                        data['action'] = 'addmateria'
                        if 'error' in request.GET:
                            data['error'] = request.GET['error']
                        return render(request ,"niveles/adicionar_materiabs.html" ,  data)
                    except Exception as ex:
                        return HttpResponseRedirect(f"/niveles?action=materias&id={eNivel.id}")

                elif action=='deletemateria':
                    data['title'] = 'Borrar Materia de Nivel Academico'
                    try:
                        materia = Materia.objects.get(pk=request.GET['id'])
                        data['materia'] = materia
                        data['nivel'] = materia.nivel
                        return render(request ,"niveles/borrar_materiabs.html" ,  data)
                    except Exception as ex:
                        return HttpResponseRedirect('/niveles')

                elif action=='deleteclases':
                    data['title'] = 'Borrar Clases de la Materia'
                    materia = Materia.objects.get(pk=request.GET['id'])
                    data['materia'] = materia
                    data['nivel'] = materia.nivel
                    return render(request ,"niveles/borrar_clasesbs.html" ,  data)

                elif action=='addprofesor':
                    data['title'] = 'Adicionar Profesor a Materia de Nivel Academico'
                    data['materia'] = Materia.objects.get(pk=request.GET['mid'])
                    data['institucion'] = MODELO_EVALUACION
                    data['conduccion'] = INSCRIPCION_CONDUCCION
                    data['form'] = ProfesorMateriaFormAdd(initial={'desde':data['materia'].inicio, 'hasta':data['materia'].fin})
                    if 'error' in request.GET:
                        data['error'] = request.GET['error']
                    return render(request ,"niveles/adicionar_profesorbs.html" ,  data)

                elif action=='addprofesornivelcerrado':
                    desde = datetime.today().date()
                    hasta=desde + timedelta(days=4)
                    data['title'] = 'Adicionar Profesor a Materia en Nivel Cerrado'
                    data['materia'] = Materia.objects.get(pk=request.GET['id'])
                    data['form'] = ProfesorMateriaFormAdd(initial={'desde':desde, 'hasta':hasta})
                    if 'error' in request.GET:
                        data['error'] = request.GET['error']
                    return render(request ,"niveles/adicionar_profesorbs.html" ,  data)

                elif action=='addrubro':
                    data['title'] = 'Adicionar Otro Rubro a Estudiantes'
                    data['nivel'] = Nivel.objects.get(pk=request.GET['nivel'])
                    hoy = datetime.today()
                    data['form'] = AdicionarOtroRubroForm(initial={'fecha': hoy})
                    persona = request.session['persona']
                    data['tiene_permisos'] = persona.puede_ver_ingresos()
                    return render(request ,"niveles/adicionar_otrosrubrosbs.html" ,  data)
                elif action=='editprofesor':
                    data['title'] = 'Editar Profesor de Materia de Nivel Academico'
                    pm = ProfesorMateria.objects.get(pk=request.GET['pmid'])
                    data['profesormateria'] = pm
                    data['institucion'] = MODELO_EVALUACION
                    data['conduccion'] = INSCRIPCION_CONDUCCION
                    if 'error' in request.GET:
                        data['error'] = request.GET['error']
                    data['form'] = ProfesorMateriaFormAdd(initial={'segmento': pm.segmento, 'profesor': pm.profesor, 'profesor_aux': pm.profesor_aux, 'desde': pm.desde , 'hasta': pm.hasta})
                    data['form'].for_tipodocente(pm.segmento.id)
                    return render(request ,"niveles/editar_profesorbs.html" ,  data)
                elif action=='abrirmateria':
                    data['title'] = 'Abrir materias cerradas'
                    materia = Materia.objects.get(pk=request.GET['id'])
                    data['materia'] = materia
                    data['form'] = ObservacionAbrirMateriaForm()
                    return render(request ,"niveles/abrirmateria.html" ,  data)

                elif action=='addrubrositb':
                    #OCU 25-06-2018 Accion para crear los rubros de los nuevos grupos de importacion ITB
                    data['title'] = 'Adicionar Rubros a Materia'
                    materia = Materia.objects.get(pk=request.GET['id'])
                    grupo=request.GET['grupo']
                    data['rubromateria'] = materia
                    data['grupo'] = grupo
                    fecha = datetime.now()
                    data['form']= PagoCursoForm(initial={'fechavence':fecha})
                    return render(request ,"niveles/addrubrositb.html" ,  data)

                elif action=='verrubrositb':
                    data['title'] = 'Editar Rubros de Materia'
                    materia = Materia.objects.get(pk=request.GET['id'])
                    grupo=request.GET['grupo']
                    data['grupo'] = grupo
                    rubros_matitb = {'rubros_matitb': ''}
                    if PagosCursoITB.objects.filter(materia=materia).exists():
                        pagositb = PagosCursoITB.objects.filter(materia=materia)
                        data['pagositb'] = pagositb
                        rubros_matitb = {
                            'rubros_matitb': PagosCursoITB.objects.filter(materia=materia)[:1].get().materia}

                    materia.__dict__.update(rubros_matitb)
                    data['materia'] = materia

                    return render(request ,"niveles/rubrosobsitb.html" ,  data)

                elif action=='delrubrositb':
                    #OCU 26-06-2018 Accion para borrar los rubros de los nuevos grupos de importacion ITB
                    data['title'] = 'Borrar Pagos'
                    pagositb = PagosCursoITB.objects.get(pk=request.GET['id'])
                    data['pagositb'] = pagositb
                    return render(request ,"niveles/borrarrubroitb.html" ,  data)
                elif action=='addfechaculm':
                    nivel = Nivel.objects.filter(pk=request.GET['nivel'])[:1].get()
                    try:
                        materia = Materia.objects.filter(pk=request.GET['mat'])[:1].get()
                        materia.culminacion_tit=convertir_fecha(request.GET['fecha'])
                        materia.save()
                    except Exception as e:
                        return HttpResponseRedirect('/niveles?action=materias&id='+str(nivel.id)+'&msj='+str(e))
                    return HttpResponseRedirect('/niveles?action=materias&id='+str(nivel.id))

                elif action=='detallearch':
                    data = {}
                    data['vermaterialdocente'] = MaterialDocente.objects.filter(profesormateria__id=request.GET['id']).order_by('fecha')

                    return render(request ,"niveles/detallearchivbec.html" ,  data)

                elif action=='verlogobservaciones':
                    pagonivellog = PagoNivelLog.objects.filter(pagonivel__id=int(request.GET['idpagonivel'])).order_by('-fecha')
                    data['historialpagonivellog']=pagonivellog
                    return render(request ,"niveles/verhistorial.html" ,  data)

                elif action=='editrubrositb':
                    #OCU 25-06-2018 Accion para crear los rubros de los nuevos grupos de importacion ITB
                    data['title'] = 'Editar Rubros a Materia '
                    pagoscursoitb = PagosCursoITB.objects.get(pk=request.GET['id'])
                    data['pagoscursoitb'] = pagoscursoitb.materia
                    data['nombre'] = pagoscursoitb.nombre
                    data['fechavence']=pagoscursoitb.fechavence
                    data['valor']=pagoscursoitb.valor
                    initial = model_to_dict(pagoscursoitb)
                    data['form'] = PagoCursoForm(initial=initial)
                    data['pagoscursoitb'] = pagoscursoitb
                    return render(request ,"niveles/editrubrositb.html" ,  data)

                elif action=='importar_estitb':
                #OC 26-junio-2018 para importar estudiantes matriculados del SGA a Buck, matricularlos y asignar los valores creados
                    materiacurso= Materia.objects.get(pk=request.GET['id'])
                    datos = requests.get(API_URL_ITB,params={'a': 'impgrupo','grupo': materiacurso.grupo })
                    pagocurso = PagosCursoITB.objects.filter(materia=materiacurso)
                    hoy = datetime.today()
                    if datos.status_code==200:
                        matriculados = datos.json()

                    for d in matriculados:
                        try:
                            if not Persona.objects.filter(cedula=d[3]).exists() and  not  Persona.objects.filter(pasaporte=d[3]).exists():
                                        cedula = ''
                                        pasaporte = ''
                                        if len(d[3])==10:
                                            cedula =d[3]
                                        else:
                                            pasaporte = d[3]
                                        p = Persona(apellido1 =d[0],
                                                    apellido2 = d[1],
                                                    nombres = d[2],
                                                    cedula = cedula,
                                                    pasaporte = pasaporte,
                                                    telefono_conv = d[5],
                                                    telefono = d[6],
                                                    email = d[7],
                                                    direccion = d[8],
                                                    direccion2 = d[9])
                                        p.save()
                                        if pasaporte != '':
                                            p.extranjero=True
                                            p.save()

                            else:
                                if Persona.objects.filter(cedula=d[3]).exists():
                                    p = Persona.objects.filter(cedula=d[3])[:1].get()
                                else:
                                    p = Persona.objects.filter(pasaporte=d[3])[:1].get()

                            if not Inscripcion.objects.filter(persona=p).exists():
                                 inscrip = Inscripcion(persona = p,
                                                       carrera_id = 2,
                                                       modalidad_id = 1,
                                                       sesion_id = 1,
                                                       especialidad_id=1,
                                                       fecha=datetime.now())
                                 inscrip.save()
                            else:
                                 inscrip = Inscripcion.objects.filter(persona=p)[:1].get()

                            #matricular alumnos
                            nivel = Nivel.objects.filter()[:1].get()
                            if not Matricula.objects.filter(inscripcion=inscrip, nivel=nivel).exists():

                                alu_matricul = Matricula(inscripcion = inscrip,
                                                         nivel = nivel)
                                alu_matricul.save()
                            else:
                                alu_matricul = Matricula.objects.filter(inscripcion=inscrip, nivel=nivel)[:1].get()

                            if not MateriaAsignada.objects.filter(matricula=alu_matricul,materia=materiacurso).exists():
                                alu_materia = MateriaAsignada(matricula = alu_matricul,
                                                              materia = materiacurso,
                                                              notafinal = 0,
                                                              asistenciafinal = 0,
                                                              supletorio = 0,
                                                              cerrado = False)
                                alu_materia.save()

                            #asignacion de rubros
                            pcurso = PagosCursoITB.objects.filter(materia=materiacurso)[:1].get()
                            if not DetallePagosITB.objects.filter(inscripcion=inscrip,materia=materiacurso,rubrocurso=pcurso).exists():
                                for pagos in pagocurso:
                                    hoy = datetime.now().date()
                                    detallepagos = DetallePagosITB(inscripcion = inscrip,
                                                                   materia=materiacurso,
                                                                   rubrocurso=pagos)
                                    detallepagos.save()

                                    r = Rubro(fecha =hoy,
                                              valor = pagos.valor,
                                              inscripcion = inscrip,
                                              cancelado = False,
                                              fechavence = pagos.fechavence)
                                    r.save()

                                    rotro = RubroOtro(rubro=r,
                                                      tipo=TipoOtroRubro.objects.get(pk=RUBRO_TIPO_CURSOS),
                                                      descripcion= pagos.materia.asignatura.nombre + " - " + pagos.materia.grupo+ " - " + pagos.nombre)
                                    rotro.save()
                                    detallepagos.rubro = r
                                    detallepagos.save()
                            else:
                                for pagos in pagocurso:
                                    if DetallePagosITB.objects.filter(inscripcion=inscrip,materia=materiacurso,rubrocurso=pagos).exists():
                                        rubrodet=DetallePagosITB.objects.get(inscripcion=inscrip,materia=materiacurso,rubrocurso=pagos)
                                        rbdet = Rubro.objects.get(pk=rubrodet.rubro.id)

                                        if rbdet.cancelado==False:
                                            rbdet.fecha=hoy
                                            rbdet.valor = pagos.valor
                                            rbdet.fechavence= pagos.fechavence
                                            rbdet.save()

                                            rubrootro=RubroOtro.objects.get(rubro=rbdet)
                                            rubrootro.descripcion=rubrodet.rubrocurso.nombre
                                            rubrootro.save()

                        except Exception as ex:
                                return HttpResponseRedirect("/?info=Error al Importar "+str(ex))

                    client_address = ip_client_address(request)
                    # Log de importacion de materia curso
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(materiacurso).pk,
                        object_id       = materiacurso.id,
                        object_repr     = force_str(materiacurso),
                        action_flag     = ADDITION,
                        change_message  = 'Importacion Realizada (' + client_address + ')')

                    return HttpResponseRedirect("/niveles?action=buscar&par="+str(materiacurso.grupo))

                elif action == 'agregarestudiante':
                    #OCU 16-07-2019 para agregar estudiantes en Buck
                    try:
                        materia = Materia.objects.get(pk=request.GET['mat'])
                        inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                        nivel = Nivel.objects.filter()[:1].get()
                        if not Matricula.objects.filter(inscripcion=inscripcion, nivel=nivel).exists():
                            alu_matricul = Matricula(inscripcion = inscripcion,nivel = nivel)
                            alu_matricul.save()
                        else:
                            alu_matricul = Matricula.objects.filter(inscripcion=inscripcion, nivel=nivel)[:1].get()
                        if not MateriaAsignada.objects.filter(matricula=alu_matricul,materia=materia).exists():
                            alu_materia = MateriaAsignada(matricula = alu_matricul,
                                                          materia = materia,
                                                          notafinal = 0,
                                                          asistenciafinal = 0,
                                                          supletorio = 0,
                                                          cerrado = False)
                            alu_materia.save()

                        return HttpResponseRedirect("/niveles")
                    except Exception as e:
                        return HttpResponseRedirect('/?info='+str(e))

                elif action == 'crear_curso_eva':
                    from moodle.functions import crear_curso_eva
                    with transaction.atomic():
                        try:
                            try:
                                eMateria = Materia.objects.get(pk=request.GET.get('id', 0))
                            except ObjectDoesNotExist:
                                raise NameError(u"Materia no encontrada")
                            crear_curso_eva(eMateria)
                            return JsonResponse({"isSuccess": True, "message": "Se creo correctamente el curso en EVA"})
                        except Exception as ex:
                            transaction.set_rollback(True)
                            return JsonResponse({"isSuccess": False, "message": u"Error al crear el curso en EVA: %s" % ex.__str__()})

                elif action == 'actualizar_modelo_eva':
                    from moodle.functions import crear_actualizar_categoria_notas_curso
                    with transaction.atomic():
                        try:
                            try:
                                eMateria = Materia.objects.get(pk=request.GET.get('id', 0))
                            except ObjectDoesNotExist:
                                raise NameError(u"Materia no encontrada")
                            crear_actualizar_categoria_notas_curso(eMateria)
                            return JsonResponse({"isSuccess": True, "message": "Se actualizo correctamente el modelo evaluativo en EVA"})
                        except Exception as ex:
                            transaction.set_rollback(True)
                            return JsonResponse({"isSuccess": False, "message": u"Error al actualizar el modelo evaluativo en EVA: %s" % ex.__str__()})

                elif action == 'actualizar_silabo_eva':
                    with transaction.atomic():
                        try:
                            from moodle.functions import crear_estilo_tarjeta, crear_actualizar_silabo
                            try:
                                eMateria = Materia.objects.get(pk=request.GET.get('id', 0))
                            except ObjectDoesNotExist:
                                raise NameError(u"Materia no encontrada")
                            crear_estilo_tarjeta(eMateria)
                            crear_actualizar_silabo(eMateria)
                            return JsonResponse({"isSuccess": True, "message": "Se actualizo correctamente el sílabo en EVA"})
                        except Exception as ex:
                            transaction.set_rollback(True)
                            return JsonResponse({"isSuccess": False, "message": u"Error al actualizar el sílabo en EVA: %s" % ex.__str__()})

                elif action == 'actualizar_profesor_eva':
                    from moodle.functions import crear_actualizar_docente_curso
                    with transaction.atomic():
                        try:
                            try:
                                eMateria = Materia.objects.get(pk=request.GET.get('id', 0))
                            except ObjectDoesNotExist:
                                raise NameError(u"Materia no encontrada")
                            crear_actualizar_docente_curso(eMateria)
                            return JsonResponse({"isSuccess": True, "message": "Se actualizo correctamente profesor(es) en EVA"})
                        except Exception as ex:
                            transaction.set_rollback(True)
                            return JsonResponse({"isSuccess": False, "message": u"Error al actualizar profesor(es) en EVA: %s" % ex.__str__()})

                elif action == 'actualizar_estudiante_eva':
                    from moodle.functions import crear_actualizar_estudiante_curso
                    with transaction.atomic():
                        try:
                            try:
                                eMateria = Materia.objects.get(pk=request.GET.get('id', 0))
                            except ObjectDoesNotExist:
                                raise NameError(u"Materia no encontrada")
                            crear_actualizar_estudiante_curso(eMateria)
                            return JsonResponse({"isSuccess": True, "message": "Se actualizo correctamente estudiante(s) en EVA"})
                        except Exception as ex:
                            transaction.set_rollback(True)
                            return JsonResponse({"isSuccess": False, "message": u"Error al actualizar estudiante(s) en EVA: %s" % ex.__str__()})

                elif action == 'crear_curso_eva_masivo':
                    from moodle.tasks.migrar import CreacionMasiva
                    try:
                        try:
                            eNivel = Nivel.objects.get(pk=request.GET.get('id', 0))
                        except ObjectDoesNotExist:
                            raise NameError(u"Nivel no encontrado")
                        eConfig = eNivel.eva
                        if not eConfig:
                            raise NameError(u"No existe configurado EVA para el nivel")
                        if not eConfig.has_web_service_data():
                            raise NameError(u"No existe configurado EVA para migrar datos: Complete dato: URL, Prefijo, Token, Roles, Categoria")
                        if eConfig.type_connection == eConfig.TypesConnections.NINGUNA:
                            raise NameError(u"No se encuentra configurada la conexión a EVA")
                        CreacionMasiva(request, eNivel).start()
                        return JsonResponse({"isSuccess": True, "message": "Se esta ejecutando proceso masivamente en EVA"})
                    except Exception as ex:
                        return JsonResponse({"isSuccess": False, "message": u"Error al ejecutar proceso masivo en EVA: %s" % ex.__str__()})

                elif action == 'listarPersonaInFirma':
                    try:
                        # Obtener parámetros de la solicitud
                        tipo = request.GET.get('tipo')
                        if not tipo:
                            raise NameError("No se encontró el tipo a filtrar")

                        id_materia = request.GET.get('id', 0)
                        try:
                            eMateria = Materia.objects.get(pk=id_materia)
                        except Materia.DoesNotExist:
                            raise NameError("No se encontró la materia")
                        ePersonas = Persona.objects.none()

                        # Filtrar según el tipo
                        if int(tipo) == 1:
                            # Filtrar docentes de la materia
                            custom_filter = Q(id__in=ProfesorMateria.objects.values_list('profesor__persona__id', flat=True).filter(materia=eMateria, profesor__activo=True))
                            ePersonas = Persona.objects.filter(custom_filter).order_by('apellido1', 'apellido2')
                        elif int(tipo) == 2:
                            # Filtrar profesores que no son docentes de la materia
                            ids_exclude = ProfesorMateria.objects.values_list('profesor__persona__id', flat=True).filter(materia=eMateria, profesor__activo=True)
                            custom_filter = Q(id__in=Profesor.objects.values_list('persona__id', flat=True).filter(activo=True).exclude(id__in=ids_exclude))
                            ePersonas = Persona.objects.filter(custom_filter).order_by('apellido1', 'apellido2')
                        elif int(tipo) == 3:
                            # Filtrar administrativos excluyendo docentes y grupos específicos
                            eProfesorMaterias = ProfesorMateria.objects.values_list('profesor__persona__id', flat=True).filter(materia=eMateria, profesor__activo=True)
                            eProfesores = Profesor.objects.values_list('persona__id', flat=True).filter(activo=True)
                            gruposexcluidos = [ALUMNOS_GROUP_ID]
                            ePersonas = Persona.objects.exclude(Q(usuario__groups__id__in=gruposexcluidos) | Q(id__in=eProfesorMaterias) | Q(id__in=eProfesores)).order_by('apellido1', 'apellido2')
                        # Preparar los resultados
                        results = [{'id': ePersona.id, 'name': ePersona.nombre_completo_inverso()} for ePersona in ePersonas]
                        return JsonResponse({"isSuccess": True, "message": f"Datos de persona", "results": results})
                    except Exception as ex:
                        return JsonResponse({"isSuccess": False, "message": f"Error al cargar los datos: {str(ex)}", "results": []})

                elif action == 'loadViewFirma':
                    try:
                        id = request.GET.get('id', 0)
                        try:
                            eMateria = Materia.objects.get(pk=id)
                        except ObjectDoesNotExist:
                            eMateria = None
                            raise NameError(u"Materia no encontrada")
                        eNivel = eMateria.nivel
                        data['title'] = 'Configurar responsables de firma del acta de calificaciones'
                        data['eMateria'] = eMateria
                        return render(request ,"niveles/firmas/view.html" ,  data)
                    except Exception as ex:
                        return HttpResponseRedirect(f"{request.path}{eMateria == 0 : '':'?action=materias&id={eMateria.nivel_id}'}")

                elif action == 'loadFormFirma':
                    from firmaec.models import FirmaActaCalificacion
                    from firmaec.forms import FirmaActaCalificacionForm
                    try:
                        id = request.GET.get('id', 0)
                        idm = request.GET.get('idm', 0)
                        try:
                            eMateria = Materia.objects.get(pk=idm)
                        except ObjectDoesNotExist:
                            raise NameError(u"No se encontro materia valida")
                        try:
                            eFirmaActaCalificacion = FirmaActaCalificacion.objects.get(pk=id)
                        except ObjectDoesNotExist:
                            eFirmaActaCalificacion = None
                        f = FirmaActaCalificacionForm()
                        if eFirmaActaCalificacion:
                            f.edit(eMateria, eFirmaActaCalificacion.tipo)
                            f.initial = model_to_dict(eFirmaActaCalificacion)
                        data['eFirmaActaCalificacion'] = eFirmaActaCalificacion
                        data['eMateria'] = eMateria
                        data['form'] = f
                        data['frmName'] = "frmFirmaActaCalificacion"
                        data['id'] = id
                        template = get_template("niveles/firmas/form.html")
                        return JsonResponse(
                            {"isSuccess": True, "message": f"Se obtuvo el formulario correctamente",
                             "html": template.render(data)})
                    except Exception as ex:
                        return JsonResponse({"isSuccess": False, "message": f"Error al construir el formulario. {ex.__str__()}"})

                return HttpResponseRedirect("/niveles")

            else:
                if CENTRO_EXTERNO==True:
                    nivel = Nivel.objects.filter()[:1].get()
                    return HttpResponseRedirect("/niveles?action=materias&id="+str(nivel.id))

                else:
                    if MODELO_EVALUACION==EVALUACION_TES:
                        # Mostrar panel TES
                        data['periodo'] = Periodo.objects.get(pk=request.session['periodo'].id)
                        data['coordinaciones'] = Coordinacion.objects.filter(carrera__grupocoordinadorcarrera__group__in=request.user.groups.all()).distinct()
                        data['niveles'] = Nivel.objects.filter(periodo=data['periodo'], nivellibrecoordinacion__coordinacion__in=data['coordinaciones']).order_by('paralelo')
                        return render(request ,"niveles/libres/nivelesbs.html" ,  data)
                    else:
                        periodo = Periodo.objects.get(pk=request.session['periodo'].id)
                        sedes = Sede.objects.filter(solobodega=False)
                        carreras = Carrera.objects.filter(grupocoordinadorcarrera__group__in=request.user.groups.all()).distinct().exclude(activo=False).order_by('nombre').order_by('nombre')
                        niveles = Nivel.objects.filter(periodo=data['periodo'],carrera__in=carreras).order_by('paralelo')
                        data['periodo'] = periodo
                        data['sedes'] = sedes
                        # data['carreras'] = Carrera.objects.filter(grupocoordinadorcarrera__group__in=request.user.groups.all()).distinct().order_by('nombre').order_by('nombre')
                        data['carreras'] = carreras
                        data['select_carreras'] = carreras
                        data['niveles'] = niveles
                        data['form_tutor'] = TutorForm2
                        data['user']=request.user

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
                                data['carreras'] = None
                                print('NO EXISTE NIVEL EN ESTE PERIODO')
                                data['msj']='EL NIVEL '+nivel[:1].get().paralelo+' SE ENCUENTRA EN EL PERIODO: '+nivel[:1].get().periodo.nombre

                        return render(request ,"niveles/nivelesbs.html" ,  data)


    except Exception as ex:
        print('ERROR'+str(ex))
        return HttpResponseRedirect('/niveles')

def mail_correoeliminaasigancion(contenido,asunto,email,materia,profesor,user,profesormateria,observacion):
        hoy = datetime.now().today()
        send_html_mail(str(asunto),"emails/correoeliminauto.html", {'fecha': hoy,"user":user,'contenido': contenido, 'asunto': asunto,'persona':profesor.persona,'materia':materia,'profesormateria':profesormateria,'observacion':observacion},email.split(","))