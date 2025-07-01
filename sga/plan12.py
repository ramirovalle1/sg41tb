from datetime import datetime, timedelta
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from decorators import secure_module
from settings import DIA_PAGO_PLAN12
from sga.commonviews import addUserData
from sga.forms import BeneficiarioPlan12Form
from sga.models import Plan12Materias, Rubro, RubroPlan12Materias


def proxima_fecha_pasada(fecha):
    mes = fecha.month+1
    anno = fecha.year
    if mes>12:
        mes = 1
        anno += 1
    return datetime(anno, mes, DIA_PAGO_PLAN12)

def proxima_fecha(fecha):
    if fecha.day>DIA_PAGO_PLAN12:
        return proxima_fecha_pasada(fecha)
    elif fecha.day<DIA_PAGO_PLAN12:
        return datetime(fecha.year, fecha.month, DIA_PAGO_PLAN12)
    elif fecha.day==DIA_PAGO_PLAN12:
        return fecha


@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    if request.method=='POST':
        action = request.POST['action']
        if action=='add':
            f = BeneficiarioPlan12Form(request.POST)
            if f.is_valid():
                beneficiario = Plan12Materias(inscripcion = f.cleaned_data['inscripcion'],
                                              numerocontrato=f.cleaned_data['contrato'],
                                              inicio=f.cleaned_data['inicio'],
                                              vencimiento=f.cleaned_data['vencimiento'],
                                              materiastotales=f.cleaned_data['materiastotales'],
                                              materiascursadas=f.cleaned_data['materiascursadas'],
                                              valorpormateria=f.cleaned_data['valorpormateria'],
                                              valortotal=f.cleaned_data['valorpormateria'] * f.cleaned_data['materiastotales'],
                                              valorpagado=0,
                                              valorvencido=f.cleaned_data['valorpormateria'] * f.cleaned_data['materiastotales']
                                              )
                beneficiario.save()

                # Crear Rubros
                if beneficiario.materiascursadas==0:
                    proxfecha = proxima_fecha(beneficiario.inicio)
                    for i in range(1, beneficiario.materiastotales+1):
                        rubro = Rubro(fecha=datetime.today().date(),
                                      valor = beneficiario.valorpormateria,
                                      inscripcion=beneficiario.inscripcion,
                                      cancelado = False,
                                      fechavence = proxfecha)
                        rubro.save()
                        rubroPlan = RubroPlan12Materias(rubro=rubro,
                                                        plan=beneficiario,
                                                        cuota=i)
                        rubroPlan.save()

                        proxfecha = proxima_fecha(proxfecha+timedelta(1))



                return HttpResponseRedirect("/plan12")
            else:
                return HttpResponseRedirect("/plan12?action=add")
        return HttpResponseRedirect("/plan12")
    else:
        data = {'title': 'Listado de Beneficiarios Plan12'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='add':
                data['title'] = 'Adicionar Beneficiario Plan12'
                data['form'] = BeneficiarioPlan12Form(initial={"inicio":datetime.today(), "vencimiento": datetime.today()})
                return render(request ,"plan12/adicionarbs.html" ,  data)
            return HttpResponseRedirect('/plan12')
        else:
            search = None
            if 's' in request.GET:
                search = request.GET['s']
            if search:
                beneficiarios = Plan12Materias.objects.filter(Q(inscripcion__persona__nombres__icontains=search) | Q(inscripcion__persona__apellido1__icontains=search) | Q(inscripcion__persona__apellido2__icontains=search) | Q(inscripcion__persona__cedula__icontains=search) | Q(inscripcion__persona__pasaporte__icontains=search)).order_by('inscripcion__persona__apellido1')
            else:
                beneficiarios = Plan12Materias.objects.all().order_by('inscripcion__persona')
            paging = Paginator(beneficiarios, 50)
            p=1
            try:
                if 'page' in request.GET:
                    p = int(request.GET['page'])
                page = paging.page(p)
            except:
                page = paging.page(1)
            data['paging'] = paging
            data['page'] = page
            data['search'] = search if search else ""
            data['beneficiarios'] = page.object_list
            return render(request ,"plan12/beneficiariosbs.html" ,  data)
