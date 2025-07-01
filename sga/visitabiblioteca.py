import random
from datetime import datetime, timedelta, time
import json
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
from decorators import secure_module
from settings import CENTRO_EXTERNO, RUBRO_TIPO_OTRO_MODULO_INTERNO, RUBRO_TIPO_OTRO_INSCRIPCION, DEFAULT_PASSWORD, \
    PROFESORES_GROUP_ID, ALUMNOS_GROUP_ID, UTILIZA_GRUPOS_ALUMNOS, REPORTE_CERTIFICADO_INSCRIPCION, EMAIL_ACTIVE, \
    EVALUACION_ITB, REGISTRO_HISTORIA_NOTAS, NOTA_ESTADO_EN_CURSO, GENERAR_RUBROS_PAGO, GENERAR_RUBRO_INSCRIPCION, \
    GENERAR_RUBRO_INSCRIPCION_MARGEN_DIAS, MODELO_EVALUACION, EVALUACION_IAVQ, EVALUACION_ITS, \
    UTILIZA_NIVEL0_PROPEDEUTICO, TIPO_PERIODO_PROPEDEUTICO, NOTA_ESTADO_APROBADO, UTILIZA_FICHA_MEDICA, EVALUACION_TES, \
    CORREO_INSTITUCIONAL, USA_CORREO_INSTITUCIONAL, INSCRIPCION_CONDUCCION, TIPO_DOCENTE, TIPO_ESTUDIANTE, \
    TIPO_ADMINISTRATIVO, TIPO_OTROS, SISTEMAS_GROUP_ID
from sga.alu_malla import aprobadaAsignatura
from sga.commonviews import addUserData, ip_client_address
from sga.docentes import calculate_username

from sga.forms import PersonaForm, InscripcionForm, RecordAcademicoForm, HistoricoRecordAcademicoForm, HistoriaNivelesDeInscripcionForm, CargarFotoForm, EmpresaInscripcionForm, EstudioInscripcionForm, DocumentoInscripcionForm, ActividadesInscripcionForm, PadreClaveForm, ConvalidacionInscripcionForm, HistoricoNotasITBForm, GraduadoDatosForm, EgresadoForm, InscripcionSenescytForm, RetiradoMatriculaForm, InscripcionCextForm, BecarioForm, InscripcionPracticaForm, ObservacionInscripcionForm, ProcesoDobeForm,  VisitaBibliotecaForm,VisitaBibliotecaForm, RVisitaBiblioForm
from sga.models import Profesor, ProcesoDobe, Persona, Inscripcion, RecordAcademico, DocumentosDeInscripcion, \
    HistoricoRecordAcademico, HistoriaNivelesDeInscripcion, FotoPersona, \
    EmpresaInscripcion, EstudioInscripcion, DocumentoInscripcion, Archivo, TipoArchivo, Grupo, InscripcionGrupo, \
    PerfilInscripcion, HistoricoNotasITB, PadreClave, Malla, \
    ConvalidacionInscripcion, TipoEstado, Rubro, RubroInscripcion, NivelMalla, EjeFormativo, AsignaturaMalla, Egresado, \
    Asignatura, InscripcionSenescyt, RetiradoMatricula, \
    Carrera, Modalidad, Sesion, Especialidad, Materia, Nivel, TipoOtroRubro, Matricula, MateriaAsignada, RubroOtro, \
    Graduado, InscripcionBecario, InscripcionPracticas, \
    ObservacionInscripcion, InscripcionConduccion, VisitaBiblioteca, TipoVisitasBiblioteca, DetalleVisitasBiblioteca, \
    TipoPersona, Sede, Aula, TipoArticulo, TituloInstitucion, convertir_fecha, RolPerfilProfesor, Coordinacion, \
    Departamento, ProfesorMateria, Periodo
from sga.notificaciones import nueva_informacion
from sga.tasks import gen_passwd
from settings import MEDIA_ROOT
import xlwt

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


def getTipoPersona(persona):
    listaperfiles = []

    if persona:
        for p in persona:
            profesor = Profesor.objects.filter(persona=p, activo=True).last()
            inscripcion = Inscripcion.objects.filter(persona=p, carrera__carrera=True).last()
            gruposexcluidos = [PROFESORES_GROUP_ID, ALUMNOS_GROUP_ID, SISTEMAS_GROUP_ID]
            administrativo = Persona.objects.filter(id=p.id, usuario__is_active=True, nacimiento__isnull=False).exclude(usuario__groups__id__in=gruposexcluidos).exclude(usuario=None)

            if profesor:
                listaperfiles.append(TIPO_DOCENTE)
            if inscripcion:
                listaperfiles.append(TIPO_ESTUDIANTE)
            if administrativo:
                listaperfiles.append(TIPO_ADMINISTRATIVO)
            # if inscripcion:
                # egresado = Egresado.objects.filter(inscripcion=inscripcion).last()
                # if egresado:
                #     listaperfiles.append()
        if not listaperfiles:
            listaperfiles.append(TIPO_OTROS)
    else:
        listaperfiles.append(TIPO_OTROS)

    return listaperfiles

def crearvisitaautomatica(persona, tipopersona):
    cedula = persona.cedula
    if not cedula:
        cedula = persona.pasaporte
    visita = VisitaBiblioteca.objects.filter(cedula__icontains=cedula).first()
    if not visita:
        if persona.cedula:
            identificacion = persona.cedula
        else:
            identificacion = persona.pasaporte

        if persona.telefono:
            numtelefono = persona.telefono
        else:
            numtelefono = persona.telefono_conv

        visita = VisitaBiblioteca(tipopersona=tipopersona,
                                  persona=persona,
                                  nombre=persona.nombre_completo(),
                                  cedula=identificacion,
                                  telefono=numtelefono,
                                  direccion=persona.direccion)
        visita.save()
    return visita

def creardetallevisitaautomatica(visita, tipopersona, request):
    sede = Sede.objects.get(id=request.POST['idsede'])
    tipovisitabiblioteca = TipoVisitasBiblioteca.objects.get(id=request.POST['tipovisitabiblioteca'])
    detallevisita = None
    if request.POST['tipoarticuloid'] != '':
        tipo_articulo_ids = request.POST['tipoarticuloid'].split(",")  # Obtener todos los IDs de tipos de artículos
        tipo_articulo_id = random.choice(tipo_articulo_ids)  # Escoger uno aleatoriamente

        if TipoArticulo.objects.filter(id=tipo_articulo_id).exists():
            articulo = TipoArticulo.objects.filter(id=tipo_articulo_id)[:1].get()

            fecha = datetime.now()
            if tipopersona.id == TIPO_ESTUDIANTE:
                nivel = visita.nivel
                fecha = obtener_fecha_aleatoria(nivel.inicio, nivel.fin)
            elif tipopersona.id == TIPO_DOCENTE:
                periodo = Periodo.objects.filter(id=request.POST['periodo']).values('inicio', 'fin').first()
                if periodo:
                    fecha = obtener_fecha_aleatoria(periodo['inicio'], periodo['fin'])
            elif tipopersona.id == TIPO_ADMINISTRATIVO:
                inicio = datetime.strptime(request.POST['fechainicio'], "%Y-%m-%d").date()
                fin = datetime.strptime(request.POST['fechafin'], "%Y-%m-%d").date()
                fecha = obtener_fecha_aleatoria(inicio, fin)

            detallevisita = DetalleVisitasBiblioteca(visitabiblioteca=visita,
                                                     tipovisitabiblioteca=tipovisitabiblioteca,
                                                     fecha=fecha,
                                                     observacion=request.POST['observacion'].upper(),
                                                     tipoarticulo=articulo,
                                                     sede=sede)
            detallevisita.save()
        return detallevisita
    return False

def obtener_fecha_aleatoria(inicio, fin):
    # Generar una lista de fechas entre inicio y fin que sean de lunes a viernes
    fechas_validas = []
    current_date = inicio
    while current_date <= fin:
        if current_date.weekday() < 5:  # 0: Lunes, 1: Martes, ..., 4: Viernes
            fechas_validas.append(current_date)
        current_date += timedelta(days=1)

    # Si no hay fechas válidas, devolver None
    if not fechas_validas:
        return None

    # Seleccionar una fecha aleatoria de la lista de fechas válidas
    fecha_random = random.choice(fechas_validas)

    # Generar una hora aleatoria entre las 9:00 AM y las 2:00 PM
    hora_inicio = time(9, 0)  # 9:00 AM
    hora_fin = time(13, 0)  # 2:00 PM

    hora_random = time(
        random.randint(hora_inicio.hour, hora_fin.hour),
        random.randint(0, 59)
    )

    # Combinar la fecha y la hora en un solo objeto datetime
    fecha_hora_random = datetime.combine(fecha_random, hora_random)

    return fecha_hora_random

@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
@transaction.atomic()
def view(request):
    if request.method=='POST':
        action = request.POST['action']
        if action=='add': # ya no se usa
            persona = None
            f = VisitaBibliotecaForm(request.POST)
            if f.is_valid():
                if Persona.objects.filter(Q(cedula__icontains=request.POST['cedula'])|Q(pasaporte__icontains=request.POST['cedula'])).exists():
                    persona=Persona.objects.filter(Q(cedula__icontains=request.POST['cedula'])|Q(pasaporte__icontains=request.POST['cedula']))[:1].get()
                if VisitaBiblioteca.objects.filter(cedula=request.POST['cedula']).exists():
                    visita = VisitaBiblioteca.objects.filter(cedula=request.POST['cedula'])[:1].get()
                    visita.tipopersona=f.cleaned_data['tipopersona']
                    visita.persona=persona
                    visita.nombre=f.cleaned_data['nombres']
                    visita.cedula=f.cleaned_data['cedula']
                    visita.telefono=f.cleaned_data['telefono']
                    visita.direccion=f.cleaned_data['direccion']
                    visita.motivovisita=f.cleaned_data['motivovisita']
                    visita.save()
                    # detallevisita = DetalleVisitasBiblioteca(visitabiblioteca=visita,
                    #                         tipovisitabiblioteca = f.cleaned_data['tipovisitabiblioteca'],
                    #                         fecha = datetime.now(),
                    #                         observacion = f.cleaned_data['observacion'])

                else:

                    visita = VisitaBiblioteca(tipopersona=f.cleaned_data['tipopersona'],
                                              persona=persona,
                                              nombre=f.cleaned_data['nombres'],
                                              cedula=f.cleaned_data['cedula'],
                                              telefono=f.cleaned_data['telefono'],
                                              direccion=f.cleaned_data['direccion'],
                                              motivovisita=f.cleaned_data['motivovisita'])

                    visita.save()
                if 'idsede' in request.POST:
                    sede = Sede.objects.get(id=request.POST['idsede'])
                else:
                    sede = f.cleaned_data['sede']
                if request.POST['tipoarticuloid'] != '':
                    for a in request.POST['tipoarticuloid'].split(","):
                        if TipoArticulo.objects.filter(id=a).exists():
                            articulo = TipoArticulo.objects.filter(id=a)[:1].get()

                            detallevisita = DetalleVisitasBiblioteca(visitabiblioteca=visita,
                                                tipovisitabiblioteca = f.cleaned_data['tipovisitabiblioteca'],
                                                fecha = datetime.now(),
                                                observacion = f.cleaned_data['observacion'],
                                                tipoarticulo = articulo,
                                                sede = sede)
                            detallevisita.save()

        elif action=='datosvisitas':
                result = {}

                if VisitaBiblioteca.objects.filter(cedula=request.POST['cedula']).exists():
                   visitabiblioteca = VisitaBiblioteca.objects.filter(cedula=request.POST['cedula'])[:1].get()

                   result['result']  = "ok"
                   result['nombre']  = visitabiblioteca.nombre
                   result['telefono']  = visitabiblioteca.telefono
                   result['direccion']  = visitabiblioteca.direccion
                   persona = Persona.objects.filter(cedula=request.POST['cedula'])
                   if persona:
                       listaperfiles = getTipoPersona(persona)
                       result['cmbtipopersona'] = [{"id": t.id, "descripcion": t.descripcion}
                                                   for t in TipoPersona.objects.filter(id__in=listaperfiles)]
                       if TIPO_DOCENTE in listaperfiles:
                           result['autoselectipo'] = TIPO_DOCENTE
                       elif TIPO_ESTUDIANTE in listaperfiles:
                           result['autoselectipo'] = TIPO_ESTUDIANTE
                       elif TIPO_ADMINISTRATIVO in listaperfiles:
                           result['autoselectipo'] = TIPO_ADMINISTRATIVO
                       elif TIPO_OTROS in listaperfiles:
                           result['autoselectipo'] = TIPO_OTROS

                   # return HttpResponse(json.dumps(result),content_type="application/json")
                   return HttpResponse(json.dumps(result),content_type="application/json")


                elif Persona.objects.filter(cedula=request.POST['cedula']).exists():
                   persona = Persona.objects.filter(cedula=request.POST['cedula'])[:1].get()

                   result['result']  = "ok"
                   result['nombre']  = persona.nombre_completo()
                   result['telefono']  = persona.telefono
                   result['direccion']  = persona.direccion

                   persona = Persona.objects.filter(cedula=request.POST['cedula'])
                   listaperfiles = getTipoPersona(persona)
                   result['cmbtipopersona'] = [{"id": t.id, "descripcion": t.descripcion}
                                               for t in TipoPersona.objects.filter(id__in=listaperfiles)]
                   if TIPO_DOCENTE in listaperfiles:
                       result['autoselectipo'] = TIPO_DOCENTE
                   elif TIPO_ESTUDIANTE in listaperfiles:
                       result['autoselectipo'] = TIPO_ESTUDIANTE
                   elif TIPO_ADMINISTRATIVO in listaperfiles:
                       result['autoselectipo'] = TIPO_ADMINISTRATIVO
                   elif TIPO_OTROS in listaperfiles:
                       result['autoselectipo'] = TIPO_OTROS

                   # return HttpResponse(json.dumps(result),content_type="application/json")
                   return HttpResponse(json.dumps(result),content_type="application/json")

                else:
                    listaperfiles = getTipoPersona(None)

                    result['cmbtipopersona'] = [{"id": t.id, "descripcion": t.descripcion}
                                                for t in TipoPersona.objects.filter(id__in=listaperfiles)]
                    if TIPO_OTROS in listaperfiles:
                        result['autoselectipo'] = TIPO_OTROS
                    result['result'] = "bad"
                    return HttpResponse(json.dumps(result),content_type="application/json")

                   # return HttpResponseRedirect("/ventas")
        elif action =='addtipovisitabiblioteca':
            try:
                data = {}
                tipovisita = TipoVisitasBiblioteca(descripcion=request.POST['descripcion'])
                tipovisita.save()
                data['result'] = 'ok'
                data['listavisita'] = [{"id": d.id, "tipovisita": str(d)} for d in TipoVisitasBiblioteca.objects.filter()]
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as ex:
                return HttpResponse(json.dumps({"result": "bad"}), content_type="application/json")
        elif action =='addtipoarticulo':
            try:
                data = {}
                tipoarticulo = TipoArticulo(descripcion=request.POST['descripcion'])
                tipoarticulo.save()
                if request.POST['estado'] == 'true':
                    tipoarticulo.estado = True
                    tipoarticulo.save()
                else:
                    tipoarticulo.estado = False
                    tipoarticulo.save()
                tipovisitabiblioteca = TipoVisitasBiblioteca.objects.get(id=request.POST['tiposervicio'])
                tipoarticulo.tipovisitabiblioteca = tipovisitabiblioteca
                tipoarticulo.save()
                data['result'] = 'ok'
                data['listaarticulo'] = [{"id": d.id, "tipoarticulo": str(d)} for d in TipoArticulo.objects.filter()]
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as ex:
                return HttpResponse(json.dumps({"result": "bad"}), content_type="application/json")

        elif action =='generarexcel':
            try:
                inicio = request.POST['inicio']
                fin = request.POST['fin']
                fechai = convertir_fecha(inicio)
                fechaf = convertir_fecha(fin)+timedelta(hours=23,minutes=59)

                # TITULO
                titulo = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                titulo.font.height = 20 * 11
                titulo1 = xlwt.easyxf('font: name Times New Roman, bold on; align: wrap on, vert centre, horiz left')
                titulo1.font.height = 20 * 11
                # CABECERA DE LA TABLA
                titulocabecera = xlwt.easyxf('font: name Times New Roman, colour black, bold on; align: wrap on, vert centre, horiz center')
                titulocabecera.font.height = 20 * 11
                # CONTENIDO DE LA TABLA
                contenido = xlwt.easyxf('font: name Times New Roman')
                contenido.font.height = 20 * 11
                # ADICIONALS
                subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                subtitulo.font.height = 20 * 10

                wb = xlwt.Workbook()
                ws = wb.add_sheet('LISTADO', cell_overwrite_ok=True)

                tit = TituloInstitucion.objects.all()[:1].get()
                ws.write_merge(0, 0, 0, 14, tit.nombre, titulo)
                ws.write_merge(1, 1, 0, 14, 'VISITAS A BIBLIOTECA', titulo)

                sede = Sede.objects.filter(pk= request.POST['sede'])[:1].get()
                ws.write(2, 0, 'SEDE: ' +sede.nombre, titulo1)
                ws.write(3, 0, 'DESDE: ' + str(fechai.date()) , titulo1)
                ws.write(4, 0, 'HASTA: ' + str(fechaf.date()), titulo1)
                fila = 6
                ws.write(fila, 0, 'NOMBRE', titulocabecera)
                ws.col(0).width = 10 * 800
                ws.write(fila, 1, 'CEDULA', titulocabecera)
                ws.col(1).width = 10 * 400
                ws.write(fila, 2, 'TELEFONO', titulocabecera)
                ws.col(2).width = 10 * 450
                ws.write(fila, 3, 'FECHA', titulocabecera)
                ws.col(3).width = 10 * 400
                ws.write(fila, 4, 'TIPO', titulocabecera)
                ws.col(4).width = 10 * 400
                ws.write(fila, 5, 'TIPO DE SERVICIO', titulocabecera)
                ws.col(5).width = 10 * 600
                ws.write(fila, 6, 'TIPO DE ARTICULO', titulocabecera)
                ws.col(6).width = 10 * 600
                # visitas = DetalleVisitasBiblioteca.objects.filter(fecha__gte=fechai, fecha__lte=fechaf,sede=sede).order_by('visitabiblioteca__nombre', 'fecha')
                visitas_cedula = DetalleVisitasBiblioteca.objects.filter(fecha__gte=fechai,fecha__lte=fechaf,sede=sede).values('visitabiblioteca__cedula').distinct()
                persona = Persona.objects.filter(usuario__is_active=True,cedula__in=visitas_cedula).order_by('cedula').distinct('cedula').values('id')
                personas = Persona.objects.filter(id__in=persona).order_by('apellido1','apellido2','nombres')
                # vistas exclusion
                visitas = DetalleVisitasBiblioteca.objects.filter(fecha__gte=fechai, fecha__lte=fechaf,sede=sede).exclude(visitabiblioteca__cedula__in=personas.values('cedula'))
                detalle = 0
                fila = 7
                for p in personas:
                    cedula = p.cedula
                    detalles_visitas = DetalleVisitasBiblioteca.objects.filter(fecha__gte=fechai, fecha__lte=fechaf,sede=sede, visitabiblioteca__cedula=p.cedula)
                    detalle += detalles_visitas.count()
                    for v in detalles_visitas:
                        if cedula:
                            nombre = p.nombre_completo_inverso()
                        else:
                            nombre = ''
                        if v.visitabiblioteca.cedula:
                            cedula = v.visitabiblioteca.cedula
                        else:
                            cedula = ''
                        if v.visitabiblioteca.telefono:
                            telefono = v.visitabiblioteca.telefono
                        else:
                            telefono = ''

                        if v.visitabiblioteca.tipopersona:
                            tipo = v.visitabiblioteca.tipopersona.descripcion
                        else:
                            tipo = ''
                        fecha = str(v.fecha.date())
                        if v.tipovisitabiblioteca:
                            tiposervicio = v.tipovisitabiblioteca.descripcion
                        else:
                            tiposervicio = ''
                        if v.tipoarticulo:
                            tipoarticulo = v.tipoarticulo.descripcion
                        else:
                            tipoarticulo = ''

                        ws.write(fila, 0, nombre, contenido)
                        ws.write(fila, 1, cedula, contenido)
                        ws.write(fila, 2, telefono, contenido)
                        ws.write(fila, 3, fecha, contenido)
                        ws.write(fila, 4, tipo, contenido)
                        ws.write(fila, 5, tiposervicio, contenido)
                        ws.write(fila, 6, tipoarticulo, contenido)
                        fila = fila + 1

                totalvisitas2 = detalle
                totalvisitas = visitas.count()
                total = totalvisitas+totalvisitas2  #7496
                for v in visitas:
                    if v.visitabiblioteca.nombre:
                        nombre = v.visitabiblioteca.nombre
                    else:
                        nombre =''
                    if v.visitabiblioteca.cedula:
                        cedula = v.visitabiblioteca.cedula
                    else:
                        cedula = ''
                    if v.visitabiblioteca.telefono:
                        telefono = v.visitabiblioteca.telefono
                    else:
                        telefono = ''

                    if v.visitabiblioteca.tipopersona:
                        tipo =v.visitabiblioteca.tipopersona.descripcion
                    else:
                        tipo = ''
                    fecha = str(v.fecha.date())
                    if v.tipovisitabiblioteca:
                        tiposervicio = v.tipovisitabiblioteca.descripcion
                    else:
                        tiposervicio = ''
                    if v.tipoarticulo:
                        tipoarticulo = v.tipoarticulo.descripcion
                    else:
                        tipoarticulo = ''

                    ws.write(fila, 0, nombre, contenido)
                    ws.write(fila, 1, cedula, contenido)
                    ws.write(fila, 2, telefono, contenido)
                    ws.write(fila, 3, fecha, contenido)
                    ws.write(fila, 4, tipo, contenido)
                    ws.write(fila, 5, tiposervicio, contenido)
                    ws.write(fila, 6, tipoarticulo, contenido)
                    fila = fila + 1

                fila = fila + 1
                ws.write(fila, 0, "Visitas: " + str(total), subtitulo)
                fila = fila + 1
                ws.write(fila, 0, "Fecha Impresion", subtitulo)
                ws.write(fila, 1, str(datetime.now()), subtitulo)
                fila = fila + 1
                ws.write(fila, 0, "Usuario", subtitulo)
                ws.write(fila, 1, str(request.user), subtitulo)

                nombre = 'repvisitabiblioteca' + str(datetime.now()).replace(" ", "").replace(".", "").replace(":","") + '.xls'
                wb.save(MEDIA_ROOT + '/reporteexcel/' + nombre)
                return HttpResponse(json.dumps({"result": "ok", "url": "/media/reporteexcel/" + nombre}),content_type="application/json")

            except Exception as ex:
                print(str(ex))
                return HttpResponse(json.dumps({"result": str(ex)}), content_type="application/json")

        elif action == 'cargatiposervicio':
            try:
                data = {}
                tipovisitabiblioteca = TipoVisitasBiblioteca.objects.get(id=request.POST['idtiposervicio'])
                data['tipoarticulos'] = [{'id': str(t.id), 'descripcion': t.descripcion}
                                         for t in TipoArticulo.objects.filter(estado=True, tipovisitabiblioteca=tipovisitabiblioteca).order_by('descripcion')]
                data['result'] = 'ok'
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as ex:
                return HttpResponse(json.dumps({"result": "bad"}), content_type="application/json")

        elif action == 'guardavisita':
            sid = transaction.savepoint()
            try:
                data = {}
                tipovisitabiblioteca = TipoVisitasBiblioteca.objects.get(id=request.POST['tipovisitabiblioteca'])
                tipopersona = TipoPersona.objects.get(id=request.POST['tipopersona'])
                persona = None
                if Persona.objects.filter(Q(cedula__icontains=request.POST['cedula'])|Q(pasaporte__icontains=request.POST['cedula'])).exists():
                    persona=Persona.objects.filter(Q(cedula__icontains=request.POST['cedula'])|Q(pasaporte__icontains=request.POST['cedula']))[:1].get()
                if VisitaBiblioteca.objects.filter(cedula=request.POST['cedula']).exists():
                    visita = VisitaBiblioteca.objects.filter(cedula=request.POST['cedula'])[:1].get()
                    visita.tipopersona=tipopersona
                    visita.persona=persona
                    visita.nombre=request.POST['nombres']
                    visita.cedula=request.POST['cedula']
                    visita.telefono=request.POST['telefono']
                    visita.direccion=request.POST['direccion']
                    visita.save()
                else:
                    visita = VisitaBiblioteca(tipopersona=tipopersona,
                                              persona=persona,
                                              nombre=request.POST['nombres'],
                                              cedula=request.POST['cedula'],
                                              telefono=request.POST['telefono'],
                                              direccion=request.POST['direccion'])
                    visita.save()

                # ------------ campos segun el perfil (tipo persona) --------- #
                if 'facultad' in request.POST:
                    facultad = Coordinacion.objects.get(id=request.POST['facultad'])
                    visita.facultad = facultad
                if 'carrera' in request.POST:
                    carrera = Carrera.objects.get(id=request.POST['carrera'])
                    visita.carrera = carrera
                if 'modalidad' in request.POST:
                    modalidad = Modalidad.objects.get(id=request.POST['modalidad'])
                    visita.modalidad = modalidad
                if 'nivel' in request.POST:
                    nivel = Nivel.objects.get(id=request.POST['nivel'])
                    visita.nivel = nivel
                if 'jornada' in request.POST:
                    jornada = Sesion.objects.get(id=request.POST['jornada'])
                    visita.jornada = jornada
                if 'departamento' in request.POST:
                    departamento = Group.objects.get(id=request.POST['departamento'])
                    visita.departamento = departamento
                if 'egresado' in request.POST:
                    visita.egresado = True
                visita.save()
                # ---------- fin campos segun perfil ----------- #

                sede = Sede.objects.get(id=request.POST['idsede'])

                if request.POST['tipoarticuloid'] != '':
                    for a in request.POST['tipoarticuloid'].split(","):
                        if TipoArticulo.objects.filter(id=a).exists():
                            articulo = TipoArticulo.objects.filter(id=a)[:1].get()

                            detallevisita = DetalleVisitasBiblioteca(visitabiblioteca=visita,
                                                                     tipovisitabiblioteca = tipovisitabiblioteca,
                                                                     fecha = datetime.now(),
                                                                     observacion = request.POST['observacion'],
                                                                     tipoarticulo = articulo,
                                                                     sede = sede)
                            detallevisita.save()
                data['result'] = 'ok'
                transaction.savepoint_commit(sid)
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as ex:
                transaction.savepoint_rollback(sid)
                return HttpResponse(json.dumps({"result": "bad", "message": str(ex)}), content_type="application/json")

        elif action == 'cargainfopersona':
            try:
                data = {}
                tipopersona = TipoPersona.objects.get(id=request.POST['id_tipopersona'])
                # TIPO_DOCENTE,  TIPO_ESTUDIANTE, TIPO_ADMINISTRATIVO, TIPO_OTROS
                if Persona.objects.filter(Q(cedula__icontains=request.POST['cedula']) | Q(pasaporte__icontains=request.POST['cedula'])).exists():
                    if tipopersona.id == TIPO_DOCENTE:
                        profesor = Profesor.objects.filter(persona__id__in=Persona.objects.filter(Q(cedula__icontains=request.POST['cedula'])|
                                                                                                  Q(pasaporte__icontains=request.POST['cedula'])).values('id'),
                                                           activo=True).last()
                        rolperfilprofesor = RolPerfilProfesor.objects.filter(profesor=profesor).last()
                        if rolperfilprofesor:
                            if rolperfilprofesor.coordinacion:
                                data['facultad'] = [{'id': str(rolperfilprofesor.coordinacion.id), 'nombre': rolperfilprofesor.coordinacion.nombre}]
                        data['docente'] = True
                    elif tipopersona.id == TIPO_ESTUDIANTE:
                        inscripcion = Inscripcion.objects.filter(persona__id__in=Persona.objects.filter(Q(cedula__icontains=request.POST['cedula']) |
                                                                                                        Q(pasaporte__icontains=request.POST['cedula']))).last()
                        carreranombre = ''
                        carreraid = ''
                        facultad = ''
                        facultadid = ''
                        nivel = None
                        egresado = Egresado.objects.filter(inscripcion=inscripcion).last()
                        if egresado:
                            data['egresado'] = True
                            matricula = Matricula.objects.filter(inscripcion=inscripcion).last()
                            if matricula:
                                nivel = matricula.nivel
                                if nivel:
                                    carrera = nivel.carrera
                                    if carrera:
                                        carreranombre = carrera.nombre
                                        carreraid = carrera.id
                                        coordinacion = Coordinacion.objects.filter(carrera=carrera).last()
                                        if coordinacion:
                                            facultad = coordinacion.nombre
                                            facultadid = coordinacion.id
                            else:
                                carrera = inscripcion.carrera
                                if carrera:
                                    carreranombre = carrera.nombre
                                    carreraid = carrera.id
                                    coordinacion = Coordinacion.objects.filter(carrera=carrera).last()
                                    if coordinacion:
                                        facultad = coordinacion.nombre
                                        facultadid = coordinacion.id
                        else:
                            if inscripcion.modalidad:
                                data['modalidad'] = [{'id': str(inscripcion.modalidad.id), 'nombre': inscripcion.modalidad.nombre}]
                            matricula = Matricula.objects.filter(inscripcion=inscripcion).last()
                            if matricula:
                                nivel = matricula.nivel
                                if nivel:
                                    nivelnombre = str(nivel)
                                    carrera = nivel.carrera
                                    if carrera:
                                        carreranombre = carrera.nombre
                                        carreraid = carrera.id
                                        coordinacion = Coordinacion.objects.filter(carrera=carrera).last()
                                        if coordinacion:
                                            facultad = coordinacion.nombre
                                            facultadid = coordinacion.id

                                    data['nivel'] = [{'id': str(nivel.id), 'nombre': nivelnombre}]

                            else:
                                carrera = inscripcion.carrera
                                if carrera:
                                    carreranombre = carrera.nombre
                                    carreraid = carrera.id
                                    coordinacion = Coordinacion.objects.filter(carrera=carrera).last()
                                    if coordinacion:
                                        facultad = coordinacion.nombre
                                        facultadid = coordinacion.id

                            if nivel:
                                if nivel.sesion:
                                    data['jornada'] = [{'id': str(nivel.sesion.id), 'nombre': str(nivel.sesion)}]

                        data['carrera'] = [{'id': str(carreraid), 'nombre': carreranombre}]
                        data['facultad'] = [{'id': facultadid, 'nombre': facultad}]
                        data['alumno'] = True
                    elif tipopersona.id == TIPO_ADMINISTRATIVO:
                        departamentonombre = ''
                        departamentoid = ''
                        gruposexcluidos = [PROFESORES_GROUP_ID, ALUMNOS_GROUP_ID, SISTEMAS_GROUP_ID]
                        persona = Persona.objects.filter(id__in=Persona.objects.filter(Q(cedula__icontains=request.POST['cedula']) |
                                                                                   Q(pasaporte__icontains=request.POST['cedula'])).values('id'),
                                                         usuario__is_active=True, nacimiento__isnull=False).exclude(
                            usuario__groups__id__in=gruposexcluidos).exclude(usuario=None).last()
                        grupousuario = persona.usuario.groups.values('id')
                        if grupousuario:
                            departament = Group.objects.filter(id__in=grupousuario).first()
                            departamentoid = departament.id
                            departamentonombre = departament.name

                        data['departamento'] = [{'id': str(departamentoid), 'nombre': departamentonombre}]
                        data['administrativo'] = True

                data['result'] = 'ok'
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as ex:
                return HttpResponse(json.dumps({"result": "bad", "message": str(ex)}), content_type="application/json")


        elif action == 'cargainfoxperfil':
            try:
                data = {}
                idtipopersona = int(request.POST['tipopersona'])
                if idtipopersona == TIPO_ESTUDIANTE:
                    data['periodos'] = [{"id": p.id, "nombre": p.nombre} for p in Periodo.objects.filter(activo=True)]
                    data['estudiante'] = True
                elif idtipopersona == TIPO_DOCENTE:
                    data['periodos'] = [{"id": p.id, "nombre": p.nombre} for p in Periodo.objects.filter(activo=True)]
                    data['docente'] = True
                elif idtipopersona == TIPO_ADMINISTRATIVO:
                    gruposexcluidos = [PROFESORES_GROUP_ID, ALUMNOS_GROUP_ID, SISTEMAS_GROUP_ID]
                    administrativos = Persona.objects.filter(usuario__is_active=True, nacimiento__isnull=False).exclude(usuario__groups__id__in=gruposexcluidos).exclude(usuario=None).exclude(
                        Q(cedula__icontains='999999999') | Q(cedula__icontains='0999999999') | Q(pasaporte__icontains='999999999') | Q(pasaporte__icontains='0999999999')
                    ).exclude(cedula__isnull=True, pasaporte__isnull=True)
                    totaladministrativos = str(administrativos.count())
                    data['totaladministrativos'] = totaladministrativos
                    data['infototaladministrativos'] = totaladministrativos + ' administrativos'
                    data['administrativo'] = True

                data['result'] = 'ok'
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as ex:
                return HttpResponse(json.dumps({"result": "bad", "message": str(ex)}), content_type="application/json")


        elif action == 'cargainfoxcarrera':
            try:
                data = {}
                carrera = Carrera.objects.get(id=request.POST['carrera'])
                periodo = Periodo.objects.get(id=request.POST['periodo'])
                tipopersona = int(request.POST['tipopersona'])
                if tipopersona == TIPO_ESTUDIANTE:
                    data['infofecha'] = ("Desde " + str(periodo.inicio.day) + "-" + str(periodo.inicio.month) + "-" + str(periodo.inicio.year) +
                                         " hasta " + str(periodo.fin.day)) + "-" + str(periodo.fin.month) + "-" + str(periodo.fin.year)
                    matriculadosperiodo = Matricula.objects.filter(nivel__periodo__id=periodo.id, nivel__carrera__id=carrera.id, liberada=False)
                    totalalumnos = str(matriculadosperiodo.count())
                    data['totalalumnos'] = totalalumnos
                    data['infototalalumnos'] = totalalumnos + ' matriculados'
                elif tipopersona == TIPO_DOCENTE:
                    data['infofecha'] = ("Desde " + str(periodo.inicio.day) + "-" + str(periodo.inicio.month) + "-" + str(periodo.inicio.year) +
                                         " hasta " + str(periodo.fin.day)) + "-" + str(periodo.fin.month) + "-" + str(periodo.fin.year)
                    profesormateria = ProfesorMateria.objects.filter(materia__id__in=Materia.objects.filter(nivel__periodo__id=periodo.id, nivel__carrera__id=carrera.id).values('id'),
                                                                     profesor__activo=True)
                    totaldocentes = str(profesormateria.count())
                    data['totaldocentes'] = totaldocentes
                    data['infototaldocentes'] = totaldocentes + ' docentes'
                data['result'] = 'ok'
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as ex:
                return HttpResponse(json.dumps({"result": "bad", "message": str(ex)}), content_type="application/json")


        elif action == 'cargacarreras':
            try:
                data = {}
                idtipopersona = int(request.POST['tipopersona'])
                if idtipopersona == TIPO_ESTUDIANTE:
                    periodo = Periodo.objects.get(id=request.POST['periodo'])
                    carreras = Carrera.objects.filter(id__in=Nivel.objects.filter(periodo__id=periodo.id).values('carrera_id'), carrera=True, activo=True)
                    data['carreras'] = [{"id": c.id, "nombre": c.nombre} for c in carreras]

                    data['result'] = 'ok'
                elif idtipopersona == TIPO_DOCENTE:
                    periodo = Periodo.objects.get(id=request.POST['periodo'])
                    carreras = Carrera.objects.filter(id__in=Nivel.objects.filter(periodo__id=periodo.id).values('carrera_id'), carrera=True, activo=True)
                    data['carreras'] = [{"id": c.id, "nombre": c.nombre} for c in carreras]

                    data['result'] = 'ok'
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as ex:
                return HttpResponse(json.dumps({"result": "bad", "message": str(ex)}), content_type="application/json")

        elif action == 'guardavisitagrupal':
            sid = transaction.savepoint()
            try:
                data = {}
                tipopersona = TipoPersona.objects.get(id=request.POST['tipopersona'])
                numvisita = int(request.POST['numvisita'])

                listapersonavisita = []

                if tipopersona.id == TIPO_ESTUDIANTE:
                    if 'periodo' in request.POST:
                        periodo = Periodo.objects.get(id=request.POST['periodo'])
                        carrera = Carrera.objects.get(id=request.POST['carrera'])
                        matriculas = Matricula.objects.filter(nivel__periodo__id=periodo.id, nivel__carrera__id=carrera.id, liberada=False).order_by('?')[:numvisita]
                        for m in matriculas:
                            inscripcion = m.inscripcion
                            persona = inscripcion.persona
                            nivel = m.nivel
                            jornada = nivel.sesion
                            visita = crearvisitaautomatica(persona, tipopersona)
                            if visita:
                                # ------------ campos segun el perfil (tipo persona) --------- #
                                visita.carrera = carrera
                                coordinacion = Coordinacion.objects.filter(carrera=carrera).last()
                                if coordinacion:
                                    visita.facultad = coordinacion
                                # egresado = Egresado.objects.filter(inscripcion=inscripcion).last()
                                # if egresado:
                                #     visita.egresado = True
                                # else:
                                # se comenta porque como se está cogiendo directamente desde un nivel
                                visita.modalidad = inscripcion.modalidad
                                visita.nivel = nivel
                                visita.jornada = jornada
                                visita.save()
                                # ---------- fin campos segun perfil ----------- #
                                detallevisita = creardetallevisitaautomatica(visita, tipopersona, request)
                                if detallevisita:
                                    client_address = ip_client_address(request)
                                    LogEntry.objects.log_action(
                                        user_id=request.user.pk,
                                        content_type_id=ContentType.objects.get_for_model(visita).pk,
                                        object_id=visita.id,
                                        object_repr=force_str(visita),
                                        action_flag=CHANGE,
                                        change_message='Visita creada' + ' (' + client_address + ')')
                                    # se llena un arreglo con los nombres de las personas a las que se le creó la visita
                                    listapersonavisita.append(persona.nombre_completo())
                                else:
                                    return HttpResponse(json.dumps({"result": "bad", "message": str("No se creó la visita (detallevisita)")}), content_type="application/json")
                            else:
                                return HttpResponse(json.dumps({"result": "bad", "message": str("No se creó la visita")}), content_type="application/json")

                elif tipopersona.id == TIPO_DOCENTE:
                    if 'periodo' in request.POST:
                        periodo = Periodo.objects.get(id=request.POST['periodo'])
                        carrera = Carrera.objects.get(id=request.POST['carrera'])
                        profesores = ProfesorMateria.objects.filter(materia__id__in=Materia.objects.filter(nivel__periodo__id=periodo.id, nivel__carrera__id=carrera.id).values('id'),
                                                                    profesor__activo=True).order_by('?')[:numvisita]
                        for p in profesores:
                            profesor = p.profesor
                            persona = profesor.persona
                            visita = crearvisitaautomatica(persona, tipopersona)
                            if visita:
                                # ------------ campos segun el perfil (tipo persona) --------- #
                                visita.carrera = carrera
                                coordinacion = Coordinacion.objects.filter(carrera=carrera).last()
                                if coordinacion:
                                    visita.facultad = coordinacion
                                visita.save()
                                # ---------- fin campos segun perfil ----------- #
                                detallevisita = creardetallevisitaautomatica(visita, tipopersona, request)
                                if detallevisita:
                                    client_address = ip_client_address(request)
                                    LogEntry.objects.log_action(
                                        user_id=request.user.pk,
                                        content_type_id=ContentType.objects.get_for_model(visita).pk,
                                        object_id=visita.id,
                                        object_repr=force_str(visita),
                                        action_flag=CHANGE,
                                        change_message='Visita creada' + ' (' + client_address + ')')
                                    # se llena un arreglo con los nombres de las personas a las que se le creó la visita
                                    listapersonavisita.append(persona.nombre_completo())
                            else:
                                return HttpResponse(json.dumps({"result": "bad", "message": str("No se creó la visita")}), content_type="application/json")

                elif tipopersona.id == TIPO_ADMINISTRATIVO:
                    gruposexcluidos = [PROFESORES_GROUP_ID, ALUMNOS_GROUP_ID, SISTEMAS_GROUP_ID]
                    administrativos = Persona.objects.filter(usuario__is_active=True, nacimiento__isnull=False).exclude(usuario__groups__id__in=gruposexcluidos).exclude(usuario=None).exclude(
                        Q(cedula__icontains='999999999') | Q(cedula__icontains='0999999999') | Q(pasaporte__icontains='999999999') | Q(pasaporte__icontains='0999999999')
                    ).exclude(cedula__isnull=True, pasaporte__isnull=True).order_by('?')[:numvisita]
                    for persona in administrativos:
                        visita = crearvisitaautomatica(persona, tipopersona)
                        if visita:
                            # ------------ campos segun el perfil (tipo persona) --------- #
                            grupousuario = persona.usuario.groups.values('id')
                            if grupousuario:
                                departamento = Group.objects.filter(id__in=grupousuario).first()
                                visita.departamento = departamento
                                visita.save()
                            # ---------- fin campos segun perfil ----------- #
                            detallevisita = creardetallevisitaautomatica(visita, tipopersona, request)
                            if detallevisita:
                                client_address = ip_client_address(request)
                                LogEntry.objects.log_action(
                                    user_id=request.user.pk,
                                    content_type_id=ContentType.objects.get_for_model(visita).pk,
                                    object_id=visita.id,
                                    object_repr=force_str(visita),
                                    action_flag=CHANGE,
                                    change_message='Visita creada' + ' (' + client_address + ')')
                                # se llena un arreglo con los nombres de las personas a las que se le creó la visita
                                listapersonavisita.append(persona.nombre_completo())
                        else:
                            return HttpResponse(json.dumps({"result": "bad", "message": str("No se creó la visita")}), content_type="application/json")

                if listapersonavisita:
                    data['listapersonavisita'] = listapersonavisita
                    data['result'] = 'ok'
                    transaction.savepoint_commit(sid)
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as ex:
                transaction.savepoint_rollback(sid)
                return HttpResponse(json.dumps({"result": "bad", "message": str(ex)}), content_type="application/json")


        return HttpResponseRedirect("/visitabiblioteca")
    else:
        data = {'title': 'Listado de Visitas a Biblioteca'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='add':
                data['title'] = 'Nueva Visita'

                # insf = VisitaBibliotecaForm(initial={'fecha': datetime.now()})
                # insf.set_add_mode()
                # else:
                client_address = ip_client_address(request)
                if Aula.objects.filter(ip=str(client_address),activa=False).exists():
                    aula = Aula.objects.filter(ip=str(client_address),activa=False)[:1].get()
                    insf = VisitaBibliotecaForm(initial={'fecha': datetime.now(),'sede':aula.sede})
                    data['idsede']= aula.sede.id
                else:
                    insf = VisitaBibliotecaForm(initial={'fecha': datetime.now()})
                data['form'] = insf
                data['utiliza_grupos_alumnos'] = UTILIZA_GRUPOS_ALUMNOS
                data['grupos_abiertos'] = Grupo.objects.filter(abierto=True).order_by('-nombre')
                data['centroexterno'] = CENTRO_EXTERNO
                data['inscripcion_conduccion'] = INSCRIPCION_CONDUCCION
                data['tipovisita'] = TipoVisitasBiblioteca.objects.filter().order_by('descripcion')
                data['tipoarticulo'] = TipoArticulo.objects.filter(estado=True).order_by('descripcion')

                # carga opciones para los combos
                sedes = Sede.objects.filter(solobodega=False).order_by('nombre')
                data['sedes'] = sedes
                tiposervicio = TipoVisitasBiblioteca.objects.all().order_by('descripcion')
                data['tiposervicio'] = tiposervicio

                return render(request ,"visitabiblioteca/adicionarbs.html" ,  data)

            elif action=='detalle':
                data = {}
                data['visita'] = DetalleVisitasBiblioteca.objects.filter(visitabiblioteca=request.GET['visita']).order_by('fecha')
                return render(request ,"visitabiblioteca/detallevisita.html" ,  data)

            elif action == 'addvarios':
                data['title'] = 'Nuevas visitas'
                # carga opciones para los combos
                sedes = Sede.objects.filter(solobodega=False).order_by('nombre')
                data['sedes'] = sedes
                tiposervicio = TipoVisitasBiblioteca.objects.all().order_by('descripcion')
                data['tiposervicio'] = tiposervicio

                # tipo de personas
                # TIPO_DOCENTE,  TIPO_ESTUDIANTE, TIPO_ADMINISTRATIVO, TIPO_OTROS
                listaperfiles = [TIPO_DOCENTE, TIPO_ESTUDIANTE, TIPO_ADMINISTRATIVO]
                data['tipoperfiles'] = TipoPersona.objects.filter(id__in=listaperfiles)
                data['TIPO_DOCENTE'] = TIPO_DOCENTE
                data['TIPO_ESTUDIANTE'] = TIPO_ESTUDIANTE
                data['TIPO_ADMINISTRATIVO'] = TIPO_ADMINISTRATIVO

                return render(request, "visitabiblioteca/addvariasvisitas.html", data)

        else:
            search = None
            todos = None

            if 's' in request.GET:
                search = request.GET['s']
            if 't' in request.GET:
                todos = request.GET['t']
            if search:
                ss = search.split(' ')
                while '' in ss:
                    ss.remove('')
                visitabiblioteca = VisitaBiblioteca.objects.filter(Q(nombre__icontains=search) | Q(cedula__icontains=search)).order_by('nombre')
                # else:
                #     visitabiblioteca = VisitaBiblioteca.objects.filter(Q(persona__apellido1__icontains=ss[0]) & Q(persona__apellido2__icontains=ss[1])).order_by('persona__apellido1','persona__apellido2','persona__nombres')


            elif 'g' in request.GET:
                grupoid = request.GET['g']
                data['grupo'] = TipoPersona.objects.get(pk=request.GET['g'])
                data['grupoid'] = int(grupoid) if grupoid else ""
                visitabiblioteca = VisitaBiblioteca.objects.filter(tipopersona=data['grupo'])
            elif 'se' in request.GET:
                grupoids = request.GET['se']
                data['grupose'] = Sede.objects.get(pk=request.GET['se'])
                data['grupoids'] = int(grupoids) if grupoids else ""
                visitabiblioteca = VisitaBiblioteca.objects.filter(detallevisitasbiblioteca__sede=data['grupose']).distinct()
            else:
                 visitabiblioteca = VisitaBiblioteca.objects.all().order_by('nombre')

            paging = MiPaginador(visitabiblioteca, 30)
            p = 1
            try:
                if 'page' in request.GET:
                    p = int(request.GET['page'])
                page = paging.page(p)
            except Exception as ex:
                print(ex)
                page = paging.page(p)

            data['paging'] = paging
            data['rangospaging'] = paging.rangos_paginado(p)
            data['page'] = page
            data['search'] = search if search else ""
            data['todos'] = todos if todos else ""
            data['visitabiblioteca'] = page.object_list
            data['utiliza_grupos_alumnos'] = UTILIZA_GRUPOS_ALUMNOS
            data['reporte_ficha_id'] = REPORTE_CERTIFICADO_INSCRIPCION
            data['clave'] = DEFAULT_PASSWORD
            data['usafichamedica'] = UTILIZA_FICHA_MEDICA
            data['centroexterno'] = CENTRO_EXTERNO
            data['matriculalibre'] = MODELO_EVALUACION==EVALUACION_TES
            data['grupos'] = TipoPersona.objects.all().order_by('descripcion')
            data['gruposede'] = Sede.objects.all().order_by('nombre')
            data['visitaform'] = RVisitaBiblioForm(initial={'inicio': datetime.now().date(), 'fin': datetime.now().date()})
            return render(request ,"visitabiblioteca/visitabiblioteca.html" ,  data)
