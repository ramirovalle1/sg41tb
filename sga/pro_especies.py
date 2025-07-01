import json
from django.contrib.admin.models import ADDITION, LogEntry
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_str
from settings import ESPECIE_CAMBIO_PROGRAMACION, EMAIL_ACTIVE, DIAS_ESPECIE, ESPECIE_RETIRO_MATRICULA, \
     ESPECIE_REINGRESO, ID_TIPO_ESPECIE_REG_NOTA,ESPECIE_ASENTAMIENTO_NOTA,ESPECIE_EXAMEN,ESPECIE_RECUPERACION, ESPECIES_JUSTIFICACION_FALTAS,ESPECIES_ASENTAMIENTO_NOTAS
from sga.controlespecies import mail_correoalumnoespecie_finaliza
from sga.models import RubroEspecieValorada,MateriaAsignada, Rubro, Grupo, Nivel, Reporte, PagoNivel, TIPOS_PAGO_NIVEL, AsistenciaLeccion, SolicitudEstudiante, Profesor, LeccionGrupo, AusenciaJustificada, EvaluacionITB, elimina_tildes, GestionTramite, Persona
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.core.paginator import Paginator
from sga.commonviews import addUserData, ip_client_address
from django.template import RequestContext
from sga.forms import ControlEspeciesForm,ControlEspeciesSecretariaForm, ControlCambioProgramacionForm, RubrosCambioProgramacionForm, RubroNivelCambioProgramacionForm, RetiradoMatriculaForm, SeguimientoEspecieForm, RespuestaEspeciePracticasForm
from datetime import datetime
import sys
from decorators import secure_module
from django.db.models.query_utils import Q
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
@secure_module
@transaction.atomic()

def view(request):

    if request.method=='POST':
        action = request.POST['action']

        if action == 'registro':
            f = ControlEspeciesForm(request.POST,request.FILES)
            rubroespecie = RubroEspecieValorada.objects.get(pk=request.POST['id'])
            if f.is_valid():
                if 'codigoe' in f.cleaned_data:
                    rubroespecie.codigoe=f.cleaned_data['codigoe'].upper()
                rubroespecie.observaciones=f.cleaned_data['observaciones'].upper()
                rubroespecie.aplicada= True
                rubroespecie.habilita= False
                rubroespecie.fecha=datetime.now().date()
                rubroespecie.usuario=request.user
                rubroespecie.destinatario=f.cleaned_data['destinatario'].upper()


                if request.POST['reporte_id']:
                    certificado = Reporte.objects.filter(pk=request.POST['reporte_id'])[:1].get()
                    rubroespecie.certificado=certificado

                if request.POST['materia']:
                    rubroespecie.materia_id=request.POST['materia']
                rubroespecie.save()

                if 'archivo' in request.FILES:
                    rubroespecie.archivo=request.FILES['archivo']
                    rubroespecie.save()

                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(rubroespecie).pk,
                    object_id       = rubroespecie.id,
                    object_repr     = force_str(rubroespecie),
                    action_flag     = ADDITION,
                    change_message  = 'Ingreso de Especie (' + client_address + ')'+ rubroespecie.tipoespecie.nombre +rubroespecie.rubro.inscripcion.persona.nombre_completo_inverso())

                if 'op' in  request.POST:
                    if request.POST['op'] == 'sol':
                        return HttpResponseRedirect("/solicitudonline?tiposol=3&s="+rubroespecie.rubro.inscripcion.persona.nombre_completo_inverso())
                if not rubroespecie.tipoespecie.id in (4,15,20,29,31):
                    return HttpResponseRedirect("/controlespecies")
                else:
                    if request.POST['op'] == 'sol':
                        return HttpResponseRedirect("/controlespecies?action=impespecies&id="+str(rubroespecie.id))+"&op=sol"
                    else:
                        return HttpResponseRedirect("/controlespecies?action=impespecies&id="+str(rubroespecie.id))
            else:
                return HttpResponseRedirect("/controlespecies?action=registro&especie="+str(rubroespecie.id))

        elif action == 'finalizar':
            solicitud=SolicitudEstudiante.objects.filter(pk=request.POST['idsolici'])[:1].get()
            rubroespecie = solicitud.rubro.especie_valorada()
            if GestionTramite.objects.filter(tramite=rubroespecie).exists():
                gestion = GestionTramite.objects.filter(tramite=rubroespecie)[:1].get()
                gestion.respuesta = request.POST['observacion']
                gestion.finalizado=True
                gestion.fecharespuesta=datetime.now()
                gestion.save()
                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                user_id         = request.user.pk,
                content_type_id = ContentType.objects.get_for_model(rubroespecie).pk,
                object_id       = rubroespecie.id,
                object_repr     = force_str(rubroespecie),
                action_flag     = ADDITION,
                change_message  = 'Gestion ingresada por el docente (' + client_address + ')'+ gestion.profesor.nombre_completo_inverso())
                # emailestudiante=elimina_tildes(rubroespecie.rubro.inscripcion.persona.emailinst)+','+elimina_tildes(rubroespecie.rubro.inscripcion.persona.email)
                mail_ingreso_gestion(rubroespecie,gestion)
            return HttpResponseRedirect("/pro_especies")
        elif action == 'verporcentaje':
            data = {}
            try:
                solicitud = SolicitudEstudiante.objects.filter(id=request.POST['id'])[:1].get()
                if AsistenciaLeccion.objects.filter(id__in=json.loads(request.POST['asistencias'])).exists():
                    asis = AsistenciaLeccion.objects.filter(id__in=json.loads(request.POST['asistencias']))[:1].get()
                    if AsistenciaLeccion.objects.filter(leccion__clase__materia=asis.leccion.clase.materia, matricula=asis.matricula, asistio=True).exists():
                        total = AsistenciaLeccion.objects.filter(leccion__clase__materia=asis.leccion.clase.materia, matricula=asis.matricula).count()
                        aprobadas = AsistenciaLeccion.objects.filter(id__in=json.loads(request.POST['asistencias'])).count()
                        real = AsistenciaLeccion.objects.filter(leccion__clase__materia=asis.leccion.clase.materia, matricula=asis.matricula, asistio=True).count()
                        if not total:
                            por =  0
                        por= ((real +  aprobadas) * 100) / total
                        data['result'] = 'ok'
                        data['porcentaje'] = por

                        return HttpResponse(json.dumps(data), content_type="application/json")

                solicitud.rubro.especie_valorada().materia.porciento_asistencia()
                data['result'] = 'bad'
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as e:
                data['result'] = 'bad'
                data['error'] =str(e)
                return HttpResponse(json.dumps(data), content_type="application/json")


        elif action == 'verinasistencias':
            data = {}
            try:
                solicitud = SolicitudEstudiante.objects.filter(id=request.POST['id'])[:1].get()
                fechas =[]
                if solicitud.tipoe.id in ESPECIES_JUSTIFICACION_FALTAS:
                    if solicitud.materia.matricula:
                        matricula = solicitud.materia.matricula
                        lecciones =  LeccionGrupo.objects.filter(fecha__lte=solicitud.fecha,profesor=solicitud.profesor,materia__nivel__periodo__activo=True,lecciones__clase__materia=solicitud.materia.materia,lecciones__asistencialeccion__matricula=matricula,lecciones__asistencialeccion__asistio=False).order_by('fecha', 'horaentrada').values('lecciones__asistencialeccion')
                        for a in AsistenciaLeccion.objects.filter(id__in=lecciones).order_by('leccion__fecha','leccion__horaentrada')[:5]:
                            fechas.append({'id':a.id,'fecha':str(a.leccion.fecha)})
                            data['porcentaje'] = a.porciento_asistencia_actual()
                        data['result'] = 'ok'
                        data['cantidad'] = lecciones.count()
                        data['fechas'] = fechas

                        return HttpResponse(json.dumps(data), content_type="application/json")
                    data['result'] = 'NO TIENE MATRICULA EN ESA MATERIA'
                    return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as e:
                data['result'] = str(e)
                print(e)
                return HttpResponse(json.dumps(data), content_type="application/json")

        elif action == 'veraprobado':
            data = {}
            try:
                solicitud = SolicitudEstudiante.objects.filter(id=request.POST['id'])[:1].get()
                fechas =[]
                for a in  AusenciaJustificada.objects.filter(numeroe=str(solicitud.rubro.especie_valorada().serie), codigoe=str(solicitud.rubro.especie_valorada().serie),
                                              usuario=request.user,inscripcion=solicitud.rubro.inscripcion).order_by('asist__leccion__fecha'):
                    fechas.append({'id':a.id,'fecha':str(a.asist.leccion.fecha)})
                    data['result'] = 'ok'
                    data['cantidad'] = len(fechas)
                    data['fechas'] = fechas

                #
                # if solicitud.tipoe.id == ESPECIE_JUSTIFICA_FALTA_AU:
                #     if solicitud.inscripcion.matricula():
                #         matricula = solicitud.inscripcion.matricula()
                #         lecciones =  LeccionGrupo.objects.filter(fecha__lte=solicitud.fecha.date(),profesor=solicitud.profesor,materia__nivel__periodo__activo=True,lecciones__clase__materia=solicitud.materia.materia,lecciones__asistencialeccion__matricula=matricula,lecciones__asistencialeccion__aprobado=True).order_by('-fecha', '-horaentrada').values('lecciones__asistencialeccion')
                #         for a in AsistenciaLeccion.objects.filter(id__in=lecciones,aprobado=True).exclude(fechaaprobacion=None):
                #
                #             fechas.append({'id':a.id,'fecha':str(a.leccion.fecha)})

                return HttpResponse(json.dumps(data), content_type="application/json")
                    # data['result'] = 'bad'
                    # return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as e:
                data['result'] = 'bad'
                return HttpResponse(json.dumps(data), content_type="application/json")

        elif action == 'guardar':
            data = {}
            try:
                contador=0
                solicitud = SolicitudEstudiante.objects.filter(id=request.POST['id'])[:1].get()
                profesor =Profesor.objects.filter(persona__usuario=request.user)[:1].get()
                for a in AsistenciaLeccion.objects.filter(id__in=json.loads(request.POST['asistencias'])):
                    a.aprobado = True
                    a.fechaaprobacion = datetime.now()
                    a.save()
                    contador =contador + 1
                    aus = AusenciaJustificada(asist=a, numeroe=str(solicitud.rubro.especie_valorada().serie),
                                              codigoe=str(solicitud.rubro.especie_valorada().serie), fechae=solicitud.rubro.fecha,
                                              profesor=profesor, observaciones='JUSTIFICACION REALIZADA POR EL DOCENTE',
                                              fecha=datetime.now(), usuario=request.user,
                                              inscripcion=solicitud.rubro.inscripcion)
                    aus.save()
                    a.asistio = True
                    a.save()
                    for materiaasignada in a.matricula.materiaasignada_set.all():
                        materiaasignada.save()
                        e = EvaluacionITB.objects.filter(materiaasignada=materiaasignada)[:1].get()
                        e.actualiza_estado_nueva()
                solicitud.aprobado =True

                solicitud.save()
                # rubroe= RubroEspecieValorada.objects.filter(rubro=solicitud.rubro)[:1].get()
                # rubroe.autorizado = True
                # rubroe.obsautorizar = 'EL DOCENTE APROBO ' + str(contador)+  " INASISTENCIA "
                # rubroe.usrautoriza = request.user
                # rubroe.save()
                # rubroe.disponible= False
                # rubroe.fecha=datetime.now().date()
                # rubroe.usuario=request.user
                # rubroe.save()
                data['result'] = 'ok'
                return HttpResponse(json.dumps(data), content_type="application/json")

            except Exception as e:
                data['result'] = 'bad'
                return HttpResponse(json.dumps(data), content_type="application/json")

        elif action == 'autorizar':
            try:
                especie = RubroEspecieValorada.objects.filter(pk=request.POST['idespecie'])[:1].get()
                if request.POST['aprobado'] =='1':
                    especie.autorizado=True
                else:
                    especie.autorizado=False
                especie.obsautorizar = request.POST['respuesta']
                especie.usrautoriza = request.user
                especie.codigoe = especie.serie
                especie.aplicada= True
                especie.habilita= False
                especie.fecha = datetime.now().date()
                especie.usuario = request.user
                especie.fechafinaliza = datetime.now()

                if 'especie_id' in request.POST:
                    solicitud = SolicitudEstudiante.objects.get(pk=request.POST['especie_id'])
                    solicitud.aprobado = True
                    solicitud.save()
                especie.save()

                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(especie).pk,
                    object_id       = especie.id,
                    object_repr     = force_str(especie),
                    action_flag     = ADDITION,
                    change_message  = 'Ingreso de Especie ' )
                if EMAIL_ACTIVE:
                    emailestudiante=elimina_tildes(especie.rubro.inscripcion.persona.emailinst)+','+elimina_tildes(especie.rubro.inscripcion.persona.email)
                    mail_correoalumnoespecie_finaliza(especie,emailestudiante)
                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            except Exception as e:
                print(e)
                return HttpResponse(json.dumps({"result":str(e)}),content_type="application/json")

        elif action == 'asentar_alcance_notas':
            try:
                solicitud = SolicitudEstudiante.objects.get(pk=request.POST['id'])
                especie = RubroEspecieValorada.objects.filter(rubro=solicitud.rubro).order_by('-id')[:1].get()
                request.session['periodo'] = especie.materia.materia.nivel.periodo
                url = 'alcance_notas?id='+str(especie.materia.materia.id)
                if especie.materia.materia.nivel.cerrado:
                    url = 'alcance_notas?nivel-cerrado=1&id='+str(especie.materia.materia.id)
                return HttpResponse(json.dumps({"result":"ok", 'url':url}), content_type="application/json")
            except Exception as e:
                print(e)
                return HttpResponse(json.dumps({"result":'bad', 'mensaje':str(e)}), content_type="application/json")

        return HttpResponseRedirect("/controlespecies")

    else:
        data = {'title': 'Control de Especies'}
        addUserData(request,data)
        hoy = datetime.today().date()
        data['fechahoy'] = hoy
        if 'action' in request.GET:
            action = request.GET['action']
            if action == 'registro':
                data['title']= 'Control de Especies'
                rubroespecie = RubroEspecieValorada.objects.get(pk=request.GET['especie'])
                inscripcion = rubroespecie.rubro.inscripcion
                data['especie']=rubroespecie
                data['especieid']=rubroespecie.id
                data['inscripcion'] = inscripcion
                if 'op' in request.GET:
                    data['op']=request.GET['op']
                else:
                    data['op']='esp'
                if rubroespecie.tipoespecie.id == ESPECIE_CAMBIO_PROGRAMACION:
                    if 'nivel' in request.GET:
                        nivel = Nivel.objects.filter(pk=request.GET['nivel'])[:1].get()
                        form2 = RubroNivelCambioProgramacionForm()
                        form2.rubros_list(nivel)
                        data['form2'] = form2
                        data['pagonivel']= PagoNivel.objects.filter(nivel=nivel)
                        data['TIPOS_PAGO_NIVEL']=TIPOS_PAGO_NIVEL
                        data['form1'] = ControlCambioProgramacionForm(initial={'numeroe':rubroespecie.serie,'fechae':rubroespecie.rubro.fecha,'nivel':nivel})
                    else:
                        data['form1'] = ControlCambioProgramacionForm(initial={'numeroe':rubroespecie.serie,'fechae':rubroespecie.rubro.fecha})
                    rubros = Rubro.objects.filter(inscripcion= rubroespecie.rubro.inscripcion,cancelado=False).values('id')
                    form = RubrosCambioProgramacionForm()
                    form.rubros_list(rubros)
                    data['rubros']= Rubro.objects.filter(inscripcion= rubroespecie.rubro.inscripcion,cancelado=False)
                    data['form']= form
                    data['matricula']=inscripcion.matricula()
                    data['grupo']=Grupo.objects.all()

                    return render(request ,"controlespecies/cambio_programacion.html" ,  data)
                if rubroespecie.tipoespecie.id == ESPECIE_RETIRO_MATRICULA:
                    if rubroespecie.rubro.inscripcion.matriculado():
                        if  not rubroespecie.rubro.inscripcion.retirado():
                            data['title'] = 'Justificar Faltas'
                            matricula =rubroespecie.rubro.inscripcion.matricula()
                            if 'error' in request.GET:
                                data['error'] = request.GET['error']
                            data['matricula'] = matricula
                            data['form'] = RetiradoMatriculaForm(initial={'fecha': datetime.now().strftime("%d-%m-%Y"),'especie':rubroespecie.serie })
                            rubros = Rubro.objects.filter(inscripcion= matricula.inscripcion,cancelado=False).values('id')
                            form2 = RubrosCambioProgramacionForm()
                            form2.rubros_list(rubros)
                            data['form2']=form2
                            data['rubros']= Rubro.objects.filter(inscripcion= matricula.inscripcion,cancelado=False)
                        else:
                            return HttpResponseRedirect("/controlespecies?s="+str(rubroespecie.serie)+"&error=YA SE ENCUENTRA RETIRADO")
                        return render(request ,"matriculas/retiro_matricula.html" ,  data)
                    else:
                        return HttpResponseRedirect("/controlespecies?s="+str(rubroespecie.serie)+"&error=NO ESTA MATRICULADO")

                materiaasignada = MateriaAsignada.objects.filter(matricula=inscripcion.matricula()).values('id')

                form = ControlEspeciesForm(initial={'numeroe':rubroespecie.serie,'fechae':rubroespecie.rubro.fecha})
                data['form']= form

                data['mat']=MateriaAsignada.objects.filter(id__in=materiaasignada).order_by('materia__asignatura__nombre')

                data['asentamiento']=ESPECIE_ASENTAMIENTO_NOTA
                data['examen']=ESPECIE_EXAMEN
                data['recuperacion'] = ESPECIE_RECUPERACION

                return render(request ,"controlespecies/registrar.html" ,  data)
            # elif action == 'actualizar':
            #     c=0
            #     for g in GestionTramite.objects.filter():
            #         try:
            #             if g.tramite.es_online().profesor:
            #                 print(str(g.profesor) + "; " +str(g.tramite.es_online().profesor.persona )+ ";"+ str(g.tramite.serie))
            #                 g.profesor = g.tramite.es_online().profesor.persona
            #                 g.save()
            #                 c = c +1
            #         except Exception as e:
            #             print(e)
            #             print(g.tramite.serie)
            #             pass
            #     print(c)
            elif action == 'impespecies':
                rubroespecie = RubroEspecieValorada.objects.filter(pk=request.GET['id'])
                data['especie']=rubroespecie
                return render(request ,"controlespecies/especies.html" ,  data)

        else:
            try:
                search = None
                todos = None
                numero = None
                especie = None
                op=None
                profesor = Profesor.objects.get(persona=data['persona'])
                if 's' in request.GET:
                    search = request.GET['s']
                if 't' in request.GET:
                    todos = request.GET['t']
                if search:
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')
                    if len(ss)==1:
                        try:
                            if int(search):
                                numero = int(search)
                                especie = SolicitudEstudiante.objects.filter(Q(rubro__rubroespecievalorada__serie=numero)).order_by('-rubro__fecha','rubro__rubroespecievalorada__serie')
                        except:
                            especie = SolicitudEstudiante.objects.filter(Q (rubro__inscripcion__persona__apellido1__icontains=search)).order_by('-rubro__fecha','rubro__rubroespecievalorada__serie')
                    else:
                        especie = SolicitudEstudiante.objects.filter(Q(rubro__inscripcion__persona__apellido1__icontains=ss[0]) & Q (rubro__inscripcion__persona__apellido2__icontains=ss[1])).order_by('-rubro__fecha','rubro__inscripcion__persona__apellido1','rubro__inscripcion__persona__apellido2','rubro__inscripcion__persona__nombres')

                else:
                    especie = SolicitudEstudiante.objects.filter().order_by('-rubro__fecha','rubro__inscripcion__persona__apellido1')

                    especie = especie.filter(Q(profesor=profesor,rubro__rubroespecievalorada__aplicada=False)|Q(rubro__rubroespecievalorada__aplicada=False,rubro__rubroespecievalorada__usrasig=profesor.persona.usuario))

                # OCastillo 18-11-2021 filtrar por solicitudes finalizadaa
                if 'cerra' in request.GET:
                    especie = SolicitudEstudiante.objects.filter().order_by('-rubro__fecha','rubro__inscripcion__persona__apellido1')
                    especie = especie.filter(Q(profesor=profesor,rubro__rubroespecievalorada__aplicada=True)|Q(rubro__rubroespecievalorada__aplicada=True,rubro__rubroespecievalorada__usrasig=profesor.persona.usuario)).order_by('-rubro__rubroespecievalorada__serie','-rubro__rubroespecievalorada__fecha')
                    data['cerrado'] = 'cerra'


                # especie = especie.filter(Q(profesor=profesor)|Q(materia__materia__profesormateria__profesor=profesor))
                # if 'op' in request.GET:
                #     if request.GET['op'] == 'buscar':
                #         asistentefilter =AsistenteDepartamento.objects.get(pk=request.GET['asist'])
                #         data['asistentefilter'] = asistentefilter
                #         especie = especie.filter(usrasig=asistentefilter.persona.usuario).order_by('-rubro__fecha','serie')
                # if AsistenteDepartamento.objects.filter(persona__usuario=request.user).exists():
                #     especie = especie.filter(usrasig=request.user).order_by('-rubro__fecha','serie')

                # else:
                #     data['asistentes'] = AsistenteDepartamento.objects.all()

                paging = MiPaginador(especie, 30)
                p = 1
                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                    page = paging.page(p)
                except:
                    page = paging.page(p)

                if 'error' in request.GET:
                    data['error'] = request.GET['error']

                data['paging'] = paging
                data['rangospaging'] = paging.rangos_paginado(p)
                data['page'] = page
                data['search'] = search if search else ""
                data['todos'] = todos if todos else ""
                data['especie'] = page.object_list
                data['form']= ControlEspeciesSecretariaForm()
                data['DIAS_ESPECIE']=DIAS_ESPECIE
                data['ESPECIES_JUSTIFICACION_FALTAS'] = ESPECIES_JUSTIFICACION_FALTAS
                data['ESPECIES_ASENTAMIENTO_NOTAS'] = ESPECIES_ASENTAMIENTO_NOTAS
                data['ESPECIE_CAMBIO_PROGRAMACION']=ESPECIE_CAMBIO_PROGRAMACION
                data['ESPECIE_REINGRESO']=ESPECIE_REINGRESO
                data['ID_TIPO_ESPECIE_REG_NOTA']=ID_TIPO_ESPECIE_REG_NOTA
                data['ESPECIE_ASENTAMIENTO']=ESPECIE_ASENTAMIENTO_NOTA
                data['respform'] = RespuestaEspeciePracticasForm()
                data['segform'] = SeguimientoEspecieForm()
                data['usuario'] = request.user
                if 'op' in request.GET:
                    op =request.GET['op']
                data['op'] = op if op else ""

                return render(request ,"controlespecies/pro_especies.html" ,  data)
            except Exception as ex:
                print(ex)
                return HttpResponseRedirect("/?error="+str(ex))


def mail_ingreso_gestion(especie,gestion):
        hoy = datetime.now().today()
        persona= Persona.objects.filter(usuario=especie.usrasig)[:1].get()
        email= persona.emailinst
        asunto = "Gestion de  tramite #" +str(especie.serie)
        contenido = "Tramite " + elimina_tildes(especie.tipoespecie.nombre)
        send_html_mail(str(asunto),"emails/gestiondocente.html", {'fecha': hoy,'contenido': contenido, 'asunto': asunto,'especie':especie,'gestion':gestion,'persona':persona},email.split(","))
