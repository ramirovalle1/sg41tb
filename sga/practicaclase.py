from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from sga.commonviews import addUserData
from sga.models import ProfesorMateria, Profesor, LeccionGrupo

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    if request.method == 'POST':
        action = request.POST['action']
    else:
        data = {'title': 'Listado de Docentes'}
        addUserData(request, data)
        if 'action' in request.GET:
            action = request.GET['action']
        else:
            search = None
            data['profesor'] = Profesor.objects.get(id=request.GET['id'])
            data['profesormateria'] = ProfesorMateria.objects.filter(profesor=data['profesor'],materia__nivel__periodo=data['periodo'],segmento__id=2)
            # if data['profesormateria'].count()>0:
            data['lecciongrupo'] = LeccionGrupo.objects.filter(profesor=data['profesor'],materia__nivel__periodo=data['periodo'])
            return render(request ,"practicaclase/practicaclase.html" ,  data)