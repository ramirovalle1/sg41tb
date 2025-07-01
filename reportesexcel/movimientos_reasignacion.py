from datetime import datetime,timedelta
from decimal import Decimal
import json
import xlwt

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from settings import MEDIA_ROOT
from sga.commonviews import addUserData
from sga.forms import RangoFacturasForm
from sga.models import convertir_fecha,TituloInstitucion,ReporteExcel,Matricula,AsistenteDepartamento,SeguimientoEspecie,Departamento
from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action :
                inicio = request.POST['inicio']
                fin = request.POST['fin']
                try:
                    fechai = convertir_fecha(inicio)
                    fechaf = convertir_fecha(fin)
                    m = 5
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10
                    style1 = xlwt.easyxf('',num_format_str='DD-MMM-YY')
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('gestiontiempo',cell_overwrite_ok=True)

                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,m+2, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,m+2, 'Listado de Movimientos Reasignacion', titulo2)
                    ws.write(3, 0, 'DESDE', titulo)
                    ws.write(3, 1, str((fechai.date())), titulo)
                    ws.write(4, 0, 'HASTA:', titulo)
                    ws.write(4, 1, str((fechaf.date())), titulo)
                    ws.write(6, 0, 'Persona/Usuario Reasigna', titulo)
                    ws.write(6, 1, 'Dpto Usuario', titulo)
                    ws.write(6, 2, 'Fecha reasignacion', titulo)
                    ws.write(6, 3, 'Hora', titulo)
                    ws.write(6, 4, 'Dpto reasignado', titulo)
                    ws.write(6, 5, 'Serie#', titulo)
                    ws.write(6, 6, 'Tipo de Tramite', titulo)
                    ws.write(6, 7, 'ESTADO DEL TRAMITE', titulo)
                    cabecera = 1
                    columna = 0
                    tot =0
                    detalle = 6
                    fila = 6
                    se=''
                    for dpto in Departamento.objects.filter(controlespecies=True).order_by('descripcion').exclude(id=27):
                        for asistente in AsistenteDepartamento.objects.filter(departamento=dpto).order_by('persona__apellido1','persona__apellido2','persona__nombres'):
                            #print(asistente)
                            asist=asistente.persona.nombre_completo_inverso()
                            for se in  SeguimientoEspecie.objects.filter(fecha__gte=fechai,fecha__lte=fechaf,usuario=asistente.persona.usuario).order_by('usuario','fecha','rubroespecie__serie'):
                           #for se in  SeguimientoEspecie.objects.filter(fecha__gte=fechai,fecha__lte=fechaf,rubroespecie__id=429959).order_by('usuario','fecha'):
                                fila=fila+1
                                #print(se.rubroespecie.id)
                                asistente=''
                                departamento=''
                                asis=''
                                estado=''
                                if AsistenteDepartamento.objects.filter(persona__usuario=se.usuario).exists():
                                    asis =  AsistenteDepartamento.objects.filter(persona__usuario=se.usuario)[:1].get()
                                    asistente=str(elimina_tildes(asis.persona.nombre_completo_inverso()))
                                    #asistente=str(elimina_tildes(asis.persona.nombre_completo_inverso()))+' USR: '+ str(se.usuario)
                                else:
                                    asistente =  se.usuario
                                if asis:
                                    if asis.departamento:
                                        departamento=elimina_tildes(asis.departamento.descripcion)
                                    else:
                                        departamento='NO TIENE DEPARTAMENTO ASIGNADO'
                                else:
                                    departamento='NO TIENE DEPARTAMENTO ASIGNADO'
                                ws.write(fila,0,str(asistente))
                                ws.write(fila,1,str(departamento))
                                if se.rubroespecie.departamento:
                                    dpto_reasignado=elimina_tildes(se.rubroespecie.departamento.descripcion)
                                else:
                                    dpto_reasignado='NO TIENE DEPARTAMENTO REASIGNADO'
                                ws.write(fila,2,str(se.fecha))
                                if se.hora:
                                    if se.hora.hour<10:
                                        hora=str('0'+str(se.hora.hour))
                                    else:
                                        hora=str(se.hora.hour)
                                    if se.hora.minute<10:
                                        minutos=str('0'+str(se.hora.minute))
                                    else:
                                        minutos=str(se.hora.minute)
                                    if se.hora.second<10:
                                        segundos=str('0'+str(se.hora.second))
                                    else:
                                        segundos=str(se.hora.second)

                                    horafinal=hora+':'+minutos+':'+segundos
                                else:
                                    horafinal='NO TIENE HORA'

                                ws.write(fila,3,str(horafinal))
                                ws.write(fila,4,str(dpto_reasignado))
                                ws.write(fila,5,str(se.rubroespecie.serie))
                                ws.write(fila,6,elimina_tildes(se.rubroespecie.tipoespecie.nombre))
                                if se.rubroespecie.aplicada :
                                    estado='FINALIZADA'
                                else:
                                    if se.rubroespecie.autorizado:
                                        estado='EN PROCESO'
                                    else:
                                        if se.rubroespecie.usrautoriza:
                                            estado='NO APROBADA'
                                        else:
                                            estado='EN PROCESO'
                                ws.write(fila,7,str(estado))

                    detalle = detalle + fila
                    ws.write(detalle, 0, "Fecha Impresion", subtitulo)
                    ws.write(detalle, 2, str(datetime.now()), subtitulo)
                    detalle=detalle +1
                    ws.write(detalle, 0, "Usuario", subtitulo)
                    ws.write(detalle, 2, str(request.user), subtitulo)

                    nombre ='movimientos'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex) + " ")
                    return HttpResponse(json.dumps({"result":str(se.id) }),content_type="application/json")
        else:
            data = {'title': 'Listado de Movimientos de Reasignacion de Tramites'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform']=RangoFacturasForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
                return render(request ,"reportesexcel/movimientos_reasignacion.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

