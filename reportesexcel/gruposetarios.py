from datetime import date, datetime
import json
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
import xlwt
from settings import MEDIA_ROOT
from sga.commonviews import addUserData
from sga.models import TituloInstitucion, convertir_fecha, Matricula, Inscripcion, ReporteExcel, Carrera, elimina_tildes


def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action== 'generaexcelgrupos' :
                inscripcion= ''
                try:
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10
                    titulo2 = xlwt.easyxf(' font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    style1 = xlwt.easyxf('',num_format_str='DD-MMM-YY')
                    wb = xlwt.Workbook()


                    # ezxf = easyxf
                    center = xlwt.easyxf('align: horiz center')

                    # writer = XLSWriter()

                    # data = ["Negrilla", "Centrada", u"Centrada y con corte de linea"]
                    # format = [ezxf('font: bold on'), ezxf('align: horiz center'), ezxf('align: wrap on, horiz center')]
                    # writer.append(data, format)
                    hoja='gruposetarios'
                    ws = wb.add_sheet(hoja,cell_overwrite_ok=True)
                    ws.write_merge(0, 0, 0, 10,)
                    ws.write_merge(1, 1, 0, 10,)
                    ws.write (0, 0, 'INSTITUTO TECNOLOGICO BOLIVARIANO',titulo2, )
                    ws.write(1, 0, 'LISTADO DE ESTUDIANTES POR GRUPOS ETARIOS ' ,titulo2)
                    ws.write(2, 0, 'CARRERA ', titulo)
                    ws.write(2, 1, 'MENOS DE 18 ', titulo2,)
                    ws.write(2, 2, 'DE 18 A 20 ', titulo2)
                    ws.write(2, 3, 'DE 21 A 25', titulo2)
                    ws.write(2, 4, 'DE 26 A 30', titulo2)
                    ws.write(2, 5, 'DE 31 A 35', titulo2)
                    ws.write(2, 6, 'DE 36 A 40', titulo2)
                    ws.write(2, 7, 'DE 41 A 45', titulo2)
                    ws.write(2, 8, 'DE 46 A 50', titulo2)
                    ws.write(2, 9, 'MAS DE 50', titulo2)

                    grupocar=3
                    totalgrupo1=0
                    totalgrupo2=0
                    totalgrupo3=0
                    totalgrupo4=0
                    totalgrupo5=0
                    totalgrupo6=0
                    totalgrupo7=0
                    totalgrupo8=0
                    totalgrupo9=0
                    for carrera in Carrera.objects.filter(activo=True).order_by('coordinacion'):
                        ws.write(grupocar,0,elimina_tildes(carrera.nombre))

                        anno=datetime.now().date().year-18
                        fecha = date(anno,datetime.now().date().month,datetime.now().date().day)
                        print(fecha)
                        inscripcionid=Matricula.objects.filter(inscripcion__persona__usuario__is_active=True,inscripcion__persona__nacimiento__gt=fecha,nivel__carrera=carrera,nivel__cerrado=False).distinct('inscripcion').values('inscripcion')
                        grupo1=Matricula.objects.filter(nivel__carrera=carrera,nivel__cerrado=False,inscripcion__id__in=inscripcionid).count()
                        totalgrupo1=totalgrupo1 + grupo1
                        ws.write(grupocar,1,grupo1)
                        anno2=datetime.now().date().year-20
                        fecha2 = date(anno2,datetime.now().date().month,datetime.now().date().day)
                        inscripcionid2=Matricula.objects.filter(inscripcion__persona__usuario__is_active=True,inscripcion__persona__nacimiento__lte=fecha,inscripcion__persona__nacimiento__gte=fecha2,nivel__carrera=carrera,nivel__cerrado=False).distinct('inscripcion').values('inscripcion')
                        grupo2=Matricula.objects.filter(nivel__carrera=carrera,nivel__cerrado=False,inscripcion__id__in=inscripcionid2).count()
                        totalgrupo2=totalgrupo2 + grupo2
                        ws.write(grupocar,2,grupo2)
                        anno3=datetime.now().date().year-21
                        fecha3 = date(anno3,datetime.now().date().month,datetime.now().date().day)
                        anno33=datetime.now().date().year-25
                        fecha33 = date(anno33,datetime.now().date().month,datetime.now().date().day)
                        inscripcionid3=Matricula.objects.filter(inscripcion__persona__usuario__is_active=True,inscripcion__persona__nacimiento__lte=fecha3,inscripcion__persona__nacimiento__gte=fecha33,nivel__carrera=carrera,nivel__cerrado=False).distinct('inscripcion').values('inscripcion')
                        grupo3=Matricula.objects.filter(nivel__carrera=carrera,nivel__cerrado=False,inscripcion__id__in=inscripcionid3).count()
                        totalgrupo3=totalgrupo3 + grupo3
                        ws.write(grupocar,3,grupo3)
                        anno4=datetime.now().date().year-26
                        fecha4 = date(anno4,datetime.now().date().month,datetime.now().date().day)
                        anno44=datetime.now().date().year-30
                        fecha44 = date(anno44,datetime.now().date().month,datetime.now().date().day)
                        inscripcionid4=Matricula.objects.filter(inscripcion__persona__usuario__is_active=True,inscripcion__persona__nacimiento__lte=fecha4,inscripcion__persona__nacimiento__gte=fecha44,nivel__carrera=carrera,nivel__cerrado=False).distinct('inscripcion').values('inscripcion')
                        grupo4=Matricula.objects.filter(nivel__carrera=carrera,nivel__cerrado=False,inscripcion__id__in=inscripcionid4).count()
                        totalgrupo4=totalgrupo4 + grupo4
                        ws.write(grupocar,4,grupo4)
                        anno5=datetime.now().date().year-31
                        fecha5 = date(anno5,datetime.now().date().month,datetime.now().date().day)
                        anno55=datetime.now().date().year-35
                        fecha55 = date(anno55,datetime.now().date().month,datetime.now().date().day)
                        inscripcionid5=Matricula.objects.filter(inscripcion__persona__usuario__is_active=True,inscripcion__persona__nacimiento__lte=fecha5,inscripcion__persona__nacimiento__gte=fecha55,nivel__carrera=carrera,nivel__cerrado=False).distinct('inscripcion').values('inscripcion')
                        grupo5=Matricula.objects.filter(nivel__carrera=carrera,nivel__cerrado=False,inscripcion__id__in=inscripcionid5).count()
                        totalgrupo5=grupo5+totalgrupo5
                        ws.write(grupocar,5,grupo5)
                        anno6=datetime.now().date().year-36
                        fecha6 = date(anno6,datetime.now().date().month,datetime.now().date().day)
                        anno66=datetime.now().date().year-40
                        fecha66 = date(anno66,datetime.now().date().month,datetime.now().date().day)
                        inscripcionid6=Matricula.objects.filter(inscripcion__persona__usuario__is_active=True,inscripcion__persona__nacimiento__lte=fecha6,inscripcion__persona__nacimiento__gte=fecha66,nivel__carrera=carrera,nivel__cerrado=False).distinct('inscripcion').values('inscripcion')
                        grupo6=Matricula.objects.filter(nivel__carrera=carrera,nivel__cerrado=False,inscripcion__id__in=inscripcionid6).count()
                        totalgrupo6=totalgrupo6 + grupo6
                        ws.write(grupocar,6,grupo6)
                        anno7=datetime.now().date().year-41
                        fecha7 = date(anno7,datetime.now().date().month,datetime.now().date().day)
                        anno77=datetime.now().date().year-45
                        fecha77=date(anno77,datetime.now().date().month,datetime.now().date().day)
                        inscripcionid7=Matricula.objects.filter(inscripcion__persona__usuario__is_active=True,inscripcion__persona__nacimiento__lte=fecha7,inscripcion__persona__nacimiento__gte=fecha77,nivel__carrera=carrera,nivel__cerrado=False).distinct('inscripcion').values('inscripcion')
                        grupo7=Matricula.objects.filter(nivel__carrera=carrera,nivel__cerrado=False,inscripcion__id__in=inscripcionid7).count()
                        totalgrupo7=totalgrupo7 + grupo7
                        ws.write(grupocar,7,grupo7)
                        anno8=datetime.now().date().year-46
                        fecha8 = date(anno8,datetime.now().date().month,datetime.now().date().day)
                        anno88=datetime.now().date().year-50
                        fecha88 = date(anno88,datetime.now().date().month,datetime.now().date().day)
                        inscripcionid8=Matricula.objects.filter(inscripcion__persona__usuario__is_active=True,inscripcion__persona__nacimiento__lte=fecha8,inscripcion__persona__nacimiento__gte=fecha88,nivel__carrera=carrera,nivel__cerrado=False).distinct('inscripcion').values('inscripcion')
                        grupo8=Matricula.objects.filter(nivel__carrera=carrera,nivel__cerrado=False,inscripcion__id__in=inscripcionid8).count()
                        totalgrupo8=totalgrupo8 + grupo8
                        ws.write(grupocar,8,grupo8)
                        inscripcionid9=Matricula.objects.filter(inscripcion__persona__usuario__is_active=True,inscripcion__persona__nacimiento__lt=fecha88,nivel__carrera=carrera,nivel__cerrado=False).distinct('inscripcion').values('inscripcion')
                        grupo9=Matricula.objects.filter(nivel__carrera=carrera,nivel__cerrado=False,inscripcion__id__in=inscripcionid9).count()
                        totalgrupo9=totalgrupo9 + grupo9
                        ws.write(grupocar,9,grupo9)

                        grupocar=grupocar+1
                    ws.write(grupocar,0,"TOTAL", titulo2)

                    ws.write(grupocar,1,totalgrupo1)
                    ws.write(grupocar,2,totalgrupo2)
                    ws.write(grupocar,3,totalgrupo3)
                    ws.write(grupocar,4,totalgrupo4)
                    ws.write(grupocar,5,totalgrupo5)
                    ws.write(grupocar,6,totalgrupo6)
                    ws.write(grupocar,7,totalgrupo7)
                    ws.write(grupocar,8,totalgrupo8)
                    ws.write(grupocar,9,totalgrupo9)

                    detalle = grupocar + 3
                    ws.write(detalle,0, "Fecha Impresion", subtitulo)
                    ws.write(detalle,1, str(datetime.now()), subtitulo)
                    detalle=detalle+2
                    ws.write(detalle,0, "Usuario", subtitulo)
                    ws.write(detalle,1, str(request.user), subtitulo)



                    nombre ='gruposetarios'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    return HttpResponse(json.dumps({"result":str(ex)+str(inscripcion)}),content_type="application/json")

        else:
                data = {'title': 'Grupos etarios por carreras '}
                addUserData(request,data)
                if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                    reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                    data['reportes'] = reportes
                # data['generarform']=XLSPeriodoForm()
                    return render(request ,"reportesexcel/grupos_etarios.html" ,  data)
                return HttpResponseRedirect("/reporteexcel")


    except Exception as e:
        print((e))
        return HttpResponseRedirect('/?info='+str(e))