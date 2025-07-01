from datetime import datetime
import json
import xlwt
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from settings import MEDIA_ROOT, PROFESORES_GROUP_ID,ALUMNOS_GROUP_ID
from sga.commonviews import addUserData, ip_client_address
from sga.models import TituloInstitucion,ReporteExcel,convertir_fecha,Persona
from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action :
                try:
                    m = 5
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10

                    docentes = Persona.objects.filter(usuario__is_active=True, usuario__groups__id__in=[PROFESORES_GROUP_ID]).exclude(usuario__groups__id__in=[ALUMNOS_GROUP_ID]).exclude(nombres__in=['CONGRESO']).order_by('apellido1','apellido2')

                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('DOCENTES',cell_overwrite_ok=True)

                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,5, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,5, 'LISTADO PERSONAL DOCENTE', titulo2)

                    fila=3
                    ws.write(fila, 0,'NOMBRE', titulo)
                    ws.write(fila, 1,'CEDULA', titulo)
                    ws.write(fila, 2,'CORREO PERSONAL', titulo)
                    ws.write(fila, 3,'CORREO INSTITUCIONAL', titulo)
                    ws.write(fila, 4,'CELULAR', titulo)
                    ws.write(fila, 5,'CONVENCIONAL', titulo)

                    fila=4
                    nombre = ''
                    email = ''
                    emailint = ''
                    celular = ''
                    convencional = ''


                    for d in docentes:
                        nombre = elimina_tildes(d.nombre_completo_inverso())
                        if d.cedula:
                            identificacion = elimina_tildes(d.cedula)
                        else:
                            identificacion = elimina_tildes(d.pasaporte)
                        if d.email:
                            email = elimina_tildes(d.email)
                        if d.emailinst:
                            emailint = elimina_tildes(d.emailinst)
                        if d.telefono:
                            celular = elimina_tildes(d.telefono)
                        if d.telefono_conv:
                            convencional = elimina_tildes(d.telefono_conv)

                        ws.write(fila, 0, nombre, subtitulo)
                        ws.write(fila, 1, identificacion, subtitulo)
                        ws.write(fila, 2, email, subtitulo)
                        ws.write(fila, 3, emailint, subtitulo)
                        ws.write(fila, 4, celular, subtitulo)
                        ws.write(fila, 5, convencional, subtitulo)

                        fila = fila+1

                    ws.write(fila+1, 0, "Fecha Impresion", subtitulo)
                    ws.write(fila+1, 2, str(datetime.now()), subtitulo)
                    ws.write(fila+2, 0, "Usuario", subtitulo)
                    ws.write(fila+2, 2, str(request.user), subtitulo)

                    nombre ='docentes_activos'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")
                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)+" "+str(d)}),content_type="application/json")

        else:
            data = {'title': 'Listado Personal Docente ITB'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                return render(request ,"reportesexcel/xls_docentesactivos.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

