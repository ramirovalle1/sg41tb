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
                    m = 5
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    center = xlwt.easyxf('align: horiz center')
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('InformacionEstudiantes',cell_overwrite_ok=True)
                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,m+18, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,m+18, 'LISTADO DE INFORMACION DE ESTUDIANTES ', titulo2)
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
                        inscripid = Matricula.objects.filter(nivel__periodo=periodo,nivel__nivelmalla__in=(1,2,3,4,5,6,10),nivel__carrera__carrera=True).exclude(nivel__carrera__in=(63,66)).distinct('inscripcion').values('inscripcion')
                    else:
                        inicio = convertir_fecha( request.POST['inicio'])
                        fin = convertir_fecha(request.POST['fin'])
                        inscripid = Matricula.objects.filter(nivel__periodo__inicio__gte=inicio,nivel__periodo__inicio__lte=fin,nivel__nivelmalla__in=(1,2,3,4,5,6,10),nivel__carrera__carrera=True).exclude(nivel__carrera__in=(63,66)).distinct('inscripcion').values('inscripcion')

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
                    ws.write(4, 16, 'TIPO DISCAPACIDAD', titulo)
                    ws.write(4, 17, 'PORCIENTO DISCAPACIDAD', titulo)
                    ws.write(4, 18, 'CARNET DISCAPACIDAD', titulo)
                    #OCastillo 06-05-2022 datos adicionales segun correo
                    ws.write(4, 19, 'F. NACIMIENTO', titulo)
                    ws.write(4, 20, 'EDAD', titulo)
                    ws.write(4, 21, 'PROVINCIA NACIMIENTO', titulo)
                    ws.write(4, 22, 'PROVINCIA RESIDENCIA', titulo)

                    fila = 5
                    detalle = 3
                    g=None
                    totalinscritos=0
                    for i in Inscripcion.objects.filter(id__in=inscripid):
                    # for i in Inscripcion.objects.filter(id=75166):
                        # print(i.id)
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


                        columna=0
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
                        try:
                            if i.persona.email2:
                                correo3=elimina_tildes(i.persona.email2)
                            else:
                                correo3=''
                        except Exception as ex:
                            correo3=''
                            pass
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

                            ws.write(fila,columna, carrera)
                            ws.write(fila,columna+1, nivel)
                            ws.write(fila,columna+2, grupo)
                            ws.write(fila,columna+3, identificacion)
                            ws.write(fila,columna+4, elimina_tildes(i.persona.nombre_completo_inverso()))
                            ws.write(fila,columna+5, str(i.persona.sexo.nombre))
                            ws.write(fila,columna+6, becado)
                            ws.write(fila,columna+7, porcentajebeca)
                            ws.write(fila,columna+8, tipobeca)
                            ws.write(fila,columna+9,  str(correo))
                            ws.write(fila,columna+10, str(correo1))
                            ws.write(fila,columna+11, str(correo2))
                            ws.write(fila,columna+12, str(correo3))
                            ws.write(fila,columna+13, telefono)
                            ws.write(fila,columna+14, telefono2)
                            ws.write(fila,columna+15, raza)
                            ws.write(fila,columna+16, tipodiscapacidad)
                            ws.write(fila,columna+17, porcientodiscapacidad)
                            ws.write(fila,columna+18, carnetdiscapacidad)
                            ws.write(fila,columna+19, f_nacimiento)
                            ws.write(fila,columna+20, edad)
                            ws.write(fila,columna+21, prov_nacimiento)
                            ws.write(fila,columna+22, prov_residencia)
                            totalinscritos+=1
                            fila = fila +1

                    detalle = detalle + fila

                    ws.write(detalle, 0, "Total Estudiantes", subtitulo)
                    ws.write(detalle, 2, totalinscritos)
                    detalle=detalle +1
                    ws.write(detalle, 0, "Fecha Impresion", subtitulo)
                    ws.write(detalle, 2, str(datetime.now()), subtitulo)
                    detalle=detalle +1
                    ws.write(detalle, 0, "Usuario", subtitulo)
                    ws.write(detalle, 2, str(request.user), subtitulo)

                    nombre ='estudiantesinformaciondobe'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")
                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)+" "+str(i)}),content_type="application/json")

        else:
            data = {'title': 'Listado de Estudiantes'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform']= CacesRangoPeriodoForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
                return render(request ,"reportesexcel/estudiantes_informaciondobe.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

