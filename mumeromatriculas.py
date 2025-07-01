#!/usr/bin/env python

import sys,os

# Full path and name to your csv file

SITE_ROOT = os.path.dirname(os.path.realpath(__file__))

csv_filepathname= "Datos.csv"
# Full path to your django project directory
your_djangoproject_home=os.path.split(SITE_ROOT)[0]

sys.path.append(your_djangoproject_home)
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'


from sga.models import *
import csv

dataReader = csv.reader(open(csv_filepathname), delimiter=';')

fin_linea = True

MODO_CARGA_NUMEROS = False
NUM_LINEA = 0
cantidad = 0

failed = open('failed.txt', 'w')
cleaned = open('cleaned.txt', 'w')

if MODO_CARGA_NUMEROS:
    for row in dataReader:
        NUM_LINEA += 1

        if len(row)==0:
            continue

        if fin_linea:
            fin_linea = False
            continue

        cedula = row[0].lstrip().strip()
        numerom = row[1].lstrip().strip()

        if Inscripcion.objects.filter(persona__cedula=cedula).exists():
            inscripcion = Inscripcion.objects.filter(persona__cedula=cedula)[:1].get()
            inscripcion.numerom = int(numerom)
            inscripcion.save()
            # print(str(inscripcion) + ' - Matricula: ' + str(inscripcion.numerom))
            cantidad +=1
        else:
            # print("FAILED: "+str(cedula))
            failed.write(";".join(row)+"\t\t"+str(cedula)+"\r\n")
else:
    inscripciones_sin_numero = Inscripcion.objects.filter(numerom=None)
    ultimo_numero = Inscripcion.objects.filter(numerom__gt=0).latest('id').numerom
    for i in inscripciones_sin_numero:
        i.numerom = ultimo_numero + 1
        i.save()
        # print(str(i) + ' - Matricula: ' + str(i.numerom))
        ultimo_numero+=1
        cantidad +=1

# print(cantidad)

failed.close()
cleaned.close()
