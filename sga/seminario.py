from datetime import datetime, timedelta
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
import json
from django.db.models import Q
from django.forms import model_to_dict
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
from decorators import secure_module
from sga.forms import LugarRecaudacionForm, GrupoSeminarioForm
from sga.models import LugarRecaudacion, GrupoSeminario, InscripcionSeminario, RubroOtro
from sga.commonviews import addUserData, ip_client_address

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

@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    if request.method=='POST':
        if 'action' in request.POST:
            action = request.POST['action']
            if action == 'buscar':
                punto = request.POST['punto']
                puntos = ''
                if LugarRecaudacion.objects.filter(puntoventa = punto,activa=True ).exists():
                    for p in LugarRecaudacion.objects.filter(puntoventa = punto ,activa=True):
                        puntos = puntos + ' - ' +p.nombre
                    fac =str( p.numerofact)
                    cre = str(p.numeronotacre)
                    dir = str(p.direccion)

                    return HttpResponse(json.dumps({'result':'ok', "puntos": str(puntos),'ncre':cre,'fac':fac,'dir':dir}),content_type="application/json")
                else:
                    return HttpResponse(json.dumps({'result':'bad'}),content_type="application/json")

            if action == 'buscarpersona':
                persona = request.POST['persona']
                puntos = ''
                if LugarRecaudacion.objects.filter(persona__id = persona,activa=True ).exists():
                    for p in LugarRecaudacion.objects.filter(persona__id = persona ,activa=True):
                        puntos = puntos + ' - ' +p.nombre

                    return HttpResponse(json.dumps({'result':'ok', "puntos": str(puntos)}),content_type="application/json")
                else:
                    return HttpResponse(json.dumps({'result':'bad'}),content_type="application/json")

            elif action == 'add':

                    f = GrupoSeminarioForm(request.POST)
                    if f.is_valid():
                        try:
                            if request.POST['ban'] == '1':
                                seminario = GrupoSeminario(taller=f.cleaned_data['taller'],
                                                         objetivo=f.cleaned_data['objetivo'],
                                                         inicio = f.cleaned_data['inicio'],
                                                         fin = f.cleaned_data['fin'],
                                                         horainicio = f.cleaned_data['horainicio'],
                                                         horafin = f.cleaned_data['horafin'],
                                                         capacidad = f.cleaned_data['capacidad'],
                                                         empezardesde = f.cleaned_data['empezardesde'],
                                                         carrera = f.cleaned_data['carrera'],
                                                         expositor = f.cleaned_data['expositor'],
                                                         ubicacion = f.cleaned_data['ubicacion'],
                                                         procedencia = f.cleaned_data['procedencia'],
                                                         libre = f.cleaned_data['libre'],
                                                         precio = f.cleaned_data['precio'])
                                seminario.save()
                                mensaje = 'Adicionado'

                            else:
                                seminario = GrupoSeminario.objects.get(pk=int(request.POST['seminario']))
                                seminario.taller=f.cleaned_data['taller']
                                seminario.objetivo=f.cleaned_data['objetivo']
                                seminario.inicio = f.cleaned_data['inicio']
                                seminario.fin = f.cleaned_data['fin']
                                seminario.horainicio = f.cleaned_data['horainicio']
                                seminario.horafin = f.cleaned_data['horafin']
                                seminario.capacidad = f.cleaned_data['capacidad']
                                seminario.empezardesde = f.cleaned_data['empezardesde']
                                seminario.carrera = f.cleaned_data['carrera']
                                seminario.expositor = f.cleaned_data['expositor']
                                seminario.procedencia = f.cleaned_data['procedencia']
                                seminario.libre = f.cleaned_data['libre']
                                seminario.ubicacion = f.cleaned_data['ubicacion']
                                seminario.precio = f.cleaned_data['precio']
                                seminario.save()

                                mensaje = 'Editado'
                        # Log Editar Inscripcion
                            client_address = ip_client_address(request)
                            LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(seminario).pk,
                                object_id       = seminario.id,
                                object_repr     = force_str(seminario),
                                action_flag     = CHANGE,
                                change_message  = mensaje + " Taller " +  '(' + client_address + ')' )

                            return HttpResponseRedirect("/seminario?s="+str(seminario.id))
                        except Exception as ex:
                            if request.POST['ban'] == '1':
                                return HttpResponseRedirect("seminario?action=add&error=1",)
                            else:
                                return HttpResponseRedirect("seminario?action=editar&error=1&id="+str(request.POST['seminario']),)
                    else:
                        if request.POST['ban'] == '1':
                            return HttpResponseRedirect("seminario?action=add&error=1",)
                        else:
                            return HttpResponseRedirect("seminario?action=editar&error=1&id="+str(request.POST['seminario']),)

    else:
        data = {'title': 'Talleres'}
        addUserData(request,data)
        try:
            if 'action' in request.GET:
                action = request.GET['action']

                if action == 'add':
                    data['form'] = GrupoSeminarioForm(initial={"inicio":datetime.now().date(),"fin":datetime.now().date(),"empezardesde":datetime.now().date(),"horainicio":'00:00:00',"horafin":'00:00:00'})
                    if 'error' in request.GET:
                        data['error'] = 1
                    data['ban'] =1
                    return render(request ,"seminario/add.html" ,  data)

                if action == 'ver':
                    data['seminario'] = GrupoSeminario.objects.get(pk=request.GET['id'])
                    data['inscritos'] = InscripcionSeminario.objects.filter(gruposeminario__id=request.GET['id'])

                    return render(request ,"seminario/ver.html" ,  data)

                if action == 'eliminarins':
                    i =  InscripcionSeminario.objects.get(pk=request.GET['id'])
                    rubrootro=None
                    if i.rubrootro:
                        rubrootro=i.rubrootro

                    g = i.gruposeminario.id

                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de EDITAR HORARIO CLASE
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(i).pk,
                        object_id       = i.id,
                        object_repr     = force_str(i),
                        action_flag     = CHANGE,
                        # change_message  = 'Eliminado Inscripcion Pre-Congreso (' + client_address + ')'  )
                        change_message  = 'Eliminada Inscripcion Taller (' + client_address + ')'  )
                    i.delete()
                    if rubrootro:
                        if rubrootro.rubro.puede_eliminarse():
                               rubrootro.rubro.delete()
                               rubrootro.delete()


                    return HttpResponseRedirect("/seminario?action=ver&id="+str(g))

                # if action == 'act':
                #     for ins in InscripcionSeminario.objects.filter():
                #         if ins.rubrootro:
                #             if not ins.rubrootro.rubro.cancelado and ins.rubrootro.rubro.puede_eliminarse() :
                #                 r = RubroOtro.objects.get(pk=ins.rubrootro.id)
                #                 r.rubro.delete()
                #                 r.delete()
                #                 ins.delete()
                #     for m in InscripcionSeminario.objects.filter().distinct('matricula').values('matricula'):
                #         if InscripcionSeminario.objects.filter(matricula__id=m['matricula'],rubrootro=None).exists():
                #            if not InscripcionSeminario.objects.filter(matricula__id=m['matricula']).exclude(rubrootro=None).count() >= 2:
                #                i = InscripcionSeminario.objects.get(matricula__id=m['matricula'],rubrootro=None)
                #                i.delete()
                #     return HttpResponseRedirect("/seminario")

                if action == 'actualizar':
                    try:
                        hoy =datetime.now().date()
                        for ins in InscripcionSeminario.objects.filter(gruposeminario__activo=True):
                            if ins.rubrootro:
                                if not ins.rubrootro.rubro.cancelado and ins.rubrootro.rubro.fechavence < hoy  and ins.rubrootro.rubro.puede_eliminarse() :
                                    r = RubroOtro.objects.get(pk=ins.rubrootro.id)
                                    ins.delete()
                                    r.rubro.delete()
                                    r.delete()
                                    # ins.delete()
                        for m in InscripcionSeminario.objects.filter(gruposeminario__activo=True).distinct('matricula').values('matricula'):
                            if InscripcionSeminario.objects.filter(gruposeminario__activo=True,matricula__id=m['matricula'],rubrootro=None).exists():
                               if not InscripcionSeminario.objects.filter(gruposeminario__activo=True,matricula__id=m['matricula']).exclude(rubrootro=None).count() >= 3:
                                   i = InscripcionSeminario.objects.filter(gruposeminario__activo=True,matricula__id=m['matricula'],rubrootro=None)
                                   i.delete()
                    except Exception as ex:
                        print(ex)
                    return HttpResponseRedirect("/seminario")

                # if action == 'actualiza':
                #     rubro = RubroOtro.objects.filter(descripcion__icontains='TALLER')
                #     pagado=0
                #     nopagado=0
                #     for r in rubro:
                #         inscripcion = InscripcionSeminario.objects.filter(rubrootro=None)
                #         for ins in inscripcion:
                #             i = ins.matricula.inscripcion
                #             if r.rubro.inscripcion == i :
                #                 ins.rubrootro = r
                #                 ins.save()
                #                 break
                #
                #         if r.rubro.cancelado:
                #             pagado = pagado +1
                #         else:
                #             nopagado = nopagado + 1
                #     print('no pagado:' + str(nopagado) + ' pagado:' + str(pagado))
                #
                #     return HttpResponseRedirect("/seminario")


                if action == 'eliminar':
                    i =  GrupoSeminario.objects.get(pk=request.GET['id'])
                    g = i
                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de EDITAR HORARIO CLASE
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(i).pk,
                        object_id       = i.id,
                        object_repr     = force_str(i),
                        action_flag     = CHANGE,
                        change_message  = 'Eliminado Taller (' + client_address + ')'  )
                    i.delete()

                    return HttpResponseRedirect("/seminario")

                elif action == 'editar':
                    seminario = GrupoSeminario.objects.get(pk=request.GET['id'])
                    initial = model_to_dict(seminario)
                    data['form'] = GrupoSeminarioForm(initial=initial)
                    if 'error' in request.GET:
                        data['error'] = 1
                    data['ban'] = 2
                    data['seminario'] =seminario
                    return render(request ,"seminario/add.html" ,  data)

            else:
                search = ""
                if 's' in request.GET:
                    search = request.GET['s']

                if search:
                    seminario = GrupoSeminario.objects.filter(Q(expositor__icontains=search)|Q(taller__icontains=search)|Q(id__icontains=search)).exclude(activo=False).order_by('id')
                else:

                    seminario = GrupoSeminario.objects.filter().exclude(activo=False).order_by('id')
                paging = MiPaginador(seminario, 30)
                p = 1
                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                        # if band==0:
                        #     inscripciones = Inscripcion.objects.all().order_by('persona__apellido1')
                        paging = MiPaginador(seminario, 30)
                    page = paging.page(p)
                except Exception as ex:
                    page = paging.page(1)


                data['paging'] = paging
                data['rangospaging'] = paging.rangos_paginado(p)
                data['page'] = page
                data['seminario'] = page.object_list
                data['search'] = search if search else ""
                return render(request ,"seminario/seminario.html" ,  data)
        except Exception as e:
            pass