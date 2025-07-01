#!/usr/bin/env python

import sys,os

# Full path and name to your csv file

SITE_ROOT = os.path.dirname(os.path.realpath(__file__))

csv_filepathname= "estudiantes.csv"
# Full path to your django project directory
your_djangoproject_home=os.path.split(SITE_ROOT)[0]

sys.path.append(your_djangoproject_home)
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'


from settings import DEFAULT_PASSWORD, ALUMNOS_GROUP_ID
from sga.models import *
from sga.docentes import calculate_username
import csv

dataReader = csv.reader(open(csv_filepathname), delimiter=';')

FEMENINO = Sexo.objects.get(pk=SEXO_FEMENINO)
MASCULINO = Sexo.objects.get(pk=SEXO_MASCULINO)

#meses = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']
meses = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']

CARRERAS = {
    'E': Carrera.objects.get(pk=26),
    'A': Carrera.objects.get(pk=23),
    'C': Carrera.objects.get(pk=8),
    'D': Carrera.objects.get(pk=4),
    'G': Carrera.objects.get(pk=12),
    'M': Carrera.objects.get(pk=17),
    'N': Carrera.objects.get(pk=24),
    'S': Carrera.objects.get(pk=19),
    'T': Carrera.objects.get(pk=25),
    'U': Carrera.objects.get(pk=22)
    }




MODALIDADES = {
    'P': Modalidad.objects.get(pk=1)
}

SESIONES = {
    '3': Sesion.objects.get(pk=10)

}

#SESION_DIURNA_ENFERMERIA = Sesion.objects.get(pk=8)
SEDE_PRINCIPAL = Sede.objects.get(pk=1)

def convert_month(s):
    if s in meses:
        return meses.index(s)+1
    return 1


GUAYAQUIL = Canton.objects.get(pk=100)
GUAYAS = Provincia.objects.get(pk=10)
SIN_SANGRE = TipoSangre.objects.get(pk=10)

first = True
failed = open('failed.txt', 'w')

for row in dataReader:

    # print(repr(row))
    if first:
        first = False
        continue

    cedula = row[0].lstrip().strip()
    identificador = row[1].lstrip().strip()

    nombre_completo = row[2].lstrip().strip().split(" ")
    nombres = " ".join(nombre_completo[2:])
    apellido1 = nombre_completo[0]
    apellido2 = nombre_completo[1]

    sexo = MASCULINO

    fnacimiento = datetime(1993,5,2)

    carrera =  CARRERAS[row[3].lstrip().strip()]
    modalidad = MODALIDADES[row[4].lstrip().strip()]
    sesion = SESIONES[row[5].lstrip().strip()]
    emailtexto = row[6].lstrip().strip()
    telefono = row[7].lstrip().strip()

    direccion = ''

    canton = GUAYAQUIL
    provincia = GUAYAS
    nacionalidad = ''

    tiposangre = SIN_SANGRE

    try:

        if Persona.objects.filter(cedula=cedula).exists():
            persona = Persona.objects.filter(cedula=cedula)[:1].get()
        else:
            persona = Persona(nombres=nombres, apellido1=apellido1, apellido2=apellido2, cedula=cedula, sexo=sexo)
            persona.save()

        persona.nacionalidad = nacionalidad
        persona.email = emailtexto
        persona.nacimiento = fnacimiento
        persona.sexo = sexo
        persona.direccion = direccion
        persona.telefono_conv = telefono

        persona.canton = canton
        persona.provincia = provincia
        persona.sangre = tiposangre
        persona.nombres = nombres
        persona.apellido1 = apellido1
        persona.apellido2 = apellido2

        persona.save()

        username = calculate_username(persona)
        password = DEFAULT_PASSWORD
        if not emailtexto:
            emailtexto = '@'
        user = User.objects.create_user(username, emailtexto, password)
        user.first_name = nombres
        user.last_name = apellido1+" "+apellido2
        user.save()

        persona.usuario = user
        persona.save()

        #Ubicarlo en el Grupo de Alumnos
        g = Group.objects.get(pk=ALUMNOS_GROUP_ID)
        g.user_set.add(user)
        g.save()

        # carrera_texto = row[6].lstrip().strip()
        # sesion_texto = row[7].lstrip().strip()

        # Inscripcion

        # paralelo = row[8].lstrip().strip()


        # especialidad_texto = row[13].lstrip().strip()

        # fingreso = convertir_fecha(row[14].lstrip().strip())
        # if Especialidad.objects.filter(nombre=especialidad_texto).exists():
        #    especialidad = Especialidad.objects.filter(nombre=especialidad_texto)[:1].get()
        # else :
        #    especialidad = Especialidad(nombre=especialidad_texto)
        #    especialidad.save()

        if not Inscripcion.objects.filter(persona=persona).exists():
            inscripcion = Inscripcion(persona=persona,
                                      fecha=datetime.today(),
                                        carrera=carrera,
                                        modalidad=modalidad,
                                        sesion=sesion,
                                        tienediscapacidad=False,
                                        identificador=identificador)
            inscripcion.save()
        else:
            inscripcion = Inscripcion.objects.filter(persona=persona)[:1].get()


        print(inscripcion.persona.nombre_completo())


    except Exception as ex:
        print("FAILED: "+str(ex))
        failed.write(";".join(row)+"\t\t"+str(ex)+"\r\n")

failed.close()
