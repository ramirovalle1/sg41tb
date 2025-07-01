from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Avg
from django.forms.models import model_to_dict
from django.http import HttpResponseRedirect
from django.shortcuts import render
from decorators import secure_module
from settings import EVALUACION_IAVQ, EVALUACION_ITB, MODELO_EVALUACION, EVALUACION_ITS, EVALUACION_IGAD, EVALUACION_TES, VALIDAR_ENTRADA_SISTEMA_CON_DEUDA, NOTA_PARA_APROBAR, \
     ASIST_PARA_APROBAR, ASIST_PARA_SEGUIR, EVALUACION_CASADE, VALIDAR_ASISTENCIAS,INSCRIPCION_CONDUCCION,MIN_EXAMEN, DEFAULT_PASSWORD
from sga.commonviews import addUserData
from sga.forms import NotaIAVQForm
from sga.models import Matricula, RecordAcademico, Inscripcion, Periodo, MateriaAsignada, NotaIAVQ, EvaluacionIAVQ2, Profesor, Materia, LeccionGrupo, ProfesorMateria, ClasesOnline


@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    data = {'title': ' Materias de Alumno'}
    addUserData(request, data)
    try:
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='friends':
                data['title'] = 'Alumnos de mi Clase'
                matricula = Matricula.objects.get(pk=request.GET['id'])
                materia = Materia.objects.get(pk=request.GET['m'])
                materiaasignadas = MateriaAsignada.objects.filter(materia = materia).exclude(matricula=matricula)

                data['matricula'] = matricula
                data['materia'] = materia
                data['materiasasignadas'] = materiaasignadas.order_by('matricula__inscripcion__persona__nombres','matricula__inscripcion__persona__apellido1','matricula__inscripcion__persona__apellido2')

                return render(request ,"alu_materias/friendsbs.html" ,  data)
            elif action=='vernotas':
                data['title'] = 'Evaluaciones del Alumno'
                materiaasignada = MateriaAsignada.objects.get(pk=request.GET['id'])
                profesor = Profesor.objects.get(pk=request.GET['p'])
                tipo_nota = int(request.GET['n'])

                evaluacion = materiaasignada.evaluacion()
                if tipo_nota==1:
                    NotasIavq = evaluacion.n1
                else:
                    NotasIavq = evaluacion.n2

                data['evaluacion'] = evaluacion
                data['notaiavq'] = NotasIavq

                data['materiaasignada'] = materiaasignada
                data['profesor'] = profesor
                data['tipo'] = tipo_nota
                return render(request ,"alu_materias/vernotasbs.html" ,  data)
            if action=='clases':
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
                    return render(request ,"alu_materias/asistencia.html" ,  data)

            if action=='clasesonline':
                data['title'] = 'Clases del Docente Online'
                pm = ProfesorMateria.objects.filter(pk=request.GET['pm'])[:1].get()
                data['pm']=pm
                clasesonline = ClasesOnline.objects.filter(profesormateria=pm).order_by('fecha')
                data['clasesonline'] = clasesonline
                return render(request ,"alu_materias/clasesonline.html" ,  data)
        else:
            try:
                inscripcion = Inscripcion.objects.get(persona=data['persona'])

                #Comprobar que no tenga deudas para que no pueda usar el sistema
                if VALIDAR_ENTRADA_SISTEMA_CON_DEUDA and inscripcion.tiene_deuda():
                    return HttpResponseRedirect("/")

                #Comprobar que el alumno este matriculado
                if not inscripcion.matriculado():
                    return HttpResponseRedirect("/?info=Ud. aun no ha sido matriculado")
                matricula = inscripcion.matricula_set.filter(nivel__periodo__activo=True, nivel__cerrado=False,liberada=False)[:1].get()
                materiasAsignadas = matricula.materiaasignada_set.all().order_by('materia__inicio')
                for maa in materiasAsignadas:
                    maa.save() #Actualizar la asistenciafinal en correspondencia con el modelo de Evaluacion
                data['promedio_notas'] = matricula.materiaasignada_set.filter(notafinal__gt=0).aggregate(Avg('notafinal'))['notafinal__avg']
                data['promedio_asistencias'] = matricula.materiaasignada_set.filter(asistenciafinal__gt=0).aggregate(Avg('asistenciafinal'))['asistenciafinal__avg']
                data['matricula'] = matricula
                data['materiasasignadas'] = materiasAsignadas
                data['records'] = RecordAcademico.objects.filter(inscripcion=matricula.inscripcion,aprobada=False)
                data['MODELO_EVALUATIVO'] = [MODELO_EVALUACION, EVALUACION_IAVQ, EVALUACION_ITB, EVALUACION_ITS, EVALUACION_TES, EVALUACION_IGAD, EVALUACION_CASADE]
                data['nota_para_aprobar'] = NOTA_PARA_APROBAR
                data['asistencia_para_aprobar'] = ASIST_PARA_APROBAR
                data['asistencia_para_seguir'] = ASIST_PARA_SEGUIR
                data['valida_asistencia'] = VALIDAR_ASISTENCIAS
                data['conduccion']=INSCRIPCION_CONDUCCION
                data['min_exa']=MIN_EXAMEN
                data['DEFAULT_PASSWORD']=DEFAULT_PASSWORD
                return render(request ,"alu_materias/materiasbs.html" ,  data)
            except Exception as ex:
                 return HttpResponseRedirect("/?info="+str(ex))

    except Exception as ex:
        return HttpResponseRedirect("/?info="+str(ex))