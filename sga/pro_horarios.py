from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render
from decorators import secure_module
from settings import PROFE_PRACT_CONDUCCION, VALIDA_MATERIA_APROBADA, DEFAULT_PASSWORD
from sga.commonviews import addUserData
from django.db.models.query_utils import Q
from sga.models import Profesor, Clase, Sesion, LeccionGrupo, ProfesorMateria,Nivel


@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    data = {}
    addUserData(request, data)
    persona = data['persona']
    try:
        profesor = Profesor.objects.get(persona=persona)
        hoy = datetime.now().date()
        data['disponible'] = LeccionGrupo.objects.filter(profesor=profesor,abierta=True).count()==0
        if not data['disponible']:
            data['lecciongrupo'] = LeccionGrupo.objects.filter(profesor=profesor,abierta=True)[:1].get()
            if ProfesorMateria.objects.filter(materia=data['lecciongrupo'].materia,profesor=data['lecciongrupo'].profesor,desde__lte=hoy,hasta__gte=hoy).exists():
                    data['profesormateria'] = ProfesorMateria.objects.get(materia=data['lecciongrupo'].materia,profesor=data['lecciongrupo'].profesor,desde__lte=hoy,hasta__gte=hoy)
        data['periodo'] = request.session['periodo']
        data['title'] = 'Horario de Profesor'
        data['profesor'] = profesor
        data['semana'] = ['Lunes','Martes','Miercoles','Jueves','Viernes', 'Sabado', 'Domingo']


        if 'error' in request.GET:
            data['error']=request.GET['error']
        hoy = datetime.now().date()
        if Profesor.objects.filter(categoria__id = PROFE_PRACT_CONDUCCION, pk = profesor.id):
            clases = Clase.objects.filter(materia__nivel__periodo__activo=True,materia__inicio__lte=hoy, materia__fin__gte=hoy,profesormateria__profesor_aux=profesor.id, profesormateria__desde__lte=hoy, profesormateria__hasta__gte=hoy,materia__nivel__periodo=data['periodo'], materia__cerrado=False).order_by('materia__inicio')
            clasespm = [(x, x.materia.profesormateria_set.filter(profesor_aux=profesor.id)[:1].get()) for x in clases]
            sesiones = Clase.objects.filter(materia__nivel__periodo__activo=True,materia__inicio__lte=hoy, materia__fin__gte=hoy, profesormateria__profesor_aux=profesor.id, profesormateria__desde__lte=hoy, profesormateria__hasta__gte=hoy,materia__nivel__periodo=data['periodo'], materia__cerrado=False).distinct('materia__nivel__sesion').values('materia__nivel__sesion')
        else:
            if VALIDA_MATERIA_APROBADA:

                clases = Clase.objects.filter((Q(materia__nivel__periodo__activo=True,materia__inicio__lte=hoy, materia__fin__gte=hoy, materia__profesormateria__desde__lte=hoy, materia__profesormateria__hasta__gte=hoy,materia__nivel__periodo=data['periodo'], materia__cerrado=False) & (Q(materia__profesormateria__profesor=profesor,materia__profesormateria__profesor_aux=None) | Q(materia__profesormateria__profesor_aux=profesor.id))),materia__aprobada=True).order_by('materia__inicio')
                clasespm = [(x, x.materia.profesormateria_set.filter(Q(profesor=profesor)|Q(profesor_aux=profesor.id))[:1].get()) for x in clases]
                sesiones = Clase.objects.filter((Q(materia__nivel__periodo__activo=True,materia__inicio__lte=hoy, materia__fin__gte=hoy, materia__profesormateria__desde__lte=hoy, materia__profesormateria__hasta__gte=hoy,materia__nivel__periodo=data['periodo'], materia__cerrado=False) & (Q(materia__profesormateria__profesor=profesor,materia__profesormateria__profesor_aux=None) | Q(materia__profesormateria__profesor_aux=profesor.id))),materia__aprobada=True).distinct('materia__nivel__sesion').values('materia__nivel__sesion')
            else:
                # clases = Clase.objects.filter(Q(materia__nivel__periodo__activo=True,materia__inicio__lte=hoy, materia__fin__gte=hoy, profesormateria__desde__lte=hoy, profesormateria__hasta__gte=hoy,materia__nivel__periodo=data['periodo'], materia__cerrado=False) & (Q(profesormateria__profesor=profesor,profesormateria__profesor_aux=None) | Q(profesormateria__profesor_aux=profesor.id))).order_by('materia__inicio')
                clases = Clase.objects.filter(Q(materia__nivel__periodo__activo=True,profesormateria__profesor=profesor,profesormateria__desde__lte=hoy, profesormateria__hasta__gte=hoy,materia__nivel__periodo=data['periodo'], materia__cerrado=False) & (Q(profesormateria__profesor_aux=None) | Q(profesormateria__profesor_aux=profesor.id))).order_by('materia__inicio')
                clasespm = [(x, x.materia.profesormateria_set.filter(Q(profesor=profesor)|Q(profesor_aux=profesor.id))[:1].get()) for x in clases]
                sesiones = Clase.objects.filter(Q(materia__nivel__periodo__activo=True,materia__inicio__lte=hoy, materia__fin__gte=hoy, profesormateria__desde__lte=hoy, profesormateria__hasta__gte=hoy,materia__nivel__periodo=data['periodo'], materia__cerrado=False) & (Q(profesormateria__profesor=profesor,profesormateria__profesor_aux=None) | Q(profesormateria__profesor_aux=profesor.id))).distinct('materia__nivel__sesion').values('materia__nivel__sesion')
        data['clases'] = clasespm
        data['DEFAULT_PASSWORD'] = DEFAULT_PASSWORD
        data['sesiones'] = Sesion.objects.filter(id__in=sesiones)
        if 'info' in request.GET :
            data['info'] = request.GET['info']

        return render(request ,"pro_horarios/horariobs.html" ,  data)
    except :
        return HttpResponseRedirect("/")


