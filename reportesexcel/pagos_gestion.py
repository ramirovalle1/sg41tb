from datetime import datetime,timedelta
import json
import xlrd
import xlwt
import locale
import os
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
from settings import MEDIA_ROOT, GESTION_INDIVIDUAL, GESTION_DESCUENTO
from sga.commonviews import addUserData
from sga.forms import RangoReferidoForm
from sga.models import RubroSeguimiento, convertir_fecha, TituloInstitucion, Persona, elimina_tildes, ReporteExcel, DescuentoSeguimiento, Pago, IndicadorComisionGestores, AsistAsuntoEstudiant, NivelTutor, Matricula, RegistroSeguimiento, Coordinacion


@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action =='generarexcel':
                try:
                    desde = request.POST['desde']
                    hasta = request.POST['hasta']
                    fechai = convertir_fecha(desde)
                    fechaf = convertir_fecha(hasta)

                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('Registros',cell_overwrite_ok=True)

                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,17, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,17, 'Valores a Pagar - Gestion por Rango de Fechas',titulo2)
                    ws.write(4, 0,'Desde:   ' +str(fechai.date()), subtitulo)
                    ws.write(5, 0,'Hasta:   ' +str(fechaf.date()), subtitulo)
                    fila = 6

                    ws.write(fila, 0,"Gestor",titulo)
                    ws.write(fila, 1,"Estudiante",titulo)
                    ws.write(fila, 2,"Cedula",titulo)
                    ws.write(fila, 3,"Celular",titulo)
                    ws.write(fila, 4,"Convencional",titulo)
                    ws.write(fila, 5,"Correo",titulo)
                    ws.write(fila, 6,'Rubro', subtitulo)
                    ws.write(fila, 7,'Valor Gestionado', subtitulo)
                    ws.write(fila, 8,'Categoria', subtitulo)
                    ws.write(fila, 9,'Factor', subtitulo)
                    ws.write(fila, 10,'% Descuento', subtitulo)
                    ws.write(fila, 11,'Fecha Gestion', subtitulo)
                    ws.write(fila, 12,'Fecha Pago', subtitulo)
                    ws.write(fila, 13,'Aplico Descuento', subtitulo)
                    ws.write(fila, 14,'Valor Descuento', subtitulo)
                    ws.write(fila, 15,'Total Recaudado', subtitulo)
                    ws.write(fila, 16,'% Comision', subtitulo)
                    ws.write(fila, 17,'Valor Cobrado', subtitulo)
                    ws.write(fila, 18,'Pago x Factor', subtitulo)
                    ws.write(fila, 19,'Comision', subtitulo)
                    ws.write(fila, 20,'Grupo', subtitulo)
                    ws.write(fila, 21,'Nivel', subtitulo)
                    ws.write(fila, 22,'Dias Vencidos', subtitulo)
                    ws.write(fila, 23,'Carrera', subtitulo)
                    ws.write(fila, 24,'Facultad', subtitulo)
                    fila = fila + 1

                    gestores = AsistAsuntoEstudiant.objects.filter(estado=True).order_by('asistente__apellido1')

                    for g in gestores:
                        valor_factor_total = 0
                        rubros_seguimiento = RubroSeguimiento.objects.filter(fechapago__gte=fechai, fechapago__lte=fechaf, seguimiento__usuario=g.asistente.usuario, rubro__cancelado=True, estado=True).exclude(fechapago=None).order_by('rubro__inscripcion__persona__apellido1','rubro__inscripcion__persona__apellido2','fechapago')
                        suma = rubros_seguimiento.aggregate(Sum('valorgestionado'))['valorgestionado__sum']
                        suma_desc = rubros_seguimiento.aggregate(Sum('valordesc'))['valordesc__sum']
                        if rubros_seguimiento.exists():
                            comision_total = g.valor_comision_xfecha(fechai,fechaf)
                            if IndicadorComisionGestores.objects.filter(mayor__lt=suma, menorigual__gte=suma, fechahasta__gte=fechaf, fechadesde__lte=fechai, orden=1).exists():
                                indicador = IndicadorComisionGestores.objects.filter(mayor__lt=suma, menorigual__gte=suma, fechahasta__gte=fechaf, fechadesde__lte=fechai, orden=1)[:1].get()
                            else:
                                suma = suma - suma_desc
                                indicador = IndicadorComisionGestores.objects.filter(mayor__lt=suma, menorigual__gte=suma, fechahasta__gte=fechaf, fechadesde__lte=fechai)[:1].get()

                            for rs in rubros_seguimiento:
                                ws.write(fila,0, elimina_tildes(g.asistente.nombre_completo_inverso()))
                                ws.write(fila,1, elimina_tildes(rs.seguimiento.inscripcion.persona.nombre_completo_inverso()))
                                ws.write(fila,2, elimina_tildes(rs.seguimiento.inscripcion.persona.cedula if rs.seguimiento.inscripcion.persona.cedula else rs.seguimiento.inscripcion.persona.pasaporte))
                                ws.write(fila,3, elimina_tildes(rs.seguimiento.inscripcion.persona.telefono if rs.seguimiento.inscripcion.persona.telefono else ""))
                                ws.write(fila,4, rs.seguimiento.inscripcion.persona.telefono_conv if rs.seguimiento.inscripcion.persona.telefono_conv else "")
                                ws.write(fila,5, elimina_tildes(rs.seguimiento.inscripcion.persona.emailinst))

                                ws.write(fila,6, elimina_tildes(rs.rubro.nombre()))
                                ws.write(fila,7, rs.valorgestionado)
                                ws.write(fila,8, elimina_tildes(rs.categoria.categoria))
                                ws.write(fila,9, elimina_tildes(rs.categoria.factor))
                                ws.write(fila,10, rs.categoria.porcentaje)
                                ws.write(fila,11, elimina_tildes(rs.seguimiento.fecha))
                                ws.write(fila,12, elimina_tildes(rs.fechapago))
                                if rs.valordesc > 0:
                                    ws.write(fila,13,"SI")
                                else:
                                    ws.write(fila,13,"NO")
                                ws.write(fila,14, rs.valordesc)
                                ws.write(fila,15, suma)
                                ws.write(fila,16, str(indicador.porcentajecomision)+'%')
                                if ((rs.aplicadescuentocategoria or rs.aprobardescuentoadd) and indicador.orden != 1):
                                    pagoxfactor = float(rs.valorgestionado-rs.valordesc)*float(rs.categoria.factor)
                                else:
                                    pagoxfactor = float(rs.valorgestionado)*float(rs.categoria.factor)
                                valor_factor_total = float(valor_factor_total) + pagoxfactor
                                ws.write(fila,17, rs.valorgestionado-rs.valordesc)
                                ws.write(fila,18, pagoxfactor)
                                valorx_factor = round(float(rs.valorgestionado-rs.valordesc),2)*round(float(rs.categoria.factor),2)
                                comision = round(valorx_factor,2)*round(float(indicador.porcentajecomision),2)/100
                                ws.write(fila,19, comision)
                                dias_vencidos = (rs.fechapago - rs.rubro.fechavence).days
                                ws.write(fila,22, dias_vencidos)
                                ws.write(fila,21, elimina_tildes(rs.rubro.inscripcion.carrera.nombre))
                                coordinacion = Coordinacion.objects.filter(carrera=rs.rubro.inscripcion.carrera)[:1].get()
                                ws.write(fila,24, elimina_tildes(coordinacion.nombre))

                                # nivel = rs.seguimiento.inscripcion.ultima_matricula()
                                if Matricula.objects.filter(inscripcion=rs.seguimiento.inscripcion).exists():
                                    matricula = Matricula.objects.filter(inscripcion=rs.seguimiento.inscripcion).order_by('-id')[:1].get()
                                    ws.write(fila,20, elimina_tildes(matricula.nivel.paralelo))
                                    ws.write(fila,21, elimina_tildes(matricula.nivel.nivelmalla.nombre))

                                fila = fila + 1
                            ws.write(fila,19, comision_total, titulo)
                            fila += 2

                            # ws.write(fila,12, valor_factor_total) #total de valor gestion x factor(por cada seguimiento rubro)
                            # ws.write(fila,13, 'COMISION:',subtitulo) #total de valor gestion x factor(por cada seguimiento rubro)
                            # comision = valor_factor_total*float(porcentaje_comision)/100
                            # ws.write(fila,14, comision)

                            # fila= fila +1


                    detalle = 2 + fila
                    ws.write(detalle, 0, "Fecha Impresion", subtitulo)
                    ws.write(detalle, 2, str(datetime.now()), subtitulo)
                    detalle=detalle +1
                    ws.write(detalle, 0, "Usuario", subtitulo)
                    ws.write(detalle, 2, str(request.user), subtitulo)

                    nombre ='pagosgestion'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")


        else:
            data = {'title': 'Gestion Carrera'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform']=RangoReferidoForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
                return render(request ,"reportesexcel/pagos_gestion.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

