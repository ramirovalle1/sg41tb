from datetime import datetime
import json
import xlwt
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from settings import MEDIA_ROOT
from sga.commonviews import addUserData
from sga.forms import RangoFacturasForm
from sga.models import convertir_fecha, TituloInstitucion, ReporteExcel, Profesor, RolPerfilProfesor
from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            inicio = request.POST['inicio']
            fin = request.POST['fin']
            if action  =='generarexcel':
                fechai = convertir_fecha(inicio)
                fechaf = convertir_fecha(fin)
                try:
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulocabecera = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    # BORDES
                    borders = xlwt.Borders()
                    borders.left = xlwt.Borders.THIN
                    borders.right = xlwt.Borders.THIN
                    borders.top = xlwt.Borders.THIN
                    borders.bottom = xlwt.Borders.THIN
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    titulocabecera.font.height = 20 * 11
                    titulocabecera.borders = borders
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('LISTADO',cell_overwrite_ok=True)
                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,8, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,8, 'LISTADO DE DOCENTES ACTIVOS POR FECHA DE INGRESO', titulo2)
                    ws.write(2, 0,'Desde:', titulo2)
                    ws.write(2, 1,str(inicio))
                    ws.write(3, 0,'Hasta: ', titulo2)
                    ws.write(3, 1,str(fin))

                    fila =5
                    ws.write(fila, 0,  'CEDULA', titulo)
                    ws.write(fila, 1,  'APELLIDOS', titulo)
                    ws.col(1).width = 10 * 700
                    ws.write(fila, 2,  'NOMBRES', titulo)
                    ws.col(2).width = 10 * 600
                    ws.write(fila, 3,  'F. INGRESO', titulo)
                    ws.write(fila, 4,  'CATEGORIA', titulo)
                    ws.write(fila, 5,  'DEDICACION', titulo)
                    ws.write(fila, 6,  'TIENE PROGRAMACION', titulo)
                    ws.write(fila, 7,  'FACULTAD', titulo)

                    profesor = Profesor.objects.filter(activo= True,fechaingreso__gte=fechai,fechaingreso__lte=fechaf).order_by('persona__apellido1','persona__apellido2','persona__nombres')
                    total_profesor = profesor.count()
                    for p in profesor:
                        programaciondocente = 0
                        coordinaciondocente=None
                        fila=fila+1
                        if p.persona.cedula:
                            identificacion = p.persona.cedula
                        else:
                            identificacion = p.persona.pasaporte

                        if p.fechaingreso:
                            fingreso = str(p.fechaingreso)
                        else:
                            fingreso =''
                        if p.dedicacion.nombre:
                            dedicacion = p.dedicacion.nombre
                        else:
                            dedicacion= ''
                        if p.categoria:
                            categoria = p.categoria.nombre
                        else:
                            categoria=''

                        if p.cantidad_materiascabierta()>0:
                            programaciondocente=p.cantidad_materiascabierta()

                        if RolPerfilProfesor.objects.filter(profesor=p).exists():
                            coordinaciondocente=RolPerfilProfesor.objects.filter(profesor=p)[:1].get()
                            if coordinaciondocente.coordinacion:
                                coordinaciondocente=coordinaciondocente.coordinacion.nombre
                            else:
                                coordinaciondocente=''

                        ws.write(fila, 0, identificacion)
                        ws.write(fila, 1, elimina_tildes(p.persona.apellido1) +' '+ elimina_tildes(p.persona.apellido2))
                        ws.write(fila, 2, elimina_tildes(p.persona.nombres))
                        ws.write(fila, 3, fingreso)
                        ws.write(fila, 4, categoria)
                        ws.write(fila, 5, dedicacion)
                        ws.write(fila, 6, 'Materias '+ str(programaciondocente))
                        ws.write(fila, 7, coordinaciondocente)

                    fila= fila+2
                    ws.write(fila,0, "Total Docentes:", subtitulo)
                    ws.write(fila,1, total_profesor, subtitulo)
                    detalle = fila + 2
                    ws.write(detalle,0, "Fecha Impresion", subtitulo)
                    ws.write(detalle,1, str(datetime.now()), subtitulo)
                    detalle=detalle+1
                    ws.write(detalle,0, "Usuario", subtitulo)
                    ws.write(detalle,1, str(request.user), subtitulo)

                    nombre ='docentesxfingreso'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}), content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)}), content_type="application/json")
        else:
            data = {'title': 'Listado Docentes'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['form'] = RangoFacturasForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
                return render(request,"reportesexcel/listadocentesporingreso.html", data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))
