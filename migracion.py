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

carreras = {
    'I': Carrera.objects.get(pk=1),
    'F': Carrera.objects.get(pk=2),
    'T': Carrera.objects.get(pk=3),
    'M': Carrera.objects.get(pk=4)

}

modalidades = {
    'P': Modalidad.objects.get(pk=1)
}

sesiones = {
    'M': Sesion.objects.get(pk=1),
    'N': Sesion.objects.get(pk=2),
    'S': Sesion.objects.get(pk=3)
}

modalidad = modalidades['P']
SEDE_PRINCIPAL = Sede.objects.get(pk=1)

LINE = 0
for row in dataReader:
    LINE += 1
    if LINE==1:
        continue

    cedula = (row[0].lstrip().strip()).zfill(10)
    carrera = carreras[row[2].lstrip().strip()]
    sesion = sesiones[row[3].lstrip().strip()]

    paralelo_texto = row[4].lstrip().strip()
    paralelo = row[2].lstrip().strip() + "" + row[3].lstrip().strip() + "" + paralelo_texto

    if Inscripcion.objects.filter(persona__cedula=cedula).exists():
        inscripcion = Inscripcion.objects.filter(persona__cedula=cedula)[:1].get()
        if Grupo.objects.filter(nombre=paralelo).exists():
            grupo = Grupo.objects.filter(nombre=paralelo)[:1].get()
        else :
            grupo = Grupo(carrera=carrera,
                        modalidad=modalidad,
                        sesion=sesion,
                        nombre=paralelo,
                        inicio=datetime.now().today(),
                        fin=datetime.now().today() + timedelta(90),
                        capacidad=40,
                        observaciones='',
                        sede=SEDE_PRINCIPAL)
            grupo.save()

        ig = inscripcion.inscripcion_grupo(grupo)
        ig.grupo = grupo
        ig.save()

        print(inscripcion.persona.nombre_completo())
        print(ig.grupo.nombre)

