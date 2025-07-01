from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render
from decorators import secure_module
from settings import REPORTE_CRONOGRAMA_MATERIAS, VALIDAR_ENTRADA_SISTEMA_CON_DEUDA, ASIGNATURA_PRACTICA_CONDUCCION, INSCRIPCION_CONDUCCION
from sga.commonviews import addUserData
from sga.models import Inscripcion

@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    data = {'title': ' Cronograma de Clases del Alumno'}
    addUserData(request, data)

    try:
        inscripcion = Inscripcion.objects.get(persona=data['persona'])

        #Comprobar que no tenga deudas para que no pueda usar el sistema
        # OCastillo 30-06-2020 se quita validacion para que estudiante pueda ver su cronograma asi tenga deuda
        #if VALIDAR_ENTRADA_SISTEMA_CON_DEUDA and inscripcion.tiene_deuda():
        #    return HttpResponseRedirect("/")

        #Comprobar que el alumno este matriculado
        if not inscripcion.matriculado():
            return HttpResponseRedirect("/?info=Ud. aun no ha sido matriculado")
        matricula = inscripcion.matricula_set.filter(nivel__periodo__activo=True, nivel__cerrado=False,liberada=False)[:1].get()
        if INSCRIPCION_CONDUCCION:
            materiasAsignadas = matricula.materiaasignada_set.all().order_by('materia__inicio').exclude(materia__asignatura__id=ASIGNATURA_PRACTICA_CONDUCCION)
        else:
            materiasAsignadas = matricula.materiaasignada_set.all().order_by('materia__inicio')

        data['matricula'] = matricula
        data['materiasasignadas'] = materiasAsignadas
        data['reporte_cronograma_materias'] = REPORTE_CRONOGRAMA_MATERIAS
        data['hoy'] = datetime.today()

        return render(request ,"alu_cronograma/materiasbs.html" ,  data)
    except Exception as ex:
        return HttpResponseRedirect("/")