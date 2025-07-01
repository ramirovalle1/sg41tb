from datetime import datetime
from decimal import Decimal
import json
from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
from decorators import secure_module
from sga.commonviews import addUserData, ip_client_address
from sga.forms import EstudianteTutoriaForm, PagartutoriaForm
from sga.models import EstudianteTutoria, Profesor,Tutoria, PagoTutoria, RolPagoProfesor, DetallePagoTutoria


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
            if action == 'pagar':
                try:
                    if RolPagoProfesor.objects.filter(id = request.POST['rol']).exists():
                        pagotutoria = PagoTutoria.objects.get(id = request.POST['id'])
                        if Decimal(request.POST['valor']) <= Decimal(pagotutoria.pagototal):
                            detallepago = DetallePagoTutoria(
                                                    pagotutoria_id = request.POST['id'],
                                                    rol_id = request.POST['rol'],
                                                    valorpago = Decimal(request.POST['valor']),
                                                    saldo = Decimal(pagotutoria.pagototal)+Decimal(pagotutoria.saldo)-Decimal(request.POST['valor']),
                                                    totaltutoria = pagotutoria.totaltutoria,
                                                    valortutorias = Decimal(pagotutoria.pagototal),
                                                    fechapago = datetime.now())
                            detallepago.save()
                            pagotutoria.saldo = Decimal(detallepago.saldo)
                            pagotutoria.save()
                            client_address = ip_client_address(request)
                            LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(detallepago).pk,
                                object_id       = detallepago.id,
                                object_repr     = force_str(detallepago),
                                action_flag     = ADDITION,
                                change_message  = 'Adicionado Pago Tutoria (' + client_address + ')' )
                            return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                        else:
                            return HttpResponse(json.dumps({"result":"badmayor"}),content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
                except:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")


            return HttpResponseRedirect('/profe_tutoria')

        else:
            data = {'title': 'Detalle de Pago Tutoria'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']

            else:
                search = None
                todos = None

                if 's' in request.GET:
                    search = request.GET['s']
                if 't' in request.GET:
                    todos = request.GET['t']
                if search:
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')

                    detallepago = DetallePagoTutoria.objects.filter(Q(pagotutoria__profesor__persona__nombres__icontains=search)|Q(pagotutoria__profesor__persona__apellido1__icontains=search)|Q(pagotutoria__profesor__persona__apellido2__icontains=search)
                                                     |Q(pagotutoria__profesor__persona__cedula__icontains=search)|Q(pagotutoria__profesor__persona__pasaporte__icontains=search))

                else:
                    detallepago = DetallePagoTutoria.objects.filter(pagotutoria__id = request.GET['id']).order_by('-id')

                paging = MiPaginador(detallepago, 30)
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
                data['detallepago'] = page.object_list
                data['profesor'] = Profesor.objects.get(id = PagoTutoria.objects.get(id = request.GET['id']).profesor.id)
                return render(request ,"tutoria/detallepagotutoria.html" ,  data)
    except Exception as ex:
        return HttpResponseRedirect("/?info=Error comunicarse con el administrador ")



