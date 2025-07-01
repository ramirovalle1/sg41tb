from django.http import JsonResponse
from sga.models import Persona, Inscripcion, Rubro

def aluCronograma(request, id):
    inscripcion = Inscripcion.objects.get(pk=id)
    if not inscripcion.matriculado():
        return 'bad'
    matricula = inscripcion.matricula_set.filter(nivel__periodo__activo=True, nivel__cerrado=False, liberada=False)[:1].get()
    materiasAsignadas = matricula.materiaasignada_set.all().order_by('materia__inicio')

    data = [
        {
            'asignatura': x.materia.asignatura.nombre,
            'horas': x.materia.horas,
            'creditos': x.materia.creditos,
            'inicio': x.materia.inicio,
            'fin': x.materia.fin,
            'profesores':
                [
                    {
                        'profesor': pm.profesor.persona.nombre_completo_inverso(),
                        'auxiliar': True if pm.profesor_aux else False,
                        'segmento': pm.segmento.descripcion,
                        'desde': pm.desde,
                        'hasta': pm.hasta,
                        'idZoom': 'https://us04web.zoom.us/j/'+pm.idzoom if pm.idzoom else None
                     } for pm in x.materia.profesores_materia()
                ],
            'horarios':
                [
                    {
                        'dia': clase.dia_semana(),
                        'turnoComienza': clase.turno.comienza,
                        'turnoTermina': clase.turno.termina,
                        'claseVirtual': clase.virtual,
                        'aula': clase.aula.nombre
                    } for clase in x.materia.clase_set.all()
                ]

        } for x in materiasAsignadas
    ]
    return JsonResponse(data, safe=False, status=200)