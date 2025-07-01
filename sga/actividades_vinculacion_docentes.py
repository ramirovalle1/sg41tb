from datetime import datetime
import json
from django.contrib.admin.models import LogEntry, ADDITION, DELETION, CHANGE
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
from decorators import secure_module
from sga.commonviews import addUserData, ip_client_address
from sga.models import DocenteVinculacion,convertir_fecha
from sga.forms import CambioFechaActividadVinculacionForm


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
@transaction.atomic()

def view(request):
    if request.method=='POST':
        action = request.POST['action']
        if action == 'edit_docenteactividad':
            try:
                print(request.POST)
                docentevinculacion = DocenteVinculacion.objects.filter(pk=request.POST['iddocenteactividad'])[:].get()
                print(docentevinculacion)
                docentevinculacion.fecha = convertir_fecha(request.POST['fecha']).date()
                docentevinculacion.fechacambio = datetime.now()
                docentevinculacion.usuariocambio=request.user
                docentevinculacion.save()
                mensaje = 'Cambio en Fecha Docente Vinculacion'
                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                user_id         = request.user.pk,
                content_type_id = ContentType.objects.get_for_model(docentevinculacion.actividad).pk,
                object_id       = docentevinculacion.id,
                object_repr     = force_str(docentevinculacion.actividad),
                action_flag     = CHANGE,
                change_message  = mensaje+' (' + client_address + ')' )
                return HttpResponseRedirect('/act_docentes_vinculacion?s='+str(docentevinculacion.persona))
            except Exception as ex:
                print(ex)
                return HttpResponseRedirect('/act_docentes_vinculacion?error=Error al editar docente actividad, vuelva a intentarlo')


    else:
        data = {'title': 'Actividades de Vinculacion Docentes'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
        else:
            try:
                hoy = str(datetime.date(datetime.now()))
                search = None
                docentes = DocenteVinculacion.objects.filter(fecha__gte='2018-01-01').order_by('-fecha')
                if 's' in request.GET:
                    search = request.GET['s']
                if search:
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')
                    if len(ss)==1:
                        docentes = docentes.filter(Q(persona__apellido1__icontains=search)|Q(persona__apellido2__icontains=search)|Q(persona__nombres__icontains=search)|Q(persona__cedula__icontains=search)).order_by('-fecha')
                    else:
                        docentes = docentes.filter(Q(persona__apellido1__icontains=ss[0]) & Q(persona__apellido2__icontains=ss[1])).order_by('-fecha')

                paging = Paginator(docentes, 30)
                p = 1
                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                    page = paging.page(p)
                except:
                    page = paging.page(1)

                data['paging'] = paging
                data['page'] = page
                data['docentes'] = page.object_list
                data['formactividad'] = CambioFechaActividadVinculacionForm(initial={'fecha': datetime.now().strftime("%d-%m-%Y")})

                data['search'] = search if search else ""
                if 'error' in request.GET:
                    data['error'] = request.GET['error']

                return render(request ,"act_vinculaciondocentes/actividades_vinculacion_docentes.html" ,  data)
            except Exception as e:
                print(e)
                return HttpResponseRedirect("/act_vinculaciondocentes")
