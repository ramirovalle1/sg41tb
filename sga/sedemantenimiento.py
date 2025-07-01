import json
from datetime import datetime, date
from django.contrib.admin.models import LogEntry, CHANGE, ADDITION, DELETION
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
from sga.alu_matricula import MiPaginador
from sga.commonviews import addUserData
from sga.forms import AulaManForm,BodegaMantForm
from sga.models import Aula,Sede,ResponsableBodegaConsultorio
from socioecon.cons_socioecon import ip_client_address
from django.db.models.query_utils import Q


def view(request):
    if request.method=='POST':

        if 'action' in request.POST:
            action = request.POST['action']
            if action=='add':
                b=BodegaMantForm(request.POST)
                if b.is_valid():
                    try:
                        if request.POST['idresp']=='':
                            idresp=0
                        else:
                             idresp=request.POST['idresp']
                        if ResponsableBodegaConsultorio.objects.filter(pk=idresp).exists():
                            edit=ResponsableBodegaConsultorio.objects.get(pk=idresp)
                            edit.bodega=b.cleaned_data['sede']
                            edit.medico=b.cleaned_data['persona']
                            edit.fechaasignacion=datetime.now()
                            edit.usuarioasignacion=request.user
                            mensaje = 'Edicion de Responsable Bodega'
                            edit.save()
                            # Log de EDICION RESPONSABLE BODEGA
                            client_address = ip_client_address(request)
                            LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(edit).pk,
                            object_id       = edit.id,
                            object_repr     = force_str(edit),
                            action_flag     = CHANGE,
                            change_message  = mensaje+' (' + client_address + ')' )
                            return HttpResponseRedirect('/sedemantenimiento')
                        else:
                            bodega=ResponsableBodegaConsultorio(bodega=b.cleaned_data['sede'],
                                    medico=b.cleaned_data['persona'],
                                    fechaasignacion=datetime.now(),
                                    usuarioasignacion=request.user)
                            bodega.save()

                            msj='Registro Adicionado'
                            client_address = ip_client_address(request)
                            LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(bodega).pk,
                            object_id       = bodega.id,
                            object_repr     = force_str(bodega),
                            action_flag     = ADDITION,
                            change_message  = msj + ' (' + client_address + ')')
                            return HttpResponseRedirect("/sedemantenimiento")
                    except Exception as e:
                        return HttpResponseRedirect("/sedemantenimiento?error="+str(e))
                else:
                    return HttpResponseRedirect("/sedemantenimiento?error=ERROR EN EL INGRESO")

    else:
        data = {'title': 'Listado de Responsables de Bodegas'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action == 'cambiaestado':
                estado=''
                bodega = ResponsableBodegaConsultorio.objects.get(pk=request.GET['id'])
                bodega.activa = not bodega.activa
                bodega.usuarioinactivacion=request.user
                bodega.fechainactivacion=datetime.now()
                bodega.save()
                if bodega.activa:
                    estado='Activa'
                else:
                    estado='Inactiva'
                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de INACTIVAR RESPONSABLE DE BODEGA
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(bodega).pk,
                    object_id       = bodega.id,
                    object_repr     = force_str(bodega),
                    action_flag     = DELETION,
                    change_message  = 'Cambia Estado Responsable Bodega ( '+ estado + client_address + ')'  )

                return HttpResponseRedirect("/sedemantenimiento")
        else:
            search  = None
            bodega  = None

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
                        bodega = ResponsableBodegaConsultorio.objects.filter(Q(bodega__nombre__icontains=search)|Q(medico__apellido1__icontains=search)|Q(medico__apellido2__icontains=search)).order_by('bodega')
                    else:
                        bodega = ResponsableBodegaConsultorio.objects.all().order_by('bodega')
                except Exception as e:
                    pass
            else:
                bodega = ResponsableBodegaConsultorio.objects.all().order_by('bodega')

            paging = MiPaginador(bodega, 30)
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
            form = BodegaMantForm()
            form.for_personal()
            data['form']=form
            data['bodega'] = page.object_list
            if 'error' in request.GET:
                data['error']= request.GET['error']
            return render(request ,"sedemantenimiento/sedemantenimiento.html" ,  data)