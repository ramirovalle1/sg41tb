from datetime import datetime
import json
import os
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Q
from django.forms.models import model_to_dict
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.utils.encoding import force_str
from decorators import secure_module
from settings import MEDIA_ROOT
from sga.commonviews import addUserData, ip_client_address
from sga.forms import TitulacionProfesorForm, CargarCVForm, PublicacionForm, AutorForm
from sga.models import Profesor, TitulacionProfesor, CVPersona, Persona, LibroPersona, LibroRevista, elimina_tildes


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
# @secure_module
def view(request):
    if request.method=='POST':
        action = request.POST['action']
        if action=='addpublicacion':
            persona = Persona.objects.get(pk=request.POST['id'])
            f = PublicacionForm(request.POST, request.FILES)
            if f.is_valid():
                try:
                    publicacion = LibroRevista(es_libro= not f.cleaned_data['es_revista'],
                                               titulo=f.cleaned_data['titulo'],
                                               codigo=f.cleaned_data['codigo'],
                                               num_paginas=f.cleaned_data['num_paginas'],
                                               volumen=f.cleaned_data['volumen'],
                                               num_capitulos=f.cleaned_data['num_capitulos'],
                                               referencias_bib=f.cleaned_data['referencias_bib'],
                                               proposito=f.cleaned_data['proposito'],
                                               anno_publ=f.cleaned_data['anno_publ'],
                                               pais=f.cleaned_data['pais'],
                                               descripcion=f.cleaned_data['descripcion'],
                                               patrocinador=f.cleaned_data['patrocinador'],
                                               electronica=f.cleaned_data['electronica'],
                                               impresa=f.cleaned_data['impresa'],
                                               frecuencia=f.cleaned_data['frecuencia'],
                                               indexado=f.cleaned_data['indexado'],
                                               imprenta=f.cleaned_data['imprenta'],
                                               usuario=request.user,
                                               fecha=datetime.now())

                    if 'bases_index' in f.cleaned_data:
                        publicacion.bases_index = f.cleaned_data['bases_index']
                    if  'archivo' in request.FILES:
                        publicacion.archivo = request.FILES['archivo']
                    publicacion.save()
                    for aut in f.cleaned_data['autor_codigos'].split(','):
                        pers = None
                        otro = ''
                        try:
                            pers = Profesor.objects.filter(pk=int(aut))[:1].get().persona
                        except:
                            otro= aut
                        libroper = LibroPersona(libro_revista=publicacion,
                                                persona=pers,
                                                autor=True,
                                                otros=otro,
                                                usuario=request.user,
                                                fecha=datetime.now())
                        libroper.save()
                    for coaut in f.cleaned_data['coautor_codigos'].split(','):
                        pers = None
                        otro = ''
                        try:
                            pers = Profesor.objects.filter(pk=int(coaut))[:1].get().persona
                        except:
                            otro= coaut
                        libroper = LibroPersona(libro_revista=publicacion,
                                                persona=pers,
                                                autor=False,
                                                otros=otro,
                                                usuario=request.user,
                                               fecha=datetime.now())
                        libroper.save()
                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de ADICIONAR HISTORICO
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(publicacion).pk,
                        object_id       = publicacion.id,
                        object_repr     = force_str(publicacion),
                        action_flag     = ADDITION,
                        change_message  = 'Adicionada Publicacion (' + client_address + ')' )
                    return HttpResponseRedirect("/publicaciones?persona="+str(persona.id)+"&op="+request.POST['op'])
                except Exception as e:
                    return HttpResponseRedirect("/publicaciones?action=add&id="+str(persona.id)+"&error="+str(e)+"&op="+request.POST['op'])
            else:
                return HttpResponseRedirect("/publicaciones?action=add&id="+str(persona.id)+"&error=Llenar todos los datos del formulario&op="+request.POST['op'])
        elif action=='editpublicacion':
                persona = Persona.objects.get(pk=request.POST['persona'])
                publicacion = LibroRevista.objects.get(pk=request.POST['id'])
                f = PublicacionForm(request.POST, request.FILES)
                if f.is_valid():
                    try:
                        publicacion.es_libro= not f.cleaned_data['es_revista']
                        publicacion.titulo=f.cleaned_data['titulo']
                        publicacion.codigo=f.cleaned_data['codigo']
                        publicacion.num_paginas=f.cleaned_data['num_paginas']
                        publicacion.volumen=f.cleaned_data['volumen']
                        publicacion.num_capitulos=f.cleaned_data['num_capitulos']
                        publicacion.referencias_bib=f.cleaned_data['referencias_bib']
                        publicacion.proposito=f.cleaned_data['proposito']
                        publicacion.anno_publ=f.cleaned_data['anno_publ']
                        publicacion.pais=f.cleaned_data['pais']
                        publicacion.descripcion=f.cleaned_data['descripcion']
                        publicacion.patrocinador=f.cleaned_data['patrocinador']
                        publicacion.imprenta=f.cleaned_data['imprenta']
                        publicacion.electronica=f.cleaned_data['electronica']
                        publicacion.impresa=f.cleaned_data['impresa']
                        publicacion.frecuencia=f.cleaned_data['frecuencia']
                        publicacion.indexado=f.cleaned_data['indexado']

                        publicacion.usuario=request.user
                        publicacion.fecha=datetime.now()
                        if 'bases_index' in f.cleaned_data:
                            publicacion.bases_index = f.cleaned_data['bases_index']

                        if  'archivo' in request.FILES:
                            if os.path.exists(MEDIA_ROOT + '/' + str(publicacion.archivo)):
                                os.remove(MEDIA_ROOT + '/' + str(publicacion.archivo))
                            publicacion.archivo = request.FILES['archivo']
                        publicacion.save()
                        LibroPersona.objects.filter(libro_revista=publicacion).delete()
                        if f.cleaned_data['autor_codigos'] != "":
                            for aut in f.cleaned_data['autor_codigos'].split(','):
                                pers = None
                                otro = ''
                                try:
                                    pers = Profesor.objects.filter(pk=int(aut))[:1].get().persona
                                except:
                                    otro= aut
                                libroper = LibroPersona(libro_revista=publicacion,
                                                        persona=pers,
                                                        autor=True,
                                                        otros=otro,
                                                        usuario=request.user,
                                                        fecha=datetime.now())
                                libroper.save()
                        if f.cleaned_data['coautor_codigos'] != "" :
                            for coaut in f.cleaned_data['coautor_codigos'].split(','):
                                pers = None
                                otro = ''
                                try:
                                    pers = Profesor.objects.filter(pk=int(coaut))[:1].get().persona
                                except:
                                    otro= coaut
                                libroper = LibroPersona(libro_revista=publicacion,
                                                        persona=pers,
                                                        autor=False,
                                                        otros=otro,
                                                        usuario=request.user,
                                                       fecha=datetime.now())
                                libroper.save()
                         #Obtain client ip address
                        client_address = ip_client_address(request)

                        # Log de ADICIONAR HISTORICO
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(publicacion).pk,
                            object_id       = publicacion.id,
                            object_repr     = force_str(publicacion),
                            action_flag     = CHANGE,
                            change_message  = 'Editada Publicacion (' + client_address + ')' )
                        return HttpResponseRedirect("/publicaciones?persona="+str(persona.id)+"&op="+request.POST['op'])
                    except Exception as e:
                        return HttpResponseRedirect("/publicaciones?action=edit&id="+str(publicacion.id)+"&error="+str(e)+"&op="+request.POST['op'])
                else:
                    return HttpResponseRedirect("/publicaciones?action=edit&id="+str(publicacion.id)+"&error=Llenar todos los datos del formulario&op="+request.POST['op'])


        return HttpResponseRedirect("/publicaciones")
    else:
        data = {'title': 'Publicaciones'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='add':
                data['title'] = 'Adicionar Publicacion'
                persona = Persona.objects.get(pk=request.GET['id'])
                data['profesor'] = persona
                form = PublicacionForm()
                data['op']=request.GET['op']
                data['form_autor'] = AutorForm(prefix='autor')
                data['form'] = form
                if 'error' in request.GET:
                    data['error']= request.GET['error']
                return render(request ,"pro_titulacion/addpublicacion.html" ,  data)
            elif action=='ver':
                data['title'] = 'Ver'
                try:
                    data={}
                    data['titulacion'] = LibroRevista.objects.get(pk=request.GET['id'])
                    return render(request ,"pro_titulacion/ver_detalle.html" ,  data)
                except Exception as ex :
                    return HttpResponse(json.dumps({'result':'bad', "error": str(ex)}),content_type="application/json")
            elif action=='edit':
                data['title'] = 'Editar'
                autor_codigos=[]
                autor_nombres=[]
                coautor_codigos=[]
                coautor_nombres=[]
                data['op']=request.GET['op']
                data['persona']=request.GET['persona']
                publicacion = LibroRevista.objects.get(pk=request.GET['id'])
                c=0
                for la in LibroPersona.objects.filter(libro_revista=publicacion,autor=True):
                    if la.persona:
                        autor_codigos.append((Profesor.objects.get(persona__id=la.persona.id).id))
                        autor_nombres.append((la.persona))
                    else:
                        if la.otros != "" :
                            autor_codigos.append((la.otros))
                            autor_nombres.append((la.otros))
                    # c=c+1
                #

                for lc in LibroPersona.objects.filter(libro_revista=publicacion,autor=False):
                    if lc.persona:
                        coautor_codigos.append((Profesor.objects.get(persona__id=lc.persona.id).id))
                        coautor_nombres.append((lc.persona))
                    else:
                        if lc.otros != "":
                            coautor_codigos.append((lc.otros))
                            coautor_nombres.append((lc.otros))
                if len(coautor_codigos) >0:
                    data['coautor_codigos']=coautor_codigos
                if len(coautor_nombres)>0:
                    data['coautor_nombres']=coautor_nombres
                if len(autor_codigos) >0 :
                    data['autor_codigos']=autor_codigos
                if len(autor_nombres) >0:
                    data['autor_nombres']=autor_nombres

                initial = model_to_dict(publicacion)
                form = PublicacionForm(initial=initial)
                data['form'] = form
                data['form_autor'] = AutorForm(prefix='autor')
                data['publicacion'] = publicacion
                if 'error' in request.GET:
                    data['error']= request.GET['error']
                return render(request ,"pro_titulacion/editpublicacion.html" ,  data)
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
            data['title'] = 'Revistas y Libros'
            search=None
            if  request.GET['op'] == 'A':
                persona = Persona.objects.get(usuario=request.user)
                if 's' in request.GET:
                    search = request.GET['s']
                    revistalibro = LibroRevista.objects.filter(Q(libropersona__persona__nombres__icontains=search) |
                                                         Q(libropersona__persona__apellido1__icontains=search) |
                                                         Q(libropersona__persona__apellido2__icontains=search) |
                                                         Q(libropersona__persona__cedula__icontains=search) |
                                                         Q(libropersona__persona__pasaporte__icontains=search))
                else:
                    revistalibro = LibroRevista.objects.filter()
                data['personal'] = persona
            else:
                persona = Persona.objects.get(pk=request.GET['persona'])
                revistalibro = LibroRevista.objects.filter(libropersona__persona=persona)
                data['personal'] = persona

            paging = MiPaginador(revistalibro, 30)
            p = 1
            try:
                if 'page' in request.GET:
                    p = int(request.GET['page'])
                    paging = MiPaginador(revistalibro, 30)
                page = paging.page(p)
            except Exception as ex:
                page = paging.page(1)
            data['paging'] = paging
            data['rangospaging'] = paging.rangos_paginado(p)
            data['page'] = page
            data['op']=request.GET['op']
            data['revistalibro'] = page.object_list
            data['search'] = search if search else ""


            return render(request ,"pro_titulacion/publicaciones.html" ,  data)
