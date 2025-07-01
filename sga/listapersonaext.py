from datetime import datetime
import json
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.utils.encoding import force_str
from decorators import secure_module
from settings import NOTA_PARA_EXAMEN_EXTERNO, NUMERO_PREGUNTA_EXTERNO, DEFAULT_PASSWORD
from sga.commonviews import addUserData, ip_client_address
from sga.models import PersonaExterna, PersonaExamenExt, ExamenExterno, DetalleExamenExt, DesactivaExterno, Inscripcion

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

__author__ = 'jurgiles'

@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    try:
        if request.method == 'POST':
            action = request.POST['action']
            if action == 'validoexamen':
                try:
                    personaexamen = PersonaExamenExt.objects.get(id=request.POST['idpersonaexam'])
                    if not personaexamen.valida:
                        if DEFAULT_PASSWORD == 'conduccion':
                            personasextr = PersonaExamenExt.objects.filter(valida=True,examenexterno=personaexamen.examenexterno,personaextern=personaexamen.personaextern).exclude(examenexterno=None)
                        else:
                            personasextr = PersonaExamenExt.objects.filter(valida=True,examenexterno=personaexamen.examenexterno,inscripcion=personaexamen.inscripcion)
                        for p in personasextr:
                            p.valida = False
                            p.save()
                        personaexamen.valida = True
                        puntaje = personaexamen.puntaje
                        mensaje = 'Activando Examen'
                    else:
                        personaexamen.valida = False
                        puntaje = 0
                        mensaje = 'Desactivando Examen'
                    personaexamen.save()

                    detvalidaexamen = DesactivaExterno(
                                        personaexamenext = personaexamen,
                                        observacion =request.POST['observacionvali'],
                                        usuario = request.user,
                                        fecha = datetime.now(),
                                        activo = personaexamen.valida)
                    detvalidaexamen.save()
                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de Graduar en Conduccion
                    LogEntry.objects.log_action(
                       user_id         = request.user.pk,
                       content_type_id = ContentType.objects.get_for_model(personaexamen).pk,
                       object_id       = personaexamen.id,
                       object_repr     = force_str(personaexamen),
                       action_flag     = CHANGE,
                       change_message  = mensaje+ ' de Grado de  Conduccion (' + client_address + ')' )

                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
        else:
            data = {"title": 'Lista de Personas Examenes'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']
                if action == 'personaexamen':
                    try:
                        data['DEFAULT_PASSWORD'] = DEFAULT_PASSWORD
                        if DEFAULT_PASSWORD == 'conduccion':
                            personaexterna = PersonaExterna.objects.get(pk=request.GET['id'])
                            if PersonaExamenExt.objects.filter(personaextern=personaexterna).exclude(examenexterno=None).exists():
                                data['personaexamenes'] = PersonaExamenExt.objects.filter(personaextern=personaexterna).exclude(examenexterno=None).order_by('examenexterno','comienza')
                                data['nota_examen']=NOTA_PARA_EXAMEN_EXTERNO
                                return render(request ,"examenexterno/detalleexamenexter.html" ,  data)
                        else:
                            if PersonaExamenExt.objects.filter(inscripcion__id=request.GET['id']).exists():
                                data['personaexamenes'] = PersonaExamenExt.objects.filter(inscripcion__id=request.GET['id']).order_by('examenexterno','comienza')
                                data['nota_examen']=NOTA_PARA_EXAMEN_EXTERNO
                                return render(request ,"examenexterno/detalleexamenexter.html" ,  data)

                    except Exception as ex:
                        return  HttpResponseRedirect("/listapersonaexter")
                elif action == 'detavaliexa':
                    try:
                        personaexamenexter = PersonaExamenExt.objects.get(pk=request.GET['id'])
                        if personaexamenexter.detalledesactiva():
                            data['detallevalida'] = personaexamenexter.detalledesactiva().order_by('fecha')
                            return render(request ,"examenexterno/detallevaliexamenexter.html" ,  data)

                    except Exception as ex:
                        return  HttpResponseRedirect("/listapersonaexter")

                elif action == "resultado":
                    try:
                        examenexterno = ExamenExterno.objects.get(id=request.GET['idexaext'])

                        if PersonaExamenExt.objects.filter(id=request.GET['id'],valida=True).exists():
                            personaexamenext = PersonaExamenExt.objects.filter(id=request.GET['id'],valida=True)[:1].get()
                            preguntaexamenext = DetalleExamenExt.objects.filter(personaexamenext=personaexamenext).order_by('id')



                            data['examenexterno'] = examenexterno

                            paging = MiPaginador(preguntaexamenext, NUMERO_PREGUNTA_EXTERNO)
                            p = 1
                            try:
                                if 'page' in request.GET:
                                    p = int(request.GET['page'])
                                page = paging.page(p)
                            except:
                                page = paging.page(1)
                            data['paging'] = paging
                            data['rangospaging'] = paging.rangos_paginado(p)
                            data['page'] = page
                            data['preguntaexamenext'] = page.object_list
                            data['personaexamenext'] = personaexamenext
                            data['DEFAULT_PASSWORD'] = DEFAULT_PASSWORD
                            data['NOTA_PARA_EXAMEN_EXTERNO'] = NOTA_PARA_EXAMEN_EXTERNO

                            return render(request ,"examenexterno/resultado.html" ,  data)
                        return HttpResponseRedirect('/examenexterno?info=Error Vuelva a Ingresar Especie')
                    except Exception as e:
                        return HttpResponseRedirect('/examenexterno?idexaext='+str(request.GET['idexaext']))
            else:
                search = None
                data['DEFAULT_PASSWORD'] = DEFAULT_PASSWORD
                if DEFAULT_PASSWORD == 'conduccion':
                    if search:
                        personaexternas = PersonaExterna.objects.filter(Q(nombres__icontains=search) | Q(numdocumento__icontains=search)).order_by('nombres')
                    else:
                        personaexternas = PersonaExterna.objects.all().order_by('nombres')
                else:
                    idinscr = PersonaExamenExt.objects.filter().distinct('inscripcion').values('inscripcion')
                    if search:
                        personaexternas = PersonaExterna.objects.filter(Q(nombres__icontains=search) | Q(numdocumento__icontains=search),id__in=idinscr).order_by('nombres')
                    else:
                        personaexternas = Inscripcion.objects.filter(id__in=idinscr)

                paging = MiPaginador(personaexternas, 30)
                p = 1
                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                        # if band==0:
                        #     inscripciones = Inscripcion.objects.all().order_by('persona__apellido1')
                        paging = MiPaginador(personaexternas, 30)
                    page = paging.page(p)
                except Exception as ex:
                    page = paging.page(1)

                data['paging'] = paging
                data['rangospaging'] = paging.rangos_paginado(p)
                data['page'] = page
                data['search'] = search if search else ""
                data['personaexternas'] = page.object_list
                if 'idpersonexter' in request.GET:
                    if DEFAULT_PASSWORD == 'conduccion':
                        data['personexter'] = PersonaExterna.objects.get(id=request.GET['idpersonexter'])
                    else:
                        data['personexter'] = Inscripcion.objects.get(id=request.GET['idpersonexter'])

                return render(request ,"examenexterno/listapersonas.html" ,  data)
    except Exception as ex:
        return HttpResponseRedirect('/?info='+str(ex))