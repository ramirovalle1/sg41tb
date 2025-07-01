from datetime import datetime
from sga.commonviews import addUserData
from sga.models import CoordinadorCarrera,Persona,HistoricoNotasPractica,Profesor,CalificacionEvaluacion,Materia,EvaluacionProfesor, DatoInstrumentoEvaluacion
from django.http import HttpResponseRedirect
from django.shortcuts import render
from settings import MATERIA_PRACTICA_CONDUCCION
from django.db.models.query_utils import Q

def view(request):
    try:
        if request.method == 'POST':
            action = request.POST['action']

        else:
            data = {'title':'Lista de Coordinadores de Carreras'}
            addUserData(request,data)
            periodo = request.session['periodo']
            if 'action' in request.GET:
                action = request.GET['action']

                if action == "verevaluacion":
                    periodo = request.session['periodo']
                    proceso = periodo.proceso_evaluativo()
                    instrumento = proceso.instrumento_coordinador()

                    persona=data['persona']
                    if CoordinadorCarrera.objects.filter(persona__id=request.GET['id'], periodo=periodo).exists():
                        search = None
                        if 's' in request.GET:
                            search = request.GET['s']

                        coordinador_carrera = CoordinadorCarrera.objects.filter(persona__id=request.GET['id'],periodo=periodo)[:1].get()
                        profesores = coordinador_carrera.mis_profesoresconsult(periodo,search)
                        carreras = coordinador_carrera.mis_carreras(periodo)
                        data['cantidadprofesores'] = profesores.count()
                        data['search'] = search if search else ""
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

                    return render(request ,"consultaevaluacion/evaluaciones.html" ,  data)

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
                elif action == "verevaluacionprofe":
                    proceso = periodo.proceso_evaluativo()
                    instrumento = proceso.instrumento_profesor()
                    profesor = Profesor.objects.get(id=request.GET['id'])
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
                    data['coord'] = request.GET['coord']
                    data['calificacion'] = CalificacionEvaluacion.objects.all().order_by('id')
                    if EvaluacionProfesor.objects.filter(proceso__periodo=periodo, instrumento=instrumento, profesor=profesor).exists():
                        data['evaluacion'] = EvaluacionProfesor.objects.filter(proceso__periodo=periodo, instrumento=instrumento, profesor=profesor)[:1].get()
                    else :
                        return HttpResponseRedirect("/?info=No existe autoevaluacion")
                    return render(request ,"consultaevaluacion/evaluacionprofe.html" ,  data)
            else:
                periodo = request.session['periodo']
                search = None
                if 's' in request.GET:
                    search = request.GET['s']

                if search:
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')
                    if len(ss)==1:
                        coordinadores = CoordinadorCarrera.objects.filter(Q(persona__nombres__icontains=search) | Q(persona__apellido1__icontains=search) | Q(persona__apellido2__icontains=search) | Q(persona__cedula__icontains=search) | Q(persona__pasaporte__icontains=search)).order_by('persona__apellido1')
                    else:
                        coordinadores = CoordinadorCarrera.objects.filter(Q(persona__apellido1__icontains=ss[0]) & Q(persona__apellido2__icontains=ss[1])).order_by('persona__apellido1','persona__apellido2','persona__nombres')
                else:
                    coordinadores = CoordinadorCarrera.objects.filter(periodo=periodo)
                coordinadores = Persona.objects.filter(id__in=coordinadores.values('persona_id').distinct())
                data['coordinadores'] = coordinadores
                data['search'] = search if search else ""
                return render(request ,"consultaevaluacion/consultaevaluacion.html" ,  data)
    except Exception as ex:
        return HttpResponseRedirect("/?info=Error "+str(ex))


