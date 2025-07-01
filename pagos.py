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


def convertir_fecha(s):
    return datetime(int(s[6:10]), int(s[3:5]), int(s[0:2]))

fin_linea = True

MODO_BORRADO = False     # Borrar las notas ingresadas
MODO_REVISION = False   # Modo de Revision
TIPO_REVISION = 1       # 1 - Cedulas 2 - Completitud de datos
EXPORTAR_LIMPIAS = False
NUM_LINEA = 0

CARRERAS_ARCHIVO = []
CEDULAS_REVISADAS = []

failed = open('failed.txt', 'w')
cleaned = open('cleaned.txt', 'w')

hoy = datetime.today().date()
TIPO_OTRO = TipoOtroRubro.objects.get(pk=4)
# SESION = SesionCaja.objects.get(pk=3)
estado_bool = False


for row in dataReader:
    NUM_LINEA += 1

    if len(row)==0:
        continue

    if MODO_REVISION and TIPO_REVISION==2:

        if len(row)!=4:
            print(str(NUM_LINEA)+" -> "+str(len(row)))
            failed.write(";".join(row)+"\r\n")
        else:
            if EXPORTAR_LIMPIAS:
                cleaned.write(";".join(row)+"\r\n")
        continue

    if not MODO_REVISION:
        print(repr(row))

    if fin_linea:
        fin_linea = False
        continue

    cedula = row[0].lstrip().strip()
    # rubro_texto = row[1].lstrip().strip()
    total = float(row[1].lstrip().strip())

    fechatexto = '21/04/2013'
    try:
        fecha = convertir_fecha(fechatexto)
    except:
        fecha = datetime.now()
        print("ERROR FECHA: ", NUM_LINEA)

    try:
        if MODO_REVISION:
            if TIPO_REVISION==1:
                if not cedula in CEDULAS_REVISADAS:
                    if Inscripcion.objects.filter(Q(persona__cedula=cedula)|Q(persona__pasaporte=cedula)).exists():
#                        print("OK")
                        CEDULAS_REVISADAS.append(cedula)
                    else:
                        print("'%s' ==> " % (cedula),)

                        print("NO EXISTE (linea "+str(NUM_LINEA)+")")
                        CEDULAS_REVISADAS.append(cedula)

        else:
            inscripcion = Inscripcion.objects.get(Q(persona__cedula=cedula)|Q(persona__pasaporte=cedula))
            print(inscripcion.persona.nombre_completo_inverso())
            if total<0:
                rc = ReciboCajaInstitucion(inscripcion=inscripcion, motivo='Migracion Inicial', fecha=fecha, hora=datetime.now().time(), valorinicial=abs(total),saldo=abs(total))
                rc.save()
            else:
                rubro = Rubro(fecha=hoy, valor=total, inscripcion=inscripcion, cancelado=False, fechavence=fecha)
                rubro.save()

                rubrootro = RubroOtro(rubro=rubro, tipo=TIPO_OTRO, descripcion='Rubro por Migracion')
                rubrootro.save()

    except Exception as ex:
        print("FAILED: "+str(ex))
        failed.write(";".join(row)+"\t\t"+str(ex)+"\r\n")

failed.close()
cleaned.close()