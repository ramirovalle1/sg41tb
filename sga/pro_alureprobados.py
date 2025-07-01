from datetime import datetime, time
import json
from django.contrib.auth.decorators import login_required
from django.forms.models import model_to_dict
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, render
from django.template.context import RequestContext
from django.template.loader import get_template
from decorators import secure_module
from settings import NOTA_PARA_APROBAR, ASIST_PARA_APROBAR, ASIST_PARA_SEGUIR, NOTA_ESTADO_APROBADO, NOTA_ESTADO_REPROBADO, NOTA_ESTADO_EN_CURSO, PORCIENTO_NOTA1, PORCIENTO_NOTA4, PORCIENTO_NOTA3, PORCIENTO_NOTA2, PORCIENTO_NOTA5
from sga.commonviews import addUserData
from sga.forms import NotaIAVQForm
from sga.models import Profesor, Materia, MateriaAsignada, EvaluacionIAVQ2, NotaIAVQ, Periodo, PeriodoEvaluacionesIAVQ

@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    data = {'title': 'Gestion de Alumnos a Supletorio o Reprobados'}
    addUserData(request,data)

    profesor = Profesor.objects.get(persona=data['persona'])
    data['profesor'] = profesor
    data['materias'] = profesor.materias_imparte()
    data['periodo'] = Periodo.objects.get(activo=True)

    return render(request ,"pro_alureprobados/listado.html" ,  data)