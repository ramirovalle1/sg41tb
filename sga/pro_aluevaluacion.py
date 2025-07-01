# -*- coding: latin-1 -*-
from datetime import datetime, timedelta
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render
from decorators import secure_module
from settings import VALIDAR_ENTRADA_SISTEMA_CON_DEUDA,ASIGNATURA_PRACTICA_CONDUCCION,MATERIA_PRACTICA_CONDUCCION
from sga.commonviews import addUserData
from sga.models import Profesor, EvaluacionProfesor, IndicadorAmbitoInstrumentoEvaluacion, DatoInstrumentoEvaluacion, Inscripcion,ProfesorMateria,Materia,HistoricoNotasPractica,Asignatura,CalificacionEvaluacion

@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    if request.method=='POST':
        try:
            inscripcion = Inscripcion.objects.get(pk=request.POST['id'])
            # if 'p2' in request.POST:
            #     profesor = Profesor.objects.get(pk=request.POST['p2'])
            # else:
            profesor = Profesor.objects.get(pk=request.POST['p'])

            persona = inscripcion.persona

            periodo = request.session['periodo']
            proceso = periodo.proceso_evaluativo()
            instrumento = proceso.instrumento_alumno()

            evaluacion = EvaluacionProfesor(proceso=proceso,instrumento=instrumento,profesor=profesor,fecha=datetime.now(), persona=persona)
            evaluacion.save()

            for x, y in request.POST.iteritems():
                if len(x)>5 and x[:5]=='valor':
                    indicador = IndicadorAmbitoInstrumentoEvaluacion.objects.get(pk=x[5:])
                    dato = DatoInstrumentoEvaluacion(evaluacion=evaluacion, indicador=indicador, valor=int(y), observaciones=request.POST['obs'+x[5:]])
                    dato.save()
            return HttpResponseRedirect("/pro_aluevaluacion")
        except Exception as ex:
            return HttpResponseRedirect("/")

    else:
        data = {'title': 'Evaluacion del Docente por Alumno'}
        addUserData(request,data)
        periodo = data['periodo']

        if 'action' in request.GET:
            action = request.GET['action']
            if action=='evaluar':
                try:
                    inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                    profesor = Profesor.objects.get(pk=request.GET['p'])
                    materia = Materia.objects.get(pk=request.GET['materia'])

                    proceso = periodo.proceso_evaluativo()
                    instrumento = proceso.instrumento_alumno()
                    ambitos = instrumento.ambitoinstrumentoevaluacion_set.all()
                    # if ProfesorMateria.objects.filter(materia=materia, profesor_aux=profesor.id).exists():
                    #     prof=ProfesorMateria.objects.filter(materia=materia, profesor_aux=profesor.id)[:1].get()
                    #     data['profesor2'] = prof.profesor
                    if 'p2' in request.GET:
                        data['profesor2'] = Profesor.objects.get(pk=request.GET['p2'])

                    data['proceso'] = proceso
                    data['inscripcion'] = inscripcion
                    data['persona'] = inscripcion.persona
                    data['profesor'] = profesor
                    data['ambitos'] = ambitos
                    data['periodo'] = periodo
                    data['fecha'] = datetime.now()
                    data['calificacion'] = CalificacionEvaluacion.objects.all().order_by('id')
                    if EvaluacionProfesor.objects.filter(profesor=profesor, persona=data['persona']).exists():
                        eval = EvaluacionProfesor.objects.filter(profesor=profesor, persona=data['persona'])[:1].get()
                        eval.delete()
                    data['evaluacion'] = None
                except Exception as ex:
                    return HttpResponseRedirect("/")

            elif action=='conseval':
                inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                profesor = Profesor.objects.get(pk=request.GET['p'])
                if 'p2' in request.GET:
                    data['profesor2'] = Profesor.objects.get(pk=request.GET['p2'])
                proceso = periodo.proceso_evaluativo()
                instrumento = proceso.instrumento_alumno()
                ambitos = instrumento.ambitoinstrumentoevaluacion_set.all()

                data['proceso'] = proceso
                data['inscripcion'] = inscripcion
                data['persona'] = inscripcion.persona
                data['profesor'] = profesor
                data['ambitos'] = ambitos
                data['periodo'] = periodo
                data['fecha'] = datetime.now()
                data['calificacion'] = CalificacionEvaluacion.objects.all().order_by('id')
                if EvaluacionProfesor.objects.filter(profesor=profesor, persona=data['persona']).exists():
                    data['evaluacion']  = EvaluacionProfesor.objects.filter(profesor=profesor, persona=data['persona'])[:1].get()
                else:
                    data['evaluacion'] = None

            return render(request ,"pro_aluevaluacion/evaluacion.html" ,  data)
        else:
            periodo = request.session['periodo']
            proceso = periodo.proceso_evaluativo()
            instrumento = proceso.instrumento_alumno

            if not proceso.proceso_activo():
                return HttpResponseRedirect("/?info=Aun no esta activo el proceso de Evaluacion de Docentes")

            if not Inscripcion.objects.filter(persona=data['persona']).exists():
                return HttpResponseRedirect("/?info=Este modulo es para evaluacion de alumnos a docentes")
            else:
                inscripcion = Inscripcion.objects.filter(persona=data['persona'])[:1].get()

                #Comprobar que no tenga deudas para que no pueda usar el sistema
                if VALIDAR_ENTRADA_SISTEMA_CON_DEUDA and inscripcion.tiene_deuda():
                    return HttpResponseRedirect("/")
                if inscripcion.matricula_periodo(periodo):
                    #     SE PERMITE REALIZAR LA EVALUACION VERIFICANDO QUE ESTE MATRICULADA NO IMPORTA SI EL NIVEL YA SE CERRRO 21oCT2020
                    # if inscripcion.matricula_set.filter(nivel__periodo=periodo,nivel__cerrado = False).exists():
                    matricula = inscripcion.matricula_periodo(periodo)
                    # matricula = inscripcion.matricula_set.filter(nivel__periodo=periodo,nivel__cerrado = False)[0]

                    hoy = datetime.today().date()
                    materiasAsignadas = matricula.materiaasignada_set.filter(materia__fin__lte=hoy)
                    if proceso.rangoactivacion:
                        materiasAsignadas = [x for x in materiasAsignadas if (x.materia.fin-timedelta(proceso.diasactivacion))<hoy]


                    data['matricula'] = matricula
                    data['materiasasignadas'] = materiasAsignadas
                    profesores = []
                    for m in materiasAsignadas:
                        for p in m.profesores2():
                            # if ProfesorMateria.objects.filter(materia=m.materia).exists():
                            #     if ProfesorMateria.objects.filter(materia=m.materia).profesor_auxiliar():
                            #        p=ProfesorMateria.objects.filter(materia=m.materia).profesor_auxiliar()[:1]
                            profesores.append(p)
                    if HistoricoNotasPractica.objects.filter(historico__inscripcion=inscripcion).exists():
                        prof = HistoricoNotasPractica.objects.filter(historico__inscripcion=inscripcion)[:1].get()
                        data['prof_pratica'] = Profesor.objects.get(pk=prof.responsable)
                        data['materia_prac'] = MATERIA_PRACTICA_CONDUCCION
                        data['eval'] = data['prof_pratica'].esta_evaluado_por(data['persona'], proceso,instrumento)
                        asig = Asignatura.objects.get(pk=ASIGNATURA_PRACTICA_CONDUCCION)
                        data['asi_pract']=asig

                    data['profesores'] = set(profesores)
                    data['evaluados'] = [(p, p.esta_evaluado_por(data['persona'], proceso,instrumento)) for p in data['profesores']]
                else:
                    data['matricula'] = ""

            return render(request ,"pro_aluevaluacion/profesoresbs.html" ,  data)

