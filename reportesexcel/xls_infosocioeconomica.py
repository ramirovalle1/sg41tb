from datetime import date, datetime
import json
from django.http import HttpResponse, HttpResponseRedirect

from django.shortcuts import render
from requests.packages.urllib3 import request
import xlwt
from settings import MEDIA_ROOT
from sga.commonviews import addUserData

from settings import MEDIA_ROOT, CARRERAS_ID_EXCLUIDAS_INEC
from sga.commonviews import addUserData
from sga.models import Carrera, elimina_tildes, Matricula, TituloInstitucion, ReporteExcel,convertir_fecha
from sga.forms import EficienciaExcelForm
from socioecon.models import GrupoSocioEconomico, InscripcionFichaSocioeconomica


def view(request):
    try:
        if request.method == 'POST':
            action = request.POST['action']
            if action == 'generaexcel':
                inscripcion = ''
                hoy = datetime.now().today()
                try:
                    desde = request.POST['desde']
                    hasta = request.POST['hasta']
                    fechai = convertir_fecha(desde)
                    fechaf = convertir_fecha(hasta)
                    carrera=Carrera.objects.filter(pk=request.POST['carrera'])[:1].get()

                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo.font.height = 20 * 11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20 * 10
                    titulo2 = xlwt.easyxf(' font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20 * 11
                    titulo2.font.height = 20 * 11
                    style1 = xlwt.easyxf('', num_format_str='DD-MMM-YY')
                    wb = xlwt.Workbook()
                    hoja='alummos_socioeco'
                    ws = wb.add_sheet(hoja,cell_overwrite_ok=True)
                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,10, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,10, 'INFORMACION DE ESTUDIANTES - NIVEL SOCIOECONOMICO POR CARRERAS  ', titulo2)

                    ws.write(3, 0,'Carrera:   ' +elimina_tildes(carrera.nombre), titulo)
                    ws.write(4, 0,'Desde:   ' +str(fechai.date()), titulo)
                    ws.write(5, 0,'Hasta:   ' +str(fechaf.date()), titulo)

                    ws.write(7,0,"CEDULA",titulo)
                    ws.write_merge(7,7,1,3,"NOMBRES",titulo)
                    ws.write_merge(7,7,4,7,"APELLIDOS",titulo)
                    ws.write(7,8,"SEXO",titulo)
                    ws.write(7,9,"EDAD",titulo)
                    ws.write(7,10,"NIVEL SOCIOECONOMICO",titulo)
                    fila = 8

                    matri=Matricula.objects.filter(nivel__carrera=carrera,nivel__cerrado=False,inscripcion__persona__usuario__is_active=True,fecha__gte=fechai,fecha__lte=fechaf).distinct('inscripcion').values('inscripcion')
                    inscrip=InscripcionFichaSocioeconomica.objects.filter(inscripcion__id__in=matri).distinct().order_by('inscripcion')
                    totalestudiantesficha=inscrip.count()
                    for i in inscrip:
                        # print(i)
                        identificacion=''
                        nombres=''
                        apellidos=''
                        sexo=''
                        edad=''
                        nivel_socioecon=''
                        codigo_socioecon=''
                        try:
                            if i.inscripcion.persona.cedula:
                                identificacion=i.inscripcion.persona.cedula
                            else:
                                identificacion=i.inscripcion.persona.pasaporte
                        except:
                            identificacion=''

                        try:
                            if i.inscripcion.persona.nombres:
                                nombres= elimina_tildes(i.inscripcion.persona.nombres)
                            else:
                                nombres=''
                        except:
                            nombres=''

                        try:
                            if i.inscripcion.persona.apellido1:
                                ape1= elimina_tildes(i.inscripcion.persona.apellido1)
                            else:
                                ape1=''
                        except:
                            ape1=''
                        try:
                            if i.inscripcion.persona.apellido2:
                                ape2= elimina_tildes(i.inscripcion.persona.apellido2)
                            else:
                                ape2=''
                        except:
                            ape2=''

                        apellidos=ape1+' '+ape2

                        try:
                            if i.inscripcion.persona.sexo:
                                sexo= elimina_tildes(i.inscripcion.persona.sexo.nombre)
                            else:
                                sexo=''
                        except:
                            sexo=''

                        try:
                            mes=''
                            anio_act=''
                            mes_act=''
                            if i.inscripcion.persona.nacimiento:
                                f_nacido=i.inscripcion.persona.nacimiento
                            anio = f_nacido.year
                            mes = f_nacido.month
                            anio_act=hoy.year
                            mes_act=hoy.month

                            if f_nacido:
                               edad=(anio_act-anio)
                               if mes_act<mes:
                                   edad=edad-1
                        except:
                            edad=''

                        try:
                            nivel_socioecon=elimina_tildes(i.grupoeconomico.nombre)
                        except:
                            nivel_socioecon=''

                        ws.write(fila,0, identificacion)
                        ws.write_merge(fila,fila,1,3,nombres)
                        ws.write_merge(fila,fila,4,7,apellidos)
                        ws.write(fila,8, sexo)
                        ws.write(fila,9, edad)
                        ws.write(fila,10, nivel_socioecon)
                        fila=fila+1

                    fila =fila+ 1
                    ws.write_merge(fila,fila,0,1,"RESUMEN", titulo2)
                    for socioeco in GrupoSocioEconomico.objects.all():
                        fila =fila+ 1
                        matric=Matricula.objects.filter(nivel__carrera=carrera,nivel__cerrado=False,inscripcion__persona__usuario__is_active=True,fecha__gte=fechai,fecha__lte=fechaf).distinct('inscripcion').values('inscripcion')
                        insc1=InscripcionFichaSocioeconomica.objects.filter(grupoeconomico=socioeco, inscripcion__id__in=matric).distinct('inscripcion').count()
                        ws.write(fila,0,elimina_tildes(socioeco.nombre))
                        ws.write(fila,1,insc1)
                    fila =fila+ 1
                    ws.write(fila,0,"TOTAL",titulo2)
                    ws.write(fila,1,totalestudiantesficha,titulo2)

                    detalle = fila + 3
                    ws.write(detalle, 0, "Fecha Impresion", subtitulo)
                    ws.write(detalle, 1, str(datetime.now()), subtitulo)
                    detalle = detalle + 2
                    ws.write(detalle, 0, "Usuario", subtitulo)
                    ws.write(detalle, 1, str(request.user), subtitulo)

                    nombre = 'informacionsocioecon' + str(datetime.now()).replace(" ", "").replace(".", "").replace(":", "") + '.xls'
                    wb.save(MEDIA_ROOT + '/reporteexcel/' + nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    return HttpResponse(json.dumps({"result":str(ex)+str(inscripcion)}),content_type="application/json")

        else:
            data = {'title': 'Listado de informacion socioeconomica por carrera '}
            addUserData(request, data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['form']=EficienciaExcelForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
                return render(request ,"reportesexcel/informacion_socioeconomica.html" ,  data)

            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        print((e))
        return HttpResponseRedirect('/?info=' + str(e))