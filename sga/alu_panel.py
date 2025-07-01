from datetime import datetime, timedelta
import json
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from decorators import secure_module
from settings import REPORTE_CRONOGRAMA_MATERIAS, VALIDAR_ENTRADA_SISTEMA_CON_DEUDA, ASIGNATURA_PRACTICA_CONDUCCION, INSCRIPCION_CONDUCCION, TIPO_OTRO_RUBRO
from sga.commonviews import addUserData,ip_client_address
from sga.models import Inscripcion, Panel, Matricula, InscripcionPanel, Rubro, RubroOtro, TipoOtroRubro,RubroInscripcion,RubroMatricula
from sga.forms import TituloForm
from django.utils.encoding import force_str
from django.contrib.admin.models import LogEntry, CHANGE
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
def view(request):
    if request.method=='POST':
        if 'action' in request.POST:
            action = request.POST['action']

            if action =='consulta_pago':
                try:
                    matricula = Matricula.objects.get(pk=request.POST['matricula'])
                    # if (InscripcionSeminario.objects.filter(matricula = matricula).count()  +1)% 3 == 0 and InscripcionSeminario.objects.filter(matricula = matricula).count() > 1:
                    if RubroMatricula.objects.filter(rubro__inscripcion = matricula.inscripcion,rubro__cancelado=True).exists() or  not RubroMatricula.objects.filter(rubro__inscripcion = matricula.inscripcion).exists():
                            return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
                except Exception as ex:
                    pass
    else:
         if 'action' in request.GET:
                action = request.GET['action']
                if action == 'matricularse':
                    try:
                        matricula = Matricula.objects.get(pk=request.GET['matricula'])
                        panel = Panel.objects.get(pk=request.GET['id'])
                        if panel.inscritos() < panel.capacidad:
                            if not InscripcionPanel.objects.filter(panel=panel,matricula = matricula).exists():
                                ipanel = InscripcionPanel(panel=panel,
                                                                  matricula = matricula,
                                                                  fecha=datetime.now().date())
                                ipanel.save()

                                 # Log Editar Inscripcion
                                client_address = ip_client_address(request)
                                LogEntry.objects.log_action(
                                    user_id         = request.user.pk,
                                    content_type_id = ContentType.objects.get_for_model(ipanel).pk,
                                    object_id       =ipanel.id,
                                    object_repr     = force_str(ipanel),
                                    action_flag     = CHANGE,
                                    change_message  =  "Seleccionado Panel  " +  '(' + client_address + ')' )
                    except Exception as ex:
                        pass

                return  HttpResponseRedirect('/alu_panel')

         else:
            data = {'title': ' Paneles'}
            addUserData(request, data)

            try:
                inscripcion = Inscripcion.objects.get(persona=data['persona'])

                #Comprobar que no tenga deudas para que no pueda usar el sistema
                if VALIDAR_ENTRADA_SISTEMA_CON_DEUDA and inscripcion.tiene_deuda():
                    return HttpResponseRedirect("/")

                #Comprobar que el alumno este matriculado
                if not inscripcion.matriculado():
                    return HttpResponseRedirect("/?info=Ud. aun no ha sido matriculado")
                matricula = inscripcion.matricula_set.filter(nivel__periodo__activo=True, nivel__cerrado=False)[:1].get()

                search = ""

                if 's' in request.GET:
                    search = request.GET['s']

                if search:
                    panel = Panel.objects.filter(nombre__icontains=search,permisopanel__inscripcion=inscripcion).order_by('id')
                else:
                    panel = Panel.objects.filter(permisopanel__inscripcion=inscripcion).order_by('id')

                if 'miscursos' in request.GET:
                    mat = Matricula.objects.get(pk=request.GET['miscursos'])
                    i = InscripcionPanel.objects.filter(matricula__inscripcion = mat.inscripcion).values('panel__id')
                    panel = Panel.objects.filter(id__in=i).order_by('id')
                    search = ' '



                data['matricula'] = matricula
                paging = MiPaginador(panel, 30)
                p = 1
                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                        # if band==0:
                        #     inscripciones = Inscripcion.objects.all().order_by('persona__apellido1')
                        paging = MiPaginador(panel, 30)
                    page = paging.page(p)
                except Exception as ex:
                    page = paging.page(1)


                data['paging'] = paging
                data['form'] = TituloForm()
                data['rangospaging'] = paging.rangos_paginado(p)
                data['page'] = page
                data['panel'] = page.object_list
                data['hoy'] = datetime.today()
                data['search'] = search if search else ""

                return render(request ,"alu_panel/panel.html" ,  data)
            except Exception as ex:
                return HttpResponseRedirect("/")