from django.forms.models import model_to_dict
from datetime import datetime
import json
import os
from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.utils.encoding import force_str
from decorators import secure_module
from settings import MEDIA_ROOT, EMAIL_ACTIVE
from sga.commonviews import addUserData, ip_client_address
from sga.forms import ResolucionForm, ArchivoResolucionForm
from sga.models import RetiradoMatricula,MotivoResolucion,Resolucion,ArchivoResolucion,Inscripcion
from django.shortcuts import render



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
    try:
        if request.method=='POST':
            if 'action' in request.POST:
                action = request.POST['action']
                if action == 'addresolucion':
                    f = ResolucionForm(request.POST,request.FILES)

                    if f.is_valid():
                        file = ''
                        if 'archivo' in request.FILES:
                            file = request.FILES['archivo']
                        nivel=None
                        if Inscripcion.objects.get(id=request.POST['inscrip']).matriculado():
                            nivel = Inscripcion.objects.get(id=request.POST['inscrip']).matricula().nivel
                        bande =0
                        if 'edit' in request.POST:

                            resolucion = Resolucion.objects.get(id=request.POST['edit'])
                            if resolucion.inscripcion_id == int(request.POST['inscrip']):
                                bande =1
                            resolucion.motivo = f.cleaned_data['motivo']
                            resolucion.inscripcion_id = request.POST['inscrip']
                            resolucion.asunto = f.cleaned_data['asunto']
                            resolucion.resumen = f.cleaned_data['resumen']
                            resolucion.fecharesolucion = f.cleaned_data['fecharesolucion']
                            resolucion.fecha = datetime.now()
                            resolucion.nivel = nivel
                            resolucion.user = request.user
                            mensaje = 'Edicion'
                            resolucion.save()
                        else:
                            resolucion =Resolucion(
                                        motivo = f.cleaned_data['motivo'],
                                        inscripcion_id = request.POST['inscrip'],
                                        asunto = f.cleaned_data['asunto'],
                                        resumen = f.cleaned_data['resumen'],
                                        fecharesolucion = f.cleaned_data['fecharesolucion'],
                                        fecha = datetime.now(),
                                        nivel = nivel,
                                        user = request.user
                                        )
                            resolucion.save()
                            if f.cleaned_data['numero'] or file:
                                archivoresol = ArchivoResolucion(
                                                                resolucion = resolucion,
                                                                numero = f.cleaned_data['numero'],
                                                                archivo = file,
                                                                fecha = datetime.now(),
                                                                user = request.user
                                                                )

                                archivoresol.save()
                            mensaje = 'Ingreso'
                        if EMAIL_ACTIVE:
                            resolucion.correo_resolucion(mensaje)
                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(resolucion).pk,
                            object_id       = resolucion.id,
                            object_repr     = force_str(resolucion),
                            action_flag     = ADDITION,
                            change_message  = mensaje +' de resolucion (' + client_address + ')' )
                        if 'edit' in request.POST and bande == 1:
                            return HttpResponseRedirect('/resoluciones?action=resolucion&id='+str(request.POST['inscrip']))

                    return HttpResponseRedirect('/resoluciones')

                elif action == 'addmotivo':
                    try:
                        mensaje = ''
                        if request.POST['edit'] == '0':
                            motivo = MotivoResolucion(descripcion = request.POST['descripcion'])
                            motivo.save()
                            mensaje = 'Ingreso'
                        else:
                            motivo = MotivoResolucion.objects.get(id = request.POST['edit'])
                            motivo.descripcion = str(request.POST['descripcion'])
                            motivo.save()
                            mensaje = 'Edicion'
                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(motivo).pk,
                            object_id       = motivo.id,
                            object_repr     = force_str(motivo),
                            action_flag     = ADDITION,
                            change_message  = mensaje +' de Motivo de resolucion (' + client_address + ')' )
                        return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                    except Exception as ex:
                        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
                elif action == 'addarchivo':
                    f = ArchivoResolucionForm(request.POST,request.FILES)
                    if 'archivo' in request.FILES:
                        archivo = request.FILES['archivo']
                    else:
                        archivo = ''

                    if request.POST['editar'] == '0':
                        archivoresol = ArchivoResolucion(
                                                        resolucion_id = request.POST['idresolu'],
                                                        numero = str(request.POST['numero']),
                                                        archivo = archivo,
                                                        fecha = datetime.now(),
                                                        user = request.user
                                                        )
                        mensaje = 'Ingreso'
                    else:
                        archivoresol = ArchivoResolucion.objects.get(id = request.POST['editar'])

                        if str(archivoresol.archivo):
                            if (MEDIA_ROOT + '/' + str(archivoresol.archivo)) and archivo:
                                os.remove(MEDIA_ROOT + '/' + str(archivoresol.archivo))

                        if archivo:
                            archivoresol.archivo = archivo
                        archivoresol.numero = str(request.POST['numero'])
                        archivoresol.fecha = datetime.now()
                        archivoresol.user = request.user
                        mensaje = 'Edicion'
                    archivoresol.save()
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(archivoresol).pk,
                        object_id       = archivoresol.id,
                        object_repr     = force_str(archivoresol),
                        action_flag     = ADDITION,
                        change_message  = mensaje +' archivo de Resolucion (' + client_address + ')' )
                    if request.POST['editar'] == '0':
                        return HttpResponseRedirect('/resoluciones?action=resolucion&id='+str(request.POST['inscripcion']))
                    else:
                        return HttpResponseRedirect('/resoluciones?action=resolucion&id='+str(request.POST['inscripcion'])+'&edit='+str(request.POST['editar']))

        else:
            data = {'title': 'Motivo de Resolucion'}
            addUserData(request,data)

            if 'action' in request.GET:
                action = request.GET['action']
                if action == 'addresoluciones':
                    data['title'] = 'Ingresar Datos'
                    data['form'] = ResolucionForm(initial={'fecharesolucion': datetime.now()})
                    return render(request ,"resoluciones/addresolucion.html" ,  data)
                elif action == 'editresolucion':
                    data['title'] = 'Ingresar Datos'
                    resolucion = Resolucion.objects.get(id=request.GET['id'])
                    data['form'] = ResolucionForm(initial=model_to_dict(resolucion))
                    data['resolucion'] = resolucion
                    return render(request ,"resoluciones/addresolucion.html" ,  data)

                elif action == 'eliminar':
                    archivoresol = ArchivoResolucion.objects.get(id=request.GET['id'])
                    resolucion = archivoresol.resolucion
                    if archivoresol.archivo:
                        if (MEDIA_ROOT + '/' + str(archivoresol.archivo)):
                                os.remove(MEDIA_ROOT + '/' + str(archivoresol.archivo))

                    archivoresol.delete()

                    if not ArchivoResolucion.objects.filter(resolucion=resolucion).exists():
                        return HttpResponseRedirect('/resoluciones?action=resolucion&id='+str(resolucion.inscripcion.id)+'&elim=1')
                    else:
                        idarch = ArchivoResolucion.objects.filter(resolucion=resolucion)[:1].get().id
                        return HttpResponseRedirect('/resoluciones?action=resolucion&id='+str(resolucion.inscripcion.id)+'&edit='+str(idarch))


                elif action=='detallearch':
                    data = {}
                    data['archresoluciones'] = ArchivoResolucion.objects.filter(resolucion__id=request.GET['id']).order_by('fecha')
                    return render(request ,"resoluciones/detallearchivo.html" ,  data)

                elif action == 'motivoresolucion':
                    search = None
                    todos = None

                    if 's' in request.GET:
                        search = request.GET['s']

                    if search:
                        ss = search.split(' ')
                        while '' in ss:
                            ss.remove('')

                        motivoresol = MotivoResolucion.objects.filter(descripcion__icontains=search).order_by('descripcion')
                    else:
                        motivoresol = MotivoResolucion.objects.all().order_by('descripcion')

                    paging = MiPaginador(motivoresol, 30)
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
                    data['todos'] = todos if todos else ""
                    data['motivoresol'] = page.object_list
                    return render(request ,"resoluciones/motivoresolucion.html" ,  data)
                elif action == 'resolucion':
                    search = None
                    todos = None

                    if 's' in request.GET:
                        search = request.GET['s']

                    if search:
                        ss = search.split(' ')
                        while '' in ss:
                            ss.remove('')

                        resolucion = Resolucion.objects.filter(asunto__icontains=search,inscripcion=request.GET['id']).order_by('asunto')
                    else:
                        resolucion = Resolucion.objects.filter(inscripcion=request.GET['id']).order_by('asunto')

                    paging = MiPaginador(resolucion, 30)
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
                    data['todos'] = todos if todos else ""
                    data['resoluciones'] = page.object_list
                    data['inscripcion'] = Inscripcion.objects.filter(id=request.GET['id'])[:1].get()
                    if 'elim' in request.GET:
                        data['error'] = 'El registro fue eliminado'
                    if 'edit' in request.GET:
                        archivo = ArchivoResolucion.objects.get(id=request.GET['edit'])
                        data['edit'] = archivo
                    data['form'] = ArchivoResolucionForm()
                    return render(request ,"resoluciones/lista_resolucion.html" ,  data)

            else:
                search = None
                if 's' in request.GET:
                    search = request.GET['s']

                if search:
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')
                    if len(ss)==1:
                        inscripciones = Inscripcion.objects.filter(id__in= Resolucion.objects.filter(Q(inscripcion__persona__nombres__icontains=search) | Q(inscripcion__persona__apellido1__icontains=search) | Q(inscripcion__persona__apellido2__icontains=search) | Q(inscripcion__persona__cedula__icontains=search) | Q(inscripcion__persona__pasaporte__icontains=search)).values('inscripcion')).order_by( 'persona__apellido1')
                    else:
                        inscripciones = Inscripcion.objects.filter(id__in= Resolucion.objects.filter(Q(inscripcion__persona__apellido1__icontains=ss[0]) & Q(inscripcion__persona__apellido2__icontains=ss[1]).values('inscripcion'))).order_by( 'persona__apellido1','persona__apellido2','persona__nombres')
                else:
                    inscripciones = Inscripcion.objects.filter(id__in=Resolucion.objects.filter().distinct().values('inscripcion') ).order_by('persona__apellido1')


                paging = MiPaginador(inscripciones, 30)
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
                data['inscripciones'] = page.object_list
                return render(request ,"resoluciones/resoluciones.html" ,  data)
    except Exception as ex:
        return HttpResponseRedirect("/?info=Error contactar con el administrador")


