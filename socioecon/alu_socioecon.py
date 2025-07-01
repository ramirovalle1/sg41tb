import json
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from settings import INSTITUCION, INSTITUTO_ITB, INSTITUTO_ITF, PERSONA_CUBRE_GASTOS_OTROS_ID, INSTITUTO_BUCK, NOMBRE_INSTITUCION, VALIDAR_ENTRADA_SISTEMA_CON_DEUDA, JR_USEROUTPUT_FOLDER, JR_JAVA_COMMAND, JR_RUN, DATABASES, JR_DB_TYPE, MEDIA_URL
from sga.commonviews import addUserData
from sga.models import Inscripcion
from socioecon.forms import SustentoHogarForm, TipoHogarForm, PersonaCubreGastoForm, NivelEstudioForm, OcupacionJefeHogarForm, CantidadBannoDuchaForm, TipoServicioHigienicoForm,\
     MaterialPisoForm, MaterialParedForm, TipoViviendaForm, CantidadTVColorHogarForm, CantidadVehiculoHogarForm, CantidadCelularHogarForm, \
     OcupacionEstudianteForm, IngresosEstudianteForm, BonoFmlaEstudianteForm
from socioecon.models import InscripcionFichaSocioeconomica, PersonaSustentaHogar, FormaTrabajo, TipoHogar, PersonaCubreGasto, NivelEstudio, OcupacionJefeHogar, \
     TipoVivienda, MaterialPared, MaterialPiso, CantidadBannoDucha, TipoServicioHigienico, CantidadTVColorHogar, CantidadCelularHogar, CantidadVehiculoHogar, \
     ParentezcoPersona,OcupacionEstudiante,IngresosEstudiante,BonoFmlaEstudiante


def ficha_socioeconomica_estudiante(inscripcion):
    if not inscripcion.inscripcionfichasocioeconomica_set.exists():
        fichasocioecon = InscripcionFichaSocioeconomica(inscripcion=inscripcion)
        fichasocioecon.save()
    else:
        fichasocioecon = inscripcion.inscripcionfichasocioeconomica_set.all()[:1].get()
    return fichasocioecon


@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            ficha = InscripcionFichaSocioeconomica.objects.get(pk=request.POST['fichaid'])

    #Check y selects sin puntaje
            if action=='changeescabezafamilia':
                if ficha.escabezafamilia:
                    ficha.escabezafamilia = False
                else:
                    ficha.escabezafamilia = True
                ficha.save()
                return HttpResponse(json.dumps({'result': 'ok'}),content_type="application/json")
            if action=='changep_msoltera':
                if ficha.p_msoltera:
                    ficha.p_msoltera = False
                else:
                    ficha.p_msoltera = True
                ficha.save()
                return HttpResponse(json.dumps({'result': 'ok'}),content_type="application/json")
            if action=='actualizanumhijos':
                try:
                    if request.POST['numh'] == '':
                        ficha.num_hijos = 0
                    else:
                        ficha.num_hijos = int(request.POST['numh'])
                    ficha.save()
                    return HttpResponse(json.dumps({'result': 'ok'}),content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({'result': 'bad' + str(e)}),content_type="application/json")


            if action=='actualizamiembrosfmla':
                if request.POST['nummiembros'] == '':
                    ficha.cantidadmiembros = None
                else:
                    ficha.cantidadmiembros = request.POST['nummiembros']
                ficha.save()
                return HttpResponse(json.dumps({'result': 'ok'}),content_type="application/json")

            elif action=='changeesdependiente':
                if ficha.esdependiente:
                    ficha.esdependiente = False
                else:
                    ficha.esdependiente = True
                ficha.save()
                return HttpResponse(json.dumps({'result': 'ok'}),content_type="application/json")

            elif action=='tipohogar':
                th = TipoHogar.objects.get(pk=request.POST['th'])
                ficha.tipohogar = th
                ficha.save()
                return HttpResponse(json.dumps({'result': 'ok'}),content_type="application/json")

            elif action=='personacubregasto':
                pcg = PersonaCubreGasto.objects.get(pk=request.POST['pcg'])
                otrosg = request.POST['otrosg']
                ficha.personacubregasto = pcg
                ficha.otroscubregasto = otrosg
                ficha.save()
                return HttpResponse(json.dumps({'result': 'ok'}),content_type="application/json")

        #Adicionar Sustentos Hogar
            elif action=='addsustentohogar':
                persona = request.POST['persona']
                formatrabajo = FormaTrabajo.objects.get(pk=int(request.POST['ft']))
                parentezco = ParentezcoPersona.objects.get(pk=int(request.POST['parentezco']))
                ingresomensual = float(request.POST['im'])
                sustento = PersonaSustentaHogar(persona=persona,
                                                parentezco=parentezco,
                                                formatrabajo=formatrabajo,
                                                ingresomensual=ingresomensual)
                sustento.save()
                ficha.sustentahogar.add(sustento)
                ficha.save()
                return HttpResponse(json.dumps({'result': 'ok'}),content_type="application/json")

            elif action=='dedicacion':
                dd = OcupacionEstudiante.objects.get(pk=request.POST['dd'])
                ficha.ocupacionestudiante = dd
                ficha.save()
                return HttpResponse(json.dumps({'result': 'ok'}),content_type="application/json")

            elif action=='ingresos':
                ie = IngresosEstudiante.objects.get(pk=request.POST['ie'])
                ficha.ingresoestudiante = ie
                ficha.save()
                return HttpResponse(json.dumps({'result': 'ok'}),content_type="application/json")

            elif action=='bonodh':
                be = BonoFmlaEstudiante.objects.get(pk=request.POST['be'])
                ficha.bonofmlaestudiante = be
                ficha.save()
                return HttpResponse(json.dumps({'result': 'ok'}),content_type="application/json")

    #Comienzan los check y selects con puntaje

        #Actividades Economicas del Hogar
            elif action=='changealguienafiliado':
                if ficha.alguienafiliado:
                    ficha.alguienafiliado = False
                    ficha.val_alguienafiliado = 0
                else:
                    ficha.alguienafiliado = True
                    ficha.val_alguienafiliado = 39
                ficha.save()
                return HttpResponse(json.dumps({'result': 'ok'}),content_type="application/json")

            elif action=='changealguienseguro':
                if ficha.alguienseguro:
                    ficha.alguienseguro = False
                    ficha.val_alguienseguro = 0
                else:
                    ficha.alguienseguro = True
                    ficha.val_alguienseguro = 55
                ficha.save()
                return HttpResponse(json.dumps({'result': 'ok'}),content_type="application/json")

        #Habitos de Consumo
            elif action=='changecompravestcc':
                if ficha.compravestcc:
                    ficha.compravestcc = False
                    ficha.val_compravestcc = 0
                else:
                    ficha.compravestcc = True
                    ficha.val_compravestcc = 6
                ficha.save()
                return HttpResponse(json.dumps({'result': 'ok'}),content_type="application/json")
            elif action=='changeusainternetseism':
                if ficha.usainternetseism:
                    ficha.usainternetseism = False
                    ficha.val_usainternetseism = 0
                else:
                    ficha.usainternetseism = True
                    ficha.val_usainternetseism = 26
                ficha.save()
                return HttpResponse(json.dumps({'result': 'ok'}),content_type="application/json")
            elif action=='changeusacorreonotrab':
                if ficha.usacorreonotrab:
                    ficha.usacorreonotrab = False
                    ficha.val_usacorreonotrab = 0
                else:
                    ficha.usacorreonotrab = True
                    ficha.val_usacorreonotrab = 27
                ficha.save()
                return HttpResponse(json.dumps({'result': 'ok'}),content_type="application/json")
            elif action=='changeregistroredsocial':
                if ficha.registroredsocial:
                    ficha.registroredsocial = False
                    ficha.val_registroredsocial = 0
                else:
                    ficha.registroredsocial = True
                    ficha.val_registroredsocial = 28
                ficha.save()
                return HttpResponse(json.dumps({'result': 'ok'}),content_type="application/json")
            elif action=='changeleidolibrotresm':
                if ficha.leidolibrotresm:
                    ficha.leidolibrotresm = False
                    ficha.val_leidolibrotresm = 0
                else:
                    ficha.leidolibrotresm = True
                    ficha.val_leidolibrotresm = 12
                ficha.save()
                return HttpResponse(json.dumps({'result': 'ok'}),content_type="application/json")

        #Posesion de Bienes
            elif action=='changetienetelefconv':
                if ficha.tienetelefconv:
                    ficha.tienetelefconv = False
                    ficha.val_tienetelefconv = 0
                else:
                    ficha.tienetelefconv = True
                    ficha.val_tienetelefconv = 19
                ficha.save()
                return HttpResponse(json.dumps({'result': 'ok'}),content_type="application/json")
            elif action=='changetienecocinahorno':
                if ficha.tienecocinahorno:
                    ficha.tienecocinahorno = False
                    ficha.val_tienecocinahorno = 0
                else:
                    ficha.tienecocinahorno = True
                    ficha.val_tienecocinahorno = 29
                ficha.save()
                return HttpResponse(json.dumps({'result': 'ok'}),content_type="application/json")
            elif action=='changetienerefrig':
                if ficha.tienerefrig:
                    ficha.tienerefrig = False
                    ficha.val_tienerefrig = 0
                else:
                    ficha.tienerefrig = True
                    ficha.val_tienerefrig = 30
                ficha.save()
                return HttpResponse(json.dumps({'result': 'ok'}),content_type="application/json")
            elif action=='changetienelavadora':
                if ficha.tienelavadora:
                    ficha.tienelavadora = False
                    ficha.val_tienelavadora = 0
                else:
                    ficha.tienelavadora = True
                    ficha.val_tienelavadora = 18
                ficha.save()
                return HttpResponse(json.dumps({'result': 'ok'}),content_type="application/json")
            elif action=='changetienemusica':
                if ficha.tienemusica:
                    ficha.tienemusica = False
                    ficha.val_tienemusica = 0
                else:
                    ficha.tienemusica = True
                    ficha.val_tienemusica = 18
                ficha.save()
                return HttpResponse(json.dumps({'result': 'ok'}),content_type="application/json")

        #Acceso a la Tecnologia
            elif action=='changetieneinternet':
                if ficha.tieneinternet:
                    ficha.tieneinternet = False
                    ficha.val_tieneinternet = 0
                else:
                    ficha.tieneinternet = True
                    ficha.val_tieneinternet = 45
                ficha.save()
                return HttpResponse(json.dumps({'result': 'ok'}),content_type="application/json")
            elif action=='changetienedesktop':
                if ficha.tienedesktop:
                    ficha.tienedesktop = False
                    ficha.val_tienedesktop = 0
                else:
                    ficha.tienedesktop = True
                    ficha.val_tienedesktop = 35
                ficha.save()
                return HttpResponse(json.dumps({'result': 'ok'}),content_type="application/json")
            elif action=='changetienelaptop':
                if ficha.tienelaptop:
                    ficha.tienelaptop = False
                    ficha.val_tienelaptop = 0
                else:
                    ficha.tienelaptop = True
                    ficha.val_tienelaptop = 39
                ficha.save()
                return HttpResponse(json.dumps({'result': 'ok'}),content_type="application/json")

        #Nivel de Educacion del Jefe de Hogar
            elif action=='niveljefehogar':
                niveleducacion = NivelEstudio.objects.get(pk=request.POST['niveledu'])
                ficha.niveljefehogar = niveleducacion
                ficha.val_niveljefehogar = niveleducacion.puntaje
                ficha.save()
                return HttpResponse(json.dumps({'result': 'ok'}),content_type="application/json")

        #Ocupacion del Jefe de Hogar
            elif action=='ocupacionjefehogar':
                ocupacion = OcupacionJefeHogar.objects.get(pk=request.POST['ocupacion'])
                ficha.ocupacionjefehogar = ocupacion
                ficha.val_ocupacionjefehogar = ocupacion.puntaje
                ficha.save()
                return HttpResponse(json.dumps({'result': 'ok'}),content_type="application/json")

        #Tipo de Vivienda
            elif action=='tipovivienda':
                tipovivienda = TipoVivienda.objects.get(pk=request.POST['tipovivienda'])
                ficha.tipovivienda = tipovivienda
                ficha.val_tipovivienda = tipovivienda.puntaje
                ficha.save()
                return HttpResponse(json.dumps({'result': 'ok'}),content_type="application/json")

        #Material predominante en Paredes
            elif action=='materialpared':
                materialpared = MaterialPared.objects.get(pk=request.POST['materialpared'])
                ficha.materialpared = materialpared
                ficha.val_materialpared = materialpared.puntaje
                ficha.save()
                return HttpResponse(json.dumps({'result': 'ok'}),content_type="application/json")

        #Material predominante en Pisos
            elif action=='materialpiso':
                materialpiso = MaterialPiso.objects.get(pk=request.POST['materialpiso'])
                ficha.materialpiso = materialpiso
                ficha.val_materialpiso = materialpiso.puntaje
                ficha.save()
                return HttpResponse(json.dumps({'result': 'ok'}),content_type="application/json")

        #Cantidad de bannos con duchas
            elif action=='cantbannoducha':
                cantbannoducha = CantidadBannoDucha.objects.get(pk=request.POST['cantduchas'])
                ficha.cantbannoducha = cantbannoducha
                ficha.val_cantbannoducha = cantbannoducha.puntaje
                ficha.save()
                return HttpResponse(json.dumps({'result': 'ok'}),content_type="application/json")

        #Tipo de Servicio Higienico
            elif action=='tiposervhig':
                tiposervhig = TipoServicioHigienico.objects.get(pk=request.POST['tiposervh'])
                ficha.tiposervhig = tiposervhig
                ficha.val_tiposervhig = tiposervhig.puntaje
                ficha.save()
                return HttpResponse(json.dumps({'result': 'ok'}),content_type="application/json")

        #Cantidad de TV a color
            elif action=='canttvcolor':
                canttv = CantidadTVColorHogar.objects.get(pk=request.POST['canttv'])
                ficha.canttvcolor = canttv
                ficha.val_canttvcolor = canttv.puntaje
                ficha.save()
                return HttpResponse(json.dumps({'result': 'ok'}),content_type="application/json")

        #Cantidad de Vehiculos
            elif action=='cantvehiculos':
                cantveh = CantidadVehiculoHogar.objects.get(pk=request.POST['cantveh'])
                ficha.cantvehiculos = cantveh
                ficha.val_cantvehiculos = cantveh.puntaje
                ficha.save()
                return HttpResponse(json.dumps({'result': 'ok'}),content_type="application/json")

        #Cantidad de Celulares
            elif action=='cantcelulares':
                cantcel = CantidadCelularHogar.objects.get(pk=request.POST['cantcel'])
                ficha.cantcelulares = cantcel
                ficha.val_cantcelulares = cantcel.puntaje
                ficha.save()
                return HttpResponse(json.dumps({'result': 'ok'}),content_type="application/json")


        # Cantidad miembros familia
            elif action=='actualizamiembrosfmla':
                if request.POST['num_miembros'] == '':
                    ficha.cantidadmiembros = None
                else:
                    ficha.cantidadmiembros = request.POST['num_miembros']

                ficha.save()
                return HttpResponse(json.dumps({'result': 'ok'}),content_type="application/json")

            return HttpResponse(json.dumps({'result': 'bad'}),content_type="application/json")

        else:
            data = {'title': 'Ficha SocioEconomica del Estudiante'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']
                if action=='delsustento':
                    if PersonaSustentaHogar.objects.filter(pk=request.GET['id']).exists():
                        sustento = PersonaSustentaHogar.objects.get(pk=request.GET['id'])
                        sustento.delete()
                        return HttpResponseRedirect("/alu_socioecon")

                return HttpResponseRedirect("/alu_socioecon")
            else:
                try:

                    if Inscripcion.objects.filter(persona=request.session['persona']).exists():
                        inscripcion = Inscripcion.objects.filter(persona=request.session['persona'])[:1].get()
                        data['inscripcion'] = inscripcion

                        #Comprobar que no tenga deudas para que no pueda usar el sistema
                        if VALIDAR_ENTRADA_SISTEMA_CON_DEUDA and inscripcion.tiene_deuda():
                            return HttpResponseRedirect("/")

                        ficha = ficha_socioeconomica_estudiante(inscripcion)
                        data['ficha'] = ficha

                        #Sustentos del hogar Form
                        data['form_sustento'] = SustentoHogarForm(initial={'ingresomensual': 0.00})
                        #Tipos de Hogares Form
                        data['form_tipohogar'] = TipoHogarForm()
                        #Quien cubre el gasto del estudiante Form
                        data['form_personacubregasto'] = PersonaCubreGastoForm()
                        data['personacubregasto_OTROS_ID'] = PERSONA_CUBRE_GASTOS_OTROS_ID
                        #Nivel de Educacion de Jefe de Hogar Form
                        data['form_niveljefehogar'] = NivelEstudioForm()
                        #Ocupacion de Jefe de Hogar Form
                        data['form_ocupacionjefehogar'] = OcupacionJefeHogarForm()

                         #Tipo de Vivienda Form
                        data['form_tipovivienda'] = TipoViviendaForm()
                        #Material predomina en Paredes Form
                        data['form_materialpared'] = MaterialParedForm()
                        #Material predomina en Piso Form
                        data['form_materialpiso'] = MaterialPisoForm()
                        #Cantidad de Banos con Duchas Form
                        data['form_cantbannoducha'] = CantidadBannoDuchaForm()
                        #Tipo de Servicio Higienico Form
                        data['form_tiposervhig'] = TipoServicioHigienicoForm()
                        #Cantidad de TV a color Form
                        data['form_canttvcolor'] = CantidadTVColorHogarForm()
                        #Cantidad de Vehiculos Form
                        data['form_cantvehiculos'] = CantidadVehiculoHogarForm()
                        #Cantidad de Celulares Form
                        data['form_cantcelulares'] = CantidadCelularHogarForm()

                        # Nuevos datos en ficha socioeconomica 11-dic-2017
                        data['form_ocupacionestudiante'] = OcupacionEstudianteForm()
                        data['form_ingresosestudiante']  = IngresosEstudianteForm()
                        data['form_bonofmlaestudiante']  = BonoFmlaEstudianteForm()

                        #Logo de cada institucion que tenga el modulo de ficha socioeconomica
                        data['INSTITUTO'] = [INSTITUCION, INSTITUTO_ITB, INSTITUTO_ITF, INSTITUTO_BUCK]

                        # #Obtain client ip address
                        # client_address = ip_client_address(request)
                        #
                        # # Log de FICHA SOCIOECONOMICA
                        # LogEntry.objects.log_action(
                        #     user_id         = request.user.pk,
                        #     content_type_id = ContentType.objects.get_for_model(ficha).pk,
                        #     object_id       = ficha.id,
                        #     object_repr     = force_str(ficha),
                        #     action_flag     = ADDITION,
                        #     change_message  = 'Alumno Ficha Socioecon (' + client_address + ')'  )

                        return render(request ,"alu_socioecon/ficha.html" ,  data)
                    else:
                        return HttpResponseRedirect("/")

                except Exception as ex:
                    return HttpResponseRedirect("/")


    except Exception as ex:
                return HttpResponseRedirect("/")