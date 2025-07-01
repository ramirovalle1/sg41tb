from datetime import datetime
import json
from django.contrib.admin.models import LogEntry
import xlwt
import os
import locale
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from settings import MEDIA_ROOT,UTILIZA_FACTURACION_CON_FPDF,JR_USEROUTPUT_FOLDER,MEDIA_URL, SITE_ROOT,COSTO_PROFESIONALIZACION,COSTO_COMPLEXIVO
from sga.commonviews import addUserData
from sga.forms import RangoFacturasForm, DistributivoForm
from sga.models import convertir_fecha,Materia,TituloInstitucion,ReporteExcel, Profesor, Materia,  Periodo, ProfesorMateria,Clase,Carrera,\
      LeccionGrupo,Sede,TitulacionProfesor, RolPerfilProfesor,CostoAsignatura
from sga.reportes import elimina_tildes
# from django.contrib.django.models import Admin_Log
from fpdf import FPDF



@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action  =='generar':
                try:
                    inicio = convertir_fecha(request.POST['inicio'])
                    fin = convertir_fecha(request.POST['fin'])
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10
                    style1 = xlwt.easyxf('',num_format_str='DD-MMM-YY')
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('Clases Impartidas',cell_overwrite_ok=True)
                    m = 18
                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,m, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,m, 'LISTADO CLASES IMPARTIDAS POR RANGO DE FECHAS', titulo2)
                    ws.write(3, 0, 'FECHA INICIO', titulo)
                    ws.write(3, 1, str(inicio.date()), titulo)
                    ws.write(4, 0, 'FECHA FIN', titulo)
                    ws.write(4, 1, str(fin.date()), titulo)

                    cont =6
                    detalle = 6
                    prof = LeccionGrupo.objects.filter(materia__nivel__periodo__activo=True,profesor__activo=True,fecha__gte=inicio,fecha__lte=fin).values('profesor')
                    # prof = LeccionGrupo.objects.filter(materia__nivel__periodo__activo=True,profesor__activo=True,fecha__gte=inicio,fecha__lte=fin,profesor=512).values('profesor')
                    # prof = LeccionGrupo.objects.filter(materia__nivel__periodo__activo=True,profesor__activo=True,fecha__gte=inicio,fecha__lte=fin,profesor=642).values('profesor')
                    leccionesGrupo = LeccionGrupo.objects.filter(materia__nivel__periodo__activo=True,profesor__activo=True).order_by('-fecha', '-horaentrada')
                    materias = Clase.objects.filter(materia__profesormateria__hasta__gte=inicio).distinct('materia').values('materia').order_by('materia__nivel__periodo','materia__nivel__carrera')
                    profesor = Profesor.objects.filter(id__in=prof).order_by('persona__apellido1','persona__apellido2','persona__nombres')

                    tprof=TitulacionProfesor.objects.filter().values('nivel').distinct('nivel')
                    c=1
                    cont = cont+2
                    ws.write(cont, 0,  'DOCENTE', titulo)
                    ws.write(cont, 1,  'CARRERA', titulo)
                    ws.write(cont, 2,  'FECHA', titulo)
                    ws.write(cont, 3,  'DIA', titulo)
                    ws.write(cont, 4,  'ENTRADA', titulo)
                    ws.write(cont, 5,  'SALIDA', titulo)
                    ws.write(cont, 6,  'TURNO ENTRADA', titulo)
                    ws.write(cont, 7,  'TURNO SALIDA', titulo)
                    ws.write(cont, 8,  'ASIGNATURA', titulo)
                    ws.write(cont, 9,  'NIVEL', titulo)
                    ws.write(cont, 10,  'DESDE', titulo)
                    ws.write(cont, 11, 'HASTA', titulo)
                    ws.write(cont, 12, 'PARALELO', titulo)
                    ws.write(cont, 13, 'CAMPUS', titulo)
                    ws.write(cont, 14, 'HORAS TURNO', titulo)
                    ws.write(cont, 15, 'VALOR TURNO', titulo)
                    # ws.write(cont, 16, 'HORAS', titulo)
                    ws.write(cont, 16, 'VALOR', titulo)
                    ws.write(cont, 17, 'TITULO TECNICO', titulo)
                    ws.write(cont, 18, 'TITULO 3ER NIVEL', titulo)
                    ws.write(cont, 19, 'TITULO 4TO NIVEL', titulo)

                    for p in profesor:
                        # print(p)
                        atraso=''
                        hora1=''
                        minu1=''
                        entradaturno=''
                        hora2=''
                        minu2=''
                        entrada=''
                        atrasado=''
                        revision=''
                        perfilrol=''
                        valorclase=0
                        costohora=0

                        if c > 0:
                            c=0

                        for lg in LeccionGrupo.objects.filter(materia__nivel__periodo__activo=True,profesor=p,fecha__gte=inicio,fecha__lte=fin).order_by('materia__nivel__grupo','fecha', 'horaentrada'):
                            if lg.horaentrada>lg.turno.comienza:
                                hora2=str(lg.horaentrada).split(':')[0]
                                minu2=str(lg.horaentrada).split(':')[1]
                                entrada=hora2+':'+minu2
                                hora1=str(lg.turno.comienza)
                                hora1=str(lg.turno.comienza).split(':')[0]
                                minu1=str(lg.turno.comienza).split(':')[1]
                                entradaturno=hora1+':'+minu1
                                atraso=OperHoras(entrada,entradaturno,'-')
                                atraso=int(atraso.split(':')[1])
                                if atraso>15:
                                   atrasado='Si'
                                else:
                                   atrasado=''

                            # if LogEntry.objects.filter(object_id=str(lg.id),change_message__icontains='Abierta Clase Docente').exists():
                            #     revision=LogEntry.objects.filter(object_id=str(lg.id),change_message__icontains='Abierta Clase Docente')[:1].get().action_time

                            dia_semana=''
                            valorhora = 0
                            c=c+1
                            cont = cont + 1
                            ws.write(cont, 0, str(elimina_tildes(p.persona.nombre_completo_inverso())),titulo)
                            ws.write(cont, 1, str(elimina_tildes(lg.materia.nivel.carrera.nombre)))
                            ws.write(cont, 2, str(lg.fecha))

                            if lg.materia.nivel.carrera.validacionprofesional:
                                if lg.dia==1:
                                    dia_semana='LUNES'
                                    valorhora = COSTO_PROFESIONALIZACION
                                elif lg.dia==2:
                                    dia_semana='MARTES'
                                    valorhora = COSTO_PROFESIONALIZACION
                                elif lg.dia==3:
                                    dia_semana='MIERCOLES'
                                    valorhora = COSTO_PROFESIONALIZACION
                                elif lg.dia==4:
                                    dia_semana='JUEVES'
                                    valorhora = COSTO_PROFESIONALIZACION
                                elif lg.dia==5:
                                    dia_semana='VIERNES'
                                    valorhora = COSTO_PROFESIONALIZACION
                                elif lg.dia==6:
                                    dia_semana='SABADO'
                                    valorhora = COSTO_PROFESIONALIZACION
                                elif lg.dia==7:
                                    dia_semana='DOMINGO'
                                    valorhora = COSTO_PROFESIONALIZACION
                            else:
                                if RolPerfilProfesor.objects.filter(profesor=p).exists():
                                    perfilrol= RolPerfilProfesor.objects.filter(profesor=p)[:1].get()
                                    valorhora = 0

                                if lg.dia==1:
                                    dia_semana='LUNES'
                                    if perfilrol:
                                        valorhora = perfilrol.chlunes
                                elif lg.dia==2:
                                    dia_semana='MARTES'
                                    if perfilrol:
                                        valorhora = perfilrol.chmartes
                                elif lg.dia==3:
                                    dia_semana='MIERCOLES'
                                    if perfilrol:
                                        valorhora = perfilrol.chmiercoles
                                elif lg.dia==4:
                                    dia_semana='JUEVES'
                                    if perfilrol:
                                        valorhora = perfilrol.chjueves
                                elif lg.dia==5:
                                    dia_semana='VIERNES'
                                    if perfilrol:
                                        valorhora = perfilrol.chviernes
                                elif lg.dia==6:
                                    dia_semana='SABADO'
                                    if perfilrol:
                                        valorhora = perfilrol.chsabado
                                elif lg.dia==7:
                                    dia_semana='DOMINGO'
                                    if perfilrol:
                                        valorhora = perfilrol.chdomingo

                            #OCastillo 26-10-2021 para examen complexivo
                            if Materia.objects.filter(pk=lg.materia.id,nivel__paralelo__icontains='COMPLEXIVO').exists():
                                paralelo=Materia.objects.filter(pk=lg.materia.id,nivel__paralelo__icontains='COMPLEXIVO')[:1].get()
                                if paralelo:
                                    if lg.dia==1:
                                        dia_semana='LUNES'
                                        valorhora = COSTO_COMPLEXIVO
                                    elif lg.dia==2:
                                        dia_semana='MARTES'
                                        valorhora = COSTO_COMPLEXIVO
                                    elif lg.dia==3:
                                        dia_semana='MIERCOLES'
                                        valorhora = COSTO_COMPLEXIVO
                                    elif lg.dia==4:
                                        dia_semana='JUEVES'
                                        valorhora = COSTO_COMPLEXIVO
                                    elif lg.dia==5:
                                        dia_semana='VIERNES'
                                        valorhora = COSTO_COMPLEXIVO
                                    elif lg.dia==6:
                                        dia_semana='SABADO'
                                        valorhora = COSTO_COMPLEXIVO
                                    elif lg.dia==7:
                                        dia_semana='DOMINGO'
                                        valorhora = COSTO_COMPLEXIVO

                            #OCastillo 05-11-2021 para costos por asignatura en malla
                            if CostoAsignatura.objects.filter(asignaturamalla__asignatura=lg.materia.asignatura,asignaturamalla__malla__carrera=lg.materia.nivel.carrera,activo=True).exists():
                                costohora=CostoAsignatura.objects.get(asignaturamalla__asignatura=lg.materia.asignatura,asignaturamalla__malla__carrera=lg.materia.nivel.carrera,activo=True).valor
                                if costohora>0:
                                    if lg.dia==1:
                                        dia_semana='LUNES'
                                        valorhora=costohora
                                    elif lg.dia==2:
                                        dia_semana='MARTES'
                                        valorhora=costohora
                                    elif lg.dia==3:
                                        dia_semana='MIERCOLES'
                                        valorhora = costohora
                                    elif lg.dia==4:
                                        dia_semana='JUEVES'
                                        valorhora = costohora
                                    elif lg.dia==5:
                                        dia_semana='VIERNES'
                                        valorhora = costohora
                                    elif lg.dia==6:
                                        dia_semana='SABADO'
                                        valorhora = costohora
                                    elif lg.dia==7:
                                        dia_semana='DOMINGO'
                                        valorhora = costohora


                            ws.write(cont, 3, str(dia_semana))
                            ws.write(cont, 4, str(lg.horaentrada))
                            ws.write(cont, 5, str(lg.horasalida))
                            ws.write(cont, 6, str(lg.turno.comienza))
                            ws.write(cont, 7, str(lg.turno.termina))
                            ws.write(cont, 8, str(elimina_tildes(lg.materia.asignatura.nombre)))
                            ws.write(cont, 9, str(elimina_tildes(lg.materia.nivel.nivelmalla.nombre)))
                            ws.write(cont, 10, str(elimina_tildes(lg.materia.inicio)))
                            ws.write(cont, 11, str(elimina_tildes(lg.materia.fin)))
                            ws.write(cont, 12, str(elimina_tildes(lg.materia.nivel.paralelo)))

                            if lg.aula:
                                sede=Sede.objects.filter(aula=lg.aula.id).get()
                                ws.write(cont, 13, str(elimina_tildes(sede.nombre)))

                            ws.write(cont, 14, lg.turno.horas)
                            ws.write(cont, 15, valorhora)
                            valorclase = (lg.turno.horas * valorhora)

                            # for pm in ProfesorMateria.objects.filter(hasta__gte=inicio,profesor=p,materia__id=lg.materia.id):
                            #     ws.write(cont, 16, lg.materia.horas_materia_rangofecha(pm,inicio,fin)[0])
                            #     ws.write(cont, 17, lg.materia.horas_materia_rangofecha(pm,inicio,fin)[1])
                            ws.write(cont, 16, valorclase)
                            col=17
                            tprof=TitulacionProfesor.objects.filter().distinct('nivel').values('nivel').order_by('nivel')

                            tecnico=''
                            tercernivel=''
                            cuartonivel=''
                            tituloprofesional=''
                            for tp in tprof:
                                tituloprofesional=''
                                if str(tp['nivel'])=='TECNICO':
                                    if TitulacionProfesor.objects.filter(profesor=p,nivel=str(tp['nivel'])).exists():
                                         for titprof in TitulacionProfesor.objects.filter(profesor=p,nivel=str(tp['nivel'])):
                                            tituloprofesional=str(elimina_tildes(titprof.titulo))
                                            tecnico=tecnico+'  '+tituloprofesional

                                if str(tp['nivel'])=='3er. NIVEL':
                                    if TitulacionProfesor.objects.filter(profesor=p,nivel=str(tp['nivel'])).exists():
                                        for titprof in TitulacionProfesor.objects.filter(profesor=p,nivel=str(tp['nivel'])):
                                            tituloprofesional=str(elimina_tildes(titprof.titulo))
                                            tercernivel=tercernivel+'  '+tituloprofesional

                                if str(tp['nivel'])=='4to. NIVEL':
                                    if TitulacionProfesor.objects.filter(profesor=p,nivel=str(tp['nivel'])).exists():
                                        for titprof in TitulacionProfesor.objects.filter(profesor=p,nivel=str(tp['nivel'])):
                                            tituloprofesional=str(elimina_tildes(titprof.titulo))
                                            cuartonivel=cuartonivel+'  '+tituloprofesional

                            ws.write(cont, col,tecnico)
                            ws.write(cont, col+1,str(tercernivel))
                            ws.write(cont, col+2,str(cuartonivel))

                            # ws.write(cont, 15, str(elimina_tildes(lg.turno.horas)))
                            # ws.write(cont, 14, str(atrasado))
                            # ws.write(cont, 11, str(revision))

                    if c == 0:
                        ws.write(cont, 0, '')
                        ws.write(cont, 1, '')
                        ws.write(cont,2, '')
                        ws.write(cont, 3, '')
                        ws.write(cont,4, '')
                        ws.write(cont,5, '')
                        ws.write(cont, 6, '')
                        ws.write(cont, 7, '')
                        ws.write(cont, 8, '')

                    detalle = detalle + cont
                    ws.write(detalle, 0, "Fecha Impresion", subtitulo)
                    ws.write(detalle, 1, str(datetime.now()), subtitulo)
                    detalle=detalle +1
                    ws.write(detalle, 0, "Usuario", subtitulo)
                    ws.write(detalle, 1, str(request.user), subtitulo)

                    nombre ='clasesimpartidas'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")
                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")

        else:
            data = {'title': 'Clases Impartidas de Docentes'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform']=DistributivoForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
                return render(request ,"reportesexcel/clasesimpartidas.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))


def OperHoras(hini, hfin, op):
    resultado = '00:00'
    if hini=='':
        hini='00:00'
    if hfin=='':
        hfin='00:00'
    if len(str(hini)) > 2 and len(str(hfin)) > 2:
        if (len(str(hini)) > 5 and len(str(hini)) <= 8 ):#********    Cuando el formato solo llega em horas      *******
            hini = str(hini).split(':')[0].zfill(2)+':'+str(hini).split(':')[1].zfill(2)
        if (len(str(hfin)) > 5 and len(str(hfin)) <= 8):
            hfin = str(hfin).split(':')[0].zfill(2)+':'+str(hfin).split(':')[1].zfill(2)

        if (len(hini) > 8):
            hini = str(hini).split(' ')[1].split(':')[0].zfill(2)+':'+str(hini).split(' ')[1].split(':')[1].zfill(2)
        if (len(hfin) > 8):
            hfin = str(hfin).split(' ')[1].split(':')[0].zfill(2)+':'+str(hfin).split(' ')[1].split(':')[1].zfill(2)


        if op == '-':
            if (int(str(hfin).split(':')[0])) >= (int(str(hini[0:2]))) and int(str(hfin).split(':')[1]) >= int(str(hini[3:])):# Si la Hora y los minutos de salida son mayores
                resultado = str((int(str(hfin).split(':')[0])) - (int(str(hini[0:2])))).zfill(2) + ':' + str((int(str(hfin).split(':')[1])) - (int(str(hini[3:])))).zfill(2)

            elif (int(str(hfin).split(':')[0])) > (int(str(hini[0:2]))) and int(str(hini[3:])) > int(str(hfin).split(':')[1]):# Solo y si los minutos son mayores mas no la Hora
                llevouna = ((int(str(hfin).split(':')[1])) + 60) - (int(str(hini[3:])))
                if llevouna >= 60:
                    llevouna = llevouna - 60
                    resultado = str(((int(str(hfin).split(':')[0]))) - (int(str(hini[0:2])))).zfill(2) + ':' + str(llevouna).zfill(2)
                else:
                    resultado = str(((int(str(hfin).split(':')[0])) - 1) - (int(str(hini[0:2])))).zfill(2) + ':' + str(llevouna).zfill(2)

            elif (int(str(hfin).split(':')[0])) == (int(str(hini[0:2])))and  int(str(hini[3:])) > int(str(hfin).split(':')[1]) and resultado == '00:00': #cuando debe horas o minutos
                resultado ='-'+ str((int(str(hini[0:2]))) - (int(str(hfin).split(':')[0]))).zfill(2) + ':' + str((int(str(hini[3:]))) - (int(str(hfin).split(':')[1]))).zfill(2)

            elif (int(str(hfin[0:2]))) < (int(str(hini[0:2]))):
                    llevouna = ((int(str(hini[3:]))) + 60) - (int(str(hfin).split(':')[1]))
                    if llevouna >= 60:
                        llevouna = llevouna - 60
                        resultado ='-'+ str(((int(str(hini[0:2])))) - (int(str(hfin).split(':')[0]))).zfill(2) + ':' + str(llevouna).zfill(2)
                    else:
                        resultado ='-'+ str(((int(str(hini[0:2]))) - 1) - (int(str(hfin).split(':')[0]))).zfill(2) + ':' + str(llevouna).zfill(2)



            # if resultado=='00:00':#Cundo se Registre solo Una Entrada Se asume que se Laboro 8 horas
            #     resultado='08:00'
        if op == '+':
            if (int(str(hfin).split(':')[1]) + int(str(hini).split(':')[1])) >= 60:
                #***********     Empareja que los valores sumados no excedn los 60 minutos        *******
                llevouna = (int(str(hfin).split(':')[1]) + int(str(hini).split(':')[1])) - 60
                resultado = str((int(str(hfin).split(':')[0]) + 1) + (int(str(hini).split(':')[0]))).zfill(2) + ':' + str(llevouna).zfill(2)
            else:
                resultado = str((int(str(hfin).split(':')[0])) + (int(str(hini).split(':')[0]))).zfill(2) + ':' + str(((int(str(hfin).split(':')[1])) + (int(str(hini).split(':')[1])))).zfill(2)
    return resultado



















