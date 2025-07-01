from datetime import datetime, timedelta,date
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
import json
from django.db.models import Q
from django.forms import model_to_dict
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.utils.encoding import force_str
from decorators import secure_module
from sga.forms import LugarRecaudacionForm, GrupoSeminarioForm, VinculacionForm, ParticipanteForm, ParticipanteIndForm, DocenteVincForm, EvidenciaForm, ObservacionForm,BeneficiariosForm, ConvenioForm, ProgramaForm
from sga.models import LugarRecaudacion, GrupoSeminario, InscripcionSeminario, ActividadVinculacion, EstudianteVinculacion, Nivel, Matricula, Inscripcion, DocenteVinculacion, Persona, EvidenciaVinculacion, ObservacionVinculacion,BeneficiariosVinculacion,Convenio,Programa
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
# @secure_module
def view(request):
    hoy = datetime.today().date()
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
            elif action =='editarb':
                b = BeneficiariosVinculacion.objects.get(id=request.POST['id'])
                return HttpResponse(json.dumps({'result':'ok', "nombre": str(b.nombre), "identificacion":b.identificacion , "edad":b.edad , "sexo":b.sexo.id , "raza":b.etnia.id , "procedencia":b.procedencia }),content_type="application/json")

            elif action == 'add':
                try:
                    f = ProgramaForm(request.POST)
                    if f.is_valid():
                        try:
                            if request.POST['ban'] == '1':
                                programa = Programa(nombre=f.cleaned_data['nombre'],
                                                     tipo=f.cleaned_data['tipo'],
                                                     objetivo=f.cleaned_data['objetivo'],
                                                     inicio = f.cleaned_data['inicio'],
                                                     fin = f.cleaned_data['fin'])
                                programa.save()
                                mensaje = 'Adicionado'

                            else:
                                programa = Programa.objects.get(pk=int(request.POST['programa']))
                                programa.nombre=f.cleaned_data['nombre']
                                programa.objetivo=f.cleaned_data['objetivo']
                                programa.inicio = f.cleaned_data['inicio']
                                programa.fin = f.cleaned_data['fin']
                                programa.tipo = f.cleaned_data['tipo']
                                programa.save()
                                mensaje = 'Editado'

                            if 'archivo' in request.FILES:
                                programa.archivo =  request.FILES['archivo']
                                programa.save()

                        # Log Editar Programa
                            client_address = ip_client_address(request)
                            LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(programa).pk,
                                object_id       = programa.id,
                                object_repr     = force_str(programa),
                                action_flag     = CHANGE,
                                change_message  = mensaje + " Programa " +  '(' + client_address + ')' )

                            # if mensaje == 'Adicionado':
                            #     convenio.mail_vinculacion(request.user)

                            return HttpResponseRedirect("/programas")
                        except Exception as ex:
                            if request.POST['ban'] == '1':
                                return HttpResponseRedirect("programas?action=add&error=1",)
                            else:
                                return HttpResponseRedirect("programas?action=editar&error=1&id="+str(request.POST['programa']),)
                    else:
                        if request.POST['ban'] == '1':
                            return HttpResponseRedirect("programas?action=add&error=1",)
                        else:
                            return HttpResponseRedirect("programas?action=editar&error=1&id="+str(request.POST['programa']),)
                except Exception as ex:
                    print(ex)

            elif action == 'addevidencia':
                try:
                    f = EvidenciaForm(request.POST,request.FILES)
                    if f.is_valid():
                        vinculacion = Convenio.objects.get(pk=request.POST['id'])
                        evidencia= EvidenciaVinculacion(vinculacion=vinculacion,
                                                    nombre = request.POST['nombre'],
                                                    foto = request.FILES['archivo'])
                        evidencia.save()
                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(vinculacion).pk,
                            object_id       = vinculacion.id,
                            object_repr     = force_str(vinculacion),
                            action_flag     = CHANGE,
                            change_message  =  " Adicionada Evidencia" +  '(' + client_address + ')' )

                        return HttpResponseRedirect("/vinculacion?action=evidencia&id="+str(vinculacion.id))
                except Exception as ex:
                    pass

            elif action == 'activa':
                   programa =  Programa.objects.filter(id=request.POST['estid'])[:1].get()
                   fecha_dia=hoy

                   if not programa.fin >= fecha_dia:
                       if programa.activo:
                          activo = False
                          mensaje = 'Proyecto Inactivo'
                       else:
                           activo = True
                           mensaje = 'Proyecto Activo'

                   else:
                       msg='Proyecto no ha finalizado, no se puede cambiar estado'
                       return HttpResponse(json.dumps({"result":str(msg)}),content_type="application/json")

                   programa.activo = activo
                   programa.save()

                   client_address = ip_client_address(request)
                   #Log de Modificar Programa
                   LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(programa).pk,
                        object_id       = programa.id,
                        object_repr     = force_str(programa),
                        action_flag     = CHANGE,
                        change_message  = mensaje +' cambio estado  (' + client_address + ')')
                   return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")

            # elif action == 'addobservacion':
            #     try:
            #         f = ObservacionForm(request.POST,request.FILES)
            #         if f.is_valid():
            #             vinculacion = Vinculacion.objects.get(pk=request.POST['id'])
            #             observacion= ObservacionVinculacion(vinculacion=vinculacion,
            #                                         observacion = request.POST['observacion'],
            #                                         fecha = datetime.datetime.now())
            #             observacion.save()
            #             client_address = ip_client_address(request)
            #             LogEntry.objects.log_action(
            #                 user_id         = request.user.pk,
            #                 content_type_id = ContentType.objects.get_for_model(vinculacion).pk,
            #                 object_id       = vinculacion.id,
            #                 object_repr     = force_str(vinculacion),
            #                 action_flag     = CHANGE,
            #                 change_message  =  " Adicionada Observacion" +  '(' + client_address + ')' )
            #             return HttpResponseRedirect("/vinculacion?action=observacion&id="+str(vinculacion.id))
            #     except Exception as ex:
            #         pass

    else:
        data = {'title': 'Programas y Proyectos'}
        addUserData(request,data)
        try:
            if 'action' in request.GET:
                action = request.GET['action']

                if action == 'add':
                    data['form'] = ProgramaForm(initial={"inicio":datetime.now().date(),"fin":datetime.now().date()})
                    if 'error' in request.GET:
                        data['error'] = 1
                    data['ban'] =1
                    return render(request ,"vinculacion/addprograma.html" ,  data)

                elif action == 'participantes':
                    data['vinculacion'] = ActividadVinculacion.objects.get(pk=request.GET['id'])
                    data['participantes'] = EstudianteVinculacion.objects.filter(actividad=data['vinculacion']).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2')
                    if 's' in request.GET:
                        search = request.GET['s']
                        data['participantes'] = EstudianteVinculacion.objects.filter(Q(actividad=data['vinculacion'],inscripcion__persona__apellido1__icontains=search)|Q(actividad=data['vinculacion'],inscripcion__persona__apellido2__icontains=search)|Q(actividad=data['vinculacion'],inscripcion__persona__nombres__icontains=search)).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2')
                        data['search'] = search
                    data['form'] = ParticipanteForm()
                    data['form2'] = ParticipanteIndForm()
                    return render(request ,"vinculacion/participantes.html" ,  data)

                # elif action == 'evidencia':
                #     data['vinculacion'] = Vinculacion.objects.get(pk=request.GET['id'])
                #     data['evidencia'] = EvidenciaVinculacion.objects.filter(vinculacion=data['vinculacion'])
                #     data['form'] = EvidenciaForm()
                #     return render(request ,"vinculacion/evidencia.html" ,  data)

                # elif action == 'observacion':
                #     data['vinculacion'] = Vinculacion.objects.get(pk=request.GET['id'])
                #     data['observacion'] = ObservacionVinculacion.objects.filter(vinculacion=data['vinculacion'])
                #     data['form'] = ObservacionForm()
                #     return render(request ,"vinculacion/observacion.html" ,  data)

                # elif action == 'docentes':
                #     data['vinculacion'] = Vinculacion.objects.get(pk=request.GET['id'])
                #     data['docente'] = DocenteVinculacion.objects.filter(vinculacion=data['vinculacion']).order_by('persona__apellido1','persona__apellido2')
                #     if 's' in request.GET:
                #         search = request.GET['s']
                #         data['docente'] = DocenteVinculacion.objects.filter(Q(vinculacion=data['vinculacion'],persona__apellido1__icontains=search)|Q(vinculacion=data['vinculacion'],persona__apellido2__icontains=search)|Q(vinculacion=data['vinculacion'],docente__persona__nombres__icontains=search)).order_by('persona__apellido1','persona__apellido2')
                #         data['search'] = search
                #     data['form2'] = DocenteVincForm()
                #     return render(request ,"vinculacion/docentes.html" ,  data)

                # elif action == 'beneficiarios':
                #     data['vinculacion'] = Vinculacion.objects.get(pk=request.GET['id'])
                #     data['beneficiarios'] = BeneficiariosVinculacion.objects.filter(vinculacion=data['vinculacion']).order_by('nombre')
                #     if 's' in request.GET:
                #         search = request.GET['s']
                #         data['beneficiarios'] = BeneficiariosVinculacion.objects.filter(Q(vinculacion=data['vinculacion'],identificacion=search)|Q(vinculacion=data['vinculacion'],nombre__icontains=search))
                #         data['search'] = search
                #     data['form2'] = BeneficiariosForm()
                #     return render(request ,"vinculacion/beneficiarios.html" ,  data)

                # elif action == 'buscar':
                #     data['nivel'] = Nivel.objects.get(pk=request.GET['id'])
                #     vinculacion = Vinculacion.objects.get(pk=request.GET['vinculacion'])
                #     data['matriculas'] = Matricula.objects.filter(nivel=data['nivel']).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2')
                #     for m in Matricula.objects.filter(nivel=data['nivel']).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2'):
                #         if not EstudianteVinculacion.objects.filter(vinculacion=vinculacion,inscripcion=m.inscripcion).exists():
                #             participante = EstudianteVinculacion(vinculacion=vinculacion,
                #                                       inscripcion=m.inscripcion)
                #             participante.save()
                #     # data['matriculas'] = EstudianteVinculacion.objects.filter(vinculacion=vinculacion).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2')
                #     return HttpResponseRedirect("/vinculacion?action=participantes&id="+str(vinculacion.id))

                # elif action == 'agregar':
                #     inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                #     vinculacion = Vinculacion.objects.get(pk=request.GET['vinculacion'])
                #     if not EstudianteVinculacion.objects.filter(vinculacion=vinculacion,inscripcion=inscripcion).exists():
                #             participante = EstudianteVinculacion(vinculacion=vinculacion,
                #                                       inscripcion=inscripcion)
                #             participante.save()
                #     # data['matriculas'] = EstudianteVinculacion.objects.filter(vinculacion=vinculacion).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2')
                #     return HttpResponseRedirect("/vinculacion?action=participantes&id="+str(vinculacion.id))

                # elif action == 'agregard':
                #     persona = Persona.objects.get(pk=request.GET['id'])
                #     vinculacion = Vinculacion.objects.get(pk=request.GET['vinculacion'])
                #     if not DocenteVinculacion.objects.filter(vinculacion=vinculacion,persona=persona).exists():
                #             docentep = DocenteVinculacion(vinculacion=vinculacion,
                #                                       persona=persona)
                #             docentep.save()
                #     # data['matriculas'] = EstudianteVinculacion.objects.filter(vinculacion=vinculacion).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2')
                #     return HttpResponseRedirect("/vinculacion?action=docentes&id="+str(vinculacion.id))

                # elif action == 'agregarb':
                #     vinculacion = Vinculacion.objects.get(pk=request.GET['id'])
                #     if request.GET['b'] == '0' :
                #         if not BeneficiariosVinculacion.objects.filter(identificacion=request.GET['iden']).exists():
                #             beneficiario = BeneficiariosVinculacion(vinculacion=vinculacion,
                #                                       nombre=request.GET['nom'],
                #                                       identificacion=request.GET['iden'],
                #                                       edad=request.GET['edad'],
                #                                       sexo_id=request.GET['sexo'],
                #                                       etnia_id=request.GET['etnia'],
                #                                       procedencia=request.GET['proce'])
                #             beneficiario.save()
                #     else:
                #         b =BeneficiariosVinculacion.objects.get(id=request.GET['b'])
                #         b.nombre=request.GET['nom']
                #         b.identificacion=request.GET['iden']
                #         b.edad=request.GET['edad']
                #         b.sexo_id=request.GET['sexo']
                #         b.etnia_id=request.GET['etnia']
                #         b.procedencia=request.GET['proce']
                #         b.save()
                #
                #     # data['matriculas'] = EstudianteVinculacion.objects.filter(vinculacion=vinculacion).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2')
                #     return HttpResponseRedirect("/vinculacion?action=beneficiarios&id="+str(vinculacion.id))

                elif action == 'eliminar':
                    i =  Programa.objects.get(pk=request.GET['id'])
                    g = i
                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de Elimimar Programa
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(i).pk,
                        object_id       = i.id,
                        object_repr     = force_str(i),
                        action_flag     = CHANGE,
                        change_message  = 'Eliminado Programa (' + client_address + ')'  )
                    i.delete()

                    return HttpResponseRedirect("/programas")

                elif action == 'editar':
                    programa = Programa.objects.get(pk=request.GET['id'])
                    initial = model_to_dict(programa)
                    data['form'] = ProgramaForm(initial=initial)
                    if 'error' in request.GET:
                        data['error'] = 1
                    data['ban'] = 2
                    data['programa'] =programa
                    return render(request ,"vinculacion/addprograma.html" ,  data)

                elif action == 'finalizar':
                    i =  Convenio.objects.get(pk=request.GET['id'])
                    if i.finalizado:
                        i.finalizado = False
                    else:
                        i.finalizado = True

                    i.fechafinalizado =datetime.now().date()
                    i.save()

                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de Cambio de Estado Convenio
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(i).pk,
                        object_id       = i.id,
                        object_repr     = force_str(i),
                        action_flag     = CHANGE,
                        change_message  = 'Proyecto Finalizado cambiado a '+  str(i.fechafinalizado) + ' (' + client_address + ')'  )

                    return HttpResponseRedirect("/programas")

            else:
                search = ""
                activos = None
                inactivos = None
                todos = None

                if 's' in request.GET:
                    search = request.GET['s']
                if 't' in request.GET:
                    todos = request.GET['t']
                if 'a' in request.GET:
                    activos = request.GET['a']
                if 'i' in request.GET:
                    inactivos = request.GET['i']

                if search:
                    programa = Programa.objects.filter(Q(nombre__icontains=search)).order_by('-tipo','-inicio')
                else:
                    programa = Programa.objects.all().order_by('-tipo','-inicio')

                if todos:
                    programa = Programa.objects.all().order_by('-tipo','-inicio')

                if activos:
                    programa = Programa.objects.filter(activo=True).order_by('-tipo','-inicio')

                if inactivos:
                    programa = Programa.objects.filter(activo=False).order_by('-tipo','-inicio')

                paging = MiPaginador(programa, 30)
                p = 1
                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                        paging = MiPaginador(programa, 30)
                    page = paging.page(p)
                except Exception as ex:
                    page = paging.page(1)

                data['paging'] = paging
                data['rangospaging'] = paging.rangos_paginado(p)
                data['page'] = page
                data['programa'] = page.object_list
                data['todos'] = todos if todos else ""
                data['activos'] = activos if activos else ""
                data['inactivos'] = inactivos if inactivos else ""
                data['search'] = search if search else ""
                return render(request ,"vinculacion/programas.html" ,  data)
        except Exception as ex:
            pass

