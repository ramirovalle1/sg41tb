from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import render
from bib.forms import PrestamoDocumentoForm
from bib.models import Documento, PrestamoDocumento
from settings import PROFESORES_GROUP_ID, ALUMNOS_GROUP_ID, ADMINISTRATIVOS_GROUP_ID
from sga.commonviews import addUserData
from sga.inscripciones import MiPaginador
from sga.models import Persona


@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    if request.method=='POST':
        action = request.POST['action']
        if action=='addprestamo':
            documento = Documento.objects.get(pk=request.POST['id'])
            responsableentrega= request.session['persona']
            f = PrestamoDocumentoForm(request.POST)
            if f.is_valid():
                prestamo = PrestamoDocumento(documento=documento,persona=f.cleaned_data['persona'],
                                            responsableentrega=responsableentrega,
                                            fechaentrega=datetime.today(), horaentrega=datetime.now().time(),
                                            entregado=f.cleaned_data['entregado'], recibido=False)
                prestamo.save()

                return HttpResponseRedirect("/prestamos")

        return HttpResponseRedirect("/documentos")

    else:
        data = {'title': 'Gestion de Biblioteca'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='recibir':
                prestamo = PrestamoDocumento.objects.get(pk=request.GET['id'])
                prestamo.responsablerecibido = request.session['persona']
                prestamo.recibido = True
                prestamo.fecharecibido = datetime.today()
                prestamo.horarecibido = datetime.now().time()
                prestamo.save()

                return HttpResponseRedirect("/prestamos")
            elif action == 'estadistica' :
                # LISTA DE MEJORES DOCENTES INVESTIGADORES
                listadocente=[]
                listaalumno=[]

                docente = [listadocente.append((x.prestamo_persona(),x.nombre_completo())) for x in Persona.objects.filter(usuario__groups__id=PROFESORES_GROUP_ID,usuario__is_active=True) if x.prestamo_persona()>0]
                listadocente.sort()
                listadocente.reverse()

                # LISTA DE MEJORES ALUMNOS INVESTIGADORES
                alumno = [listaalumno.append((x.prestamo_persona(),x.nombre_completo())) for x in
                          Persona.objects.filter(usuario__groups__id=ALUMNOS_GROUP_ID , usuario__is_active=True) if x.prestamo_persona()>3]
                listaalumno.sort()
                listaalumno.reverse()
                data['lista_docente'] = listadocente[:10]
                data['lista_alumno'] = listaalumno[:10]
                return render(request ,"biblioteca/estadisticaprestamos.html" ,  data)
        else:
            search = None
            todos = None
            pendientes = None

            if 's' in request.GET:
                search = request.GET['s']
            if 't' in request.GET:
                todos = request.GET['t']
            if 'p' in request.GET:
                pendientes = request.GET['p']
            if search:
                # prestamos = PrestamoDocumento.objects.filter(documento__codigo=search).order_by('fechaentrega')
                prestamos = PrestamoDocumento.objects.filter(Q(documento__codigo__icontains=search)| Q(documento__nombre__icontains=search) | Q(persona__nombres__icontains=search) | Q(persona__apellido1__icontains=search) | Q(persona__apellido2__icontains=search) ).order_by('fechaentrega')
            elif pendientes:
                prestamos = PrestamoDocumento.objects.filter(recibido=False).order_by('fechaentrega')
            else:
                prestamos = PrestamoDocumento.objects.all().order_by('-fechaentrega')

            paging = MiPaginador(prestamos, 30)
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
            data['pendientes'] = pendientes if pendientes else ""
            data['prestamos'] = page.object_list
            data['persona'] = request.session['persona']
            return render(request ,"biblioteca/prestamos.html" ,  data)
