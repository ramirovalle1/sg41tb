from datetime import datetime
import json
from django.contrib.admin.models import LogEntry, ADDITION, DELETION, CHANGE
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import RequestContext
import xlwt
from decorators import secure_module
from settings import FINANCIERO_GROUP_ID, MEDIA_ROOT, EMAIL_ACTIVE, INCIDENCIA_CAB, PROFESORES_GROUP_ID, ALUMNOS_GROUP_ID, SITE_ROOT, STATIC_ROOT
from sga.commonviews import addUserData, ip_client_address
from sga.models import Inscripcion, Pais, Provincia, Canton, Parroquia, InscripcionesCAB, InfoEconInscripcionesCAB, ReferenciaInscripcionesCAB, BeneficiarioInscripcionesCAB, Persona, Rubro, PagoNivel, CuotaCAB, RubroCuota, RubroMatricula, DesafiliacionCAB, TituloInstitucion, TipoIncidencia, GaranteCAB, InfoEconGaranteCAB, ModuloGrupo, Modulo, Profesor
from sga.reportes import elimina_tildes
from sga.tasks import send_html_mail


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
@secure_module
@transaction.atomic()

def view(request):
    if request.method=='POST':
        action = request.POST['action']

        if action == 'consulta_canton':
            result =  {}
            try:
                result  = {"canton": [{"id": x.id, "nombre": x.nombre } for x in Canton.objects.filter(provincia__id=request.POST['id']).order_by('nombre')]}
                result['result']  = 'ok'
                return HttpResponse(json.dumps(result), content_type="application/json")
            except Exception as e:
                print(e)
                result['result']  = 'bad'
                return HttpResponse(json.dumps(result), content_type="application/json")

        elif action =='consulta_parroquia':
            result =  {}
            try:
                result  = {"parroquia": [{"id": x.id, "nombre": x.nombre } for x in Parroquia.objects.filter(canton__id=request.POST['id']).order_by('nombre')]}
                result['result']  = 'ok'
                return HttpResponse(json.dumps(result), content_type="application/json")
            except Exception as e:
                    result['result']  = 'bad'
                    return HttpResponse(json.dumps(result), content_type="application/json")

        elif action == 'add_form':
            result = {}
            try:
                persona = Persona.objects.get(pk=request.POST['persona'])
                print(persona.id)
                inscripcion = None
                if Inscripcion.objects.filter(pk=request.POST['inscripcion']).exists():
                    inscripcion = Inscripcion.objects.get(pk=request.POST['inscripcion'])
                cargo = False
                if request.POST['cargo_politico']=='1':
                    cargo = True
                # if InscripcionesCAB.objects.filter(Q(inscripcion=inscripcion, estado=True)|Q(persona=persona, estado=True)).exclude(inscripcion=None).exists():
                if (inscripcion and InscripcionesCAB.objects.filter(inscripcion=inscripcion, estado=True).exclude(inscripcion=None).exists()) or (InscripcionesCAB.objects.filter(persona=persona, estado=True).exists()):
                    result['result']  = 'existe'
                else:
                    cab = InscripcionesCAB(ciudad = Canton.objects.get(pk=100),
                                           fecha=datetime.date(datetime.now()),
                                           estado_civil=request.POST['estado_civil'],
                                           num_cargasfam = int(request.POST['num_cargas']),
                                           pais_resid = Pais.objects.get(pk=request.POST['paisresidencia']),
                                           provincia_resid = Provincia.objects.get(pk=request.POST['provinciaresidencia']),
                                           canton_resid = Canton.objects.get(pk=request.POST['cantonresidencia']),
                                           parroquia_resid = Parroquia.objects.get(pk=request.POST['parroquiaresidencia']),
                                           email=request.POST['email'],
                                           domicilio=request.POST['domicilio'],
                                           convencional=request.POST['convencional'],
                                           celular=request.POST['celular'],
                                           actecon_tipo=request.POST['tipotrabajo'],
                                           actecon_empresa=request.POST['nombreempresa'],
                                           actecon_empresaactividad=request.POST['actividadeconomicaempresa'],
                                           actecon_direccion=request.POST['direcciontrabajo'],
                                           actecon_telefono=request.POST['numerotrabajo'],
                                           actecon_cargopolitico=cargo,
                                           proposito=request.POST['proposito'],
                                           origen=request.POST['origen'],
                                           monto=request.POST['monto'])
                    cab.save()

                    if inscripcion:
                        cab.inscripcion = inscripcion
                    else:
                        cab.persona = persona
                    cab.save()

                    if request.POST['estado_civil'] == 'CASADO':
                        cab.apellidos_conyuge = request.POST['apellidosconyuge']
                        cab.nombres_conyuge = request.POST['nombreconyuge']
                        cab.tipo_identificacion_conyuge = request.POST['tipoidentificacionconyuge']
                        cab.num_identificacion_conyuge = request.POST['identificacionconyuge']
                        cab.pais_conyuge = Pais.objects.get(pk=request.POST['paisconyuge'])
                        cab.save()

                    for i in json.loads(request.POST['info_economica']):
                        info_econ = InfoEconInscripcionesCAB(inscripcioncab = cab,
                                                             tipo = i['tipo'],
                                                             descripcion = i['descipcion'],
                                                             valor = float(i['valor']))
                        info_econ.save()

                    for r in json.loads(request.POST['referencias']):
                        referencia = ReferenciaInscripcionesCAB(inscripcioncab = cab,
                                                              nombre = r['nombre'],
                                                              relacion = r['relacion'],
                                                              telefono = r['telefono'],
                                                              ciudad = Canton.objects.get(pk=r['ciudad']))
                        referencia.save()

                    for b in json.loads(request.POST['beneficiarios']):
                        beneficiario = BeneficiarioInscripcionesCAB(inscripcioncab = cab,
                                                              apellidos = b['apellidos'],
                                                              nombres = b['nombres'],
                                                              porcentaje = b['porcentaje'],
                                                              telefono = b['telefono'],
                                                              tipo_identificacion = b['tipo_identificacion'],
                                                              numero_identificacion = b['num_identificacion'],
                                                              parentesto = b['parentesco'])
                        beneficiario.save()
                    inscripcion.cab = True
                    inscripcion.save()

                    # pagos = PagoNivel.objects.filter(nivel=inscripcion.matricula().nivel).order_by('fecha')
                    if inscripcion:
                        rubrocuota = RubroCuota.objects.filter(matricula=inscripcion.matricula())
                        rubromatricula = RubroMatricula.objects.filter(matricula=inscripcion.matricula())
                        if (Rubro.objects.filter(id__in=rubrocuota.values('rubro'), fechavence__gte=datetime.now())|Rubro.objects.filter(id__in=rubromatricula.values('rubro'), fechavence__gte=datetime.now())).exists():
                            rubros = Rubro.objects.filter(id__in=rubromatricula.values('rubro'), fechavence__gte=datetime.now()).order_by('fechavence')|Rubro.objects.filter(id__in=rubrocuota.values('rubro'), fechavence__gte=datetime.now()).order_by('fechavence')
                            sec=1
                            for r in rubros:
                                cuota_cab = CuotaCAB(descripcion='CUOTA CAB #'+str(sec),
                                                     rubro=r,
                                                     inscripcioncab=cab,
                                                     fechavence=r.fechavence,
                                                     valor=float(request.POST['monto']),
                                                     nivel=inscripcion.matricula().nivel)
                                cuota_cab.save()
                                sec = sec + 1

                    if EMAIL_ACTIVE:
                        tipo = TipoIncidencia.objects.get(pk=INCIDENCIA_CAB)
                        hoy = datetime.now().today()
                        contenido = 'AFILIACION INSCRIPCION CAB'
                        send_html_mail(contenido, "emails/cab_afiliacion.html", {'fecha':hoy, 'contenido':contenido, 'usuario':request.user, 'cab': cab}, tipo.correo.split(","))


                    result['result']  = 'ok'
                return HttpResponse(json.dumps(result), content_type="application/json")
            except Exception as ex:
                print(ex)
                result['result']  = str(ex)
                return HttpResponse(json.dumps(result), content_type="application/json")

        elif action == 'cambiar_estado':
            result =  {}
            try:
                inscripcion_cab = InscripcionesCAB.objects.get(pk=request.POST['id'])
                inscripcion_cab.en_cab = True
                inscripcion_cab.save()
                try:
                    identificacion = inscripcion_cab.inscripcion.persona.cedula
                except:
                    identificacion = inscripcion_cab.inscripcion.persona.pasaporte
                result['result']  = 'ok'
                result['identificacion']  = identificacion
                return HttpResponse(json.dumps(result), content_type="application/json")
            except Exception as e:
                print(e)
                result['result']  = 'bad'
                return HttpResponse(json.dumps(result), content_type="application/json")

        elif action == 'enviar_solicitud_desafiliacion':
            result =  {}
            try:
                inscripcion_cab = InscripcionesCAB.objects.get(pk=request.POST['cab_id'])
                if DesafiliacionCAB.objects.filter(inscripcioncab=inscripcion_cab, inscripcioncab__estado=True).exists():
                    desafiliacion = DesafiliacionCAB.objects.filter(inscripcioncab=inscripcion_cab, inscripcioncab__estado=True).order_by('-id')[:1].get()
                    desafiliacion.motivo = request.POST['motivo']
                    desafiliacion.fecha = datetime.date(datetime.now())
                    desafiliacion.solicitud = request.POST['ruta']
                    desafiliacion.solicitud_enviada = True
                    desafiliacion.save()
                else:
                    desafiliacion = DesafiliacionCAB(inscripcioncab=inscripcion_cab,
                                                     motivo=request.POST['motivo'],
                                                     fecha=datetime.date(datetime.now()),
                                                     solicitud=request.POST['ruta'],
                                                     solicitud_enviada=True)
                    desafiliacion.save()

                if EMAIL_ACTIVE:
                    tipo = TipoIncidencia.objects.get(pk=INCIDENCIA_CAB)
                    hoy = datetime.now().today()
                    contenido = 'DESAFILIACION INSCRIPCION CAB'
                    send_html_mail(contenido, "emails/cab_desafiliacion.html", {'fecha':hoy, 'contenido':contenido, 'usuario':request.user, 'desafiliacion': desafiliacion}, tipo.correo.split(","))

                result['result']  = 'ok'
                return HttpResponse(json.dumps(result), content_type="application/json")
            except Exception as e:
                print(e)
                result['result']  = 'bad'
                return HttpResponse(json.dumps(result), content_type="application/json")

        elif action == 'rechazar_desafiliacion':
            result =  {}
            try:
                desafiliacion = DesafiliacionCAB.objects.get(pk=request.POST['id'])
                desafiliacion.solicitud_rechazada = True
                desafiliacion.motivo_rechazo = request.POST['motivo']
                desafiliacion.fecha_aceptacionrechazo = datetime.date(datetime.now())
                desafiliacion.save()

                result['result']  = 'ok'
                return HttpResponse(json.dumps(result), content_type="application/json")
            except Exception as e:
                print(e)
                result['result']  = 'bad'
                return HttpResponse(json.dumps(result), content_type="application/json")

        elif action == 'aprobar_desafiliacion':
            result =  {}
            try:
                desafiliacion = DesafiliacionCAB.objects.get(pk=request.POST['id'])
                desafiliacion.solicitud_aceptada = True
                desafiliacion.fecha_aceptacionrechazo = datetime.date(datetime.now())
                desafiliacion.save()

                inscripcion_cab = InscripcionesCAB.objects.filter(pk=desafiliacion.inscripcioncab.id)[:1].get()
                inscripcion_cab.estado = False
                inscripcion_cab.save()
                inscripcion_cab.inscripcion.cab = False
                inscripcion_cab.inscripcion.save()

                if CuotaCAB.objects.filter(inscripcioncab=inscripcion_cab, cancelado=False).exists():
                    cuotas = CuotaCAB.objects.filter(inscripcioncab=inscripcion_cab, cancelado=False)
                    for c in cuotas:
                        c.delete()

                result['result']  = 'ok'
                return HttpResponse(json.dumps(result), content_type="application/json")
            except Exception as e:
                print(e)
                result['result']  = 'bad'
                return HttpResponse(json.dumps(result), content_type="application/json")

        elif action == 'cajeros_cuotas':
            print(request.POST)
            result =  {}
            try:
                contador = 0
                total = 0
                titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                titulo.font.height = 20*11
                titulo2.font.height = 20*11
                subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                subtitulo.font.height = 20*10
                wb = xlwt.Workbook()
                ws = wb.add_sheet('LISTA',cell_overwrite_ok=True)

                tit = TituloInstitucion.objects.all()[:1].get()
                ws.write_merge(0, 0,0,5, tit.nombre , titulo2)
                ws.write_merge(1, 1,0,5, 'LISTADO DE VALORES EN CAB', titulo2)
                ws.write(3, 0,'FECHA', titulo)
                ws.write(3, 1, request.POST['fecha'], titulo)

                ws.write(5, 0,'NOMBRE ALUMNO', titulo)
                ws.write(5, 1,'CEDULA', titulo)
                ws.write(5, 2,'CARRERA', titulo)
                ws.write(5, 3,'VALOR', titulo)
                ws.write(5, 4,'BENEFICIO', titulo)
                ws.write(5, 5,'FECHA', titulo)
                ws.write(5, 6,'RUBRO ASOCIADO', titulo)

                fila = 6
                for c in json.loads(request.POST['lista']):
                    if not CuotaCAB.objects.get(pk=c['id']).encab:
                        cuota_cab = CuotaCAB.objects.get(pk=c['id'])
                        cuota_cab.encab = True
                        cuota_cab.fechaencab = datetime.now().date()
                        cuota_cab.save()
                        contador = contador+1
                        total = float(total) + float(cuota_cab.valor_benef) + float(cuota_cab.valor)

                        ws.write(fila, 0, elimina_tildes(cuota_cab.inscripcioncab.inscripcion.persona.nombre_completo_inverso()))
                        if cuota_cab.inscripcioncab.inscripcion.persona.cedula:
                            identificacion = cuota_cab.inscripcioncab.inscripcion.persona.cedula
                        else:
                            identificacion = cuota_cab.inscripcioncab.inscripcion.persona.pasaporte
                        ws.write(fila, 1, identificacion)
                        ws.write(fila, 2, elimina_tildes(cuota_cab.inscripcioncab.inscripcion.carrera.nombre))
                        ws.write(fila, 3, cuota_cab.valor)
                        ws.write(fila, 4, cuota_cab.valor_benef)
                        ws.write(fila, 5, str(cuota_cab.fecha_benef))
                        ws.write(fila, 6, cuota_cab.rubro.nombre())
                        fila = fila+1

                ws.write(fila, 2, 'TOTAL', subtitulo)
                ws.write_merge(fila, fila,3,4, total, subtitulo)

                fila = fila+3
                ws.write(fila, 0, "Fecha Impresion", subtitulo)
                ws.write(fila, 2, str(datetime.now()), subtitulo)
                ws.write(fila+1, 0, "Usuario", subtitulo)
                ws.write(fila+1, 2, str(request.user), subtitulo)

                nombre ='Listado'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                # return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                result['result']  = 'ok'
                result['total']  = contador
                result['valor_total']  = total
                result['url']  =  "/media/reporteexcel/"+nombre
                return HttpResponse(json.dumps(result), content_type="application/json")
            except Exception as e:
                print(e)
                result['result']  = 'bad'
                return HttpResponse(json.dumps(result), content_type="application/json")

        elif action == 'add_garante':
            result = {}
            try:
                print(request.POST)
                inscripcion_cab = InscripcionesCAB.objects.get(pk=request.POST['inscripcion_cab'])
                fecha_nacimiento = datetime.strptime(str(request.POST['fechanacimiento']),'%d-%m-%Y').date()
                cargo = False
                if request.POST['cargo_politico']=='1':
                    cargo = True
                else:
                    garante = GaranteCAB(inscripcioncab=inscripcion_cab,
                                       fecha=datetime.date(datetime.now()),
                                       apellidos=request.POST['apellidos'],
                                       nombre=request.POST['nombre'],
                                       tipo_identificacion=request.POST['tipoidentificacion'],
                                       num_identificacion=request.POST['identificacion'],
                                       pais=Pais.objects.get(pk=request.POST['nacionalidad']),
                                       canton=Canton.objects.get(pk=request.POST['ciudadnacimiento']),
                                       fecha_nacimiento=fecha_nacimiento,

                                       estado_civil=request.POST['estado_civil'],
                                       num_cargasfam = int(request.POST['num_cargas']),
                                       pais_resid = Pais.objects.get(pk=request.POST['paisresidencia']),
                                       provincia_resid = Provincia.objects.get(pk=request.POST['provinciaresidencia']),
                                       canton_resid = Canton.objects.get(pk=request.POST['cantonresidencia']),
                                       parroquia_resid = Parroquia.objects.get(pk=request.POST['parroquiaresidencia']),
                                       email=request.POST['email'],
                                       domicilio=request.POST['domicilio'],
                                       convencional=request.POST['convencional'],
                                       celular=request.POST['celular'],
                                       actecon_tipo=request.POST['tipotrabajo'],
                                       actecon_empresa=request.POST['nombreempresa'],
                                       actecon_empresaactividad=request.POST['actividadeconomicaempresa'],
                                       actecon_direccion=request.POST['direcciontrabajo'],
                                       actecon_telefono=request.POST['numerotrabajo'],
                                       actecon_cargopolitico=cargo)
                    garante.save()

                    for i in json.loads(request.POST['info_economica']):
                        info_econ = InfoEconGaranteCAB(garante = garante,
                                                             tipo = i['tipo'],
                                                             descripcion = i['descipcion'],
                                                             valor = float(i['valor']))
                        info_econ.save()

                    # if EMAIL_ACTIVE:
                    #     tipo = TipoIncidencia.objects.get(pk=INCIDENCIA_CAB)
                    #     hoy = datetime.now().today()
                    #     contenido = 'ADICION DE GARANTE'
                    #     send_html_mail(contenido, "emails/cab_afiliacion.html", {'fecha':hoy, 'contenido':contenido, 'usuario':request.user, 'garante': garante}, tipo.correo.split(","))


                    result['result']  = 'ok'
                return HttpResponse(json.dumps(result), content_type="application/json")
            except Exception as ex:
                print(ex)
                result['result']  = str(ex)
                return HttpResponse(json.dumps(result), content_type="application/json")

        elif action == 'change_monto':
            print(request.POST)
            cab = InscripcionesCAB.objects.get(pk=request.POST['id'])
            cab.monto = request.POST['monto']
            cab.save()
            tipopersonal = 'Administrativo'
            if Profesor.objects.filter(persona=cab.persona).exists():
                tipopersonal = 'Docente'
            if EMAIL_ACTIVE:
                tipo = TipoIncidencia.objects.get(pk=INCIDENCIA_CAB)
                hoy = datetime.now().today()
                contenido = 'CAMBIO MONTO DE APORTACION ADMINISTRATIVO/DOCENTE'
                send_html_mail(contenido, "emails/change_monto_cab.html", {'fecha':hoy, 'contenido':contenido, 'usuario':request.user, 'cab':cab, 'personal':tipopersonal}, tipo.correo.split(","))
            return HttpResponseRedirect('/alumnos_cab')

    else:
        data = {'title': 'CAB'}
        addUserData(request, data)
        hoy = datetime.date(datetime.now())
        if 'action' in request.GET:
            action = request.GET['action']
            if action == 'form':
                try:
                    if Inscripcion.objects.filter(persona__usuario__username=request.user, persona__usuario__is_active=True).exists():
                        inscripcion = Inscripcion.objects.filter(persona__usuario__username=request.user, persona__usuario__is_active=True)[:1].get()
                        data['inscripcion'] = inscripcion
                    elif Profesor.objects.filter(persona__usuario__username=request.user, persona__usuario__is_active=True).exists():
                        data['docente'] = Profesor.objects.filter(persona__usuario__username=request.user, persona__usuario__is_active=True)[:1].get()
                    else:
                        data['administrativo'] = True

                    persona = Persona.objects.filter(usuario__username=request.user, usuario__is_active=True)[:1].get()
                    data['persona'] = persona
                    data['hoy'] = hoy
                    data['paises'] = Pais.objects.all().order_by('nombre')
                    data['provincias'] = Provincia.objects.all().order_by('nombre')
                    data['cantones'] = Canton.objects.all().order_by('nombre')
                    data['parroquias'] = Parroquia.objects.all().order_by('nombre')

                    return render(request ,"cab/formulario.html" ,  data)
                except Exception as ex:
                    print(ex)
                    return HttpResponseRedirect('/alumnos_cab')

            elif action == 'ver_form':
                try:
                    if 'inscripcionid' in request.GET:
                        inscripcion = Inscripcion.objects.get(pk=request.GET['inscripcionid'])
                        inscripcion_cab = InscripcionesCAB.objects.filter(inscripcion=inscripcion,  estado=True).order_by('-id')[:1].get()
                        data['tipo'] = "ALUMNO"
                    else:
                        persona = Persona.objects.get(pk=request.GET['personaid'])
                        inscripcion_cab = InscripcionesCAB.objects.filter(persona=persona, estado=True).order_by('-id')[:1].get()
                        if Persona.objects.filter(persona__usuario__groups__id=PROFESORES_GROUP_ID).exists():
                            data['tipo'] = "DOCENTE"
                        else:
                            data['tipo'] = "ADMINISTRATIVO"
                    data['inscripcion_cab'] = inscripcion_cab
                    data['persona'] = inscripcion_cab.persona if inscripcion_cab.persona else inscripcion_cab.inscripcion.persona
                    data['hoy'] = hoy

                    return render(request ,"cab/ver_formulario.html" ,  data)
                except Exception as ex:
                    print(ex)
                    return HttpResponseRedirect('/alumnos_cab')

            elif action == 'desafiliarse':
                try:
                    persona = Persona.objects.filter(usuario__username=request.user, usuario__is_active=True)[:1].get()
                    inscripcion_cab = InscripcionesCAB.objects.filter(pk=request.GET['id'], estado=True).order_by('-id')[:1].get()
                    if inscripcion_cab.inscripcion:
                        data['inscripcion'] = inscripcion_cab.inscripcion
                    data['inscripcion_cab'] = inscripcion_cab
                    data['persona'] = persona
                    data['hoy'] = hoy

                    return render(request ,"cab/desafiliar.html" ,  data)
                except Exception as ex:
                    print(ex)
                    return HttpResponseRedirect('/alumnos_cab')

            elif action == 'add_garante':
                inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                inscripcion_cab = InscripcionesCAB.objects.filter(inscripcion=inscripcion, estado=True).order_by('-id')[:1].get()
                data['inscripcion_cab'] = inscripcion_cab
                data['inscripcion'] = inscripcion
                data['hoy'] = hoy
                data['paises'] = Pais.objects.all().order_by('nombre')
                data['provincias'] = Provincia.objects.all().order_by('nombre')
                data['cantones'] = Canton.objects.all().order_by('nombre')
                data['parroquias'] = Parroquia.objects.all().order_by('nombre')

                return render(request ,"cab/add_garante.html" ,  data)

            elif action == 'ver_garante':
                try:
                    data['garante'] = GaranteCAB.objects.get(pk=request.GET['id'])
                    data['hoy'] = hoy
                    return render(request ,"cab/ver_garante.html" ,  data)
                except Exception as ex:
                    print(ex)

        else:
            try:
                # modulo = Modulo.objects.get(pk=228)
                # for m in ModuloGrupo.objects.filter():
                #     if not m.modulos.filter(id=228):
                #         m.modulos.add(modulo)

                data['hoy'] = hoy
                # INSCRIPCIONES
                if Inscripcion.objects.filter(persona__usuario__username=request.user).exists():
                    inscripcion = Inscripcion.objects.filter(persona__usuario__username=request.user)[:1].get()
                    data['inscripcion'] = inscripcion
                    if InscripcionesCAB.objects.filter(inscripcion=inscripcion, estado=True).exists():
                        inscripcion_cab = InscripcionesCAB.objects.filter(inscripcion=inscripcion, estado=True).order_by('-id')[:1].get()
                        data['inscripcion_cab'] = inscripcion_cab
                        if DesafiliacionCAB.objects.filter(inscripcioncab=inscripcion_cab).exists():
                            solicitud_desafiliacion = DesafiliacionCAB.objects.filter(inscripcioncab=inscripcion_cab).order_by('-id')
                            data['solicitud_desafiliacion'] = solicitud_desafiliacion
                    tipo = TipoIncidencia.objects.get(pk=INCIDENCIA_CAB)
                    # print(tipo.correo.split(",")).append('luis.gomez.veloz@gmail.com')
                    return render(request ,"cab/alumnos_cab.html" ,  data)

                # CAJEROS
                elif request.user.has_perm('sga.change_inscripcionescab') and  Persona.objects.filter(usuario__username=request.user)[:1].get().usuario.groups.filter(id__in=[7]).exists():
                    if 'f' in request.GET:
                        fecha = datetime.strptime(request.GET['f'], '%d-%m-%Y').date()
                        cuotas = CuotaCAB.objects.filter(encab=False, cancelado=True, fechapago=fecha)
                        data['cuotas'] = cuotas
                        data['fecha'] = fecha
                    if 'estado' in request.GET:
                        cuotas = CuotaCAB.objects.filter(encab=True).order_by('fechapago')
                        data['cuotas'] = cuotas
                        data['encab'] = True
                    pendientes = CuotaCAB.objects.filter(encab=False, cancelado=True)
                    data['pendientes'] = pendientes.distinct('fechapago').values('fechapago')
                    return render(request ,"cab/financiero_cab.html" ,  data)

                # ADMINISTRADORES DEL MODULO
                elif request.user.has_perm('sga.change_inscripcionescab') or User.objects.filter(username=request.user)[:1].get().is_superuser:
                    search = None
                    afiliados = InscripcionesCAB.objects.filter().order_by('-id')
                    if 'tipo' in request.GET:
                        tipo = request.GET['tipo']
                        if tipo == 'ins': #INSCRIPCIONES
                            data['inscripciones'] =  True
                            afiliados = afiliados.exclude(inscripcion=None).order_by('-id')
                        elif tipo == 'doc': #DOCENTES
                            data['docentes'] =  True
                            personas = Persona.objects.filter(usuario__groups__id=PROFESORES_GROUP_ID)
                            afiliados = afiliados.filter(persona__id__in=personas.values('id')).order_by('-id')
                        elif tipo == 'adm': #ADMINISTRATIVOS
                            data['administrativos'] =  True
                            personas = Persona.objects.filter().exclude(usuario__groups__id__in=[PROFESORES_GROUP_ID, ALUMNOS_GROUP_ID])
                            afiliados = afiliados.filter(persona__id__in=personas).order_by('-id')
                    else:
                        data['inscripciones'] = True
                        afiliados = afiliados.exclude(inscripcion=None).order_by('-id')

                    if 's' in request.GET:
                        search = request.GET['s']
                    if search:
                        ss = search.split(' ')
                        while '' in ss:
                            ss.remove('')
                        if len(ss)==1:
                            afiliados = afiliados.filter(Q(inscripcion__persona__nombres__icontains=search) | Q(inscripcion__persona__apellido1__icontains=search) | Q(inscripcion__persona__apellido2__icontains=search) | Q(inscripcion__persona__cedula__icontains=search) | Q(inscripcion__persona__pasaporte__icontains=search) | Q(inscripcion__persona__usuario__username__icontains=search))
                        else:
                            afiliados = afiliados.filter(Q(inscripcion__persona__apellido1__icontains=ss[0]) & Q(inscripcion__persona__apellido2__icontains=ss[1]))
                    if 'e' in request.GET:
                        if request.GET['e'] == '1':
                            afiliados = afiliados.filter(en_cab=True)
                        else:
                            afiliados = afiliados.filter(en_cab=False)
                        data['estado'] = True
                    data['search'] = search if search else ""
                    data['inscripciones_cab'] = afiliados
                    return render(request ,"cab/cab.html" ,  data)

                #PERSONAL DOCENTE Y ADMINISTRATIVO
                else:
                    persona = Persona.objects.filter(usuario__username=request.user)[:1].get()
                    data['persona'] = persona
                    if InscripcionesCAB.objects.filter(persona=persona, estado=True).exists():
                        persona_cab = InscripcionesCAB.objects.filter(persona=persona, estado=True).order_by('-id')[:1].get()
                        data['persona_cab'] = persona_cab
                        data['STATIC_ROOT'] = STATIC_ROOT
                        if DesafiliacionCAB.objects.filter(inscripcioncab=persona_cab).exists():
                            solicitud_desafiliacion = DesafiliacionCAB.objects.filter(inscripcioncab=persona_cab).order_by('-id')
                            data['solicitud_desafiliacion'] = solicitud_desafiliacion
                    return render(request ,"cab/personal_cab.html" ,  data)

            except Exception as ex:
                print(ex)
                return HttpResponseRedirect("/alumnos_cab")
