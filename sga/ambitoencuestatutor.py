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
from sga.models import  AmbitoEncuestaTutor, AmbitosTutor, IndicadoresEvaluacionTutor, TutorEncuesta
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.core.paginator import Paginator
from sga.commonviews import addUserData, ip_client_address
from django.template import RequestContext
from sga.forms import RegistroMedicamentoForm, PersonalConvenioForm, EncuestaTutorForm, IndicadorEncuestaForm, EncuestaAmbitosForm
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
            if action == 'addpregunta':
                result={}
                try:
                    if AmbitosTutor.objects.filter(pk=request.POST['idambito']).exists():
                        ambito=AmbitosTutor.objects.filter(pk=request.POST['idambito'])[:1].get()
                        if TutorEncuesta.objects.filter(pk=request.POST['idencuesta']).exists():
                            encuesta=TutorEncuesta.objects.filter(pk=request.POST['idencuesta'])[:1].get()
                            if not AmbitoEncuestaTutor.objects.filter(ambitotutor=ambito, encuestatutor=encuesta).exists():
                                encuestaambito=AmbitoEncuestaTutor(ambitotutor=ambito, encuestatutor=encuesta )

                                msj='Registro Guardado'
                                encuestaambito.save()
                                client_address = ip_client_address(request)
                                LogEntry.objects.log_action(
                                    user_id         = request.user.pk,
                                    content_type_id = ContentType.objects.get_for_model(encuestaambito).pk,
                                    object_id       = encuestaambito.id,
                                    object_repr     = force_str(encuestaambito),
                                    action_flag     = ADDITION,
                                    change_message  = msj + '(' + client_address + ')' )
                                result['result']  = "ok"
                                return HttpResponse(json.dumps(result), content_type="application/json")
                except Exception as e:
                    result['result']  = str(e)
                    return HttpResponse(json.dumps(result), content_type="application/json")
            elif action == 'eliminar_encuesta':
                result={}
                try:
                    if AmbitosTutor.objects.filter(pk=request.POST['idambito']).exists():
                        ambito=AmbitosTutor.objects.filter(pk=request.POST['idambito'])[:1].get()
                        if TutorEncuesta.objects.filter(pk=request.POST['idencuesta']).exists():
                            encuesta=TutorEncuesta.objects.filter(pk=request.POST['idencuesta'])[:1].get()
                            if AmbitoEncuestaTutor.objects.filter(ambitotutor=ambito, encuestatutor=encuesta).exists():
                                encuesta =AmbitoEncuestaTutor.objects.filter(ambitotutor=ambito,encuestatutor=encuesta)[:1].get()
                                mensaje = 'Eliminada Pregunta'
                                client_address = ip_client_address(request)
                                LogEntry.objects.log_action(
                                    user_id         = request.user.pk,
                                    content_type_id = ContentType.objects.get_for_model(encuesta).pk,
                                    object_id       = encuesta.id,
                                    object_repr     = force_str(encuesta),
                                    action_flag     = DELETION,
                                    change_message  = mensaje+' (' + client_address + ')' )
                                encuesta.delete()
                                result['result']  = "ok"
                                return HttpResponse(json.dumps(result), content_type="application/json")
                except Exception as e:
                    result['result']  = str(e)
                    return HttpResponse(json.dumps(result), content_type="application/json")
            if action== 'addpreguntaencuesta':
                e= EncuestaTutorForm(request.POST)
                if e.is_valid():
                    try:
                        if TutorEncuesta.objects.filter(pk=request.POST['idencuestatutor']).exists():
                            encuesta=TutorEncuesta.objects.filter(pk=request.POST['idencuestatutor'])[:1].get()
                            ambito=AmbitosTutor(pregunta=e.cleaned_data['pregunta'], orden=e.cleaned_data['orden'])
                            ambito.save()
                            encuestaambito=AmbitoEncuestaTutor(ambitotutor=ambito,encuestatutor=encuesta)
                            msj='Pregunta Guardada'
                            encuestaambito.save()
                            client_address = ip_client_address(request)
                            LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(encuesta).pk,
                                object_id       = encuesta.id,
                                object_repr     = force_str(encuesta),
                                action_flag     = ADDITION,
                                change_message  = msj + '(' + client_address + ')' )
                            return HttpResponseRedirect("/encuestaevaluacion?action=pregunta&id="+str(encuesta.id))
                    except Exception as e:
                        return HttpResponseRedirect("/ambitoencuestatutor?error="+str(e))
        else:
            data = {'title': 'Preguntas de Encuesta a tutores'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']

            else:
                search = None
                todos = None
                bandera = 0
                ambito=None
                encuesta=TutorEncuesta.objects.filter(pk=request.GET['idencuesta'])



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
                            ambito = AmbitosTutor.objects.filter(pregunta__icontains=search).order_by('orden')
                        else:
                            ambito = AmbitosTutor.objects.all().order_by('orden')
                    except Exception as e:
                        pass
                else:
                    ambito = AmbitosTutor.objects.all().order_by('orden')

                paging = MiPaginador(ambito, 30)
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


                data['search'] = search if search else ""
                data['todos'] = todos if todos else ""
                data['ambito'] = page.object_list
                data['encuesta']=encuesta

                # data['ambitotutor']=AmbitoEncuestaTutor.objects.filter()
                if 'error' in request.GET:
                    data['error']= request.GET['error']
                return render(request ,"tutorencuesta/ambitoencuestatutor.html" ,  data)
    except Exception as ex:
        return HttpResponseRedirect("/")