from datetime import datetime
import json
from django.db.models import Q
from django.forms import model_to_dict
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from bib.models import Documento, ConsultaBiblioteca, OtraBibliotecaVirtual, ReferenciaWeb
from settings import BIBLIOTECA_PARAMETRIZADA
from sga.models import Coordinacion, Inscripcion, RolPerfilProfesor


def view(request):
    if request.method=='POST':
        busqueda = request.POST['search']
        t = busqueda
        #documentos = Documento.objects.all()
        #for t in terminos:

        ss = busqueda.split(' ')
        if len(ss)==1:
             documentos = Documento.objects.filter(Q(docente__persona__apellido1__icontains=t)|
                                           Q(docente__persona__apellido2__icontains=t)|
                                           Q(inscripcion__persona__apellido1__icontains=t)|
                                           Q(inscripcion__persona__apellido2__icontains=t)|
                                           Q(inscripcion__persona__cedula__icontains=t)
                                         )
        else:
             documentos = Documento.objects.filter(Q(docente__persona__apellido1__icontains=ss[0])|Q(docente__persona__apellido2__icontains=ss[1])|Q(inscripcion__persona__apellido1__icontains=ss[0])|Q(inscripcion__persona__apellido2__icontains=ss[1]))

        if len(documentos)==0:

            documentos=  Documento.objects.filter(Q(codigo__icontains=t) | Q(nombre__icontains=t) | Q(autor__icontains=t)  | Q(tutor__icontains=t) | Q(anno__icontains=t) )



        fisicos = documentos.filter(fisico=True).exclude(tipo__id=3)[:30]
        tesisf = documentos.filter(tipo__id=3, fisico=True)[:30]
        tesisd = documentos.filter(tipo__id=3, fisico=False)[:30]
        digitales = documentos.exclude(digital='').exclude(tipo__id=3)[:30]

        totalfisicos = documentos.filter(fisico=True).exclude(tipo__id=3).count()   #Libros Fisicos, no incluye tesis
        totaltesisf = documentos.filter(tipo__id=3, fisico=True).count()            #Tesis Fisicas
        totaltesisd = documentos.filter(tipo__id=3, fisico=False).count()           #Tesis Digitales
        totaldigitales = documentos.exclude(digital='').exclude(tipo__id=3).count() #Libros digitales, no incluyan tesis

        #data = {"busqueda": ", ".join(t)}
        data = {"busqueda": t}
        data['fisicos'] = fisicos
        data['digitales'] = digitales
        data['tesisf'] = tesisf
        data['tesisd'] = tesisd

        data['tfisicos'] = totalfisicos
        data['tdigitales'] = totaldigitales
        data['ttesisf'] = totaltesisf
        data['ttesisd'] = totaltesisd

        try:
            persona=request.session['persona']
            consulta = ConsultaBiblioteca(fecha=datetime.today(),
                                          hora=datetime.now().time(),
                                          persona=persona,
                                          busqueda=t)
            consulta.save()
            request.session['consulta'] = consulta

            return render(request ,"biblioteca/bibliosearch.html" ,  data)
        except Exception as ex:
            return HttpResponse(json.dumps({"result":"bad", "error": "Person not found"}),content_type="application/json")
    else:
        return HttpResponse(json.dumps({"result":"bad", "error": "Only POST search"}),content_type="application/json")


def otras(request):
    data = {}
    data['otras'] = OtraBibliotecaVirtual.objects.filter(estado=True).order_by('-id')
    return render(request ,"biblioteca/otrasbibliotecas.html" ,  data)

def gourl(request):
    try:
        persona = request.session['persona']
        action = request.GET['action']
        if action=='ref':
            referencia = ReferenciaWeb.objects.get(pk=request.GET['id'])
            consulta = ConsultaBiblioteca(fecha=datetime.today(), hora=datetime.now().time(), persona=persona, busqueda="")
            consulta.save()
            consulta.referenciasconsultadas.add(referencia)
            consulta.save()
            url =referencia.url
            # try:
            #     if referencia.id==BIBLIOTECA_PARAMETRIZADA:
            #         if Inscripcion.objects.filter(persona= persona).exists():
            #             inscripcion = Inscripcion.objects.get(persona= persona)
            #             coordinacion = Coordinacion.objects.filter(carrera__id= inscripcion.carrera_id)[:1].get()
            #             url = referencia.url+"?e="+str(persona.id)+"&n="+persona.nombres+"&l="+persona.apellido1+" "+persona.apellido2+"&decanatura="+coordinacion.nombre+"&carrera="+inscripcion.carrera.alias
            #         elif RolPerfilProfesor.objects.filter(profesor__persona=persona).exists():
            #             profesor =  RolPerfilProfesor.objects.get(profesor__persona=persona)
            #             url = referencia.url+"?e="+str(persona.id)+"&n="+persona.nombres+"&l="+persona.apellido1+" "+persona.apellido2+"&decanatura="+profesor.coordinacion.nombre
            #         elif persona.es_administrativo():
            #             per = persona.usuario.groups.all()[:1].get()
            #             usuario = per.name
            #             print('entro adm')
            #             url = referencia.url+"?e="+str(persona.id)+"&n="+persona.nombres+"&l="+persona.apellido1+" "+persona.apellido2+"&departamento="+usuario
            # except Exception as ex:
            #     return HttpResponseRedirect("/")
            return HttpResponseRedirect(url)
        elif action=='otra':
            otrabiblio = OtraBibliotecaVirtual.objects.get(pk=request.GET['id'])
            consulta = ConsultaBiblioteca(fecha=datetime.today(), hora=datetime.now().time(), persona=persona, busqueda="")
            consulta.save()
            consulta.otrabibliotecaconsultadas.add(otrabiblio)
            consulta.save()
            return HttpResponseRedirect(otrabiblio.url)
        else:
            return HttpResponseRedirect("/")
    except Exception as ex:
        return HttpResponseRedirect("/")

def book(request, id):
    documento = Documento.objects.get(pk=id)
    if 'consulta' in request.session:
        consulta = request.session['consulta']
        consulta.documentosconsultados.add(documento)
        consulta.save()
    data = model_to_dict(documento, exclude=['digital','portada'])
    data['tipo'] = documento.tipo.nombre
    data['sede'] = documento.sede.nombre
    if documento.digital:
        data['digital'] = documento.digital.url
    if documento.portada:
        data['portada'] = documento.portada.url
    if documento.autor:
        data['autor']=documento.autor
    else:
        data['autor']=documento.inscripcion.persona.nombre_completo_inverso()

    if documento.tutor:
        data['tutor']=documento.tutor
    else:
        data['tutor']=documento.docente.persona.nombre_completo_inverso()
    data['disponibles'] = documento.copias_restantes()
    return HttpResponse(json.dumps(data),content_type="application/json")
