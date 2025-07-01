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
from settings import UTILIZA_GRUPOS_ALUMNOS, EMAIL_ACTIVE,MEDIA_ROOT, ASIG_VINCULACION, ASIG_PRATICA,NOTA_PARA_APROBAR,ASIST_PARA_APROBAR
from sga.commonviews import addUserData, ip_client_address
from sga.forms import RangoFacturasForm,RangoNCForm, VinculacionExcelForm, GestionExcelForm
from sga.models import Inscripcion,convertir_fecha,Factura,TituloInstitucion,ReporteExcel,Nivel,Grupo,InscripcionPracticas,EstudianteVinculacion, \
     Provincia, Canton

from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action :
                try:
                    m = 5
                    # grupo = Grupo.objects.filter(pk=request.POST['grupo'])[:1].get()
                    nivel = Nivel.objects.filter(pk=request.POST['nivel'])[:1].get()
                    #nivel = Nivel.objects.filter(pk=5963)[:1].get()
                    # nivel = Nivel.objects.filter(grupo=grupo).order_by('-id')[:1].get()
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo1 = xlwt.easyxf('font: bold on,colour green, bold on; align: wrap on, vert centre, horiz center')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo4 = xlwt.easyxf('font: name Times New Roman;align: wrap on, vert centre, horiz center')
                    subtitulo3 = xlwt.easyxf('font: name Times New Roman,colour black, bold on; align: wrap on, vert centre, horiz center')
                    subtitulo.font.height = 20*10
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('Registros',cell_overwrite_ok=True)
                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,3,m+8, tit.nombre , titulo2)
                    ws.write_merge(1, 1,3,m+8, 'PRACTICAS Y VINCULACION DE ESTUDIANTES POR GRUPO',titulo2)
                    ws.write(3, 0,'CARRERA: ' +nivel.carrera.nombre , subtitulo)
                    ws.write(4, 0,'GRUPO:   ' +nivel.grupo.nombre+' '+nivel.nivelmalla.nombre, subtitulo)

                    ws.write(7, 0,'IDENTIFICACION', subtitulo)
                    ws.write(7, 1,'APELLIDOS Y NOMBRES', subtitulo)
                    ws.write(7, 6,'CONVENCIONAL', subtitulo)
                    ws.write(7, 7,'CELULAR', subtitulo)
                    ws.write(7, 8,'DIRECCION', subtitulo)
                    ws.write(7, 9,'EMAIL INSTITUCIONAL', subtitulo)
                    ws.write(7, 10,'EMAIL PERSONAL', subtitulo)
                    ws.write(7, 11,'PROVINCIA NACIMIENTO', subtitulo)
                    ws.write(7, 12,'CANTON NACIMIENTO', subtitulo)
                    ws.write(7, 13,'FECHA NACIMIENTO', subtitulo)
                    ws.write(7, 14,'PROVINCIA RESIDENCIA', subtitulo)
                    ws.write(7, 15,'CANTON RESIDENCIA', subtitulo)
                    # ws.write_merge(6,6,11,15,'PRACTICAS',titulo1)
                    ws.write(7, 16,'HORAS PRACTICA', subtitulo)
                    # ws.write(7, 12,'DESDE', subtitulo)
                    # ws.write(7, 13,'HASTA', subtitulo)
                    # ws.write(7, 14,'HORAS', subtitulo)
                    # ws.write(7, 15,'NIVEL PRACTICA', subtitulo)
                    # ws.write_merge(6,6,16,20,'VINCULACION',titulo1)
                    # ws.write(7, 16,'TUTOR VINCULACION', subtitulo)
                    # ws.write(7, 17,'DESDE', subtitulo)
                    # ws.write(7, 18,'HASTA', subtitulo)
                    ws.write(7, 17,'HORAS VINCULACION', subtitulo)
                    ws.write(7, 18,'TOTAL GENERAL', subtitulo)

                    fila = 8
                    com = 9
                    detalle = 3
                    c=0
                    columna=0
                    estudiante=''
                    if nivel.matriculados()==None:
                        detalle = detalle + fila
                        ws.write(detalle, 1, "Fecha Impresion", subtitulo)
                        ws.write(detalle, 2, str(datetime.now()), subtitulo)
                        ws.write(detalle+1, 1, "Usuario", subtitulo)
                        ws.write(detalle+1, 2, str(request.user), subtitulo)

                        nombre ='practicas_vinculacion_xgrupo'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                        wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                        return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")
                    for matri in nivel.matriculados():
                        total_horas=0
                        estudiante=matri.inscripcion
                        # print(matri.inscripcion.id)
                        telefono1=''
                        telefono2=''
                        cedula=''
                        pasaporte=''
                        tiposangre=''
                        provincianacimiento=''
                        cantonnacimiento=''
                        provincia=''
                        canton=''
                        fechanacimiento=''
                        if matri.inscripcion.persona.cedula:
                            identificacion=matri.inscripcion.persona.cedula
                        else:
                            identificacion=matri.inscripcion.persona.pasaporte

                        if matri.inscripcion.persona.provincia:
                            provincianacimiento= Provincia.objects.get(id=matri.inscripcion.persona.provincia.id)
                        else:
                            provincianacimiento=''

                        if matri.inscripcion.persona.canton:
                            cantonnacimiento= Canton.objects.get(id=matri.inscripcion.persona.canton.id)
                        else:
                            cantonnacimiento=''

                        if matri.inscripcion.persona.nacimiento:
                            fechanacimiento= str(matri.inscripcion.persona.nacimiento)
                        else:
                            fechanacimiento=''

                        if matri.inscripcion.persona.cantonresid:
                            canton= Canton.objects.get(id=matri.inscripcion.persona.cantonresid.id)
                        else:
                            canton=''

                        if matri.inscripcion.persona.provinciaresid:
                            provincia= Provincia.objects.get(id=matri.inscripcion.persona.provinciaresid.id)
                        else:
                            provincia=''

                        ws.write(fila,columna,str(elimina_tildes(identificacion)))
                        ws.write_merge(fila,fila,columna+1,columna+5,elimina_tildes(matri.inscripcion.persona.nombre_completo_inverso()))
                        ws.write(fila,columna+5,str(elimina_tildes(matri.inscripcion.sesion.nombre)))

                        if matri.inscripcion.persona.telefono_conv:
                            telefono1=matri.inscripcion.persona.telefono_conv

                        if matri.inscripcion.persona.telefono:
                            telefono2=matri.inscripcion.persona.telefono

                        ws.write(fila,columna+6,str(elimina_tildes(telefono1)))
                        try:
                            ws.write(fila,columna+7,str(elimina_tildes(telefono2)))
                        except:
                            ws.write(fila,columna+7,str('Error en celular'))

                        try:
                            ws.write(fila,columna+8,str(elimina_tildes(matri.inscripcion.persona.direccion)))
                        except:
                            ws.write(fila,columna+8,str('Error en Direccion'))

                        try:
                            ws.write(fila,columna+9,str(elimina_tildes(matri.inscripcion.persona.emailinst)))
                        except:
                            ws.write(fila,columna+9,str('Error en correo institucional'))
                        try:
                            ws.write(fila,columna+10,str(elimina_tildes(matri.inscripcion.persona.email)))
                        except:
                            ws.write(fila,columna+10,str('Error en correo personal'))

                        ws.write(fila,columna+11,elimina_tildes(provincianacimiento))
                        ws.write(fila,columna+12,elimina_tildes(cantonnacimiento))
                        ws.write(fila,columna+13,elimina_tildes(fechanacimiento))
                        ws.write(fila,columna+14,elimina_tildes(provincia))
                        ws.write(fila,columna+15,elimina_tildes(canton))
                        if InscripcionPracticas.objects.filter(inscripcion=matri.inscripcion).exists():
                            fila2=fila
                            t_horas_practica=0
                            t_horas_practica = InscripcionPracticas.objects.filter(inscripcion=matri.inscripcion).aggregate(Sum('horas'))['horas__sum']
                            # for pract in InscripcionPracticas.objects.filter(inscripcion=matri.inscripcion).order_by('inicio'):
                            #     pract_tutor=''
                            #     pract_desde=''
                            #     pract_hasta=''
                            #     pract_horas=''
                            #     pract_nivel=''
                            #
                            #     pract_tutor=pract.profesor.persona.nombre_completo_inverso()
                            #     pract_desde=pract.inicio
                            #     pract_hasta=pract.fin
                            #     pract_horas=pract.horas
                            #     t_horas_practica=t_horas_practica+pract_horas
                            #     if pract.nivelmalla:
                            #         pract_nivel=pract.nivelmalla.nombre
                            #     else:
                            #         pract_nivel=''
                            #
                            #     ws.write(fila2,columna+11,elimina_tildes(pract_tutor))
                            #     ws.write(fila2,columna+12,str(pract_desde))
                            #     ws.write(fila2,columna+13,str(pract_hasta))
                            #     ws.write(fila2,columna+14,str(pract_horas))
                            #     ws.write(fila2,columna+15,str(pract_nivel))
                            total_horas=total_horas+t_horas_practica
                                # fila2=fila2+1
                            # ws.write(fila2,columna+12,'TOTAL H PRACTICAS',subtitulo)
                            ws.write(fila2,columna+16,t_horas_practica,subtitulo)
                        else:
                            fila2=fila
                            pract_tutor=0
                            ws.write(fila2,columna+16,pract_tutor)

                        if EstudianteVinculacion.objects.filter(inscripcion=matri.inscripcion).exists():
                            fila3=fila
                            t_horas_vincula=0
                            t_horas_vincula = EstudianteVinculacion.objects.filter(inscripcion=matri.inscripcion).aggregate(Sum('horas'))['horas__sum']
                            # for vincula in EstudianteVinculacion.objects.filter(inscripcion=matri.inscripcion).order_by('actividad__inicio'):
                            #     vincula_tutor=''
                            #     vincula_desde=''
                            #     vincula_hasta=''
                            #     vincula_horas=''
                            #     vincula_nivel=''
                            #
                            #     vincula_tutor=vincula.actividad.lider
                            #     vincula_desde=vincula.actividad.inicio
                            #     vincula_hasta=vincula.actividad.fin
                            #     vincula_horas=vincula.horas
                            #     t_horas_vincula=t_horas_vincula+vincula_horas
                            #     if vincula.nivelmalla:
                            #         vincula_nivel=vincula.nivelmalla.nombre
                            #     else:
                            #         vincula_nivel=''
                            #
                            #     ws.write(fila3,columna+16,elimina_tildes(vincula_tutor))
                            #     ws.write(fila3,columna+17,str(vincula_desde))
                            #     ws.write(fila3,columna+18,str(vincula_hasta))
                            #     ws.write(fila3,columna+19,str(vincula_horas))
                            #     ws.write(fila3,columna+20,str(vincula_nivel))
                            total_horas=total_horas+t_horas_vincula
                            #     fila3=fila3+1
                            # ws.write(fila3,columna+17,'TOTAL H VINCULACION',subtitulo)
                            ws.write(fila3,columna+17,t_horas_vincula,subtitulo)
                        else:
                            fila3=fila
                            vincula_tutor=0
                            ws.write(fila3,columna+17,vincula_tutor)

                        com=fila+1
                        # if fila2<fila3:
                        #     fila = fila3 + 1
                        # else:
                        #     fila = fila2 + 1

                        # ws.write_merge(fila,fila,columna+6,columna+10,'TOTAL HORAS PRACTICAS PRE PROFESIONALES',subtitulo)
                        ws.write(fila,columna+18,total_horas,subtitulo)
                        fila = fila + 1
                    detalle = detalle + fila

                    ws.write(detalle, 1, "Fecha Impresion", subtitulo)
                    ws.write(detalle, 2, str(datetime.now()), subtitulo)
                    ws.write(detalle+1, 1, "Usuario", subtitulo)
                    ws.write(detalle+1, 2, str(request.user), subtitulo)

                    nombre ='practicas_vinculacion_xgrupo'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")

        else:
            data = {'title': 'Practicas y Vinculacion de Estudiantes por Grupo'}
            addUserData(request,data)
            # if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
            reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
            data['reportes'] = reportes
            return render(request ,"reportesexcel/xgrupo_practicas_vinculacion.html" ,  data)
        return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))


