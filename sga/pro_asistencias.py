from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.db.models.query_utils import Q
from decorators import secure_module
from sga.commonviews import addUserData
from sga.models import Profesor, LeccionGrupo, Materia, Periodo

@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    if 'action' in request.GET:
        if request.GET['action']=='segmento':
            materia = Materia.objects.get(pk=request.GET['id'])
            return render(request, "pro_asistencias/segmentobs.html", {'materia': materia})
    else:
        data = {'title': 'Asistencias de Alumnos'}
        addUserData(request,data)
        try:
            profesor = Profesor.objects.get(persona=data['persona'])
            data['profesor'] = profesor

            materias = Materia.objects.filter(Q(nivel__periodo__activo=True)& (Q(profesormateria__profesor=profesor,profesormateria__profesor_aux=None) | Q(profesormateria__profesor_aux=profesor.id)))
            data['materias'] = materias

    #        data['materias'] = list(set([clase.materia for clase in profesor.clase_set.all()]))
    #        data['periodo'] = Periodo.periodo_vigente()

            return render(request ,"pro_asistencias/asistenciasbs.html" ,  data)
        except :
            return HttpResponseRedirect("/?info=Ud. no ha sido asignado como profesor")
