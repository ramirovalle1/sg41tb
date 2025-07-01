from datetime import datetime,timedelta
import json
import xlrd
import xlwt

from django.contrib.auth.decorators import login_required

from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from settings import UTILIZA_GRUPOS_ALUMNOS, EMAIL_ACTIVE,MEDIA_ROOT, ASIG_VINCULACION, ASIG_PRATICA
from sga.commonviews import addUserData, ip_client_address
from sga.forms import CacesRangoPeriodoForm
from sga.models import TituloInstitucion,convertir_fecha,ReporteExcel,Inscripcion,Matricula,PerfilInscripcion,Periodo
from socioecon.models import  InscripcionFichaSocioeconomica,PersonaSustentaHogar
from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action :
                try:
                    periodo=None
                    inicio=''
                    fin=''


                    # anio = request.POST['anio']
                    # graduados = Graduado.objects.filter(fechagraduado__year=anio,inscripcion__tienediscapacidad=True).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')
                    # totalg = graduados.count()
                    m = 5
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    center = xlwt.easyxf('align: horiz center')
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('EstudiantesconDiscapacidad',cell_overwrite_ok=True)
                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,m+52, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,m+52, 'LISTADO DE ESTUDIANTES CON DISCAPACIDAD ', titulo2)
                    if request.POST['periodo'] != '':
                        periodo= Periodo.objects.filter(pk=request.POST['periodo'])[:1].get()
                        ws.write (2, 0, 'Periodo: ',center )
                        ws.write (2, 1, str(periodo.nombre),titulo)
                    else:
                        inicio = convertir_fecha( request.POST['inicio'])
                        fin = convertir_fecha(request.POST['fin'])
                        ws.write (2, 0, 'Desde: ',center)
                        ws.write (2, 1, str(inicio.date()),titulo)
                        ws.write (3, 0, 'Hasta: ',center)
                        ws.write (3, 1, str(fin.date()),titulo)
                    if request.POST['periodo'] != '':
                        periodo= Periodo.objects.filter(pk=request.POST['periodo'])[:1].get()
                        inscripid = Matricula.objects.filter(becado=True,nivel__periodo=periodo,nivel__nivelmalla__in=(1,2,3,4,5,6,10),nivel__carrera__carrera=True,inscripcion__tienediscapacidad=True).distinct('inscripcion').values('inscripcion')
                    else:
                        inicio = convertir_fecha( request.POST['inicio'])
                        fin = convertir_fecha(request.POST['fin'])
                        inscripid = Matricula.objects.filter(becado=True,nivel__periodo__inicio__gte=inicio,nivel__periodo__inicio__lte=fin,nivel__nivelmalla__in=(1,2,3,4,5,6,10),nivel__carrera__carrera=True,inscripcion__tienediscapacidad=True).distinct('inscripcion').values('inscripcion')

                    ws.write(4, 0, 'CARRERA', titulo)
                    ws.write(4, 1, 'NIVEL', titulo)
                    ws.write(4, 2, 'GRUPO', titulo)
                    ws.write(4, 3, 'IDENTIFICACION', titulo)
                    ws.write(4, 4, 'NOMBRES', titulo)
                    ws.write(4, 5, 'SEXO', titulo)
                    ws.write(4, 6, 'BECADO', titulo)
                    ws.write(4, 7, 'POR CIENTO BECA', titulo)
                    ws.write(4, 8, 'TIPO BECA', titulo)
                    ws.write(4, 9, 'EMAIL PERSONAL', titulo)
                    ws.write(4, 10, 'EMAIL INST',titulo)
                    ws.write(4, 11, 'EMAIL 1',titulo)
                    ws.write(4, 12, 'EMAIL 2',titulo)
                    ws.write(4, 13, 'TLF. CONVENCIONAL', titulo)
                    ws.write(4, 14, 'CELULAR', titulo)
                    ws.write(4, 15, 'RAZA', titulo)
                    ws.write(4, 16, 'ESTRATO', titulo)
                    ws.write(4, 17, 'TIPO DISCAPACIDAD', titulo)
                    ws.write(4, 18, 'PORCIENTO DISCAPACIDAD', titulo)
                    ws.write(4, 19, 'CARNET DISCAPACIDAD', titulo)
                    # Datos Ficha Socioeconomica
                    ws.write(4, 20, 'PUNTAJE TOTAL', titulo)
                    ws.write(4, 21, 'GRUPO SOCIOECONOMICO', titulo)
                    ws.write(4, 22, 'TIPO HOGAR', titulo)
                    ws.write(4, 23, 'ES CABEZA DE FAMILIA', titulo)
                    ws.write(4, 24, 'ES DEPENDIENTE', titulo)
                    ws.write(4, 25, 'PERSONA CUBRE GASTO', titulo)
                    ws.write(4, 26, 'OTROS CUBRE GASTO', titulo)
                    ws.write(4, 27, 'SUSTENTA HOGAR', titulo)
                    ws.write(4, 28, 'TIPO VIVIENDA', titulo)
                    ws.write(4, 29, 'VALOR TIPO VIVIENDA', titulo)
                    ws.write(4, 30, 'MATERIAL PARED', titulo)
                    ws.write(4, 31, 'VALOR MATERIAL PARED', titulo)
                    ws.write(4, 32, 'MATERIAL PISO', titulo)
                    ws.write(4, 33, 'VALOR MATERIAL PISO', titulo)
                    ws.write(4, 34, 'CANTIDAD BANIO DUCHA', titulo)
                    ws.write(4, 35, 'VALOR BANIO DUCHA', titulo)
                    ws.write(4, 36, 'TIPO SSHH', titulo)
                    ws.write(4, 37, 'VALOR TIPO SSHH', titulo)
                    ws.write(4, 38, 'TIENE INTERNET', titulo)
                    ws.write(4, 39, 'VALOR INTERNET', titulo)
                    ws.write(4, 40, 'TIENE COMPUTADOR', titulo)
                    ws.write(4, 41, 'VALOR COMPUTADOR', titulo)
                    ws.write(4, 42, 'TIENE LAPTOP', titulo)
                    ws.write(4, 43, 'VALOR LAPTOP', titulo)
                    ws.write(4, 44, 'CANT. CELULARES', titulo)
                    ws.write(4, 45, 'VALOR CANT. CELULARES', titulo)
                    ws.write(4, 46, 'TELEF. CONV,', titulo)
                    ws.write(4, 47, 'VALOR TELEF. CONV,', titulo)
                    ws.write(4, 48, 'TIENE COCINA/HORNO', titulo)
                    ws.write(4, 49, 'VALOR COCINA/HORNO', titulo)
                    ws.write(4, 50, 'TIENE REFRI', titulo)
                    ws.write(4, 51, 'VALOR REFRI', titulo)
                    ws.write(4, 52, 'TIENE LAVADORA', titulo)
                    ws.write(4, 53, 'VALOR LAVADORA', titulo)
                    ws.write(4, 54, 'TIENE E. SONIDO', titulo)
                    ws.write(4, 55, 'VALOR E. SONIDO', titulo)
                    ws.write(4, 56, 'CANT. TV', titulo)
                    ws.write(4, 57, 'VALOR CANT. TV', titulo)
                    ws.write(4, 58, 'CANT. VEHICULO', titulo)
                    ws.write(4, 59, 'VALOR CANT. VEHICULO', titulo)
                    ws.write(4, 60, 'COMPRA C. COMERCIAL', titulo)
                    ws.write(4, 61, 'VALOR COMPRA C. COMERCIAL', titulo)
                    ws.write(4, 62, 'USA INTERNET ULT. 6 MESES', titulo)
                    ws.write(4, 63, 'VALOR USA INTERNET ULT. 6 MESES', titulo)
                    ws.write(4, 64, 'EMAIL NO TRABAJO', titulo)
                    ws.write(4, 65, 'VALOR EMAIL NO TRABAJO', titulo)
                    ws.write(4, 66, 'USA REDES SOCIALES', titulo)
                    ws.write(4, 67, 'VALOR USA REDES SOCIALES', titulo)
                    ws.write(4, 68, 'LIBRO LEIDO', titulo)
                    ws.write(4, 69, 'VALOR LIBRO LEIDO', titulo)
                    ws.write(4, 70, 'NIVEL ESTUDIO JEFE HOGAR', titulo)
                    ws.write(4, 71, 'VALOR NIVEL ESTUDIO JEFE HOGAR', titulo)
                    ws.write(4, 72, 'AFILIADO IESS y/o ISSPOL o ISSFA', titulo)
                    ws.write(4, 73, 'VALOR AFILIADO IESS y/o ISSPOL o ISSFA', titulo)
                    ws.write(4, 74, 'FAMILIAR TIENE SEGURO PRIVADO', titulo)
                    ws.write(4, 75, 'VALOR FAMILIAR TIENE SEGURO PRIVADO', titulo)
                    ws.write(4, 76, 'OCUPACION JEFE HOGAR', titulo)
                    ws.write(4, 77, 'VALOR OCUPACION JEFE HOGAR', titulo)
                    ws.write(4, 78, 'ES PADRE/MADRE SOLTERO/A', titulo)
                    ws.write(4, 79, 'NUMERO HIJOS', titulo)
                    ws.write(4, 80, 'OCUPACION ESTUDIANTE', titulo)
                    ws.write(4, 81, 'INGRESO ESTUDIANTE', titulo)
                    ws.write(4, 82, 'RECIBEN BONO FMLA', titulo)
                    ws.write(4, 83, 'CANTID. MIEMBROS FMLA', titulo)
                    #OCastillo 06-05-2022 datos adicionales segun correo
                    ws.write(4, 84, 'F. NACIMIENTO', titulo)
                    ws.write(4, 85, 'EDAD', titulo)
                    ws.write(4, 86, 'PROVINCIA NACIMIENTO', titulo)
                    ws.write(4, 87, 'PROVINCIA RESIDENCIA', titulo)

                    fila = 4
                    detalle = 3
                    g=None
                    totalinscritos=0
                    for i in Inscripcion.objects.filter(id__in=inscripid):
                        totalinscritos+=1
                        f_nacimiento=''
                        edad=''
                        prov_nacimiento=''
                        prov_residencia=''
                        nivel=''
                        grupo=''
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
                        carrera = elimina_tildes(i.carrera.nombre)
                        if i.persona.email1:
                            correo=elimina_tildes(i.persona.email1)
                        else:
                            correo=''
                        if i.persona.emailinst:
                            correo1=elimina_tildes(i.persona.emailinst)
                        else:
                            correo1=''
                        if i.persona.email1:
                            correo2=elimina_tildes(i.persona.email1)
                        else:
                            correo2=''
                        if i.persona.email2:
                            correo3=elimina_tildes(i.persona.email2)
                        else:
                            correo3=''
                        try:
                            if i.persona.telefono_conv:
                                telefono=i.persona.telefono_conv.replace("-","")
                            else:
                                telefono=''
                        except Exception as ex:
                            telefono=''
                            pass
                        try:
                            if i.persona.telefono:
                                telefono2=i.persona.telefono.replace("-","")
                            else:
                                telefono2=''
                        except Exception as ex:
                            telefono2=''
                            pass

                        if not i.persona.cedula:
                            identificacion=str(i.persona.pasaporte)
                        else:
                            identificacion=str(i.persona.cedula)

                        if i.persona.nacimiento:
                            edad= str(i.persona.edad_actual())
                            f_nacimiento=str(i.persona.nacimiento)
                        else:
                            edad= ''
                            f_nacimiento=''

                        if i.persona.provincia:
                            prov_nacimiento=elimina_tildes(i.persona.provincia.nombre)
                        else:
                            prov_nacimiento=''
                        if i.persona.provinciaresid:
                            prov_residencia=elimina_tildes(i.persona.provinciaresid.nombre)
                        else:
                            prov_residencia=''

                        if periodo:
                            if Matricula.objects.filter(inscripcion=i,nivel__periodo=periodo).exists():
                                matricula = Matricula.objects.filter(inscripcion=i,nivel__periodo=periodo)[:1].get()
                            else:
                                matricula = None
                        else:
                            if Matricula.objects.filter(inscripcion=i,nivel__periodo__inicio__gte=inicio,nivel__periodo__inicio__lte=fin,nivel__nivelmalla__in=(1,2,3,4,5,6),nivel__carrera__carrera=True).exists():
                                matricula=Matricula.objects.filter(inscripcion=i,nivel__periodo__inicio__gte=inicio,nivel__periodo__inicio__lte=fin,nivel__nivelmalla__in=(1,2,3,4,5,6),nivel__carrera__carrera=True)[:1].get()

                            else:
                                matricula=None

                        if matricula:
                            nivel=elimina_tildes(matricula.nivel.nivelmalla.nombre)
                            grupo=elimina_tildes(matricula.nivel.grupo.nombre)
                            try:
                                if matricula.becado:
                                    becado='SI'
                                    porcentajebeca=str(matricula.porcientobeca)
                                    tipobeca=elimina_tildes(matricula.tipobeca.nombre)
                                else:
                                    becado=''
                                    porcentajebeca=''
                                    tipobeca=''
                            except Exception as ex:
                                porcentajebeca=''
                                tipobeca=''
                                pass

                        else:
                            nivel=''
                            grupo=''

                        if PerfilInscripcion.objects.filter(inscripcion=i).exists():
                            perfil=PerfilInscripcion.objects.filter(inscripcion=i)[:1].get()
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

                            if InscripcionFichaSocioeconomica.objects.filter(inscripcion=i).exists():
                                fichasocioecon=InscripcionFichaSocioeconomica.objects.filter(inscripcion=i)[:1].get()
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
                            ws.write(fila,columna+1, nivel)
                            ws.write(fila,columna+2, grupo)
                            ws.write(fila,columna+3, identificacion)
                            ws.write(fila,columna+4, elimina_tildes(i.persona.nombre_completo_inverso()))
                            ws.write(fila,columna+5, str(i.persona.sexo.nombre))
                            ws.write(fila,columna+6, becado)
                            ws.write(fila,columna+7, porcentajebeca)
                            ws.write(fila,columna+8, tipobeca)
                            ws.write(fila,columna+9, str(correo))
                            ws.write(fila,columna+10, str(correo1))
                            ws.write(fila,columna+11, str(correo2))
                            ws.write(fila,columna+12, str(correo3))
                            ws.write(fila,columna+13, telefono)
                            ws.write(fila,columna+14, telefono2)
                            ws.write(fila,columna+15, raza)
                            ws.write(fila,columna+16, estrato)
                            ws.write(fila,columna+17, tipodiscapacidad)
                            ws.write(fila,columna+18, porcientodiscapacidad)
                            ws.write(fila,columna+19, carnetdiscapacidad)
                            #datos ficha socioeconomica
                            ws.write(fila,columna+20, puntaje)
                            ws.write(fila,columna+21, gruposocioecon)
                            ws.write(fila,columna+22, tipohogar)
                            ws.write(fila,columna+23, cabezafamilia)
                            ws.write(fila,columna+24, esdependiente)
                            ws.write(fila,columna+25, personacubregasto)
                            ws.write(fila,columna+26, otroscubregasto)
                            ws.write(fila,columna+27, sustentahogar)
                            ws.write(fila,columna+28, tipovivienda)
                            ws.write(fila,columna+29, valortipovivienda)
                            ws.write(fila,columna+30, materialpared)
                            ws.write(fila,columna+31, valormaterialpared)
                            ws.write(fila,columna+32, materialpiso)
                            ws.write(fila,columna+33, valormaterialpiso)
                            ws.write(fila,columna+34, cantidadbanioducha)
                            ws.write(fila,columna+35, valorcantidadbanioducha)
                            ws.write(fila,columna+36, tiposshh)
                            ws.write(fila,columna+37, valortiposshh)
                            ws.write(fila,columna+38, tieneinternet)
                            ws.write(fila,columna+39, valortieneinternet)
                            ws.write(fila,columna+40, tienecomputador)
                            ws.write(fila,columna+41, valortienecomputador)
                            ws.write(fila,columna+42, tienelaptop)
                            ws.write(fila,columna+43, valortienelaptop)
                            ws.write(fila,columna+44, cantidadcelulares)
                            ws.write(fila,columna+45, valorcantidadcelulares)
                            ws.write(fila,columna+46, telfconv)
                            ws.write(fila,columna+47, valortelfconv)
                            ws.write(fila,columna+48, tienecocina)
                            ws.write(fila,columna+49, valortienecocina)
                            ws.write(fila,columna+50, tienerefri)
                            ws.write(fila,columna+51, valortienerefri)
                            ws.write(fila,columna+52, tienelavadora)
                            ws.write(fila,columna+53, valortienelavadora)
                            ws.write(fila,columna+54, tieneesonido)
                            ws.write(fila,columna+55, valortieneesonido)
                            ws.write(fila,columna+56, canttv)
                            ws.write(fila,columna+57, valorcanttv)
                            ws.write(fila,columna+58, cantvehiculo)
                            ws.write(fila,columna+59, valorcantvehiculo)
                            ws.write(fila,columna+60, compracc)
                            ws.write(fila,columna+61, valorcompracc)
                            ws.write(fila,columna+62, usainternet)
                            ws.write(fila,columna+63, valorusainternet)
                            ws.write(fila,columna+64, usaemailnotrabajo)
                            ws.write(fila,columna+65, valorusaemailnotrabajo)
                            ws.write(fila,columna+66, usaredessociales)
                            ws.write(fila,columna+67, valorusaredessociales)
                            ws.write(fila,columna+68, libroleido)
                            ws.write(fila,columna+69, valorlibroleido)
                            ws.write(fila,columna+70, nivelestudiojefehogar)
                            ws.write(fila,columna+71, valornivelestudiojefehogar)
                            ws.write(fila,columna+72, afiliadoiess)
                            ws.write(fila,columna+73, valorafiliadoiess)
                            ws.write(fila,columna+74, tieneseguroprivado)
                            ws.write(fila,columna+75, valortieneseguroprivado)
                            ws.write(fila,columna+76, ocupacionjefehogar)
                            ws.write(fila,columna+77, valorocupacionjefehogar)
                            ws.write(fila,columna+78, espadresoltero)
                            ws.write(fila,columna+79, numhijos)
                            ws.write(fila,columna+80, ocupacionestudiante)
                            ws.write(fila,columna+81, ingresoestudiante)
                            ws.write(fila,columna+82, recibenbono)
                            ws.write(fila,columna+83, cantmiembrosfmla)
                            #datos adicionales
                            ws.write(fila,columna+84, f_nacimiento)
                            ws.write(fila,columna+85, edad)
                            ws.write(fila,columna+86, prov_nacimiento)
                            ws.write(fila,columna+87, prov_residencia)

                    detalle = detalle + fila

                    ws.write(detalle, 0, "Total Estudiantes con Discapacidad", subtitulo)
                    ws.write(detalle, 2, totalinscritos)
                    detalle=detalle +1
                    ws.write(detalle, 0, "Fecha Impresion", subtitulo)
                    ws.write(detalle, 2, str(datetime.now()), subtitulo)
                    detalle=detalle +1
                    ws.write(detalle, 0, "Usuario", subtitulo)
                    ws.write(detalle, 2, str(request.user), subtitulo)

                    nombre ='estudiantescondiscapacidad'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")
                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)+" "+str(i)}),content_type="application/json")

        else:
            data = {'title': 'Listado de Estudiantes con Discapacidad'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform']= CacesRangoPeriodoForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
                return render(request ,"reportesexcel/estudiantes_condiscapacidad.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

