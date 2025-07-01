from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from decorators import secure_module
from settings import ACEPTA_PAGO_EFECTIVO, ACEPTA_PAGO_TARJETA, ACEPTA_PAGO_CHEQUE, FACTURACION_ELECTRONICA
from sga.commonviews import addUserData
from sga.forms import SesionCajaForm, CierreSesionCajaForm
from sga.inscripciones import MiPaginador
from sga.models import LugarRecaudacion, Pago, SesionCaja, CierreSesionCaja
from django.template import RequestContext
from sga.commonviews import addUserData, ip_client_address
from django.contrib.contenttypes.models import ContentType
from django.contrib.admin.models import LogEntry, CHANGE
from django.utils.encoding import force_str
import json

@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    if request.method=='POST':
        action = request.POST['action']

        if action == 'cerrarsesion':
            try:
                sesioncaja = SesionCaja.objects.get(pk=request.POST['id'])
                sesioncaja.abierta=False
                sesioncaja.save()
                mensaje='Cierre de Sesion por accion'

                cs = CierreSesionCaja(sesion=sesioncaja,
                                     enmonedas = (sesioncaja.total_sesion_pedagogia()),
                                     total = float(sesioncaja.total_sesion_pedagogia()),
                                     fecha=sesioncaja.fecha,
                                     hora=datetime.now().time())
                cs.save()


                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                    user_id=request.user.pk,
                    content_type_id=ContentType.objects.get_for_model(sesioncaja).pk,
                    object_id=sesioncaja.id,
                    object_repr=force_str(sesioncaja),
                    action_flag=CHANGE,
                    change_message=mensaje + ' (' + client_address + ')')
                return HttpResponse(json.dumps({"result": "ok"}), content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({"result": "bad"}), content_type="application/json")
    else:
        data = {}
        addUserData(request, data)
        if 'action' in request.GET:
           pass
        else:
            try:
                data = {'title': 'Listado de Sesiones'}
                search = None
                if 's' in request.GET:
                    search = request.GET['s']
                if search:
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')
                    if len(ss)==1:
                        sesiones = SesionCaja.objects.filter(pk__icontains=search).order_by('fecha')
                    else:
                        sesiones = SesionCaja.objects.filter(pk__icontains=ss).order_by('fecha')
                else:
                    sesiones = SesionCaja.objects.all().order_by('-id','-fecha','-hora')

                paging = MiPaginador(sesiones, 30)
                p = 1
                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                        paging = MiPaginador(sesiones, 30)
                    page = paging.page(p)
                except Exception as ex:
                    page = paging.page(1)

                data['paging'] = paging
                data['page'] = page
                data['search'] = search if search else ""
                data['rangospaging'] = paging.rangos_paginado(p)
                data['sesiones'] = page.object_list

                return render(request ,"caja/sesiones_caja.html" ,  data)
            except:
                return HttpResponseRedirect("/")
