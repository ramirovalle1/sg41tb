from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.core.paginator import Paginator
from django.db.models.query_utils import Q
from django.forms.models import model_to_dict
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from med.forms import PersonaExtensionForm, PersonaPatologicoForm, PersonaGinecologicoForm, PersonaHabitoForm, PersonaPatologicoFamiliarForm, \
    PersonaFamiliaForm,PersonaRayosxForm, PersonaExamenesLabForm
from med.models import PersonaExamenFisico, PersonaExtension, PersonaFichaMedica,PersonaValoracionImagen, PersonaExamenesLab
from settings import DEFAULT_PASSWORD, PROFESORES_GROUP_ID, ALUMNOS_GROUP_ID
from sga.commonviews import addUserData
from sga.forms import PersonaForm, InscripcionForm, RecordAcademicoForm, HistoricoRecordAcademicoForm, GraduadoForm, EgresadoForm, PerfilInscripcionForm, DobeInscripcionForm
from sga.models import Profesor, Persona, Inscripcion, RecordAcademico, DocumentosDeInscripcion, HistoricoRecordAcademico, Graduado, Egresado, PerfilInscripcion, InscripcionGrupo


@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    if request.method=='POST':
        action = request.POST['action']
        if action=='datosextension':
           persona = Persona.objects.get(pk=request.POST['id'])
           pexamenfisico = PersonaExamenFisico.objects.get(personafichamedica__personaextension__persona=persona)
           f = PersonaExtensionForm(request.POST)
           if f.is_valid():
                pexamenfisico.personafichamedica.personaextension.estadocivil = f.cleaned_data['estadocivil']
                pexamenfisico.personafichamedica.personaextension.tienelicencia = f.cleaned_data['tienelicencia']
                pexamenfisico.personafichamedica.personaextension.tipolicencia = f.cleaned_data['tipolicencia']
                pexamenfisico.personafichamedica.personaextension.telefonos = f.cleaned_data['telefonos']
                pexamenfisico.personafichamedica.personaextension.tieneconyuge = f.cleaned_data['tieneconyuge']
                pexamenfisico.personafichamedica.personaextension.hijos = f.cleaned_data['hijos']

                pexamenfisico.personafichamedica.personaextension.save()
                if 'ban' in request.POST:
                    if request.POST['ban'] == '1' :
                        return HttpResponseRedirect("/per_medical?action=verficha&id="+str(persona.id))
                return HttpResponseRedirect("/per_medical")

           else:
               return HttpResponseRedirect("/per_medical?action=datos&id="+str(persona.id))

        elif action=='patologicop':
            persona = Persona.objects.get(pk=request.POST['id'])
            pexamenfisico = PersonaExamenFisico.objects.get(personafichamedica__personaextension__persona=persona)
            f = PersonaPatologicoForm(request.POST)
            if f.is_valid():
                pexamenfisico.personafichamedica.vacunas = f.cleaned_data['vacunas']
                pexamenfisico.personafichamedica.nombrevacunas = f.cleaned_data['nombrevacunas']
                pexamenfisico.personafichamedica.enfermedades = f.cleaned_data['enfermedades']
                pexamenfisico.personafichamedica.nombreenfermedades = f.cleaned_data['nombreenfermedades']
                pexamenfisico.personafichamedica.alergiamedicina = f.cleaned_data['alergiamedicina']
                pexamenfisico.personafichamedica.nombremedicinas = f.cleaned_data['nombremedicinas']
                pexamenfisico.personafichamedica.alergiaalimento = f.cleaned_data['alergiaalimento']
                pexamenfisico.personafichamedica.nombrealimentos = f.cleaned_data['nombrealimentos']
                pexamenfisico.personafichamedica.cirugias = f.cleaned_data['cirugias']
                pexamenfisico.personafichamedica.nombrecirugia = f.cleaned_data['nombrecirugia']
                pexamenfisico.personafichamedica.fechacirugia = f.cleaned_data['fechacirugia']
                pexamenfisico.personafichamedica.aparato = f.cleaned_data['aparato']
                pexamenfisico.personafichamedica.tipoaparato = f.cleaned_data['tipoaparato']

                pexamenfisico.personafichamedica.save()
                if 'ban' in request.POST:
                    if request.POST['ban'] == '1' :
                        return HttpResponseRedirect("/per_medical?action=verficha&id="+str(persona.id))
                return HttpResponseRedirect("/per_medical")
            else:
                return HttpResponseRedirect("/per_medical?action=patologicop&id="+str(persona.id))

        elif action=='habitos':
            persona = Persona.objects.get(pk=request.POST['id'])
            pexamenfisico = PersonaExamenFisico.objects.get(personafichamedica__personaextension__persona=persona)
            f = PersonaHabitoForm(request.POST)
            if f.is_valid():
                pexamenfisico.personafichamedica.cigarro = f.cleaned_data['cigarro']
                pexamenfisico.personafichamedica.numerocigarros = f.cleaned_data['numerocigarros']
                pexamenfisico.personafichamedica.tomaalcohol = f.cleaned_data['tomaalcohol']
                pexamenfisico.personafichamedica.tipoalcohol = f.cleaned_data['tipoalcohol']
                pexamenfisico.personafichamedica.copasalcohol = f.cleaned_data['copasalcohol']
                pexamenfisico.personafichamedica.tomaantidepresivos = f.cleaned_data['tomaantidepresivos']
                pexamenfisico.personafichamedica.antidepresivos = f.cleaned_data['antidepresivos']
                pexamenfisico.personafichamedica.tomaotros = f.cleaned_data['tomaotros']
                pexamenfisico.personafichamedica.otros = f.cleaned_data['otros']
                pexamenfisico.personafichamedica.horassueno = f.cleaned_data['horassueno']
                pexamenfisico.personafichamedica.calidadsuenno = f.cleaned_data['calidadsuenno']

                pexamenfisico.personafichamedica.save()

                if 'ban' in request.POST:
                    if request.POST['ban'] == '1' :
                        return HttpResponseRedirect("/per_medical?action=verficha&id="+str(persona.id))
                return HttpResponseRedirect("/per_medical")
            else:
                return HttpResponseRedirect("/per_medical?action=habitos&id="+str(persona.id))

        elif action=='ginecologico':
            persona = Persona.objects.get(pk=request.POST['id'])
            pexamenfisico = PersonaExamenFisico.objects.get(personafichamedica__personaextension__persona=persona)
            f = PersonaGinecologicoForm(request.POST)
            if f.is_valid():
                pexamenfisico.personafichamedica.gestacion = f.cleaned_data['gestacion']
                pexamenfisico.personafichamedica.partos = f.cleaned_data['partos']
                pexamenfisico.personafichamedica.abortos = f.cleaned_data['abortos']
                pexamenfisico.personafichamedica.cesareas = f.cleaned_data['cesareas']
                pexamenfisico.personafichamedica.hijos2 = f.cleaned_data['hijos2']

                pexamenfisico.personafichamedica.save()
                if 'ban' in request.POST:
                    if request.POST['ban'] == '1' :
                        return HttpResponseRedirect("/per_medical?action=verficha&id="+str(persona.id))
                return HttpResponseRedirect("/per_medical")
            else:
                return HttpResponseRedirect("/per_medical?action=ginecologico&id="+str(persona.id))

        elif action=='patologicof':
            persona = Persona.objects.get(pk=request.POST['id'])
            pexamenfisico = PersonaExamenFisico.objects.get(personafichamedica__personaextension__persona=persona)
            f = PersonaPatologicoFamiliarForm(request.POST)
            if f.is_valid():
                pexamenfisico.personafichamedica.personaextension.enfermedadpadre = f.cleaned_data['enfermedadpadre']
                pexamenfisico.personafichamedica.personaextension.enfermedadmadre = f.cleaned_data['enfermedadmadre']
                pexamenfisico.personafichamedica.personaextension.enfermedadabuelos = f.cleaned_data['enfermedadabuelos']
                pexamenfisico.personafichamedica.personaextension.enfermedadhermanos = f.cleaned_data['enfermedadhermanos']
                pexamenfisico.personafichamedica.personaextension.enfermedadotros = f.cleaned_data['enfermedadotros']

                pexamenfisico.personafichamedica.personaextension.save()
                if 'ban' in request.POST:
                    if request.POST['ban'] == '1' :
                        return HttpResponseRedirect("/per_medical?action=verficha&id="+str(persona.id))
                return HttpResponseRedirect("/per_medical")
            else:
                return HttpResponseRedirect("/per_medical?action=patologicof&id="+str(persona.id))


        elif action=='rayosx':
            persona = Persona.objects.get(pk=request.POST['idper'])
            f = PersonaRayosxForm(request.POST,request.FILES)
            if f.is_valid():
                obs=f.cleaned_data['observaciones'].upper()
                valoracionimagen=PersonaValoracionImagen(persona=persona,
                                                         observaciones=obs,
                                                         fecha = datetime.now(),
                                                         user=request.user)

                valoracionimagen.save()

                if 'diagnostico' in request.FILES:
                    valoracionimagen.diagnostico= request.FILES['diagnostico']
                    valoracionimagen.save()

                if 'imagen' in request.FILES:
                    valoracionimagen.imagen= request.FILES['imagen']
                    valoracionimagen.save()

                return HttpResponseRedirect("/per_medical?action=verficha&id="+str(persona.id))
            else:
                return HttpResponseRedirect("/per_medical?action=rayosx&id="+str(persona.id))

        elif action=='examenlab':
            persona = Persona.objects.get(pk=request.POST['idperl'])
            f = PersonaExamenesLabForm(request.POST,request.FILES)
            if f.is_valid():
                obs=f.cleaned_data['observaciones'].upper()
                examenlab=PersonaExamenesLab(persona=persona,
                                             observaciones=obs,
                                             fecha = datetime.now(),
                                             user=request.user)
                examenlab.save()

                if 'resultadoslab' in request.FILES:
                    examenlab.resultadoslab= request.FILES['resultadoslab']
                    examenlab.save()

                return HttpResponseRedirect("/per_medical?action=verficha&id="+str(persona.id))
            else:
                return HttpResponseRedirect("/per_medical?action=examenlab&id="+str(persona.id))

        elif action=='familia':
            persona = Persona.objects.get(pk=request.POST['id'])
            pexamenfisico = PersonaExamenFisico.objects.get(personafichamedica__personaextension__persona=persona)
            f = PersonaFamiliaForm(request.POST)
            if f.is_valid():
                pexamenfisico.personafichamedica.personaextension.padre = f.cleaned_data['padre']
                pexamenfisico.personafichamedica.personaextension.edadpadre = f.cleaned_data['edadpadre']
                pexamenfisico.personafichamedica.personaextension.estadopadre = f.cleaned_data['estadopadre']
                pexamenfisico.personafichamedica.personaextension.telefpadre = f.cleaned_data['telefpadre']
                pexamenfisico.personafichamedica.personaextension.educacionpadre = f.cleaned_data['educacionpadre']
                pexamenfisico.personafichamedica.personaextension.profesionpadre = f.cleaned_data['profesionpadre']
                pexamenfisico.personafichamedica.personaextension.trabajopadre = f.cleaned_data['trabajopadre']

                pexamenfisico.personafichamedica.personaextension.madre = f.cleaned_data['madre']
                pexamenfisico.personafichamedica.personaextension.edadmadre = f.cleaned_data['edadmadre']
                pexamenfisico.personafichamedica.personaextension.estadomadre = f.cleaned_data['estadomadre']
                pexamenfisico.personafichamedica.personaextension.telefmadre = f.cleaned_data['telefmadre']
                pexamenfisico.personafichamedica.personaextension.educacionmadre = f.cleaned_data['educacionmadre']
                pexamenfisico.personafichamedica.personaextension.profesionmadre = f.cleaned_data['profesionmadre']
                pexamenfisico.personafichamedica.personaextension.trabajomadre = f.cleaned_data['trabajomadre']

                pexamenfisico.personafichamedica.personaextension.conyuge = f.cleaned_data['conyuge']
                pexamenfisico.personafichamedica.personaextension.edadconyuge = f.cleaned_data['edadconyuge']
                pexamenfisico.personafichamedica.personaextension.estadoconyuge = f.cleaned_data['estadoconyuge']
                pexamenfisico.personafichamedica.personaextension.telefconyuge = f.cleaned_data['telefconyuge']
                pexamenfisico.personafichamedica.personaextension.educacionconyuge = f.cleaned_data['educacionconyuge']
                pexamenfisico.personafichamedica.personaextension.profesionconyuge = f.cleaned_data['profesionconyuge']
                pexamenfisico.personafichamedica.personaextension.trabajoconyuge = f.cleaned_data['trabajoconyuge']

                pexamenfisico.personafichamedica.personaextension.save()
                if 'ban' in request.POST:
                    if request.POST['ban'] == '1' :
                        return HttpResponseRedirect("/per_medical?action=verficha&id="+str(persona.id))
                return HttpResponseRedirect("/per_medical")
            else:
                return HttpResponseRedirect("/per_medical?action=familia&id="+str(persona.id))

    else:
        data = {'title': 'Ficha Medica Personal'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            persona = Persona.objects.get(pk=request.GET['id'])
            data['persona'] = persona
            if PersonaExamenFisico.objects.filter(personafichamedica__personaextension__persona = persona).exists():
                pex = PersonaExamenFisico.objects.get(personafichamedica__personaextension__persona = persona)

            if PersonaValoracionImagen.objects.filter(persona=persona).exists():
                pvi=PersonaValoracionImagen.objects.filter(persona=persona)

            if PersonaExamenesLab.objects.filter(persona=persona).exists():
               pel=PersonaExamenesLab.objects.filter(persona=persona)

            if action=='datos':
                data['title'] = 'Datos Adicionales Personales'
                initial = model_to_dict(pex.personafichamedica.personaextension)
                data['form'] = PersonaExtensionForm(initial=initial)
                if 'ban' in request.GET:
                    data['ban'] = request.GET['ban']
                return render(request ,"per_medical/datosextension.html" ,  data)

            elif action=='familia':
                data['title'] = 'Datos Familiares'
                initial = model_to_dict(pex.personafichamedica.personaextension)
                form = PersonaFamiliaForm(initial=initial)
                data['form'] = form
                if 'ban' in request.GET:
                    data['ban'] = request.GET['ban']
                return render(request ,"per_medical/familia.html" ,  data)
            elif action=='eliminaexamlab':
                examenlab=PersonaExamenesLab.objects.get(pk=request.GET['id'])
                personalab=examenlab.persona
                examenlab.delete()
                return HttpResponseRedirect("per_medical?action=verficha&id="+str(personalab.id))
            elif action=='eliminarayos':
                rayosx=PersonaValoracionImagen.objects.get(pk=request.GET['id'])
                personax=rayosx.persona
                rayosx.delete()
                return HttpResponseRedirect("per_medical?action=verficha&id="+str(personax.id))
            elif action=='patologicop':
                data['title'] = 'Antecedentes Patologicos'
                initial = model_to_dict(pex.personafichamedica)
                form = PersonaPatologicoForm(initial=initial)
                data['form'] = form
                if 'ban' in request.GET:
                    data['ban'] = request.GET['ban']
                return render(request ,"per_medical/patologicop.html" ,  data)
            elif action=='ginecologico':
                data['title'] = 'Antecedentes Ginecologicos'
                initial = model_to_dict(pex.personafichamedica)
                data['form'] = PersonaGinecologicoForm(initial=initial)
                if 'ban' in request.GET:
                    data['ban'] = request.GET['ban']
                return render(request ,"per_medical/ginecologico.html" ,  data)
            elif action=='habitos':
                data['title'] = 'Habitos Personales'
                initial = model_to_dict(pex.personafichamedica)
                data['form'] = PersonaHabitoForm(initial=initial)
                if 'ban' in request.GET:
                    data['ban'] = request.GET['ban']
                return render(request ,"per_medical/habitos.html" ,  data)

            elif action=='patologicof':
                data['title'] = 'Antecedentes Patologicos de familiares'
                initial = model_to_dict(pex.personafichamedica.personaextension)
                data['form'] = PersonaPatologicoFamiliarForm(initial=initial)
                if 'ban' in request.GET:
                    data['ban'] = request.GET['ban']
                return render(request ,"per_medical/patologicof.html" ,  data)

            elif action == 'verficha':
                persona = Persona.objects.get(pk=request.GET['id'])
                data['persona'] = persona
                persona2=Persona.objects.get(usuario=request.user)
                data['persona2'] = persona2
                if PersonaExamenFisico.objects.filter(personafichamedica__personaextension__persona=data['persona']).exists():
                    pexamenfisico = PersonaExamenFisico.objects.filter(personafichamedica__personaextension__persona=data['persona'])[:1].get()
                else:
                    pext = PersonaExtension(persona=data['persona'])
                    pext.save()
                    pfichamedica = PersonaFichaMedica(personaextension=pext)
                    pfichamedica.save()
                    pexamenfisico = PersonaExamenFisico(personafichamedica=pfichamedica)
                    pexamenfisico.save()

                if PersonaValoracionImagen.objects.filter(persona=data['persona']).exists():
                    pvaloracionimagen=PersonaValoracionImagen.objects.filter(persona=data['persona'])
                    data['registros']=pvaloracionimagen

                if PersonaExamenesLab.objects.filter(persona=data['persona']).exists():
                    pexamenlab=PersonaExamenesLab.objects.filter(persona=data['persona'])
                    data['regexamlab']=pexamenlab

                data['pex'] = pexamenfisico
                data['ban'] = 1
                return render(request ,"per_medical/datos.html" ,  data)

        else:
            data['persona'] = request.session['persona']
            if PersonaExamenFisico.objects.filter(personafichamedica__personaextension__persona=data['persona']).exists():
                pexamenfisico = PersonaExamenFisico.objects.filter(personafichamedica__personaextension__persona=data['persona'])[:1].get()
            else:
                pext = PersonaExtension(persona=data['persona'])
                pext.save()
                pfichamedica = PersonaFichaMedica(personaextension=pext)
                pfichamedica.save()
                pexamenfisico = PersonaExamenFisico(personafichamedica=pfichamedica)
                pexamenfisico.save()

            if PersonaValoracionImagen.objects.filter(persona=data['persona']).exists():
                pvaloracionimagen=PersonaValoracionImagen.objects.filter(persona=data['persona'])
                data['registros']=pvaloracionimagen

            if PersonaExamenesLab.objects.filter(persona=data['persona']).exists():
                pexamenlab=PersonaExamenesLab.objects.filter(persona=data['persona'])
                data['regexamlab']=pexamenlab

            data['pex'] = pexamenfisico
            data['ban'] = 2
            data['ingresoform']=PersonaRayosxForm()
            data['ingresolab'] =PersonaExamenesLabForm()

            return render(request ,"per_medical/datos.html" ,  data)
