from datetime import datetime
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
import json
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
from decorators import secure_module
from sga.commonviews import addUserData, ip_client_address
from sga.forms import MallaForm, AsignaturaMallaForm, SyllabusForm, CapituloForm, TemaForm, DetTemaForm, SubTemaForm, HabilidadesForm,  HorasForm
from sga.models import SyllabusCampos, Syllabus, CamposFormacion,AsignaturaMalla, UnidadOrganizacion,CapituloSyllabus, TemaSyllabus, DetalleTema, DetalleCapitulo, SubTemaSyll,Malla, DetalleSubTemaSyll, HabilidadesTema, ValoresTema, HorasTema
from settings import MEDIA_ROOT
import os

@login_required(redirect_field_name='ret', login_url='/login')
# @secure_module
def view(request):
    if request.method=='POST':
        action = request.POST['action']
        if action == 'addcap':
            try:
                syllabus = Syllabus.objects.filter(pk=request.POST['id'])[:1].get()
                if request.POST['op']=='0':
                    capitulo = CapituloSyllabus(syllabus=syllabus,
                                                numero=request.POST['num'],
                                                nombre=request.POST['nombre'],
                                                orden=request.POST['orden'],
                                                contenido=request.POST['contenido'])
                    capitulo.save()
                else:
                    capitulo = CapituloSyllabus.objects.get(pk=request.POST['cap'])
                    capitulo.numero=request.POST['num']
                    capitulo.nombre=request.POST['nombre']
                    capitulo.orden=request.POST['orden']
                    capitulo.contenido=request.POST['contenido']
                    capitulo.save()


                if request.POST['det'] == '1':
                    capitulo.tiene_detalle = True
                    capitulo.save()
                else:
                    capitulo.tiene_detalle = False
                    capitulo.save()

                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            except Exception as ex:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

        elif action == 'addarchivo':
                f = SyllabusForm(request.POST,request.FILES)
                if Syllabus.objects.filter(pk=request.POST['id_syllabus']).exists():
                    syllabus = Syllabus.objects.filter(pk=request.POST['id_syllabus'])[:1].get()
                    if f.is_valid():
                        if 'archivo' in request.FILES:
                            archivo = request.FILES['archivo']
                        else:
                            archivo = ''

                            if str(syllabus.archivo):
                                if (MEDIA_ROOT + '/' + str(syllabus.archivo)) and archivo:
                                    os.remove(MEDIA_ROOT + '/' + str(syllabus.archivo))
                            if archivo:
                                syllabus.archivo = archivo

                                syllabus.save()
                                client_address = ip_client_address(request)
                                LogEntry.objects.log_action(
                                    user_id         = request.user.pk,
                                    content_type_id = ContentType.objects.get_for_model(syllabus).pk,
                                    object_id       = syllabus.id,
                                    object_repr     = force_str(syllabus),
                                    action_flag     = ADDITION,
                                    change_message  = ' Adicionado Archivo Syllabus (' + client_address + ')' )

                            return HttpResponseRedirect('/syllabus?action=ver&id='+str(syllabus.asigmalla.id)+"&malla="+str(request.POST['id_malla']))
                    else:
                        return HttpResponseRedirect("/syllabus?action=ver&id="+str(syllabus.asigmalla.id)+"&malla="+str(request.POST['id_malla'])+"&error=el archivo no tiene el formato correcto")
        elif action == 'addtema':
            try:
                capsyllabus = CapituloSyllabus.objects.filter(pk=request.POST['id'])[:1].get()
                if request.POST['op']=='0':
                    tema = TemaSyllabus(capitulo=capsyllabus,
                                        numero=request.POST['num'],
                                        nombre=request.POST['nombre'],
                                        orden=request.POST['orden'],
                                        contenido=request.POST['contenido'])
                    tema.save()
                else:
                    tema = TemaSyllabus.objects.get(pk=request.POST['tid'])
                    tema.numero=request.POST['num']
                    tema.nombre=request.POST['nombre']
                    tema.orden=request.POST['orden']
                    tema.contenido=request.POST['contenido']
                    tema.save()

                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            except Exception as ex:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

        elif action == 'addprerequisito':
            try:
                syllabus = Syllabus.objects.filter(pk=request.POST['id'])[:1].get()
                syllabus.prerrequisito=request.POST['prer']
                syllabus.save()

                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            except Exception as ex:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

        elif action == 'addcorequisito':
            try:
                syllabus = Syllabus.objects.filter(pk=request.POST['id'])[:1].get()
                syllabus.correquisito=request.POST['correquisito']
                syllabus.save()

                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            except Exception as ex:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

        elif action == 'adddettema':
            try:
                if request.POST['op']=='0':
                    tema= TemaSyllabus.objects.filter(pk=request.POST['id'])[:1].get()
                    dettema = DetalleTema(tema=tema,
                                       descripcion =request.POST['descripcion'])
                    dettema.save()
                else:
                    dettema = DetalleTema.objects.get(pk=request.POST['det'])
                    dettema.descripcion =request.POST['descripcion']
                    dettema.save()

                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            except Exception as ex:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

        elif action == 'adddetcap':
            try:
                if request.POST['op']=='0':
                    capitulo= CapituloSyllabus.objects.filter(pk=request.POST['id'])[:1].get()
                    detcapitulo = DetalleCapitulo(capitulo=capitulo,
                                       descripcion =request.POST['descripcion'])
                    detcapitulo.save()
                else:
                    detcapitulo = DetalleCapitulo.objects.get(pk=request.POST['dc'])
                    detcapitulo.descripcion=request.POST['descripcion']
                    detcapitulo.save()

                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            except Exception as ex:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

        elif action == 'adddsubtema':
            try:
                if request.POST['op']=='0':
                    tema= TemaSyllabus.objects.filter(pk=request.POST['id'])[:1].get()
                    subtema = SubTemaSyll(tema=tema,
                                       contenido =request.POST['descripcion'],
                                       numero=request.POST['numero'])
                    subtema.save()
                else:
                    subtema = SubTemaSyll.objects.get(pk=request.POST['sub'])
                    subtema.contenido=request.POST['descripcion']
                    subtema.numero=request.POST['numero']
                    subtema.save()

                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            except Exception as ex:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

        elif action == 'adddetalle':
            try:
                if request.POST['op']=='0':
                    subtema= SubTemaSyll.objects.filter(pk=request.POST['id'])[:1].get()
                    detsubtema = DetalleSubTemaSyll(subtema=subtema,
                                       contenido =request.POST['descripcion'],
                                       numero=request.POST['numero'])
                    detsubtema.save()
                else:
                    detsubtema = DetalleSubTemaSyll.objects.get(pk=request.POST['sub'])
                    detsubtema.contenido=request.POST['descripcion']
                    detsubtema.numero=request.POST['numero']
                    detsubtema.save()

                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            except Exception as ex:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

        elif action == 'addhabilidad':
            try:
                if request.POST['op']=='0':
                    tema= TemaSyllabus.objects.filter(pk=request.POST['id'])[:1].get()
                    habilidad= HabilidadesTema(tema=tema,
                                       descripcion =request.POST['habilidad'])
                    habilidad.save()
                else:
                    habilidad = HabilidadesTema.objects.get(pk=request.POST['hab'])
                    habilidad.descripcion=request.POST['habilidad']
                    habilidad.save()

                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            except Exception as ex:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

        elif action == 'deletecap':
            try:
                capitulo = CapituloSyllabus.objects.get(pk=request.POST['id'])
                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(capitulo).pk,
                    object_id       = capitulo.id,
                    object_repr     = force_str(capitulo),
                    action_flag     = DELETION,
                    change_message  = 'Eliminado Capitulo Syllabus (' + client_address + ')' )
                capitulo.delete()
                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            except Exception as ex:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

        elif action == 'deletedetcap':
            try:
                detcapitulo = DetalleCapitulo.objects.get(pk=request.POST['id'])
                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(detcapitulo).pk,
                    object_id       = detcapitulo.id,
                    object_repr     = force_str(detcapitulo),
                    action_flag     = DELETION,
                    change_message  = 'Eliminado Detalle Capitulo Syllabus (' + client_address + ')' )
                detcapitulo.delete()
                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            except Exception as ex:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

        elif action == 'deletedetalle':
            try:
                detallesub = DetalleSubTemaSyll.objects.get(pk=request.POST['id'])
                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(detallesub).pk,
                    object_id       = detallesub.id,
                    object_repr     = force_str(detallesub),
                    action_flag     = DELETION,
                    change_message  = 'Eliminado Detalle de SubTema (' + client_address + ')' )
                detallesub.delete()
                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            except Exception as ex:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

        elif action == 'deletesubtema':
            try:
                subtema = SubTemaSyll.objects.get(pk=request.POST['id'])
                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(subtema).pk,
                    object_id       = subtema.id,
                    object_repr     = force_str(subtema),
                    action_flag     = DELETION,
                    change_message  = 'Eliminado SubTema (' + client_address + ')' )
                subtema.delete()
                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            except Exception as ex:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

        elif action == 'deletedettema':
            try:
                detema = DetalleTema.objects.get(pk=request.POST['id'])
                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(detema).pk,
                    object_id       = detema.id,
                    object_repr     = force_str(detema),
                    action_flag     = DELETION,
                    change_message  = 'Eliminado Detalle Tema (' + client_address + ')' )
                detema.delete()
                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            except Exception as ex:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

        elif action == 'deletetema':
            try:
                tema = TemaSyllabus.objects.get(pk=request.POST['id'])
                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(tema).pk,
                    object_id       = tema.id,
                    object_repr     = force_str(tema),
                    action_flag     = DELETION,
                    change_message  = 'Eliminado Tema (' + client_address + ')' )
                tema.delete()
                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            except Exception as ex:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

        elif action == 'deletehab':
            try:
                hab = HabilidadesTema.objects.get(pk=request.POST['id'])
                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(hab).pk,
                    object_id       = hab.id,
                    object_repr     = force_str(hab),
                    action_flag     = DELETION,
                    change_message  = 'Eliminada Habilidad (' + client_address + ')' )
                hab.delete()
                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            except Exception as ex:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

        elif action == 'deletevalores':
            try:
                valores = ValoresTema.objects.get(pk=request.POST['id'])
                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(valores).pk,
                    object_id       = valores.id,
                    object_repr     = force_str(valores),
                    action_flag     = DELETION,
                    change_message  = 'Eliminada Valores (' + client_address + ')' )
                valores.delete()
                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            except Exception as ex:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

        elif action == 'deletehora':
            try:
                horas = HorasTema.objects.get(pk=request.POST['id'])
                client_address = ip_client_address(request)
                if request.POST['op']=='d':
                    horas.d = None
                if request.POST['op']=='a':
                    horas.a = None
                if request.POST['op']=='p':
                    horas.p = None
                horas.save()
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(horas).pk,
                    object_id       = horas.id,
                    object_repr     = force_str(horas),
                    action_flag     = DELETION,
                    change_message  = 'Eliminada Hora '+ request.POST['op'] + ' (' + client_address + ')' )
                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            except Exception as ex:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

        elif action == 'addvalores':
            try:
                if request.POST['op']=='0':
                    tema= TemaSyllabus.objects.filter(pk=request.POST['id'])[:1].get()
                    valores= ValoresTema(tema=tema,
                                       descripcion =request.POST['valores'])
                    valores.save()
                else:
                    valores = ValoresTema.objects.get(pk=request.POST['val'])
                    valores.descripcion=request.POST['valores']
                    valores.save()

                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            except Exception as ex:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

        elif action == 'addhora':
            try:
                if not 'hid' in request.POST:
                    if request.POST['op']=='0':
                        tema= TemaSyllabus.objects.filter(pk=request.POST['id'])[:1].get()
                        horas= HorasTema(tema=tema)
                        horas.save()
                else:
                    horas = HorasTema.objects.get(pk=request.POST['hid'])

                if request.POST['opcion']=='d':
                    horas.d=request.POST['hora']

                elif request.POST['opcion']=='a':
                    horas.a=request.POST['hora']

                elif request.POST['opcion']=='p':
                    horas.p=request.POST['hora']
                horas.save()
                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            except Exception as ex:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")


        elif action == 'addunidad':
            try:
                syllabus = Syllabus.objects.filter(pk=request.POST['id'])[:1].get()
                unidad = UnidadOrganizacion.objects.get(pk=request.POST['unidad'])
                syllabus.unidadorg=unidad
                syllabus.save()
                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            except Exception as ex:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

        elif action == 'addcampo':
            try:
                syllabus = Syllabus.objects.filter(pk=request.POST['id'])[:1].get()
                campo= CamposFormacion.objects.get(pk=request.POST['idcampo'])
                if SyllabusCampos.objects.filter(campo=campo,syllabus=syllabus).exists():
                    c = SyllabusCampos.objects.filter(campo=campo,syllabus=syllabus)[:1].get()
                else:
                    c = SyllabusCampos(campo=campo,syllabus=syllabus)
                    c.save()
                if request.POST['campo'] == '0':
                    c.delete()

                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            except Exception as ex:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

        elif action == 'addlinea':
            try:
                syllabus = Syllabus.objects.filter(pk=request.POST['id'])[:1].get()
                syllabus.lineasinv=request.POST['linea']
                syllabus.save()

                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            except Exception as ex:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
        return HttpResponseRedirect("/syllabus")
    else:
        data = {'title': 'Syllabus'}
        addUserData(request,data)
        if "error" in request.GET:
            data['error'] = request.GET['error']
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='ver':
                data['title'] = 'Syllabus'
                asig = AsignaturaMalla.objects.get(pk=request.GET['id'])
                if Syllabus.objects.filter(asigmalla=asig).exists():
                    syllabus = Syllabus.objects.filter(asigmalla=asig)[:1].get()
                else:
                    syllabus = Syllabus(asigmalla=asig)
                    syllabus.save()
                if 'error' in request.GET:
                    data['error']=request.GET['error']

                # data['form'] = MallaForm(instance=Malla(inicio=datetime.now()))
                data['syllabus'] = syllabus
                data['asignatura'] = asig
                data['malla'] =request.GET['malla']
                data['campos'] = CamposFormacion.objects.filter(activo=True)
                data['camposyll'] = SyllabusCampos.objects.filter(syllabus=syllabus)
                data['unidad'] = UnidadOrganizacion.objects.filter(activo=True)
                data['capitulos'] = CapituloSyllabus.objects.filter(syllabus=syllabus).order_by('orden')
                data['form'] = CapituloForm()
                data['formtema'] = TemaForm()
                data['formdettema'] = DetTemaForm()
                data['formdetsubtema'] = SubTemaForm()
                data['formsyll'] = SyllabusForm()
                data['habilidadfrm'] = HabilidadesForm()
                data['horasfrm'] = HorasForm()
                return render(request ,"syllabus/syllabus.html" ,  data)
