import json

from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template import RequestContext
from datetime import datetime, date

from settings import OTRODEPORTE, NIVEL_MALLA_UNO
from sga.commonviews import addUserData
from sga.models import Provincia, Canton, Carrera, Raza, Inscripcion, EncuestaItb, Grupo, Sexo, Genero, NucleoFamiliar, InscripcionGrupo, \
    PerfilInscripcion, Persona, ZonaResidencia, CondicionesHogar, MaterialCasa, TipoServicio, Afiliacion, \
    TipoIngresoHogar, TipoIngresoPropio, TipoEmpleo, Deporte, ManifestacionArtistica, TipoTransporte, UsoTransporte, \
    MotivoSeleccion, Matricula, Periodo, Nivel, DeseosFuturos
from med.models import PersonaEstadoCivil
from socioecon.models import InscripcionFichaSocioeconomica


def view(request):
    if request.method == 'POST':
        action = request.POST['action']

        if action =='preguardar':
            try:
                data = {'title': ''}

                nombre = list(request.POST.keys())[1]
                valor = request.POST[nombre]
                persona = int(request.POST['idpersona'])
                if not EncuestaItb.objects.filter(persona_id=persona).exists():
                    encuesta = EncuestaItb(persona_id=persona)
                    encuesta.save()

                # Compare and save if different
                    existencia = getattr(encuesta, nombre, None)
                    if existencia != valor:
                        setattr(encuesta, nombre, valor)  # Set the attribute dynamically
                        encuesta.save()
                    data['result'] = 'ok'
                    return HttpResponse(json.dumps(data), content_type="application/json")
                else:
                    encuesta = EncuestaItb.objects.filter(persona_id=persona)[:1].get()
                    existencia = getattr(encuesta, nombre, None)
                    if existencia != valor:
                        setattr(encuesta, nombre, valor)  # Set the attribute dynamically
                        encuesta.save()

                    data['result'] = 'ok'
                    return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}),content_type="application/json")

        if action == 'agregarencuesta':
            try:
                data = {'title': ''}

                sid = transaction.savepoint()

                fecha= datetime.now().strftime("%Y-%m-%d")
                hora_actual = datetime.now().time()

                carrera = Carrera.objects.get(pk=int(request.POST['carrera']))
                grupo = Grupo.objects.get(pk=int(request.POST['grupo']))
                provincia=Provincia.objects.get(pk=int(request.POST['provincianacimiento']))
                provinciavive=Provincia.objects.get(pk=int(request.POST['provinciavive']))
                ciudadnacimiento=Canton.objects.get(nombre=request.POST['cuidadnacimiento'])
                ciudadvive=Canton.objects.get(nombre=request.POST['ciudadvive'])
                sexo = Sexo.objects.get(pk=int(request.POST['sexo']))
                estadocivil = PersonaEstadoCivil.objects.get(pk=int(request.POST['estadocivil']))
                # if not InscripcionFichaSocioeconomica.objects.filter(inscripcion= request.POST['datainscripcion']).exists():
                deportes_seleccionados = request.POST.getlist('deporte')
                deportes = ','.join(deportes_seleccionados)
                if request.POST['otrodeporte'] !='':
                    otrodeporte = request.POST['otrodeporte']
                else:
                    otrodeporte=''
                opciones_seleccionados = request.POST.getlist('opciones')
                opcion = ','.join(opciones_seleccionados)
                deseos_seleccionados = request.POST.getlist('deseos')
                deseo = ','.join(deseos_seleccionados)

                if Persona.objects.filter(Q(cedula=request.POST['cedula'])|Q(pasaporte=request.POST['cedula'])).exists():
                    persona = Persona.objects.filter(Q(cedula=request.POST['cedula'])|Q(pasaporte=request.POST['cedula']))[:1].get()
                    if not persona.direccion:
                        persona.direccion = request.POST['direccion']
                    persona.estadocivilid = int(estadocivil.id)
                    persona.save()
                inscripcion =Inscripcion.objects.filter(persona_id =int(request.POST['idpersona']))[:1].get()
                if not PerfilInscripcion.objects.filter(inscripcion=inscripcion).exists():
                    perfil = PerfilInscripcion(inscripcion=inscripcion)
                    perfil.raza_id = int(request.POST['raza'])
                    perfil.save()
                if not InscripcionFichaSocioeconomica.objects.filter(inscripcion= inscripcion).exists():
                    socioeconomica = InscripcionFichaSocioeconomica(inscripcion=inscripcion,num_hijos =request.POST['num_hijos'])
                    socioeconomica.save()

                etnia=Raza.objects.get(pk=int(request.POST['raza']))

                if request.POST['familia'] == '1':
                    familia = True
                else:
                    familia =False
                if request.POST['amistad'] == '1':
                    amistad = True
                else:
                    amistad =False
                if request.POST['carreracheck'] == '1':
                    carreracheck = True
                else:
                    carreracheck = False
                if request.POST['empleocheck'] == '1':
                    empleocheck = True
                else:
                    empleocheck =False

                if  EncuestaItb.objects.filter(persona_id=int(request.POST['idpersona'])).exists():
                    encuesta =EncuestaItb.objects.filter(persona_id=int(request.POST['idpersona']))[:1].get()
                    encuesta.nombres =str(request.POST['nombres']).upper()
                    encuesta.apellidos=str(request.POST['apellidos']).upper()
                    encuesta.correo=str(request.POST['email']).lower()
                    encuesta.carrera =carrera
                    encuesta.grupo =grupo
                    encuesta.provincianacimiento=provincia
                    encuesta.ciudadnacimiento=ciudadnacimiento
                    encuesta.provinciavivienda=provinciavive
                    encuesta.ciudadvivienda=ciudadvive
                    encuesta.sexo=sexo
                    encuesta.genero_id=int(request.POST['genero'])
                    encuesta.telefono=request.POST['celular']
                    encuesta.direccion=str(request.POST['direccion']).upper()
                    encuesta.estadocivil=estadocivil
                    encuesta.numhijo=int(request.POST['num_hijos'])
                    encuesta.nucleofamiliar_id=int(request.POST['nucleo'])
                    encuesta.fechanacimiento=request.POST['fechanacimiento']
                    encuesta.edad = request.POST['edad']
                    encuesta.zona_id= int(request.POST['zonaresi'])
                    encuesta.condicion_id=int(request.POST['condiciones'])
                    encuesta.materialcasa_id=int(request.POST['materialcasa'])
                    encuesta.servicio_id=int(request.POST['servicio'])
                    encuesta.afiliacion_id=int(request.POST['afiliacion'])
                    encuesta.ingresohogar_id=int(request.POST['ingresohogar'])
                    encuesta.ingresopropio_id=int(request.POST['ingresopropio'])
                    encuesta.empleo_id=int(request.POST['empleo'])
                    encuesta.usotransporte_id= int(request.POST['usotransporte'])
                    encuesta.transporte_id= int(request.POST['transporte'])
                    encuesta.etnia=etnia
                    encuesta.manifestacion_id = int(request.POST['manifestacion']) # ,deporte=deporte
                    encuesta.familia = familia
                    encuesta.amistad = amistad
                    encuesta.duracioncarrera = carreracheck
                    encuesta.disponibilidadempleo = empleocheck
                    encuesta.deporte = deportes
                    encuesta.motivo = opcion
                    encuesta.deseo = deseo
                    encuesta.otrodeporte = otrodeporte
                    encuesta.estadorealizado=True
                    encuesta.fecharealizado = fecha
                    encuesta.inscripcion_id = inscripcion.id
                    encuesta.save()

                # encuesta = EncuestaItb(
                #                        nombres=str(request.POST['nombres']).upper(),apellidos=str(request.POST['apellidos']).upper(),
                #                        correo=str(request.POST['email']).lower(),telefono=str(request.POST['celular']),carrera=carrera,
                #                        provincianacimiento=provincia,ciudadnacimiento=ciudadnacimiento,provinciavivienda=provinciavive,
                #                        ciudadvivienda=ciudadvive,direccion=str(request.POST['direccion']).upper(),
                #                        fechanacimiento=request.POST['fechanacimiento'],grupo=grupo,etnia=raza,persona_id=int(request.POST['idpersona'])
                #
                #
                #                  )


                transaction.savepoint_commit(sid)
                data['result'] = 'ok'
                return HttpResponse(json.dumps(data),content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}),content_type="application/json")


        # elif action == 'buscarcedula':
        #     cedula = request.POST['cedula']
        #     data = {'title': ''}
        #     try:
        #         mensaje ='No coincide con el registro'
        #         persona = Persona.objects.filter(usuario = request.user)[:1].get()
        #         if cedula== persona.cedula or cedula ==persona.pasaporte:
        #         # if cedula:
        #             if Inscripcion.objects.filter(Q(persona__cedula=cedula)|Q(persona__pasaporte=cedula)).exists():
        #                 inscripcion = Inscripcion.objects.get(Q(persona__cedula=cedula)|Q(persona__pasaporte=cedula))
        #                 grupo = InscripcionGrupo.objects.get(inscripcion=inscripcion)
        #
        #                 data['datospersona'] = {"id": inscripcion.id,
        #                                         "nombres": inscripcion.persona.nombres,
        #                                         "apellidos": str(inscripcion.persona.apellido1) + ' ' +str(inscripcion.persona.apellido2),
        #                                         "nacimiento":inscripcion.persona.nacimiento.strftime('%Y-%m-%d'),
        #                                         "edad": inscripcion.persona.edad_actual(),
        #                                         "carrera": inscripcion.carrera.id,
        #                                         "grupo": grupo.grupo.id,
        #                                         "sexo": inscripcion.persona.sexo.id,
        #                                         "canton":inscripcion.persona.canton.nombre, #de nacimiento
        #                                         "provincia":inscripcion.persona.provincia.id, #de nacimiento
        #                                         "cantonres":inscripcion.persona.cantonresid.nombre, #de residencia
        #                                         "provinciares": inscripcion.persona.provinciaresid.id, # de residencia
        #                                         "direccion": inscripcion.persona.direccion,
        #                                         "telefono":inscripcion.persona.telefono,
        #                                         "estadocivil": inscripcion.persona.existen_datos_medicos().estadocivil.id if inscripcion.persona.existen_datos_medicos().estadocivil else 0,
        #                                         "etnia": inscripcion.raza().id if inscripcion.raza() else 0,
        #                                         "num_hijos": inscripcion.existe_fichasocioeconomico().num_hijos if inscripcion.existe_fichasocioeconomico() else 0 #numero de hijos
        #                                         }
        #                 data['result'] = 'ok'
        #                 return HttpResponse(json.dumps(data),content_type='application/json')
        #         return HttpResponse(json.dumps({'result': 'bad', 'message': mensaje}), content_type='application/json')
        #     except Exception as e:
        #         return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}), content_type="application/json")

        if action == 'buscarcantones':
            try:
                data = {'title': ''}
                listCan= []
                listCan.append({"id": 0, "nombre": "Seleccionar el Canton"})
                if Canton.objects.filter(provincia__id=int(request.POST['idprovincia'])).order_by("nombre").exists():
                    for g in Canton.objects.filter(provincia__id=int(request.POST['idprovincia'])).order_by("nombre"):
                        listCan.append({"id": g.id, "nombre": g.nombre})
                data['listacanton'] = listCan
                data['result'] = 'ok'
                return HttpResponse(json.dumps(data),content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}),content_type="application/json")


        if action == 'buscargrupo':
            try:
                data = {'title': ''}
                listGrupo= []
                listGrupo.append({"id": 0, "nombre": "Seleccionar el Grupo"})
                if Grupo.objects.filter(carrera__id=int(request.POST['idcarrera']),abierto=True).order_by("nombre").exists():
                    for g in Grupo.objects.filter(carrera__id=int(request.POST['idcarrera']),abierto=True).order_by("nombre"):
                        listGrupo.append({"id": g.id, "nombre": g.nombre})
                data['listGrupo'] = listGrupo
                data['result'] = 'ok'
                return HttpResponse(json.dumps(data),content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}),content_type="application/json")



    else:
        try:
            data = {'title': 'Encuesta Itb'}
            addUserData(request, data)
            persona = Persona.objects.filter(usuario=request.user)[:1].get()
            periodo = Periodo.objects.get(pk=request.session['periodo'].id)
            fecha_hoy = datetime.now()
            if Matricula.objects.filter(inscripcion__persona=persona, nivel__nivelmalla=NIVEL_MALLA_UNO,nivel__periodo__activo=True, nivel__cerrado=False).exists():  # and persona.id== 77890
                matricula = Matricula.objects.filter(inscripcion__persona=persona,nivel__nivelmalla=NIVEL_MALLA_UNO,nivel__periodo__activo=True, nivel__cerrado =False)[:1].get()
                inscripcion =Inscripcion.objects.filter(pk=matricula.inscripcion.id)[:1].get()
                if matricula.materia_asignada_testingreso(fecha_hoy) :
                # inscripcion =Inscripcion.objects.filter(pk=74994)[:1]. get()
                    grupo = InscripcionGrupo.objects.get(inscripcion=inscripcion)
                    if EncuestaItb.objects.filter(persona_id=persona, estadorealizado=True).exists():
                        return HttpResponseRedirect("/?info=Ya realizo la encuesta")
                    #     data['encuesta'] = encuesta
                    data['datainscripcion'] =inscripcion
                    data['datagrupo']= grupo
                    data['listcarrera'] = Carrera.objects.filter(activo=True)
                    data['listgrupo'] = Grupo.objects.filter()
                    data['lisprovincia'] = Provincia.objects.filter()
                    data['listaraza'] = Raza.objects.filter()
                    data['listsexo']= Sexo.objects.filter()
                    data['listgenero']=Genero.objects.filter()
                    data['listestadocivil']=PersonaEstadoCivil.objects.filter()
                    data['listnucleo']=NucleoFamiliar.objects.filter()
                    data['listzona']=ZonaResidencia.objects.filter()
                    data['listhogar']=CondicionesHogar.objects.filter()
                    data['listcasa']=MaterialCasa.objects.filter()
                    data['listservicio']=TipoServicio.objects.filter()
                    data['listafiliacion']=Afiliacion.objects.filter()
                    data['listingresohogar']=TipoIngresoHogar.objects.filter()
                    data['listingresopropio']=TipoIngresoPropio.objects.filter()
                    data['listempleo']=TipoEmpleo.objects.filter()
                    data['listusotrans'] = UsoTransporte.objects.filter()
                    data['listtransporte']=TipoTransporte.objects.filter()
                    data['listdeporte'] = Deporte.objects.filter()
                    data['listmanifestacion'] = ManifestacionArtistica.objects.filter()
                    data['listseleccion'] = MotivoSeleccion.objects.filter()
                    data['listdeseos'] = DeseosFuturos.objects.filter()
                    data['otrodeporte'] = OTRODEPORTE

                    if EncuestaItb.objects.filter(persona_id=persona, estadorealizado=False).exists():
                        encuesta = EncuestaItb.objects.filter(persona_id=persona, estadorealizado=False)[:1].get()
                        data['encuesta'] = encuesta
                    return render(request ,"encuestaitb/encuestaitbbs.html" ,  data)
                else:
                    return HttpResponseRedirect("/?info=Error comunicarse con el administrador ")
            else:
                return HttpResponseRedirect("/?info=Error comunicarse con el administrador ")
        except Exception as e:
            print(e)
            return HttpResponseRedirect("/?info=Error comunicarse con el administrador ")