from datetime import datetime
from decimal import Decimal
import decimal
import json
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
import xlwt
from settings import MEDIA_ROOT, SEXO_FEMENINO, SEXO_MASCULINO
from sga.commonviews import addUserData
from sga.models import ReporteExcel, Inscripcion, TituloInstitucion, Parroquia, Canton, Provincia, Sector

__author__ = 'jjurgiles'

def view(request):
    try:
        if request.method == 'POST':
            action = request.POST['action']
            if action :
                try:
                    provincia = None
                    canton = None
                    parroquia = None
                    if int(request.POST['idparr']) > 0:
                        parroquia = Parroquia.objects.get(id=request.POST['idparr'])
                        inscripciones = Inscripcion.objects.filter(persona__sectorresid__parroquia__id=request.POST['idparr'],fecha__gte=request.POST['desde'],fecha__lte=request.POST['hasta'])
                        titulomens = "INSCRITOS POR SECTOR DE LA PARROQUIA "+ parroquia.nombre
                        nombrexce = 'inscritosector'
                    elif int(request.POST['idcant']) > 0:
                        canton = Canton.objects.get(id=request.POST['idcant'])
                        inscripciones = Inscripcion.objects.filter(persona__sectorresid__parroquia__canton__id=request.POST['idcant'],fecha__gte=request.POST['desde'],fecha__lte=request.POST['hasta'])
                        titulomens = "INSCRITOS POR PARROQUIA DEL CANTON "+canton.nombre
                        nombrexce = 'inscritoparroquia'
                    elif int(request.POST['idprov']) > 0:
                        provincia = Provincia.objects.get(id=request.POST['idprov'])
                        inscripciones = Inscripcion.objects.filter(persona__sectorresid__parroquia__canton__provincia__id=request.POST['idprov'],fecha__gte=request.POST['desde'],fecha__lte=request.POST['hasta'])
                        titulomens = "INSCRITOS POR CANTON DE LA PROVINCIA "+provincia.nombre
                        nombrexce = 'inscritocanton'
                    else:
                        inscripciones = Inscripcion.objects.filter(fecha__gte=request.POST['desde'],fecha__lte=request.POST['hasta']).exclude(persona__sectorresid=None)
                        titulomens = "INSCRITOS POR PROVINCIA "
                        nombrexce = 'inscritoprovincia'
                    m = 10
                    total=inscripciones.count()
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo3 = xlwt.easyxf('font: name Times New Roman; align: wrap on, vert centre, horiz center')
                    subtitulo.font.height = 20*10
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('Registros',cell_overwrite_ok=True)

                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,m, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,m, titulomens,titulo2)
                    ws.write(2,0, 'TOTAL INSCRITOS',subtitulo)
                    ws.write(2,1, str(total),subtitulo3)
                    ws.write(2,3, 'FECHA DESDE',subtitulo)
                    ws.write(2,4, str(request.POST['desde']),subtitulo3)
                    ws.write(2,5, 'FECHA HASTA',subtitulo)
                    ws.write(2,6, str(request.POST['hasta']),subtitulo3)
                    if parroquia:
                        ws.write(3, 0,'SECTOR' , subtitulo3)
                        ws.write(3, 1,'MUJERES', subtitulo)
                        ws.write(3, 2,'PORCENTAJE', subtitulo)
                        ws.write(3, 3,'HOMBRES', subtitulo)
                        ws.write(3, 4,'PORCENTAJE', subtitulo)
                        ws.write(3, 5,'INSCRITOS', subtitulo)
                        ws.write(3, 6,'PORCEN. TOTAL', subtitulo)

                        fila = 4
                        for sec in Sector.objects.filter(parroquia=parroquia).order_by('nombre'):
                            inscrip = Inscripcion.objects.filter(persona__sectorresid=sec,fecha__gte=request.POST['desde'],fecha__lte=request.POST['hasta'])
                            if inscrip:
                                porcentaje = Decimal((Decimal(inscrip.count())*100) / total).quantize(Decimal(10)**-1)
                            else:
                                porcentaje = 0
                            numfemen = 0
                            porfemen = 0
                            nummasc = 0
                            pornummasc = 0
                            if inscrip.filter(persona__sexo__id=SEXO_FEMENINO):
                                numfemen = inscrip.filter(persona__sexo__id=SEXO_FEMENINO).count()
                                porfemen = Decimal((Decimal(numfemen)*100) / total).quantize(Decimal(10)**-1)
                            if inscrip.filter(persona__sexo__id=SEXO_MASCULINO):
                                nummasc = inscrip.filter(persona__sexo__id=SEXO_MASCULINO).count()
                                pornummasc = Decimal((Decimal(nummasc)*100) / total).quantize(Decimal(10)**-1)
                            ws.write(fila,0,sec.nombre,subtitulo)
                            ws.write(fila,1,numfemen, subtitulo3)
                            ws.write(fila,2,porfemen, subtitulo3)
                            ws.write(fila,3,nummasc, subtitulo3)
                            ws.write(fila,4,pornummasc, subtitulo3)
                            ws.write(fila,5,inscrip.count(), subtitulo)
                            ws.write(fila,6,porcentaje, subtitulo)
                            fila=fila+1
                    elif canton:
                        ws.write(3, 0,'SECTOR' , subtitulo3)
                        ws.write(3, 1,'MUJERES', subtitulo)
                        ws.write(3, 2,'PORCENTAJE', subtitulo)
                        ws.write(3, 3,'HOMBRES', subtitulo)
                        ws.write(3, 4,'PORCENTAJE', subtitulo)
                        ws.write(3, 5,'INSCRITOS', subtitulo)
                        ws.write(3, 6,'PORCEN. TOTAL', subtitulo)
                        fila = 4
                        for par in Parroquia.objects.filter(canton=canton).order_by('nombre'):
                            inscrip = Inscripcion.objects.filter(persona__sectorresid__parroquia=par,fecha__gte=request.POST['desde'],fecha__lte=request.POST['hasta'])
                            if inscrip:
                                porcentaje = Decimal((Decimal(inscrip.count())*100) / total).quantize(Decimal(10)**-1)
                            else:
                                porcentaje = 0
                            numfemen = 0
                            porfemen = 0
                            nummasc = 0
                            pornummasc = 0
                            if inscrip.filter(persona__sexo__id=SEXO_FEMENINO):
                                numfemen = inscrip.filter(persona__sexo__id=SEXO_FEMENINO).count()
                                porfemen = Decimal((Decimal(numfemen)*100) / total).quantize(Decimal(10)**-1)
                            if inscrip.filter(persona__sexo__id=SEXO_MASCULINO):
                                nummasc = inscrip.filter(persona__sexo__id=SEXO_MASCULINO).count()
                                pornummasc = Decimal((Decimal(nummasc)*100) / total).quantize(Decimal(10)**-1)
                            ws.write(fila,0,par.nombre,subtitulo)
                            ws.write(fila,1,numfemen, subtitulo3)
                            ws.write(fila,2,porfemen, subtitulo3)
                            ws.write(fila,3,nummasc, subtitulo3)
                            ws.write(fila,4,pornummasc, subtitulo3)
                            ws.write(fila,5,inscrip.count(), subtitulo)
                            ws.write(fila,6,porcentaje, subtitulo)
                            fila=fila+1
                    elif provincia:
                        ws.write(3, 0,'SECTOR' , subtitulo3)
                        ws.write(3, 1,'MUJERES', subtitulo)
                        ws.write(3, 2,'PORCENTAJE', subtitulo)
                        ws.write(3, 3,'HOMBRES', subtitulo)
                        ws.write(3, 4,'PORCENTAJE', subtitulo)
                        ws.write(3, 5,'INSCRITOS', subtitulo)
                        ws.write(3, 6,'PORCEN. TOTAL', subtitulo)
                        fila = 4
                        for can in Canton.objects.filter(provincia=provincia).order_by('nombre'):
                            inscrip = Inscripcion.objects.filter(persona__sectorresid__parroquia__canton=can,fecha__gte=request.POST['desde'],fecha__lte=request.POST['hasta'])
                            if inscrip:
                                porcentaje = Decimal((Decimal(inscrip.count())*100) / total).quantize(Decimal(10)**-1)
                            else:
                                porcentaje = 0
                            numfemen = 0
                            porfemen = 0
                            nummasc = 0
                            pornummasc = 0
                            if inscrip.filter(persona__sexo__id=SEXO_FEMENINO):
                                numfemen = inscrip.filter(persona__sexo__id=SEXO_FEMENINO).count()
                                porfemen = Decimal((Decimal(numfemen)*100) / total).quantize(Decimal(10)**-1)
                            if inscrip.filter(persona__sexo__id=SEXO_MASCULINO):
                                nummasc = inscrip.filter(persona__sexo__id=SEXO_MASCULINO).count()
                                pornummasc = Decimal((Decimal(nummasc)*100) / total).quantize(Decimal(10)**-1)
                            ws.write(fila,0,can.nombre,subtitulo)
                            ws.write(fila,1,numfemen, subtitulo3)
                            ws.write(fila,2,porfemen, subtitulo3)
                            ws.write(fila,3,nummasc, subtitulo3)
                            ws.write(fila,4,pornummasc, subtitulo3)
                            ws.write(fila,5,inscrip.count(), subtitulo)
                            ws.write(fila,6,porcentaje, subtitulo)
                            fila=fila+1
                    else:
                        ws.write(3, 0,'SECTOR' , subtitulo3)
                        ws.write(3, 1,'MUJERES', subtitulo)
                        ws.write(3, 2,'PORCENTAJE', subtitulo)
                        ws.write(3, 3,'HOMBRES', subtitulo)
                        ws.write(3, 4,'PORCENTAJE', subtitulo)
                        ws.write(3, 5,'INSCRITOS', subtitulo)
                        ws.write(3, 6,'PORCEN. TOTAL', subtitulo)
                        fila = 4
                        for prov in Provincia.objects.filter().order_by('nombre'):
                            inscrip = Inscripcion.objects.filter(persona__sectorresid__parroquia__canton__provincia=prov,fecha__gte=request.POST['desde'],fecha__lte=request.POST['hasta'])
                            if inscrip:
                                porcentaje = Decimal((Decimal(inscrip.count())*100) / total).quantize(Decimal(10)**-1)
                            else:
                                porcentaje = 0
                            numfemen = 0
                            porfemen = 0
                            nummasc = 0
                            pornummasc = 0
                            if inscrip.filter(persona__sexo__id=SEXO_FEMENINO):
                                numfemen = inscrip.filter(persona__sexo__id=SEXO_FEMENINO).count()
                                porfemen = Decimal((Decimal(numfemen)*100) / total).quantize(Decimal(10)**-1)
                            if inscrip.filter(persona__sexo__id=SEXO_MASCULINO):
                                nummasc = inscrip.filter(persona__sexo__id=SEXO_MASCULINO).count()
                                pornummasc = Decimal((Decimal(nummasc)*100) / total).quantize(Decimal(10)**-1)
                            ws.write(fila,0,prov.nombre,subtitulo)
                            ws.write(fila,1,numfemen, subtitulo3)
                            ws.write(fila,2,porfemen, subtitulo3)
                            ws.write(fila,3,nummasc, subtitulo3)
                            ws.write(fila,4,pornummasc, subtitulo3)
                            ws.write(fila,5,inscrip.count(), subtitulo)
                            ws.write(fila,6,porcentaje, subtitulo)
                            fila=fila+1
                    detalle = fila + 2
                    ws.write(detalle,0, "Fecha Impresion", subtitulo)
                    ws.write(detalle,1, str(datetime.now()), subtitulo)
                    detalle=detalle+2
                    ws.write(detalle,0, "Usuario", subtitulo)
                    ws.write(detalle,1, str(request.user), subtitulo)

                    nombre =nombrexce+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")

        else:
            data = {'title': 'Inscrito Por Sector '}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['fechahoy'] = datetime.now()
                return render(request ,"reportesexcel/excelprovcanparsec.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")
    except Exception as e:
        print('Error Excepcion excelprovcant '+str(e))
        return HttpResponseRedirect('/?info=Error comuniquese con el Administrador')