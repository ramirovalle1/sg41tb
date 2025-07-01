from django.urls import include, re_path as url, path, re_path
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static
import django.views.static
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from django.views.decorators.cache import never_cache

import settings
from bib import documentos, prestamos, busqueda
from clinicaestetica import historclinico
from med import alu_medical, box_medical, per_medical
from reportesexcel import reporteexcel, listadofacturas, listadoncreditos, eval_alumdoce_resumen, cronograma, \
    exc_egresados, vinculacion_practicas, proceso_titulacion, xls_seguimiento_graduados, eficiencia, resumen_egresados, \
    materias_por_grupo, estado_cta_por_nivel, gestion_carrera, seguimiento_grupo, valores_inscritos_por_usuario, \
    matriculados_sms, estudiantes_xcarreraysexo, inscritos_general, alumnosporgrupo, conduccion_estudiantes_xperiodo, \
    cobroscontarjetas, informacion_estudiantes, sms_porcarrera, xls_inscritos_porrangofecha, clasesimpartidas, \
    pedagogia, vencimiento_xvencer_estudiantes, vencidos_xvencer_xrubros, matriculados_cne, especies_valoradas, \
    materiasnivelabierto_xgrupo, estudiantes_xgrupo, gestion_moraxnivel, gestion_moraxcarrera, retirados_porrangofecha, \
    listado_sinvinculacion_sinpracticas, distributivo_aulas, matriculados_extranjeros, xls_matriculados_xrangofechas, \
    cobrosonline, resumen_cartera, pagos_gestion, datos_estudiantes, xgrupo_practicas_vinculacion, \
    absentos_porrangofecha, ingresos_caja_fecha, cobros_rango_fecha, cobros_rango_fecha_jornada, \
    rubros_xvencer_matriculados, asistenciasxnivel, xlsmatriculadosxprovincias, becados_xperiodo, \
    indicadores_fichasocioecon, promocion_estudiantes, nivelsocioecon_xperiodo, pagopymentez, estudiantemallasinpago, \
    mallacompletaconsulta, excelprovcanparsec, seguimientograduado_rangofecha, deuda_estudiantes, bandeja_atencion, \
    listadoalumnosmatriculadogrupo, movimientos_reasignacion, actividad_vinculacion_porrangofecha, alumnos_xetnia, \
    est_carga_masiva_estudiantes, cpe_carga_masiva_carreras_estudiante, resumen_sesionescajas, \
    mat_carga_masiva_matriculas, estgeneral_carga_masiva_estudiantes, lib_carga_masiva, informacion_alumnos, \
    cantidad_alumnos_matriculadosxcarreras, segregado_tramites_solicitudes, pagos_tiporubrosestudiante, \
    inscritosporanio, matriculadospagoinscripcion, asistenciasxperiodoycarrera, estudiantesxconvenios, \
    ingresos_formadepago, base_matriculados, xls_descuentosaplicados, gruposetarios, alumnos_socioeconomica, \
    matriz_graduados, caces_estudiantes_rangofecha, caces_estudiantes_periodo, caces_becados, \
    caces_estudiantes_practicas, caces_proyecto_participantes, graduados_sinpracticas, estudiantesfamiliar, \
    xls_terminos_constancia_inscritos, horaspracticasporrol, calificacionesyasistenciasxperiodocarreranivel, \
    valoresvencidos_xperiodo_xcoordinacion, horaspracticasporrangodefechas, descuentos_promociones, \
    xls_graduadosxanioycarrera, xls_informacion_alumnosxgrupo, xls_graduados_condiscapacidad, \
    xls_estudiantes_condiscapacidad, graduados_general, mesadeayuda_porrangofechas, tiemporespuesta_bandejadocente, \
    xls_pagos_nivel_descuento, xls_absentosyretirados_porfacultad, xls_deudasinscripciones_xcoordinacion, \
    xls_asistencias_xcoordinacion, xls_personalitb, xls_registrovacunas, xls_inscripciones_gads, materias_culminadas, \
    xls_vacunasregistroxfacultades, bandejacajeros_xrangofechas, inscritos_xcanton, xls_estudiantes_informaciondobe, \
    xls_inscritos_xprovincia, compromisopagos_xfechas, inscritos_cursosingles, xls_docentesactivos, \
    datapichincha_matriculados, xls_especiesvaloradasxdepartamento, formasdepago_ingresos, xls_cierreclases_porfacultad, \
    xls_clasescerradasdocentes_porfacultad, xls_documentos_bib, cant_inscritos_xcarrera, calificaciones_xnivel, \
    xls_referidos_cobro, xls_infosocioeconomica, tiempo_tramites_bandeja, xls_visitabibliotecaxcarrera, \
    listadoprogramasvinculacion, listadoproyectosvinculacion, listadoaccesobiblioteca, listadodocentes, \
    totalestudiantesxanio, xls_convenios, xls_listadocentesporingreso, xls_entrega_uniformes_admision, \
    xls_pago_sustentaciones_docente, xls_sesiones_caja, xls_promocionuniformes, xls_informacionitb, \
    xls_resumen_visitasbiblioteca, xls_matriculados_xperiodo
from sga import (preguntatestingreso, respuestatestingreso, inscribiralumnos, inscripciontest, columnatestarrastar, \
    encuestaitb, commonviews, reportes, reporteria, solicitudes, retirados, mallas, niveles, horarios, becas_matricula, \
    docentes, administrativos, inscripciones, pre_inscripciones, matriculas, pro_clases, pro_horarios, pro_asistencias, \
    pro_evaluaciones, pro_documentos, pro_autoevaluacion, pro_aluevaluacion, pro_coordevaluacion, pro_alureprobados, \
    pro_titulacion, pro_cronograma, cons_documentos, alu_horarios, alu_materias, alu_notas, alu_solicitudes, \
    alu_documentos, graduados, egresados, alu_finanzas, alu_malla, alu_cronograma, asignaturas, cons_mallas, \
    cons_alumnos, consultas, adm_docentes, noticias, incidencias, dobe, becados, fecha_evaluaciones, distributivo, \
    recepcion_actas, caja, finanzas, facturas, notacredito, recibocaja, vale_caja, recibo_caja, cheques, \
    adm_evaluaciondocentes, adm_grupos, api, estadisticas, rol_pago, prestamo_inst, pro_multas, adm_calendario, \
    calendario, visitabiblioteca, sesiones_caja, qr, dbf, materias_externas, encuestas, cronograma_pagos, \
    estudiantesxdesertar, printdoc, becarios, plan12, justificacion, elimado_matricula, practicasconduc, alumnopractica, \
    practicasadmin, visitabox, test_propedeutico, carrera_admi, inscripcionescurso, gruposcurso, admin_vehiculos, \
    consultafactura, alu_facturacion_electronica, facturacion_electronica, registromedicamento, suministrobox, \
    tipomedicamento, admin_tutoria, profe_tutoria, admin_detalle_tutoria, tutoria, visitabtiket, tiketsturnos, \
    tipooficio, oficios, practicaclase, congreso, descuentos, turno, vistaturno, atencioncliente, newstiket, \
    turnotikets, guarderia, registroguarderia, documentos_alu, estadisticaguarderia, recaudacion, tipovisbox, nee, \
    discapacidad, consultaalumno, seguimiento, registros, resoluciones, seminario, alu_seminario, beca_solicitud, \
    vinculacion, consultagraduados_condu, consultaevaluaciones, absentismo, convenios, programas, cons_niveles, \
    cons_matriculas, periodo, asistente_estudiantiles, incidencia_x_administrativa, consultamovil, alu_panel, panel, \
    seguimiento_inscrip, syllabus, absentismo_finaliza, mantenimiento, alu_referidos, referidos, cita, \
    admin_examencondu, examen_conduc, aula_administracion, inscripcionesaspirantes, consultadocente, enviocorreo, \
    colegio, conveniobox, tipoconvenio, preciobox, pagowester, archivowester, convenio_academico, controlespecies, \
    examen_convalidac, incidencia_doc, requerimiento_x_depart, solicitudonline, archivos_generales, facturacioncronoff, \
    pro_publicaciones, ponencia, mensajetexto, documentos_vinculacion, adminexamenexterno, admintest, examenexterno, \
    listapersonaext, mtto_sectores, externos, tipoprogramas, pagospedagogia, datoscongreso, pago_online, pypagos, \
    nuevoreportecarrera, prueba_psicologica, alcance_notas, aprobacion_alcance_notas, pacifico, especies_admin, \
    entrega_uniforme_municipio, cuentabancaria, preguntaasignatura, profe_examenparcial, inscrip_examenparcial, \
    adminprofeexamen, conduceonline, pagosconduceonline, perfil_profesormateria, jornada, vendedor, \
    admin_grupo_municipio, promociones, alu_matricula, pro_entrega_acta, admin_ayudafinanciera, matriculaseliminadas, \
    empresaconvenio, bancos, alcance_nivelcerrado, aprobacion_nivelcerrado, requeri_soporte, soportetics, pro_especies, \
    archivopichincha, tutorcongreso, tutor_matricula, verrequerimiento, tutor_grupo, multa_docente_materia, \
    bandeja_asistente, webinar, revisionsolicitudpagos, liberarmatricula, eliminados_alcancenotas, escenariopractica, \
    solicitudpracticas, solicitudpracticaadm, supervisarevalest, paramevalpract, entregauniformes, chat, \
    chatsoporte_admin, parametrodescuento, permisosga, tallauniforme, coloruniforme, aulaman, tallazapato, colorzapato, \
    empresasinconvenio, horarioasisitentesolicitudes, clientefactura, inscripcionpostulacion, \
    pago_sustentaciones_docente, sedemantenimiento, encuestatut, ambitoencuestatutor, encuestatutor, \
    encuestainscripcion, encuestaestudiante, alum_tutorias, pagopracticas_docente, cab, \
    actividades_vinculacion_docentes, profesionalizacion, infocont, actividadesextra, evaluaciondocenteman, \
    evaluacionesdocente, alu_evaluaciondocente, doc_evaluaciondocente, doc_evaluaciondirectivo, localizacion_gps, \
    resultadosevaluacion, tipoestadosolicitud, archivosolicitudbeca, tipogestionbeca, solicitudatencion, solicitudadmin, \
    bibliotecavirtual, notificaciones, notificaciones_mant, busqueda_usuario, testingreso, evaluaciondecano, \
    man_referenciasweb, man_otrasbibliotecas, solicitud_materiaonline, encuestadesercion, solicitudpostulacionbeca, \
    solicitudpostulacionbecaadmin, estadisticasadmin, api_rest, vertestingresoitb, tutoria_pedagogica, \
    cons_encuestaingreso, conveniocarrera, solicitudpostulacionbecadjudicada, pro_aulavirtual, \
    adm_cronogramaacademico, distributivodocente, pro_calificaciones, aprobarsilabo,
    cons_encuestaingreso, conveniocarrera, solicitudpostulacionbecadjudicada, admin_teleclinica, teleclinica, \
    solicitudpostulacionbecasoftware)
from sga.templatetags import sga_extras
from socioecon import alu_socioecon, cons_socioecon

admin.autodiscover()
# handler404 = commonviews.page_404
# handler500 = login_user

urlpatterns = static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += staticfiles_urlpatterns()

if not settings.DEBUG:
    urlpatterns = [
        url(r'^static/(?P<path>.*)$', django.views.static.serve,
            {'document_root': settings.STATIC_ROOT}),
        url(r'^media/(?P<path>.*)$', django.views.static.serve,
            {'document_root': settings.MEDIA_ROOT}),
    ]
from importlib import import_module
def lazy_view_import(view_name):
    def view(request, *args, **kwargs):
        module_name, func_name = view_name.rsplit('.', 1)
        module = import_module(module_name)
        view_func = getattr(module, func_name)
        return view_func(request, *args, **kwargs)
    return view

urlpatterns += {
    # Examples:
    # url(r'^$', 'iavq.views.home', name='home'),
    # url(r'^iavq/', include('iavq.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', admin.site.urls),

    # url(r'^login$', lazy_view_import('sga.commonviews.login_user')),
    url(r'^login$', lazy_view_import('sga.commonviews.login_user_new')),
    url(r'^loginparent$', lazy_view_import('sga.commonviews.login_parent')),
    url(r'^reestablecer_pass$', lazy_view_import('sga.commonviews.reestablecer_pass')),
    # url(r'^template$', commonviews.template),
    # url(r'^login$', commonviews.login_user),
    url(r'^login$', commonviews.login_user_new),
    url(r'^loginparent$', commonviews.login_parent),
    url(r'^reestablecer_pass$', commonviews.reestablecer_pass),


    url(r'^logout$', commonviews.logout_user),
    url(r'^account$', commonviews.account),
    url(r'^pass$', commonviews.passwd),
    url(r'^$', commonviews.panel),

    # REPORTES
    url(r'^reportes$', reportes.view),
    url(r'^reporteria$', reporteria.view),

    # SOLICITUDES A SECRETARIA
    url(r'^solicitudes$', solicitudes.view),
    # ALUMNOS RETIRADOS
    url(r'^retirados$', retirados.view),

    # CONSULTA DE MATRICULA DE ALUMNOS
    # url(r'^cons_matriculas$', cons_matriculas.view),
    # MALLAS
    url(r'^mallas$', mallas.view),
    # NIVELES
    url(r'^niveles$', niveles.view),
    # HORARIOS
    url(r'^horarios$', horarios.view),

    # BECAS MATRICULAS
    url(r'^becas_matricula', becas_matricula.view),
    # DOCENTES
    url(r'^docentes$', docentes.view),
    # ADMINISTRATIVOS
    url(r'^administrativos', administrativos.view),
    # INSCRIPCIONES
    url(r'^inscripciones$', inscripciones.view),

    #PRE INSCRIPCIONES
    url(r'^pre_inscripciones$', pre_inscripciones.view),

    # MATRICULAS
    url(r'^matriculas$', matriculas.view),
    # PROFESORES CLASES
    url(r'^pro_clases$', pro_clases.view),
    # PROFESORES HORARIOS
    url(r'^pro_horarios$', pro_horarios.view),
    # PROFESORES ASISTENCIAS
    url(r'^pro_asistencias$', pro_asistencias.view),
    # PROFESORES EVALUACIONES
    url(r'^pro_evaluaciones$', pro_evaluaciones.view),
    # PROFESORES ARCHIVOS Y DOCUMENTOS
    url(r'^pro_documentos$', pro_documentos.view),
    # PROFESORES AUTOEVALUACION
    url(r'^pro_autoevaluacion$', pro_autoevaluacion.view),
    #PROFESORES EVALUACION POR SUS ALUMNOS
    url(r'^pro_aluevaluacion$', pro_aluevaluacion.view),

    #PROFESORES EVALUACION POR SUS COORDINADORES DE CARRERA
    url(r'^pro_coordevaluacion$', pro_coordevaluacion.view),
    #PROFESORES CONTROL DE ALUMNOS A SUPLETORIO O REPROBADOS
    url(r'^pro_alureprobados$', pro_alureprobados.view),
    #PROFESORES CERTIFICADOS Y TITULOS
    url(r'^pro_titulacion$', pro_titulacion.view),
    #PROFESORES CRONOGRAMAS DE CLASES
    url(r'^pro_cronograma$', pro_cronograma.view),
    #PROFESORES AULA VIRTUAL DE CLASES
    url(r'^pro_aulavirtual$', pro_aulavirtual.view),

    # PROFESORES CONSULTA DE SYLLABUS
    url(r'^cons_documentos$', cons_documentos.view),

    # ALUMNOS HORARIOS
    url(r'^alu_horarios$', alu_horarios.view),
    # ALUMNOS MATERIAS
    url(r'^alu_materias$', alu_materias.view),
    # ALUMNOS RECORD
    url(r'^alu_notas$', alu_notas.view),
    # ALUMNOS SOLICITUDES
    url(r'^alu_solicitudes$', alu_solicitudes.view),
    # ALUMNOS SOLICITUDES
    url(r'^alu_documentos$', alu_documentos.view),
    # ALUMNOS GRADUADOS
    url(r'^graduados$', graduados.view),
    # ALUMNOS EGRESADOS
    url(r'^egresados$', egresados.view),
    # ALUMNOS FINANZAS
    url(r'^alu_finanzas', alu_finanzas.view),
    # ALUMNOS MALLA
    url(r'^alu_malla', alu_malla.view),
    # ALUMNOS FICHA MEDICA
    url(r'^alu_medical', alu_medical.view),
    # ALUMNOS CRONOGRAMA DE MATERIAS
    url(r'^alu_cronograma', alu_cronograma.view),
    # DOCTOR DPTO MEDICO
    url(r'^box_medical', box_medical.view),
    # PERSONAL FICHA MEDICA
    url(r'^per_medical', per_medical.view),
    # ALUMNOS FICHA SOCIOECONOMICA
    url(r'^alu_socioecon', alu_socioecon.view),

    # CONFIGURACION DE ASIGNATURAS
    url(r'^asignaturas$', asignaturas.view),

    # CONSULTAS DE MALLAS
    url(r'^cons_mallas$', cons_mallas.view),

    # CONSULTAS DE ALUMNOS
    url(r'^cons_alumnos$', cons_alumnos.view),

    # CONSULTAS DE NIVELES SOCIOECONOMICOS
    url(r'^cons_socioecon$', cons_socioecon.view),

    # CONSULTAS DE HORARIOS POR PROFESORES
    url(r'^cons_horarios$', consultas.view),

    # ADMINISTRAR CLASES Y EVALUACIONES DE DOCENTES POR EL JEFE ACADEMICO
    url(r'^adm_docentes$', adm_docentes.view),

    # NOTICIAS
    url(r'^noticias$', noticias.view),

    # INCIDENCIAS
    url(r'^incidencias$', incidencias.view),

    #PERFILES DE INSCRIPCION
    url(r'^dobe$', dobe.view),

    #ESTUDIANTES CON BECA
    url(r'^becados$', becados.view),

    # PERIODO DE CALIFICACIONES
    url(r'^fecha_evaluaciones$', fecha_evaluaciones.view),

    # DISTRIBUTIVO DE AULAS
    url(r'^distributivo$', distributivo.view),

    # RECEPCION DE ACTAS DE NOTAS - MATERIAS CERRADAS
    url(r'^recepcion_actas$', recepcion_actas.view),

    # FINANZAS
    url(r'^caja$', caja.view),
    url(r'^finanzas$', finanzas.view),
    url(r'^facturas$', facturas.view),
    url(r'^notacredito', notacredito.view),
    url(r'^recibocaja', recibocaja.view),
    url(r'^vale_caja$', vale_caja.view),
    url(r'^recibo_caja$', recibo_caja.view),
    url(r'^cheques$', cheques.view),

    # MALLA DE ALUMNO
    url(r'^alu_malla$', alu_malla.view),

    # GESTION DE EVALUACION DE DOCENTES
    url(r'^adm_evaluaciondocentes$', adm_evaluaciondocentes.view),

    # GESTION DE GRUPOS
    url(r'^adm_grupos$', adm_grupos.view),

    # API FOR THIRD PARTY APPS
    url(r'^api$', api.view),

    # ESTADISTICAS Y GRAFICOS
    url(r'^estadisticas$', estadisticas.view),

    # ROLES DE PAGOS A DOCENTES
    url(r'^rol_pago$', rol_pago.view),

    # PRESTAMOS INSTITUCIONALES
    url(r'^prestamo_inst$', prestamo_inst.view),

    # PRESTAMOS INSTITUCIONALES
    url(r'^pro_multas$', pro_multas.view),

    # ADMINISTRADOR DE CALENDARIO DE ACTIVIDADES
    url(r'^adm_calendario$', adm_calendario.view),
    # CALENDARIO DE ACTIVIDADES
    url(r'^calendario$', calendario.view),
    url(r'^visitabiblioteca', visitabiblioteca.view),
    url(r'^sesionescaja$', sesiones_caja.view),


    # INTEGRACION QR
    url(r'^aula$', qr.aulas),
    url(r'^aula/(?P<id>\d+)$', qr.aula),

    # EXPORTAR DBF CONTABILIDAD
    url(r'^dbf$', dbf.view),

    # PARA ENTRAR COMO OTRO USUARIO
    url(r'^cu$', commonviews.changeuser),


    # BIBLIOTECA
    url(r'^documentos$', documentos.view),
    url(r'^prestamos$', prestamos.view),
    url(r'^bibliosearch$', busqueda.view),
    url(r'^otrasbiblio$', busqueda.otras),
    url(r'^gourl$', busqueda.gourl),
    url(r'^book/(?P<id>\d+)$', busqueda.book),

    # MATERIAS EXTERNAS
    url(r'^materias_externas$', materias_externas.view),

    url(r'^encuestas$', encuestas.view),

    # CRONOGRAMA DE PAGOS
    url(r'^cronogramapagos$', cronograma_pagos.view),

    # POSIBLES DESERTORES
    url(r'^estudiantesxdesertar$', estudiantesxdesertar.view),


    # IMPRESION NEW STYLE
    url(r'^print/(?P<referencia>.+)/(?P<id>\d+)$', printdoc.view),

    # ESTUDIANTES CON BECA ASIGNADA (BECARIOS)
    url(r'^becarios$', becarios.view),


    # PLAN 12 MATERIAS
    url(r'^plan12$', plan12.view),

    # JUSTIFICACION DE AUSENCIAS
    url(r'^justificacion$', justificacion.view),

    # MATRICULAS ELIMINADAS
    url(r'^eliminado_matricula$', elimado_matricula.view),

    # PRACTICAS ALUMNOS CONDUCCION
    url(r'^practicasconduc$', practicasconduc.view),
    url(r'^alumnopractica$', alumnopractica.view),
    url(r'^practicasadmin$', practicasadmin.view),           # administrar tablas de practicas conduccion
    #VISITABOX
    url(r'^visitabox$', visitabox.view),

    #TEST_PROPEDEUTICO
    url(r'^test_propedeutico$', test_propedeutico.view),
    url(r'^test_dobe$', test_propedeutico.test_dobe),
    # CARRERA
    url(r'^carrera_admi$', carrera_admi.view),
    url(r'^inscripcionescurso', inscripcionescurso.view),
    url(r'^gruposcurso', gruposcurso.view),
    url(r'^admin_vehiculos', admin_vehiculos.view),
    url(r'^facturaelect', commonviews.facturaelect),
    url(r'^consultafactura', consultafactura.view),
    url(r'^alu_facturacion_electronica', alu_facturacion_electronica.view),
    url(r'^facturacion_electronica', facturacion_electronica.view),
    url(r'^registromedicamento', registromedicamento.view),
    url(r'^suministrobox', suministrobox.view),
    url(r'^tipomedicamento', tipomedicamento.view),
    # url(r'^facturacioncron', facturacioncron.view),
    url(r'^admin_tutoria', admin_tutoria.view),
    url(r'^profe_tutoria', profe_tutoria.view),
    url(r'^admin_detalle_tutoria', admin_detalle_tutoria.view),
    url(r'^tutoria', tutoria.view),
    url(r'^visitabtiket', visitabtiket.view),
    url(r'^tiketsturno', tiketsturnos.view),
    url(r'^tipooficio', tipooficio.view),
    url(r'^oficio', oficios.view),
    url(r'^practicaclase', practicaclase.view),
    url(r'^congreso', congreso.view),
    url(r'^descuento', descuentos.view),
    url(r'^turno', turno.view),
    url(r'^vistaturno', vistaturno.view),
    url(r'^atencionclientes', atencioncliente.view),
    url(r'^newstiket', newstiket.view),
    url(r'^tiketsadmin', turnotikets.view),
    url(r'^guarderia', guarderia.view),
    url(r'^registroguarderia', registroguarderia.view),
    url(r'^documentos_alu', documentos_alu.view),
    url(r'^estadisticaguarderia', estadisticaguarderia.view),
    url(r'^recaudacion', recaudacion.view),
    url(r'^tipovisbox', tipovisbox.view),
    url(r'^nee', nee.view),
    url(r'^accioncalendar', sga_extras.accioncalendar),
    url(r'^discapacidad', discapacidad.view),
    url(r'^consultaalumno', consultaalumno.view),
    url(r'^seguimiento', seguimiento.view),
    url(r'^registros$', registros.view),
    url(r'^resoluciones', resoluciones.view),
    url(r'^seminario', seminario.view),
    url(r'^alu_seminario', alu_seminario.view),
    url(r'^beca_solicitud', beca_solicitud.view),
    url(r'^vinculacion', vinculacion.view),
    url(r'^consultagraduados_condu', consultagraduados_condu.view),
    url(r'^consultaevaluacion', consultaevaluaciones.view),
    url(r'^absentismo', absentismo.view),
    url(r'^convenios', convenios.view),
    url(r'^programas', programas.view),
    url(r'^cons_niveles', cons_niveles.view),
    url(r'^cons_matriculas', cons_matriculas.view),
    url(r'^periodo', periodo.view),
    url(r'^asistente_estudiantiles', asistente_estudiantiles.view),
    url(r'^incidenciaadministrativa', incidencia_x_administrativa.view),
    # consulta movil
    url(r'^consmovil$', consultamovil.view),
    url(r'^panel', panel.view),
    url(r'^alu_panel', alu_panel.view),
    url(r'^rees$', commonviews.reestablecer),
    url(r'^cambiar_clave', commonviews.cambiar_clave),
   #TEST_PROPEDEUTICO
   url(r'^test_propedeutico$', test_propedeutico.view),
   url(r'^test_dobe$', test_propedeutico.test_dobe),
   # CARRERA
   url(r'^carrera_admi$', carrera_admi.view),
   url(r'^inscripcionescurso', inscripcionescurso.view),
   url(r'^gruposcurso', gruposcurso.view),
   url(r'^admin_vehiculos', admin_vehiculos.view),
   url(r'^facturaelect', commonviews.facturaelect),
   url(r'^consultafactura', consultafactura.view),
   url(r'^alu_facturacion_electronica', alu_facturacion_electronica.view),
   url(r'^facturacion_electronica', facturacion_electronica.view),
   url(r'^registromedicamento$', registromedicamento.view),
   url(r'^suministrobox', suministrobox.view),
   url(r'^tipomedicamento', tipomedicamento.view),
   # url(r'^facturacioncron', facturacioncron.view),
   url(r'^admin_tutoria', admin_tutoria.view),
   url(r'^profe_tutoria', profe_tutoria.view),
   url(r'^admin_detalle_tutoria', admin_detalle_tutoria.view),
   url(r'^tutoria', tutoria.view),
   url(r'^visitabtiket', visitabtiket.view),
   url(r'^tiketsturno', tiketsturnos.view),
   url(r'^tipooficio', tipooficio.view),
   url(r'^oficio', oficios.view),
   url(r'^practicaclase', practicaclase.view),
   url(r'^congreso', congreso.view),
   url(r'^descuento', descuentos.view),
   url(r'^turno', turno.view),
   url(r'^vistaturno', vistaturno.view),
   url(r'^atencionclientes', atencioncliente.view),
   url(r'^newstiket', newstiket.view),
   url(r'^tiketsadmin', turnotikets.view),
   url(r'^guarderia', guarderia.view),
   url(r'^registroguarderia', registroguarderia.view),
   url(r'^documentos_alu', documentos_alu.view),
   url(r'^estadisticaguarderia', estadisticaguarderia.view),
   url(r'^recaudacion', recaudacion.view),
   url(r'^tipovisbox', tipovisbox.view),
   url(r'^nee', nee.view),
   url(r'^accioncalendar', sga_extras.accioncalendar),
   url(r'^discapacidad', discapacidad.view),
   url(r'^consultaalumno', consultaalumno.view),
   url(r'^seguimiento', seguimiento.view),
   url(r'^registros$', registros.view),
   url(r'^resoluciones', resoluciones.view),
   url(r'^seminario', seminario.view),
   url(r'^alu_seminario', alu_seminario.view),
   url(r'^beca_solicitud', beca_solicitud.view),
   url(r'^vinculacion', vinculacion.view),
   url(r'^consultagraduados_condu', consultagraduados_condu.view),
   url(r'^consultaevaluacion', consultaevaluaciones.view),
   url(r'^absentismo', absentismo.view),
   url(r'^convenios', convenios.view),
   url(r'^programas', programas.view),
   url(r'^cons_niveles', cons_niveles.view),
   url(r'^cons_matriculas', cons_matriculas.view),
   url(r'^periodo', periodo.view),
   url(r'^asistente_estudiantiles', asistente_estudiantiles.view),
   url(r'^incidenciaadministrativa', incidencia_x_administrativa.view),
   # consulta movil
   url(r'^consmovil$', consultamovil.view),
   url(r'^panel', panel.view),
   url(r'^alu_panel', alu_panel.view),
   url(r'^rees$', commonviews.reestablecer),
   url(r'^cambiar_clave', commonviews.cambiar_clave),
    url(r'^seguimien_inscrip', seguimiento_inscrip.view),
    url(r'^syllabus', syllabus.view),
    url(r'^finalizaabsent', absentismo_finaliza.view),
    url(r'^mantenimiento', mantenimiento.view),
    url(r'^alu_referidos', alu_referidos.view),
    url(r'^referidos', referidos.view),
    url(r'^cita', cita.view),
    url(r'^admin_examencondu', admin_examencondu.view),
    url(r'^examen_conduc', examen_conduc.view),
    url(r'^aula_administrador', aula_administracion.view),

    url(r'^inscripcionesaspirantes', inscripcionesaspirantes.view),
    url(r'^consultadocente', consultadocente.view),
    url(r'^enviocorreo', enviocorreo.view),



    url(r'^colegio', colegio.view),
    url(r'^reporteexcel', reporteexcel.view),
    url(r'^listadofacturas', listadofacturas.view),
    url(r'^listadoncreditos', listadoncreditos.view),
    url(r'^conveniobox', conveniobox.view),
    url(r'^tipoconvenio', tipoconvenio.view),
    url(r'^preciobox', preciobox.view),
    url(r'^eval_alumdoce_resumen', eval_alumdoce_resumen.view),
    url(r'^cronograma', cronograma.view),
    url(r'^pagowester', pagowester.view),
    url(r'^archivowester', archivowester.view),
    url(r'^convenio_academico', convenio_academico.view),
    url(r'^controlespecies', controlespecies.view),
    url(r'^examen_convalida', examen_convalidac.view),
    url(r'^incidenciasdoc', incidencia_doc.view),
    url(r'^requerimiento', requerimiento_x_depart.view),
    url(r'^respuestareque', requerimiento_x_depart.resps),
    url(r'^solicitudonline', solicitudonline.view),
    url(r'^archivos_generales', archivos_generales.view),
    url(r'^oflineffacturacioncron', facturacioncronoff.view),
    url(r'^exc_egresados', exc_egresados.view),
    url(r'^practicas_vinculacion', vinculacion_practicas.view),
    url(r'^proceso_titulacion', proceso_titulacion.view),
    url(r'^xls_seguimiento_graduados', xls_seguimiento_graduados.view),
    url(r'^eficiencia', eficiencia.view),
    url(r'^resumen_egresados', resumen_egresados.view),
    url(r'^materias_por_grupo', materias_por_grupo.view),
    url(r'^estado_cta_por_nivel', estado_cta_por_nivel.view),
    url(r'^gestion_carrera', gestion_carrera.view),
    url(r'^publicaciones', pro_publicaciones.view),
    url(r'^ponencia', ponencia.view),
    url(r'^grupo_seguimiento', seguimiento_grupo.view),
    url(r'^valores_inscritos', valores_inscritos_por_usuario.view),
    url(r'^matriculados_sms', matriculados_sms.view),
    url(r'^estudiantes_xcarreraysexo', estudiantes_xcarreraysexo.view),
    url(r'^inscritos_general', inscritos_general.view),
    url(r'^alumnosporgrupo', alumnosporgrupo.view),
    url(r'^conduccion_estudiantes_xperiodo', conduccion_estudiantes_xperiodo.view),
    url(r'^mensajetexto', mensajetexto.view),
    url(r'^cobroscontarjetas', cobroscontarjetas.view),
    url(r'^informacion_estudiantes', informacion_estudiantes.view),
    url(r'^sms_porcarrera', sms_porcarrera.view),

    url(r'^documentos_vinculacion', documentos_vinculacion.view),
    url(r'^adminexamenexterno', adminexamenexterno.view),
    url(r'^admintest', admintest.view),
    url(r'^examenexterno', examenexterno.view),
    url(r'^listapersonaexter', listapersonaext.view),
    url(r'^xls_inscritos_porrangofecha', xls_inscritos_porrangofecha.view),
    url(r'^mtto_sectores', mtto_sectores.view),
    url(r'^reinicia_sec', api.reinicia_secuencia),
    url(r'^clasesimpartidas', clasesimpartidas.view),
    url(r'^externos', externos.view),
    url(r'^pedagogia', pedagogia.view),
    url(r'^vencimiento_xvencer_estudiantes', vencimiento_xvencer_estudiantes.view),
    url(r'^vencidos_xvencer_xrubros', vencidos_xvencer_xrubros.view),
    url(r'^matriculados_cne', matriculados_cne.view),
    url(r'^tipoprogramas', tipoprogramas.view),
    url(r'^especiesvaloradas', especies_valoradas.view),
    url(r'^pagospedagogia', pagospedagogia.view),
    url(r'^datoscongreso', datoscongreso.view),
    # url(r'^cerrarcajapedagogia', api.cerrar_caja_congreso),
    url(r'^cerrarcajaonline', api.cerrar_caja_online),
    url(r'^callback', api.callback),
    url(r'^facturacionpedagogia', api.facturacion_pedagogia),
    url(r'^online', pago_online.view),
    url(r'^materiasnivelabierto_xgrupo', materiasnivelabierto_xgrupo.view),
    url(r'^estudiantes_xgrupo', estudiantes_xgrupo.view),
    url(r'^gestion_moraxnivel', gestion_moraxnivel.view),
    url(r'^gestion_moraxcarrera', gestion_moraxcarrera.view),
    url(r'^historiaclinica', historclinico.view),
    url(r'^pypagos', pypagos.view),
    url(r'^retirados_porrangofecha', retirados_porrangofecha.view),
    url(r'^listado_sinvinculacion_sinpracticas', listado_sinvinculacion_sinpracticas.view),
    url(r'^nuevoreportecarrera', nuevoreportecarrera.view),
    url(r'^distributivo_aulas', distributivo_aulas.view),
    url(r'^actualiza_archivo', gestion_moraxnivel.view),
    url(r'^matriculados_extranjeros', matriculados_extranjeros.view),
    url(r'^prueba_psicologica', prueba_psicologica.view),
    # url(r'^pago_online_prueba', pago_online_prueba.view),

}
urlpatterns += {
    url(r'^xls_matriculados_xrangofechas', xls_matriculados_xrangofechas.view),
    url(r'^cobrosonline', cobrosonline.view),
    url(r'^alcance_notas', alcance_notas.view),
    url(r'^aprobacion_alcance_notas', aprobacion_alcance_notas.view),
    url(r'^autenticaad', api.autenticaAD),
    url(r'^editclavead', api.editclaveAD),
    url(r'^pagosgestion', pagos_gestion.view),
    url(r'^resumencartera', resumen_cartera.view),
    url(r'^pacifico$', pacifico.view),
    url(r'^cambioclave', commonviews.cambiarclaveAD),
    url(r'^datos_estudiantes', datos_estudiantes.view),
    url(r'^xgrupo_practicas_vinculacion', xgrupo_practicas_vinculacion.view),
    url(r'^absentos_porrangofecha', absentos_porrangofecha.view),
    url(r'^especies_admin', especies_admin.view),
    url(r'^entrega_uniforme_municipio', entrega_uniforme_municipio.view),
    url(r'^ingresos_caja_fecha', ingresos_caja_fecha.view),
    url(r'^cobros_rango_fecha', cobros_rango_fecha.view),
    url(r'^jornada_cobros_rango_fecha', cobros_rango_fecha_jornada.view),
    url(r'^rubros_xvencer_matriculados', rubros_xvencer_matriculados.view),
    # url(r'^diferircuota', diferircuota.view),
    url(r'^cerrarcajareferido', api.cerrar_caja_referido),
    url(r'^asistenciasxnivel', asistenciasxnivel.view),
    url(r'^cuentabancaria', cuentabancaria.view),
    url(r'^xlsmatriculadosxprovincias', xlsmatriculadosxprovincias.view),
    url(r'^becados_xperiodo', becados_xperiodo.view),
    url(r'^preguntaasignatura', preguntaasignatura.view),
    url(r'^proexamenparcial', profe_examenparcial.view),
    url(r'^inscrexamenparcial', inscrip_examenparcial.view),
    url(r'^adminprofeexamen', adminprofeexamen.view),
    url(r'^conduceonline', conduceonline.view),
    url(r'^pagosconduceonline', pagosconduceonline.view),
    url(r'^logincondu$', commonviews.logincondu),
    url(r'^logoutpago$', commonviews.logoutpago),
    url(r'^indicadores_fichasocioecon', indicadores_fichasocioecon.view),
    url(r'^factura_online', api.factura_online),
    url(r'^promocion_estudiantes', promocion_estudiantes.view),
    url(r'^perfil_profesormateria', perfil_profesormateria.view),
    url(r'^jornada', jornada.view),
    url(r'^nivelsocioecon_xperiodo', nivelsocioecon_xperiodo.view),
    url(r'^vendedor', vendedor.view),
    url(r'^admin_grupo_municipio', admin_grupo_municipio.view),
    url(r'^promociones', promociones.view),
    url(r'^alu_matricula', alu_matricula.view),
    url(r'^pro_entrega_acta', pro_entrega_acta.view),
    url(r'^appprivacidad', consultamovil.privacidad),
    url(r'^admin_ayudafinanciera', admin_ayudafinanciera.view),
    url(r'^cerrar_materias', api.cerrar_materias),
    url(r'^matriculas_eliminadas', matriculaseliminadas.view),
    url(r'^empresaconvenio', empresaconvenio.view),
    url(r'^pagopymentez', pagopymentez.view),
    url(r'^estudiantemallasinpago', estudiantemallasinpago.view),
    url(r'^mallacompletaconsulta', mallacompletaconsulta.view),
    url(r'^bancos', bancos.view),
    url(r'^alcance_nivelcerrado', alcance_nivelcerrado.view),
    url(r'^aprobacion_nivelcerrado', aprobacion_nivelcerrado.view),
    url(r'^requersoporte', requeri_soporte.view),
    url(r'^soportetics', soportetics.view),
    url(r'^pro_especies', pro_especies.view),
    url(r'^asigna_especies', api.asigna_especies),
    url(r'^archivopichincha', archivopichincha.view),
    url(r'^factura_pichincha', api.factura_pichincha),
    url(r'^inscribircongreso', api.inscribircongreso),
    url(r'^tutorcongreso', tutorcongreso.view),
    url(r'^tutormatricula', tutor_matricula.view),
    url(r'^excelprovcanparsec', excelprovcanparsec.view),
    url(r'^verrequerimiento', verrequerimiento.view),
    url(r'^seg_graduado', seguimientograduado_rangofecha.view),
    url(r'^deuda_estudiantes', deuda_estudiantes.view),
    url(r'^bandeja_atencion', bandeja_atencion.view),
    url(r'^listadoalumnosporgrupo', listadoalumnosmatriculadogrupo.view),
    url(r'^movimientos_reasignacion', movimientos_reasignacion.view),
    url(r'^actividad_vinculacion_porrangofecha', actividad_vinculacion_porrangofecha.view),
    url(r'^tutor_grupo', tutor_grupo.view),
    url(r'^generarpichincha', api.generarpinchincha),
    url(r'^alumnos_xetnia', alumnos_xetnia.view),
    url(r'^multa_docente_materia', multa_docente_materia.view),
    url(r'^est_estudiantes', est_carga_masiva_estudiantes.view),
    url(r'^cpe_carreras_estudiante', cpe_carga_masiva_carreras_estudiante.view),
    url(r'^resumen_sesionescajas', resumen_sesionescajas.view),
    url(r'^mat_carga_masiva', mat_carga_masiva_matriculas.view),
    url(r'^estgeneral_estudiantes', estgeneral_carga_masiva_estudiantes.view),
    url(r'^lib_carga_masiva', lib_carga_masiva.view),
    url(r'^informacion_alumnos', informacion_alumnos.view),
    url(r'^cerrarcajapichincha', api.cerrar_caja_pichincha),
    url(r'^horario_asistente', bandeja_asistente.view),
    url(r'^creahorarios', api.creahorarios),
    url(r'^webinar', webinar.view),
    url(r'^revisionsolicitudpagos', revisionsolicitudpagos.view),
    url(r'^liberarmatricula', liberarmatricula.view),
    url(r'^eliminados_alcancenotas', eliminados_alcancenotas.view),
    url(r'^matriculadosxcarreras', cantidad_alumnos_matriculadosxcarreras.view),
    url(r'^segregado_tramites_solicitudes', segregado_tramites_solicitudes.view),
    url(r'^pagos_rubrosestudiantes', pagos_tiporubrosestudiante.view),
    url(r'^inscritosporanio', inscritosporanio.view),
    url(r'^matriculadospagoinscripcion', matriculadospagoinscripcion.view),
    url(r'^asistenciasxperiodoycarrera', asistenciasxperiodoycarrera.view),
    url(r'^estudiantesxconvenios', estudiantesxconvenios.view),
    url(r'^escenariopractica', escenariopractica.view),
    url(r'^solicitudpracticas', solicitudpracticas.view),
    url(r'^asigna_asistentehorario', api.asigna_asistentehorario),
    url(r'^solicitud_practicasadm', solicitudpracticaadm.view),
    url(r'^supervisor', supervisarevalest.view),
    url(r'^paramevalpract', paramevalpract.view),
    url(r'^ingresos_formadepago', ingresos_formadepago.view),
    url(r'^entregauniformes', entregauniformes.view),
    url(r'^chat', chat.view),
    url(r'^chatsoporte_admin', chatsoporte_admin.view),
    url(r'^parametrodescuento$', parametrodescuento.view),
    url(r'^permisosga$', permisosga.view),
    url(r'^tallauniforme$', tallauniforme.view),
    url(r'^coloruniforme$', coloruniforme.view),
    url(r'^aulamantenimiento$', aulaman.view),
    url(r'^tallazapato$', tallazapato.view),
    url(r'^colorzapato$', colorzapato.view),
    url(r'^empresasinconvenio$', empresasinconvenio.view),
   url(r'^xls_matriculados_xrangofechas', xls_matriculados_xrangofechas.view),
   url(r'^cobrosonline', cobrosonline.view),
   url(r'^alcance_notas', alcance_notas.view),
   url(r'^aprobacion_alcance_notas', aprobacion_alcance_notas.view),
   url(r'^autenticaad', api.autenticaAD),
   url(r'^editclavead', api.editclaveAD),
   url(r'^pagosgestion', pagos_gestion.view),
   url(r'^resumencartera', resumen_cartera.view),
   url(r'^pacifico$', pacifico.view),
   url(r'^cambioclave', commonviews.cambiarclaveAD),
   url(r'^datos_estudiantes', datos_estudiantes.view),
   url(r'^xgrupo_practicas_vinculacion', xgrupo_practicas_vinculacion.view),
   url(r'^absentos_porrangofecha', absentos_porrangofecha.view),
   url(r'^especies_admin', especies_admin.view),
   url(r'^entrega_uniforme_municipio', entrega_uniforme_municipio.view),
   url(r'^ingresos_caja_fecha', ingresos_caja_fecha.view),
   url(r'^cobros_rango_fecha', cobros_rango_fecha.view),
   url(r'^xls_jornada_cobros_rango_fecha', cobros_rango_fecha_jornada.view),
   url(r'^rubros_xvencer_matriculados', rubros_xvencer_matriculados.view),
   # url(r'^diferircuota', diferircuota.view),
   url(r'^cerrarcajareferido', api.cerrar_caja_referido),
   url(r'^asistenciasxnivel', asistenciasxnivel.view),
   url(r'^cuentabancaria', cuentabancaria.view),
   url(r'^xlsmatriculadosxprovincias', xlsmatriculadosxprovincias.view),
   url(r'^becados_xperiodo', becados_xperiodo.view),
   url(r'^preguntaasignatura', preguntaasignatura.view),
   url(r'^proexamenparcial', profe_examenparcial.view),
   url(r'^inscrexamenparcial', inscrip_examenparcial.view),
   url(r'^adminprofeexamen', adminprofeexamen.view),
   url(r'^conduceonline', conduceonline.view),
   url(r'^pagosconduceonline', pagosconduceonline.view),
   url(r'^logincondu$', commonviews.logincondu),
   url(r'^logoutpago$', commonviews.logoutpago),
   url(r'^indicadores_fichasocioecon', indicadores_fichasocioecon.view),
   url(r'^factura_online', api.factura_online),
   url(r'^promocion_estudiantes', promocion_estudiantes.view),
   url(r'^perfil_profesormateria', perfil_profesormateria.view),
   url(r'^jornada', jornada.view),
   url(r'^nivelsocioecon_xperiodo', nivelsocioecon_xperiodo.view),
   url(r'^vendedor', vendedor.view),
   url(r'^admin_grupo_municipio', admin_grupo_municipio.view),
   url(r'^promociones', promociones.view),
   url(r'^alu_matricula', alu_matricula.view),
   url(r'^pro_entrega_acta', pro_entrega_acta.view),
   url(r'^appprivacidad', consultamovil.privacidad),
   url(r'^admin_ayudafinanciera', admin_ayudafinanciera.view),
   url(r'^cerrar_materias', api.cerrar_materias),
   url(r'^matriculas_eliminadas', matriculaseliminadas.view),
   url(r'^empresaconvenio', empresaconvenio.view),
   url(r'^pagopymentez', pagopymentez.view),
   url(r'^estudiantemallasinpago', estudiantemallasinpago.view),
   url(r'^mallacompletaconsulta', mallacompletaconsulta.view),
   url(r'^bancos', bancos.view),
   url(r'^alcance_nivelcerrado', alcance_nivelcerrado.view),
   url(r'^aprobacion_nivelcerrado', aprobacion_nivelcerrado.view),
   url(r'^requersoporte', requeri_soporte.view),
   url(r'^soportetics', soportetics.view),
   url(r'^pro_especies', pro_especies.view),
   url(r'^asigna_especies', api.asigna_especies),
   url(r'^archivopichincha', archivopichincha.view),
   url(r'^factura_pichincha', api.factura_pichincha),
   url(r'^inscribircongreso', api.inscribircongreso),
   url(r'^tutorcongreso', tutorcongreso.view),
   url(r'^tutormatricula', tutor_matricula.view),
   url(r'^excelprovcanparsec', excelprovcanparsec.view),
   url(r'^verrequerimiento', verrequerimiento.view),
   url(r'^seg_graduado', seguimientograduado_rangofecha.view),
   url(r'^deuda_estudiantes', deuda_estudiantes.view),
   url(r'^bandeja_atencion', bandeja_atencion.view),
   url(r'^listadoalumnosporgrupo', listadoalumnosmatriculadogrupo.view),
   url(r'^movimientos_reasignacion', movimientos_reasignacion.view),
   url(r'^actividad_vinculacion_porrangofecha', actividad_vinculacion_porrangofecha.view),
   url(r'^tutor_grupo', tutor_grupo.view),
   url(r'^generarpichincha', api.generarpinchincha),
   url(r'^alumnos_xetnia', alumnos_xetnia.view),
   url(r'^multa_docente_materia', multa_docente_materia.view),
   url(r'^est_estudiantes', est_carga_masiva_estudiantes.view),
   url(r'^cpe_carreras_estudiante', cpe_carga_masiva_carreras_estudiante.view),
   url(r'^resumen_sesionescajas', resumen_sesionescajas.view),
   url(r'^mat_carga_masiva', mat_carga_masiva_matriculas.view),
   url(r'^estgeneral_estudiantes', estgeneral_carga_masiva_estudiantes.view),
   url(r'^lib_carga_masiva', lib_carga_masiva.view),
   url(r'^informacion_alumnos', informacion_alumnos.view),
   url(r'^cerrarcajapichincha', api.cerrar_caja_pichincha),
   url(r'^horario_asistente', bandeja_asistente.view),
   url(r'^creahorarios', api.creahorarios),
   url(r'^webinar', webinar.view),
   url(r'^revisionsolicitudpagos', revisionsolicitudpagos.view),
   url(r'^liberarmatricula', liberarmatricula.view),
   url(r'^eliminados_alcancenotas', eliminados_alcancenotas.view),
   url(r'^matriculadosxcarreras', cantidad_alumnos_matriculadosxcarreras.view),
   url(r'^segregado_tramites_solicitudes', segregado_tramites_solicitudes.view),
   url(r'^pagos_rubrosestudiantes', pagos_tiporubrosestudiante.view),
   url(r'^inscritosporanio', inscritosporanio.view),
   url(r'^matriculadospagoinscripcion', matriculadospagoinscripcion.view),
   url(r'^asistenciasxperiodoycarrera', asistenciasxperiodoycarrera.view),
   url(r'^estudiantesxconvenios', estudiantesxconvenios.view),
   url(r'^escenariopractica', escenariopractica.view),
   url(r'^solicitudpracticas', solicitudpracticas.view),
   url(r'^asigna_asistentehorario', api.asigna_asistentehorario),
   url(r'^solicitud_practicasadm', solicitudpracticaadm.view),
   url(r'^supervisor', supervisarevalest.view),
   url(r'^paramevalpract', paramevalpract.view),
   url(r'^ingresos_formadepago', ingresos_formadepago.view),
   url(r'^entregauniformes', entregauniformes.view),
   url(r'^chat', chat.view),
   url(r'^chatsoporte_admin', chatsoporte_admin.view),
   url(r'^parametrodescuento$', parametrodescuento.view),
   url(r'^permisosga$', permisosga.view),
   url(r'^tallauniforme$', tallauniforme.view),
   url(r'^coloruniforme$', coloruniforme.view),
   url(r'^aulamantenimiento$', aulaman.view),
   url(r'^tallazapato$', tallazapato.view),
   url(r'^colorzapato$', colorzapato.view),
   url(r'^empresasinconvenio$', empresasinconvenio.view),

    url(r'^horarioasistentesolicitudes$', horarioasisitentesolicitudes.view),
    url(r'^base_matriculados', base_matriculados.view),
    url(r'^clientefactura', clientefactura.view),
    url(r'^xls_descuentosaplicados', xls_descuentosaplicados.view),
    url(r'^inscripostulacion', inscripcionpostulacion.view),
    url(r'^xls_gruposetarios', gruposetarios.view),
    url(r'^xls_alumnossocioeco', alumnos_socioeconomica.view),
    url(r'^pago_sustentaciones_docente', pago_sustentaciones_docente.view),
    url(r'^matriz_graduados', matriz_graduados.view),
    url(r'^caces_estudiantes_rangofecha', caces_estudiantes_rangofecha.view),
    url(r'^caces_estudiantes_periodo', caces_estudiantes_periodo.view),
    url(r'^caces_becados', caces_becados.view),
    url(r'^caces_estudiantes_practicas', caces_estudiantes_practicas.view),
    url(r'^caces_proyecto_participantes', caces_proyecto_participantes.view),
    url(r'^listado_pago_sustentaciones', pago_sustentaciones_docente.view),
    url(r'^graduados_sinpracticas', graduados_sinpracticas.view),
    url(r'^estudiantesfamiliar', estudiantesfamiliar.view),
    url(r'^sedemantenimiento', sedemantenimiento.view),
    url(r'^encuestatutores', encuestatut.view),
    url(r'^ambitoencuestatutor', ambitoencuestatutor.view),
    url(r'^encuestaevaluacion', encuestatutor.view),
    url(r'^encuestainscripcion', encuestainscripcion.view),
    url(r'^encuestaestudiante', encuestaestudiante.view),
    url(r'^terminos_constancia', xls_terminos_constancia_inscritos.view),
    url(r'^horaspracticas', horaspracticasporrol.view),
    url(r'^alum_tutorias', alum_tutorias.view),
    url(r'^calificacionesyasistencias', calificacionesyasistenciasxperiodocarreranivel.view),
    url(r'^valoresvencidos_xperiodo_xcoordinacion', valoresvencidos_xperiodo_xcoordinacion.view),
    url(r'^xfechashoraspracticas', horaspracticasporrangodefechas.view),
    url(r'^pagopracticas_docente', pagopracticas_docente.view),
    url(r'^xls_descuentos_promociones', descuentos_promociones.view),
    url(r'^xls_graduadosxanioycarrera', xls_graduadosxanioycarrera.view),
    url(r'^xls_informacion_alumnosxgrupo', xls_informacion_alumnosxgrupo.view),
    url(r'^xls_graduados_condiscapacidad', xls_graduados_condiscapacidad.view),
    url(r'^xls_estudiantes_condiscapacidad', xls_estudiantes_condiscapacidad.view),
    url(r'^xls_convenios', xls_convenios.view),
    url(r'^xls_graduados_general', graduados_general.view),
    url(r'^mesadeayudaxrangofechas', mesadeayuda_porrangofechas.view),
    url(r'^xls_tiemporespuesta_bandejadocente', tiemporespuesta_bandejadocente.view),
    url(r'^xls_pagos_nivel_descuento', xls_pagos_nivel_descuento.view),
    url(r'^procesoquitarabsentimo', pro_clases.procesoquitarabsentimo),
    url(r'^absentosyretirados', xls_absentosyretirados_porfacultad.view),
    url(r'^xls_deudasinscripciones', xls_deudasinscripciones_xcoordinacion.view),
    url(r'^xls_asistencias_xcoordinacion', xls_asistencias_xcoordinacion.view),
    url(r'^xls_personalitb', xls_personalitb.view),
    url(r'^xls_registrovacunas', xls_registrovacunas.view),
    url(r'^xls_inscripciones_gads', xls_inscripciones_gads.view),
    url(r'^xls_materias_culminadas', materias_culminadas.view),
    url(r'^xls_vacunasxfacultades', xls_vacunasregistroxfacultades.view),
    url(r'^cerrarcajasabiertas', api.cerrar_cajas_abiertas),
    url(r'^xls_bandejacajeros_xrangofechas', bandejacajeros_xrangofechas.view),
    url(r'^xls_inscritos_xcanton', inscritos_xcanton.view),
    url(r'^xls_informaciondobe', xls_estudiantes_informaciondobe.view),
    url(r'^xls_inscritos_xprovincia', xls_inscritos_xprovincia.view),
    url(r'^xls_compromisopagos', compromisopagos_xfechas.view),
    url(r'^xls_cursosingles', inscritos_cursosingles.view),
    url(r'^xls_docentes$', xls_docentesactivos.view),
    url(r'^alumnos_cab', cab.view),
    url(r'^xls_datapichincha', datapichincha_matriculados.view),
    url(r'^xls_especiesxdpto', xls_especiesvaloradasxdepartamento.view),
    # url(r'^xls_especiesasuntos', xls_tramitesxdepartamento_asuntos.view),
    url(r'^xls_formasdepago', formasdepago_ingresos.view),
    url(r'^verifica_absentismos', api.verifica_absentismos),
    # url(r'^matrizsecreta', matrizsecreta.view),
   url(r'^horarioasistentesolicitudes$', horarioasisitentesolicitudes.view),
   url(r'^base_matriculados', base_matriculados.view),
   url(r'^clientefactura', clientefactura.view),
   url(r'^xls_descuentosaplicados', xls_descuentosaplicados.view),
   url(r'^inscripostulacion', inscripcionpostulacion.view),
   url(r'^xls_gruposetarios', gruposetarios.view),
   url(r'^xls_alumnossocioeco', alumnos_socioeconomica.view),
   url(r'^pago_sustentaciones_docente', pago_sustentaciones_docente.view),
   url(r'^matriz_graduados', matriz_graduados.view),
   url(r'^caces_estudiantes_rangofecha', caces_estudiantes_rangofecha.view),
   url(r'^caces_estudiantes_periodo', caces_estudiantes_periodo.view),
   url(r'^caces_becados', caces_becados.view),
   url(r'^caces_estudiantes_practicas', caces_estudiantes_practicas.view),
   url(r'^caces_proyecto_participantes', caces_proyecto_participantes.view),
   url(r'^listado_pago_sustentaciones', xls_pago_sustentaciones_docente.view),
   url(r'^graduados_sinpracticas', graduados_sinpracticas.view),
   url(r'^estudiantesfamiliar', estudiantesfamiliar.view),
   url(r'^sedemantenimiento', sedemantenimiento.view),
   url(r'^encuestatutores', encuestatut.view),
   url(r'^ambitoencuestatutor', ambitoencuestatutor.view),
   url(r'^encuestaevaluacion', encuestatutor.view),
   url(r'^encuestainscripcion', encuestainscripcion.view),
   url(r'^encuestaestudiante', encuestaestudiante.view),
   url(r'^terminos_constancia', xls_terminos_constancia_inscritos.view),
   url(r'^horaspracticas', horaspracticasporrol.view),
   url(r'^alum_tutorias', alum_tutorias.view),
   url(r'^calificacionesyasistencias', calificacionesyasistenciasxperiodocarreranivel.view),
   url(r'^valoresvencidos_xperiodo_xcoordinacion', valoresvencidos_xperiodo_xcoordinacion.view),
   url(r'^xfechashoraspracticas', horaspracticasporrangodefechas.view),
   url(r'^pagopracticas_docente', pagopracticas_docente.view),
   url(r'^xls_descuentos_promociones', descuentos_promociones.view),
   url(r'^xls_graduadosxanioycarrera', xls_graduadosxanioycarrera.view),
   url(r'^xls_informacion_alumnosxgrupo', xls_informacion_alumnosxgrupo.view),
   url(r'^xls_graduados_condiscapacidad', xls_graduados_condiscapacidad.view),
   url(r'^xls_estudiantes_condiscapacidad', xls_estudiantes_condiscapacidad.view),
   url(r'^xls_convenios', xls_convenios.view),
   url(r'^xls_graduados_general', graduados_general.view),
   url(r'^mesadeayudaxrangofechas', mesadeayuda_porrangofechas.view),
   url(r'^xls_tiemporespuesta_bandejadocente', tiemporespuesta_bandejadocente.view),
   url(r'^xls_pagos_nivel_descuento', xls_pagos_nivel_descuento.view),
   url(r'^procesoquitarabsentimo', pro_clases.procesoquitarabsentimo),
   url(r'^absentosyretirados', xls_absentosyretirados_porfacultad.view),
   url(r'^xls_deudasinscripciones', xls_deudasinscripciones_xcoordinacion.view),
   url(r'^xls_asistencias_xcoordinacion', xls_asistencias_xcoordinacion.view),
   url(r'^xls_personalitb', xls_personalitb.view),
   url(r'^xls_registrovacunas', xls_registrovacunas.view),
   url(r'^xls_inscripciones_gads', xls_inscripciones_gads.view),
   url(r'^xls_materias_culminadas', materias_culminadas.view),
   url(r'^xls_vacunasxfacultades', xls_vacunasregistroxfacultades.view),
   url(r'^cerrarcajasabiertas', api.cerrar_cajas_abiertas),
   url(r'^xls_bandejacajeros_xrangofechas', bandejacajeros_xrangofechas.view),
   url(r'^xls_inscritos_xcanton', inscritos_xcanton.view),
   url(r'^xls_informaciondobe', xls_estudiantes_informaciondobe.view),
   url(r'^xls_inscritos_xprovincia', xls_inscritos_xprovincia.view),
   url(r'^xls_compromisopagos', compromisopagos_xfechas.view),
   url(r'^xls_cursosingles', inscritos_cursosingles.view),
   url(r'^xls_docentes$', xls_docentesactivos.view),
   url(r'^alumnos_cab', cab.view),
   url(r'^xls_datapichincha', datapichincha_matriculados.view),
   url(r'^xls_especiesxdpto', xls_especiesvaloradasxdepartamento.view),
   # url(r'^xls_especiesasuntos', xls_tramitesxdepartamento_asuntos.view),
   url(r'^xls_formasdepago', formasdepago_ingresos.view),
   url(r'^verifica_absentismos', api.verifica_absentismos),
   # url(r'^matrizsecreta', matrizsecreta.view),

    url(r'^act_docentes_vinculacion', actividades_vinculacion_docentes.view),
    url(r'^profesionalizacion', profesionalizacion.view),
    url(r'^validacorreoinstitucional$', commonviews.valida_correo_institucional),

    url(r'^cierra_clases', api.cierra_clasesabiertas),
    url(r'^xls_cierreclases', xls_cierreclases_porfacultad.view),
    url(r'^xls_docentesclasescerradas$', xls_clasescerradasdocentes_porfacultad.view),
    url(r'^xls_documentos_bib$', xls_documentos_bib.view),
    url(r'^cant_inscritos_xcarrera', cant_inscritos_xcarrera.view),
    url(r'^calificaciones_xnivel', calificaciones_xnivel.view),
    url(r'^infocont', infocont.view),
    url(r'^actividades_horaextra$', actividadesextra.view),
    url(r'^evaluaciondocenteman$', evaluaciondocenteman.view),
    url(r'^evaluacionesdocentes$', evaluacionesdocente.view),
    url(r'^alu_evaluaciondocente$', alu_evaluaciondocente.view),
    url(r'^doc_evaluaciondocente$', doc_evaluaciondocente.view),
    url(r'^dire_evaluaciondocente$', doc_evaluaciondirectivo.view),
    url(r'^localizacion_gps', localizacion_gps.view),
    url(r'^resultadosevaluacion$', resultadosevaluacion.view),
    # url(r'^xls_inscritos', xls_inscritos_datos.view),
    url(r'^xls_referidos_cobro', xls_referidos_cobro.view),

    url(r'^consultasolicitudbeca', tipoestadosolicitud.view),
    url(r'^tipoarchivosolicitudbeca', archivosolicitudbeca.view),
    url(r'^tipogestionbeca', tipogestionbeca.view),
    url(r'^calculaevaluacion', api.calificaciondocente),
    url(r'^xls_infosocioeconomica', xls_infosocioeconomica.view),
    url(r'^solicitudatencion$', solicitudatencion.view),
    url(r'^solicitudadmin$', solicitudadmin.view),
    url(r'^bibliotecavirtual', bibliotecavirtual.view),
    url(r'^notificaciones$', notificaciones.view),
    url(r'^notificaciones_mant$', notificaciones_mant.view),
    url(r'^busqueda', busqueda_usuario.view),
    url(r'^tiempo_tramites_bandeja', tiempo_tramites_bandeja.view),
    url(r'^visitasbiblioteca', xls_visitabibliotecaxcarrera.view),
    url(r'^listadoprogramasvinculacion', listadoprogramasvinculacion.view),
    url(r'^listadoproyectosvinculacion', listadoproyectosvinculacion.view),
    url(r'^testingresoadmin$', testingreso.view),
    url(r'^preguntatestingreso', preguntatestingreso.view),
    url(r'^respuestatestingreso', respuestatestingreso.view),
    url(r'^inscribiralumno', inscribiralumnos.view),
    url(r'^inscripciontest', inscripciontest.view),
    url(r'^colummatestarrastar', columnatestarrastar.view),
    url(r'^encuestaitb', encuestaitb.view),
    url(r'^evaluaciondecano$', evaluaciondecano.view),

    url(r'^man_referenciasweb', man_referenciasweb.view),
    url(r'^man_otrasbibliotecas', man_otrasbibliotecas.view),
    url(r'^listadoaccesobiblioteca', listadoaccesobiblioteca.view),
    url(r'^solicitud_materiaonline$', solicitud_materiaonline.view),
    url(r'^listadodocentes', listadodocentes.view),

    url(r'^logout$', lazy_view_import('sga.commonviews.logout_user')),
    url(r'^account$', lazy_view_import('sga.commonviews.account')),
    url(r'^pass$', lazy_view_import('sga.commonviews.passwd')),
    url(r'^$', lazy_view_import('sga.commonviews.panel')),
    url(r'^encuestadesersionitb', encuestadesercion.view),

    url(r'^solicitudpostulacionbeca$', solicitudpostulacionbeca.view),
    url(r'^solicitudpostulacionbecadmin$', solicitudpostulacionbecaadmin.view),
    url(r'^totalestudiantesxanio', totalestudiantesxanio.view),

   url(r'^estadisticasadmin$', estadisticasadmin.view),
   url(r'^api_rest$', api_rest.view),
   url(r'^xls_docentesxingreso', xls_listadocentesporingreso.view),
   url(r'^xls_entrega_uniformes_admision$', xls_entrega_uniformes_admision.view),
   url(r'^xls_sesiones_caja', xls_sesiones_caja.view),
   url(r'^xls_promouniformes', xls_promocionuniformes.view),
   url(r'^vertestingresoitb$', vertestingresoitb.view),
   url(r'^pedagogica_tutoria$', tutoria_pedagogica.view),
   url(r'^cons_encuestaingreso$', cons_encuestaingreso.view),
   url(r'^conveniocarrera$', conveniocarrera.view),
   url(r'^xls_informacionitb$', xls_informacionitb.view),
   url(r'^solicitudpostulacionbecadjudicada$', solicitudpostulacionbecadjudicada.view),
   url(r'^resumenvisitasbiblioteca', xls_resumen_visitasbiblioteca.view),
   url(r'^xls_matriculados_xperiodo', xls_matriculados_xperiodo.view),

    #     actualización
    url(r'^pro_aulavirtual', pro_aulavirtual.view),
    url(r'^adm_cronogramaacademico', adm_cronogramaacademico.view),
    url(r'^distributivodocente', distributivodocente.view),
    # PROFESORES EVALUACIONES
    url(r'^pro_calificaciones$', pro_calificaciones.view),
    re_path(r'^firma_ec/', include('firmaec.urls')),
    url(r'^aprobarsilabo', aprobarsilabo.view),
   url(r'^admin_teleclinica', admin_teleclinica.view),
   url(r'^evaluacion_teleclinica', teleclinica.view),
   url(r'^solicitudpostulacionbecasoftware$', solicitudpostulacionbecasoftware.view),
}
# urlpatterns += patterns('',
#    url(r'^cambiarclave', commonviews.cambiarclave),
# )
urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += [
    # ...
    path("__debug__/", include("debug_toolbar.urls")),
]
