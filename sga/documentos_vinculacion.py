from datetime import datetime, timedelta
from django.contrib.admin.models import LogEntry, ADDITION,CHANGE,DELETION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
from decorators import secure_module
from django.forms import model_to_dict
from django.db.models import Q
from settings import VALIDAR_ENTRADA_SISTEMA_CON_DEUDA, ARCHIVO_TIPO_PLANCLASE
from sga.commonviews import addUserData
from sga.forms import DeberAlumnoForm,DocumentoVinculacionForm, TipoDocumentosOficialesForm
from sga.models import DocumentosOficialesVinculacion,RecordAcademico, Inscripcion, Periodo, LeccionGrupo, Profesor, Materia, DeberAlumno, TipoDocumentosOficiales
from sga.commonviews import addUserData, ip_client_address
from sga.reportes import elimina_tildes


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
def view(request):
    if request.method=='POST':
         action = request.POST['action']
         f = DocumentoVinculacionForm(request.POST)
         if action == 'add':
            if f.is_valid():
                try:
                    if request.POST['ban'] == '1':
                        documento = DocumentosOficialesVinculacion(tipo=f.cleaned_data['tipo'],
                                     director1_id=f.cleaned_data['director1id'],
                                     director2_id=f.cleaned_data['director2id'],
                                     fecha = datetime.now(),
                                     usuario=request.user,
                                     nombredocumento=f.cleaned_data['nombredocumento'],
                                     inicio=f.cleaned_data['inicio'],
                                     fin=f.cleaned_data['fin'])
                        documento.save()
                        mensaje = 'Adicionado'

                        # Log Adicionar Documento Vinculacion
                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(documento).pk,
                            object_id       = documento.id,
                            object_repr     = force_str(documento),
                            action_flag     = ADDITION,
                            change_message  = mensaje + " Documento " +  '(' + client_address + ')' )

                    else:
                        documento= DocumentosOficialesVinculacion.objects.get(pk=int(request.POST['doc']))
                        documento.tipo=f.cleaned_data['tipo']
                        documento.director1_id=f.cleaned_data['director1id']
                        documento.director2_id=f.cleaned_data['director2id']
                        documento.nombredocumento=f.cleaned_data['nombredocumento']
                        documento.inicio=f.cleaned_data['inicio']
                        documento.fin=f.cleaned_data['fin']
                        documento.save()
                        mensaje = 'Editado'

                        # Log Editar Documento Vinculacion
                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(documento).pk,
                            object_id       = documento.id,
                            object_repr     = force_str(documento),
                            action_flag     = CHANGE,
                            change_message  = mensaje + " Documento " +  '(' + client_address + ')' )


                    if 'documento' in request.FILES:
                        documento.documento =  request.FILES['documento']
                        documento.save()

                    return HttpResponseRedirect("/documentos_vinculacion")
                except Exception as ex:
                    if request.POST['ban'] == '1':
                        return HttpResponseRedirect("documentos_vinculacion?action=add&error=1",)
                    else:
                        return HttpResponseRedirect("documentos_vinculacion?action=editar&error=1&id="+str(request.POST['documento']),)
            else:
                if request.POST['ban'] == '1':
                    return HttpResponseRedirect("documentos_vinculacion?action=add&error=1",)
                else:
                    return HttpResponseRedirect("documentos_vinculacion?action=editar&error=1&id="+str(request.POST['documento']),)

         elif action == 'add_tipo':
             try:
                tipo = elimina_tildes(request.POST['tipo']).upper()
                existe = TipoDocumentosOficiales.objects.filter(tipo=tipo).exists()
                if existe:
                    return HttpResponseRedirect('/documentos_vinculacion?error=Tipo de Documento existente')
                else:
                    guardar = TipoDocumentosOficiales(tipo=tipo)
                    guardar.save()
                    mensaje = 'Ingreso Tipo Documento Vinculacion'
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(guardar).pk,
                    object_id       = guardar.id,
                    object_repr     = force_str(guardar),
                    action_flag     = ADDITION,
                    change_message  = mensaje+' (' + client_address + ')' )
                return HttpResponseRedirect('/documentos_vinculacion')
             except Exception as ex:
                print(ex)
                return HttpResponseRedirect('/documentos_vinculacion?error=Ocurrio un error, vuelva a intentarlo')

    else:
        data = {'title': 'Listado de Documentos Oficiales de Vinculacion'}
        addUserData(request, data)
        try:
            if 'action' in request.GET:
                action = request.GET['action']
                if action == 'add':
                    data['form'] = DocumentoVinculacionForm()
                    if 'error' in request.GET:
                        data['error'] = 1
                    data['ban'] =1
                    data['form'] = DocumentoVinculacionForm(initial={'inicio': datetime.now().date(),'fin':datetime.now().date()})
                    return render(request ,"documentos_vinculacion/add_documento.html" ,  data)

                elif action == 'editar':
                    documento = DocumentosOficialesVinculacion.objects.get(pk=request.GET['id'])
                    initial = model_to_dict(documento)
                    form = DocumentoVinculacionForm(initial=initial)

                    if 'error' in request.GET:
                        data['error'] = 1
                    data['ban'] = 2
                    data['documento'] =documento
                    if documento.director1:
                        data['director1'] = documento.director1
                    else:
                        data['director1'] = ''
                    if documento.director2:
                        data['director2'] = documento.director2
                    else:
                        data['director2'] = ''
                    data['form'] = form
                    return render(request ,"documentos_vinculacion/add_documento.html" ,  data)

                elif action == 'eliminar':
                    d =  DocumentosOficialesVinculacion.objects.get(pk=request.GET['id'])

                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de Eliminar Documentos
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(d).pk,
                        object_id       = d.id,
                        object_repr     = force_str(d),
                        action_flag     = DELETION,
                        change_message  = 'Eliminado Documento Vinculacion (' + client_address + ')'  )
                    d.delete()
                    return HttpResponseRedirect("/documentos_vinculacion")

                elif action == 'vertipos':
                    tipo = TipoDocumentosOficiales.objects.filter()
                    data['tipos'] = tipo
                    if 'error' in request.GET:
                        data['error'] = 1
                    return render(request ,"documentos_vinculacion/ver_tipos.html" ,  data)

            else:
                data['title'] = 'Documentos de Vinculacion'
                addUserData(request,data)
                try:
                    search = ""
                    if 's' in request.GET:
                        search = request.GET['s']

                    if search:
                        documento = DocumentosOficialesVinculacion.objects.filter(Q(tipo__tipo__icontains=search)| Q(director1__persona__apellido1__icontains=search)| Q(director1__persona__apellido2__icontains=search)).order_by('-fecha')
                    else:

                        documento = DocumentosOficialesVinculacion.objects.all().order_by('-fecha','-id')
                    paging = MiPaginador(documento, 30)
                    p = 1
                    try:
                        if 'page' in request.GET:
                            p = int(request.GET['page'])
                        page = paging.page(p)
                    except:
                        p = 1
                        page = paging.page(p)

                    data['paging'] = paging
                    data['rangospaging'] = paging.rangos_paginado(p)
                    data['page'] = page
                    data['search'] = search if search else ""
                    data['documento'] = page.object_list
                    data['form'] = TipoDocumentosOficialesForm
                    if 'error' in request.GET:
                        data['error'] = request.GET['error']

                    return render(request ,"documentos_vinculacion/documentos_vinculacion.html" ,  data)

                except Exception as ex:
                    return HttpResponseRedirect("/")

        except Exception as ex:
            print(ex)
            return HttpResponseRedirect("/")