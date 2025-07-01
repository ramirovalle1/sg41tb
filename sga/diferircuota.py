from itertools import chain
import json
from datetime import datetime, timedelta, date
from decimal import Decimal
from calendar import monthrange

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from settings import INICIO_DIFERIR, FECHA_INCIO_DIFERIR, FECHA_DIFERIR, MESES_DIFERIR, TIPO_CUOTA_RUBRO, FIN_DIFERIR
from sga.commonviews import addUserData

from sga.models import Inscripcion, Rubro, Pago, RubroOtro, DirferidoRubro, RubroCuota, ParametrosPromocion


@login_required(redirect_field_name='ret', login_url='/login')
@transaction.atomic()
def view(request):
    try:
        if request.method == 'POST':
            action = request.POST['action']
            if action == 'diferir':
                sid = transaction.savepoint()
                try:
                    inscripcion = Inscripcion.objects.get(id=request.POST['id'])
                    parametros = ParametrosPromocion.objects.filter()[:1].get()
                    # iniciodife = date(INICIO_DIFERIR[0], INICIO_DIFERIR[1],INICIO_DIFERIR[2])
                    iniciodife = parametros.iniciodiferir
                    findiferir = parametros.findiferir
                    # findiferir = date(FIN_DIFERIR[0], FIN_DIFERIR[1],FIN_DIFERIR[2])
                    idrub = {}
                    if RubroCuota.objects.filter(rubro__fechavence__gte=iniciodife, rubro__fechavence__lte=findiferir,
                                                 rubro__cancelado=True, rubro__inscripcion=inscripcion).exists() or \
                            RubroOtro.objects.filter(rubro__fechavence__gte=iniciodife,
                                                     rubro__fechavence__lte=findiferir, rubro__cancelado=True,
                                                     rubro__inscripcion=inscripcion, tipo__nombre='CUOTA'):
                        idrub1 = RubroCuota.objects.filter(rubro__fechavence__gte=iniciodife, rubro__fechavence__lte=findiferir,
                                                 rubro__cancelado=True, rubro__inscripcion=inscripcion).values_list('rubro',flat=True)
                        idrub2 = RubroOtro.objects.filter(rubro__fechavence__gte=iniciodife, rubro__fechavence__lte=findiferir,
                                                 rubro__cancelado=True, rubro__inscripcion=inscripcion).values_list('rubro',flat=True)
                        idrub = list(chain(idrub1, idrub2))
                    if idrub:
                        rubroactual = Rubro.objects.filter(id__in=idrub, inscripcion=inscripcion,cancelado=True).order_by('-fechavence')[:1].get()
                        fechahasta = date(rubroactual.fechavence.year,rubroactual.fechavence.month,1)
                        fechainicio = parametros.iniciodiferir
                        # fechainicio = date(FECHA_INCIO_DIFERIR[0], FECHA_INCIO_DIFERIR[1],FECHA_INCIO_DIFERIR[2])
                        fechadiferir = parametros.fechadiferir
                        # fechadiferir = date(FECHA_DIFERIR[0],FECHA_DIFERIR[1],FECHA_DIFERIR[2])
                        fechahasta = fechahasta - timedelta(days=1)
                        meses = int(request.POST['meses'])
                        rubros = Rubro.objects.filter(fechavence__gte=fechainicio, fechavence__lte=fechahasta,
                                                      cancelado=False, inscripcion=inscripcion)
                        sumarubro = rubros.aggregate(Sum('valor'))
                        sumapago = Pago.objects.filter(rubro__id__in=rubros.values('id')).aggregate(Sum('valor'))
                        sumapago = sumapago['valor__sum'] if sumapago['valor__sum'] else 0
                        sumarubro = sumarubro['valor__sum'] if sumarubro['valor__sum'] else 0
                        valor = sumarubro - sumapago
                        cuotaval = Decimal(valor/meses).quantize(Decimal(10)**-2)
                        rubrosliq = []
                        totacuato = Decimal(0)
                        for r in  rubros:
                            if r.total_pagado() > 0:
                                r.valor = float(r.total_pagado())
                            else:
                                r.valor = float(0)
                            r.cancelado = True
                            r.save()

                            rubrosliq.append(r.id)
                        rubrosdif = []
                        for i in range(meses):

                            if((i+1)==meses):
                                cuotaval = Decimal(valor) - Decimal(totacuato)
                            totacuato = totacuato + cuotaval
                            rubro = Rubro(fecha=datetime.today().date(),
                                          valor=cuotaval, inscripcion=inscripcion,
                                          cancelado=False, fechavence=fechadiferir)
                            rubro.save()
                            ro = RubroOtro(rubro=rubro, tipo_id=TIPO_CUOTA_RUBRO, descripcion='DIFERIDO CUOTA #' + str(i+1))
                            ro.save()
                            rubrosdif.append(rubro.id)
                            fechadiferir = date(fechadiferir.year, fechadiferir.month, fechadiferir.day)+ timedelta(days=monthrange(fechadiferir.year,fechadiferir.month)[1])
                        diferidorubro = DirferidoRubro(inscripcion=inscripcion,
                                                       fecha=datetime.now().date(),
                                                       rubrosactuales=rubrosdif,
                                                       rubrosanteriores=rubrosliq)
                        diferidorubro.save()
                        transaction.savepoint_commit(sid)
                        return HttpResponse(json.dumps({'result': 'ok'}), content_type='application/json')
                    return HttpResponse(json.dumps({'result': 'bad'}), content_type='application/json')
                except Exception as e:
                    transaction.savepoint_rollback(sid)
                    return HttpResponse(json.dumps({'result': 'bad', "error": str(e)}), content_type='application/json')

        else:
            data = {'title':'diferir'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']
            else:
                inscripcion = Inscripcion.objects.get(persona=data['persona'])
                parametros = ParametrosPromocion.objects.filter()[:1].get()
                # iniciodife = date(INICIO_DIFERIR[0], INICIO_DIFERIR[1],INICIO_DIFERIR[2])
                iniciodife = parametros.iniciodiferir
                findiferir = parametros.findiferir
                # findiferir = date(FIN_DIFERIR[0], FIN_DIFERIR[1],FIN_DIFERIR[2])
                idrub = {}
                if RubroCuota.objects.filter(rubro__fechavence__gte=iniciodife, rubro__fechavence__lte=findiferir,
                                             rubro__cancelado=True, rubro__inscripcion=inscripcion).exists() or \
                        RubroOtro.objects.filter(rubro__fechavence__gte=iniciodife,
                                                 rubro__fechavence__lte=findiferir, rubro__cancelado=True,
                                                 rubro__inscripcion=inscripcion, tipo__nombre='CUOTA').exists():
                    idrub1 = RubroCuota.objects.filter(rubro__fechavence__gte=iniciodife, rubro__fechavence__lte=findiferir,
                                             rubro__cancelado=True, rubro__inscripcion=inscripcion).values_list('rubro',flat=True)
                    idrub2 = RubroOtro.objects.filter(rubro__fechavence__gte=iniciodife, rubro__fechavence__lte=findiferir,
                                             rubro__cancelado=True, rubro__inscripcion=inscripcion, tipo__nombre='CUOTA').values_list('rubro',flat=True)
                    idrub = list(chain(idrub1, idrub2))
                if idrub:
                    rubroactual = Rubro.objects.filter(id__in=idrub, inscripcion=inscripcion,cancelado=True).order_by('-fechavence')[:1].get()
                    fechahasta = date(rubroactual.fechavence.year,rubroactual.fechavence.month,1)
                    fechainicio = parametros.iniciodiferir
                    # fechainicio = date(FECHA_INCIO_DIFERIR[0], FECHA_INCIO_DIFERIR[1],FECHA_INCIO_DIFERIR[2])
                    fechadiferir = parametros.fechadiferir
                    # fechadiferir = date(FECHA_DIFERIR[0],FECHA_DIFERIR[1],FECHA_DIFERIR[2])
                    fechainidiferir = parametros.fechadiferir
                    # fechainidiferir = date(FECHA_DIFERIR[0],FECHA_DIFERIR[1],FECHA_DIFERIR[2])
                    fechahasta = fechahasta - timedelta(days=1)
                    rubros = Rubro.objects.filter(fechavence__gte= fechainicio,fechavence__lte=fechahasta,cancelado=False,inscripcion=inscripcion)
                    sumarubro = rubros.aggregate(Sum('valor'))
                    sumapago = Pago.objects.filter(rubro__id__in=rubros.values('id')).aggregate(Sum('valor'))
                    sumapago = sumapago['valor__sum'] if sumapago['valor__sum'] else 0
                    sumarubro = sumarubro['valor__sum'] if sumarubro['valor__sum'] else 0
                    data['valordiferir'] = sumarubro - sumapago
                    data['FECHA_DIFERIR'] =  parametros.fechadiferir
                    # data['FECHA_DIFERIR'] = FECHA_DIFERIR
                    lista = []
                    for i in range(MESES_DIFERIR):
                        lista.append((i+1,str(fechadiferir)))
                        fechadiferir = date(fechadiferir.year,fechadiferir.month,fechadiferir.day) + timedelta(days=monthrange(fechadiferir.year,fechadiferir.month)[1])
                    data['meses_diferir'] = lista
                    data['inscripcion'] = inscripcion
                    data['fechainidiferir'] = fechainidiferir
                    return render(request ,"diferir/diferircuota.html" ,  data)
                else:
                    return HttpResponseRedirect('/?info=Debe cancelar algun rubro de cuota desde el mes de '+str(iniciodife) +' para diferir')
    except Exception as e:
        print('Error  diferircuota'+str(e))
        return HttpResponseRedirect('/?info=Error en excepcion comuniquese con el administrador')