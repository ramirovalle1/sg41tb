#!/usr/bin/env python

import sys,os

# Full path and name to your csv file

SITE_ROOT = os.path.dirname(os.path.realpath(__file__))

# csv_filepathname= "plan12.csv"
# Full path to your django project directory
your_djangoproject_home=os.path.split(SITE_ROOT)[0]

sys.path.append(your_djangoproject_home)
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from sga.models import *

def convertir_fecha_corta(f):
    s = f.split("/")
    return datetime(int(s[2]), int(s[0]), int(s[1]))

f = open("notasdecreditos.csv",'w')

for nc in NotaCreditoInstitucion.objects.all().order_by('id'):
    #print(datos)
    datos = str(nc.id) + ' ' + nc.numero + ' ' + nc.fecha.strftime('%d-%m-%Y') + ' ' + str(nc.valor) + ' ' + str(nc.factura) + ' ' + nc.usuario + ' ' + nc.motivo
    f.write(datos + "\r\n")
    # print(str(nc.id))
    print(datos)

f.close()