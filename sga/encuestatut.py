import json
from django.contrib.admin.models import LogEntry, ADDITION, DELETION, CHANGE
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator


from datetime import datetime
from django.db import transaction
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
from decorators import secure_module
from sga.commonviews import ip_client_address, addUserData
from sga.forms import EncuestaTutorForm, IndicadorEncuestaForm
from sga.models import AmbitosTutor, IndicadoresEvaluacionTutor, PersonalConvenio


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
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action == 'addpregunta':
                e = EncuestaTutorForm(request.POST)
                if e.is_valid():
                    try:

                        if request.POST['idpregunta']=='':
                            idpregunta=0
                        else:
                             idpregunta=request.POST['idpregunta']
                        if AmbitosTutor.objects.filter(pk=idpregunta).exists():
                            edit=AmbitosTutor.objects.filter(pk=idpregunta)[:1].get()
                            edit.pregunta=e.cleaned_data['pregunta']
                            edit.orden=e.cleaned_data['orden']
                            mensaje = 'Edicion de Pregunta'
                            edit.save()
                            # Log de APLICAR DONACION
                            client_address = ip_client_address(request)
                            LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(edit).pk,
                            object_id       = edit.id,
                            object_repr     = force_str(edit),
                            action_flag     = CHANGE,
                            change_message  = mensaje+' (' + client_address + ')' )
                            return HttpResponseRedirect('/encuestatutores')
                        else:
                            encuesta=AmbitosTutor(pregunta=e.cleaned_data['pregunta'],orden=e.cleaned_data['orden'])
                            msj='Pregunta Guardada'
                            encuesta.save()
                            client_address = ip_client_address(request)
                            LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(encuesta).pk,
                                object_id       = encuesta.id,
                                object_repr     = force_str(encuesta),
                                action_flag     = ADDITION,
                                change_message  = msj + '(' + client_address + ')' )
                            return HttpResponseRedirect("/encuestatutores")

                    except Exception as e:
                        return HttpResponseRedirect("/encuestatutores?error="+str(e))
            elif action == 'eliminar_pregunta':
                result={}
                try:
                    encuesta =AmbitosTutor.objects.filter(pk=request.POST['idpregunta'])[:1].get()
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
            elif action == 'indicador':
                i = IndicadorEncuestaForm(request.POST)
                if i.is_valid():
                    try:
                        if request.POST['idindicador']=='':
                            idindicador=0
                        else:
                             idindicador=request.POST['idindicador']
                        if IndicadoresEvaluacionTutor.objects.filter(pk=idindicador).exists():
                            indicador=IndicadoresEvaluacionTutor.objects.filter(pk=idindicador)[:1].get()
                            indicador.nombre=i.cleaned_data['nombre']
                            mensaje = 'Edicion de Indicador'
                            indicador.save()

                            client_address = ip_client_address(request)
                            LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(indicador).pk,
                            object_id       = indicador.id,
                            object_repr     = force_str(indicador),
                            action_flag     = CHANGE,
                            change_message  = mensaje+' (' + client_address + ')' )
                            return HttpResponseRedirect('/encuestatutores?action=indicador')
                        else:
                            indicado=IndicadoresEvaluacionTutor(nombre=i.cleaned_data['nombre'])
                            msj='Indicador Guardado'
                            indicado.save()
                            client_address = ip_client_address(request)
                            LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(indicado).pk,
                                object_id       = indicado.id,
                                object_repr     = force_str(indicado),
                                action_flag     = ADDITION,
                                change_message  = msj + '(' + client_address + ')' )
                            return HttpResponseRedirect("/encuestatutores?action=indicador")
                    except Exception as e:
                        return HttpResponseRedirect("/encuestatutores?error="+str(e))
            elif action == 'eliminar_indicador':
                result={}
                try:
                    encuesta =IndicadoresEvaluacionTutor.objects.filter(pk=request.POST['idindicador'])[:1].get()
                    mensaje = 'Indicador Eliminado'
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

        else:
            data = {'title': 'Preguntas de Encuesta a tutores'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']

                if action == 'indicador':
                    data['title']= 'Indicadores de Evaluacion'
                    indicadores=IndicadoresEvaluacionTutor.objects.filter()
                    data['indicadorencuesta']=indicadores
                    data['formindicador']= IndicadorEncuestaForm()
                    return render(request ,"tutorencuesta/indicadores.html" ,  data)
                elif action == 'pregunta':
                    ambito=AmbitosTutor.objects.filter()
                    data['ambito']=ambito
                    return render(request ,"tutorencuesta/ambitoencuestatutor.html" ,  data)

                    # data['title']= 'Editar Medicamento'
                    # if 'error' in request.GET:
                    #     data['error']=request.GET['error']
                    # data['regismed']= RegistroMedicamento.objects.get(id=request.GET['id'])
                    # initial = model_to_dict(data['regismed'])
                    # form = RegistroMedicamentoForm(initial=initial)
                    # data['form']= form

                elif action == 'eliminar':
                    personal = PersonalConvenio.objects.get(id=request.GET['id'])
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(personal).pk,
                        object_id       = personal.id,
                        object_repr     = force_str(personal),
                        action_flag     = ADDITION,
                        change_message  = 'Eliminado Personal (' + client_address + ')' )
                    personal.delete()
                    return  HttpResponseRedirect("/conveniobox")

            else:
                search = None
                todos = None
                bandera = 0
                encuestatutor=None

                if 's' in request.GET:
                    search = request.GET['s']
                if 't' in request.GET:
                    todos = request.GET['t']
                if search:
                    try:
                        if int(search)> 0:
                            encuestatutor = AmbitosTutor.objects.filter(orden=search).order_by('orden')
                    except  Exception as e:
                        try:
                            encuestatutor = AmbitosTutor.objects.filter(pregunta__icontains=search).order_by('orden')

                        except Exception as e:
                            pass
                else:
                    encuestatutor = AmbitosTutor.objects.all().order_by('orden')

                paging = MiPaginador(encuestatutor, 30)
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
                data['formpregunta']= EncuestaTutorForm()

                data['search'] = search if search else ""
                data['todos'] = todos if todos else ""
                data['encuestatutor'] = page.object_list

                if 'error' in request.GET:
                    data['error']= request.GET['error']
                return render(request ,"tutorencuesta/encuesta.html" ,  data)
    except Exception as ex:
        return HttpResponseRedirect("/")