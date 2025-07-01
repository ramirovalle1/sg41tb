from django.http import JsonResponse

from sga.commonviews import addUserData
from sga.models import Persona, Inscripcion, Rubro


def alu_finanzas(request, id):
    # addUserData(request, data)
    persona = Persona.objects.get(id=id)
    inscripcion = Inscripcion.objects.filter(persona__id=id, persona__usuario__is_active=True, persona=persona).order_by('-id')[:1].get()
    rubros = Rubro.objects.filter(inscripcion=inscripcion).order_by('cancelado', 'fechavence', '-id')

    from sga.api_rest import decimal_format
    data = [
        {
            'rubro': x.nombre(),
            'fecha': str(x.fecha),
            'fechaVencimiento': str(x.fechavence),
            'valor': decimal_format(x.valor),
            'pagado': decimal_format(x.verifica_total_pagado()),
            'vencido': decimal_format(x.vencido()),
            'porPagar': decimal_format(x.verifica_adeudado()),
            'cancelado': x.cancelado
        } for x in rubros
    ]
    return JsonResponse(data, safe=False, status=200)