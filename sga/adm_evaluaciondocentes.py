import json
import datetime
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.template.context import RequestContext
from django.db.models.expressions import F
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.utils.encoding import force_str
from decorators import secure_module
from sga.commonviews import addUserData, ip_client_address
from sga.models import Periodo, AmbitoEvaluacion, AmbitoInstrumentoEvaluacion, IndicadorEvaluacion, IndicadorAmbitoInstrumentoEvaluacion, Clase, CoordinadorCarrera, Profesor, EvaluacionProfesor, Matricula, MateriaAsignada, DatoInstrumentoEvaluacion, DIAS_EVALUACION

def convertDate(s):
    d = int(s[0:2])
    m = int(s[3:5])
    y = int(s[6:])
    return datetime.date(y,m,d)

@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    if request.method=='POST':

        return HttpResponseRedirect("/adm_evaluaciondocentes")
    else:
        data = {'title': 'Proceso de Evaluacion de Docentes'}
        addUserData(request,data)
        data['proceso'] = data['periodo'].proceso_evaluativo()

        if 'action' in request.GET:
            action = request.GET['action']
            if action=="setup":

                activado = request.GET['activado']=="1"
                rangoactivacion = request.GET['rangoactivacion']=="1"
                diasactivacion = request.GET['diasactivacion']

                proceso = data['proceso']
                proceso.activado = activado
                proceso.rangoactivacion = rangoactivacion
                proceso.diasactivacion = diasactivacion
                proceso.save()
                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(proceso).pk,
                    object_id       = proceso.id,
                    object_repr     = force_str(proceso),
                    action_flag     = CHANGE,
                    change_message  =  "Cambia de Estado de Proceso  " + str(proceso.activado) +  ' ( ' + client_address + ')' )


                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            elif action=='addambito':
                inst = int(request.GET['inst'])
                if inst==1:
                    instr = data['proceso'].instrumento_alumno()
                elif inst==2:
                    instr = data['proceso'].instrumento_profesor()
                elif inst==3:
                    instr = data['proceso'].instrumento_coordinador()
                na = AmbitoInstrumentoEvaluacion(instrumento=instr, ambito=AmbitoEvaluacion.objects.get(pk=request.GET['amb']))
                na.save()
                return HttpResponseRedirect('/adm_evaluaciondocentes?action='+str(inst))
            elif action=='addambitonuevo':
                inst = int(request.GET['inst'])
                if inst==1:
                    instr = data['proceso'].instrumento_alumno()
                elif inst==2:
                    instr = data['proceso'].instrumento_profesor()
                elif inst==3:
                    instr = data['proceso'].instrumento_coordinador()
                ambito = AmbitoEvaluacion(nombre=request.GET['nombre'])
                ambito.save()
                na = AmbitoInstrumentoEvaluacion(instrumento=instr, ambito=ambito)
                na.save()
                return HttpResponseRedirect('/adm_evaluaciondocentes?action='+str(inst))
            elif action=='delambito':
                ambito = AmbitoInstrumentoEvaluacion.objects.get(pk=request.GET['id'])
                ambito.delete()
                return HttpResponseRedirect("/adm_evaluaciondocentes?action="+request.GET['inst'])
            elif action=='addindicador':
                ambito = AmbitoInstrumentoEvaluacion.objects.get(pk=request.GET['ambito'])
                indicador = IndicadorAmbitoInstrumentoEvaluacion(ambitoinstrumento=ambito, indicador=IndicadorEvaluacion.objects.get(pk=request.GET['indicador']))
                indicador.save()
                return HttpResponseRedirect("/adm_evaluaciondocentes?action="+request.GET['inst'])
            elif action=='addindicadornuevo':
                ambito = AmbitoInstrumentoEvaluacion.objects.get(pk=request.GET['ambito'])
                indicadornuevo = IndicadorEvaluacion(nombre=request.GET['nombre'])
                indicadornuevo.save()
                indicador = IndicadorAmbitoInstrumentoEvaluacion(ambitoinstrumento=ambito, indicador=indicadornuevo)
                indicador.save()
                return HttpResponseRedirect("/adm_evaluaciondocentes?action="+request.GET['inst'])
            elif action=='delindicador':
                indicador = IndicadorAmbitoInstrumentoEvaluacion.objects.get(pk=request.GET['id'])
                indicador.delete()
                return HttpResponseRedirect("/adm_evaluaciondocentes?action="+request.GET['inst'])
            elif action=='1':
                # Instrumento 1 (Alumnos)
                data['instrumento'] = data['proceso'].instrumento_alumno()
                data['tipo'] = "Evaluacion del Docente por Alumnos"
                data['ambitoslibres'] = AmbitoEvaluacion.objects.exclude(id__in=[x.ambito.id for x in data['instrumento'].ambitoinstrumentoevaluacion_set.all()])
                data['indicadores'] = IndicadorEvaluacion.objects.all()
                data['instrumentonumero'] = "1"
                return render(request ,"adm_evaluaciondocentes/editarbs.html" ,  data)
            elif action=='ver1':
                # Instrumento 1 (Alumnos)
                data['instrumento'] = data['proceso'].instrumento_alumno()
                data['tipo'] = "Ver Evaluacion del Docente por Alumnos"
                data['ambitoslibres'] = AmbitoEvaluacion.objects.exclude(id__in=[x.ambito.id for x in data['instrumento'].ambitoinstrumentoevaluacion_set.all()])
                data['indicadores'] = IndicadorEvaluacion.objects.all()
                data['instrumentonumero'] = "1"
                return render(request ,"adm_evaluaciondocentes/verinstrumentobs.html" ,  data)
            elif action=='2':
                # Instrumento 2 (Docentes)
                data['instrumento'] = data['proceso'].instrumento_profesor()
                data['tipo'] = "Autoevaluacion del Docente"
                data['ambitoslibres'] = AmbitoEvaluacion.objects.exclude(id__in=[x.ambito.id for x in data['instrumento'].ambitoinstrumentoevaluacion_set.all()])
                data['indicadores'] = IndicadorEvaluacion.objects.all()
                data['instrumentonumero'] = "2"
                return render(request ,"adm_evaluaciondocentes/editarbs.html" ,  data)
            elif action=='ver2':
                # Instrumento 2 (Docentes)
                data['instrumento'] = data['proceso'].instrumento_profesor()
                data['tipo'] = "Autoevaluacion del Docente"
                data['ambitoslibres'] = AmbitoEvaluacion.objects.exclude(id__in=[x.ambito.id for x in data['instrumento'].ambitoinstrumentoevaluacion_set.all()])
                data['indicadores'] = IndicadorEvaluacion.objects.all()
                data['instrumentonumero'] = "2"
                return render(request ,"adm_evaluaciondocentes/verinstrumentobs.html" ,  data)
            elif action=='3':
                # Instrumento 3 (Coordinador)
                data['instrumento'] = data['proceso'].instrumento_coordinador()
                data['tipo'] = "Evaluacion del Docente por Coordinador"
                data['ambitoslibres'] = AmbitoEvaluacion.objects.exclude(id__in=[x.ambito.id for x in data['instrumento'].ambitoinstrumentoevaluacion_set.all()])
                data['indicadores'] = IndicadorEvaluacion.objects.all()
                data['instrumentonumero'] = "3"
                return render(request ,"adm_evaluaciondocentes/editarbs.html" ,  data)
            elif action=='ver3':
                # Instrumento 3 (Coordinador)
                data['instrumento'] = data['proceso'].instrumento_coordinador()
                data['tipo'] = "Evaluacion del Docente por Coordinador"
                data['ambitoslibres'] = AmbitoEvaluacion.objects.exclude(id__in=[x.ambito.id for x in data['instrumento'].ambitoinstrumentoevaluacion_set.all()])
                data['indicadores'] = IndicadorEvaluacion.objects.all()
                data['instrumentonumero'] = "3"
                return render(request ,"adm_evaluaciondocentes/verinstrumentobs.html" ,  data)
            elif action=='resumen':
                #Resumen de Evaluaciones de Docentes
                periodo = request.session['periodo']
                data['profesores'] = Profesor.objects.filter(clase__in=Clase.objects.filter(materia__nivel__periodo=periodo)).distinct()
                return render(request ,"adm_evaluaciondocentes/resumendocentes.html" ,  data)
            elif action=='verobserv':
                #Observaciones y Opiniones de Alumnos a Docentes
                if 'ret' in request.GET:
                    data['ret'] = request.GET['ret']
                data['profesor'] = Profesor.objects.get(pk=request.GET['id'])
                data['datos'] = DatoInstrumentoEvaluacion.objects.filter(evaluacion__in=EvaluacionProfesor.objects.filter(proceso=data['proceso'], profesor=data['profesor'], instrumento=data['proceso'].instrumento_alumno()), observaciones__gt='')
                return render(request ,"adm_evaluaciondocentes/observaciones.html" ,  data)

            return HttpResponseRedirect('/adm_evaluaciondocentes')

        else:
            # Calculo de Autoevaluaciones de Docentes
            lista_profesores = Profesor.objects.filter(clase__in=Clase.objects.filter(profesor__profesormateria__materia__nivel__periodo=data['periodo'])).distinct()
            total_profesores = float(lista_profesores.count())

            autoevaluados = EvaluacionProfesor.objects.filter(proceso=data['proceso'], profesor__persona=F('persona')).count()

            data['autoevaluados'] = autoevaluados
            data['totalprofesores']= total_profesores
            data['porcientoautoevaluados'] = (autoevaluados/total_profesores)*100 if total_profesores else 0

            # Calculo de Evaluaciones por Coordinadores
            periodo = data['periodo']

            coordinador_total = 0
            coordinador_eval = 0

            for coordinador in set([x.persona for x in CoordinadorCarrera.objects.filter(periodo=periodo)]):

                profesores = []
                for carrera in [x.carrera for x in CoordinadorCarrera.objects.filter(persona=coordinador, periodo=periodo)]:
                    profesores_carrera = Profesor.objects.filter(clase__in=Clase.objects.filter(profesor__profesormateria__materia__nivel__periodo=periodo,profesor__profesormateria__materia__nivel__carrera=carrera)).distinct()
                    for p in profesores_carrera:
                        if not p in profesores:
                            profesores.append(p)

                coordinador_total += len(profesores)
                coordinador_eval += EvaluacionProfesor.objects.filter(proceso=data['proceso'], profesor__in=profesores, persona=coordinador).count()

            data['evaluadosporcoordinadores'] = coordinador_eval
            data['totalprofesoresporcoordinadores']= coordinador_total
            data['porcientoevaluadosporcoordinadores'] = (coordinador_eval/float(coordinador_total))*100.0 if coordinador_total else 0

            # Calculo de Evaluaciones por Alumnos
            alumnos_total = MateriaAsignada.objects.filter(matricula__in=Matricula.objects.filter(nivel__periodo=periodo)).count()
            alumnos_eval = EvaluacionProfesor.objects.filter(persona__inscripcion__matricula__in=Matricula.objects.filter(nivel__periodo=periodo)).count()

            data['totalprofesoresporalumnos'] = alumnos_total
            data['evaluadosporalumnos'] = alumnos_eval
            data['rangosdiasevaluacion'] = DIAS_EVALUACION

            return render(request ,"adm_evaluaciondocentes/procesobs.html" ,  data)
