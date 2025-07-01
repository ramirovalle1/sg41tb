from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType


from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
from sga.alu_matricula import MiPaginador
from sga.commonviews import addUserData, ip_client_address
from sga.forms import ParametroDescuentoForm, EmpresaSinConvenioForm
from sga.models import ParametroDescuento, EmpresaSinConvenio
import json


def view(request):
    if request.method=='POST':

        if 'action' in request.POST:
            action = request.POST['action']
            if action=='add':
                em=EmpresaSinConvenioForm(request.POST)
                if em.is_valid():
                    try:
                        if request.POST['idconvenio']=='':
                            idconvenio=0
                        else:
                             idconvenio=request.POST['idconvenio']
                        if EmpresaSinConvenio.objects.filter(pk=idconvenio).exists():
                            edit = EmpresaSinConvenio.objects.get(pk=idconvenio)
                            edit.nombre=em.cleaned_data['nombre']
                            edit.ruc = em.cleaned_data['ruc']
                            edit.activideconomica = em.cleaned_data['activideconomica']
                            edit.direccion = em.cleaned_data['direccion']
                            edit.estadoempresa = em.cleaned_data['estadoempresa']
                            edit.ciudad = em.cleaned_data['ciudad']
                            edit.estado = em.cleaned_data['estado']

                            mensaje = 'Edicion de Empresa sin convenio'
                            edit.save()
                            # Log de APLICAR DONACION
                            client_address = ip_client_address(request)
                            LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(edit).pk,
                            object_id       = edit.id,
                            object_repr     = force_str(edit),
                            action_flag     = CHANGE,
                            change_message  = mensaje+' (' + client_address + ')' )
                            return HttpResponseRedirect('/empresasinconvenio')
                        else:
                            empresa=EmpresaSinConvenio(nombre=em.cleaned_data['nombre'],
                                     ruc=em.cleaned_data['ruc'],
                                    activideconomica=em.cleaned_data['activideconomica'],
                                      direccion=em.cleaned_data['direccion'],
                                      estadoempresa=em.cleaned_data['estadoempresa'],
                                      ciudad=em.cleaned_data['ciudad'],
                                      estado=em.cleaned_data['estado'],)
                            empresa.save()
                            msj='Guardado registro de empresa sin convenio'
                            client_address = ip_client_address(request)
                            LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(empresa).pk,
                            object_id       = empresa.id,
                            object_repr     = force_str(empresa),
                            action_flag     = ADDITION,
                            change_message  = msj + ' (' + client_address + ')')
                            return HttpResponseRedirect("/empresasinconvenio")
                    except Exception as e:
                        return HttpResponseRedirect("/empresasinconvenio?error="+str(e))
                else:
                    return HttpResponseRedirect("/empresasinconvenio?error=Error en el formulario")

            elif action == 'eliminar_convenio':
                result={}
                try:
                    eliminar =EmpresaSinConvenio.objects.filter(pk=request.POST['idconvenio'])[:1].get()
                    mensaje = 'Eliminar empresa sin convenio'
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
    else:
        data = {'title': 'Listado de Empresas sin Convenio'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
        else:
            search  = None
            empresa=None
            filtro  = None

            if 'filter' in request.GET:
                filtro = request.GET['filter']
                data['filtro']  = filtro

            if 's' in request.GET:
                search = request.GET['s']

            if search:
                try:
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')
                    if len(ss)==1:
                        empresa= EmpresaSinConvenio.objects.filter(nombre=search).order_by('nombre')
                    else:
                        empresa = EmpresaSinConvenio.objects.filter(nombre=ss[0]) .order_by('nombre')
                except Exception as e:
                    pass
            else:
                empresa = EmpresaSinConvenio.objects.all().order_by('nombre')
            paging = MiPaginador(empresa, 30)
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
            data['search'] = search if search else ""
            data['form'] = EmpresaSinConvenioForm()
            data['convenio'] = page.object_list
            if 'error' in request.GET:
                data['error']= request.GET['error']
            return render(request ,"empresasinconvenio/empresasinconvenio.html" ,  data)
