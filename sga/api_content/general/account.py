from django.http import JsonResponse
from sga.models import Persona, FotoPersona, Provincia, Canton, Parroquia, TipoSangre

def cuenta(request, id):
    persona = Persona.objects.get(id=id)
    foto = 'https://sga.itb.edu.ec/static/images/itb_iso_circulo.png'
    if FotoPersona.objects.filter(persona=persona).exists():
        foto = 'https://sga.itb.edu.ec/media/' + str(FotoPersona.objects.filter(persona=persona).order_by('-id')[:1].get().foto)

    response = {
        'idPersona': persona.id,
        'nombre': persona.nombre_completo_inverso(),
        'identificacion': persona.cedula if persona.cedula else persona.pasaporte,
        'extranjero': True if persona.pasaporte else False,
        'nacionalidad': persona.nacionalidad.nombre,
        'fechaNacimiento': persona.nacimiento,
        'provinciaNacimiento': persona.provincia.nombre,
        'cantonNacimiento': persona.canton.nombre,
        'sexo': persona.sexo.nombre,
        'madre': persona.madre,
        'padre': persona.padre,
        'domicilioCallePrincipal': persona.direccion,
        'domicilioCalleSecundaria': persona.direccion2,
        'domicilio_numero': persona.num_direccion,
        'sector': persona.sector if persona.sector else None,
        'username': persona.usuario.username,
        'celular': persona.telefono if persona.telefono else None,
        'convencional': persona.telefono_conv if persona.telefono_conv else None,
        'email': persona.email if persona.email else None,
        'emailinst': persona.emailinst,
        'foto': str(foto),
        # Data con ids
        'nombreProvinciaResidencia': persona.provinciaresid.nombre,
        'nombreCantonResidencia': persona.cantonresid.nombre,
        'nombreParroquia': persona.parroquia.nombre,
        'nombreTipoSangre': persona.sangre.sangre,
        'idProvinciaResidencia': persona.provinciaresid.id,
        'idCantonResidencia': persona.cantonresid.id,
        'idParroquia': persona.parroquia.id,
        'idTipoSangre': persona.sangre.id,
    }

    # listProvincias = [{'id': x.id, 'nombre': x.nombre} for x in Provincia.objects.all().order_by('nombre')]
    # listCantones = [{'id': x.id, 'nombre': x.nombre, 'idProvincia': x.provincia.id} for x in Canton.objects.all().order_by('nombre')]
    # listParroquias = [{'id': x.id, 'nombre': x.nombre, 'idCanton': x.canton.id} for x in Parroquia.objects.all().order_by('nombre')]
    # listTipoSangre = [{'id': x.id, 'nombre': x.sangre} for x in TipoSangre.objects.all().order_by('sangre')]
    #
    # data['persona'] = listPersona
    # data['provincias'] = listProvincias
    # data['cantones'] = listCantones
    # data['parroquias'] = listParroquias
    # data['tipoSangre'] = listTipoSangre

    return JsonResponse(response, safe=False, status=200)
