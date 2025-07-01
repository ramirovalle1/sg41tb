from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models.aggregates import Sum
from django.forms.models import model_to_dict
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
import requests
from decorators import secure_module
from settings import ACEPTA_PAGO_EFECTIVO, VALIDAR_ENTRADA_SISTEMA_CON_DEUDA, DEFAULT_PASSWORD
from sga.commonviews import addUserData
from sga.models import Matricula, RecordAcademico, Inscripcion, Periodo, MateriaAsignada, Profesor, Rubro, Banco, Pago, InscripcionDescuentoRef


@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    if request.method=='POST':
        return HttpResponseRedirect("/alu_finanzas")
    else:
        data = {'title': ' Mis Finanzas'}
        addUserData(request, data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='pagos':
                rubro = Rubro.objects.get(pk=request.GET['id'])
                data['title'] = rubro.nombre()
                data['rubro'] = rubro
                pagos = Pago.objects.filter(rubro=rubro).order_by('fecha')
                data['pagos'] = pagos

                return render(request ,"alu_finanzas/pagosbs.html" ,  data)
        else:

            data['title'] = 'Listado de Rubros del Alumno: '+str(data['persona'])
            try:
                inscripcion = Inscripcion.objects.get(persona=data['persona'])

                #Comprobar que no tenga deudas para que no pueda usar el sistema
                # OCastillo 30-06-2020 se quita validacion para que estudiante pueda ver sus finanzas asi tenga deuda
                #if VALIDAR_ENTRADA_SISTEMA_CON_DEUDA and inscripcion.tiene_deuda():
                #    return HttpResponseRedirect("/")

                matricula = inscripcion.matricula_set.filter(nivel__periodo__activo=True, nivel__cerrado=False)
                rubros = Rubro.objects.filter(inscripcion=inscripcion).order_by('cancelado','fechavence')
                for r in Rubro.objects.filter(inscripcion=inscripcion,cancelado=True).order_by('cancelado','fechavence'):
                    if r.valor != r.total_pagado():
                        r.cancelado =False

                data['inscripcion'] = inscripcion
                data['matricula'] = matricula

                paging = Paginator(rubros, 40)
                try:
                   if 'page' in request.GET:
                       p = int(request.GET['page'])
                   page = paging.page(p)
                except:
                   page = paging.page(1)
                data['paging'] = paging
                data['page'] = page
                data['rubros'] = page.object_list
                data['total_rubros'] = rubros.aggregate(Sum('valor'))['valor__sum']
                data['total_pagado'] = sum([x.verifica_total_pagado() for x in rubros])
                data['total_adeudado'] = sum([x.verifica_adeudado() for x in rubros])
                if InscripcionDescuentoRef.objects.filter(inscripcion=inscripcion,aplicado=False).exists():
                    data['des'] = InscripcionDescuentoRef.objects.filter(inscripcion=inscripcion,aplicado=False)[:1].get()
                if DEFAULT_PASSWORD == 'itb':
                        try:
                            if inscripcion.persona.extranjero:
                                ced = inscripcion.persona.pasaporte
                                op=0
                            else:
                                op=1
                                ced = inscripcion.persona.cedula
                            datos = requests.get('http://sga.buckcenter.com.ec/api',params={'a': 'datos_finanzas', 'ced':ced,'op': op })
                            if datos.status_code==200:
                                data['otrosrubros']=datos.json()['rubros']
                        except Exception as e:
                            pass
                return render(request ,"alu_finanzas/rubrosbs.html" ,  data)
            except:
                return HttpResponseRedirect("/")