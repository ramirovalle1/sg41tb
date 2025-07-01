from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.core.paginator import Paginator
import json
from django.db.models.query_utils import Q
from django.forms.models import model_to_dict
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template import RequestContext
from decorators import secure_module
from settings import DEFAULT_PASSWORD, PROFESORES_GROUP_ID, ALUMNOS_GROUP_ID
from sga.commonviews import addUserData
from sga.forms import AsignaturaForm
from sga.models import Asignatura,AsignaturaMalla, RubroOtro,Rubro,TipoOtroRubro, Inscripcion, Profesor, Persona, elimina_tildes
from datetime import datetime


@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    if request.method=='POST':
        action = request.POST['action']
        if action=='add':
            f = AsignaturaForm(request.POST)
            if f.is_valid():
                codigo = ""
                if f.cleaned_data['codigo']:
                    codigo = f.cleaned_data['codigo']
                asignatura = Asignatura(nombre = elimina_tildes(f.cleaned_data['nombre']),
                                        codigo=codigo,
                                        creditos=f.cleaned_data['creditos'],
                                        promedia = f.cleaned_data['promedia'] ,
                                        asistencia = f.cleaned_data['asistencia'] ,
                                        sin_malla = f.cleaned_data['sin_malla'] ,
                                        titulacion = f.cleaned_data['titulacion'],
                                        nivelacion = f.cleaned_data['nivelacion'] )
                asignatura.save()
                asignatura.precedencia.set(f.cleaned_data['precedencia'])
                return HttpResponseRedirect("/asignaturas")
            else:
                return HttpResponseRedirect("/asignaturas?action=add")

        elif action=='edit':
            asignatura = Asignatura.objects.get(pk=request.POST['id'])
            f = AsignaturaForm(request.POST)
            if f.is_valid():
                codigo=""
                if f.cleaned_data['codigo']:
                    codigo = f.cleaned_data['codigo']
                asignatura.nombre = elimina_tildes(f.cleaned_data['nombre'])
                asignatura.codigo = codigo
                asignatura.creditos = f.cleaned_data['creditos']
                asignatura.promedia = f.cleaned_data['promedia']
                asignatura.asistencia = f.cleaned_data['asistencia']
                asignatura.sin_malla = f.cleaned_data['sin_malla']
                asignatura.titulacion = f.cleaned_data['titulacion']
                asignatura.nivelacion = f.cleaned_data['nivelacion']
                asignatura.save()
                asignatura.precedencia.set(f.cleaned_data['precedencia'])


        elif action=='delete':
            asignatura = Asignatura.objects.get(pk=request.POST['id'])
            asignatura.delete()

#        elif action=='rectora':
#            asignatura = Asignatura.objects.get(pk=request.POST['id'])
#            asignatura.rectora = request.POST['val'] == 'y'
#            asignatura.save()
#            return HttpResponse(json.dumps({"result":"ok"}), content_type="application/json")

        return HttpResponseRedirect("/asignaturas")
    else:
        data = {'title': 'Listado de Asignaturas'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='add':
                data['title'] = 'Adicionar Asignatura'
                data['form'] = AsignaturaForm()
                return render(request ,"asignaturas/adicionarbs.html" ,  data)
            # elif action=='congreso':
            #     c=0
            #     for r in RubroOtro.objects.filter(descripcion__icontains='5TO CONGRESO', rubro__cancelado=False):
            #         if not r.rubro.total_pagado() > 0:
            #             tipootro = TipoOtroRubro.objects.get(pk=7)
            #             inscripcion = r.rubro.inscripcion
            #             rubro = Rubro(fecha=datetime.now().date(), valor=30,
            #                           inscripcion=inscripcion, cancelado=False, fechavence='2016-09-30')
            #             rubro.save()
            #             rubrootro = RubroOtro(rubro=rubro, tipo=tipootro, descripcion='5TO CONGRESO DE SALUD CUOTA 1' )
            #             rubrootro.save()
            #
            #             tipootro = TipoOtroRubro.objects.get(pk=7)
            #             inscripcion = r.rubro.inscripcion
            #             rubro = Rubro(fecha=datetime.now().date(), valor=25,
            #                           inscripcion=inscripcion, cancelado=False, fechavence='2016-10-07')
            #             rubro.save()
            #             rubrootro = RubroOtro(rubro=rubro, tipo=tipootro, descripcion='5TO CONGRESO DE SALUD CUOTA 2' )
            #             rubrootro.save()
            #             # c = c + 1
            #             # print(str(r.rubro.inscripcion))
            #             r.rubro.delete()
            #     # print(c)


            elif action=='matri':
                for i in Inscripcion.objects.filter():
                    if i.matriculado():
                        print(str(i.persona.cedula) + ";1")
                    else:
                        print(str(i.persona.cedula) + ";0")
            elif action=='doc':
                for i in Profesor.objects.filter(activo=True):
                        print(str(i.persona.cedula))
            elif action=='adm':
                gruposexcluidos = [PROFESORES_GROUP_ID,ALUMNOS_GROUP_ID]
                for p in Persona.objects.filter(usuario__is_active=True).exclude(usuario__groups__id__in=gruposexcluidos).order_by('apellido1'):
                    print(p.cedula)

            elif action=='edit':
                data['title'] = 'Editar Asignaturas'
                asignatura = Asignatura.objects.get(pk=request.GET['id'])
                data['form'] = AsignaturaForm(instance=asignatura)
                data['asignatura'] = asignatura
                return render(request ,"asignaturas/editarbs.html" ,  data)
            elif action=='delete':
                data['title'] = 'Eliminar Asignatura'
                data['asignatura'] = Asignatura.objects.get(pk=request.GET['id'])
                return render(request ,"asignaturas/borrarbs.html" ,  data)
            elif action=='info':

                    if Asignatura.objects.get(id=request.GET['aid']).sin_malla:
                        a =Asignatura.objects.get(id=request.GET['aid'])
                        return HttpResponse(json.dumps({'result': 'ok', 'creditos': a.creditos,
                                                    'codigo': a.codigo,
                                                    'horas': a.horas}),content_type="application/json")
                    else:
                         try:
                            a = AsignaturaMalla.objects.filter(asignatura__id=request.GET['aid'])[:1].get()
                            return HttpResponse(json.dumps({'result': 'ok', 'creditos': a.creditos,
                                                            'codigo': a.asignatura.codigo,
                                                            'horas': a.horas}),content_type="application/json")
                         except:
                             return HttpResponse(json.dumps({"result": "bad"}),content_type="application/json")
                    # return HttpResponseRedirect('/asignaturas')
        else:
            search = None
            if 's' in request.GET:
                search = request.GET['s']
            if search:
                asignaturas = Asignatura.objects.filter(Q(nombre__icontains=search)).order_by('nombre')
            else:
                asignaturas = Asignatura.objects.all().order_by('nombre')
            paging = Paginator(asignaturas, 50)
            try:
                if 'page' in request.GET:
                    asignaturas = int(request.GET['page'])
                page = paging.page(asignaturas)
            except:
                page = paging.page(1)
            data['paging'] = paging
            data['page'] = page
            data['search'] = search if search else ""
            data['asignaturas'] = page.object_list
            return render(request ,"asignaturas/asignaturasbs.html" ,  data)
