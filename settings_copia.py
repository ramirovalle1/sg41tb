# Django settings for iavq project.
import os
import platform
import django
from psycopg2 import pool

DEBUG = True
# TEMPLATE_DEBUG = DEBUG

ALLOWED_HOSTS = ['*']

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# SITE_ROOT = os.path.dirname(os.path.realpath(__file__))
SITE_ROOT = os.path.dirname(os.path.realpath("settings.py"))
DJANGO_ROOT = os.path.dirname(os.path.realpath(django.__file__))

SECRETARIA_EMAIL = ['secretaria@bolivariano.edu.ec']

NOMBRE_INSTITUCION = "Instituto Superior Tecnologico Bolivariano de Tecnologia"

DEFAULT_PASSWORD = 'itb'
CENTRO_ID = 1

CENTRO_EXTERNO = False
INSCRIPCION_CONDUCCION = False
ADMINISTRATIVOS_GROUP_ID = 28
RECTORADO_GROUP_ID = 3
VICERECTORADO_GROUP_ID = 38
SISTEMAS_GROUP_ID = 1
TICS_GROUP_ID = 79
PROFESORES_GROUP_ID = 5
ALUMNOS_GROUP_ID = 6
FINANCIERO_GROUP_ID = 11
SECRETARIAGENERAL_GROUP_ID = 4
COORDINACION_ACADEMICA_GROUP_ID = 4
BUCKI_GROUP_ID = 41
COORDINACION_ACADEMICA_UASS = 2
COORD_ACADEMICO_UACECD = 17
ESTADISTICA = 51
ASISTENTE_VICERECTORADO = 63
DOBE_GROUP_ID = 10

# linea adicionada por Freddy Bravo para activar memcached#CACHE_BACKEND = 'memcached://127.0.0.1:11211/'

ADMINS = (
    ('Tatiana', 'tytapia@gmail.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'itb',  # Or path to database file if using sqlite3.
        'USER': 'postgres',  # Not used with sqlite3.
        'PASSWORD': '123456',  # Not used with sqlite3.
        'HOST': '127.0.0.1',  # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '5432',  # Set to empty string for default. Not used with sqlite3.
        #	'OPTIONS': {
        #           'options': '-c lock_timeout=5min -c statement_timeout=10min'
        #       },
    },
    'moodle_eva_1': {
        'ENGINE': 'django.db.backends.mysql',
        # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'moodle',  # Or path to database file if using sqlite3.
        'USER': 'moodleuser',  # Not used with sqlite3.
        'PASSWORD': 'M00dL3Bu1nc0ITB**',  # Not used with sqlite3.
        'HOST': '104.196.251.127',  # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '3306',  # Set to empty string for default. Not used with sqlite3.
    },
}
# Construir la cadena de conexión DSN
db_params = DATABASES['default']
dsn = f"dbname={db_params['NAME']} user={db_params['USER']} password={db_params['PASSWORD']} host={db_params['HOST']} port={db_params['PORT']}"

# Configurar el pool de conexiones
minconn = 5  # Número mínimo de conexiones en el pool
maxconn = 200  # Número máximo de conexiones en el pool
connection_pool = pool.ThreadedConnectionPool(minconn=minconn, maxconn=maxconn, dsn=dsn)

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Guayaquil'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-es'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = os.path.join(SITE_ROOT, 'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
# STATIC_ROOT = os.path.join(SITE_ROOT, 'static')
STATIC_ROOT = ''

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# URL prefix for admin static files -- CSS, JavaScript and images.
# Make sure to use a trailing slash.
# Examples: "http://foo.com/static/admin/", "/static/admin/".
ADMIN_MEDIA_PREFIX = '/static/admin/'

# # Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(SITE_ROOT, 'static'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    #    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '04m76#%5&*fg8^6677d%8lv0+2t$hkjw=8emvaed(an118!y6a'

# List of callables that know how to import templates from various sources.


MIDDLEWARE = [
    # 'debug_toolbar.middleware.DebugToolbarMiddleware', "LUEGO HABILITAR - QUITA MUCHO RECURSOS"
    # 'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',

    'django_cprofile_middleware.middleware.ProfilerMiddleware',
    #    'django.middleware.cache.FetchFromCacheMiddleware',
]
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.SHA1PasswordHasher'
]
CP_PROFILE_DIR = '/var/lib/django/archivopstats/archivorepoakad/'
DJANGO_CPROFILE_MIDDLEWARE_REQUIRE_STAFF = False
ROOT_URLCONF = 'urls'

# TEMPLATE_DIRS = (
#     # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
#     # Always use forward slashes, even on Windows.
#     # Don't forget to use absolute paths, not relative paths.
#     os.path.join(SITE_ROOT, 'templates'),
# )

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(SITE_ROOT, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'debug': DEBUG,
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    # 'django_extensions',
    # Uncomment the next line to enable admin documentation:
    'django.contrib.admin',
    # 'django.contrib.admindocs',
    'sga',
    'med',
    'bib',
    'ext',
    'socioecon',
    'clinicaestetica',
    # 'debug_toolbar', "LUEGO HABILITAR - QUITA MUCHO RECURSOS"
    'moodle',
    'firmaec',
    'documental'
)
INTERNAL_IPS = [
    # ...
    "127.0.0.1",
    "*",
    "190.15.134.142"
    # ...
]
# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# CONFIGURACION DEL THIRD PARTY RUNJASPERREPORTS
# JR_RUN = os.path.join(SITE_ROOT, 'thirdparty', 'lib')
# JR_JAVA_COMMAND = 'java'
JR_RUN = os.path.join(SITE_ROOT, 'thirdparty', 'jasperstarter', '3.6.2', 'lib')
JR_JAVA_COMMAND = os.path.join(SITE_ROOT, 'thirdparty', 'jasperstarter', '3.6.2', 'java', 'jdk1.8.0_202', 'bin', 'java.exe')

JR_REPORTS_FOLDER = os.path.join(SITE_ROOT, 'media', 'reports')
JR_USEROUTPUT_FOLDER = os.path.join(SITE_ROOT, 'media', 'documentos', 'userreports')
JR_DB_TYPE = 'postgresql'

EMAIL_ACTIVE = False  # para activar el envio de solicitudes o incidencias automaticas a Secretaria o Sistemas
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'sgaitb@itb.edu.ec'
EMAIL_HOST_PASSWORD = 'sgaitb2013$'
EMAIL_USE_TLS = True
# EMAIL_HOST_USER = 'info@oksoftwr.com'
# EMAIL_HOST_PASSWORD = 'magic.number.82'

# CONFIGURACIONES ESPECIFICAS DE INSTITUTO
CLASES_HORARIO_ESTRICTO = True  # Horario estricto de apertura/cierre de clases
CLASES_APERTURA_ANTES = 15  # Minutos de apertura antes de inicio
CLASES_APERTURA_DESPUES = 15  # Minutos de apertura despues de inicio
CLASES_CIERRE_ANTES = 0  # Minutos de cierre antes de terminacion
CLASES_SEGUN_CRONOGRAMA = True  # Horario donde solo aparecen las materias segun cronograma

# PARA EL CONTROL DE ALUMNOS (LLENAR DATOS PERSONALES Y QUE HAYA PAGADO MATRICULA)
PAGO_ESTRICTO = True  # Pago estricto, no permite acciones de asistencia y evaluaciones si no se ha pagado la matricula.
DATOS_ESTRICTO = False  # Datos de Cuenta de alumnos, no permite acciones de asistencia y evaluacion si no ha llenado los datos personales
FICHA_MEDICA_ESTRICTA = True  # Datos de Ficha Medica del Alumno, aviso en clases para los docentes en caso de q el estudiante no ha llenado su ficha medica

# TIPOS DE ARCHIVOS / SYLLABUS O DEBER
ARCHIVO_TIPO_SYLLABUS = 1
ARCHIVO_TIPO_DEBERES = 2
ARCHIVO_TIPO_GENERAL = 6

# TIPOS Y PARAMETROS DE NOTAS ESPECIFICAS DEL INSTITUTO
NOTA_TIPO_N1 = 1
NOTA_TIPO_N2 = 2
NOTA_TIPO_NO = 3

PARAMETROS_NOTA1 = 'TAREAS, INVESTIGACIONES Y TRABAJOS EXTRACLASES [15%]'
PARAMETROS_NOTA2 = 'LECCIONES ORALES, ESCRITAS, DEBATES Y FOROS [15%]'
PARAMETROS_NOTA3 = 'LABORATORIOS, PRACTICAS, TALLERES Y EXPOSICIONES [20%]'
PARAMETROS_NOTA4 = 'DESARROLLO DE LOS VALORES HUMANOS [10%]'
PARAMETROS_NOTA5 = 'EXAMEN [40%]'

NOTA_ESTADO_APROBADO = 1
NOTA_ESTADO_REPROBADO = 2
NOTA_ESTADO_EN_CURSO = 3
NOTA_ESTADO_SUPLETORIO = 4

PORCIENTO_NOTA1 = 15
PORCIENTO_NOTA2 = 15
PORCIENTO_NOTA3 = 15
PORCIENTO_NOTA4 = 20
PORCIENTO_NOTA5 = 35
PORCIENTO_RECUPERACION = 100

NOTA_PARA_APROBAR = 70  # Valor Limite Minimo para Aprobar una Materia
NOTA_PARA_SUPLET = 40  # Valor Limite Minimo para poder ir a Supletorio
ASIST_PARA_APROBAR = 75  # Valor Limite Minimo de Asistencias por Materia para Pasar de Nivel
ASIST_PARA_SEGUIR = 60  # Valor Limite Minimo de Asistencias por Materia pero no pasa de Nivel (entre 60 y 69 va a Supletorio)
SUMA_PARA_APROBAR = 21
VALIDAR_ASISTENCIAS = True
NOTA_MAXIMA = 100

EVAL_MAL = 1
EVAL_REGULAR = 2
EVAL_BIEN = 3
EVAL_MUYBIEN = 4
EVAL_EXCELENTE = 5

MODULO_FINANZAS_ACTIVO = True
GENERAR_RUBROS_PAGO = True
GENERAR_RUBRO_INSCRIPCION = True
GENERAR_RUBRO_INSCRIPCION_MARGEN_DIAS = 0
GENERAR_RUBRO_DERECHO = False

ACEPTA_PAGO_EFECTIVO = True
ACEPTA_PAGO_CHEQUE = True
ACEPTA_PAGO_TARJETA = True
ACEPTA_PAGO_DEPOSITO = True
ACEPTA_PAGO_TRANSFERENCIA = True

FORMA_PAGO_EFECTIVO = 1
FORMA_PAGO_CHEQUE = 2
FORMA_PAGO_TARJETA = 4
FORMA_PAGO_DEPOSITO = 5
FORMA_PAGO_TRANSFERENCIA = 6
FORMA_PAGO_NOTA_CREDITO = 7
FORMA_PAGO_RECIBOCAJAINSTITUCION = 8
FORMA_PAGO_TARJETA_DEB = 9
FORMA_PAGO_ELECTRONICO = 10
FORMA_PAGO_WESTER = 11
FORMA_PAGO_PICHINCHA = 12
FORMA_PAGO_PACIFICO = 13
FORMA_PAGO_FACILITO = 14
FORMA_PAGO_REFERIDO = 15
FORMA_PAGO_PAGOONLINE = 16
FORMA_PAGO_RETENCION = 17
FORMA_PAGO_CHEQUE_POSTFECHADO = 18

# TIPOS OTROS RUBROS
TIPO_INSCRIPCION_RUBRO = 1
TIPO_CUOTA_RUBRO = 2
TIPO_OTRO_RUBRO = 4
TIPO_MORA_RUBRO = 5
TIPO_CONGRESO_RUBRO = 7
TIPO_ARRASTRE_RUBRO = 8
TIPO_CURSOS_RUBRO = 9
TIPO_CONVALIDACION_RUBRO = 10
TIPO_DERECHOEXAMEN_RUBRO = 6
VALOR_DERECHOEXAMEN_RUBRO = 0
TIPO_RETENCION_IVA = 4
TIPO_RETENCION_FUENTE = 3

# Identificar el tipo de especie valorada para Retirar de Matriculas
UTILIZA_ESPECIE_PARA_RETIRAR = True
TIPO_ESPECIE_RETIRO_MATRICULA = 21

SEXO_FEMENINO = 1
SEXO_MASCULINO = 2

# Grupo de Usuarios que Pueden Gestionar Periodos
MANAGER_PERIODO_GROUP_ID = 27

# Define si se utilizan grupos de alumnos
UTILIZA_GRUPOS_ALUMNOS = True

# Define si usa o no Asignaturas Rectoras de un nivel
REGISTRO_HISTORIA_NOTAS = True

# Define si utiliza nivel 0 (propedeutico)
UTILIZA_NIVEL0_PROPEDEUTICO = True
TIPO_PERIODO_PROPEDEUTICO = 1
TIPO_PERIODO_REGULAR = 2
NIVEL_MALLA_CERO = 9
NIVEL_MALLA_UNO = 1
NIVEL_SEMINARIO = 13
NIVEL_GRADUACION = 10

# Define si usa o no Asignaturas Rectoras de un nivel
UTILIZA_ASIGNATURA_RECTORA = False

REPORTE_CERTIFICADO_INSCRIPCION = 1
REPORTE_CRONOGRAMA_MATERIAS = 17
REPORTE_CRONOGRAMA_PROFESOR = 16
REPORTE_ALUMNOS_INSCRITOS = 5
REPORTE_ACTA_NOTAS = 14

CALCULA_FECHA_FIN_MATERIA = True

EVALUACION_IAVQ = 1
EVALUACION_ITB = 2
EVALUACION_ITS = 3
EVALUACION_TES = 4
EVALUACION_IGAD = 5
EVALUACION_CASADE = 6
MODELO_EVALUACION = EVALUACION_ITB

# Tipo de Ayuda Financiera para crear Notas de Credito en lugar de aplicar porcientos de Beca en Matriculas
TIPO_AYUDA_FINANCIERA = 2

# Tipo de Beca para aplicar el 100% de beca o sea el alumno se matricula y pasa el nivel gratis
TIPO_BECA_SENESCYT = 4

SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Coordinaciones Academicas de Carreras
UTILIZA_COORDINACIONES = True
COORDINACION_UASSS = 1
COORDINACION_SISTEMAS = 2
COORDINACION_UACED = 3

# Para los Roles de Pago a Docentes
COEFICIENTE_PORCIENTO_IESS = 0.0945
COEFICIENTE_RETENCION = 0.08
COEFICIENTE_IVA = 0.12
COEFICIENTE_IMPUESTO_RENTA = 0.10
COEFICIENTE_ANTICIPO_QUINCENA = 0.40  # 40% del salario base
DIAS_TRABAJO = 30

# Para envio automatico de correo al Dobe cuando se apliquen Becas
TIPO_INCIDENCIA_DOBE = 9
TIPO_INCIDENCIA_SECRETARIA = 3

# Si usa o no la Ficha Medica y el Dpto Medico
UTILIZA_FICHA_MEDICA = True

# Si usa Matricula Extraordinaria con Recargos Financieros
UTILIZA_MATRICULA_RECARGO = True

# Si se permite que desde el modulo de Clases y Evaluaciones se puedan cambiar en las notas de los docentes
PUEDE_CAMBIAR_CALIFICACIONES = False

# Si usa la Biblioteca Virtual
UTILIZA_MODULO_BIBLIOTECA = True

# Validar si tiene deuda, los docentes no puedan pasar Calificaciones
VALIDA_DEUDA_EVALUACIONES = False

# centro externo
RUBRO_TIPO_OTRO_INSCRIPCION = 0
RUBRO_TIPO_OTRO_MODULO_EXTERNO = 0
RUBRO_TIPO_OTRO_MODULO_INTERNO = 0
RUBRO_TIPO_OTRO_LIBRO = 0
RUBRO_TIPO_OTRO_CD = 0

UTILIZA_MODULO_ENCUESTAS = True

ALLOWED_IPS_FOR_INHOUSE = ['*']

CREDITOS_NIVEL_TES = 0

MODELO_IMPRESION_NUEVO = False
GRUPO_USUARIOS_IMPRESION = 1
DIA_PAGO_PLAN12 = 5

# CORREO INSTITUCIONAL PARA EL SNIESE
USA_CORREO_INSTITUCIONAL = True
CORREO_INSTITUCIONAL = '@itb.edu.ec'

# INSTRUMENTOS DE EVALUACION
INSTRUMENTO_PROFESOR_ID = 4
INSTRUMENTO_ALUMNO_ID = 5
INSTRUMENTO_COORDINADOR_ID = 6

# TIPO OBSERVACION ESTUDIANTE CRITICA
TIPO_OBSERVACION_CRITICA_ID = 2

# PARA CONTROL DE ABRIR CLASES SOLO DESDE EL AULA
ABRIR_CLASES_DESDE_AULA = False

# PARA SABER QUE INSTITUCION ES Y PONER EL LOG CORRESPONDIENTE
INSTITUTO_ITB = 1
INSTITUTO_ITF = 2
INSTITUTO_BUCK = 3
UNIVERSIDAD_CIU = 4
INSTITUCION = INSTITUTO_ITB

# PERSONA CUBRE GASTOS - CASO DE OTROS GUARDAR EL ID PARA OPCION DE ESPECIFICAR
PERSONA_CUBRE_GASTOS_OTROS_ID = 7

# VALIDAR QUE NO PUEDA USAR EL SISTEMA UN ESTUDIANTE SI TIENE DEUDAS VENCIDAS
VALIDAR_ENTRADA_SISTEMA_CON_DEUDA = True

# VARIABLE PARA SI USA O NO FICHA SOCIOECONOMICA
UTILIZA_FICHA_SOCIOECONOMICA = True

# CARRERAS EXCLUIDAS DE LA ESTADISTICA SOCIOECONOMICO
CARRERAS_ID_EXCLUIDAS_INEC = [7, 8, 9, 11, 12, 13, 14, 15, 16, 17, 19, 18, 20]

# VARIABLE PARA SABER SI TIENE ENTRADA DE PADRES O NO
TIENE_INGRESO_PADRES = True

# USA MODULO DE JUSTIFICACION DE AUSENCIAS
USA_MODULO_JUSTIFICACION_AUSENCIAS = True

# FACTURACION CON IVA
FACTURACION_CON_IVA = False
COEFICIENTE_CALCULO_BASE_IMPONIBLE = 1.12

# FACTURACION EN CAJA CON FPDF, SIN PROGRAMA EN JAVA
UTILIZA_FACTURACION_CON_FPDF = False

# variable para identificar a los estudiantes prospensos a desertar
NUMERO_POSIBLE_DESERTOR = 2

# variable para profesores de practica
PROFE_PRACT_CONDUCCION = 2

# VISITABOX DENTISTA
COD_TIPOVISITABOX = 1

# DIA MAXIMO DE ANULACION DE FACTURA
DIA_MAX_ANULA = 12

# VALORES PARA IMPRESION EN FPDF
# MOZILLA FIREFOX Y 120x144 (EPSON FX-890)
POSICIONES_IMPRESION = {
    'orientacion': "PORTRAIT",
    'fuente': ['courier', 11],
    'numerofactura': [150, 20],
    'dia': [146, 35],
    'mes': [156, 35],
    'anno': [167, 35],
    'ruccliente': [21, 39],
    'nombrecliente': [21, 45],
    'direccioncliente': [21, 51, 23, 47, 23, 70],
    'telefonocliente': [158, 51],
    'rubroalumno': [21, 67],
    'rubrotipo': [21, 71],
    'rubrovalor': [167, 71],
    'enletras': [21, 143],
    'subtotal': [171, 150],
    'iva': [171, 161],
    'total': [171, 171],

}

# CUPO MAXIMO DE ALUMNOS BOX
CUPO_MAXIMO = 200
# visita box medico
COD_ODONTOLOGICO = 5

# CODIGO DE ASIGNATURA PRACTICA
ASIGNATURA_PRACTICA_CONDUCCION = 9

# TEST_VOCACIONAL VARIABLE
TEST_VOCACIONAL = 4

# INGRESO_SISTEMA_TEST
TEST_INGRESO_SISTEMA = True

# RUBRO PARA CURSOS CETICS
RUBRO_TIPO_CURSOS = 6

# ASIGNATURAS GRADO CONDUCCION
ASIGNATURA_EDU_VIAL = 14
ASIGNATURA_LEY_TRANSPORTE = 15

# AMBIENTE FACTURACION
AMBIENTE_FACTURACION = 2
EMISION_ELECTRONICA = 1
CODIGO_NUMERICO_ELEC = '12345678'
IDENTIFICACION_COMPRADOR = '05'
CODIGO_INFORMACION_INSTITUTO = 1
IVA_FACTU_ELECTRONICA = '12.00'
ATS_PATH = os.path.join(MEDIA_ROOT, 'comprobantes')
DIR_COMPRO = '/media/comprobantes/'
FACTURACION_ELECTRONICA = True

MATERIA_PRACTICA_CONDUCCION = 327
AMBIENTE_DESCRIPCION = 'PRODUCCION'
TIPO_NC_ANULACION = 1
TIPO_NC_DEVOLUCION = 2
ASIGNATURA_PRACTICAS_CONDU = 17
INCIDENCIA_FACT = 16
AUTO_LOGOUT_DELAY = 10
SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'
URL_PRE_INSCRIPCION = "https://www.itb.edu.ec/public/docs/datauserregister.txt"
RUTA_PRE_INSCRIPCION = "/var/lib/django/repoakad/media/reportes/dato.txt"

NO_TUTORIA = 10
# VARIABLE PARA VALIDAR QUE NO PUEDA ABRIR CLASE SI TIENE MATERIAS PENDIENTES DE CERRAR
VALIDA_MATERIAS = False
# VALIDA QUE NO DEBA PARA LA MATRICULACION AUTOMATICA
VALIDA_DEUDA_MATRICULA = True
# VALIDA QUE NO TENGA MATERIAS REPROBADAS O PENDIENTES PARA LA MATRICULACION AUT
VALIDA_PASE_NIVEL = True

# ADMISION VARIABLE
ATENCIONCLI = 99

# VARIABLE EVIDENCIA BAJA MEDICAMENTO
INCIDENCIA_BAJAMEDI = 24
INCIDENCIA_SUSPENSION = 25

TESIS_URL = 'https://sga.itb.edu.ec'
VALIDA_PROV_CANTON_RESI = True

# VARIABLES DE SOLICITUD BECA
PUNTAJE_BECA_DISCAPA = 80
PUNTAJE_BECA_NORMAL = 90
TIPO_ESPECIE_BECA = 1

# VARIABLES DE FICHABECA
ID_VIVIPROPIA_BECA = 1
ID_VIVIARREN_BECA = 2
ID_VIVICEDIDA_BECA = 3
ID_TIPVIVOTRO_BECA = 7
ID_DATOECONOTRO_BECA = 7
EXCLUYE_NIVEL = [6, 10, 13]
TIPO_INCIDENCIA_VINCULACION = 27

# ID DE GRUPO DE BOX
GRUPO_BOX_ID = [10, 23, 44, 45, 59, 58, 84]
EXCLUYE_MAT_UACED = [2, 3, 6]
VALOR_PERMISO_CONDU = 10

TIPO_ATENCION_BOX_EST = 1
TIPO_ATENCION_BOX_COMUN = 2

VALIDA_CLAVE_CALIFICACION = False
INCIDENCIA_SEGUIMIENTO_RUBRO = 14
INCIDENCIA_APERTURA_CLASE = 15
TIPO_INCIDENCIA_INGLES = 29
CORREO_JEFE_ASUNTO_ESTUDIANTIL = 'mcaicedo@bolivariano.edu.ec'
ID_DEPARTAMENTO_ASUNTO_ESTUDIANT = [27, 4, 14, 19, 58, 56, 1]
TIPOSEGMENTO_PRACT = 2
DESCUENTO_REFERIDO = 15
CAMPANA_REFERIDOS = True

NOTA_PARA_EXAMEN_CONDUCCION = 12
NUMERO_PREGUNTA = 40
NOMBRE_INSTITUCION_EXAMEN = 'Instituto Superior Tecnologico Bolivariano de Tecnologia'
SEGUIMIENTO_SYLLABUS = False
FECHA_PAGO_TUTORIA = '2016-07-22'
RUBRO_TIPO_OTRO_LIBRO2 = 0
CANTIDAD_JUSTIFICACION_ESPECIE = 5
HORAS_VINCULACION = 160
HORAS_PRACTICA = 240
ASIG_PRATICA = 531
ASIG_VINCULACION = 513
INCIDENCIA_PRAC_VINC = 36
ARCHIVO_TIPO_PLANCLASE = 0
ARCHIVO_TIPO_MATERIALAPOYO = 0
UTILIZA_MENSAJE_INICIO = True
OPC_MENSAJE = "VIDEO"

ASIGNATURA_EXAMEN_GRADO_CONDU = [878, 511, 939, 909, 960, 605, 782, 749, 713, 650, 676, 875, 1029, 1063, 1261, 1097]
VALIDA_IP_CAJA = False
CONSUMIDOR_FINAL = 23498
MARGEN_GANANCIA = 0
VALIDA_ABRIR_CLASES = True
EXAMEN_PRACTI_COMPLEX = 70
EXAMEN_TEORI_COMPLEX = 70
EXAMEN_PRACTIPORC_COMPLEX = 60
EXAMEN_TEORIPORC_COMPLEX = 40
CANTIDAD_ASIGNATURAS = 0
DOCENTE_POR_DEFINIR = 387
VALIDA_MATERIA_APROBADA = False
MAXIMO_HORAS_CLASE = 0
VALIDA_MAXIMO_HORAS = False
TIPO_INCIDENCIA_MAT_APROBADA = 38
VALIDAR_PAGO_RUBRO = True
VALIDAR_ASISTENCIAS_EXAMEN = True
FORMA_PAGO_WESTER = 11
TIPO_INCIDENCIA_ABSENTISMO = 28
TIPO_RUBRO_SOLICITUD = 16
ANIO_PARA_INSCRIPCION = 15
DIAS_ESPECIE = 30
ESPECIE_CAMBIO_PROGRAMACION = 10
VALIDA_PRECEDENCIA = True
TIPO_EXAMEN_COMPLEXIVO = 2
CULMINACION_ESTUDIOS = 1
VALOR_VINCULACION = 10
URL_WEBSERVICE_FIRMA = 'http://10.10.9.53:8080/facturacionelectronica/firmarelectronica?WSDL'
FECHA_ELECT_FAC = '2015-01-01'
ANIO_TESIS = 2015
TIPO_DOCUMENTO = 3
ASIGNACION_TUTOR = 2
CAJA_FACILITO = 100
API_URL_ITB = "http://sga.itb.edu.ec/api"
ASIGNATURA_SEMINARIO = [511, 605, 650, 676, 713, 749]
ESPECIE_RETIRO_MATRICULA = 21
ESPECIE_JUSTIFICA_FALTA = 14
ESPECIE_JUSTIFICA_FALTA_AU = 38
ADMISION_GROUP_ID = 8
# EXAMEN EXTERNO
EXAMEN_EXTERNO_INGRESO = False
NUMERO_PREGUNTA_EXTERNO = 20
NOTA_PARA_EXAMEN_EXTERNO = 16
TIPO_AULA = 1

FECHA_CIERRE_SINACTA = '2018-08-01'
VERIFICA_ACTAENTREGA = False
TIPOSEGMENTO_TEORIA = 1
PROMEDIO_ASISTENCIAS_CONDU = 95

COORDINADOR_GROUP_ID = 0
ID_GRUPO_EXAMEN_CASADE = [0]
ENVIAR_CODIGO_CEL = False
VALIDA_DEUDA_EXAM_ASIST = False
ID_TIPO_ESPECIE_REG_NOTA = 39
CAJA_CONGRESO = 112
SERVICIOS_SPA = [22, 23]
ID_TIPO_SOLICITUD = 67
ASUNT_ESTUDIANTILES = [64, 65]
USER_CONGRESO = 58657
ID_CARRERA_RECUPERACION = 0

ID_TIPO_GENERAL = 3
ID_TIPO_FACIAL = 1
ID_TIPO_CORPORAL = 2
ID_TIPO_RUBRO_TRICO = 19
ID_TIPO_RUBRO_TRI_SESE = 20

CAJA_ONLINE = 113

ESPECIE_REINGRESO = 28

# Parametros carrera recuperacion puntos
SUMA_PARA_APROBAR_RECU = 0
ASIST_PARA_APROBAR_RECU = 0

NOTA1_RECU = 0
NOTA2_RECU = 0
NOTA3_RECU = 0
NOTA4_RECU = 0
EXAM_RECU = 0
PROMOCION_GYM = True

# Parametros por nuevo modelo de calificacion
NOTA_ESTADO_DERECHOEXAMEN = 5
DIAS_BLOQUEO_NOTAS = 0
MIN_APROBACION = 46
MAX_APROBACION = 65
MIN_RECUPERACION = 40
MAX_RECUPERACION = 45
MIN_EXAMEN = 1
MAX_EXAMEN = 35
MIN_EXAMENRECUPERACION = 70
ESPECIE_ASENTAMIENTO_NOTA = 45
ESPECIE_EXAMEN = 13
ESPECIE_RECUPERACION = 16
NOTIFICACION_CIERRE = 31

GESTION_DESCUENTO = 5
GESTION_INDIVIDUAL = 10
EJE_PRACTICA = 8

CAJA_PACIFICO = 153

NEW_PASSWORD = 'Bolivarian0'
ACTIVA_ADD_EDIT_AD = True

ESPECIE_MEJORAMIENTO = 47
MULTA24H = 1
MULTA48H = 2
MULTA4DIAS = 3
NOTIFICACION_MULTA4DIAS = 63
DIAS_BLOQUEO_EJECUTIVO = 0
DIAS_BLOQUEO_MATERIA = 4

MATERIA_PRAC_ENFERMERIA = [162, 552, 182, 183]
NOTA_NUEVA_ACTA_MIN_PRESEN = 80
NOTA_NUEVA_ACTA_MIN_ONLINE = 70
VALOR_COMISION_REFERIDO = 25
CAJA_REFERIDO = 118

PORCENTAJE_DESCUENTO = 10
INICIO_DIFERIR = (2020, 1, 1)
FIN_DIFERIR = (2020, 12, 31)
MESES_DIFERIR = 4
CANTIDAD_CUOTAS = 4
FECHA_DIFERIR = (2021, 2, 1)
FECHA_INCIO_DIFERIR = (2020, 1, 1)
HABILITA_APLICA_DESCUE = False
PORCENTAJE_DESC_CUOTAS = 20
CUOTAS_CANCELAR = 3
VALIDA_PROMOCION_EMERG = True

ABRIR_EXAMEN_DESDE_AULA = True
PUNTAJE_MIN_EXAMEN = 60
NUM_PREGUN_EXAMENPARC = 7
NUM_PREGUN_EXAMENPARCSUPLE = 5
LISTA_GRUPO_MUNICIPO = [1539, 1540, 1544, 1545, 1546, 1547, 1548, 1549, 1550, 1551, 1552]
PORCENTAJE_DESCUENTO15 = 15
ID_CARRERA_CONGRESO = 16
LLENAR_CAMPOS = True
CARRERAENFERMERIAMEDICA = 50
LISTA_TIPO_BECA = [1, 2]
ID_VENTA_EXTERNA2 = 146
ESPECIE_TRAMITES_VARIOS = 53
CAJA_PICHINCHA = 129
ASISTENTE_SECRETARIA = 34
ID_TIPO_ESTADO_BECA = [1, 2, 5]
ID_FUNDACION_CRISFE = 50
EXAMEN_CONVALIDACION = 79
TIPO_PAGOS_EXAMEN_DE_ADMISION = 13
TIPO_PAGOS_CURSO_DE_NIVELACION = 14
TIPO_ID_OTRO_RUBRO_EXAMEN_ADMISION = 20
TIPO_ID_OTRO_RUBRO_CURSO_NIVELACION = 21
EXCLUIR_TIPO_PAGO = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]

# /////////PRACTICAS PREPROFESIONALES
NIVELMALLA_INICIO_PRACTICA = 4
HORAS_MAX_LABORA = '06:30'
TIPO_ESPECIEVALO_PRACPRE = 81
TIPO_SOLIC__SECRET_PRACPRE = 82
ID_SOLIC__ONLINE = 3
TIPO_INCIDENCIA_PRACPRE = 68
URL_DEL_SISTEMA = 'http://localhost:8000/'
SOLICITUD_APLAZAMIEN_PRACT_ID = 81
VALIDA_ESCENARIO_PRACTICA = False
ID_REPORTE_CARTA_COMPROM = 1
ID_REPORTE_CARTA_ASIGNAC = 2
ID_REPORTE_CERTI_PRACTIC = 3
HORAS_MIN_PRACTICAS = 80
PUNTAJE_APRUEBA_PRACTICA = 3
# /////////////////
HABILITA_DESC_MATRI = False
DESCUENTO_MATRIC_PORCENT = 15
HABILITA_DESC_INSCRIPCION = False
DESCUENTO_INSCRIPCION = 25

ASIGNATURA_PRACTICAS_SM = 1200
ID_DEPARTAMENTO_PRACTICAS = 39

GRUPO_CAJEROS = 27
ASIGNATURA_INTRODUCCION = 570
TUTORES_GROUP_ID = 158
COSTO_PROFESIONALIZACION = 20
COSTO_COMPLEXIVO = 15
PROMOCION_REGALA_SONRISAS = 13
SEGMENTO_REFERIDO = 5
SEGMENTO_REFERIDO_ONLINE = 10
VENTANILLA_SECRETARIA = 15
TIPO_PAGOS_INGLES = 15
TIPO_ID_OTRO_RUBRO_INGLES = 23
ID_USUARIO_RUDY = 25858
ID_TIPOBECA = 18
ID_MOTIVO_BECA_MUNICIPIO = 108
ID_TIPO_BENEFICICO_BECA = 1

ID_GESTION_SECRETARIA = 6
ID_GESTION_ANALSIS = 3
ID_TIPO_SOLICITUD_BECA = 1
ID_TIPO_SOLICITUD_BECA_AYUDA = 2
INCIDENCIA_CAB = 71
ID_ASIGNATURA_PRACT = [940, 850, 651, 721, 908, 1061, 1009, 1062, 816, 1016]
COSTO_PROFESIONALIZACION_TRANSPORTE = 15
TIPO_RUBRO_CREDENCIAL = 25
RUBRO_PLAGIO = 21.50
WEBINAR_PATH = os.path.join(MEDIA_ROOT, 'webinars')
VALOR_HORA_MINIMO = 1
VALOR_HORA_MAXIMO = 10
ID_MOTIVO_BECA_TEC = 123
ID_CONVENIO_BECA_TECT = 29
COSTO_SEGMENTO_PRACTICA = 10
PORCENTAJE_DESCUENTO_CIERREAUTOMATICO = 50
COORDINACION_TRANSPORTE = 5

IP_SERVIDOR_API_DIRECTORY = 'http://10.10.10.4:4443'
INCIDENCIA_COBRANZAS = 62

ESPECIE_ASENTAMIENTOCONVENIO_SINVALOR = 88
ESPECIE_ASENTAMIENTOCONVENIO_CONVALOR = 89
BIBLIOTECA_PARAMETRIZADA = 20

HABILITA_NOTIFICACIONES = True

TIPO_RUBRO_MATERIALAPOYO = 31

ESPECIE_JUSTIFICACIONCONVENIO_CONVALOR = 90
ESPECIE_JUSTIFICACIONCONVENIO_SINVALOR = 91

ESPECIES_ASUNTOS_ESTUDIANTILES = [ESPECIE_ASENTAMIENTOCONVENIO_SINVALOR,
                                  ESPECIE_ASENTAMIENTOCONVENIO_CONVALOR,
                                  ESPECIE_JUSTIFICACIONCONVENIO_CONVALOR,
                                  ESPECIE_JUSTIFICACIONCONVENIO_SINVALOR]

ESPECIES_ASENTAMIENTO_NOTAS = [ESPECIE_ASENTAMIENTOCONVENIO_SINVALOR,
                               ESPECIE_ASENTAMIENTOCONVENIO_CONVALOR,
                               ID_TIPO_ESPECIE_REG_NOTA]

ESPECIES_JUSTIFICACION_FALTAS = [ESPECIE_JUSTIFICA_FALTA_AU,
                                 ESPECIE_JUSTIFICACIONCONVENIO_CONVALOR,
                                 ESPECIE_JUSTIFICACIONCONVENIO_SINVALOR]
ID_CARRRERA_NUEVA_BECA = [21, 4, 67, 23, 75, 48, 41, 65, 50, 76, 33]

ID_TEST_ENCUESTA_DESERCION = 5
ID_TIPO_ESPECIE_CONVENIO_PAGO = 1
VALOR_MATERIALAPOYO = 32
INCIDENCIA_CIERRENIVELFATV = 73
INCIDENCIA_CIERRENIVELFACES= 74
INCIDENCIA_CIERRENIVELFASS = 75
ID_AUDITOR_INTERNO=172
OTRODEPORTE=20
PRIMERNIVEL=0
ID_MOTIVO_BECA_NUEVOECUADOR=135

TIPO_OTRO_FRAUDE = 33
ID_TIPO_ESPECIE_FRAUDE_TARJETA = 93

TIPO_DOCENTE = 4
TIPO_ESTUDIANTE = 2
TIPO_ADMINISTRATIVO = 1
TIPO_OTROS = 6

HORAS_TELECLINICA = 16
TEST_EXCELENTE = 90
TEST_BUENO = 80
TEST_REGULAR = 70


# Detectar el sistema operativo
system = platform.system()

# Definir la ruta a Java según el sistema operativo
if system == 'Windows':
    JAVA_20_EXECUTABLE = os.path.join(SITE_ROOT, 'thirdparty', 'java', 'windows', 'jdk-20.0.2', 'bin', 'java.exe')
elif system == 'Linux':
    JAVA_20_EXECUTABLE = os.path.join(SITE_ROOT, 'thirdparty', 'java', 'linux', 'jdk-20.0.2', 'bin', 'java')
else:
    raise EnvironmentError(f"Unsupported OS: {system}")

JAR_FIRMA_EC = os.path.join(SITE_ROOT, "thirdparty", "FIRMA_EC.jar")

# Asegúrate de que la ruta sea válida
if not os.path.isfile(JAVA_20_EXECUTABLE):
    raise FileNotFoundError(f"Java executable not found: {JAVA_20_EXECUTABLE}")

if not os.path.isfile(JAR_FIRMA_EC):
    raise FileNotFoundError(f"Java executable not found: {JAR_FIRMA_EC}")

