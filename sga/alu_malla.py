from django.contrib.auth.decorators import login_required
from django.db.models import Sum,Max
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from decorators import secure_module
from settings import VALIDAR_ENTRADA_SISTEMA_CON_DEUDA, ASIST_PARA_APROBAR, EJE_PRACTICA, HORAS_TELECLINICA
from sga.commonviews import addUserData
from sga.models import Inscripcion, NivelMalla, EjeFormativo, AsignaturaMalla, RecordAcademico, InscripcionPracticas, \
    EstudianteVinculacion, AprobacionVinculacion, InscripcionExamen


@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    data = {}
    addUserData(request, data)
    persona = data['persona']
    try:
        data['title'] = 'Malla del Alumno'

        inscripcion = Inscripcion.objects.get(persona=persona)

        #Comprobar que no tenga deudas para que no pueda usar el sistema
        if VALIDAR_ENTRADA_SISTEMA_CON_DEUDA and inscripcion.tiene_deuda():
            return HttpResponseRedirect("/")

        inscripcionmalla = inscripcion.malla_inscripcion()
        #Comprobar que exista la malla en la carrera de la inscripcion
        if not inscripcionmalla:
            return HttpResponseRedirect("/?info=Ud. no tiene ninguna malla asociada")
        malla = inscripcionmalla.malla

        data['inscripcion'] = inscripcion
        data['inscripcion_malla'] = inscripcionmalla
        data['malla'] = malla

        data['nivelesdemallas'] = NivelMalla.objects.all().order_by('orden')
        data['ejesformativos'] = EjeFormativo.objects.all().order_by('nombre')
        data['asignaturasmallas'] = [(x, aprobadaAsignatura(x, inscripcion), horaspracticas(x, inscripcion),horasteleclinica(x,inscripcion)) for x in AsignaturaMalla.objects.filter(malla=malla)]
        resumenNiveles = [{'id':x.id, 'horas': x.total_horas2(malla,inscripcion), 'creditos': x.total_creditos(malla)} for x in NivelMalla.objects.all().order_by('orden')]
        data['resumenes'] = resumenNiveles
        data['title'] = "Ver Malla Curricular : "+malla.carrera.nombre
        data['ASIST_PARA_APROBAR']=ASIST_PARA_APROBAR
        if InscripcionPracticas.objects.filter(inscripcion=inscripcion).exists():
            practicas = InscripcionPracticas.objects.filter(inscripcion=inscripcion).aggregate(Sum('horas'))['horas__sum']
            data['practicas'] = practicas
        if EstudianteVinculacion.objects.filter(inscripcion=inscripcion).exists():
            data['vinculacion'] = EstudianteVinculacion.objects.filter(inscripcion=inscripcion)
            if AprobacionVinculacion.objects.filter(inscripcion=inscripcion).exists():
                vinculacion= EstudianteVinculacion.objects.filter(inscripcion=inscripcion).aggregate(Sum('horas'))['horas__sum']
                data['tohorasvin'] =vinculacion
        #OCastillo 13-03-2023 cambio para tecnologias universitarias de Podologia y Gerontologia
        if inscripcion.malla_inscripcion().malla.id ==72 or inscripcion.malla_inscripcion().malla.id ==74:
            data['EJE_PRACTICA']  = 9
            data['HORAS_TELECLINICA']   =HORAS_TELECLINICA
        else:
            data['EJE_PRACTICA']   =EJE_PRACTICA
        return render(request ,"alu_malla/mallabs.html" ,  data)
    except :
        return HttpResponseRedirect("/")

def aprobadaAsignatura(asignaturamalla, inscripcion):
    try:
        return RecordAcademico.objects.get(inscripcion=inscripcion, asignatura=asignaturamalla.asignatura)
    except :
        return None

def horaspracticas(asignaturamalla, inscripcion):
    try:
        # print(asignaturamalla.nivelmalla)
        practicas= -1
        if 'PRACTIC' in asignaturamalla.asignatura.nombre or 'PREPROFESIONALES' in asignaturamalla.asignatura.nombre or 'TELECLINICA' in asignaturamalla.asignatura.nombre:
            if InscripcionPracticas.objects.filter(inscripcion=inscripcion,nivelmalla=asignaturamalla.nivelmalla).exists():
                return  InscripcionPracticas.objects.filter(inscripcion=inscripcion,nivelmalla=asignaturamalla.nivelmalla).aggregate(Sum('horas'))['horas__sum']

            if AprobacionVinculacion.objects.filter(inscripcion__in=EstudianteVinculacion.objects.filter(inscripcion=inscripcion,nivelmalla=asignaturamalla.nivelmalla).values('inscripcion')).exists():
                return EstudianteVinculacion.objects.filter(inscripcion=inscripcion,nivelmalla=asignaturamalla.nivelmalla).aggregate(Sum('horas'))['horas__sum']

        return practicas
    except :
        return 0

def horasteleclinica(asignaturamalla, inscripcion):
    try:
        teleclinica= -1
        if 'TELECLINICA' in asignaturamalla.asignatura.nombre:
            if InscripcionExamen.objects.filter(inscripcion=inscripcion,tituloexamencondu__asignatura=asignaturamalla.asignatura).exists():
                return  InscripcionExamen.objects.filter(inscripcion=inscripcion,tituloexamencondu__asignatura=asignaturamalla.asignatura).aggregate(Max('puntaje'))['puntaje__max']
        return teleclinica
    except :
        return 0