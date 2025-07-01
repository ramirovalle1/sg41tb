from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Avg
from django.db.models.query_utils import Q
from django.forms.models import model_to_dict
from django.http import HttpResponseRedirect
from django.shortcuts import render, render
from django.template.context import RequestContext
from django.template.loader import get_template
from decorators import secure_module
from settings import NOTA_PARA_APROBAR, ASIST_PARA_APROBAR, ASIST_PARA_SEGUIR, PORCIENTO_NOTA1, PORCIENTO_NOTA2, PORCIENTO_NOTA3, PORCIENTO_NOTA4, PORCIENTO_NOTA5, NOTA_ESTADO_APROBADO, NOTA_ESTADO_REPROBADO, NOTA_ESTADO_EN_CURSO, NOTA_ESTADO_SUPLETORIO, NOTA_PARA_SUPLET, MODELO_EVALUACION, EVALUACION_IAVQ, EVALUACION_ITB, VALIDAR_ASISTENCIAS, EVALUACION_ITS, EVALUACION_TES, CENTRO_EXTERNO, EVALUACION_IGAD, EVALUACION_CASADE
from sga.commonviews import addUserData
from sga.forms import NotaIAVQForm
from sga.models import Profesor, Materia, Matricula, LeccionGrupo, MateriaAsignada, NotaIAVQ, EvaluacionIAVQ2, RecordAcademico,Inscripcion,\
     SolicitudEstudiante,RequerimientoSoporte,Persona

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
            if action=='editnota':
                materiaasignada = MateriaAsignada.objects.get(pk=request.POST['id'])
                tipo = int(request.POST['tipo'])
                evaluacion = materiaasignada.evaluacion()

                if tipo==1:
                    notaiavq = evaluacion.n1
                else:
                    notaiavq = evaluacion.n2

                f = NotaIAVQForm(request.POST, initial=notaiavq)
                if f.is_valid():
                    notaiavq.p1=f.cleaned_data['p1']
                    notaiavq.p2=f.cleaned_data['p2']
                    notaiavq.p3=f.cleaned_data['p3']
                    notaiavq.p4=f.cleaned_data['p4']
                    notaiavq.p5=f.cleaned_data['p5']
                    notaiavq.save()

                    evaluacion.nota_n3()
                    evaluacion.actualiza_estado()
                    return HttpResponseRedirect("/cons_alumnos?alumno="+str(materiaasignada.matricula_id))

            elif action=='otrasnotas':
                materiaasignada = MateriaAsignada.objects.get(pk=request.POST['id'])
                materiasasignadas = MateriaAsignada.objects.filter(matricula=materiaasignada.matricula).exclude(id=materiaasignada.id)
                tipo_num = int(request.POST['tipo_num'])
                val = float(request.POST['valor'])

                evaluacion = materiaasignada.evaluacion()

                if tipo_num == 3:
                    evaluacion.pi = val
                    evaluacion.nota_n3()
                    evaluacion.actualiza_estado()

                    if materiaasignada.materia.rectora:
                        #Este codigo sirve para escribir la misma nota del P.I a todas las materias del nivel de ese alumno y actualizarle ESTADO a c/u, no tener en cuenta la validacion del PI, pq solo es en la rectora
                        for materiaasignada2 in materiasasignadas:
                            evaluac = materiaasignada2.evaluacion()
                            evaluac.pi = val
                            evaluac.nota_n3()
                            evaluac.actualiza_estado()


                elif tipo_num == 4:
                    materiaasignada.supletorio = evaluacion.su = val
                    materiaasignada.notafinal= evaluacion.nota_final()

                    if evaluacion.n1.nota and evaluacion.n2.nota and evaluacion.su:
                        if evaluacion.nota_final()>=NOTA_PARA_APROBAR:
                            evaluacion.estado_id = NOTA_ESTADO_APROBADO
                        else:
                            evaluacion.estado_id = NOTA_ESTADO_REPROBADO

                    if not evaluacion.su:
                        if evaluacion.n1.nota and evaluacion.n2.nota and evaluacion.pi:
                            if evaluacion.nota_final()>=NOTA_PARA_APROBAR and materiaasignada.porciento_asistencia()>=ASIST_PARA_APROBAR:
                                evaluacion.estado_id = NOTA_ESTADO_APROBADO
                            if (ASIST_PARA_SEGUIR <= materiaasignada.porciento_asistencia() < ASIST_PARA_APROBAR) or (NOTA_PARA_SUPLET<=evaluacion.nota_final()<NOTA_PARA_APROBAR) or (evaluacion.pi<NOTA_PARA_APROBAR):
                                evaluacion.estado_id = NOTA_ESTADO_SUPLETORIO
                            if evaluacion.nota_final()<NOTA_PARA_SUPLET or materiaasignada.porciento_asistencia()<ASIST_PARA_SEGUIR:
                                evaluacion.estado_id = NOTA_ESTADO_REPROBADO
                        else:
                            evaluacion.estado_id = NOTA_ESTADO_EN_CURSO

                    evaluacion.actualiza_estado()
                    materiaasignada.save()

                return HttpResponseRedirect("/cons_alumnos?alumno="+str(materiaasignada.matricula_id))

            return HttpResponseRedirect("/cons_alumnos")


    else:
        data = {'title': 'Evaluaciones por Alumnos'}
        addUserData(request,data)

        if 'action' in request.GET:
            action = request.GET['action']
            if action=='segmento':
                data = {'title': 'Consulta de Alumnos'}
                matricula = Matricula.objects.get(pk=request.GET['id'])
                materiasAsignadas = matricula.materiaasignada_set.all().order_by('materia__asignatura__nombre')

                data['promedio_notas'] = matricula.materiaasignada_set.filter(notafinal__gt=0).aggregate(Avg('notafinal'))['notafinal__avg']
                data['promedio_asistencias'] = matricula.materiaasignada_set.filter(asistenciafinal__gt=0).aggregate(Avg('asistenciafinal'))['asistenciafinal__avg']
                data['materiasasignadas'] = materiasAsignadas
                data['matricula'] = matricula
                data['records'] = RecordAcademico.objects.filter(inscripcion=matricula.inscripcion,aprobada=False)
                data['MODELO_EVALUATIVO'] = [MODELO_EVALUACION, EVALUACION_IAVQ, EVALUACION_ITB, EVALUACION_ITS, EVALUACION_TES, EVALUACION_IGAD, EVALUACION_CASADE]
                data['valida_asistencia'] = VALIDAR_ASISTENCIAS
                data['nota_para_aprobar'] = NOTA_PARA_APROBAR
                data['asistencia_para_aprobar'] = ASIST_PARA_APROBAR
                data['centroexterno'] = CENTRO_EXTERNO
                return render(request ,"cons_alumnos/segmentobs.html" ,  data)
            if action=='segmento2':
                matricula= Matricula.objects.get(pk=request.GET['id'])
                data['matricula'] =matricula
                data['inscripcion'] =matricula.inscripcion
                data['op']=1
                return render(request ,"cons_alumnos/alumnosbs.html" ,  data)

            elif action == 'versolicitudes':
                if request.GET['id']:
                    data['title'] = 'Solicitudes del Alumno'
                    inscripcion = request.GET['id']
                    if Inscripcion.objects.filter(pk=inscripcion).exists():
                        inscripcion = Inscripcion.objects.get(pk=inscripcion)
                        solicitudes=SolicitudEstudiante.objects.filter(inscripcion=inscripcion,solicitud__libre=True).order_by('-fecha')
                        data['solicitudes'] = solicitudes
                        data['inscripcion']=inscripcion
                        data['matricula']=Matricula.objects.filter(inscripcion=inscripcion,nivel__cerrado=False)[:1].get()
                        return render(request ,"cons_alumnos/cons_solicitudes.html" ,  data)

            elif action == 'vermesaayuda':
                if request.GET['id']:
                    data['title'] = 'Requerimientos en Mesa de Ayuda'
                    inscripcion = request.GET['id']
                    if Inscripcion.objects.filter(pk=inscripcion).exists():
                        inscripcion = Inscripcion.objects.get(pk=inscripcion)
                        persona = Persona.objects.get(pk=inscripcion.persona.id)
                        requerimientos=RequerimientoSoporte.objects.filter(persona=persona).order_by('-fecha')

                        #data['requerimientos'] = requerimientos
                        data['inscripcion']=inscripcion
                        data['matricula']=Matricula.objects.filter(inscripcion=inscripcion,nivel__cerrado=False)[:1].get()
                        paging = MiPaginador(requerimientos, 30)
                        p=1
                        try:
                            if 'page' in request.GET:
                                p = int(request.GET['page'])
                            page = paging.page(p)
                        except:
                            page = paging.page(1)
                        data['paging'] = paging
                        data['page'] = page
                        data['rangospaging'] = paging.rangos_paginado(p)

                        data['requerimientos'] = page.object_list
                        return render(request ,"cons_alumnos/cons_requerimientos.html" ,  data)

            elif action=='search':
                search = request.GET['term']
                data = {}

                if ' ' in search:
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')
                    if len(ss)>1:
                        data['matriculas'] = Matricula.objects.filter(Q(inscripcion__persona__apellido1__icontains=ss[0]) & Q(inscripcion__persona__apellido2__icontains=ss[1]),nivel__cerrado=False).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')
                    else:
                        data['matriculas'] = Matricula.objects.filter(inscripcion__persona__cedula__icontains=ss,nivel__cerrado=False).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')
                else:
                    data['matriculas'] = Matricula.objects.filter(Q(inscripcion__persona__nombres__icontains=search) | Q(inscripcion__persona__apellido1__icontains=search) | Q(inscripcion__persona__apellido2__icontains=search) | Q(inscripcion__persona__cedula__icontains=search) | Q(inscripcion__persona__pasaporte__icontains=search), nivel__cerrado=False).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')
                return render(request ,"cons_alumnos/selector.html" ,  data)

            elif action=='clases':
                data['title'] = 'Clases del Docente'
                profesor = Profesor.objects.get(pk=request.GET['p'])
                materia = Materia.objects.get(pk=request.GET['id'])
                matricula = Matricula.objects.get(pk=request.GET['m'])

                leccionesGrupo = LeccionGrupo.objects.filter(materia__nivel__periodo__activo=True,lecciones__clase__materia=materia).order_by('-fecha', '-horaentrada')

                paging = Paginator(leccionesGrupo, 50)
                p=1
                try:
                   if 'page' in request.GET:
                       p = int(request.GET['page'])
                   page = paging.page(p)
                except:
                    page = paging.page(1)
                data['paging'] = paging
                data['page'] = page
                data['leccionesgrupo'] = page.object_list
                data['profesor'] = profesor
                data['matricula'] = matricula
                data['materia'] = materia
                return render(request ,"cons_alumnos/clasesbs.html" ,  data)

            elif action=='editnota':
                data['title'] = 'Evaluacion del Alumno'
                materiaasignada = MateriaAsignada.objects.get(pk=request.GET['id'])
                profesor = Profesor.objects.get(persona=data['persona'])
                tipo_nota = int(request.GET['n'])

                evaluacion = materiaasignada.evaluacion()
                if tipo_nota==1:
                    NotasIavq = evaluacion.n1
                else:
                    NotasIavq = evaluacion.n2

                initial = model_to_dict(NotasIavq)
                data['evaluacion'] = evaluacion
                data['notaiavq'] = NotasIavq
                data['form'] = NotaIAVQForm(initial)

                data['materiaasignada'] = materiaasignada
                data['profesor'] = profesor
                data['tipo'] = tipo_nota

                data['porciento_p1'] = PORCIENTO_NOTA1
                data['porciento_p2'] = PORCIENTO_NOTA2
                data['porciento_p3'] = PORCIENTO_NOTA3
                data['porciento_p4'] = PORCIENTO_NOTA4
                data['porciento_p5'] = PORCIENTO_NOTA5

                return render(request ,"cons_alumnos/editnotabs.html" ,  data)

            elif action=='otrasnotas':
                data['title'] = 'Evaluacion del Alumno'
                materiaasignada = MateriaAsignada.objects.get(pk=request.GET['id'])
                profesor = ", ".join([x.profesor.persona.nombre_completo() for x in materiaasignada.materia.profesormateria_set.all()])
                evaluacion = materiaasignada.evaluacion()

                tipo_nota = int(request.GET['n'])


                if tipo_nota == 3:
                    data['tipo_num'] = 3
                    data['tipo'] = 'Proyecto Integrador'
                    data['valor'] = evaluacion.pi
                if tipo_nota == 4:
                    data['tipo_num'] = 4
                    data['tipo'] = 'Supletorio'
                    data['valor'] = evaluacion.su

                matricula = materiaasignada.matricula
                data['matricula'] = matricula
                data['materiaasignada'] = materiaasignada
                data['profesor'] = profesor
                return render(request ,"cons_alumnos/otranotabs.html" ,  data)

        else:
            data = {'title': 'Consulta de Alumnos'}
            addUserData(request,data)
            #profesor = Profesor.objects.get(persona=data['persona'])
            #data['profesor'] = profesor
            #data['materias'] = list(set([clase.materia for clase in profesor.clase_set.all()]))
            #data['matriculas'] = Matricula.objects.all().order_by('inscripcion__persona')
            if 'alumno' in request.GET:
                matricula = Matricula.objects.get(pk=request.GET['alumno'],liberada=False)
                materiasAsignadas = matricula.materiaasignada_set.all().order_by('materia__asignatura__nombre')
                data['materiasasignadas'] = materiasAsignadas
                data['matricula'] = matricula
                data['MODELO_EVALUATIVO'] = [MODELO_EVALUACION, EVALUACION_IAVQ, EVALUACION_ITB, EVALUACION_ITS, EVALUACION_TES, EVALUACION_IGAD, EVALUACION_CASADE]
                data['listadoprecargado'] = get_template("cons_alumnos/segmentobs.html").render(RequestContext(request,data))
            return render(request ,"cons_alumnos/alumnosbs.html" ,  data)