from datetime import datetime,timedelta
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
from settings import UTILIZA_GRUPOS_ALUMNOS, EMAIL_ACTIVE,MEDIA_ROOT, ASIG_VINCULACION, ASIG_PRATICA
from sga.commonviews import addUserData, ip_client_address
from sga.forms import AbsentosyRetiradosExcelForm
from sga.models import Inscripcion,convertir_fecha,Matricula,TituloInstitucion,ReporteExcel,Coordinacion,Carrera,Absentismo,RetiradoMatricula,DetalleRetiradoMatricula

from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            anio = request.POST['anio']
            coordinacion = Coordinacion.objects.get(pk=request.POST['coordinacion'])
            carreras = Carrera.objects.filter(coordinacion__id = coordinacion.id).values('id')

            if action :
                wb = xlwt.Workbook()
                ws = wb.add_sheet('Registros',cell_overwrite_ok=True)
                try:
                    m = 14
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo3 = xlwt.easyxf('font: name Times New Roman; align: wrap on, vert centre, horiz center')
                    subtitulo.font.height = 20*10


                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,m, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,m, 'ESTUDIANTES ABSENTOS Y RETIRADOS POR FACULTAD',titulo2)
                    ws.write(3, 0,'Anio:   ' +str(anio), subtitulo)
                    ws.write(4, 0,'Facultad:   ' +str(coordinacion.nombre), subtitulo)

                    ws.write(7,0,"Identificacion",titulo)
                    ws.write(7,1,"Nombres y Apellidos",titulo)
                    ws.write(7,2,"Convencional",titulo)
                    ws.write(7,3,"Celular",titulo)
                    ws.write(7,4,"Email Inst",titulo)
                    ws.write(7,5,"Email Personal",titulo)
                    ws.write(7,6,"Carrera",titulo)
                    ws.write(7,7,"Nivel",titulo)
                    ws.write(7,8,"Grupo",titulo)
                    ws.write(7,9,"Absento",titulo)
                    ws.write(7,10,"Motivo",titulo)
                    ws.write(7,11,"Fecha",titulo)
                    ws.write(7,12,"Retirado",titulo)
                    ws.write(7,13,"Motivo",titulo)
                    ws.write(7,14,"Fecha",titulo)
                    fila = 8
                    detalle=3
                    matri=''
                    identificacion=''

                    for carrera in carreras:
                        matriculas = Matricula.objects.filter(fecha__year=anio,nivel__carrera__carrera=True,nivel__carrera__id=carrera['id']).distinct('inscripcion')
                        for matri in matriculas:
                            try:
                                absento=None
                                retirado=None
                                celular=''
                                identificacion=''
                                correo1=''
                                correo2=''
                                esabsento='No'
                                absentomotivo=''
                                absentofecha=''
                                esretirado='No'
                                retiradomotivo=''
                                retiradofecha=''

                                if matri.inscripcion.persona.cedula:
                                    identificacion = matri.inscripcion.persona.cedula
                                else:
                                    identificacion = matri.inscripcion.persona.pasaporte

                                nombrecompleto= ''
                                nivel=''
                                grupo=''
                                try:
                                    nombrecompleto=elimina_tildes(matri.inscripcion.persona.nombre_completo())
                                except :
                                    nombrecompleto=''

                                convencional=''
                                try:
                                    if matri.inscripcion.persona.telefono_conv:
                                        convencional=elimina_tildes(matri.inscripcion.persona.telefono_conv)
                                except Exception as t:
                                        convencional=''

                                try:
                                    if matri.inscripcion.persona.telefono:
                                        celular=elimina_tildes(matri.inscripcion.persona.telefono)
                                except Exception as t:
                                        celular=''

                                if matri.inscripcion.persona.emailinst:
                                    correo1= elimina_tildes(matri.inscripcion.persona.emailinst)
                                else:
                                    correo1=''

                                if matri.inscripcion.persona.email:
                                    correo2=elimina_tildes(matri.inscripcion.persona.email)
                                else:
                                    correo2=''

                                try:
                                    carrera = elimina_tildes(matri.inscripcion.carrera.nombre)
                                except:
                                    carrera = ''

                                try:
                                    nivel = elimina_tildes(matri.nivel.nivelmalla)
                                except:
                                    nivel = ''

                                try:
                                    grupo = elimina_tildes(matri.nivel.grupo.nombre)
                                except:
                                    grupo = ''

                                if Absentismo.objects.filter(materiaasignada__matricula__inscripcion__persona__usuario__is_active=True,finalizado=False,materiaasignada__matricula=matri).exists():
                                    absento = Absentismo.objects.filter(materiaasignada__matricula__inscripcion__persona__usuario__is_active=True,finalizado=False,materiaasignada__matricula=matri)[:1].get()
                                    esabsento='Si'
                                    absentomotivo=elimina_tildes(absento.observacion)
                                    absentofecha=str(absento.fecha.date())

                                if RetiradoMatricula.objects.filter(inscripcion=matri.inscripcion,nivel=matri.nivel,activo=False).exists():
                                    retirado= RetiradoMatricula.objects.filter(inscripcion=matri.inscripcion,nivel=matri.nivel,activo=False)[:1].get()
                                    detalleretirado= DetalleRetiradoMatricula.objects.filter(retirado=retirado).order_by('-id')[:1].get()
                                    esretirado='Si'
                                    retiradomotivo=elimina_tildes(detalleretirado.motivo)
                                    retiradofecha=str(detalleretirado.fecha)

                                if absento or retirado:
                                    # print(matri)
                                    ws.write(fila,0,(identificacion),subtitulo3)
                                    ws.write(fila,1,(nombrecompleto),subtitulo3)
                                    ws.write(fila,2,convencional,subtitulo3)
                                    ws.write(fila,3,celular,subtitulo3)
                                    ws.write(fila,4,correo2,subtitulo3)
                                    ws.write(fila,5,correo1,subtitulo3)
                                    ws.write(fila,6,carrera,subtitulo3)
                                    ws.write(fila,7,nivel,subtitulo3)
                                    ws.write(fila,8,grupo,subtitulo3)
                                    ws.write(fila,9,esabsento,subtitulo3)
                                    ws.write(fila,10,absentomotivo,subtitulo3)
                                    ws.write(fila,11,absentofecha,subtitulo3)
                                    ws.write(fila,12,esretirado,subtitulo3)
                                    ws.write(fila,13,retiradomotivo,subtitulo3)
                                    ws.write(fila,14,retiradofecha,subtitulo3)

                                    fila=fila+1
                            except:
                                print((identificacion))
                                pass

                    detalle = detalle + fila
                    ws.write(detalle,0, "Fecha Impresion", subtitulo)
                    ws.write(detalle,1, str(datetime.now()), subtitulo)
                    detalle=detalle+2
                    ws.write(fila+5,0, "Usuario", subtitulo)
                    ws.write(fila+6,1, str(request.user), subtitulo)

                except Exception as ex:
                    print(str(ex))
                    pass
                nombre ='absentosyretirados'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

        else:
            data = {'title': 'Absentos y Retirados por Facultad'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform']=AbsentosyRetiradosExcelForm()
                return render(request ,"reportesexcel/absentosyretirados_poranio.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

