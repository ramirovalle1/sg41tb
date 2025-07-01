# -*- coding: latin-1 -*-
from datetime import datetime
from decimal import Decimal
import json
from django.contrib.auth.decorators import login_required
from django.forms.models import model_to_dict
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from decorators import secure_module
from settings import MODELO_EVALUACION, EVALUACION_CASADE, INSCRIPCION_CONDUCCION,PROFE_PRACT_CONDUCCION
from sga.commonviews import addUserData
from sga.forms import RolPagoForm
from sga.models import  RolPago, RolPagoProfesor, PrestamoInstitucional
from sga.commonviews import ip_client_address
from django.contrib.admin.models import LogEntry, ADDITION,CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_str
def convertir_fecha(s):
    return datetime(int(s[6:10]), int(s[3:5]), int(s[0:2])).date()


@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    if request.method=='POST':
        action = request.POST['action']
        if action=='add':
            f = RolPagoForm(request.POST)
            if f.is_valid():
                rolpago = RolPago(nombre=f.cleaned_data['nombre'],
                                  inicio=f.cleaned_data['inicio'],
                                  fin=f.cleaned_data['fin'],
                                  fecha=datetime.now().date(),
                                  fechamax=f.cleaned_data['fechamax'],
                                  fechamaxvin=f.cleaned_data['fechamaxvin'],
                                  tablatarifa=f.cleaned_data['tablatarifa'])
                rolpago.save()
                rolpago.calcular_rolpagoprofesor()

                #OCastillo 23-02-2023 log en esta accion
                #Obtain client ip address
                client_address = ip_client_address(request)
                # Log de Creacion de rol
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(rolpago).pk,
                    object_id       = rolpago.id,
                    object_repr     = force_str(rolpago),
                    action_flag     = ADDITION,
                    change_message  = 'Creacion de rol '+' (' + client_address + ')'  )
            else:
                return HttpResponseRedirect("/rol_pago?action=add")

        elif action == 'activacion':
            d = RolPago.objects.get(pk=request.POST['id'])
            if not d.cerrado:
                d.fechacierre = datetime.now()
            d.cerrado = not d.cerrado
            d.save()
            return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")

        elif action=='edit':
            rolpago = RolPago.objects.get(pk=request.POST['id'])
            f = RolPagoForm(request.POST)
            if f.is_valid():
                rolpago.nombre = f.cleaned_data['nombre']
                rolpago.inicio = f.cleaned_data['inicio']
                rolpago.fin = f.cleaned_data['fin']
                rolpago.fechamax = f.cleaned_data['fechamax']
                rolpago.fechamaxvin = f.cleaned_data['fechamaxvin']
                rolpago.tablatarifa = f.cleaned_data['tablatarifa']
                rolpago.save()
                rolpago.calcular_rolpagoprofesor()

                #OCastillo 23-02-2023 log en esta accion
                #Obtain client ip address
                client_address = ip_client_address(request)
                # Log de Edicion de rol
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(rolpago).pk,
                    object_id       = rolpago.id,
                    object_repr     = force_str(rolpago),
                    action_flag     = CHANGE,
                    change_message  = 'Modificacion de rol '+' (' + client_address + ')'  )

            else:
                return HttpResponseRedirect("/rol_pago?action=edit"+str(rolpago.id))

        elif action=='borrar':
            rolpago = RolPago.objects.get(pk=request.POST['id'])
            rolpago.activo = False
            rolpago.save()

            #OCastillo 23-02-2023 log en esta accion
            #Obtain client ip address
            client_address = ip_client_address(request)
            # Log de Eliminar rol
            LogEntry.objects.log_action(
                user_id         = request.user.pk,
                content_type_id = ContentType.objects.get_for_model(rolpago).pk,
                object_id       = rolpago.id,
                object_repr     = force_str(rolpago),
                action_flag     = DELETION,
                change_message  = 'Eliminacion de rol '+' (' + client_address + ')'  )

            return HttpResponseRedirect("/rol_pago")

        elif action=='calcular':
            try:
                rolpago = RolPago.objects.get(pk=request.POST['id'])
                rolpago.calcular_rolpagoprofesor()  #recalcular todos los valores de rol de pagos de  los profesores
                return HttpResponse(json.dumps({'result':'ok', "rolpago": str(rolpago.id)}),content_type="application/json")
            except Exception as ex :
                return HttpResponse(json.dumps({'result':'bad', "error": str(ex)}),content_type="application/json")

        elif action=='prestamoss':
            rolpagoprofesor = RolPagoProfesor.objects.get(pk=request.POST['rpp'])
            valor = float(request.POST['valor'])
            rolpagoprofesor.prestamoss = valor
            rolpagoprofesor.save()
            rolpagoprofesor.rolpagodetalleprofesor_set.all().delete()
            rolpagoprofesor.recalcular()
            return HttpResponse(json.dumps({'result': 'ok', 'sueldopercibir': '$ %.2f'%(rolpagoprofesor.salario_con_descuento())}),content_type="application/json")

        elif action=='descuentoinst':
            rolpagoprofesor = RolPagoProfesor.objects.get(pk=request.POST['rpp'])
            #Descuentos
            desc = rolpagoprofesor.modelo_descuento()
            pia = desc.prestamoinst
            if request.POST['id']=='0':
                desc.prestamoinst = None
                desc.descuentoprestamoinst = 0
                desc.save()
                if pia:
                    pia.recalcula()
            else:
                pi = PrestamoInstitucional.objects.get(pk=request.POST['id'])
                desc.prestamoinst = pi
                desc.descuentoprestamoinst = pi.proximo_descuento()
                desc.save()
                if pia:
                    pia.recalcula()
                if pi:
                    pi.recalcula()

            # rolpagoprofesor.rolpagodetalleprofesor_set.all().delete()
            rolpagoprofesor.recalcular()

            return HttpResponse(json.dumps({"result": "ok",
                                            "proximodescuento": "$ %.2f"%(desc.descuentoprestamoinst),
                                            "totaldesc": str(desc.totaldesc),
                                            "salariopercibir": str(rolpagoprofesor.salariopercibir)}))

        elif action=='actualizadias':
            rolpagoprofesor = RolPagoProfesor.objects.get(pk=request.POST['rppid'])
            rolpagoprofesor.dias = int(request.POST['nuevosdias'])
            rolpagoprofesor.save()
            rolpagoprofesor.recalcular()
            #Ingresos
            salariomesnuevo = rolpagoprofesor.salariomes
            totalinggravados = rolpagoprofesor.totalinggravados
            totalingresos = rolpagoprofesor.total_ingresos_general()
            bonifaciondocencia = rolpagoprofesor.diferenciavalor
            #Descuentos
            desc = rolpagoprofesor.modelo_descuento()
            iess = desc.iess
            totaldesc = desc.totaldesc
            #Total percibir
            salariopercibir = rolpagoprofesor.salariopercibir
            return HttpResponse(json.dumps({'result':'ok',
                                            "nuevosdiastrabajados": str(rolpagoprofesor.dias),
                                            "nuevosalariomes": str(salariomesnuevo),
                                            "totalinggrav": str(totalinggravados),
                                            "totalingresos": str(totalingresos),
                                            "bonificaciondocencia": str(bonifaciondocencia),
                                            "iess": str(iess),
                                            "totaldesc": str(totaldesc),
                                            "salariopercibir": str(salariopercibir)}),content_type="application/json")

        elif action=='tutorias':
            rolpagoprofesor = RolPagoProfesor.objects.get(pk=request.POST['rppid'])
            rolpagoprofesor.tutorias = Decimal(request.POST['valortutorias'])
            rolpagoprofesor.save()
            rolpagoprofesor.recalcular()
            #Ingresos
            totalinggravados = rolpagoprofesor.totalinggravados
            totalingresos = rolpagoprofesor.total_ingresos_general()
            #Descuentos
            desc = rolpagoprofesor.modelo_descuento()
            iess = desc.iess
            totaldesc = desc.totaldesc
            #Total percibir
            salariopercibir = rolpagoprofesor.salariopercibir
            return HttpResponse(json.dumps({'result':'ok',
                                            "nuevovalortutorias": str(rolpagoprofesor.tutorias),
                                            "totalinggrav": str(totalinggravados),
                                            "totalingresos": str(totalingresos),
                                            "iess": str(iess),
                                            "totaldesc": str(totaldesc),
                                            "salariopercibir": str(salariopercibir)}),content_type="application/json")

        elif action=='horasextras':
            rolpagoprofesor = RolPagoProfesor.objects.get(pk=request.POST['rppid'])
            rolpagoprofesor.hextrass = Decimal(request.POST['valorhextrass'])
            rolpagoprofesor.hextrase = Decimal(request.POST['valorhextrase'])
            rolpagoprofesor.save()
            rolpagoprofesor.recalcular()
            #Ingresos
            totalinggravados = rolpagoprofesor.totalinggravados
            totalingresos = rolpagoprofesor.total_ingresos_general()
            #Descuentos
            desc = rolpagoprofesor.modelo_descuento()
            iess = desc.iess
            totaldesc = desc.totaldesc
            #Total percibir
            salariopercibir = rolpagoprofesor.salariopercibir
            return HttpResponse(json.dumps({'result':'ok',
                                            "nuevovalorhextras": str(rolpagoprofesor.horas_extras()),
                                            "totalinggrav": str(totalinggravados),
                                            "totalingresos": str(totalingresos),
                                            "iess": str(iess),
                                            "totaldesc": str(totaldesc),
                                            "salariopercibir": str(salariopercibir)}),content_type="application/json")

        elif action=='otrosingresos':
            rolpagoprofesor = RolPagoProfesor.objects.get(pk=request.POST['rppid'])
            rolpagoprofesor.otrosing = Decimal(request.POST['valorotrosing'])
            rolpagoprofesor.save()
            rolpagoprofesor.recalcular()
            #Ingresos
            totalinggravados = rolpagoprofesor.totalinggravados
            totalingresos = rolpagoprofesor.total_ingresos_general()
            #Descuentos
            desc = rolpagoprofesor.modelo_descuento()
            iess = desc.iess
            totaldesc = desc.totaldesc
            #Total percibir
            salariopercibir = rolpagoprofesor.salariopercibir
            return HttpResponse(json.dumps({'result':'ok',
                                            "nuevovalorotrosing": str(rolpagoprofesor.otrosing),
                                            "totalinggrav": str(totalinggravados),
                                            "totalingresos": str(totalingresos),
                                            "iess": str(iess),
                                            "totaldesc": str(totaldesc),
                                            "salariopercibir": str(salariopercibir)}),content_type="application/json")

        elif action=='otrosdescuentos':
            rolpagoprofesor = RolPagoProfesor.objects.get(pk=request.POST['rppid'])
            #Descuentos
            desc = rolpagoprofesor.modelo_descuento()
            desc.otrosdesc = Decimal(request.POST['valorotrosdesc'])
            desc.save()
            rolpagoprofesor.recalcular()
            return HttpResponse(json.dumps({'result':'ok',
                                            "nuevovalorotrosdesc": str(desc.otrosdesc),
                                            "totaldesc": str(desc.totaldesc),
                                            "salariopercibir": str(rolpagoprofesor.salariopercibir)}),content_type="application/json")

        elif action=='prestamoiess':
            rolpagoprofesor = RolPagoProfesor.objects.get(pk=request.POST['rppid'])
            #Descuentos
            desc = rolpagoprofesor.modelo_descuento()
            desc.prestamoiess = Decimal(request.POST['valorprestamoiess'])
            desc.save()
            rolpagoprofesor.recalcular()
            return HttpResponse(json.dumps({'result':'ok',
                                            "nuevovalorprestamoiess": str(desc.prestamoiess),
                                            "totaldesc": str(desc.totaldesc),
                                            "salariopercibir": str(rolpagoprofesor.salariopercibir)}),content_type="application/json")


        return HttpResponseRedirect("/rol_pago")
    else:
        data = {'title': 'Roles de Pagos'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='add':
                data['title'] = 'Adicionar Rol de Pago'
                data['form'] = RolPagoForm(initial={'inicio': datetime.today(), 'fin': datetime.today(), 'fechamax': datetime.today(), 'fechamaxvin': datetime.today()})
                return render(request ,"rol_pago/add.html" ,  data)

            elif action=='edit':
                data['title'] = 'Editar Rol de Pago'
                rolpago = RolPago.objects.get(pk=request.GET['id'])
                initial = model_to_dict(rolpago)
                data['rolpago'] = rolpago
                data['form'] = RolPagoForm(initial=initial)
                return render(request ,"rol_pago/edit.html" ,  data)

            elif action=='borrar':
                data['title'] = 'Borrar Rol de Pago'
                data['rolpago'] = RolPago.objects.get(pk=request.GET['id'])
                return render(request ,"rol_pago/borrarrol.html" ,  data)

            elif action=='ver':
                data['title'] = 'Ver Rol de Pago Docente'
                rolpago = RolPago.objects.get(pk=request.GET['id'])
                if 'p' in request.GET :
                    data['p'] = 1
                    rolespagoprofesores = RolPagoProfesor.objects.filter(rol=rolpago,profesor__categoria__id=PROFE_PRACT_CONDUCCION).order_by('profesor__persona__apellido1', 'profesor__persona__apellido2')
                else:
                    if INSCRIPCION_CONDUCCION:
                        rolespagoprofesores = RolPagoProfesor.objects.filter(rol=rolpago).exclude(profesor__dedicacion__id=4).order_by('profesor__persona__apellido1', 'profesor__persona__apellido2')
                    else:
                        rolespagoprofesores = RolPagoProfesor.objects.filter(rol=rolpago).exclude(profesor__categoria__id=PROFE_PRACT_CONDUCCION).order_by('profesor__persona__apellido1', 'profesor__persona__apellido2')

                data['rolpago'] = rolpago
                data['rolespagoprofesores'] = rolespagoprofesores
                data['MODELO_EVALUATIVO'] = [MODELO_EVALUACION, EVALUACION_CASADE]
                data ['MODELO_CONDU'] = INSCRIPCION_CONDUCCION
                return render(request ,"rol_pago/verrol.html" ,  data)

            elif action=='roldetalleprofesor':
                rolpagoprofesor = RolPagoProfesor.objects.get(pk=request.GET['id'])
                #Generar el detalle por cada rol profesor (materias y horas)
                # rolpagoprofesor.genera_roldetallepagoprofesor()
                data['roldetallepagoprofesor'] = rolpagoprofesor.rolpagodetalleprofesor_set.all()
                data['rolpagoprofesor'] = rolpagoprofesor
                return render(request ,"rol_pago/roldetalleprofesor.html" ,  data)

            elif action=='detalleingresos':
                data['rolpago'] = RolPago.objects.get(pk=request.GET['rpp'])
                return render(request ,"rol_pago/detalleingresos.html" ,  data)

            elif action=='detalledescuentos':
                data['rolpago'] = RolPago.objects.get(pk=request.GET['rpp'])
                return render(request ,"rol_pago/detalledescuentos.html" ,  data)

            elif action=='detalleirenta':
                data['rolpagoprofesor'] = RolPagoProfesor.objects.get(pk=request.GET['rpp'])
                return render(request ,"rol_pago/detalleirenta.html" ,  data)

        else:
            data['rolespago'] = RolPago.objects.filter(activo=True).order_by('-id')
            return render(request ,"rol_pago/rolprofesores.html" ,  data)

