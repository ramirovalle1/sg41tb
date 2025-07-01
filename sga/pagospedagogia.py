 # -*- coding: latin-1 -*-
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
from settings import CENTRO_EXTERNO, RUBRO_TIPO_OTRO_MODULO_INTERNO, RUBRO_TIPO_OTRO_INSCRIPCION, DEFAULT_PASSWORD, PROFESORES_GROUP_ID, ALUMNOS_GROUP_ID, UTILIZA_GRUPOS_ALUMNOS, REPORTE_CERTIFICADO_INSCRIPCION, EMAIL_ACTIVE, EVALUACION_ITB, REGISTRO_HISTORIA_NOTAS, NOTA_ESTADO_EN_CURSO, GENERAR_RUBROS_PAGO, GENERAR_RUBRO_INSCRIPCION, GENERAR_RUBRO_INSCRIPCION_MARGEN_DIAS, MODELO_EVALUACION, EVALUACION_IAVQ, EVALUACION_ITS, UTILIZA_NIVEL0_PROPEDEUTICO, TIPO_PERIODO_PROPEDEUTICO, NOTA_ESTADO_APROBADO, UTILIZA_FICHA_MEDICA, EVALUACION_TES, CORREO_INSTITUCIONAL, USA_CORREO_INSTITUCIONAL, INSCRIPCION_CONDUCCION,TIPO_AYUDA_FINANCIERA, URL_PRE_INSCRIPCION, RUTA_PRE_INSCRIPCION
from sga.alu_malla import aprobadaAsignatura
from sga.commonviews import addUserData, ip_client_address
from sga.docentes import calculate_username
from sga.forms import PersonaForm, InscripcionForm, RecordAcademicoForm, HistoricoRecordAcademicoForm, HistoriaNivelesDeInscripcionForm, CargarFotoForm, EmpresaInscripcionForm, EstudioInscripcionForm, DocumentoInscripcionForm, ActividadesInscripcionForm, PadreClaveForm, ConvalidacionInscripcionForm, HistoricoNotasITBForm, GraduadoDatosForm, EgresadoForm, InscripcionSenescytForm, RetiradoMatriculaForm, InscripcionCextForm, BecarioForm, InscripcionPracticaForm, ObservacionInscripcionForm, ProcesoDobeForm,  ActivaInactivaUsuarioForm, MatriculaBecaForm,InscripcionCextForm, ExternoForm
from sga.models import Profesor, ProcesoDobe, Persona, Inscripcion, RecordAcademico, DocumentosDeInscripcion, HistoricoRecordAcademico, HistoriaNivelesDeInscripcion, FotoPersona, EmpresaInscripcion, EstudioInscripcion, DocumentoInscripcion, Archivo, TipoArchivo, Grupo, InscripcionGrupo, PerfilInscripcion, HistoricoNotasITB, PadreClave, Malla, ConvalidacionInscripcion, TipoEstado, Rubro, RubroInscripcion, NivelMalla, EjeFormativo, AsignaturaMalla, Egresado, Asignatura, InscripcionSenescyt, RetiradoMatricula, Carrera, Modalidad, Sesion, Especialidad, Materia, Nivel, TipoOtroRubro, Matricula, MateriaAsignada, RubroOtro, Graduado, InscripcionBecario, InscripcionPracticas,\
    ObservacionInscripcion, InscripcionConduccion, InactivaActivaUsr, PreInscripcion, Sede, Sexo,Canton,Provincia, TipoAnuncio, TipoIncidencia, RegistroExterno, CuentaBanco, PagoTransferenciaDeposito, PagoExternoPedagogia, RubroMatricula
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
def guardadatos(datos):
    grupo=None
    inscripcion=None
    for d in datos['response']['inscripcion']:
        try:
            fecha = datetime.now().date().year
            cedula = (d['ci'].lstrip().strip()).zfill(10)
            if Grupo.objects.filter(nombre=d['codigo'].upper()).exists():
                grupo= Grupo.objects.filter(nombre=d['codigo'].upper())[:1].get()
            try:
                valor = Decimal(d['valor'])
            except:
                valor = None
            if grupo :
                if d['tipodni'] == 'c':
                    if Inscripcion.objects.filter(persona__cedula=cedula).exists():
                        inscripcion = Inscripcion.objects.filter(persona__cedula=cedula)[:1].get()
                if d['tipodni'] == 'p':
                    if Inscripcion.objects.filter(persona__pasaporte=cedula).exists():
                        inscripcion = Inscripcion.objects.filter(persona__pasaporte=cedula)[:1].get()
                # if Inscripcion.objects.filter(persona__cedula=cedula).exists():
                #     inscripcion =  Inscripcion.objects.filter(persona__cedula=cedula,carrera__grupo=grupo)[:1].get()
                if inscripcion:
                    if not PagoExternoPedagogia.objects.filter(inscripcion=inscripcion,grupo=grupo).exists():
                        pagoped = PagoExternoPedagogia(inscripcion=inscripcion,
                                                       grupo=grupo,
                                                       nombresruc = d['fac_nombre'],
                                                        documento = d['comprobante'],
                                                        identificacionruc =  d['fac_ci'],
                                                        emailruc =  d['fac_email'],
                                                        fonoruc = d['telefono'],
                                                        fecha=d['fac_compro'],
                                                        direccionruc = d['fac_direcion'])
                        pagoped.save()
                    else:
                        pagoped = PagoExternoPedagogia.objects.filter(inscripcion=inscripcion,grupo=grupo)[:1].get()
                        pagoped.nombresruc = d['fac_nombre']
                        pagoped.documento = d['comprobante']
                        pagoped.identificacionruc =  d['fac_ci']
                        pagoped.emailruc =  d['fac_email']
                        pagoped.fecha = d['fac_compro']
                        pagoped.fonoruc = d['telefono']
                        pagoped.direccionruc = d['fac_direcion']
                        pagoped.save()
                    if valor:
                        pagoped.valor=valor
                        pagoped.save()
                    if inscripcion.matricula():

                        if RubroMatricula.objects.filter(matricula = inscripcion.matricula(),matricula__fecha__year=fecha).exists():
                            rubro = RubroMatricula.objects.filter(matricula = inscripcion.matricula(),matricula__fecha__year=fecha)[:1].get()
                            pagoped.rubro = rubro.rubro
                            pagoped.save()
        except Exception as e:
            pass

@login_required(redirect_field_name='ret', login_url='/login')
# @secure_module
@transaction.atomic()

def view(request):
    if request.method=='POST':
        action = request.POST['action']
        if action == 'add':
           pass

    else:
        data = {'title': 'Listado de Comprobantes - Pedagogia'}
        addUserData(request,data)

        if 'action' in request.GET:
            action = request.GET['action']
            pass
        else:
            if DEFAULT_PASSWORD == 'itb':
            # pre_insc('http://www.admin.pedagogia.edu.ec/public/docs/dataformregistro.txt','dato3.txt')
                datos = requests.post('http://api.pedagogia.edu.ec',{'action': 'comprobante',"pagado":"0", 'codigo':'5TO CONGRESO DE PEDAGOGIA'},verify=False)
                if datos.status_code==200:
                    guardadatos( datos.json())
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
                    pagos = PagoExternoPedagogia.objects.filter(Q(nombresruc__icontains=search) | Q(identificacionruc__icontains=search)).order_by('-fecha','nombresruc')
                else:
                    pagos = PagoExternoPedagogia.objects.filter().order_by('-fecha','nombresruc')
                if facturados :
                    pagos = pagos.filter(rubro__cancelado=True).order_by('-fecha','nombresruc')

                if pendientes :
                    pagos = pagos.filter(rubro__cancelado=False).order_by('-fecha','nombresruc')
                paging = MiPaginador(pagos, 30)
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
                data['pagos'] = page.object_list
                data['utiliza_grupos_alumnos'] = UTILIZA_GRUPOS_ALUMNOS
                data['reporte_ficha_id'] = REPORTE_CERTIFICADO_INSCRIPCION
                return render(request ,"pagospedagogia/registro.html" ,  data)
            except:
                return HttpResponseRedirect("/")