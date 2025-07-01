from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render
from decorators import secure_module
from settings import REPORTE_CRONOGRAMA_PROFESOR,TIPO_PERIODO_REGULAR,ARCHIVO_TIPO_PLANCLASE
from sga.commonviews import addUserData
from sga.models import Materia, MateriaAsignada, Persona, Matricula, Profesor, Rubro, Periodo, GrupoSeminario, CalificacionEvaluacion


@login_required(redirect_field_name='ret', login_url='/login')
# @secure_module
def view(request):
    data = {'title': 'Consulta de Docente'}
    addUserData(request, data)
    data['profesor'] = ''
    # if Profesor.objects.filter(persona__usuario=request.user).exists():
    #     data['profesor']  = Profesor.objects.get(persona__usuario=request.user). id
    data['bandera'] = 0
    if 'id' in request.GET or data['profesor'] != '':
        if 'id' in request.GET:
            id= request.GET['id']
        # else:
        #     id = data['profesor']
        if Profesor.objects.filter(pk=id).exists():
            profesor = Profesor.objects.get(pk=id)
            # rubros = Rubro.objects.filter(inscripcion=inscripcion,cancelado=False).order_by('cancelado','fechavence')
            # rubros = Rubro.objects.filter(inscripcion=inscripcion).order_by('cancelado','fechavence')
            # data['rubros'] = rubros
            data['personal'] = profesor.persona
            periodo = request.session['periodo']
            data['per'] = Periodo.objects.filter(activo=True,tipo__id=TIPO_PERIODO_REGULAR)
            ret = None
            if 'ret' in request.GET:
                ret = request.GET['ret']

            if 'id' in request.GET:
                profesor = Profesor.objects.get(pk=request.GET['id'])
                data['id'] = request.GET['id']
            # else:
            #     profesor = Profesor.objects.get(persona=data['persona'])
            data['profesor'] = profesor
            if profesor.materias_imparte_sinperiodo():
                materias = profesor.materias_imparte_sinperiodo().order_by('inicio','nivel__sede')

                data['periodo'] = periodo

                data['materias'] = materias
                data['ret'] = ret if ret else ""
                data['reporte_cronograma_profesor'] = REPORTE_CRONOGRAMA_PROFESOR
                data['calificacion'] = CalificacionEvaluacion.objects.all().order_by('id')
            # if Materia.objects.filter(nivel__periodo=periodo,profesormateria__profesor=profesor).exists() or Materia.objects.filter(nivel__periodo=True, profesormateria__profesor_aux=profesor.id).exists():
            #     materias =  Materia.objects.filter(Q(nivel__periodo=periodo,profesormateria__profesor=profesor)& (Q(profesormateria__profesor=profesor,profesormateria__profesor_aux=None) | Q(profesormateria__profesor_aux=profesor.id))).order_by('asignatura','nivel__sede','nivel__nivelmalla')
            #     data['materias'] = materias
            #     data['nivel'] = materias[0].nivel
            #     data['periodo'] = periodo
            #     if 'info' in request.GET:
            #         data['info'] = request.GET['info']
            data['ARCHIVO_TIPO_PLANCLASE'] = ARCHIVO_TIPO_PLANCLASE

                # data['error'] = 'No esta matriculado'
    if data['profesor'] != '' and not 'id' in request.GET:

        return render(request ,"docentes/registrodocente.html" ,  data)
    else:
        return render(request ,"docentes/consultadocente.html" ,  data)