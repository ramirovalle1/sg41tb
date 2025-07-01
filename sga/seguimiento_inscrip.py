import csv
from datetime import datetime
import json
import os
import urllib
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template import RequestContext
from decorators import secure_module
from settings import UTILIZA_GRUPOS_ALUMNOS, REPORTE_CERTIFICADO_INSCRIPCION, DEFAULT_PASSWORD, UTILIZA_FICHA_MEDICA, CENTRO_EXTERNO, MODELO_EVALUACION, EVALUACION_TES, ID_DEPARTAMENTO_ASUNTO_ESTUDIANT, PROFESORES_GROUP_ID, ALUMNOS_GROUP_ID,EMAIL_ACTIVE
from sga.commonviews import addUserData
from sga.models import SolicituInfo, PreInscripcion, RegistroSeguimiento, OpcionRespuesta, Referidos, LlamadaUsuario, EstadoLlamada, OpcionEstadoLlamada, Sexo, AsistAsuntoEstudiant, Inscripcion, Grupo, TipoRespuesta, CitaLlamada

def convertir_fecha(s):
    try:
        return datetime(int(s[-4:]), int(s[3:5]), int(s[:2]))
    except:
        return None
def guardar():
    try:
        url = ("http://www.itb.edu.ec/public/docs/dataformcontacto.txt")

        # Crea el archivo dato.txt
        # urllib.urlretrieve(url,"contacto3.txt")
        urllib.urlretrieve(url,"/var/lib/django/repobucki/media/reportes/contacto.txt")
        #
        # Archivo web
        # SITE_ROOT = os.path.dirname(os.path.realpath(__file__))

        # csv_filepathname= "dato.txt"

        # csv_filepathname="contacto3.txt"
        csv_filepathname="/var/lib/django/repobucki/media/reportes/contacto.txt"

        # your_djangoproject_home=os.path.split(SITE_ROOT)[0]

        # sys.path.append(your_djangoproject_home)
        os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

        dataReader = csv.reader(open(csv_filepathname), delimiter=';')


        LINE = -1
        for row in dataReader:
            if row:
                # LINE += 1
                # if LINE==1:
                #     continue
                try:
                    if not SolicituInfo.objects.filter(codigo=row[0]).exists():
                        solicitud  = SolicituInfo(codigo=row[0],
                                        identificacion  = row[0],
                                        nombres=row[1],
                                        correo=row[2],
                                        ciudad=row[3],
                                        direccion=row[4],
                                        fonodom=row[5],
                                        fonoofi=row[6],
                                        celular=row[7],
                                        interes=row[9],
                                        mensaje=row[10],
                                        fecha = row[11])
                        solicitud.save()
                    else:
                        solicitud=SolicituInfo.objects.filter(codigo=row[0])[:1].get()
                        solicitud.codigo=row[0]
                        solicitud.nombres=row[1]
                        solicitud.correo=row[2]
                        solicitud.ciudad=row[3]
                        solicitud.direccion=row[4]
                        solicitud.fonodom=row[5]
                        solicitud.fonoofi=row[6]
                        solicitud.celular=row[7]
                        solicitud.interes=row[9]
                        solicitud.mensaje=row[10]
                        solicitud.fecha = row[11]

                    solicitud.save()
                        # print(preinscripcion.nombres + " " +preinscripcion.apellido1)
                except Exception as ex:
                        pass
    except Exception as ex:
        pass
    # os.remove("contacto.txt")
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
    if request.method=='POST':
        action = request.POST['action']
        try:
            if action=='addseguimientoinscrito':
                try:


                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
            # //////////////////////////////////////////////////////////////////////////////////////////////////



            # //////////////////////////////////////////////////////////////////////////////////////////////////
            elif action=='addseguimientopreinscrito':
                try:
                    preinscripcion =  PreInscripcion.objects.get(pk=request.POST['id'])


                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

            elif action == 'guardar':
                try:
                    registro = RegistroSeguimiento.objects.get(pk=request.POST['id'])
                    registro.identificacion = request.POST['iden']
                    registro.nombres = request.POST['nomb']
                    registro.apellidos = request.POST['ape']
                    registro.celular = request.POST['cel']
                    registro.email = request.POST['email']
                    registro.ciudad = request.POST['ciu']
                    registro.fonodomicilio = request.POST['fonod']
                    registro.fonotrabajo = request.POST['fonot']
                    registro.lugartrabajo = request.POST['lugart']
                    registro.ext = request.POST['ext']

                    registro.observacion = request.POST['obs']
                    registro.save()

                    if request.POST['sexo'] !='0' :
                        registro.sexo.id = request.POST['sexo']
                        registro.save()

                    if 'opc' in request.POST:
                        try:
                            if OpcionRespuesta.objects.filter(pk=request.POST['opc']).exists():
                                op = OpcionRespuesta.objects.get(pk=request.POST['opc'])
                                registro.opcionrespuesta = op
                                registro.save()
                        except:
                            pass

                    if 'motivor' in request.POST:
                        if request.POST['motivor'] != '0':
                            tipores = TipoRespuesta.objects.get(pk=request.POST['motivor'])
                            registro.tiporespuesta =tipores
                            registro.save()

                    if 'info' in request.POST:
                        if request.POST['info'] == 'on':
                            registro.enviarinformacion = True

                        else:
                            registro.enviarinformacion = False
                        registro.save()
                    if 'enviado' in request.POST:
                        if request.POST['enviado'] == 'on':
                            registro.enviado = True

                        else:
                            registro.enviado = False
                        registro.save()
                    if request.POST['rid1']:
                        if Referidos.objects.filter(pk=request.POST['rid1']).exists():
                            referido = Referidos.objects.get(pk=request.POST['rid1'])
                            referido.nombres = request.POST['rnombre1']
                            referido.celular = request.POST['rcel1']
                            referido.email = request.POST['remail1']
                            referido.save()

                    else:
                        referido = Referidos(registro=registro,
                                             nombres = request.POST['rnombre1'],
                                             celular = request.POST['rcel1'],
                                             email = request.POST['remail1'])

                        referido.save()
                    if request.POST['rid2']:
                        if Referidos.objects.filter(pk=request.POST['rid2']).exists():
                            referido = Referidos.objects.get(pk=request.POST['rid2'])
                            referido.nombres = request.POST['rnombre2']
                            referido.celular = request.POST['rcel2']
                            referido.email = request.POST['remail2']
                            referido.save()
                    else:
                         referido = Referidos(registro=registro,
                                              nombres = request.POST['rnombre2'],
                                             celular = request.POST['rcel2'],
                                             email = request.POST['remail2'])

                         referido.save()
                    if request.POST['rid3']:
                        if Referidos.objects.filter(pk=request.POST['rid3']).exists():
                            referido = Referidos.objects.get(pk=request.POST['rid3'])
                            referido.nombres = request.POST['rnombre3']
                            referido.celular = request.POST['rcel3']
                            referido.email = request.POST['remail3']
                            referido.save()
                    else:
                         referido = Referidos(registro=registro,
                                             nombres = request.POST['rnombre3'],
                                             celular = request.POST['rcel3'],
                                             email = request.POST['remail3'])

                         referido.save()



                    usuario = LlamadaUsuario(usuario=request.user,
                                             registro=registro,
                                             fecha=datetime.now())
                    usuario.save()
                    if 'estado' in request.POST:
                        if  EstadoLlamada.objects.filter(pk=request.POST['estado']).exists():
                            est = EstadoLlamada.objects.get(pk=request.POST['estado'])
                            usuario.estadollamada = est
                            usuario.save()
                    if 'opcestado' in request.POST:
                        if  OpcionEstadoLlamada.objects.filter(pk=request.POST['opcestado']).exists():
                            opc = OpcionEstadoLlamada.objects.get(pk=request.POST['opcestado'])
                            usuario.opcionllamada= opc
                            usuario.save()

                    if 'nota' in request.POST:
                        usuario.nota= request.POST['nota']
                        usuario.save()

                    if  request.POST['ids'] != '':
                        solicitud = SolicituInfo.objects.get(pk=request.POST['ids'])
                        solicitud.identificacion = registro.identificacion
                        solicitud.save()

                    if request.POST['cita'] =='true':
                        dpto = Group.objects.get(pk=request.POST['dpto'])
                        cita = CitaLlamada(registro=registro,
                                        fecha = convertir_fecha(request.POST['fecha']),
                                        hora = request.POST['hora'],
                                        departamento=dpto)
                        cita.save()
                        if EMAIL_ACTIVE:
                            cita.correo(request.user)



                    if request.POST['finaliza'] =='true':
                        registro.finalizada=True
                        registro.save()

                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

            elif action == 'consulta':
                try:
                    lista=[]
                    if OpcionEstadoLlamada.objects.filter(estadollamada__id=request.POST['id']).exists():
                        for op in OpcionEstadoLlamada.objects.filter(estadollamada__id=request.POST['id']):
                            lista.append((op.id , op.descripcion))
                        return HttpResponse(json.dumps({"result":"ok","lista":lista }),content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({"result":"nodata" }),content_type="application/json")


                except:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")






            return HttpResponseRedirect("/seguimien_inscrip")

        except:
            return HttpResponseRedirect("/seguimien_inscrip")
    else:
        data = {'title': 'Seguimiento'}
        addUserData(request,data)
        try:
            if 'action' in request.GET:
                action = request.GET['action']

                if action=='correos':
                    if 'ficha' in request.GET:
                        solicitud = SolicituInfo.objects.get(id=request.GET['id'])
                        data['solicitud'] = solicitud
                        if RegistroSeguimiento.objects.filter(identificacion=solicitud.identificacion).exists():
                            registro = RegistroSeguimiento.objects.filter(identificacion=solicitud.identificacion)[:1].get()

                        else:
                            registro = RegistroSeguimiento(identificacion = solicitud.identificacion,
                                                           nombres=solicitud.nombres,
                                                            celular = solicitud.celular,
                                                            email =  solicitud.correo,
                                                            fonodomicilio = solicitud.fonodom,
                                                            fonotrabajo = solicitud.fonoofi,
                                                            ciudad=solicitud.ciudad)

                            registro.save()
                        # registro.seinscribio = registro.se_incribio()
                        # registro.pago = registro.pago_ins()
                        data['registro'] = registro
                        ref =[]
                        if registro.opcionrespuesta:
                            data['opcrespuesta'] = OpcionRespuesta.objects.filter().exclude(pk=registro.opcionrespuesta.id)
                        else:
                            data['opcrespuesta'] = OpcionRespuesta.objects.all()
                        data['estadollamada'] = EstadoLlamada.objects.all()
                        data['opcllamada'] = OpcionEstadoLlamada.objects.all()
                        if registro.sexo:
                            data['sexo'] = Sexo.objects.filter().exclude(pk=registro.sexo.id)
                        else:
                            data['sexo'] = Sexo.objects.all()
                        # data['referidos'] = Referidos.objects.filter(registro=registro)
                        for r in Referidos.objects.filter(registro=registro):
                            ref.append((r.id,r.nombres,r.celular,r.email))
                        data['ref'] = ref

                        data['llamada'] = LlamadaUsuario.objects.filter(registro=registro)
                        if LlamadaUsuario.objects.filter(registro=registro,estadollamada__id=1).exists():
                            data['efectiva'] = 1
                        data['op'] = 'correo'
                        return render(request ,"seguimiento/ficha.html" ,  data)
                    else:

                        search = None
                        todos = None
                        activos = None
                        finalizados = None
                        band=0
                        if 's' in request.GET:
                            search = request.GET['s']
                            band=1
                        if 'a' in request.GET:
                            activos = request.GET['a']
                        if 'i' in request.GET:
                            inactivos = request.GET['i']
                        if 't' in request.GET:
                            todos = request.GET['t']
                        if 'f' in request.GET:
                            finalizados = request.GET['f']
                        if search:
                            ss = search.split(' ')
                            while '' in ss:
                                ss.remove('')
                            if len(ss)==1:
                                solicitudes = SolicituInfo.objects.filter(Q(Q(nombres__icontains=search) | Q(codigo__icontains=search) | Q(identificacion=search))).order_by('-codigo')
                            else:
                                solicitudes = SolicituInfo.objects.filter(Q(Q(nombres__icontains=search) | Q(codigo__icontains=search))).order_by('-codigo')

                        else:
                            # guardar()
                            solicitudes = SolicituInfo.objects.filter(finalizado=False).order_by('-codigo')
                            # inscripciones = Inscripcion.objects.filter(persona__usuario__is_active=True,fecha__gte=fecha).order_by('persona__apellido1')[:100]


                        #     inscripciones = inscripciones.filter(carrera__grupocoordinadorcarrera__group__in=request.user.groups.all()).distinct()

                        if todos:
                            solicitudes = SolicituInfo.objects.filter(finalizado=False).order_by('-codigo')

                        if finalizados:
                            data['finalizados'] = finalizados
                            solicitudes = SolicituInfo.objects.filter(finalizado=True).order_by('-codigo')


                        paging = MiPaginador(solicitudes, 30)
                        p = 1
                        try:
                            if 'page' in request.GET:
                                p = int(request.GET['page'])
                                # if band==0:
                                #     inscripciones = Inscripcion.objects.all().order_by('persona__apellido1')
                                paging = MiPaginador(solicitudes, 30)
                            page = paging.page(p)
                        except Exception as ex:
                            page = paging.page(1)

                        # Para atencion al cliente

                        data['paging'] = paging
                        data['rangospaging'] = paging.rangos_paginado(p)
                        data['page'] = page
                        data['search'] = search if search else ""
                        data['todos'] = todos if todos else ""
                        data['solicitudes'] = page.object_list
                        data['fechaactual'] = datetime.now().date()
                        data['asistasuntoestudiant'] = AsistAsuntoEstudiant.objects.filter(estado=True)


                        return render(request ,"seguimiento/seguimiento.html" ,  data)


                elif action == 'online':
                    hoy = str(datetime.date(datetime.now()))
                    if 'ficha' in request.GET:
                        preinscripcion = PreInscripcion.objects.get(id=request.GET['id'])
                        if RegistroSeguimiento.objects.filter(identificacion=preinscripcion.cedula).exists():
                            registro = RegistroSeguimiento.objects.filter(identificacion=preinscripcion.cedula)[:1].get()

                        else:
                            registro = RegistroSeguimiento(identificacion = preinscripcion.cedula,
                                                           nombres=preinscripcion.nombres,
                                                           apellidos = str(preinscripcion.apellido1 + " "+  preinscripcion.apellido2),
                                                            celular = preinscripcion.celular,
                                                            email =  preinscripcion.email,
                                                            fonodomicilio = preinscripcion.telefono,
                                                            sexo_id = preinscripcion.sexo.id)
                            registro.save()
                        # registro.seinscribio = registro.se_incribio()
                        # registro.pago = registro.pago_ins()
                        registro.save()
                        data['registro'] = registro
                        ref =[]
                        if registro.opcionrespuesta:
                            data['opcrespuesta'] = OpcionRespuesta.objects.filter().exclude(pk=registro.opcionrespuesta.id)
                        else:
                            data['opcrespuesta'] = OpcionRespuesta.objects.all()
                        data['estadollamada'] = EstadoLlamada.objects.all()
                        data['opcllamada'] = OpcionEstadoLlamada.objects.all()
                        data['tiporespuesta'] = TipoRespuesta.objects.all()
                        if registro.sexo:
                            data['sexo'] = Sexo.objects.filter().exclude(pk=registro.sexo.id)
                        else:
                            data['sexo'] = Sexo.objects.all()
                        # data['referidos'] = Referidos.objects.filter(registro=registro)
                        for r in Referidos.objects.filter(registro=registro):
                            ref.append((r.id,r.nombres,r.celular,r.email))
                        data['ref'] = ref

                        data['llamada'] = LlamadaUsuario.objects.filter(registro=registro)
                        if LlamadaUsuario.objects.filter(registro=registro,estadollamada__id=1).exists():
                            data['efectiva'] = 1

                        data['op'] = 'online'
                        gruposexcluidos = [PROFESORES_GROUP_ID,ALUMNOS_GROUP_ID]
                        data['departamentos'] = Group.objects.filter(id__in=ID_DEPARTAMENTO_ASUNTO_ESTUDIANT).exclude(user=None).exclude(id__in=gruposexcluidos).order_by('name')
                        data['citas']=CitaLlamada.objects.filter(registro=registro)
                        return render(request ,"seguimiento/ficha.html" ,  data)


                    # elif 'addregistro' in request.GET:
                    #
                    #     return render(request ,"seguimiento/addobservacion.html" ,  data)


                    else:
                        try:
                            hoy = str(datetime.date(datetime.now()))
                            search = None
                            todos = None
                            activos = None
                            inactivos = None
                            op = None
                            lista=[]
                            if 's' in request.GET:
                                search = request.GET['s']
                            if 'a' in request.GET:
                                activos = request.GET['a']
                            if 'i' in request.GET:
                                inactivos = request.GET['i']
                            if 't' in request.GET:
                                todos = request.GET['t']
                            if 'op' in request.GET:
                                op=request.GET['op']
                                estado =EstadoLlamada.objects.get(pk=request.GET['llamada'])
                                data['llamada'] =request.GET['llamada']
                                llamada = LlamadaUsuario.objects.filter(estadollamada=estado).values('registro')
                                for r in  RegistroSeguimiento.objects.filter(seinscribio=False,pk__in=llamada):
                                    if  LlamadaUsuario.objects.filter(registro=r).exists():
                                        re=  LlamadaUsuario.objects.filter(registro=r).latest('id')
                                        if re.estadollamada==estado:
                                            lista.append(r.identificacion)
                            if search:
                                ss = search.split(' ')
                                while '' in ss:
                                    ss.remove('')
                                if len(ss)==1:
                                    preinscritos = PreInscripcion.objects.filter(Q(nombres__icontains=search,inscrito=False, fecha_caducidad__lt=hoy) | Q(apellido1__icontains=search,inscrito=False, fecha_caducidad__lt=hoy) | Q(apellido2__icontains=search,inscrito=False, fecha_caducidad__lt=hoy) | Q(cedula__icontains=search,inscrito=False, fecha_caducidad__lt=hoy) | Q(cedula=search,inscrito=False)| Q(grupo__nombre__icontains=search,inscrito=False, fecha_caducidad__lt=hoy) | Q(carrera__nombre__icontains=search,inscrito=False, fecha_caducidad__lt=hoy)).exclude(id__in=PreInscripcion.objects.filter(cedula__in=Inscripcion.objects.all().values('persona__cedula')).order_by('-fecha_registro').values('id')).order_by('-fecha_registro')
                                else:
                                    preinscritos = PreInscripcion.objects.filter(Q(apellido1__icontains=ss[0],inscrito=False, fecha_caducidad__lt=hoy) & Q(apellido2__icontains=ss[1],inscrito=False, fecha_caducidad__lt=hoy)).exclude(id__in=PreInscripcion.objects.filter(cedula__in=Inscripcion.objects.all().values('persona__cedula')).order_by('-fecha_registro').values('id')).order_by('-fecha_registro','apellido1','apellido2','nombres')

                            else:
                                # i = Inscripcion.objects.all().values('persona__cedula')

                                # preinscritos = PreInscripcion.objects.filter().exclude(cedula__in=Inscripcion.objects.all().values('persona__cedula')).order_by('-fecha_registro')
                                preinscritos=PreInscripcion.objects.filter(fecha_caducidad__lt=hoy).exclude(id__in=PreInscripcion.objects.filter(cedula__in=Inscripcion.objects.all().values('persona__cedula')).order_by('fecha_registro').values('id')).order_by('-fecha_registro')

                            if op:
                                data['estado'] = estado
                                preinscritos=PreInscripcion.objects.filter(fecha_caducidad__lt=hoy,cedula__in=lista)
                                # preinscritos = PreInscripcion.objects.filter(inscrito=False, fecha_caducidad__lt=hoy).exclude(cedula__in=i).order_by('-fecha_registro')

                            if 'telefono' in request.GET:
                                data['telefono'] = 1
                                preinscritos=PreInscripcion.objects.filter(fecha_caducidad__lt=hoy).exclude(telefono="''",celular="''").exclude(telefono="",celular="").exclude(id__in=PreInscripcion.objects.filter(cedula__in=Inscripcion.objects.all().values('persona__cedula')).order_by('fecha_registro').values('id')).order_by('-fecha_registro')

                            if 'email' in request.GET:
                                data['email'] = 1
                                preinscritos=PreInscripcion.objects.filter(Q(fecha_caducidad__lt=hoy),Q(telefono="''",celular="''")|Q(telefono="",celular="")).exclude(email="''").exclude(id__in=PreInscripcion.objects.filter(cedula__in=Inscripcion.objects.all().values('persona__cedula')).order_by('fecha_registro').values('id')).order_by('-fecha_registro')

                            # else:
                            #     preinscritos = PreInscripcion.objects.filter(carrera__grupocoordinadorcarrera__group__in=request.user.groups.all()).distinct()

                            paging = MiPaginador(preinscritos, 30)
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
                            data['op'] = op if op else ""
                            data['preinscritos'] = page.object_list
                            data['utiliza_grupos_alumnos'] = UTILIZA_GRUPOS_ALUMNOS
                            data['reporte_ficha_id'] = REPORTE_CERTIFICADO_INSCRIPCION
                            data['clave'] = DEFAULT_PASSWORD
                            data['usafichamedica'] = UTILIZA_FICHA_MEDICA
                            data['centroexterno'] = CENTRO_EXTERNO
                            data['matriculalibre'] = MODELO_EVALUACION==EVALUACION_TES
                            data['grupos'] = Grupo.objects.all().order_by('nombre')
                            data['estadollamada'] = EstadoLlamada.objects.all()
                            return render(request ,"seguimiento/preinscripcionesbs.html" ,  data)

                        except Exception as e:
                            return HttpResponseRedirect("/seguimien_inscrip")


            else:
                return render(request ,"seguimiento/menu_inscrip.html" ,  data)

        except Exception as ex:
            return HttpResponseRedirect("/?info="+str(ex))