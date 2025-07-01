from django.http import JsonResponse

from sga.models import Canton, Parroquia


def parroquias(request, id):
    canton = Canton.objects.get(id=id)
    response = [
        {
            'id': x.id,
            'idCanton': x.canton.id,
            'nombre': x.nombre
        } for x in Parroquia.objects.filter(canton=canton).order_by('nombre')
    ]

    return JsonResponse(response, safe=False, status=200)