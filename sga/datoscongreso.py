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

from sga.models import Profesor, ProcesoDobe, Persona, Inscripcion,  Grupo,  TipoIncidencia, DatosPersonaCongresoIns, Matricula
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

@login_required(redirect_field_name='ret', login_url='/login')
# @secure_module
@transaction.atomic()

def view(request):
    if request.method=='POST':
        action = request.POST['action']
        if action == 'add':
           pass
    else:
        data = {'title': ' Listado de Asistentes'}
        addUserData(request,data)

        if 'action' in request.GET:
            action = request.GET['action']
            if action== 'ver':
                try:
                    data={}
                    datos =[]
                    inscripcion = Inscripcion.objects.get(pk=request.GET['rid'])
                    registro = DatosPersonaCongresoIns.objects.filter(inscripcion=inscripcion).order_by('grupo').distinct('grupo').values('grupo')
                    grupos = Grupo.objects.filter(id__in=registro)
                    data['inscripcion'] = inscripcion
                    data['grupos'] = grupos
                    return render(request ,"pagospedagogia/detalle.html" ,  data)
                except Exception as ex :
                    return HttpResponse(json.dumps({'result':'bad', "error": str(ex)}),content_type="application/json")

        else:
            try:
                search = None
                facturados = None
                pendientes = None
                if 'msj' in request.GET:
                    data['msj']=request.GET['msj']
                if 's' in request.GET:
                    search = request.GET['s']

                if 't' in request.GET:
                    todos = request.GET['t']

                ins = DatosPersonaCongresoIns.objects.filter().exclude(inscripcion=None).distinct('inscripcion').values('inscripcion')
                if search:
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')
                    if len(ss)==1:
                           registro = Matricula.objects.filter(Q(inscripcion__persona__nombres__icontains=search) | Q(inscripcion__persona__apellido1__icontains=search) | Q(inscripcion__persona__apellido2__icontains=search) | Q(inscripcion__persona__cedula__icontains=search) | Q(inscripcion__persona__pasaporte__icontains=search) | Q(inscripcion__identificador__icontains=search) | Q(inscripcion__inscripciongrupo__grupo__nombre__icontains=search) | Q(inscripcion__carrera__nombre__icontains=search) | Q(inscripcion__persona__usuario__username__icontains=search),inscripcion__id__in=ins,nivel__cerrado=False).order_by('persona__apellido1')
                    else:
                        registro = Matricula.objects.filter(Q(inscripcion__persona__apellido1__icontains=ss[0]) & Q(inscripcion__persona__apellido2__icontains=ss[1]),inscripcion__id__in=ins,nivel__cerrado=False).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')
                else:
                    registro = Matricula.objects.filter(inscripcion__id__in=ins,nivel__cerrado=False).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')[:100]
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

                data['registro'] = page.object_list
                data['utiliza_grupos_alumnos'] = UTILIZA_GRUPOS_ALUMNOS
                data['reporte_ficha_id'] = REPORTE_CERTIFICADO_INSCRIPCION
                return render(request ,"pagospedagogia/datosregistro.html" ,  data)
            except:
                return HttpResponseRedirect("/")