from django.http import JsonResponse

from sga.models import Provincia


def provincias(request):
    response = [
        {
            'id': x.id,
            'nombre': x.nombre
        } for x in Provincia.objects.all().order_by('nombre')
    ]

    return JsonResponse(response, safe=False, status=200)