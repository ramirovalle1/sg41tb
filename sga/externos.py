 # -*- coding: latin-1 -*-
import csv
from datetime import datetime, timedelta
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
from decorators import secure_module
from settings import CENTRO_EXTERNO, RUBRO_TIPO_OTRO_MODULO_INTERNO, RUBRO_TIPO_OTRO_INSCRIPCION, DEFAULT_PASSWORD, PROFESORES_GROUP_ID, ALUMNOS_GROUP_ID, UTILIZA_GRUPOS_ALUMNOS, REPORTE_CERTIFICADO_INSCRIPCION, EMAIL_ACTIVE, EVALUACION_ITB, REGISTRO_HISTORIA_NOTAS, NOTA_ESTADO_EN_CURSO, GENERAR_RUBROS_PAGO, GENERAR_RUBRO_INSCRIPCION, GENERAR_RUBRO_INSCRIPCION_MARGEN_DIAS, MODELO_EVALUACION, EVALUACION_IAVQ, EVALUACION_ITS, UTILIZA_NIVEL0_PROPEDEUTICO, TIPO_PERIODO_PROPEDEUTICO, NOTA_ESTADO_APROBADO, UTILIZA_FICHA_MEDICA, EVALUACION_TES, CORREO_INSTITUCIONAL, USA_CORREO_INSTITUCIONAL, INSCRIPCION_CONDUCCION,TIPO_AYUDA_FINANCIERA, URL_PRE_INSCRIPCION, RUTA_PRE_INSCRIPCION
from sga.alu_malla import aprobadaAsignatura
from sga.commonviews import addUserData, ip_client_address
from sga.docentes import calculate_username
from sga.forms import PersonaForm, InscripcionForm, RecordAcademicoForm, HistoricoRecordAcademicoForm, HistoriaNivelesDeInscripcionForm, CargarFotoForm, EmpresaInscripcionForm, EstudioInscripcionForm, DocumentoInscripcionForm, ActividadesInscripcionForm, PadreClaveForm, ConvalidacionInscripcionForm, HistoricoNotasITBForm, GraduadoDatosForm, EgresadoForm, InscripcionSenescytForm, RetiradoMatriculaForm, InscripcionCextForm, BecarioForm, InscripcionPracticaForm, ObservacionInscripcionForm, ProcesoDobeForm,  ActivaInactivaUsuarioForm, MatriculaBecaForm,InscripcionCextForm, ExternoForm
from sga.models import Profesor, ProcesoDobe, Persona, Inscripcion, RecordAcademico, DocumentosDeInscripcion, HistoricoRecordAcademico, HistoriaNivelesDeInscripcion, FotoPersona, EmpresaInscripcion, EstudioInscripcion, DocumentoInscripcion, Archivo, TipoArchivo, Grupo, InscripcionGrupo, PerfilInscripcion, HistoricoNotasITB, PadreClave, Malla, ConvalidacionInscripcion, TipoEstado, Rubro, RubroInscripcion, NivelMalla, EjeFormativo, AsignaturaMalla, Egresado, Asignatura, InscripcionSenescyt, RetiradoMatricula, Carrera, Modalidad, Sesion, Especialidad, Materia, Nivel, TipoOtroRubro, Matricula, MateriaAsignada, RubroOtro, Graduado, InscripcionBecario, InscripcionPracticas,\
    ObservacionInscripcion, InscripcionConduccion, InactivaActivaUsr, PreInscripcion, Sede, Sexo,Canton,Provincia, TipoAnuncio, TipoIncidencia, RegistroExterno, CuentaBanco, PagoTransferenciaDeposito
from sga.tasks import gen_passwd, send_html_mail


def email_error(errores):
        if TipoIncidencia.objects.filter(pk=50).exists():
            tipo=TipoIncidencia.objects.get(pk=50)
            hoy = datetime.now().today()
            send_html_mail("Error en Registros Externos",
                "emails/error_externo.html", {'contenido': "Error Registros Externos", 'errores': errores, 'fecha': hoy},tipo.correo.split(","))
def TildesHtml(cadena):
        return cadena.replace('&aacute;',u'á').replace('&eacute;',u'é').replace('&iacute;',u'í').replace('&oacute;',u'ó').replace('&uacute;',u'ú').replace('&ntilde;',u"ñ",).replace('&NTILDE;',u"Ñ",)\
            .replace('&Aacute;',u"Á",).replace('&Eacute;',u"É",).replace('&Iacute;',u"Í",).replace('&Oacute;',u"Ó",).replace('&Uacute;',u"Ú",)

def buscar(url_pre,ruta_pre,):

        url = (url_pre)

        # Crea el archivo dato.txt
        # urllib.urlretrieve("dato.txt")
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

        dataReader = csv.reader(open(csv_filepathname), delimiter='|')


        LINE = -1
        errores= []
        for row in dataReader:
            try:
                if row:
                    # LINE += 1
                    # if LINE==1:
                    #     continue
                    identificacion = row[5]
                    cuenta=None
                    referencia=None
                    if  row[9] != '':
                        if not CuentaBanco.objects.filter(numero = row[9]).exists():
                            errores.append((str(row[5]),str((row[4])+ " " + (row[3])),'No existe la cuenta'))
                            referencia =  row[11]
                        else:
                            cuenta = CuentaBanco.objects.filter(numero = row[9])[:1].get()
                            if PagoTransferenciaDeposito.objects.filter(cuentabanco=cuenta,referencia= row[11].upper()).exists():
                                errores.append((str(row[5]),str((row[4])+ " " + (row[3])),'Ya existe un pago con ese banco y referencia'))
                            elif RegistroExterno.objects.filter(cuenta=cuenta,referencia=row[11].upper()).exists():
                                reg =RegistroExterno.objects.filter(cuenta=cuenta,referencia=row[11].upper())[:1].get()
                                if reg.rubro:
                                    errores.append((str(row[5]),str((row[4])+ " " + (row[3])),'Ya existe un registro con ese banco y referencia en los registros externos'))
                                else:
                                    referencia =  row[11]
                            else:
                                referencia =  row[11]

                    try:
                        # if referencia:
                        if not RegistroExterno.objects.filter(identificacion=identificacion).exists():
                            registro = RegistroExterno( nombres = TildesHtml(row[3]),
                                                        titulo =row[0],
                                                        codigo =row[1],
                                                        apellidos =TildesHtml(row[4]),
                                                        identificacion = row[5],
                                                        email =row[6],
                                                        fono = row[7],
                                                        direccion = TildesHtml(row[8]),
                                                        cuenta = cuenta,
                                                        tipopago = row[10],
                                                        referencia = referencia,
                                                        documento = row[13],
                                                        valor = row[12],
                                                        fecha = row[2])
                        else:
                            registro=RegistroExterno.objects.filter(identificacion=identificacion)[:1].get()
                            if not registro.rubro:
                                registro.nombres = TildesHtml(row[3])
                                registro.titulo =row[0]
                                registro.codigo =row[1]
                                registro.apellidos =TildesHtml(row[4])
                                registro.identificacion = row[5]
                                registro.email =row[6]
                                registro.fono = row[7]
                                registro.direccion =TildesHtml( row[8])
                                registro.cuenta = cuenta
                                registro.tipopago = row[10]
                                registro.referencia =referencia
                                registro.documento = row[13]
                                # registro.valor = row[12]
                                registro.fecha = row[2]
                        registro.save()
                    except Exception as ex:
                       try:
                           print(ex)
                           errores.append((str(row[5]),str(TildesHtml(row[4])+ " " + TildesHtml(row[3])),'Ocurrio un Error' + str(ex)))
                           # email_error(str(row[5]),str(TildesHtml(row[4])+ " " + TildesHtml(row[3])),'Ocurrio un Error' + str(ex))
                       except Exception as e:
                           pass
                    pass


            except Exception as ex:
                try:
                    print(ex)
                    errores.append((str(row[5]),str(TildesHtml(row[4])+ " " + TildesHtml(row[3])),'Ocurrio un Error' + str(ex)))
                except Exception as e:
                    pass
                pass
        if errores:
            email_error(errores)

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
        if action == 'add':
            f = ExternoForm(request.POST)
            if f.is_valid():
                if f.cleaned_data['extranjero']:
                    identificacion=f.cleaned_data['pasaporte']
                    extranjero =  True
                else:
                    identificacion=f.cleaned_data['cedula']
                    extranjero =  False
                if request.POST['externo'] != '0' :
                    externo = RegistroExterno.objects.filter(pk=request.POST['externo'])[:1].get()
                    if not RegistroExterno.objects.filter(identificacion=identificacion).exclude(pk=request.POST['externo']).exists():
                        externo.nombres = f.cleaned_data['nombres']
                        externo.titulo ='1ER SIMPOSIO POLITICO  '
                        externo.codigo ='COMPOL201812'
                        externo.apellidos = f.cleaned_data['apellidos']
                        externo.identificacion = identificacion
                        externo.email = f.cleaned_data['email']
                        externo.fono = f.cleaned_data['fono']
                        externo.direccion = f.cleaned_data['direccion']
                        externo.valor = f.cleaned_data['valor']
                        externo.extranjero = extranjero
                        externo.save()
                        mensaje = 'Editado'
                    else:
                        return HttpResponseRedirect("/externos?msj=Ya existe un registro con esa identificacion")
                else:
                    if not RegistroExterno.objects.filter(identificacion=identificacion).exists():
                        externo = RegistroExterno( nombres = f.cleaned_data['nombres'],
                                                    titulo ='1ER SIMPOSIO POLITICO  ',
                                                    codigo ='COMPOL201812',
                                                    apellidos = f.cleaned_data['apellidos'],
                                                    identificacion = identificacion,
                                                    email =f.cleaned_data['email'],
                                                    fono = f.cleaned_data['fono'],
                                                    direccion = f.cleaned_data['direccion'],
                                                    valor = f.cleaned_data['valor'],
                                                    extranjero=extranjero,
                                                    fecha = datetime.now())
                        externo.save()
                        mensaje = 'Adicionado'

                    else:
                        return HttpResponseRedirect("/externos?msj=Ya existe un registro con esa identificacion")
                client_address = ip_client_address(request)
                # Log de ELIMINACION DE ESTUDIOS QUE CURSA EL DOCENTE
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(externo).pk,
                    object_id       = externo.id,
                    object_repr     = force_str(externo),
                    action_flag     = DELETION,
                    change_message  = mensaje + ' Registro Externo (' + client_address + ')')
                return HttpResponseRedirect("/externos")
        elif action == 'edit':
            f = ExternoForm(request.POST)
            if f.is_valid():
                if f.cleaned_data['extranjero']:
                    identificacion=f.cleaned_data['pasaporte']
                else:
                    identificacion=f.cleaned_data['cedula']
                if RegistroExterno.objects.filter(identificacion=identificacion).exists():
                    registro = RegistroExterno( nombres = f.cleaned_data['nombres'],
                                                titulo ='1ER SIMPOSIO POLITICO  ',
                                                codigo ='COMPOL201812',
                                                apellidos = f.cleaned_data['nombres'],
                                                identificacion = identificacion,
                                                email =f.cleaned_data['email'],
                                                fono = f.cleaned_data['fono'],
                                                direccion = f.cleaned_data['direccion'],
                                                valor = f.cleaned_data['valor'],
                                                fecha = datetime.now())
                    registro.save()
                    return HttpResponseRedirect("/externos")
                else:
                    return HttpResponseRedirect("/externos?msj=Ya existe un registro con esa identificacion")


    else:
        data = {'title': 'Listado de Registros Externos'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='activation':
                d = Profesor.objects.get(pk=request.GET['id'])
                d.activo = not d.activo
                d.save()
                return HttpResponseRedirect("/docentes")
            elif action=='actualizar':
                buscar('http://compol.ec/wp-content/uploads/registros/registro.txt','/var/lib/django/repobucki/media/reportes/dato4.txt')
                return  HttpResponseRedirect("/externos")
            elif action=='nuevo':
                data['title'] = 'Adicionar Externo'
                data['form'] = ExternoForm(initial={'nacimiento': datetime.now()})
                data['externo_id']='0'
                return render(request ,"registro_externo/adicionarbs.html" ,  data)
            elif action=='edit':
                data['title'] = 'Editar Externo'
                externo = RegistroExterno.objects.filter(pk=request.GET['id'])[:1].get()
                initial = model_to_dict(externo)
                data['externo'] = externo
                data['form'] = ExternoForm(initial=initial)
                data['externo_id']=externo.id
                return render(request ,"registro_externo/adicionarbs.html" ,  data)
        else:
            try:
                search = None
                facturados = None
                pendientes = None
                if 'msj' in request.GET:
                    data['msj']=request.GET['msj']
                if 's' in request.GET:
                    search = request.GET['s']
                if 'f' in request.GET:
                    facturados = request.GET['f']
                if 'p' in request.GET:
                    pendientes = request.GET['p']
                if 't' in request.GET:
                    todos = request.GET['t']
                if search:
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')
                    if len(ss)==1:
                        registro = RegistroExterno.objects.filter(Q(nombres__icontains=search) | Q(apellidos__icontains=search)| Q(identificacion__icontains=search)).order_by('-fecha','apellidos','nombres',)
                    else:
                        registro = RegistroExterno.objects.filter(Q(nombres__icontains=ss[0]) & Q(apellidos__icontains=ss[1])).order_by('-fecha','apellidos','nombres')
                else:
                    registro = RegistroExterno.objects.filter().order_by('-fecha','apellidos','nombres')
                if facturados :
                    registro = registro.filter(rubro__cancelado=True).order_by('-fecha','apellidos','nombres')

                if pendientes :
                    registro = registro.filter(Q(rubro__cancelado=False)|Q(rubro =None)).order_by('-fecha','apellidos','nombres')
                paging = MiPaginador(registro, 30)
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
                data['facturados'] = facturados if facturados else ""
                data['pendientes'] = pendientes if pendientes else ""
                data['registro'] = page.object_list
                data['utiliza_grupos_alumnos'] = UTILIZA_GRUPOS_ALUMNOS
                data['reporte_ficha_id'] = REPORTE_CERTIFICADO_INSCRIPCION
                data['puede_pagar'] = data['persona'].puede_recibir_pagos()
                return render(request ,"registro_externo/registro.html" ,  data)
            except:
                return HttpResponseRedirect("/externos")