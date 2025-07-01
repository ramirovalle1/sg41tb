
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
from sga.models import UsuarioConvenio, TipoMedicamento, DetalleRegistroMedicamento, BajaMedicamento, RecetaVisitaBox, Sede, Persona, TrasladoMedicamento,DetalleVisitasBox,PersonalConvenio, ConvenioBox, AmbitoEncuestaTutor, AmbitosTutor, IndicadoresEvaluacionTutor, TutorEncuesta, Carrera, EncuentasCarrera, Inscripcion, TutorCongreso, NivelTutor, EncuestaInscripcion, EncuestaAmbitoIndicador
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
            if action == 'addindicadores':
                result = {}
                try:
                    if IndicadoresEvaluacionTutor.objects.filter(pk=request.POST['idselector']).exists():
                        indicador=IndicadoresEvaluacionTutor.objects.filter(pk=request.POST['idselector'])[:1].get()

                        if EncuestaAmbitoIndicador.objects.filter(pk=request.POST['idencuestaambito']).exists():
                            encuestaindicador=EncuestaAmbitoIndicador.objects.filter(pk=request.POST['idencuestaambito'])[:1].get()
                            encuestaindicador.indicador=indicador
                            encuestaindicador.save()

                            result['result']  = "ok"
                            return HttpResponse(json.dumps(result), content_type="application/json")
                except Exception as e:
                    result['result']  = str(e)
                    return HttpResponse(json.dumps(result), content_type="application/json")
            if action=='finalizaencuesta':
                result={}
                try:
                    if EncuestaInscripcion.objects.filter(pk=request.POST['idencuestains']).exists():
                        encuestainscripcion=EncuestaInscripcion.objects.filter(pk=request.POST['idencuestains'])[:1].get()
                        if not encuestainscripcion.puede_finalizar_encuesta():
                            encuestainscripcion.finalizado=True
                            encuestainscripcion.save()
                            client_address = ip_client_address(request)
                            LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(encuestainscripcion).pk,
                                object_id       = encuestainscripcion.id,
                                object_repr     = force_str(encuestainscripcion),
                                action_flag     = ADDITION,
                                change_message  =  '(' + client_address + ')' )
                            result['result']  = "ok"
                            return HttpResponse(json.dumps(result), content_type="application/json")
                        else:
                            result['result']  = "error"
                            return HttpResponse(json.dumps(result), content_type="application/json")

                except Exception as e:
                    result['result']  = str(e)
                    return HttpResponse(json.dumps(result), content_type="application/json")

        else:
            data = {'title': 'Encuesta'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']

            else:
                try:
                    niveltutor = None
                    encuesta = None
                    ambitoencuesta = 0
                    indicador=None
                    encuestainscripcion=None
                    indicadorambito=None
                    inscripcion=Inscripcion.objects.filter(persona__usuario=request.user)[:1].get()
                    if inscripcion.matriculado():
                        nivel = inscripcion.matricula().nivel
                        if NivelTutor.objects.filter(nivel=nivel).exists():
                            niveltutor=NivelTutor.objects.filter(nivel=nivel)[:1].get()
                        else:
                            return HttpResponseRedirect("/?info=No existe tutor para ese nivel")
                        if EncuentasCarrera.objects.filter(carrera=inscripcion.carrera,encuestatutor__estado=True).exists():
                            encuestacarrera=EncuentasCarrera.objects.filter(carrera=inscripcion.carrera,encuestatutor__estado=True)[:1].get()
                            encuesta=encuestacarrera.encuestatutor
                            ambitoencuesta=AmbitoEncuestaTutor.objects.filter(encuestatutor=encuesta)
                            indicador=IndicadoresEvaluacionTutor.objects.filter(estado=True)
                            if not EncuestaInscripcion.objects.filter(encuesta=encuesta,inscripcion=inscripcion,tutor=niveltutor,estado=True).exists():
                                encuestainscripcion=EncuestaInscripcion(encuesta=encuesta,inscripcion=inscripcion, tutor=niveltutor, fecha=datetime.now(), estado=True)
                                encuestainscripcion.save()
                            else:

                                encuestainscripcion=EncuestaInscripcion.objects.filter(encuesta=encuesta,inscripcion=inscripcion,tutor=niveltutor,estado=True)[:1].get()
                            if not encuestainscripcion.finalizado:
                                for ambito in ambitoencuesta:
                                    if not EncuestaAmbitoIndicador.objects.filter(encuestainscripcion=encuestainscripcion,ambito=ambito.ambitotutor).exists():

                                            encuestaambitoindicador=EncuestaAmbitoIndicador(encuestainscripcion=encuestainscripcion,ambito=ambito.ambitotutor)
                                            encuestaambitoindicador.save()
                            indicadorambito=EncuestaAmbitoIndicador.objects.filter(encuestainscripcion=encuestainscripcion).order_by('ambito__pregunta')
                        else:
                            return HttpResponseRedirect("/?info=No existe encuesta para esa carrera")

                        data['inscripcion']=inscripcion
                        data['niveltutor']=niveltutor
                        data['encuesta']=encuesta
                        data['ambitoencuesta']=ambitoencuesta
                        data['indicador']=indicador
                        data['encuestainscripcion']=encuestainscripcion
                        data['encuestaambitoindicador']=indicadorambito

                        if 'error' in request.GET:
                            data['error']= request.GET['error']
                        return render(request ,"tutorencuesta/encuestainscripcion.html" ,  data)
                    else:
                        return HttpResponseRedirect("/?info=UD. AUN NO SE ENCUENTRA MATRICULADO")
                except Exception as e:
                    print(e)
                    return HttpResponseRedirect("/encuestainscripcion")
    except Exception as ex:
        return HttpResponseRedirect("/encuestainscripcion")
