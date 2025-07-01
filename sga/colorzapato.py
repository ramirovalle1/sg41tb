import json
from django.contrib.admin.models import LogEntry, CHANGE, ADDITION, DELETION
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
from sga.alu_matricula import MiPaginador
from sga.commonviews import addUserData
from sga.forms import UniformeForm
from sga.models import  ColorZapato
from socioecon.cons_socioecon import ip_client_address


def view(request):
    if request.method=='POST':

        if 'action' in request.POST:
            action = request.POST['action']
            if action=='add':
                u= UniformeForm(request.POST)
                if u.is_valid():
                    try:
                        if request.POST['idcolorzapato']=='':
                            idcolorzapato=0
                        else:
                             idcolorzapato=request.POST['idcolorzapato']
                        if ColorZapato.objects.filter(pk=idcolorzapato).exists():
                            edit=ColorZapato.objects.get(pk=idcolorzapato)
                            edit.nombre=u.cleaned_data['nombre']
                            mensaje = 'Edicion de Color de Zapato'
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
                            return HttpResponseRedirect('/colorzapato')
                        else:
                            colorzapato=ColorZapato(nombre=u.cleaned_data['nombre'])
                            colorzapato.save()
                            msj='Adicionado color de zapato'
                            client_address = ip_client_address(request)
                            LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(colorzapato).pk,
                            object_id       = colorzapato.id,
                            object_repr     = force_str(colorzapato),
                            action_flag     = ADDITION,
                            change_message  = msj + ' (' + client_address + ')')
                            return HttpResponseRedirect("/colorzapato")
                    except Exception as e:
                        return HttpResponseRedirect("/colorzapato?error="+str(e))
                else:
                    return HttpResponseRedirect("/colorzapato?error=Error en el Formulario")

            elif action == 'eliminar_colorzapato':
                result={}
                try:
                    colorzapato =ColorZapato.objects.filter(pk=request.POST['idcolorzapato'])[:1].get()
                    mensaje = 'Eliminado Color de zapato'
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(colorzapato).pk,
                        object_id       = colorzapato.id,
                        object_repr     = force_str(colorzapato),
                        action_flag     = DELETION,
                        change_message  = mensaje+' (' + client_address + ')' )
                    colorzapato.delete()
                    result['result']  = "ok"
                    return HttpResponse(json.dumps(result), content_type="application/json")
                except Exception as e:
                    result['result']  = str(e)
                    return HttpResponse(json.dumps(result), content_type="application/json")
    else:
        data = {'title': 'Listado de Tallas de Zapatos'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
        else:
            search  = None
            filtro  = None
            colorzapato = None
            ejerce = None
            cargo = None
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
                        colorzapato = ColorZapato.objects.filter(nombre__icontains=search).order_by('nombre')
                    else:
                        colorzapato = ColorZapato.objects.all().order_by('nombre')
                except Exception as e:
                    pass
            else:
                colorzapato = ColorZapato.objects.all().order_by('nombre')


            paging = MiPaginador(colorzapato, 30)
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
            data['form'] = UniformeForm()
            data['colorzapato'] = page.object_list
            if 'error' in request.GET:
                data['error']= request.GET['error']
            return render(request ,"colorzapato/colorzapato.html" ,  data)
