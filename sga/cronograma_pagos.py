from datetime import datetime
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.forms import model_to_dict
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.utils.encoding import force_str
from decorators import secure_module
from sga.commonviews import addUserData
from sga.forms import PagoCalendarioForm, PagoCalendarioEditForm
from sga.models import PagoCalendario, Periodo, PagoNivel, Nivel, RubroCuota


@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    if request.method=='POST':
        if 'action' in request.POST:
            action = request.POST['action']
            if action=='addpagos':
                periodo = Periodo.objects.get(pk=request.POST['id'])
                f = PagoCalendarioForm(request.POST)
                if f.is_valid():
                    pagocal = PagoCalendario(periodo=periodo, tipo=f.cleaned_data['tipo'],fecha=f.cleaned_data['fecha'],valor=f.cleaned_data['valor'])
                    pagocal.save()

                    # Log de ADICIONAR PAGOS NIVEL
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(pagocal.periodo).pk,
                        object_id       = pagocal.id,
                        object_repr     = force_str(pagocal),
                        action_flag     = ADDITION,
                        change_message  = 'Adicionado Pago Calendario' )

                    # ADICIONAR CUOTA EN TODOS LOS NIVELES DEL PERIODO
                    for n in Nivel.objects.filter(periodo=periodo):
                        if n.pagonivel_set.filter(tipo=pagocal.tipo).exists():
                            pn = n.pagonivel_set.filter(tipo=pagocal.tipo)[:1].get()
                            pn.fecha = pagocal.fecha
                            pn.valor = pagocal.valor
                            pn.save()
                        else:
                            pn = PagoNivel(nivel=n, fecha=pagocal.fecha, valor=pagocal.valor, tipo=pagocal.tipo)
                            pn.save()

                    return HttpResponseRedirect("/cronogramapagos")
                else:
                    return HttpResponseRedirect("/cronogramapagos?action=addpagos")
            elif action=='editpagos':
                pagocal = PagoCalendario.objects.get(pk=request.POST['id'])
                periodo = pagocal.periodo
                f = PagoCalendarioEditForm(request.POST)
                if f.is_valid():
                    pagocal.fecha=f.cleaned_data['fecha']
                    pagocal.valor=f.cleaned_data['valor']
                    pagocal.save()

                    # Log de EDITAR PAGOS NIVEL
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(pagocal.periodo).pk,
                        object_id       = pagocal.id,
                        object_repr     = force_str(pagocal),
                        action_flag     = CHANGE,
                        change_message  = 'Modificado Cronograma Pago Periodo' )

                    # Buscar PagoNivel de este periodo y actualizarles fecha y valor
                    for pn in PagoNivel.objects.filter(nivel__periodo=periodo, tipo=pagocal.tipo):
                        pn.fecha = pagocal.fecha
                        pn.valor = pagocal.valor
                        pn.save()

                    # Buscar Rubros y actualizarles la fecha de vencimiento
                    for r in RubroCuota.objects.filter(matricula__nivel__periodo=periodo, cuota=pagocal.tipo):
                        r.rubro.fechavence = pagocal.fecha
                        r.rubro.save()

                    return HttpResponseRedirect("/cronogramapagos")
                else:
                    return HttpResponseRedirect("/cronogramapagos?action=editpagos&id="+request.POST['id'])

        return HttpResponseRedirect("/cronogramapagos")
    else:

        data = {'title': 'Niveles Academicos'}
        addUserData(request,data)

        if 'action' in request.GET:
            action = request.GET['action']
            if action=='addpagos':
                data['title'] = 'Adicionar Fecha de Pago al Periodo Academico'
                data['periodo'] = request.session['periodo']
                fecha = datetime.now()
                data['form']= PagoCalendarioForm(initial={'fecha':fecha})
                data['form'].excluir_tipos(data['periodo'])
                return render(request ,"cronograma_pagos/addpagosbs.html" ,  data)
            elif action=='delpagos':
                pagocal = PagoCalendario.objects.get(pk=request.GET['id'])
                periodo = pagocal.periodo
                tipo = pagocal.tipo

                # BORRAR EN TODOS LOS NIVELES
                for n in Nivel.objects.filter(periodo=periodo):
                    pns = n.pagonivel_set.filter(tipo=tipo)
                    pns.delete()

                # Log de EDITAR PAGOS NIVEL
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(pagocal.periodo).pk,
                    object_id       = pagocal.id,
                    object_repr     = force_str(pagocal),
                    action_flag     = DELETION,
                    change_message  = 'Borrar Cronograma Pago Periodo' )

                pagocal.delete()
                return HttpResponseRedirect("/cronogramapagos")
            elif action=='editpagos':
                data['title'] = 'Editar Cronograma de Pagos del Periodo'
                pagocal = PagoCalendario.objects.get(pk=request.GET['id'])
                data['periodo'] = pagocal.periodo
                data['tipo'] = pagocal.nombre
                initial = model_to_dict(pagocal)
                data['form'] = PagoCalendarioEditForm(initial=initial)
                data['pagocal'] = pagocal
                return render(request ,"cronograma_pagos/editarpagosbs.html" ,  data)
            return HttpResponseRedirect("/cronogramapagos")
        else:
            data['title'] = 'Cronograma de Pagos del Nivel Academico'
            data['pagos'] = PagoCalendario.objects.filter(periodo=request.session['periodo'])
            return render(request ,"cronograma_pagos/pagosbs.html" ,  data)