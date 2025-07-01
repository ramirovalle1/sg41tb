from datetime import datetime
import json
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import render
from django.template import RequestContext

from med.models import PersonaEstadoCivil
from settings import ID_CARRRERA_NUEVA_BECA
from sga.models import TipoIdentificacion, SolicitudPostulacionBeca, viewTodaPersona, Canton, Pais, Provincia, Carrera, \
    elimina_tildes, Sexo, Parroquia, DatosAdicionalPostulacionBeca, DocumentosPostulacionBeca, Grupo, \
    HorariosCarreraPostulacion, EmpresaConvenio, CarreraConvenio, ConvenioCarrera, Modalidad, TipoAnuncio


def view(request):
    if request.method == 'POST':
        action = request.POST['action']

        if action == 'agregarsolicitud':
            try:
                data = {'title': ''}

                sid = transaction.savepoint()
                actualizado=False

                fecha = datetime.now().strftime("%Y-%m-%d")
                tienetitulotercernivel=False
                if request.POST['tienetitulotercernivel']=='true':
                    tienetitulotercernivel=True

                empresaconvenio = EmpresaConvenio.objects.get(id=39,activapostulacion=True)


                if SolicitudPostulacionBeca.objects.filter(identificacion=str(request.POST['identificacion']).upper(),empresaconvenio=empresaconvenio).exists():

                    return HttpResponse(
                        json.dumps({'result': 'bad', 'message': str("Ya se encuentra registrado en la postulación")}),
                        content_type="application/json")
                    # datasoli=SolicitudPostulacionBeca.objects.filter(identificacion=str(request.POST['identificacion']).upper(),empresaconvenio=empresaconvenio)[:1].get()
                    # actualizado=True
                    # datasoli.nombres=str(elimina_tildes(request.POST['nombres']).upper())
                    # datasoli.apellidos=str(elimina_tildes(request.POST['apellidos']).upper())
                    # datasoli.sexo_id=int(request.POST['sexo'])
                    # datasoli.estadocivil_id=int(request.POST['estadocivil'])
                    # datasoli.numerocasa=str(elimina_tildes(request.POST['numcasa']))
                    # datasoli.jornada=int(request.POST['idjornada'])
                    # datasoli.parroquia_id=int(request.POST['idparroquia'])
                    # datasoli.referencia=str(elimina_tildes(request.POST['referencia']))
                    # datasoli.calleprincipal=str(elimina_tildes(request.POST['calleprincipal']))
                    # datasoli.callesecundaria=str(elimina_tildes(request.POST['callesecundaria']))
                    # datasoli.email = str(request.POST['email']).lower()
                    # datasoli.provincia_id=int(request.POST['idprovincia'])
                    # datasoli.ciudad_id=int(request.POST['idciudad'])
                    # datasoli.telefono = request.POST['telefono']
                    # datasoli.celular = request.POST['celular']
                    # datasoli.carrera_id=int(request.POST['carrera'])
                    # datasoli.modalidad_id = int(request.POST['modalidad'])
                    # datasoli.fechanacimiento= request.POST['fechanacimiento']
                    # datasoli.anuncio_id = int(request.POST['medioenterastes'])


                else:
                    datasoli = SolicitudPostulacionBeca(tipoidentificacion_id=int(request.POST['tipoidenticacion']),
                    identificacion=request.POST['identificacion'],fecha=datetime.now(),
                    nombres=str(elimina_tildes(request.POST['nombres']).upper()),
                    apellidos=str(elimina_tildes(request.POST['apellidos']).upper()),
                    sexo_id=int(request.POST['sexo']),
                    estadocivil_id=int(request.POST['estadocivil']),
                    numerocasa=str(elimina_tildes(request.POST['numcasa'])),
                    parroquia_id=int(request.POST['idparroquia']),
                    referencia=str(elimina_tildes(request.POST['referencia'])),
                    calleprincipal=str(elimina_tildes(request.POST['calleprincipal'])),
                    callesecundaria=str(elimina_tildes(request.POST['callesecundaria'])),
                    email = str(request.POST['email']).lower(),
                    provincia_id=int(request.POST['idprovincia']),
                    ciudad_id=int(request.POST['idciudad']),
                    telefono = request.POST['telefono'],
                    carrera_id=int(request.POST['carrera']),
                    empresaconvenio=empresaconvenio,
                    modalidad_id=int(request.POST['modalidad']),
                    fechanacimiento= request.POST['fechanacimiento'],
                    celular = request.POST['celular'],
                    anuncio_id= int(request.POST['medioenterastes']),
                    titulotercernivel=tienetitulotercernivel)

                    datasoli.save()

                # guardar datos del resposable solidario
                # if not DatosAdicionalPostulacionBeca.objects.filter(solicitudpostulacion=datasoli,tipoadicion=1).exists():
                #     datosrespo=DatosAdicionalPostulacionBeca(fecha=fecha,tipoadicion=1,
                #                                              solicitudpostulacion=datasoli
                #     ,tipoidentificacion_id=int(request.POST['tipoidenresponsable']),
                #                                              identificacion=str(request.POST['identificacionresponsable']),
                #                                              sexo_id=int(request.POST['idsexoresponsable']),
                #                                              estadocivil_id=int(request.POST['idestadocivilresponsable']),
                #                                              nombres=str(elimina_tildes(request.POST['nombreresponsable']).upper()),
                #                                              apellidos=str(elimina_tildes(request.POST['apellidosresponsable'])).upper(),
                #                                              pais_id=1,provincia_id=int(request.POST['idprovinciaresponsable']),
                #                                              ciudad_id=int(request.POST['idciudadresponsable']),
                #                                              parroquia_id=int(request.POST['idparroquiaresponsable']),
                #                                              telefono=str(request.POST['telefonoresponsable']),
                #                                              celular=str(request.POST['celularesponsable']),
                #                                              email=str(request.POST['emailresponsable']).lower(),
                #                                              referencia=str(elimina_tildes(request.POST['referenciaresponsable'])).upper(),
                #                                              calleprincipal=str(elimina_tildes(request.POST['calleresponsable'])).upper(),
                #                                              callesecundaria=str(elimina_tildes(request.POST['callesecundariaresponsable'])).upper(),
                #                                              numerocasa=str(elimina_tildes(request.POST['numcasarepon']))
                #                                              )
                # else:
                #     datosrespo=DatosAdicionalPostulacionBeca.objects.filter(solicitudpostulacion=datasoli,tipoadicion=1)[:1].get()
                #     datosrespo.tipoidentificacion_id=int(request.POST['tipoidenresponsable'])
                #     datosrespo.identificacion=str(request.POST['identificacionresponsable'])
                #     datosrespo.sexo_id=int(request.POST['idsexoresponsable'])
                #     datosrespo.estadocivil_id=int(request.POST['idestadocivilresponsable'])
                #     datosrespo.nombres=str(request.POST['nombreresponsable']).upper()
                #     datosrespo.apellidos=str(request.POST['apellidosresponsable']).upper()
                #     datosrespo.provincia_id=int(request.POST['idprovinciaresponsable'])
                #     datosrespo.ciudad_id=int(request.POST['idciudadresponsable'])
                #     datosrespo.parroquia_id=int(request.POST['idparroquiaresponsable'])
                #     datosrespo.telefono=str(request.POST['telefonoresponsable'])
                #     datosrespo.celular=str(request.POST['celularesponsable'])
                #     datosrespo.email=str(request.POST['emailresponsable']).lower()
                #     datosrespo.referencia=str(elimina_tildes(request.POST['referenciaresponsable']).upper())
                #     datosrespo.calleprincipal=str(elimina_tildes(request.POST['calleresponsable']).upper())
                #     datosrespo.callesecundaria=str(elimina_tildes(request.POST['callesecundariaresponsable']).upper())
                #     datosrespo.numerocasa=str(elimina_tildes(request.POST['numcasarepon']))
                #
                # datosrespo.save()

                # guardar datos del conyuge responsable solidario
                # if datosrespo.estadocivil_id == 2:
                #     if not DatosAdicionalPostulacionBeca.objects.filter(solicitudpostulacion=datasoli,
                #                                                         tipoadicion=2,
                #                                                         pertenece=datosrespo.id).exists():
                #         datosconyugesoli = DatosAdicionalPostulacionBeca(fecha=fecha, tipoadicion=2,
                #                                                          solicitudpostulacion=datasoli
                #                                                          , tipoidentificacion_id=int(
                #                 request.POST['tipoidencoyugesoli']),
                #                                                          identificacion=str(
                #                                                              request.POST['identificacionconyugesoli']),
                #                                                          sexo_id=int(request.POST['idsexoconyugesoli']),
                #                                                          estadocivil_id=int(
                #                                                              request.POST['idestadocivilconyugesoli']),
                #                                                          nombres=str(elimina_tildes(
                #                                                              request.POST[
                #                                                                  'nombreconyugesoli']).upper()),
                #                                                          apellidos=str(elimina_tildes(
                #                                                              request.POST[
                #                                                                  'apellidosconyugesoli']).upper()),
                #                                                          pais_id=1,
                #                                                          provincia_id=int(
                #                                                              request.POST['idprovinciaconyugesoli']),
                #                                                          ciudad_id=int(
                #                                                              request.POST['idciudadconyugesoli']),
                #                                                          parroquia_id=int(
                #                                                              request.POST['idparroquiaconyugesoli']),
                #                                                          telefono=str(
                #                                                              request.POST['telefonoconyugesoli']),
                #                                                          celular=str(
                #                                                              request.POST['celularconyugesoli']),
                #                                                          email=str(
                #                                                              request.POST['emailconyugesoli']).lower(),
                #                                                          referencia=str(elimina_tildes(
                #                                                              request.POST[
                #                                                                  'referenciaconyugesoli']).upper()),
                #                                                          calleprincipal=str(elimina_tildes(
                #                                                              request.POST['calleconyugesoli']).upper()),
                #                                                          callesecundaria=str(elimina_tildes(
                #                                                              request.POST[
                #                                                                  'callesecundariaconyugesoli']).upper()),
                #                                                          pertenece=datosrespo.id,
                #                                                          numerocasa=str(elimina_tildes(
                #                                                              request.POST['numcasaconyugesoli']))
                #                                                          )
                #     else:
                #         datosconyugesoli = DatosAdicionalPostulacionBeca.objects.filter(solicitudpostulacion=datasoli,
                #                                                                         tipoadicion=2,
                #                                                                         pertenece=datosrespo.id)[
                #                            :1].get()
                #
                #         datosconyugesoli.tipoidentificacion_id = int(
                #             request.POST['tipoidencoyugesoli'])
                #         datosconyugesoli.identificacion = str(
                #             request.POST['identificacionconyugesoli'])
                #         datosconyugesoli.sexo_id = int(request.POST['idsexoconyugesoli'])
                #         datosconyugesoli.estadocivil_id = int(request.POST['idestadocivilconyugesoli'])
                #         datosconyugesoli.nombres = str(elimina_tildes(request.POST['nombreconyugesoli']).upper())
                #         datosconyugesoli.apellidos = str(elimina_tildes(request.POST['apellidosconyugesoli']).upper())
                #         datosconyugesoli.provincia_id = int(request.POST['idprovinciaconyugesoli'])
                #         datosconyugesoli.ciudad_id = int(request.POST['idciudadconyugesoli'])
                #         datosconyugesoli.parroquia_id = int(request.POST['idparroquiaconyugesoli'])
                #         datosconyugesoli.telefono = str(request.POST['telefonoconyugesoli'])
                #         datosconyugesoli.celular = str(request.POST['celularconyugesoli'])
                #         datosconyugesoli.email = str(request.POST['emailconyugesoli']).lower()
                #         datosconyugesoli.referencia = str(elimina_tildes(
                #             request.POST['referenciaconyugesoli']).upper())
                #         datosconyugesoli.calleprincipal = str(elimina_tildes(request.POST['calleconyugesoli']).upper())
                #         datosconyugesoli.callesecundaria = str(elimina_tildes(
                #             request.POST['callesecundariaconyugesoli']).upper())
                #         datosconyugesoli.numerocasa = str(elimina_tildes(
                #             request.POST['numcasaconyugesoli']))
                #
                #     datosconyugesoli.save()
                #
                # # guardar datos del conyuge becario
                # if datasoli.estadocivil_id == 2:
                #     if not DatosAdicionalPostulacionBeca.objects.filter(solicitudpostulacion=datasoli,
                #                                                         tipoadicion=3).exists():
                #         datosconyuge = DatosAdicionalPostulacionBeca(fecha=fecha, tipoadicion=3,solicitudpostulacion=datasoli
                #                                                    , tipoidentificacion_id=int(
                #                 request.POST['tipoidencoyuge']),
                #                                                    identificacion=str(
                #                                                        request.POST['identificacionconyuge']),
                #                                                    sexo_id=int(request.POST['idsexoconyuge']),
                #                                                    estadocivil_id=int(request.POST['idestadocivilconyuge']),
                #                                                    nombres=str(elimina_tildes(request.POST['nombreconyuge']).upper()),
                #                                                    apellidos=str(elimina_tildes(request.POST['apellidosconyuge']).upper()),
                #                                                    pais_id=1,
                #                                                    provincia_id=int(request.POST['idprovinciaconyuge']),
                #                                                    ciudad_id=int(request.POST['idciudadconyuge']),
                #                                                    parroquia_id=int(request.POST['idparroquiaconyuge']),
                #                                                    telefono=str(request.POST['telefonoconyuge']),
                #                                                    celular=str(request.POST['celularconyuge']),
                #                                                    email=str(request.POST['emailconyuge']).lower(),
                #                                                    referencia=str(elimina_tildes(
                #                                                        request.POST['referenciaconyuge']).upper()),
                #                                                    calleprincipal=str(elimina_tildes(request.POST['calleconyuge']).upper()),
                #                                                    callesecundaria=str(elimina_tildes(
                #                                                        request.POST['callesecundariaconyuge']).upper()),
                #                                                      numerocasa=str(elimina_tildes(request.POST['numcasaconyuge']))
                #                                                    )
                #     else:
                #         datosconyuge=DatosAdicionalPostulacionBeca.objects.filter(solicitudpostulacion=datasoli,
                #                                                      tipoadicion=3)[:1].get()
                #
                #         datosconyuge.tipoidentificacion_id = int(
                #             request.POST['tipoidencoyuge'])
                #         datosconyuge.identificacion = str(
                #             request.POST['identificacionconyuge'])
                #         datosconyuge.sexo_id = int(request.POST['idsexoconyuge'])
                #         datosconyuge.estadocivil_id = int(request.POST['idestadocivilconyuge'])
                #         datosconyuge.nombres = str(elimina_tildes(request.POST['nombreconyuge']).upper())
                #         datosconyuge.apellidos = str(elimina_tildes(request.POST['apellidosconyuge']).upper())
                #         datosconyuge.provincia_id = int(request.POST['idprovinciaconyuge'])
                #         datosconyuge.ciudad_id = int(request.POST['idciudadconyuge'])
                #         datosconyuge.parroquia_id = int(request.POST['idparroquiaconyuge'])
                #         datosconyuge.telefono = str(request.POST['telefonoconyuge'])
                #         datosconyuge.celular = str(request.POST['celularconyuge'])
                #         datosconyuge.email = str(request.POST['emailconyuge']).lower()
                #         datosconyuge.referencia = str(elimina_tildes(
                #             request.POST['referenciaconyuge']).upper())
                #         datosconyuge.calleprincipal = str(elimina_tildes(request.POST['calleconyuge']).upper())
                #         datosconyuge.callesecundaria = str(elimina_tildes(
                #             request.POST['callesecundariaconyuge']).upper())
                #         datosconyuge.numerocasa = str(elimina_tildes(request.POST['numcasaconyuge']))
                #
                #
                #
                #     datosconyuge.save()
                #
                #
                #
                #
                datasoli.actualizado=actualizado
                datasoli.save()



                if "filecedula" in request.FILES:
                    if not DocumentosPostulacionBeca.objects.filter(solicitudpostulacion=datasoli,pertenece=1).exists():
                        documentacioncedula = DocumentosPostulacionBeca(solicitudpostulacion=datasoli,pertenece=1,archivo=request.FILES["filecedula"],fecha=datetime.now())
                    else:
                        documentacioncedula =DocumentosPostulacionBeca.objects.filter(solicitudpostulacion=datasoli,pertenece=1)[:1].get()
                        documentacioncedula.archivo=request.FILES["filecedula"]

                    documentacioncedula.save()

                if "filecedulaconyuge" in request.FILES:
                    if not DocumentosPostulacionBeca.objects.filter(solicitudpostulacion=datasoli,
                                                                    pertenece=2).exists():
                        documentacioncedulaconyuge = DocumentosPostulacionBeca(solicitudpostulacion=datasoli, pertenece=2,
                                                                        archivo=request.FILES["filecedulaconyuge"],
                                                                        fecha=datetime.now())
                    else:
                        documentacioncedulaconyuge = DocumentosPostulacionBeca.objects.filter(solicitudpostulacion=datasoli,
                                                                                       pertenece=2)[:1].get()
                        documentacioncedulaconyuge.archivo = request.FILES["filecedulaconyuge"]

                    documentacioncedulaconyuge.save()

                if "filecedulasolidario" in request.FILES:
                    if not DocumentosPostulacionBeca.objects.filter(solicitudpostulacion=datasoli,
                                                                    pertenece=3).exists():
                        documentacioncedulasolidario = DocumentosPostulacionBeca(solicitudpostulacion=datasoli, pertenece=3,
                                                                        archivo=request.FILES["filecedulasolidario"],
                                                                        fecha=datetime.now())
                    else:
                        documentacioncedulasolidario = DocumentosPostulacionBeca.objects.filter(solicitudpostulacion=datasoli,
                                                                                       pertenece=3)[:1].get()
                        documentacioncedulasolidario.archivo = request.FILES["filecedulasolidario"]

                    documentacioncedulasolidario.save()

                if "filecedulasolidarioconyuge" in request.FILES:
                    if not DocumentosPostulacionBeca.objects.filter(solicitudpostulacion=datasoli,
                                                                    pertenece=4).exists():
                        documentacioncedulasolidarioconyu = DocumentosPostulacionBeca(solicitudpostulacion=datasoli, pertenece=4,
                                                                        archivo=request.FILES["filecedulasolidarioconyuge"],
                                                                        fecha=datetime.now())
                    else:
                        documentacioncedulasolidarioconyu = DocumentosPostulacionBeca.objects.filter(solicitudpostulacion=datasoli,
                                                                                       pertenece=4)[:1].get()
                        documentacioncedulasolidarioconyu.archivo = request.FILES["filecedulasolidarioconyuge"]

                    documentacioncedulasolidarioconyu.save()



                datasoli.mail_postulacion()



                transaction.savepoint_commit(sid)
                data['result'] = 'ok'
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}), content_type="application/json")

        if action == 'validaridentificacion':
            try:
                data = {'title': ''}
                data['exitesolicitud'] = 0
                empresaconvenio=EmpresaConvenio.objects.get(id=39,activapostulacion=True)

                if SolicitudPostulacionBeca.objects.filter(identificacion=str(request.POST['cedu']).strip(),empresaconvenio=empresaconvenio).exists():
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str("Ya se encuentra registrado en la postulación")}),
                                        content_type="application/json")
                    # data['exitesolicitud'] = 1
                    # datospersona = SolicitudPostulacionBeca.objects.filter(identificacion=str(request.POST['cedu']).strip(),empresaconvenio=empresaconvenio)[:1].get()
                    # apellidos = ""
                    # if datospersona.apellidos:
                    #     apellidos = datospersona.apellidos
                    # listJornada = []
                    # listJornada.append({"id": 0, "nombre": "Seleccionar el Jornada"})
                    # if HorariosCarreraPostulacion.objects.filter(carrera=datospersona.carrera.id).exists():
                    #     for g in HorariosCarreraPostulacion.objects.filter(carrera=datospersona.carrera.id).order_by("jornada"):
                    #         listJornada.append({"id": g.id, "nombre": str(g)})
                    #
                    # data['listJornada'] = listJornada
                    #
                    # listParroquia = []
                    # listParroquia.append({"id": 0, "nombre": "Seleccionar la parroquia"})
                    # if Parroquia.objects.filter(canton=datospersona.ciudad).exists():
                    #     for x in Parroquia.objects.filter(canton=datospersona.ciudad).order_by("nombre"):
                    #         listParroquia.append({"id": x.id, "nombre": str(x.nombre)})
                    #
                    # data['listParroquia'] = listParroquia
                    #
                    #
                    #
                    # data['datospersona'] = [{"cedula": datospersona.identificacion,
                    #                          "apellidos": apellidos,
                    #                          "nombres": datospersona.nombres,
                    #                          "email":str(datospersona.email).strip() if str(datospersona.email).strip() else 'SIN CORREO',
                    #                          "celular":datospersona.celular if datospersona.celular else '000000000',
                    #                          "telefono": datospersona.telefono if datospersona.telefono else '000000000',
                    #                          "idprovincia": datospersona.provincia_id if datospersona.provincia else '0',
                    #                          "idciudad": datospersona.ciudad_id if datospersona.ciudad else '0',
                    #                          "idcarrera":datospersona.carrera_id if datospersona.carrera else '0',
                    #                          "idsexo":datospersona.sexo_id if datospersona.sexo else '0',
                    #                          "idestadocivil": datospersona.estadocivil_id if datospersona.estadocivil else '0',
                    #                          "idparroquia":datospersona.parroquia_id if datospersona.parroquia else '0',
                    #                          "idjornada":datospersona.jornada if datospersona.jornada>0 else '0',
                    #                          "referencia": datospersona.referencia if datospersona.referencia else '',
                    #                          "calleprincipal":datospersona.calleprincipal if datospersona.calleprincipal else '',
                    #                          "callesecundaria": datospersona.callesecundaria if datospersona.callesecundaria else '',
                    #                          "numerocasa": datospersona.numerocasa if datospersona.numerocasa else '',
                    #                          "modalidad": datospersona.modalidad_id if datospersona.modalidad else '0',
                    #                          "fechanacimiento":str(datospersona.fechanacimiento)
                    #
                    #
                    #
                    #                          }]
                    #
                    #
                    #
                    # if DatosAdicionalPostulacionBeca.objects.filter(solicitudpostulacion=datospersona,tipoadicion=1).exists():
                    #
                    #     datosrep=DatosAdicionalPostulacionBeca.objects.filter(solicitudpostulacion=datospersona,tipoadicion=1)[:1].get()
                    #     data['tienedatosresolidario']=1
                    #     data['datosresolidario'] = [{"tipoidentificacion":datosrep.tipoidentificacion_id,"cedula": datosrep.identificacion,
                    #                              "apellidos": datosrep.apellidos,
                    #                              "nombres": datosrep.nombres,
                    #                              "email": str(datosrep.email).strip() if str(
                    #                                  datosrep.email).strip() else 'SIN CORREO',
                    #                              "celular": datosrep.celular if datosrep.celular else '000000000',
                    #                              "telefono": datosrep.telefono if datosrep.telefono else '000000000',
                    #                              "idprovincia": datosrep.provincia_id if datosrep.provincia else '0',
                    #                              "idciudad": datosrep.ciudad_id if datosrep.ciudad else '0',
                    #                              "idsexo": datosrep.sexo_id if datosrep.sexo else '0',
                    #                              "idestadocivil": datosrep.estadocivil_id if datosrep.estadocivil else '0',
                    #                              "idparroquia": datosrep.parroquia_id if datosrep.parroquia else '0',
                    #                              "refrencia": datosrep.referencia if datosrep.referencia else '',
                    #                              "calleprincipal": datosrep.calleprincipal if datosrep.calleprincipal else '',
                    #                              "callesecundaria": datosrep.callesecundaria if datosrep.callesecundaria else '',
                    #                              "numerocasa": datosrep.numerocasa if datosrep.numerocasa else ''
                    #
                    #                              }]
                    #
                    #     listParroquiaRespo = []
                    #     listParroquiaRespo.append({"id": 0, "nombre": "Seleccionar la parroquia"})
                    #     if Parroquia.objects.filter(canton= datosrep.ciudad_id).exists():
                    #         for x in Parroquia.objects.filter(canton= datosrep.ciudad_id).order_by("nombre"):
                    #             listParroquiaRespo.append({"id": x.id, "nombre": str(x.nombre)})
                    #
                    #     data['listParroquiaRespo'] = listParroquiaRespo
                    #
                    #
                    #     if datosrep.estadocivil_id==2 or datosrep.estadocivil_id==5:
                    #         if DatosAdicionalPostulacionBeca.objects.filter(solicitudpostulacion=datospersona,
                    #                                                         tipoadicion=2,pertenece=datosrep.id).exists():
                    #
                    #             datosConyubeSolidario = DatosAdicionalPostulacionBeca.objects.filter(
                    #                 solicitudpostulacion=datospersona, tipoadicion=2,pertenece=datosrep.id)[:1].get()
                    #             data['tienedatosconyugesolidario'] = 1
                    #             data['datosconyugesolidario'] = [{"tipoidentificacion": datosConyubeSolidario.tipoidentificacion_id,
                    #                                              "cedula": datosConyubeSolidario.identificacion,
                    #                                              "apellidos": datosConyubeSolidario.apellidos,
                    #                                              "nombres": datosConyubeSolidario.nombres,
                    #                                              "email": str(datosConyubeSolidario.email).strip() if str(
                    #                                                  datosConyubeSolidario.email).strip() else 'SIN CORREO',
                    #                                              "celular": datosConyubeSolidario.celular if datosConyubeSolidario.celular else '000000000',
                    #                                              "telefono": datosConyubeSolidario.telefono if datosConyubeSolidario.telefono else '000000000',
                    #                                              "idprovincia": datosConyubeSolidario.provincia_id if datosConyubeSolidario.provincia else '0',
                    #                                              "idciudad": datosConyubeSolidario.ciudad_id if datosConyubeSolidario.ciudad else '0',
                    #                                              "idsexo": datosConyubeSolidario.sexo_id if datosConyubeSolidario.sexo else '0',
                    #                                              "idestadocivil": datosConyubeSolidario.estadocivil_id if datosConyubeSolidario.estadocivil else '0',
                    #                                              "idparroquia": datosConyubeSolidario.parroquia_id if datosConyubeSolidario.parroquia else '0',
                    #                                              "refrencia": datosConyubeSolidario.referencia if datosConyubeSolidario.referencia else '',
                    #                                              "calleprincipal": datosConyubeSolidario.calleprincipal if datosConyubeSolidario.calleprincipal else '',
                    #                                              "callesecundaria": datosConyubeSolidario.callesecundaria if datosConyubeSolidario.callesecundaria else '',
                    #                                              "numerocasa": datosConyubeSolidario.numerocasa if datosConyubeSolidario.numerocasa else ''
                    #
                    #                                              }]
                    #
                    #             listParroquiaConyugeSolidario = []
                    #             listParroquiaConyugeSolidario.append({"id": 0, "nombre": "Seleccionar la parroquia"})
                    #             if Parroquia.objects.filter(canton=datosConyubeSolidario.ciudad_id).exists():
                    #                 for x in Parroquia.objects.filter(canton=datosConyubeSolidario.ciudad_id).order_by("nombre"):
                    #                     listParroquiaConyugeSolidario.append({"id": x.id, "nombre": str(x.nombre)})
                    #
                    #             data['listParroquiaConyugeSolidario'] = listParroquiaConyugeSolidario
                    #
                    #         else:
                    #             data['tienedatosconyugesolidario'] = 0
                    #
                    # else:
                    #     data['tienedatosresolidario'] = 0
                    #
                    #
                    #
                    # if DatosAdicionalPostulacionBeca.objects.filter(solicitudpostulacion=datospersona,tipoadicion=3).exists():
                    #
                    #     datosConyube=DatosAdicionalPostulacionBeca.objects.filter(solicitudpostulacion=datospersona,tipoadicion=3)[:1].get()
                    #     data['tienedatosconyugebecario']=1
                    #     data['datosconyugebecarrio'] = [{"tipoidentificacion":datosConyube.tipoidentificacion_id,"cedula": datosConyube.identificacion,
                    #                              "apellidos": datosConyube.apellidos,
                    #                              "nombres": datosConyube.nombres,
                    #                              "email": str(datosConyube.email).strip() if str(
                    #                                  datosConyube.email).strip() else 'SIN CORREO',
                    #                              "celular": datosConyube.celular if datosConyube.celular else '000000000',
                    #                              "telefono": datosConyube.telefono if datosConyube.telefono else '000000000',
                    #                              "idprovincia": datosConyube.provincia_id if datosConyube.provincia else '0',
                    #                              "idciudad": datosConyube.ciudad_id if datosConyube.ciudad else '0',
                    #                              "idsexo": datosConyube.sexo_id if datosConyube.sexo else '0',
                    #                              "idestadocivil": datosConyube.estadocivil_id if datosConyube.estadocivil else '0',
                    #                              "idparroquia": datosConyube.parroquia_id if datosConyube.parroquia else '0',
                    #                              "refrencia": datosConyube.referencia if datosConyube.referencia else '',
                    #                              "calleprincipal": datosConyube.calleprincipal if datosConyube.calleprincipal else '',
                    #                              "callesecundaria": datosConyube.callesecundaria if datosConyube.callesecundaria else '',
                    #                              "numerocasa": datosConyube.numerocasa if datosConyube.numerocasa else ''
                    #
                    #                              }]
                    #
                    #     listParroquiaConyuge = []
                    #     listParroquiaConyuge.append({"id": 0, "nombre": "Seleccionar la parroquia"})
                    #     if Parroquia.objects.filter(canton= datosConyube.ciudad_id).exists():
                    #         for x in Parroquia.objects.filter(canton= datosConyube.ciudad_id).order_by("nombre"):
                    #             listParroquiaConyuge.append({"id": x.id, "nombre": str(x.nombre)})
                    #
                    #     data['listParroquiaConyugeBecario'] = listParroquiaConyuge
                    #
                    #
                    # else:
                    #     data['tienedatosconyugebecario'] = 0

                data['result'] = 'ok'

                return HttpResponse(json.dumps(data), content_type="application/json")

            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}), content_type="application/json")


        if action == 'buscarcantones':
            try:
                data = {'title': ''}
                listCan= []

                if Canton.objects.filter(provincia__id=int(request.POST['idprovincia']),pk=int(request.POST['idcanton'])).order_by("nombre").exists():
                    for g in Canton.objects.filter(provincia__id=int(request.POST['idprovincia']),pk=int(request.POST['idcanton'])).order_by("nombre"):
                        listCan.append({"id": g.id, "nombre": g.nombre})
                else:
                    listCan.append({"id": 0, "nombre": "Sin Canton"})
                data['listacanton'] = listCan
                data['result'] = 'ok'
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}), content_type="application/json")

        elif action == 'buscarcantonesotro':
            try:
                data = {'title': ''}
                listCan = []
                listCan.append({"id": 0, "nombre": "Seleccionar el Canton"})
                if Canton.objects.filter(provincia__id=int(request.POST['idprovincia'])).order_by("nombre").exists():
                    for g in Canton.objects.filter(provincia__id=int(request.POST['idprovincia'])).order_by("nombre"):
                        listCan.append({"id": g.id, "nombre": g.nombre})
                data['listacanton'] = listCan
                data['result'] = 'ok'
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}), content_type="application/json")

        elif action == 'buscarparroquias':
            try:
                data = {'title': ''}
                lisParro = []
                lisParro.append({"id": 0, "nombre": "Seleccionar la parroquia"})
                if Parroquia.objects.filter(canton__id=int(request.POST['idcanton'])).exists():
                    for a in Parroquia.objects.filter(canton__id=int(request.POST['idcanton'])).order_by("nombre"):
                        lisParro.append({"id": a.id, "nombre": a.nombre})



                data['listaparroquia'] = lisParro


                data['result'] = 'ok'
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}), content_type="application/json")


        elif action == 'buscarcarreramodalidad':
            try:
                data = {'title': ''}
                listacarrera = []
                listacarrera.append({"id": 0, "nombre": "Seleccionar la carrera"})
                if ConvenioCarrera.objects.filter(empresaconvenio__id=39,modalidad__id=int(request.POST['idmodalidad'])).exists():
                    for a in ConvenioCarrera.objects.filter(empresaconvenio__id=39,modalidad__id=int(request.POST['idmodalidad'])).order_by("carrera__nombre"):
                        listacarrera.append({"id": a.carrera.id, "nombre": a.carrera.nombre})



                data['listcarrera'] = listacarrera


                data['result'] = 'ok'
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}), content_type="application/json")



    else:
        data = {'title': 'Solicitudes de Postulacion Beca'}
        empresaconvenio = EmpresaConvenio.objects.filter(activapostulacion=True).first()
        data['listtipoidentificacion'] = TipoIdentificacion.objects.filter(estado=True).order_by("id")
        data['liscarrera'] = ConvenioCarrera.objects.filter(empresaconvenio=empresaconvenio,activo=True)
        data['listpais'] = Pais.objects.filter(pk=1)
        # data['lisprovincia'] = Provincia.objects.filter(id__in=[1,2,10,11,6])
        data['lisprovincia'] = Provincia.objects.filter()
        data['listsexo'] = Sexo.objects.filter()
        data['listsexobecario'] = Sexo.objects.filter(id=1)
        data['listmodalidad'] = Modalidad.objects.filter(id__in=[1,4])
        data['listaestadocivil'] = PersonaEstadoCivil.objects.filter().exclude(pk=6)
        data['listamedio'] =  TipoAnuncio.objects.filter(id__in=[25,13,27,28,29,30,31,32,33,34],activo=True).order_by("descripcion")

        return render(request,"solicitudpostulacionbeca/solicitudpostulacionbecabs.html", data)
