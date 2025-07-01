import json
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.db.models.aggregates import Sum
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from decorators import secure_module
from sga.models import SolicitudPracticas, SegmentoIndicadorEmp, PuntajeIndicador, EvaluacionSupervisorEmp, FichaReceptora
__author__ = 'jjurgiles'

@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    try:
        if request.method == 'POST':
            action = request.POST['action']
            if action == 'guardareval':
                result = {}
                try:
                    datos = json.loads(request.POST['datos'])
                    solicitud = SolicitudPracticas.objects.get(id=datos['idsolicitud'])
                    for d in datos['indicadores']:
                        evaluacion = EvaluacionSupervisorEmp(solicitudpracticas = solicitud,
                                                        segmentodetalle_id = d['iddetseg'] ,
                                                        fecha = datetime.now(),
                                                        puntajeindicador_id = d['idindic'])
                        evaluacion.save()
                    solicitud.save()
                    solicitud.mail_evaluacrealizada(request.user)
                    solicitud.promedioevasuper = EvaluacionSupervisorEmp.objects.filter(solicitudpracticas = solicitud).aggregate(Sum('puntajeindicador__puntos'))['puntajeindicador__puntos__sum']
                    solicitud.save()
                    result['result'] = 'ok'
                    return HttpResponse(json.dumps(result),content_type="application/json")

                except Exception as e:
                    print("error excep guardareval superv "+str(e))
                    result['result'] ="bad"
                    return HttpResponse(json.dumps(result),content_type="application/json")
            elif action == 'logearse':
                result = {}
                try:
                    solicitudpractica = SolicitudPracticas.objects.get(id=request.POST['idsoli'])
                    if not FichaReceptora.objects.filter(correo=request.POST['correo'],solicitudpracticas=solicitudpractica).exists():
                        result['result'] = 'bad'
                        return HttpResponse(json.dumps(result),content_type="application/json")
                    fichareceptora = FichaReceptora.objects.get(correo=request.POST['correo'],solicitudpracticas=solicitudpractica)
                    contrasena = crear_contrasena(fichareceptora)
                    if contrasena == request.POST['contrasena']:
                        request.session['fichareceptora'] = fichareceptora

                        result['result'] = 'ok'
                    else:
                        result['result'] = 'bad'
                        return HttpResponse(json.dumps(result),content_type="application/json")
                    return HttpResponse(json.dumps(result),content_type="application/json")

                except Exception as e:
                    print("error excep guardareval superv "+str(e))
                    result['result'] ="bad"
                    return HttpResponse(json.dumps(result),content_type="application/json")
        else:
            data = {'title':'supervisor'}

            if 'action' in request.GET:
                action = request.GET['action']
                if action == 'evaluar':
                    # if FichaReceptora.objects.filter(corre=)
                    if 'id' in request.GET:
                        if 'fichareceptora' in request.session:
                            if SolicitudPracticas.objects.filter(id=request.GET['id'],finalizada=False).exists():
                                solicitud = SolicitudPracticas.objects.get(id=request.GET['id'])
                                data['solicitud'] = solicitud
                                data['segmentoindicadoremp'] = SegmentoIndicadorEmp.objects.filter(estado=True)
                                data['puntajeindicador'] = PuntajeIndicador.objects.filter(estado=True).order_by('-puntos')

                                return render(request ,"solicitudpractica/evaluaempresa.html" ,  data)
                        return HttpResponseRedirect("/supervisor?id="+request.GET['id'])
                    return HttpResponseRedirect("/")
            else:
                if 'id' in request.GET:
                    data['id'] = request.GET['id']
                    request.session.flush()
                    data['solicitud'] = SolicitudPracticas.objects.get(id=request.GET['id'])
                    if SolicitudPracticas.objects.filter(id=request.GET['id'],finalizada=True).exists():
                        data["finalizada"] = True
                return render(request ,"solicitudpractica/loginsupervisor.html" ,  data)
    except Exception as e:
        print("Error en supervisarevalest"+str(e))
        return HttpResponseRedirect("/?info=Error comuniquese con el administrador")

def crear_contrasena(fichareceptora):
    contrasen = ''
    ingreso = 0
    for i in range(len(fichareceptora.supervisor.split(' '))):
        numero1 = fichareceptora.supervisor.split(' ')[i]
        c = 0
        vocal = False

        for x in range(len(numero1)):
            if numero1[x] == 'A' or  numero1[x] == 'a':
                c = c + 1
                contrasen = contrasen+'4'
                vocal = True
            elif numero1[x] == 'E' or  numero1[x] == 'e':
                c = c + 1
                contrasen = contrasen+'3'
                vocal = True
            elif numero1[x] == 'I' or  numero1[x] == 'i':
                c = c + 1
                contrasen = contrasen+'1'
                vocal = True
            elif numero1[x] == 'O' or  numero1[x] == 'o':
                c = c + 1
                contrasen = contrasen+'0'
                vocal = True
            elif numero1[x] == 'U' or  numero1[x] == 'u':
                c = c + 1
                contrasen = contrasen+'4'
                vocal = True
            else:
                if ingreso == 0:
                    ingreso = 1
                    contrasen = contrasen+str(numero1[x]).upper()
                else:
                    contrasen = contrasen+str(numero1[x]).lower()
                if vocal:
                    c = c + 1
            if c == 3:
                break
    return contrasen
