import sys
import time
from datetime import datetime
from django.db import connections, transaction
from moodle.config import MY_PRIFIX_MOODLE
from sga.funciones import null_to_decimal
from sga.models import Materia, Persona
from moodle.core import CategoriasMoodle


def remover_comilla_simple(cadena):
    return cadena.replace(u"'", u'')

#################################################################################################################
# BUSCAR USUARIO POR USERNAME
#################################################################################################################
def get_user_detail_by_username(username, cursor, detail='username', prefix=MY_PRIFIX_MOODLE):
    """
    Busca el usuario por username y retorna el detalle especificado (username o id).

    Args:
    username (str): El nombre de usuario a buscar.
    cursor (object): El cursor de la base de datos.
    detail (str): El detalle a retornar, puede ser 'username' o 'id'. Por defecto es 'username'.

    Returns:
    str or int or None: El valor del detalle especificado si se encuentra, de lo contrario None.
    """
    if detail not in ['username', 'id']:
        raise ValueError("El detalle debe ser 'username' o 'id'")
    query = f""" SELECT m_use.{detail} FROM {prefix}user AS m_use WHERE m_use.username=%s AND m_use.deleted=0"""
    cursor.execute(query, (username,))
    registro = cursor.fetchone()
    return registro[0] if registro else None


#################################################################################################################
# CREAR USUARIO POR PERSONA
#################################################################################################################
def crear_usuario(cursor, ePerson: Persona, prefix=MY_PRIFIX_MOODLE):
    try:
        username = ePerson.usuario.username
        user_id = get_user_detail_by_username(username, cursor, 'id', prefix)
        if user_id:
            return True, "Usuario ya creado", user_id

        print('Creando usuario...')
        auth_ = 'db'
        pass_ = 'not cached'

        sql1 = f"""
                    INSERT INTO {prefix}user 
                    (username, auth, PASSWORD, firstname, lastname, email, city, country, idnumber, lang, calendartype, confirmed, mnethostid, maildisplay, mailformat, maildigest, autosubscribe, trackforums)
                    VALUES (%s, %s, %s, %s, %s, %s, 'GUAYAQUIL', 'EC', %s, 'es', 'gregorian', '1', '1', '2', '1', '0', '1', '0') RETURNING id;
                """

        cursor.execute(sql1, (
            username, auth_, pass_,
            ePerson.get_nombres(), ePerson.get_apellidos(),
            ePerson.emailinst, ePerson.get_identificacion()
        ))

        user_id = cursor.fetchone()[0]

        if not user_id:
            raise NameError(u"No se creo el usuario")

        print(f'Usuario creado id: {user_id}')
        print('Creando contexto...')

        sql2 = f"""
                    INSERT INTO {prefix}context 
                    (contextlevel, instanceid, DEPTH, PATH, locked) 
                    VALUES ('30', %s, '0', NULL, '0') RETURNING id;
                """

        cursor.execute(sql2, (user_id,))
        context_id = cursor.fetchone()[0]

        print(f'Contexto creado id: {context_id}')

        sql3 = f"""
                    UPDATE {prefix}context 
                    SET contextlevel = '30', instanceid = %s, depth = '2', path = '/1/{context_id}', locked = '0' 
                    WHERE id = %s;
                """

        cursor.execute(sql3, (user_id, context_id))
        return True, '', user_id
    except Exception as ex:
        print(f"Error: {ex}")
        return False, str(ex), 0


#################################################################################################################
# ENROLAR USUARIO POR ID_USER, ID_CURSO, ID_ROL
#################################################################################################################
def enrolar_usuario(cursor, user_id, id_moodle_course, id_role, prefix=MY_PRIFIX_MOODLE):
    try:
        # Obtener el contexto del curso
        sql1 = f"SELECT id FROM {prefix}context WHERE contextlevel = '50' AND instanceid = %s"
        cursor.execute(sql1, (id_moodle_course,))
        result = cursor.fetchone()
        if not result:
            raise NameError(u"Curso no tiene contexto")
        context_id = result[0]
        # Obtener el enrolamiento del curso
        sql2 = f"SELECT id FROM {prefix}enrol WHERE courseid = %s AND status = '0' ORDER BY sortorder, id"
        cursor.execute(sql2, (id_moodle_course,))
        result = cursor.fetchone()
        if not result:
            raise NameError(u"No hay enrolamientos disponibles para el curso")
        rol_manual_id = result[0]

        # Verificar si el usuario ya está enrolado
        sql3 = f"SELECT id FROM {prefix}user_enrolments WHERE enrolid = %s AND userid = %s"
        cursor.execute(sql3, (rol_manual_id, user_id))
        result = cursor.fetchone()
        if result:
            raise NameError(u"Usuario ya está enrolado")

        # Inscribir al usuario
        print("Inscribiendo...")
        fcreacion = int(time.mktime(datetime.now().timetuple()))
        sql4 = f"""
                INSERT INTO {prefix}user_enrolments (enrolid, status, userid, timestart, timeend, modifierid, timecreated, timemodified)
                VALUES (%s, '0', %s, '0', '0', '2', %s, %s)
            """
        cursor.execute(sql4, (rol_manual_id, user_id, fcreacion, fcreacion))

        # Verificar si el usuario ya tiene el rol asignado
        sql5 = f"""
                    SELECT id FROM {prefix}role_assignments 
                    WHERE roleid = %s AND contextid = %s AND userid = %s AND component = '' AND itemid = '0' ORDER BY id
                """
        cursor.execute(sql5, (id_role, context_id, user_id))
        result = cursor.fetchone()

        if result:
            raise NameError(u"Usuario ya está en role_assignments")

        # Asignar el rol al usuario
        print("Confirmar inscripción...")
        sql6 = f"""
                INSERT INTO {prefix}role_assignments (roleid, contextid, userid, component, itemid, timemodified, modifierid, sortorder)
                VALUES (%s, %s, %s, '', '0', %s, '2', '0')
            """
        cursor.execute(sql6, (id_role, context_id, user_id, fcreacion))

        # Verificar y crear cache
        sql7 = f"""
                    SELECT id FROM {prefix}cache_flags 
                    WHERE name = %s AND flagtype = 'accesslib/dirtyusers' LIMIT 1
                """
        cursor.execute(sql7, (user_id,))
        result = cursor.fetchone()

        if not result:
            print("Creando Cache...")
            sql8 = f"""
                        INSERT INTO {prefix}cache_flags (flagtype, name, value, expiry, timemodified)
                        VALUES ('accesslib/dirtyusers', %s, '1', %s, %s)
                    """
            cursor.execute(sql8, (user_id, fcreacion, fcreacion))
        return True, '', 0
    except Exception as ex:
        return False, str(ex), 0


def BuscarCursoQuery(cursor, idcurso_number=None, prefix=MY_PRIFIX_MOODLE):
    try:
        idcurso = 0
        if idcurso_number:
            print(f'Buscando curso...')
            sql4_ = f"SELECT id FROM {prefix}course WHERE idnumber = '{idcurso_number}'"
            cursor.execute(sql4_)
            result4_ = cursor.fetchall()
            if result4_:
                idcurso = result4_[0][0]
        return idcurso, '', True
    except Exception as ex:
        print(ex)
        return 0, ex, False


#################################################################################################################
# CREAR CURSO
#################################################################################################################
def crear_curso_eva(eMateria: Materia):
    from moodle.api import BuscarCategoriasid, BuscarCategorias, CrearCategorias, CrearCursosTarjeta
    eNivel = eMateria.nivel
    eConfig = eNivel.eva
    if not eConfig:
        raise NameError(u"No existe configurado EVA para el nivel")
    if not eConfig.has_web_service_data():
        raise NameError(
            u"No existe configurado EVA para migrar datos: Complete dato: URL, Prefijo, Token, Roles, Categoria")
    prefix = eConfig.prefix_db if eConfig.prefix_db else MY_PRIFIX_MOODLE
    connection_eva = eConfig.type_connection
    if connection_eva == eConfig.TypesConnections.NINGUNA:
        raise NameError(u"No se encuentra configurada la conexión a EVA")
    category_id = eConfig.category_id
    parent_id = 0
    isSuccess, message, data = BuscarCategoriasid(eConfig, category_id)
    if not isSuccess:
        raise NameError(f"Ocurrio un error al buscar (CATEGORIA PRINCIPAL): {message}")
    if data:
        respuesta = data.get('respuesta', [])
        if len(respuesta):
            if 'id' in respuesta[0]:
                parent_id = respuesta[0]['id']
    ePeriodo = eNivel.periodo
    eCarrera = eNivel.carrera
    eNivelMalla = eNivel.nivelmalla
    eGrupo = eNivel.grupo
    eModeloEvaluativo = eMateria.modelo_evaluativo
    if not eCarrera:
        raise NameError(u"No existe carrera configura en el nivel de la materia")
    if not eNivelMalla:
        raise NameError(u"No existe nivel de malla configura en el nivel de la materia")
    if not eGrupo:
        raise NameError(u"No existe grupo configurado en el nivel de la materia")
    if not eModeloEvaluativo:
        raise NameError(u"No existe modelo evaluativo configurado en la materia")

    if parent_id > 0:
        """"
            CREANDO LA CARRERA
        """
        isSuccess, message, data = BuscarCategorias(eConfig, eCarrera.id_number_moodle())
        if not isSuccess:
            raise NameError(f"Ocurrio un error al buscar (CATEGORIA CARRERA): {message}")
        if data:
            respuesta = data.get('respuesta', [])
            parent_carreraid = 0
            if len(respuesta):
                if 'id' in respuesta[0]:
                    parent_carreraid = respuesta[0]['id']
            else:
                isSuccess, message, data = CrearCategorias(eConfig,
                                                           eCarrera.nombre,
                                                           eCarrera.id_number_moodle(),
                                                           eCarrera.nombre,
                                                           parent=parent_id)
                if not isSuccess:
                    raise NameError(f"Ocurrio un error al crear (CATEGORIA CARRERA): {message}")
                if data:
                    respuesta = data.get('respuesta', [])
                    if len(respuesta):
                        if 'id' in respuesta[0]:
                            parent_carreraid = respuesta[0]['id']
            print('Carrera: %s' % eCarrera)
            if parent_carreraid > 0:
                """"
                    CREANDO EL PERIODO ACADEMICO
                """
                idnumber_periodo = u'%s-%s' % (eCarrera.id_number_moodle(), ePeriodo.id_number_moodle())
                isSuccess, message, data = BuscarCategorias(eConfig, idnumber_periodo)
                if not isSuccess:
                    raise NameError(f"Ocurrio un error al buscar (CATEGORIA PERIODO): {message}")
                if data:
                    respuesta = data.get('respuesta', [])
                    parent_periodoid = 0
                    if len(respuesta):
                        if 'id' in respuesta[0]:
                            parent_periodoid = respuesta[0]['id']
                    else:
                        isSuccess, message, data = CrearCategorias(eConfig,
                                                                   ePeriodo.nombre_moodle(),
                                                                   idnumber_periodo,
                                                                   ePeriodo.periodo_repr(),
                                                                   parent=parent_carreraid)
                        if not isSuccess:
                            raise NameError(f"Ocurrio un error al crear (CATEGORIA PERIODO): {message}")
                        if data:
                            respuesta = data.get('respuesta', [])
                            if len(respuesta):
                                if 'id' in respuesta[0]:
                                    parent_periodoid = respuesta[0]['id']
                    print('Periodo lectivo: %s' % ePeriodo)
                    if parent_periodoid > 0:
                        """"
                            CREANDO EL NIVEL MALLA
                        """
                        idnumber_nivelmalla = u'%s-%s' % (idnumber_periodo, eNivelMalla.id_number_moodle())
                        isSuccess, message, data = BuscarCategorias(eConfig, idnumber_nivelmalla)
                        if not isSuccess:
                            raise NameError(f"Ocurrio un error al buscar (CATEGORIA NIVEL MALLA): {message}")
                        if data:
                            respuesta = data.get('respuesta', [])
                            parent_nivelmallaid = 0
                            if len(respuesta):
                                if 'id' in respuesta[0]:
                                    parent_nivelmallaid = respuesta[0]['id']
                            else:
                                isSuccess, message, data = CrearCategorias(eConfig,
                                                                           eNivelMalla.nombre,
                                                                           idnumber_nivelmalla,
                                                                           eNivelMalla.nombre,
                                                                           parent=parent_periodoid)
                                if not isSuccess:
                                    raise NameError(f"Ocurrio un error al crear (CATEGORIA PERIODO): {message}")
                                if data:
                                    respuesta = data.get('respuesta', [])
                                    if len(respuesta):
                                        if 'id' in respuesta[0]:
                                            parent_nivelmallaid = respuesta[0]['id']
                            print('Nivel malla: %s' % eNivelMalla)
                            if parent_nivelmallaid > 0:
                                """"
                                    CREANDO EL GRUPO
                                """
                                idnumber_grupo = u'%s-%s' % (idnumber_nivelmalla, eGrupo.id_number_moodle())
                                isSuccess, message, data = BuscarCategorias(eConfig, idnumber_grupo)
                                if not isSuccess:
                                    raise NameError(f"Ocurrio un error al buscar (CATEGORIA GRUPO): {message}")
                                if data:
                                    respuesta = data.get('respuesta', [])
                                    parent_grupoid = 0
                                    if len(respuesta):
                                        if 'id' in respuesta[0]:
                                            parent_grupoid = respuesta[0]['id']
                                    else:
                                        isSuccess, message, data = CrearCategorias(eConfig,
                                                                                   eGrupo.nombre,
                                                                                   idnumber_grupo,
                                                                                   eGrupo.nombre,
                                                                                   parent=parent_nivelmallaid)
                                        if not isSuccess:
                                            raise NameError(f"Ocurrio un error al crear (CATEGORIA GRUPO): {message}")
                                        if data:
                                            respuesta = data.get('respuesta', [])
                                            if len(respuesta):
                                                if 'id' in respuesta[0]:
                                                    parent_grupoid = respuesta[0]['id']
                                    print('Grupo: %s' % eGrupo)
                                    if parent_grupoid > 0:
                                        """"
                                            CREANDO EL CURSO
                                        """
                                        cursor = connections[connection_eva].cursor()
                                        idnumber_materia = u'%s-%s' % (idnumber_grupo, eMateria.id_number_moodle())
                                        print(idnumber_materia)
                                        cursoid, message, isSuccess = BuscarCursoQuery(cursor, idnumber_materia, prefix)
                                        if not isSuccess:
                                            raise NameError(f"Ocurrio un error al buscar (CURSO): {message}")
                                        cursoid = int(cursoid)
                                        print(f"Curso Id Moodle {cursoid}")
                                        if cursoid == 0:
                                            numsections = 1
                                            summary = u''
                                            startdate = int(time.mktime(eMateria.inicio.timetuple()))
                                            enddate = int(time.mktime(eMateria.fin.timetuple()))
                                            isSuccess, message, data = CrearCursosTarjeta(eConfig,
                                                                                          u'%s' % eMateria.nombre_moodle(),
                                                                                          u'%s - G(%s) - %s' % (
                                                                                              eMateria.nombre_moodle(),
                                                                                              eMateria.nivel.grupo.nombre,
                                                                                              eMateria.id),
                                                                                          parent_grupoid,
                                                                                          idnumber_materia,
                                                                                          summary,
                                                                                          startdate,
                                                                                          enddate,
                                                                                          numsections)
                                            # print(data)
                                            if not isSuccess:
                                                raise NameError(f"Ocurrio un error al crear (CURSO): {message}")
                                            else:
                                                if data:
                                                    respuesta = data.get('respuesta', [])
                                                    if len(respuesta):
                                                        if 'id' in respuesta[0]:
                                                            cursoid = respuesta[0]['id']
                                        if cursoid > 0:
                                            if eMateria.id_moodle_course != cursoid:
                                                eMateria.id_moodle_course = cursoid
                                                eMateria.save()
                                            try:
                                                crear_actualizar_categoria_notas_curso(eMateria)
                                            except Exception as ex:
                                                print(f"Error al crear/actualizar (CATEGORIA NOTAS): {ex}")
                                            try:
                                                crear_actualizar_docente_curso(eMateria)
                                            except Exception as ex:
                                                print(f"Error al crear/actualizar (Docentes): {ex}")

                                            try:
                                                crear_estilo_tarjeta(eMateria)
                                            except Exception as ex:
                                                print(f"Error al crear/actualizar (Tarjeta): {ex}")

                                            try:
                                                crear_actualizar_silabo(eMateria)
                                            except Exception as ex:
                                                print(f"Error al crear/actualizar (Silabo): {ex}")

                                            try:
                                                crear_actualizar_estudiante_curso(eMateria)
                                            except Exception as ex:
                                                print(f"Error al crear/actualizar (Estudiantes): {ex}")
                                            print('********Curso: %s' % eMateria)


#################################################################################################################
# AGREGAR SISTEMA DE CALIFICACION
#################################################################################################################
def crear_actualizar_categoria_notas_curso(eMateria: Materia):
    eNivel = eMateria.nivel
    eConfig = eNivel.eva
    if not eConfig:
        raise NameError(u"No existe configurado EVA para el nivel")
    if not eConfig.has_web_service_data():
        raise NameError(
            u"No existe configurado EVA para migrar datos: Complete dato: URL, Prefijo, Token, Roles, Categoria")
    prefix = eConfig.prefix_db if eConfig.prefix_db else MY_PRIFIX_MOODLE
    eModeloEvaluativo = eMateria.modelo_evaluativo
    if not eModeloEvaluativo:
        raise NameError(u"No existe modelo evaluativo configurado en la materia")
    id_moodle_course = eMateria.id_moodle_course
    if not id_moodle_course:
        raise NameError(u"No se encuentra creado el curso en EVA")
    connection_eva = eConfig.type_connection
    if connection_eva == eConfig.TypesConnections.NINGUNA:
        raise NameError(u"No se encuentra configurada la conexión a EVA")
    cursor = connections[connection_eva].cursor()
    id_moodle_course = eMateria.id_moodle_course
    modelonotas = eModeloEvaluativo.detallemodeloevaluativo_set.filter(puede_migrar_moodle=True)
    if modelonotas:
        query = f"SELECT id FROM {prefix}grade_categories WHERE parent is null and depth=1 and courseid= %s" % id_moodle_course
        cursor.execute(query)
        row = cursor.fetchall()
        padrenota = 0
        fecha = int(time.mktime(datetime.now().date().timetuple()))
        if not row:
            query = f"INSERT INTO {prefix}grade_categories(courseid, parent, depth, path, fullname, aggregation, keephigh, droplow, aggregateonlygraded, hidden, timecreated, timemodified) VALUES (%s, null, 1, '', '?', 13, 0, 0, 0, 0, %s, %s)" % (
                id_moodle_course, fecha, fecha)
            cursor.execute(query)
            query = f"SELECT id FROM {prefix}grade_categories WHERE parent is null and depth=1 and courseid= %s" % id_moodle_course
            cursor.execute(query)
            row = cursor.fetchall()
            query = f"UPDATE {prefix}grade_categories SET path='/%s/' WHERE id= %s" % (row[0][0], row[0][0])
            cursor.execute(query)
            padrenota = row[0][0]
        else:
            padrenota = row[0][0]
        if padrenota > 0:
            ordennota = 1
            query = f"SELECT id FROM {prefix}grade_items WHERE courseid=%s and itemtype='course' and iteminstance=%s" % (
                id_moodle_course, padrenota)
            cursor.execute(query)
            row = cursor.fetchall()
            if not row:
                query = f"INSERT INTO {MY_PRIFIX_MOODLE}grade_items (courseid, categoryid, itemname, itemtype, itemmodule, iteminstance, itemnumber, iteminfo, idnumber, calculation, gradetype, grademax, grademin, scaleid, outcomeid, gradepass, multfactor, plusfactor, aggregationcoef, aggregationcoef2, sortorder, display, decimals, hidden, locked, locktime, needsupdate, weightoverride, timecreated, timemodified) VALUES (%s, null, null, 'course', null, %s, null, null, null, null, 1, 100, 0, null, null, 0, 1, 0, 0, 0, %s, 0, 2, 0, 0, 0, 0, 0, %s, %s)" % (
                    id_moodle_course, padrenota, ordennota, fecha, fecha)
                cursor.execute(query)

            for modelo in modelonotas:
                query = f"SELECT id FROM {prefix}grade_categories WHERE parent=%s and depth=2 and courseid= %s and fullname='%s'" % (
                    padrenota, id_moodle_course, modelo.nombre)
                cursor.execute(query)
                row = cursor.fetchall()
                padremodelo = 0
                if not row:
                    query = f"INSERT INTO {prefix}grade_categories(courseid, parent, depth, path, fullname, aggregation, keephigh, droplow, aggregateonlygraded, hidden, timecreated, timemodified) VALUES (%s, %s, 2, '', '%s', 0, 0, 0, 0, 0, %s, %s)" % (
                        id_moodle_course, padrenota, modelo.nombre, fecha, fecha)
                    cursor.execute(query)
                    query = f"SELECT id FROM {prefix}grade_categories WHERE parent=%s and depth=2 and courseid= %s and fullname='%s'" % (
                        padrenota, id_moodle_course, modelo.nombre)
                    cursor.execute(query)
                    row = cursor.fetchall()
                    padremodelo = row[0][0]
                    query = f"UPDATE {prefix}grade_categories SET path='/%s/%s/' WHERE id= %s" % (
                        padrenota, padremodelo, padremodelo)
                    cursor.execute(query)
                else:
                    padremodelo = row[0][0]
                if padremodelo > 0:
                    ordennota += 1
                    query = f"SELECT id FROM {prefix}grade_items WHERE courseid=%s and itemtype='category' and iteminstance=%s" % (
                        id_moodle_course, padremodelo)
                    cursor.execute(query)
                    row = cursor.fetchall()
                    if not row:
                        query = f"INSERT INTO {prefix}grade_items (courseid, categoryid, itemname, itemtype, itemmodule, iteminstance, itemnumber, iteminfo, idnumber, calculation, gradetype, grademax, grademin, scaleid, outcomeid, gradepass, multfactor, plusfactor, aggregationcoef, aggregationcoef2, sortorder, display, decimals, hidden, locked, locktime, needsupdate, weightoverride, timecreated, timemodified) " \
                                f"VALUES (%s, null, '', 'category', null, %s, null, '', '', null, 1, %s, 0, null, null, 0, 1, 0, 0, %s, %s, 0, %s, 0, 0, 0, 0, 0, %s, %s)" \
                                % (id_moodle_course, padremodelo, modelo.nota_maxima,
                                   null_to_decimal(modelo.nota_maxima / 100, 2), ordennota, 2, fecha, fecha)
                        cursor.execute(query)


#################################################################################################################
# QUITAR DOCENTE
#################################################################################################################
def quitar_docente_curso(eMateria: Materia):
    from moodle.api import UnEnrolarCurso
    eNivel = eMateria.nivel
    eConfig = eNivel.eva
    if not eConfig:
        raise NameError(u"No existe configurado EVA para el nivel")
    if not eConfig.has_web_service_data():
        raise NameError(
            u"No existe configurado EVA para migrar datos: Complete dato: URL, Prefijo, Token, Roles, Categoria")
    prefix = eConfig.prefix_db if eConfig.prefix_db else MY_PRIFIX_MOODLE
    connection_eva = eConfig.type_connection
    if connection_eva == eConfig.TypesConnections.NINGUNA:
        raise NameError(u"No se encuentra configurada la conexión a EVA")
    id_moodle_course = eMateria.id_moodle_course
    if not id_moodle_course:
        raise NameError(u"No se encuentra creado el curso en EVA")
    cursor = connections[connection_eva].cursor()
    rol_teacher_id = eConfig.role_teacher
    user_ids = ""
    for eProfesorMateria in eMateria.profesores_materia():
        eProfesor = eProfesorMateria.profesor
        if eProfesor and eProfesor.persona.usuario and not 'DEFINIR POR' in eProfesor.persona.nombres:
            username = eProfesor.persona.usuario.username
            user_id = get_user_detail_by_username(username, cursor, 'id', prefix)
            if user_id is not None:
                user_ids += "%s," % user_id
    query = f"""
            SELECT DISTINCT m_asi.userid 
            FROM {prefix}role_assignments AS m_asi 
            INNER JOIN {prefix}context AS m_con ON m_asi.contextid = m_con.id
            INNER JOIN {prefix}user AS m_user ON m_user.id = m_asi.userid 
            WHERE m_asi.roleid = %s AND m_con.instanceid = %s AND m_user.username = %s
        """
    cursor.execute(query, (rol_teacher_id, id_moodle_course, username))
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            unrolest = UnEnrolarCurso(eConfig, rol_teacher_id, row[0], id_moodle_course)
            print('************ Eliminar Profesor: *** %s' % username)


#################################################################################################################
# AGREGAR DOCENTE
#################################################################################################################
def crear_actualizar_docente_curso(eMateria: Materia):
    eNivel = eMateria.nivel
    eConfig = eNivel.eva
    if not eConfig:
        raise NameError(u"No existe configurado EVA para el nivel")
    if not eConfig.has_web_service_data():
        raise NameError(
            u"No existe configurado EVA para migrar datos: Complete dato: URL, Prefijo, Token, Roles, Categoria")
    prefix = eConfig.prefix_db if eConfig.prefix_db else MY_PRIFIX_MOODLE
    connection_eva = eConfig.type_connection
    if connection_eva == eConfig.TypesConnections.NINGUNA:
        raise NameError(u"No se encuentra configurada la conexión a EVA")
    id_moodle_course = eMateria.id_moodle_course
    if not id_moodle_course:
        raise NameError(u"No se encuentra creado el curso en EVA")
    cursor = connections[connection_eva].cursor()
    if id_moodle_course:
        quitar_docente_curso(eMateria)
        for eProfesorMateria in eMateria.profesores_materia():
            eProfesor = eProfesorMateria.profesor
            if eProfesor and eProfesor.persona.usuario and not 'DEFINIR POR' in eProfesor.persona.nombres:
                username = eProfesor.persona.usuario.username
                user_id = get_user_detail_by_username(username, cursor, 'id', prefix)
                if user_id is None:
                    isSuccess, message, user_id = crear_usuario(cursor, eProfesor.persona, prefix)
                    if not isSuccess:
                        raise NameError(message)

                    if user_id > 0:
                        isSuccess, message, id = enrolar_usuario(cursor, user_id, id_moodle_course,
                                                                 eConfig.role_teacher, prefix)
                        if not isSuccess:
                            raise NameError(message)
                        print('**********PROFESOR: %s' % eProfesor)


#################################################################################################################
# QUITAR ESTUDIANTE
#################################################################################################################
def quitar_estudiante_curso(eMateria: Materia):
    from moodle.api import UnEnrolarCurso
    eNivel = eMateria.nivel
    eConfig = eNivel.eva
    if not eConfig:
        raise NameError(u"No existe configurado EVA para el nivel")
    if not eConfig.has_web_service_data():
        raise NameError(
            u"No existe configurado EVA para migrar datos: Complete dato: URL, Prefijo, Token, Roles, Categoria")
    prefix = eConfig.prefix_db if eConfig.prefix_db else MY_PRIFIX_MOODLE
    connection_eva = eConfig.type_connection
    if connection_eva == eConfig.TypesConnections.NINGUNA:
        raise NameError(u"No se encuentra configurada la conexión a EVA")
    id_moodle_course = eMateria.id_moodle_course
    if not id_moodle_course:
        raise NameError(u"No se encuentra creado el curso en EVA")
    cursor = connections[connection_eva].cursor()
    rol_student_id = eConfig.role_student
    user_ids = ""
    for eMateriaAsignada in eMateria.materiaasignada_set.filter(cerrado=False):
        eMatricula = eMateriaAsignada.matricula
        eInscripcion = eMatricula.inscripcion
        ePersona = eInscripcion.persona
        if ePersona and ePersona.usuario:
            username = ePersona.usuario.username
            user_id = get_user_detail_by_username(username, cursor, 'id', prefix)
            if user_id is not None:
                user_ids += "%s," % user_id
    if user_ids:
        query = f"""
                SELECT DISTINCT m_asi.userid 
                FROM {prefix}role_assignments AS m_asi 
                INNER JOIN {prefix}context AS m_con ON m_asi.contextid = m_con.id
                INNER JOIN {prefix}user AS m_user ON m_user.id = m_asi.userid 
                WHERE m_asi.roleid = %s AND m_con.instanceid = %s AND m_user.username = %s
            """
        cursor.execute(query, (rol_student_id, id_moodle_course, username))
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                unrolest = UnEnrolarCurso(eConfig, rol_student_id, row[0], id_moodle_course)
                print('************ Eliminar Estudiante: *** %s' % username)


#################################################################################################################
# AGREGAR ESTUDIANTE
#################################################################################################################
def crear_actualizar_estudiante_curso(eMateria: Materia):
    eNivel = eMateria.nivel
    eConfig = eNivel.eva
    if not eConfig:
        raise NameError(u"No existe configurado EVA para el nivel")
    if not eConfig.has_web_service_data():
        raise NameError(
            u"No existe configurado EVA para migrar datos: Complete dato: URL, Prefijo, Token, Roles, Categoria")
    prefix = eConfig.prefix_db if eConfig.prefix_db else MY_PRIFIX_MOODLE
    connection_eva = eConfig.type_connection
    if connection_eva == eConfig.TypesConnections.NINGUNA:
        raise NameError(u"No se encuentra configurada la conexión a EVA")
    id_moodle_course = eMateria.id_moodle_course
    if not id_moodle_course:
        raise NameError(u"No se encuentra creado el curso en EVA")
    cursor = connections[connection_eva].cursor()
    if id_moodle_course:
        try:
            quitar_estudiante_curso(eMateria)
        except Exception as ex:
            print(f"Error al quitar estudiante del curso: {ex}")
        for eMateriaAsignada in eMateria.materiaasignada_set.filter(cerrado=False):
            eMatricula = eMateriaAsignada.matricula
            eInscripcion = eMatricula.inscripcion
            ePersona = eInscripcion.persona
            if ePersona and ePersona.usuario:
                username = ePersona.usuario.username
                user_id = get_user_detail_by_username(username, cursor, 'id', prefix)
                if user_id is None:
                    isSuccess, message, user_id = crear_usuario(cursor, ePersona, prefix)
                    if not isSuccess:
                        raise NameError(message)

                    if user_id > 0:
                        isSuccess, message, id = enrolar_usuario(cursor, user_id, id_moodle_course,
                                                                 eConfig.role_student, prefix)
                        if not isSuccess:
                            raise NameError(message)
                        print('**********ESTUDIANTE: %s' % eInscripcion)


#################################################################################################################
# CATEGORIAS EVA DEL CURSO
#################################################################################################################
def obtener_categorias_curso(eMateria: Materia):
    eNivel = eMateria.nivel
    eConfig = eNivel.eva
    if not eConfig:
        raise NameError(u"No existe configurado EVA para el nivel")
    if not eConfig.has_web_service_data():
        raise NameError(
            u"No existe configurado EVA para migrar datos: Complete dato: URL, Prefijo, Token, Roles, Categoria")
    prefix = eConfig.prefix_db if eConfig.prefix_db else MY_PRIFIX_MOODLE
    connection_eva = eConfig.type_connection
    if connection_eva == eConfig.TypesConnections.NINGUNA:
        raise NameError(u"No se encuentra configurada la conexión a EVA")
    id_moodle_course = eMateria.id_moodle_course
    if not id_moodle_course:
        raise NameError(u"No se encuentra creado el curso en EVA")
    categorias = []
    try:
        cursor = connections[connection_eva].cursor()
        sql = f"""
        SELECT DISTINCT UPPER(gc.fullname), items.sortorder 
        FROM {prefix}grade_items AS items
        LEFT JOIN {prefix}grade_categories AS gc ON gc.courseid = items.courseid
        WHERE items.itemtype = 'category' AND items.courseid = %s AND gc.id = items.iteminstance AND gc.depth = 2
        ORDER BY items.sortorder;""" % str(id_moodle_course)
        cursor.execute(sql)
        rows = cursor.fetchall()
        categorias = [row[0] for row in rows]
    except Exception as e:
        raise RuntimeError("Error al ejecutar la consulta en la base de datos") from e
    finally:
        cursor.close()
    return categorias


def obtener_calificaciones_curso(eMateria: Materia, ePersona: Persona):
    eNivel = eMateria.nivel
    eConfig = eNivel.eva
    if not eConfig:
        raise NameError(u"No existe configurado EVA para el nivel")
    if not eConfig.has_web_service_data():
        raise NameError(
            u"No existe configurado EVA para migrar datos: Complete dato: URL, Prefijo, Token, Roles, Categoria")
    prefix = eConfig.prefix_db if eConfig.prefix_db else MY_PRIFIX_MOODLE
    connection_eva = eConfig.type_connection
    if connection_eva == eConfig.TypesConnections.NINGUNA:
        raise NameError(u"No se encuentra configurada la conexión a EVA")
    id_moodle_course = eMateria.id_moodle_course
    if not id_moodle_course:
        raise NameError(u"No se encuentra creado el curso en EVA")
    username = ePersona.usuario.username
    if username == 'nlalmendares':
        pass

    calificaciones = []
    try:
        cursor = connections[connection_eva].cursor()
        sql = f"""SELECT ROUND(nota.finalgrade,2), UPPER(gc.fullname)
                            FROM {prefix}grade_grades nota
                    INNER JOIN {prefix}grade_items it ON nota.itemid=it.id AND courseid=%s AND itemtype='category'
                    INNER JOIN {prefix}grade_categories gc ON gc.courseid=it.courseid AND gc.id=it.iteminstance AND gc.depth=2
                    INNER JOIN {prefix}user us ON nota.userid=us.id
                    WHERE us.username ='%s' 
                    ORDER BY it.sortorder
                """ % (str(id_moodle_course), username)
        cursor.execute(sql)
        rows = cursor.fetchall()
        calificaciones = [{'nota': row[0], 'campo': row[1]} for row in rows]
    except Exception as e:
        raise RuntimeError("Error al ejecutar la consulta en la base de datos") from e
    finally:
        cursor.close()
    return calificaciones


def crear_estilo_tarjeta(eMateria: Materia):
    eNivel = eMateria.nivel
    eConfig = eNivel.eva
    if not eConfig:
        raise NameError(u"No existe configurado EVA para el nivel")
    if not eConfig.has_web_service_data():
        raise NameError(u"No existe configurado EVA para migrar datos: Complete dato: URL, Prefijo, Token, Roles, Categoria")
    prefix = eConfig.prefix_db if eConfig.prefix_db else MY_PRIFIX_MOODLE
    connection_eva = eConfig.type_connection
    if connection_eva == eConfig.TypesConnections.NINGUNA:
        raise NameError(u"No se encuentra configurada la conexión a EVA")
    id_moodle_course = eMateria.id_moodle_course
    if not id_moodle_course:
        raise NameError(u"No se encuentra creado el curso en EVA")
    cursor = connections[connection_eva].cursor()
    with transaction.atomic(using=connection_eva):
        try:
            # Actualiza el formato de los temas a 'topics'
            cursor.execute(f"UPDATE {prefix}course_format_options SET value=%s WHERE courseid=%s AND format=%s",
                           [0, id_moodle_course, 'topics']
                           )

            # Verifica y actualiza/insertar 'coursedisplay' en 'remuiformat'
            cursor.execute(f"SELECT id FROM {prefix}course_format_options WHERE name=%s AND courseid=%s AND format=%s",
                           ['coursedisplay', id_moodle_course, 'remuiformat']
                           )
            exists = cursor.fetchone()

            if exists:
                cursor.execute(f"UPDATE {prefix}course_format_options SET value=%s WHERE name=%s AND courseid=%s AND format=%s",
                               [1, 'coursedisplay', id_moodle_course, 'remuiformat']
                               )
            else:
                cursor.execute(f"""INSERT INTO {prefix}course_format_options (courseid, format, sectionid, name, value)
                    VALUES (%s, %s, %s, %s, %s)""",
                               [id_moodle_course, 'remuiformat', 0, 'coursedisplay', 1]
                               )

            # Verifica y actualiza/insertar 'remuicourseformat' en 'remuiformat'
            cursor.execute(f"SELECT id FROM {prefix}course_format_options WHERE name=%s AND courseid=%s AND format=%s",
                           ['remuicourseformat', id_moodle_course, 'remuiformat']
                           )
            exists = cursor.fetchone()

            if exists:
                cursor.execute(f"UPDATE {prefix}course_format_options SET value=%s WHERE name=%s AND courseid=%s AND format=%s",
                               [0, 'remuicourseformat', id_moodle_course, 'remuiformat']
                               )
            else:
                cursor.execute(f"""INSERT INTO {prefix}course_format_options (courseid, format, sectionid, name, value) VALUES (%s, %s, %s, %s, %s)""",
                               [id_moodle_course, 'remuiformat', 0, 'remuicourseformat', 0]
                               )
        except Exception as ex:
            transaction.set_rollback(True, using=connection_eva)
            print(f"{str(ex)} - {sys.exc_info()[-1].tb_lineno}")
        finally:
            cursor.close()


#################################################################################################################
# AGREGAR SILABO
#################################################################################################################
def crear_actualizar_silabo(eMateria: Materia):
    eNivel = eMateria.nivel
    eConfig = eNivel.eva
    if not eConfig:
        raise NameError(u"No existe configurado EVA para el nivel")
    if not eConfig.has_web_service_data():
        raise NameError(u"No existe configurado EVA para migrar datos: Complete dato: URL, Prefijo, Token, Roles, Categoria")
    prefix = eConfig.prefix_db if eConfig.prefix_db else MY_PRIFIX_MOODLE
    connection_eva = eConfig.type_connection
    if connection_eva == eConfig.TypesConnections.NINGUNA:
        raise NameError(u"No se encuentra configurada la conexión a EVA")
    id_moodle_course = eMateria.id_moodle_course
    if not id_moodle_course:
        raise NameError(u"No se encuentra creado el curso en EVA")
    cursor = connections[connection_eva].cursor()
    sumary = ''
    with transaction.atomic(using=connection_eva):
        try:
            name = eMateria.asignatura.nombre
            # sumary += '<iframe src="https://sga.itb.edu.ec/adm_silabo?action=pregrado&codigo=' + str(eMateria.id) + '"  class="filter_hvp" id="hvp_4383" style="width:100%; height:1000px; border:0;" frameborder="0" allowfullscreen="allowfullscreen"></iframe>'
            sumary = remover_comilla_simple(sumary)
            queries = []

            # Consulta sección 0
            cursor.execute(f"SELECT id FROM {prefix}course_sections WHERE course = %s AND section = %s",
                           [id_moodle_course, 0])
            r_seccion_0 = cursor.fetchone()
            if r_seccion_0:
                # Actualizar sección 0
                queries.append((f"UPDATE {prefix}course_sections SET name = %s, summary = %s, availability = %s WHERE course = %s AND section = %s",
                                [eMateria.asignatura.nombre, sumary, '{"op":"&","c":[],"showc":[]}', id_moodle_course, 0]))

            else:
                # Insertar sección 0
                queries.append((f"""INSERT INTO {prefix}course_sections (id, course, section, name, summary, availability, summaryformat, visible, timemodified) VALUES (default, %s, %s, %s, %s, %s, %s, %s, %s)""",
                                [id_moodle_course, 0, eMateria.asignatura.nombre, sumary, '{"op":"&","c":[],"showc":[]}', 1, 1, int(time.mktime(datetime.now().timetuple()))]
                                ))

            # Consulta sección 1
            cursor.execute(f"SELECT id FROM {prefix}course_sections WHERE course = %s AND section = %s",
                           [id_moodle_course, CategoriasMoodle.CLASES_VIRTUALES])
            r_seccion_1 = cursor.fetchone()
            if r_seccion_1:
                # Actualizar sección 1
                queries.append((f"UPDATE {prefix}course_sections SET name = %s, summary = %s WHERE course = %s AND section = %s",
                                [f'{CategoriasMoodle.get_option_display(CategoriasMoodle.CLASES_VIRTUALES)}',
                                 '', id_moodle_course, CategoriasMoodle.CLASES_VIRTUALES]))

            else:
                # Insertar sección 1
                queries.append((f"""INSERT INTO {prefix}course_sections (id, course, section, name, summary, summaryformat, visible, timemodified) VALUES (default, %s, %s, %s, %s, %s, %s, %s)""",
                                [id_moodle_course, CategoriasMoodle.CLASES_VIRTUALES,
                                 f'{CategoriasMoodle.get_option_display(CategoriasMoodle.CLASES_VIRTUALES)}', '', 1, 1,
                                 int(time.mktime(datetime.now().timetuple()))]
                                ))

            # Consulta sección 2
            cursor.execute(f"SELECT id FROM {prefix}course_sections WHERE course = %s AND section = %s",
                           [id_moodle_course, CategoriasMoodle.CLASES_DE_REFUERZO])
            r_seccion_2 = cursor.fetchone()
            if r_seccion_2:
                # Actualizar sección 2
                queries.append((f"UPDATE {prefix}course_sections SET name = %s, summary = %s WHERE course = %s AND section = %s",
                                [f'{CategoriasMoodle.get_option_display(CategoriasMoodle.CLASES_DE_REFUERZO)}',
                                 '', id_moodle_course, CategoriasMoodle.CLASES_DE_REFUERZO]))

            else:
                # Insertar sección 2
                queries.append((f"""INSERT INTO {prefix}course_sections (id, course, section, name, summary, summaryformat, visible, timemodified) VALUES (default, %s, %s, %s, %s, %s, %s, %s)""",
                                [id_moodle_course, CategoriasMoodle.CLASES_DE_REFUERZO,
                                 f'{CategoriasMoodle.get_option_display(CategoriasMoodle.CLASES_DE_REFUERZO)}', '', 1, 1,
                                 int(time.mktime(datetime.now().timetuple()))]
                                ))


            # Consulta sección 3
            cursor.execute(f"SELECT id FROM {prefix}course_sections WHERE course = %s AND section = %s",
                           [id_moodle_course, CategoriasMoodle.ACTIVIDAD_AUTONOMA])
            r_seccion_3 = cursor.fetchone()
            if r_seccion_3:
                # Actualizar sección 3
                queries.append((f"UPDATE {prefix}course_sections SET name = %s, summary = %s WHERE course = %s AND section = %s",
                                [f'{CategoriasMoodle.get_option_display(CategoriasMoodle.ACTIVIDAD_AUTONOMA)}',
                                 '', id_moodle_course, CategoriasMoodle.ACTIVIDAD_AUTONOMA]))

            else:
                # Insertar sección 3
                queries.append((f"""INSERT INTO {prefix}course_sections (id, course, section, name, summary, summaryformat, visible, timemodified) VALUES (default, %s, %s, %s, %s, %s, %s, %s)""",
                                [id_moodle_course, CategoriasMoodle.ACTIVIDAD_AUTONOMA,
                                 f'{CategoriasMoodle.get_option_display(CategoriasMoodle.ACTIVIDAD_AUTONOMA)}', '', 1, 1,
                                 int(time.mktime(datetime.now().timetuple()))]
                                ))

            sections = [
                (CategoriasMoodle.ACTIVIDAD_CONTACTO_DOCENTE, f'{CategoriasMoodle.get_option_display(CategoriasMoodle.ACTIVIDAD_CONTACTO_DOCENTE)}'),
                (CategoriasMoodle.FOROS, f'{CategoriasMoodle.get_option_display(CategoriasMoodle.FOROS)}'),
                (CategoriasMoodle.COMPENDIOS, f'{CategoriasMoodle.get_option_display(CategoriasMoodle.COMPENDIOS)}'),
                (CategoriasMoodle.PRESENTACIONES, f'{CategoriasMoodle.get_option_display(CategoriasMoodle.PRESENTACIONES)}'),
                (CategoriasMoodle.VIDEOS_MAGISTRALES, f'{CategoriasMoodle.get_option_display(CategoriasMoodle.VIDEOS_MAGISTRALES)}'),
                (CategoriasMoodle.MATERIAL_COMPLEMENTARIO, f'{CategoriasMoodle.get_option_display(CategoriasMoodle.MATERIAL_COMPLEMENTARIO)}'),
                (CategoriasMoodle.GUIAS_DEL_ESTUDIANTE, f'{CategoriasMoodle.get_option_display(CategoriasMoodle.GUIAS_DEL_ESTUDIANTE)}'),
                (CategoriasMoodle.ACTIVIDADES_PRACTICA_EXPERIMENTAL, f'{CategoriasMoodle.get_option_display(CategoriasMoodle.ACTIVIDADES_PRACTICA_EXPERIMENTAL)}'),
                (CategoriasMoodle.EXAMENES, f'{CategoriasMoodle.get_option_display(CategoriasMoodle.EXAMENES)}'),
            ]

            for section, section_name in sections:
                cursor.execute(f"SELECT id FROM {prefix}course_sections WHERE course = %s AND section = %s",
                               [id_moodle_course, section])
                result = cursor.fetchone()

                if result:
                    queries.append((f"UPDATE {prefix}course_sections SET name = %s, summary = %s, visible = %s WHERE course = %s AND section = %s",
                                    [section_name, '', 1, id_moodle_course, section]
                                    ))
                else:
                    queries.append((f"""INSERT INTO {prefix}course_sections (id, course, section, name, summary, summaryformat, visible, timemodified)
                            VALUES (default, %s, %s, %s, %s, %s, %s, %s)""",
                                    [id_moodle_course, section, section_name, '', 1, 1,
                                     int(time.mktime(datetime.now().timetuple()))]
                                    ))

            # Ejecutar todas las consultas
            for query, params in queries:
                cursor.execute(query, params)

            # Actualizar cacherev en la tabla course
            fecha = int(time.mktime(datetime.now().timetuple()))
            cursor.execute(f"UPDATE {prefix}course SET cacherev = %s WHERE id = %s", [fecha, id_moodle_course])

        except Exception as ex:
            transaction.set_rollback(True, using=connection_eva)
            print(f"Error: {str(ex)} - Línea {sys.exc_info()[-1].tb_lineno}")
        finally:
            cursor.close()


def crear_actualizar_portada(eMateria: Materia):
    from moodle.api import BuscarCategoriasid
    eNivel = eMateria.nivel
    eConfig = eNivel.eva
    if not eConfig:
        raise NameError(u"No existe configurado EVA para el nivel")
    if not eConfig.has_web_service_data():
        raise NameError(u"No existe configurado EVA para migrar datos: Complete dato: URL, Prefijo, Token, Roles, Categoria")
    prefix = eConfig.prefix_db if eConfig.prefix_db else MY_PRIFIX_MOODLE
    connection_eva = eConfig.type_connection
    if connection_eva == eConfig.TypesConnections.NINGUNA:
        raise NameError(u"No se encuentra configurada la conexión a EVA")
    id_moodle_course = eMateria.id_moodle_course
    if not id_moodle_course:
        raise NameError(u"No se encuentra creado el curso en EVA")
    cursor = connections[connection_eva].cursor()
    isSuccess, message, data = BuscarCategoriasid(eConfig, category_id)
    if not isSuccess:
        raise NameError(f"Ocurrio un error al buscar (CATEGORIA PRINCIPAL): {message}")
    sumary = ''
    with transaction.atomic(using=connection_eva):
        try:
            pass

        except Exception as ex:
            transaction.set_rollback(True, using=connection_eva)
            print(f"Error: {str(ex)} - Línea {sys.exc_info()[-1].tb_lineno}")
        finally:
            cursor.close()




def calculo_modelo_evaluativo(eMateriaAsignada):
    N1 = eMateriaAsignada.campo('N1')
    N2 = eMateriaAsignada.campo('N2')
    N3 = eMateriaAsignada.campo('N3')
    N4 = eMateriaAsignada.campo('N4')
    EX = eMateriaAsignada.campo('EX')
    P = eMateriaAsignada.campo('P')
    RE = eMateriaAsignada.campo('RE')
    P.valor = N1.valor + N2.valor + N3.valor + N4.valor + EX.valor
    P.save()
    promedio = P.valor
    eMateriaAsignada.notafinal = null_to_decimal(promedio, 0)
    if eMateriaAsignada.notafinal < 40:
        RE.valor = 0
        RE.save()
    elif eMateriaAsignada.notafinal < 70:
        if RE.valor > 0:
            eMateriaAsignada.notafinal = null_to_decimal((RE.valor + float(eMateriaAsignada.notafinal)) / 2, 0)
    else:
        RE.valor = 0
        RE.save()
    if EX.valor > 0 or RE.valor > 0:
        if eMateriaAsignada.asistenciafinal < 70:
            EX.valor = 0
            EX.save()
            RE.valor = 0
            RE.save()
            P.valor = N1.valor + N2.valor + N3.valor + N4.valor + EX.valor
            P.save()
            promedio = P.valor
            eMateriaAsignada.notafinal = null_to_decimal(promedio, 0)
    eMateriaAsignada.save()