from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render
from django.template import RequestContext
from decorators import secure_module
from sga.commonviews import addUserData
from sga.models import Profesor, Periodo


@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
        data = {'title': 'Consultar y Descargar Syllabus Docentes'}
        addUserData(request,data)

        data['periodo'] = Periodo.objects.get(pk=request.session['periodo'].id)

        profesores = [x for x in Profesor.objects.filter(activo=True).order_by('persona__apellido1') if x.materias_imparte_periodo(data['periodo'])]

        if 'p' in request.GET:
            profesorid = request.GET['p']
            data['prof'] = Profesor.objects.get(pk=request.GET['p'])
            data['profid'] = int(profesorid) if profesorid else ""

        # profesores = Profesor.objects.all().order_by('persona__apellido1')
        paging = Paginator(profesores, 40)
        p=1
        try:
            if 'page' in request.GET:
                p = int(request.GET['page'])
            page = paging.page(p)
        except:
            page = paging.page(1)

        data['paging'] = paging
        data['page'] = page
        data['profesores'] = page.object_list
        data['todosprofesores'] = profesores
        return render(request ,"cons_documentos/syllabusbs.html" ,  data)
