import csv
from datetime import datetime
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
import xlwt
from decorators import secure_module
from settings import CENTRO_EXTERNO, RUBRO_TIPO_OTRO_MODULO_INTERNO, RUBRO_TIPO_OTRO_INSCRIPCION, DEFAULT_PASSWORD, PROFESORES_GROUP_ID, ALUMNOS_GROUP_ID, UTILIZA_GRUPOS_ALUMNOS, REPORTE_CERTIFICADO_INSCRIPCION, EMAIL_ACTIVE, EVALUACION_ITB, REGISTRO_HISTORIA_NOTAS, NOTA_ESTADO_EN_CURSO, GENERAR_RUBROS_PAGO, GENERAR_RUBRO_INSCRIPCION, GENERAR_RUBRO_INSCRIPCION_MARGEN_DIAS, MODELO_EVALUACION, EVALUACION_IAVQ, EVALUACION_ITS, UTILIZA_NIVEL0_PROPEDEUTICO, TIPO_PERIODO_PROPEDEUTICO, NOTA_ESTADO_APROBADO, UTILIZA_FICHA_MEDICA, EVALUACION_TES, CORREO_INSTITUCIONAL, USA_CORREO_INSTITUCIONAL, INSCRIPCION_CONDUCCION,TIPO_AYUDA_FINANCIERA, URL_PRE_INSCRIPCION, RUTA_PRE_INSCRIPCION, MEDIA_ROOT, PROMOCION_REGALA_SONRISAS
from sga.alu_malla import aprobadaAsignatura
from sga.commonviews import addUserData, ip_client_address
from sga.dbf import elimina_tildes
from sga.docentes import calculate_username
from sga.forms import InscripcionCextForm,InscripcionReferidoForm, RangoReferidoForm, RangoReferidoComisionaForm
from sga.inscripciones import convertir_fecha
from sga.models import Profesor, ProcesoDobe, Persona, Inscripcion, RecordAcademico, DocumentosDeInscripcion, HistoricoRecordAcademico, \
     HistoriaNivelesDeInscripcion, FotoPersona, EmpresaInscripcion, EstudioInscripcion, DocumentoInscripcion, Archivo, TipoArchivo, Grupo, \
     InscripcionGrupo, PerfilInscripcion, HistoricoNotasITB, PadreClave, Malla, ConvalidacionInscripcion, TipoEstado, Rubro, \
     RubroInscripcion, NivelMalla, EjeFormativo, AsignaturaMalla, Egresado, Asignatura, InscripcionSenescyt, RetiradoMatricula, Carrera, \
     Modalidad, Sesion, Especialidad, Materia, Nivel, TipoOtroRubro, Matricula, MateriaAsignada, RubroOtro, Graduado, InscripcionBecario,\
     InscripcionPracticas,ObservacionInscripcion, InscripcionConduccion, InactivaActivaUsr, PreInscripcion, Sede, Sexo,Canton,Provincia,\
     ReferidosInscripcion,LugarRecaudacion, SesionCaja, Promocion
from sga.tasks import gen_passwd

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

        elif action == 'cambiaestado':
            try:
                referidos = ReferidosInscripcion.objects.get(pk=request.POST['rid'])
                client_address = ip_client_address(request)
                cambiar = False
                if referidos.online:
                    if referidos.verificar_inscrip_online() and referidos.verificar_pago_online():
                        cambiar = True
                    if referidos.verificar_promocion_rsonrisas_online():
                        if not referidos.verificar_pago_cuota1_online():
                            cambiar=False
                elif referidos.conduccion:
                    if referidos.verificar_inscrip_conduccion() and referidos.verificar_pago_conduccion():
                        cambiar = True

                else:
                    if referidos.inscrito:
                        if referidos.inscripcionref.promocion_id == PROMOCION_REGALA_SONRISAS:
                            if referidos.verificar_pago_matricula() and referidos.verificar_pago_1():
                                cambiar = True
                        else:
                            if referidos.verificar_pago_matricula():
                                cambiar = True
                    else:
                        return HttpResponse(json.dumps({'result': 'bad' , 'mensaje':'El referido no esta Inscrito'}), content_type="application/json")

                if cambiar:
                    referidos.aprobado_pago = not referidos.aprobado_pago
                    referidos.save()

                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(referidos).pk,
                        object_id       = referidos.id,
                        object_repr     = force_str(referidos),
                        action_flag     = DELETION,
                        change_message  = 'CAMBIO DE ESTADO DE PAGO A ' + str(referidos.aprobado_pago) +' (' + client_address + ')' )
                    return HttpResponse(json.dumps({'result': 'ok'}), content_type="application/json")
                else:
                    return HttpResponse(json.dumps({'result': 'bad' , 'mensaje':'El referido no ha REalizado los pagos necesarios'}), content_type="application/json")
            except Exception as e:
                print(e)
                return HttpResponse(json.dumps({'result': 'bad', 'mensaje': str(e)}),   content_type="application/json")

        elif action=='pago_comision':

            try:

                if SesionCaja.objects.filter(id=request.POST['sesion_id'], abierta=True).exists():
                    sesion = SesionCaja.objects.get(id=request.POST['sesion_id'], abierta=True)

                    referidos = ReferidosInscripcion.objects.get(pk=request.POST['idreferido'])
                    referidos.pagocomision=True
                    referidos.valorpago=Decimal(request.POST['total'])
                    referidos.fechapago=datetime.now()
                    referidos.observacion=str(request.POST['motivo']).upper()
                    referidos.sesioncaja=sesion

                    referidos.save()

                    referidos.correo_referidos_pago(request.user,'SE REGISTRO PAGO COMISION REFERIDO')

                    return HttpResponse(json.dumps({'result': 'ok'}),
                            content_type="application/json")

                return HttpResponse(json.dumps({'result': 'bad','message': 'NO TIENE SESION DE CAJA ABIERTA'}),
                                content_type="application/json")

            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}),
                                    content_type="application/json")


        elif action =='add':
            f = InscripcionReferidoForm(request.POST)
            if f.is_valid():
                pass
            inscripcion = None
            administrativo = None
            if 'administrativo' in request.POST:
                administrativo = Persona.objects.get(pk=request.POST['id'])
            else:
                inscripcion = Inscripcion.objects.get(pk=request.POST['id'])
            if 'ref' in request.POST:
                referidos = ReferidosInscripcion.objects.get(pk=request.POST['ref'])
                referidos.cedula=f.cleaned_data['cedula']
                referidos.apellido1=f.cleaned_data['apellido1']
                referidos.extranjero=f.cleaned_data['extranjero']
                referidos.apellido2=f.cleaned_data['apellido2']
                referidos.nombres=f.cleaned_data['nombres']
                referidos.pasaporte=f.cleaned_data['pasaporte']
                referidos.sexo=f.cleaned_data['sexo']
                referidos.telefono_conv=f.cleaned_data['telefono_conv']
                referidos.telefono=f.cleaned_data['telefono']
                referidos.fecha=datetime.now().date()
                referidos.inscripcion=inscripcion
                referidos.administrativo=administrativo
                referidos.email=f.cleaned_data['email']
                referidos.carrea=f.cleaned_data['carrera']
                referidos.modalidad=f.cleaned_data['modalidad']
                referidos.save()
            else:

                referidos = ReferidosInscripcion(cedula=f.cleaned_data['cedula'],
                                                 apellido1=f.cleaned_data['apellido1'],
                                                 extranjero=f.cleaned_data['extranjero'],
                                                 apellido2=f.cleaned_data['apellido2'],
                                                 nombres=f.cleaned_data['nombres'],
                                                 pasaporte=f.cleaned_data['pasaporte'],
                                                 sexo=f.cleaned_data['sexo'],
                                                 telefono_conv=f.cleaned_data['telefono_conv'],
                                                 telefono=f.cleaned_data['telefono'],
                                                 fecha=datetime.now().date(),
                                                 inscripcion=inscripcion,
                                                 administrativo=administrativo,
                                                 email=f.cleaned_data['email'],
                                                 carrea=f.cleaned_data['carrera'],
                                                 modalidad=f.cleaned_data['modalidad'])
            referidos.save()
            return HttpResponseRedirect("/alu_referidos")

        elif action == 'generararchivo':
            try:
                data = {'title': ''}
                referidos = ReferidosInscripcion.objects.filter(fecha__gt=convertir_fecha(request.POST['fechainicio']),
                fecha__lt=convertir_fecha(request.POST['fechafinal']),activo=True).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')

                titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                titulo.font.height = 20 * 11
                subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                subtitulo.font.height = 20 * 10
                wb = xlwt.Workbook()

                ws = wb.add_sheet('Referidos', cell_overwrite_ok=True)

                ws.write(0, 1, 'INSTITUTO TECNOLOGICO BOLIVARIANO', titulo)
                ws.write(1, 1, 'REPORTE DE REFERIDO', titulo)

                fila = 3
                col = 0

                ws.write(fila - 1, col , "FECHA REGISTRO",titulo)
                ws.write(fila - 1, col + 1, "NOMBRES",titulo)
                ws.write(fila - 1, col + 2, "CEDULA", titulo)
                ws.write(fila - 1, col + 3, "TELEFONO", titulo)
                ws.write(fila - 1, col + 4, "TELEFONO CONVENCIONAL", titulo)
                ws.write(fila - 1, col + 5, "EMAIL", titulo)
                ws.write(fila - 1, col + 6, "PERSONA QUE REFIERE", titulo)
                ws.write(fila - 1, col + 7, "VENDEDOR", titulo)
                ws.write(fila - 1, col + 8, "INSCRIPCION PAGADA	", titulo)
                ws.write(fila - 1, col + 9, "MATRICULA PAGADA", titulo)
                ws.write(fila - 1, col + 10, "PAGO DE COMISION", titulo)
                ws.write(fila - 1, col + 11, "ONLINE", titulo)
                ws.write(fila - 1, col + 12, "ESTADO", titulo)
                ws.write(fila - 1, col + 13, "PAGO APROBADO", titulo)
                ws.write(fila - 1, col + 14, "CARRERA", titulo)
                ws.write(fila - 1, col + 15, "TIPO PERSONA", titulo)
                ws.write(fila - 1, col + 16, "EFECTIVO", titulo)
                ws.write(fila - 1, col + 17, "RAZON ESTADO", titulo)
                ws.write(fila - 1, col + 18, "OBSERVACION", titulo)
                ws.write(fila - 1, col + 19, "SE INSCRIBIRA", titulo)
                ws.write(fila - 1, col + 20, "F POSIBLE INSCRIPCION", titulo)
                ws.write(fila - 1, col + 21, "GESTOR", titulo)
                ws.write(fila - 1, col + 22, "CONDUCCION", titulo)

                c=''
                for c in referidos:
                    #print(c)
                    #OCastillo 31-07-2020 para traer info de CRM
                    carrera=''
                    gestion=''
                    efectivo=''
                    razon=''
                    observacion=''
                    seinscribira=''
                    f_posible=''
                    tipopersona=''
                    if c.online==False:
                        if c.conduccion==True:
                            datos = requests.get('https://crmcondu.itb.edu.ec/funciones',params={'a': 'vergestion','idprospecto':str(c.idprospecto)},verify=False)
                        else:
                            datos = requests.get('https://crm.itb.edu.ec/api',params={'a': 'vergestion','idprospecto':str(c.idprospecto)},verify=False)
                    else:
                        datos = requests.get('https://sgaonline.itb.edu.ec/funciones',params={'a': 'vergestion','idprospecto':str(c.idprospecto)},verify=False)

                    if datos.status_code == 200:
                        datos=datos.json()
                        if datos['result']=='ok':
                            listahistorial= datos['listahistorial']
                            if len(listahistorial)>0:
                                efectivo=elimina_tildes(listahistorial[0]['efectivo'])
                                razon=elimina_tildes(listahistorial[0]['razonestado'])
                                observacion=elimina_tildes(listahistorial[0]['observacion'])
                                if listahistorial[0]['inscripcion']:
                                    seinscribira="Si"
                                else:
                                    seinscribira="No"
                                f_posible=str(listahistorial[0]['fechainscripcion'])
                                gestion=listahistorial[0]['gestor']
                            else:
                                if len(listahistorial)==0:
                                    gestion='NO TIENE GESTION'

                    ws.write(fila, col,  str(c.fecha))
                    ws.write(fila, col + 1,  elimina_tildes(c.apellido1)+" "+elimina_tildes(c.apellido2)+" "+elimina_tildes(c.nombres))
                    ws.write(fila, col + 2, c.cedula)
                    ws.write(fila, col + 3, c.telefono)
                    ws.write(fila, col + 4, c.telefono_conv)
                    ws.write(fila, col + 5, c.email)
                    if c.inscripcion:
                        ws.write(fila, col + 6, str(c.inscripcion))
                    else:
                        ws.write(fila, col + 6, str(c.administrativo))

                    if c.online:
                       ws.write(fila, col + 7, elimina_tildes(c.verficarNombreVendedor()))
                    else:
                       if c.conduccion==True:
                            ws.write(fila, col + 7, elimina_tildes(c.verficarNombreVendedorConduccion()))
                       else:
                            ws.write(fila, col + 7, elimina_tildes(c.verficarNombreVendedor().nombre_completo()) if c.verficarNombreVendedor() else '')

                    if c.online:
                        if c.verificar_inscrip_online():
                            ws.write(fila, col + 8, str("SI"))
                        else:
                            ws.write(fila, col + 8, str("NO"))
                    elif c.conduccion:
                        if c.conduccion==True:
                            if c.verificar_inscrip_conduccion():
                                ws.write(fila, col + 8, str("SI"))
                            else:
                                ws.write(fila, col + 8, str("NO"))
                    else:
                        if c.inscrito:
                            ws.write(fila, col + 8, str("SI"))
                        else:
                            ws.write(fila, col + 8, str("NO"))

                    if c.online:
                        if c.verificar_pago_online():
                            ws.write(fila, col + 9, str("SI"))
                        else:
                            ws.write(fila, col + 9, str("NO"))
                    else:
                        if c.conduccion==True:

                            if c.verificar_pago_conduccion():
                                ws.write(fila, col + 9, str("SI"))
                            else:
                                ws.write(fila, col + 9, str("NO"))

                        else:
                            if c.verificar_pago_matricula():
                                ws.write(fila, col + 9, str("SI"))
                            else:
                                ws.write(fila, col + 9, str("NO"))

                    if c.pagocomision:
                        ws.write(fila, col + 10, str("SI"))
                    else:
                        ws.write(fila, col + 10, str("NO"))

                    if c.online:
                        ws.write(fila, col + 11, str("SI"))
                    else:
                        ws.write(fila, col + 11, str("NO"))

                    if c.activo:
                        ws.write(fila, col + 12, str("SI"))
                    else:
                        ws.write(fila, col + 12, str("NO"))

                    if c.aprobado_pago:
                        ws.write(fila, col + 13, str("SI"))
                    else:
                        ws.write(fila, col + 13, str("NO"))

                    try:
                        if c.carrera.nombre:
                            carrera=elimina_tildes(c.carrera.nombre)
                        else:
                            carrera='NO TIENE CARRERA'
                            
                    except Exception as ex:
                            pass
                            carrera='NO TIENE CARRERA'
                    ws.write(fila, col + 14,  carrera)

                    if c.administrativo:
                        if c.administrativo:
                            usuario = c.administrativo.usuario.id
                            if User.objects.filter(pk=usuario, groups__id=146,is_active=True):
                                tipopersona='VENTAS EXTERNAS 2'
                            else:
                                tipopersona='ADMINISTRATIVO'
                        ws.write(fila, col + 15, str(tipopersona))
                        #ws.write(fila, col + 15, str("ADMINISTRATIVO"))
                    else:
                        ws.write(fila, col + 15, str("ALUMNO"))

                    ws.write(fila, col + 16, efectivo)
                    ws.write(fila, col + 17, razon)
                    ws.write(fila, col + 18, observacion)
                    ws.write(fila, col + 19, seinscribira)
                    ws.write(fila, col + 20, f_posible)
                    try:
                        if gestion:
                            gestion=elimina_tildes(gestion)
                        else:
                            gestion='NO TIENE GESTION'
                    except Exception as ex:
                            pass
                            gestion='NO TIENE GESTION'
                    ws.write(fila, col + 21, gestion)

                    if c.conduccion:
                        ws.write(fila, col + 22, str("SI"))
                    else:
                        ws.write(fila, col + 22, str("NO"))

                    fila = fila + 1
                cont = fila + 3

                ws.write(cont, 0, "Fecha Impresion", subtitulo)
                ws.write(cont, 2, str(datetime.now()), subtitulo)
                cont = cont + 1
                ws.write(cont, 0, "Usuario", subtitulo)
                ws.write(cont, 2, str(request.user), subtitulo)

                nombre = 'referido' + str(datetime.now()).replace(" ", "").replace(".", "").replace(":",
                                                                                                                "") + '.xls'
                carpeta = MEDIA_ROOT + '/reportes_excel/'
                try:
                    os.makedirs(carpeta)
                except:
                    pass
                wb.save(carpeta + nombre)

                return HttpResponse(
                    json.dumps({"result": "ok", "url": "/media/reportes_excel/" + nombre}),content_type="application/json")

            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}),content_type="application/json")


        elif action=='ver_gestionreferido':
            referidos = ReferidosInscripcion.objects.get(pk=request.POST['idpreregistro'])
            if referidos.online==False:
                    if referidos.conduccion==True:
                        datos = requests.get('https://crmcondu.itb.edu.ec/funciones',params={'a': 'vergestion','idprospecto':str(referidos.idprospecto)},verify=False)
                    else:
                        datos = requests.get('https://crm.itb.edu.ec/api',params={'a': 'vergestion','idprospecto':str(referidos.idprospecto)},verify=False)
            else:
                datos = requests.get('https://sgaonline.itb.edu.ec/funciones',params={'a': 'vergestion','idprospecto':str(referidos.idprospecto)},verify=False)

            if datos.status_code == 200:
                datos=datos.json()
                if datos['result']=='ok':
                    listahistorial= datos['listahistorial']

                    if len(listahistorial)>0:

                        return HttpResponse(json.dumps(datos),content_type="application/json")

                    else:
                       return HttpResponse(json.dumps({'result': 'bad', 'message': str('NO TIENE GESTION')}),content_type="application/json")

                    return HttpResponse(json.dumps({'result': 'ok'}),content_type="application/json")
                else:
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(datos['message'])}),content_type="application/json")
            else:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str("Error al conectar con el CRM ITB")}),content_type="application/json")

        elif action == 'generar_reporte2':
            try:
                data = {'title': ''}
                general=0
                print(request.POST)
                administrativo=None
                if request.POST['esadmin']=='1':
                    if Persona.objects.filter(pk=request.POST['administrativo']).exists():
                        administrativo = Persona.objects.get(pk=request.POST['administrativo'])
                        referidos = ReferidosInscripcion.objects.filter(administrativo=administrativo,activo=True).order_by('fecha','inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')
                        if User.objects.filter(pk=administrativo.usuario.id, groups__id=146,is_active=True):
                            tipopersona='VENTAS EXTERNAS 2'
                        else:
                            tipo_persona = 'ADMINISTRATIVO'
                    nombre = administrativo
                else:
                    if request.POST['inscripcion']!='':
                        inscripcion = Inscripcion.objects.get(pk=request.POST['inscripcion'])
                        referidos = ReferidosInscripcion.objects.filter(inscripcion=inscripcion,activo=True).order_by('fecha','inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')
                        tipo_persona = 'ALUMNO'
                        nombre = inscripcion.persona
                    else:
                        referidos = ReferidosInscripcion.objects.filter(activo=True).order_by('fecha','inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')
                        tipo_persona=''
                        nombre=''
                        general=1


                titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                titulo.font.height = 20 * 11
                subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                subtitulo.font.height = 20 * 10
                wb = xlwt.Workbook()
                ws = wb.add_sheet('Referidos', cell_overwrite_ok=True)

                fila = 8
                col = 0

                if request.POST['rangofechas']=='1':
                    referidos = referidos.filter(fecha__gte=convertir_fecha(request.POST['fechainicio']), fecha__lte=convertir_fecha(request.POST['fechafinal']))
                    ws.write(6, 0 , "FECHA",titulo)
                    ws.write(6, 1, 'Del '+str(convertir_fecha(request.POST['fechainicio']))+' al '+str(convertir_fecha(request.POST['fechafinal'])))
                    fila = 9

                ws.write(0, 1, 'INSTITUTO TECNOLOGICO BOLIVARIANO', titulo)
                ws.write(1, 1, 'LISTADO DE REFERIDOS (PERSONAS QUE COMISIONAN)', titulo)

                if general!=1:
                    ws.write(3, 0 , "PERSONA QUE REFIERE (COMISIONA)",titulo)
                    ws.write(3, 1, str(tipo_persona))
                    ws.write(4, 0 , "TIPO PERSONA",titulo)
                    ws.write(4, 1, str(nombre))
                    ws.write(5, 0 , "# REFERIDOS",titulo)
                    ws.write(5, 1, str(referidos.count()))

                ws.write(fila - 1, col , "FECHA REGISTRO",titulo)
                ws.write(fila - 1, col + 1, "NOMBRES",titulo)
                ws.write(fila - 1, col + 2, "CEDULA", titulo)
                ws.write(fila - 1, col + 3, "TELEFONO", titulo)
                ws.write(fila - 1, col + 4, "TELEFONO CONVENCIONAL", titulo)
                ws.write(fila - 1, col + 5, "EMAIL", titulo)
                ws.write(fila - 1, col + 6, "VENDEDOR", titulo)
                ws.write(fila - 1, col + 7, "INSCRIPCION PAGADA	", titulo)
                ws.write(fila - 1, col + 8, "MATRICULA PAGADA", titulo)
                ws.write(fila - 1, col + 9, "PAGO DE COMISION", titulo)
                ws.write(fila - 1, col + 10, "ONLINE", titulo)
                ws.write(fila - 1, col + 11, "ESTADO", titulo)
                ws.write(fila - 1, col + 12, "PAGO APROBADO", titulo)
                ws.write(fila - 1, col + 13, "CARRERA", titulo)
                ws.write(fila - 1, col + 14, "EFECTIVO", titulo)
                ws.write(fila - 1, col + 15, "RAZON ESTADO", titulo)
                ws.write(fila - 1, col + 16, "OBSERVACION", titulo)
                ws.write(fila - 1, col + 17, "SE INSCRIBIRA", titulo)
                ws.write(fila - 1, col + 18, "F POSIBLE INSCRIPCION", titulo)
                ws.write(fila - 1, col + 19, "GESTOR", titulo)
                ws.write(fila - 1, col + 20, "CONDUCCION", titulo)
                if general==1:
                    ws.write(fila-1,col+21 , "PERSONA QUE REFIERE (COMISIONA)",titulo)
                    ws.write(fila-1,col+22 , "TIPO PERSONA",titulo)

                c=''
                for c in referidos:
                    carrera=''
                    gestion=''
                    efectivo=''
                    razon=''
                    observacion=''
                    seinscribira=''
                    f_posible=''
                    tipopersona=''
                    if c.online==False:
                        if c.conduccion==True:
                            datos = requests.get('https://crmcondu.itb.edu.ec/funciones',params={'a': 'vergestion','idprospecto':str(c.idprospecto)},verify=False)
                        else:
                            datos = requests.get('https://crm.itb.edu.ec/api',params={'a': 'vergestion','idprospecto':str(c.idprospecto)},verify=False)
                    else:
                        datos = requests.get('https://sgaonline.itb.edu.ec/funciones',params={'a': 'vergestion','idprospecto':str(c.idprospecto)},verify=False)

                    if datos.status_code == 200:
                        datos=datos.json()
                        if datos['result']=='ok':
                            listahistorial= datos['listahistorial']
                            if len(listahistorial)>0:
                                efectivo=elimina_tildes(listahistorial[0]['efectivo'])
                                razon=elimina_tildes(listahistorial[0]['razonestado'])
                                observacion=elimina_tildes(listahistorial[0]['observacion'])
                                if listahistorial[0]['inscripcion']:
                                    seinscribira="Si"
                                else:
                                    seinscribira="No"
                                f_posible=str(listahistorial[0]['fechainscripcion'])
                                gestion=listahistorial[0]['gestor']
                            else:
                                if len(listahistorial)==0:
                                    gestion='NO TIENE GESTION'

                    ws.write(fila, col,  str(c.fecha))
                    ws.write(fila, col + 1,  elimina_tildes(c.apellido1)+" "+elimina_tildes(c.apellido2)+" "+elimina_tildes(c.nombres))
                    ws.write(fila, col + 2, c.cedula)
                    ws.write(fila, col + 3, c.telefono)
                    ws.write(fila, col + 4, c.telefono_conv)
                    ws.write(fila, col + 5, c.email)

                    if c.online:
                       ws.write(fila, col + 6, elimina_tildes(c.verficarNombreVendedor()))
                    else:
                       if c.conduccion==True:
                            ws.write(fila, col + 6, elimina_tildes(c.verficarNombreVendedorConduccion()))
                       else:
                            ws.write(fila, col + 6, elimina_tildes(c.verficarNombreVendedor().nombre_completo()) if c.verficarNombreVendedor() else '')

                    if c.online:
                        if c.verificar_inscrip_online():
                            ws.write(fila, col + 7, str("SI"))
                        else:
                            ws.write(fila, col + 7, str("NO"))
                    else:
                        if c.conduccion==True:
                            if c.verificar_inscrip_conduccion():
                                ws.write(fila, col + 7, str("SI"))
                            else:
                                ws.write(fila, col + 7, str("NO"))

                        else:
                            if c.inscrito:
                                ws.write(fila, col + 7, str("SI"))
                            else:
                                ws.write(fila, col + 7, str("NO"))

                    if c.online:
                        if c.verificar_pago_online():
                            ws.write(fila, col + 8, str("SI"))
                        else:
                            ws.write(fila, col + 8, str("NO"))
                    else:
                        if c.conduccion==True:

                            if c.verificar_pago_conduccion():
                                ws.write(fila, col + 8, str("SI"))
                            else:
                                ws.write(fila, col + 8, str("NO"))

                        else:
                            if c.verificar_pago_matricula():
                                ws.write(fila, col + 8, str("SI"))
                            else:
                                ws.write(fila, col + 8, str("NO"))

                    if c.pagocomision:
                        ws.write(fila, col + 9, str("SI"))
                    else:
                        ws.write(fila, col + 9, str("NO"))

                    if c.online:
                        ws.write(fila, col + 10, str("SI"))
                    else:
                        ws.write(fila, col + 10, str("NO"))

                    if c.activo:
                        ws.write(fila, col + 11, str("SI"))
                    else:
                        ws.write(fila, col + 11, str("NO"))

                    if c.aprobado_pago:
                        ws.write(fila, col + 12, str("SI"))
                    else:
                        ws.write(fila, col + 12, str("NO"))

                    try:
                        if c.carrera.nombre:
                            carrera=elimina_tildes(c.carrera.nombre)
                        else:
                            carrera='NO TIENE CARRERA'

                    except Exception as ex:
                            pass
                            carrera='NO TIENE CARRERA'
                    ws.write(fila, col + 13,  carrera)



                    ws.write(fila, col + 14, efectivo)
                    ws.write(fila, col + 15, razon)
                    ws.write(fila, col + 16, observacion)
                    ws.write(fila, col + 17, seinscribira)
                    ws.write(fila, col + 18, f_posible)
                    try:
                        if gestion:
                            gestion=elimina_tildes(gestion)
                        else:
                            gestion='NO TIENE GESTION'
                    except Exception as ex:
                            pass
                            gestion='NO TIENE GESTION'
                    ws.write(fila, col + 19, gestion)

                    if c.conduccion:
                        ws.write(fila, col + 20, str("SI"))
                    else:
                        ws.write(fila, col + 20, str("NO"))

                    if general==1:
                        referidopor=''
                        if c.administrativo:
                            if Persona.objects.filter(pk=c.administrativo.id).exists():
                                referidopor=Persona.objects.filter(pk=c.administrativo.id)[:1].get()
                                if User.objects.filter(pk=referidopor.usuario.id, groups__id=146,is_active=True):
                                    tipopersona='VENTAS EXTERNAS 2'
                                else:
                                    tipopersona = 'ADMINISTRATIVO'
                        else:
                            if c.inscripcion:
                                if Persona.objects.filter(pk=c.inscripcion.persona.id).exists():
                                    referidopor=Persona.objects.filter(pk=c.inscripcion.persona.id)[:1].get()
                                    tipopersona = 'ESTUDIANTE'

                        ws.write(fila, col + 21, elimina_tildes(referidopor.nombre_completo_inverso()))
                        ws.write(fila, col + 22, tipopersona)


                    fila = fila + 1
                cont = fila + 3

                ws.write(cont, 0, "Fecha Impresion", subtitulo)
                ws.write(cont, 2, str(datetime.now()), subtitulo)
                cont = cont + 1
                ws.write(cont, 0, "Usuario", subtitulo)
                ws.write(cont, 2, str(request.user), subtitulo)

                nombre = 'referido' + str(datetime.now()).replace(" ", "").replace(".", "").replace(":",
                                                                                                                "") + '.xls'
                carpeta = MEDIA_ROOT + '/reportes_excel/'
                try:
                    os.makedirs(carpeta)
                except:
                    pass
                wb.save(carpeta + nombre)

                return HttpResponse(json.dumps({"result": "ok", "url": "/media/reportes_excel/" + nombre}),content_type="application/json")

            except Exception as e:
                print(e)
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}),content_type="application/json")

    else:
        data = {'title': 'Listado de Referidos'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='add':
                data['inscripcion'] = Inscripcion.objects.get(persona=data['persona'])
                data['form'] = InscripcionReferidoForm()
                data['form'].cargarcarrera()
                # i = Inscripcion.objects.get(persona=request['persona'])
                return render(request ,"alu_referidos/adicionarbs.html" ,  data)

            if action=='editar':
                if Inscripcion.objects.filter(persona=data['persona']).exists():
                    data['inscripcion'] = Inscripcion.objects.get(persona=data['persona'])
                else:
                    data['administrativo'] = Persona.objects.get(persona=data['persona'])
                r = ReferidosInscripcion.objects.get(pk=request.GET['id'])
                initial = model_to_dict(r)
                initial.update({'extranjero': r.extranjero})
                referidos = InscripcionReferidoForm(initial=initial)
                data['form'] =referidos
                data['form'].cargarcarrera()
                data['ref']=r
                return render(request ,"alu_referidos/adicionarbs.html" ,  data)

            elif action=='eliminar_referido':
                referidos = ReferidosInscripcion.objects.get(pk=request.GET['id'])
                if referidos.online==False:
                    datos = requests.get('https://crm.itb.edu.ec/api',params={'a': 'eliminareferido','idprospecto':str(referidos.idprospecto)},verify=False)
                else:
                    datos = requests.get('https://sgaonline.itb.edu.ec/funciones',params={'a': 'eliminareferido','idprospecto':str(referidos.idprospecto)},verify=False)

                if datos.status_code == 200:
                  datos=datos.json()
                  if datos['result']=='ok':
                    referidos.delete()
                    client_address = ip_client_address(request)

                    #Log de ADICIONAR INSCRIPCION
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(referidos).pk,
                        object_id       = referidos.id,
                        object_repr     = force_str(referidos),
                        action_flag     = DELETION,
                        change_message  = 'REFERIDO ELIMINADO (' + client_address + ')' )


                    referidos.correo_referido_eliminado(request.user,'SE ELIMINO REFERIDO')

                    return HttpResponseRedirect("/referidos")
                  else:
                    return HttpResponseRedirect("/referidos?info="+datos['message'])
                else:
                  return HttpResponseRedirect("/referidos?info="+"Error al conectar con el CRM ITB")

        else:
            try:
                hoy = str(datetime.date(datetime.now()))
                search = None
                todos = None
                activos = None
                inactivos = None

                if 'info' in request.GET:
                    data['error'] = 1
                    data['info'] = request.GET['info']
                else:
                    data['error'] = 0

                if 's' in request.GET:
                    search = request.GET['s']

                if 't' in request.GET:
                    todos = request.GET['t']
                if search:
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')
                    if len(ss)==1:
                        referidos = ReferidosInscripcion.objects.filter(Q(inscripcionref__persona__nombres__icontains=search) | Q(inscripcionref__persona__apellido1__icontains=search) | Q(inscripcionref__persona__apellido2__icontains=search) | Q(inscripcionref__persona__cedula__icontains=search) |
                            Q(inscripcion__persona__nombres__icontains=search) | Q(inscripcion__persona__apellido1__icontains=search) | Q(inscripcion__persona__apellido2__icontains=search) | Q(inscripcion__persona__cedula__icontains=search) | Q(administrativo__nombres__icontains=search) | Q(administrativo__apellido1__icontains=search) | Q(administrativo__apellido2__icontains=search) | Q(administrativo__cedula__icontains=search) ,activo=True).order_by('-fecha','inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres','administrativo__apellido1','administrativo__apellido2','administrativo__nombres')
                        if (len(referidos)==0):
                           referidos = ReferidosInscripcion.objects.filter(Q(administrativo__nombres__icontains=search) | Q(administrativo__apellido1__icontains=search) | Q(administrativo__apellido2__icontains=search) | Q(administrativo__cedula__icontains=search),activo=True).order_by('-fecha','administrativo__apellido1','administrativo__apellido2','administrativo__nombres')

                        if (len(referidos)==0):
                           referidos = ReferidosInscripcion.objects.filter(cedula=search,activo=True)

                    else:
                        referidos = ReferidosInscripcion.objects.filter(Q(inscripcionref__persona__nombres__icontains=search) | Q(inscripcionref__persona__apellido1__icontains=ss[0]) | Q(inscripcionref__persona__apellido2__icontains=ss[0]) | Q(inscripcionref__persona__cedula__icontains=search) |
                            Q(inscripcion__persona__nombres__icontains=search) | Q(inscripcion__persona__apellido1__icontains=ss[0]) | Q(inscripcion__persona__apellido2__icontains=ss[1]) | Q(inscripcion__persona__cedula__icontains=search) | Q(administrativo__nombres__icontains=search) | Q(administrativo__apellido1__icontains=ss[0]) | Q(administrativo__apellido2__icontains=ss[1]) | Q(administrativo__cedula__icontains=search) ,activo=True).order_by('-fecha','inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres','administrativo__apellido1','administrativo__apellido2','administrativo__nombres')
                        if (len(referidos)==0):
                           referidos = ReferidosInscripcion.objects.filter(Q(administrativo__nombres__icontains=search) | Q(administrativo__apellido1__icontains=search) | Q(administrativo__apellido2__icontains=search) | Q(administrativo__cedula__icontains=search),activo=True).order_by('-fecha','administrativo__apellido1','administrativo__apellido2','administrativo__nombres')

                else:
                    referidos = ReferidosInscripcion.objects.filter(activo=True).order_by('-fecha','inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')



                paging = MiPaginador(referidos, 30)
                p = 1
                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                    page = paging.page(p)
                except:
                    page = paging.page(1)

                data['paging'] = paging
                data['rangospaging'] = paging.rangos_paginado(p)
                data['formestd'] = RangoReferidoForm(initial={'inicio': datetime.now().date(),'fin': datetime.now().date()})
                data['form_comisiona'] = RangoReferidoComisionaForm(initial={'finicio': datetime.now().date(),'ffin': datetime.now().date()})
                data['page'] = page
                data['search'] = search if search else ""
                data['referidos'] = page.object_list
                if LugarRecaudacion.objects.filter(persona=data['persona'],activa=True).exists():
                    data['caja'] = LugarRecaudacion.objects.filter(persona=data['persona'],activa=True)[:1].get()
                    #Para los cajeros que tengan sesion de caja abierta
                    if SesionCaja.objects.filter(caja=data['caja'], abierta=True).exists():
                        sesion = SesionCaja.objects.get(caja=data['caja'], abierta=True)
                        data['sesion'] = sesion

                return render(request ,"alu_referidos/referidos.html" ,  data)

            except Exception as e:
                print(e)
                return HttpResponseRedirect("/?info="+str(e))