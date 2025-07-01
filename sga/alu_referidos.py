import csv
from datetime import datetime,timedelta
import json
import xlwt
from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator

from django.db import transaction
from django.db.models.query_utils import Q
from django.forms.models import model_to_dict
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.utils.encoding import force_str
from django.template import RequestContext

import psycopg2
import requests


from settings import CENTRO_EXTERNO, RUBRO_TIPO_OTRO_MODULO_INTERNO, RUBRO_TIPO_OTRO_INSCRIPCION, DEFAULT_PASSWORD, PROFESORES_GROUP_ID, ALUMNOS_GROUP_ID, UTILIZA_GRUPOS_ALUMNOS, REPORTE_CERTIFICADO_INSCRIPCION, EMAIL_ACTIVE, EVALUACION_ITB, REGISTRO_HISTORIA_NOTAS, NOTA_ESTADO_EN_CURSO, GENERAR_RUBROS_PAGO, GENERAR_RUBRO_INSCRIPCION, GENERAR_RUBRO_INSCRIPCION_MARGEN_DIAS, MODELO_EVALUACION, EVALUACION_IAVQ, EVALUACION_ITS, UTILIZA_NIVEL0_PROPEDEUTICO, TIPO_PERIODO_PROPEDEUTICO, NOTA_ESTADO_APROBADO, UTILIZA_FICHA_MEDICA, EVALUACION_TES, CORREO_INSTITUCIONAL, USA_CORREO_INSTITUCIONAL, INSCRIPCION_CONDUCCION,TIPO_AYUDA_FINANCIERA, URL_PRE_INSCRIPCION, RUTA_PRE_INSCRIPCION, CARRERAS_ID_EXCLUIDAS_INEC,VALOR_COMISION_REFERIDO, CAJA_REFERIDO, FACTURACION_ELECTRONICA, ID_VENTA_EXTERNA2,MEDIA_ROOT, SEGMENTO_REFERIDO_ONLINE, SEGMENTO_REFERIDO
from sga.commonviews import addUserData, ip_client_address
from sga.facturacionelectronica import mail_errores_autorizacion

from sga.forms import PersonaForm, InscripcionForm, RecordAcademicoForm, HistoricoRecordAcademicoForm, HistoriaNivelesDeInscripcionForm, CargarFotoForm, EmpresaInscripcionForm, EstudioInscripcionForm, DocumentoInscripcionForm, ActividadesInscripcionForm, PadreClaveForm, ConvalidacionInscripcionForm, HistoricoNotasITBForm, GraduadoDatosForm, EgresadoForm, InscripcionSenescytForm, RetiradoMatriculaForm, InscripcionCextForm, BecarioForm, InscripcionPracticaForm, ObservacionInscripcionForm, ProcesoDobeForm,  ActivaInactivaUsuarioForm, MatriculaBecaForm,InscripcionCextForm, InscripcionReferidoForm,RangoFacturasForm
from sga.models import Profesor, ProcesoDobe, Persona, Inscripcion, RecordAcademico, DocumentosDeInscripcion, HistoricoRecordAcademico, HistoriaNivelesDeInscripcion, FotoPersona, EmpresaInscripcion, EstudioInscripcion, DocumentoInscripcion, Archivo, TipoArchivo, Grupo, InscripcionGrupo, PerfilInscripcion, HistoricoNotasITB, PadreClave, Malla, ConvalidacionInscripcion, TipoEstado, Rubro, RubroInscripcion, NivelMalla, EjeFormativo, AsignaturaMalla, Egresado, Asignatura, InscripcionSenescyt, RetiradoMatricula, Carrera, Modalidad, Sesion, Especialidad, Materia, Nivel, TipoOtroRubro, Matricula, MateriaAsignada, RubroOtro, Graduado, InscripcionBecario, InscripcionPracticas,\
    ObservacionInscripcion, InscripcionConduccion, InactivaActivaUsr, PreInscripcion, Sede, Sexo,Canton,Provincia,ReferidosInscripcion, DescuentoReferido, InscripcionDescuentoRef, elimina_tildes, ClienteFactura, Factura, Pago, LugarRecaudacion, ReciboCajaInstitucion, ViewCrmReferidos, convertir_fecha,TituloInstitucion, RubroMatricula
from sga.tasks import gen_passwd
from decimal import Decimal

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

        elif action=='aplicar':
            sid = transaction.savepoint()
            try:
                inscripcion = Inscripcion.objects.get(persona__usuario=request.user)
                referidos = ReferidosInscripcion.objects.filter(activo=True,inscripcion=inscripcion,pagocomision=False,aprobado_pago=True)
                valorrecibo=0
                from sga.api import abrir_caja
                valor = referidos.count() * VALOR_COMISION_REFERIDO
                while valor > 0:
                    if not Rubro.objects.filter(inscripcion=inscripcion,cancelado=False).order_by('fechavence').exists():
                        valorrecibo = valor
                        valor = 0
                    else:
                        for r  in  Rubro.objects.filter(inscripcion=inscripcion,cancelado=False).order_by('fechavence'):
                            if valor == 0:
                                break
                            if r.adeudado() > valor:
                                valpago= valor
                            else:
                                valpago = r.adeudado()
                            valor = valor - valpago

                            if abrir_caja(CAJA_REFERIDO):
                                if inscripcion.persona.cedula:
                                    ruc =  inscripcion.persona.cedula
                                else:
                                    ruc =  inscripcion.persona.pasaporte
                                caja = abrir_caja(CAJA_REFERIDO)
                                try:

                                    cliente = ClienteFactura.objects.filter(ruc=ruc)[:1].get()
                                    cliente.nombre =elimina_tildes(inscripcion.persona.nombre_completo())
                                    cliente.direccion =elimina_tildes(inscripcion.persona.direccion)
                                    cliente.telefono =inscripcion.persona.telefono
                                    cliente.correo =inscripcion.persona.email
                                    if cliente.contrasena == None:
                                        cliente.contrasena =inscripcion.persona.cedula
                                        cliente.numcambio = 0
                                    cliente.save()
                                except :
                                    cliente = ClienteFactura(ruc=ruc, nombre=elimina_tildes(inscripcion.persona.nombre_completo()),
                                        direccion=elimina_tildes(inscripcion.persona.direccion), telefono= inscripcion.persona.telefono,
                                        correo=inscripcion.persona.email,contrasena=inscripcion.persona.cedula,numcambio=0)
                                    cliente.save()

                                if not Factura.objects.filter(numero=caja.caja.puntoventa.strip()+"-"+str(caja.caja.numerofact).zfill(9)).exists():
                                    factura = Factura(numero = caja.caja.puntoventa.strip()+"-"+str(caja.caja.numerofact).zfill(9), fecha = datetime.now().date(),
                                                            valida = True, cliente = cliente,hora = datetime.now().time(),
                                                            subtotal =valpago , iva = 0, total = valpago,
                                                            impresa=False, caja=caja.caja, estado = '', mensaje = '',dirfactura='')
                                    factura.save()


                                    pago2 = Pago(fecha=datetime.now().date(),
                                                            recibe=caja.caja.persona,
                                                            valor=valpago,
                                                            rubro=r,
                                                            efectivo=False,
                                                            wester=False,
                                                            sesion=caja,
                                                            electronico=False,
                                                            facilito=False,
                                                            referido=True)
                                    pago2.save()

                                    factura.pagos.add(pago2)
                                    if r.adeudado()==0:
                                        r.cancelado = True
                                        r.save()

                                    caja.facturatermina= int(caja.caja.numerofact)+1
                                    caja.save()

                                    if FACTURACION_ELECTRONICA or caja.caja.numerofact  != None:
                                        for luga in LugarRecaudacion.objects.all():
                                            if luga.puntoventa == caja.caja.puntoventa:
                                                luga.numerofact = int(caja.caja.numerofact)+1
                                                luga.save()
                                    client_address = ip_client_address(request)

                                    # Log de CREACION DE NOTA DE CREDITO INSTITUCIONAL
                                    LogEntry.objects.log_action(
                                        # user_id         = request.user.pk,
                                        user_id         = caja.caja.persona.usuario.pk,
                                        content_type_id = ContentType.objects.get_for_model(factura).pk,
                                        object_id       = factura.id,
                                        object_repr     = force_str(factura),
                                        action_flag     = ADDITION,
                                        change_message  = 'Adicionada Factura Pago - Referido '+  ' (' + client_address + ')' )
                                    try:
                                        if Factura.objects.filter(numero= factura.numero).count()>1:
                                            mail_errores_autorizacion("FACTURA REPETIDA "+DEFAULT_PASSWORD,"Existe mas de una factura repetida verificar en factura PAGO ONLINE",factura.numero)
                                            transaction.savepoint_rollback(sid)
                                            continue

                                        for referidos in ReferidosInscripcion.objects.filter(activo=True,inscripcion=inscripcion,pagocomision=False,aprobado_pago=True):
                                            referidos.pagocomision=True
                                            referidos.valorpago=Decimal(VALOR_COMISION_REFERIDO)
                                            referidos.fechapago=datetime.now()
                                            referidos.observacion='PAGO CRUZADO AUTOMATICAMENTE'
                                            referidos.sesioncaja=caja
                                            referidos.save()


                                        # factura.notificacion_pago_online(rubro)
                                    except Exception as ex:
                                        print(ex)
                                        transaction.savepoint_rollback(sid)

                            else:
                                transaction.savepoint_rollback(sid)
                                print("Erro")
                                return HttpResponse(json.dumps({'result':'bad'}), content_type="application/json")
                                # errores.append(('Factura Repetida' ,d['ci']))
                                # email_error_pagoonline(errores,'ONLINE')
                                # return HttpResponse(json.dumps({'codigo':0,'mensaje':'Factura Repetida'}),content_type="application/json")


                client_address = ip_client_address(request)

                # Log de ADICIONAR RECORD
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(inscripcion).pk,
                    object_id       = inscripcion.id,
                    object_repr     = force_str(inscripcion),
                    action_flag     = ADDITION,
                    change_message  = 'Aplicado Pago Referido (' + client_address + ')' )
                if valorrecibo > 0:
                    rc = ReciboCajaInstitucion(inscripcion=inscripcion,
                                               motivo='RECIBO GENERADO POR PAGO COMISION',
                                               sesioncaja=abrir_caja(CAJA_REFERIDO),
                                               fecha=datetime.now().date(),
                                               hora=datetime.now().time(),
                                               valorinicial = float(valorrecibo),
                                               saldo=float(valorrecibo))
                    rc.save()
                    caja = abrir_caja(CAJA_REFERIDO)
                    for referidos in ReferidosInscripcion.objects.filter(activo=True,inscripcion=inscripcion,pagocomision=False,aprobado_pago=True):

                        referidos.pagocomision=True
                        referidos.valorpago=Decimal(VALOR_COMISION_REFERIDO)
                        referidos.fechapago=datetime.now()
                        referidos.observacion='PAGO CRUZADO AUTOMATICAMENTE'
                        referidos.sesioncaja=caja
                        referidos.save()
                transaction.savepoint_commit(sid)


                return HttpResponse(json.dumps({'result':'ok'}), content_type="application/json")
            except Exception as e:

                transaction.savepoint_rollback(sid)
                return HttpResponse(json.dumps({'result':'bad'}), content_type="application/json")

        elif action == 'buscar':
            cedula = request.POST['cedula']
            try:
                if cedula:

                    if Persona.objects.filter(cedula=cedula).exists():
                       return HttpResponse(json.dumps({'result':'bad', 'mensaje':"Persona ya encuentra registrada"}),content_type='application/json')

                    if Persona.objects.filter(pasaporte=cedula).exists():
                       return HttpResponse(json.dumps({'result':'bad', 'mensaje':"Persona ya encuentra registrada"}),content_type='application/json')

                    if Inscripcion.objects.filter(persona__cedula=cedula).exclude(carrera__in=CARRERAS_ID_EXCLUIDAS_INEC).exists():
                        return HttpResponse(json.dumps({'result':'bad', 'mensaje':"Persona ya encuentra inscrita"}),content_type='application/json')

                    elif ReferidosInscripcion.objects.filter(cedula=cedula).exists():
                        return HttpResponse(json.dumps({'result':'bad', 'mensaje':"Persona ya encuentra referida"}),content_type='application/json')
                    else:

                        # return HttpResponse(json.dumps({'result':'ok'}), content_type='application/json')

                        datos = requests.get('https://crm.itb.edu.ec/api',params={'a': 'verificarprospecto','identificacion':request.POST['cedula']},verify=False)

                        if datos.status_code == 200:
                          datos=datos.json()
                          if datos['result']=='bad':
                             return HttpResponse(json.dumps({'result': 'bad', 'mensaje': str(datos['message'])}),
                                        content_type='application/json')


                        datos = requests.get('https://sgaonline.itb.edu.ec/funciones',params={'a': 'verificarprospecto','identificacion':request.POST['cedula']},verify=False)

                        if datos.status_code == 200:
                          datos=datos.json()
                          if datos['result']=='bad':
                             return HttpResponse(json.dumps({'result': 'bad', 'mensaje': str(datos['message'])}),
                                        content_type='application/json')

                        return HttpResponse(json.dumps({'result':'ok'}), content_type='application/json')
            except requests.Timeout:
                print("Error Timeout")
                return HttpResponse(json.dumps({"result": "Error por Timeout"}), content_type="application/json")
            except requests.ConnectionError:
                print("Error Conexion")
                return HttpResponse(json.dumps({"result": "Error de conexion"}), content_type="application/json")

        elif action== 'buscarcarreraonline':
            try:
                 data={}
                 # cn = psycopg2.connect("host=localhost dbname=sgaprueba user=postgres password=postgres")
                 cn = psycopg2.connect("host=10.10.9.45 dbname=sgaonline user=aok password=R0b3rt0.1tb$")
                 cur = cn.cursor()
                 cur.execute("select * from view_carreraonline")
                 dato = cur.fetchall()
                 lista=[]
                 # if cur:
                 cur.fetchall()
                 #names = [row[0] for row in cursor.fetchall()]
                 cur.close()
                 for row in dato:
                    rowid=row[0]
                    rownombre=row[1]
                    lista.append({'id':row[0],'nombre':row[1]})

                 data['lista'] = lista
                 data['result'] = 'ok'
                 return HttpResponse(json.dumps(data), content_type="application/json")

            except Exception as e:
                return HttpResponse(json.dumps({'result':'bad','mensaje':str(e)}), content_type="application/json")

        elif action=='ver_gestionreferido':
                referidos = ReferidosInscripcion.objects.get(pk=int(request.POST['idpreregistro']))
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

                        return HttpResponse(json.dumps(datos),
                                    content_type="application/json")

                    else:
                       return HttpResponse(json.dumps({'result': 'bad', 'message': str('NO TIENE GESTION')}),
                                    content_type="application/json")



                    return HttpResponse(json.dumps({'result': 'ok'}),
                                    content_type="application/json")
                  else:
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(datos['message'])}),
                                    content_type="application/json")
                else:
                  return HttpResponse(json.dumps({'result': 'bad', 'message': str("Error al conectar con el CRM ITB")}),
                                    content_type="application/json")

        elif action =='add':
            f = InscripcionReferidoForm(request.POST)
            if f.is_valid():
                pass
            try:
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
                    referidos.carrera=f.cleaned_data['carrera'] if f.cleaned_data['online']==False else None
                    referidos.online=True if f.cleaned_data['online']==True else False
                    referidos.carreraonline=f.cleaned_data['carreraonline'] if f.cleaned_data['online']==True else 0
                    referidos.modalidad=f.cleaned_data['modalidad'] if f.cleaned_data['online']==False else None
                    referidos.conduccion=True if f.cleaned_data['conduccion']==True else False
                    referidos.tipolicencia=f.cleaned_data['tipolicencia'] if f.cleaned_data['conduccion']==True else 0


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
                                                     carrera=f.cleaned_data['carrera'] if f.cleaned_data['online']==False else None,
                                                     modalidad=f.cleaned_data['modalidad'] if f.cleaned_data['online']==False else None,
                                                     online = True if f.cleaned_data['online']==True else False,
                                                     carreraonline=f.cleaned_data['carreraonline'] if f.cleaned_data['online']==True else 0,
                                                     conduccion=True if f.cleaned_data['conduccion']==True else False,
                                                     tipolicencia=f.cleaned_data['tipolicencia'] if f.cleaned_data['conduccion']==True else None,
                                                     )


                if 'ref' in request.POST:


                  try:

                     if f.cleaned_data['conduccion']==False:
                          if f.cleaned_data['online']==True:
                                datos = requests.get('https://sgaonline.itb.edu.ec/funciones',params={'a': 'editarreferido','idprospecto':str(referidos.idprospecto),
                                    'cedula': referidos.cedula if referidos.extranjero==False else referidos.pasaporte,
                                    'nombres':elimina_tildes(referidos.nombres),'apellido1':elimina_tildes(referidos.apellido1),
                                    'apellido2':elimina_tildes(referidos.apellido2),
                                    'extranjero':str(referidos.extranjero),'idsexo':str(referidos.sexo.id),'telefono':str(referidos.telefono_conv),'celular':str(referidos.telefono),'correo':str(f.cleaned_data['email']),
                                    'idcarrera':str(f.cleaned_data['carreraonline'])},timeout=15,verify=False)
                          else:

                              datos = requests.get('https://crm.itb.edu.ec/api',params={'a': 'editarreferido','idprospecto':str(referidos.idprospecto),
                                    'cedula': referidos.cedula if referidos.extranjero==False else referidos.pasaporte,
                                    'nombres':elimina_tildes(referidos.nombres),'apellido1':elimina_tildes(referidos.apellido1),
                                    'apellido2':elimina_tildes(referidos.apellido2),
                                    'extranjero':str(referidos.extranjero),'idsexo':str(referidos.sexo.id),'telefono':str(referidos.telefono_conv),'celular':str(referidos.telefono),'correo':str(f.cleaned_data['email']),
                                    'idcarrera':str(f.cleaned_data['carrera'].id),'idmodalidad':str(f.cleaned_data['modalidad'].id)},timeout=15,verify=False)
                     else:
                        datos = requests.get('https://crmcondu.itb.edu.ec/funciones',params={'a': 'editarreferido','idprospecto':str(referidos.idprospecto),
                                    'cedula': str(f.cleaned_data['cedula']) if f.cleaned_data['extranjero']==False else str(f.cleaned_data['pasaporte']),
                                    'nombres':elimina_tildes(f.cleaned_data['nombres']),'apellido1':elimina_tildes(f.cleaned_data['apellido1']),
                                    'apellido2':elimina_tildes(f.cleaned_data['apellido2']),
                                    'extranjero':f.cleaned_data['extranjero'],'idsexo':str(f.cleaned_data['sexo'].id),'telefono':str(f.cleaned_data['telefono_conv']),'celular':str(f.cleaned_data['telefono']),'correo':str(f.cleaned_data['email']),'usuario':str(request.user.id),'idcarrera':str(f.cleaned_data['tipolicencia']),'sgapresencial':'True','referidoventaexterna':'True'},timeout=15,verify=False)

                     if datos.status_code == 200:
                          datos=datos.json()
                          if datos['result']=='ok':
                            referidos.save()
                          else:
                           return HttpResponseRedirect("alu_referidos/?action=editar&id="+request.POST['ref']+"&info="+datos['message'])
                     else:
                        return HttpResponseRedirect("alu_referidos/?action=editar&id="+request.POST['ref']+"&info="+"Error al actualizar referido CRM ITB")

                  except requests.Timeout:
                    print("Error Timeout")
                    return HttpResponse(json.dumps({"result": "Error por Timeout"}), content_type="application/json")
                  except requests.ConnectionError:
                    print("Error Conexion")
                    return HttpResponse(json.dumps({"result": "Error de conexion"}), content_type="application/json")
                else:
                  try:
                       referidoventaexterna2=False
                       usuario = User.objects.get(pk=request.user.id)

                       if usuario.groups.filter(id__in=[ID_VENTA_EXTERNA2]).exists():
                           referidoventaexterna2=True

                       mensaje=''
                       if f.cleaned_data['conduccion']==False:
                           if f.cleaned_data['online']==True:
                               persona = Persona.objects.get(usuario__id=request.user.id)
                               mensaje='Online'

                               datos = requests.get('https://crm.itb.edu.ec/api',params={'a': 'verificarprospecto','identificacion': referidos.cedula if referidos.extranjero==False else referidos.pasaporte},timeout=15,verify=False)

                               if datos.status_code == 200:
                                    datos=datos.json()
                                    if datos['result']=='ok':
                                        pass
                                    else:
                                        return HttpResponseRedirect("alu_referidos/?action=add&info="+"Ya existe la identificacion en el CRM Presencial")

                               #  pregunto si no existe ese prospecto en el crm de conduccion


                               datos = requests.get('https://crmcondu.itb.edu.ec/exceldescar',params={'a': 'verificarprospecto','identificacion': referidos.cedula if referidos.extranjero==False else referidos.pasaporte},timeout=15,verify=False)

                               if datos.status_code == 200:
                                    datos=datos.json()
                                    if datos['result']=='ok':
                                        pass
                                    else:
                                        return HttpResponseRedirect("alu_referidos/?action=add&info="+"Ya existe la identificacion en el CRM CONDUCCION")

                               datos = requests.get('https://sgaonline.itb.edu.ec/funciones',params={'a': 'registrareferido',
                                    'cedula': str(f.cleaned_data['cedula']) if f.cleaned_data['extranjero']==False else str(f.cleaned_data['pasaporte']),
                                    'nombres':elimina_tildes(f.cleaned_data['nombres']),'apellido1':elimina_tildes(f.cleaned_data['apellido1']),
                                    'apellido2':elimina_tildes(f.cleaned_data['apellido2']),
                                    'extranjero':f.cleaned_data['extranjero'],'idsexo':str(f.cleaned_data['sexo'].id),'telefono':str(f.cleaned_data['telefono_conv']),'celular':str(f.cleaned_data['telefono']),'correo':str(f.cleaned_data['email']),'idpersona':str(persona.id),'idcarrera':str(f.cleaned_data['carreraonline']),'sgaonline':'True','referidoventaexterna':referidoventaexterna2,'conduccion':'False','segmento':SEGMENTO_REFERIDO_ONLINE},timeout=15,verify=False)

                           else:

                               datos = requests.get('https://sgaonline.itb.edu.ec/funciones',params={'a': 'verificarprospecto','identificacion': referidos.cedula if referidos.extranjero==False else referidos.pasaporte},timeout=15,verify=False)

                               if datos.status_code == 200:
                                    datos=datos.json()
                                    if datos['result']=='ok':
                                        pass
                                    else:
                                        return HttpResponseRedirect("alu_referidos/?action=add&info="+"Ya existe la identificacion en el CRM Online")

                               #  pregunto si no existe ese prospecto en el crm de conduccion
                               datos = requests.get('https://crmcondu.itb.edu.ec/exceldescar',params={'a': 'verificarprospecto','identificacion': referidos.cedula if referidos.extranjero==False else referidos.pasaporte},timeout=15,verify=False)


                               if datos.status_code == 200:
                                    datos=datos.json()
                                    if datos['result']=='ok':
                                        pass
                                    else:
                                        return HttpResponseRedirect("alu_referidos/?action=add&info="+"Ya existe la identificacion en el CRM CONDUCCION")

                               datos = requests.get('https://crm.itb.edu.ec/api',params={'a': 'registrareferido',
                                    'cedula': str(f.cleaned_data['cedula']) if f.cleaned_data['extranjero']==False else str(f.cleaned_data['pasaporte']),
                                    'nombres':elimina_tildes(f.cleaned_data['nombres']),'apellido1':elimina_tildes(f.cleaned_data['apellido1']),
                                    'apellido2':elimina_tildes(f.cleaned_data['apellido2']),
                                    'extranjero':f.cleaned_data['extranjero'],'idsexo':str(f.cleaned_data['sexo'].id),'telefono':str(f.cleaned_data['telefono_conv']),'celular':str(f.cleaned_data['telefono']),'correo':str(f.cleaned_data['email']),'usuario':str(request.user.id),'idcarrera':str(f.cleaned_data['carrera'].id),'idmodalidad':str(f.cleaned_data['modalidad'].id),'sgaonline':'False','referidoventaexterna':referidoventaexterna2,'conduccion':'False','segmento':SEGMENTO_REFERIDO},timeout=15,verify=False)
                       else:
                           persona = Persona.objects.get(usuario__id=request.user.id)
                           mensaje='CONDUCCION'

                           datos = requests.get('https://crm.itb.edu.ec/api',params={'a': 'verificarprospecto','identificacion': referidos.cedula if referidos.extranjero==False else referidos.pasaporte},timeout=15,verify=False)

                           if datos.status_code == 200:
                                datos=datos.json()
                                if datos['result']=='ok':
                                    pass
                                else:
                                    return HttpResponseRedirect("alu_referidos/?action=add&info="+"Ya existe la identificacion en el CRM Presencial")

                           datos = requests.get('https://sgaonline.itb.edu.ec/funciones',params={'a': 'verificarprospecto','identificacion': referidos.cedula if referidos.extranjero==False else referidos.pasaporte},timeout=15,verify=False)

                           if datos.status_code == 200:
                                datos=datos.json()
                                if datos['result']=='ok':
                                    pass
                                else:
                                    return HttpResponseRedirect("alu_referidos/?action=add&info="+"Ya existe la identificacion en el CRM Online")

                           datos = requests.get('https://crmcondu.itb.edu.ec/funciones',params={'a': 'registrareferido',
                                    'cedula': str(f.cleaned_data['cedula']) if f.cleaned_data['extranjero']==False else str(f.cleaned_data['pasaporte']),
                                    'nombres':elimina_tildes(f.cleaned_data['nombres']),'apellido1':elimina_tildes(f.cleaned_data['apellido1']),
                                    'apellido2':elimina_tildes(f.cleaned_data['apellido2']),
                                    'extranjero':f.cleaned_data['extranjero'],'idsexo':str(f.cleaned_data['sexo'].id),'telefono':str(f.cleaned_data['telefono_conv']),'celular':str(f.cleaned_data['telefono']),'correo':str(f.cleaned_data['email']),'usuario':str(request.user.id),'idcarrera':str(f.cleaned_data['tipolicencia']),'sgapresencial':'True','sgaonline':'False','referidoventaexterna':'True','conduccion':'False'},timeout=15,verify=False)

                       if datos.status_code == 200:
                          datos=datos.json()
                          if int(datos['idprospecto'])>0:
                              referidos.idprospecto=int(datos['idprospecto'])
                              referidos.save()

                              client_address = ip_client_address(request)

                              #Log de ADICIONAR INSCRIPCION
                              LogEntry.objects.log_action(
                                    user_id         = request.user.pk,
                                    content_type_id = ContentType.objects.get_for_model(referidos).pk,
                                    object_id       = referidos.id,
                                    object_repr     = force_str(referidos),
                                    action_flag     = ADDITION,
                                    change_message  = 'ADICIONADO REFERIDO '+mensaje+' (' + client_address + ')' )

                              referidos.correo_referidos(request.user,'SE AGREGO REFERIDO')


                          else:
                              return HttpResponseRedirect("alu_referidos/?action=add&info="+'YA EXISTE LA IDENTIFICACION')

                       else:
                          return HttpResponseRedirect("alu_referidos/?action=add&info="+"Error al registrar referido CRM ITB")

                  except requests.Timeout:
                    print("Error Timeout")
                    return HttpResponse(json.dumps({"result": "Error por Timeout"}), content_type="application/json")
                  except requests.ConnectionError:
                    print("Error Conexion")
                    return HttpResponse(json.dumps({"result": "Error de conexion"}), content_type="application/json")

                return HttpResponseRedirect("/alu_referidos")
            except  Exception as e:
                return HttpResponseRedirect("/?info="+str(e))

        elif action == 'generar_excel':
            try:
                inicio = request.POST['inicio']
                fin = request.POST['fin']
                fechai = convertir_fecha(inicio)
                fechaf = convertir_fecha(fin)+timedelta(hours=23,minutes=59)
                titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                titulo.font.height = 20*11
                titulo2.font.height = 20*11
                subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                subtitulo.font.height = 20*10
                wb = xlwt.Workbook()
                ws = wb.add_sheet('Listado',cell_overwrite_ok=True)

                tit = TituloInstitucion.objects.all()[:1].get()
                ws.write_merge(0, 0,0,14, tit.nombre , titulo2)
                ws.write_merge(1, 1,0,14, 'LISTADO DE REFERIDOS POR RANGO DE FECHAS', titulo2)
                ws.write(2, 0, 'DESDE', titulo)
                ws.write(2, 1, str((fechai.date())), titulo)
                ws.write(3, 0, 'HASTA:', titulo)
                ws.write(3, 1, str((fechaf.date())), titulo)
                fila=5
                persona = Persona.objects.filter(usuario__username=request.user)[:1].get()
                referidos = ReferidosInscripcion.objects.filter(fecha__gte=fechai, fecha__lte=fechaf,activo=True, administrativo=persona).order_by('fecha','apellido1','apellido2','nombres')
                if referidos.exists():
                    ws.write(fila, 0,  'FECHA', titulo)
                    ws.write(fila, 1,  'NOMBRES', titulo)
                    ws.write(fila, 2,  'CEDULA', titulo)
                    ws.write(fila, 3,  'CELULAR', titulo)
                    ws.write(fila, 4,  'CONVENCIONAL', titulo)
                    ws.write(fila, 5,  'EMAIL', titulo)
                    ws.write(fila, 6,  'VENDEDOR', titulo)
                    ws.write(fila, 7,  'INSCRIPCION PAGADA', titulo)
                    ws.write(fila, 8,  'MATRICULA PAGADA', titulo)
                    ws.write(fila, 9,  'PAGO DE COMISION', titulo)
                    ws.write(fila, 10, 'ONLINE', titulo)
                    ws.write(fila, 11, 'CONDUCCION', titulo)
                    ws.write(fila, 12, 'DESERTOR', titulo)
                    ws.write(fila, 13, 'OBSERVACION',titulo)
                    ws.write(fila, 14, 'ESTADO GESTION',titulo)
                    for r in referidos:
                        print(r.id)
                        crm = ViewCrmReferidos.objects.filter()
                        if crm.filter(cedula=r.cedula).exists():
                            ref = crm.filter(cedula=r.cedula)[:1].get()

                        fila=fila+1
                        try:
                            ws.write(fila, 0, str(r.fecha))
                        except:
                            ws.write(fila, 0, '')
                        try:
                            ws.write(fila, 1, elimina_tildes(r.apellido1+' '+r.apellido2+' '+r.nombres))
                        except:
                            ws.write(fila, 1, '')
                        try:
                            if r.cedula:
                                ws.write(fila, 2, elimina_tildes(r.cedula))
                            else:
                                ws.write(fila, 2, elimina_tildes(r.pasaporte))
                        except:
                            ws.write(fila, 2, '')
                        try:
                            ws.write(fila, 3, elimina_tildes(r.telefono))
                        except:
                            ws.write(fila, 3, '')
                        try:
                            ws.write(fila, 4, elimina_tildes(r.telefono_conv))
                        except:
                            ws.write(fila, 4, '')
                        try:
                            ws.write(fila, 5, elimina_tildes(r.email))
                        except:
                            ws.write(fila, 5, '')
                        try:
                            if r.online:
                                ws.write(fila, 6, elimina_tildes(r.verficarNombreVendedor()))
                            else:
                                if r.verficarNombreVendedor():
                                    ws.write(fila, 6, elimina_tildes(r.verficarNombreVendedor().nombre_completo()))
                                else:
                                    ws.write(fila, 6, 'NO TIENE GESTOR')
                        except:
                            ws.write(fila, 6, 'NO VALE')
                        try:
                            if r.online:
                                if r.verificar_inscrip_online():
                                    ws.write(fila, 7, 'SI')
                                else:
                                    ws.write(fila, 7, 'NO')
                            elif r.conduccion:
                                if r.verificar_inscrip_conduccion():
                                    ws.write(fila, 7, 'SI')
                                else:
                                    ws.write(fila, 7, 'NO')
                            else:
                                if r.inscrito:
                                    ws.write(fila, 7, 'SI')
                                else:
                                    ws.write(fila, 7, 'NO')
                        except:
                            ws.write(fila, 7, '')
                        try:
                            if r.online:
                                if r.verificar_pago_online():
                                    ws.write(fila, 8, 'SI')
                                else:
                                    ws.write(fila, 8, 'NO')
                            elif r.conduccion:
                                if r.verificar_pago_conduccion():
                                    ws.write(fila, 8, 'SI')
                                else:
                                    ws.write(fila, 8, 'NO')
                            else:
                                if r.verificar_pago_matricula():
                                    # rubro=RubroMatricula.objects.filter(rubro__inscripcion=r.inscripcionref,rubro__cancelado=True)
                                    # if rubro.exists():
                                    ws.write(fila, 8, 'SI')
                                else:
                                    ws.write(fila, 8, 'NO')
                        except:
                            ws.write(fila, 8, '')
                        try:
                            if r.pagocomision:
                                ws.write(fila, 9, 'SI')
                            else:
                                ws.write(fila, 9, 'NO')
                        except:
                            ws.write(fila, 9, '')
                        try:
                            if r.online:
                                ws.write(fila, 10, 'SI')
                            else:
                                ws.write(fila, 10, 'NO')
                        except:
                            ws.write(fila, 10, '')
                        try:
                            if r.conduccion:
                                ws.write(fila, 11, 'SI')
                            else:
                                ws.write(fila, 11, 'NO')
                        except:
                            ws.write(fila, 11, '')
                        try:
                            if ref.seinscribe:
                                ws.write(fila, 12, 'NO')
                            else:
                                ws.write(fila, 12, 'SI')
                        except:
                            ws.write(fila, 12, '')
                        try:
                            if ref.observacion:
                                ws.write(fila, 13, elimina_tildes(ref.observacion))
                            else:
                                ws.write(fila, 13, '')
                        except:
                            ws.write(fila, 13, '')
                        try:
                            if ref.estado:
                                ws.write(fila, 14, elimina_tildes(ref.estado))
                            else:
                                ws.write(fila, 14, '')
                        except:
                            ws.write(fila, 14, '')

                nombre ='referidos'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

            except Exception as ex:
                print(ex)

    else:
        data = {'title': 'Listado de Referidos'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='add':
                if Inscripcion.objects.filter(persona=data['persona']).exists():
                    inscripcion = Inscripcion.objects.get(persona=data['persona'])
                    data['inscripcion'] = inscripcion
                else:
                   persona = data['persona']
                   data['administrativo'] = persona
                #data['inscripcion'] = Inscripcion.objects.get(persona=data['persona'])
                data['form'] = InscripcionReferidoForm()
                data['form'].cargarcarrera()
                data['form'].cargarcarreraconduccion()
                data['nuevo'] = True
                if 'info' in request.GET:
                   data['info'] = request.GET['info']
                # i = Inscripcion.objects.get(persona=request['persona'])
                return render(request ,"alu_referidos/adicionarbs.html" ,  data)

            if action=='editar':
                if Inscripcion.objects.filter(persona=data['persona']).exists():
                    inscripcion = Inscripcion.objects.get(persona=data['persona'])
                    data['inscripcion'] = inscripcion
                else:
                   persona = data['persona']
                   data['administrativo'] = persona

                if 'info' in request.GET:
                    data['info']=request.GET['info']
                r = ReferidosInscripcion.objects.get(pk=request.GET['id'])
                initial = model_to_dict(r)
                initial.update({'extranjero': r.extranjero})
                referidos = InscripcionReferidoForm(initial=initial)
                data['form'] =referidos
                data['form'].cargarcarrera()
                data['form'].cargarcarreraconduccion()
                data['ref']=r
                return render(request ,"alu_referidos/adicionarbs.html" ,  data)

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

               if 't' in request.GET:
                  todos = request.GET['t']

               if Inscripcion.objects.filter(persona=data['persona']).exists():
                    inscripcion = Inscripcion.objects.get(persona=data['persona'])
                    data['inscripcion'] = inscripcion
                    persona = data['persona']
                    if search:
                        ss = search.split(' ')
                        while '' in ss:
                            ss.remove('')
                        if len(ss)==1:
                            referidos = ReferidosInscripcion.objects.filter(Q(nombres__icontains=search,inscripcion=inscripcion) | Q(apellido1__icontains=search,inscripcion=inscripcion) | Q(apellido2__icontains=search,inscripcion=inscripcion) | Q(cedula__icontains=search,inscripcion=inscripcion)).order_by('apellido1','apellido2','nombres')
                        else:
                            referidos = ReferidosInscripcion.objects.filter(Q(apellido1__icontains=ss[0],activo=True,administrativo=persona) | Q(apellido2__icontains=ss[1],activo=True,administrativo=persona)| Q(cedula__icontains=search,administrativo=persona)).order_by('apellido1','apellido2','nombres')
                            if not referidos:
                                referidos = ReferidosInscripcion.objects.filter(Q(apellido1__icontains=ss[0],activo=True,inscripcion=inscripcion) | Q(apellido2__icontains=ss[1],activo=True,inscripcion=inscripcion)| Q(cedula__icontains=search,inscripcion=inscripcion)).order_by('apellido1','apellido2','nombres')


                    else:
                        referidos = ReferidosInscripcion.objects.filter(inscripcion=inscripcion).order_by('apellido1','apellido2','nombres')
               else:
                   persona = data['persona']
                   data['administrativo'] = persona
                   if search:
                        ss = search.split(' ')
                        while '' in ss:
                            ss.remove('')
                        if len(ss)==1:
                            referidos = ReferidosInscripcion.objects.filter(Q(nombres__icontains=search,activo=True,administrativo=persona)| Q(apellido1__icontains=search,activo=True,administrativo=persona)|  Q(apellido2__icontains=search,activo=True,administrativo=persona) | Q(cedula__icontains=search,administrativo=persona)).order_by('apellido1','apellido2','nombres')
                        else:
                            referidos = ReferidosInscripcion.objects.filter(Q(apellido1__icontains=ss[0],activo=True,administrativo=persona) & Q(apellido2__icontains=ss[1],activo=True,administrativo=persona) ).order_by('apellido1','apellido2','nombres')

                   else:
                        referidos = ReferidosInscripcion.objects.filter(activo=True,administrativo=persona).order_by('apellido1','apellido2','nombres')

               if 'des' in request.GET:
                   list=[]
                   referidos = referidos.filter(inscrito=False)
                   for r in referidos:
                       crm = ViewCrmReferidos.objects.filter(cedula=r.cedula, estado='EFECTIVO', seinscribe=True)
                       if crm.exists():
                            list.append(r)
                   referidos=list

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
               data['page'] = page
               data['search'] = search if search else ""
               data['referidos'] = page.object_list
               data['generarform']=RangoFacturasForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})

               return render(request ,"alu_referidos/alu_referidos.html" ,  data)
            except Exception as ex:
                return HttpResponseRedirect("/alu_referidos")