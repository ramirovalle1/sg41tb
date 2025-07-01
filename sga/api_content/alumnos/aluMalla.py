from django.http import JsonResponse

from sga.models import Inscripcion, AsignaturaMalla, Malla, NivelMalla, RecordAcademico


def aluMalla(request, id):
    inscripcion = Inscripcion.objects.get(pk=id)
    malla = Malla.objects.filter(carrera=inscripcion.carrera).order_by('-id')[:1].get()
    asignaturasMalla = AsignaturaMalla.objects.filter(malla=malla).order_by('nivelmalla__orden','ejeformativo__orden')

    from sga.api_rest import decimal_format
    response = []
    for nivelMalla in NivelMalla.objects.filter(promediar=True).order_by('orden'):
        listAsignaturas = []
        for x in asignaturasMalla.filter(nivelmalla=nivelMalla).order_by('nivelmalla__orden', 'ejeformativo__orden'):
            record = None
            if RecordAcademico.objects.filter(inscripcion=inscripcion, asignatura=x.asignatura).exists():
                record = RecordAcademico.objects.filter(inscripcion=inscripcion, asignatura=x.asignatura).order_by('-id')[:1].get()

            listAsignaturas.append(
                {
                    'ejeFormativo': x.ejeformativo.nombre,
                    'asignaturaMallaIdent': x.identificacion,
                    'asignaturaNombre': x.asignatura.nombre,
                    'record': True if record else False,
                    'aprobado': record.aprobada if record else False,
                    'reprobado': not record.aprobada if record else False,
                    'nota': decimal_format(record.nota) if record else decimal_format(0),
                    'asistencia': decimal_format(record.asistencia) if record else decimal_format(0) ,
                }
            )

        data = {
            'nivelmallaNombre': nivelMalla.nombre,
            'nivelmallaNombreCorto': nivelMalla.nombrematriz,
            'asignaturas': listAsignaturas
        }
        response.append(data)
    return JsonResponse(response, safe=False, status=200)