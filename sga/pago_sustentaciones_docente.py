
from datetime import datetime
import json
from django.contrib.admin.models import LogEntry, CHANGE, ADDITION, DELETION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
from sga.commonviews import addUserData, ip_client_address
from sga.forms import PagoSustentacionesDocenteForm, RangoFacturasForm, PagoOtrosIngresosForm,AprobacionSustentacionesDocenteForm
from sga.models import Banco, CuentaBanco, PagoCheque, PagoSustentacionesDocente, Profesor, RolPago, TipoIngresoDocente, IngresoDocente,convertir_fecha


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
@transaction.atomic()

def view(request):
    if request.method=='POST':
        action = request.POST['action']
        if action == 'add':
            try:
                profesor = Profesor.objects.get(pk=request.POST['profesor'])
                valor_total = float(request.POST['valorxestudiante'])*float(request.POST['numestudiantes'])
                fecha = datetime.strptime(request.POST['fecha'], ('%d-%m-%Y')).date()

                if not request.POST['idpago'] == '':
                # if PagoSustentacionesDocente.objects.filter(pk=request.POST['idpago']).exists():
                    edit = PagoSustentacionesDocente.objects.get(pk=request.POST['idpago'])
                    edit.profesor=profesor
                    edit.valorxestudiante=request.POST['valorxestudiante']
                    edit.numestudiantes=request.POST['numestudiantes']
                    edit.valortotal=valor_total
                    edit.fecha=fecha
                    mensaje = 'Edicion Pago de Sustentacion a Docente'
                    edit.save()

                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(edit).pk,
                    object_id       = edit.id,
                    object_repr     = force_str(edit),
                    action_flag     = CHANGE,
                    change_message  = mensaje+' (' + client_address + ')' )
                else:
                    add = PagoSustentacionesDocente(profesor=profesor,
                                                    valorxestudiante=request.POST['valorxestudiante'],
                                                    numestudiantes=request.POST['numestudiantes'],
                                                    valortotal=valor_total,
                                                    fecha=fecha,
                                                    fechaingreso=datetime.now().date())
                    mensaje = 'Nuevo Pago de Sustentacion a Docente'
                    add.save()
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(add).pk,
                    object_id       = add.id,
                    object_repr     = force_str(add),
                    action_flag     = ADDITION,
                    change_message  = mensaje+' (' + client_address + ')' )
                return HttpResponseRedirect('/pago_sustentaciones_docente')
            except Exception as ex:
                print(ex)
                return HttpResponseRedirect('/pago_sustentaciones_docente?error=Ocurrio un error, vuelva a intentarlo. ('+str(ex)+')')

        elif action == 'eliminar':
            result = {}
            try:
                eliminar = PagoSustentacionesDocente.objects.get(pk=request.POST['idpago'])
                mensaje = 'Eliminar pago Sustentacion Docente'
                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(eliminar).pk,
                    object_id       = eliminar.id,
                    object_repr     = force_str(eliminar),
                    action_flag     = DELETION,
                    change_message  = mensaje+' (' + client_address + ')' )
                eliminar.delete()
                result['result']  = "ok"
                return HttpResponse(json.dumps(result), content_type="application/json")
            except Exception as e:
                result['result']  = str(e)
                return HttpResponse(json.dumps(result), content_type="application/json")

        elif action == 'aprobar_pago':
            result = {}
            try:
                pago = PagoSustentacionesDocente.objects.filter(pk=request.POST['idpago'])[:1].get()
                fecha = request.POST['fechaaprob']
                fecha= convertir_fecha(fecha).date()
                hoy = datetime.now().date()
                # rolactual = RolPago.objects.filter(cerrado=False).order_by('-id')[:1].get()
                if RolPago.objects.filter(inicio__lte=fecha, fin__gte=fecha, cerrado=False).order_by('-id').exists():
                    rol = RolPago.objects.filter(inicio__lte=fecha, fin__gte=fecha, cerrado=False).order_by('-id')[:1].get()
                    if rol.fechamax >= hoy:
                        pago.aprobado = True
                        pago.fechaaprobacion = fecha
                        pago.save()
                        mensaje = 'Aprobar pago Sustentacion Docente'
                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(pago).pk,
                            object_id       = pago.id,
                            object_repr     = force_str(pago),
                            action_flag     = CHANGE,
                            change_message  = mensaje+' (' + client_address + ')' )
                        result['result']  = "ok"
                        result['rol'] = rol.nombre
                    else:
                        result['result']  = "No puede aprobar pago con la fecha ingresada"
                else:
                    result['result']  = "No puede aprobar pago con la fecha ingresada"
                return HttpResponse(json.dumps(result), content_type="application/json")
            except Exception as e:
                print(e)
                result['result']  = str(e)
                return HttpResponse(json.dumps(result), content_type="application/json")

        elif action == 'aprobar_pagos':
            result = {}
            try:
                rolpago = RolPago.objects.get(pk=request.POST['rol'])
                if PagoSustentacionesDocente.objects.filter(fecha__gte=rolpago.inicio, fecha__lte=rolpago.fin, aprobado=False).exists():
                    pagos = PagoSustentacionesDocente.objects.filter(fecha__gte=rolpago.inicio, fecha__lte=rolpago.fin, aprobado=False)
                    for p in pagos:
                        p.aprobado=True
                        p.fechaaprobacion = datetime.now()
                        p.save()
                        mensaje = 'Aprobar pagos Sustentaciones Docentes'
                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(p).pk,
                            object_id       = p.id,
                            object_repr     = force_str(p),
                            action_flag     = DELETION,
                            change_message  = mensaje+' (' + client_address + ')' )
                    return HttpResponse(json.dumps({"result": "ok","mensaje":'Se han aprobado '+str(pagos.count())+' pagos de sustentaciones docentes'}),content_type="application/json")
                else:
                    return HttpResponse(json.dumps({"result": "bad","mensaje":'No existen pagos por aprobar en el rol actual'}),content_type="application/json")

            except Exception as e:
                result['result']  = str(e)
                return HttpResponse(json.dumps(result), content_type="application/json")

        if action == 'add_ingreso':
            try:
                print(request.POST)
                profesor = Profesor.objects.get(pk=request.POST['profesor'])
                valor = request.POST['valor']
                fecha = datetime.now()
                tipo = TipoIngresoDocente.objects.get(pk=request.POST['tipo'])

                if request.POST['idpago'] != '':
                    edit = IngresoDocente.objects.get(pk=request.POST['idpago'])
                    edit.profesor=profesor
                    edit.valor=valor
                    edit.fecha=fecha
                    mensaje = 'Edicion Pago Docente'
                    edit.save()

                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(edit).pk,
                    object_id       = edit.id,
                    object_repr     = force_str(edit),
                    action_flag     = CHANGE,
                    change_message  = mensaje+' (' + client_address + ')' )
                else:
                    add = IngresoDocente(profesor=profesor,
                                        valor=valor,
                                        fecha=fecha,
                                        tipo=tipo)
                    mensaje = 'Nuevo Pago Docente'
                    add.save()
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(add).pk,
                    object_id       = add.id,
                    object_repr     = force_str(add),
                    action_flag     = ADDITION,
                    change_message  = mensaje+' (' + client_address + ')' )
                return HttpResponseRedirect('/pago_sustentaciones_docente?action=ingresos&id='+str(tipo.id))
            except Exception as ex:
                print(ex)
                return HttpResponseRedirect('/pago_sustentaciones_docente?error=Ocurrio un error, vuelva a intentarlo. ('+str(ex)+')')

        elif action == 'aprobar_ingreso':

            result = {}
            try:
                pago = IngresoDocente.objects.get(pk=request.POST['idpago'])
                #OCastillo 04-08-2022 fecha de aprobacion sea ingresada por usuario aprueba
                fecha = request.POST['fechaaprob']
                fecha=convertir_fecha(fecha)
                pago.aprobado = True
                pago.fechaaprobacion = fecha
                pago.save()
                mensaje = 'Aprobar Ingreso Docente'
                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(pago).pk,
                    object_id       = pago.id,
                    object_repr     = force_str(pago),
                    action_flag     = CHANGE,
                    change_message  = mensaje+' (' + client_address + ')' )

                result['result']  = "ok"
                return HttpResponse(json.dumps(result), content_type="application/json")
            except Exception as e:
                result['result']  = str(e)
                return HttpResponse(json.dumps(result), content_type="application/json")

    else:
        data = {'title': 'Listado Pago Sustentaciones Docente'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action == 'ingresos':
                print(request.GET)
                try:
                    tipoingreso = TipoIngresoDocente.objects.get(pk=request.GET['id'])
                    ingresos = IngresoDocente.objects.filter(tipo=tipoingreso).order_by('-id')
                    print(ingresos.count())
                    search = None
                    if 's' in request.GET:
                        search = request.GET['s']
                    if search:
                        ss = search.split(' ')
                        while '' in ss:
                            ss.remove('')
                        if len(ss)==1:
                            ingresos = ingresos.filter(Q(profesor__persona__nombres__icontains=search) | Q(profesor__persona__apellido1__icontains=search) | Q(profesor__persona__apellido2__icontains=search) | Q(profesor__persona__cedula__icontains=search) | Q(profesor__persona__pasaporte__icontains=search) | Q(profesor__persona__usuario__username__icontains=search)).order_by('profesor__persona__apellido1')[:100]
                        else:
                            ingresos = ingresos.filter(Q(profesor__persona__apellido1__icontains=ss[0]) & Q(profesor__persona__apellido2__icontains=ss[1])).order_by('profesor__persona__apellido1','profesor__persona__apellido2','profesor__persona__nombres')[:100]

                    paging = Paginator(ingresos, 30)
                    p = 1
                    try:
                        if 'page' in request.GET:
                            p = int(request.GET['page'])
                        page = paging.page(p)
                    except:
                        page = paging.page(1)
                    data['paging'] = paging
                    data['page'] = page
                    data['search'] = search if search else ""
                    data['ingresos'] = page.object_list
                    data['tipo_ingreso'] = tipoingreso
                    data['rol_pago'] = RolPago.objects.filter().order_by('-id')[:1].get()
                    data['form']=PagoOtrosIngresosForm()
                    data['form2']=AprobacionSustentacionesDocenteForm(initial={'fechaaprueba':datetime.now().date()})
                    if 'error' in request.GET:
                        data['error'] = request.GET['error']
                    data['otrosingresos'] = TipoIngresoDocente.objects.filter(estado=True).order_by('descripcion')

                    return render(request ,"pago_sustentaciones_docente/otrospagos.html" ,  data)
                except Exception as ex:
                    print(ex)


        else:
            try:
                pagos_sustentaciones = PagoSustentacionesDocente.objects.filter().order_by('-fecha')
                search = None
                if 's' in request.GET:
                    search = request.GET['s']
                if search:
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')
                    if len(ss)==1:
                        pagos_sustentaciones = pagos_sustentaciones.filter(Q(profesor__persona__nombres__icontains=search) | Q(profesor__persona__apellido1__icontains=search) | Q(profesor__persona__apellido2__icontains=search) | Q(profesor__persona__cedula__icontains=search) | Q(profesor__persona__pasaporte__icontains=search) | Q(profesor__persona__usuario__username__icontains=search)).order_by('-fecha','profesor__persona__apellido1','profesor__persona__apellido2','profesor__persona__nombres')[:100]
                    else:
                        pagos_sustentaciones = pagos_sustentaciones.filter(Q(profesor__persona__apellido1__icontains=ss[0]) & Q(profesor__persona__apellido2__icontains=ss[1])).order_by('-fecha','profesor__persona__apellido1','profesor__persona__apellido2','profesor__persona__nombres')[:100]

                paging = Paginator(pagos_sustentaciones, 30)
                p = 1
                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                    page = paging.page(p)
                except:
                    page = paging.page(1)
                data['paging'] = paging
                data['page'] = page
                data['search'] = search if search else ""
                data['pagos_sustentaciones'] = page.object_list
                data['rol_pago'] = RolPago.objects.filter().order_by('-id')[:1].get()
                data['form']=PagoSustentacionesDocenteForm(initial={'fecha':datetime.now().strftime('%d-%m-%Y')})
                data['form2']=AprobacionSustentacionesDocenteForm(initial={'fechaaprueba':datetime.now().date()})
                data['generarform']=RangoFacturasForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
                if 'error' in request.GET:
                    data['error'] = request.GET['error']
                data['otrosingresos'] = TipoIngresoDocente.objects.filter(estado=True).order_by('descripcion')
                return render(request ,"pago_sustentaciones_docente/pago_sustentacionesbs.html" ,  data)
            except Exception as e:
                print(e)
                return HttpResponseRedirect("/?"+str(e))
