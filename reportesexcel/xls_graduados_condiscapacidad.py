from datetime import datetime,timedelta
import json
import xlrd
import xlwt

from django.contrib.auth.decorators import login_required

from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from settings import UTILIZA_GRUPOS_ALUMNOS, EMAIL_ACTIVE,MEDIA_ROOT, ASIG_VINCULACION, ASIG_PRATICA
from sga.commonviews import addUserData, ip_client_address
from sga.forms import GraduadosMatrizForm
from sga.models import TituloInstitucion,ReporteExcel,Graduado,PerfilInscripcion
from socioecon.models import  InscripcionFichaSocioeconomica,PersonaSustentaHogar
from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action :

                try:
                    anio = request.POST['anio']
                    graduados = Graduado.objects.filter(fechagraduado__year=anio,inscripcion__tienediscapacidad=True).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')
                    totalg = graduados.count()
                    m = 5
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('GraduadosconDiscapacidad',cell_overwrite_ok=True)
                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,m+52, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,m+52, 'LISTADO DE GRADUADOS CON DISCAPACIDAD ', titulo2)
                    ws.write(2, 0, 'ANIO:' +str(anio), titulo)

                    ws.write(4, 0, 'CARRERA', titulo)
                    ws.write(4, 1, 'IDENTIFICACION', titulo)
                    ws.write(4, 2, 'NOMBRES', titulo)
                    ws.write(4, 3, 'SEXO', titulo)
                    ws.write(4, 4, 'F. GRADUADO', titulo)
                    ws.write(4, 5, 'NOTA TESIS', titulo)
                    ws.write(4, 6, 'NOTA FINAL', titulo)
                    ws.write(4, 7, 'REGISTRO SENESCYT', titulo)
                    ws.write(4, 8, 'BECADO', titulo)
                    ws.write(4, 9, 'POR CIENTO BECA', titulo)
                    ws.write(4, 10, 'TIPO BECA', titulo)
                    ws.write(4, 11, 'EMAIL PERSONAL', titulo)
                    ws.write(4, 12, 'EMAIL INST',titulo)
                    ws.write(4, 13, 'EMAIL 1',titulo)
                    ws.write(4, 14, 'EMAIL 2',titulo)
                    ws.write(4, 15, 'TLF. CONVENCIONAL', titulo)
                    ws.write(4, 16, 'CELULAR', titulo)
                    ws.write(4, 17, 'RAZA', titulo)
                    ws.write(4, 18, 'ESTRATO', titulo)
                    ws.write(4, 19, 'TIPO DISCAPACIDAD', titulo)
                    ws.write(4, 20, 'PORCIENTO DISCAPACIDAD', titulo)
                    ws.write(4, 21, 'CARNET DISCAPACIDAD', titulo)
                    # Datos Ficha Socioeconomica
                    ws.write(4, 22, 'PUNTAJE TOTAL', titulo)
                    ws.write(4, 23, 'GRUPO SOCIOECONOMICO', titulo)
                    ws.write(4, 24, 'TIPO HOGAR', titulo)
                    ws.write(4, 25, 'ES CABEZA DE FAMILIA', titulo)
                    ws.write(4, 26, 'ES DEPENDIENTE', titulo)
                    ws.write(4, 27, 'PERSONA CUBRE GASTO', titulo)
                    ws.write(4, 28, 'OTROS CUBRE GASTO', titulo)
                    ws.write(4, 29, 'SUSTENTA HOGAR', titulo)
                    ws.write(4, 30, 'TIPO VIVIENDA', titulo)
                    ws.write(4, 31, 'VALOR TIPO VIVIENDA', titulo)
                    ws.write(4, 32, 'MATERIAL PARED', titulo)
                    ws.write(4, 33, 'VALOR MATERIAL PARED', titulo)
                    ws.write(4, 34, 'MATERIAL PISO', titulo)
                    ws.write(4, 35, 'VALOR MATERIAL PISO', titulo)
                    ws.write(4, 36, 'CANTIDAD BANIO DUCHA', titulo)
                    ws.write(4, 37, 'VALOR BANIO DUCHA', titulo)
                    ws.write(4, 38, 'TIPO SSHH', titulo)
                    ws.write(4, 39, 'VALOR TIPO SSHH', titulo)
                    ws.write(4, 40, 'TIENE INTERNET', titulo)
                    ws.write(4, 41, 'VALOR INTERNET', titulo)
                    ws.write(4, 42, 'TIENE COMPUTADOR', titulo)
                    ws.write(4, 43, 'VALOR COMPUTADOR', titulo)
                    ws.write(4, 44, 'TIENE LAPTOP', titulo)
                    ws.write(4, 45, 'VALOR LAPTOP', titulo)
                    ws.write(4, 46, 'CANT. CELULARES', titulo)
                    ws.write(4, 47, 'VALOR CANT. CELULARES', titulo)
                    ws.write(4, 48, 'TELEF. CONV,', titulo)
                    ws.write(4, 49, 'VALOR TELEF. CONV,', titulo)
                    ws.write(4, 50, 'TIENE COCINA/HORNO', titulo)
                    ws.write(4, 51, 'VALOR COCINA/HORNO', titulo)
                    ws.write(4, 52, 'TIENE REFRI', titulo)
                    ws.write(4, 53, 'VALOR REFRI', titulo)
                    ws.write(4, 54, 'TIENE LAVADORA', titulo)
                    ws.write(4, 55, 'VALOR LAVADORA', titulo)
                    ws.write(4, 56, 'TIENE E. SONIDO', titulo)
                    ws.write(4, 57, 'VALOR E. SONIDO', titulo)
                    ws.write(4, 58, 'CANT. TV', titulo)
                    ws.write(4, 59, 'VALOR CANT. TV', titulo)
                    ws.write(4, 60, 'CANT. VEHICULO', titulo)
                    ws.write(4, 61, 'VALOR CANT. VEHICULO', titulo)
                    ws.write(4, 62, 'COMPRA C. COMERCIAL', titulo)
                    ws.write(4, 63, 'VALOR COMPRA C. COMERCIAL', titulo)
                    ws.write(4, 64, 'USA INTERNET ULT. 6 MESES', titulo)
                    ws.write(4, 65, 'VALOR USA INTERNET ULT. 6 MESES', titulo)
                    ws.write(4, 66, 'EMAIL NO TRABAJO', titulo)
                    ws.write(4, 67, 'VALOR EMAIL NO TRABAJO', titulo)
                    ws.write(4, 68, 'USA REDES SOCIALES', titulo)
                    ws.write(4, 69, 'VALOR USA REDES SOCIALES', titulo)
                    ws.write(4, 70, 'LIBRO LEIDO', titulo)
                    ws.write(4, 71, 'VALOR LIBRO LEIDO', titulo)
                    ws.write(4, 72, 'NIVEL ESTUDIO JEFE HOGAR', titulo)
                    ws.write(4, 73, 'VALOR NIVEL ESTUDIO JEFE HOGAR', titulo)
                    ws.write(4, 74, 'AFILIADO IESS y/o ISSPOL o ISSFA', titulo)
                    ws.write(4, 75, 'VALOR AFILIADO IESS y/o ISSPOL o ISSFA', titulo)
                    ws.write(4, 76, 'FAMILIAR TIENE SEGURO PRIVADO', titulo)
                    ws.write(4, 77, 'VALOR FAMILIAR TIENE SEGURO PRIVADO', titulo)
                    ws.write(4, 78, 'OCUPACION JEFE HOGAR', titulo)
                    ws.write(4, 79, 'VALOR OCUPACION JEFE HOGAR', titulo)
                    ws.write(4, 80, 'ES PADRE/MADRE SOLTERO/A', titulo)
                    ws.write(4, 81, 'NUMERO HIJOS', titulo)
                    ws.write(4, 82, 'OCUPACION ESTUDIANTE', titulo)
                    ws.write(4, 83, 'INGRESO ESTUDIANTE', titulo)
                    ws.write(4, 84, 'RECIBEN BONO FMLA', titulo)
                    ws.write(4, 85, 'CANTID. MIEMBROS FMLA', titulo)

                    fila = 4
                    detalle = 3
                    g=None
                    if graduados.count()>0:
                        for g in graduados:
                            carrera=''
                            identificacion=''
                            correo=''
                            correo1=''
                            correo2=''
                            correo3=''
                            telefono=''
                            telefono2=''
                            becado=''
                            porcentajebeca=0
                            tipobeca=''
                            raza=''
                            estrato=''
                            tipodiscapacidad=''
                            porcientodiscapacidad=''
                            carnetdiscapacidad=''
                            #variables ficha socioeconomica
                            puntaje=0
                            gruposocioecon=''
                            tipohogar=''
                            cabezafamilia=''
                            esdependiente=''
                            personacubregasto=''
                            otroscubregasto=''
                            sustentahogar=''
                            tipovivienda=''
                            valortipovivienda=''
                            materialpared=''
                            valormaterialpared=''
                            materialpiso=''
                            valormaterialpiso=''
                            cantidadbanioducha=''
                            valorcantidadbanioducha=''
                            tiposshh=''
                            valortiposshh=''
                            tieneinternet=''
                            valortieneinternet=''
                            tienecomputador=''
                            valortienecomputador=''
                            tienelaptop=''
                            valortienelaptop=''
                            cantidadcelulares=''
                            valorcantidadcelulares=''
                            telfconv=''
                            valortelfconv=''
                            tienecocina=''
                            valortienecocina=''
                            tienerefri=''
                            valortienerefri=''
                            tienelavadora=''
                            valortienelavadora=''
                            tieneesonido=''
                            valortieneesonido=''
                            canttv=''
                            valorcanttv=''
                            cantvehiculo=''
                            valorcantvehiculo=''
                            compracc=''
                            valorcompracc=''
                            usainternet=''
                            valorusainternet=''
                            usaemailnotrabajo=''
                            valorusaemailnotrabajo=''
                            usaredessociales=''
                            valorusaredessociales=''
                            libroleido=''
                            valorlibroleido=''
                            nivelestudiojefehogar=''
                            valornivelestudiojefehogar=''
                            afiliadoiess=''
                            valorafiliadoiess=''
                            tieneseguroprivado=''
                            valortieneseguroprivado=''
                            ocupacionjefehogar=''
                            valorocupacionjefehogar=''
                            espadresoltero=''
                            numhijos=''
                            ocupacionestudiante=''
                            ingresoestudiante=''
                            recibenbono=''
                            cantmiembrosfmla=''

                            fila = fila +1
                            columna=0
                            # print(g.id)
                            carrera = elimina_tildes(g.inscripcion.carrera.nombre)
                            if g.inscripcion.persona.email1:
                                correo=elimina_tildes(g.inscripcion.persona.email1)
                            else:
                                correo=''
                            if g.inscripcion.persona.emailinst:
                                correo1=elimina_tildes(g.inscripcion.persona.emailinst)
                            else:
                                correo1=''
                            if g.inscripcion.persona.email1:
                                correo2=elimina_tildes(g.inscripcion.persona.email1)
                            else:
                                correo2=''
                            if g.inscripcion.persona.email2:
                                correo3=elimina_tildes(g.inscripcion.persona.email2)
                            else:
                                correo3=''
                            try:
                                if g.inscripcion.persona.telefono_conv:
                                    telefono=g.inscripcion.persona.telefono_conv.replace("-","")
                                else:
                                    telefono=''
                            except Exception as ex:
                                telefono=''
                                pass
                            try:
                                if g.inscripcion.persona.telefono:
                                    telefono2=g.inscripcion.persona.telefono.replace("-","")
                                else:
                                    telefono2=''
                            except Exception as ex:
                                telefono2=''
                                pass

                            if not g.inscripcion.persona.cedula:
                                identificacion=str(g.inscripcion.persona.pasaporte)
                            else:
                                identificacion=str(g.inscripcion.persona.cedula)

                            ultimamatricula = g.inscripcion.ultima_matricula()
                            if ultimamatricula:

                                if ultimamatricula.tipobeca:
                                    tipobeca =elimina_tildes(ultimamatricula.tipobeca.nombre)
                                else:
                                    tipobeca=''
                                if ultimamatricula.porcientobeca:
                                    porcentajebeca =str(ultimamatricula.porcientobeca)
                                else:
                                    porcentajebeca=''
                                becado='SI'
                                # porcentajebeca=str(ultimamatricula.porcientobeca)
                                # tipobeca=elimina_tildes(g.inscripcion.ultima_matricula().tipobeca.nombre)
                            else:
                                becado=''
                                porcentajebeca=''
                                tipobeca=''

                            if PerfilInscripcion.objects.filter(inscripcion=g.inscripcion).exists():
                                perfil=PerfilInscripcion.objects.filter(inscripcion=g.inscripcion)[:1].get()
                                if perfil.raza:
                                    raza=elimina_tildes(perfil.raza.nombre)
                                else:
                                    raza=''
                                if perfil.estrato:
                                    estrato= elimina_tildes(perfil.estrato.nombre)
                                else:
                                    estrato=''
                                if perfil.tipodiscapacidad:
                                    tipodiscapacidad=elimina_tildes(perfil.tipodiscapacidad.nombre)
                                else:
                                    tipodiscapacidad=''
                                if perfil.porcientodiscapacidad:
                                    porcientodiscapacidad= str(perfil.porcientodiscapacidad)
                                else:
                                    porcientodiscapacidad=''
                                if perfil.carnetdiscapacidad:
                                    carnetdiscapacidad= elimina_tildes(perfil.carnetdiscapacidad)
                                else:
                                    carnetdiscapacidad=''

                                if InscripcionFichaSocioeconomica.objects.filter(inscripcion=g.inscripcion).exists():
                                    fichasocioecon=InscripcionFichaSocioeconomica.objects.filter(inscripcion=g.inscripcion)[:1].get()
                                    if fichasocioecon.puntajetotal:
                                        puntaje=str(fichasocioecon.puntajetotal)
                                    else:
                                        puntaje=''
                                    if fichasocioecon.grupoeconomico:
                                        gruposocioecon=elimina_tildes(fichasocioecon.grupoeconomico.nombre)
                                    else:
                                        gruposocioecon=''
                                    if fichasocioecon.tipohogar:
                                        tipohogar=elimina_tildes(fichasocioecon.tipohogar.nombre)
                                    else:
                                        tipohogar=''
                                    if fichasocioecon.escabezafamilia:
                                        cabezafamilia='SI'
                                    else:
                                        cabezafamilia='NO'
                                    if fichasocioecon.esdependiente:
                                        esdependiente='SI'
                                    else:
                                        esdependiente='NO'
                                    if fichasocioecon.personacubregasto:
                                        personacubregasto=elimina_tildes(fichasocioecon.personacubregasto.nombre)
                                    else:
                                        personacubregasto=''
                                    if fichasocioecon.otroscubregasto:
                                        otroscubregasto=fichasocioecon.otroscubregasto
                                    else:
                                        otroscubregasto=''
                                    try:
                                        for sustento in fichasocioecon.sustentahogar.all():
                                            sustentahogar=elimina_tildes(sustento.persona)+' '+elimina_tildes(sustento.parentezco.nombre)
                                    except Exception as ex:
                                        sustentahogar=''
                                        pass
                                    try:
                                        if fichasocioecon.tipovivienda:
                                            tipovivienda=str(elimina_tildes(fichasocioecon.tipovivienda.nombre.replace("/","")))
                                        else:
                                            tipovivienda=''
                                    except Exception as ex:
                                        tipovivienda=''
                                        pass

                                    if fichasocioecon.materialpared:
                                        materialpared=elimina_tildes(fichasocioecon.materialpared.nombre)
                                        valormaterialpared=fichasocioecon.val_materialpared
                                    else:
                                        materialpared=''
                                        valormaterialpared=''
                                    if fichasocioecon.materialpiso:
                                        materialpiso=elimina_tildes(fichasocioecon.materialpiso.nombre)
                                        valormaterialpiso=fichasocioecon.val_materialpiso
                                    else:
                                        materialpiso=''
                                        valormaterialpiso=''
                                    if fichasocioecon.cantbannoducha:
                                        cantidadbanioducha=elimina_tildes(fichasocioecon.cantbannoducha.nombre)
                                        valorcantidadbanioducha=str(fichasocioecon.cantbannoducha.puntaje)
                                    else:
                                        cantidadbanioducha=''
                                        valorcantidadbanioducha=''
                                    if fichasocioecon.tiposervhig:
                                        tiposshh=elimina_tildes(fichasocioecon.tiposervhig.nombre)
                                        valortiposshh=str(fichasocioecon.val_tiposervhig)
                                    else:
                                        tiposshh=''
                                        valortiposshh=''
                                    if fichasocioecon.tieneinternet:
                                        tieneinternet='SI'
                                        valortieneinternet=str(fichasocioecon.val_tieneinternet)
                                    else:
                                        tieneinternet='NO'
                                        valortieneinternet=''

                                    if fichasocioecon.tienedesktop:
                                        tienecomputador='SI'
                                        valortienecomputador=str(fichasocioecon.val_tienedesktop)
                                    else:
                                        tienecomputador=''
                                        valortienecomputador=''
                                    if fichasocioecon.tienelaptop:
                                        tienelaptop='SI'
                                        valortienelaptop=str(fichasocioecon.val_tienelaptop)
                                    else:
                                        tienelaptop=''
                                        valortienelaptop=''
                                    if fichasocioecon.cantcelulares:
                                        cantidadcelulares=elimina_tildes(fichasocioecon.cantcelulares.nombre)
                                        valorcantidadcelulares=str(fichasocioecon.val_cantcelulares)
                                    else:
                                        cantidadcelulares=''
                                        valorcantidadcelulares=''
                                    if fichasocioecon.tienetelefconv:
                                        telfconv='SI'
                                        valortelfconv=str(fichasocioecon.val_tienetelefconv)
                                    else:
                                        telfconv=''
                                        valortelfconv=''
                                    if fichasocioecon.tienecocinahorno:
                                        tienecocina='SI'
                                        valortienecocina=str(fichasocioecon.val_tienecocinahorno)
                                    else:
                                        tienecocina=''
                                        valortienecocina=''
                                    if fichasocioecon.tienerefrig:
                                        tienerefri='SI'
                                        valortienerefri=str(fichasocioecon.val_tienerefrig)
                                    else:
                                        tienerefri=''
                                        valortienerefri=''
                                    if fichasocioecon.tienelavadora:
                                        tienelavadora='SI'
                                        valortienelavadora=str(fichasocioecon.val_tienelavadora)
                                    else:
                                        tienelavadora=''
                                        valortienelavadora=''
                                    if fichasocioecon.tienemusica:
                                        tieneesonido='SI'
                                        valortieneesonido=str(fichasocioecon.val_tienemusica)
                                    else:
                                        tieneesonido=''
                                        valortieneesonido=''
                                    if fichasocioecon.canttvcolor:
                                        canttv=elimina_tildes(fichasocioecon.canttvcolor.nombre)
                                        valorcanttv=str(fichasocioecon.val_canttvcolor)
                                    else:
                                        canttv=''
                                        valorcanttv=''
                                    if fichasocioecon.cantvehiculos:
                                        cantvehiculo=elimina_tildes(fichasocioecon.cantvehiculos.nombre)
                                        valorcantvehiculo=str(fichasocioecon.val_cantvehiculos)
                                    else:
                                        cantvehiculo=''
                                        valorcantvehiculo=''
                                    if fichasocioecon.compravestcc:
                                        compracc='SI'
                                        valorcompracc=str(fichasocioecon.val_compravestcc)
                                    else:
                                        compracc=''
                                        valorcompracc=''
                                    if fichasocioecon.tieneinternet:
                                        usainternet='SI'
                                        valorusainternet=str(fichasocioecon.val_tieneinternet)
                                    else:
                                        usainternet=''
                                        valorusainternet=''
                                    if fichasocioecon.usacorreonotrab:
                                        usaemailnotrabajo='SI'
                                        valorusaemailnotrabajo=str(fichasocioecon.val_usacorreonotrab)
                                    else:
                                        usaemailnotrabajo=''
                                        valorusaemailnotrabajo=''
                                    if fichasocioecon.registroredsocial:
                                        usaredessociales='SI'
                                        valorusaredessociales=str(fichasocioecon.val_registroredsocial)
                                    else:
                                        usaredessociales=''
                                        valorusaredessociales=''
                                    if fichasocioecon.leidolibrotresm:
                                        libroleido='SI'
                                        valorlibroleido=fichasocioecon.val_leidolibrotresm
                                    else:
                                        libroleido=''
                                        valorlibroleido=''
                                    if fichasocioecon.niveljefehogar:
                                        nivelestudiojefehogar=elimina_tildes(fichasocioecon.niveljefehogar.nombre)
                                        valornivelestudiojefehogar=str(fichasocioecon.val_niveljefehogar)
                                    else:
                                        nivelestudiojefehogar=''
                                        valornivelestudiojefehogar=''
                                    if fichasocioecon.alguienafiliado:
                                        afiliadoiess='SI'
                                        valorafiliadoiess=str(fichasocioecon.val_alguienafiliado)
                                    else:
                                        afiliadoiess=''
                                        valorafiliadoiess=''
                                    if fichasocioecon.alguienseguro:
                                        tieneseguroprivado='SI'
                                        valortieneseguroprivado=str(fichasocioecon.val_alguienseguro)
                                    else:
                                        tieneseguroprivado=''
                                        valortieneseguroprivado=''
                                    if fichasocioecon.ocupacionjefehogar:
                                        ocupacionjefehogar=elimina_tildes(fichasocioecon.ocupacionjefehogar.nombre)
                                        valorocupacionjefehogar=str(fichasocioecon.val_ocupacionjefehogar)
                                    else:
                                        ocupacionjefehogar=''
                                        valorocupacionjefehogar=''
                                    if fichasocioecon.p_msoltera:
                                        espadresoltero='SI'
                                        numhijos=fichasocioecon.num_hijos
                                    else:
                                        espadresoltero=''
                                        numhijos=fichasocioecon.num_hijos
                                    if fichasocioecon.ocupacionestudiante:
                                        ocupacionestudiante=elimina_tildes(fichasocioecon.ocupacionestudiante.nombre)
                                    else:
                                        ocupacionestudiante=''
                                    if fichasocioecon.ingresoestudiante:
                                        ingresoestudiante=str(fichasocioecon.ingresoestudiante.nombre)
                                    else:
                                        ingresoestudiante=''
                                    if fichasocioecon.bonofmlaestudiante:
                                        recibenbono=elimina_tildes(fichasocioecon.bonofmlaestudiante.nombre)
                                    else:
                                        recibenbono=''
                                    if fichasocioecon.cantidadmiembros:
                                        cantmiembrosfmla=str(fichasocioecon.cantidadmiembros)
                                    else:
                                        cantmiembrosfmla=''

                            ws.write(fila,columna , carrera)
                            ws.write(fila,columna+1, identificacion)
                            ws.write(fila,columna+2, elimina_tildes(g.inscripcion.persona.nombre_completo_inverso()))
                            ws.write(fila,columna+3, str(g.inscripcion.persona.sexo.nombre))
                            ws.write(fila,columna+4, str(g.fechagraduado))
                            ws.write(fila,columna+5, str(g.notatesis))
                            ws.write(fila,columna+6, str(g.notafinal))
                            ws.write(fila,columna+7, elimina_tildes(g.registro))
                            ws.write(fila,columna+8, becado)
                            ws.write(fila,columna+9, porcentajebeca)
                            ws.write(fila,columna+10, tipobeca)
                            ws.write(fila,columna+11, str(correo))
                            ws.write(fila,columna+12, str(correo1))
                            ws.write(fila,columna+13, str(correo2))
                            ws.write(fila,columna+14, str(correo3))
                            ws.write(fila,columna+15, telefono)
                            ws.write(fila,columna+16, telefono2)
                            ws.write(fila,columna+17, raza)
                            ws.write(fila,columna+18, estrato)
                            ws.write(fila,columna+19, tipodiscapacidad)
                            ws.write(fila,columna+20, porcientodiscapacidad)
                            ws.write(fila,columna+21, carnetdiscapacidad)
                            #datos ficha socioeconomica
                            ws.write(fila,columna+22, puntaje)
                            ws.write(fila,columna+23, gruposocioecon)
                            ws.write(fila,columna+24, tipohogar)
                            ws.write(fila,columna+25, cabezafamilia)
                            ws.write(fila,columna+26, esdependiente)
                            ws.write(fila,columna+27, personacubregasto)
                            ws.write(fila,columna+28, otroscubregasto)
                            ws.write(fila,columna+29, sustentahogar)
                            ws.write(fila,columna+30, tipovivienda)
                            ws.write(fila,columna+31, valortipovivienda)
                            ws.write(fila,columna+32, materialpared)
                            ws.write(fila,columna+33, valormaterialpared)
                            ws.write(fila,columna+34, materialpiso)
                            ws.write(fila,columna+35, valormaterialpiso)
                            ws.write(fila,columna+36, cantidadbanioducha)
                            ws.write(fila,columna+37, valorcantidadbanioducha)
                            ws.write(fila,columna+38, tiposshh)
                            ws.write(fila,columna+39, valortiposshh)
                            ws.write(fila,columna+40, tieneinternet)
                            ws.write(fila,columna+41, valortieneinternet)
                            ws.write(fila,columna+42, tienecomputador)
                            ws.write(fila,columna+43, valortienecomputador)
                            ws.write(fila,columna+44, tienelaptop)
                            ws.write(fila,columna+45, valortienelaptop)
                            ws.write(fila,columna+46, cantidadcelulares)
                            ws.write(fila,columna+47, valorcantidadcelulares)
                            ws.write(fila,columna+48, telfconv)
                            ws.write(fila,columna+49, valortelfconv)
                            ws.write(fila,columna+50, tienecocina)
                            ws.write(fila,columna+51, valortienecocina)
                            ws.write(fila,columna+52, tienerefri)
                            ws.write(fila,columna+53, valortienerefri)
                            ws.write(fila,columna+54, tienelavadora)
                            ws.write(fila,columna+55, valortienelavadora)
                            ws.write(fila,columna+56, tieneesonido)
                            ws.write(fila,columna+57, valortieneesonido)
                            ws.write(fila,columna+58, canttv)
                            ws.write(fila,columna+59, valorcanttv)
                            ws.write(fila,columna+60, cantvehiculo)
                            ws.write(fila,columna+61, valorcantvehiculo)
                            ws.write(fila,columna+62, compracc)
                            ws.write(fila,columna+63, valorcompracc)
                            ws.write(fila,columna+64, usainternet)
                            ws.write(fila,columna+65, valorusainternet)
                            ws.write(fila,columna+66, usaemailnotrabajo)
                            ws.write(fila,columna+67, valorusaemailnotrabajo)
                            ws.write(fila,columna+68, usaredessociales)
                            ws.write(fila,columna+69, valorusaredessociales)
                            ws.write(fila,columna+70, libroleido)
                            ws.write(fila,columna+71, valorlibroleido)
                            ws.write(fila,columna+72, nivelestudiojefehogar)
                            ws.write(fila,columna+73, valornivelestudiojefehogar)
                            ws.write(fila,columna+74, afiliadoiess)
                            ws.write(fila,columna+75, valorafiliadoiess)
                            ws.write(fila,columna+76, tieneseguroprivado)
                            ws.write(fila,columna+77, valortieneseguroprivado)
                            ws.write(fila,columna+78, ocupacionjefehogar)
                            ws.write(fila,columna+79, valorocupacionjefehogar)
                            ws.write(fila,columna+80, espadresoltero)
                            ws.write(fila,columna+81, numhijos)
                            ws.write(fila,columna+82, ocupacionestudiante)
                            ws.write(fila,columna+83, ingresoestudiante)
                            ws.write(fila,columna+84, recibenbono)
                            ws.write(fila,columna+85, cantmiembrosfmla)

                    detalle = detalle + fila

                    ws.write(detalle, 0, "Total Graduados con Discapacidad", subtitulo)
                    ws.write(detalle, 2, graduados.count())
                    detalle=detalle +1
                    ws.write(detalle, 0, "Fecha Impresion", subtitulo)
                    ws.write(detalle, 2, str(datetime.now()), subtitulo)
                    detalle=detalle +1
                    ws.write(detalle, 0, "Usuario", subtitulo)
                    ws.write(detalle, 2, str(request.user), subtitulo)

                    nombre ='graduadoscondiscapacidad'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")
                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)+" "+str(g)}),content_type="application/json")

        else:
            data = {'title': 'Listado de Graduados con Discapacidad'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform']=GraduadosMatrizForm()
                return render(request ,"reportesexcel/graduados_condiscapacidad.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

