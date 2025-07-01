import csv
from datetime import datetime, timedelta
from decimal import Decimal
import json
import os
import urllib
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Avg
from django.db.models.aggregates import Sum
from django.db import transaction
from django.db.models.query_utils import Q
from django.forms.models import model_to_dict
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.utils.encoding import force_str
from django.template import RequestContext
import sys
import requests
from decorators import secure_module
from settings import CENTRO_EXTERNO, RUBRO_TIPO_OTRO_MODULO_INTERNO, RUBRO_TIPO_OTRO_INSCRIPCION, DEFAULT_PASSWORD, PROFESORES_GROUP_ID, ALUMNOS_GROUP_ID, UTILIZA_GRUPOS_ALUMNOS, REPORTE_CERTIFICADO_INSCRIPCION, EMAIL_ACTIVE, EVALUACION_ITB, REGISTRO_HISTORIA_NOTAS, NOTA_ESTADO_EN_CURSO, GENERAR_RUBROS_PAGO, GENERAR_RUBRO_INSCRIPCION, GENERAR_RUBRO_INSCRIPCION_MARGEN_DIAS, MODELO_EVALUACION, EVALUACION_IAVQ, EVALUACION_ITS, UTILIZA_NIVEL0_PROPEDEUTICO, TIPO_PERIODO_PROPEDEUTICO, NOTA_ESTADO_APROBADO, UTILIZA_FICHA_MEDICA, EVALUACION_TES, CORREO_INSTITUCIONAL, USA_CORREO_INSTITUCIONAL, INSCRIPCION_CONDUCCION,TIPO_AYUDA_FINANCIERA, URL_PRE_INSCRIPCION, RUTA_PRE_INSCRIPCION, USER_CONGRESO, CARRERAENFERMERIAMEDICA
from sga.alu_malla import aprobadaAsignatura
from sga.commonviews import addUserData, ip_client_address
from sga.docentes import calculate_username
from sga.forms import PersonaForm, InscripcionForm, RecordAcademicoForm, HistoricoRecordAcademicoForm, HistoriaNivelesDeInscripcionForm, CargarFotoForm, EmpresaInscripcionForm, EstudioInscripcionForm, DocumentoInscripcionForm, ActividadesInscripcionForm, PadreClaveForm, ConvalidacionInscripcionForm, HistoricoNotasITBForm, GraduadoDatosForm, EgresadoForm, InscripcionSenescytForm, RetiradoMatriculaForm, InscripcionCextForm, BecarioForm, InscripcionPracticaForm, ObservacionInscripcionForm, ProcesoDobeForm,  ActivaInactivaUsuarioForm, MatriculaBecaForm,InscripcionCextForm
from sga.models import Profesor, ProcesoDobe, Persona, Inscripcion, RecordAcademico, DocumentosDeInscripcion, HistoricoRecordAcademico, HistoriaNivelesDeInscripcion, FotoPersona, EmpresaInscripcion, EstudioInscripcion, DocumentoInscripcion, Archivo, TipoArchivo, Grupo, InscripcionGrupo, PerfilInscripcion, HistoricoNotasITB, PadreClave, Malla, ConvalidacionInscripcion, TipoEstado, Rubro, RubroInscripcion, NivelMalla, EjeFormativo, AsignaturaMalla, Egresado, Asignatura, InscripcionSenescyt, RetiradoMatricula, Carrera, Modalidad, Sesion, Especialidad, Materia, Nivel, TipoOtroRubro, Matricula, MateriaAsignada, RubroOtro, Graduado, InscripcionBecario, InscripcionPracticas,\
    ObservacionInscripcion, InscripcionConduccion, InactivaActivaUsr, PreInscripcion, Sede, Sexo,Canton,Provincia, TipoAnuncio, TipoIncidencia, TipoPersonaCongreso,  RequerimientoCongreso, DatosPersonaCongresoIns, Discapacidad, Colegio, elimina_tildes
from sga.tasks import gen_passwd, send_html_mail

def email_error_pagoonline(errores,op):
        if TipoIncidencia.objects.filter(pk=50).exists():
            tipo=TipoIncidencia.objects.get(pk=50)
            hoy = datetime.now().today()
            send_html_mail("Se encontraron errores el pago online",
                "emails/error_pagoonlinecongreso.html", {'contenido': "Error Pago Online", 'errores': errores,'op':op},tipo.correo.split(","))

def email_error(error,ruta):
        if TipoIncidencia.objects.filter(pk=50).exists():
            tipo=TipoIncidencia.objects.get(pk=50)
            hoy = datetime.now().today()
            send_html_mail("Se encontro un error en la Preinscripcion",
                "emails/error_preins.html", {'contenido': "Error Preinscripcion", 'error': error, 'fecha': hoy,'ruta':ruta},tipo.correo.split(","))

def email_error_congreso(errores,op):
        if TipoIncidencia.objects.filter(pk=50).exists():
            tipo=TipoIncidencia.objects.get(pk=50)
            hoy = datetime.now().today()
            send_html_mail("Se encontraron errores",
                "emails/error_congreso.html", {'contenido': "Error", 'errores': errores,'op':op},tipo.correo.split(","))
def pre_insc(url_pre,ruta_pre,):

        url = (url_pre)

        # Crea el archivo dato.txt
        # urllib.urlretrieve(url,"dato.txt")
        urllib.urlretrieve(url,ruta_pre)
        #
        # Archivo web
        # SITE_ROOT = os.path.dirname(os.path.realpath(__file__))

        # csv_filepathname= "dato.txt"

        # csv_filepathname="dato.txt"
        csv_filepathname=ruta_pre

        # your_djangoproject_home=os.path.split(SITE_ROOT)[0]

        # sys.path.append(your_djangoproject_home)
        os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

        dataReader = csv.reader(open(csv_filepathname), delimiter=';')


        LINE = -1
        for row in dataReader:
            try:
                if row:
                    # LINE += 1
                    # if LINE==1:
                    #     continue
                    canton = None
                    provincia = None
                    tipoanuncio = None
                    if Carrera.objects.filter(nombre=row[0].upper()).exists():
                        carrera = Carrera.objects.filter(nombre=row[0].upper())[:1].get()
                    else:
                        carrera = Carrera.objects.all()[:1].get()

                    if Modalidad.objects.filter(nombre=row[1].upper()).exists():
                        modalidad= Modalidad.objects.filter(nombre=row[1].upper())[:1].get()
                    else:
                        modalidad = Modalidad.objects.all()[:1].get()

                    if row[25] != '':
                        if Canton.objects.filter(pk=row[25]).exists():
                            canton= Canton.objects.filter(pk=row[25])[:1].get()
                    if row[26] != '':
                        if Provincia.objects.filter(pk=row[26]).exists():
                            provincia= Provincia.objects.filter(pk=row[26])[:1].get()
                    try:
                        if row[27] != '':
                            if TipoAnuncio.objects.filter(pk=row[27]).exists():
                                tipoanuncio= TipoAnuncio.objects.filter(pk=row[27])[:1].get()
                    except :
                        pass

                    # if Sesion.objects.filter(nombre=row[2].upper()).exists():
                    #     seccion= Sesion.objects.filter(nombre=row[2].upper())[:1].get()
                    # else:
                    #     seccion = Sesion.objects.all()[:1].get()

                    if Grupo.objects.filter(nombre=row[3].upper()).exists():
                        grupo= Grupo.objects.filter(nombre=row[3].upper())[:1].get()
                        seccion = grupo.sesion
                    else:
                        grupo = Grupo.objects.all()[:1].get()
                        seccion = Sesion.objects.all()[:1].get()

                    if Sexo.objects.filter(nombre=row[10].upper()).exists():
                        sexo= Sexo.objects.filter(nombre=row[10].upper())[:1].get()
                    else:
                        sexo = Sexo.objects.all()[:1].get()

                    if Especialidad.objects.filter(nombre=row[17].upper()).exists():
                        especialidad= Especialidad.objects.filter(nombre=row[17].upper())[:1].get()
                    else:
                        especialidad = Especialidad.objects.all()[:1].get()

                    cedula = (row[8].lstrip().strip()).zfill(10)
                    hoy = str(datetime.date(datetime.now()))
                    caducidad = (row[20])
                    try:
                        if (caducidad>=hoy):
                            horaregnuv = None
                            if row[19] != '':
                                horaregnuv = row[19]

                            if not PreInscripcion.objects.filter(cedula=cedula,carrera=carrera).exists():
                                preinscripcion = PreInscripcion(carrera=carrera,
                                                modalidad=modalidad,
                                                seccion=seccion,
                                                grupo=grupo,
                                                inicio_clases=(row[4]),
                                                nombres=row[5],
                                                apellido1=row[6],
                                                apellido2=row[7],
                                                cedula=cedula,
                                                nacimiento=row[9],
                                                email=(row[11].lower()),
                                                sexo=sexo,
                                                telefono=row[12],
                                                celular=row[14],
                                                colegio=row[16],
                                                especialidad=especialidad,
                                                fecha_registro=row[18],
                                                hora_registro=horaregnuv,
                                                fecha_caducidad=row[20],
                                                calleprincipal=row[22],
                                                callesecundaria=row[23],
                                                numerocasa=row[24],
                                                canton=canton,
                                                provincia=provincia,
                                                tipoanuncio=tipoanuncio)
                            else:
                                preinscripcion=PreInscripcion.objects.filter(cedula=cedula,carrera=carrera)[:1].get()
                                preinscripcion.carrera=carrera
                                preinscripcion.modalidad=modalidad
                                preinscripcion.grupo=grupo
                                preinscripcion.inicio_clases=row[4]
                                preinscripcion.nombres=row[5]
                                preinscripcion.apellido1=row[6]
                                preinscripcion.apellido2=row[7]
                                preinscripcion.cedula=cedula
                                preinscripcion.nacimiento=row[9]
                                preinscripcion.email=row[11].lower()
                                preinscripcion.sexo=sexo
                                preinscripcion.telefono=row[12]
                                preinscripcion.celular=row[14]
                                preinscripcion.colegio=row[16]
                                preinscripcion.especialidad=especialidad
                                preinscripcion.fecha_registro=row[18]
                                preinscripcion.hora_registro=horaregnuv
                                preinscripcion.fecha_caducidad=row[20]
                                preinscripcion.calleprincipal=row[22]
                                preinscripcion.callesecundaria=row[23]
                                preinscripcion.numerocasa=row[24]
                                preinscripcion.canton=canton
                                preinscripcion.provincia=provincia
                                preinscripcion.tipoanuncio = tipoanuncio
                            # if Inscripcion.objects.filter(persona__cedula=preinscripcion.cedula).exists():
                            #     for i in Inscripcion.objects.filter(persona__cedula=preinscripcion.cedula):
                            #         for ic in i.inscripciongrupo_set.all():
                            #             if not i.matricula():
                            #                 if ic.grupo.carrera == preinscripcion.grupo.carrera:
                            #                     preinscripcion.inscrito=True
                            #                     preinscripcion.save()

                            if PreInscripcion.objects.filter(cedula=cedula,carrera=carrera).count() < 1:
                                preinscripcion.save()
                            # print(preinscripcion.nombres + " " +preinscripcion.apellido1)
                    except Exception as ex:
                       try:
                            email_error(str(ex) + "ERROR1 Ced: " +str(row[8])+ " len" +str(len(row))+ " cont.len" +str(len(row[len(row)])),url_pre)
                       except Exception as e:
                           pass
                    pass


            except Exception as ex:
                try:
                    email_error(str(ex) + "ERROR2 Ced: " +str(row[8])+ " len" +str(len(row))+ " cont.len" +str(len(row[len(row)])),url_pre)
                except Exception as e:
                    pass
                pass
# os.remove("dato.txt")

def guardadatos(datos):
    errores =[]
    for d in datos['response']['inscripcion']:
        canton = None
        provincia = None
        tipoanuncio = None
        colegio = None
        inscripcion = None

        try:
            if Carrera.objects.filter(nombre=d['cnombre'].upper()).exists():
                carrera = Carrera.objects.filter(nombre=d['cnombre'].upper())[:1].get()
            else:
                carrera = Carrera.objects.all()[:1].get()

            if Modalidad.objects.filter(nombre=d['tipo'].upper()).exists():
                modalidad= Modalidad.objects.filter(nombre=d['tipo'].upper())[:1].get()
            else:
                modalidad = Modalidad.objects.all()[:1].get()


            if TipoAnuncio.objects.filter(pk=13).exists():
                tipoanuncio= TipoAnuncio.objects.filter(pk=13)[:1].get()

            if Grupo.objects.filter(nombre=d['codigo'].upper()).exists():
                grupo= Grupo.objects.filter(nombre=d['codigo'].upper())[:1].get()
                seccion = grupo.sesion
            else:
                grupo = Grupo.objects.all()[:1].get()
                seccion = Sesion.objects.all()[:1].get()

            if Sexo.objects.filter(nombre=d['sexo'].upper()).exists():
                sexo= Sexo.objects.filter(nombre=d['sexo'].upper())[:1].get()
            else:
                sexo = Sexo.objects.all()[:1].get()


            valor = Decimal(d['valor'])



            cedula = (d['ci'].lstrip().strip())
            hoy = str(datetime.date(datetime.now()))
            # caducidad = (row[20])
            if not PreInscripcion.objects.filter(cedula=cedula,carrera=carrera).exists():
                preinscripcion = PreInscripcion(
                                tipodoc = d['tipodni'],
                                carrera=carrera,
                                modalidad=modalidad,
                                seccion=seccion,
                                grupo=grupo,
                                # inicio_clases=(row[4]),
                                nombres=elimina_tildes(d['nombre']),
                                apellido1=elimina_tildes(d['paterno']),
                                apellido2=elimina_tildes(d['materno']),
                                cedula=cedula,
                                fecha_registro = d['creado'],
                                nacimiento=d['fecha'],
                                email=(d['email'].lower()),
                                sexo=sexo,
                                telefono=d['telefono'],
                                celular=d['cell'],
                                fecha_caducidad=d['vence'],
                                calleprincipal=d['direccion'],
                                valor=valor,
                                tipoanuncio=tipoanuncio)
            else:
                preinscripcion=PreInscripcion.objects.filter(cedula=cedula,carrera=carrera)[:1].get()
                preinscripcion.carrera=carrera
                preinscripcion.modalidad=modalidad
                preinscripcion.seccion=seccion
                preinscripcion.grupo=grupo
                preinscripcion.nombres=d['nombre']
                preinscripcion.tipodoc=d['tipodni']
                preinscripcion.apellido1=d['paterno']
                preinscripcion.apellido2=d['materno']
                preinscripcion.cedula=cedula
                preinscripcion.email=(d['email'].lower())
                preinscripcion.sexo=sexo
                preinscripcion.telefono=d['telefono']
                preinscripcion.celular=d['cell']
                preinscripcion.fecha_caducidad=d['vence']
                preinscripcion.valor=valor
                preinscripcion.fecha_registro=d['creado']
                preinscripcion.calleprincipal=d['direccion']
                preinscripcion.tipoanuncio=tipoanuncio
            preinscripcion.save()

            if DatosPersonaCongresoIns.objects.filter(preinscripcion=preinscripcion,grupo=preinscripcion.grupo,inscripcion=None).exists():
                DatosPersonaCongresoIns.objects.filter(preinscripcion=preinscripcion,grupo=preinscripcion.grupo,inscripcion=None).delete()
            for part in d['participa'].split(','):
                try:
                    partid = int(part)
                except:
                    partid =0

                if TipoPersonaCongreso.objects.filter(pk=partid).exists():
                    tipopersona = TipoPersonaCongreso.objects.filter(pk=partid)[:1].get()
                    if not DatosPersonaCongresoIns.objects.filter(preinscripcion=preinscripcion,tipopersona=tipopersona,grupo=preinscripcion.grupo).exists():
                        personains = DatosPersonaCongresoIns(preinscripcion=preinscripcion,
                                                       tipopersona=tipopersona,
                                                       grupo=preinscripcion.grupo)
                        personains.save()

            for dis in d['discapacidad'].split(','):
                try:
                    disid = int(dis)
                except:
                    disid =0
                if Discapacidad.objects.filter(pk=disid).exists():
                    discapacidad = Discapacidad.objects.filter(pk=disid)[:1].get()
                    if not DatosPersonaCongresoIns.objects.filter(preinscripcion=preinscripcion,tipodiscapacidad=discapacidad,grupo=preinscripcion.grupo).exists():
                        personains = DatosPersonaCongresoIns(preinscripcion=preinscripcion,
                                                       tipodiscapacidad=discapacidad,
                                                       grupo=preinscripcion.grupo)
                        personains.save()
            for r in d['requerimiento'].split(','):
                try:
                    rid = int(r)
                except:
                    rid=0
                if RequerimientoCongreso.objects.filter(pk=rid).exists():
                    requerimiento = RequerimientoCongreso.objects.filter(pk=rid)[:1].get()
                    if not DatosPersonaCongresoIns.objects.filter(preinscripcion=preinscripcion,requerimiento=requerimiento,grupo=preinscripcion.grupo).exists():
                        personains = DatosPersonaCongresoIns(preinscripcion=preinscripcion,
                                                       requerimiento=requerimiento,
                                                       grupo=preinscripcion.grupo)
                        personains.save()
            inscripciones=''
            if d['tipodni'] == 'c':
                if Inscripcion.objects.filter(persona__cedula=preinscripcion.cedula).exists():
                    inscripciones = Inscripcion.objects.filter(persona__cedula=preinscripcion.cedula)
            if d['tipodni'] == 'p':
                    if Inscripcion.objects.filter(persona__pasaporte=preinscripcion.cedula).exists():
                        inscripciones = Inscripcion.objects.filter(persona__pasaporte=preinscripcion.cedula)
            if inscripciones:
                for i in inscripciones:
                    for ic in i.inscripciongrupo_set.all():
                        if ic.grupo.carrera == preinscripcion.grupo.carrera:
                            ic.grupo = preinscripcion.grupo
                            ic.save()
                            inscripcion = i
                            preinscripcion.inscrito=True
                            preinscripcion.save()

                preinscripcion.save()
                if not inscripcion.matricula():
                    try:

                        nivel=Nivel.objects.filter(grupo=grupo)[:1].get()
                        inscripcion.matricular_pedagogia(nivel)
                    except Exception as e:
                        errores.append((e,d['ci']))
                        pass
            else:
                fechacaducidad = datetime(int(preinscripcion.fecha_caducidad.split('-')[0]),int(preinscripcion.fecha_caducidad.split('-')[1]), int(preinscripcion.fecha_caducidad.split('-')[2]))
                p=1
                if fechacaducidad.date() >= datetime.now().date() or p ==1:
                    extranjero=False
                    pasaporte=''
                    cedula=''
                    if preinscripcion.tipodoc =='p':
                        extranjero=True
                        pasaporte=preinscripcion.cedula
                    else:
                        cedula=preinscripcion.cedula
                    persona = Persona(nombres=elimina_tildes(d['nombre']),
                                        apellido1= elimina_tildes(d['paterno']),
                                        apellido2=elimina_tildes(d['materno']),
                                        extranjero=extranjero,
                                        cedula=cedula,
                                        pasaporte=pasaporte,
                                        nacimiento=d['fecha'],
                                        sexo=sexo,
                                        direccion=d['direccion'],
                                        telefono=d['cell'],
                                        telefono_conv=d['telefono'],
                                        email=(d['email'].lower()))
                    persona.save()
                    username = calculate_username(persona)
                    password = DEFAULT_PASSWORD
                    user = User.objects.create_user(username, persona.email, password)
                    user.save()
                    persona.usuario = user
                    persona.save()
                    usuariocon = User.objects.get(pk=USER_CONGRESO)
                    inscripcion = Inscripcion(persona=persona,
                                            fecha = datetime.now(),
                                            carrera=grupo.carrera,
                                            descuentoporcent=0,
                                            modalidad=grupo.modalidad,
                                            sesion=grupo.sesion,
                                            identificador='',
                                            tienediscapacidad=False,
                                            doblematricula=False,
                                            observacion="INSCRIPCION AUTOMATICA",
                                            anuncio=tipoanuncio,
                                            user=usuariocon )
                    # inscripcion.save()
                    i = Inscripcion.objects.latest('id') if Inscripcion.objects.exists() else None
                    if i:
                        inscripcion.numerom = i.numerom + 1
                    else:
                        inscripcion.numerom = 1
                    inscripcion.save()
                    if not InscripcionGrupo.objects.filter(inscripcion=inscripcion, grupo=grupo, activo=True).exists():
                        ig = InscripcionGrupo(inscripcion=inscripcion, grupo=grupo, activo=True)
                        ig.save()
                    else:
                        ig= InscripcionGrupo.objects.filter(inscripcion=inscripcion,activo=True)[:1].get()
                        ig.grupo=grupo
                        ig.save()
                    if not inscripcion.matricula():
                        try:

                            nivel=Nivel.objects.filter(grupo=grupo)[:1].get()
                            inscripcion.matricular_pedagogia(nivel)
                        except Exception as e:
                            errores.append((e,d['ci']))
                            pass
                else:
                    if not preinscripcion.enviocorreo:
                        preinscripcion.correo_aviso()
                        if not inscripcion.matricula():
                            preinscripcion.enviocorreo=True
                            preinscripcion.save()



        except Exception as e:
            errores.append((e,d['ci']))
    if errores:
          email_error_congreso(errores,'PREINSCRIPCION CONGRESO')

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
        if action=='inscribir':
            data=[]
            preinscripcion = PreInscripcion.objects.get(pk=request.POST['id'])
            data['title'] = 'Nueva Inscripcion de Alumno'
            insf = InscripcionCextForm(initial={'fecha': datetime.now()})
            data['form'] = insf
            data['utiliza_grupos_alumnos'] = UTILIZA_GRUPOS_ALUMNOS
            data['grupos_abiertos'] = Grupo.objects.filter(abierto=True).order_by('-nombre')
            data['centroexterno'] = CENTRO_EXTERNO
            data['inscripcion_conduccion'] = INSCRIPCION_CONDUCCION
            return render(request ,"inscripciones/adicionarbs.html" ,  data)

            # return HttpResponseRedirect("/becas_matricula?action=practicas&id="+str(preinscripcion.id))
    else:
        # pre_insc(URL_PRE_INSCRIPCION,RUTA_PRE_INSCRIPCION)
        # if DEFAULT_PASSWORD == 'itb':
        #     datos = requests.post('http://api.pedagogia.edu.ec',{'action': 'consulta', 'pagado': '0','codigo':'6TO CONGRESO DE PEDAGOGIA'},verify=False)
        #     if datos.status_code==200:
        #         guardadatos( datos.json())
        data = {'title': 'Listado de PreInscritos'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='activation':
                d = Profesor.objects.get(pk=request.GET['id'])
                d.activo = not d.activo
                d.save()
                return HttpResponseRedirect("/docentes")
            elif action=='inscribir':
                preinscripcion = PreInscripcion.objects.get(pk=request.GET['id'])
                data['title'] = 'Nueva Inscripcion de Alumno'
                insf = InscripcionCextForm(initial={'fecha': datetime.now()})
                data['form'] = insf
                data['utiliza_grupos_alumnos'] = UTILIZA_GRUPOS_ALUMNOS
                data['grupos_abiertos'] = Grupo.objects.filter(abierto=True).order_by('-nombre')
                data['centroexterno'] = CENTRO_EXTERNO
                data['inscripcion_conduccion'] = INSCRIPCION_CONDUCCION
                return HttpResponseRedirect("/inscripciones?action=add&preinscripcion="+str(preinscripcion.id))

        else:
            try:
                hoy = str(datetime.date(datetime.now()))
                search = None
                todos = None
                activos = None
                inactivos = None

                if 's' in request.GET:
                    search = request.GET['s']
                if 'a' in request.GET:
                    activos = request.GET['a']
                if 'i' in request.GET:
                    inactivos = request.GET['i']
                if 't' in request.GET:
                    todos = request.GET['t']
                if search:
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')
                    if len(ss)==1:
                        preinscritos = PreInscripcion.objects.filter(Q(nombres__icontains=search,inscrito=False) | Q(apellido1__icontains=search,inscrito=False) | Q(apellido2__icontains=search,inscrito=False, fecha_caducidad__gte=hoy) | Q(cedula__icontains=search,inscrito=False)| Q(grupo__nombre__icontains=search,inscrito=False) | Q(carrera__nombre__icontains=search,inscrito=False),carrera__id=CARRERAENFERMERIAMEDICA).order_by('-fecha_registro')
                    else:
                        preinscritos = PreInscripcion.objects.filter(Q(apellido1__icontains=ss[0],inscrito=False, fecha_caducidad__gte=hoy) & Q(apellido2__icontains=ss[1],inscrito=False),carrera__id=CARRERAENFERMERIAMEDICA).order_by('-fecha_registro','apellido1','apellido2','nombres')

                else:
                    preinscritos = PreInscripcion.objects.filter(inscrito=False,carrera__id=CARRERAENFERMERIAMEDICA).order_by('-fecha_registro')

                if 'g' in request.GET:
                    grupoid = request.GET['g']
                    data['grupo'] = Grupo.objects.get(pk=request.GET['g'])
                    data['grupoid'] = int(grupoid) if grupoid else ""
                    preinscritos = PreInscripcion.objects.filter( grupo=data['grupo'],inscrito=False,carrera__id=CARRERAENFERMERIAMEDICA).distinct().order_by('-fecha_registro')
                    # preinscritos = PreInscripcion.objects.filter(carrera__grupocoordinadorcarrera__group__in=request.user.groups.all(), grupo=data['grupo'],inscrito=False, fecha_caducidad__gte=hoy).distinct().order_by('-fecha_registro')
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
                data['preinscritos'] = page.object_list
                data['utiliza_grupos_alumnos'] = UTILIZA_GRUPOS_ALUMNOS
                data['reporte_ficha_id'] = REPORTE_CERTIFICADO_INSCRIPCION
                data['clave'] = DEFAULT_PASSWORD
                data['usafichamedica'] = UTILIZA_FICHA_MEDICA
                data['centroexterno'] = CENTRO_EXTERNO
                data['matriculalibre'] = MODELO_EVALUACION==EVALUACION_TES
                data['grupos'] = Grupo.objects.all().order_by('nombre')
                return render(request ,"pre_inscripciones/preinscripcionesbs.html" ,  data)

            except:
                return HttpResponseRedirect("/pre_inscripciones")

