
import json
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import Sum
from django.forms import model_to_dict
from django.utils.encoding import force_str
from decorators import secure_module
from settings import EMAIL_ACTIVE
from sga.models import UsuarioConvenio, TipoMedicamento, DetalleRegistroMedicamento, BajaMedicamento, RecetaVisitaBox, Sede, Persona, TrasladoMedicamento,DetalleVisitasBox,PersonalConvenio, ConvenioBox, AmbitoEncuestaTutor, AmbitosTutor, IndicadoresEvaluacionTutor, TutorEncuesta, Carrera, EncuentasCarrera, EncuestaInscripcion
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.core.paginator import Paginator
from sga.commonviews import addUserData, ip_client_address
from django.template import RequestContext
from sga.forms import RegistroMedicamentoForm, PersonalConvenioForm, EncuestaTutorForm, IndicadorEncuestaForm, CrearEncuestaForm, EncuestaAmbitosForm, CarreraEncuestaForm
from datetime import datetime

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
        if request.method=='POST':
            action = request.POST['action']
            if action == 'addencuesta':
                e = CrearEncuestaForm(request.POST)
                if e.is_valid():
                    try:
                        encuesta=TutorEncuesta(cabecera=e.cleaned_data['cabecera'],
                                               recomendaciones=e.cleaned_data['recomendaciones'],
                                               objetivos=e.cleaned_data['objetivos'],
                                               estado=e.cleaned_data['estado'],
                                               fechacreacion=datetime.now(),
                                                   usuario=request.user)
                        msj='Encuesta Guardada'
                        encuesta.save()
                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(encuesta).pk,
                            object_id       = encuesta.id,
                            object_repr     = force_str(encuesta),
                            action_flag     = ADDITION,
                            change_message  = msj + '(' + client_address + ')' )
                        return HttpResponseRedirect("/encuestaevaluacion")

                    except Exception as e:
                        return HttpResponseRedirect("/encuestaevaluacion?error="+str(e))
            elif action == 'addcarrera':
                result = {}
                try:
                    if TutorEncuesta.objects.filter(pk=request.POST['idencuesta']).exists():
                        encuesta=TutorEncuesta.objects.filter(pk=request.POST['idencuesta'])[:1].get()
                        if Carrera.objects.filter(pk=request.POST['idcarrera']).exists():
                            carrera= Carrera.objects.filter(pk=request.POST['idcarrera'])[:1].get()
                            if not EncuentasCarrera.objects.filter(carrera=carrera,encuestatutor=encuesta).exists():
                                encuestacarrera=EncuentasCarrera(carrera=carrera,encuestatutor=encuesta)
                                encuestacarrera.save()

                                result['result']  = "ok"
                                return HttpResponse(json.dumps(result), content_type="application/json")
                except Exception as e:
                    result['result']  = str(e)
                    return HttpResponse(json.dumps(result), content_type="application/json")

            elif action == 'eliminacarrera':
                result = {}
                try:
                    encuestacarrera =EncuentasCarrera.objects.filter(pk=request.POST['encuestacarrera'])
                    encuestacarrera.delete()
                    result['result']  = "ok"
                    return HttpResponse(json.dumps(result), content_type="application/json")
                except Exception as e:
                    result['result']  = str(e)
                    return HttpResponse(json.dumps(result), content_type="application/json")

            elif action == 'eliminar_datosencuesta':
                result={}
                try:
                    eliminar =TutorEncuesta.objects.filter(pk=request.POST['ideliminar'])[:1].get()
                    mensaje = 'Eliminar datos'
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(eliminar).pk,
                        object_id       = eliminar.id,
                        object_repr     = force_str(eliminar),
                        action_flag     = DELETION,
                        change_message  = mensaje+' (' + client_address + ')' )
                    eliminar.delete()
                    result['result']  = "ok"
                    return HttpResponse(json.dumps(result), content_type="application/json")
                except Exception as e:
                    result['result']  = str(e)
                    return HttpResponse(json.dumps(result), content_type="application/json")
            if action == 'activacion':
                try:
                    encuesta = TutorEncuesta.objects.get(pk=request.POST['id'])
                    if EncuestaInscripcion.objects.filter(finalizado=False,encuesta=encuesta).exists():
                        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
                    else:
                        if encuesta.estado:
                            encuesta.estado = False
                        else:
                            encuesta.estado = True
                        encuesta.save()
                        return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")

                except:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
            if action=='editarencuesta':
                c= CrearEncuestaForm(request.POST)
                if c.is_valid():
                    try:
                        if request.POST['idencuesta']=='':
                            idencuesta=0
                        else:
                             idencuesta=request.POST['idencuesta']
                        if TutorEncuesta.objects.filter(pk=idencuesta).exists():
                            edit = TutorEncuesta.objects.get(pk=idencuesta)
                            edit.cabecera=c.cleaned_data['cabecera']
                            edit.objetivos = c.cleaned_data['objetivos']
                            edit.recomendaciones = c.cleaned_data['recomendaciones']
                            edit.estado = c.cleaned_data['estado']

                            mensaje = 'Edicion de Encuesta'
                            edit.save()

                            client_address = ip_client_address(request)
                            LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(edit).pk,
                            object_id       = edit.id,
                            object_repr     = force_str(edit),
                            action_flag     = CHANGE,
                            change_message  = mensaje+' (' + client_address + ')' )
                            return HttpResponseRedirect('/encuestaevaluacion')
                    except Exception as e:
                        return HttpResponseRedirect("/encuestaevaluacion?error="+str(e))
        else:
            data = {'title': 'Preguntas de Encuesta a tutores'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']
                if action == 'pregunta':
                    data['title']= 'Preguntas de evaluacion'
                    ambito=AmbitosTutor.objects.filter().order_by('orden')

                    if TutorEncuesta.objects.filter(pk=request.GET['id']).exists():
                        encuesta=TutorEncuesta.objects.filter(pk=request.GET['id'])[:1].get()
                        data['encuesta']=encuesta
                        if encuesta.puedeeliminarse():
                            ambitot = AmbitoEncuestaTutor.objects.filter(encuestatutor=encuesta).values('ambitotutor')
                            ambito=AmbitosTutor.objects.filter(id__in=ambitot).order_by('orden')

                        data['formamb']= EncuestaAmbitosForm()
                        data['formpregunta']= EncuestaTutorForm()
                    data['ambito']=ambito
                    return render(request ,"tutorencuesta/ambitoencuestatutor.html" ,  data)

                elif action == 'vercarrera':
                    try:
                        encuesta=TutorEncuesta.objects.filter(pk=request.GET['encuesta'])[:1].get()
                        encuestacarrera = EncuentasCarrera.objects.filter(encuestatutor=encuesta)
                        data['encuestacarrera']=encuestacarrera
                        data['encuesta']=encuesta

                        # data['carrera'] = EspecieGrupo.objects.filter(tipoe=especie)
                        return render(request ,"tutorencuesta/carrera.html" ,  data)
                        # # else:
                        #     return render(request ,"inscripciones/panel.html" ,  data)
                    except:
                        return render(request ,"tutorencuesta/carrera.html" ,  data)
                elif action == 'encuestados':
                    try:
                        data['title']= 'Estudiantes encuestados'
                        encuesta=TutorEncuesta.objects.filter(pk=request.GET['id'])[:1].get()
                        encuestados = EncuestaInscripcion.objects.filter(encuesta=encuesta,)
                        data['encuestados']=encuestados
                        data['encuesta']=encuesta

                        return render(request ,"tutorencuesta/encuestados.html" ,  data)

                    except:
                        return render(request ,"tutorencuesta/encuestados.html" ,  data)
            else:
                search = None
                todos = None
                bandera = 0
                tutor=None

                if 's' in request.GET:
                    search = request.GET['s']
                if 't' in request.GET:
                    todos = request.GET['t']
                if search:
                    try:
                        ss = search.split(' ')
                        while '' in ss:
                            ss.remove('')
                        if len(ss)==1:
                            tutor = TutorEncuesta.objects.filter(objetivos__icontains=search).order_by('fechacreacion')
                        else:
                            tutor = TutorEncuesta.objects.all().order_by('fechacreacion')
                    except Exception as e:
                        pass
                else:
                    tutor = TutorEncuesta.objects.all().order_by('fechacreacion')

                paging = MiPaginador(tutor, 30)
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
                data['form']= CrearEncuestaForm()


                data['search'] = search if search else ""
                data['todos'] = todos if todos else ""
                data['tutor'] = page.object_list
                data['formcarrera']=CarreraEncuestaForm()


                if 'error' in request.GET:
                    data['error']= request.GET['error']
                return render(request ,"tutorencuesta/encuestatutor.html" ,  data)
    except Exception as ex:
        return HttpResponseRedirect("/")