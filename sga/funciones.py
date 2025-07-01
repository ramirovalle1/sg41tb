# Embedded file name: ./funciones.py
import calendar
import unicodedata
from datetime import datetime, timedelta
from django.contrib.admin.models import LogEntry, ADDITION, DELETION, CHANGE
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.shortcuts import render
from django.template import RequestContext


class MiPaginador(Paginator):

    def __init__(self, object_list, per_page, orphans=0, allow_empty_first_page=True, rango=5):
        super(MiPaginador, self).__init__(object_list, per_page, orphans=orphans,
                                          allow_empty_first_page=allow_empty_first_page)
        self.rango = rango
        self.paginas = []
        self.primera_pagina = False
        self.ultima_pagina = False

    def rangos_paginado(self, pagina):
        left = pagina - self.rango
        right = pagina + self.rango
        if left < 1:
            left = 1
        if right > self.num_pages:
            right = self.num_pages
        self.paginas = range(left, right + 1)
        self.primera_pagina = True if left > 1 else False
        self.ultima_pagina = True if right < self.num_pages else False
        self.ellipsis_izquierda = left - 1
        self.ellipsis_derecha = right + 1


def proximafecha(fecha, periocidad):
    if periocidad == 1:
        return fecha + timedelta(days=1)
    if periocidad == 2:
        return fecha + timedelta(days=7)
    if periocidad == 3:
        day = fecha.day
        month = fecha.month
        year = fecha.year
        if month == 12:
            nextmonth = 1
            nextyear = year + 1
        else:
            nextmonth = month + 1
            nextyear = year
        if day >= 29:
            for i in range(29, 32):
                nuevafecha = fecha + timedelta(days=i)
                if nuevafecha.month == nextmonth:
                    return nuevafecha

        else:
            return datetime(nextyear, nextmonth, fecha.day)
    return fecha


def custom_render_to_response(template, data, request):
    if 'formerror' in request.GET:
        data['formerror'] = request.GET['formerror']
    return render(request, template, data)


def calculate_username(persona, variant=1):
    s = persona.nombres.lower().split(' ')
    while '' in s:
        s.remove('')

    if len(s) > 1:
        usernamevariant = s[0][0] + s[1][0] + persona.apellido1.lower()
    else:
        usernamevariant = s[0][0] + persona.apellido1.lower()
    usernamevariant = usernamevariant.replace(' ', '').replace(u'\xd1', 'n').replace(u'\xf1', 'n')
    if variant > 1:
        usernamevariant += str(variant)
    import psycopg2
    db = psycopg2.connect("host=10.10.9.45 dbname=sgaonline user=postgres password=Itb$2019")
    cursor = db.cursor()
    cursor.execute("select * from auth_user where username='" + str(usernamevariant) + "'")
    dato = cursor.fetchall()
    # names = [row[0] for row in cursor.fetchall()]
    db.close()
    if len(dato) > 0:
        return calculate_username(persona, variant + 1)
    db = psycopg2.connect("host=10.10.9.45 dbname=conduccion user=postgres password=Itb$2019")
    cursor = db.cursor()
    cursor.execute("select * from auth_user where username='" + str(usernamevariant) + "'")
    dato = cursor.fetchall()
    # names = [row[0] for row in cursor.fetchall()]
    db.close()
    if len(dato) > 0:
        return calculate_username(persona, variant + 1)
    db = psycopg2.connect("host=10.10.9.45 dbname=contable2 user=postgres password=Itb$2019")
    cursor = db.cursor()
    cursor.execute("select * from auth_user where username='" + str(usernamevariant) + "'")
    dato = cursor.fetchall()
    db.close()
    if len(dato) > 0:
        return calculate_username(persona, variant + 1)
    db = psycopg2.connect("host=10.10.9.45 dbname=educacontinua user=postgres password=Itb$2019")
    cursor = db.cursor()
    cursor.execute("select * from auth_user where username='" + str(usernamevariant) + "'")
    dato = cursor.fetchall()
    # names = [row[0] for row in cursor.fetchall()]
    db.close()
    if len(dato) > 0:
        return calculate_username(persona, variant + 1)
    if User.objects.filter(username=usernamevariant).count() == 0:
        return usernamevariant
    else:
        return calculate_username(persona, variant + 1)


def log(mensaje, request, accion):
    if accion == 'del':
        logaction = DELETION
    elif accion == 'add':
        logaction = ADDITION
    else:
        logaction = CHANGE
    LogEntry.objects.log_action(user_id=request.user.pk, content_type_id=None, object_id=None, object_repr='',
                                action_flag=logaction, change_message=str(mensaje))


def sumar_mes(fecha):
    year = fecha.year + (fecha.month // 12)
    month = fecha.month % 12 + 1
    dias_siguientes = calendar.monthrange(year, month)[1]

    nuevo_dia = min(fecha.day, dias_siguientes)

    if fecha.day == calendar.monthrange(fecha.year, fecha.month)[1]:
        nuevo_dia = dias_siguientes

    nueva_fecha = fecha.replace(year=year, month=month, day=nuevo_dia)
    return nueva_fecha


import subprocess
def is_mounted(path):
    result = subprocess.run(['mountpoint', '-q', path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.returncode == 0

def mount_directory():
    try:
        # Ejecutar el comando `mount -a` y capturar la salida estándar y de error
        command = ['sudo', '/usr/local/bin/mount_nsenter.sh']
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print("Comando ejecutado con exito")
        print("Salida:", result.stdout)

    except subprocess.CalledProcessError as e:
        print('Error al montar CalledProcessError  excep'+ str(e) +' OUTPUT '+str(e.stdout)+" CODIGO DE SALIDA:" +str(e.returncode) + ' ERROR '+str(e.stderr))

    except subprocess.SubprocessError as e:
        print('Error al montar SubprocessError  excep' + str(e) + 'error Error executing mount command')
    except Exception as e:
        print('Error al montar   excep' + str(e) + 'error Error executing mount command')

def two_decimals(num):
    return "{:.2f}".format(num)


def null_to_numeric(valor, decimales=None):
    if decimales:
        return round((valor if valor else 0), decimales)
    return valor if valor else 0


def null_to_decimal(valor, decimales=None):
    from django.db import connections
    if not valor is None:
        sql = """SELECT round(%s::numeric,%s)""" % (valor, decimales if decimales else 0)
        cursor = connections['default'].cursor()
        cursor.execute(sql)
        results = cursor.fetchone()
        return float(results[0])
    return valor if valor else 0


def logEntry(request, objetoTable, mensaje):
    from django.utils.encoding import force_str
    from .commonviews import ip_client_address
    client_address = ip_client_address(request)
    LogEntry.objects.log_action(
        user_id=request.user.pk,
        content_type_id=ContentType.objects.get_for_model(objetoTable).pk,
        object_id=objetoTable.id,
        object_repr=force_str(objetoTable),
        action_flag=DELETION,
        change_message=mensaje + '(' + client_address + ')')


# def calculo_modelo_evaluativo(eMateriaAsignada):
#     P1 = eMateriaAsignada.campo('P1')
#     N1 = eMateriaAsignada.campo('N1')
#     N2 = eMateriaAsignada.campo('N2')
#     EX1 = eMateriaAsignada.campo('EX1')
#     P2 = eMateriaAsignada.campo('P2')
#     N3 = eMateriaAsignada.campo('N3')
#     N4 = eMateriaAsignada.campo('N4')
#     EX2 = eMateriaAsignada.campo('EX2')
#     RE = eMateriaAsignada.campo('RE')
#     P1.valor = N1.valor + N2.valor + EX1.valor
#     P1.save()
#     P2.valor = N3.valor + N4.valor + EX2.valor
#     P2.save()
#     promedio = P1.valor + P2.valor
#     eMateriaAsignada.notafinal = null_to_decimal(promedio, 0)
#     if eMateriaAsignada.notafinal < 40:
#         RE.valor = 0
#         RE.save()
#     elif eMateriaAsignada.notafinal < 70:
#         if RE.valor > 0:
#             eMateriaAsignada.notafinal = null_to_decimal((RE.valor + float(eMateriaAsignada.notafinal)) / 2, 0)
#     else:
#         RE.valor = 0
#         RE.save()
#     if EX2.valor > 0 or RE.valor > 0:
#         if eMateriaAsignada.asistenciafinal < 70:
#             EX2.valor = 0
#             EX2.save()
#             RE.valor = 0
#             RE.save()
#             P2.valor = N3.valor + N4.valor + EX2.valor
#             P2.save()
#             promedio = P1.valor + P2.valor
#             eMateriaAsignada.notafinal = null_to_decimal(promedio, 0)
#     eMateriaAsignada.save()


def actualizar_nota_cuadro_calificacion(materiaasignada_id, campo, valor):
    from django.core.exceptions import ObjectDoesNotExist
    from sga.models import MateriaAsignada
    from settings import NOTA_ESTADO_EN_CURSO
    try:
        isSuccess = False
        message = "Ocurrio un error al guardar la calificación"
        data = {}
        try:
            eMateriaAsignada = MateriaAsignada.objects.get(pk=materiaasignada_id)
        except ObjectDoesNotExist:
            raise NameError(u"No se encontro materia del alumno asigando")
        if eMateriaAsignada.materia.cerrado:
            raise NameError("Materia se encuentra cerrada")
        eModeloEvaluativo = eMateriaAsignada.materia.modelo_evaluativo
        eDetalleModeloEvaluativo = eModeloEvaluativo.campo(campo)
        if type(valor) is str:
            valor = null_to_decimal(valor, eDetalleModeloEvaluativo.decimales)
        try:
            if not valor:
                valor = null_to_decimal(float(valor), eDetalleModeloEvaluativo.decimales)
            if valor >= eDetalleModeloEvaluativo.nota_maxima:
                valor = eDetalleModeloEvaluativo.nota_maxima
            elif valor <= eDetalleModeloEvaluativo.nota_minima:
                valor = eDetalleModeloEvaluativo.nota_minima
        except:
            valor = eDetalleModeloEvaluativo.nota_minima
        eEvaluacionGenerica = eMateriaAsignada.campo(campo)
        eEvaluacionGenerica.valor = valor
        eEvaluacionGenerica.save()
        # FUNCION DIMAMICA
        d = locals()
        exec(eModeloEvaluativo.logica, globals(), d)
        d['calculo_modelo_evaluativo'](eMateriaAsignada)
        # calculo_modelo_evaluativo(eMateriaAsignada)
        eMateriaAsignada.notafinal = null_to_decimal(eMateriaAsignada.notafinal, eModeloEvaluativo.nota_final_decimales)
        if eMateriaAsignada.notafinal > eModeloEvaluativo.nota_maxima:
            eMateriaAsignada.notafinal = eModeloEvaluativo.nota_maxima
        eMateriaAsignada.save()
        camposdependientes = []
        encurso = True
        for eDetalleModeloEvaluativo in eModeloEvaluativo.campos():
            if eDetalleModeloEvaluativo.es_dependiente:
                camposdependientes.append((eDetalleModeloEvaluativo.htmlid(),
                                           eMateriaAsignada.valor_nombre_campo(eDetalleModeloEvaluativo.nombre),
                                           eDetalleModeloEvaluativo.decimales))
            if eDetalleModeloEvaluativo.puede_actualizar_estado and eMateriaAsignada.valor_nombre_campo(
                    eDetalleModeloEvaluativo.nombre) > 0:
                encurso = False
        if not encurso:
            eMateriaAsignada.actualiza_estado()
        else:
            eMateriaAsignada.estado_id = NOTA_ESTADO_EN_CURSO
            eMateriaAsignada.save()
        isSuccess = True
        message = None
        data['dependientes'] = camposdependientes
        campo = eMateriaAsignada.campo(campo)
        data['valor'] = campo.valor
        data['nota_final'] = eMateriaAsignada.notafinal
        data['estado_display'] = eMateriaAsignada.estado.nombre.lower().capitalize()
        data['estado_id'] = eMateriaAsignada.estado_id
    except Exception as ex:
        isSuccess = False
        message = f"{ex.__str__()}"
    return {'isSuccess': isSuccess, 'message': message, 'data': data}


def remover_caracteres_especiales_unicode(cadena):
    normalized = unicodedata.normalize('NFD', cadena)
    return ''.join(
        c for c in normalized
        if unicodedata.category(c) != 'Mn'
    ).encode('ascii', 'ignore').decode('ascii')

def generar_nombre(nombre, original):
    ext = ""
    if original.find(".") > 0:
        ext = original[original.rfind("."):]
    fecha = datetime.now().date()
    hora = datetime.now().time()
    return nombre + fecha.year.__str__() + fecha.month.__str__() + fecha.day.__str__() + hora.hour.__str__() + hora.minute.__str__() + hora.second.__str__() + ext.lower()