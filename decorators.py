from django.http import HttpResponseRedirect
from settings import ALLOWED_IPS_FOR_INHOUSE, EVALUACION_TES
import settings
from sga.commonviews import ip_client_address
from sga.models import Modulo, Aula
from functools import wraps



def localhost(f):
    """Requires that a view be invoked from localhost only."""

    def new_f(*args, **kwargs):
        request = args[0]
        if request.META["REMOTE_ADDR"] != "127.0.0.1":
            raise Exception("This URL is only invokable by localhost.")
        return f(*args, **kwargs)
    return new_f


def secure_module(f):

    def new_f(*args, **kwargs):
        request = args[0]
        p = request.session['persona']
        if settings.MODELO_EVALUACION!=EVALUACION_TES:
            if Modulo.objects.filter(modulogrupo__grupos__in=p.usuario.groups.all(), url=request.path[1:],activo=True).exists():
                return f(request)
            else:
                return HttpResponseRedirect("/")
        return f(request)

    return new_f

def inhouse_only(f):

    def new_f(*args, **kargs):
        request = args[0]
        if '*' in ALLOWED_IPS_FOR_INHOUSE:
            return f(request)
        elif request.META['REMOTE_ADDR'] in ALLOWED_IPS_FOR_INHOUSE:
            return f(request)
        else:
            return HttpResponseRedirect('/')

    return new_f


def inhouse_check(request):
    if '*' in ALLOWED_IPS_FOR_INHOUSE:
        return True
    elif request.META['REMOTE_ADDR'] in ALLOWED_IPS_FOR_INHOUSE:
        return True
    return False


def inclassroom_check(request):
    # client_address = ip_client_address(request)
    try:
        # case server externo
        client_address = request.META['HTTP_X_FORWARDED_FOR']
    except:
        # case localhost o 127.0.0.1
        client_address = request.META['REMOTE_ADDR']
    ips_aulas = [x.ip for x in Aula.objects.all()]
    if client_address in ips_aulas:
        return True
    return False

def inclassroom_check_docente(request):
    # client_address = ip_client_address(request)
    try:
        # case server externo
        client_address = request.META['HTTP_X_FORWARDED_FOR']
    except:
        # case localhost o 127.0.0.1
        client_address = request.META['REMOTE_ADDR']
    ips_aulas = [x.ip for x in Aula.objects.filter(activa=True)]
    if client_address in ips_aulas:
        return True
    return False