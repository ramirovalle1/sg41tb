from datetime import datetime
from decimal import Decimal
import json
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.forms import model_to_dict
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
from sga.commonviews import addUserData, ip_client_address
from sga.forms import InscripcionGuarderiaForm, DetalleInscripcionGuarderiaForm, RegistroGuarderiaForm
from sga.models import InscripcionGuarderia, DetalleInscGuarderia, Inscripcion, Matricula, IngresoGuarderia, SalidaGuarderia

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
def view(request):
    if request.method=='POST':
        action = request.POST['action']
        if action == 'salida':
            try:
                ingreso = IngresoGuarderia.objects.get(pk=request.POST['id'])
                salida = SalidaGuarderia(ingreso=ingreso,
                                         horasalida=datetime.now().time(),
                                         fechasalida=datetime.now().date(),
                                         observacion=request.POST['obs'])
                salida.save()
            except:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
            if InscripcionGuarderia.objects.filter(identificacion=request.POST['iden']).exists():
                salida.retiraresponsable = True
                salida.save()

            return HttpResponse(json.dumps({"result":"ok","id":str(ingreso.detalle.id)}),content_type="application/json")



        elif action == 'consulta':
            ingreso = IngresoGuarderia.objects.get(pk=request.POST['id'])
            if InscripcionGuarderia.objects.filter(Q(inscripcion__persona__cedula=request.POST['ident']) | Q(identificacion=request.POST['ident']) | Q(inscripcion__persona__pasaporte=request.POST['ident'])).exists() and InscripcionGuarderia.objects.filter(inscripcion=ingreso.detalle.inscripcionguarderia.inscripcion):
                if InscripcionGuarderia.objects.filter(identificacion=request.POST['ident']).exists():
                    ins = InscripcionGuarderia.objects.filter(identificacion=request.POST['ident'])[:1].get()
                    persona = ins.responsable
                elif InscripcionGuarderia.objects.filter(inscripcion__persona__cedula=request.POST['ident']).exists():
                    ins = InscripcionGuarderia.objects.filter(inscripcion__persona__cedula=request.POST['ident'])[:1].get()
                    persona = ins.inscripcion.persona.nombre_completo()
                else:
                    ins = InscripcionGuarderia.objects.filter(inscripcion__persona__pasaporte=request.POST['ident'])[:1].get()
                    persona=ins.inscripcion.persona.nombre_completo()

                return HttpResponse(json.dumps({"result":"ok","nombre":str(persona)}),content_type="application/json")
            else:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
    else:
        data = {'title': 'Inscripcion Guarderia '}
        addUserData(request, data)
        if 'action' in request.GET:
            action = request.GET['action']


        else:
            todos = None
            search = None
            if 's' in request.GET:
                search = request.GET['s']
            if 'id' in request.GET:
                ingresos = IngresoGuarderia.objects.filter(detalle__id=request.GET['id'])
                data['id']=request.GET['id']
            elif search:
                ingresos = IngresoGuarderia.objects.filter(Q(detalle__inscripcionguarderia__inscripcion__persona__nombres__icontains=search) | Q(detalle__inscripcionguarderia__inscripcion__persona__apellido1__icontains=search) | Q(detalle__nombre__icontains=search)  | Q(detalle__inscripcionguarderia__inscripcion__persona__apellido2__icontains=search) | Q(detalle__inscripcionguarderia__inscripcion__persona__cedula__icontains=search)).order_by('-fechaentrada')
            else:
                ingresos = IngresoGuarderia.objects.all().order_by('-fechaentrada')
            paging = MiPaginador(ingresos, 30)
            p = 1
            try:
                if 'page' in request.GET:
                    p = int(request.GET['page'])
                    # if band==0:
                    #     inscripciones = Inscripcion.objects.all().order_by('persona__apellido1')
                    paging = MiPaginador(ingresos, 30)
                page = paging.page(p)
            except Exception as ex:
                page = paging.page(1)
            data['paging'] = paging
            data['rangospaging'] = paging.rangos_paginado(p)
            data['page'] = page
            data['search'] = search if search else ""
            data['todos'] = todos if todos else ""
            data['ingresos'] = page.object_list
            return render(request ,"guarderia/registroguarderia.html" ,  data)

