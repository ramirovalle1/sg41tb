from datetime import datetime
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Avg
from django.db.models.query_utils import Q
from django.forms.models import model_to_dict
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.utils.encoding import force_str
from decorators import secure_module
from sga.commonviews import addUserData
from sga.forms import MultaForm
from sga.models import Multa


@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    if request.method=='POST':
        action = request.POST['action']
        if action=='add':
            f = MultaForm(request.POST)
            if f.is_valid():
                multa = Multa(profesor=f.cleaned_data['profesor'],
                             valor=f.cleaned_data['valor'],
                             tipo=f.cleaned_data['tipo'],
                             motivo=f.cleaned_data['motivo'],
                             fecha=datetime.today(),
                             cancelada=False)
                multa.save()

                # Log de ADICIONAR MULTAS A DOCENTES
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(multa).pk,
                    object_id       = multa.id,
                    object_repr     = force_str(multa),
                    action_flag     = ADDITION,
                    change_message  = 'Adicionada Multa Docente')
            else:
                return HttpResponseRedirect("/pro_multas?action=add")

        elif action=='edit':
            multa = Multa.objects.get(pk=request.POST['id'])
            f = MultaForm(request.POST)
            if f.is_valid():
                multa.profesor = f.cleaned_data['profesor']
                multa.valor = f.cleaned_data['valor']
                multa.tipo = f.cleaned_data['tipo']
                multa.motivo = f.cleaned_data['motivo']
                multa.save()

                # Log de EDITAR MULTA A DOCENTES
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(multa).pk,
                    object_id       = multa.id,
                    object_repr     = force_str(multa),
                    action_flag     = CHANGE,
                    change_message  = 'Editada Multa Docente' )
            else:
                return HttpResponseRedirect("/pro_multas?action=edit&id="+str(multa.id))

        elif action=='del':
            multa = Multa.objects.get(pk=request.POST['id'])

            # Log de ELIMINAR MULTAS DOCENTES
            LogEntry.objects.log_action(
                user_id         = request.user.pk,
                content_type_id = ContentType.objects.get_for_model(multa).pk,
                object_id       = multa.id,
                object_repr     = force_str(multa),
                action_flag     = DELETION,
                change_message  = 'Eliminada Multa Docente' )

            multa.delete()


        return HttpResponseRedirect("/pro_multas")
    else:
        data = {'title': 'Listado de Multas Docentes'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='add':
                data['title'] = 'Adicionar Multa Docente'
                form = MultaForm()
                data['form'] = form
                return render(request ,"pro_multas/adicionar.html" ,  data)
            elif action=='edit':
                data['title'] = 'Editar Multa Docente'
                multa = Multa.objects.get(pk=request.GET['id'])
                initial = model_to_dict(multa)
                data['multa'] = multa
                data['form'] = MultaForm(initial=initial)
                return render(request ,"pro_multas/editar.html" ,  data)
            elif action=='del':
                data['title'] = 'Borrar Multa Docente'
                data['multa'] = Multa.objects.get(pk=request.GET['id'])
                return render(request ,"pro_multas/borrar.html" ,  data)

        else:
            search = None
            if 's' in request.GET:
                search = request.GET['s']
            if search:
                multas = Multa.objects.filter(Q(profesor__persona__nombres__icontains=search) | Q(profesor__persona__apellido1__icontains=search) | Q(profesor__persona__apellido2__icontains=search) | Q(motivo__icontains=search)).order_by('cancelada','fecha')
            else:
                multas = Multa.objects.all().order_by('fecha')
            paging = Paginator(multas, 30)
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
            data['multas'] = page.object_list
            return render(request ,"pro_multas/multas.html" ,  data)
