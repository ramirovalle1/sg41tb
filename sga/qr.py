from datetime import datetime
from django.shortcuts import render
from sga.commonviews import addUserData
from sga.models import Aula, Clase


def aula(request, id):
    data = {'title': 'Aula'}
    addUserData(request, data)
    aula = Aula.objects.get(pk=id)
    data['aula'] = aula
    hoy = datetime.today().date()
    data['hoy'] = hoy
    dia = hoy.weekday()+1
    clases = Clase.objects.filter(aula=aula, materia__nivel__cerrado=False,dia=dia,materia__inicio__lte=hoy,materia__fin__gte=hoy).order_by('turno__comienza')
    data['clases'] = clases
    return render(request ,"qr/aula.html" ,  data)

def aulas(request):
    data = {'title': 'Aulas'}
    addUserData(request, data)
    aulas = Aula.objects.all().order_by('nombre')
    data['aulas'] = aulas
    return render(request ,"qr/aulas.html" ,  data)
