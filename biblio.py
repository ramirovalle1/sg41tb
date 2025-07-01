#!/usr/bin/env python

import sys,os

# Full path and name to your csv file

SITE_ROOT = os.path.dirname(os.path.realpath(__file__))

csv_filepathname= "Datos.csv"
# Full path to your django project directory
your_djangoproject_home=os.path.split(SITE_ROOT)[0]

sys.path.append(your_djangoproject_home)
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'


from bib.models import *
import csv


dataReader = csv.reader(open(csv_filepathname), delimiter=';')

SEDE_PRINCIPAL = Sede.objects.get(pk=1)

LINE = 0

failed = open('failed.txt', 'w')

for row in dataReader:
    LINE += 1
    if LINE==1:
        continue

    codigo = row[0].lstrip().strip().upper()
    nombre = row[1].lstrip().strip().upper()
    autor = row[2].lstrip().strip().upper()

    tipo_texto = row[3].lstrip().strip().upper()
    if tipo_texto:
        if TipoDocumento.objects.filter(nombre=tipo_texto).exists():
            tipodoc = TipoDocumento.objects.filter(nombre=tipo_texto)[:1].get()
        else:
            tipodoc = TipoDocumento(nombre=tipo_texto)
            tipodoc.save()
    else:
        tipodoc = TipoDocumento.objects.get(pk=16)

    if row[4].lstrip().strip():
        anno = row[4].lstrip().strip()
    else:
        anno = 0

    if row[5].lstrip().strip():
        copias = row[5].lstrip().strip()
    else:
        copias = 0

    editora = row[6].lstrip().strip().upper()
    codigodewey = row[7].lstrip().strip().upper()
    tutor = row[8].lstrip().strip().upper()

    try:

        if Documento.objects.filter(codigo=codigo).exists():
            documento = Documento.objects.filter(codigo=codigo)[:1].get()
            documento.nombre = nombre
            documento.autor = autor
            documento.tipo = tipodoc
            documento.anno = int(anno)
            documento.copias = int(copias)
            documento.editora = editora
            documento.fisico = True
            documento.sede = SEDE_PRINCIPAL
            documento.codigodewey = codigodewey
            documento.tutor = tutor
            documento.save()
        else:
            documento = Documento(codigo=codigo,
                                  nombre=nombre,
                                  autor=autor,
                                  tipo=tipodoc,
                                  anno=int(anno),
                                  copias=int(copias),
                                  editora=editora,
                                  fisico=True,
                                  sede=SEDE_PRINCIPAL,
                                  codigodewey=codigodewey,
                                  tutor=tutor)
            documento.save()

            print(documento)

    except Exception as ex:
        print("FAILED: "+str(ex))
        failed.write(";".join(row)+"\t\t"+str(ex)+"\r\n")

failed.close()
