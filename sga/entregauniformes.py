from datetime import datetime, date
from decimal import Decimal
import json
import locale
import os
from django.contrib.admin.models import LogEntry, ADDITION, DELETION, CHANGE
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models.query_utils import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template.context import RequestContext
from django.utils.encoding import force_str
from fpdf import FPDF
from decorators import secure_module
from settings import COORDINACION_UASSS,EMAIL_ACTIVE
from sga.commonviews import addUserData, ip_client_address
from sga.forms import ColorTallaUniformeForm,ColorTallaZapatosyUniformeForm,EntregaUniformeExcelForm
from sga.inscripciones import MiPaginador
from sga.tasks import send_html_mail
from sga.models import Matricula,Coordinacion,EntregaUniforme,TipoIncidencia,Persona,TallaUniforme,TallaZapato,EmpresaConvenio, Carrera, Nivel, RubroOtro
from sga.reportes import elimina_tildes

def correo_entrega(contenido,entregado1,entregado2,estudiante,correos,user,op):
    if TipoIncidencia.objects.filter(pk=69).exists():
        tipo = TipoIncidencia.objects.get(pk=69)
        hoy = datetime.now().today()
        persona = Persona.objects.get(usuario=user)
        correos=correos+','+persona.emailinst+','+tipo.correo
        asunto="ENTREGA CONVENIO MUNICIPIO"
        contenido = contenido
        send_html_mail(str(asunto),"emails/email_entregauniformemunicipio.html", {'fecha': hoy,'contenido': contenido, 'usuario': user,'estudiante':estudiante,'entrega1':entregado1,'entrega2':entregado2,'op':op},correos.split(","))


@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    if request.method=='POST':
        action = request.POST['action']

        if action=='entrega_uniforme':
            try:
                if Matricula.objects.filter(pk=request.POST['ids']).exists():
                    matricula=Matricula.objects.filter(pk=request.POST['ids'])[:1].get()

                    if EntregaUniforme.objects.filter(matricula=matricula).exists():
                        uniforme = EntregaUniforme.objects.filter(matricula=matricula)[:1].get()
                        uniforme.entregado= True
                        uniforme.fechaentregado=datetime.now()
                        uniforme.usuarioentrega=request.user
                        uniforme.save()
                        mensaje = request.POST['observacion']
                        #Obtain client ip address
                        client_address = ip_client_address(request)
                        # Log de ADICIONAR INSCRIPCION
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(uniforme).pk,
                            object_id       = uniforme.id,
                            object_repr     = force_str(uniforme),
                            action_flag     = ADDITION,
                            change_message  = mensaje+ ' (' + client_address + ')' )
                        return HttpResponse(json.dumps({"result": "ok"}), content_type="application/json")
                    return HttpResponse(json.dumps({"result": "bad"}), content_type="application/json")
            except Exception as ex:
                return HttpResponse(json.dumps({"result": "bad", "error": str(ex)}), content_type="application/json")

        if action=='add_uniformezapatos':
            correos=''
            matricula = Matricula.objects.get(pk=request.POST['id'])
            tallauniforme=TallaUniforme.objects.get(nombre=request.POST['tallauni'])
            tallazapatos=TallaZapato.objects.get(nombre=request.POST['tallazap'])
            try:
                entrega = EntregaUniforme(matricula=matricula,
                          uniforme=True,
                          tallauniforme_id=tallauniforme.id,
                          coloruniforme_id=request.POST['coloruni'],
                          zapatos=True,
                          tallazapatos_id=tallazapatos.id,
                          colorzapatos_id=request.POST['colorzap'],
                          fecha = datetime.now(),usuario=request.user,
                          fecharep=datetime.now().date())
                entrega.save()

                #Obtain client ip address
                client_address = ip_client_address(request)
                 # Log de Registro de Entrega de Uniformes y Zapatos
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(entrega).pk,
                    object_id       = entrega.id,
                    object_repr     = force_str(entrega),
                    action_flag     = ADDITION,
                    change_message  = 'Registro Entrega Uniforme y Zapatos (' + client_address + ')')

                if EMAIL_ACTIVE:
                   entregado1=' color '+entrega.coloruniforme.nombre + ' talla ' + entrega.tallauniforme.nombre
                   entregado2=' color '+entrega.colorzapatos.nombre + ' talla ' + entrega.tallazapatos.nombre
                   correos=matricula.inscripcion.persona.email+','+matricula.inscripcion.persona.emailinst
                   estudiante=matricula
                   op=1
                   correo_entrega('DETALLE DE LO ENTREGADO A ESTUDIANTE',entregado1,entregado2,estudiante,correos, request.user,op)
                   datos = {"result": "ok"}
                   return HttpResponse(json.dumps(datos),content_type="application/json")
            except Exception as ex:
                return HttpResponse(json.dumps({"result": "bad", "error": str(ex)}),content_type="application/json")

        elif action=='add_mandil':
            correos=''
            matricula = Matricula.objects.get(pk=request.POST['id'])
            try:
                entrega = EntregaUniforme(matricula=matricula,mandil=True,
                          fecha = datetime.now(),usuario=request.user,fecharep=datetime.now().date())
                entrega.save()

                #Obtain client ip address
                client_address = ip_client_address(request)
                 # Log de Registro de Entrega de Mandil
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(entrega).pk,
                    object_id       = entrega.id,
                    object_repr     = force_str(entrega),
                    action_flag     = ADDITION,
                    change_message  = 'Registro Entrega Mandil (' + client_address + ')')

                if EMAIL_ACTIVE:
                   entregado1=''
                   entregado2=''
                   correos=matricula.inscripcion.persona.email+','+matricula.inscripcion.persona.emailinst
                   estudiante=matricula
                   op=2
                   correo_entrega('DETALLE DE LO ENTREGADO A ESTUDIANTE',entregado1,entregado2,estudiante,correos, request.user,op)
                   datos = {"result": "ok"}
                   return HttpResponse(json.dumps(datos),content_type="application/json")
            except Exception as ex:
                return HttpResponse(json.dumps({"result": "bad", "error": str(ex)}),content_type="application/json")

        elif action=='add_solouniforme':
            correos=''
            matricula = Matricula.objects.get(pk=request.POST['id'])
            tallauniforme=TallaUniforme.objects.get(nombre=request.POST['tallauni'])
            try:
                entrega = EntregaUniforme(matricula=matricula,
                          uniforme=True,
                          tallauniforme_id=tallauniforme.id,
                          coloruniforme_id=request.POST['coloruni'],
                          fecha = datetime.now(),usuario=request.user,fecharep=datetime.now().date())
                entrega.save()

                #Obtain client ip address
                client_address = ip_client_address(request)
                 # Log de Registro de Entrega de Uniforme
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(entrega).pk,
                    object_id       = entrega.id,
                    object_repr     = force_str(entrega),
                    action_flag     = ADDITION,
                    change_message  = 'Registro Entrega Uniforme (' + client_address + ')')

                if EMAIL_ACTIVE:
                   entregado1=' color '+entrega.coloruniforme.nombre + ' talla ' + entrega.tallauniforme.nombre
                   entregado2=''
                   correos=matricula.inscripcion.persona.email+','+matricula.inscripcion.persona.emailinst
                   estudiante=matricula
                   op=3
                   correo_entrega('DETALLE DE LO ENTREGADO A ESTUDIANTE',entregado1,entregado2,estudiante,correos, request.user,op)
                   datos = {"result": "ok"}
                   return HttpResponse(json.dumps(datos),content_type="application/json")
            except Exception as ex:
                return HttpResponse(json.dumps({"result": "bad", "error": str(ex)}),content_type="application/json")

    else:
        data = {'title': 'Entrega de Uniformes'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            # if action == 'seleciona':

        else:
            nivel = None
            search = None
            matricula = ""
            entregas = ""
            carreras=""
            carreram=""
            nivelid=''
            convenio=""
            estado=''
            if EmpresaConvenio.objects.filter(pk=1,estado=True).exists():
                convenio=EmpresaConvenio.objects.filter(pk=1,estado=True)[:1].get()
            if Coordinacion.objects.filter(pk=COORDINACION_UASSS).order_by('id').exists():
                coordinacion=Coordinacion.objects.filter(pk=COORDINACION_UASSS)[:1].get()
                carreras= Coordinacion.objects.filter(id=coordinacion.id).order_by('id').values('carrera')

            data['niveles']=list(Nivel.objects.filter(carrera__in = carreras, cerrado= False).values_list('id',flat=True))
            data['carreras']= list(Carrera.objects.filter(id__in=carreras).values_list('id', flat=True))

            if 'nivel' in request.GET:
                if (request.GET['nivel']) != '':
                    data['filtro'] = True
                    nivel=Nivel.objects.filter(pk=request.GET['nivel'])
                    nivelid= nivel.filter().values('id')
                    data['nivel']=request.GET['nivel']
                    matricula = Matricula.objects.filter(nivel__in =nivelid,inscripcion__persona__usuario__is_active=True).order_by('inscripcion__persona__apellido1')
            if 'carrera' in request.GET:
                if(request.GET['carrera']):
                    data['filtro'] = True
                    carreram = Carrera.objects.filter(pk= request.GET['carrera'])
                    carreraid= carreram.filter().values('id')
                    data['carrera']=request.GET['carrera']
                    matricula = Matricula.objects.filter(nivel__cerrado = False,nivel__carrera__in= carreraid,inscripcion__persona__usuario__is_active=True).order_by('-fecha','inscripcion__persona__apellido1')
            if 'e' in request.GET:
                estado =int(request.GET['e'])

            if 's' in request.GET:
                search = request.GET['s']
            if search:
                ss = search.split(' ')
                while '' in ss:
                    ss.remove('')
                if len(ss)==1:
                    if nivel:
                        matricula = matricula.filter(Q(inscripcion__persona__nombres__icontains=search) | Q(inscripcion__persona__apellido1__icontains=search) | Q(inscripcion__persona__apellido2__icontains=search) | Q(inscripcion__persona__cedula__icontains=search) | Q(inscripcion__persona__pasaporte__icontains=search) | Q(inscripcion__carrera__nombre__icontains=search))

                    elif carreram:
                        matricula = matricula.filter(Q(inscripcion__persona__nombres__icontains=search) | Q(inscripcion__persona__apellido1__icontains=search) | Q(inscripcion__persona__apellido2__icontains=search) | Q(inscripcion__persona__cedula__icontains=search) | Q(inscripcion__persona__pasaporte__icontains=search) | Q(inscripcion__carrera__nombre__icontains=search)).order_by('-fecha','inscripcion__persona__apellido1')
                    else:
                        matricula = Matricula.objects.filter(Q(inscripcion__persona__nombres__icontains=search) | Q(inscripcion__persona__apellido1__icontains=search) | Q(inscripcion__persona__apellido2__icontains=search) | Q(inscripcion__persona__cedula__icontains=search) | Q(inscripcion__persona__pasaporte__icontains=search) | Q(inscripcion__carrera__nombre__icontains=search),nivel__cerrado=False,nivel__carrera__in=carreras,inscripcion__persona__usuario__is_active=True).order_by('-fecha','inscripcion__persona__apellido1')
                    # matricula = Matricula.objects.filter(Q(inscripcion__persona__nombres__icontains=search) | Q(inscripcion__persona__apellido1__icontains=search) | Q(inscripcion__persona__apellido2__icontains=search) | Q(inscripcion__persona__cedula__icontains=search) | Q(inscripcion__persona__pasaporte__icontains=search) | Q(inscripcion__carrera__nombre__icontains=search),nivel__cerrado=False,nivel__carrera__in=carreras,inscripcion__becamunicipio=True,inscripcion__persona__usuario__is_active=True).order_by('inscripcion__persona__apellido1')
                    # matricula = Matricula.objects.filter(Q(inscripcion__persona__nombres__icontains=search) | Q(inscripcion__persona__apellido1__icontains=search) | Q(inscripcion__persona__apellido2__icontains=search) | Q(inscripcion__persona__cedula__icontains=search) | Q(inscripcion__persona__pasaporte__icontains=search) | Q(inscripcion__carrera__nombre__icontains=search),nivel__cerrado=False,nivel__carrera__in=carreras,inscripcion__empresaconvenio=convenio,inscripcion__persona__usuario__is_active=True).order_by('inscripcion__persona__apellido1')
                else:
                    # matricula = Matricula.objects.filter(Q(inscripcion__persona__apellido1__icontains=ss[0]) & Q(inscripcion__persona__apellido2__icontains=ss[1]),nivel__cerrado=False,nivel__carrera__in=carreras,inscripcion__becamunicipio=True,inscripcion__persona__usuario__is_active=True).order_by('inscripcion__persona__apellido1')
                    matricula = Matricula.objects.filter(Q(inscripcion__persona__apellido1__icontains=ss[0]) & Q(inscripcion__persona__apellido2__icontains=ss[1]),nivel__cerrado=False,nivel__carrera__in=carreras,inscripcion__persona__usuario__is_active=True).order_by('-fecha','inscripcion__persona__apellido1')
            else:
                if estado ==1:
                    entregas = EntregaUniforme.objects.filter(entregado=True).order_by('matricula__inscripcion__persona__apellido1')
                    data['estado1']= True
                elif estado ==2:
                    entregas = EntregaUniforme.objects.filter(entregado=False).order_by('matricula__inscripcion__persona__apellido1')
                    data['estado1'] = True
                else:
                    entregas = EntregaUniforme.objects.all().order_by('matricula__inscripcion__persona__apellido1','matricula__inscripcion__persona__apellido2')

                # if nivel:
                #     matricula = Matricula.objects.filter(nivel__cerrado=False,nivel__carrera__in=carreras,nivel__in = nivel,inscripcion__persona__usuario__is_active=True)
                #
                # else:
                #     entregas = EntregaUniforme.objects.all().order_by('matricula__inscripcion__persona__apellido1','matricula__inscripcion__persona__apellido2')

            if len(matricula)>0:
                paging = MiPaginador(matricula, 70)
            else:
                paging = MiPaginador(entregas, 70)
            p=1
            try:
                if 'page' in request.GET:
                    p = int(request.GET['page'])
                page = paging.page(p)
            except:
                page = paging.page(1)

            paging.rangos_paginado(p)

            data['paging'] = paging
            data['page'] = page
            data['search'] = search if search else ""
            if len(matricula)>0:
                data['matricula'] = page.object_list
            else:
                data['entregas'] = page.object_list
            data['entrega']= EntregaUniforme.objects.filter()

            data['uniforme'] = ColorTallaUniformeForm()
            data['zapatosuniforme'] = ColorTallaZapatosyUniformeForm()
            data['formfechas'] = EntregaUniformeExcelForm(initial={'inicio': datetime.now().date(),'fin': datetime.now().date()})

            return render(request, "entrega_uniformes/entrega_uniformes.html", data)
