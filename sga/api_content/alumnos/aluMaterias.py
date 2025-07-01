from django.http import JsonResponse
from sga.models import Inscripcion, ProfesorMateria, AsistenciaLeccion, RecordAcademico, LeccionGrupo


def aluMaterias(request, id):
    inscripcion = Inscripcion.objects.get(pk=id)
    if inscripcion.matricula_set.filter(nivel__periodo__activo=True, nivel__cerrado=False, liberada=False).exists():
        matricula = inscripcion.matricula_set.filter(nivel__periodo__activo=True, nivel__cerrado=False, liberada=False)[:1].get()
        materiasAsignadas = matricula.materiaasignada_set.all().order_by('materia__inicio')



        from sga.api_rest import decimal_format
        response = [
            {
                'materiaNombre': mat.materia.asignatura.nombre,
                'materiaInicio': mat.materia.inicio,
                'materiaFin': mat.materia.fin,
                'numAsistencias': AsistenciaLeccion.objects.filter(leccion__clase__materia=mat.materia, matricula=matricula, asistio=True).count(),
                'estado': mat.evaluacion().estado.nombre,
                'asistencias': decimal_format(mat.porciento_asistencia()),
                'lecciones': [
                    {
                        'fecha': leccion.fecha,
                        'horaEntrada':leccion.horaentrada,
                        'horaSalida':leccion.horasalida,
                        'asistio': False
                    } for leccion in LeccionGrupo.objects.filter(materia__nivel__periodo__activo=True,lecciones__clase__materia=mat.materia).order_by('-fecha', '-horaentrada')
                ],
                'profesores': [
                    {
                        'profesorNombre': pm.profesor.persona.nombre_completo_inverso(),
                        'numClases': pm.cantidad_lecciones() if pm.tiene_lecciones() else 0
                    } for pm in ProfesorMateria.objects.filter(materia=mat.materia).order_by('desde')
                ]

            } for mat in materiasAsignadas
        ]
    else:
        response = {'error': 'No se encuentra matriculado.'}

    return JsonResponse(response, safe=False, status=200)