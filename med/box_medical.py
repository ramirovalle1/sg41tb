from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.core.paginator import Paginator
from django.db.models.query_utils import Q
from django.forms.models import model_to_dict
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render
from med.forms import PersonaExtensionForm, PersonaPatologicoForm, PersonaGinecologicoForm, PersonaHabitoForm, PersonaPatologicoFamiliarForm, PersonaFamiliaForm, PersonaExamenFisicoForm, PersonaRayosxForm, PersonaExamenesLabForm
from med.models import PersonaExamenFisico, PersonaExtension, PersonaFichaMedica, PersonaValoracionImagen, PersonaExamenesLab
from settings import DEFAULT_PASSWORD, PROFESORES_GROUP_ID, ALUMNOS_GROUP_ID, UTILIZA_GRUPOS_ALUMNOS
from sga.commonviews import addUserData
from sga.forms import PersonaForm, InscripcionForm, RecordAcademicoForm, HistoricoRecordAcademicoForm, GraduadoForm, EgresadoForm, PerfilInscripcionForm, DobeInscripcionForm
from sga.inscripciones import MiPaginador
from sga.models import Profesor, Persona, Inscripcion, RecordAcademico, DocumentosDeInscripcion, HistoricoRecordAcademico, Graduado, Egresado, PerfilInscripcion, InscripcionGrupo


@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    if request.method=='POST':
        action = request.POST['action']
        try:
            if action=='datosextension':
                pexamenfisico = PersonaExamenFisico.objects.get(pk=request.POST['id'])
                inscripcion = Inscripcion.objects.get(pk=request.POST['ins'])
                f = PersonaExtensionForm(request.POST)
                if f.is_valid():
                    pexamenfisico.personafichamedica.personaextension.estadocivil = f.cleaned_data['estadocivil']
                    pexamenfisico.personafichamedica.personaextension.tienelicencia = f.cleaned_data['tienelicencia']
                    pexamenfisico.personafichamedica.personaextension.tipolicencia = f.cleaned_data['tipolicencia']
                    pexamenfisico.personafichamedica.personaextension.telefonos = f.cleaned_data['telefonos']
                    pexamenfisico.personafichamedica.personaextension.tieneconyuge = f.cleaned_data['tieneconyuge']
                    pexamenfisico.personafichamedica.personaextension.hijos = f.cleaned_data['hijos']

                    pexamenfisico.personafichamedica.personaextension.save()

                    return HttpResponseRedirect("/box_medical?action=ficha&id="+str(inscripcion.id))
                else:
                    return HttpResponseRedirect("/box_medical?action=datos&id="+str(pexamenfisico.id)+"&ins="+str(inscripcion.id)+"&error=1")

            elif action=='patologicop':
                pexamenfisico = PersonaExamenFisico.objects.get(pk=request.POST['id'])
                inscripcion = Inscripcion.objects.get(pk=request.POST['ins'])
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

                    return HttpResponseRedirect("/box_medical?action=ficha&id="+str(inscripcion.id))
                else:
                    return HttpResponseRedirect("/box_medical?action=patologicop&id="+str(pexamenfisico.id)+"&ins="+str(inscripcion.id)+"&error=1")

            elif action=='habitos':
                pexamenfisico = PersonaExamenFisico.objects.get(pk=request.POST['id'])
                inscripcion = Inscripcion.objects.get(pk=request.POST['ins'])
                f = PersonaHabitoForm(request.POST)
                try:
                    if f.is_valid():
                        if  f.cleaned_data['cigarro'] and f.cleaned_data['numerocigarros'] == None:
                            return HttpResponseRedirect("/box_medical?action=habitos&id="+str(pexamenfisico.id)+"&ins="+str(inscripcion.id)+"&error=1")
                        elif f.cleaned_data['tomaalcohol'] and f.cleaned_data['tipoalcohol'] and f.cleaned_data['copasalcohol'] == None:
                            return HttpResponseRedirect("/box_medical?action=habitos&id="+str(pexamenfisico.id)+"&ins="+str(inscripcion.id)+"&error=1")
                        elif f.cleaned_data['tomaantidepresivos'] and f.cleaned_data['antidepresivos'] == None:
                            return HttpResponseRedirect("/box_medical?action=habitos&id="+str(pexamenfisico.id)+"&ins="+str(inscripcion.id)+"&error=1")
                        elif f.cleaned_data['tomaotros'] and f.cleaned_data['otros'] == None:
                            return HttpResponseRedirect("/box_medical?action=habitos&id="+str(pexamenfisico.id)+"&ins="+str(inscripcion.id)+"&error=1")
                        else:
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

                            return HttpResponseRedirect("/box_medical?action=ficha&id="+str(inscripcion.id))
                    else:
                        return HttpResponseRedirect("/box_medical?action=habitos&id="+str(pexamenfisico.id)+"&ins="+str(inscripcion.id)+"&error=1")
                except:
                    return HttpResponseRedirect("/box_medical?action=habitos&id="+str(pexamenfisico.id)+"&ins="+str(inscripcion.id)+"&error=1")

            elif action=='ginecologico':
                pexamenfisico = PersonaExamenFisico.objects.get(pk=request.POST['id'])
                inscripcion = Inscripcion.objects.get(pk=request.POST['ins'])
                f = PersonaGinecologicoForm(request.POST)
                if f.is_valid():
                    pexamenfisico.personafichamedica.gestacion = f.cleaned_data['gestacion']
                    pexamenfisico.personafichamedica.partos = f.cleaned_data['partos']
                    pexamenfisico.personafichamedica.abortos = f.cleaned_data['abortos']
                    pexamenfisico.personafichamedica.cesareas = f.cleaned_data['cesareas']
                    pexamenfisico.personafichamedica.hijos2 = f.cleaned_data['hijos2']

                    pexamenfisico.personafichamedica.save()

                    return HttpResponseRedirect("/box_medical?action=ficha&id="+str(inscripcion.id))
                else:
                    return HttpResponseRedirect("/box_medical?action=ginecologico&id="+str(pexamenfisico.id)+"&ins="+str(inscripcion.id)+"&error=1")

            elif action=='patologicof':
                pexamenfisico = PersonaExamenFisico.objects.get(pk=request.POST['id'])
                inscripcion = Inscripcion.objects.get(pk=request.POST['ins'])
                f = PersonaPatologicoFamiliarForm(request.POST)
                if f.is_valid():
                    pexamenfisico.personafichamedica.personaextension.enfermedadpadre = f.cleaned_data['enfermedadpadre']
                    pexamenfisico.personafichamedica.personaextension.enfermedadmadre = f.cleaned_data['enfermedadmadre']
                    pexamenfisico.personafichamedica.personaextension.enfermedadabuelos = f.cleaned_data['enfermedadabuelos']
                    pexamenfisico.personafichamedica.personaextension.enfermedadhermanos = f.cleaned_data['enfermedadhermanos']
                    pexamenfisico.personafichamedica.personaextension.enfermedadotros = f.cleaned_data['enfermedadotros']

                    pexamenfisico.personafichamedica.personaextension.save()

                    return HttpResponseRedirect("/box_medical?action=ficha&id="+str(inscripcion.id))
                else:
                    return HttpResponseRedirect("/box_medical?action=patologicof&id="+str(pexamenfisico.id)+"&ins="+str(inscripcion.id)+"&error=1")

            elif action=='rayosx':
                inscripcion = Inscripcion.objects.get(pk=request.POST['idins'])
                persona = inscripcion.persona
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

                    return HttpResponseRedirect("/box_medical?action=ficha&id="+str(inscripcion.id))
                else:
                    return HttpResponseRedirect("/box_medical?action=rayosx&id="+str(persona.id))


            elif action=='examenlab':
                inscripcion = Inscripcion.objects.get(pk=request.POST['idins2'])
                persona = inscripcion.persona
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

                    return HttpResponseRedirect("/box_medical?action=ficha&id="+str(inscripcion.id))
                else:
                    return HttpResponseRedirect("/box_medical?action=examenlab&id="+str(persona.id))

            elif action=='familia':
                pexamenfisico = PersonaExamenFisico.objects.get(pk=request.POST['id'])
                inscripcion = Inscripcion.objects.get(pk=request.POST['ins'])
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

                    return HttpResponseRedirect("/box_medical?action=ficha&id="+str(inscripcion.id))
                else:
                    # return HttpResponseRedirect("/box_medical?action=familia&id="+str(pexamenfisico.id))
                    return HttpResponseRedirect("/box_medical?action=familia&id="+str(pexamenfisico.id)+"&ins="+str(inscripcion.id)+"&error=1")

            elif action=='editar':
                pexamenfisico = PersonaExamenFisico.objects.get(pk=request.POST['id'])
                inscripcion = Inscripcion.objects.get(pk=request.POST['ins'])
                f = PersonaExamenFisicoForm(request.POST)
                if f.is_valid():
                    pexamenfisico.inspeccion = f.cleaned_data['inspeccion']
                    pexamenfisico.usalentes = f.cleaned_data['usalentes']
                    pexamenfisico.motivo = f.cleaned_data['motivo']

                    # Signos Vitales
                    pexamenfisico.peso = f.cleaned_data['peso']
                    pexamenfisico.talla = f.cleaned_data['talla']
                    pexamenfisico.pa = f.cleaned_data['pa']
                    pexamenfisico.pulso = f.cleaned_data['pulso']
                    pexamenfisico.rcar = f.cleaned_data['rcar']
                    pexamenfisico.rresp = f.cleaned_data['rresp']
                    pexamenfisico.temp = f.cleaned_data['temp']

                    pexamenfisico.observaciones = f.cleaned_data['observaciones']

                    pexamenfisico.save()
                    return HttpResponseRedirect("/box_medical?action=valoracion&id="+str(inscripcion.id))
                else:
                    return HttpResponseRedirect("/box_medical?action=editar&id="+str(pexamenfisico.id)+"&ins="+str(inscripcion.id))

            elif action=='editarpersonal':
                pexamenfisico = PersonaExamenFisico.objects.get(pk=request.POST['id'])
                persona = Persona.objects.get(pk=request.POST['per'])
                f = PersonaExamenFisicoForm(request.POST)
                if f.is_valid():
                    pexamenfisico.inspeccion = f.cleaned_data['inspeccion']
                    pexamenfisico.usalentes = f.cleaned_data['usalentes']
                    pexamenfisico.motivo = f.cleaned_data['motivo']

                    # Signos Vitales
                    pexamenfisico.peso = f.cleaned_data['peso']
                    pexamenfisico.talla = f.cleaned_data['talla']
                    pexamenfisico.pa = f.cleaned_data['pa']
                    pexamenfisico.pulso = f.cleaned_data['pulso']
                    pexamenfisico.rcar = f.cleaned_data['rcar']
                    pexamenfisico.rresp = f.cleaned_data['rresp']
                    pexamenfisico.temp = f.cleaned_data['temp']

                    pexamenfisico.observaciones = f.cleaned_data['observaciones']

                    pexamenfisico.save()
                    return HttpResponseRedirect("/box_medical?action=valoracionpersona&id="+str(persona.id))
                else:
                    return HttpResponseRedirect("/box_medical?action=editarpersonal&id="+str(pexamenfisico.id)+"&ins="+str(persona.id))
        except:
            HttpResponseRedirect("/box_medical")

    else:
        try:
            data = {'title': 'Ficha Medica de Alumnos'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']
                if action=='ficha':
                    data['title'] = 'Ver Ficha Medica del Estudiante'
                    inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                    persona = inscripcion.persona
                    if PersonaExamenFisico.objects.filter(personafichamedica__personaextension__persona=persona).exists():
                        pexamenfisico = PersonaExamenFisico.objects.filter(personafichamedica__personaextension__persona=persona)[:1].get()
                    else:
                        pext = PersonaExtension(persona=persona)
                        pext.save()
                        pfichamedica = PersonaFichaMedica(personaextension=pext)
                        pfichamedica.save()
                        pexamenfisico = PersonaExamenFisico(personafichamedica=pfichamedica)
                        pexamenfisico.save()

                    if PersonaValoracionImagen.objects.filter(persona=persona).exists():
                        pvaloracionimagen=PersonaValoracionImagen.objects.filter(persona=persona)
                        data['registros']= pvaloracionimagen

                    if PersonaExamenesLab.objects.filter(persona=persona).exists():
                        pexamenlab=PersonaExamenesLab.objects.filter(persona=persona)
                        data['regexamlab']=pexamenlab

                    data['pex'] = pexamenfisico
                    data['inscripcion'] = inscripcion
                    data['ingresoform']= PersonaRayosxForm()
                    data['ingresolab'] = PersonaExamenesLabForm()

                    return render(request ,"box_medical/datosbs.html" ,  data)

                elif action=='datos':
                    data['title'] = 'Datos Adicionales del Estudiante'
                    if 'error' in request.GET:
                        data['error'] = request.GET['error']
                    pex = PersonaExamenFisico.objects.get(pk=request.GET['id'])
                    inscripcion = Inscripcion.objects.get(pk=request.GET['ins'])
                    initial = model_to_dict(pex.personafichamedica.personaextension)
                    ext=PersonaExtensionForm(initial=initial)
                    data['form'] = PersonaExtensionForm(initial=initial)
                    data['pex'] = pex
                    data['inscripcion'] = inscripcion
                    return render(request ,"box_medical/datosextension.html" ,  data)
                elif action=='familia':
                    data['title'] = 'Datos Familiares'
                    if 'error' in request.GET:
                        data['error'] = request.GET['error']
                    pex = PersonaExamenFisico.objects.get(pk=request.GET['id'])
                    try:
                        inscripcion = Inscripcion.objects.get(pk=request.GET['ins'])
                        initial = model_to_dict(pex.personafichamedica.personaextension)
                        form = PersonaFamiliaForm(initial=initial)
                        data['form'] = form
                        data['pex'] = pex
                        data['inscripcion'] = inscripcion
                        # aqui 1
                        return render(request ,"box_medical/familiabs.html" ,  data)
                    except Exception as ex:
                        # return HttpResponseRedirect("/box_medical?action=familia&id="+str(pex.id))
                        return render(request ,"box_medical/familiabs.html" ,  data)
                elif action=='patologicop':
                    data['title'] = 'Antecedentes Patologicos del Estudiante'
                    if 'error' in request.GET:
                        data['error'] = request.GET['error']
                    pex = PersonaExamenFisico.objects.get(pk=request.GET['id'])
                    inscripcion = Inscripcion.objects.get(pk=request.GET['ins'])
                    initial = model_to_dict(pex.personafichamedica)
                    form = PersonaPatologicoForm(initial=initial)
                    data['form'] = form
                    data['pex'] = pex
                    data['inscripcion'] = inscripcion
                    return render(request ,"box_medical/patologicopbs.html" ,  data)
                elif action=='ginecologico':
                    data['title'] = 'Antecedentes Ginecologicos del Alumno'
                    if 'error' in request.GET:
                        data['error'] = request.GET['error']
                    pex = PersonaExamenFisico.objects.get(pk=request.GET['id'])
                    inscripcion = Inscripcion.objects.get(pk=request.GET['ins'])
                    initial = model_to_dict(pex.personafichamedica)
                    data['form'] = PersonaGinecologicoForm(initial=initial)
                    data['pex'] = pex
                    data['inscripcion'] = inscripcion
                    return render(request ,"box_medical/ginecologicobs.html" ,  data)
                elif action=='habitos':
                    data['title'] = 'Habitos del Alumno'
                    if 'error' in request.GET:
                        data['error'] = request.GET['error']
                    pex = PersonaExamenFisico.objects.get(pk=request.GET['id'])
                    inscripcion = Inscripcion.objects.get(pk=request.GET['ins'])
                    initial = model_to_dict(pex.personafichamedica)
                    data['form'] = PersonaHabitoForm(initial=initial)
                    data['pex'] = pex
                    data['inscripcion'] = inscripcion
                    return render(request ,"box_medical/habitosbs.html" ,  data)
                elif action=='patologicof':
                    data['title'] = 'Antecedentes Patologicos de familiares'
                    pex = PersonaExamenFisico.objects.get(pk=request.GET['id'])
                    inscripcion = Inscripcion.objects.get(pk=request.GET['ins'])
                    initial = model_to_dict(pex.personafichamedica.personaextension)
                    data['form'] = PersonaPatologicoFamiliarForm(initial=initial)
                    data['pex'] = pex
                    data['inscripcion'] = inscripcion
                    return render(request ,"box_medical/patologicofbs.html" ,  data)

                elif action=='valoracion':
                    data['title'] = 'Valoracion Medica del Estudiante'
                    inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                    persona = inscripcion.persona
                    if PersonaExamenFisico.objects.filter(personafichamedica__personaextension__persona=persona).exists():
                        pexamenfisico = PersonaExamenFisico.objects.filter(personafichamedica__personaextension__persona=persona)[:1].get()
                    else:
                        pext = PersonaExtension(persona=persona)
                        pext.save()
                        pfichamedica = PersonaFichaMedica(personaextension=pext)
                        pfichamedica.save()
                        pexamenfisico = PersonaExamenFisico(personafichamedica=pfichamedica)
                        pexamenfisico.save()

                    data['pex'] = pexamenfisico
                    data['inscripcion'] = inscripcion
                    return render(request ,"box_medical/valoracionbs.html" ,  data)

                elif action=='valoracionpersona':
                    data['title'] = 'Valoracion Medica de Personal'
                    persona = Persona.objects.get(pk=request.GET['id'])
                    persona2=Persona.objects.get(usuario=request.user)
                    if PersonaExamenFisico.objects.filter(personafichamedica__personaextension__persona=persona).exists():
                        pexamenfisico = PersonaExamenFisico.objects.filter(personafichamedica__personaextension__persona=persona)[:1].get()
                    else:
                        pext = PersonaExtension(persona=persona)
                        pext.save()
                        pfichamedica = PersonaFichaMedica(personaextension=pext)
                        pfichamedica.save()
                        pexamenfisico = PersonaExamenFisico(personafichamedica=pfichamedica)
                        pexamenfisico.save()

                    data['pex'] = pexamenfisico
                    data['persona'] = persona
                    data['persona2'] = persona2
                    return render(request ,"box_medical/valoracionpersonal.html" ,  data)

                elif action=='editar':
                    data['title'] = 'Editar Valoracion Medica del Estudiante'
                    pex = PersonaExamenFisico.objects.get(pk=request.GET['id'])
                    inscripcion = Inscripcion.objects.get(pk=request.GET['ins'])
                    initial = model_to_dict(pex)
                    data['form'] = PersonaExamenFisicoForm(initial=initial)
                    data['pex'] = pex
                    data['inscripcion'] = inscripcion
                    return render(request ,"box_medical/editarbs.html" ,  data)

                elif action=='editarpersona':
                    data['title'] = 'Editar Valoracion Medica de la Persona'
                    pex = PersonaExamenFisico.objects.get(pk=request.GET['id'])
                    persona = Persona.objects.get(pk=request.GET['per'])
                    initial = model_to_dict(pex)
                    data['form'] = PersonaExamenFisicoForm(initial=initial)
                    data['pex'] = pex
                    data['persona'] = persona
                    return render(request ,"box_medical/editarpersonal.html" ,  data)

                elif action=='eliminarayos':
                    rayosx = PersonaValoracionImagen.objects.get(pk=request.GET['id'])
                    inscripcion=rayosx.persona.inscripcion()
                    rayosx.delete()
                    return HttpResponseRedirect("/box_medical?action=ficha&id="+str(inscripcion.id))

                elif action=='eliminaexamlab':
                    examenlab = PersonaExamenesLab.objects.get(pk=request.GET['id'])
                    inscripcion=examenlab.persona.inscripcion()
                    examenlab.delete()
                    return HttpResponseRedirect("/box_medical?action=ficha&id="+str(inscripcion.id))

            else:
                search = None
                if 's' in request.GET:
                    search = request.GET['s']
                if search:
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')
                    if len(ss)==1:
                        inscripciones = Inscripcion.objects.filter(Q(persona__nombres__icontains=search) | Q(persona__apellido1__icontains=search) | Q(persona__apellido2__icontains=search) | Q(persona__cedula__icontains=search) | Q(persona__pasaporte__icontains=search) | Q(identificador__icontains=search) | Q(inscripciongrupo__grupo__nombre__icontains=search) | Q(carrera__nombre__icontains=search)).order_by('persona__apellido1')
                    else:
                        inscripciones = Inscripcion.objects.filter(Q(persona__apellido1__icontains=ss[0]) & Q(persona__apellido2__icontains=ss[1])).order_by('persona__apellido1')

                else:
                    inscripciones = Inscripcion.objects.all().order_by('persona__apellido1')

                # inscripciones = inscripciones.filter(graduado=None, carrera__grupocoordinadorcarrera__group__in=request.user.groups.all()).distinct()

                paging = MiPaginador(inscripciones, 60)
                p = 1
                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                    page = paging.page(p)
                except:
                    p = 1
                    page = paging.page(p)

                data['paging'] = paging
                data['rangospaging'] = paging.rangos_paginado(p)
                data['page'] = page
                data['search'] = search if search else ""
                data['inscripciones'] = page.object_list
                data['utiliza_grupos_alumnos'] = UTILIZA_GRUPOS_ALUMNOS
                return render(request ,"box_medical/inscripcionesbs.html" ,  data)
        except:
            HttpResponseRedirect("/box_medical")
