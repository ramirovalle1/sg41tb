from datetime import datetime
import json
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Q
from django.db import transaction
from django.forms.models import model_to_dict
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
from decorators import secure_module
from sga.commonviews import addUserData, ip_client_address
from sga.forms import CuentaBancoForm
from sga.models import CuentaBanco, Banco


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
#@secure_module
@transaction.atomic()

def view(request):
    if request.method=='POST':
        action = request.POST['action']

        if action == 'eliminar':
                result = {}
                try:
                    eliminar = CuentaBanco.objects.get(pk=request.POST['id'])
                    msj = 'Eliminado Cuenta'
                    result['result']  = "ok"

                    #Obtain client ip address
                    client_address = ip_client_address(request)
                    client_address = ip_client_address(request)

                    # Log de APLICAR DONACION
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(eliminar).pk,
                        object_id       = eliminar.id,
                        object_repr     = force_str(eliminar),
                        action_flag     = ADDITION,
                        change_message  = msj + ' (' + client_address + ')')
                    eliminar.delete()
                    return HttpResponse(json.dumps(result), content_type="application/json")
                except Exception as e:
                    result['result']  = str(e)
                    return HttpResponse(json.dumps(result), content_type="application/json")


        elif action=='buscar':
            # verificar cuenta antes de grabar
            cta=request.POST['numero']
            if CuentaBanco.objects.filter(numero=int(request.POST['numero'])).exists():
               cuenta=cta
               return HttpResponse(json.dumps({"result":"bad","cuenta":cuenta}),content_type="application/json")
            else:
               return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")


        elif action=='add':
            try:
                banco = request.POST['banco']
                numero = request.POST['numero']
                tipocuenta = request.POST['tipocuenta']
                representante = request.POST['representante']
                if request.POST['idcuenta'] == '':
                    cuenta_id = 0
                else:
                    cuenta_id = request.POST['idcuenta']

                if CuentaBanco.objects.filter(pk=cuenta_id).exists():

                    if CuentaBanco.objects.filter(banco=banco, numero=numero).exclude(id=cuenta_id).exists():
                        return HttpResponseRedirect("/cuentabancaria?error=Cuenta Bancaria ya existe")
                    else:
                        cuenta = CuentaBanco.objects.get(pk=request.POST['idcuenta'])
                        cuenta.banco_id         = banco
                        cuenta.numero           = numero
                        cuenta.tipocuenta       = tipocuenta
                        cuenta.representante    = representante
                        cuenta.save()
                        msj = 'Editada Cuenta'
                else:
                    if CuentaBanco.objects.filter(banco=banco, numero=numero).exists():
                        return HttpResponseRedirect("/cuentabancaria?error=Cuenta Bancaria ya existe")
                    else:
                        cuenta = CuentaBanco(banco_id=banco, numero=numero, tipocuenta=tipocuenta, representante=representante)
                        cuenta.save()
                        msj = 'Adicionada Cuenta'
                        #Obtain client ip address
                if 'activo' in request.POST:
                    activo=request.POST['activo']
                else:
                    activo=False
                cuenta.activo = activo
                cuenta.save()

                client_address = ip_client_address(request)

                # Log de APLICAR DONACION
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(cuenta).pk,
                    object_id       = cuenta.id,
                    object_repr     = force_str(cuenta),
                    action_flag     = ADDITION,
                    change_message  = msj + ' (' + client_address + ')')

                return HttpResponseRedirect("/cuentabancaria")
            except Exception as ex:
                return HttpResponseRedirect('/cuentabancaria?error=Error al realizar la transaccion')

    else:
        data = {'title': 'Listado de Cuentas Bancarias'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']

        else:
            try:
                search = None

                if 's' in request.GET:
                    search = request.GET['s']

                if search:
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')
                    if len(ss)==1:
                        cuenta = CuentaBanco.objects.filter(Q(banco__nombre__icontains=search)|Q(numero__icontains = search)).order_by('banco')
                    else:
                        cuenta = CuentaBanco.objects.filter(Q(banco__nombre__icontains=ss[0])|Q(numero__icontains = ss[0])).order_by('banco')
                else:
                    cuenta = CuentaBanco.objects.filter().order_by('banco')

                paging = MiPaginador(cuenta, 30)
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
                data['form'] = CuentaBancoForm()
                data['cuentabanco'] = page.object_list
                if 'error' in request.GET:
                    data['error']= request.GET['error']
                return render(request ,"cuentabancaria/cuentabancaria.html" ,  data)

            except Exception as e:
                return HttpResponseRedirect("/")