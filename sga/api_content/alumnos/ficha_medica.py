from django.http import JsonResponse

from med.models import PersonaExamenFisico, PersonaExtension, PersonaFichaMedica
from sga.models import Persona


def ficha_medica(request, id):
    response = {}
    data = []
    # addUserData(request, data)
    persona = Persona.objects.get(id=id)
    if PersonaExamenFisico.objects.filter(personafichamedica__personaextension__persona=persona).exists():
        pexamenfisico = PersonaExamenFisico.objects.filter(personafichamedica__personaextension__persona=persona)[:1].get()
    else:
        pext = PersonaExtension(persona=persona)
        pext.save()
        pfichamedica = PersonaFichaMedica(personaextension=pext)
        pfichamedica.save()
        pexamenfisico = PersonaExamenFisico(personafichamedica=pfichamedica)
        pexamenfisico.save()






    return JsonResponse(response, safe=False, status=200)