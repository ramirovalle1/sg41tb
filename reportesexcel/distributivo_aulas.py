from datetime import datetime,timedelta
import json
import xlwt
import os
import locale
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from settings import MEDIA_ROOT,UTILIZA_FACTURACION_CON_FPDF,JR_USEROUTPUT_FOLDER,MEDIA_URL, SITE_ROOT
from sga.commonviews import addUserData
from sga.forms import RangoFacturasForm, DistributivoForm, Distributivo_AulasForm
from sga.models import convertir_fecha,Materia,TituloInstitucion,ReporteExcel, Profesor, Materia,  Periodo, ProfesorMateria,Clase,Carrera, Aula, Sede
from sga.reportes import elimina_tildes
from fpdf import FPDF


@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    semanas=0
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action  =='generar':
                try:
                    inicio = convertir_fecha(request.POST['inicio'])
                    fin = convertir_fecha(request.POST['fin'])
                    sede=Sede.objects.filter(pk=request.POST['sede'])[:1].get()
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10
                    style1 = xlwt.easyxf('',num_format_str='DD-MMM-YY')
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('distribucion',cell_overwrite_ok=True)

                    ws.write_merge(1, 1,0,8, 'OCUPACION DE AULAS POR SEDES', titulo2)
                    ws.write(2, 0, 'SEDE', titulo)
                    ws.write(2, 1, elimina_tildes(sede.nombre), titulo)
                    ws.write(4, 0, 'FECHA INICIO', titulo)
                    ws.write(4, 1, str(inicio.date()), titulo)
                    ws.write(5, 0, 'FECHA FIN', titulo)
                    ws.write(5, 1, str(fin.date()), titulo)

                    cont =7
                    c=1
                    cont = cont+2
                    ws.write_merge(7, 7,4,9, 'JORNADA MATUTINA', titulo2)
                    ws.write_merge(9,9,2,3, 'DESDE-HASTA', titulo2)
                    ws.write(cont, 4, 'LUNES', titulo)
                    ws.write(cont, 5, 'MARTES', titulo)
                    ws.write(cont, 6, 'MIERCOLES', titulo)
                    ws.write(cont, 7, 'JUEVES', titulo)
                    ws.write(cont, 8, 'VIERNES', titulo)
                    ws.write(cont, 9, 'TOTAL L-V', titulo)

                    ws.write_merge(7, 7,11,16, 'JORNADA VESPERTINA', titulo2)
                    ws.write(cont, 11, 'LUNES', titulo)
                    ws.write(cont, 12, 'MARTES', titulo)
                    ws.write(cont, 13, 'MIERCOLES', titulo)
                    ws.write(cont, 14, 'JUEVES', titulo)
                    ws.write(cont, 15, 'VIERNES', titulo)
                    ws.write(cont, 16, 'TOTAL L-V', titulo)

                    ws.write_merge(7, 7,18,23, 'JORNADA NOCTURNA', titulo2)
                    ws.write(cont, 18, 'LUNES', titulo)
                    ws.write(cont, 19, 'MARTES', titulo)
                    ws.write(cont, 20, 'MIERCOLES', titulo)
                    ws.write(cont, 21, 'JUEVES', titulo)
                    ws.write(cont, 22, 'VIERNES', titulo)
                    ws.write(cont, 23, 'TOTAL L-V', titulo)

                    ws.write_merge(7, 7,25,27, 'FIN DE SEMANA', titulo2)
                    ws.write(cont, 25, 'SABADO', titulo)
                    ws.write(cont, 26, 'DOMINGO', titulo)
                    ws.write(cont, 27, 'TOTAL S-D', titulo)

                    lun = 4
                    mar = 5
                    mier = 6
                    jue = 7
                    vie = 8

                    lunvesp = 11
                    marvesp = 12
                    miervesp = 13
                    juevesp = 14
                    vievesp = 15

                    lunnoc = 18
                    marnoc = 19
                    miernoc = 20
                    juevnoc = 21
                    viernoc = 22

                    sab = 25
                    dom = 26

                    fila=10
                    cont = cont + 1
                    ocupa = cont
                    desde=inicio
                    hasta=fin

                    aulas = sede.aulas()   #Obtener todas las aulas de una sede
                    for aula in aulas.exclude(tipo__id=9):
                        nombreaula=''
                        lunesmat=0
                        martesmat=0
                        miercolesmat=0
                        juevesmat=0
                        viernesmat=0

                        lunesves=0
                        martesves=0
                        miercolesves=0
                        juevesves=0
                        viernesves=0

                        lunesnoc=0
                        martesnoc=0
                        miercolesnoc=0
                        juevesnoc=0
                        viernesnoc=0

                        sabado=0
                        domingo=0
                        matutino=0
                        vespertino=0
                        nocturno=0

                        findesemana=0
                        banmatutina=0
                        banvespertina=0
                        bannocturna=0
                        bansabado=0
                        bandomingo=0

                        try :
                            nombreaula=aula.nombre
                            ws.write(fila,0,str(nombreaula), titulo)
                            ws.write(fila,2,str(inicio.date()))
                            for dia in daterange(desde, hasta):
                                numdia = dia.weekday() + 1
                                ocupada = aula.ocupada_fecha(dia,numdia)
                                clases = aula.clases_fecha(dia,numdia)

                                if ocupada:
                                    for clase in clases:
                                         if clase.jornadaclases()=='MATUTINA':
                                             banmatutina  = 1
                                         if clase.jornadaclases()=='VESPERTINA':
                                             banvespertina  = 2
                                         if clase.jornadaclases()=='NOCTURNA':
                                             bannocturna  = 3
                                         if clase.jornadaclases()=='FIN DE SEMANA' and numdia==6:
                                             bansabado = 4
                                         if clase.jornadaclases()=='FIN DE SEMANA' and numdia==7:
                                             bandomingo = 5

                                if numdia==1:
                                    ws.write(ocupa,2,str(dia.date()))
                                    if banmatutina:
                                        lunesmat=0.20
                                        ws.write(ocupa,lun,0.20)

                                    if banvespertina:
                                        lunesves=0.20
                                        ws.write(ocupa,lunvesp,0.20)

                                    if bannocturna:
                                        lunesnoc=0.20
                                        ws.write(ocupa,lunnoc,0.20)

                                if numdia==2:
                                    if banmatutina:
                                        martesmat=0.20
                                        ws.write(ocupa,mar,0.20)

                                    if banvespertina:
                                        martesves=0.20
                                        ws.write(ocupa,marvesp,0.20)

                                    if bannocturna:
                                        martesnoc=0.20
                                        ws.write(ocupa,marnoc,0.20)

                                if numdia==3:
                                    if banmatutina:
                                        miercolesmat=0.20
                                        ws.write(ocupa,mier,0.20)

                                    if banvespertina:
                                        miercolesves=0.20
                                        ws.write(ocupa,miervesp,0.20)

                                    if bannocturna:
                                        miercolesnoc=0.20
                                        ws.write(ocupa,miernoc,0.20)

                                if numdia==4:
                                    if banmatutina:
                                        juevesmat=0.20
                                        ws.write(ocupa,jue,0.20)

                                    if banvespertina:
                                        juevesves=0.20
                                        ws.write(ocupa,juevesp,0.20)

                                    if bannocturna:
                                        juevesnoc=0.20
                                        ws.write(ocupa,juevnoc,0.20)

                                if numdia==5:
                                    if banmatutina:
                                        viernesmat=0.20
                                        ws.write(ocupa,vie,0.20)
                                        matutino=lunesmat+martesmat+miercolesmat+juevesmat+viernesmat
                                        ws.write(ocupa,vie+1,matutino)

                                    if banvespertina:
                                        viernesves=0.20
                                        ws.write(ocupa,vievesp,0.20)
                                        vespertino=lunesves+martesves+miercolesves+juevesves+viernesves
                                        ws.write(ocupa,vievesp + 1,vespertino)

                                    if bannocturna:
                                        viernesnoc=0.20
                                        ws.write(ocupa,viernoc,0.20)
                                        nocturno=lunesnoc+martesnoc+miercolesnoc+juevesnoc+viernesnoc
                                        ws.write(ocupa,viernoc + 1,nocturno)

                                if numdia==6 or numdia==7:
                                    if bansabado == 4:
                                        sabado=0.50
                                        ws.write(ocupa,sab,0.50)
                                    if bandomingo == 5:
                                        domingo=0.50
                                        ws.write(ocupa,dom,0.50)

                                    findesemana=sabado+domingo
                                    if findesemana>0:
                                        ws.write(ocupa,sab+2,findesemana)

                                if numdia==7:
                                    ws.write(ocupa,3,str(dia.date()))
                                    ocupa =  ocupa +1
                            fila=ocupa+1
                            matutino=0
                            vespertino=0
                            nocturno=0
                            findesemana=0

                        except Exception as ex:
                            pass



                    nombre ='distributivo_aulas'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")

        else:
            data = {'title': 'Disponibilidad de Aulas por Sede'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
            data['generarform']=Distributivo_AulasForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
            return render(request ,"reportesexcel/distributivo_aulas.html" ,  data)
        return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))


def daterange(desde, hasta):
    hasta = hasta + timedelta(days=1)
    for n in range(int ((hasta - desde).days)):
        yield desde + timedelta(n)

def jornadaestudios():
    jornadasemanal = ['MATUTINA','VESPERTINA','NOCTURNA','SABADO','DOMINGO']
    return jornadasemanal

















