from datetime import datetime
import json
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from decorators import secure_module
from sga.commonviews import addUserData,ip_client_address
from sga.forms import MallaForm, AsignaturaMallaForm
from sga.models import Malla, NivelMalla, EjeFormativo, AsignaturaMalla,CostoAsignatura
from django.template import RequestContext
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_str
from sga.reportes import elimina_tildes


@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
        data = {'title': 'Consulta de Mallas Curriculares'}
        addUserData(request,data)
        if request.method=='POST':
            action = request.POST['action']
            if action == 'valorasignatura':
                try:
                    am = AsignaturaMalla.objects.get(pk=request.POST['id'])

                    costo = CostoAsignatura(asignaturamalla = am,
                                            valor = request.POST['costo'],
                                            usuario = request.user,fecha =  datetime.now())
                    costo.save()

                    client_address = ip_client_address(request)

                    # Log de AGREGAR COSTO EN LA ASIGNATURA
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(costo).pk,
                        object_id       = costo.id,
                        object_repr     = force_str(costo),
                        action_flag     = ADDITION,
                        change_message  = 'Se ha agregado valor a asignatura (' + elimina_tildes(costo.asignaturamalla.asignatura.nombre) + ' Carrera: ' + elimina_tildes(costo.asignaturamalla.malla.carrera.nombre)+ ' (' + client_address + ')' )

                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as e:
                        return HttpResponse(json.dumps({"result":"bad","mensaje":e.message}),content_type="application/json")

            elif  action=='inactivarvalores':
                try:
                    costo = CostoAsignatura.objects.get(pk=request.POST['id'])
                    costo.activo=False
                    costo.usrinactiva=request.user
                    costo.fechainactiva =datetime.now()
                    costo.save()
                    #Obtener el ip de donde estan accediendo
                    try:
                        # case server externo
                        client_address = request.META['HTTP_X_FORWARDED_FOR']
                    except:
                        # case localhost o 127.0.0.1
                        client_address = request.META['REMOTE_ADDR']

                    # Log de INACTIVAR VALOR ASIGNATURA
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(costo).pk,
                        object_id       = costo.id,
                        object_repr     = force_str(costo),
                        action_flag     = CHANGE,
                        change_message  = 'Valor de Asignatura Inactivado '+ elimina_tildes(costo.asignaturamalla.malla.carrera.nombre) + ' Asignatura: ' + elimina_tildes(costo.asignaturamalla.asignatura.nombre) +' (' + client_address + ')' )

                    return HttpResponse(json.dumps({"result": "ok"}),content_type="application/json")

                except Exception as e:
                    return HttpResponse(json.dumps({"result": "bad","error":str(e)}),content_type="application/json")

        else:
            if "error" in request.GET:
                data['error'] = request.GET['error']
            if 'action' in request.GET:
                action = request.GET['action']
                if action=='view':
                    data['malla'] = Malla.objects.get(pk=request.GET['id'])
                    data['nivelesdemallas'] = NivelMalla.objects.all().order_by('nombre')
                    data['ejesformativos'] = EjeFormativo.objects.all().order_by('nombre')
                    data['asignaturasmallas'] = AsignaturaMalla.objects.filter(malla=data['malla'])
                    resumenNiveles = [{'id':x.id, 'horas': x.total_horas(data['malla']), 'creditos': x.total_creditos(data['malla'])} for x in NivelMalla.objects.all().order_by('nombre')]
                    data['resumenes'] = resumenNiveles
                    data['title'] = "Ver Malla Curricular : "+data['malla'].carrera.nombre
                    return render(request ,"mallas/ver_mallasbs.html" ,  data)

                #OCastillo 04-11-2021 para consultar los valores por asignatura registrados
                elif action=='vervalores':
                    asigmalla = AsignaturaMalla.objects.filter(id=request.GET['id'])
                    costos=CostoAsignatura.objects.filter(asignaturamalla=asigmalla).order_by('-fecha')
                    data['costos'] = costos
                    return render(request ,"mallas/valores.html" ,  data)
                else:
                    return HttpResponseRedirect("/cons_mallasbs")
            else:
                data['mallas'] = Malla.objects.all().order_by('-inicio')
                return render(request ,"mallas/cons_mallasbs.html" ,  data)