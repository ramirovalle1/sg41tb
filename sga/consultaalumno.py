from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render
from decorators import secure_module
from sga.commonviews import addUserData
from sga.models import Carrera, MateriaAsignada, Persona, Matricula, Inscripcion, Rubro, InscripcionSeminario, GrupoSeminario,InscripcionPracticas,EstudianteVinculacion,\
     EstudianteTutoria,Tutoria,VisitaBox,DetalleVisitasBox,ExamenPractica,InscripcionExamen, InscripcionGrupoPonencia, GrupoPonencia,\
     DocumentosVinculacionEstudiantes
from django.db.models.aggregates import Sum
from settings import COD_TIPOVISITABOX,EXAMEN_PRACTI_COMPLEX,EXAMEN_TEORI_COMPLEX

@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    data = {'title': 'Busqueda de Cursos'}
    addUserData(request, data)
    data['estudiant'] = ''
    fech=datetime.now().year
    if Inscripcion.objects.filter(persona__usuario=request.user).exists():
        data['estudiant']  = Inscripcion.objects.get(persona__usuario=request.user). id
    data['bandera'] = 0
    if 'id' in request.GET or data['estudiant'] != '':
        if 'id' in request.GET:
            id= request.GET['id']
        else:
            id = data['estudiant']
        if Inscripcion.objects.filter(pk=id).exists():
            inscripcion = Inscripcion.objects.get(pk=id)
            data['inscripcion']=inscripcion
            # rubros = Rubro.objects.filter(inscripcion=inscripcion,cancelado=False).order_by('cancelado','fechavence')
            # rubros = Rubro.objects.filter(inscripcion=inscripcion).order_by('cancelado','fechavence')
            # data['rubros'] = rubros
            data['personal'] = inscripcion.persona
            if Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=False,liberada=False).exists():
                rubros = Rubro.objects.filter(inscripcion=inscripcion,cancelado=False).order_by('cancelado','fechavence')
                data['rubros'] = rubros
                matricula = Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=False,liberada=False)[:1].get()

                data['materiasignada'] = MateriaAsignada.objects.filter(matricula__inscripcion=inscripcion,matricula=matricula,cerrado=False).order_by('materia__inicio')

                data['matricula'] = matricula
                data['num']=data['materiasignada'].count()
                if InscripcionSeminario.objects.filter(matricula = matricula).exists():
                    grupo = InscripcionSeminario.objects.filter(matricula__inscripcion = matricula.inscripcion).values('gruposeminario__id')
                    data["seminario"] = GrupoSeminario.objects.filter(id__in=grupo,fin__gte=datetime.now().date()).order_by('id')

                if InscripcionGrupoPonencia.objects.filter(matricula = matricula).exists():
                    grupoponencia = InscripcionGrupoPonencia.objects.filter(matricula__inscripcion = matricula.inscripcion).values('grupoponencia__id')
                    data["ponencia"] = GrupoPonencia.objects.filter(id__in=grupoponencia,activo=True).order_by('id')
            else:
                rubros = Rubro.objects.filter(inscripcion=inscripcion).order_by('cancelado','fechavence')
                data['rubros'] = rubros
                # data['error'] = 'No esta matriculado'

            #Practicas Preprofesionales
            hpracticas = 0
            vinculacion = 0
            if InscripcionPracticas.objects.filter(inscripcion=inscripcion).exists():
                practicas = InscripcionPracticas.objects.filter(inscripcion=inscripcion).order_by('inicio')
                data['totalhoras'] = practicas.aggregate(Sum('horas'))['horas__sum']
                hpracticas = practicas.aggregate(Sum('horas'))['horas__sum']
                data['practicas'] = practicas
            if EstudianteVinculacion.objects.filter(inscripcion=inscripcion).exists():
                data['vinculacion'] = EstudianteVinculacion.objects.filter(inscripcion=inscripcion)
                vinculacion= EstudianteVinculacion.objects.filter(inscripcion=inscripcion).aggregate(Sum('horas'))['horas__sum']
                data['tohorasvin'] =vinculacion
            data['totalgen'] = vinculacion + hpracticas

            #Tutorias
            if Tutoria.objects.filter(estudiante=inscripcion,estado=True).exists():
                tutorias = Tutoria.objects.get(estudiante=inscripcion,estado=True)
                data['tutorias'] = tutorias
                if EstudianteTutoria.objects.filter(tutoria=tutorias.id).exists():
                    data['tuto_estudiante']=EstudianteTutoria.objects.filter(tutoria=tutorias.id)

            #Ver Profilaxis
            if VisitaBox.objects.filter(cedula=inscripcion.persona.cedula).exists():
                visita=VisitaBox.objects.filter(cedula=inscripcion.persona.cedula)
                for v in visita:
                    if DetalleVisitasBox.objects.filter(visitabox__id=v.id,tipoconsulta=COD_TIPOVISITABOX,fecha__year=fech).exists():
                        profilaxis=DetalleVisitasBox.objects.get(visitabox__id=v.id,tipoconsulta=COD_TIPOVISITABOX,fecha__year=fech)
                        atendido_por=Persona.objects.get(usuario__id=profilaxis.usuario_id)
                        data['profilaxis'] = profilaxis
                        data['atendido']=atendido_por

            #Para presentar notas de examen practico y teorico de complexivo si lo tiene
            if inscripcion.alumno_estado():
                data['examenpracticos'] = ExamenPractica.objects.filter(inscripcion=inscripcion)
                data['nota_examen_pract']=EXAMEN_PRACTI_COMPLEX
                # inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                if InscripcionExamen.objects.filter(inscripcion=inscripcion).exists():
                    data['inscripcionexamen'] = InscripcionExamen.objects.filter(inscripcion=inscripcion).order_by('tituloexamencondu','fecha')
                    data['nota_examen_teorico']=EXAMEN_TEORI_COMPLEX

            #Para presentar informacion de malla de estudiantes
            if inscripcion.puede_egresar() == "":
                data['malla_inscripcion'] = "Malla Completa"
            else:
                data['malla_inscripcion'] = inscripcion.puede_egresar()

            if DocumentosVinculacionEstudiantes.objects.filter().exists():
                data['documento'] = DocumentosVinculacionEstudiantes.objects.all().order_by('fecha')

    if data['estudiant'] != '':
        return render(request ,"congreso/registroestudiante.html" ,  data)
    else:
        return render(request ,"congreso/consultaalumno.html" ,  data)