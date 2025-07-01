
from datetime import datetime
import json
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render
from sga.commonviews import addUserData
from sga.models import ConvenioCarrera, EmpresaConvenio, Modalidad, Carrera

from sga.panel import MiPaginador



def view(request):
    if request.method == 'POST':
        action = request.POST['action']

        if action == 'guardarconveniocarrera':
            try:
                data = {'title': ''}

                idcarrera = request.POST['idcarrera'].split(",")
                for x in idcarrera:
                    conveniocarrera = ConvenioCarrera(empresaconvenio_id=int(request.POST['idconv']),
                                                      modalidad_id=int(request.POST['idmodalidad']),
                                                      carrera_id=int(x),activo=True)
                    conveniocarrera.save()
                data['result'] = 'ok'
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}),
                                    content_type="application/json")

        if action == 'eliminar':
            try:
                data = {'title': ''}
                conveniocarrera = ConvenioCarrera.objects.get(pk=request.POST['idconv'])
                conveniocarrera.delete()
                data['result'] = 'ok'
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}),
                                    content_type="application/json")





    else:

        data = {'title': 'Listado de Convenio por Carrera'}
        addUserData(request, data)
        search = None
        fecha = datetime.now().strftime("%Y-%m-%d")
        if 'action' in request.GET:
            action = request.GET['action']




        else:
            try:
                    conveniocarrea = ConvenioCarrera.objects.filter().order_by('-id')
                    if 's' in request.GET:
                        search = request.GET['s']

                        conveniocarrea=conveniocarrea.filter( Q(carrera__nombre__icontains=search) | Q(empresaconvenio__nombre__icontains=search)).order_by('carrera__nombre')


                    paging = MiPaginador(conveniocarrea, 30)
                    p = 1
                    try:
                        if 'page' in request.GET:
                            p = int(request.GET['page'])
                            paging = MiPaginador(conveniocarrea, 30)
                        page = paging.page(p)
                    except Exception as ex:
                        page = paging.page(1)


                    data['hoy'] = datetime.now()

                    data['paging'] = paging
                    data['rangospaging'] = paging.rangos_paginado(p)
                    data['page'] = page
                    data['empresaconvenios'] = page.object_list
                    data['fechah'] = datetime.now().strftime("%Y-%m-%d")
                    hora_actual = datetime.now().time()
                    data['horactual'] = hora_actual.strftime('%H:%M')
                    data['search'] = search if search else ""
                    data['listconvenio'] = EmpresaConvenio.objects.filter()
                    data['listamodalidad'] = Modalidad.objects.filter()
                    data['listcarrera'] = Carrera.objects.filter(activo=True)


                    return render(request,"solicitudpostulacionbeca/conveniocarrera.html", data)

            except Exception as ex:
                print(ex)