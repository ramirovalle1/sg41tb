from datetime import datetime, timedelta
from django.contrib.admin.models import LogEntry, DELETION, CHANGE, ADDITION
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
from settings import TIPO_OTRO_RUBRO
from sga.forms import LugarRecaudacionForm, GrupoSeminarioForm, GrupoPonenciaForm, InscripcionPonenciaForm, ComisionCongresoForm
from sga.models import LugarRecaudacion, GrupoSeminario, InscripcionSeminario, RubroOtro,GrupoPonencia, InscripcionGrupoPonencia, Inscripcion, ObservacionInscripcion, TipoOtroRubro, Rubro, ComisionCongreso
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

def view(request):
    if request.method=='POST':
        if 'action' in request.POST:
            action = request.POST['action']
            if action == 'add':
                try:
                    f = GrupoPonenciaForm(request.POST)
                    if f.is_valid():
                        try:
                            if request.POST['ban'] == '1':
                                ponencia = GrupoPonencia(nombre=f.cleaned_data['nombre'],
                                                         codigo=f.cleaned_data['codigo'],
                                                         horainicio = f.cleaned_data['horainicio'],
                                                         horafin = f.cleaned_data['horafin'],
                                                         integrantes = f.cleaned_data['integrantes'],
                                                         precio=f.cleaned_data['precio'],
                                                         revisadopor=f.cleaned_data['revisadopor'],
                                                         comision = f.cleaned_data['comision'],
                                                         tipo = f.cleaned_data['tipo'],
                                                         ubicacion = f.cleaned_data['ubicacion'],
                                                         modalidad = f.cleaned_data['modalidad'],
                                                         numero = f.cleaned_data['numero'],
                                                         activo = True)
                                ponencia.save()
                                mensaje = 'Adicionado'

                            else:
                                print(f.cleaned_data['integrantes'])
                                ponencia = GrupoPonencia.objects.get(pk=int(request.POST['ponencia']))
                                ponencia.nombre=f.cleaned_data['nombre']
                                ponencia.codigo=f.cleaned_data['codigo']
                                ponencia.horainicio = f.cleaned_data['horainicio']
                                ponencia.horafin = f.cleaned_data['horafin']
                                ponencia.integrantes = f.cleaned_data['integrantes']
                                ponencia.precio=f.cleaned_data['precio']
                                ponencia.revisadopor=f.cleaned_data['revisadopor']
                                ponencia.comision = f.cleaned_data['comision']
                                ponencia.ubicacion = f.cleaned_data['ubicacion']
                                ponencia.modalidad = f.cleaned_data['modalidad']
                                ponencia.tipo = f.cleaned_data['tipo']
                                ponencia.numero = f.cleaned_data['numero']
                                ponencia.activo=True
                                ponencia.save()
                                mensaje = 'Editado'

                        # Log Agregar Ponencia
                            client_address = ip_client_address(request)
                            LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(ponencia).pk,
                                object_id       = ponencia.id,
                                object_repr     = force_str(ponencia),
                                action_flag     = ADDITION,
                                change_message  = mensaje + " Ponencia " +  '(' + client_address + ')' )

                            return HttpResponseRedirect("/ponencia?s="+str(ponencia.codigo  ))
                        except Exception as ex:
                            if request.POST['ban'] == '1':
                                return HttpResponseRedirect("ponencia?action=add&error=1",)
                            else:
                                return HttpResponseRedirect("ponencia?action=editar&error=1&id="+str(request.POST['ponencia']),)
                    else:
                        if request.POST['ban'] == '1':
                            return HttpResponseRedirect("ponencia?action=add&error=1",)
                        else:
                            return HttpResponseRedirect("ponencia?action=editar&error=1&id="+str(request.POST['ponencia']),)
                except Exception as ex:
                    return HttpResponseRedirect('/ponencia?error=Error al ingresar ponencia, vuelva a intentarlo')

            elif action == 'activar_estado':
                try:
                    ponencia =  GrupoPonencia.objects.get(pk=request.POST['id'])
                    if ponencia.activo:
                        mensaje = 'Desactivacion de ponencia'
                    else:
                        mensaje = 'Activacion de ponencia'
                    ponencia.activo =  not ponencia.activo
                    ponencia.save()
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(ponencia).pk,
                        object_id       = ponencia.id,
                        object_repr     = force_str(ponencia),
                        action_flag     = ADDITION,
                        change_message  = mensaje+' (' + client_address + ')' )

                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

            elif action == 'desactivar_todas':
                try:
                    ponencia =  GrupoPonencia.objects.filter(activo=True)
                    if ponencia.exists():
                        for p in ponencia:
                            p.activo =  False
                            p.save()
                        return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({"result":"No existen ponencias activas"}),content_type="application/json")

                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

            if action == 'add_comision':
                try:
                    print(request.POST)
                    print(request.GET)
                    if request.POST['idcomision']=='':
                        id_comision=0
                    else:
                        id_comision=request.POST['idcomision']
                    if 'activo' in request.POST:
                        activo = True
                    else:
                        activo = False

                    if ComisionCongreso.objects.filter(pk=id_comision).exists():
                        edit = ComisionCongreso.objects.get(pk=id_comision)

                        edit.nombre = request.POST['nombre']
                        edit.moderador =request.POST['moderador']
                        edit.lugar  = request.POST['lugar']
                        edit.fecha = request.POST['fecha']
                        edit.horainicio = request.POST['horainicio']
                        edit.horafin = request.POST['horafin']
                        edit.activo = activo
                        edit.ubicacion = request.POST['ubicacion']
                        edit.imgubicacion = request.POST['imgubicacion']

                        mensaje = 'Edicion de comision'
                        edit.save()
                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(edit).pk,
                        object_id       = edit.id,
                        object_repr     = force_str(edit),
                        action_flag     = CHANGE,
                        change_message  = mensaje+' (' + client_address + ')' )
                    else:
                        add = ComisionCongreso(nombre=request.POST['nombre'],
                                                moderador =request.POST['moderador'],
                                                lugar  = request.POST['lugar'],
                                                fecha = request.POST['fecha'],
                                                horainicio = request.POST['horainicio'],
                                                horafin = request.POST['horafin'],
                                                activo = activo,
                                                ubicacion = request.POST['ubicacion'],
                                                imgubicacion = request.POST['imgubicacion'])
                        mensaje = 'Ingreso de nueva comision'
                        add.save()
                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(add).pk,
                        object_id       = add.id,
                        object_repr     = force_str(add),
                        action_flag     = ADDITION,
                        change_message  = mensaje+' (' + client_address + ')' )
                    return HttpResponseRedirect('/ponencia?action=comisiones')

                except Exception as ex:
                    print(ex)
                    return HttpResponseRedirect('/ponencia?action=comisiones?error=Error al ingresar ponencia, vuelva a intentarlo')

            elif action == 'eliminar_comision':
                result = {}
                try:
                    if GrupoPonencia.objects.filter(comision__id=request.POST['idcomision']).exists():
                        result['result']  = "No se puede eliminar, registro utilizado por otros modelos"
                        return HttpResponse(json.dumps(result), content_type="application/json")
                    else:
                        eliminar =ComisionCongreso.objects.filter(pk=request.POST['idcomision'])[:1].get()
                        mensaje = 'Eliminar comision'
                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(eliminar).pk,
                            object_id       = eliminar.id,
                            object_repr     = force_str(eliminar),
                            action_flag     = DELETION,
                            change_message  = mensaje+' (' + client_address + ')' )
                        eliminar.delete()
                        result['result']  = "ok"
                        return HttpResponse(json.dumps(result), content_type="application/json")
                except Exception as e:
                    result['result']  = str(e)
                    return HttpResponse(json.dumps(result), content_type="application/json")

            elif action == 'desactivar_todas_comisiones':
                try:
                    print(request.POST)
                    comision =  ComisionCongreso.objects.filter(activo=True)
                    if comision.exists():
                        for p in comision:
                            p.activo =  False
                            p.save()
                        return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({"result":"No existen comisiones activas"}),content_type="application/json")
                except:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

            elif action == 'activar_estado_comision':
                try:
                    comision =  ComisionCongreso.objects.get(pk=request.POST['id'])
                    if comision.activo:
                        mensaje = 'Desactivacion de ponencia'
                    else:
                        mensaje = 'Activacion de ponencia'
                    comision.activo =  not comision.activo
                    comision.save()
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(comision).pk,
                        object_id       = comision.id,
                        object_repr     = force_str(comision),
                        action_flag     = ADDITION,
                        change_message  = mensaje+' (' + client_address + ')' )

                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")


    else:
        data = {'title': 'Aporte Cientifico'}
        addUserData(request,data)
        try:
            if 'action' in request.GET:
                action = request.GET['action']

                if action == 'add':
                    data['form'] = GrupoPonenciaForm(initial={"fecha":datetime.now().date()})
                    if 'error' in request.GET:
                        data['error'] = 1
                    data['ban'] =1
                    return render(request ,"ponencia/add.html" ,  data)

                if action == 'ver':
                    data['ponencia'] = GrupoPonencia.objects.get(pk=request.GET['id'])
                    data['inscritos'] = InscripcionGrupoPonencia.objects.filter(grupoponencia__id=request.GET['id']).order_by('matricula__inscripcion__persona__apellido1')

                    return render(request ,"ponencia/ver.html" ,  data)

                if action == 'eliminarins':
                    i =  InscripcionGrupoPonencia.objects.get(pk=request.GET['id'])
                    g = i.grupoponencia.id
                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de Eliminar Inscripcion Grupo Ponencia
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(i).pk,
                        object_id       = i.id,
                        object_repr     = force_str(i),
                        action_flag     = DELETION,
                        change_message  = 'Eliminada Inscripcion Ponencia (' + client_address + ')'  )
                    i.delete()

                    return HttpResponseRedirect("/ponencia?action=ver&id="+str(g))

                if action == 'addparticipantes':
                    try:
                        magisterio=""
                        ponencia = GrupoPonencia.objects.get(pk=request.GET['id'])
                        if request.GET['inscripcion']:
                            inscripcion=Inscripcion.objects.get(pk=request.GET['inscripcion'])
                            if InscripcionGrupoPonencia.objects.filter(grupoponencia=ponencia,autor=True).exists():
                                matri =InscripcionGrupoPonencia.objects.get(grupoponencia=ponencia,autor=True)
                                return HttpResponse(json.dumps({"result":"autor","autorponencia":str(matri.matricula.inscripcion.persona.nombre_completo_inverso())}),content_type="application/json")
                            else:
                                if inscripcion.matricula():
                                    matricula = inscripcion.matricula()
                                    if not InscripcionGrupoPonencia.objects.filter(grupoponencia=ponencia,matricula=matricula).exists():
                                        if ponencia.inscritos()+1 <= ponencia.integrantes:
                                            inscrip_ponencia = InscripcionGrupoPonencia(grupoponencia=ponencia,
                                                               matricula = matricula,
                                                               institucion=request.GET['insti'],
                                                               usuario=request.user,
                                                               fecha=datetime.now())
                                            inscrip_ponencia.save()

                                            if  ObservacionInscripcion.objects.filter(inscripcion=matricula.inscripcion,tipo__id=3).exists():
                                                    magisterio="Si"
                                                    tipootro = TipoOtroRubro.objects.get(pk=TIPO_OTRO_RUBRO)
                                                    rubro = Rubro(fecha=datetime.now().date(),
                                                                  valor=ponencia.precio,
                                                                  inscripcion=matricula.inscripcion,
                                                                  cancelado=False,
                                                                  fechavence=datetime.now())
                                                    rubro.save()
                                                    rubrootro = RubroOtro(rubro=rubro, tipo=tipootro, descripcion='PONENCIA ' + str(ponencia.id) + ' - '+str(ponencia.codigo) )

                                                    rubrootro.save()
                                                    inscrip_ponencia.rubrootro = rubrootro
                                                    inscrip_ponencia.save()

                                            # Obtain client ip address
                                            client_address = ip_client_address(request)
                                            # Log de ADICIONAR AUTOR PONENCIA
                                            LogEntry.objects.log_action(
                                                user_id         = request.user.pk,
                                                content_type_id = ContentType.objects.get_for_model(ponencia).pk,
                                                object_id       = inscripcion.id,
                                                object_repr     = force_str(ponencia),
                                                action_flag     = ADDITION,
                                                change_message  = 'Adicionado Autor Ponencia (' + client_address + ')' )
                                            if magisterio:
                                                return HttpResponse(json.dumps({"result":"mag","magisterio":magisterio,"costo":str(ponencia.precio)}),content_type="application/json")
                                            else:
                                                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                                        else:
                                          return HttpResponse(json.dumps({"result":"bad1","integrantes":str(ponencia.integrantes)}),content_type="application/json")
                                    else:
                                          return HttpResponse(json.dumps({"result":"bad3","inscrip2":str(inscripcion)}),content_type="application/json")
                                else:
                                  return HttpResponse(json.dumps({"result":"bad2","inscrip":str(inscripcion)}),content_type="application/json")
                        else:
                                if ponencia.inscritos()+1 <= ponencia.integrantes:
                                    coautor=  request.GET['coautor']
                                    # coautor = coautor.upper( )
                                    inscrip_ponencia = InscripcionGrupoPonencia(grupoponencia=ponencia,
                                                       coautor =coautor,
                                                       autor=False,
                                                       institucion=request.GET['insti'],
                                                       usuario=request.user,
                                                       fecha=datetime.now())
                                    inscrip_ponencia.save()

                                    # Obtain client ip address
                                    client_address = ip_client_address(request)
                                    # Log de ADICIONAR COAUTORES PONENCIA
                                    LogEntry.objects.log_action(
                                        user_id         = request.user.pk,
                                        content_type_id = ContentType.objects.get_for_model(ponencia).pk,
                                        object_id       = ponencia.id,
                                        object_repr     = force_str(ponencia),
                                        action_flag     = ADDITION,
                                        change_message  = 'Adicionado Coautor Ponencia (' + client_address + ')' )
                                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                                else:
                                    return HttpResponse(json.dumps({"result":"bad1","integrantes":str(ponencia.integrantes)}),content_type="application/json")

                    except Exception as ex:
                        print(ex)

                if action == 'eliminar':
                    i =  GrupoPonencia.objects.get(pk=request.GET['id'])
                    g = i
                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de ELIMINAR Ponencia
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(i).pk,
                        object_id       = i.id,
                        object_repr     = force_str(i),
                        action_flag     = DELETION,
                        change_message  = 'Eliminada Ponencia (' + client_address + ')'  )
                    i.delete()
                    return HttpResponseRedirect("/ponencia")

                elif action == 'editar':
                    ponencia = GrupoPonencia.objects.get(pk=request.GET['id'])
                    initial = model_to_dict(ponencia)
                    data['form'] = GrupoPonenciaForm(initial=initial)
                    if 'error' in request.GET:
                        data['error'] = 1
                    data['ban'] = 2
                    data['ponencia'] =ponencia
                    return render(request ,"ponencia/add.html" ,  data)

                elif action == 'comisiones':
                    try:
                        search = ""
                        if 's' in request.GET:
                            search = request.GET['s']

                        if 'inactivos' in request.GET:
                            comision = ComisionCongreso.objects.filter(activo=False).order_by('-fecha','horainicio','nombre')
                            data['estado'] = 1
                        else:
                            comision = ComisionCongreso.objects.filter(activo=True).order_by('-fecha','horainicio','nombre')
                        if search:
                            comision = comision.filter(Q(nombre__icontains=search)|Q(moderador__icontains=search)).order_by('-fecha','horainicio','nombre')

                        data['comisiones'] = comision
                        data['search'] = search if search else ""
                        data['fechaactual']=datetime.now().date()
                        data['form'] = ComisionCongresoForm(initial={"fecha":datetime.now().date()})
                        if 'error' in request.GET:
                            data['error'] = 1
                        return render(request ,"ponencia/comisionesbs.html" ,  data)
                    except Exception as ex:
                        print(ex)

            else:
                search = ""
                if 's' in request.GET:
                    search = request.GET['s']
                ponencia = GrupoPonencia.objects.all()
                if 'inactivos' in request.GET:
                    ponencia = ponencia.filter(activo=False).order_by('-codigo')
                    data['estado_inactivos'] = 1
                elif 'ensayos' in request.GET:
                    ponencia = ponencia.filter(activo=True, tipo__id=2).order_by('-codigo')
                    data['estado_ensayos'] = 1
                elif 'ponencias' in request.GET:
                    ponencia = ponencia.filter(activo=True, tipo__id=1).order_by('-codigo')
                    data['estado_ponencias'] = 1
                else:
                    ponencia = ponencia.filter().exclude(activo=False).order_by('-codigo')
                if search:
                    ponencia = ponencia.filter(Q(nombre__icontains=search)|Q(codigo__icontains=search)).order_by('-codigo')
                if 'p' in request.GET:
                    p = request.GET['p']
                    ponencia = GrupoPonencia.objects.filter().order_by('-codigo')
                paging = MiPaginador(ponencia, 25)
                p = 1
                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                        paging = MiPaginador(ponencia, 25)
                    page = paging.page(p)
                except Exception as ex:
                    page = paging.page(1)

                data['paging'] = paging
                data['rangospaging'] = paging.rangos_paginado(p)
                data['page'] = page
                data['ponencia'] = page.object_list
                data['search'] = search if search else ""
                docuform = InscripcionPonenciaForm()
                data['docuform']=docuform
                data['total_participantes']= InscripcionGrupoPonencia.objects.filter(activo=True, grupoponencia__activo=True).count()
                data['num_ensayos']= InscripcionGrupoPonencia.objects.filter(activo=True, grupoponencia__activo=True, grupoponencia__tipo__id=2).count()
                data['num_ponencias']= InscripcionGrupoPonencia.objects.filter(activo=True, grupoponencia__activo=True, grupoponencia__tipo__id=1).count()

                return render(request ,"ponencia/ponencia.html" ,  data)
        except Exception as e:
            pass