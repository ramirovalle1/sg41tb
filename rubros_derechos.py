#!/usr/bin/env python

import sys,os

# Full path and name to your csv file
from settings import TIPO_DERECHOEXAMEN_RUBRO

SITE_ROOT = os.path.dirname(os.path.realpath(__file__))

# Full path to your django project directory
your_djangoproject_home=os.path.split(SITE_ROOT)[0]

sys.path.append(your_djangoproject_home)
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'


from sga.models import *


MODO_BORRADO = False     # Borrar las notas ingresadas
MODO_REVISION = False   # Modo de Revision
TIPO_REVISION = 2

tipo_derecho = TipoOtroRubro.objects.get(pk=TIPO_DERECHOEXAMEN_RUBRO)
failed = open('failed.txt', 'w')


if TIPO_REVISION==1:
    matriculas = Matricula.objects.all()

    for matri in matriculas:
        if not matri.nivel_cerrado():
            inscrp = matri.inscripcion
            repetidas = Matricula.objects.filter(inscripcion=inscrp).count()
            if repetidas>1:
                print(inscrp)


if TIPO_REVISION==2:
    matriculas = Matricula.objects.all()
    hoy = datetime.now().today()
    for matri in matriculas:
        inscripcion = matri.inscripcion
        if not matri.nivel_cerrado():
            try:
                print(inscripcion)
                materiasasig = MateriaAsignada.objects.filter(matricula = matri)
                for ma in materiasasig:
                    asignatura = ma.materia.asignatura.nombre
                    print(asignatura)
                    rubro = Rubro(fecha=hoy,valor=2,inscripcion=inscripcion,cancelado=False,fechavence=hoy+timedelta(7))
                    rubro.save()

                    paralelo = matri.nivel.paralelo
                    rubroo = RubroOtro(rubro=rubro, tipo=tipo_derecho, descripcion=tipo_derecho.nombre+"-"+asignatura+"-"+paralelo)
                    rubroo.save()

            except Exception as ex:
                print("FAILED: "+str(ex))
                failed.write(";"+"-"+"\t\t"+str(ex)+"\r\n")

    failed.close()

