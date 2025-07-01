from django.http import JsonResponse

from sga.models import Provincia, Canton


def cantones(request, id):
    provincia = Provincia.objects.get(id=id)
    response = [
        {
            'id': x.id,
            'idProvincia': x.provincia.id,
            'nombre': x.nombre
        } for x in Canton.objects.filter(provincia=provincia).order_by('nombre')
    ]

    return JsonResponse(response, safe=False, status=200)