#!/usr/bin/env python
# coding=utf-8

import sys,os

# Full path and name to your csv file

SITE_ROOT = os.path.dirname(os.path.realpath(__file__))

# Full path to your django project directory
your_djangoproject_home=os.path.split(SITE_ROOT)[0]

sys.path.append(your_djangoproject_home)
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

estudiantes_mal_cedula = open('estudiantesmalcedula.txt', 'w')

from sga.models import *

def chequeaDocumento(numero):
    suma = 0
    residuo = 0
    pri = False
    pub = False
    nat = False
    numeroProvincias = 24
    modulo = 11

    try:
        prov = int(numero[:2])
        if prov>numeroProvincias or prov<=0:
            return 'El codigo de la provincia (dos primeros digitos) es invalido'

        # Aqui almacenamos los digitos de la cedula en variables.
        d1 = int(numero[:1])
        d2 = int(numero[1:2])
        d3 = int(numero[2:3])
        d4 = int(numero[3:4])
        d5 = int(numero[4:5])
        d6 = int(numero[5:6])
        d7 = int(numero[6:7])
        d8 = int(numero[7:8])
        d9 = int(numero[8:9])
        d10 = int(numero[9:10])

        # El tercer digito es:
        # 9 para sociedades privadas y extranjeros
        # 6 para sociedades publicas
        # menor que 6 (0,1,2,3,4,5) para personas naturales

        if d3==7 or d3==8:
            return 'El tercer digito ingresado es invalido'

        # Solo para personas naturales (modulo 10)
        if d3 < 6:
            nat = True
            p1 = d1 * 2
            if p1 >= 10:
                p1 -= 9
            p2 = d2 * 1
            if p2 >= 10:
                p2 -= 9
            p3 = d3 * 2
            if p3 >= 10:
                p3 -= 9
            p4 = d4 * 1
            if p4 >= 10:
                p4 -= 9
            p5 = d5 * 2
            if p5 >= 10:
                p5 -= 9
            p6 = d6 * 1
            if p6 >= 10:
                p6 -= 9
            p7 = d7 * 2
            if p7 >= 10:
                p7 -= 9
            p8 = d8 * 1
            if p8 >= 10:
                p8 -= 9
            p9 = d9 * 2
            if p9 >= 10:
                p9 -= 9
            modulo = 10

        # Solo para sociedades publicas (modulo 11)
        # Aqui el digito verficador esta en la posicion 9, en las otras 2 en la pos. 10
        elif d3 == 6:
            pub = True
            p1 = d1 * 3
            p2 = d2 * 2
            p3 = d3 * 7
            p4 = d4 * 6
            p5 = d5 * 5
            p6 = d6 * 4
            p7 = d7 * 3
            p8 = d8 * 2
            p9 = 0

        # Solo para entidades privadas (modulo 11)
        elif d3 == 9:
            pri = True
            p1 = d1 * 4
            p2 = d2 * 3
            p3 = d3 * 2
            p4 = d4 * 7
            p5 = d5 * 6
            p6 = d6 * 5
            p7 = d7 * 4
            p8 = d8 * 3
            p9 = d9 * 2

        suma = p1 + p2 + p3 + p4 + p5 + p6 + p7 + p8 + p9
        residuo = suma % modulo

        # Si residuo=0, dig.ver.=0, caso contrario 10 - residuo
        if residuo == 0:
            digitoVerificador = 0
        else:
            digitoVerificador = modulo - residuo

        # ahora comparamos el elemento de la posicion 10 con el dig. ver.
        if pub==True:
            if digitoVerificador != d9:
                return 'El ruc de la empresa del sector publico es incorrecto.'

            # El ruc de las empresas del sector publico terminan con 0001
            if numero[-4:] != '0001':
                return 'El ruc de la empresa del sector publico debe terminar con 0001'

        elif pri==True:
            if digitoVerificador != d10:
                return 'El ruc de la empresa del sector privado es incorrecto.'

            if numero[-3:] != '001':
                return 'El ruc de la empresa del sector privado debe terminar con 001'

        elif nat==True:
            if digitoVerificador != d10:
                return 'El numero de cedula de la persona natural es incorrecto.'

            if len(numero) >10 and numero[-3:] != '001' :
                return 'El ruc de la persona natural debe terminar con 001'

        return ''

    except Exception as ex:
        print(ex)

inscripciones = Inscripcion.objects.filter(persona__usuario__is_active=True)

for entidad in inscripciones:
    identificacion = entidad.persona.cedula
    print(entidad.persona)

    if not entidad.persona.extranjero:
        if identificacion:
            if len(identificacion) == 10:
                if not '-' in identificacion:
                    if identificacion:
                        chequeo = chequeaDocumento(identificacion)
                        if chequeo != '':
                            # ent = identificacion + chequeo
                            try:
                                estudiantes_mal_cedula.write("Estudiante: " + entidad.persona.nombre_completo_inverso() + " (" + identificacion + ") -> " + chequeo + "\r\n")
                            except:
                                estudiantes_mal_cedula.write("Estudiante: " + entidad.persona.nombre_completo_simple() + " (" + identificacion + ") -> " + chequeo + "\r\n")
                if '-' in identificacion:
                    try:
                        estudiantes_mal_cedula.write("Estudiante: " + entidad.persona.nombre_completo_inverso() + " (" + identificacion + ") -> Error en el numero de cedula, tiene un -" + "\r\n")
                    except:
                        estudiantes_mal_cedula.write("Estudiante: " + entidad.persona.nombre_completo_simple() + " (" + identificacion + ") -> Error en el numero de cedula, tiene un -" + "\r\n")
            else:
                try:
                    estudiantes_mal_cedula.write("Estudiante: " + entidad.persona.nombre_completo_inverso() + " (" + identificacion + ") -> Error en el tamanno de cedula, tiene menos de 10 caracteres" + "\r\n")
                except:
                    estudiantes_mal_cedula.write("Estudiante: " + entidad.persona.nombre_completo_simple() + " (" + identificacion + ") -> Error en el tamanno de cedula, tiene menos de 10 caracteres" + "\r\n")
        else:
            try:
                estudiantes_mal_cedula.write("Cedula esta en BLANCO: " + entidad.persona.nombre_completo_inverso() + "\r\n")
            except:
                estudiantes_mal_cedula.write("Cedula esta en BLANCO: " + entidad.persona.nombre_completo_simple() + "\r\n")


estudiantes_mal_cedula.close()








