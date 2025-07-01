from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render
from decorators import secure_module
from settings import EVALUACION_ITS, MODELO_EVALUACION, EVALUACION_IAVQ
from sga.commonviews import addUserData
from sga.forms import PeriodoEvaluacionesIAVQForm, PeriodoEvaluacionesITSForm
from sga.models import PeriodoEvaluacionesIAVQ, PeriodoEvaluacionesITS


@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    if request.method=='POST':
        action = request.POST['action']
        if action=='add':
            if MODELO_EVALUACION == EVALUACION_IAVQ:
                f = PeriodoEvaluacionesIAVQForm(request.POST)
            if MODELO_EVALUACION == EVALUACION_ITS:
                f = PeriodoEvaluacionesITSForm(request.POST)
            if f.is_valid():
                f.save()
            else:
                return HttpResponseRedirect("/fecha_evaluaciones?action=add")

        elif action=='edit':
            if MODELO_EVALUACION == EVALUACION_IAVQ:
                f = PeriodoEvaluacionesIAVQForm(request.POST, instance=PeriodoEvaluacionesIAVQ.objects.get(pk=request.POST['id']))
            if MODELO_EVALUACION == EVALUACION_ITS:
                f = PeriodoEvaluacionesITSForm(request.POST, instance=PeriodoEvaluacionesITS.objects.get(pk=request.POST['id']))
            if f.is_valid():
                f.save()
            else:
                return HttpResponseRedirect("/fecha_evaluaciones?action=edit&id="+str(request.POST['id']))

        return HttpResponseRedirect("/fecha_evaluaciones")
    else:
        data = {'title': 'Listado de Periodos Evaluativos'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='add':
                data['title'] = 'Crear Periodo de Evaluacion'
                if MODELO_EVALUACION == EVALUACION_IAVQ:
                    data['form'] = PeriodoEvaluacionesIAVQForm()
                if MODELO_EVALUACION == EVALUACION_ITS:
                    data['form'] = PeriodoEvaluacionesITSForm()
                return render(request ,"fecha_evaluaciones/adicionarbs.html" ,  data)

            elif action=='edit':
                data['title'] = 'Editar Periodo de Evaluacion'
                if MODELO_EVALUACION == EVALUACION_IAVQ:
                    data['periodoevaluaciones'] = PeriodoEvaluacionesIAVQ.objects.get(pk=request.GET['id'])
                    data['form'] = PeriodoEvaluacionesIAVQForm(instance=data['periodoevaluaciones'])
                if MODELO_EVALUACION == EVALUACION_ITS:
                    data['periodoevaluaciones'] = PeriodoEvaluacionesITS.objects.get(pk=request.GET['id'])
                    data['form'] = PeriodoEvaluacionesITSForm(instance=data['periodoevaluaciones'])
                return render(request ,"fecha_evaluaciones/editarbs.html" ,  data)

            return HttpResponseRedirect("/fecha_evaluaciones")
        else:
            if MODELO_EVALUACION == EVALUACION_IAVQ:
                data['periodoevaluaciones'] = PeriodoEvaluacionesIAVQ.objects.all()
            if MODELO_EVALUACION == EVALUACION_ITS:
                data['periodoevaluaciones'] = PeriodoEvaluacionesITS.objects.all()

            data['MODELO_EVALUATIVO'] = [MODELO_EVALUACION, EVALUACION_IAVQ, EVALUACION_ITS]
            return render(request ,"fecha_evaluaciones/periodosbs.html" ,  data)
