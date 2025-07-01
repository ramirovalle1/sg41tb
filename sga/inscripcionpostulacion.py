from datetime import datetime, timedelta
from decimal import Decimal
import json
from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.http import HttpResponse
from django.utils.encoding import force_str
import psycopg2
from med.models import PersonaExtension, PersonaFichaMedica, PersonaExamenFisico
from settings import DEFAULT_PASSWORD, USA_CORREO_INSTITUCIONAL, CORREO_INSTITUCIONAL, EMAIL_ACTIVE, ALUMNOS_GROUP_ID, INSCRIPCION_CONDUCCION, GENERAR_RUBROS_PAGO, GENERAR_RUBRO_INSCRIPCION, DESCUENTO_REFERIDO, HABILITA_DESC_INSCRIPCION, DESCUENTO_INSCRIPCION, GENERAR_RUBRO_INSCRIPCION_MARGEN_DIAS, UTILIZA_NIVEL0_PROPEDEUTICO, UTILIZA_GRUPOS_ALUMNOS, NIVEL_MALLA_UNO, ID_USUARIO_RUDY, ID_MOTIVO_BECA_MUNICIPIO, ID_TIPOBECA, ID_MOTIVO_BECA_TEC
from sga.commonviews import ip_client_address
from sga.docentes import calculate_username
from sga.models import Carrera, Modalidad, Sexo, Canton, Provincia, Parroquia, Nacionalidad, Inscripcion, Persona, TipoSangre, elimina_tildes, EmpresaConvenio, PerfilInscripcion, DocumentosDeInscripcion, ProcesoDobleMatricula, Sesion, InscripcionGrupo, RubrosConduccion, Rubro, RubroOtro, ReferidosInscripcion, InscripcionAspirantes, InscripcionVendedor, Descuento, DetalleDescuento, RubroInscripcion, Grupo, RetiradoMatricula, Matricula, SolicitudBeca, RubroCuota, TablaDescuentoBeca, RubroMatricula, HistorialGestionBeca, Resolucionbeca
from socioecon.models import InscripcionFichaSocioEconomicaBeca, ReferenciaPersonal, DatoResidente, DatoTrabajo, Detallevivienda, EnfermedadFamilia, DetalleIngrexEgres, DatosAcademicos, InscripcionFichaSocioeconomica, ReferenciaBeca


def view(request):
    """

    :param request:
    :return:
    """
    if request.method == 'POST':
        action = request.POST['a']

        if action == 'inscribirpostulacionbeca':
                try:
                    resultado = {}
                    identificacion = ''
                    sid = transaction.savepoint()
                    carrera = Carrera.objects.get(id=int(request.POST['idcarrera']))
                    modalidad = Modalidad.objects.get(id=int(request.POST['idmodalidad']))
                    sesion = Sesion.objects.get(id=int(request.POST['idsesion']))
                    gensexo = Sexo.objects.get(id=int(request.POST['idsexo']))
                    cantonresidencia = Canton.objects.get(id=int(request.POST['idcanton']))
                    provinciaresidencia = Provincia.objects.get(id=int(request.POST['idprovincia']))
                    parroquiaresidencia = Parroquia.objects.get(id=int(request.POST['idparroquia']))
                    nacionalidad=Nacionalidad.objects.get(pk=1)


                    if int(request.POST['idtiposangre'])>0:
                        sangre = TipoSangre.objects.get(id=int(request.POST['idtiposangre']))
                    else:
                        sangre = None

                    if(int(request.POST['idcantonacimiento'])>0):
                        cantonnacimiento = Canton.objects.get(id=int(request.POST['idcantonacimiento']))
                    else:
                        cantonnacimiento = None
                    if (int(request.POST['idprovincianacimiento']) > 0):
                        provincianacimiento = Provincia.objects.get(id=int(request.POST['idprovincianacimiento']))
                    else:
                        provincianacimiento = None

                    if (str(request.POST['titulo']) == 'true'):
                        titulo = True
                    else:
                        titulo = False

                    if (str(request.POST['actagrado']) == 'true'):
                        actagrado = True
                    else:
                        actagrado = False

                    if (str(request.POST['copiacedula']) == 'true'):
                        copiacedula = True
                    else:
                        copiacedula = False

                    if (str(request.POST['copiapapeletavota']) == 'true'):
                        copiapapeletavota = True
                    else:
                        copiapapeletavota = False

                    if (str(request.POST['fechanacimiento']) == ''):
                        fechanacimiento = None
                    else:
                        fechanacimiento = str(request.POST['fechanacimiento'])

                    if (str(request.POST['tienediscapacidad']) == 'true'):
                        tienediscapacidad = True
                    else:
                        tienediscapacidad = False

                    if (str(request.POST['extranjero']) == 'true'):
                        extranjero = True
                        identificacion = request.POST['identificacion']
                    else:
                        extranjero = False
                        identificacion = request.POST['identificacion']

                    if (str(request.POST['actafirmada']) == 'true'):
                        actafirmada = True
                    else:
                        actafirmada = False

                    if (str(request.POST['foto']) == 'true'):
                        foto = True
                    else:
                        foto = False

                    existe=False
                    insecontrada=None

                    # if  Inscripcion.objects.filter(persona__cedula=identificacion,carrera=carrera).exclude(persona__cedula=None).exclude(persona__cedula='').exists():
                    #       insecontrada= Inscripcion.objects.filter(persona__cedula=identificacion,carrera=carrera)[:1].get()
                    #       existe=True
                    #
                    # elif Inscripcion.objects.filter(persona__pasaporte=identificacion,carrera=carrera).exclude(persona__pasaporte=None).exclude(persona__pasaporte='').exists():
                    #       insecontrada= Inscripcion.objects.filter(persona__pasaporte=identificacion,carrera=carrera)[:1].get()
                    #       existe=True

                    if existe==False:
                        persona = Persona(nombres=elimina_tildes(request.POST['nombres']),
                              apellido1=elimina_tildes(request.POST['apellido1']),
                              apellido2=elimina_tildes(request.POST['apellido2']),
                              extranjero=extranjero,
                              cedula=identificacion,
                              nacimiento=fechanacimiento,
                              provincia=provincianacimiento,
                              canton=cantonnacimiento,
                              sexo=gensexo,
                              nacionalidad=nacionalidad,
                              direccion=str(elimina_tildes(request.POST['calleprincipal'])).upper(),
                              num_direccion=str(request.POST['numerodomicilio']).upper(),
                              sector=str(request.POST['sectorresidencia']).upper(),
                              provinciaresid=provinciaresidencia,
                              cantonresid=cantonresidencia,
                              telefono=str(request.POST['celular']),
                              telefono_conv=str(request.POST['telefono']),
                              email=elimina_tildes(request.POST['correo']).lower(),
                              email1=elimina_tildes(request.POST['correo']).lower(),
                              email2=elimina_tildes(request.POST['correoalternativo']).lower(),
                              parroquia=parroquiaresidencia,
                              sangre=sangre)
                        persona.save()

                        username = calculate_username(persona)
                        password = DEFAULT_PASSWORD
                        user = User.objects.create_user(username, persona.email, password)
                        user.save()
                        persona.usuario = user
                        if USA_CORREO_INSTITUCIONAL:
                            persona.emailinst = user.username + '' + CORREO_INSTITUCIONAL
                        else:
                            persona.emailinst = ''
                        persona.save()


                        doblematricula=False


                          # 1 si el por el municipio de guayaquil y 2 si son las becas del gobierno
                        if int(request.POST['coveniosolicitud'])==1:
                            convenioninstituciona = EmpresaConvenio.objects.get(pk=1)
                        else:
                            convenioninstituciona = EmpresaConvenio.objects.get(pk=29)

                        # if Inscripcion.objects.filter(persona__cedula=identificacion).exclude(persona__cedula=None).exclude(
                        #         persona__cedula='').exists():
                        #     doblematricula = True
                        # if Inscripcion.objects.filter(persona__pasaporte=identificacion).exclude(
                        #         persona__pasaporte=None).exclude(persona__pasaporte='').exists():
                        #     doblematricula = True

                        inscripcion = Inscripcion(persona=persona,
                                                  fecha=datetime.now(),
                                                  carrera=carrera,
                                                  modalidad=modalidad,
                                                  sesion=sesion,
                                                  tienediscapacidad=tienediscapacidad,
                                                  doblematricula=doblematricula,
                                                  observacion=str(request.POST['motivoinscripcion']).upper(),
                                                  empresaconvenio=convenioninstituciona)


                        # Verifica que no se cree una Inscripcion doble (misma Cedula y Carrera)
                        if not Inscripcion.objects.filter(persona__cedula=persona.cedula, carrera=carrera,
                                              persona__pasaporte=persona.pasaporte).exists():

                            i = Inscripcion.objects.latest('id') if Inscripcion.objects.exists() else None
                            if i:
                                inscripcion.numerom = i.numerom + 1
                            else:
                                inscripcion.numerom = 1


                            inscripcion.save()

                            # Crear el registro en el Perfil de Inscripciones si es discapacitado para el DOBE
                            if inscripcion.tienediscapacidad:
                                perfil = PerfilInscripcion(inscripcion=inscripcion, tienediscapacidad=True)
                                perfil.save()

                            if inscripcion.doblematricula:
                                px = ''
                                doblemat = ProcesoDobleMatricula(inscripcion=inscripcion, aprobado=False, fecha=datetime.now())
                                doblemat.save()

                                # obtengo informacion de ficha medica completa para grabar en nueva inscripcion OCU 28-03-2016
                                if PersonaExtension.objects.filter(persona__cedula=persona.cedula).exclude(
                                        persona__cedula='').exists() or PersonaExtension.objects.filter(
                                        persona__pasaporte=persona.pasaporte).exclude(persona__pasaporte='').exists():
                                    if PersonaExtension.objects.filter(persona__cedula=persona.cedula).exclude(
                                            persona__cedula='').exists():
                                        for p in PersonaExtension.objects.filter(persona__cedula=persona.cedula).exclude(
                                                persona__cedula=''):
                                            if not p.persona.datos_medicos_incompletos():
                                                px = p
                                    else:
                                        # obtengo informacion de ficha medica completa para grabar en nueva inscripcion OCU 31-03-2016
                                        for p in PersonaExtension.objects.filter(persona__pasaporte=persona.pasaporte).exclude(
                                                persona__pasaporte=''):
                                            if not p.persona.datos_medicos_incompletos():
                                                px = p
                                    if px!='':
                                        if not px.persona.datos_medicos_incompletos():

                                            personaext = PersonaExtension(persona=persona,
                                                                          estadocivil=px.estadocivil,
                                                                          tienelicencia=px.tienelicencia,
                                                                          tipolicencia=px.tipolicencia,
                                                                          telefonos=px.telefonos,
                                                                          tieneconyuge=px.tieneconyuge,
                                                                          hijos=px.hijos,
                                                                          padre=px.padre,
                                                                          edadpadre=px.edadpadre,
                                                                          estadopadre=px.estadopadre,
                                                                          telefpadre=px.telefpadre,
                                                                          educacionpadre=px.educacionpadre,
                                                                          profesionpadre=px.profesionpadre,
                                                                          trabajopadre=px.trabajopadre,
                                                                          madre=px.madre,
                                                                          edadmadre=px.edadmadre,
                                                                          estadomadre=px.estadomadre,
                                                                          telefmadre=px.telefmadre,
                                                                          educacionmadre=px.educacionmadre,
                                                                          profesionmadre=px.profesionmadre,
                                                                          trabajomadre=px.trabajomadre,
                                                                          conyuge=px.conyuge,
                                                                          edadconyuge=px.edadconyuge,
                                                                          estadoconyuge=px.estadoconyuge,
                                                                          telefconyuge=px.telefconyuge,
                                                                          educacionconyuge=px.educacionconyuge,
                                                                          profesionconyuge=px.profesionconyuge,
                                                                          trabajoconyuge=px.trabajoconyuge,
                                                                          enfermedadpadre=px.enfermedadpadre,
                                                                          enfermedadmadre=px.enfermedadmadre,
                                                                          enfermedadabuelos=px.enfermedadabuelos,
                                                                          enfermedadhermanos=px.enfermedadhermanos,
                                                                          enfermedadotros=px.enfermedadotros)
                                            personaext.save()

                                            # Ficha Medica
                                            if PersonaFichaMedica.objects.filter(personaextension=px).exists():
                                                pfm = PersonaFichaMedica.objects.get(personaextension=px)
                                                personafmedica = PersonaFichaMedica(personaextension=personaext,
                                                                                    vacunas=pfm.vacunas,
                                                                                    nombrevacunas=pfm.nombrevacunas,
                                                                                    enfermedades=pfm.enfermedades,
                                                                                    nombreenfermedades=pfm.nombreenfermedades,
                                                                                    alergiamedicina=pfm.alergiamedicina,
                                                                                    nombremedicinas=pfm.nombremedicinas,
                                                                                    alergiaalimento=pfm.alergiaalimento,
                                                                                    nombrealimentos=pfm.nombrealimentos,
                                                                                    cirugias=pfm.cirugias,
                                                                                    nombrecirugia=pfm.nombrecirugia,
                                                                                    fechacirugia=pfm.fechacirugia,
                                                                                    aparato=pfm.aparato,
                                                                                    tipoaparato=pfm.tipoaparato,
                                                                                    gestacion=pfm.gestacion,
                                                                                    partos=pfm.partos,
                                                                                    abortos=pfm.abortos,
                                                                                    cesareas=pfm.cesareas,
                                                                                    hijos2=pfm.hijos2,
                                                                                    cigarro=pfm.cigarro,
                                                                                    numerocigarros=pfm.numerocigarros,
                                                                                    tomaalcohol=pfm.tomaalcohol,
                                                                                    tipoalcohol=pfm.tipoalcohol,
                                                                                    copasalcohol=pfm.copasalcohol,
                                                                                    tomaantidepresivos=pfm.tomaantidepresivos,
                                                                                    antidepresivos=pfm.antidepresivos,
                                                                                    tomaotros=pfm.tomaotros,
                                                                                    otros=pfm.otros,
                                                                                    horassueno=pfm.horassueno,
                                                                                    calidadsuenno=pfm.calidadsuenno)
                                                personafmedica.save()

                                            # Examen Fisico
                                            if PersonaExamenFisico.objects.filter(personafichamedica__personaextension=px).exists():
                                                pef = PersonaExamenFisico.objects.get(personafichamedica__personaextension=px)
                                                personaef = PersonaExamenFisico(personafichamedica=personafmedica,
                                                                                inspeccion=pef.inspeccion,
                                                                                usalentes=pef.usalentes,
                                                                                motivo=pef.motivo,
                                                                                peso=pef.peso,
                                                                                talla=pef.talla,
                                                                                pa=pef.pa,
                                                                                pulso=pef.pulso,
                                                                                rcar=pef.rcar,
                                                                                rresp=pef.rresp,
                                                                                temp=pef.temp,
                                                                                observaciones=pef.observaciones)
                                                personaef.save()

                                # Verificar documentos en secretaria con cedula 31-03-2016 OCU ok

                                if Inscripcion.objects.filter(persona__cedula=persona.cedula).exclude(
                                        persona__cedula='').exists() or Inscripcion.objects.filter(
                                        persona__pasaporte=persona.pasaporte).exclude(persona__pasaporte='').exists():
                                    if Inscripcion.objects.filter(persona__cedula=persona.cedula).exclude(
                                            persona__cedula='').exists():
                                        perins = Inscripcion.objects.filter(persona__cedula=persona.cedula).order_by('id')[
                                                 :1].get()
                                        doc_insc = DocumentosDeInscripcion.objects.filter(inscripcion=perins)[:1].get()
                                    else:
                                        perins = Inscripcion.objects.filter(persona__pasaporte=persona.pasaporte).order_by(
                                            'id')[:1].get()
                                        doc_insc = DocumentosDeInscripcion.objects.filter(inscripcion=perins)[:1].get()
                                    if doc_insc:
                                        insdoc = DocumentosDeInscripcion(inscripcion=inscripcion,
                                                                         titulo=titulo,
                                                                         acta=actagrado,
                                                                         cedula=copiacedula,
                                                                         votacion=copiapapeletavota,
                                                                         fotos=foto,
                                                                         actafirmada=actafirmada)
                                        insdoc.save()

                            if EMAIL_ACTIVE and inscripcion.doblematricula:
                                doblemat.mail_procesodoblematricula(persona, inscripcion.carrera.nombre, request.user)
                    else:
                        inscripcion=insecontrada
                        user=inscripcion.persona.usuario

                        if inscripcion.matricula():
                             return HttpResponse(json.dumps({"result":"bad","error":str('El estudiante esta matriculado actualmente')}), content_type="application/json")

                        # if Rubro.objects.filter(inscripcion=inscripcion).exists():
                        #      return HttpResponse(json.dumps({"result":"bad","error":str('El estudiante tiene rubro en sus finanzas')}), content_type="application/json")




                    if UTILIZA_GRUPOS_ALUMNOS:
                        if int(request.POST['grupo'])>0 :
                            grupo = Grupo.objects.get(id=request.POST['grupo'])
                            for x in InscripcionGrupo.objects.filter(inscripcion=inscripcion):
                                x.activo=False
                                x.save()
                            if InscripcionGrupo.objects.filter(inscripcion=inscripcion,grupo=grupo).exists():
                                ig=InscripcionGrupo.objects.filter(inscripcion=inscripcion,grupo=grupo).order_by('-id')[:1].get()
                                ig.activo=True
                            else:
                                ig = InscripcionGrupo(inscripcion=inscripcion, grupo=grupo, activo=True)
                            ig.save()


                        #Actualizar el estado del Grupo
                        if grupo.abierto:
                            grupo.abierto = grupo.esta_abierto()
                            grupo.save()

                        # Precios de Carrera segun grupo
                        pcg = grupo.precios()
                        valor =0
                        if INSCRIPCION_CONDUCCION:
                            if RubrosConduccion.objects.filter(carrera=inscripcion.carrera).exists():
                                r = RubrosConduccion.objects.filter(carrera=inscripcion.carrera)[:1].get()
                                rubro = Rubro(fecha=datetime.now(),valor=r.precio,inscripcion=inscripcion,cancelado=False,fechavence=ig.grupo.fin)
                                rubro.save()
                                #Se crea el tipo de Rubro Otro q es de tipo Derecho Examen
                                rubroo = RubroOtro(rubro=rubro, tipo=r.tipo, descripcion=r.descripcion)
                                rubroo.save()

                        if GENERAR_RUBROS_PAGO and GENERAR_RUBRO_INSCRIPCION:
                            if int(request.POST['coveniosolicitud']) == 1:
                                if 'referido' in request.POST:
                                    referido = ReferidosInscripcion.objects.get(pk=request.POST['referido'])
                                    referido.inscrito=True
                                    referido.inscripcionref = inscripcion
                                    referido.save()
                                    if pcg.precioinscripcion>0:
                                        valor = Decimal(pcg.precioinscripcion) - Decimal((pcg.precioinscripcion*DESCUENTO_REFERIDO)/100).quantize(Decimal(10)**-2)
                                else:
                                    if pcg.precioinscripcion>0:
                                        valor = pcg.precioinscripcion

                                if 'insasp' in request.POST:
                                    aspirante = InscripcionAspirantes.objects.get(pk=request.POST['insasp'])
                                    aspirante.inscrito=True
                                    aspirante.inscripcion=inscripcion
                                    aspirante.activo = False
                                    aspirante.save()

                                    if aspirante.vendedor:
                                        insc_vend = InscripcionVendedor(inscripcion=inscripcion,
                                                    fecha=datetime.now().date(),
                                                    vendedor=aspirante.vendedor)
                                        insc_vend.save()

                                hoy = datetime.today().date()
                                if valor>0:
                                    tienedescuento =False
                                    valdescuento=0
                                    if  inscripcion.promocion:
                                        if inscripcion.promocion.val_inscripcion > 0:
                                            tienedescuento =True
                                            valdescuento = (( valor * inscripcion.promocion.val_inscripcion)/100)
                                            valor =valor - valdescuento
                                            porcentajedescuento = inscripcion.promocion.val_inscripcion
                                            descripdeta ='PROMOCION '+ elimina_tildes(inscripcion.promocion.descripcion) + ' ' + str(inscripcion.promocion.val_inscripcion)

                                    if HABILITA_DESC_INSCRIPCION and not  tienedescuento:
                                        if not inscripcion.carrera.validacionprofesional:
                                                valdescuento = (( valor * DESCUENTO_INSCRIPCION)/100)
                                                valor =valor - valdescuento
                                                descripdeta = 'PROMOCION ' + str(DESCUENTO_INSCRIPCION) + ' DESCUENTO POR INSCRIPCION'
                                                porcentajedescuento = DESCUENTO_INSCRIPCION
                                    rubro = Rubro(fecha=hoy, valor=valor,
                                                    inscripcion=inscripcion, cancelado=False,
                                                    fechavence=hoy+timedelta(GENERAR_RUBRO_INSCRIPCION_MARGEN_DIAS))
                                    rubro.save()
                                    if valdescuento > 0:
                                        desc = Descuento(inscripcion = inscripcion,
                                                      motivo =descripdeta,
                                                      total = valdescuento,
                                                      fecha = datetime.now().date())
                                        desc.save()
                                        detalle = DetalleDescuento(descuento =desc,
                                                                    rubro =rubro,
                                                                    valor = valdescuento,
                                                                    porcentaje = porcentajedescuento)
                                        detalle.save()
                                    if rubro.valor == 0:
                                        rubro.cancelado=True
                                        rubro.save()
                                    ri = RubroInscripcion(rubro=rubro)
                                    ri.save()


                    if tienediscapacidad and EMAIL_ACTIVE:


                        if tienediscapacidad:
                            tipo_notificacion='DISCAPACIDAD'

                        # inscripcion.notificacion_dobe(request.user)
                        # inscripcion.notificacion_dobe(request.user,tipo_notificacion)
                        # OCU 04-sep-2017
                        asunto='Se ha inscrito una persona'
                        inscripcion.notificacion_dobe(request.user,tipo_notificacion, asunto)


                    # OCU 31-marzo-2016 realiza esto en el caso de inscripcion nueva
                    if not inscripcion.doblematricula:
                        documentos = DocumentosDeInscripcion(inscripcion=inscripcion,
                                                                     titulo=titulo,
                                                                     acta=actagrado,
                                                                     cedula=copiacedula,
                                                                     votacion=copiapapeletavota,
                                                                     fotos=foto,
                                                                     actafirmada=actafirmada)
                        documentos.save()

                    if existe==False:
                        g = Group.objects.get(pk=ALUMNOS_GROUP_ID)
                        g.user_set.add(user)
                        g.save()

                    if not InscripcionFichaSocioEconomicaBeca.objects.filter(inscripcion = inscripcion).exists():

                        inscripficha = InscripcionFichaSocioEconomicaBeca(
                                                inscripcion = inscripcion,
                                                edad = inscripcion.persona.edad_actual(),
                                                estadocivil_id = int(request.POST['estadocivil']),
                                                ciudad_id = int(request.POST['cantonresid']),
                                                direccion = request.POST['calleurba'],
                                                numero = request.POST['numero'],
                                                sector_id = int(request.POST['sector']),
                                                telefono = request.POST['teldomic'],
                                                celular = request.POST['celular'],
                                                emailpersona= request.POST['emailpersonal'],
                                                tipovivienda_id=int(request.POST['tipovivienda_id']),
                                                personacubregasto_id=int(request.POST['personacubregasto']),
                                                descripcubregasto=request.POST['descripcubregasto'],
                                                completo=True
                                                )

                        inscripficha.save()


                        listareferencia = json.loads(request.POST['listareferencia'])
                        if listareferencia!='':
                            for d in listareferencia:
                               referenciapersona= ReferenciaPersonal(fichabeca=inscripficha,
                                                   nombre=elimina_tildes(d['nombres']),
                                                   telefono=d['telefonoconvencional'],
                                                   celular=d['telefonocelular'],
                                                   parentesco_id=int(d['parentesco'])
                                                   )
                               referenciapersona.save()

                               referenciabeca=ReferenciaBeca(fichabeca=inscripficha,telefono=d['telefonoconvencional'],
                                                               parentesco_id=int(d['parentesco']))

                               referenciabeca.save()


                        listaresidentes = json.loads(request.POST['listaresidentes'])
                        if listaresidentes!='':
                            for m in listaresidentes:
                               datosresidentes= DatoResidente(fichabeca=inscripficha,
                                                   nombres=elimina_tildes(m['nombres']),
                                                   edad=m['edad'],
                                                   estadocivil_id=int(m['estadocivil']),
                                                   parentesco_id=int(m['parentesco']),
                                                   instruccion_id=int(m['instruccion']),
                                                   ocupacion_id=int(m['ocupacion']),
                                                   lugar=m['lugar']
                                                   )
                               datosresidentes.save()


                        listadatostrabajo = json.loads(request.POST['listadatostrabajo'])
                        if len(listadatostrabajo)>0:
                            for l in listadatostrabajo:

                              if l['fecha']!='None':
                                   datostrabajo= DatoTrabajo(fichabeca=inscripficha,
                                                       trabaja=l['trabaja'],
                                                       empresa=elimina_tildes(l['empresa']),
                                                       direccion=elimina_tildes(l['direccion']),
                                                       telefono=l['telefono'],
                                                       cargo=l['cargo'],
                                                       fecha=l['fecha'],
                                                       tiempolab=l['tiempolab'],
                                                       actual=l['actual'],
                                                       tipotrabajo_id=int(l['tipotrabajo'])
                                                       )
                              else:

                                  datostrabajo= DatoTrabajo(fichabeca=inscripficha,
                                                       trabaja=l['trabaja'],
                                                       empresa=elimina_tildes(l['empresa']),
                                                       direccion=elimina_tildes(l['direccion']),
                                                       telefono=l['telefono'],
                                                       cargo=l['cargo'],
                                                       tiempolab=l['tiempolab'],
                                                       actual=l['actual'],
                                                       tipotrabajo_id=int(l['tipotrabajo'])
                                                       )

                              datostrabajo.save()
                        else:

                            datostrabajo= DatoTrabajo(fichabeca=inscripficha,
                                                   trabaja=False,
                                                   actual=True
                                                   )
                            datostrabajo.save()


                        inquilinos=False
                        if request.POST['inquilino']=='true':
                           inquilinos=True

                        detallevivienda= Detallevivienda(fichabeca=inscripficha,inquilino=inquilinos,
                                                         numeroinqui=int(request.POST['numeroinqui']),valorarriendo=float(request.POST['valorarriendo']),
                                                         cedidadescrip=elimina_tildes(request.POST['cedidadescrip']),numerodormit=int(request.POST['numerodormit']))

                        detallevivienda.save()

                        if int(request.POST['parentesco'])>0:

                            enfermedadfamiliar= EnfermedadFamilia(fichabeca=inscripficha,problemsalud=request.POST['problemsalud'],parentesco_id=int(request.POST['parentesco']),descripcion=elimina_tildes(request.POST['descripcion']))
                        else:
                            enfermedadfamiliar= EnfermedadFamilia(fichabeca=inscripficha,problemsalud=False,descripcion=elimina_tildes(request.POST['descripcion']))

                        enfermedadfamiliar.save()




                        datosacademicos =DatosAcademicos(fichabeca=inscripficha,fiscal=request.POST['fiscal'],anio=int(request.POST['anio']),nota=request.POST['nota'])
                        datosacademicos.save()


                        listingresoegresopersonadata = json.loads(request.POST['listingresoegresopersonadata'])
                        if listingresoegresopersonadata!='':
                            for x in listingresoegresopersonadata:
                                if int(x['tipoingreso'])!=0 or int(x['tipoegreso'])!=0:
                                    if int(x['tipoingreso'])!=0:
                                        detalleingresoegreso=  DetalleIngrexEgres(fichabeca=inscripficha,tipoingreso_id=int(x['tipoingreso']),
                                                                                 valoringreso=float(x['valoringreso']),tipoegreso_id=int(x['tipoegreso']),valoregreso=float(x['valoregreso']) )


                                    else:

                                        detalleingresoegreso=  DetalleIngrexEgres(fichabeca=inscripficha,
                                                                                 valoringreso=float(x['valoringreso']),tipoegreso_id=int(x['tipoegreso']),valoregreso=float(x['valoregreso']) )


                                    detalleingresoegreso.save()

                        inscricpionfiechasocioecon=InscripcionFichaSocioeconomica(inscripcion=inscripcion,grupoeconomico_id=int(request.POST['gruposocioeconomico']))

                        inscricpionfiechasocioecon.save()

                    # matricular al estudiante
                    if not grupo.nivel_set.filter(nivelmalla__id=NIVEL_MALLA_UNO,cerrado=False
                                                   ).exists():
                        inscripcion.persona.usuario.delete()
                        return HttpResponse(json.dumps({"result": "bad", "error": str('No se encontro el nivel abierto para ese grupo')}),
                                           content_type="application/json")

                    nivel = grupo.nivel_set.filter(nivelmalla__id=NIVEL_MALLA_UNO,cerrado=False
                                                                           )[:1].get()

                    datoscarrera= json.loads(request.POST['informacioncarrera'])
                    inscripcion.matricularBecaMunicipio(nivel,
                                                    datoscarrera['montocubierto'],datoscarrera['numeroperiodo'],datoscarrera['valortotalcarrera'])

                    userrudy=User.objects.get(id=ID_USUARIO_RUDY)

                    if SolicitudBeca.objects.filter().exists():
                        idsoli= SolicitudBeca.objects.filter().order_by('-id')[:1].get().id +1
                    else:
                        idsoli=1

                    if int(request.POST['coveniosolicitud']) == 1:
                        motivo =str('BECA OTORGADA POR EL MUNICIPIO')
                        motivo_id=ID_MOTIVO_BECA_MUNICIPIO
                    else:
                        motivo =str('BECA OTORGADA POR EL GOBIERNO NACIONAL ')
                        motivo_id = ID_MOTIVO_BECA_TEC

                    # graudar la solicitud de beca
                    solicitudbeca = SolicitudBeca(id=idsoli,
                                    inscripcion = inscripcion,
                                    motivo = motivo,
                                    nivel = nivel,
                                    puntaje = 0,
                                    fecha = datetime.now(),
                                    estadoverificaciondoc=True)
                    solicitudbeca.save()


                    # Bucar todos los rubros de la inscripcion
                    lisrubro= Rubro.objects.filter(inscripcion=inscripcion,cancelado=False)
                    if int(request.POST['coveniosolicitud']) == 1:
                        des =float(100)
                    else:
                        des = datoscarrera['porcentajecubierto']

                    for rub in lisrubro:

                        if RubroCuota.objects.filter(rubro=rub).exists():
                            rubrocuota=RubroCuota.objects.get(rubro=rub)

                            tabadescuento=  TablaDescuentoBeca(solicitudbeca=solicitudbeca,inscripcion=solicitudbeca.inscripcion,
                                                          rubro=rub,valorubro=rub.valor,
                                                          descuento=des,fecha = datetime.now(),estado=True,
                                                          usuario=userrudy,cuota=rubrocuota.cuota,descripcion=rub.nombre())

                        elif RubroMatricula.objects.filter(rubro=rub).exists() :

                            tabadescuento=  TablaDescuentoBeca(solicitudbeca=solicitudbeca,inscripcion=solicitudbeca.inscripcion,
                                                          rubro=rub,valorubro=rub.valor,
                                                          descuento=des,fecha = datetime.now(),estado=True,
                                                          usuario=userrudy,cuota=0,descripcion=rub.nombre())

                        else:

                            tabadescuento=  TablaDescuentoBeca(solicitudbeca=solicitudbeca,inscripcion=solicitudbeca.inscripcion,
                                                          rubro=rub,valorubro=rub.valor,
                                                          descuento=des,fecha = datetime.now(),estado=True,
                                                          usuario=userrudy,cuota=0,descripcion=rub.nombre())


                        tabadescuento.save()


                    # llenar el log de historial de la solicitud beca
                    loshistorial= HistorialGestionBeca(solicitudbeca=solicitudbeca,inscripcion=solicitudbeca.inscripcion,
                                                                fecha=datetime.now(),estado=3, usuario=userrudy,comentariocorreo=motivo,
                                                                tipobeca_id=ID_TIPOBECA,motivobeca_id=motivo_id,
                                                                puntajerenovacion=Decimal('95').quantize(Decimal(10)**-2))

                    loshistorial.save()

                    resolucionbeca = Resolucionbeca(solicitudbeca=solicitudbeca,fecha=datetime.now())
                    resolucionbeca.save()
                    numerosolucion= 'ITB-BO-'+str(datetime.now().year)+'-00'+str(resolucionbeca.id)
                    resolucionbeca.numerosolucion=numerosolucion
                    resolucionbeca.save()


                    # llenar el log de historial de la solicitud beca
                    loshistorial= HistorialGestionBeca(solicitudbeca=solicitudbeca,inscripcion=solicitudbeca.inscripcion,
                                                                fecha=datetime.now(),estado=20, usuario=userrudy,comentariocorreo='APROBACION DE TABLA DE DESCUENTO DE BECA POR JEFE DOBE')
                    loshistorial.save()

                    solicitudbeca.asignaciontarficadescuento=True
                    solicitudbeca.save()

                    resolucionbeca = Resolucionbeca.objects.get(solicitudbeca=solicitudbeca)
                    resolucionbeca.fechaprobacion=datetime.now()
                    resolucionbeca.estado=True
                    resolucionbeca.save()

                      # llenar el log de historial de la solicitud beca por aprobacion del estudiante
                    loshistorial= HistorialGestionBeca(solicitudbeca=solicitudbeca,inscripcion=solicitudbeca.inscripcion,
                                                    fecha=datetime.now(),estado=18, usuario=inscripcion.persona.usuario,comentariocorreo=str('APROBACION DEL ESTUDIANTE AUTOMATICAMENTE POR BECA'))
                    loshistorial.save()



                    loshistorial= HistorialGestionBeca(solicitudbeca=solicitudbeca,inscripcion=solicitudbeca.inscripcion,
                                                                fecha=datetime.now(),estado=26, usuario=userrudy,
                                                                comentariocorreo=str('BECA APLICADA AUTOMATICAMENTE '))
                    loshistorial.save()

                    solicitudbeca.estadosolicitud=7
                    solicitudbeca.save()

                    solicitudbeca.aprobacionestudiante=True
                    solicitudbeca.asignaciontarficadescuento=True
                    solicitudbeca.envioanalisis=True
                    solicitudbeca.aprobado=True

                    solicitudbeca.save()


                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                    user_id         = userrudy.pk,
                    content_type_id = ContentType.objects.get_for_model(solicitudbeca).pk,
                    object_id       = solicitudbeca.id,
                    object_repr     = force_str(solicitudbeca),
                    action_flag     = ADDITION,
                    change_message  = 'Ingreso y Aplicacion de Solicitud de Beca desde sistema integral de beca                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  (' + client_address + ')' )




                    transaction.savepoint_commit(sid)

                    if EMAIL_ACTIVE and (
                            inscripcion.documentos_entregados().cedula or inscripcion.documentos_entregados().titulo or inscripcion.documentos_entregados().votacion or inscripcion.documentos_entregados().fotos or inscripcion.documentos_entregados().acta ):
                        inscripcion.correo_entregadocumentos(inscripcion.documentos_entregados(), userrudy)







                    resultado['result'] = "ok"
                    return HttpResponse(json.dumps(resultado),content_type="application/json")
                except Exception as ex:
                    if insecontrada==None:
                        user_inscrip = inscripcion.persona.usuario
                        user_inscrip.delete()
                    return HttpResponse(json.dumps({"result":"bad","error":str(ex)}), content_type="application/json")


    else:
        data = {'title': ''}
        if 'a' in request.GET:
            action = request.GET['a']


            if action=='verificarexistesga':
                try:

                    inscrip=None

                    if Inscripcion.objects.filter(persona__cedula=str(request.GET['cedula'])).exclude(persona__cedula=None).exclude(
                        persona__cedula='').exclude(carrera__id=66).exists():

                        inscrip= Inscripcion.objects.filter(persona__cedula=str(request.GET['cedula']))[:1].get()

                        if inscrip.persona.usuario.is_active:

                            return HttpResponse(json.dumps({'result': 'bad',
                                                        'message': 'Ya se encuentra Registro como Estudiante'}),
                                            content_type="application/json")

                    if Inscripcion.objects.filter(persona__pasaporte=str(request.GET['cedula'])).exclude(
                        persona__pasaporte=None).exclude(persona__pasaporte='').exclude(carrera__id=66).exists():

                        inscrip= Inscripcion.objects.filter(persona__cedula=str(request.GET['cedula']))[:1].get()

                        if inscrip.persona.usuario.is_active:

                            return HttpResponse(json.dumps({'result': 'bad',
                                                        'message': 'Ya se encuentra Registro como Estudiante'}),
                                            content_type="application/json")

                    if inscrip!=None:
                        if inscrip.persona.usuario.is_active:
                            if Matricula.objects.filter(inscripcion=inscrip,becado=True).exists():
                                return HttpResponse(json.dumps({'result': 'bad',
                                                            'message': 'No puede postularse porque ya tiene una beca con ITB'}),
                                                content_type="application/json")

                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")

                except Exception as ex:
                    return HttpResponse(json.dumps({"result":str(ex)}), content_type="application/json")


            elif action=='verificartienebeca':
                try:

                    inscrip=None

                    if Inscripcion.objects.filter(persona__cedula=str(request.GET['cedula'])).exclude(persona__cedula=None).exclude(
                        persona__cedula='').exclude(carrera__id=66).exists():
                        inscrip=Inscripcion.objects.filter(persona__cedula=str(request.GET['cedula'])).order_by('-id')[:1].get()

                    if Inscripcion.objects.filter(persona__pasaporte=str(request.GET['cedula'])).exclude(
                        persona__pasaporte=None).exclude(persona__pasaporte='').exclude(carrera__id=66).exists():

                        inscrip=Inscripcion.objects.filter(persona__pasaporte=str(request.GET['cedula'])).order_by('-id')[:1].get()

                    if inscrip!=None:
                        if inscrip.persona.usuario.is_active:
                            if Matricula.objects.filter(inscripcion=inscrip,becado=True).exists():
                                return HttpResponse(json.dumps({'result': 'bad',
                                                            'message': 'No puede postularse porque ya tiene una beca con ITB'}),
                                                content_type="application/json")

                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")

                except Exception as ex:
                    return HttpResponse(json.dumps({"result":'bad', 'message':str('Error de Consulta')}), content_type="application/json")


            elif action=='verusuario':
                try:
                    inscripcion = None
                    if Inscripcion.objects.filter(persona__cedula=str(request.GET['cedula'])).exclude(persona__cedula=None).exclude(
                        persona__cedula='').exists():

                        inscripcion= Inscripcion.objects.filter(persona__cedula=str(request.GET['cedula'])).order_by('-id').exclude(persona__cedula=None).exclude(
                        persona__cedula='')[:1].get()

                    if Inscripcion.objects.filter(persona__pasaporte=str(request.GET['cedula'])).exclude(
                        persona__pasaporte=None).exclude(persona__pasaporte='').exists():

                        inscripcion=Inscripcion.objects.filter(persona__pasaporte=str(request.GET['cedula'])).order_by('-id').exclude(
                        persona__pasaporte=None).exclude(persona__pasaporte='')[:1].get()

                    if  inscripcion== None:

                         return HttpResponse(json.dumps({'result': 'bad',
                                                    'message': 'No se encuentra registro'}),
                                        content_type="application/json")
                    else:

                        return HttpResponse(json.dumps({"result":"ok","usuario":inscripcion.persona.usuario.username,"correoinstitucional":inscripcion.persona.emailinst}),content_type="application/json")

                except Exception as ex:
                    return HttpResponse(json.dumps({"result":str(ex)}), content_type="application/json")


            elif action=='eliminarregistrosga':
                try:
                    inscripcion = None
                    if Inscripcion.objects.filter(persona__cedula=str(request.GET['cedula'])).exclude(persona__cedula=None).exclude(
                        persona__cedula='').exists():

                        inscripcion= Inscripcion.objects.filter(persona__cedula=str(request.GET['cedula'])).order_by('-id').exclude(persona__cedula=None).exclude(
                        persona__cedula='')[:1].get()

                    if Inscripcion.objects.filter(persona__pasaporte=str(request.GET['cedula'])).exclude(
                        persona__pasaporte=None).exclude(persona__pasaporte='').exists():

                        inscripcion=Inscripcion.objects.filter(persona__pasaporte=str(request.GET['cedula'])).order_by('-id').exclude(
                        persona__pasaporte=None).exclude(persona__pasaporte='')[:1].get()

                    if  inscripcion== None:

                         pass
                    else:

                        if Matricula.objects.filter(inscripcion = inscripcion).exists():

                            return HttpResponse(json.dumps({'result': 'bad',
                                                        'message': 'No se puede eliminar porque tiene matricula'}),
                                            content_type="application/json")

                        user_inscrip = inscripcion.persona.usuario.id
                        usuario= User.objects.get(pk=user_inscrip)
                        usuario.delete()

                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")

                except Exception as ex:
                    return HttpResponse(json.dumps({"result":str(ex)}), content_type="application/json")







def dias_entre_fecha(d1,d2):
    return abs(d2-d1).days
