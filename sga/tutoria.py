from datetime import datetime
from decimal import Decimal
import json
from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.forms import model_to_dict
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
from decorators import secure_module
from settings import NO_TUTORIA, NIVEL_MALLA_CERO, EMAIL_ACTIVE, ASIGNACION_TUTOR, DEFAULT_PASSWORD
from sga.alu_malla import aprobadaAsignatura
from sga.commonviews import addUserData, ip_client_address
from sga.forms import TutoriaForm, ArchivoTesisForm, RevisionTutoriaForm, ActaSustentacionForm, ComiteSustentacionForm
from sga.models import Tutoria, Profesor, Inscripcion, AsignaturaMalla, ObservacionTutoria, EstudianteTutoria, Persona, SolicitudEstudiante, RevisionTutoria


class MiPaginador(Paginator):
    def __init__(self, object_list, per_page, orphans=0, allow_empty_first_page=True, rango=5):
        super(MiPaginador,self).__init__(object_list, per_page, orphans=orphans, allow_empty_first_page=allow_empty_first_page)
        self.rango = rango
        self.paginas = []
        self.primera_pagina = False
        self.ultima_pagina = False

    def rangos_paginado(self, pagina):
        left = pagina - self.rango
        right = pagina + self.rango
        if left<1:
            left=1
        if right>self.num_pages:
            right = self.num_pages
        self.paginas = range(left, right+1)
        self.primera_pagina = True if left>1 else False
        self.ultima_pagina = True if right<self.num_pages else False
        self.ellipsis_izquierda = left-1
        self.ellipsis_derecha = right+1

@login_required(redirect_field_name='ret', login_url='/login')
# @secure_module
# @transaction.atomic()
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action == 'add':
                f= TutoriaForm(request.POST)
                if f.is_valid():
                    edit = 0
                    if Decimal(f.cleaned_data['valor']) != 0.00:
                        if 'tutor' in request.POST:
                            tutoria = Tutoria.objects.get(id = request.POST['tutor'])
                            tutoria.profesor.id = request.POST['id']
                            tutoria.estudiante.id = f.cleaned_data['estudiante']
                            tutoria.numtutoria = int(f.cleaned_data['numtutoria'])
                            tutoria.valor = Decimal(f.cleaned_data['valor'])
                            tutoria.estado = f.cleaned_data['estado']
                            tutoria.fecha = datetime.now().date()
                            tutoria.persona = Persona.objects.filter(usuario=request.user)[:1].get()
                            edit = 1
                        else:
                            tutoria = Tutoria(
                                                profesor_id = request.POST['id'],
                                                estudiante_id = f.cleaned_data['estudiante'] ,
                                                numtutoria = int(f.cleaned_data['numtutoria']),
                                                valor = Decimal(f.cleaned_data['valor']),
                                                estado = f.cleaned_data['estado'],
                                                persona = Persona.objects.filter(usuario=request.user)[:1].get(),
                                                fecha = datetime.now().date())
                        tutoria.save()

                        if edit == 0:
                            if EMAIL_ACTIVE:
                                tutoria.email_enviatuto(request.user)
                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(tutoria).pk,
                        object_id       = tutoria.id,
                        object_repr     = force_str(tutoria),
                        action_flag     = ADDITION,
                        change_message  = 'Ingreso o edicion de Registro de Tutoria (' + client_address + ')' )
                        if not  SolicitudEstudiante.objects.filter(inscripcion=tutoria.estudiante,tipo__id=ASIGNACION_TUTOR).exists():
                            return HttpResponseRedirect('/tutoria?id='+str(tutoria.profesor.id)+"&soli=no")
                        else:
                            return HttpResponseRedirect('/tutoria?id='+str(tutoria.profesor.id))
                    return HttpResponseRedirect('/tutoria?action=add&error=1&id='+str(f.cleaned_data['profesor'].id))
                return HttpResponseRedirect('/tutoria?action=add')
            if action == 'edittuto':
                try:
                    f= TutoriaForm(request.POST)
                    if f.is_valid():
                        tutoria = Tutoria.objects.get(id = request.POST['tutor'])
                        numeanterior = tutoria.numtutoria
                        if tutoria.numtutoria == int(f.cleaned_data['numtutoria']):
                            return HttpResponseRedirect('/tutoria?id='+str(tutoria.profesor.id)+'&info=No se modifico el registro')
                        tutoria.numtutoria = int(f.cleaned_data['numtutoria'])
                        tutoria.fecha = datetime.now().date()
                        tutoria.persona = Persona.objects.filter(usuario=request.user)[:1].get()
                        tutoria.save()
                        observaciontutoria = ObservacionTutoria(tutoria=tutoria,
                                                                observacion=request.POST['observacion']+' - editado de '+ str(numeanterior) + ' a ' + str(f.cleaned_data['numtutoria']),
                                                                usuario=request.user,
                                                                fecha=datetime.now())
                        observaciontutoria.save()
                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(tutoria).pk,
                        object_id       = tutoria.id,
                        object_repr     = force_str(tutoria),
                        action_flag     = ADDITION,
                        change_message  = 'Edicion de Registro de Tutoria (' + client_address + ')' )
                        return HttpResponseRedirect('/tutoria?id='+str(tutoria.profesor.id))
                except Exception as ex:
                   return HttpResponseRedirect('/?info=Error vuelva a intentarlo')
            elif action == 'activacion':
                try:
                    t = Tutoria.objects.get(pk=request.POST['id'])
                    # if t.estado:
                    #     if Tutoria.objects.filter(estudiante=t.estudiante,estado=True):
                    #         return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
                    t.estado = not t.estado
                    t.save()

                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(t).pk,
                        object_id       = t.id,
                        object_repr     = force_str(t),
                        action_flag     = ADDITION,
                        change_message  = 'Activacion o desactivacion tutoria (' + client_address + ')' )
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

            elif action == 'existe':
                try:
                    if Tutoria.objects.filter(estudiante__id=request.POST['id'],estado=True).exists():
                        return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                    else:
                        if Inscripcion.objects.filter(id=request.POST['id']).exists():
                            inscripcion = Inscripcion.objects.get(pk=request.POST['id'])
                            if (inscripcion.grupo().nombre[0:1] == 'E' or inscripcion.grupo().nombre[0:1] == 'P' or inscripcion.grupo().nombre[0:1]== 'G') and DEFAULT_PASSWORD == 'itb':
                                if not SolicitudEstudiante.objects.filter(pk=ASIGNACION_TUTOR).exists():
                                    return HttpResponse(json.dumps({"result":"badsoli"}),content_type="application/json")
                            if inscripcion.adeuda_a_la_fecha():
                                return HttpResponse(json.dumps({"result":"okadeuda"}),content_type="application/json")
                            inscripcionmalla = inscripcion.malla_inscripcion()
                            num=0
                            for x in AsignaturaMalla.objects.filter(malla=inscripcionmalla.malla).exclude(nivelmalla__id=NIVEL_MALLA_CERO).exclude(asignatura__nivelacion=True).exclude(asignatura__nombre__icontains='TRABAJO DE TITULACI').exclude(asignatura__nombre__icontains='CTICAS PREPROFE'):
                                try:
                                    if aprobadaAsignatura(x, inscripcion).aprobada:
                                        # print(x.asignatura)
                                        num = num + 1
                                except:
                                    pass
                            # print(num)
                            if Inscripcion.objects.get(id=request.POST['id']).matricula():
                                if Inscripcion.objects.get(id=request.POST['id']).matricula().esta_retirado():
                                    return HttpResponse(json.dumps({"result":"okret"}),content_type="application/json")
                                else:
                                     #OCastillo 07-09-2021 se excluyen asignaturas practica y titulacion para carrera Tricologia
                                     if inscripcion.carrera.id!=33:
                                         if( num >= AsignaturaMalla.objects.filter(malla=inscripcionmalla.malla).exclude(nivelmalla__id=NIVEL_MALLA_CERO).exclude(asignatura__nivelacion=True).count() -1) :
                                            return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
                                         else:
                                            return HttpResponse(json.dumps({"result":"matr"}),content_type="application/json")
                                     else:
                                         if( num >= AsignaturaMalla.objects.filter(malla=inscripcionmalla.malla).exclude(nivelmalla__id=NIVEL_MALLA_CERO).exclude(asignatura__nivelacion=True).exclude(asignatura__id__in=[650,651]).count() -1) :
                                            return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
                                         else:
                                            return HttpResponse(json.dumps({"result":"matr"}),content_type="application/json")
                            else:
                                #OCastillo 07-09-2021 se excluyen asignaturas practica y titulacion para carrera Tricologia
                                if inscripcion.carrera.id!=33:
                                    if ( num >= AsignaturaMalla.objects.filter(malla=inscripcionmalla.malla).exclude(nivelmalla__id=NIVEL_MALLA_CERO).exclude(asignatura__nivelacion=True).exclude(asignatura__nivelacion=True).exclude(asignatura__nombre__icontains='TRABAJO DE TITULACI').exclude(asignatura__nombre__icontains='CTICAS PREPROFE').count() - 1 ):
                                        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
                                    else:
                                        return HttpResponse(json.dumps({"result":"matr"}),content_type="application/json")
                                else:
                                     if( num >= AsignaturaMalla.objects.filter(malla=inscripcionmalla.malla).exclude(nivelmalla__id=NIVEL_MALLA_CERO).exclude(asignatura__nivelacion=True).exclude(asignatura__id__in=[650,651]).count() -1) :
                                        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
                                     else:
                                        return HttpResponse(json.dumps({"result":"matr"}),content_type="application/json")
                        else:
                            return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
                except:
                    return HttpResponse(json.dumps({"result":"err"}),content_type="application/json")


            return HttpResponseRedirect('/tutoria')


        else:
            data = {'title': 'Registro de Tutoria'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']
                if action == 'add':
                    data['title'] = 'Ingreso de Tutoria'
                    if 'error' in request.GET:
                        data['error']= 'Ingrese valor mayor a cero'
                    hoy = datetime.now().date()
                    form = TutoriaForm(initial={"fecha":hoy, "numtutoria":NO_TUTORIA})
                    form.tutoria(request.GET['id'])
                    data['profesor']= Profesor.objects.get(activo=True,id=request.GET['id'])
                    data['form'] = form
                    return render(request ,"tutoria/addtutoria.html" ,  data)
                elif action =='revision':
                    if Profesor.objects.filter(persona__usuario=request.user).exists():
                        idprofe = Profesor.objects.get(persona__usuario=request.user).id
                        data['idprofe']=idprofe

                    if Inscripcion.objects.filter(persona__usuario=request.user).exists():
                        data['estu']=1
                    tutoria = Tutoria.objects.get(pk=request.GET['tut'])
                    revision = RevisionTutoria.objects.filter(tutoria=tutoria).order_by('-id')
                    paging = MiPaginador(revision, 30)
                    p = 1
                    try:
                        if 'page' in request.GET:
                            p = int(request.GET['page'])
                        page = paging.page(p)
                    except:
                        page = paging.page(p)

                    data['paging'] = paging
                    data['tutoria'] = tutoria
                    data['rangospaging'] = paging.rangos_paginado(p)
                    data['page'] = page
                    data['revision'] = page.object_list
                    data['form'] = RevisionTutoriaForm()
                    if 'error' in request.GET:
                        data['error'] = request.GET['error']
                    return render(request ,"tutoria/revision.html" ,  data)
                elif action == 'detalletutor':
                    data = {}
                    data['observaciontutorias'] = ObservacionTutoria.objects.filter(tutoria__id=request.GET['id'])
                    return render(request ,"tutoria/modificatutoria.html" ,  data)
                elif action == 'edit':
                    data['title'] = 'Editar Tutoria'
                    tutoria = Tutoria.objects.get(id = request.GET['id'])
                    data['profesor'] = Profesor.objects.get(activo=True,id=tutoria.profesor.id)
                    data['num'] = request.GET['num']
                    data['tutor'] = tutoria
                    data['edit'] = 1
                    initial = model_to_dict(tutoria)
                    data['form'] = TutoriaForm(initial=initial)
                    return render(request ,"tutoria/addtutoria.html" ,  data)
                elif action == 'edittuto':
                    data['title'] = 'Editar Tutoria'
                    tutoria = Tutoria.objects.get(id = request.GET['id'])
                    data['profesor'] = Profesor.objects.get(activo=True,id=tutoria.profesor.id)
                    data['num'] = request.GET['num']
                    data['tutor'] = tutoria
                    data['edit'] = 1
                    initial = model_to_dict(tutoria)
                    data['form'] = TutoriaForm(initial=initial)
                    return render(request ,"tutoria/edittuto.html" ,  data)
                elif action == 'delete':
                    tutoria = Tutoria.objects.get(id = request.GET['id'])
                    tutoria.delete()
                    return HttpResponseRedirect('/tutoria?id='+str(request.GET['idprof']))
                pass
            else:
                if Profesor.objects.filter(persona__usuario=request.user).exists():
                    idprofe = Profesor.objects.get(persona__usuario=request.user).id
                    data['profe'] = 1
                elif 'id' in request.GET:
                    idprofe = request.GET['id']
                    data['id'] = request.GET['id']
                if 'info' in request.GET:
                    data['info'] = request.GET['info']
                search = None
                todos = None

                if 's' in request.GET:
                    search = request.GET['s']
                if 't' in request.GET:
                    todos = request.GET['t']
                if 'i' in request.GET:
                    data["i"] = request.GET['i']
                if search:
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')
                    if len(ss) == 1:
                        tutoria = Tutoria.objects.filter(Q(profesor__persona__nombres__icontains=search)|Q(profesor__persona__apellido1__icontains=search)|Q(profesor__persona__apellido2__icontains=search)
                                                         |Q(profesor__persona__cedula__icontains=search)|Q(profesor__persona__pasaporte__icontains=search)|Q(estudiante__persona__nombres__icontains=search)
                                                         |Q(estudiante__persona__apellido1__icontains=search)|Q(estudiante__persona__apellido2__icontains=search)|Q(estudiante__persona__cedula__icontains=search)
                                                         |Q(estudiante__persona__pasaporte__icontains=search),profesor__id=idprofe).order_by('-fecha')
                    else:
                        tutoria = Tutoria.objects.filter(Q(estudiante__persona__apellido1__icontains=ss[0]) &
                                                         Q(estudiante__persona__apellido2__icontains=ss[1])).order_by('-fecha','estudiante__persona__apellido1', 'estudiante__persona__apellido2', 'estudiante__persona__nombres')
                else:
                     if 'id' in request.GET:
                        # tutoria = Tutoria.objects.filter(profesor__id=idprofe).order_by('-fecha')
                         if "i" in request.GET:
                            tutoria = [x for x in Tutoria.objects.filter(profesor__id=idprofe,estado=True).order_by('-fecha') if (EstudianteTutoria.objects.filter(tutoria=x).count()== x.numtutoria)]
                         else:
                            tutoria = [x for x in Tutoria.objects.filter(profesor__id=idprofe,estado=True).order_by('-fecha') if (EstudianteTutoria.objects.filter(tutoria=x).count()!= x.numtutoria)]
                     else:
                         if "i" in request.GET:
                            tutoria = [x for x in Tutoria.objects.filter(profesor__id=idprofe,estado=True).order_by('-fecha') if (EstudianteTutoria.objects.filter(tutoria=x).count()== x.numtutoria)]
                         else:
                            tutoria = [x for x in Tutoria.objects.filter(profesor__id=idprofe,estado=True).order_by('-fecha') if (EstudianteTutoria.objects.filter(tutoria=x).count()!= x.numtutoria)]


                paging = MiPaginador(tutoria, 30)
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
                data['todos'] = todos if todos else ""
                data['tutoria'] = page.object_list
                if 'error' in request.GET:
                    data['error'] = request.GET['error']
                if 'msj' in request.GET:
                    data['msj'] = request.GET['msj']
                data['idprofesor'] = Profesor.objects.get(id=idprofe)
                data['formtesis']= ArchivoTesisForm()
                data['actaform']= ActaSustentacionForm()
                data['comiteform']= ComiteSustentacionForm()
                if 'soli' in request.GET:
                    data['soli']=1
                data['hoy'] = datetime.now().date()
                return render(request ,"tutoria/tutoria.html" ,  data)
    except Exception as ex:
        return HttpResponseRedirect("/?info=Error comunicarse con el administrador ")