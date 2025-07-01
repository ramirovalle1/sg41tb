import json
from django.contrib.admin.models import ADDITION, LogEntry
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_str
from sga.models import InscripcionAspirantes, TipoRegistroAspirante, OpcionRespuesta,Grupo,TipoNoRegistroAspirante,SesionPractica,\
     Inscripcion,TipoEspecieValorada,RubroEspecieValorada,Rubro,SolicitudOnline,SolicitudEstudiante
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.core.paginator import Paginator
from sga.commonviews import addUserData, ip_client_address
from django.template import RequestContext
from sga.forms import SuministroBoxForm, InscripcionAspirantesForm,InscripcionCextForm
from settings import  EMAIL_ACTIVE,UTILIZA_GRUPOS_ALUMNOS,CENTRO_EXTERNO,INSCRIPCION_CONDUCCION,CARRERAS_ID_EXCLUIDAS_INEC,DIAS_ESPECIE
from datetime import datetime,timedelta
import sys
from decorators import secure_module
from django.db.models.query_utils import Q
from sga.reportes import elimina_tildes
from sga.finanzas import generador_especies

class MiPaginador(Paginator):
    def __init__(self, object_list, per_page, orphans=0, allow_empty_first_page=True, rango=5):
        super(MiPaginador,self).__init__(object_list, per_page, orphans=orphans, allow_empty_first_page=allow_empty_first_page)
        self.rango = rango
        self.paginas = []
        self.primera_pagina = False
        self.ultima_pagina = False

    def rangos_paginado(self, pagina):
        left = pagina - self.rango
        right = pagina + self.rango
        if left<1:
            left=1
        if right>self.num_pages:
            right = self.num_pages
        self.paginas = range(left, right+1)
        self.primera_pagina = True if left>1 else False
        self.ultima_pagina = True if right<self.num_pages else False
        self.ellipsis_izquierda = left-1
        self.ellipsis_derecha = right+1

@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
@transaction.atomic()

def view(request):
    if request.method=='POST':
        action = request.POST['action']
        if action=='inscribir':
            data=[]
            aspirante = InscripcionAspirantes.objects.get(pk=request.POST['id'])
            data['title'] = 'Nueva Inscripcion de Alumno'
            insf = InscripcionAspirantesForm(request.POST)
            data['form'] = insf
            data['utiliza_grupos_alumnos'] = UTILIZA_GRUPOS_ALUMNOS
            data['grupos_abiertos'] = Grupo.objects.filter(abierto=True).order_by('-nombre')
            data['centroexterno'] = CENTRO_EXTERNO
            data['inscripcion_conduccion'] = INSCRIPCION_CONDUCCION

            return render(request ,"inscripciones/adicionarbs.html" ,  data)

        elif action == 'add':
            asp=None
            cedula=None
            pasaporte=None
            f = InscripcionAspirantesForm(request.POST)
            if f.is_valid():
                if  f.cleaned_data['cedula']:
                    cedula= f.cleaned_data['cedula']
                    if InscripcionAspirantes.objects.filter(cedula=cedula,activo=True).order_by('-id').exists():
                       asp = InscripcionAspirantes.objects.filter(cedula=cedula,activo=True).order_by('-id')[:1].get()
                if f.cleaned_data['pasaporte']:
                    pasaporte=f.cleaned_data['pasaporte']
                    if InscripcionAspirantes.objects.filter(pasaporte=f.cleaned_data['pasaporte'],extranjero=True,activo=True).order_by('-id').exists():
                       asp = InscripcionAspirantes.objects.filter(pasaporte=f.cleaned_data['pasaporte'],extranjero=True,activo=True).order_by('-id')[:1].get()
                if asp:
                    if  asp.fueratiempo()<=7:
                        mensajeasp='Aspirante ya esta registrado, no puede ser ingresado nuevamente'
                        return HttpResponseRedirect("/inscripcionesaspirantes?action=add&error1="+(str(mensajeasp)))

                inscripcion=Inscripcion.objects.filter(persona__apellido1='ASPIRANTE')[:1].get()
                inscritoasp = InscripcionAspirantes(nombres=f.cleaned_data['nombres'],
                             apellido1=f.cleaned_data['apellido1'],
                             apellido2=f.cleaned_data['apellido2'],
                             carrera=f.cleaned_data['carrera'],
                             respuesta=f.cleaned_data['respuesta'],
                             sexo=f.cleaned_data['sexo'],
                             telefono=f.cleaned_data['telefono'],
                             telefono_conv=f.cleaned_data['telefono_conv'],
                             email=f.cleaned_data['email'],
                             tiporegistro=f.cleaned_data['tiporegistro'],
                             tiponoregistro=f.cleaned_data['tiponoregistro'],
                             f_inscripcion= f.cleaned_data['f_inscripcion'],
                             sesionpractica=f.cleaned_data['sesionpractica'],
                             cedula=cedula,
                             pasaporte=pasaporte,
                             #vendedor=f.cleaned_data['vendedor'],
                             activo=True,
                             fecha=datetime.now().date(),
                             usuario=request.user,
                             hora=datetime.now().time(),
                             inscripaspirante = inscripcion)
                inscritoasp.save()

                if inscritoasp.pasaporte:
                    inscritoasp.extranjero=True
                    inscritoasp.save()

                #if EMAIL_ACTIVE:
                #    inscritoasp.mail_saludoaspirante(request.user.pk)

                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(inscritoasp).pk,
                    object_id       = inscritoasp.id,
                    object_repr     = force_str(inscritoasp),
                    action_flag     = ADDITION,
                    change_message  = 'Ingreso de Aspirantes (' + client_address + ')')
                return HttpResponseRedirect("/inscripcionesaspirantes")

        elif action == 'generaespecie':
            try:
                fechamax = (datetime.now() - timedelta(days=DIAS_ESPECIE)).date()
                aspirante =InscripcionAspirantes.objects.get(pk=request.POST['id'])
                inscrip=aspirante.inscripaspirante
                tipoespecie = TipoEspecieValorada.objects.get(nombre="CONVALIDACION EXTERNA")
                inscripcionasp = Inscripcion.objects.get(persona__apellido1="ASPIRANTE")
                solicitud = SolicitudOnline.objects.filter(activo=True,libre=True)[:1].get()

                if solicitud.libre:
                    solicitudest = SolicitudEstudiante(solicitud=solicitud,
                                                      inscripcion=inscrip,
                                                      #observacion=f.cleaned_data['observacion'],
                                                      tipoe = tipoespecie,
                                                      correo=aspirante.email,
                                                      celular=aspirante.telefono,
                                                      fecha=datetime.now())
                    solicitudest.save()

                    rubro = Rubro(fecha=datetime.now().date(),
                                valor=tipoespecie.precio,
                                inscripcion = inscrip,
                                cancelado=tipoespecie.precio==0,
                                fechavence=datetime.now().date()  + timedelta(45))
                    rubro.save()

                    # Rubro especie valorada
                    rubroespecie = generador_especies.generar_especie(rubro=rubro, tipo=tipoespecie)
                    rubroespecie.autorizado=False
                    rubroespecie.save()

                    aspirante.tieneespecie=True
                    aspirante.rubroespecie=rubroespecie
                    aspirante.save()

                    inscripcionasp.carrera=aspirante.carrera
                    inscripcionasp.save()

                    datos = {"result": "ok"}
                    return HttpResponse(json.dumps(datos),content_type="application/json")
                else:
                    datos = {"result": "error"}
                    return HttpResponse(json.dumps(datos),content_type="application/json")

            except Exception as ex:
                return HttpResponse(json.dumps({"result":"bad", "error": str(ex)}),content_type="application/json")

        elif action == 'generaespecieproforma':
            try:
                fechamax = (datetime.now() - timedelta(days=DIAS_ESPECIE)).date()
                aspirante =InscripcionAspirantes.objects.get(pk=request.POST['id'])
                inscrip=aspirante.inscripaspirante
                tipoespecie = TipoEspecieValorada.objects.get(nombre="PRESUPUESTO DE CARRERA")
                inscripcionasp = Inscripcion.objects.get(persona__apellido1="ASPIRANTE")
                solicitud = SolicitudOnline.objects.filter(activo=True,libre=True)[:1].get()

                if solicitud.libre:
                    solicitudest = SolicitudEstudiante(solicitud=solicitud,
                                                      inscripcion=inscrip,
                                                      tipoe = tipoespecie,
                                                      correo=aspirante.email,
                                                      celular=aspirante.telefono,
                                                      fecha=datetime.now())
                    solicitudest.save()

                    rubro = Rubro(fecha=datetime.now().date(),
                                valor=tipoespecie.precio,
                                inscripcion = inscrip,
                                cancelado=tipoespecie.precio==0,
                                fechavence=datetime.now().date()  + timedelta(45))
                    rubro.save()

                    # Rubro especie valorada
                    rubroespecie = generador_especies.generar_especie(rubro=rubro, tipo=tipoespecie)
                    rubroespecie.autorizado=False
                    rubroespecie.save()

                    aspirante.especieproforma=True
                    aspirante.rubroespecieproforma=rubroespecie
                    aspirante.save()

                    inscripcionasp.carrera=aspirante.carrera
                    inscripcionasp.save()

                    datos = {"result": "ok"}
                    return HttpResponse(json.dumps(datos),content_type="application/json")
                else:
                    datos = {"result": "error"}
                    return HttpResponse(json.dumps(datos),content_type="application/json")

            except Exception as ex:
                return HttpResponse(json.dumps({"result":"bad", "error": str(ex)}),content_type="application/json")

        elif action=='buscarapellidos':
            ap1=request.POST['apellido1']
            ap2=request.POST['apellido2']
            nom=request.POST['nombres']
            # OCastillo 14-julio-2016 para verificar si existe aspirante en bd
            if ap1 and ap2:
                if InscripcionAspirantes.objects.filter(apellido1=ap1.upper(), apellido2=ap2.upper(),nombres=nom.upper(),activo=True).order_by('-id').exists():
                    asp = InscripcionAspirantes.objects.filter(apellido1=ap1.upper(), apellido2=ap2.upper(),nombres=nom.upper(),activo=True).order_by('-id')[:1].get()
                    if asp.fueratiempo()<=7:
                        return HttpResponse(json.dumps({'result':'bad'}),content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({'result':'ok'}),content_type="application/json")
                else:
                    return HttpResponse(json.dumps({'result':'ok'}),content_type="application/json")


        elif action=='buscarcedula':
            estudiante = ''
            cedula=request.POST['cedula']

            documentos=[]

            if cedula:
                if InscripcionAspirantes.objects.filter(cedula=cedula,activo=True).order_by('-id').exists():
                     for asp in InscripcionAspirantes.objects.filter(cedula=cedula,activo=True).order_by('-id'):
                         if asp.fueratiempo()<=7:
                            return HttpResponse(json.dumps({"result":"bad2","aspirante": (str(elimina_tildes(asp.apellido1))+' '+str(elimina_tildes(asp.apellido2))+' Cedula: '+str(asp.cedula))}),content_type="application/json")
                # OCastillo 02-10-2015 se incluye validacion que excluya Congresos y Seminarios
                elif Inscripcion.objects.filter(persona__cedula=request.POST['cedula']).exclude(carrera__in=CARRERAS_ID_EXCLUIDAS_INEC).exists():
                    for i in Inscripcion.objects.filter(persona__cedula=request.POST['cedula']).exclude(carrera__in=CARRERAS_ID_EXCLUIDAS_INEC):
                        estudiante = estudiante + ' - ' +i.carrera.nombre

                    return HttpResponse(json.dumps({"result":"bad","estudiante": str(estudiante),"documentos":documentos}),content_type="application/json")
                else:
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")

        elif action=='buscarpas':
            estudiante = ''
            pasaporte=  request.POST['pasaporte']
            pasaporte = pasaporte.upper( )
            documentos=[]

            # OCastillo 05-10-2015 para pasaporte se incluye validacion que excluya Congresos y Seminarios
            if pasaporte:
                if InscripcionAspirantes.objects.filter(pasaporte=pasaporte,activo=True).order_by('-id').exists():
                     for asp in InscripcionAspirantes.objects.filter(pasaporte=pasaporte,activo=True).order_by('-id'):
                         if asp.fueratiempo()<=7:
                            return HttpResponse(json.dumps({"result":"bad2","aspirante": (str(elimina_tildes(asp.apellido1))+' '+str(elimina_tildes(asp.apellido2))+' Pasaporte: '+str(asp.pasaporte))}),content_type="application/json")
                elif Inscripcion.objects.filter(persona__pasaporte=pasaporte).exists():
                    for i in Inscripcion.objects.filter(persona__pasaporte=pasaporte).exclude(carrera__in=CARRERAS_ID_EXCLUIDAS_INEC):
                        estudiante = estudiante + ' - ' +i.carrera.nombre

                    return HttpResponse(json.dumps({"result":"bad","estudiante": str(estudiante),"documentos":documentos}),content_type="application/json")
                else:
                        return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")

        return HttpResponseRedirect("/inscripcionesaspirantes?action=add")

    else:
        data = {'title': 'Aspirantes'}
        addUserData(request,data)
        hoy = datetime.today().date()
        data['fechahoy'] = hoy
        if 'action' in request.GET:
            action = request.GET['action']
            if action == 'add':
                data['title']= 'Registro de Aspirantes'

                form = InscripcionAspirantesForm(initial={'f_inscripcion':hoy})
                data['form']= form
                if 'error1' in request.GET:
                    data['error1'] = request.GET['error1']
                return render(request ,"inscripcionesaspirantes/adicionarbs.html" ,  data)

        # elif 'action' == 'buscarapellidos':
        #     ap1=request.GET['apellido1']
        #     ap2=request.GET['apellido2']
        #     nom=request.GET['nombres']
        #
        #     if ap1 and ap2:
        #         if InscripcionAspirantes.objects.filter(apellido1=ap1.upper(), apellido2=ap2.upper()).exists():
        #             return HttpResponse(json.dumps({'result':'bad'}),content_type="application/json")
        #         else:
        #             return HttpResponse(json.dumps({'result':'ok'}),content_type="application/json")

        else:
            search = None
            todos = None

            if 's' in request.GET:
                search = request.GET['s']
            if 't' in request.GET:
                todos = request.GET['t']
            if search:
                ss = search.split(' ')
                while '' in ss:
                    ss.remove('')
                if len(ss)==1:
                    insasp = InscripcionAspirantes.objects.filter(Q(apellido1__icontains=search) | Q(apellido2__icontains=search)|Q(cedula=search)| Q(pasaporte=search)).order_by('-fecha','apellido1')
                else:
                    insasp = InscripcionAspirantes.objects.filter(Q(apellido1__icontains=ss[0]) & Q (apellido2__icontains=ss[1])).order_by('-fecha','apellido1','apellido2','nombres')

            else:
                fecha =datetime.now().date() + timedelta(days=-7)
                insasp =InscripcionAspirantes.objects.filter(activo=True,fecha__gte=fecha).order_by('-fecha','apellido1')

                # insasp = InscripcionAspirantes.objects.filter(activo=True).order_by('-fecha','apellido1')

            paging = MiPaginador(insasp, 30)
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
            data['insasp'] = page.object_list
            return render(request ,"inscripcionesaspirantes/inscripcionesbs.html" ,  data)
