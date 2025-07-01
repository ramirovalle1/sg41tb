from datetime import datetime, timedelta, date
import json
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from decorators import secure_module
from settings import UTILIZA_COORDINACIONES, TIPO_CUOTA_RUBRO, TIPO_INSCRIPCION_RUBRO, TIPO_OTRO_RUBRO, TIPO_MORA_RUBRO, TIPO_CONGRESO_RUBRO, TIPO_ARRASTRE_RUBRO, TIPO_CURSOS_RUBRO, TIPO_CONVALIDACION_RUBRO, TIPO_DERECHOEXAMEN_RUBRO
from sga.commonviews import addUserData, total_efectivo_dia, cantidad_facturas_dia, cantidad_cheques_dia, total_cheque_dia, cantidad_tarjetas_dia, total_tarjeta_dia, cantidad_depositos_dia, total_deposito_dia, cantidad_transferencias_dia, total_transferencia_dia, cantidad_notasdecredito_dia, total_notadecredito_dia, total_dia, total_matriculados, cantidad_facturas_total_fechas, total_pagos_rango_fechas, facturas_total_fecha, pagos_total_fecha, cantidad_total_deudores, valor_total_deudores, valor_total_porcobrar, cantidad_total_porcobrar, valor_total_creditos, cantidad_total_creditos, total_matriculados_hombres, total_matriculados_mujeres, cantidad_matriculados_discapacidad, cantidad_matriculados_beca, matriculados_menor_30, matriculados_31_40, matriculados_41_50, matriculados_51_60, matriculados_mayor_61, cantidad_total_deudores_retirados, cantidad_total_deudores_inactivos, cantidad_total_deudores_activos, valor_total_deudores_retirados, valor_total_deudores_inactivos, valor_total_deudores_activos, cantidad_total_creditos_retirados, valor_total_creditos_activos, cantidad_total_creditos_inactivos, valor_total_creditos_inactivos, valor_total_creditos_retirados, cantidad_total_creditos_activos, valor_total_porcobrar_retirados, valor_total_porcobrar_inactivos, valor_total_porcobrar_activos, cantidad_total_porcobrar_retirados, cantidad_total_porcobrar_inactivos, cantidad_total_porcobrar_activos, cantidad_recibocaja_dia, total_recibocaja_dia, cantidad_retencion_dia, total_retencion_dia, total_matriculados_mujeresfil, total_matriculados_hombresfil,  total_matriculadosfilcanton, total_matriculadosprovinnull, total_matriculadoscantonnull,total_matriculados_edades,total_matriculados_becasdiscapacidad
from sga.models import SesionCaja, Coordinacion, Carrera, Inscripcion, Provincia, Canton, Sexo, Pago,InscripcionGrupo,Grupo,total_matriculadosfil, total_matriculadosfilnullprovin, total_matriculadosfilprovinporcent, total_matriculadosfilcantonporcent, total_matriculadosprovinporcent, total_matriculadoscantonporcent


def convertir_fecha(s):
    return datetime(int(s[6:10]), int(s[3:5]), int(s[0:2])).date()

# COORDINACIONES ------------- COORDINACIONES ----------COORDINACIONES

# PAGO DE RUBROS COMUNES: Matricula, Cuota, Nota Debito, Especies, Materia
def total_depagos_rubrosinscripciones_rango_fechas(coordinacion, inicio, fin):
    return Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__inscripcion__carrera__in=coordinacion.carrera.all(), rubro__rubroinscripcion__isnull=False).aggregate(Sum('valor'))['valor__sum'] if Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__inscripcion__carrera__in=coordinacion.carrera.all(), rubro__rubroinscripcion__isnull=False).exists() else 0

def total_depagos_rubrosmatriculas_rango_fechas(coordinacion, inicio, fin):
    return Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__inscripcion__carrera__in=coordinacion.carrera.all(), rubro__rubromatricula__isnull=False).aggregate(Sum('valor'))['valor__sum'] if Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__inscripcion__carrera__in=coordinacion.carrera.all(), rubro__rubromatricula__isnull=False).exists() else 0

def total_depagos_rubrosespecies_rango_fechas(coordinacion, inicio, fin):
    return Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__inscripcion__carrera__in=coordinacion.carrera.all(), rubro__rubroespecievalorada__isnull=False).aggregate(Sum('valor'))['valor__sum'] if Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__inscripcion__carrera__in=coordinacion.carrera.all(), rubro__rubroespecievalorada__isnull=False).exists() else 0

def total_depagos_rubroscuotas_rango_fechas(coordinacion, inicio, fin):
    return Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__inscripcion__carrera__in=coordinacion.carrera.all(), rubro__rubrocuota__isnull=False).aggregate(Sum('valor'))['valor__sum'] if Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__inscripcion__carrera__in=coordinacion.carrera.all(), rubro__rubrocuota__isnull=False).exists() else 0

def total_depagos_rubrosnotasdebito_rango_fechas(coordinacion, inicio, fin):
    return Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__inscripcion__carrera__in=coordinacion.carrera.all(), rubro__rubronotadebito__isnull=False).aggregate(Sum('valor'))['valor__sum'] if Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__inscripcion__carrera__in=coordinacion.carrera.all(), rubro__rubronotadebito__isnull=False).exists() else 0

def total_depagos_rubrosmaterias_rango_fechas(coordinacion, inicio, fin):
    return Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__inscripcion__carrera__in=coordinacion.carrera.all(), rubro__rubromateria__isnull=False).aggregate(Sum('valor'))['valor__sum'] if Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__inscripcion__carrera__in=coordinacion.carrera.all(), rubro__rubromateria__isnull=False).exists() else 0

# PAGOS DE RUBROS DE TIPO OTRO
def total_depagos_rubrosotrosinscripciones_rango_fechas(coordinacion, inicio, fin):
    return Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__inscripcion__carrera__in=coordinacion.carrera.all(), rubro__rubrootro__isnull=False, rubro__rubrootro__tipo__id=TIPO_INSCRIPCION_RUBRO).aggregate(Sum('valor'))['valor__sum'] if Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__inscripcion__carrera__in=coordinacion.carrera.all(), rubro__rubrootro__isnull=False, rubro__rubrootro__tipo__id=TIPO_INSCRIPCION_RUBRO).exists() else 0

def total_depagos_rubrosotroscuotas_rango_fechas(coordinacion, inicio, fin):
    return Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__inscripcion__carrera__in=coordinacion.carrera.all(), rubro__rubrootro__isnull=False, rubro__rubrootro__tipo__id=TIPO_CUOTA_RUBRO).aggregate(Sum('valor'))['valor__sum'] if Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__inscripcion__carrera__in=coordinacion.carrera.all(), rubro__rubrootro__isnull=False, rubro__rubrootro__tipo__id=TIPO_CUOTA_RUBRO).exists() else 0

def total_depagos_rubrosotrosmoras_rango_fechas(coordinacion, inicio, fin):
    return Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__inscripcion__carrera__in=coordinacion.carrera.all(), rubro__rubrootro__isnull=False, rubro__rubrootro__tipo__id=TIPO_MORA_RUBRO).aggregate(Sum('valor'))['valor__sum'] if Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__inscripcion__carrera__in=coordinacion.carrera.all(), rubro__rubrootro__isnull=False, rubro__rubrootro__tipo__id=TIPO_MORA_RUBRO).exists() else 0

def total_depagos_rubrosotroscongresos_rango_fechas(coordinacion, inicio, fin):
    return Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__inscripcion__carrera__in=coordinacion.carrera.all(), rubro__rubrootro__isnull=False, rubro__rubrootro__tipo__id=TIPO_CONGRESO_RUBRO).aggregate(Sum('valor'))['valor__sum'] if Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__inscripcion__carrera__in=coordinacion.carrera.all(), rubro__rubrootro__isnull=False, rubro__rubrootro__tipo__id=TIPO_CONGRESO_RUBRO).exists() else 0

def total_depagos_rubrosotrosarrastres_rango_fechas(coordinacion, inicio, fin):
    return Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__inscripcion__carrera__in=coordinacion.carrera.all(), rubro__rubrootro__isnull=False, rubro__rubrootro__tipo__id=TIPO_ARRASTRE_RUBRO).aggregate(Sum('valor'))['valor__sum'] if Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__inscripcion__carrera__in=coordinacion.carrera.all(), rubro__rubrootro__isnull=False, rubro__rubrootro__tipo__id=TIPO_ARRASTRE_RUBRO).exists() else 0

def total_depagos_rubrosotroscursos_rango_fechas(coordinacion, inicio, fin):
    return Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__inscripcion__carrera__in=coordinacion.carrera.all(), rubro__rubrootro__isnull=False, rubro__rubrootro__tipo__id=TIPO_CURSOS_RUBRO).aggregate(Sum('valor'))['valor__sum'] if Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__inscripcion__carrera__in=coordinacion.carrera.all(), rubro__rubrootro__isnull=False, rubro__rubrootro__tipo__id=TIPO_CURSOS_RUBRO).exists() else 0

def total_depagos_rubrosotrosotros_rango_fechas(coordinacion, inicio, fin):
    return Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__inscripcion__carrera__in=coordinacion.carrera.all(), rubro__rubrootro__isnull=False, rubro__rubrootro__tipo__id=TIPO_OTRO_RUBRO).aggregate(Sum('valor'))['valor__sum'] if Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__inscripcion__carrera__in=coordinacion.carrera.all(), rubro__rubrootro__isnull=False, rubro__rubrootro__tipo__id=TIPO_OTRO_RUBRO).exists() else 0

# Total Pagos de Todos los Tipos de rubros Comunes u Otros de la Coordinacion
def total_depagos_rubros_rango_fechas(coordinacion, inicio, fin):
    return Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__inscripcion__carrera__in=coordinacion.carrera.all()).aggregate(Sum('valor'))['valor__sum'] if Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__inscripcion__carrera__in=coordinacion.carrera.all()).exists() else 0

# Total General Pagos de Todos los Tipos de rubros Comunes u Otros de todas las coordinaciones o carreras
def totalgeneral_depagos_rubros_rango_fechas(inicio, fin):
    return Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin).aggregate(Sum('valor'))['valor__sum'] if Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin).exists() else 0

# VALORES TOTALES POR COLUMNAS DE PAGOS SEGUN TIPOS DE RUBROS
def totalgeneral_depagos_rubrosinscripciones_rango_fechas(inicio, fin):
    return Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__rubroinscripcion__isnull=False).aggregate(Sum('valor'))['valor__sum'] if Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__rubroinscripcion__isnull=False).exists() else 0

def totalgeneral_depagos_rubrosmatriculas_rango_fechas(inicio, fin):
    return Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__rubromatricula__isnull=False).aggregate(Sum('valor'))['valor__sum'] if Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__rubromatricula__isnull=False).exists() else 0

def totalgeneral_depagos_rubrosespecies_rango_fechas(inicio, fin):
    return Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__rubroespecievalorada__isnull=False).aggregate(Sum('valor'))['valor__sum'] if Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__rubroespecievalorada__isnull=False).exists() else 0

def totalgeneral_depagos_rubroscuotas_rango_fechas(inicio, fin):
    return Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__rubrocuota__isnull=False).aggregate(Sum('valor'))['valor__sum'] if Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__rubrocuota__isnull=False).exists() else 0

def totalgeneral_depagos_rubrosnotasdebito_rango_fechas(inicio, fin):
    return Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__rubronotadebito__isnull=False).aggregate(Sum('valor'))['valor__sum'] if Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__rubronotadebito__isnull=False).exists() else 0

def totalgeneral_depagos_rubrosmaterias_rango_fechas(inicio, fin):
    return Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__rubromateria__isnull=False).aggregate(Sum('valor'))['valor__sum'] if Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__rubromateria__isnull=False).exists() else 0

def totalgeneral_depagos_rubrosotrosinscripciones_rango_fechas(inicio, fin):
    return Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__rubrootro__isnull=False, rubro__rubrootro__tipo__id=TIPO_INSCRIPCION_RUBRO).aggregate(Sum('valor'))['valor__sum'] if Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__rubrootro__isnull=False, rubro__rubrootro__tipo__id=TIPO_INSCRIPCION_RUBRO).exists() else 0

def totalgeneral_depagos_rubrosotroscuotas_rango_fechas(inicio, fin):
    return Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__rubrootro__isnull=False, rubro__rubrootro__tipo__id=TIPO_CUOTA_RUBRO).aggregate(Sum('valor'))['valor__sum'] if Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__rubrootro__isnull=False, rubro__rubrootro__tipo__id=TIPO_CUOTA_RUBRO).exists() else 0

def totalgeneral_depagos_rubrosotrosmoras_rango_fechas(inicio, fin):
    return Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__rubrootro__isnull=False, rubro__rubrootro__tipo__id=TIPO_MORA_RUBRO).aggregate(Sum('valor'))['valor__sum'] if Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__rubrootro__isnull=False, rubro__rubrootro__tipo__id=TIPO_MORA_RUBRO).exists() else 0

def totalgeneral_depagos_rubrosotroscongresos_rango_fechas(inicio, fin):
    return Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__rubrootro__isnull=False, rubro__rubrootro__tipo__id=TIPO_CONGRESO_RUBRO).aggregate(Sum('valor'))['valor__sum'] if Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__rubrootro__isnull=False, rubro__rubrootro__tipo__id=TIPO_CONGRESO_RUBRO).exists() else 0

def totalgeneral_depagos_rubrosotrosarrastres_rango_fechas(inicio, fin):
    return Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__rubrootro__isnull=False, rubro__rubrootro__tipo__id=TIPO_ARRASTRE_RUBRO).aggregate(Sum('valor'))['valor__sum'] if Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__rubrootro__isnull=False, rubro__rubrootro__tipo__id=TIPO_ARRASTRE_RUBRO).exists() else 0

def totalgeneral_depagos_rubrosotroscursos_rango_fechas(inicio, fin):
    return Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__rubrootro__isnull=False, rubro__rubrootro__tipo__id=TIPO_CURSOS_RUBRO).aggregate(Sum('valor'))['valor__sum'] if Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__rubrootro__isnull=False, rubro__rubrootro__tipo__id=TIPO_CURSOS_RUBRO).exists() else 0

def totalgeneral_depagos_rubrosotrosotros_rango_fechas(inicio, fin):
    return Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__rubrootro__isnull=False, rubro__rubrootro__tipo__id=TIPO_OTRO_RUBRO).aggregate(Sum('valor'))['valor__sum'] if Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__rubrootro__isnull=False, rubro__rubrootro__tipo__id=TIPO_OTRO_RUBRO).exists() else 0

# CARRERAS ------------- CARRERAS ----------CARRERAS

# PAGO DE RUBROS COMUNES: Matricula, Cuota, Nota Debito, Especies, Materia
def totalcarrera_depagos_rubrosinscripciones_rango_fechas(carrera, inicio, fin):
    return Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__inscripcion__carrera=carrera, rubro__rubroinscripcion__isnull=False).aggregate(Sum('valor'))['valor__sum'] if Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__inscripcion__carrera=carrera, rubro__rubroinscripcion__isnull=False).exists() else 0

def totalcarrera_depagos_rubrosmatriculas_rango_fechas(carrera, inicio, fin):
    return Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__inscripcion__carrera=carrera, rubro__rubromatricula__isnull=False).aggregate(Sum('valor'))['valor__sum'] if Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__inscripcion__carrera=carrera, rubro__rubromatricula__isnull=False).exists() else 0

def totalcarrera_depagos_rubrosespecies_rango_fechas(carrera, inicio, fin):
    return Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__inscripcion__carrera=carrera, rubro__rubroespecievalorada__isnull=False).aggregate(Sum('valor'))['valor__sum'] if Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__inscripcion__carrera=carrera, rubro__rubroespecievalorada__isnull=False).exists() else 0

def totalcarrera_depagos_rubroscuotas_rango_fechas(carrera, inicio, fin):
    return Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__inscripcion__carrera=carrera, rubro__rubrocuota__isnull=False).aggregate(Sum('valor'))['valor__sum'] if Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__inscripcion__carrera=carrera, rubro__rubrocuota__isnull=False).exists() else 0

def totalcarrera_depagos_rubrosnotasdebito_rango_fechas(carrera, inicio, fin):
    return Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__inscripcion__carrera=carrera, rubro__rubronotadebito__isnull=False).aggregate(Sum('valor'))['valor__sum'] if Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__inscripcion__carrera=carrera, rubro__rubronotadebito__isnull=False).exists() else 0

def totalcarrera_depagos_rubrosmaterias_rango_fechas(carrera, inicio, fin):
    return Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__inscripcion__carrera=carrera, rubro__rubromateria__isnull=False).aggregate(Sum('valor'))['valor__sum'] if Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__inscripcion__carrera=carrera, rubro__rubromateria__isnull=False).exists() else 0

# PAGOS DE RUBROS DE TIPO OTRO
def totalcarrera_depagos_rubrosotrosinscripciones_rango_fechas(carrera, inicio, fin):
    return Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__inscripcion__carrera=carrera, rubro__rubrootro__isnull=False, rubro__rubrootro__tipo__id=TIPO_INSCRIPCION_RUBRO).aggregate(Sum('valor'))['valor__sum'] if Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__inscripcion__carrera=carrera, rubro__rubrootro__isnull=False, rubro__rubrootro__tipo__id=TIPO_INSCRIPCION_RUBRO).exists() else 0

def totalcarrera_depagos_rubrosotroscuotas_rango_fechas(carrera, inicio, fin):
    return Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__inscripcion__carrera=carrera, rubro__rubrootro__isnull=False, rubro__rubrootro__tipo__id=TIPO_CUOTA_RUBRO).aggregate(Sum('valor'))['valor__sum'] if Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__inscripcion__carrera=carrera, rubro__rubrootro__isnull=False, rubro__rubrootro__tipo__id=TIPO_CUOTA_RUBRO).exists() else 0

def totalcarrera_depagos_rubrosotrosmoras_rango_fechas(carrera, inicio, fin):
    return Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__inscripcion__carrera=carrera, rubro__rubrootro__isnull=False, rubro__rubrootro__tipo__id=TIPO_MORA_RUBRO).aggregate(Sum('valor'))['valor__sum'] if Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__inscripcion__carrera=carrera, rubro__rubrootro__isnull=False, rubro__rubrootro__tipo__id=TIPO_MORA_RUBRO).exists() else 0

def totalcarrera_depagos_rubrosotroscongresos_rango_fechas(carrera, inicio, fin):
    return Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__inscripcion__carrera=carrera, rubro__rubrootro__isnull=False, rubro__rubrootro__tipo__id=TIPO_CONGRESO_RUBRO).aggregate(Sum('valor'))['valor__sum'] if Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__inscripcion__carrera=carrera, rubro__rubrootro__isnull=False, rubro__rubrootro__tipo__id=TIPO_CONGRESO_RUBRO).exists() else 0

def totalcarrera_depagos_rubrosotrosarrastres_rango_fechas(carrera, inicio, fin):
    return Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__inscripcion__carrera=carrera, rubro__rubrootro__isnull=False, rubro__rubrootro__tipo__id=TIPO_ARRASTRE_RUBRO).aggregate(Sum('valor'))['valor__sum'] if Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__inscripcion__carrera=carrera, rubro__rubrootro__isnull=False, rubro__rubrootro__tipo__id=TIPO_ARRASTRE_RUBRO).exists() else 0

def totalcarrera_depagos_rubrosotroscursos_rango_fechas(carrera, inicio, fin):
    return Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__inscripcion__carrera=carrera, rubro__rubrootro__isnull=False, rubro__rubrootro__tipo__id=TIPO_CURSOS_RUBRO).aggregate(Sum('valor'))['valor__sum'] if Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__inscripcion__carrera=carrera, rubro__rubrootro__isnull=False, rubro__rubrootro__tipo__id=TIPO_CURSOS_RUBRO).exists() else 0

def totalcarrera_depagos_rubrosotrosotros_rango_fechas(carrera, inicio, fin):
    return Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__inscripcion__carrera=carrera, rubro__rubrootro__isnull=False, rubro__rubrootro__tipo__id=TIPO_OTRO_RUBRO).aggregate(Sum('valor'))['valor__sum'] if Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__inscripcion__carrera=carrera, rubro__rubrootro__isnull=False, rubro__rubrootro__tipo__id=TIPO_OTRO_RUBRO).exists() else 0

# Total Pagos de Todos los Tipos de rubros Comunes u Otros de la Coordinacion
def totalcarrera_depagos_rubros_rango_fechas(carrera, inicio, fin):
    return Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__inscripcion__carrera=carrera).aggregate(Sum('valor'))['valor__sum'] if Pago.objects.filter(sesion__fecha__gte=inicio, sesion__fecha__lte=fin, rubro__inscripcion__carrera=carrera).exists() else 0

@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    if request.method=='POST':
        action = request.POST['action']
        if action=='colchartsesion':
            hoy = datetime.today().date()
            #Sesiones del dia con algun valor final
            data = {"results": [{"id": x.id, "caja":x.caja.nombre, "efectivo":x.total_efectivo_sesion(), "cheque":x.total_cheque_sesion(),
                                 "tarjeta":x.total_tarjeta_sesion(),"deposito":x.total_deposito_sesion(),"transf":x.total_transferencia_sesion(),
                                 "ncredito":x.total_notadecredito_sesion()} for x in SesionCaja.objects.filter(fecha=hoy).order_by('caja__nombre') if x.total_sesion()]}
            return HttpResponse(json.dumps(data), content_type="application/json")
        elif action=='colchartsesionfecha':
            fecha = convertir_fecha(request.POST['fecha'])
            #Sesiones del dia con algun valor final
            data = {"results": [{"id": x.id, "caja":x.caja.nombre, "efectivo":x.total_efectivo_sesion(), "cheque":x.total_cheque_sesion(),
                                 "tarjeta":x.total_tarjeta_sesion(),"deposito":x.total_deposito_sesion(),"transf":x.total_transferencia_sesion(),
                                 "ncredito":x.total_notadecredito_sesion()} for x in SesionCaja.objects.filter(fecha=fecha).order_by('caja__nombre') if x.total_sesion()]}
            return HttpResponse(json.dumps(data), content_type="application/json")


    else:
        data = {'title': 'Estadisticas y Graficos'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='colchartsesion':
                data['title'] = 'Grafica de Valores del dia por Cajas'
                hoy = datetime.today().date()
                data['hoy'] = hoy
                #Sesiones del dia que tengan al menos una operacion y valor
                data['sesiones']=[x for x in SesionCaja.objects.filter(fecha=hoy).order_by('caja__nombre') if x.total_sesion()]
                data['maximo_escala'] = max([x.total_efectivo_sesion() for x in SesionCaja.objects.filter(fecha=hoy).order_by('caja__nombre') if x.total_sesion()])
                return render(request ,"estadisticas/colchartsesion.html" ,  data)

            elif action=='colchartsesionfecha':
                data['title'] = 'Grafica de Valores por Cajas segun fecha'
                fecha = convertir_fecha(request.GET['fecha'])
                data['fecha'] = fecha
                #Sesiones del dia que tengan al menos una operacion y valor
                data['sesiones']=[x for x in SesionCaja.objects.filter(fecha=fecha).order_by('caja__nombre') if x.total_sesion()]
                data['maximo_escala'] = max([x.total_efectivo_sesion() for x in SesionCaja.objects.filter(fecha=fecha).order_by('caja__nombre') if x.total_sesion()])
                return render(request ,"estadisticas/colchartsesionfecha.html" ,  data)

            elif action=='piechartcoordinacion':
                data['title'] = 'Graficas del dia por Coordinaciones'
                data['hoy'] = datetime.today().date()
                data['coordinaciones'] = Coordinacion.objects.all().order_by('id') #Todas las Coordinaciones
                return render(request ,"estadisticas/piechartcoordinacion.html" ,  data)

            elif action=='piechartcoordinacionfecha':
                data['title'] = 'Graficas segun fecha por Coordinaciones'
                fecha = convertir_fecha(request.GET['fecha'])
                data['fecha'] = fecha
                coordinaciones = Coordinacion.objects.all().order_by('id') #Todas las Coordinaciones
                lista_facturas = []
                lista_valores = []
                lista_matriculados = []
                for c in coordinaciones:
                    lista_facturas.append((c.nombre, c.cantidad_facturas_fecha(fecha)))
                    lista_valores.append((c.nombre, c.total_pagos_fecha(fecha)))
                    lista_matriculados.append((c.nombre, c.cantidad_matriculados()))
                data['lista_facturas'] = lista_facturas
                data['lista_valores'] = lista_valores
                data['lista_matriculados'] = lista_matriculados
                return render(request ,"estadisticas/piechartcoordinacionfecha.html" ,  data)

            elif action=='piechartsexoscoord':
                data['title'] = 'Graficas comparativas de Sexos por Coordinaciones'
                data['hoy'] = datetime.today().date()
                data['coordinaciones'] = [c for c in Coordinacion.objects.all().order_by('id') ] #Todas las Coordinaciones q tengan al menos un matriculado
                data['sexos'] = Sexo.objects.all()
                data['total_matriculados_mujeres'] = total_matriculados_mujeres()
                data['total_matriculados_hombres'] = total_matriculados_hombres()
                data['total_matriculados'] = total_matriculados()
                return render(request ,"estadisticas/piechartgenerocoord.html" ,  data)

            # OCU 09-sep-2015
            elif action=='piechartmatedades':
                data['title'] = 'Graficas comparativas de Edades por Coordinaciones'
                data['hoy'] = datetime.today().date()
                data['coordinaciones'] = [c for c in Coordinacion.objects.all().order_by('id') ] #Todas las Coordinaciones q tengan al menos un matriculado
                data['total_matriculados_menor_30'] = matriculados_menor_30()
                data['total_matriculados_31_40'] = matriculados_31_40()
                data['total_matriculados_41_50'] = matriculados_41_50()
                data['total_matriculados_51_60'] = matriculados_51_60()
                data['total_matriculados_mayor_61'] = matriculados_mayor_61()
                data['total_matriculados'] = total_matriculados_edades()
                return render(request ,"estadisticas/piechartgeneroedad.html" ,  data)

            # OCU 10-sep-2015
            elif action=='piechartmatbecdisc':
                data['title'] = 'Graficas comparativas de Becas y Discapacidades por Coordinaciones'
                data['hoy'] = datetime.today().date()
                data['coordinaciones'] = [c for c in Coordinacion.objects.all().order_by('id') if c.cantidad_matriculados()] #Todas las Coordinaciones q tengan al menos un matriculado
                data['total_matriculados_beca'] = cantidad_matriculados_beca()
                data['total_matriculados_discapacidad'] = cantidad_matriculados_discapacidad()
                data['total_matriculados'] = total_matriculados_becasdiscapacidad()
                return render(request ,"estadisticas/piechartgenerobecadisc.html" ,  data)

            elif action=='piechartgenerocarr':
                data['title'] = 'Graficas comparativas de Sexos por Carreras'
                data['hoy'] = datetime.today().date()
                data['carreras'] = [c for c in Carrera.objects.all().order_by('id') if c.mat_carrera2()] #Todas las Carreras q tengan al menos un matriculado
                data['sexos'] = Sexo.objects.all()
                data['total_matriculados_mujeres'] = total_matriculados_mujeres()
                data['total_matriculados_hombres'] = total_matriculados_hombres()
                data['total_matriculados'] = total_matriculados()
                return render(request ,"estadisticas/piechartgenerocarr.html" ,  data)

            # OCU 14-sep-2015
            elif action=='piechartedadescarr':
                data['title'] = 'Graficas comparativas de Edades por Carreras'
                data['hoy'] = datetime.today().date()
                data['carreras'] = [c for c in Carrera.objects.all().order_by('id') if c.mat_carrera2()] #Todas las Carreras q tengan al menos un matriculado
                data['total_matriculados_menor_30'] = matriculados_menor_30()
                data['total_matriculados_31_40'] = matriculados_31_40()
                data['total_matriculados_41_50'] = matriculados_41_50()
                data['total_matriculados_51_60'] = matriculados_51_60()
                data['total_matriculados_mayor_61'] = matriculados_mayor_61()
                data['total_matriculados'] = total_matriculados_edades()
                return render(request ,"estadisticas/piechartedadescarr.html" ,  data)

            # OCU 15-sep-2015
            elif action=='piechartbecasdisccarr':
                data['title'] = 'Graficas Matriculados Becados y Discapacitados'
                data['hoy'] = datetime.today().date()
                data['carreras'] = [c for c in Carrera.objects.all().order_by('id') if c.mat_carrera2()] #Todas las Carreras q tengan al menos un matriculado
                data['total_matriculados_beca'] = cantidad_matriculados_beca()
                data['total_matriculados_discapacidad'] = cantidad_matriculados_discapacidad()
                data['total_matriculados'] = total_matriculados_becasdiscapacidad()
                return render(request ,"estadisticas/piechartbecasdisccarr.html" ,  data)

            elif action=='piechartcarrera':
                data['title'] = 'Graficas del dia por Carreras'
                data['hoy'] = datetime.today().date()
                data['carreras'] = [x for x in Carrera.objects.all() if x.mat_carrera2()]   #Todas las Carreras que tengan al menos un matriculado
                return render(request ,"estadisticas/piechartcarrera.html" ,  data)

            elif action=='piechartcarrerafecha':
                data['title'] = 'Graficas segun fecha por Carreras'
                fecha = convertir_fecha(request.GET['fecha'])
                data['fecha'] = fecha
                carreras = [x for x in Carrera.objects.all() if x.mat_carrera2()]  #Todas las Carreras q tengan al menos un matriculado
                lista_facturas = []
                lista_valores = []
                lista_matriculados = []
                for c in carreras:
                    lista_facturas.append((c.alias, c.cantidad_facturas_fecha(fecha)))
                    lista_valores.append((c.alias, c.total_pagos_fecha(fecha)))
                    lista_matriculados.append((c.alias, c.mat_carrera2()))
                data['lista_facturas'] = lista_facturas
                data['lista_valores'] = lista_valores
                data['lista_matriculados'] = lista_matriculados
                return render(request ,"estadisticas/piechartcarrerafecha.html" ,  data)

            elif action=='geochartprovincias':
                data['title'] = 'Mapa Matriculados por Provincias'
                if 'fechainicio' in request.GET:
                    fechainicio = date(int(str(request.GET['fechainicio']).split('-')[2]),int(str(request.GET['fechainicio']).split('-')[1]),int(str(request.GET['fechainicio']).split('-')[0]))
                    fechafin = date(int(str(request.GET['fechafin']).split('-')[2]),int(str(request.GET['fechafin']).split('-')[1]),int(str(request.GET['fechafin']).split('-')[0]))
                    data['fechainicio'] = fechainicio
                    data['fechafin'] = fechafin
                    data['provincias'] = [x for x in Provincia.objects.all() if x.cantidad_matriculadosfil(fechainicio,fechafin)]   #Todas las Provincias que tengan al menos un matriculado
                    data['provinciasnul'] = total_matriculadosfilnullprovin(fechainicio,fechafin)
                else:
                    data['provincias'] = [x for x in Provincia.objects.all() if x.cantidad_matriculados()]   #Todas las Provincias que tengan al menos un matriculado
                    data['provinciasnul'] = total_matriculadosprovinnull()
                return render(request ,"estadisticas/geochartprovincias.html" ,  data)

            elif action=='geochartcantones':
                data['title'] = 'Mapa Matriculados por Cantones'
                if 'fechainicio' in request.GET:
                    fechainicio = date(int(str(request.GET['fechainicio']).split('-')[2]),int(str(request.GET['fechainicio']).split('-')[1]),int(str(request.GET['fechainicio']).split('-')[0]))
                    fechafin = date(int(str(request.GET['fechafin']).split('-')[2]),int(str(request.GET['fechafin']).split('-')[1]),int(str(request.GET['fechafin']).split('-')[0]))
                    data['fechainicio'] = fechainicio
                    data['fechafin'] = fechafin
                    data['cantones'] = [y for y in Canton.objects.all() if y.cantidad_matriculadosfil(fechainicio,fechafin)]   #Todas los Cantones que tengan al menos un matriculado
                    # data['cantonnul'] = total_matriculadosfilcanton(fechainicio,fechafin)
                else:
                    data['cantones'] = [y for y in Canton.objects.all() if y.cantidad_matriculados()]   #Todas los Cantones que tengan al menos un matriculado
                    # data['cantonnul'] = total_matriculadoscantonnull()
                return render(request ,"estadisticas/geochartcantones.html" ,  data)

            elif action=='tablasegmentocoord':
                data['title'] = 'Tablas de valores historicos por coordinaciones'
                finicio = convertir_fecha(request.GET['inicio'])
                ffin = convertir_fecha(request.GET['fin'])

                coordinaciones = Coordinacion.objects.all().order_by('id')

                fechas=[]
                totales=[]
                porcientos=[]
                iterfecha = finicio
                totalfacturas=0
                totalvalores=0
                while iterfecha <= ffin:
                    fila = []
                    for coordinacion in coordinaciones:
                        fila.append((coordinacion.cantidad_facturas_fecha(iterfecha),coordinacion.total_pagos_fecha(iterfecha)))

                    fechas.append((iterfecha,fila,facturas_total_fecha(iterfecha),pagos_total_fecha(iterfecha)))
                    iterfecha += timedelta(1)

                for coordinacion in coordinaciones:
                    totales.append((coordinacion.cantidad_facturas_rango_fechas(finicio, ffin),coordinacion.total_pagos_rango_fechas(finicio,ffin)))
                    porcientos.append((coordinacion.porciento_cantidad_facturas(finicio, ffin),coordinacion.porciento_valor_pagos(finicio,ffin)))
                    totalfacturas+=coordinacion.porciento_cantidad_facturas(finicio,ffin)
                    totalvalores+=coordinacion.porciento_valor_pagos(finicio,ffin)

                data['fechas'] = fechas
                data['totales'] = totales
                data['porcientos'] = porcientos
                data['hoy'] = datetime.now().today()
                data['coordinaciones'] = coordinaciones
                data['cant_facturas_total'] = cantidad_facturas_total_fechas(finicio, ffin)
                data['total_pagos_rango_fechas'] = total_pagos_rango_fechas(finicio, ffin)
                data['totalfacturas']= totalfacturas
                data['totalvalores'] = totalvalores

                persona=data['persona']
                if persona.puede_ver_ingresos():
                    return render(request ,"estadisticas/tablasegmentocoord.html" ,  data)

            elif action=='consultainscritos':
                data['title'] = 'Tablas de Alumnos inscritos por Carrera'
                inicio = convertir_fecha(request.GET['inicio'])
                fin = convertir_fecha(request.GET['fin'])

                data['carreras'] = Carrera.objects.all().order_by('coordinacion__id')
                g= InscripcionGrupo.objects.filter(grupo__fin__gte=inicio,grupo__fin__lte=fin).values('grupo').distinct()
                data['total']= InscripcionGrupo.objects.filter(grupo__id__in=g).count()
                data['grupos'] = Grupo.objects.filter(pk__in=g).order_by('carrera')

                fechas=[]
                totales=[]
                porcientos=[]

                persona=data['persona']
                return render(request ,"estadisticas/tablasegmentoinsc.html" ,  data)

            elif action=='tablapagostiposrubroscoord':
                data['title'] = 'Tablas de pagos de rubros por coordinaciones segun fechas'
                finicio = convertir_fecha(request.GET['inicio'])
                ffin = convertir_fecha(request.GET['fin'])

                coordinaciones = Coordinacion.objects.all().order_by('id')
                totales_columnas=[]
                totales=[]
                for coordinacion in coordinaciones:
                    totales.append((coordinacion.nombre,
                                    round(total_depagos_rubrosinscripciones_rango_fechas(coordinacion,finicio,ffin) + total_depagos_rubrosotrosinscripciones_rango_fechas(coordinacion, finicio, ffin), 2),
                                    total_depagos_rubrosmatriculas_rango_fechas(coordinacion, finicio, ffin),
                                    total_depagos_rubrosespecies_rango_fechas(coordinacion, finicio, ffin),
                                    round(total_depagos_rubroscuotas_rango_fechas(coordinacion, finicio, ffin) + total_depagos_rubrosotroscuotas_rango_fechas(coordinacion, finicio, ffin), 2),
                                    total_depagos_rubrosnotasdebito_rango_fechas(coordinacion, finicio, ffin),
                                    total_depagos_rubrosmaterias_rango_fechas(coordinacion, finicio, ffin),
                                    total_depagos_rubrosotrosmoras_rango_fechas(coordinacion, finicio, ffin),
                                    total_depagos_rubrosotroscongresos_rango_fechas(coordinacion, finicio, ffin),
                                    total_depagos_rubrosotrosarrastres_rango_fechas(coordinacion, finicio, ffin),
                                    total_depagos_rubrosotroscursos_rango_fechas(coordinacion, finicio, ffin),
                                    total_depagos_rubrosotrosotros_rango_fechas(coordinacion, finicio, ffin),
                                    total_depagos_rubros_rango_fechas(coordinacion, finicio, ffin)
                                    ))

                # Calcular los totales por columnas de los Pagos segun tipo de Rubro
                totales_columnas.append(("TOTALES",
                                         round(totalgeneral_depagos_rubrosinscripciones_rango_fechas(finicio, ffin) + totalgeneral_depagos_rubrosotrosinscripciones_rango_fechas(finicio, ffin), 2),
                                         totalgeneral_depagos_rubrosmatriculas_rango_fechas(finicio, ffin),
                                         totalgeneral_depagos_rubrosespecies_rango_fechas(finicio, ffin),
                                         round(totalgeneral_depagos_rubroscuotas_rango_fechas(finicio, ffin) + totalgeneral_depagos_rubrosotroscuotas_rango_fechas(finicio, ffin), 2),
                                         totalgeneral_depagos_rubrosnotasdebito_rango_fechas(finicio, ffin),
                                         totalgeneral_depagos_rubrosmaterias_rango_fechas(finicio, ffin),
                                         totalgeneral_depagos_rubrosotrosmoras_rango_fechas(finicio, ffin),
                                         totalgeneral_depagos_rubrosotroscongresos_rango_fechas(finicio, ffin),
                                         totalgeneral_depagos_rubrosotrosarrastres_rango_fechas(finicio, ffin),
                                         totalgeneral_depagos_rubrosotroscursos_rango_fechas(finicio, ffin),
                                         totalgeneral_depagos_rubrosotrosotros_rango_fechas(finicio, ffin),
                                         totalgeneral_depagos_rubros_rango_fechas(finicio, ffin) ))

                data['totales'] = totales
                data['totales_columnas'] = totales_columnas
                data['hoy'] = datetime.now().today()
                data['coordinaciones'] = coordinaciones

                persona=data['persona']
                if persona.puede_ver_ingresos():
                    return render(request ,"estadisticas/tblpagosrubros.html" ,  data)

            elif action=='tablapagostiposrubroscarr':
                data['title'] = 'Tablas de pagos de rubros por carreras segun fechas'
                finicio = convertir_fecha(request.GET['inicio'])
                ffin = convertir_fecha(request.GET['fin'])

                carreras = set([x for x in Carrera.objects.all().order_by('coordinacion__id') if x.total_pagos_rango_fechas(finicio, ffin)])
                totales_columnas=[]
                totales=[]
                for carrera in carreras:
                    totales.append((carrera.alias,
                                    round(totalcarrera_depagos_rubrosinscripciones_rango_fechas(carrera,finicio,ffin) + totalcarrera_depagos_rubrosotrosinscripciones_rango_fechas(carrera, finicio, ffin), 2),
                                    totalcarrera_depagos_rubrosmatriculas_rango_fechas(carrera, finicio, ffin),
                                    totalcarrera_depagos_rubrosespecies_rango_fechas(carrera, finicio, ffin),
                                    round(totalcarrera_depagos_rubroscuotas_rango_fechas(carrera, finicio, ffin) + totalcarrera_depagos_rubrosotroscuotas_rango_fechas(carrera, finicio, ffin), 2),
                                    totalcarrera_depagos_rubrosnotasdebito_rango_fechas(carrera, finicio, ffin),
                                    totalcarrera_depagos_rubrosmaterias_rango_fechas(carrera, finicio, ffin),
                                    totalcarrera_depagos_rubrosotrosmoras_rango_fechas(carrera, finicio, ffin),
                                    totalcarrera_depagos_rubrosotroscongresos_rango_fechas(carrera, finicio, ffin),
                                    totalcarrera_depagos_rubrosotrosarrastres_rango_fechas(carrera, finicio, ffin),
                                    totalcarrera_depagos_rubrosotroscursos_rango_fechas(carrera, finicio, ffin),
                                    totalcarrera_depagos_rubrosotrosotros_rango_fechas(carrera, finicio, ffin),
                                    totalcarrera_depagos_rubros_rango_fechas(carrera, finicio, ffin)
                                    ))

                # Calcular los totales por columnas de los Pagos segun tipo de Rubro
                totales_columnas.append(("TOTALES",
                                         round(totalgeneral_depagos_rubrosinscripciones_rango_fechas(finicio, ffin) + totalgeneral_depagos_rubrosotrosinscripciones_rango_fechas(finicio, ffin), 2),
                                         totalgeneral_depagos_rubrosmatriculas_rango_fechas(finicio, ffin),
                                         totalgeneral_depagos_rubrosespecies_rango_fechas(finicio, ffin),
                                         round(totalgeneral_depagos_rubroscuotas_rango_fechas(finicio, ffin) + totalgeneral_depagos_rubrosotroscuotas_rango_fechas(finicio, ffin), 2),
                                         totalgeneral_depagos_rubrosnotasdebito_rango_fechas(finicio, ffin),
                                         totalgeneral_depagos_rubrosmaterias_rango_fechas(finicio, ffin),
                                         totalgeneral_depagos_rubrosotrosmoras_rango_fechas(finicio, ffin),
                                         totalgeneral_depagos_rubrosotroscongresos_rango_fechas(finicio, ffin),
                                         totalgeneral_depagos_rubrosotrosarrastres_rango_fechas(finicio, ffin),
                                         totalgeneral_depagos_rubrosotroscursos_rango_fechas(finicio, ffin),
                                         totalgeneral_depagos_rubrosotrosotros_rango_fechas(finicio, ffin),
                                         totalgeneral_depagos_rubros_rango_fechas(finicio, ffin) ))

                data['totales'] = totales
                data['totales_columnas'] = totales_columnas
                data['hoy'] = datetime.now().today()
                data['carreras'] = carreras

                persona=data['persona']
                if persona.puede_ver_ingresos():
                    return render(request ,"estadisticas/tblpagosrubroscarr.html" ,  data)

            elif action=='linechartfactcoord':
                data['title'] = 'Grafico Lineal de Facturas por Coordinaciones'
                finicio = convertir_fecha(request.GET['inicio'])
                ffin = convertir_fecha(request.GET['fin'])

                coordinaciones = Coordinacion.objects.all().order_by('id')

                fechas_fact=[]
                iterfecha = finicio
                while iterfecha <= ffin:
                    fila_fact = []
                    for coordinacion in coordinaciones:
                        fila_fact.append(coordinacion.cantidad_facturas_fecha(iterfecha))

                    fechas_fact.append((iterfecha,fila_fact))
                    iterfecha += timedelta(1)

                data['fechas_fact'] = fechas_fact
                data['inicio'] = finicio
                data['fin'] = ffin
                data['hoy'] = datetime.now().today()
                data['coordinaciones'] = coordinaciones

                persona=data['persona']
                if persona.puede_ver_ingresos():
                    return render(request ,"estadisticas/linechartfactcoord.html" ,  data)

            elif action=='linecharttotalfact':
                data['title'] = 'Grafico Lineal de Facturas en el intervalo de fechas'
                finicio = convertir_fecha(request.GET['inicio'])
                ffin = convertir_fecha(request.GET['fin'])

                fechas_totales_fact=[]
                iterfecha = finicio
                while iterfecha <= ffin:
                    fechas_totales_fact.append((iterfecha,facturas_total_fecha(iterfecha)))
                    iterfecha += timedelta(1)

                data['fechas_totales_fact'] = fechas_totales_fact
                data['inicio'] = finicio
                data['fin'] = ffin
                data['hoy'] = datetime.now().today()

                persona=data['persona']
                if persona.puede_ver_ingresos():
                    return render(request ,"estadisticas/linechartotalfact.html" ,  data)

            elif action=='linechartvalcoord':
                data['title'] = 'Grafico Lineal de Valores Diarios por Coordinaciones'
                finicio = convertir_fecha(request.GET['inicio'])
                ffin = convertir_fecha(request.GET['fin'])

                coordinaciones = Coordinacion.objects.all().order_by('id')

                fechas_val=[]
                iterfecha = finicio
                while iterfecha <= ffin:
                    fila_val = []
                    for coordinacion in coordinaciones:
                        fila_val.append(coordinacion.total_pagos_fecha(iterfecha))

                    fechas_val.append((iterfecha,fila_val))
                    iterfecha += timedelta(1)

                data['fechas_val'] = fechas_val
                data['inicio'] = finicio
                data['fin'] = ffin
                data['hoy'] = datetime.now().today()
                data['coordinaciones'] = coordinaciones

                persona=data['persona']
                if persona.puede_ver_ingresos():
                    return render(request ,"estadisticas/linechartvalcoord.html" ,  data)

            elif action=='linecharttotalval':
                data['title'] = 'Grafico Lineal de Ingreso de Valores en el intervalo de fechas'
                finicio = convertir_fecha(request.GET['inicio'])
                ffin = convertir_fecha(request.GET['fin'])

                fechas_totales_val=[]
                iterfecha = finicio
                while iterfecha <= ffin:
                    fechas_totales_val.append((iterfecha, pagos_total_fecha(iterfecha)))
                    iterfecha += timedelta(1)

                data['fechas_totales_val'] = fechas_totales_val
                data['inicio'] = finicio
                data['fin'] = ffin
                data['hoy'] = datetime.now().today()

                persona=data['persona']
                if persona.puede_ver_ingresos():
                    return render(request ,"estadisticas/linecharttotalval.html" ,  data)

            elif action=='tablasegmentocarrera':
                data['title'] = 'Tablas de valores historicos por carreras'
                finicio = convertir_fecha(request.GET['inicio'])
                ffin = convertir_fecha(request.GET['fin'])

                carreras = [x for x in Carrera.objects.all() if x.mat_carrera2()]

                fechas=[]
                totales=[]
                porcientos=[]
                iterfecha = finicio
                while iterfecha <= ffin:
                    fila = []
                    for carrera in carreras:
                        fila.append((carrera.cantidad_facturas_fecha(iterfecha),carrera.total_pagos_fecha(iterfecha)))

                    fechas.append((iterfecha,fila,facturas_total_fecha(iterfecha),pagos_total_fecha(iterfecha)))
                    iterfecha += timedelta(1)

                for carrera in carreras:
                    totales.append((carrera.cantidad_facturas_rango_fechas(finicio, ffin),carrera.total_pagos_rango_fechas(finicio,ffin)))
                    porcientos.append((carrera.porciento_cantidad_facturas(finicio, ffin),carrera.porciento_valor_pagos(finicio,ffin)))

                data['fechas'] = fechas
                data['totales'] = totales
                data['porcientos'] = porcientos
                data['hoy'] = datetime.now().today()
                data['carreras'] = carreras
                data['cant_facturas_total'] = cantidad_facturas_total_fechas(finicio, ffin)
                data['total_pagos_rango_fechas'] = total_pagos_rango_fechas(finicio, ffin)

                persona=data['persona']
                if persona.puede_ver_ingresos():
                    return render(request ,"estadisticas/tablasegmentocarrera.html" ,  data)

            elif action=='linechartfactcarr':
                data['title'] = 'Grafico Lineal de Facturas por Carreras'
                finicio = convertir_fecha(request.GET['inicio'])
                ffin = convertir_fecha(request.GET['fin'])

                carreras = [x for x in Carrera.objects.all() if x.mat_carrera2()]

                fechas_fact=[]
                iterfecha = finicio
                while iterfecha <= ffin:
                    fila_fact = []
                    for carrera in carreras:
                        fila_fact.append(carrera.cantidad_facturas_fecha(iterfecha))

                    fechas_fact.append((iterfecha,fila_fact))
                    iterfecha += timedelta(1)

                data['fechas_fact'] = fechas_fact
                data['inicio'] = finicio
                data['fin'] = ffin
                data['hoy'] = datetime.now().today()
                data['carreras'] = carreras

                persona=data['persona']
                if persona.puede_ver_ingresos():
                    return render(request ,"estadisticas/linechartfactcarr.html" ,  data)

            elif action=='linechartvalcarr':
                data['title'] = 'Grafico Lineal de Valores Diarios por Carreras'
                finicio = convertir_fecha(request.GET['inicio'])
                ffin = convertir_fecha(request.GET['fin'])

                carreras = [x for x in Carrera.objects.all() if x.mat_carrera2()]

                fechas_val=[]
                iterfecha = finicio
                while iterfecha <= ffin:
                    fila_val = []
                    for carrera in carreras:
                        fila_val.append(carrera.total_pagos_fecha(iterfecha))

                    fechas_val.append((iterfecha,fila_val))
                    iterfecha += timedelta(1)

                data['fechas_val'] = fechas_val
                data['inicio'] = finicio
                data['fin'] = ffin
                data['hoy'] = datetime.now().today()
                data['carreras'] = carreras

                persona=data['persona']
                if persona.puede_ver_ingresos():
                    return render(request ,"estadisticas/linechartvalcarr.html" ,  data)

            elif action=='tablasegmentodia':
                data['title'] = 'Tablas de operaciones del dia'
                persona=data['persona']
                hoy = datetime.now().today()
                data['hoy'] = hoy

                if persona.puede_ver_ingresos():
                    data['total_efectivo_dia'] = total_efectivo_dia(hoy)
                    data['cantidad_cheques_dia'] = cantidad_cheques_dia(hoy)
                    data['total_cheque_dia'] = total_cheque_dia(hoy)
                    data['cantidad_tarjetas_dia'] = cantidad_tarjetas_dia(hoy)
                    data['total_tarjeta_dia'] = total_tarjeta_dia(hoy)
                    data['cantidad_depositos_dia'] = cantidad_depositos_dia(hoy)
                    data['total_deposito_dia'] = total_deposito_dia(hoy)
                    data['cantidad_transferencias_dia'] = cantidad_transferencias_dia(hoy)
                    data['total_transferencia_dia'] = total_transferencia_dia(hoy)
                    data['cantidad_recibocaja_dia'] = cantidad_recibocaja_dia(hoy)
                    data['total_recibocaja_dia'] = total_recibocaja_dia(hoy)
                    data['cantidad_retencion_dia'] = cantidad_retencion_dia(hoy)
                    data['total_retencion_dia'] = total_retencion_dia(hoy)

                    data['cantidad_facturas_dia'] = cantidad_facturas_dia(hoy)
                    data['total_dia'] = total_dia(hoy)
                    data['total_matriculados'] = total_matriculados()

                    #sesiones del dia con algun valor final
                    data['sesiones']=[x for x in SesionCaja.objects.filter(fecha=hoy).order_by('caja__nombre') if x.total_sesion()]

                    #datos del dia por carreras que tengan al menos un matriculado
                    data['carreras']=[x for x in Carrera.objects.all() if x.mat_carrera2()]

                    #Si usa coordinaciones de carreras para las tablas resumenes por coordinaciones academicas
                    if UTILIZA_COORDINACIONES:
                        data['utiliza_coordinaciones'] = UTILIZA_COORDINACIONES
                        data['coordinaciones'] = Coordinacion.objects.all().order_by('id')

                    return render(request ,"estadisticas/tablasegmento.html" ,  data)

            elif action=='tablasegmentofecha':
                data['title'] = 'Tablas de operaciones segun fecha'
                persona=data['persona']
                fecha = convertir_fecha(request.GET['fecha'])
                data['fecha'] = fecha

                if persona.puede_ver_ingresos():
                    data['total_efectivo_dia'] = total_efectivo_dia(fecha)
                    data['cantidad_cheques_dia'] = cantidad_cheques_dia(fecha)
                    data['total_cheque_dia'] = total_cheque_dia(fecha)
                    data['cantidad_tarjetas_dia'] = cantidad_tarjetas_dia(fecha)
                    data['total_tarjeta_dia'] = total_tarjeta_dia(fecha)
                    data['cantidad_depositos_dia'] = cantidad_depositos_dia(fecha)
                    data['total_deposito_dia'] = total_deposito_dia(fecha)
                    data['cantidad_transferencias_dia'] = cantidad_transferencias_dia(fecha)
                    data['total_transferencia_dia'] = total_transferencia_dia(fecha)
                    data['cantidad_recibocaja_dia'] = cantidad_recibocaja_dia(fecha)
                    data['total_recibocaja_dia'] = total_recibocaja_dia(fecha)
                    data['cantidad_retencion_dia'] = cantidad_retencion_dia(fecha)
                    data['total_retencion_dia'] = total_retencion_dia(fecha)

                    data['cantidad_facturas_dia'] = cantidad_facturas_dia(fecha)
                    data['total_dia'] = total_dia(fecha)
                    data['total_matriculados'] = total_matriculados()

                    #sesiones del dia con algun valor final
                    data['sesiones']=[x for x in SesionCaja.objects.filter(fecha=fecha).order_by('caja__nombre') if x.total_sesion()]

                    #datos del dia por carreras que tengan al menos un matriculado
                    carreras=[x for x in Carrera.objects.all() if x.mat_carrera2()]

                    lista_carreras = []
                    for c in carreras:
                        lista_carreras.append((c.alias, c.cantidad_facturas_fecha(fecha), c.total_pagos_fecha(fecha), c.mat_carrera2()))
                    data['lista_carreras']=lista_carreras

                    #Si usa coordinaciones de carreras para las tablas resumenes por coordinaciones academicas
                    if UTILIZA_COORDINACIONES:
                        data['utiliza_coordinaciones'] = UTILIZA_COORDINACIONES
                        coordinaciones = Coordinacion.objects.all().order_by('id')

                        lista_coordinaciones = []
                        for c in coordinaciones:
                            lista_coordinaciones.append((c.nombre, c.cantidad_facturas_fecha(fecha), c.total_pagos_fecha(fecha), c.cantidad_matriculados()))
                        data['lista_coordinaciones']=lista_coordinaciones

                    return render(request ,"estadisticas/tablasegmentofecha.html" ,  data)

            elif action=='tablasegmentodeudacoord':
                data['title'] = 'Tablas de Creditos y Deudas por Coordinaciones'

                data['coordinaciones'] = Coordinacion.objects.all().order_by('id')
                data['utiliza_coordinaciones'] = UTILIZA_COORDINACIONES

                #Datos totales sobre Alumnos con Creditos y Deudas y los Valores correspondientes
                data['valor_total_porcobrar'] = valor_total_porcobrar()
                data['valor_total_porcobrar_retirados'] = valor_total_porcobrar_retirados()
                data['valor_total_porcobrar_inactivos'] = valor_total_porcobrar_inactivos()
                data['valor_total_porcobrar_activos'] = valor_total_porcobrar_activos()

                data['cantidad_total_porcobrar'] = cantidad_total_porcobrar()
                data['cantidad_total_porcobrar_retirados'] = cantidad_total_porcobrar_retirados()
                data['cantidad_total_porcobrar_inactivos'] = cantidad_total_porcobrar_inactivos()
                data['cantidad_total_porcobrar_activos'] = cantidad_total_porcobrar_activos()

                persona=data['persona']
                if persona.puede_ver_ingresos():
                    return render(request ,"estadisticas/tablasegmentodeudacoord.html" ,  data)

            elif action=='tablasegmentodeudacoordvenc':
                data['title'] = 'Tablas de Deudas por Coordinaciones'

                data['coordinaciones'] = Coordinacion.objects.all().order_by('id')
                data['utiliza_coordinaciones'] = UTILIZA_COORDINACIONES

                #Datos sobre Alumnos Deudores y los Valores correspondientes de deuda
                data['valor_total_deudores'] = valor_total_deudores()
                data['valor_total_deudores_retirados'] = valor_total_deudores_retirados()
                data['valor_total_deudores_inactivos'] = valor_total_deudores_inactivos()
                data['valor_total_deudores_activos'] = valor_total_deudores_activos()

                data['cantidad_total_deudores'] = cantidad_total_deudores()
                data['cantidad_total_deudores_retirados'] = cantidad_total_deudores_retirados()
                data['cantidad_total_deudores_inactivos'] = cantidad_total_deudores_inactivos()
                data['cantidad_total_deudores_activos'] = cantidad_total_deudores_activos()

                persona=data['persona']
                if persona.puede_ver_ingresos():
                    return render(request ,"estadisticas/tablasegmentodeudacoordvenc.html" ,  data)

            elif action=='tablasegmentodeudacoordcred':
                data['title'] = 'Tablas de Valores por Pagar por Coordinaciones'

                data['coordinaciones'] = Coordinacion.objects.all().order_by('id')
                data['utiliza_coordinaciones'] = UTILIZA_COORDINACIONES

                #Datos sobre Alumnos con Creditos y los Valores correspondientes por Pagar
                data['valor_total_creditos'] = valor_total_creditos()
                data['valor_total_creditos_retirados'] = valor_total_creditos_retirados()
                data['valor_total_creditos_inactivos'] = valor_total_creditos_inactivos()
                data['valor_total_creditos_activos'] = valor_total_creditos_activos()

                data['cantidad_total_creditos'] = cantidad_total_creditos()
                data['cantidad_total_creditos_retirados'] = cantidad_total_creditos_retirados()
                data['cantidad_total_creditos_inactivos'] = cantidad_total_creditos_inactivos()
                data['cantidad_total_creditos_activos'] = cantidad_total_creditos_activos()

                persona=data['persona']
                if persona.puede_ver_ingresos():
                    return render(request ,"estadisticas/tablasegmentodeudacoordcred.html" ,  data)

            elif action=='tablasegmentodeudacarr':
                data['title'] = 'Tablas Totales de Creditos y Deudas por Carreras'
                data['carreras'] = Carrera.objects.all().order_by('id')

                #Datos totales sobre Alumnos con Creditos y Deudas y los Valores correspondientes
                data['valor_total_porcobrar'] = valor_total_porcobrar()
                data['valor_total_porcobrar_retirados'] = valor_total_porcobrar_retirados()
                data['valor_total_porcobrar_inactivos'] = valor_total_porcobrar_inactivos()
                data['valor_total_porcobrar_activos'] = valor_total_porcobrar_activos()

                data['cantidad_total_porcobrar'] = cantidad_total_porcobrar()
                data['cantidad_total_porcobrar_retirados'] = cantidad_total_porcobrar_retirados()
                data['cantidad_total_porcobrar_inactivos'] = cantidad_total_porcobrar_inactivos()
                data['cantidad_total_porcobrar_activos'] = cantidad_total_porcobrar_activos()

                persona=data['persona']
                if persona.puede_ver_ingresos():
                    return render(request ,"estadisticas/tablasegmentodeudacarr.html" ,  data)

            elif action=='tablasegmentodeudacarrvenc':
                data['title'] = 'Tablas Totales de Creditos y Deudas por Carreras'
                data['carreras'] = Carrera.objects.all().order_by('id')

                #Datos sobre Alumnos Deudores y los Valores correspondientes de deuda
                data['valor_total_deudores'] = valor_total_deudores()
                data['valor_total_deudores_retirados'] = valor_total_deudores_retirados()
                data['valor_total_deudores_inactivos'] = valor_total_deudores_inactivos()
                data['valor_total_deudores_activos'] = valor_total_deudores_activos()

                data['cantidad_total_deudores'] = cantidad_total_deudores()
                data['cantidad_total_deudores_retirados'] = cantidad_total_deudores_retirados()
                data['cantidad_total_deudores_inactivos'] = cantidad_total_deudores_inactivos()
                data['cantidad_total_deudores_activos'] = cantidad_total_deudores_activos()

                persona=data['persona']
                if persona.puede_ver_ingresos():
                    return render(request ,"estadisticas/tablasegmentodeudacarrvenc.html" ,  data)

            elif action=='tablasegmentodeudacarrcred':
                data['title'] = 'Tablas Totales de Creditos y Deudas por Carreras'
                data['carreras'] = Carrera.objects.all().order_by('id')

                #Datos sobre Alumnos con Creditos y los Valores correspondientes por Pagar
                data['valor_total_creditos'] = valor_total_creditos()
                data['valor_total_creditos_retirados'] = valor_total_creditos_retirados()
                data['valor_total_creditos_inactivos'] = valor_total_creditos_inactivos()
                data['valor_total_creditos_activos'] = valor_total_creditos_activos()

                data['cantidad_total_creditos'] = cantidad_total_creditos()
                data['cantidad_total_creditos_retirados'] = cantidad_total_creditos_retirados()
                data['cantidad_total_creditos_inactivos'] = cantidad_total_creditos_inactivos()
                data['cantidad_total_creditos_activos'] = cantidad_total_creditos_activos()

                persona=data['persona']
                if persona.puede_ver_ingresos():
                    return render(request ,"estadisticas/tablasegmentodeudacarrcred.html" ,  data)

            elif action=='segmentoacademico':
                data['title'] = 'Tablas Academicas por coordinaciones'

                coordinaciones = [c for c in Coordinacion.objects.all().order_by('id') ]
                data['coordinaciones'] = coordinaciones

                #Datos totales de matriculados por sexos
                data['total_matriculados_mujeres'] = total_matriculados_mujeres()
                data['total_matriculados_hombres'] = total_matriculados_hombres()
                data['total_matriculados'] = total_matriculados()

                #Enviar datos de matriculados con becas y discapacidad
                data['cantidad_matriculados_beca'] = cantidad_matriculados_beca()
                data['cantidad_matriculados_discapacidad'] = cantidad_matriculados_discapacidad()

                #Enviar datos totales de matriculados por rango de edades
                data['matriculados_menor_30'] = matriculados_menor_30()
                data['matriculados_31_40'] = matriculados_31_40()
                data['matriculados_41_50'] = matriculados_41_50()
                data['matriculados_51_60'] = matriculados_51_60()
                data['matriculados_mayor_61'] = matriculados_mayor_61()

                return render(request ,"estadisticas/tablasegmentoacademico.html" ,  data)

            elif action=='provcantoncoord':
                data['title'] = 'Tablas de Provincias y Cantones por Coordinaciones'
                if 'fechainicio' in request.GET:
                    fechainicio = date(int(str(request.GET['fechainicio']).split('-')[2]),int(str(request.GET['fechainicio']).split('-')[1]),int(str(request.GET['fechainicio']).split('-')[0]))
                    fechafin = date(int(str(request.GET['fechafin']).split('-')[2]),int(str(request.GET['fechafin']).split('-')[1]),int(str(request.GET['fechafin']).split('-')[0]))
                    coordinaciones = [c for c in Coordinacion.objects.all().order_by('id') if c.cantidad_matriculadosfilt(fechainicio,fechafin)]
                    provincias = [x for x in Provincia.objects.all() if x.cantidad_matriculadosfil(fechainicio,fechafin)]
                    cantones = [y for y in Canton.objects.all() if y.cantidad_matriculadosfil(fechainicio,fechafin)]
                    data['total_matriculados_mujeres'] = total_matriculados_mujeresfil(fechainicio,fechafin)
                    data['total_matriculados_hombres'] = total_matriculados_hombresfil(fechainicio,fechafin)
                    data['total_matriculados'] = total_matriculadosfil(fechainicio,fechafin)

                    data['fechainicio'] = fechainicio
                    data['fechafin'] = fechafin
                    #Para calcular cuantos matriculados por Provincias y por Coordinacioenes
                    listaxprovincia = []
                    provinnull = []
                    for provincia in provincias:
                        fila = []
                        for coordinacion in coordinaciones:
                            fila.append(coordinacion.cantidad_matriculados_provinciafil(provincia,fechainicio,fechafin))

                        listaxprovincia.append((provincia.nombre, fila, provincia.cantidad_matriculadosfil(fechainicio,fechafin), provincia.porciento_matriculadosfil(fechainicio,fechafin)))

                    for coordinacion in coordinaciones:
                        if coordinacion.cantidad_matriculados_provinciafilnull(fechainicio,fechafin):
                            provinnull.append(coordinacion.cantidad_matriculados_provinciafilnull(fechainicio,fechafin))
                    listaxprovincia.append(('PROVINCIA NO ASIGNADA', provinnull, total_matriculadosfilnullprovin(fechainicio,fechafin), total_matriculadosfilprovinporcent(fechainicio,fechafin)))

                    #Para calcular cuantos matriculados por Cantones y por Coordinacioenes
                    listaxcanton = []
                    cantonnull = []
                    for canton in cantones:
                        fila = []
                        for coordinacion in coordinaciones:
                            fila.append(coordinacion.cantidad_matriculados_cantonfil(canton,fechainicio,fechafin))
                        listaxcanton.append((canton.nombre, fila, canton.cantidad_matriculadosfil(fechainicio,fechafin), canton.porciento_matriculadosfil(fechainicio,fechafin)))
                    for coordinacion in coordinaciones:
                        if coordinacion.cantidad_matriculados_cantonfilnull(fechainicio,fechafin):
                            cantonnull.append(coordinacion.cantidad_matriculados_cantonfilnull(fechainicio,fechafin))
                    listaxcanton.append(('CANTON NO ASIGNADO', cantonnull, total_matriculadosfilcanton(fechainicio,fechafin), total_matriculadosfilcantonporcent(fechainicio,fechafin)))
                else:
                    coordinaciones = [c for c in Coordinacion.objects.all().order_by('id') if c.cantidad_matriculados()]
                    provincias = [x for x in Provincia.objects.all() if x.cantidad_matriculados()]
                    cantones = [y for y in Canton.objects.all() if y.cantidad_matriculados()]
                    data['total_matriculados_mujeres'] = total_matriculados_mujeres()
                    data['total_matriculados_hombres'] = total_matriculados_hombres()
                    data['total_matriculados'] = total_matriculados()
                    #Para calcular cuantos matriculados por Provincias y por Coordinacioenes
                    listaxprovincia = []
                    provinnull = []
                    for provincia in provincias:
                        fila = []
                        for coordinacion in coordinaciones:
                            fila.append(coordinacion.cantidad_matriculados_provincia(provincia))
                        listaxprovincia.append((provincia.nombre, fila, provincia.cantidad_matriculados(), provincia.porciento_matriculados()))

                    for coordinacion in coordinaciones:
                        if coordinacion.cantidad_matriculados_provincianull():
                            provinnull.append(coordinacion.cantidad_matriculados_provincianull())
                    listaxprovincia.append(('PROVINCIA NO ASIGNADA', provinnull, total_matriculadosprovinnull(), total_matriculadosprovinporcent()))

                    #Para calcular cuantos matriculados por Cantones y por Coordinacioenes
                    listaxcanton = []
                    cantonnull = []
                    for canton in cantones:
                        fila = []
                        for coordinacion in coordinaciones:
                            fila.append(coordinacion.cantidad_matriculados_canton(canton))
                        listaxcanton.append((canton.nombre, fila, canton.cantidad_matriculados(), canton.porciento_matriculados()))

                    for coordinacion in coordinaciones:
                        if coordinacion.cantidad_matriculados_cantonnull():
                            cantonnull.append(coordinacion.cantidad_matriculados_cantonnull())
                    listaxcanton.append(('CANTON NO ASIGNADO', cantonnull, total_matriculadoscantonnull(), total_matriculadoscantonporcent()))




                data['coordinaciones'] = coordinaciones
                data['provincias'] = provincias
                data['cantones'] = cantones


                data['listaxprovincia']  = listaxprovincia
                data['listaxcanton']  = listaxcanton

                #Datos totales de matriculados por sexos


                return render(request ,"estadisticas/provcantoncoord.html" ,  data)

            elif action=='segmentoacademicocarrera':
                data['title'] = 'Tablas Academicas por carreras'
                carreras = [c for c in Carrera.objects.all().order_by('id') ]
                data['carreras'] = carreras

                #Datos totales de matriculados por sexos
                data['total_matriculados_mujeres'] = total_matriculados_mujeres()
                data['total_matriculados_hombres'] = total_matriculados_hombres()
                data['total_matriculados'] = total_matriculados()

                #Enviar datos de matriculados con becas y discapacidad
                data['cantidad_matriculados_beca'] = cantidad_matriculados_beca()
                data['cantidad_matriculados_discapacidad'] = cantidad_matriculados_discapacidad()

                #Enviar datos totales de matriculados por rango de edades
                data['matriculados_menor_30'] = matriculados_menor_30()
                data['matriculados_31_40'] = matriculados_31_40()
                data['matriculados_41_50'] = matriculados_41_50()
                data['matriculados_51_60'] = matriculados_51_60()
                data['matriculados_mayor_61'] = matriculados_mayor_61()

                return render(request ,"estadisticas/tablasegmentoacademicocarr.html" ,  data)

            elif action=='provcantoncarr':
                data['title'] = 'Tablas de Provincias y Cantones por carreras'
                if 'fechainicio' in request.GET:
                    fechainicio = date(int(str(request.GET['fechainicio']).split('-')[2]),int(str(request.GET['fechainicio']).split('-')[1]),int(str(request.GET['fechainicio']).split('-')[0]))
                    fechafin = date(int(str(request.GET['fechafin']).split('-')[2]),int(str(request.GET['fechafin']).split('-')[1]),int(str(request.GET['fechafin']).split('-')[0]))

                    carreras = [c for c in Carrera.objects.all().order_by('id') if c.mat_carrera2fil(fechainicio,fechafin)]
                    provincias = [x for x in Provincia.objects.all() if x.cantidad_matriculadosfil(fechainicio,fechafin)]
                    cantones = [y for y in Canton.objects.all() if y.cantidad_matriculadosfil(fechainicio,fechafin)]
                    data['total_matriculados_mujeres'] = total_matriculados_mujeresfil(fechainicio,fechafin)
                    data['total_matriculados_hombres'] = total_matriculados_hombresfil(fechainicio,fechafin)
                    data['total_matriculados'] = total_matriculadosfil(fechainicio,fechafin)
                    data['fechainicio'] = fechainicio
                    data['fechafin'] = fechafin
                    #Para calcular cuantos matriculados por Provincias y por Coordinacioenes
                    listaxprovincia = []
                    provinnull = []
                    for provincia in provincias:
                        fila = []
                        for carrera in carreras:
                            fila.append(carrera.cantidad_matriculados_provinciafil(provincia,fechainicio,fechafin))
                        listaxprovincia.append((provincia.nombre, fila, provincia.cantidad_matriculadosfil(fechainicio,fechafin), provincia.porciento_matriculadosfil(fechainicio,fechafin)))
                    for carrera in carreras:
                        if carrera.cantidad_matriculados_provinciafilnull(fechainicio,fechafin):
                            provinnull.append(carrera.cantidad_matriculados_provinciafilnull(fechainicio,fechafin))
                    listaxprovincia.append(('PROVINCIA NO ASIGNADA', provinnull, total_matriculadosfilnullprovin(fechainicio,fechafin), total_matriculadosfilprovinporcent(fechainicio,fechafin)))

                    #Para calcular cuantos matriculados por Cantones y por Coordinacioenes
                    listaxcanton = []
                    cantonnull = []
                    for canton in cantones:
                        fila = []
                        for carrera in carreras:
                            fila.append(carrera.cantidad_matriculados_cantonfil(canton,fechainicio,fechafin))
                        listaxcanton.append((canton.nombre, fila, canton.cantidad_matriculadosfil(fechainicio,fechafin), canton.porciento_matriculadosfil(fechainicio,fechafin)))

                    for carrera in carreras:
                        if carrera.cantidad_matriculados_cantonfilnull(fechainicio,fechafin):
                            cantonnull.append(carrera.cantidad_matriculados_cantonfilnull(fechainicio,fechafin))
                    listaxcanton.append(('CANTON NO ASIGNADO', cantonnull, total_matriculadosfilcanton(fechainicio,fechafin), total_matriculadosfilcantonporcent(fechainicio,fechafin)))

                else:
                    carreras = [c for c in Carrera.objects.all().order_by('id') if c.mat_carrera2()]
                    provincias = [x for x in Provincia.objects.all() if x.cantidad_matriculados()]
                    cantones = [y for y in Canton.objects.all() if y.cantidad_matriculados()]
                    #Datos totales de matriculados por sexos
                    data['total_matriculados_mujeres'] = total_matriculados_mujeres()
                    data['total_matriculados_hombres'] = total_matriculados_hombres()
                    data['total_matriculados'] = total_matriculados()
                    #Para calcular cuantos matriculados por Provincias y por Carreras
                    listaxprovincia = []
                    provinnull = []
                    for provincia in provincias:
                        fila = []
                        for carrera in carreras:
                            fila.append(carrera.cantidad_matriculados_provincia(provincia))
                        listaxprovincia.append((provincia.nombre, fila, provincia.cantidad_matriculados(), provincia.porciento_matriculados()))

                    for carrera in carreras:
                        if carrera.cantidad_matriculados_provincianull():
                            provinnull.append(carrera.cantidad_matriculados_provincianull())
                    listaxprovincia.append(('PROVINCIA NO ASIGNADA', provinnull, total_matriculadosprovinnull(), total_matriculadosprovinporcent()))
                    #Para calcular cuantos matriculados por Cantones y por Carreras
                    listaxcanton = []
                    cantonnull = []
                    for canton in cantones:
                        fila = []
                        for carrera in carreras:
                            fila.append(carrera.cantidad_matriculados_canton(canton))
                        listaxcanton.append((canton.nombre, fila, canton.cantidad_matriculados(), canton.porciento_matriculados()))

                    for carrera in carreras:
                        if carrera.cantidad_matriculados_cantonnull():
                            cantonnull.append(carrera.cantidad_matriculados_cantonnull())
                    listaxcanton.append(('CANTON NO ASIGNADO', cantonnull, total_matriculadoscantonnull(), total_matriculadoscantonporcent()))
                data['carreras'] = carreras


                data['provincias'] = provincias

                data['cantones'] = cantones



                data['listaxprovincia']  = listaxprovincia
                data['listaxcanton']  = listaxcanton



                return render(request ,"estadisticas/provcantoncarr.html" ,  data)


            return HttpResponseRedirect("/estadisticas")
        else:
            data = {'title': 'Estadisticas y Graficos'}
            addUserData(request,data)

            persona=data['persona']
            data['hoy'] = datetime.now().today()
            data['iniciomes'] = data['hoy'] - timedelta(data['hoy'].day - 1)

            # if persona.puede_ver_ingresos():
                #sesiones del dia con algun valor final
            data['sesiones']=[x for x in SesionCaja.objects.filter(fecha=datetime.today()).order_by('caja__nombre') if x.total_sesion()]

            #datos del dia por carreras que tengan al menos un matriculado
            data['carreras']=[x for x in Carrera.objects.all() if x.mat_carrera2()]

            data['utiliza_coordinaciones'] = UTILIZA_COORDINACIONES
            data['coordinaciones'] = Coordinacion.objects.all().order_by('id')
            data['fechahoy'] = datetime.now().date()
            return render(request ,"estadisticas/estadisticas.html" ,  data)
            # else:
            #     return HttpResponseRedirect("/")

