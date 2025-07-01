import os
from datetime import datetime
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.auth.decorators import login_required
from bib.models import DocuemntoGraduado
from sga.commonviews import addUserData, ip_client_address
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Avg
from django.db.models.query_utils import Q
from django.forms.models import model_to_dict
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
from decorators import secure_module
from settings import TESIS_URL, MEDIA_ROOT
from sga.commonviews import addUserData
from sga.forms import GraduadoForm, SeguimientoGraduadoForm, GraduadoDatosForm, ObservacionGraduadoForm
from sga.models import Inscripcion, Graduado, SeguimientoGraduado, Asignatura, Carrera, ObservacionGraduado
from sga.reportes import elimina_tildes

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
        action = request.POST['action']
        if action=='add':
            inscripcion = Inscripcion.objects.get(pk=request.POST['id'])
            f = GraduadoForm(request.POST,request.FILES)
            archiv = None
            if f.is_valid():
                if 'archivo' in request.FILES:
                    archiv = request.FILES['archivo']
                graduado = Graduado(inscripcion=inscripcion,tematesis=f.cleaned_data['tematesis'],
                                    notatesis=f.cleaned_data['notatesis'],notafinal=f.cleaned_data['notafinal'],
                                    fechagraduado=f.cleaned_data['fechagraduado'], registro=f.cleaned_data['registro'],
                                    archivo = archiv)
                graduado.save()

                client_address = ip_client_address(request)
                # Log de ADICIONAR GRADUADO
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(graduado).pk,
                    object_id       = graduado.id,
                    object_repr     = force_str(graduado),
                    action_flag     = ADDITION,
                    change_message  = 'Adicionado Graduado (' + client_address + ')' )
            else:
                return HttpResponseRedirect("/graduados?action=add&id="+str(inscripcion.id))

        elif action=='edit':
            graduado = Graduado.objects.get(pk=request.POST['id'])
            f = GraduadoForm(request.POST)
            if f.is_valid():
                graduado.tematesis = f.cleaned_data['tematesis']
                graduado.notatesis = f.cleaned_data['notatesis']
                graduado.notafinal = f.cleaned_data['notafinal']
                graduado.fechagraduado = f.cleaned_data['fechagraduado']
                graduado.registro = f.cleaned_data['registro']
                graduado.save()
                if DocuemntoGraduado.objects.filter(graduado=graduado):
                   documentogra =DocuemntoGraduado.objects.get(graduado=graduado)
                   documentogra.documento_id= int(f.cleaned_data['tesis'])
                else:
                   documentogra =DocuemntoGraduado(graduado=graduado,documento_id=int(f.cleaned_data['tesis']))

                documentogra.save()

                # Log de EDITAR GRADUADO
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(graduado).pk,
                    object_id       = graduado.id,
                    object_repr     = force_str(graduado),
                    action_flag     = CHANGE,
                    change_message  = 'Editado Graduado' )
            else:
                return HttpResponseRedirect("/graduados?action=edit&id="+str(graduado.id))

        elif action=='del':
            graduado = Graduado.objects.get(pk=request.POST['id'])
            graduado.delete()

            # Log de ELIMINAR GRADUADO
            LogEntry.objects.log_action(
                user_id         = request.user.pk,
                content_type_id = ContentType.objects.get_for_model(graduado).pk,
                object_id       = graduado.id,
                object_repr     = force_str(graduado),
                action_flag     = DELETION,
                change_message  = 'Eliminado Graduado' )

        elif action=='datos':
            graduado = Graduado.objects.get(pk=request.POST['id'])
            return HttpResponseRedirect("/graduados?s="+str(graduado.inscripcion.persona.cedula))

        elif action=='addseguimiento':
            graduado = Graduado.objects.get(pk=request.POST['id'])
            f = SeguimientoGraduadoForm(request.POST)
            sueldo=0
            try:
                if f.is_valid():
                    if f.cleaned_data['ejerce']==True:
                        seguimiento = SeguimientoGraduado(graduado=graduado,empresa=f.cleaned_data['empresa'],
                                                        cargo=f.cleaned_data['cargo'],ocupacion=f.cleaned_data['ocupacion'],
                                                        telefono=f.cleaned_data['telefono'],email=f.cleaned_data['email'],
                                                        sueldo=f.cleaned_data['sueldo'],ejerce=f.cleaned_data['ejerce'],
                                                        observaciones=f.cleaned_data['observaciones'],
                                                        usuario=request.user,fecha = datetime.now(),
                                                        hora = datetime.now().time())

                        seguimiento.save()
                        return HttpResponseRedirect("/graduados?action=seguimiento&id="+str(graduado.id))
                    else:
                        #OCU 23-enero-2019 solicitado por R Grunauer si ejerce o no profesion se debe grabar la informacion
                        # seguimiento = SeguimientoGraduado(graduado=graduado,empresa="NO APLICA",
                        #                                 cargo="NO APLICA",ocupacion="NO APLICA",
                        #                                 sueldo=0,ejerce=f.cleaned_data['ejerce'],
                        #                                 observaciones=f.cleaned_data['observaciones'],
                        #                                 usuario=request.user,fecha = datetime.now())
                        if f.cleaned_data['sueldo']==0 or f.cleaned_data['sueldo']==None:
                            sueldo=0
                        else:
                            sueldo=f.cleaned_data['sueldo']
                        seguimiento = SeguimientoGraduado(graduado=graduado,
                                                          empresa=f.cleaned_data['empresa'],
                                                            cargo=f.cleaned_data['cargo'],
                                                            ocupacion=f.cleaned_data['ocupacion'],
                                                            telefono=f.cleaned_data['telefono'],
                                                            email=f.cleaned_data['email'],
                                                            sueldo=sueldo,
                                                            ejerce=False,
                                                            observaciones=f.cleaned_data['observaciones'],
                                                            usuario=request.user,
                                                            fecha = datetime.now(),
                                                            hora = datetime.now().time())
                        seguimiento.save()

                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de ADICIONAR SEGUIMIENTO
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(seguimiento).pk,
                        object_id       = seguimiento.id,
                        object_repr     = force_str(seguimiento),
                        action_flag     = ADDITION,
                        change_message  = 'Adicionado Seguimiento Graduado(' + client_address + ')' )

                    return HttpResponseRedirect("/graduados?action=seguimiento&id="+str(graduado.id))
                else:
                    # Enviar mensaje de error
                    # return HttpResponseRedirect("/graduados?action=addseguimiento")
                    return HttpResponseRedirect("/graduados?error=Error en el formulario al ingresar seguimiento")

            except Exception as ex:
                return HttpResponseRedirect("/graduados?error=Error en el ingreso de seguimiento")

        elif action=='editseguimiento':
            seguimiento = SeguimientoGraduado.objects.get(pk=request.POST['id'])
            f = SeguimientoGraduadoForm(request.POST)
            sueldo=0
            try:
                if f.is_valid():
                    if f.cleaned_data['ejerce']==True:
                        seguimiento.empresa = f.cleaned_data['empresa']
                        seguimiento.cargo = f.cleaned_data['cargo']
                        seguimiento.ocupacion = f.cleaned_data['ocupacion']
                        seguimiento.telefono = f.cleaned_data['telefono']
                        seguimiento.email = f.cleaned_data['email']
                        seguimiento.sueldo = f.cleaned_data['sueldo']
                        seguimiento.ejerce = f.cleaned_data['ejerce']
                        seguimiento.observaciones = f.cleaned_data['observaciones']
                        seguimiento.usuario=request.user
                        seguimiento.fecha = datetime.now()
                        seguimiento.hora = datetime.now().time()
                        seguimiento.save()

                        #Obtain client ip address
                        client_address = ip_client_address(request)

                        # Log de ADICIONAR SEGUIMIENTO
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(seguimiento).pk,
                            object_id       = seguimiento.id,
                            object_repr     = force_str(seguimiento),
                            action_flag     = CHANGE,
                            change_message  = 'Modificado Seguimiento Graduado(' + client_address + ')' )

                        return HttpResponseRedirect("/graduados?action=seguimiento&id="+str(seguimiento.graduado.id))
                    else:
                        # seguimiento.empresa="NO APLICA"
                        # seguimiento.cargo="NO APLICA"
                        # seguimiento.ocupacion="NO APLICA"
                        # seguimiento.telefono="NO APLICA"
                        # seguimiento.email="NO APLICA"
                        # seguimiento.sueldo=0
                        # seguimiento.ejerce=False
                        # seguimiento.observaciones =f.cleaned_data['observaciones']
                        # seguimiento.usuario=request.user
                        # seguimiento.fecha = datetime.now()
                        # seguimiento.save()

                        #OCU 23-enero-2019 solicitado por R Grunauer si ejerce o no profesion se debe grabar la informacion
                        if f.cleaned_data['sueldo']==0 or f.cleaned_data['sueldo']==None:
                            sueldo=0
                        else:
                            sueldo=f.cleaned_data['sueldo']
                        seguimiento.empresa = f.cleaned_data['empresa']
                        seguimiento.cargo = f.cleaned_data['cargo']
                        seguimiento.ocupacion = f.cleaned_data['ocupacion']
                        seguimiento.telefono = f.cleaned_data['telefono']
                        seguimiento.email = f.cleaned_data['email']
                        seguimiento.sueldo = sueldo
                        seguimiento.ejerce = False
                        seguimiento.observaciones = f.cleaned_data['observaciones']
                        seguimiento.usuario=request.user
                        seguimiento.fecha = datetime.now()
                        seguimiento.hora = datetime.now().time()
                        seguimiento.save()

                        #Obtain client ip address
                        client_address = ip_client_address(request)

                        # Log de ADICIONAR SEGUIMIENTO
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(seguimiento).pk,
                            object_id       = seguimiento.id,
                            object_repr     = force_str(seguimiento),
                            action_flag     = CHANGE,
                            change_message  = 'Modificado Seguimiento Graduado(' + client_address + ')' )

                        return HttpResponseRedirect("/graduados?action=seguimiento&id="+str(seguimiento.graduado.id))
                else:
                    # Enviar mensaje de error
                    # return HttpResponseRedirect("/graduados?action=editseguimiento")
                    return HttpResponseRedirect("/graduados?error=Error en el formulario al editar seguimiento")

            except Exception as ex:
                return HttpResponseRedirect("/graduados?error=Error al editar seguimiento")

        elif action=='delseguimiento':
            seguimiento = SeguimientoGraduado.objects.get(pk=request.POST['id'])
            graduado = seguimiento.graduado
            seguimiento.delete()
            return HttpResponseRedirect("/graduados?action=seguimiento&id="+str(graduado.id))

        #Observaciones a Graduados
        elif action=='addobservacion':
            graduado = Graduado.objects.get(pk=request.POST['id'])
            f = ObservacionGraduadoForm(request.POST)
            if f.is_valid():
                observacion = ObservacionGraduado(graduado=graduado,
                                                  observaciones=f.cleaned_data['observaciones'],
                                                  fecha = f.cleaned_data['fechaobs'])
                observacion.save()
                return HttpResponseRedirect("/graduados?action=observaciones&id="+str(graduado.id))
            else:
                return HttpResponseRedirect("/graduados?action=addobservacion")

        elif action=='editobservacion':
            observacion = ObservacionGraduado.objects.get(pk=request.POST['id'])
            f = ObservacionGraduadoForm(request.POST)
            if f.is_valid():
                observacion.observaciones = f.cleaned_data['observaciones']
                observacion.fecha = f.cleaned_data['fechaobs']
                observacion.save()
                return HttpResponseRedirect("/graduados?action=observaciones&id="+str(observacion.graduado.id))
            else:
                return HttpResponseRedirect("/graduados?action=editobservacion&id="+str(observacion.id))

        elif action=='delobservacion':
            observacion = ObservacionGraduado.objects.get(pk=request.POST['id'])
            graduado = observacion.graduado
            observacion.delete()
            return HttpResponseRedirect("/graduados?action=observaciones&id="+str(graduado.id))


        elif action=='addarchivo':
            try:
                graduado = Graduado.objects.get(id=request.POST['idgradua'])
                if (MEDIA_ROOT + '/'+str(graduado.archivo)):
                    os.remove(MEDIA_ROOT + '/'+ str(graduado.archivo))
                graduado.archivo = request.FILES['archivo']
                graduado.save()
                return HttpResponseRedirect("/graduados")
            except Exception as ex:
                return HttpResponseRedirect("/graduados?error=Error en el ingreso de la tesis vuelva a intentarlo")

        return HttpResponseRedirect("/graduados")
    else:
        data = {'title': 'Listado de Graduados'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='add':
                data['title'] = 'Graduar Estudiante'
                inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                data['inscripcion'] = inscripcion
                # OCU 29-08-2017 validacion malla completa
                if inscripcion.mallacompleta():
                    promedio = round(inscripcion.recordacademico_set.filter(aprobada=True, asignatura__in=Asignatura.objects.filter(asignaturamalla__nivelmalla__promediar=True)).aggregate(Avg('nota'))['nota__avg'],2)
                    data['form'] = GraduadoForm(initial={'fechagraduado': datetime.now().strftime("%d-%m-%Y"), 'notafinal': promedio})
                    return render(request ,"graduados/adicionarbs.html" ,  data)
                else:
                    return HttpResponseRedirect("/egresados?s="+str(elimina_tildes(inscripcion.persona.nombre_completo_inverso()))+"&error= estudiante no ha completado malla")

            elif action=='edit':
                data['title'] = 'Editar Graduacion del Estudiante'
                graduado = Graduado.objects.get(pk=request.GET['id'])
                initial = model_to_dict(graduado)
                data['graduado'] = graduado
                data['form'] = GraduadoForm(initial=initial)
                return render(request ,"graduados/editarbs.html" ,  data)
            elif action=='del':
                data['title'] = 'Borrar graduacion'
                data['graduado'] = Graduado.objects.get(pk=request.GET['id'])
                return render(request ,"graduados/borrarbs.html" ,  data)
            elif action=='seguimiento':
                data['title'] = 'Seguimiento de Graduados'
                graduado = Graduado.objects.get(pk=request.GET['id'])
                data['seguimientos'] = SeguimientoGraduado.objects.filter(graduado=graduado).order_by('-id')
                data['graduado'] = graduado
                return render(request ,"graduados/seguimientobs.html" ,  data)
            elif action=='addseguimiento':
                data['title'] = 'Adicionar Seguimiento laboral del Graduado'
                graduado = Graduado.objects.get(pk=request.GET['id'])
                data['form'] = SeguimientoGraduadoForm()
                data['graduado'] = graduado
                return render(request ,"graduados/addseguimientobs.html" ,  data)
            elif action=='editseguimiento':
                data['title'] = 'Editar Seguimiento laboral del Alumno'
                seguimiento = SeguimientoGraduado.objects.get(pk=request.GET['id'])
                initial = model_to_dict(seguimiento)
                data['form'] = SeguimientoGraduadoForm(initial=initial)
                data['seguimiento'] = seguimiento
                return render(request ,"graduados/editseguimientobs.html" ,  data)
            elif action=='delseguimiento':
                data['title'] = 'Eliminar Seguimiento del Graduado'
                data['seguimiento'] = SeguimientoGraduado.objects.get(pk=request.GET['id'])
                return render(request ,"graduados/delseguimientobs.html" ,  data)
            elif action=='datos':
                data['title'] = 'Datos de Contacto del Graduado'
                graduado = Graduado.objects.get(pk=request.GET['id'])
                inscripcion = graduado.inscripcion
                initial = model_to_dict(inscripcion)
                initial.update(model_to_dict(inscripcion.persona))
                gform = GraduadoDatosForm(initial=initial)
                data['form'] = gform
                data['graduado'] = graduado
                data['inscripcion'] = inscripcion
                return render(request ,"graduados/datosbs.html" ,  data)

            elif action=='observaciones':
                data['title'] = 'Observaciones de Graduados'
                graduado = Graduado.objects.get(pk=request.GET['id'])
                data['observaciones'] = graduado.observaciongraduado_set.all()
                data['graduado'] = graduado
                return render(request ,"graduados/observaciones.html" ,  data)
            elif action=='addobservacion':
                data['title'] = 'Adicionar Observacion del Graduado'
                graduado = Graduado.objects.get(pk=request.GET['id'])
                data['form'] = ObservacionGraduadoForm(initial={'fechaobs':datetime.today()})
                data['graduado'] = graduado
                return render(request ,"graduados/addobservacion.html" ,  data)
            elif action=='editobservacion':
                data['title'] = 'Editar Observacion del Alumno'
                observacion = ObservacionGraduado.objects.get(pk=request.GET['id'])
                # initial = model_to_dict(observacion)
                data['form'] = ObservacionGraduadoForm(initial={'observaciones':observacion.observaciones,'fechaobs':observacion.fecha})
                data['observacion'] = observacion
                return render(request ,"graduados/editobservacion.html" ,  data)
            elif action=='delobservacion':
                data['title'] = 'Eliminar Observacion del Graduado'
                data['observacion'] = ObservacionGraduado.objects.get(pk=request.GET['id'])
                return render(request ,"graduados/delobservacion.html" ,  data)


        else:
            search  = None
            filtro  = None
            anio    = None
            ejerce = None
            cargo = None

            if 'filter' in request.GET:
                filtro = request.GET['filter']
                data['filtro']  = filtro

            if 'anio' in request.GET:
                anio =datetime.now().year

            if 's' in request.GET:
                search = request.GET['s']




            if search:

                ss = search.split(' ')
                while '' in ss:
                    ss.remove('')
                if len(ss)==1:
                    graduados = Graduado.objects.filter(Q(inscripcion__persona__nombres__icontains=search) | Q(inscripcion__persona__apellido1__icontains=search) | Q(inscripcion__persona__apellido2__icontains=search) | Q(inscripcion__persona__cedula__icontains=search) | Q(inscripcion__persona__pasaporte__icontains=search)).order_by('-fechagraduado', 'inscripcion__persona__apellido1', 'inscripcion__carrera__nombre')
                else:
                    graduados = Graduado.objects.filter(Q(inscripcion__persona__apellido1__icontains=ss[0]) & Q(inscripcion__persona__apellido2__icontains=ss[1])).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')
            else:
                graduados = Graduado.objects.all().order_by('-fechagraduado', 'inscripcion__persona__apellido1', 'inscripcion__carrera__nombre')


            if anio:
                if search:
                    graduados = graduados.filter(fechagraduado__year=anio).order_by('-fechagraduado', 'inscripcion__persona__apellido1', 'inscripcion__carrera__nombre')
                else:
                    graduados = Graduado.objects.filter(fechagraduado__year=anio).order_by('-fechagraduado', 'inscripcion__persona__apellido1', 'inscripcion__carrera__nombre')



            if filtro:
                carrera = Carrera.objects.get(pk=filtro)
                graduados = Graduado.objects.filter(inscripcion__carrera=carrera).order_by('-fechagraduado', 'inscripcion__persona__apellido1', 'inscripcion__carrera__nombre')
            data['totalgraduados'] = graduados.count()
            if 'cargo' in request.GET:
                graduados = graduados.filter().exclude(seguimientograduado__cargo='NO APLICA').exclude(seguimientograduado__cargo=None)
                cargo = graduados.count()
                data['cargo']=cargo
            if 'ejerce' in request.GET:
                graduados = graduados.filter(seguimientograduado__ejerce = True)
                ejerce = graduados.count()
                data['ejerce']=ejerce
            paging = MiPaginador(graduados, 30)
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
            data['search'] = search if search else ""
            data['filter'] = carrera if filtro else ""
            data['anio'] = anio if anio else ""
            data['carreras'] = Carrera.objects.all().order_by('nombre')

            data['graduados'] = page.object_list
            data['TESIS_URL'] = TESIS_URL
            if 'error' in request.GET:
                data['error'] = request.GET['error']
            return render(request ,"graduados/graduadosbs.html" ,  data)
