from datetime import datetime,timedelta
import json
import xlwt
import xlrd
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render

from sga.forms import  RangoPagoTarjetasForm
from sga.models import TituloInstitucion, Inscripcion, elimina_tildes, ReporteExcel, convertir_fecha, InscripcionGrupo, Grupo, Nivel
from sga.commonviews import addUserData
from settings import MEDIA_ROOT


@login_required(redirect_field_name='ret', login_url='/login')
def view(request):

    try:
        if request.method=='POST':
            action = request.POST['action']
            if action :
                if 'exportar' in request.POST:
                    nivel = Nivel.objects.filter(pk=request.POST['g'])[:1].get()
                    matriculados =nivel.matriculados()
                else:
                    inicio = request.POST['inicio']
                    fin = request.POST['fin']
                    fechai = convertir_fecha(inicio)
                    fechaf = convertir_fecha(fin)
                    inscritos = Inscripcion.objects.filter(persona__usuario__is_active=True, fecha__gte=fechai,fecha__lte=fechaf).order_by('persona__apellido1','persona__apellido2')
                try:
                    m = 8
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10
                    style1 = xlwt.easyxf('',num_format_str='DD-MMM-YY')
                    wb = xlwt.Workbook()

                    ws = wb.add_sheet('Informacion',cell_overwrite_ok=True)
                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,m+2, tit.nombre , titulo2)
                    if 'exportar' in request.POST:
                        ws.write_merge(1, 1, 0, m + 2, 'DATOS DE ESTUDIANTES ' + nivel.grupo.nombre , titulo2)
                    else:
                        ws.write_merge(1, 1,0,m+2, 'DATOS DE ESTUDIANTES ', titulo2)
                    detalle = 4
                    fila = 2

                    identificacion=''
                    estudiante=''
                    canton_residencia=''
                    provincia_residencia=''
                    parroquia_residencia=''
                    colegio=''
                    sector=''
                    empresa=''
                    nombreempresa=''
                    cargo=''
                    matri=''
                    nivel=''
                    paralelo=''
                    emailinst=''
                    email=''
                    telefono=''
                    celular=''
                    modalidad=''
                    inscripcion=''

                    if 'exportar' in request.POST:
                        for matricula in matriculados:
                            matriculado = 'NO'
                            nivel = ''
                            paralelo = ''
                            if matricula.inscripcion.persona.cedula:
                                identificacion = matricula.inscripcion.persona.cedula
                            else:
                                identificacion = matricula.inscripcion.persona.pasaporte

                            estudiante = matricula.inscripcion.persona.nombre_completo_inverso()

                            if matricula.inscripcion.persona.emailinst:
                                emailinst=matricula.inscripcion.persona.emailinst
                            else:
                                emailinst=''

                            if matricula.inscripcion.persona.email:
                                email=matricula.inscripcion.persona.email
                            else:
                                email=''


                            grupo = ''
                            if not 'exportar' in request.POST:
                                if InscripcionGrupo.objects.filter(inscripcion=inscripcion).exists():
                                    grupo = InscripcionGrupo.objects.filter(inscripcion=inscripcion)[:1].get().grupo.nombre

                            ws.write(fila, 0, elimina_tildes(matricula.inscripcion.persona.usuario.username))
                            ws.write(fila, 1, str(identificacion))
                            ws.write(fila, 2, elimina_tildes(matricula.inscripcion.persona.nombres))
                            ws.write(fila, 3, elimina_tildes(matricula.inscripcion.persona.apellido1))
                            ws.write(fila, 4, elimina_tildes(matricula.inscripcion.persona.apellido2))
                            ws.write(fila, 5, emailinst)
                            ws.write(fila, 6, email)
                            ws.write(fila, 7, elimina_tildes(matricula.inscripcion.carrera.nombre))
                            fila=fila + 1

                    else:
                        for inscripcion in inscritos:
                            matriculado = 'NO'
                            nivel = ''
                            paralelo = ''
                            if inscripcion.persona.cedula:
                                identificacion = inscripcion.persona.cedula
                            else:
                                identificacion = inscripcion.persona.pasaporte

                            estudiante = inscripcion.persona.nombre_completo_inverso()

                            if inscripcion.persona.emailinst:
                                emailinst=inscripcion.persona.emailinst
                            else:
                                emailinst=''

                            if inscripcion.persona.email:
                                email=inscripcion.persona.email
                            else:
                                email=''

                            grupo = ''
                            if InscripcionGrupo.objects.filter(inscripcion=inscripcion).exists():
                                grupo = InscripcionGrupo.objects.filter(inscripcion=inscripcion)[:1].get().grupo.nombre

                            ws.write(fila, 0, elimina_tildes(inscripcion.persona.usuario.username))
                            ws.write(fila, 1, str(identificacion))
                            ws.write(fila, 2, elimina_tildes(inscripcion.persona.nombres))
                            ws.write(fila, 3, elimina_tildes(inscripcion.persona.apellido1))
                            ws.write(fila, 4, elimina_tildes(inscripcion.persona.apellido2))
                            ws.write(fila, 5, emailinst)
                            ws.write(fila, 6, grupo)
                            fila=fila + 1

                    detalle = detalle + fila
                    ws.write(detalle, 0, "Fecha Impresion", subtitulo)
                    ws.write(detalle, 1, str(datetime.now()), subtitulo)
                    detalle=detalle +1
                    ws.write(detalle, 0, "Usuario", subtitulo)
                    ws.write(detalle, 1, str(request.user), subtitulo)

                    nombre ='datos'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    return HttpResponse(json.dumps({"result":str(ex)+str(inscripcion)}), content_type="application/json")

        else:
            data = {'title': 'Datos de Estudiantes '}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform'] = RangoPagoTarjetasForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
            return render(request ,"reportesexcel/datos_estudiantes.html" ,  data)

    except Exception as e:
        print((e))
        return HttpResponseRedirect('/?info='+str(e))