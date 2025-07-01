import csv
from datetime import datetime, timedelta, date
from calendar import calendar,monthrange
import json
import os
import urllib
from sga.reportes import elimina_tildes
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
from decorators import secure_module
from settings import CENTRO_EXTERNO, RUBRO_TIPO_OTRO_MODULO_INTERNO, RUBRO_TIPO_OTRO_INSCRIPCION, DEFAULT_PASSWORD, PROFESORES_GROUP_ID, ALUMNOS_GROUP_ID, UTILIZA_GRUPOS_ALUMNOS, REPORTE_CERTIFICADO_INSCRIPCION, EMAIL_ACTIVE, EVALUACION_ITB, REGISTRO_HISTORIA_NOTAS, NOTA_ESTADO_EN_CURSO, GENERAR_RUBROS_PAGO, GENERAR_RUBRO_INSCRIPCION, GENERAR_RUBRO_INSCRIPCION_MARGEN_DIAS, MODELO_EVALUACION, EVALUACION_IAVQ, EVALUACION_ITS, UTILIZA_NIVEL0_PROPEDEUTICO, TIPO_PERIODO_PROPEDEUTICO, NOTA_ESTADO_APROBADO, UTILIZA_FICHA_MEDICA, EVALUACION_TES, CORREO_INSTITUCIONAL, USA_CORREO_INSTITUCIONAL, INSCRIPCION_CONDUCCION, COD_TIPOVISITABOX, CUPO_MAXIMO, COD_ODONTOLOGICO, GRUPO_BOX_ID, TIPO_ATENCION_BOX_EST,TIPO_ATENCION_BOX_COMUN, CONSUMIDOR_FINAL, SERVICIOS_SPA
from sga.alu_malla import aprobadaAsignatura
from sga.commonviews import addUserData, ip_client_address
from sga.docentes import calculate_username
from sga.forms import PersonaForm, InscripcionForm, RecordAcademicoForm, HistoricoRecordAcademicoForm, HistoriaNivelesDeInscripcionForm, CargarFotoForm, EmpresaInscripcionForm, EstudioInscripcionForm, DocumentoInscripcionForm, ActividadesInscripcionForm, PadreClaveForm, ConvalidacionInscripcionForm, HistoricoNotasITBForm, GraduadoDatosForm, EgresadoForm, InscripcionSenescytForm, RetiradoMatriculaForm, InscripcionCextForm, BecarioForm, InscripcionPracticaForm, ObservacionInscripcionForm, ProcesoDobeForm,  VisitaBibliotecaForm, VisitaBoxForm, MedicamentoForm, TipoVistForm
from sga.models import VisitaTiket,VisTiketDet,TipoVisitasBox,Profesor, ProcesoDobe, Persona, Inscripcion, RecordAcademico, DocumentosDeInscripcion, \
    HistoricoRecordAcademico, HistoriaNivelesDeInscripcion, FotoPersona, EmpresaInscripcion, EstudioInscripcion, DocumentoInscripcion, Archivo, TipoArchivo, \
    Grupo, InscripcionGrupo, PerfilInscripcion, HistoricoNotasITB, PadreClave, Malla, ConvalidacionInscripcion, TipoEstado, Rubro, RubroInscripcion, \
    NivelMalla, EjeFormativo, AsignaturaMalla, Egresado, Asignatura, InscripcionSenescyt, RetiradoMatricula, Carrera, Modalidad, Sesion, Especialidad, \
    Materia, Nivel, TipoOtroRubro, Matricula, MateriaAsignada, RubroOtro, Graduado, InscripcionBecario, InscripcionPracticas, ObservacionInscripcion, \
    InscripcionConduccion, VisitaBiblioteca, TipoVisitasBiblioteca, DetalleVisitasBiblioteca, TipoPersona, VisitaBox, DetalleVisitasBox, Sede, Periodo, \
    TipoConsulta, TipoVisitasBox, SesionTratamiento, ClaveBox, ServiciosBox, SuministroBox, TipoMedicamento, RegistroMedicamento, RecetaVisitaBox, Aula,\
    EspecialistaVisitaBox,PersonalConvenio, RubroReceta, BoxEterno, Sexo, ConvenioBox, DetalleRegistroMedicamento, TrasladoMedicamento,\
    ResponsableBodegaConsultorio,CitasCancelasBox
from sga.tasks import gen_passwd
import psycopg2


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


def cita_web(url_pre,ruta_pre):
    # try:
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

    dataReader = csv.reader(open(csv_filepathname), delimiter=';')


    LINE = -1
    for row in dataReader:
        fe = row[8]
        hoy = datetime.now().date()
        if date(int(fe[0:4]),int(fe[5:7]),int(fe[9:11]))  >= hoy :
            if Sexo.objects.filter(nombre=row[4].upper()).exists():
                sexo= Sexo.objects.filter(nombre=row[4].upper())[:1].get()
            else:
                sexo = Sexo.objects.all()[:1].get()
            if Sede.objects.filter(pk=row[13]).exists():
                campus= Sede.objects.filter(pk=row[13])[:1].get()
            else:
                campus = Sede.objects.all()[:1].get()
            if row[10] == 1:
                activa =False
            else:
                activa=True
            try:
                if not PersonalConvenio.objects.filter(identificacion=row[1]).exists():
                    personaconvenio = PersonalConvenio(identificacion=row[1],
                                                nombres = row[2],
                                                conveniobox=ConvenioBox.objects.get(pk=2))

                else:
                    personaconvenio = PersonalConvenio.objects.filter(identificacion=row[1],conveniobox__id=2)[:1].get()
                    personaconvenio.nombres = row[2]
                personaconvenio.save()
                if not BoxEterno.objects.filter(codigo=row[0]).exists():
                    boxexterno = BoxEterno(codigo = row[0],
                                           persona_convenio=personaconvenio,
                                           sexo=sexo,
                                           telefono=row[5],
                                           fechacita=row[8],
                                           iniciocita=row[6],
                                           fincita=row[7],
                                           motivo=row[12],
                                           campus =campus,
                                           activa=activa)
                    boxexterno.save()
                else:
                    if  row[10] == '0':
                        if not BoxEterno.objects.filter(codigo=row[0])[:1].get().check_in:
                            boxexterno = BoxEterno.objects.filter(codigo=row[0])[:1].get()
                            boxexterno.sexo=sexo
                            boxexterno.telefono=row[5]
                            boxexterno.fechacita=row[8]
                            boxexterno.iniciocita=row[6]
                            boxexterno.finciocita=row[7]
                            boxexterno.motivo=row[12]
                            boxexterno.sede =campus
                            boxexterno.save()
                    # print(preinscripcion.nombres + " " +preinscripcion.apellido1)
            except Exception as ex:
               return  str(ex)
    # except Exception as ex:
    #     return  str(ex)
@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
@transaction.atomic()
def view(request):
    if request.method=='POST':
        action = request.POST['action']
        if action == 'turno':
           try:
                result = {}
                result['result']  = "ok"
                result['turnos']  = TipoVisitasBox.objects.filter().exclude(alias='')
                return HttpResponse(json.dumps(result), content_type="application/json")
           except:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
        if action == 'cuantos':
           try:
                tipid = request.POST['id']
                result = {}
                result['result'] ="ok"
                result['totales']="0"
                result['turno']  ="0"
                sede = None
                client_address = ip_client_address(request)
                if Aula.objects.filter(ip=str(client_address),activa=False).exists():
                    sede = Aula.objects.filter(ip=str(client_address),activa=False)[:1].get().sede.id
                if VisitaTiket.objects.filter(fechatiket=datetime.now().date(),tipovisitabox=tipid,tipovisitabox__sede__id=sede).exists():
                    visi = VisitaTiket.objects.get(fechatiket=datetime.now().date(),tipovisitabox=tipid,tipovisitabox__sede__id=sede)
                    result['totales']= visi.totaltiket
                    if VisTiketDet.objects.filter(atendido=False,visitatiket__id=visi.id,visitatiket__tipovisitabox__sede__id=sede).exists():
                        det =VisTiketDet.objects.filter(atendido=True,visitatiket__id=visi.id,visitatiket__tipovisitabox__sede__id=sede)
                        result['turno']  = det.count()+1
                    else:
                        det =VisTiketDet.objects.filter(atendido=True,visitatiket__id=visi.id,visitatiket__tipovisitabox__sede__id=sede).order_by('-id')[:1].get()
                        result['turno']  = det.tiket
                        result['result'] ="nada"
                else:
                     result['result'] ="nada"
                return HttpResponse(json.dumps(result),content_type="application/json")
           except:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

        if action == 'atender':
           try:
                tipid = request.POST['id']
                result = {}
                result['result'] ="nada"
                if VisitaTiket.objects.filter(fechatiket=datetime.now().date(),tipovisitabox=tipid).exists():
                    visi = VisitaTiket.objects.get(fechatiket=datetime.now().date(),tipovisitabox=tipid)
                    result['totales']= visi.totaltiket
                    if VisTiketDet.objects.filter(atendido=False,visitatiket__id=visi.id,tipoatencionbox__id=TIPO_ATENCION_BOX_EST).exists():
                        det = VisTiketDet.objects.filter(atendido=False,visitatiket__id=visi.id,tipoatencionbox__id=TIPO_ATENCION_BOX_EST).order_by('id')[:1].get()
                        det.atendido=True
                        det.horaatendido=datetime.now()
                        det.save()
                    else:
                        if VisTiketDet.objects.filter(atendido=False,visitatiket__id=visi.id,tipoatencionbox__id=TIPO_ATENCION_BOX_COMUN).exists():
                            det = VisTiketDet.objects.filter(atendido=False,visitatiket__id=visi.id,tipoatencionbox__id=TIPO_ATENCION_BOX_COMUN).order_by('id')[:1].get()
                            det.atendido=True
                            det.horaatendido=datetime.now()
                            det.save()
                    result['result'] ="ok"
                return HttpResponse(json.dumps(result),content_type="application/json")
           except:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

        if action=='add':
            f = VisitaBoxForm(request.POST)
            visita={}
            detallevisita={}
            client_address = ip_client_address(request)
            try:
                if f.is_valid():
                    data={}
                    erroere=0
                    errordescri = ''
                    deuda = False
                    data['veri']= 0
                    if not f.cleaned_data['tipoconsulta']==None:
                        data['veri']= 1
                    # if f.cleaned_data['costo']== False and not Inscripcion.objects.filter(persona__cedula=request.POST['cedula']).exists():
                    if (ServiciosBox.objects.filter(tipovisita=f.cleaned_data['tipovisitabox'],tipopersona= f.cleaned_data['tipopersona'], libre=False).exists() and (f.cleaned_data['costo']==False)):
                    # if f.cleaned_data['costo']== False and not Inscripcion.objects.filter(persona__cedula=request.POST['cedula']).exists():
                        erroere = 1
                        errordescri = 'ESTE SERVICIO TIENE COSTO PARA EL GRUPO: ' + str(f.cleaned_data['tipopersona'])
                    elif (ServiciosBox.objects.filter(tipovisita=f.cleaned_data['tipovisitabox'],tipopersona= f.cleaned_data['tipopersona'], libre=False).exists() and ( f.cleaned_data['valor'] <= 0 )):
                        erroere = 1
                        errordescri = 'ESTE SERVICIO TIENE COSTO PARA EL GRUPO: ' + str(f.cleaned_data['tipopersona']) + " - INGRESAR UN VALOR MAYOR A CERO"


                    elif f.cleaned_data['valor']== 0.00 and f.cleaned_data['costo']== True:
                        erroere = 1
                        errordescri = 'EL VALOR DEL PAGO ESTA EN CERO'
                    elif Inscripcion.objects.filter(persona__cedula=request.POST['cedula']).exists():
                       fecha2=2010
                       c=0
                       data['veri']= 0
                       numconsult= 0
                       if not f.cleaned_data['tipoconsulta']==None:
                           data['veri']= 1
                           if VisitaBox.objects.filter(cedula=request.POST['cedula']).exists():
                               visitabox = VisitaBox.objects.filter(cedula=request.POST['cedula'])[:1].get()
                               if TipoConsulta.objects.filter(pk=request.POST['tipoconsulta']).exists():
                                    if DetalleVisitasBox.objects.filter(visitabox=visitabox,tipoconsulta=request.POST['tipoconsulta']).exists():
                                        detallevisita= DetalleVisitasBox.objects.filter(visitabox=visitabox,tipoconsulta=request.POST['tipoconsulta'])
                                        for detalle in detallevisita:
                                            if detalle.fecha.year == datetime.now().year:
                                               c = c+1
                                               consult=TipoConsulta.objects.get(pk=request.POST['tipoconsulta'])
                                               numconsult=consult.veces
                                    else:
                                        numconsult=1
                       inscripcion = None
                       if Inscripcion.objects.filter(persona__cedula=request.POST['cedula'],persona__usuario__is_active=True,carrera__carrera=True).count() > 1:
                           inscripcion = Inscripcion.objects.filter(persona__cedula=request.POST['cedula'],persona__usuario__is_active=True,carrera__carrera=True)[:1].get()
                       else:
                           if Inscripcion.objects.filter(persona__cedula=request.POST['cedula'],persona__usuario__is_active=True,carrera__carrera=True).exists():
                                inscripcion = Inscripcion.objects.filter(persona__cedula=request.POST['cedula'],persona__usuario__is_active=True,carrera__carrera=True)[:1].get()
                       periodo = request.session['periodo']
                       t=f.cleaned_data['tipovisitabox']
                       if inscripcion:
                           if Matricula.objects.filter(inscripcion=inscripcion).exists():
                               matricula = Matricula.objects.filter(inscripcion=inscripcion).order_by('-id')[:1].get()
                               periodo = matricula.nivel.periodo

                                   # if not inscripcion.persona.usuario.is_active and f.cleaned_data['costo']== False :
                                   #    erroere = 1
                                   #    errordescri = 'ESTE ALUMNO ESTA INACTIVO NO PUEDE USAR ESTE SERVICIO SINO INGRESA EL PAGO RESPECTIVO'

                           if t.valida_retiro and int (f.cleaned_data['tipopersona'].id) != 3:
                               if inscripcion.esta_retiradoper(periodo) and f.cleaned_data['costo']== False:
                                   erroere = 1
                                   errordescri = 'ESTE ALUMNO ESTA RETIRADO NO PUEDE USAR ESTE SERVICIO, DEBERA INGRESAR COMO EXTERNO E INGRESAR PAGO'


                           if inscripcion.tiene_deuda() and f.cleaned_data['costo']== False and t.valida_deuda and int(f.cleaned_data['tipopersona'].id) != 3:
                               if f.cleaned_data['tipovisitabox'].id==COD_TIPOVISITABOX:
                                  deuda = True
                               else:
                                  erroere = 1
                                  errordescri = 'ESTE ALUMNO TIENE DEUDA NO PUEDE USAR ESTE SERVICIO DEBE CANCELAR SU DEUDA'
                           if inscripcion.tiene_deuda() and f.cleaned_data['costo']== True and f.cleaned_data['tipovisitabox'].id!= COD_TIPOVISITABOX and  t.valida_deuda and int(f.cleaned_data['tipopersona'].id) != 3:
                                erroere = 1
                                errordescri = 'ESTE ALUMNO TIENE DEUDA NO PUEDE USAR ESTE SERVICIO DEBE CANCELAR SU DEUDA'
                           if c >= numconsult and f.cleaned_data['costo']== False and f.cleaned_data['tipoconsulta']!= None and c!= 0:
                                erroere = 1
                                errordescri = 'ESTE ALUMNO REALIZO SU SERVICIO GRATUIT0 EN ESTE ANIO DEBERA INGRESAR EL PAGO RESPECTIVO'
                    if erroere != 0:

                        data['title'] = 'Nueva Visita'

                        # insf = VisitaBoxForm(initial={'fecha': datetime.now()})
                        # insf.set_add_mode()
                        # else:
                        insf = VisitaBoxForm(initial={'sede':f.cleaned_data['sede'] ,'tipovisitabox': f.cleaned_data['tipovisitabox'],
                                                      'tipoconsulta': f.cleaned_data['tipoconsulta'],'tipopersona': f.cleaned_data['tipopersona'],
                                                      'costo': f.cleaned_data['costo'],'valor': f.cleaned_data['valor'],'cedula': f.cleaned_data['cedula'],
                                                      'nombres': f.cleaned_data['nombres'],'direccion': f.cleaned_data['direccion'],'telefono': f.cleaned_data['telefono'],
                                                      'sexo': f.cleaned_data['sexo'],'motivo': f.cleaned_data['motivo'],'observacion': f.cleaned_data['observacion'],'clavebox': f.cleaned_data['clavebox'],
                                                      'sesion': f.cleaned_data['sesion'],'contratamiento': f.cleaned_data['contratamiento'],'sesiontratamiento': f.cleaned_data['sesiontratamiento'],
                                                      'consesion': f.cleaned_data['consesion'],'descripciontrata': f.cleaned_data['descripciontrata']})
                        data['form'] = insf
                        data['utiliza_grupos_alumnos'] = UTILIZA_GRUPOS_ALUMNOS
                        data['grupos_abiertos'] = Grupo.objects.filter(abierto=True).order_by('-nombre')
                        data['centroexterno'] = CENTRO_EXTERNO
                        data['inscripcion_conduccion'] = INSCRIPCION_CONDUCCION
                        data['COD_TIPOVISITABOX']=COD_TIPOVISITABOX
                        data['error']= erroere
                        data['errordesc']= errordescri
                        return render(request ,"visitabox/adicionarbs.html" ,  data)

                    if VisitaBox.objects.filter(cedula=request.POST['cedula']).exists():
                        visita = VisitaBox.objects.filter(cedula=request.POST['cedula'])[:1].get()
                        visita.tipopersona=f.cleaned_data['tipopersona']
                        visita.convenio=f.cleaned_data['convenio']
                        visita.nombre=f.cleaned_data['nombres']
                        visita.cedula=f.cleaned_data['cedula']
                        visita.telefono=f.cleaned_data['telefono']
                        visita.direccion=f.cleaned_data['direccion']
                        visita.save()

                    else:

                        visita = VisitaBox(tipopersona=f.cleaned_data['tipopersona'],
                                        convenio=f.cleaned_data['convenio'],
                                        nombre=f.cleaned_data['nombres'],
                                        cedula=f.cleaned_data['cedula'],
                                        telefono=f.cleaned_data['telefono'],
                                        direccion=f.cleaned_data['direccion'],
                                        sexo=f.cleaned_data['sexo'])

                        visita.save()


                    sesiontrata = 0
                    sesion = 0
                    if f.cleaned_data['consesion']== True:
                        sesiontratamiento = SesionTratamiento(visitabox = visita,
                                                             tipovisitabox = f.cleaned_data['tipovisitabox'],
                                                             descripcion = f.cleaned_data['descripciontrata'],
                                                             numerosesion = f.cleaned_data['numerosesion'] )
                        sesiontratamiento.save()
                        sesiontrata=sesiontratamiento.id
                    if f.cleaned_data['contratamiento']== True:
                        sesion = f.cleaned_data['sesion']
                        sesiontrata = f.cleaned_data['sesiontratamiento'].id

                    tconsul=0
                    if not f.cleaned_data['tipoconsulta']==None:
                        tipoconsulta = f.cleaned_data['tipoconsulta']
                        tconsul = tipoconsulta.id



                    detallevisita = DetalleVisitasBox(visitabox=visita,
                                        usuario =  request.user,
                                        tipovisitabox = f.cleaned_data['tipovisitabox'],
                                        fecha = datetime.now(),
                                        motivo = f.cleaned_data ['motivo'],
                                        observacion = f.cleaned_data ['observacion'],
                                        sede = f.cleaned_data['sede'],
                                        valor = f.cleaned_data['valor'],
                                        costo = f.cleaned_data['costo'],
                                        clavebox = f.cleaned_data['clavebox'],
                                        sesion = sesion,
                                        deuda = deuda,
                                        tipoconsulta = tconsul,
                                        sesiontratamiento = sesiontrata)
                    detallevisita.save()
                    if CitasCancelasBox.objects.filter(cedula=request.POST['cedula'],atendido=False).exists():
                        visitacancelada = CitasCancelasBox.objects.filter(cedula=request.POST['cedula'],atendido=False)[:1].get()
                        visitacancelada.atendido=True
                        visitacancelada.save()
                    if 'boxexterno' in request.POST:
                        boxexterno = BoxEterno.objects.filter(pk=request.POST['boxexterno'])[:1].get()
                        boxexterno.visitabox = detallevisita
                        boxexterno.save()
                        boxexterno.notificacion()
                        detallevisita.alternativa = f.cleaned_data['alternativa']
                        detallevisita.save()

                    if deuda:
                        if EMAIL_ACTIVE:
                            detallevisita.mail_inscdeuda(request.user.pk,visita.cedula)
                else:
                    errorbox='Falta informacion por ingresar'
                    return HttpResponseRedirect("/visitabox?action=add&errorbox="+(str(errorbox)))

            except Exception as e:
                print(str(e))
                # return render(request ,"visitabox/adicionarbs.html & e_add=3" ,  data)
                # return HttpResponseRedirect("/documentos?action=add&e_add=3")
                # return HttpResponseRedirect("visitabox/adicionarbs.html"+"&e_add=3")
                return HttpResponseRedirect("visitabox?action=add&e_add="+str(e))
                # return HttpResponseRedirect("/documentos?action=add&e_add=3")

            #Obtain client ip address
            #Log de ADICIONAR INSCRIPCION
            LogEntry.objects.log_action(
                user_id         = request.user.pk,
                content_type_id = ContentType.objects.get_for_model(visita).pk,
                object_id       = visita.id,
                object_repr     = force_str(visita),
                action_flag     = ADDITION,
                change_message  = 'Adicionada Visita Box (' + client_address + ')')
            if 'receta' in request.POST:
                return HttpResponseRedirect("visitabox?action=addreceta&id="+str(detallevisita.id))
            else:
                return HttpResponseRedirect("visitabox?action=detalle&visita="+str(visita.id))
        elif action =='addreceta':
            try:
                datos = json.loads(request.POST['datos'])
                visi=""
                precio = 0
                medi = ""
                receta = None
                if datos != "":
                    for d in datos:
                        if d['tipbaja'] == 'detalle':
                            bajamedicamento = DetalleRegistroMedicamento.objects.get(id=d['medic'])
                            re = bajamedicamento.registromedicamento
                        else:
                            bajamedicamento = TrasladoMedicamento.objects.get(id=d['medic'])
                            re = bajamedicamento.registmedicadest
                        if re.cantidad >= int( d['cantidad']):
                            receta = RecetaVisitaBox(
                                            registro_id = int(re.id),
                                            visita_id = int(d['visita']),
                                            cantidad = int(d['cantidad']),
                                            lote = bajamedicamento.lote,
                                            precio = d['precio'],
                                            fecha = datetime.now().date())
                            receta.save()
                            if d['tipbaja'] == 'detalle':
                                receta.detalle = bajamedicamento
                            else:
                                receta.traslado = bajamedicamento
                            receta.save()
                            if (re.factura and receta.visita.visitabox.tipopersona.id != 2 and  receta.visita.visitabox.tipopersona.id != 10 and  receta.visita.visitabox.tipopersona.id != 12) and request.POST['emer'] == '0':
                                receta.factura = re.factura
                                receta.save()
                            visi= VisitaBox.objects.get(id=receta.visita.visitabox.id)
                            if (receta.registro.factura and receta.visita.visitabox.tipopersona.id != 2 and  receta.visita.visitabox.tipopersona.id != 10 and  receta.visita.visitabox.tipopersona.id != 12)  and request.POST['emer'] == '0':
                                precio = precio + (receta.cantidad * float(receta.precio))
                            else:
                                # OCU 19-03-2019
                                if DetalleVisitasBox.objects.filter(id=receta.visita.id,tipovisitabox__id__in=SERVICIOS_SPA).exists():
                                    detallevisita= DetalleVisitasBox.objects.filter(id=receta.visita.id,tipovisitabox__id__in=SERVICIOS_SPA)[:1].get()
                                    if (receta.registro.factura and (receta.visita.visitabox.tipopersona.id == 2 or  receta.visita.visitabox.tipopersona.id == 10 or  receta.visita.visitabox.tipopersona.id == 12))  and request.POST['emer'] == '0' and detallevisita.tipovisitabox.id in SERVICIOS_SPA:
                                        precio = precio + (receta.cantidad * float(receta.precio))
                                #hasta aqui OCU
                                if request.POST['fact'] == '0' or request.POST['emer'] == '1':
                                    regist = RegistroMedicamento.objects.get(id=receta.registro_id)
                                    regist.cantidad = regist.cantidad - receta.cantidad
                                    bajamedicamento.stock = bajamedicamento.stock - receta.cantidad
                                    bajamedicamento.save()
                                    regist.save()
                        else:
                            if medi:
                                medi = medi + " - "
                            medi = medi + " " + re.nombre.descripcion
                            # return HttpResponse(json.dumps({"result":"badcant","registrome":re.nombre.descripcion}),content_type="application/json")
                    if receta and  precio:
                        tipootro = TipoOtroRubro.objects.get(pk=15)
                        inscripcion = Inscripcion.objects.get(pk=CONSUMIDOR_FINAL)
                        rubro = Rubro(fecha=datetime.now().date(), valor=float(precio),
                              inscripcion=inscripcion, cancelado=False, fechavence=datetime.now().date())
                        rubro.save()
                        rubrootro = RubroOtro(rubro=rubro, tipo=tipootro, descripcion='TRATAMIENTO ' + receta.visita.tipovisitabox.descripcion + " - " + receta.visita.visitabox.cedula )
                        rubrootro.save()
                        recetarubro = RubroReceta(rubrootro=rubrootro,detallebox = receta.visita)
                        recetarubro.save()
                    if  request.POST['emer'] == '1':
                        receta.visita.emeregencia=True
                        receta.visita.save()
                    if EMAIL_ACTIVE and receta :
                        receta.visita.correo_receta(request.user,request.POST['emer'])
                    return HttpResponse(json.dumps({"result":"ok","visita":str(visi.id)}),content_type="application/json")
                else:
                    return HttpResponse(json.dumps({"result":"badreg"}),content_type="application/json")
            except Exception as ex:
                transaction.set_rollback(True)
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
        elif action =='addespecialista':
            try:
                datos = json.loads(request.POST['datos'])
                visi=""
                if datos != "":
                    for d in datos:
                        receta = EspecialistaVisitaBox(
                                        especialista_id = int(d['espec']),
                                        visita_id = int(d['detvisita']),
                                        fecha = datetime.now().date()
                                        )
                        receta.save()
                        visi= VisitaBox.objects.get(id=receta.visita.visitabox.id)

                    return HttpResponse(json.dumps({"result":"ok","visita":str(visi.id)}),content_type="application/json")
                else:
                    return HttpResponse(json.dumps({"result":"badreg"}),content_type="application/json")
            except Exception as ex:
                transaction.set_rollback(True)
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
        elif action == 'numerosesion':
            if DetalleVisitasBox.objects.filter(sesiontratamiento=request.POST['trata']).exists():
                d = DetalleVisitasBox.objects.filter(sesiontratamiento=request.POST['trata']).order_by('-id')[:1].get()
                s = SesionTratamiento.objects.get(pk=request.POST['trata'])
                result = {}
                result['result'] = 'ok'
                result['num'] = d.sesion+1
                result['nums'] = s.numerosesion
                return HttpResponse(json.dumps(result),content_type="application/json")
            else:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
        elif action =='consultcant':
            if RegistroMedicamento.objects.filter(id=request.POST['regis']).exists():
                registro = RegistroMedicamento.objects.get(id=request.POST['regis'])
                if registro.cantidad >= int(request.POST['cantidad']):
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                else:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
            else:
                return HttpResponse(json.dumps({"result":"badex"}),content_type="application/json")
        #   Turno
        elif action == 'turno':
             TipoVisitasBox.objects.filter().exclude(alias='')
             return HttpResponse(json.dumps({"result":"badex"}),content_type="application/json")

        elif action =='consult':
            if TipoConsulta.objects.filter(tipovisitabox=request.POST['id']).exists():
                return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
            else:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
        elif action=='datosvisitas':
            # try:
                result = {}
                convenio = ''
                curniv=None
                cedula = request.POST['cedula']
                tpersona=None
                dato3=None
                if PersonalConvenio.objects.filter(identificacion=cedula).exists():
                   persona = PersonalConvenio.objects.filter(identificacion=cedula)[:1].get()
                   tpersona = TipoPersona.objects.get(pk=7)
                   result['tpersona'] = tpersona.id
                   convenio = persona.conveniobox
                   result['convenio']  = persona.conveniobox.id

                else:
                   gruposexcluidos = [PROFESORES_GROUP_ID,ALUMNOS_GROUP_ID]
                   if Persona.objects.filter(cedula=cedula,usuario__groups__id=PROFESORES_GROUP_ID).exists():
                       persona = Persona.objects.filter(cedula=cedula,usuario__groups__id=PROFESORES_GROUP_ID)[:1].get()
                       tpersona = TipoPersona.objects.get(pk=4)

                   elif  Matricula.objects.filter(inscripcion__persona__cedula=cedula,nivel__cerrado=False,inscripcion__persona__usuario__is_active=True).exclude(nivel__carrera__nombre='CONGRESO DE PEDAGOGIA').exists():
                   # elif  Persona.objects.filter(cedula=cedula,usuario__groups__id=ALUMNOS_GROUP_ID).exists():
                       persona = Persona.objects.filter(cedula=cedula,usuario__groups__id=ALUMNOS_GROUP_ID,usuario__is_active=True)[:1].get()
                       # persona = Persona.objects.filter(cedula=cedula,usuario__groups__id=ALUMNOS_GROUP_ID)[:1].get()
                       if persona:
                           if not RetiradoMatricula.objects.filter(inscripcion__persona=persona, activo=False).exists():
                                tpersona = TipoPersona.objects.get(pk=2)
                   elif  Matricula.objects.filter(inscripcion__persona__pasaporte=cedula,nivel__cerrado=False).exclude(nivel__carrera__nombre='CONGRESO DE PEDAGOGIA').exists():
                       # elif  Persona.objects.filter(cedula=cedula,usuario__groups__id=ALUMNOS_GROUP_ID).exists():
                           persona = Persona.objects.filter(pasaporte=cedula,usuario__groups__id=ALUMNOS_GROUP_ID,usuario__is_active=True)[:1].get()
                           # persona = Persona.objects.filter(cedula=cedula,usuario__groups__id=ALUMNOS_GROUP_ID)[:1].get()
                           if persona:
                               if not RetiradoMatricula.objects.filter(inscripcion__persona=persona, activo=False).exists():
                                    tpersona = TipoPersona.objects.get(pk=2)

                   elif Persona.objects.filter(cedula=cedula,usuario__is_active=True).exclude(usuario__groups__id__in=gruposexcluidos).exists():
                       persona = Persona.objects.filter(cedula=cedula,usuario__is_active=True).exclude(usuario__groups__id__in=gruposexcluidos)[:1].get()
                       tpersona = TipoPersona.objects.get(pk=1)

                   # elif VisitaBox.objects.filter(cedula=cedula).exists():
                   #     persona = VisitaBox.objects.filter(cedula=cedula)[:1].get()
                   #     tpersona = persona.tipopersona
                   #     convenio = persona.convenio
                   else:
                       cn = psycopg2.connect("host=10.10.9.45 dbname=conduccion user=aok password=R0b3rt0.1tb$")
                       # cn = psycopg2.connect("host=localhost dbname=conduccion_10junio user=postgres password=sa port=5433 ") #DATOS DE LA BASE
                       cur = cn.cursor()
                       # cur.execute("select distinct auth_group.id as id_grupo "
                       #                "from sga_persona,auth_user,auth_user_groups ,auth_group ,sga_matricula,sga_inscripcion,sga_nivel "
                       #                "where sga_persona.usuario_id=auth_user.id "
                       #                "and auth_user_groups.user_id=auth_user.id "
                       #                "and auth_user_groups.group_id=auth_group.id "
                       #                 "and sga_matricula.inscripcion_id=sga_inscripcion.id "
                       #                 "and sga_inscripcion.persona_id=sga_persona.id "
                       #                  "and sga_matricula.nivel_id=sga_nivel.id "
                       #                  "and sga_nivel.cerrado=False "
                       #                 "and sga_persona.cedula ='" + cedula +"'")
                       # # # if cur:
                       # dato  = cur.fetchone()
                       # cur.close()
                       #OCastillo 07-07-2021 para presentar la informacion de estudiantes de conduccion
                       cur.execute("select grupoid,nombres,direccion,telefono, sexoid from consultaconduccion where cedula='"+cedula+"'")
                       dato2 = cur.fetchone()
                       if dato2:
                           # estudiantes
                           if dato2[0] == 2:
                               tipopersona = 10
                               result['nombre']  = elimina_tildes(dato2[1])
                               try:
                                    result['direccion']=elimina_tildes(dato2[2])
                               except:
                                   result['direccion']=''
                               try:
                                    result['telefono']=elimina_tildes(dato2[3])
                               except:
                                   result['telefono']  =''
                               result['sexo']  = dato2[4]
                               cur.close()

                               if  TipoPersona.objects.filter(pk=tipopersona).exists():
                                   tpersona =TipoPersona.objects.filter(pk=tipopersona)[:1].get()
                                   result['tpersona'] = tpersona.id
                                   result['result']  = "ok"
                                   return HttpResponse(json.dumps(result),content_type="application/json")
                       else:
                            #OCastillo 07-07-2021 para presentar la informacion de docentes de conduccion
                            cur.execute("select grupoid,nombres,direccion,telefono, sexoid from consultadocentescondu where cedula='"+cedula+"'")
                            dato3 = cur.fetchone()
                            if dato3:
                                if dato3[0] == 3:
                                    tipopersona = 9
                                    result['nombre']=elimina_tildes(dato3[1])
                                    try:
                                        result['direccion']=elimina_tildes(dato3[2])
                                    except:
                                        result['direccion']=''
                                    try:
                                        result['telefono']=elimina_tildes(dato3[3])
                                    except:
                                        result['telefono']= ''

                                    result['sexo'] = dato3[4]
                                    cur.close()

                                    if  TipoPersona.objects.filter(pk=tipopersona).exists():
                                        tpersona =TipoPersona.objects.filter(pk=tipopersona)[:1].get()
                                        result['tpersona'] = tpersona.id
                                        result['result']  = "ok"
                                        return HttpResponse(json.dumps(result),content_type="application/json")
                            else:
                                #OCastillo 08-07-2021 para presentar la informacion de administrativos
                                cur.execute("select grupoid,nombres,direccion,telefono, sexoid from consultaadministrativoscondu where cedula='"+cedula+"'")
                                dato4 = cur.fetchone()
                                if dato4:
                                    tipopersona = 8
                                    result['nombre']  = elimina_tildes(dato4[1])
                                    try:
                                        result['direccion']=elimina_tildes(dato4[2])
                                    except:
                                        result['direccion']=''
                                    try:
                                        result['telefono']= elimina_tildes(dato4[3])
                                    except:
                                        result['telefono']=''
                                    result['sexo']  = dato4[4]
                                    cur.close()
                                    if  TipoPersona.objects.filter(pk=tipopersona).exists():
                                       tpersona =TipoPersona.objects.filter(pk=tipopersona)[:1].get()
                                       result['tpersona'] = tpersona.id
                                       result['result']  = "ok"
                                       return HttpResponse(json.dumps(result),content_type="application/json")
                                else:
                                   nivelacion = psycopg2.connect("host=10.10.9.45 dbname=sgaonline user=aok password=R0b3rt0.1tb$") #DATOS DE LA BASE
                                   # nivelacion = psycopg2.connect("host=localhost dbname=online_29junio user=postgres password=sa port=5433 ") #DATOS DE LA BASE DESARROLLO
                                   curniv = nivelacion.cursor()
                                   # curniv.execute("select distinct auth_group.id as id_grupo "
                                   #            "from sga_persona,auth_user,auth_user_groups ,auth_group ,sga_matricula,sga_inscripcion,sga_nivel "
                                   #            "where sga_persona.usuario_id=auth_user.id "
                                   #            "and auth_user_groups.user_id=auth_user.id "
                                   #            "and auth_user_groups.group_id=auth_group.id "
                                   #             "and sga_matricula.inscripcion_id=sga_inscripcion.id "
                                   #             "and sga_inscripcion.persona_id=sga_persona.id "
                                   #              "and sga_matricula.nivel_id=sga_nivel.id "
                                   #              "and sga_nivel.cerrado=False "
                                   #             "and sga_persona.cedula ='" + cedula +"'")

                                   # if cur:
                                   #OCastillo 05-07-2021 para presentar la informacion de estudiantes online
                                   curniv.execute("select grupoid,nombres,direccion,telefono, sexoid from consultaonline where cedula='"+cedula+"'")
                                   datoniv2 = curniv.fetchone()
                                   if datoniv2:
                                       if datoniv2[0] == 7:
                                           tipopersona = 12
                                           if  TipoPersona.objects.filter(pk=tipopersona).exists():
                                                tpersona =TipoPersona.objects.filter(pk=tipopersona)[:1].get()
                                                result['tpersona'] = tpersona.id
                                                result['nombre']  = elimina_tildes(datoniv2[1])
                                                try:
                                                    result['direccion'] =elimina_tildes(datoniv2[2])
                                                except:
                                                    result['direccion'] =''
                                                try:
                                                    result['telefono']  = elimina_tildes(datoniv2[3])
                                                except:
                                                    result['telefono']  =''
                                                result['sexo']  = datoniv2[4]
                                                result['result']  = "ok"
                                                curniv.close()
                                                return HttpResponse(json.dumps(result),content_type="application/json")
                                   else:
                                        #OCastillo 15-08-2022 administrativos educacion continua
                                        educaadmin = psycopg2.connect("host=10.10.9.45 dbname=educacontinua user=aok password=R0b3rt0.1tb$") #DATOS DE LA BASE
                                        # educaadmin = psycopg2.connect("host=localhost dbname=educacont_22julio user=postgres password=aok port=5433 ") #DATOS DE LA BASE DESARROLLO
                                        curadmineduca = educaadmin.cursor()
                                        curadmineduca.execute("select grupoid,nombres,direccion,telefono, sexoid from consultaadministrativoseducacont where cedula='"+cedula+"'")
                                        datoadmineduca = curadmineduca.fetchone()
                                        if datoadmineduca:
                                            tipopersona = 13
                                            result['nombre']  = elimina_tildes(datoadmineduca[1])
                                            try:
                                                result['direccion']=elimina_tildes(datoadmineduca[2])
                                            except:
                                                result['direccion']=''
                                            try:
                                                result['telefono']= elimina_tildes(datoadmineduca[3])
                                            except:
                                                result['telefono']=''
                                            result['sexo']  = datoadmineduca[4]
                                            cur.close()
                                            if  TipoPersona.objects.filter(pk=tipopersona).exists():
                                               tpersona =TipoPersona.objects.filter(pk=tipopersona)[:1].get()
                                               result['tpersona'] = tpersona.id
                                               result['result']  = "ok"
                                               return HttpResponse(json.dumps(result),content_type="application/json")

                if not tpersona:
                    tpersona = TipoPersona.objects.get(pk=3)
                    result['tpersona'] = tpersona.id
                    result['result']  = "ok"


                fecha2=0
                numsesion=0
                tipovisita =''
                if TipoVisitasBox.objects.filter(pk=request.POST['trata']).exists():
                    tipovisita=TipoVisitasBox.objects.filter(pk=request.POST['trata'])[:1].get()
                if VisitaBox.objects.filter(cedula=request.POST['cedula']).exists():
                   visitabox = VisitaBox.objects.filter(cedula=request.POST['cedula'])[:1].get()
                   if Inscripcion.objects.filter(persona__cedula=request.POST['cedula'],persona__usuario__is_active=True,carrera__carrera=True).exists() or  Inscripcion.objects.filter(persona__pasaporte=request.POST['cedula'],persona__usuario__is_active=True,carrera__carrera=True).exists() :
                       if Inscripcion.objects.filter(persona__cedula=request.POST['cedula'],persona__usuario__is_active=True,carrera__carrera=True).exists():
                            inscripcion = Inscripcion.objects.filter(persona__cedula=request.POST['cedula'],persona__usuario__is_active=True,carrera__carrera=True)[:1].get()
                       else:
                           inscripcion = Inscripcion.objects.filter(persona__pasaporte=request.POST['cedula'],persona__usuario__is_active=True,carrera__carrera=True)[:1].get()
                       periodo=request.session['periodo']
                       if Matricula.objects.filter(inscripcion=inscripcion).exists():
                           matricula = Matricula.objects.filter(inscripcion=inscripcion).order_by('-id')[:1].get()
                           periodo = matricula.nivel.periodo

                           # if not inscripcion.persona.usuario.is_active:
                           #    fecha2=2
                       if tipovisita:
                           if tipovisita.valida_retiro and  tpersona.id !=3:
                                if inscripcion.esta_retiradoper(periodo):
                                    fecha2=3

                           if tipovisita.valida_deuda and  tpersona.id !=3:
                               if inscripcion.tiene_deuda():
                                    fecha2=4

                       elif TipoConsulta.objects.filter(pk=request.POST['consulta']).exists():
                           if DetalleVisitasBox.objects.filter(visitabox=visitabox,tipoconsulta=request.POST['consulta']).exists():
                               detallevisita= DetalleVisitasBox.objects.filter(visitabox=visitabox,tipoconsulta=request.POST['consulta'])
                               c=0
                               for detalle in detallevisita:
                                   if detalle.fecha.year == datetime.now().year:
                                       c = c+1
                               consult=TipoConsulta.objects.get(pk=request.POST['consulta'])
                               if consult.veces == c:
                                    fecha2=1

                       elif SesionTratamiento.objects.filter(visitabox=visitabox,tipovisitabox=request.POST['trata']).exists():
                            sesiontr = SesionTratamiento.objects.filter(visitabox=visitabox,tipovisitabox=request.POST['trata'])
                            for sesi in sesiontr:
                                detallebox = DetalleVisitasBox.objects.filter(sesiontratamiento=sesi.id).order_by('-id')[:1].get()
                                if sesi.numerosesion > detallebox.sesion:
                                    fecha2 = 5

                   result = {}
                   result['result']  = "ok"
                   result['nombre']  = visitabox.nombre
                   result['telefono']  = visitabox.telefono
                   result['direccion']  = visitabox.direccion
                   result['sexo']  = visitabox.sexo.id
                   result['fecha']  = fecha2
                   result['tpersona'] = tpersona.id
                   if convenio:
                         result['convenio'] = convenio.id
                    # result['result'] = 'ok'

                   return HttpResponse(json.dumps(result),content_type="application/json")

                elif Persona.objects.filter(cedula=request.POST['cedula']).exists() or Persona.objects.filter(pasaporte=request.POST['cedula']).exists():
                   if Inscripcion.objects.filter(persona__cedula=request.POST['cedula']).exists() or  Inscripcion.objects.filter(persona__pasaporte=request.POST['cedula']).exists():
                       if Inscripcion.objects.filter(persona__cedula=request.POST['cedula']).exists():
                            if Inscripcion.objects.filter(persona__cedula=request.POST['cedula']).count() > 1:
                                inscripcion = Inscripcion.objects.filter(persona__cedula=request.POST['cedula'],persona__usuario__is_active=True)[:1].get()
                            else:
                                inscripcion = Inscripcion.objects.filter(persona__cedula=request.POST['cedula'])[:1].get()
                       else:
                           if Inscripcion.objects.filter(persona__pasaporte=request.POST['cedula']).count() > 1:
                                inscripcion = Inscripcion.objects.filter(persona__pasaporte=request.POST['cedula'],persona__usuario__is_active=True)[:1].get()
                           else:
                                inscripcion = Inscripcion.objects.filter(persona__pasaporte=request.POST['cedula'])[:1].get()
                       periodo=request.session['periodo']
                       if Matricula.objects.filter(inscripcion=inscripcion).exists():
                           matricula = Matricula.objects.filter(inscripcion=inscripcion).order_by('-id')[:1].get()
                           periodo = matricula.nivel.periodo
                                # if not inscripcion.persona.usuario.is_active:
                                #     fecha2=2

                       if tipovisita:
                           if tipovisita.valida_retiro and  tpersona.id !=3:
                                if inscripcion.esta_retiradoper(periodo):
                                    fecha2=3

                       # if tipovisita:
                           if tipovisita.valida_deuda and  tpersona.id !=3:
                                if inscripcion.tiene_deuda():
                                    fecha2=4
                   if  Persona.objects.filter(cedula=request.POST['cedula']).exists():
                        persona = Persona.objects.filter(cedula=request.POST['cedula'])[:1].get()
                   else:
                        persona = Persona.objects.filter(pasaporte=request.POST['cedula'])[:1].get()
                   result = {}
                   result['result']  = "ok"
                   result['nombre']  = persona.nombre_completo()
                   result['telefono']  = persona.telefono
                   result['direccion']  = persona.direccion
                   result['sexo']  = persona.sexo.id
                   result['fecha']  = fecha2
                   result['tpersona'] = tpersona.id
                   if convenio:
                         result['convenio'] = convenio.id
                   return HttpResponse(json.dumps(result),content_type="application/json")
                elif PersonalConvenio.objects.filter(identificacion=request.POST['cedula']).exists():
                    persona = PersonalConvenio.objects.filter(identificacion=request.POST['cedula'])[:1].get()
                    result = {}
                    result['result']  = "ok"
                    result['nombre']  = persona.nombres
                    result['convenio']  = persona.conveniobox.id
                    tpersona = TipoPersona.objects.get(pk=7)
                    result['tpersona'] = tpersona.id
                    return HttpResponse(json.dumps(result),content_type="application/json")

                else:
                   return HttpResponse(json.dumps(result),content_type="application/json")
        elif action == 'addfirma':
            try:
                visitabox = VisitaBox.objects.filter(id=request.POST['idvisita'])[:].get()

                if "archivo" in request.FILES:
                    visitabox.firma = request.FILES["archivo"]
                    visitabox.save()
                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de ABRIR CLASE
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(visitabox).pk,
                    object_id       = visitabox.id,
                    object_repr     = force_str(visitabox),
                    action_flag     = ADDITION,
                    change_message  = 'Agregar firma de visitabox (' + client_address + ')' )

                return HttpResponse(json.dumps({"result": "ok"}),content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({"result": "bad"}),content_type="application/json")
        elif action == 'editfirma':
            try:
                visitabox = VisitaBox.objects.filter(id=request.POST['idvisita'])[:].get()

                if "archivo" in request.FILES:
                    visitabox.firma = request.FILES["archivo"]
                    visitabox.save()
                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de ABRIR CLASE
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(visitabox).pk,
                    object_id       = visitabox.id,
                    object_repr     = force_str(visitabox),
                    action_flag     = ADDITION,
                    change_message  = 'Editar firma de visitabox (' + client_address + ')' )

                return HttpResponse(json.dumps({"result": "ok"}),content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({"result": "bad"}),content_type="application/json")

                   # return HttpResponseRedirect("/ventas")
        return HttpResponseRedirect("/visitabox")
    else:
        data = {'title': 'Listado de Visitas Box'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='add':
                data['title'] = 'Nueva Visita'

                # insf = VisitaBoxForm(initial={'fecha': datetime.now()})
                # insf.set_add_mode()
                # else:
                errordescri=''
                error=0
                sede = 0
                # client_address = ip_client_address(request)
                # if Aula.objects.filter(ip=str(client_address),activa=False).exists():
                #     sede = Aula.objects.filter(ip=str(client_address),activa=False)[:1].get().sede.id
                #OCastillo 21-07-2021 cambio por nueva tabla responsable bodega
                medico=Persona.objects.filter(usuario=request.user)[:1].get()
                if ResponsableBodegaConsultorio.objects.filter(medico=medico,activa=True).exists():
                   sede=ResponsableBodegaConsultorio.objects.filter(medico=medico,activa=True)[:1].get().bodega.id
                if 'pago' in request.GET:
                    form=None
                    consultapagada = CitasCancelasBox.objects.get(pk=request.GET['pago'])
                    if consultapagada.buscarpersonavisita():
                        form = VisitaBoxForm(initial={'fecha': datetime.now(),'sede':consultapagada.tipovisita.sede.id,'tipovisitabox':consultapagada.tipovisita.id,
                                                      'nombres': consultapagada.buscarpersonavisita().nombre,'cedula':consultapagada.cedula,'tipopersona':consultapagada.buscarpersonavisita().tipopersona,
                                                      'direccion':consultapagada.buscarpersonavisita().direccion,'sexo':consultapagada.buscarpersonavisita().sexo.id,
                                                      'telefono':consultapagada.buscarpersonavisita().telefono})
                    else:
                        form = VisitaBoxForm(initial={'fecha': datetime.now(),'sede':consultapagada.tipovisita.sede.id,'tipovisitabox':consultapagada.tipovisita.id,
                                                      'nombres': consultapagada.buscarpersonafactura().nombre,
                                                      'cedula':consultapagada.cedula,'direccion':consultapagada.buscarpersonafactura().direccion,
                                                      'telefono':consultapagada.buscarpersonafactura().telefono})
                    data['form'] = form
                else:
                    form = VisitaBoxForm(initial={'fecha': datetime.now()})
                    form.consulta_tipvisita(sede)
                    data['form'] = form
                data['utiliza_grupos_alumnos'] = UTILIZA_GRUPOS_ALUMNOS
                data['grupos_abiertos'] = Grupo.objects.filter(abierto=True).order_by('-nombre')
                data['centroexterno'] = CENTRO_EXTERNO
                data['inscripcion_conduccion'] = INSCRIPCION_CONDUCCION
                data['COD_TIPOVISITABOX']=COD_TIPOVISITABOX
                data['error']= error
                data['errordesc']= errordescri
                data['veri']= 0
                if 'e_add' in request.GET:
                    data['e_add'] = request.GET['e_add']
                if 'errorbox' in request.GET:
                    data['errorbox'] = request.GET['errorbox']
                if 'boxexterno' in request.GET:
                    boxexterno = BoxEterno.objects.filter(pk=request.GET['boxexterno'])[:1].get()
                    tipovisita = TipoVisitasBox.objects.filter(descripcion='FUNDACION MAJOL',sede__id=boxexterno.campus.id)[:1].get()
                    form = VisitaBoxForm(initial={'fecha': datetime.now(),'sede':boxexterno.campus.id,'tipovisitabox':tipovisita.id,'nombres': boxexterno.persona_convenio.nombres,'cedula':boxexterno.persona_convenio.identificacion,
                                                  'sexo':boxexterno.sexo.id,'telefono':boxexterno.telefono,'motivo':boxexterno.motivo,'convenio':boxexterno.persona_convenio.conveniobox.id,'tipopersona':7})
                    data['form'] = form
                    data['boxexterno'] = request.GET['boxexterno']
                return render(request ,"visitabox/adicionarbs.html" ,  data)
            elif action == 'listar':
                data['title'] = 'Registro de Citas'
                # client_address = ip_client_address(request)
                # if Aula.objects.filter(ip=str(client_address),activa=False).exists():
                #     sede = Aula.objects.filter(ip=str(client_address),activa=False)[:1].get().sede.id
                #OCastillo 21-07-2021 cambio por nueva tabla responsable bodega
                medico=Persona.objects.filter(usuario=request.user)[:1].get()
                if ResponsableBodegaConsultorio.objects.filter(medico=medico,activa=True).exists():
                    sede=ResponsableBodegaConsultorio.objects.filter(medico=medico,activa=True)[:1].get().bodega.id
                    boxexterno = BoxEterno.objects.filter(activa=True,fechacita=datetime.now().date(),visitabox=None,campus=sede).order_by('fechacita','iniciocita')
                    data['boxexterno']=boxexterno
                    return render(request ,"visitabox/citas.html" ,  data)
                return render(request ,"visitabox/citas.html" ,  data)
            elif action == 'buscarpagadas':
                data['title'] = 'Registro de Citas Pagadas y no atendidas'
                data['citaspagadas']=None
                #OCastillo 21-07-2021 cambio por nueva tabla responsable bodega
                if CitasCancelasBox.objects.filter(rubro__cancelado=True,atendido=False).exists():
                    citaspagadas=CitasCancelasBox.objects.filter(rubro__cancelado=True,atendido=False)
                    data['citaspagadas']=citaspagadas
                return render(request ,"visitabox/citaspagadas.html" ,  data)

            elif action=='detallemedi':
                data = {}
                data['receta'] = RecetaVisitaBox.objects.filter(visita=request.GET['id']).order_by('fecha')
                visita= RecetaVisitaBox.objects.filter(visita=request.GET['id'])[:1].get()
                if RubroReceta.objects.filter(detallebox=visita.visita).exists():
                    data['recetarubro'] = RubroReceta.objects.filter(detallebox=visita.visita)[:1].get()
                return render(request ,"visitabox/detallemedicina.html" ,  data)
            elif action=='especialisdeta':
                data = {}
                data['especialistas'] = EspecialistaVisitaBox.objects.filter(visita=request.GET['id']).order_by('fecha')
                return render(request ,"visitabox/detallespecialista.html" ,  data)
            elif action == 'anulareceta':
                result={}
                try:
                    recetarubro = RubroReceta.objects.filter(id=request.GET['id'])[:1].get()
                    for r in RecetaVisitaBox.objects.filter(visita=recetarubro.detallebox):
                        # r.registro.cantidad = r.registro.cantidad + r.cantidad
                        # r.registro.save()
                        r.delete()
                    rubrootro = recetarubro.rubrootro
                    recetarubro.correo("Receta Anulada",'Se realizo la anulacion de la receta.',37,request.user,'anu',None)
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(recetarubro.detallebox.visitabox).pk,
                        object_id       = recetarubro.id,
                        object_repr     = force_str(recetarubro.detallebox.visitabox),
                        action_flag     = DELETION,
                        change_message  = 'Receta eliminada (' + client_address + ')')
                    recetarubro.delete()
                    rubrootro.rubro.delete()
                    rubrootro.delete()
                    result['result'] = 'ok'

                    return HttpResponse(json.dumps(result), content_type="application/json")
                except Exception as e:
                    result['result'] = 'bad'
                    return HttpResponse(json.dumps(result), content_type="application/json")
            elif action == 'addreceta':
                addUserData(request,data)
                data['title'] = 'Nueva Ingreso'
                data['visita'] = DetalleVisitasBox.objects.get(id=request.GET['id'])
                data['registromedicamento'] = RegistroMedicamento.objects.filter(cantidad__gte=1)
                data['detallemedicamento'] = DetalleRegistroMedicamento.objects.filter(stock__gte=1,registromedicamento__cantidad__gt=0)
                data['trasladomedicamento'] = TrasladoMedicamento.objects.filter(stock__gte=1,registmedicadest__cantidad__gt=0)
                form = MedicamentoForm()
                client_address = ip_client_address(request)
                aula = 0
                # if Aula.objects.filter(ip=str(client_address),activa=False).exists():
                #     aula = Aula.objects.filter(ip=str(client_address),activa=False)[:1].get().sede.id
                #OCastillo 21-07-2021 cambio por nueva tabla responsable bodega
                medico=Persona.objects.filter(usuario=request.user)[:1].get()
                if ResponsableBodegaConsultorio.objects.filter(medico=medico,activa=True).exists():
                   aula=ResponsableBodegaConsultorio.objects.filter(medico=medico,activa=True)[:1].get().bodega.id
                data['sede'] = aula
                form.registrobodega(aula)
                data['form'] = form
                return render(request ,"visitabox/addmedicina.html" ,  data)
            elif action =='consult':
                error = 0
                errordescri=""
                con = TipoVisitasBox.objects.get(pk=request.GET['id'])
                if Sede.objects.filter(pk=request.GET['sede']).exists():
                   form = VisitaBoxForm(initial={'sede': Sede.objects.get(pk=request.GET['sede']),'tipovisitabox': TipoVisitasBox.objects.get(pk=request.GET['id'],sede=request.GET['sede'])})
                else:
                   form = VisitaBoxForm(initial={'fecha': datetime.now(),'tipovisitabox': TipoVisitasBox.objects.get(pk=request.GET['id'])})
                form.consulta_tip(con)
                if COD_ODONTOLOGICO == con.id:
                    hoy = datetime.now().date()
                    primer = datetime.strptime((str(hoy.year)+'-'+str(hoy.month)+'-'+'1'),'%Y-%m-%d').date()
                    dia = monthrange(hoy.year,hoy.month)
                    ultimodia=datetime.strptime((str(hoy.year)+'-'+str(hoy.month)+'-'+str(dia[1])),'%Y-%m-%d').date()
                    usuario= Persona.objects.filter(usuario=request.user).get()
                    cupo= DetalleVisitasBox.objects.filter(usuario=request.user,fecha__gte=primer,fecha__lte=ultimodia).count()

                    if cupo > CUPO_MAXIMO:
                        error = 1
                        errordescri = 'USTED YA REALIZO EL CUPO DE 200 ALUMNOS MENSUALES'
                data['form'] = form
                data['utiliza_grupos_alumnos'] = UTILIZA_GRUPOS_ALUMNOS
                data['grupos_abiertos'] = Grupo.objects.filter(abierto=True).order_by('-nombre')
                data['centroexterno'] = CENTRO_EXTERNO
                data['inscripcion_conduccion'] = INSCRIPCION_CONDUCCION
                data['COD_TIPOVISITABOX']=COD_TIPOVISITABOX
                data['error']= error
                data['errordesc']= errordescri
                data['veri']= 1
                return render(request ,"visitabox/adicionarbs.html" ,  data)


            elif action =='consultsede':
                error = 0
                errordescri=""
                form = VisitaBoxForm(initial={'sede': Sede.objects.get(pk=request.GET['sede'])})
                form.consulta_tipvisita(request.GET['sede'])

                data['form'] = form
                data['utiliza_grupos_alumnos'] = UTILIZA_GRUPOS_ALUMNOS
                data['grupos_abiertos'] = Grupo.objects.filter(abierto=True).order_by('-nombre')
                data['centroexterno'] = CENTRO_EXTERNO
                data['inscripcion_conduccion'] = INSCRIPCION_CONDUCCION
                data['COD_TIPOVISITABOX']=COD_TIPOVISITABOX
                data['error']= error
                data['errordesc']= errordescri
                data['veri']= 0
                return render(request ,"visitabox/adicionarbs.html" ,  data)


            elif action == 'addespecialista':
                addUserData(request,data)
                data['title'] = 'Nueva Ingreso'
                data['visita'] = DetalleVisitasBox.objects.get(id=request.GET['id'])
                data['grupo_box_id']=GRUPO_BOX_ID
                return render(request ,"visitabox/addespecialista.html" ,  data)


            elif action =='tratamiento':
                con = VisitaBox.objects.get(cedula=request.GET['cedula'])
                if ClaveBox.objects.filter(pk=request.GET['clave']).exists():
                   form = VisitaBoxForm(initial={'sede': Sede.objects.get(pk=request.GET['sede']),'tipovisitabox': TipoVisitasBox.objects.get(pk=request.GET['tipo']),
                                                 'tipopersona': TipoPersona.objects.get(pk=request.GET['persona']),'cedula': request.GET['cedula'],
                                                 'clavebox': ClaveBox.objects.get(pk=request.GET['clave'])})
                else:
                   form = VisitaBoxForm(initial={'sede': Sede.objects.get(pk=request.GET['sede']),'tipovisitabox': TipoVisitasBox.objects.get(pk=request.GET['tipo']),
                                                 'tipopersona': TipoPersona.objects.get(pk=request.GET['persona']),'cedula': request.GET['cedula']})
                # form = VisitaBoxForm()
                lista =[]
                tipo= TipoVisitasBox.objects.get(pk=request.GET['tipo'])
                if SesionTratamiento.objects.filter(visitabox=con).exists():
                    sesiontr = SesionTratamiento.objects.filter(visitabox=con)
                    for sesi in sesiontr:
                        detallebox = DetalleVisitasBox.objects.filter(sesiontratamiento=sesi.id).order_by('-id')[:1].get()
                        if sesi.numerosesion == detallebox.sesion:
                            lista.append(sesi.id)

                form.consulta_tratamiento(con,lista,tipo)
                data['form'] = form
                data['utiliza_grupos_alumnos'] = UTILIZA_GRUPOS_ALUMNOS
                data['grupos_abiertos'] = Grupo.objects.filter(abierto=True).order_by('-nombre')
                data['centroexterno'] = CENTRO_EXTERNO
                data['inscripcion_conduccion'] = INSCRIPCION_CONDUCCION
                data['COD_TIPOVISITABOX']=COD_TIPOVISITABOX
                data['error']= 0
                data['veri']= 2
                return render(request ,"visitabox/adicionarbs.html" ,  data)
            elif action =='importar':
                try:
                    cita_web("http://www.itb.edu.ec/public/docs/datausercita.txt",'/var/lib/django/repobucki/media/reportes/citaweb.txt')
                except Exception as e:
                    return HttpResponseRedirect("/?info=Ocurrieron  errores  " + str(e))
                return HttpResponseRedirect("/visitabox?action=listar")

            elif action=='detalle':
                medico=Persona.objects.filter(usuario=request.user)[:1].get()
                data['medico']=medico
                addUserData(request,data)
                data['title'] = 'Historial Medico'
                detallevisita = DetalleVisitasBox.objects.filter(visitabox=request.GET['visita']).order_by('-fecha')
                visita = VisitaBox.objects.get(pk=request.GET['visita'])
                paging = MiPaginador(detallevisita, 30)
                p = 1
                if 'ret' in request.GET:
                    data['ret'] = request.GET['ret']
                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                    page = paging.page(p)
                except:
                    page = paging.page(1)
                data['paging'] = paging
                data['rangospaging'] = paging.rangos_paginado(p)
                data['page'] = page
                data['detalle'] = page.object_list
                data['visita'] = visita
                return render(request ,"visitabox/detallebox.html" ,  data)


        else:
            search = None
            todos = None

            if 's' in request.GET:
                search = request.GET['s']

            if 't' in request.GET:
                todos = request.GET['t']
            if search:
                ss = search.split(' ')
                while '' in ss:
                    ss.remove('')

                visitabox = VisitaBox.objects.filter(Q(nombre__icontains=search) | Q(cedula__icontains=search)).order_by('nombre')
                # else:
                #     visitabiblioteca = VisitaBox.objects.filter(Q(persona__apellido1__icontains=ss[0]) & Q(persona__apellido2__icontains=ss[1])).order_by('persona__apellido1','persona__apellido2','persona__nombres')


            elif 'g' in request.GET:
                grupoid = request.GET['g']
                data['grupo'] = TipoPersona.objects.get(pk=request.GET['g'])
                data['grupoid'] = int(grupoid) if grupoid else ""
                visitabox = VisitaBox.objects.filter(tipopersona=data['grupo'])

            elif 'se' in request.GET:
                grupoids = request.GET['se']
                data['grupose'] = Sede.objects.get(pk=request.GET['se'])
                data['grupoids'] = int(grupoids) if grupoids else ""
                visitabox = VisitaBox.objects.filter(detallevisitasbox__sede=data['grupose']).distinct()
            else:
                visitabox = VisitaBox.objects.all().order_by('nombre')

            paging = MiPaginador(visitabox, 30)
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
            data['todos'] = todos if todos else ""
            data['visitabox'] = page.object_list
            data['utiliza_grupos_alumnos'] = UTILIZA_GRUPOS_ALUMNOS
            data['reporte_ficha_id'] = REPORTE_CERTIFICADO_INSCRIPCION
            data['clave'] = DEFAULT_PASSWORD
            data['usafichamedica'] = UTILIZA_FICHA_MEDICA
            data['centroexterno'] = CENTRO_EXTERNO
            data['matriculalibre'] = MODELO_EVALUACION==EVALUACION_TES
            data['grupos'] = TipoPersona.objects.all().order_by('descripcion')
            data['gruposede'] = Sede.objects.filter().exclude(solobodega=True).order_by('nombre')
            data['tipoconsulta'] = TipoConsulta.objects.all()
            data['tipovisitabox'] = TipoVisitasBox.objects.all()
            client_address = ip_client_address(request)
            aula = 0
            #OCastillo 21-07-2021 cambio por nueva tabla responsable bodega
            medico=Persona.objects.filter(usuario=request.user)[:1].get()
            if ResponsableBodegaConsultorio.objects.filter(medico=medico,activa=True).exists():
               aula=ResponsableBodegaConsultorio.objects.filter(medico=medico,activa=True)[:1].get().bodega.id
            # if Aula.objects.filter(ip=str(client_address),activa=False).exists():
            #     aula = Aula.objects.filter(ip=str(client_address),activa=False)[:1].get().sede.id
            form = TipoVistForm()
            form.list_visitabox(aula)
            data['form'] = form
            return render(request ,"visitabox/visitabox.html" ,  data)