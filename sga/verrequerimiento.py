from datetime import datetime
import json
from django.contrib.admin.models import ADDITION, CHANGE, LogEntry, DELETION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
from decorators import secure_module
from sga.commonviews import addUserData, ip_client_address
from sga.models import RequerimientoAsistentes, RequerimientoSoporte, DepartamentoGroup, Persona


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

__author__ = 'jjurgiles'


@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    try:
        if request.method == 'POST':
            action = request.POST['action']
            if action == 'existe':
                try:
                    if not RequerimientoAsistentes.objects.filter(asistente__id=request.POST['idasist'],jefe__usuario=request.user).exists():
                        return HttpResponse(json.dumps({'result': 'ok'}), content_type="application/json")
                    return HttpResponse(json.dumps({'result': 'bad', 'mensaj':'EL tutor ya existe para este nivel'}), content_type="application/json")
                except Exception as e:
                    print("Error JSON existe tutorcongreso"+str(e))
                    return HttpResponse(json.dumps({'result': 'bad','mensaj':'Error al guardar los datos'}), content_type="application/json")
            elif action == 'guardar':
                try:
                    jefe = Persona.objects.filter(usuario=request.user)[:1].get()
                    if int(request.POST['editar']) == 0:
                        asistente = RequerimientoAsistentes(jefe = jefe,
                                                      asistente_id = request.POST['idasist'],
                                                      fecha = datetime.now())
                        actflag = ADDITION
                        mens = 'Agregado Asistente'
                    else:
                        asistente = RequerimientoAsistentes.objects.get(id=request.POST['editar'])
                        asistente.asistente_id = request.POST['idasist']
                        asistente.fecha = datetime.now()
                        actflag = CHANGE
                        mens = 'Editado Asistente'
                    asistente.save()

                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de ADICIONAR GRUPO
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(asistente).pk,
                        object_id       = asistente.id,
                        object_repr     = force_str(asistente),
                        action_flag     = actflag,
                        change_message  = mens+' (' + client_address + ')'  )

                    return HttpResponse(json.dumps({'result': 'ok'}), content_type="application/json")
                except Exception as e:
                    print("Error JSON guardar tutorcongreso"+str(e))
                    return HttpResponse(json.dumps({'result': 'bad','mensaj':'Error al guardar los datos'}), content_type="application/json")

            elif action == 'eliminar':
                try:
                    requerimiento = RequerimientoAsistentes.objects.get(id=request.POST['idreq'])

                    requerimiento.delete()
                    client_address = ip_client_address(request)

                    #Log de ADICIONAR INSCRIPCION
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(requerimiento).pk,
                        object_id       = requerimiento.id,
                        object_repr     = force_str(requerimiento),
                        action_flag     = DELETION,
                        change_message  = 'REQUERIMIENTO ASISTENTE ELIMINADO  (' + client_address + ')' )
                    return HttpResponse(json.dumps({'result': 'ok','mensaje':'Registro eliminado'}), content_type="application/json")
                except Exception as e:
                    print(e)
                    return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")
        else:
            data = {'title':'Ver requerimeinto'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']
                if action=='verasitentes':
                    data = {}
                    jefe = Persona.objects.filter(usuario=request.user)[:1].get()
                    requerimientoasitentes = RequerimientoAsistentes.objects.filter(jefe=jefe)
                    data['requerimientoasitentes'] = requerimientoasitentes
                    return render(request ,"soportereque/asitentes.html" ,  data)
            else:
                personaid = RequerimientoAsistentes.objects.filter(jefe=data['persona']).values('asistente')
                data["personaasistente"] = RequerimientoAsistentes.objects.filter(jefe=data['persona'])
                if DepartamentoGroup.objects.filter(group__id__in=data['persona'].usuario.groups.all().values('id')).exists():
                    departamento = DepartamentoGroup.objects.filter(group__id__in=data['persona'].usuario.groups.all().values('id'))[:1].get().departamento
                    groupid = DepartamentoGroup.objects.filter(departamento=departamento).distinct('group').values_list('group',flat=True)
                    data['groupid'] = groupid
                    requerimientos = None
                    if 'idasis' in request.GET:
                        data['idasis']= int(request.GET['idasis'])
                        requerimientos = RequerimientoSoporte.objects.filter(persona__id=request.GET['idasis']).order_by('-fecha')
                        data['requerimientoasistente'] = RequerimientoAsistentes.objects.filter(jefe=data['persona'],asistente__id=request.GET['idasis'])[:1].get()
                    if 'sincal' in request.GET:
                        if requerimientos:
                            requerimientos = requerimientos.filter(finalizado = True,calificacion=None ).order_by('-fecha')
                        else:
                            requerimientos = RequerimientoSoporte.objects.filter(finalizado = True,persona__id__in=personaid,calificacion=None ).order_by('-fecha')
                        data['sincal'] = 1
                    elif 'finali' in request.GET:
                        if requerimientos:
                            requerimientos = requerimientos.filter(finalizado = True).order_by('-fecha')
                        else:
                            requerimientos = RequerimientoSoporte.objects.filter(finalizado = True,persona__id__in=personaid ).order_by('-fecha')
                    else:
                        if requerimientos:
                            requerimientos = requerimientos.filter(finalizado = False).order_by('-fecha')
                        else:
                            requerimientos = RequerimientoSoporte.objects.filter(finalizado = False,persona__id__in=personaid).order_by('-fecha')
                    paging = MiPaginador(requerimientos, 30)
                    p=1
                    try:
                        if 'page' in request.GET:
                            p = int(request.GET['page'])
                        page = paging.page(p)
                    except:
                        page = paging.page(1)

                    data['paging'] = paging
                    data['page'] = page
                    data['rangospaging'] = paging.rangos_paginado(p)
                    data['finali'] = "finali" if 'finali' in request.GET else ""
                    data['requerimientos'] = page.object_list
                    return render(request ,"soportereque/verrequerimiento.html" ,  data)
                return HttpResponseRedirect("/?info=No tiene un Departamento Asignado")
    except Exception as e:
        print("Error excepcion verrequerimiento "+str(e))
        return HttpResponseRedirect("/?info=error comuniquese con el administrador")
