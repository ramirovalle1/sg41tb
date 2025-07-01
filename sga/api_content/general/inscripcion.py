from django.db.models import Q
from django.http import JsonResponse

from sga.models import Inscripcion, FotoPersona


def inscripcion(
        request,
        search = None,
        desde = None,
        hasta = None
):
    desde = int(desde) if desde else 1
    hasta = int(hasta) if hasta else 20
    rango = hasta - desde + 1
    print(rango)

    ss = search.split(' ') if search else []
    while '' in ss:
        ss.remove('')

    inscripciones = Inscripcion.objects.all().order_by('persona__apellido1', 'persona__apellido1', 'persona__nombres')

    if search:
        if len(ss) == 1:
            inscripciones = inscripciones.filter(
                Q(persona__nombres__icontains=search) | Q(persona__apellido1__icontains=search) |
                Q(persona__apellido2__icontains=search) | Q(persona__cedula__icontains=search) |
                Q(persona__pasaporte__icontains=search) | Q(identificador__icontains=search) |
                Q(inscripciongrupo__grupo__nombre__icontains=search) | Q(carrera__nombre__icontains=search) |
                Q(persona__usuario__username__icontains=search)
            ).order_by('persona__apellido1', 'persona__apellido2', 'persona__nombres')
        elif len(ss) > 1:
            inscripciones = inscripciones.filter(Q(persona__apellido1__icontains=ss[0]) & Q(persona__apellido2__icontains=ss[1])).order_by('persona__apellido1', 'persona__apellido2', 'persona__nombres')

    total_inscripciones = inscripciones.count() + 1
    hasta_filter = hasta if hasta <= total_inscripciones else total_inscripciones
    if desde > 0 and hasta_filter <= total_inscripciones:
        inscripciones = inscripciones[desde - 1:hasta_filter - 1]

        data = []
        for x in inscripciones:
            if FotoPersona.objects.filter(persona=x.persona).exists():
                foto = 'https://sga.itb.edu.ec/media/' + str(FotoPersona.objects.filter(persona=x.persona).order_by('-id')[:1].get().foto)
            else:
                foto = "https://sga.itb.edu.ec/static/images/female2.png" if x.persona.sexo.id == 1 else "https://sga.itb.edu.ec/static/images/male2.png"

            data.append({
                'id': x.id,
                'idPersona': x.persona.id,
                'nombre': x.persona.nombre_completo_inverso(),
                'identificacion': x.persona.cedula if x.persona.cedula else x.persona.pasaporte,
                'activo': x.persona.usuario.is_active,
                'username': x.persona.usuario.username,
                'password': x.persona.usuario.password,
                'celular': x.persona.telefono,
                'convencional': x.persona.telefono_conv,
                'email': x.persona.emailinst,
                'email_personal': x.persona.email if x.persona.email else '',
                'carrera': x.carrera.nombre,
                'grupo': x.grupo().nombre if x.grupo() else '',
                'foto': foto
            })

        next_desde = desde + rango
        next_hasta = hasta + rango
        back_desde = desde - rango
        back_hasta = hasta - rango

        response = {
            'inscripciones': data,
            'paging': {
                'back': {
                    'from': back_desde,
                    'to': back_hasta,
                },
                'next': {
                    'from': next_desde,
                    'to': next_hasta,
                },
                'first': desde == 1,
                'last': hasta >= total_inscripciones
            }
        }
    else:
        response = {"error": "No se pueden filtrar inscripciones, faltan datos."}

    return JsonResponse(response, safe=False, status=200)
