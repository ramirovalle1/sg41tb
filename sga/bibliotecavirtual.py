
from django.db.models import Q
from django.shortcuts import render
from django.template import RequestContext
from bib.models import  ConsultaBiblioteca, ReferenciaWeb, OtraBibliotecaVirtual
from sga.commonviews import addUserData
from sga.examen_conduc import MiPaginador


def view(request):
    data = {'title': 'Listado de Acceso a Bibliotecas Virtuales'}
    addUserData(request,data)

    referencias = ReferenciaWeb.objects.filter()
    otrasbibliotecas = OtraBibliotecaVirtual.objects.filter()
    biblioteca =ConsultaBiblioteca.objects.filter(Q(referenciasconsultadas__id__in = referencias)| Q( otrabibliotecaconsultadas__id__in=otrasbibliotecas))

    search  = None
    filtro  = None
    if 'filter' in request.GET:
        filtro = request.GET['filter']
        data['filtro']  = filtro

    if 's' in request.GET:
        search = request.GET['s']

    if search:
        ss = search.split(' ')
        while '' in ss:
            ss.remove('')
        if len(ss)==1:
        # try:
            biblioteca = biblioteca.filter(Q(persona__apellido1__icontains=search)| Q(persona__apellido2__icontains=search)| Q(persona__nombres__icontains=search)).order_by('-fecha','-hora','-persona__apellido1')
        else:
            biblioteca = biblioteca.filter(Q(persona__apellido1__icontains=ss[0]) & Q(persona__apellido2__icontains=ss[1])).order_by('-fecha','-hora','-persona__apellido1')
        # except Exception as e:
        #     pass
    else:
        biblioteca = biblioteca.filter().order_by('-fecha','-hora')

    paging = MiPaginador(biblioteca, 30)
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
    data['biblioteca'] = page.object_list
    if 'error' in request.GET:
        data['error']= request.GET['error']
    return render(request ,"biblioteca/bibliotecavirtual.html" ,  data)
