from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render
from decorators import secure_module
from sga.commonviews import addUserData
from sga.models import Profesor, Materia, EvaluacionProfesor, IndicadorAmbitoInstrumentoEvaluacion, DatoInstrumentoEvaluacion, CoordinadorCarrera,HistoricoNotasPractica, CalificacionEvaluacion


@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    data = {'title': 'Evaluacion del Docente por Alumno'}
    addUserData(request,data)
    periodo = data['periodo']
    proceso = periodo.proceso_evaluativo()
    if request.method=='POST':
        coordinador = CoordinadorCarrera.objects.get(pk=request.POST['id'])
        profesor = Profesor.objects.get(pk=request.POST['p'])
        persona = coordinador.persona
        instrumento = proceso.instrumento_coordinador()
        evaluacion = EvaluacionProfesor(proceso=proceso,instrumento=instrumento,profesor=profesor,fecha=datetime.now(), persona=persona)
        evaluacion.save()
        for x, y in request.POST.iteritems():
            if len(x)>5 and x[:5]=='valor':
                indicador = IndicadorAmbitoInstrumentoEvaluacion.objects.get(pk=x[5:])
                dato = DatoInstrumentoEvaluacion(evaluacion=evaluacion, indicador=indicador, valor=int(y), observaciones=request.POST['obs'+x[5:]])
                dato.save()
        return HttpResponseRedirect("/pro_coordevaluacion")
    else:
        data = {'title': 'Evaluacion del Docente por Alumno'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='evaluar':
                periodo = request.session['periodo']
                coordinador = CoordinadorCarrera.objects.get(pk=request.GET['id'])
                profesor = Profesor.objects.get(pk=request.GET['p'])
                proceso = periodo.proceso_evaluativo()
                instrumento = proceso.instrumento_coordinador()
                ambitos = instrumento.ambitoinstrumentoevaluacion_set.all()
                if "consueval" in request.GET:
                    data["consueval"] = request.GET["consueval"]
                data['proceso'] = proceso
                data['coordinador'] = coordinador
                data['persona'] = coordinador.persona
                data['profesor'] = profesor
                data['ambitos'] = ambitos
                data['fecha'] = datetime.now()
                data['calificacion'] = CalificacionEvaluacion.objects.all().order_by('id')
                if EvaluacionProfesor.objects.filter(profesor=profesor, persona=coordinador.persona, instrumento=instrumento).exists():
                    data['evaluacion'] = EvaluacionProfesor.objects.filter(profesor=profesor, persona=coordinador.persona, instrumento=instrumento)[:1].get()
                else:
                    data['evaluacion'] = None

            elif action=='verobserv':
                #Observaciones y Opiniones de Alumnos a Docentes
                if 'ret' in request.GET:
                    data['ret'] = request.GET['ret']
                profesor = Profesor.objects.get(pk=request.GET['id'])
                periodo = request.session['periodo']
                proceso = periodo.proceso_evaluativo()
                if "consueval" in request.GET:
                    data["consueval"] = request.GET["consueval"]
                data['profesor'] = profesor
                data['calificacion'] = CalificacionEvaluacion.objects.all().order_by('id')
                data['datos'] = DatoInstrumentoEvaluacion.objects.filter(evaluacion__in=EvaluacionProfesor.objects.filter(proceso=proceso, profesor=profesor, instrumento=proceso.instrumento_alumno()), observaciones__gt='')
                return render(request ,"pro_coordevaluacion/observaciones.html" ,  data)

            return render(request ,"pro_coordevaluacion/evaluacion.html" ,  data)
        else:
            periodo = request.session['periodo']
            proceso = periodo.proceso_evaluativo()
            instrumento = proceso.instrumento_coordinador()
            if periodo.proceso_evaluativo().proceso_activo() is False:
                return HttpResponseRedirect("/?info=Aun no esta activo el proceso de Evaluacion de Docentes para este periodo")
            persona=data['persona']
            if CoordinadorCarrera.objects.filter(persona=persona, periodo=periodo).exists():
                coordinador_carrera = CoordinadorCarrera.objects.filter(persona=persona, periodo=periodo)[:1].get()
                profesores = coordinador_carrera.mis_profesores(periodo)
                carreras = coordinador_carrera.mis_carreras(periodo)
                if profesores:
                    data['cantidadprofesores'] = profesores.count()
                # data['cantidadprofesores']  = 0
            else:
                coordinador_carrera = None
                profesores = None
                carreras = None
                data['cantidadprofesores'] = 0
            if  HistoricoNotasPractica.objects.all().exclude(responsable=None).exists():
                prof_prac = HistoricoNotasPractica.objects.all().exclude(responsable=None).distinct('responsable').values(('responsable'))
                pro = Profesor.objects.filter(pk__in=prof_prac)
                data['profesores2'] = pro
            data['coordinador'] = coordinador_carrera
            data['carreras'] = carreras
            data['profesores'] = profesores
            data['proceso'] = proceso
            data['instrumento'] = instrumento
            data['calificacion'] = CalificacionEvaluacion.objects.all().order_by('id')
            return render(request ,"pro_coordevaluacion/profesoresbs.html" ,  data)
