#!/usr/bin/env python

import sys,os

# Full path and name to your csv file

SITE_ROOT = os.path.dirname(os.path.realpath(__file__))

csv_filepathname="/Users/ernesto/Desktop/profesores2011.txt"
# Full path to your django project directory
your_djangoproject_home=os.path.join(SITE_ROOT, "..")

sys.path.append(your_djangoproject_home)
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'


from settings import DEFAULT_PASSWORD, PROFESORES_GROUP_ID, SEXO_MASCULINO, SEXO_FEMENINO
from sga.models import *
from sga.docentes import calculate_username
import csv

dataReader = csv.reader(open(csv_filepathname), delimiter=',')

FEMENINO = Sexo.objects.get(pk=SEXO_FEMENINO)
MASCULINO = Sexo.objects.get(pk=SEXO_MASCULINO)
TIEMPO_COMPLETO = TiempoDedicacionDocente.objects.get(pk=1)

def convert_fecha(s):
    if '/' in s:
        # Formato 1
        s1 = s.index('/')
        s2 = s.rindex('/')
        mes = int(s[0:s1])
        dia = int(s[s1+1:s2])
        annoS = s[s2+1:]
        anno = int('19'+annoS) if len(annoS)==2 else int(annoS)
        return datetime(anno, mes, dia)
    else:
        return datetime(1980, 11, 21)

CATEGORIA_DOCENTE = {}

LINE = 0

for cat in CategorizacionDocente.objects.all():
    CATEGORIA_DOCENTE[cat.nombre] = cat

for row in dataReader:
    LINE += 1
    if LINE==1:
        continue
    print(repr(row))

    cedula = row[0].strip()
    apellido1 = row[1].strip()
    apellido2 = row[2].strip()
    nombres = row[3].strip()

    sexo = MASCULINO if row[4].strip().upper()=='H' else FEMENINO
    nacionalidad = row[5].strip()
    fecha_nac = convert_fecha(row[6].strip())

    direccion = ''
    telefono = ''
    categoriaS = row[17].strip()
    email = row[18].strip()

    if categoriaS in CATEGORIA_DOCENTE:
        categoria = CATEGORIA_DOCENTE[categoriaS]
    else:
        categoria = CategorizacionDocente(nombre=categoriaS)
        categoria.save()
        CATEGORIA_DOCENTE[categoriaS] = categoria


    activo = True

    persona = Persona(nombres=nombres, apellido1=apellido1, apellido2=apellido2, cedula=cedula,
                        sexo=sexo, telefono=telefono, telefono_conv='',
                        nacionalidad=nacionalidad, nacimiento=fecha_nac,
                        email=email)

    username = calculate_username(persona)
    password = DEFAULT_PASSWORD
    user = User.objects.create_user(username, persona.email, password)
    user.save()
    persona.usuario = user
    persona.save()

    profesor = Profesor(persona=persona,
        activo=activo,
        fechaingreso= datetime.now(),
        dedicacion= TIEMPO_COMPLETO, categoria=categoria)
    profesor.save()

    g = Group.objects.get(pk=PROFESORES_GROUP_ID)
    g.user_set.add(user)
    g.save()
