# -*- coding: latin-1 -*-
from datetime import datetime
import json
import  os
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from decorators import secure_module
from settings import ARCHIVO_TIPO_SYLLABUS, ARCHIVO_TIPO_DEBERES, ARCHIVO_TIPO_MATERIALAPOYO,MEDIA_ROOT, ARCHIVO_TIPO_PLANCLASE
from sga.commonviews import addUserData
from sga.forms import ArchivoSyllabusForm, ArchivoDeberForm, ArchivoForm
from sga.models import Profesor, LeccionGrupo, Materia, Archivo, TipoArchivo, Periodo, Leccion,DeberAlumno


@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    if request.method=='POST':
        action = request.POST['action']
        if action=='addsyllabus':
            form = ArchivoSyllabusForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    archivo = Archivo(nombre=form.cleaned_data['nombre'],
                                     materia=form.cleaned_data['materia'],
                                     fecha=datetime.now(),
                                     archivo = request.FILES['archivo'],
                                     tipo = TipoArchivo.objects.get(pk=ARCHIVO_TIPO_SYLLABUS))
                    archivo.save()
                except:
                    return HttpResponseRedirect("/pro_documentos?action=addsyllabus&id="+str(form.cleaned_data['materia'].id)+"&error=1")
            else:
                return HttpResponseRedirect("/pro_documentos?action=addsyllabus&id="+str(request.POST['materia'])+"&error=1")

        elif action == 'ver':
            try:
                deber = DeberAlumno.objects.get(pk=request.POST['id'])
                deber.visto = True
                deber.save()
                return HttpResponse(json.dumps({"result": "ok", "ruta":str(deber.archivo)  }),content_type="application/json")
            except :
                return HttpResponse(json.dumps({"result": "bad" }),content_type="application/json")
        elif action == 'addnota':
            try:
                deber = DeberAlumno.objects.get(pk=request.POST['id'])
                deber.nota = request.POST['nota']
                deber.save()
                return HttpResponse(json.dumps({"result": "ok" }),content_type="application/json")
            except :
                return HttpResponse(json.dumps({"result": "bad" }),content_type="application/json")
        elif action=='addmaterial':
                form = ArchivoForm(request.POST, request.FILES)
                if form.is_valid():
                    try:
                        leccion = Leccion.objects.filter(pk=request.POST['leccion'])[:1].get()
                        materia = leccion.clase.materia
                        archivo = Archivo(nombre='MATERIAL DE APOYO',
                                      materia=materia,
                                      lecciongrupo=leccion.leccion_grupo(),
                                      fecha=datetime.now(),
                                      archivo = request.FILES['archivo'],
                                      tipo = TipoArchivo.objects.get(pk=ARCHIVO_TIPO_MATERIALAPOYO))
                        archivo.save()

                        return HttpResponseRedirect("/pro_documentos?action=material&id="+request.POST['materia'])
                    except Exception as ex:
                        pass
                return HttpResponseRedirect("/pro_documentos?action=addmaterial&id="+request.POST['materia']+"&error=1")


        elif action=='addplanclase':
            form = ArchivoForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    archivo = Archivo.objects.filter(pk=request.POST['id'])[:1].get()
                    nombre = archivo.archivo
                    archivo.fecha=datetime.now()
                    archivo.archivo = request.FILES['archivo']
                    archivo.save()
                    os.remove(MEDIA_ROOT + '/' + str(nombre))

                    return HttpResponseRedirect("/pro_documentos")
                except Exception as ex:
                    pass
            return HttpResponseRedirect("/pro_documentos?action=addplanclase&id="+request.POST['id']+"&error=1")

        elif action=='adddeberes':
            form = ArchivoDeberForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    leccion = Leccion.objects.filter(pk=request.POST['leccion'])[:1].get()
                    materia = leccion.clase.materia
                    archivo = Archivo(nombre=form.cleaned_data['nombre'],
                                      materia=materia,
                                      puntaje=form.cleaned_data['puntaje'],
                                      lecciongrupo=leccion.leccion_grupo(),
                                      fecha=datetime.now(),
                                      archivo = request.FILES['archivo'],
                                      tipo = TipoArchivo.objects.get(pk=ARCHIVO_TIPO_DEBERES))
                    archivo.save()
                    return HttpResponseRedirect("/pro_documentos?action=deberes&id="+request.POST['materia'])
                except Exception as ex:
                    return HttpResponseRedirect("/pro_documentos?action=adddeberes&id="+request.POST['materia']+"&leccion="+request.POST['leccion']+"&error="+str(ex))
            return HttpResponseRedirect("/pro_documentos?action=adddeberes&id="+request.POST['materia']+"&leccion="+request.POST['leccion']+"&error=1")
        return HttpResponseRedirect("/pro_documentos")

    else:
        data = {'title': 'Archivos del Profesor'}
        addUserData(request,data)

        if 'action' in request.GET:
            action = request.GET['action']
            if action=='addsyllabus':
                data['title'] = 'Adicionar Syllabus'
                materia = Materia.objects.get(pk=request.GET['id'])
                data['materia'] = materia
                form = ArchivoSyllabusForm()
                form.for_materia(materia.id)
                data['form'] =form

                if 'error' in request.GET:
                    data['formerror'] = "Los archivos que son subidos no deben tener tildes, '&ntilde;' u otros caracteres especiales en su nombre, ser del tipo especificado y no exceder el tama&ntildeo m&aacute;ximo."
                return render(request ,"pro_documentos/adicionarbs.html" ,  data)

            elif action=='delsyllabus':
                try:
                    archivo = Archivo.objects.get(pk=request.GET['id'])
                    archivo.delete()
                    return HttpResponseRedirect("/pro_documentos")
                except:
                    pass
            elif action=='addmaterial':
                data['title'] = 'Adicionar Material'
                materia = Materia.objects.get(pk=request.GET['id'])
                leccion = Leccion.objects.get(pk=request.GET['leccion'])
                data['materia'] = materia
                data['leccion'] = leccion
                data['form'] = ArchivoForm()
                if 'error' in request.GET:
                    data['formerror'] = "Los archivos que son subidos no deben tener tildes, '&ntilde;' u otros caracteres especiales en su nombre, ser del tipo especificado y no exceder el tama&ntildeo m&aacute;ximo."
                return render(request ,"pro_documentos/addmaterial.html" ,  data)

            elif action=='addplanclase':
                data['title'] = 'Cambiar Plan de Clase'
                archivo = Archivo.objects.get(pk=request.GET['id'])
                data['archivo'] = archivo
                data['form'] = ArchivoForm()
                if 'error' in request.GET:
                    data['formerror'] = "Los archivos que son subidos no deben tener tildes, '&ntilde;' u otros caracteres especiales en su nombre, ser del tipo especificado y no exceder el tama&ntildeo m&aacute;ximo."
                return render(request ,"pro_documentos/addplanclase.html" ,  data)

            elif action=='adddeberes':
                data['title'] = 'Adicionar Deberes'
                materia = Materia.objects.get(pk=request.GET['id'])
                leccion = Leccion.objects.get(pk=request.GET['leccion'])
                data['materia'] = materia
                data['leccion'] = leccion
                data['form'] = ArchivoDeberForm(initial={'fechaentrega':datetime.now()})
                if 'error' in request.GET:
                    if request.GET['error'] != 1:
                        data['formerror'] = data['error']
                    else:
                        data['formerror'] = "Los archivos que son subidos no deben tener tildes, '&ntilde;' u otros caracteres especiales en su nombre, ser del tipo especificado y no exceder el tama&ntildeo m&aacute;ximo."

                return render(request ,"pro_documentos/adddeberesbs.html" ,  data)

            elif action == 'verdeberes':
                if LeccionGrupo.objects.filter(lecciones=request.GET['id']).exists():
                    data['lecciongrupo'] = LeccionGrupo.objects.get(lecciones=request.GET['id'])
                    data['deberes'] = DeberAlumno.objects.filter(lecciongrupo=data['lecciongrupo']).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2')
                return render(request ,"pro_documentos/verdeberes.html" ,  data)

            elif action=='deldeber':
                try:
                    archivo = Archivo.objects.get(pk=request.GET['id'])
                    materia = archivo.materia_id
                    archivo.delete()
                    return HttpResponseRedirect("/pro_documentos?action=deberes&id="+ str(materia))
                except:
                    pass

            elif action=='delmaterial':
                try:
                    archivo = Archivo.objects.get(pk=request.GET['id'])
                    materia = archivo.materia_id
                    archivo.delete()
                    return HttpResponseRedirect("/pro_documentos?action=material&id="+ str(materia))
                except:
                    pass

            elif action=='deberes':
                data['title'] = 'Deberes por Clases'
                materia = Materia.objects.get(pk=request.GET['id'])
                profesor = Profesor.objects.get(persona=data['persona'])
                #leccionesGrupo = LeccionGrupo.objects.filter(materia=materia,profesor=profesor).order_by('-fecha','-horaentrada')
                leccionesGrupo = LeccionGrupo.objects.filter(lecciones__clase__materia=materia).order_by('-fecha','-horaentrada')
                lecciones = Leccion.objects.filter(clase__materia=materia).order_by('-fecha','-horaentrada')
                paging = Paginator(lecciones, 30)
                p=1
                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                    page = paging.page(p)
                except:
                    page = paging.page(1)

                data['paging'] = paging
                data['page'] = page
                data['leccionesgrupo'] = leccionesGrupo
                data['lecciones'] = page.object_list
                data['materia'] = materia
                data['profesor'] = profesor
                return render(request ,"pro_documentos/clasesbs.html" ,  data)

            elif action=='material':
                data['title'] = 'Material de Clase'
                materia = Materia.objects.get(pk=request.GET['id'])
                profesor = Profesor.objects.get(persona=data['persona'])
                #leccionesGrupo = LeccionGrupo.objects.filter(materia=materia,profesor=profesor).order_by('-fecha','-horaentrada')
                leccionesGrupo = LeccionGrupo.objects.filter(lecciones__clase__materia=materia).order_by('-fecha','-horaentrada')
                lecciones = Leccion.objects.filter(clase__materia=materia).order_by('-fecha','-horaentrada')
                paging = Paginator(lecciones, 30)
                p=1
                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                    page = paging.page(p)
                except:
                    page = paging.page(1)

                data['paging'] = paging
                data['page'] = page
                data['leccionesgrupo'] = leccionesGrupo
                data['lecciones'] = page.object_list
                data['materia'] = materia
                data['profesor'] = profesor
                return render(request ,"pro_documentos/material.html" ,  data)
            return HttpResponseRedirect("/pro_documentos")
        else:
            try:
                profesor = Profesor.objects.get(persona=data['persona'])
                data['profesor'] = profesor
                periodo = request.session['periodo']
                if Materia.objects.filter(nivel__periodo=periodo,profesormateria__profesor=profesor).exists() or Materia.objects.filter(nivel__periodo=True, profesormateria__profesor_aux=profesor.id).exists():
                    materias =  Materia.objects.filter(Q(nivel__periodo=periodo,profesormateria__profesor=profesor)& (Q(profesormateria__profesor=profesor,profesormateria__profesor_aux=None) | Q(profesormateria__profesor_aux=profesor.id))).order_by('asignatura','nivel__sede','nivel__nivelmalla')
                    data['materias'] = materias
                    data['nivel'] = materias[0].nivel
                    data['periodo'] = periodo
                    if 'info' in request.GET:
                        data['info'] = request.GET['info']
                data['ARCHIVO_TIPO_PLANCLASE'] = ARCHIVO_TIPO_PLANCLASE
                return render(request ,"pro_documentos/materiasbs.html" ,  data)
            except Exception as ex:
                return HttpResponseRedirect("/")
