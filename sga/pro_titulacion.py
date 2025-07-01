from django.contrib.auth.decorators import login_required
from django.forms.models import model_to_dict
from django.http import HttpResponseRedirect
from django.shortcuts import render
from decorators import secure_module
from sga.commonviews import addUserData
from sga.forms import TitulacionProfesorForm, CargarCVForm
from sga.models import Profesor, TitulacionProfesor, CVPersona



@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    if request.method=='POST':
        action = request.POST['action']
        if action=='addtitulacion':
            profesor = Profesor.objects.get(pk=request.POST['id'])
            f = TitulacionProfesorForm(request.POST)
            if f.is_valid():
                profesortitulacion = TitulacionProfesor(profesor=profesor,
                                                        titulo=f.cleaned_data['titulo'],
                                                        nivel=f.cleaned_data['nivel'],
                                                        pais=f.cleaned_data['pais'],
                                                        institucion=f.cleaned_data['institucion'],
                                                        fecha=f.cleaned_data['fecha'],
                                                        registro=f.cleaned_data['registro'],
                                                        codigoprofesional=f.cleaned_data['codigoprofesional'],
                                                        subarea=f.cleaned_data['subarea'])
                profesortitulacion.save()

                return HttpResponseRedirect("/pro_titulacion?action=titulacion&id="+str(profesor.id))
            else:
                return HttpResponseRedirect("/pro_titulacion?action=addtitulacion&id="+str(profesor.id))
        elif action=='edittitulacion':
            titulacion=TitulacionProfesor.objects.get(pk=request.POST['id'])
            f = TitulacionProfesorForm(request.POST)
            if f.is_valid():
                titulacion.titulo = f.cleaned_data['titulo']
                titulacion.nivel = f.cleaned_data['nivel']
                titulacion.pais = f.cleaned_data['pais']
                titulacion.fecha = f.cleaned_data['fecha']
                titulacion.institucion = f.cleaned_data['institucion']
                titulacion.registro = f.cleaned_data['registro']
                titulacion.codigoprofesional = f.cleaned_data['codigoprofesional']
                titulacion.subarea=f.cleaned_data['subarea']
                titulacion.save()
                return HttpResponseRedirect("/pro_titulacion?action=titulacion&id="+str(titulacion.profesor_id))
            else:
                return HttpResponseRedirect("/pro_titulacion?action=edittitulacion&id="+str(request.POST['id']))
        elif action=='deltitulacion':
            titulacion = TitulacionProfesor.objects.get(pk=request.POST['id'])
            profesor = titulacion.profesor
            titulacion.delete()
            return HttpResponseRedirect("/pro_titulacion?action=titulacion&id="+str(profesor.id))
        elif action == 'cargarcv':
            profesor = Profesor.objects.get(pk=request.POST['id'])
            form = CargarCVForm(profesor, request.FILES)
            if form.is_valid():
                persona = profesor.persona
                cv = persona.cv()
                if cv!=None:
                    cv.cv = request.FILES['cv']
                else:
                    cv = CVPersona(persona=persona, cv=request.FILES['cv'])

                cv.save()

        return HttpResponseRedirect("/pro_titulacion")
    else:
        data = {'title': 'Listado de Titulos del Profesor'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='addtitulacion':
                data['title'] = 'Adicionar Titulacion del Docente'
                profesor = Profesor.objects.get(pk=request.GET['id'])
                data['profesor'] = profesor
                form = TitulacionProfesorForm()
                data['form'] = form
                return render(request ,"pro_titulacion/adicionartitulacionbs.html" ,  data)
            elif action=='edittitulacion':
                data['title'] = 'Editar Titulacion del Docente'
                titulacion = TitulacionProfesor.objects.get(pk=request.GET['id'])
                data['profesor'] = titulacion.profesor
                initial = model_to_dict(titulacion)
                form = TitulacionProfesorForm(initial=initial)
                data['form'] = form
                data['titulacion'] = titulacion
                return render(request ,"pro_titulacion/editartitulacionbs.html" ,  data)
            elif action=='deltitulacion':
                data['title'] = 'Borrar Titulacion del Profesor'
                data['titulacion'] = TitulacionProfesor.objects.get(pk=request.GET['id'])
                data['profesor'] = data['titulacion'].profesor
                return render(request ,"pro_titulacion/borrartitulacionbs.html" ,  data)
            elif action=='cargarcv':
                data['profesor'] = Profesor.objects.get(pk=request.GET['id'])
                data['form'] = CargarCVForm()
                return render(request ,"pro_titulacion/cargarcvbs.html" ,  data)
            elif action=='borrarcv':
                profesor = Profesor.objects.get(pk=request.GET['id'])
                persona = profesor.persona
                persona.borrar_cv()
                data['profesor'] = profesor
                return HttpResponseRedirect("/pro_titulacion")

            return HttpResponseRedirect("/pro_titulacion")
        else:
            data['title'] = 'Titulos del Docente'
            profesor = Profesor.objects.get(persona=data['persona'])
            data['profesor'] = profesor
            return render(request ,"pro_titulacion/titulacionbs.html" ,  data)
