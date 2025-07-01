from datetime import datetime,timedelta,date
import json
import xlrd
import xlwt
from decimal import Decimal
from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.db.models import Sum
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from django.utils.encoding import force_str
from decorators import secure_module
from med.models import PersonaExtension
from settings import MEDIA_ROOT
from sga.commonviews import addUserData
from sga.forms import EstudianteFamiliarForm
from sga.models import ReporteExcel, RetiradoMatricula, EstudiantesFamiliar, convertir_fecha, Carrera
from sga.reportes import elimina_tildes
from socioecon.models import InscripcionFichaSocioeconomica


@login_required(redirect_field_name='ret', login_url='/login')
def view(request):

    try:
        if request.method=='POST':
            action = request.POST['action']
            if action :
                # periodo= Periodo.objects.filter(pk=request.POST['periodo'])[:1].get()
                inicio = request.POST['inicio']
                fin = request.POST['fin']
                fechai = convertir_fecha(inicio)
                fechaf = convertir_fecha(fin) + timedelta(hours=23, minutes=59)
                todos = request.POST['todos']

                inscripcion= ''
                try:
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10
                    style1 = xlwt.easyxf('',num_format_str='DD-MMM-YY')
                    wb = xlwt.Workbook()

                    # ezxf = easyxf
                    center = xlwt.easyxf('align: horiz center')
                    # writer = XLSWriter()

                    # data = ["Negrilla", "Centrada", u"Centrada y con corte de linea"]
                    # format = [ezxf('font: bold on'), ezxf('align: horiz center'), ezxf('align: wrap on, horiz center')]
                    # writer.append(data, format)

                    ws = wb.add_sheet('Datos',cell_overwrite_ok=True)
                    # sheet_name.write_merge(fila_inicial, fila_final, columna_inicial, columna_final,).
                    ws.write_merge(0, 0, 0, 30,)
                    ws.write_merge(1, 1, 0, 30,)
                    periodo=None
                    inicio=''
                    fin=''
                    ws.write (0, 0, 'INSTITUTO TECNOLOGICO BOLIVARIANO',center )
                    ws.write(2, 0, 'CEDULA', titulo)
                    ws.write(2, 1, 'NOMBRES', titulo)
                    ws.write(2, 2, 'APELLIDO 1', titulo)
                    ws.write(2, 3, 'APELLIDO 2', titulo)
                    ws.write(2, 4, 'GRUPO', titulo)
                    ws.write(2, 5, 'CARRERA', titulo)
                    ws.write(2, 6, 'INTEGRANTES FAMILIARES - SOCIOECONOMICA', titulo)
                    ws.write(2, 7, 'DECLARADOS EN FICHA MEDICA', titulo)
                    # ws.write(2, 8, 'NOMBRES', titulo)
                    # ws.write(2, 9, 'PARENTESCO', titulo)


                    # periodo= Periodo.objects.filter(pk=request.POST['periodo'])[:1].get()

                    cont = 3
                    c=1
                    detalle=3
                    from django.db import connection
                    cur = connection.cursor()
                    cur.execute("REFRESH MATERIALIZED VIEW estudiantesfamiliar;")
                    try:
                        connection.commit()
                    except Exception as e:
                        print("Error al actualizar la vista materializada estudiantesfamiliar:", str(e))
                        connection.rollback()
                    # print(Matricula.objects.filter(nivel__periodo__inicio__gte=inicio,nivel__periodo__inicio__lte=fin,nivel__nivelmalla__in=(1,2,3,4,5,6),nivel__carrera__carrera=True).distinct('inscripcion').values('inscripcion').count())
                    if todos == 'True':
                        inscripciones = EstudiantesFamiliar.objects.filter(fechainscripcion__gte=fechai, fechainscripcion__lte= fechaf).order_by('apellido1','apellido2')
                    else:
                        carrera = Carrera.objects.filter(pk=request.POST['carrera'])[:1].get()
                        inscripciones = EstudiantesFamiliar.objects.filter(fechainscripcion__gte=fechai,fechainscripcion__lte=fechaf, carrera=carrera).order_by('apellido1', 'apellido2')
                    total = (inscripciones.count())
                    # for matricula in Matricula.objects.filter(nivel__periodo=periodo,nivel__nivelmalla__in=(1,2,3,4,5,6),nivel__periodo__tipo__id=2).order_by('id'):
                    periodo=''
                    num_hoja=1
                    hoja='Datos'+str(num_hoja)
                    for inscripcion in inscripciones:
                        presentar=True
                        # inscripcion = i
                        retiradomat =RetiradoMatricula.objects.filter(inscripcion=inscripcion.inscripcion_id, activo=True)
                        if retiradomat:
                            presentar=False

                        if presentar:
                            if cont==65500:
                                num_hoja=num_hoja+1
                                hoja='Datos'+str(num_hoja)
                                ws = wb.add_sheet(hoja,cell_overwrite_ok=True)
                                cont=1
                            if inscripcion.pasaporte:
                                tipoDocumentoId = 'PASAPORTE'
                                try:
                                    numeroIdentificacion = inscripcion.pasaporte
                                except:
                                    numeroIdentificacion= 'ERROR AL OBTENER PASAPORTE '
                            else:
                                tipoDocumentoId = 'CEDULA'
                                try:
                                    numeroIdentificacion = inscripcion.cedula
                                except:
                                    numeroIdentificacion= 'ERROR AL OBTENER CEDULA '
                            if inscripcion.nombresex == "FEMENINO":
                                sexoId = 'MUJER'
                            else:
                                sexoId = 'HOMBRE'
                            try:
                                nombreins = inscripcion.nombresinscri
                            except:
                                nombreins = 'NO SE PUDO ESCRIBIR EL NOMBRE'
                            try:
                                apellido1 = inscripcion.apellido1
                            except:
                                apellido1 = 'NO SE PUDO ESCRIBIR EL APELLIDO 1'
                            try:
                                apellido2 = inscripcion.apellido2
                            except:
                                apellido2 = 'NO SE PUDO ESCRIBIR EL APELLIDO 2'
                            cantidad =''
                            carrera = elimina_tildes(inscripcion.carrera)
                            grupo=''
                            if inscripcion.grupo_id:
                                try:
                                    grupo = elimina_tildes(inscripcion.gruponombre)
                                except:
                                    grupo =  'NO SE PUDO ESCRIBIR EL GRUPO'
                            fichasocioec =InscripcionFichaSocioeconomica.objects.filter(inscripcion=inscripcion.inscripcion_id).select_related('inscripcion')
                            if  fichasocioec:
                                ficha = fichasocioec.filter()[:1].get()
                                cantidad = ficha.cantidadmiembros
                            cantidad2=0
                            persona_ext=PersonaExtension.objects.filter(persona=inscripcion.persona_id).select_related('persona')
                            if persona_ext:
                                perex  = persona_ext.filter()[:1].get()
                                if perex.padre:
                                    cantidad2 = cantidad2 + 1
                                if perex.madre:
                                    cantidad2 = cantidad2 + 1

                                if perex.conyuge:
                                    cantidad2 = cantidad2 + 1

                            # if PersonaExtension.objects.filter(persona=inscripcion.persona).exists():
                            #     perex  = PersonaExtension.objects.filter(persona=inscripcion.persona)[:1].get()
                            #     if perex.padre:
                            #         padre=''
                            #         try:
                            #             padre = elimina_tildes(perex.padre)
                            #         except:
                            #             padre =  'NO SE PUDO ESCRIBIR EL NOMBRE DEL PADRE'
                            #         ws.write(cont, 0, numeroIdentificacion)
                            #         ws.write(cont, 1, nombreins)
                            #         ws.write(cont, 2, apellido1)
                            #         ws.write(cont, 3, apellido2)
                            #         ws.write(cont, 4, grupo)
                            #         ws.write(cont, 5, carrera)
                            #         ws.write(cont, 6, cantidad)
                            #         ws.write(cont, 7, cantidad2)
                            #         ws.write(cont, 8, padre)
                            #         ws.write(cont, 9, 'PADRE')
                            #         cont=cont+1
                            #         print(cont)
                            #
                            #     if perex.madre:
                            #         madre=''
                            #         try:
                            #             madre = elimina_tildes(perex.madre)
                            #         except:
                            #             madre =  'NO SE PUDO ESCRIBIR EL NOMBRE DE LA MADRE'
                            #         ws.write(cont, 0, numeroIdentificacion)
                            #         ws.write(cont, 1, nombreins)
                            #         ws.write(cont, 2, apellido1)
                            #         ws.write(cont, 3, apellido2)
                            #         ws.write(cont, 4, grupo)
                            #         ws.write(cont, 5, carrera)
                            #         ws.write(cont, 6, cantidad)
                            #         ws.write(cont, 7, cantidad2)
                            #         ws.write(cont, 8, madre)
                            #         ws.write(cont, 9, 'MADRE')
                            #         cont=cont+1
                            #         print(cont)
                            #     if perex.conyuge:
                            #         cony=''
                            #         try:
                            #             cony = elimina_tildes(perex.conyuge)
                            #         except:
                            #             cony =  'NO SE PUDO ESCRIBIR EL NOMBRE DEL CONYUGE'
                            ws.write(cont, 0, numeroIdentificacion)
                            ws.write(cont, 1, nombreins)
                            ws.write(cont, 2, apellido1)
                            ws.write(cont, 3, apellido2)
                            ws.write(cont, 4, grupo)
                            ws.write(cont, 5, carrera)
                            ws.write(cont, 6, cantidad)
                            ws.write(cont, 7, cantidad2)
                            cont=cont+1
                            print(cont)
                    detalle = detalle + cont
                    ws.write(detalle, 0, "Total Estudiantes", subtitulo)
                    ws.write(detalle, 2, total, subtitulo)
                    detalle = detalle + 1
                    ws.write(detalle, 0, "Fecha Impresion", subtitulo)
                    ws.write(detalle, 2, str(datetime.now()), subtitulo)
                    detalle = detalle + 1
                    ws.write(detalle, 0, "Usuario", subtitulo)
                    ws.write(detalle, 2, str(request.user), subtitulo)

                    nombre ='estudiantesfamiiliar'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    return HttpResponse(json.dumps({"result":str(ex)+str(inscripcion)}),content_type="application/json")
        else:
                data = {'title': 'ESTUDIANTES FAMILIARES'}
                addUserData(request,data)
                if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                    reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                    data['reportes'] = reportes
                    data['generarform'] = EstudianteFamiliarForm(
                        initial={'inicio': datetime.now().date(), 'fin': datetime.now().date()})
                    return render(request ,"reportesexcel/estudiantesfamiliar.html" ,  data)
                return HttpResponseRedirect("/reporteexcel")


    except Exception as e:
        print((e))
        return HttpResponseRedirect('/?info='+str(e))