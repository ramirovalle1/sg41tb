from datetime import datetime, timedelta
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Avg
from django.db.models.query_utils import Q
from django.forms.models import model_to_dict
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.utils.encoding import force_str
from decorators import secure_module
from settings import DEFAULT_PASSWORD, PROFESORES_GROUP_ID, ALUMNOS_GROUP_ID, UTILIZA_GRUPOS_ALUMNOS
from sga.commonviews import addUserData
from sga.forms import PersonaForm, InscripcionForm, RecordAcademicoForm, HistoricoRecordAcademicoForm, GraduadoForm, SeguimientoGraduadoForm, GraduadoDatosForm, EncuestaForm
from sga.models import Profesor, Persona, Inscripcion, RecordAcademico, DocumentosDeInscripcion, HistoricoRecordAcademico, Graduado, SeguimientoGraduado, Asignatura, Encuesta, InstrumentoEvaluacion, AmbitoEvaluacion, IndicadorEvaluacion, AmbitoInstrumentoEvaluacion, IndicadorAmbitoInstrumentoEvaluacion, RespuestaEncuesta, DatoRespuestaEncuesta


@login_required(redirect_field_name='ret', login_url='/login')
#@secure_module
def view(request):
    if request.method=='POST':
        action = request.POST['action']
        if action=='add':
            f = EncuestaForm(request.POST)
            if f.is_valid():
                en = Encuesta(nombre=f.cleaned_data['nombre'],
                              fechainicio=f.cleaned_data['fechainicio'],
                              fechafin=f.cleaned_data['fechafin'],
                              activa=f.cleaned_data['activa'],
                              obligatoria=f.cleaned_data['obligatoria'],
                              instrumento=None)
                en.save()
                for g in f.cleaned_data['grupos']:
                    en.grupos.add(g)
            else:
                return HttpResponseRedirect("/encuestas?action=add")
        elif action=='edit':
            en = Encuesta.objects.get(pk=request.POST['id'])
            f = EncuestaForm(request.POST)
            if f.is_valid():
                en.nombre = f.cleaned_data['nombre']
                en.fechainicio = f.cleaned_data['fechainicio']
                en.fechafin = f.cleaned_data['fechafin']
                en.activa = f.cleaned_data['activa']
                en.obligatoria = f.cleaned_data['obligatoria']
                en.save()
                for g in en.grupos.all():
                    en.grupos.remove(g)
                for g in f.cleaned_data['grupos']:
                    en.grupos.add(g)

        elif action=='responder':
            encuesta = Encuesta.objects.get(pk=request.POST['id'])
            persona = request.session['persona']
            respuesta = RespuestaEncuesta(encuesta=encuesta,fecha=datetime.now(), persona=persona)
            respuesta.save()
            for x, y in request.POST.iteritems():
                if len(x)>5 and x[:5]=='valor':
                    indicador = IndicadorAmbitoInstrumentoEvaluacion.objects.get(pk=x[5:])
                    dato = DatoRespuestaEncuesta(respuesta=respuesta, indicador=indicador, valor=int(y), observaciones=request.POST['obs'+x[5:]])
                    dato.save()
            return HttpResponseRedirect("/")

        return HttpResponseRedirect("/encuestas")
    else:
        data = {'title': 'Gestion de Encuestas'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='add':
                data['title'] = 'Crear nueva Encuesta'
                data['form'] = EncuestaForm(initial={'fechainicio': datetime.today(), 'fechafin': datetime.today()+timedelta(15)})
                return render(request ,"encuestas/adicionarbs.html" ,  data)
            elif action=='edit':
                data['title'] = 'Editar Encuesta'
                encuesta = Encuesta.objects.get(pk=request.GET['id'])
                initial = model_to_dict(encuesta)
                data['encuesta'] = encuesta
                data['form'] = EncuestaForm(initial=initial)
                return render(request ,"encuestas/editbs.html" ,  data)
            elif action=='del':
                data['title'] = 'Borrar graduacion'
                data['graduado'] = Graduado.objects.get(pk=request.GET['id'])
                return render(request ,"graduados/borrarbs.html" ,  data)
            elif action=='editinst':
                if 'id' in request.GET:
                    en = Encuesta.objects.get(pk=request.GET['id'])
                    if not en.instrumento:
                        ins = InstrumentoEvaluacion(nombre=en.nombre)
                        ins.save()
                        en.instrumento = ins
                        en.save()
                    data['instrumento'] = en.instrumento
                elif 'in' in request.GET:
                    ins = InstrumentoEvaluacion.objects.get(pk=request.GET['in'])
                    data['instrumento'] = ins
                data['tipo'] = "Encuesta %s"%(data['instrumento'].nombre)
                data['ambitoslibres'] = AmbitoEvaluacion.objects.filter(encuesta=True).exclude(id__in=[x.ambito.id for x in data['instrumento'].ambitoinstrumentoevaluacion_set.all()])
                data['indicadores'] = IndicadorEvaluacion.objects.filter(encuesta=True)
                data['instrumentonumero'] = "1"
                return render(request ,"encuestas/editarinstbs.html" ,  data)
            elif action=='addambito':
                inst = InstrumentoEvaluacion.objects.get(pk=request.GET['inst'])
                na = AmbitoInstrumentoEvaluacion(instrumento=inst, ambito=AmbitoEvaluacion.objects.get(pk=request.GET['amb']))
                na.save()
                return HttpResponseRedirect('/encuestas?action=editinst&in='+str(inst.id))
            elif action=='addambitonuevo':
                inst = InstrumentoEvaluacion.objects.get(pk=request.GET['inst'])
                ambito = AmbitoEvaluacion(nombre=request.GET['nombre'], encuesta=True)
                ambito.save()
                na = AmbitoInstrumentoEvaluacion(instrumento=inst, ambito=ambito)
                na.save()
                return HttpResponseRedirect('/encuestas?action=editinst&in='+str(inst.id))
            elif action=='delambito':
                ambito = AmbitoInstrumentoEvaluacion.objects.get(pk=request.GET['id'])
                ambito.delete()
                inst = InstrumentoEvaluacion.objects.get(pk=request.GET['inst'])
                return HttpResponseRedirect('/encuestas?action=editinst&in='+str(inst.id))
            elif action=='addindicador':
                ambito = AmbitoInstrumentoEvaluacion.objects.get(pk=request.GET['ambito'])
                indicador = IndicadorAmbitoInstrumentoEvaluacion(ambitoinstrumento=ambito, indicador=IndicadorEvaluacion.objects.get(pk=request.GET['indicador']))
                indicador.save()
                inst = InstrumentoEvaluacion.objects.get(pk=request.GET['inst'])
                return HttpResponseRedirect('/encuestas?action=editinst&in='+str(inst.id))
            elif action=='addindicadornuevo':
                ambito = AmbitoInstrumentoEvaluacion.objects.get(pk=request.GET['ambito'])
                indicadornuevo = IndicadorEvaluacion(nombre=request.GET['nombre'], encuesta=True)
                indicadornuevo.save()
                indicador = IndicadorAmbitoInstrumentoEvaluacion(ambitoinstrumento=ambito, indicador=indicadornuevo)
                indicador.save()
                inst = InstrumentoEvaluacion.objects.get(pk=request.GET['inst'])
                return HttpResponseRedirect('/encuestas?action=editinst&in='+str(inst.id))
            elif action=='delindicador':
                indicador = IndicadorAmbitoInstrumentoEvaluacion.objects.get(pk=request.GET['id'])
                indicador.delete()
                inst = InstrumentoEvaluacion.objects.get(pk=request.GET['inst'])
                return HttpResponseRedirect('/encuestas?action=editinst&in='+str(inst.id))
            elif action=='responder':
                encuesta = Encuesta.objects.get(pk=request.GET['id'])
                instrumento = encuesta.instrumento
                ambitos = instrumento.ambitoinstrumentoevaluacion_set.all()
                data['encuesta'] = encuesta
                data['ambitos'] = ambitos
                data['fecha'] = datetime.now()
                if RespuestaEncuesta.objects.filter(encuesta=encuesta, persona=data['persona']).exists():
                    data['respuesta'] = RespuestaEncuesta.objects.filter(encuesta=encuesta, persona=data['persona'])[:1].get()
                else:
                    data['respuesta'] = None
                return render(request ,"encuestas/responder.html" ,  data)

            elif action=='piechartgeneral':
                data['title'] = 'Graficas Generales sobre Encuesta'
                encuesta = Encuesta.objects.get(pk=request.GET['id'])
                respuestasencuesta = encuesta.respuestaencuesta_set.all()

                ambitos_encuesta = encuesta.ambitos()
                data['total_excelente'] = sum([x.encuestaron_excelente() for x in ambitos_encuesta])
                data['total_muybien'] = sum([x.encuestaron_muybien() for x in ambitos_encuesta])
                data['total_bien'] = sum([x.encuestaron_bien() for x in ambitos_encuesta])
                data['total_regular'] = sum([x.encuestaron_regular() for x in ambitos_encuesta])
                data['total_mal'] = sum([x.encuestaron_mal() for x in ambitos_encuesta])

                data['hoy'] = datetime.today().date()
                data['encuesta'] = encuesta
                data['universo_a_encuestar'] = encuesta.universo_a_encuestar()
                data['no_encuestados'] = encuesta.no_encuestados()
                data['encuestados'] = encuesta.encuestados()
                data['ambitos'] = ambitos_encuesta

                return render(request ,"encuestas/piechartgeneral.html" ,  data)

            elif action=='piechartindicadores':
                data['title'] = 'Graficas sobre Indicadores'
                encuesta = Encuesta.objects.get(pk=request.GET['id'])

                data['indicadores'] = encuesta.indicadores()
                data['hoy'] = datetime.today().date()
                data['encuesta'] = encuesta

                return render(request ,"encuestas/piechartindicadores.html" ,  data)

            return HttpResponseRedirect("/encuestas")
        else:
            search = None
            if 's' in request.GET:
                search = request.GET['s']
            encuestas = Encuesta.objects.all().order_by('-id')
            paging = Paginator(encuestas, 50)
            p=1
            try:
                if 'page' in request.GET:
                    p = int(request.GET['page'])
                page = paging.page(p)
            except:
                page = paging.page(1)
            data['paging'] = paging
            data['page'] = page
            data['search'] = search if search else ""
            data['encuestas'] = page.object_list
            return render(request ,"encuestas/encuestasbs.html" ,  data)
