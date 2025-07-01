import datetime
from django.contrib.admin.models import LogEntry, CHANGE, DELETION, ADDITION
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
from sga.alu_matricula import MiPaginador
from sga.commonviews import addUserData
from sga.forms import PermisoSgaForm
from sga.models import PermisosSga
from socioecon.cons_socioecon import ip_client_address
import json

def view(request):
    if request.method=='POST':

        if 'action' in request.POST:
            action = request.POST['action']
            if action=='add':
                p= PermisoSgaForm(request.POST)
                if p.is_valid():
                    try:
                        if request.POST['idpermiso']=='':
                            idpermiso=0
                        else:
                             idpermiso=request.POST['idpermiso']
                        if PermisosSga.objects.filter(pk=idpermiso).exists():
                            edit=PermisosSga.objects.get(pk=idpermiso)
                            edit.modulo=p.cleaned_data['modulo']
                            edit.permiso = p.cleaned_data['permiso']
                            edit.observacion = p.cleaned_data['observacion']
                            edit.accion = p.cleaned_data['accion']

                            mensaje = 'Edicion de Permiso'
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
                            return HttpResponseRedirect('/permisosga')
                        else:
                            permiso=PermisosSga(modulo=p.cleaned_data['modulo'],
                                     permiso=p.cleaned_data['permiso'],
                                     observacion=p.cleaned_data['observacion'],
                                     accion=p.cleaned_data['accion'])

                            permiso.save()
                            msj='Guardado registro'
                            client_address = ip_client_address(request)
                            LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(permiso).pk,
                            object_id       = permiso.id,
                            object_repr     = force_str(permiso),
                            action_flag     = ADDITION,
                            change_message  = msj + ' (' + client_address + ')')
                            return HttpResponseRedirect("/permisosga")
                    except Exception as e:
                       return HttpResponseRedirect("/permisosga?error="+str(e))
                else:
                    return HttpResponseRedirect("/permisosga?error=Error en el Formulario")

            elif action == 'eliminar_permiso':
                result={}
                try:
                    eliminar =PermisosSga.objects.filter(pk=request.POST['idpermiso'])[:1].get()
                    mensaje = 'Eliminar datos'
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
        data = {'title': 'Listado de Permisos'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
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
                try:
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')
                    if len(ss)==1:
                        permiso = PermisosSga.objects.filter(Q(modulo__nombre__icontains=search) | Q(accion__icontains=search) | Q(permiso__icontains=search)).order_by('modulo','accion','permiso')
                    else:
                        permiso = PermisosSga.objects.filter(Q(modulo__nombre__icontains=ss[0]) & Q(accion__icontains=ss[1])).order_by('modulo','accion')
                except Exception as e:
                    pass
            else:
                permiso = PermisosSga.objects.all().order_by('modulo','accion')


            paging = MiPaginador(permiso, 30)
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
            data['form'] = PermisoSgaForm()
            data['permiso'] = page.object_list
            if 'error' in request.GET:
                data['error']= request.GET['error']
            return render(request ,"permisosga/permisosga.html" ,  data)

