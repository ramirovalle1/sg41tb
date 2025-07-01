from datetime import datetime
import json
import xlwt
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from settings import MEDIA_ROOT
from sga.commonviews import addUserData
from sga.forms import ListadoDocentexCoordinacion
from sga.models import TituloInstitucion,ReporteExcel,Coordinacion, Profesor, RolPerfilProfesor
from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']

            if action  =='generarexcel':
                try:
                    coordinacion = Coordinacion.objects.filter(pk= request.POST['coordinacion'])[:1].get()
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
                    ws.write_merge(1, 1,0,8, 'LISTADO DE DOCENTES POR COORDINACION', titulo2)

                    fila =3
                    ws.write(fila,0, 'COORDINACION:', titulo)
                    ws.write(fila,1, coordinacion.nombre, titulo)

                    fila=5
                    ws.write(fila, 0,  'NOMBRES', titulo)
                    ws.col(0).width = 10 * 600
                    ws.write(fila, 1,  'APELLIDOS', titulo)
                    ws.col(1).width = 10 * 700
                    ws.write(fila, 2,  'CEDULA', titulo)
                    ws.write(fila, 3,  'DIRECCION', titulo)
                    ws.col(3).width = 10 * 800
                    ws.write(fila, 4,  'TELEFONO', titulo)
                    ws.write(fila, 5,  'TIEMPO DE DEDICACION', titulo)
                    ws.col(5).width = 10 * 500
                    ws.write(fila, 6,  'FECHA NACIMIENTO', titulo)
                    ws.col(6).width = 10 * 400
                    ws.write(fila, 7,  'N. CONTRATO', titulo)
                    ws.col(7).width = 10 * 400
                    ws.write(fila, 8,  'F. INGRESO', titulo)
                    ws.write(fila, 9,  'CORREO PERSONAL', titulo)
                    ws.col(9).width = 10 * 700
                    ws.write(fila, 10,  'CORREO EDUCATIVO', titulo)
                    ws.col(10).width = 10 * 700
                    ws.write(fila, 11,  'DISCAPACIDAD', titulo)

                    # carreraprofesor = Coordinacion.objects.filter(pk=request.POST['coordinacion']).values_list('carrera',flat=True)
                    coordinacionid = Coordinacion.objects.filter(pk= request.POST['coordinacion']).values('id')
                    profesorM = RolPerfilProfesor.objects.filter(coordinacion__in=coordinacionid,profesor__activo= True)
                    profesor = Profesor.objects.filter(id__in= profesorM)
                    total_profesor =0
                    for p in profesor:
                        fila=fila+1
                        total_profesor = profesor.count()
                        if p.persona.cedula:
                            nacionalidad = p.persona.cedula
                        else:
                            nacionalidad =p.persona.pasaporte
                        if p.persona.direccion:
                            direccion = p.persona.direccion
                        else:
                            direccion =''

                        if p.dedicacion.nombre:
                            tiempo = p.dedicacion.nombre
                        else:
                            tiempo= ''
                        if p.numerocontrato:
                            numerocontrato =p.numerocontrato
                        else:
                            numerocontrato=''

                        if p.tienediscapacidad:
                            discapacidad = p.tipodiscapacidad.nombre
                        else:
                            discapacidad =''

                        ws.write(fila, 0, p.persona.nombres)
                        ws.write(fila, 1, p.persona.apellido1 +' '+ p.persona.apellido2)
                        ws.write(fila, 2, nacionalidad)
                        ws.write(fila, 3, direccion)
                        ws.write(fila, 4, p.persona.telefono)
                        ws.write(fila, 5, tiempo)
                        ws.write(fila, 6, str(p.persona.nacimiento))
                        ws.write(fila, 7, numerocontrato)
                        ws.write(fila, 8, str(p.fechaingreso))
                        ws.write(fila, 9, p.persona.email)
                        ws.write(fila, 10, p.persona.emailinst)
                        ws.write(fila, 11, discapacidad)

                    fila= fila+2
                    ws.write(fila,0, "Total de Docentes:", subtitulo)
                    ws.write(fila,1, total_profesor, subtitulo)
                    detalle = fila + 2
                    ws.write(detalle,0, "Fecha Impresion", subtitulo)
                    ws.write(detalle,1, str(datetime.now()), subtitulo)
                    detalle=detalle+1
                    ws.write(detalle,0, "Usuario", subtitulo)
                    ws.write(detalle,1, str(request.user), subtitulo)

                    nombre ='listadodocente'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}), content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)}), content_type="application/json")
        else:
            data = {'title': 'Listado Docente'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['form'] = ListadoDocentexCoordinacion()
                return render(request,"reportesexcel/listadodocentes.html", data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))
