from datetime import datetime, timedelta, time
import json
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from settings import EMAIL_ACTIVE
from sga.commonviews import addUserData
from sga.forms import AulaAdministraForm
from sga.models import AulaAdministra, Clase, Actividad


def view(request):
    try:
        if request.method == 'POST':
            action = request.POST['action']
            if action == "disponibleaula":
                try:
                    fecha = datetime(int(request.POST['fecha'].split("-")[2]),int(request.POST['fecha'].split("-")[1]),int(request.POST['fecha'].split("-")[0]),0,0,0)
                    if request.POST['fin'] != '' and request.POST['inicio'] != '':
                        if AulaAdministra.objects.filter(Q(aula__id=request.POST['aulaid']),Q(fecha=fecha),
                                                         (Q(horainicio__lte=request.POST['inicio']) & Q(horafin__gte=request.POST['inicio'])) |
                                                         (Q(horainicio__lte=request.POST['fin']) & Q(horafin__gte=request.POST['fin'])) |
                                                         (Q(horainicio__gte=request.POST['inicio']) & Q(horafin__lte=request.POST['fin']))).exclude(id=request.POST['idaulaadmin']).exists():
                            return HttpResponse(json.dumps({"result":"bad","msn":"El auditorio se encuentra ocupado cambiar la fecha o la Hora de inicio y fin."}),content_type="application/json")
                    else:
                        if AulaAdministra.objects.filter(aula__id=request.POST['aulaid'],fecha=fecha).exclude(id=request.POST['idaulaadmin']).exists():

                            return HttpResponse(json.dumps({"result":"bad","msn":"El auditorio se encuentra ocupado cambiar la fecha o la Hora de inicio y fin."}),content_type="application/json")

                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
            elif action == "addauditorio":
                try:
                    fecha = datetime(int(request.POST['fecha'].split("-")[2]),int(request.POST['fecha'].split("-")[1]),int(request.POST['fecha'].split("-")[0]),0,0,0)
                    if request.POST['idaulaadmin'] == "0":
                        if request.POST['horafin'] == '' or request.POST['horainicio'] == '':
                            if AulaAdministra.objects.filter(aula__id=request.POST['aula'],fecha=fecha).exists():
                                return HttpResponseRedirect('/aula_administrador?error=El Auditorio se encuentra ocupado cambiar la fecha.')
                            aulaadministra = AulaAdministra(
                                                aula_id = request.POST['aula'],
                                                motivo = request.POST['motivo'],
                                                fecha = fecha,
                                                horainicio = "00:00",
                                                horafin = "23:59",
                                                user = request.user,
                                                fechaingreso = datetime.now())
                        else:
                            horainicio = time(int(request.POST['horainicio'].split(':')[0]),int(request.POST['horainicio'].split(':')[1]))
                            horafin = time(int(request.POST['horafin'].split(':')[0]),int(request.POST['horafin'].split(':')[1]))
                            if request.POST['horafin'] < request.POST['horainicio']:
                                return HttpResponseRedirect('/aula_administrador?error=La Hora de inicio debe de ser menor a la hora de fin.')
                            if AulaAdministra.objects.filter(Q(aula__id=request.POST['aula']),Q(fecha=fecha),
                                                             (Q(horainicio__lte=horainicio) & Q(horafin__gte=horainicio)) |
                                                             (Q(horainicio__lte=horafin) & Q(horafin__gte=horafin)) |
                                                             (Q(horainicio__gte=horainicio) & Q(horafin__lte=horafin))).exists():
                                return HttpResponseRedirect('/aula_administrador?error=El Auditorio se encuentra ocupado cambiar la fecha o la Hora de inicio y fin.')
                            aulaadministra = AulaAdministra(
                                                aula_id = request.POST['aula'],
                                                motivo = request.POST['motivo'],
                                                fecha = fecha,
                                                horainicio = request.POST['horainicio'],
                                                horafin = request.POST['horafin'],
                                                user = request.user,
                                                fechaingreso = datetime.now())
                    else:
                        aulaadministra = AulaAdministra.objects.filter(id=request.POST["idaulaadmin"])[:1].get()
                        if request.POST['horafin'] == '' or request.POST['horainicio'] == '':
                            if AulaAdministra.objects.filter(Q(aula=aulaadministra.aula),Q(fecha=fecha),
                                                             (Q(horainicio__lte='00:00') & Q(horafin__gte='00:00')) |
                                                             (Q(horainicio__lte='23:59') & Q(horafin__gte='23:59')) |
                                                             (Q(horainicio__gte='00:00') & Q(horafin__lte='23:59'))).exclude(id=aulaadministra.id).exists():
                                return HttpResponseRedirect('/aula_administrador?error=El Auditorio se encuentra ocupado cambiar la fecha o la Hora de inicio y fin.')
                            aulaadministra.motivo = request.POST['motivo']
                            aulaadministra.fecha = fecha
                            aulaadministra.fechaingreso = datetime.now()
                            aulaadministra.horainicio = '00:00'
                            aulaadministra.horafin = '23:59'
                            aulaadministra.user = request.user
                        else:
                            horainicio = time(int(request.POST['horainicio'].split(':')[0]),int(request.POST['horainicio'].split(':')[1]))
                            horafin = time(int(request.POST['horafin'].split(':')[0]),int(request.POST['horafin'].split(':')[1]))
                            if request.POST['horafin'] < request.POST['horainicio']:
                                return HttpResponseRedirect('/aula_administrador?error=La Hora de inicio debe de ser menor a la hora de fin.')
                            if AulaAdministra.objects.filter(Q(aula__id=request.POST['aula']),Q(fecha=fecha),
                                                             (Q(horainicio__lte=horainicio) & Q(horafin__gte=horainicio)) |
                                                             (Q(horainicio__lte=horafin) & Q(horafin__gte=horafin)) |
                                                             (Q(horainicio__gte=horainicio) & Q(horafin__lte=horafin))).exclude(id=aulaadministra.id).exists():
                               return HttpResponseRedirect('/aula_administrador?error=El Auditorio se encuentra ocupado cambiar la fecha o la Hora de inicio y fin.')
                            aulaadministra.motivo = request.POST['motivo']
                            aulaadministra.fecha = fecha
                            aulaadministra.fechaingreso = datetime.now()
                            aulaadministra.horainicio = horainicio
                            aulaadministra.horafin = horafin
                            aulaadministra.user = request.user
                    if 'actividad' in request.POST:
                        aulaadministra.actividad_id=request.POST['actividad']
                    aulaadministra.save()
                    if not EMAIL_ACTIVE:
                        aulaadministra.correo_adminauditorio()
                    return HttpResponseRedirect('/aula_administrador')
                except Exception as ex:
                    return HttpResponseRedirect('/aula_administrador?error=Error en el ingreso vuelva a intentarlo')
        else:
            data = {'title':'Administracion de Aulas'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']
                if action == "eliminar":
                    aulaadministra = AulaAdministra.objects.filter(id=request.GET['id'])[:1].get()
                    aulaadministra.delete()
                    return HttpResponseRedirect('/aula_administrador')
                elif action== 'veractividad':
                    try:
                        data={}
                        actividad = Actividad.objects.get(pk=request.GET['act'])
                        data['actividad'] = actividad

                        return render(request ,"aula_administracion/ver_actividad.html" ,  data)
                    except Exception as ex :
                        return HttpResponse(json.dumps({'result':'bad', "error": str(ex)}),content_type="application/json")

            else:
                aulaadministra = AulaAdministra.objects.filter().order_by('-fecha','horainicio')
                data['aulaadministra'] =aulaadministra
                form = AulaAdministraForm(initial={'fecha':datetime.now().date()+ timedelta(days=1)})
                form.for_aulafilter()
                data['form1'] = form
                data['fechaactual'] = datetime.now().date()
                if 'error' in request.GET:
                    data['error'] = request.GET['error']
                return render(request ,"aula_administracion/aula_administracion.html" ,  data)
            return HttpResponseRedirect('/')
    except Exception as ex:
        return HttpResponseRedirect('/?info='+str(ex))
