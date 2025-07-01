from datetime import datetime
import json
import xlwt
from django.contrib.admin.models import LogEntry
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from decorators import secure_module
from settings import MEDIA_ROOT
from sga.commonviews import addUserData
from sga.forms import EficienciaExcelForm
from sga.models import TituloInstitucion, ReporteExcel, Persona, Inscripcion, Profesor, Matricula
from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method == 'POST':
            action = request.POST['action']
            if action == 'generarexcel':
                try:
                    mtr = Matricula.objects.filter(nivel__cerrado=False,).values_list('inscripcion',flat=True)
                    inscripcion=Inscripcion.objects.filter(Q(carrera__carrera=False)|Q(matricula__nivel__cerrado=True),~Q(id__in=mtr)).order_by('persona_id').distinct('persona_id').values('persona_id')

                    usu=User.objects.filter(groups=None).values('id')
                    # matri2=Matricula.objects.filter(nivel__cerrado=False,nivel__periodo__activo=True, inscripcion__persona__usuario__is_active=True,liberada=False).count()
                    persona = (Persona.objects.filter(usuario__is_active=True).exclude(nombres__in=['CONGRESO']).exclude(cedula='').
                               exclude(cedula__icontains='999999').exclude(pasaporte__icontains='999999').exclude(id__in=inscripcion).exclude(usuario__id__in=usu).distinct('apellido1', 'apellido2', 'nombres', 'cedula').order_by('apellido1', 'apellido2', 'nombres', 'cedula'))


                    titulo_style = xlwt.easyxf('font: name Times New Roman, colour black, bold on, height 220; align: horiz center')
                    subtitulo_style = xlwt.easyxf('font: name Times New Roman, colour black, bold on, height 200; align: horiz center')
                    header_style = xlwt.easyxf('pattern: pattern solid, fore_colour grey25; font: name Times New Roman, colour black, bold on, height 200; align: horiz center')
                    cell_style = xlwt.easyxf('font: name Times New Roman, height 200; align: horiz left')

                    wb = xlwt.Workbook()
                    row_limit = 65536
                    headers = ["ID", "FIRST NAME", "LAST NAME", "DEPARTMENT", "START TIME OF EFFECTIVE PERIOD",
                               "END TIME OF EFFECTIVE PERIOD", "GENDER", "EMAIL", "PHONE"]
                    col_widths = [3000, 7000, 9000, 8000, 8000, 8000, 8000,8000,8000]
                    def add_headers(ws, sheet_num):
                        tit = TituloInstitucion.objects.all()[:1].get()
                        ws.write_merge(0, 0, 0, 8, tit.nombre, titulo_style)
                        ws.write_merge(1, 1, 0, 8, 'LISTADO DE PERSONAL ITB', titulo_style)
                        ws.write_merge(2, 2, 0, 8, f'Página {sheet_num}', titulo_style)
                        for col_num, header in enumerate(headers):
                            ws.write(6, col_num, header, header_style)
                        for col, width in enumerate(col_widths):
                            ws.col(col).width = width

                    sheet_num = 1
                    ws = wb.add_sheet(f'Registros {sheet_num}', cell_overwrite_ok=True)
                    add_headers(ws, sheet_num)

                    fila = 7
                    con=0
                    con2=0
                    for p in persona:
                        if fila >= row_limit:
                            sheet_num += 1
                            ws = wb.add_sheet(f'Registros {sheet_num}', cell_overwrite_ok=True)
                            add_headers(ws, sheet_num)
                            fila = 7
                        identificacion = p.cedula if p.cedula else elimina_tildes(p.pasaporte)
                        ws.write(fila, 0, identificacion, cell_style)
                        ws.write(fila, 1, elimina_tildes(str(p.nombres)), cell_style)
                        ws.write(fila, 2, elimina_tildes(str(p.apellido1)) + ' ' + elimina_tildes(str(p.apellido2)),
                                 cell_style)
                        if Inscripcion.objects.filter(persona=p).exists():
                            ins= Inscripcion.objects.filter(persona=p)[:1].get()
                            if ins.matriculado():
                                ws.write(fila, 3, 'ESTUDIANTE', cell_style)
                                con=con+1
                            else:
                                ws.write(fila, 3, 'ESTUDIANTE SIN MATRICULA', cell_style)
                                con2=con2+1
                        elif Profesor.objects.filter(persona=p).exists():
                            ws.write(fila, 3, 'DOCENTE', cell_style)

                        elif p.usuario.groups:
                            mo=p.usuario.groups.first()
                            ws.write(fila, 3, str(mo), cell_style)
                        if p.usuario.date_joined:
                            date_joined_formatted = p.usuario.date_joined.strftime('%Y/%m/%d %H:%M:%S')
                            ws.write(fila, 4, date_joined_formatted, cell_style)
                        if p.usuario.last_login:
                            last_login_formatted = p.usuario.last_login.strftime('%Y/%m/%d %H:%M:%S')
                            ws.write(fila, 5, last_login_formatted, cell_style)
                        if p.sexo:
                            ws.write(fila, 6, elimina_tildes(str(p.sexo.nombre)), cell_style)
                        else:
                            ws.write(fila, 6, '', cell_style)
                        if p.emailinst:
                            ws.write(fila, 7, elimina_tildes(str(p.emailinst)), cell_style)
                        else:
                            ws.write(fila, 7, '', cell_style)
                        if p.telefono:
                            ws.write(fila, 8, p.telefono, cell_style)
                        else:
                            if p.telefono_conv:
                                ws.write(fila, 8, p.telefono_conv, cell_style)
                            else:
                                ws.write(fila, 8, '', cell_style)

                        fila += 1

                    ws.write(fila + 1, 0, "Fecha Impresión", subtitulo_style)
                    ws.write(fila + 1, 1, str(datetime.now()), cell_style)
                    ws.write(fila + 2, 0, "Usuario", subtitulo_style)
                    ws.write(fila + 2, 1, str(request.user), cell_style)


                    nombre = 'PersonalItb' + str(datetime.now()).replace(" ", "").replace(".", "").replace(":",
                                                                                                           "") + '.xls'
                    wb.save(MEDIA_ROOT + '/reporteexcel/' + nombre)
                    return HttpResponse(json.dumps({"result": "ok", "url": "/media/reporteexcel/" + nombre}),
                                        content_type="application/json")

                except Exception as ex:
                    print(ex)
                    return HttpResponse(json.dumps({"result": str(ex)}), content_type="application/json")

        else:
            data = {'title': 'Personal'}
            addUserData(request, data)


            return render(request, "reportesexcel/xls_personalitb.html", data)

    except Exception as e:
        return HttpResponseRedirect('/?info=' + str(e))
