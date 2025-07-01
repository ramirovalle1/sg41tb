from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.shortcuts import render
from decorators import secure_module
from settings import ARCHIVO_TIPO_SYLLABUS, ARCHIVO_TIPO_DEBERES, MATERIA_PRACTICA_CONDUCCION
from sga.commonviews import addUserData
from sga.forms import ArchivoSyllabusForm, ArchivoDeberForm
from sga.models import Profesor, LeccionGrupo, Materia, Archivo, TipoArchivo, Periodo, AmbitoEvaluacion, AmbitoInstrumentoEvaluacion, EvaluacionProfesor, ProcesoEvaluativo, IndicadorAmbitoInstrumentoEvaluacion, DatoInstrumentoEvaluacion, HistoricoNotasPractica, CalificacionEvaluacion


@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    data = {'title': 'Autoevaluacion del Docente'}
    addUserData(request,data)
    periodo = data['periodo']
    proceso = periodo.proceso_evaluativo()

    if request.method=='POST':
        instrumento = proceso.instrumento_profesor()
        persona = request.session['persona']
        profesor = Profesor.objects.get(persona=persona)
        evaluacion = EvaluacionProfesor(proceso=proceso,instrumento=instrumento,profesor=profesor,fecha=datetime.now(), persona=persona)
        evaluacion.save()
        for x, y in request.POST.iteritems():
            if len(x)>5 and x[:5]=='valor':
                indicador = IndicadorAmbitoInstrumentoEvaluacion.objects.get(pk=x[5:])
                dato = DatoInstrumentoEvaluacion(evaluacion=evaluacion, indicador=indicador, valor=int(y), observaciones=request.POST['obs'+x[5:]])
                dato.save()
        return HttpResponseRedirect("/pro_autoevaluacion")
    else:
        if not proceso.proceso_activo():
            return HttpResponseRedirect("/?info=Aun no esta activo el proceso de Autoevaluacion")

        data = {'title': 'Autoevaluacion del Docente'}
        addUserData(request,data)
        instrumento = proceso.instrumento_profesor()
        profesor = Profesor.objects.get(persona=data['persona'])
        ambitos = instrumento.ambitoinstrumentoevaluacion_set.all()
        materias = profesor.materias_imparte()
        carrera = []
        if materias:
            for materia in materias:
                carrera.append(materia.nivel.carrera)
        if  HistoricoNotasPractica.objects.filter(responsable=profesor.id).exists():
            data['materia2'] = Materia.objects.get(pk=MATERIA_PRACTICA_CONDUCCION)
        data['proceso'] = proceso
        data['carreras'] = set(carrera)
        data['profesor'] = profesor
        data['ambitos'] = ambitos
        data['fecha'] = datetime.now()
        data['calificacion'] = CalificacionEvaluacion.objects.all().order_by('id')
        if EvaluacionProfesor.objects.filter(proceso__periodo=periodo, instrumento=instrumento, profesor=profesor, persona=data['persona']).exists():
            data['evaluacion'] = EvaluacionProfesor.objects.filter(proceso__periodo=periodo, instrumento=instrumento, profesor=profesor, persona=data['persona'])[:1].get()
        else :
            data['evaluacion'] = None
        return render(request ,"pro_autoevaluacion/autoevaluacion.html" ,  data)
