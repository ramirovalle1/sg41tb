from datetime import datetime,timedelta,time
import json
from django.db.models import Q
import xlwt
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from bib.models import ConsultaBiblioteca, ReferenciaWeb, OtraBibliotecaVirtual
from settings import MEDIA_ROOT
from sga.commonviews import addUserData
from sga.forms import ConsultasBibliotecasVirtualesForm
from sga.models import convertir_fecha,TituloInstitucion,ReporteExcel,Carrera,Inscripcion,Persona, Profesor
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
                    fechainicio = convertir_fecha(inicio)
                    fechafin = convertir_fecha(fin)
                    carrera=[]
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
                    estudiante = request.POST['estudiante']
                    docente = request.POST['docente']
                    if estudiante=='True':
                        carrera = Carrera.objects.filter(pk=request.POST['carrera'])[:1].get()
                        ws.write(fila,0, 'PERFIL:', titulo)
                        ws.write(fila,1, 'ESTUDIANTE',titulo)
                    elif docente=='True':
                        ws.write(fila,0, 'PERFIL:', titulo)
                        ws.write(fila,1, 'DOCENTE',titulo)

                    ws.write(fila+1, 0, 'DESDE:', titulo)
                    ws.write(fila+1, 1, str((fechainicio.date())), titulo)
                    ws.write(fila+2, 0, 'HASTA:', titulo)
                    ws.write(fila+2, 1, str((fechafin.date())), titulo)

                    fila=7
                    ws.write(fila, 0,  'NOMBRE COMPLETO', titulo)
                    ws.col(0).width = 10 * 800
                    ws.write(fila, 1,  'FECHA DE ACCESO', titulo)
                    ws.col(1).width = 10 * 400
                    ws.write(fila, 2,  'HORA', titulo)
                    ws.write(fila, 3,  'BIBLIOTECA', titulo)
                    ws.col(3).width = 10 * 500
                    ws.write(fila, 4,  'URL', titulo)

                    totalvisitas=0

                    referencias = ReferenciaWeb.objects.filter()
                    otrasbibliotecas = OtraBibliotecaVirtual.objects.filter()
                    acceso=[]
                    if estudiante=='True':
                        inscripciones = Inscripcion.objects.filter(carrera=carrera).values_list('persona')

                        if len(inscripciones)>0:
                            acceso = ConsultaBiblioteca.objects.filter(Q(referenciasconsultadas__id__in = referencias)| Q( otrabibliotecaconsultadas__id__in=otrasbibliotecas), fecha__gte=fechainicio, fecha__lte=fechafin, persona__in= inscripciones).order_by('-fecha','-hora')

                            totalvisitas = acceso.count()

                    if docente=='True':
                        docentes = Profesor.objects.filter().values_list('persona')
                        if len(docentes)>0:
                            acceso= ConsultaBiblioteca.objects.filter(Q(referenciasconsultadas__id__in = referencias)| Q( otrabibliotecaconsultadas__id__in=otrasbibliotecas), fecha__gte=fechainicio, fecha__lte=fechafin, persona__in= docentes).order_by('-fecha','-hora')
                            totalvisitas = acceso.count()
                    for a in acceso:
                        fila=fila+1
                        ws.write(fila, 0, a.persona.nombre_completo_inverso())
                        ws.write(fila, 1, str(a.fecha))
                        ws.write(fila, 2, a.hora.strftime("%H:%M"))
                        if a.fun_referencias():
                            for bib in a.fun_referencias():
                                ws.write(fila, 3, bib.nombre)
                                ws.write(fila, 4, bib.url)
                        if a.fun_otrasbiblio():
                            for bib in a.fun_otrasbiblio():
                                ws.write(fila, 3, bib.nombre)
                                ws.write(fila, 4, bib.url)
                        # if not a.fun_referencias() and not a.fun_otrasbiblio():
                        #     ws.write(fila,4, "DOCUMENTO")

                    fila= fila+3

                    ws.write(fila,0, "Total de Visitas", subtitulo)
                    ws.write(fila,1, totalvisitas, subtitulo)
                    detalle = fila + 1
                    ws.write(detalle,0, "Fecha Impresion", subtitulo)
                    ws.write(detalle,1, str(datetime.now()), subtitulo)
                    detalle=detalle+1
                    ws.write(detalle,0, "Usuario", subtitulo)
                    ws.write(detalle,1, str(request.user), subtitulo)

                    nombre ='listadoaccesobiblioteca'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}), content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)}), content_type="application/json")
        else:
            data = {'title': 'Visitas a Biblioteca por Carrera'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['formbiblio'] = ConsultasBibliotecasVirtualesForm(initial={'desde':datetime.now().date(),'hasta':datetime.now().date()})
                return render(request, "reportesexcel/listadoaccesobiblioteca.html", data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))
