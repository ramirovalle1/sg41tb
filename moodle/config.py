from django.apps import AppConfig


class MoodleConfig(AppConfig):
    name = 'moodle'
    verbose_name = 'Administrador de Moodle'


MY_ENDPOINT_MOODLE = "/webservice/rest/server.php"
MY_PRIFIX_MOODLE = 'mdl_'
MY_USE_AUTH = 'db' # Valor por defecto para "manual" //Auth plugins include manual, ldap, etc
MY_PASSWORD_DEFAULT = 'itb2024**'
MY_LANG = 'es'  # Valor por defecto para "es" //Language code such as "en", must exist on server