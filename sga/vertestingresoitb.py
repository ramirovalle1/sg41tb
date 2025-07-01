from datetime import datetime
from django.contrib.auth.decorators import login_required
import json

from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render

from med.models import PersonaEstadoCivil
from sga.commonviews import addUserData, ip_client_address
from sga.models import Periodo, EncuestaItb, Persona, Deporte, MotivoSeleccion, DeseosFuturos, Inscripcion, \
    InscripcionTestIngreso, PreguntaTestIngreso, RespuestaInscripcionTest, ConclusionesTest, Test, Encuesta, Grupo, \
    RespuestaTestIngreso, ZonaResidencia, CondicionesHogar, MaterialCasa, TipoServicio, Afiliacion, TipoIngresoHogar, \
    TipoIngresoPropio, TipoEmpleo, UsoTransporte, TipoTransporte, ManifestacionArtistica, PerfilInscripcion, ProcesoDobe

from django.core.paginator import Paginator
from fpdf import FPDF
from settings import MEDIA_URL, SITE_ROOT, MEDIA_ROOT, NOTA_PARA_APROBAR, TEST_EXCELENTE, TEST_BUENO, TEST_REGULAR
import os
import unicodedata
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
def nombremeses(mes):

    if mes==1:
        return 'enero'
    elif mes==2:
        return 'febrero'
    elif mes==3:
        return 'marzo'
    elif mes==4:
        return 'abril'
    elif mes==5:
        return 'mayo'
    elif mes==6:
        return 'junio'
    elif mes==7:
        return 'julio'
    elif mes==8:
        return 'agosto'
    elif mes==9:
        return 'septiembre'
    elif mes==10:
        return 'octubre'
    elif mes==11:
        return 'novimebre'
    elif mes==12:
        return 'diciembre'
def add_page_with_logo(pdf, title, subtitle=None, logo_path=None):
    pdf.add_page()
    if logo_path:
        pdf.image(logo_path, x=10, y=8, w=30)
    pdf.set_font('Arial', 'B', 14)
    pdf.set_y(40)
    pdf.set_x(10)
    pdf.multi_cell(0, 10, title, 0, 'C')
    pdf.ln(10)
    if subtitle:
        pdf.set_font('Arial', 'B', 12)
        pdf.multi_cell(0, 10, subtitle, 0, 'C')
        pdf.ln(10)
def add_two_boxes(pdf, text1, text2, width1=90, width2=90, height=8):
    pdf.multi_cell(width1, height, text1, border=1)
    pdf.set_x(pdf.get_x() + width1)
    pdf.multi_cell(width2, height, text2, border=1)
    pdf.ln(height)

def draw_radio_button(self, x, y, selected=False):
    self.set_xy(x, y)
    if selected:
        self.cell(10, 10, '●', 0, 0)
    else:
        self.cell(10, 10, 'o', 0, 0)

def add_parrafo_inicial(pdf, text, font_size=9, align='J', line_height=7):
    pdf.set_font('Arial', '', font_size)
    pdf.multi_cell(0, line_height, text, align=align)
    pdf.ln(1)

def add_parrafo(pdf, text, font_size=10, align='J', line_height=7):
    pdf.set_font('Arial', '', font_size)
    pdf.multi_cell(0, line_height, text, align=align)
    pdf.ln(1)

def add_parrafo_negrita(pdf, text, font_size=9, align='J', line_height=7):
    pdf.set_font('Arial', 'B', font_size)
    pdf.multi_cell(0, line_height, text, align=align)
    pdf.ln(1)
def add_parrafo_negrita_titulo(pdf, text, font_size=12, align='J', line_height=7):
    pdf.set_font('Arial', 'B', font_size)
    pdf.multi_cell(0, line_height, text, align=align)
    pdf.ln(1)
def documentacioninforme(grupo):
    try:
        elements = []
        pdf = FPDF(format='A4')
        pdf.add_page('Portrait')

        # ENCABEZADO
        pdf.image(SITE_ROOT + '/static/images/logo.png', 15, 15, 27, 27)  # Logo
        pdf.set_font('Arial', 'B', 12) #Titulo
        pdf.set_xy(50, 6)
        pdf.cell(w=100, h=20, txt="INSTITUTO SUPERIOR UNIVERSITARIO BOLIVARIANO DE TECNOLOGÍA", border=0)

        pdf.set_font('Arial', 'B', 12)  # Arial bold 12
        pdf.set_xy(60, 13)
        pdf.cell(w=100, h=20, txt="Dirección: VÍCTOR MANUEL RENDÓN 236 Y PEDRO CARBO", border=0)

        pdf.set_xy(90, 21)
        pdf.cell(w=100, h=20, txt="Teléfonos: 5000175 - 1800-ITBITB", border=0)

        pdf.set_xy(65, 29)
        pdf.cell(w=100, h=20, txt="Correo: info@bolivariano.edu.ec - Web:www.itb.edu.ec", border=0)
        pdf.ln(11)
        ######

        pdf.set_font('Arial', 'B', 9)
        fechahoy = datetime.now()
        pdf.cell(0, 10, 'Fecha de Impresión: ' + format(fechahoy.day) + " de " + nombremeses(fechahoy.month) + ", del " + format(fechahoy.year), 0, 0, 'R')
        pdf.ln(11)

        pdf.set_font('Arial', 'B', 12)
        # Obtener el ancho de la página
        page_width = pdf.w - 2 * pdf.l_margin  # Ancho de la página menos los márgenes

        # Agregar el texto centrado
        pdf.cell(page_width, 10, "DIAGNÓSTICO Y CARACTERIZACIÓN DE ESTUDIANTES QUE INGRESAN AL ITB", align='C')
        pdf.ln(10)

        pdf.set_font('Arial', 'B', 9)
        add_parrafo_negrita(pdf,"Objetivo:")
        add_parrafo_inicial(pdf,"Identificar las características individuales, intereses y habilidades potenciales, así como posibles obstáculos que pudieran afectar el proceso formativo, "
                          "como base para el acompañamiento pedagógico a los estudiantes. Esta estrategia busca prevenir o mitigar los factores que puedan obstaculizar el éxito estudiantil, al mismo tiempo que "
                          "fortalece la motivación profesional, la permanencia y la formación integral a lo largo de toda la carrera.")
        # ENCUESTA ITB
        add_parrafo_negrita_titulo(pdf,"I.	INFORMACIÓN GENERAL DEL GRUPO: {}".format(grupo.nombre))
        encuestas = EncuestaItb.objects.filter(estadorealizado=True,grupo = grupo.id)
        total_encuestados = encuestas.count()
        add_parrafo_inicial(pdf, "1. Total, de estudiantes: {}".format(total_encuestados))
        total_mujer = encuestas.filter(sexo_id=1).count() #Mujer
        total_hombre = encuestas.filter(sexo_id=2).count()  # Hombre
        add_parrafo_inicial(pdf,"Total, de hombres: {}".format(total_hombre))
        add_parrafo_inicial(pdf,"Total, de mujeres: {}".format(total_mujer))

        add_parrafo_inicial(pdf, "2. Estado Civil:")
        listado_estadocivil=[]
        estado_civil = PersonaEstadoCivil.objects.filter()
        for estado in estado_civil:
            estadocivil_conteo = encuestas.filter(estadocivil=estado).count()
            listado_estadocivil.append("{}: {}".format(estado.nombre, estadocivil_conteo))
        listado_estadocivil2 = "\n".join(listado_estadocivil)
        add_parrafo_inicial(pdf, "{}".format(listado_estadocivil2))

        add_parrafo_negrita(pdf,"CONDICIONES DE VIDA DE LOS ESTUDIANTES")
        add_parrafo_inicial(pdf, "1. Zona Residencia:")
        listado_zonaresidencia = []
        zonaresidencia = ZonaResidencia.objects.filter()
        for zona in zonaresidencia:
            zonaresidencia_conteo = encuestas.filter(zona=zona).count()
            listado_zonaresidencia.append("{}: {}".format(zona.nombre, zonaresidencia_conteo))
        listado_zonaresidencia2 = "\n".join(listado_zonaresidencia)
        add_parrafo_inicial(pdf, "{}".format(listado_zonaresidencia2))

        add_parrafo_inicial(pdf, "2. Condiciones del hogar:")
        listado_condiciones = []
        condiciones = CondicionesHogar.objects.filter()
        for c in condiciones:
            condiciones_conteo = encuestas.filter(condicion=c).count()
            listado_condiciones.append("{}: {}".format(c.nombre, condiciones_conteo))
        listado_condiciones2 = "\n".join(listado_condiciones)
        add_parrafo_inicial(pdf, "{}".format(listado_condiciones2))

        add_parrafo_inicial(pdf, "3. Materiales de construccion de la casa:")
        listado_materiales = []
        materiales = MaterialCasa.objects.filter()
        for mat in materiales:
            materiales_conteo = encuestas.filter(materialcasa=mat).count()
            listado_materiales.append("{}: {}".format(mat.nombre, materiales_conteo))
        listado_materiales2 = "\n".join(listado_materiales)
        add_parrafo_inicial(pdf, "{}".format(listado_materiales2))

        add_parrafo_inicial(pdf, "4. Servicios:")
        listado_servicios = []
        servicios = TipoServicio.objects.filter()
        for ser in servicios:
            servicios_conteo = encuestas.filter(servicio=ser).count()
            listado_servicios.append("{}: {}".format(ser.nombre, servicios_conteo))
        listado_servicios2 = "\n".join(listado_servicios)
        add_parrafo_inicial(pdf, "{}".format(listado_servicios2))

        add_parrafo_inicial(pdf, "5. Afiliación:")
        listado_afiliacion = []
        afiliacion = Afiliacion.objects.filter()
        for a in afiliacion:
            afiliacion_conteo = encuestas.filter(afiliacion=a).count()
            listado_afiliacion.append("{}: {}".format(a.nombre, afiliacion_conteo))
        listado_afiliacion2 = "\n".join(listado_afiliacion)
        add_parrafo_inicial(pdf, "{}".format(listado_afiliacion2))

        add_parrafo_negrita(pdf,"DESEMPLEO, INGRESO Y GASTOS")
        add_parrafo_inicial(pdf, "1. Ingresos en el hogar:")
        listado_ingresohogar = []
        ingresos_hogar = TipoIngresoHogar.objects.filter()
        for ih in ingresos_hogar:
            ingresohogar_conteo = encuestas.filter(ingresohogar=ih).count()
            listado_ingresohogar.append("{}: {}".format(ih.nombre, ingresohogar_conteo))
        listado_ingresohogar2 = "\n".join(listado_ingresohogar)
        add_parrafo_inicial(pdf, "{}".format(listado_ingresohogar2))

        add_parrafo_inicial(pdf, "2.Ingresos propios:")
        listado_ingresopropio = []
        ingresos_propio = TipoIngresoPropio.objects.filter()
        for ip in ingresos_propio:
            ingresopropio_conteo = encuestas.filter(ingresopropio=ip).count()
            listado_ingresopropio.append("{}: {}".format(ip.nombre, ingresopropio_conteo))
        listado_ingresopropio2 = "\n".join(listado_ingresopropio)
        add_parrafo_inicial(pdf, "{}".format(listado_ingresopropio2))

        add_parrafo_inicial(pdf, "3.Empleo:")
        listado_empleos = []
        empleos = TipoEmpleo.objects.filter()
        for e in empleos:
            empleos_conteo = encuestas.filter(empleo=e).count()
            listado_empleos.append("{}: {}".format(e.nombre, empleos_conteo))
        listado_empleos2 = "\n".join(listado_empleos)
        add_parrafo_inicial(pdf, "{}".format(listado_empleos2))

        add_parrafo_negrita(pdf,"TRANSPORTE Y MOVILIZACIÓN")
        add_parrafo_inicial(pdf, "1. Uso del transporte:")
        listado_usotransporte = []
        usotransporte = UsoTransporte.objects.filter()
        for u in usotransporte:
            usotransporte_conteo = encuestas.filter(usotransporte=u).count()
            listado_usotransporte.append("{}: {}".format(u.nombre, usotransporte_conteo))
        listado_usotransporte2 = "\n".join(listado_usotransporte)
        add_parrafo_inicial(pdf, "{}".format(listado_usotransporte2))

        add_parrafo_inicial(pdf, "2. Transporte:")
        listado_transporte = []
        transportes = TipoTransporte.objects.filter()
        for tr in transportes:
            transportes_conteo = encuestas.filter(transporte=tr).count()
            listado_transporte.append("{}: {}".format(tr.nombre, transportes_conteo))
        listado_transporte2 = "\n".join(listado_usotransporte)
        add_parrafo_inicial(pdf, "{}".format(listado_transporte2))

        add_parrafo_negrita(pdf," INCLINACIÓN POR EL DEPORTE Y MANIFESTACIONES ARTÍSTICAS:")
        add_parrafo_inicial(pdf, "1. Deportes (opción multiple):")
        listado_deportes = []
        deportes = Deporte.objects.filter()
        for d in deportes:
            deportes_conteo = encuestas.filter(deporte__icontains=d.id).count()
            listado_deportes.append("{}: {}".format(d.nombre, deportes_conteo))
        listado_deportes2 = ";  ".join(listado_deportes)
        add_parrafo_inicial(pdf, "{}".format(listado_deportes2))

        add_parrafo_inicial(pdf, "2. Manifestaciones artísticas:")
        listado_manifestaciones = []
        manifestaciones = ManifestacionArtistica.objects.filter()
        for m in manifestaciones:
            manifestaciones_conteo = encuestas.filter(manifestacion=m).count()
            listado_manifestaciones.append("{}: {}".format(m.nombre, manifestaciones_conteo))
        listado_manifestaciones2 = "\n".join(listado_manifestaciones)
        add_parrafo_inicial(pdf, "{}".format(listado_manifestaciones2))

        add_parrafo_negrita(pdf,"SOBRE MOTIVACIÓN Y ELECCIÓN DE LA CARRERA")

        add_parrafo_inicial(pdf, "1. Motivo de selección:")
        listado_motivos = []
        motivaciones = MotivoSeleccion.objects.filter()
        for mot in motivaciones:
            motivaciones_conteo = encuestas.filter(motivo__icontains=mot.id).count()
            listado_motivos.append("{}: {}".format(mot.nombre, motivaciones_conteo))
        listado_motivos2 = "\n".join(listado_motivos)
        add_parrafo_inicial(pdf, "{}".format(listado_motivos2))

        # TEST INGRESO
        pdf.add_page()
        add_parrafo_negrita_titulo(pdf,"II.	CONOCIMIENTOS ANTECEDENTES Y EXPERIENCIAS PREVIAS EN ASIGNATURAS BÁSICAS GENERALES:")
        for t in Test.objects.filter(id__in=[1,2,3],estado=True):
            inscripciones = InscripcionTestIngreso.objects.filter(grupo=grupo.id,finalizado=True, test=t)
            if inscripciones:
                add_parrafo_negrita(pdf,"RESULTADO DEL DIAGNÓSTICO DE {}".format(t.titulo))
                total_inscripciones = inscripciones.count()
                if total_inscripciones:
                    add_parrafo_inicial(pdf, "Total, de estudiantes evaluados: {}".format(total_inscripciones))

                    # APROBADOS
                    aprobados = inscripciones.filter(puntaje__gte= NOTA_PARA_APROBAR).count()
                    porcentaje_aprobados = (aprobados*100)/total_inscripciones

                    add_parrafo_inicial(pdf, "Total, de estudiantes aprobados {} que representa el {}%".format(aprobados,porcentaje_aprobados))
                    add_parrafo_inicial(pdf, "Comportamiento por rango de calificación")

                    # tabla de calificacion de aprobados
                    # cabecera de la tabla
                    cabecera = ["NRO.", "EXCELENTE","BUENO", "REGULAR"]
                    w = [15, 50, 40, 40]
                    for i in range(0, len(cabecera)):
                        pdf.cell(w[i], 5, cabecera[i], 1, 0, 'C', 0)
                    pdf.ln()
                    # Filtrar las calificaciones
                    calificacion_excelente = inscripciones.filter(puntaje__gte=TEST_EXCELENTE).count() #90-100
                    calificacion_buena = inscripciones.filter(puntaje__lt=TEST_EXCELENTE, puntaje__gte=TEST_BUENO).count() #80-89
                    calificacion_regular = inscripciones.filter(puntaje__lt=TEST_BUENO, puntaje__gte=TEST_REGULAR).count() #70-79

                    # Contar los resultados y escribirlos en el PDF
                    pdf.cell(w[0], 5, "", 1)
                    pdf.cell(w[1], 5, str(calificacion_excelente), 1,0, 'C',)
                    pdf.cell(w[2], 5, str(calificacion_buena), 1, 0,'C',)
                    pdf.cell(w[3], 5, str(calificacion_regular), 1,0, 'C',)
                    pdf.ln()

                    add_parrafo_inicial(pdf, "En el grupo {} se evidencia que {} estudiantes lograron una calificación excelente,"
                                             "mientras que {} estudiantes lograron calificación Buena, "
                                             "sin embargo, {} alcanzaron notas regulares".format(grupo.nombre,calificacion_excelente,calificacion_buena,calificacion_regular))
                    # REPROBADOS
                    reprobados = inscripciones.filter(puntaje__lt=NOTA_PARA_APROBAR).count()
                    porcentaje_reprobados = (reprobados * 100) / total_inscripciones

                    add_parrafo_inicial(pdf, "Total, de estudiantes reprobados {} que representa el {}%".format(reprobados,porcentaje_reprobados))

                    if reprobados:
                        add_parrafo_inicial(pdf,"En este grupo, {} estudiantes desaprobaron la {}, que representa el {}% del total de estudiantes evaluados."
                                                "Los dominios académicos que evidencian mayor dificultad fueron: ".format(reprobados, t.titulo.lower(), porcentaje_reprobados))
                        add_parrafo_inicial(pdf,"Por ejemplo:")

                    # puntuacion de preguntas con puntaje menor a 70

                    pdf.set_font('Arial', 'B', 9)
                    pdf.cell(w=100,h=20, txt="Relación nominal de estudiantes que desaprobaron:")

                    lista = inscripciones.values_list('persona', flat=True)
                    listpersona = Persona.objects.filter(id__in=lista)
                    pdf.ln(12)

                    pdf.set_font('Arial', '', 9)
                    nombres_completos = "\n".join(["{}. {}".format(i+1,persona.nombre_completo_inverso()) for i,persona in enumerate(listpersona)])
                    pdf.multi_cell(110, 8, "N1. Apellidos y Nombres:\n{}".format(nombres_completos))
                    pdf.ln(5)
        pdf.add_page()
        add_parrafo_negrita_titulo(pdf,"III.	RESULTADO DEL DIAGNÓSTICO DE MOTIVACIÓN Y ELECCIÓN DE LA CARRERA")
        cantidad_miembro= grupo.miembros().count()
        inscritos_grupo = grupo.miembros().values('id')
        inscritos_encuesta = EncuestaItb.objects.filter(inscripcion__in= inscritos_grupo).count()
        add_parrafo_inicial(pdf,"	Proyección profesional: Intereses, motivaciones y expectativas")
        add_parrafo_inicial(pdf,"	Se evidencia que es un grupo que necesita motivación para realizar las actividades que se indican, "
                                "pues solo {}/{} estudiantes han realizado la encuesta donde se evidencian su proyección de vida, intereses, deseos, motivos etc."
                                 " Por lo que se sugiere tener en cuenta durante el proceso docente educativo".format(inscritos_encuesta,cantidad_miembro))
        listadosignos=[]
        id_personas_contador={}
        for t in Test.objects.filter(id__in=[1, 2, 3], estado=True):
            listadoinscripciones = InscripcionTestIngreso.objects.filter(grupo=grupo.id, finalizado=True, test=t, puntaje__lt=TEST_REGULAR)
            if listadoinscripciones:
                listadosignos.append(t.titulo.lower())
                for inscripcion in listadoinscripciones:
                    id_persona = inscripcion.persona.id
                    if id_persona in id_personas_contador:
                        id_personas_contador[id_persona]+=1
                    else:
                        id_personas_contador[id_persona] = 1 #contador

        reprobados_todostest= [estudianteid for estudianteid, count in id_personas_contador.items() if count == 3]

        if listadosignos:
            nombre_test = ', '.join(listadosignos)
            add_parrafo_negrita_titulo(pdf, "IV.	IDENTIFICACIÓN DE TIPOS DE SIGNOS DE ALARMA")
            add_parrafo_inicial(pdf, "Una gran cantidad de estudiantes se encuentran desaprobados en áreas a fines a la especialidad como son la {}.".format(nombre_test))
            if reprobados_todostest:
                add_parrafo_inicial(pdf, "Sin embargo, llama la atención que estudiantes desaporobaron en las tres materias con notas muy bajas.")
                add_parrafo_negrita(pdf, "Relación nominal de estudiantes con signos de alarmas:")
                personas_reprobadas = Persona.objects.filter(id__in = reprobados_todostest)
                nombres_completos = "\n".join(
                    ["{}. {}".format(i + 1, persona.nombre_completo_inverso())
                     for i,persona in enumerate(personas_reprobadas)] )
                pdf.set_font('Arial', '', 9)
                pdf.multi_cell(110, 8, "N1. Apellidos y Nombres:\n{}".format(nombres_completos))

            add_parrafo_negrita(pdf,"ACOMPAÑAMIENTO/ RECOMENDACIONES PARA LA ESTUDIANTE CON SIGNOS DE ALARMAS")
            add_parrafo_inicial(pdf,"1-Observar sistemáticamente para determinar si presenta dificultades académicas o comportamentales asociadas a la motivación. \n" 
                                         "2-Prestar los niveles de ayuda (orientación, explicación, ejemplificación, demostración o elaboración conjunta), en caso necesario para resolver las actividades que se indican durante el proceso docente. \n"
                                         "3- Determinar su estilo de aprendizaje (visual, auditivo, kinestésico o mixto) para apoyarse en él si fuera necesario. \n"
                                         "4- En caso que se evidencie que la estudiante presenta dificultades en el aprendizaje o en el comportamiento de forma sistemática y persistente en el tiempo, que puedan estar incidiendo en el rendimiento académico, derivar al Departamento de Bienestar Estudiantil para proceder a pedir evaluación externa que justifique si posee Necesidades Educativas asociadas o no a discapacidad.")
            pdf.ln(5)
        pdf.ln(5)
        pdf.add_page()
        inscritos = grupo.miembros().values('id')
        listado_personadiscapacidad = PerfilInscripcion.objects.filter(inscripcion__in=inscritos,tienediscapacidad=True)
        contador_listado_personadiscapacidad = listado_personadiscapacidad.count()
        if listado_personadiscapacidad:
            add_parrafo_negrita_titulo(pdf, "V.	IDENTIFICACIÓN DE NECESIDADES EDUCATIVAS ESPECIALES")
            add_parrafo_inicial(pdf,"Existen {} estudiantes con Necesidades Educativas asociadas a discapacidades :".format(contador_listado_personadiscapacidad))
            add_parrafo_negrita(pdf,"MOTIVOS DE LA DISCAPACIDAD")
            for lp in listado_personadiscapacidad:
                tipo_discapacidad = lp.tipodiscapacidad.nombre.lower()
                porcentaje = lp.porcientodiscapacidad
                # procesodobe = ProcesoDobe.objects.filter(inscripcion = lp.inscripcion.id)[:1].get()
                add_parrafo_inicial(pdf, "-. El estudiante {}, tiene una discapacidad {} del {}%".format(lp.inscripcion.persona.nombre_completo_inverso(), tipo_discapacidad,porcentaje))
                pdf.ln(2)

            add_parrafo_negrita(pdf,"Relación nominal de estudiantes que desaprobaron:")
            lista = listado_personadiscapacidad.values_list('inscripcion__persona', flat=True)
            listpersona = Persona.objects.filter(id__in=lista)
            pdf.set_font('Arial', '', 9)
            nombres_completos = "\n".join(["{}. {}".format(i + 1, persona.nombre_completo_inverso()) for i, persona in enumerate(listpersona)])
            pdf.multi_cell(110, 8, "N1. Apellidos y Nombres:\n{}".format(nombres_completos))
        pdf.ln(5)

        add_parrafo_negrita(pdf,"ACOMPAÑAMIENTO/ RECOMENDACIONES PARA EL ESTUDIANTE CON NECESIDAD EDUCATIVA.")
        add_parrafo_inicial(pdf,"1. Ubicarlo cerca del docente para brindarle el apoyo oportuno. \n"
                                     "2. En cada inicio de una nueva actividad dar instrucciones cortas y precisas, asegurándose de que lo ha comprendido. \n"
                                     "3. Corroborar si ha entendido el contenido y de ser posible, explicarle mediante la ejemplificación, demostración o elaboración conjunta. \n"
                                     "4. Leer el examen y dar más tiempo si fuese necesario. \n"
                                     "5. Ubicar en grupos, donde exista un estudiante con actitud generosa pueda servirle como tutor o apoyo durante el trabajo.\n"
                                     "6. Permitir durante las exposiciones el apoyo de medios, como tarjetas diapositivas u otras.")

        add_parrafo_negrita(pdf,"ACOMPAÑAMIENTO/ RECOMENDACIONES PARA ESTUDIANTES QUE HAN REPROBADO MATERIAS A FINES A LA CARRERA")
        add_parrafo_inicial(pdf,"1. Reforzar el área de la expresión gramática mediante la utilización de la interdisciplinariedad, Ej. En las exposiciones, teniendo en cuenta que la habilidad de la expresión oral y escrita es esencial, redacción de documentos, actividades prácticas relacionadas a la especialidad u otras como proyectos, con intencionalidad social, Ej. Un pesquizaje de pacientes con necesidad de realizarse rehabilitación física en un determinado sector; es una buena oportunidad para desarrollar estar habilidades que constituirán la base para su futuro profesional. \n"
                                     "2. Potenciar la Zona de Desarrollo Próximo en el área de las matemáticas ya que se evidencia un buen desarrollo cognitivo pudiendo utilizar situaciones problémicas relacionadas al área de la Rehabilitación Ej. La importancia de la rehabilitación temprana y oportuna en los menores que sufren parálisis cerebral infantil producto de un parto distócico, etc. \n"
                                     "3. Reforzar los conceptos básicos de la informatización mediante actividades prácticas y proyectos relacionados al campo de la salud de manera que constaten la importancia de la misma y se interesen por profundizar en el conocimiento que les permite tener un futuro profesional más amplio y seguro. \n"
                                     "4. Plantear situaciones problemáticas o casos prácticos relacionadas con su contexto o procesos vivenciales cotidianos y vincularlo a actividades dentro del proceso docente educativo con énfasis a la salud pública. \n" )

        add_parrafo_inicial(pdf,"5. Determinar cuál es el estilo de aprendizaje de la mayoría del grupo (visual, auditivo o kinestésico o mixto) para que se elaboren estrategias de aprendizaje acorde al mismo y lograr mayor motivación, participación, concentración y eleve los resultados de los aprendizajes potenciando el método demostrativo Ej. En una clase de Técnicas de Evaluación Funcional, además de explicar la teoría, mostrar en láminas o diapositivas se sugiere utilizar estudiantes para mostrar la técnica correcta en dependencia de la patología y la edad del paciente Ej. Fracturas de Fémur, Tibia, Peroné etc. \n"
                                     "6. Observar el desempeño académico y comportamental para determinar si la cantidad de estudiantes desaprobados en Expresión Oral y Escrita está dada por desinterés cognitivo relacionado a estas materias o es parte de la responsabilidad y cumplimiento de las tareas asignadas. \n "
                                     "7. Siempre que se le indiquen tareas o actividades que constituyan un aspecto fundamental tanto en su formación personal o profesional, explicar la importancia y trascendencia y lo que puede implicar tanto en los aspectos positivos como negativos su cumplimiento o no. \n "
                                     "8. Reforzar el área motivacional mediante actividades creativas, investigativas y colaboradoras.")

        add_parrafo_negrita(pdf,"ACOMPAÑAMIENTO/ RECOMENDACIONES EXPRESIÓN ORAL Y ESCRITA")
        add_parrafo_inicial(pdf, "1. Planificar actividades donde siempre tengan un momento para destacar una regla ortográfica, o una curiosidad ortográfica u otra relacionada a la expresión oral y escrita.\n"
                                     "2. Realizar concursos Ej. el mejor mensaje de WhatsApp con el tema: Ej. 'La rehabilitación es esencial para los niños con parálisis cerebral infantil'. \n"
                                     "3. Utilización de Tic, siempre que sea posible en cada actividad. \n "
                                     "4. Modelar situaciones cotidianas donde una o una enfermera/o tenga que expresarse correctamente, escribir y utilizar las Tic. Ej. Diálogos entre una el Rehabilitador/ra y el paciente.")

        add_parrafo_negrita(pdf, "ACOMPAÑAMIENTO / RECOMENDACIONES INFORMÁTICA")
        add_parrafo_inicial(pdf,"1. Innovación educativa. \n -.Piense primero en los dispositivos móviles.\n -.Prioriza la conexión sobre el contenido. \n -.Utilización de guías que orienten los temas y el orden de cada uno de los nuevos contenidos. \n "
                                     "2. Gamificación. Existen muchas webs que ofrecen test y juegos educativos personalizables a las necesidades de cada aula o los objetivos del docente. La Realidad Virtual o los concursos colaborativos son también una opción divertida para repasar lo aprendido.\n "
                                     "3. Proyectos: Por ejemplo, presentando un trabajo que incluya diapositivas para proyectar y un vídeo. Así, serán ellos quienes manipulen las tecnologías con libertad de manera autónoma.\n "
                                     "4. Formación complementaria. Existen exposiciones, eventos, museos y charlas sobre nuevas tecnologías, redes sociales, robótica o informática que resultan interesantes a tus alumnos. \n"
                                     "5. Creación de una comunidad virtual. La mejor forma de evaluar las competencias tecnológicas de los estudiantes es que practiquen y creen su propio contenido, ya sea a través de una web o blog conjunto en el que escribir artículos sobre lo estudiado o abriendo un perfil en redes para compartir el día a día del aula.")

        add_parrafo_negrita(pdf, "ACOMPAÑAMIENTO/RECOMENDACIONES GENERALES PARA EL DOCENTE")
        add_parrafo_inicial(pdf, "1. Observar sistemáticamente el desempeño académico y comportamental.\n 2. Utilizar actividades que permitan la experimentación. \n "
                                      "3. Las instrucciones deben estar segmentadas, ser cortas y claras, en caso de estudiante con Necesidad Educativa asociada o no a discapacidad. \n 4. Respetar el ritmo y estilo de aprendizaje individual. \n"
                                      "5. Buscar actividades y entornos en los que los estudiantes interactúen socialmente, en caso de estudiante con Necesidad Educativa asociada o no a discapacidad. \n "
                                      "6. Asignar trabajos adicionales en aquellas materias en que un estudiante presente más dificultades por Ej. en caso de estudiante con Necesidad Educativa asociada o no a discapacidad. \n "
                                      "7. Tutorías entre pares en la lectura de textos, trabajos en grupo y tareas en clases. \n 8. Realizar modelado de las actividades en vez de largas explicaciones. \n"
                                      "9. Ofrecerle retos que estimulen su aprendizaje. \n 10. Reforzar las iniciativas de los estudiantes cuando quieran emprender una tarea, dándole ideas de lo que puede hacer. \n "
                                      "11. Valorar continuamente el esfuerzo y los logros alcanzados, con evaluaciones u observaciones permanentes.\n "
                                      "12. Asignar responsabilidades dentro y fuera del aula, teniendo en cuenta el diagnóstico en caso de estudiante con Necesidad Educativa asociada o no a discapacidad. \n"
                                      "13. Sentar cerca del docente para proporcionarle apoyo oportuno, en caso de estudiante con Necesidad Educativa asociada o no a discapacidad.\n "
                                      "14. Brindarle apoyo cuando lo requiera de manera individual, en caso de estudiante con Necesidad Educativa asociada o no a discapacidad. \n "
                                      "15. Fomentar el respeto y las buenas relaciones entre los compañeros a través de actividades grupales en las que se privilegie el trabajo cooperativo.\n "
                                      "16. Fomentar una cultura de valores en el grupo. \n 17. Sensibilizar a los compañeros en el respeto a la diversidad. \n "
                                      "18. Manejar un criterio diferenciado de evaluación a través de pruebas en función de las fortalezas del estudiante, ejemplo pruebas de selección múltiple, orales, entre otras. \n "
                                      "19. Apoyarse en el informe con las recomendaciones o adaptaciones curriculares en caso estudiantes con Necesidades Educativas o signos de alarmas.")

        nombre_grupo = str(grupo.nombre).replace("/","-")
        fecha_actual = datetime.now().strftime('%Y%m%d') #_%H%M
        pdfname = 'informe_'+nombre_grupo+'_'+fecha_actual+'.pdf'
        carpeta = MEDIA_ROOT + '/informes_testingreso/'
        print(carpeta)

        try:
            os.makedirs(carpeta, exist_ok=True)
        except Exception as e:
            print(f"Error al crear carpeta:"+ str(e))
        guardar= os.path.join(carpeta,pdfname)

        try:
            pdf.output(guardar)
        except Exception as e:
            print(str(e))
        return pdfname

    except Exception as e:
        print("Error al generar el PDF: {}".format(str(e)))
        return None


@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action == 'verficha':
                try:
                    persona = Persona.objects.filter(pk= request.POST['idper'])[:1].get()
                    return HttpResponse(json.dumps({"result": "ok"}), content_type="application/json")
                except Exception as ex:
                    print(ex)
                    return HttpResponse(json.dumps({"result": "bad", "mensaje": str(ex)}),content_type="application/json")

            elif  action == 'generarinforme':
                try:
                    import requests as req
                    grupo = Grupo.objects.get(pk=int(request.POST['id']))
                    pdfname = documentacioninforme(grupo)

                    return HttpResponse(json.dumps({'result': 'ok', 'reportfile': "/".join([MEDIA_URL, 'informes_testingreso', pdfname])}),content_type="application/json")

                except Exception as e:
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}),
                                        content_type="application/json")
        else:
            data = {'title': 'Encuestas Realizadas'}
            addUserData(request, data)
            if 'action' in request.GET:
                action = request.GET['action']
                if action == 'detalleingreso':
                    data = {}
                    resultadodep=[]
                    resultadomot=[]
                    resultadodes=[]
                    inscripcion = Inscripcion.objects.filter(persona_id = request.GET['pid'])[:1].get()
                    data['inscripcion']=inscripcion
                    encuesta = EncuestaItb.objects.filter(persona_id=int(request.GET['pid']))[:1].get()
                    data['detalle'] = encuesta
                    if encuesta.deporte:
                        deporte = Deporte.objects.filter(pk__in = encuesta.deporte.split(','))
                        for d in deporte:
                            resultadodep.append(str(d.nombre))
                        deportes = ",".join(resultadodep)
                        data['deportes']=deportes
                    if encuesta.motivo:
                        motivo = MotivoSeleccion.objects.filter(pk__in = encuesta.motivo.split(','))
                        for m in motivo:
                            resultadomot.append(str(m.nombre))
                        motivos = ",".join(resultadomot)
                        data['motivos']=motivos
                    if encuesta.deseo:
                        deseo = DeseosFuturos.objects.filter(pk__in = encuesta.deseo.split(','))
                        for d in deseo:
                            resultadodes.append(str(d.nombre))
                        deseos = ",".join(resultadodes)
                        data['deseos']=deseos

                    return render(request, "testingresoitb/detalletestingreso.html", data)

                # TEST MATEMATICA - LENGUAJE - INFORMATICA
                elif action == 'detalle_testsingreso':
                    try:
                        data = {}
                        listado=[]
                        encuesta = EncuestaItb.objects.filter(pk= request.GET['encuestaid'])[:1].get()
                        if encuesta.tiene_testingreso():
                            lista = encuesta.tiene_testingreso()
                            for l in lista:
                                listapreguntas = PreguntaTestIngreso.objects.filter(testingreso=l.test).order_by('orden')
                                cantidad_respuestas= RespuestaInscripcionTest.objects.filter(inscripciontest=l, validada=True).count()
                                listarespuesta= RespuestaInscripcionTest.objects.filter(inscripciontest=l, validada=True).order_by('orden')
                                conclusiones = ConclusionesTest.objects.filter(test=l.test).order_by('id')

                                test_data = {'idtest':l.test.id,
                                             'test_nombre': l.test.titulo,
                                             'puntaje': l.puntaje,
                                             'testestudiante': l.id,
                                             'listapreguntas': list(listapreguntas),
                                             'cantidadrespuestaenviada': cantidad_respuestas,
                                             'listarespuesta': list(listarespuesta),
                                             'listatablaconclu': list(conclusiones)
                                             }

                                listado.append(test_data)
                            data['tests']= listado

                            return render(request, "testingresoitb/detalle_test.html", data)
                    except Exception as e:
                        print(e)

            else:
                search = None
                periodo = Periodo.objects.get(pk=request.session['periodo'].id)
                hoy = datetime.now().date()
                encuesta = EncuestaItb.objects.filter(estadorealizado=True)

                grupos = encuesta.values_list('grupo__id', flat=True)
                data['grupos']= list(grupos)

                if 's' in request.GET:
                    search = request.GET['s']
                if search:
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')
                    if len(ss) == 1:
                        encuestas = encuesta.filter(Q(persona__nombres__icontains=search) | Q(persona__apellido1__icontains=search) | Q(persona__apellido2__icontains=search))
                    else:
                        encuestas = encuesta.filter(Q(persona__apellido1__icontains=ss[0]) & Q(persona__apellido2__icontains=ss[1]) )
                else:
                    encuestas = encuesta.filter()
                paging = MiPaginador(encuestas, 60)
                p = 1
                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                    page = paging.page(p)
                except:
                    p = 1
                    page = paging.page(p)
                data['contador']= encuesta.count()
                data['paging'] = paging
                data['rangospaging'] = paging.rangos_paginado(p)
                data['page'] = page
                data['encuesta'] = page.object_list
                usuario = User.objects.get(pk=request.user.id)
                data['usuario']=  usuario
                data['search'] = search if search else ""
                return render(request,"testingresoitb/vertestingresoitb.html", data)

    except Exception as e:
        print(e)
        return HttpResponseRedirect("/?info=Error comunicarse con el administrador ")
