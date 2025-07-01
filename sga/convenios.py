from datetime import datetime, timedelta,date
from django.contrib.admin.models import LogEntry, CHANGE, ADDITION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
import json
from django.db.models import Q, Sum
from django.forms import model_to_dict
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
from decorators import secure_module
from sga.forms import LugarRecaudacionForm, GrupoSeminarioForm, VinculacionForm, ParticipanteForm, ParticipanteIndForm, DocenteVincForm, EvidenciaForm, ObservacionForm,BeneficiariosForm, ConvenioForm, DatoForm, DatoForm2, DatoForm3, TipoConvenioForm
from sga.models import LugarRecaudacion, GrupoSeminario, InscripcionSeminario, ActividadVinculacion, EstudianteVinculacion, Nivel, Matricula, Inscripcion, DocenteVinculacion, Persona, EvidenciaVinculacion, ObservacionVinculacion,BeneficiariosVinculacion,Convenio, CarreraConvenio, Carrera, ModalidadCarreraConvenio, Modalidad, Clasificacion, ConvenioClasificacion, TipoConvenio
from sga.commonviews import addUserData, ip_client_address
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
    hoy = datetime.today().date()
    if request.method=='POST':
        if 'action' in request.POST:
            action = request.POST['action']
            if action == 'add':
                f = ConvenioForm(request.POST)
                if f.is_valid():
                    try:
                        if request.POST['ban'] == '1':
                            convenio = Convenio(nombre=f.cleaned_data['nombre'],
                                                 institucion=f.cleaned_data['institucion'],
                                                 objetivo = f.cleaned_data['objetivo'],
                                                 nacional = f.cleaned_data['nacional'],
                                                 inicio = f.cleaned_data['inicio'],
                                                 fin = f.cleaned_data['fin'],
                                                 contacto = f.cleaned_data['contacto'],
                                                 canton_id = f.cleaned_data['idcanton'],
                                                 indefinido = f.cleaned_data['indefinido'],
                                                 prolonga = f.cleaned_data['prolonga'],
                                                 contactoemail = f.cleaned_data['contactoemail'],
                                                 contactofono = f.cleaned_data['contactofono'],

                                                 representante = f.cleaned_data['representante'],
                                                 representantetelefono = f.cleaned_data['representantetelefono'],
                                                 representanteemail = f.cleaned_data['representanteemail'],

                                                 pais_id = f.cleaned_data['idpais'],
                                                 tiempo = f.cleaned_data['tiempo'],
                                                 tipo = f.cleaned_data['tipo'])
                            convenio.save()
                            mensaje = 'Adicionado'

                        else:
                            convenio = Convenio.objects.get(pk=int(request.POST['convenio']))
                            convenio.nombre=f.cleaned_data['nombre']
                            convenio.institucion=f.cleaned_data['institucion']
                            convenio.objetivo = f.cleaned_data['objetivo']
                            convenio.nacional = f.cleaned_data['nacional']
                            convenio.inicio = f.cleaned_data['inicio']
                            convenio.fin = f.cleaned_data['fin']
                            convenio.contacto = f.cleaned_data['contacto']
                            convenio.canton_id = f.cleaned_data['idcanton']
                            convenio.pais_id = f.cleaned_data['idpais']
                            convenio.contactofono = f.cleaned_data['contactofono']
                            convenio.contactoemail = f.cleaned_data['contactoemail']
                            convenio.tiempo = f.cleaned_data['tiempo']
                            convenio.prolonga = f.cleaned_data['prolonga']
                            convenio.indefinido = f.cleaned_data['indefinido']
                            convenio.tipo = f.cleaned_data['tipo']

                            convenio.representante = f.cleaned_data['representante']
                            convenio.representantetelefono = f.cleaned_data['representantetelefono']
                            convenio.representanteemail = f.cleaned_data['representanteemail']

                            # convenio.nivelmalla = f.cleaned_data['nivelmalla']
                            convenio.save()
                            mensaje = 'Editado'

                        if 'archivo' in request.FILES:
                            convenio.archivo =  request.FILES['archivo']
                            convenio.save()

                    # Log Editar Inscripcion
                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(convenio).pk,
                            object_id       = convenio.id,
                            object_repr     = force_str(convenio),
                            action_flag     = CHANGE,
                            change_message  = mensaje + " Convenio " +  '(' + client_address + ')' )

                        # if mensaje == 'Adicionado':
                        #     convenio.mail_vinculacion(request.user)

                        return HttpResponseRedirect("/convenios")
                    except Exception as ex:
                        if request.POST['ban'] == '1':
                            return HttpResponseRedirect("convenios?action=add&error="+str(ex))
                        else:
                            return HttpResponseRedirect("convenios?action=editar&error="+ str(ex)+ "&id="+str(request.POST['convenio']),)
                else:
                    if request.POST['ban'] == '1':
                        return HttpResponseRedirect("convenios?action=add&error=1",)
                    else:
                        return HttpResponseRedirect("convenios?action=editar&error=1&id="+str(request.POST['vinculacion']),)
            elif action =='addcarrera':
                try:
                    convenio = Convenio.objects.get(pk=request.POST['id'])
                    carrera = Carrera.objects.get(pk=request.POST['carrera'])
                    if not  CarreraConvenio.objects.filter(carrera=carrera,convenio=convenio).exists():
                        cc = CarreraConvenio(carrera=carrera,convenio=convenio)
                        cc.save()

                        #Obtain client ip address
                        client_address = ip_client_address(request)

                        # Log de BORRAR HISTORICO
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(cc).pk,
                            object_id       = cc.id,
                            object_repr     = force_str(cc),
                            action_flag     = ADDITION,
                            change_message  = 'Agregado Carrera a Convenio (' + client_address + ')')
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

            elif action =='addclasificacion':
                try:
                    if not  Clasificacion.objects.filter(nombre=request.POST['nombre']).exists():
                        cc = Clasificacion(nombre=request.POST['nombre'])
                        cc.save()

                        #Obtain client ip address
                        client_address = ip_client_address(request)

                        # Log de BORRAR HISTORICO
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(cc).pk,
                            object_id       = cc.id,
                            object_repr     = force_str(cc),
                            action_flag     = ADDITION,
                            change_message  = 'Agregada Clasificacion (' + client_address + ')')
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

            elif action =='addmodalidad':
                try:
                    carreraconvenio = CarreraConvenio.objects.get(pk=request.POST['id'])
                    modalidad = Modalidad.objects.get(pk=request.POST['modalidad'])
                    if not  ModalidadCarreraConvenio.objects.filter(carreraconvenio=carreraconvenio,modalidad=modalidad).exists():
                        cc = ModalidadCarreraConvenio(carreraconvenio=carreraconvenio,modalidad=modalidad)
                        cc.save()

                        #Obtain client ip address
                        client_address = ip_client_address(request)

                        # Log de BORRAR HISTORICO
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(cc).pk,
                            object_id       = cc.id,
                            object_repr     = force_str(cc),
                            action_flag     = ADDITION,
                            change_message  = 'Agregado Modalidad a Convenio (' + client_address + ')')
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

            elif action =='addclasificacionconvenio':
                try:
                    convenio = Convenio.objects.get(pk=request.POST['id'])
                    clasificacion = Clasificacion.objects.get(pk=request.POST['clasificacion'])
                    if not  ConvenioClasificacion.objects.filter(convenio=convenio,clasificacion=clasificacion).exists():
                        cc = ConvenioClasificacion(convenio=convenio,clasificacion=clasificacion)
                        cc.save()

                        #Obtain client ip address
                        client_address = ip_client_address(request)

                        # Log de BORRAR HISTORICO
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(cc).pk,
                            object_id       = cc.id,
                            object_repr     = force_str(cc),
                            action_flag     = ADDITION,
                            change_message  = 'Agregado Clasificacion a Convenio (' + client_address + ')')
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

            elif action =='editclasificacion':
                try:
                    clasificacion = Clasificacion.objects.get(pk=request.POST['id'])
                    clasificacion.nombre = request.POST['nombre']
                    clasificacion.save()
                        #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de BORRAR HISTORICO
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(clasificacion).pk,
                        object_id       = clasificacion.id,
                        object_repr     = force_str(clasificacion),
                        action_flag     = ADDITION,
                        change_message  = 'Editada Clasificacion (' + client_address + ')')
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")


            elif action == 'activa':
                   convenio =  Convenio.objects.filter(id=request.POST['estid'])[:1].get()
                   fecha_dia=hoy

                   # if not convenio.fin >= fecha_dia:
                   #     if convenio.activo:
                   #        activo = False
                   #        mensaje = 'Convenio Inactivo'
                   #     else:
                   #         activo = True
                   #         mensaje = 'Convenio Activo'
                   #
                   # else:
                   #     msg='Convenio no ha finalizado, no se puede cambiar estado'
                   #     return HttpResponse(json.dumps({"result":str(msg)}),content_type="application/json")

                   if convenio.activo:
                      activo = False
                      mensaje = 'Convenio Inactivo'
                   else:
                       activo = True
                       mensaje = 'Convenio Activo'
                   convenio.activo = activo
                   convenio.save()

                   client_address = ip_client_address(request)
                   #Log de MODIFICAR CONVENIO
                   LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(convenio).pk,
                        object_id       = convenio.id,
                        object_repr     = force_str(convenio),
                        action_flag     =CHANGE,
                        change_message  = mensaje +' cambio estado (' + client_address + ')')
                   return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")

            elif action == 'add_tipo':
             try:
                nombre = elimina_tildes(request.POST['nombre']).upper()
                existe = TipoConvenio.objects.filter(nombre=nombre).exists()
                if existe:
                    return HttpResponseRedirect('/convenios?error=Tipo de Convenio existente')
                else:
                    guardar = TipoConvenio(nombre=nombre)
                    guardar.save()
                    mensaje = 'Ingreso Tipo Documento Vinculacion'
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(guardar).pk,
                    object_id       = guardar.id,
                    object_repr     = force_str(guardar),
                    action_flag     = ADDITION,
                    change_message  = mensaje+' (' + client_address + ')' )
                return HttpResponseRedirect('/convenios')
             except Exception as ex:
                print(ex)
                return HttpResponseRedirect('/convenios?error=Ocurrio un error, vuelva a intentarlo')

    else:
        data = {'title': 'Convenios de Vinculacion'}
        addUserData(request,data)
        try:
            if 'action' in request.GET:
                action = request.GET['action']

                if action == 'add':
                    data['form'] = ConvenioForm(initial={"inicio":datetime.now().date(),"fin":datetime.now().date()})
                    if 'error' in request.GET:
                        data['error'] = 1
                    data['ban'] =1
                    return render(request ,"vinculacion/addconvenio.html" ,  data)

                elif action == 'eliminar':
                    i =  Convenio.objects.get(pk=request.GET['id'])
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
                        change_message  = 'Eliminado Convenio (' + client_address + ')'  )
                    i.delete()

                    return HttpResponseRedirect("/convenios")

                elif action == 'editar':
                    convenio = Convenio.objects.get(pk=request.GET['id'])
                    initial = model_to_dict(convenio)
                    data['form'] = ConvenioForm(initial=initial)
                    if 'error' in request.GET:
                        data['error'] = 1
                    data['ban'] = 2
                    data['convenio'] =convenio
                    if convenio.canton:
                        data['canton'] = convenio.canton
                    else:
                        data['canton'] = ''
                    if convenio.pais:
                        data['pais'] = convenio.pais
                    else:
                        data['pais'] = ''
                    return render(request ,"vinculacion/addconvenio.html" ,  data)

                elif action =='discapVinculacion':
                     num_est_aprobado=0
                     listaEstudiante=[]
                     id_estudiante= EstudianteVinculacion.objects.filter(actividad__fin__year=request.GET['dato'],inscripcion__tienediscapacidad=True).distinct('inscripcion').values('inscripcion')
                     for lista in Inscripcion.objects.filter(id__in=id_estudiante):
                         hora_inscip = EstudianteVinculacion.objects.filter(actividad__fin__year=request.GET['dato'],inscripcion=lista).aggregate(Sum('horas'))['horas__sum']
                         if hora_inscip>= 160:
                            num_est_aprobado = num_est_aprobado +1
                            if not lista.id in listaEstudiante:
                                listaEstudiante.append(lista.id)

                     data['num_est_aprobado']=num_est_aprobado
                     data['periodo']=request.GET['dato']
                     data['listaEstudiante']=EstudianteVinculacion.objects.filter(inscripcion__in=id_estudiante).order_by('inscripcion__persona')

                     return render(request ,"vinculacion/convenioDiscapacidad.html" ,  data)


                elif action == 'verclasificacion':
                    try:
                        if Clasificacion.objects.all().exists():
                            data['clasificacion'] = Clasificacion.objects.all().order_by('nombre')
                        return render(request ,"vinculacion/clasificacion.html" ,  data)
                    except:
                        return render(request ,"vinculacion/clasificacion.html" ,  data)

                elif action == 'verclasificacionconvenio':
                    try:
                        convenio = Convenio.objects.get(pk=request.GET['id'])
                        if ConvenioClasificacion.objects.filter(convenio=convenio).exists():
                            data['clasificaciones'] = ConvenioClasificacion.objects.filter(convenio=convenio).order_by('convenio')
                        return render(request ,"vinculacion/convenioclasificacion.html" ,  data)
                    except:
                        return render(request ,"vinculacion/convenioclasificacion.html" ,  data)

                elif action == 'vercarreras':
                    try:
                        convenio = Convenio.objects.get(pk=request.GET['id'])
                        if CarreraConvenio.objects.filter(convenio=convenio).exists():
                            data['carreras'] = CarreraConvenio.objects.filter(convenio=convenio).order_by('carrera__nombre')
                        return render(request ,"vinculacion/carreraconvenio.html" ,  data)
                    except:
                        return render(request ,"vinculacion/carreraconvenio.html" ,  data)

                elif action == 'eliminacarrera':
                    i =  CarreraConvenio.objects.get(pk=request.GET['id'])
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
                        change_message  = 'Eliminada Carrera de Convenio (' + client_address + ')'  )
                    i.delete()

                    return HttpResponseRedirect("/convenios")

                elif action == 'eliminaclasificacion':
                    i =  Clasificacion.objects.get(pk=request.GET['id'])
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
                        change_message  = 'Eliminada Clasificacion (' + client_address + ')'  )
                    i.delete()

                    return HttpResponseRedirect("/convenios")

                elif action == 'eliminaclasificacionconvenio':
                    i =  ConvenioClasificacion.objects.get(pk=request.GET['id'])
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
                        change_message  = 'Eliminada Clasificacion Convenio (' + client_address + ')'  )
                    i.delete()

                    return HttpResponseRedirect("/convenios")
                elif action == 'eliminamodalidad':
                    i =  ModalidadCarreraConvenio.objects.get(pk=request.GET['id'])
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
                        change_message  = 'Eliminada Modalidad de Convenio (' + client_address + ')'  )
                    i.delete()

                    return HttpResponseRedirect("/convenios")

                elif action == 'vertipos':
                    tipo = TipoConvenio.objects.filter()
                    data['tipos'] = tipo
                    if 'error' in request.GET:
                        data['error'] = 1
                    return render(request ,"vinculacion/tipoconvenio.html" ,  data)
                return HttpResponseRedirect("/convenios")

            else:
                search = ""
                activos = None
                inactivos = None
                todos = None
                carrera = ''
                carreracon = ''
                banc = 0
                banm = 0


                if 's' in request.GET:
                    search = request.GET['s']
                if 't' in request.GET:
                    todos = request.GET['t']
                if 'a' in request.GET:
                    activos = request.GET['a']
                if 'i' in request.GET:
                    inactivos = request.GET['i']

                if search:
                    convenio = Convenio.objects.filter(Q(institucion__icontains=search)).order_by('-inicio','-activo','institucion')
                else:
                    convenio = Convenio.objects.all().order_by('-inicio','-activo','institucion')

                if todos:
                    convenio = Convenio.objects.all().order_by('-inicio','-activo','institucion')

                if activos:
                    convenio = Convenio.objects.filter(activo=True).order_by('-inicio','institucion')

                if inactivos:
                    convenio = Convenio.objects.filter(activo=False).order_by('-inicio','institucion')


                if 'car' in request.GET:
                    if  request.GET['car'] != '0'  and request.GET['car'] != '':
                        data['carrera_id']=Carrera.objects.filter(pk=request.GET['car'])[:1].get()
                        convenio=convenio.filter(carreraconvenio__carrera = data['carrera_id']).distinct().order_by('-inicio','institucion')

                if 'mod' in request.GET:
                    if  request.GET['mod'] != '0' and request.GET['mod'] != '':
                        data['modalidad_id']=Modalidad.objects.filter(pk=request.GET['mod'])[:1].get()
                        convenio =  convenio.filter(carreraconvenio__modalidadcarreraconvenio__modalidad=data['modalidad_id']).distinct().order_by('-inicio','institucion')

                if 'cla' in request.GET:
                    if  request.GET['cla'] != '0' and request.GET['cla'] != '':
                        data['clasificacion_id']=Clasificacion.objects.filter(pk=request.GET['cla'])[:1].get()
                        convenio =  convenio.filter(convenioclasificacion__clasificacion=data['clasificacion_id']).distinct().order_by('-inicio','institucion')

                if 'tipo' in request.GET:
                    tipo = TipoConvenio.objects.filter(pk=request.GET['tipo'])[:1].get()
                    data['tipo_id'] = tipo
                    convenio = convenio.filter(tipo=tipo)

                paging = MiPaginador(convenio, 30)
                p = 1
                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                        # if band==0:
                        #     inscripciones = Inscripcion.objects.all().order_by('persona__apellido1')
                        paging = MiPaginador(convenio, 30)
                    page = paging.page(p)
                except Exception as ex:
                    page = paging.page(1)

                data['paging'] = paging
                data['rangospaging'] = paging.rangos_paginado(p)
                data['page'] = page
                data['convenio'] = page.object_list
                data['todos'] = todos if todos else ""
                data['activos'] = activos if activos else ""
                data['inactivos'] = inactivos if inactivos else ""
                data['search'] = search if search else ""
                data['datoform'] = DatoForm()
                data['datoform2'] = DatoForm2()
                data['datoform3'] = DatoForm3()
                data['carreras'] = Carrera.objects.filter(activo=True).order_by('nombre')
                data['modalidad'] = Modalidad.objects.filter().order_by('nombre')
                data['clasificacion'] = Clasificacion.objects.filter().order_by('nombre')
                data['tipo'] = TipoConvenio.objects.filter().order_by('nombre')
                data['formtipo'] = TipoConvenioForm
                return render(request ,"vinculacion/convenio.html" ,  data)
        except Exception as ex:
            pass

