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

#meses = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']
meses = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']

TIPO_ESTADO_APROBADO = 1
TIPO_ESTADO_REPROBADO = 2


def convert_month(s):
    if s in meses:
        return meses.index(s)+1
    return 1

def convertir_fecha(s):
    try:
        if int(s[-2:])<=12:
            return datetime(int(s[-2:])+2000,convert_month(s[3:5]),int(s[:2]))
        return datetime(int(s[-2:])+1900,convert_month(s[3:5]),int(s[:2]))
    except :
        return datetime.now()

fin_linea = True


MODO_BORRADO = False     # Borrar las notas ingresadas
MODO_REVISION = False   # Modo de Revision
TIPO_REVISION = 2       # 1 - MATERIAS, 2 - Cedulas 3 - Completitud de datos
EXPORTAR_LIMPIAS = False
ASIGNATURAS_REVISADAS = []
CEDULAS_REVISADAS = []
NUM_LINEA = 0

failed = open('failed.txt', 'w')
cleaned = open('cleaned.txt', 'w')

for row in dataReader:
    NUM_LINEA += 1

    if len(row)==0:
        continue

    if MODO_REVISION and TIPO_REVISION==3:
        if len(row)!=12:
            print(str(NUM_LINEA)+" -> "+str(len(row)))
            failed.write(";".join(row)+"\r\n")
        else:
            if EXPORTAR_LIMPIAS:
                cleaned.write(";".join(row)+"\r\n")

        continue

    if not MODO_REVISION:
        print(repr(row))

    if fin_linea:
#        cod_1 = row[1].lstrip().strip()
#        cod_2 = row[2].lstrip().strip()
#        cod_3 = row[3].lstrip().strip()
#        cod_4 = row[4].lstrip().strip()
        fin_linea = False
        continue

    cedula_texto = row[0].lstrip().strip()
    cedula = cedula_texto.replace('-', '')
#    n1 = row[1].lstrip().strip()
#    n2 = row[2].lstrip().strip()
#    n3 = row[3].lstrip().strip()
#    n4 = row[4].lstrip().strip()
#    n5 = row[5].lstrip().strip()

#    total = row[6].lstrip().strip()
#    recup = row[7].lstrip().strip()
#    notafinal = row[8].lstrip().strip()


#    nombre = row[1].lstrip().strip()
    materia = (row[2].lstrip().strip()).upper()
    notafinal = row[3].lstrip().strip()
    estado = row[4].lstrip().strip()
    asistencia = row[5].lstrip().strip()
    fecha = convertir_fecha(row[6].lstrip().strip())

    if estado=='A':
        #Tipo Estado APROBADO
        aprobado = True
        estado_int = TIPO_ESTADO_APROBADO
    else:
        #Tipo Estado REPROBADO
        aprobado = False
        estado_int = TIPO_ESTADO_REPROBADO

    try:
        if MODO_REVISION:
            if TIPO_REVISION==1:
                if not materia in ASIGNATURAS_REVISADAS:
                    print('%-40s ==> ' % (materia))
                    if Asignatura.objects.filter(nombre=materia).exists():
                        print('OK')
                        ASIGNATURAS_REVISADAS.append(materia)
                    else:
                        print("NO EXISTE (linea "+str(NUM_LINEA)+")")
                        ASIGNATURAS_REVISADAS.append(materia)
            elif TIPO_REVISION==2:
                if not cedula in CEDULAS_REVISADAS:
                    print('%-20s ==> ' % (cedula),)
                    if Inscripcion.objects.filter(Q(persona__cedula=cedula)|Q(persona__pasaporte=cedula)).exists():
                        print("OK")
                        CEDULAS_REVISADAS.append(cedula)
                    else:
                        print("NO EXISTE (linea "+str(NUM_LINEA)+")")
                        CEDULAS_REVISADAS.append(cedula)

        else:
            if MODO_BORRADO:
                inscripcion = Inscripcion.objects.get(Q(persona__cedula=cedula)|Q(persona__pasaporte=cedula))
                asignatura = Asignatura.objects.get(nombre=materia)

                historicos = HistoricoRecordAcademico.objects.filter(inscripcion=inscripcion, asignatura=asignatura);
                records = RecordAcademico.objects.filter(inscripcion=inscripcion, asignatura=asignatura)

                historicos.delete()
                records.delete()

            else:
                inscripcion = Inscripcion.objects.get(Q(persona__cedula=cedula)|Q(persona__pasaporte=cedula))
                asignatura = Asignatura.objects.get(nombre=materia)

                historico = HistoricoRecordAcademico(inscripcion=inscripcion,
                                                    asignatura=asignatura,
                                                    nota=float(notafinal),
                                                    asistencia=asistencia,
                                                    fecha=fecha,
                                                    aprobada=aprobado,
                                                    convalidacion=False,
                                                    pendiente=False)
                historico.save()

                record = RecordAcademico(inscripcion=historico.inscripcion,
                                        asignatura=historico.asignatura,
                                        nota=historico.nota,
                                        asistencia=historico.asistencia,
                                        fecha=historico.fecha,
                                        aprobada=historico.aprobada,
                                        convalidacion=False,
                                        pendiente=False)
                record.save()

    except Exception as ex:
        print("FAILED: "+str(ex))
        failed.write(";".join(row)+"\t\t"+str(ex)+"\r\n")

failed.close()
cleaned.close()








