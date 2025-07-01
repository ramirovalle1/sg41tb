from datetime import datetime
from django.contrib.admin.models import LogEntry, CHANGE, DELETION
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models.query_utils import Q
from django.forms.models import model_to_dict
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.utils.encoding import force_str
from decorators import secure_module
from settings import DEFAULT_PASSWORD, PROFESORES_GROUP_ID, ALUMNOS_GROUP_ID
from sga.commonviews import addUserData
from sga.forms import PersonaForm, InscripcionForm, RecordAcademicoForm, HistoricoRecordAcademicoForm, GraduadoForm, EgresadoForm, BecarioForm
from sga.models import Profesor, Persona, Inscripcion, RecordAcademico, DocumentosDeInscripcion, HistoricoRecordAcademico, Graduado, Egresado, InscripcionBecario, TipoBeca


@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    if request.method=='POST':
        action = request.POST['action']
        if action=='edit':
            becario = InscripcionBecario.objects.get(pk=request.POST['id'])
            f = BecarioForm(request.POST)
            if f.is_valid():
                becario.porciento = f.cleaned_data['porciento']
                becario.tipobeca = f.cleaned_data['tipobeca']
                becario.motivo = f.cleaned_data['motivo']
                becario.save()

                # Log de EDITAR BECARIO
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(becario).pk,
                    object_id       = becario.id,
                    object_repr     = force_str(becario),
                    action_flag     = CHANGE,
                    change_message  = 'Editado Becario' )

            else:
                return HttpResponseRedirect("/becarios?action=edit&id="+str(request.POST['id']))

        elif action=='del':
            becario = InscripcionBecario.objects.get(pk=request.POST['id'])
            becario.delete()

            # Log de BORRAR BECARIO
            LogEntry.objects.log_action(
                user_id         = request.user.pk,
                content_type_id = ContentType.objects.get_for_model(becario).pk,
                object_id       = becario.id,
                object_repr     = force_str(becario),
                action_flag     = DELETION,
                change_message  = 'Eliminado Becario' )

        return HttpResponseRedirect("/becarios")
    else:
        data = {'title': 'Listado de Estudiantes Becados'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='edit':
                data['title'] = 'Editar Becario'
                becario = InscripcionBecario.objects.get(pk=request.GET['id'])
                initial = model_to_dict(becario)
                form = BecarioForm(initial=initial)
                data['becario'] = becario
                data['form'] = form
                return render(request ,"becarios/editarbs.html" ,  data)
            elif action=='del':
                data['title'] = 'Borrar Becario'
                data['becario'] = InscripcionBecario.objects.get(pk=request.GET['id'])
                return render(request ,"becarios/borrarbs.html" ,  data)

        else:
            search = None
            tipo = None

            if 't' in request.GET:
                tipo = request.GET['t']
                data['tipoid'] = int(tipo) if tipo else ""

            if 's' in request.GET:
                search = request.GET['s']
            if search:
                becarios = InscripcionBecario.objects.filter(Q(inscripcion__persona__nombres__icontains=search) | Q(inscripcion__persona__apellido1__icontains=search) | Q(inscripcion__persona__apellido2__icontains=search) | Q(inscripcion__persona__cedula__icontains=search) | Q(inscripcion__persona__pasaporte__icontains=search)).order_by('inscripcion__persona__apellido1')
            elif tipo:
                becarios = InscripcionBecario.objects.filter(tipobeca__id=tipo).order_by('inscripcion__persona')
            else:
                becarios = InscripcionBecario.objects.all().order_by('inscripcion__persona')
            paging = Paginator(becarios, 50)
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
            data['becarios'] = page.object_list
            data['tipobecas'] = TipoBeca.objects.all().order_by('nombre')
            return render(request ,"becarios/becarios.html" ,  data)
