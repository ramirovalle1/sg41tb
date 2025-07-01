from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.core.paginator import Paginator
from django.db.models.query_utils import Q
from django.forms.models import model_to_dict
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from decorators import secure_module
from settings import DEFAULT_PASSWORD, PROFESORES_GROUP_ID, ALUMNOS_GROUP_ID, UTILIZA_GRUPOS_ALUMNOS, EMAIL_ACTIVE, RECTORADO_GROUP_ID, SISTEMAS_GROUP_ID, COORDINACION_ACADEMICA_GROUP_ID
from sga.commonviews import addUserData
from sga.forms import TipoIncidenciaForm, ResponderIncidenciaForm
from sga.models import Egresado, Incidencia, TipoIncidencia, DepartamentoGroup, Persona


@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    if request.method=='POST':
        action = request.POST['action']
        # Para borrar incidencias en el futuro, por el momento solo se usa el Cerrar
        if action=='del':
            incidencia = Incidencia.objects.get(pk=request.POST['id'])
            incidencia.delete()
        elif action=='reenviar':
            incidencia = Incidencia.objects.get(pk=request.POST['id'])
            f = TipoIncidenciaForm(request.POST)
            if f.is_valid():
                incidencia.tipo = f.cleaned_data['tipo']
                incidencia.save()
                if EMAIL_ACTIVE:
                    incidencia.mail_nuevo()

        elif action=='responder':
            incidencia = Incidencia.objects.get(pk=request.POST['id'])
            f = ResponderIncidenciaForm(request.POST)
            persona = Persona.objects.filter(usuario=request.user)[:1].get()
            if f.is_valid():
                incidencia.solucion = f.cleaned_data['solucion'].upper()
                incidencia.cerrada = True
                incidencia.fechacontest = datetime.now()
                incidencia.personacont = persona
                incidencia.save()
                if EMAIL_ACTIVE:
                    incidencia.mail_respuesta()

        return HttpResponseRedirect("/incidencias")
    else:
        data = {'title': 'Listado de Incidencias en Clases'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='del':
                data['title'] = 'Eliminar Incidencia'
                data['incidencia'] = Incidencia.objects.get(pk=request.GET['id'])
                return render(request ,"incidencias/borrarbs.html" ,  data)
            elif action=='reenviar':
                incidencia = Incidencia.objects.get(pk=request.GET['id'])
                data['incidencia'] = incidencia
                data['title'] = 'Reenviar Incidencia'
                data['form'] = TipoIncidenciaForm()
                return render(request ,"incidencias/reenviar.html" ,  data)
            elif action=='responder':
                incidencia = Incidencia.objects.get(pk=request.GET['id'])
                data['incidencia'] = incidencia
                data['title'] = 'Responder Incidencia'
                data['form'] = ResponderIncidenciaForm()
                return render(request ,"incidencias/responder.html" ,  data)

            elif action=='cerrar':
                incidencia = Incidencia.objects.get(pk=request.GET['id'])
                incidencia.cerrada = True
                incidencia.mail_respuesta()
                incidencia.save()
                return HttpResponseRedirect("/incidencias")

        else:
            search = None
            per = data['persona']
            if 'i' in request.GET:
                search = request.GET['i']
                incidencias = Incidencia.objects.filter(pk=search)
            elif 's' in request.GET:
                search = request.GET['s']
                incidencias = Incidencia.objects.filter(Q(tipo__responsable=per, lecciongrupo__profesor__persona__nombres__icontains=search) | Q(lecciongrupo__profesor__persona__apellido1__icontains=search) | Q(lecciongrupo__profesor__persona__apellido2__icontains=search) | Q(tipo__nombre__icontains=search), cerrada=False,tipo__id__in=DepartamentoGroup.objects.filter(claseincide=True, group__id__in=per.usuario.groups.filter().values("id")).values("tipoincidencia")).order_by('-lecciongrupo__fecha')
            else:
                if per.en_grupo(RECTORADO_GROUP_ID) or per.en_grupo(SISTEMAS_GROUP_ID) or per.en_grupo(COORDINACION_ACADEMICA_GROUP_ID):
                    # incidencias = Incidencia.objects.order_by('-lecciongrupo__fecha')
                    incidencias = Incidencia.objects.filter(tipo__id__in=DepartamentoGroup.objects.filter(claseincide=True, group__id__in=per.usuario.groups.filter().values("id")).values("tipoincidencia")).order_by('-lecciongrupo__fecha')
                else:
                    # incidencias = Incidencia.objects.filter(tipo__responsable=per).order_by('-lecciongrupo__fecha')
                    incidencias = Incidencia.objects.filter(tipo__id__in=DepartamentoGroup.objects.filter(claseincide=True, group__id__in=per.usuario.groups.filter().values("id")).values("tipoincidencia")).order_by('-lecciongrupo__fecha')

            paging = Paginator(incidencias, 100)
            p=1
            try:
                if 'page' in request.GET:
                    p = int(request.GET['page'])
                page = paging.page(p)
            except:
                page = paging.page(1)
            data['paging'] = paging
            data['page'] = page
            data['search'] = search if search else ""
            data['incidencias'] = page.object_list
            data['utiliza_grupos'] = UTILIZA_GRUPOS_ALUMNOS
            return render(request ,"incidencias/incidenciasbs.html" ,  data)
