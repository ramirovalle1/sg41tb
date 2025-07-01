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
from sga.models import AsistenteDepartamento, Nivel, PerfilProfesorAsignatura, MultaDocenteMateria, RolPago


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

        if action == 'cambiar_estado':
            try:
                multa =  MultaDocenteMateria.objects.get(pk=request.POST['id'])
                if multa.aprobado:
                    mensaje = 'Desactivacion de multa'
                else:
                    mensaje = 'Activacion de multa'
                multa.aprobado = not multa.aprobado
                multa.fechaaprobacion = datetime.now()
                multa.usuarioaprobacion = request.user
                multa.save()
                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(multa).pk,
                    object_id       = multa.id,
                    object_repr     = force_str(multa),
                    action_flag     = CHANGE,
                    change_message  = mensaje+' (' + client_address + ')' )

                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            except:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")


    else:
        data = {'title': 'Listado de Multas Docentes'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']

        else:
            try:
                hoy = str(datetime.date(datetime.now()))
                search = None
                multas = MultaDocenteMateria.objects.filter(activo=True).order_by('-fechadesde','-aprobado')
                if 's' in request.GET:
                    search = request.GET['s']
                if search:
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')
                    if len(ss)==1:
                        multas = multas.filter(Q(profesor__persona__apellido1__icontains=search)|Q(profesor__persona__apellido2__icontains=search)|Q(profesor__persona__nombres__icontains=search)|Q(profesor__persona__cedula__icontains=search)).order_by('profesor__persona__apellido1','profesor__persona__apellido2')
                    else:
                        multas = multas.filter(Q(profesor__persona__apellido1__icontains=ss[0]) & Q(profesor__persona__apellido2__icontains=ss[1])).order_by('profesor__persona__apellido1','profesor__persona__apellido2')

                paging = Paginator(multas, 30)
                p = 1
                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                    page = paging.page(p)
                except:
                    page = paging.page(1)

                data['paging'] = paging
                data['page'] = page
                data['multas'] = page.object_list
                data['search'] = search if search else ""
                if 'error' in request.GET:
                    data['error'] = request.GET['error']

                return render(request ,"multa_docente_materia/multa_docente_materia.html" ,  data)
            except Exception as e:
                print(e)
                return HttpResponseRedirect("/multa_docente_materia")
