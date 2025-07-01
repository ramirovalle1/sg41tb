import csv
import os
import smtplib
from datetime import datetime
import json
from decimal import Decimal
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render
import xlwt
from django.utils.encoding import force_str
from fpdf import FPDF

from med.models import PersonaEstadoCivil, PersonaExtension, PersonaFichaMedica, PersonaExamenFisico
from settings import MEDIA_ROOT, DEFAULT_PASSWORD, USA_CORREO_INSTITUCIONAL, EMAIL_ACTIVE, UTILIZA_GRUPOS_ALUMNOS, \
    INSCRIPCION_CONDUCCION, ALUMNOS_GROUP_ID, \
    NIVEL_MALLA_UNO, ID_USUARIO_RUDY, ID_TIPOBECA, CORREO_INSTITUCIONAL, \
    ID_MOTIVO_BECA_NUEVOECUADOR, SITE_ROOT
from sga.commonviews import addUserData, ip_client_address
from sga.funciones import calculate_username
from sga.panel import MiPaginador
from sga.models import TipoIdentificacion, SolicitudPostulacionBeca, Pais, Provincia, TituloInstitucion, Persona, \
    Carrera, Canton, DatosAdicionalPostulacionBeca, Sexo, HorariosCarreraPostulacion, Parroquia, \
    DocumentosPostulacionBeca, elimina_tildes, Grupo, Modalidad, Sesion, Inscripcion, Nacionalidad, \
    EmpresaConvenio, PerfilInscripcion, ProcesoDobleMatricula, DocumentosDeInscripcion, InscripcionGrupo, \
    RubrosConduccion, Rubro, RubroOtro, SolicitudBeca, HistorialGestionBeca, Resolucionbeca, Pago, ConvenioCarrera, \
    TipoAnuncio, Matricula, RecordAcademico, MateriaAsignada
from sga.pro_cronograma import load_file
from socioecon.models import InscripcionFichaSocioEconomicaBeca, ReferenciaPersonal



def nombremesenfermeria(mes):

    if mes==1:
        return 'enero'
    elif mes==2:
        return 'febrero'
    elif mes==3:
        return 'marzo'
    elif mes==4:
        return 'abril'
    elif mes==5:
        return 'mayo'
    elif mes==6:
        return 'junio'
    elif mes==7:
        return 'julio'
    elif mes==8:
        return 'agosto'
    elif mes==9:
        return 'septiembre'
    elif mes==10:
        return 'octubre'
    elif mes==11:
        return 'novimebre'
    elif mes==12:
        return 'diciembre'

def enviarcertificadoinscripcion(solicitudpostulacion):
    try:

        # buscar la inscripcion

        if Inscripcion.objects.filter(persona__cedula=solicitudpostulacion.identificacion,
                                      carrera=solicitudpostulacion.carrera).exclude(persona__cedula=None).exclude(
                persona__cedula='').exists():
            insecontrada = Inscripcion.objects.filter(persona__cedula=solicitudpostulacion.identificacion,
                                                      carrera=solicitudpostulacion.carrera)[:1].get()

            cedula=insecontrada.persona.cedula

        elif Inscripcion.objects.filter(persona__pasaporte=solicitudpostulacion.identificacion,
                                        carrera=solicitudpostulacion.carrera).exclude(persona__pasaporte=None).exclude(
                persona__pasaporte='').exists():
            insecontrada = Inscripcion.objects.filter(persona__pasaporte=solicitudpostulacion.identificacion,
                                                      carrera=solicitudpostulacion.carrera)[:1].get()

            cedula = insecontrada.persona.pasaporte

        user = insecontrada.persona.usuario
        user.set_password(DEFAULT_PASSWORD)
        user.save()



        pdf = FPDF(format='A4')
        pdf.add_page('Portrait')
        pdf.set_font('Arial', 'B', 8)  # Arial bold 8
        pdf.alias_nb_pages(alias='pag_total')



        pdf.image(SITE_ROOT + '/static/images/logo-universitario.png', 10, 15, 60, 25)  # Logo
        pdf.set_font('Arial', 'B', 11)  # Arial bold 8
        pdf.text(70, 22, "INSTITUTO SUPERIOR UNIVERSITARIO BOLIVARIANO DE TECNOLOGÍA")
        pdf.set_font('Arial', '', 8)  # Arial bold 12
        pdf.text(75, 27, "Dirección: VÍCTOR MANUEL RENDÓN 236 Y PEDRO CARBO Teléfonos: 5000175 - 1800-ITBITB")
        pdf.text(110, 32, "Correo: info@bolivariano.edu.ec")
        pdf.text(119, 37, "Web:www.itb.edu.ec")

        fechahoy = datetime.now()
        # fechahoy = fechahoy.strftime('%d/%m/%Y %H:%M:%S%p')  # formato dd/mm/yyyy hh:mm:ss am o fm

        pdf.set_font('Arial', '', 10)  # Arial bold 12
        pdf.text(140, 50,"Guayaquil, " + format(fechahoy.day) + " de " + nombremesenfermeria(fechahoy.month) + ", del " + format(
                     fechahoy.year))

        pdf.set_font('Arial', 'B', 15)  # Arial bold 12
        pdf.text(80, 65, "CERTIFICADO")

        pdf.set_font('Arial', '', 10)  # Arial bold 12
        pdf.set_xy(15, 75)

        pdf.multi_cell(w=190, h=5, txt="Por medio del presente se certifica que  "
                                       "Sr.(a./ta.) " + str(
            insecontrada.persona.nombre_completo_inverso()) + " con  C.I./PASS,  " + str(
            cedula) + " se  encuentra admitido  en la carrera de " + str(
            insecontrada.carrera.nombre) + " en  el grupo " + str(insecontrada.grupo().nombre) + ',  jornada ' + str(
            insecontrada.grupo().sesion) + ", campus " + str(insecontrada.grupo().sede) + ".")

        pdf.set_font('Arial', 'B', 10)  # Arial bold 12
        pdf.text(15, 100, "Importante:")
        pdf.text(15, 106, "Pasos para ingresar al SGA y Correo Institucional")
        pdf.set_font('Arial', '', 10)  # Arial bold 12
        pdf.text(15, 111,"1) Ingresar a la siguiente dirección www.itb.edu.ec, opción Portal Estudiantil")
        pdf.text(15, 116,"2) Su usuario del SGA es: "+str(insecontrada.persona.usuario))
        pdf.text(15, 121,"3) Su contraseña del SGA es: itb")
        pdf.text(15, 127,"4) Cambiar la contraseña en la opción Clave que se encuentra en la parte superior")
        pdf.text(15, 133,"5) Llenar Ficha Médica. Finalizada la ficha médica asistir al Box Médico para realizar valoración médica.")
        pdf.text(15, 138,"6) Para el correo institucional debe ingresar a www.gmail.com Su correo es: " + insecontrada.persona.emailinst +".Este correo")
        pdf.text(18, 143,
                 " institucional está  sincronizado  con  su SGA, al  momento  de  actualizar  la clave en https://sga.itb.edu.ec ,")
        pdf.text(18, 148,"esa será la contraseña del correo institucional.")


        pdf.set_font('Arial', 'B', 10)  # Arial bold 12
        pdf.text(15, 225, "CELULAR: "+str(insecontrada.persona.telefono))
        pdf.text(15, 235, "EMAIL: " + str(insecontrada.persona.email))

        pdf.set_font('Arial', '', 10)  # Arial bold 12
        pdf.text(15, 250, "________________________________________")
        pdf.text(50, 255, "FIRMA")

        pdf.text(15, 265, "NOMMBRE: " + str(insecontrada.persona.nombre_completo_inverso()))
        pdf.text(15, 270, "C.I./PASS: " + str(solicitudpostulacion.identificacion))

        pdf.text(15, 277, "Si tiene algun problema con el acceso a la plataforma, puede enviar un correo a soporteitb@bolivariano.edu.ec")
        pdf.text(15, 282, "o comunicarse al Telf. 5000175 ext 1173-1174-1175-5170")




        d = datetime.now()
        pdfname = str(solicitudpostulacion.identificacion) + '.pdf'
        carpeta = MEDIA_ROOT + '/certificadoinscripcion/'
        try:
            os.makedirs(carpeta)
        except:
            pass


        pdf.output(os.path.join(carpeta, pdfname))



        smtp_server = 'smtp.gmail.com:587'
        smtp_user = 'sgaitb2@itb.edu.ec'
        smtp_pass = 'sgaitb2013$'
        email = MIMEMultipart()
        email['To'] =  solicitudpostulacion.email
        email['From'] = 'sgaitb2@itb.edu.ec'




        email[
           'Subject'] = "PROGRAMA DE BECAS " + solicitudpostulacion.empresaconvenio.nombre +"  EN LA CARRERA DE " + solicitudpostulacion.carrera.nombre + "."

        try:
            email.attach(MIMEText(
                '<h3>' + str('FELICITACIONES!!!!') + '</h3><br>' +
                '<h4>' + str(
                    'USTED SE ENCUENTRA MATRICULADO COMO ESTUDIANTE DEL ITB Y REGISTRADO EN EL SISTEMA DE GESTION ACADEMICA. PARA MAYOR INFORMACION LEA EL ARCHIVO ADJUNTO.') + '</h4>' +
                '<h4>' + str('BIENVENIDO.') + '</h4><br><br>' +

                '<h4>' + str(
                    '(Las tildes han sido omitidas intencionalmente para evitar problemas de lectura).') + '</h4><br><br>' +

                '<h4>' + str('Por favor no responder al remitente.') + '</h4>'
                , 'html'))

        except Exception as ex:
            pass
        # email.attach(load_file('C://repoaka//media//reportes_excel//'+nombre ,'listadoalumnos.xls'))
        email.attach(load_file(MEDIA_ROOT + '/certificadoinscripcion/' + pdfname, 'certificadoinscripcion.pdf'))
        smtp = smtplib.SMTP(smtp_server)
        smtp.starttls()
        smtp.login(smtp_user, smtp_pass)
        # enviomailstr=str('floresvillamarinm@gmail.com')
        enviomailstr=str(solicitudpostulacion.email)

        try:
            smtp.sendmail('sgaitb2@itb.edu.ec', enviomailstr.split(","), email.as_string())
        except Exception as ex:
            pass
        smtp.quit()
        print
        "E-mail enviado!"

    except Exception as ex:
        print
        str(ex)
        return HttpResponse(json.dumps({"result": "ok"}), content_type="application/json")

def view(request):
    if request.method == 'POST':
        action = request.POST['action']
        if action == 'generar_excel':
            try:



                titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                titulo.font.height = 20*11
                titulo2.font.height = 20*11
                subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                subtitulo.font.height = 20*10
                wb = xlwt.Workbook()
                ws = wb.add_sheet('Listado',cell_overwrite_ok=True)

                tit = TituloInstitucion.objects.all()[:1].get()
                ws.write_merge(0, 0,0,14, tit.nombre , titulo2)
                ws.write_merge(1, 1,0,14, 'LISTADO DE POSTULANTES DE BECAS ', titulo2)
                fila=5
                soli = SolicitudPostulacionBeca.objects.filter(empresaconvenio_id=int(request.POST['empresaconvenio_id'])).order_by('fecha','apellidos','nombres')
                if soli.exists():

                    ws.write(fila, 0,  'FECHA', titulo)
                    ws.write(fila, 1, 'ACTUALIZADO', titulo)
                    ws.write(fila, 2,  'NUMERO DE CEDULA', titulo)
                    ws.write(fila, 3,  'NOMBRES APELLIDOS DEL BECARIO', titulo)
                    ws.write(fila, 4,  'ESTADO CIVIL', titulo)
                    ws.write(fila, 5,  'TELEFONO CONVENCIONAL', titulo)
                    ws.write(fila, 6,  'TELEFONO CELULAR', titulo)
                    ws.write(fila, 7,  'CORREO ELECTRONICO', titulo)
                    ws.write(fila, 8,  'REFERENCIA GEOGRAFICA', titulo)
                    ws.write(fila, 9,  'PAIS', titulo)
                    ws.write(fila, 10,  'PROVINCIA', titulo)
                    ws.write(fila, 11, 'PARROQUIA', titulo)
                    ws.write(fila, 12, 'CANTON', titulo)
                    ws.write(fila, 13, 'CALLE PRINCIPAL', titulo)
                    ws.write(fila, 14, 'CALLE SECUNDARIA', titulo)
                    ws.write(fila, 15, 'NRO.DE CASA', titulo)

                    ws.write(fila, 16, 'NUMERO DE CEDULA', titulo)
                    ws.write(fila, 17, 'NOMBRES APELLIDOS DEL CONYUGE BECARIO', titulo)
                    ws.write(fila, 18, 'ESTADO CIVIL', titulo)
                    ws.write(fila, 19, 'TELEFONO CONVENCIONAL', titulo)
                    ws.write(fila, 20, 'TELEFONO CELULAR', titulo)
                    ws.write(fila, 21, 'CORREO ELECTRONICO', titulo)
                    ws.write(fila, 22, 'REFERENCIA GEOGRAFICA', titulo)
                    ws.write(fila, 23, 'PAIS', titulo)
                    ws.write(fila, 24, 'PROVINCIA', titulo)
                    ws.write(fila, 25, 'PARROQUIA', titulo)
                    ws.write(fila, 26, 'CANTON', titulo)
                    ws.write(fila, 27, 'CALLE PRINCIPAL', titulo)
                    ws.write(fila, 28, 'CALLE SECUNDARIA', titulo)
                    ws.write(fila, 29, 'NRO.DE CASA', titulo)

                    ws.write(fila, 30, 'NUMERO DE CEDULA', titulo)
                    ws.write(fila, 31, 'NOMBRES APELLIDOS DEL RESPONSABLE SOLIDARIO', titulo)
                    ws.write(fila, 32, 'ESTADO CIVIL', titulo)
                    ws.write(fila, 33, 'TELEFONO CONVENCIONAL', titulo)
                    ws.write(fila, 34, 'TELEFONO CELULAR', titulo)
                    ws.write(fila, 35, 'CORREO ELECTRONICO', titulo)
                    ws.write(fila, 36, 'REFERENCIA GEOGRAFICA', titulo)
                    ws.write(fila, 37, 'PAIS', titulo)
                    ws.write(fila, 38, 'PROVINCIA', titulo)
                    ws.write(fila, 39, 'PARROQUIA', titulo)
                    ws.write(fila, 40, 'CANTON', titulo)
                    ws.write(fila, 41, 'CALLE PRINCIPAL', titulo)
                    ws.write(fila, 42, 'CALLE SECUNDARIA', titulo)
                    ws.write(fila, 43, 'NRO.DE CASA', titulo)

                    ws.write(fila, 44, 'NUMERO DE CEDULA', titulo)
                    ws.write(fila, 45, 'NOMBRES APELLIDOS DEL CONYUGE SOLIDARIO', titulo)
                    ws.write(fila, 46, 'ESTADO CIVIL', titulo)
                    ws.write(fila, 47, 'TELEFONO CONVENCIONAL', titulo)
                    ws.write(fila, 48, 'TELEFONO CELULAR', titulo)
                    ws.write(fila, 49, 'CORREO ELECTRONICO', titulo)
                    ws.write(fila, 50, 'REFERENCIA GEOGRAFICA', titulo)
                    ws.write(fila, 51, 'PAIS', titulo)
                    ws.write(fila, 52, 'PROVINCIA', titulo)
                    ws.write(fila, 53, 'PARROQUIA', titulo)
                    ws.write(fila, 54, 'CANTON', titulo)
                    ws.write(fila, 55, 'CALLE PRINCIPAL', titulo)
                    ws.write(fila, 56, 'CALLE SECUNDARIA', titulo)
                    ws.write(fila, 57, 'NRO.DE CASA', titulo)
                    ws.write(fila, 58, 'CARRERA', titulo)

                    ws.write(fila, 59, 'JORNADA', titulo)
                    ws.write(fila, 60, 'INSCRITO', titulo)
                    ws.write(fila, 61, 'GRUPO', titulo)
                    ws.write(fila, 62, 'CARRERA ANTERIORMENTE', titulo)
                    ws.write(fila, 63, 'MEDIO TE ENTERASTES', titulo)



                    for r in soli:

                        fila=fila+1
                        ws.write(fila, 0, str(r.fecha))
                        ws.write(fila, 1, str('SI') if r.actualizado else str('NO'))
                        ws.write(fila, 2, str(r.identificacion))
                        ws.write(fila, 3, str(r.nombres)+ str(' ') +str(r.apellidos))
                        ws.write(fila, 4, str(r.estadocivil.nombre) if r.estadocivil else str('SIN ESTADO CIVIL'))
                        ws.write(fila, 5, str(r.telefono) if r.telefono else str(''))
                        ws.write(fila, 6, str(r.celular) if r.celular else str(''))
                        ws.write(fila, 7, str(r.email) if r.email else str(''))
                        ws.write(fila, 8, str(r.referencia) if r.referencia else str(''))
                        ws.write(fila, 9, str(r.pais.nombre) if r.pais else str(''))
                        ws.write(fila, 10, str(r.provincia.nombre) if r.provincia else str(''))
                        ws.write(fila, 11, str(r.parroquia.nombre) if r.parroquia else str(''))
                        ws.write(fila, 12, str(r.ciudad.nombre) if r.ciudad else str(''))
                        ws.write(fila, 13, str(r.calleprincipal) if r.calleprincipal else str(''))
                        ws.write(fila, 14, str(r.callesecundaria) if r.callesecundaria else str(''))
                        ws.write(fila, 15, str(r.numerocasa) if r.numerocasa else str(''))
                        ws.write(fila, 58, str(r.carrera.nombre) if r.carrera else str('NO'))
                        ws.write(fila, 59, str(r.nombrejornada()) if r.jornada else str('SIN JORNDA'))
                        ws.write(fila, 60, str("SI") if r.inscrito else str('NO'))
                        ws.write(fila, 61, str(r.nombregrupo()) if r.grupo>0 else str(''))
                        if  r.inscrito:
                            ws.write(fila, 62, str(Inscripcion.objects.filter(persona__cedula=r.identificacion).first().carrera.nombre) if Inscripcion.objects.filter(persona__cedula=r.identificacion).count()>2 else str(''))
                        else:
                            ws.write(fila, 62, str(Inscripcion.objects.filter(
                                persona__cedula=r.identificacion).first().carrera.nombre) if Inscripcion.objects.filter(
                                persona__cedula=r.identificacion) else str(''))

                        ws.write(fila, 63, str(r.anuncio.descripcion) if r.anuncio else str(''))

                        # datos del conyuge del becario

                        if DatosAdicionalPostulacionBeca.objects.filter(solicitudpostulacion=r,
                                                                        tipoadicion=3).exists():
                            datosConyube = DatosAdicionalPostulacionBeca.objects.filter(
                                solicitudpostulacion=r, tipoadicion=3)[:1].get()

                            ws.write(fila, 16, str(datosConyube.identificacion))
                            ws.write(fila, 17, str(datosConyube.nombres) + str(' ') + str(datosConyube.apellidos))
                            ws.write(fila, 18, str(datosConyube.estadocivil.nombre) if datosConyube.estadocivil else str('SIN ESTADO CIVIL'))
                            ws.write(fila, 19, str(datosConyube.telefono) if datosConyube.telefono else str(''))
                            ws.write(fila, 20, str(datosConyube.celular) if datosConyube.celular else str(''))
                            ws.write(fila, 21, str(datosConyube.email) if datosConyube.email else str(''))
                            ws.write(fila, 22, str(datosConyube.referencia) if datosConyube.referencia else str(''))
                            ws.write(fila, 23, str(datosConyube.pais.nombre) if datosConyube.pais else str(''))
                            ws.write(fila, 24, str(datosConyube.provincia.nombre) if datosConyube.provincia else str(''))
                            ws.write(fila, 25, str(datosConyube.parroquia.nombre) if datosConyube.parroquia else str(''))
                            ws.write(fila, 26, str(datosConyube.ciudad.nombre) if datosConyube.ciudad else str(''))
                            ws.write(fila, 27, str(datosConyube.calleprincipal) if datosConyube.calleprincipal else str(''))
                            ws.write(fila, 28, str(datosConyube.callesecundaria) if datosConyube.callesecundaria else str(''))
                            ws.write(fila, 29, str(datosConyube.numerocasa) if datosConyube.numerocasa else str(''))
                        else:

                            ws.write(fila, 16, str(''))
                            ws.write(fila, 17, str(''))
                            ws.write(fila, 18, str(''))
                            ws.write(fila, 19, str(''))
                            ws.write(fila, 20, str(''))
                            ws.write(fila, 21, str(''))
                            ws.write(fila, 22, str(''))
                            ws.write(fila, 23, str(''))
                            ws.write(fila, 24,str(''))
                            ws.write(fila, 25,str(''))
                            ws.write(fila, 26, str(''))
                            ws.write(fila, 27,str(''))
                            ws.write(fila, 28,str(''))
                            ws.write(fila, 29, str(''))

                        # datos del responsable solidario
                        if DatosAdicionalPostulacionBeca.objects.filter(solicitudpostulacion=r,
                                                                        tipoadicion=1).exists():
                            datosrep = DatosAdicionalPostulacionBeca.objects.filter(solicitudpostulacion=r,
                                                                                    tipoadicion=1)[:1].get()

                            ws.write(fila, 30, str(datosrep.identificacion))
                            ws.write(fila, 31, str(datosrep.nombres) + str(' ') + str(datosrep.apellidos))
                            ws.write(fila, 32,
                                     str(datosrep.estadocivil.nombre) if datosrep.estadocivil else str(
                                         'SIN ESTADO CIVIL'))
                            ws.write(fila, 33, str(datosrep.telefono) if datosrep.telefono else str(''))
                            ws.write(fila, 34, str(datosrep.celular) if datosrep.celular else str(''))
                            ws.write(fila, 35, str(datosrep.email) if datosrep.email else str(''))
                            ws.write(fila, 36, str(datosrep.referencia) if datosrep.referencia else str(''))
                            ws.write(fila, 37, str(datosrep.pais.nombre) if datosrep.pais else str(''))
                            ws.write(fila, 38,
                                     str(datosrep.provincia.nombre) if datosrep.provincia else str(''))
                            ws.write(fila, 39,
                                     str(datosrep.parroquia.nombre) if datosrep.parroquia else str(''))
                            ws.write(fila, 40, str(datosrep.ciudad.nombre) if datosrep.ciudad else str(''))
                            ws.write(fila, 41,
                                     str(datosrep.calleprincipal) if datosrep.calleprincipal else str(''))
                            ws.write(fila, 42,
                                     str(datosrep.callesecundaria) if datosrep.callesecundaria else str(''))
                            ws.write(fila, 43, str(datosrep.numerocasa) if datosrep.numerocasa else str(''))

                        if datosrep.estadocivil_id == 2:
                            if DatosAdicionalPostulacionBeca.objects.filter(solicitudpostulacion=r,
                                                                            tipoadicion=2,pertenece=datosrep.id).exists():

                                datosConyubeSolidario = DatosAdicionalPostulacionBeca.objects.filter(
                                    solicitudpostulacion=r, tipoadicion=2,pertenece=datosrep.id)[:1].get()

                                ws.write(fila, 44, str(datosConyubeSolidario.identificacion))
                                ws.write(fila, 45, str(datosConyubeSolidario.nombres) + str(' ') + str(datosConyubeSolidario.apellidos))
                                ws.write(fila, 46,
                                         str(datosConyubeSolidario.estadocivil.nombre) if datosConyubeSolidario.estadocivil else str(
                                             'SIN ESTADO CIVIL'))
                                ws.write(fila, 47, str(datosConyubeSolidario.telefono) if datosConyubeSolidario.telefono else str(''))
                                ws.write(fila, 48, str(datosConyubeSolidario.celular) if datosConyubeSolidario.celular else str(''))
                                ws.write(fila, 49, str(datosConyubeSolidario.email) if datosConyubeSolidario.email else str(''))
                                ws.write(fila, 50, str(datosConyubeSolidario.referencia) if datosConyubeSolidario.referencia else str(''))
                                ws.write(fila, 51, str(datosConyubeSolidario.pais.nombre) if datosConyubeSolidario.pais else str(''))
                                ws.write(fila, 52,
                                         str(datosConyubeSolidario.provincia.nombre) if datosConyubeSolidario.provincia else str(''))
                                ws.write(fila, 53,
                                         str(datosConyubeSolidario.parroquia.nombre) if datosConyubeSolidario.parroquia else str(''))
                                ws.write(fila, 54, str(datosConyubeSolidario.ciudad.nombre) if datosConyubeSolidario.ciudad else str(''))
                                ws.write(fila, 55,
                                         str(datosConyubeSolidario.calleprincipal) if datosConyubeSolidario.calleprincipal else str(''))
                                ws.write(fila, 56,
                                         str(datosConyubeSolidario.callesecundaria) if datosConyubeSolidario.callesecundaria else str(''))
                                ws.write(fila, 57, str(datosConyubeSolidario.numerocasa) if datosConyubeSolidario.numerocasa else str(''))

                            else:

                                ws.write(fila, 44, str(''))
                                ws.write(fila, 45, str(''))
                                ws.write(fila, 46, str(''))
                                ws.write(fila, 47, str(''))
                                ws.write(fila, 48, str(''))
                                ws.write(fila, 49, str(''))
                                ws.write(fila, 50, str(''))
                                ws.write(fila, 51, str(''))
                                ws.write(fila, 52, str(''))
                                ws.write(fila, 53, str(''))
                                ws.write(fila, 54, str(''))
                                ws.write(fila, 55, str(''))
                                ws.write(fila, 56, str(''))
                                ws.write(fila, 57, str(''))


                    else:

                        ws.write(fila, 30, str(''))
                        ws.write(fila, 31, str(''))
                        ws.write(fila, 32, str(''))
                        ws.write(fila, 33, str(''))
                        ws.write(fila, 34, str(''))
                        ws.write(fila, 35, str(''))
                        ws.write(fila, 36, str(''))
                        ws.write(fila, 37, str(''))
                        ws.write(fila, 38, str(''))
                        ws.write(fila, 39, str(''))
                        ws.write(fila, 40, str(''))
                        ws.write(fila, 41, str(''))
                        ws.write(fila, 42, str(''))
                        ws.write(fila, 43, str(''))












                nombre ='postulantesbecas'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}), content_type="application/json")

            except Exception as ex:
                print(ex)

        elif action == 'buscarcantones':
            try:
                data = {'title': ''}
                listCan = []
                listCan.append({"id": 0, "nombre": "TODOS"})
                if Canton.objects.filter(provincia__id=int(request.POST['idprovincia'])).order_by("nombre").exists():
                    for g in Canton.objects.filter(provincia__id=int(request.POST['idprovincia'])).order_by("nombre"):
                        listCan.append({"id": g.id, "nombre": g.nombre})
                data['listacanton'] = listCan
                data['result'] = 'ok'
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}), content_type="application/json")

        elif action == 'aprobarpostulacion':
            try:
                data = {'title': ''}
                solicitudbeca = SolicitudPostulacionBeca.objects.get(id=int(request.POST['idsoli']))
                solicitudbeca.aprobado=True
                solicitudbeca.motivoaprobacion=elimina_tildes(request.POST['txtmotivo']).upper()
                solicitudbeca.save()

                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                    user_id=request.user.pk,
                    content_type_id=ContentType.objects.get_for_model(solicitudbeca).pk,
                    object_id=solicitudbeca.id,
                    object_repr=force_str(solicitudbeca),
                    action_flag=ADDITION,
                    change_message=' Aprobacion de la postulacion beca nuevo ecuador (' + client_address + ')')

                data['result'] = 'ok'
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}), content_type="application/json")

        elif action == 'cambiocarrerasolicitud':
            try:
                data = {'title': ''}
                solicitudbeca = SolicitudPostulacionBeca.objects.get(id=int(request.POST['idsolicitud']))
                solicitudbeca.carrera_id=int(request.POST['carrera'])
                solicitudbeca.save()

                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                    user_id=request.user.pk,
                    content_type_id=ContentType.objects.get_for_model(solicitudbeca).pk,
                    object_id=solicitudbeca.id,
                    object_repr=force_str(solicitudbeca),
                    action_flag=ADDITION,
                    change_message=' Cambio de Carrera (' + client_address + ')')

                data['result'] = 'ok'
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}), content_type="application/json")

        elif action == 'datosgrupoprospecto':
            try:
                data = {'title': ''}
                grupo=Grupo.objects.get(id=int(request.POST['idgrupo']))

                data['idcarrera'] =grupo.carrera_id
                data['idmodalidad'] = grupo.modalidad_id
                data['idsession'] =grupo.sesion_id

                data['result'] = 'ok'
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}), content_type="application/json")

        elif action == 'eliminarregistrosga':
            try:
                data = {'title': ''}
                import requests as req

                solicitudpostulacion = SolicitudPostulacionBeca.objects.get(pk=int(request.POST['idsolicitud']))

                inscripcion = None
                if Inscripcion.objects.filter(persona__cedula=str(solicitudpostulacion.identificacion),carrera=solicitudpostulacion.carrera).exclude(
                        persona__cedula=None).exclude(
                        persona__cedula='').exists():
                    inscripcion = Inscripcion.objects.filter(persona__cedula=str(solicitudpostulacion.identificacion),carrera=solicitudpostulacion.carrera).order_by(
                        '-id').exclude(persona__cedula=None).exclude(
                        persona__cedula='')[:1].get()

                if Inscripcion.objects.filter(persona__pasaporte=str(solicitudpostulacion.identificacion),carrera=solicitudpostulacion.carrera).exclude(
                        persona__pasaporte=None).exclude(persona__pasaporte='').exists():
                    inscripcion = Inscripcion.objects.filter(persona__pasaporte=str(solicitudpostulacion.identificacion),carrera=solicitudpostulacion.carrera).order_by(
                        '-id').exclude(
                        persona__pasaporte=None).exclude(persona__pasaporte='')[:1].get()

                if inscripcion == None:

                    pass
                else:

                    if Pago.objects.filter(rubro__id__in=Rubro.objects.filter(inscripcion=inscripcion).values_list('id',flat=True)).exists():
                        return HttpResponse(json.dumps({'result': 'bad', 'message': str("No se puede eliminar el registro en el sga porque tiene pagos")}),
                                            content_type="application/json")

                    user_inscrip = inscripcion.persona.usuario.id
                    usuario = User.objects.get(pk=user_inscrip)
                    usuario.delete()

                    solicitudpostulacion.inscrito = False
                    solicitudpostulacion.grupo = 0
                    solicitudpostulacion.save()

                data['result'] = 'ok'

                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}), content_type="application/json")

        elif action == 'inscribirpostulacion':
            try:

                data = {'title': ''}
                tienediscapacidad=False
                user = request.user
                sid = transaction.savepoint()

                solicitudpostulacion = SolicitudPostulacionBeca.objects.get(pk=int(request.POST['idsolicitud']))
                solicitudpostulacion.numerocasa=str(request.POST['numerocasa'])
                solicitudpostulacion.save()
                documentopostulacion=None
                if DocumentosPostulacionBeca.objects.filter(solicitudpostulacion=solicitudpostulacion).exists():
                    documentopostulacion=DocumentosPostulacionBeca.objects.filter(solicitudpostulacion=solicitudpostulacion)[:1].get()


                estadocivil=PersonaEstadoCivil.objects.get(pk=solicitudpostulacion.estadocivil.id)

                nacionalidad = Nacionalidad.objects.get(pk=1)

                copiacedula = False
                if documentopostulacion:
                    if documentopostulacion.pertenece == 1:
                        copiacedula = True


                existe = False
                insecontrada = None

                if  Inscripcion.objects.filter(persona__cedula=solicitudpostulacion.identificacion,carrera=solicitudpostulacion.carrera).exclude(persona__cedula=None).exclude(persona__cedula='').exists():
                      insecontrada= Inscripcion.objects.filter(persona__cedula=solicitudpostulacion.identificacion,carrera=solicitudpostulacion.carrera)[:1].get()
                      existe=True

                elif Inscripcion.objects.filter(persona__pasaporte=solicitudpostulacion.identificacion,carrera=solicitudpostulacion.carrera).exclude(persona__pasaporte=None).exclude(persona__pasaporte='').exists():
                      insecontrada= Inscripcion.objects.filter(persona__pasaporte=solicitudpostulacion.identificacion,carrera=solicitudpostulacion.carrera)[:1].get()
                      existe=True

                if existe == False:
                    persona = Persona(nombres=elimina_tildes(solicitudpostulacion.nombres),
                                      apellido1=elimina_tildes(solicitudpostulacion.apellidos),
                                      apellido2=str(''),
                                      extranjero=False,
                                      cedula=solicitudpostulacion.identificacion,
                                      provincia=solicitudpostulacion.provincia,
                                      canton=solicitudpostulacion.ciudad,
                                      parroquia=solicitudpostulacion.parroquia,
                                      sexo=solicitudpostulacion.sexo,
                                      nacionalidad=nacionalidad,
                                      direccion=elimina_tildes(request.POST['calleprincipal']).upper(),
                                      direccion2=elimina_tildes(request.POST['callesecundaria']).upper(),
                                      num_direccion=str(solicitudpostulacion.numerocasa).upper(),
                                      sector=str(solicitudpostulacion.referencia).upper(),
                                      telefono=str(solicitudpostulacion.celular),
                                      telefono_conv=str(solicitudpostulacion.telefono) if solicitudpostulacion.telefono.isdigit() else '0000000000',
                                      email=elimina_tildes(solicitudpostulacion.email).lower(),
                                      email1=elimina_tildes(solicitudpostulacion.email).lower(),
                                      estadocivilid=estadocivil.id
                                      )
                    persona.save()

                    username = calculate_username(persona)
                    password = DEFAULT_PASSWORD
                    user = User.objects.create_user(username, persona.email, password)
                    user.save()
                    persona.usuario = user
                    if USA_CORREO_INSTITUCIONAL:
                        persona.emailinst = user.username + '' + CORREO_INSTITUCIONAL
                    else:
                        persona.emailinst = ''
                    persona.save()

                    doblematricula = False

                    # BECAS DEL GOBIERNO DE UN NUEVO ECUADOR
                    convenioninstituciona = EmpresaConvenio.objects.get(pk=solicitudpostulacion.empresaconvenio.id)

                    # if Inscripcion.objects.filter(persona__cedula=identificacion).exclude(persona__cedula=None).exclude(
                    #         persona__cedula='').exists():
                    #     doblematricula = True
                    # if Inscripcion.objects.filter(persona__pasaporte=identificacion).exclude(
                    #         persona__pasaporte=None).exclude(persona__pasaporte='').exists():
                    #     doblematricula = True
                    motivoinscripcion = str('BECA OTORGADA POR EL ' + str(convenioninstituciona.nombre).upper())
                    inscripcion = Inscripcion(persona=persona,
                                              fecha=datetime.now(),
                                              carrera=solicitudpostulacion.carrera,
                                              anuncio=solicitudpostulacion.anuncio,
                                              modalidad_id=int(request.POST['cmbmodalidadinscripcion']),
                                              sesion_id=int(request.POST['cmbsesioninscripcion']),
                                              doblematricula=doblematricula,
                                              observacion=motivoinscripcion,
                                              empresaconvenio=convenioninstituciona)

                    # Verifica que no se cree una Inscripcion doble (misma Cedula y Carrera)
                    if not Inscripcion.objects.filter(persona__cedula=persona.cedula, carrera=solicitudpostulacion.carrera,
                                                      persona__pasaporte=persona.pasaporte).exists():

                        i = Inscripcion.objects.latest('id') if Inscripcion.objects.exists() else None
                        if i:
                            inscripcion.numerom = i.numerom + 1
                        else:
                            inscripcion.numerom = 1

                        inscripcion.save()

                        # Crear el registro en el Perfil de Inscripciones si es discapacitado para el DOBE
                        if inscripcion.tienediscapacidad:
                            perfil = PerfilInscripcion(inscripcion=inscripcion, tienediscapacidad=True)
                            perfil.save()

                        if inscripcion.doblematricula:
                            px = ''
                            doblemat = ProcesoDobleMatricula(inscripcion=inscripcion, aprobado=False,
                                                             fecha=datetime.now())
                            doblemat.save()

                            # obtengo informacion de ficha medica completa para grabar en nueva inscripcion OCU 28-03-2016
                            if PersonaExtension.objects.filter(persona__cedula=persona.cedula).exclude(
                                    persona__cedula='').exists() or PersonaExtension.objects.filter(
                                persona__pasaporte=persona.pasaporte).exclude(persona__pasaporte='').exists():
                                if PersonaExtension.objects.filter(persona__cedula=persona.cedula).exclude(
                                        persona__cedula='').exists():
                                    for p in PersonaExtension.objects.filter(persona__cedula=persona.cedula).exclude(
                                            persona__cedula=''):
                                        if not p.persona.datos_medicos_incompletos():
                                            px = p
                                else:
                                    # obtengo informacion de ficha medica completa para grabar en nueva inscripcion OCU 31-03-2016
                                    for p in PersonaExtension.objects.filter(
                                            persona__pasaporte=persona.pasaporte).exclude(
                                            persona__pasaporte=''):
                                        if not p.persona.datos_medicos_incompletos():
                                            px = p
                                if px != '':
                                    if not px.persona.datos_medicos_incompletos():

                                        personaext = PersonaExtension(persona=persona,
                                                                      estadocivil=px.estadocivil,
                                                                      tienelicencia=px.tienelicencia,
                                                                      tipolicencia=px.tipolicencia,
                                                                      telefonos=px.telefonos,
                                                                      tieneconyuge=px.tieneconyuge,
                                                                      hijos=px.hijos,
                                                                      padre=px.padre,
                                                                      edadpadre=px.edadpadre,
                                                                      estadopadre=px.estadopadre,
                                                                      telefpadre=px.telefpadre,
                                                                      educacionpadre=px.educacionpadre,
                                                                      profesionpadre=px.profesionpadre,
                                                                      trabajopadre=px.trabajopadre,
                                                                      madre=px.madre,
                                                                      edadmadre=px.edadmadre,
                                                                      estadomadre=px.estadomadre,
                                                                      telefmadre=px.telefmadre,
                                                                      educacionmadre=px.educacionmadre,
                                                                      profesionmadre=px.profesionmadre,
                                                                      trabajomadre=px.trabajomadre,
                                                                      conyuge=px.conyuge,
                                                                      edadconyuge=px.edadconyuge,
                                                                      estadoconyuge=px.estadoconyuge,
                                                                      telefconyuge=px.telefconyuge,
                                                                      educacionconyuge=px.educacionconyuge,
                                                                      profesionconyuge=px.profesionconyuge,
                                                                      trabajoconyuge=px.trabajoconyuge,
                                                                      enfermedadpadre=px.enfermedadpadre,
                                                                      enfermedadmadre=px.enfermedadmadre,
                                                                      enfermedadabuelos=px.enfermedadabuelos,
                                                                      enfermedadhermanos=px.enfermedadhermanos,
                                                                      enfermedadotros=px.enfermedadotros)
                                        personaext.save()

                                        # Ficha Medica
                                        if PersonaFichaMedica.objects.filter(personaextension=px).exists():
                                            pfm = PersonaFichaMedica.objects.get(personaextension=px)
                                            personafmedica = PersonaFichaMedica(personaextension=personaext,
                                                                                vacunas=pfm.vacunas,
                                                                                nombrevacunas=pfm.nombrevacunas,
                                                                                enfermedades=pfm.enfermedades,
                                                                                nombreenfermedades=pfm.nombreenfermedades,
                                                                                alergiamedicina=pfm.alergiamedicina,
                                                                                nombremedicinas=pfm.nombremedicinas,
                                                                                alergiaalimento=pfm.alergiaalimento,
                                                                                nombrealimentos=pfm.nombrealimentos,
                                                                                cirugias=pfm.cirugias,
                                                                                nombrecirugia=pfm.nombrecirugia,
                                                                                fechacirugia=pfm.fechacirugia,
                                                                                aparato=pfm.aparato,
                                                                                tipoaparato=pfm.tipoaparato,
                                                                                gestacion=pfm.gestacion,
                                                                                partos=pfm.partos,
                                                                                abortos=pfm.abortos,
                                                                                cesareas=pfm.cesareas,
                                                                                hijos2=pfm.hijos2,
                                                                                cigarro=pfm.cigarro,
                                                                                numerocigarros=pfm.numerocigarros,
                                                                                tomaalcohol=pfm.tomaalcohol,
                                                                                tipoalcohol=pfm.tipoalcohol,
                                                                                copasalcohol=pfm.copasalcohol,
                                                                                tomaantidepresivos=pfm.tomaantidepresivos,
                                                                                antidepresivos=pfm.antidepresivos,
                                                                                tomaotros=pfm.tomaotros,
                                                                                otros=pfm.otros,
                                                                                horassueno=pfm.horassueno,
                                                                                calidadsuenno=pfm.calidadsuenno)
                                            personafmedica.save()

                                        # Examen Fisico
                                        if PersonaExamenFisico.objects.filter(
                                                personafichamedica__personaextension=px).exists():
                                            pef = PersonaExamenFisico.objects.get(
                                                personafichamedica__personaextension=px)
                                            personaef = PersonaExamenFisico(personafichamedica=personafmedica,
                                                                            inspeccion=pef.inspeccion,
                                                                            usalentes=pef.usalentes,
                                                                            motivo=pef.motivo,
                                                                            peso=pef.peso,
                                                                            talla=pef.talla,
                                                                            pa=pef.pa,
                                                                            pulso=pef.pulso,
                                                                            rcar=pef.rcar,
                                                                            rresp=pef.rresp,
                                                                            temp=pef.temp,
                                                                            observaciones=pef.observaciones)
                                            personaef.save()

                            # Verificar documentos en secretaria con cedula 31-03-2016 OCU ok

                            if Inscripcion.objects.filter(persona__cedula=persona.cedula).exclude(
                                    persona__cedula='').exists() or Inscripcion.objects.filter(
                                persona__pasaporte=persona.pasaporte).exclude(persona__pasaporte='').exists():
                                if Inscripcion.objects.filter(persona__cedula=persona.cedula).exclude(
                                        persona__cedula='').exists():
                                    perins = Inscripcion.objects.filter(persona__cedula=persona.cedula).order_by('id')[
                                             :1].get()
                                    doc_insc = DocumentosDeInscripcion.objects.filter(inscripcion=perins)[:1].get()
                                else:
                                    perins = Inscripcion.objects.filter(persona__pasaporte=persona.pasaporte).order_by(
                                        'id')[:1].get()
                                    doc_insc = DocumentosDeInscripcion.objects.filter(inscripcion=perins)[:1].get()
                                if doc_insc:

                                    insdoc = DocumentosDeInscripcion(inscripcion=inscripcion,
                                                                     titulo=False,
                                                                     acta=False,
                                                                     cedula=copiacedula,
                                                                     votacion=False,
                                                                     fotos=False,
                                                                     actaconv=False,
                                                                     partida_nac=False,
                                                                     actafirmada=False)
                                    insdoc.save()

                        if EMAIL_ACTIVE and inscripcion.doblematricula:
                            doblemat.mail_procesodoblematricula(persona, inscripcion.carrera.nombre, request.user)
                else:
                    inscripcion = insecontrada
                    user = inscripcion.persona.usuario

                    if inscripcion:
                        return HttpResponse(
                            json.dumps({"result": "bad", "error": str('El estudiante esta matriculado actualmente')}),
                            content_type="application/json")

                    # if Rubro.objects.filter(inscripcion=inscripcion).exists():
                    #      return HttpResponse(json.dumps({"result":"bad","error":str('El estudiante tiene rubro en sus finanzas')}), content_type="application/json")

                if UTILIZA_GRUPOS_ALUMNOS:
                    if int(request.POST['cmbgrupoinscripcion']) > 0:
                        grupo = Grupo.objects.get(id=request.POST['cmbgrupoinscripcion'])
                        for x in InscripcionGrupo.objects.filter(inscripcion=inscripcion):
                            x.activo = False
                            x.save()
                        if InscripcionGrupo.objects.filter(inscripcion=inscripcion, grupo=grupo).exists():
                            ig = InscripcionGrupo.objects.filter(inscripcion=inscripcion, grupo=grupo).order_by('-id')[
                                 :1].get()
                            ig.activo = True
                        else:
                            ig = InscripcionGrupo(inscripcion=inscripcion, grupo=grupo, activo=True)
                        ig.save()

                    # Actualizar el estado del Grupo
                    if grupo.abierto:
                        grupo.abierto = grupo.esta_abierto()
                        grupo.save()

                    # Precios de Carrera segun grupo
                    pcg = grupo.precios()
                    valor = 0
                    if INSCRIPCION_CONDUCCION:
                        if RubrosConduccion.objects.filter(carrera=inscripcion.carrera).exists():
                            r = RubrosConduccion.objects.filter(carrera=inscripcion.carrera)[:1].get()
                            rubro = Rubro(fecha=datetime.now(), valor=r.precio, inscripcion=inscripcion,
                                          cancelado=False, fechavence=ig.grupo.fin)
                            rubro.save()
                            # Se crea el tipo de Rubro Otro q es de tipo Derecho Examen
                            rubroo = RubroOtro(rubro=rubro, tipo=r.tipo, descripcion=r.descripcion)
                            rubroo.save()


                if tienediscapacidad and EMAIL_ACTIVE:

                    if tienediscapacidad:
                        tipo_notificacion = 'DISCAPACIDAD'

                    # inscripcion.notificacion_dobe(request.user)
                    # inscripcion.notificacion_dobe(request.user,tipo_notificacion)
                    # OCU 04-sep-2017
                    asunto = 'Se ha inscrito una persona'
                    inscripcion.notificacion_dobe(request.user, tipo_notificacion, asunto)

                # OCU 31-marzo-2016 realiza esto en el caso de inscripcion nueva
                if not inscripcion.doblematricula:
                    documentos = DocumentosDeInscripcion(inscripcion=inscripcion,
                                                     titulo=False,
                                                     acta=False,
                                                     cedula=copiacedula,
                                                     votacion=False,
                                                     fotos=False,
                                                     actaconv=False,
                                                     partida_nac=False,
                                                     actafirmada=False)
                    documentos.save()


                if existe == False:
                    g = Group.objects.get(pk=ALUMNOS_GROUP_ID)
                    g.user_set.add(user)
                    g.save()

                if not InscripcionFichaSocioEconomicaBeca.objects.filter(inscripcion=inscripcion).exists():

                    inscripficha = InscripcionFichaSocioEconomicaBeca(
                        inscripcion=inscripcion,
                        edad=inscripcion.persona.edad_actual(),
                        estadocivil=estadocivil,
                        ciudad=solicitudpostulacion.ciudad,
                        direccion=solicitudpostulacion.referencia,
                        numero=solicitudpostulacion.numerocasa,
                        telefono=str(solicitudpostulacion.telefono) if solicitudpostulacion.telefono.isdigit() else '0000000000',
                        celular=str(solicitudpostulacion.celular) if solicitudpostulacion.celular.isdigit() else '0000000000',
                        emailpersona=solicitudpostulacion.email,
                        completo=True
                    )

                    inscripficha.save()

                    if DatosAdicionalPostulacionBeca.objects.filter(solicitudpostulacion=solicitudpostulacion).exists():
                        datosadicionales = DatosAdicionalPostulacionBeca.objects.filter(
                            solicitudpostulacion=solicitudpostulacion,tipoadicion=1)[:1].get()


                        referenciapersona = ReferenciaPersonal(fichabeca=inscripficha,
                                                               nombre=elimina_tildes(datosadicionales.nombre_completo_inverso()),
                                                               telefono=datosadicionales.telefono,
                                                               celular=datosadicionales.celular,
                                                               parentesco_id=12
                                                               )
                        referenciapersona.save()



                # matricular al estudiante
                if not grupo.nivel_set.filter(nivelmalla__id=NIVEL_MALLA_UNO, cerrado=False
                                              ).exists():
                    inscripcion.persona.usuario.delete()
                    return HttpResponse(
                        json.dumps({"result": "bad", "error": str('No se encontro el nivel abierto para ese grupo')}),
                        content_type="application/json")

                nivel = grupo.nivel_set.filter(nivelmalla__id=NIVEL_MALLA_UNO, cerrado=False
                                               )[:1].get()

                inscripcion.matricularBecaMunicipio(nivel,
                                                    None, None,
                                                    None)

                userrudy = User.objects.get(id=ID_USUARIO_RUDY)

                if SolicitudBeca.objects.filter().exists():
                    idsoli = SolicitudBeca.objects.filter().order_by('-id')[:1].get().id + 1
                else:
                    idsoli = 1


                motivo = str('BECA OTORGADA POR EL GOBIERNO NACIONAL ')
                motivo_id = ID_MOTIVO_BECA_NUEVOECUADOR

                # graudar la solicitud de beca
                solicitudbeca = SolicitudBeca(id=idsoli,
                                              inscripcion=inscripcion,
                                              motivo=motivo,
                                              nivel=nivel,
                                              puntaje=0,
                                              fecha=datetime.now(),
                                              estadoverificaciondoc=True)
                solicitudbeca.save()

                # llenar el log de historial de la solicitud beca
                loshistorial = HistorialGestionBeca(solicitudbeca=solicitudbeca, inscripcion=solicitudbeca.inscripcion,
                                                    fecha=datetime.now(), estado_id=3, usuario=userrudy,
                                                    comentariocorreo=motivo,
                                                    tipobeca_id=ID_TIPOBECA, motivobeca_id=motivo_id,
                                                    puntajerenovacion=Decimal('95').quantize(Decimal(10) ** -2))

                loshistorial.save()

                resolucionbeca = Resolucionbeca(solicitudbeca=solicitudbeca, fecha=datetime.now())
                resolucionbeca.save()
                numerosolucion = 'ITB-BO-' + str(datetime.now().year) + '-00' + str(resolucionbeca.id)
                resolucionbeca.numerosolucion = numerosolucion
                resolucionbeca.save()


                solicitudbeca.asignaciontarficadescuento = True
                solicitudbeca.save()

                resolucionbeca = Resolucionbeca.objects.get(solicitudbeca=solicitudbeca)
                resolucionbeca.fechaprobacion = datetime.now()
                resolucionbeca.estado = True
                resolucionbeca.save()

                # llenar el log de historial de la solicitud beca por aprobacion del estudiante
                loshistorial = HistorialGestionBeca(solicitudbeca=solicitudbeca, inscripcion=solicitudbeca.inscripcion,
                                                    fecha=datetime.now(), estado_id=18,
                                                    usuario=inscripcion.persona.usuario, comentariocorreo=str(
                        'APROBACION DEL ESTUDIANTE AUTOMATICAMENTE POR BECA'))
                loshistorial.save()

                loshistorial = HistorialGestionBeca(solicitudbeca=solicitudbeca, inscripcion=solicitudbeca.inscripcion,
                                                    fecha=datetime.now(), estado_id=26, usuario=userrudy,
                                                    comentariocorreo=str('BECA APLICADA AUTOMATICAMENTE '))
                loshistorial.save()

                solicitudbeca.estadosolicitud_id = 7
                solicitudbeca.save()

                solicitudbeca.aprobacionestudiante = True
                solicitudbeca.asignaciontarficadescuento = True
                solicitudbeca.envioanalisis = True
                solicitudbeca.aprobado = True

                solicitudbeca.save()

                solicitudpostulacion.inscrito=True
                solicitudpostulacion.grupo = grupo.id
                solicitudpostulacion.save()


                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                    user_id=userrudy.pk,
                    content_type_id=ContentType.objects.get_for_model(solicitudbeca).pk,
                    object_id=solicitudbeca.id,
                    object_repr=force_str(solicitudbeca),
                    action_flag=ADDITION,
                    change_message='Ingreso y Aplicacion de Solicitud de Becas del gobierno nuevo ecuador(' + client_address + ')')

                transaction.savepoint_commit(sid)

                # envio del certificado de inscripcion cuando ya esta inscrito
                enviarcertificadoinscripcion(solicitudpostulacion)

                if EMAIL_ACTIVE and (
                        inscripcion.documentos_entregados().cedula or inscripcion.documentos_entregados().titulo or inscripcion.documentos_entregados().votacion or inscripcion.documentos_entregados().fotos or inscripcion.documentos_entregados().acta):
                    inscripcion.correo_entregadocumentos(inscripcion.documentos_entregados(), userrudy)

                data['result'] = 'ok'

                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as e:

                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}), content_type="application/json")


        elif action == 'buscarcarreramodalidad':
            try:
                data = {'title': ''}
                listacarrera = []
                listacarrera.append({"id": 0, "nombre": "Seleccionar la carrerar"})
                if ConvenioCarrera.objects.filter(modalidad__id=int(request.POST['idmodalidad'])).exists():
                    for a in ConvenioCarrera.objects.filter(modalidad__id=int(request.POST['idmodalidad'])).order_by("carrera__nombre"):
                        listacarrera.append({"id": a.carrera.id, "nombre": a.carrera.nombre})



                data['listcarrera'] = listacarrera


                data['result'] = 'ok'
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}), content_type="application/json")

        elif action == 'enviarcertificadoinscripcion':
            try:
                data = {'title': ''}
                import requests as req


                listapostulantesinscritos = SolicitudPostulacionBeca.objects.filter(empresaconvenio__id=request.POST['idconvenio'],inscrito=True,enviocorrecertificacion=False).order_by('-id')

                if listapostulantesinscritos.count()>0:

                    for c in listapostulantesinscritos:

                        enviarcertificadoinscripcion(c)
                        c.enviocorrecertificacion = True
                        c.save()

                    data['result'] = 'ok'

                else:
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str('No existe solicitud que no se ha enviado el certificado de inscripción')}),
                                        content_type="application/json")
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}), content_type="application/json")


        elif action == 'reenviocertificadosga':
            try:
                data = {'title': ''}
                import requests as req

                solicitudpostulacion = SolicitudPostulacionBeca.objects.get(pk=int(request.POST['idsolicitud']))
                enviarcertificadoinscripcion(solicitudpostulacion)
                solicitudpostulacion.enviocorrecertificacion = True
                solicitudpostulacion.save()

                data['result'] = 'ok'
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}), content_type="application/json")




    else:

        data = {'title': 'Solicitudes de Postulacion Becfa'}
        addUserData(request, data)
        search = None
        fecha = datetime.now().strftime("%Y-%m-%d")
        if 'action' in request.GET:
            action = request.GET['action']

            if 'action' in request.GET:
                action = request.GET['action']

                if action == 'verdatosresposable':
                    solicitudbeca = SolicitudPostulacionBeca.objects.get(id=int(request.GET['idpreregistro']))
                    datosresposabale=DatosAdicionalPostulacionBeca.objects.get(solicitudpostulacion=solicitudbeca,tipoadicion=1)
                    data['datosresposabale'] = datosresposabale

                    return render(request, "solicitudpostulacionbeca/datosresponsable.html", data)

                elif action == 'cambiarcarrerapostulacion':

                    solicitudpostulacion = SolicitudPostulacionBeca.objects.get(pk=int(request.GET['idsolicitud']))
                    data['datossolicitud'] = solicitudpostulacion
                    data['liscarrera'] = Carrera.objects.filter(activo=True,carrera=True)


                    return render(request, "solicitudpostulacionbeca/cambiarcarrerapostulacion.html", data)

                elif action == 'versolicitud':
                    solicitudbeca = SolicitudPostulacionBeca.objects.get(id=int(request.GET['idsolicitud']))
                    if DatosAdicionalPostulacionBeca.objects.filter(solicitudpostulacion=solicitudbeca,tipoadicion=1).exists():
                        datosresposabale=DatosAdicionalPostulacionBeca.objects.get(solicitudpostulacion=solicitudbeca,tipoadicion=1)
                        data['datosresposabale'] = datosresposabale
                        # verificar si el responsable solidario es casado
                        if datosresposabale.estadocivil_id == 2:
                            if DatosAdicionalPostulacionBeca.objects.filter(solicitudpostulacion=solicitudbeca,
                                                                            tipoadicion=2,
                                                                            pertenece=datosresposabale.id).exists():
                                datosConyubeSolidario = DatosAdicionalPostulacionBeca.objects.filter(
                                    solicitudpostulacion=solicitudbeca, tipoadicion=2, pertenece=datosresposabale.id)[:1].get()
                                data['datosConyubeSolidario'] = datosConyubeSolidario


                    # verificar si el becario es casado
                    if solicitudbeca.estadocivil_id == 2 :
                        if DatosAdicionalPostulacionBeca.objects.filter(solicitudpostulacion=solicitudbeca,
                                                                        tipoadicion=3).exists():

                            datosConyube=DatosAdicionalPostulacionBeca.objects.filter(solicitudpostulacion=solicitudbeca,tipoadicion=3)[:1].get()
                            data['datosConyube'] = datosConyube


                    if HorariosCarreraPostulacion.objects.filter(carrera=solicitudbeca.carrera.id).exists():
                            data['listaJornada'] = HorariosCarreraPostulacion.objects.filter(carrera=solicitudbeca.carrera.id)

                    # verificar si tienes documento
                    if DocumentosPostulacionBeca.objects.filter(solicitudpostulacion=solicitudbeca).exists():
                        data['listdocumentos'] = DocumentosPostulacionBeca.objects.filter(solicitudpostulacion=solicitudbeca)

                    data['datossolicitud'] = solicitudbeca
                    data['listtipoidentificacion'] = TipoIdentificacion.objects.filter(estado=True).order_by("id")
                    data['liscarrera'] = ConvenioCarrera.objects.filter(empresaconvenio=solicitudbeca.empresaconvenio,modalidad=solicitudbeca.modalidad, activo=True)

                    data['listpais'] = Pais.objects.filter(pk=1)
                    data['lisprovincia'] = Provincia.objects.filter()
                    data['listaciudad'] = Canton.objects.filter(provincia=solicitudbeca.provincia)
                    data['listaparroquia'] = Parroquia.objects.filter(canton=solicitudbeca.ciudad)
                    data['listsexo'] = Sexo.objects.filter()
                    data['listaestadocivil'] = PersonaEstadoCivil.objects.filter().exclude(pk=6)
                    data['listmodalidad'] = Modalidad.objects.filter(id__in=[1,4])
                    data['listamedio'] = TipoAnuncio.objects.filter(activo=True).order_by("descripcion")

                    return render(request, "solicitudpostulacionbeca/verdatospostulacion.html", data)

                elif action == 'regitsrarsga':

                    solicitudpostulacion = SolicitudPostulacionBeca.objects.get(id=int(request.GET['idsolicitud']))
                    data['datossolicitud'] = solicitudpostulacion
                    data['listcarrera'] = Carrera.objects.filter()

                    data['listgrupoinscripcion'] = Grupo.objects.filter(
                        carrera=solicitudpostulacion.carrera)
                    data['search'] = request.GET['s']
                    data['carrera'] = request.GET['carrera']
                    data['listamodalidad'] =Modalidad.objects.filter()
                    data['listsesion'] =Sesion.objects.filter()

                    return render(request, "solicitudpostulacionbeca/registrarsga.html", data)






        else:
            try:



                    solicitudpostulacion = SolicitudPostulacionBeca.objects.filter().order_by('-fecha')
                    carrera=0
                    convenio=0
                    provincia=0
                    ciudad=0
                    certificadoeviado=0
                    inscrito=0
                    medio=0
                    if 's' in request.GET:
                        search = request.GET['s']

                        solicitudpostulacion=solicitudpostulacion.filter( Q(nombres__icontains=search) | Q(apellidos__icontains=search) |
                           Q(identificacion__icontains=search) | Q(
                            celular__icontains=search) | Q(email__icontains=search),
                            ).order_by('-fecha')

                    if 'carrera' in request.GET:
                        if int(request.GET['carrera'])>0:
                            carrera=int(request.GET['carrera'])
                            solicitudpostulacion=solicitudpostulacion.filter(carrera__id=int(request.GET['carrera']))

                    if 'convenio' in request.GET:
                        if int(request.GET['convenio']) > 0:
                            convenio = int(request.GET['convenio'])
                            solicitudpostulacion = solicitudpostulacion.filter(empresaconvenio__id=int(request.GET['convenio']))

                    if 'provincia' in request.GET:
                        if int(request.GET['provincia']) > 0:
                            provincia = int(request.GET['provincia'])
                            solicitudpostulacion = solicitudpostulacion.filter(
                                provincia__id=int(request.GET['provincia']))

                    if 'ciudad' in request.GET:
                        if int(request.GET['ciudad']) > 0:
                            ciudad = int(request.GET['ciudad'])
                            solicitudpostulacion = solicitudpostulacion.filter(ciudad__id=int(request.GET['ciudad']))

                    if 'certificadoeviado' in request.GET:
                        if int(request.GET['certificadoeviado']) > 0:
                            certificadoeviado=int(request.GET['certificadoeviado'])
                            if certificadoeviado==1:
                                solicitudpostulacion = solicitudpostulacion.filter(enviocorrecertificacion=True)
                            else:
                                solicitudpostulacion = solicitudpostulacion.filter(enviocorrecertificacion=False)

                    if 'inscrito' in request.GET:
                        if int(request.GET['inscrito']) > 0:
                            inscrito=int(request.GET['inscrito'])
                            if inscrito==1:
                                solicitudpostulacion = solicitudpostulacion.filter(inscrito=True)
                            else:
                                solicitudpostulacion = solicitudpostulacion.filter(inscrito=False)

                    if 'medio' in request.GET:
                        if int(request.GET['medio']) > 0:
                            medio = int(request.GET['medio'])
                            solicitudpostulacion = solicitudpostulacion.filter(
                                anuncio__id=int(request.GET['medio']))

                    # nombre_archivo = 'C://Users//Usuario//Downloads//nummatricucvsitb.csv'
                    #
                    #
                    # # Abre el archivo en modo lectura con la codificación ISO-8859-1
                    # with open(nombre_archivo, mode='r', newline='', encoding='ISO-8859-1') as archivo:
                    #     lector_csv = csv.reader(archivo, delimiter=';', quotechar='"')
                    #
                    #     for fila in lector_csv:
                    #         if Inscripcion.objects.filter(persona__cedula=str(fila[0]),persona__usuario__is_active=True).exists():
                    #             inscrip = Inscripcion.objects.filter(persona__cedula=str(fila[0]),persona__usuario__is_active=True).order_by('id')[
                    #                       :1].get()
                    #             nivelmalla=None
                    #             if inscrip.matricula_periodo(data['periodo']):
                    #                 matricula=inscrip.matricula_periodo(data['periodo'])
                    #                 grupo=matricula.nivel.grupo
                    #                 nivelmalla=matricula.nivel.nivelmalla
                    #                 nummatricula=MateriaAsignada.objects.filter(matricula__inscripcion=inscrip,
                    #                                                matricula__nivel__carrera=matricula.nivel.carrera,
                    #                                                matricula__nivel__nivelmalla=matricula.nivel.nivelmalla).count()
                    #             else:
                    #                 grupo=None
                    #
                    #                 if InscripcionGrupo.objects.filter(inscripcion=inscrip).exists():
                    #                     grupo=InscripcionGrupo.objects.filter(inscripcion=inscrip).order_by('-inscripcion__fecha')[:1].get().grupo
                    #
                    #                 if grupo.nivel_grupo()==None:
                    #                     if RecordAcademico.objects.filter(inscripcion=inscrip).exists():
                    #                         nivelmalla=RecordAcademico.objects.filter(inscripcion=inscrip).order_by('-id')[:1].get().nivel_asignatura()
                    #                 else:
                    #                     nivelmalla=grupo.nivel_grupo().nivelmalla
                    #
                    #                 nummatricula = MateriaAsignada.objects.filter(matricula__inscripcion=inscrip,
                    #                                                               matricula__nivel__carrera=inscrip.carrera,
                    #                                                               matricula__nivel__nivelmalla=nivelmalla).count()
                    #
                    #             print(str(fila[0]) + ';' + str(nummatricula))
                    #
                    #
                    #
                    #         else:
                    #             print(str(fila[0])+';'+str('NO INSCRITO'))




                    paging = MiPaginador(solicitudpostulacion, 30)
                    p = 1
                    try:
                        if 'page' in request.GET:
                            p = int(request.GET['page'])
                            paging = MiPaginador(solicitudpostulacion, 30)
                        page = paging.page(p)
                    except Exception as ex:
                        page = paging.page(1)



                    data['hoy'] = datetime.now()

                    data['paging'] = paging
                    data['rangospaging'] = paging.rangos_paginado(p)
                    data['totalpostulantes'] = solicitudpostulacion.count()
                    data['page'] = page
                    data['solicitudpostulacion'] = page.object_list
                    data['fechah'] = datetime.now().strftime("%Y-%m-%d")
                    hora_actual = datetime.now().time()
                    data['horactual'] = hora_actual.strftime('%H:%M')
                    data['search'] = search if search else ""
                    data['carrera'] = carrera
                    data['convenio'] = convenio
                    data['provincia'] =   provincia
                    data['ciudad'] = ciudad
                    data['certificadoeviado'] = certificadoeviado
                    data['inscrito'] = inscrito
                    data['medio'] = medio
                    data['listcarrerapostulacion'] = Carrera.objects.filter(activo=True,carrera=True)
                    data['listconvenio'] = EmpresaConvenio.objects.filter()
                    data['listprovincia'] = Provincia.objects.filter()
                    data['listipoanuncio'] = TipoAnuncio.objects.filter()



                    return render(request,"solicitudpostulacionbeca/solictudapostulaciondmin.html", data)

            except Exception as ex:
                print(ex)

