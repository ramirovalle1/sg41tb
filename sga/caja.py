from datetime import datetime
from decimal import Decimal
import json
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Sum
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
import xlwt
from decorators import secure_module
from settings import ACEPTA_PAGO_EFECTIVO, ACEPTA_PAGO_TARJETA, ACEPTA_PAGO_CHEQUE, FACTURACION_ELECTRONICA, AMBIENTE_FACTURACION, VALIDA_IP_CAJA, FORMA_PAGO_CHEQUE, TIPO_NC_ANULACION, MEDIA_ROOT
from sga.commonviews import addUserData, ip_client_address
from sga.forms import SesionCajaForm, CierreSesionCajaForm
from sga.models import LugarRecaudacion, Pago, SesionCaja, CierreSesionCaja, IpRecaudLugar, NotaCreditoInstitucion, TituloInstitucion


@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    if request.method=='POST':
        action = request.POST['action']
        try:
            caja = LugarRecaudacion.objects.get(persona=request.session['persona'],activa=True)
        except :
            return HttpResponseRedirect("/")
        if action=='abrirsesion':
            f = SesionCajaForm(request.POST)
            if FACTURACION_ELECTRONICA:
                for lugar in LugarRecaudacion.objects.filter(puntoventa=caja.puntoventa).exclude(pk=caja.id):
                    if SesionCaja.objects.filter(caja=lugar,abierta=True).exists():
                       return HttpResponseRedirect("/?info=Este punto de emision ya se encuentra abierto")
            if f.is_valid() and not caja.esta_abierta():
                sc = SesionCaja(caja=caja, fecha=datetime.now(), hora=datetime.now().time(),
                                fondo=f.cleaned_data['fondo'],
                                facturaempieza=f.cleaned_data['facturaempieza'],
                                facturatermina=f.cleaned_data['facturaempieza'],
                                autorizacion=f.cleaned_data['autorizacion'],
                                abierta=True)
                sc.save()

        if action == 'generarexcel':
            print(request.POST)
            try:

                sesion = SesionCaja.objects.filter(pk=request.POST['sesion'])[:1].get()
                cierrecaja = CierreSesionCaja.objects.filter(sesion=sesion)[:1].get()
                print(33)
                borders = xlwt.Borders()
                borders.left = xlwt.Borders.THIN
                borders.right = xlwt.Borders.THIN
                borders.top = xlwt.Borders.THIN
                borders.bottom = xlwt.Borders.THIN
                titulo = xlwt.easyxf(
                    'font: name Times New Roman, colour black, bold on; borders: left thin, right thin, top thin, bottom thin')
                titul3 = xlwt.easyxf(
                    'font: name Times New Roman, colour black; borders: left thin, right thin, top thin, bottom thin')
                titul4 = xlwt.easyxf(
                    'font: name Times New Roman, colour black;')
                titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                titulocabecera = xlwt.easyxf('font: name Times New Roman, colour black, bold on; '
                                             'align: wrap on, vert centre, horiz center;'
                                             'pattern: pattern solid, fore_colour silver_ega;')
                titulocabecera2 = xlwt.easyxf('font: name Times New Roman, colour black, bold on; '
                                             'align: wrap on, vert centre, horiz center;'
                                             )
                titulo.font.height = 20 * 11
                titulocabecera.font.height = 20 * 11
                titulocabecera2.font.height = 20 * 11
                titulocabecera.borders = borders
                # titulocabecera2.borders = borders
                titulo2.font.height = 20 * 11
                subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                subtitulo.font.height = 20 * 10
                titulox = xlwt.easyxf(
                    'font: name Times New Roman, colour black, bold off; align: wrap off, vert centre')
                titulox.borders = borders

                celdaprogramas = xlwt.easyxf(
                    'font: name Times New Roman, colour black, bold off; align: wrap on, vert centre, horiz center')
                celdaprogramas.borders = borders

                wb = xlwt.Workbook()
                m = 0
                ws = wb.add_sheet('cierrecaja', cell_overwrite_ok=True)
                tit = TituloInstitucion.objects.all()[:1].get()
                ws.write_merge(0, 3, 0, m + 3, tit.nombre, titulocabecera2)
                pagoreferido = 0

                pagotarjetas =  0
                pagodeposito =  0
                totalpago =  0
                if Pago.objects.filter(sesion=sesion,referido=True).exists():
                    pagoreferido=Pago.objects.filter(sesion=sesion,referido=True).aggregate(Sum('valor'))['valor__sum']
                    pagoreferido = Decimal(pagoreferido).quantize(Decimal(10) ** -2)
                if Pago.objects.filter(sesion=sesion).exists():
                    pagotarjetas=sesion.total_tarjeta_sesion()
                    pagotarjetas = Decimal(pagotarjetas).quantize(Decimal(10) ** -2)
                    pagodeposito=sesion.total_deposito_sesion()+sesion.total_transferencia_sesion()
                    pagodeposito = Decimal(pagodeposito).quantize(Decimal(10) ** -2)
                    pagocheque=sesion.total_cheque_sesion()
                    pagocheque = Decimal(pagocheque).quantize(Decimal(10) ** -2)

                ws.write(4, 0, 'RESPONSABLE: ', titulocabecera2)
                ws.write(4, 1, cierrecaja.sesion.caja.persona.nombre_completo_inverso(), titul4)
                # total=Decimal(cierrecaja.totalrecaudado).quantize(Decimal(10) ** -2)
                # ws.write(5,0,'MONTO FACTURADO:' + total )
                ws.write(5, 0, 'FECHA DE LA CAJA:' , titulocabecera2)
                ws.write(5, 1, str(cierrecaja.sesion.fecha), titul4)
                ws.write(6, 0, 'FECHA DE CIERRE: ', titulocabecera2)
                ws.write(6, 1, str(cierrecaja.fecha), titul4)

                ws.write(8, 0, 'EFECTIVO EN CAJA', titulocabecera)
                ws.col(0).width = 10 * 1000

                ws.write(8, 1, 'DENOMINACION', titulocabecera)
                ws.col(1).width = 10 * 800

                ws.write(8, 2, 'CANTIDAD', titulocabecera)
                ws.col(2).width = 10 * 300

                ws.write(8, 3, 'VALORES EN DOLARES', titulocabecera)
                ws.col(3).width = 10 * 1000
                ##BILLETES

                ws.write(9, 0, 'BILLETES DE', titul3)
                ws.col(0).width = 10 * 1000
                ws.write(10, 0, 'BILLETES DE', titul3)
                ws.col(0).width = 10 * 1000
                ws.write(11, 0, 'BILLETES DE', titul3)
                ws.col(0).width = 10 * 1000
                ws.write(12, 0, 'BILLETES DE', titul3)
                ws.col(0).width = 10 * 1000
                ws.write(13, 0, 'BILLETES DE', titul3)
                ws.col(0).width = 10 * 1000
                ws.write(14, 0, 'BILLETES DE', titul3)
                ws.col(0).width = 10 * 1000
                ws.write(15, 0, 'BILLETES DE', titul3)
                ws.col(0).width = 10 * 1000
                ##VALES
                # ws.write(16, 0, 'VALES', titul3)
                # ws.col(0).width = 10 * 1000
                ##MONEDAS
                ws.write(17, 0, 'MONEDAS DE', titul3)
                ws.col(0).width = 10 * 1000
                ws.write(18, 0, 'MONEDAS DE', titul3)
                ws.col(0).width = 10 * 1000
                ws.write(19, 0, 'MONEDAS DE', titul3)
                ws.col(0).width = 10 * 1000
                ws.write(20, 0, 'MONEDAS DE', titul3)
                ws.col(0).width = 10 * 1000
                ws.write(21, 0, 'MONEDAS DE', titul3)
                ws.col(0).width = 10 * 1000
                ws.write(22, 0, 'MONEDAS DE', titul3)
                ws.col(0).width = 10 * 1000
                ##DENOMINACION
                ws.write(9, 1, 'US$ 100', titul3)
                ws.col(0).width = 10 * 1000
                ws.write(10, 1, 'US$ 50', titul3)
                ws.col(0).width = 10 * 1000
                ws.write(11, 1, 'US$ 20', titul3)
                ws.col(0).width = 10 * 1000
                ws.write(12, 1, 'US$ 10', titul3)
                ws.col(0).width = 10 * 1000
                ws.write(13, 1, 'US$ 5', titul3)
                ws.col(0).width = 10 * 1000
                ws.write(14, 1, 'US$ 2', titul3)
                ws.col(0).width = 10 * 1000
                ws.write(15, 1, 'US$ 1', titul3)
                ws.col(0).width = 10 * 1000
                ##VALES
                ws.write(16, 1, '', titul3)
                ws.write(16, 2, '', titul3)
                ws.write(16, 3, '', titul3)
                ws.col(0).width = 10 * 1000
                ##DENOMINACION
                ws.write(17, 1, 'CTV$ 0.01', titul3)
                ws.col(0).width = 10 * 1000
                ws.write(18, 1, 'CTV$ 0.05', titul3)
                ws.col(0).width = 10 * 1000
                ws.write(19, 1, 'CTV$ 0.10', titul3)
                ws.col(0).width = 10 * 1000
                ws.write(20, 1, 'CTV$ 0.25', titul3)
                ws.col(0).width = 10 * 1000
                ws.write(21, 1, 'CTV$ 0.5', titul3)
                ws.col(0).width = 10 * 1000
                ws.write(22, 1, 'US$ 1', titul3)
                ws.col(0).width = 10 * 1000
                ## CANTIDAD
                ##BILLETES

                if cierrecaja.bill100:
                    ws.write(9, 2, cierrecaja.bill100, titul3)
                    ws.write(9, 3, (cierrecaja.bill100) * 100, titul3)
                else:
                    cierrecaja.bill100 = 0
                    cierrecaja.bill100 = Decimal(cierrecaja.bill100).quantize(Decimal(10) ** -2)
                    ws.write(9, 2, '0', titul3)
                    ws.write(9, 3, '0', titul3)
                if cierrecaja.bill50:
                    ws.write(10, 2, cierrecaja.bill50, titul3)
                    ws.write(10, 3, (cierrecaja.bill50) * 50, titul3)
                else:
                    cierrecaja.bill50 = 0
                    cierrecaja.bill50 = Decimal(cierrecaja.bill50).quantize(Decimal(10) ** -2)
                    ws.write(10, 2, '0', titul3)
                    ws.write(10, 3, '0', titul3)
                if cierrecaja.bill20:
                    ws.write(11, 2, cierrecaja.bill20, titul3)
                    ws.write(11, 3, (cierrecaja.bill20) * 20, titul3)
                else:
                    cierrecaja.bill20 = 0
                    cierrecaja.bill20 = Decimal(cierrecaja.bill20).quantize(Decimal(10) ** -2)

                    ws.write(11, 2, '0', titul3)
                    ws.write(11, 3, '0', titul3)
                if cierrecaja.bill10:
                    ws.write(12, 2, cierrecaja.bill10, titul3)
                    ws.write(12, 3, (cierrecaja.bill10) * 10, titul3)
                else:
                    cierrecaja.bill10 = 0
                    cierrecaja.bill10 = Decimal(cierrecaja.bill10).quantize(Decimal(10) ** -2)

                    ws.write(12, 2, '0', titul3)
                    ws.write(12, 3, '0', titul3)
                if cierrecaja.bill5:
                    ws.write(13, 2, cierrecaja.bill5, titul3)
                    ws.write(13, 3, (cierrecaja.bill5) * 5, titul3)
                else:
                    cierrecaja.bill5 = 0
                    cierrecaja.bill5 = Decimal(cierrecaja.bill5).quantize(Decimal(10) ** -2)

                    ws.write(13, 2, '0', titul3)
                    ws.write(13, 3, '0', titul3)
                if cierrecaja.bill2:
                    ws.write(14, 2, cierrecaja.bill2, titul3)
                    ws.write(14, 3, (cierrecaja.bill2) * 2, titul3)
                else:
                    cierrecaja.bill2 = 0
                    cierrecaja.bill2 = Decimal(cierrecaja.bill2).quantize(Decimal(10) ** -2)

                    ws.write(14, 2, '0', titul3)
                    ws.write(14, 3, '0', titul3)
                if cierrecaja.bill1:

                    ws.write(15, 2, cierrecaja.bill1, titul3)
                    ws.write(15, 3, cierrecaja.bill1, titul3)
                else:
                    cierrecaja.bill1 = 0
                    cierrecaja.bill1 = Decimal(cierrecaja.bill1).quantize(Decimal(10) ** -2)

                    ws.write(15, 2, '0', titul3)
                    ws.write(15, 3, '0', titul3)
##monedas
                if cierrecaja.enmonedas1:
                    ws.write(17, 2, cierrecaja.enmonedas1, titul3)

                    ws.write(17, 3, (cierrecaja.enmonedas1) * 0.01, titul3)
                else:
                    cierrecaja.enmonedas1=0
                    cierrecaja.enmonedas1 = Decimal(cierrecaja.enmonedas1).quantize(Decimal(10) ** -2)

                    ws.write(17, 2, '0', titul3)
                    ws.write(17, 3, '0', titul3)
                if cierrecaja.enmonedas5:
                    ws.write(18, 2, cierrecaja.enmonedas5, titul3)
                    ws.write(18, 3, (cierrecaja.enmonedas5) * 0.05, titul3)
                else:
                    cierrecaja.enmonedas5=0
                    cierrecaja.enmonedas5 = Decimal(cierrecaja.enmonedas5).quantize(Decimal(10) ** -2)

                    ws.write(18, 2, '0', titul3)
                    ws.write(18, 3, '0', titul3)
                if cierrecaja.enmonedas10:
                    ws.write(19, 2, cierrecaja.enmonedas10, titul3)
                    ws.write(19, 3, (cierrecaja.enmonedas10) * 0.10, titul3)
                else:
                    cierrecaja.enmonedas10=0
                    cierrecaja.enmonedas10 = Decimal(cierrecaja.enmonedas10).quantize(Decimal(10) ** -2)

                    ws.write(19, 2, '0', titul3)
                    ws.write(19, 3, '0', titul3)
                if cierrecaja.enmonedas25:

                    ws.write(20, 2, cierrecaja.enmonedas25, titul3)
                    ws.write(20, 3, (cierrecaja.enmonedas25) * 0.25, titul3)
                else:
                    cierrecaja.enmonedas25=0
                    cierrecaja.enmonedas25 = Decimal(cierrecaja.enmonedas25).quantize(Decimal(10) ** -2)
                    ws.write(20, 2, '0', titul3)
                    ws.write(20, 3, '0', titul3)
                if cierrecaja.enmonedas50:

                    ws.write(21, 2, cierrecaja.enmonedas50, titul3)
                    ws.write(21, 3, (cierrecaja.enmonedas50) * 0.5, titul3)
                else:
                    cierrecaja.enmonedas50 = 0
                    cierrecaja.enmonedas50 = Decimal(cierrecaja.enmonedas50).quantize(Decimal(10) ** -2)

                    ws.write(21, 2, '0', titul3)
                    ws.write(21, 3, '0', titul3)
                if cierrecaja.enmonedas100:
                    ws.write(22, 2, cierrecaja.enmonedas100, titul3)
                    ws.write(22, 3, (cierrecaja.enmonedas100), titul3)
                else:
                    cierrecaja.enmonedas100=0
                    cierrecaja.enmonedas100 = Decimal(cierrecaja.enmonedas100).quantize(Decimal(10) ** -2)

                    ws.write(22, 2, '0', titul3)
                    ws.write(22, 3, '0', titul3)
                # por05= Decimal(0.5).quantize(Decimal(10) ** -2)
                por01= Decimal(0.01).quantize(Decimal(10) ** -2)
                por05= Decimal(0.05).quantize(Decimal(10) ** -2)
                por10= Decimal(0.1).quantize(Decimal(10) ** -2)
                por25= Decimal(0.25).quantize(Decimal(10) ** -2)
                por50= Decimal(0.5).quantize(Decimal(10) ** -2)
                # por100= Decimal(0.5).quantize(Decimal(10) ** -2)
                ##total efectivo
                if not cierrecaja.vale:
                    cierrecaja.vale=0
                    cierrecaja.vale = Decimal(cierrecaja.vale).quantize(Decimal(10) ** -2)
                else:
                    cierrecaja.vale = Decimal(cierrecaja.vale).quantize(Decimal(10) ** -2)
                ws.write(23, 0, 'TOTAL EFECTIVO', titulo)
                totalefectivo = Decimal(cierrecaja.bill1) + (Decimal(cierrecaja.bill2) * 2) + (Decimal(cierrecaja.bill5) * 5) + (
                        Decimal(cierrecaja.bill10) * 10) \
                                + (Decimal(cierrecaja.bill20) * 20) + (Decimal(cierrecaja.bill50) * 50) + (
                                        Decimal(cierrecaja.bill100) * 100) + Decimal(cierrecaja.vale) \
                                + Decimal(cierrecaja.enmonedas100) + (Decimal(cierrecaja.enmonedas5) * por05) + (Decimal(cierrecaja.enmonedas25) * por25) + (Decimal(cierrecaja.enmonedas10) * por10) \
                                + (Decimal(cierrecaja.enmonedas50) * por50) + (Decimal(cierrecaja.enmonedas1) * por01)
                totalefectivo = Decimal(totalefectivo).quantize(Decimal(10) ** -2)

                ws.write(23, 1, '', titulo)
                ws.write(23, 2, '', titulo)
                ws.write(23, 3, totalefectivo, titulo)
                ws.write(24, 0, 'CHEQUES A LA FECHA', titulo)
                ws.write(24, 1, '', titulo)
                ws.write(24, 2, '', titulo)
                ws.write(24, 3, cierrecaja.cheque, titulo)
                ws.write(25, 0, 'TOTAL TARJETAS CREDITO/DEBITO ', titulo)
                ws.write(25, 1, '', titulo)
                ws.write(25, 2, '', titulo)
                ws.write(25, 3, pagotarjetas, titulo)
                ws.write(26, 0, 'TOTAL DEPOSITO/TRANSFERENCIAS ', titulo)
                ws.write(26, 1, '', titulo)
                ws.write(26, 2, '', titulo)
                ws.write(26, 3, pagodeposito, titulo)
                ws.write(27, 0, 'REFERIDO ', titulo)
                ws.write(27, 1, '', titulo)
                ws.write(27, 2, '', titulo)
                ws.write(27, 3, pagoreferido, titulo)
                ws.write(28, 0, 'TOTAL EFECTIVO SISTEMA ', titulo)
                ws.write(28, 3, totalefectivo + pagotarjetas + pagodeposito + pagoreferido , titulo)
                ws.write(28, 1, '', titulo)
                ws.write(28, 2, '', titulo)
                ws.write(29, 0, 'VALES', titulo)
                ws.write(29, 3, cierrecaja.vale, titulo)
                ws.write(29, 2, '', titulo)
                ws.write(29, 1, '', titulo)
                ws.write(30, 0, 'TOTAL SESION ', titulo)
                ws.write(30, 3, totalefectivo + pagotarjetas + pagodeposito + pagoreferido-Decimal(cierrecaja.vale), titulo)
                ws.write(30, 1, '', titulo)
                ws.write(30, 2, '', titulo)
                ws.write(31, 0, 'FALTANTE ', titulo)
                ws.write(31, 3, cierrecaja.faltante,titulo)
                ws.write(31, 1, '', titulo)
                ws.write(31, 2, '', titulo)
                ws.write(32, 0, 'SOBRANTE ', titulo)
                ws.write(32, 3, cierrecaja.sobrante, titulo)
                ws.write(32, 1, '', titulo)
                ws.write(32, 2, '', titulo)
                ws.write(33, 0, 'OBSERVACION ', titulo)
                ws.write_merge(33, 33, 1, 3, cierrecaja.observacion, titul3)
                # ws.write(33, 3, cierrecaja.sobrante, titulo)
                nombre = 'cierresesiondecaja' + str(datetime.now()).replace(" ", "").replace(".", "").replace(":",
                                                                                                              "") + '.xls'
                wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}), content_type="application/json")

            except Exception as ex:
                print(str(ex))
                return HttpResponse(json.dumps({"result": str(ex)}), content_type="application/json")

        elif action == 'cerrarsesion':
            try:
                f = CierreSesionCajaForm(request.POST)
                pagos = 0
                sesion = 0

                print(request.POST)
                caja = SesionCaja.objects.filter(pk=request.POST['sesioncaja'])[:1].get()
                if f.is_valid() and caja.abierta:
                    cs = CierreSesionCaja(sesion=caja,
                                          bill100=f.cleaned_data['bill100'],
                                          bill50=f.cleaned_data['bill50'],
                                          bill20=f.cleaned_data['bill20'],
                                          bill10=f.cleaned_data['bill10'],
                                          bill5=f.cleaned_data['bill5'],
                                          bill2=f.cleaned_data['bill2'],
                                          bill1=f.cleaned_data['bill1'],
                                          # bill1=f.cleaned_data['bill1'],
                                          enmonedas1=f.cleaned_data['enmonedas1'],
                                          enmonedas5=f.cleaned_data['enmonedas5'],
                                          enmonedas10=f.cleaned_data['enmonedas10'],
                                          enmonedas25=f.cleaned_data['enmonedas25'],
                                          enmonedas50=f.cleaned_data['enmonedas50'],
                                          enmonedas100=f.cleaned_data['enmonedas100'],
                                          # referido=f.cleaned_data['referido'],
                                          vale=f.cleaned_data['vales'],
                                          tarjetas=f.cleaned_data['tarjetas'],
                                          # cs.totalrecaudado =
                                          faltante=f.cleaned_data['faltante'],
                                          sobrante=f.cleaned_data['sobrante'],
                                          observacion=f.cleaned_data['observacion'],
                                          totalrecaudado=f.cleaned_data['totalrecaudado'],
                                          # total = 0,
                                          # enmonedas=f.cleaned_data['enmonedas'],
                                          # deposito=f.cleaned_data['deposito'],
                                          fecha=datetime.now(),
                                          total=0,
                                          hora=datetime.now().time())
                    cs.save()

                    if 'pagoreferido' in request.POST:
                        cs.referido = Decimal(request.POST['pagoreferido']).quantize(Decimal(10) ** -2)

                    if 'totaltrarjeta' in request.POST:
                        cs.tarjetas = Decimal(request.POST['totaltrarjeta']).quantize(Decimal(10) ** -2)

                    if 'pagodeposito' in request.POST:
                        cs.deposito = Decimal(request.POST['pagodeposito']).quantize(Decimal(10) ** -2)

                    if 'pagocheque' in request.POST:
                        cs.cheque = Decimal(request.POST['pagocheque']).quantize(Decimal(10) ** -2)


                    # sc = caja

                    if Pago.objects.filter(sesion=caja).exists():

                        pagos = Pago.objects.filter(sesion=caja).aggregate(Sum('valor'))['valor__sum']

                    if NotaCreditoInstitucion.objects.filter(sesioncaja=caja, tipo__id=TIPO_NC_ANULACION).exists():


                        sesion = NotaCreditoInstitucion.objects.filter(sesioncaja=caja, tipo__id=TIPO_NC_ANULACION).aggregate(Sum('valor'))['valor__sum']
                        # sesion_numerico = 0
                        # if sesion is not None:
                        #     sesion_numerico = float(sesion)


                    if pagos > sesion:

                        cs.total = pagos - sesion
                    else:
                        print(988946)
                        cs.total = 0
                    cs.save()
                    print('entro')
                    # caja = caja.objects.filter(abierta=True).get()
                    caja.facturatermina -= 1
                    caja.abierta = False
                    caja.save()
                    return HttpResponseRedirect("/caja")
            except Exception as ex:
                print(ex)
                return HttpResponseRedirect("/?info=Error: " + str(ex))
        return HttpResponseRedirect('/caja')
    else:
        data = {}
        addUserData(request, data)
        if LugarRecaudacion.objects.filter(persona=data['persona'],activa=True).exists():
            lugarRecaudacion = LugarRecaudacion.objects.filter(persona=data['persona'],activa=True)[:1].get()
            data['caja'] = lugarRecaudacion
        else:
            return HttpResponseRedirect("/?info=Error")

        if 'action' in request.GET:
            action = request.GET['action']
            if action=='addsesion':
                lugarRecaudacion = LugarRecaudacion.objects.get(persona=data['persona'],activa=True)
                f=""
                data['vari']= 0
                if SesionCaja.objects.filter(caja=lugarRecaudacion).exists():
                    caja=SesionCaja.objects.filter(caja=lugarRecaudacion).order_by('-pk')[:1].get()


                if FACTURACION_ELECTRONICA:
                    # Log Editar Inscripcion
                    client_address = ip_client_address(request)
                    if VALIDA_IP_CAJA:
                        if not IpRecaudLugar.objects.filter(lugarrecaudacion=lugarRecaudacion,ip__ip=client_address).exists():
                            return HttpResponseRedirect("/?info=No puede Abrir Sesion de Caja desde este equipo")
                    nu=0
                    if lugarRecaudacion.numerofact==None:
                        nu=caja.facturatermina
                    else:
                        nu=lugarRecaudacion.numerofact
                    if AMBIENTE_FACTURACION==1:
                        f = SesionCajaForm(initial={'facturaempieza':(int(nu))})
                    else:
                        f = SesionCajaForm(initial={'facturaempieza':(int(nu)),'autorizacion':123456789})
                    data['AMBIENTE_FACTURACION']= AMBIENTE_FACTURACION
                    data['vari']= 1
                else:
                    f = SesionCajaForm()
                data['form'] = f
                return render(request ,"caja/adicionarbs.html" ,  data)
            elif action=='closesesion':
                 try:
                    f = CierreSesionCajaForm()
                    data['form'] = f
                    sesioncaja = SesionCaja.objects.filter(id=request.GET['id'])[:1].get()
                    data['sesioncaja'] = sesioncaja
                    pagoreferido=0
                    pagotarjetas=0


                    pagodeposito=0
                    pagocheque=0
                    totalpago=0
                    if Pago.objects.filter(sesion=sesioncaja,referido=True).exists():
                        pagoreferido=Pago.objects.filter(sesion=sesioncaja,referido=True).aggregate(Sum('valor'))['valor__sum']
                        pagoreferido = Decimal(pagoreferido).quantize(Decimal(10) ** -2)

                    if Pago.objects.filter(sesion=sesioncaja).exists():
                        # pagotarjetadebito=Pago.objects.filter(sesion=sesioncaja,formapago__id=3).aggregate(Sum('valor'))['valor__sum']
                        pagotarjetas=sesioncaja.total_tarjeta_sesion()
                        pagotarjetas = Decimal(pagotarjetas).quantize(Decimal(10) ** -2)
                        pagodeposito=sesioncaja.total_deposito_sesion()+sesioncaja.total_transferencia_sesion()
                        pagodeposito = Decimal(pagodeposito).quantize(Decimal(10) ** -2)
                        pagocheque=sesioncaja.total_cheque_sesion()
                        pagocheque = Decimal(pagocheque).quantize(Decimal(10) ** -2)

                    data['pagoreferido'] = pagoreferido
                    data['totaltrarjeta'] = pagotarjetas
                    data['pagodeposito'] = pagodeposito
                    data['pagocheque'] = pagocheque

                    data['totalpago'] = totalpago
                    # data['acc'] = request.GET['acc']
                    pagos = 0
                    sesion= 0
                    if Pago.objects.filter(sesion=sesioncaja).exists():

                        pagos = Pago.objects.filter(sesion=sesioncaja).aggregate(Sum('valor'))['valor__sum']
                    if NotaCreditoInstitucion.objects.filter(sesioncaja=sesioncaja,tipo__id=TIPO_NC_ANULACION).exists():
                        sesion = NotaCreditoInstitucion.objects.filter(sesioncaja=sesioncaja,tipo__id=TIPO_NC_ANULACION).aggregate(Sum('valor'))['valor__sum']
                    if pagos > sesion:
                        data['total'] = pagos - sesion
                    else:
                        data['total'] = 0
                    return render(request,"caja/cerrarsesionbs.html", data)
                 except Exception as ex:
                    print(ex)
                    return HttpResponseRedirect("/?info=Error: "+str(ex))
                 # return HttpResponseRedirect("/")
        else:
            try:
                lugarRecaudacion = LugarRecaudacion.objects.get(persona=data['persona'],activa=True)
                data['caja'] = lugarRecaudacion

                if FACTURACION_ELECTRONICA:
                    for lugar in LugarRecaudacion.objects.filter(puntoventa=lugarRecaudacion.puntoventa).exclude(pk=lugarRecaudacion.id):
                        if SesionCaja.objects.filter(caja=lugar,abierta=True).exists():
                           return HttpResponseRedirect("/?info=Este punto de emision ya se encuentra abierto")
                sesiones = SesionCaja.objects.filter(caja=lugarRecaudacion).order_by('-fecha','-hora')
                paging = Paginator(sesiones, 50)
                p = 1
                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                    sesionespagina = paging.page(p)
                except:
                    sesionespagina = paging.page(1)

                data['paging'] = paging
                data['page'] = sesionespagina
                data['sesiones'] = sesionespagina.object_list
                data['abierta'] = SesionCaja.objects.filter(caja=data['caja'], abierta=True)

                return render(request ,"caja/sesionesbs.html" ,  data)
            except Exception as ex:
                 return HttpResponseRedirect("/?info=Error: "+str(ex))

