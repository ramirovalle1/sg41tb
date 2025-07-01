from datetime import datetime,timedelta,time
from decimal import Decimal
import json
import xlwt

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from settings import MEDIA_ROOT
from sga.commonviews import addUserData
from sga.forms import RangoFacturasForm
from django.contrib.auth.models import User
from sga.models import convertir_fecha,TituloInstitucion,ReporteExcel, RubroEspecieValorada,Matricula,AsistenteDepartamento,\
     Coordinacion,SeguimientoEspecie,SolicitudSecretariaDocente,IncidenciaAsignada,Inscripcion,Persona,Profesor,SolicitudEstudiante
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
                    #fechai2 = convertir_fecha(inicio).date()
                    fechaf2 = convertir_fecha(fin).date()
                    m = 5
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10
                    style1 = xlwt.easyxf('',num_format_str='DD-MMM-YY')
                    wb = xlwt.Workbook()
                    anio='2020'
                    num_hoja=1
                    hoja='gestiontiempo' + ' '+anio
                    ws = wb.add_sheet(hoja,cell_overwrite_ok=True)
                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,m+17, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,m+17, 'Listado de Gestion de Tiempos en Solicitudes y Tramites', titulo2)
                    ws.write(3, 0, 'DESDE', titulo)
                    ws.write(3, 1, str((fechai.date())), titulo)
                    ws.write(4, 0, 'HASTA:', titulo)
                    ws.write(4, 1, str((fechaf.date())), titulo)
                    ws.write(6, 0,  'DIA', titulo)
                    ws.write(6, 1,  'MES', titulo)
                    ws.write(6, 2,  'ANIO', titulo)
                    ws.write(6, 3,  'HORA', titulo)
                    ws.write(6, 4,  'TIEMPO DE ESPERA', titulo)
                    ws.write(6, 5,  'TIEMPO DE GESTION', titulo)
                    ws.write(6, 6,  'ESTUDIANTE', titulo)
                    ws.write(6, 7,  'CEDULA', titulo)
                    ws.write(6, 8,  'CELULAR', titulo)
                    ws.write(6, 9,  'CONVENCIONAL', titulo)
                    ws.write(6, 10,  'CORREO PERSONAL', titulo)
                    ws.write(6, 11, 'CORREO INSTITUCIONAL', titulo)
                    ws.write(6, 12, 'GRUPO', titulo)
                    ws.write(6, 13, 'CARRERA', titulo)
                    ws.write(6, 14, 'FACULTAD', titulo)
                    ws.write(6, 15, '# DE TRAMITE', titulo)
                    ws.write(6, 16, 'REQUERIMIENTO', titulo)
                    ws.write(6, 17, 'DETALLE REQ/SOLIC.', titulo)
                    ws.write(6, 18, 'TIPO DE REQUERIMIENTO', titulo)
                    ws.write(6, 19, 'RESPONSABLE', titulo)
                    ws.write(6, 20, 'CENTRO DE ATENCION', titulo)
                    ws.write(6, 21, 'GESTION', titulo)
                    ws.write(6, 22, 'OBSERVACION', titulo)
                    ws.write(6, 23, 'OBS. RESOLUCION', titulo)
                    ws.write(6, 24, 'ESTADO DEL TRAMITE', titulo)
                    cabecera = 1
                    columna = 0
                    tot =0
                    detalle = 6
                    anterior = 0
                    actual = 0
                    fila = 6
                    identificacion=''
                    hoy=datetime.now()
                    aniocambio=''
                    #Tramites
                    #fechaaux2=datetime.combine(fechaf,time(23,59,0,000001))
                    for re in  RubroEspecieValorada.objects.filter(rubro__fecha__gte=fechai,rubro__fecha__lte=fechaf).order_by('rubro__fecha','serie'):
                        #for re in  RubroEspecieValorada.objects.filter(pk=436911,rubro__fecha__gte=fechai,rubro__fecha__lte=fechaf).order_by('rubro__fecha'):
                        if re.es_online():
                            #print((re.id))
                            telefono=''
                            celular=''
                            email=''
                            obsestudiante=''
                            coordinacion=''
                            matriculaactual=''
                            asis=''
                            grupo=''
                            gestion=''
                            gestiondocente=''
                            estadotramite=''
                            dia=''
                            mes=''
                            hora=''
                            minutos=''
                            horas=''
                            asistente=''
                            departamento=''
                            observaciones=''
                            observacioresolucion=''
                            h_espera=0
                            h_espera2=0
                            horas_totales=0
                            horasesperaestudiante=0
                            fechaaux2=datetime.combine(fechaf,time(23,59,0,1))
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
                                #print(re.id)
                                #print(re.rubro.fecha)
                                aniocambio=str(re.rubro.fecha.year)
                                if anio!=aniocambio:
                                    anio=aniocambio
                                    num_hoja=1
                                    hoja='gestiontiempo' + ' '+anio
                                    hoja=hoja+' '+str(num_hoja)
                                    num_hoja = num_hoja+1
                                    ws = wb.add_sheet(hoja,cell_overwrite_ok=True)
                                    ws.write_merge(0, 0,0,m+17, tit.nombre , titulo2)
                                    ws.write_merge(1, 1,0,m+17, 'Listado de Gestion de Tiempos en Solicitudes y Tramites', titulo2)
                                    ws.write(3, 0, 'DESDE', titulo)
                                    ws.write(3, 1, str((fechai.date())), titulo)
                                    ws.write(4, 0, 'HASTA:', titulo)
                                    ws.write(4, 1, str((fechaf.date())), titulo)
                                    ws.write(6, 0,  'DIA', titulo)
                                    ws.write(6, 1,  'MES', titulo)
                                    ws.write(6, 2,  'ANIO', titulo)
                                    ws.write(6, 3,  'HORA', titulo)
                                    ws.write(6, 4,  'TIEMPO DE ESPERA', titulo)
                                    ws.write(6, 5,  'TIEMPO DE GESTION', titulo)
                                    ws.write(6, 6,  'ESTUDIANTE', titulo)
                                    ws.write(6, 7,  'CEDULA', titulo)
                                    ws.write(6, 8,  'CELULAR', titulo)
                                    ws.write(6, 9,  'CONVENCIONAL', titulo)
                                    ws.write(6, 10,  'CORREO PERSONAL', titulo)
                                    ws.write(6, 11, 'CORREO INSTITUCIONAL', titulo)
                                    ws.write(6, 12, 'GRUPO', titulo)
                                    ws.write(6, 13, 'CARRERA', titulo)
                                    ws.write(6, 14, 'FACULTAD', titulo)
                                    ws.write(6, 15, '# DE TRAMITE', titulo)
                                    ws.write(6, 16, 'REQUERIMIENTO', titulo)
                                    ws.write(6, 17, 'DETALLE REQ/SOLIC.', titulo)
                                    ws.write(6, 18, 'TIPO DE REQUERIMIENTO', titulo)
                                    ws.write(6, 19, 'RESPONSABLE', titulo)
                                    ws.write(6, 20, 'CENTRO DE ATENCION', titulo)
                                    ws.write(6, 21, 'GESTION', titulo)
                                    ws.write(6, 22, 'OBSERVACION', titulo)
                                    ws.write(6, 23, 'OBS. RESOLUCION', titulo)
                                    ws.write(6, 24, 'ESTADO DEL TRAMITE', titulo)
                                    fila=6
                                fila = fila +1
                                if fila==65500:
                                    num_hoja=num_hoja
                                    hoja=hoja+' '+str(num_hoja+1)
                                    num_hoja = num_hoja+1
                                    ws = wb.add_sheet(hoja,cell_overwrite_ok=True)
                                    ws.write_merge(0, 0,0,m+17, tit.nombre , titulo2)
                                    ws.write_merge(1, 1,0,m+17, 'Listado de Gestion de Tiempos en Solicitudes y Tramites', titulo2)
                                    ws.write(3, 0, 'DESDE', titulo)
                                    ws.write(3, 1, str((fechai.date())), titulo)
                                    ws.write(4, 0, 'HASTA:', titulo)
                                    ws.write(4, 1, str((fechaf.date())), titulo)
                                    ws.write(6, 0,  'DIA', titulo)
                                    ws.write(6, 1,  'MES', titulo)
                                    ws.write(6, 2,  'ANIO', titulo)
                                    ws.write(6, 3,  'HORA', titulo)
                                    ws.write(6, 4,  'TIEMPO DE ESPERA', titulo)
                                    ws.write(6, 5,  'TIEMPO DE GESTION', titulo)
                                    ws.write(6, 6,  'ESTUDIANTE', titulo)
                                    ws.write(6, 7,  'CEDULA', titulo)
                                    ws.write(6, 8,  'CELULAR', titulo)
                                    ws.write(6, 9,  'CONVENCIONAL', titulo)
                                    ws.write(6, 10,  'CORREO PERSONAL', titulo)
                                    ws.write(6, 11, 'CORREO INSTITUCIONAL', titulo)
                                    ws.write(6, 12, 'GRUPO', titulo)
                                    ws.write(6, 13, 'CARRERA', titulo)
                                    ws.write(6, 14, 'FACULTAD', titulo)
                                    ws.write(6, 15, '# DE TRAMITE', titulo)
                                    ws.write(6, 16, 'REQUERIMIENTO', titulo)
                                    ws.write(6, 17, 'DETALLE REQ/SOLIC.', titulo)
                                    ws.write(6, 18, 'TIPO DE REQUERIMIENTO', titulo)
                                    ws.write(6, 19, 'RESPONSABLE', titulo)
                                    ws.write(6, 20, 'CENTRO DE ATENCION', titulo)
                                    ws.write(6, 21, 'GESTION', titulo)
                                    ws.write(6, 22, 'OBSERVACION', titulo)
                                    ws.write(6, 23, 'OBS. RESOLUCION', titulo)
                                    ws.write(6, 24, 'ESTADO DEL TRAMITE', titulo)
                                    fila=7

                                if re.rubro.fecha.day<10:
                                    dia=str('0'+str(re.rubro.fecha.day))
                                else:
                                    dia=str(re.rubro.fecha.day)
                                if re.rubro.fecha.month<10:
                                    mes=str('0'+str(re.rubro.fecha.month))
                                else:
                                    mes=str(re.rubro.fecha.month)

                                ws.write(fila,0,dia)
                                ws.write(fila,1,mes)
                                ws.write(fila,2,str(re.rubro.fecha.year))

                                if re.es_online():
                                    if re.fechaasigna!= None and re.fechaasigna < re.es_online().fecha:
                                        re.fechaasigna = re.es_online().fecha
                                        re.save()

                                    if re.es_online().fecha.hour<10:
                                        hora=str('0'+str(re.es_online().fecha.hour))
                                    else:
                                        hora=str(re.es_online().fecha.hour)
                                    if re.es_online().fecha.minute<10:
                                        minutos=str('0'+ str(re.es_online().fecha.minute))
                                    else:
                                        minutos=str(re.es_online().fecha.minute)
                                    horas=hora+':'+minutos

                                    if re.fechaasigna!=None and re.fechafinaliza!=None:
                                        if re.fechafinaliza<fechaaux2 and re.fechaasigna<fechaaux2:
                                            dias_espera = (re.fechafinaliza-re.fechaasigna).days
                                            h_espera=(dias_espera*24)
                                            segundos_espera = (re.fechafinaliza-re.fechaasigna).seconds
                                            h_espera2= Decimal(Decimal(segundos_espera).quantize(Decimal(10)**-2)/Decimal(3600).quantize(Decimal(10)**-2)).quantize(Decimal(10)**-2)
                                            if dias_espera<0:
                                                h_espera=0
                                            horas_totales=h_espera+h_espera2
                                            horasesperaestudiante=re.tiempoesperaestudiante(re.es_online().fecha,1)
                                        elif estadotramite=='FINALIZADA':
                                            dias_espera = (hoy-re.es_online().fecha).days
                                            h_espera=(dias_espera*24)
                                            segundos_espera = (hoy-re.es_online().fecha).seconds
                                            h_espera2= Decimal(Decimal(segundos_espera).quantize(Decimal(10)**-2)/Decimal(3600).quantize(Decimal(10)**-2)).quantize(Decimal(10)**-2)
                                            if dias_espera<0:
                                                h_espera=0
                                            horas_totales=h_espera+h_espera2
                                            horasesperaestudiante=re.tiempoesperaestudiante(re.es_online().fecha,4)
                                    elif re.fechaasigna==None:
                                        horas_totales=0
                                        horasesperaestudiante=re.tiempoesperaestudiante(re.es_online().fecha,4)
                                    elif re.fechafinaliza and re.fechaasigna==None and fechaaux2<re.fechafinaliza:
                                        dias_espera = (re.fechafinaliza-re.es_online().fecha).days
                                        h_espera=(dias_espera*24)
                                        segundos_espera = (re.fechafinaliza-re.es_online().fecha).seconds
                                        h_espera2= Decimal(Decimal(segundos_espera).quantize(Decimal(10)**-2)/Decimal(3600).quantize(Decimal(10)**-2)).quantize(Decimal(10)**-2)
                                        if dias_espera<0:
                                            h_espera=0
                                        horas_totales=h_espera+h_espera2
                                        horasesperaestudiante=re.tiempoesperaestudiante(re.es_online().fecha,1)
                                    else:
                                        dias_espera = (datetime.now()-re.fechaasigna).days
                                        h_espera=(dias_espera*24)
                                        segundos_espera = (datetime.now()-re.fechaasigna).seconds
                                        h_espera2= Decimal(Decimal(segundos_espera).quantize(Decimal(10)**-2)/Decimal(3600).quantize(Decimal(10)**-2)).quantize(Decimal(10)**-2)
                                        if dias_espera<0:
                                            h_espera=0
                                        horas_totales=h_espera+h_espera2
                                        horasesperaestudiante=re.tiempoesperaestudiante(datetime.now(),2)
                                else:
                                    #para las especies generadas en caja
                                    if re.fechafinaliza!=None and  re.fechaasigna!=None:
                                        if re.fechafinaliza<fechaaux2 and re.fechaasigna<=fechaaux2:
                                            dias_espera = (re.fechafinaliza-re.fechaasigna).days
                                            h_espera=(dias_espera*24)
                                            segundos_espera = (re.fechafinaliza-re.fechaasigna).seconds
                                            h_espera2= Decimal(Decimal(segundos_espera).quantize(Decimal(10)**-2)/Decimal(3600).quantize(Decimal(10)**-2)).quantize(Decimal(10)**-2)
                                            if dias_espera<0:
                                                h_espera=0
                                            horas_totales=h_espera+h_espera2
                                            horasesperaestudiante=re.tiempoesperaestudiante(re.fechaasigna,1)
                                        else:
                                            dias_espera = (datetime.now()- re.fechaasigna).days
                                            h_espera=(dias_espera*24)
                                            segundos_espera = (datetime.now()- re.fechaasigna).seconds
                                            h_espera2= Decimal(Decimal(segundos_espera).quantize(Decimal(10)**-2)/Decimal(3600).quantize(Decimal(10)**-2)).quantize(Decimal(10)**-2)
                                            if dias_espera<0:
                                                h_espera=0
                                            horas_totales=h_espera+h_espera2
                                            horasesperaestudiante=re.tiempoesperaestudiante(datetime.now(),2)
                                    elif re.fechaasigna==None:
                                        horas_totales=0
                                        fecharubro=datetime.combine(re.rubro.fecha,time(00,00,0,1))
                                        horasesperaestudiante=re.tiempoesperaestudiante(fecharubro,4)
                                ws.write(fila,3 ,horas)
                                ws.write(fila,4 ,horasesperaestudiante)
                                ws.write(fila,5 ,horas_totales)
                                try:
                                    nombreest = elimina_tildes(re.rubro.inscripcion.persona.nombre_completo())
                                except:
                                    nombreest ='Error Nombre'

                                ws.write(fila,6 ,nombreest)
                                if re.rubro.inscripcion.persona.cedula:
                                   identificacion= re.rubro.inscripcion.persona.cedula
                                else:
                                    identificacion= re.rubro.inscripcion.persona.pasaporte
                                try:
                                    if re.rubro.inscripcion.persona.telefono:
                                        celular=str(re.rubro.inscripcion.persona.telefono)
                                except:
                                    celular=''
                                try:
                                    if re.rubro.inscripcion.persona.telefono_conv:
                                        telefono=str(re.rubro.inscripcion.persona.telefono_conv)
                                except:
                                    telefono=''
                                try:
                                    if re.rubro.inscripcion.persona.email:
                                        email=str(re.rubro.inscripcion.persona.email)
                                except:
                                    email=''
                                ws.write(fila,7 ,str(identificacion))
                                ws.write(fila,8 ,celular)
                                ws.write(fila,9 ,telefono)
                                ws.write(fila,10 ,email)
                                ws.write(fila,11 ,str(re.rubro.inscripcion.persona.emailinst))
                                if Matricula.objects.filter(inscripcion = re.rubro.inscripcion,nivel__cerrado=False).exists():
                                    matriculaactual = Matricula.objects.filter(inscripcion = re.rubro.inscripcion,nivel__cerrado=False).order_by('-fecha')[:1].get()
                                    grupo=matriculaactual.nivel.grupo.nombre
                                    coordinacion=matriculaactual.nivel.coordinacion().nombre
                                else:
                                    grupo=re.rubro.inscripcion.grupo().nombre
                                    carrera= re.rubro.inscripcion.carrera
                                    if Coordinacion.objects.filter(carrera=carrera).exists():
                                        coordinacion=Coordinacion.objects.filter(carrera=carrera)[:1].get()
                                        coordinacion=coordinacion.nombre
                                ws.write(fila,12 ,str(grupo))
                                ws.write(fila,13 ,elimina_tildes(re.rubro.inscripcion.carrera))
                                ws.write(fila,14 ,elimina_tildes(coordinacion))
                                ws.write(fila,15 ,str(re.serie))
                                ws.write(fila,16 ,str('TRAMITE'))
                                try:
                                    if re.es_online().observacion:
                                        obsestudiante= (elimina_tildes(re.es_online().observacion)).replace(","," ").replace(":","").replace("%"," ").replace("\ "," ")
                                except:
                                    obsestudiante=''

                                ws.write(fila,17 ,obsestudiante)
                                ws.write(fila,18 ,elimina_tildes(re.tipoespecie.nombre))
                                fechaaux3=datetime.combine(fechaf,time(23,59,0,1))
                                if re.usrasig and re.fechaasigna<=fechaaux3 and re.fechaasigna!=None:
                                    estadousr=''
                                    if AsistenteDepartamento.objects.filter(persona__usuario=re.usrasig,departamento=re.departamento).exists():
                                        asis =  AsistenteDepartamento.objects.filter(persona__usuario=re.usrasig,departamento=re.departamento).order_by('-departamento__id')[:1].get()
                                        usuario=User.objects.filter(id=re.usrasig.id)[:1].get()
                                        departamento=elimina_tildes(asis.departamento.descripcion)
                                        if not usuario.is_active:
                                            estadousr='Inactivo'
                                            asistente=str(elimina_tildes(asis.persona.nombre_completo_inverso()))+' USR: '+ str(re.usrasig)+' Estado: '+estadousr
                                        else:
                                            asistente=str(elimina_tildes(asis.persona.nombre_completo_inverso()))+' USR: '+ str(re.usrasig)
                                    else:
                                        persona=Persona.objects.filter(usuario=re.usrasig)[:1].get()
                                        asistente= str(elimina_tildes(persona.nombre_completo_inverso())+' USR: '+ str(re.usrasig))
                                        if Profesor.objects.filter(persona=persona,activo=True).exists():
                                            departamento='NO TIENE DEPARTAMENTO ASIGNADO'
                                else:
                                    asistente=''
                                    if departamento=='':
                                        if re.dptoactual():
                                            departamento=elimina_tildes(re.dptoactual())

                                ws.write(fila,19 ,asistente)
                                if departamento=='':
                                    if re.dptoactual():
                                        departamento=elimina_tildes(re.dptoactual())
                                ws.write(fila,20 ,departamento)
                                if SeguimientoEspecie.objects.filter(rubroespecie=re).exists():
                                    for seguimiento in SeguimientoEspecie.objects.filter(rubroespecie=re):
                                        try:
                                            if seguimiento.observacion:
                                                gestion=(elimina_tildes(seguimiento.observacion)).replace(","," ").replace(":","").replace("%"," ") +' USR Gestion: '+ str(seguimiento.usuario)+' '+str(seguimiento.fecha)+' '+str(seguimiento.hora)
                                            else:
                                                gestion=''
                                        except:
                                            gestion='Error en gestion'
                                else:
                                    gestion=''
                                if re.fechaasigna!=None:
                                    try:
                                        if re.fechaasigna<=fechaaux2:
                                            if re.tienegestion_docente():
                                                if re.tienegestion_docente().finalizado:
                                                    gestiondocente='Docente: '+ elimina_tildes(re.tienegestion_docente().profesor)+' Resp. '+ elimina_tildes(re.tienegestion_docente().respuesta)
                                                else:
                                                    gestiondocente='Docente: '+ elimina_tildes(re.tienegestion_docente().profesor)
                                            else:
                                                gestiondocente=''
                                        else:
                                            gestiondocente=''
                                    except:
                                        gestiondocente='Docente: '+ elimina_tildes(re.tienegestion_docente().profesor)
                                else:
                                        gestiondocente=''

                                ws.write(fila,21,elimina_tildes(gestion+' '+gestiondocente))
                                if re.fechaasigna!=None:
                                    if re.fechaasigna<=fechaaux2:
                                        try:
                                            if re.observaciones:
                                               observaciones= (elimina_tildes(re.observaciones)).replace(","," ").replace(":","").replace("%"," ")
                                        except:
                                            observaciones='Error en observacion'
                                    else:
                                        observaciones=''

                                ws.write(fila,22,observaciones)

                                if re.fechaasigna!=None:
                                    if re.fechaasigna<=fechaaux2:
                                        try:
                                            if re.obsautorizar:
                                                observacioresolucion=(re.obsautorizar).replace("%"," ").replace(","," ").replace(":","").replace("      ","").replace("\ "," ")
                                        except:
                                            observacioresolucion='Error en obs resolucion'
                                    else:
                                        observacioresolucion=''
                                else:
                                        observacioresolucion=''
                                ws.write(fila,23,observacioresolucion)
                                if re.fechaasigna!=None and re.fechaasigna>fechaaux2 and re.fechafinaliza==None:
                                    estadotramite='EN PROCESO'
                                elif re.fechaasigna!=None and re.fechaasigna<fechaaux2 and re.fechafinaliza==None:
                                    estadotramite='EN PROCESO'
                                elif re.fechaasigna==None and re.fechaasigna==None:
                                    estadotramite='EN PROCESO'
                                elif fechaaux2<re.fechafinaliza:
                                    estadotramite='EN PROCESO'
                                elif re.aplicada and fechaaux2<re.fechafinaliza:
                                    estadotramite='EN PROCESO'
                                ws.write(fila,24 ,str(estadotramite))

                    #Solicitudes
                    for sol in  SolicitudSecretariaDocente.objects.filter(fecha__gte=fechai,fecha__lte=fechaf).order_by('fecha').exclude(solicitudestudiante=None):
                    #for sol in  SolicitudSecretariaDocente.objects.filter(pk=44645,fecha__gte=fechai,fecha__lte=fechaf).order_by('fecha').exclude(solicitudestudiante=None):
                        #print(sol.id)
                        coordinacion=''
                        carrera=''
                        matriculaactual=''
                        asis=''
                        grupo=''
                        gestion=''
                        gestiondocente=''
                        estadotramite=''
                        dia=''
                        mes=''
                        hora=''
                        minutos=''
                        horas=''
                        asistente=''
                        departamento=''
                        observaciones=''
                        observacioresolucion=''
                        obsestudiante=''
                        telefono=''
                        celular=''
                        email=''
                        if sol.cerrada:
                            estadotramite='FINALIZADO'
                        else:
                            estadotramite='EN PROCESO'
                        #print(sol.id)
                        #print(estadotramite)
                        fila = fila +1
                        if fila==65500:
                            num_hoja=num_hoja
                            hoja=hoja+str(num_hoja+1)
                            num_hoja = num_hoja+1
                            ws = wb.add_sheet(hoja,cell_overwrite_ok=True)
                            fila=7

                        if sol.fecha.day<10:
                            dia=str('0'+str(sol.fecha.day))
                        else:
                            dia=str(sol.fecha.day)
                        if sol.fecha.month<10:
                            mes=str('0'+str(sol.fecha.month))
                        else:
                            mes=str(sol.fecha.month)

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

                        ws.write(fila,3,horas)

                        h_espera=0
                        h_espera2=0
                        horas_totales=0
                        tiempoesperaestudiante=0
                        fcierre=''
                        if sol.cerrada  and sol.fechacierre<=fechaf2:
                            if sol.fechacierre and sol.fechaasignacion and sol.fechaasignacion<=fechaaux2 and sol.fechaasignacion!=None:
                                sol_estud=SolicitudEstudiante.objects.filter(pk=sol.solicitudestudiante.id)[:1].get()
                                fcierre=datetime.combine(sol.fechacierre,sol.hora)
                                dias_espera = (fcierre-sol.fechaasignacion).days
                                h_espera=(dias_espera*24)
                                segundos_espera = (fcierre-sol.fechaasignacion).seconds
                                h_espera2= Decimal(Decimal(segundos_espera).quantize(Decimal(10)**-2)/Decimal(3600).quantize(Decimal(10)**-2)).quantize(Decimal(10)**-2)
                                if dias_espera<0:
                                    h_espera=0
                                horas_totales=h_espera+h_espera2
                                tiempoesperaestudiante=sol.tiempoesperaestudiante(sol_estud.fecha,1)
                            else:
                                #cuando no tiene fecha de asignacion
                                sol_estud=SolicitudEstudiante.objects.filter(pk=sol.solicitudestudiante.id)[:1].get()
                                fcierre=datetime.combine(sol.fechacierre,sol.hora)
                                dias_espera = (fcierre-sol_estud.fecha).days
                                h_espera=(dias_espera*24)
                                segundos_espera = (fcierre-sol_estud.fecha).seconds
                                h_espera2= Decimal(Decimal(segundos_espera).quantize(Decimal(10)**-2)/Decimal(3600).quantize(Decimal(10)**-2)).quantize(Decimal(10)**-2)
                                if dias_espera<0:
                                    h_espera=0
                                horas_totales=h_espera+h_espera2
                                tiempoesperaestudiante=sol.tiempoesperaestudiante(sol_estud.fecha,1)
                        else:
                            sol_estud=SolicitudEstudiante.objects.filter(pk=sol.solicitudestudiante.id)[:1].get()
                            dias_espera = (hoy-sol_estud.fecha).days
                            h_espera=(dias_espera*24)
                            segundos_espera = (hoy-sol_estud.fecha).seconds
                            h_espera2= Decimal(Decimal(segundos_espera).quantize(Decimal(10)**-2)/Decimal(3600).quantize(Decimal(10)**-2)).quantize(Decimal(10)**-2)
                            if dias_espera<0:
                                h_espera=0
                            horas_totales=h_espera+h_espera2
                            tiempoesperaestudiante=sol.tiempoesperaestudiante(hoy,2)

                        ws.write(fila,4 ,tiempoesperaestudiante)
                        ws.write(fila,5 ,horas_totales)

                        try:
                            nombreest = elimina_tildes(sol.persona.nombre_completo())
                        except:
                            nombreest ='Error Nombre'

                        ws.write(fila,6 ,nombreest)
                        if sol.persona.cedula:
                           identificacion= sol.persona.cedula
                        else:
                            identificacion= sol.persona.pasaporte
                        ws.write(fila,7 ,str(identificacion))

                        try:
                            if sol.persona.telefono:
                                celular = str(sol.persona.telefono)
                        except:
                            celular =''
                        try:
                            if sol.persona.telefono_conv:
                                telefono = str(sol.persona.telefono_conv)
                        except:
                            telefono =''
                        try:
                            if sol.persona.email:
                                email = str(sol.persona.email)
                        except:
                            email =''

                        ws.write(fila,8,celular)
                        ws.write(fila,9,telefono)
                        ws.write(fila,10,email)
                        ws.write(fila,11,str(sol.persona.emailinst))

                        if Inscripcion.objects.filter(persona=sol.persona).exists():
                            inscripcion=Inscripcion.objects.filter(persona=sol.persona).order_by('-id')[:1].get()
                            if Matricula.objects.filter(inscripcion=inscripcion,nivel__cerrado=False).exists():
                                matriculaactual = Matricula.objects.filter(inscripcion = inscripcion,nivel__cerrado=False).order_by('-fecha')[:1].get()
                                grupo=matriculaactual.nivel.grupo.nombre
                                carrera=elimina_tildes(inscripcion.carrera)
                                coordinacion=matriculaactual.nivel.coordinacion().nombre
                            else:
                                grupo=inscripcion.grupo().nombre
                                carrera=elimina_tildes(inscripcion.carrera)
                                if Coordinacion.objects.filter(carrera=inscripcion.carrera.id).exists():
                                    coordinacion=Coordinacion.objects.filter(carrera=inscripcion.carrera.id)[:1].get()
                                    coordinacion=coordinacion.nombre
                                else:
                                    coordinacion=''

                        ws.write(fila,12,str(grupo))
                        ws.write(fila,13,elimina_tildes(carrera))
                        ws.write(fila,14,elimina_tildes(coordinacion))
                        ws.write(fila,15,str(sol.id))
                        ws.write(fila,16,str('SOLICITUD'))

                        try:
                            if sol.descripcion:
                                obsestudiante= (elimina_tildes(sol.descripcion)).replace(","," ").replace(":","").replace("%"," ").replace("\ "," ")
                        except:
                            obsestudiante=''
                        ws.write(fila,17,obsestudiante)
                        ws.write(fila,18,elimina_tildes(sol.tipo.nombre))

                        if sol.fechaasignacion!=None:
                            if sol.fechaasignacion<=fechaaux2:
                                if sol.personaasignada:
                                    asistente=str(elimina_tildes(sol.personaasignada.nombre_completo_inverso()))+' USR: '+ str(sol.personaasignada.usuario)
                                    if AsistenteDepartamento.objects.filter(persona=sol.personaasignada,departamento=sol.departamento).exists():
                                        asis =  AsistenteDepartamento.objects.filter(persona=sol.personaasignada,departamento=sol.departamento).order_by('-departamento__id')[:1].get()
                                        if asis.departamento:
                                            departamento=elimina_tildes(asis.departamento.descripcion)
                                        else:
                                            departamento='NO TIENE DEPARTAMENTO ASIGNADO'
                                    else:
                                        departamento=elimina_tildes(sol.departamento.descripcion)
                                else:
                                    if AsistenteDepartamento.objects.filter(persona__usuario=sol.usuario,departamento=sol.departamento).exists():
                                        asis =  AsistenteDepartamento.objects.filter(persona__usuario=sol.usuario,departamento=sol.departamento).order_by('-departamento__id')[:1].get()
                                        asistente=str(elimina_tildes(asis.persona.nombre_completo_inverso()))+' USR: '+ str(asis.persona.usuario)
                                        departamento=elimina_tildes(asis.departamento.descripcion)
                                    else:
                                       departamento=elimina_tildes(sol.departamento.descripcion)
                            else:
                                if sol.tienegestion():
                                    if IncidenciaAsignada.objects.filter(solicitusecret=sol,observacion="CAMBIO DE DEPARTAMENTO").order_by('-id').exists():
                                        solasis=IncidenciaAsignada.objects.filter(solicitusecret=sol,observacion="CAMBIO DE DEPARTAMENTO").order_by('-id')[:1].get()
                                        asis =  AsistenteDepartamento.objects.filter(pk=solasis.asistentedepartamento.id).order_by('-departamento__id')[:1].get()
                                        asistente=str(elimina_tildes(asis.persona.nombre_completo_inverso()))+' USR: '+ str(asis.persona.usuario)
                                        departamento=elimina_tildes(sol.departamento.descripcion)
                                    else:
                                        departamento=elimina_tildes(sol.departamento.descripcion)
                                        asistente=''
                                else:
                                    departamento=elimina_tildes(sol.departamento.descripcion)
                                    asistente=''
                        else:
                            if sol.personaasignada:
                                asistente=str(elimina_tildes(sol.personaasignada.nombre_completo_inverso()))+' USR: '+ str(sol.personaasignada.usuario)
                                if AsistenteDepartamento.objects.filter(persona=sol.personaasignada,departamento=sol.departamento).exists():
                                    asis =  AsistenteDepartamento.objects.filter(persona=sol.personaasignada,departamento=sol.departamento).order_by('-departamento__id')[:1].get()
                                    if asis.departamento:
                                        departamento=elimina_tildes(asis.departamento.descripcion)
                                    else:
                                        departamento=elimina_tildes(sol.departamento.descripcion)
                            elif sol.cerrada and sol.fechacierre>fechaf2:
                                departamento=elimina_tildes(sol.departamento.descripcion)
                                asistente=''

                        ws.write(fila,19,str(asistente))
                        ws.write(fila,20,departamento)
                        if sol.fechaasignacion!=None:
                            if sol.fechaasignacion<=fechaaux2:
                                if IncidenciaAsignada.objects.filter(solicitusecret=sol).exists():
                                    for indicencia in IncidenciaAsignada.objects.filter(solicitusecret=sol):
                                        try:
                                            if indicencia.observacion:
                                                gestion=(elimina_tildes(indicencia.observacion)).replace(","," ").replace(":","").replace("%"," ") +' USR Gestion: '+ str(indicencia.usuario)+' '+str(indicencia.fecha)
                                            else:
                                                gestion=''
                                        except:
                                            gestion='Error en gestion'
                                else:
                                    gestion=''
                            else:
                                gestion=''
                        else:
                                gestion=''

                        ws.write(fila,21,str(gestion))
                        if sol.fechaasignacion!=None:
                            if sol.fechaasignacion<=fechaaux2:
                                try:
                                    if sol.observacion:
                                        observaciones= (elimina_tildes(sol.observacion)).replace(","," ").replace(":","").replace("%"," ").replace("\ "," ")
                                    else:
                                        observaciones=''
                                except:
                                    observaciones='Error en observacion'
                            else:
                                observaciones=''
                        else:
                                observaciones=''
                        ws.write(fila,22,observaciones)
                        try:
                            if sol.fechaasignacion!=None:
                                if sol.resolucion and sol.fechaasignacion<=fechaaux2:
                                    observacioresolucion= (elimina_tildes(sol.resolucion)).replace(","," ").replace(":","").replace("%"," ").replace("\ "," ") +' '+str(fcierre)
                                else:
                                    observacioresolucion=''
                            else:
                                if sol.resolucion and sol.cerrada and sol.fechacierre<=fechaf2:
                                    observacioresolucion= (elimina_tildes(sol.resolucion)).replace(","," ").replace(":","").replace("%"," ").replace("\ "," ") +' '+str(fcierre)
                                else:
                                    observacioresolucion=''
                        except:
                            observacioresolucion ='Error en observacion resolucion'

                        ws.write(fila,23,observacioresolucion)
                        if sol.fechaasignacion!=None:
                            if sol.cerrada and sol.fechacierre<=fechaf2:
                                estadotramite='FINALIZADO'
                            else:
                                estadotramite='EN PROCESO'
                        else:
                            if sol.cerrada and sol.fechacierre>fechaf2:
                                estadotramite='EN PROCESO'
                        ws.write(fila,24,str(estadotramite))

                    detalle = detalle + fila
                    ws.write(detalle, 0, "Fecha Impresion", subtitulo)
                    ws.write(detalle, 2, str(datetime.now()), subtitulo)
                    detalle=detalle +1
                    ws.write(detalle, 0, "Usuario", subtitulo)
                    ws.write(detalle, 2, str(request.user), subtitulo)

                    nombre ='bandejagestion'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex) + " ")
                    return HttpResponse(json.dumps({"result":str(re.id) }),content_type="application/json")
        else:
            data = {'title': 'Listado de Gestion de Tiempos en Solicitudes y Tramites'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform']=RangoFacturasForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
                return render(request ,"reportesexcel/bandeja_atencion.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

