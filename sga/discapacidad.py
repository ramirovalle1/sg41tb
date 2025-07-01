import json
from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models.query_utils import Q
from django.forms import model_to_dict
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
from decorators import secure_module
from settings import EMAIL_ACTIVE
from datetime import datetime, date, timedelta
from sga.commonviews import addUserData, ip_client_address
from sga.forms import PerfilInscripcionForm, DobeInscripcionForm, TipoTestDobeForm, AddTipoTestDobeForm, RecomendacionForm,  AddPersonaForm
from sga.models import Inscripcion, PerfilInscripcion, TipoTestDobe, Nee, InscripcionTipoTestDobe, SeguimientoNee, PersonaNee


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
@secure_module
def view(request):
    if request.method=='POST':
        action = request.POST['action']
        if action=='add':
            if request.POST['id']:
                inscripcion = Inscripcion.objects.get(pk=request.POST['id'])
                f = DobeInscripcionForm(request.POST)
                if f.is_valid():
                    perfil = PerfilInscripcion(inscripcion=inscripcion,
                                                raza=f.cleaned_data['raza'],
                                                estrato=f.cleaned_data['estrato'],
                                                tienediscapacidad=f.cleaned_data['tienediscapacidad'],
                                                porcientodiscapacidad=f.cleaned_data['porcientodiscapacidad'],
                                                carnetdiscapacidad=f.cleaned_data['carnetdiscapacidad'])
                    perfil.save()
                    if perfil.tienediscapacidad:
                        inscripcion.tienediscapacidad = True
                        inscripcion.save()

            else:
                f = PerfilInscripcionForm(request.POST)
                if f.is_valid():
                    f.save()
                else:
                    return HttpResponseRedirect("/dobe?action=add")

        elif action=='edit':
            f = PerfilInscripcionForm(request.POST, instance=PerfilInscripcion.objects.get(pk=request.POST['id']))
            if f.is_valid():
                inscripcion = Inscripcion.objects.get(pk=request.POST['inscripcion'])
                perfil = PerfilInscripcion.objects.filter(inscripcion=inscripcion)[:1].get()
                perfil.raza = f.cleaned_data['raza']
                perfil.estrato = f.cleaned_data['estrato']
                perfil.tipodiscapacidad = f.cleaned_data['tipodiscapacidad']
                perfil.porcientodiscapacidad = f.cleaned_data['porcientodiscapacidad']
                tienediscapacidad = request.POST['tienediscapacidad']
                if tienediscapacidad=='on':
                    inscripcion.tienediscapacidad = True
                    perfil.tienediscapacidad = True
                else:
                    inscripcion.tienediscapacidad = False
                    perfil.tienediscapacidad = False

                if 'tienenee' in request.POST:
                    if request.POST['tienenee'] =='on':
                        perfil.tienenee = True
                    else:
                        perfil.tienenee = False
                perfil.carnetdiscapacidad = f.cleaned_data['carnetdiscapacidad']
                perfil.save()
                inscripcion.save()
                if perfil.tienenee:

                    if Nee.objects.filter(inscripcion=perfil.inscripcion).exists():
                        nee = Nee.objects.filter(inscripcion=perfil.inscripcion)[:1].get()
                        nee.tutor = f.cleaned_data['tutor']
                        nee.contacto = f.cleaned_data['contacto']
                        nee.mediostecnicos = f.cleaned_data['mediostecnicos']

                        nee.save()


                    else:
                        nee = Nee(inscripcion = perfil.inscripcion,
                                              usuario = request.user,
                                              valoracion = f.cleaned_data['valoracion'],
                                              tutor = f.cleaned_data['tutor'],
                                              contacto = f.cleaned_data['contacto'],
                                              mediostecnicos = f.cleaned_data['mediostecnicos'],

                                              fechavaloracion =  datetime.now().date())

                        nee.save()

                    if 'resumen' in request.FILES:
                        if not nee.informe:
                             nee.resumen= request.FILES['resumen']
                             nee.fecharesumen = f.cleaned_data['fecharesumen']
                             nee.save()

                        if  EMAIL_ACTIVE :
                                nee.mail_cargadoc(request.session['persona'].usuario,'Se ha cargado el  Resumen del Proceso Dobe')


                    if 'informe' in request.FILES:
                        if not nee.informe:
                             nee.informe= request.FILES['informe']
                             nee.fechaemision = f.cleaned_data['fechaemision']
                             nee.save()

                             if EMAIL_ACTIVE :
                                nee.mail_cargadoc(request.session['persona'].usuario,'Se ha cargado el  informe del Proceso Dobe')

                    if f.cleaned_data['fechamatricula']:
                        if not nee.fechamatricula:
                            nee.fechamatricula =  f.cleaned_data['fechamatricula']
                            nee.save()

                            if  EMAIL_ACTIVE :
                                nee.mail_cargadoc(request.session['persona'].usuario,'Se ha cargado el  informe del Proceso Dobe')


                return HttpResponseRedirect("/dobe?s="+str(perfil.inscripcion.persona.cedula))
            else:
                return HttpResponseRedirect("/dobe?action=edit&id="+str(request.POST['id']))

        elif action=='del':
            perfil = PerfilInscripcion.objects.get(pk=request.POST['id'])
            perfil.delete()

        elif action == 'addtipotest':
            f= TipoTestDobeForm(request.POST)
            if f.is_valid():
                if 'tipotest' in request.POST:
                    tipotestdobe = TipoTestDobe.objects.get(pk=request.POST['tipotest'])
                    tipotestdobe.nombre = f.cleaned_data['nombre']
                    mensaje = 'Editado'

                else:
                    tipotestdobe = TipoTestDobe(nombre=f.cleaned_data['nombre'])
                    mensaje = 'Adicionado'
                tipotestdobe.save()
                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(tipotestdobe).pk,
                    object_id       = tipotestdobe.id,
                    object_repr     = force_str(tipotestdobe),
                    action_flag     = ADDITION,
                    change_message  = mensaje + ' Tipo de Test Dobe(' + client_address + ')' )

                return  HttpResponseRedirect("/dobe?action=tipotest")
        elif action == 'addtipotestdobe':
            f= AddTipoTestDobeForm(request.POST)
            perfil =  PerfilInscripcion.objects.get(pk=request.POST['id'])
            if f.is_valid():
                if Nee.objects.filter(inscripcion=perfil.inscripcion).exists():
                    nee = Nee.objects.filter(inscripcion=perfil.inscripcion)[:1].get()

                    if not InscripcionTipoTestDobe.objects.filter(nee=nee,tipotes = f.cleaned_data['nombre']).exists():

                        inscdobe = InscripcionTipoTestDobe(nee=nee,
                                                           tipotes = f.cleaned_data['nombre'])
                        inscdobe.save()

                    if 'continuar' in request.POST:
                            return HttpResponseRedirect("/dobe?action=addtipotestdobe&id="+str(perfil.id))
                    else:
                        return HttpResponseRedirect("/dobe?s="+str(perfil.inscripcion.persona.cedula))
            else:
                return  HttpResponseRedirect("/dobe?action=addtipotestdobe&id="+str(perfil.id))

        elif action == 'recomendacion':
            f= RecomendacionForm(request.POST)
            perfil =  PerfilInscripcion.objects.get(pk=request.POST['id'])
            if f.is_valid():
                nee = Nee.objects.filter(inscripcion=perfil.inscripcion)[:1].get()

                if request.POST['op'] == 'e':
                    if  nee.obseducativa == None:
                        mensaje = 'Adicionada Recomendacion Psci. Educativo'
                    else:
                        mensaje = 'Editada Recomendacion Psci. Educativo'
                    nee.obseducativa = f.cleaned_data['recomendacion']


                if request.POST['op'] == 'c':
                    if nee.obsclinica == None:
                        mensaje = 'Adicionada Recomendacion Psci. Clinico'
                    else:
                        mensaje = 'Editada Recomendacion Psci. Clinico'
                    nee.obsclinica = f.cleaned_data['recomendacion']

                nee.save()
                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(nee).pk,
                    object_id       = nee.id,
                    object_repr     = force_str(nee),
                    action_flag     = ADDITION,
                    change_message  = mensaje + ' (' + client_address + ')' )


                return HttpResponseRedirect("/dobe?s="+str(perfil.inscripcion.persona.cedula))
            else:
                 return HttpResponseRedirect("/dobe?s="+str(perfil.inscripcion.persona.cedula))

        elif action == 'addseguimiento':
            try:
                perfil =  PerfilInscripcion.objects.get(pk=request.POST['id'])
                nee = Nee.objects.filter(inscripcion=perfil.inscripcion)[:1].get()
                seguimiento = SeguimientoNee(nee=nee,
                                             observacion = request.POST['obs'],
                                             fecha=datetime.now().date(),
                                             usuario = request.user)
                seguimiento.save()

                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(nee).pk,
                    object_id       = nee.id,
                    object_repr     = force_str(nee),
                    action_flag     = ADDITION,
                    change_message  = 'Adicionado Seguimiento (' + client_address + ')' )

                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            except:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

        elif action == 'addpersona':
            f= AddPersonaForm(request.POST)
            perfil =  PerfilInscripcion.objects.get(pk=request.POST['id'])
            if f.is_valid():
                if Nee.objects.filter(inscripcion=perfil.inscripcion).exists():
                    nee = Nee.objects.filter(inscripcion=perfil.inscripcion)[:1].get()

                    if not PersonaNee.objects.filter(nee=nee,persona__id = f.cleaned_data['nombre_id']).exists():
                        persona = PersonaNee(nee=nee,persona_id = f.cleaned_data['nombre_id'])
                        persona.save()

                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(nee).pk,
                            object_id       = nee.id,
                            object_repr     = force_str(nee),
                            action_flag     = ADDITION,
                            change_message  = 'Adicionada Persona Dobe (' + client_address + ')' )

                    if 'continuar' in request.POST:
                        return HttpResponseRedirect("/dobe?action=addpersona&id="+str(perfil.id))
                    else:
                        return HttpResponseRedirect("/dobe?s="+str(perfil.inscripcion.persona.cedula))
            else:
                return  HttpResponseRedirect("/dobe?action=addtipotestdobe&id="+str(perfil.id))
        return HttpResponseRedirect("/dobe")
    else:
        data = {'title': 'Estudiante Discapacitado'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='detalles':
                data['title'] = 'Detalles'
                nee = Nee.objects.get(pk=request.GET['id'])
                data['nee'] = nee
                if InscripcionTipoTestDobe.objects.filter(nee=nee).exists():
                    data['testaplicado'] = InscripcionTipoTestDobe.objects.filter(nee=nee)

                if SeguimientoNee.objects.filter(nee=nee).exists():
                    data['seguimiento'] = SeguimientoNee.objects.filter(nee=nee)

                if PersonaNee.objects.filter(nee=nee).exists():
                        data['personas'] =PersonaNee.objects.filter(nee=nee)

                return render(request ,"nee/detalledis.html" ,  data)
        else:
            search = None

            if 's' in request.GET:
                search = request.GET['s']
            if search:
                ss = search.split(' ')
                while '' in ss:
                    ss.remove('')
                if len(ss)==1:
                    perfiles = Nee.objects.filter(Q(inscripcion__persona__nombres__icontains=search) | Q(inscripcion__persona__apellido1__icontains=search) | Q(inscripcion__persona__apellido2__icontains=search) | Q(inscripcion__persona__cedula__icontains=search) | Q(inscripcion__persona__pasaporte__icontains=search)).order_by('inscripcion__persona__apellido1', 'inscripcion__persona__apellido2', 'inscripcion__persona__nombres')
                else:
                    perfiles = Nee.objects.filter(Q(inscripcion__persona__apellido1__icontains=ss[0]) & Q(inscripcion__persona__apellido2__icontains=ss[1])).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')

            else:
                perfiles = Nee.objects.all().order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')

            paging = MiPaginador(perfiles, 40)
            p = 1
            try:
                if 'page' in request.GET:
                    p = int(request.GET['page'])
                page = paging.page(p)
            except:
                page = paging.page(1)
            data['paging'] = paging
            data['page'] = page
            data['rangospaging'] = paging.rangos_paginado(p)
            data['search'] = search if search else ""
            data['perfiles'] = page.object_list
            return render(request ,"nee/discapacidad.html" ,  data)
