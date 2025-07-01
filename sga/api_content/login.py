from datetime import datetime
from django.contrib.auth import login, authenticate
from django.http import JsonResponse

from sga.models import Persona, FotoPersona

def apiLogin(request, username, password):
    user = authenticate(username=username, password=password)
    if user is not None and user.is_active:
        persona = Persona.objects.get(usuario=user)
        if persona is not None:
            login(request, user)
            request.session['persona'] = persona
            request.session['last_touch'] = datetime.now()

            foto = None
            if FotoPersona.objects.filter(persona=persona).exists():
                foto = FotoPersona.objects.filter(persona=persona).order_by('-id')[:1].get().foto
            listPersona = {
                'idPersona': persona.id,
                'nombre': persona.nombre_completo_inverso(),
                'identificacion': persona.cedula if persona.cedula else persona.pasaporte,
                'username': persona.usuario.username,
                'celular': persona.telefono if persona.telefono else None,
                'convencional': persona.telefono_conv if persona.telefono_conv else None,
                'email': persona.email if persona.email else None,
                'emailinst': persona.emailinst,
                'gender': persona.sexo.nombre if persona.sexo else '',
                'photo': str(foto),
            }

            # data = {
            #     'status': 'success',
            #     'data': {'user': listPersona}
            # }

            return JsonResponse(listPersona, status=200)
        else:
            return JsonResponse({"error": "No se encontró la persona asociada"}, status=401)
    else:
        return JsonResponse({"error": "Credenciales incorrectas"}, status=400)