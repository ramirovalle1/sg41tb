from datetime import datetime
import json
import xlwt

from django.contrib.auth.decorators import login_required

from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from settings import MEDIA_ROOT, PROFESORES_GROUP_ID, ALUMNOS_GROUP_ID, SISTEMAS_GROUP_ID
from sga.commonviews import addUserData, ip_client_address
from sga.forms import RangoPagoTarjetasForm, CoordinacionForm
from sga.models import TituloInstitucion,ReporteExcel,Graduado,PerfilInscripcion, convertir_fecha, Absentismo, Coordinacion, MateriaAsignada, Carrera, Inscripcion, Nivel, Matricula, ProfesorMateria, Persona
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

                    administrativos = Persona.objects.filter(usuario__is_active=True).exclude(usuario__groups__id__in=[PROFESORES_GROUP_ID,ALUMNOS_GROUP_ID,SISTEMAS_GROUP_ID]).exclude(nombres__in=['CONGRESO'])
                    docentes = Persona.objects.filter(usuario__is_active=True, usuario__groups__id__in=[PROFESORES_GROUP_ID]).exclude(nombres__in=['CONGRESO'])

                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('ADMINISTRATIVOS',cell_overwrite_ok=True)
                    wsp = wb.add_sheet('DOCENTES',cell_overwrite_ok=True)

                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,5, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,5, 'LISTADO PERSONAL ADMINISTRATIVO', titulo2)

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
                    p=None

                    for p in administrativos:
                        nombre = elimina_tildes(p.nombre_completo_inverso())
                        if p.cedula:
                            identificacion = elimina_tildes(p.cedula)
                        else:
                            identificacion = elimina_tildes(p.pasaporte)
                        if p.email:
                            email = elimina_tildes(p.email)
                        if p.emailinst:
                            emailint = elimina_tildes(p.emailinst)
                        if p.telefono:
                            celular = elimina_tildes(p.telefono)
                        if p.telefono_conv:
                            convencional = elimina_tildes(p.telefono_conv)

                        ws.write(fila, 0, nombre)
                        ws.write(fila, 1, identificacion)
                        ws.write(fila, 2, email)
                        ws.write(fila, 3, emailint)
                        ws.write(fila, 4, celular)
                        ws.write(fila, 5, convencional)

                        fila = fila+1

                    ws.write(fila+1, 0, "Fecha Impresion", subtitulo)
                    ws.write(fila+1, 2, str(datetime.now()), subtitulo)
                    ws.write(fila+2, 0, "Usuario", subtitulo)
                    ws.write(fila+2, 2, str(request.user), subtitulo)

# ------------------------------------------------------- DOCENTES ------------------------------------------------------
                    wsp.write_merge(0, 0,0,5, tit.nombre , titulo2)
                    wsp.write_merge(1, 1,0,5, 'LISTADO PERSONAL DOCENTE', titulo2)

                    fila=3
                    wsp.write(fila, 0,'NOMBRE', titulo)
                    wsp.write(fila, 1,'CEDULA', titulo)
                    wsp.write(fila, 2,'CORREO PERSONAL', titulo)
                    wsp.write(fila, 3,'CORREO INSTITUCIONAL', titulo)
                    wsp.write(fila, 4,'CELULAR', titulo)
                    wsp.write(fila, 5,'CONVENCIONAL', titulo)

                    fila=4
                    nombre = ''
                    email = ''
                    emailint = ''
                    celular = ''
                    convencional = ''

                    for p in administrativos:
                        nombre = elimina_tildes(p.nombre_completo_inverso())
                        if p.cedula:
                            identificacion = elimina_tildes(p.cedula)
                        else:
                            identificacion = elimina_tildes(p.pasaporte)
                        if p.email:
                            email = elimina_tildes(p.email)
                        if p.emailinst:
                            emailint = elimina_tildes(p.emailinst)
                        if p.telefono:
                            celular = elimina_tildes(p.telefono)
                        if p.telefono_conv:
                            convencional = elimina_tildes(p.telefono_conv)

                        wsp.write(fila, 0, nombre)
                        wsp.write(fila, 1, identificacion)
                        wsp.write(fila, 2, email)
                        wsp.write(fila, 3, emailint)
                        wsp.write(fila, 4, celular)
                        wsp.write(fila, 5, convencional)

                        fila = fila+1

                    wsp.write(fila+1, 0, "Fecha Impresion", subtitulo)
                    wsp.write(fila+1, 2, str(datetime.now()), subtitulo)
                    wsp.write(fila+2, 0, "Usuario", subtitulo)
                    wsp.write(fila+2, 2, str(request.user), subtitulo)

                    nombre ='personalITB'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")
                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)+" "+str(p)}),content_type="application/json")

        else:
            data = {'title': 'Listado Personal ITB'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                return render(request ,"reportesexcel/xls_personalitb.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

