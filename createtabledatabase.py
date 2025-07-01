import psycopg2
from django.db import connections
from psycopg2 import sql

# Información de conexión a la base de datos
db_config = {
    'dbname': 'nombre_de_la_base_de_datos',
    'user': 'nombre_usuario',
    'password': 'contraseña',
    'host': 'localhost',
    'port': '5432'
}

# Información de conexión a la base de datos
db_config = {
    'dbname': 'itb_bdfull',
    'user': 'postgres',
    'password': '123',
    'host': 'localhost',
    'port': '5432'
}

try:
    connection = psycopg2.connect(**db_config)
    # cursor = connections['default'].cursor()
    cursor = connection.cursor()

    # Definir el comando SQL para crear la tabla PlanAnalitico
    create_table_plan_analitico = """
    CREATE TABLE IF NOT EXISTS sga_plananalitico (
        id SERIAL PRIMARY KEY,
        asignaturamalla_id INTEGER,
        sumilla TEXT DEFAULT '',
        compromiso TEXT DEFAULT '',
        caracterinvestigacion TEXT DEFAULT '',
        fecha_creacion TIMESTAMPTZ NOT NULL,
        fecha_ultimamodificacion TIMESTAMPTZ NOT NULL
    );
    """

    create_table_plan_analitico_rai = """
       CREATE TABLE IF NOT EXISTS sga_PlanAnaliticoRAI (
           id SERIAL PRIMARY KEY,
           plananalitico_id INTEGER,
           descripcion TEXT DEFAULT ''
       );
       """

    create_table_plan_analitico_rac = """
       CREATE TABLE IF NOT EXISTS sga_PlanAnaliticoRAC (
           id SERIAL PRIMARY KEY,
           plananalitico_id INTEGER,
           descripcion TEXT DEFAULT '',
           activo BOOLEAN DEFAULT TRUE
       );
       """

    create_table_plan_analitico_objetivo = """
       CREATE TABLE IF NOT EXISTS sga_PlanAnaliticoObjetivo (
           id SERIAL PRIMARY KEY,
           plananalitico_id INTEGER,
           descripcion TEXT DEFAULT '',
           activo BOOLEAN DEFAULT TRUE
       );
       """

    create_table_plan_analitico_metodologia = """
       CREATE TABLE IF NOT EXISTS sga_PlanAnaliticoMetodologia (
           id SERIAL PRIMARY KEY,
           plananalitico_id INTEGER,
           descripcion TEXT DEFAULT '',
           activo BOOLEAN DEFAULT TRUE
       );
       """

    create_table_plan_analitico_resul_aprend = """
       CREATE TABLE IF NOT EXISTS sga_PlanAnaliticoResulAprend (
           id SERIAL PRIMARY KEY,
           plananalitico_id INTEGER,
           descripcion TEXT DEFAULT ''
       );
       """

    create_table_plan_analitico_unidad = """
       CREATE TABLE IF NOT EXISTS sga_PlanAnaliticoUnidad (
           id SERIAL PRIMARY KEY,
           resultadoaprend_id INTEGER,
           descripcion TEXT DEFAULT ''
       );
       """

    create_table_plan_analitico_tema = """
       CREATE TABLE IF NOT EXISTS sga_PlanAnaliticoTema (
           id SERIAL PRIMARY KEY,
           unidad_id INTEGER,
           descripcion TEXT DEFAULT ''
       );
       """

    create_table_plan_analitico_sub_tema = """
       CREATE TABLE IF NOT EXISTS sga_PlanAnaliticoSubTema (
           id SERIAL PRIMARY KEY,
           unidad_id INTEGER,
           descripcion TEXT DEFAULT ''
       );
       """

    create_table_plan_analitico_elaborado = """
       CREATE TABLE IF NOT EXISTS sga_PlanAnaliticoElaborado (
           id SERIAL PRIMARY KEY,
           plananalitico_id INTEGER,
           descripcion TEXT DEFAULT ''
       );
       """

    create_table_plan_analitico_apa = """
       CREATE TABLE IF NOT EXISTS sga_PlanAnaliticoApa (
           id SERIAL PRIMARY KEY,
           plananalitico_id INTEGER,
           descripcion TEXT DEFAULT ''
       );
       """

    create_table_cronograma_academico = """
           CREATE TABLE IF NOT EXISTS sga_CronograAcademico (
                    id SERIAL PRIMARY KEY,
                    periodo_id INTEGER NOT NULL,
                    nombre VARCHAR(250) NOT NULL,
                    fecha_creacion TIMESTAMP NULL,
                    fecha_ultimamodificacion TIMESTAMP NULL,
                    activo BOOLEAN NOT NULL DEFAULT TRUE
                );
           """

    create_table_cronograma_academico_detalle = """
            CREATE TABLE IF NOT EXISTS sga_CronograAcademicoDetalle (
            id SERIAL PRIMARY KEY,
            cronogramaacademico_id INTEGER NOT NULL,
            descripcion TEXT DEFAULT '',
            inicio DATE NOT NULL,
            fin DATE NOT NULL,
            parcial INTEGER NOT NULL,
            numsemana INTEGER NOT NULL,
            examen BOOLEAN NOT NULL DEFAULT FALSE,
            CONSTRAINT fk_cronogramaacademico
                FOREIGN KEY(cronogramaacademico_id)
                REFERENCES sga_CronograAcademico(id)
                ON DELETE CASCADE
        );
    """

    create_table_cronograma_academico_materia = """
        CREATE TABLE IF NOT EXISTS sga_CronograAcademicoMateria (
        id SERIAL PRIMARY KEY,
        cronogramaacademico_id INTEGER NOT NULL,
        materia_id INTEGER NOT NULL,
        UNIQUE (cronogramaacademico_id, materia_id),
        CONSTRAINT fk_cronogramaacademico
            FOREIGN KEY(cronogramaacademico_id)
            REFERENCES sga_CronograAcademico(id)
            ON DELETE CASCADE
    );
    """

    create_table_silabo_materia = """
        CREATE TABLE IF NOT EXISTS sga_silabo (
        id SERIAL PRIMARY KEY,
        profesor_id INTEGER REFERENCES sga_profesor(id),
        materia_id INTEGER REFERENCES sga_materia(id),
        plananalitico_id INTEGER REFERENCES sga_plananalitico(id),
        silabofirmado BYTEA, -- Assuming file is stored as binary data
        aprobado BOOLEAN DEFAULT FALSE,
        videomagistral BOOLEAN DEFAULT FALSE,
        versionsilabo INTEGER DEFAULT 2,
        versionrecurso INTEGER DEFAULT 2,
        codigoqr BOOLEAN DEFAULT FALSE,
        estado INTEGER DEFAULT null
    );
    """

    create_table_silabo_detalle_materia = """
        CREATE TABLE sga_AprobarSilabo (
        id SERIAL PRIMARY KEY,
        silabo_id INTEGER REFERENCES sga_silabo(id),
        observacion TEXT DEFAULT '',
        fecha TIMESTAMP WITH TIME ZONE,
        persona_id INTEGER REFERENCES sga_persona(id),
        estadoaprobacion INTEGER
    );
    """

    create_table_silabosemanal_materia = """
    CREATE TABLE sga_silabosemanal (
    id SERIAL PRIMARY KEY,
    silabo_id INTEGER REFERENCES sga_silabo(id),
    numsemana INTEGER DEFAULT 0,
    semana INTEGER DEFAULT 0,
    fechainiciosemana DATE,
    fechafinsemana DATE,
    objetivoaprendizaje TEXT,
    enfoque TEXT,
    recursos TEXT,
    evaluacion TEXT,
    horaspresencial NUMERIC(30, 2) DEFAULT 0,
    horaautonoma NUMERIC(30, 2) DEFAULT 0,
    estado INTEGER,
    observaciontecnica TEXT DEFAULT '',
    observacionacademica TEXT DEFAULT '',
    estadocumplimiento INTEGER DEFAULT 2,
    personaobservacion_id INTEGER REFERENCES sga_persona(id),
    fechaobservacion DATE,
    clasevirtualtutor TEXT DEFAULT '',
    zoomurltutor TEXT DEFAULT '',
    recursotutor BYTEA, -- Assuming file is stored as binary data
    fecharecursotutor DATE,
    enfoquedos TEXT,
    enfoquetres TEXT,
    examen BOOLEAN DEFAULT FALSE,
    parcial INTEGER,
    fecha_creacion TIMESTAMPTZ NOT NULL,
    UNIQUE (silabo_id, fechainiciosemana, fechafinsemana, fecha_creacion) -- Assuming fecha_creacion is not available
);
    """

    create_table_silabosemanal_temas = """
        CREATE TABLE sga_DetalleSilaboSemanalTema (
        id SERIAL PRIMARY KEY,
        silabosemanal_id INTEGER REFERENCES sga_silabosemanal(id),
        plananaliticotema_id INTEGER REFERENCES sga_PlanAnaliticoTema(id),
        UNIQUE (silabosemanal_id, plananaliticotema_id) -- Assuming fecha_creacion is not available
    );
    """

    create_table_silabosemanal_subtemas = """
            CREATE TABLE sga_DetalleSilaboSemanalSubTema (
            id SERIAL PRIMARY KEY,
            silabosemanal_id INTEGER REFERENCES sga_silabosemanal(id),
            plananaliticosubtema_id INTEGER REFERENCES sga_PlanAnaliticoSubTema(id),
            UNIQUE (silabosemanal_id, plananaliticosubtema_id) -- Assuming fecha_creacion is not available
        );
    """

    create_table_silabosemanal_recursos = """
                CREATE TABLE sga_RecursosDidacticosSemanal (
                id SERIAL PRIMARY KEY,
                silabosemanal_id INTEGER REFERENCES sga_silabosemanal(id),
                descripcion VARCHAR(250),
                link TEXT,
                UNIQUE (silabosemanal_id, descripcion) -- Assuming fecha_creacion is not available
            );
    """

    # create_table_tiemepodedicacion = """
    #                 CREATE TABLE sga_TiempoDedicacionProfesor (
    #                 id SERIAL PRIMARY KEY,
    #                 nombre VARCHAR(250),
    #                 link TEXT,
    #                 UNIQUE (nombre) -- Assuming fecha_creacion is not available
    #             );
    #     """

    create_table_criterio = """
                        CREATE TABLE sga_Criterio (
                        id SERIAL PRIMARY KEY,
                        nombre VARCHAR(250),
                        dedicacion_id INTEGER REFERENCES sga_TiempoDedicacionDocente(id),
                        tipocriterio INTEGER,
                        UNIQUE (nombre, dedicacion_id) -- Assuming fecha_creacion is not available
                    );
            """

    create_table_criterioperiodo = """
                            CREATE TABLE sga_CriterioPeriodo (
                            id SERIAL PRIMARY KEY,
                            criterio_id INTEGER REFERENCES sga_Criterio(id),
                            periodo_id INTEGER REFERENCES sga_periodo(id),
                            tipocriterio INTEGER,
                            UNIQUE (criterio_id, periodo_id) -- Assuming fecha_creacion is not available
                        );
                """

    # Ejecutar el comando SQL para crear la tabla PlanAnalitico
    # cursor.execute(create_table_plan_analitico)
    # cursor.execute(create_table_plan_analitico_rai)
    # cursor.execute(create_table_plan_analitico_rac)
    # cursor.execute(create_table_plan_analitico_objetivo)
    # cursor.execute(create_table_plan_analitico_metodologia)
    # cursor.execute(create_table_plan_analitico_resul_aprend)
    # cursor.execute(create_table_plan_analitico_unidad)
    # cursor.execute(create_table_plan_analitico_tema)
    # cursor.execute(create_table_plan_analitico_sub_tema)
    # cursor.execute(create_table_plan_analitico_elaborado)
    # cursor.execute(create_table_cronograma_academico)
    # cursor.execute(create_table_cronograma_academico_detalle)
    # cursor.execute(create_table_silabo_materia)
    # cursor.execute(create_table_silabo_detalle_materia)
    # cursor.execute(create_table_silabosemanal_materia)
    # cursor.execute(create_table_silabosemanal_temas)
    # cursor.execute(create_table_silabosemanal_subtemas)
    # cursor.execute(create_table_silabosemanal_recursos)
    # cursor.execute(create_table_tiemepodedicacion)
    cursor.execute(create_table_criterio)
    cursor.execute(create_table_criterioperiodo)

    # Confirmar los cambios
    connection.commit()

    print("Tablas creada exitosamente.")

except (Exception, psycopg2.DatabaseError) as error:
    print(f"Error al crear las tablas: {error}")
finally:
    # Cerrar la conexión
    if connection:
        cursor.close()
        connection.close()

