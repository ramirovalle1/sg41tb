import json
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from decorators import secure_module
from sga.commonviews import addUserData,ip_client_address
from sga.forms import DescuentosporConvenioForm,IndicadoresExamComplexivoForm,MotivoInactivarAtrasoDocenteForm, SupervisorGruposForm
from sga.models import RubroOtro, DescuentosporConvenio, \
    EmpresaConvenio,IndicEvaluacionExamen,Carrera,Coordinacion, RolPago, LeccionGrupo,MotivoJustificarAperturaTardiaClases, SupervisorGrupos, User, Persona, Group
from settings import COORDINACION_UASSS
from django.contrib.admin.models import LogEntry, CHANGE, DELETION, ADDITION
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_str
from sga.reportes import elimina_tildes
from datetime import datetime
from django.db.models.query_utils import Q


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
@transaction.atomic()
def view(request):
    try:
        if request.method == 'POST':
            action = request.POST['action']
            if action == "editrubrootro":
                try:
                    if RubroOtro.objects.filter(id=request.POST['idrubrootro']).exists():
                        rubrootro = RubroOtro.objects.filter(id=request.POST['idrubrootro'])[:1].get()
                        rubrootro.descripcion = request.POST['descripcion']
                        rubrootro.save()
                        return HttpResponse(json.dumps({"result": "ok","id":str(rubrootro.rubro.id)}),content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({"result": "bad"}),content_type="application/json")

            elif action == 'add_descuento':
                try:
                    print(request.POST)
                    if 'activo' in request.POST:
                        activo = True
                    else:
                        activo = False
                    empresaconvenio = EmpresaConvenio.objects.get(pk=request.POST['empresaconvenio'])
                    if request.POST['iddescuento'] == '':
                        descuento = DescuentosporConvenio(empresaconvenio=empresaconvenio,
                                                          descripcion=request.POST['descripcion'],
                                                          descuento=request.POST['descuento'],
                                                          activo=activo)
                        descuento.save()
                    else:
                        if DescuentosporConvenio.objects.filter(pk=request.POST['iddescuento']).exists():
                            descuento = DescuentosporConvenio.objects.get(pk=request.POST['iddescuento'])
                            descuento.empresaconvenio = empresaconvenio
                            descuento.activo = activo
                            descuento.descripcion = request.POST['descripcion']
                            descuento.descuento = request.POST['descuento']
                            descuento.save()
                    return HttpResponseRedirect("/mantenimiento?action=descuentosporconvenios")
                except Exception as ex:
                    print(ex)
                    return HttpResponseRedirect("/mantenimiento?error=1")

            elif action == 'eliminar_descuento':
                print(request.POST)
                descuento = DescuentosporConvenio.objects.get(pk=request.POST['iddescuento'])
                descuento.delete()
                return HttpResponse(json.dumps({"result": "ok"}),content_type="application/json")

            #OCastillo 16-08-2022 adicionar indicadores para examenes complexivos
            elif action == 'add_indicador':
                try:
                    print(request.POST)
                    carrera=None
                    coordinacion=Coordinacion.objects.get(pk=COORDINACION_UASSS)
                    if len(request.POST['carrera']) >0:
                        carrera=Carrera.objects.get(pk=request.POST['carrera'])
                        coordinacion=carrera.coordinacion_pertenece()
                    if 'estado' in request.POST:
                        activo = True
                    else:
                        activo = False
                    if request.POST['idindicador'] == '':
                        indicador = IndicEvaluacionExamen(descripcion = elimina_tildes(request.POST['descripcion'].upper()),
                                    escala = request.POST['escala'],
                                    carrera = carrera,
                                    coordinacion=coordinacion,estado=activo)
                        indicador.save()
                        mensaje='Se ha adicionado'
                    else:
                        indicador= IndicEvaluacionExamen.objects.get(pk = request.POST['idindicador'])
                        indicador.descripcion=elimina_tildes(request.POST['descripcion'].upper())
                        indicador.carrera=carrera
                        indicador.escala=request.POST['escala']
                        indicador.coordinacion=coordinacion
                        indicador.estado=activo
                        indicador.save()
                        mensaje='Se ha modificado'

                    #Obtain client ip address
                    client_address = ip_client_address(request)
                    # Log de Adicionar o modificar indicador de complexivo
                    LogEntry.objects.log_action(
                       user_id         = request.user.pk,
                       content_type_id = ContentType.objects.get_for_model(indicador).pk,
                       object_id       = indicador.id,
                       object_repr     = force_str(indicador),
                       action_flag     = ADDITION,
                       change_message  = mensaje+' Indicador Complexivo (' + client_address + ')' )
                    return HttpResponseRedirect("/mantenimiento?action=adminexamencomplexivo")
                except Exception as ex:
                    print(ex)
                    return HttpResponseRedirect("/mantenimiento?error=1")

            #OCastillo 03-10-2023 adicionar motivo inactivacion apertura tardia clase docente
            elif action == 'add_motivo':
                try:
                    leccion= LeccionGrupo.objects.get(pk = request.POST['idleccion'])
                    leccion.descuentoporatraso=False
                    leccion.save()

                    motivo=MotivoJustificarAperturaTardiaClases(lecciongrupo=leccion,motivo=elimina_tildes(request.POST['motivo']),usuario=request.user,fecha=datetime.now())
                    motivo.save()
                    #Obtain client ip address
                    client_address = ip_client_address(request)
                    # Log de Adicionar justificacion atraso
                    LogEntry.objects.log_action(
                       user_id         = request.user.pk,
                       content_type_id = ContentType.objects.get_for_model(leccion).pk,
                       object_id       = leccion.id,
                       object_repr     = force_str(leccion),
                       action_flag     = ADDITION,
                       change_message  = ' Se ha quitado multa por clase abierta a destiempo (' + client_address + ')' )
                    return HttpResponseRedirect("/mantenimiento?action=adminclasesconatrasos")
                except Exception as ex:
                    print(ex)
                    return HttpResponseRedirect("/mantenimiento?error=1")
            elif action == 'add_supervisorgrupo':
                try:
                    print(request.POST)

                    if request.POST['idsupervisorgrupo'] == '':
                        jefeg = SupervisorGrupos(supervisor = Persona.objects.get(id = int(request.POST['supervisor'])),usuario=request.user, director = Persona.objects.get(id = int(request.POST['director'])), activo = True)
                        jefeg.save()
                        for g in request.POST.getlist('grupo'):
                            jefeg.grupo.add(g)

                    else:
                        if SupervisorGrupos.objects.filter(pk=request.POST['idsupervisorgrupo']).exists():
                            jefeg = SupervisorGrupos.objects.get(pk=request.POST['idsupervisorgrupo'])
                            jefeg.supervisor =  Persona.objects.get(id = int(request.POST['supervisor']))
                            jefeg.director =  Persona.objects.get(id = int(request.POST['director']))
                            jefeg.usuario_modifica = request.user
                            jefeg.save()
                            for g in jefeg.grupo.all():
                                jefeg.grupo.remove(g)
                            for g in request.POST.getlist('grupo'):
                                jefeg.grupo.add(g)

                    return HttpResponseRedirect("/mantenimiento?action=supervisordepartamento")
                except Exception as ex:
                    print(ex)
                    return HttpResponseRedirect("/mantenimiento?error=1")

        else:
            data = {'title':'Mantenimiento'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']

                if action == 'rubrootro':
                    search = None
                    rubrootro = None
                    if 's' in request.GET:
                        search = request.GET['s']
                        data['search'] = search
                    if search:
                        rubrootro = RubroOtro.objects.filter(rubro__id=search)
                    if rubrootro:
                        paging = MiPaginador(rubrootro, 30)
                        p = 1
                        try:
                            if 'page' in request.GET:
                                p = int(request.GET['page'])
                                # if band==0:
                                #     inscripciones = Inscripcion.objects.all().order_by('persona__apellido1')
                                paging = MiPaginador(rubrootro, 30)
                            page = paging.page(p)
                        except Exception as ex:
                            page = paging.page(1)

                        data['paging'] = paging
                        data['rangospaging'] = paging.rangos_paginado(p)
                        data['page'] = page

                        data['rubrootros'] = page.object_list
                    return render(request ,"mantenimiento/rubrootro.html" ,  data)

                elif action == 'descuentosporconvenios':
                    descuentos = DescuentosporConvenio.objects.all().order_by('-id')
                    data['descuentos'] = descuentos
                    data['form'] = DescuentosporConvenioForm
                    return render(request ,"mantenimiento/descuentosporconvenios.html" ,  data)

                elif action == 'adminexamencomplexivo':
                    search = None
                    indicador = None
                    if 's' in request.GET:
                        search = request.GET['s']
                        data['search'] = search
                    if search:
                        indicador = IndicEvaluacionExamen.objects.filter(carrera__nombre__icontains=search)
                    else:
                        indicador = IndicEvaluacionExamen.objects.filter(coordinacion__id=COORDINACION_UASSS,teorico=False).order_by('carrera','descripcion')
                    if indicador:
                        paging = MiPaginador(indicador, 30)
                        p = 1
                        try:
                            if 'page' in request.GET:
                                p = int(request.GET['page'])
                                paging = MiPaginador(indicador, 30)
                            page = paging.page(p)
                        except Exception as ex:
                            page = paging.page(1)

                        data['paging'] = paging
                        data['rangospaging'] = paging.rangos_paginado(p)
                        data['page'] = page

                        data['indicador'] = page.object_list
                    data['indicadores'] = indicador
                    data['form'] = IndicadoresExamComplexivoForm()
                    return render(request ,"mantenimiento/mantenimientoindicadores.html" ,  data)

                elif action == 'adminclasesconatrasos':
                    search = None
                    lecciones = []
                    apt = []
                    rolpago = RolPago.objects.filter().order_by('-id')[:1].get()
                    apertura_tardia=LogEntry.objects.filter(change_message__icontains='Abierta Clase Docente',action_time__gte=rolpago.inicio,action_time__lte=rolpago.fin).order_by('-action_time')
                    for apertura in apertura_tardia:
                        apt.append((int(apertura.object_id)))

                    if 's' in request.GET:
                        search = request.GET['s']
                        data['search'] = search

                    if search:
                        ss = search.split(' ')
                        while '' in ss:
                            ss.remove('')
                        if len(ss)==1:
                            if LeccionGrupo.objects.filter(Q(materia__nivel__carrera__nombre__icontains=search)|Q(profesor__persona__apellido1__icontains=search)|Q(profesor__persona__apellido2__icontains=search) ,fecha__gte=rolpago.inicio, fecha__lte=rolpago.fin,id__in=apt).exists():
                                lecciones=LeccionGrupo.objects.filter(Q(materia__nivel__carrera__nombre__icontains=search)|Q(profesor__persona__apellido1__icontains=search)|Q(profesor__persona__apellido2__icontains=search),fecha__gte=rolpago.inicio, fecha__lte=rolpago.fin,id__in=apt).order_by('-fecha')
                        else:
                            lecciones=LeccionGrupo.objects.filter(Q(profesor__persona__apellido1__icontains=ss[0])|Q(profesor__persona__apellido2__icontains=ss[1]),fecha__gte=rolpago.inicio, fecha__lte=rolpago.fin,id__in=apt).order_by('-fecha')
                    else:
                        if LeccionGrupo.objects.filter(fecha__gte=rolpago.inicio, fecha__lte=rolpago.fin,id__in=apt).exists():
                            lecciones=LeccionGrupo.objects.filter(fecha__gte=rolpago.inicio, fecha__lte=rolpago.fin,id__in=apt).order_by('-fecha')

                    if lecciones:
                        paging = MiPaginador(lecciones, 30)
                        p = 1
                        try:
                            if 'page' in request.GET:
                                p = int(request.GET['page'])
                                paging = MiPaginador(lecciones, 30)
                            page = paging.page(p)
                        except Exception as ex:
                            page = paging.page(1)
                        data['paging'] = paging
                        data['rangospaging'] = paging.rangos_paginado(p)
                        data['page'] = page
                        data['lecciones'] = page.object_list
                    data['lecciones'] = lecciones
                    data['form'] = MotivoInactivarAtrasoDocenteForm()
                    data['rol_pago'] = RolPago.objects.filter().order_by('-id')[:1].get()
                    return render(request ,"mantenimiento/aperturatardiaclases.html" ,  data)
                elif action == 'supervisordepartamento':
                   try:
                        search = None
                        supervdep = None
                        if 's' in request.GET:
                            search = request.GET['s']
                            data['search'] = search
                        if search:
                            supervdep = SupervisorGrupos.objects.filter(supervisor__nombres__icontains = search,supervisor__apellido__icontains = search )
                        else:
                            supervdep = SupervisorGrupos.objects.filter()

                        if supervdep:
                            paging = MiPaginador(supervdep, 30)
                            p = 1
                            try:
                                if 'page' in request.GET:
                                    p = int(request.GET['page'])
                                page = paging.page(p)
                            except Exception as ex:
                                page = paging.page(1)

                            data['paging'] = paging
                            data['rangospaging'] = paging.rangos_paginado(p)
                            data['page'] = page

                            data['supervdep'] = page.object_list
                        data['form'] = SupervisorGruposForm
                        return render(request ,"mantenimiento/supervisorgrupos.html" ,  data)
                   except Exception as ex:
                       print(ex)

            else:
                return render(request ,"mantenimiento/menu.html" ,  data)

    except Exception as e:
        print(e)
        return HttpResponseRedirect('/info='+str(e))