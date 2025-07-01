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

NUM_LINEA = 0
cantidad = 0

failed = open('failed.txt', 'w')
cleaned = open('cleaned.txt', 'w')

for row in dataReader:
    NUM_LINEA += 1

    if len(row)==0:
        continue

    if fin_linea:
        fin_linea = False
        continue

    parroquia = row[0].lstrip().strip().upper()

    if not Parroquia.objects.filter(nombre=parroquia).exists():
        parroquia = Parroquia(nombre=parroquia)
        parroquia.save()
        print(parroquia)
        cantidad +=1

print(cantidad)

failed.close()
cleaned.close()








