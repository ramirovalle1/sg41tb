from django.http import JsonResponse

from settings import FECHA_ELECT_FAC
from sga.models import Inscripcion, Factura, NotaCreditoInstitucion


def aluFacturasElectronicas(request, id):
    inscripcion = Inscripcion.objects.get(id=id)
    persona = inscripcion.persona

    facturas = None
    notasCredito = None
    if persona.extranjero:
        facturas = Factura.objects.filter(cliente__ruc=persona.pasaporte, estado='AUTORIZADO', fecha__gte=FECHA_ELECT_FAC).order_by('-fecha')#.values('id', 'numero', 'fecha', 'estado', 'dirfactura', 'numautorizacion')
        if NotaCreditoInstitucion.objects.filter(inscripcion__persona__pasaporte=persona.pasaporte, estado='AUTORIZADO').exists():
            notasCredito = NotaCreditoInstitucion.objects.filter(inscripcion__persona__pasaporte=persona.pasaporte, estado='AUTORIZADO')
    else:
        facturas = Factura.objects.filter(cliente__ruc=persona.cedula, estado='AUTORIZADO', fecha__gte=FECHA_ELECT_FAC).order_by('-fecha')#.values('id', 'numero', 'fecha', 'estado', 'dirfactura', 'numautorizacion')
        if NotaCreditoInstitucion.objects.filter(inscripcion__persona__cedula=persona.cedula, estado='AUTORIZADO').exists():
            notasCredito = NotaCreditoInstitucion.objects.filter(inscripcion__persona__cedula=persona.cedula, estado='AUTORIZADO')

    response = []

    if facturas:
        for x in facturas:
            response.append(
                {
                    'tipo': 'Factura',
                    'numero': x.numero,
                    'numeroAutorizacion': x.numautorizacion,
                    'fecha': x.fecha,
                    'ride': '/reportes?action=run&n=factura_sri&rt=pdf&factura='+str(x.id),
                    'xml': x.dirfactura
                }
            )

    if notasCredito:
        for x in notasCredito:
            ride = '/reportes?action=run&n=notacredito_sri&rt=pdf&notacredito=' + str(x.id)
            if x.tipo.id == 1:
                ride = '/reportes?action=run&n=notacredito_sri_nodet&rt=pdf&factura=' + str(x.factura.id)
            response.append(
                {
                    'tipo': 'Nota de credito',
                    'numero': x.numero,
                    'numeroAutorizacion': x.numautorizacion,
                    'fecha': x.fecha,
                    'ride': ride,
                    'xml': x.dirnotacredito
                }
            )

    return JsonResponse(response, safe=False, status=200)



