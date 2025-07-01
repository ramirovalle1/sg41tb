import json
from django.http import HttpResponse
from django.template import Context
from django.template.loader import get_template
from sga.models import *


def imprimir_contenido(user, referencia, iden):
    mi = ModeloImpresion.objects.get(referencia=referencia)
    modelo = eval(mi.modelo)
    dato = modelo.objects.get(pk=iden)

    impresion = Impresion(usuario=user,impresa=False,contenido='')
    impresion.save()

    template = get_template("print/tesprint/%s"%(mi.plantilla))
    d = Context({'dato': dato, "id": impresion.id})
    json_content = template.render(d)

    impresion.contenido = json_content
    impresion.save()

def view(request, referencia, id):
    if ModeloImpresion.objects.filter(referencia=referencia).exists():
        imprimir_contenido(request.user, referencia, id)
        return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
    else:
        return HttpResponse(json.dumps({"result":"bad", "error": "No existe modelo de impresion"}),content_type="application/json")