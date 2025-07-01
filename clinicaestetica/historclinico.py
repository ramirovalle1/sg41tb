from datetime import datetime, time, timedelta
import json
from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
import requests
from clinicaestetica.models import TipoHabito, ParametroEstetico, FichaMedica, TipoPersona, AntecedenteMedFicha, HabitoFicha, AntecedenteEsteticoFicha, Consulta, EvaluacionEstetica, RubroEstetico
from med.models import PersonaEstadoCivil
from settings import ID_TIPO_GENERAL, ID_TIPO_CORPORAL, ID_TIPO_FACIAL, ID_TIPO_RUBRO_TRICO
from sga.commonviews import addUserData, ip_client_address
from sga.models import Sexo, Rubro, RubroOtro

__author__ = 'jurgiles'


class MiPaginador(Paginator):
    def __init__(self, object_list, per_page, orphans=0, allow_empty_first_page=True, rango=5):
        super(MiPaginador,self).__init__(object_list, per_page, orphans=orphans, allow_empty_first_page=allow_empty_first_page)
        self.rango = rango
        self.paginas = []
        self.primera_pagina = False
        self.ultima_pagina = False

    def rangos_paginado(self, pagina):
        left = pagina - self.rango
        right = pagina + self.rango
        if left<1:
            left=1
        if right>self.num_pages:
            right = self.num_pages
        self.paginas = range(left, right+1)
        self.primera_pagina = True if left>1 else False
        self.ultima_pagina = True if right<self.num_pages else False
        self.ellipsis_izquierda = left-1
        self.ellipsis_derecha = right+1

@login_required(redirect_field_name='ret', login_url='/login')
# @secure_module
@transaction.atomic()
def view(request):
    """

    :param request:
    :return:
    """
    if request.method == 'POST':
        action = request.POST['action']
        if action == 'buscar':
            try:
                if 'opc' in request.POST:
                    if FichaMedica.objects.filter(numdocumento=request.POST['cedula']).exclude(id=request.POST['opc']).exists():
                        data = {"result": "bad"}
                    else:
                        data = {"result": "ok"}
                    return HttpResponse(json.dumps(data),content_type="application/json")
                else:
                    if FichaMedica.objects.filter(numdocumento=request.POST['cedula']).exists():
                        data = {"result": "ok"}
                        data['id'] = FichaMedica.objects.filter(numdocumento=request.POST['cedula'])[:1].get().id
                    else:
                        data = {"result": "bad"}
                    return HttpResponse(json.dumps(data),content_type="application/json")
            except Exception as ex:
                data = {"result": str(ex)}
                return HttpResponse(json.dumps(data),content_type="application/json")
        elif action == 'guardarantec':
            try:
                fichamedica = FichaMedica.objects.get(id=request.POST['idfichamed'])
                if request.POST['opc']=='patpersonales':
                    if AntecedenteMedFicha.objects.filter(descripcion=request.POST['antece'],patolog_personales = True,fichamedica = fichamedica).exists():
                        return HttpResponse(json.dumps({"result": "El Antecedente ya existe"}),content_type="application/json")
                    else:
                        antecedentemedficha = AntecedenteMedFicha(fichamedica = fichamedica,
                                                descripcion = request.POST['antece'],
                                                patolog_personales = True,
                                                fecha = datetime.now())
                        antecedentemedficha.save()
                elif request.POST['opc']=='patfamiliares':
                    if AntecedenteMedFicha.objects.filter(descripcion=request.POST['antece'],fichamedica = fichamedica,patolog_familiares = True).exists():
                        return HttpResponse(json.dumps({"result": "El Antecedente ya existe"}),content_type="application/json")
                    else:
                        antecedentemedficha = AntecedenteMedFicha(fichamedica = fichamedica,
                                                descripcion = request.POST['antece'],
                                                patolog_familiares = True,
                                                fecha = datetime.now())
                        antecedentemedficha.save()
                elif request.POST['opc']=='antequirur':
                    if AntecedenteMedFicha.objects.filter(descripcion=request.POST['antece'],fichamedica = fichamedica,quirurgico = True).exists():
                        return HttpResponse(json.dumps({"result": "El Antecedente ya existe"}),content_type="application/json")
                    else:
                        antecedentemedficha = AntecedenteMedFicha(fichamedica = fichamedica,
                                                descripcion = request.POST['antece'],
                                                quirurgico = True,
                                                fecha = datetime.now())
                        antecedentemedficha.save()
                elif request.POST['opc']=='alergiadiv':
                    if AntecedenteMedFicha.objects.filter(descripcion=request.POST['antece'],fichamedica = fichamedica,alergia = True).exists():
                        return HttpResponse(json.dumps({"result": "El Antecedente ya existe"}),content_type="application/json")
                    else:
                        antecedentemedficha = AntecedenteMedFicha(fichamedica = fichamedica,
                                                descripcion = request.POST['antece'],
                                                alergia = True,
                                                fecha = datetime.now())
                        antecedentemedficha.save()
                elif request.POST['opc']=='antcirugi':
                    if AntecedenteEsteticoFicha.objects.filter(descripcion=request.POST['antece'],fichamedica = fichamedica,cirugia = True,tipoestetico__id=ID_TIPO_FACIAL).exists():
                        return HttpResponse(json.dumps({"result": "El Antecedente ya existe"}),content_type="application/json")
                    else:
                        antecedenteestetficha = AntecedenteEsteticoFicha(fichamedica = fichamedica,
                                                descripcion = request.POST['antece'],
                                                cirugia = True,
                                                tipoestetico_id=ID_TIPO_FACIAL,
                                                fecha = datetime.now())
                        antecedenteestetficha.save()
                elif request.POST['opc']=='anttratat':
                    if AntecedenteEsteticoFicha.objects.filter(descripcion=request.POST['antece'],fichamedica = fichamedica,tratamiento = True,tipoestetico__id=ID_TIPO_FACIAL).exists():
                        return HttpResponse(json.dumps({"result": "El Antecedente ya existe"}),content_type="application/json")
                    else:
                        antecedenteestetficha = AntecedenteEsteticoFicha(fichamedica = fichamedica,
                                                descripcion = request.POST['antece'],
                                                tratamiento = True,
                                                tipoestetico_id=ID_TIPO_FACIAL,
                                                fecha = datetime.now())
                        antecedenteestetficha.save()
                elif request.POST['opc']=='autotrata':
                    if AntecedenteEsteticoFicha.objects.filter(descripcion=request.POST['antece'],fichamedica = fichamedica,autotratamiento = True,tipoestetico__id=ID_TIPO_FACIAL).exists():
                        return HttpResponse(json.dumps({"result": "El Antecedente ya existe"}),content_type="application/json")
                    else:
                        antecedenteestetficha = AntecedenteEsteticoFicha(fichamedica = fichamedica,
                                                descripcion = request.POST['antece'],
                                                autotratamiento = True,
                                                tipoestetico_id=ID_TIPO_FACIAL,
                                                fecha = datetime.now())
                        antecedenteestetficha.save()
                elif request.POST['opc']=='corpcirugi':
                    if AntecedenteEsteticoFicha.objects.filter(descripcion=request.POST['antece'],fichamedica = fichamedica,cirugia = True,tipoestetico__id=ID_TIPO_CORPORAL).exists():
                        return HttpResponse(json.dumps({"result": "El Antecedente ya existe"}),content_type="application/json")
                    else:
                        antecedenteestetficha = AntecedenteEsteticoFicha(fichamedica = fichamedica,
                                                descripcion = request.POST['antece'],
                                                cirugia = True,
                                                tipoestetico_id=ID_TIPO_CORPORAL,
                                                fecha = datetime.now())
                        antecedenteestetficha.save()
                elif request.POST['opc']=='corptratat':
                    if AntecedenteEsteticoFicha.objects.filter(descripcion=request.POST['antece'],fichamedica = fichamedica,tratamiento = True,tipoestetico__id=ID_TIPO_CORPORAL).exists():
                        return HttpResponse(json.dumps({"result": "El Antecedente ya existe"}),content_type="application/json")
                    else:
                        antecedenteestetficha = AntecedenteEsteticoFicha(fichamedica = fichamedica,
                                                descripcion = request.POST['antece'],
                                                tratamiento = True,
                                                tipoestetico_id=ID_TIPO_CORPORAL,
                                                fecha = datetime.now())
                        antecedenteestetficha.save()
                elif request.POST['opc']=='autotratacorp':
                    if AntecedenteEsteticoFicha.objects.filter(descripcion=request.POST['antece'],fichamedica = fichamedica,autotratamiento = True,tipoestetico__id=ID_TIPO_CORPORAL).exists():
                        return HttpResponse(json.dumps({"result": "El Antecedente ya existe"}),content_type="application/json")
                    else:
                        antecedenteestetficha = AntecedenteEsteticoFicha(fichamedica = fichamedica,
                                                descripcion = request.POST['antece'],
                                                autotratamiento = True,
                                                tipoestetico_id=ID_TIPO_CORPORAL,
                                                fecha = datetime.now())
                        antecedenteestetficha.save()
                client_address = ip_client_address(request)
                # Log de ANULAR FACTURA
                LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(fichamedica).pk,
                        object_id       = fichamedica.id,
                        object_repr     = force_str(fichamedica),
                        action_flag     = ADDITION,
                        change_message  = 'Agregar antecedente estetico '+ request.POST['opc'] +' (' + client_address + ')')
                fichamedica.edicion = datetime.now()
                fichamedica.save()
                data = {"result": "ok"}
                return HttpResponse(json.dumps(data),content_type="application/json")

            except Exception as ex:
                data = {"result": 'Error comuniquese con el Administrador '+str(ex)+' o Vuelva a intentarlo'}
                return HttpResponse(json.dumps(data),content_type="application/json")
        elif action == 'guardarfichcont':
            try:
                fichamedica = FichaMedica.objects.get(id=request.POST['idfichamed'])
                if request.POST['opc']=='hijos':
                    fichamedica.hijos = request.POST['descrip']
                elif request.POST['opc']=='partos':
                    fichamedica.partos = request.POST['descrip']
                elif request.POST['opc']=='cesareas':
                    fichamedica.cesareas = request.POST['descrip']
                elif request.POST['opc']=='metodcontron':
                    fichamedica.controlnatal = request.POST['descrip']
                elif request.POST['opc']=='fum':
                    fichamedica.fum = request.POST['descrip']
                elif 'habgener' in request.POST['opc']:
                    tipohabito = TipoHabito.objects.get(id=request.POST['idhabit'])
                    if HabitoFicha.objects.filter(habito=tipohabito,fichamedica=fichamedica).exists():
                        habitoficha = HabitoFicha.objects.filter(habito=tipohabito,fichamedica=fichamedica)[:1].get()
                    else:
                        habitoficha = HabitoFicha(fichamedica = fichamedica,
                                                  habito = tipohabito)
                    if tipohabito.cant:
                            habitoficha.cant = request.POST['descrip']
                    else:
                        habitoficha.descripcion = request.POST['descrip']
                    habitoficha.save()
                client_address = ip_client_address(request)
                # Log de ANULAR FACTURA
                LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(fichamedica).pk,
                        object_id       = fichamedica.id,
                        object_repr     = force_str(fichamedica),
                        action_flag     = ADDITION,
                        change_message  = 'Agregar Habitos o registro a ficha medica opcion '+ request.POST['opc'] +' (' + client_address + ')')
                fichamedica.edicion = datetime.now()
                fichamedica.save()
                data = {"result": "ok"}
                return HttpResponse(json.dumps(data),content_type="application/json")

            except Exception as ex:
                data = {"result": 'Error comuniquese con el Administrador '+str(ex)+' o Vuelva a intentarlo'}
                return HttpResponse(json.dumps(data),content_type="application/json")
        elif action == 'eliminarantec':
            try:
                fichamedica = FichaMedica.objects.get(id=request.POST['idfichamed'])
                if request.POST['opc']=='patpersonales':
                    if AntecedenteMedFicha.objects.filter(descripcion=request.POST['antece'],patolog_personales = True,fichamedica = fichamedica).exists():
                        antecedentemedficha = AntecedenteMedFicha.objects.filter(descripcion=request.POST['antece'],patolog_personales = True,fichamedica = fichamedica)[:1].get()
                        antecedentemedficha.delete()
                    else:
                        return HttpResponse(json.dumps({"result": "bad"}),content_type="application/json")
                elif request.POST['opc']=='patfamiliares':
                    if AntecedenteMedFicha.objects.filter(descripcion=request.POST['antece'],fichamedica = fichamedica,patolog_familiares = True).exists():
                        antecedentemedficha = AntecedenteMedFicha.objects.filter(descripcion=request.POST['antece'],fichamedica = fichamedica,patolog_familiares = True)[:1].get()
                        antecedentemedficha.delete()
                    else:
                        return HttpResponse(json.dumps({"result": "bad"}),content_type="application/json")
                elif request.POST['opc']=='antequirur':
                    if AntecedenteMedFicha.objects.filter(descripcion=request.POST['antece'],fichamedica = fichamedica,quirurgico = True).exists():
                        antecedentemedficha = AntecedenteMedFicha.objects.filter(descripcion=request.POST['antece'],fichamedica = fichamedica,quirurgico = True)[:1].get()
                        antecedentemedficha.delete()
                    else:
                        return HttpResponse(json.dumps({"result": "bad"}),content_type="application/json")
                elif request.POST['opc']=='alergiadiv':
                    if AntecedenteMedFicha.objects.filter(descripcion=request.POST['antece'],fichamedica = fichamedica,alergia = True).exists():
                        antecedentemedficha = AntecedenteMedFicha.objects.filter(descripcion=request.POST['antece'],fichamedica = fichamedica,alergia = True)[:1].get()
                        antecedentemedficha.delete()
                    else:
                        return HttpResponse(json.dumps({"result": "bad"}),content_type="application/json")
                elif request.POST['opc']=='antcirugi':
                    if AntecedenteEsteticoFicha.objects.filter(descripcion=request.POST['antece'],fichamedica = fichamedica,cirugia = True,tipoestetico__id=ID_TIPO_FACIAL).exists():
                        antecedenteesteticoficha = AntecedenteEsteticoFicha.objects.filter(descripcion=request.POST['antece'],fichamedica = fichamedica,cirugia = True,tipoestetico__id=ID_TIPO_FACIAL)[:1].get()
                        antecedenteesteticoficha.delete()
                    else:
                        return HttpResponse(json.dumps({"result": "bad"}),content_type="application/json")
                elif request.POST['opc']=='anttratat':
                    if AntecedenteEsteticoFicha.objects.filter(descripcion=request.POST['antece'],fichamedica = fichamedica,tratamiento = True,tipoestetico__id=ID_TIPO_FACIAL).exists():
                        antecedenteesteticoficha = AntecedenteEsteticoFicha.objects.filter(descripcion=request.POST['antece'],fichamedica = fichamedica,tratamiento = True,tipoestetico__id=ID_TIPO_FACIAL)[:1].get()
                        antecedenteesteticoficha.delete()
                    else:
                        return HttpResponse(json.dumps({"result": "bad"}),content_type="application/json")
                elif request.POST['opc']=='autotrata':
                    if AntecedenteEsteticoFicha.objects.filter(descripcion=request.POST['antece'],fichamedica = fichamedica,autotratamiento = True,tipoestetico__id=ID_TIPO_FACIAL).exists():
                        antecedenteesteticoficha = AntecedenteEsteticoFicha.objects.filter(descripcion=request.POST['antece'],fichamedica = fichamedica,autotratamiento = True,tipoestetico__id=ID_TIPO_FACIAL)[:1].get()
                        antecedenteesteticoficha.delete()
                    else:
                        return HttpResponse(json.dumps({"result": "bad"}),content_type="application/json")
                elif request.POST['opc']=='corpcirugi':
                    if AntecedenteEsteticoFicha.objects.filter(descripcion=request.POST['antece'],fichamedica = fichamedica,cirugia = True,tipoestetico__id=ID_TIPO_CORPORAL).exists():
                        antecedenteesteticoficha = AntecedenteEsteticoFicha.objects.filter(descripcion=request.POST['antece'],fichamedica = fichamedica,cirugia = True,tipoestetico__id=ID_TIPO_CORPORAL)[:1].get()
                        antecedenteesteticoficha.delete()
                    else:
                        return HttpResponse(json.dumps({"result": "bad"}),content_type="application/json")
                elif request.POST['opc']=='corptratat':
                    if AntecedenteEsteticoFicha.objects.filter(descripcion=request.POST['antece'],fichamedica = fichamedica,tratamiento = True,tipoestetico__id=ID_TIPO_CORPORAL).exists():
                        antecedenteesteticoficha = AntecedenteEsteticoFicha.objects.filter(descripcion=request.POST['antece'],fichamedica = fichamedica,tratamiento = True,tipoestetico__id=ID_TIPO_CORPORAL)[:1].get()
                        antecedenteesteticoficha.delete()
                    else:
                        return HttpResponse(json.dumps({"result": "bad"}),content_type="application/json")
                elif request.POST['opc']=='autotratacorp':
                    if AntecedenteEsteticoFicha.objects.filter(descripcion=request.POST['antece'],fichamedica = fichamedica,autotratamiento = True,tipoestetico__id=ID_TIPO_CORPORAL).exists():
                        antecedenteesteticoficha = AntecedenteEsteticoFicha.objects.filter(descripcion=request.POST['antece'],fichamedica = fichamedica,autotratamiento = True,tipoestetico__id=ID_TIPO_CORPORAL)[:1].get()
                        antecedenteesteticoficha.delete()
                    else:
                        return HttpResponse(json.dumps({"result": "bad"}),content_type="application/json")
                client_address = ip_client_address(request)
                # Log de ANULAR FACTURA
                LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(fichamedica).pk,
                        object_id       = fichamedica.id,
                        object_repr     = force_str(fichamedica),
                        action_flag     = ADDITION,
                        change_message  = 'Eliminacion de antecedente estetico '+ request.POST['opc'] +' (' + client_address + ')')
                fichamedica.edicion = datetime.now()
                fichamedica.save()
                return HttpResponse(json.dumps({"result": "ok"}),content_type="application/json")
            except Exception as ex:
                data = {"result": str(ex)}
                return HttpResponse(json.dumps(data),content_type="application/json")



        elif action == 'addgeneral':
            try:
                pasaport = False
                op = 1
                if request.POST['pasapor'] == 'true':
                    pasaport = True
                    op = 0
                tipopersona = TipoPersona.objects.filter(id=request.POST['tipopersona'])[:1].get()
                b = 0
                if  tipopersona.verifica:
                    try:
                        datos = requests.get(tipopersona.url, params={'a': 'tipopersona','identificacion': str(request.POST['numdocumento']),'op': str(op)})
                    except Exception as e:
                        data = {"result": str(e)}
                        return HttpResponse(json.dumps(data),content_type="application/json")
                    b = 1
                    if datos.status_code == 200:
                        dato = datos.json()
                        codigo = dato['codigo'].upper()
                        if tipopersona.codigo == codigo:
                            b = 0
                if b == 0:
                    if not 'id' in request.POST:
                        fichamedica = FichaMedica(nombres = request.POST['nombres'],
                                                apellidos = request.POST['apellido'],
                                                numdocumento = request.POST['numdocumento'],
                                                pasaporte = pasaport,
                                                telefono = request.POST['telefonocel'],
                                                ocupacion = request.POST['ocupacion'],
                                                sexo_id = request.POST['sexo'],
                                                fechanacimiento = request.POST['fechnacimiento'],
                                                estadocivil_id = request.POST['estadocivil'],
                                                direccion = request.POST['direccion'],
                                                email = request.POST['email'] ,
                                                tipopersona = tipopersona,
                                                creacion = datetime.now(),
                                                edicion = datetime.now())
                        mensaje = 'Creacion de Ficha medica'
                    else:
                        fichamedica = FichaMedica.objects.get(id=request.POST['id'])
                        fichamedica.nombres = request.POST['nombres']
                        fichamedica.apellidos = request.POST['apellido']
                        fichamedica.telefono = request.POST['telefonocel']
                        fichamedica.ocupacion = request.POST['ocupacion']
                        fichamedica.sexo_id = request.POST['sexo']
                        fichamedica.fechanacimiento = request.POST['fechnacimiento']
                        fichamedica.estadocivil_id = request.POST['estadocivil']
                        fichamedica.direccion = request.POST['direccion']
                        fichamedica.email = request.POST['email']
                        fichamedica.tipopersona = tipopersona
                        fichamedica.edicion = datetime.now()
                        mensaje = 'Edicion de Ficha medica'

                    fichamedica.save()
                    client_address = ip_client_address(request)
                    # Log de ANULAR FACTURA
                    LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(fichamedica).pk,
                            object_id       = fichamedica.id,
                            object_repr     = force_str(fichamedica),
                            action_flag     = ADDITION,
                            change_message  = mensaje+' (' + client_address + ')')

                    data = {"result": "ok"}
                    data['id'] = fichamedica.id
                    return HttpResponse(json.dumps(data),content_type="application/json")
                data = {"result": "noexiste"}
                return HttpResponse(json.dumps(data),content_type="application/json")
            except Exception as ex:
                data = {"result": str(ex)}
                return HttpResponse(json.dumps(data),content_type="application/json")

        elif action == 'adddatoclinico':
            try:
                if FichaMedica.objects.filter(id=request.POST['id']).exists():
                    fichamedica = FichaMedica.objects.get(id=request.POST['id'])
                    horasol = time(int(request.POST['exponsol'].split(":")[0]), int(request.POST['exponsol'].split(":")[1]), 0)
                    consulta =  Consulta(fichamedica=fichamedica,
                                            motivo = request.POST['motivocon'],
                                            medicamento = request.POST['medicamenactual'],
                                            horasol = horasol,
                                            fps = request.POST['fps'],
                                            fecha = datetime.now())
                    consulta.save()
                    client_address = ip_client_address(request)
                    # Log de ANULAR FACTURA
                    LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(consulta).pk,
                            object_id       = consulta.id,
                            object_repr     = force_str(consulta),
                            action_flag     = ADDITION,
                            change_message  = 'Ingresar consulta (' + client_address + ')')
                    data = {"result": "ok"}
                    data['idconsult'] = consulta.id
                    return HttpResponse(json.dumps(data),content_type="application/json")
                data = {"result": "noexiste"}
                return HttpResponse(json.dumps(data),content_type="application/json")
            except Exception as ex:
                data = {"result": 'Error comuniquese con el Administrador '+str(ex)}
                return HttpResponse(json.dumps(data),content_type="application/json")

        elif action == 'cosmeticoactual':
            try:
                if FichaMedica.objects.filter(id=request.POST['id']).exists():
                    consulta = Consulta.objects.get(id=request.POST['idconsult'])
                    consulta.cosmetico = request.POST['descrip']
                    consulta.save()
                    data = {"result": "ok"}
                    return HttpResponse(json.dumps(data),content_type="application/json")
                data = {"result": "noexiste"}
                return HttpResponse(json.dumps(data),content_type="application/json")
            except Exception as ex:
                data = {"result": 'Error comuniquese con el Administrador '+str(ex)}
                return HttpResponse(json.dumps(data),content_type="application/json")

        elif action == 'evalesteticafac':
            try:
                if FichaMedica.objects.filter(id=request.POST['id']).exists():
                    fichamedica = FichaMedica.objects.get(id=request.POST['id'])
                    consulta = Consulta.objects.get(id=request.POST['idconsult'])
                    if not EvaluacionEstetica.objects.filter(consulta=consulta,tipoestetico=ID_TIPO_FACIAL).exists():
                        evaluacionestetica = EvaluacionEstetica(
                                                consulta = consulta,
                                                tipoestetico_id=ID_TIPO_FACIAL)
                    else:
                        evaluacionestetica = EvaluacionEstetica.objects.get(consulta=consulta,tipoestetico__id=ID_TIPO_FACIAL)
                    evaluacionestetica.save()
                    if request.POST['opc'] == 'fotopiel':
                        trat = request.POST['descrip']
                        if int(request.POST['descrip']) == 0:
                            trat = None
                        evaluacionestetica.fotpiel_id = trat
                    elif request.POST['opc'] == 'biotipo':
                        trat = request.POST['descrip']
                        if int(request.POST['descrip']) == 0:
                            trat = None
                        evaluacionestetica.biotipo_id = trat
                    elif request.POST['opc'] == 'tipopiel':
                        trat = request.POST['descrip']
                        if int(request.POST['descrip']) == 0:
                            trat = None
                        evaluacionestetica.tipopiel_id = trat
                    elif request.POST['opc'] == 'glogau':
                        trat = request.POST['descrip']
                        if int(request.POST['descrip']) == 0:
                            trat = None
                        evaluacionestetica.glogau_id = trat
                    elif request.POST['opc'] == 'lineexpre':
                        trat = request.POST['descrip']
                        if int(request.POST['descrip']) == 0:
                            trat = None
                        evaluacionestetica.linexpre_id = trat
                    elif request.POST['opc'] == 'textpiel':
                        evaluacionestetica.ftextpiel_cpeso = request.POST['descrip']
                    elif request.POST['opc'] == 'poro':
                        evaluacionestetica.fporos_ctalla = request.POST['descrip']
                    elif request.POST['opc'] == 'comedones':
                        evaluacionestetica.fcomedones_cimc = request.POST['descrip']
                    elif request.POST['opc'] == 'altcutanea':
                        evaluacionestetica.falteraciones_cgrasa = request.POST['descrip']
                    elif request.POST['opc'] == 'diagnostico':
                        evaluacionestetica.diagnostico = request.POST['descrip']
                    elif request.POST['opc'] == 'tratamientofac':
                        trat = request.POST['descrip']
                        if int(request.POST['descrip']) == 0:
                            trat = None
                        evaluacionestetica.tratamiento_id = trat
                    elif request.POST['opc'] == 'desctratamiento':
                        evaluacionestetica.desctratamiento = request.POST['descrip']
                    elif request.POST['opc'] == 'sesiones':
                        sesion = request.POST['descrip']
                        if not request.POST['descrip']:
                            sesion = None
                        evaluacionestetica.sesion = sesion
                    elif request.POST['opc'] == 'cantdias':
                        cantdias = request.POST['descrip']
                        if not request.POST['descrip']:
                            cantdias = None
                        evaluacionestetica.dias = cantdias
                    evaluacionestetica.fecha = datetime.now()
                    evaluacionestetica.save()
                    data = {"result": "ok"}
                    return HttpResponse(json.dumps(data),content_type="application/json")
                data = {"result": "noexiste"}
                return HttpResponse(json.dumps(data),content_type="application/json")
            except Exception as ex:
                data = {"result": 'Error comuniquese con el Administrador '+str(ex)}
                return HttpResponse(json.dumps(data),content_type="application/json")

        elif action == 'evalesteticacorp':
            try:
                if FichaMedica.objects.filter(id=request.POST['id']).exists():
                    consulta = Consulta.objects.get(id=request.POST['idconsult'])
                    if not EvaluacionEstetica.objects.filter(consulta=consulta,tipoestetico=ID_TIPO_CORPORAL).exists():
                        evaluacionestetica = EvaluacionEstetica(
                                                consulta = consulta,
                                                tipoestetico_id=ID_TIPO_CORPORAL)
                    else:
                        evaluacionestetica = EvaluacionEstetica.objects.get(consulta=consulta,tipoestetico__id=ID_TIPO_CORPORAL)
                    evaluacionestetica.save()
                    if request.POST['opc'] == 'peso':
                        evaluacionestetica.ftextpiel_cpeso = request.POST['descrip']
                    elif request.POST['opc'] == 'talla':
                        evaluacionestetica.fporos_ctalla = request.POST['descrip']
                    elif request.POST['opc'] == 'imc':
                        evaluacionestetica.fcomedones_cimc = request.POST['descrip']
                    elif request.POST['opc'] == 'grascorp':
                        evaluacionestetica.falteraciones_cgrasa = request.POST['descrip']
                    elif request.POST['opc'] == 'cuello':
                        trat = request.POST['descrip']
                        if not request.POST['descrip']:
                            trat = None
                        evaluacionestetica.cuello = trat
                    elif request.POST['opc'] == 'abalto':
                        trat = request.POST['descrip']
                        if not request.POST['descrip']:
                            trat = None
                        evaluacionestetica.abalto = trat
                    elif request.POST['opc'] == 'cintura':
                        trat = request.POST['descrip']
                        if not request.POST['descrip']:
                            trat = None
                        evaluacionestetica.cintura = trat
                    elif request.POST['opc'] == 'abbajo':
                        trat = request.POST['descrip']
                        if not request.POST['descrip']:
                            trat = None
                        evaluacionestetica.abbajo = trat
                    elif request.POST['opc'] == 'muslo':
                        trat = request.POST['descrip']
                        if not request.POST['descrip']:
                            trat = None
                        evaluacionestetica.muslo = trat
                    elif request.POST['opc'] == 'brazo':
                        trat = request.POST['descrip']
                        if not request.POST['descrip']:
                            trat = None
                        evaluacionestetica.brazo = trat
                    elif request.POST['opc'] == 'pesoideal':
                        trat = request.POST['descrip']
                        if not request.POST['descrip']:
                            trat = None
                        evaluacionestetica.pesoideal = trat
                    elif request.POST['opc'] == 'pesodesado':
                        trat = request.POST['descrip']
                        if not request.POST['descrip']:
                            trat = None
                        evaluacionestetica.pesodesado = trat
                    elif request.POST['opc'] == 'diagnostico':
                        evaluacionestetica.diagnostico = request.POST['descrip']
                    elif request.POST['opc'] == 'tratamientocorp':
                        trat = request.POST['descrip']
                        if int(request.POST['descrip']) == 0:
                            trat = None
                        evaluacionestetica.tratamiento_id = trat
                    elif request.POST['opc'] == 'desctratamiento':
                        evaluacionestetica.desctratamiento = request.POST['descrip']
                    elif request.POST['opc'] == 'sesiones':
                        sesion = request.POST['descrip']
                        if not request.POST['descrip']:
                            sesion = None
                        evaluacionestetica.sesion = sesion
                    elif request.POST['opc'] == 'cantdias':
                        cantdias = request.POST['descrip']
                        if not request.POST['descrip']:
                            cantdias = None
                        evaluacionestetica.dias = cantdias

                    evaluacionestetica.fecha = datetime.now()
                    evaluacionestetica.save()
                    data = {"result": "ok"}
                    return HttpResponse(json.dumps(data),content_type="application/json")
                data = {"result": "noexiste"}
                return HttpResponse(json.dumps(data),content_type="application/json")
            except Exception as ex:
                data = {"result": 'Error comuniquese con el Administrador '+str(ex)}
                return HttpResponse(json.dumps(data),content_type="application/json")
        elif action == 'validaguardar':
            try:
                datos = ''
                if FichaMedica.objects.filter(id=request.POST['id']).exists():
                    consulta = Consulta.objects.get(id=request.POST['idconsult'])
                    if request.POST['opc'] == 'facial':
                        if not EvaluacionEstetica.objects.filter(consulta=consulta,tipoestetico=ID_TIPO_FACIAL).exists():
                            data = {"result": 'ok'}
                            return HttpResponse(json.dumps(data),content_type="application/json")
                        datos = EvaluacionEstetica.objects.filter(consulta=consulta,tipoestetico=ID_TIPO_FACIAL).values('fotpiel','biotipo','tipopiel','glogau',
                                                                                                                          'linexpre','ftextpiel_cpeso','fporos_ctalla',
                                                                                                                          'fcomedones_cimc','falteraciones_cgrasa','diagnostico','desctratamiento')
                        evaluacionestetica = EvaluacionEstetica.objects.get(consulta=consulta,tipoestetico=ID_TIPO_FACIAL)
                        if datos:
                            if (evaluacionestetica.fotpiel and evaluacionestetica.biotipo and evaluacionestetica.tipopiel and evaluacionestetica.glogau and
                                 evaluacionestetica.linexpre and evaluacionestetica.ftextpiel_cpeso and evaluacionestetica.fporos_ctalla and evaluacionestetica.fcomedones_cimc and evaluacionestetica.falteraciones_cgrasa and
                                    evaluacionestetica.diagnostico):
                                data = {"result": 'ok'}
                                return HttpResponse(json.dumps(data),content_type="application/json")
                            data = {"result": 'Faltan datos esteticos Faciales por ingresar'}
                            return HttpResponse(json.dumps(data),content_type="application/json")
                        else:
                            evaluacionestetica.consulta.cosmetico = ''
                            evaluacionestetica.consulta.save()
                            evaluacionestetica.delete()
                    if request.POST['opc'] == 'corporal':
                        if not EvaluacionEstetica.objects.filter(consulta=consulta,tipoestetico=ID_TIPO_CORPORAL).exists():
                            data = {"result": 'ok'}
                            return HttpResponse(json.dumps(data),content_type="application/json")
                        datos = EvaluacionEstetica.objects.filter(consulta=consulta,tipoestetico=ID_TIPO_CORPORAL).values('ftextpiel_cpeso','fporos_ctalla','fcomedones_cimc',
                                                                                                            'falteraciones_cgrasa','cuello','abalto','cintura','abbajo',
                                                                                                            'muslo','brazo','pesoideal','pesodesado','diagnostico','desctratamiento')

                        evaluacionestetica = EvaluacionEstetica.objects.get(consulta=consulta,tipoestetico=ID_TIPO_CORPORAL)
                        if datos:
                            if (evaluacionestetica.ftextpiel_cpeso and evaluacionestetica.fporos_ctalla and evaluacionestetica.fcomedones_cimc and evaluacionestetica.falteraciones_cgrasa and
                                 evaluacionestetica.cuello and evaluacionestetica.abalto and evaluacionestetica.cintura and evaluacionestetica.abbajo and evaluacionestetica.muslo and
                                evaluacionestetica.brazo and evaluacionestetica.pesoideal and evaluacionestetica.pesodesado and evaluacionestetica.diagnostico):
                                data = {"result": 'ok'}
                                return HttpResponse(json.dumps(data),content_type="application/json")
                            data = {"result": 'Faltan datos esteticos Corporales por ingresar'}
                            return HttpResponse(json.dumps(data),content_type="application/json")
                        else:
                            evaluacionestetica.delete()


                    data = {"result": 'ok'}
                    return HttpResponse(json.dumps(data),content_type="application/json")

            except Exception as ex:
                data = {"result": 'Error comuniquese con el Administrador '+str(ex)}
                return HttpResponse(json.dumps(data),content_type="application/json")
        elif action == 'eliminardato':
            try:
                datos = ''
                if FichaMedica.objects.filter(id=request.POST['id']).exists():
                    consulta = Consulta.objects.get(id=request.POST['idconsult'])
                    if request.POST['opc'] == 'facial':
                        if not EvaluacionEstetica.objects.filter(consulta=consulta,tipoestetico=ID_TIPO_FACIAL).exists():
                            data = {"result": 'ok'}
                            return HttpResponse(json.dumps(data),content_type="application/json")
                        evaluacionestetica = EvaluacionEstetica.objects.get(consulta=consulta,tipoestetico=ID_TIPO_FACIAL)
                        evaluacionestetica.consulta.cosmetico = ''
                        evaluacionestetica.consulta.save()
                        evaluacionestetica.delete()
                    if request.POST['opc'] == 'corporal':
                        if not EvaluacionEstetica.objects.filter(consulta=consulta,tipoestetico=ID_TIPO_CORPORAL).exists():
                            data = {"result": 'ok'}
                            return HttpResponse(json.dumps(data),content_type="application/json")
                        evaluacionestetica = EvaluacionEstetica.objects.filter(consulta=consulta,tipoestetico=ID_TIPO_CORPORAL)
                        evaluacionestetica.delete()
                    data = {"result": 'ok'}
                    return HttpResponse(json.dumps(data),content_type="application/json")

            except Exception as ex:
                data = {"result": 'Error comuniquese con el Administrador '+str(ex)+' O vuelva a intentarlo'}
                return HttpResponse(json.dumps(data),content_type="application/json")
        elif action == 'guardardatos':
            sid = transaction.savepoint()
            try:
                if FichaMedica.objects.filter(id=request.POST['id']).exists():
                    fichamedica = FichaMedica.objects.get(id=request.POST['id'])
                    consulta = Consulta.objects.get(id=request.POST['idconsult'])
                    validadato = False
                    if EvaluacionEstetica.objects.filter(consulta=consulta,tipoestetico=ID_TIPO_FACIAL).exists():
                        evaluacionestetica = EvaluacionEstetica.objects.get(consulta=consulta,tipoestetico=ID_TIPO_FACIAL)
                        if evaluacionestetica.tratamiento:
                            tratamientoprecio = evaluacionestetica.tratamiento.preciotratamiento(fichamedica)
                            if evaluacionestetica.sesion and evaluacionestetica.dias:
                                dias = evaluacionestetica.sesion * evaluacionestetica.dias
                            else:
                                dias = 15
                            hoy =datetime.now() + timedelta(dias)
                            rubro = Rubro(fecha = datetime.now(),
                                        valor = tratamientoprecio.valor,
                                        fichamedica = fichamedica,
                                        cancelado = False,
                                        fechavence = hoy)
                            rubro.save()
                            rubrootro = RubroOtro(rubro = rubro,
                                                tipo_id = ID_TIPO_RUBRO_TRICO,
                                                descripcion = tratamientoprecio.tratamiento.nombre)
                            rubrootro.save()
                            rubroestetico = RubroEstetico(
                                                rubro = rubro.id,
                                                evaluacionestetica = evaluacionestetica,
                                                fecha = datetime.now())
                            rubroestetico.save()
                        validadato = True


                    if EvaluacionEstetica.objects.filter(consulta=consulta,tipoestetico=ID_TIPO_CORPORAL).exists():
                        evaluacionestetica = EvaluacionEstetica.objects.get(consulta=consulta,tipoestetico=ID_TIPO_CORPORAL)
                        if evaluacionestetica.tratamiento:
                            tratamientoprecio = evaluacionestetica.tratamiento.preciotratamiento(fichamedica)
                            if evaluacionestetica.sesion and evaluacionestetica.dias:
                                dias = evaluacionestetica.sesion * evaluacionestetica.dias
                            else:
                                dias = 15
                            hoy =datetime.now() + timedelta(dias)
                            rubro = Rubro(fecha = datetime.now(),
                                        valor = tratamientoprecio.valor,
                                        fichamedica = fichamedica,
                                        cancelado = False,
                                        fechavence = hoy)
                            rubro.save()
                            rubrootro = RubroOtro(rubro = rubro,
                                                tipo_id = ID_TIPO_RUBRO_TRICO,
                                                descripcion = tratamientoprecio.tratamiento.nombre)
                            rubrootro.save()
                            rubroestetico = RubroEstetico(
                                                rubro = rubro.id,
                                                evaluacionestetica = evaluacionestetica,
                                                fecha = datetime.now())
                            rubroestetico.save()
                        validadato = True
                    if validadato:
                        consulta.guardado = True
                        consulta.usuario = request.user
                        transaction.savepoint_commit(sid)
                        data = {"result": 'ok'}
                        return HttpResponse(json.dumps(data),content_type="application/json")
                    else:
                        transaction.savepoint_rollback(sid)
                        data = {"result": 'Ingresar datos esteticos Faciales o Corporales'}
                        return HttpResponse(json.dumps(data),content_type="application/json")
                data = {"result": 'no exite la ficha medica vuelva a ingresar'}
                return HttpResponse(json.dumps(data),content_type="application/json")

            except Exception as ex:
                transaction.savepoint_rollback(sid)
                data = {"result": 'Error comuniquese con el Administrador '+str(ex)+' O vuelva a intentarlo'}
                return HttpResponse(json.dumps(data),content_type="application/json")
    else:

        data = {'title':'Historia Clinica'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action == 'add':
                if 'id' in request.GET:
                    data['fichamedica'] = FichaMedica.objects.get(id=request.GET['id'])
                    if AntecedenteMedFicha.objects.filter(fichamedica = data['fichamedica'],patolog_personales  = True).exists():
                        data['antecedentepersonales'] = AntecedenteMedFicha.objects.filter(fichamedica = data['fichamedica'],patolog_personales = True)
                    if AntecedenteMedFicha.objects.filter(fichamedica = data['fichamedica'],patolog_familiares  = True).exists():
                        data['antecedentefamiliares'] = AntecedenteMedFicha.objects.filter(fichamedica = data['fichamedica'],patolog_familiares = True)
                    if AntecedenteMedFicha.objects.filter(fichamedica = data['fichamedica'],quirurgico  = True).exists():
                        data['quirurgicos'] = AntecedenteMedFicha.objects.filter(fichamedica = data['fichamedica'],quirurgico = True)
                    if AntecedenteMedFicha.objects.filter(fichamedica = data['fichamedica'],alergia  = True).exists():
                        data['alergias'] = AntecedenteMedFicha.objects.filter(fichamedica = data['fichamedica'],alergia = True)
                    if AntecedenteEsteticoFicha.objects.filter(fichamedica = data['fichamedica'],cirugia  = True,tipoestetico__id=ID_TIPO_FACIAL).exists():
                        data['anteestetfaccirugia'] = AntecedenteEsteticoFicha.objects.filter(fichamedica = data['fichamedica'],cirugia  = True,tipoestetico__id=ID_TIPO_FACIAL)
                    if AntecedenteEsteticoFicha.objects.filter(fichamedica = data['fichamedica'],tratamiento  = True,tipoestetico__id=ID_TIPO_FACIAL).exists():
                        data['anteestetfactratamiento'] = AntecedenteEsteticoFicha.objects.filter(fichamedica = data['fichamedica'],tratamiento  = True,tipoestetico__id=ID_TIPO_FACIAL)
                    if AntecedenteEsteticoFicha.objects.filter(fichamedica = data['fichamedica'],autotratamiento  = True,tipoestetico__id=ID_TIPO_FACIAL).exists():
                        data['anteestetfacauttratamiento'] = AntecedenteEsteticoFicha.objects.filter(fichamedica = data['fichamedica'],autotratamiento  = True,tipoestetico__id=ID_TIPO_FACIAL)
                    if AntecedenteEsteticoFicha.objects.filter(fichamedica = data['fichamedica'],cirugia  = True,tipoestetico__id=ID_TIPO_CORPORAL).exists():
                        data['anteestetcorpcirugia'] = AntecedenteEsteticoFicha.objects.filter(fichamedica = data['fichamedica'],cirugia  = True,tipoestetico__id=ID_TIPO_CORPORAL)
                    if AntecedenteEsteticoFicha.objects.filter(fichamedica = data['fichamedica'],tratamiento  = True,tipoestetico__id=ID_TIPO_CORPORAL).exists():
                        data['anteestetcorptratamiento'] = AntecedenteEsteticoFicha.objects.filter(fichamedica = data['fichamedica'],tratamiento  = True,tipoestetico__id=ID_TIPO_CORPORAL)
                    if AntecedenteEsteticoFicha.objects.filter(fichamedica = data['fichamedica'],autotratamiento  = True,tipoestetico__id=ID_TIPO_CORPORAL).exists():
                        data['anteestetcorpauttratamiento'] = AntecedenteEsteticoFicha.objects.filter(fichamedica = data['fichamedica'],autotratamiento  = True,tipoestetico__id=ID_TIPO_CORPORAL)
                data['habitogeneral1'] = TipoHabito.objects.filter(tipoestetico=ID_TIPO_GENERAL,activo=True).order_by('id')[:4]
                data['habitogeneral2'] = TipoHabito.objects.filter(id__in=TipoHabito.objects.filter(tipoestetico=ID_TIPO_GENERAL).order_by('-id')[:5].values('id'),activo=True).order_by('id')
                data['fotpiel'] = ParametroEstetico.objects.filter(fotpiel=True,activo=True).order_by('id')
                data['biotipo'] = ParametroEstetico.objects.filter(biotipo=True,activo=True).order_by('id')
                data['tippiel'] = ParametroEstetico.objects.filter(tippiel=True,activo=True).order_by('id')
                data['eglogau'] = ParametroEstetico.objects.filter(eglogau=True,activo=True).order_by('id')
                data['linexpr'] = ParametroEstetico.objects.filter(linexpr=True,activo=True).order_by('id')
                data['sexo'] = Sexo.objects.filter().order_by('id')
                data['estadocivil'] = PersonaEstadoCivil.objects.filter().order_by('id')
                data['habitocorporal'] = TipoHabito.objects.filter(tipoestetico=ID_TIPO_CORPORAL,activo=True).order_by('id')
                data['tipopersona'] = TipoPersona.objects.filter().order_by('id')
                data['fechahoy'] = datetime.now()
                data['ID_TIPO_FACIAL'] = ID_TIPO_FACIAL
                data['ID_TIPO_CORPORAL'] = ID_TIPO_CORPORAL
                data['fechaactual'] = str(datetime.now().date().year)+"-"+str(datetime.now().date().month).zfill(2)+"-"+str(datetime.now().date().day).zfill(2)
                return render(request ,"historiaclinica/historiaclinica.html" ,  data)
            elif action == 'del':
                try:
                    consulta = Consulta.objects.get(id=request.GET['idconsul'])
                    if EvaluacionEstetica.objects.filter(consulta = consulta).exists():
                        evaluacionestetica = EvaluacionEstetica.objects.filter(consulta = consulta)
                        evaluacionestetica.delete()
                    consulta.delete()

                    return HttpResponseRedirect('/historiaclinica')
                except Exception as ex:
                    return HttpResponseRedirect('/historiaclinica?info='+str(ex))
            elif action=='consultas':
                data['title'] = 'Consultas Esteticas'
                consultas = Consulta.objects.filter(fichamedica=request.GET['idficha']).order_by('-fecha')
                fichamedica = FichaMedica.objects.get(pk=request.GET['idficha'])
                paging = MiPaginador(consultas, 30)
                p = 1
                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                    page = paging.page(p)
                except:
                    page = paging.page(1)
                data['paging'] = paging
                data['rangospaging'] = paging.rangos_paginado(p)
                data['page'] = page
                data['consultas'] = page.object_list
                data['fichamedica'] = fichamedica
                return render(request ,"historiaclinica/consultas.html" ,  data)
            elif action=='verconsulta':
                data['title'] = 'Ver Consulta'
                consulta = Consulta.objects.get(id=request.GET['idconsult'])
                fichamedica = consulta.fichamedica
                if EvaluacionEstetica.objects.filter(consulta=consulta, tipoestetico__id=ID_TIPO_FACIAL).exists():
                    data['esteticafacial'] = EvaluacionEstetica.objects.get(consulta=consulta, tipoestetico__id=ID_TIPO_FACIAL)
                if EvaluacionEstetica.objects.filter(consulta=consulta, tipoestetico__id=ID_TIPO_CORPORAL).exists():
                    data['esteticacorporal'] = EvaluacionEstetica.objects.get(consulta=consulta, tipoestetico__id=ID_TIPO_CORPORAL)

                data['consulta'] = consulta
                data['fichamedica'] = fichamedica
                data['fotpiel'] = ParametroEstetico.objects.filter(fotpiel=True,activo=True).order_by('id')
                data['biotipo'] = ParametroEstetico.objects.filter(biotipo=True,activo=True).order_by('id')
                data['tippiel'] = ParametroEstetico.objects.filter(tippiel=True,activo=True).order_by('id')
                data['eglogau'] = ParametroEstetico.objects.filter(eglogau=True,activo=True).order_by('id')
                data['linexpr'] = ParametroEstetico.objects.filter(linexpr=True,activo=True).order_by('id')
                return render(request ,"historiaclinica/verconsulta.html" ,  data)
            elif action=='verficha':
                data['title'] = 'Ver Consulta'
                data['fichamedica'] = FichaMedica.objects.get(id=request.GET['idficha'])
                if AntecedenteMedFicha.objects.filter(fichamedica = data['fichamedica'],patolog_personales  = True).exists():
                    data['antecedentepersonales'] = AntecedenteMedFicha.objects.filter(fichamedica = data['fichamedica'],patolog_personales = True)
                if AntecedenteMedFicha.objects.filter(fichamedica = data['fichamedica'],patolog_familiares  = True).exists():
                    data['antecedentefamiliares'] = AntecedenteMedFicha.objects.filter(fichamedica = data['fichamedica'],patolog_familiares = True)
                if AntecedenteMedFicha.objects.filter(fichamedica = data['fichamedica'],quirurgico  = True).exists():
                    data['quirurgicos'] = AntecedenteMedFicha.objects.filter(fichamedica = data['fichamedica'],quirurgico = True)
                if AntecedenteMedFicha.objects.filter(fichamedica = data['fichamedica'],alergia  = True).exists():
                    data['alergias'] = AntecedenteMedFicha.objects.filter(fichamedica = data['fichamedica'],alergia = True)
                if AntecedenteEsteticoFicha.objects.filter(fichamedica = data['fichamedica'],cirugia  = True,tipoestetico__id=ID_TIPO_FACIAL).exists():
                    data['anteestetfaccirugia'] = AntecedenteEsteticoFicha.objects.filter(fichamedica = data['fichamedica'],cirugia  = True,tipoestetico__id=ID_TIPO_FACIAL)
                if AntecedenteEsteticoFicha.objects.filter(fichamedica = data['fichamedica'],tratamiento  = True,tipoestetico__id=ID_TIPO_FACIAL).exists():
                    data['anteestetfactratamiento'] = AntecedenteEsteticoFicha.objects.filter(fichamedica = data['fichamedica'],tratamiento  = True,tipoestetico__id=ID_TIPO_FACIAL)
                if AntecedenteEsteticoFicha.objects.filter(fichamedica = data['fichamedica'],autotratamiento  = True,tipoestetico__id=ID_TIPO_FACIAL).exists():
                    data['anteestetfacauttratamiento'] = AntecedenteEsteticoFicha.objects.filter(fichamedica = data['fichamedica'],autotratamiento  = True,tipoestetico__id=ID_TIPO_FACIAL)
                if AntecedenteEsteticoFicha.objects.filter(fichamedica = data['fichamedica'],cirugia  = True,tipoestetico__id=ID_TIPO_CORPORAL).exists():
                    data['anteestetcorpcirugia'] = AntecedenteEsteticoFicha.objects.filter(fichamedica = data['fichamedica'],cirugia  = True,tipoestetico__id=ID_TIPO_CORPORAL)
                if AntecedenteEsteticoFicha.objects.filter(fichamedica = data['fichamedica'],tratamiento  = True,tipoestetico__id=ID_TIPO_CORPORAL).exists():
                    data['anteestetcorptratamiento'] = AntecedenteEsteticoFicha.objects.filter(fichamedica = data['fichamedica'],tratamiento  = True,tipoestetico__id=ID_TIPO_CORPORAL)
                if AntecedenteEsteticoFicha.objects.filter(fichamedica = data['fichamedica'],autotratamiento  = True,tipoestetico__id=ID_TIPO_CORPORAL).exists():
                    data['anteestetcorpauttratamiento'] = AntecedenteEsteticoFicha.objects.filter(fichamedica = data['fichamedica'],autotratamiento  = True,tipoestetico__id=ID_TIPO_CORPORAL)
                data['habitogeneral1'] = TipoHabito.objects.filter(tipoestetico=ID_TIPO_GENERAL,activo=True).order_by('id')[:4]
                data['habitogeneral2'] = TipoHabito.objects.filter(id__in=TipoHabito.objects.filter(tipoestetico=ID_TIPO_GENERAL).order_by('-id')[:5].values('id'),activo=True).order_by('id')
                data['fotpiel'] = ParametroEstetico.objects.filter(fotpiel=True,activo=True).order_by('id')
                data['biotipo'] = ParametroEstetico.objects.filter(biotipo=True,activo=True).order_by('id')
                data['tippiel'] = ParametroEstetico.objects.filter(tippiel=True,activo=True).order_by('id')
                data['eglogau'] = ParametroEstetico.objects.filter(eglogau=True,activo=True).order_by('id')
                data['linexpr'] = ParametroEstetico.objects.filter(linexpr=True,activo=True).order_by('id')
                data['sexo'] = Sexo.objects.filter().order_by('id')
                data['estadocivil'] = PersonaEstadoCivil.objects.filter().order_by('id')
                data['habitocorporal'] = TipoHabito.objects.filter(tipoestetico=ID_TIPO_CORPORAL,activo=True).order_by('id')
                data['tipopersona'] = TipoPersona.objects.filter().order_by('id')
                data['fechahoy'] = datetime.now()
                data['ID_TIPO_FACIAL'] = ID_TIPO_FACIAL
                data['ID_TIPO_CORPORAL'] = ID_TIPO_CORPORAL
                data['fechaactual'] = str(datetime.now().date().year)+"-"+str(datetime.now().date().month).zfill(2)+"-"+str(datetime.now().date().day).zfill(2)
                return render(request ,"historiaclinica/verficha.html" ,  data)
        else:
            search = None

            if 'info' in request.GET:
                data['info'] = request.GET['info']

            if 's' in request.GET:
                search = request.GET['s']

            if search:

                fichamedica = FichaMedica.objects.filter(Q(nombre__icontains=search) | Q(cedula__icontains=search) | Q(apellidos__icontains=search)).order_by('nombre')

            else:
                fichamedica = FichaMedica.objects.filter()
            paging = MiPaginador(fichamedica, 30)
            p = 1
            try:
                if 'page' in request.GET:
                    p = int(request.GET['page'])
                page = paging.page(p)
            except:
                page = paging.page(1)

            data['paging'] = paging
            data['rangospaging'] = paging.rangos_paginado(p)
            data['page'] = page
            data['search'] = search if search else ""
            data['fichamedicas'] = page.object_list

            if Consulta.objects.filter(guardado=False).exists():
                for c in Consulta.objects.filter(guardado=False):
                    fecha = c.fecha + timedelta(minutes=50)
                    if fecha < datetime.now():
                        if EvaluacionEstetica.objects.filter(consulta = c).exists():
                            evaluacionestetica = EvaluacionEstetica.objects.filter(consulta = c)
                            evaluacionestetica.delete()
                        c.delete()
            return render(request ,"historiaclinica/fichasmedicas.html" ,  data)