#!/usr/bin/python
# -*- coding: utf-8 -*-
import csv
from datetime import datetime
import time
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders as Encoders
import os
import re
import smtplib
import urllib.request
from django.http import HttpResponseRedirect
from django.shortcuts import render
import unicodedata
from settings import ATS_PATH, EMAIL_HOST, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, MEDIA_ROOT, PROFESORES_GROUP_ID, ALUMNOS_GROUP_ID, SISTEMAS_GROUP_ID, EMAIL_PORT
from sga.commonviews import addUserData
from sga.forms import EnvioCorreoForm
from sga.models import Carrera, NivelMalla, ImgenCorreo, Absentismo, Inscripcion, Persona, Matricula, Nivel, Profesor, EstudiantesXDesertar, Graduado, Egresado, PreInscripcion, Modalidad, Canton, Provincia, Grupo, Sesion, Sexo, Especialidad, RetiradoMatricula
from sga.tasks import send_html_mail
def pre_insc(url_pre,ruta_pre,):
    try:
        url = (url_pre)

        # Crea el archivo dato.txt
        # urllib.urlretrieve("dato.txt")
        urllib.request.urlretrieve(url,ruta_pre)
        #
        # Archivo web
        # SITE_ROOT = os.path.dirname(os.path.realpath(__file__))

        # csv_filepathname= "dato.txt"

        # csv_filepathname="dato.txt"
        csv_filepathname=ruta_pre

        # your_djangoproject_home=os.path.split(SITE_ROOT)[0]

        # sys.path.append(your_djangoproject_home)
        os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

        dataReader = csv.reader(open(csv_filepathname), delimiter=';')


        LINE = -1
        for row in dataReader:
            if row:
                # LINE += 1
                # if LINE==1:
                #     continue
                canton = None
                provincia = None
                if Carrera.objects.filter(nombre=row[0].upper()).exists():
                    carrera = Carrera.objects.filter(nombre=row[0].upper())[:1].get()
                else:
                    carrera = Carrera.objects.all()[:1].get()

                if Modalidad.objects.filter(nombre=row[1].upper()).exists():
                    modalidad= Modalidad.objects.filter(nombre=row[1].upper())[:1].get()
                else:
                    modalidad = Modalidad.objects.all()[:1].get()

                if row[25] != '':
                    if Canton.objects.filter(pk=row[25]).exists():
                        canton= Canton.objects.filter(pk=row[25])[:1].get()
                if row[26] != '':
                    if Provincia.objects.filter(pk=row[26]).exists():
                        provincia= Provincia.objects.filter(pk=row[26])[:1].get()

                # if Sesion.objects.filter(nombre=row[2].upper()).exists():
                #     seccion= Sesion.objects.filter(nombre=row[2].upper())[:1].get()
                # else:
                #     seccion = Sesion.objects.all()[:1].get()

                if Grupo.objects.filter(nombre=row[3].upper()).exists():
                    grupo= Grupo.objects.filter(nombre=row[3].upper())[:1].get()
                    seccion = grupo.sesion
                else:
                    grupo = Grupo.objects.all()[:1].get()
                    seccion = Sesion.objects.all()[:1].get()

                if Sexo.objects.filter(nombre=row[10].upper()).exists():
                    sexo= Sexo.objects.filter(nombre=row[10].upper())[:1].get()
                else:
                    sexo = Sexo.objects.all()[:1].get()

                if Especialidad.objects.filter(nombre=row[17].upper()).exists():
                    especialidad= Especialidad.objects.filter(nombre=row[17].upper())[:1].get()
                else:
                    especialidad = Especialidad.objects.all()[:1].get()

                cedula = (row[8].lstrip().strip()).zfill(10)
                hoy = str(datetime.date(datetime.now()))
                caducidad = (row[20])
                try:
                    if (caducidad>=hoy):
                        if not PreInscripcion.objects.filter(cedula=cedula,carrera=carrera).exists():
                            preinscripcion = PreInscripcion(carrera=carrera,
                                            modalidad=modalidad,
                                            seccion=seccion,
                                            grupo=grupo,
                                            inicio_clases=(row[4]),
                                            nombres=row[5],
                                            apellido1=row[6],
                                            apellido2=row[7],
                                            cedula=cedula,
                                            nacimiento=row[9],
                                            email=(row[11].lower()),
                                            sexo=sexo,
                                            telefono=row[12],
                                            celular=row[14],
                                            colegio=row[16],
                                            especialidad=especialidad,
                                            fecha_registro=row[18],
                                            hora_registro=row[19],
                                            fecha_caducidad=row[20],
                                            calleprincipal=row[22],
                                            callesecundaria=row[23],
                                            numerocasa=row[24],
                                            canton=canton,
                                            provincia=provincia)
                        else:
                            preinscripcion=PreInscripcion.objects.filter(cedula=cedula,carrera=carrera)[:1].get()
                            preinscripcion.carrera=carrera
                            preinscripcion.modalidad=modalidad
                            preinscripcion.grupo=grupo
                            preinscripcion.inicio_clases=row[4]
                            preinscripcion.nombres=row[5]
                            preinscripcion.apellido1=row[6]
                            preinscripcion.apellido2=row[7]
                            preinscripcion.cedula=cedula
                            preinscripcion.nacimiento=row[9]
                            preinscripcion.email=row[11].lower()
                            preinscripcion.sexo=sexo
                            preinscripcion.telefono=row[12]
                            preinscripcion.celular=row[14]
                            preinscripcion.colegio=row[16]
                            preinscripcion.especialidad=especialidad
                            preinscripcion.fecha_registro=row[18]
                            preinscripcion.hora_registro=row[19]
                            preinscripcion.fecha_caducidad=row[20]
                            preinscripcion.calleprincipal=row[22]
                            preinscripcion.callesecundaria=row[23]
                            preinscripcion.numerocasa=row[24]
                            preinscripcion.canton=canton
                            preinscripcion.provincia=provincia

                        preinscripcion.save()
                        # print(preinscripcion.nombres + " " +preinscripcion.apellido1)
                except Exception as ex:
                   pass
    except Exception as ex:
        pass

__author__ = 'jurgiles'

def view(request):
    try:
        if request.method == 'POST':
            action = request.POST['action']
            if action == 'absentos':
                imgencorreo = ''
                try:
                    f = EnvioCorreoForm(request.POST,request.FILES)
                    imagen = ''
                    inscripciones = Inscripcion.objects.filter(persona__usuario__is_active=True,pk__in=Absentismo.objects.filter(materiaasignada__absentismo=True).exclude(finalizado=True).distinct('materiaasignada__matricula__inscripcion').values('materiaasignada__matricula__inscripcion')).order_by('persona__apellido1')
                    correoema = ''
                    c = 0
                    contador = 0
                    if 'prueba' in request.POST:
                        if request.POST['prueba'] == 'on':
                            info = envio_correomod(request.POST['emails'].replace(';',','),request.POST,request.FILES)
                            return HttpResponseRedirect('/enviocorreo?info='+info)
                    for inscrip in inscripciones:
                        contador = contador + 1
                        if inscrip.persona.email:
                            if re.match('^[(a-z0-9\_\-\.)]+@[(a-z0-9\_\-\.)]+\.[(a-z)]{2,15}$',inscrip.persona.email.lower()):
                                c = c + 1
                                correoema = correoema + inscrip.persona.email + ','
                            # correoema = str('jjurgiles@bolivariano.edu.ec,soporteitb@bolivariano.edu.ec,sgallegos@bolivariano.edu.ec,ocastillo@bolivariano.edu.ec,rcardona@bolivariano.edu.ec')
                            if c == 83 or contador == inscripciones.count():
                                if correoema != '':
                                    correoema = correoema + 'jjurgiles@bolivariano.edu.ec,sgallegos@bolivariano.edu.ec,'
                                    info = envio_correomod(correoema,request.POST,request.FILES)
                                    time.sleep(3)
                                    c = 0
                                    correoema = ''
                    # correoema = str('jjurgiles@bolivariano.edu.ec,juan.jose85@hotmail.com')
                    return HttpResponseRedirect('/enviocorreo?info='+info)
                    # return HttpResponseRedirect('/enviocorreo?info=no existe informacion para enviar el correo')
                except Exception as ex:
                    return HttpResponseRedirect('/?info'+str(ex))
            elif action == 'administrativo':
                imgencorreo = ''
                try:
                    f = EnvioCorreoForm(request.POST,request.FILES)
                    imagen = ''
                    gruposexcluidos = [PROFESORES_GROUP_ID,ALUMNOS_GROUP_ID]
                    administrativos = Persona.objects.filter(usuario__is_active=True).exclude(usuario__groups__id__in=gruposexcluidos).exclude(usuario=None).order_by('apellido1')
                    correoema = ''
                    c = 0
                    contador = 0
                    if 'prueba' in request.POST:
                        if request.POST['prueba'] == 'on':
                            info = envio_correomod(request.POST['emails'].replace(';',','),request.POST,request.FILES)
                            return HttpResponseRedirect('/enviocorreo?info='+info)
                    for adminis in administrativos:
                        contador = contador + 1
                        if adminis.email:
                            if re.match('^[(a-z0-9\_\-\.)]+@[(a-z0-9\_\-\.)]+\.[(a-z)]{2,15}$',adminis.email.lower()):
                                c = c + 1
                                correoema = correoema + adminis.email + ','
                            # correoema = str('jjurgiles@bolivariano.edu.ec,soporteitb@bolivariano.edu.ec,sgallegos@bolivariano.edu.ec,ocastillo@bolivariano.edu.ec,rcardona@bolivariano.edu.ec')
                            if c == 83 or contador == administrativos.count():
                                if correoema != '':
                                    correoema = correoema + 'jjurgiles@bolivariano.edu.ec,sgallegos@bolivariano.edu.ec,'
                                    info = envio_correomod(correoema,request.POST,request.FILES)
                                    time.sleep(3)
                                    c = 0
                                    correoema = ''
                    return HttpResponseRedirect('/enviocorreo?info='+info)
                    # return HttpResponseRedirect('/enviocorreo?info=no existe informacion para enviar el correo')
                except Exception as ex:
                    return HttpResponseRedirect('/?info'+str(ex))
            elif action == 'carrera':
                imgencorreo = ''
                try:
                    f = EnvioCorreoForm(request.POST,request.FILES)
                    imagen = ''
                    if Nivel.objects.filter(carrera=request.POST['carrera'],periodo=request.POST['periodo'],nivelmalla=request.POST['nivel']).exists():
                        nivel = Nivel.objects.filter(carrera=request.POST['carrera'],periodo=request.POST['periodo'],nivelmalla=request.POST['nivel'])
                        correoema = ''
                        c = 0
                        if 'prueba' in request.POST:
                            if request.POST['prueba'] == 'on':
                                info = envio_correomod(request.POST['emails'].replace(';',','),request.POST,request.FILES)
                                return HttpResponseRedirect('/enviocorreo?info='+info)
                        for niv in nivel:
                            matricula = Matricula.objects.filter(nivel=niv)
                            contador = 0
                            for matri in matricula:
                                contador = contador + 1
                                if matri.inscripcion.persona.email:
                                    if re.match('^[(a-z0-9\_\-\.)]+@[(a-z0-9\_\-\.)]+\.[(a-z)]{2,15}$',matri.inscripcion.persona.email.lower()):
                                        c = c + 1
                                        correoema = correoema + matri.inscripcion.persona.email + ','
                                    # correoema = str('jjurgiles@bolivariano.edu.ec,soporteitb@bolivariano.edu.ec,sgallegos@bolivariano.edu.ec,ocastillo@bolivariano.edu.ec,rcardona@bolivariano.edu.ec')
                                    if c == 83 or contador == matricula.count():
                                        if correoema != '':
                                            correoema = correoema + 'jjurgiles@bolivariano.edu.ec,sgallegos@bolivariano.edu.ec,'
                                            info = envio_correomod(correoema,request.POST,request.FILES)
                                            time.sleep(3)
                                            c = 0
                                            correoema = ''
                        # correoema = str('jjurgiles@bolivariano.edu.ec,juan.jose85@hotmail.com')
                        # if correoema != '':
                        #     info = envio_correomod(correoema,request.POST,request.FILES)
                        return HttpResponseRedirect('/enviocorreo?info='+info)
                        # return HttpResponseRedirect('/enviocorreo?info=no existe informacion para enviar el correo')
                    return HttpResponseRedirect('/enviocorreo?info=no existe informacion para enviar el correo')
                except Exception as ex:
                    return HttpResponseRedirect('/?info'+str(ex))
            elif action == 'docentes':
                imgencorreo = ''
                try:
                    f = EnvioCorreoForm(request.POST,request.FILES)
                    imagen = ''
                    if Profesor.objects.filter(activo=True).order_by('persona__apellido1').exists():
                        profesores = Profesor.objects.filter(activo=True).order_by('persona__apellido1')
                        correoema = ''
                        c = 0
                        contador = 0
                        if 'prueba' in request.POST:
                            if request.POST['prueba'] == 'on':
                                info = envio_correomod(request.POST['emails'].replace(';',','),request.POST,request.FILES)
                                return HttpResponseRedirect('/enviocorreo?info='+info)
                        for profe in profesores:
                            contador = contador + 1
                            if profe.persona.email:
                                if re.match('^[(a-z0-9\_\-\.)]+@[(a-z0-9\_\-\.)]+\.[(a-z)]{2,15}$',profe.persona.email.lower()):
                                    c = c + 1
                                    correoema = correoema + profe.persona.email + ','
                                # correoema = str('jjurgiles@bolivariano.edu.ec,soporteitb@bolivariano.edu.ec,sgallegos@bolivariano.edu.ec,ocastillo@bolivariano.edu.ec,rcardona@bolivariano.edu.ec')
                                if c == 83 or contador == profesores.count():
                                    if correoema != '':
                                        correoema = correoema + 'jjurgiles@bolivariano.edu.ec,sgallegos@bolivariano.edu.ec,'
                                        info = envio_correomod(correoema,request.POST,request.FILES)
                                        time.sleep(3)
                                        c = 0
                                        correoema = ''
                        # correoema = str('jjurgiles@bolivariano.edu.ec,juan.jose85@hotmail.com')
                        # if correoema != '':
                        #     info = envio_correomod(correoema,request.POST,request.FILES)
                        return HttpResponseRedirect('/enviocorreo?info='+info)
                        # return HttpResponseRedirect('/enviocorreo?info=no existe informacion para enviar el correo')
                    return HttpResponseRedirect('/enviocorreo?info=no existe informacion para enviar el correo')
                except Exception as ex:
                    return HttpResponseRedirect('/?info'+str(ex))
            elif action == 'desertores':
                imgencorreo = ''
                try:
                    f = EnvioCorreoForm(request.POST,request.FILES)
                    imagen = ''
                    if EstudiantesXDesertar.objects.filter(reintegro=False).exists():
                        estudiantesxdesertar = EstudiantesXDesertar.objects.filter(reintegro=False).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')
                        correoema = ''
                        c = 0
                        contador = 0
                        if 'prueba' in request.POST:
                            if request.POST['prueba'] == 'on':
                                info = envio_correomod(request.POST['emails'].replace(';',','),request.POST,request.FILES)
                                return HttpResponseRedirect('/enviocorreo?info='+info)
                        for estudiantesxde in estudiantesxdesertar:
                            contador = contador + 1
                            if estudiantesxde.inscripcion.persona.email:
                                if re.match('^[(a-z0-9\_\-\.)]+@[(a-z0-9\_\-\.)]+\.[(a-z)]{2,15}$',estudiantesxde.inscripcion.persona.email.lower()):
                                    c = c + 1
                                    correoema = correoema + estudiantesxde.inscripcion.persona.email + ','
                                # correoema = str('jjurgiles@bolivariano.edu.ec,soporteitb@bolivariano.edu.ec,sgallegos@bolivariano.edu.ec,ocastillo@bolivariano.edu.ec,rcardona@bolivariano.edu.ec')
                                if c == 83 or contador == estudiantesxdesertar.count():
                                    if correoema != '':
                                        correoema = correoema + 'jjurgiles@bolivariano.edu.ec,sgallegos@bolivariano.edu.ec,'
                                        info = envio_correomod(correoema,request.POST,request.FILES)
                                        time.sleep(3)
                                        c = 0
                                        correoema = ''
                        # correoema = str('jjurgiles@bolivariano.edu.ec,juan.jose85@hotmail.com')
                        # if correoema != '':
                        #     info = envio_correomod(correoema,request.POST,request.FILES)
                        return HttpResponseRedirect('/enviocorreo?info='+info)
                        # return HttpResponseRedirect('/enviocorreo?info=no existe informacion para enviar el correo')
                    return HttpResponseRedirect('/enviocorreo?info=no existe informacion para enviar el correo')
                except Exception as ex:
                    return HttpResponseRedirect('/?info'+str(ex))
            elif action == 'egresados':
                imgencorreo = ''
                try:
                    f = EnvioCorreoForm(request.POST,request.FILES)
                    imagen = ''
                    g=Graduado.objects.all().values('inscripcion')
                    if Egresado.objects.all().exclude(inscripcion__in=g).exists():
                        egresados = Egresado.objects.all().exclude(inscripcion__in=g).order_by('inscripcion__persona')
                        correoema = ''
                        c = 0
                        contador = 0
                        if 'prueba' in request.POST:
                            if request.POST['prueba'] == 'on':
                                info = envio_correomod(request.POST['emails'].replace(';',','),request.POST,request.FILES)
                                return HttpResponseRedirect('/enviocorreo?info='+info)
                        for egresado in egresados:
                            if egresado.inscripcion.carrera.id == int(request.POST['carrera']):
                                contador = contador + 1
                                if egresado.inscripcion.persona.email:
                                    if re.match('^[(a-z0-9\_\-\.)]+@[(a-z0-9\_\-\.)]+\.[(a-z)]{2,15}$',egresado.inscripcion.persona.email.lower()):
                                        c = c + 1
                                        correoema = correoema + egresado.inscripcion.persona.email + ','
                                    # correoema = str('jjurgiles@bolivariano.edu.ec,soporteitb@bolivariano.edu.ec,sgallegos@bolivariano.edu.ec,ocastillo@bolivariano.edu.ec,rcardona@bolivariano.edu.ec')
                                    if c == 83 or contador == egresados.count():
                                        if correoema != '':
                                            correoema = correoema + 'jjurgiles@bolivariano.edu.ec,sgallegos@bolivariano.edu.ec,'
                                            info = envio_correomod(correoema,request.POST,request.FILES)
                                            time.sleep(3)
                                            c = 0
                                            correoema = ''
                        # correoema = str('jjurgiles@bolivariano.edu.ec,juan.jose85@hotmail.com')

                        return HttpResponseRedirect('/enviocorreo?info='+info)
                        # return HttpResponseRedirect('/enviocorreo?info=no existe informacion para enviar el correo')
                    return HttpResponseRedirect('/enviocorreo?info=no existe informacion para enviar el correo')
                except Exception as ex:
                    return HttpResponseRedirect('/?info'+str(ex))
            elif action == 'graduados':
                imgencorreo = ''
                try:
                    f = EnvioCorreoForm(request.POST,request.FILES)
                    imagen = ''
                    if Graduado.objects.filter().exists():
                        graduados = Graduado.objects.filter()
                        correoema = ''
                        c = 0
                        contador = 0
                        if 'prueba' in request.POST:
                            if request.POST['prueba'] == 'on':
                                info = envio_correomod(request.POST['emails'].replace(';',','),request.POST,request.FILES)
                                return HttpResponseRedirect('/enviocorreo?info='+info)
                        for graduado in graduados:
                            if graduado.inscripcion.carrera.id == int(request.POST['carrera']):
                                contador = contador + 1
                                if graduado.inscripcion.persona.email:
                                    if re.match('^[(a-z0-9\_\-\.)]+@[(a-z0-9\_\-\.)]+\.[(a-z)]{2,15}$',graduado.inscripcion.persona.email.lower()):
                                        c = c + 1
                                        correoema = correoema + graduado.inscripcion.persona.email + ','
                                    # correoema = str('jjurgiles@bolivariano.edu.ec,soporteitb@bolivariano.edu.ec,sgallegos@bolivariano.edu.ec,ocastillo@bolivariano.edu.ec,rcardona@bolivariano.edu.ec')
                                    if c == 83 or contador == graduados.count():
                                        if correoema != '':
                                            correoema = correoema + 'jjurgiles@bolivariano.edu.ec,sgallegos@bolivariano.edu.ec,'
                                            info = envio_correomod(correoema,request.POST,request.FILES)
                                            time.sleep(3)
                                            c = 0
                                            correoema = ''
                        # correoema = str('jjurgiles@bolivariano.edu.ec,juan.jose85@hotmail.com')
                        # if correoema != '':
                        #     info = envio_correomod(correoema,request.POST,request.FILES)
                        return HttpResponseRedirect('/enviocorreo?info='+info)
                        # return HttpResponseRedirect('/enviocorreo?info=no existe informacion para enviar el correo')
                    return HttpResponseRedirect('/enviocorreo?info=no existe informacion para enviar el correo')
                except Exception as ex:
                    return HttpResponseRedirect('/?info'+str(ex))
            elif action == 'preinscriptos':
                imgencorreo = ''
                try:
                    f = EnvioCorreoForm(request.POST,request.FILES)
                    imagen = ''
                    hoy = str(datetime.date(datetime.now()))
                    pre_insc('http://www.pedagogia.edu.ec/public/docs/dataformregistro.txt','/var/lib/django/repobucki/media/reportes/dato3.txt')
                    if PreInscripcion.objects.filter(inscrito=False, fecha_caducidad__gte=hoy).exists():
                        preinscritos = PreInscripcion.objects.filter(inscrito=False, fecha_caducidad__gte=hoy).order_by('-fecha_registro')
                        correoema = ''
                        c = 0
                        contador = 0
                        if 'prueba' in request.POST:
                            if request.POST['prueba'] == 'on':
                                info = envio_correomod(request.POST['emails'].replace(';',','),request.POST,request.FILES)
                                return HttpResponseRedirect('/enviocorreo?info='+info)
                        for preinscrito in preinscritos:

                            contador = contador + 1
                            if preinscrito.email:
                                if re.match('^[(a-z0-9\_\-\.)]+@[(a-z0-9\_\-\.)]+\.[(a-z)]{2,15}$',preinscrito.email.lower()):
                                    c = c + 1
                                    correoema = correoema + preinscrito.email + ','
                                # correoema = str('jjurgiles@bolivariano.edu.ec,soporteitb@bolivariano.edu.ec,sgallegos@bolivariano.edu.ec,ocastillo@bolivariano.edu.ec,rcardona@bolivariano.edu.ec')
                                if c == 83 or contador == preinscritos.count():
                                    if correoema != '':
                                        correoema = correoema + 'jjurgiles@bolivariano.edu.ec,sgallegos@bolivariano.edu.ec,'
                                        info = envio_correomod(correoema,request.POST,request.FILES)
                                        time.sleep(3)
                                        c = 0
                                        correoema = ''
                        # correoema = str('jjurgiles@bolivariano.edu.ec,juan.jose85@hotmail.com')
                        # if correoema != '':
                        #     info = envio_correomod(correoema,request.POST,request.FILES)
                        return HttpResponseRedirect('/enviocorreo?info='+info)
                        # return HttpResponseRedirect('/enviocorreo?info=no existe informacion para enviar el correo')
                    return HttpResponseRedirect('/enviocorreo?info=no existe informacion para enviar el correo')
                except Exception as ex:
                    return HttpResponseRedirect('/?info'+str(ex))
            elif action == 'retirados':
                imgencorreo = ''
                try:
                    f = EnvioCorreoForm(request.POST,request.FILES)
                    imagen = ''
                    if RetiradoMatricula.objects.filter(activo=False).exists():
                        retirados = RetiradoMatricula.objects.filter(activo=False).order_by('inscripcion__persona__apellido1')
                        correoema = ''
                        c = 0
                        contador = 0
                        if 'prueba' in request.POST:
                            if request.POST['prueba'] == 'on':
                                info = envio_correomod(request.POST['emails'].replace(';',','),request.POST,request.FILES)
                                return HttpResponseRedirect('/enviocorreo?info='+info)
                        for retirado in retirados:
                            contador = contador + 1
                            if retirado.inscripcion.persona.email:
                                if re.match('^[(a-z0-9\_\-\.)]+@[(a-z0-9\_\-\.)]+\.[(a-z)]{2,15}$',retirado.inscripcion.persona.email.lower()):
                                    c = c + 1
                                    correoema = correoema + retirado.inscripcion.persona.email + ','
                                # correoema = str('jjurgiles@bolivariano.edu.ec,soporteitb@bolivariano.edu.ec,sgallegos@bolivariano.edu.ec,ocastillo@bolivariano.edu.ec,rcardona@bolivariano.edu.ec')
                                if c == 83 or contador == retirados.count():
                                    if correoema != '':
                                        correoema = correoema + 'jjurgiles@bolivariano.edu.ec,sgallegos@bolivariano.edu.ec,'
                                        info = envio_correomod(correoema,request.POST,request.FILES)
                                        time.sleep(3)
                                        c = 0
                                        correoema = ''
                        # correoema = str('jjurgiles@bolivariano.edu.ec,juan.jose85@hotmail.com')
                        # if correoema != '':
                        #     info = envio_correomod(correoema,request.POST,request.FILES)
                        return HttpResponseRedirect('/enviocorreo?info='+info)
                        # return HttpResponseRedirect('/enviocorreo?info=no existe informacion para enviar el correo')
                    return HttpResponseRedirect('/enviocorreo?info=no existe informacion para enviar el correo')
                except Exception as ex:
                    return HttpResponseRedirect('/?info'+str(ex))
        else:
            data = {'title':'Envio de Correo Masivos'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']
                if action == 'absento':
                    form = EnvioCorreoForm()
                    form.for_absentos()
                    data['form'] = form
                    data['accion'] = 'absentos'
                    data['titulo'] = 'Enviar Correo a Estudiantes en Absentismo'
                    return render(request ,"enviocorreo/enviocorreo.html" ,  data)
                elif action == 'administrativo':
                    form = EnvioCorreoForm()
                    form.for_absentos()
                    data['form'] = form
                    data['accion'] = 'administrativo'
                    data['titulo'] = 'Enviar Correo al Personal Administrativo'
                    return render(request ,"enviocorreo/enviocorreo.html" ,  data)
                elif action == 'carrera':
                    form = EnvioCorreoForm()
                    data['form'] = form
                    data['accion'] = 'carrera'
                    data['titulo'] = 'Enviar Correo a Estudiantes x Carrera'
                    return render(request ,"enviocorreo/enviocorreo.html" ,  data)
                elif action == 'docentes':
                    form = EnvioCorreoForm()
                    form.for_absentos()
                    data['form'] = form
                    data['accion'] = 'docentes'
                    data['titulo'] = 'Enviar Correo a Docentes'
                    return render(request ,"enviocorreo/enviocorreo.html" ,  data)
                elif action == 'desertores':
                    form = EnvioCorreoForm()
                    form.for_absentos()
                    data['form'] = form
                    data['accion'] = 'desertores'
                    data['titulo'] = 'Enviar Correo a Estudiantes Desertores'
                    return render(request ,"enviocorreo/enviocorreo.html" ,  data)
                elif action == 'egresados':
                    form = EnvioCorreoForm()
                    form.for_egresados()
                    data['form'] = form
                    data['accion'] = 'egresados'
                    data['titulo'] = 'Enviar Correo a Estudiantes Egresados'
                    return render(request ,"enviocorreo/enviocorreo.html" ,  data)
                elif action == 'graduados':
                    form = EnvioCorreoForm()
                    form.for_egresados()
                    data['form'] = form
                    data['accion'] = 'graduados'
                    data['titulo'] = 'Enviar Correo a Estudiantes Graduados'
                    return render(request ,"enviocorreo/enviocorreo.html" ,  data)
                elif action == 'preinscriptos':
                    form = EnvioCorreoForm()
                    form.for_absentos()
                    data['form'] = form
                    data['accion'] = 'preinscriptos'
                    data['titulo'] = 'Enviar Correo a PRE-INSCRIPTOS'
                    return render(request ,"enviocorreo/enviocorreo.html" ,  data)
                elif action == 'retirados':
                    form = EnvioCorreoForm()
                    form.for_absentos()
                    data['form'] = form
                    data['accion'] = 'retirados'
                    data['titulo'] = 'Enviar Correo a Estudiantes Retirados'
                    return render(request ,"enviocorreo/enviocorreo.html" ,  data)

                return HttpResponseRedirect('/enviocorreo')
            else:
                if 'info' in request.GET:
                    data['info'] = request.GET['info']
                return render(request ,"enviocorreo/enviocorreomenu.html" ,  data)
    except Exception as ex:
        return HttpResponseRedirect('/?info'+str(ex))


def envio_correomod(correoema,POST,FILES):
    imgencorreo = ''
    try:
        hoy = datetime.now().date()
        # msgImage = MIMEImage(archivo_imagen.read())
        # msg = MIMEMultipart('alternative')
        # for valueSearch, valueReplace in dic.iteritems():
        #     POST['asunto'] = POST['asunto'].replace(valueSearch, valueReplace)
        msg = MIMEMultipart()
        msg.set_charset('utf-8')
        msg['To'] = correoema
        msg['From'] = u'Instituto Tecnológico Bolivariano'
        msg['Subject'] = POST['asunto']


        for valueSearch, valueReplace in dic.iteritems():
            POST['correo'] = POST['correo'].replace(valueSearch, valueReplace)


        # msg['Date'] = formatdate(localtime = True)
        #cuerpo del mensaje en HTML y si fuera solo text puede colocar en el 2da parametro 'plain'
        msg.attach(MIMEText('<br/>'+POST['correo']+'<br/>'
                            +'<br/> <p>Nota: Favor no responder a la direcci&oacute;n de correo electr&oacute;nico del remitente.</p>  <br/><br/>'
                            +'<br/><br/>'
                            +'<p class="smaller">Antes de imprimir este mensaje, por favor compruebe que es necesario hacerlo.<p>'
                            +'<p>AHORRE PAPEL Y SALVE UN ARBOL / SAVE A PAPER SAVE A TREE</p>'
                            +'<p class="smaller">'
                            +'Clausula de Confidencialidad: La informaci&oacute;n contenida en el presente mensaje es confidencial,'
                            +'est&aacute; dirigida exclusivamente a su destinatario y no puede ser vinculante.'
                            +'El ITB no se responsabiliza por su uso.'
                            +'Este mensaje est&aacute; protegido por la Ley de Propiedad Intelectual, Ley de Comercio Electr&oacute;nico, Firmas y Mensajes de datos,'
                            +'reglamentos y acuerdos internacionales relacionados.'
                            +'Si usted no es el destinatario de este mensaje, recomendamos su eliminaci&oacute;n inmediata.'
                            +'La distribuci&oacute;n o copia del mismo, est&aacute; prohibida y ser&aacute; sancionada de acuerdo al C&oacute;digo Penal y dem&aacute;s normas aplicables.'
                            +'La transmisi&oacute;n de informaci&oacute;n por correo electr&oacute;nico, no garantiza que la misma sea segura o est&eacute; libre de error, por consiguiente, se recomienda su verificaci&oacute;n.'
                            +'</p><br/><br/>'
                            +'<p>Enviado por el Sistema de Gesti&oacute;n Acad&eacute;mica </p>','html'))

        #adjuntamos fichero de texto pero puede ser cualquer tipo de archivo
        ##cargamos el archivo a adjuntar
        if 'archivo' in FILES:
            imgencorreo = ImgenCorreo(imagen=FILES['archivo'])
            imgencorreo.save()
            fp = open(MEDIA_ROOT+'/'+imgencorreo.imagen.name,'rb')
            adjunto =  MIMEBase('application', "octet-stream")
            #lo insertamos en una variable
            adjunto.set_payload(fp.read())
            fp.close()
            #lo encriptamos en base64 para enviarlo
            Encoders.encode_base64(adjunto)
            #agregamos una cabecera y le damos un nombre al archivo que adjuntamos puede ser el mismo u otro
            # adjunto.add_header('Content-Disposition', 'attachment', filename='2104201601099218002100120010040000489041234567810.xml')

            adjunto.add_header('Content-Disposition', 'attachment; filename= "%s"'%  os.path.basename(MEDIA_ROOT+'/'+imgencorreo.imagen.name))
            #adjuntamos al mensaje
            msg.attach(adjunto)



        #///////////////////////////////////////////////////////////
        ##///////////////////////////////////////////////////////////////
        # href="consultafactura?action=run&direct=true&n=retencion_sri&rt=pdf&retencion={{ d.0.id }}"
        #href="/consultafactura?action=run&direct=true&n=facturacion_electronica&rt=pdf&factura={{ d.0.id }}"
        #/alu_facturacion_electronica?action=run&direct=true&n=factura_sri&rt=pdf&factura={{ d.0.id }}
        dirpdf = ""


        try:
            # inicializamos el stmp para hacer el envio
            server = smtplib.SMTP(EMAIL_HOST,EMAIL_PORT)
            # server.mail()
            # server.rcpt()
            server.starttls()
            # server.ehlo()
            #logeamos con los datos ya seteamos en la parte superior
            server.login('informacionitb@bolivariano.edu.ec','0992180021')
            #el envio
            server.sendmail('informacionitb@bolivariano.edu.ec', correoema.split(",") , msg.as_string())
            #apagamos conexion stmp
            server.quit()
        except Exception as ex:
            if imgencorreo:
                url = MEDIA_ROOT+'/'+imgencorreo.imagen.name
                imgencorreo.delete()
                if os.path.exists(url):
                    os.remove(url)
            return 'Correo No Enviado Vuelva a Intentarlo'
        if imgencorreo:
            url = MEDIA_ROOT+'/'+imgencorreo.imagen.name
            imgencorreo.delete()
            if os.path.exists(url):
                os.remove(url)

        return 'Correo Enviado'
    except Exception as ex:
        if imgencorreo:
            url = MEDIA_ROOT+'/'+imgencorreo.imagen.name
            imgencorreo.delete()
            if os.path.exists(url):
                os.remove(url)
        return str(ex)
dic={
    u"á":u"&aacute;", u"é":u"&eacute;", u"í":u"&iacute;", u"ó":u"&oacute;", u"ú":u"&uacute;",
    u"Á":u"&Aacute;", u"É":u"&Eacute;", u"Í":u"&Iacute;", u"Ó":u"&Oacute;", u"Ú":u"&Uacute;",
    u"à":u"&agrave;", u"è":u"&egrave;", u"ì":u"&igrave;", u"ò":u"&ograve;", u"ù":u"&ugrave;",
    u"À":u"&Agrave;", u"È":u"&Egrave;", u"Ì":u"&Igrave;", u"Ò":u"&Ograve;", u"Ù":u"&Ugrave;",
    u"Â":u"&Acirc;",  u"Ã":u"&Atilde;", u"Ä":u"&Auml;",   u"Å":u"&Aring;", u"Æ":u"&AElig;",
    u"â":u"&acirc;",  u"ã":u"&atilde;", u"ä":u"&auml;",   u"å":u"&aring;", u"æ":u"&aelig;",
    u"Ç":u"&Ccedil;", u"Ê":u"&Ecirc;", u"Ë":u"&Euml;",   u"Î":u"&Icirc;", u"Ï":u"&Iuml;",
    u"Ð":u"&ETH;", u"Ô":u"&Ocirc;", u"Õ":u"&Otilde;",   u"Ö":u"&Ouml;", u"×":u"&times;",u"ß":u"&szlig;",
    u"Ø":u"&Oslash;", u"Û":u"&Ucirc;", u"Ü":u"&Uuml;",   u"Ý":u"&Yacute;", u"Þ":u"&THORN;",
    u"ç":u"&ccedil;", u"ê":u"&ecirc;", u"ë":u"&euml;",   u"î":u"&icirc;", u"÷":u"&divide;", u"ÿ":u"&yuml;",
    u"ø":u"&oslash;", u"û":u"&ucirc;", u"ü":u"&uuml;",   u"ý":u"&yacute;", u"þ":u"&thorn;",
    u"ð":u"&eth;", u"ô":u"&ocirc;", u"õ":u"&otilde;",   u"ö":u"&ouml;", u"ï":u"&iuml;",
    u"ñ":u"&ntilde;", u"Ñ":u"&Ntilde;",u"¡":u"&iexcl;",u"¢":u"&cent;",u"£":u"&pound;",u"¤":u"&curren;",
    u"¥":u"&yen;",u"¦":u"&brvbar;",u"§":u"&sect;",u"¨":u"&uml;",u"©":u"&copy;",u"ª":u"&ordf;",u"«":u"&laquo;",
    u"¬":u"&not;",u"®":u"&reg;",u"¯":u"&macr;",u"°":u"&deg;",u"±":u"&plusmn;",u"²":u"&sup2;",u"³":u"&sup3;",
    u"´":u"&acute;",u"µ":u"&micro;",u"¶":u"&para;",u"·":u"&middot;",u"¸":u"&cedil;",u"¹":u"&sup1;",u"º":u"&ordm;",
    u"»":u"&raquo;",u"¼":u"&frac14;",u"½":u"&frac12;",u"¾":u"&frac34;",u"¿":u"&iquest;",u"€":u"&euro;"}