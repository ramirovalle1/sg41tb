from datetime import datetime, timedelta
import json
import os
from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models.query_utils import Q
from django.forms.models import model_to_dict
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template.context import RequestContext
from django.utils.encoding import force_str
from decorators import secure_module
from settings import TIPO_MORA_RUBRO, MEDIA_ROOT
from sga.commonviews import addUserData, ip_client_address
from sga.forms import ChequeProtestadoForm, ChequeFechaCobroForm, DocumentoInscripcionForm
from sga.models import Factura, PagoCheque, ChequeProtestado, InscripcionFlags, TipoOtroRubro, Rubro, RubroOtro, RubroNotaDebito, Inscripcion, DocumentoInscripcion, Archivo
from django.db import transaction

@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
@transaction.atomic()
def view(request):
    if request.method=='POST':
        action = request.POST['action']
        if action=='adddocumento':
            form = DocumentoInscripcionForm(request.POST, request.FILES)
            inscripcion = Inscripcion.objects.get(pk=int(request.POST['inscripcion']))
            if form.is_valid():
                archivo = Archivo(nombre=form.cleaned_data['tipo'].nombre,
                    fecha=datetime.now(),
                    archivo = request.FILES['archivo'],
                    tipo = form.cleaned_data['tipo'])
                archivo.save()

                documento = DocumentoInscripcion(inscripcion=inscripcion, archivo=archivo)
                documento.save()
                documento.correo_secretaria('NOTIFICACION DOCUMENTO SUBIDO')

                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de ADICIONAR DOCUMENTO
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(documento).pk,
                    object_id       = documento.id,
                    object_repr     = force_str(documento),
                    action_flag     = ADDITION,
                    change_message  = 'Adicionado Documento  por Alumno (' + client_address + ')' )
        if action=='cambiar':
            form = DocumentoInscripcionForm(request.POST, request.FILES)
            documento = DocumentoInscripcion.objects.get(pk=int(request.POST['documento']))

            if "archivo" in request.FILES:
                if documento.archivo.archivo:
                    if os.path.exists(MEDIA_ROOT+'/'+str(documento.archivo.archivo)):
                        os.remove(MEDIA_ROOT+'/'+str(documento.archivo.archivo))

                documento.archivo.archivo=request.FILES['archivo']
                documento.archivo.save()
                documento.correo_secretaria('NOTIFICACION DOCUMENTO HA SIDO CAMBIADO')

                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de ADICIONAR DOCUMENTO
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(documento).pk,
                    object_id       = documento.id,
                    object_repr     = force_str(documento),
                    action_flag     = ADDITION,
                    change_message  = 'Cambiado Documento  por Alumno (' + client_address + ')' )

        return HttpResponseRedirect("/documentos_alu")


    else:
        data = {'title': 'Documentos Entregados'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='adddocumento':
                data['title'] = 'Adicionar Documento del Alumno'
                inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                data['inscripcion'] = inscripcion
                data['form'] = DocumentoInscripcionForm()
                data['form'].for_tipoarchivo()
                data['puedesubir']=True
                return render(request ,"inscripciones/adicionar_documentosbs.html" ,  data)
            if action=='cambiar':
                data['title'] = 'Cambiar Documento del Alumno'
                documento = DocumentoInscripcion.objects.get(pk=request.GET['id'])
                data['inscripcion'] =documento.inscripcion
                data['documento'] = documento
                data['form'] = DocumentoInscripcionForm(initial={'tipo':documento.archivo.tipo})
                data['form'].for_tipoarchivo()

                data['puedesubir']=True
                return render(request ,"inscripciones/adicionar_documentosbs.html" ,  data)

        else:
            inscripcion = Inscripcion.objects.get(persona=data['persona'])
            if inscripcion.persona.usuario == request.user:
                data['puedesubir'] = True
            else:
                data['puedesubir'] = False
            data['inscripcion'] = inscripcion
            documentos = DocumentoInscripcion.objects.filter(inscripcion=inscripcion)
            data['documentos'] = documentos
            return render(request ,"inscripciones/documentosbs.html" ,  data)


