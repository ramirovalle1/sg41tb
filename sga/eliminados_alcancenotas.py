from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from django.template.context import RequestContext
import requests
from decorators import secure_module
from settings import REGISTRO_HISTORIA_NOTAS, VALIDAR_ENTRADA_SISTEMA_CON_DEUDA,VALIDA_DEUDA_EXAM_ASIST, DEFAULT_PASSWORD, INSCRIPCION_CONDUCCION, \
     NOTA_ESTADO_EN_CURSO, ID_TIPO_ESPECIE_REG_NOTA, DIAS_ESPECIE, NOTA_ESTADO_DERECHOEXAMEN, EMAIL_ACTIVE,MIN_APROBACION, MAX_APROBACION, MIN_RECUPERACION, \
     MAX_RECUPERACION, MIN_EXAMEN, MAX_EXAMEN, MIN_EXAMENRECUPERACION,PORCIENTO_NOTA1,PORCIENTO_NOTA2,PORCIENTO_NOTA3,PORCIENTO_NOTA4,PORCIENTO_NOTA5,\
     PORCIENTO_RECUPERACION, NOTA_ESTADO_REPROBADO, ESPECIE_ASENTAMIENTO_NOTA, ESPECIE_EXAMEN, ESPECIE_RECUPERACION, ESPECIE_MEJORAMIENTO, ASIST_PARA_APROBAR
from sga.commonviews import addUserData

from sga.forms import EvaluacionObservacionForm,AprobacionCambioNotaForm
from sga.models import Inscripcion, Profesor, Materia, MateriaAsignada, RubroEspecieValorada, Persona, \
    EvaluacionITB, EvaluacionAlcance, CodigoEvaluacion, Coordinacion, MotivoAlcance, ProfesorMateria
from django.db.models.query_utils import Q
from sga.tasks import plaintext2html,send_html_mail
from datetime import datetime, time, timedelta
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_str
import json
from sga.reportes import elimina_tildes


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
#@secure_module
def view(request):
    data = {'title': 'Registro Academico'}
    addUserData(request, data)
    if request.method=='POST':
        if 'action' in request.POST:
            action = request.POST['action']
            if action=='cambiodeestado':
                try:
                    if EvaluacionAlcance.objects.filter(materiaasignada=request.POST['matasignada']).exists():
                        evalua = EvaluacionAlcance.objects.filter(materiaasignada=request.POST['matasignada'])[:1].get()
                        evalua.eliminado=False
                        evalua.save()
                        # Log de Cambio de estado
                        LogEntry.objects.log_action(
                            user_id=request.user.pk,
                            content_type_id=ContentType.objects.get_for_model(evalua).pk,
                            object_id=evalua.id,
                            object_repr=force_str(evalua),
                            action_flag=CHANGE,
                            change_message='Cambio Alcance Activo')
                        datos = {"result": "ok"}
                        return HttpResponse(json.dumps(datos),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result": "bad", "error": str(ex)}),content_type="application/json")
    else:
        data = {'title': 'Evaluaciones por Alumnos'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
        else:
            data = {'title': 'Eliminados de Alcance Notas'}
            evaalcance = None
            mat = ''
            todos = None
            fechamax = datetime.now() - timedelta(days=DIAS_ESPECIE)
            data['aprobacionform'] = AprobacionCambioNotaForm()

            if 'profesorid' in request.GET:
                profesor = Profesor.objects.filter(pk=request.GET['profesorid'])[:1].get()
                data['profesor'] = profesor
                materiasid = ProfesorMateria.objects.filter(Q(profesor=profesor, materia__cerrado=True, materia__nivel__cerrado=False) | Q(profesor_aux=profesor.id, materia__cerrado=True, materia__nivel__cerrado=False)).distinct('materia').values('materia')
                data['materias'] = Materia.objects.filter(id__in=materiasid)
                evaalcance = EvaluacionAlcance.objects.filter(materiaasignada__materia__id__in=materiasid,materiaasignada__materia__nivel__cerrado=False,eliminado=True).order_by('materiaasignada__matricula__inscripcion__persona__apellido1','materiaasignada__matricula__inscripcion__persona__apellido2','materiaasignada__matricula__inscripcion__persona__nombres')
            if 'id' in request.GET:
                mat = request.GET['id']
                materia = Materia.objects.get(pk=mat)
                evaalcance = EvaluacionAlcance.objects.filter(materiaasignada__materia=materia,materiaasignada__materia__cerrado=True,materiaasignada__materia__nivel__cerrado=False,eliminado=True).order_by('materiaasignada__matricula__inscripcion__persona__apellido1','materiaasignada__matricula__inscripcion__persona__apellido2','materiaasignada__matricula__inscripcion__persona__nombres')
                data['mat'] = int(mat)
                data['materiaselec'] = materia
            elif 't' in request.GET:
                todos = request.GET['t']
                evaalcance = EvaluacionAlcance.objects.filter(materiaasignada__materia__cerrado=True,materiaasignada__materia__nivel__cerrado=False,eliminado=True).order_by('materiaasignada__matricula__inscripcion__persona__apellido1','materiaasignada__matricula__inscripcion__persona__apellido2','materiaasignada__matricula__inscripcion__persona__nombres')

            elif 'aprob' in request.GET:
                evaalcance = EvaluacionAlcance.objects.filter(aprobado=True,materiaasignada__materia__nivel__cerrado=False,eliminado=True).order_by('materiaasignada__matricula__inscripcion__persona__apellido1','materiaasignada__matricula__inscripcion__persona__apellido2','materiaasignada__matricula__inscripcion__persona__nombres')
                data['aprobadas'] = 'aprob'

            elif 'noaprob' in request.GET:
                evaalcance = EvaluacionAlcance.objects.filter(aprobado=False,materiaasignada__materia__nivel__cerrado=False,eliminado=True).order_by('materiaasignada__matricula__inscripcion__persona__apellido1','materiaasignada__matricula__inscripcion__persona__apellido2','materiaasignada__matricula__inscripcion__persona__nombres')
                data['noaprobadas'] = 'noaprob'

            elif 'noexa' in request.GET:
                evaalcance = EvaluacionAlcance.objects.filter(aprobadoex=False,materiaasignada__materia__nivel__cerrado=False,eliminado=True).order_by('materiaasignada__matricula__inscripcion__persona__apellido1','materiaasignada__matricula__inscripcion__persona__apellido2','materiaasignada__matricula__inscripcion__persona__nombres')
                data['noaprobexa'] = 'noexa'

            elif 'norec' in request.GET:
                evaalcance = EvaluacionAlcance.objects.filter(aprobadorec=False,materiaasignada__materia__nivel__cerrado=False,eliminado=True).order_by('materiaasignada__matricula__inscripcion__persona__apellido1','materiaasignada__matricula__inscripcion__persona__apellido2','materiaasignada__matricula__inscripcion__persona__nombres')
                data['noaprobrec'] = 'norec'

            else:
                if not evaalcance:
                    evaalcance = EvaluacionAlcance.objects.filter(materiaasignada__materia__cerrado=True,materiaasignada__materia__nivel__cerrado=False,eliminado=True).order_by('materiaasignada__matricula__inscripcion__persona__apellido1','materiaasignada__matricula__inscripcion__persona__apellido2','materiaasignada__matricula__inscripcion__persona__nombres')

                    data['todos'] = evaalcance

            paging = MiPaginador(evaalcance, 60)
            p = 1
            try:
                if 'page' in request.GET:
                    p = int(request.GET['page'])
                    paging = MiPaginador(evaalcance, 60)
                page = paging.page(p)
            except Exception as ex:
                page = paging.page(1)
            data['paging'] = paging
            data['rangospaging'] = paging.rangos_paginado(p)
            data['page'] = page
            data['evaalcance'] = page.object_list
            data['todos'] = todos if todos else ""
            data['encurso'] = NOTA_ESTADO_EN_CURSO
            data['examen'] = NOTA_ESTADO_DERECHOEXAMEN
            data['reprobado'] = NOTA_ESTADO_REPROBADO
            data['min_aproba'] = MIN_APROBACION
            data['max_aproba'] = MAX_APROBACION
            data['min_recupera'] = MIN_RECUPERACION
            data['max_recupera'] = MAX_RECUPERACION
            data['min_exa'] = MIN_EXAMEN
            data['max_exa'] = MAX_EXAMEN
            data['min_exarecupera'] = MIN_EXAMENRECUPERACION
            data['porcnota1'] = PORCIENTO_NOTA1
            data['porcnota2'] = PORCIENTO_NOTA2
            data['porcnota3'] = PORCIENTO_NOTA3
            data['porcnota4'] = PORCIENTO_NOTA4
            data['porcnota5'] = PORCIENTO_NOTA5
            data['porcrecupera'] = PORCIENTO_RECUPERACION
            data['asistencia_aprobar'] = ASIST_PARA_APROBAR
            return render(request ,"aprobacion_alcance_notas/eliminados_alcancebs.html" ,  data)
