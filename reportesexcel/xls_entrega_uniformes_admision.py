from datetime import datetime,timedelta
import json
import xlwt
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from settings import MEDIA_ROOT
from sga.commonviews import addUserData
from sga.forms import RangoPagoTarjetasForm
from sga.models import convertir_fecha, TituloInstitucion, ReporteExcel, Carrera, Matricula, EntregaUniformeAdmisiones, \
    InscripcionGrupo
from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action :
                try:
                    inicio = convertir_fecha(request.POST['inicio'])
                    fin = convertir_fecha(request.POST['fin'])
                    entregas = EntregaUniformeAdmisiones.objects.filter(fecha__range=(inicio, fin)).order_by('fecha')
                    # entregas = EntregaUniformeAdmisiones.objects.filter(fecha__range=(inicio,fin)).order_by('fecha')
                    totalestudiantes=entregas.count()
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo3 = xlwt.easyxf('font: name Times New Roman; align: wrap on, vert centre, horiz center')
                    subtitulo.font.height = 20*10
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('Registros',cell_overwrite_ok=True)

                    tit = TituloInstitucion.objects.first()
                    ws.write_merge(0, 0 ,0, 12, tit.nombre , titulo2)
                    ws.write_merge(1, 1, 0, 12, 'ENTREGA DE UNIFORMES POR PARTE DE ADMISIONES',titulo2)

                    ws.write(3, 0, 'DESDE: '+str(inicio), subtitulo)
                    ws.write(4, 0, 'HASTA: '+str(fin), subtitulo)

                    ws.write(6, 0, 'FECHA', subtitulo)
                    ws.write(6, 1, 'IDENTIFICACION', subtitulo)
                    ws.write(6, 2, 'NOMBRE ALUMNO', subtitulo)
                    ws.write(6, 3, 'CELULAR', subtitulo)
                    ws.write(6, 4, 'CONVENCIONAL', subtitulo)
                    ws.write(6, 5, 'EMAIL PERSONAL', subtitulo)
                    ws.write(6, 6, 'EMAIL INSTITUCIONAL', subtitulo)
                    ws.write(6, 7, 'PROMOCION', subtitulo)
                    ws.write(6, 8, 'GRUPO', subtitulo)
                    ws.write(6, 9, 'TALLA', subtitulo)
                    ws.write(6, 10, 'USUARIO REGISTRA', subtitulo)
                    ws.write(6, 11, 'ENTREGADO', subtitulo)
                    ws.write(6, 12, 'FECHA ENTREGA', subtitulo)
                    ws.write(6, 13, 'USUARIO ENTREGA', subtitulo)
                    ws.write(6, 14, 'CARRERA', subtitulo)

                    fila = 7
                    for x in entregas:
                        grupo = InscripcionGrupo.objects.filter(inscripcion=x.inscripcion, activo=True).last().grupo.nombre
                        ws.write(fila, 0, str(x.fecha))
                        ws.write(fila, 1, x.inscripcion.persona.cedula if x.inscripcion.persona.cedula else x.inscripcion.persona.pasaporte)
                        ws.write(fila, 2, elimina_tildes(x.inscripcion.persona.nombre_completo_inverso()))
                        ws.write(fila, 3, x.inscripcion.persona.telefono if x.inscripcion.persona.telefono else '')
                        ws.write(fila, 4, x.inscripcion.persona.telefono_conv if x.inscripcion.persona.telefono_conv else '')
                        ws.write(fila, 5, x.inscripcion.persona.email if x.inscripcion.persona.email else '')
                        ws.write(fila, 6, x.inscripcion.persona.emailinst if x.inscripcion.persona.emailinst else '')
                        ws.write(fila, 7, elimina_tildes(x.inscripcion.promocion.descripcion))
                        ws.write(fila, 8, grupo)
                        ws.write(fila, 9, x.talla.nombre)
                        ws.write(fila, 10, x.usuario.username)
                        ws.write(fila, 11, 'SI' if x.entregado else 'NO')
                        ws.write(fila, 12, str(x.fechaentrega) if x.fechaentrega else '')
                        ws.write(fila, 13, str(x.usuarioentrega.username) if x.usuarioentrega else '')
                        ws.write(fila, 14, str(x.inscripcion.carrera) if x.inscripcion.carrera else '')

                        fila += 1
                    fila += 1
                    ws.write(fila, 0, "Total Estudiantes: "+ str(totalestudiantes), subtitulo)
                    fila += 1
                    ws.write(fila, 0, "Fecha Impresion", subtitulo)
                    ws.write(fila, 1, str(datetime.now()), subtitulo)
                    ws.write(fila+1, 0, "Usuario", subtitulo)
                    ws.write(fila+1, 1, str(request.user), subtitulo)

                    nombre ='uniformes'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")
                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)}), content_type="application/json")

        else:
            data = {'title': 'Entrega de Uniformes'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform'] = RangoPagoTarjetasForm(initial={'inicio':datetime.now().date(), 'fin':datetime.now().date()})
                return render(request ,"reportesexcel/entrega_uniformes_admision.html", data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

