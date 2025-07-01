from datetime import datetime, timedelta
from decimal import Decimal
import json
import os
from django.contrib.admin.models import LogEntry, ADDITION, DELETION, CHANGE
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import Q
from django.db.transaction import rollback
from django.forms.models import model_to_dict
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template.context import RequestContext
from django.utils.encoding import force_str
from decorators import secure_module
from settings import NOTA_ESTADO_EN_CURSO
from sga.models import MateriaAsignada, EliminacionMatricula, elimina_tildes, DetalleEliminaMatricula, EvaluacionITB,TipoEstado
from sga.commonviews import addUserData, ip_client_address
from django.core.paginator import Paginator

def convertir_fecha(s):
    return datetime(int(s[6:10]), int(s[3:5]), int(s[0:2]))

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
    """
    :param request:
    :return:
    """
    if request.method=='POST':
        try:
            if 'action' in request.POST:
                action = request.POST['action']

                if action == 'copiarnota':
                    detallenotas = DetalleEliminaMatricula.objects.get(pk=request.POST['id'])
                    eliminadamat = EliminacionMatricula.objects.get(pk=detallenotas.eliminadamatriculada.id)
                    estudiante = eliminadamat.inscripcion
                    try:
                        if estudiante.matriculado():
                            mat = estudiante.matricula()
                            if MateriaAsignada.objects.filter(matricula=mat,materia__asignatura=detallenotas.asignatura).exists():
                                matasignada = MateriaAsignada.objects.filter(matricula=mat,materia__asignatura=detallenotas.asignatura)[:1].get()
                                if EvaluacionITB.objects.filter(materiaasignada=matasignada).exists():
                                    evalua = EvaluacionITB.objects.filter(materiaasignada=matasignada)[:1].get()
                                    evalua.n1 = detallenotas.n1
                                    evalua.n2 = detallenotas.n2
                                    evalua.n3 = detallenotas.n3
                                    evalua.n4 = detallenotas.n4
                                    evalua.examen = detallenotas.examen
                                    evalua.recuperacion = detallenotas.recuperacion
                                    evalua.save()
                                    evalua.actualiza_estado_nueva()

                                    detallenotas.traspaso = True
                                    detallenotas.save()
                                else:
                                    estado = TipoEstado.objects.get(pk=NOTA_ESTADO_EN_CURSO)
                                    evalua = EvaluacionITB(materiaasignada=matasignada,
                                             n1 = detallenotas.n1,
                                             n2 = detallenotas.n2,
                                             n3 = detallenotas.n3,
                                             n4 = detallenotas.n4,
                                             examen = detallenotas.examen,
                                             recuperacion = detallenotas.recuperacion,
                                             estado=estado)

                                    evalua.save()
                                    evalua.actualiza_estado_nueva()

                                    detallenotas.traspaso = True
                                    detallenotas.save()

                                # Log de copia de notas a nueva asignacion
                                LogEntry.objects.log_action(
                                    user_id=request.user.pk,
                                    content_type_id=ContentType.objects.get_for_model(detallenotas).pk,
                                    object_id=detallenotas.id,
                                    object_repr=force_str(detallenotas),
                                    action_flag=ADDITION,
                                    change_message='Copia de Nota a nueva asignatura')

                                return HttpResponse(json.dumps({"result": "ok","url": "/matriculas_eliminadas?action=detallematerias&id=" + str(eliminadamat.id)}), content_type="application/json")
                            else:
                                mensaje = 'Materia no se encuentra asignada'
                                return HttpResponse(json.dumps({'result': 'bad', 'message': str(mensaje)}),content_type="application/json")
                    except Exception as e:
                        print(e)
                        return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}),content_type="application/json")




            return HttpResponseRedirect("/?info="+request.POST['action'])
        except Exception as e:
            return HttpResponseRedirect("/?info="+str(e))
    else:
        try:
            data = {'title': 'Matriculas de Alumnos Eliminadas'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']

                if action == 'detallematerias':
                    data['title'] = 'Detalle de Materias Nivel Eliminado'
                    detalleelimatricula = DetalleEliminaMatricula.objects.filter(
                        eliminadamatriculada=request.GET['id']).order_by('asignatura__nombre')
                    data['elimatricula'] = EliminacionMatricula.objects.get(pk=request.GET['id'])
                    if 'error' in request.GET:
                        data['error'] = request.GET['error']
                    data['detalleelimatricula'] = detalleelimatricula
                    return render(request ,"matriculaseliminadas/detallenotas.html" ,  data)

            else:
                search = None
                todos = None

                if 's' in request.GET:
                    search = request.GET['s']

                if todos:
                    eliminadosmatriculas = EliminacionMatricula.objects.filter(fecha__gte='2020-06-23').order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')[:100]
                    #eliminadosmatriculas = EliminacionMatricula.objects.filter().exclude(nivel__cerrado=False).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')[:100]

                if search:
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')
                    if len(ss)==1:
                        eliminadosmatriculas = EliminacionMatricula.objects.filter(Q(inscripcion__persona__nombres__icontains=search) | Q(inscripcion__persona__apellido1__icontains=search) | Q(inscripcion__persona__apellido2__icontains=search) | Q(inscripcion__persona__cedula__icontains=search) | Q(inscripcion__persona__pasaporte__icontains=search)).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')
                    else:
                        eliminadosmatriculas = EliminacionMatricula.objects.filter((Q(inscripcion__persona__apellido1__icontains=ss[0]) & Q(inscripcion__persona__apellido2__icontains=ss[1]))).order_by('inscripcion__persona__apellido1', 'inscripcion__persona__apellido2')
                else:
                    #eliminadosmatriculas= EliminacionMatricula.objects.filter().exclude(nivel__cerrado=False).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')
                    eliminadosmatriculas= EliminacionMatricula.objects.filter(fecha__gte='2020-06-23').order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')

                paging = MiPaginador(eliminadosmatriculas, 30)
                p = 1
                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                    page = paging.page(p)
                except:
                    page = paging.page(1)
                data['paging'] = paging
                data['page'] = page
                data['rangospaging'] = paging.rangos_paginado(p)
                data['search'] = search if search else ""
                data['todos'] = todos if todos else ""
                data['eliminadosmatriculas'] = page.object_list
                return render(request ,"matriculaseliminadas/matriculaseliminadasbs.html" ,  data)

        except Exception as e:
            return HttpResponseRedirect('/?info='+str(e))