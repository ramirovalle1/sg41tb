#!/usr/bin/env python
# Este archivo usa el encoding: utf-8
import calendar
import csv
from datetime import datetime
import os
import pandas as pd
# from dbfpy import dbf
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from django.http import HttpResponseRedirect
from django.shortcuts import render
import unicodedata
from decorators import secure_module
from settings import JR_USEROUTPUT_FOLDER, MEDIA_URL, TIPO_PERIODO_REGULAR, CENTRO_EXTERNO, MEDIA_ROOT
from sga.commonviews import addUserData
from sga.forms import DBFForm, DBFMesForm, SNIESEForm, SNIESEAnnoForm, DBFForm2
from sga.models import Factura, Pago, PagoCheque, MONTH_CHOICES, FacturaCancelada, ClienteFactura, Matricula

def elimina_tildes(s):
    return ''.join((c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn'))

@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    if request.method == 'POST':
        if request.POST['action']=='exportar':
            if not CENTRO_EXTERNO:
                f = DBFForm(request.POST)
            else:
                f = DBFForm2(request.POST)
            if f.is_valid():
                try:
                    # Generar DBF
                    output_folder = os.path.join(JR_USEROUTPUT_FOLDER,request.user.username)

                    caja = f.cleaned_data['caja']
                    formato = int(f.cleaned_data['formato'])

                    #Si es centro externo entonces obtener las fechas inicio y fin
                    if CENTRO_EXTERNO:
                        inicio = f.cleaned_data['inicio']
                        fin = f.cleaned_data['fin']
                    else:
                        fecha = f.cleaned_data['fecha']


                    if formato==1:
                        if CENTRO_EXTERNO:
                            fname = 'cg%s%s%s_%s%s%s-%s.dbf'%(str(inicio.year).zfill(4),str(inicio.month).zfill(2),str(inicio.day).zfill(2),str(fin.year).zfill(4),str(fin.month).zfill(2),str(fin.day).zfill(2),str(caja.id))
                        else:
                            fname = 'cg%s%s%s-%s.dbf'%(str(fecha.year).zfill(4),str(fecha.month).zfill(2),str(fecha.day).zfill(2),str(caja.id))
                    else:
                        fname = 'cg%s%s%s-%s.csv'%(str(fecha.year).zfill(4),str(fecha.month).zfill(2),str(fecha.day).zfill(2),str(caja.id))
                    df = ''
                    if formato==1:
                        if not CENTRO_EXTERNO:
                            field_spec = [
                                ('tipo','C', 1),
                                ('doc', 'C', 3),
                                ('cjf_sts_da', 'D'), # Fecha de generacion del archivo
                                ('cjf_nombre', 'C', 100), # Nombre del Alumno
                                ('cjf_matric', 'C', 10), # no
                                ('cjf_factur', 'C', 13), # Numero de Factura
                                ('cjf_efecti', 'N', 10, 2), # Efectivo
                                ('cjf_ch_val', 'N', 10, 2), # Valor Cheque
                                ('cjf_tc_val', 'N', 10, 2), # Tarjeta Credito
                                ('cjf_nc_val', 'N', 10, 2), # Nota Credito
                                ('cjf_tr_val', 'N', 10, 2), # Transferencia
                                ('cjf_dp_val', 'N', 10, 2), # Deposito
                                ('sum_det', 'N', 10, 2), # Suma de todos los valores
                                ('fecha1', 'D'), # Fecha generacion
                                ('fecha2', 'D'), # Fecha generacion
                                ('cjf_chf_va', 'N', 10, 2), # 0
                                ('cjf_ret_va', 'N', 10, 2), # 0
                                ('cod_carrer', 'N', 2),     # no
                                ('nom_carrer', 'C', 100),   # no
                                ('ruc', 'C', 13),           # no
                                ('unidad', 'C', 3)          # 3 primeros caracteres de la carrera
                            ]
                        else:
                            field_spec = [
                                ('factura', 'C', 15),
                                ('fecha', 'D'), # Fecha sesion caja
                                ('referencia', 'C', 100), # Referencia
                                ('tipoid', 'C', 1),           #Tipo IDentificacion
                                ('idcliente', 'C', 13),   #Identificacion
                                ('cliente', 'C', 100), # Nombre del cliente
                                ('EF', 'N', 10, 2), # Efectivo
                                ('CH', 'N', 10, 2), # Valor Cheque
                                ('TC', 'N', 10, 2), # Tarjeta Credito
                                ('NC', 'N', 10, 2), # Nota Credito
                                ('TR', 'N', 10, 2), # Transferencia
                                ('DP', 'N', 10, 2), # Deposito
                                ('TOTAL', 'N', 10, 2), # Suma de todos los valores
                                ('base0', 'N', 10, 2), # Base 0%
                                ('base12', 'N', 10, 2), # Base 12%
                                ('iva', 'N', 10, 2),    # Iva
                                ('banco', 'C', 100)          # banco
                            ]
                        df = pd.DataFrame(columns=[field[0] for field in field_spec])
                    else:
                        db_csv = csv.writer(open(os.path.join(output_folder, fname), "wb"))
                        db_csv.writerow(["Tipo","Doc","Fecha",
                                         "Nombre","Factura","Efectivo", "Cheque", "Tarjeta",
                                         "Recibo Caja", "Transferencia", "Deposito", "Total",
                                         "Carrera"])

                    # Guardar datos
                    if not CENTRO_EXTERNO:
                        sesiones = caja.sesion_fecha(fecha)
                        if sesiones:
                            for sesion in sesiones:
                                pagos = Pago.objects.filter(sesion=sesion)
                                for pago in pagos:

                                    if formato==1:
                                        # rec = db.newRecord()
                                        rec = {}

                                    rec_csv = []

                                    if pago.es_chequepostfechado():
                                        if formato==1:
                                            rec['tipo'] = '3'
                                        else:
                                            rec_csv.append('3')
                                    elif pago.es_chequevista():
                                        if formato==1:
                                            rec['tipo'] = '1'
                                        else:
                                            rec_csv.append('1')
                                    elif pago.es_recibocajainst():
                                        if formato==1:
                                            rec['tipo'] = 4
                                        else:
                                            rec_csv.append('4')
                                    else:
                                        if formato==1:
                                            rec['tipo'] = '1'
                                        else:
                                            rec_csv.append('1')


                                    if pago.es_especievalorada():
                                        if formato==1:
                                            rec['doc'] = 'CER'
                                        else:
                                            rec_csv.append('CER')
                                    else:
                                        if formato==1:
                                            rec['doc'] = 'FAC'
                                        else:
                                            rec_csv.append('FAC')

                                    if formato==1:
                                        rec['cjf_sts_da'] = sesion.fecha
                                    else:
                                        rec_csv.append(sesion.fecha)

                                    inscripcion = pago.rubro.inscripcion
                                    if inscripcion:
                                        if formato==1:
                                            rec['cjf_nombre'] = inscripcion.persona.nombre_completo().encode("ascii","ignore")
                                            rec['cjf_matric'] = ''
                                        else:
                                            rec_csv.append(inscripcion.persona.nombre_completo().encode("ascii","ignore"))

                                        factura = pago.dbf_factura()
                                        if factura:
                                            if formato==1:
                                                rec['cjf_factur'] = factura.dbf_numero()
                                            else:
                                                rec_csv.append(factura.dbf_numero())

                                            efec = pago.valor if pago.efectivo else 0
                                            chv = pago.valor if pago.es_chequevista() or pago.es_chequepostfechado() else 0
                                            tar = pago.valor if pago.es_tarjeta() else 0
                                            rc = pago.valor if pago.es_recibocajainst() else 0
                                            tr = pago.valor if pago.es_transferencia() else 0
                                            dp = pago.valor if pago.es_deposito() else 0

                                            if formato==1:
                                                rec['cjf_efecti'] = efec
                                                rec['cjf_ch_val'] = chv
                                                rec['cjf_tc_val'] = tar
                                                rec['cjf_nc_val'] = rc
                                                rec['cjf_tr_val'] = tr
                                                rec['cjf_dp_val'] = dp

                                                rec['sum_det'] = (efec + chv + tar + rc + tr + dp)
                                                rec['fecha1'] = sesion.fecha
                                                rec['fecha2'] = sesion.fecha
                                                rec['cjf_chf_va'] = 0
                                                rec['cjf_ret_va'] = 0

                                                rec['cod_carrer'] = 0
                                                rec['nom_carrer'] = ''
                                                rec['ruc'] = str(pago.id) # str(pago.id) # Solo como prueba
                                                rec['unidad'] = inscripcion.carrera.alias[0:3].upper()
                                                rec.store()
                                            else:
                                                rec_csv.append(efec)
                                                rec_csv.append(chv)
                                                rec_csv.append(tar)
                                                rec_csv.append(rc)
                                                rec_csv.append(tr)
                                                rec_csv.append(dp)
                                                rec_csv.append((efec + chv + tar + rc + tr + dp))
                                                rec_csv.append(inscripcion.carrera.nombre.encode("ascii","ignore"))
                                                db_csv.writerow(rec_csv)

                                        else:
                                            pass



                                    else:
                                        pass
                                    if formato == 1:
                                        df = df.append(rec, ignore_index=True)
                                # Cheques a la fecha cobrados este dia
                                pagos_cheques_post_hoy = Pago.objects.filter(pagocheque__protestado=False, sesion__caja=caja, pagocheque__fechacobro=fecha)
                                for pago in pagos_cheques_post_hoy:
                                    if not pago.es_chequepostfechado():
                                        continue
                                    if formato==1:
                                        # rec = db.newRecord()
                                        rec = {}
                                    rec_csv = []

                                    if pago.es_chequepostfechado():
                                        if formato==1:
                                            rec['tipo'] = '2'
                                        else:
                                            rec_csv.append('2')
                                    elif pago.es_recibocajainst():
                                        if formato==1:
                                            rec['tipo'] = '4'
                                        else:
                                            rec_csv.append('4')
                                    else:
                                        if formato==1:
                                            rec['tipo'] = '1'
                                        else:
                                            rec_csv.append('1')

                                    if pago.es_especievalorada():
                                        if formato==1:
                                            rec['doc'] = 'CER'
                                        else:
                                            rec_csv.append('CER')
                                    else:
                                        if formato==1:
                                            rec['doc'] = 'FAC'
                                        else:
                                            rec_csv.append('FAC')

                                    if formato==1:
                                        rec['cjf_sts_da'] = sesion.fecha
                                    else:
                                        rec_csv.append(sesion.fecha)

                                    inscripcion = pago.rubro.inscripcion
                                    if inscripcion:
                                        if formato==1:
                                            rec['cjf_nombre'] = inscripcion.persona.nombre_completo().encode("ascii","ignore")
                                            rec['cjf_matric'] = ''
                                        else:
                                            rec_csv.append(inscripcion.persona.nombre_completo().encode("ascii","ignore"))

                                        factura = pago.dbf_factura()
                                        if factura:
                                            if formato==1:
                                                rec['cjf_factur'] = factura.dbf_numero()
                                            else:
                                                rec_csv.append(factura.dbf_numero())

                                            efec = pago.valor if pago.efectivo else 0
                                            chv = pago.valor if pago.es_chequevista() or pago.es_chequepostfechado() else 0
                                            tar = pago.valor if pago.es_tarjeta() else 0
                                            rc = pago.valor if pago.es_recibocajainst() else 0
                                            tr = pago.valor if pago.es_transferencia() else 0
                                            dp = pago.valor if pago.es_deposito() else 0


                                            if formato==1:
                                                rec['cjf_efecti'] = efec
                                                rec['cjf_ch_val'] = chv
                                                rec['cjf_tc_val'] = tar
                                                rec['cjf_nc_val'] = rc
                                                rec['cjf_tr_val'] = tr
                                                rec['cjf_dp_val'] = dp

                                                rec['sum_det'] = round(efec + chv + tar + rc + tr + dp, 2)
                                                rec['fecha1'] = sesion.fecha
                                                rec['fecha2'] = sesion.fecha
                                                rec['cjf_chf_va'] = 0
                                                rec['cjf_ret_va'] = 0

                                                rec['cod_carrer'] = 0
                                                rec['nom_carrer'] = ''
                                                rec['ruc'] = str(pago.id) # Solo como prueba
                                                rec['unidad'] = inscripcion.carrera.alias[0:3].upper()
                                            else:
                                                rec_csv.append(efec)
                                                rec_csv.append(chv)
                                                rec_csv.append(tar)
                                                rec_csv.append(rc)
                                                rec_csv.append(tr)
                                                rec_csv.append(dp)
                                                rec_csv.append(round(efec + chv + tar + rc + tr + dp, 2))
                                                rec_csv.append(inscripcion.carrera.nombre.encode("ascii","ignore"))
                                                db_csv.writerow(rec_csv)
                                        else:
                                            pass

                                    if formato == 1:
                                        df = df.append(rec, ignore_index=True)
                                # Recibos de Caja
                                for rci in sesion.recibocajainstitucion_set.all():
                                    if formato==1:
                                        # rec = db.newRecord()
                                        rec = {}
                                    rec_csv = []

                                    if formato==1:
                                        rec['tipo'] = '5'
                                    else:
                                        rec_csv.append('5')


                                    if formato==1:
                                        rec['doc'] = 'RCF'
                                    else:
                                        rec_csv.append('RCF')

                                    if formato==1:
                                        rec['cjf_sts_da'] = rci.fecha
                                    else:
                                        rec_csv.append(rci.fecha)

                                    inscripcion = rci.inscripcion
                                    if inscripcion:
                                        if formato==1:
                                            rec['cjf_nombre'] = inscripcion.persona.nombre_completo().encode("ascii","ignore")
                                            rec['cjf_matric'] = ''
                                        else:
                                            rec_csv.append(inscripcion.persona.nombre_completo().encode("ascii","ignore"))

                                        if formato==1:
                                            rec['cjf_factur'] = ''
                                        else:
                                            rec_csv.append('')

                                        efec = 0
                                        chv = 0
                                        tar = 0
                                        rc = rci.valorinicial
                                        tr = 0
                                        dp = 0

                                        if formato==1:
                                            rec['cjf_efecti'] = efec
                                            rec['cjf_ch_val'] = chv
                                            rec['cjf_tc_val'] = tar
                                            rec['cjf_nc_val'] = rc
                                            rec['cjf_tr_val'] = tr
                                            rec['cjf_dp_val'] = dp

                                            rec['sum_det'] = round(efec + chv + tar + rc + tr + dp, 2)
                                            rec['fecha1'] = sesion.fecha
                                            rec['fecha2'] = sesion.fecha
                                            rec['cjf_chf_va'] = 0
                                            rec['cjf_ret_va'] = 0

                                            rec['cod_carrer'] = 0
                                            rec['nom_carrer'] = ''
                                            rec['ruc'] = str('') # str(pago.id) # Solo como prueba
                                            rec['unidad'] = inscripcion.carrera.alias[0:3].upper()
                                        else:
                                            rec_csv.append(efec)
                                            rec_csv.append(chv)
                                            rec_csv.append(tar)
                                            rec_csv.append(rc)
                                            rec_csv.append(tr)
                                            rec_csv.append(dp)
                                            rec_csv.append(round(efec + chv + tar + rc + tr + dp, 2))
                                            rec_csv.append(inscripcion.carrera.nombre.encode("ascii","ignore"))
                                            db_csv.writerow(rec_csv)



                                    else:
                                        pass
                                    if formato == 1:
                                        df = df.append(rec, ignore_index=True)

                        if formato==1:
                            df.to_dbf(os.path.join(output_folder, fname), index=False)

                        return HttpResponseRedirect("/".join([MEDIA_URL,'documentos','userreports',request.user.username, fname]))

                    else:
                        sesiones = caja.sesiones_fechas(inicio, fin)
                        if sesiones:
                            for sesion in sesiones:
                                pagos = Pago.objects.filter(sesion=sesion)
                                for pago in pagos:
                                    try:
                                        # rec = db.newRecord()
                                        rec = {}

                                        inscripcion = pago.rubro.inscripcion
                                        # print(sesion.fecha.strftime('%d-%m-%Y') + ' -> ' + str(inscripcion))
                                        nombre = inscripcion.persona.nombre_completo().replace(u'Ñ', 'N').replace(u'ñ','n')
                                        # print(nombre)

                                        factura = pago.dbf_factura()
                                        clientefactura = factura.cliente.nombre.replace(u'Ñ', 'N').replace(u'ñ','n')
                                        # print(clientefactura)

                                        if inscripcion:
                                            rec['referencia'] = elimina_tildes(nombre) + ' ' + elimina_tildes(pago.rubro.nombre())
                                            # print(elimina_tildes(nombre) + ' ' + elimina_tildes(pago.rubro.nombre() + ' idRubro: ' + str(pago.rubro.id)))

                                            rec['cliente'] = elimina_tildes(clientefactura)
                                            rec['idcliente'] = factura.cliente.ruc

                                            if len(factura.cliente.ruc) == 10:
                                                rec['tipoid'] = 'C'
                                            if len(factura.cliente.ruc) < 10:
                                                rec['tipoid'] = 'P'
                                            if len(factura.cliente.ruc) > 10:
                                                rec['tipoid'] = 'R'

                                            if factura:
                                                rec['factura'] = factura.dbf_numero_centroexterno()
                                                rec['fecha'] = sesion.fecha

                                                efec = pago.valor if pago.efectivo else 0
                                                chv = pago.valor if pago.es_chequevista() or pago.es_chequepostfechado() else 0
                                                tar = pago.valor if pago.es_tarjeta() else 0
                                                nc = pago.valor if pago.es_notacreditoinst() else 0
                                                tr = pago.valor if pago.es_transferencia() else 0
                                                dp = pago.valor if pago.es_deposito() else 0

                                                if formato==1:
                                                    rec['EF'] = efec
                                                    rec['CH'] = chv
                                                    rec['TC'] = tar
                                                    rec['NC'] = nc
                                                    rec['TR'] = tr
                                                    rec['DP'] = dp

                                                    rec['TOTAL'] = (efec + chv + tar + nc + tr + dp)
                                                    rec['base0'] = (efec + chv + tar + nc + tr + dp)
                                                    rec['base12'] = 0
                                                    rec['iva'] = 0

                                                    if chv and pago.es_chequevista():
                                                        rec['banco'] = pago.chequevista().banco.nombre
                                                    if chv and pago.es_chequepostfechado():
                                                        rec['banco'] = pago.chequepostfechado().banco.nombre


                                            else:
                                                pass

                                        else:
                                            pass
                                        df = df.append(rec, ignore_index=True)
                                    except Exception as ex:
                                        # print(str(ex) + ' -> ' + str(pago.rubro.id))
                                        return HttpResponseRedirect("/dbf?error="+str(ex) + ' -> ' + str(pago.id))

                        if df:
                            df.to_dbf(os.path.join(output_folder, fname), index=False)

                        # camino = "\\".join([MEDIA_ROOT,"exportaciones", fname])

                        return HttpResponseRedirect("/".join([MEDIA_URL,'documentos','userreports',request.user.username, fname]))

                except Exception as ex:
                    print(ex)
                    return HttpResponseRedirect("/dbf?error="+str(ex))
            else:
                return HttpResponseRedirect("/dbf?error=1")

        elif request.POST['action']=='exportarsniese':
            f = SNIESEForm(request.POST)
            if f.is_valid():
                periodo = f.cleaned_data['periodo']

                output_folder = os.path.join(JR_USEROUTPUT_FOLDER,request.user.username)
                fname = 'sniese-%s.csv'%(periodo.nombre)

                db_csv = csv.writer(open(os.path.join(output_folder, fname), "wb"))
                db_csv.writerow(["PERIODO","SEDE","CARRERA",
                                 "SESION","NIVEL","CREDITOS MATRICULADOS", "CEDULA",
                                 "APELLIDO 1", "APELLIDO 2", "NOMBRES",
                                 "DIRECCION", "TELEFONO1", "TELEFONO2", "EMAIL",
                                 "GENERO"])
                matriculas = Matricula.objects.filter(nivel__periodo=periodo)
                for matricula in matriculas:
                    rec_csv = []
                    rec_csv.append(periodo.nombre.encode("utf-8"))
                    rec_csv.append(matricula.nivel.sede.nombre.encode("utf-8"))
                    rec_csv.append(str(matricula.nivel.carrera).encode("utf-8"))
                    rec_csv.append(str(matricula.nivel.sesion).encode("utf-8"))
                    rec_csv.append(matricula.nivel.nivelmalla.nombre.encode("utf-8"))
                    rec_csv.append(matricula.cantidad_creditos())
                    rec_csv.append(matricula.inscripcion.persona.cedula)
                    rec_csv.append(matricula.inscripcion.persona.apellido1.encode("utf-8"))
                    rec_csv.append(matricula.inscripcion.persona.apellido2.encode("utf-8"))
                    rec_csv.append(matricula.inscripcion.persona.nombres.encode("utf-8"))
                    rec_csv.append(matricula.inscripcion.persona.direccion_completa().encode("utf-8"))
                    rec_csv.append(matricula.inscripcion.persona.telefono.encode("utf-8"))
                    rec_csv.append(matricula.inscripcion.persona.telefono_conv.encode("utf-8"))
                    rec_csv.append(matricula.inscripcion.persona.email.encode("utf-8"))
                    rec_csv.append(matricula.inscripcion.persona.sexo.nombre.encode("utf-8"))
                    db_csv.writerow(rec_csv)

                return HttpResponseRedirect("/".join([MEDIA_URL,'documentos','userreports',request.user.username, fname]))
            else:
                return HttpResponseRedirect("/dbf?error=1")

        elif request.POST['action']=='exportarsnieseanno':
            f = SNIESEAnnoForm(request.POST)
            if f.is_valid():
                annomatricula = f.cleaned_data['annomatricula']

                output_folder = os.path.join(JR_USEROUTPUT_FOLDER,request.user.username)
                fname = '%s_MNF.csv'%(str(annomatricula))

                db_csv = csv.writer(open(os.path.join(output_folder, fname), "wb"))
                db_csv.writerow(["CARRERA",
                                 "CEDULA",
                                 "APELLIDO 1", "APELLIDO 2", "NOMBRES",
                                 "DIRECCION", "TELEFONO1", "TELEFONO2", "EMAIL",
                                 "GENERO"])
                matriculas = Matricula.objects.filter(Q(nivel__inicio__year=annomatricula) |
                                                      Q(nivel__fin__year=annomatricula), nivel__periodo__tipo__id=TIPO_PERIODO_REGULAR).distinct("inscripcion")

                for matricula in matriculas:
                    rec_csv = []

                    rec_csv.append(str(matricula.nivel.carrera).encode("utf-8"))
                    rec_csv.append(matricula.inscripcion.persona.cedula)
                    rec_csv.append(matricula.inscripcion.persona.apellido1.encode("utf-8"))
                    rec_csv.append(matricula.inscripcion.persona.apellido2.encode("utf-8"))
                    rec_csv.append(matricula.inscripcion.persona.nombres.encode("utf-8"))
                    rec_csv.append(matricula.inscripcion.persona.direccion_completa().encode("utf-8"))
                    rec_csv.append(matricula.inscripcion.persona.telefono.encode("utf-8"))
                    rec_csv.append(matricula.inscripcion.persona.telefono_conv.encode("utf-8"))
                    rec_csv.append(matricula.inscripcion.persona.email.encode("utf-8"))
                    rec_csv.append(matricula.inscripcion.persona.sexo.nombre.encode("utf-8"))
                    db_csv.writerow(rec_csv)

                return HttpResponseRedirect("/".join([MEDIA_URL,'documentos','userreports',request.user.username, fname]))
            else:
                return HttpResponseRedirect("/dbf?error=1")

        elif request.POST['action']=='exportarmes':
            f = DBFMesForm(request.POST)
            if f.is_valid():
                try:
                    mes = int(f.cleaned_data['mes'])
                    anno = int(f.cleaned_data['anno'])
                    tipoexp = int(f.cleaned_data['tipoexp'])
                    output_folder = os.path.join(JR_USEROUTPUT_FOLDER,request.user.username)
                    fname = ''
                    if tipoexp==1:
                        fname = 'anuladas-%s.dbf'%(MONTH_CHOICES[mes-1][1])
                    elif tipoexp==2:
                        fname = 'ventas-%s.dbf'%(MONTH_CHOICES[mes-1][1])
                    elif tipoexp==3:
                        fname = 'facturas-%s.dbf'%(MONTH_CHOICES[mes-1][1])
                    df = ''
                    if tipoexp==1:
                        # db = dbf.Dbf(os.path.join(output_folder, fname), new=True)
                        field_spec = [

                            ('Periodo','C', 4),
                            ('Mes', 'N', 2),
                            ('TipoCompro', 'C', 2),
                            ('Establec', 'C', 3),
                            ('PtoEmision', 'C', 3),
                            ('Inicio', 'C', 9),
                            ('Fin', 'C', 9),
                            ('Autoriza', 'C', 12)
                        ]
                        df = pd.DataFrame(columns=[field[0] for field in field_spec])

                        start_date = datetime(anno, mes, 1)
                        end_date = datetime(anno, mes, calendar.mdays[mes])
                        anuladas = FacturaCancelada.objects.filter(fecha__gte=start_date, fecha__lte=end_date).distinct("factura__id")
                        for f in anuladas:
                            # rec = db.newRecord()
                            rec = {}
                            rec['Periodo'] = str(anno)
                            rec['Mes'] = mes
                            rec['TipoCompro'] = '01'
                            rec['Establec'] = f.factura.numero[0:3]
                            rec['PtoEmision'] = f.factura.numero[4:7]
                            rec['Inicio'] = f.factura.numero[8:]
                            rec['Fin'] = f.factura.numero[8:]
                            rec['Autoriza'] = f.sesion.autorizacion if f.sesion else ''
                            # rec.store()
                            df = df.append(rec, ignore_index=True)
                        # db.close()
                    elif tipoexp==2:
                        # db = dbf.Dbf(os.path.join(output_folder, fname), new=True)
                        field_spec = [
                            ('Periodo','C', 4),
                            ('Mes', 'N', 2),
                            ('TpIdClient', 'C', 2),
                            ('IdCliente', 'C', 13),
                            ('TipoCompro', 'C', 2),
                            ('NumCompro', 'N', 7),
                            ('bNoGraIva', 'N', 12, 2),
                            ('bImponible', 'N', 12, 2),
                            ('bImpGrav', 'N', 12, 2),
                            ('MontoIva', 'N', 12, 2),
                            ('ValRetIva', 'N', 12, 2),
                            ('ValRetRent', 'N', 12, 2),
                            ('Cliente', 'C',100)
                        ]
                        df = pd.DataFrame(columns=[field[0] for field in field_spec])

                        start_date = datetime(anno, mes, 1)
                        end_date = datetime(anno, mes, calendar.mdays[mes])
                        clientes = ClienteFactura.objects.filter(factura__fecha__gte=start_date,factura__fecha__lte=end_date).distinct()
                        for c in clientes:
                            # rec = db.newRecord()
                            rec = {}
                            rec['Periodo'] = str(anno)
                            rec['Mes'] = mes
                            rec['TpIdClient'] = fn_tipoid(c)
                            rec['IdCliente'] = c.ruc
                            rec['TipoCompro'] = '01'
                            facturas = Factura.objects.filter(cliente=c, fecha__gte=start_date, fecha__lte=end_date, valida=True)

                            rec['NumCompro'] = facturas.count()
                            rec['bNoGraIva'] = 0
                            total = facturas.aggregate(Sum('total'))
                            rec['bImponible'] = total['total__sum'] if total['total__sum'] else 0
                            rec['bImpGrav'] = 0
                            rec['MontoIva'] = 0
                            rec['ValRetIva'] = 0
                            rec['ValRetRent'] = 0
                            rec['Cliente'] = elimina_tildes(c.nombre)
                            df = df.append(rec, ignore_index=True)
                    elif tipoexp==3:
                        # db = dbf.Dbf(os.path.join(output_folder, fname), new=True)
                        field_spec = [
                            ('Periodo','C', 4),
                            ('Mes', 'N', 2),
                            ('TpIdClient', 'C', 2),
                            ('IdCliente', 'C', 13),
                            ('TipoCompro', 'C', 2),

                            ('PtoVenta', 'C', 3),
                            ('NumFac', 'C', 20),
                            ('Autoriza', 'C', 20),

                            ('bNoGraIva', 'N', 12, 2),
                            ('bImponible', 'N', 12, 2),
                            ('bImpGrav', 'N', 12, 2),
                            ('MontoIva', 'N', 12, 2),
                            ('ValRetIva', 'N', 12, 2),
                            ('ValRetRent', 'N', 12, 2)
                        ]
                        df = pd.DataFrame(columns=[field[0] for field in field_spec])

                        start_date = datetime(anno, mes, 1)
                        end_date = datetime(anno, mes, calendar.mdays[mes])
                        clientes = ClienteFactura.objects.filter(factura__fecha__gte=start_date,factura__fecha__lte=end_date).distinct()
                        for c in clientes:

                            facturas = Factura.objects.filter(cliente=c, fecha__gte=start_date, fecha__lte=end_date, valida=True)

                            for factura in facturas:
                                rec = {}
                                rec['Periodo'] = str(anno)
                                rec['Mes'] = mes
                                rec['TpIdClient'] = fn_tipoid(c)
                                rec['IdCliente'] = c.ruc
                                rec['TipoCompro'] = '01'

                                rec['PtoVenta'] = factura.numero[0:3]
                                rec['NumFac'] = factura.numero
                                rec['Autoriza'] = factura.sesion().autorizacion if factura.sesion() else ""

                                rec['bNoGraIva'] = 0
                                rec['bImponible'] = factura.total
                                rec['bImpGrav'] = 0
                                rec['MontoIva'] = 0
                                rec['ValRetIva'] = 0
                                rec['ValRetRent'] = 0
                                df = df.append(rec, ignore_index=True)
                    if df:
                        df.to_dbf(os.path.join(output_folder, fname), index=False)


                    return HttpResponseRedirect("/".join([MEDIA_URL,'documentos','userreports',request.user.username, fname]))
                except Exception as ex:
                    return HttpResponseRedirect("/dbf?error="+str(ex))
            else:
                return HttpResponseRedirect("/dbf?error=1")


        return HttpResponseRedirect("/dbf")
    else:
        data = {}
        addUserData(request,data)
        if not CENTRO_EXTERNO:
            data['form'] = DBFForm(initial={'fecha': datetime.today()})
        else:
            data['form'] = DBFForm2(initial={'inicio': datetime.today(), 'fin': datetime.today()})

        data['formmes'] = DBFMesForm(initial={'fechainicio': datetime.today(), 'fechafin': datetime.today()})
        data['formsniese'] = SNIESEForm()
        data['formsnieseanno'] = SNIESEAnnoForm()
        data['centroexterno']=CENTRO_EXTERNO
        return render(request ,"dbf/archivo.html" ,  data)


def fn_tipoid(cliente):
    if cliente.ruc in ['9999999999','9999999999999']:
        return '07'
    elif len(cliente.ruc)<10:
        return '06'
    elif len(cliente.ruc)==10:
        return '05'
    elif len(cliente.ruc)==13:
        return '04'
    return '05'