from datetime import datetime,timedelta,time
import json
import xlwt
import os
import locale
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from settings import MEDIA_ROOT,UTILIZA_FACTURACION_CON_FPDF,JR_USEROUTPUT_FOLDER,MEDIA_URL, SITE_ROOT
from sga.commonviews import addUserData
from sga.forms import RepVisitasBibliotecaPorCarreraForm
from sga.models import convertir_fecha,TituloInstitucion,ReporteExcel,Carrera,Sede,DetalleVisitasBiblioteca,Inscripcion,Persona
from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            inicio = request.POST['desde']
            fin = request.POST['hasta']

            if action  =='generarexcel':
                try:
                    fechai = convertir_fecha(inicio)
                    fechaf = convertir_fecha(fin)
                    campus = Sede.objects.filter(pk=request.POST['sede'])[:1].get()
                    carrera = Carrera.objects.filter(pk=request.POST['carrera'])[:1].get()
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('LISTADO',cell_overwrite_ok=True)

                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,8, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,8, 'LISTADO DE VISITAS A  LA BIBLIOTECA', titulo2)

                    fila =3
                    ws.write(fila,0, 'CAMPUS:', titulo)
                    ws.write(fila,1, elimina_tildes(campus.nombre), titulo)

                    ws.write(fila+1,0, 'CARRERA:', titulo)
                    ws.write(fila+1,1, str(carrera.alias), titulo)

                    ws.write(fila+2, 0, 'DESDE:', titulo)
                    ws.write(fila+2, 1, str((fechai.date())), titulo)
                    ws.write(fila+3, 0, 'HASTA:', titulo)
                    ws.write(fila+3, 1, str((fechaf.date())), titulo)

                    fila=8
                    ws.write(fila, 0,  'CEDULA', titulo)
                    ws.write(fila, 1,  'NOMBRE', titulo)
                    ws.write(fila, 2,  'SEXO', titulo)
                    ws.write(fila, 3,  'MOTIVO', titulo)
                    ws.write(fila, 4,  'DIA VISITA', titulo)
                    ws.write(fila, 5,  'OBS. REALIZADA', titulo)

                    detallevisita=None
                    totalvisitas=0
                    detallealumnos = DetalleVisitasBiblioteca.objects.filter(sede=campus, fecha__gte=fechai, fecha__lte=fechaf).distinct('visitabiblioteca__cedula').values_list('visitabiblioteca__cedula',flat=True)
                    inscripciones= Inscripcion.objects.filter(carrera=carrera,persona__cedula__in=detallealumnos).order_by('persona__apellido1','persona__apellido2').values_list('persona__cedula',flat=True)
                    if len(inscripciones)>0:
                        detallevisita = DetalleVisitasBiblioteca.objects.filter(sede=campus, fecha__gte=fechai, fecha__lte=fechaf,visitabiblioteca__cedula__in=inscripciones).order_by('visitabiblioteca__nombre')
                        # print(detallevisita.query.__str__())
                        totalvisitas=detallevisita.count()
                        for dv in detallevisita:
                            sexo=''
                            fila=fila+1
                            ws.write(fila, 0, dv.visitabiblioteca.cedula)
                            try:
                                if dv.visitabiblioteca.cedula:
                                    per=Persona.objects.filter(cedula=dv.visitabiblioteca.cedula)[:1].get()
                                    sexo=per.sexo.nombre
                                else:
                                    sexo=''
                            except Exception as ex:
                                pass
                            ws.write(fila, 1, elimina_tildes(dv.visitabiblioteca.nombre))
                            ws.write(fila, 2, sexo)
                            ws.write(fila, 3, elimina_tildes(dv.visitabiblioteca.motivovisita.descripcion))
                            ws.write(fila, 4, str(dv.fecha))
                            ws.write(fila, 5, elimina_tildes(dv.observacion))

                    fila= fila+3

                    ws.write(fila,0, "Total de Visitas", subtitulo)
                    ws.write(fila,1, totalvisitas, subtitulo)
                    detalle = fila + 3
                    ws.write(detalle,0, "Fecha Impresion", subtitulo)
                    ws.write(detalle,1, str(datetime.now()), subtitulo)
                    detalle=detalle+1
                    ws.write(detalle,0, "Usuario", subtitulo)
                    ws.write(detalle,1, str(request.user), subtitulo)

                    nombre ='xls_visitasbibliotecacarrera'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")
        else:
            data = {'title': 'Visitas a Biblioteca por Carrera'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['formbiblio'] = RepVisitasBibliotecaPorCarreraForm(initial={'desde':datetime.now().date(),'hasta':datetime.now().date()})
                return render(request ,"reportesexcel/xls_visitabibliotecaxcarrera.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))
