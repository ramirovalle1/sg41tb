from datetime import datetime, timedelta
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render
from decorators import secure_module
from settings import VALIDAR_ENTRADA_SISTEMA_CON_DEUDA
from sga.commonviews import addUserData
from sga.models import Profesor, Sesion, Clase, Inscripcion, Periodo, Materia

@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    data = {}
    addUserData(request, data)
    persona = data['persona']
    try:
        data['title'] = 'Horario de Alumno'

        inscripcion = Inscripcion.objects.get(persona=persona)

        #Comprobar que no tenga deudas para que no pueda usar el sistema
        if VALIDAR_ENTRADA_SISTEMA_CON_DEUDA and inscripcion.tiene_deuda():
            return HttpResponseRedirect("/")

        #Comprobar que el alumno este matriculado
        if not inscripcion.matriculado():
            return HttpResponseRedirect("/?info=Ud. aun no ha sido matriculado")

        materias = Materia.objects.filter(materiaasignada__matricula__inscripcion=inscripcion,materiaasignada__matricula__liberada=False)

        data['inscripcion'] = inscripcion
        data['periodo'] = request.session['periodo']
        data['matricula'] = inscripcion.matricula_set.filter(nivel__periodo=data['periodo'],liberada=False)

        data['materias'] = materias
        data['semana'] = ['Lunes','Martes','Miercoles','Jueves','Viernes', 'Sabado', 'Domingo']


        #hoy = datetime.now().date()
        hoy = datetime.now().date()

        clases = Clase.objects.filter(materia__nivel__periodo__activo=True, materia__nivel__cerrado=False, materia__materiaasignada__matricula__inscripcion=inscripcion, materia__inicio__lte=hoy, materia__fin__gte=hoy).order_by('materia__inicio')
        clasespm = [(x, x.materia.profesormateria_set.filter(desde__lte=hoy, hasta__gte=hoy)[:1].get() if x.materia.profesormateria_set.filter(desde__lte=hoy, hasta__gte=hoy).exists() else None) for x in clases]
        sesiones = Clase.objects.filter(materia__nivel__periodo__activo=True, materia__nivel__cerrado=False, materia__materiaasignada__matricula__inscripcion=inscripcion, materia__inicio__lte=hoy, materia__fin__gte=hoy).distinct('materia__nivel__sesion').values('materia__nivel__sesion')

        data['clases'] = clasespm
        data['sesiones'] = Sesion.objects.filter(id__in=sesiones)

        return render(request ,"alu_horarios/horariobs.html" ,  data)
    except Exception as ex:
        print(ex)
        return HttpResponseRedirect("/")
