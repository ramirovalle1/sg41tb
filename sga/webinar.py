from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import json
import os
import smtplib
import unicodedata
from django.contrib.auth.models import User
import xlrd
from django.contrib.admin.models import LogEntry, ADDITION, DELETION, CHANGE
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
import xlwt
from sga.commonviews import addUserData, ip_client_address
from sga.forms import SesionForm, SesionJornadaForm, JornadaForm, TurnoForm, WebinarForm, TipoWebinarForm
from sga.models import SesionJornada, Sesion, Webinar, Inscripcion, Matricula, NivelTutor, Participante, ParticipanteWebinar, Reporte, TipoWebinar, convertir_fecha, Persona
from settings import EMAIL_ACTIVE, MEDIA_ROOT, SITE_ROOT, INCIDENCIA_FACT, HABILITA_APLICA_DESCUE, JR_RUN, JR_JAVA_COMMAND, JR_USEROUTPUT_FOLDER, DATABASES, MEDIA_URL, WEBINAR_PATH
import subprocess
from sga.pro_cronograma import load_file
from sga.reportes import fixParametro

import time

def elimina_tildes(cadena):
    s = ''.join((c for c in unicodedata.normalize('NFD',str(cadena)) if unicodedata.category(c) != 'Mn'))
    return s

def transform_jasperstarter(parametro, request):
    if parametro.tipo == 1 or parametro.tipo == 7:
        return "%s='%s'" % (parametro.nombre, fixParametro(parametro.tipo, elimina_tildes(request.GET[parametro.nombre])))
    else:
        return '%s=%s' % (parametro.nombre, fixParametro(parametro.tipo, request.GET[parametro.nombre]))

def transform_jasperstarter2(parametro, participantewebinar):
    if parametro.nombre == 'participante':
        return '%s=%s' % (parametro.nombre, fixParametro(parametro.tipo, participantewebinar.participante.id))
    else:
        return '%s=%s' % (parametro.nombre, fixParametro(parametro.tipo, participantewebinar.webinar.id))

def mail_enviar_certificado(usuario, pw, ruta):
    smtp_server = 'smtp.gmail.com:587'
    smtp_user = 'webinaritb@itb.edu.ec'
    smtp_pass = 'W3b1n4rs+-'
    email = MIMEMultipart()
    email['To'] = pw.participante.correo
    email['From'] = 'webinaritb@itb.edu.ec'
    email['Subject'] = 'Certificado Webinar ITB'

    message = ""
    try:
        email.attach(MIMEText('<b> Participante: </b>'+ pw.participante.apellidos +' '+  pw.participante.nombres +'<br/> '+
                            '<b> Webinar: </b>'+ pw.webinar.nombre +'<br/> '+
                            '<b> Fecha: </b>'+ str(pw.webinar.fecha) +'<br/> '+
                            '<b> Hora: </b>' + str(pw.webinar.hora) +'<br/><br/> '+
                            '<h4>'+ str('Por favor no responder al remitente.')+'</h4>', 'html'))

    except Exception as ex:
         pass
    # email.attach(load_file('C://itb_sga//repoaka//media//documentos//userreports//lagomez5//certificado_webinar20201124_170948.pdf','prueba.pdf'))
    email.attach(load_file(ruta,'Certificado_Webinar_ITB.pdf'))

    smtp = smtplib.SMTP(smtp_server)
    smtp.starttls()
    smtp.login(smtp_user,smtp_pass)
    try:
        smtp.sendmail('sgaitb@itb.edu.ec', pw.participante.correo.split(","), email.as_string())
    except Exception as ex:
         pass
    smtp.quit()
    print("E-mail enviado!")

class MiPaginador(Paginator):
    def __init__(self, object_list, per_page, orphans=0, allow_empty_first_page=True, rango=5):
        super(MiPaginador,self).__init__(object_list, per_page, orphans=orphans, allow_empty_first_page=allow_empty_first_page)
        self.rango = rango
        self.paginas = []
        self.primera_pagina = False
        self.ultima_pagina = False

    def rangos_paginado(self, pagina):
        left = pagina - self.rango
        right = pagina + self.rango
        if left<1:
            left=1
        if right>self.num_pages:
            right = self.num_pages
        self.paginas = range(left, right+1)
        self.primera_pagina = True if left>1 else False
        self.ultima_pagina = True if right<self.num_pages else False
        self.ellipsis_izquierda = left-1
        self.ellipsis_derecha = right+1

@login_required(redirect_field_name='ret', login_url='/login')
# @secure_module
@transaction.atomic()

def view(request):
    if request.method=='POST':
        action = request.POST['action']

        if action == 'add_webinar':
            prueba = ''
            try:
                contador=0
                f = WebinarForm(request.POST,request.FILES)
                # tipo = TipoWebinar.objects.get(pk=request.POST['tipo'])
                desde = request.POST['fecha']
                hasta = request.POST['hasta']
                fechai = convertir_fecha(desde)
                fechaf = convertir_fecha(hasta)
                usuario = User.objects.get(username=request.user)
                if request.POST['idwebinar']=='':
                    id_webinar=0
                else:
                    id_webinar=request.POST['idwebinar']
                if Webinar.objects.filter(pk=id_webinar).exists():
                    webinar = Webinar.objects.filter(pk=id_webinar)[:1].get()
                    webinar.nombre = request.POST['nombre']
                    webinar.fecha = fechai
                    webinar.fecha_hasta = fechaf
                    webinar.hora = request.POST['hora']
                    # webinar.tipo = tipo
                    webinar.usuario = usuario
                    mensaje = 'Edicion de Webinar'
                    webinar.save()

                else:
                    if Webinar.objects.filter(nombre=request.POST['nombre']).exists():
                        return HttpResponseRedirect('/webinar?info=Ya existe un Webinar con ese nombre')
                    else:
                        webinar = Webinar(nombre=request.POST['nombre'],
                                      fecha=fechai,
                                      fecha_hasta=fechaf,
                                      hora=request.POST['hora'],
                                      activo=True,
                                      # tipo=tipo
                                      usuario = usuario
                        )
                        mensaje = 'Ingreso de nuevo Webinar'
                        webinar.save()

                if 'archivofondo' in request.FILES:
                    webinar.certificado=request.FILES['archivofondo']
                    webinar.save()

                if 'archivo' in request.FILES:
                    webinar.archivobase=request.FILES['archivo']
                    webinar.fechaarchivo=datetime.now()
                    webinar.save()

                    ruta = xlrd.open_workbook(SITE_ROOT + webinar.archivobase.url)
                    hoja1 = ruta.sheet_by_index(0)
                    num_filas1 = hoja1.nrows
                    participantes = []
                    for i in range (num_filas1-1):
                        participantes.append([0]*9)

                    f = 1
                    p = 0
                    for j in range(num_filas1-1):
                        prueba = j
                        participantes[p][0] = elimina_tildes(hoja1.cell_value(f,0).lstrip()).rstrip() #CEDULA
                        participantes[p][1] = elimina_tildes(hoja1.cell_value(f,1).lstrip()).rstrip()
                        participantes[p][2] = elimina_tildes(hoja1.cell_value(f,2).lstrip()).rstrip()
                        participantes[p][3] = elimina_tildes(hoja1.cell_value(f,3).lstrip()).rstrip()
                        participantes[p][4] = elimina_tildes(hoja1.cell_value(f,4).lstrip()).rstrip()

                        f = f+1
                        p = p+1





                    for p in participantes:
                        if not Participante.objects.filter(identificacion=p[0]).exists():
                            participante = Participante(identificacion=p[0], nombres=p[1], apellidos=p[2], correo=p[3], telefono=p[4])
                            participante.save()
                        else:
                            participante = Participante.objects.get(identificacion=p[0])
                        if not ParticipanteWebinar.objects.filter(participante=participante, webinar=webinar).exists():
                            pw = ParticipanteWebinar(participante=participante, webinar=webinar)
                            pw.save()
                            contador = contador+1

                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(webinar).pk,
                    object_id       = webinar.id,
                    object_repr     = force_str(webinar),
                    action_flag     = CHANGE,
                    change_message  = mensaje+' (' + client_address + ')' )

                excel = request.POST['soloexcel']
                if id_webinar == 0 or excel != '':
                    return HttpResponseRedirect('/webinar?info=Se cargaron '+str(contador)+' participantes')
                else:
                    return HttpResponseRedirect('/webinar')

            except Exception as ex:
                print(str(ex)+" - "+str(prueba))
                return HttpResponseRedirect('/webinar?info=Error al ingresar webinar, Verifique informacion en la fila '+str(prueba+2))

        elif action == 'eliminar_webinar':
            result = {}
            try:
                webinar = Webinar.objects.filter(pk=request.POST['idwebinar'])
                if ParticipanteWebinar.objects.filter(webinar=webinar).exists():
                    result['result']  = "No se puede eliminar, existen participantes para este Webinar"
                else:
                    webinar = webinar[:1].get()
                    mensaje = 'Elimina turno'
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(webinar).pk,
                        object_id       = webinar.id,
                        object_repr     = force_str(webinar),
                        action_flag     = CHANGE,
                        change_message  = mensaje+' (' + client_address + ')' )
                    webinar.delete()
                    result['result']  = "ok"

                return HttpResponse(json.dumps(result), content_type="application/json")
            except Exception as e:
                result['result']  = str(e)
                return HttpResponse(json.dumps(result), content_type="application/json")

        elif action=='generar_certificados':
            result = {}
            try:
                webinar = Webinar.objects.get(pk=request.POST['idwebinar'])
                participante_webinar = ParticipanteWebinar.objects.filter(webinar=webinar)
                contador=0
                for pw in participante_webinar:
                    if not os.path.exists(SITE_ROOT+"/media/"+str(pw.certificado)) or not pw.certificado:
                        if generar_certificado(pw):
                            contador = contador+1

                result['result']  = "Se han generado "+str(contador)+" certificados en la Base de Datos del ITB"

                return HttpResponse(json.dumps(result), content_type="application/json")

            except Exception as ex:
                print(ex)
                return HttpResponseRedirect("/")

        elif action == 'enviar_certificados':
            result = {}
            try:
                webinar = Webinar.objects.get(pk=request.POST['idwebinar'])
                pw = ParticipanteWebinar.objects.filter(webinar=webinar)
                for p in pw:
                    ruta = os.path.join(MEDIA_ROOT,str(p.certificado))
                    time.sleep(5)
                    mail_enviar_certificado(request.user, p, ruta)
                result['result']  = "ok"

                return HttpResponse(json.dumps(result), content_type="application/json")
            except Exception as ex:
                print(ex)
                result['result']   = str(ex)
                return HttpResponse(json.dumps(result), content_type="application/json")

        elif action == 'add_tipo_webinar':
            try:
                tipo = TipoWebinar(nombre=str(request.POST['nombre']).upper(),
                                   certificado=request.FILES['archivo'])
                tipo.save()
                return HttpResponseRedirect('/webinar?action=tipos_webinar')
            except Exception as ex:
                print(ex)
                return HttpResponseRedirect('/webinar?info=Error al ingresar tipo de webinar, vuelva a intentarlo')

        elif action == 'print_ejemplo':
            result = {}
            try:
                persona = Persona.objects.filter(usuario__username=request.user)[:1].get()
                webinar = Webinar.objects.get(pk=request.POST['id'])
                if Participante.objects.filter(identificacion=persona.cedula if persona.cedula else persona.pasaporte).exists():
                    participante = Participante.objects.filter(identificacion=persona.cedula if persona.cedula else persona.pasaporte)[:1].get()
                else:
                    participante = Participante(nombres=persona.nombres,
                                                apellidos=persona.apellido1+" "+persona.apellido2,
                                                correo=persona.emailinst,
                                                telefono=persona.telefono,
                                                identificacion=persona.cedula if persona.cedula else persona.pasaporte)
                    participante.save()

                if ParticipanteWebinar.objects.filter(webinar=webinar, participante=participante).exists():
                    pw = ParticipanteWebinar.objects.filter(participante=participante, webinar=webinar)[:1].get()
                else:
                    pw = ParticipanteWebinar(participante=participante, webinar=webinar)
                    pw.save()

                if not os.path.exists(SITE_ROOT+"/media/"+str(pw.certificado)) or not pw.certificado:
                    if generar_certificado(pw):
                        pass
                    else:
                        result['result'] = 'Error al generar certificado'
                        return HttpResponse(json.dumps(result), content_type="application/json")

                result['result']  = "ok"
                result['webinar']  = str(pw.webinar.id)
                result['participante'] = str(pw.participante.id)
                result['certificado'] = str(pw.certificado)
                return HttpResponse(json.dumps(result), content_type="application/json")
            except Exception as ex:
                print("ERROR 1: "+str(ex))
                result['result'] = str(ex)
                return HttpResponse(json.dumps(result), content_type="application/json")

    else:
        data = {'title': 'Listado de Webinars'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action == 'ver_participantes':
                try:
                    webinar = Webinar.objects.filter(pk=request.GET['id'])[:1].get()
                    participantes = ParticipanteWebinar.objects.filter(webinar=webinar)
                    search = None
                    if 's' in request.GET:
                        search = request.GET['s']
                    if search:
                        ss = search.split(' ')
                        while '' in ss:
                            ss.remove('')
                        if len(ss)==1:
                            participantes = participantes.filter(Q(participante__nombres__icontains=search)|Q(participante__apellidos__icontains=search))
                        else:
                            participantes = participantes.filter(Q(participante__nombres__icontains=ss)|Q(participante__apellidos__icontains=ss))

                    data['search'] = search if search else ""
                    data['webinar'] = webinar
                    data['participantes'] = participantes
                    return render(request ,"webinar/participantes.html" ,  data)
                except Exception as ex:
                    print(ex)
                    return render(request ,"webinar/participantes.html" ,  data)

            elif action == 'enviar_certificado':
                try:
                    webinar = Webinar.objects.filter(pk=request.GET['wid'])[:1].get()
                    participante = Participante.objects.filter(pk=request.GET['pid'])[:1].get()
                    pw = ParticipanteWebinar.objects.filter(webinar=webinar, participante=participante)[:1].get()
                    ruta = os.path.join(MEDIA_ROOT,str(pw.certificado))

                    mail_enviar_certificado(request.user, pw, ruta)

                    return HttpResponseRedirect("/webinar?action=ver_participantes&id="+request.GET['wid'])
                except Exception as ex:
                    print(ex)
                    return HttpResponseRedirect("/webinar")

            elif action == 'tipos_webinar':
                data['tipos_webinar'] = None
                data['form'] = TipoWebinarForm
                if TipoWebinar.objects.filter(activo=True).exists():
                    data['tipos_webinar'] = TipoWebinar.objects.filter(activo=True).order_by('-id')
                return render(request ,"webinar/tipo_webinar.html" ,  data)

            elif action == 'ver_imagen':
                print(request.GET)
                tipo = TipoWebinar.objects.get(pk=request.GET['id'])
                data['tipo'] = tipo
                data['DIRECCION_MEDIA'] = MEDIA_ROOT
                return render(request ,"webinar/img.html" ,  data)

        else:
            try:
                search = None
                if 's' in request.GET:
                    search = request.GET['s']
                if search:
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')
                    if len(ss)==1:
                        webinar = Webinar.objects.filter(nombre__icontains=search, activo=True)
                    else:
                        webinar = Webinar.objects.filter(nombre__icontains=ss, activo=True)
                else:
                    webinar = Webinar.objects.filter().order_by('-id')

                data['search'] = search if search else ""
                data['webinars'] = webinar
                data['form'] = WebinarForm(initial={'fecha':datetime.now().date(),'hasta':datetime.now().date()})
                if 'info' in request.GET:
                    data['info'] = request.GET['info']

                return render(request ,"webinar/webinar.html" ,  data)
            except Exception as e:
                print(e)
                return HttpResponseRedirect("/webinar")


def generar_certificado(pw):
    reporte = Reporte.objects.get(nombre='certificado_webinar')
    tipo = 'pdf'
    output_folder = os.path.join(WEBINAR_PATH, 'certificados', str(pw.webinar.id))
    try:
        os.makedirs(output_folder)
    except :
        pass
    d = datetime.now()
    pdfname = reporte.nombre+d.strftime('%Y%m%d_%H%M%S')+'_'+str(pw.participante.id)
    runjrcommand = [JR_JAVA_COMMAND,'-jar',
            os.path.join(JR_RUN, 'jasperstarter.jar'),
             'pr', reporte.archivo.file.name,
             '--jdbc-dir', JR_RUN,
             '-f', tipo,
             '-t', 'postgres',
             '-H', DATABASES['default']['HOST'],
             '-n', DATABASES['default']['NAME'],
             '-u', DATABASES['default']['USER'],
             '-p', DATABASES['default']['PASSWORD'],
             '-o', output_folder + os.sep + pdfname]

    parametros = reporte.parametros()
    paramlist = [transform_jasperstarter2(p, pw) for p in parametros]

    if paramlist:
        runjrcommand.append('-P')
        for parm in paramlist:
            runjrcommand.append(parm)
    try:
        mensaje = ''
        for m in runjrcommand:
            mensaje += ' ' + m
        runjr = subprocess.call(mensaje, shell=True)
    except Exception as ex:
        print("ERROR 1: "+str(ex))
        pw.certificado = None
        pw.save()
        return False

    if runjr != 1:
        sp = os.path.split(reporte.archivo.file.name)
        ruta_certificado = os.path.join('webinars', 'certificados', str(pw.webinar.id), pdfname+"."+tipo)
        pw.certificado = ruta_certificado
        pw.save()
        return True
    pw.certificado = None
    pw.save()
