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
from sga.models import convertir_fecha,TituloInstitucion,ReporteExcel,Graduado,ConvalidacionInscripcion,Matricula,Tutoria
from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action :

                try:
                    anio = request.POST['anio']
                    graduados = Graduado.objects.filter(fechagraduado__year=anio).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')
                    totalg = graduados.count()
                    m = 5
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    center = xlwt.easyxf('align: horiz center')
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('Graduados',cell_overwrite_ok=True)
                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0, 0, 20,)
                    ws.write_merge(1, 1, 0, 20,)
                    ws.write (0, 0, elimina_tildes(tit.nombre),center )
                    ws.write(1, 0, 'MATRIZ DE GRADUADOS '+ str(anio) )
                    ws.write(3, 0, 'CODIGO_IES', titulo)
                    ws.write(3, 1, 'CODIGO_CARRERA', titulo)
                    ws.write(3, 2, 'CIUDAD_CARRERA', titulo)
                    ws.write(3, 3, 'TIPO_IDENTIFICACION', titulo)
                    ws.write(3, 4, 'IDENTIFICACION', titulo)
                    ws.write(3, 5, 'PRIMER_APELLIDO', titulo)
                    ws.write(3, 6, 'SEGUNGO_APELLIDO', titulo)
                    ws.write(3, 7, 'NOMBRES', titulo)
                    ws.write(3, 8, 'SEXO', titulo)
                    ws.write(3, 9, 'FECHA_NACIMIENTO', titulo)
                    ws.write(3, 10,'PAIS_ORIGEN', titulo)
                    ws.write(3, 11,'DISCAPACIDAD', titulo)
                    ws.write(3, 12,'NUMERO_CONADIS', titulo)
                    ws.write(3, 13,'DIRECCION', titulo)
                    ws.write(3, 14,'EMAIL_PERSONAL', titulo)
                    ws.write(3, 15,'EMAIL_INSTITUCIONAL', titulo)
                    ws.write(3, 16,'FECHA_INICIO_PRIMERNIVEL', titulo)
                    ws.write(3, 17,'FECHA_INGRESO_CONVALIDACION', titulo)
                    ws.write(3, 18,'FECHA_GRADUACION', titulo)
                    ws.write(3, 19,'MECANISMO_TITULACION', titulo)
                    ws.write(3, 20,'CARRERA', titulo)
                    ws.write(3, 21,'MODALIDAD', titulo)

                    fila = 3
                    detalle = 3
                    g=None
                    if graduados.count()>0:
                        for g in graduados:
                            #print(g.id)
                            nombres=''
                            apellido1=''
                            apellido2=''
                            documento=''
                            codigocarrera=''
                            tipodocumento=''
                            fechagraduacion=''
                            fechaconvalidacion=''
                            fechainicioprimernivel=''
                            fechanacimiento=''
                            correo1=''
                            correo2=''
                            paisorigen=''
                            sexo=''
                            direccion=''
                            discapacidad=''
                            carnetnumero=''
                            mecanismotitulacion=''
                            modalidad=''
                            fila = fila +1
                            columna=0
                            if g.inscripcion.persona.pasaporte:
                                tipodocumento = 'PASAPORTE'
                                try:
                                    documento = g.inscripcion.persona.pasaporte
                                except:
                                    documento= 'ERROR AL OBTENER PASAPORTE '
                            else:
                                tipodocumento = 'CEDULA'
                                try:
                                    documento = g.inscripcion.persona.cedula
                                except:
                                    documento= 'ERROR AL OBTENER CEDULA '

                            if ConvalidacionInscripcion.objects.filter(record__inscripcion=g.inscripcion).exists():
                                conval =ConvalidacionInscripcion.objects.filter(record__inscripcion=g.inscripcion).order_by('id')[:1].get()
                                try:
                                    if conval.fecha:
                                        fechaconvalidacion = conval.fecha.strftime('%Y-%m-%d')
                                    else:
                                        fechaconvalidacion =str(conval.anno)
                                except:
                                    fechaconvalidacion= 'ERROR EN FECHA CONVALIDACION '
                            else:
                                if Matricula.objects.filter(inscripcion=g.inscripcion,nivel__nivelmalla__id=1).exists():
                                    matfech = Matricula.objects.filter(inscripcion=g.inscripcion,nivel__nivelmalla__id=1).order_by('id')[:1].get()
                                else:
                                    if  Matricula.objects.filter(inscripcion=g.inscripcion,nivel__nivelmalla__id__in=(1,2,3,4,5,6)).exists():
                                        matfech = Matricula.objects.filter(inscripcion=g.inscripcion,nivel__nivelmalla__id__in=(1,2,3,4,5,6)).order_by('id')[:1].get()
                                if matfech !='':
                                    try:
                                        fechainicioprimernivel = matfech.nivel.periodo.inicio.strftime('%Y-%m-%d')
                                        try:
                                            # nivel = matfech.nivel.nivelmalla.nombre
                                            # grupo = matfech.nivel.grupo.nombre
                                            modalidad=matfech.nivel.grupo.modalidad.nombre
                                        except Exception as e:
                                            # nivel = 'NO SE PUDO OBTENER EL NIVEL'
                                            # grupo=''
                                            modalidad=''
                                    except:
                                        fechainicioprimernivel = 'ERROR EN FECHA INICIO'
                                        try:
                                            # nivel = matfech.nivel.nivelmalla.nombre
                                            # grupo = matfech.nivel.grupo.nombre
                                            modalidad=matfech.nivel.grupo.modalidad.nombre
                                        except Exception as e:
                                            # nivel = 'NO SE PUDO OBTENER EL NIVEL'
                                            # grupo=''
                                            modalidad=''


                            if g.inscripcion.persona.sexo.id==1:
                                sexo='FEMENINO'

                            else:
                                sexo = 'MASCULINO'

                            try:
                                fechagraduacion = g.fechagraduado.strftime('%d-%m-%Y')
                            except:
                                fechagraduacion='ERROR EN FECHA GRADUACION'

                            try:
                                fechanacimiento = g.inscripcion.persona.nacimiento.strftime('%d-%m-%Y')
                            except:
                                fechanacimiento='ERROR EN FECHA NACIMIENTO'

                            # if g.tematesis!='':
                            #     try:
                            #         if str(g.tematesis).strip()=="EXAMEN COMPLEXIVO":
                            #             mecanismotitulacion = "EXAMEN COMPLEXIVO"
                            #         else:
                            #             mecanismotitulacion = "TRABAJO TITULACION"
                            #     except:
                            #             mecanismotitulacion='TRABAJO TITULACION'

                            # OCU 15-06-2021 si estudiante tiene tutoria es trabajo de titulacion
                            if Tutoria.objects.filter(estudiante=g.inscripcion,numtutoria=10).exists():
                                mecanismotitulacion = "TRABAJO TITULACION"
                            else:
                                mecanismotitulacion = "EXAMEN COMPLEXIVO"

                            if g.inscripcion.persona.emailinst:
                                correo1=elimina_tildes(g.inscripcion.persona.emailinst)
                            else:
                                correo1=''

                            if g.inscripcion.persona.email1:
                                correo2=elimina_tildes(g.inscripcion.persona.email1)
                            else:
                                correo2=''

                            try:
                                if g.inscripcion.persona.direccion:
                                    direccion=elimina_tildes(g.inscripcion.persona.direccion)
                            except:
                                direccion='ERROR AL OBTENER DIRECCION'

                            discapacidad='NINGUNA '
                            if g.inscripcion.nee():
                                if g.inscripcion.nee().tienediscapacidad:
                                    carnetnumero = g.inscripcion.nee().carnetdiscapacidad
                                    if g.inscripcion.nee().tipodiscapacidad:
                                        try:
                                            discapacidad = elimina_tildes(g.inscripcion.nee().tipodiscapacidad.nombre)
                                        except :
                                            discapacidad= 'ERROR AL OBTENER DISCAPACIDAD'

                            if g.inscripcion.carrera:
                                carrera=elimina_tildes(g.inscripcion.carrera.nombre)
                            else:
                                carrera=''
                            if g.inscripcion.carrera.codigocarrera:
                                codigocarrera=elimina_tildes(g.inscripcion.carrera.codigocarrera)
                            else:
                                codigocarrera=''

                            if g.inscripcion.persona.nacionalidad:
                                if g.inscripcion.persona.nacionalidad.id == 1:
                                    paisorigen = 'ECUADOR'
                                elif g.inscripcion.persona.nacionalidad.id == 2:
                                    paisorigen = 'CUBA'
                                elif g.inscripcion.persona.nacionalidad.id == 3:
                                    paisorigen = 'COLOMBIA'
                                elif g.inscripcion.persona.nacionalidad.id == 4:
                                    paisorigen = 'VENEZUELA'
                                elif g.inscripcion.persona.nacionalidad.id == 5:
                                    paisorigen = 'COREA'
                                elif g.inscripcion.persona.nacionalidad.id == 6:
                                    paisorigen = 'PERU'
                                elif g.inscripcion.persona.nacionalidad.id == 7:
                                    paisorigen = 'ESTADOS UNIDOS'
                                elif g.inscripcion.persona.nacionalidad.id == 8:
                                    paisorigen = 'ESPANA'
                                elif g.inscripcion.persona.nacionalidad.id == 9:
                                    paisorigen = 'BRASIL'
                                elif g.inscripcion.persona.nacionalidad.id == 10:
                                    paisorigen = 'ARGENTINA'
                                elif g.inscripcion.persona.nacionalidad.id == 11:
                                    paisorigen = 'CHILE'
                                elif g.inscripcion.persona.nacionalidad.id == 12:
                                    paisorigen = 'COSTA RICA'
                                elif g.inscripcion.persona.nacionalidad.id == 13:
                                    paisorigen = 'CHINA'
                                elif g.inscripcion.persona.nacionalidad.id == 14:
                                    paisorigen = 'PARAGUAY'
                                elif g.inscripcion.persona.nacionalidad.id == 15:
                                    paisorigen = 'ITALIA'
                                elif g.inscripcion.persona.nacionalidad.id == 16:
                                    paisorigen = 'ALEMANIA'

                            try:
                                ws.write(fila,columna+3, elimina_tildes(g.inscripcion.persona.email))
                            except Exception as ex:
                                ws.write(fila,columna+3, "")

                            try:
                                nombres = elimina_tildes(g.inscripcion.persona.nombres)
                            except:
                                nombres ='ERROR EN NOMBRES'
                            try:
                                apellido1 = elimina_tildes(g.inscripcion.persona.apellido1)
                            except:
                                apellido1 ='ERROR EN APELLIDO1'

                            try:
                                apellido2 = elimina_tildes(g.inscripcion.persona.apellido2)
                            except:
                                apellido2 ='ERROR EN APELLIDO2'

                            ws.write(fila,columna, '2397')
                            ws.write(fila,columna+1, codigocarrera)
                            ws.write(fila,columna+2, 'GUAYAQUIL')
                            ws.write(fila,columna+3, str(tipodocumento))
                            ws.write(fila,columna+4, str(documento))
                            ws.write(fila,columna+5, str(apellido1))
                            ws.write(fila,columna+6, str(apellido2))
                            ws.write(fila,columna+7, str(nombres))
                            ws.write(fila,columna+8, str(sexo))
                            ws.write(fila,columna+9, str(fechanacimiento))
                            ws.write(fila,columna+10, str(paisorigen))
                            ws.write(fila,columna+11, str(discapacidad))
                            ws.write(fila,columna+12, str(carnetnumero))
                            ws.write(fila,columna+13, str(direccion))
                            ws.write(fila,columna+14,str(correo1))
                            ws.write(fila,columna+15,str(correo2))
                            ws.write(fila,columna+16,str(fechainicioprimernivel))
                            ws.write(fila,columna+17,str(fechaconvalidacion))
                            ws.write(fila,columna+18,str(fechagraduacion))
                            ws.write(fila,columna+19,str(mecanismotitulacion))
                            ws.write(fila,columna+20,carrera)
                            ws.write(fila,columna+21,str(modalidad))

                    detalle = detalle + fila
                    ws.write(detalle, 0, "Fecha Impresion", subtitulo)
                    ws.write(detalle, 2, str(datetime.now()), subtitulo)
                    detalle=detalle +1
                    ws.write(detalle, 0, "Usuario", subtitulo)
                    ws.write(detalle, 2, str(request.user), subtitulo)


                    nombre ='matriz_graduados'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)+" "+str(g)}),content_type="application/json")

        else:
            data = {'title': 'Matriz de Graduados por Anio'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform']=GraduadosMatrizForm()
                return render(request ,"reportesexcel/matriz_graduados.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

