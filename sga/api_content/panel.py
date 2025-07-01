from django.http import JsonResponse

from sga.commonviews import addUserData
from sga.models import Persona, ModuloGrupo, Modulo, Periodo, Inscripcion, FotoPersona


def apiPanel(request, id):
    response = {}
    data = []
    # addUserData(request, data)
    persona = Persona.objects.get(id=id)
    grupos = persona.usuario.groups.all().order_by('name')
    modulos_grupos = ModuloGrupo.objects.filter(grupos__id__in=grupos.values('id'))

    for mg in modulos_grupos:
        modulos = mg.modulos.filter(activo=True).order_by('nombre').distinct()
        data_grupos = {
            'grupo': mg.nombre,
            'modulos': [
                {
                    'nombre': x.nombre,
                    'descripcion': x.descripcion,
                    'url': x.url,
                    'img': str(x.icono),
                }
            for x in modulos
            ]
        }
        data.append(data_grupos)

        response['grupoModulos'] = data

        response['periodos'] = [
            {
                'id': x.id,
                'nombre':x.nombre,
                'desde':x.inicio,
                'hasta':x.fin
            } for x in Periodo.objects.filter(activo=True).order_by('-id')[:10]
        ]

        inscripcion = None
        if Inscripcion.objects.filter(persona=persona).exists():
            inscripcion = Inscripcion.objects.filter(persona=persona).order_by('-id')[:1].get()
        foto = 'https://sga.itb.edu.ec/static/images/itb_iso_circulo.png'
        if FotoPersona.objects.filter(persona=persona).exists():
            foto = 'https://sga.itb.edu.ec/media/' + str(FotoPersona.objects.filter(persona=persona).order_by('-id')[:1].get().foto)
        response['persona'] = {
            'idPersona': persona.id,
            'nombre': nombre_completo(persona),
            'identificacion': persona.cedula if persona.cedula else persona.pasaporte,
            'tipoIdentificacion': 'CI' if persona.cedula else 'TP',
            'nacionalidadEmoticon': persona.nacionalidad.emoticon,
            'esInscripcion': True if inscripcion  else False,
            'idInscripcion': inscripcion.id if inscripcion else None,
            'usuario': persona.usuario.username,
            'celular': persona.telefono if persona.telefono else None,
            'convencional': persona.telefono_conv if persona.telefono_conv else None,
            'email': persona.email if persona.email else None,
            'emailinst': persona.emailinst,
            'sexo': persona.sexo.nombre if persona.sexo else '',
            'foto': str(foto),
        }

    return JsonResponse(response, safe=False, status=200)

    # return JsonResponse({'status': 'error', 'error':'ERROR DE PRUEBA'}, status=400)

def nombre_completo(persona):
    try:
        primerNombre, segundoNombre = persona.nombres.split()
        return "{} {} {} {}".format(
            primerNombre.capitalize(),
            segundoNombre.capitalize(),
            persona.apellido1.capitalize(),
            persona.apellido2.capitalize()
        )
    except Exception as e:
        return persona.nombre_completo()