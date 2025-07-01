import csv
from datetime import datetime, timedelta
import json
import os
import urllib
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Avg
from django.db.models.aggregates import Sum
from django.db import transaction
from django.db.models.query_utils import Q
from django.forms.models import model_to_dict
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.utils.encoding import force_str
from django.template import RequestContext
import sys
from decorators import secure_module
from settings import CENTRO_EXTERNO, RUBRO_TIPO_OTRO_MODULO_INTERNO, RUBRO_TIPO_OTRO_INSCRIPCION, DEFAULT_PASSWORD, PROFESORES_GROUP_ID, ALUMNOS_GROUP_ID, UTILIZA_GRUPOS_ALUMNOS, REPORTE_CERTIFICADO_INSCRIPCION, EMAIL_ACTIVE, EVALUACION_ITB, REGISTRO_HISTORIA_NOTAS, NOTA_ESTADO_EN_CURSO, GENERAR_RUBROS_PAGO, GENERAR_RUBRO_INSCRIPCION, GENERAR_RUBRO_INSCRIPCION_MARGEN_DIAS, MODELO_EVALUACION, EVALUACION_IAVQ, EVALUACION_ITS, UTILIZA_NIVEL0_PROPEDEUTICO, TIPO_PERIODO_PROPEDEUTICO, NOTA_ESTADO_APROBADO, UTILIZA_FICHA_MEDICA, EVALUACION_TES, CORREO_INSTITUCIONAL, USA_CORREO_INSTITUCIONAL, INSCRIPCION_CONDUCCION,TIPO_AYUDA_FINANCIERA, URL_PRE_INSCRIPCION, RUTA_PRE_INSCRIPCION
from sga.alu_malla import aprobadaAsignatura
from sga.commonviews import addUserData, ip_client_address
from sga.docentes import calculate_username
from sga.forms import PersonaForm, InscripcionForm, RecordAcademicoForm, HistoricoRecordAcademicoForm, HistoriaNivelesDeInscripcionForm, CargarFotoForm, EmpresaInscripcionForm, EstudioInscripcionForm, DocumentoInscripcionForm, ActividadesInscripcionForm, PadreClaveForm, ConvalidacionInscripcionForm, HistoricoNotasITBForm, GraduadoDatosForm, EgresadoForm, InscripcionSenescytForm, RetiradoMatriculaForm, InscripcionCextForm, BecarioForm, InscripcionPracticaForm, ObservacionInscripcionForm, ProcesoDobeForm,  ActivaInactivaUsuarioForm, MatriculaBecaForm,InscripcionCextForm, InscripcionReferidoForm, CitaForm
from sga.models import CitaLlamada,RegistroSeguimiento
from sga.tasks import gen_passwd

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
@transaction.atomic()

def view(request):
    if request.method=='POST':
        action = request.POST['action']
        if action=='inscribir':
            pass


    else:
        data = {'title': 'Listado de Citas'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if  action == 'atender':
                try:
                    cita =CitaLlamada.objects.get(pk=request.GET['id'])
                    asistio = False
                    if request.GET['asistio'] == 'true':
                        asistio = True

                    cita.asistio = False
                    cita.observacion = request.GET['obs']
                    cita.usuario=request.user
                    cita.fechaasistencia = datetime.now()
                    cita.save()

                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

                return HttpResponseRedirect("/cita")

        else:
            try:
                hoy = str(datetime.date(datetime.now()))
                search = None
                todos = None
                activos = None
                inactivos = None
                reg=[]
                cit=[]

                if 's' in request.GET:
                    search = request.GET['s']

                if 't' in request.GET:
                    todos = request.GET['t']
                if search:
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')
                    if len(ss)==1:
                        registro = CitaLlamada.objects.filter(Q(registro__nombres__icontains=search) | Q(registro__apellidos__icontains=search) | Q(registro__identificacion__icontains=search)).order_by('-fecha','registro__apellidos','registro__nombres')
                    else:
                        registro = CitaLlamada.objects.filter(Q(registro__nombres__icontains=ss[0]) & Q(registro__apellidos__icontains=ss[1])).order_by('-fecha','registro__apellidos','registro__nombres')

                else:

                    registro =CitaLlamada.objects.filter().order_by('-fecha')
                for c in registro:
                    if not c.registro.id in reg  :
                        reg.append(c.registro.id)
                        cit.append(c.id)

                citas = CitaLlamada.objects.filter(id__in=cit).order_by('-fecha','asistio')


                paging = MiPaginador(citas, 30)
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
                data['search'] = search if search else ""
                data['citas'] = page.object_list
                data['form'] = CitaForm()
                data['p']=request.GET['p']
                return render(request ,"registros/cita.html" ,  data)

            except Exception as e:
                return HttpResponseRedirect("/cita")