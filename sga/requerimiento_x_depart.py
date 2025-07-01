from datetime import datetime
import json
import os
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.utils.encoding import force_str
from settings import EMAIL_ACTIVE, MEDIA_URL, MEDIA_ROOT
from sga.commonviews import addUserData, ip_client_address
from sga.models import RequerimientoDepart, Departamento, Persona, DepartamentoGroup, DetalleRequerimiento

class MiPaginador(Paginator):
    def __init__(self, object_list, per_page, orphans=0, allow_empty_first_page=True, rango=5):
        super(MiPaginador,self).__init__(object_list, per_page, orphans=orphans, allow_empty_first_page=allow_empty_first_page)
        self.rango = rango
        self.paginas = []
        self.primera_pagina = False
        self.ultima_pagina = False

    def rangos_paginado(self, pagina):
        left = pagina - self.rango
        right = pagina + self.rango
        if left<1:
            left=1
        if right>self.num_pages:
            right = self.num_pages
        self.paginas = range(left, right+1)
        self.primera_pagina = True if left>1 else False
        self.ultima_pagina = True if right<self.num_pages else False
        self.ellipsis_izquierda = left-1
        self.ellipsis_derecha = right+1


def view(request):
    try:
        if request.method == "POST":
            action = request.POST["action"]
            if action == "addrequer":
                try:
                    persona = Persona.objects.filter(usuario=request.user)[:].get()
                    if RequerimientoDepart.objects.filter(novedad = request.POST["requerimiento"],departamento__id = request.POST["departamento"],persona=persona).exists():
                        return HttpResponse(json.dumps({"result": "ok"}),content_type="application/json")
                    requerimientodepart =RequerimientoDepart(novedad = request.POST["requerimiento"],
                                                        departamento_id = request.POST["departamento"],
                                                        persona=persona,
                                                        fechaingre=datetime.now())
                    requerimientodepart.save()
                    if "archivo" in request.FILES:
                        requerimientodepart.archivo = request.FILES["archivo"]
                        requerimientodepart.save()
                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de ABRIR CLASE
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(requerimientodepart).pk,
                        object_id       = requerimientodepart.id,
                        object_repr     = force_str(requerimientodepart),
                        action_flag     = ADDITION,
                        change_message  = 'Ingreso de Requerimiento (' + client_address + ')' )

                    if EMAIL_ACTIVE:
                        try:
                            requerimientodepart.email_requerimiento("add",request,client_address)
                        except Exception as e:
                            pass
                    return HttpResponse(json.dumps({"result": "ok"}),content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({"result": "bad"}),content_type="application/json")
            elif action == "edditrequer":
                try:
                    persona = Persona.objects.filter(usuario=request.user)[:].get()
                    requerimientodepart =RequerimientoDepart.objects.get(id = request.POST["idrequer"])
                    requerimientodepart.novedad = request.POST["requerimiento"]
                    requerimientodepart.departamento_id = request.POST["departamento"]
                    requerimientodepart.persona=persona
                    requerimientodepart.fechaingre=datetime.now()
                    requerimientodepart.save()

                    if "archivo" in request.FILES:
                        if requerimientodepart.archivo:
                            if (MEDIA_ROOT + '/' + str(requerimientodepart.archivo)):
                                os.remove(MEDIA_ROOT + '/' + str(requerimientodepart.archivo))
                        requerimientodepart.archivo = request.FILES["archivo"]
                        requerimientodepart.save()
                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de ABRIR CLASE
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(requerimientodepart).pk,
                        object_id       = requerimientodepart.id,
                        object_repr     = force_str(requerimientodepart),
                        action_flag     = CHANGE,
                        change_message  = 'Modificacion de Requerimiento (' + client_address + ')' )

                    if EMAIL_ACTIVE:
                        try:
                            requerimientodepart.email_requerimiento("add",request,client_address)
                        except Exception as e:
                            pass
                    return HttpResponse(json.dumps({"result": "ok"}),content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({"result": "bad"}),content_type="application/json")

            elif action == "responder":
                try:
                    detallerequerimiento = DetalleRequerimiento.objects.get(id = request.POST["idetall"])
                    detallerequerimiento.respuestarequer = request.POST["respuesta"]
                    detallerequerimiento.fechares = datetime.now()
                    detallerequerimiento.save()
                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de ABRIR CLASE
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(detallerequerimiento).pk,
                        object_id       = detallerequerimiento.id,
                        object_repr     = force_str(detallerequerimiento),
                        action_flag     = ADDITION,
                        change_message  = 'Responder Consulta (' + client_address + ')' )

                    if EMAIL_ACTIVE:
                        try:
                            detallerequerimiento.email_detrequerimiento("respuest",request,client_address)
                        except Exception as e:
                            pass
                    return HttpResponse(json.dumps({"result": "ok"}),content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({"result": "bad"}),content_type="application/json")
        else:
            data = {"title":"Requerimiento"}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET["action"]
                if action == "detconsult":
                    data = {}
                    requerimientodepart = RequerimientoDepart.objects.get(id=request.GET["idreq"])
                    data["requerimientodepart"] = requerimientodepart
                    data["detallerequerimiento"] = DetalleRequerimiento.objects.filter(requerimiento=requerimientodepart)
                    return render(request ,"requerimiento/detarequerimiento.html" ,  data)
                if action == "reenviar":
                    try:
                        requerimientodepart = RequerimientoDepart.objects.get(id=request.GET["idreq"])
                        if EMAIL_ACTIVE:
                            #Obtain client ip address
                            client_address = ip_client_address(request)
                            requerimientodepart.email_requerimiento("add",request,client_address)
                        return HttpResponseRedirect("/requerimiento")
                    except Exception as e:
                        return HttpResponseRedirect("/?info=error "+str(e))

            else:
                persona = data['persona']
                data["requerimiento"] = RequerimientoDepart.objects.filter(persona__usuario__groups__in=persona.usuario.groups.filter().values("id")).distinct("id").order_by("-fechaingre")
                search = None
                pendiente = None
                finalizado = None
                dpto = None
                if 'dpto' in request.GET:
                    dpto = request.GET['dpto']
                if 's' in request.GET:
                    search = request.GET['s']

                if 'f' in request.GET:
                    finalizado = request.GET['f']

                if 'p' in request.GET:
                    pendiente = request.GET['p']

                if search:
                    requerimiento = RequerimientoDepart.objects.filter(novedad__icontains=search,persona__usuario__groups__in=persona.usuario.groups.filter().values("id")).distinct("id").order_by("-fechaingre")
                elif finalizado:
                    requerimiento = RequerimientoDepart.objects.filter(finalizado=True,persona__usuario__groups__in=persona.usuario.groups.filter().values("id")).distinct("id").order_by("-fechaingre")

                elif pendiente:
                    requerimiento = RequerimientoDepart.objects.filter(finalizado=False,persona__usuario__groups__in=persona.usuario.groups.filter().values("id")).distinct("id").order_by("-fechaingre")

                elif dpto:
                    requerimiento =  RequerimientoDepart.objects.filter(departamento__id=dpto,persona__usuario__groups__in=persona.usuario.groups.filter().values("id")).distinct("id").order_by("-fechaingre")
                    data['deparid'] = dpto if dpto else ""
                    data['depar'] = Departamento.objects.get(pk=dpto) if dpto else ""
                else:
                    requerimiento = RequerimientoDepart.objects.filter(persona__usuario__groups__in=persona.usuario.groups.filter().values("id")).distinct("id").order_by("-fechaingre")
                paging = MiPaginador(requerimiento, 30)
                p = 1
                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                    page = paging.page(p)
                except:
                    page = paging.page(1)


                data['paging'] = paging
                data['rangospaging'] = paging.rangos_paginado(p)
                data['page'] = page
                data["requerimiento"] = page.object_list
                data["departamento"] = Departamento.objects.filter(departamentogroup__claseincide=False).exclude(departamentogroup__departamento=None).distinct("id")
                data['search'] = search if search else ""
                data['pendiente'] = pendiente if pendiente else ""
                data['finalizado'] = finalizado if finalizado else ""
                return render(request ,"requerimiento/requerimiento.html" ,  data)
    except Exception as e:
        return HttpResponseRedirect("/?info"+str(e))

def resps(request):
    try:
        if request.method == "POST":
            action = request.POST["action"]
            if action == "consultar":
                try:
                    requerimientodepart =RequerimientoDepart.objects.get(id = request.POST["idrequer"])

                    detallerequerimiento = DetalleRequerimiento(requerimiento = requerimientodepart,
                                                            preguntadepart = request.POST["consulta"],fechapreg=datetime.now())
                    detallerequerimiento.save()
                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de ABRIR CLASE
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(detallerequerimiento).pk,
                        object_id       = detallerequerimiento.id,
                        object_repr     = force_str(detallerequerimiento),
                        action_flag     = ADDITION,
                        change_message  = 'Consulta de Requerimiento (' + client_address + ')' )

                    if EMAIL_ACTIVE:
                        try:
                            detallerequerimiento.email_detrequerimiento("consult",request,client_address)
                        except Exception as e:
                            pass
                    return HttpResponse(json.dumps({"result": "ok"}),content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({"result": "bad"}),content_type="application/json")
            elif action == "finalizar":
                try:

                    requerimientodepart =RequerimientoDepart.objects.get(id = request.POST["idrequer"])
                    requerimientodepart.observacion = request.POST["consulta"]
                    requerimientodepart.finalizado = True
                    if "archivofin" in request.FILES:
                        if requerimientodepart.archivofin:
                            if (MEDIA_ROOT + '/' + str(requerimientodepart.archivofin)):
                                os.remove(MEDIA_ROOT + '/' + str(requerimientodepart.archivofin))
                        requerimientodepart.archivofin = request.FILES["archivofin"]
                        requerimientodepart.save()
                    requerimientodepart.fechafinal = datetime.now()
                    requerimientodepart.save()

                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de ABRIR CLASE
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(requerimientodepart).pk,
                        object_id       = requerimientodepart.id,
                        object_repr     = force_str(requerimientodepart),
                        action_flag     = CHANGE,
                        change_message  = 'Finalizacion de Requerimiento (' + client_address + ')' )

                    if EMAIL_ACTIVE:
                        try:
                            requerimientodepart.email_requerimiento("final",request,client_address)
                        except Exception as e:
                            pass
                    return HttpResponse(json.dumps({"result": "ok"}),content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({"result": "bad"}),content_type="application/json")
        else:
            data = {"title":"Requerimiento"}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET["action"]
                if action == "detconsult":
                    data = {}
                    requerimientodepart = RequerimientoDepart.objects.get(id=request.GET["idreq"])
                    data["requerimientodepart"] = requerimientodepart
                    data["detallerequerimiento"] = DetalleRequerimiento.objects.filter(requerimiento=requerimientodepart)
                    data["consultamod"] = True
                    return render(request ,"requerimiento/detarequerimiento.html" ,  data)
            else:
                persona = data['persona']
                search = None
                pendiente = None
                finalizado = None
                if 's' in request.GET:
                    search = request.GET['s']

                if 'f' in request.GET:
                    finalizado = request.GET['f']

                if 'p' in request.GET:
                    pendiente = request.GET['p']

                departamento = DepartamentoGroup.objects.filter(group__id__in=persona.usuario.groups.filter().values("id"),claseincide=False).distinct("departamento").values("departamento")

                if search:
                    data["requerimiento"] = RequerimientoDepart.objects.filter(novedad__icontains=search,departamento__in=departamento).order_by("-fechaingre")
                elif finalizado:
                    data["requerimiento"] = RequerimientoDepart.objects.filter(finalizado=True,departamento__in=departamento).order_by("-fechaingre")

                elif pendiente:
                    data["requerimiento"] = RequerimientoDepart.objects.filter(finalizado=False,departamento__in=departamento).order_by("-fechaingre")
                else:
                    data["requerimiento"] = RequerimientoDepart.objects.filter(departamento__in=departamento).order_by("-fechaingre")
                data["departamento"] = Departamento.objects.all()
                data['search'] = search if search else ""
                data['pendiente'] = pendiente if pendiente else ""
                data['finalizado'] = finalizado if finalizado else ""
                return render(request ,"requerimiento/requerimientorespuest.html" ,  data)
    except Exception as e:
        return HttpResponseRedirect("/?info"+str(e))
