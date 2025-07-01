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
from settings import FECHA_PAGO_TUTORIA
from sga.commonviews import addUserData, ip_client_address
from sga.forms import EstudianteTutoriaForm, PagartutoriaForm
from sga.models import EstudianteTutoria, Tutoria, PagoTutoria, RolPagoProfesor, DetallePagoTutoria, Profesor, RolPago


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
@transaction.atomic()
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action == 'pagar':
                try:
                    if RolPagoProfesor.objects.filter(id = request.POST['rol']).exists():
                        pagotutoria = PagoTutoria.objects.get(id = request.POST['id'])
                        rolpago = RolPago.objects.filter().order_by('-id')[:1].get()
                        if Decimal(request.POST['valor']) <= Decimal(pagotutoria.pagototal)+Decimal(pagotutoria.saldo):
                            if RolPagoProfesor.objects.filter(rol__id=request.POST['rol'],profesor=pagotutoria.profesor).exists():
                                rolprofesor = RolPagoProfesor.objects.get(rol__id=request.POST['rol'],profesor=pagotutoria.profesor)
                                rolprofesor.tutorias =  Decimal(request.POST['valor'])+ Decimal(rolprofesor.tutorias)

                            else:
                                return HttpResponse(json.dumps({"result":"badrol"}),content_type="application/json")

                            num=0
                            if DetallePagoTutoria.objects.filter(pagotutoria=pagotutoria).exists():
                                detallepago = DetallePagoTutoria.objects.filter(pagotutoria=pagotutoria).order_by('-id')[:1].get()
                                tutoria1 = Tutoria.objects.filter(profesor = pagotutoria.profesor)
                                for tutor in tutoria1:
                                    num = num + len(EstudianteTutoria.objects.filter(tutoria = tutor,fecha__gte=rolpago.inicio,fecha__lte=rolpago.fin,fechaaprobar__gte=datetime(rolpago.inicio.year,rolpago.inicio.month,rolpago.inicio.day,0,0),fechaaprobar__lte=datetime(rolpago.fin.year,rolpago.fin.month,rolpago.fin.day,23,59)).exclude(aprobar=False,asistencia=True).exclude(fechaaprobar__lte=detallepago.fechapago))
                            else:
                                tutoria1 = Tutoria.objects.filter(profesor = pagotutoria.profesor)
                                for tutor in tutoria1:
                                    num = num + len(EstudianteTutoria.objects.filter(tutoria = tutor,fecha__gte=rolpago.inicio,fecha__lte=rolpago.fin,fechaaprobar__lte=datetime(rolpago.fin.year,rolpago.fin.month,rolpago.fin.day,23,59)).exclude(aprobar=False,asistencia=True))
                            if num > 0:
                                saldo = Decimal(pagotutoria.pagototal) + Decimal(pagotutoria.saldo) - Decimal(request.POST['valor'])
                                # valotutoria = Decimal(pagotutoria.pagototal)+Decimal(pagotutoria.saldo)
                            else:
                                saldo = Decimal(pagotutoria.saldo)- Decimal(request.POST['valor'])
                                # valotutoria = Decimal(pagotutoria.saldo)
                            detallepago = DetallePagoTutoria(
                                                    pagotutoria_id = request.POST['id'],
                                                    rol_id = request.POST['rol'],
                                                    valorpago = Decimal(request.POST['valor']),
                                                    saldo = saldo,
                                                    totaltutoria = pagotutoria.totaltutoria,
                                                    valortutorias = Decimal(pagotutoria.pagototal),
                                                    fechapago = datetime.now(),
                                                    contarol = request.POST['contarol'])
                            detallepago.save()
                            pagotutoria.saldo = Decimal(detallepago.saldo)
                            pagotutoria.pagototal = Decimal(0.00)
                            pagotutoria.save()
                            rolprofesor.save()

                            client_address = ip_client_address(request)
                            LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(detallepago).pk,
                                object_id       = detallepago.id,
                                object_repr     = force_str(detallepago),
                                action_flag     = ADDITION,
                                change_message  = 'Pago de Tutoria (' + client_address + ')' )
                            return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                        else:
                            return HttpResponse(json.dumps({"result":"badmayor"}),content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
                except Exception as ex:

                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")



        else:
            data = {'title': 'Detalle de Pagos de Tutorias'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']
                if action == 'pagar':
                    data['title'] = 'Ingreso de Tutoria a Estudiante'
                    hoy = datetime.now().date()
                    form = PagartutoriaForm()
                    data['form'] = form
                    return render(request ,"tutoria/addprofetutoria.html" ,  data)

            else:
                search = None
                todos = None

                if EstudianteTutoria.objects.filter().exists():
                    rolpago = RolPago.objects.filter().order_by('-id')[:1].get()
                    profesor = Profesor.objects.filter(id__in=Tutoria.objects.all().values('profesor'))
                    for profe in profesor:
                        num=0
                        if not PagoTutoria.objects.filter(profesor = profe).exists():
                            tutoria = Tutoria.objects.filter(profesor = profe)
                            for tutor in tutoria:
                                num = num + len(EstudianteTutoria.objects.filter(tutoria = tutor,fecha__gte=FECHA_PAGO_TUTORIA,fecha__lte=rolpago.fin,fechaaprobar__gte=datetime(rolpago.inicio.year,rolpago.inicio.month,rolpago.inicio.day,0,0),fechaaprobar__lte=datetime(rolpago.fin.year,rolpago.fin.month,rolpago.fin.day,23,59)).exclude(aprobar=False,asistencia=True))
                            if num > 0:
                                pagotutoria = PagoTutoria(
                                                    profesor = tutor.profesor,
                                                    totaltutoria = num,
                                                    pagototal = num * tutor.valor,
                                                    saldo = 0.00,
                                                    fecha =datetime.now().date())
                                pagotutoria.save()
                        else:
                            pagotutoria = PagoTutoria.objects.get(profesor = profe)
                            if DetallePagoTutoria.objects.filter(pagotutoria=pagotutoria).exists():
                                detallepago = DetallePagoTutoria.objects.filter(pagotutoria=pagotutoria).order_by('-id')[:1].get()
                                tutoria = Tutoria.objects.filter(profesor = profe)
                                for tutor in tutoria:
                                    num = num + len(EstudianteTutoria.objects.filter(tutoria = tutor,fecha__gte=rolpago.inicio,fecha__lte=rolpago.fin,fechaaprobar__gte=datetime(rolpago.inicio.year,rolpago.inicio.month,rolpago.inicio.day,0,0),fechaaprobar__lte=datetime(rolpago.fin.year,rolpago.fin.month,rolpago.fin.day,23,59)).exclude(aprobar=False,asistencia=True).exclude(fechaaprobar__lte=detallepago.fechapago))
                                if num > 0:
                                    pagotutoria.totaltutoria = num
                                    pagotutoria.pagototal = num * tutor.valor
                                    pagotutoria.fecha =datetime.now().date()
                                    pagotutoria.save()

                                else:
                                    pagotutoria.totaltutoria = num
                                    pagotutoria.pagototal = 0
                                    pagotutoria.save()

                            else:
                                tutoria = Tutoria.objects.filter(profesor = profe)
                                for tutor in tutoria:
                                    num = num + len(EstudianteTutoria.objects.filter(tutoria = tutor,fecha__gte=rolpago.inicio,fecha__lte=rolpago.fin,fechaaprobar__lte=datetime(rolpago.fin.year,rolpago.fin.month,rolpago.fin.day,23,59)).exclude(aprobar=False,asistencia=True))
                                if num > 0:
                                    pagotutoria.profesor = tutor.profesor
                                    pagotutoria.totaltutoria = num
                                    pagotutoria.pagototal = num * tutor.valor
                                    pagotutoria.saldo = 0.00
                                    pagotutoria.fecha =datetime.now().date()
                                    pagotutoria.save()

                                else:
                                    pagotutoria.totaltutoria = num
                                    pagotutoria.pagototal = 0
                                    pagotutoria.save()




                if 's' in request.GET:
                    search = request.GET['s']
                if 't' in request.GET:
                    todos = request.GET['t']
                if search:
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')

                    pagotutoria = PagoTutoria.objects.filter(Q(profesor__persona__nombres__icontains=search)|Q(profesor__persona__apellido1__icontains=search)|Q(profesor__persona__apellido2__icontains=search)
                                                     |Q(profesor__persona__cedula__icontains=search)|Q(profesor__persona__pasaporte__icontains=search))

                else:
                    pagotutoria = PagoTutoria.objects.all().order_by('profesor')

                paging = MiPaginador(pagotutoria, 30)
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
                data['pagotutoria'] = page.object_list
                data['form'] = PagartutoriaForm()
                return render(request ,"tutoria/admin_tutoria.html" ,  data)
    except Exception as ex:
        return HttpResponseRedirect("/?info=Error comunicarse con el administrador ")


