from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render
from decorators import secure_module
from sga.commonviews import addUserData
from sga.models import Carrera, MateriaAsignada, Persona

@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    data = {'title': 'Busqueda de Cursos'}
    addUserData(request, data)
    search = None
    if 's' in request.GET:
        search = request.GET['s']
        if search:
            ss = search.split(' ')
            while '' in ss:
                ss.remove('')
            if len(ss) == 1:
                carrera=Carrera.objects.get(id=16)
                # nivel=MateriaAsignada.objects.filter(matricula__carrera=carrera)
                data['materiasignada'] = MateriaAsignada.objects.filter((Q(matricula__inscripcion__persona__cedula=search) |Q(matricula__inscripcion__persona__pasaporte=search)),matricula__nivel__carrera=carrera).order_by('materia')
                if Persona.objects.filter(Q(cedula=search)|Q(pasaporte=search)).exists():
                    if Persona.objects.filter(cedula=search).exists():
                        data['personal'] = Persona.objects.filter(cedula=search)[:1].get()
                    else:
                        data['personal'] = Persona.objects.filter(pasaporte=search)[:1].get()

                data['num']=data['materiasignada'].count()
    return render(request ,"congreso/congreso.html" ,  data)