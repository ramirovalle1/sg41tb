from datetime import datetime

from django.http import JsonResponse
from sga.models import Inscripcion, Clase, MateriaAsignada, ProfesorMateria, DIAS_CHOICES, Matricula

def aluHorarios(request, id):
    inscripcion = Inscripcion.objects.get(pk=id)

    if Matricula.objects.filter(inscripcion=inscripcion).exclude(nivel__cerrado=True).exists():
        matricula = Matricula.objects.filter(inscripcion=inscripcion).exclude(nivel__cerrado=True)[:1].get()
        materiasAsignadas = MateriaAsignada.objects.filter(matricula=matricula).order_by('materia__inicio')

        from sga.api_rest import decimal_format
        response = [
            {
                'materiaNombre': mat.materia.asignatura.nombre,
                'materiaInicio': mat.materia.inicio,
                'materiaFin': mat.materia.fin,
                'nivelMalla': mat.materia.nivel.nivelmalla.nombre,
                'paralelo': mat.materia.nivel.paralelo,
                'clases': [
                    {
                        'dia': DIAS_CHOICES[clase.dia - 1][1],
                        'turnoComienza': clase.turno.comienza,
                        'turnoTermina': clase.turno.termina,
                        'turnoHoras': decimal_format(clase.turno.horas) if clase.turno.horas else decimal_format(0),
                        'esPractica': clase.turno.practica,
                        'sesion': clase.turno.sesion.nombre,
                        'profesor': clase.profesormateria.profesor.persona.nombre_completo_inverso(),
                        'virtual': clase.virtual,
                        'aula': clase.aula.nombre,
                        'sede': clase.aula.sede.nombre
                    } for clase in Clase.objects.filter(materia=mat.materia).order_by('dia', 'turno__comienza')
                ]
            } for mat in materiasAsignadas
        ]
    else:
        response = {'error': 'No se encuentra matriculado.'}

    return JsonResponse(response, safe=False, status=200)