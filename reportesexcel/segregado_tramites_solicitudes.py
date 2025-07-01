from datetime import datetime,timedelta,time
from decimal import Decimal
import json
import xlwt
from django.db.models.query_utils import Q
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from settings import MEDIA_ROOT
from sga.commonviews import addUserData
from sga.forms import RangoFacturasForm
from sga.models import convertir_fecha,TituloInstitucion,ReporteExcel, RubroEspecieValorada,Matricula,AsistenteDepartamento,\
     Coordinacion,SeguimientoEspecie,SolicitudSecretariaDocente,IncidenciaAsignada,Inscripcion,Departamento,GestionTramite,\
     Persona
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
                    ws = wb.add_sheet('segregado',cell_overwrite_ok=True)

                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,m+7, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,m+7, 'Segregado de Gestion de Tiempos en Solicitudes y Tramites', titulo2)
                    ws.write(3, 0, 'DESDE', titulo)
                    ws.write(3, 1, str((fechai.date())), titulo)
                    ws.write(4, 0, 'HASTA:', titulo)
                    ws.write(4, 1, str((fechaf.date())), titulo)
                    ws.write(6, 0,  'DIA', titulo)
                    ws.write(6, 1,  'MES', titulo)
                    ws.write(6, 2,  'ANIO', titulo)
                    ws.write(6, 3,  'HORA', titulo)
                    ws.write(6, 4, '# DE TRAMITE', titulo)
                    ws.write(6, 5, 'REQUERIMIENTO', titulo)
                    ws.write(6, 6, 'TIEMPO DE GESTION/ESPERA', titulo)
                    ws.write(6, 7, 'USUARIO TRAMITE', titulo)
                    ws.write(6, 8, 'RESPONSABLE', titulo)
                    ws.write(6, 9, 'DEPARTAMENTO', titulo)
                    ws.write(6, 10, 'ESTUDIANTE', titulo)
                    ws.write(6, 11, 'CEDULA', titulo)

                    cabecera = 1
                    columna = 0
                    tot =0
                    detalle = 6
                    anterior = 0
                    actual = 0
                    fila = 7
                    identificacion=''
                    hoy=datetime.now()
                    #Tramites
                    for re in  RubroEspecieValorada.objects.filter(rubro__fecha__gte=fechai,rubro__fecha__lte=fechaf).order_by('rubro__fecha','serie'):
                    #for re in  RubroEspecieValorada.objects.filter(pk=433105,rubro__fecha__gte=fechai,rubro__fecha__lte=fechaf).order_by('rubro__fecha','serie'):
                        if re.es_online():
                            dia=''
                            mes=''
                            horas=''
                            hora=''
                            minutos=''
                            identificacion=''
                            fechaaux2=datetime.combine(fechaf,time(23,59,0,1))
                            horas_gestion=0
                            if re.rubro.cancelado:
                                if re.aplicada:
                                    estadotramite='FINALIZADA'
                                else:
                                    if re.autorizado:
                                        estadotramite='EN PROCESO'
                                    else:
                                        if  re.usrautoriza:
                                            estadotramite='NO APROBADA'
                                        else:
                                            estadotramite='EN PROCESO'
                                print(re.id)
                                #print(re.rubro.fecha)
                                #fila = fila +1
                                if re.rubro.fecha.day<10:
                                    dia=str('0'+str(re.rubro.fecha.day))
                                else:
                                    dia=str(re.rubro.fecha.day)
                                if re.rubro.fecha.month<10:
                                    mes=str('0'+str(re.rubro.fecha.month))
                                else:
                                    mes=str(re.rubro.fecha.month)
                            for seg in SeguimientoEspecie.objects.filter(Q(observacion='REASIGNACION DE DEPARTAMENTO',rubroespecie=re)|Q(observacion='REASIGNACION DE USUARIO',rubroespecie=re)):
                                horas_totales=0
                                if seg.fechaasig and seg.fecha and seg.fechaasig!=None:
                                    fechacierre = datetime.combine(seg.fecha, seg.hora)
                                    dias_espera = (fechacierre-seg.fechaasig).days
                                    h_espera=(dias_espera*24)
                                    segundos_espera = (fechacierre-seg.fechaasig).seconds
                                    h_espera2= Decimal(Decimal(segundos_espera).quantize(Decimal(10)**-2)/Decimal(3600).quantize(Decimal(10)**-2)).quantize(Decimal(10)**-2)
                                    horas_totales=h_espera+h_espera2

                                    ws.write(fila,0,dia)
                                    ws.write(fila,1,mes)
                                    ws.write(fila,2,str(re.rubro.fecha.year))
                                    if re.es_online():
                                        if re.es_online().fecha.hour<10:
                                            hora=str('0'+str(re.es_online().fecha.hour))
                                        else:
                                            hora=str(re.es_online().fecha.hour)
                                        if re.es_online().fecha.minute<10:
                                            minutos=str('0'+ str(re.es_online().fecha.minute))
                                        else:
                                            minutos=str(re.es_online().fecha.minute)
                                        horas=hora+':'+minutos
                                        ws.write(fila,3 ,horas)
                                    else:
                                        ws.write(fila,3 ,'')
                                    ws.write(fila,4 ,re.serie)
                                    ws.write(fila,5 ,'TRAMITE')
                                    ws.write(fila,6,horas_totales)
                                    ws.write(fila,7,str(seg.asistente))
                                    if seg.asistente:
                                        asistente=Persona.objects.filter(usuario=seg.asistente)[:1].get()
                                        if seg.asistentedepartamento:
                                            asistentedpto=AsistenteDepartamento.objects.filter(pk=seg.asistentedepartamento.id)[:1].get()
                                            ws.write(fila,8,elimina_tildes(asistentedpto.persona.nombre_completo_inverso()))
                                            ws.write(fila,9,elimina_tildes(asistentedpto.departamento.descripcion))
                                        else:
                                            ws.write(fila,8,elimina_tildes(asistente.nombre_completo_inverso()))
                                            ws.write(fila,9,elimina_tildes('NO TIENE DEPARTAMENTO'))
                                    else:
                                        asistente=Persona.objects.filter(usuario=seg.usuario)[:1].get()
                                        if AsistenteDepartamento.objects.filter(persona=asistente.id).exists():
                                            asistentedpto=AsistenteDepartamento.objects.filter(persona=asistente.id)[:1].get()
                                            ws.write(fila,8,elimina_tildes(asistentedpto.persona.nombre_completo_inverso()))
                                            ws.write(fila,9,elimina_tildes(asistentedpto.departamento.descripcion))
                                        else:
                                            ws.write(fila,8,elimina_tildes(asistente.nombre_completo_inverso()))
                                            ws.write(fila,9,elimina_tildes('NO TIENE DEPARTAMENTO'))
                                    ws.write(fila,10,elimina_tildes(re.rubro.inscripcion.persona.nombre_completo_inverso()))
                                    if re.rubro.inscripcion.persona.cedula:
                                        identificacion=elimina_tildes(re.rubro.inscripcion.persona.cedula)
                                    else:
                                        identificacion=elimina_tildes(re.rubro.inscripcion.persona.pasaporte)
                                    ws.write(fila,11,str(identificacion))
                                    fila = fila +1

                    #fila = fila +1
                    #Solicitudes
                    for sol in  SolicitudSecretariaDocente.objects.filter(fecha__gte=fechai,fecha__lte=fechaf).order_by('fecha').exclude(solicitudestudiante=None):
                    #for sol in  SolicitudSecretariaDocente.objects.filter(pk=20582,fecha__gte=fechai,fecha__lte=fechaf).order_by('fecha').exclude(solicitudestudiante=None):
                        horas_totales=0
                        identificacion=''
                        if sol.cerrada:
                            estadotramite='FINALIZADO'
                        else:
                            estadotramite='EN PROCESO'
                        #print(sol.id)
                        #print(estadotramite)
                        #fila = fila +1
                        if sol.fecha.day<10:
                            dia=str('0'+str(sol.fecha.day))
                        else:
                            dia=str(sol.fecha.day)
                        if sol.fecha.month<10:
                            mes=str('0'+str(sol.fecha.month))
                        else:
                            mes=str(sol.fecha.month)

                        if sol.fechacierre and sol.fechaasignacion:
                            fechacierre = datetime.combine(sol.fechacierre,sol.hora)
                            dias_espera = (fechacierre-sol.fechaasignacion).days
                            h_espera=(dias_espera*24)
                            segundos_espera = (fechacierre-sol.fechaasignacion).seconds
                            h_espera2 = int(segundos_espera/3600)
                            horas_totales=h_espera+h_espera2
                        horas_totalesseg=0
                        for inci in IncidenciaAsignada.objects.filter(Q(solicitusecret=sol,observacion='CAMBIO DE DEPARTAMENTO' )|Q(solicitusecret=sol,observacion='REASIGNACION DE USUARIO' )):
                            if inci.fechaasig and inci.fecha:
                                dias_esperaseg = (inci.fecha-inci.fechaasig).days
                                h_esperaseg=(dias_esperaseg*24)
                                segundos_esperaseg = (inci.fecha-inci.fechaasig).seconds
                                h_espera2seg = int(segundos_esperaseg/3600)
                                horas_totalesseg =h_esperaseg +h_espera2seg
                                ws.write(fila,0,dia)
                                ws.write(fila,1,mes)
                                ws.write(fila,2,str(sol.fecha.year))
                            if sol.fechaasignacion:
                                if sol.fechaasignacion.hour<10:
                                    hora=str('0'+str(sol.fechaasignacion.hour))
                                else:
                                    hora=str(sol.fechaasignacion.hour)
                                if sol.fechaasignacion.minute<10:
                                    minutos=str('0'+ str(sol.fechaasignacion.minute))
                                else:
                                    minutos=str(sol.fechaasignacion.minute)
                                horas=hora+':'+minutos
                            else:
                                horas='NO TIENE ASIGNACION'
                            ws.write(fila,0,dia)
                            ws.write(fila,1,mes)
                            ws.write(fila,2,str(sol.fecha.year))
                            ws.write(fila,3,horas)
                            ws.write(fila,4 ,sol.id)
                            ws.write(fila,5 ,'SOLICITUD')
                            ws.write(fila,6,horas_totalesseg)
                            try:
                                if inci.asistenteasig:
                                    ws.write(fila,7,str(inci.asistenteasig))
                                    asistente=Persona.objects.filter(usuario=inci.asistenteasig)[:1].get()
                                    if inci.asistentedepartamento:
                                        asistentedpto=AsistenteDepartamento.objects.filter(pk=inci.asistentedepartamento.id)[:1].get()
                                        ws.write(fila,8,elimina_tildes(asistentedpto.persona.nombre_completo_inverso()))
                                        ws.write(fila,9,elimina_tildes(asistentedpto.departamento.descripcion))
                                    else:
                                        ws.write(fila,8,elimina_tildes(asistente.nombre_completo_inverso()))
                                        ws.write(fila,9,elimina_tildes('NO TIENE DEPARTAMENTO'))
                                else:
                                    asistente=Persona.objects.filter(usuario=inci.usuario)[:1].get()
                                    ws.write(fila,7,str(inci.usuario))
                                    if AsistenteDepartamento.objects.filter(persona=asistente.id).exists():
                                        asistentedpto=AsistenteDepartamento.objects.filter(persona=asistente.id)[:1].get()
                                        ws.write(fila,8,elimina_tildes(asistentedpto.persona.nombre_completo_inverso()))
                                        ws.write(fila,9,elimina_tildes(asistentedpto.departamento.descripcion))
                                    else:
                                        ws.write(fila,8,elimina_tildes(asistente.nombre_completo_inverso()))
                                        ws.write(fila,9,elimina_tildes('NO TIENE DEPARTAMENTO'))
                                ws.write(fila,10,elimina_tildes(sol.persona.nombre_completo_inverso()))
                                if sol.persona.cedula:
                                    identificacion=elimina_tildes(sol.persona.cedula)
                                else:
                                    identificacion=elimina_tildes(sol.persona.pasaporte)
                                ws.write(fila,11,str(identificacion))
                            except:
                                asistente=Persona.objects.filter(usuario=inci.usuario)[:1].get()
                                ws.write(fila,7,str(inci.usuario))
                                if AsistenteDepartamento.objects.filter(persona=asistente.id).exists():
                                    asistentedpto=AsistenteDepartamento.objects.filter(persona=asistente.id)[:1].get()
                                    ws.write(fila,8,elimina_tildes(asistentedpto.persona.nombre_completo_inverso()))
                                    ws.write(fila,9,elimina_tildes(asistentedpto.departamento.descripcion))
                                else:
                                    ws.write(fila,8,elimina_tildes(asistente.nombre_completo_inverso()))
                                    ws.write(fila,9,elimina_tildes('NO TIENE DEPARTAMENTO'))
                                ws.write(fila,10,elimina_tildes(sol.persona.nombre_completo_inverso()))
                                if sol.persona.cedula:
                                    identificacion=elimina_tildes(sol.persona.cedula)
                                else:
                                    identificacion=elimina_tildes(sol.persona.pasaporte)
                                ws.write(fila,11,str(identificacion))
                            fila = fila +1

                    detalle = detalle + fila
                    ws.write(detalle, 0, "Fecha Impresion", subtitulo)
                    ws.write(detalle, 2, str(datetime.now()), subtitulo)
                    detalle=detalle +1
                    ws.write(detalle, 0, "Usuario", subtitulo)
                    ws.write(detalle, 2, str(request.user), subtitulo)

                    nombre ='segregado'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex) + " ")
                    #return HttpResponse(json.dumps({"result":str(re.id) }),content_type="application/json")
                    return HttpResponse(json.dumps({"result":str(sol.id) }),content_type="application/json")
        else:
            data = {'title': 'Listado de Gestion de Tiempos Segregado en Solicitudes y Tramites'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform']=RangoFacturasForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
            return render(request ,"reportesexcel/segregado_tramites_solicitudes.html" ,  data)
        return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

