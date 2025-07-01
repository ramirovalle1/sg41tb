from datetime import datetime,timedelta
import json
import xlwt
import os
from decimal import Decimal
from django.db.models import Sum
from django.http import HttpResponseRedirect,HttpResponse
from settings import MEDIA_ROOT,MEDIA_URL, SITE_ROOT
from sga.commonviews import ip_client_address
from sga.models import TituloInstitucion, Carrera, Matricula, Rubro, Pago, Coordinacion, InscripcionGrupo, \
    ArchivoReporteCarrera, AsistAsuntoEstudiant, ResumenCartera, NivelTutor, Inscripcion, CategoriaRubro, \
    RubroSeguimiento, RegistroSeguimiento, TipoIncidencia, RubrosGestionMora
from sga.reportes import elimina_tildes
from sga.tasks import send_html_mail


def view(request):
    try:
        start_time = datetime.now()
        client_address = ip_client_address(request)
        if 'cron' in request.GET:
            print('actualizaarchivo '+str(datetime.now().date())+' SE ENVIO CRON EN EL GET')
        print('actualizaarchivo '+str(datetime.now().date())+'EJECUCION URL ACTUALIZA ARCHIVO INICIO '+str(datetime.now())+ ' IP:'+str(client_address))
        titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
        titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
        titulo.font.height = 20*11
        titulo2.font.height = 20*11
        subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
        subtitulo3 = xlwt.easyxf('font: name Times New Roman; align: wrap on, vert centre, horiz center')
        subtitulo.font.height = 20*10
        tit = TituloInstitucion.objects.all()[:1].get()
        asistentes = AsistAsuntoEstudiant.objects.filter(estado=True).distinct('id').values('id')
        contador = AsistAsuntoEstudiant.objects.filter(estado=True).distinct('id').values('id').count()
        contaasi = 0

        coordinacion_tota1 = {}
        coordinacion_tota2 = {}
        coordinacion_tota3 = {}
        coordinacion_totb1 = {}
        coordinacion_totb2 = {}
        coordinacion_totc1 = {}
        coordinacion_totc2 = {}
        coordinacion_totd = {}
        coordinacion_tote = {}

        carrera_tota1 = {}
        carrera_tota2 = {}
        carrera_tota3 = {}
        carrera_totb1 = {}
        carrera_totb2 = {}
        carrera_totc1 = {}
        carrera_totc2 = {}
        carrera_totd = {}
        carrera_tote = {}
        carreras =[]
        from django.db import connection
        cur = connection.cursor()
        cur.execute("REFRESH MATERIALIZED VIEW rubrosgestionmora;")
        try:
            connection.commit()
        except Exception as e:
            print("Error al actualizar la vista materializada rubrosgestionmora:", str(e))
            connection.rollback()

        coordinaciones = Coordinacion.objects.filter(id__in=Coordinacion.objects.filter(carrera__carrera=True, carrera__activo=True).select_related('carrera').values('id')).order_by('id')
        for coordinacion in coordinaciones:
            insc_tota1 = []
            insc_tota2 = []
            insc_tota3 = []
            insc_totb1 = []
            insc_totb2 = []
            insc_totc1 = []
            insc_totc2 = []
            insc_totd = []
            insc_tote = []
            carrera_cord =Carrera.objects.filter(carrera=True, activo=True, id__in=coordinacion.carrera.all())
            for c in carrera_cord:
                carreras.append(c.id)
                tota1=Decimal(0)
                tota2=Decimal(0)
                tota3=Decimal(0)
                totb1=Decimal(0)
                totb2=Decimal(0)
                totc1=Decimal(0)
                totc2=Decimal(0)
                totd=Decimal(0)
                tote=Decimal(0)

                arreglo_tota1 = []
                arreglo_tota2 = []
                arreglo_tota3 = []
                arreglo_totb1 = []
                arreglo_totb2 = []
                arreglo_totc1 = []
                arreglo_totc2 = []
                arreglo_totd = []
                arreglo_tote = []

                ins_tota1 = []
                ins_tota2 = []
                ins_tota3 = []
                ins_totb1 = []
                ins_totb2 = []
                ins_totc1 = []
                ins_totc2 = []
                ins_totd = []
                ins_tote = []

                fecha = datetime.now().date()
                columna=0
                archivorep =ArchivoReporteCarrera.objects.filter(carrera=c)[:1]
                if archivorep:
                    a = archivorep.filter().get()
                    a.fechaactualiza = fecha
                    a.save()
                else:
                    a = ArchivoReporteCarrera(carrera=c,fechaactualiza=fecha)
                    a.save()
                try:

                    carrera = a.carrera
                    # total=nivel.matriculados().count()
                    wb = xlwt.Workbook()
                    num_hoja=1
                    hoja='Registros'+str(num_hoja)
                    # ws = wb.add_sheet('Registros',cell_overwrite_ok=True)
                    ws = wb.add_sheet(hoja,cell_overwrite_ok=True)

                    telefono1=''
                    telefono2=''

                    ws.write_merge(0, 0,0,15, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,15, 'GESTION DE MORA POR CARRERA RUBROS NO PAGADOS Y ABONADOS - ARCHIVO ACTUALIZADO ' + str(datetime.now().date()),titulo2)
                    ws.write(3, 0,'CARRERA: ' +elimina_tildes(a.carrera.nombre) , subtitulo)
                    ws.write(6,0,"UNIDAD ACADEMICA",subtitulo3)
                    # ws.write(6,1,"PERIODO",subtitulo3)
                    # ws.write(6,2,"CARRERA",subtitulo3)
                    # ws.write_merge(6,6,3,6,"ESTUDIANTE",subtitulo3)
                    ws.write(6,1,"ESTUDIANTE",subtitulo3)
                    # ws.write(6,4,"NIVEL",subtitulo3)
                    ws.write(6,2,"TUTOR",subtitulo3)
                    ws.write(6,3,"GRUPO",subtitulo3)
                    ws.write(6,4,"TIPO DE RUBRO",subtitulo3)
                    ws.write(6,5,"VALOR",subtitulo3)
                    ws.write(6,6,"ABONO",subtitulo3)
                    ws.write(6,7,"SALDO",subtitulo3)
                    ws.write(6,8,"F. VENCIMIENTO",subtitulo3)
                    ws.write(6,9,"F. PAGO",subtitulo3)
                    ws.write(6,10,"F. ABONO",subtitulo3)
                    ws.write(6,11,"DIAS VENCIDOS",subtitulo3)
                    ws.write(6,12,"CALIFICACION",subtitulo3)
                    ws.write(6,13,"TEL.CELULAR",subtitulo3)
                    ws.write(6,14,"TEL.CONVENCIONAL",subtitulo3)
                    ws.write(6,15,"TIPO BECA",subtitulo3)
                    ws.write(6,16,"% BECA",subtitulo3)
                    ws.write(6,17,"GESTOR",subtitulo3)
                    m = 10
                    fila = 7
                    com = 7
                    todas=[]

                    # for rubro in  Rubro.objects.filter(inscripcion__carrera=c,cancelado=False,inscripcion__persona__usuario__is_active=True):
                    rubro_isncr=RubrosGestionMora.objects.filter(carrera_id = c.id)
                    for rubro in rubro_isncr:
                        inscripcionid= rubro.inscripcion_id
                        agregar = 0
                        if fila==65500:
                            num_hoja=num_hoja
                            hoja='Registros'+str(num_hoja+1)
                            num_hoja = num_hoja+1

                            ws = wb.add_sheet(hoja,cell_overwrite_ok=True)
                            fila=7
                        rbnombre=''
                        rbvalor=0
                        abono=0
                        saldo=0
                        pagototal=0
                        rbabono=0
                        rbfechavence=''
                        rbfechapago=''
                        rbfabono=''
                        diasvence=0
                        vencimiento=''
                        grupo=''
                        conbeca=''
                        telefono1=''
                        telefono2=''
                        tipobeca=''
                        porcientobeca=''
                        grupo2=''

                        try:
                            telefono_con = rubro.telefono_con
                            if telefono_con:
                                telefono1 = telefono_con.replace('-','').replace(' ','').replace('+','')
                            else:
                                telefono1=''
                        except Exception as ex:
                            pass

                        try:
                            telefono = rubro.telefono
                            if  telefono:
                                telefono2 = telefono.replace('-','').replace(' ','').replace('+','')
                            else:
                                telefono2=''
                        except Exception as ex:
                            pass

                        #para datos de beca
                        try:
                            tipobeca=''
                            porcientobeca=''
                            matricula_inscr= rubro.matricula_id
                            if matricula_inscr:
                                tipobeca = elimina_tildes(rubro.tipobeca)
                                porcientobeca = elimina_tildes(rubro.porcentaje)
                            # if Matricula.objects.filter(inscripcion= rubro.inscripcion,nivel__cerrado=False,becado=True).exists():
                            #     conbeca=Matricula.objects.filter(inscripcion= rubro.inscripcion,nivel__cerrado=False,becado=True).order_by('-id')[:1].get()
                            #     tipobeca=elimina_tildes(conbeca.tipobeca)
                            #     porcientobeca=str(conbeca.porcientobeca)
                        except Exception as ex:
                            pass
                        ws.write(fila,columna+15,tipobeca,subtitulo3)
                        ws.write(fila,columna+16,porcientobeca,subtitulo3)
                        try:
                            ws.write(fila, columna+17, rubro.nombreasistente)
                        except:
                            ws.write(fila, columna+17, '')
                        try:
                            inscripcion_grupo= rubro.inscripciongrupo_id
                            if inscripcion_grupo:
                                grupo2 = elimina_tildes(rubro.nombregrupo)
                            # if InscripcionGrupo.objects.get(inscripcion=rubro.inscripcion_id):
                            #     grupo=InscripcionGrupo.objects.get(inscripcion=rubro.inscripcion_id)
                            #     grupo2=elimina_tildes(grupo.grupo.nombre)
                            else:
                                grupo2=''
                        except Exception as ex:
                            pass

                        try:
                            rubro_tn =Rubro.objects.filter(pk= rubro.rubro_id)[:1].get()
                            if rubro_tn:
                                rubro_tipo = rubro_tn.tipo()
                                rubro_nombre = rubro_tn.nombre()
                                if rubro_tipo and rubro_nombre:
                                    rbnombre= str(elimina_tildes(rubro_tipo.replace('-','').replace(' ','').replace('+','')) + " " + elimina_tildes(rubro_nombre.replace('-','').replace(' ','').replace('+','').replace(u"\u2013",' ')))
                                else:
                                    rbnombre=''
                        except Exception as ex:
                            pass

                        rbvalor=rubro.valor
                        rbfechavence=rubro.fechavence
                        rubro_pago = Rubro.objects.filter(pk=rubro.rubro_id)[:1].get()

                        pago_rubro=Pago.objects.filter(rubro=rubro_pago).select_related('rubro').order_by('-fecha')
                        if pago_rubro:
                            abono=pago_rubro.filter().aggregate(Sum('valor'))['valor__sum']
                            rbfechaabono=pago_rubro.filter()[:1].get()
                            rbfabono=rbfechaabono.fecha
                            diasvence=(datetime.now().date()- rubro.fechavence).days
                            if diasvence<0:
                                diasvence=0
                            vencimiento = rubro_pago.diasvencimiento2()
                        else:
                            abono=0
                            diasvence=(datetime.now().date()- rubro.fechavence).days
                            if diasvence<0:
                                diasvence=0
                            vencimiento = rubro_pago.diasvencimiento2()
                        saldo=rubro.valor - abono
                        if rubro.valor==0:
                            vencimiento = "A1"
                        #RUBRO ADEUDADO
                        adeudado = rubro_pago.adeudado()
                        if vencimiento == "A1":
                            tota1 =  tota1 + Decimal(adeudado)
                            if not [rubro.inscripcion_id] in arreglo_tota1:# if not [rubro.inscripcion.id ] in arreglo_tota1:
                                arreglo_tota1.append(rubro.inscripcion_id)#     arreglo_tota1.append(rubro.inscripcion.id)


                        if vencimiento == "A2":
                            tota2 = tota2 + Decimal(adeudado)
                            if not [rubro.inscripcion_id] in arreglo_tota2: # if not [rubro.inscripcion.id ] in arreglo_tota2:
                                arreglo_tota1.append(rubro.inscripcion_id) #arreglo_tota2.append(rubro.inscripcion.id)
                                agregar = 1

                        if vencimiento == "A3":
                            tota3 = tota3 +  Decimal(adeudado)
                            if not [rubro.inscripcion_id ] in arreglo_tota3: #if not [rubro.inscripcion.id ] in arreglo_tota3:
                                arreglo_tota3.append(rubro.inscripcion_id) # arreglo_tota3.append(rubro.inscripcion.id)
                                agregar = 1

                        if vencimiento == "B1":
                            totb1 = totb1 +  Decimal(adeudado)
                            if not [rubro.inscripcion_id ] in arreglo_totb1: #if not [rubro.inscripcion.id ] in arreglo_totb1:
                                arreglo_totb1.append(rubro.inscripcion_id) #arreglo_totb1.append(rubro.inscripcion.id)
                                agregar = 1

                        if vencimiento == "B2":
                            totb2 = totb2 +  Decimal(adeudado)
                            if not [rubro.inscripcion_id ] in arreglo_totb2: #if not [rubro.inscripcion.id ] in arreglo_totb2:
                                arreglo_totb2.append(rubro.inscripcion_id) # arreglo_totb2.append(rubro.inscripcion.id)
                                agregar = 1

                        if vencimiento == "C1":
                            totc1 = totc1 +  Decimal(adeudado)
                            if not [rubro.inscripcion_id ] in arreglo_totc1: #if not [rubro.inscripcion.id ] in arreglo_totc1:
                                arreglo_totc1.append(rubro.inscripcion_id) # arreglo_totc1.append(rubro.inscripcion.id)
                                agregar = 1

                        if vencimiento == "C2":
                            totc2 = totc2 +  Decimal(adeudado)
                            if not [rubro.inscripcion_id ] in arreglo_totc2: # if not [rubro.inscripcion.id ] in arreglo_totc2:
                                arreglo_totc2.append(rubro.inscripcion_id) # arreglo_totc2.append(rubro.inscripcion.id)
                                agregar = 1

                        if vencimiento == "D":
                            totd = totd +  Decimal(adeudado)
                            if not [rubro.inscripcion_id ] in arreglo_totd: #if not [rubro.inscripcion.id ] in arreglo_totd:
                                arreglo_totd.append(rubro.inscripcion_id) #arreglo_totd.append(rubro.inscripcion.id)

                        if vencimiento == "E":
                            tote = tote +  Decimal(adeudado)
                            if not [rubro.inscripcion_id ] in arreglo_tote: #if not [rubro.inscripcion.id ] in arreglo_tote:
                                arreglo_tote.append(rubro.inscripcion_id)# arreglo_tote.append(rubro.inscripcion.id)
                                agregar = 1

                        try:
                            coordinacion_c =carrera.coordinacion_pertenece()
                            if coordinacion_c:
                                coord = elimina_tildes(coordinacion_c)
                            else:
                                coord= ''
                        except:
                            coord = ''

                        if not inscripcionid in todas:
                            todas.append(inscripcionid)

                        if agregar == 1:
                            if contaasi > contador -1 :
                                contaasi = 0
                            rubro_asis = Rubro.objects.filter(pk=rubro.rubro_id)[:1].get()
                            asistente = rubro_asis.inscripcion.asistente
                            if not asistente:
                                asis = AsistAsuntoEstudiant.objects.filter(pk=asistentes[contaasi]['id'])[:1].get()
                                rubro_asis.inscripcion.asistente = asis
                                rubro_asis.inscripcion.save()
                                contaasi = contaasi + 1
                            ### ANTES
                            # if not rubro.inscripcion.asistente:
                            #     asis = AsistAsuntoEstudiant.objects.filter(pk=asistentes[contaasi]['id'])[:1].get()
                            #     rubro.inscripcion.asistente = asis
                            #     rubro.inscripcion.save()
                            #     contaasi = contaasi +1

                        gruporubro = rubro.grupo_id
                        # grupo_ = InscripcionGrupo.objects.get(inscripcion=rubro.inscripcion)
                        tutor = ''
                        if NivelTutor.objects.filter(nivel__grupo=gruporubro).exists():
                            tutor = NivelTutor.objects.filter(nivel__grupo=gruporubro).order_by('-nivel__nivelmalla')[:1].get().tutor.persona.nombre_completo_inverso()
                        ws.write(fila,columna,coord,subtitulo3)
                        # ws.write(fila,columna+1,str(nv.periodo.nombre),subtitulo3)
                        # ws.write(fila,columna+2,str(nv.carrera.alias),subtitulo3)
                        ws.write(fila,columna+1,elimina_tildes(rubro.nombreestudiante), subtitulo)
                        ws.write(fila,columna+2,elimina_tildes(tutor), subtitulo)
                        # ws.write(fila,columna+4,str(nv.nivelmalla.nombre),subtitulo3)
                        ws.write(fila,columna+3,str(grupo2),subtitulo3)
                        ws.write(fila,columna + 13,telefono1, subtitulo3)
                        ws.write(fila,columna + 14,telefono2, subtitulo3)
                        #para datos de beca
                        ws.write(fila,columna+15,tipobeca,subtitulo3)
                        ws.write(fila,columna+16,porcientobeca,subtitulo3)

                        ws.write(fila,4,str(rbnombre))
                        ws.write(fila,5,rbvalor)
                        ws.write(fila,6,abono)
                        ws.write(fila,7,saldo)
                        ws.write(fila,8,str(rbfechavence))
                        ws.write(fila,9,str(rbfechapago))
                        ws.write(fila,10,str(rbfabono))
                        ws.write(fila,11,diasvence)
                        ws.write(fila,12,vencimiento)

                        fila = fila + 1

                    for inscripcionid in todas:
                        if inscripcionid in arreglo_tote:
                            if not inscripcionid  in insc_tote:
                                insc_tote.append(inscripcionid)
                                ins_tote.append(inscripcionid)

                        elif inscripcionid in arreglo_totd:
                            if not inscripcionid  in insc_totd:
                                insc_totd.append(inscripcionid)
                                ins_totd.append(inscripcionid)

                        elif inscripcionid in arreglo_totc2:
                            if not inscripcionid  in insc_totc2:
                                insc_totc2.append(inscripcionid)
                                ins_totc2.append(inscripcionid)

                        elif inscripcionid in arreglo_totc1:
                            if not inscripcionid  in insc_totc1:
                                insc_totc1.append(inscripcionid)
                                ins_totc1.append(inscripcionid)

                        elif inscripcionid in arreglo_totb2:
                            if not inscripcionid  in insc_totb2:
                                insc_totb2.append(inscripcionid)
                                ins_totb2.append(inscripcionid)

                        elif inscripcionid in arreglo_totb1:
                            if not inscripcionid  in insc_totb1:
                                insc_totb1.append(inscripcionid)
                                ins_totb1.append(inscripcionid)

                        elif inscripcionid in arreglo_tota3:
                            if not inscripcionid  in insc_tota3:
                                insc_tota3.append(inscripcionid)
                                ins_tota3.append(inscripcionid)

                        elif inscripcionid in arreglo_tota2:
                            if not inscripcionid  in insc_tota2:
                                insc_tota2.append(inscripcionid)
                                ins_tota2.append(inscripcionid)

                        elif inscripcionid in arreglo_tota1:
                            if not inscripcionid  in insc_tota1:
                                insc_tota1.append(inscripcionid)
                                ins_tota1.append(inscripcionid)
                    try:
                        if a.archivo_pendientes :
                            if (SITE_ROOT + '/' + str(a.archivo_pendientes )):
                                os.remove(SITE_ROOT + '/' + str(a.archivo_pendientes ))
                    except:
                        pass
                    nombre =str(elimina_tildes(a.carrera.nombre))+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'

                    a.ta1 = tota1
                    a.ta2 = tota2
                    a.ta3 = tota3
                    a.tb1 = totb1
                    a.tb2 = totb2
                    a.tc1 = totc1
                    a.tc2 = totc2
                    a.td = totd
                    a.te = tote
                    a.tea1 = len(arreglo_tota1)
                    a.tea2 = len(arreglo_tota2)
                    a.tea3 = len(arreglo_tota3)
                    a.teb1 = len(arreglo_totb1)
                    a.teb2 = len(arreglo_totb2)
                    a.tec1 = len(arreglo_totc1)
                    a.tec2 = len(arreglo_totc2)
                    a.ted = len(arreglo_totd)
                    a.tee = len(arreglo_tote)
                    a.save()
                    wb.save(MEDIA_ROOT+'/gestion/'+nombre)
                    a.archivo_pendientes=MEDIA_URL+'gestion/'+nombre
                    # a.fechaactualiza =datetime.now()
                    a.save()

                except Exception as e:
                    print("error2 ->" + str(e))

                carrera_tota1.setdefault(c.id,ins_tota1)
                carrera_tota2.setdefault(c.id,ins_tota2)
                carrera_tota3.setdefault(c.id,ins_tota3)
                carrera_totb1.setdefault(c.id,ins_totb1)
                carrera_totb2.setdefault(c.id,ins_totb2)
                carrera_totc1.setdefault(c.id,ins_totc1)
                carrera_totc2.setdefault(c.id,ins_totc2)
                carrera_totd.setdefault(c.id,ins_totd)
                carrera_tote.setdefault(c.id,ins_tote)

            coordinacion_tota1.setdefault(coordinacion.id,insc_tota1)
            coordinacion_tota2.setdefault(coordinacion.id,insc_tota2)
            coordinacion_tota3.setdefault(coordinacion.id,insc_tota3)
            coordinacion_totb1.setdefault(coordinacion.id,insc_totb1)
            coordinacion_totb2.setdefault(coordinacion.id,insc_totb2)
            coordinacion_totc1.setdefault(coordinacion.id,insc_totc1)
            coordinacion_totc2.setdefault(coordinacion.id,insc_totc2)
            coordinacion_totd.setdefault(coordinacion.id,insc_totd)
            coordinacion_tote.setdefault(coordinacion.id,insc_tote)
    except Exception as ex:
        print('ERROR REPORTE '+str(ex))


# -------------------------------------------------------RESUMEN------------------------------------------------------------------
    try:
        # coordinaciones = Coordinacion.objects.filter(id__in=Coordinacion.objects.filter(carrera__carrera=True, carrera__activo=True).values('id')).order_by('id')
        coordinaciones = Coordinacion.objects.filter(id__in=Coordinacion.objects.filter(carrera__id__in=carreras).values('id')).order_by('id')

        # carrera = a.carrera
            # total=nivel.matriculados().count()
        wb = xlwt.Workbook()
        num_hoja=1

        hoja='Resumen'
        # ws = wb.add_sheet('Registros',cell_overwrite_ok=True)
        ws = wb.add_sheet(hoja,cell_overwrite_ok=True)
        totga1 = 0
        totga2 = 0
        totga3 = 0
        totgb1 = 0
        totgb2 = 0
        totgc1 = 0
        totgc2 = 0
        totgd = 0
        totge = 0
        totgeneral = 0
        ws.write_merge(0, 0,0,8, 'CARTERA POR COBRAR '+elimina_tildes(tit.nombrecomercial) , titulo2)
        ws.write_merge(1, 1,1,4, 'TOTAL '+tit.nombrecomercial , titulo2)
        ws.write_merge(1, 1,5,7, 'TOTAL '+tit.nombrecomercial , titulo2)

        ws.write(2,0,"DIAS",subtitulo3)
        ws.write(2,1,"CALIFICACION",subtitulo3)
        ws.write(2,2,"MONTO",subtitulo3)
        ws.write(2,3,"%",subtitulo3)
        ws.write(2,4,"# PAGOS",subtitulo3)
        ws.write(2,5,"# ESTUDIANTES",subtitulo3)
        ws.write(2,6,"CATEGORIA",subtitulo3)
        ws.write(2,7,"MONTO",subtitulo3)
        ws.write(2,8,"%",subtitulo3)

        totga1 = ArchivoReporteCarrera.objects.all().aggregate(Sum('ta1'))['ta1__sum']
        totga2 = ArchivoReporteCarrera.objects.all().aggregate(Sum('ta2'))['ta2__sum']
        totga3 = ArchivoReporteCarrera.objects.all().aggregate(Sum('ta3'))['ta3__sum']
        totgb1 = ArchivoReporteCarrera.objects.all().aggregate(Sum('tb1'))['tb1__sum']
        totgb2 = ArchivoReporteCarrera.objects.all().aggregate(Sum('tb2'))['tb2__sum']
        totgc1 = ArchivoReporteCarrera.objects.all().aggregate(Sum('tc1'))['tc1__sum']
        totgc2 = ArchivoReporteCarrera.objects.all().aggregate(Sum('tc2'))['tc2__sum']
        totgd = ArchivoReporteCarrera.objects.all().aggregate(Sum('td'))['td__sum']
        totge = ArchivoReporteCarrera.objects.all().aggregate(Sum('te'))['te__sum']
        totgeneral = totga1 + totga2 + totga3 + totgb1 + totgb2 + totgc1 + totgc2 + totgd + totge

        totega1 = ArchivoReporteCarrera.objects.all().aggregate(Sum('tea1'))['tea1__sum']
        totega2 = ArchivoReporteCarrera.objects.all().aggregate(Sum('tea2'))['tea2__sum']
        totega3 = ArchivoReporteCarrera.objects.all().aggregate(Sum('tea3'))['tea3__sum']
        totegb1 = ArchivoReporteCarrera.objects.all().aggregate(Sum('teb1'))['teb1__sum']
        totegb2 = ArchivoReporteCarrera.objects.all().aggregate(Sum('teb2'))['teb2__sum']
        totegc1 = ArchivoReporteCarrera.objects.all().aggregate(Sum('tec1'))['tec1__sum']
        totegc2 = ArchivoReporteCarrera.objects.all().aggregate(Sum('tec2'))['tec2__sum']
        totegd = ArchivoReporteCarrera.objects.all().aggregate(Sum('ted'))['ted__sum']
        totege = ArchivoReporteCarrera.objects.all().aggregate(Sum('tee'))['tee__sum']
        totegeneral = totega1 + totega2 + totega3 + totegb1 + totegb2 + totegc1 + totegc2 + totegd + totege

        ws.write(3,0,"0",subtitulo3)
        ws.write(3,1,"A1",subtitulo3)
        ws.write(3,2,totga1)
        ws.write(3,3,Decimal((totga1 * 100) / totgeneral).quantize(Decimal(10)**-2))
        ws.write(3,4,totega1)
        # ws.write(3,5,len(insc_tota1) )
        a1 = 0
        for c in coordinacion_tota1:
            a1 = a1 + len(coordinacion_tota1[c])
        ws.write(3,5, a1)

        ws.write(4,0,"1-8",subtitulo3)
        ws.write(4,1,"A2",subtitulo3)
        ws.write(4,2,totga2)
        ws.write(4,3,Decimal((totga2 * 100) / totgeneral).quantize(Decimal(10)**-2))
        ws.write(4,4,totega2)
        # ws.write(4,10,len(insc_tota2) )
        a2 = 0
        for c in coordinacion_tota2:
            a2 = a2 + len(coordinacion_tota2[c])
        ws.write(4,5, a2)

        ws.write(5,0,"9-15",subtitulo3)
        ws.write(5,1,"A3",subtitulo3)
        ws.write(5,2,totga3)
        ws.write(5,3,Decimal((totga3 * 100) / totgeneral).quantize(Decimal(10)**-2))
        ws.write(5,4,totega3)
        # ws.write(5,10,len(insc_tota3) )
        a3 = 0
        for c in coordinacion_tota3:
            a3 = a3 + len(coordinacion_tota3[c])
        ws.write(5,5, a3)

        ws.write(6,0,"16-30",subtitulo3)
        ws.write(6,1,"B1",subtitulo3)
        ws.write(6,2,totgb1)
        ws.write(6,3,Decimal((totgb1 * 100) / totgeneral).quantize(Decimal(10)**-2))
        ws.write(6,4,totegb1)
        # ws.write(6,5,len(insc_totb1) )
        b1 = 0
        for c in coordinacion_totb1:
            b1 = b1 + len(coordinacion_totb1[c])
        ws.write(6,5, b1)

        ws.write(7,0,"31-45",subtitulo3)
        ws.write(7,1,"B2",subtitulo3)
        ws.write(7,2,totgb2)
        ws.write(7,3,Decimal((totgb2 * 100) / totgeneral).quantize(Decimal(10)**-2))
        ws.write(7,4,totegb2)
        # ws.write(7,5,len(insc_totb2) )
        b2 = 0
        for c in coordinacion_totb2:
            b2 = b2 + len(coordinacion_totb2[c])
        ws.write(7,5, b2)

        ws.write(8,0,"46-70",subtitulo3)
        ws.write(8,1,"C1",subtitulo3)
        ws.write(8,2,totgc1)
        ws.write(8,3,Decimal((totgc1 * 100) / totgeneral).quantize(Decimal(10)**-2))
        ws.write(8,4,totegc1)
        # ws.write(8,5,len(insc_totc1) )
        c1 = 0
        for c in coordinacion_totc1:
            c1 = c1 + len(coordinacion_totc1[c])
        ws.write(8,5, c1)

        ws.write(9,0,"71-90",subtitulo3)
        ws.write(9,1,"C2",subtitulo3)
        ws.write(9,2,totgc2)
        ws.write(9,3,Decimal((totgc2 * 100) / totgeneral).quantize(Decimal(10)**-2))
        ws.write(9,4,totegc2)
        # ws.write(9,5,len(insc_totc2) )
        c2 = 0
        for c in coordinacion_totc2:
            c2 = c2 + len(coordinacion_totc2[c])
        ws.write(9,5, c2)

        ws.write(10,0,"91-120",subtitulo3)
        ws.write(10,1,"D",subtitulo3)
        ws.write(10,2,totgd)
        ws.write(10,3,Decimal((totgd * 100) / totgeneral).quantize(Decimal(10)**-2))
        ws.write(10,4,totegd)
        # ws.write(10,5,len(insc_totd) )
        d = 0
        for c in coordinacion_totd:
            d = d + len(coordinacion_totd[c])
        ws.write(10,5, d)

        ws.write(11,0,">120",subtitulo3)
        ws.write(11,1,"E",subtitulo3)
        ws.write(11,2,totge)
        ws.write(11,3,Decimal((totge * 100) / totgeneral).quantize(Decimal(10)**-2))
        ws.write(11,4,totege)
        # ws.write(11,5,len(insc_tote) )
        e = 0
        for c in coordinacion_tote:
            e = e + len(coordinacion_tote[c])
        ws.write(11,5, e)

        ws.write(12,1,"Total General",subtitulo3)
        ws.write(12,2,totgeneral)
        ws.write(12,3,"100%")
        ws.write(12,4,totegeneral)
        # ws.write(12,5,len(insc_tota1) + len(insc_tota2) + len(insc_tota3) + len(insc_totb1) + len(insc_totb2) + len(insc_totc1) + len(insc_totc2) + len(insc_totd) + len(insc_tote))
        ws.write(12,5, a1+a2+a3+b1+b2+c1+c2+d+e)

        ws.write(3,6,"Programado",subtitulo3)
        ws.write(3,7,totga1)
        ws.write(3,8,Decimal((totga1 * 100) / totgeneral).quantize(Decimal(10)**-2))

        totgestionable = totga2 + totga3 + totgb1 + totgb2 + totgc1 + totgc2 + totgd
        ws.write(4,6,"Gestionable",subtitulo3)
        ws.write(4,7,totgestionable)
        ws.write(4,8,Decimal(((totgestionable / totgeneral)*100)).quantize(Decimal(10)**-2))

        ws.write(5,6,"Dificil de Recuperar",subtitulo3)
        ws.write(5,7,totge)
        ws.write(5,8,Decimal((totge * 100) / totgeneral).quantize(Decimal(10)**-2))
        if not ResumenCartera.objects.filter(fecha=datetime.now().date()).exists():
            resumen = ResumenCartera(programado = totga1,
                                     gestionable =totgestionable,
                                     dificil=totge,
                                     fecha=datetime.now().date())
            resumen.save()
        else:
            resumen = ResumenCartera.objects.filter(fecha=datetime.now().date())[:1].get()
            resumen.programado = totga1
            resumen.gestionable = totgestionable
            resumen.dificil =totge
            resumen.save()

        fila = 14
        for c in Coordinacion.objects.filter(id__in = coordinaciones).order_by('id'):
            # carreras = Carrera.objects.filter(id__in= c.carrera.all(), carrera=True, activo=True).values('id')
            carreras = Carrera.objects.filter(id__in=c.carrera.all()).values('id')

            ws.write_merge(fila+1, fila+1,0,4, 'TOTAL '+elimina_tildes(tit.nombrecomercial)+' '+elimina_tildes(c.nombre) , titulo2)
            ws.write_merge(fila+1, fila+1,5,8, 'TOTAL '+elimina_tildes(tit.nombrecomercial) , titulo2)

            ws.write(fila+2,0,"DIAS",subtitulo3)
            ws.write(fila+2,1,"CALIFICACION",subtitulo3)
            ws.write(fila+2,2,"MONTO",subtitulo3)
            ws.write(fila+2,3,"%",subtitulo3)
            ws.write(fila+2,4,"# PAGOS",subtitulo3)
            ws.write(fila+2,5,"# ESTUDIANTES",subtitulo3)
            ws.write(fila+2,6,"CATEGORIA",subtitulo3)
            ws.write(fila+2,7,"MONTO",subtitulo3)
            ws.write(fila+2,8,"%",subtitulo3)

            totga1 = ArchivoReporteCarrera.objects.filter(carrera__id__in=carreras).aggregate(Sum('ta1'))['ta1__sum']
            totga2 = ArchivoReporteCarrera.objects.filter(carrera__id__in=carreras).aggregate(Sum('ta2'))['ta2__sum']
            totga3 = ArchivoReporteCarrera.objects.filter(carrera__id__in=carreras).aggregate(Sum('ta3'))['ta3__sum']
            totgb1 = ArchivoReporteCarrera.objects.filter(carrera__id__in=carreras).aggregate(Sum('tb1'))['tb1__sum']
            totgb2 = ArchivoReporteCarrera.objects.filter(carrera__id__in=carreras).aggregate(Sum('tb2'))['tb2__sum']
            totgc1 = ArchivoReporteCarrera.objects.filter(carrera__id__in=carreras).aggregate(Sum('tc1'))['tc1__sum']
            totgc2 = ArchivoReporteCarrera.objects.filter(carrera__id__in=carreras).aggregate(Sum('tc2'))['tc2__sum']
            totgd = ArchivoReporteCarrera.objects.filter(carrera__id__in=carreras).aggregate(Sum('td'))['td__sum']
            totge = ArchivoReporteCarrera.objects.filter(carrera__id__in=carreras).aggregate(Sum('te'))['te__sum']
            totgeneral = totga1 + totga2 + totga3 + totgb1 + totgb2 + totgc1 + totgc2 + totgd + totge

            totega1 = ArchivoReporteCarrera.objects.filter(carrera__id__in=carreras).aggregate(Sum('tea1'))['tea1__sum']
            totega2 = ArchivoReporteCarrera.objects.filter(carrera__id__in=carreras).aggregate(Sum('tea2'))['tea2__sum']
            totega3 = ArchivoReporteCarrera.objects.filter(carrera__id__in=carreras).aggregate(Sum('tea3'))['tea3__sum']
            totegb1 = ArchivoReporteCarrera.objects.filter(carrera__id__in=carreras).aggregate(Sum('teb1'))['teb1__sum']
            totegb2 = ArchivoReporteCarrera.objects.filter(carrera__id__in=carreras).aggregate(Sum('teb2'))['teb2__sum']
            totegc1 = ArchivoReporteCarrera.objects.filter(carrera__id__in=carreras).aggregate(Sum('tec1'))['tec1__sum']
            totegc2 = ArchivoReporteCarrera.objects.filter(carrera__id__in=carreras).aggregate(Sum('tec2'))['tec2__sum']
            totegd = ArchivoReporteCarrera.objects.filter(carrera__id__in=carreras).aggregate(Sum('ted'))['ted__sum']
            totege = ArchivoReporteCarrera.objects.filter(carrera__id__in=carreras).aggregate(Sum('tee'))['tee__sum']
            totegeneral = totega1 + totega2 + totega3 + totegb1 + totegb2 + totegc1 + totegc2 + totegd + totege

            ws.write(fila+3,0,"0",subtitulo3)
            ws.write(fila+3,1,"A1",subtitulo3)
            ws.write(fila+3,2,totga1)
            ws.write(fila+3,3,Decimal((totga1 * 100) / totgeneral).quantize(Decimal(10)**-2))
            ws.write(fila+3,4,totega1 )
            ws.write(fila+3,5,len(coordinacion_tota1[c.id]) )

            ws.write(fila+4,0,"1-8",subtitulo3)
            ws.write(fila+4,1,"A2",subtitulo3)
            ws.write(fila+4,2,totga2)
            ws.write(fila+4,3,Decimal((totga2 * 100) / totgeneral).quantize(Decimal(10)**-2))
            ws.write(fila+4,4,totega2)
            ws.write(fila+4,5,len(coordinacion_tota2[c.id]) )

            ws.write(fila+5,0,"9-15",subtitulo3)
            ws.write(fila+5,1,"A3",subtitulo3)
            ws.write(fila+5,2,totga3)
            ws.write(fila+5,3,Decimal((totga3 * 100) / totgeneral).quantize(Decimal(10)**-2))
            ws.write(fila+5,4,totega3)
            ws.write(fila+5,5,len(coordinacion_tota3[c.id]) )

            ws.write(fila+6,0,"16-30",subtitulo3)
            ws.write(fila+6,1,"B1",subtitulo3)
            ws.write(fila+6,2,totgb1)
            ws.write(fila+6,3,Decimal((totgb1 * 100) / totgeneral).quantize(Decimal(10)**-2))
            ws.write(fila+6,4,totegb1)
            ws.write(fila+6,5,len(coordinacion_totb1[c.id]) )

            ws.write(fila+7,0,"31-45",subtitulo3)
            ws.write(fila+7,1,"B2",subtitulo3)
            ws.write(fila+7,2,totgb2)
            ws.write(fila+7,3,Decimal((totgb2 * 100) / totgeneral).quantize(Decimal(10)**-2))
            ws.write(fila+7,4,totegb2)
            ws.write(fila+7,5,len(coordinacion_totb2[c.id]) )

            ws.write(fila+8,0,"46-70",subtitulo3)
            ws.write(fila+8,1,"C1",subtitulo3)
            ws.write(fila+8,2,totgc1)
            ws.write(fila+8,3,Decimal((totgc1 * 100) / totgeneral).quantize(Decimal(10)**-2))
            ws.write(fila+8,4,totegc1)
            ws.write(fila+8,5,len(coordinacion_totc1[c.id]) )

            ws.write(fila+9,0,"71-90",subtitulo3)
            ws.write(fila+9,1,"C2",subtitulo3)
            ws.write(fila+9,2,totgc2)
            ws.write(fila+9,3,Decimal((totgc2 * 100) / totgeneral).quantize(Decimal(10)**-2))
            ws.write(fila+9,4,totegc2)
            ws.write(fila+9,5,len(coordinacion_totc2[c.id]) )

            ws.write(fila+10,0,"91-120",subtitulo3)
            ws.write(fila+10,1,"D",subtitulo3)
            ws.write(fila+10,2,totgd)
            ws.write(fila+10,3,Decimal((totgd * 100) / totgeneral).quantize(Decimal(10)**-2))
            ws.write(fila+10,4,totegd)
            ws.write(fila+10,5,len(coordinacion_totd[c.id]) )

            ws.write(fila+11,0,">120",subtitulo3)
            ws.write(fila+11,1,"E",subtitulo3)
            ws.write(fila+11,2,totge)
            ws.write(fila+11,3,Decimal((totge * 100) / totgeneral).quantize(Decimal(10)**-2))
            ws.write(fila+11,4,totege)
            ws.write(fila+11,5,len(coordinacion_tote[c.id]) )

            ws.write(fila+12,1,"Total General",subtitulo3)
            ws.write(fila+12,2,totgeneral)
            ws.write(fila+12,3,"100%")
            ws.write(fila+12,4,totegeneral)
            totales = len(coordinacion_tota1[c.id]) + len(coordinacion_tota2[c.id]) + len(coordinacion_tota3[c.id]) + len(coordinacion_totb1[c.id]) + len(coordinacion_totb2[c.id]) + len(coordinacion_totc1[c.id]) + len(coordinacion_totc2[c.id]) + len(coordinacion_totd[c.id]) + len(coordinacion_tote[c.id])
            ws.write(fila+12,5,totales)

            ws.write(fila+3,6,"Programado",subtitulo3)
            ws.write(fila+3,7,totga1)
            ws.write(fila+3,8,Decimal((totga1 * 100) / totgeneral).quantize(Decimal(10)**-2))

            totgestionable = totga2 + totga3 + totgb1 + totgb2 + totgc1 + totgc2 + totgd
            ws.write(fila+4,6,"Gestionable",subtitulo3)
            ws.write(fila+4,7,totgestionable)
            ws.write(fila+4,8,Decimal(((totgestionable / totgeneral)*100)).quantize(Decimal(10)**-2))

            ws.write(fila+5,6,"Dificil de Recuperar",subtitulo3)
            ws.write(fila+5,7,totge)
            ws.write(fila+5,8,Decimal((totge * 100) / totgeneral).quantize(Decimal(10)**-2))

            fila = fila+14

        for coord in Coordinacion.objects.filter(id__in = coordinaciones).order_by('id'):
            ws = wb.add_sheet(elimina_tildes(coord.nombre),cell_overwrite_ok=True)
            carreras = Carrera.objects.filter(coordinacion=coord).values('id')
            totgca1 = ArchivoReporteCarrera.objects.filter(carrera__id__in=carreras).aggregate(Sum('ta1'))['ta1__sum']
            totgca2 = ArchivoReporteCarrera.objects.filter(carrera__id__in=carreras).aggregate(Sum('ta2'))['ta2__sum']
            totgca3 = ArchivoReporteCarrera.objects.filter(carrera__id__in=carreras).aggregate(Sum('ta3'))['ta3__sum']
            totgcb1 = ArchivoReporteCarrera.objects.filter(carrera__id__in=carreras).aggregate(Sum('tb1'))['tb1__sum']
            totgcb2 = ArchivoReporteCarrera.objects.filter(carrera__id__in=carreras).aggregate(Sum('tb2'))['tb2__sum']
            totgcc1 = ArchivoReporteCarrera.objects.filter(carrera__id__in=carreras).aggregate(Sum('tc1'))['tc1__sum']
            totgcc2 = ArchivoReporteCarrera.objects.filter(carrera__id__in=carreras).aggregate(Sum('tc2'))['tc2__sum']
            totgcd = ArchivoReporteCarrera.objects.filter(carrera__id__in=carreras).aggregate(Sum('td'))['td__sum']
            totgce = ArchivoReporteCarrera.objects.filter(carrera__id__in=carreras).aggregate(Sum('te'))['te__sum']
            totgeneralcarrera = (totgca1) + (totgca2) + (totgca3) + (totgcb1) + (totgcb2) + (totgcc1) + (totgcc2) + (totgcd) + (totgce)
            ws.write_merge(0, 0,0,carreras.count()+6, elimina_tildes(coord.nombre), subtitulo3)
            ws.write_merge(1, 1,1,2,"Calificacion" , subtitulo3)
            ws.write(2,1,"Calificacion",subtitulo3)
            ws.write(2,2,"Dias",subtitulo3)
            ws.write(3,1,"A1",subtitulo3)
            ws.write(3,2,"0",subtitulo3)
            ws.write(4,1,"A2",subtitulo3)
            ws.write(4,2,"1-8",subtitulo3)
            ws.write(5,1,"A3",subtitulo3)
            ws.write(5,2,"9-15",subtitulo3)
            ws.write(6,1,"B1",subtitulo3)
            ws.write(6,2,"16-30",subtitulo3)
            ws.write(7,1,"B2",subtitulo3)
            ws.write(7,2,"31-45",subtitulo3)
            ws.write(8,1,"C1",subtitulo3)
            ws.write(8,2,"46-70",subtitulo3)
            ws.write(9,1,"C2",subtitulo3)
            ws.write(9,2,"71-90",subtitulo3)
            ws.write(10,1,"D",subtitulo3)
            ws.write(10,2,"91-120",subtitulo3)
            ws.write(11,1,"E",subtitulo3)
            ws.write(11,2,">120",subtitulo3)

            ws.write(3,4,"A1",subtitulo3)
            ws.write(4,4,"A2",subtitulo3)
            ws.write(5,4,"A3",subtitulo3)
            ws.write(6,4,"B1",subtitulo3)
            ws.write(7,4,"B2",subtitulo3)
            ws.write(8,4,"C1",subtitulo3)
            ws.write(9,4,"C2",subtitulo3)
            ws.write(10,4,"D",subtitulo3)
            ws.write(11,4,"E",subtitulo3)
            ws.write(12,4,"Total General",subtitulo3)

            ws.write(16,4,"A1",subtitulo3)
            ws.write(17,4,"A2",subtitulo3)
            ws.write(18,4,"A3",subtitulo3)
            ws.write(19,4,"B1",subtitulo3)
            ws.write(20,4,"B2",subtitulo3)
            ws.write(21,4,"C1",subtitulo3)
            ws.write(22,4,"C2",subtitulo3)
            ws.write(23,4,"D",subtitulo3)
            ws.write(24,4,"E",subtitulo3)
            col = 5
            archivo_carrera = ArchivoReporteCarrera.objects.filter(carrera__id__in=coord.carrera.all())
            for archi in archivo_carrera:
                totcarrera = archi.ta1 + archi.ta2 + archi.ta3 +archi.tb1 + archi.tb2 + archi.tc1 +archi.tc2 + archi.td + archi.te
                ws.write(2 ,col,elimina_tildes(archi.carrera.nombre), subtitulo3)
                ws.write(3 ,col,archi.ta1)
                ws.write(4 ,col,archi.ta2)
                ws.write(5 ,col,archi.ta3)
                ws.write(6 ,col,archi.tb1)
                ws.write(7 ,col,archi.tb2)
                ws.write(8 ,col,archi.tc1)
                ws.write(9 ,col,archi.tc2)
                ws.write(10 ,col,archi.td)
                ws.write(11 ,col,archi.te)
                ws.write(12 ,col,totcarrera)

                ws.write(15 ,col,elimina_tildes(archi.carrera.nombre), subtitulo3)
                ws.write(16 ,col,len(carrera_tota1[archi.carrera.id]))
                ws.write(17 ,col,len(carrera_tota2[archi.carrera.id]))
                ws.write(18 ,col,len(carrera_tota3[archi.carrera.id]))
                ws.write(19 ,col,len(carrera_totb1[archi.carrera.id]))
                ws.write(20 ,col,len(carrera_totb2[archi.carrera.id]))
                ws.write(21 ,col,len(carrera_totc1[archi.carrera.id]))
                ws.write(22 ,col,len(carrera_totc2[archi.carrera.id]))
                ws.write(23 ,col,len(carrera_totd[archi.carrera.id]))
                ws.write(24 ,col,len(carrera_tote[archi.carrera.id]))

                col = col + 1
            col = carreras.count()+5
            ws.write(2 ,col,"Total" + elimina_tildes(coord.nombre),subtitulo3)
            ws.write(3 ,col,totgca1,subtitulo3)
            ws.write(4 ,col,totgca2,subtitulo3)
            ws.write(5 ,col,totgca3,subtitulo3)
            ws.write(6 ,col,totgcb1,subtitulo3)
            ws.write(7 ,col,totgcb2,subtitulo3)
            ws.write(8 ,col,totgcc1,subtitulo3)
            ws.write(9 ,col,totgcc2,subtitulo3)
            ws.write(10 ,col,totgcd,subtitulo3)
            ws.write(11 ,col,totgce,subtitulo3)
            ws.write(12 ,col,totgeneralcarrera,subtitulo3)
            col = col + 1
            ws.write(2 ,col,"%" ,titulo2)
            ws.write(3 ,col,Decimal((totgca1/totgeneralcarrera)*100).quantize(Decimal(10)**-2),subtitulo3)
            ws.write(4 ,col,Decimal((totgca2/totgeneralcarrera)*100).quantize(Decimal(10)**-2),subtitulo3)
            ws.write(5 ,col,Decimal((totgca3/totgeneralcarrera)*100).quantize(Decimal(10)**-2),subtitulo3)
            ws.write(6 ,col,Decimal((totgcb1/totgeneralcarrera)*100).quantize(Decimal(10)**-2),subtitulo3)
            ws.write(7 ,col,Decimal((totgcb2/totgeneralcarrera)*100).quantize(Decimal(10)**-2),subtitulo3)
            ws.write(8 ,col,Decimal((totgcc1/totgeneralcarrera)*100).quantize(Decimal(10)**-2),subtitulo3)
            ws.write(9 ,col,Decimal((totgcc2/totgeneralcarrera)*100).quantize(Decimal(10)**-2),subtitulo3)
            ws.write(10 ,col,Decimal((totgcd/totgeneralcarrera)*100).quantize(Decimal(10)**-2),subtitulo3)
            ws.write(11 ,col,Decimal((totgce/totgeneralcarrera)*100).quantize(Decimal(10)**-2),subtitulo3)
            ws.write(12 ,col,Decimal((totgeneralcarrera/totgeneralcarrera)*100).quantize(Decimal(10)**-2),subtitulo3)
            fila = 15


        try:
            if os.path.exists(SITE_ROOT + '/media/gestion/'+'ReporteResumen.xls'):
                os.remove(SITE_ROOT + '/media/gestion/'+'ReporteResumen.xls')
        except Exception as ex:
            print('ERROR REPORTE MORA: '+str(ex))
            pass

        wb.save(MEDIA_ROOT+'/gestion/'+'ReporteResumen.xls')
        print('actualizaarchivo '+str(datetime.now().date())+' EJECUCION URL ACTUALIZA ARCHIVO FIN '+str(datetime.now())+' Tiempo de Duracion: {}'.format(datetime.now() - start_time))

        borrados = []
        hoy = datetime.now().date()
        if RubroSeguimiento.objects.filter(rubro__cancelado=False,fechaposiblepago__lt=hoy,fechapago=None, estado=True).exists():
            for rs in RubroSeguimiento.objects.filter(rubro__cancelado=False,fechaposiblepago__lt=hoy,fechapago=None, estado=True):
                sietediasdespues = rs.fechaposiblepago +  timedelta(7)
                if sietediasdespues < hoy:
                    borrados.append((rs.rubro.inscripcion.persona.nombre_completo(), rs.rubro.nombre(),rs.fechaposiblepago,rs.seguimiento.usuario))
                    rs.estado = False
                    rs.save()
            if borrados:
                email_gestiones_borradas(borrados)

        return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
    except Exception as e:
        print('ERROR REPORTE MORA-> '+str(e))
        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

def email_gestiones_borradas(borradas):
     if TipoIncidencia.objects.filter(pk=62).exists():
        tipo = TipoIncidencia.objects.get(pk=62)
        hoy = datetime.now().today()
        contenido = u"Gestiones dadas de baja"
        send_html_mail(contenido,
            "emails/gestiones_borradas.html", {'rubros':borradas,'fecha':hoy },tipo.correo.split(","))