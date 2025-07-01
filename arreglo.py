#!/usr/bin/env python

import sys,os

# Full path and name to your csv file

SITE_ROOT = os.path.dirname(os.path.realpath(__file__))

# csv_filepathname= "plan12.csv"
# Full path to your django project directory
your_djangoproject_home=os.path.split(SITE_ROOT)[0]

sys.path.append(your_djangoproject_home)
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'


from settings import DEFAULT_PASSWORD, ALUMNOS_GROUP_ID, SEXO_MASCULINO, SEXO_FEMENINO, NOTA_ESTADO_APROBADO
from sga.models import *
from sga.docentes import calculate_username
import csv

# dataReader = csv.reader(open(csv_filepathname), delimiter=',')

def convertir_fecha_corta(f):
    s = f.split("/")
    return datetime(int(s[2]), int(s[0]), int(s[1]))

# noexiste = 0
# failed = open('failed.txt', 'w')
#
# for row in dataReader:
#     nombre = row[0].strip()
#     contrato = row[1].strip()
#     inicio = convertir_fecha_corta(row[2].strip()).date()
#     totalapagar = float(row[3].strip())
#     valorespagados = float(row[4].strip())
#     porpagar = float(row[5].strip())
#     materiastomadas = int(row[6].strip())
#     valoresvencidos = float(row[7].strip())
#     vencimiento = convertir_fecha_corta(row[8].strip()).date()
#
#
#     s = nombre.split(", ")
#     apellidos = s[0].split(' ')
#     nombres = s[1]
#
#         porpagar, materiastomadas, valoresvencidos, vencimiento,
#
#     if Inscripcion.objects.filter(persona__apellido1=apellidos[0],
#                                   persona__apellido2=apellidos[1],
#                                   persona__nombres=nombres).exists():
#         inscripcion = Inscripcion.objects.filter(persona__apellido1=apellidos[0],
#                                   persona__apellido2=apellidos[1],
#                                   persona__nombres=nombres)[:1].get()
#
#         plan12 = Plan12Materias(inscripcion=inscripcion,
#                                 numerocontrato=contrato,
#                                 inicio=inicio,
#                                 vencimiento=vencimiento,
#                                 materiastotales=12,
#                                 materiascursadas=materiastomadas,
#                                 valorpormateria=totalapagar/12,
#                                 valortotal=totalapagar,
#                                 valorpagado=valorespagados,
#                                 valorvencido=valoresvencidos)
#         plan12.save()
#
#
#     else:
#         noexiste += 1
#         linea = ",".join(row)
#         failed.write(linea+"\r\n")
#
#


periodo = Periodo.objects.get(pk=3)

lista = []
for m in Materia.objects.filter(nivel__periodo=periodo):
    datos = [m.nivel.nivellibrecoordinacion_set.get().coordinacion.nombre.encode("ascii","ignore"), m.identificacion, m.asignatura.nombre.encode("ascii","ignore")]
    #clases = m.clase_set.all()
    aulas = Aula.objects.filter(clase__materia=m).distinct()
    #datos.append(aulas.count())
    datos.append(m.profesores().encode("ascii","ignore"))
    if aulas:
        datos.append(aulas[0].nombre)
        datos.extend( [ m.materiaasignada_set.count(), aulas[0].capacidad ])
        if m.materiaasignada_set.count()>aulas[0].capacidad:
            datos.append("OVERCAPACITY")
        else:
            datos.append("")
    else:
        datos.append("")
    lista.append(datos)

f = open("materias.csv",'w')

fcsv = csv.writer(f)

for d in lista:
    fcsv.writerow(d)

f.close()