from datetime import datetime
from django.template import RequestContext
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models.query_utils import Q
from django.forms.models import model_to_dict
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.encoding import force_str
from decorators import secure_module
from settings import TIPOSEGMENTO_PRACT,EMAIL_ACTIVE
from sga.tasks import gen_passwd, send_html_mail
from sga.commonviews import addUserData, ip_client_address
from sga.forms import MateriaRecepcionActaNotasForm
from sga.inscripciones import MiPaginador
from sga.models import MateriaRecepcionActaNotas, Materia, Persona, Periodo,ProfesorMateria, TipoIncidencia, Coordinacion

@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    if request.method=='POST':
        action = request.POST['action']
        if action == 'refreshmaterias':
            #Buscar aquellas materias que esten cerradas o que hayan terminado y aun no esten en lista
            # for m in Materia.objects.filter(cerrado=True):
            for m in Materia.objects.filter(cerrado=True,materiarecepcionactanotas__materia=None):
            # for m in Materia.objects.filter(Q(cerrado=True)|Q(fin__lt=datetime.now())):
                if not m.materiarecepcionactanotas_set.exists():
                    mrecep = MateriaRecepcionActaNotas(materia=m)
                    mrecep.save()

        elif action == 'edit':
            r = MateriaRecepcionActaNotas.objects.get(pk=request.POST['id'])
            f = MateriaRecepcionActaNotasForm(request.POST)
            if f.is_valid():
                r.entregada = f.cleaned_data['entregada']
                r.fecha = datetime.now() if f.cleaned_data['entregada'] else None
                r.hora = datetime.now().time() if f.cleaned_data['entregada'] else None
                r.codigo = f.cleaned_data['codigo']
                r.entrega = f.cleaned_data['entrega']
                r.observaciones = f.cleaned_data['observaciones']
                # r.usuario = request.user
                r.alcanceentregada = f.cleaned_data['alcanceentregada']
                r.observacionesalcance = f.cleaned_data['observacionesalcance']
                r.actanivelentregada = f.cleaned_data['actanivelentregada']
                r.actanivelobservaciones = f.cleaned_data['actanivelobservaciones']
                r.usuario = request.user
                r.save()

                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de EDITAR RECEPCION ACTA DE NOTAS
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(r).pk,
                    object_id       = r.id,
                    object_repr     = force_str(r),
                    action_flag     = CHANGE,
                    change_message  = 'Recepcion Acta Notas (' + client_address + ')')
                correo =None
                if EMAIL_ACTIVE:
                    hoy = datetime.now().today()
                    docente=ProfesorMateria.objects.filter(materia=r.materia).order_by('-hasta')[:1].get()
                    profesor=docente.profesor.persona.nombre_completo_inverso()
                    personarespon = Persona.objects.filter(usuario=request.user)[:1].get()
                    tipo=''
                    correocoordinacion=''
                    correo=''
                    #OCastillo 27-02-2020 para que se envie correo por coordinacion
                    carrera=r.materia.nivel.carrera
                    if Coordinacion.objects.filter(carrera=carrera).exists():
                        correocoordinacion=Coordinacion.objects.filter(carrera=carrera)[:1].get()
                        if TipoIncidencia.objects.filter(pk=57).exists():
                            tipo = TipoIncidencia.objects.get(pk=57)
                        correo=str(docente.profesor.persona.emailinst)+','+tipo.correo+','+correocoordinacion.correo

                    if correo:
                        send_html_mail("ENTREGA ACTA DE NOTAS",
                            "emails/correo_entregaactanotas.html", {'contenido': "ENTREGA ACTA DE NOTAS", 'self': r, 'docente': profesor,'personarespon': personarespon.nombre_completo(), 'fecha': hoy},correo.split(','))
                return HttpResponseRedirect("/recepcion_actas?id=" + str(r.id))

            else:
                return HttpResponseRedirect("/recepcion_actas?action=edit&id=" + str(r.id))

        return HttpResponseRedirect("/recepcion_actas")

    else:
        data = {'title': 'Recepciones de Actas de Notas'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action == 'edit':
                r = MateriaRecepcionActaNotas.objects.get(pk=request.GET['id'])
                initial = model_to_dict(r)
                data['form'] = MateriaRecepcionActaNotasForm(initial=initial)
                data['r'] = r
                return render(request ,"recepcion_actas/editar.html" ,  data)

        else:
            search = None
            op = None
            en = None
            id = None
            searchparalelo = None
            periodoid = None

            if 'p' in request.GET:
                periodoid = request.GET['p']
            if 's' in request.GET:
                search = request.GET['s']

            if 'id' in request.GET:
                id = request.GET['id']

            if 'op' in request.GET:
                op = request.GET['op']

            if 'par' in request.GET:
                searchparalelo = request.GET['par']

            if 'en' in request.GET:
                en = request.GET['en']
            #OCastillo 02-08-2022 se quita filtro de materias practicas por otras coordinaciones que no son FASS
            if periodoid and search:
                ss = search.split(' ')
                while '' in ss:
                    ss.remove('')
                if len(ss)==1:
                    recepcion_actas =[x for x in MateriaRecepcionActaNotas.objects.filter(Q(materia__asignatura__nombre__icontains=search) | Q(materia__profesormateria__profesor__persona__apellido1__icontains=search)| Q(materia__profesormateria__profesor__persona__apellido2__icontains=search)| Q(materia__profesormateria__profesor__persona__nombres__icontains=search)| Q(materia__profesormateria__profesor__persona__cedula__icontains=search), materia__nivel__periodo__id=periodoid).order_by('-materia__fechacierre','materia__nivel__periodo')  if
                                     x.materia.profesormateria_set.all().exists()]
                    # recepcion_actas = MateriaRecepcionActaNotas.objects.filter(Q(materia__asignatura__nombre__icontains=search) | Q(materia__profesormateria__profesor__persona__apellido1__icontains=search)| Q(materia__profesormateria__profesor__persona__apellido2__icontains=search)| Q(materia__profesormateria__profesor__persona__nombres__icontains=search)| Q(materia__profesormateria__profesor__persona__cedula__icontains=search), materia__nivel__periodo__id=periodoid).exclude(materia__profesormateria__segmento__id=TIPOSEGMENTO_PRACT).order_by('materia__nivel__periodo')
                else:
                    recepcion_actas =[x for x in MateriaRecepcionActaNotas.objects.filter(Q(materia__profesormateria__profesor__persona__apellido1__icontains=ss[0]) & Q(materia__profesormateria__profesor__persona__apellido2__icontains=ss[1]), materia__nivel__periodo__id=periodoid).order_by('-materia__fechacierre','materia__nivel__periodo')  if
                                     x.materia.profesormateria_set.all().exists()]
                    # recepcion_actas = MateriaRecepcionActaNotas.objects.filter(Q(materia__profesormateria__profesor__persona__apellido1__icontains=ss[0]) & Q(materia__profesormateria__profesor__persona__apellido2__icontains=ss[1]), materia__nivel__periodo__id=periodoid).exclude(materia__profesormateria__segmento__id=TIPOSEGMENTO_PRACT).order_by('materia__nivel__periodo')

            elif search:
                ss = search.split(' ')
                while '' in ss:
                    ss.remove('')
                if len(ss)==1:
                    recepcion_actas =[x for x in MateriaRecepcionActaNotas.objects.filter(Q(materia__asignatura__nombre__icontains=search) | Q(materia__profesormateria__profesor__persona__apellido1__icontains=search)| Q(materia__profesormateria__profesor__persona__apellido2__icontains=search)| Q(materia__profesormateria__profesor__persona__nombres__icontains=search)| Q(materia__profesormateria__profesor__persona__cedula__icontains=search)).order_by('-materia__fechacierre','materia__nivel__periodo')  if
                                     x.materia.profesormateria_set.all().exists()]
                    # recepcion_actas = MateriaRecepcionActaNotas.objects.filter(Q(materia__asignatura__nombre__icontains=search) | Q(materia__profesormateria__profesor__persona__apellido1__icontains=search)| Q(materia__profesormateria__profesor__persona__apellido2__icontains=search)| Q(materia__profesormateria__profesor__persona__nombres__icontains=search)| Q(materia__profesormateria__profesor__persona__cedula__icontains=search)).exclude(materia__profesormateria__segmento__id=TIPOSEGMENTO_PRACT).order_by('materia__nivel__periodo')
                else:
                    # recepcion__actas = MateriaRecepcionActaNotas.objects.filter(Q(materia__profesormateria__profesor__persona__apellido1__icontains=ss[0]) & Q(materia__profesormateria__profesor__persona__apellido2__icontains=ss[1])).exclude(materia__profesormateria__segmento__id=TIPOSEGMENTO_PRACT).order_by('materia__nivel__periodo')
                    recepcion_actas = [x for x in  MateriaRecepcionActaNotas.objects.filter(Q(materia__profesormateria__profesor__persona__apellido1__icontains=ss[0]) & Q(materia__profesormateria__profesor__persona__apellido2__icontains=ss[1])).order_by('-materia__fechacierre','materia__nivel__periodo')  if
                                        x.materia.profesormateria_set.all().exists()]

            elif searchparalelo:
                # recepcion_actas = MateriaRecepcionActaNotas.objects.filter(materia__nivel__paralelo=searchparalelo).exclude(materia__profesormateria__segmento__id=TIPOSEGMENTO_PRACT).order_by('materia__nivel__periodo')
                recepcion_actas = [x for x in MateriaRecepcionActaNotas.objects.filter(materia__nivel__paralelo=searchparalelo).order_by('-materia__fechacierre','materia__nivel__periodo') if
                                    x.materia.profesormateria_set.all().exists()]

            elif periodoid:
                recepcion_actas = [x for x in  MateriaRecepcionActaNotas.objects.filter(materia__nivel__periodo__id=periodoid).order_by('-materia__fechacierre','materia__nivel__periodo') if
                                    x.materia.profesormateria_set.all().exists()]
                # recepcion_actas = MateriaRecepcionActaNotas.objects.filter(materia__nivel__periodo__id=periodoid).exclude(materia__profesormateria__segmento__id=TIPOSEGMENTO_PRACT).order_by('fecha')

            elif op:
                if op == 'true':
                    recepcion_actas = [x for x in MateriaRecepcionActaNotas.objects.filter(materia__cerrado=True).order_by('-materia__fechacierre','materia__nivel__periodo') if
                                    x.materia.profesormateria_set.all().exists()]
                    # recepcion_actas = MateriaRecepcionActaNotas.objects.filter(materia__cerrado=True).exclude(materia__profesormateria__segmento__id=TIPOSEGMENTO_PRACT).order_by('fecha','materia__nivel__periodo')
                else:
                    recepcion_actas =[x for x in MateriaRecepcionActaNotas.objects.filter(materia__cerrado=False).order_by('fecha','materia__nivel__periodo') if
                                    x.materia.profesormateria_set.all().exists()]
                    # recepcion_actas = MateriaRecepcionActaNotas.objects.filter(materia__cerrado=False).exclude(materia__profesormateria__segmento__id=TIPOSEGMENTO_PRACT).order_by('fecha','materia__nivel__periodo')
            elif id:
                    recepcion_actas = MateriaRecepcionActaNotas.objects.filter(pk=id).order_by('fecha','materia__nivel__periodo')
            elif en:
                if en == 'si':
                    recepcion_actas = [x for x in MateriaRecepcionActaNotas.objects.filter(entregada=True).order_by('-materia__fechacierre','materia__nivel__periodo') if
                                    x.materia.profesormateria_set.all().exists()]
                    # recepcion_actas = MateriaRecepcionActaNotas.objects.filter(materia__cerrado=True).exclude(materia__profesormateria__segmento__id=TIPOSEGMENTO_PRACT).order_by('fecha','materia__nivel__periodo')
                else:
                    recepcion_actas =[x for x in MateriaRecepcionActaNotas.objects.filter(entregada=False).order_by('fecha','materia__nivel__periodo') if
                                    x.materia.profesormateria_set.all().exists()]
            else:

                recepcion_actas =[x for x in MateriaRecepcionActaNotas.objects.filter().order_by('-materia__fechacierre','materia__nivel__periodo')[:100] if
                                    x.materia.profesormateria_set.all().exists()]
                # recepcion_actas = MateriaRecepcionActaNotas.objects.all().exclude(materia__profesormateria__segmento__id=TIPOSEGMENTO_PRACT).order_by('fecha','materia__nivel__periodo')

            paging = MiPaginador(recepcion_actas, 30)
            p = 1
            try:
                if 'page' in request.GET:
                    p = int(request.GET['page'])
                page = paging.page(p)
            except:
                page = paging.page(p)

            data['paging'] = paging
            data['rangospaging'] = paging.rangos_paginado(p)
            data['page'] = page
            data['search'] = search if search else ""
            data['op'] = op  if op else ""
            data['searchparalelo'] = searchparalelo if searchparalelo else ""
            data['periodoid'] = int(periodoid) if periodoid else ""
            data['periodo'] = Periodo.objects.get(pk=request.GET['p']) if periodoid else ""
            data['recepcionesactas'] = page.object_list
            data['periodos'] = Periodo.objects.all().order_by('-tipo', '-inicio')
            return render(request ,"recepcion_actas/materias.html" ,  data)
