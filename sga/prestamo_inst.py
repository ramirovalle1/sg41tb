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
from settings import DEFAULT_PASSWORD, PROFESORES_GROUP_ID, ALUMNOS_GROUP_ID, UTILIZA_GRUPOS_ALUMNOS
from sga.commonviews import addUserData
from sga.forms import PersonaForm, InscripcionForm, RecordAcademicoForm, HistoricoRecordAcademicoForm, GraduadoForm, SeguimientoGraduadoForm, GraduadoDatosForm, PrestamoInstitucionalForm
from sga.models import Profesor, Persona, Inscripcion, RecordAcademico, DocumentosDeInscripcion, HistoricoRecordAcademico, Graduado, SeguimientoGraduado, Asignatura, PrestamoInstitucional


@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    if request.method=='POST':
        action = request.POST['action']
        if action=='add':
            f = PrestamoInstitucionalForm(request.POST)
            if f.is_valid():
                prestamoinst = PrestamoInstitucional(persona=f.cleaned_data['persona'],
                                                     valor=f.cleaned_data['valor'],
                                                     cuota=f.cleaned_data['cuota'],
                                                     motivo=f.cleaned_data['motivo'],
                                                     fecha=datetime.today(),
                                                     cancelado=False)
                prestamoinst.save()

                # Log de ADICIONAR PRESTAMO INSTITUCIONAL
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(prestamoinst).pk,
                    object_id       = prestamoinst.id,
                    object_repr     = force_str(prestamoinst),
                    action_flag     = ADDITION,
                    change_message  = 'Adicionado Prestamo Institucional' )
            else:
                return HttpResponseRedirect("/prestamo_inst?action=add")

        elif action=='edit':
            prestamoinst = PrestamoInstitucional.objects.get(pk=request.POST['id'])
            f = PrestamoInstitucionalForm(request.POST)
            if f.is_valid():
                prestamoinst.persona = f.cleaned_data['persona']
                prestamoinst.valor = f.cleaned_data['valor']
                prestamoinst.cuota = f.cleaned_data['cuota']
                prestamoinst.motivo = f.cleaned_data['motivo']
                prestamoinst.fecha = datetime.today()
                prestamoinst.recalcula()
                prestamoinst.save()

                # Log de EDITAR PRESTAMO INSTITUCIONAL
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(prestamoinst).pk,
                    object_id       = prestamoinst.id,
                    object_repr     = force_str(prestamoinst),
                    action_flag     = CHANGE,
                    change_message  = 'Editado Prestamo Institucional' )
            else:
                return HttpResponseRedirect("/prestamo_inst?action=edit&id="+str(prestamoinst.id))

        elif action=='del':
            prestamoinst = PrestamoInstitucional.objects.get(pk=request.POST['id'])

            # Log de ELIMINAR PRESTAMO INSTITUCIONAL
            LogEntry.objects.log_action(
                user_id         = request.user.pk,
                content_type_id = ContentType.objects.get_for_model(prestamoinst).pk,
                object_id       = prestamoinst.id,
                object_repr     = force_str(prestamoinst),
                action_flag     = DELETION,
                change_message  = 'Eliminado Prestamo Institucional' )

            prestamoinst.delete()


        return HttpResponseRedirect("/prestamo_inst")
    else:
        data = {'title': 'Listado de Prestamos Institucionales'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='add':
                data['title'] = 'Adicionar Prestamo Institucional'
                form = PrestamoInstitucionalForm()
                form.for_profesor()
                data['form'] = form
                return render(request ,"prestamo_inst/adicionar.html" ,  data)
            elif action=='edit':
                data['title'] = 'Editar Prestamo Institucional'
                prestamoinst = PrestamoInstitucional.objects.get(pk=request.GET['id'])
                initial = model_to_dict(prestamoinst)
                data['prestamoinst'] = prestamoinst
                data['form'] = PrestamoInstitucionalForm(initial=initial)
                return render(request ,"prestamo_inst/editar.html" ,  data)
            elif action=='del':
                data['title'] = 'Borrar Prestamo Institucional'
                data['prestamoinst'] = PrestamoInstitucional.objects.get(pk=request.GET['id'])
                return render(request ,"prestamo_inst/borrar.html" ,  data)

        else:
            search = None
            if 's' in request.GET:
                search = request.GET['s']
            if search:
                prestamoinst = PrestamoInstitucional.objects.filter(Q(persona__nombres__icontains=search) | Q(persona__apellido1__icontains=search) | Q(persona__apellido2__icontains=search) | Q(motivo__icontains=search)).order_by('fecha')
            else:
                prestamoinst = PrestamoInstitucional.objects.all().order_by('fecha')
            paging = Paginator(prestamoinst, 50)
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
            data['prestamoinst'] = page.object_list
            return render(request ,"prestamo_inst/prestamoinst.html" ,  data)
